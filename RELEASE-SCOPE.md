# Release scope — główna strona

Ten release jest jednym spójnym przebudowaniem serwisu z pozycji „automatyzacje sklepów” w stronę sprzedażową **aplikacji, systemów, integracji i automatyzacji dla firm**, z zachowaniem klastra e-commerce.

## Zakres funkcjonalny

- nowa architektura informacji i nawigacja mobile,
- rozbudowane landingi usługowe,
- poradniki i automatyczny spis treści,
- case studies PV Roof Configurator i panelu wypożyczalni,
- formularz „Opisz projekt” z autosave/TXT,
- kwalifikator pierwszego etapu,
- kalkulator kosztu ręcznej pracy,
- wyszukiwarka poradników,
- first-touch UTM + źródło wewnętrzne,
- spójny cennik,
- „Co dalej?” / linkowanie wewnętrzne,
- hub e-commerce,
- polityka prywatności i security.txt,
- własne 404 / 50x,
- feed.xml / llms.txt / sitemap + image sitemap,
- per-page social previews,
- JSON-LD / Service / Person / WebApplication / ItemList,
- no-JS fallbacks,
- print/PDF cennika,
- responsive WebP.

## Zakres jakości / SEO

- 46 wygenerowanych stron HTML,
- 44 indeksowane URL-e w sitemapie,
- 14 obrazów w image sitemap,
- brak stron-sierot,
- maks. 3 kliknięcia od homepage,
- audyt kanibalizacji treści,
- audyt canonical / OG / schema,
- pełny Chrome runtime crawl wszystkich stron,
- budżet assetów w CI + lokalny performance gate,
- performance gate: cold 4G + 4×CPU, LCP ≤ 3,2 s, CLS ≤ 0,10, transfer ≤ 200 KB,
- Accessibility Tree wszystkich stron,
- external link audit,
- cache-busting CSS/JS po hashach.

## Zakres infrastruktury

- GitHub Actions build + audyt,
- `.dockerignore`,
- gotowy `deploy/nginx.conf`,
- CSP/HSTS/nosniff/Referrer-Policy/Permissions-Policy,
- gzip/cache,
- blokady plików źródłowych/dotfiles,
- `www → apex`,
- `index.html → /`,
- canonical redirect extensionless → `.html`,
- `/healthz`,
- custom 404/50x,
- smoke test produkcji.

## Pliki źródłowe i wygenerowane

Serwis celowo trzyma:
- źródła pod `zrodla/*.html`,
- generator `narzedzia/buduj-nowa.py`,
- **wygenerowane** HTML/CSS/JS/sitemap/feed w root repo.

Po zmianie źródeł uruchom:
`python3 narzedzia/buduj-nowa.py`

Wygenerowane artefakty muszą być commitowane razem ze źródłami. CI zatrzyma release, jeżeli build po checkout zmieni pliki.

## Pliki, których nie wolno commitować przypadkiem

- `_audit*`,
- lokalne `*.db`, `*.sqlite`,
- backupy `*.bak`, `*.old`,
- tymczasowe logi i screenshoty audytowe,
- pliki z sekretami / lokalnymi ścieżkami.

## Przed stagingiem

```bash
./narzedzia/release-check.sh
python3 narzedzia/audyt-chrome.py
python3 narzedzia/audyt-csp.py
python3 narzedzia/audyt-runtime.py
python3 narzedzia/audyt-performance.py
python3 narzedzia/audyt-linkow-zewnetrznych.py
./narzedzia/review-release.sh
```

Dopiero potem:
- `git add -A`,
- `git diff --cached --check`,
- przegląd `git status`,
- commit/push zgodnie z `DEPLOY-PLAN.md`.
