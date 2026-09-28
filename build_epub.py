"""Собирает EPUB 3 с оглавлением раздел → [период] → произведение
из brodsky_all_texts.jsonl, который пишет scrape_brodsky.py.

    python build_epub.py [--in brodsky_all_texts.jsonl] [--out brodsky.epub]
"""
import argparse
import json
import re
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from collections import Counter
from itertools import groupby
from pathlib import Path

HERE = Path(__file__).parent

CSS = """body { font-family: serif; line-height: 1.45; margin: 0 5%; }
h1 { font-size: 1.6em; text-align: center; margin: 2em 0 1em; }
h2 { font-size: 1.25em; margin: 1.5em 0 .3em; }
p { margin: 0 0 .9em; text-indent: 0; }
.src { font-size: .75em; color: #777; margin-bottom: 1.5em; word-break: break-all; }
ol { list-style: none; padding-left: 0; } ol ol { padding-left: 1.2em; }
"""

XHTML = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ru" xml:lang="ru">
<head><meta charset="utf-8"/><title>{title}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
{body}
</body>
</html>
"""


def text_to_html(text: str) -> str:
    """Абзац/строфа = блок через пустую строку; строки внутри — <br/>; отступы — неразрывные пробелы."""
    out = []
    for block in re.split(r"\n\s*\n", text):
        lines = []
        for ln in block.split("\n"):
            n = len(ln) - len(ln.lstrip(" "))
            lines.append("&#160;" * n + escape(ln.lstrip(" ")))
        out.append("<p>" + "<br/>\n".join(lines) + "</p>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(HERE / "brodsky_all_texts.jsonl"))
    ap.add_argument("--out", default=str(HERE / "brodsky.epub"))
    ap.add_argument("--book-title", default="Иосиф Бродский. Собрание текстов")
    ap.add_argument("--subtitle", default="Стихотворения, поэмы, проза, эссе, интервью, письма")
    args = ap.parse_args()

    records = [json.loads(l) for l in open(args.inp, encoding="utf-8")]
    book_id = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'https://iosif-brodskiy.ru#' + args.book_title)}"
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    files = {}   # имя -> xhtml
    toc = []     # дерево: (заголовок, файл, [дети])
    n = 0

    def work_page(r):
        nonlocal n
        n += 1
        fname = f"t{n:04d}.xhtml"
        body = (f'<h2>{escape(r["title"])}</h2>\n<p class="src">{escape(r["url"])}</p>\n'
                + text_to_html(r["text"]))
        files[fname] = XHTML.format(title=escape(r["title"]), body=body)
        return (r["title"], fname, [])

    def list_page(fname, title, children):
        items = "\n".join(f'<li><a href="{f}">{escape(t)}</a></li>' for t, f, _ in children)
        files[fname] = XHTML.format(title=escape(title), body=f"<h1>{escape(title)}</h1>\n<ol>\n{items}\n</ol>")

    p_idx = 0
    for s_idx, (sec, grp) in enumerate(groupby(records, key=lambda r: r["section_title"]), 1):
        sec_file = f"s{s_idx:02d}.xhtml"
        files[sec_file] = None  # резервируем место: страница раздела идёт в spine перед его текстами
        children = []
        for period, pgrp in groupby(grp, key=lambda r: r.get("period")):
            if period:  # стихотворения: промежуточный уровень «период»
                p_idx += 1
                p_file = f"p{p_idx:02d}.xhtml"
                files[p_file] = None
                works = [work_page(r) for r in pgrp]
                list_page(p_file, period, works)
                children.append((period, p_file, works))
            else:
                children.extend(work_page(r) for r in pgrp)
        list_page(sec_file, sec, children)
        toc.append((sec, sec_file, children))

    src_names = {"iosif-brodskiy.ru": "https://iosif-brodskiy.ru",
                 "СИБ": "«Сочинения Иосифа Бродского» в 7 томах (СПб.: Пушкинский фонд, 2001–2003)"}
    src_count = Counter(r.get("source", "iosif-brodskiy.ru") for r in records)
    sources = "<br/>".join(f"{escape(src_names.get(s, s))} — {c}" for s, c in src_count.items())
    title_page = XHTML.format(title=escape(args.book_title), body=(
        f"<h1>{escape(args.book_title)}</h1>\n<p style=\"text-align:center\">{escape(args.subtitle)}</p>\n"
        f"<p style=\"text-align:center\">Произведений: {len(records)}</p>\n"
        f"<p class=\"src\" style=\"text-align:center\">Источники:<br/>{sources}</p>"))
    files = {"title.xhtml": title_page, **files}

    def nav_ol(nodes):
        return "<ol>\n" + "\n".join(
            f'<li><a href="{f}">{escape(t)}</a>' + (nav_ol(ch) if ch else "") + "</li>" for t, f, ch in nodes
        ) + "\n</ol>"
    nav = XHTML.format(title="Оглавление", body=(
        f'<nav epub:type="toc" id="toc"><h1>Оглавление</h1>\n{nav_ol(toc)}</nav>'))

    # NCX для старых читалок (EPUB 2)
    po = 0
    def np(label, src, children):
        nonlocal po
        po += 1
        head = (f'<navPoint id="np{po}" playOrder="{po}"><navLabel><text>{escape(label)}</text></navLabel>'
                f'<content src="{src}"/>')
        return head + "".join(np(*c) for c in children) + "</navPoint>"
    ncx_points = np("Титул", "title.xhtml", []) + "".join(np(*node) for node in toc)
    ncx = (f'<?xml version="1.0" encoding="utf-8"?>\n<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
           f'<head><meta name="dtb:uid" content="{book_id}"/><meta name="dtb:depth" content="3"/></head>'
           f'<docTitle><text>{escape(args.book_title)}</text></docTitle><navMap>{ncx_points}</navMap></ncx>')

    order = list(files)
    manifest = "\n".join(f'<item id="i{i}" href="{f}" media-type="application/xhtml+xml"/>'
                         for i, f in enumerate(order))
    spine = "\n".join(f'<itemref idref="i{i}"/>' for i in range(len(order)))
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="ru">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{book_id}</dc:identifier>
<dc:title>{escape(args.book_title)}</dc:title>
<dc:creator>Иосиф Бродский</dc:creator>
<dc:language>ru</dc:language>
<dc:source>https://iosif-brodskiy.ru</dc:source>
<meta property="dcterms:modified">{modified}</meta>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="css" href="style.css" media-type="text/css"/>
{manifest}
</manifest>
<spine toc="ncx">
<itemref idref="nav"/>
{spine}
</spine>
</package>"""
    container = ('<?xml version="1.0"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                 '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                 '</rootfiles></container>')

    with zipfile.ZipFile(args.out, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)  # первым и без сжатия
        z.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
        for name, data in [("content.opf", opf), ("nav.xhtml", nav), ("toc.ncx", ncx), ("style.css", CSS),
                           *files.items()]:
            z.writestr(f"OEBPS/{name}", data, compress_type=zipfile.ZIP_DEFLATED)
    print(f"{args.out}: разделов {len(toc)}, периодов {p_idx}, произведений {n}")


if __name__ == "__main__":
    main()
