"""Правки страницы «Бродский на_просвет» (октябрь 2026), накладываются на собранную страницу:
шапка (подзаголовок под «на_просвет»), часть II «Стих» -> «Поэтика», без подсказки-тултипа
на телефоне, общие определения свёрнуты в «Справку».

python3 patch_pravki.py path/to/naprosvet/brodsky/index.html
Повторный запуск ничего не меняет."""
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
