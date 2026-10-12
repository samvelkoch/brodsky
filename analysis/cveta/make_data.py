"""Собирает cveta.json для раздела IV.4 «Цвета» из построчной разметки цвета.

Вход: corpus.pkl (корпус) и razmetka-po-strokam.json ({pid: {номер непустой строки: [оттенок, n|o|m, основание, уверенность 1-3]}}),
pid — номер в списке собственных русских стихотворений корпуса. Разметку делала модель по контексту строки (промпт в prompt-razmetki.md).
Выход: палитра в фиксированном порядке оттенков, сглаженные доли по годам для трёх режимов и по стихотворению список окрашенных строк.
Текстов строк в выходе нет.

python make_data.py ../corpus.pkl razmetka-po-strokam.json cveta.json
"""
import json, pickle, sys
from palette import PAL

corpus, razm, out = sys.argv[1:4]
own = [o for o in pickle.load(open(corpus, "rb")) if o["author"] == "own" and o["lang"] == "ru" and o["genre"] == "poetry"]
R = json.load(open(razm, encoding="utf-8"))
ORDER = ["белый", "бледный", "серебряный", "серый", "тёмно-серый", "чёрный", "ночной синий", "тёмно-синий", "синий", "голубой",
         "бирюзовый", "тёмно-зелёный", "зелёный", "оливковый", "охра", "жёлтый", "медовый", "золотой", "оранжевый", "кирпичный",
         "красный", "багровый", "розовый", "лиловый", "коричневый"]
assert set(ORDER) == set(PAL)
idx = {k: i for i, k in enumerate(ORDER)}
MODES = {"named": "n", "objects": "no", "all": "nom"}   # какие источники цвета входят в режим
Y = list(range(1957, 1997))
# недатированные — в середину периода по разделу собрания
SP = {"Стихотворения 1930—1960": 1958, "Стихотворения 1961—1966": 1963, "Стихотворения 1967—1972": 1970,
      "Стихотворения 1973—1984": 1978, "Стихотворения 1985—1989": 1987, "Стихотворения 1990—1996": 1993}
YEAR_FIX = {"Шествие (поэма)": 1961}   # в корпусе без года и вне разделов по периодам

raw = {m: [[0] * len(ORDER) for _ in Y] for m in MODES}
poems = []
for pid, lines in R.items():
    o = own[int(pid)]
    marks = sorted((int(i), c, s) for i, (c, s, *_) in lines.items())
    y = o["year"] or YEAR_FIX.get(o["title"])
    if y and Y[0] <= y <= Y[-1]:
        for _, c, s in marks:
            for m, ok in MODES.items():
                if s in ok: raw[m][y - Y[0]][idx[c]] += 1
    q = {"y": y, "t": o["title"][:60], "n": len([l for l in o["text"].splitlines() if l.strip()]),
         "c": [[i, idx[c], "nom".index(s)] for i, c, s in marks]}
    if not y: q["y"] = SP.get(o.get("period")); q["u"] = 1
    if q["y"]: poems.append(q)
poems.sort(key=lambda q: (q["y"], q.get("u", 0)))

W = [1, 2, 3, 2, 1]   # сглаживание по годам: окно в пять лет
sm = {}
for m in MODES:
    rows = []
    for i in range(len(Y)):
        acc = [0.0] * len(ORDER)
        for d, w in zip(range(-2, 3), W):
            if 0 <= i + d < len(Y):
                for k in range(len(ORDER)): acc[k] += w * raw[m][i + d][k]
        t = sum(acc) or 1
        rows.append([round(a / t, 4) for a in acc])
    sm[m] = rows
res = {"order": ORDER, "hex": [PAL[k] for k in ORDER], "years": Y, "sm": sm, "cnt": {m: [sum(r) for r in raw[m]] for m in MODES}, "poems": poems}
s = json.dumps(res, ensure_ascii=False, separators=(",", ":"))
open(out, "w", encoding="utf-8").write(s)
print(out, len(s), "байт,", len(poems), "стихотворений")
