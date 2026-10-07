#!/usr/bin/env python3
"""Кандидаты фото: выбор (CHOICES) -> скачать 1280-px превью с upload.wikimedia.org -> кроп 4:3 -> два варианта обработки -> webp 1x/2x.
Результат: photos/{N}{буква}_{duo|hatch}_{1x|2x}.webp, photos/index.json (метаданные и атрибуция), photos/src/ — исходные превью (кэш).
Запуск: ../.venv/bin/python photo_build.py"""
import json, re, time, urllib.request
from pathlib import Path
from PIL import Image
import treat
HERE = Path(__file__).parent; C = HERE / "cache"; P = HERE / "photos"; SRC = P / "src"; SRC.mkdir(parents=True, exist_ok=True)
UA = "naprosvet-sketch/0.1 (+https://github.com/samvelkoch/naprosvet)"
# место -> [(список в commons_all.json, индекс, буква, пометка о сюжете, (fx, fy, zoom))]
CHOICES = {
 1: [(2, 4, "a", "Palazzo Maravegia (Villa Maravege) на Fondamenta Bollani; что пансион стоит именно в этом здании, не проверено (в статье — «старая вилла»)", (.5, .42, 1)),
     (2, 20, "b", "Palazzo Maravegia, фасад с набережной", (.5, .5, 1)),
     (2, 21, "c", "Palazzo Maravegia, вид вдоль набережной", (.5, .45, 1))],
 2: [(2, 0, "a", "Fondamenta di Borgo (улица ресторана) в наводнение; сам ресторан не снят", (.5, .5, 1)),
     (2, 22, "b", "Рио ди Сан-Тровазо рядом с Fondamenta di Borgo; сам ресторан не снят", (.5, .5, 1)),
     (2, 5, "c", "Мост Сан-Тровазо рядом; сам ресторан не снят", (.5, .5, 1))],
 3: [(3, 1, "a", "Fondamenta Zattere al Ponte Lungo, где стоит Nico; кафе в кадре нет", (.5, .5, 1)),
     (3, 10, "b", "Застройка Zattere al Ponte Lungo; кафе в кадре нет", (.5, .5, 1)),
     (3, 11, "c", "Zattere al Ponte Lungo с воды; кафе в кадре нет", (.4, .55, 1.15))],
 4: [(4, 30, "a", "Бывший госпиталь Неисцелимых на набережной, вид с воды", (.5, .6, 1.5)),
     (4, 6, "b", "Casa degli Incurabili, вид с воды", (.5, .5, 1)),
     (4, 0, "c", "Памятная доска Бродскому (оговорка: итальянское право, свободы панорамы нет, скульптурная работа 2009 г.)", (.5, .5, 1))],
 5: [(5, 3, "a", "Рио де Верона (Rio Menuo o de la Verona)", (.5, .5, 1)),
     (5, 6, "b", "Табличка «Rio Menuo o de la Verona»", (.5, .3, 1))],
 6: [(6, 13, "a", "Фасад Harry's Bar, Calle Vallaresso", (.5, .5, 1)),
     (6, 12, "b", "Окно с надписью Harry's Bar", (.5, .5, 1)),
     (6, 10, "c", "Вид с Большого канала у причала Vallaresso", (.55, .5, 1))],
 7: [(7, 9, "a", "Вывеска Caffè Florian, аркады Procuratie Nuove", (.65, .5, 1)),
     (7, 10, "b", "Аркады Caffè Florian на площади Сан-Марко", (.5, .5, 1)),
     (7, 20, "c", "Интерьер с зеркалами", (.5, .5, 1))],
 8: [(8, 1, "a", "Salizada San Provolo (улица траттории); сама траттория не снята", (.3, .6, 1)),
     (8, 7, "b", "Рио ди Сан-Проволо рядом; сама траттория не снята", (.5, .5, 1)),
     (8, 5, "c", "Мост Дьявола на рио ди Сан-Проволо; сама траттория не снята", (.6, .5, 1))],
 9: [(9, 27, "a", "Fondamenta dell'Arsenale, стена Арсенала", (.5, .5, 1)),
     (9, 12, "b", "Ворота Arsenale, Campo de l'Arsenal", (.5, .5, 1)),
     (9, 37, "c", "Rio dell'Arsenale к северу", (.5, .5, 1))],
 10: [(10, 17, "a", "Campo Santi Giovanni e Paolo", (.5, .5, 1)),
      (10, 5, "b", "Campo Santi Giovanni e Paolo на закате", (.5, .5, 1)),
      (10, 13, "c", "Базилика Санти-Джованни-э-Паоло", (.5, .5, 1))],
 11: [(11, 35, "a", "Могила Бродского на Сан-Микеле", (.35, .5, 1.1)),
      (11, 25, "b", "Могила Бродского на Сан-Микеле", (.5, .5, 1)),
      (11, 0, "c", "Кладбищенская стена Сан-Микеле, вид с воды", (.5, .5, 1))],
}

def fetch(url, f):
    if f.exists() and f.stat().st_size > 2000: return
    for att in range(5):
        try:
            f.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90).read()); time.sleep(1.2); return
        except Exception as e:
            print("retry", url, e); time.sleep(6 * (att + 1))

def author(a):
    a = re.sub(r"^This (Photo|picture) (was taken by|belongs to)\s*", "", a).strip()
    a = re.sub(r"\.\s*Feel free.*$", "", a)
    return re.sub(r"\s+", " ", a)

def main():
    allc = json.load(open(C / "commons_all.json")); idx = {}
    for pid, cands in CHOICES.items():
        for lid, i, letter, note, (fx, fy, z) in cands:
            f = allc[str(lid)][i]; key = f"{pid}{letter}"
            big = re.sub(r"/\d+px-", "/1280px-", f["thumb"]); sp = SRC / f"{key}.jpg"; fetch(big, sp)
            im = Image.open(sp).convert("RGB"); cr = treat.crop43(im, fx, fy, z)
            rec = dict(key=key, place=pid, letter=letter, note=note, title=f["title"], page=f["page"], author=author(f["author"]), license=f["license"], license_url=f["license_url"],
                       source_px=[f["w"], f["h"]], crop=dict(fx=fx, fy=fy, zoom=z), files={})
            for name, fn in (("duo", treat.duo), ("hatch", treat.hatch)):
                out = fn(cr)
                p2 = P / f"{key}_{name}_2x.webp"; p1 = P / f"{key}_{name}_1x.webp"
                q2 = treat.save_webp(out, p2, None, 72)
                q1 = treat.save_webp(out.resize((320, 240), Image.LANCZOS), p1, 30, 74)
                rec["files"][name] = dict(x1=p1.name, x2=p2.name, kb1=round(p1.stat().st_size / 1024, 1), kb2=round(p2.stat().st_size / 1024, 1), q1=q1, q2=q2)
            idx[key] = rec; print(key, rec["files"]["duo"]["kb1"], rec["files"]["hatch"]["kb1"], f["license"], rec["author"][:30])
    (P / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
