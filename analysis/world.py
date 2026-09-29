"""Персонажи, места, транспорт, еда и напитки. Пишет analysis/world.json.

Ручной разметки нет. Названные лица и места находятся автоматически:
  * слово с заглавной буквы не в начале фразы (в стихах с заглавной в начале каждой строки начало строки не считается);
  * доля заглавных написаний леммы среди всех её употреблений внутри фразы не меньше 0,7;
  * тип определяет морфология pymorphy3 (Name/Surn/Patr — лицо, Geox — место), а слова без метки — соседство:
    рядом с именем или инициалами — лицо, после предлога «в/на/из/до…» — место.
Бытовые категории (места вообще, транспорт, еда, напитки) считаются по словарям лемм, но в результат попадают
только слова, которые в текстах есть. Слова с заведомо частым другим значением в словари не входят.
"""
import json
import pickle
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pymorphy3

HERE = Path(__file__).parent
morph = pymorphy3.MorphAnalyzer()

PERIODS = [(1957, 1960, "1957–1960"), (1961, 1966, "1961–1966"), (1967, 1972, "1967–1972"),
           (1973, 1984, "1973–1984"), (1985, 1989, "1985–1989"), (1990, 1996, "1990–1996")]
SITE_PERIOD = {"Стихотворения 1930—1960": 0, "Стихотворения 1961—1966": 1, "Стихотворения 1967—1972": 2,
               "Стихотворения 1973—1984": 3, "Стихотворения 1985—1989": 4, "Стихотворения 1990—1996": 5}
NP = len(PERIODS)   # индекс 6 — стихи без периода; у прозы период не определяется
TOK = re.compile(r"[А-Яа-яЁёA-Za-z]+(?:-[А-Яа-яЁё]+)*")
EDITORIAL = re.compile(r"С\.\s?В\.|Текст (приводится|по )|Источник|отсутствует в СИБ|^\s*\*|^\s*\d{1,2}\s+[\x22«(А-ЯA-Z]|"
                       r"^\s*Примечани|^\s*<\.\.\.>\s*$")
MONTHS = r"январ|феврал|март|апрел|ма[йя]|июн|июл|август|сентябр|октябр|ноябр|декабр"
DATE_LINE = re.compile(rf"^\s*[<(\[]?\s*(({MONTHS})[а-я]*\s*)?(19\d\d|\d{{2}})[\s,\-–—?>\])]*(\d{{4}})?.{{0,40}}$", re.I)
PLACE_PREP = {"в", "во", "на", "из", "изо", "от", "до", "под", "над", "около", "возле", "через", "близ", "у", "с", "к", "по",
              "за", "между", "среди", "вокруг", "мимо", "вдоль", "против", "сквозь", "про"}
SACRED = {"бог", "господь", "христос", "иисус", "богородица", "сатана", "дьявол", "муза", "магдалина"}
NOT_ENTITY = {"я", "ты", "он", "она", "оно", "мы", "вы", "они"}


def period_of(o):
    if o["year"]:
        for i, (a, b, _) in enumerate(PERIODS):
            if a <= o["year"] <= b:
                return i
    return SITE_PERIOD.get(o.get("period"))


def clean_lines(text, poetry):
    out = []
    for ln in text.split("\n"):
        if EDITORIAL.search(ln):
            continue
        if poetry and len(TOK.findall(ln)) > 28:
            continue
        s = ln.strip()
        if s and DATE_LINE.match(s) and len(s) < 60 and re.search(r"19\d\d|\d{2}\s*$", s) and len(TOK.findall(s)) <= 6:
            continue
        out.append(ln)
    return out


@lru_cache(maxsize=None)
def parses(w):
    return morph.parse(w)[:4]


def grams(w):
    g = set()
    for p in parses(w):
        g |= {x for x in ("Name", "Surn", "Patr", "Geox", "Orgn") if x in p.tag.grammemes}
    return g


@lru_cache(maxsize=None)
def lemma(w):
    return parses(w)[0].normal_form


def nominative(w):
    """Именительный падеж слова с заглавной: «Цветаевой» → «Цветаева»."""
    ps = parses(w)
    p = next((q for q in ps if {"Surn", "Name", "Geox", "Patr"} & q.tag.grammemes), ps[0])
    f = p.inflect({"nomn"}) if p.tag.POS == "NOUN" else None
    return (f.word if f else p.normal_form).capitalize()


C = pickle.load(open(HERE / "corpus.pkl", "rb"))
own = [o for o in C if o["author"] == "own" and o["lang"] == "ru"]
texts = []
for o in own:
    poetry = o["genre"] == "poetry"
    if not poetry and o["title"].startswith('Набережная неисцелимых - "Fondamenta'):
        continue
    lines = clean_lines(o["text"], poetry)
    texts.append({"idx": o["idx"], "title": o["title"], "year": o["year"], "poetry": poetry,
                  "per": (period_of(o) if poetry else None), "lines": lines, "url": o.get("url")})
print("текстов", len(texts), "стихов", sum(t["poetry"] for t in texts))

# ------------------------------------------------------------------ разбор текстов на слова
# occ: (текст, блок, строка, слово, позиция в строке, начало фразы?, слово-соседи слева/справа)
occ = []
lower_cnt = Counter()        # лемма -> вхождения со строчной буквы внутри фразы
words_by_text = []           # для словарей: [(лемма, POS, блок, строка, позиция)]
for ti, t in enumerate(texts):
    nonempty = [l.strip() for l in t["lines"] if l.strip()]
    capl = sum(l[0].isupper() for l in nonempty) / max(1, len(nonempty))
    caps_lines = t["poetry"] and capl >= 0.8
    block, since_blank, prev_end = 0, 0, True
    wl = []
    for li, ln in enumerate(t["lines"]):
        s = ln.strip()
        if not s:
            if since_blank:
                block += 1
            since_blank, prev_end = 0, True
            continue
        bk = block * 100 + (since_blank // 12 if t["poetry"] else 0)      # стихи без пустых строк режем по 12 строк
        since_blank += 1
        first = True
        toks = [m for m in TOK.finditer(s) if re.search("[А-Яа-яЁё]", m.group(0))]
        for k, m in enumerate(toks):
            w = m.group(0)
            pre = s[:m.start()].rstrip()
            sent_start = (first and (caps_lines or prev_end)) or bool(pre and pre[-1] in ".!?…")
            first = False
            lw = w.lower()
            wl.append((lemma(lw), str(parses(lw)[0].tag.POS), bk, li, k))
            if w[0].isupper() and len(w) > 1 and not w.isupper():
                occ.append((ti, bk, li, w, k, sent_start, toks[k - 1].group(0) if k else "", m.start()))
            elif w.islower() and not sent_start:
                lower_cnt[lemma(lw)] += 1
        prev_end = s[-1] in ".!?…»\""
    words_by_text.append(wl)
print("заглавных вхождений", len(occ), "| текстов", len(texts))

# ------------------------------------------------------------------ какие леммы — имена собственные
cap_mid = Counter(lemma(w.lower()) for (_, _, _, w, _, ss, _, _) in occ if not ss)
proper = {}
for l, c in cap_mid.items():
    share = c / (c + lower_cnt[l])
    if l in NOT_ENTITY:
        continue
    if (c >= 2 and share >= 0.7) or (l in SACRED and c >= 2):
        proper[l] = round(share, 2)
print("лемм с заглавной внутри фразы", len(cap_mid), "-> имена собственные", len(proper))


def is_initial(w):
    return len(w) == 1 and w.isupper()


# ------------------------------------------------------------------ сущности: типы и вхождения
by_lemma = defaultdict(list)          # лемма -> вхождения
line_index = defaultdict(list)        # (текст, строка) -> вхождения слева направо
line_caps = defaultdict(dict)         # (текст, строка) -> {позиция: слово с заглавной}
for o in occ:
    line_caps[(o[0], o[2])][o[4]] = o[3]
for o in occ:
    ti, bk, li, w, k, ss, prev, pos = o
    l = lemma(w.lower())
    if l not in proper:
        continue
    if ss and not grams(w.lower()) and l not in SACRED:
        continue                        # начало фразы и нет морфологической метки — скорее обычное слово
    by_lemma[l].append(o)
    line_index[(ti, li)].append((k, l, w))
for v in line_index.values():
    v.sort()


# один человек под разными именами: имя без фамилии, написание, второе имя
ALIAS = {"харди": "гарди", "уистан": "оден", "стивен": "спендер", "райнер": "рильке", "флакк": "гораций", "назона": "овидий",
         "иисус": "христос", "виргилий": "вергилий", "исак": "исаак"}
for a_, b_ in ALIAS.items():
    if a_ in by_lemma and b_ in by_lemma:
        by_lemma[b_] += by_lemma.pop(a_)
STRICT_PREP = {"в", "во", "на", "из", "изо", "до", "около", "возле", "близ", "через"}
EXCLUDE = {"рождество", "пасха", "бродский", "иосиф", "новогодний", "новогоднее",
           "георгик", "энеида", "буколика", "одиссея", "илиада"}     # праздники, автор, названия книг
KIND_FIX = {"гомера": "person", "гомер": "person", lemma("альпы"): "place"}                # pymorphy считает Гомера топонимом     # праздники; сам автор не показывается
CATS = {}


def cat_occ(o):
    """Что означает это вхождение: person (рядом с именем) / geo (первый разбор — место) / prep (после предлога места) / None."""
    ti, bk, li, w, k, ss, prev, pos = o
    lw = w.lower()
    row = line_index[(ti, li)]
    pv = next((x for x in row if x[0] == k - 1), None)
    nxw = line_caps[(ti, li)].get(k + 1)
    if is_initial(prev) or (pv and (grams(pv[2].lower()) & {"Name", "Patr"})):
        return "person"
    if nxw and "Geox" not in grams(nxw.lower()) and lemma(nxw.lower()) in proper and grams(lw) & {"Name", "Surn", "Patr", "Geox"}:
        return "person"                     # «Уистан Оден», «Милан Кундера»
    if prev.lower() in STRICT_PREP:
        return "prep"
    return None


def kind_of(l):
    occs = by_lemma[l]
    if l in EXCLUDE:
        return None
    if l in SACRED:
        return "sacred"
    if l in KIND_FIX:
        return KIND_FIX[l]
    votes = Counter(cat_occ(o) for o in occs)
    n = len(occs)
    g = set()
    for o in occs:
        g |= grams(o[3].lower())
    person_g = g & {"Name", "Surn", "Patr"}
    if "Geox" in g and not person_g:
        return "person" if votes["person"] >= 2 and votes["person"] >= 0.05 * n and votes["person"] > votes["prep"] else "place"
    if "Geox" in g:                          # и место, и имя: решают соседи и предлоги
        if votes["person"] >= 0.3 * n:
            return "person"
        return "place" if votes["prep"] >= 0.25 * n else "person"
    if person_g:
        return "person"
    if votes["person"] >= 2 and votes["person"] / n >= 0.15:
        return "person"
    if votes["prep"] >= 0.5 * n and n >= 3 and proper[l] >= 0.9:
        return "place"
    return None


DISPLAY_FIX = {"публия": "Публий", "венцлов": "Венцлова", "проперция": "Проперций", "назона": "Назон", "боря": "Борей",
               "гарди": "Гарди"}       # pymorphy путает падежи и род у имён


def is_nom(w):
    p = parses(w.lower())[0]
    return "nomn" in p.tag.grammemes and "sing" in p.tag.grammemes


def display(l):
    """Написание для показа: лемма, если она есть среди форм; иначе среди частых форм — именительный, иначе самая короткая."""
    if l in DISPLAY_FIX:
        return DISPLAY_FIX[l]
    forms = Counter(o[3] for o in by_lemma[l])
    for w in forms:
        if w.lower() == l:
            return w
    top = max(forms.values())
    cand = [w for w, c in forms.items() if c >= 0.25 * top]
    nom = [w for w in cand if is_nom(w)]
    return max(nom, key=lambda w: forms[w]) if nom else min(cand, key=lambda w: (len(w), -forms[w]))


KIND = {l: kind_of(l) for l in by_lemma}


def drop_part(o):
    """Имя перед фамилией («Томас Гарди») и отчество после имени («Базиль Модестович») считаются упоминанием одного лица."""
    ti, bk, li, w, k, ss, prev, pos = o
    g = grams(w.lower())
    nxw = line_caps[(ti, li)].get(k + 1)
    if "Name" in g and "Surn" not in g and nxw and KIND.get(lemma(nxw.lower())) == "person" and "Patr" not in grams(nxw.lower()):
        return True
    pv = line_caps[(ti, li)].get(k - 1)
    return bool("Patr" in g and pv and "Name" in grams(pv.lower()) and KIND.get(lemma(pv.lower())) == "person")


for l in list(by_lemma):
    if KIND[l] == "person":
        keep = [o for o in by_lemma[l] if not drop_part(o)]
        by_lemma[l] = keep
        if len(keep) < 2:
            KIND[l] = None
print(Counter(KIND.values()))


# ------------------------------------------------------------------ записи сущностей
def snippet(t, li, pos, poetry):
    line = t["lines"][li].strip()
    if poetry or len(line) <= 110:
        return line
    a, b = max(0, pos - 70), min(len(line), pos + 80)
    a = line.rfind(" ", 0, a) + 1 if a else 0
    b = line.find(" ", b) if b < len(line) else len(line)
    b = len(line) if b < 0 else b
    return ("… " if a else "") + line[a:b].strip() + (" …" if b < len(line) else "")


def pick_contexts(occs, n=3):
    rows = []
    seen = set()
    for (ti, bk, li, w, k, ss, prev, pos) in occs:
        t = texts[ti]
        if ti in seen:
            continue
        seen.add(ti)
        sn = snippet(t, li, pos, t["poetry"])
        rows.append((0 if t["poetry"] else 1, 0 if len(sn) <= 90 else 1, t["year"] or 9999, t["title"], sn, t["year"], t["poetry"]))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    best = rows[:12]
    if len(best) > n:                        # равномерно по времени
        best.sort(key=lambda r: r[2])
        best = [best[int(i * (len(best) - 1) / (n - 1))] for i in range(n)]
    return [{"t": r[3], "y": r[5], "s": r[4], "p": 1 if r[6] else 0} for r in best]


def make_entity(l):
    occs = by_lemma[l]
    per_p = [0] * (NP + 1); poet = prose = 0
    poems_set, prose_set, years = set(), set(), []
    blocks = set()
    for (ti, bk, li, w, k, ss, prev, pos) in occs:
        t = texts[ti]
        blocks.add((ti, bk))
        if t["poetry"]:
            poet += 1; poems_set.add(ti); per_p[t["per"] if t["per"] is not None else NP] += 1
            if t["year"]:
                years.append(t["year"])
        else:
            prose += 1; prose_set.add(ti)
    return {"l": l, "name": display(l), "n": len(occs), "np": poet, "nr": prose, "per": per_p,
            "poems": len(poems_set), "essays": len(prose_set), "y0": min(years) if years else None, "y1": max(years) if years else None,
            "ctx": pick_contexts(occs), "_blocks": blocks, "_texts": poems_set | prose_set}


ENT = {l: make_entity(l) for l in by_lemma if KIND[l] in ("person", "sacred", "place")}
for l, e in ENT.items():
    e["kind"] = KIND[l]
persons = sorted((e for e in ENT.values() if e["kind"] in ("person", "sacred")), key=lambda e: -e["n"])
places = sorted((e for e in ENT.values() if e["kind"] == "place"), key=lambda e: -e["n"])
print("персонажей", len(persons), "| мест", len(places))

# ------------------------------------------------------------------ словари: места вообще, транспорт, еда, напитки
def E(w):
    return w.replace("ё", "е")


LEX = {
    "places": {
        "Вода": "море океан река озеро залив канал болото пруд лагуна ручей пролив берег набережная пристань порт остров пляж гавань омут родник колодец мель водопад фонтан пирс причал маяк шлюз верфь мыс бухта отмель дельта устье лиман фьорд архипелаг риф протока трясина топь парапет",
        "Город": "город улица площадь переулок проспект бульвар сквер мост двор подворотня арка вокзал базар кафе ресторан бар трактир кабак гостиница отель магазин аптека почта тюрьма больница школа университет библиотека музей театр цирк казарма завод фабрика окраина предместье пригород аллея пустырь свалка застава слобода лавка пивная закусочная чайная забегаловка кофейня пансион казино кинотеатр филармония консерватория галерея кабинет",
        "Дом и жильё": "дом комната кухня спальня чердак подвал лестница коридор прихожая балкон крыша квартира подъезд веранда терраса мансарда чулан кладовая вилла дача усадьба хижина лачуга шалаш землянка барак хибара палатка бунгало",
        "Природа": "лес поле роща сад парк луг гора холм пустыня степь тундра долина ущелье овраг обрыв дюна поляна тропа перевал пещера утес чаща дебри заросли джунгли оазис скала каньон лощина опушка просека склон подножие вулкан равнина плато",
        "Святые и памятные места": "церковь собор храм часовня кладбище могила монастырь мечеть синагога алтарь пантеон мавзолей базилика капелла склеп некрополь катакомбы крипта пагода колокольня",
        "Дворцы и крепости": "дворец башня цитадель бастион амфитеатр арена пирамида колоннада портик ротонда",
        "Скамейки и закоулки": "скамья скамейка лавочка закоулок",
        "Деревня и провинция": "деревня село хутор поселок провинция глушь",
    },
    "transport": {
        "По рельсам": "поезд вагон паровоз локомотив электричка трамвай метро дрезина фуникулер",
        "По дороге": "автобус троллейбус такси автомобиль мотоцикл велосипед грузовик лимузин телега повозка карета коляска дрожки сани дилижанс фаэтон колесница бричка ландо кабриолет кибитка тарантас возок арба броневик танк мопед самокат рикша носилки паланкин нарты санки упряжка",
        "По воде": "лодка корабль пароход судно катер яхта баржа шхуна гондола челн плот парусник фрегат каравелла лайнер байдарка ковчег подлодка субмарина батискаф эсминец крейсер линкор броненосец ледокол траулер шлюпка ялик галера бригантина клипер бриг шаланда джонка катамаран",
        "По воздуху": "самолет аэроплан вертолет ракета дирижабль аэростат планер гидроплан истребитель бомбардировщик космолет",
    },
    "food": {
        "Хлеб и выпечка": "хлеб булка батон сухарь пирог пирожок торт пирожное печенье пряник блин оладья баранка бублик каравай лепешка кекс бисквит пончик сухарик гренка крендель кулич ватрушка кулебяка вафля лаваш хачапури чебурек",
        "Мясо и рыба": "мясо колбаса ветчина окорок сосиска котлета бифштекс отбивная курица индейка баранина говядина свинина шашлык сало селедка сардина килька икра устрица креветка краб осетрина сельдь салака ростбиф шницель фарш тефтели гуляш сарделька паштет салями сервелат грудинка телятина конина оленина бекон холодец студень кебаб люля манты долма шаурма",
        "Овощи и грибы": "картошка картофель капуста морковь свекла чеснок огурец помидор редиска репа гриб укроп петрушка редис баклажан кабачок тыква спаржа артишок сельдерей",
        "Фрукты и ягоды": "яблоко груша слива вишня виноград лимон апельсин мандарин банан арбуз дыня персик абрикос ананас изюм орех финик инжир ягода малина клубника земляника крыжовник смородина гранат оливка маслина хурма айва черешня",
        "Блюда": "суп борщ щи каша уха пельмени макароны спагетти паста омлет яичница салат бутерброд пицца пюре рагу заливное винегрет окрошка бульон похлебка харчо солянка рассольник жаркое плов лагман лазанья паэлья сэндвич",
        "Сладкое": "сахар конфета шоколад варенье мед мороженое халва леденец пастила мармелад джем повидло зефир марципан карамель",
        "Молочное, крупы, приправы": "сыр творог сметана яйцо соль перец уксус горчица рис фасоль горох гречка овсянка сливки простокваша корица ваниль имбирь тмин",
        "Трапезы и застолья": "еда пища закуска ужин обед завтрак десерт аперитив пирушка застолье трапеза пир банкет пикник",
    },
    "drinks": {
        "Вино и шампанское": "вино шампанское портвейн херес вермут мартини кагор бордо кьянти мадера токай рислинг мускат цинандали кахетинское марсала кампари",
        "Крепкое": "водка коньяк граппа джин самогон спирт ликер бренди абсент текила кальвадос шнапс чача самогонка спиртное настойка пунш глинтвейн сидр бурбон ракия арак чекушка шкалик амаретто",
        "Пиво и брага": "пиво эль портер бражка брага пойло кумыс",
        "Чай, кофе и безалкогольное": "чай кофе молоко лимонад квас какао кефир компот кипяток кисель морс нектар тоник чифирь коктейль",
        "Посуда для питья": "рюмка стопка чарка стакан бокал бутылка графин фужер чашка фляга кувшин штопор бочка",
    },
}
ANY_POS = {"шампанское", "мороженое", "спиртное"}          # эти слова — прилагательные по форме
LEX_LEMMA = {}          # лемма токена -> (категория, группа, слово)
for cat, groups in LEX.items():
    for g, ws in groups.items():
        for w in ws.split():
            # ключ слова: само слово, если pymorphy знает его как начальную форму; иначе «догадка» лемматизатора (граппа -> грапп)
            own_form = any(p.normal_form == w and str(p.tag.POS) in ("NOUN", "ADJF") for p in morph.parse(w))
            keys = {E(w)} if own_form else {E(lemma(w))}
            for k_ in keys:
                LEX_LEMMA.setdefault(k_, (cat, g, w))


def tok_span(ti, li, k):
    ln = texts[ti]["lines"][li].strip()
    toks = [m for m in TOK.finditer(ln) if re.search("[А-Яа-яЁё]", m.group(0))]
    return (toks[k].start(), toks[k].end()) if k < len(toks) else None


def build_lex():
    """Считает вхождения словарных лемм. Возвращает {cat: {group: {word: rec}}}."""
    rec = defaultdict(lambda: {"n": 0, "np": 0, "nr": 0, "per": [0] * (NP + 1), "texts": set(), "occ": []})
    for ti, wl in enumerate(words_by_text):
        t = texts[ti]
        for (lm, pos, bk, li, k) in wl:
            key = E(lm)
            if key not in LEX_LEMMA:
                continue
            if pos != "NOUN" and key not in ANY_POS:
                continue
            cat, g, w = LEX_LEMMA[key]
            if key == "чай":                                  # «На улице, чай, не Франция» — частица, а не напиток
                sp = tok_span(ti, li, k)
                ln = texts[ti]["lines"][li].strip()
                if sp and ln[:sp[0]].rstrip().endswith(",") and ln[sp[1]:].lstrip().startswith(","):
                    continue
            r = rec[(cat, g, key)]
            r["n"] += 1; r["texts"].add(ti)
            if t["poetry"]:
                r["np"] += 1; r["per"][t["per"] if t["per"] is not None else NP] += 1
            else:
                r["nr"] += 1
            r["occ"].append((ti, li, k))
    return rec


def word_line(ti, li, k):
    """Строка и слово (по номеру слова в строке) — для контекста."""
    return texts[ti]["lines"][li].strip()


LEXREC = build_lex()


def lex_contexts(occ_list, n=3):
    """Строки с упоминанием: стихи вперёд, короткие вперёд, потом равномерно по времени."""
    rows, seen = [], set()
    for ti, li, k in occ_list:
        if ti in seen:
            continue
        seen.add(ti)
        t = texts[ti]
        sp = tok_span(ti, li, k)
        sn = snippet(t, li, sp[0] if sp else 0, t["poetry"])
        rows.append((0 if t["poetry"] else 1, 0 if len(sn) <= 90 else 1, t["year"] or 9999, t["title"], sn, t["year"], t["poetry"]))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    best = rows[:12]
    if len(best) > n:
        best.sort(key=lambda r: r[2])
        best = [best[int(i * (len(best) - 1) / (n - 1))] for i in range(n)]
    return [{"t": r[3], "y": r[5], "s": r[4], "p": 1 if r[6] else 0} for r in best]


def lex_out(cat):
    out = []
    for g in LEX[cat]:
        items = []
        for (c, gg, key), r in LEXREC.items():
            if c == cat and gg == g:
                items.append({"w": LEX_LEMMA[key][2], "n": r["n"], "np": r["np"], "nr": r["nr"], "per": r["per"], "texts": len(r["texts"]),
                              "ctx": lex_contexts(r["occ"])})
        items.sort(key=lambda x: (-x["n"], x["w"]))
        if items:
            out.append({"g": g, "n": sum(i["n"] for i in items), "per": [sum(i["per"][p] for i in items) for p in range(NP + 1)], "items": items})
    out.sort(key=lambda x: -x["n"])
    return out


def ent_out(e, idx=None):
    d = {"name": e["name"], "kind": e["kind"], "n": e["n"], "np": e["np"], "nr": e["nr"], "per": e["per"], "poems": e["poems"],
         "essays": e["essays"], "texts": e["poems"] + e["essays"], "y0": e["y0"], "y1": e["y1"], "ctx": e["ctx"]}
    if idx is not None:
        d["i"] = idx
    return d


# ------------------------------------------------------------------ сеть персонажей
NET_N = 120
pool = sorted(persons, key=lambda e: (-(e["poems"] + e["essays"]), -e["n"]))
pool = [e for e in pool if e["poems"] + e["essays"] >= 3][:NET_N]
idx = {e["l"]: i for i, e in enumerate(pool)}
N = len(pool)
W = np.zeros((N, N)); WT = np.zeros((N, N))
blk = defaultdict(set); txt = defaultdict(set)
for l, i in idx.items():
    for b in ENT[l]["_blocks"]:
        blk[b].add(i)
    for tx in ENT[l]["_texts"]:
        txt[tx].add(i)
for b, mem in blk.items():
    m = sorted(mem)
    for a in range(len(m)):
        for c in range(a + 1, len(m)):
            W[m[a], m[c]] += 1; W[m[c], m[a]] += 1
for tx, mem in txt.items():
    m = sorted(mem)
    for a in range(len(m)):
        for c in range(a + 1, len(m)):
            WT[m[a], m[c]] += 1; WT[m[c], m[a]] += 1
# связь — соседство в одной строфе или абзаце; общий текст без соседства связью не считается
S = W.copy()
np.fill_diagonal(S, 0)
print("рёбер с весом ≥1:", int((S >= 1).sum() // 2), "≥2:", int((S >= 2).sum() // 2), "≥3:", int((S >= 3).sum() // 2))

# сообщества: спектральная кластеризация (собственные векторы нормированной матрицы связей) + k-средних
deg = S.sum(1) + 0.02 * WT.sum(1) / max(1, WT.sum(1).max()) + 1e-9
Sn = (S + 0.05 * WT / max(1.0, WT.max())) / np.sqrt(np.outer(deg, deg))
vals, vecs = np.linalg.eigh(Sn)
K = 8
X = vecs[:, -K:]
X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
rng = np.random.default_rng(7)
cent = X[rng.choice(N, K, replace=False)]
for _ in range(80):
    lab = np.argmin(((X[:, None, :] - cent[None]) ** 2).sum(2), axis=1)
    new_c = np.array([X[lab == c].mean(0) if (lab == c).any() else cent[c] for c in range(K)])
    if np.allclose(new_c, cent):
        break
    cent = new_c
sizes = Counter(lab)
top_cl = [c for c, _ in sizes.most_common() if sizes[c] >= 4][:8]
cl = np.array([top_cl.index(c) if c in top_cl else -1 for c in lab])

np.savez(HERE / "world_graph.npz", S=S, WT=WT, cl=cl, names=np.array([e["name"] for e in pool]), texts=np.array([e["poems"] + e["essays"] for e in pool]))
# раскладка «островами»: круг имён — остров на кольце, внутри острова самые упоминаемые ближе к центру (спираль)
def island_layout(cl, tx):
    ids = sorted(set(cl.tolist()) - {-1}, key=lambda c: -int((cl == c).sum()))
    size = {c: int((cl == c).sum()) for c in ids}
    rad = {c: 0.11 * np.sqrt(size[c]) + 0.05 for c in ids}
    tot = sum(2 * rad[c] for c in ids); a = 0.3; cen = {}
    R = max(0.62, tot / (2 * np.pi) * 1.08)
    for c in ids:
        wd = 2 * rad[c] / tot * 2 * np.pi
        cen[c] = R * np.array([np.cos(a + wd / 2), np.sin(a + wd / 2)]); a += wd
    P = np.zeros((len(cl), 2)); golden = 2.39996
    for c in ids:
        mem = sorted((i for i in range(len(cl)) if cl[i] == c), key=lambda i: -tx[i])
        sc = rad[c] / np.sqrt(len(mem) + 0.5)
        for r, i in enumerate(mem):
            P[i] = cen[c] + sc * np.sqrt(r + 0.5) * np.array([np.cos(r * golden), np.sin(r * golden)])
    free = [i for i in range(len(cl)) if cl[i] == -1]
    for r, i in enumerate(free):
        P[i] = 0.28 * np.sqrt((r + 0.5) / max(1, len(free))) * np.array([np.cos(r * golden), np.sin(r * golden)])
    return P / (np.abs(P).max() * 1.04)


pos = island_layout(cl, np.array([e["poems"] + e["essays"] for e in pool]))

nodes = []
for i, e in enumerate(pool):
    nb = [(int(j), float(S[i, j])) for j in np.argsort(-S[i])[:6] if S[i, j] > 0]
    d = ent_out(e, i)
    d.update({"cl": int(cl[i]), "x": round(float(pos[i, 0]), 4), "y": round(float(pos[i, 1]), 4), "nb": [[j, round(w, 2)] for j, w in nb]})
    nodes.append(d)
keep = {(i, j) for i in range(N) for j in range(i + 1, N) if S[i, j] >= 2}
for i in range(N):                          # у каждого узла — хотя бы самая сильная связь
    if S[i].max() >= 1:
        j = int(np.argmax(S[i])); keep.add((min(i, j), max(i, j)))
edges = [[i, j, round(float(S[i, j]), 2)] for i, j in sorted(keep)]
clusters = []
for c in range(len(top_cl)):
    mem = sorted((i for i in range(N) if cl[i] == c), key=lambda i: -(pool[i]["poems"] + pool[i]["essays"]))
    clusters.append({"names": [pool[i]["name"] for i in mem[:3]], "n": len(mem)})

OUT = {"periods": [p[2] for p in PERIODS],
       "persons": {"nodes": nodes, "edges": edges, "clusters": clusters, "total": len(persons),
                   "poems_named": sum(1 for e in persons if e["np"] > 0),
                   "others": [ent_out(e) for e in persons if e["l"] not in idx and e["n"] >= 2]},
       "places": {"named": [ent_out(e) for e in sorted(places, key=lambda e: (-(e["poems"] + e["essays"]), -e["n"]))[:60]],
                  "total_named": len(places), "generic": lex_out("places")},
       "transport": lex_out("transport"), "food": lex_out("food"), "drinks": lex_out("drinks"),
       "meta": {"texts": len(texts), "poems": sum(t["poetry"] for t in texts)}}
(HERE / "world.json").write_text(json.dumps(OUT, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("world.json", round((HERE / "world.json").stat().st_size / 1024), "KB | узлов", N, "рёбер", len(edges), "| кластеров", len(clusters))
for c in clusters:
    print("  ", c["n"], c["names"])

if __name__ == "__main__" and "--audit" in __import__("sys").argv:
    # сверка со словами в сыром тексте: слова, которые начинаются как словарное слово, но не сосчитаны
    print("===== АУДИТ ПРОПУСКОВ")
    blob = [(ti, E(" ".join(t["lines"]).lower())) for ti, t in enumerate(texts)]
    for cat, groups in LEX.items():
        for g, ws in groups.items():
            for w in ws.split():
                st = E(w)[:-1] if len(w) > 4 else E(w)
                forms = Counter()
                for ti, b in blob:
                    for m in re.finditer(r"(?<![а-я])" + re.escape(st) + r"[а-я]{0,3}(?![а-я])", b):
                        forms[m.group(0)] += 1
                got = LEXREC.get((cat, g, E(lemma(w))), {"n": 0})["n"]
                tot = sum(forms.values())
                if tot > got:
                    print(f"{cat}/{w}: по тексту {tot}, засчитано {got}; формы: {dict(forms.most_common(6))}")

if __name__ == "__main__" and "--ctx" in __import__("sys").argv:
    for word in __import__("sys").argv[__import__("sys").argv.index("--ctx") + 1:]:
        k = next((k for k in LEXREC if LEX_LEMMA[k[2]][2] == word), None)
        if not k:
            print("==", word, "— нет"); continue
        r = LEXREC[k]
        print("==", word, r["n"])
        for ti, li, kk in r["occ"][:6]:
            sp = tok_span(ti, li, kk); ln = texts[ti]["lines"][li].strip(); a = max(0, (sp[0] if sp else 0) - 45)
            print("     ", texts[ti]["title"][:22], "|", ln[a:a + 100])
if __name__ == "__main__" and "--disc" in __import__("sys").argv:
    """Поиск слов, которых нет в словарях: существительные в 4 словах после глаголов питья, еды и движения."""
    groups = {
        "пьют": {"пить", "выпить", "налить", "допить", "пригубить", "глотать", "хлебнуть", "запить", "выпивать", "разливать", "наливать", "распить"},
        "едят": {"есть", "съесть", "кушать", "жевать", "ужинать", "обедать", "завтракать", "закусывать", "закусить", "жарить", "варить", "печь", "испечь", "доесть"},
        "едут": {"ехать", "поехать", "ездить", "плыть", "поплыть", "плавать", "лететь", "полететь", "летать", "сесть", "садиться", "отплыть", "прибыть", "уехать", "приехать", "уплыть", "улететь", "сойти", "погрузиться"},
    }
    known = {E(lemma(w)) for cat in LEX.values() for gr in cat.values() for w in gr.split()}
    for gname, verbs in groups.items():
        cnt = Counter(); ex = {}
        for ti, wl in enumerate(words_by_text):
            for a, (lm, pos, bk, li, k) in enumerate(wl):
                if lm in verbs:
                    for lm2, pos2, bk2, li2, k2 in wl[a + 1: a + 5]:
                        if pos2 == "NOUN" and E(lm2) not in known:
                            cnt[lm2] += 1
                            ex.setdefault(lm2, texts[ti]["lines"][li2].strip()[:80])
        print("=====", gname)
        print(", ".join(f"{w} {n}" for w, n in cnt.most_common(70)))

if __name__ == "__main__" and "--unk" in __import__("sys").argv:
    """Слова, которых не знает pymorphy (как «граппа»), рядом с глаголами питья и еды: кандидаты для словарей."""
    vb = {"пить", "выпить", "налить", "допить", "пригубить", "глотать", "хлебнуть", "запить", "выпивать", "наливать", "есть", "съесть", "закусывать", "ужинать", "обедать", "завтракать", "жевать", "закусить", "бутылка", "стакан", "рюмка", "бокал", "графин", "стол", "буфет", "ужин", "обед", "завтрак", "закуска"}
    seen = defaultdict(list)
    for ti, wl in enumerate(words_by_text):
        for a, (lm, pos, bk, li, k) in enumerate(wl):
            if lm in vb:
                for lm2, pos2, bk2, li2, k2 in wl[max(0, a - 6): a + 7]:
                    if not parses(lm2)[0].is_known and len(lm2) > 3:
                        seen[lm2].append((texts[ti]["title"][:20], texts[ti]["lines"][li2].strip()[:75]))
    for w, v in sorted(seen.items(), key=lambda kv: -len(kv[1]))[:60]:
        print(w, len(v), "|", v[0][1])
if __name__ == "__main__" and "--qa" in __import__("sys").argv:
    print("===== СЛОВАРИ")
    for cat in LEX:
        for g in LEX[cat]:
            row = sorted(((k[2], r["n"], r["np"], r["nr"]) for k, r in LEXREC.items() if k[0] == cat and k[1] == g), key=lambda x: -x[1])
            print(f"[{cat}/{g}]", ", ".join(f"{w} {n}({np}/{nr})" for w, n, np, nr in row))
    for grp, nm in ((persons[:0], "ЛИЦА"),):
        print("=====", nm)
        for e in grp:
            c = e["ctx"][0] if e["ctx"] else {"s": "", "t": ""}
            print(f'{e["name"]:16} n={e["n"]:<4} стихи={e["np"]:<4} проза={e["nr"]:<4} | {c["t"][:26]} | {c["s"][:80]}')
