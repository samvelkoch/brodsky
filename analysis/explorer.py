"""Данные для интерактивных модулей артефакта. Пишет analysis/explorer.json.

Импортирует compute.py (очистка, леммы, словари полей) и добавляет:
силуэты стихотворений, метрики каждого стихотворения, индекс лемм для поиска,
эпитеты, рифменные пары, строфику, окончания строк, кривую словаря, карту эссе.
Полные тексты в выход не попадают: только числа, названия и не больше 2 строк-примеров
для 300 самых частых слов.
"""
import json
import math
import re
from collections import Counter, defaultdict
from functools import lru_cache

import numpy as np

import compute as K
from compute import (PERIODS, TOK, FIELDS, PROPER, CONTENT, STOPLEM, _e, clean_lines, content_lemmas, morph, poems,
                     prose, syll, tag)

HERE = K.HERE
NP = len(PERIODS)          # 6 периодов; индекс 6 — стихи без периода
FUNC = {"PREP", "CONJ", "PRCL"}
SKIP_POS = {"PREP", "CONJ", "PRCL", "INTJ"}
CYR_V = re.compile("[аеёиоуыэюяАЕЁИОУЫЭЮЯ]")


@lru_cache(maxsize=None)
def nf(w):
    return morph.parse(w)[0].normal_form


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
for i, o in enumerate(P):
    o["pid"] = i

# ---------- idf для характерных слов стихотворения
poem_cl = [list(content_lemmas(o)) for o in P]
df = Counter(l for cl in poem_cl for l in set(cl))
N = len(P)
field_names = list(FIELDS)

X = {"periods": [p[2] for p in PERIODS], "fields": field_names}
plist = []
stanza_by_per = [Counter() for _ in range(NP + 1)]
final_func_by_per = [[0, 0] for _ in range(NP + 1)]
final_func_words = Counter()
syl_hist_by_per = [Counter() for _ in range(NP + 1)]
rhyme_pairs = Counter()
for o, cl in zip(P, poem_cl):
    L = poem_lines(o["clean"])
    syl = [min(s, 40) for s, _ in L]
    real = [(s, t) for s, t in L if s]
    if not real:
        continue
    per = o["per"] if o["per"] is not None else NP
    sy = [s for s, _ in real]
    # части речи
    pos = Counter(str(tag(w.lower()).POS) for w in o["ctoks"])
    noun, verb = pos["NOUN"], pos["VERB"] + pos["INFN"]
    # концы строк
    ends_tok = [TOK.findall(t)[-1] for _, t in real]
    open_ = sum(t.rstrip()[-1].isalpha() for _, t in real)
    func_end = 0
    for w in ends_tok:
        if str(tag(w.lower()).POS) in FUNC:
            func_end += 1
            final_func_words[w.lower()] += 1
    final_func_by_per[per][0] += func_end
    final_func_by_per[per][1] += len(real)
    # рифма (как в compute.py) + пары рифм
    ends = [_e(w.lower()) for w in ends_tok]
    e3 = [w[-3:] if len(w) >= 3 else w for w in ends]
    hit = sum(1 for i, e in enumerate(e3) if any(e3[j] == e for j in range(max(0, i - 4), min(len(e3), i + 5)) if j != i))
    for i in range(len(ends)):
        for j in range(i + 1, min(len(ends), i + 5)):
            if e3[i] == e3[j] and ends[i] != ends[j] and len(ends[i]) >= 3 and len(ends[j]) >= 3:
                rhyme_pairs[tuple(sorted((ends[i], ends[j])))] += 1
    # строфы
    sizes, cur = [], 0
    for s, _ in L:
        if s:
            cur += 1
        else:
            sizes.append(cur); cur = 0
    sizes.append(cur)
    stanza_by_per[per].update(sizes)
    syl_hist_by_per[per].update(min(s, 30) for s in sy)
    # поля
    lk = Counter(_e(l.lower()) for l in o["clem"])
    fields = [sum(lk[w] for w in FIELDS[f]) for f in field_names]
    # характерные слова (tf-idf)
    tf = Counter(cl)
    top = sorted(tf, key=lambda w: -tf[w] * math.log(N / df[w]))[:6]
    plist.append({
        "t": o["title"], "y": o["year"], "p": per, "src": o["source"], "u": o["url"],
        "syl": syl, "n": len(real), "w": len(o["ctoks"]),
        "med": float(np.median(sy)), "mean": round(float(np.mean(sy)), 2),
        "nv": round(noun / verb, 2) if verb else None,
        "open": round(100 * open_ / len(real), 1), "rh": round(100 * hit / len(real), 1),
        "fe": round(100 * func_end / len(real), 1),
        "st": len(sizes), "stm": Counter(sizes).most_common(1)[0][0],
        "f": fields, "top": top,
    })
X["poems"] = plist

# ---------- индекс лемм
idx_poetry = defaultdict(lambda: [0] * (NP + 1))
idx_poems = defaultdict(set)
idx_prose = Counter()
display = {}
per_tokens = [0] * (NP + 1)
for o in P:
    per = o["per"] if o["per"] is not None else NP
    per_tokens[per] += len(o["ctoks"])
    for w, l in zip(o["ctoks"], o["clem"]):
        t = tag(w.lower())
        if str(t.POS) in SKIP_POS:
            continue
        k = _e(l.lower())
        if len(k) < 2 and k != "я":
            continue
        idx_poetry[k][per] += 1
        idx_poems[k].add(o["pid"])
        display.setdefault(k, l.capitalize() if l in PROPER else l)
for o in prose:
    for w, l in zip(o["ctoks"], o["clem"]):
        if str(tag(w.lower()).POS) in SKIP_POS:
            continue
        k = _e(l.lower())
        if len(k) < 2 and k != "я":
            continue
        idx_prose[k] += 1
        display.setdefault(k, l.capitalize() if l in PROPER else l)
keep = [k for k in set(idx_poetry) | set(idx_prose) if sum(idx_poetry[k]) >= 2 or idx_prose[k] >= 5]
keep.sort(key=lambda k: -(sum(idx_poetry[k]) + idx_prose[k]))
X["lex"] = {k: [display[k], idx_poetry[k], idx_prose[k], sorted(idx_poems[k])] for k in keep}
X["per_tokens"] = per_tokens
X["prose_tokens"] = sum(len(o["ctoks"]) for o in prose)
# знаменательные токены по периодам — знаменатель для сравнения периодов
X["per_content"] = [sum(1 for o in P if (o["per"] if o["per"] is not None else NP) == p for _ in content_lemmas(o))
                    for p in range(NP + 1)]
content_keys = {_e(l.lower()) for o in P for l in content_lemmas(o)}
X["content_keys"] = sorted(k for k in content_keys if k in X["lex"])

# ---------- примеры строк: 300 частых знаменательных слов, по 1–2 строки (самое раннее и самое позднее стихотворение)
cp = Counter(_e(l.lower()) for o in P for l in content_lemmas(o))
cand_lines = []  # (pid, строка, множество лемм) — считается один раз
for o in P:
    for s, line in poem_lines(o["clean"]):
        if s and 20 <= len(line) <= 80:
            cand_lines.append((o["pid"], line, {_e(nf(w.lower())) for w in TOK.findall(line)}))
examples = {}
for k, _ in cp.most_common(300):
    first = next((c for c in cand_lines if k in c[2]), None)
    last = next((c for c in reversed(cand_lines) if k in c[2]), None)
    pick = [c for c in (first, last) if c]
    if len(pick) == 2 and pick[0][0] == pick[1][0]:
        pick = pick[:1]
    if pick:
        examples[k] = [{"l": c[1], "pid": c[0]} for c in pick]
X["examples"] = examples

# ---------- эпитеты: прилагательное + существительное, согласованные по падежу и числу
IDIOMS = {("крайний", "мера"), ("хороший", "случай"), ("конечный", "счёт"), ("всякий", "случай"),
          ("худой", "конец"), ("самый", "дело"), ("полный", "мера")}  # устойчивые обороты, не эпитеты
SURF = defaultdict(Counter)


def epithets(objs):
    c = Counter()
    for o in objs:
        toks = [w.lower() for w in o["ctoks"]]
        for a, b in zip(toks, toks[1:]):
            ta, tb = tag(a), tag(b)
            if (ta.POS == "ADJF" and "Apro" not in ta and tb.POS == "NOUN" and ta.case == tb.case
                    and ta.number == tb.number and not ({"Name", "Surn", "Geox", "Patr"} & tb.grammemes)
                    and (ta.number == "plur" or ta.gender is None or ta.gender == tb.gender)):
                pair = (nf(a), nf(b))
                if pair in IDIOMS:
                    continue
                c[pair] += 1
                SURF[pair][f"{a} {b}"] += 1
    return c


ep_all = epithets(P)
surf = lambda pr: SURF[pr].most_common(1)[0][0]
X["epithets"] = {"all": [[surf((a, b)), n] for (a, b), n in ep_all.most_common(30)],
                 "by_period": [[[surf((a, b)), n] for (a, b), n in epithets([o for o in P if o["per"] == p]).most_common(10)]
                               for p in range(NP)]}
X["rhyme_pairs"] = [[a, b, n] for (a, b), n in rhyme_pairs.most_common(30)]

# ---------- строфика, конец строки, слоги по периодам
def stanza_buckets(c):
    tot = sum(c.values()) or 1
    b = [("1", [1]), ("2", [2]), ("3", [3]), ("4", [4]), ("5", [5]), ("6", [6]), ("7–8", [7, 8]),
         ("9–12", range(9, 13)), ("13+", range(13, 5000))]
    return [[lab, round(100 * sum(c[s] for s in rng) / tot, 1)] for lab, rng in b]


X["stanzas"] = [{"p": PERIODS[p][2], "b": stanza_buckets(stanza_by_per[p]), "n": sum(stanza_by_per[p].values())}
                for p in range(NP)]
X["final_func"] = {"by_period": [{"p": PERIODS[p][2], "share": round(100 * final_func_by_per[p][0] / final_func_by_per[p][1], 2),
                                  "n": final_func_by_per[p][1]} for p in range(NP)],
                   "words": [[w, n] for w, n in final_func_words.most_common(15)]}
X["syl_hist_by_period"] = [[syl_hist_by_per[p].get(s, 0) for s in range(1, 31)] for p in range(NP)]

# ---------- кривая роста словаря (закон Хипса), стихи в хронологическом порядке
seen, n_tok, heaps, step = set(), 0, [], 1500
for o in P:
    for l in o["clem"]:
        n_tok += 1
        seen.add(_e(l.lower()))
        if n_tok % step == 0:
            heaps.append([n_tok, len(seen), o["year"] or (PERIODS[o["per"]][1] if o["per"] is not None else None)])
heaps.append([n_tok, len(seen), None])
X["heaps"] = heaps

# ---------- эссе
essays = []
for o in prose:
    t = re.sub(r"\s+", " ", K.norm_punct(o["clean"]))
    sl = [len(TOK.findall(s)) for s in re.split(r"(?<=[.!?])\s+(?=[«\"(—A-ZА-ЯЁ0-9])", t) if TOK.search(s)]
    y = re.search(r"(19\d\d)", o["title"])
    w = len(o["ctoks"]) or 1
    essays.append({"t": o["title"], "y": int(y.group(1)) if y else None, "w": len(o["ctoks"]),
                   "sm": float(np.median(sl)) if sl else None, "s90": float(np.percentile(sl, 90)) if sl else None,
                   "dash": round(1000 * t.count("—") / w, 1), "par": round(1000 * t.count("(") / w, 1),
                   "src": o["source"]})
X["essays"] = essays

# ---------- места и имена раздельно для стихов и прозы
def names(objs):
    geo, sur = Counter(), Counter()
    for o in objs:
        for w in o["ctoks"]:
            if not w[0].isupper():
                continue
            t = tag(w.lower())
            n = nf(w.lower())
            if "Geox" in t and n not in K.GEO_AMBIG:
                geo[n] += 1
            elif "Surn" in t:
                sur[n] += 1
    return geo, sur


SUR_G = defaultdict(Counter)
for o in P + prose:
    for w in o["ctoks"]:
        if w[0].isupper() and "Surn" in tag(w.lower()):
            SUR_G[nf(w.lower())][morph.parse(w.lower())[0].tag.gender] += 1


def pretty_sur(w):
    p0 = next((p for p in morph.parse(w) if "Surn" in p.tag), morph.parse(w)[0])
    g = SUR_G[w].most_common(1)[0][0] if SUR_G[w] else p0.tag.gender
    f = p0.inflect({"nomn", "sing", g}) if g else p0.inflect({"nomn", "sing"})
    return (f.word if f else w).capitalize()


gp, sp = names(P)
gr, sr = names(prose)
X["names"] = {
    "geo": {"poetry": [[K.nomn(w), n] for w, n in gp.most_common(20)], "prose": [[K.nomn(w), n] for w, n in gr.most_common(20)]},
    "sur": {"poetry": [[pretty_sur(w), n] for w, n in sp.most_common(20)], "prose": [[pretty_sur(w), n] for w, n in sr.most_common(20)]},
}

# ---------- цвета по периодам
COL = {_e(k): (k, v) for k, v in K.COLORS.items()}
col_per = [Counter() for _ in range(NP)]
for o in P:
    if o["per"] is None:
        continue
    for l in o["clem"]:
        k = _e(l.lower())
        if k in COL:
            col_per[o["per"]][COL[k][0]] += 1
X["colors_by_period"] = [{"p": PERIODS[p][2], "c": [[w, K.COLORS[w], n] for w, n in col_per[p].most_common()]}
                         for p in range(NP)]

# ---------- поля: вклад каждой леммы по периодам и в прозе
drill = {}
per_lk = [Counter() for _ in range(NP)]
for o in P:
    if o["per"] is not None:
        per_lk[o["per"]].update(_e(l.lower()) for l in o["clem"])
pr_lk = Counter(_e(l.lower()) for o in prose for l in o["clem"])
for f in field_names:
    rows = [[w, [per_lk[p][w] for p in range(NP)], pr_lk[w]] for w in FIELDS[f]]
    rows.sort(key=lambda r: -(sum(r[1]) + r[2]))
    drill[f] = rows
X["field_drill"] = drill
X["per_lemmas"] = [sum(per_lk[p].values()) for p in range(NP)]
X["prose_lemmas"] = sum(pr_lk.values())

# ---------- силуэты венецианских стихов
vs = []
for r in K.VEN:
    if r["section_title"] != "Стихотворения":
        continue
    L = poem_lines(clean_lines(r["text"], poetry=True))
    vs.append({"t": r["title"], "y": K.PANICIERI_YEARS.get(r["title"]), "syl": [min(s, 40) for s, _ in L]})
vs.sort(key=lambda r: r["y"] or 0)
X["venice_sil"] = vs

out = HERE / "explorer.json"
json.dump(X, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("explorer.json", round(out.stat().st_size / 1024), "KB")
print("poems", len(plist), "lex", len(X["lex"]), "examples", len(examples), "content_keys", len(X["content_keys"]))
print("per_tokens", per_tokens, "per_content", X["per_content"])
print("epithets", X["epithets"]["all"][:12])
print("rhyme pairs", X["rhyme_pairs"][:12])
print("final func", X["final_func"])
print("stanzas", [(s["p"], s["b"][3]) for s in X["stanzas"]])
print("heaps end", heaps[-1])
print("essays", len(essays), sum(1 for e in essays if e["y"]))
print("geo poetry", X["names"]["geo"]["poetry"][:8]); print("geo prose", X["names"]["geo"]["prose"][:8])
print("sur poetry", X["names"]["sur"]["poetry"][:8])
print("undated/no period poems", sum(1 for p in plist if p["p"] == NP))
