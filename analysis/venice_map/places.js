(function(){
var pts=[].slice.call(document.querySelectorAll('.vm-pt')),cur=null,touch=false,wasOn=false;
function bounds(w){var r=w.getBoundingClientRect(),bar=document.querySelector('.bar'),bt=bar&&getComputedStyle(bar).position==='sticky'?bar.getBoundingClientRect().bottom:0;return{l:Math.max(r.left,0)+4,t:Math.max(r.top,bt,0)+4,r:Math.min(r.right,innerWidth)-4,b:Math.min(r.bottom,innerHeight)-4}}
function place(pt){var pop=pt.querySelector('.vm-pop'),mk=pt.querySelector('.vm-mk'),B=bounds(pt.closest('.vm-wrap')),o=pt.getBoundingClientRect(),
 mr=mk.getBoundingClientRect(),rad=mr.width/2+7,pw=pop.offsetWidth,ph=pop.offsetHeight,cx=mr.left+mr.width/2,cy=mr.top+mr.height/2;
 var cand=[{x:cx-pw/2,y:cy-rad-ph,m:'y'},{x:cx-pw/2,y:cy+rad,m:'y'},{x:cx+rad,y:cy-ph/2,m:'x'},{x:cx-rad-pw,y:cy-ph/2,m:'x'}],best=null;
 cand.forEach(function(c){var ox=Math.max(0,B.l-c.x)+Math.max(0,c.x+pw-B.r),oy=Math.max(0,B.t-c.y)+Math.max(0,c.y+ph-B.b),over=c.m==='y'?oy:ox;
  var pen=over*1000+(c.m==='y'?oy:ox)+(c.m==='y'?ox:oy)*0.01;if(!best||pen<best.pen)best={c:c,pen:pen}});
 var c=best.c,x=Math.min(Math.max(c.x,B.l),Math.max(B.l,B.r-pw)),y=Math.min(Math.max(c.y,B.t),Math.max(B.t,B.b-ph));
 pop.style.left=(x-o.left)+'px';pop.style.top=(y-o.top)+'px'}
function show(pt){if(cur&&cur!==pt)hide(cur);pt.classList.add('on');cur=pt;place(pt)}
function hide(pt){pt.classList.remove('on');if(cur===pt)cur=null}
pts.forEach(function(pt){var mk=pt.querySelector('.vm-mk');
 mk.addEventListener('pointerdown',function(e){touch=e.pointerType!=='mouse';wasOn=pt.classList.contains('on')});
 pt.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse')show(pt)});
 pt.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse'&&document.activeElement!==mk)hide(pt)});
 mk.addEventListener('focus',function(){show(pt)});mk.addEventListener('blur',function(){hide(pt)});
 mk.addEventListener('click',function(e){e.stopPropagation();if(touch){wasOn?hide(pt):show(pt);touch=false}else show(pt)})});
document.addEventListener('click',function(e){if(cur&&!e.target.closest('.vm-pt'))hide(cur)});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&cur)hide(cur)});
addEventListener('resize',function(){if(cur)place(cur)});addEventListener('scroll',function(){if(cur)place(cur)},{passive:true});
})();
