"""Правки страницы «Бродский на_просвет» (октябрь 2026), накладываются на собранную страницу:
шапка (подзаголовок под «на_просвет»), часть II «Стих» -> «Поэтика», без подсказки-тултипа
на телефоне, общие определения свёрнуты в «Справку», раздел IV.6 «Среди поэтов XX века» (данные — poety_xx.json).

python3 patch_pravki.py path/to/naprosvet/brodsky/index.html
Повторный запуск ничего не меняет."""
import json
import os
import re
import sys

SUBTITLE = "Глубокий анализ корпуса текстов"
PART2 = "Поэтика"

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
if "data-pravki-2026-10" in s:
    print("уже применено"); sys.exit(0)


def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        raise SystemExit(f"ожидалось {n} вхождений, найдено {c}: {old[:80]!r}")
    s = s.replace(old, new)


# --- 1. шапка: «Стихи и проза» сверху, подзаголовок крупно под «на_просвет»
rep('<div class="eyebrow">Стихи и проза, 1957–1996 · частотный и стилевой анализ</div>',
    '<div class="eyebrow">Стихи и проза, 1957–1996</div>')
rep('<span class="hand">на<i>_</i>просвет</span></h1>',
    f'<span class="hand">на<i>_</i>просвет</span></h1>\n        <p class="hero-sub" data-pravki-2026-10>{SUBTITLE}</p>')

# --- 2. «Стих» = одна строка; часть II называется «Стихосложение»
rep('<small>II</small>Стих</button>', f'<small>II</small>{PART2}</button>')
rep('<div class="g">II · Стих</div>', f'<div class="g">II · {PART2}</div>')
rep('<div class="n">Часть II</div><h1>Стих</h1>', f'<div class="n">Часть II</div><h1>{PART2}</h1>')
rep('<span>Стих</span></div>', f'<span>{PART2}</span></div>', 6)

# --- 3. на телефоне чёрная подсказка не показывается: подписи на графиках её дублируют
rep("function showTipHTML(html,x,y){ tip.innerHTML=",
    "function showTipHTML(html,x,y){ if(tipTouch){ tip.hidden=true; return; } tip.innerHTML=")

# --- 6. общие определения — в сворачиваемую «Справку», находки про Бродского остаются открытыми
REF = [  # (раздел, подпись, что убрать в справку: регулярка внутри <section>)
    ("razmer", "Справка: что такое размер стиха",
     r'  <p>Русский стих держится.*?</p>\n  <div class="gloss" id="meter-gloss"></div>\n'),
    ("rifma", "Справка: что такое рифма и какой она бывает",
     r'  <p>Рифма — совпадение.*?</p>\n  <div class="gloss" id="rhyme-gloss"></div>\n'),
    ("strofa", "Справка: перенос и фраза через строфу",
     r'  <div class="gloss" id="enj-gloss"></div>\n'),
    ("zvuk", "Справка: что такое аллитерация и как её искали",
     r'  <p>Аллитерация — повтор.*?</p>\n'),
    ("epitety", "Справка: эпитет, сравнение, родительная формула",
     r'  <p>Эпитет — прилагательное.*?</p>\n'),
]
for sid, label, rx in REF:
    m = re.search(rf'<section id="{sid}">.*?</section>', s, re.S)
    sec = m.group(0)
    mm = re.search(rx, sec, re.S)
    if not mm:
        raise SystemExit(f"не найден текст справки в #{sid}")
    block = (f'  <details class="ref"><summary><span class="q" aria-hidden="true">?</span><span>{label}</span>'
             f'<span class="ch" aria-hidden="true">▸</span></summary><div class="ref-body">\n{mm.group(0)}  </div></details>\n')
    if sid == "strofa":  # справку про перенос ставим сразу под заголовок, к остальным определениям
        sec2 = sec.replace(mm.group(0), "")
        sec2 = sec2.replace('<h2>Строфа, фраза, перенос</h2>\n', '<h2>Строфа, фраза, перенос</h2>\n' + block, 1)
    else:
        sec2 = sec.replace(mm.group(0), block, 1)
    s = s.replace(sec, sec2)


# --- 5. Бродский среди 34 поэтов XX века (poety_xx.py -> poety_xx.json)
PX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "poety_xx.json"), encoding="utf-8"))
RANK = {m["k"]: m["rank"] for m in PX["measures"]}
assert RANK["prep"] == 2 and RANK["dot"] == 2 and RANK["open"] == 3 and RANK["excl"] == 32 and RANK["adj"] == 33, RANK
assert 15 <= RANK["dash"] <= 22, RANK  # текст ниже говорит «в середине»
rep('<a href="#perelomy"><span>IV.5</span>Где ломается стиль</a>',
    '<a href="#perelomy"><span>IV.5</span>Где ломается стиль</a><a href="#poety"><span>IV.6</span>Среди поэтов XX века</a>', 2)
NAMES = ", ".join(sorted(p["name"] for p in PX["poets"] if not p["brodsky"]))
SEC = f"""
<section id="poety">
  <div class="kick"><b>IV.6</b><span>Стиль</span></div>
  <h2>Среди поэтов XX века</h2>
  <p class="finding">Среди 34 поэтов XX века Бродский выделяется не тире, а строкой. Чаще всех, кроме Маяковского, он обрывает строку на предлоге или союзе и чаще почти всех оставляет её без знака в конце. Точек у него больше, чем у всех, кроме Самойлова, а восклицательных знаков и прилагательных меньше почти всех. По тире он в середине.</p>
  <details class="ref"><summary><span class="q" aria-hidden="true">?</span><span>Справка: с кем и как сравниваем</span><span class="ch" aria-hidden="true">▸</span></summary><div class="ref-body">
  <p>Источник — открытый «Поэтический корпус русского языка» И. Гусева: 16,7 тыс. стихотворений 195 поэтов, собранных с сайтов поэзии. Взяты 34 поэта XX века, у каждого в корпусе больше 10 тыс. слов: {NAMES}. Поэты XVIII–XIX веков не взяты: у них другие нормы пунктуации и другой стих. Детские поэты и песенники 1930-х тоже не взяты.</p>
  <p>Бродский здесь — его 93 стихотворения из того же корпуса (1958–1976), а не 561 из остальной страницы: так у всех одна типографика и один подсчёт. Поэтому числа здесь отличаются от разделов выше: тире, например, 16 на 1000 слов, а не 20. Поздних стихов Бродского в этом корпусе нет. Длина строки от типографики не зависит, поэтому для неё отдельно отмечен весь корпус Бродского 1957–1996 (полый кружок).</p>
  </div></details>
  <div class="panel"><div class="cap"><span class="t">Бродский и 34 поэта XX века</span><span class="u">точка — поэт; красная — Бродский; подписаны крайние</span></div>
    <div class="chart" id="c-poety"></div></div>
</section>
"""
i = s.index('<section id="perelomy">')
j = s.index("</section>", i) + len("</section>")
s = s[:j] + "\n" + SEC + s[j:]
rep('<script type="application/json" id="data-stats">',
    '<script type="application/json" id="data-poety">' + json.dumps(PX, ensure_ascii=False) + '</script>\n<script type="application/json" id="data-stats">')
JS = r"""
/* ================= среди поэтов XX века ================= */
(function(){ const PX=JSON.parse(document.getElementById('data-poety').textContent);
  const BR=PX.poets.find(p=>p.brodsky), OTH=PX.poets.filter(p=>!p.brodsky);
  const ln=PS.filter(p=>p.mean&&p.n); const fullSyl=ln.reduce((a,p)=>a+p.mean*p.n,0)/ln.reduce((a,p)=>a+p.n,0);
  const fmtk=(k,v)=>k==='lem'?fmt(Math.round(v)):fmt1(v);
  chart(()=>{ const box=$('#c-poety'); const rowH=102; const h=PX.measures.length*rowH+8; const [s,w]=svg(box,h); const L=12,R=12;
    PX.measures.forEach((m,i)=>{ const y0=i*rowH; const vals=PX.poets.map(p=>p.v[m.k]).concat(m.k==='syl'?[fullSyl]:[]);
      let lo=Math.min(...vals), hi=Math.max(...vals); const pad=(hi-lo)*0.04; lo-=pad; hi+=pad; const X=v=>L+(w-L-R)*(v-lo)/(hi-lo);
      txt(s,L,y0+18,m.label,{style:'font-family:var(--f-body);font-size:14.5px;fill:var(--ink)'});
      const u=txt(s,L,y0+34,m.unit+' · ',{style:'font-family:var(--f-mono);font-size:11px;fill:var(--muted)'});
      el('tspan',{style:'fill:var(--accent);font-weight:600'},u).textContent=`${m.rank}-е место из ${m.of}`;
      const cy=y0+68; el('line',{x1:L,x2:w-R,y1:cy,y2:cy,stroke:css('--grid')},s);
      const srt=OTH.slice().sort((a,b)=>a.v[m.k]-b.v[m.k]);
      srt.forEach(p=>{ el('circle',{cx:X(p.v[m.k]),cy,r:4.5,fill:css('--muted'),'fill-opacity':.45,'data-tip':`${esc(p.full)}: ${fmtk(m.k,p.v[m.k])}`},s); });
      [srt[0],srt[srt.length-1]].forEach((p,j)=>txt(s,X(p.v[m.k]),cy+22,p.name,{'text-anchor':j?'end':'start',style:'font-family:var(--f-mono);font-size:10.5px;fill:var(--muted)'}));
      if(m.k==='syl'){ el('circle',{cx:X(fullSyl),cy,r:6.5,fill:'none',stroke:css('--accent'),'stroke-width':2,'data-tip':`Весь корпус Бродского, 1957–1996: ${fmt1(fullSyl)}`},s); }
      const bx=X(BR.v[m.k]); el('circle',{cx:bx,cy,r:7,fill:css('--accent'),'data-tip':`Бродский (93 стихотворения из того же корпуса): ${fmtk(m.k,BR.v[m.k])}`},s);
      const anc=bx<w*0.25?'start':bx>w*0.75?'end':'middle';
      txt(s,bx,cy-12,`Бродский ${fmtk(m.k,BR.v[m.k])}`,{'text-anchor':anc,style:'font-family:var(--f-mono);font-size:11px;font-weight:600;fill:var(--accent)'});
    }); });
  table($('#c-poety'),['Мера','Бродский','Медиана 34 поэтов','Место'],PX.measures.map(m=>{ const v=OTH.map(p=>p.v[m.k]).sort((a,b)=>a-b); const md=(v[16]+v[17])/2; return [m.label+', '+m.unit, fmtk(m.k,BR.v[m.k]), fmtk(m.k,md), `${m.rank} из ${m.of}`]; }));
})();
"""
rep("/* ================= пунктуация ================= */", JS + "\n/* ================= пунктуация ================= */")
rep("$('#t-punct').innerHTML=`Тире у Бродского — рабочий инструмент и в стихах, и в прозе: ${fmt1(PU.poetry['тире'])} и ${fmt1(PU.prose['тире'])} на 1000 слов.",
    "$('#t-punct').innerHTML=`Тире у Бродского встречается одинаково часто в стихах и в прозе: ${fmt1(PU.poetry['тире'])} и ${fmt1(PU.prose['тире'])} на 1000 слов. Для поэта XX века это обычная частота (<a href=\"#poety\">IV.6</a>).")

CSS = """
/* правки 2026-10: подзаголовок шапки, справки */
.hero-sub{font-family:var(--f-body); font-size:clamp(24px,3.2vw,34px); line-height:1.2; font-weight:600; color:var(--htext); margin:14px 0 18px}
@media (max-width:640px){.hero-sub{font-size:19px; margin:10px 0 14px}}
details.ref{margin:14px 0 18px; border:1px dashed var(--rule)}
details.ref>summary{list-style:none; cursor:pointer; padding:11px 14px; font:500 13.5px/1.35 var(--f-mono); letter-spacing:.03em; color:var(--ink-2); display:flex; gap:10px; align-items:center}
details.ref>summary::-webkit-details-marker{display:none}
details.ref>summary:hover{color:var(--ink)}
details.ref>summary .q{flex:none; width:22px; height:22px; border:1px solid var(--accent); color:var(--accent); display:flex; align-items:center; justify-content:center; font-weight:700}
details.ref>summary .ch{margin-left:auto; color:var(--muted); transition:transform .2s}
details.ref[open]>summary .ch{transform:rotate(90deg)}
details.ref .ref-body{padding:0 14px 4px}
details.ref .ref-body>p:first-child{margin-top:4px}
"""
rep("</style>\n\n<div id=\"tip\"", CSS + "</style>\n\n<div id=\"tip\"")

open(path, "w", encoding="utf-8").write(s)
print("ok")
