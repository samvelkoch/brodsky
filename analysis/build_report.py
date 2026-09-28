"""Собирает HTML артефакта: подставляет stats.json и explorer.json в report2.template.html."""
import sys
from pathlib import Path
HERE = Path(__file__).parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "brodsky-v-chislah.html"
t = (HERE / "report3.template.html").read_text(encoding="utf-8")
safe = lambda s: s.replace("</", "<\\/")
t = t.replace("/*DATA*/", safe((HERE / "stats.json").read_text(encoding="utf-8")), 1)
import json
ex = json.loads((HERE / "explorer.json").read_text(encoding="utf-8"))
content = set(ex.pop("content_keys"))
# запись индекса: [написание или 0, счёт по периодам, проза, стихотворения, знаменательное 1/0]
ex["lex"] = {k: [v[0] if v[0] != k else 0, v[1], v[2], v[3], 1 if k in content else 0] for k, v in ex["lex"].items()}
t = t.replace("/*EX*/", safe(json.dumps(ex, ensure_ascii=False, separators=(",", ":"))), 1)
vs = json.loads((HERE / "verse.json").read_text(encoding="utf-8"))
vs.pop("poem_feats", None)
st = json.loads((HERE / "style.json").read_text(encoding="utf-8"))
t = t.replace("/*VERSE*/", safe(json.dumps(vs, ensure_ascii=False, separators=(",", ":"))), 1)
t = t.replace("/*STYLE*/", safe(json.dumps(st, ensure_ascii=False, separators=(",", ":"))), 1)
out.write_text(t, encoding="utf-8")
print(out, round(out.stat().st_size / 1024), "KB")
