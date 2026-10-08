(function(){
  document.querySelectorAll('.detail-showcase').forEach(function(root){
    var buttons=[].slice.call(root.querySelectorAll('.detail-tabs button'));
    var panels=[].slice.call(root.querySelectorAll('.detail-panel'));
    buttons.forEach(function(btn){
      btn.addEventListener('click',function(){
        var key=btn.dataset.view;
        buttons.forEach(function(b){b.classList.toggle('tu',b===btn)});
        panels.forEach(function(p){
          var active=p.dataset.view===key;
          p.classList.toggle('tu',active);
          // A user-selected screen must load immediately, even when its natural-height
          // gallery is temporarily collapsed before the image has decoded.
          if(active)p.querySelectorAll('img').forEach(function(img){img.loading='eager'});
        });
      });
    });
  });
})();
