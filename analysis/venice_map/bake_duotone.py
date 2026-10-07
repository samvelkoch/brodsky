"""Печёт дуотон фото-всплывашек в готовые webp: photos/duo/N-light.webp и N-dark.webp (светлая и тёмная тема).

Раньше серый webp шёл в CSS-маску (mask-image / mask-mode:luminance): в Safari маска ложилась не так, и в кадре были
видны только небо или заливка. Теперь страница вставляет обычные <img>, а цвета запечены здесь.

Цвета берутся из report4.head.html, а не копируются: светлая тема — тени --ink, света --page; тёмная — тени --page,
света --ink (значения --page и --ink из блока :root[data-theme="dark"]; блок prefers-color-scheme:dark обязан совпадать).
Формула та же, что у маски: светимость 0.2125 R + 0.7154 G + 0.0721 B исходного серого, смешение в sRGB:
пиксель = тень + (свет - тень) * L / 255.

Размер 400x300 (всплывашка шире 240 px, внутри рамки 226 px, т.е. около 1.8x), webp q70, method 6.
Нужны pillow и numpy; результат лежит в репозитории, block.py читает готовые файлы (только стандартная библиотека).

    python bake_duotone.py
"""
import re
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
HEAD = HERE.parent / "report4.head.html"
SIZE = (400, 300)
QUALITY = 70


def _hex(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def theme_colors():
    css = HEAD.read_text(encoding="utf-8")

    def pick(block_start):
        i = css.index(block_start)
        blk = css[i:css.index("}", i)]
        return {k: re.search(rf"--{k}:(#[0-9a-fA-F]{{6}})", blk).group(1) for k in ("page", "ink")}

    light = pick(":root{")
    dark = pick(':root[data-theme="dark"]{')
    media = pick(':root:not([data-theme="light"]){')
    assert media == dark, "prefers-color-scheme:dark и data-theme=dark разошлись"
    return {"light": (_hex(light["ink"]), _hex(light["page"])),     # (тени, света)
            "dark": (_hex(dark["page"]), _hex(dark["ink"]))}


def main():
    cols = theme_colors()
    out = HERE / "photos" / "duo"
    out.mkdir(exist_ok=True)
    total = 0
    for src in sorted((HERE / "photos").glob("*.webp"), key=lambda p: int(p.stem)):
        a = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32)
        lum = (0.2125 * a[..., 0] + 0.7154 * a[..., 1] + 0.0721 * a[..., 2]) / 255
        lum = np.asarray(Image.fromarray(np.rint(lum * 255).astype(np.uint8)).resize(SIZE, Image.LANCZOS), dtype=np.float32) / 255
        for theme, (d, l) in cols.items():
            d, l = np.array(d, np.float32), np.array(l, np.float32)
            img = Image.fromarray(np.rint(d + (l - d) * lum[..., None]).astype(np.uint8))
            dst = out / f"{src.stem}-{theme}.webp"
            img.save(dst, "WEBP", quality=QUALITY, method=6)
            total += dst.stat().st_size
            print(dst.name, round(dst.stat().st_size / 1024, 1), "KB")
    print("итого", round(total / 1024), "KB,", cols)


if __name__ == "__main__":
    main()
