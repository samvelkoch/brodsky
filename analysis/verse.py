"""Стиховедческий анализ по расставленным ударениям. Пишет analysis/verse.json.

Вход: poem_lines.json (строки в порядке explorer.py), accented.json (ruaccent: «+» перед ударной гласной),
corpus.pkl (для лемм прозы и морфологии). Ручной разметки нет: все классификаторы автоматические,
их допущения описаны в комментариях и в разделе «Методика» отчёта.
"""
import json
import math
import random
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pymorphy3

HERE = Path(__file__).parent
PERIODS = ["1957–1960", "1961–1966", "1967–1972", "1973–1984", "1985–1989", "1990–1996"]
NP = len(PERIODS)
VOW = "аеёиоуыэюя"
morph = pymorphy3.MorphAnalyzer()
random.seed(7)


@lru_cache(maxsize=None)
def tag(w):
    return morph.parse(w)[0].tag


@lru_cache(maxsize=None)
def nf(w):
    return morph.parse(w)[0].normal_form


poems = json.loads((HERE / "poem_lines.json").read_text(encoding="utf-8"))
acc = json.loads((HERE / "accented.json").read_text(encoding="utf-8"))
poems = [p for p in poems if str(p["pid"]) in acc and len(acc[str(p["pid"])]) == len(p["lines"])]
print("poems with accents:", len(poems))

WORD = re.compile(r"[А-Яа-яЁё+]+(?:-[А-Яа-яЁё+]+)*")


# ───────────────────────── слоговой профиль строки ─────────────────────────
def syllables(acc_line):
    """Слоги строки: 'S' — ударный слог многосложного слова, 'u' — безударный слог многосложного,
    's' — односложное слово с ударением (вероятно ударное), 'x' — односложное без ударения или неизвестно."""
    out, words = [], []
    acc_line = acc_line.replace("--", " ").replace("—", " ").replace("–", " ")
    for w in WORD.findall(acc_line):
        low = w.lower()
        vs = [i for i, ch in enumerate(low) if ch in VOW]
        if not vs:
            continue
        stressed = {i + 1 for i, ch in enumerate(low) if ch == "+" and i + 1 < len(low)}
        if len(vs) == 1:
            out.append("s" if stressed else "x")
        else:
            marks = ["S" if v in stressed else "u" for v in vs]
            if "S" not in marks:
                marks = ["x"] * len(vs)
            out += marks
        words.append(low)
    return out, words


METERS = {"ямб": (2, 1), "хорей": (2, 0), "дактиль": (3, 0), "амфибрахий": (3, 1), "анапест": (3, 2)}


def fits(sy, k, a):
    """Строка укладывается в метр: ни одного ударения многосложного слова на слабом месте."""
    return all(not (st == "S" and (i - a) % k != 0) for i, st in enumerate(sy)) and "S" in sy


def intervals(sy):
    pos = [i for i, st in enumerate(sy) if st in "Ss"]
    return [b - a - 1 for a, b in zip(pos, pos[1:]) if b - a - 1 > 0]


def feet(sy, k, a):
    last = max(i for i, st in enumerate(sy) if st in "Ss")
    return (last - a) // k + 1 if last >= a else 1


def classify_meter(lines_sy):
    ok = [l for l in lines_sy if sum(st in "Ss" for st in l) >= 2]
    if len(ok) < 3:
        return "мало данных", None, {}
    shares = {m: sum(fits(l, k, a) for l in ok) / len(ok) for m, (k, a) in METERS.items()}
    best = max(shares, key=shares.get)
    if shares[best] >= 0.85:
        k, a = METERS[best]
        fs = Counter(feet(l, k, a) for l in ok if fits(l, k, a))
        ft, n = fs.most_common(1)[0]
        return best, (ft if n / sum(fs.values()) >= 0.6 else None), shares
    # Неклассические размеры — по распределению промежутков между ударениями во всём стихотворении
    # (построчная проверка «всё или ничего» ломается на длинных строках из-за единичных пропусков ударения).
    iv = Counter(x for l in ok for x in intervals(l))
    tot = sum(iv.values()) or 1
    p1, p2, p3 = iv[1] / tot, iv[2] / tot, iv[3] / tot
    p5 = sum(v for k, v in iv.items() if k >= 5) / tot
    if p1 + p2 >= 0.75 and min(p1, p2) >= 0.15 and p3 < 0.12 and p5 <= 0.05:
        return "дольник", None, shares
    if p1 + p2 + p3 >= 0.85 and p3 >= 0.12 and p5 <= 0.05:
        return "тактовик", None, shares
    return "свободный", None, shares


# ───────────────────────── рифма ─────────────────────────
POST = str.maketrans({"о": "а", "е": "и", "я": "и", "э": "и", "ю": "у", "ы": "и", "ё": "о"})
STRESSED = {"я": "а", "ю": "у", "е": "э", "ё": "о", "ы": "и"}
DEVOICE = {"б": "п", "в": "ф", "г": "к", "д": "т", "ж": "ш", "з": "с"}


def clausula(acc_line):
    """Окончание строки от последней ударной гласной: (звуковой ключ, сырой хвост, опорная согласная,
    число слогов после ударения, составная ли рифма, последнее слово)."""
    acc_line = acc_line.replace("--", " ").replace("—", " ").replace("–", " ")
    low = acc_line.lower().replace("ё", "+ё") if "+" not in acc_line.lower() else acc_line.lower()
    low = re.sub(r"[^а-яё+\s-]", " ", low)
    low = re.sub(r"\s+", " ", low).strip()
    idx = low.rfind("+")
    if idx < 0 or idx + 1 >= len(low):
        return None
    words_tail = re.findall(r"[а-яё+]+(?:-[а-яё+]+)*", low)
    if words_tail:
        lw = words_tail[-1]
        if "+" not in lw and sum(ch in VOW for ch in lw) >= 2:   # ударение последнего слова неизвестно
            return None
    tail = low[idx + 1:]
    before = low[:idx].replace("+", "")
    tail = tail.replace("+", "")
    compound = " " in tail.strip()
    t = tail.replace(" ", "").replace("-", "")
    if not t or t[0] not in VOW:
        return None
    t = re.sub(r"т?ь?ся$", "ца", t).replace("сч", "щ").replace("ъ", "").replace("ь", "")
    head = STRESSED.get(t[0], t[0])
    rest = t[1:].translate(POST)
    if rest and rest[-1] in DEVOICE:
        rest = rest[:-1] + DEVOICE[rest[-1]]
    rest = re.sub(r"(.)\1", r"\1", rest)
    key = head + rest
    sup = ""
    for ch in reversed(before.replace(" ", "").replace("-", "")):
        if ch in "ьъ":
            continue
        sup = "" if ch in VOW else ch
        break
    post_syl = sum(ch in VOW for ch in rest)
    last_word = re.findall(r"[а-яё]+(?:-[а-яё]+)*", acc_line.lower().replace("+", ""))
    return key, tail.strip(), sup, post_syl, compound, (last_word[-1] if last_word else "")


def lev(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (ca != cb))
    return d[-1]


def cons(s):
    return "".join(ch for ch in s if ch not in VOW)


def rhyme_type(c1, c2):
    """'точная' | 'неточная' | 'созвучие' | None. c = результат clausula()."""
    if not c1 or not c2 or c1[5] == c2[5]:
        return None
    k1, k2 = c1[0], c2[0]
    if k1[0] != k2[0] or c1[3] != c2[3]:
        return None
    if k1 == k2:
        if len(k1) == 1 and c1[2] != c2[2]:        # открытая мужская рифма требует общей опорной согласной
            return "созвучие"
        return "точная"
    if c1[3] == 0 and ((k1[-1] in VOW) != (k2[-1] in VOW)):   # мужская: открытый слог не рифмуется с закрытым
        return None
    a, b = cons(k1[1:]), cons(k2[1:])
    if a.rstrip("й") == b.rstrip("й"):
        return "неточная"
    if lev(a, b) <= 1 and (c1[3] >= 1 or min(len(a), len(b)) >= 2):   # мужская «ночь — бой» не рифма
        return "неточная"
    if a[-1:] == b[-1:]:
        return "созвучие"
    return None


# ───────────────────────── проход по стихотворениям ─────────────────────────
meter_by_poem, rhyme_dict, rhyme_pairs = [], defaultdict(Counter), Counter()
poem_feats = {}
meter_examples = defaultdict(list)     # размер → [(строка с ударениями, схема, pid)]
rhyme_type_ex = defaultdict(list)      # тип рифмы / окончания → [(слово, слово, pid)]
scheme_ex = {}                         # схема строфы → (4 конечных слова, pid)
enj_ex = []                            # перенос на служебном слове: (строка, следующая, pid)


def pattern(sy):
    return "-".join("ТА" if st in "Ss" else "та" for st in sy)
per = {k: [Counter() for _ in range(NP + 1)] for k in
       ("meter_lines", "rtype", "claus", "scheme4", "rich", "compound", "gram", "enj", "sent")}
scheme_all = Counter()
examples = {"compound": [], "rich": [], "long": []}
meter_check = {}
line_records = []   # (per, syllables-профиль) для звука

for p in poems:
    pid, pr = p["pid"], (p["per"] if p["per"] is not None else NP)
    A = acc[str(pid)]
    raw = p["lines"]
    sy_lines, cl, stanza_of, idx_real = [], [], [], []
    st = 0
    for i, (r, a) in enumerate(zip(raw, A)):
        if not r:
            st += 1
            continue
        sy, _ = syllables(a)
        sy_lines.append(sy)
        cl.append(clausula(a))
        stanza_of.append(st)
        idx_real.append(i)
        line_records.append((pr, r))
    if not sy_lines:
        continue
    meter, ft, shares = classify_meter(sy_lines)
    meter_by_poem.append({"pid": pid, "m": meter, "ft": ft, "n": len(sy_lines)})
    real_acc = [a for r, a in zip(raw, A) if r]
    for sy, a_line in zip(sy_lines, real_acc):
        plain = a_line.replace("+", "")
        if not (22 <= len(plain) <= 58) or len(meter_examples[meter]) >= 40:
            continue
        nS = sum(st in "Ss" for st in sy)
        iv = intervals(sy)
        if nS == 0:
            continue
        if meter in METERS:
            k, a0 = METERS[meter]
            last = max(i for i, st in enumerate(sy) if st in "Ss")
            ict = [i for i in range(a0, last + 1, k)]
            good = (fits(sy, k, a0) and len(ict) >= 3 and all(sy[i] in "Ss" for i in ict)
                    and not any(st in "Ss" for i, st in enumerate(sy) if (i - a0) % k != 0))
        elif meter == "дольник":
            good = 1 in iv and 2 in iv and all(x in (1, 2) for x in iv)
        elif meter == "тактовик":
            good = 3 in iv and all(x in (1, 2, 3) for x in iv)
        else:
            good = nS >= 4 and any(x >= 4 for x in iv)
        if good:
            meter_examples[meter].append((a_line, pattern(sy), pid))
    per["meter_lines"][pr][meter] += len(sy_lines)
    if p["t"] in ("Лагуна", "Письма римскому другу", "Рождественский романс", "Ни страны, ни погоста",
                  "Большая элегия Джону Донну", "Я входил вместо дикого зверя в клетку", "Сретенье"):
        meter_check[p["t"]] = [meter, ft, {k: round(v, 2) for k, v in shares.items()}]
    # клаузулы
    for c in cl:
        if c:
            per["claus"][pr][min(c[3], 3)] += 1
    # рифмы: партнёр в окне 4 строк, не дальше соседней строфы
    n = len(cl)
    partner = [None] * n
    for i in range(n):
        for j in range(i + 1, min(n, i + 5)):
            if stanza_of[j] - stanza_of[i] > 1:
                break
            t = rhyme_type(cl[i], cl[j])
            if t in ("точная", "неточная") or (t == "созвучие" and j - i <= 2):
                if partner[i] is None:
                    partner[i] = (j, t)
                if partner[j] is None:
                    partner[j] = (i, t)
                w1, w2 = cl[i][5], cl[j][5]
                ok_ex = len(w1) >= 3 and len(w2) >= 3
                if ok_ex and len(rhyme_type_ex[t]) < 60:
                    rhyme_type_ex[t].append((w1, w2, pid))
                ck = ["мужская", "женская", "дактилическая", "гипердактилическая"][min(cl[i][3], 3)]
                if ok_ex and t == "точная" and len(rhyme_type_ex[ck]) < 60:
                    rhyme_type_ex[ck].append((w1, w2, pid))
                rhyme_dict[w1][w2] += 1; rhyme_dict[w2][w1] += 1
                rhyme_pairs[tuple(sorted((w1, w2)))] += 1
                if t == "точная":
                    if cl[i][2] and cl[i][2] == cl[j][2]:
                        per["rich"][pr]["богатая"] += 1
                        if len(examples["rich"]) < 400:
                            examples["rich"].append((w1, w2, pid, len(cl[i][0])))
                    else:
                        per["rich"][pr]["обычная"] += 1
                    if len(cl[i][0]) >= 5 and len(examples["long"]) < 400:
                        examples["long"].append((w1, w2, pid, len(cl[i][0])))
                if cl[i][4] or cl[j][4]:
                    per["compound"][pr]["составная"] += 1
                    if len(examples["compound"]) < 300:
                        two = lambda k: " ".join(re.findall(r"[а-яё]+", real_acc[k].lower().replace("+", ""))[-2:])
                        examples["compound"].append((two(i) if cl[i][4] else w1, two(j) if cl[j][4] else w2, pid))
                else:
                    per["compound"][pr]["простая"] += 1
                t1, t2 = tag(w1), tag(w2)
                same = t1.POS == t2.POS and t1.POS in ("VERB", "INFN", "NOUN", "ADJF") and w1[-2:] == w2[-2:]
                per["gram"][pr]["однородная" if same else "разнородная"] += 1
                break
    rt = Counter(partner[i][1] if partner[i] else "без рифмы" for i in range(n))
    for k, v in rt.items():
        per["rtype"][pr][k] += v
    fem = sum(1 for c in cl if c and c[3] >= 1)
    poem_feats[pid] = {"exact": round(rt["точная"] / n, 3), "unrh": round(rt["без рифмы"] / n, 3),
                       "fem": round(fem / n, 3), "meter": meter}
    # схемы четверостиший
    for s_id in sorted(set(stanza_of)):
        ids = [i for i in range(n) if stanza_of[i] == s_id]
        if len(ids) != 4:
            continue
        lab, letters = {}, []
        for i in ids:
            pt = partner[i]
            if pt and pt[0] in lab:
                letters.append(lab[pt[0]])
            else:
                L = "ABCD"[len(set(letters) - {'-'})] if pt else "-"
                letters.append(L)
            lab[i] = letters[-1]
        sch = "".join(letters)
        if sch in ("ABAB", "AABB", "ABBA") and sch not in scheme_ex:
            scheme_ex[sch] = ([cl[i][5] for i in ids], pid)
        name = {"AABB": "парная (ААББ)", "ABAB": "перекрёстная (АБАБ)", "ABBA": "опоясывающая (АББА)"}.get(sch, "другая")
        if "-" in sch and sch.count("-") >= 2:
            name = "без рифмы"
        per["scheme4"][pr][name] += 1
        scheme_all[sch] += 1

# ───────────────────────── сводки по рифме и метру ─────────────────────────
def shares(counter_list, keys):
    return [{k: round(100 * c[k] / max(1, sum(c.values())), 1) for k in keys} | {"n": sum(c.values())}
            for c in counter_list[:NP]]


METER_KEYS = ["ямб", "хорей", "дактиль", "амфибрахий", "анапест", "дольник", "тактовик", "свободный"]
V = {"periods": PERIODS}
V["meter"] = {"by_period": shares(per["meter_lines"], METER_KEYS), "keys": METER_KEYS,
              "poems": Counter(m["m"] for m in meter_by_poem),
              "feet": Counter(f"{m['ft']}-стопный {m['m']}" for m in meter_by_poem if m["ft"]).most_common(12),
              "check": meter_check}
V["meter_by_poem"] = {m["pid"]: [m["m"], m["ft"]] for m in meter_by_poem}
V["rhyme"] = {
    "type": shares(per["rtype"], ["точная", "неточная", "созвучие", "без рифмы"]),
    "clausula": shares(per["claus"], [0, 1, 2, 3]),
    "rich": shares(per["rich"], ["богатая", "обычная"]),
    "compound": shares(per["compound"], ["составная", "простая"]),
    "gram": shares(per["gram"], ["однородная", "разнородная"]),
    "scheme4": shares(per["scheme4"], ["перекрёстная (АБАБ)", "парная (ААББ)", "опоясывающая (АББА)", "другая", "без рифмы"]),
    "top_pairs": [[a, b, n] for (a, b), n in rhyme_pairs.most_common(40)],
    "schemes_all": scheme_all.most_common(12),
}
# словарь рифм: слово → партнёры (слова с ≥1 рифмой; для отчёта — 4000 самых «рифмуемых»)
rd = sorted(rhyme_dict.items(), key=lambda kv: -sum(kv[1].values()))
V["rhyme_dict"] = {w: [[x, n] for x, n in c.most_common(14)] for w, c in rd[:4000]}
V["rhyme_dict_size"] = len(rhyme_dict)
seen = set()


def uniq(lst, k=24, key=lambda r: tuple(sorted(r[:2]))):
    out = []
    for r in lst:
        kk = key(r)
        if kk in seen:
            continue
        seen.add(kk); out.append(r)
        if len(out) >= k:
            break
    return out


V["rhyme_examples"] = {
    "long": uniq(sorted(examples["long"], key=lambda r: -r[3])),
    "rich": uniq(random.sample(examples["rich"], min(200, len(examples["rich"])))),
    "compound": uniq(examples["compound"], 30),
}

# ───────────────────────── звук: аллитерация против случайных строк ─────────────────────────
CONS = set("бвгджзклмнпрстфхцчшщ")
FUNC_SHORT = {"в", "во", "на", "и", "но", "не", "ни", "по", "за", "из", "от", "до", "к", "ко", "с", "со", "у", "о",
              "об", "же", "ли", "бы", "что", "как", "так", "то", "там", "тут", "где", "его", "её", "их", "мне", "меня"}


def initials(line):
    ws = [w for w in re.findall(r"[а-яё]+", line.lower()) if len(w) >= 3 and w not in FUNC_SHORT]
    return [w[0] for w in ws if w[0] in CONS], ws


def allit(line):
    _, ws = initials(line)
    c = Counter(w[0] for w in set(ws) if w[0] in CONS)
    return max(c.values()) if c else 0, (c.most_common(1)[0][0] if c else None)


word_pool = [[] for _ in range(NP + 1)]
line_len = [[] for _ in range(NP + 1)]
obs = [[0, 0] for _ in range(NP + 1)]
hot_cons = Counter()
top_lines = []
for pr, line in line_records:
    ini, ws = initials(line)
    word_pool[pr] += ws; line_len[pr].append(len(ws))
    sc, ch = allit(line)
    obs[pr][1] += 1
    if sc >= 3:
        obs[pr][0] += 1; hot_cons[ch] += 1
        dens = sc / max(1, len(ws))
        if sc >= 4 and 25 <= len(line) <= 70:
            top_lines.append((sc, dens, line, ch))
base = []
for pr in range(NP):
    pool, lens, hit, tot = word_pool[pr], line_len[pr], 0, 0
    for _ in range(20):
        for L in lens:
            ws = random.sample(pool, L) if L <= len(pool) else []
            c = Counter(w[0] for w in set(ws) if w[0] in CONS)
            hit += (max(c.values()) if c else 0) >= 3; tot += 1
    base.append(round(100 * hit / tot, 2) if tot else None)
V["sound"] = {
    "by_period": [{"obs": round(100 * obs[p][0] / max(1, obs[p][1]), 2), "base": base[p], "n": obs[p][1]} for p in range(NP)],
    "hot_consonants": hot_cons.most_common(12),
    "top_lines": [[l, ch, sc] for sc, d, l, ch in sorted(top_lines, key=lambda r: (-r[0], -r[1]))[:10]],
}

# любимые согласные стихов относительно прозы того же автора
import pickle  # noqa: E402
C = pickle.load(open(HERE / "corpus.pkl", "rb"))
prose_txt = " ".join(o["text"].lower() for o in C if o["author"] == "own" and o["lang"] == "ru" and o["genre"] == "prose")
poem_txt = " ".join(l.lower() for _, l in line_records)
cp, cr = Counter(ch for ch in poem_txt if ch in CONS), Counter(ch for ch in prose_txt if ch in CONS)
tp, tr = sum(cp.values()), sum(cr.values())
V["sound"]["consonant_ratio"] = sorted([[ch, round((cp[ch] / tp) / (cr[ch] / tr), 3)] for ch in CONS if cr[ch]],
                                       key=lambda r: -r[1])

# ───────────────────────── фраза и строфа ─────────────────────────
SENT_END = re.compile(r"[.!?…]+[»\"')]*(?=\s|$)")
sent_rows = [[] for _ in range(NP + 1)]
cross_stanza = [[0, 0] for _ in range(NP + 1)]
adj_noun = [[0, 0] for _ in range(NP + 1)]
longest_sent = []
for p in poems:
    pr = p["per"] if p["per"] is not None else NP
    raw = p["lines"]
    li = st = 0
    start_line, start_st, cur_lines = 0, 0, 0
    real = []
    for r in raw:
        if not r:
            st += 1
            continue
        real.append((li, st, r)); li += 1
    # предложения
    s_line, s_st = 0, 0
    my_sent, my_cross = [], 0
    for k, (li, st, r) in enumerate(real):
        if k == 0:
            s_line, s_st = li, st
        ends = list(SENT_END.finditer(r))
        if ends:
            span_lines = li - s_line + 1
            span_st = st - s_st + 1
            sent_rows[pr].append(span_lines); my_sent.append(span_lines); my_cross += span_st > 1
            cross_stanza[pr][0] += span_st > 1; cross_stanza[pr][1] += 1
            if span_lines >= 20:
                longest_sent.append((span_lines, span_st, p["pid"]))
            tail = r[ends[-1].end():].strip()
            if tail and re.search(r"[А-Яа-яЁё]", tail):   # новое предложение началось в этой же строке
                s_line, s_st = li, st
            else:
                s_line, s_st = li + 1, st
                if k + 1 < len(real):
                    s_line, s_st = real[k + 1][0], real[k + 1][1]
    if p["pid"] in poem_feats and my_sent:
        poem_feats[p["pid"]]["sent"] = round(float(np.mean(my_sent)), 2)
        poem_feats[p["pid"]]["cross"] = round(my_cross / len(my_sent), 3)
    # разрыв «прилагательное | существительное» на стыке строк
    for (li, st, r), nxt in zip(real, real[1:]):
        lastw = re.findall(r"[А-Яа-яЁё]+", r)
        if lastw and re.search(r"[А-Яа-яЁё]$", r.rstrip()) and str(tag(lastw[-1].lower()).POS) == "PREP" \
                and len(enj_ex) < 40 and 15 <= len(r) <= 60 and 10 <= len(nxt[2]) <= 60:
            enj_ex.append((r.strip(), nxt[2].strip(), p["pid"]))
        if not re.search(r"[А-Яа-яЁё]$", r.rstrip()):
            adj_noun[pr][1] += 1
            continue
        a = re.findall(r"[А-Яа-яЁё]+", r)[-1].lower()
        b = re.findall(r"[А-Яа-яЁё]+", nxt[2])
        adj_noun[pr][1] += 1
        if b:
            ta, tb = tag(a), tag(b[0].lower())
            if ta.POS == "ADJF" and tb.POS == "NOUN" and ta.case == tb.case and ta.number == tb.number:
                adj_noun[pr][0] += 1
seen_long = set()
V["phrase"] = {
    "by_period": [{"med_lines": float(np.median(sent_rows[p])) if sent_rows[p] else None,
                   "mean_lines": round(float(np.mean(sent_rows[p])), 2) if sent_rows[p] else None,
                   "p90_lines": float(np.percentile(sent_rows[p], 90)) if sent_rows[p] else None,
                   "cross_stanza": round(100 * cross_stanza[p][0] / max(1, cross_stanza[p][1]), 1),
                   "adj_noun": round(100 * adj_noun[p][0] / max(1, adj_noun[p][1]), 2),
                   "n": len(sent_rows[p])} for p in range(NP)],
    "hist": {str(k): v for k, v in sorted(Counter(min(x, 25) for p in range(NP + 1) for x in sent_rows[p]).items())},
    "longest": [r for r in sorted(longest_sent, reverse=True)
                if not (r[2] in seen_long or seen_long.add(r[2]))][:12],
}

# ───────────────────────── сравнения и родительные формулы ─────────────────────────
SIM = {"словно": r"\bсловно\b", "будто": r"\bбудто\b", "как будто": r"\bкак будто\b", "подобно": r"\bподобно\b",
       "точно (в значении «как»)": r"[,—]\s*точно\b", "как (после запятой)": r",\s*как\b(?!\s+будто)"}
sim_rows = []
gen = Counter()
gen_per = [Counter() for _ in range(NP)]
words_per = [0] * (NP + 1)
for pr in range(NP + 1):
    txt = "\n".join(l for q, l in line_records if q == pr).lower()
    words_per[pr] = len(re.findall(r"[а-яё]+", txt))
    if pr < NP:
        sim_rows.append({k: round(1000 * len(re.findall(rx, txt)) / max(1, words_per[pr]), 2) for k, rx in SIM.items()})
for q, l in line_records:
    toks = re.findall(r"[А-Яа-яЁё]+", l)
    for a, b in zip(toks, toks[1:]):
        ta, tb = tag(a.lower()), tag(b.lower())
        if ta.POS == "NOUN" and tb.POS == "NOUN" and tb.case == "gent" and "Name" not in tb and "Surn" not in tb \
                and a[0].islower() and b[0].islower() and a.lower() != b.lower():
            k = f"{a.lower()} {b.lower()}"
            gen[k] += 1
            if q < NP:
                gen_per[q][k] += 1
V["figures"] = {"similes": sim_rows, "simile_keys": list(SIM),
                "genitive_top": gen.most_common(30),
                "genitive_rate": [round(1000 * sum(gen_per[p].values()) / max(1, words_per[p]), 2) for p in range(NP)]}

V["poem_feats"] = poem_feats
rnd = random.Random(11)
V_enj = enj_ex


def pick(lst, k):
    by_pid, out = {}, []
    for r in lst:
        by_pid.setdefault(r[-1], r)
    cand = list(by_pid.values()); rnd.shuffle(cand)
    return cand[:k]


V["examples"] = {
    "meter": {m: [[a, pat, pid] for a, pat, pid in pick(v, 3)] for m, v in meter_examples.items()},
    "rhyme": {t: [[a, b, pid] for a, b, pid in pick(v, 4)] for t, v in rhyme_type_ex.items()},
    "scheme": {k: [v[0], v[1]] for k, v in scheme_ex.items()},
    "enj": [list(r) for r in pick(enj_ex, 3)],
}
json.dump(V, open(HERE / "verse.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(json.dumps({k: V[k] for k in ("meter",)}, ensure_ascii=False)[:1800])
print("rhyme type", V["rhyme"]["type"])
print("claus", V["rhyme"]["clausula"])
print("scheme4", V["rhyme"]["scheme4"])
print("top pairs", V["rhyme"]["top_pairs"][:15])
print("sound", V["sound"]["by_period"], V["sound"]["hot_consonants"][:6])
print("phrase", V["phrase"]["by_period"])
print("similes", V["figures"]["similes"])
print("genitive", V["figures"]["genitive_top"][:15])
