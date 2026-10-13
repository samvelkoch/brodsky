/* ================= Мир Бродского: персонажи, места, транспорт, еда, напитки ================= */
const WD=JSON.parse(document.getElementById('data-world').textContent);
const PT7=EX.per_tokens, PTOT=PT7.slice(0,6).reduce((a,b)=>a+b,0);
const per10k=(n,p)=>PT7[p]?n/PT7[p]*1e4:0;
const POEM_BY=new Map(); PS.forEach((p,i)=>POEM_BY.set(p.t+'|'+(p.y||''),i));
const reEsc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const stemOf=w=>{ w=String(w).replace(/ё/g,'е'); return w.length>4?w.slice(0,-1):w; };
function hiWord(s,w){ const t=esc(s); const st=stemOf(w); try{ return t.replace(new RegExp('('+reEsc(st).replace(/е/g,'[её]')+'[а-яё]*)','i'),'<b>$1</b>'); }catch(e){ return t; } }
function quotesHTML(ctx,word){ if(!ctx||!ctx.length) return '<p class="muted">Строк для показа нет.</p>';
  return ctx.map(c=>{ const ok=c.p&&POEM_BY.has(c.t+'|'+(c.y||'')); return `<blockquote>${hiWord(c.s,word)}<cite>${esc(tidy(c.t))}${c.y?', '+c.y:''}${c.p?'':' · проза'}${ok?` · <button type="button" class="lnk" data-t="${esc(c.t)}" data-y="${c.y||''}">карточка стихотворения</button>`:''}</cite></blockquote>`; }).join(''); }
function bindQuotes(host){ host.querySelectorAll('button.lnk').forEach(b=>b.addEventListener('click',()=>{ const i=POEM_BY.get(b.dataset.t+'|'+b.dataset.y); if(i!=null) selectPoem(i,true); })); }
function sparkSVG(vals,{h=46,color='var(--s1)',labels=PSH,unit=''}={}){ const n=vals.length, w=n*30, mx=Math.max(...vals,1e-9);
  const bars=vals.map((v,i)=>{ const bh=Math.max(v>0?2:0,(h-14)*v/mx); return `<rect x="${i*30+4}" y="${h-12-bh}" width="22" height="${bh}" rx="2" fill="${color}" data-tip="${esc(labels[i])}: ${fmt1(v)}${unit}"/><text x="${i*30+15}" y="${h-1}" text-anchor="middle" style="font-size:8.5px;fill:var(--muted)">${esc(String(labels[i]).slice(2,4)+'–'+String(labels[i]).slice(-2))}</text>`; }).join('');
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" style="max-width:${w*1.5}px;display:block" role="img">${bars}</svg>`; }

/* ---------- карточка сущности (лица, места, слова) ---------- */
function entityCard(host,o){
  const per=o.per?o.per.slice(0,6):null; const rates=per?per.map((v,i)=>per10k(v,i)):null;
  host.innerHTML=`<div class="eyebrow">${esc(o.eyebrow||'')}</div><div class="ttl">${esc(o.title)}</div><div class="meta">${esc(o.meta||'')}</div>
    <div class="tiles">${o.tiles.map(([b,l])=>`<div><b>${b}</b><span>${l}</span></div>`).join('')}</div>
    ${rates&&per.some(v=>v>0)?`<h4>В стихах по периодам, на 10 000 слов</h4>${sparkSVG(rates,{color:o.color||'var(--s1)'})}`:''}
    ${o.chips&&o.chips.length?`<h4>${esc(o.chipsTitle||'Рядом')}</h4><div class="chips">${o.chips.map((c,i)=>`<button type="button" class="chip" data-c="${i}">${esc(c.label)}</button>`).join('')}</div>`:''}
    <h4>Строки</h4>${quotesHTML(o.ctx,o.word||o.title)}${o.note?`<p class="muted" style="font-size:13.5px;margin-top:10px">${o.note}</p>`:''}`;
  host.querySelectorAll('button.chip[data-c]').forEach(b=>b.addEventListener('click',()=>o.chips[+b.dataset.c].fn()));
  bindQuotes(host);
}

/* ================= персонажи ================= */
const PPL=WD.persons, PN=PPL.nodes, POTH=PPL.others;
const PPALL=[...PN,...POTH];
const PP={mode:'all',per:-1,cl:-1,sel:null,hov:null,N:null};
const ppCount=n=>PP.per>=0?n.per[PP.per]:(PP.mode==='poems'?n.np:PP.mode==='prose'?n.nr:n.n);
const ppSize=n=>PP.per>=0?n.per[PP.per]:(PP.mode==='poems'?n.poems:PP.mode==='prose'?n.essays:n.texts);
const clCol=c=>c<0?css('--neutral-bar'):css('--g'+(c+1));
const KINDN={person:'человек',sacred:'божественное имя'};
(function(){
  const bp=[...PPALL].sort((a,b)=>b.poems-a.poems||b.np-a.np), br=[...PPALL].sort((a,b)=>b.essays-a.essays||b.nr-a.nr);
  const top=(arr,f,n)=>arr.filter(x=>f(x)>0).slice(0,n).map(x=>x.name).join(', ');
  const E=PPL.edges.slice().sort((a,b)=>b[2]-a[2])[0];
  $('#f-pers').textContent=`В текстах Бродского названо по имени ${fmt(PPL.total)} ${plural(PPL.total, ['лицо', 'лица', 'лиц'])}, в стихах — ${fmt(PPL.poems_named)}. Больше всего стихотворений, где они названы: ${top(bp,x=>x.poems,4)}. В прозе, по числу текстов: ${top(br,x=>x.essays,4)}. Ближе всего друг к другу стоят ${PN[E[0]].name} и ${PN[E[1]].name}: ${E[2]} ${plural(E[2], ['общая строфа или абзац', 'общие строфы или абзацы', 'общих строф или абзацев'])}.`;
})();
seg($('#seg-ppmode'),[['all','стихи и проза'],['poems','стихи'],['prose','проза']],PP.mode,v=>{ PP.mode=v; PP.per=-1; ppApply(); });
(function(){ const h=$('#pp-per'); [[-1,'все годы'],...PER.map((p,i)=>[i,pshort(p)])].forEach(([i,l])=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=l; b.setAttribute('aria-pressed',String(i===PP.per));
  b.addEventListener('click',()=>{ PP.per=i; if(i>=0) PP.mode='poems'; else if(PP.mode==='poems'&&false) PP.mode='all'; $('#seg-ppmode').querySelectorAll('button').forEach((x,j)=>x.setAttribute('aria-pressed',String(['all','poems','prose'][j]===PP.mode))); ppApply(); }); h.appendChild(b); }); })();
(function(){ const g=$('#pp-clusters'); const mk=(i,l)=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.setAttribute('aria-pressed',String(i===PP.cl));
  b.innerHTML=(i>=0?`<i style="background:var(--g${i+1})"></i>`:'')+esc(l); b.addEventListener('click',()=>{ PP.cl=(PP.cl===i&&i>=0)?-1:i; ppApply(); }); g.appendChild(b); };
  mk(-1,'все круги'); PPL.clusters.forEach((c,i)=>mk(i,c.names.join(' · ')+' ('+c.n+')')); })();
/* хордовая диаграмма связей: имена по кругу (сгруппированы по кругам имён), ленты — общие абзацы/строфы.
   chordNet(box, nodes, edges, {pick(i|null), hover(i|null)}) → {apply({foc, sel, on(i), tip(i)})} */
function chordNet(box, NOD, EDG, o){
  const Wd=box.clientWidth||800, mob=innerWidth<600, h=mob?Wd+60:Math.round(Math.min(Wd,760)); const [s,w]=svg(box,h);
  const fs=mob?10.5:11.5, th=mob?8:11, cx=w/2, cy=h/2, R=Math.min(w,h-(mob?60:0))/2-(mob?54:92), N=NOD.length, TAU=2*Math.PI;
  const P=(a,r)=>[cx+r*Math.cos(a),cy+r*Math.sin(a)], f1=v=>v.toFixed(1);
  // связи сети + у каждого имени его ближайшие соседи (nb): иначе у редких имён остаётся одна лента
  const EM=new Map(), key=(i,j)=>i<j?i+'_'+j:j+'_'+i; EDG.forEach(([i,j,wt])=>EM.set(key(i,j),[Math.min(i,j),Math.max(i,j),wt]));
  NOD.forEach((n,i)=>(n.nb||[]).forEach(([j,wt])=>{ if(j!==i&&!EM.has(key(i,j))) EM.set(key(i,j),[Math.min(i,j),Math.max(i,j),wt]); }));
  const E2=[...EM.values()];
  const adj=NOD.map(()=>[]); E2.forEach(([i,j,wt])=>{ adj[i].push([j,wt]); adj[j].push([i,wt]); });
  const str=adj.map(a=>a.reduce((t,[,wt])=>t+wt,0)), wOf=i=>Math.max(str[i],1);
  const cls=[...new Set(NOD.map(n=>n.cl))].sort((a,b)=>(a<0)-(b<0)||a-b);
  const order=[]; cls.forEach(c=>NOD.map((_,i)=>i).filter(i=>NOD[i].cl===c).sort((a,b)=>wOf(b)-wOf(a)||NOD[b].n-NOD[a].n).forEach(i=>order.push(i)));
  const gap=cls.length>1?0.03:0, span=TAU-gap*cls.length, tot=order.reduce((t,i)=>t+wOf(i),0);
  const a0=[], a1=[], ang=[]; let a=-Math.PI/2, prev=null;
  order.forEach(i=>{ if(prev!==null&&NOD[i].cl!==prev) a+=gap; prev=NOD[i].cl; const d=span*wOf(i)/tot; a0[i]=a; a1[i]=a+d; ang[i]=a+d/2; a+=d; });
  const dA=(x,y)=>Math.atan2(Math.sin(x-y),Math.cos(x-y));
  const gR=el('g',{},s), gA=el('g',{},s), gL=el('g',{},s);
  // ленты: у каждого имени свой отрезок дуги на каждую связь, по порядку соседей вокруг круга
  const slot={}; NOD.forEach((_,i)=>{ let c=a0[i]; const k=(a1[i]-a0[i])/wOf(i);
    adj[i].slice().sort((p,q)=>dA(ang[q[0]],ang[i])-dA(ang[p[0]],ang[i])).forEach(([j,wt])=>{ slot[i+'_'+j]=[c,c+wt*k]; c+=wt*k; }); });
  const Ri=R-1, arcTo=(x,y)=>`A${f1(Ri)},${f1(Ri)} 0 0 1 ${f1(x)},${f1(y)}`;
  const ribs=E2.map(([i,j,wt])=>{ const [p0,p1]=slot[i+'_'+j], [q0,q1]=slot[j+'_'+i];
    const A0=P(p0,Ri),A1=P(p1,Ri),B0=P(q0,Ri),B1=P(q1,Ri);
    const d=`M${f1(A0[0])},${f1(A0[1])}${arcTo(...A1)}Q${f1(cx)},${f1(cy)} ${f1(B0[0])},${f1(B0[1])}${arcTo(...B1)}Q${f1(cx)},${f1(cy)} ${f1(A0[0])},${f1(A0[1])}Z`;
    return {i,j,wt,p:el('path',{d},gR)}; });
  const arcs=NOD.map((n,i)=>{ const b=Math.max(a1[i]-.0025,a0[i]+.002), big=b-a0[i]>Math.PI?1:0;
    const [x0,y0]=P(a0[i],R),[x1,y1]=P(b,R),[x2,y2]=P(b,R+th),[x3,y3]=P(a0[i],R+th);
    const p=el('path',{d:`M${f1(x0)},${f1(y0)}A${f1(R)},${f1(R)} 0 ${big} 1 ${f1(x1)},${f1(y1)}L${f1(x2)},${f1(y2)}A${f1(R+th)},${f1(R+th)} 0 ${big} 0 ${f1(x3)},${f1(y3)}Z`,
      class:'clickable',tabindex:0,role:'button','aria-label':n.name},gA);
    p.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); o.pick(i); } });
    p.addEventListener('pointerenter',e=>{ if(e.pointerType==='mouse') o.hover(i); }); p.addEventListener('pointerleave',e=>{ if(e.pointerType==='mouse') o.hover(null); });
    return p; });
  // нажатие: по дуге или рядом с кругом — ближайшее имя по углу; в середине круга — снять выбор
  s.addEventListener('click',e=>{ const bb=s.getBoundingClientRect(), k=w/bb.width, x=(e.clientX-bb.left)*k-cx, y=(e.clientY-bb.top)*k-cy, r=Math.hypot(x,y);
    if(r<R*.72){ o.pick(null); return; } const t=Math.atan2(y,x); let best=null, bd=9;
    order.forEach(i=>{ const d=Math.max(0,Math.abs(dA(t,ang[i]))-(a1[i]-a0[i])/2); if(d<bd){ bd=d; best=i; } });
    o.pick(best); });
  const col=c=>c<0?css('--neutral-bar'):css('--g'+(c+1));
  const LBL='font-family:var(--f-body);pointer-events:none;paint-order:stroke;stroke-width:3px;stroke:'+css('--surface')+`;font-size:${fs}px`;
  function apply({foc,sel,on,tip}){
    const nb=new Set(); if(foc!=null){ nb.add(foc); adj[foc].forEach(([j])=>nb.add(j)); }
    ribs.forEach(r=>{ const both=on(r.i)&&on(r.j), isF=foc!=null&&(r.i===foc||r.j===foc);
      const c=isF?NOD[r.i===foc?r.j:r.i].cl:(NOD[r.i].n>=NOD[r.j].n?NOD[r.i].cl:NOD[r.j].cl);
      r.p.setAttribute('fill',col(c)); r.p.style.opacity=!both?.03:(foc==null?.42:(isF?.85:.04)); if(isF) gR.appendChild(r.p); });
    arcs.forEach((p,i)=>{ p.setAttribute('fill',col(NOD[i].cl)); p.style.opacity=!on(i)?.15:(foc!=null&&!nb.has(i)?.3:1);
      p.setAttribute('stroke',i===sel?css('--ink'):'none'); p.setAttribute('stroke-width',1.5); p.setAttribute('data-tip',tip(i)); });
    // подписи: сначала выбранное имя и его соседи, потом самые связанные; на телефоне при выборе — только соседи
    gL.innerHTML=''; const shown=[], minGap=(fs+1)/(R+th);
    const pri=i=>(i===foc?2e9:0)+(nb.has(i)?1e9:0)+wOf(i);
    order.slice().sort((x,y)=>pri(y)-pri(x)).forEach(i=>{ if(!on(i)&&i!==foc) return; if(foc!=null&&mob&&!nb.has(i)) return;
      if(shown.some(t=>Math.abs(dA(t,ang[i]))<minGap)) return; shown.push(ang[i]);
      const t=ang[i], left=Math.cos(t)<0, [x,y]=P(t,R+th+5);
      const dx=Math.cos(t), dy=Math.sin(t), room=Math.min(dx>.01?(w-x)/dx:dx<-.01?x/-dx:1e9, dy>.01?(h-y)/dy:dy<-.01?y/-dy:1e9)-4;
      let nm=NOD[i].name; const maxc=Math.floor(room/(fs*.56)); if(nm.length>maxc) nm=maxc>3?nm.slice(0,maxc-1)+'…':'';
      if(!nm) return; const deg=t*180/Math.PI;
      const tx=txt(gL,f1(x),f1(y),nm,{'text-anchor':left?'end':'start','dominant-baseline':'middle',transform:`rotate(${f1(left?deg+180:deg)} ${f1(x)} ${f1(y)})`,style:LBL});
      tx.style.fill=css('--ink'); tx.style.fontWeight=i===foc?'700':'400'; tx.style.opacity=foc!=null&&!nb.has(i)?.35:1; });
  }
  return {apply};
}
function drawNet(){
  PP.N=chordNet($('#c-net'),PN,PPL.edges,{pick:i=>{ PP.sel=(i==null||PP.sel===i)?null:i; ppApply();  },hover:i=>{ PP.hov=i; ppApply(); }});
  ppApply();
}
function ppApply(){
  document.querySelectorAll('#pp-per button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===PP.per)));
  document.querySelectorAll('#pp-clusters button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===PP.cl)));
  if(PP.N){ const foc=PP.hov!=null?PP.hov:PP.sel;
    PP.N.apply({foc,sel:PP.sel,on:i=>ppCount(PN[i])>0&&(PP.cl<0||PN[i].cl===PP.cl),tip:i=>`${esc(PN[i].name)}<br>в стихах ${fmt(PN[i].np)}, в прозе ${fmt(PN[i].nr)} (упоминаний)<br>нажмите, чтобы открыть карточку`}); }
  ppCard();
}
function ppFindIdx(name){ return PN.findIndex(n=>n.name===name); }
function ppCard(){
  const host=$('#pp-card'); const sel=PP.sel!=null?PN[PP.sel]:PP.other;
  if(!sel){ host.innerHTML=`<div class="eyebrow">Карточка</div><div class="ttl">Выберите имя</div><p class="muted" style="font-size:14.5px">Нажмите на имя на круге или найдите человека по имени. Цвет — круг имён, которые чаще встречаются вместе. Ленты — общая строфа или абзац: чем шире лента, тем чаще. Длина дуги — сколько у имени таких общих мест.</p>`; return; }
  const nbs=(sel.nb||[]).map(([j,w])=>({label:PN[j].name+' · '+w,fn:()=>{ PP.other=null; PP.sel=j; ppApply(); }}));
  const yrs=sel.y0?(sel.y0===sel.y1?String(sel.y0):sel.y0+'–'+sel.y1):'';
  entityCard(host,{eyebrow:'Карточка лица',title:sel.name,meta:(KINDN[sel.kind]||'')+(yrs?' · в стихах '+yrs+' годов':''),
    tiles:[[fmt(sel.np),plural(sel.np,['упоминание в стихах','упоминания в стихах','упоминаний в стихах'])],[fmt(sel.nr),'в прозе'],[fmt(sel.poems),plural(sel.poems, ['стихотворение', 'стихотворения', 'стихотворений'])],[fmt(sel.essays),plural(sel.essays, ['прозаический текст', 'прозаических текста', 'прозаических текстов'])],[fmt(sel.texts),plural(sel.texts,['текст всего','текста всего','текстов всего'])],[sel.i!=null?fmt(sel.nb.length):'—','ближайших имён']],
    per:sel.per,chips:nbs,chipsTitle:'Чаще всего рядом (сколько общих строф или абзацев)',ctx:sel.ctx,word:sel.name,
    note:sel.i==null?'Это имя не попало в сеть: оно встречается реже, чем у 120 самых упоминаемых.':''});
}
PP.other=null;
function ppSelectByName(name){ const i=ppFindIdx(name); if(i>=0){ PP.other=null; PP.sel=i; } else { const o=POTH.find(x=>x.name===name); if(o){ PP.sel=null; PP.other=o; } } ppApply(); }
(function(){ const inp=$('#pp-find'), sug=$('#pp-sug');
  const upd=()=>{ const q=norm(inp.value); sug.innerHTML=''; if(!q) return; const m=PPALL.filter(x=>norm(x.name).startsWith(q)).slice(0,8);
    m.forEach(x=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=x.name; b.addEventListener('click',()=>{ inp.value=x.name; sug.innerHTML=''; ppSelectByName(x.name); }); sug.appendChild(b); });
    if(m.length===1&&norm(m[0].name)===q) ppSelectByName(m[0].name); };
  inp.addEventListener('input',upd); inp.addEventListener('keydown',e=>{ if(e.key==='Enter'){ const q=norm(inp.value); const m=PPALL.find(x=>norm(x.name).startsWith(q)); if(m){ ppSelectByName(m.name); sug.innerHTML=''; } } }); })();
chart(drawNet,$('#c-net'));
/* рейтинги и когда кого упоминали */
(function(){
  const rows=(arr,f)=>arr.filter(x=>f(x)>0).slice(0,15).map(x=>({l:x.name,v:f(x),k:x.name,tip:`${esc(x.name)}: стихотворений ${fmt(x.poems)}, прозаических текстов ${fmt(x.essays)}<br>упоминаний: в стихах ${fmt(x.np)}, в прозе ${fmt(x.nr)}<br>нажмите, чтобы открыть карточку`}));
  const bp=[...PPALL].sort((a,b)=>b.poems-a.poems||b.np-a.np), br=[...PPALL].sort((a,b)=>b.essays-a.essays||b.nr-a.nr);
  const open=r=>{ ppSelectByName(r.k); goTo('personazhi'); };
  hbars($('#c-pp-poems'),rows(bp,x=>x.poems),{color:'var(--s1)',labelW:110,rowH:22,fmtv:fmt,onClick:open});
  hbars($('#c-pp-prose'),rows(br,x=>x.essays),{color:'var(--s2)',labelW:110,rowH:22,fmtv:fmt,onClick:open});
  const hp=[...PPALL].sort((a,b)=>b.np-a.np).slice(0,20);
  heatTable($('#c-pp-heat'),hp.map(x=>x.name),PSH,hp.map(x=>x.per.slice(0,6)),{labelW:120,cellH:24,fmtv:v=>v?fmt(Math.round(v)):'',tipf:(i,j)=>`${esc(hp[i].name)} · ${PER[j]}: ${pn(hp[i].per[j],['упоминание в стихах','упоминания в стихах','упоминаний в стихах'])}`,onRow:i=>{ ppSelectByName(hp[i].name); goTo('personazhi'); }});
  const all=[...PPALL].sort((a,b)=>a.name.localeCompare(b.name,'ru'));
  $('#pp-all-n').textContent=fmt(all.length);
  $('#pp-all').addEventListener('toggle',function(){ if(!this.open||$('#pp-allchips').childElementCount) return; const h=$('#pp-allchips');
    all.forEach(x=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=x.name+' · '+x.n; b.addEventListener('click',()=>{ ppSelectByName(x.name); goTo('personazhi'); }); h.appendChild(b); }); });
})();

/* ================= места ================= */
const PL=WD.places;
(function(){
  const NP_=PL.named; const bp=[...NP_].sort((a,b)=>b.poems-a.poems||b.np-a.np), br=[...NP_].sort((a,b)=>b.essays-a.essays||b.nr-a.nr);
  const top=(arr,f,n)=>arr.filter(x=>f(x)>0).slice(0,n).map(x=>x.name).join(', ');
  $('#f-place').textContent=`Бродский называет ${fmt(PL.total_named)} ${plural(PL.total_named, ['место', 'места', 'мест'])}: города, страны, реки, моря. Больше всего стихотворений, где они названы: ${top(bp,x=>x.poems,5)}. В прозе, по числу текстов: ${top(br,x=>x.essays,5)}.`;
  const pick=o=>{ entityCard($('#pl-card'),{eyebrow:'Карточка места',title:o.name,meta:o.y0?'в стихах '+(o.y0===o.y1?o.y0:o.y0+'–'+o.y1)+' годов':'',
    tiles:[[fmt(o.np),plural(o.np,['упоминание в стихах','упоминания в стихах','упоминаний в стихах'])],[fmt(o.nr),'в прозе'],[fmt(o.poems),plural(o.poems, ['стихотворение', 'стихотворения', 'стихотворений'])],[fmt(o.essays),plural(o.essays, ['прозаический текст', 'прозаических текста', 'прозаических текстов'])],[fmt(o.texts),plural(o.texts,['текст всего','текста всего','текстов всего'])],[fmt(o.n),plural(o.n,RUF.mention)]],per:o.per,ctx:o.ctx,word:o.name,color:'var(--s2)'}); };
  const tp=[...NP_].sort((a,b)=>b.texts-a.texts||b.n-a.n).slice(0,20);
  hbars($('#c-pl-top'),tp.map(x=>({l:x.name,v:x.texts,k:x.name,tip:`${esc(x.name)}: ${pn(x.texts,RUF.text)}; в стихах ${fmt(x.np)}, в прозе ${pn(x.nr,RUF.mention)}<br>нажмите, чтобы открыть карточку`})),{color:'var(--s2)',labelW:120,rowH:22,fmtv:fmt,onClick:r=>pick(NP_.find(x=>x.name===r.k))});
  table($('#c-pl-top'),['Место','Текстов','В стихах','В прозе'],tp.map(x=>[x.name,x.texts,x.np,x.nr]));
  const hp=[...NP_].sort((a,b)=>b.np-a.np).slice(0,16);
  heatTable($('#c-pl-heat'),hp.map(x=>x.name),PSH,hp.map(x=>x.per.slice(0,6)),{labelW:120,cellH:24,fmtv:v=>v?fmt(Math.round(v)):'',tipf:(i,j)=>`${esc(hp[i].name)} · ${PER[j]}: ${pn(hp[i].per[j],['упоминание в стихах','упоминания в стихах','упоминаний в стихах'])}`,onRow:i=>pick(hp[i])});
  pick(bp[0]&&bp[0].np>=1?NP_.find(x=>x.name==='Рим')||bp[0]:NP_[0]);
})();

/* ================= полки: места вообще, транспорт, еда, напитки ================= */
const SHELF_NOTE='Слова считаются по начальной форме; если форма совпадает с другим словом («виски» — напиток или височки, «паром» — паром или пар), слово в подсчёт не входит. Поэтому числа — нижняя оценка. Слов, которых нет в списке, здесь нет.';
function shelf(hostId,groups,{noun,unit,findId,extra=null}){
  const host=document.getElementById(hostId); const G=groups; const col=i=>'var(--g'+(i+1)+')';
  const all=G.flatMap((g,gi)=>g.items.map(it=>({...it,g:g.g,gi})));
  const total=all.reduce((a,b)=>a+b.n,0);
  const byP=[...all].sort((a,b)=>b.np-a.np), byR=[...all].sort((a,b)=>b.nr-a.nr);
  const topN=(arr,f,n)=>arr.filter(x=>f(x)>0).slice(0,n).map(x=>`${x.w} (${f(x)})`).join(', ');
  const fid=document.getElementById(findId); if(fid) fid.textContent=`В текстах Бродского нашлось ${fmt(all.length)} ${plural(all.length, ['слово', 'слова', 'слов'])} из этой темы, всего ${fmt(total)} ${plural(total, ['упоминание', 'упоминания', 'упоминаний'])}. В стихах чаще всего: ${topN(byP,x=>x.np,5)}. В прозе: ${topN(byR,x=>x.nr,5)}.${extra?' '+extra(all):''}`;
  host.innerHTML=`<div class="shelf"><div class="shelf-main"><div class="shelf-groups" id="${hostId}-g"></div></div><aside class="card shelf-card" id="${hostId}-card" aria-live="polite"></aside></div>
    <div class="panel"><div class="cap"><span class="t">Как менялись эти слова в стихах</span><span class="u">упоминаний на 10 000 слов, по группам</span></div><div class="legend" id="${hostId}-leg"></div><div class="chart" id="${hostId}-chart"></div></div>
    <div class="panel"><div class="cap"><span class="t">Редкие гости</span><span class="u">слова, которые встречаются один или два раза; наведите, чтобы увидеть строку</span></div><div class="chips" id="${hostId}-rare"></div></div>
    <p class="muted" style="font-size:13.5px">${SHELF_NOTE}</p>`;
  const card=document.getElementById(hostId+'-card');
  const show=it=>{ const sibs=G[it.gi].items.filter(x=>x.w!==it.w).slice(0,8).map(x=>({label:x.w+' · '+x.n,fn:()=>show({...x,g:it.g,gi:it.gi})}));
    entityCard(card,{eyebrow:'Карточка слова',title:it.w,meta:it.g+' · в '+fmt(it.texts)+' '+plural(it.texts, ['тексте', 'текстах', 'текстах']),tiles:[[fmt(it.n),plural(it.n, ['упоминание', 'упоминания', 'упоминаний'])],[fmt(it.np),'в стихах'],[fmt(it.nr),'в прозе']],per:it.per,chips:sibs,chipsTitle:'Из той же группы',ctx:it.ctx,word:it.w,color:col(it.gi)}); };
  const gh=document.getElementById(hostId+'-g');
  G.forEach((g,gi)=>{ const mx=Math.max(...g.items.map(i=>i.n)); const div=document.createElement('div'); div.className='sh-group';
    const rates=g.per.slice(0,6).map((v,i)=>per10k(v,i));
    div.innerHTML=`<div class="sh-h"><span class="sw" style="background:${col(gi)}"></span><b>${esc(g.g)}</b><span class="muted">${fmt(g.n)}</span></div><div class="sh-spark">${sparkSVG(rates,{h:40,color:col(gi)})}</div><ul class="sh-list"></ul>`;
    const ul=div.querySelector('ul'); const LIM=8; const draw=(more)=>{ ul.innerHTML=''; g.items.slice(0,more?g.items.length:LIM).forEach(it=>{ const li=document.createElement('li');
      li.innerHTML=`<button type="button" data-tip="${esc(it.w)}: ${fmt(it.np)} в стихах, ${fmt(it.nr)} в прозе">${esc(it.w)}</button><span class="b"><i style="width:${100*it.np/mx}%;background:${col(gi)}"></i><i style="width:${100*it.nr/mx}%;background:${col(gi)};opacity:.4"></i></span><span class="n">${fmt(it.n)}</span>`;
      li.querySelector('button').addEventListener('click',()=>{ show({...it,g:g.g,gi}); if(matchMedia('(max-width:999px)').matches) card.scrollIntoView({behavior:calmMotion()?'auto':'smooth',block:'nearest'}); }); ul.appendChild(li); });
      if(g.items.length>LIM){ const li=document.createElement('li'); li.className='more'; li.innerHTML=`<button type="button">${more?'свернуть':'ещё '+(g.items.length-LIM)}</button>`; li.querySelector('button').addEventListener('click',()=>draw(!more)); ul.appendChild(li); } };
    draw(false); gh.appendChild(div); });
  // динамика по группам
  const rowsP=PER.map((p,pi)=>({p,pi,parts:G.map((g,gi)=>({gi,g:g.g,v:per10k(g.per[pi],pi),c:g.per[pi]}))}));
  document.getElementById(hostId+'-leg').innerHTML=G.map((g,gi)=>`<span><i style="background:${col(gi)}"></i>${esc(g.g)}</span>`).join('');
  chart(()=>{ const box=document.getElementById(hostId+'-chart'); const rowH=34,L=86,R=44,T=6,Bm=24; const h=T+rowH*rowsP.length+Bm; const [s,w]=svg(box,h);
    const mx=niceMax(Math.max(...rowsP.map(r=>r.parts.reduce((a,b)=>a+b.v,0)),1e-9)); const sx=v=>L+(w-L-R)*v/mx; const ax=el('g',{class:'ax'},s);
    ticks(mx,4).forEach(t=>{ el('line',{x1:sx(t),x2:sx(t),y1:T,y2:h-Bm,stroke:css('--grid')},ax); txt(ax,sx(t),h-8,fmt1(t),{'text-anchor':'middle'}); });
    rowsP.forEach((r,i)=>{ const y=T+i*rowH; txt(s,L-8,y+rowH/2+2,pshort(r.p),{'text-anchor':'end',style:'fill:var(--ink)'}); let x=sx(0);
      r.parts.forEach(pt=>{ const ww=sx(pt.v)-sx(0); if(ww<=0) return; el('rect',{x:x+1,y:y+4,width:Math.max(0,ww-2),height:rowH-10,rx:2,fill:css('--g'+(pt.gi+1)),'data-tip':`${esc(r.p)} · ${esc(pt.g)}: ${fmt1(pt.v)} на 10 000 слов (${pn(pt.c,RUF.mention)})`},s); x+=ww; });
      const tot=r.parts.reduce((a,b)=>a+b.v,0); txt(s,sx(tot)+6,y+rowH/2+3,fmt1(tot)); });
  },document.getElementById(hostId+'-chart'));
  table(document.getElementById(hostId+'-chart'),['Период',...G.map(g=>g.g)],rowsP.map(r=>[r.p,...r.parts.map(p=>+p.v.toFixed(1))]));
  // редкие
  const rare=all.filter(x=>x.n<=2).sort((a,b)=>a.w.localeCompare(b.w,'ru')); const rh=document.getElementById(hostId+'-rare');
  rare.forEach(it=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=it.w; const c=it.ctx[0]; b.setAttribute('data-tip',c?`«${esc(c.s.slice(0,110))}»<br>${esc(tidy(c.t))}${c.y?', '+c.y:''}`:esc(it.w));
    b.addEventListener('click',()=>{ show(it); card.scrollIntoView({behavior:calmMotion()?'auto':'smooth',block:'nearest'}); }); rh.appendChild(b); });
  if(!rare.length) rh.innerHTML='<span class="muted">Таких слов нет.</span>';
  show(all.sort((a,b)=>b.n-a.n)[0]);
}
shelf('sh-places',PL.generic,{findId:'f-places2'});
shelf('sh-transport',WD.transport,{findId:'f-transport'});
shelf('sh-food',WD.food,{findId:'f-food'});
shelf('sh-drinks',WD.drinks,{findId:'f-drinks',extra:all=>{ const g=all.find(x=>x.w==='граппа'); const d=all.find(x=>x.w==='водка'), v=all.find(x=>x.w==='вино');
  return (v&&d?`Вина (${v.n}) втрое чаще, чем водки (${d.n}). `:'')+(g?`Граппа встречается ${g.n} ${plural(g.n, ['раз', 'раза', 'раз'])}, оба — в «${g.ctx[0].t}».`:''); }});
[`Персонажи и места найдены автоматически. Имя — это слово с заглавной буквы внутри фразы (в стихах с заглавной в начале каждой строки начало строки не считается), у которого не меньше 70% написаний с заглавной. Лицо или место определяется по разбору pymorphy3 и по соседям: рядом с именем или инициалами — лицо, после предлога «в», «на», «из» — место. Ручных отборов нет, кроме коротких исправлений: склеены написания одного человека («Харди» и «Гарди», «Уистан» и «Оден»), убраны праздники, названия книг и сам автор, Гомер отнесён к лицам.`,
 `Связь между двумя лицами в сети — они названы в одной строфе стихотворения (стихи без пустых строк режутся по 12 строк) или в одном абзаце прозы. Круги имён найдены спектральной кластеризацией по этим связям. Расположение узлов рассчитано силовой раскладкой: рядом стоят те, кого часто называют вместе. В сеть входят 120 самых упоминаемых, остальные лица есть в поиске.`,
 `Слова для мест, транспорта, еды и напитков берутся из списков, которые я составил; в текстах считаются те слова, что там нашлись. Слова с частым другим значением в списки не вошли («виски» — височки, «паром» — пар, «угол», «камера», «рынок»). Слово считается, если его начальная форма совпадает; форма, похожая на другое слово («парка» — парк или куртка), не засчитывается, поэтому числа — нижняя оценка. Слова, которых нет в списках, не найдены; проверка на пропуски делалась по строкам, но полноты не гарантирует.`]
 .forEach(t=>$('#method').insertAdjacentHTML('beforeend',`<li>${t}</li>`));
