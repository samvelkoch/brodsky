/* ---------- карта словаря: области, эпохи, соседи ---------- */
const WM={per:-1, group:-1, sel:null, hov:null, timer:null, n:null, edges:null};
const WMK={}; ST.wmap.forEach(m=>{ WMK[m.k]=m; });
const PT6=EX.per_tokens.slice(0,6), PTALL=EX.per_tokens.reduce((a,b)=>a+b,0);
const wmKnown=m=>!!LEX[m.k];
const wmCount=(m,p)=>{ const e=LEX[m.k]; if(!e) return p<0?m.n:0; return p<0?e[1].reduce((a,b)=>a+b,0):e[1][p]; };
const wmRate=(m,p)=>wmCount(m,p)/(p<0?PTALL:PT6[p])*1000;
const RMAX_ALL=Math.max(...ST.wmap.map(m=>wmRate(m,-1)));
const RMAX_PER=Math.max(...ST.wmap.flatMap(m=>wmKnown(m)?PT6.map((_,p)=>wmRate(m,p)):[0]));
const wmGroupLabel=c=>ST.wgroups[c].slice(0,2).join(' · ');
function wmRising(m,p){ return p>=0 && wmKnown(m) && wmCount(m,p)>=6 && wmRate(m,p)/Math.max(wmRate(m,-1),1e-9)>=1.5; }
function wmTop(p,n=7){ return ST.wmap.filter(m=>wmRising(m,p)).sort((a,b)=>wmRate(b,p)/wmRate(b,-1)-wmRate(a,p)/wmRate(a,-1)).slice(0,n); }

const wmTerrOp=()=>lum(css('--surface'))<0.2?.2:.34;
function drawWmap(){
  const box=$('#c-wmap'); const W=box.clientWidth||800; const h=W<600?Math.round(W*1.3):Math.round(Math.min(720,Math.max(460,W*0.66))); const [s,w]=svg(box,h);
  const M=ST.wmap; const xs=M.map(m=>m.x), ys=M.map(m=>m.y); const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  const padX=W<600?26:54, padY=34; const sx=x=>padX+(w-2*padX)*(x-x0)/(x1-x0), sy=y=>padY+(h-2*padY)*(y-y0)/(y1-y0);
  const pos={}; M.forEach(m=>{ pos[m.k]=[sx(m.x),sy(m.y)]; });
  const defs=el('defs',{},s); const f=el('filter',{id:'wm-blur',x:'-20%',y:'-20%',width:'140%',height:'140%'},defs); el('feGaussianBlur',{stdDeviation:W<600?11:17},f);
  const terr=el('g',{class:'wm-terr',filter:'url(#wm-blur)'},s);
  const R=W<600?24:34;
  M.forEach(m=>el('circle',{cx:pos[m.k][0],cy:pos[m.k][1],r:R,fill:css('--g'+(m.c+1)),opacity:wmTerrOp(),'data-g':m.c},terr));
  ST.wgroups.forEach((g,c)=>{ const mm=M.filter(m=>m.c===c); if(!mm.length) return;
    const cx=mm.reduce((a,m)=>a+pos[m.k][0],0)/mm.length, cy=mm.reduce((a,m)=>a+pos[m.k][1],0)/mm.length;
    const t=txt(s,cx,cy,wmGroupLabel(c),{'text-anchor':'middle',class:'wm-lab','data-lab':c,style:`font-size:${W<600?9:11}px;fill:${css('--ink-2')};opacity:0`}); t.setAttribute('paint-order','stroke'); t.setAttribute('stroke',css('--surface')); t.setAttribute('stroke-width','5'); });
  const edges=el('g',{class:'wm-terr'},s); WM.edges=edges;
  const nodes=[];
  M.forEach(m=>{ const [X,Y]=pos[m.k];
    const t=txt(s,X,Y,m.w,{'text-anchor':'middle',tabindex:0,role:'button','aria-label':m.w,style:'font-family:var(--f-body);cursor:pointer'});
    const c=el('circle',{cx:X,cy:Y-4,r:3.2,class:'dot clickable'},s);
    const pick=()=>{ WM.sel=(WM.sel===m.k)?null:m.k; wmApply(); };
    [t,c].forEach(n=>{ n.addEventListener('click',pick); n.addEventListener('pointerenter',e=>{ if(e.pointerType==='mouse'){ WM.hov=m.k; wmApply(); } });
      n.addEventListener('pointerleave',e=>{ if(e.pointerType==='mouse'){ WM.hov=null; wmApply(); } }); });
    t.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); pick(); } });
    nodes.push({m,t,c,X,Y}); });
  WM.n={nodes,pos,w,h};
  wmApply();
}
function wmApply(){
  if(!WM.n) return; const {nodes,pos,w,h}=WM.n; const p=WM.per, focus=WM.hov||WM.sel;
  const nb=focus?new Set((ST.neighbors[focus]||[]).filter(k=>WMK[k])):new Set();
  const rmax=p<0?RMAX_ALL:RMAX_PER;
  const items=nodes.map(o=>{ const known=wmKnown(o.m); const cnt=wmCount(o.m,p); const r=known?wmRate(o.m,p):0;
    const rise=wmRising(o.m,p); const fs=known&&cnt>0?10.5+8.5*Math.sqrt(Math.min(1,r/rmax)):10.5; return {o,known,cnt,r,rise,fs}; });
  const order=items.slice().sort((a,b)=>((b.o.m.k===focus||nb.has(b.o.m.k))?1e9:0)+(b.rise?1e6:0)+b.r-(((a.o.m.k===focus||nb.has(a.o.m.k))?1e9:0)+(a.rise?1e6:0)+a.r));
  const placed=[]; const fits=b=>!placed.some(q=>b.x<q.x+q.w&&b.x+b.w>q.x&&b.y<q.y+q.h&&b.y+b.h>q.y);
  order.forEach(it=>{ const m=it.o.m, forced=(m.k===focus||nb.has(m.k)); const bw=m.w.length*it.fs*0.55+6, bh=it.fs+2;
    const bx={x:it.o.X-bw/2,y:it.o.Y-it.fs,w:bw,h:bh}; it.show=(it.known?it.cnt>0:true)&&(forced||fits(bx)); if(it.show) placed.push(bx); });
  const inGroup=m=>WM.group<0||m.c===WM.group;
  items.forEach(it=>{ const m=it.o.m; const dim=(WM.group>=0&&!inGroup(m))||(focus&&m.k!==focus&&!nb.has(m.k));
    const absent=it.known&&it.cnt===0; const isF=m.k===focus; const isN=nb.has(m.k);
    const tip=`${esc(m.w)}<br>${it.known?`${pn(it.cnt,RUF.raz)} в стихах${p>=0?', '+PER[p]:''}`:`${pn(m.n,RUF.raz)} в стихах`}<br>нажмите, чтобы увидеть близкие слова`;
    const ink=isF||isN||it.rise?'--mark':(dim?'--muted':'--ink');
    it.o.t.setAttribute('data-tip',tip); it.o.c.setAttribute('data-tip',tip);
    const st=it.o.t.style; st.fontSize=it.fs.toFixed(1)+'px'; st.fill=css(ink); st.fontWeight=(isF||it.rise)?'700':'400';
    st.opacity=it.show?(dim?.22:(absent?.15:1)):0; st.pointerEvents=it.show?'auto':'none';
    it.o.c.setAttribute('fill',css(isF||isN?'--mark':(it.rise?'--mark':'--neutral-bar')));
    it.o.c.style.opacity=it.show?0:(dim?.12:(absent?.1:(it.rise?.9:.55))); it.o.c.style.pointerEvents=it.show?'none':'auto'; });
  WM.n.nodes[0]&&document.querySelectorAll('#c-wmap circle[data-g]').forEach(c=>{ const g=+c.getAttribute('data-g'); c.style.opacity=(WM.group<0||g===WM.group)?wmTerrOp():.04; });
  document.querySelectorAll('#c-wmap .wm-lab').forEach(t=>{ const g=+t.getAttribute('data-lab'); t.style.opacity=(WM.group>=0&&g===WM.group)?.9:0; t.style.fontSize=(WM.group>=0&&g===WM.group)?'15px':''; });
  const E=WM.edges; while(E.firstChild) E.removeChild(E.firstChild);
  if(focus&&pos[focus]){ const [ax,ay]=pos[focus]; nb.forEach(k=>{ const [bx,by]=pos[k]; const dx=bx-ax, dy=by-ay, d=Math.hypot(dx,dy)||1; const cx=(ax+bx)/2-dy*0.16, cy=(ay+by)/2+dx*0.16;
    el('path',{d:`M${ax},${ay-4} Q${cx},${cy} ${bx},${by-4}`,fill:'none',stroke:css('--mark'),'stroke-width':1.5,'stroke-linecap':'round',opacity:.7},E); });
    el('circle',{cx:ax,cy:ay-4,r:14,fill:'none',stroke:css('--mark'),'stroke-width':1.5,opacity:.8},E); }
  document.querySelectorAll('#wm-groups button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===WM.group)));
  document.querySelectorAll('#wm-per button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===WM.per)));
  $('#wm-play').textContent=WM.timer?'❚❚ Пауза':'▶ Играть';
  wmReadout();
}
function wmReadout(){ const host=$('#wm-read'); const p=WM.per, k=WM.sel;
  const link=(kk)=>`<button type="button" class="chip" data-wk="${esc(kk)}">${esc(disp(kk))}</button>`;
  let html;
  if(k){ const m=WMK[k]; const nbs=(ST.neighbors[k]||[]);
    html=`<b>${esc(m.w)}</b> — ${pn(wmCount(m,-1),RUF.raz)} в стихах${wmKnown(m)?`; по периодам: ${PER.map((pp,i)=>`${pshort(pp)}: ${fmt(wmCount(m,i))}`).join(', ')}`:''}.<br>Близкие по употреблению (линии на карте): ${nbs.map(link).join(' ')||'—'} <button type="button" class="btn" data-open="${esc(k)}">Открыть в словоискателе →</button>`;
  } else if(p>=0){ const top=wmTop(p);
    html=`<b>${esc(PER[p])}.</b> Красным выделены слова, которых в эти годы заметно больше, чем в среднем по всем стихам (не реже чем в 1,5 раза, не меньше 6 употреблений): ${top.map(m=>link(m.k)).join(' ')||'—'}`;
  } else html=`Размер слова — как часто Бродский его употребляет; цветная область — группа слов, которые он ставит в похожее окружение. Выберите период или нажмите «Играть», чтобы увидеть, как менялся словарь, и нажмите на слово, чтобы увидеть его ближайших соседей.`;
  host.innerHTML=html;
  host.querySelectorAll('[data-wk]').forEach(b=>b.addEventListener('click',()=>{ WM.sel=b.dataset.wk; wmApply(); }));
  host.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>openWord(b.dataset.open,true)));
}
function wmSetPer(p,userPick){ if(userPick&&WM.timer){ clearInterval(WM.timer); WM.timer=null; } WM.per=p; wmApply(); }
function wmPlay(){ if(WM.timer){ clearInterval(WM.timer); WM.timer=null; wmApply(); return; }
  if(WM.per<0||WM.per>=NPER-1) WM.per=0; wmApply();
  WM.timer=setInterval(()=>{ WM.per=(WM.per+1)%NPER; wmApply(); },2600); wmApply(); }
(function(){
  const g=$('#wm-groups'); const mk=(i,l,c)=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.setAttribute('aria-pressed',String(i===WM.group));
    b.innerHTML=(c?`<i style="background:var(--g${i+1})"></i>`:'')+esc(l); b.addEventListener('click',()=>{ WM.group=(WM.group===i&&i>=0)?-1:i; wmApply(); }); g.appendChild(b); };
  mk(-1,'все слова',false); ST.wgroups.forEach((gr,i)=>mk(i,wmGroupLabel(i),true));
  const pr=$('#wm-per'); [[-1,'все годы'],...PER.map((pp,i)=>[i,pshort(pp)])].forEach(([i,l])=>{ const b=document.createElement('button'); b.type='button'; b.textContent=l; b.setAttribute('aria-pressed',String(i===WM.per));
    b.addEventListener('click',()=>wmSetPer(i,true)); pr.appendChild(b); });
  $('#wm-play').addEventListener('click',wmPlay);
  $('#wm-find').addEventListener('input',e=>{ const q=norm(e.target.value); if(!q){ return; } const hit=WMK[q]||ST.wmap.find(m=>norm(m.w).startsWith(q)); if(hit){ WM.sel=hit.k; wmApply(); } });
  chart(drawWmap,$('#c-wmap')); })();
