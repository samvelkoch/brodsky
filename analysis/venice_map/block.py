"""Блок «Места Бродского в Венеции» для раздела «Венеция» (вставляется patch_report4.py).

Читает готовые map-fragment.svg и points.json (их пишет build_map.py), places.json и photos/N.webp (11 мест из статьи
1600.venezia.it, выбранные фото с Wikimedia Commons), только стандартная библиотека.
Рисунок встраивается инлайн, а не через <img>: так он видит переменные цвета страницы и переключатель темы.
Фото — серые webp (дуотон), в страницу встроены как data-URI и окрашиваются стилем из --ink и --page (в тёмной теме
цвета меняются местами). Стили лежат в report4.head.html (правила .vm* и .ph), поведение всплывашки — places.js.

Источник сведений о местах один: статья «Iosif Aleksandrovich Brodsky — Здесь у него были любимые места и свои маршруты»,
1600.venezia.it, 15.06.2021. Координаты — OpenStreetMap (osm у каждого места в places.json); у мест, помеченных
«приблизительно», точка стоит на ближайшем ориентире OSM.
"""
import base64
import html
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
ARTICLE = "https://1600.venezia.it/ru/articolo/iosif-aleksandrovich-brodsky-zdes-nego-byli-lyubimye-mesta-svoi-marshruty"
# близкие пары на узкой карте: маркер сдвигается (в % ширины карты), настоящая точка остаётся маленькой меткой на конце линии
OFFSETS = {2: (-2.4, -1.2), 6: (-1.8, 1.6), 7: (1.5, -1.0)}
LABEL_MOVE = {"San Marco": (51.5, 47.5)}      # подпись района не должна лежать под точками 5-7
esc = html.escape


def _photo_uri(rel):
    return "data:image/webp;base64," + base64.b64encode((HERE / rel).read_bytes()).decode()


def venice_map_block():
    ov = json.loads((HERE / "points.json").read_text(encoding="utf-8"))
    places = json.loads((HERE / "places.json").read_text(encoding="utf-8"))["places"]
    frag = (HERE / "map-fragment.svg").read_text(encoding="utf-8")
    js = (HERE / "places.js").read_text(encoding="utf-8")
    w, h = ov["w"], ov["h"]
    byn = {p["n"]: p for p in ov["points"]}
    lab = []
    for l in ov["labels"]:
        x, y = LABEL_MOVE.get(l["text"], (l["x_pct"], l["y_pct"]))
        lab.append(f'<span class="vm-l {l["cls"]}" style="left:{x}%;top:{y}%'
                   + (f';transform:translate(-50%,-50%) rotate({l["rot"]}deg)' if l["rot"] else "") + f'">{l["text"]}</span>')
    pts, leads, leg = [], [], []
    for p in places:
        n = p["n"]
        x, y = byn[n]["x_pct"], byn[n]["y_pct"]
        assert (round(x, 2), round(y, 2)) == (round(p["map"]["x_pct"], 2), round(p["map"]["y_pct"], 2)), f"точка {n}: places.json и points.json разошлись"
        ox, oy = OFFSETS.get(n, (0, 0))
        left, top = (f"calc({x}% + {ox}cqw)", f"calc({y}% + {oy}cqw)") if (ox or oy) else (f"{x}%", f"{y}%")
        if ox or oy:
            leads.append(f'<span class="vm-tip" style="left:{x}%;top:{y}%"></span>'
                         f'<span class="vm-ld" style="left:{x}%;top:{y}%;width:{math.hypot(ox, oy):.2f}cqw;transform:rotate({math.degrees(math.atan2(oy, ox)):.1f}deg)"></span>')
        ph = p["photo"]
        credit = f'Фото: {ph["author"]}, {ph["license"]}'
        pts.append(f'<span class="vm-pt" style="left:{left};top:{top}"><button type="button" class="vm-mk" aria-describedby="vmp{n}" aria-label="{n}. {esc(p["name_ru"])}">{n}</button>'
                   f'<span class="vm-pop" id="vmp{n}" role="tooltip"><span class="ph" style="--src:url({_photo_uri(ph["file"])})"></span>'
                   f'<b>{esc(p["name_ru"])}</b><i>{esc(p["popup_line"])}</i><em>{esc(credit)}</em></span></span>')
        ap = f' <span class="ap">(приблизительно)</span>' if p["approx"] else ""
        lic = f'<a href="{esc(ph["license_url"])}">{esc(ph["license"])}</a>' if ph["license_url"] else esc(ph["license"])
        leg.append(f'<li><span class="vm-no">{n}</span><div><h3>{esc(p["name_ru"])}{ap}</h3><p class="f">{esc(p["popup_line"])}</p>'
                   f'<p class="s">статья 1600.venezia.it · OSM {p["osm"].replace("/", " ")}</p>'
                   f'<p class="s ph-cr">Фото: {esc(ph["author"])}, {lic}, <a href="{esc(ph["page"])}">Wikimedia Commons</a></p></div></li>')
    sc = ov["scale"]
    scl = (f'<span class="vm-sc" style="left:{sc["x_pct"] - 1.2:.2f}%;top:{sc["y_pct"]:.2f}%;'
           f'transform:translate(-100%,-50%)">{sc["meters"]} м</span>')
    n_all = len(places)
    return f'''<figure class="vm vm-fig">
  <svg class="vm-defs" width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">{frag}</svg>
  <div class="cap"><span class="t">Места Бродского в Венеции</span><span class="u">номера — как в списке под картой</span></div>
  <div class="vm-wrap" style="aspect-ratio:{w} / {h}">
    <svg class="vm" viewBox="0 0 {w} {h}" role="img" aria-label="Карта Венеции: {n_all} мест, связанных с Бродским, номера 1–{n_all}"><use href="#vm-art"/></svg>
    {"".join(lab)}{scl}{"".join(leads)}{"".join(pts)}
  </div>
  <ol class="vm-leg">{"".join(leg)}</ol>
  <p class="vm-src">Сведения о местах: <a href="{ARTICLE}">статья 1600.venezia.it</a> (15 июня 2021). Карта: © участники OpenStreetMap, лицензия ODbL. Геометрия упрощена, контуры домов слегка искажены.</p>
  <script>
{js}</script>
</figure>'''


if __name__ == "__main__":
    print(len(venice_map_block()))
