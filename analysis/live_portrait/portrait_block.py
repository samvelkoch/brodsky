"""Блоки «живого портрета»: портрет на первом экране и карточка биографии в «Хронологии».

Вставляются patch_report4.py. Читают только то, что лежит в репозитории:
  signature.svg  — подпись (public domain, Wikimedia Commons, векторизована);
  bio.json       — биография, дословно из naprosvet-book/config/brodsky.json (обновляется `sync_assets.py bio`);
  final/         — финальный ролик и постер (кладёт `sync_assets.py final`).
Стили — в report4.head.html (правила .lp*, .bio*), поведение — portrait.js.

Без final/ сборка падает. Для разработки на заглушках нужно явно задать LIVE_PORTRAIT_DEV=<папка с заглушками>
(см. `sync_assets.py dev`): тогда в stderr печатается предупреждение, а страница не годится для публикации.
"""
import base64
import html
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
FINAL = HERE / "final"
DEV = os.environ.get("LIVE_PORTRAIT_DEV")
DATES = "1940, Ленинград — 1996, Нью-Йорк"
SOURCE = "по статье „Бродский, Иосиф Александрович“, ru.wikipedia"


def _assets():
    """Папка с постером и роликом: final/ или явно заданная папка заглушек."""
    if DEV:
        d = Path(DEV)
        print(f"ВНИМАНИЕ: LIVE_PORTRAIT_DEV={d}: сборка на ЗАГЛУШКАХ, публиковать нельзя", file=sys.stderr)
        return d, True
    need = ["portrait.mp4", "portrait.webm", "portrait-poster.webp", "portrait-poster.jpg"]
    miss = [n for n in need if not (FINAL / n).is_file() or (FINAL / n).stat().st_size == 0]
    if miss:
        sys.exit(f"ОШИБКА: нет финального ролика, в {FINAL} не хватает: {', '.join(miss)}. "
                 "Выполните `python live_portrait/sync_assets.py final` (читает naprosvet/live/lp/final/); "
                 "заглушки молча не подставляются.")
    return FINAL, False


def poster_data_uri(folder):
    for name, mime in (("portrait-poster.webp", "image/webp"), ("portrait-poster.jpg", "image/jpeg")):
        f = folder / name
        if f.is_file():
            return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode("ascii")
    sys.exit(f"ОШИБКА: в {folder} нет постера portrait-poster.webp / .jpg")


def signature_svg():
    svg = (HERE / "signature.svg").read_text(encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    d = re.search(r' d="([^"]+)"', svg).group(1)
    return (f'<svg class="lp-sig" viewBox="{vb}" role="img" aria-label="Подпись Иосифа Бродского">'
            f'<path fill="currentColor" fill-rule="evenodd" d="{d}"/></svg>')


def portrait_block():
    folder, dev = _assets()
    poster = poster_data_uri(folder)
    sources = []
    if (folder / "portrait.webm").is_file():
        sources.append('<source src="portrait.webm" type="video/webm; codecs=vp9">')
    elif not dev:
        sys.exit("ОШИБКА: нет portrait.webm")
    sources.append('<source src="portrait.mp4" type="video/mp4">')
    # ролик лежит в <template>: пока скрипт его не достанет, браузер ничего не качает
    # (при prefers-reduced-motion скрипт его не достаёт, и остаётся только постер)
    video = ('<template id="lp-video"><video class="lp-video" muted playsinline preload="auto" aria-hidden="true" tabindex="-1">'
             + "".join(sources) + "</video></template>")
    return f'''<aside class="hero-portrait">
        <figure class="lp" id="lp">
          <div class="lp-sheet"><div class="lp-art"><img class="lp-poster" src="{poster}" width="640" height="800" alt="Иосиф Бродский, портрет, рисунок">{video}</div></div>
        </figure>
        {signature_svg()}
        <p class="lp-dates">{DATES}</p>
      </aside>'''


def bio_card():
    bio = json.load(open(HERE / "bio.json", encoding="utf-8"))
    paras = "\n".join(f"    <p>{html.escape(t, quote=False)}</p>" for t in bio["paragraphs"])
    return f'''<aside class="bio" aria-labelledby="bio-t">
    <div class="bio-k">{html.escape(bio["kicker"])}</div>
    <h3 class="bio-t" id="bio-t">{html.escape(bio["title"])}</h3>
{paras}
    <p class="bio-src">Источник: {SOURCE}</p>
  </aside>'''
