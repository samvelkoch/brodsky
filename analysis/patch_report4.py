"""Собирает report4.template.html (новое оформление отчёта) из report3.template.html.

Данные, расчёты и графики остаются прежними. Меняются: шапка с CSS (report4.head.html), разметка
(части сплошной ленты с боковым указателем), карта словаря (report4.wmap.js), несколько строк JS,
которые зависят от оформления, и навигация (report4.chrome.js).
report3.template.html и его сборка не затрагиваются.
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
t = (HERE / "report3.template.html").read_text(encoding="utf-8")

# ---------------------------------------------------------------- куски исходника
body_start = t.index('<div id="tip"')
script_start = t.index('<script type="application/json" id="data-stats">')
scripts = t[script_start:]
body = t[body_start:script_start]

main = body[body.index("<main>") + len("<main>"): body.index("</main>")]
ASTER = '<div class="asterism" aria-hidden="true">* * *</div>'
chunks = [c.strip() for c in main.split(ASTER)]

sections = {}
for c in chunks:
    for m in re.finditer(r'<section id="(\w+)"[^>]*>.*?</section>', c, re.S):
        sections[m.group(1)] = m.group(0)
# панель «Сравнения по периодам» стоит после секции «Эпитеты» вне секции — вносим её внутрь
ep_chunk = next(c for c in chunks if '<section id="epitety"' in c)
orphan = ep_chunk[ep_chunk.rindex("</section>") + len("</section>"):].strip()
assert orphan.startswith('<div class="panel">') and "c-sim" in orphan
sections["epitety"] = sections["epitety"].replace("</section>", orphan + "\n</section>")
sections["glavnoe"] = sections["glavnoe"].replace(' style="padding-top:28px"', "")
assert "синее — реже" in sections["temy"]
sections["temy"] = sections["temy"].replace("синее — реже", "зелёное — реже")

# новая карта словаря: период, «Играть», поиск, группы
sections["karta"] = '''<section id="karta">
  <h2>Карта словаря <span class="tag">интерактив</span></h2>
  <p>260 самых частых слов стихов разложены так, что рядом оказываются слова, которые Бродский употребляет в похожем окружении. Цветные области — группы слов. Выберите период или нажмите «Играть»: слова, характерные для периода, вырастут и покраснеют. Нажмите на слово, чтобы увидеть его ближайших соседей.</p>
  <div class="wm-ctl">
    <button type="button" class="wm-play" id="wm-play">▶ Играть</button>
    <div class="wm-per" id="wm-per" role="group" aria-label="Период"></div>
    <input type="search" id="wm-find" placeholder="найти слово на карте" autocomplete="off" spellcheck="false" aria-label="Найти слово на карте">
  </div>
  <div class="ctrl"><span class="lab">Группа</span><div class="chips" id="wm-groups"></div></div>
  <div class="panel"><div class="chart wmap" id="c-wmap"></div></div>
  <p class="wm-read" id="wm-read" aria-live="polite"></p>
</section>'''

# ---------------------------------------------------------------- разделы «Мира Бродского»
def shelf_section(sid, title, intro, find_id, host):
    return f'''<section id="{sid}">
  <h2>{title}</h2>
  <p>{intro}</p>
  <p class="finding" id="{find_id}"></p>
  <div id="{host}"></div>
</section>'''


sections["personazhi"] = '''<section id="personazhi">
  <h2>Персонажи <span class="tag">интерактив</span></h2>
  <p>Все, кого Бродский называет по имени: поэты и императоры, современники, боги и герои пьес. Имена найдены в текстах автоматически, вручную никого не отбирали. В сети 120 самых упоминаемых, остальных можно найти по имени. Линия между двумя именами значит, что они названы в одной строфе или в одном абзаце.</p>
  <p class="finding" id="f-pers"></p>
  <div class="wd-ctl"><span class="lab">Где</span><div id="seg-ppmode"></div><span class="lab">Период</span><div class="chips" id="pp-per"></div></div>
  <div class="wd-ctl"><input type="search" id="pp-find" placeholder="найти имя" autocomplete="off" spellcheck="false" aria-label="Найти имя"><div class="chips" id="pp-sug"></div></div>
  <div class="ctrl"><span class="lab">Круги имён</span><div class="chips" id="pp-clusters"></div></div>
  <div class="wd-grid"><div class="panel" style="margin:0"><div class="chart" id="c-net"></div></div><aside class="card" id="pp-card" aria-live="polite"></aside></div>
  <div class="grid2">
    <div class="panel"><div class="cap"><span class="t">Кого чаще всего называют в стихах</span><span class="u">в скольких стихотворениях назван</span></div><div class="chart" id="c-pp-poems"></div></div>
    <div class="panel"><div class="cap"><span class="t">Кого чаще всего называют в прозе</span><span class="u">в скольких прозаических текстах назван</span></div><div class="chart" id="c-pp-prose"></div></div>
  </div>
  <div class="panel"><div class="cap"><span class="t">Кого называли в какие годы</span><span class="u">упоминаний в стихах; нажмите на имя</span></div><div class="chart" id="c-pp-heat"></div></div>
  <details class="data" id="pp-all"><summary>Все имена (<span id="pp-all-n"></span>)</summary><div class="chips" id="pp-allchips" style="margin-top:10px"></div></details>
</section>'''

sections["mesta"] = '''<section id="mesta">
  <h2>Места <span class="tag">интерактив</span></h2>
  <p>Города и страны, реки и моря, острова и площади. Названные места найдены так же, как имена: по заглавной букве и по окружению. Ниже места без названий: набережные, болота, океаны, скамейки, комнаты.</p>
  <p class="finding" id="f-place"></p>
  <div class="wd-grid"><div class="panel" style="margin:0"><div class="cap"><span class="t">Самые упоминаемые места</span><span class="u">в скольких текстах названо; нажмите на название</span></div><div class="chart" id="c-pl-top"></div></div><aside class="card" id="pl-card" aria-live="polite"></aside></div>
  <div class="panel"><div class="cap"><span class="t">Какие места называли в какие годы</span><span class="u">упоминаний в стихах; нажмите на название</span></div><div class="chart" id="c-pl-heat"></div></div>
  <h3 style="margin-top:30px">Места без названий</h3>
  <p class="finding" id="f-places2"></p>
  <div id="sh-places"></div>
</section>'''
sections["transport"] = shelf_section("transport", "Средства передвижения", "Поезда и трамваи, лодки и гондолы, самолёты. Слова разложены по тому, где движется транспорт: по рельсам, по дороге, по воде, по воздуху.", "f-transport", "sh-transport")
sections["eda"] = shelf_section("eda", "Еда", "Хлеб и пирожные, устрицы и шашлык, яблоки и арбузы. Слова по группам: что подают на стол, из чего это сделано и как называется застолье.", "f-food", "sh-food")
sections["napitki"] = shelf_section("napitki", "Напитки", "От вина и граппы до чая и молока. Слова по группам, вместе с посудой, из которой пьют.", "f-drinks", "sh-drinks")

# ---------------------------------------------------------------- части
PARTS = [
    ("obzor", "Обзор", "I", "Что вошло в корпус, как он распределён по годам и что о Бродском принято говорить.",
     ["glavnoe", "mify", "hronologia"]),
    ("stih", "Стих", "II", "Как устроена строка: длина, размер, рифма, строфа и звук. С примерами из самих стихов.",
     ["stroka", "razmer", "rifma", "strofa", "zvuk", "atlas"]),
    ("slova", "Слова", "III", "Какие слова Бродский любил, как они менялись от периода к периоду и с чем сочетались. Здесь же поиск по любому слову.",
     ["slovar", "poisk", "karta", "epohi", "epitety", "temy"]),
    ("stil", "Стиль", "IV", "Грамматика, знаки препинания, имена, цвета и годы, где стиль менялся резче всего.",
     ["grammatika", "punktuacia", "imena", "cveta", "perelomy"]),
    ("mir", "Мир Бродского", "V", "Кого, где и что: персонажи и места его текстов, транспорт, еда и напитки.",
     ["personazhi", "mesta", "transport", "eda", "napitki"]),
    ("venecia", "Венеция", "VI", "Венецианские тексты отдельно: чем их слова и строки отличаются от остальных стихов.",
     ["venecia"]),
    ("proza", "Проза", "VII", "Эссе, английские стихи, рекорды корпуса и то, как всё это считалось.",
     ["proza", "english", "rekordy", "metod"]),
]
assert sorted(s for c in PARTS for s in c[4]) == sorted(sections), set(sections) ^ {s for c in PARTS for s in c[4]}


def sec_title(sec_html):
    h = re.search(r"<h2>(.*?)</h2>", sec_html, re.S).group(1)
    return re.sub(r'\s*<span class="tag">.*?</span>', "", h).strip()


def kicker(sec_html, roman, name, i):
    return re.sub(r'(<section id="\w+"[^>]*>)',
                  lambda m: m.group(1) + f'\n  <div class="kick"><b>{roman}.{i}</b><span>{name}</span></div>', sec_html, count=1)


tabs = "".join(
    f'<button type="button" data-part="part-{k}" aria-current="{"true" if n == 0 else "false"}"><small>{r}</small>{nm}</button>'
    for n, (k, nm, r, _, _) in enumerate(PARTS))

HERO = '''<header class="hero" id="top">
  <div class="inner">
    <div class="eyebrow">Стихи и проза, 1957–1996 · частотный и стилевой анализ</div>
    <h1><span class="typed">Бродский</span><span class="hand">на просвет</span></h1>
    <p class="lede" id="lede"></p>
    <div class="tools">
      <label for="hl-input">Подсветить слово на страницах</label>
      <input type="search" id="hl-input" placeholder="например, стекло" autocomplete="off" spellcheck="false">
      <div class="chips" id="hl-chips"></div>
      <span class="count" id="hl-count" aria-live="polite"></span>
    </div>
    <div class="pages" id="pages"><canvas id="pages-cv" role="img" aria-label="Все стихотворения Бродского в хронологическом порядке: каждое изображено страницей, каждая строка — штрихом длиной в число слогов"></canvas></div>
    <p class="pages-note">Каждый лист — стихотворение, каждый штрих — строка: чем длиннее штрих, тем больше в строке слогов. Пропуск между штрихами — граница строфы, длинные стихотворения сжаты по высоте. Листы идут по времени, слева — годы ряда. Нажмите на лист, чтобы открыть его карточку в атласе: там строение стихотворения крупно и ссылка на текст.</p>
    <div class="figures" id="figures"></div>
  </div>
</header>'''

rail = []
parts_html = []
for n, (key, name, roman, lead, ids) in enumerate(PARTS):
    rail.append(f'<div class="g">{roman} · {name}</div>')
    rail += [f'<a href="#{s}"><span>{roman}.{i}</span>{sec_title(sections[s])}</a>' for i, s in enumerate(ids, 1)]
    links = "" if len(ids) == 1 else '<div class="ch-links">' + "".join(
        f'<a href="#{s}"><span>{roman}.{i}</span>{sec_title(sections[s])}</a>' for i, s in enumerate(ids, 1)) + "</div>"
    head = (f'<div class="part-head"><div class="n">Часть {roman}</div><h1>{name}</h1><p class="lead">{lead}</p>{links}</div>')
    secs = "\n\n".join(kicker(sections[s], roman, name, i) for i, s in enumerate(ids, 1))
    parts_html.append(f'<div class="part" id="part-{key}">\n{head}\n{secs}\n</div>')

out = ['<div id="tip" role="tooltip" hidden></div>',
       f'<div class="bar"><div class="inner"><div class="brand">Бродский<i>_</i> на просвет</div>'
       f'<nav class="tabs" aria-label="Части">{tabs}</nav></div></div>',
       HERO,
       '<div class="inner"><div class="layout">',
       f'<nav class="rail" aria-label="Разделы">{"".join(rail)}</nav>',
       '<div class="content">', "\n\n".join(parts_html),
       '<div class="endnote"><span>Бродский на просвет · 561 стихотворение и 72 прозаических текста</span><a href="#top">К началу ↑</a></div>',
       '</div></div></div>\n\n']
new_body = "\n".join(out)


# ---------------------------------------------------------------- правки JS, зависящие от оформления
def sub1(s, old, new, count=1):
    assert s.count(old) == count, (old[:60], s.count(old))
    return s.replace(old, new)


scripts = sub1(scripts,
    "const ink=css('--ink'), hl=css('--s1'), mut=css('--muted'), thumb=css('--thumb'), ring=css('--rule'), acc=css('--accent');",
    "const ink=css('--hink'), hl=css('--hmark'), mut=css('--hmute'), thumb=css('--hsheet'), ring=css('--hring'), acc=css('--hsel');")
scripts = sub1(scripts, "g.fillStyle=mut; g.font='11px \"PT Mono\", ui-monospace, monospace';",
               "g.fillStyle=css('--hlabel'); g.font='11px \"IBM Plex Mono\", ui-monospace, monospace';")
# прокрутка к разделам
scripts = sub1(scripts, "$('#atlas').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});", "goTo('atlas');")
scripts = sub1(scripts, "$('#poisk').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});", "goTo('poisk');")
scripts = sub1(scripts, "$('#top').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});", "goTo('top');")
scripts = sub1(scripts, "$('#rifma').scrollIntoView({behavior:'smooth'});", "goTo('rifma');")
# цвета в подписях: синий заменён зелёным
scripts = sub1(scripts, "насколько чаще (красное) или реже (синее) обычного для этой темы", "насколько чаще (красное) или реже (зелёное) обычного для этой темы")
if "красное — чаще обычного для неё, синее — реже" in scripts:
    scripts = scripts.replace("красное — чаще обычного для неё, синее — реже", "красное — чаще обычного для неё, зелёное — реже")
scripts = sub1(scripts, "Палитра «Венеция Бродского»: лагуна, венецианский кирпич, патина, охра, гранит.",
               "Палитра: кирпич, патина, охра и розовая глина на тёплой бумаге.")
# новая карта словаря
a = scripts.index("/* ---------- карта словаря ---------- */")
b = scripts.index("/* ---------- где ломается стиль ---------- */")
scripts = scripts[:a] + (HERE / "report4.wmap.js").read_text(encoding="utf-8") + "\n" + scripts[b:]
# старый указатель слева и подсветка по прокрутке заменяются навигацией по частям
a = scripts.index("const links=[...document.querySelectorAll('nav.toc a')];")
b = scripts.index("document.querySelectorAll('main section, header.hero').forEach(s=>io.observe(s));")
b += len("document.querySelectorAll('main section, header.hero').forEach(s=>io.observe(s));")
scripts = scripts[:a] + (HERE / "report4.chrome.js").read_text(encoding="utf-8") + scripts[b:]

a = scripts.index("/* ================= старт ================= */")
scripts = scripts[:a] + (HERE / "report4.world.js").read_text(encoding="utf-8") + "\n" + scripts[a:]
scripts = sub1(scripts, '<script type="application/json" id="data-style">/*STYLE*/</script>', '<script type="application/json" id="data-style">/*STYLE*/</script>\n<script type="application/json" id="data-world">/*WORLD*/</script>')

head = (HERE / "report4.head.html").read_text(encoding="utf-8")
(HERE / "report4.template.html").write_text(head + "\n" + new_body + scripts, encoding="utf-8")
print("report4.template.html", round((HERE / "report4.template.html").stat().st_size / 1024), "KB")
