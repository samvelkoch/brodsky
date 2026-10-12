"""Вставляет новый раздел IV.4 «Цвета» (построчная разметка цвета) в собранную страницу «Бродский на просвет».

Заменяет <section id="cveta">, блок скрипта «цвета» до «венеция», добавляет стили и данные cveta.json.
Повторный запуск безопасен. Запускать после build_report.py / wrap_pages.py на каждой собранной странице:

python patch_cveta.py ../../docs/prosvet.html ../../../naprosvet/brodsky/index.html
"""
import re, sys
from pathlib import Path

HERE = Path(__file__).parent
sec = (HERE / "section.html").read_text(encoding="utf-8").strip()
js = (HERE / "cveta.js").read_text(encoding="utf-8").strip() + "\n"
cssb = "<style id=\"cv-css\">\n" + (HERE / "cveta.css").read_text(encoding="utf-8").strip() + "\n</style>"
data = "<script type=\"application/json\" id=\"data-cv\">" + (HERE / "cveta.json").read_text(encoding="utf-8").replace("</", "<\\/") + "</script>"

for f in sys.argv[1:]:
    p = Path(f); t = p.read_text(encoding="utf-8")
    t, n1 = re.subn(r'<section id="cveta">.*?</section>', lambda m: sec, t, count=1, flags=re.S)
    t, n2 = re.subn(r'/\* =+ цвета =+ \*/.*?(?=/\* =+ венеция =+ \*/)', lambda m: js + "\n", t, count=1, flags=re.S)
    if 'id="cv-css"' in t: t = re.sub(r'<style id="cv-css">.*?</style>', lambda m: cssb, t, count=1, flags=re.S)
    else: t = t.replace("</head>", cssb + "\n</head>", 1)
    if 'id="data-cv"' in t: t = re.sub(r'<script type="application/json" id="data-cv">.*?</script>', lambda m: data, t, count=1, flags=re.S)
    else: t = t.replace('<script type="application/json" id="data-ex">', data + '\n<script type="application/json" id="data-ex">', 1)
    assert n1 == 1 and n2 == 1 and 'id="cv-css"' in t and 'id="data-cv"' in t, (f, n1, n2)
    p.write_text(t, encoding="utf-8"); print(p, round(p.stat().st_size / 1024), "KB")
