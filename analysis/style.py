"""Диахрония стиля и карта словаря. Пишет analysis/style.json.

Вход: explorer.json (метрики стихотворений), verse.json (размер, рифма, фраза по стихотворениям),
poem_lines.json (очищенные строки), corpus.pkl (леммы стихов и прозы для векторов слов).
"""
import json
import math
import pickle
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pymorphy3

# В основном окружении scikit-learn/gensim/umap несовместимы с numpy 2.x — нужные алгоритмы ниже на чистом numpy.


def kmeans(X, k, n_init=30, iters=300, seed=42):
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(n_init):
        cen = [X[rng.integers(len(X))]]
        for _ in range(1, k):                                   # k-means++
            d = np.min(((X[:, None] - np.array(cen)[None]) ** 2).sum(-1), 1)
            cen.append(X[rng.choice(len(X), p=d / d.sum())])
        cen = np.array(cen)
        for _ in range(iters):
            lab = ((X[:, None] - cen[None]) ** 2).sum(-1).argmin(1)
            new = np.array([X[lab == c].mean(0) if (lab == c).any() else cen[c] for c in range(k)])
            if np.allclose(new, cen):
                break
            cen = new
        inertia = ((X - cen[lab]) ** 2).sum()
        if best is None or inertia < best[0]:
            best = (inertia, lab, cen)
    return best[1], best[2]


def ari(a, b):
    a, b = np.asarray(a), np.asarray(b)
    ct = np.array([[((a == i) & (b == j)).sum() for j in np.unique(b)] for i in np.unique(a)])
    c2 = lambda x: x * (x - 1) / 2
    s_ij, s_a, s_b, n = c2(ct).sum(), c2(ct.sum(1)).sum(), c2(ct.sum(0)).sum(), c2(len(a))
    exp = s_a * s_b / n
    return (s_ij - exp) / (0.5 * (s_a + s_b) - exp)


def rsvd(M, k, it=5, seed=0):
    rng = np.random.default_rng(seed)
    Q = np.linalg.qr(M @ rng.standard_normal((M.shape[1], k + 10)))[0]
    for _ in range(it):
        Q = np.linalg.qr(M @ (M.T @ Q))[0]
    U, S, _ = np.linalg.svd(Q.T @ M, full_matrices=False)
    return (Q @ U)[:, :k], S[:k]


def tsne(X, perplexity=15, iters=1200, seed=42):
    """Компактный t-SNE (van der Maaten, 2008) для нескольких сотен точек."""
    rng = np.random.default_rng(seed)
    n = len(X)
    D = ((X[:, None] - X[None]) ** 2).sum(-1)
    P = np.zeros((n, n))
    target = np.log(perplexity)
    for i in range(n):
        lo, hi, beta = 1e-20, 1e20, 1.0
        di = np.delete(D[i], i)
        for _ in range(60):
            pi = np.exp(-di * beta); sp = pi.sum() + 1e-12
            H = np.log(sp) + beta * (di * pi).sum() / sp
            if abs(H - target) < 1e-5:
                break
            if H > target:
                lo = beta; beta = beta * 2 if hi == 1e20 else (beta + hi) / 2
            else:
                hi = beta; beta = (beta + lo) / 2
        P[i, np.arange(n) != i] = pi / sp
    P = (P + P.T) / (2 * n); P = np.maximum(P, 1e-12)
    Y = rng.standard_normal((n, 2)) * 1e-4
    vel, gains = np.zeros_like(Y), np.ones_like(Y)
    for t in range(iters):
        ex = 12.0 if t < 250 else 1.0
        num = 1 / (1 + ((Y[:, None] - Y[None]) ** 2).sum(-1)); np.fill_diagonal(num, 0)
        Q = np.maximum(num / num.sum(), 1e-12)
        G = 4 * (((ex * P - Q) * num)[:, :, None] * (Y[:, None] - Y[None])).sum(1)
        mom = 0.5 if t < 250 else 0.8
        gains = (gains + 0.2) * ((G > 0) != (vel > 0)) + gains * 0.8 * ((G > 0) == (vel > 0))
        gains = np.maximum(gains, 0.01)
        vel = mom * vel - 200 * gains * G
        Y = Y + vel; Y -= Y.mean(0)
    return Y

HERE = Path(__file__).parent
EX = json.loads((HERE / "explorer.json").read_text(encoding="utf-8"))
VS = json.loads((HERE / "verse.json").read_text(encoding="utf-8"))
PL = json.loads((HERE / "poem_lines.json").read_text(encoding="utf-8"))
PERIODS = EX["periods"]
morph = pymorphy3.MorphAnalyzer()
PF = {int(k): v for k, v in VS["poem_feats"].items()}
CLASSIC = {"ямб", "хорей", "дактиль", "амфибрахий", "анапест"}
TOK = re.compile(r"[а-яё]+")
I_FORMS = {"я", "меня", "мне", "мной", "мною"}

# ───────────── признаки по годам ─────────────
by_year = {}
for i, p in enumerate(EX["poems"]):
    if not p["y"] or i not in PF:
        continue
    by_year.setdefault(p["y"], []).append(i)
MIN_POEMS = 6
years = sorted(y for y, ids in by_year.items() if len(ids) >= MIN_POEMS)

FEATS = [("med", "длина строки"), ("classic", "доля классических размеров"), ("free", "доля свободного стиха"),
         ("exact", "доля точных рифм"), ("unrh", "доля строк без рифмы"), ("fem", "доля женских окончаний"),
         ("open", "строки без знака в конце"), ("fe", "строка на служебном слове"), ("nv", "существительных на глагол"),
         ("sent", "длина фразы в строках"), ("cross", "фраза через границу строфы"), ("ego", "«я» на 1000 слов")]


def year_vector(ids):
    P = [EX["poems"][i] for i in ids]
    n = np.array([p["n"] for p in P], float)
    syl = [s for p in P for s in p["syl"] if s]
    f = {}
    f["med"] = float(np.median(syl))
    f["classic"] = sum(p["n"] for i, p in zip(ids, P) if PF[i]["meter"] in CLASSIC) / n.sum()
    f["free"] = sum(p["n"] for i, p in zip(ids, P) if PF[i]["meter"] == "свободный") / n.sum()
    for k in ("exact", "unrh", "fem"):
        f[k] = float(np.average([PF[i][k] for i in ids], weights=n))
    f["open"] = float(np.average([p["open"] for p in P], weights=n)) / 100
    f["fe"] = float(np.average([p["fe"] for p in P], weights=n)) / 100
    nvs = [(p["nv"], p["w"]) for p in P if p["nv"] is not None and p["w"] >= 40]
    f["nv"] = float(np.average([a for a, _ in nvs], weights=[b for _, b in nvs])) if nvs else float("nan")
    ss = [(PF[i].get("sent"), p["n"]) for i, p in zip(ids, P) if PF[i].get("sent")]
    f["sent"] = float(np.average([a for a, _ in ss], weights=[b for _, b in ss]))
    cs = [(PF[i].get("cross"), p["n"]) for i, p in zip(ids, P) if PF[i].get("cross") is not None]
    f["cross"] = float(np.average([a for a, _ in cs], weights=[b for _, b in cs]))
    toks = [w for i in ids for l in PL[i]["lines"] for w in TOK.findall(l.lower())]
    f["ego"] = 1000 * sum(w in I_FORMS for w in toks) / max(1, len(toks))
    return f, len(toks)


rows, ntok = [], {}
for y in years:
    f, nt = year_vector(by_year[y])
    rows.append(f); ntok[y] = nt
M = np.array([[r[k] for k, _ in FEATS] for r in rows])
col_mean = np.nanmean(M, 0)
M = np.where(np.isnan(M), col_mean, M)
Z = (M - M.mean(0)) / M.std(0)
D_form = np.sqrt(((Z[:, None, :] - Z[None, :, :]) ** 2).mean(-1))


# ───────────── словарная дистанция: Burrows' Delta по 100 самым частым словам ─────────────
year_tok = {y: [w for i in by_year[y] for l in PL[i]["lines"] for w in TOK.findall(l.lower())] for y in years}
mfw = [w for w, _ in Counter(w for y in years for w in year_tok[y]).most_common(100)]
F = np.array([[Counter(year_tok[y])[w] / len(year_tok[y]) for w in mfw] for y in years])
FZ = (F - F.mean(0)) / F.std(0)
D_words = np.abs(FZ[:, None, :] - FZ[None, :, :]).mean(-1)


# ───────────── поиск переломов: бинарная сегментация по сумме квадратов отклонений ─────────────
def segment(X, max_cp=4, min_len=2):
    """Жадно добавляет точки перелома, каждый раз выбирая разрез, сильнее всего уменьшающий разброс внутри отрезков.
    Возвращает [(индекс начала нового отрезка, доля объяснённого разброса)]."""
    def sse(a, b):
        seg = X[a:b]
        return ((seg - seg.mean(0)) ** 2).sum()
    total = sse(0, len(X))
    cps, out = [0, len(X)], []
    for _ in range(max_cp):
        best = None
        for a, b in zip(cps, cps[1:]):
            base = sse(a, b)
            for c in range(a + min_len, b - min_len + 1):
                gain = base - sse(a, c) - sse(c, b)
                if best is None or gain > best[0]:
                    best = (gain, c)
        if not best or best[0] <= 0:
            break
        cps = sorted(cps + [best[1]])
        out.append((best[1], round(best[0] / total, 3)))
    return out


cp_form = [(years[i], g) for i, g in segment(Z)]
cp_words = [(years[i], g) for i, g in segment(FZ)]

# ───────────── группы стихотворений без учёта дат ─────────────
feat_keys = ["med", "open", "fe", "exact", "unrh", "fem", "nv", "sent", "cross", "classic", "free"]
Xp, lab, meta = [], [], []
for i, p in enumerate(EX["poems"]):
    if i not in PF or p["n"] < 12 or p["p"] >= len(PERIODS) or PF[i].get("sent") is None:
        continue
    v = [p["med"], p["open"] / 100, p["fe"] / 100, PF[i]["exact"], PF[i]["unrh"], PF[i]["fem"],
         min(p["nv"] if p["nv"] is not None else 2.5, 8), min(PF[i]["sent"], 15), PF[i]["cross"],
         1.0 if PF[i]["meter"] in CLASSIC else 0.0, 1.0 if PF[i]["meter"] == "свободный" else 0.0]
    Xp.append(v); lab.append(p["p"]); meta.append(i)
Xp = np.array(Xp)
Xs = (Xp - Xp.mean(0)) / Xp.std(0)
km_labels, km_centers = kmeans(Xs, len(PERIODS))
ari_v = ari(lab, km_labels)
rng = np.random.default_rng(0)
ari_null = [ari(rng.permutation(lab), km_labels) for _ in range(200)]
cross = [[int(((km_labels == c) & (np.array(lab) == p)).sum()) for p in range(len(PERIODS))] for c in range(len(PERIODS))]
NAMES = {"med": ("длинная строка", "короткая строка"), "open": ("много строк без знака", "строки замкнуты знаком"),
         "fe": ("строка рвётся на служебном слове", "строка не рвётся на служебном слове"),
         "exact": ("точная рифма", "мало точных рифм"), "unrh": ("много строк без рифмы", "почти всё зарифмовано"),
         "fem": ("много женских окончаний", "мужские окончания"), "nv": ("много существительных", "много глаголов"),
         "sent": ("длинные фразы", "короткие фразы"), "cross": ("фраза перетекает через строфу", "фраза умещается в строфе"),
         "classic": ("классический размер", "неклассический размер"), "free": ("свободный стих", "размер держится")}
clusters = []
for c in range(len(PERIODS)):
    cen = km_centers[c]
    order = np.argsort(-np.abs(cen))[:3]
    desc = [NAMES[feat_keys[j]][0 if cen[j] > 0 else 1] for j in order]
    ys = [EX["poems"][meta[k]]["y"] for k in range(len(meta)) if km_labels[k] == c and EX["poems"][meta[k]]["y"]]
    clusters.append({"n": int((km_labels == c).sum()), "desc": desc, "year_med": float(np.median(ys)) if ys else None,
                     "by_period": cross[c]})
order_c = sorted(range(len(clusters)), key=lambda c: clusters[c]["year_med"] or 0)

# ───────────── векторы слов на корпусе Бродского ─────────────
C = pickle.load(open(HERE / "corpus.pkl", "rb"))
own = [o for o in C if o["author"] == "own" and o["lang"] == "ru"]
KEEP_POS = {"NOUN", "ADJF", "ADJS", "VERB", "INFN", "PRTF", "PRTS", "GRND"}  # без наречий-связок
PRONOUNISH = {"весь", "свой", "сам", "самый", "наш", "ваш", "мой", "твой", "этот", "тот", "такой", "который", "какой",
              "каждый", "никакой", "другой", "иной", "всякий", "чей", "один", "быть", "мочь", "стать", "самое"}
sents = []
for o in own:
    lem = [l.lower().replace("ё", "е") for l, pos in zip(o["lemmas"], o["pos"])
           if pos in KEEP_POS and l.lower() not in PRONOUNISH]
    for k in range(0, len(lem), 12):
        chunk = lem[k:k + 24]
        if len(chunk) >= 4:
            sents.append(chunk)
lex = EX["lex"]
freq = Counter(w for ch in sents for w in ch)
vocab = [w for w, c in freq.most_common() if c >= 8][:6000]
vi = {w: i for i, w in enumerate(vocab)}
Cm = np.zeros((len(vocab), len(vocab)), np.float32)
for ch in sents:
    ids = [vi[w] for w in ch if w in vi]
    for x, i in enumerate(ids):
        for j in ids[max(0, x - 5):x]:
            Cm[i, j] += 1; Cm[j, i] += 1
ctx = Cm.sum(0) ** 0.75
pmi = np.log(np.maximum(Cm * ctx.sum() / (Cm.sum(1, keepdims=True) * ctx[None, :] + 1e-9), 1e-9))
ppmi = np.maximum(pmi, 0).astype(np.float32)
U, Sv = rsvd(ppmi, 100)
W = U * np.sqrt(Sv)
W /= np.linalg.norm(W, axis=1, keepdims=True) + 1e-9
content = [k for k in EX.get("content_keys", lex) if k in vi]
cp = sorted(content, key=lambda k: -sum(lex[k][1]))
top_words = cp[:260]
neighbors = {}
for k in cp[:3000]:
    sims = W @ W[vi[k]]
    neighbors[k] = [vocab[j] for j in np.argsort(-sims)[1:30] if vocab[j] in lex and vocab[j] != k][:6]
Vt = np.array([W[vi[k]] for k in top_words])
emb = tsne(Vt)
wl, _ = kmeans(Vt, 8, n_init=15)
wmap = [{"w": lex[k][0] or k, "k": k, "x": round(float(x), 3), "y": round(float(y), 3), "c": int(c),
         "n": int(sum(lex[k][1]))} for k, (x, y), c in zip(top_words, emb, wl)]
groups = []
for c in range(8):
    ws = sorted([m for m in wmap if m["c"] == c], key=lambda m: -m["n"])
    groups.append([m["w"] for m in ws[:4]])

S = {
    "years": years, "features": FEATS, "year_values": [[round(r[k], 4) for k, _ in FEATS] for r in rows],
    "year_poems": [len(by_year[y]) for y in years], "year_tokens": [ntok[y] for y in years],
    "dist_form": np.round(D_form, 3).tolist(), "dist_words": np.round(D_words, 3).tolist(),
    "cp_form": cp_form, "cp_words": cp_words, "mfw": mfw[:30],
    "clusters": [clusters[c] for c in order_c], "ari": round(float(ari_v), 3),
    "ari_null95": round(float(np.percentile(ari_null, 95)), 3), "cluster_n": len(meta),
    "wmap": wmap, "wgroups": groups, "neighbors": neighbors,
}
json.dump(S, open(HERE / "style.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("years", years)
print("cp form", cp_form); print("cp words", cp_words)
print("ARI", S["ari"], "null95", S["ari_null95"], "n", len(meta))
for c in S["clusters"]:
    print(c["year_med"], c["n"], c["desc"], c["by_period"])
print("word groups", groups)
print("neighbors время:", neighbors.get("время"), "| стекло:", neighbors.get("стекло"))
