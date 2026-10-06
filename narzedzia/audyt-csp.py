#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pełny crawl HTML pod przygotowaną produkcyjną Content-Security-Policy."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import contextlib
import os
import re
import sys
import threading

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from cdp import Karta
except Exception as exc:
    print("Nie można uruchomić CSP audit:", exc)
    sys.exit(2)

cfg = (ROOT / "deploy" / "nginx.conf").read_text(encoding="utf-8")
m = re.search(r'add_header Content-Security-Policy "([^"]+)" always;', cfg)
if not m:
    raise SystemExit("Brak CSP w deploy/nginx.conf")

# Lokalny audyt działa po HTTP. Ta dyrektywa na produkcji wymusza HTTPS, ale
# lokalnie podniosłaby również względne assety do https://127.0.0.1.
CSP = m.group(1).replace("; upgrade-insecure-requests", "")

if "'unsafe-inline'" in CSP.split("script-src", 1)[1].split(";", 1)[0]:
    raise SystemExit("script-src nadal zawiera unsafe-inline")

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, *args):
        pass

@contextlib.contextmanager
def server():
    old = os.getcwd()
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
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
    browser.cmd("Network.enable")
    browser.cmd(
        "Network.setBlockedURLs",
        urls=["*://statystyki.automatyzacjesklepow.pl/*"],
    )
    browser.cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        source="""
          try { localStorage.setItem('umami.disabled','1'); } catch(e) {}
          window.__csp=[]; window.__runtimeErrors=[];
          addEventListener('securitypolicyviolation', e => window.__csp.push({
            blocked:e.blockedURI, directive:e.effectiveDirective,
            source:e.sourceFile, line:e.lineNumber
          }));
          addEventListener('error', e => window.__runtimeErrors.push({
            type:'error', msg:e.message||String(e.error), src:e.filename||'', line:e.lineno||0
          }));
          addEventListener('unhandledrejection', e => window.__runtimeErrors.push({
            type:'rejection', msg:String(e.reason)
          }));
        """,
    )

    try:
        for i, page in enumerate(pages, 1):
            browser.idz(f"{base}/{page}?csp-audit=1", .28)
            result = browser.js("""(()=>({
              csp: window.__csp || [],
              errors: window.__runtimeErrors || [],
              enhanced: document.documentElement.classList.contains('js'),
              inlineHandlers: [...document.querySelectorAll('*')].some(el =>
                [...el.attributes].some(a => /^on/i.test(a.name))
              )
            }))()""")
            ok = not result["csp"] and not result["errors"] and result["enhanced"] and not result["inlineHandlers"]
            print(
                f"[{'OK' if ok else 'FAIL'}] {i:02d}/{len(pages)} {page} "
                f"csp={len(result['csp'])} errors={len(result['errors'])} enhanced={result['enhanced']}"
            )
            if not ok:
                issues.append((page, result))
    finally:
        browser.zamknij()

print(f"\nCSP crawl: {len(pages)} stron, błędy: {len(issues)}")
if issues:
    for page, result in issues:
        print(" -", page, result)
    sys.exit(1)

print("OK — wszystkie strony działają pod produkcyjną CSP bez unsafe-inline; dozwolony jest tylko hashowany bootstrap.")
