# Checklist produkcyjny — automatyzacjesklepow.pl

Stan audytu: 2026-10-03.

## 1. Kod i build — gotowe lokalnie

- [x] generator jest przenośny i nie używa ścieżki konkretnego Maca,
- [x] build jest idempotentny,
- [x] 46 stron HTML; sitemap zawiera 44 indeksowane URL-e (404/50x wykluczone),
- [x] statyczny audyt przechodzi,
- [x] lokalny audyt Chrome przechodzi (0 błędów),
- [x] zewnętrzne linki urzędowe przechodzą audyt,
- [x] mobile bez horizontal overflow,
- [x] 404 i 50x mają `noindex`,
- [x] sitemap wyklucza strony błędów,
- [x] Open Graph / Twitter / JSON-LD / breadcrumbs,
- [x] responsive WebP + fallback JPG/PNG,
- [x] hashowane URL-e CSS/JS,
- [x] Atom feed i llms.txt,
- [x] automatyczne spisy treści dla długich poradników,
- [x] kalkulator kosztu ręcznej pracy + test matematyczny w Chrome,
- [x] kwalifikator pierwszego etapu projektu,
- [x] formularz briefu: mailto, kopiowanie, TXT, autosave w sessionStorage,
- [x] fallbacki bez JavaScriptu dla briefu, kalkulatora, kwalifikatora i poradników,
- [x] first-touch UTM + źródło wewnętrzne zachowywane do briefu,
- [x] polityka prywatności opisuje formularz, UTM i statystyki bez treści pól,
- [x] `.dockerignore` blokuje publikację `zrodla/`, `narzedzia/`, `deploy/` i repo metadata,
- [x] GitHub Actions odpala build + statyczny audyt i pilnuje wygenerowanych plików,
- [x] `deploy/nginx.conf` jest zsynchronizowany z README,
- [x] finalna konfiguracja nginx przeszła `nginx -t` w aktualnym obrazie nginx z Coolify.
- [x] symulacja release’u w tymczasowym klonie: artefakty przed i po commicie są identyczne.

## 2. Obecna produkcja — poprawić przy deployu

Obecny live nadal działa na starej wersji.

- [ ] sprawdzarka: `./narzedzia/release-check.sh` → 160 testów zielonych,
- [ ] sprawdzarka: commit/push/deploy wersji z retencją 30 dni, cleanupem, limitami kolejki/odpowiedzi i CSP,
- [ ] sprawdzarka: `HEAD /` → 200 oraz `/healthz` → `{"status":"ok"}`,
- [ ] sprawdzarka: potwierdzić na live komunikat „automatycznie usuwane po 30 dniach”,
- [ ] sprawdzarka: potwierdzić na live brak pola e-mail (raport jest dostępny przez niepubliczny link),
- [ ] sprawdzarka: potwierdzić natywny Ceneo XML + Google Merchant RSS oraz healthcheck,
- [ ] sprawdzarka: potwierdzić security.txt, CSP/HSTS i Swagger/OpenAPI → 404,
- [ ] dopiero potem lub w tym samym release: commit zmian strony głównej,
- [ ] push strony do `main`,
- [ ] pełny redeploy aplikacji Static w Coolify,
- [ ] Coolify healthcheck strony ustawić na `/healthz`,
- [ ] sprawdzić, czy `.dockerignore` został użyty podczas builda,
- [ ] `/zrodla/index.html` musi zwracać 404,
- [ ] `/narzedzia/buduj-nowa.py` musi zwracać 404,
- [ ] `/.well-known/security.txt` musi zwracać 200,
- [ ] `/og-image.png` musi zwracać 200,
- [ ] `/feed.xml` i `/llms.txt` muszą zwracać 200.

Po deployu:

```bash
python3 narzedzia/sprawdz-live.py
```

## 3. Nginx / Coolify — do wdrożenia razem z release

Obecnie:
- `http://` → `https://` działa,
- `www` NIE przekierowuje na apex,
- brak HSTS,
- brak `X-Content-Type-Options`,
- brak `Referrer-Policy`,
- brak `Permissions-Policy`.

Do zrobienia:
- [ ] wkleić przygotowaną konfigurację nginx z README do Coolify,
- [ ] `www.automatyzacjesklepow.pl/*` → 301 do `https://maciejgryziec.pl/*`,
- [ ] HSTS,
- [ ] nosniff,
- [ ] Referrer-Policy,
- [ ] Permissions-Policy,
- [ ] Content-Security-Policy,
- [ ] gzip dla zasobów tekstowych,
- [ ] cache statycznych assetów (CSS/JS immutable dzięki hashom),
- [ ] blokady źródeł/dotfiles także na poziomie nginx,
- [ ] 301 `index.html → /` i extensionless → kanoniczne `.html`,
- [ ] własne 404 i 50x.

## 4. TLS — stan dobry

- [x] apex: Let’s Encrypt,
- [x] www: Let’s Encrypt,
- [x] TLS 1.1 odrzucony,
- [x] TLS 1.2 działa,
- [x] TLS 1.3 działa.

Certyfikaty podczas audytu były ważne do 23.11.2026. Coolify/Let’s Encrypt powinien je odnawiać automatycznie — warto potwierdzić po kolejnym renewalu.

## 5. DNS / e-mail — nie zmieniać automatycznie

Obecny stan:
- [x] MX: OVH Mail,
- [x] SPF: `v=spf1 include:mx.ovh.com ~all`,
- [x] DMARC istnieje,
- [ ] DMARC ma `p=none` — tylko monitoring,
- [ ] DKIM nie został potwierdzony w tym audycie,
- [x] Google Search Console verification TXT istnieje,
- [ ] CAA brak — opcjonalne.

Przed zmianą DMARC/SPF:
1. potwierdzić w OVH, że DKIM jest aktywny dla domeny,
2. sprawdzić, czy z domeny wysyła tylko OVH czy także inne systemy,
3. sprawdzić raporty DMARC,
4. dopiero później rozważyć `p=quarantine`, a następnie `p=reject`,
5. `~all` → `-all` dopiero po potwierdzeniu wszystkich legalnych nadawców.

Nie zmieniać tych rekordów „dla lepszego wyniku” bez powyższej weryfikacji — można przypadkiem pogorszyć dostarczalność poczty.

## 6. Google po deployu

Domena ma już rekord `google-site-verification`, więc Search Console była co najmniej przygotowana / zweryfikowana DNS-em.

Po deployu:
- [ ] otworzyć Search Console,
- [ ] zgłosić / ponownie przesłać `https://maciejgryziec.pl/sitemap.xml`,
- [ ] sprawdzić indeksowanie nowych głównych URL-i,
- [ ] po 2–4 tygodniach sprawdzić zapytania, CTR i strony z wyświetleniami,
- [ ] nie oceniać SEO po 1–2 dniach.

## 7. Dane firmy / prawne — potrzebne dane właściciela

Nie wpisywałem danych, których nie mam lub nie mogę potwierdzić.

Przed traktowaniem strony jako finalnej strony działalności należy potwierdzić, czy trzeba pokazać m.in.:
- [ ] pełną nazwę podmiotu / firmy,
- [ ] adres działalności / dane rejestrowe,
- [ ] NIP / KRS — jeśli dotyczą,
- [ ] dane administratora danych w polityce prywatności,
- [ ] potwierdzić, że komunikat „ceny netto” używany na homepage i w cenniku jest właściwy dla sposobu rozliczania,
- [ ] zasady ofertowania / ewentualny regulamin, jeśli zacznie się sprzedaż usług bezpośrednio przez stronę.

Tych informacji nie wolno zgadywać.

## 8. LinkedIn — następny etap

Po poprawnym deployu i zielonym `sprawdz-live.py`:
- [ ] zaktualizować link w profilu LinkedIn,
- [ ] przygotować serię postów opartych o PV Roof Configurator, panel wypożyczalni i budowę własnego systemu,
- [ ] linkować posty do konkretnych landingów, nie zawsze do homepage,
- [ ] używać UTM, np. `?utm_source=linkedin&utm_medium=social&utm_campaign=case_photonroof`,
- [ ] porównywać w Umami wejścia → kwalifikator → brief-start → CTA.

## Dane formalne do potwierdzenia przed publikacją

- [ ] potwierdzić, czy administratorem/usługodawcą ma być publicznie `Maciej Gryziec`, czy pełna zarejestrowana nazwa działalności; jeśli działalność ma obowiązkowe dane identyfikacyjne, uzupełnić je w polityce/footerze bez zgadywania,
- [ ] po stabilnym deployu strony wykonać osobny Etap L z `DEPLOY-PLAN.md` dla Umami; nie łączyć upgrade'u analityki z tym samym wdrożeniem.
