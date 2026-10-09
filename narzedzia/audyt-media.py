#!/usr/bin/env python3
"""Audit logo cache versioning and actual screenshot resolution in isolated Chrome.
Does not interact with any visible browser, user tabs, mailbox or live application data.
"""
from pathlib import Path
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs, unquote
import argparse
import base64
import hashlib
import json
import os
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'narzedzia'))
from cdp import Karta
from media_assets import ASSETS, DIGESTS, local_path, finalize_assets

ap = argparse.ArgumentParser()
ap.add_argument('--live', action='store_true')
args = ap.parse_args()
OUT = ROOT / '.audit-media' / ('live' if args.live else 'local')
OUT.mkdir(parents=True, exist_ok=True)
results = []
limits = []

def check(name, ok, detail=None):
    results.append({'name': name, 'ok': bool(ok), 'detail': detail})
    if not ok:
        print('FAIL', name, detail, flush=True)

class BrandParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.assets = []; self.header = False; self.header_logos = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'header': self.header = True
        if tag == 'img' and self.header and a.get('class') in ('b', 'c'):
            self.header_logos.append(a.get('src', ''))
        for name in ('src', 'href'):
            value = a.get(name, '')
            if local_path(value) in DIGESTS: self.assets.append(value)
    def handle_endtag(self, tag):
        if tag == 'header': self.header = False

# Static checks remain necessary for internal 404/50x documents as well.
for p in sorted(ROOT.glob('*.html')):
    text = p.read_text(); parser = BrandParser(); parser.feed(text)
    wrong = [url for url in parser.assets if parse_qs(urlsplit(url).query).get('v') != [DIGESTS[local_path(url)]]]
    check('brand/' + p.name, len(parser.header_logos) == 2 and not wrong, wrong)
    check('asset-pass-idempotent/' + p.name, finalize_assets(text) == text)

variant_lookup = {v['path']: (key, v) for key, entry in ASSETS.items() for v in entry['variants']}
# Validate the exported files' dimensions, not density-adjusted img.naturalWidth values.
from PIL import Image
for path, (key, variant) in variant_lookup.items():
    with Image.open(ROOT / path) as im:
        check('dimensions/' + path, list(im.size) == [variant['width'], variant['height']])

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
server = None
if args.live:
    base = 'https://maciejgryziec.pl'
else:
    os.chdir(ROOT)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:' + str(server.server_port)

def collect(k, selector, prefix):
    js = '''(async()=>{const imgs=[...document.querySelectorAll(SELECTOR)];for(const i of imgs){i.loading='eager';await Promise.race([i.decode().catch(()=>{}),new Promise(r=>setTimeout(r,8000))]);}return imgs.filter(i=>i.offsetWidth&&i.offsetHeight).map(i=>{const c=getComputedStyle(i);return {key:i.dataset.media,src:i.currentSrc,w:parseFloat(c.width),h:parseFloat(c.height),fit:c.objectFit,dpr:devicePixelRatio,loaded:i.complete&&i.naturalWidth>0};});})()'''.replace('SELECTOR', json.dumps(selector))
    rows = k.js(js) or []
    check(prefix + '/present', bool(rows))
    for index, row in enumerate(rows):
        parsed = urlsplit(row['src'])
        path = unquote(parsed.path).lstrip('/')
        if parsed.netloc != urlsplit(base).netloc or path not in variant_lookup:
            check(prefix + '/known-' + str(index), False, row);continue
        key, variant = variant_lookup[path]
        entry = ASSETS[key]
        ratio = variant['width'] / variant['height']
        painted = max(row['w'], row['h'] * ratio) if row['fit'] == 'cover' else row['w']
        need = painted * row['dpr']
        available = entry['width']
        row.update(file_pixels=variant['width'], needed_pixels=round(need), available_pixels=available)
        check(prefix + '/' + key + '/' + str(index), row['loaded'] and variant['width'] + 2 >= min(need * .97, available), row)
        if available < need * .97:
            limits.append(dict(row, scenario=prefix))
    return rows

try:
    for width, height, dpr in [(1440,1000,1),(1440,1000,2),(390,844,2)]:
        label=f'{width}@{dpr}x';k=Karta();k.ws.settimeout(25)
        try:
            k.rozmiar(width,height,dpr,width<500)
            k.cmd('Network.enable');k.cmd('Network.setCacheDisabled',cacheDisabled=True)
            k.cmd('Emulation.setEmulatedMedia',features=[{'name':'prefers-reduced-motion','value':'reduce'}])
            k.cmd('Page.addScriptToEvaluateOnNewDocument',source="try{localStorage.setItem('umami.disabled','1')}catch(e){};window.__mediaErrors=[];addEventListener('error',e=>window.__mediaErrors.push(e.message));")
            k.idz(base+'/realizacje.html?media-qa='+str(time.time_ns()),.8)
            collect(k,'#photonroof figure img[data-media],#wypozyczalnia figure img[data-media]',label+'/figures')
            groups=k.js("[...document.querySelectorAll('.detail-showcase')].map(g=>({id:g.dataset.detail,views:[...g.querySelectorAll('.detail-tabs button')].map(b=>b.dataset.view)}))") or []
            for group in groups:
                for view in group['views']:
                    root=f'.detail-showcase[data-detail="{group["id"]}"]'
                    k.js('document.querySelector('+json.dumps(root+f' .detail-tabs button[data-view="{view}"]')+').click()')
                    selector=root+' .detail-panel.tu img[data-media]'
                    if k.js('!!document.querySelector('+json.dumps(selector)+')'):
                        collect(k,selector,label+'/detail/'+group['id']+'/'+view)
            if width==1440 and dpr==1:
                k.js("document.querySelector('#wypozyczalnia figure:nth-of-type(3)').scrollIntoView({block:'center',behavior:'instant'})")
                k.zrzut(str(OUT/'rental-gallery.jpg'),96)
            check(label+'/details-no-errors',not k.js('window.__mediaErrors'))
            k.idz(base+'/?media-qa='+str(time.time_ns()),.7)
            for i in range(6):
                k.js('document.querySelector(\'.hero-projekt-nav button[data-to="'+str(i)+'"]\').click()')
                selector='.hero-projekt.aktywny .project-view.tu img[data-media]'
                if k.js('!!document.querySelector('+json.dumps(selector)+')'):
                    collect(k,selector,label+'/hero/'+str(i))
            collect(k,'.program-real-stack img[data-media]',label+'/stack')
            check(label+'/home-no-overflow',not k.js('document.documentElement.scrollWidth>innerWidth'))
            if width==1440 and dpr==1:
                k.js("document.querySelector('.hero-projekt-nav button[data-to=\"0\"]').click();scrollTo(0,0)")
                k.zrzut(str(OUT/'home.jpg'),96)
            print('MEDIA DONE',label,flush=True)
        finally:
            k.zamknij()
finally:
    if server:server.shutdown();server.server_close()
failures=[r for r in results if not r['ok']]
report={'base':base,'checks':len(results),'failures':failures,'results':results,
        'native_resolution_limits':limits,'note':'A native-resolution limit is reported separately; original pixels are not upscaled or invented.'}
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('MEDIA SUMMARY',len(results),'checks;',len(failures),'failures;',len(limits),'native-source limits',flush=True)
sys.exit(1 if failures else 0)
