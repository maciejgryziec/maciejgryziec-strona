#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

echo "==> Python syntax"
python3 -m py_compile \
  narzedzia/buduj-nowa.py \
  narzedzia/audyt-strony.py \
  narzedzia/audyt-tresci.py \
  narzedzia/audyt-assets.py \
  narzedzia/audyt-kontrast.py \
  narzedzia/audyt-print.py \
  narzedzia/audyt-chrome.py \
  narzedzia/audyt-runtime.py \
  narzedzia/audyt-csp.py \
  narzedzia/audyt-linkow-zewnetrznych.py \
  narzedzia/sprawdz-live.py

echo "==> Build"
python3 narzedzia/buduj-nowa.py >/tmp/automatyzacjesklepow-build.log

echo "==> Static audit"
python3 narzedzia/audyt-strony.py

echo "==> Content / cannibalization audit"
python3 narzedzia/audyt-tresci.py

echo "==> Asset budget"
python3 narzedzia/audyt-assets.py

echo "==> Contrast audit"
python3 narzedzia/audyt-kontrast.py

echo "==> XML"
if command -v xmllint >/dev/null 2>&1; then
  xmllint --noout sitemap.xml feed.xml
else
  python3 - <<'PY'
import xml.etree.ElementTree as ET
ET.parse("sitemap.xml")
ET.parse("feed.xml")
print("XML OK")
PY
fi

echo "==> Whitespace / Git diff"
git diff --check

echo "==> Build idempotence"
python3 - <<'PY'
from pathlib import Path
import hashlib
import subprocess

root = Path(".")
files = sorted(list(root.glob("*.html")) + [root / "list.css", root / "list.js", root / "sitemap.xml", root / "feed.xml"])

def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

before = hashes()
subprocess.run(["python3", "narzedzia/buduj-nowa.py"], check=True, stdout=subprocess.DEVNULL)
after = hashes()

if before != after:
    changed = [p for p in before if before[p] != after[p]]
    raise SystemExit("Build is not idempotent: " + ", ".join(changed))
print("IDEMPOTENT OK")
PY

echo "==> Generated files committed/synced check"
if ! git diff --quiet; then
  echo "NOTE: working tree contains intentional uncommitted changes."
  echo "Before push, run this script again after staging/committing generated files."
fi

echo
echo "Release preflight OK."
echo "Optional local browser audit: python3 narzedzia/audyt-chrome.py"
echo "Optional CSP browser audit: python3 narzedzia/audyt-csp.py"
echo "Optional full runtime crawl: python3 narzedzia/audyt-runtime.py"
echo "Optional performance audit: python3 narzedzia/audyt-performance.py"
echo "Optional print/PDF audit: python3 narzedzia/audyt-print.py"
echo "Optional external links audit: python3 narzedzia/audyt-linkow-zewnetrznych.py"
echo "After deployment: python3 narzedzia/sprawdz-live.py"
