(function(){
  document.querySelectorAll('.detail-showcase').forEach(function(root){
    var buttons=[].slice.call(root.querySelectorAll('.detail-tabs button'));
    var panels=[].slice.call(root.querySelectorAll('.detail-panel'));
    buttons.forEach(function(btn){
      btn.addEventListener('click',function(){
        var key=btn.dataset.view;
        buttons.forEach(function(b){b.classList.toggle('tu',b===btn)});
        panels.forEach(function(p){p.classList.toggle('tu',p.dataset.view===key)});
      });
    });
  });
})();
