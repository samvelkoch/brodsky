#!/usr/bin/env python3
"""Карта Венеции для раздела «Венеция» отчёта «Бродский на просвет».

Источник геометрии: OpenStreetMap через Overpass API (ODbL), © участники OpenStreetMap.
Запросы лежат в cache/*.ql, ответы кэшируются в cache/*.json. Большой ответ cache/base.json (около 16 МБ)
в репозиторий не входит: без него скрипт заново запросит Overpass (карта может чуть измениться вслед за OSM).

    python build_map.py   # -> venice-map.svg (отдельный файл), map-fragment.svg и points.json

В отчёт идут готовые map-fragment.svg и points.json: их читает block.py, поэтому для сборки страницы
этот скрипт и его библиотеки (shapely, pyproj, numpy; см. requirements.txt) не нужны.
"""
import json
import math
import random
import time
import urllib.request
import urllib.parse
from pathlib import Path

import numpy as np
from pyproj import Transformer
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely import make_valid
from shapely.ops import linemerge, polygonize, unary_union
from shapely import affinity

HERE = Path(__file__).parent
CACHE = HERE / "cache"
UA = "naprosvet-sketch/0.1 (+https://github.com/samvelkoch/naprosvet)"

# ------------------------------------------------------------------ охват и масштаб
LAT_S, LAT_N, LON_W, LON_E = 45.4212, 45.4505, 12.312, 12.358      # видимая рамка карты
SCALE = 1.6                                                       # единиц SVG на метр

# ------------------------------------------------------------------ точки (источники см. POINTS_SRC)
def _load_points():
    """Точки — из places.json (11 мест из статьи 1600.venezia.it; координаты — OpenStreetMap)."""
    d = json.loads((HERE / "places.json").read_text(encoding="utf-8"))
    return [dict(n=p["n"], name=p["name_ru"], lat=p["lat"], lon=p["lon"], osm=p["osm"]) for p in d["places"]]


POINTS = _load_points()

# ------------------------------------------------------------------ Overpass: один запрос на основу, кэш на диск
BASE_QL = CACHE / "q_base.ql"
BASE_JSON = CACHE / "base.json"


def fetch_base():
    if BASE_JSON.exists() and BASE_JSON.stat().st_size > 1_000_000:
        return
    CACHE.mkdir(exist_ok=True)
    bb = "(45.416,12.306,45.456,12.368)"
    ql = f"""[out:json][timeout:180][maxsize:268435456];
(
 way["building"]{bb}; relation["building"]{bb};
 way["natural"="coastline"]{bb};
 way["natural"="water"]{bb};
 way["waterway"~"^(canal|riverbank|river|dock)$"]{bb}; relation["waterway"="riverbank"]{bb};
 way["place"~"^(island|islet)$"]{bb}; relation["place"~"^(island|islet)$"]{bb};
 way["landuse"~"^(cemetery|grass|forest)$"]{bb}; relation["landuse"="cemetery"]{bb};
 way["leisure"~"^(park|garden)$"]{bb};
 way["man_made"~"^(pier|breakwater)$"]{bb};
);
out geom;"""
    BASE_QL.write_text(ql)
    req = urllib.request.Request("https://overpass-api.de/api/interpreter",
                                 data=urllib.parse.urlencode({"data": ql}).encode(), headers={"User-Agent": UA})
    BASE_JSON.write_bytes(urllib.request.urlopen(req, timeout=300).read())


# ------------------------------------------------------------------ проекция: Web Mercator, поправленная на широту (≈ метры)
_T = Transformer.from_crs(4326, 3857, always_xy=True)
_K = math.cos(math.radians((LAT_S + LAT_N) / 2))
_X0, _Y0 = _T.transform(LON_W, LAT_S)
_X1, _Y1 = _T.transform(LON_E, LAT_N)
W_M, H_M = (_X1 - _X0) * _K, (_Y1 - _Y0) * _K
W_U, H_U = round(W_M * SCALE), round(H_M * SCALE)


def proj(lon, lat):
    x, y = _T.transform(lon, lat)
    return (x - _X0) * _K, (y - _Y0) * _K


def proj_pts(g):
    lons = np.array([p["lon"] for p in g]); lats = np.array([p["lat"] for p in g])
    x, y = _T.transform(lons, lats)
    return list(zip((x - _X0) * _K, (y - _Y0) * _K))


# ------------------------------------------------------------------ сборка геометрии OSM
def way_line(e):
    g = e.get("geometry")
    return LineString(proj_pts(g)) if g and len(g) > 1 else None


def way_poly(e):
    g = e.get("geometry")
    if not g or len(g) < 4:
        return None
    pts = proj_pts(g)
    if pts[0] != pts[-1]:
        return None
    p = Polygon(pts)
    return p if p.is_valid else p.buffer(0)


def rel_poly(e):
    outers, inners = [], []
    for m in e.get("members", []):
        g = m.get("geometry")
        if not g or len(g) < 2 or m.get("type") != "way":
            continue
        (inners if m.get("role") == "inner" else outers).append(LineString(proj_pts(g)))
    if not outers:
        return None
    try:
        o = unary_union([make_valid(q) for q in polygonize(linemerge(outers))])
        if o.is_empty:
            return None
        if inners:
            i = unary_union([make_valid(q) for q in polygonize(linemerge(inners))])
            if not i.is_empty:
                o = o.difference(i)
        return o if o.is_valid else make_valid(o)
    except Exception:          # битые отношения OSM (самопересечения) пропускаем
        return None


def poly_of(e):
    return way_poly(e) if e["type"] == "way" else rel_poly(e)


LAGOON_REL = 3049430          # «Laguna di Venezia», 85 тыс. точек: в основу не берём
SKIP_BLD = {"roof", "bridge", "kiosk", "portal", "column", "grandstand", "hut", "shed"}
SOLID_BLD = {"church", "cathedral", "chapel", "basilica"}


def load():
    els = json.loads(BASE_JSON.read_text())["elements"]
    clip = box(-60, -60, W_M + 60, H_M + 60)
    L = dict(island=[], water=[], canal=[], bld=[], solid=[], cem=[], green=[], pier=[])
    for e in els:
        if e["type"] == "relation" and e["id"] == LAGOON_REL:
            continue
        t = e.get("tags", {})
        if t.get("place") in ("island", "islet"):
            g = poly_of(e)
            if g is not None: L["island"].append(g)
        if t.get("natural") == "water" and t.get("water") != "lagoon" or t.get("waterway") in ("riverbank", "dock"):
            g = poly_of(e)
            if g is not None and not g.is_empty: L["water"].append(g)
        if t.get("waterway") in ("canal", "river") and e["type"] == "way":
            g = way_line(e)
            if g is not None: L["canal"].append((g, t.get("width")))
        if "building" in t and t["building"] not in SKIP_BLD and t.get("man_made") != "pier":
            g = poly_of(e)
            if g is not None and not g.is_empty:
                (L["solid"] if t["building"] in SOLID_BLD else L["bld"]).append(g)
        if t.get("landuse") == "cemetery":
            g = poly_of(e)
            if g is not None: L["cem"].append(g)
        if t.get("landuse") in ("grass", "forest") or t.get("leisure") in ("park", "garden"):
            g = poly_of(e)
            if g is not None: L["green"].append(g)
    L["_clip"] = clip
    return L


# ------------------------------------------------------------------ «дрожание»: плавная деформация + шум вершин
_RNG = random.Random(7)


def warp_xy(x, y):
    """Гладкое смещение (амплитуда ~1.3 м): соседние контуры сдвигаются вместе, стыки домов не расходятся."""
    dx = 1.3 * math.sin(y / 31.0 + 0.7) + 0.8 * math.sin(y / 11.5 + x / 47.0)
    dy = 1.3 * math.sin(x / 37.0 + 1.9) + 0.8 * math.sin(x / 13.0 - y / 41.0)
    return x + dx, y + dy


def to_u(x, y, noise=0.0):
    x, y = warp_xy(x, y)
    if noise:
        x += _RNG.uniform(-noise, noise); y += _RNG.uniform(-noise, noise)
    return round(x * SCALE), round((H_M - y) * SCALE)


# ------------------------------------------------------------------ вывод путей (относительные целые координаты)
class PathBuilder:
    def __init__(self):
        self.parts = []
        self.cx = self.cy = 0

    def ring(self, pts, close):
        pts = [pts[0]] + [p for i, p in enumerate(pts[1:], 1) if p != pts[i - 1]]
        if close and len(pts) > 1 and pts[-1] == pts[0]:
            pts = pts[:-1]
        if len(pts) < (3 if close else 2):
            return
        s = f"m{pts[0][0] - self.cx} {pts[0][1] - self.cy}" if self.parts else f"M{pts[0][0]} {pts[0][1]}"
        px, py = pts[0]
        body = []
        for x, y in pts[1:]:
            body.append(f"{x - px} {y - py}")
            px, py = x, y
        s += "l" + " ".join(body)
        if close:
            s += "z"
            self.cx, self.cy = pts[0]
        else:
            self.cx, self.cy = px, py
        self.parts.append(s.replace(" -", "-"))

    def d(self):
        return "".join(self.parts)


def polys_of(g):
    if g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)] + \
           [q for p in getattr(g, "geoms", []) if hasattr(p, "geoms") for q in polys_of(p)]


def lines_of(g):
    if g.is_empty: return []
    if isinstance(g, LineString): return [g]
    out = []
    for p in getattr(g, "geoms", []):
        out += lines_of(p)
    return out


def polys_to_d(polys, tol, noise=0.0, min_area=0.0):
    pb = PathBuilder()
    for g in polys:
        for p in polys_of(g):
            if p.area < min_area: continue
            p = p.simplify(tol, preserve_topology=True)
            for p2 in polys_of(p):
                pb.ring([to_u(x, y, noise) for x, y in p2.exterior.coords], True)
                for r in p2.interiors:
                    pb.ring([to_u(x, y, noise) for x, y in r.coords], True)
    return pb.d()


def lines_to_d(lines, tol):
    pb = PathBuilder()
    for g in lines:
        for ln in lines_of(g):
            ln = ln.simplify(tol)
            if ln.length < 4: continue
            pb.ring([to_u(x, y) for x, y in ln.coords], False)
    return pb.d()


# ------------------------------------------------------------------ сборка слоёв
def build_layers(L):
    clip = L["_clip"]
    visible = box(0, 0, W_M, H_M)
    wide = box(-80, -80, W_M + 80, H_M + 80)

    land = unary_union([g.buffer(0) for g in L["island"]]).intersection(wide)
    carve = []
    for g, w in L["canal"]:
        try:
            width = float(str(w).replace("m", "").strip()) if w else 4.0
        except ValueError:
            width = 4.0
        carve.append(g.buffer(max(1.2, min(width, 12.0) / 2), cap_style=2))
    carve += [g.buffer(0) for g in L["water"]]
    land_c = land.difference(unary_union(carve)).buffer(0)           # суша без каналов и воды внутри городов
    # дома входят в сушу (острова размечены грубо) — так береговые дома не окажутся «в воде»
    bld_all = unary_union([g.buffer(0) for g in L["bld"] + L["solid"]]).intersection(wide)
    land_full = unary_union([land_c, bld_all]).buffer(0.5).buffer(-0.5)

    # ---- рябь воды: контуры буфера суши на растущих расстояниях
    base = land_full.simplify(2.5)
    ripples = []
    dists = [5, 11, 19, 30, 45, 64, 88, 118, 154, 196]
    for i, d in enumerate(dists):
        b = base.buffer(d, quad_segs=3)
        ln = b.boundary.intersection(visible.buffer(2))
        ripples.append(lines_to_d([ln], 1.2 + d * 0.06))

    # ---- суша (тон), дома, кладбище, зелень
    land_vis = land_full.intersection(visible)
    land_d = polys_to_d([land_vis.simplify(1.6)], 0.8)
    cem = unary_union([g.buffer(0) for g in L["cem"]]).intersection(visible)
    green = unary_union([g.buffer(0) for g in L["green"]]).intersection(visible).difference(cem)
    bl = [g for g in L["bld"] if not g.is_empty]
    bld_d = polys_to_d([g.intersection(visible) for g in bl], 0.55, noise=0.3, min_area=14)
    sol_d = polys_to_d([g.intersection(visible) for g in L["solid"]], 0.55, noise=0.3, min_area=14)
    cem_d = polys_to_d([cem.simplify(1.2)], 0.8)
    grn_d = polys_to_d([green.simplify(1.2)], 0.8)

    # ---- береговая линия (контур суши, тонкая линия)
    shore_d = lines_to_d([land_full.simplify(1.5).boundary.intersection(visible)], 1.0)
    return dict(ripples=ripples, land=land_d, bld=bld_d, sol=sol_d, cem=cem_d, grn=grn_d, shore=shore_d,
                n_bld=len(bl), n_sol=len(L["solid"]))


# ------------------------------------------------------------------ SVG
# Классы с префиксом vm-, без зависимости от предков: рисунок один раз лежит в <defs> и подключается через <use>.
# Цвета берутся из переменных сайта (--ink, --page, --s1); запасные значения — палитра сайта, светлая тема.
CSS = """
.vm{color:var(--ink,#211b16);--vm-paper:var(--page,#e9e4da);--vm-acc:var(--vm-accent,var(--s1,#c2452a))}
.vm-land{fill:currentColor;fill-opacity:.075}
.vm-shore{fill:none;stroke:currentColor;stroke-width:.9px;vector-effect:non-scaling-stroke;stroke-linejoin:round}
.vm-rip{fill:none;stroke:currentColor;stroke-width:.55px;vector-effect:non-scaling-stroke;stroke-linecap:round}
.vm-bld{fill:url(#vm-hatch);stroke:currentColor;stroke-width:.5px;vector-effect:non-scaling-stroke;stroke-linejoin:round}
.vm-sol{fill:currentColor;fill-opacity:.9;stroke:currentColor;stroke-width:.5px;vector-effect:non-scaling-stroke}
.vm-cem{fill:url(#vm-cross);stroke:none}
.vm-grn{fill:url(#vm-grass);stroke:none}
.vm-nm{font-family:var(--f-body,"PT Serif",Georgia,serif);font-style:italic;font-size:88px;fill:currentColor;paint-order:stroke;stroke:var(--vm-paper);stroke-width:18px;stroke-linejoin:round;text-anchor:middle}
.vm-nm.caps{font-style:normal;letter-spacing:.3em;font-size:96px}
.vm-cap{font-family:var(--f-mono,"IBM Plex Mono",monospace);font-size:76px;fill:currentColor;fill-opacity:.75}
.vm-pt .halo{fill:none;stroke:var(--vm-acc);stroke-width:2.4px;vector-effect:non-scaling-stroke}
.vm-pt .dot{fill:var(--vm-acc);stroke:var(--vm-paper);stroke-width:18px;paint-order:stroke}
.vm-pt text{font-family:var(--f-mono,"IBM Plex Mono",monospace);font-weight:600;font-size:84px;fill:var(--vm-paper);text-anchor:middle}
"""
# корень отдельного файла: свои переменные (на сайте они уже есть); :root.vm совпадает только когда svg — корень документа
CSS_STANDALONE = """
:root.vm{--ink:#211b16;--page:#e9e4da;--s1:#c2452a;background:var(--page)}
@media (prefers-color-scheme:dark){:root.vm{--ink:#f0e8d8;--page:#16110e;--s1:#e4664a}.vm-bld,.vm-sol,.vm-shore{opacity:.82}}
"""

DEFS = """<pattern id="vm-hatch" width="19" height="19" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="19" stroke="currentColor" stroke-width="6.6"/></pattern>
<pattern id="vm-cross" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M17 10v14M10 17h14" stroke="currentColor" stroke-width="3.6" fill="none"/></pattern>
<pattern id="vm-grass" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M4 9v-5M15 21v-5M18 7v-4" stroke="currentColor" stroke-width="2.6" fill="none"/></pattern>
<filter id="vm-blur" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="95"/></filter>"""

# имена: из OSM (place=suburb/neighbourhood, waterway=canal, place=island); (текст, долгота, широта, класс, поворот)
LABELS = [
    ("Cannaregio", 12.3235, 45.4455, "caps", 0),
    ("San Marco", 12.3385, 45.4345, "caps", 0),
    ("Dorsoduro", 12.3185, 45.4330, "caps", 0),
    ("Giudecca", 12.3265, 45.4252, "caps", 0),
    ("Canal Grande", 12.3320, 45.4352, "", -50),
    ("San Michele", 12.3466, 45.4437, "", 0),
]
ROSE_LL = (12.3520, 45.4262)     # центр розы ветров (открытая вода Бачино)
ROSE_R = 210
SCALE_M = 500


def rose(cx, cy, r):
    """Роза ветров: четыре длинных луча, четыре коротких, кольцо, N. Половина каждого луча залита, половина в контуре."""
    parts = []
    for ang, rad, w in [(0, r, r * .17), (90, r, r * .17), (180, r, r * .17), (270, r, r * .17),
                        (45, r * .62, r * .1), (135, r * .62, r * .1), (225, r * .62, r * .1), (315, r * .62, r * .1)]:
        a = math.radians(ang)
        tip = (cx + rad * math.sin(a), cy - rad * math.cos(a))
        p1 = (cx + w * math.sin(a - math.pi / 2), cy - w * math.cos(a - math.pi / 2))
        p2 = (cx + w * math.sin(a + math.pi / 2), cy - w * math.cos(a + math.pi / 2))
        parts.append(f'<path d="M{tip[0]:.0f} {tip[1]:.0f}L{p1[0]:.0f} {p1[1]:.0f}L{cx:.0f} {cy:.0f}z" fill="currentColor"/>')
        parts.append(f'<path d="M{tip[0]:.0f} {tip[1]:.0f}L{p2[0]:.0f} {p2[1]:.0f}L{cx:.0f} {cy:.0f}z" fill="none" stroke="currentColor" stroke-width=".8" vector-effect="non-scaling-stroke"/>')
    parts.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*.74:.0f}" fill="none" stroke="currentColor" stroke-width=".8" vector-effect="non-scaling-stroke"/>')
    parts.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*.8:.0f}" fill="none" stroke="currentColor" stroke-width=".5" vector-effect="non-scaling-stroke"/>')
    parts.append(f'<text x="{cx:.0f}" y="{cy - r - 26:.0f}" class="vm-nm" style="stroke-width:0;font-style:normal;font-size:92px">N</text>')
    return '<g class="vm-rose">' + "".join(parts) + "</g>"


def scalebar(x, y, meters=SCALE_M):
    L_ = meters * SCALE
    ticks = "".join(f'<path d="M{x + L_*i/5:.0f} {y}v-22"/>' for i in range(6))
    return (f'<g class="vm-scale" fill="none" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke">'
            f'<path d="M{x} {y}h{L_:.0f}" style="stroke-width:2.4px"/>{ticks}</g>'), L_


def at(lon, lat):
    x, y = proj(lon, lat)
    return to_u(x, y)


def collect_overlay():
    pts = []
    for p in POINTS:
        ux, uy = at(p["lon"], p["lat"])
        p.update(x_u=ux, y_u=uy, x_pct=round(100 * ux / W_U, 3), y_pct=round(100 * uy / H_U, 3))
        pts.append(p)
    labels = []
    for t, lo, la, cls, rot in LABELS:
        x, y = at(lo, la)
        labels.append(dict(text=t, x=x, y=y, cls=cls, rot=rot, x_pct=round(100 * x / W_U, 3), y_pct=round(100 * y / H_U, 3)))
    rx, ry = at(*ROSE_LL)
    sx, sy = round(W_U - 120 - SCALE_M * SCALE), H_U - 110     # линейка — внизу справа, под розой; подпись слева от неё
    return pts, labels, (rx, ry), (sx, sy)


def make_art(layers, rose_xy, scale_xy):
    """Рисунок карты без подписей и точек: вода, суша, дома, кладбище, зелень (с мягким краем), роза и линейка."""
    rip = "".join(f'<path class="vm-rip" style="stroke-opacity:{op}" d="{d}"/>'
                  for d, op in zip(layers["ripples"], [.9, .8, .7, .6, .5, .42, .34, .27, .2, .14]))
    m = 230
    mask = (f'<mask id="vm-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W_U}" height="{H_U}">'
            f'<rect x="{m}" y="{m}" width="{W_U - 2*m}" height="{H_U - 2*m}" fill="#fff" filter="url(#vm-blur)"/></mask>')
    sb, _ = scalebar(*scale_xy)
    return (mask + f'<g mask="url(#vm-fade)"><g>{rip}</g>'
            f'<path class="vm-land" fill-rule="evenodd" d="{layers["land"]}"/>'
            f'<path class="vm-grn" fill-rule="evenodd" d="{layers["grn"]}"/>'
            f'<path class="vm-cem" fill-rule="evenodd" d="{layers["cem"]}"/>'
            f'<path class="vm-bld" fill-rule="evenodd" d="{layers["bld"]}"/>'
            f'<path class="vm-sol" fill-rule="evenodd" d="{layers["sol"]}"/>'
            f'<path class="vm-shore" d="{layers["shore"]}"/></g>'
            + rose(*rose_xy, ROSE_R) + sb)


def main():
    fetch_base()
    t0 = time.time()
    L = load()
    print("loaded", {k: len(v) for k, v in L.items() if isinstance(v, list)}, round(time.time() - t0, 1), "s")
    layers = build_layers(L)
    print("layers", {k: (len(v) if isinstance(v, str) else v) for k, v in layers.items() if k != "ripples"},
          "ripples KB", [round(len(r) / 1024) for r in layers["ripples"]], round(time.time() - t0, 1), "s")
    pts, labels, rose_xy, scale_xy = collect_overlay()
    art = make_art(layers, rose_xy, scale_xy)
    _, sbL = scalebar(*scale_xy)

    # ---- отдельный файл: рисунок + подписи + точки + атрибуция внутри SVG
    lab = "".join(f'<text class="vm-nm {l["cls"]}" x="{l["x"]}" y="{l["y"]}"'
                  + (f' transform="rotate({l["rot"]} {l["x"]} {l["y"]})"' if l["rot"] else "") + f'>{l["text"]}</text>'
                  for l in labels)
    pm = "".join(f'<g class="vm-pt" data-n="{p["n"]}"><circle class="halo" cx="{p["x_u"]}" cy="{p["y_u"]}" r="104"/>'
                 f'<circle class="dot" cx="{p["x_u"]}" cy="{p["y_u"]}" r="64"/>'
                 f'<text x="{p["x_u"]}" y="{p["y_u"] + 29}">{p["n"]}</text></g>' for p in pts)
    cap = (f'<text class="vm-cap" x="{scale_xy[0] - 30:.0f}" y="{scale_xy[1] + 26}" text-anchor="end">{SCALE_M} м</text>'
           f'<text class="vm-cap" x="120" y="{H_U - 84}">© участники OpenStreetMap, ODbL</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="vm" viewBox="0 0 {W_U} {H_U}" role="img" '
           f'aria-label="Карта Венеции: пансион Accademia, могила Бродского на Сан-Микеле, доска на Дзаттере">'
           f'<title>Карта Венеции</title><style>{CSS_STANDALONE}{CSS}</style>'
           f'<defs>{DEFS}</defs>{art}{lab}<g>{pm}</g>{cap}</svg>')
    (HERE / "venice-map.svg").write_text(svg, encoding="utf-8")

    # ---- фрагмент для sketch.html: рисунок отдельно (без текста и точек: они в макете — HTML, чтобы не мельчали)
    (HERE / "map-fragment.svg").write_text(f'<defs>{DEFS}<g id="vm-art">{art}</g></defs>', encoding="utf-8")
    ov = dict(w=W_U, h=H_U, bbox=[LAT_S, LAT_N, LON_W, LON_E], points=pts, labels=labels,
              scale=dict(x_pct=round(100 * scale_xy[0] / W_U, 3), y_pct=round(100 * scale_xy[1] / H_U, 3),
                         w_pct=round(100 * sbL / W_U, 3), meters=SCALE_M))
    (HERE / "points.json").write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding="utf-8")
    print("svg KB", round(len(svg.encode()) / 1024), "fragment KB", round((HERE / "map-fragment.svg").stat().st_size / 1024),
          "viewBox", W_U, H_U, "| W_M,H_M", round(W_M), round(H_M))


if __name__ == "__main__":
    main()
