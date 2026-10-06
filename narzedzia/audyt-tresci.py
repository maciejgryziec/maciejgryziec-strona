# -*- coding: utf-8 -*-
"""Audyt treści: kanibalizacja SEO, powtarzalne akapity i skrajnie krótkie landingi."""
from pathlib import Path
from collections import Counter
import html
import math
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "zrodla"
EXCLUDE = {"404.html", "50x.html"}
STOP = set("""
i w z na do od dla oraz lub ale że ze się to jest są jako przy po pod nad przez nie czy jak co
który która które ten ta te też już tylko może można jeśli gdy albo między więc bez o a
""".split())

warnings = []
errors = []

def visible_text(path):
    src = path.read_text(encoding="utf-8")
    src = re.sub(r"<script.*?</script>|<style.*?</style>|<header.*?</header>|<footer.*?</footer>", " ", src, flags=re.I | re.S)
    src = re.sub(r"<[^>]+>", " ", src)
    return " ".join(html.unescape(src).split())

def tokens(path):
    text = visible_text(path).lower()
    return [
        w for w in re.findall(r"[a-ząćęłńóśźż0-9]+", text)
        if len(w) >= 3 and w not in STOP
    ]

pages = sorted(p for p in SOURCE.glob("*.html") if p.name not in EXCLUDE)
counts = {p.name: Counter(tokens(p)) for p in pages}
N = len(pages)

# TF-IDF cosine similarity.
df = Counter()
for counter in counts.values():
    for word in counter:
        df[word] += 1
idf = {w: math.log((N + 1) / (d + 1)) + 1 for w, d in df.items()}

def vector(counter):
    return {w: (1 + math.log(n)) * idf[w] for w, n in counter.items()}

vectors = {name: vector(counter) for name, counter in counts.items()}

def cosine(a, b):
    common = set(a) & set(b)
    dot = sum(a[w] * b[w] for w in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0

pairs = []
names = sorted(vectors)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        score = cosine(vectors[a], vectors[b])
        pairs.append((score, a, b))
        if score >= 0.65:
            errors.append(f"kanibalizacja {score:.3f}: {a} <> {b}")
        elif score >= 0.50:
            warnings.append(f"wysokie podobieństwo {score:.3f}: {a} <> {b}")

# Repeated substantive paragraphs. Shared boilerplate/link blocks are ignored by removing headers/footers.
paragraphs = {}
for path in pages:
    src = path.read_text(encoding="utf-8")
    src = re.sub(r"<header.*?</header>|<footer.*?</footer>", " ", src, flags=re.I | re.S)
    for raw in re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", src, flags=re.I | re.S):
        text = " ".join(re.sub(r"<[^>]+>", " ", html.unescape(raw)).split())
        norm = re.sub(r"\W+", " ", text.lower()).strip()
        if len(norm) >= 180:
            paragraphs.setdefault(norm, []).append(path.name)

for norm, files in paragraphs.items():
    unique = sorted(set(files))
    if len(unique) >= 3:
        warnings.append(f"ten sam długi akapit na {len(unique)} stronach: {', '.join(unique)}")

# Word count: only flag truly thin source pages; short error/contact/tool pages are allowed.
ALLOW_SHORT = {
    "opisz-projekt.html", "polityka-prywatnosci.html", "sprawdzarka.html",
    "kalkulator-kosztu-recznej-pracy.html",
}
word_counts = {}
for path in pages:
    count = len(re.findall(r"\b[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ-]+\b", visible_text(path)))
    word_counts[path.name] = count
    if count < 220 and path.name not in ALLOW_SHORT:
        errors.append(f"bardzo krótka treść {count} słów: {path.name}")
    elif count < 300 and path.name not in ALLOW_SHORT:
        warnings.append(f"krótka treść {count} słów: {path.name}")

print(f"Audyt treści: {len(pages)} źródeł")
print("Najbardziej podobne pary:")
for score, a, b in sorted(pairs, reverse=True)[:8]:
    print(f" - {score:.3f}  {a} <> {b}")

if warnings:
    print(f"\nOstrzeżenia ({len(warnings)}):")
    for item in warnings:
        print(" -", item)

if errors:
    print(f"\nBŁĘDY ({len(errors)}):")
    for item in errors:
        print(" -", item)
    sys.exit(1)

print("\nOK — brak krytycznej kanibalizacji i skrajnie cienkich treści.")
