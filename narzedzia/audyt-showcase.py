from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os, sys, json, threading, time, argparse

R=Path(__file__).resolve().parent.parent
OUT=R/'.audit-showcase'; OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'narzedzia'))
from cdp import Karta
ap=argparse.ArgumentParser(); ap.add_argument('--live',action='store_true'); ap.add_argument('--screens-only',action='store_true'); args=ap.parse_args()
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
httpd=None
if args.live:base='https://maciejgryziec.pl'
else:
 os.chdir(R);httpd=ThreadingHTTPServer(('127.0.0.1',0),Quiet);threading.Thread(target=httpd.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{httpd.server_address[1]}'
checks=[]
def check(name,ok,info=None):
 checks.append({'name':name,'ok':bool(ok),'info':info})
 if not ok:print('FAIL',name,info,flush=True)
def click(k,selector):
 js='''(()=>{const e=document.querySelector(SELECTOR);if(!e)return {error:'missing'};e.scrollIntoView({block:'center',inline:'center',behavior:'instant'});const r=e.getBoundingClientRect();const x=r.x+r.width/2,y=r.y+r.height/2;const top=document.elementFromPoint(x,y);return {x,y,hit:!!top&&(top===e||e.contains(top)),width:r.width,height:r.height}})()'''.replace('SELECTOR',json.dumps(selector))
 pt=k.js(js)
 if not pt or not pt.get('hit'):return pt
 k.cmd('Input.dispatchMouseEvent',type='mousePressed',x=pt['x'],y=pt['y'],button='left',clickCount=1)
 k.cmd('Input.dispatchMouseEvent',type='mouseReleased',x=pt['x'],y=pt['y'],button='left',clickCount=1)
 return pt
try:
 for width,height in ((1440,1000),(390,844)):
  k=Karta();k.ws.settimeout(12)
  try:
   k.rozmiar(width,height,1,width<500)
   k.cmd('Page.addScriptToEvaluateOnNewDocument',source="try{localStorage.setItem('umami.disabled','1')}catch(e){};window.__portfolioErrors=[];addEventListener('error',e=>window.__portfolioErrors.push(e.message));addEventListener('unhandledrejection',e=>window.__portfolioErrors.push(String(e.reason)))")
   k.cmd('Emulation.setEmulatedMedia',features=[{'name':'prefers-reduced-motion','value':'reduce'}])
   k.idz(base+'/?portfolio-qa='+str(time.time_ns()),1.2)
   info=k.js("(()=>{const h=document.querySelector('.hero-realizacje').getBoundingClientRect(),t=document.querySelector('.start h1').getBoundingClientRect();return {hero:h.toJSON(),title:t.toJSON(),overflow:document.documentElement.scrollWidth>innerWidth,main:document.querySelectorAll('main').length}})()")
   check(f'{width} hero width',info['hero']['width']> (width*.8 if width<500 else 500),info)
   check(f'{width} hero fits',info['hero']['left']>=0 and info['hero']['right']<=width+1,info)
   check(f'{width} title fits',info['title']['left']>=0 and info['title']['right']<=width+1,info)
   check(f'{width} structure',not info['overflow'] and info['main']==1,info)
   k.zrzut(str(OUT/f'home-after-{width}.jpg'),90)
   k.js("document.querySelector('.hero-realizacje').scrollIntoView({block:'center',behavior:'instant'})")
   k.zrzut(str(OUT/f'hero-after-{width}.jpg'),90)
   if not args.screens_only:
    for i in range(6):
     pt=click(k,f'.hero-projekt-nav button[data-to="{i}"]');check(f'{width} project {i} clickable',pt and pt.get('hit'),pt)
     active=k.js("document.querySelector('.hero-projekt.aktywny').dataset.project")
     check(f'{width} project {i} active',active==str(i),active)
     views=k.js("Array.from(document.querySelectorAll('.hero-projekt.aktywny .project-view-tabs button')).map(e=>e.dataset.view)") or []
     for view in views:
      selector=f'.hero-projekt.aktywny .project-view-tabs button[data-view="{view}"]'
      pt=click(k,selector);check(f'{width} {i}/{view} clickable',pt and pt.get('hit'),pt)
      state=k.js("""(async()=>{const s=document.querySelector('.hero-projekt.aktywny'),p=s.querySelector('.project-view.tu');await Promise.all(Array.from(p.querySelectorAll('img')).map(i=>i.decode().catch(()=>{})));return {view:p.dataset.view,hidden:p.hidden,display:getComputedStyle(p).display,broken:Array.from(p.querySelectorAll('img')).filter(i=>!i.currentSrc||!i.complete||i.naturalWidth===0).map(i=>i.getAttribute('src')),errors:window.__portfolioErrors}})()""")
      check(f'{width} {i}/{view} loaded',state and state['view']==view and not state['hidden'] and state['display']!='none' and not state['broken'] and not state['errors'],state)
     if i==1:
      click(k,'.hero-projekt.aktywny .project-view-tabs button[data-view="dashboard"]')
      k.zrzut(str(OUT/f'judler-after-{width}.jpg'),90)
    k.idz(base+'/realizacje.html?portfolio-qa='+str(time.time_ns()),1)
    groups=k.js("Array.from(document.querySelectorAll('.detail-showcase')).map(e=>({id:e.dataset.detail,views:Array.from(e.querySelectorAll('.detail-tabs button')).map(b=>b.dataset.view)}))")
    for group in groups:
     for view in group['views']:
      sel=f'.detail-showcase[data-detail="{group["id"]}"] .detail-tabs button[data-view="{view}"]'
      pt=click(k,sel);check(f'{width} detail {group["id"]}/{view} clickable',pt and pt.get('hit'),pt)
      result=k.js(('''(async()=>{const root=document.querySelector(ROOT),p=root.querySelector('.detail-panel.tu');await Promise.all(Array.from(p.querySelectorAll('img')).map(i=>i.decode().catch(()=>{})));return {view:p.dataset.view,width:p.getBoundingClientRect().width,broken:Array.from(p.querySelectorAll('img')).some(i=>!i.currentSrc||i.naturalWidth===0),errors:window.__portfolioErrors}})()''').replace('ROOT',json.dumps(f'.detail-showcase[data-detail="{group["id"]}"]')))
      check(f'{width} detail {group["id"]}/{view} loaded',result and result['view']==view and not result['broken'] and not result['errors'],result)
    k.js("document.getElementById('frankie').scrollIntoView({block:'start',behavior:'instant'})")
    k.zrzut(str(OUT/f'detail-frankie-{width}.jpg'),90)
   print('DONE',width,flush=True)
  finally:k.zamknij()
finally:
 if httpd:httpd.shutdown();httpd.server_close()
failed=[c for c in checks if not c['ok']]
report={'base':base,'checks':len(checks),'failures':failed,'results':checks}
(OUT/('live-showcase-results.json' if args.live else 'local-showcase-results.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('SUMMARY',len(checks),'checks;',len(failed),'failures',flush=True)
sys.exit(1 if failed else 0)
