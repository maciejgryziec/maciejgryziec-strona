# -*- coding: utf-8 -*-
"""Lekki quality gate dla statycznej strony. Tylko biblioteka standardowa."""
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "zrodla"
DOMAIN = "https://maciejgryziec.pl"
BOOTSTRAP_JS = 'document.documentElement.classList.remove("no-js");document.documentElement.classList.add("js");'
BOOTSTRAP_HASH = "'sha256-9h4+QNjOt3CgNFpdn6iqbeII0Hyi4PqjGT1QhTZFYlc='"
errors = []
warnings = []

def err(page, msg):
    errors.append(f"{page}: {msg}")

def text_meta(src, pattern):
    m = re.search(pattern, src, re.I | re.S)
    return html.unescape(m.group(1).strip()) if m else ""

pages = sorted(ROOT.glob("*.html"))
titles = {}
descriptions = {}
canonicals = {}

for path in pages:
    src = path.read_text(encoding="utf-8")
    name = path.name
    title = text_meta(src, r"<title>(.*?)</title>")
    desc = text_meta(src, r'<meta\s+name="description"\s+content="([^"]*)"')
    canonical = text_meta(src, r'<link\s+rel="canonical"\s+href="([^"]+)"')
    titles.setdefault(title, []).append(name)
    descriptions.setdefault(desc, []).append(name)
    canonicals.setdefault(canonical, []).append(name)

    og_title = text_meta(src, r'<meta\s+property="og:title"\s+content="([^"]*)"')
    og_desc = text_meta(src, r'<meta\s+property="og:description"\s+content="([^"]*)"')
    og_url = text_meta(src, r'<meta\s+property="og:url"\s+content="([^"]*)"')
    if og_title and og_title != title:
        err(name, "og:title różni się od title")
    if og_desc and og_desc != desc:
        err(name, "og:description różni się od description")
    if og_url and og_url != canonical:
        err(name, f"og:url różni się od canonical: {og_url} != {canonical}")

    if len(re.findall(r"<h1\b", src, re.I)) != 1:
        err(name, "oczekiwano dokładnie jednego H1")
    if not (25 <= len(title) <= 70):
        err(name, f"długość title={len(title)}")
    if not (70 <= len(desc) <= 175):
        err(name, f"długość description={len(desc)}")
    if not canonical.startswith(DOMAIN):
        err(name, "brak lub błędny canonical")

    for required in (
        'property="og:title"', 'property="og:description"', 'property="og:url"',
        'property="og:image"', 'property="og:image:type"', 'property="og:image:alt"',
        'name="twitter:card"', 'name="twitter:image:alt"', 'rel="manifest"'
    ):
        if required not in src:
            err(name, f"brak meta: {required}")

    og_image = text_meta(src, r'<meta\s+property="og:image"\s+content="([^"]+)"')
    if og_image.startswith(DOMAIN):
        og_path = urlsplit(og_image).path.lstrip("/")
        if not (ROOT / og_path).exists():
            err(name, f"lokalny og:image nie istnieje: {og_path}")
    og_w = text_meta(src, r'<meta\s+property="og:image:width"\s+content="([^"]+)"')
    og_h = text_meta(src, r'<meta\s+property="og:image:height"\s+content="([^"]+)"')
    if not (og_w.isdigit() and og_h.isdigit() and int(og_w) > 0 and int(og_h) > 0):
        err(name, f"niepoprawne wymiary og:image: {og_w}x{og_h}")

    ld = re.search(r'<script\s+type="application/ld\+json">(.*?)</script>', src, re.S | re.I)
    if not ld:
        err(name, "brak JSON-LD")
    else:
        try:
            json.loads(ld.group(1))
        except Exception as exc:
            err(name, f"niepoprawny JSON-LD: {exc}")

    if 'list.css?w=' in src or 'list.js?w=' in src:
        err(name, "stary statyczny numer wersji CSS/JS zamiast hasha")
    if not re.search(r'list\.css\?v=[0-9a-f]{10}', src):
        err(name, "brak hashowanej wersji list.css")
    if not re.search(r'list\.js\?v=[0-9a-f]{10}', src):
        err(name, "brak hashowanej wersji list.js")

    # Jedyny wykonywalny inline JS to ściśle hashowany bootstrap no-js -> js.
    bootstrap_count = 0
    for script in re.finditer(r'<script([^>]*)>(.*?)</script>', src, re.S | re.I):
        attrs = script.group(1)
        if "src=" in attrs.lower().replace(" ", ""):
            continue
        typ = text_meta(attrs, r'type="([^"]+)"').lower()
        if typ == "application/ld+json":
            continue
        body = script.group(2).strip()
        if body == BOOTSTRAP_JS:
            bootstrap_count += 1
        else:
            err(name, "niedozwolony wykonywalny inline <script>")
    if bootstrap_count != 1:
        err(name, f"liczba bootstrapów no-js→js={bootstrap_count}, oczekiwano 1")
    inline_handler = re.search(
        r'\s(on(?:click|change|input|submit|load|error|keydown|keyup))="',
        src,
        re.I,
    )
    if inline_handler:
        err(name, f"inline event handler: {inline_handler.group(1)}")

    # Podstawowe etykiety elementów interaktywnych.
    for button in re.findall(r'<button\b[^>]*>.*?</button>', src, re.I | re.S):
        visible = re.sub(r'<[^>]+>', '', button).strip()
        if not visible and not re.search(r'aria-label="[^"]+"', button, re.I):
            err(name, f"button bez nazwy dostępnej: {button[:100]}")
    for input_tag in re.findall(r'<input\b[^>]*>', src, re.I):
        typ = text_meta(input_tag, r'type="([^"]+)"').lower() or "text"
        if typ in {"hidden", "submit", "button"}:
            continue
        iid = text_meta(input_tag, r'id="([^"]+)"')
        named = bool(re.search(r'aria-label="[^"]+"|aria-labelledby="[^"]+"', input_tag, re.I))
        labelled = bool(iid and re.search(rf'<label[^>]*for="{re.escape(iid)}"', src, re.I))
        wrapped = bool(re.search(r'<label[^>]*>.*?'+re.escape(input_tag)+r'.*?</label>', src, re.I | re.S))
        if not (named or labelled or wrapped):
            err(name, f"input bez label: {input_tag[:100]}")

    # Hierarchia nagłówków: dokładnie jeden H1 i brak skoków np. H1 -> H3.
    headings=[int(x) for x in re.findall(r'<h([1-6])\b', src, re.I)]
    if headings.count(1) != 1:
        err(name, f"liczba H1={headings.count(1)}, oczekiwano 1")
    previous=0
    for level in headings:
        if previous and level > previous + 1:
            err(name, f"skok hierarchii nagłówków H{previous} -> H{level}")
            break
        previous=level

    ids = re.findall(r'\bid="([^"]+)"', src)
    dup_ids = sorted({x for x in ids if ids.count(x) > 1})
    if dup_ids:
        err(name, f"duplikaty id: {dup_ids}")

    for tag, ref in re.findall(r'\b(href|src)="([^"]+)"', src):
        if ref.startswith(("mailto:", "tel:", "data:", "javascript:")):
            continue
        parsed = urlsplit(ref)
        if parsed.scheme in ("http", "https"):
            continue
        target_name = parsed.path
        target = path if not target_name else ROOT / target_name
        if not target.exists():
            err(name, f"brak zasobu {tag}={ref}")
            continue
        if tag == "href" and parsed.fragment and target.suffix.lower() == ".html":
            target_src = target.read_text(encoding="utf-8")
            frag = re.escape(parsed.fragment)
            if not re.search(rf'\bid="{frag}"', target_src):
                err(name, f"brak kotwicy {ref}")

    for img in re.findall(r"<img\b[^>]*>", src, re.I):
        if 'src="zdjecia/' in img:
            if 'width="' not in img or 'height="' not in img:
                err(name, f"obraz bez width/height: {img[:100]}")
            if 'alt="' not in img:
                err(name, "obraz bez alt")

for value, files in titles.items():
    if value and len(files) > 1:
        err("META", f"duplikat title w {files}")
for value, files in descriptions.items():
    if value and len(files) > 1:
        err("META", f"duplikat description w {files}")
for value, files in canonicals.items():
    if value and len(files) > 1:
        err("META", f"duplikat canonical w {files}: {value}")

# Każde źródło HTML musi mieć wygenerowany odpowiednik w katalogu głównym.
source_pages = sorted(SOURCE.glob("*.html"))
for source_page in source_pages:
    generated = ROOT / source_page.name
    if not generated.exists():
        err("BUILD", f"brak wygenerowanej strony dla {source_page.name}")
for generated in pages:
    if not (SOURCE / generated.name).exists():
        err("BUILD", f"wygenerowany HTML bez źródła: {generated.name}")


# noindex ma być wyłącznie na stronach błędów.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    has_noindex=bool(re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex',txt,re.I))
    if pth.name in {"404.html","50x.html"}:
        if not has_noindex:
            err(pth.name,"brak noindex")
    elif has_noindex:
        err(pth.name,"nieoczekiwany noindex")

# Spójność publicznego cennika — historyczne widełki nie mogą wrócić.
legacy_patterns = [
    (r"4\s?500\s*[–-]\s*6\s?000\s*zł", "historyczne widełki 4 500–6 000 zł"),
    (r"\bMost do księgowości\b", "stara nazwa pakietu Most do księgowości"),
    (r"\bPełny most\b", "stara nazwa Pełny most"),
]
for folder, fileset in (("ROOT", pages), ("SOURCE", sorted(SOURCE.glob("*.html")))):
    for pth in fileset:
        txt=pth.read_text(encoding="utf-8")
        for pattern,label in legacy_patterns:
            if re.search(pattern,txt,re.I):
                err(pth.name,f"{label} ({folder})")

# Format głównych cen używanych w komunikacji sprzedażowej.
for pth in list(pages) + sorted(SOURCE.glob("*.html")):
    txt=pth.read_text(encoding="utf-8")
    if re.search(r"(?<!\d)1200\s*zł",txt):
        err(pth.name,"użyj formatu 1 200 zł zamiast 1200 zł")
    if re.search(r"(?<!\d)2900\s*zł",txt):
        err(pth.name,"użyj formatu 2 900 zł zamiast 2900 zł")

# Kanoniczna strona główna to /, nie /index.html.
for pth in list(pages) + sorted(SOURCE.glob("*.html")):
    txt=pth.read_text(encoding="utf-8")
    if re.search(r'href="index\.html(?:[#?][^"]*)?"',txt):
        err(pth.name,"wewnętrzny link do index.html zamiast / lub właściwej podstrony")

# Aktualność bloków ze źródłami prawnymi/urzędowymi.
for pth in sorted(SOURCE.glob("*.html")):
    txt=pth.read_text(encoding="utf-8")
    if 'class="zrodla-box"' not in txt:
        continue
    boxes=re.findall(r'<div class="zrodla-box"([^>]*)>',txt,re.I)
    for attrs in boxes:
        m=re.search(r'data-verified="(\d{4}-\d{2}-\d{2})"',attrs)
        if not m:
            err(pth.name,"zrodla-box bez data-verified")
            continue
        try:
            checked=datetime.strptime(m.group(1),"%Y-%m-%d").date()
            age=(datetime.now(timezone.utc).date()-checked).days
            if age>365:
                err(pth.name,f"źródła niezweryfikowane od {age} dni")
            elif age>180:
                warnings.append(f"{pth.name}: źródła weryfikowane {age} dni temu")
        except ValueError:
            err(pth.name,f"niepoprawna data data-verified: {m.group(1)}")

# Sekrety i lokalne ścieżki nie mogą trafić do publicznych artefaktów.
secret_patterns = [
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "private key"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"gh[pousr]_[A-Za-z0-9_]{30,}", "GitHub token"),
    (r"sk-[A-Za-z0-9]{20,}", "API key sk-..."),
    (r"xox[baprs]-[A-Za-z0-9-]{20,}", "Slack token"),
    (r"AIza[0-9A-Za-z_-]{30,}", "Google API key"),
]
public_text_files = list(pages) + [ROOT / "list.css", ROOT / "list.js", ROOT / "robots.txt", ROOT / "sitemap.xml", ROOT / "feed.xml", ROOT / "llms.txt"]
for pth in public_text_files:
    if not pth.exists():
        continue
    txt=pth.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"/(?:Users|home)/[^/\s]+/", txt):
        err(pth.name,"publiczny plik zawiera lokalną ścieżkę użytkownika")
    for pattern,label in secret_patterns:
        if re.search(pattern,txt):
            err(pth.name,f"podejrzenie sekretu: {label}")

# Skan źródeł repo (tekstowych) przed pushem — obrazy i .git pomijamy.
scan_ext = {".py",".sh",".yml",".yaml",".md",".txt",".html",".css",".js",".xml",".json",".conf"}
for pth in ROOT.rglob("*"):
    if not pth.is_file() or ".git" in pth.parts or pth.suffix.lower() not in scan_ext:
        continue
    try:
        txt=pth.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    for pattern,label in secret_patterns:
        if re.search(pattern,txt):
            err(str(pth.relative_to(ROOT)),f"podejrzenie sekretu w repo: {label}")

# Graf linkowania wewnętrznego: brak sierot i maks. 3 kliknięcia od strony głównej.
page_map = {p.name: p for p in pages}
internal_links = defaultdict(set)
inbound_links = defaultdict(set)
for pth in pages:
    txt = pth.read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"]+)"', txt, re.I):
        if href.startswith(("mailto:", "tel:", "http://", "https://", "#", "javascript:")):
            continue
        parsed = urlsplit(href)
        path = parsed.path
        if path in ("", "/"):
            target = "index.html"
        else:
            target = path.lstrip("/")
            if target not in page_map and target + ".html" in page_map:
                target += ".html"
        if target in page_map and target != pth.name:
            internal_links[pth.name].add(target)
            inbound_links[target].add(pth.name)

indexable = set()
for pth in pages:
    txt = pth.read_text(encoding="utf-8")
    if not re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', txt, re.I):
        indexable.add(pth.name)

depth = {"index.html": 0}
queue = deque(["index.html"])
while queue:
    current = queue.popleft()
    for target in internal_links[current]:
        if target not in depth:
            depth[target] = depth[current] + 1
            queue.append(target)

for name in sorted(indexable):
    if name == "index.html":
        continue
    if not inbound_links[name]:
        err(name, "indeksowana strona-sierota bez linku wewnętrznego")
    elif len(inbound_links[name]) == 1:
        warnings.append(f"{name}: tylko 1 link wejściowy z innej strony")
    if name not in depth:
        err(name, "brak ścieżki linków od strony głównej")
    elif depth[name] > 3:
        err(name, f"głębokość linkowania {depth[name]} > 3")

# FAQ schema musi odpowiadać widocznym pytaniom, nie osobnej ukrytej treści.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    visible_faq=0
    faq_block=re.search(r'<div class="pytania"[^>]*>(.*?)</div>',txt,re.S|re.I)
    if faq_block:
        visible_faq=len(re.findall(r'<details[^>]*>\s*<summary>',faq_block.group(1),re.S|re.I))

    ld_match=re.search(r'<script\s+type="application/ld\+json">(.*?)</script>',txt,re.S|re.I)
    faq_schema=None
    if ld_match:
        try:
            ld_data=json.loads(ld_match.group(1))
            for node in ld_data.get("@graph",[]):
                if node.get("@type")=="FAQPage":
                    faq_schema=node
                    break
        except Exception:
            pass

    if visible_faq:
        if faq_schema is None:
            err(pth.name,f"widoczne FAQ ({visible_faq}) bez FAQPage schema")
        else:
            schema_count=len(faq_schema.get("mainEntity",[]))
            if schema_count != visible_faq:
                err(pth.name,f"FAQ schema {schema_count} != widoczne FAQ {visible_faq}")
    elif faq_schema is not None:
        err(pth.name,"FAQPage schema bez widocznego bloku .pytania")

# LCP preload jest celowy tylko na realizacjach; nie preloadujemy nieaktywnych kart.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    preloads=re.findall(r'<link[^>]+rel="preload"[^>]+as="image"[^>]*>',txt,re.I)
    if pth.name == "realizacje.html":
        if len(preloads) != 1 or "photonroof-wymiary-800.webp" not in preloads[0]:
            err(pth.name,f"oczekiwano jednego preloada LCP PV Roof Configurator, znaleziono {len(preloads)}")
    elif preloads:
        err(pth.name,f"niepotrzebny preload obrazu ({len(preloads)})")

# Historyczne obietnice monitoringu/SLA nie mogą wrócić przez kopiowanie starej treści.
stale_support_claims = [
    "Pilnuję codziennie",
    "raz dziennie sprawdzam",
    "sprawdzam połączenia codziennie",
    "codziennie sprawdzam połączenie",
]
for pth in list(pages) + sorted(SOURCE.glob("*.html")):
    txt=pth.read_text(encoding="utf-8")
    for phrase in stale_support_claims:
        if phrase.lower() in txt.lower():
            err(pth.name,f"stara obietnica monitoringu/SLA: {phrase}")

# Landmark głównej treści i skip-link.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    mains=re.findall(r'<main\b[^>]*>',txt,re.I)
    if len(mains) != 1:
        err(pth.name,f"oczekiwano dokładnie jednego <main>, znaleziono {len(mains)}")
    elif 'id="main-content"' not in mains[0]:
        err(pth.name,"<main> bez id=main-content")
    elif 'tabindex="-1"' not in mains[0]:
        err(pth.name,"<main> bez tabindex=-1 dla poprawnego skip-link focus")
    if '<a class="skip-link" href="#main-content">' not in txt:
        err(pth.name,"skip-link nie prowadzi do #main-content")

# Polityka prywatności: minimalny zestaw informacji operacyjnych/RODO.
privacy_path=ROOT / "polityka-prywatnosci.html"
privacy=privacy_path.read_text(encoding="utf-8")
privacy_required=(
    "Administrator danych",
    "Cele i podstawy przetwarzania",
    "Odbiorcy i kategorie podmiotów",
    "Jak długo dane są przechowywane?",
    "Twoje prawa",
    "Prezesa Urzędu Ochrony Danych Osobowych",
    "Zautomatyzowane decyzje i profilowanie",
    "Self-hosted Umami",
)
for token in privacy_required:
    if token not in privacy:
        err("polityka-prywatnosci.html",f"brak wymaganej informacji: {token}")

# Umami jest ładowane warunkowo z list.js i ma osobny website ID dla maciejgryziec.pl.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    if 'https://statystyki.automatyzacjesklepow.pl/script.js' in txt:
        err(pth.name,"tracker Umami powinien być ładowany wyłącznie dynamicznie z list.js")

site_js=(ROOT / "list.js").read_text(encoding="utf-8")
for token in (
    'UMAMI_URL = "https://statystyki.automatyzacjesklepow.pl/script.js"',
    'UMAMI_WEBSITE_ID = "7bf89ecf-f690-413f-863a-658c0a0f4baa"',
    'data-umami-loader',
    'umami.disabled',
):
    if token not in site_js:
        err("list.js",f"brak konfiguracji Umami: {token}")
if "426e2d75-f696-4c0a-ab60-79e76cf1d73c" in site_js:
    err("list.js","list.js nadal zawiera website ID starej domeny")

# Główne CTA sprzedażowe mają spójny tracking i nie używają surowego mailto/#.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    for attrs in re.findall(r'<a\b([^>]*class="[^"]*\bprzycisk\b[^"]*"[^>]*)>',txt,re.I):
        href_match=re.search(r'href="([^"]*)"',attrs,re.I)
        href=href_match.group(1) if href_match else ""
        event_match=re.search(r'data-umami-event="([^"]*)"',attrs,re.I)
        event=event_match.group(1) if event_match else ""
        if not href or href == "#" or href.lower().startswith("javascript:"):
            err(pth.name,f"główne CTA ma nieprawidłowy href: {href!r}")
        if href.startswith("mailto:"):
            err(pth.name,"główne CTA nie powinno omijać briefu przez mailto")
        if href.startswith("opisz-projekt.html") and event != "klik-opisz-projekt":
            err(pth.name,f"CTA brief bez klik-opisz-projekt: {event!r}")
        if href.startswith("opisz-projekt.html"):
            query=parse_qs(urlsplit(href).query)
            if not query.get("zrodlo"):
                err(pth.name,f"CTA brief bez parametru zrodlo: {href}")
        if href.startswith("sprawdzarka.html") and event != "klik-sprawdzarka":
            err(pth.name,f"CTA sprawdzarki bez klik-sprawdzarka: {event!r}")

# Globalne CTA header/mobile/footer też zachowują last-touch source.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    slug=pth.stem
    for cls,suffix,event in (
        ("mobile-cta","mobile","klik-opisz-projekt-mobile"),
        ("nav-cta","nav","klik-opisz-projekt"),
        ("stopka-cta","footer","klik-opisz-projekt"),
    ):
        match=re.search(
            rf'<a\b([^>]*class="[^"]*\b{re.escape(cls)}\b[^"]*"[^>]*)>',
            txt,
            re.I,
        )
        if not match:
            err(pth.name,f"brak globalnego CTA .{cls}")
            continue
        attrs=match.group(1)
        href_match=re.search(r'href="([^"]+)"',attrs,re.I)
        href=href_match.group(1) if href_match else ""
        q=parse_qs(urlsplit(href).query)
        expected=f"{slug}-{suffix}"
        if q.get("zrodlo") != [expected]:
            err(pth.name,f".{cls} bez zrodlo={expected}: {href}")
        ev=re.search(r'data-umami-event="([^"]+)"',attrs,re.I)
        if not ev or ev.group(1) != event:
            err(pth.name,f".{cls} bez eventu {event}")

    if pth.name == "index.html":
        for expected in ("index-hero","index-hero-links","index-cennik","index-koniec"):
            if f"zrodlo={expected}" not in txt:
                err(pth.name,f"homepage bez last-touch {expected}")

# Last-touch source dla kart powiązanych i końcowego CTA podstrony.
for pth in pages:
    if pth.name in {"index.html","opisz-projekt.html","404.html","50x.html"}:
        continue
    txt=pth.read_text(encoding="utf-8")
    for attrs in re.findall(r'<a\b([^>]*class="[^"]*\bpowiazane-karta\b[^"]*"[^>]*)>',txt,re.I):
        href_match=re.search(r'href="([^"]+)"',attrs,re.I)
        if not href_match:
            continue
        href=href_match.group(1)
        if href.startswith("opisz-projekt.html"):
            q=parse_qs(urlsplit(href).query)
            expected=pth.stem+"-powiazane"
            if q.get("zrodlo") != [expected]:
                err(pth.name,f"powiązane CTA bez zrodlo={expected}: {href}")
            ev=re.search(r'data-umami-event="([^"]+)"',attrs,re.I)
            if not ev or ev.group(1) != "klik-opisz-projekt-powiazane":
                err(pth.name,"powiązane CTA bez klik-opisz-projekt-powiazane")

    koniec=re.search(r'<section class="[^"]*\bkoniec\b[^"]*"[^>]*>(.*?)</section>',txt,re.S|re.I)
    if koniec:
        link=re.search(r'<a[^>]+data-umami-event="klik-opisz-projekt"[^>]+href="([^"]+)"',koniec.group(1),re.I)
        if not link:
            err(pth.name,"sekcja końcowa bez CTA klik-opisz-projekt")
        else:
            href=link.group(1)
            q=parse_qs(urlsplit(href).query)
            expected=pth.stem+"-koniec"
            if q.get("zrodlo") != [expected]:
                err(pth.name,f"końcowe CTA bez zrodlo={expected}: {href}")

# Generyczne nazwy linków muszą mieć kontekstowy aria-label.
generic_link_labels={"zobacz więcej","więcej","czytaj więcej","sprawdź więcej","dowiedz się więcej"}
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    for attrs,inner in re.findall(r'<a\b([^>]*)>(.*?)</a>',txt,re.S|re.I):
        label=' '.join(re.sub(r'<[^>]+>',' ',html.unescape(inner)).split()).strip().lower()
        if label in generic_link_labels and not re.search(r'aria-label="[^"]+"',attrs,re.I):
            href=re.search(r'href="([^"]*)"',attrs,re.I)
            err(pth.name,f"generyczny link bez aria-label: {label!r} -> {(href.group(1) if href else '')}")

# Social metadata: canonical / Open Graph / Twitter muszą być spójne.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    if re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex',txt,re.I):
        continue

    def _meta(pattern):
        m=re.search(pattern,txt,re.I)
        return m.group(1) if m else ""

    canonical=_meta(r'<link\s+rel="canonical"\s+href="([^"]+)"')
    og_url=_meta(r'<meta\s+property="og:url"\s+content="([^"]+)"')
    og_title=_meta(r'<meta\s+property="og:title"\s+content="([^"]+)"')
    og_desc=_meta(r'<meta\s+property="og:description"\s+content="([^"]+)"')
    og_image=_meta(r'<meta\s+property="og:image"\s+content="([^"]+)"')
    tw_title=_meta(r'<meta\s+name="twitter:title"\s+content="([^"]+)"')
    tw_desc=_meta(r'<meta\s+name="twitter:description"\s+content="([^"]+)"')
    tw_image=_meta(r'<meta\s+name="twitter:image"\s+content="([^"]+)"')

    if canonical != og_url:
        err(pth.name,f"canonical != og:url: {canonical!r} vs {og_url!r}")
    if tw_title != og_title:
        err(pth.name,"twitter:title != og:title")
    if tw_desc != og_desc:
        err(pth.name,"twitter:description != og:description")
    if tw_image != og_image:
        err(pth.name,"twitter:image != og:image")

# Sitemap: wszystkie strony poza 404.
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
try:
    tree = ET.parse(ROOT / "sitemap.xml")
    sitemap_urls = {
        n.text.rstrip("/") or DOMAIN
        for n in tree.getroot().findall("s:url/s:loc", ns)
        if n.text
    }
except Exception as exc:
    err("sitemap.xml", str(exc))
    sitemap_urls = set()

expected_urls = {
    DOMAIN if p.name == "index.html" else f"{DOMAIN}/{p.name}"
    for p in pages if p.name not in {"404.html", "50x.html"}
}
image_ns = {"i": "http://www.google.com/schemas/sitemap-image/1.1"}
try:
    image_nodes = tree.getroot().findall(".//i:image/i:loc", image_ns)
    for node in image_nodes:
        if not node.text or not node.text.startswith(DOMAIN + "/"):
            err("sitemap.xml", f"nieprawidłowy image:loc: {node.text!r}")
            continue
        local = ROOT / node.text[len(DOMAIN)+1:]
        if not local.exists():
            err("sitemap.xml", f"image:loc nie istnieje lokalnie: {node.text}")
except Exception as exc:
    err("sitemap.xml", f"błąd audytu image sitemap: {exc}")

if sitemap_urls != expected_urls:
    missing = sorted(expected_urls - sitemap_urls)
    extra = sorted(sitemap_urls - expected_urls)
    if missing:
        err("sitemap.xml", f"brakuje URL: {missing}")
    if extra:
        err("sitemap.xml", f"nadmiarowe URL: {extra}")

# Ochrona obrazu produkcyjnego: źródła i narzędzia nie mogą wejść do nginx.
dockerignore = ROOT / ".dockerignore"
if not dockerignore.exists():
    err(".dockerignore", "brak pliku — Coolify COPY . . opublikuje źródła")
else:
    docker_rules = {
        line.strip().rstrip("/")
        for line in dockerignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    for required in (".git", ".github", "zrodla", "narzedzia", "deploy"):
        if required not in docker_rules:
            err(".dockerignore", f"brak ochrony: {required}")

# Atom feed i indeks tekstowy.
feed_path = ROOT / "feed.xml"
if not feed_path.exists():
    err("feed.xml", "brak feedu Atom")
else:
    try:
        feed_tree = ET.parse(feed_path)
        feed_ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = feed_tree.getroot().findall("a:entry", feed_ns)
        article_sources = [SOURCE / f"{slug}.html" for slug in (
            "system-zamiast-excela", "gotowy-system-czy-dedykowane-oprogramowanie",
            "ile-kosztuje-aplikacja-dla-firmy", "jak-przygotowac-brief-aplikacji",
            "ai-w-automatyzacji-firmy", "wtyczka-czy-integracja", "ksef-dla-jdg-terminy"
        ) if (SOURCE / f"{slug}.html").exists()]
        if len(entries) != len(article_sources):
            err("feed.xml", f"liczba wpisów={len(entries)}, oczekiwano={len(article_sources)}")
    except Exception as exc:
        err("feed.xml", f"niepoprawny XML: {exc}")

llms_path = ROOT / "llms.txt"
if not llms_path.exists():
    err("llms.txt", "brak indeksu tekstowego")
else:
    llms = llms_path.read_text(encoding="utf-8")
    for required in ("Oferta dla firm", "Realizacje", "Opisz projekt", "## Kontakt"):
        if required not in llms:
            err("llms.txt", f"brak sekcji/odnośnika: {required}")

# Przygotowana konfiguracja nginx / Coolify.
nginx_cfg = ROOT / "deploy" / "nginx.conf"
if not nginx_cfg.exists():
    err("deploy/nginx.conf", "brak przygotowanej konfiguracji")
else:
    cfg = nginx_cfg.read_text(encoding="utf-8")
    required_nginx = (
        'server_name maciejgryziec.pl www.maciejgryziec.pl;',
        'return 301 https://maciejgryziec.pl$request_uri;',
        'server_tokens off;',
        'absolute_redirect off;',
        'etag on;',
        'if_modified_since exact;',
        'gzip on;',
        'gzip_proxied any;',
        'gzip_comp_level 5;',
        'Strict-Transport-Security',
        'X-Content-Type-Options',
        'X-Frame-Options',
        'Cross-Origin-Opener-Policy',
        'Referrer-Policy',
        'Permissions-Policy',
        'Content-Security-Policy',
        "script-src 'self' 'sha256-9h4+QNjOt3CgNFpdn6iqbeII0Hyi4PqjGT1QhTZFYlc=' https://statystyki.automatyzacjesklepow.pl;",
        "connect-src 'self' https://statystyki.automatyzacjesklepow.pl;",
        'location ^~ /zrodla/ { return 404; }',
        'location ^~ /narzedzia/ { return 404; }',
        'location ^~ /deploy/ { return 404; }',
        'location ^~ /.git/ { return 404; }',
        'location ^~ /.github/ { return 404; }',
        r'location ~* \.(?:py|sh|ya?ml|md|toml|ini|conf|lock|env|bak|old|orig|swp|tmp)$',
        r'location ~* \.(?:css|js)$',
        'expires -1;',
        'expires 365d;',
        'expires 30d;',
        'location = /index.html',
        'if (-f $document_root$uri.html)',
        'return 301 $uri.html$is_args$args;',
        'location = /healthz',
        'return 200 "ok\\n";',
        'error_page 404 /404.html;',
        'error_page 500 502 503 504 /50x.html;',
    )
    for token in required_nginx:
        if token not in cfg:
            err("deploy/nginx.conf", f"brak dyrektywy: {token}")
    if "script-src " not in cfg:
        err("deploy/nginx.conf", "brak script-src w CSP")
    else:
        script_src_value = cfg.split("script-src ",1)[1].split(";",1)[0]
        if "\x27unsafe-inline\x27" in script_src_value:
            err("deploy/nginx.conf", "script-src nie może zawierać unsafe-inline")
        if BOOTSTRAP_HASH not in script_src_value:
            err("deploy/nginx.conf", "script-src nie zawiera hasha bootstrapa no-js→js")

    if 'add_header X-Frame-Options "DENY" always;' not in cfg:
        err("deploy/nginx.conf","X-Frame-Options nie jest DENY")
    if "frame-ancestors 'none'" not in cfg:
        err("deploy/nginx.conf","CSP frame-ancestors nie jest none")
    if "base-uri 'none'" not in cfg:
        err("deploy/nginx.conf","CSP base-uri nie jest none")

    if 'includeSubDomains' in cfg:
        warnings.append("deploy/nginx.conf: HSTS includeSubDomains — upewnij się, że wszystkie subdomeny działają po HTTPS")
    if re.search(r'location\s+~\*\s+\.\(\?:', cfg):
        err("deploy/nginx.conf", "regex location wygląda jak .(?:...) bez escapowanego \.")
    # Prosty balans klamer; nie zastępuje nginx -t, ale łapie uszkodzone bloki.
    if cfg.count("{") != cfg.count("}"):
        err("deploy/nginx.conf", f"niezbalansowane klamry: {cfg.count('{')} != {cfg.count('}')} ")

# robots, manifest, security.
robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
for token in ("Sitemap:", "Disallow: /zrodla/", "Disallow: /narzedzia/", "Disallow: /deploy/", "Disallow: /DEPLOY-PLAN.md", "Disallow: /RELEASE-SCOPE.md"):
    if token not in robots:
        err("robots.txt", f"brak {token}")

try:
    manifest = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
    for field in ("id","name","short_name","description","start_url","scope","theme_color","background_color"):
        if not manifest.get(field):
            err("site.webmanifest", f"brak pola {field}")
    for icon in manifest.get("icons", []):
        icon_path = ROOT / icon["src"].lstrip("/")
        if not icon_path.exists():
            err("site.webmanifest", f"brak ikony {icon_path.name}")
except Exception as exc:
    err("site.webmanifest", str(exc))

security = (ROOT / ".well-known" / "security.txt")
if not security.exists():
    err("security.txt", "brak /.well-known/security.txt")
else:
    sec = security.read_text(encoding="utf-8")
    for token in ("Contact:", "Expires:", "Canonical:"):
        if token not in sec:
            err("security.txt", f"brak {token}")
    expiry = re.search(r"^Expires:\s*(\S+)", sec, re.M)
    if expiry:
        try:
            expires_at = datetime.fromisoformat(expiry.group(1).replace("Z", "+00:00"))
            if expires_at <= datetime.now(timezone.utc) + timedelta(days=90):
                err("security.txt", f"Expires zbyt blisko lub w przeszłości: {expiry.group(1)}")
        except ValueError:
            err("security.txt", f"niepoprawny format Expires: {expiry.group(1)}")

# Screenshoty poniżej pierwszej sekcji mają być lazy i nie mogą mieć wysokiego priorytetu.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    first_end=txt.find("</section>")
    for m in re.finditer(r'<img\b[^>]*>',txt,re.I):
        if first_end >= 0 and m.start() < first_end:
            continue
        tag=m.group(0)
        src_m=re.search(r'src="([^"]+)"',tag,re.I)
        if not src_m or not src_m.group(1).startswith("zdjecia/"):
            continue
        if not re.search(r'\bloading="lazy"',tag,re.I):
            err(pth.name,f"obraz poniżej pierwszej sekcji bez loading=lazy: {src_m.group(1)}")
        if re.search(r'\bfetchpriority="high"',tag,re.I):
            err(pth.name,f"obraz poniżej pierwszej sekcji ma fetchpriority=high: {src_m.group(1)}")

# Odroczone obrazy karuzeli muszą wskazywać na istniejące pliki.
for pth in pages:
    txt=pth.read_text(encoding="utf-8")
    for rel in re.findall(r'data-carousel-src="([^"]+)"',txt,re.I):
        local=ROOT / urlsplit(rel).path
        if not local.exists():
            err(pth.name,f"data-carousel-src nie istnieje: {rel}")
    for srcset in re.findall(r'data-carousel-srcset="([^"]+)"',txt,re.I):
        for candidate in srcset.split(','):
            rel=candidate.strip().split()[0] if candidate.strip() else ""
            local=ROOT / urlsplit(rel).path if rel else None
            if rel and not local.exists():
                err(pth.name,f"data-carousel-srcset nie istnieje: {rel}")

# Screeny dowodowe w realizacjach muszą mieć opisowy alt.
realizacje_html=(ROOT / "realizacje.html").read_text(encoding="utf-8")
for figure in re.findall(r'<figure[^>]*>(.*?)</figure>',realizacje_html,re.S|re.I):
    for attrs in re.findall(r'<img\b([^>]*)>',figure,re.I):
        src_match=re.search(r'src="([^"]+)"',attrs,re.I)
        alt_match=re.search(r'alt="([^"]*)"',attrs,re.I)
        src=src_match.group(1) if src_match else "<bez src>"
        if not alt_match or not alt_match.group(1).strip():
            err("realizacje.html",f"screen w <figure> bez opisowego alt: {src}")

# Każdy oryginalny screenshot portfolio powinien mieć WebP.
for original in sorted((ROOT / "zdjecia").iterdir()):
    if original.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        continue
    webp = original.with_suffix(".webp")
    webp_800 = original.with_name(original.stem + "-800.webp")
    if not webp.exists():
        err("zdjecia", f"brak WebP dla {original.name}")
    if not webp_800.exists():
        err("zdjecia", f"brak WebP 800 px dla {original.name}")

# Formularz leadowy i prywatność.
brief = (ROOT / "opisz-projekt.html").read_text(encoding="utf-8")
if 'id="brief-form"' not in brief or "brief-przygotuj-email" not in brief:
    err("opisz-projekt.html", "brak formularza/trackingu briefu")
for error_page in ("404.html", "50x.html"):
    if 'name="robots" content="noindex,follow"' not in (ROOT / error_page).read_text(encoding="utf-8"):
        err(error_page, f"{error_page} powinno mieć noindex,follow")
if "Formularz „Opisz projekt”" not in (ROOT / "polityka-prywatnosci.html").read_text(encoding="utf-8"):
    err("polityka-prywatnosci.html", "polityka nie opisuje formularza")

print(f"Audyt: {len(pages)} stron HTML")
if warnings:
    print("\nOstrzeżenia:")
    for item in warnings:
        print(" -", item)
if errors:
    print(f"\nBŁĘDY ({len(errors)}):")
    for item in errors:
        print(" -", item)
    sys.exit(1)
print("OK — linki, meta, schema, sitemap, obrazy i pliki techniczne są spójne.")
