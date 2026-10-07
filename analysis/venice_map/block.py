"""Блок «карта Венеции» для раздела «Венеция» (вставляется patch_report4.py).

Читает готовые map-fragment.svg и points.json (их пишет build_map.py), только стандартная библиотека.
Рисунок встраивается инлайн, а не через <img>: так он видит переменные цвета страницы и переключатель темы.
Стили лежат в report4.head.html (правила .vm*).

Источники точек:
  1. «Лагуна» (1973), ч. I, строки «пансион "Аккадемиа" вместе со / всей Вселенной плывет к Рождеству»;
     адрес пансиона — OSM node 12778940301 (Pensione Accademia), по совпадению названия.
  2. и 3. ru.wikipedia, «Бродский, Иосиф Александрович»: перезахоронение 21 июня 1997 года в протестантской части
     кладбища Сан-Микеле; мемориальная доска на Дзаттере открыта 21 мая 2009 года, скульптор Георгий Франгулян.
     OSM: могила — node 4824705622, доска — node 5498137523.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

LEGEND = [
    dict(n=1, h="Пансион «Accademia»",
         f="Назван в «Лагуне» (1973): «пансион „Аккадемиа“ вместе со…»",
         s="Бродский, „Лагуна“, 1973 · OSM node 12778940301"),
    dict(n=2, h="Могила на Сан-Микеле",
         f="Перезахоронен 21 июня 1997 года в протестантской части кладбища.",
         s="ru.wikipedia, „Бродский, Иосиф Александрович“ · OSM node 4824705622"),
    dict(n=3, h="Доска на Дзаттере",
         f="Открыта 21 мая 2009 года на набережной Неисцелимых, работа скульптора Георгия Франгуляна.",
         s="ru.wikipedia, „Бродский, Иосиф Александрович“ · OSM node 5498137523"),
]


def venice_map_block():
    ov = json.loads((HERE / "points.json").read_text(encoding="utf-8"))
    frag = (HERE / "map-fragment.svg").read_text(encoding="utf-8")
    w, h = ov["w"], ov["h"]
    lab = "".join(
        f'<span class="vm-l {l["cls"]}" style="left:{l["x_pct"]}%;top:{l["y_pct"]}%'
        + (f';transform:translate(-50%,-50%) rotate({l["rot"]}deg)' if l["rot"] else "") + f'">{l["text"]}</span>'
        for l in ov["labels"])
    mk = "".join(f'<span class="vm-mk" style="left:{p["x_pct"]}%;top:{p["y_pct"]}%" role="img" aria-label="Точка {p["n"]}">{p["n"]}</span>'
                 for p in ov["points"])
    sc = ov["scale"]
    scl = (f'<span class="vm-sc" style="left:{sc["x_pct"] - 1.2:.2f}%;top:{sc["y_pct"]:.2f}%;'
           f'transform:translate(-100%,-50%)">{sc["meters"]} м</span>')
    leg = "".join(f'<li><span class="vm-no">{x["n"]}</span><div><h3>{x["h"]}</h3><p class="f">{x["f"]}</p>'
                  f'<p class="s">{x["s"]}</p></div></li>' for x in LEGEND)
    return f'''<figure class="vm vm-fig">
  <svg class="vm-defs" width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">{frag}</svg>
  <div class="cap"><span class="t">Три места Бродского в Венеции</span><span class="u">1 · 2 · 3 — как в списке под картой</span></div>
  <div class="vm-wrap" style="aspect-ratio:{w} / {h}">
    <svg class="vm" viewBox="0 0 {w} {h}" role="img" aria-label="Карта Венеции: пансион Accademia (1), могила Бродского на Сан-Микеле (2), доска на набережной Дзаттере (3)"><use href="#vm-art"/></svg>
    {lab}{mk}{scl}
  </div>
  <ol class="vm-leg">{leg}</ol>
  <p class="vm-src">Карта: © участники OpenStreetMap, лицензия ODbL. Геометрия упрощена, контуры домов слегка искажены.</p>
</figure>'''


if __name__ == "__main__":
    print(len(venice_map_block()))
