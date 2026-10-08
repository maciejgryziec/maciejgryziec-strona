# -*- coding: utf-8 -*-
"""Pełny crawl wszystkich wygenerowanych stron w lokalnym Chrome: JS errors, obrazy, overflow."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import contextlib
import os
import sys
import threading

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from cdp import Karta
except Exception as exc:
    print("Nie można uruchomić Chrome runtime audit:", exc)
    sys.exit(2)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

@contextlib.contextmanager
def server():
    old = os.getcwd()
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        os.chdir(old)

pages = sorted(p.name for p in ROOT.glob("*.html"))
issues = []

with server() as base:
    browser = Karta()
    browser.rozmiar(1100, 850, 1, False)
    browser.cmd("Page.addScriptToEvaluateOnNewDocument", source="""
        window.__runtimeErrors=[];
        addEventListener('error', e => window.__runtimeErrors.push({
          type:'error', msg:e.message||String(e.error), src:e.filename||'', line:e.lineno||0
        }));
        addEventListener('unhandledrejection', e => window.__runtimeErrors.push({
          type:'rejection', msg:String(e.reason)
        }));
    """)

    try:
        for i, page in enumerate(pages, 1):
            browser.idz(f"{base}/{page}?runtime-audit=1", .25)
            result = browser.js("""(()=>({
              errors: window.__runtimeErrors || [],
              broken: [...document.images].filter(i=>!i.hasAttribute("data-carousel-src")&&!i.hasAttribute("data-project-src")&&i.complete&&i.naturalWidth===0).map(i=>i.currentSrc||i.getAttribute("src")||""),
              overflow: document.documentElement.scrollWidth > innerWidth
            }))()""")
            ax = browser.cmd("Accessibility.getFullAXTree").get("nodes", [])
            unnamed = []
            interactive = {"button","link","textbox","searchbox","combobox","checkbox","radio","switch","slider"}
            for node in ax:
                if node.get("ignored"):
                    continue
                role = ((node.get("role") or {}).get("value") or "").lower()
                name = ((node.get("name") or {}).get("value") or "").strip()
                if role in interactive and not name:
                    unnamed.append(role)
            result["unnamedAX"] = unnamed
            ok = not result["errors"] and not result["broken"] and not result["overflow"] and not unnamed
            print(f"[{'OK' if ok else 'FAIL'}] {i:02d}/{len(pages)} {page} "
                  f"errors={len(result['errors'])} broken={len(result['broken'])} overflow={result['overflow']} axUnnamed={len(unnamed)}")
            if not ok:
                issues.append((page, result))
    finally:
        browser.zamknij()

print(f"\nRuntime crawl: {len(pages)} stron, błędy: {len(issues)}")
if issues:
    for page, result in issues:
        print(" -", page, result)
    sys.exit(1)

print("OK — wszystkie strony przeszły runtime crawl w Chrome.")
