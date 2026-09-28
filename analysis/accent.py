"""Расстановка ударений во всех строках стихотворений (ruaccent, CPU).
Запуск в отдельном окружении: .venv-accent/bin/python accent.py
Вход: poem_lines.json. Выход: accented.json — {pid: [строка с «+» перед ударной гласной | "" для границы строфы]}.
Прогресс сохраняется каждые 500 строк; повторный запуск продолжает с места остановки.
"""
import json
import time
from pathlib import Path

from ruaccent import RUAccent

HERE = Path(__file__).parent
SRC, OUT = HERE / "poem_lines.json", HERE / "accented.json"
poems = json.loads(SRC.read_text(encoding="utf-8"))
done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

acc = RUAccent()
acc.load(omograph_model_size="turbo3.1", use_dictionary=True, tiny_mode=False)

total = sum(len(p["lines"]) for p in poems)
n, t0, since = sum(len(v) for v in done.values()), time.time(), 0
for p in poems:
    key = str(p["pid"])
    if key in done and len(done[key]) == len(p["lines"]):
        continue
    res = []
    for line in p["lines"]:
        res.append(acc.process_all(line) if line else "")
        n += 1; since += 1
    done[key] = res
    if since >= 500:
        OUT.write_text(json.dumps(done, ensure_ascii=False), encoding="utf-8"); since = 0
        el = time.time() - t0
        print(f"{n}/{total} lines, {el/60:.1f} min", flush=True)
OUT.write_text(json.dumps(done, ensure_ascii=False), encoding="utf-8")
print("DONE", n, "lines", flush=True)
