"""Файлы «живого портрета»: подпись, биография, финальный ролик.

    python sync_assets.py bio             # подпись и биография из naprosvet-book -> signature.svg, bio.json (лежат в репозитории)
    python sync_assets.py final           # lp/final/ -> final/ (portrait.mp4, portrait.webm, постеры); без полного набора падает
    python sync_assets.py deploy          # final/portrait.{mp4,webm} -> docs/ и naprosvet-site/brodsky/ (рядом со страницами)
    python sync_assets.py dev DEST        # ЗАГЛУШКИ для разработки в DEST (вне репозитория): ролик из review/p2-5s.mp4, постер из lp/src_A.png

Генератор (portrait_block.py) берёт постер и проверяет ролик только в final/. Без final/ сборка падает; чтобы собрать
страницу на заглушке, нужно явно задать LIVE_PORTRAIT_DEV=DEST (страница при этом не годится для публикации).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent
WORK = REPO.parent
BOOK = WORK / "naprosvet-book"
LIVE = WORK / "naprosvet" / "live"
LP_FINAL = LIVE / "lp" / "final"
FINAL = HERE / "final"
NEED = ["portrait.mp4", "portrait.webm", "portrait-poster.jpg", "portrait-poster.webp"]


def die(msg):
    sys.exit("ОШИБКА: " + msg)


def cmd_bio(_):
    cfg = json.load(open(BOOK / "config" / "brodsky.json", encoding="utf-8"))
    bio = cfg["bio"]
    keep = {"kicker": bio["kicker"], "title": bio["title"], "paragraphs": bio["paragraphs"]}
    (HERE / "bio.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    shutil.copyfile(BOOK / "template" / "brand" / "signature.svg", HERE / "signature.svg")
    print("bio.json:", len(keep["paragraphs"]), "абзацев; signature.svg скопирована")


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=codec_name,width,height,duration", "-of", "json", str(path)],
                         capture_output=True, text=True)
    if out.returncode:
        die(f"ffprobe не открыл {path}: {out.stderr.strip()}")
    return json.loads(out.stdout)["streams"][0]


def cmd_final(_):
    missing = [n for n in NEED if not (LP_FINAL / n).is_file() or (LP_FINAL / n).stat().st_size == 0]
    if missing:
        die(f"нет финального ролика: в {LP_FINAL} не хватает {', '.join(missing)}. "
            "Заглушки вместо него не берутся; для разработки есть LIVE_PORTRAIT_DEV (см. docstring).")
    mp4, webm = probe(LP_FINAL / "portrait.mp4"), probe(LP_FINAL / "portrait.webm")
    if mp4["codec_name"] != "h264" or webm["codec_name"] != "vp9":
        die(f"ожидались h264 и vp9, получено {mp4['codec_name']} и {webm['codec_name']}")
    FINAL.mkdir(exist_ok=True)
    for n in NEED:
        shutil.copyfile(LP_FINAL / n, FINAL / n)
    print("final/ обновлён:", {n: (FINAL / n).stat().st_size for n in NEED})
    print("mp4", mp4["width"], "x", mp4["height"], mp4["duration"], "с; webm", webm["width"], "x", webm["height"], webm["duration"], "с")


def cmd_deploy(a):
    missing = [n for n in NEED if not (FINAL / n).is_file()]
    if missing:
        die(f"в {FINAL} не хватает {', '.join(missing)}: сначала `sync_assets.py final`")
    for d in (Path(a.docs), Path(a.site)):
        d.mkdir(parents=True, exist_ok=True)
        for n in ("portrait.mp4", "portrait.webm"):
            shutil.copyfile(FINAL / n, d / n)
        print("ролик ->", d)


def cmd_dev(a):
    dest = Path(a.dest).resolve()
    if REPO in dest.parents or dest == REPO:
        die("заглушки нельзя класть внутрь репозитория")
    dest.mkdir(parents=True, exist_ok=True)
    src_mp4 = LIVE / "review" / "p2-5s.mp4"
    shutil.copyfile(src_mp4, dest / "portrait.mp4")
    # webm-заглушку здесь собрать нечем (в локальном ffmpeg нет libvpx), поэтому в режиме dev подключается только mp4
    from PIL import Image
    im = Image.open(LIVE / "lp" / "src_A.png").convert("RGB").resize((640, 800), Image.LANCZOS)
    im.save(dest / "portrait-poster.webp", quality=66, method=6)
    im.save(dest / "portrait-poster.jpg", quality=85, optimize=True)
    print("ЗАГЛУШКИ в", dest, {p.name: p.stat().st_size for p in sorted(dest.iterdir())})
    print("для сборки: export LIVE_PORTRAIT_DEV=" + str(dest))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="c", required=True)
    sp.add_parser("bio").set_defaults(f=cmd_bio)
    sp.add_parser("final").set_defaults(f=cmd_final)
    d = sp.add_parser("deploy"); d.set_defaults(f=cmd_deploy)
    d.add_argument("--docs", default=str(REPO / "docs"))
    d.add_argument("--site", default=str(WORK / "naprosvet-site" / "brodsky"))
    v = sp.add_parser("dev"); v.set_defaults(f=cmd_dev); v.add_argument("dest")
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
