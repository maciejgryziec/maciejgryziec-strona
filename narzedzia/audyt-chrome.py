# -*- coding: utf-8 -*-
"""Lokalny smoke/UX audit w prawdziwym Chrome. Nie jest uruchamiany w CI."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import contextlib
import os
import socket
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from cdp import Karta
except Exception as exc:
    print("Nie można uruchomić audytu Chrome:", exc)
    print("Wymagany jest lokalny Chrome oraz pakiet Python websocket-client.")
    sys.exit(2)

errors = []

def check(label, condition, detail=""):
    mark = "OK" if condition else "FAIL"
    print(f"[{mark}] {label}" + (f": {detail}" if detail else ""))
    if not condition:
        errors.append(label + (": " + detail if detail else ""))

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

@contextlib.contextmanager
def server():
    old = os.getcwd()
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        os.chdir(old)


def open_page(base, page, width=390, height=900, mobile=True):
    k = Karta()
    k.rozmiar(width, height, 1, mobile)
    sep = "&" if "?" in page else "?"
    k.idz(f"{base}/{page}{sep}audit={time.time_ns()}", .55)
    return k

with server() as base:
    # Najważniejsze strony: brak poziomego overflow i uszkodzonych obrazów.
    pages = [
        "index.html", "opisz-projekt.html", "cennik.html", "poradniki.html",
        "crm-na-zamowienie.html", "system-do-wycen-i-ofert.html", "realizacje.html", "kalkulator-kosztu-recznej-pracy.html", "404.html", "50x.html",
    ]
    for page in pages:
        k = open_page(base, page)
        try:
            overflow = bool(k.js("document.documentElement.scrollWidth>innerWidth"))
            broken = k.js('[...document.images].filter(i=>!i.hasAttribute("data-carousel-src")&&i.complete&&i.naturalWidth===0).map(i=>i.currentSrc||i.getAttribute("src")||"")') or []
            check(f"{page} mobile overflow", not overflow)
            check(f"{page} obrazy", not broken, str(broken) if broken else "0 uszkodzonych")
        finally:
            k.zamknij()

    # Mobile tap targets: standalone controls/CTA must meet WCAG 2.2 minimum 24x24.
    tap_pages = [
        "index.html", "realizacje.html", "cennik.html", "opisz-projekt.html",
        "poradniki.html", "sprawdzarka.html", "kalkulator-kosztu-recznej-pracy.html",
    ]
    for page in tap_pages:
        k = open_page(base, page)
        try:
            too_small = k.js('''(()=>[...document.querySelectorAll("button,input,select,textarea,summary,a.przycisk,.mobile-cta")].map(el=>{var r=el.getBoundingClientRect(),cs=getComputedStyle(el);return {tag:el.tagName.toLowerCase(),name:(el.innerText||el.getAttribute("aria-label")||el.name||"").trim().slice(0,50),w:r.width,h:r.height,display:cs.display,visibility:cs.visibility,hidden:el.hidden,type:el.type||""};}).filter(x=>x.type!=="hidden"&&!x.hidden&&x.display!=="none"&&x.visibility!=="hidden"&&x.w>0&&x.h>0&&(x.w<24||x.h<24)))()''') or []
            check("tap targets " + page, not too_small, str(too_small) if too_small else "min. 24×24")
        finally:
            k.zamknij()

    # Skip-link: klawiatura musi przenieść nie tylko scroll, ale też fokus na <main>.
    k = open_page(base, "index.html", 1200, 800, False)
    try:
        k.js('document.body.setAttribute("tabindex","-1");document.body.focus();document.body.removeAttribute("tabindex")')
        k.cmd("Input.dispatchKeyEvent", type="keyDown", key="Tab", code="Tab", windowsVirtualKeyCode=9)
        k.cmd("Input.dispatchKeyEvent", type="keyUp", key="Tab", code="Tab", windowsVirtualKeyCode=9)
        time.sleep(.1)
        skip_before = k.js('({tag:document.activeElement.tagName,cls:document.activeElement.className,href:document.activeElement.getAttribute("href"),text:document.activeElement.textContent.trim()})')
        check("skip-link pierwszy Tab", skip_before.get("tag") == "A" and "skip-link" in skip_before.get("cls","") and skip_before.get("href") == "#main-content", str(skip_before))
        k.cmd("Input.dispatchKeyEvent", type="keyDown", key="Enter", code="Enter", windowsVirtualKeyCode=13)
        k.cmd("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter", windowsVirtualKeyCode=13)
        time.sleep(.2)
        skip_after = k.js('({tag:document.activeElement.tagName,id:document.activeElement.id,hash:location.hash})')
        check("skip-link fokus na main", skip_after.get("tag") == "MAIN" and skip_after.get("id") == "main-content" and skip_after.get("hash") == "#main-content", str(skip_after))
    finally:
        k.zamknij()

    # Mobile menu.
    k = open_page(base, "index.html")
    try:
        k.js('document.querySelector(".menu-toggle").click()')
        time.sleep(.25)
        state = k.js('({expanded:document.querySelector(".menu-toggle").getAttribute("aria-expanded"),vis:getComputedStyle(document.querySelector("#nav-main")).visibility,count:document.querySelectorAll("#nav-main a").length})')
        check("menu mobilne otwiera się", state["expanded"] == "true" and state["vis"] == "visible", str(state))
        check("menu mobilne ma pełną nawigację", state["count"] >= 6, str(state["count"]))
    finally:
        k.zamknij()

    # Mobile menu — focus/keyboard/disclosure behavior.
    k = open_page(base, "index.html")
    try:
        k.js('document.querySelector(".menu-toggle").focus();document.querySelector(".menu-toggle").click()')
        time.sleep(.15)
        opened = k.js('({expanded:document.querySelector(".menu-toggle").getAttribute("aria-expanded"),label:document.querySelector(".menu-toggle").getAttribute("aria-label"),focused:document.activeElement===document.querySelector(".menu-toggle")})')
        check("menu focus po otwarciu", opened.get("expanded") == "true" and opened.get("label") == "Zamknij menu" and opened.get("focused"), str(opened))

        k.cmd("Input.dispatchKeyEvent", type="keyDown", key="Tab", code="Tab", windowsVirtualKeyCode=9)
        k.cmd("Input.dispatchKeyEvent", type="keyUp", key="Tab", code="Tab", windowsVirtualKeyCode=9)
        time.sleep(.1)
        tab_state = k.js('({tag:document.activeElement.tagName,href:document.activeElement.getAttribute("href"),inside:document.querySelector("#nav-main").contains(document.activeElement)})')
        check("menu Tab do nawigacji", bool(tab_state.get("inside")) and tab_state.get("tag") == "A", str(tab_state))

        k.cmd("Input.dispatchKeyEvent", type="keyDown", key="Escape", code="Escape", windowsVirtualKeyCode=27)
        k.cmd("Input.dispatchKeyEvent", type="keyUp", key="Escape", code="Escape", windowsVirtualKeyCode=27)
        time.sleep(.1)
        escaped = k.js('({expanded:document.querySelector(".menu-toggle").getAttribute("aria-expanded"),open:document.body.classList.contains("menu-open"),focused:document.activeElement===document.querySelector(".menu-toggle")})')
        check("menu Escape + focus return", escaped.get("expanded") == "false" and not escaped.get("open") and escaped.get("focused"), str(escaped))

        k.js('document.querySelector(".menu-toggle").click();document.querySelector("#tresc").dispatchEvent(new MouseEvent("click",{bubbles:true}))')
        time.sleep(.1)
        outside = k.js('({expanded:document.querySelector(".menu-toggle").getAttribute("aria-expanded"),open:document.body.classList.contains("menu-open")})')
        check("menu klik poza zamyka", outside.get("expanded") == "false" and not outside.get("open"), str(outside))

        k.js('document.querySelector(".menu-toggle").click()')
        k.rozmiar(1100, 844, 1, False)
        k.js('window.dispatchEvent(new Event("resize"))')
        time.sleep(.1)
        desktop = k.js('({expanded:document.querySelector(".menu-toggle").getAttribute("aria-expanded"),open:document.body.classList.contains("menu-open")})')
        check("menu resize desktop reset", desktop.get("expanded") == "false" and not desktop.get("open"), str(desktop))
    finally:
        k.zamknij()

    # Aktywna sekcja głównej nawigacji na podstronach.
    nav_cases = [
        ("crm-na-zamowienie.html", "Usługi"),
        ("system-zamiast-excela.html", "Poradniki"),
        ("cennik.html", "Cennik"),
        ("realizacje.html", "Realizacje"),
    ]
    for page, expected in nav_cases:
        k = open_page(base, page, 1100, 850, False)
        try:
            active = k.js('[...document.querySelectorAll("#nav-main a[aria-current=page]")].map(a=>a.textContent.trim())') or []
            check("aktywna nawigacja " + page, active == [expected], str(active))
        finally:
            k.zamknij()

    # Mobile touch targets: samodzielne kontrolki minimum 24x24 px (WCAG 2.2).
    for page in [
        "index.html", "realizacje.html", "cennik.html",
        "opisz-projekt.html", "poradniki.html",
        "dedykowane-oprogramowanie-dla-firm.html",
    ]:
        k = open_page(base, page, 390, 844, True)
        try:
            controls = k.js('''[...document.querySelectorAll("button,input,select,textarea,summary,.przycisk,.mobile-cta,.menu-toggle,.strzalka,.kropy button")].map((el)=>{let r=el.getBoundingClientRect(),cs=getComputedStyle(el);return {tag:el.tagName,cls:el.className||"",text:(el.innerText||el.getAttribute("aria-label")||el.getAttribute("placeholder")||"").trim().slice(0,60),w:r.width,h:r.height,display:cs.display,vis:cs.visibility,opacity:cs.opacity,disabled:el.disabled||false};}).filter(x=>x.display!=="none"&&x.vis!=="hidden"&&x.opacity!=="0"&&!x.disabled)''')
            bad = [x for x in controls if x.get("w",0) < 24 or x.get("h",0) < 24]
            check("touch targets " + page, not bad, str(bad[:8]))
        finally:
            k.zamknij()

    # Deep-linki / spis treści nie mogą chować nagłówków pod fixed headerem.
    for page, anchor in [
        ("system-zamiast-excela.html", "#sygnaly-ze-firma-wyrosla-z-arkusza"),
        ("gotowy-system-czy-dedykowane-oprogramowanie.html", "#a-gdzie-low-code-i-no-code"),
    ]:
        for width, height, mobile in [(1200, 900, False), (390, 844, True)]:
            k = Karta(); k.rozmiar(width, height, 1, mobile); k.idz(base + "/" + page + anchor, .45)
            try:
                values = k.js(f'(()=>{{var el=document.querySelector("{anchor}"),head=document.querySelector(".gora");return {{exists:!!el,top:el?el.getBoundingClientRect().top:null,header:head?head.getBoundingClientRect().height:null}};}})()')
                check(
                    "deep-link offset " + page + " " + str(width),
                    bool(values.get("exists")) and values.get("top", 0) >= values.get("header", 0) + 20,
                    str(values),
                )
            finally:
                k.zamknij()

    # Wyszukiwarka poradników.
    k = open_page(base, "poradniki.html", 1100, 900, False)
    try:
        k.js('var i=document.querySelector("[data-poradniki-filter]");i.value="Excel";i.dispatchEvent(new Event("input"))')
        visible = k.js('[...document.querySelectorAll(".wpisy li:not([hidden]) a")].map(a=>a.textContent.trim())') or []
        check("wyszukiwarka poradników", any("Excel" in x for x in visible), str(visible))
    finally:
        k.zamknij()

    # Kwalifikator projektu.
    k = open_page(base, "cennik.html", 1100, 900, False)
    try:
        k.js('var q=document.querySelector("[data-kwalifikator]");q.querySelector("[name=problem]").value="zlecenia";q.querySelector("[name=problem]").dispatchEvent(new Event("change"))')
        title = k.js('document.querySelector("[data-wynik] h3")?.textContent||""')
        href = k.js('document.querySelector("[data-wynik] a")?.getAttribute("href")||""')
        check("kwalifikator projektu", "obsługi zleceń" in title and href.startswith("opisz-projekt.html?"), f"{title} | {href}")
    finally:
        k.zamknij()

    # Kwalifikator: ręczne wyceny/oferty mają własny wynik i prefill briefu.
    k = open_page(base, "cennik.html", 1100, 900, False)
    try:
        k.js('var q=document.querySelector("[data-kwalifikator]");q.querySelector("[name=problem]").value="wyceny";q.querySelector("[name=problem]").dispatchEvent(new Event("change"))')
        quote_result = k.js('({title:document.querySelector("[data-wynik] h3")?.textContent||"",href:document.querySelector("[data-wynik] a")?.getAttribute("href")||""})')
        check("kwalifikator wyceny/oferty", "wycen i ofert" in quote_result.get("title", "") and "System%20do%20wycen%20i%20ofert" in quote_result.get("href", ""), str(quote_result))
    finally:
        k.zamknij()

    # Kalkulator kosztu ręcznej pracy — kontrola matematyki.
    k = open_page(base, "kalkulator-kosztu-recznej-pracy.html", 1100, 900, False)
    try:
        values = k.js('Object.fromEntries([...document.querySelectorAll("[data-r]")].map(x=>[x.dataset.r,x.textContent.replace(/\s/g," ").trim()]))')
        check("kalkulator operacje", values.get("operacje") == "420", str(values))
        check("kalkulator godziny", values.get("godziny") == "35 h", str(values))
        check("kalkulator rok", values.get("rok-h") == "420 h", str(values))
        numeric_cost = "".join(ch for ch in values.get("koszt", "") if ch.isdigit())
        numeric_year = "".join(ch for ch in values.get("rok-koszt", "") if ch.isdigit())
        check("kalkulator koszt miesiąc", numeric_cost == "2100", values.get("koszt", ""))
        check("kalkulator koszt rok", numeric_year == "25200", values.get("rok-koszt", ""))
    finally:
        k.zamknij()

    # Prefill formularza z kwalifikatora.
    k = open_page(base, "opisz-projekt.html?typ=System%20do%20obsługi%20zleceń", 1100, 900, False)
    try:
        selected = k.js('document.querySelector("[name=typ]").value')
        check("prefill formularza", selected == "System do obsługi zleceń", selected)
    finally:
        k.zamknij()

    # Prefill nowego landingu: system do wycen i ofert.
    k = open_page(base, "opisz-projekt.html?typ=System%20do%20wycen%20i%20ofert&zrodlo=system-wyceny-oferty", 1100, 900, False)
    try:
        selected_quote = k.js('document.querySelector("[name=typ]").value')
        check("prefill system wycen i ofert", selected_quote == "System do wycen i ofert", selected_quote)
    finally:
        k.zamknij()

    # Brief: autosave w sessionStorage + realne pobranie TXT po migracji do list.js.
    k = open_page(base, "opisz-projekt.html", 1100, 900, False)
    try:
        k.js('var f=document.querySelector("#brief-form");f.querySelector("[name=imie]").value="Audyt Brief";f.querySelector("[name=email]").value="audit@example.com";f.querySelector("[name=typ]").value="System do obsługi zleceń";f.querySelector("[name=dzis]").value="Dane robocze do testu autosave";f.querySelector("[name=problem]").value="Test problemu";["imie","email","typ","dzis","problem"].forEach(function(n){f.querySelector("[name="+n+"]").dispatchEvent(new Event("input",{bubbles:true}));});')
        time.sleep(.35)
        stored = k.js('JSON.parse(sessionStorage.getItem("briefDraft")||"{}")') or {}
        check("brief autosave zapis", stored.get("imie") == "Audyt Brief" and stored.get("dzis") == "Dane robocze do testu autosave", str(stored))

        k.idz(base + "/opisz-projekt.html?brief-reload=1", .45)
        restored = k.js('({imie:document.querySelector("[name=imie]").value,dzis:document.querySelector("[name=dzis]").value})')
        check("brief autosave odtworzenie", restored.get("imie") == "Audyt Brief" and restored.get("dzis") == "Dane robocze do testu autosave", str(restored))

        download_dir = ROOT / ".audit-downloads"
        download_dir.mkdir(exist_ok=True)
        for child in download_dir.iterdir():
            if child.is_file():
                child.unlink()
        k.cmd("Browser.setDownloadBehavior", behavior="allow", downloadPath=str(download_dir))
        k.js('document.querySelector("#pobierz-brief").click()')
        time.sleep(.8)
        downloaded = download_dir / "brief-projektu.txt"
        text_download = downloaded.read_text(encoding="utf-8") if downloaded.exists() else ""
        check("brief pobranie TXT", downloaded.exists() and "Audyt Brief" in text_download and "Test problemu" in text_download, str(downloaded))
        for child in download_dir.iterdir():
            if child.is_file():
                child.unlink()
        download_dir.rmdir()
    finally:
        k.zamknij()

    # Prywatność: nowa domena nie ładuje trackera do czasu nadania osobnego ID.
    k = open_page(base, "polityka-prywatnosci.html", 1100, 900, False)
    try:
        tracker = bool(k.js('!!document.querySelector("script[data-umami-loader=\"1\"]")'))
        requests = k.js('performance.getEntriesByType("resource").filter(e=>e.name.includes("statystyki.automatyzacjesklepow.pl")).length') or 0
        status_text = k.js('document.querySelector("#umami-status") && document.querySelector("#umami-status").textContent') or ""
        off_disabled = bool(k.js('document.querySelector("#umami-off") && document.querySelector("#umami-off").disabled'))
        on_disabled = bool(k.js('document.querySelector("#umami-on") && document.querySelector("#umami-on").disabled'))
        state = {"tracker":tracker,"requests":requests,"text":status_text,"off":off_disabled,"on":on_disabled}
        check("privacy analytics disabled", not tracker and requests == 0 and "wyłączone" in status_text and off_disabled and on_disabled, str(state))
    finally:
        k.zamknij()

    # Cennik: przycisk drukowania działa bez inline onclick.
    k = open_page(base, "cennik.html", 1100, 900, False)
    try:
        k.js('window.__printed=0;window.print=function(){window.__printed++;};document.querySelector("[data-print-cennik]").click()')
        time.sleep(.1)
        printed = k.js('window.__printed')
        check("cennik druk/PDF", printed == 1, str(printed))
    finally:
        k.zamknij()

    # Atrybucja: first-touch UTM ma przetrwać wewnętrzne źródło kwalifikatora.
    k = open_page(base, "index.html?utm_source=linkedin&utm_medium=social&utm_campaign=test", 1100, 900, False)
    try:
        k.idz(base + "/opisz-projekt.html?typ=System%20do%20obsługi%20zleceń&zrodlo=kwalifikator", .45)
        source = k.js('JSON.parse(sessionStorage.getItem("leadSource")||"{}")') or {}
        check("atrybucja UTM zachowana", source.get("utm_source") == "linkedin" and source.get("utm_campaign") == "test", str(source))
        check("atrybucja źródła wewnętrznego", source.get("zrodlo") == "kwalifikator", str(source))
    finally:
        k.zamknij()

    # Globalny header CTA zachowuje last-touch source do briefu.
    k = open_page(base, "crm-na-zamowienie.html", 1100, 900, False)
    try:
        nav_href = k.js('document.querySelector(".nav-cta").getAttribute("href")')
        mobile_href = k.js('document.querySelector(".mobile-cta").getAttribute("href")')
        footer_href = k.js('document.querySelector(".stopka-cta").getAttribute("href")')
        check("global CTA nav source", "zrodlo=crm-na-zamowienie-nav" in (nav_href or ""), str(nav_href))
        check("global CTA mobile source", "zrodlo=crm-na-zamowienie-mobile" in (mobile_href or ""), str(mobile_href))
        check("global CTA footer source", "zrodlo=crm-na-zamowienie-footer" in (footer_href or ""), str(footer_href))
        k.js('document.querySelector(".nav-cta").click()')
        time.sleep(.5)
        source = k.js('JSON.parse(sessionStorage.getItem("leadSource")||"{}")') or {}
        check(
            "global CTA nav zapisuje source",
            source.get("zrodlo") == "crm-na-zamowienie-nav",
            str(source),
        )
    finally:
        k.zamknij()

    # Fallbacki bez JavaScriptu dla kluczowych interakcji.
    nojs_cases = [
        ("opisz-projekt.html", "#brief-form", "Interaktywny brief działa lokalnie"),
        ("kalkulator-kosztu-recznej-pracy.html", ".roi-calc", "Kalkulator wymaga JavaScriptu"),
        ("cennik.html", ".kwalifikator", "Szybki kwalifikator wymaga JavaScriptu"),
        ("poradniki.html", ".poradniki-filter", "Gotowy system czy dedykowane oprogramowanie?"),
    ]
    for page, selector, text in nojs_cases:
        k = Karta(); k.rozmiar(390, 900, 1, True); k.cmd("Emulation.setScriptExecutionDisabled", value=True); k.idz(base + "/" + page + "?nojs-audit=1", .4)
        try:
            hidden = k.js(f'getComputedStyle(document.querySelector({selector!r})).display') == "none"
            fallback = bool(k.js(f'document.body.innerText.includes({text!r})'))
            check("no-JS " + page, hidden and fallback, f"hidden={hidden}, fallback={fallback}")
        finally:
            k.zamknij()

    # Reduced motion: systemowe ograniczenie ruchu musi wyłączać dekoracyjne animacje.
    k = Karta()
    k.rozmiar(390, 844, 1, True)
    k.cmd("Emulation.setEmulatedMedia", media="screen", features=[{"name":"prefers-reduced-motion","value":"reduce"}])
    k.idz(base + "/index.html?reduced-motion-audit=1", .6)
    try:
        reduced = k.js('(()=>({matches:matchMedia("(prefers-reduced-motion: reduce)").matches,laptop:getComputedStyle(document.querySelector(".laptop")).animationName,cta:getComputedStyle(document.querySelector(".start .cta svg")).animationName,stars:getComputedStyle(document.querySelector(".gwiazdy.a")).animationName,pakiet:getComputedStyle(document.querySelector(".mosty .pakiet")).animationName,bubble:getComputedStyle(document.querySelector(".dymek")).display,wjazd:getComputedStyle(document.querySelector(".wjazd")).opacity}))()')
        check("reduced motion animacje", reduced.get("matches") and reduced.get("laptop") == "none" and reduced.get("cta") == "none" and reduced.get("stars") == "none" and reduced.get("pakiet") == "none" and reduced.get("bubble") == "none" and reduced.get("wjazd") == "1", str(reduced))
        before_rm = k.js('[...document.querySelectorAll(".ksiega .karta")].findIndex(x=>x.classList.contains("aktywna"))')
        k.js('document.querySelector(".ksiega .strzalka.prawa").click()')
        time.sleep(.08)
        after_rm = k.js('[...document.querySelectorAll(".ksiega .karta")].findIndex(x=>x.classList.contains("aktywna"))')
        check("reduced motion karuzela bez animacji", before_rm == 0 and after_rm == 1, f"{before_rm} -> {after_rm}")
    finally:
        k.zamknij()

    # Karuzela: screenshot drugiej karty nie może być pobrany przed aktywacją.
    k = open_page(base, "realizacje.html", 390, 844, True)
    try:
        before = k.js('(()=>({deferred:!!document.querySelector(".ksiega img[data-carousel-src]"),resources:performance.getEntriesByType("resource").filter(e=>e.name.includes("wypozyczalnia-flota")).length}))()')
        check("karuzela lazy przed aktywacją", before.get("deferred") and before.get("resources") == 0, str(before))
        k.js('document.querySelector(".ksiega .strzalka.prawa").click()')
        time.sleep(1.15)
        after = k.js('(()=>{var cards=[...document.querySelectorAll(".ksiega .karta")],img=cards[1].querySelector("img");return {active:cards.findIndex(x=>x.classList.contains("aktywna")),deferred:img.hasAttribute("data-carousel-src"),complete:img.complete,nw:img.naturalWidth,resources:performance.getEntriesByType("resource").filter(e=>e.name.includes("wypozyczalnia-flota")).length};})()')
        check("karuzela lazy po aktywacji", after.get("active") == 1 and not after.get("deferred") and after.get("complete") and after.get("nw",0) > 0 and after.get("resources",0) >= 1, str(after))
    finally:
        k.zamknij()

    # Reduced motion: animacje/transition mają być wyłączone, a karuzela przełączać się natychmiast.
    k = Karta(); k.rozmiar(1200, 900, 1, False)
    k.cmd("Emulation.setEmulatedMedia", media="", features=[{"name":"prefers-reduced-motion","value":"reduce"}])
    k.idz(base + "/realizacje.html?reduced-motion=1", .55)
    try:
        motion = k.js('(()=>{var el=document.querySelector(".wjazd"),cards=[...document.querySelectorAll(".ksiega .karta")];return {matches:matchMedia("(prefers-reduced-motion: reduce)").matches,transition:getComputedStyle(el).transitionDuration,transform:getComputedStyle(el).transform,active:cards.findIndex(x=>x.classList.contains("aktywna"))};})()')
        check("reduced-motion media", bool(motion.get("matches")), str(motion))
        check("reduced-motion wjazd", motion.get("transition") in ("0s", "0.001ms", "0.01ms") and motion.get("transform") == "none", str(motion))
        k.js('document.querySelector(".ksiega .strzalka.prawa").click()')
        time.sleep(.12)
        after = k.js('[...document.querySelectorAll(".ksiega .karta")].findIndex(x=>x.classList.contains("aktywna"))')
        check("reduced-motion karuzela", after == 1, str(after))
    finally:
        k.zamknij()

    # Karuzela nie rusza sama i ukrywa nieaktywne linki z tab-order.
    k = open_page(base, "index.html", 1200, 900, False)
    try:
        k.js('document.querySelector(".ksiega").scrollIntoView({block:"center"})')
        time.sleep(.2)
        before = k.js('[...document.querySelectorAll(".ksiega .karta")].findIndex(x=>x.classList.contains("aktywna"))')
        time.sleep(5.8)
        after = k.js('[...document.querySelectorAll(".ksiega .karta")].findIndex(x=>x.classList.contains("aktywna"))')
        hidden_tabs = k.js('[...document.querySelectorAll(".ksiega .karta:not(.aktywna) a")].every(a=>a.getAttribute("tabindex")==="-1")')
        check("karuzela bez autoplay", before == after, f"{before} -> {after}")
        check("karuzela tab-order", bool(hidden_tabs))
    finally:
        k.zamknij()

print(f"\nChrome audit: {len(errors)} błędów")
if errors:
    for item in errors:
        print(" -", item)
    sys.exit(1)
print("OK — kluczowe zachowania UX działają w Chrome.")
