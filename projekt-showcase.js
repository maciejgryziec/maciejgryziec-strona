(function () {
  'use strict';
  var root = document.querySelector('.hero-realizacje');
  if (!root) return;
  var slides = Array.from(root.querySelectorAll('.hero-projekt'));
  var nav = root.querySelector('.hero-projekt-nav');
  var buttons = nav ? Array.from(nav.querySelectorAll('button[data-to]')) : [];
  var current = 0;

  function loadDeferred(scope) {
    if (!scope) return;
    scope.querySelectorAll('img[data-project-src]').forEach(function (img) {
      if (img.dataset.projectSizes) img.sizes = img.dataset.projectSizes;
      if (img.dataset.projectSrcset) img.srcset = img.dataset.projectSrcset;
      img.src = img.dataset.projectSrc;
      delete img.dataset.projectSrc;
      delete img.dataset.projectSrcset;
      delete img.dataset.projectSizes;
    });
  }
  function revealTab(bar, button) {
    // Scroll only this horizontal strip, never jump the whole page to a new project.
    var left = button.offsetLeft - bar.offsetLeft - (bar.clientWidth - button.offsetWidth) / 2;
    bar.scrollTo({left: Math.max(0, left), behavior: 'auto'});
  }
  function setPanel(panel, on) {
    panel.hidden = !on;
    panel.inert = !on;
    panel.setAttribute('aria-hidden', String(!on));
  }
  function show(index, focus) {
    if (!slides.length || !Number.isFinite(index)) return;
    current = (index + slides.length) % slides.length;
    slides.forEach(function (slide, i) {
      var on = i === current;
      slide.classList.toggle('aktywny', on);
      setPanel(slide, on);
    });
    buttons.forEach(function (button, i) {
      var on = i === current;
      button.classList.toggle('tu', on);
      button.setAttribute('aria-selected', String(on));
      button.tabIndex = on ? 0 : -1;
      if (on) {
        revealTab(nav, button);
        if (focus) button.focus({preventScroll: true});
      }
    });
    loadDeferred(slides[current].querySelector('.project-view.tu'));
  }
  function keyboardIndex(event, index, length) {
    if (event.key === 'ArrowRight') return (index + 1) % length;
    if (event.key === 'ArrowLeft') return (index + length - 1) % length;
    if (event.key === 'Home') return 0;
    if (event.key === 'End') return length - 1;
    return null;
  }
  if (nav) {
    nav.setAttribute('role', 'tablist');
    buttons.forEach(function (button, i) {
      button.type = 'button';
      button.id = 'project-tab-' + i;
      button.setAttribute('role', 'tab');
      button.setAttribute('aria-controls', 'project-panel-' + i);
      slides[i].id = 'project-panel-' + i;
      slides[i].setAttribute('role', 'tabpanel');
      slides[i].setAttribute('aria-labelledby', button.id);
    });
    nav.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-to]');
      if (button && nav.contains(button)) show(Number(button.dataset.to), false);
    });
    nav.addEventListener('keydown', function (event) {
      var index = keyboardIndex(event, current, slides.length);
      if (index !== null) {
        event.preventDefault(); event.stopPropagation(); show(index, true);
      }
    });
  }
  root.querySelectorAll('.hero-project-arrow').forEach(function (button) {
    button.addEventListener('click', function () {
      show(current + (button.classList.contains('prev') ? -1 : 1), false);
    });
  });
  root.querySelectorAll('.project-view-tabs').forEach(function (bar) {
    var slide = bar.closest('.hero-projekt');
    var group = slide.querySelector('.project-views');
    if (!group) return;
    var tabs = Array.from(bar.querySelectorAll('button[data-view]'));
    var panels = Array.from(group.querySelectorAll('.project-view'));
    var active = 0;
    bar.setAttribute('role', 'tablist');
    bar.setAttribute('aria-label', 'Widoki projektu ' + bar.dataset.tabs);
    tabs.forEach(function (tab) {
      var panel = panels.find(function (p) { return p.dataset.view === tab.dataset.view; });
      if (!panel) return;
      tab.type = 'button'; tab.id = 'view-tab-' + bar.dataset.tabs + '-' + tab.dataset.view;
      panel.id = 'view-panel-' + bar.dataset.tabs + '-' + tab.dataset.view;
      tab.setAttribute('role', 'tab'); tab.setAttribute('aria-controls', panel.id);
      panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', tab.id);
    });
    function choose(index, focus, load) {
      active = index;
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.classList.toggle('tu', on); tab.tabIndex = on ? 0 : -1;
        tab.setAttribute('aria-selected', String(on));
      });
      panels.forEach(function (panel) {
        var on = panel.dataset.view === tabs[index].dataset.view;
        panel.classList.toggle('tu', on); setPanel(panel, on);
        if (on && load) loadDeferred(panel);
      });
      revealTab(bar, tabs[index]);
      if (focus) tabs[index].focus({preventScroll: true});
    }
    bar.addEventListener('click', function (event) {
      var tab = event.target.closest('button[data-view]');
      var index = tabs.indexOf(tab);
      if (index >= 0) choose(index, false, true);
    });
    bar.addEventListener('keydown', function (event) {
      var index = keyboardIndex(event, active, tabs.length);
      if (index !== null) {
        event.preventDefault(); event.stopPropagation(); choose(index, true, true);
      }
    });
    choose(0, false, false);
  });
  show(0, false);
})();
