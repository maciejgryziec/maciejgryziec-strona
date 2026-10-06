# -*- coding: utf-8 -*-
"""Stabilny, CI-friendly budżet rozmiaru assetów.

Nie mierzy czasu renderowania. Pilnuje tylko, żeby bundle i obrazy nie urosły
niepostrzeżenie ponad rozsądne granice.
"""

from pathlib import Path
import gzip
import sys

ROOT = Path(__file__).resolve().parent.parent

LIMITS = {
    "list.css": 20_000,  # gzip bytes
    "list.js": 15_000,   # gzip bytes
}
MOBILE_WEBP_LIMIT = 100_000
FULL_WEBP_LIMIT = 300_000

issues = []

for name, limit in LIMITS.items():
    path = ROOT / name
    if not path.exists():
        issues.append(f"brak pliku {name}")
        continue
    raw = path.read_bytes()
    packed = gzip.compress(raw, compresslevel=9)
    print(f"{name}: raw={len(raw)}B gzip={len(packed)}B limit={limit}B")
    if len(packed) > limit:
        issues.append(f"{name}: gzip {len(packed)}B > {limit}B")

for path in sorted((ROOT / "zdjecia").glob("*.webp")):
    size = path.stat().st_size
    limit = MOBILE_WEBP_LIMIT if path.stem.endswith("-800") else FULL_WEBP_LIMIT
    if size > limit:
        issues.append(f"{path.relative_to(ROOT)}: {size}B > {limit}B")
    print(f"{path.relative_to(ROOT)}: {size}B / {limit}B")

print()
if issues:
    print(f"Asset budget: {len(issues)} problemów")
    for issue in issues:
        print(" -", issue)
    sys.exit(1)

print("Asset budget OK.")
