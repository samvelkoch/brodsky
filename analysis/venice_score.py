"""Оценка «венецианскости» каждого произведения. Пишет analysis/venice_scores.json"""
import json, pickle, re
from pathlib import Path
HERE = Path(__file__).parent
C = pickle.load(open(HERE / "corpus.pkl", "rb"))
# Маркеры, однозначно указывающие на Венецию (по леммам / словоформам в нижнем регистре)
STRONG = {
    "венеция": "Венеция", "венецианский": "венецианский", "венецианец": "венецианец", "венецианка": "венецианка",
    "venice": "Venice", "venetian": "Venetian", "venezia": "Venezia", "veneziano": "Venezia",
    "гондола": "гондола", "гондольер": "гондольер", "gondola": "gondola", "вапоретто": "вапоретто",
    "риальто": "Риальто", "джудекка": "Джудекка", "дзаттере": "Дзаттере", "мурано": "Мурано",
    "торчелло": "Торчелло", "бурано": "Бурано", "серениссима": "Серениссима", "salute": "Салюте", "салют": None,
}
PHRASES = {  # многословные и дефисные
    r"сан[- ]марк": "Сан-Марко", r"сан[- ]микел": "Сан-Микеле", r"сан[- ]джорджо": "Сан-Джорджо",
    r"сан[- ]пьетро": "Сан-Пьетро", r"сан[- ]дзаккари": "Сан-Дзаккария", r"canal grande|канал[а-я]* гранде|больш[а-я]+ канал": "Канал Гранде",
    r"fondamenta|фондамент": "Фондамента", r"incurabili|неисцелим": "Неисцелимые", r"лагун": "лагуна", r"lagoon": "lagoon",
    r"\bлидо\b": "Лидо", r"салюте": "Салюте", r"адриатик": "Адриатика", r"марчелло": "Марчелло",
}
rows = []
for o in C:
    if o["author"] in ("other",):
        continue
    low = o["text"].lower()
    hits = {}
    for lem in o["lemmas"]:
        lab = STRONG.get(lem)
        if lab: hits[lab] = hits.get(lab, 0) + 1
    for rx, lab in PHRASES.items():
        n = len(re.findall(rx, low))
        if n: hits[lab] = hits.get(lab, 0) + n
    total = sum(hits.values()); words = max(1, len(o["tokens"]))
    title_hit = bool(re.search(r"венеци|venice|venezia|лагун|сан[- ]пьетро|сан[- ]марк|неисцелим|марчелло|гондол", o["title"].lower()))
    rows.append({"idx": o["idx"], "title": o["title"], "section": o["section_title"], "genre": o["genre"],
                 "author": o["author"], "hits": hits, "total": total, "per1k": round(1000 * total / words, 2),
                 "words": words, "title_hit": title_hit})
rows = [r for r in rows if r["total"]]
rows.sort(key=lambda r: (-r["title_hit"], -r["per1k"]))
json.dump(rows, open(HERE / "venice_scores.json", "w"), ensure_ascii=False, indent=0)
print("texts with any marker:", len(rows))
for r in rows:
    print(f"{'T' if r['title_hit'] else ' '} {r['total']:>3} {r['per1k']:>6} {r['words']:>6} {r['genre'][:4]} {r['author'][:5]} | {r['title'][:48]:48} | {dict(sorted(r['hits'].items(), key=lambda x:-x[1])[:4])}")
