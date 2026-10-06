"""Одноразовый патч: report2.template.html → report3.template.html (новые разделы стиха, рифмы, звука,
фразы, карты словаря, переломов стиля, мифов; простой язык вместо терминов)."""
from pathlib import Path

HERE = Path(__file__).parent
s = (HERE / "report2.template.html").read_text(encoding="utf-8")


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:90])
    s = s.replace(a, b)


# ─────────── CSS ───────────
rep("</style>", r"""
.find{display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr)); gap:12px}
.find div{background:var(--surface); border-left:3px solid var(--accent); padding:12px 14px; border-radius:0 4px 4px 0}
.find b{display:block; font-family:var(--f-display); font-weight:400; font-size:26px; line-height:1.1}
.find span{font-size:14.5px; color:var(--ink-2); line-height:1.4; display:block; margin-top:4px}
.gloss{display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr)); gap:12px; margin:14px 0}
.term{background:var(--surface); border:1px solid var(--ring); border-radius:6px; padding:14px 16px}
.term h3{font-family:var(--f-display); font-weight:400; font-size:22px; margin:0 0 2px}
.term .what{font-size:14.5px; color:var(--ink-2); margin:0 0 8px; line-height:1.45}
.term .ex{font-family:var(--f-body); font-size:16px; line-height:1.5; margin:6px 0 2px}
.term .ex b.st{color:var(--accent); font-weight:700; text-decoration:underline; text-underline-offset:3px}
.term .pat{font-family:var(--f-mono); font-size:11.5px; color:var(--muted); overflow-wrap:anywhere}
.term .src{font-family:var(--f-mono); font-size:11.5px; color:var(--muted); margin-top:2px}
.pair{font-family:var(--f-body); font-size:17px}
.pair i{font-style:normal; color:var(--muted); margin:0 6px}
.letters{display:grid; grid-template-columns:auto 1fr; gap:2px 10px; font-family:var(--f-body); font-size:15.5px; margin-top:6px}
.letters span.L{font-family:var(--f-mono); font-weight:700; text-align:center; border-radius:3px; padding:0 6px; color:var(--surface)}
.myth{display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr)); gap:12px}
.myth article{background:var(--surface); border:1px solid var(--ring); border-radius:6px; padding:14px 16px}
.myth .q{font-family:var(--f-display); font-size:21px; line-height:1.25; margin:0 0 8px}
.verdict{display:inline-flex; align-items:center; gap:6px; font-family:var(--f-mono); font-size:12px; font-weight:700; padding:2px 8px; border-radius:10px; border:1.5px solid currentColor}
.v-yes{color:#0a7d0a} .v-no{color:#c02f2f} .v-part{color:#a86200}
:root[data-theme="dark"] .v-yes{color:#3ecf3e} :root[data-theme="dark"] .v-no{color:#ff7b7b} :root[data-theme="dark"] .v-part{color:#f0a640}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]) .v-yes{color:#3ecf3e} :root:not([data-theme="light"]) .v-no{color:#ff7b7b} :root:not([data-theme="light"]) .v-part{color:#f0a640} }
.myth .num{font-size:14.5px; color:var(--ink-2); margin:8px 0 0; line-height:1.45}
.rhymebox .big{font-family:var(--f-display); font-size:40px; line-height:1; margin:6px 0}
.rchips{display:flex; flex-wrap:wrap; gap:6px}
.rchips button{font-family:var(--f-body); font-size:15.5px; background:var(--page); border:1px solid var(--rule); border-radius:14px; padding:3px 10px; cursor:pointer; color:var(--ink)}
.rchips button:hover{border-color:var(--accent); color:var(--accent)}
.rchips button small{font-family:var(--f-mono); font-size:11px; color:var(--muted); margin-left:4px}
.qline{font-family:var(--f-body); font-style:italic; font-size:16px; margin:4px 0}
.qline b{font-style:normal; color:var(--accent)}
.qline cite{font-style:normal; font-family:var(--f-mono); font-size:11.5px; color:var(--muted); margin-left:8px}
.wmap{position:relative}
.wmap text{cursor:pointer}
</style>""")

# ─────────── оглавление ───────────
rep('''  <a href="#top">Все стихотворения</a>
  <a href="#hronologia">Хронология</a>''', '''  <a href="#top">Все стихотворения</a>
  <a href="#glavnoe">Главное коротко</a>
  <a href="#mify">Мифы и факты</a>
  <a href="#hronologia">Хронология</a>''')
rep('''  <a href="#strofa">Строфа и перенос</a>''', '''  <a href="#razmer">Размер</a>
  <a href="#rifma">Рифма</a>
  <a href="#strofa">Строфа, фраза, перенос</a>
  <a href="#zvuk">Звук</a>''')
rep('''  <a href="#poisk">Словоискатель</a>''', '''  <a href="#poisk">Словоискатель</a>
  <a href="#karta">Карта словаря</a>''')
rep('''  <a href="#epitety">Эпитеты и рифмы</a>''', '''  <a href="#epitety">Эпитеты и сравнения</a>''')
rep('''  <a href="#cveta">Цвета</a>''', '''  <a href="#cveta">Цвета</a>
  <a href="#perelomy">Где ломается стиль</a>''')

# ─────────── главное + мифы (после героя) ───────────
rep('''<div class="asterism" aria-hidden="true">* * *</div>
<section id="hronologia">''', '''<section id="glavnoe" style="padding-top:28px">
  <h2>Главное коротко</h2>
  <div class="find" id="findings"></div>
</section>

<div class="asterism" aria-hidden="true">* * *</div>
<section id="mify">
  <h2>Мифы и факты</h2>
  <p>О Бродском часто говорят одни и те же вещи. Вот что из этого видно в цифрах. Вердикт — только про измеримую сторону утверждения.</p>
  <div class="myth" id="myths"></div>
</section>

<div class="asterism" aria-hidden="true">* * *</div>
<section id="hronologia">''')

# ─────────── размер и рифма (после «Строки») ───────────
rep('''<div class="asterism" aria-hidden="true">* * *</div>
<section id="strofa">
  <h2>Строфа и перенос</h2>''', '''<div class="asterism" aria-hidden="true">* * *</div>
<section id="razmer">
  <h2>Размер</h2>
  <p>Русский стих держится на ударениях. Если ударные слоги идут через равные промежутки, это классический размер: ямб, хорей, дактиль, амфибрахий, анапест. Если промежутки гуляют, но в заданных пределах, — дольник или тактовик. Если порядка нет совсем — свободный стих. Ниже каждый размер показан на строке самого Бродского: ударные слоги выделены, под строкой — её ритм.</p>
  <div class="gloss" id="meter-gloss"></div>
  <p class="finding" id="f-meter"></p>
  <div class="panel"><div class="cap"><span class="t">Какими размерами написаны стихи</span><span class="u">% строк в каждом периоде</span></div>
    <div class="legend" id="meter-legend"></div>
    <div class="chart" id="c-meter"></div></div>
  <div class="panel"><div class="cap"><span class="t">Самые частые конкретные размеры</span><span class="u">число стихотворений</span></div>
    <div class="chart" id="c-feet"></div></div>
</section>

<div class="asterism" aria-hidden="true">* * *</div>
<section id="rifma">
  <h2>Рифма <span class="tag">интерактив</span></h2>
  <p>Рифма — совпадение звуков в концах строк, начиная с последнего ударного гласного. Совпадает всё — рифма точная; совпадает почти всё — неточная; совпадает только ударный гласный и что-то рядом — созвучие. Примеры ниже взяты из стихов Бродского.</p>
  <div class="gloss" id="rhyme-gloss"></div>
  <div class="panel rhymebox"><div class="cap"><span class="t">Словарь рифм Бродского</span><span class="u" id="rd-size"></span></div>
    <p style="margin:0 0 8px">Напишите слово так, как оно стоит в конце строки («ночь», «меня», «времени») — и увидите, с чем Бродский его рифмовал.</p>
    <div class="ctrl"><input type="search" id="rd-input" placeholder="например, ночь" autocomplete="off" spellcheck="false" aria-label="Слово для словаря рифм"><div class="chips" id="rd-sug"></div></div>
    <div id="rd-out"></div></div>
  <p class="finding" id="f-rhyme"></p>
  <div class="panel"><div class="cap"><span class="t">Какие бывают рифмы</span><span class="u">% строк в каждом периоде</span></div>
    <div class="legend" id="rtype-legend"></div>
    <div class="chart" id="c-rtype"></div></div>
  <div class="grid2">
    <div class="panel"><div class="cap"><span class="t">Куда падает последнее ударение</span><span class="u">% строк: на последний слог, на предпоследний, раньше</span></div>
      <div class="legend" id="claus-legend"></div>
      <div class="chart" id="c-claus"></div></div>
    <div class="panel"><div class="cap"><span class="t">Как рифмуются четверостишия</span><span class="u">% четверостиший</span></div>
      <div class="legend" id="sch-legend"></div>
      <div class="chart" id="c-sch"></div></div>
  </div>
  <div class="grid2">
    <div class="panel"><div class="cap"><span class="t">Самые частые рифмы</span><span class="u">пар во всех стихах</span></div>
      <div class="chart" id="c-rpairs"></div></div>
    <div class="panel"><div class="cap"><span class="t">Самые длинные точные рифмы</span><span class="u">совпадают звуки от ударения до конца</span></div>
      <div class="rchips" id="c-rlong"></div>
      <h3 style="margin-top:16px">Составные рифмы</h3>
      <p class="muted" style="font-size:14px;margin:0 0 6px">Одно слово рифмуется с двумя.</p>
      <div class="rchips" id="c-rcomp"></div></div>
  </div>
</section>

<div class="asterism" aria-hidden="true">* * *</div>
<section id="strofa">
  <h2>Строфа, фраза, перенос</h2>''')

# фраза — внутрь раздела «Строфа»
rep('''    <div class="panel"><div class="cap"><span class="t">Строки без знака в конце</span><span class="u">% строк; грубый индикатор переноса</span></div>
      <div class="chart" id="c-open"></div></div>
  </div>
</section>''', '''    <div class="panel"><div class="cap"><span class="t">Строки без знака в конце</span><span class="u">% строк; грубый индикатор переноса</span></div>
      <div class="chart" id="c-open"></div></div>
  </div>
  <div class="gloss" id="enj-gloss"></div>
  <div class="grid2">
    <div class="panel"><div class="cap"><span class="t">Сколько строк занимает фраза</span><span class="u">число предложений</span></div>
      <div class="chart" id="c-shist"></div></div>
    <div class="panel"><div class="cap"><span class="t">Фраза перетекает в следующую строфу</span><span class="u">% предложений</span></div>
      <div class="chart" id="c-cross"></div></div>
  </div>
  <div class="panel"><div class="cap"><span class="t">Самые длинные фразы</span><span class="u">одно предложение, строк</span></div>
    <div class="chart" id="c-longsent"></div></div>
</section>

<div class="asterism" aria-hidden="true">* * *</div>
<section id="zvuk">
  <h2>Звук</h2>
  <p>Аллитерация — повтор одного и того же согласного в начале нескольких разных слов строки («Все строки спят. Спит ямбов строгий свод»). Чтобы понять, нарочно ли это, строки сравниваются со случайными: те же слова того же периода, перемешанные и собранные в строки той же длины.</p>
  <p class="finding" id="f-sound"></p>
  <div class="grid2">
    <div class="panel"><div class="cap"><span class="t">Строки, где три слова и больше начинаются с одного звука</span><span class="u">% строк; пунктир — случайные строки</span></div>
      <div class="chart" id="c-allit"></div></div>
    <div class="panel"><div class="cap"><span class="t">Звуки, которые стихи любят больше прозы</span><span class="u">во сколько раз чаще, чем в прозе Бродского</span></div>
      <div class="chart" id="c-cons"></div></div>
  </div>
  <div class="panel"><div class="cap"><span class="t">Самые звонкие строки</span><span class="u">четыре слова и больше на один звук</span></div>
    <div id="c-allit-lines"></div></div>
</section>''')

# карта словаря — после словоискателя
rep('''<div class="asterism" aria-hidden="true">* * *</div>
<section id="epohi">''', '''<div class="asterism" aria-hidden="true">* * *</div>
<section id="karta">
  <h2>Карта словаря <span class="tag">интерактив</span></h2>
  <p>260 самых частых слов стихов разложены так, что рядом оказываются слова, которые Бродский употребляет в похожем окружении. Выберите группу, чтобы подсветить её; нажмите на слово, чтобы открыть его в словоискателе.</p>
  <div class="ctrl"><div class="chips" id="wm-groups"></div></div>
  <div class="panel"><div class="chart wmap" id="c-wmap"></div></div>
</section>

<div class="asterism" aria-hidden="true">* * *</div>
<section id="epohi">''')

# эпитеты: рифмы → сравнения и формулы
rep('''  <h2>Эпитеты и рифмы</h2>
  <p>Эпитет — прилагательное сразу перед существительным, согласованное с ним по падежу, числу и роду; устойчивые обороты вроде «по крайней мере» исключены. Рифменная пара — два разных конечных слова в пределах четырёх строк с одинаковыми тремя последними буквами.</p>''',
    '''  <h2>Эпитеты, сравнения, формулы</h2>
  <p>Эпитет — прилагательное прямо перед существительным, согласованное с ним («белый свет»); устойчивые обороты вроде «по крайней мере» исключены. Сравнение — оборот со «словно», «будто», «как». Родительная формула — два существительных, где второе стоит в родительном падеже: «часть речи», «край темноты».</p>''')
rep('''    <div class="panel"><div class="cap"><span class="t">Частые рифменные пары</span><span class="u">раз во всех стихах</span></div>
      <div class="chart" id="c-rp"></div></div>''', '''    <div class="panel"><div class="cap"><span class="t">Родительные формулы</span><span class="u">сочетаний в стихах</span></div>
      <div class="chart" id="c-gen"></div></div>''')
rep('''<div class="asterism" aria-hidden="true">* * *</div>
<section id="temy">''', '''<div class="panel"><div class="cap"><span class="t">Сравнения по периодам</span><span class="u">на 1000 слов</span></div>
  <div class="ctrl"><div id="seg-sim"></div></div>
  <div class="chart" id="c-sim"></div></div>

<div class="asterism" aria-hidden="true">* * *</div>
<section id="temy">''')
# рифменная диаграмма в пунктуации больше не нужна
rep('''    <div class="panel"><div class="cap"><span class="t">Строки с точной рифмой рядом</span><span class="u">% строк; пунктир — та же мера для прозы</span></div>
      <div class="chart" id="c-rhyme"></div></div>''', '''    <div class="panel"><div class="cap"><span class="t">Сравнения и формулы</span><span class="u">родительных формул на 1000 слов</span></div>
      <div class="chart" id="c-genrate"></div></div>''')

# переломы стиля — после цветов
rep('''<div class="asterism" aria-hidden="true">* * *</div>
<section id="venecia">''', '''<div class="asterism" aria-hidden="true">* * *</div>
<section id="perelomy">
  <h2>Где ломается стиль <span class="tag">интерактив</span></h2>
  <p>Периоды в этом отчёте взяты с сайта. Но где стиль меняется на самом деле? Для каждого года, где у Бродского шесть и больше стихотворений, собран «отпечаток»: длина строки, размер, точность рифмы, переносы, длина фразы, частота «я» и ещё шесть мер. Алгоритм сам ищет годы, где отпечаток меняется резче всего, — ему не сообщали ни дат эмиграции, ни границ периодов.</p>
  <p class="finding" id="f-cp"></p>
  <div class="ctrl"><div id="seg-dist"></div></div>
  <div class="panel"><div class="cap"><span class="t" id="dist-t"></span><span class="u">светлее — годы похожи; линии — найденные переломы</span></div>
    <div class="chart" id="c-dist"></div></div>
  <div class="panel"><div class="cap"><span class="t">Двенадцать мер по годам</span><span class="u">у каждой мини-диаграммы своя шкала; пунктир — переломы по форме стиха</span></div>
    <div class="chart" id="c-feats"></div></div>
  <div class="panel"><div class="cap"><span class="t">Группы стихотворений, найденные без дат</span><span class="u" id="cl-u"></span></div>
    <p id="t-clusters" style="font-size:15px"></p>
    <div class="chart" id="c-clusters"></div></div>
</section>

<div class="asterism" aria-hidden="true">* * *</div>
<section id="venecia">''')

# ─────────── токены 3-го и 4-го категориальных цветов (проверены валидатором) ───────────
rep("--s1:#2a78d6; --s2:#eb6834;", "--s1:#2a78d6; --s2:#eb6834; --c3:#1baf7a; --c4:#eda100;")
rep("--s1:#3987e5; --s2:#d95926;", "--s1:#3987e5; --s2:#d95926; --c3:#199e70; --c4:#c98500;", 2)
# размер стихотворения в карточке
rep("""<div><b>${p.src==='СИБ'?'СИБ':'сайт'}</b><span>источник</span></div>""",
    """<div><b style="font-size:17px">${(m=>m?(m[1]?m[1]+'-стопный '+m[0]:m[0]):'—')(VS.meter_by_poem[String(i)])}</b><span>размер</span></div>""")

# ─────────── данные ───────────
rep('''<script type="application/json" id="data-ex">/*EX*/</script>''', '''<script type="application/json" id="data-ex">/*EX*/</script>
<script type="application/json" id="data-verse">/*VERSE*/</script>
<script type="application/json" id="data-style">/*STYLE*/</script>''')
rep('''const EX = JSON.parse(document.getElementById('data-ex').textContent);''', '''const EX = JSON.parse(document.getElementById('data-ex').textContent);
const VS = JSON.parse(document.getElementById('data-verse').textContent);
const ST = JSON.parse(document.getElementById('data-style').textContent);''')

# старые обращения к удалённым графикам
rep('''hbars($('#c-rp'),EX.rhyme_pairs.slice(0,20).map(([a,b,n])=>({l:`${a} — ${b}`,v:n,tip:`«${esc(a)}» — «${esc(b)}»: ${n} раз`})),{labelW:170,rowH:22,fmtv:fmt});''', '')
rep('''dots($('#c-rhyme'),D.rhyme.by_period.map(r=>({l:pshort(r.p),v:r.share,tip:`${r.p}: ${fmt1(r.share)}% строк<br>${fmt(r.n)} строк`})),{h:220,min:0,max:40,unit:'%',ref:D.rhyme.prose_baseline,refLabel:`проза ${fmt1(D.rhyme.prose_baseline)}%`,fmtv:v=>fmt1(v)});''', '')
rep(''' ['Самая частая рифма',`${EX.rhyme_pairs[0][0]} — ${EX.rhyme_pairs[0][1]}`,`${EX.rhyme_pairs[0][2]} раз`],''',
    ''' ['Самая частая рифма',`${VS.rhyme.top_pairs[0][0]} — ${VS.rhyme.top_pairs[0][1]}`,`${pnr(VS.rhyme.top_pairs[0][2],RUF.raz)}`],''')

# простой язык
rep('''<span class="t">Лексическое разнообразие</span><span class="u">MATTR, окно 500 лемм</span>''',
    '''<span class="t">Разнообразие словаря</span><span class="u">доля разных слов в каждых 500 подряд</span>''')
rep('''<span class="t">Закон Ципфа в стихах</span><span class="u">частота леммы от её ранга, обе оси логарифмические</span>''',
    '''<span class="t">Немногие слова — очень часто, большинство — редко</span><span class="u">закон Ципфа: частота слова от его места в списке</span>''')
rep('''  <p>Какие слова период употребляет заметно чаще остальных. Мера — логарифм отношения шансов с информативным априорным распределением (Monroe, Colaresi, Quinn, 2008), длина полоски — z-оценка. Учтены существительные, прилагательные и глаголы, встретившиеся в периоде не меньше пяти раз; имена собственные исключены. Слово можно нажать, оно откроется в словоискателе.</p>''',
    '''  <p>Какие слова каждый период употребляет заметно чаще остальных. Длина полоски — сила отличия: чем длиннее, тем увереннее можно сказать, что слово принадлежит именно этим годам, а не случайно всплыло. Учтены слова, встретившиеся в периоде хотя бы пять раз; имена собственные исключены. Слово можно нажать.</p>''')
rep('''<span class="u">z-оценка; слова, встретившиеся в двух периодах вместе 6 раз и больше</span>''', '''<span class="u">сила отличия; слова, встретившиеся в двух периодах вместе 6 раз и больше</span>''')
rep('''<span class="u">z-оценка против остальных стихов</span>''', '''<span class="u">сила отличия от остальных стихов</span>''')
rep('''  <p>Двадцать смысловых полей, в каждом по 20 лемм; поля не пересекаются. В режиме «частота» цвет показывает число употреблений на 1000 слов. В режиме «отклонение» каждая строка сравнивается со своим средним: красное — чаще обычного, синее — реже. Нажмите на название поля, чтобы увидеть, какие слова его наполняют.</p>''',
    '''  <p>Двадцать тем, в каждой по 20 слов; темы не пересекаются. В режиме «частота» цвет показывает, сколько раз слова темы встречаются на 1000 слов. В режиме «отклонение» каждая тема сравнивается сама с собой: красное — чаще обычного для неё, синее — реже. Нажмите на название темы, чтобы увидеть, какие слова её наполняют.</p>''')
rep('''<span>${fmt(d.tokens)} знам. слов</span>''', '''<span>${pn(d.tokens,RUF.word)}</span>''')
rep('''${esc(w.w)}: ${w.n} раз в периоде, z = ${w.z}''', '''${esc(w.w)}: ${pnr(w.n,RUF.raz)} в периоде; сила отличия ${fmt1(w.z)}''')
rep("'отклонение от среднего по строке, в стандартных отклонениях'",
    "'насколько чаще (красное) или реже (синее) обычного для этой темы'")
rep('''<br>отклонение ${fmt1(Mz[i][j])}''', '''<br>${Mz[i][j]>0?'чаще':'реже'} обычного: ${fmt1(Math.abs(Mz[i][j]))}''')

# ─────────── код новых разделов ───────────
NEW_JS = (HERE / "report3.sections.js").read_text(encoding="utf-8")
rep('''/* ================= старт ================= */''', NEW_JS + '''
/* ================= старт ================= */''')

# ─────────── простой язык: без «назывного», «вещного», «синтагмы», «леммы», MATTR ───────────
rep("""по слогам, леммам, частям речи, строфам и знакам препинания. Главное видно уже на первом экране: <strong>строка Бродского с годами удлиняется, а стих становится назывным и «вещным»</strong>.`;""",
    """по слогам, словам, частям речи, строфам и знакам препинания. Главное видно уже на первом экране: <strong>с годами строка Бродского становится длиннее, а в стихах становится больше предметов и меньше действий</strong> — существительных на каждый глагол приходится ${fmt1(D.pos[5].noun_verb)} в 1990-е против ${fmt1(D.pos[1].noun_verb)} в 1961–1966.`;""")
rep("""[fmt(O.unique_lemmas),'разных лемм'],[`${SP[0].med} → ${SP[SP.length-1].med}`,'слогов в медианной строке, 1957 → 1996']""",
    """[fmt(O.unique_lemmas),plural(O.unique_lemmas,['разное слово','разных слова','разных слов'])],[`${SP[0].med} → ${SP[SP.length-1].med}`,'слогов в типичной строке, 1957 → 1996']""")
rep("""<span class="u">разные леммы по мере чтения стихов подряд</span>""", """<span class="u">сколько разных слов встретилось, если читать стихи подряд</span>""")
rep("""<br>${fmt(p[1])} разных лемм`},s));""", """<br>${pn(p[1],RUF.uword)}`},s));""")
rep("""В индексе <span id="lex-n"></span> лемм, встретившихся""", """В индексе <span id="lex-n"></span>""")
rep("""$('#t-dict').innerHTML=`В стихах ${fmt(D.hapax_poetry.types)} разных лемм;""", """$('#t-dict').innerHTML=`В стихах ${pn(D.hapax_poetry.types,RUF.uword)} (все формы одного слова — «окно», «окна», «окном» — считаются вместе);""")
rep("""Ниже — по 20 самых частых знаменательных слов на 10 000 слов""", """Ниже — по 20 самых частых слов без предлогов, союзов и местоимений, на 10 000 слов текста""")
rep("""<div class="eyebrow">лемма</div>""", """<div class="eyebrow">слово</div>""")
rep("""tip:`${r.p}: MATTR ${r.mattr.toFixed(3)}<br>${fmt(r.tokens)} слов`""", """tip:`${r.p}: в среднем ${pnr(Math.round(r.mattr*500),RUF.uword)} на каждые 500 подряд<br>${pn(r.tokens,RUF.word)}`""")
rep("""table($('#c-mattr'),['Период','MATTR','Слов']""", """table($('#c-mattr'),['Период','Доля разных слов','Слов']""")
rep("""Бродский начинает рвать строку посередине синтагмы: доля строк""", """Бродский начинает рвать строку посреди фразы, между словами, которые по смыслу неразделимы: доля строк""")
rep("""Стих становится назывным: мир описан через вещи, а не через действия.`;""", """Проще говоря, в этих стихах больше предметов и меньше действий: мир описан тем, что в нём стоит, а не тем, что в нём происходит.`;""")
rep("""$('#f-line').textContent=`Медианная строка выросла""", """$('#f-line').textContent=`Типичная строка (медиана: половина строк короче, половина длиннее) выросла""")

# ─────────── палитра «Венеция Бродского»: лагуна, кирпич, патина, охра, гранит (проверена валидатором) ───────────
rep("--s1:#2a78d6; --s2:#eb6834; --c3:#1baf7a; --c4:#eda100;", "--s1:#1576b0; --s2:#c94f35; --c3:#249c7c; --c4:#d69b22;")
rep("--s1:#3987e5; --s2:#d95926; --c3:#199e70; --c4:#c98500;", "--s1:#3a92d0; --s2:#e36a42; --c3:#2aa07f; --c4:#b8841a;", 2)
rep("--neutral-bar:#5b5e66; --b:#e34948;", "--neutral-bar:#5d6168; --b:#c94f35;")
rep("--neutral-bar:#a9abb2; --b:#e66767;", "--neutral-bar:#a3a7ae; --b:#e36a42;", 2)
rep("--div-neg:#2a78d6; --div-mid:#f0efec; --div-pos:#e34948;", "--div-neg:#1576b0; --div-mid:#eeefeb; --div-pos:#c94f35;")
rep("--div-neg:#3987e5; --div-mid:#383835; --div-pos:#e66767;", "--div-neg:#3a92d0; --div-mid:#34373a; --div-pos:#e36a42;", 2)
rep("--heat-lo:#eef3fb; --heat-hi:#0d366b;", "--heat-lo:#edf2f3; --heat-hi:#0e3b58;")
rep("--heat-lo:#1c2330; --heat-hi:#9ec5f4;", "--heat-lo:#1a2329; --heat-hi:#8ec6e8;", 2)
rep("--accent:#1c5cab; --accent-soft:#dfe9f7;", "--accent:#0f5d8c; --accent-soft:#dcebf2;")
rep("--accent:#86b6ef; --accent-soft:#1a2842;", "--accent:#7fbfe6; --accent-soft:#16303f;", 2)

(HERE / "report3.template.html").write_text(s, encoding="utf-8")
print("report3.template.html written")
