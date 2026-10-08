/* Cosmetic animation of the approved concept. No API requests or live system metrics. */
(function () {
  'use strict';
  var scenes = Array.from(document.querySelectorAll('.judler-motion'));
  if (!scenes.length || !('IntersectionObserver' in window)) return;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var visible = new WeakMap();
  function update() {
    scenes.forEach(function (scene) {
      var hiddenPanel = scene.closest('[hidden], [aria-hidden="true"], [inert]');
      var card = scene.closest('.karta');
      var on = !document.hidden && !reduced.matches && visible.get(scene) &&
        !hiddenPanel && (!card || card.classList.contains('aktywna'));
      scene.classList.toggle('is-animating', Boolean(on));
    });
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      visible.set(entry.target, entry.isIntersecting && entry.intersectionRatio > 0.03);
    });
    update();
  }, {threshold: [0, 0.03, 0.2]});
  scenes.forEach(function (scene) { observer.observe(scene); });
  // Switching a tab or carousel card must stop the hidden scene immediately.
  var mutations = new MutationObserver(update);
  var containers = new Set();
  scenes.forEach(function (scene) {
    [scene.closest('.hero-projekt'), scene.closest('.project-view'), scene.closest('.karta'), scene.closest('.detail-panel')].forEach(function (node) {
      if (node && !containers.has(node)) {
        containers.add(node);
        mutations.observe(node, {attributes: true, attributeFilter: ['class', 'hidden', 'aria-hidden', 'inert']});
      }
    });
  });
  document.addEventListener('visibilitychange', update);
  if (reduced.addEventListener) reduced.addEventListener('change', update);
  else if (reduced.addListener) reduced.addListener(update);
  window.addEventListener('pagehide', function () {
    scenes.forEach(function (scene) { scene.classList.remove('is-animating'); });
  });
  window.addEventListener('pageshow', update);
})();
