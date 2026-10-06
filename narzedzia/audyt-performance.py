# -*- coding: utf-8 -*-
"""Lokalny performance gate dla cold-start mobile.

To nie jest CI: czas renderowania zależy od hosta, więc używamy go przed większym
release'em. Profil: 390x844, 100 ms RTT, ~1.6 Mb/s download, CPU x4, cache off.
"""

from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
import statistics
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Karta  # noqa: E402

PAGES = [
    "index.html",
    "realizacje.html",
    "cennik.html",
    "opisz-projekt.html",
    "kalkulator-kosztu-recznej-pracy.html",
]

LCP_LIMIT_MS = 3200
CLS_LIMIT = 0.10
TRANSFER_LIMIT = 200_000
RUNS = 2


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


old_cwd = os.getcwd()
os.chdir(ROOT)
httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
thread = threading.Thread(target=httpd.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{httpd.server_address[1]}"

issues = []

try:
    for page in PAGES:
        rows = []
        for run in range(RUNS):
            valid = None
            for attempt in range(3):
                k = Karta()
                k.rozmiar(390, 844, 1, True)
                k.cmd("Network.enable")
                k.cmd("Network.clearBrowserCache")
                k.cmd("Network.setCacheDisabled", cacheDisabled=True)
                k.cmd(
                    "Network.emulateNetworkConditions",
                    offline=False,
                    latency=100,
                    downloadThroughput=200000,
                    uploadThroughput=100000,
                    connectionType="cellular4g",
                )
                k.cmd("Emulation.setCPUThrottlingRate", rate=4)
                k.cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    source="""
                      window.__vitals={lcp:0,cls:0,url:''};
                      try {
                        new PerformanceObserver((list)=>{
                          for (const e of list.getEntries()) {
                            window.__vitals.lcp=e.startTime;
                            window.__vitals.url=e.url||'';
                          }
                        }).observe({type:'largest-contentful-paint',buffered:true});
                      } catch(e) {}
                      try {
                        new PerformanceObserver((list)=>{
                          for (const e of list.getEntries()) {
                            if(!e.hadRecentInput) window.__vitals.cls+=e.value;
                          }
                        }).observe({type:'layout-shift',buffered:true});
                      } catch(e) {}
                    """,
                )
                try:
                    expected = "/" + page
                    k.idz(base + expected + f"?perf-audit={run}-{attempt}-{time.time_ns()}", .15)
                    deadline = time.monotonic() + 8.0
                    row = None
                    while time.monotonic() < deadline:
                        time.sleep(.4)
                        row = k.js(
                            """(()=>{
                              const paints=performance.getEntriesByType('paint');
                              const resources=performance.getEntriesByType('resource');
                              const fcp=Math.round((paints.find(x=>x.name==='first-contentful-paint')||{}).startTime||0);
                              const rawLcp=Math.round(window.__vitals.lcp||0);
                              const resourceByUrl=new Map(resources.map(e=>[e.name,e]));
                              let aboveFoldImageEnd=0;
                              [...document.images].forEach(img=>{
                                const r=img.getBoundingClientRect();
                                if(!img.currentSrc || r.bottom<=0 || r.top>=innerHeight) return;
                                const entry=resourceByUrl.get(img.currentSrc);
                                if(entry) aboveFoldImageEnd=Math.max(aboveFoldImageEnd,Math.round(entry.responseEnd||0));
                              });
                              const effectiveLcp=rawLcp||Math.max(fcp,aboveFoldImageEnd);
                              return {
                                fcp:fcp,
                                lcp:effectiveLcp,
                                lcpRaw:rawLcp,
                                lcpFallback:rawLcp===0,
                                aboveFoldImageEnd:aboveFoldImageEnd,
                                cls:+(window.__vitals.cls||0).toFixed(4),
                                transfer:resources.reduce((a,e)=>a+(e.transferSize||0),0),
                                resources:resources.length,
                                rentalRequests:resources.filter(e=>e.name.includes('wypozyczalnia-flota')).length,
                                path:location.pathname,
                                ready:document.readyState
                              };
                            })()"""
                        )
                        if (
                            row.get("path") == expected
                            and row.get("ready") == "complete"
                            and row.get("fcp", 0) > 0
                            and row.get("lcp", 0) > 0
                            and row.get("resources", 0) > 0
                            and row.get("transfer", 0) > 0
                        ):
                            valid = row
                            break
                    if valid is not None:
                        break
                finally:
                    k.zamknij()
            if valid is None:
                issues.append(f"{page}: nie udało się uzyskać prawidłowego pomiaru cold-start")
                print(f"[FAIL] {page}: brak prawidłowego pomiaru po 3 próbach")
                continue
            rows.append(valid)

        if len(rows) != RUNS:
            continue

        # 2 runy: bierzemy gorszy timing jako prosty bufor przeciw przypadkowemu "zielonemu".
        lcp = max(r["lcp"] for r in rows)
        fcp = max(r["fcp"] for r in rows)
        cls = max(r["cls"] for r in rows)
        transfer = max(r["transfer"] for r in rows)
        resources = max(r["resources"] for r in rows)
        fallback_count = sum(1 for r in rows if r.get("lcpFallback"))

        ok = lcp <= LCP_LIMIT_MS and cls <= CLS_LIMIT and transfer <= TRANSFER_LIMIT
        if page == "realizacje.html":
            ok = ok and max(r["rentalRequests"] for r in rows) == 0

        print(
            f"[{'OK' if ok else 'FAIL'}] {page}: "
            f"FCP<={fcp}ms LCP<={lcp}ms CLS={cls:.4f} "
            f"transfer={transfer}B resources={resources} "
            f"lcp-fallback={fallback_count}/{RUNS}"
        )
        if page == "realizacje.html":
            print(
                "     nieaktywna karta wypożyczalni requests=",
                max(r["rentalRequests"] for r in rows),
            )

        if lcp > LCP_LIMIT_MS:
            issues.append(f"{page}: LCP {lcp}ms > {LCP_LIMIT_MS}ms")
        if cls > CLS_LIMIT:
            issues.append(f"{page}: CLS {cls:.4f} > {CLS_LIMIT}")
        if transfer > TRANSFER_LIMIT:
            issues.append(f"{page}: transfer {transfer}B > {TRANSFER_LIMIT}B")
        if page == "realizacje.html" and max(r["rentalRequests"] for r in rows) != 0:
            issues.append("realizacje.html: nieaktywna karta pobierana przed kliknięciem")
finally:
    httpd.shutdown()
    httpd.server_close()
    os.chdir(old_cwd)

print()
if issues:
    print(f"Performance gate: {len(issues)} problemów")
    for issue in issues:
        print(" -", issue)
    raise SystemExit(1)

print("Performance gate OK.")
