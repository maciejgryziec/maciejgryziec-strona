# -*- coding: utf-8 -*-
"""CI-friendly audyt kluczowych kontrastów WCAG AA z faktycznego list.css."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "list.css").read_text(encoding="utf-8")
MIN_NORMAL = 4.5
MIN_UI = 3.0


def rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def linear(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    r, g, b = rgb(hex_color)
    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def ratio(fg: str, bg: str) -> float:
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def composite_white(bg: str, alpha: float) -> str:
    br, bgc, bb = rgb(bg)
    out = [
        round(alpha * 255 + (1 - alpha) * br),
        round(alpha * 255 + (1 - alpha) * bgc),
        round(alpha * 255 + (1 - alpha) * bb),
    ]
    return "#" + "".join(f"{v:02x}" for v in out)


def css_var(name: str) -> str:
    m = re.search(rf"--{re.escape(name)}\s*:\s*(#[0-9a-fA-F]{{3,6}})", CSS)
    if not m:
        raise RuntimeError(f"Brak tokenu --{name} w list.css")
    return m.group(1).lower()


def rgba_alpha(selector_fragment: str) -> float:
    pattern = re.escape(selector_fragment) + r"[^}]*color\s*:\s*rgba\(255\s*,\s*255\s*,\s*255\s*,\s*([0-9.]+)\)"
    m = re.search(pattern, CSS)
    if not m:
        raise RuntimeError(f"Brak białego rgba dla {selector_fragment}")
    return float(m.group(1))


issues: list[str] = []


def check(label: str, fg: str, bg: str, minimum: float = MIN_NORMAL) -> None:
    value = ratio(fg, bg)
    print(f"{label}: {fg} / {bg} = {value:.2f}:1")
    if value < minimum:
        issues.append(f"{label}: {value:.2f}:1 < {minimum}:1")


# Podstawowe tokeny na bieli.
white = "#ffffff"
check("tekst / białe", css_var("tekst"), white)
check("szary / białe", css_var("szary"), white)
check("link / białe", css_var("link"), white)
check("biały / główny CTA", white, css_var("blekit"))

# Dwa jawne CTA/nav kolory spoza :root.
mobile = re.search(r"\.mobile-cta\{[^}]*background\s*:\s*(#[0-9a-fA-F]{6})", CSS)
if mobile:
    check("biały / mobile CTA", white, mobile.group(1))
else:
    issues.append("nie znaleziono koloru mobile CTA")

dark_nav_text = re.search(r"body\.ciemna \.mobile-cta\{[^}]*color\s*:\s*(#[0-9a-fA-F]{6})", CSS)
if dark_nav_text:
    check("ciemny tekst / białe CTA", dark_nav_text.group(1), white)

# Najjaśniejsze możliwe fragmenty ciemnych teł.
dark_backgrounds: set[str] = set()
for selector in (".noc", ".czern", ".ziel", ".ksiega-tlo"):
    m = re.search(re.escape(selector) + r"\{([^}]*)\}", CSS)
    if m:
        dark_backgrounds.update(x.lower() for x in re.findall(r"#[0-9a-fA-F]{6}", m.group(1)))

# Ciemne mobilne menu.
m = re.search(r"body\.ciemna \.gora nav\{[^}]*background\s*:\s*(#[0-9a-fA-F]{6})", CSS)
if m:
    dark_backgrounds.add(m.group(1).lower())

if not dark_backgrounds:
    issues.append("nie znaleziono ciemnych teł do audytu")

secondary_selectors = [
    ".rozdzial.ciemny .slaby",
    ".ciemny .cena",
    ".ciemny .etykieta",
    ".ciemny .okruszki",
    ".ciemny .article-meta",
]

for selector in secondary_selectors:
    try:
        alpha = rgba_alpha(selector)
    except RuntimeError as exc:
        issues.append(str(exc))
        continue

    worst = (999.0, "", "")
    for bg in dark_backgrounds:
        fg = composite_white(bg, alpha)
        value = ratio(fg, bg)
        if value < worst[0]:
            worst = (value, fg, bg)

    value, fg, bg = worst
    print(f"{selector}: alpha={alpha:.2f}, worst {fg} / {bg} = {value:.2f}:1")
    if value < MIN_NORMAL:
        issues.append(f"{selector}: najgorszy kontrast {value:.2f}:1 < {MIN_NORMAL}:1 na {bg}")

# Non-text contrast: granice interaktywnych kontrolek na białym tle.
def border_hex(selector: str):
    m = re.search(re.escape(selector) + r"\{([^}]*)\}", CSS)
    if not m:
        return None
    b = re.search(r"border(?:-color)?\s*:[^;]*?(#[0-9a-fA-F]{6})", m.group(1))
    return b.group(1).lower() if b else None

control_selectors = [
    ".formularz-prosty input",
    ".privacy-actions button",
    ".print-action button",
    ".roi-grid input",
    ".kwalifikator select",
    ".poradniki-filter input",
    ".brief-form input,.brief-form select,.brief-form textarea",
    ".brief-actions .drugorzedny",
    ".brief-fallback",
]
for selector in control_selectors:
    color = border_hex(selector)
    if not color:
        issues.append(f"brak koloru border dla kontrolki {selector}")
        continue
    check(f"border {selector}", color, white, MIN_UI)

# Border formularza na ciemnym tle — najgorszy z używanych ciemnych kolorów.
m = re.search(r"\.ciemny \.formularz-prosty input\{([^}]*)\}", CSS)
if m:
    alpha_match = re.search(r"border-color\s*:\s*rgba\(255\s*,\s*255\s*,\s*255\s*,\s*([0-9.]+)\)", m.group(1))
    if alpha_match:
        alpha = float(alpha_match.group(1))
        worst = min((ratio(composite_white(bg, alpha), bg), bg) for bg in dark_backgrounds)
        print(f"border ciemnego formularza: alpha={alpha:.2f}, worst={worst[0]:.2f}:1 na {worst[1]}")
        if worst[0] < MIN_UI:
            issues.append(f"border ciemnego formularza: {worst[0]:.2f}:1 < {MIN_UI}:1")
    else:
        issues.append("brak rgba border-color dla ciemnego formularza")
else:
    issues.append("brak reguły .ciemny .formularz-prosty input")

# Placeholder zielonego formularza: alfa tekstu na półprzezroczystym tle inputa.
placeholder = re.search(r"\.ziel input::placeholder\{[^}]*color\s*:\s*rgba\(255\s*,\s*255\s*,\s*255\s*,\s*([0-9.]+)\)", CSS)
input_bg_alpha = re.search(r"\.ziel input\{[^}]*background\s*:\s*rgba\(255\s*,\s*255\s*,\s*255\s*,\s*([0-9.]+)\)", CSS)
if placeholder and input_bg_alpha:
    section_bg = "#0f3d2e"
    field_bg = composite_white(section_bg, float(input_bg_alpha.group(1)))
    placeholder_fg = composite_white(field_bg, float(placeholder.group(1)))
    check("placeholder zielonego formularza", placeholder_fg, field_bg, MIN_NORMAL)
else:
    issues.append("nie udało się odczytać kontrastu placeholdera zielonego formularza")

# Focus ring: zewnętrzna niebieska warstwa musi być widoczna na jasnym tle.
focus = re.search(r"summary:focus-visible\{([^}]*)\}", CSS)
if focus:
    ring = re.search(r"box-shadow\s*:[^;]*?(#[0-9a-fA-F]{6})", focus.group(1))
    if ring:
        check("focus ring / białe", ring.group(1), white, MIN_UI)
    else:
        issues.append("focus-visible bez kontrastowej zewnętrznej warstwy")
else:
    issues.append("brak reguły focus-visible")

print()
if issues:
    print(f"Kontrast: {len(issues)} problemów")
    for issue in issues:
        print(" -", issue)
    sys.exit(1)

print("Kontrast WCAG AA OK.")
