#!/usr/bin/env python3
"""Поиск кандидатов фото на Wikimedia Commons (только API метаданных; кэш в cache/commons_*.json).
Для каждого места: поисковые запросы + категории -> файлы с лицензией CC0/PD/CC BY/CC BY-SA, шириной >= 1000 px.
Запуск: ../.venv/bin/python photo_search.py [--sheets]   (--sheets: контактные листы в cache/sheets/ для просмотра глазами)"""
import json, re, sys, time, html, urllib.parse, urllib.request
from pathlib import Path
HERE = Path(__file__).parent; C = HERE / "cache"; C.mkdir(exist_ok=True)
UA = "naprosvet-sketch/0.1 (+https://github.com/samvelkoch/naprosvet)"
API = "https://commons.wikimedia.org/w/api.php"
# id места -> (поисковые запросы, категории)
SEARCH = {
 1: (["Pensione Accademia Venice", "Villa Maravegie Venezia", "Fondamenta Bollani Venezia", "Rio de San Trovaso Accademia", "Rio Terà Antonio Foscarini Venezia", "Accademia Dorsoduro Rio de la Toletta", "Fondamenta Bollani Rio Terà Foscarini", "Campo della Carità Venezia"], ["Category:Rio de San Trovaso"]),
 2: (["Antica Locanda Montin", "Locanda Montin Venezia", "Fondamenta di Borgo Venezia", "Rio di San Trovaso Venezia", "Fondamenta Priuli Venezia Dorsoduro", "Ponte Foscari Venezia Dorsoduro"], ["Category:Fondamenta di Borgo (Venice)", "Category:Rio de San Trovaso"]),
 3: (["Gelateria Nico Venezia", "Gelateria Nico Zattere", "Zattere al Ponte Lungo"], []),
 4: (["Fondamenta Zattere ai Incurabili", "Zattere Venezia Incurabili", "Ospedale degli Incurabili Venezia"], ["Category:Fondamenta delle Zattere"]),
 5: (["Rio de la Verona Venezia", "Fondamenta de la Verona Venezia", "Rio Menuo o de la Verona"], ["Category:Rio de la Verona"]),
 6: (["Harry's Bar Venezia"], ["Category:Harry's Bar (Venice)"]),
 7: (["Caffè Florian Venezia"], ["Category:Caffè Florian"]),
 8: (["Salizada San Provolo Venezia", "Ponte San Provolo Venezia", "Trattoria alla Rivetta"], ["Category:Campo San Provolo"]),
 9: (["Arsenale di Venezia Porta Magna", "Arsenale Venezia mura nord", "Rio dell'Arsenale"], ["Category:Arsenale di Venezia"]),
 10: (["Campo Santi Giovanni e Paolo Venezia", "Ospedale Civile Venezia facciata", "Basilica dei Santi Giovanni e Paolo facade"], ["Category:Campo Santi Giovanni e Paolo (Venice)"]),
 11: (["Cimitero di San Michele Venezia", "Joseph Brodsky grave Venice", "tomba Brodskij San Michele"], ["Category:Cimitero di San Michele"]),
}
OK_LIC = re.compile(r"^(CC0|CC BY( |-)|CC BY-SA|Public domain|PD|Attribution|No restrictions)", re.I)

def call(params, key):
    f = C / f"commons_{key}.json"
    if f.exists(): return json.loads(f.read_text())
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60))
    f.write_text(json.dumps(d, ensure_ascii=False)); time.sleep(1.1); return d

def clean(s): return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def info_params():
    return dict(prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=640, iiextmetadatafilter="Artist|LicenseShortName|LicenseUrl|ImageDescription|Credit|Restrictions")

def collect(pid):
    qs, cats = SEARCH[pid]; files = {}
    def take(d):
        for p in (d.get("query", {}).get("pages", {}) or {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii or ii.get("mime") not in ("image/jpeg", "image/png"): continue
            md = ii.get("extmetadata", {}); lic = clean(md.get("LicenseShortName", {}).get("value"))
            if not OK_LIC.search(lic) or md.get("Restrictions", {}).get("value"): continue
            if ii["width"] < 1000: continue
            files[p["title"]] = dict(title=p["title"], w=ii["width"], h=ii["height"], thumb=ii["thumburl"], url=ii["url"], page=ii["descriptionurl"],
                                     author=clean(md.get("Artist", {}).get("value")), license=lic, license_url=md.get("LicenseUrl", {}).get("value", ""),
                                     desc=clean(md.get("ImageDescription", {}).get("value"))[:160])
    for i, q in enumerate(qs):
        take(call(dict(action="query", generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6, gsrlimit=25, **info_params()), f"s{pid}_{i}"))
    for i, c in enumerate(cats):
        take(call(dict(action="query", generator="categorymembers", gcmtitle=c, gcmtype="file", gcmlimit=60, **info_params()), f"c{pid}_{i}"))
    return list(files.values())

if __name__ == "__main__":
    allc = {}
    for pid in SEARCH:
        allc[pid] = collect(pid); print(pid, len(allc[pid]), "файлов с допустимой лицензией")
    (C / "commons_all.json").write_text(json.dumps(allc, ensure_ascii=False, indent=1))
