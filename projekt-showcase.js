(function(){
  var root=document.querySelector('.hero-realizacje');
  if(!root) return;

  var slides=[].slice.call(root.querySelectorAll('.hero-projekt'));
  var nav=document.querySelector('.hero-projekt-nav');
  var current=0;

  function loadDeferred(scope){
    if(!scope) return;
    scope.querySelectorAll('img[data-project-src]').forEach(function(img){
      var src=img.getAttribute('data-project-src');
      var srcset=img.getAttribute('data-project-srcset');
      var sizes=img.getAttribute('data-project-sizes');
      if(srcset) img.setAttribute('srcset',srcset);
      if(sizes) img.setAttribute('sizes',sizes);
      if(src) img.setAttribute('src',src);
      img.removeAttribute('data-project-src');
      img.removeAttribute('data-project-srcset');
      img.removeAttribute('data-project-sizes');
    });
  }

  function buttons(){
    return nav ? [].slice.call(nav.querySelectorAll('button[data-to]')) : [];
  }

  function show(index, scrollTile){
    if(!slides.length) return;
    current=(index+slides.length)%slides.length;

    slides.forEach(function(slide,i){
      slide.classList.toggle('aktywny',i===current);
      slide.setAttribute('aria-hidden',i===current?'false':'true');
    });

    buttons().forEach(function(btn,i){
      var on=i===current;
      btn.classList.toggle('tu',on);
      btn.setAttribute('aria-current',on?'true':'false');
      if(on && scrollTile!==false){
        try{btn.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'});}catch(e){}
      }
    });

    var activeSlide=slides[current];
    loadDeferred(activeSlide.querySelector('.project-view.tu') || activeSlide);
  }

  if(nav){
    nav.addEventListener('click',function(e){
      var btn=e.target.closest('button[data-to]');
      if(!btn) return;
      e.preventDefault();
      e.stopPropagation();
      show(Number(btn.dataset.to),true);
    });
  }

  var prev=document.querySelector('.hero-project-arrow.prev');
  var next=document.querySelector('.hero-project-arrow.next');
  if(prev) prev.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();show(current-1,true);});
  if(next) next.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();show(current+1,true);});

  document.querySelectorAll('.project-view-tabs').forEach(function(tabbar){
    var group=tabbar.dataset.tabs;
    var groupRoot=document.querySelector('.project-views[data-group="'+group+'"]');
    if(!groupRoot) return;
    var views=[].slice.call(groupRoot.querySelectorAll('.project-view'));
    tabbar.addEventListener('click',function(e){
      var btn=e.target.closest('button[data-view]');
      if(!btn) return;
      e.preventDefault();
      e.stopPropagation();
      var key=btn.dataset.view;
      [].slice.call(tabbar.querySelectorAll('button[data-view]')).forEach(function(b){
        b.classList.toggle('tu',b===btn);
      });
      views.forEach(function(v){v.classList.toggle('tu',v.dataset.view===key);});
      loadDeferred(groupRoot.querySelector('.project-view.tu'));
    });
  });

  root.addEventListener('keydown',function(e){
    if(e.key==='ArrowLeft'){e.preventDefault();show(current-1,true);}
    if(e.key==='ArrowRight'){e.preventDefault();show(current+1,true);}
  });

  show(0,false);
})();