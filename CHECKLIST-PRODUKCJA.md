# Checklist produkcyjny — maciejgryziec.pl

Stan po migracji: 2026-10-06.

## 0. Granice projektu — ważne

- [x] Produkcyjna strona maciejgryziec.pl działa jako osobna aplikacja Static w Coolify.
- [x] Źródło: maciejgryziec/maciejgryziec-strona, branch main.
- [x] Produkcyjny VPS: 54.37.234.39.
- [x] automatyzacjesklepow.pl jest osobnym serwisem/projektem i nie wolno przekierowywać całej domeny na maciejgryziec.pl.
- [x] Nie zmieniać konfiguracji aplikacji automatyzacjesklepow.pl przy pracach nad maciejgryziec.pl.
- [x] Nie używać Vercela dla tego wdrożenia.

## 1. Kod i build

- [x] generator jest przenośny i nie używa ścieżki konkretnego Maca,
- [x] build jest idempotentny,
- [x] audyt statyczny przechodzi,
- [x] 33 strony HTML; sitemap zawiera 31 indeksowalnych URL-i,
- [x] 404 i 50x mają noindex,
- [x] sitemap wyklucza strony błędów,
- [x] Open Graph / Twitter / JSON-LD / breadcrumbs,
- [x] responsive WebP + fallback JPG/PNG,
- [x] hashowane URL-e CSS/JS,
- [x] Atom feed i llms.txt,
- [x] formularz briefu, kwalifikator i kalkulator działają z fallbackami bez JS,
- [x] first-touch UTM i źródło wewnętrzne są zachowywane do briefu,
- [x] .dockerignore blokuje publikację zrodla/, narzedzia/, deploy/ i metadanych repo,
- [x] GitHub Actions pilnuje builda i audytu,
- [x] deploy/nginx.conf jest używany jako finalna konfiguracja nginx.

## 2. Produkcja maciejgryziec.pl

Ostatni wdrożony commit: c980bfc — Align live smoke test with disabled Umami.

- [x] pełny deploy Static w Coolify zakończony sukcesem,
- [x] healthcheck Coolify: GET http://localhost:80/healthz,
- [x] pierwszy healthcheck nowego kontenera: healthy,
- [x] https://maciejgryziec.pl/ → 200,
- [x] https://www.maciejgryziec.pl/* → 301 do apex,
- [x] http:// → HTTPS,
- [x] /healthz → 200 ok,
- [x] /.well-known/security.txt → 200,
- [x] /og-image.png → 200,
- [x] /feed.xml, /llms.txt, /site.webmanifest, /sitemap.xml → 200,
- [x] /zrodla/index.html → 404,
- [x] /narzedzia/buduj-nowa.py → 404,
- [x] pliki repo/deploy/docs są niedostępne publicznie,
- [x] własna strona 404 zachowuje HTTP 404,
- [x] python3 narzedzia/sprawdz-live.py — produkcja OK.

## 3. Nginx / bezpieczeństwo / cache

- [x] HSTS,
- [x] X-Content-Type-Options: nosniff,
- [x] X-Frame-Options: DENY,
- [x] Cross-Origin-Opener-Policy: same-origin,
- [x] Referrer-Policy: strict-origin-when-cross-origin,
- [x] Permissions-Policy,
- [x] Content-Security-Policy,
- [x] script-src bez unsafe-inline,
- [x] gzip dla HTML/CSS/JS,
- [x] długi cache CSS/JS,
- [x] cache obrazów,
- [x] HTML rewalidowany przez no-cache,
- [x] ETag,
- [x] blokady źródeł/dotfiles na poziomie nginx,
- [x] index.html → /,
- [x] extensionless → kanoniczne .html,
- [x] własne 404/50x.

## 4. TLS

Zweryfikowano 2026-10-06:

- [x] osobny certyfikat Let’s Encrypt dla maciejgryziec.pl,
- [x] osobny certyfikat Let’s Encrypt dla www.maciejgryziec.pl,
- [x] oba hosty przechodzą poprawny handshake TLS,
- [x] certyfikaty ważne do 2027-01-04,
- [x] www po TLS przekierowuje do apex.

## 5. DNS / e-mail

Zweryfikowano po migracji:

- [x] A @ → 54.37.234.39,
- [x] A www → 54.37.234.39,
- [x] rekordy są widoczne na autorytatywnym DNS OVH, Cloudflare DNS i Google DNS,
- [x] MX OVH pozostawione bez zmian,
- [x] SPF pozostawiony bez zmian: v=spf1 include:mx.ovh.com -all,
- [x] dodany TXT Google Search Console,
- [ ] DKIM/DMARC — nie zmieniać bez osobnego audytu poczty,
- [ ] CAA — opcjonalne; nie jest blokadą.

## 6. Google Search Console / indeksowanie

Własność domenowa maciejgryziec.pl została zweryfikowana rekordem DNS TXT.

- [x] Search Console — własność domeny zweryfikowana,
- [x] https://maciejgryziec.pl/sitemap.xml zgłoszona,
- [x] strona główna jest już w indeksie Google,
- [x] dla strony głównej wysłano ponowną prośbę o indeksowanie po migracji,
- [x] wysłano priorytetowe prośby o indeksowanie:
  - dedykowane-oprogramowanie-dla-firm.html,
  - realizacje.html,
  - cennik.html,
  - opisz-projekt.html.
- [ ] sitemap: Search Console przy pierwszym odczycie pokazało Nie udało się pobrać; sam plik ma HTTP 200, poprawny XML, 31 URL-i i jest wskazany w robots.txt. Najbardziej prawdopodobny powód: pierwszy fetch odbył się podczas propagacji DNS. Nie zmieniać poprawnego pliku — sprawdzić status ponownie po odświeżeniu cache Google.
- [ ] po 1–2 dniach sprawdzić ponownie status sitemap i raport Strony,
- [ ] po 2–4 tygodniach sprawdzić zapytania, CTR i strony z wyświetleniami,
- [ ] nie oceniać SEO po 1–2 dniach od migracji.

## 7. Analityka Umami

- [x] tracker Umami jest celowo wyłączony na maciejgryziec.pl,
- [x] nowa domena nie dziedziczy website ID starego serwisu,
- [x] CSP nie dopuszcza zewnętrznego skryptu Umami,
- [x] sprawdz-live.py jest zsynchronizowany z tą decyzją.
- [ ] osobny etap: utworzyć oddzielną witrynę / website ID w self-hosted Umami i dopiero wtedy świadomie włączyć tracker oraz zaktualizować politykę/CSP.

## 8. Dane firmy / prawne — wymagają potwierdzenia właściciela

Nie zgadywać danych formalnych.

Do decyzji przed traktowaniem strony jako finalnej strony działalności:
- [ ] pełna nazwa podmiotu / firmy,
- [ ] adres działalności / dane rejestrowe,
- [ ] NIP / KRS — jeśli dotyczą,
- [ ] dane administratora danych w polityce prywatności,
- [ ] potwierdzenie, czy komunikat ceny netto jest właściwy dla sposobu rozliczania,
- [ ] zasady ofertowania / ewentualny regulamin, jeśli rozpocznie się sprzedaż usług bezpośrednio przez stronę.

## 9. LinkedIn — kolejny osobny etap

Nie mieszać z migracją domeny. Po stabilizacji indeksowania:
- [ ] zaktualizować link w profilu LinkedIn,
- [ ] uruchomić serię postów opartych o realizacje,
- [ ] linkować do konkretnych landingów,
- [ ] używać UTM,
- [ ] po uruchomieniu osobnej analityki porównywać wejścia → kwalifikator → brief-start → CTA.
