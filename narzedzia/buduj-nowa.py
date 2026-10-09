# -*- coding: utf-8 -*-
# Sklada nowa wersje strony automatyzacjesklepow.pl (styl "listu" z rozdzialami-swiatami)
# do folderu demo/strona/nowa/. Zrodlem tresci podstron sa obecne pliki produkcyjne.
import re, os, glob, html, json, subprocess, hashlib, unicodedata
from datetime import date
from media_assets import finalize_assets
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ZR = os.path.join(REPO, "zrodla")
CEL = REPO
PALETA = "c"               # "" = paleta bazowa z list.css; "a"/"b"/"c" = nakladka paleta-X.css
os.makedirs(CEL, exist_ok=True)


def data_pliku(sciezka):
    """Data SEO zgodna przed i po commicie: dirty/untracked = dziś, czysty plik = ostatni commit."""
    try:
        rel=os.path.relpath(sciezka, REPO)
        status=subprocess.check_output(
            ["git","status","--porcelain","--",rel],
            cwd=REPO, stderr=subprocess.DEVNULL, text=True
        ).strip()
        if status:
            return date.today().isoformat()
        out=subprocess.check_output(
            ["git","log","-1","--format=%cs","--",rel],
            cwd=REPO, stderr=subprocess.DEVNULL, text=True
        ).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", out):
            return out
    except Exception:
        pass
    return date.fromtimestamp(os.path.getmtime(sciezka)).isoformat()


def data_publikacji(sciezka):
    """Pierwszy commit pliku; dla nowych plików używa lokalnej daty utworzenia/mtime."""
    try:
        rel=os.path.relpath(sciezka, REPO)
        out=subprocess.check_output(
            ["git","log","--follow","--format=%cs","--reverse","--",rel],
            cwd=REPO, stderr=subprocess.DEVNULL, text=True
        ).strip().splitlines()
        if out and re.fullmatch(r"\d{4}-\d{2}-\d{2}", out[0]):
            return out[0]
    except Exception:
        pass
    return data_pliku(sciezka)

# ---------------------------------------------------------------- CSS
CSS = r"""
:root{
  --tekst:#1c1c21; --szary:#5e5f66; --blekit:#1550d0; --link:#1340c8; --kreska:#e3e4ea;
  --lewy:max(24px, calc(50vw - 340px));
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","Inter","Helvetica Neue",Arial,sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:auto;scroll-padding-top:76px}
body{margin:0;font:15px/1.6 var(--sans);color:var(--tekst);background:#fff;-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:var(--link);text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px}
a:hover{color:#0a2a8c}
p{margin:0 0 1.1em}
strong{font-weight:650}
h1,h2,h3{font-weight:650;letter-spacing:-.01em;margin:0 0 .8em;text-wrap:balance}
h1{font-size:22px;line-height:1.4;font-weight:400}
h1 strong{font-weight:650}
h2{font-size:20px;line-height:1.35}
h3{font-size:16px;margin:1.8em 0 .5em}
img{max-width:100%;height:auto}
picture{display:block}
.slaby{color:var(--szary)}

/* naglowek */
.gora{position:fixed;top:0;left:0;right:0;z-index:50;pointer-events:none;background:rgba(255,255,255,.86);border-bottom:1px solid rgba(22,31,55,.08);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);transition:background .25s,border-color .25s}
.gora .w{position:relative;height:58px}
.gora .znak{position:absolute;left:var(--lewy);top:14px;display:flex;align-items:center;gap:12px;pointer-events:auto;text-decoration:none;color:var(--tekst);font-weight:700;font-size:15px;letter-spacing:-.01em;transition:color .3s}
body.ciemna .gora{background:rgba(14,38,86,.84);border-color:rgba(255,255,255,.12)}
body.ciemna .gora .znak{color:#fff}
@media (max-width:900px){.gora .znak span{display:none}}
.gora .znak img{width:40px;height:auto;display:block}
.gora .znak img.b{display:none}
body.ciemna .gora .znak img.c{display:none}
body.ciemna .gora .znak img.b{display:block}
.gora nav{position:absolute;right:max(24px, calc(50vw - 560px));top:7px;display:flex;gap:18px;font-size:14px;pointer-events:auto;padding:7px 10px;border-radius:10px;background:transparent;transition:background .3s}
body.ciemna .gora nav{background:transparent}
.gora nav a{color:var(--link);text-decoration:underline;transition:color .3s}
.gora nav a[aria-current="page"]{font-weight:750;text-decoration-thickness:2px;text-underline-offset:4px}
body.ciemna .gora nav a{color:#fff}
.mobile-actions{display:none}
@media (max-width:900px){
  .gora .znak{left:18px;top:13px}.gora .znak img{width:38px}
  .mobile-actions{position:absolute;right:10px;top:4px;display:flex;align-items:center;gap:7px;pointer-events:auto}
  .mobile-cta{display:inline-flex;align-items:center;height:44px;padding:0 13px;border-radius:999px;background:#1a5cf0;color:#fff!important;text-decoration:none!important;font-size:12px;font-weight:750;box-shadow:0 8px 24px -16px rgba(0,0,0,.6)}
  body.ciemna .mobile-cta{background:#fff;color:#143a8b!important}
  .menu-toggle{position:relative;width:44px;height:44px;border:1px solid rgba(20,30,70,.15);border-radius:999px;background:rgba(255,255,255,.86);padding:0;cursor:pointer}
  .menu-toggle i,.menu-toggle::before,.menu-toggle::after{content:"";position:absolute;left:14px;width:14px;height:1.5px;background:#1c1c21;transition:transform .2s,top .2s,opacity .2s}
  .menu-toggle::before{top:13px}.menu-toggle i{top:21px}.menu-toggle::after{top:29px}
  body.ciemna .menu-toggle{background:rgba(0,0,0,.35);border-color:rgba(255,255,255,.18)}body.ciemna .menu-toggle i,body.ciemna .menu-toggle::before,body.ciemna .menu-toggle::after{background:#fff}
  body.menu-open .menu-toggle::before{top:21px;transform:rotate(45deg)}body.menu-open .menu-toggle i{opacity:0}body.menu-open .menu-toggle::after{top:21px;transform:rotate(-45deg)}
  .gora nav{left:auto;right:10px;top:52px;width:min(310px,calc(100vw - 20px));display:flex;flex-direction:column;align-items:stretch;gap:0;font-size:14px;padding:10px;background:#fff!important;border:1px solid rgba(20,30,70,.1);border-radius:14px;box-shadow:0 20px 50px -28px rgba(0,0,0,.55);opacity:0;visibility:hidden;transform:translateY(-8px);pointer-events:none;transition:opacity .18s,transform .18s}
  body.ciemna .gora nav{background:#102a5e!important;border-color:rgba(255,255,255,.14)}
  body.menu-open .gora nav{opacity:1;visibility:visible;transform:none;pointer-events:auto}
  body.menu-open{overflow:hidden}
  .gora nav a{display:block!important;white-space:normal;padding:10px 11px;border-radius:8px;text-decoration:none}
  .gora nav a:hover{background:rgba(21,80,208,.08)}body.ciemna .gora nav a:hover{background:rgba(255,255,255,.08)}
  .gora nav .nav-cta{display:none!important}
}

/* kolumny i rozdzialy */
.tekst{position:relative;z-index:2;margin-left:var(--lewy);max-width:440px;padding-right:24px}
.czolo .tekst{max-width:520px}
.rozdzial{position:relative;overflow:hidden;--t:0;--w:0}
.rozdzial .w{position:relative;min-height:88vh;display:flex;align-items:center;padding:14vh 0}
.rozdzial .obraz{position:absolute;right:0;top:50%;transform:translateY(-50%);width:min(50vw,720px);z-index:1;pointer-events:none}
.rozdzial.ciemny{color:#fff}
.rozdzial.ciemny a{color:#fff}
.rozdzial.ciemny h1,.rozdzial.ciemny h2{color:#fff}
.rozdzial.ciemny .slaby{color:rgba(255,255,255,.84)}
.cena{color:var(--szary)}
.ciemny .cena{color:rgba(255,255,255,.84)}
.linki a{display:inline-block;margin-right:16px}
[data-s]{transform:translateY(calc(var(--t) * var(--s,0px)))}

/* swiaty */
.jasny{background:#e8eefc}      .jasny h2,.jasny h1 strong{color:#1f2a6b}
.bialy{background:#fff}
.piasek{background:#f5e9d2}     .piasek h2,.piasek h1 strong{color:#6b4a1c}
.szary{background:#f1f1f3}      .szary h2{color:#1c1c21}
.czern{background:#0a0c14}
.noc{background:linear-gradient(#0c2350,#1c4b9c 70%,#2b62bb)}
.ziel{background:#0f3d2e}

/* ukosne krawedzie */
.skos-dol{clip-path:polygon(0 0,100% 0,100% calc(100% - 7vw),0 100%)}
.skos-dol.lewo{clip-path:polygon(0 0,100% 0,100% 100%,0 calc(100% - 7vw))}
.skos-gora{clip-path:polygon(0 7vw,100% 0,100% 100%,0 100%);margin-top:-7vw;padding-top:7vw}
.skos-oba{clip-path:polygon(0 7vw,100% 0,100% calc(100% - 7vw),0 100%);margin-top:-7vw;padding-top:7vw}
.czolo .w{min-height:auto;padding:150px 0 110px}
.czolo.rozdzial .w{min-height:88vh;padding:120px 0 90px}
.czolo.pod .w{min-height:68vh;padding:130px 0 90px}
.czolo.pod.kontakt-hero .w{min-height:54vh;padding-top:120px;padding-bottom:80px}
.pod .kasa{margin-top:70px;transform:scale(.82) translateY(calc(var(--t) * -30px));transform-origin:50% 0}

/* ---- czolo: pelny ekran, laptop z mapa mostow ---- */
.start{background:#1a5cf0;color:#fff;overflow:hidden}
.rozdzial.czolo.start .w{min-height:100vh;padding:110px 0 80px;display:flex;align-items:center}
.start .tekst{max-width:520px}
.start .nadtytul{display:inline-flex;align-items:center;gap:10px;font-size:13px;font-weight:600;background:rgba(255,255,255,.14);padding:6px 12px;border-radius:999px;margin-bottom:26px}
.start .nadtytul i{width:8px;height:8px;border-radius:50%;background:#7CF2A5;box-shadow:0 0 10px #7CF2A5}
.start h1{font-size:clamp(40px,5.2vw,68px);line-height:1.02;font-weight:800;letter-spacing:-.03em;margin:0 0 .5em;color:#fff}
.start h1 em{font-style:normal;color:#ffd23f}
.start .zacheta{font-size:18px;line-height:1.5;max-width:460px;color:rgba(255,255,255,.92)}
.start .cta{display:flex;align-items:center;gap:14px;margin:30px 0 40px;font-weight:700;font-size:17px;line-height:1.25}
.start .cta a{color:#fff;text-decoration:none;border-bottom:2px solid #ffd23f;padding-bottom:2px}
.start .cta svg{width:34px;height:34px;flex:none;animation:machaj 1.6s ease-in-out infinite}
@keyframes machaj{0%,100%{transform:translateX(0)}50%{transform:translateX(-6px)}}
.trust-row{display:flex;gap:8px;flex-wrap:wrap;margin:-18px 0 30px}.trust-row span{font-size:11.5px;line-height:1;padding:7px 9px;border:1px solid rgba(255,255,255,.22);border-radius:999px;color:rgba(255,255,255,.82);background:rgba(255,255,255,.06)}
.start .drobne{font-size:13px;color:rgba(255,255,255,.65)}
.start .drobne a{color:rgba(255,255,255,.85);margin-right:14px}
.start .obraz{left:calc(var(--lewy) + 470px);right:auto;width:min(54vw,840px,calc(100vw - var(--lewy) - 400px));pointer-events:none}
.start .tekst{max-width:470px}
.kropki i{position:absolute;border-radius:50%;background:rgba(255,255,255,.35)}
.laptop{position:relative;width:94%;margin-left:3%;transform:perspective(1800px) rotateY(-16deg) rotateX(5deg) rotate(-2deg);transform-origin:50% 60%;animation:wjazd-laptopa 1.3s cubic-bezier(.2,.8,.2,1) both, bujaj 7s ease-in-out 1.3s infinite}
@keyframes wjazd-laptopa{from{opacity:0;transform:perspective(1800px) rotateY(-30deg) rotateX(10deg) rotate(4deg) translate(120px,160px)}to{opacity:1;transform:perspective(1800px) rotateY(-16deg) rotateX(5deg) rotate(-2deg)}}
@keyframes bujaj{0%,100%{translate:0 0}50%{translate:0 -12px}}
.laptop .ekran{position:relative;box-sizing:content-box;background:#0a1230;border:10px solid #1c1e26;border-bottom-width:14px;border-radius:16px 16px 6px 6px;aspect-ratio:16/10;overflow:hidden;box-shadow:0 60px 90px -40px rgba(0,0,0,.6),inset 0 0 0 1px rgba(255,255,255,.06)}
.laptop .ekran::before{content:"";position:absolute;left:50%;top:0;width:90px;height:8px;margin-left:-45px;background:#1c1e26;border-radius:0 0 8px 8px;z-index:3}
.laptop .podstawa{height:16px;margin:0 -2%;background:linear-gradient(#e6e8ee,#b4b8c3);border-radius:2px 2px 14px 14px;box-shadow:0 30px 50px -20px rgba(0,0,0,.6)}
.laptop .podstawa::after{content:"";display:block;width:14%;height:5px;margin:0 auto;background:#9a9ea9;border-radius:0 0 6px 6px}
.mosty{width:100%;height:auto;aspect-ratio:16/10;display:block}
.mosty .lin{fill:none;stroke:#3d63c9;stroke-width:2.5;stroke-linecap:round}
.mosty .lin.pos{stroke:#6f9bff;stroke-width:6;opacity:.18;filter:blur(3px)}
.mosty .kafel{fill:#131d3d;stroke:#4a6ae0;stroke-width:1.5}
.mosty .kafel.glowny{fill:#1a5cf0;stroke:#9dbbff;stroke-width:2}
.mosty .ikona{fill:none;stroke:#cfe0ff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.mosty .belka{fill:#0e1630}
.mosty .belka-lin{stroke:#243266;stroke-width:1}
.mosty .lampka{fill:#59e08d}
.mosty .lampka.a{animation:lampka 2.4s ease-in-out infinite}
@keyframes lampka{0%,100%{opacity:1}50%{opacity:.35}}
.podpisy{position:absolute;inset:0}
.podpisy span{position:absolute;transform:translate(-50%,-50%);font:600 clamp(8px,.95vw,14px)/1.2 var(--sans);color:#e9eeff;white-space:nowrap}
.podpisy span.m{font-weight:500;font-size:clamp(6px,.7vw,10px);color:#9db4f0}
.podpisy span.naglowek-e{transform:translate(0,-50%);font-weight:600;font-size:clamp(7px,.8vw,12px);color:#c9d6ff}
.podpisy span.status{transform:translate(-100%,-50%);font-weight:600;font-size:clamp(6px,.7vw,10px);color:#7CF2A5}
.mosty .pakiet{fill:#ffd23f;filter:drop-shadow(0 0 6px #ffd23f);offset-rotate:0deg;animation:jedz 3.2s linear infinite}
@keyframes jedz{0%{offset-distance:0%;opacity:0}8%{opacity:1}92%{opacity:1}100%{offset-distance:100%;opacity:0}}
.mosty .puls{fill:none;stroke:#7CF2A5;stroke-width:2;opacity:0;animation:puls 3.2s ease-out infinite}
@keyframes puls{0%,70%{opacity:0;r:22}80%{opacity:.9;r:22}100%{opacity:0;r:44}}
.mosty .tlo{fill:none;stroke:rgba(255,255,255,.05);stroke-width:1}
.dymek{position:absolute;background:#fff;color:#1c1c21;font:600 13px/1.3 var(--sans);padding:12px 16px;border-radius:14px;box-shadow:0 30px 50px -20px rgba(0,0,0,.5);opacity:0;animation:dymek 12s ease-in-out infinite;animation-delay:var(--d);white-space:nowrap}
.dymek small{display:block;font-weight:500;color:#5e5f66;font-size:11px}
.dymek::after{content:"";position:absolute;left:22px;bottom:-8px;border:8px solid transparent;border-top-color:#fff;border-bottom:0}
.dymek.zolty{background:#ffd23f}.dymek.zolty::after{border-top-color:#ffd23f}
@keyframes dymek{0%,4%{opacity:0;transform:translateY(16px) scale(.9)}8%,28%{opacity:1;transform:translateY(0) scale(1)}33%,100%{opacity:0;transform:translateY(-10px) scale(.95)}}
@media (max-width:820px){
  .start .w{min-height:auto;padding:100px 0 40px;display:block}
  .start h1{font-size:40px}
  .start .obraz{width:100%;right:auto;margin-top:20px}
  .laptop{width:92%;margin:0 4%}
  .dymek{font-size:11px;padding:8px 10px}
}
/* ---- czolo: mapa polaczen (logo) ---- */
.mapa{width:100%;height:auto;overflow:visible}
.mapa .lin{fill:none;stroke:var(--blekit);stroke-width:26;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:var(--dl,3000px);stroke-dashoffset:calc(var(--dl,3000px) * (1 - var(--w)))}
.mapa .wezel{fill:var(--blekit);--k:clamp(0, calc((var(--w) - var(--o)) * 4), 1);opacity:var(--k);transform-box:fill-box;transform-origin:center;transform:scale(var(--k))}
.mapa .pod{font:600 30px var(--sans);fill:#1c1c21;--k:clamp(0, calc((var(--w) - var(--o) - .1) * 4), 1);opacity:var(--k)}
.mapa .pod.j{fill:#5e5f66;font-weight:500}

/* ---- schody ---- */
.schody{width:100%;height:auto;overflow:visible}
.schody text{font:700 17px var(--sans);fill:#fff}
.schody text.czas{font:500 12px var(--sans);fill:rgba(255,255,255,.8)}
.schody .tor{fill:none;stroke:url(#zloty);stroke-width:4;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:var(--dl,2000px);stroke-dashoffset:calc(var(--dl,2000px) * (1 - var(--w)))}
.schody .grot{opacity:clamp(0, calc((var(--w) - .92) * 14), 1)}
.schody .stopien{transform:translate(calc((1 - var(--w)) * var(--dx)), calc((1 - var(--w)) * var(--dy) + var(--t) * var(--s,0px)));opacity:clamp(0, calc(var(--w) * 3 - var(--o)), 1)}

/* ---- stos faktur ---- */
.faktura .w{min-height:96vh}
.stos{position:relative;width:100%;aspect-ratio:1/1;perspective:1600px;perspective-origin:50% 30%;transform:translateY(calc(var(--t) * -40px))}
.kartka{position:absolute;left:22%;top:46%;width:50%;aspect-ratio:1/1.25;background:#fff;border:1px solid #d9dbe2;
  box-shadow:0 30px 50px -25px rgba(20,30,70,.35);
  transform:translate(calc(var(--i) * (var(--w) * -34px)), calc(var(--i) * (-10px - var(--w) * 128px))) rotateX(42deg) rotateZ(-22deg);transform-origin:50% 50%;
  padding:5% 6%;color:#1c1c21;opacity:clamp(0, calc(var(--w) * 4 - var(--i) * .6), 1);font-size:clamp(6.5px,.82vw,10.5px);line-height:1.45;overflow:hidden}
.kartka .naglowek{display:flex;justify-content:space-between;align-items:baseline;font-weight:650;font-size:1.35em;margin-bottom:.6em;padding-bottom:.4em;border-bottom:2px solid #1c1c21}
.kartka .naglowek small{font-weight:400;color:#8a8b93;font-size:.75em}
.kartka .piecz{position:absolute;right:7%;bottom:7%;font-weight:650;font-size:1.05em;color:#158a4c;border:2px solid #158a4c;padding:3px 7px;transform:rotate(-8deg)}
.dok .strony{display:grid;grid-template-columns:1fr 1fr;gap:6%;margin-bottom:.8em}
.dok .strony b{display:block;font-size:.8em;letter-spacing:.06em;text-transform:uppercase;color:#8a8b93;margin-bottom:.2em}
.dok .strony span{display:block;color:#3c3d45}
.dok table{width:100%;border-collapse:collapse;font-size:.95em}
.dok th{font-size:.75em;letter-spacing:.05em;text-transform:uppercase;color:#8a8b93;text-align:left;padding:.25em 0;border-bottom:1px solid #d9dbe2;font-weight:600}
.dok td{padding:.3em 0;border-bottom:1px solid #eceef3;color:#3c3d45;vertical-align:top}
.dok th.l,.dok td.l{text-align:right;white-space:nowrap}
.dok .sumy{margin-top:.6em;margin-left:auto;width:58%}
.dok .sumy div{display:flex;justify-content:space-between;padding:.15em 0;color:#3c3d45}
.dok .sumy div.r{font-weight:700;color:#1c1c21;border-top:2px solid #1c1c21;margin-top:.2em;padding-top:.3em;font-size:1.1em}
.dok .dol-dok{margin-top:.8em;font-size:.8em;color:#8a8b93}
.dok .mail{color:#3c3d45}
.dok .mail p{margin:0 0 .6em}
.dok .zal{display:inline-block;border:1px solid #d9dbe2;padding:.2em .6em;border-radius:4px;font-weight:600;color:#1c1c21;margin-top:.4em}
.dok .status{display:inline-block;background:#e6f6ec;color:#158a4c;font-weight:700;padding:.15em .6em;border-radius:4px}

/* ---- kartony ---- */
.kartony{width:100%;height:auto;overflow:visible}
.kartony text{font:650 14px var(--sans);fill:#3b2a12}
.kartony .zero{fill:#c23b2b}
.kartony .karton{--k:clamp(0, calc((var(--w) - var(--o)) * 3), 1);transform:translateY(calc((1 - var(--k)) * -220px + var(--t) * var(--s,0px)));opacity:var(--k)}
.kartony .regal{transform:translateY(calc(var(--t) * 20px))}

/* ---- dokument ksef ---- */
.kolejka{position:relative;width:min(46%,300px);margin:0 auto;aspect-ratio:1/1.38}
.kolejka{width:min(56%,360px)}
.dokument{position:absolute;inset:0;background:#fff;color:#1c1c21;padding:6% 7%;font-size:clamp(6.5px,.85vw,11px);line-height:1.45;
  box-shadow:0 0 0 1px rgba(255,255,255,.08),0 0 140px rgba(110,140,255,.28),0 60px 80px -40px rgba(0,0,0,.9);transform:translateY(calc(var(--t) * -40px))}
.dokument.tlo{transform:translate(-9%,6%) rotate(-5deg) translateY(calc(var(--t) * -20px));opacity:.35;box-shadow:none}
.dokument.tlo2{transform:translate(9%,-5%) rotate(4deg) translateY(calc(var(--t) * -60px));opacity:.2;box-shadow:none}
.dokument .tyt{font-weight:650;font-size:1.25em;display:flex;justify-content:space-between;margin-bottom:.8em}
.dokument .tyt small{color:#8a8b93;font-weight:400;font-size:.85em}
.dokument .naglowek{display:flex;justify-content:space-between;align-items:baseline;font-weight:650;font-size:1.35em;margin-bottom:.6em;padding-bottom:.4em;border-bottom:2px solid #1c1c21}
.dokument .naglowek small{font-weight:400;color:#8a8b93;font-size:.75em}
.dokument tr,.dokument .strony,.dokument .sumy div{opacity:clamp(0, calc((var(--w) - var(--o,.2)) * 6), 1)}
.dokument .qr{position:absolute;right:8%;bottom:8%;width:22%;aspect-ratio:1;display:grid;grid-template-columns:repeat(9,1fr);gap:1px;opacity:clamp(0, calc((var(--w) - .55) * 5), 1)}
.dokument .qr b{background:#1c1c21;display:block}
.dokument .qr b.p{background:transparent}
.dokument .upo{position:absolute;left:8%;bottom:9%;font-weight:650;font-size:1.05em;line-height:1.3;color:#158a4c;border:2px solid #158a4c;padding:4px 8px;--k:clamp(0, calc((var(--w) - .78) * 6), 1);opacity:var(--k);transform:rotate(-6deg) scale(calc(2.2 - var(--k) * 1.2))}
.dokument .upo small{display:block;font-weight:400;color:#158a4c;font-size:.85em}
.daty{margin-top:1.4em;display:flex;gap:28px;font-size:13px;color:rgba(255,255,255,.65)}
.daty b{display:block;color:#fff;font-size:20px;font-weight:650}

/* ---- noc ---- */
.noc .w{min-height:96vh}
.noc .obraz{width:100%;right:0;top:auto;bottom:0;transform:none;height:100%}
.gory{position:absolute;left:0;right:0;bottom:0;width:100%;height:auto;display:block}
.miasto{position:absolute;left:0;right:0;bottom:0;width:100%;height:auto;display:block}
.miasto .okno{fill:#ffd98a;--k:clamp(0, calc((var(--w) - var(--o)) * 5), 1);opacity:calc(var(--k) * .9)}
.miasto .mig{animation:mrug var(--dt,9s) steps(1) infinite;animation-delay:var(--dl,0s)}
@keyframes mrug{0%,55%{opacity:1}56%,100%{opacity:.08}}
.gwiazdy.b{background-position:47px 31px;background-size:150px 110px;animation:migot 4.6s ease-in-out infinite}
.gwiazdy.a{animation:migot 6.2s ease-in-out infinite reverse}
@keyframes migot{0%,100%{opacity:.2}50%{opacity:.75}}
.ksiezyc{position:absolute;right:16%;top:16%;width:64px;height:64px;border-radius:50%;background:#f4e9c8;box-shadow:0 0 60px rgba(244,233,200,.5);transform:translateY(calc(var(--t) * -30px))}
.ksiezyc::after{content:"";position:absolute;left:-14px;top:-10px;width:56px;height:56px;border-radius:50%;background:#143d86}
.gwiazdy{position:absolute;inset:0;background-image:radial-gradient(#fff 0.7px,transparent 1.2px);background-size:120px 90px;opacity:.55;transform:translateY(calc(var(--t) * -60px))}
.lampki{display:flex;gap:6px;margin:1.2em 0 0;font-size:12px;color:rgba(255,255,255,.7);align-items:center;flex-wrap:wrap}
.lampki b{width:10px;height:10px;border-radius:50%;background:#59e08d;box-shadow:0 0 10px #59e08d;display:inline-block;--k:clamp(0, calc((var(--w) - .45 - var(--o)) * 8), 1);opacity:calc(.15 + var(--k) * .85);transform:scale(calc(.6 + var(--k) * .4))}
.lampki span{opacity:clamp(0, calc((var(--w) - .9) * 10), 1)}

/* ---- droga (cztery kroki) ---- */
.droga{width:100%;height:auto;overflow:visible}
.droga .trasa{fill:none;stroke:#c9cbd6;stroke-width:3;stroke-dasharray:8 8}
.droga .trasa.jazda{stroke:var(--blekit);stroke-dasharray:var(--dl,2000px);stroke-dashoffset:calc(var(--dl,2000px) * (1 - var(--w)))}
.droga .przystanek{--k:clamp(0, calc((var(--w) - var(--o)) * 5), 1);opacity:var(--k);transform:translateY(calc((1 - var(--k)) * 14px + var(--t) * var(--s,0px)))}
.droga .przystanek circle{fill:#fff;stroke:var(--blekit);stroke-width:3}
.droga .przystanek .nr{font:700 13px var(--sans);fill:var(--blekit)}
.droga .przystanek .naz{font:650 15px var(--sans);fill:#1c1c21}
.droga .przystanek .op{font:400 12px var(--sans);fill:#5e5f66}
.droga .przystanek .cn{font:600 12px var(--sans);fill:var(--blekit)}

/* ---- raport ---- */
.raport{margin-left:28%;width:60%;background:#fff;color:#1c1c21;padding:22px 24px;box-shadow:0 50px 80px -40px rgba(0,0,0,.7);transform:rotate(-2deg) translateY(calc(var(--t) * -30px))}
.raport .adres{font:500 13px var(--sans);color:#8a8b93;margin-bottom:12px;border-bottom:1px solid #e6e7ee;padding-bottom:10px;display:flex;justify-content:space-between}
.raport .adres i{font-style:normal;color:#158a4c}
.raport ul{list-style:none;margin:0;padding:0;font-size:14px}
.raport li{display:flex;gap:12px;padding:7px 0;border-bottom:1px solid #f0f0f4;align-items:baseline;--k:clamp(0, calc((var(--w) - .35 - var(--o)) * 5), 1);opacity:var(--k);transform:translateX(calc((1 - var(--k)) * -14px))}
.raport li:last-child{border:0}
.raport span{font:650 11px var(--sans);letter-spacing:.06em;min-width:52px}
.raport .b{color:#c23b2b}.raport .u{color:#b7791f}.raport .o{color:#158a4c}
.ziel form:not(.formularz-prosty){display:flex;margin:1.2em 0 .6em;max-width:420px}
.ziel input{flex:1;min-width:0;font:15px var(--sans);padding:11px 14px;border:1px solid rgba(255,255,255,.35);background:rgba(255,255,255,.08);color:#fff;border-radius:0}
.ziel input::placeholder{color:rgba(255,255,255,.65)}
.ziel button{font:600 15px var(--sans);padding:11px 18px;border:0;background:#fff;color:#0f3d2e;cursor:pointer}

/* ---- paragon (cennik) ---- */
.kasa{position:relative;width:min(78%,420px);margin:0 auto;transform:translateY(calc(var(--t) * -30px))}
.drukarka{position:relative;z-index:2;height:74px;background:linear-gradient(#3a3d46,#22242b);border-radius:12px 12px 6px 6px;box-shadow:0 30px 50px -25px rgba(0,0,0,.6)}
.drukarka::before{content:"";position:absolute;left:8%;right:8%;top:14px;height:6px;background:#0e0f13;border-radius:3px}
.drukarka::after{content:"";position:absolute;right:10%;top:34px;width:10px;height:10px;border-radius:50%;background:#59e08d;box-shadow:0 0 10px #59e08d}
.drukarka i{position:absolute;left:8%;right:8%;bottom:-1px;height:3px;background:#0e0f13}
.paragon{position:relative;z-index:1;margin:-6px 6% 0;background:#fff;color:#1c1c21;padding:26px 22px 34px;font:12.5px/1.5 ui-monospace,Menlo,Consolas,monospace;
  box-shadow:0 40px 60px -30px rgba(20,30,70,.45);clip-path:polygon(0 0,100% 0,100% calc(100% - 8px),97% 100%,94% calc(100% - 8px),91% 100%,88% calc(100% - 8px),85% 100%,82% calc(100% - 8px),79% 100%,76% calc(100% - 8px),73% 100%,70% calc(100% - 8px),67% 100%,64% calc(100% - 8px),61% 100%,58% calc(100% - 8px),55% 100%,52% calc(100% - 8px),49% 100%,46% calc(100% - 8px),43% 100%,40% calc(100% - 8px),37% 100%,34% calc(100% - 8px),31% 100%,28% calc(100% - 8px),25% 100%,22% calc(100% - 8px),19% 100%,16% calc(100% - 8px),13% 100%,10% calc(100% - 8px),7% 100%,4% calc(100% - 8px),1% 100%,0 calc(100% - 8px));
  transform-origin:top;transform:rotate(-1.2deg)}
.paragon .wys{overflow:hidden;max-height:calc(var(--w) * 640px)}
.paragon .naglowek{text-align:center;font-weight:700;letter-spacing:.08em;margin-bottom:2px}
.paragon .drobne{text-align:center;color:#6b6c73;font-size:11px}
.paragon hr{border:0;border-top:1px dashed #b9bbc4;margin:10px 0}
.paragon .poz{display:flex;justify-content:space-between;gap:10px}
.paragon .poz.sz{color:#6b6c73;font-size:11px;padding-left:22px}
.paragon .poz b{font-weight:700}
.paragon .razem{display:flex;justify-content:space-between;gap:10px;font-weight:700;font-size:14px;margin-top:4px}
.paragon .poz span:last-child{white-space:nowrap}
.paragon .kod{height:34px;margin:12px 10% 0;background:repeating-linear-gradient(90deg,#1c1c21 0 2px,transparent 2px 4px,#1c1c21 4px 5px,transparent 5px 9px,#1c1c21 9px 12px,transparent 12px 14px)}
.paragon .kod+p{text-align:center;font-size:10px;color:#6b6c73;margin:4px 0 0}
.cennik-tabela table{font:13px/1.5 ui-monospace,Menlo,Consolas,monospace}
.cennik-tabela th{font-family:var(--sans)}
.cennik-tabela td{border-bottom:1px dashed #c9cbd6}

/* ---- ksiega realizacji ---- */
.ksiega-tlo{background:#0b0b0d radial-gradient(60% 50% at 50% 40%,#1c1d24,#0b0b0d 70%)}
.ksiega-tlo .w{display:block;min-height:auto;padding:12vh 0 10vh}
.ksiega-tlo .tekst{max-width:560px;margin-bottom:34px}
.ksiega{position:relative;width:min(92vw,980px);margin:0 auto;perspective:2200px}
.karty{position:relative;aspect-ratio:16/9.6}
.karta{position:absolute;inset:0;border-radius:22px;overflow:hidden;color:#fff;padding:5% 6%;backface-visibility:hidden;transform-origin:100% 50%;box-shadow:0 60px 100px -40px rgba(0,0,0,.9);opacity:0;pointer-events:none;transform:rotateY(0)}
.karta.aktywna{opacity:1;pointer-events:auto;z-index:3}
.karta.pod-spodem{opacity:1;z-index:2;transform:scale(.985)}
.karta.odchodzi{z-index:4;opacity:1;animation:strona-w-prawo .9s cubic-bezier(.6,.05,.3,1) forwards}
.karta.wraca{z-index:4;opacity:1;transform-origin:0 50%;animation:strona-z-lewej .9s cubic-bezier(.6,.05,.3,1) forwards}
@keyframes strona-w-prawo{0%{transform:rotateY(0)}60%{opacity:1}100%{transform:rotateY(-115deg);opacity:0}}
@keyframes strona-z-lewej{0%{transform:rotateY(115deg);opacity:0}40%{opacity:1}100%{transform:rotateY(0);opacity:1}}
.karta .duze{position:absolute;left:5%;top:8%;right:5%;font-size:var(--rozmiar,clamp(40px,8.2vw,116px));line-height:.9;font-weight:900;letter-spacing:-.04em;text-transform:uppercase;color:rgba(255,255,255,.92);word-break:keep-all}
.karta .duze small{display:block;font-size:.26em;font-weight:500;letter-spacing:.02em;text-transform:none;margin-bottom:.35em;opacity:.85}
.karta .zdjecie{position:absolute;right:4%;bottom:7%;width:56%;aspect-ratio:16/10;border-radius:10px;overflow:hidden;box-shadow:0 40px 60px -20px rgba(0,0,0,.7);transform:rotate(-3deg);border:1px solid rgba(255,255,255,.25)}
.karta .zdjecie img{width:100%;height:100%;object-fit:cover;object-position:top left;display:block}
.karta .zdjecie.panelowe{width:56%;right:4%;bottom:7%;aspect-ratio:16/11;background:#14161d;color:#e9ecf3;padding:4% 4.5%;font:500 clamp(8px,.9vw,12px)/1.4 var(--sans);transform:rotate(-4deg)}
.panel .gora-p{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.9em;font-weight:700;font-size:1.2em}
.panel .gora-p small{font-weight:500;color:#8f95a3;font-size:.8em}
.panel .kafle{display:grid;grid-template-columns:repeat(3,1fr);gap:.6em}
.panel .kafel{background:#1d2029;border-radius:6px;padding:.6em .7em;border-left:3px solid #59e08d}
.panel .kafel.uwaga{border-left-color:#f0b03c}
.panel .kafel b{display:block;font-size:.95em;margin-bottom:.15em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.panel .kafel span{display:block;color:#8f95a3;font-size:.85em}
.panel .kafel i{display:flex;gap:2px;align-items:flex-end;height:14px;margin-top:.4em}
.panel .kafel i em{flex:1;background:#2f7f5b;border-radius:1px}
.panel .kafel.uwaga i em{background:#8a6a2a}
.panel .dol{display:flex;gap:1.4em;margin-top:.9em;color:#8f95a3;font-size:.9em}
.panel .dol b{color:#fff;font-size:1.3em;margin-right:.3em}
.spr .gora-p{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.6em;padding-bottom:.4em;border-bottom:1px solid #e6e7ee;font-weight:700;color:#1c1c21}
.spr .gora-p small{color:#8a8b93;font-weight:500}
.spr .wynik{display:flex;align-items:center;gap:.8em;margin-bottom:.6em;color:#1c1c21}
.spr .wynik b{font-size:2.2em;font-weight:800;line-height:1}
.spr .wynik span{color:#5e5f66;font-size:.9em}
.spr .pasek-w{height:6px;background:#eceef3;border-radius:3px;overflow:hidden;margin-bottom:.7em}
.spr .pasek-w i{display:block;height:100%;width:62%;background:linear-gradient(90deg,#c23b2b,#b7791f 50%,#158a4c)}
.spr ul{list-style:none;margin:0;padding:0;font-size:.95em;color:#1c1c21}
.spr li{display:flex;gap:.7em;padding:.3em 0;border-bottom:1px solid #f0f0f4;align-items:baseline}
.spr li span{font-weight:700;font-size:.8em;letter-spacing:.05em;min-width:3.6em}
.spr .b{color:#c23b2b}.spr .u{color:#b7791f}.spr .o{color:#158a4c}
.karta .zdjecie.jasne{background:#fff;color:#1c1c21}
.karta .opis{position:absolute;left:6%;bottom:8%;max-width:34%;font-size:clamp(11px,1.2vw,15px);line-height:1.45}
.karta .opis b{display:block;font-size:1.15em;margin-bottom:.3em}
.karta .opis a{color:#fff}
.ksiega .strzalka{position:absolute;top:50%;width:64px;height:44px;margin-top:-22px;background:none;border:0;cursor:pointer;color:#fff;opacity:.85;padding:0}
.ksiega .strzalka:hover{opacity:1}
.ksiega .strzalka.lewa{left:-80px}.ksiega .strzalka.prawa{right:-80px}
.ksiega .strzalka svg{width:100%;height:100%;overflow:visible}
.kropy{display:flex;justify-content:center;gap:2px;margin-top:12px}
.kropy button{position:relative;width:32px;height:32px;border:0;padding:0;cursor:pointer;background:transparent;border-radius:50%}
.kropy button::before{content:"";position:absolute;left:50%;top:50%;width:12px;height:12px;border-radius:50%;background:rgba(255,255,255,.25);transform:translate(-50%,-50%);transition:transform .3s,background .3s}
.kropy button.tu::before{background:#fff;transform:translate(-50%,-50%) scale(1.35)}
@media (max-width:1140px){.ksiega .strzalka.lewa{left:6px}.ksiega .strzalka.prawa{right:6px}}
@media (max-width:820px){
  .karty{aspect-ratio:3/4}
  .karta .duze{font-size:44px}
  .karta .zdjecie{width:78%;right:-8%;bottom:20%}
  .karta .opis{max-width:88%;bottom:5%}
  .karta .opis span{display:none}
  .ksiega .strzalka{width:44px;height:44px;margin-top:-22px}
}

/* ---- ekrany ---- */
.realizacje .obraz{width:min(44vw,640px)}
.ekrany{position:relative;width:100%;aspect-ratio:1/0.7}
.ekran{position:absolute;background:#fff;border:1px solid #d9dbe2;box-shadow:0 40px 60px -30px rgba(20,30,70,.4);overflow:hidden}
.ekran img{display:block;width:100%;height:100%;object-fit:cover;object-position:top left}
.ekran .screen-bg{display:block;width:100%;height:100%;background-size:cover;background-position:top left}
/* A responsive picture must fill the frame, not size itself to its intrinsic image height. */
.ekrany .ekran>picture,.karta .zdjecie:not(.panelowe)>picture{position:absolute;inset:0;display:block;width:100%;height:100%;margin:0;padding:0}
.ekrany .ekran>img,.ekrany .ekran>picture>img,.karta .zdjecie:not(.panelowe)>img,.karta .zdjecie:not(.panelowe)>picture>img{display:block;width:100%;height:100%;margin:0;padding:0;object-fit:cover;object-position:center;max-height:none}
.studium>figure>picture{display:block;line-height:0;margin:0;padding:0}
.studium>figure>picture>img{display:block;width:100%;height:auto;margin:0;object-fit:cover}

@media(min-width:821px){.ekran.b .screen-bg{background-image:url("zdjecia/ostre-20261009/rental-pulpit-800.webp");background-image:image-set(url("zdjecia/ostre-20261009/rental-pulpit-800.webp") 1x,url("zdjecia/ostre-20261009/rental-pulpit-1600.webp") 2x)}}
@media(max-width:820px){.ekran.b{display:none}}
.ekran.a{left:6%;top:6%;width:58%;aspect-ratio:16/10;transform:translate(calc((1 - var(--w)) * -160px), calc(var(--t) * 40px)) rotate(-3deg);opacity:clamp(0, calc(var(--w) * 2.5), 1)}
.ekran.b{left:44%;top:34%;width:50%;aspect-ratio:16/10;transform:translate(calc((1 - var(--w)) * 160px), calc(var(--t) * -40px)) rotate(2deg);opacity:clamp(0, calc(var(--w) * 2.5 - .4), 1)}
.wpisy{list-style:none;padding:0;margin:1.2em 0 0}
.wpisy li{margin-bottom:.9em}
.wpisy small{display:block;color:var(--szary);font-size:13px}

/* ---- koniec i stopka ---- */
.koniec .w{min-height:auto;padding:14vh 0 6vh}
.stopka{margin:0;padding:54px max(24px,calc(50vw - 560px)) 28px;color:var(--szary);font-size:13px;border-top:1px solid var(--kreska)}
.stopka a{color:var(--szary)}
.stopka-grid{display:grid;grid-template-columns:1.45fr 1fr 1fr 1fr;gap:42px;max-width:1120px;margin:0 auto}
.stopka-grid>div>strong{display:block;color:var(--tekst);font-size:14px;margin-bottom:12px}
.stopka-grid>div:not(.stopka-brand) a{display:block;text-decoration:none;margin:7px 0;line-height:1.35}
.stopka-grid>div:not(.stopka-brand) a:hover{text-decoration:underline}
.stopka-brand p{margin:8px 0;max-width:300px}
.stopka .stopka-cta{display:inline-block;background:var(--blekit);color:#fff;text-decoration:none;font-weight:700;padding:8px 12px;border-radius:999px;margin:4px 0}
.stopka-dol{max-width:1120px;margin:38px auto 0;padding-top:18px;border-top:1px solid var(--kreska);display:flex;gap:20px;flex-wrap:wrap;color:var(--szary)}
.stopka-dol span{margin-right:auto}
@media(max-width:820px){.stopka{padding:38px 22px 24px}.stopka-grid{grid-template-columns:1fr 1fr;gap:28px 24px}.stopka-brand{grid-column:1/-1}.stopka-dol{margin-top:28px}}
@media(max-width:520px){.stopka-grid{grid-template-columns:1fr}.stopka-brand{grid-column:auto}.stopka-dol{display:block}.stopka-dol>*{display:block;margin:7px 0}}

/* ---- tresc podstron ---- */
.tresc{margin-left:var(--lewy);max-width:600px;padding:60px 24px 20px 0}
.tresc h2{margin-top:2.2em}
.tresc h2:first-child{margin-top:0}
.tresc h3{font-size:15px}
.tresc p{color:#33343b;text-wrap:pretty}
.tresc ul,.tresc ol{padding-left:1.2em;color:#33343b}
.tresc li{margin-bottom:.4em}
.etykieta{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--szary);margin-bottom:1.4em}
.ciemny .etykieta{color:rgba(255,255,255,.84)}
.pod h1{font-size:26px;line-height:1.3;font-weight:650;max-width:600px}
.pod .wstep{font-size:17px;line-height:1.55;max-width:520px}
.pytania details{border-top:1px solid var(--kreska);padding:.7em 0}
.pytania details:last-child{border-bottom:1px solid var(--kreska)}
.pytania summary{cursor:pointer;font-weight:600;list-style:none;position:relative;padding-right:28px}
.pytania summary::-webkit-details-marker{display:none}
.pytania summary::after{content:"+";position:absolute;right:4px;top:0;color:var(--blekit)}
.pytania details[open] summary::after{content:"–"}
.pytania details>p{margin:.6em 0 .3em}
.pudlo{border-left:3px solid var(--blekit);padding:.2em 0 .2em 18px;margin:2em 0}
.pudlo h3{margin-top:0}
a.przycisk{display:inline-block;font-weight:600}
a.przycisk svg{display:none}
.przewijane{max-width:100%;overflow-x:auto;margin:1.5em 0;-webkit-overflow-scrolling:touch;scrollbar-gutter:stable}.przewijane:focus-visible{outline:3px solid #ffd23f;outline-offset:3px}.przewijane table{min-width:460px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:.7em .8em .7em 0;border-bottom:1px solid var(--kreska)}
th{font-weight:650;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--szary)}
td.kwota{white-space:nowrap;font-weight:600}
.siatka-problemow{display:block}
.problem{padding:1.6em 0;border-top:1px solid var(--kreska);position:relative}
.problem-ikona{display:inline-flex;width:34px;height:34px;color:var(--blekit);margin-bottom:.6em}
.problem-ikona svg{width:100%;height:100%}
.problem h2{font-size:18px;margin-top:0}
.problem .objaw{margin-bottom:.8em}
.naprawa{border-left:3px solid var(--blekit);padding-left:16px}
.naprawa-etykieta{display:block;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--blekit);font-weight:650;margin-bottom:.3em}
.naprawa p{margin:0}
.problem .cena{font-size:13px;margin-top:.8em}
.projekty{display:block}
.projekt{display:block;padding:1.4em 0;border-top:1px solid var(--kreska);color:inherit;text-decoration:none}
.projekt .rodzaj{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--szary);margin-bottom:.4em}
.projekt h2{margin:.2em 0 .5em;font-size:17px}
.projekt .stan{color:var(--link);text-decoration:underline;margin:.4em 0 0}
a.projekt:hover .stan{color:#0a2a8c}
.uslugi,.metryka{list-style:none;padding:0;margin:1.2em 0 2em;display:flex;flex-wrap:wrap;gap:.4em 1.2em;font-size:13px;color:var(--szary)}
.uslugi li::before,.metryka li::before{content:"·";margin-right:.6em;color:var(--blekit)}
.studium{margin-top:3em;padding-top:2em;border-top:1px solid var(--kreska)}
.studium figure,.tresc figure{margin:1.6em 0}
.tresc figure img{border:1px solid var(--kreska);box-shadow:0 30px 50px -30px rgba(20,30,70,.35)}
.tresc figcaption{font-size:13px;color:var(--szary);margin-top:.5em}
.przypis{font-size:13px;color:var(--szary);font-style:italic;margin-top:2em}
.kafelki{display:block}
.kafelek{padding:1.2em 0;border-top:1px solid var(--kreska)}
.kafelek .ikona{width:28px;height:28px;color:var(--blekit);display:block;margin-bottom:.5em}
.kafelek h3{margin:0 0 .3em}
.kafelek p{margin:0}
.formularz-prosty{display:block;max-width:520px;margin:1.4em 0}.sprawdzarka-glowny{display:flex;align-items:stretch}.sprawdzarka-glowny input{margin:0;flex:1;min-width:0}.sprawdzarka-glowny button{flex:none}
.formularz-prosty label{position:absolute;left:-9999px}
.formularz-prosty input{flex:1;min-width:0;min-height:44px;box-sizing:border-box;font:15px var(--sans);padding:11px 14px;border:1px solid #7f899f;border-radius:0}
.formularz-prosty button{min-height:44px;font:600 15px var(--sans);padding:11px 18px;border:0;background:var(--blekit);color:#fff;cursor:pointer;white-space:nowrap;display:inline-flex;align-items:center;gap:8px}
.czolo .formularz-prosty{max-width:520px;margin-bottom:.6em}
.czolo .nota{font-size:14px;max-width:520px}
.ciemny .formularz-prosty input{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.65);color:#fff}
.ciemny .formularz-prosty button{background:#fff;color:#0f3d2e}
.rzad-przyciskow{display:flex;flex-wrap:wrap;gap:.6em 1.4em}
.tresc .etykieta{margin-top:2.5em}

.sprawdzarka-opcje{flex-basis:100%;width:100%;margin-top:10px}.sprawdzarka-opcje summary{cursor:pointer;font-size:13px;font-weight:650;line-height:22px;padding:11px 0;color:inherit}.sprawdzarka-opcje-grid{display:grid;grid-template-columns:1fr;gap:6px;margin-top:10px}.sprawdzarka-opcje-grid label{position:static!important;font-size:12px;font-weight:650}.formularz-prosty .sprawdzarka-opcje-grid input{width:100%;border-radius:0;box-sizing:border-box}.ciemny .sprawdzarka-opcje summary{color:#fff}@media(max-width:620px){.sprawdzarka-glowny{display:flex;flex-wrap:wrap}.sprawdzarka-glowny input{flex:1 1 100%;width:100%}.sprawdzarka-glowny button{margin-top:0}}

/* wjazd tekstu */
.wjazd{opacity:0;transform:translateY(14px);transition:opacity .7s ease,transform .7s ease}
.czolo .wjazd,.start .wjazd,.tresc>.blok.wjazd{opacity:1;transform:none}
.wjazd.widac{opacity:1;transform:none}

@media (max-width:820px){
  :root{--lewy:22px}
  .tekst,.czolo .tekst{max-width:none;padding-right:22px}
  .rozdzial .w{min-height:auto;display:block;padding:12vw 0 8vw}
  .rozdzial .obraz,.realizacje .obraz{position:relative;right:auto;top:auto;transform:none;width:100%;margin:28px 0 0;padding:0 22px}
  .czolo .w,.czolo.rozdzial .w,.czolo.pod .w{min-height:auto;padding:110px 0 60px}
  .pod .kasa{transform:none}
  .skos-dol,.skos-dol.lewo{clip-path:polygon(0 0,100% 0,100% calc(100% - 10vw),0 100%)}
  .skos-gora,.skos-oba{clip-path:polygon(0 10vw,100% 0,100% calc(100% - 10vw),0 100%);margin-top:-10vw;padding-top:10vw}
  .noc .obraz{position:absolute;padding:0;margin:0;height:100%;bottom:0}
  .noc .w{min-height:70vh;position:relative}
  .noc .tekst{position:relative;z-index:2}
  .kolejka{width:60%}
  .stos{aspect-ratio:1/0.95;perspective:900px}
  .kartka{left:22%;top:44%;width:54%;transform:translate(calc(var(--i) * (var(--w) * -18px)), calc(var(--i) * (-8px - var(--w) * 80px))) rotateX(42deg) rotateZ(-18deg)}
  .raport{margin-left:0;width:100%}
  .tresc{padding:40px 22px 20px 0}
  .mapa .pod{font-size:34px}
}

/* ---- dostępność, nawigacja i breadcrumbs ---- */
.skip-link{position:fixed;left:16px;top:-80px;z-index:200;background:#fff;color:#111;padding:10px 14px;border-radius:8px;box-shadow:0 8px 30px rgba(0,0,0,.18);transition:top .15s}
.skip-link:focus{top:12px}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,summary:focus-visible{outline:3px solid #fff;outline-offset:2px;box-shadow:0 0 0 6px #1550d0}
.gora nav .nav-cta{background:#1a5cf0;color:#fff;text-decoration:none;padding:5px 11px;border-radius:999px;font-weight:700}
body.ciemna .gora nav .nav-cta{background:#fff;color:#143a8b}
.okruszki{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;margin:0 0 18px;color:var(--szary)}
.okruszki a{color:inherit;text-decoration:none}
.okruszki a:hover{text-decoration:underline}
.okruszki span[aria-hidden]{opacity:.55}
.ciemny .okruszki{color:rgba(255,255,255,.84)}
.article-meta{font-size:12.5px;color:var(--szary);margin:14px 0 0}
.article-meta a{color:inherit}
.ciemny .article-meta{color:rgba(255,255,255,.84)}

.privacy-actions{display:flex;gap:10px;flex-wrap:wrap;margin:.9em 0}
.privacy-actions button{min-height:44px;font:600 14px var(--sans);border:1px solid #7f899f;background:#fff;color:var(--link);padding:10px 12px;border-radius:8px;cursor:pointer}
.privacy-actions button:hover{background:#f3f6ff}


.case-next{margin:2rem 0;padding:18px;border:1px solid #dfe2ea;border-radius:12px;background:#f8f9fc}.case-next strong{display:block;margin-bottom:.4em}.case-next p{margin:0}
.case-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:1.3rem 0 2rem}.case-facts>div{padding:13px 14px;border:1px solid var(--kreska);border-radius:10px;background:rgba(255,255,255,.55)}.case-facts small{display:block;text-transform:uppercase;letter-spacing:.12em;font-size:10px;color:var(--szary);margin-bottom:4px}.case-facts strong{display:block;font-size:13.5px;line-height:1.4}.case-jump{display:flex;flex-wrap:wrap;gap:8px;margin:1.2rem 0 2.5rem}.case-jump a{display:inline-block;padding:7px 10px;border:1px solid var(--kreska);border-radius:999px;text-decoration:none;font-size:12.5px}.case-jump a:hover{border-color:#9fabce}
@media(max-width:680px){.case-facts{grid-template-columns:1fr}}

.kontakt-skroty{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:1.5rem 0 2rem}.kontakt-skroty a{display:flex;flex-direction:column;padding:14px 16px;border:1px solid #dfe2ea;border-radius:11px;background:#fff;text-decoration:none}.kontakt-skroty strong{color:var(--tekst);font-size:14px}.kontakt-skroty span{color:var(--szary);font-size:12.5px;margin-top:4px}.kontakt-skroty a:hover{border-color:#9fabce}
@media(max-width:620px){.kontakt-skroty{grid-template-columns:1fr}}

.zrodla-box{margin:2rem 0;padding:16px 18px;border:1px solid #dfe2ea;border-radius:12px;background:#f8f9fc}.zrodla-box>strong{display:block;margin-bottom:.5em}.zrodla-box ul{margin:.6em 0;padding-left:1.15em}.zrodla-box p{font-size:13px;color:var(--szary);margin:.7em 0 0}


/* ---- progressive enhancement / brak JavaScriptu ---- */
.no-js .brief-form,
.no-js .roi-calc,
.no-js .kwalifikator,
.no-js .poradniki-filter{display:none!important}
@media(max-width:900px){
  .no-js .mobile-actions{display:none!important}
  .no-js .gora nav{
    opacity:1!important;visibility:visible!important;pointer-events:auto!important;
    transform:none!important;top:58px!important;background:#fff!important
  }
  .no-js body.ciemna .gora nav{background:#102a5e!important}
  .no-js .gora nav .nav-cta{display:block!important}
}

/* ---- powiązane / kwalifikator / wyszukiwanie ---- */
.porownanie-opcji{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:1.5rem 0 2.4rem}.porownanie-opcji>div{padding:15px;border:1px solid var(--kreska);border-radius:10px;background:#fff}.porownanie-opcji small{display:block;text-transform:uppercase;letter-spacing:.1em;font-size:9.5px;color:var(--szary);margin-bottom:6px}.porownanie-opcji strong,.porownanie-opcji span{display:block}.porownanie-opcji strong{font-size:13.5px;line-height:1.4;margin-bottom:6px}.porownanie-opcji span{font-size:12.5px;line-height:1.45;color:var(--szary)}
@media(max-width:680px){.porownanie-opcji{grid-template-columns:1fr}}
.tresc h2[id]{scroll-margin-top:92px}
.spis-tresci{margin:0 0 2.5rem;padding:16px 18px;border:1px solid var(--kreska);border-radius:11px;background:#fafbfe}.spis-tresci strong{display:block;margin-bottom:8px;font-size:13px}.spis-tresci ol{margin:0;padding-left:1.25rem;columns:2;column-gap:28px}.spis-tresci li{break-inside:avoid;margin:.28rem 0;font-size:12.5px;line-height:1.4}.spis-tresci a{text-decoration:none}.spis-tresci a:hover{text-decoration:underline}
@media(max-width:640px){.spis-tresci ol{columns:1}}
.autor-box{display:grid;grid-template-columns:auto 1fr;gap:16px;margin:3rem 0 1rem;padding:18px;border:1px solid var(--kreska);border-radius:12px;background:#fafafa}.autor-box p{margin:.35em 0;font-size:13.5px}.autor-znak{display:flex;align-items:center;justify-content:center;width:42px;height:42px;border-radius:50%;background:#194586;color:#fff;font-size:12px;font-weight:800;letter-spacing:.04em}.artykul-body{display:block}
.powiazane{margin:4rem 0 1.5rem;padding-top:2rem;border-top:1px solid var(--kreska)}
.powiazane h2{margin:.15em 0 1em}.powiazane-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.powiazane-karta{display:flex;flex-direction:column;min-height:155px;padding:18px;border:1px solid #d9dce6;border-radius:12px;background:#fff;color:var(--tekst);text-decoration:none}
.powiazane-karta:hover{border-color:#9fabce;transform:translateY(-2px)}.powiazane-karta strong{margin-bottom:8px}.powiazane-karta span{font-size:13.5px;color:var(--szary)}.powiazane-karta i{margin-top:auto;font-size:22px;color:var(--link);font-style:normal}
.print-action{margin:-.9rem 0 2.2rem}.print-action button{min-height:44px;border:1px solid #7f899f;background:#fff;color:var(--link);font:600 13px var(--sans);padding:10px 12px;border-radius:8px;cursor:pointer}.print-action button:hover{background:#f4f7ff}
.zrodla-box{margin:1.6rem 0;padding:15px 17px;border:1px solid #dfe2ea;border-radius:10px;background:#f8f9fc}.zrodla-box>strong{display:block}.zrodla-data{display:block;margin:.15rem 0 .6rem;font-size:11px;color:var(--szary)}.zrodla-box ul{margin:.5rem 0 .8rem;padding-left:1.2rem}.zrodla-box p:last-child{margin-bottom:0}
.price-note{margin:0 0 2rem;padding:12px 14px;border-left:3px solid var(--blekit);background:#f7f8fb;font-size:13.5px}.price-note strong{color:var(--tekst)}
.roi-calc{margin:1rem 0 3rem;padding:24px;border:1px solid #dfe2ea;border-radius:16px;background:#f8f9fc}.roi-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.roi-grid label{display:block;font-weight:650;font-size:13.5px}.roi-grid label>span{display:block;margin-bottom:7px}.roi-grid label>div{display:flex;align-items:center;gap:8px}.roi-grid input{width:100%;min-width:0;min-height:44px;box-sizing:border-box;padding:10px 11px;border:1px solid #7f899f;border-radius:8px;background:#fff;font:15px var(--sans)}.roi-grid small{white-space:nowrap;color:var(--szary);font-weight:500}.roi-grid em{display:block;font-style:normal;font-weight:400;font-size:11.5px;line-height:1.4;color:var(--szary);margin-top:6px}.roi-wide{grid-column:1/-1}.roi-results{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:22px 0}.roi-results>div{padding:13px 10px;border-radius:10px;background:#fff;border:1px solid #e0e3ec}.roi-results small,.roi-results strong{display:block}.roi-results small{font-size:10.5px;line-height:1.3;color:var(--szary);min-height:28px}.roi-results strong{font-size:18px;line-height:1.25;margin-top:4px}.roi-note{font-size:12.5px;color:var(--szary);padding-top:4px}.roi-calc .przycisk{margin-top:.3rem}
@media(max-width:760px){.roi-grid{grid-template-columns:1fr}.roi-wide{grid-column:auto}.roi-results{grid-template-columns:1fr 1fr}.roi-results>div:last-child{grid-column:1/-1}.roi-calc{padding:18px}}
.kwalifikator{margin:2.5rem 0;padding:24px;border:1px solid #dfe2ea;border-radius:16px;background:#f8f9fc}.kwalifikator-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.kwalifikator label{font-weight:650;font-size:14px}.kwalifikator select{width:100%;min-height:44px;margin-top:7px;padding:10px;border:1px solid #7f899f;border-radius:8px;background:#fff}.kwalifikator-wynik{margin-top:18px;padding:17px;border-left:3px solid var(--blekit);background:#fff}
.problem-start{display:grid;gap:5px;margin:0 0 2.4rem;padding:16px 18px;border-left:3px solid var(--blekit);background:#f7f9ff}.problem-start strong{font-size:14px}.problem-start span{font-size:13px;color:var(--szary)}.problem-start a{font-size:13px;font-weight:650;margin-top:3px}.ecommerce-hub{margin-top:1rem}
.poradniki-filter{margin:1.8rem 0 2.8rem}.poradniki-filter label{display:block;font-size:13px;font-weight:700;margin-bottom:7px}.poradniki-filter input{width:100%;padding:12px 14px;border:1px solid #7f899f;border-radius:9px;background:#fff;font:15px var(--sans)}.poradniki-filter .wyniki{display:block;font-size:12.5px;color:var(--szary);margin-top:7px}.wpisy li[hidden]{display:none!important}
@media(max-width:760px){.powiazane-grid,.kwalifikator-grid{grid-template-columns:1fr}.powiazane-karta{min-height:0}.kwalifikator{padding:18px}}

/* ---- formularz briefu ---- */
.brief-form{margin:2rem 0 3rem;padding:26px;border:1px solid #dfe2ea;background:#f8f9fc;border-radius:16px}
.brief-form label{display:block;margin:0 0 18px}
.brief-form label>span{display:block;font-weight:650;margin-bottom:7px;color:#252631}
.brief-form label small{font-weight:400;color:var(--szary)}
.brief-form input,.brief-form select,.brief-form textarea{width:100%;font:15px/1.5 var(--sans);color:var(--tekst);background:#fff;border:1px solid #7f899f;border-radius:8px;padding:11px 12px}
.brief-form textarea{resize:vertical;min-height:90px}
.brief-form input:focus,.brief-form select:focus,.brief-form textarea:focus{border-color:#1a5cf0}
.brief-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}
.brief-actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:8px}
.brief-actions .przycisk{min-height:44px;display:inline-flex;align-items:center;justify-content:center;padding:11px 14px;border:0;border-radius:8px;font:600 14px var(--sans);cursor:pointer}
.brief-actions .drugorzedny{background:#fff;color:#1a5cf0;border:1px solid #7f899f}
.brief-clear{min-height:44px;border:0;background:transparent;color:var(--szary);font:13px var(--sans);text-decoration:underline;cursor:pointer;padding:10px 6px}
.brief-info{font-size:13px;color:var(--szary);margin:15px 0 0}
.brief-fallback{margin-top:14px;width:100%;font:13px/1.45 ui-monospace,Menlo,Consolas,monospace;background:#fff;border:1px solid #7f899f;border-radius:8px;padding:12px;white-space:pre-wrap}
@media(max-width:680px){.brief-grid{grid-template-columns:1fr}.brief-form{padding:18px}.brief-actions{align-items:stretch}.brief-actions .przycisk{width:100%;text-align:center}}


@media print{
  @page{size:A4;margin:16mm}
  html{scroll-behavior:auto}
  body{background:#fff!important;color:#000!important;font-size:11pt;overflow:visible}
  .gora,.stopka,.koniec,.mobile-actions,.menu-toggle,.strzalka,.kropy,.brief-actions,.poradniki-filter,.kwalifikator,.print-action,.skip-link,.okruszki,.powiazane,.no-print{display:none!important}
  .czolo,.rozdzial,.tresc,.studium{clip-path:none!important;background:#fff!important;color:#000!important;margin:0!important;overflow:visible!important}
  .czolo .w,.rozdzial .w{min-height:0!important;padding:0 0 18mm!important;display:block!important}
  .czolo .tekst,.tekst,.tresc{margin:0!important;max-width:none!important;padding:0!important;color:#000!important}
  .czolo .obraz,.rozdzial .obraz{display:none!important}
  .wjazd{opacity:1!important;transform:none!important}
  a{color:#000!important;text-decoration:none!important}
  a[href^="http"]::after{content:" (" attr(href) ")";font-size:8pt;color:#555}
  figure,.pudlo,.case-facts,.powiazane-karta,.autor-box,table{break-inside:avoid}
  picture,img{max-width:100%!important}
  .powiazane-grid{grid-template-columns:1fr 1fr 1fr!important}
  .tresc table{font-size:9pt}
}

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{transition-duration:.01ms!important;transition-delay:0s!important}
  .wjazd{opacity:1!important;transform:none!important;transition:none!important}
  .rozdzial{--w:1!important;--t:0!important}
  .start .cta svg,.laptop,.mosty .lampka.a,.mosty .pakiet,.mosty .puls,
  .miasto .mig,.gwiazdy.a,.gwiazdy.b{animation:none!important}
  .laptop{transform:perspective(1800px) rotateY(-16deg) rotateX(5deg) rotate(-2deg)!important}
  .dymek{display:none!important}
  .karta.odchodzi,.karta.wraca{animation:none!important}
}
"""

# ---------------------------------------------------------------- JS
JS = r"""
(function(){
  var spokoj = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var NS = "http://www.w3.org/2000/svg";
  var UMAMI_URL = "https://statystyki.automatyzacjesklepow.pl/script.js";
  var UMAMI_WEBSITE_ID = "7bf89ecf-f690-413f-863a-658c0a0f4baa";
  function analyticsDisabled(){try{return localStorage.getItem("umami.disabled")==="1";}catch(e){return false;}}
  function loadAnalytics(){
    if(analyticsDisabled()){window.siteAnalyticsEnabled=false;return false;}
    window.siteAnalyticsEnabled=true;
    if(document.querySelector('script[data-umami-loader="1"]'))return true;
    var sc=document.createElement("script");
    sc.defer=true;
    sc.src=UMAMI_URL;
    sc.setAttribute("data-website-id",UMAMI_WEBSITE_ID);
    sc.setAttribute("data-umami-loader","1");
    document.head.appendChild(sc);
    return true;
  }
  window.siteTrack = window.siteTrack || function(name,data){try{if(window.umami&&typeof window.umami.track==="function")window.umami.track(name,data||{});}catch(e){}};
  loadAnalytics();

  // kartony: rysowane izometrycznie na regale
  document.querySelectorAll("svg.kartony").forEach(function(svg){
    function wielokat(pkt, kolor, klasa){
      var p = document.createElementNS(NS,"polygon");
      p.setAttribute("points", pkt.map(function(q){return q.join(",")}).join(" "));
      p.setAttribute("fill", kolor); if (klasa) p.setAttribute("class", klasa); return p;
    }
    function karton(cx, cy, s, h, napis, zero, par, o){
      var g = document.createElementNS(NS,"g"); g.setAttribute("class","karton");
      g.style.setProperty("--s", par + "px"); g.style.setProperty("--o", o);
      var w = s, d = s*0.5;
      g.appendChild(wielokat([[cx,cy-h],[cx+w,cy-h-d],[cx,cy-h-2*d],[cx-w,cy-h-d]],"#eacf9d"));
      g.appendChild(wielokat([[cx-w,cy-d],[cx,cy],[cx,cy-h],[cx-w,cy-h-d]],"#c9a36c"));
      g.appendChild(wielokat([[cx,cy],[cx+w,cy-d],[cx+w,cy-h-d],[cx,cy-h]],"#a97f4a"));
      g.appendChild(wielokat([[cx-w*0.15,cy-h-d*0.85],[cx+w*0.85,cy-h-d*1.35],[cx+w*0.85,cy-h-d*1.15],[cx-w*0.15,cy-h-d*0.65]],"#d9b57a"));
      // naklejka z kodem na przedniej scianie
      var nk = wielokat([[cx-w*0.8,cy-d*0.8-h*0.55],[cx-w*0.25,cy-d*0.25-h*0.55],[cx-w*0.25,cy-d*0.25-h*0.25],[cx-w*0.8,cy-d*0.8-h*0.25]],"#fff");
      g.appendChild(nk);
      for (var i=0;i<6;i++){ var kr = wielokat([[cx-w*0.75+i*w*0.07,cy-d*0.75+i*d*0.07-h*0.5],[cx-w*0.73+i*w*0.07,cy-d*0.73+i*d*0.07-h*0.5],[cx-w*0.73+i*w*0.07,cy-d*0.73+i*d*0.07-h*0.3],[cx-w*0.75+i*w*0.07,cy-d*0.75+i*d*0.07-h*0.3]],"#3b2a12"); g.appendChild(kr); }
      var txt = document.createElementNS(NS,"text");
      txt.setAttribute("x", cx+w*0.5); txt.setAttribute("y", cy-h*0.4-d*0.5+6); txt.setAttribute("text-anchor","middle");
      if (zero) txt.setAttribute("class","zero");
      txt.textContent = napis; g.appendChild(txt);
      svg.appendChild(g);
    }
    var regal = document.createElementNS(NS,"g"); regal.setAttribute("class","regal");
    regal.appendChild(wielokat([[120,470],[420,320],[700,460],[400,610]],"#e2d2b3"));
    regal.appendChild(wielokat([[120,470],[120,486],[400,626],[400,610]],"#cbb78f"));
    regal.appendChild(wielokat([[400,610],[400,626],[700,476],[700,460]],"#b9a377"));
    svg.appendChild(regal);
    karton(300,470,80,80,"14",false,40,.05);
    karton(380,430,80,80,"27",false,50,.15);
    karton(460,390,80,80,"3",false,60,.25);
    karton(540,470,80,80,"0 → 8",true,70,.35);
    karton(300,470,64,64,"",false,30,.0); // wypelniacz z tylu (bez napisu) - usuniety ponizej
    svg.removeChild(svg.lastChild);
    karton(380,330,64,64,"9",false,90,.45);
    karton(460,290,64,64,"41",false,110,.55);
    karton(540,390,64,64,"6",false,100,.5);
  });

  // ksiega realizacji: przewracanie kart
  document.querySelectorAll(".ksiega").forEach(function(ks){
    var karty = [].slice.call(ks.querySelectorAll(".karta")), kropy = [].slice.call(ks.querySelectorAll(".kropy button"));
    var i = 0, zajety = false, n = karty.length;
    function zaladujKarte(karta){
      karta.querySelectorAll("img[data-carousel-src]").forEach(function(img){
        var srcset=img.getAttribute("data-carousel-srcset"), sizes=img.getAttribute("data-carousel-sizes"), src=img.getAttribute("data-carousel-src");
        if(srcset)img.setAttribute("srcset",srcset);
        if(sizes)img.setAttribute("sizes",sizes);
        if(src)img.setAttribute("src",src);
        img.removeAttribute("data-carousel-src");
        img.removeAttribute("data-carousel-srcset");
        img.removeAttribute("data-carousel-sizes");
      });
    }
    function ustaw(){
      karty.forEach(function(k, j){
        var active=j===i;
        if(active)zaladujKarte(k);
        k.classList.toggle("aktywna", active); k.classList.toggle("pod-spodem", j === (i+1)%n);
        k.setAttribute("aria-hidden", active ? "false" : "true");
        k.setAttribute("aria-label", (j+1)+" z "+n);
        k.setAttribute("role","group");
        k.querySelectorAll("a,button,input,select,textarea").forEach(function(el){if(active)el.removeAttribute("tabindex");else el.setAttribute("tabindex","-1");});
      });
      kropy.forEach(function(d, j){ d.classList.toggle("tu", j === i); d.setAttribute("aria-current", j===i ? "true" : "false"); });
    }
    function idz(kier){
      if (zajety) return; zajety = true;
      var stara = karty[i], nowy = (i + kier + n) % n, nowa = karty[nowy];
      zaladujKarte(nowa);
      if (spokoj){ i = nowy; ustaw(); zajety = false; return; }
      if (kier > 0){
        nowa.classList.add("pod-spodem"); karty.forEach(function(k){ if (k!==stara && k!==nowa) k.classList.remove("pod-spodem"); });
        stara.classList.add("odchodzi");
        setTimeout(function(){ stara.classList.remove("odchodzi"); i = nowy; ustaw(); zajety = false; }, 900);
      } else {
        nowa.classList.add("wraca");
        setTimeout(function(){ nowa.classList.remove("wraca"); i = nowy; ustaw(); zajety = false; }, 900);
      }
    }
    ks.querySelector(".strzalka.prawa").addEventListener("click", function(){ idz(1); });
    ks.querySelector(".strzalka.lewa").addEventListener("click", function(){ idz(-1); });
    kropy.forEach(function(d, j){ d.addEventListener("click", function(){ if (j !== i) idz(j > i ? 1 : -1); }); });
    var x0 = null;
    ks.addEventListener("pointerdown", function(e){ x0 = e.clientX; });
    ks.addEventListener("pointerup", function(e){ if (x0 === null) return; var dx = e.clientX - x0; x0 = null; if (Math.abs(dx) > 40) idz(dx < 0 ? 1 : -1); });

    ks.addEventListener("keydown", function(e){ if (e.key === "ArrowRight"){e.preventDefault();idz(1);} if (e.key === "ArrowLeft"){e.preventDefault();idz(-1);} });
    ustaw();
  });

  // kod na dokumencie ksef
  document.querySelectorAll(".qr").forEach(function(qr){
    var z = 7; for (var i=0;i<81;i++){ z = (z*48271)%2147483647; var b=document.createElement("b"); if (z%3===0) b.className="p"; qr.appendChild(b);}
  });

  // dlugosci linii, ktore maja sie rysowac
  document.querySelectorAll(".schody .tor, .droga .trasa.jazda, .mapa .lin").forEach(function(l){
    if (l.getTotalLength) l.style.setProperty("--dl", (l.getTotalLength()+2).toFixed(0) + "px");
  });

  // wjazd tekstu
  var wj = document.querySelectorAll(".wjazd");
  if (spokoj || !("IntersectionObserver" in window)) { wj.forEach(function(e){e.classList.add("widac")}); }
  else {
    var ob = new IntersectionObserver(function(ws){ ws.forEach(function(w){ if(!w.isIntersecting) return; w.target.classList.add("widac"); ob.unobserve(w.target); }); },{rootMargin:"0px 0px -10% 0px"});
    wj.forEach(function(e){ob.observe(e)});
    setTimeout(function(){ wj.forEach(function(e){e.classList.add("widac")}); }, 1500);
  }

  // pierwsze źródło wejścia / UTM — tylko w sessionStorage, do kontekstu leada
  (function(){
    try{
      var p=new URLSearchParams(location.search), saved=JSON.parse(sessionStorage.getItem("leadSource")||"{}"), changed=false;
      ["utm_source","utm_medium","utm_campaign","utm_content","utm_term"].forEach(function(k){
        if(p.get(k)&&!saved[k]){saved[k]=p.get(k);changed=true;}
      });
      if(!saved.entry){saved.entry=location.pathname;changed=true;}
      if(!saved.referrer&&document.referrer){saved.referrer=document.referrer;changed=true;}
      if(p.get("zrodlo")){saved.zrodlo=p.get("zrodlo");changed=true;}
      if(changed)sessionStorage.setItem("leadSource",JSON.stringify(saved));
    }catch(e){}
  })();

  // filtrowanie bazy wiedzy
  document.querySelectorAll("[data-poradniki-filter]").forEach(function(input){
    var items=[].slice.call(document.querySelectorAll(".wpisy li"));
    var out=document.querySelector("[data-poradniki-count]"), tracked=false;
    function norm(v){return (v||"").toLocaleLowerCase("pl").normalize("NFD").replace(/[\u0300-\u036f]/g,"");}
    function filtruj(){var q=norm(input.value.trim()),visible=0;items.forEach(function(li){var ok=!q||norm(li.textContent).indexOf(q)>=0;li.hidden=!ok;if(ok)visible++;});if(out)out.textContent=q?("Pasujących pozycji: "+visible):("Wszystkich pozycji: "+items.length);}
    input.addEventListener("input",function(){filtruj();if(!tracked&&input.value.trim().length>=2){tracked=true;siteTrack("poradniki-szukaj");}});filtruj();
  });

  // kwalifikator pierwszego etapu — wskazuje punkt startowy, nie wycenę całego projektu
  document.querySelectorAll("[data-kwalifikator]").forEach(function(box){
    var problem=box.querySelector("[name=problem]"),stan=box.querySelector("[name=stan]"),wynik=box.querySelector("[data-wynik]");
    var map={
      excel:["Pierwszy moduł aplikacji","od 2 900 zł","Proponuję zacząć od jednego zadania i wspólnej bazy, np. listy aktywnych zleceń ze statusami.","System zamiast Excela"],
      przepisywanie:["Integracja systemów","od 2 900 zł","Sprawdzę możliwości połączenia obu programów i ustalimy, który z nich przechowuje dane nadrzędne.","Integracja kilku programów / API"],
      sprzedaz:["Pierwszy moduł CRM","od 2 900 zł","Pierwsza wersja może obejmować klientów, zapytania i wybrany etap sprzedaży.","CRM lub obsługa sprzedaży"],
      wyceny:["Pierwszy moduł wycen i ofert","od 2 900 zł","Na początek ustalimy jeden sposób kalkulacji, zasady marży i szablon oferty PDF.","System do wycen i ofert"],
      zlecenia:["Pierwszy moduł obsługi zleceń","od 2 900 zł","Lista spraw, karta zlecenia i statusy zwykle wystarczą na pierwszy etap.","System do obsługi zleceń"],
      rezerwacje:["Pierwszy moduł rezerwacji","od 2 900 zł","Najpierw trzeba opisać zasoby i reguły, które decydują o dostępności.","System rezerwacji"],
      dokumenty:["Automatyzacja dokumentu","od 2 900 zł","Przygotuj wzór dokumentu i przykład danych, z których ma powstawać. Usuń informacje klientów.","Automatyzacja dokumentów"],
      klient:["Panel klienta / B2B","od 2 900 zł","Najpierw wybieramy jedną informację lub czynność, którą klient ma obsłużyć sam.","Panel klienta B2B"],
      ai:["Wstępny plan zastosowania AI","0 zł na start","Ustalimy, które czynności wymagają interpretacji tekstu lub dokumentów, a które można opisać regułami.","Automatyzacja z AI"]
    };
    function render(track){var m=map[problem.value];if(!m){wynik.hidden=true;return;}if(track)siteTrack("kwalifikator-wynik",{problem:problem.value,stan:stan.value});var dopisek=stan.value==="niejasny"?" Jeśli sposób pracy wymaga doprecyzowania, zaczniemy od bezpłatnego wstępnego planu.":"";var href="opisz-projekt.html?typ="+encodeURIComponent(m[3])+"&zrodlo=kwalifikator";wynik.innerHTML='<h3>'+m[0]+'</h3><p><strong>Cena pierwszego etapu: '+m[1]+'</strong></p><p>'+m[2]+dopisek+'</p><p class="slaby">To propozycja pierwszego etapu na podstawie cennika, nie wycena całego projektu. Zakres i cenę potwierdzamy po rozmowie.</p><a class="przycisk" data-umami-event="kwalifikator-opisz-projekt" href="'+href+'">Opisz ten projekt</a>';wynik.hidden=false;}
    problem.addEventListener("change",function(){render(true)});stan.addEventListener("change",function(){render(true)});render(false);
  });

  // dostępne menu mobilne
  (function(){
    var btn=document.querySelector(".menu-toggle"), nav=document.getElementById("nav-main"); if(!btn||!nav)return;
    function close(){document.body.classList.remove("menu-open");btn.setAttribute("aria-expanded","false");btn.setAttribute("aria-label","Otwórz menu");}
    btn.addEventListener("click",function(){var open=!document.body.classList.contains("menu-open");document.body.classList.toggle("menu-open",open);btn.setAttribute("aria-expanded",open?"true":"false");btn.setAttribute("aria-label",open?"Zamknij menu":"Otwórz menu");});
    nav.addEventListener("click",function(e){if(e.target.closest("a"))close();});
    document.addEventListener("keydown",function(e){if(e.key==="Escape"&&document.body.classList.contains("menu-open")){close();btn.focus();}});
    addEventListener("resize",function(){if(innerWidth>900)close();});
    document.addEventListener("click",function(e){if(document.body.classList.contains("menu-open")&&!nav.contains(e.target)&&!btn.contains(e.target))close();});
  })();

  // oglądanie case studies — tylko identyfikator sekcji, bez danych użytkownika
  (function(){
    if(!("IntersectionObserver" in window))return;
    var seen={};
    var obs=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting&&!seen[e.target.id]){seen[e.target.id]=true;siteTrack("case-study-view",{case:e.target.id});obs.unobserve(e.target);}});},{threshold:.05,rootMargin:"0px 0px -20% 0px"});
    ["photonroof","wypozyczalnia"].forEach(function(id){var el=document.getElementById(id);if(el)obs.observe(el);});
  })();

  // aktywna pozycja głównej nawigacji
  (function(){
    var current = location.pathname.split("/").pop() || "index.html";
    var group = document.body.getAttribute("data-nav-active") || "";
    document.querySelectorAll(".gora nav a[href]").forEach(function(a){
      var raw = a.getAttribute("href");
      if (!raw || raw.indexOf(":") >= 0 || raw.charAt(0) === "#") return;
      var target = raw.split("#")[0].split("?")[0] || "index.html";
      if (target === current || target === group) a.setAttribute("aria-current","page");
      else a.removeAttribute("aria-current");
    });
  })();

  // ciemny naglowek nad ciemnymi rozdzialami
  var ciemne = [].slice.call(document.querySelectorAll("[data-ciemna]"));
  function naglowek(){
    var y = 30, c = false;
    ciemne.forEach(function(s){ var r = s.getBoundingClientRect(); if (r.top <= y && r.bottom >= y) c = true; });
    document.body.classList.toggle("ciemna", c);
  }

  // ruch: kazdy rozdzial dostaje --t (polozenie wzgledem srodka ekranu) i --w (ile wjechal). Reszte robi CSS.
  var rozdzialy = [].slice.call(document.querySelectorAll(".rozdzial")).map(function(s){ return {el:s, t:0, w:0, ct:0, cw:0}; });
  function gladko(x){ return x*x*(3-2*x); }
  function zmierz(){
    var H = innerHeight, waski = innerWidth < 821;
    rozdzialy.forEach(function(r){
      var b = r.el.getBoundingClientRect();
      if (b.bottom < -H || b.top > 2*H) return;
      var t = (b.top + b.height/2 - H/2) / H;
      r.ct = waski ? 0 : Math.max(-1.5, Math.min(1.5, t));
      var w = (H - b.top) / (H * 0.85);
      if (r.el.classList.contains("czolo")) w = (performance.now() - start) / 1400;   // czolo sklada sie samo po wejsciu
      r.cw = gladko(Math.max(0, Math.min(1, w)));
    });
  }
  var start = performance.now(), ruch = false;
  function krok(){
    var zostalo = false;
    zmierz();
    rozdzialy.forEach(function(r){
      if (spokoj) { r.t = 0; r.w = 1; }
      else { r.t += (r.ct - r.t) * 0.16; r.w += (r.cw - r.w) * 0.16; }
      if (Math.abs(r.ct - r.t) > 0.0005 || Math.abs(r.cw - r.w) > 0.0005) zostalo = true;
      r.el.style.setProperty("--t", r.t.toFixed(4));
      r.el.style.setProperty("--w", r.w.toFixed(4));
    });
    naglowek();
    if (zostalo || performance.now() - start < 1600) requestAnimationFrame(krok); else ruch = false;
  }
  function zaplanuj(){ if (!ruch){ ruch = true; requestAnimationFrame(krok); } }
  addEventListener("scroll", zaplanuj, {passive:true});
  addEventListener("resize", zaplanuj);
  zaplanuj();

  // page-specific: kalkulator kosztu ręcznej pracy
  (function(){
    var box=document.querySelector("[data-roi-calc]"); if(!box)return;
    var tracked=false;
    var fmt0=new Intl.NumberFormat("pl-PL",{maximumFractionDigits:0});
    var fmt1=new Intl.NumberFormat("pl-PL",{maximumFractionDigits:1});
    var money=new Intl.NumberFormat("pl-PL",{style:"currency",currency:"PLN",maximumFractionDigits:0});
    function val(n){var x=parseFloat(box.querySelector("[name="+n+"]").value);return Number.isFinite(x)&&x>=0?x:0;}
    function render(){
      var minutes=val("minuty"),times=val("razy"),people=val("osoby"),days=val("dni"),rate=val("stawka");
      var ops=times*people*days,hours=ops*minutes/60,cost=hours*rate;
      box.querySelector("[data-r=operacje]").textContent=fmt0.format(ops);
      box.querySelector("[data-r=godziny]").textContent=fmt1.format(hours)+" h";
      box.querySelector("[data-r=koszt]").textContent=money.format(cost);
      box.querySelector("[data-r=rok-h]").textContent=fmt0.format(hours*12)+" h";
      box.querySelector("[data-r=rok-koszt]").textContent=money.format(cost*12);
    }
    box.addEventListener("input",function(){
      render();
      if(!tracked){tracked=true;siteTrack("kalkulator-kosztu-pracy-uzyty");}
    });
    render();
  })();

  // page-specific: formularz briefu
  (function(){
    var form=document.getElementById("brief-form"); if(!form)return;
    var copy=document.getElementById("kopiuj-brief"),
        download=document.getElementById("pobierz-brief"),
        clear=document.getElementById("wyczysc-brief"),
        info=document.getElementById("brief-info"),
        fallback=document.getElementById("brief-fallback");
    function value(fd,n){return (fd.get(n)||"").toString().trim();}
    var briefStarted=false,saveTimer;

    function saveDraft(){
      try{
        var obj={};
        new FormData(form).forEach(function(v,k){obj[k]=v;});
        sessionStorage.setItem("briefDraft",JSON.stringify(obj));
      }catch(e){}
    }

    try{
      var draft=JSON.parse(sessionStorage.getItem("briefDraft")||"{}");
      Object.keys(draft).forEach(function(k){
        var el=form.elements[k];
        if(el&&draft[k]!=null)el.value=draft[k];
      });
    }catch(e){}

    form.addEventListener("input",function(){
      if(!briefStarted){briefStarted=true;siteTrack("brief-start");}
      clearTimeout(saveTimer);
      saveTimer=setTimeout(saveDraft,180);
    },{passive:true});
    form.addEventListener("change",saveDraft,{passive:true});

    var params=new URLSearchParams(location.search);
    var typParam=params.get("typ");
    if(typParam){
      var select=form.querySelector("[name=typ]");
      var match=[].slice.call(select.options).find(function(o){return o.text===typParam;});
      if(match)select.value=match.value;
    }

    function showFallback(message){
      fallback.value=message;
      fallback.hidden=false;
      fallback.focus();
      fallback.select();
      info.textContent="Nie udało się skopiować tekstu automatycznie. Skopiuj zaznaczony opis poniżej i wyślij go na kontakt@maciejgryziec.pl.";
    }

    function brief(){
      var fd=new FormData(form),ref=document.referrer||location.href,source="";
      try{
        var saved=JSON.parse(sessionStorage.getItem("leadSource")||"{}");
        source=Object.keys(saved).map(function(k){return k+"="+saved[k];}).join(" | ");
      }catch(e){}
      return [
        "Dzień dobry","","chcę porozmawiać o projekcie dla firmy.","",
        "Imię i nazwisko: "+value(fd,"imie"),
        "Firma: "+(value(fd,"firma")||"nie podano"),
        "E-mail: "+value(fd,"email"),
        "Telefon: "+(value(fd,"telefon")||"nie podano"),
        "Typ projektu: "+value(fd,"typ"),"",
        "Obecny sposób pracy:",value(fd,"dzis"),"",
        "Największy problem:",value(fd,"problem"),"",
        "Obecne narzędzia: "+(value(fd,"narzedzia")||"nie podano"),
        "Liczba użytkowników: "+value(fd,"uzytkownicy"),
        "Orientacyjny budżet: "+(value(fd,"budzet")||"nie podano"),"",
        "Oczekiwany efekt pierwszego etapu:",value(fd,"efekt")||"nie podano","",
        "Strona, z której trafiłem do formularza: "+ref,
        "Źródło / kampania: "+(source||"nie podano")
      ].join("\n");
    }

    form.addEventListener("submit",async function(e){
      e.preventDefault();
      if(!form.reportValidity())return;
      var fd=new FormData(form);
      var subject="Zapytanie o projekt: "+(fd.get("typ")||"aplikacja dla firmy");
      var message=brief();
      var copied=false;
      try{await navigator.clipboard.writeText(message);copied=true;}catch(err){}
      var mailBody=message;
      if(message.length>3500&&copied){
        mailBody="Dzień dobry,\n\nprzygotowałem opis projektu w formularzu na stronie. Wklejam go poniżej.\n\nPozdrawiam";
        info.textContent="Opis projektu został skopiowany. Po otwarciu wiadomości wklej go pod przygotowanym tekstem.";
      }else if(message.length>3500&&!copied){
        showFallback(message);return;
      }else{
        info.textContent=copied?"Treść została również skopiowana do schowka.":"Otwieram program pocztowy z przygotowaną wiadomością.";
      }
      siteTrack("brief-mailto-ready",{typ:value(fd,"typ")});
      location.href="mailto:kontakt@maciejgryziec.pl?subject="+encodeURIComponent(subject)+"&body="+encodeURIComponent(mailBody);
    });

    if(copy)copy.addEventListener("click",async function(){
      if(!form.reportValidity())return;
      var message=brief();
      try{
        await navigator.clipboard.writeText(message);
        fallback.hidden=true;
        info.textContent="Opis skopiowany. Wklej go do wiadomości na kontakt@maciejgryziec.pl.";
      }catch(e){showFallback(message);}
    });

    if(download)download.addEventListener("click",function(){
      if(!form.reportValidity())return;
      var blob=new Blob([brief()],{type:"text/plain;charset=utf-8"}),
          url=URL.createObjectURL(blob),
          a=document.createElement("a");
      a.href=url;
      a.download="brief-projektu.txt";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function(){URL.revokeObjectURL(url);},1000);
      info.textContent="Opis zapisany w pliku TXT.";
    });

    if(clear)clear.addEventListener("click",function(){
      if(!confirm("Usunąć szkic zapisany w tej karcie?"))return;
      form.reset();
      fallback.hidden=true;
      sessionStorage.removeItem("briefDraft");
      info.textContent="Szkic został usunięty. Możesz przygotować nowy opis.";
      form.querySelector("[name=imie]").focus();
    });
  })();

  // page-specific: użytkownik może wyłączyć lub ponownie włączyć self-hosted Umami.
  (function(){
    var status=document.getElementById("umami-status"); if(!status)return;
    var off=document.getElementById("umami-off"),on=document.getElementById("umami-on");
    function disabled(){return analyticsDisabled();}
    function render(){
      var d=disabled();
      status.textContent=d?"Statystyki na tym urządzeniu są wyłączone.":"Statystyki na tym urządzeniu są włączone.";
      if(off){off.disabled=d;off.setAttribute("aria-disabled",d?"true":"false");}
      if(on){on.disabled=!d;on.setAttribute("aria-disabled",!d?"true":"false");}
    }
    if(off)off.addEventListener("click",function(){try{localStorage.setItem("umami.disabled","1");}catch(e){}location.reload();});
    if(on)on.addEventListener("click",function(){try{localStorage.removeItem("umami.disabled");}catch(e){}location.reload();});
    render();
  })();

  // druk / zapis cennika jako PDF
  document.querySelectorAll("[data-print-cennik]").forEach(function(btn){
    btn.addEventListener("click",function(){window.print();});
  });
})();
"""

# ---------------------------------------------------------------- ilustracje
LOGO = '<svg viewBox="918 401 897 733" aria-hidden="true"><g stroke="#fff" stroke-width="46" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M999 482 L1124 466 L1199 621"/><path d="M1199 621 L1734 621"/><path d="M1199 621 L1284 897"/><path d="M1734 621 L1648 897"/><path d="M1284 897 L1648 897"/><path d="M1284 897 L1333 1053"/><path d="M1333 1053 L1600 1053"/></g><g fill="#fff"><circle cx="999" cy="482" r="72"/><circle cx="1199" cy="621" r="72"/><circle cx="1734" cy="621" r="72"/><circle cx="1284" cy="897" r="72"/><circle cx="1648" cy="897" r="72"/><circle cx="1333" cy="1053" r="72"/><circle cx="1600" cy="1053" r="72"/></g></svg>'

def mapa():
    # logo jako mapa polaczen: wezly = miejsca, do ktorych trafia zamowienie
    wezly = [(999,482,"klient","0"),(1199,621,"sklep","0.15"),(1734,621,"Allegro","0.3"),(1284,897,"magazyn","0.45"),(1648,897,"faktury","0.55"),(1333,1053,"księgowa","0.7"),(1600,1053,"KSeF","0.8")]
    s = '<svg class="mapa" viewBox="700 340 1300 900" aria-hidden="true">'
    s += '<path class="lin" d="M999 482 L1124 466 L1199 621 L1734 621 L1648 897 L1284 897 L1199 621 M1284 897 L1333 1053 L1600 1053"/>'
    for x,y,n,o in wezly:
        s += f'<circle class="wezel" cx="{x}" cy="{y}" r="44" style="--o:{o}"/>'
    # podpisy: gdzie sie miesci
    poz = {"klient":(940,430,"end"),"sklep":(1150,690,"end"),"Allegro":(1790,610,"start"),"magazyn":(1230,960,"end"),"faktury":(1700,960,"start"),"księgowa":(1280,1120,"end"),"KSeF":(1660,1120,"start")}
    for x,y,n,o in wezly:
        px,py,anch = poz[n]
        s += f'<text class="pod" x="{px}" y="{py}" text-anchor="{anch}" style="--o:{o}">{n}</text>'
    s += '</svg>'
    return s

def laptop():
    # ekran laptopa: kafelki polaczone krzywymi, po ktorych plyna paczki danych; naglowek jak w panelu straznika
    W = {"sklep":(400,268),"Allegro":(150,134),"magazyn":(150,402),"faktury":(650,134),"KSeF":(650,402),"klient":(400,68),"ksiegowa":(400,466)}
    NAZWY = {"sklep":"Twój sklep","Allegro":"Allegro","magazyn":"magazyn","faktury":"faktury","KSeF":"KSeF","klient":"klient","ksiegowa":"księgowa"}
    IKONY = {"sklep":"M-9 -2 h18 l-2 8 h-14 z M-6 6 v3 h12 v-3", "Allegro":"M-8 -6 h16 v12 h-16 z M-8 -1 h16", "magazyn":"M-8 -4 l8 -4 l8 4 v10 h-16 z M-8 -4 l8 4 l8 -4 M0 0 v10",
             "faktury":"M-6 -8 h9 l4 4 v12 h-13 z M-3 0 h7 M-3 4 h7", "KSeF":"M0 -8 l8 3 v6 c0 5 -4 8 -8 9 c-4 -1 -8 -4 -8 -9 v-6 z M-3 1 l2 2 l4 -5", "klient":"M0 -6 m-3 0 a3 3 0 1 0 6 0 a3 3 0 1 0 -6 0 M-7 8 c0 -5 14 -5 14 0", "ksiegowa":"M-8 -3 h16 M-6 -3 v9 M0 -3 v9 M6 -3 v9 M-9 6 h18 M0 -7 l8 4 h-16 z"}
    lin = [("sklep","Allegro"),("sklep","magazyn"),("sklep","faktury"),("faktury","KSeF"),("faktury","ksiegowa"),("sklep","klient"),("magazyn","ksiegowa"),("Allegro","magazyn")]
    s = '<svg class="mosty" viewBox="0 0 800 500" preserveAspectRatio="none" aria-hidden="true">'
    for gx in range(0,801,40): s += f'<line class="tlo" x1="{gx}" y1="0" x2="{gx}" y2="500"/>'
    for gy in range(0,501,40): s += f'<line class="tlo" x1="0" y1="{gy}" x2="800" y2="{gy}"/>'
    for i,(a,b) in enumerate(lin):
        (x1,y1),(x2,y2) = W[a],W[b]
        mx,my = (x1+x2)/2,(y1+y2)/2; dx,dy = x2-x1,y2-y1
        cx,cy = mx - dy*0.18, my + dx*0.18       # lekki luk
        d = f"M{x1} {y1} Q{cx:.0f} {cy:.0f} {x2} {y2}"
        s += f'<path class="lin pos" d="{d}"/><path class="lin" d="{d}"/>'
        s += f'<circle class="pakiet" r="4.5" style="offset-path:path(\'{d}\');animation-delay:{i*0.45:.2f}s"/>'
    for n,(x,y) in W.items():
        g = n=="sklep"; w,h = (210,60) if g else (128,46)
        s += f'<rect class="kafel{" glowny" if g else ""}" x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="9"/>'
        s += f'<path class="ikona" transform="translate({x-w/2+22} {y})" d="{IKONY[n]}"/>'
        s += f'<circle class="lampka{" a" if n in ("faktury","magazyn") else ""}" cx="{x+w/2-12}" cy="{y-h/2+12}" r="3.5"/>'
    # belka u gory ekranu
    s += '<rect class="belka" x="0" y="0" width="800" height="34"/><line class="belka-lin" x1="0" y1="34" x2="800" y2="34"/><circle cx="18" cy="17" r="4" fill="#ff5f57"/><circle cx="32" cy="17" r="4" fill="#febc2e"/><circle cx="46" cy="17" r="4" fill="#28c840"/>'
    s += '</svg><div class="podpisy"><span class="naglowek-e" style="left:8.5%;top:3.4%">Strażnik połączeń · dziś 06:00</span><span class="status" style="left:97%;top:3.4%">● 12 mostów działa</span>'
    for n,(x,y) in W.items():
        g = n=="sklep"; w = 210 if g else 128
        lx = (x - w/2 + 44 + (w-44)/2)/8
        if g: s += f'<span style="left:{lx:.1f}%;top:{(y-8)/5:.1f}%">Twój sklep</span><span class="m" style="left:{lx:.1f}%;top:{(y+12)/5:.1f}%">Shoper · 312 produktów</span>'
        else: s += f'<span style="left:{lx:.1f}%;top:{y/5:.1f}%">{NAZWY[n]}</span>'
    s += '</div>'
    dymki = [("zolty","FV/09/141 wystawiona","12:04:14 · wFirma","left:4%;top:-9%","0s"),("","Allegro → magazyn: stan zgodny","12:04:12","right:0;top:62%","3s"),("","Faktura przyjęta w KSeF","UPO 12:04:15","left:12%;top:72%","6s"),("zolty","12 mostów sprawdzonych","06:00 · wszystkie działają","right:2%;top:-9%","9s")]
    d = ''.join(f'<div class="dymek {k}" style="{st};--d:{dl}">{t}<small>{m}</small></div>' for k,t,m,st,dl in dymki)
    kropki = ''.join(f'<i style="left:{x}%;top:{y}%;width:{w}px;height:{w}px"></i>' for x,y,w in [(4,20,10),(96,30,14),(8,86,8),(60,96,10),(92,88,8),(30,4,6)])
    return f'<div class="kropki">{kropki}</div><div class="laptop"><div class="ekran">{s}</div><div class="podstawa"></div></div>{d}'

def schody(nazwy=("sklep","magazyn","faktura","księgowość","e-mail"), czasy=("12:04:11","12:04:12","12:04:14","12:04:15","12:04:16")):
    # piec plyt wznoszacych sie w prawo; kazda ma sciane przednia, wierzch i bok. Zlota linia wchodzi po nich jak po schodach.
    kol = [("#8b9bff","#b9c3ff","#4a57c9"),("#6f7ff0","#a3aefc","#3b47b3"),("#5461d6","#8b97f2","#2e3894"),("#3f4bb8","#7380e8","#232b78"),("#2f377f","#5a63c7","#1a2058")]
    s = '<svg class="schody" viewBox="0 0 1000 560" aria-hidden="true"><defs><linearGradient id="zloty" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#f6c94a"/><stop offset="1" stop-color="#f08a3c"/></linearGradient></defs>'
    for i in range(5):
        x0 = 150 + i*118; yb = 520 - i*84; w = 330; sk = 0.25; h = 54; g = 16
        (c1,c2,c3) = kol[i]
        s += f'<g class="stopien" style="--s:{8+i*5}px;--dx:{-220+i*30}px;--dy:{70-i*8}px;--o:{i*0.3:.1f}">'
        # przednia sciana
        s += f'<polygon points="{x0},{yb} {x0+w},{yb-w*sk} {x0+w},{yb-w*sk-h} {x0},{yb-h}" fill="{c1}"/>'
        # wierzch (jasniejszy)
        s += f'<polygon points="{x0},{yb-h} {x0+w},{yb-w*sk-h} {x0+w+g},{yb-w*sk-h-g*0.45} {x0+g},{yb-h-g*0.45}" fill="{c2}"/>'
        # bok prawy (ciemniejszy)
        s += f'<polygon points="{x0+w},{yb-w*sk} {x0+w+g},{yb-w*sk-g*0.45} {x0+w+g},{yb-w*sk-h-g*0.45} {x0+w},{yb-w*sk-h}" fill="{c3}"/>'
        tx, ty = x0+40, yb-32
        s += f'<g transform="rotate(-14.04 {tx} {ty})"><text x="{tx}" y="{ty}" style="font-size:17px">{nazwy[i]}</text><text class="czas" x="{tx}" y="{ty+15}">{czasy[i]}</text></g></g>'
    # linia: pionowo w gore, potem po wierzchu kazdej plyty
    d = "M60 545 V500 q0 -16 16 -16 H150 q16 0 16 -16 V420 q0 -16 16 -16 H268 q16 0 16 -16 V336 q0 -16 16 -16 H386 q16 0 16 -16 V252 q0 -16 16 -16 H504 q16 0 16 -16 V168 q0 -16 16 -16 H622 q16 0 16 -16 V60"
    s += f'<g style="--s:6px"><path class="tor" d="{d}"/><path class="grot" d="M622 80 L638 58 L654 80" fill="none" stroke="#f08a3c" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></g></svg>'
    return s

def schody_firma():
    return schody(
        ("zapytanie","CRM","realizacja","dokument","klient"),
        ("nowe","kwalifikacja","w toku","gotowy","powiadomiony")
    )

POZYCJE = [("Kurtka przeciwdeszczowa Nordal, r. M","1","329,00","329,00"),("Sweter wełniany Bergen, r. L","1","249,00","249,00"),("Koszula lniana Lund, biała","2","139,00","278,00"),("Skarpety merino, 3 pary","1","69,00","69,00")]
def tabela_pozycji(z_o=False):
    t = '<table><tr><th>Nazwa</th><th class="l">Ilość</th><th class="l">Cena</th><th class="l">Wartość</th></tr>'
    for j,(n,i,c,w) in enumerate(POZYCJE):
        t += f'<tr style="--o:{.2+j*.06:.2f}"><td>{n}</td><td class="l">{i}</td><td class="l">{c}</td><td class="l">{w}</td></tr>'
    return t + '</table>'
SUMY = '<div class="sumy"><div style="--o:.45"><span>Razem netto</span><span>752,03</span></div><div style="--o:.5"><span>VAT 23%</span><span>172,97</span></div><div class="r" style="--o:.55"><span>Do zapłaty</span><span>925,00 zł</span></div></div>'
STRONY = '<div class="strony" style="--o:.15"><div><b>Sprzedawca</b><span>Odzież Północ sp. z o.o.</span><span>ul. Długa 12, 80-827 Gdańsk</span><span>NIP 583-000-00-00</span></div><div><b>Nabywca</b><span>Anna Kowalska</span><span>ul. Polna 4/7, 60-001 Poznań</span><span>zamówienie #4821</span></div></div>'

def stos():
    return ('<div class="stos">'
      f'<div class="kartka dok" style="--i:0"><div class="naglowek">Zamówienie #4821 <small>sklep · 12:04:11</small></div><div class="strony"><div><b>Klient</b><span>Anna Kowalska</span><span>customer@example.com</span></div><div><b>Dostawa</b><span>Kurier InPost, 14,99 zł</span><span>płatność: BLIK, opłacone</span></div></div>{tabela_pozycji()}<div class="sumy"><div><span>Produkty</span><span>925,00</span></div><div><span>Dostawa</span><span>14,99</span></div><div class="r"><span>Razem</span><span>939,99 zł</span></div></div></div>'
      f'<div class="kartka dok" style="--i:1"><div class="naglowek">Faktura FV/09/141 <small>wFirma · 12:04:14</small></div>{STRONY}{tabela_pozycji()}{SUMY}<div class="dol-dok">Data sprzedaży 07.09.2026 · termin płatności: zapłacono · wystawił: system</div></div>'
      '<div class="kartka dok" style="--i:2"><div class="naglowek">KSeF <small>Krajowy System e-Faktur · 12:04:15</small></div><div class="strony"><div><b>Numer KSeF</b><span>5830000000-20260907-A1F2C3-4D</span></div><div><b>Status</b><span class="status">przyjęta</span></div></div><div class="strony"><div><b>Dokument</b><span>FV/09/141, 925,00 zł brutto</span></div><div><b>Data przyjęcia</b><span>07.09.2026 12:04:15</span></div></div><div class="dol-dok">Urzędowe Poświadczenie Odbioru zapisane przy fakturze w wFirmie.</div><div class="piecz">UPO · przyjęto</div></div>'
      '<div class="kartka dok" style="--i:3"><div class="naglowek">E-mail do klienta <small>12:04:16</small></div><div class="strony"><div><b>Do</b><span>customer@example.com</span></div><div><b>Temat</b><span>Zamówienie #4821 przyjęte, faktura w załączniku</span></div></div><div class="mail"><p>Dzień dobry,</p><p>dziękujemy za zamówienie. Paczka wyjdzie dziś kurierem InPost, numer przesyłki wyślemy osobno.</p><p>Pozdrawiamy, Odzież Północ</p><span class="zal">📎 FV-09-141.pdf</span></div></div>'
      '</div>')
    poz = '<div class="poz"><span>Filtr do wody Aqua 3</span><span>249,00</span></div><div class="poz"><span>Wkład węglowy, 2 szt.</span><span>118,00</span></div><div class="poz"><span>Głowica z zaworem</span><span>882,00</span></div>'
    return ('<div class="stos">'
      f'<div class="kartka" style="--i:0"><div class="naglowek">Zamówienie #4821 <small>12:04:11</small></div><div class="poz n"><span>Jan Kowalski, Poznań</span><span>przelew</span></div>{poz}<div class="suma">1 249,00 zł</div></div>'
      f'<div class="kartka" style="--i:1"><div class="naglowek">Faktura FV/09/141 <small>12:04:14</small></div><div class="poz n"><span>NIP 779-000-00-00</span><span>VAT 23%</span></div>{poz}<div class="suma">1 249,00 zł</div></div>'
      f'<div class="kartka" style="--i:2"><div class="naglowek">KSeF <small>12:04:15</small></div><div class="poz n"><span>numer KSeF</span><span>7790000000-20260907-…</span></div><div class="poz"><span>FV/09/141</span><span>przyjęta</span></div><div class="piecz">UPO · przyjęto</div></div>'
      '<div class="kartka" style="--i:3"><div class="naglowek">E-mail do klienta <small>12:04:16</small></div><div class="poz n"><span>do: jan@…</span><span>z fakturą PDF</span></div><div class="mail">Dziękujemy za zamówienie #4821. Faktura w załączniku, paczka wyjdzie dziś.</div></div>'
      '</div>')

def kartony():
    return '<svg class="kartony" viewBox="0 0 760 560" aria-hidden="true"></svg>'

def dokument():
    return ('<div class="kolejka"><div class="dokument tlo2"></div><div class="dokument tlo"></div>'
      f'<div class="dokument dok"><div class="naglowek">FV/09/141 <small>faktura VAT · KSeF</small></div>{STRONY}{tabela_pozycji()}{SUMY}'
      '<div class="upo">UPO<small>przyjęto 12:04:15</small></div><div class="qr"></div></div></div>')

def noc():
    # miasto z oknami, ktore zapalaja sie po kolei; gory w tle
    okna = ''
    bud = [(80,300,70,120),(170,260,60,160),(250,320,90,100),(360,240,70,180),(450,290,80,130),(550,270,60,150),(630,310,100,110),(750,250,70,170),(840,300,80,120),(940,280,60,140),(1020,320,90,100),(1130,260,70,160),(1220,300,80,120),(1320,280,90,140)]
    r=''; k=0
    for x,y,w,h in bud:
        r += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#0a1d45"/>'
        for oy in range(y+14, y+h-10, 22):
            for ox in range(x+10, x+w-10, 20):
                k += 1
                if (k*7) % 3 == 0:
                    okno = f'<rect class="okno" x="{ox}" y="{oy}" width="8" height="10" style="--o:{(k%17)/17*0.5:.2f}"/>'
                    if (k*5) % 4 == 0: okno = f'<g class="mig" style="--dt:{6+(k%9)}s;--dl:-{(k*3)%11}s">{okno}</g>'
                    okna += okno
    return ('<div class="gwiazdy a"></div><div class="gwiazdy b"></div><div class="ksiezyc"></div>'
      '<svg class="gory" viewBox="0 0 1440 420" preserveAspectRatio="none" aria-hidden="true">'
      '<polygon data-s style="--s:40px" points="0,300 180,180 320,250 520,120 700,230 900,140 1100,240 1250,170 1440,260 1440,420 0,420" fill="#2a5fb8"/>'
      '<polygon data-s style="--s:20px" points="0,360 220,270 400,330 600,240 800,320 1000,250 1200,330 1440,280 1440,420 0,420" fill="#1c4b9c"/></svg>'
      f'<svg class="miasto" viewBox="0 0 1440 420" preserveAspectRatio="none" aria-hidden="true"><g data-s style="--s:10px">{r}{okna}</g><rect x="0" y="418" width="1440" height="2" fill="#081538"/></svg>')

def droga():
    kroki = [(90,430,"01","Wstępny plan","problem → pierwszy krok","0 zł · 1-2 dni",".05"),
             (300,330,"02","Pierwszy moduł","działający etap aplikacji","od 2 900 zł",".25"),
             (510,230,"03","System na zamówienie","kolejne moduły i integracje","wycena etapami",".45"),
             (700,120,"04","Opieka miesięczna","monitoring i rozwój","od 349 zł / mies.",".65")]
    s = '<svg class="droga" viewBox="0 0 920 520" aria-hidden="true">'
    d = "M40 470 C120 470 60 330 300 330 C520 330 420 230 510 230 C640 230 600 120 700 120 L760 120"
    s += f'<path class="trasa" d="{d}"/><path class="trasa jazda" d="{d}"/>'
    for x,y,nr,naz,op,cn,o in kroki:
        s += f'<g class="przystanek" style="--o:{o};--s:{30+int(o[1:])*0.5:.0f}px"><circle cx="{x}" cy="{y}" r="16"/><text class="nr" x="{x}" y="{y+5}" text-anchor="middle">{nr}</text>'
        s += f'<text class="naz" x="{x+28}" y="{y-4}">{naz}</text><text class="op" x="{x+28}" y="{y+13}">{op}</text><text class="cn" x="{x+28}" y="{y+30}">{cn}</text></g>'
    return s + '</svg>'

def raport():
    w = [("b","98 adresów z mapy strony nie działa"),("b","12 promocji bez najniższej ceny z 30 dni"),("u","41 produktów bez numeru EAN"),("u","brak danych producenta wymaganych przez GPSR"),("o","certyfikat ważny jeszcze 214 dni"),("o","cena w Ceneo zgodna ze sklepem")]
    return ('<div class="raport"><div class="adres"><span>sprawdzarka · mojsklep.pl</span><i>312 podstron</i></div><ul>'
      + ''.join(f'<li style="--o:{j*.07:.2f}"><span class="{k}">{ {"b":"BŁĄD","u":"UWAGA","o":"OK"}[k] }</span> {t}</li>' for j,(k,t) in enumerate(w)) + '</ul></div>')

def paragon():
    poz = [("01 Wstępny plan","0 zł"),("   problem → pierwszy krok → budżet",None),("02 Pierwszy moduł","od 2 900 zł"),("   działający etap aplikacji",None),("02+ Integracja systemów","od 2 900 zł"),("   CRM / sklep / kalendarz → dokumenty",None),("03 System na zamówienie","wycena"),("   kolejne moduły etapami",None),("04 Opieka miesięczna",""),("   podstawowa","349 zł"),("   rozszerzona","599 zł"),("   pełna","899 zł")]
    w = ''
    for a,b in poz:
        if a.startswith("   "): w += f'<div class="poz sz"><span>{a.strip()}</span><span>{b or ""}</span></div>'
        else: w += f'<div class="poz"><b>{a}</b><span>{b}</span></div>'
    return ('<div class="kasa"><div class="drukarka"><i></i></div><div class="paragon"><div class="wys">'
      '<div class="naglowek">AUTOMATYZACJE DLA FIRM</div><div class="drobne">Maciej Gryziec · aplikacje i systemy na zamówienie</div><div class="drobne">' + "zakres i cena ustalone przed startem" + '</div><hr>'
      + w + '<hr><div class="razem"><span>RAZEM</span><span>zgodnie z zaakceptowaną wyceną</span></div><div class="poz sz"><span>cena uzgodnionego zakresu jest stała</span></div><div class="poz sz"><span>Dodatkowy zakres wyceniam osobno.</span></div><hr>'
      '<div class="drobne">Płatna praca zaczyna się po akceptacji zakresu.</div><div class="kod"></div><p>5 902 2026 0907 4</p></div></div></div>')

def ksiega():
    spr = ('<div class="spr"><div class="gora-p">sprawdzarka · mojsklep.pl <small>312 podstron, 41 s</small></div><div class="wynik"><b>62</b><span>punkty na 100<br>3 błędy, 2 ostrzeżenia, 9 sprawdzeń OK</span></div><div class="pasek-w"><i></i></div><ul>'
           '<li><span class="b">BŁĄD</span> 98 adresów z mapy strony zwraca 404</li><li><span class="b">BŁĄD</span> 12 promocji bez najniższej ceny z 30 dni (Omnibus)</li><li><span class="b">BŁĄD</span> brak danych producenta przy 27 produktach (GPSR)</li><li><span class="u">UWAGA</span> 41 produktów bez numeru EAN</li><li><span class="u">UWAGA</span> cena w Ceneo różni się w 6 ofertach</li><li><span class="o">OK</span> certyfikat SSL ważny 214 dni</li><li><span class="o">OK</span> regulamin i polityka zwrotów dostępne</li></ul></div>')
    mosty = [("Formularz → CRM","nowa sprawa · 12:04",False,[6,7,5,8,7,9,8]),("Kalendarz → realizacja","termin · 12:04",False,[8,8,7,9,8,8,9]),("wFirma → KSeF","UPO · 12:04",False,[5,6,6,7,8,8,9]),("CRM → faktury","dokument · 12:04",True,[7,7,3,2,4,6,7]),("Faktury → KSeF","UPO · 12:04",False,[9,8,9,9,8,9,9]),("CRM → klient","e-mail · 12:04",False,[8,9,8,8,9,9,8])]
    kaf = ''.join(f'<div class="kafel{" uwaga" if u else ""}"><b>{n}</b><span>{o}</span><i>' + ''.join(f'<em style="height:{h*10}%"></em>' for h in sl) + '</i></div>' for n,o,u,sl in mosty)
    panel = f'<div class="panel"><div class="gora-p">Strażnik połączeń <small>wtorek 8.09 · sprawdzono 06:00</small></div><div class="kafle">{kaf}</div><div class="dol"><div><b>12</b>mostów</div><div><b>1</b>ostrzeżenie</div><div><b>0</b>awarii</div><div><b>14 dni</b>od ostatniej naprawy</div></div></div>'
    karty = [("#5b6cff","Konfigurator","PV Roof Configurator",'<img src="zdjecia/photonroof-wymiary.jpg" alt="" fetchpriority="high" decoding="async">',"Konfigurator dachówek fotowoltaicznych","Klient podaje parametry dachu i otrzymuje podsumowanie w przeglądarce. <span>Dane z konfiguracji można przekazać do dalszej wyceny.</span>","realizacje.html#photonroof"),
             ("#e6982f","Panel firmy","<span style=\"font-size:.72em\">Wypożyczalnia</span>",'<img data-carousel-src="zdjecia/wypozyczalnia-flota-800.webp?v=20261006b" data-carousel-srcset="zdjecia/wypozyczalnia-flota-800.webp?v=20261006b 800w, zdjecia/wypozyczalnia-flota.webp?v=20261006b 1440w" data-carousel-sizes="(max-width: 820px) calc(100vw - 44px), 720px" alt="" width="1440" height="900" fetchpriority="low" decoding="async">',"Panel wypożyczalni samochodowej","Flota, najmy, faktury i kalendarz, który sam wykrywa podwójną rezerwację. <span>Przykład systemu szytego pod jedną branżę.</span>","realizacje.html#wypozyczalnia"),
             ("#2f9e88","Narzędzie","Sprawdzarka",spr,"Sprawdzarka sklepu","Wpisujesz adres, dostajesz listę tego, co widać z zewnątrz: GPSR, Omnibus, EAN, mapa strony. <span>Bezpłatnie, działa dziś.</span>","https://automatyzacjesklepow.pl/sprawdzarka.html"),
             ("#c8473f","Abonament","Strażnik",panel,"Strażnik połączeń","Codziennie sprawdza, czy formularze, CRM, kalendarz, dokumenty i integracje nadal wymieniają dane. <span>Powiadomienia pomagają szybciej zauważyć przerwę w wymianie danych.</span>","cennik.html#straznik")]
    k = ''
    for i,(kol,nad,duze,obr,tyt,op,link) in enumerate(karty):
        zd = f'<div class="zdjecie">{obr}</div>' if i < 2 else (f'<div class="zdjecie panelowe jasne">{obr}</div>' if i == 2 else f'<div class="zdjecie panelowe">{obr}</div>')
        k += f'<article class="karta{" aktywna" if i==0 else (" pod-spodem" if i==1 else "")}" style="background:{kol}"><div class="duze"><small>{nad}</small>{duze}</div>{zd}<div class="opis"><b>{tyt}</b>{op}<br><a href="{link}" aria-label="Zobacz więcej: {html.escape(tyt)}">Zobacz więcej</a></div></article>'
    strz = lambda kl, d: f'<button class="strzalka {kl}" type="button" aria-label="{ "Poprzednia" if kl=="lewa" else "Następna"} karta"><svg viewBox="0 0 64 44" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="{d}"/></svg></button>'
    return ('<div class="ksiega" role="region" tabindex="0" aria-label="Realizacje. Użyj strzałek w lewo i w prawo." aria-roledescription="karuzela"><div class="karty">' + k + '</div>' + strz("lewa","M60 22 C40 10 24 12 6 22 M16 12 L6 22 L16 32") + strz("prawa","M4 22 C24 10 40 12 58 22 M48 12 L58 22 L48 32") + '<div class="kropy">' + ''.join(f'<button type="button" class="{"tu" if i==0 else ""}" aria-label="Karta {i+1}"></button>' for i in range(4)) + '</div></div>')

def ekrany():
    return '<div class="ekrany"><div class="ekran a"><img src="zdjecia/photonroof-kreator3d.jpg" alt="" fetchpriority="high" decoding="async"></div><div class="ekran b" aria-hidden="true"><span class="screen-bg"></span></div></div>'

ASSET_VERSION = hashlib.sha256((CSS + "\n" + JS).encode("utf-8")).hexdigest()[:10]
CASE_IMAGE_VERSION = "20261006b"

# ---------------------------------------------------------------- szkielet
NAV = '<a href="dedykowane-oprogramowanie-dla-firm.html">Usługi</a><a href="realizacje.html">Realizacje</a><a href="jak-pracuje.html">Jak pracuję</a><a href="cennik.html">Cennik</a><a href="poradniki.html">Poradniki</a><a href="o-mnie.html">O mnie</a><a class="nav-cta" data-umami-event="klik-opisz-projekt" href="opisz-projekt.html">Opisz projekt</a>'
ARTYKULY = {
  "system-zamiast-excela", "gotowy-system-czy-dedykowane-oprogramowanie",
  "ile-kosztuje-aplikacja-dla-firmy", "jak-przygotowac-brief-aplikacji",
  "ai-w-automatyzacji-firmy", "wtyczka-czy-integracja", "ksef-dla-jdg-terminy",
}
ECOMMERCE = {
  "sprawdzarka", "automatyczne-faktury-allegro", "automatyzacja-allegro",
  "integracja-allegro-z-woocommerce", "integracja-baselinker",
  "integracja-sklepu-z-fakturownia", "integracja-sklepu-z-hurtownia",
  "integracja-sklepu-z-ksiegowoscia", "integracja-sklepu-z-wfirma",
  "integracje-idosell", "integracje-shoper", "ksef-dla-sklepu-internetowego",
}
USLUGI = {
  "dedykowane-oprogramowanie-dla-firm", "aplikacje-webowe-dla-firm",
  "automatyzacja-dokumentow-w-firmie", "automatyzacja-procesow-w-firmie",
  "crm-na-zamowienie", "system-do-wycen-i-ofert", "integracje-api-dla-firm", "kalkulator-konfigurator-dla-klientow",
  "panel-klienta-b2b", "program-dla-wypozyczalni", "system-dla-firmy-uslugowej",
  "system-dla-produkcji-na-zamowienie", "system-dla-serwisu-technicznego",
  "system-do-obslugi-zlecen", "system-rezerwacji-dla-firm", "jak-pracuje",
}

POWIAZANE = {
  "dedykowane-oprogramowanie-dla-firm": [
    ("Jak pracuję", "jak-pracuje.html", "Zobacz, jak dzielę projekt na małe, działające etapy."),
    ("Ile kosztuje aplikacja?", "ile-kosztuje-aplikacja-dla-firmy.html", "Sprawdź, co wpływa na cenę i zakres projektu."),
    ("Opisz projekt", "opisz-projekt.html", "Opisz obecną pracę i oczekiwany efekt."),
  ],
  "crm-na-zamowienie": [
    ("System do wycen i ofert", "system-do-wycen-i-ofert.html", "Kalkulacja, marża, rabaty i PDF jako kolejny krok procesu sprzedaży."),
    ("System do obsługi zleceń", "system-do-obslugi-zlecen.html", "Co dzieje się ze sprawą po wygranej sprzedaży."),
    ("Opisz proces sprzedaży", "opisz-projekt.html?typ=CRM%20lub%20obsługa%20sprzedaży", "Przejdź od obecnego procesu do pierwszego modułu."),
  ],
  "system-do-obslugi-zlecen": [
    ("Automatyzacja dokumentów", "automatyzacja-dokumentow-w-firmie.html", "Protokoły, potwierdzenia i PDF z danych zlecenia."),
    ("Panel klienta B2B", "panel-klienta-b2b.html", "Udostępnij klientowi status i dokumenty bez telefonów."),
    ("Opisz jedno zlecenie", "opisz-projekt.html?typ=System%20do%20obsługi%20zleceń", "Pokaż drogę sprawy od zapytania do zakończenia."),
  ],
  "system-zamiast-excela": [
    ("Gotowy czy dedykowany?", "gotowy-system-czy-dedykowane-oprogramowanie.html", "Sprawdź, czy na pewno potrzebujesz własnego systemu."),
    ("Aplikacje webowe", "aplikacje-webowe-dla-firm.html", "Jak wygląda wspólna aplikacja zamiast wielu arkuszy."),
    ("Pokaż obecny proces", "opisz-projekt.html?typ=System%20zamiast%20Excela", "Opisz, co dziś robicie w Excelu."),
  ],
  "integracje-api-dla-firm": [
    ("Automatyzacja procesów", "automatyzacja-procesow-w-firmie.html", "Połącz integracje z regułami całego procesu."),
    ("Monitoring i opieka", "cennik.html#straznik", "Co dzieje się, gdy zewnętrzne API przestanie działać."),
    ("Podaj dwa systemy", "opisz-projekt.html?typ=Integracja%20kilku%20programów%20%2F%20API", "Zacznij od źródła danych i miejsca docelowego."),
  ],
  "automatyzacja-procesow-w-firmie": [
    ("Policz koszt ręcznej pracy", "kalkulator-kosztu-recznej-pracy.html", "Zobacz, ile godzin miesięcznie pochłania powtarzalna czynność."),
    ("Integracje API", "integracje-api-dla-firm.html", "Usuń ręczne przenoszenie danych między programami."),
    ("Opisz powtarzalną czynność", "opisz-projekt.html", "Wskaż krok, który zespół wykonuje codziennie."),
  ],
  "aplikacje-webowe-dla-firm": [
    ("Panel klienta B2B", "panel-klienta-b2b.html", "Przykład aplikacji dostępnej dla klientów po logowaniu."),
    ("System rezerwacji", "system-rezerwacji-dla-firm.html", "Przykład aplikacji z kalendarzem i zasobami."),
    ("Jak pracuję", "jak-pracuje.html", "Od pierwszego modułu do stabilnej aplikacji."),
  ],
  "panel-klienta-b2b": [
    ("Integracje API", "integracje-api-dla-firm.html", "Panel powinien korzystać z tych samych danych co firma."),
    ("Automatyzacja dokumentów", "automatyzacja-dokumentow-w-firmie.html", "Dokumenty klienta generowane z procesu."),
    ("Opisz obsługę klienta", "opisz-projekt.html?typ=Panel%20klienta%20B2B", "Wskaż pytania, na które pracownicy odpowiadają najczęściej."),
  ],
  "system-rezerwacji-dla-firm": [
    ("Program dla wypożyczalni", "program-dla-wypozyczalni.html", "Rezerwacja zasobu w praktycznym przykładzie."),
    ("Integracje API", "integracje-api-dla-firm.html", "Kalendarz, płatność i CRM jako jeden proces."),
    ("Opisz reguły rezerwacji", "opisz-projekt.html?typ=System%20rezerwacji", "Co poza terminem decyduje o dostępności?"),
  ],
  "kalkulator-konfigurator-dla-klientow": [
    ("Realizacja PV Roof Configurator", "realizacje.html#photonroof", "Zobacz konfigurator oparty na parametrach klienta."),
    ("System do wycen i ofert", "system-do-wycen-i-ofert.html", "Połącz dane klienta z wewnętrzną kalkulacją handlową i ofertą PDF."),
    ("Opisz logikę wyceny", "opisz-projekt.html?typ=Kalkulator%20lub%20konfigurator%20dla%20klientów", "Pokaż, co handlowiec dziś liczy ręcznie."),
  ],
  "automatyzacja-dokumentow-w-firmie": [
    ("System zleceń", "system-do-obslugi-zlecen.html", "Dokument jako kolejny krok realizacji."),
    ("System do wycen i ofert", "system-do-wycen-i-ofert.html", "Oferta PDF generowana z policzonej i zatwierdzonej wyceny."),
    ("Podeślij wzór dokumentu", "opisz-projekt.html?typ=Automatyzacja%20dokumentów", "Zacznij od dokumentu, który dziś powstaje ręcznie."),
  ],
  "ai-w-automatyzacji-firmy": [
    ("Automatyzacja procesów", "automatyzacja-procesow-w-firmie.html", "Sprawdź, które powtarzalne zadania można zautomatyzować."),
    ("Integracje API", "integracje-api-dla-firm.html", "AI jako jeden krok większego systemu."),
    ("Opisz zadanie dla AI", "opisz-projekt.html?typ=Automatyzacja%20z%20AI", "Pokaż, co dziś wymaga czytania lub interpretacji."),
  ],
  "program-dla-wypozyczalni": [
    ("Realizacja wypożyczalni", "realizacje.html#wypozyczalnia", "Zobacz kalendarz, flotę i faktury na ekranach."),
    ("System rezerwacji", "system-rezerwacji-dla-firm.html", "Logika dostępności i blokowania kolizji."),
    ("Opisz swoją flotę lub sprzęt", "opisz-projekt.html", "Jak dziś pilnujesz dostępności, dokumentów i zwrotów?"),
  ],
  "system-dla-firmy-uslugowej": [
    ("Obsługa zleceń", "system-do-obslugi-zlecen.html", "Rdzeń większości procesów usługowych."),
    ("System rezerwacji", "system-rezerwacji-dla-firm.html", "Jeśli klient wybiera termin lub zasób."),
    ("Opisz jedną usługę", "opisz-projekt.html", "Od zapytania klienta do rozliczenia."),
  ],
  "system-dla-serwisu-technicznego": [
    ("Obsługa zleceń", "system-do-obslugi-zlecen.html", "Status, technik, termin i historia sprawy."),
    ("Automatyzacja dokumentów", "automatyzacja-dokumentow-w-firmie.html", "Protokół serwisowy z danych i zdjęć."),
    ("Opisz zgłoszenie", "opisz-projekt.html", "Pokaż drogę od awarii do zamknięcia naprawy."),
  ],
  "system-dla-produkcji-na-zamowienie": [
    ("System do wycen i ofert", "system-do-wycen-i-ofert.html", "Połącz kalkulację handlową, wersję oferty i specyfikację przekazywaną do realizacji."),
    ("Integracje API", "integracje-api-dla-firm.html", "Połącz sprzedaż z obecnym ERP lub magazynem."),
    ("Opisz drogę zamówienia", "opisz-projekt.html", "Od zapytania i specyfikacji do uruchomienia realizacji."),
  ],
  "system-do-wycen-i-ofert": [
    ("CRM na zamówienie", "crm-na-zamowienie.html", "Klient, szansa i historia kontaktu przed przygotowaniem wyceny."),
    ("Automatyzacja dokumentów", "automatyzacja-dokumentow-w-firmie.html", "Szablony PDF, wersje i dokumenty generowane z danych procesu."),
    ("Opisz obecny sposób wyceny", "opisz-projekt.html?typ=System%20do%20wycen%20i%20ofert", "Podeślij logikę ceny, rabatów i jeden przykładowy wzór oferty."),
  ],
  "ile-kosztuje-aplikacja-dla-firmy": [
    ("Cennik", "cennik.html", "Zobacz jawne ceny pierwszych etapów."),
    ("Jak pracuję", "jak-pracuje.html", "Dlaczego projekt dzielę na działające moduły."),
    ("Opisz projekt", "opisz-projekt.html", "Podaj informacje potrzebne do wstępnej wyceny."),
  ],
  "gotowy-system-czy-dedykowane-oprogramowanie": [
    ("System zamiast Excela", "system-zamiast-excela.html", "Przykład sytuacji, w której własne narzędzie może mieć sens."),
    ("Integracje API", "integracje-api-dla-firm.html", "Czasem wystarczy połączyć to, co już działa."),
    ("Opisz obecne narzędzia", "opisz-projekt.html", "Sprawdźmy, czego naprawdę brakuje."),
  ],
  "jak-przygotowac-brief-aplikacji": [
    ("Opisz projekt", "opisz-projekt.html", "Formularz przeprowadzi Cię przez dokładnie te pytania."),
    ("Ile kosztuje aplikacja?", "ile-kosztuje-aplikacja-dla-firmy.html", "Zobacz, co wpływa na budżet."),
    ("Jak pracuję", "jak-pracuje.html", "Co dzieje się po pierwszym opisie procesu."),
  ],
}

def blok_powiazanych(nazwa):
    pozycje=POWIAZANE.get(nazwa)
    if not pozycje:
        return ""
    karty=[]
    for tyt,href,opis in pozycje:
        event=' data-umami-event="klik-opisz-projekt-powiazane"' if href.startswith("opisz-projekt.html") else ""
        if href.startswith("opisz-projekt.html") and "zrodlo=" not in href:
            sep = "&" if "?" in href else "?"
            href = f"{href}{sep}zrodlo={nazwa}-powiazane"
        karty.append(f'<a class="powiazane-karta" href="{href}"{event}><strong>{tyt}</strong><span>{opis}</span><i aria-hidden="true">→</i></a>')
    return '<aside class="powiazane" aria-labelledby="powiazane-title"><p class="etykieta">Co dalej?</p><h2 id="powiazane-title">Przydatne informacje</h2><div class="powiazane-grid">'+''.join(karty)+'</div></aside>'

def blok_autora(nazwa):
    if nazwa not in ARTYKULY:
        return ""
    return '''<aside class="autor-box" aria-label="Autor tekstu">
      <div><span class="autor-znak" aria-hidden="true"><img src="znak-bialy.svg" width="28" height="17" alt=""></span></div>
      <div><strong>Maciej Gryziec</strong><p>Projektuję aplikacje, integracje i automatyzacje wokół realnego procesu firmy. Na stronie pokazuję zarówno rozwiązania dedykowane, jak i sytuacje, w których lepiej zostać przy gotowym narzędziu.</p><p><a href="o-mnie.html">O mnie</a> · <a href="realizacje.html">Zobacz realizacje</a></p></div>
    </aside>'''

WYMIARY_ZDJEC = {
    "photonroof-kopertowy.jpg": (1600, 905),
    "photonroof-kreator3d.jpg": (1600, 833),
    "photonroof-mapa.jpg": (1600, 827),
    "photonroof-tryby.png": (1280, 800),
    "photonroof-wymiary.jpg": (1600, 914),
    "wypozyczalnia-faktury.png": (1440, 900),
    "wypozyczalnia-flota.png": (1440, 900),
    "wypozyczalnia-kalendarz.png": (1440, 740),
    "wypozyczalnia-pulpit.png": (1440, 900),
    "frankie-orders-focus.webp": (1080, 708),
    "frankie-products-focus.webp": (1080, 706),
    "frankie-analytics-focus.webp": (1080, 707),
    "judler-dashboard.webp": (691, 482),
    "monitoring-dashboard.webp": (691, 482),
    "sleeper-garage-screen.png": (1600, 900),
    "sleeper-garage-screen.webp": (1600, 900),
    "bacteria-hd-menu.webp": (2048, 853),
    "bacteria-hd-gameplay.webp": (2047, 859),
    "bacteria-hd-bacteria.webp": (2048, 860),
    "bacteria-hd-vehicles.webp": (2048, 861),
    "bacteria-hd-clothes.webp": (2047, 856),
    "bacteria-hd-hats.webp": (2048, 859),
}

# Pełne WebP istniejących JPG/PNG mają te same wymiary co źródła.
for _name, _dims in list(WYMIARY_ZDJEC.items()):
    _stem, _ext = os.path.splitext(_name)
    _webp = _stem + ".webp"
    if os.path.exists(os.path.join(REPO, "zdjecia", _webp)):
        WYMIARY_ZDJEC.setdefault(_webp, _dims)

def uzupelnij_wymiary_obrazow(html_text):
    def repl(m):
        caly=m.group(0)
        plik=m.group(1)
        plik_czysty=plik.split("?",1)[0].split("#",1)[0]
        if plik_czysty not in WYMIARY_ZDJEC:
            return caly
        if not re.search(r'\bwidth=', caly):
            w,h=WYMIARY_ZDJEC[plik_czysty]
            caly=caly[:-1] + f' width="{w}" height="{h}">'
        if 'data-webp=' in caly:
            return caly
        webp=os.path.splitext(plik_czysty)[0] + ".webp"
        webp_path=os.path.join(REPO, "zdjecia", webp)
        if not os.path.exists(webp_path):
            return caly
        w,_=WYMIARY_ZDJEC[plik_czysty]
        case_asset = plik_czysty.startswith("photonroof-") or plik_czysty.startswith("wypozyczalnia-")
        suffix = f"?v={CASE_IMAGE_VERSION}" if case_asset else ""
        webp_800=os.path.splitext(plik_czysty)[0] + "-800.webp"
        webp_800_path=os.path.join(REPO, "zdjecia", webp_800)
        if os.path.exists(webp_800_path):
            srcset=f'zdjecia/{webp_800}{suffix} 800w, zdjecia/{webp}{suffix} {w}w'
            sizes='(max-width: 820px) calc(100vw - 44px), 720px'
            source=f'<source srcset="{srcset}" sizes="{sizes}" type="image/webp">'
        else:
            source=f'<source srcset="zdjecia/{webp}{suffix}" type="image/webp">'
        if suffix and "?" not in plik:
            caly=caly.replace(f'src="zdjecia/{plik}"', f'src="zdjecia/{plik}{suffix}"', 1)
        caly=caly[:-1] + ' data-webp="1">'
        return f'<picture>{source}{caly}</picture>'
    return re.sub(r'<img\b[^>]*\ssrc="zdjecia/([^"]+)"[^>]*>', repl, html_text)

def wersjonuj_portfolio(html_text):
    for name in ("portfolio-display.css", "judler-motion.js", "projekt-showcase.css", "projekt-showcase.js", "realizacje-projekty.css", "realizacje-projekty.js", "znak.svg", "znak-bialy.svg"):
        asset = os.path.join(REPO, name)
        with open(asset, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()[:12]
        pattern = r'((?:href|src)=")' + re.escape(name) + r'(?:\?[^" ]*)?"'
        html_text = re.sub(pattern, lambda m: m.group(1) + name + "?v=" + digest + '"', html_text)
    return html_text

def oznacz_lazy_po_pierwszej_sekcji(html_text):
    """Obrazy po pierwszej sekcji ładuj leniwie; hero pozostaje natychmiastowy."""
    first_end=html_text.find("</section>")
    if first_end < 0:
        return html_text
    head=html_text[:first_end+10]
    tail=html_text[first_end+10:]
    def repl(m):
        tag=m.group(0)
        if 'src="zdjecia/' not in tag:
            return tag
        if not re.search(r'\bloading=', tag, re.I):
            tag=tag[:-1] + ' loading="lazy">'
        if not re.search(r'\bdecoding=', tag, re.I):
            tag=tag[:-1] + ' decoding="async">'
        tag=re.sub(r'\s+fetchpriority="high"', '', tag, flags=re.I)
        return tag
    return head + re.sub(r'<img\b[^>]*>', repl, tail, flags=re.I)

def slug_kotwicy(tekst):
    tekst=html.unescape(re.sub(r"<[^>]+>","",tekst))
    tekst=tekst.translate(str.maketrans({"ł":"l","Ł":"L","đ":"d","Đ":"D"}))
    tekst=unicodedata.normalize("NFKD",tekst).encode("ascii","ignore").decode("ascii").lower()
    tekst=re.sub(r"[^a-z0-9]+","-",tekst).strip("-")
    return tekst[:80] or "sekcja"

def dodaj_spis_tresci(body):
    naglowki=[]; used=set()
    def repl(m):
        attrs=m.group(1) or ""; inner=m.group(2)
        idm=re.search(r'\bid="([^"]+)"',attrs)
        base=idm.group(1) if idm else slug_kotwicy(inner)
        ident=base; n=2
        while ident in used:
            ident=f"{base}-{n}"; n+=1
        used.add(ident)
        if not idm: attrs += f' id="{ident}"'
        label=' '.join(re.sub(r'<[^>]+>',' ',html.unescape(inner)).split())
        naglowki.append((ident,label))
        return f'<h2{attrs}>{inner}</h2>'
    body=re.sub(r'<h2([^>]*)>(.*?)</h2>',repl,body,flags=re.S|re.I)
    if len(naglowki)<3:
        return body
    links=''.join(f'<li><a href="#{ident}">{html.escape(label)}</a></li>' for ident,label in naglowki)
    toc=f'<nav class="spis-tresci" aria-label="Spis treści"><strong>Na tej stronie</strong><ol>{links}</ol></nav>'
    return toc+body

def rodzic_dla(nazwa):
    if nazwa in ARTYKULY or nazwa == "kalkulator-kosztu-recznej-pracy":
        return ("Poradniki", "poradniki.html")
    if nazwa in ECOMMERCE and nazwa != "sprawdzarka":
        return ("Dla sklepów", "sprawdzarka.html")
    if nazwa in USLUGI and nazwa != "dedykowane-oprogramowanie-dla-firm":
        return ("Dla firm", "dedykowane-oprogramowanie-dla-firm.html")
    return None

OG_MEDIA = {
  "realizacje": ("https://maciejgryziec.pl/zdjecia/photonroof-kreator3d.jpg?v=20261006b", 1600, 833, "Kreator 3D dachu w aplikacji RoofPVCalculator"),
  "kalkulator-konfigurator-dla-klientow": ("https://maciejgryziec.pl/zdjecia/photonroof-kreator3d.jpg?v=20261006b", 1600, 833, "Kreator 3D i kalkulator PV Roof Configurator"),
  "program-dla-wypozyczalni": ("https://maciejgryziec.pl/zdjecia/wypozyczalnia-kalendarz.png?v=20261006b", 1440, 740, "Kalendarz obłożenia w panelu wypożyczalni"),
  "system-rezerwacji-dla-firm": ("https://maciejgryziec.pl/zdjecia/wypozyczalnia-kalendarz.png?v=20261006b", 1440, 740, "Przykład kalendarza rezerwacji zasobów"),
}

def faq_zrodla(nazwa):
    """Zwraca widoczne pytania/odpowiedzi z bloku .pytania w źródle strony."""
    if not nazwa:
        return []
    sciezka=os.path.join(ZR,nazwa+".html")
    if not os.path.exists(sciezka):
        return []
    src=open(sciezka,encoding="utf-8").read()
    blok=re.search(r'<div class="pytania"[^>]*>(.*?)</div>',src,re.S|re.I)
    if not blok:
        return []
    wynik=[]
    for summary,answer in re.findall(
        r'<details[^>]*>\s*<summary>(.*?)</summary>(.*?)</details>',
        blok.group(1),
        re.S|re.I,
    ):
        pytanie=' '.join(re.sub(r'<[^>]+>',' ',html.unescape(summary)).split())
        odpowiedz=' '.join(re.sub(r'<[^>]+>',' ',html.unescape(answer)).split())
        if pytanie and odpowiedz:
            wynik.append((pytanie,odpowiedz))
    return wynik


def glowa(tytul, opis, kanon, nazwa=None):
    PAL = f'\n<link rel="stylesheet" href="paleta-{PALETA}.css?w=1">' if PALETA else ''
    PRELOAD = ''
    if nazwa == "realizacje":
        PRELOAD = ('\n<link rel="preload" as="image" '
                   'href="zdjecia/photonroof-wymiary-800.webp?v=20261006b" '
                   'imagesrcset="zdjecia/photonroof-wymiary-800.webp?v=20261006b 800w, zdjecia/photonroof-wymiary.webp?v=20261006b 1600w" '
                   'imagesizes="(max-width: 820px) calc(100vw - 44px), 720px" '
                   'type="image/webp" fetchpriority="high">')
    og_image, og_w, og_h, og_alt = OG_MEDIA.get(nazwa, ("https://maciejgryziec.pl/og-image.png", 1200, 630, "Maciej Gryziec: aplikacje i automatyzacje dla firm"))
    og_mime = "image/png" if og_image.lower().endswith(".png") else "image/jpeg"
    page_type = "ContactPage" if nazwa == "opisz-projekt" else ("CollectionPage" if nazwa in ("poradniki","realizacje") else "WebPage")
    graph = [{
        "@type":page_type, "@id":kanon+"#webpage", "url":kanon, "name":tytul,
        "description":opis, "inLanguage":"pl-PL",
        "isPartOf":{"@id":"https://maciejgryziec.pl/#website"}
    }]
    if nazwa:
        elementy=[{"@type":"ListItem","position":1,"name":"Start","item":"https://maciejgryziec.pl/"}]
        rodzic=rodzic_dla(nazwa)
        pos=2
        if rodzic:
            elementy.append({"@type":"ListItem","position":pos,"name":rodzic[0],"item":"https://maciejgryziec.pl/"+rodzic[1]})
            pos+=1
        elementy.append({"@type":"ListItem","position":pos,"name":tytul,"item":kanon})
        graph.append({"@type":"BreadcrumbList","itemListElement":elementy})
        if nazwa in ARTYKULY:
            sciezka_art=os.path.join(ZR,nazwa+".html")
            data_modyfikacji=data_pliku(sciezka_art)
            graph.append({
                "@type":"BlogPosting","headline":tytul,"description":opis,"inLanguage":"pl-PL",
                "datePublished":data_publikacji(sciezka_art),"dateModified":data_modyfikacji,
                "image":"https://maciejgryziec.pl/og-image.png",
                "mainEntityOfPage":{"@id":kanon+"#webpage"},
                "author":{"@type":"Person","@id":"https://maciejgryziec.pl/o-mnie.html#person","name":"Maciej Gryziec","url":"https://maciejgryziec.pl/o-mnie.html"}
            })
    if nazwa == "o-mnie":
        graph.append({
            "@type":"Person","@id":"https://maciejgryziec.pl/o-mnie.html#person",
            "name":"Maciej Gryziec","url":"https://maciejgryziec.pl/o-mnie.html",
            "email":"kontakt@maciejgryziec.pl","telephone":"+48570427127"
        })
        graph.append({
            "@type":"ProfilePage","@id":kanon+"#profile","url":kanon,"name":tytul,
            "mainEntity":{"@id":"https://maciejgryziec.pl/o-mnie.html#person"}
        })
    if nazwa in USLUGI and nazwa != "jak-pracuje":
        graph.append({
            "@type":"Service","@id":kanon+"#service","name":tytul,"description":opis,"url":kanon,
            "areaServed":{"@type":"Country","name":"Polska"},
            "provider":{"@type":"Person","@id":"https://maciejgryziec.pl/o-mnie.html#person","name":"Maciej Gryziec","url":"https://maciejgryziec.pl/o-mnie.html"}
        })
    if nazwa == "poradniki":
        src_por=open(os.path.join(ZR,"poradniki.html"),encoding="utf-8").read()
        lista=[]; seen=set()
        for href,label in re.findall(r'<li><a href="([^"]+)">(.*?)</a>',src_por,re.S):
            clean=re.sub(r'<[^>]+>', '', label).strip()
            if not href.endswith('.html') or href in seen: continue
            seen.add(href)
            lista.append({"@type":"ListItem","position":len(lista)+1,"name":clean,"url":"https://maciejgryziec.pl/"+href})
        graph.append({"@type":"ItemList","name":"Poradniki i rozwiązania dla firm","itemListElement":lista})
    if nazwa == "kalkulator-kosztu-recznej-pracy":
        graph.append({
            "@type":"WebApplication","name":tytul,"description":opis,"url":kanon,
            "applicationCategory":"BusinessApplication","operatingSystem":"Any",
            "browserRequirements":"JavaScript",
            "offers":{"@type":"Offer","price":"0","priceCurrency":"PLN"}
        })
    faq=faq_zrodla(nazwa)
    if faq:
        graph.append({
            "@type":"FAQPage",
            "@id":kanon+"#faq",
            "mainEntity":[
                {
                    "@type":"Question",
                    "name":pytanie,
                    "acceptedAnswer":{"@type":"Answer","text":odpowiedz},
                }
                for pytanie,odpowiedz in faq
            ],
        })
    LD=json.dumps({"@context":"https://schema.org","@graph":graph},ensure_ascii=False)
    og_type = "article" if nazwa in ARTYKULY else "website"
    nav_active = ""
    if nazwa == "jak-pracuje":
        nav_active = "jak-pracuje.html"
    elif nazwa == "o-mnie":
        nav_active = "o-mnie.html"
    elif nazwa in ECOMMERCE:
        nav_active = ""
    elif nazwa in USLUGI or nazwa == "problemy":
        nav_active = "dedykowane-oprogramowanie-dla-firm.html"
    elif nazwa in ARTYKULY or nazwa in {"poradniki", "kalkulator-kosztu-recznej-pracy"}:
        nav_active = "poradniki.html"
    elif nazwa in {"realizacje", "cennik", "opisz-projekt"}:
        nav_active = nazwa + ".html"
    nav_attr = f' data-nav-active="{nav_active}"' if nav_active else ""
    source_slug = nazwa or "index"
    nav_html = NAV.replace(
        'href="opisz-projekt.html"',
        f'href="opisz-projekt.html?zrodlo={source_slug}-nav"',
        1,
    )
    mobile_href = f"opisz-projekt.html?zrodlo={source_slug}-mobile"
    article_tags = ""
    if nazwa in ARTYKULY:
        sciezka_art=os.path.join(ZR,nazwa+".html")
        data_modyfikacji=data_pliku(sciezka_art)
        data_pub=data_publikacji(sciezka_art)
        article_tags = f'\n<meta property="article:published_time" content="{data_pub}T00:00:00+02:00">\n<meta property="article:modified_time" content="{data_modyfikacji}T00:00:00+02:00">\n<meta property="article:author" content="https://maciejgryziec.pl/o-mnie.html">\n<link rel="author" href="o-mnie.html">'
    return f'''<!doctype html>
<html class="no-js" lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.remove("no-js");document.documentElement.classList.add("js");</script>
<meta name="theme-color" content="#194586">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<title>{tytul}</title>
<meta name="description" content="{opis}">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="pl_PL">{article_tags}
<meta property="og:site_name" content="Maciej Gryziec">
<meta property="og:title" content="{tytul}">
<meta property="og:description" content="{opis}">
<meta property="og:url" content="{kanon}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="{og_w}">
<meta property="og:image:height" content="{og_h}">
<meta property="og:image:type" content="{og_mime}">
<meta property="og:image:alt" content="{og_alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{tytul}">
<meta name="twitter:description" content="{opis}">
<meta name="twitter:image" content="{og_image}">
<meta name="twitter:image:alt" content="{og_alt}">
<link rel="canonical" href="{kanon}">
<link rel="alternate" type="application/atom+xml" title="Poradniki Macieja Gryźca" href="feed.xml">{PRELOAD}
<link rel="stylesheet" href="list.css?v={ASSET_VERSION}">{PAL}
<link rel="icon" type="image/svg+xml" href="ikona.svg?v=8ef07109ecdc" sizes="any">
<link rel="icon" href="favicon.ico?v=8ef07109ecdc" sizes="16x16 32x32 48x48 96x96">
<link rel="icon" type="image/png" sizes="96x96" href="favicon.png">
<link rel="icon" type="image/png" sizes="192x192" href="ikona-192.png?v=8ef07109ecdc">
<link rel="apple-touch-icon" href="ikona-180.png?v=8ef07109ecdc">
<link rel="mask-icon" href="znak.svg" color="#194586">
<link rel="manifest" href="site.webmanifest">
<script type="application/ld+json">{LD}</script>
</head>
<body{nav_attr}>
<a class="skip-link" href="#main-content">Przejdź do treści</a>
<header class="gora"><div class="w">
  <a class="znak" href="/" aria-label="Maciej Gryziec: aplikacje i automatyzacje dla firm"><img class="c" src="znak.svg" alt=""><img class="b" src="znak-bialy.svg" alt=""><span>Maciej Gryziec</span></a>
  <div class="mobile-actions"><a class="mobile-cta" data-umami-event="klik-opisz-projekt-mobile" href="{mobile_href}">Opisz projekt</a><button class="menu-toggle" type="button" aria-label="Otwórz menu" aria-controls="nav-main" aria-expanded="false"><i></i></button></div>
  <nav id="nav-main" aria-label="Główna nawigacja">{nav_html}</nav>
</div></header>
'''
STOPKA = f"""
<footer class="stopka">
  <div class="stopka-grid">
    <div class="stopka-brand">
      <strong>Maciej Gryziec</strong>
      <p>Aplikacje, systemy i automatyzacje dla firm. Pracuję zdalnie z firmami w całej Polsce.</p>
      <p><a class="stopka-cta" data-umami-event="klik-opisz-projekt" href="opisz-projekt.html">Opisz projekt →</a></p>
      <p><a data-umami-event="klik-mail" href="mailto:kontakt@maciejgryziec.pl">kontakt@maciejgryziec.pl</a><br><a data-umami-event="klik-telefon" href="tel:+48570427127">570 427 127</a></p>
    </div>
    <div>
      <strong>Rozwiązania</strong>
      <a href="dedykowane-oprogramowanie-dla-firm.html">Oprogramowanie na zamówienie</a>
      <a href="crm-na-zamowienie.html">CRM na zamówienie</a>
      <a href="system-do-wycen-i-ofert.html">Wyceny i oferty</a>
      <a href="system-do-obslugi-zlecen.html">Obsługa zleceń</a>
      <a href="integracje-api-dla-firm.html">Integracje API</a>
      <a href="aplikacje-webowe-dla-firm.html">Aplikacje webowe</a>
    </div>
    <div>
      <strong>Zastosowania</strong>
      <a href="system-zamiast-excela.html">System zamiast Excela</a>
      <a href="panel-klienta-b2b.html">Panel klienta B2B</a>
      <a href="system-rezerwacji-dla-firm.html">System rezerwacji</a>
      <a href="automatyzacja-dokumentow-w-firmie.html">Automatyzacja dokumentów</a>
      <a href="https://automatyzacjesklepow.pl/">Automatyzacje e-commerce</a>
    </div>
    <div>
      <strong>Firma i wiedza</strong>
      <a href="realizacje.html">Realizacje</a>
      <a href="cennik.html">Cennik</a>
      <a href="jak-pracuje.html">Jak pracuję</a>
      <a href="o-mnie.html">O mnie</a>
      <a href="poradniki.html">Poradniki</a>
    </div>
  </div>
  <div class="stopka-dol">
    <span>© 2026 Maciej Gryziec</span>
    <a href="polityka-prywatnosci.html">Polityka prywatności</a>
    <a href=".well-known/security.txt">Zgłoszenia bezpieczeństwa</a>
  </div>
</footer>
<script src="list.js?v={ASSET_VERSION}"></script>
</body>
</html>
"""

def stopka_dla(nazwa):
    slug = nazwa or "index"
    return STOPKA.replace(
        'href="opisz-projekt.html"',
        f'href="opisz-projekt.html?zrodlo={slug}-footer"',
        1,
    )

def rozdzial(klasa, tekst, obraz, extra="", ciemny=False):
    c = " ciemny" if ciemny else ""
    d = " data-ciemna" if ciemny else ""
    return f'<section class="rozdzial {klasa}{c}"{d}{extra}><div class="w"><div class="tekst wjazd">{tekst}</div><div class="obraz">{obraz}</div></div></section>\n'

KONIEC = """<section class="rozdzial koniec KONIEC_KLASA" KONIEC_ATR><div class="w"><div class="tekst wjazd">
  <h2>Co chcesz usprawnić w swojej firmie?</h2>
  <p><a data-umami-event="klik-opisz-projekt" href="opisz-projekt.html">Opisz, jak dziś wygląda ta praca</a>. Podaj używane programy, opisz problem i oczekiwany efekt. Na tej podstawie zaproponuję rozwiązanie.</p>
  <p><a href="realizacje.html">Zobacz realizacje</a> i sprawdź przykłady aplikacji. <a href="poradniki.html">Przejrzyj poradniki</a>, aby porównać rozwiązania. <a href="https://automatyzacjesklepow.pl/">Prowadzisz sklep internetowy?</a> Zobacz osobny serwis poświęcony automatyzacjom e-commerce.</p>
  <p><a data-umami-event="klik-telefon" href="tel:+48570427127">Zadzwoń: 570 427 127</a>, jeśli wolisz rozmawiać. Rozmawiasz bezpośrednio ze mną.</p>
</div></div></section>
"""

# ---------------------------------------------------------------- strona glowna
def index():
    src = ZR + "/index.html"
    if not os.path.exists(src):
        raise FileNotFoundError("Brak zrodla/index.html")
    with open(src, encoding="utf-8") as f:
        s = f.read()
    s = uzupelnij_wymiary_obrazow(s)
    s = wersjonuj_portfolio(oznacz_lazy_po_pierwszej_sekcji(s))
    s = re.sub(r'href="list\.css\?[^"]*"', f'href="list.css?v={ASSET_VERSION}"', s)
    s = re.sub(r'src="list\.js\?[^"]*"', f'src="list.js?v={ASSET_VERSION}"', s)
    with open(CEL + "/index.html", "w", encoding="utf-8") as f:
        f.write(s)

# ---------------------------------------------------------------- podstrony
SWIATY = {
  "integracja-sklepu-z-wfirma": ("jasny", stos), "integracja-sklepu-z-fakturownia": ("jasny", stos), "automatyczne-faktury-allegro": ("jasny", stos),
  "integracja-sklepu-z-ksiegowoscia": ("jasny", schody), "integracja-baselinker": ("jasny", schody),
  "automatyzacja-allegro": ("piasek", kartony), "integracja-sklepu-z-hurtownia": ("piasek", kartony),
  "integracje-shoper": ("jasny", schody), "integracje-idosell": ("piasek", kartony), "integracja-allegro-z-woocommerce": ("piasek", kartony),
  "ksef-dla-sklepu-internetowego": ("czern", dokument), "ksef-dla-jdg-terminy": ("czern", dokument),
  "wtyczka-czy-integracja": ("jasny", schody), "cennik": ("szary", paragon), "realizacje": ("czern", ksiega),
  "problemy": ("jasny", schody_firma), "sprawdzarka": ("ziel", raport),
  "dedykowane-oprogramowanie-dla-firm": ("jasny", ekrany),
  "system-zamiast-excela": ("szary", schody_firma),
  "crm-na-zamowienie": ("jasny", schody_firma),
  "system-do-wycen-i-ofert": ("jasny", schody_firma),
  "system-do-obslugi-zlecen": ("piasek", schody_firma),
  "automatyzacja-procesow-w-firmie": ("jasny", schody_firma),
  "integracje-api-dla-firm": ("jasny", schody_firma),
  "kalkulator-konfigurator-dla-klientow": ("czern", ekrany),
  "kalkulator-kosztu-recznej-pracy": ("jasny", schody_firma),
  "ile-kosztuje-aplikacja-dla-firmy": ("szary", paragon),
  "gotowy-system-czy-dedykowane-oprogramowanie": ("jasny", schody_firma),
  "aplikacje-webowe-dla-firm": ("jasny", ekrany),
  "panel-klienta-b2b": ("piasek", schody_firma),
  "system-rezerwacji-dla-firm": ("jasny", schody_firma),
  "automatyzacja-dokumentow-w-firmie": ("szary", stos),
  "ai-w-automatyzacji-firmy": ("czern", ekrany),
  "jak-przygotowac-brief-aplikacji": ("jasny", schody_firma),
  "system-dla-firmy-uslugowej": ("jasny", schody_firma),
  "system-dla-serwisu-technicznego": ("piasek", schody_firma),
  "system-dla-produkcji-na-zamowienie": ("szary", schody_firma),
  "program-dla-wypozyczalni": ("jasny", ekrany),
  "poradniki": ("jasny", ksiega),
  "opisz-projekt": ("jasny", ekrany),
  "jak-pracuje": ("jasny", droga),
  "o-mnie": ("jasny", droga),
  "polityka-prywatnosci": ("szary", schody_firma),
  "404": ("szary", schody_firma),
  "50x": ("szary", schody_firma),
}
CIEMNE = {"czern","ziel","noc"}
KSIEGA_NA_PODSTRONIE = {"realizacje"}

def podstrona(plik):
    nazwa = os.path.basename(plik)[:-5]
    # Realizacje mają własny, rozbudowany układ portfolio. Trzymamy gotowy dokument
    # jako źródło strony, żeby build nie rozbijał interaktywnych showcase'ów.
    override = os.path.join(REPO, "zrodla-final", nazwa + ".html")
    if nazwa == "realizacje" and os.path.exists(override):
        s = open(override, encoding="utf-8").read()
        s = re.sub(r'href="list\.css\?[^"]*"', f'href="list.css?v={ASSET_VERSION}"', s)
        s = re.sub(r'src="list\.js\?[^"]*"', f'src="list.js?v={ASSET_VERSION}"', s)
        s = uzupelnij_wymiary_obrazow(s)
        s = wersjonuj_portfolio(oznacz_lazy_po_pierwszej_sekcji(s))
        open(CEL + "/" + nazwa + ".html", "w", encoding="utf-8").write(s)
        return nazwa
    h = open(plik, encoding="utf-8").read()
    tytul = re.search(r"<title>(.*?)</title>", h, re.S).group(1).strip()
    opis = re.search(r'name="description" content="([^"]*)"', h).group(1)
    kanon = re.search(r'rel="canonical" href="([^"]*)"', h).group(1)
    body = h[h.find("</header>")+9 : h.find("<footer")]
    body = body.replace('<div class="pasek-gorny"></div>', '')
    # tytul strony
    m = re.search(r'<div class="tytul-strony[^"]*">(.*?)</div>\s*', body, re.S)
    tyt = m.group(1) if m else ""
    body = body.replace(m.group(0), "", 1) if m else body
    ety = re.search(r'<p class="etykieta">(.*?)</p>', tyt, re.S); ety = ety.group(1).strip() if ety else ""
    h1 = re.search(r'<h1>(.*?)</h1>', tyt, re.S); h1 = h1.group(1).strip() if h1 else nazwa
    wst = re.search(r'<p class="slaby"[^>]*>(.*?)</p>', tyt, re.S); wst = re.sub(r'\s+',' ',wst.group(1)).strip() if wst else ""
    # tresc: zdejmujemy opakowanie section/srodek
    body = re.sub(r'^\s*<section[^>]*>\s*<div class="srodek">', '', body.strip(), flags=re.S)
    body = re.sub(r'</div>\s*</section>\s*$', '', body.strip(), flags=re.S)
    # sciezki do zasobow
    # wjazd zostaje (dziala w nowym js). style inline z font-size zdejmujemy
    body = re.sub(r' style="font-size:[^"]*"', '', body)
    body = body.replace('class="tresc ', 'class="blok ').replace('class="tresc"', 'class="blok"')
    swiat, obraz = SWIATY.get(nazwa, ("jasny", schody))
    ciemny = swiat in CIEMNE
    # formularz sprawdzarki w czole zamiast w tresci
    czolo_extra = ""
    if nazwa == "sprawdzarka":
        f = re.search(r'<form class="formularz-prosty.*?</form>', body, re.S)
        if f:
            frm = f.group(0); body = body.replace(frm, "", 1)
            # dopisek wychodzi z formularza (inaczej jest trzecim elementem w wierszu i sciska pole)
            m = re.search(r'\s*<p class="slaby">.*?</p>\s*', frm, re.S)
            nota = ""
            if m: nota = '<p class="slaby nota">' + re.sub(r'\s+', ' ', re.sub(r'</?p[^>]*>', '', m.group(0))).strip() + '</p>'; frm = frm.replace(m.group(0), "")
            czolo_extra = frm + nota
    s = glowa(tytul, opis, kanon, nazwa)
    s += '<main id="main-content" tabindex="-1">\n'
    rodzic = rodzic_dla(nazwa)
    okruszki = '<nav class="okruszki" aria-label="Okruszki"><a href="/">Start</a><span aria-hidden="true">›</span>'
    if rodzic:
        okruszki += f'<a href="{rodzic[1]}">{rodzic[0]}</a><span aria-hidden="true">›</span>'
    okruszki += f'<span aria-current="page">{re.sub(r"<[^>]+>", "", h1)}</span></nav>'
    meta_artykulu = ""
    if nazwa in ARTYKULY:
        data_modyfikacji = date.fromisoformat(data_pliku(os.path.join(ZR, nazwa + ".html")))
        meta_artykulu = f'<p class="article-meta">Maciej Gryziec · aktualizacja {data_modyfikacji.strftime("%d.%m.%Y")} · <a href="o-mnie.html">o autorze</a></p>'
    tekst = okruszki + f'<p class="etykieta">{ety}</p><h1>{h1}</h1>' + (f'<p class="wstep">{wst}</p>' if wst else "") + meta_artykulu + czolo_extra
    kl = f"czolo pod {swiat} skos-dol" + (" lewo" if swiat in ("piasek","szary") else "")
    if nazwa in ("opisz-projekt","404","50x"):
        kl += " kontakt-hero"
    if nazwa in KSIEGA_NA_PODSTRONIE:
        s += f'<section id="tresc" class="rozdzial czolo pod ksiega-tlo ciemny" data-ciemna><div class="w"><div class="tekst wjazd">{tekst}</div>{obraz()}</div></section>\n'
    else:
        s += rozdzial(kl, tekst, obraz(), extra=' id="tresc"', ciemny=ciemny)
    body = re.sub(r'(<a class="przycisk"[^>]*?)href="mailto:kontakt@maciejgryziec\.pl"', r'\1href="opisz-projekt.html"', body)
    body = body.replace('data-umami-event="klik-mail" href="opisz-projekt.html"', 'data-umami-event="klik-opisz-projekt" href="opisz-projekt.html"')
    if nazwa not in ("opisz-projekt", "404", "50x"):
        body = body.replace('href="opisz-projekt.html"', f'href="opisz-projekt.html?zrodlo={nazwa}"')
    body = re.sub(r'<a class="przycisk"(?![^>]*data-umami-event)([^>]*href="opisz-projekt\.html(?:\?[^"]*)?"[^>]*)>', r'<a class="przycisk" data-umami-event="klik-opisz-projekt"\1>', body)
    body = re.sub(r'<a class="przycisk"(?![^>]*data-umami-event)([^>]*href="sprawdzarka\.html(?:\?[^"]*)?"[^>]*)>', r'<a class="przycisk" data-umami-event="klik-sprawdzarka"\1>', body)
    body = re.sub(r'<img (?![^>]*loading=)(?=[^>]*src="zdjecia/)', '<img loading="lazy" decoding="async" ', body)
    body = uzupelnij_wymiary_obrazow(body)
    if nazwa in ARTYKULY:
        body = dodaj_spis_tresci(body)
    body += blok_powiazanych(nazwa)
    s += f'<div class="tresc{" cennik-tabela" if nazwa=="cennik" else ""}">{body}</div>\n'
    if nazwa in ("404","50x"):
        s = s.replace('<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">', '<meta name="robots" content="noindex,follow">', 1)
        s += '</main>\n' + stopka_dla(nazwa)
    elif nazwa == "opisz-projekt":
        s += '</main>\n' + stopka_dla(nazwa)
    else:
        koniec = KONIEC.replace('href="opisz-projekt.html"', f'href="opisz-projekt.html?zrodlo={nazwa}-koniec"', 1)
        s += koniec + '</main>\n' + stopka_dla(nazwa)
    s = uzupelnij_wymiary_obrazow(s)
    open(CEL + "/" + nazwa + ".html", "w", encoding="utf-8").write(s)
    return nazwa

KONIEC = KONIEC.replace('KONIEC_KLASA', 'ciemny' if PALETA == 'a' else '').replace(' KONIEC_ATR', ' data-ciemna' if PALETA == 'a' else '')
open(CEL + "/list.css", "w", encoding="utf-8").write(CSS.strip() + "\n")
open(CEL + "/list.js", "w", encoding="utf-8").write(JS.strip() + "\n")
index()
zrobione = []
for plik in sorted(glob.glob(ZR + "/*.html")):
    if os.path.basename(plik) == "index.html": continue
    zrobione.append(podstrona(plik))
# A single final asset pass for all 33 pages, including error documents and service pages.
for _page in ["index.html"] + [_name + ".html" for _name in zrobione]:
    _path = os.path.join(CEL, _page)
    with open(_path, encoding="utf-8") as _f:
        _html = _f.read()
    with open(_path, "w", encoding="utf-8") as _f:
        _f.write(finalize_assets(_html))
SITEMAP_IMAGES = {
  "realizacje.html": [
    ("zdjecia/photonroof-tryby.png", "PV Roof Configurator — wybór trybu konfiguratora"),
    ("zdjecia/photonroof-mapa.jpg", "PV Roof Configurator — konfiguracja dachu na mapie satelitarnej"),
    ("zdjecia/photonroof-kreator3d.jpg", "PV Roof Configurator — kreator dachu 3D"),
    ("zdjecia/photonroof-kopertowy.jpg", "PV Roof Configurator — model dachu kopertowego"),
    ("zdjecia/photonroof-wymiary.jpg", "PV Roof Configurator — wymiary i wynik konfiguracji dachu"),
    ("zdjecia/wypozyczalnia-pulpit.png", "Panel wypożyczalni — pulpit"),
    ("zdjecia/wypozyczalnia-kalendarz.png", "Panel wypożyczalni — kalendarz obłożenia"),
    ("zdjecia/wypozyczalnia-flota.png", "Panel wypożyczalni — flota"),
    ("zdjecia/wypozyczalnia-faktury.png", "Panel wypożyczalni — faktury"),
  ],
  "kalkulator-konfigurator-dla-klientow.html": [
    ("zdjecia/photonroof-kreator3d.jpg", "Przykład konfiguratora online — PV Roof Configurator"),
    ("zdjecia/photonroof-mapa.jpg", "Przykład kalkulatora opartego na parametrach klienta"),
  ],
  "program-dla-wypozyczalni.html": [
    ("zdjecia/wypozyczalnia-pulpit.png", "Przykład programu dla wypożyczalni — pulpit"),
    ("zdjecia/wypozyczalnia-kalendarz.png", "Przykład programu dla wypożyczalni — kalendarz"),
  ],
  "system-rezerwacji-dla-firm.html": [
    ("zdjecia/wypozyczalnia-kalendarz.png", "Przykład kalendarza rezerwacji zasobów"),
  ],
}

# mapa strony jest budowana automatycznie z wszystkich stron HTML w katalogu produkcyjnym
priorytet = {
    "index.html": "1.0",
    "dedykowane-oprogramowanie-dla-firm.html": "0.9",
    "realizacje.html": "0.9",
    "cennik.html": "0.8",
    "system-zamiast-excela.html": "0.8",
    "crm-na-zamowienie.html": "0.8",
    "system-do-wycen-i-ofert.html": "0.8",
    "system-do-obslugi-zlecen.html": "0.8",
    "automatyzacja-procesow-w-firmie.html": "0.8",
    "integracje-api-dla-firm.html": "0.8",
    "kalkulator-konfigurator-dla-klientow.html": "0.8",
    "kalkulator-kosztu-recznej-pracy.html": "0.8",
    "aplikacje-webowe-dla-firm.html": "0.8",
    "panel-klienta-b2b.html": "0.8",
    "system-rezerwacji-dla-firm.html": "0.8",
    "automatyzacja-dokumentow-w-firmie.html": "0.8",
    "ai-w-automatyzacji-firmy.html": "0.7",
    "jak-przygotowac-brief-aplikacji.html": "0.7",
    "system-dla-firmy-uslugowej.html": "0.7",
    "system-dla-serwisu-technicznego.html": "0.7",
    "system-dla-produkcji-na-zamowienie.html": "0.7",
    "program-dla-wypozyczalni.html": "0.8",
    "poradniki.html": "0.9",
    "opisz-projekt.html": "0.9",
    "jak-pracuje.html": "0.8",
    "o-mnie.html": "0.7",
    "polityka-prywatnosci.html": "0.3",
}
linie = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
for pth in sorted(glob.glob(CEL + "/*.html")):
    fn = os.path.basename(pth)
    if fn in ("404.html","50x.html"):
        continue
    url = "https://maciejgryziec.pl/" if fn == "index.html" else "https://maciejgryziec.pl/" + fn
    pr = priorytet.get(fn, "0.7")
    zrodlo_daty = os.path.join(REPO, "zrodla-final", fn) if fn == "realizacje.html" else os.path.join(ZR, fn)
    if not os.path.exists(zrodlo_daty):
        zrodlo_daty = pth
    lastmod = data_pliku(zrodlo_daty)
    wpis=[f'  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod><changefreq>monthly</changefreq><priority>{pr}</priority>']
    for img_path,img_title in SITEMAP_IMAGES.get(fn,[]):
        wpis.append(f'<image:image><image:loc>https://maciejgryziec.pl/{html.escape(img_path)}</image:loc><image:title>{html.escape(img_title)}</image:title></image:image>')
    wpis.append('</url>')
    linie.append(''.join(wpis))
linie.append('</urlset>')
open(CEL + "/sitemap.xml", "w", encoding="utf-8").write(chr(10).join(linie) + chr(10))

# Atom feed dla stron poradnikowych.
artykuly_feed=[]
for nazwa in sorted(ARTYKULY):
    src_path=os.path.join(ZR,nazwa+".html")
    if not os.path.exists(src_path):
        continue
    src_txt=open(src_path,encoding="utf-8").read()
    title_m=re.search(r"<title>(.*?)</title>",src_txt,re.S)
    desc_m=re.search(r'name="description" content="([^"]*)"',src_txt)
    if not title_m or not desc_m:
        continue
    artykuly_feed.append({
        "title":re.sub(r"<[^>]+>","",title_m.group(1)).strip(),
        "desc":desc_m.group(1).strip(),
        "url":f"https://maciejgryziec.pl/{nazwa}.html",
        "published":data_publikacji(src_path),
        "modified":data_pliku(src_path),
    })
feed_updated=max((a["modified"] for a in artykuly_feed),default=date.today().isoformat())
feed=['<?xml version="1.0" encoding="UTF-8"?>','<feed xmlns="http://www.w3.org/2005/Atom">',
      '<title>Poradniki Macieja Gryźca</title>',
      '<id>https://maciejgryziec.pl/feed.xml</id>',
      '<link href="https://maciejgryziec.pl/feed.xml" rel="self"/>',
      '<link href="https://maciejgryziec.pl/poradniki.html"/>',
      f'<updated>{feed_updated}T00:00:00+02:00</updated>',
      '<author><name>Maciej Gryziec</name></author>']
for a in sorted(artykuly_feed,key=lambda x:x["modified"],reverse=True):
    feed += ['<entry>',f'<title>{html.escape(a["title"])}</title>',f'<id>{a["url"]}</id>',
             f'<link href="{a["url"]}"/>',f'<published>{a["published"]}T00:00:00+02:00</published>',
             f'<updated>{a["modified"]}T00:00:00+02:00</updated>',
             f'<summary>{html.escape(a["desc"])}</summary>','</entry>']
feed.append('</feed>')
open(CEL+"/feed.xml","w",encoding="utf-8").write(chr(10).join(feed)+chr(10))

print("index +", len(zrobione), "podstron:", ", ".join(zrobione))
