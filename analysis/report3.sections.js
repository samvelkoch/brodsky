/* ================= новые разделы: размер, рифма, фраза, звук, карта словаря, переломы, мифы ================= */
const pidTitle = pid => PS[pid] ? `«${tidy(PS[pid].t)}», ${PS[pid].y||'без даты'}` : '';
function accHTML(a){ a=a.replace(/^[\s\-–—]+|[\s\-–—]+$/g,''); let out=''; for(let i=0;i<a.length;i++){ const ch=a[i]; if(ch==='+'){ const v=a[i+1]||''; out+=`<b class="st">${esc(v)}</b>`; i++; } else out+=esc(ch); } return out.replace(/--/g,'—'); }
function legendTo(host, items){ host.innerHTML=items.map(([l,c])=>`<span><i style="background:${c}"></i>${l}</span>`).join(''); }
function stacked100(box, rows, {rowH=32, labelW=80, fmtv=v=>Math.round(v)+'%'}={}){
  return chart(()=>{ const h=rows.length*rowH+6; const [s,w]=svg(box,h); const W=w-labelW-4;
    rows.forEach((r,i)=>{ const y=i*rowH+3; const tot=r.parts.reduce((a,p)=>a+p.v,0)||1; let x=labelW;
      txt(s,labelW-10,y+(rowH-8)/2+4,r.l,{'text-anchor':'end',style:'fill:var(--ink)'});
      r.parts.forEach(p=>{ const ww=W*p.v/tot; if(ww<=0) return; const col=css(p.c.replace(/var\((.*)\)/,'$1'))||p.c;
        el('rect',{x:x+1,y,width:Math.max(0,ww-2),height:rowH-8,rx:2,fill:col,'data-tip':`${esc(r.full||r.l)} · ${esc(p.k)}: ${fmt1(p.v)}%${p.tip?'<br>'+p.tip:''}`},s);
        if(ww>=34){ const ink=lum(col)<0.36?'#ffffff':'#15161a'; txt(s,x+ww/2,y+(rowH-8)/2+4,fmtv(p.v),{'text-anchor':'middle',style:`pointer-events:none;font-size:11px;fill:${ink}`}); }
        x+=ww; }); });
  }, box);
}
const C4 = ['var(--s1)','var(--s2)','var(--c3)','var(--c4)'];

/* ---------- размер ---------- */
const MDEF = {
  'ямб':['та-ТА','Ударение на каждом втором слоге, начиная со второго. Самый частый размер русской поэзии: «Мой дядя самых честных правил».'],
  'хорей':['ТА-та','Ударение на каждом втором слоге, начиная с первого. Песенный, «плясовой» размер: «Буря мглою небо кроет».'],
  'дактиль':['ТА-та-та','Ударение через два слога, начиная с первого. Размер плавный, раскачивающийся.'],
  'амфибрахий':['та-ТА-та','Ударение через два слога, начиная со второго. Балладный размер.'],
  'анапест':['та-та-ТА','Ударение через два слога, начиная с третьего. Им написано знаменитое «Ни страны, ни погоста…».'],
  'дольник':['та-ТА-та-та-ТА-та-ТА','Между ударениями то один, то два безударных слога. Ритм «с запинкой» — главный размер русской поэзии XX века.'],
  'тактовик':['та-ТА-та-та-та-ТА','Между ударениями от одного до трёх слогов: ещё свободнее дольника, но ударения всё равно считаются.'],
  'свободный':['—','Постоянного промежутка между ударениями нет, строка держится на интонации и синтаксисе. У Бродского это чаще всего длинные «разговорные» строки.'],
};
const MFAM = [['двусложные: ямб, хорей',['ямб','хорей'],'var(--s1)'],['трёхсложные: дактиль, амфибрахий, анапест',['дактиль','амфибрахий','анапест'],'var(--s2)'],
  ['дольник и тактовик',['дольник','тактовик'],'var(--c3)'],['свободный стих',['свободный'],'var(--c4)']];
(function(){
  const g=$('#meter-gloss'); const EXM=VS.examples.meter;
  g.insertAdjacentHTML('beforeend',`<div class="term"><h3>Стопа</h3><p class="what">Повторяющийся кусок ритма: одно ударение и безударные слоги при нём. «Пятистопный ямб» — строка из пяти пар «та-ТА»: <span class="mono">та-ТА-та-ТА-та-ТА-та-ТА-та-ТА</span>. Пропуск ударения на сильном месте нормален и не ломает размер.</p></div>`);
  Object.keys(MDEF).forEach(m=>{ const [sch,what]=MDEF[m]; const ex=(EXM[m]||[]).slice(0,2);
    g.insertAdjacentHTML('beforeend',`<div class="term"><h3>${m==='свободный'?'Свободный стих':m[0].toUpperCase()+m.slice(1)} <span class="mono" style="font-size:13px;color:var(--muted)">${sch}</span></h3><p class="what">${what}</p>${
      ex.map(([a,pat,pid])=>`<div class="ex">${accHTML(a)}</div><div class="pat">${esc(pat)}</div><div class="src">${esc(pidTitle(pid))}</div>`).join('')||'<p class="muted">Пример не найден.</p>'}</div>`); });
  const B=VS.meter.by_period; const fam=r=>MFAM.map(([l,ks])=>ks.reduce((a,k)=>a+(r[k]||0),0));
  const f0=fam(B[1]), fL=fam(B[5]);
  $('#f-meter').textContent=`В 1961–1966 годах ${Math.round(f0[0])}% строк написаны ямбом или хореем, а дольником и тактовиком — ${Math.round(f0[2])}%. В 1990-е соотношение ${Math.round(fL[0])}% к ${Math.round(fL[2])}%, свободного стиха — ${Math.round(fL[3])}%.`;
  legendTo($('#meter-legend'),MFAM.map(([l,,c])=>[l,c]));
  stacked100($('#c-meter'),B.map((r,i)=>({l:PSH[i],full:PER[i],parts:MFAM.map(([l,ks,c])=>({k:l,v:ks.reduce((a,k)=>a+(r[k]||0),0),c,tip:ks.map(k=>`${k}: ${fmt1(r[k]||0)}%`).join(', ')}))})));
  table($('#c-meter'),['Период',...VS.meter.keys,'строк'],B.map((r,i)=>[PER[i],...VS.meter.keys.map(k=>r[k]),r.n]));
  hbars($('#c-feet'),VS.meter.feet.map(([l,n])=>({l,v:n})),{labelW:230,rowH:22,fmtv:fmt,color:'var(--s1)'});
})();

/* ---------- рифма ---------- */
(function(){
  const R=VS.rhyme, E=VS.examples.rhyme, g=$('#rhyme-gloss');
  const pairs=(lst,k=3)=>(lst||[]).slice(0,k).map(([a,b,pid])=>`<div class="pair">${esc(a)}<i>—</i>${esc(b)}</div><div class="src">${esc(pidTitle(pid))}</div>`).join('');
  const TERMS=[['Точная рифма','Звуки совпадают полностью, начиная с последнего ударного гласного.','точная'],
    ['Неточная рифма','Совпадает ударный гласный и почти все согласные: одна согласная лишняя, пропущенная или другая. Бродский пользуется такой рифмой очень свободно.','неточная'],
    ['Созвучие','Совпадает ударный гласный и что-то рядом, но меньше, чем в неточной рифме. На слух рифма есть, на бумаге — едва.','созвучие'],
    ['Мужская рифма','Ударение на последнем слоге строки. Звучит твёрдо, «с точкой».','мужская'],
    ['Женская рифма','Ударение на предпоследнем слоге: после ударного есть ещё один безударный.','женская'],
    ['Дактилическая рифма','Ударение на третьем слоге от конца: после ударного ещё два безударных.','дактилическая']];
  TERMS.forEach(([h,what,k])=>g.insertAdjacentHTML('beforeend',`<div class="term"><h3>${h}</h3><p class="what">${what}</p>${pairs(E[k])||'<p class="muted">Пример не найден.</p>'}</div>`));
  const rich=(VS.rhyme_examples.rich||[]).slice(0,3), comp=(VS.rhyme_examples.compound||[]).slice(0,3);
  g.insertAdjacentHTML('beforeend',`<div class="term"><h3>Богатая рифма</h3><p class="what">Точная рифма, в которой совпадает ещё и согласная перед ударным гласным. Звучит особенно «плотно».</p>${rich.map(([a,b,pid])=>`<div class="pair">${esc(a)}<i>—</i>${esc(b)}</div><div class="src">${esc(pidTitle(pid))}</div>`).join('')}</div>`);
  g.insertAdjacentHTML('beforeend',`<div class="term"><h3>Составная рифма</h3><p class="what">С одним словом рифмуются два: окончание распадается на слово и безударное словечко после него.</p>${comp.map(([a,b,pid])=>`<div class="pair">${esc(a)}<i>—</i>${esc(b)}</div><div class="src">${esc(pidTitle(pid))}</div>`).join('')}</div>`);
  const SC={ABAB:['Перекрёстная рифмовка (АБАБ)','Рифмуются первая строка с третьей, вторая с четвёртой.'],AABB:['Парная рифмовка (ААББ)','Рифмуются соседние строки.'],ABBA:['Опоясывающая рифмовка (АББА)','Крайние строки рифмуются друг с другом, средние — между собой.']};
  const LC={A:'var(--s1)',B:'var(--s2)'};
  Object.entries(SC).forEach(([k,[h,what]])=>{ const ex=VS.examples.scheme[k]; if(!ex) return; const [ws,pid]=ex;
    g.insertAdjacentHTML('beforeend',`<div class="term"><h3>${h}</h3><p class="what">${what} Концы строк настоящего четверостишия:</p><div class="letters">${ws.map((w,i)=>`<span class="L" style="background:${LC[k[i]]}">${k[i]==='A'?'А':'Б'}</span><span>…${esc(w)}</span>`).join('')}</div><div class="src">${esc(pidTitle(pid))}</div></div>`); });
  // выводы
  const T=R.type; const ex=i=>T[i]['точная'], ne=i=>T[i]['неточная']+T[i]['созвучие'], un=i=>T[i]['без рифмы'];
  $('#f-rhyme').textContent=`Точных рифм в 1961–1966 годах — ${Math.round(ex(1))}% строк, в 1990-е — ${Math.round(ex(5))}%. Неточных и созвучий — ${Math.round(ne(1))}% и ${Math.round(ne(5))}%. Без рифмы остаётся ${Math.round(un(1))}% и ${Math.round(un(5))}% строк.`;
  const RT=[['точная','var(--s1)'],['неточная','var(--c3)'],['созвучие','var(--c4)'],['без рифмы','var(--neutral-bar)']];
  legendTo($('#rtype-legend'),RT);
  stacked100($('#c-rtype'),T.map((r,i)=>({l:PSH[i],full:PER[i],parts:RT.map(([k,c])=>({k,v:r[k],c}))})));
  table($('#c-rtype'),['Период','точная','неточная','созвучие','без рифмы','строк'],T.map((r,i)=>[PER[i],r['точная'],r['неточная'],r['созвучие'],r['без рифмы'],r.n]));
  const CL=[['на последний слог (мужская)','var(--s1)',['0']],['на предпоследний (женская)','var(--s2)',['1']],['раньше (дактилическая и дальше)','var(--c3)',['2','3']]];
  legendTo($('#claus-legend'),CL.map(([l,c])=>[l,c]));
  stacked100($('#c-claus'),R.clausula.map((r,i)=>({l:PSH[i],full:PER[i],parts:CL.map(([k,c,ks])=>({k,v:ks.reduce((a,x)=>a+(r[x]||0),0),c}))})));
  const SCH=[['перекрёстная (АБАБ)','var(--s1)'],['парная (ААББ)','var(--s2)'],['опоясывающая (АББА)','var(--c3)'],['другая','var(--c4)'],['без рифмы','var(--neutral-bar)']];
  legendTo($('#sch-legend'),SCH);
  stacked100($('#c-sch'),R.scheme4.map((r,i)=>({l:PSH[i],full:PER[i],parts:SCH.map(([k,c])=>({k,v:r[k],c}))})));
  hbars($('#c-rpairs'),R.top_pairs.slice(0,20).map(([a,b,n])=>({l:`${a} — ${b}`,v:n})),{labelW:190,rowH:22,fmtv:fmt});
  $('#c-rlong').innerHTML=(VS.rhyme_examples.long||[]).slice(0,18).map(([a,b,pid])=>`<button type="button" class="chip-r" data-w="${esc(a)}" data-tip="${esc(pidTitle(pid))}">${esc(a)} — ${esc(b)}</button>`).join('');
  $('#c-rcomp').innerHTML=(VS.rhyme_examples.compound||[]).slice(0,18).map(([a,b,pid])=>`<button type="button" data-w="${esc(a.split(' ')[0])}" data-tip="${esc(pidTitle(pid))}">${esc(a)} — ${esc(b)}</button>`).join('');
  document.querySelectorAll('#c-rlong button,#c-rcomp button').forEach(b=>b.addEventListener('click',()=>{ rdOpen(b.dataset.w); $('#rifma').scrollIntoView({behavior:'smooth'}); }));
})();

/* словарь рифм */
const RD=VS.rhyme_dict; const RDN={}; Object.keys(RD).forEach(k=>{ RDN[norm(k)]=k; });
const RD_KEYS=Object.keys(RDN);
$('#rd-size').textContent=`${fmt(VS.rhyme_dict_size)} слов с рифмой; в словаре — ${fmt(Object.keys(RD).length)} самых рифмуемых`;
function rdOpen(word){
  const k=RDN[norm(word)]; const out=$('#rd-out'); $('#rd-input').value=word;
  if(!k){ out.innerHTML=`<p class="muted">Такого слова нет среди рифмуемых концов строк. Попробуйте другую форму: «ночь», «ночи», «ночью» — это разные рифмы.</p>`; return; }
  const P=RD[k]; const tot=P.reduce((a,x)=>a+x[1],0);
  out.innerHTML=`<div class="big">${esc(k)}</div><p style="margin:0 0 8px">рифмуется ${fmt(tot)} раз; разных партнёров в списке — ${P.length}:</p>
    <div class="rchips">${P.map(([w,n])=>`<button type="button" data-w="${esc(w)}">${esc(w)}<small>${n}</small></button>`).join('')}</div>`;
  out.querySelectorAll('button[data-w]').forEach(b=>b.addEventListener('click',()=>rdOpen(b.dataset.w)));
}
function rdSug(q){ const h=$('#rd-sug'); const nq=norm(q); const L=nq?RD_KEYS.filter(k=>k.startsWith(nq)).slice(0,10).map(k=>RDN[k]):['ночь','меня','век','времени','глаз','тишина','любовь','свет'].filter(w=>RDN[norm(w)]);
  h.innerHTML=L.map(w=>`<button type="button" class="chip" data-w="${esc(w)}">${esc(w)}</button>`).join('');
  h.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>rdOpen(b.dataset.w))); }
$('#rd-input').addEventListener('input',e=>{ const v=e.target.value; if(RDN[norm(v)]) rdOpen(v); rdSug(v); });
rdSug(''); rdOpen(RDN['ночь']?'ночь':RD_KEYS[0]);

/* ---------- перенос и фраза ---------- */
(function(){
  const g=$('#enj-gloss'); const e=VS.examples.enj||[];
  g.insertAdjacentHTML('beforeend',`<div class="term"><h3>Перенос (анжамбеман)</h3><p class="what">Фраза не кончается вместе со строкой и продолжается в следующей. Самый резкий случай — строка обрывается на предлоге или союзе, отрывая его от слова, к которому он относится.</p>${
    e.slice(0,2).map(([a,b,pid])=>`<div class="ex">${esc(a)}<br>${esc(b)}</div><div class="src">${esc(pidTitle(pid))}</div>`).join('')}</div>`);
  g.insertAdjacentHTML('beforeend',`<div class="term"><h3>Фраза через строфу</h3><p class="what">Предложение начинается в одной строфе, а кончается в следующей. Строфа перестаёт быть законченной мыслью и становится просто рамкой.</p></div>`);
  const H=VS.phrase.hist; const keys=Object.keys(H).map(Number).sort((a,b)=>a-b);
  vbars($('#c-shist'),keys.map(k=>({l:k===25?'25+':String(k),v:H[k],tip:`${k===25?'25 и больше':k} строк: ${fmt(H[k])} предложений`})),{h:220,every:4,fmtv:fmt});
  dots($('#c-cross'),VS.phrase.by_period.map((r,i)=>({l:PSH[i],v:r.cross_stanza,tip:`${PER[i]}: ${fmt1(r.cross_stanza)}% предложений переходят в следующую строфу<br>медиана фразы — ${r.med_lines} стр., каждая десятая длиннее ${r.p90_lines} стр.`})),{h:220,min:0,max:Math.max(20,niceMax(Math.max(...VS.phrase.by_period.map(r=>r.cross_stanza)))),unit:'%',fmtv:v=>fmt1(v)});
  hbars($('#c-longsent'),VS.phrase.longest.slice(0,10).map(([n,st,pid])=>({l:(t=>t.length>38?t.slice(0,36)+'…':t)(tidy(PS[pid].t)),v:n,tip:`${esc(pidTitle(pid))}<br>одно предложение на ${n} строк и ${st} строф`})),{labelW:260,rowH:22,fmtv:fmt});
})();

/* ---------- звук ---------- */
(function(){
  const B=VS.sound.by_period; const o=B.reduce((a,r)=>a+r.obs*r.n,0)/B.reduce((a,r)=>a+r.n,0), b=B.reduce((a,r)=>a+(r.base||0)*r.n,0)/B.reduce((a,r)=>a+r.n,0);
  const ratio=o/b;
  $('#f-sound').textContent=`В стихах ${fmt1(o)}% строк содержат три разных слова и больше на один звук; в случайных строках из тех же слов — ${fmt1(b)}%. `+
    (ratio>=1.15?`Совпадения случаются в ${fmt1(ratio)} раза чаще, чем если бы слова стояли наугад: звукопись — сознательный приём.`
      :ratio<=0.9?`Это даже реже, чем при случайном порядке слов.`
      :`Разница невелика: аллитерация у Бродского — не систематический приём, а отдельные яркие строки вроде тех, что ниже.`);
  chart(()=>{ const box=$('#c-allit'); const h=230; const [s,w]=svg(box,h); const L=40,R=14,T=16,B2=28; const vals=B.flatMap(r=>[r.obs,r.base||0]); const hi=niceMax(Math.max(...vals)*1.15);
    const bw=(w-L-R)/B.length, sy=v=>h-B2-(h-B2-T)*v/hi; const ax=el('g',{class:'ax'},s);
    ticks(hi,4).forEach(t=>{ el('line',{x1:L,x2:w-R,y1:sy(t),y2:sy(t),stroke:css('--grid')},ax); txt(ax,L-6,sy(t)+4,fmt1(t),{'text-anchor':'end'}); });
    const P=(k)=>B.map((r,i)=>[L+bw*i+bw/2,sy(r[k]||0)]);
    el('polyline',{points:P('base').map(p=>p.join(',')).join(' '),fill:'none',stroke:css('--muted'),'stroke-width':2,'stroke-dasharray':'5 4'},s);
    el('polyline',{points:P('obs').map(p=>p.join(',')).join(' '),fill:'none',stroke:css('--s1'),'stroke-width':2},s);
    B.forEach((r,i)=>{ const x=L+bw*i+bw/2; el('circle',{cx:x,cy:sy(r.obs),r:4.5,fill:css('--s1'),stroke:css('--surface'),'stroke-width':2},s);
      txt(s,x,sy(r.obs)-9,fmt1(r.obs),{'text-anchor':'middle',style:'fill:var(--ink)'}); txt(ax,x,h-8,PSH[i],{'text-anchor':'middle'});
      el('rect',{class:'hit',x:x-bw/2,y:T,width:bw,height:h-B2-T,'data-tip':`${PER[i]}: ${fmt1(r.obs)}% строк; в случайных строках ${fmt1(r.base||0)}%`},s); });
    txt(s,w-R,sy(B[B.length-1].base||0)+16,'случайные строки',{'text-anchor':'end',style:'fill:var(--muted);font-size:11px'});
  }, $('#c-allit'));
  const CR=VS.sound.consonant_ratio.slice(0,10);
  hbars($('#c-cons'),CR.map(([ch,r])=>({l:ch.toUpperCase(),v:(r-1)*100,tip:`«${ch}» в стихах встречается на ${fmt1((r-1)*100)}% чаще, чем в прозе`})),{labelW:40,rowH:22,unit:'%',fmtv:v=>'+'+fmt1(v)});
  $('#c-allit-lines').innerHTML=VS.sound.top_lines.map(([l,ch])=>`<div class="qline">${esc(l).replace(new RegExp(`(^|[\\s«"(—-])(${ch})`,'gi'),'$1<b>$2</b>')}</div>`).join('');
})();

/* ---------- сравнения и формулы ---------- */
(function(){
  const F=VS.figures; let k=F.simile_keys[0];
  const draw=()=>dots($('#c-sim'),F.similes.map((r,i)=>({l:PSH[i],v:r[k],tip:`${PER[i]}: «${k}» — ${fmt2(r[k])} на 1000 слов`})),{h:210,min:0,max:niceMax(Math.max(...F.similes.map(r=>r[k]))*1.2),fmtv:v=>fmt2(v)});
  seg($('#seg-sim'),F.simile_keys.map(x=>[x,x]),k,v=>{ k=v; draw(); }); draw();
  hbars($('#c-gen'),F.genitive_top.slice(0,20).map(([t,n])=>({l:t,v:n})),{labelW:190,rowH:22,fmtv:fmt});
  dots($('#c-genrate'),F.genitive_rate.map((v,i)=>({l:PSH[i],v,tip:`${PER[i]}: ${fmt2(v)} родительных формул на 1000 слов`})),{h:220,min:0,max:niceMax(Math.max(...F.genitive_rate)*1.2),fmtv:v=>fmt1(v)});
})();

/* ---------- карта словаря ---------- */
let wmGroup=-1;
function drawWmap(){
  const box=$('#c-wmap'); const W=box.clientWidth||800; const h=Math.round(Math.min(640,Math.max(420,W*0.62))); const [s,w]=svg(box,h);
  const M=ST.wmap; const xs=M.map(m=>m.x), ys=M.map(m=>m.y); const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  const pad=36; const sx=x=>pad+(w-2*pad)*(x-x0)/(x1-x0), sy=y=>pad*0.6+(h-1.2*pad)*(y-y0)/(y1-y0); const nmax=Math.max(...M.map(m=>m.n));
  const placed=[]; const fitsBox=(b)=>!placed.some(p=>b.x<p.x+p.w&&b.x+b.w>p.x&&b.y<p.y+p.h&&b.y+b.h>p.y);
  M.slice().sort((a,b)=>b.n-a.n).forEach(m=>{ const on=wmGroup<0||m.c===wmGroup; const fs=10.5+7*Math.sqrt(m.n/nmax);
    const X=sx(m.x), Y=sy(m.y); const bw=m.w.length*fs*0.56+4, bh=fs+2; const box={x:X-bw/2,y:Y-fs,w:bw,h:bh};
    const tip=`${esc(m.w)}: ${fmt(m.n)} раз в стихах<br>близкие: ${(ST.neighbors[m.k]||[]).slice(0,5).map(disp).join(', ')||'—'}`;
    let node;
    if(fitsBox(box)||(wmGroup>=0&&m.c===wmGroup)){ placed.push(box);
      node=txt(s,X,Y,m.w,{'text-anchor':'middle',style:`font-family:var(--f-body);font-size:${fs.toFixed(1)}px;fill:var(${on?(wmGroup<0?'--ink':'--accent'):'--muted'});opacity:${on?1:.3};${wmGroup===m.c?'font-weight:600;':''}`,'data-tip':tip,tabindex:0,role:'button','aria-label':m.w});
    } else {
      node=el('circle',{cx:X,cy:Y-fs/3,r:3,fill:css(on?(wmGroup<0?'--neutral-bar':'--accent'):'--muted'),opacity:on?.7:.25,'data-tip':tip,class:'clickable'},s);
    }
    node.addEventListener('click',()=>openWord(m.k,true)); node.addEventListener('keydown',e=>{ if(e.key==='Enter') openWord(m.k,true); }); });
  txt(s,w-8,h-8,'точка — слово, для подписи которого не хватило места; наведите, чтобы увидеть',{'text-anchor':'end',style:'font-size:10.5px;fill:var(--muted)'});
}
(function(){ const h=$('#wm-groups'); const mk=(i,l)=>{ const b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=l; b.setAttribute('aria-pressed',String(i===wmGroup));
    b.addEventListener('click',()=>{ wmGroup=(wmGroup===i&&i>=0)?-1:i; h.querySelectorAll('button').forEach((x,j)=>x.setAttribute('aria-pressed',String(j-1===wmGroup))); drawWmap(); }); h.appendChild(b); };
  mk(-1,'все слова'); ST.wgroups.forEach((g,i)=>mk(i,g.slice(0,3).join(', ')));
  chart(drawWmap,$('#c-wmap')); })();

/* ---------- где ломается стиль ---------- */
let distMode='form';
(function(){
  const cpf=ST.cp_form.map(c=>c[0]), cpw=ST.cp_words.map(c=>c[0]);
  const yrs=ST.years;
  $('#f-cp').textContent=`По форме стиха самые резкие переломы — ${cpf.slice(0,3).sort((a,b)=>a-b).map(y=>y+' год').join(', ')}; по словарю — ${cpw.slice(0,3).sort((a,b)=>a-b).map(y=>y+' год').join(', ')}. Год перелома — первый год нового отрезка; учтены годы, где шесть и больше стихотворений (${yrs.length} лет).`;
  const draw=()=>{ const D2=distMode==='form'?ST.dist_form:ST.dist_words; const cps=distMode==='form'?cpf:cpw;
    $('#dist-t').textContent=distMode==='form'?'Насколько похожи годы по форме стиха':'Насколько похожи годы по самым частым словам';
    chart(()=>{ const box=$('#c-dist'); const n=yrs.length; const W=box.clientWidth||700; const L=46,T=10; const cell=Math.max(8,Math.min(26,Math.floor((W-L-10)/n))); const h=T+cell*n+34; const [s,w]=svg(box,h);
      const mx=Math.max(...D2.flat()); const lo=css('--heat-lo'), hi=css('--heat-hi');
      yrs.forEach((ya,i)=>yrs.forEach((yb,j)=>{ el('rect',{x:L+j*cell,y:T+i*cell,width:cell-1,height:cell-1,fill:mixc(lo,hi,D2[i][j]/mx),'data-tip':`${ya} и ${yb}: ${i===j?'один и тот же год':'расстояние '+fmt2(D2[i][j])}<br>0 — одинаковы, чем больше — тем непохожее`},s); }));
      const every=cell<14?2:1;
      yrs.forEach((y,i)=>{ if(i%every) return; txt(s,L-6,T+i*cell+cell/2+4,y,{'text-anchor':'end',style:'font-size:10.5px;fill:var(--muted)'}); txt(s,L+i*cell+cell/2,T+n*cell+14,String(y).slice(2),{'text-anchor':'middle',style:'font-size:10.5px;fill:var(--muted)'}); });
      cps.forEach(y=>{ const i=yrs.indexOf(y); if(i<0) return; const p=L+i*cell-0.5;
        el('line',{x1:p,x2:p,y1:T,y2:T+n*cell,stroke:css('--b'),'stroke-width':2},s); el('line',{x1:L,x2:L+n*cell,y1:T+i*cell-0.5,y2:T+i*cell-0.5,stroke:css('--b'),'stroke-width':2},s); });
      txt(s,L,T+n*cell+30,'красные линии — найденные переломы',{style:'font-size:11px;fill:var(--ink-2)'});
    },$('#c-dist')); };
  seg($('#seg-dist'),[['form','по форме стиха'],['words','по словарю']],distMode,v=>{ distMode=v; draw(); }); draw();
  chart(()=>{ const box=$('#c-feats'); box.innerHTML=''; const g=document.createElement('div'); g.style.cssText='display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px 24px'; box.appendChild(g);
    const cells=ST.features.map(()=>{ const c=document.createElement('div'); g.appendChild(c); return c; });
    ST.features.forEach(([k,lab],fi)=>{ const vals=ST.year_values.map(r=>r[fi]); const c=cells[fi]; const h=96; const [s,w]=svg(c,h); const L=4,R=4,T=26,B=14;
      const fin=vals.filter(v=>v!=null&&!isNaN(v)); const mn=Math.min(...fin), mx=Math.max(...fin); const sx=i=>L+(w-L-R)*i/(vals.length-1), sy=v=>h-B-(h-B-T)*(v-mn)/((mx-mn)||1);
      txt(s,0,14,lab,{style:'font-family:var(--f-body);font-size:13px;fill:var(--ink)'});
      cpf.forEach(y=>{ const i=yrs.indexOf(y); if(i>=0) el('line',{x1:sx(i)-(w-L-R)/(2*(vals.length-1)),x2:sx(i)-(w-L-R)/(2*(vals.length-1)),y1:T-4,y2:h-B,stroke:css('--b'),'stroke-dasharray':'3 3','stroke-width':1.2},s); });
      el('polyline',{points:vals.map((v,i)=>`${sx(i)},${sy(v)}`).join(' '),fill:'none',stroke:css('--s1'),'stroke-width':1.8},s);
      txt(s,sx(0),h-2,yrs[0],{style:'font-size:10px;fill:var(--muted)'}); txt(s,sx(vals.length-1),h-2,yrs[yrs.length-1],{'text-anchor':'end',style:'font-size:10px;fill:var(--muted)'});
      vals.forEach((v,i)=>el('rect',{class:'hit',x:sx(i)-6,y:0,width:12,height:h,'data-tip':`${lab}, ${yrs[i]}: ${fmt2(v)}<br>стихотворений: ${ST.year_poems[i]}`},s)); });
  },$('#c-feats'));
  const CLs=ST.clusters; $('#cl-u').textContent=`${fmt(ST.cluster_n)} стихотворений от 12 строк; строка — группа, ячейка — сколько её стихов в каждом периоде`;
  $('#t-clusters').textContent=`Стихотворения разложены на шесть групп только по форме (длина строки, размер, рифма, перенос, фраза, существительные), без дат. Совпадение групп с периодами — ${fmt2(ST.ari)} по шкале, где 0 — случайное совпадение, а 1 — полное; случайная раскладка даёт не больше ${fmt2(ST.ari_null95)}. ${ST.ari>0.3?'Группы заметно повторяют периоды.':ST.ari>ST.ari_null95?'Связь с периодами есть, но слабая: стиль меняется постепенно, а внутри каждого периода уживаются очень разные стихи.':'Группы не повторяют периоды.'}`;
  heatTable($('#c-clusters'),CLs.map(c=>c.desc.join(' · ')),PSH,CLs.map(c=>c.by_period),{labelW:Math.min(420,($('#c-clusters').clientWidth||700)*0.55),cellH:30,fmtv:v=>fmt(v),
    tipf:(i,j)=>`группа: ${CLs[i].desc.join(', ')}<br>${PER[j]}: ${CLs[i].by_period[j]} стихотв. из ${CLs[i].n}; медианный год группы — ${CLs[i].year_med||'—'}`});
})();

/* ---------- мифы и факты, главное ---------- */
(function(){
  const PSo=D.pos, M=VS.meter.by_period, T=VS.rhyme.type, PH=VS.phrase.by_period, SPp=D.line_syllables_by_period, PR=D.pronouns;
  const fam=(r,ks)=>ks.reduce((a,k)=>a+(r[k]||0),0);
  const early=(f)=>(f(1)), late=(f)=>(f(4)+f(5))/2;
  const V=(cls,txt)=>({cls,txt});
  const dol=i=>fam(M[i],['дольник','тактовик']), cls=i=>fam(M[i],['ямб','хорей','дактиль','амфибрахий','анапест']);
  const zima=FR=>D.fields.rows.slice(0,6).map(r=>r['Зима, холод']);
  const Z=zima(); const nounRank=D.top_nouns.poetry.findIndex(r=>r.w==='время')+1;
  const q4=i=>{ const b=EX.stanzas[i].b; return b.find(x=>x[0]==='4')[1]; };
  const myths=[
    ['С годами Бродский уходит от классических размеров к дольнику', ()=>{ const d0=dol(1), d1=(dol(4)+dol(5))/2, c1=(cls(4)+cls(5))/2;
      return [d1-d0>=10?(c1>=50?V('v-part','отчасти'):V('v-yes','подтверждается')):V('v-no','не подтверждается'),
        `Дольник и тактовик: ${Math.round(d0)}% строк в 1961–1966 → ${Math.round(d1)}% в 1985–1996. Классические размеры в поздние годы — всё ещё ${Math.round(c1)}%.`]; }],
    ['Строка с годами становится длиннее', ()=>[SPp[5].med>SPp[1].med?V('v-yes','подтверждается'):V('v-no','не подтверждается'),
        `Медианная строка: ${SPp[0].med} слогов в 1957–1960, ${SPp[1].med} в 1961–1966, ${SPp[5].med} в 1990-е.`]],
    ['Фраза у Бродского не помещается в строфу', ()=>{ const a=PH[1].cross_stanza, b=Math.max(...PH.slice(2).map(r=>r.cross_stanza));
      return [b>=50?V('v-yes','подтверждается'):b>a?V('v-part','отчасти'):V('v-no','не подтверждается'),
        `Через границу строфы переходит ${fmt1(a)}% предложений в 1961–1966 и до ${fmt1(b)}% в поздние периоды. Растёт, но большинство фраз строфу не покидает.`]; }],
    ['Существительное вытесняет глагол', ()=>{ const mx=PSo.reduce((a,b)=>b.noun_verb>a.noun_verb?b:a);
      return [PSo[5].noun_verb>PSo[1].noun_verb+0.2?V('v-part','отчасти'):V('v-no','не подтверждается'),
        `Существительных на глагол: ${fmt1(PSo[1].noun_verb)} в 1961–1966, пик ${fmt1(mx.noun_verb)} в ${mx.p}, затем ${fmt1(PSo[5].noun_verb)} в 1990-е. Вытеснение есть, но оно волнообразное.`]; }],
    ['Рифма становится всё менее точной', ()=>{ const a=T[1]['точная'], b=(T[4]['точная']+T[5]['точная'])/2;
      return [a-b>=8?V('v-yes','подтверждается'):a-b>2?V('v-part','отчасти'):V('v-no','не подтверждается'),
        `Точных рифм: ${Math.round(a)}% строк в 1961–1966, ${Math.round(b)}% в 1985–1996.`]; }],
    ['Поздний Бродский реже говорит «я»', ()=>{ const a=PR[1]['я'], b=(PR[4]['я']+PR[5]['я'])/2;
      return [a-b>=2?V('v-yes','подтверждается'):b-a>=2?V('v-no','наоборот'):V('v-part','разница мала'),
        `«Я» и его формы на 1000 слов: ${fmt1(a)} в 1961–1966, ${fmt1(b)} в 1985–1996.`]; }],
    ['Бродский — поэт зимы и холода', ()=>[Z[5]<Z[1]/2?V('v-no','к концу — нет'):V('v-part','отчасти'),
        `Слова темы «Зима, холод» на 1000 слов: ${fmt1(Z[1])} в 1961–1966 и ${fmt1(Z[5])} в 1990-е. Зима — примета ранних стихов, а не всего пути.`]],
    ['Любимая строфа — четверостишие', ()=>{ const s=EX.stanzas.map((r,i)=>q4(i)); const top=EX.stanzas.every(r=>{ const b=r.b.slice(); const mx=b.reduce((a,x)=>x[1]>a[1]?x:a); return mx[0]==='4'; });
      return [top?V('v-yes','подтверждается'):V('v-part','отчасти'),`Четверостишия — ${Math.round(Math.min(...s))}–${Math.round(Math.max(...s))}% строф в зависимости от периода${top?', и в каждом периоде это самый частый размер строфы':''}.`]; }],
    ['Главное слово Бродского — «время»', ()=>[nounRank===1?V('v-yes','подтверждается'):nounRank<=3?V('v-part','почти'):V('v-no','не подтверждается'),
        `Среди существительных в стихах «время» — на ${nounRank}-м месте; впереди ${D.top_nouns.poetry.slice(0,nounRank-1).map(r=>'«'+r.w+'»').join(', ')||'никого'}.`]],
    ['Бродский почти не пишет без рифмы', ()=>{ const u=T.map(r=>r['без рифмы']); return [Math.max(...u)<20?V('v-yes','подтверждается'):V('v-part','отчасти'),
        `Строк без рифмы: от ${Math.round(Math.min(...u))}% до ${Math.round(Math.max(...u))}% в зависимости от периода.`]; }],
  ];
  const ico={'v-yes':'✓','v-no':'✕','v-part':'≈'};
  $('#myths').innerHTML=myths.map(([q,f])=>{ const [v,num]=f(); return `<article><p class="q">${q}</p><span class="verdict ${v.cls}"><span aria-hidden="true">${ico[v.cls]}</span>${v.txt}</span><p class="num">${num}</p></article>`; }).join('');
  const FFp=EX.final_func.by_period, rd0=VS.rhyme.top_pairs[0], cpf=ST.cp_form.map(c=>c[0]).slice(0,3).sort((a,b)=>a-b);
  const find=[[`${SPp[0].med} → ${SPp[5].med}`,'слогов в медианной строке: от первых стихов к последним'],
    [`${Math.round(dol(1))}% → ${Math.round((dol(4)+dol(5))/2)}%`,'строк дольником и тактовиком: 1961–1966 против 1985–1996'],
    [`${fmt1(FFp[1].share)}% → ${fmt1(FFp[2].share)}%`,'строк обрывается на предлоге, союзе или частице — скачок около 1967 года'],
    [`${Math.round(T[1]['точная'])}% → ${Math.round(T[5]['точная'])}%`,'строк с точной рифмой: 1961–1966 против 1990-х'],
    [cpf.join(', '),'годы, где алгоритм без подсказки нашёл самые резкие переломы формы стиха'],
    [`${rd0[0]} — ${rd0[1]}`,`самая частая рифма: ${rd0[2]} раз`]];
  $('#findings').innerHTML=find.map(([b,t])=>`<div><b>${esc(b)}</b><span>${esc(t)}</span></div>`).join('');
})();

/* близкие слова в словоискателе */
const _renderWord=renderWord;
renderWord=function(k){ _renderWord(k); const nb=ST.neighbors[k]; if(!nb||!nb.length) return; const host=$('#x-out .panel');
  host.insertAdjacentHTML('beforeend',`<h3 style="margin-top:16px">Близкие по употреблению</h3><p class="muted" style="font-size:14px;margin:0 0 6px">Слова, которые Бродский ставит в похожее окружение.</p><div class="chips">${nb.map(w=>`<button type="button" class="chip" data-k="${esc(w)}">${esc(disp(w))}</button>`).join('')}</div>`);
  host.querySelectorAll('button.chip[data-k]').forEach(b=>b.addEventListener('click',()=>openWord(b.dataset.k,false))); };

/* методика новых разделов */
[`Ударения расставлены автоматически моделью <code>ruaccent</code> (со словарём и разрешением омографов вроде «з<b>а</b>мок — зам<b>о</b>к»). Ручной проверки нет; в редких словах и топонимах модель ошибается («Н<b>о</b>ренская» вместо «Нор<b>е</b>нская»), и такие ошибки переходят в размер и рифму.`,
 `Размер. Стихотворение считается написанным классическим размером, если не меньше 85% его строк не ставят ударение многосложного слова на слабое место этого размера (пропуск ударения на сильном месте допустим). Иначе смотрится, какие промежутки между ударениями встречаются: 1–2 слога почти всегда — дольник; заметная доля трёхсложных — тактовик; больше — свободный стих.`,
 `Рифма ищется у строк в пределах четырёх строк и не дальше соседней строфы. Окончание сравнивается от последнего ударного гласного, с оглушением конечных согласных и редукцией безударных гласных. Точная — полное совпадение (для открытых мужских окончаний нужна ещё общая согласная перед ударным); неточная — отличается одна согласная; созвучие — совпадает ударный гласный и последний звук.`,
 `Аллитерация сравнивается со случайными строками: слова того же периода перемешиваются и собираются в строки той же длины, 20 повторов. Считаются только разные слова, чтобы повтор одного слова не выдавал себя за звукопись.`,
 `Переломы стиля найдены жадной бинарной сегментацией: годы идут подряд, алгоритм ищет разрезы, сильнее всего уменьшающие разброс двенадцати мер внутри отрезков. Словарная карта годов — дельта Барроуза по 100 самым частым словам. Группы стихотворений — метод k-средних по 11 мерам формы; совпадение с периодами — скорректированный индекс Рэнда.`,
 `Карта словаря: векторы слов построены на всём корпусе Бродского (совместная встречаемость в окне 5 слов → PPMI → SVD, 100 измерений) и уложены на плоскость методом t-SNE. Корпус небольшой, поэтому соседство слов показывает привычки Бродского, а не общий язык.`,
 `Палитра «Венеция Бродского»: лагуна, венецианский кирпич, патина, охра, гранит. Цвета проверены на различимость при нарушениях цветового зрения и на контраст в светлой и тёмной теме; у светлых цветов на графиках всегда есть подписи значений.`]
 .forEach(t=>$('#method').insertAdjacentHTML('beforeend',`<li>${t}</li>`));
