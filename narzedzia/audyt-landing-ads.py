#!/usr/bin/env python3
"""Focused landing-page checks. Local files, isolated browser, analytics disabled."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
import json, threading, time, sys
from cdp import Karta
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.audit-landing-ads';OUT.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_): pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(server.server_port)
checks=[]
try:
    for page in ['kalkulator-konfigurator-dla-klientow','crm-na-zamowienie','integracje-api-dla-firm']:
        for width,height in [(1440,1000),(390,844)]:
            k=Karta()
            try:
                k.rozmiar(width,height,1,width<500)
                k.cmd('Page.addScriptToEvaluateOnNewDocument',source="try{localStorage.setItem('umami.disabled','1')}catch(e){};window.__errors=[];addEventListener('error',e=>__errors.push(e.message));")
                k.idz(base+'/'+page+'.html',1)
                k.js("document.querySelectorAll('.wjazd').forEach(e=>e.classList.add('widac'))")
                data=k.js("""(()=>{const e=document.querySelector('.hero-actions'),a=e.querySelector('a'),r=e.getBoundingClientRect(),ar=a.getBoundingClientRect();return {title:document.title,h1:document.querySelector('h1').textContent,h1Count:document.querySelectorAll('h1').length,overflow:document.documentElement.scrollWidth>innerWidth,cta:{top:r.top,left:r.left,right:r.right,height:ar.height,href:a.getAttribute('href')},proof:e.querySelector('.landing-proof-link').getAttribute('href'),errors:__errors,canonical:document.querySelector('link[rel=canonical]').href};})()""")
                ok=data['h1Count']==1 and not data['overflow'] and not data['errors'] and data['cta']['height']>=44 and data['cta']['left']>=0 and data['cta']['right']<=width+1
                checks.append({'page':page,'width':width,'ok':ok,'data':data})
                k.zrzut(str(OUT/(page+'-'+str(width)+'.jpg')),75)
                print(page,width,'OK' if ok else 'FAIL',json.dumps(data,ensure_ascii=False))
            finally:k.zamknij()
finally:server.shutdown();server.server_close()
(OUT/'results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
sys.exit(any(not c['ok'] for c in checks))
