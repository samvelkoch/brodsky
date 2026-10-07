#!/usr/bin/env python3
"""Обработка фото: кроп 4:3, два варианта (оттенки серого; цвет подставляет страница из --ink/--page):
 duo  — «дуотон»: тоновая коррекция, мягкий контраст (на странице: тени -> чернила, света -> бумага)
 hatch — «гравюра»: диагональная штриховка с перекрёстной на тенях, мягкая растушёвка"""
import numpy as np
from PIL import Image, ImageFilter, ImageOps

OUT_W, OUT_H = 640, 480           # 2x; 1x = 320x240

def crop43(im, fx=0.5, fy=0.5, zoom=1.0):
    """Кроп 4:3 с центром в (fx, fy) относительно кадра; zoom>1 — ближе."""
    W, H = im.size
    cw = min(W, H * 4 / 3) / zoom; ch = cw * 3 / 4
    x0 = min(max(fx * W - cw / 2, 0), W - cw); y0 = min(max(fy * H - ch / 2, 0), H - ch)
    return im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch)))

def tone(im):
    g = ImageOps.grayscale(im.convert("RGB")).resize((OUT_W, OUT_H), Image.LANCZOS)
    a = np.asarray(g, dtype=np.float32) / 255
    lo, hi = np.percentile(a, 1.5), np.percentile(a, 98.5)
    a = np.clip((a - lo) / max(hi - lo, 1e-3), 0, 1)
    return a

def duo(im):
    a = tone(im)
    a = a ** 0.95
    a = 0.04 + 0.92 * a                       # не уходим в чистые чёрный/белый: на странице это ink/page
    return Image.fromarray((a * 255).round().astype(np.uint8), "L").filter(ImageFilter.UnsharpMask(1.2, 60, 2))

def hatch(im, ss=3):
    a = tone(im)
    L = Image.fromarray((a * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(1.1))
    big = np.asarray(L.resize((OUT_W * ss, OUT_H * ss), Image.BICUBIC), dtype=np.float32) / 255
    dark = 1 - big
    h, w = big.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    period = OUT_W * ss / 105.0                # одинаково выглядит на 1x и 2x (период ~ 1/105 ширины)
    def lines(angle, width):
        c, s = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        u = (xx * c + yy * s) / period
        tri = np.abs((u % 1.0) - 0.5) * 2         # 0 на оси линии, 1 между линиями
        gain = period / (2.0 * ss)                # край линии размыт на ~1 px финальной картинки
        return np.clip((np.clip(width, 0, 1) - tri) * gain, 0, 1)
    ink = lines(45, (dark - 0.06) * 1.15)
    ink2 = lines(135, (dark - 0.55) * 1.7)
    ink = np.maximum(ink, ink2)
    out = 1 - ink
    img = Image.fromarray((out * 255).astype(np.uint8), "L").resize((OUT_W, OUT_H), Image.LANCZOS)
    o = np.asarray(img, dtype=np.float32) / 255
    base = np.asarray(L, dtype=np.float32) / 255
    o = 0.80 * o + 0.20 * base                 # лёгкая тоновая подложка — «растушёвка»
    o = 0.05 + 0.90 * o
    return Image.fromarray((o * 255).round().astype(np.uint8), "L")

def save_webp(img, path, max_kb=None, q=70):
    """Сохраняет webp; для 1x подбирает качество, чтобы уложиться в max_kb."""
    for qq in range(q, 20, -4):
        img.save(path, "WEBP", quality=qq, method=6)
        if max_kb is None or path.stat().st_size <= max_kb * 1024: return qq
    return qq
