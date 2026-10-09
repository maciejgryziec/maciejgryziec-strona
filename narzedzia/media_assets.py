"""Final asset pass shared by EVERY page. Standard library only.

Correct responsive sizes for real rendered slots, preserve deferred loading and
version all brand assets. Image pixels come from separately reviewed demo files.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / 'narzedzia/portfolio-media.json').read_text())
ASSETS = MANIFEST['assets']
ALIASES = dict(MANIFEST['aliases'])
for _key, _entry in ASSETS.items():
    for _variant in _entry['variants']:
        ALIASES[_variant['path']] = _key
BRAND = ('brief-send.js', 'brief-send.css', 'znak.svg', 'znak-bialy.svg', 'logo.svg', 'ikona.svg', 'favicon.ico',
         'favicon.png', 'favicon-192.png', 'favicon-512.png', 'ikona-16.png',
         'ikona-32.png', 'ikona-48.png', 'ikona-96.png', 'ikona-180.png',
         'ikona-192.png', 'ikona-512.png', 'site.webmanifest')
DIGESTS = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:12]
           for name in BRAND if (ROOT / name).is_file()}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}


def local_path(url):
    u = urlsplit(url)
    if u.netloc and u.netloc not in ('maciejgryziec.pl', 'www.maciejgryziec.pl'):
        return ''
    return unquote(u.path).lstrip('/')


class _Images(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.offsets = [0]
        for match in re.finditer('\n', text):
            self.offsets.append(match.end())
        self.stack = []
        self.images = []
        self.preloads = []

    def position(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        node = {'tag': tag, 'attrs': dict(attrs), 'start': self.position(),
                'end': self.position() + len(raw)}
        if tag == 'link' and node['attrs'].get('rel') == 'preload' and node['attrs'].get('as') == 'image':
            self.preloads.append(node)
        if tag == 'img':
            node['ancestors'] = list(self.stack)
            self.images.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                end = self.text.find('>', self.position()) + 1
                self.stack[i]['end'] = end
                del self.stack[i:]
                return


def _scaled_sizes(scale, mobile_vw, mobile_offset, desktop_px, breakpoint=980):
    # Account for cover cropping: intrinsic image width can be greater than its box.
    return ('(max-width: %dpx) calc(%.2fvw - %.2fpx), %dpx' %
            (breakpoint, mobile_vw * scale, mobile_offset * scale,
             round(desktop_px * scale)))


def _sizes(node, entry):
    classes = set()
    for ancestor in node['ancestors']:
        classes.update((ancestor['attrs'].get('class') or '').split())
    ratio = entry['width'] / entry['height']
    cover_scale = max(1, ratio / 1.6)
    if 'hero-projekt' in classes:
        return _scaled_sizes(cover_scale, 100, 40, 780)
    if 'program-real-shot' in classes:
        return _scaled_sizes(cover_scale, 82, 30, 620)
    if 'karta' in classes:
        # Wide full-screen cards span the row; other frames retain the side-by-side layout.
        if ratio > 2.2:
            return '(max-width: 800px) calc(100vw - 88px), (max-width: 1216px) calc(100vw - 176px), 1040px'
        return '(max-width: 800px) calc(100vw - 88px), 720px'
    if 'ekrany' in classes:
        return _scaled_sizes(cover_scale, 60, 0, 650, 820)
    if 'detail-panel' in classes:
        return '100vw'
    # Full-width figures on Realizacje, not the old shared 720px assumption.
    return '(max-width: 1200px) calc(100vw - 40px), 1160px'


def _img_tag(attrs):
    return '<img ' + ' '.join(k if v is None else k + '="' + html.escape(str(v), quote=True) + '"'
                              for k, v in sorted(attrs.items())) + '>'


def responsive_screens(text):
    p = _Images(text)
    p.feed(text)
    edits = []
    for node in p.images:
        attrs = dict(node['attrs'])
        field = next((k for k in ('data-project-src', 'data-carousel-src', 'src') if attrs.get(k)), None)
        if not field:
            continue
        key = ALIASES.get(local_path(attrs[field]))
        if key is None:
            continue
        classes = {c for a in node['ancestors'] for c in (a['attrs'].get('class') or '').split()}
        # Use complete, reviewed source screenshots rather than old 16:10 crops.
        full = {'card-frankie': 'frankie-orders', 'card-roofpv': 'roofpv-3d',
                'card-rental': 'rental-flota', 'card-bacteria': 'bacteria-hd-gameplay'}
        if 'karta' in classes:
            key = full.get(key, key)
        entry = ASSETS[key]
        if 'karta' in classes:
            frame = next((a for a in reversed(node['ancestors']) if 'zdjecie' in (a['attrs'].get('class') or '').split()), None)
            if frame:
                opening_end = text.find('>', frame['start']) + 1
                opening = text[frame['start']:opening_end]
                opening = re.sub(r'\sdata-full-screen="[^"]*"', '', opening)
                style_match = re.search(r'\sstyle="([^"]*)"', opening)
                style = style_match.group(1) if style_match else ''
                style = re.sub(r'--screen-ratio\s*:[^;]*;?', '', style).strip('; ')
                style += (';' if style else '') + '--screen-ratio:%s/%s' % (entry['width'], entry['height'])
                if style_match:
                    opening = opening[:style_match.start()] + opening[style_match.end():]
                opening = opening[:-1] + ' data-full-screen="' + key + '" style="' + style + '">'
                edits.append((frame['start'], opening_end, opening))
        sizes = _sizes(node, entry)
        variants = entry['variants']
        srcset = ', '.join(v['path'] + ' ' + str(v['width']) + 'w' for v in variants)
        default = next((v for v in variants if v['width'] >= 1600), variants[-1])
        for name in ('src', 'srcset', 'sizes', 'data-project-src', 'data-project-srcset',
                     'data-project-sizes', 'data-carousel-src', 'data-carousel-srcset',
                     'data-carousel-sizes'):
            attrs.pop(name, None)
        if field == 'src':
            attrs.update(src=default['path'], srcset=srcset, sizes=sizes)
        else:
            prefix = field[:-3]
            attrs[field] = default['path']
            attrs[prefix + 'srcset'] = srcset
            attrs[prefix + 'sizes'] = sizes
        attrs['width'] = str(entry['width'])
        attrs['height'] = str(entry['height'])
        attrs['data-media'] = key
        attrs['data-webp'] = '1'
        attrs.setdefault('decoding', 'async')
        # A source in <picture> overrides img.srcset. Replace old 800w sources too.
        picture = next((a for a in reversed(node['ancestors']) if a['tag'] == 'picture'), None)
        if picture:
            count = sum(any(a is picture for a in image['ancestors']) for image in p.images)
            if count != 1:
                raise ValueError('Unexpected multi-image picture wrapper')
            edits.append((picture['start'], picture['end'], '<picture>' + _img_tag(attrs) + '</picture>'))
        else:
            edits.append((node['start'], node['end'], _img_tag(attrs)))
    for node in p.preloads:
        attrs = dict(node['attrs'])
        key = ALIASES.get(local_path(attrs.get('href', '')))
        if key is None:
            continue
        first = next((i for i in p.images if ALIASES.get(local_path(i['attrs'].get('src', '')))), None)
        if first:
            key = ALIASES[local_path(first['attrs']['src'])]
        if first and any('karta' in (a['attrs'].get('class') or '').split() for a in first['ancestors']):
            key = {'card-frankie': 'frankie-orders', 'card-roofpv': 'roofpv-3d',
                   'card-rental': 'rental-flota', 'card-bacteria': 'bacteria-hd-gameplay'}.get(key, key)
        entry = ASSETS[key]
        sizes = _sizes(first, entry) if first else '100vw'
        variants = entry['variants']
        default = next((v for v in variants if v['width'] >= 1600), variants[-1])
        attrs.update(href=default['path'], imagesizes=sizes,
                     imagesrcset=', '.join(v['path'] + ' ' + str(v['width']) + 'w' for v in variants),
                     type='image/webp')
        markup = '<link ' + ' '.join(k + '="' + html.escape(str(v), quote=True) + '"' for k, v in sorted(attrs.items())) + '>'
        edits.append((node['start'], node['end'], markup))
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def version_brand(text):
    # The same generated logo addresses are used for header, icons, mask icon and metadata.
    for name, digest in DIGESTS.items():
        pattern = r'(?P<q>[\"\'])(?P<prefix>(?:https://(?:www\.)?maciejgryziec\.pl/|/)?)' + re.escape(name) + r'(?:\?[^\"\']*)?(?P=q)'
        text = re.sub(pattern, lambda m: m['q'] + m['prefix'] + name + '?v=' + digest + m['q'], text)
    return text


def finalize_assets(text):
    return version_brand(responsive_screens(text))
