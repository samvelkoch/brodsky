"""Скрапер текстов с https://iosif-brodskiy.ru в один .txt файл.

Использование:
    python scrape_brodsky.py                 # полный прогон
    python scrape_brodsky.py --pilot         # по одной странице на раздел
    python scrape_brodsky.py --include-articles   # добавить раздел articles/ (сторонние рекламные статьи)
"""
import argparse
import hashlib
import html
import json
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urldefrag, urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://iosif-brodskiy.ru"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; brodsky-text-archiver/1.0)"}
HERE = Path(__file__).parent
CACHE = HERE / ".html_cache"

# Порядок разделов — как в меню сайта
SECTION_ORDER = [
    "biografiia", "interviu", "poemy", "pisma", "stikhotvoreniia-i-poemy",
    "proza-i-esse", "pesy", "esse-vystupleniia", "basni", "vospominaniia",
    "perevody", "perevody-s-angliiskogo", "kritika", "articles",
]
SECTION_TITLES = {
    "biografiia": "Биография", "interviu": "Интервью", "poemy": "Поэмы", "pisma": "Письма",
    "stikhotvoreniia-i-poemy": "Стихотворения и поэмы", "proza-i-esse": "Проза и эссе",
    "pesy": "Пьесы", "esse-vystupleniia": "Эссе, выступления", "basni": "Басни",
    "vospominaniia": "Воспоминания", "perevody": "Переводы",
    "perevody-s-angliiskogo": "Переводы с английского", "kritika": "Критика",
    "articles": "Статьи (сторонние)",
}
# Периоды для «Стихотворений и поэм» — по страницам сайта po-godam/*
PERIODS = [
    ("stikhotvoreniia-1930-1960-g", "Стихотворения 1930—1960"),
    ("stikhotvoreniia-1961-1966-g", "Стихотворения 1961—1966"),
    ("stikhotvoreniia-1967-1972-g", "Стихотворения 1967—1972"),
    ("stikhotvoreniia-1973-1984-g", "Стихотворения 1973—1984"),
    ("stikhotvoreniia-1985-1989-g", "Стихотворения 1985—1989"),
    ("stikhotvoreniia-1990-1996-g", "Стихотворения 1990—1996"),
]
NEAR_DUP_JACCARD = 0.9  # сходство по 5-словным шинглам, выше — одна и та же вещь
LINK_RATIO_SKIP = 0.6  # страница-оглавление: >60% текста — ссылки
PAGINATION_RE = re.compile(r"limitstart|showall=|article-index|Страница \d+ из", re.I)


def sitemap_urls():
    xml = requests.get(f"{BASE}/sitemap.xml", headers=HEADERS, timeout=30).text
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def fetch(url, retries=3):
    CACHE.mkdir(exist_ok=True)
    fp = CACHE / (hashlib.md5(url.encode()).hexdigest() + ".html")
    if fp.exists():
        return fp.read_bytes(), 200
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=40)
            if r.status_code == 200:
                fp.write_bytes(r.content)
                time.sleep(0.3)
                return r.content, 200
            last = r.status_code
        except requests.RequestException as e:
            last = repr(e)
        time.sleep(2 * (i + 1))
    return None, last


def html_to_text(fragment: str) -> str:
    s = re.sub(r"(?is)<(script|style|ins|noscript)\b.*?</\1>", "", fragment)
    s = re.sub(r"\r?\n", " ", s)  # сырые переводы строк в HTML = пробел; строки задаются <br>
    s = re.sub(r"(?i)<br\b[^>]*>", "\n", s)  # в т.ч. <br class="..."/> из EPUB
    s = re.sub(r"(?i)</?(p|div|h[1-6]|li|tr|blockquote)\b[^>]*>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ").replace("\r", "")
    lines = [ln.rstrip() for ln in s.split("\n")]
    # снимаем только общий отступ, сохраняя «лесенку»
    indents = [len(ln) - len(ln.lstrip(" \t")) for ln in lines if ln.strip()]
    common = min(indents) if indents else 0
    lines = [ln[common:] if ln.strip() else "" for ln in lines]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract(raw: bytes):
    """Возвращает (title, text, info) или (None, None, reason)."""
    doc = raw.decode("utf-8", errors="replace")
    soup = BeautifulSoup(doc, "html.parser")
    art = next((a for a in soup.select("article.item") if a.select_one("h1.title")), None)
    if art is None:
        return None, None, "no article.item with h1.title"
    title = art.select_one("h1.title").get_text(" ", strip=True)
    content = art.select_one("div.content")
    if content is None:
        return None, None, "no div.content"
    for sel in ["script", "style", "ins", "noscript", ".uptolike-buttons", "div.page-nav", "p.meta"]:
        for t in content.select(sel):
            t.decompose()
    plain = content.get_text(" ", strip=True)
    link_txt = sum(len(a.get_text(strip=True)) for a in content.find_all("a"))
    if plain and link_txt / len(plain) > LINK_RATIO_SKIP:
        return None, None, f"listing page (link ratio {link_txt / len(plain):.2f})"
    text = html_to_text(str(content))
    if "�" in text:  # ремонт кодировки только для этой страницы
        alt = BeautifulSoup(raw.decode("cp1251", errors="replace"), "html.parser")
        a2 = next((a for a in alt.select("article.item") if a.select_one("h1.title")), None)
        if a2 is not None and a2.select_one("div.content"):
            t2 = html_to_text(str(a2.select_one("div.content")))
            if t2.count("�") < text.count("�"):
                text = t2
    if not text:
        return None, None, "empty content"
    info = {"pagination": bool(PAGINATION_RE.search(str(art)))}
    return title, text, info


def period_map():
    """url -> (индекс периода, название, позиция на странице периода)."""
    m = {}
    for p_idx, (slug, name) in enumerate(PERIODS):
        url = f"{BASE}/po-godam/{slug}.html"
        raw, status = fetch(url)
        if raw is None:
            raise RuntimeError(f"не удалось скачать {url}: {status}")
        soup = BeautifulSoup(raw.decode("utf-8", errors="replace"), "html.parser")
        art = next(a for a in soup.select("article.item") if a.select_one("h1.title"))
        for pos, a in enumerate(art.select("div.content a[href]")):
            link = urldefrag(urljoin(url, a["href"]))[0].rstrip("/")
            m.setdefault(link, (p_idx, name, pos))
    return m


def shingles(text, k=5):
    w = re.findall(r"[а-яёa-z]+", text.lower())
    return {" ".join(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}


def letters(text):
    return len(re.findall(r"[А-Яа-яЁёA-Za-z]", text))


def drop_near_duplicates(records):
    """Одна и та же вещь в разных разделах под разными заголовками. Оставляем более полную копию
    (больше букв), при равенстве — ту, что раньше в порядке меню. records уже отсортированы."""
    sh = [shingles(r["text"]) for r in records]
    drop, pairs = set(), []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            if i in drop or j in drop or min(len(sh[i]), len(sh[j])) / max(len(sh[i]), len(sh[j])) < 0.8:
                continue
            jac = len(sh[i] & sh[j]) / len(sh[i] | sh[j])
            if jac >= NEAR_DUP_JACCARD:
                keep, lose = (j, i) if letters(records[j]["text"]) > letters(records[i]["text"]) else (i, j)
                drop.add(lose)
                pairs.append({"dropped": records[lose]["url"], "kept": records[keep]["url"],
                              "jaccard": round(jac, 3)})
    return [r for k, r in enumerate(records) if k not in drop], pairs


def section_of(url):
    parts = url.replace(BASE, "").strip("/").split("/")
    return parts[0] if len(parts) >= 2 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--include-articles", action="store_true")
    ap.add_argument("--out", default=str(HERE / "brodsky_all_texts.txt"))
    args = ap.parse_args()

    urls = list(dict.fromkeys(u.rstrip("/") for u in sitemap_urls()))
    sitemap_counts = Counter(section_of(u) or "(top-level)" for u in urls)
    leaf = [u for u in urls if section_of(u) and section_of(u) != "po-godam"]
    skipped = [(u, "top-level listing/nav page") for u in urls if not section_of(u)]
    skipped += [(u, "po-godam: listing by years") for u in urls if section_of(u) == "po-godam"]
    if not args.include_articles:
        skipped += [(u, "articles/: third-party ad content (excluded)") for u in leaf if section_of(u) == "articles"]
        leaf = [u for u in leaf if section_of(u) != "articles"]
    if args.pilot:
        seen, pilot = set(), []
        for u in leaf:
            if section_of(u) not in seen:
                seen.add(section_of(u)); pilot.append(u)
        leaf = pilot

    with ThreadPoolExecutor(max_workers=4) as ex:
        raws = list(ex.map(fetch, leaf))

    records, failed, hashes, dups = [], [], {}, []
    for url, (raw, status) in zip(leaf, raws):
        if raw is None:
            failed.append((url, status)); continue
        title, text, info = extract(raw)
        if title is None:
            skipped.append((url, info)); continue
        h = hashlib.md5(re.sub(r"\s+", " ", text).encode()).hexdigest()
        if h in hashes:
            dups.append((url, hashes[h])); continue
        hashes[h] = url
        records.append({"url": url, "section": section_of(url), "title": title, "text": text, **info})

    order = {s: i for i, s in enumerate(SECTION_ORDER)}
    idx = {u: i for i, u in enumerate(urls)}
    records.sort(key=lambda r: (order.get(r["section"], 99), idx[r["url"]]))
    records, near_dups = drop_near_duplicates(records)

    pmap = period_map()
    for r in records:
        p = pmap.get(r["url"]) if r["section"] == "stikhotvoreniia-i-poemy" else None
        r["period"] = p[1] if p else None
        r["_pkey"] = (p[0], p[2]) if p else (99, 0)
    records.sort(key=lambda r: (order.get(r["section"], 99), r["_pkey"], idx[r["url"]]))
    unperioded = [r["url"] for r in records if r["section"] == "stikhotvoreniia-i-poemy" and not r["period"]]
    for r in records:
        del r["_pkey"]

    out = Path(args.out)
    with out.open("w", encoding="utf-8") as f:
        f.write("ИОСИФ БРОДСКИЙ — тексты с сайта https://iosif-brodskiy.ru\n")
        f.write(f"Собрано: {time.strftime('%Y-%m-%d')}. Произведений: {len(records)}\n")
        cur = cur_p = None
        for r in records:
            if r["section"] != cur:
                cur, cur_p = r["section"], None
                f.write("\n\n" + "#" * 72 + f"\n# РАЗДЕЛ: {SECTION_TITLES.get(cur, cur)}\n" + "#" * 72 + "\n")
            if r["period"] and r["period"] != cur_p:
                cur_p = r["period"]
                f.write("\n\n" + "~" * 72 + f"\n~ {cur_p}\n" + "~" * 72 + "\n")
            f.write("\n" + "=" * 72 + f"\n{r['title']}\n[{SECTION_TITLES.get(cur, cur)}] {r['url']}\n" + "=" * 72 + "\n\n")
            f.write(r["text"] + "\n")

    with out.with_suffix(".jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps({**r, "section_title": SECTION_TITLES.get(r["section"], r["section"])},
                               ensure_ascii=False) + "\n")

    report = {
        "sitemap_counts": dict(sitemap_counts),
        "written_by_section": dict(Counter(r["section"] for r in records)),
        "written_total": len(records),
        "skipped": len(skipped), "duplicates": len(dups), "near_duplicates": len(near_dups),
        "failed": len(failed),
        "poems_by_period": dict(Counter(r["period"] for r in records if r["period"])),
        "poems_without_period": unperioded,
        "chars": sum(len(r["text"]) for r in records),
        "words": sum(len(r["text"].split()) for r in records),
        "replacement_chars": sum(r["text"].count("�") for r in records),
        "pages_with_pagination_markers": [r["url"] for r in records if r["pagination"]],
    }
    log = out.with_suffix(".log.json")
    log.write_text(json.dumps({"report": report, "skipped": skipped, "duplicates": dups,
                               "near_duplicates": near_dups, "failed": failed},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    print("->", out, "\n->", log)


if __name__ == "__main__":
    main()
