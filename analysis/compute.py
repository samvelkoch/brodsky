"""Статистика корпуса для артефакта. Пишет analysis/stats.json (только агрегаты).

Корпус анализа: собственные тексты Бродского на русском (author == "own", lang == "ru"):
стихи и проза раздельно. Переводы чужих стихов, интервью и биография исключены.
"""
import json
import math
import pickle
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pymorphy3

HERE = Path(__file__).parent
C = pickle.load(open(HERE / "corpus.pkl", "rb"))
morph = pymorphy3.MorphAnalyzer()

PERIODS = [(1957, 1960, "1957–1960"), (1961, 1966, "1961–1966"), (1967, 1972, "1967–1972"),
           (1973, 1984, "1973–1984"), (1985, 1989, "1985–1989"), (1990, 1996, "1990–1996")]
SITE_PERIOD = {"Стихотворения 1930—1960": 0, "Стихотворения 1961—1966": 1, "Стихотворения 1967—1972": 2,
               "Стихотворения 1973—1984": 3, "Стихотворения 1985—1989": 4, "Стихотворения 1990—1996": 5}
VOW = set("аеёиоуыэюяАЕЁИОУЫЭЮЯ")
TOK = re.compile(r"[А-Яа-яЁёA-Za-z]+(?:-[А-Яа-яЁёA-Za-z]+)*")
EDITORIAL = re.compile(r"С\.\s?В\.|Текст (приводится|по )|Источник|отсутствует в СИБ|^\s*\*|^\s*\d{1,2}\s+[\x22«(А-ЯA-Z]|"
                       r"^\s*Примечани|^\s*<\.\.\.>\s*$")
MONTHS = r"январ|феврал|март|апрел|ма[йя]|июн|июл|август|сентябр|октябр|ноябр|декабр"
DATE_LINE = re.compile(rf"^\s*[<(\[]?\s*(({MONTHS})[а-я]*\s*)?(19\d\d|\d{{2}})[\s,\-–—?>\])]*(\d{{4}})?.{{0,40}}$", re.I)


@lru_cache(maxsize=None)
def tag(w):
    return morph.parse(w)[0].tag


DROPPED_LONG = []


def clean_lines(text, poetry=False):
    out = []
    for ln in text.split("\n"):
        if EDITORIAL.search(ln):
            continue
        if poetry and len(TOK.findall(ln)) > 28:  # абзац прозы/комментария внутри стихотворной записи
            DROPPED_LONG.append(ln[:80])
            continue
        s = ln.strip()
        if s and DATE_LINE.match(s) and len(s) < 60 and re.search(r"19\d\d|\d{2}\s*$", s) and len(TOK.findall(s)) <= 6:
            continue
        out.append(ln)
    return "\n".join(out)


def syll(s):
    return sum(ch in VOW for ch in s)


def period_of(o):
    if o["year"]:
        for i, (a, b, _) in enumerate(PERIODS):
            if a <= o["year"] <= b:
                return i
    return SITE_PERIOD.get(o.get("period"))


own = [o for o in C if o["author"] == "own" and o["lang"] == "ru"]
poems = [o for o in own if o["genre"] == "poetry"]
prose = [o for o in own if o["genre"] == "prose"
         and not o["title"].startswith('Набережная неисцелимых - "Fondamenta')]  # дубль полной редакции СИБ
en_poems = [o for o in C if o["author"] == "own" and o["lang"] == "en" and o["genre"] == "poetry"]

# --- очищенные тексты и леммы
for o in own + en_poems:
    o["clean"] = clean_lines(o["text"], poetry=o["genre"] == "poetry")
    toks = TOK.findall(o["clean"])
    o["ctoks"] = toks
    if o["lang"] == "ru":
        o["clem"] = [tag(w.lower()) and morph.parse(w.lower())[0].normal_form for w in toks]
    o["per"] = period_of(o) if o in poems else None

S = {}
S["overview"] = {
    "poems": len(poems), "prose": len(prose), "en_poems": len(en_poems),
    "poem_words": sum(len(o["ctoks"]) for o in poems), "prose_words": sum(len(o["ctoks"]) for o in prose),
    "en_words": sum(len(o["ctoks"]) for o in en_poems),
    "unique_lemmas": len({l for o in own for l in o["clem"]}),
    "excluded": dict(Counter(o["author"] for o in C if not (o["author"] == "own" and o["lang"] == "ru")
                             and not (o["author"] == "own" and o["lang"] == "en"))),
    "total_records": len(C),
}

# --- хронология
yrs = Counter(o["year"] for o in poems if o["year"] and 1955 <= o["year"] <= 1996)
S["years"] = {"counts": {str(y): yrs.get(y, 0) for y in range(1956, 1997)},
              "dated": sum(yrs.values()), "total": len(poems)}
xmas = Counter(o["year"] for o in poems if o["year"] and re.search(r"рождеств", (o["title"] + o["clean"][:400]).lower()))
S["christmas"] = {"by_year": {str(y): xmas.get(y, 0) for y in range(1960, 1997)},
                  "titles": sorted({o["title"] for o in poems if re.search(r"рождеств", o["title"].lower())})}

# --- строки: длина в слогах, число строк
line_rows = []
per_poem = []
for o in poems:
    lines = [l for l in o["clean"].split("\n") if l.strip() and TOK.search(l)]
    sy = [syll(l) for l in lines]
    if not lines:
        continue
    per_poem.append({"t": o["title"], "y": o["year"], "p": o["per"], "lines": len(lines),
                     "med_syl": float(np.median(sy)), "words": len(o["ctoks"])})
    for l, s in zip(lines, sy):
        line_rows.append((o["year"], o["per"], s, l))
by_year_syl = defaultdict(list)
for y, p, s, l in line_rows:
    if y and 1957 <= y <= 1996:
        by_year_syl[y].append(s)
S["line_syllables_by_year"] = [{"y": y, "n": len(v), "q1": float(np.percentile(v, 25)), "med": float(np.median(v)),
                                "q3": float(np.percentile(v, 75))} for y, v in sorted(by_year_syl.items()) if len(v) >= 40]
by_per_syl = defaultdict(list)
for y, p, s, l in line_rows:
    if p is not None:
        by_per_syl[p].append(s)
S["line_syllables_by_period"] = [{"p": PERIODS[p][2], "mean": round(float(np.mean(v)), 2), "med": float(np.median(v)),
                                  "n": len(v)} for p, v in sorted(by_per_syl.items())]
hist = Counter(min(s, 30) for _, _, s, _ in line_rows)
S["line_syllable_hist"] = [{"s": s, "n": hist.get(s, 0)} for s in range(1, 31)]
lp = defaultdict(list)
for r in per_poem:
    if r["p"] is not None:
        lp[r["p"]].append(r["lines"])
S["lines_per_poem_by_period"] = [{"p": PERIODS[p][2], "med": float(np.median(v)), "q1": float(np.percentile(v, 25)),
                                  "q3": float(np.percentile(v, 75)), "n": len(v), "max": int(max(v))}
                                 for p, v in sorted(lp.items())]

# --- словарь: топ лемм (знаменательные)
CONTENT = {"NOUN", "ADJF", "ADJS", "VERB", "INFN"}
STOPLEM = {"быть", "мочь", "весь", "свой", "который", "такой", "самый", "этот", "тот", "стать", "один", "иметь",
           "сказать", "говорить", "есть", "другой", "каждый", "должный", "год", "раз", "время_"}


_cap, _all = Counter(), Counter()
for o in own:
    for w, l in zip(o["ctoks"], o["clem"]):
        _all[l] += 1
        _cap[l] += w[0].isupper()
PROPER = {l for l, n in _all.items() if _cap[l] / n >= 0.6}  # чаще с заглавной — имя собственное


def content_lemmas(o):
    for w, l in zip(o["ctoks"], o["clem"]):
        t = tag(w.lower())
        if (t.POS in CONTENT and l not in STOPLEM and len(l) > 1 and l not in PROPER
                and not ({"Apro", "Name", "Surn", "Patr", "Geox", "Orgn", "Abbr"} & t.grammemes)):
            yield l


cp = Counter(l for o in poems for l in content_lemmas(o))
cr = Counter(l for o in prose for l in content_lemmas(o))
wp = S["overview"]["poem_words"]; wr = S["overview"]["prose_words"]


def pos_of(l):
    return str(morph.parse(l)[0].tag.POS)


def top(counter, words, pos_set, k=20):
    rows = [(l, c) for l, c in counter.most_common(1500) if pos_of(l) in pos_set][:k]
    return [{"w": l, "n": c, "per10k": round(1e4 * c / words, 1)} for l, c in rows]


S["top_nouns"] = {"poetry": top(cp, wp, {"NOUN"}), "prose": top(cr, wr, {"NOUN"})}
S["top_verbs"] = {"poetry": top(cp, wp, {"VERB", "INFN"}), "prose": top(cr, wr, {"VERB", "INFN"})}
S["top_adj"] = {"poetry": top(cp, wp, {"ADJF", "ADJS"}), "prose": top(cr, wr, {"ADJF", "ADJS"})}

# --- отличительные слова периодов: log-odds с информативным априорным Дирихле (Monroe et al., 2008)
per_counts = [Counter() for _ in PERIODS]
for o in poems:
    if o["per"] is not None:
        per_counts[o["per"]].update(content_lemmas(o))
tot = sum(per_counts, Counter())
a0 = sum(tot.values())
dist = []
for i, pc in enumerate(per_counts):
    rest = tot - pc
    n_i, n_j = sum(pc.values()), sum(rest.values())
    scores = []
    for w, c in pc.items():
        if c < 5:
            continue
        aw = tot[w] * 0.01 * a0 / a0 * 1.0 + 0.01  # prior ∝ общей частоте
        aw = 0.01 * a0 * tot[w] / a0
        a_all = 0.01 * a0
        yi, yj = c, rest[w]
        d = math.log((yi + aw) / (n_i + a_all - yi - aw)) - math.log((yj + aw) / (n_j + a_all - yj - aw))
        var = 1 / (yi + aw) + 1 / (yj + aw)
        scores.append((d / math.sqrt(var), w, c))
    scores.sort(reverse=True)
    dist.append({"p": PERIODS[i][2], "words": [{"w": w, "z": round(z, 2), "n": c} for z, w, c in scores[:20]],
                 "tokens": n_i})
S["distinctive"] = dist

# --- лексическое богатство: MATTR (окно 500 лемм) по периодам
def mattr(lems, w=500):
    if len(lems) < w:
        return None
    cnt = Counter(lems[:w]); vals = [len(cnt)]
    for i in range(w, len(lems)):
        cnt[lems[i]] += 1
        old = lems[i - w]; cnt[old] -= 1
        if cnt[old] == 0:
            del cnt[old]
        vals.append(len(cnt))
    return round(float(np.mean(vals)) / w, 4)


per_lem = defaultdict(list)
for o in poems:
    if o["per"] is not None:
        per_lem[o["per"]].extend(l.lower() for l in o["clem"])
S["mattr"] = [{"p": PERIODS[p][2], "mattr": mattr(v), "tokens": len(v)} for p, v in sorted(per_lem.items())]
S["mattr_prose"] = mattr([l for o in prose for l in o["clem"]])
S["mattr_poetry"] = mattr([l for o in poems for l in o["clem"]])
all_poem_lem = Counter(l for o in poems for l in o["clem"])
S["hapax_poetry"] = {"hapax": sum(1 for c in all_poem_lem.values() if c == 1), "types": len(all_poem_lem)}
ranks = [c for _, c in all_poem_lem.most_common()]
S["zipf"] = [{"r": r, "f": ranks[r - 1]} for r in sorted({int(round(10 ** x)) for x in np.arange(0, math.log10(len(ranks)), 0.05)})]
S["zipf_top"] = [{"w": w, "n": c} for w, c in all_poem_lem.most_common(12)]

# --- семантические поля: 20 полей × 20 лемм (мои словари), на 1000 слов по периодам и в прозе
FIELDS = {
    "Время": "время час год век минута секунда вечность прошлое будущее вчера завтра календарь хронология мгновение эпоха срок пора сутки неделя столетие",
    "Смерть": "смерть умереть умирать мёртвый гроб могила похороны покойник прах небытие кладбище труп погибнуть гибель убить надгробие венок саван вдова тлен",
    "Вода, море": "вода море волна река океан залив берег лагуна канал дождь прилив пена парус корабль лодка остров плыть влага пучина отлив",
    "Пространство": "пространство горизонт даль точка линия пустота воздух простор перспектива бесконечность плоскость угол граница расстояние глубина высота ширина равнина пейзаж измерение",
    "Бог, вера": "бог господь ангел христос рождество крест храм церковь молитва душа младенец волхв рай ад грех вера святой библия мария небеса",
    "Империя, власть": "империя тиран царь цезарь император власть государство провинция солдат генерал армия война трон указ приказ страж легион полководец держава диктатор",
    "Город": "город улица площадь дом мост фонарь квартира двор окно подъезд переулок проспект трамвай крыша стена фасад колоннада набережная башня парк",
    "Любовь": "любовь любить возлюбленная поцелуй милый нежность ласка страсть разлука измена ревность свидание объятие желание невеста жена влюблённый любимый целовать обнимать",
    "Зима, холод": "зима снег мороз холод лёд январь декабрь февраль вьюга метель стужа иней сугроб холодный замёрзнуть снежинка озноб зимний ледяной оттепель",
    "Вещи": "вещь стул стол предмет стекло лампа зеркало шкаф кресло пепельница чашка стакан бутылка часы кровать диван комод буфет ваза подсвечник",
    "Слово, письмо": "слово язык речь буква строка стих перо бумага грамматика рифма чернила алфавит глагол фраза письмо текст страница рукопись словарь запятая",
    "Свет, тьма": "свет тьма тень луч солнце луна свеча сумерки мрак сияние блеск рассвет закат заря полумрак темнота мерцание огонь светить темнеть",
    "Тело": "тело рука глаз лицо голова губа нога плечо кожа кровь сердце лоб волос палец зрачок ухо рот грудь спина колено",
    "Звук, музыка": "звук музыка голос песня тишина эхо шум крик шёпот звон мелодия нота скрипка оркестр хор труба колокол гул петь слышать",
    "Животные, птицы": "птица ворон ястреб голубь ласточка чайка кошка собака конь лошадь сова мышь волк лиса пёс бабочка муха насекомое корова зверь",
    "Растения, природа": "дерево лес лист трава куст цветок роза сад ветка корень поле холм гора облако ветер туча сосна берёза ель листва",
    "Родина, изгнание": "родина отечество изгнание эмиграция чужбина ссылка беглец эмигрант возвращение отъезд вернуться уехать отчизна паспорт виза таможня чужой изгнанник странник эмигрировать",
    "Память": "память помнить вспоминать забыть забвение воспоминание след былое минувшее забывать напоминать вспомнить запомнить помниться памятник припоминать незабвенный забытый памятный реликвия",
    "Античность": "рим греция эллада афины троя гомер овидий вергилий гораций одиссей телемак эней муза аполлон зевс амфора сатир кентавр нимфа римлянин",
    "Свобода, неволя": "свобода судьба рок удел неволя тюрьма клетка решётка заключённый доля участь выбор воля жребий фатум приговор суд арест цепь свободный",
}
_e = lambda w: w.replace("ё", "е")
FIELDS = {k: [_e(w) for w in v.split()] for k, v in FIELDS.items()}
_seen = Counter(w for ws in FIELDS.values() for w in ws)
assert len(FIELDS) == 20 and all(len(ws) == 20 and len(set(ws)) == 20 for ws in FIELDS.values()), \
    {k: len(set(v)) for k, v in FIELDS.items()}
assert not [w for w, c in _seen.items() if c > 1], [w for w, c in _seen.items() if c > 1]
FIELDS = {k: set(v) for k, v in FIELDS.items()}


def field_rates(lemmas):
    c = Counter(_e(l.lower()) for l in lemmas); n = sum(c.values()) or 1
    return {f: round(1000 * sum(c[w] for w in ws) / n, 2) for f, ws in FIELDS.items()}


heat = [{"p": PERIODS[p][2], **field_rates(per_lem.get(p, []))} for p in range(len(PERIODS))]
heat.append({"p": "Проза", **field_rates([l for o in prose for l in o["clem"]])})
S["fields"] = {"rows": heat, "fields": list(FIELDS), "lexicon": {k: sorted(v) for k, v in FIELDS.items()}}

# --- местоимения и части речи по периодам
PRON = ["я", "ты", "мы", "вы", "он", "она", "они"]
pr_rows = []
pos_rows = []
for p in range(len(PERIODS)):
    toks = [o for o in poems if o["per"] == p]
    lem = [l.lower() for o in toks for l in o["clem"]]
    words = [w.lower() for o in toks for w in o["ctoks"]]
    n = len(lem) or 1
    c = Counter(lem)
    pr_rows.append({"p": PERIODS[p][2], **{x: round(1000 * c[x] / n, 2) for x in PRON}})
    pc = Counter(str(tag(w).POS) for w in words)
    noun, verb = pc["NOUN"], pc["VERB"] + pc["INFN"]
    adj = pc["ADJF"] + pc["ADJS"]
    part = pc["PRTF"] + pc["PRTS"] + pc["GRND"]
    pos_rows.append({"p": PERIODS[p][2], "noun": round(100 * noun / n, 2), "verb": round(100 * verb / n, 2),
                     "adj": round(100 * adj / n, 2), "part": round(100 * part / n, 2),
                     "noun_verb": round(noun / max(1, verb), 2)})
wprose = [w.lower() for o in prose for w in o["ctoks"]]
pcp = Counter(str(tag(w).POS) for w in wprose); n = len(wprose)
S["pos_prose"] = {"noun": round(100 * pcp["NOUN"] / n, 2), "verb": round(100 * (pcp["VERB"] + pcp["INFN"]) / n, 2),
                  "adj": round(100 * (pcp["ADJF"] + pcp["ADJS"]) / n, 2),
                  "noun_verb": round(pcp["NOUN"] / (pcp["VERB"] + pcp["INFN"]), 2)}
S["pronouns"] = pr_rows
S["pos"] = pos_rows

# --- пунктуация на 1000 слов
def norm_punct(t):
    t = t.replace("--", "—").replace(" - ", " — ").replace("…", "...")
    return t


PUNCT = {"запятая": r",", "тире": r"—", "точка": r"(?<!\.)\.(?!\.)", "двоеточие": r":", "точка с запятой": r";",
         "скобки": r"\(", "вопрос": r"\?", "восклицание": r"!", "многоточие": r"\.\.\.", "кавычки": r"[«\"]"}


def punct_rate(texts, words):
    t = norm_punct("\n".join(texts))
    return {k: round(1000 * len(re.findall(rx, t)) / words, 1) for k, rx in PUNCT.items()}


S["punct"] = {"poetry": punct_rate([o["clean"] for o in poems], wp),
              "prose": punct_rate([o["clean"] for o in prose], wr)}
pp = []
enj = []
for p in range(len(PERIODS)):
    ts = [o for o in poems if o["per"] == p]
    w = sum(len(o["ctoks"]) for o in ts)
    pp.append({"p": PERIODS[p][2], **punct_rate([o["clean"] for o in ts], w)})
    ends = [l.rstrip()[-1] for o in ts for l in o["clean"].split("\n") if l.strip() and TOK.search(l)]
    enj.append({"p": PERIODS[p][2], "open": round(100 * sum(ch.isalpha() for ch in ends) / len(ends), 1),
                "n": len(ends)})
S["punct_by_period"] = pp
S["open_line_ends"] = enj

# --- рифма (эвристика): совпадение последних 3 букв конечного слова с одной из соседних ±4 строк
def rhyme_share(o):
    lines = [l for l in o["clean"].split("\n") if l.strip() and TOK.search(l)]
    ends = []
    for l in lines:
        ws = TOK.findall(l)
        e = ws[-1].lower().replace("ё", "е")
        ends.append(e[-3:] if len(e) >= 3 else e)
    hit = 0
    for i, e in enumerate(ends):
        if any(ends[j] == e for j in range(max(0, i - 4), min(len(ends), i + 5)) if j != i):
            hit += 1
    return hit, len(ends)


rh = []
for p in range(len(PERIODS)):
    h = n = 0
    for o in poems:
        if o["per"] == p:
            a, b = rhyme_share(o); h += a; n += b
    rh.append({"p": PERIODS[p][2], "share": round(100 * h / n, 1), "n": n})
h = n = 0
for o in prose:
    a, b = rhyme_share(o); h += a; n += b
S["rhyme"] = {"by_period": rh, "prose_baseline": round(100 * h / n, 1)}

# --- топонимы и имена
geo, sur = Counter(), Counter()
for o in own:
    for i, w in enumerate(o["ctoks"]):
        if not w[0].isupper():
            continue
        t = tag(w.lower())
        nf = morph.parse(w.lower())[0].normal_form
        if "Geox" in t:
            geo[nf] += 1
        elif "Surn" in t:
            sur[nf] += 1
def nomn(w):
    p = morph.parse(w)[0]
    f = p.inflect({"nomn", "sing"}) or p.inflect({"nomn"})
    return (f.word if f else w).capitalize()


GEO_AMBIG = {"рейн"}  # и река, и Евгений Рейн
S["geo"] = [{"w": nomn(w), "n": c} for w, c in geo.most_common(30) if w not in GEO_AMBIG][:20]
sur_forms = defaultdict(Counter)
for o in own:
    for w in o["ctoks"]:
        if w[0].isupper() and "Surn" in tag(w.lower()):
            sur_forms[morph.parse(w.lower())[0].normal_form][morph.parse(w.lower())[0].tag.gender] += 1
S["surnames"] = []
for w, c in sur.most_common(20):
    g = sur_forms[w].most_common(1)[0][0]
    p0 = next((p for p in morph.parse(w) if "Surn" in p.tag), morph.parse(w)[0])
    f = p0.inflect({"nomn", "sing", g}) if g else None
    S["surnames"].append({"w": (f.word if f else w).capitalize(), "n": c})

# --- цвета
COLORS = {"белый": "#f4f4f0", "чёрный": "#111111", "серый": "#8a8a86", "синий": "#1f47b8", "голубой": "#7fb1e6",
          "красный": "#c62f2f", "жёлтый": "#e6c229", "зелёный": "#2f8a3a", "коричневый": "#7a4a26",
          "золотой": "#c9a227", "серебряный": "#b9bcc2", "розовый": "#e89ab2", "лиловый": "#8a5aa8",
          "бурый": "#6b4a2e", "рыжий": "#c8641e", "пурпурный": "#7d1e6a", "багровый": "#8e1b1b",
          "алый": "#e0263a", "бледный": "#e6e2d6", "тёмный": "#2a2a2a"}
cl = Counter()
for o in poems:
    for l in o["clem"]:
        k = l.lower().replace("е", "ё") if l.lower().replace("е", "ё") in COLORS else l.lower()
        if k in COLORS:
            cl[k] += 1
S["colors"] = [{"w": w, "n": cl[w], "hex": COLORS[w]} for w in sorted(COLORS, key=lambda x: -cl[x]) if cl[w]]

# --- проза: длина предложения
sent_len = []
longest = (0, "", "")
for o in prose:
    t = re.sub(r"\s+", " ", norm_punct(o["clean"]))
    for s in re.split(r"(?<=[.!?])\s+(?=[«\"(—A-ZА-ЯЁ0-9])", t):
        n = len(TOK.findall(s))
        if n:
            sent_len.append(n)
            if n > longest[0]:
                longest = (n, s, o["title"])
sl = np.array(sent_len)
bins = [(1, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 30), (31, 40), (41, 50), (51, 75), (76, 100), (101, 10 ** 6)]
S["sentences"] = {"n": len(sl), "median": float(np.median(sl)), "mean": round(float(sl.mean()), 1),
                  "p90": float(np.percentile(sl, 90)),
                  "hist": [{"b": f"{a}–{b}" if b < 10 ** 6 else f"{a}+", "n": int(((sl >= a) & (sl <= b)).sum())}
                           for a, b in bins],
                  "longest": {"words": longest[0], "title": longest[2], "start": longest[1][:320]}}

# --- длина слова
def wl(objs):
    L = [len(w.replace("-", "")) for o in objs for w in o["ctoks"]]
    c = Counter(min(x, 15) for x in L)
    return {"mean": round(float(np.mean(L)), 2), "hist": [round(100 * c.get(i, 0) / len(L), 2) for i in range(1, 16)]}


S["word_len"] = {"poetry": wl(poems), "prose": wl(prose)}

# --- английские стихи
en_lines = [l for o in en_poems for l in o["clean"].split("\n") if l.strip() and TOK.search(l)]
ru_lines = [l for _, _, _, l in line_rows]
EN_STOP = set("the a an and of to in on at is it that this for with as by from or be was are his her its i you he she we they my your me not but no so if all what there their them than then when which who into out up down one".split())
enw = Counter(w.lower() for o in en_poems for w in o["ctoks"] if w.lower() not in EN_STOP and len(w) > 2)
S["english"] = {"poems": len(en_poems), "words": S["overview"]["en_words"],
                "words_per_line": round(float(np.mean([len(TOK.findall(l)) for l in en_lines])), 2),
                "ru_words_per_line": round(float(np.mean([len(TOK.findall(l)) for l in ru_lines])), 2),
                "top": [{"w": w, "n": c} for w, c in enw.most_common(15)],
                "titles": [o["title"] for o in en_poems]}

# --- рекорды
pp_sorted = sorted(per_poem, key=lambda r: r["lines"])
longest_line = max(line_rows, key=lambda r: r[2])
all_tokens = [(w, o["title"]) for o in own for w in o["ctoks"]]
longw = max(all_tokens, key=lambda x: len(x[0].replace("-", "")))
longw_single = max(((w, t) for w, t in all_tokens if "-" not in w), key=lambda x: len(x[0]))
S["records"] = {
    "longest_poem": {"t": pp_sorted[-1]["t"], "lines": pp_sorted[-1]["lines"], "words": pp_sorted[-1]["words"]},
    "shortest_poem": {"t": pp_sorted[0]["t"], "lines": pp_sorted[0]["lines"]},
    "longest_line": {"syl": longest_line[2], "text": longest_line[3].strip()[:260], "year": longest_line[0]},
    "longest_word": {"w": longw[0], "len": len(longw[0].replace("-", "")), "t": longw[1]},
    "longest_single_word": {"w": longw_single[0], "len": len(longw_single[0]), "t": longw_single[1]},
    "dropped_editorial_lines": len(DROPPED_LONG),
    "median_lines": float(np.median([r["lines"] for r in per_poem])),
}
# --- производные числа
h = S["line_syllable_hist"]; tot = sum(x["n"] for x in h); acc = 0
for x in h:
    acc += x["n"]
    if acc >= 0.99 * tot:
        S["records"]["p99_syllables"] = x["s"]; break
S["records"].pop("longest_line", None)
S["years"]["share_dated"] = round(100 * S["years"]["dated"] / S["years"]["total"], 1)

# --- Венеция: 8 стихотворений и «Набережная неисцелимых» из сборника analysis/venice.jsonl
VEN = [json.loads(l) for l in open(HERE / "venice.jsonl", encoding="utf-8")]
PANICIERI_YEARS = {"Лагуна": 1973, "Сан-Пьетро": 1977, "Венецианские строфы (1)": 1982, "Венецианские строфы (2)": 1982,
                   "В Италии": 1985, "Посвящается Джироламо Марчелло": 1988, "Лидо": 1989, "С натуры": 1995}
vpo = []
for r in VEN:
    if r["section_title"] != "Стихотворения":
        continue
    t = clean_lines(r["text"], poetry=True)
    lines = [l for l in t.split("\n") if l.strip() and TOK.search(l)]
    toks = TOK.findall(t)
    vpo.append({"t": r["title"], "y": PANICIERI_YEARS.get(r["title"]), "lines": len(lines),
                "med_syl": float(np.median([syll(l) for l in lines])), "words": len(toks),
                "lem": [morph.parse(w.lower())[0].normal_form for w in toks], "toks": toks})
vpo.sort(key=lambda r: r["y"] or 0)
ven_titles = {r["t"] for r in vpo} | {"Посмертные публикации"}
rest_poems = [o for o in poems if o["title"] not in ven_titles]
# сравнение длины строки с остальными стихами тех же лет (1973–1995)
same = [s_ for y, p_, s_, l in line_rows if y and 1973 <= y <= 1995]
ven_lines = [syll(l) for r in vpo for l in clean_lines([x for x in VEN if x["title"] == r["t"]][0]["text"], True).split("\n")
             if l.strip() and TOK.search(l)]


def ven_content(lems, toks):
    for w, l in zip(toks, lems):
        t = tag(w.lower())
        if (t.POS in CONTENT and l not in STOPLEM and len(l) > 1 and l not in PROPER
                and not ({"Apro", "Name", "Surn", "Patr", "Orgn", "Abbr"} & t.grammemes)):
            yield l


vc = Counter(l for r in vpo for l in ven_content(r["lem"], r["toks"]))
rc = Counter(l for o in rest_poems for l in content_lemmas(o))
nv, nr = sum(vc.values()), sum(rc.values()); tot_c = vc + rc; a_all = 0.01 * (nv + nr)
vs = []
for w, c in vc.items():
    if c < 3:
        continue
    aw = a_all * tot_c[w] / (nv + nr)
    d = math.log((c + aw) / (nv + a_all - c - aw)) - math.log((rc[w] + aw) / (nr + a_all - rc[w] - aw))
    vs.append((d / math.sqrt(1 / (c + aw) + 1 / (rc[w] + aw)), w, c))
vs.sort(reverse=True)
nab = next(o for o in own if o["title"].startswith("НАБЕРЕЖНАЯ НЕИСЦЕЛИМЫХ"))
VEN_WORDS = ["вода", "город", "лагуна", "канал", "гондола", "мост", "туман", "зима", "отражение", "стекло",
             "мрамор", "фасад", "колокол", "церковь", "свет", "зеркало", "волна", "набережная", "палаццо", "площадь"]
nc = Counter(_e(l.lower()) for l in nab["clem"])
S["venice"] = {
    "poems": [{k: r[k] for k in ("t", "y", "lines", "med_syl", "words")} for r in vpo],
    "poem_words": sum(r["words"] for r in vpo),
    "line_med_venice": float(np.median(ven_lines)), "line_med_same_years": float(np.median(same)),
    "line_mean_venice": round(float(np.mean(ven_lines)), 2), "line_mean_same_years": round(float(np.mean(same)), 2),
    "distinctive": [{"w": w, "z": round(z, 2), "n": c} for z, w, c in vs[:20]],
    "fields_venice": field_rates([l for r in vpo for l in r["lem"]]),
    "fields_poetry": field_rates([l for o in rest_poems for l in o["clem"]]),
    "nab": {"words": len(nab["ctoks"]),
            "lex": sorted([{"w": w, "n": nc[_e(w)], "per10k": round(1e4 * nc[_e(w)] / len(nab["clem"]), 1)} for w in VEN_WORDS],
                          key=lambda x: -x["n"])},
    "selection": {"candidates": 28, "included": 17, "reference": "S. Panicieri, eSamizdat: 8 стихотворений 1973–1995"},
}

json.dump(S, open(HERE / "stats.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: S[k] for k in ("overview", "records")}, ensure_ascii=False, indent=1))
print("dated", S["years"]["dated"], "/", S["years"]["total"])
print("syl by period", S["line_syllables_by_period"])
print("mattr", S["mattr"], S["mattr_prose"], S["mattr_poetry"])
print("rhyme", S["rhyme"]); print("open ends", S["open_line_ends"])
print("pos", S["pos"], S["pos_prose"])
print("distinctive", [(d["p"], [w["w"] for w in d["words"][:6]]) for d in S["distinctive"]])
print("geo", S["geo"][:12]); print("sur", S["surnames"][:12]); print("colors", [(c["w"], c["n"]) for c in S["colors"]])
print("sent", {k: v for k, v in S["sentences"].items() if k != "hist"})
print("xmas", {k: v for k, v in S["christmas"]["by_year"].items() if v}, S["christmas"]["titles"][:5])
print("top nouns poetry", [x["w"] for x in S["top_nouns"]["poetry"]])
print("top nouns prose", [x["w"] for x in S["top_nouns"]["prose"]])
