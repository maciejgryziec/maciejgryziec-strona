/* ═══════════════════════════════════════════════════════════════
   RUCH — chwyty z „drogich" stron, do wklejenia w dowolny projekt.

   Nic nie trzeba wywoływać z kodu. Wystarczy dopisać atrybut w HTML:

     <div data-ruch="wjazd">              wjeżdża, gdy wchodzi w kadr
     <img data-ruch="parallaks" data-sila="0.3">
     <section data-ruch="przypiete">      przypina ekran i liczy postęp
     <div  data-ruch="sekwencja" data-klatki="klatki/k#.jpg" data-ile="36">
     <span data-ruch="licznik" data-do="1284358">
     <section data-ruch="poziomo">        przewijanie w dół jedzie w bok
     <div data-ruch="przenikanie">        dzieci przenikają jedno w drugie
     <div data-ruch="odsloniecie">        odsłania się jak zasłona

   NAJWAŻNIEJSZE: sekcja z data-ruch="przypiete" ustawia na sobie
   zmienną CSS --postep (0…1). Można nią sterować DOWOLNĄ własnością
   w arkuszu stylów, bez pisania choćby linijki kodu:

     .cos { transform: scale(calc(1 + var(--postep) * 0.4)) }
   ═══════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  var spokoj = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function lista(s, w) { return [].slice.call((w || document).querySelectorAll(s)); }
  function ogranicz(x, a, b) { return x < a ? a : (x > b ? b : x); }

  /* postęp przewijania wewnątrz sekcji przypiętej: 0 na wejściu, 1 na wyjściu */
  function postepSekcji(sekcja) {
    var pole = sekcja.getBoundingClientRect();
    var droga = sekcja.offsetHeight - window.innerHeight;
    if (droga <= 0) return pole.top <= 0 ? 1 : 0;
    return ogranicz(-pole.top / droga, 0, 1);
  }

  var zadania = [];          /* rzeczy odświeżane przy każdym przewinięciu */

  /* ── 1. WJAZD ─────────────────────────────────────────────── */
  var doWjazdu = lista('[data-ruch="wjazd"], [data-ruch="odsloniecie"]');
  if (doWjazdu.length) {
    if (spokoj || !("IntersectionObserver" in window)) {
      doWjazdu.forEach(function (e) { e.classList.add("widac"); });
    } else {
      doWjazdu.forEach(function (e) { e.classList.add("ruch-czeka"); });
      var oko = new IntersectionObserver(function (wpisy) {
        wpisy.forEach(function (w) {
          if (!w.isIntersecting) return;
          w.target.classList.add("widac");
          oko.unobserve(w.target);
        });
      }, { rootMargin: "0px 0px -12% 0px" });
      doWjazdu.forEach(function (e) { oko.observe(e); });
    }
  }

  /* ── 2. PARALLAKS ─────────────────────────────────────────── */
  lista('[data-ruch="parallaks"]').forEach(function (e) {
    if (spokoj) return;
    var sila = parseFloat(e.dataset.sila || "0.25");
    e.style.willChange = "transform";
    zadania.push(function () {
      var pole = e.getBoundingClientRect();
      var srodek = pole.top + pole.height / 2 - window.innerHeight / 2;
      e.style.transform = "translate3d(0," + (-srodek * sila).toFixed(1) + "px,0)";
    });
  });

  /* ── 3. SEKCJA PRZYPIĘTA + zmienna --postep ───────────────── */
  lista('[data-ruch="przypiete"]').forEach(function (sekcja) {
    zadania.push(function () {
      sekcja.style.setProperty("--postep", postepSekcji(sekcja).toFixed(4));
    });
  });

  /* ── 4. SEKWENCJA OBRAZKÓW ────────────────────────────────
     Serce metody z filmiku: obiekt „w 3D", który wcale nie jest
     liczony na żywo — to gotowe klatki przewijane kółkiem myszy. */
  lista('[data-ruch="sekwencja"]').forEach(function (pojemnik) {
    var wzor = pojemnik.dataset.klatki;
    var ile = parseInt(pojemnik.dataset.ile, 10) || 0;
    var cyfry = parseInt(pojemnik.dataset.cyfry || "2", 10);
    /* zawrzyj = cała klatka widoczna (bezpieczne przy pionowych klatkach)
       wypelnij = klatka wypełnia kadr, brzegi obcięte */
    var wypelnij = pojemnik.dataset.dopasowanie === "wypelnij";
    if (!wzor || !ile) return;

    var plotno = pojemnik.querySelector("canvas") || pojemnik.appendChild(
      document.createElement("canvas"));
    var pedzel = plotno.getContext("2d");
    var obrazki = [], zaladowane = 0, ostatnia = -1;

    for (var i = 0; i < ile; i++) {
      var nr = String(i);
      while (nr.length < cyfry) nr = "0" + nr;
      var o = new Image();
      o.src = wzor.replace("#", nr);
      o.onload = function () { zaladowane++; if (zaladowane === 1) rysuj(0); };
      obrazki.push(o);
    }

    function dopasuj() {
      var r = window.devicePixelRatio || 1;
      plotno.width = Math.round(pojemnik.clientWidth * r);
      plotno.height = Math.round(pojemnik.clientHeight * r);
      ostatnia = -1;
    }

    function rysuj(nr) {
      var o = obrazki[nr];
      if (!o || !o.complete || !o.naturalWidth) return;
      var pw = plotno.width, ph = plotno.height;
      var skala = wypelnij
        ? Math.max(pw / o.naturalWidth, ph / o.naturalHeight)
        : Math.min(pw / o.naturalWidth, ph / o.naturalHeight);
      var w = o.naturalWidth * skala, h = o.naturalHeight * skala;
      pedzel.clearRect(0, 0, pw, ph);
      pedzel.drawImage(o, (pw - w) / 2, (ph - h) / 2, w, h);
    }

    dopasuj();
    window.addEventListener("resize", dopasuj);

    var sekcja = pojemnik.closest('[data-ruch="przypiete"]') || pojemnik;
    zadania.push(function () {
      var nr = Math.min(ile - 1, Math.floor(postepSekcji(sekcja) * ile));
      if (nr === ostatnia) return;
      ostatnia = nr;
      rysuj(nr);
    });
  });

  /* ── 5. LICZNIK ───────────────────────────────────────────── */
  lista('[data-ruch="licznik"]').forEach(function (e) {
    var cel = parseFloat(e.dataset.do || "0");
    function policz() {
      if (spokoj) { e.textContent = cel.toLocaleString("pl-PL"); return; }
      var start = null, czas = parseInt(e.dataset.czas || "1600", 10);
      (function krok(teraz) {
        if (start === null) start = teraz;
        var p = ogranicz((teraz - start) / czas, 0, 1);
        e.textContent = Math.round(cel * (1 - Math.pow(1 - p, 3))).toLocaleString("pl-PL");
        if (p < 1) requestAnimationFrame(krok);
      })(performance.now());
    }
    if (!("IntersectionObserver" in window)) return policz();
    var oko = new IntersectionObserver(function (w) {
      if (!w[0].isIntersecting) return;
      policz(); oko.disconnect();
    }, { threshold: 0.6 });
    oko.observe(e);
  });

  /* ── 6. PRZEWIJANIE W BOK ─────────────────────────────────── */
  lista('[data-ruch="poziomo"]').forEach(function (sekcja) {
    var tor = sekcja.querySelector(".ruch-tor");
    if (!tor) return;
    tor.style.willChange = "transform";
    zadania.push(function () {
      if (window.innerWidth < 700) { tor.style.transform = ""; return; }
      var droga = tor.scrollWidth - window.innerWidth + 48;
      tor.style.transform = "translate3d(" + (-postepSekcji(sekcja) * droga) + "px,0,0)";
    });
  });

  /* ── 7. PRZENIKANIE ───────────────────────────────────────── */
  lista('[data-ruch="przenikanie"]').forEach(function (pojemnik) {
    var dzieci = [].slice.call(pojemnik.children);
    if (dzieci.length < 2) return;
    var sekcja = pojemnik.closest('[data-ruch="przypiete"]') || pojemnik;
    zadania.push(function () {
      var poz = postepSekcji(sekcja) * (dzieci.length - 1);
      dzieci.forEach(function (d, i) {
        d.style.opacity = ogranicz(1 - Math.abs(poz - i), 0, 1);
      });
    });
  });

  /* ── wspólna pętla ────────────────────────────────────────── */
  var czeka = false;
  function odswiez() {
    if (czeka) return;
    czeka = true;
    requestAnimationFrame(function () {
      for (var i = 0; i < zadania.length; i++) zadania[i]();
      czeka = false;
    });
  }
  window.addEventListener("scroll", odswiez, { passive: true });
  window.addEventListener("resize", odswiez);
  window.addEventListener("load", odswiez);
  odswiez();
})();
