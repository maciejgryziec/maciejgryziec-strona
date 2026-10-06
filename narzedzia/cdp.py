import json, subprocess, time, base64, urllib.request, websocket
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT=9455
def start():
    try: urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1); return
    except Exception: pass
    subprocess.Popen([CH,"--headless=new","--disable-gpu","--hide-scrollbars",f"--remote-debugging-port={PORT}","--remote-allow-origins=*","--user-data-dir=/tmp/cdp-prof-9455","--window-size=1440,900","about:blank"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(50):
        try: urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1); return
        except Exception: time.sleep(0.2)
class Karta:
    def __init__(self):
        start()
        req=urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?about:blank", method="PUT"); t=json.load(urllib.request.urlopen(req))
        self.ws=websocket.create_connection(t["webSocketDebuggerUrl"]); self.n=0; self.id=t["id"]
        self.cmd("Page.enable"); self.cmd("Runtime.enable")
    def cmd(self,m,**p):
        self.n+=1; self.ws.send(json.dumps({"id":self.n,"method":m,"params":p}))
        while True:
            r=json.loads(self.ws.recv())
            if r.get("id")==self.n: return r.get("result",r)
    def rozmiar(self,w,h,dpr=1,mobile=False): self.cmd("Emulation.setDeviceMetricsOverride",width=w,height=h,deviceScaleFactor=dpr,mobile=mobile)
    def idz(self,url,czekaj=1.5): self.cmd("Page.navigate",url=url); time.sleep(czekaj)
    def js(self,kod):
        r=self.cmd("Runtime.evaluate",expression=kod,returnByValue=True,awaitPromise=True); return r.get("result",{}).get("value")
    def zrzut(self,sciezka,q=80):
        d=self.cmd("Page.captureScreenshot",format="jpeg",quality=q)["data"]; open(sciezka,"wb").write(base64.b64decode(d))
    def zamknij(self): urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/close/{self.id}")
