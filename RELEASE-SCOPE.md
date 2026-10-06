# Release scope — maciejgryziec.pl

Stan produkcyjny: 2026-10-06.

## Cel release’u

Serwis działa jako osobna strona sprzedażowa Macieja Gryźca dla:
- aplikacji i systemów dla firm,
- dedykowanego oprogramowania,
- integracji API,
- automatyzacji procesów,
- konfiguratorów i paneli B2B,
- realizacji i poradników.

Domena automatyzacjesklepow.pl pozostaje osobnym serwisem i nie jest przekierowywana globalnie na maciejgryziec.pl.

## Zakres funkcjonalny

- architektura informacji i nawigacja mobile,
- landingi usługowe,
- poradniki i linkowanie wewnętrzne,
- realizacje / case studies,
- formularz „Opisz projekt” z autosave i eksportem TXT,
- kwalifikator pierwszego etapu projektu,
- kalkulator kosztu ręcznej pracy,
- wyszukiwarka poradników,
- first-touch UTM + źródło wewnętrzne,
- cennik,
- polityka prywatności i security.txt,
- własne 404 / 50x,
- feed.xml / llms.txt / sitemap.xml,
- JSON-LD / canonical / Open Graph / Twitter,
- no-JS fallbacks,
- responsive WebP.

## Zakres jakości / SEO

Aktualny build:
- 33 strony HTML,
- 31 indeksowalnych URL-i w sitemap.xml,
- brak krytycznej kanibalizacji treści,
- poprawne canonical / OG / schema,
- audyt statyczny: OK,
- audyt Chrome: 0 błędów,
- audyt CSP: 33/33 stron bez naruszeń,
- asset budget: OK,
- kontrast WCAG AA: OK,
- build idempotentny,
- release-check: OK.

## Infrastruktura

- repo: maciejgryziec/maciejgryziec-strona,
- branch: main,
- hosting: Coolify na VPS,
- bez Vercela,
- aplikacja Coolify: mdd5pqas5vvybdfdgurcb7zq,
- produkcyjny adres IPv4: 54.37.234.39,
- build strategy: Static,
- healthcheck: /healthz,
- nginx: własna konfiguracja zsynchronizowana z deploy/nginx.conf.

Produkcja ma:
- www → apex,
- HTTP → HTTPS,
- HSTS,
- CSP,
- nosniff,
- Referrer-Policy,
- Permissions-Policy,
- gzip,
- cache statycznych assetów,
- blokady plików źródłowych i repo,
- custom 404/50x.

## DNS / TLS

- A @ → 54.37.234.39,
- A www → 54.37.234.39,
- rekordy widoczne w DNS OVH, Cloudflare i Google,
- osobne certyfikaty Let’s Encrypt dla apex i www,
- poczta OVH pozostawiona bez zmian.

## Google Search Console

- własność domenowa maciejgryziec.pl zweryfikowana przez TXT DNS,
- strona główna jest w indeksie Google,
- wysłano ponowną prośbę o indeksowanie strony głównej,
- ręcznie zgłoszono do indeksowania kluczowe nowe URL-e:
  - dedykowane-oprogramowanie-dla-firm.html,
  - realizacje.html,
  - cennik.html,
  - opisz-projekt.html,
- sitemap.xml została zgłoszona,
- po propagacji DNS Google odczytało sitemapę poprawnie: status Sukces,
- Search Console wykrywa 31 stron z mapy witryny.

## Umami

Dla maciejgryziec.pl działa osobna witryna w self-hosted Umami.

- nazwa: Maciej Gryziec,
- domena: maciejgryziec.pl,
- website ID: 7bf89ecf-f690-413f-863a-658c0a0f4baa,
- stara witryna Automatyzacje Sklepów pozostaje osobna,
- tracker ładuje się warunkowo z list.js,
- użytkownik może wyłączyć analitykę lokalnie,
- polityka prywatności opisuje self-hosted Umami,
- produkcyjny CSP dopuszcza serwer Umami w script-src i connect-src,
- test live potwierdził żądania do script.js i /api/send.

## Produkcja

Wdrożony release funkcjonalny:
- commit 8063e7d — Enable dedicated Umami analytics for maciejgryziec.pl.

Po wdrożeniu:
- pełny narzedzia/sprawdz-live.py → PRODUKCJA OK,
- healthz → 200,
- wszystkie wymagane pliki techniczne → 200,
- prywatne źródła/repo/docs → 404,
- www redirect → 301,
- tracker Umami → działa z osobnym website ID,
- CSP live → poprawny.

## Co dalej

1. Nie zmieniać już infrastruktury maciejgryziec.pl bez konkretnej potrzeby.
2. Search Console: sitemap jest już zielona; dalej obserwować raport Strony i indeksację ręcznie zgłoszonych URL-i.
3. Po 2–4 tygodniach przeanalizować:
   - zapytania,
   - CTR,
   - strony z wyświetleniami,
   - dane Umami.
4. Dopiero na podstawie danych rozwijać SEO i landing pages.
5. LinkedIn pozostaje poza zakresem obecnych prac zgodnie z decyzją z 2026-10-06.
