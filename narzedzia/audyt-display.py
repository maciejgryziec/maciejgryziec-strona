#!/usr/bin/env python3
"""Regression checks for full-bleed portfolio cards and approved Judler animation.
Runs in an isolated headless Chrome profile; never manipulates the user's browser.
"""
import argparse
import base64
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from cdp import Karta

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--live', action='store_true')
args = parser.parse_args()
OUT = ROOT / '.audit-display' / ('live' if args.live else 'local')
OUT.mkdir(parents=True, exist_ok=True)
checks = []

def check(name, condition, detail=None):
    checks.append({'name': name, 'ok': bool(condition), 'detail': detail})
    if not condition:
        print('FAIL', name, json.dumps(detail, ensure_ascii=False), flush=True)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

server = None
if args.live:
    base = 'https://maciejgryziec.pl'
else:
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}'

try:
    for width, height in [(1440, 1000), (1024, 900), (390, 844), (320, 740)]:
        k = Karta()
        k.ws.settimeout(25)
        try:
            k.rozmiar(width, height, 1, width < 500)
            k.cmd('Page.bringToFront')  # This is the isolated headless browser, not the user's Chrome.
            k.cmd('Page.addScriptToEvaluateOnNewDocument', source="window.__displayErrors=[];window.addEventListener('error',e=>window.__displayErrors.push(e.message));try{localStorage.setItem('umami.disabled','1')}catch(e){}")
            k.cmd('Emulation.setEmulatedMedia', features=[{'name': 'prefers-reduced-motion', 'value': 'reduce'}])
            for page in ['index.html', 'realizacje.html']:
                k.idz(base + '/' + page, .6)
                k.js("document.fonts.ready")
                count = k.js("document.querySelectorAll('.screen-carousel .karta').length")
                check(f'{width}/{page}: carousel present', count == 7, count)
                for i in range(count or 0):
                    k.js(f"document.querySelectorAll('.screen-carousel .kropy button')[{i}].click()")
                    time.sleep(.16)
                    k.js("document.querySelector('.screen-carousel .karty').scrollIntoView({block:'center',behavior:'instant'})")
                    info = k.js("""(async()=>{
                      const card=document.querySelector('.screen-carousel .karta.aktywna');
                      const frame=card.querySelector('.zdjecie');
                      await Promise.all(Array.from(frame.querySelectorAll('img')).map(i=>i.decode().catch(()=>{})));
                      const c=card.getBoundingClientRect(), f=frame.getBoundingClientRect();
                      const title=card.querySelector('.duze').getBoundingClientRect(), desc=card.querySelector('.opis').getBoundingClientRect();
                      const intersects=(a,b)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>2&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2;
                      return {title:card.querySelector('.duze').innerText,frame:f.toJSON(),card:c.toJSON(),heading:title.toJSON(),description:desc.toJSON(),overlap:intersects(f,title)||intersects(f,desc),textFits:title.bottom<=c.bottom+1&&desc.bottom<=c.bottom+1&&title.left>=c.left-1&&desc.right<=c.right+1,overflow:document.documentElement.scrollWidth>innerWidth+1,
                        images:Array.from(frame.querySelectorAll('img')).map(im=>({media:im.dataset.media,src:im.currentSrc,loaded:im.complete&&im.naturalWidth>0,width:im.offsetWidth,height:im.offsetHeight,nw:Number(im.getAttribute('width')),nh:Number(im.getAttribute('height')),fit:getComputedStyle(im).objectFit})),errors:window.__displayErrors};
                    })()""")
                    check(f'{width}/{page}/card{i}: layout', info and not info['overflow'] and not info['overlap'] and info['textFits'], info)
                    if info and info['images']:
                        full = all(im['loaded'] and im['fit'] in ('cover', 'contain') and abs(im['height'] - im['width'] * im['nh']/im['nw']) <= 1.5 for im in info['images'])
                        check(f'{width}/{page}/card{i}: filled native-ratio image', full, info['images'])
                        check(f'{width}/{page}/card{i}: no nested mockup', all(im.get('media') in {'frankie-orders','roofpv-3d','rental-flota','judler-orchestration-v2','card-monitor-report-v2','bacteria-hd-gameplay'} for im in info['images']), info['images'])
                    check(f'{width}/{page}/card{i}: runtime', info and not info['errors'], info['errors'] if info else None)
                    if (width in (1440, 390)) and page == 'index.html' and i in (0, 1, 3, 4, 6):
                        k.zrzut(str(OUT/f'{width}-card-{i}.jpg'), 91)
            # Functional motion, visibility and reduced-motion checks on the hero.
            k.idz(base + '/index.html', .5)
            k.js("document.querySelector('.hero-projekt-nav button[data-to=\"1\"]').click();document.querySelector('.hero-realizacje').scrollIntoView({block:'center',behavior:'instant'})")
            k.js("Promise.all(Array.from(document.querySelector('.hero-judler .project-view.tu').querySelectorAll('img')).map(i=>i.decode().catch(()=>{})))")
            time.sleep(.15)
            reduced = k.js("(()=>{const a=document.querySelector('.hero-judler .judler-motion'),p=a.querySelector('.judler-signal');return {on:a.classList.contains('is-animating'),animation:getComputedStyle(p).animationName}})()")
            check(f'{width}: reduced motion disabled', reduced and not reduced['on'] and reduced['animation']=='none', reduced)
            if width in (1440, 390):
                k.zrzut(str(OUT/f'{width}-judler.jpg'), 94)
            k.cmd('Emulation.setEmulatedMedia', features=[{'name': 'prefers-reduced-motion', 'value': 'no-preference'}])
            # Wait for the media-query and intersection observers to apply the new state.
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if k.js("document.querySelector('.hero-judler .judler-motion').classList.contains('is-animating')"):
                    break
                time.sleep(.08)
            active = k.js("(()=>{const a=document.querySelector('.hero-judler .judler-motion'),p=a.querySelector('.judler-signal');return {on:a.classList.contains('is-animating'),state:getComputedStyle(p).animationPlayState,offset:getComputedStyle(p).strokeDashoffset}})()")
            later = active['offset'] if active else None
            # Animation frames may be throttled briefly after screenshots or a media-query change.
            deadline = time.monotonic() + 2.5
            while time.monotonic() < deadline:
                time.sleep(.08)
                later = k.js("getComputedStyle(document.querySelector('.hero-judler .judler-signal')).strokeDashoffset")
                if active and later != active['offset']:
                    break
            check(f'{width}: connection animation advances', active and active['on'] and active['state']=='running' and active['offset']!=later, {'first':active,'later':later})
            k.js("document.querySelector('.hero-judler .project-view-tabs button[data-view=\"agents\"]').click()")
            time.sleep(.1)
            hidden = k.js("document.querySelector('.hero-judler .judler-motion').classList.contains('is-animating')")
            check(f'{width}: hidden panel animation paused', hidden is False, hidden)
            k.js("document.querySelector('.hero-judler .project-view-tabs button[data-view=\"dashboard\"]').click();window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})")
            time.sleep(.2)
            offscreen = k.js("document.querySelector('.hero-judler .judler-motion').classList.contains('is-animating')")
            check(f'{width}: offscreen animation paused', offscreen is False, offscreen)
            print('DONE DISPLAY', width, flush=True)
        finally:
            k.zamknij()
finally:
    if server:
        server.shutdown()
        server.server_close()
failed = [item for item in checks if not item['ok']]
(OUT/'results.json').write_text(json.dumps({'base':base,'checks':len(checks),'failures':failed,'results':checks}, ensure_ascii=False, indent=2))
print('DISPLAY SUMMARY', len(checks), 'checks;', len(failed), 'failures', flush=True)
raise SystemExit(1 if failed else 0)
