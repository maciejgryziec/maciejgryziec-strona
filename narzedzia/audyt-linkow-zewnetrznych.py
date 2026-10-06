# -*- coding: utf-8 -*-
"""Ręczny audyt zewnętrznych linków HTTP(S). Nie jest częścią CI, żeby chwilowa awaria obcej strony nie blokowała release'u."""
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
DOMAIN_SUFFIX = "automatyzacjesklepow.pl"

class Redirect(HTTPRedirectHandler):
    pass

opener = build_opener(Redirect)
urls = set()

for path in sorted(ROOT.glob("*.html")):
    src = path.read_text(encoding="utf-8")
    for url in re.findall(r'(?:href|src)="(https://[^"]+)"', src):
        host = urlsplit(url).netloc.lower()
        if host.endswith(DOMAIN_SUFFIX):
            continue
        urls.add(url)

failures = []

for url in sorted(urls):
    req = Request(url, headers={"User-Agent": "external-link-audit/1.0"})
    try:
        response = opener.open(req, timeout=15)
        status = response.status
        final = response.geturl()
    except HTTPError as exc:
        status = exc.code
        final = exc.geturl()
    except URLError as exc:
        failures.append((url, f"connection error: {exc}"))
        print(f"[FAIL] {url} -> {exc}")
        continue

    ok = 200 <= status < 400
    print(f"[{'OK' if ok else 'FAIL'}] {status} {url}" + (f" -> {final}" if final != url else ""))
    if not ok:
        failures.append((url, f"HTTP {status}"))

print(f"\nExternal links: {len(urls)}, failures: {len(failures)}")
if failures:
    for url, reason in failures:
        print(" -", url, reason)
    sys.exit(1)
