"""Дополняет тексты с сайта произведениями из «Сочинений Иосифа Бродского» (СИБ, 7 томов, EPUB),
которых на сайте нет. Сопоставление — по содержанию (5-словные шинглы), не по названиям.

    python merge_sib.py [--sib-dir DIR] [--site brodsky_all_texts.jsonl] [--out brodsky_combined]
    python build_epub.py --in brodsky_combined.jsonl --out brodsky_combined.epub
"""
import argparse
import glob
import json
import posixpath
import re
import zipfile
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

from scrape_brodsky import html_to_text, letters, shingles

HERE = Path(__file__).parent
DEFAULT_SIB = Path.home() / "Downloads" / "Бродский Иосиф - Сочинения Иосифа Бродского - 2001, 2003"
MARK = "⁣§§{}§§"
ON_SITE = 0.5          # доля шинглов, найденных на сайте, выше — произведение уже есть
MIN_LETTERS = 20       # отсекает заголовки разделов без текста
# Не произведения Бродского / служебное
SERVICE = ("ИОСИФ БРОДСКИЙ: НОВАЯ ОДИССЕЯ", "АЛФАВИТНЫЙ УКАЗАТЕЛЬ", "БИБЛИОГРАФИЧЕСКАЯ СПРАВКА",
           "ОТ СОСТАВИТЕЛЯ", "Annotation", "Сочинения Иосифа Бродского", "Примечания", "notes")
# Эти эссе есть на сайте в другом переводе (совпадение текста ~0, совпадение названия/темы)
ALT_TRANSLATION = {
    "МУЗА ПЛАЧА": "Скорбная муза (1982)",
    "АКТОВАЯ РЕЧЬ": "Напутствие",
    "НЕСКРОМНОЕ ПРЕДЛОЖЕНИЕ": "Нескромное предложение (1991)",
    "ПАМЯТИ СТИВЕНА СПЕНДЕРА": "Памяти Стивена Спендера",
    "МАРК СТРЭНД": "О Марке Стрэнде (1988)",
}
# Есть на сайте, но в СИБ полнее: на сайте нет 7 абзацев (~6,8 тыс. букв) — добавляем редакцию СИБ целиком
FULLER_IN_SIB = {"НАБЕРЕЖНАЯ НЕИСЦЕЛИМЫХ"}
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}


def clean_label(label):
    return re.sub(r"\[\d+\]", "", label).strip()


def read_volume(path):
    """Нарезает том по якорям оглавления. Возвращает (сегменты, сноски{номер: текст}, metadata)."""
    vol = int(re.search(r"Том (\d)", path).group(1))
    z = zipfile.ZipFile(path)
    names = z.namelist()
    opf = next(n for n in names if n.endswith(".opf"))
    o = BeautifulSoup(z.read(opf), "xml")
    base = posixpath.dirname(opf)
    man = {i["id"]: posixpath.normpath(posixpath.join(base, i["href"])) for i in o.find_all("item")}
    spine = [man[i["idref"]] for i in o.find("spine").find_all("itemref")]
    meta = {k: (o.find(k).get_text(strip=True) if o.find(k) else None) for k in ("dc:publisher", "dc:date")}

    ncx = next(n for n in names if n.endswith(".ncx"))
    nx = BeautifulSoup(z.read(ncx), "xml")
    pts = []
    for p in nx.find_all("navPoint"):
        fn, _, anchor = p.find("content")["src"].partition("#")
        parents = [q.find("navLabel").get_text(strip=True) for q in p.find_parents("navPoint")]
        pts.append({"label": p.find("navLabel").get_text(strip=True),
                    "file": posixpath.normpath(posixpath.join(posixpath.dirname(ncx), fn)),
                    "anchor": anchor, "parents": parents[::-1]})
    by_file = {}
    for k, p in enumerate(pts):
        by_file.setdefault(p["file"], []).append(k)

    chunks = []
    for fn in spine:
        s = BeautifulSoup(z.read(fn), "html.parser")
        for k in by_file.get(fn, []):
            el = s.find(id=pts[k]["anchor"]) if pts[k]["anchor"] else None
            # якорь часто стоит на пустом <a> внутри заголовка — маркер ставим перед самим заголовком
            if el is not None and el.parent is not None and el.parent.name and re.fullmatch(r"h\d", el.parent.name):
                el = el.parent
            marker = s.new_string(MARK.format(k))
            if el is not None:
                el.insert_before(marker)
            elif s.body:
                s.body.insert(0, marker)
        chunks.append(str(s.body or s))
    parts = re.split("⁣§§(\\d+)§§", "".join(chunks))
    segs = []
    for k, frag in zip(parts[1::2], parts[2::2]):
        p = pts[int(k)]
        frag = re.sub(r"(?is)^\s*<h\d\b.*?</h\d>", "", frag)  # заголовок произведения — в оглавлении
        segs.append({**p, "vol": vol, "text": html_to_text(frag)})
    notes = {int(s["label"]): s["text"] for s in segs if s["label"].isdigit()}
    return segs, notes, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sib-dir", default=str(DEFAULT_SIB))
    ap.add_argument("--site", default=str(HERE / "brodsky_all_texts.jsonl"))
    ap.add_argument("--out", default=str(HERE / "brodsky_combined"))
    args = ap.parse_args()

    site = [json.loads(l) for l in open(args.site, encoding="utf-8")]
    for r in site:
        r["source"] = "iosif-brodskiy.ru"
    site_sh = set().union(*(shingles(r["text"]) for r in site))

    added, skipped, meta = [], [], {}
    for path in sorted(glob.glob(str(Path(args.sib_dir) / "*.epub"))):
        segs, notes, meta = read_volume(path)
        for s in segs:
            label = clean_label(s["label"])
            n_let = letters(s["text"])
            if s["label"].isdigit() or n_let < MIN_LETTERS:
                continue
            if label.startswith(SERVICE) or label.upper() == "КОММЕНТАРИЙ":
                skipped.append((s["vol"], label, "service/not by Brodsky")); continue
            sh = shingles(s["text"])
            cov = len(sh & site_sh) / len(sh)
            fuller = label in FULLER_IN_SIB
            if cov >= ON_SITE and not fuller:
                continue
            if label in ALT_TRANSLATION:
                skipped.append((s["vol"], label, f"on site in another translation: {ALT_TRANSLATION[label]}"))
                continue
            text = s["text"]
            refs = [int(x) for x in re.findall(r"\[(\d+)\]", s["label"] + "\n" + text)]
            used = [n for n in dict.fromkeys(refs) if n in notes]
            if used:
                text += "\n\nПримечания:\n" + "\n".join(f"[{n}] {notes[n]}" for n in used)
            title = label + (" (полная редакция «Сочинений»)" if fuller else "")
            if re.fullmatch(r"[*\s]+", title):  # «* * *» → первая строка, как на сайте
                first = next(ln.strip() for ln in s["text"].split("\n") if ln.strip())
                first = re.sub(r"\s+", " ", first).rstrip(",.;:—-")
                title = f'"{first}..."'
            poetry = s["vol"] <= 4
            group = next((p for p in reversed(s["parents"]) if not p.startswith("Сочинения Иосифа Бродского")
                          and not re.fullmatch(r"1[89]\d\d", p)), None)
            added.append({
                "url": f"«Сочинения Иосифа Бродского», т. {ROMAN[s['vol']]}"
                       + (f" — раздел «{group}»" if group else ""),
                "section": "sib-poetry" if poetry else "sib-prose",
                "section_title": ("Стихотворения и переводы — дополнение из «Сочинений Иосифа Бродского»" if poetry
                                  else "Эссе и статьи — дополнение из «Сочинений Иосифа Бродского»"),
                "title": title, "text": text, "period": f"Том {ROMAN[s['vol']]}",
                "source": "СИБ", "coverage_on_site": round(cov, 3), "pagination": False,
            })

    records = site + added
    out = Path(args.out)
    with out.with_suffix(".jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with out.with_suffix(".txt").open("w", encoding="utf-8") as f:
        f.write(f"ИОСИФ БРОДСКИЙ — объединённое собрание. Произведений: {len(records)}\n"
                f"Источники: https://iosif-brodskiy.ru ({len(site)}); «Сочинения Иосифа Бродского» в 7 т. ({len(added)})\n")
        cur = cur_p = None
        for r in records:
            if r["section_title"] != cur:
                cur, cur_p = r["section_title"], None
                f.write("\n\n" + "#" * 72 + f"\n# РАЗДЕЛ: {cur}\n" + "#" * 72 + "\n")
            if r.get("period") and r["period"] != cur_p:
                cur_p = r["period"]
                f.write("\n\n" + "~" * 72 + f"\n~ {cur_p}\n" + "~" * 72 + "\n")
            f.write("\n" + "=" * 72 + f"\n{r['title']}\n[{r['source']}] {r['url']}\n" + "=" * 72 + "\n\n")
            f.write(r["text"] + "\n")
    log = {"site": len(site), "added": len(added),
           "added_by_volume": dict(Counter(a["period"] for a in added)),
           "added_letters": sum(letters(a["text"]) for a in added),
           "partial_matches_added": [(a["title"], a["url"], a["coverage_on_site"]) for a in added
                                     if a["coverage_on_site"] >= 0.2],
           "skipped": skipped, "sib_metadata": meta}
    out.with_suffix(".log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in log.items() if k != "skipped"}, ensure_ascii=False, indent=1))
    print("skipped:", *skipped, sep="\n  ")


if __name__ == "__main__":
    main()
