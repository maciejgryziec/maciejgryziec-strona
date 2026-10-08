#!/usr/bin/env python3
"""Check editorial regressions, metadata and the currently published contact address.
This is not an AI-text detector. The qualitative review is recorded separately.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse
import concurrent.futures
import json
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '.audit-copy'
BAD_PUNCTUATION = re.compile('[\u2013\u2014\u2026]')
STALE_COPY = (
    '11 projektów', '46 stron HTML', 'anonymized B2B client',
    'jedno uzgodnione źródło danych dla danych',
    'Nie ma handlowca, odbieram ja.', 'Ile kosztuje ogarnięcie tego',
    'ja pilnuję rur', 'Następny sensowny krok',
)

class CopyParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.text = []
        self.attributes = []
        self.contact = []
        self.title_count = 0
        self.description_count = 0
        self.main_count = 0
        self.script_type = None
        self.script_content = []
        self.json_blocks = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'script':
            self.script_type = a.get('type', '')
            self.script_content = []
        if tag == 'title':
            self.title_count += 1
        if tag == 'meta' and a.get('name') == 'description':
            self.description_count += 1
        if tag == 'main':
            self.main_count += 1
        for key in ('alt', 'title', 'placeholder', 'aria-label'):
            if a.get(key):
                self.attributes.append(a[key])
        if tag == 'meta' and (a.get('name') == 'description' or a.get('property', '').startswith(('og:', 'twitter:'))):
            self.attributes.append(a.get('content', ''))
        if tag == 'a' and a.get('href', '').lower().startswith('mailto:'):
            self.contact.append(a['href'][7:].split('?')[0])

    def handle_endtag(self, tag):
        if tag == 'script':
            if self.script_type == 'application/ld+json':
                self.json_blocks.append(''.join(self.script_content))
            self.script_type = None
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if self.script_type is not None:
            self.script_content.append(data)
        if not self.skip and data.strip():
            self.text.append(data)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for x in value:
            yield from strings(x)
    elif isinstance(value, dict):
        for x in value.values():
            yield from strings(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--contact', default='kontakt@maciejgryziec.pl', help='Verified active contact mailbox. Change only after mail tests pass.')
    args = ap.parse_args()
    files = sorted(ROOT.glob('*.html'))
    failures = []
    results = []

    def read(name):
        if not args.live:
            return (ROOT / name).read_text()
        req = urllib.request.Request('https://maciejgryziec.pl/' + name, headers={'User-Agent': 'Portfolio-copy-audit/1.0', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode('utf-8')

    def check_page(path):
        name = path.name
        raw = read(name)
        p = CopyParser()
        p.feed(raw)
        chunks = p.text + p.attributes
        schema_ok = True
        for block in p.json_blocks:
            try:
                chunks.extend(strings(json.loads(block)))
            except json.JSONDecodeError:
                schema_ok = False
        plain = ' '.join(' '.join(x.split()) for x in p.text)
        reasons = []
        remaining = [x[:180] for x in chunks if BAD_PUNCTUATION.search(x)]
        if remaining:
            reasons.append({'long_dashes_or_ellipsis': remaining[:5]})
        stale = [x for x in STALE_COPY if x in plain]
        if stale:
            reasons.append({'stale_copy': stale})
        if p.title_count != 1 or p.description_count != 1 or p.main_count != 1:
            reasons.append({'structure': [p.title_count, p.description_count, p.main_count]})
        if not schema_ok:
            reasons.append('Invalid JSON-LD')
        wrong = sorted(set(x for x in p.contact if x.lower() != args.contact.lower()))
        if wrong or not p.contact:
            reasons.append({'contact': wrong, 'links': len(p.contact)})
        if re.search(r'</(?:a|b|strong|em)>\s+[.,;:]', raw):
            reasons.append('Whitespace before punctuation following an inline element')
        return {'page': name, 'ok': not reasons, 'reasons': reasons, 'mailto_links': len(p.contact), 'words': len(plain.split())}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(check_page, files):
            results.append(result)
            if not result['ok']:
                failures.append(result)
    js = read('list.js')
    # Review double-quoted and single-quoted UI literals; comments are not marketing copy.
    literals = re.findall(r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')''', js)
    remaining = [x[:180] for x in literals if BAD_PUNCTUATION.search(x)]
    if remaining:
        failures.append({'page': 'list.js', 'reasons': remaining[:10]})
    if 'mailto:' + args.contact not in js:
        failures.append({'page': 'list.js', 'reasons': ['Brief recipient does not match verified contact']})
    summary = {
        'mode': 'live' if args.live else 'local', 'pages': len(files),
        'results': results, 'failures': failures,
        'verified_contact': args.contact, 'qualitative_review': 'performed separately; this audit checks regressions only',
    }
    OUT.mkdir(exist_ok=True)
    (OUT / ('live.json' if args.live else 'local.json')).write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print('COPY AUDIT:', len(files), 'pages;', len(failures), 'failures')
    for failure in failures:
        print(json.dumps(failure, ensure_ascii=False))
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
