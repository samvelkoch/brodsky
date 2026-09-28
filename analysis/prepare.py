"""Разметка корпуса и лемматизация. Пишет analysis/corpus.pkl"""
import json, re, pickle, functools
from pathlib import Path
import pymorphy3

HERE = Path(__file__).parent
R = [json.loads(l) for l in open(HERE.parent / "brodsky_combined.jsonl", encoding="utf-8")]
morph = pymorphy3.MorphAnalyzer()

@functools.lru_cache(maxsize=None)
def parse(w):
    p = morph.parse(w)[0]
    return p.normal_form, str(p.tag.POS)

TOK = re.compile(r"[А-Яа-яЁёA-Za-z]+(?:-[А-Яа-яЁёA-Za-z]+)*")

def body(r):
    t = r["text"].split("\n\nПримечания:")[0]
    return t

def classify(r, t):
    lines = [l for l in t.split("\n") if l.strip()]
    lat = len(re.findall(r"[A-Za-z]", t)); cyr = len(re.findall(r"[А-Яа-яЁё]", t))
    lang = "en" if lat > cyr else "ru"
    short = sum(len(l.strip()) <= 75 for l in lines) / max(1, len(lines))
    genre = "poetry" if short >= 0.85 and len(lines) >= 4 else "prose"
    sec, url = r["section_title"], r["url"]
    if sec in ("Интервью", "Биография"):
        author = "about"
    elif r["title"].startswith(("Р. М. Рильке", "Марина Цветаева. Новогоднее")):
        author = "other"  # чужие стихи, приложенные к эссе
    elif sec in ("Переводы", "Переводы с английского") or "раздел «Из " in url or "ПОДСТРОЧНЫЕ" in url:
        author = "translation"
    else:
        author = "own"
    return lang, genre, author

NOTE = re.compile(r"С\.\s?В\.|Текст (приводится|по )|Источник|публикац|журнал|альманах|отсутствует в СИБ|^\s*\*|Новый Мир|No\.|N\s?\d", re.I)


def year_of(r, t):
    """Год из авторской даты в последних строках: «1964», «май 1964», «<1966?>», «22.01.1970».
    Пометы публикатора («Текст по публикации ... 1997») и десятилетия («1960-е») не считаются."""
    # строка-дата короткая; длинные строки — проза послесловий и комментариев
    lines = [l for l in t.split("\n") if l.strip() and not NOTE.search(l) and len(l.split()) <= 8]
    ys = []
    for l in lines[-4:]:
        ys += [int(y) for y in re.findall(r"(?<!\d)(19[5-9]\d)(?!\d)(?!\s*[-–]\s*[ех](?![а-я]))", l)]
    ys = [y for y in ys if 1955 <= y <= 1996]
    return ys[-1] if ys else None

out = []
for i, r in enumerate(R):
    t = body(r)
    lang, genre, author = classify(r, t)
    toks = TOK.findall(t)
    lem = [parse(w.lower()) for w in toks] if lang == "ru" else [(w.lower(), None) for w in toks]
    out.append({**{k: r.get(k) for k in ("url", "title", "section_title", "source", "period")},
                "idx": i, "text": t, "lang": lang, "genre": genre, "author": author,
                "year": year_of(r, t) if genre == "poetry" else None,
                "tokens": toks, "lemmas": [l for l, _ in lem], "pos": [p for _, p in lem]})
pickle.dump(out, open(HERE / "corpus.pkl", "wb"))
from collections import Counter
print(Counter((o["author"], o["lang"], o["genre"]) for o in out))
print("tokens", sum(len(o["tokens"]) for o in out), "| unique forms", parse.cache_info().currsize)
print("poems with year", sum(1 for o in out if o["year"]), "/", sum(1 for o in out if o["genre"]=="poetry" and o["author"]=="own" and o["lang"]=="ru"))
