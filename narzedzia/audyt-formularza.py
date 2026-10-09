#!/usr/bin/env python3
"""Isolated browser tests for direct delivery. Mail endpoints are mocked; sends no email."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
import json
import sys
import threading
import time
from cdp import Karta

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.audit-form';OUT.mkdir(exist_ok=True)
checks=[]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(server.server_port)

def check(name,ok,data=None):
    checks.append({'name':name,'ok':bool(ok),'data':data})
    if not ok:print('FAIL',name,data,flush=True)

try:
    for mode in ['success','failed','unknown','network','bad-confirmation','unconfigured']:
        k=Karta();k.ws.settimeout(15)
        try:
            k.rozmiar(390,844,1,True)
            source='''
            window.__mailCalls=[];window.__clipboardWrites=0;window.__formErrors=[];
            try{localStorage.setItem('umami.disabled','1')}catch(e){}
            addEventListener('error',e=>window.__formErrors.push(e.message));
            const fetchOriginal=window.fetch.bind(window);
            window.fetch=async function(url,opts){
              if(String(url)==='/api/contact/session')return new Response(JSON.stringify({ready:MODE!=='unconfigured',token:'test-browser-token'}),{status:200,headers:{'Content-Type':'application/json'}});
              if(String(url)==='/api/contact'){
                const payload=JSON.parse(opts.body);window.__mailCalls.push(payload);
                if(MODE==='network')throw new TypeError('simulated network failure');
                if(MODE==='success')return new Response(JSON.stringify({ok:true,status:'sent',request_id:payload.request_id}),{status:200,headers:{'Content-Type':'application/json'}});
                if(MODE==='bad-confirmation')return new Response(JSON.stringify({ok:true,status:'sent',request_id:'wrong-id'}),{status:200,headers:{'Content-Type':'application/json'}});
                return new Response(JSON.stringify({ok:false,code:MODE==='unknown'?'delivery_unknown':'delivery_failed',message:'Wiadomość nie została potwierdzona. Zachowaj opis.'}),{status:503,headers:{'Content-Type':'application/json'}});
              }
              return fetchOriginal(url,opts);
            };
            try{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async function(){window.__clipboardWrites++;}}});}catch(e){}
            '''.replace('MODE',json.dumps(mode))
            k.cmd('Page.addScriptToEvaluateOnNewDocument',source=source)
            k.idz(base+'/opisz-projekt.html',.7)
            label=k.js("document.querySelector('#brief-form button[type=submit]').textContent")
            if mode=='unconfigured':
                check('unconfigured keeps honest existing action','Przygotuj' in label,label)
                check('unconfigured sends nothing',k.js('window.__mailCalls.length')==0)
                continue
            check(mode+'/send label',label=='Wyślij',label)
            k.js('''(()=>{const f=document.getElementById('brief-form');const data={imie:'Osoba Testowa',email:'browser-test@example.org',typ:'Własna aplikacja / system',dzis:'Opis czynności testowej',problem:'Powtarzalne zadanie',efekt:'Oczekiwany efekt'};Object.keys(data).forEach(k=>{f.elements[k].value=data[k];});f.dispatchEvent(new Event('input',{bubbles:true}));f.requestSubmit();f.requestSubmit();})()''')
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                state=k.js("(()=>{const f=document.getElementById('brief-form'),b=f.querySelector('button[type=submit]');return {label:b.textContent,disabled:b.disabled,message:document.getElementById('brief-info').textContent,fields:f.elements.dzis.value,calls:window.__mailCalls.length,url:location.href,clipboard:window.__clipboardWrites,errors:window.__formErrors,overflow:document.documentElement.scrollWidth>innerWidth};})()")
                if state and state['label']!='Wysyłanie...' and state['calls']:break
                time.sleep(.2)
            check(mode+'/single request',state['calls']==1,state)
            check(mode+'/no mail-client navigation',state['url']==base+'/opisz-projekt.html',state['url'])
            check(mode+'/no automatic clipboard',state['clipboard']==0,state['clipboard'])
            check(mode+'/no errors or overflow',not state['errors'] and not state['overflow'],state)
            if mode=='success':
                check('success clears draft and confirms',state['label']=='Wysłano' and state['disabled'] and not state['fields'] and 'została wysłana' in state['message'],state)
                check('success no saved personal draft',k.js("sessionStorage.getItem('briefDraft')") is None)
            else:
                check(mode+'/no false success',state['label']=='Wyślij' and not state['disabled'] and 'została wysłana' not in state['message'] and bool(state['fields']),state)
            print('FORM',mode,'checked',flush=True)
        finally:k.zamknij()
finally:
    server.shutdown();server.server_close()
failed=[x for x in checks if not x['ok']]
(OUT/'results.json').write_text(json.dumps({'checks':len(checks),'failures':failed,'results':checks,'mail_was_mocked':True},ensure_ascii=False,indent=2))
print('DIRECT FORM',len(checks),'checks;',len(failed),'failures; no real email sent')
sys.exit(bool(failed))
