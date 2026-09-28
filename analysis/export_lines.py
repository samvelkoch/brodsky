"""Выгружает строки стихотворений (в порядке и с очисткой explorer.py) для расстановки ударений."""
import json
import re
import compute as K
from compute import PERIODS, poems, syll

CYR_V = re.compile("[аеёиоуыэюяАЕЁИОУЫЭЮЯ]")

def poem_lines(text):
    """[(слоги, строка)], 0 — граница строфы. Строки без русских гласных (римские цифры) — тоже граница."""
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s or not CYR_V.search(s):
            if out and out[-1][0] != 0:
                out.append((0, ""))
            continue
        out.append((syll(s), s))
    while out and out[-1][0] == 0:
        out.pop()
    while out and out[0][0] == 0:
        out.pop(0)
    return out


def sort_key(o):
    if o["year"]:
        return (o["year"], 0, o["idx"])
    if o["per"] is not None:
        return (PERIODS[o["per"]][1], 1, o["idx"])      # без даты — в конец своего периода
    return (9999, 2, o["idx"])


P = sorted(poems, key=sort_key)
out = [{"pid": i, "t": o["title"], "y": o["year"], "per": o["per"], "lines": [t for s, t in poem_lines(o["clean"])]}
       for i, o in enumerate(P)]
json.dump(out, open(K.HERE / "poem_lines.json", "w", encoding="utf-8"), ensure_ascii=False)
print("poems", len(out), "lines", sum(1 for p in out for l in p["lines"] if l))
