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
      excel:["Pierwszy moduł aplikacji","od 2 900 zł","Zacząłbym od jednego procesu i wspólnej bazy zamiast przenoszenia całego Excela 1:1.","System zamiast Excela"],
      przepisywanie:["Integracja systemów","od 2 900 zł","Najpierw sprawdziłbym API obu programów i ustalił jedno źródło prawdy dla danych.","Integracja kilku programów / API"],
      sprzedaz:["Pierwszy moduł CRM","od 2 900 zł","Warto zacząć od klientów, szans i jednego realnego etapu sprzedaży.","CRM lub obsługa sprzedaży"],
      wyceny:["Pierwszy moduł wycen i ofert","od 2 900 zł","Zacząłbym od jednego sposobu kalkulacji, kontroli marży i jednego szablonu oferty PDF.","System do wycen i ofert"],
      zlecenia:["Pierwszy moduł obsługi zleceń","od 2 900 zł","Lista spraw, karta zlecenia i statusy zwykle wystarczą na pierwszy etap.","System do obsługi zleceń"],
      rezerwacje:["Pierwszy moduł rezerwacji","od 2 900 zł","Najpierw trzeba opisać zasoby i reguły, które decydują o dostępności.","System rezerwacji"],
      dokumenty:["Automatyzacja dokumentu","od 2 900 zł","Najlepszym wejściem jest jeden prawdziwy wzór dokumentu i źródło jego danych.","Automatyzacja dokumentów"],
      klient:["Panel klienta / B2B","od 2 900 zł","Najpierw wybieramy jedną informację lub czynność, którą klient ma obsłużyć sam.","Panel klienta B2B"],
      ai:["Wstępny plan + punktowe AI","0 zł na start","Najpierw oddzieliłbym zwykłe reguły od kroku, który naprawdę wymaga interpretacji.","Automatyzacja z AI"]
    };
    function render(track){var m=map[problem.value];if(!m){wynik.hidden=true;return;}if(track)siteTrack("kwalifikator-wynik",{problem:problem.value,stan:stan.value});var dopisek=stan.value==="niejasny"?" Przy niejasnym procesie zacząłbym od bezpłatnego wstępnego planu.":"";var href="opisz-projekt.html?typ="+encodeURIComponent(m[3])+"&zrodlo=kwalifikator";wynik.innerHTML='<h3>'+m[0]+'</h3><p><strong>Punkt startowy: '+m[1]+'</strong></p><p>'+m[2]+dopisek+'</p><p class="slaby">To nie jest automatyczna wycena całego projektu — wynik wskazuje najbardziej prawdopodobny pierwszy etap na podstawie obecnego cennika.</p><a class="przycisk" data-umami-event="kwalifikator-opisz-projekt" href="'+href+'">Opisz ten projekt →</a>';wynik.hidden=false;}
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
      info.textContent="Przeglądarka nie pozwoliła skopiować automatycznie. Gotowy brief jest zaznaczony poniżej — skopiuj go ręcznie i wyślij na kontakt@automatyzacjesklepow.pl.";
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
        "Firma: "+(value(fd,"firma")||"—"),
        "E-mail: "+value(fd,"email"),
        "Telefon: "+(value(fd,"telefon")||"—"),
        "Typ projektu: "+value(fd,"typ"),"",
        "JAK WYGLĄDA TO DZISIAJ","----------------------",value(fd,"dzis"),"",
        "NAJWIĘKSZY PROBLEM","-----------------",value(fd,"problem"),"",
        "Obecne narzędzia: "+(value(fd,"narzedzia")||"—"),
        "Liczba użytkowników: "+value(fd,"uzytkownicy"),
        "Orientacyjny budżet: "+(value(fd,"budzet")||"—"),"",
        "EFEKT PIERWSZEGO ETAPU","----------------------",value(fd,"efekt")||"—","",
        "Strona, z której trafiłem do formularza: "+ref,
        "Źródło / kampania: "+(source||"—")
      ].join("\n");
    }

    form.addEventListener("submit",async function(e){
      e.preventDefault();
      if(!form.reportValidity())return;
      var fd=new FormData(form);
      var subject="Zapytanie o projekt — "+(fd.get("typ")||"aplikacja dla firmy");
      var message=brief();
      var copied=false;
      try{await navigator.clipboard.writeText(message);copied=true;}catch(err){}
      var mailBody=message;
      if(message.length>3500&&copied){
        mailBody="Dzień dobry,\n\nprzygotowałem pełny brief projektu w formularzu na stronie. Został skopiowany do schowka — wkleję go poniżej tej wiadomości.\n\nPozdrawiam";
        info.textContent="Pełny brief został skopiowany. Po otwarciu wiadomości wklej go pod przygotowanym tekstem.";
      }else if(message.length>3500&&!copied){
        showFallback(message);return;
      }else{
        info.textContent=copied?"Brief został też skopiowany do schowka jako kopia zapasowa.":"Otwieram program pocztowy z przygotowanym briefem.";
      }
      siteTrack("brief-mailto-ready",{typ:value(fd,"typ")});
      location.href="mailto:kontakt@automatyzacjesklepow.pl?subject="+encodeURIComponent(subject)+"&body="+encodeURIComponent(mailBody);
    });

    if(copy)copy.addEventListener("click",async function(){
      if(!form.reportValidity())return;
      var message=brief();
      try{
        await navigator.clipboard.writeText(message);
        fallback.hidden=true;
        info.textContent="Brief skopiowany. Wklej go do wiadomości na kontakt@automatyzacjesklepow.pl.";
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
      info.textContent="Brief zapisany jako plik TXT.";
    });

    if(clear)clear.addEventListener("click",function(){
      if(!confirm("Wyczyścić cały szkic briefu zapisany w tej karcie?"))return;
      form.reset();
      fallback.hidden=true;
      sessionStorage.removeItem("briefDraft");
      info.textContent="Szkic wyczyszczony. Formularz nadal niczego nie wysyła na serwer.";
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
