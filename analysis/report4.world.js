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
function drawNet(){
  const box=$('#c-net'); const W=box.clientWidth||800; const h=Math.round(Math.min(780,Math.max(480,W*0.76))); const [s,w]=svg(box,h);
  const padX=W<600?24:56, padY=36; const xs=PN.map(n=>n.x), ys=PN.map(n=>n.y); const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  const X=x=>padX+(w-2*padX)*(x-x0)/(x1-x0), Y=y=>padY+(h-2*padY)*(y-y0)/(y1-y0);
  const gE=el('g',{},s), gN=el('g',{},s), gL=el('g',{},s);
  const edges=PPL.edges.map(([i,j,wt])=>({i,j,wt,l:el('line',{x1:X(PN[i].x),y1:Y(PN[i].y),x2:X(PN[j].x),y2:Y(PN[j].y),'stroke-linecap':'round'},gE)}));
  const nodes=PN.map((n,i)=>{ const c=el('circle',{cx:X(n.x),cy:Y(n.y),r:5,class:'clickable',tabindex:0,role:'button','aria-label':n.name},gN);
    const t=txt(gL,X(n.x),Y(n.y)-9,n.name,{'text-anchor':'middle',style:'font-family:var(--f-body);font-size:12px;pointer-events:none;paint-order:stroke;stroke:'+css('--surface')+';stroke-width:3px'});
    const pick=()=>{ PP.sel=(PP.sel===i)?null:i; ppApply(); };
    c.addEventListener('click',pick); c.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); pick(); } });
    c.addEventListener('pointerenter',e=>{ if(e.pointerType==='mouse'){ PP.hov=i; ppApply(); } }); c.addEventListener('pointerleave',e=>{ if(e.pointerType==='mouse'){ PP.hov=null; ppApply(); } });
    return {n,c,t,X:X(n.x),Y:Y(n.y)}; });
  PP.N={edges,nodes,w,h}; ppApply();
}
function ppApply(){
  document.querySelectorAll('#pp-per button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===PP.per)));
  document.querySelectorAll('#pp-clusters button').forEach((b,j)=>b.setAttribute('aria-pressed',String(j-1===PP.cl)));
  if(PP.N){ const {edges,nodes}=PP.N; const foc=PP.hov!=null?PP.hov:PP.sel;
    const nb=new Set(); if(foc!=null){ nb.add(foc); PPL.edges.forEach(([i,j])=>{ if(i===foc) nb.add(j); if(j===foc) nb.add(i); }); }
    const cnt=nodes.map(o=>ppCount(o.n)), sz=nodes.map(o=>ppSize(o.n)), mx=Math.max(...sz,1);
    const placed=[]; const fit=b=>!placed.some(q=>b.x<q.x+q.w&&b.x+b.w>q.x&&b.y<q.y+q.h&&b.y+b.h>q.y);
    const order=nodes.map((_,i)=>i).sort((a,b)=>((b===foc||nb.has(b))?1e6:0)+sz[b]-(((a===foc||nb.has(a))?1e6:0)+sz[a]));
    nodes.forEach((o,i)=>{ const on=cnt[i]>0&&(PP.cl<0||o.n.cl===PP.cl); const dim=!on||(foc!=null&&!nb.has(i));
      const r=on?3.5+9*Math.sqrt(sz[i]/mx):3; o.r=r;
      o.c.setAttribute('r',r.toFixed(1)); o.c.setAttribute('fill',clCol(o.n.cl)); o.c.setAttribute('stroke',css('--surface')); o.c.setAttribute('stroke-width',i===PP.sel?3:1.5);
      o.c.style.opacity=on?(dim?.18:.92):.1; o.c.style.stroke=i===foc?css('--ink'):css('--surface');
      o.c.setAttribute('data-tip',`${esc(o.n.name)}<br>в стихах ${fmt(o.n.np)}, в прозе ${fmt(o.n.nr)} (упоминаний)<br>нажмите, чтобы открыть карточку`); });
    order.forEach(i=>{ const o=nodes[i]; const on=cnt[i]>0&&(PP.cl<0||o.n.cl===PP.cl); const forced=i===foc||nb.has(i);
      const fs=12, bw=o.n.name.length*fs*0.56+6, bx={x:o.X-bw/2,y:o.Y-o.r-fs-4,w:bw,h:fs+3}; const show=on&&(forced||(sz[i]>=2&&fit(bx)));
      if(show) placed.push(bx); o.t.setAttribute('y',(o.Y-o.r-4).toFixed(1)); o.t.style.opacity=show?((foc!=null&&!forced)?.25:1):0; o.t.style.fontWeight=i===foc?'700':'400'; });
    edges.forEach(e=>{ const a=nodes[e.i], b=nodes[e.j]; const bothOn=cnt[e.i]>0&&cnt[e.j]>0&&(PP.cl<0||(PN[e.i].cl===PP.cl&&PN[e.j].cl===PP.cl));
      const isF=foc!=null&&(e.i===foc||e.j===foc);
      e.l.setAttribute('stroke',isF?css('--mark'):css('--axis')); e.l.setAttribute('stroke-width',isF?(1.2+.5*Math.sqrt(e.wt)).toFixed(1):(.5+.35*Math.sqrt(e.wt)).toFixed(1));
      e.l.style.opacity=!bothOn?0:(foc!=null?(isF?.9:.05):.5); }); }
  ppCard();
}
function ppFindIdx(name){ return PN.findIndex(n=>n.name===name); }
function ppCard(){
  const host=$('#pp-card'); const sel=PP.sel!=null?PN[PP.sel]:PP.other;
  if(!sel){ host.innerHTML=`<div class="eyebrow">Карточка</div><div class="ttl">Выберите имя</div><p class="muted" style="font-size:14.5px">Нажмите на кружок в сети или найдите человека по имени. Размер кружка — в скольких текстах он назван. Цвет — круг имён, которые чаще встречаются вместе. Линии — общая строфа или абзац.</p>`; return; }
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
