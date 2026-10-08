#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check every screenshot placement for empty frame bands and stretched images.
Runs in the existing isolated headless test browser, never a user's visible tab.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import argparse, json, os, re, threading, time
from cdp import Karta

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--live', action='store_true')
parser.add_argument('--label', default=None)
parser.add_argument('--widths', nargs='+', type=int, default=[1440, 1024, 390, 320])
args = parser.parse_args()
OUT = ROOT / '.audit-screen-fill' / (args.label or ('live' if args.live else 'local'))
OUT.mkdir(parents=True, exist_ok=True)
PAGES = sorted(p.name for p in ROOT.glob('*.html') if re.search(r'<img\b[^>]*(?:src|data-project-src|data-carousel-src)="zdjecia/', p.read_text()))
checks = []
server = None
if args.live:
    base = 'https://maciejgryziec.pl'
else:
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:' + str(server.server_address[1])

FRAME_SELECTORS = '.program-real-shot,.ekrany .ekran,.karta .zdjecie:not(.panelowe),.project-view,.detail-panel.screenshot-panel,.judler-approved-detail .detail-panel,.studium>figure>picture'
VISIBILITY = """e=>e.getClientRects().length && !e.closest('[hidden],[inert],[aria-hidden="true"]') && (!e.closest('.karta') || e.closest('.karta').classList.contains('aktywna')) && (!e.closest('.project-view') || e.closest('.project-view').classList.contains('tu')) && (!e.closest('.detail-panel') || e.closest('.detail-panel').classList.contains('tu'))"""
MEASURE = """(async()=>{
 const e=document.querySelector('[data-fill-audit-id="ID"]');
 const img=e.querySelector('img');
 const bg=e.querySelector('.screen-bg');
 const fw=e.clientWidth,fh=e.clientHeight,cs=getComputedStyle(e);
 const out={frame:e.className||e.tagName,width:fw,height:fh,padding:[cs.paddingTop,cs.paddingRight,cs.paddingBottom,cs.paddingLeft]};
 if(!img){
   if(!bg)return {...out,skip:true};
   const style=getComputedStyle(bg),url=style.backgroundImage.match(/url\\(["']?(.*?)["']?\\)/);
   if(!url)return {...out,ok:false,error:'missing background'};
   const probe=new Image();probe.src=url[1];await probe.decode().catch(()=>{});
   return {...out,source:url[1],fit:style.backgroundSize,ok:probe.naturalWidth>0 && style.backgroundSize==='cover' && Math.abs(bg.clientWidth-fw)<=2 && Math.abs(bg.clientHeight-fh)<=2};
 }
 await Promise.race([img.decode().catch(()=>{}),new Promise(r=>setTimeout(r,5000))]);
 const st=getComputedStyle(img),iw=parseFloat(st.width),ih=parseFloat(st.height),nw=img.naturalWidth,nh=img.naturalHeight;
 let gapX=Math.max(0,fw-iw),gapY=Math.max(0,fh-ih),stretched=false;
 if(st.objectFit==='contain'||st.objectFit==='scale-down'){
   const scale=Math.min(iw/nw,ih/nh,st.objectFit==='scale-down'?1:Infinity);
   gapX+=Math.max(0,iw-nw*scale);gapY+=Math.max(0,ih-nh*scale);
 }else if(st.objectFit==='fill'){
   stretched=Math.abs(iw/ih-nw/nh)>.01;
 }
 const ok=nw>0 && nh>0 && fw>0 && fh>0 && gapX<=2.1 && gapY<=2.1 && !stretched && out.padding.every(p=>parseFloat(p)===0);
 return {...out,source:img.currentSrc||img.src,fit:st.objectFit,imageBox:[iw,ih],natural:[nw,nh],gap:[gapX,gapY],stretched,ok};
})()"""

def capture_frames(k, prefix, scope='document'):
    ids = k.js("""(()=>{document.querySelectorAll('[data-fill-audit-id]').forEach(e=>delete e.dataset.fillAuditId);const root=SCOPE;return Array.from(root.querySelectorAll(SELECTOR)).filter(VISIBLE).filter(e=>e.querySelector('img,.screen-bg')).map((e,i)=>{e.dataset.fillAuditId='audit-'+i;return e.dataset.fillAuditId})})()""".replace('SCOPE', scope).replace('SELECTOR', json.dumps(FRAME_SELECTORS)).replace('VISIBLE', VISIBILITY)) or []
    for ident in ids:
        k.js('document.querySelector('+json.dumps('[data-fill-audit-id="'+ident+'"]')+').scrollIntoView({block:"center",behavior:"instant"})')
        time.sleep(.08)
        row = k.js(MEASURE.replace('ID', ident))
        if not row or row.get('skip'): continue
        checks.append({'name':prefix+'/'+ident, **row})
    return ids

def click(k, selector):
    return k.js('(()=>{const e=document.querySelector('+json.dumps(selector)+');if(!e)return false;e.click();return true})()')

def screenshot(k, selector, filename):
    k.js('document.querySelector('+json.dumps(selector)+').scrollIntoView({block:"center",behavior:"instant"})')
    time.sleep(.12)
    k.zrzut(str(OUT/filename),92)

try:
    for width in args.widths:
        k=Karta()
        k.ws.settimeout(20)
        k.cmd('Page.addScriptToEvaluateOnNewDocument',source="try{localStorage.setItem('umami.disabled','1')}catch(e){}")
        try:
            k.rozmiar(width,1000 if width>=1000 else 844,1,width<1000)
            k.cmd('Emulation.setEmulatedMedia',media='screen',features=[{'name':'prefers-reduced-motion','value':'reduce'}])
            for page in PAGES:
                k.idz(base+'/'+page,.35)
                k.js('document.fonts.ready')
                prefix=str(width)+'/'+page
                capture_frames(k,prefix)
                overflow=k.js('document.documentElement.scrollWidth>innerWidth+1')
                checks.append({'name':prefix+'/no-page-overflow','ok':not overflow})
                if page=='index.html':
                    screenshot(k,'.programy-sekcja','stack-'+str(width)+'.jpg')
                    projects=k.js("Array.from(document.querySelectorAll('.hero-projekt-nav [data-to]')).map(e=>e.dataset.to)") or []
                    for project in projects:
                        click(k,'.hero-projekt-nav [data-to="'+project+'"]')
                        views=k.js("Array.from(document.querySelectorAll('.hero-projekt.aktywny .project-view-tabs [data-view]')).map(e=>e.dataset.view)") or []
                        for view in views:
                            click(k,'.hero-projekt.aktywny .project-view-tabs [data-view="'+view+'"]')
                            capture_frames(k,prefix+'/hero-'+project+'-'+view,"document.querySelector('.hero-realizacje')")
                if page=='realizacje.html':
                    groups=k.js("Array.from(document.querySelectorAll('.detail-showcase')).filter(e=>e.querySelector('.screenshot-panel,.judler-art')).map(e=>({key:e.dataset.detail,views:Array.from(e.querySelectorAll('.detail-tabs [data-view]')).map(b=>b.dataset.view)}))") or []
                    for group in groups:
                        for view in group['views']:
                            root='.detail-showcase[data-detail="'+group['key']+'"]'
                            click(k,root+' .detail-tabs [data-view="'+view+'"]')
                            capture_frames(k,prefix+'/detail-'+group['key']+'-'+view,'document.querySelector('+json.dumps(root)+')')
                        if width in [1440,390] and group['key'] in ['frankie','bacteria']:
                            screenshot(k,root,group['key']+'-detail-'+str(width)+'.jpg')
                cards=k.js("Array.from(document.querySelectorAll('.ksiega .kropy button')).length") or 0
                for card in range(cards):
                    click(k,'.ksiega .kropy button:nth-child('+str(card+1)+')')
                    time.sleep(.1)
                    capture_frames(k,prefix+'/card-'+str(card),"document.querySelector('.ksiega')")
                if page=='opisz-projekt.html' and width in [1440,390]:
                    screenshot(k,'.ekrany','landing-'+str(width)+'.jpg')
            print('DONE ALL SCREEN LOCATIONS',width,flush=True)
        finally:
            k.zamknij()
finally:
    if server:
        server.shutdown();server.server_close()
failed=[c for c in checks if not c.get('ok')]
report={'base':base,'pages':PAGES,'widths':args.widths,'checks':len(checks),'failures':failed,'results':checks}
(OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('SCREEN FILL',len(PAGES),'pages;',len(checks),'checks;',len(failed),'failures',flush=True)
for failure in failed[:12]:print(json.dumps(failure,ensure_ascii=False),flush=True)
raise SystemExit(1 if failed else 0)
