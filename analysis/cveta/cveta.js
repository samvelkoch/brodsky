/* ================= цвета ================= */
/* Цвет каждой строки определила модель по контексту (cveta/make_data.py). Режимы: только названные цвета, плюс цвет предметов, плюс настроение. */
const CV=JSON.parse(document.getElementById('data-cv').textContent);
const CVN=CV.order.length, CVY0=CV.years[0], CVY1=CV.years[CV.years.length-1];
const CVSRC={named:[0],objects:[0,1],all:[0,1,2]};
const CVPER=[[1957,1960],[1961,1966],[1967,1972],[1973,1984],[1985,1989],[1990,1996]];
const cvRows=CVPER.map(([a,b])=>CV.poems.filter(p=>p.y>=a&&p.y<=b));
let cvMode='objects', cvT=1965, cvPlaying=false, cvLast=0, cvSeen=false, cvVisible=false;
const cvReduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const cvLines=CV.poems.reduce((a,p)=>a+p.n,0);
function cvCount(mode, ps){ const ok=CVSRC[mode], c=new Array(CVN).fill(0); for(const p of ps) for(const z of p.c) if(ok.includes(z[2])) c[z[1]]++; return c; }
const cvTot={named:cvCount('named',CV.poems), objects:cvCount('objects',CV.poems), all:cvCount('all',CV.poems)};
const cvSum=a=>a.reduce((x,y)=>x+y,0);
const cvTop=(m,n)=>cvTot[m].map((v,k)=>[v,k]).sort((a,b)=>b[0]-a[0]).slice(0,n).map(([v,k])=>`${CV.order[k]} ${Math.round(100*v/cvSum(cvTot[m]))}%`).join(', ');
const cvPoemsColored=CV.poems.filter(p=>p.c.length).length;
$('#t-colors').textContent=`Цвет каждой строки во всех стихотворениях определила языковая модель по контексту. Она учитывала не только слова «белый» или «синий», но и цвет предметов: снег белый, ночь ночная синяя, огонь оранжевый, гранит серый. Окрашенной оказалась примерно каждая шестая строка (${fmt(cvSum(cvTot.all))} из ${fmt(cvLines)}), строки без цвета остались пустыми.`;
$('#f-colors').textContent=`По одним названным цветам палитра Бродского графическая: ${cvTop('named',3)}. С цветом предметов она становится серо-ночной: ${cvTop('objects',3)}.`;
$('#t-cv-method').textContent=`Как размечали. Модель (Claude Sonnet) читала стихи целиком и для каждой строки выбирала один из ${CVN} оттенков или оставляла строку пустой. Для каждой метки она указывала источник: цвет назван словом, это цвет предмета или настроение строки. Спорные слова вроде «небо», «море» и «тьма» тоже размечены. Слепой проверки разметки людьми не было, поэтому отдельные строки могут быть окрашены спорно. Годы без даты отнесены к середине периода по разделу собрания.`;
const CVMODE={named:'Только цвета, названные словом: прилагательные, существительные и глаголы (белизна, чернеть, седой).',
  objects:'Плюс цвет предметов и времени суток: снег белый, ночь ночная синяя, огонь оранжевый, гранит серый.',
  all:'Плюс строки, окрашенные настроением без цветного предмета. Таких мало, около 3% разметки.'};
function cvShares(tt){ const i=Math.min(Math.floor(tt-CVY0),CVY1-CVY0), f=tt-CVY0-i, a=CV.sm[cvMode][i], b=CV.sm[cvMode][Math.min(i+1,CVY1-CVY0)];
  const e=f*f*(3-2*f); return a.map((v,k)=>v+(b[k]-v)*e); }
function cvFit(c){ const w=Math.max(260,c.clientWidth), d=devicePixelRatio||1, h=+c.getAttribute('height');
  if(c.width!==Math.round(w*d)||c.height!==Math.round(h*d)){ c.width=Math.round(w*d); c.height=Math.round(h*d); c.style.height=h+'px'; }
  const x=c.getContext('2d'); x.setTransform(d,0,0,d,0,0); return [x,w,h]; }
const cvLight=h=>{ const n=parseInt(h.slice(1),16); return (.3*(n>>16)+.59*((n>>8)&255)+.11*(n&255))>205; };
const cvAnch=CV.order.map((_,k)=>{ const a=(k*137.508)*Math.PI/180, r=.18+.30*((k*.618)%1); return [.5+r*Math.cos(a)*1.25,.5+r*Math.sin(a)]; });
let cvLegKey='';
function cvDraw(now){
  const s=cvShares(cvT); $('#cv-yr').textContent=Math.floor(cvT);
  let [x,w,h]=cvFit($('#cv-bar')); x.clearRect(0,0,w,h); let p=0;
  for(let k=0;k<CVN;k++){ const sw=s[k]*w; if(sw<.2) continue; x.fillStyle=CV.hex[k]; x.fillRect(p,0,sw+.5,h);
    if(sw>58){ x.fillStyle=cvLight(CV.hex[k])?'#211b16':'#fff'; x.font='11px "IBM Plex Mono", monospace'; x.fillText(CV.order[k],p+5,15); } p+=sw; }
  x.strokeStyle=css('--ring'); x.lineWidth=1; x.strokeRect(.5,.5,w-1,h-1);
  const top=s.map((v,k)=>[v,k]).sort((a,b)=>b[0]-a[0]).slice(0,6), key=cvMode+top.map(([v,k])=>k+':'+Math.round(v*100)).join();
  if(key!==cvLegKey){ cvLegKey=key; $('#cv-leg').innerHTML=top.map(([v,k])=>`<span><i style="background:${CV.hex[k]}"></i>${CV.order[k]} ${Math.round(v*100)}%</span>`).join(''); }
  [x,w,h]=cvFit($('#cv-blot')); x.clearRect(0,0,w,h);
  const R=Math.min(w,h*1.6)*.55;
  for(const [v,k] of s.map((v,k)=>[v,k]).sort((a,b)=>b[0]-a[0])){ if(v<.004) continue;
    const [ax,ay]=cvAnch[k], ph=now/2600+k, cx=ax*w+Math.sin(ph)*8, cy=ay*h+Math.cos(ph*1.3)*6, r=Math.sqrt(v)*R;
    const g=x.createRadialGradient(cx,cy,0,cx,cy,r); g.addColorStop(0,CV.hex[k]+'ee'); g.addColorStop(.55,CV.hex[k]+'aa'); g.addColorStop(1,CV.hex[k]+'00');
    x.fillStyle=g; x.beginPath(); x.arc(cx,cy,r,0,7); x.fill(); }
}
function cvSetPlay(on){ cvPlaying=on; cvLast=0; $('#cv-play').textContent=on?'❚❚ Пауза':'▶ Играть'; if(on) cvLoop(); }
let cvRaf=0;
function cvLoop(){ if(cvRaf) return; cvRaf=requestAnimationFrame(function f(now){
  if(cvPlaying){ if(cvLast) cvT+=(now-cvLast)/900; cvLast=now; if(cvT>CVY1+.99){ cvT=CVY0; } $('#cv-slider').value=Math.min(cvT,CVY1); }
  cvDraw(cvReduce?0:now);
  cvRaf=(cvVisible&&(cvPlaying||!cvReduce))?requestAnimationFrame(f):0; }); }
$('#cv-play').addEventListener('click',()=>cvSetPlay(!cvPlaying));
$('#cv-slider').addEventListener('input',e=>{ cvT=+e.target.value; cvSetPlay(false); cvLoop(); });
new IntersectionObserver(es=>{ for(const e of es){ cvVisible=e.isIntersecting; if(cvVisible){ if(!cvSeen){ cvSeen=true; if(!cvReduce) cvSetPlay(true); } cvLoop(); } } },{threshold:.15}).observe($('#cv-blot').closest('.panel'));
chart(()=>cvDraw(cvReduce?0:performance.now()), $('#cv-bar'));
function cvPalette(){ const box=$('#c-palette'); const rowH=34, labelW=70; const h=CVPER.length*rowH+8; const [s,w]=svg(box,h); const ring=css('--ring');
  cvRows.forEach((ps,i)=>{ const y=i*rowH+4, c=cvCount(cvMode,ps), tot=cvSum(c)||1; let x=labelW; const W=w-labelW-4;
    txt(s,labelW-10,y+17,pshort(PER[i]),{'text-anchor':'end',style:'fill:var(--ink)'});
    c.map((n,k)=>[n,k]).sort((a,b)=>b[0]-a[0]).forEach(([n,k])=>{ const ww=W*n/tot; if(ww<0.5) return;
      el('rect',{x:x+.5,y,width:Math.max(.5,ww-1),height:rowH-10,fill:CV.hex[k],stroke:ring,'stroke-width':.6,'data-tip':`${PER[i]} · ${CV.order[k]}: ${pnr(n,RUF.line)} (${fmt1(100*n/tot)}%)`},s); x+=ww; }); }); }
chart(cvPalette, $('#c-palette'));
function cvList(){ const c=cvTot[cvMode]; hbars($('#c-colors'),c.map((v,k)=>({l:CV.order[k],v,hex:CV.hex[k],tip:`${CV.order[k]}: ${pnr(v,RUF.line)}`})).filter(r=>r.v).sort((a,b)=>b.v-a.v),
  {color:'var(--neutral-bar)',labelW:104,swatch:true,rowH:22,fmtv:fmt}); }
const cvWall=$('#cv-wall');
cvWall.innerHTML=cvRows.map((ps,i)=>`<div class="cv-per">${PER[i]} · ${pnr(ps.length,RUF.poem)}</div><canvas class="cv-cnv" data-r="${i}" height="104" aria-hidden="true"></canvas>`).join('');
$('#cv-wall-u').textContent=`${pnr(CV.poems.length,RUF.poem)}; столбик — стихотворение сверху вниз`;
function cvDrawWall(){ cvWall.querySelectorAll('canvas').forEach(c=>{ const ps=cvRows[+c.dataset.r]; const [x,w,h]=cvFit(c);
  x.fillStyle=css('--shade'); x.clearRect(0,0,w,h); x.fillRect(0,0,w,h); const cw=w/ps.length, ok=CVSRC[cvMode];
  ps.forEach((p,i)=>{ const lh=h/p.n; for(const [li,ci,sr] of p.c){ if(!ok.includes(sr)) continue; x.fillStyle=CV.hex[ci]; x.fillRect(i*cw,li*lh,Math.max(cw-(cw>3?1:0),.8),Math.max(lh,1.2)); } }); }); }
chart(cvDrawWall, cvWall);
function cvPick(e){ const c=e.target.closest('canvas'); if(!c) return; const ps=cvRows[+c.dataset.r], b=c.getBoundingClientRect();
  const p=ps[Math.floor((e.clientX-b.left)/b.width*ps.length)]; if(!p) return;
  const n=p.c.filter(z=>CVSRC[cvMode].includes(z[2])).length;
  showTipHTML(`<b>${esc(tidy(p.t))}</b><br>${p.y}${p.u?' (год по разделу собрания)':''} · цвет в ${n} из ${pnr(p.n,RUF.line)}`,e.clientX,e.clientY); }
cvWall.addEventListener('pointermove',cvPick); cvWall.addEventListener('pointerdown',cvPick);
cvWall.addEventListener('pointerleave',()=>{ tip.hidden=true; });
function cvApply(){ $('#cv-mode').textContent=CVMODE[cvMode]; cvLegKey=''; cvList(); enqueue(cvPalette); enqueue(cvDrawWall); cvDraw(cvReduce?0:performance.now()); }
seg($('#seg-cv'),[['named','Названные цвета'],['objects','+ цвет предметов'],['all','+ настроение']],cvMode,v=>{ cvMode=v; cvApply(); });
$('#cv-mode').textContent=CVMODE[cvMode]; cvList();

