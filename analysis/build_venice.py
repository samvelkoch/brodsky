"""Сборник «Бродский и Венеция».

Отбор в три шага:
1. Кандидаты — автоматически: венецианские маркеры в тексте (леммы и топонимы) или в названии.
2. Каждый кандидат просмотрен в контексте вручную; вердикт и причина записаны в DECISIONS.
3. Если кандидат появился, а вердикта для него нет, — сборка падает (ничего не пропускаем молча).

    python analysis/build_venice.py
    python build_epub.py --in analysis/venice.jsonl --out brodsky_venice.epub --book-title "Иосиф Бродский. Венеция" ...
"""
import json
import pickle
import re
from pathlib import Path

HERE = Path(__file__).parent
C = pickle.load(open(HERE / "corpus.pkl", "rb"))

LEMMAS = {"венеция", "венецианский", "венецианец", "венецианка", "venice", "venetian", "venezia",
          "гондола", "гондольер", "gondola", "вапоретто", "риальто", "джудекка", "дзаттере", "мурано",
          "торчелло", "бурано", "серениссима"}
PATTERNS = [r"сан[- ]марк", r"сан[- ]микел", r"сан[- ]джорджо", r"сан[- ]дзаккари", r"canal grande",
            r"канал[а-я]* гранде", r"fondamenta", r"фондамент", r"incurabili", r"неисцелим", r"лагун",
            r"lagoon", r"\bлидо\b", r"салюте", r"адриатик", r"марчелло"]
TITLE_RX = r"венеци|venice|venezia|лагун|сан[- ]пьетро|сан[- ]марк|неисцелим|марчелло|гондол|\bлидо\b"

# title-префикс → (вердикт, режим, причина). Режимы: full | fragment | subpoem:<название>
DECISIONS = {
    "Венецианские строфы (1)": ("in", "full", "Венеция в названии и тексте"),
    "Венецианские строфы (2)": ("in", "full", "Венеция в названии"),
    "Лагуна": ("in", "full", "венецианская лагуна, Сан-Марко, гондола"),
    "Сан-Пьетро": ("in", "full", "название; «городок Северной Адриатики» — связь с Венецией по названию, "
                                 "в самом тексте город не назван"),
    "Лидо": ("in", "full", "название — остров Лидо; в тексте маркеров нет"),
    "Посвящается Джироламо Марчелло": ("in", "full", "адресат — венецианец; прибытие морем зимой"),
    "В Италии": ("in", "full", "«лучшая в мире лагуна с золотой голубятней»"),
    "НАБЕРЕЖНАЯ НЕИСЦЕЛИМЫХ (полная редакция": ("in", "full", "книга о Венеции; берётся полная редакция СИБ"),
    "Набережная неисцелимых - \"Fondamenta": ("out", "", "дубль: вместо неё полная редакция СИБ"),
    "Посмертные публикации": ("in", "subpoem:С натуры", "из подборки берётся только «С натуры» — "
                                                        "Джироламо Марчелло, «венецианское небо»"),
    "Трофейное": ("in", "fragment", "эпизод: открытки с видами Венеции, романы Анри де Ренье"),
    "Никакой мелодрамы": ("in", "fragment", "ответ о романах де Ренье с зимней Венецией"),
    "Свена Биркертс": ("in", "fragment", "вопрос и ответ «почему вы любите Венецию»"),
    "Римлянин": ("in", "fragment", "вдова о похоронах Бродского в Венеции"),
    "Иосиф Бродский - Елена Якович": ("out", "", "Венеция только в подписи «Венеция. Ноябрь 1993»"),
    "Место не хуже любого": ("in", "mention", "Фениче и Сан-Джорджо — в перечне черт «любого» города"),
    "Эклога 4-я": ("out", "", "«салют» — фейерверк, не Салюте"),
    "В Англии": ("out", "", "«венецианское стекло» в лондонском интерьере"),
    "Вертумн": ("out", "", "Адриатика упомянута мимоходом, стихотворение о Риме"),
    "\"Пришла зима": ("out", "", "«гондолы» — железнодорожные вагоны"),
    "На стороне Кавафиса": ("out", "", "«неисцелимой скуки» — не топоним"),
    "ПУТЕВОДИТЕЛЬ ПО ПЕРЕИМЕНОВАННОМУ ГОРОДУ": ("out", "", "«венецианские окна» в Петербурге"),
    "ДАНЬ МАРКУ АВРЕЛИЮ": ("out", "", "пьяцца Венеция в Риме"),
    "Путешествие в Стамбул": ("in", "mention", "пароходная линия Стамбул — Венеция"),
    "Иосиф Бродский. История двадцатого века": ("in", "mention", "Дворец дожей Моне в перечне"),
    "Бенгт Янгфельдт": ("in", "mention", "текст о Бродском: где писалась «Набережная»"),
    "ТРИ СТИХОТВОРЕНИЯ ЛИНУЧЧЕ": ("out", "", "перевод, Адриатика вообще"),
    "ЗАГОВОРЕННЫЕ ДРОЖКИ": ("out", "", "перевод, улица Венеции в Кракове"),
}


def markers(o):
    low = o["text"].lower()
    n = sum(l in LEMMAS for l in o["lemmas"]) + sum(len(re.findall(p, low)) for p in PATTERNS)
    return n


def decision_for(title):
    for k, v in DECISIONS.items():
        if title.startswith(k):
            return k, v
    return None, None


HIT_RX = r"венеци|гондол|лагун|сан[- ]марк"


def trim(par, window=2, limit=1500):
    """Длинный абзац → только предложения с упоминанием ± window соседних."""
    if len(par) <= limit:
        return par
    sents = re.split(r"(?<=[.!?…])\s+", par)
    hit = {i for i, x in enumerate(sents) if re.search(HIT_RX, x, re.I)}
    keep = sorted({j for i in hit for j in range(i - window, i + window + 1) if 0 <= j < len(sents)})
    out, prev = [], None
    for j in keep:
        if prev is not None and j != prev + 1:
            out.append("<...>")
        out.append(sents[j])
        prev = j
    return ("<...> " if keep[0] > 0 else "") + " ".join(out) + (" <...>" if keep[-1] < len(sents) - 1 else "")


def fragment(text, neighbors):
    """Абзацы с упоминаниями (± соседний абзац для прозы); пропуски помечаются <...>."""
    paras = re.split(r"\n\s*\n", text)
    hit = {i for i, x in enumerate(paras) if re.search(HIT_RX, x, re.I)}
    keep = sorted({j for i in hit for j in range(i - neighbors, i + neighbors + 1) if 0 <= j < len(paras)})
    out, prev = [], None
    for j in keep:
        if prev is not None and j != prev + 1:
            out.append("<...>")
        out.append(trim(paras[j]))
        prev = j
    if keep and keep[0] > 0:
        out.insert(0, "<...>")
    if keep and keep[-1] < len(paras) - 1:
        out.append("<...>")
    return "\n\n".join(out)


def mention(text):
    """Только предложения с упоминанием Венеции ± одно соседнее."""
    sents = re.split(r"(?<=[.!?…])\s+", re.sub(r"\s*\n\s*", " ", text))
    hit = {i for i, x in enumerate(sents) if re.search(r"венеци|venice|фениче|сан[- ]джорджо", x, re.I)}
    keep = sorted({j for i in hit for j in (i - 1, i, i + 1) if 0 <= j < len(sents)})
    out, prev = [], None
    for j in keep:
        if prev is None or j != prev + 1:
            out.append("<...>")
        out.append(sents[j])
        prev = j
    return " ".join(out) + " <...>"


def subpoem(text, name):
    """Вырезает стихотворение из подборки: от строки-заголовка до следующего заголовка без отступа."""
    lines = text.split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == name and not l.startswith(" "))
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].strip() and not lines[i].startswith(" ") and i > start + 2), len(lines))
    return "\n".join(lines[start + 1:end]).strip("\n")


def main():
    cands, log, missing = [], [], []
    for o in C:
        if o["author"] == "other":
            continue
        n = markers(o)
        t_hit = bool(re.search(TITLE_RX, o["title"].lower()))
        if not (n or t_hit):
            continue
        key, dec = decision_for(o["title"])
        if dec is None:
            missing.append((o["title"], n))
            continue
        cands.append((o, n, dec))
        log.append({"title": o["title"], "markers": n, "per1k_words": round(1000 * n / max(1, len(o["tokens"])), 2),
                    "title_hit": t_hit, "verdict": dec[0], "mode": dec[1], "reason": dec[2]})
    if missing:
        raise SystemExit(f"Нет вердикта для кандидатов: {missing}")

    recs = []
    for o, n, (verdict, mode, reason) in cands:
        if verdict != "in":
            continue
        title, text = o["title"], o["text"]
        if mode == "fragment":
            text, title = fragment(text, 0 if o["author"] == "about" else 1), f"{title} (фрагмент)"
        elif mode.startswith("subpoem:"):
            name = mode.split(":", 1)[1]
            text, title = subpoem(text, name), name
        elif mode == "mention":
            text, title = mention(text), f"{title} (упоминание)"
        poetry = o["genre"] == "poetry"
        sec = ("Упоминания Венеции" if mode == "mention" else "Стихотворения" if poetry else
               "Из интервью" if o["author"] == "about" else "Проза")
        recs.append({"title": title, "text": text, "section_title": sec, "period": None,
                     "url": o["url"], "source": o["source"],
                     "_order": (["Стихотворения", "Проза", "Из интервью", "Упоминания Венеции"].index(sec), o["year"] or 9999)})
    recs.sort(key=lambda r: r["_order"])

    ins = [l for l in log if l["verdict"] == "in"]
    outs = [l for l in log if l["verdict"] == "out"]
    method = (
        "Сборник составлен из объединённого собрания (сайт iosif-brodskiy.ru + «Сочинения Иосифа Бродского» "
        "в 7 томах).\n\n"
        "Шаг 1. Автоматический поиск кандидатов: венецианские слова и топонимы в тексте (Венеция, венецианский, "
        "гондола, лагуна, Сан-Марко, Джудекка, Фондамента, Лидо, Адриатика, Марчелло и др., с учётом падежей) "
        "или в названии.\n\n"
        f"Шаг 2. Каждый из {len(log)} кандидатов прочитан в контексте. Включены тексты о Венеции; из прозы и "
        "интервью, где Венеция — эпизод, взяты только эти фрагменты (пропуски помечены <...>). Исключены "
        "случайные совпадения.\n\n"
        "Шаг 3. Сверка с внешним перечнем: S. Panicieri, «Brodsky's Travelling Exile Pays Homage to Venice» "
        "(eSamizdat) называет 8 русских стихотворений о Венеции 1973–1995 гг.: «Лагуна» (1973), «Сан-Пьетро» "
        "(1977), «Венецианские строфы» I и II (1982), «В Италии» (1985), «Посвящается Джироламо Марчелло» "
        "(1988), «Лидо» (1989), «С натуры» / In Front of Casa Marcello (1995). Все 8 найдены шагами 1–2.\n\n"
        "Раздел «Упоминания Венеции» — выдержки из текстов, где город упомянут, но не является темой.\n\n"
        "Ограничение: стихотворение о Венеции, в котором нет ни одного маркера и название ничего не подсказывает, "
        "этим методом не находится.\n\n"
        f"Включено ({len(ins)}):\n" + "\n".join(f"— {l['title']}: {l['reason']}" for l in ins) +
        f"\n\nИсключено ({len(outs)}):\n" + "\n".join(f"— {l['title']}: {l['reason']}" for l in outs))
    recs.append({"title": "Как отбирались тексты", "text": method, "section_title": "О сборнике",
                 "period": None, "url": "", "source": "составитель"})

    with open(HERE / "venice.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            r.pop("_order", None)
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(log, open(HERE / "venice_selection.json", "w"), ensure_ascii=False, indent=1)
    print(f"кандидатов {len(log)}: включено {len(ins)}, исключено {len(outs)}; записей в книге {len(recs)}")
    for r in recs:
        print(f"  [{r['section_title']}] {r['title'][:60]} — {len(r['text'])} симв.")


if __name__ == "__main__":
    main()
