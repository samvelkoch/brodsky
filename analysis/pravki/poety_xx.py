"""Бродский среди 34 поэтов XX века: те же меры, тот же подсчёт, один источник.

Источник: «Поэтический корпус русского языка» И. Гусева (github.com/IlyaGusev/PoetryCorpus, datasets/corpus/all.xml),
16 694 стихотворения 195 поэтов. Бродский берётся из этого же корпуса (93 стихотворения 1957–1979),
а не из нашего, чтобы у всех были одна типографика и один подсчёт.

python3 poety_xx.py [путь к all.xml] -> poety_xx.json рядом со скриптом"""
import collections
import functools
import json
import os
import re
import statistics as st
import sys
import urllib.request
import xml.etree.ElementTree as ET

import pymorphy3

URL = "https://raw.githubusercontent.com/IlyaGusev/PoetryCorpus/master/datasets/corpus/all.xml"
POETS = ["Иннокентий Анненский", "Анна Ахматова", "Эдуард Багрицкий", "Константин Бальмонт", "Александр Блок",
         "Валерий Брюсов", "Иван Бунин", "Максимилиан Волошин", "Николай Гумилев", "Сергей Есенин", "Вячеслав Иванов",
         "Осип Мандельштам", "Владимир Маяковский", "Борис Пастернак", "Игорь Северянин", "Владислав Ходасевич",
         "Марина Цветаева", "Саша Черный",
         "Павел Антокольский", "Белла Ахмадулина", "Константин Ваншенкин", "Андрей Вознесенский", "Владимир Высоцкий",
         "Евгений Долматовский", "Евгений Евтушенко", "Николай Заболоцкий", "Леонид Мартынов", "Булат Окуджава",
         "Давид Самойлов", "Илья Сельвинский", "Борис Слуцкий", "Арсений Тарковский", "Вероника Тушнова",
         "Василий Федоров"]
SHOW = {"Николай Гумилев": "Гумилёв", "Саша Черный": "Саша Чёрный", "Вячеслав Иванов": "Вяч. Иванов", "Василий Федоров": "В. Фёдоров"}

TOK = re.compile(r"[А-Яа-яЁёA-Za-z]+(?:-[А-Яа-яЁёA-Za-z]+)*")
VOW = re.compile(r"[аеёиоуыэюяАЕЁИОУЫЭЮЯ]")
FUNC = {"PREP", "CONJ", "PRCL"}
M = pymorphy3.MorphAnalyzer()


@functools.lru_cache(maxsize=None)
def an(w):
    p = M.parse(w)[0]
    return str(p.tag.POS), p.normal_form


def norm(t):  # как в compute.py, плюс короткое тире с пробелами
    return t.replace("--", "—").replace(" - ", " — ").replace(" – ", " — ").replace("…", "...")


MEASURES = [  # ключ, подпись, единица, функция(признаки)
    ("syl", "Слогов в строке", "в среднем"),
    ("prep", "Строка рвётся на предлоге, союзе", "% строк"),
    ("open", "Строка без знака в конце", "% строк"),
    ("dot", "Точки", "на 1000 слов"),
    ("lem", "Разных слов (лемм)", "на первые 10 000 слов"),
    ("excl", "Восклицательные знаки", "на 1000 слов"),
    ("adj", "Прилагательные", "% слов"),
    ("dash", "Тире", "на 1000 слов"),
]


def feats(texts):
    t = norm("\n".join(texts))
    toks = TOK.findall(t)
    w = len(toks)
    lines = [l for l in t.split("\n") if TOK.search(l)]
    low = [x.lower() for x in toks]
    pos = collections.Counter(an(x)[0] for x in low)
    return {
        "syl": st.mean(len(VOW.findall(l)) for l in lines),
        "prep": 100 * sum(an(TOK.findall(l)[-1].lower())[0] in FUNC for l in lines) / len(lines),
        "open": 100 * sum(l.rstrip()[-1].isalpha() for l in lines) / len(lines),
        "dot": 1000 * len(re.findall(r"(?<!\.)\.(?!\.)", t)) / w,
        "lem": len({an(x)[1] for x in low[:10000]}),
        "excl": 1000 * t.count("!") / w,
        "adj": 100 * (pos["ADJF"] + pos["ADJS"]) / w,
        "dash": 1000 * t.count("—") / w,
        "words": w, "poems": len(texts),
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "all.xml")
    if not os.path.exists(src):
        urllib.request.urlretrieve(URL, src)
    by = collections.defaultdict(list)
    years = collections.defaultdict(list)
    for it in ET.parse(src).getroot():
        a = (it.findtext("author") or "").strip()
        by[a].append(it.findtext("text") or "")
        y = it.findtext("date_from") or ""
        if y[:4].isdigit():
            years[a].append(int(y[:4]))
    out = {"source": "Поэтический корпус русского языка (И. Гусев)", "measures": [], "poets": []}
    rows = []
    for a, ts in by.items():
        if a in POETS or a == "Иосиф Бродский":
            f = feats(ts)
            if a != "Иосиф Бродский" and f["words"] < 10000:
                raise SystemExit(f"мало текста: {a}")
            rows.append((a, f))
    names = {a for a, _ in rows}
    missing = set(POETS) - names
    if missing:
        raise SystemExit(f"нет в корпусе: {missing}")
    for a, f in rows:
        yy = years.get(a) or [0]
        out["poets"].append({"name": "Бродский" if a == "Иосиф Бродский" else SHOW.get(a, a.split()[-1]),
                             "full": a, "brodsky": a == "Иосиф Бродский", "words": f["words"], "poems": f["poems"],
                             "years": [min(yy), max(yy)],
                             "v": {k: round(f[k], 2) for k, _, _ in MEASURES}})
    for k, label, unit in MEASURES:
        vals = sorted((p["v"][k] for p in out["poets"]), reverse=True)
        b = next(p for p in out["poets"] if p["brodsky"])["v"][k]
        out["measures"].append({"k": k, "label": label, "unit": unit, "rank": vals.index(b) + 1, "of": len(vals)})
    json.dump(out, open(os.path.join(here, "poety_xx.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for m in out["measures"]:
        print(m)


if __name__ == "__main__":
    main()
