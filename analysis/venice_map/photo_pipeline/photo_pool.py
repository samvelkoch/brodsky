#!/usr/bin/env python3
"""Скачивает превью (640 px, upload.wikimedia.org) отобранного пула и строит контактные листы cache/sheets/N.jpg для просмотра.
Пул — индексы в cache/commons_all.json (после photo_search.py)."""
import json, sys, time, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).parent; C = HERE / "cache"; T = C / "thumbs"; S = C / "sheets"; T.mkdir(exist_ok=True); S.mkdir(exist_ok=True)
UA = "naprosvet-sketch/0.1 (+https://github.com/samvelkoch/naprosvet)"
POOL = {
 1: [2, 4, 19, 20, 21, 0, 16, 17],
 2: [0, 4, 5, 22, 6, 13, 18, 14],
 3: [0, 1, 2, 7, 8, 10, 11, 3, 4],
 4: [0, 2, 3, 4, 5, 6, 10, 13, 21, 28, 29, 30, 9, 12],
 5: [3, 6, 0, 2, 4, 7],
 6: [7, 9, 10, 11, 12, 13, 5, 18, 19, 20],
 7: [4, 9, 10, 13, 14, 15, 18, 20, 3, 17],
 8: [1, 2, 7, 5, 8, 0, 6],
 9: [5, 8, 9, 12, 15, 26, 27, 24, 34, 37, 38, 30, 33, 10, 6, 19],
 10: [1, 2, 3, 5, 13, 14, 17, 26, 25, 33, 21, 6, 7, 8, 9],
 11: [25, 28, 33, 35, 26, 27, 0, 2, 18, 29, 31],
}
def dl(url, f):
    if f.exists() and f.stat().st_size > 1000: return
    for att in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read(); f.write_bytes(data); time.sleep(1.0); return
        except Exception as e:
            print("retry", url, e); time.sleep(5 * (att + 1))
if __name__ == "__main__":
    allc = json.load(open(C / "commons_all.json"))
    for pid, idx in POOL.items():
        files = allc[str(pid)]; tiles = []
        for i in idx:
            f = files[i]; p = T / f"{pid}_{i}.jpg"; dl(f["thumb"], p); tiles.append((i, p, f))
        W, H, cols = 320, 240, 4; rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (W * cols, (H + 18) * rows), "white"); d = ImageDraw.Draw(sheet)
        for k, (i, p, f) in enumerate(tiles):
            try: im = Image.open(p).convert("RGB")
            except Exception: continue
            im.thumbnail((W, H)); x, y = (k % cols) * W, (k // cols) * (H + 18)
            sheet.paste(im, (x, y + 18)); d.text((x + 3, y + 3), f"[{i}] {f['title'][5:40]}", fill="black")
        sheet.save(S / f"{pid}.jpg", quality=80); print(pid, "лист готов", len(tiles))
