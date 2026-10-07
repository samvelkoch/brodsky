#!/usr/bin/env python3
"""Экспорт утверждённого набора в репозиторий brodsky: analysis/venice_map/places.json (только выбранные фото) и photos/N.webp (дуотон, 640x480).
Запуск: ../.venv/bin/python export_site.py [куда, по умолчанию /Users/samvel/claude-workspace/brodsky/analysis/venice_map]"""
import json, shutil, sys
from pathlib import Path
HERE = Path(__file__).parent
DEST = Path(sys.argv[1] if len(sys.argv) > 1 else "/Users/samvel/claude-workspace/brodsky/analysis/venice_map")
CHOSEN = {1: "1a", 2: "2c", 3: "3c", 4: "4c", 5: "5a", 6: "6b", 7: "7c", 8: "8c", 9: "9a", 10: "10c", 11: "11a"}   # решение пользователя
data = json.loads((HERE / "places.json").read_text(encoding="utf-8")); (DEST / "photos").mkdir(parents=True, exist_ok=True)
out = []
for p in data["places"]:
    key = CHOSEN[p["n"]]; c = next(c for c in p["photo_candidates"] if c["key"] == key)
    shutil.copyfile(HERE / "photos" / c["files"]["duo"]["x2"], DEST / "photos" / f"{p['n']}.webp")
    out.append(dict(n=p["n"], name_ru=p["name_ru"], name_it=p["name_it"], lat=p["lat"], lon=p["lon"], osm=f"{p['osm']['type']}/{p['osm']['id']}", approx=p["approx"],
                    popup_line=p["popup_line"], map=p["map"],
                    photo=dict(key=key, file=f"photos/{p['n']}.webp", note=c["note"], author=c["author"], license=c["license"], license_url=c["license_url"], page=c["commons_page"])))
meta = dict(source=data["meta"]["source"], coords=data["meta"]["coords"], map_frame=data["meta"]["map_frame"], photos="Wikimedia Commons; дуотон, кроп 4:3, 640x480")
(DEST / "places.json").write_text(json.dumps(dict(meta=meta, places=out), ensure_ascii=False, indent=1), encoding="utf-8")
print("записано", len(out), "мест в", DEST)
