"""Оборачивает сборку отчёта (out2.html) в две готовые страницы.

  docs/prosvet.html                    — обёртка превью: <!doctype>, viewport, базовый стиль;
  ../naprosvet-site/brodsky/index.html — обёртка сайта: theme.js, favicon, OG-теги, Яндекс.Метрика.

Обёртки берутся из уже опубликованных файлов (всё до «</head><body>»): так они не расходятся с сайтом.
Тело страницы одно и то же; на сайте нет строки @media (hover:none)…: её даёт theme.js.

    python wrap_pages.py out2.html                 # перезаписать обе страницы
    python wrap_pages.py out2.html --docs X --site Y   # свои пути (например, для проверки в песочнице)
    python wrap_pages.py out2.html --check         # только сверить с уже лежащими файлами, ничего не писать
"""
import argparse
from pathlib import Path

HERE = Path(__file__).parent
CUT = "</head><body>"
HOVER = "@media (hover:none) and (pointer:coarse){input[type=search],input[type=text],select,textarea{font-size:16px!important}}\n"


def split(page):
    i = page.index(CUT) + len(CUT)
    return page[:i]


def wrap_docs(build, old_docs):
    return split(old_docs) + "\n" + build + "</body></html>"


def wrap_site(build, old_site):
    body = "\n" + build + "</body></html>"
    assert body.count(HOVER) == 1, "в сборке должна быть ровно одна строка @media (hover:none)…"
    return split(old_site) + body.replace(HOVER, "", 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("--docs", default=str(HERE.parent / "docs" / "prosvet.html"))
    ap.add_argument("--site", default=str(HERE.parent.parent / "naprosvet-site" / "brodsky" / "index.html"))
    ap.add_argument("--prefix-docs", help="файл, из которого берётся обёртка docs (по умолчанию — сам --docs)")
    ap.add_argument("--prefix-site", help="файл, из которого берётся обёртка сайта (по умолчанию — сам --site)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    build = (HERE / a.build).read_text(encoding="utf-8") if not Path(a.build).is_absolute() else Path(a.build).read_text(encoding="utf-8")
    old_d = Path(a.prefix_docs or a.docs).read_text(encoding="utf-8")
    old_s = Path(a.prefix_site or a.site).read_text(encoding="utf-8")
    new_d, new_s = wrap_docs(build, old_d), wrap_site(build, old_s)
    if a.check:
        cur_d, cur_s = Path(a.docs).read_text(encoding="utf-8"), Path(a.site).read_text(encoding="utf-8")
        print("docs совпадает:", new_d == cur_d, "| сайт совпадает:", new_s == cur_s)
        raise SystemExit(0 if (new_d == cur_d and new_s == cur_s) else 1)
    for path, text in ((a.docs, new_d), (a.site, new_s)):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
        print(path, round(len(text.encode("utf-8")) / 1024), "KB")


if __name__ == "__main__":
    main()
