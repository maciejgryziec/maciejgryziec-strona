/* Direct delivery is enabled only after the private SMTP setup test succeeds.
   Until then the existing email-draft action remains available, not a fake send button. */
(function () {
  'use strict';
  var form = document.getElementById('brief-form');
  if (!form || !window.fetch || !window.crypto || !crypto.subtle) return;
  var button = form.querySelector('button[type="submit"]');
  var info = document.getElementById('brief-info');
  var names = ['imie','email','firma','telefon','typ','dzis','problem','narzedzia','uzytkownicy','budzet','efekt'];
  var session = null, sessionAt = 0, busy = false, sent = false, memoryPending = null;
  var trap = document.createElement('div');
  trap.setAttribute('aria-hidden','true');
  trap.style.cssText = 'position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;';
  var label = document.createElement('label');
  label.textContent = 'Pozostaw to pole puste';
  var honeypot = document.createElement('input');
  honeypot.name = 'website'; honeypot.type = 'text'; honeypot.autocomplete = 'off'; honeypot.tabIndex = -1;
  label.appendChild(honeypot); trap.appendChild(label); form.appendChild(trap);

  async function request(url, options, timeout) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, timeout);
    try {
      var response = await fetch(url, Object.assign({credentials:'same-origin',cache:'no-store',signal:controller.signal}, options));
      var data = await response.json();
      return {response:response,data:data};
    } finally { clearTimeout(timer); }
  }
  async function prepare() {
    try {
      var r = await request('/api/contact/session', {method:'GET'}, 9000);
      if (!r.response.ok || !r.data.ready || typeof r.data.token !== 'string') return false;
      session = r.data; sessionAt = Date.now();
      form.dataset.directSend = 'ready';
      button.textContent = 'Wyślij';
      button.setAttribute('data-umami-event','brief-wyslij');
      if (!busy && !sent) {
        info.textContent = 'Przycisk Wyślij prześle opis bezpośrednio na kontakt@maciejgryziec.pl. Nie musisz otwierać programu pocztowego. Szkic pozostaje w tej karcie do wysłania lub wyczyszczenia.';
      }
      return true;
    } catch (_) { return false; }
  }
  function uuid() {
    if (crypto.randomUUID) return crypto.randomUUID();
    var b = crypto.getRandomValues(new Uint8Array(16));
    b[6] = (b[6] & 15) | 64; b[8] = (b[8] & 63) | 128;
    var s = Array.from(b, function (x) { return x.toString(16).padStart(2,'0'); }).join('');
    return s.slice(0,8)+'-'+s.slice(8,12)+'-'+s.slice(12,16)+'-'+s.slice(16,20)+'-'+s.slice(20);
  }
  function pending() {
    try { return JSON.parse(sessionStorage.getItem('briefDelivery') || 'null') || memoryPending; }
    catch (_) { return memoryPending; }
  }
  function savePending(value) {
    memoryPending = value;
    try { if (value) sessionStorage.setItem('briefDelivery',JSON.stringify(value)); else sessionStorage.removeItem('briefDelivery'); }
    catch (_) {}
  }
  async function deliveryId(data) {
    var bytes = new TextEncoder().encode(JSON.stringify(data));
    var digest = await crypto.subtle.digest('SHA-256',bytes);
    var hash = Array.from(new Uint8Array(digest),function(x){return x.toString(16).padStart(2,'0');}).join('');
    var old = pending();
    if (old && old.hash === hash) return old.id;
    var next = {id:uuid(),hash:hash}; savePending(next); return next.id;
  }
  form.addEventListener('input', function () {
    if (sent && !busy) { sent = false; button.disabled = false; button.textContent = 'Wyślij'; }
  });
  form.addEventListener('submit', async function (event) {
    if (!session) return; // Keep the existing, functioning draft action until SMTP is configured.
    event.preventDefault(); event.stopImmediatePropagation();
    if (busy || sent || !form.reportValidity()) return;
    var fd = new FormData(form), data = {};
    names.forEach(function (name) { data[name] = String(fd.get(name) || '').trim(); });
    data.website = honeypot.value;
    busy = true; button.textContent = 'Wysyłanie...';
    info.textContent = 'Wysyłam wiadomość. Zaczekaj na potwierdzenie.';
    var controls = Array.from(form.querySelectorAll('input,select,textarea,button')).map(function(el){return [el,el.disabled];});
    controls.forEach(function(pair){pair[0].disabled=true;});
    try {
      var id = await deliveryId(data);
      if (Date.now()-sessionAt > 3500000 && !await prepare()) throw new Error('session');
      // Gives the signed anti-spam token its minimum age, including an autofilled form.
      var delay = 2300 - (Date.now()-sessionAt);
      if (delay > 0) await new Promise(function(resolve){setTimeout(resolve,delay);});
      data.request_id = id; data.token = session.token;
      var r = await request('/api/contact', {
        method:'POST',headers:{'Content-Type':'application/json','X-Contact-Form':'1'},body:JSON.stringify(data)
      }, 45000);
      if (r.response.ok && r.data.ok === true && r.data.status === 'sent' && r.data.request_id === id) {
        sent = true; form.reset(); savePending(null);
        try { sessionStorage.removeItem('briefDraft'); } catch (_) {}
        info.textContent = 'Wiadomość została wysłana. Dziękuję za opis projektu. Odpowiem na podany adres e-mail.';
        if (typeof window.siteTrack === 'function') window.siteTrack('brief-wyslano');
      } else {
        info.textContent = typeof r.data.message === 'string' ? r.data.message : 'Nie udało się potwierdzić wysyłki. Zachowaj opis i skontaktuj się bezpośrednio.';
        if (r.data.code === 'delivery_failed' || r.data.code === 'validation') savePending(null);
        if (r.data.code === 'token') { sessionAt=0; }
      }
    } catch (_) {
      info.textContent = 'Nie udało się potwierdzić wysyłki. Opis pozostał w formularzu. Możesz ponowić sprawdzenie lub skopiować go i napisać na kontakt@maciejgryziec.pl.';
    } finally {
      controls.forEach(function(pair){pair[0].disabled=pair[1];});
      busy = false; button.disabled = sent;
      button.textContent = sent ? 'Wysłano' : 'Wyślij';
    }
  }, true);
  prepare();
})();
