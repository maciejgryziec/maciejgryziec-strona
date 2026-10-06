# -*- coding: utf-8 -*-
"""Lokalny audyt prawdziwego PDF cennika generowanego przez Chromium.

Wymaga lokalnie:
- Chrome/CDP używanego przez cdp.Karta,
- pypdf,
- Pillow,
- pdftoppm (Poppler).

Celowo nie działa w CI - render/PDF zależy od środowiska graficznego.
"""

from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cdp import Karta  # noqa: E402

try:
    from pypdf import PdfReader
    from PIL import Image
except ImportError as exc:
    print("Brak lokalnej zależności do audytu print:", exc)
    raise SystemExit(2)

if shutil.which("pdftoppm") is None:
    print("Brak pdftoppm (Poppler) - nie można zweryfikować renderu PDF.")
    raise SystemExit(2)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check(label: str, condition: bool, details="") -> None:
    if condition:
        print(f"[OK] {label}" + (f": {details}" if details else ""))
    else:
        print(f"[FAIL] {label}" + (f": {details}" if details else ""))
        problems.append(label + (f": {details}" if details else ""))


problems = []
old_cwd = os.getcwd()
os.chdir(ROOT)
httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{httpd.server_address[1]}"

try:
    with tempfile.TemporaryDirectory(prefix="cennik-print-audit-") as tmp:
        tmpdir = Path(tmp)
        pdf_path = tmpdir / "cennik.pdf"
        render_prefix = tmpdir / "page"

        k = Karta()
        k.rozmiar(1200, 900, 1, False)
        try:
            k.idz(base + "/cennik.html?print-audit=1", .8)
            k.cmd("Emulation.setEmulatedMedia", media="print")

            dom = k.js(
                """(()=>{
                  function display(sel) {
                    const el=document.querySelector(sel);
                    return el ? getComputedStyle(el).display : 'missing';
                  }
                  return {
                    header:display('.gora'),
                    footer:display('.stopka'),
                    skip:display('.skip-link'),
                    breadcrumb:display('.okruszki'),
                    related:display('.powiazane'),
                    printAction:display('.print-action'),
                    table:display('table'),
                    bodyBg:getComputedStyle(document.body).backgroundColor,
                    scrollWidth:document.documentElement.scrollWidth,
                    clientWidth:document.documentElement.clientWidth
                  };
                })()"""
            ) or {}

            for key in ("header", "footer", "skip", "breadcrumb", "printAction"):
                check(f"print ukrywa {key}", dom.get(key) == "none", str(dom.get(key)))
            check(
                "print bez bloku powiązanych",
                dom.get("related") in {"none", "missing"},
                str(dom.get("related")),
            )
            check("tabela pozostaje widoczna", dom.get("table") == "table", str(dom.get("table")))
            check("białe tło wydruku", dom.get("bodyBg") == "rgb(255, 255, 255)", str(dom.get("bodyBg")))
            check(
                "brak poziomego overflow w print media",
                dom.get("scrollWidth", 1) <= dom.get("clientWidth", 0),
                f"{dom.get('scrollWidth')} / {dom.get('clientWidth')}",
            )

            result = k.cmd(
                "Page.printToPDF",
                printBackground=True,
                preferCSSPageSize=True,
                displayHeaderFooter=False,
            )
            pdf_path.write_bytes(base64.b64decode(result["data"]))
        finally:
            k.zamknij()

        check("PDF ma sensowny rozmiar", 100_000 <= pdf_path.stat().st_size <= 1_500_000, str(pdf_path.stat().st_size))

        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        check("liczba stron PDF", 2 <= page_count <= 4, str(page_count))

        # CSS @page ma wymuszać A4: ~595.28 x 841.89 pt.
        for number, page in enumerate(reader.pages, 1):
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            check(
                f"A4 strona {number}",
                abs(width - 595.28) <= 1.0 and abs(height - 841.89) <= 1.0,
                f"{width:.1f} x {height:.1f} pt",
            )

        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        text_flat = re.sub(r"\s+", " ", text)
        check("PDF zawiera dużo treści", len(text) >= 3000, str(len(text)))

        required = (
            "CENNIK",
            "01 Wstępny",
            "02 Pierwszy",
            "02+ Integracja",
            "03 System na",
            "04 Opieka miesięczna",
            "349 zł / mies.",
            "899 zł / mies.",
        )
        for marker in required:
            check(f"PDF zawiera: {marker}", marker in text_flat)

        forbidden = (
            "Przejdź do treści",
            "Start ›",
            "Następny sensowny krok",
        )
        for marker in forbidden:
            check(f"PDF bez webowego tekstu: {marker}", marker not in text)

        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r",
                "110",
                str(pdf_path),
                str(render_prefix),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        pngs = sorted(tmpdir.glob("page-*.png"))
        check("liczba renderów = liczba stron", len(pngs) == page_count, f"{len(pngs)} / {page_count}")

        for number, png in enumerate(pngs, 1):
            image = Image.open(png).convert("L")
            histogram = image.histogram()
            nonwhite = sum(histogram[:245]) / (image.width * image.height)

            # A4 przy 110 dpi powinno mieć ok. 909x1287 px.
            check(
                f"geometria renderu {number}",
                abs(image.width - 909) <= 3 and abs(image.height - 1287) <= 3,
                f"{image.width}x{image.height}",
            )
            check(
                f"strona {number} nie jest pusta",
                nonwhite >= 0.02,
                f"nonwhite={nonwhite:.4f}",
            )

finally:
    httpd.shutdown()
    httpd.server_close()
    os.chdir(old_cwd)

print()
if problems:
    print(f"Print/PDF audit: {len(problems)} problemów")
    for problem in problems:
        print(" -", problem)
    raise SystemExit(1)

print("Print/PDF audit OK.")
