# -*- coding: utf-8 -*-
"""Smoke test produkcji po wdrożeniu. Nie zmienia żadnego stanu."""
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
import sys

APEX = "https://maciejgryziec.pl"
WWW = "https://www.maciejgryziec.pl"
CHECKER = "https://sprawdzarka.automatyzacjesklepow.pl"
ANALYTICS = "https://statystyki.automatyzacjesklepow.pl"
BOOTSTRAP_HASH = "sha256-9h4+QNjOt3CgNFpdn6iqbeII0Hyi4PqjGT1QhTZFYlc="

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = build_opener(NoRedirect)
failures = []

def request(url, method="GET", extra_headers=None):
    headers={"User-Agent": "site-smoke-test/1.1"}
    if extra_headers:
        headers.update(extra_headers)
    req = Request(url, headers=headers, method=method)
    try:
        r = opener.open(req, timeout=12)
        body = r.read(300000)
        return r.status, r.headers, body
    except HTTPError as e:
        body = e.read(300000)
        return e.code, e.headers, body
    except URLError as e:
        failures.append(f"{url}: błąd połączenia: {e}")
        return 0, {}, b""

def check(label, ok, detail):
    mark = "OK" if ok else "FAIL"
    print(f"[{mark}] {label}: {detail}")
    if not ok:
        failures.append(f"{label}: {detail}")

# Główna wersja strony.
status, headers, body = request(APEX + "/")
check("strona główna", status == 200, f"HTTP {status}")
text = body.decode("utf-8", "replace")
check("nowa wersja strony", "Opisz projekt" in text and "Aplikacje," in text and "Przykłady programów" in text, "CTA, hero i realizacje")
check("brak statycznego trackera Umami", "statystyki.automatyzacjesklepow.pl/script.js" not in text, "tracker ładowany warunkowo z list.js")

# Canonical host.
status, headers, _ = request(WWW + "/test-redirect")
location = headers.get("Location", "")
check("www → apex", status in (301, 308) and location.startswith(APEX + "/test-redirect"), f"HTTP {status}, Location={location or 'brak'}")

status, health_headers, health_body = request(APEX + "/healthz")
check("main healthz", status == 200 and health_body.strip() == b"ok", f"HTTP {status}, body={health_body[:20]!r}")

# Publiczne pliki techniczne, które mają istnieć.
for path, label in (
    ("/.well-known/security.txt", "security.txt"),
    ("/og-image.png", "OG image"),
    ("/feed.xml", "Atom feed"),
    ("/llms.txt", "llms.txt"),
    ("/site.webmanifest", "manifest"),
    ("/sitemap.xml", "sitemap"),
):
    status, _, _ = request(APEX + path)
    check(label, status == 200, f"HTTP {status}")

# Repo/development nie może być publiczne po deployu.
for path in (
    "/zrodla/index.html",
    "/narzedzia/buduj-nowa.py",
    "/.github/workflows/site-audit.yml",
    "/README.md",
    "/CHECKLIST-PRODUKCJA.md",
    "/DEPLOY-PLAN.md",
    "/RELEASE-SCOPE.md",
    "/deploy/nginx.conf",
):
    status, _, _ = request(APEX + path)
    check("ukryty plik " + path, status == 404, f"HTTP {status}")

# Własna strona 404 ma zachować kod 404 i własną treść.
status, _, body404 = request(APEX + "/__smoke-nie-istnieje-20261003")
body404_text = body404.decode("utf-8", "replace")
check("custom 404 status", status == 404, f"HTTP {status}")
check("custom 404 body", "Tej strony tutaj nie ma" in body404_text, "własny komunikat")

# Zależności zewnętrzne strony.
status, _, checker_body = request(CHECKER + "/")
check("sprawdzarka subdomena", status == 200, f"HTTP {status}")
checker_text = checker_body.decode("utf-8", "replace")
check("sprawdzarka retencja 30 dni", "automatycznie usuwane po 30 dniach" in checker_text, "jawna informacja o retencji")
check("sprawdzarka bez zbędnego e-maila", 'name="email"' not in checker_text, "formularz nie zbiera nieużywanego adresu e-mail")
status, _, _ = request(CHECKER + "/", method="HEAD")
check("sprawdzarka HEAD /", status == 200, f"HTTP {status}")
status, health_headers, health_body = request(CHECKER + "/healthz")
check("sprawdzarka healthz", status == 200 and b'"status":"ok"' in health_body.replace(b" ", b""), f"HTTP {status}")
check("sprawdzarka healthz noindex", "noindex" in health_headers.get("X-Robots-Tag", ""), health_headers.get("X-Robots-Tag", "brak"))
status, checker_headers, _ = request(CHECKER + "/sprawdz", method="OPTIONS")
allow = checker_headers.get("Allow", "")
check("sprawdzarka endpoint POST", status == 405 and "POST" in allow.upper(), f"HTTP {status}, Allow={allow or 'brak'}")
status, checker_security_headers, checker_security_body = request(CHECKER + "/.well-known/security.txt")
check("sprawdzarka security.txt", status == 200 and b"Contact: mailto:kontakt@automatyzacjesklepow.pl" in checker_security_body, f"HTTP {status}")
for path in ("/docs", "/redoc", "/openapi.json"):
    status, _, _ = request(CHECKER + path)
    check("sprawdzarka ukryte API docs " + path, status == 404, f"HTTP {status}")

status, analytics_headers, _ = request(ANALYTICS + "/script.js")
check("Umami script", status == 200, f"HTTP {status}, Cache-Control={analytics_headers.get('Cache-Control','brak')}")
status, _, list_js_body = request(APEX + "/list.js")
list_js_text = list_js_body.decode("utf-8", "replace")
check(
    "Umami wyłączone na nowej domenie",
    status == 200
    and "Statystyki na maciejgryziec.pl są obecnie wyłączone." in list_js_text
    and "statystyki.automatyzacjesklepow.pl/script.js" not in list_js_text
    and "data-umami-loader" not in list_js_text,
    f"HTTP {status}",
)

# Nagłówki bezpieczeństwa.
status, headers, _ = request(APEX + "/")
header_expectations = {
    "Strict-Transport-Security": "HSTS",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "frame policy",
    "Cross-Origin-Opener-Policy": "COOP",
    "Referrer-Policy": "referrer policy",
    "Permissions-Policy": "permissions policy",
    "Content-Security-Policy": "content security policy",
}
for key, label in header_expectations.items():
    check(label, bool(headers.get(key)), headers.get(key, "brak"))

csp = headers.get("Content-Security-Policy", "")
script_src = ""
if "script-src " in csp:
    script_src = csp.split("script-src ", 1)[1].split(";", 1)[0]
check(
    "CSP script-src bez unsafe-inline",
    bool(script_src) and "'unsafe-inline'" not in script_src,
    script_src or "brak script-src",
)
check(
    "CSP bez zewnętrznego Umami",
    "'self'" in script_src and "https://statystyki.automatyzacjesklepow.pl" not in script_src,
    script_src or "brak script-src",
)
check(
    "CSP hash bootstrapa no-js→js",
    BOOTSTRAP_HASH in script_src,
    script_src or "brak script-src",
)

# Kompresja gzip dla tekstowych odpowiedzi.
for path, label in (("/", "HTML"), ("/list.css", "CSS"), ("/list.js", "JS")):
    status, h, _ = request(APEX + path, extra_headers={"Accept-Encoding": "gzip"})
    encoding = h.get("Content-Encoding", "")
    vary = h.get("Vary", "")
    check(
        "gzip " + label,
        status == 200 and encoding.lower() == "gzip" and "Accept-Encoding" in vary,
        f"HTTP {status}, Content-Encoding={encoding or 'brak'}, Vary={vary or 'brak'}",
    )

# Cache po konfiguracji nginx: HTML rewalidowany, assety długo cache'owane.
status, html_headers, _ = request(APEX + "/")
html_cache = html_headers.get("Cache-Control", "")
check("HTML rewalidacja", status == 200 and "no-cache" in html_cache, f"HTTP {status}, Cache-Control={html_cache or 'brak'}")
check("HTML ETag", bool(html_headers.get("ETag")), html_headers.get("ETag", "brak"))

for asset in ("/list.js", "/list.css"):
    status, h, _ = request(APEX + asset)
    cache = h.get("Cache-Control", "")
    check("długi cache " + asset, status == 200 and "max-age=31536000" in cache, f"HTTP {status}, Cache-Control={cache or 'brak'}")

for asset in ("/og-image.png", "/ikona-192.png"):
    status, h, _ = request(APEX + asset)
    cache = h.get("Cache-Control", "")
    check("cache obrazu " + asset, status == 200 and "max-age=2592000" in cache, f"HTTP {status}, Cache-Control={cache or 'brak'}")

# Gzip musi działać także za reverse proxy (Via).
for path in ("/", "/list.css", "/list.js"):
    status, h, _ = request(
        APEX + path,
        method="HEAD",
        extra_headers={"Accept-Encoding": "gzip", "Via": "1.1 site-smoke"},
    )
    encoding=h.get("Content-Encoding", "")
    vary=h.get("Vary", "")
    check(
        "gzip " + path,
        status == 200 and encoding.lower() == "gzip" and "Accept-Encoding" in vary,
        f"HTTP {status}, Content-Encoding={encoding or 'brak'}, Vary={vary or 'brak'}",
    )

if failures:
    print(f"\nNIEGOTOWE: {len(failures)} problemów.")
    for item in failures:
        print(" -", item)
    sys.exit(1)
print("\nPRODUKCJA OK — testy po wdrożeniu przeszły.")
