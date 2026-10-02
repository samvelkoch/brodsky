/* ---------- граф рифм: по словарю рифм, режимы «вокруг слова» и «карта рифм» ----------
   Подключается после основного скрипта отчёта: берёт VS.rhyme_dict, RDN, rdOpen и хелперы графиков
   (el, txt, svg, css, seg, chart, esc, norm, fmt). Панель вставляется сразу под словарём рифм. */
(function () {
  if (typeof VS === 'undefined' || !VS.rhyme_dict) return;
  const host = document.querySelector('#rifma .panel.rhymebox'); if (!host) return;

  // смежность по всем парам словаря, симметрично; вес пары — сколько раз она встретилась
  const ADJ = new Map(), WT = new Map();
  const add = (a, b, n) => { if (a === b) return; if (!ADJ.has(a)) ADJ.set(a, new Map()); const m = ADJ.get(a); m.set(b, Math.max(m.get(b) || 0, n)); };
  for (const k in VS.rhyme_dict) for (const [w, n] of VS.rhyme_dict[k]) { add(k, w, n); add(w, k, n); }
  ADJ.forEach((m, k) => { let s = 0; m.forEach(v => { s += v; }); WT.set(k, s); });
  const nDict = Object.keys(VS.rhyme_dict).length;
  const plr = (n, one, few, many) => { const a = n % 10, b = n % 100; return a === 1 && b !== 11 ? one : (a >= 2 && a <= 4 && (b < 12 || b > 14) ? few : many); };

  const panel = document.createElement('div'); panel.className = 'panel'; panel.id = 'rg-panel';
  panel.innerHTML = '<div class="cap"><span class="t">Граф рифм</span><span class="u" id="rg-u"></span></div>' +
    '<div class="ctrl"><div id="rg-mode"></div></div><div class="chart" id="c-rgraph"></div>' +
    '<div class="legend" id="rg-legend"></div><p class="muted" id="rg-note" style="font-size:14px;margin:8px 0 0"></p>';
  host.insertAdjacentElement('afterend', panel);

  let mode = 'ego';
  const cur = RDN[norm((document.querySelector('#rd-input') || {}).value || '')];
  let center = cur || (RDN['ночь'] ? 'ночь' : Object.keys(VS.rhyme_dict)[0]);

  function withEdges(nodes) {
    const N = [...nodes.keys()], idx = new Map(N.map((w, i) => [w, i])), E = [];
    N.forEach((a, i) => { const m = ADJ.get(a); if (m) m.forEach((n, b) => { const j = idx.get(b); if (j !== undefined && j > i) E.push([i, j, n]); }); });
    return { N, ring: N.map(w => nodes.get(w)), E };
  }
  const byW = m => [...(m || new Map())].sort((a, b) => b[1] - a[1] || (WT.get(b[0]) || 0) - (WT.get(a[0]) || 0));
  function egoGraph(c, narrow) {
    const n1 = narrow ? 12 : 22, n2 = narrow ? 1 : 3, cap = narrow ? 32 : 68, nodes = new Map([[c, 0]]);
    const p1 = byW(ADJ.get(c)).slice(0, n1); p1.forEach(([w]) => nodes.set(w, 1));
    for (const [w] of p1) for (const [x] of byW(ADJ.get(w)).filter(([x]) => !nodes.has(x)).slice(0, n2)) { if (nodes.size >= cap) break; nodes.set(x, 2); }
    return withEdges(nodes);
  }
  // карта: главные рифменные узлы (самые частые слова в рифме) и их ближайшие пары
  function mapGraph(narrow) {
    const hubs = [...WT].sort((a, b) => b[1] - a[1]).slice(0, narrow ? 10 : 24).map(x => x[0]), nodes = new Map();
    hubs.forEach(h => nodes.set(h, 3));
    hubs.forEach(h => byW(ADJ.get(h)).slice(0, narrow ? 4 : 5).forEach(([w]) => { if (!nodes.has(w)) nodes.set(w, 3); }));
    return withEdges(nodes);
  }
  // «семьи» рифм: взвешенное распространение меток, детерминированное
  function families(G) {
    const n = G.N.length, lab = G.N.map((_, i) => i), nb = G.N.map(() => []);
    G.E.forEach(([i, j, w]) => { nb[i].push([j, w]); nb[j].push([i, w]); });
    const order = [...Array(n).keys()].sort((a, b) => WT.get(G.N[b]) - WT.get(G.N[a]));
    for (let it = 0; it < 30; it++) {
      let ch = 0;
      for (const i of order) {
        if (!nb[i].length) continue; const sc = new Map(); nb[i].forEach(([j, w]) => sc.set(lab[j], (sc.get(lab[j]) || 0) + w));
        let best = lab[i], bv = -1; sc.forEach((v, l) => { if (v > bv || (v === bv && l < best)) { bv = v; best = l; } });
        if (best !== lab[i]) { lab[i] = best; ch++; }
      }
      if (!ch) break;
    }
    const cnt = new Map(); lab.forEach(l => cnt.set(l, (cnt.get(l) || 0) + 1));
    const rank = [...cnt].filter(x => x[1] >= 3).sort((a, b) => b[1] - a[1]).slice(0, 8).map(x => x[0]);
    return lab.map(l => rank.indexOf(l));
  }
  // раскладка: каждое связное гнездо раскладывается отдельно (Фрюхтерман — Рейнгольд, детерминированно),
  // затем гнёзда укладываются рядами в рамку с наибольшим масштабом, при котором всё помещается
  function fr(G, ids) {
    const n = ids.length, loc = new Map(ids.map((g, i) => [g, i])), k = 40;
    const E = G.E.filter(([i, j]) => loc.has(i) && loc.has(j)).map(([i, j, w]) => [loc.get(i), loc.get(j), w]);
    const P = ids.map((g, i) => { const r = G.ring[g] === 0 ? 0 : 30 + 9 * Math.sqrt(i + 1), a = i * 2.39996; return [Math.cos(a) * r, Math.sin(a) * r]; });
    let t = 40;
    for (let it = 0; it < (n > 2 ? 320 : 0); it++) {
      const D = P.map(() => [0, 0]);
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        let dx = P[i][0] - P[j][0], dy = P[i][1] - P[j][1]; const d = Math.max(Math.hypot(dx, dy), 0.5), f = k * k / d; dx /= d; dy /= d;
        D[i][0] += dx * f; D[i][1] += dy * f; D[j][0] -= dx * f; D[j][1] -= dy * f;
      }
      for (const [i, j, wt] of E) {
        let dx = P[i][0] - P[j][0], dy = P[i][1] - P[j][1]; const d = Math.max(Math.hypot(dx, dy), 0.5), f = d * d / k * (1 + Math.log1p(wt) * 0.2); dx /= d; dy /= d;
        D[i][0] -= dx * f; D[i][1] -= dy * f; D[j][0] += dx * f; D[j][1] += dy * f;
      }
      for (let i = 0; i < n; i++) {
        D[i][0] -= P[i][0] * 0.04; D[i][1] -= P[i][1] * 0.06;
        const d = Math.hypot(D[i][0], D[i][1]) || 0.01, m = Math.min(d, t);
        P[i][0] += D[i][0] / d * m; P[i][1] += D[i][1] / d * m;
      }
      t = Math.max(0.5, t * 0.985);
    }
    if (n === 2) { P[0] = [0, 0]; P[1] = [k * 1.4, 0]; }
    const xs = P.map(p => p[0]), ys = P.map(p => p[1]);
    return { ids, P, x0: Math.min(...xs), y0: Math.min(...ys), bw: Math.max(...xs) - Math.min(...xs), bh: Math.max(...ys) - Math.min(...ys) };
  }
  function layout(G, w, h) {
    const n = G.N.length, par = [...Array(n).keys()], root = x => par[x] === x ? x : (par[x] = root(par[x]));
    G.E.forEach(([i, j]) => { par[root(i)] = root(j); });
    const groups = new Map(); for (let i = 0; i < n; i++) { const r = root(i); if (!groups.has(r)) groups.set(r, []); groups.get(r).push(i); }
    const C = [...groups.values()].map(ids => fr(G, ids)).sort((a, b) => b.ids.length - a.ids.length);
    const mx = 70, my = 30, top = 22, avail = h - top - 6;
    const shelf = s => {
      const rows = []; let row = { items: [], w: 0, h: 0 };
      for (const c of C) {
        const cw = c.bw * s + mx, ch = c.bh * s + my;
        if (cw > w) return null;
        if (row.w + cw > w && row.items.length) { rows.push(row); row = { items: [], w: 0, h: 0 }; }
        row.items.push([c, cw, ch]); row.w += cw; row.h = Math.max(row.h, ch);
      }
      rows.push(row); return { rows, h: rows.reduce((a, r) => a + r.h, 0) };
    };
    let lo = 0.05, hi = 3, best = null;
    for (let it = 0; it < 28; it++) { const s = (lo + hi) / 2, r = shelf(s); if (r && r.h <= avail) { best = [s, r]; lo = s; } else hi = s; }
    if (!best) best = [lo, shelf(lo)];
    const [s, pack] = best, P = new Array(n);
    let y = top + (avail - pack.h) / 2;
    for (const row of pack.rows) {
      let x = (w - row.w) / 2;
      for (const [c, cw, ch] of row.items) {
        const ox = x + (cw - c.bw * s) / 2, oy = y + (row.h - c.bh * s) / 2 + my * 0.3;
        c.ids.forEach((g, i) => { P[g] = [ox + (c.P[i][0] - c.x0) * s, oy + (c.P[i][1] - c.y0) * s]; });
        x += cw;
      }
      y += row.h;
    }
    return P;
  }

  function focus(word) { if (RDN[norm(word)]) rdOpen(word); else { center = word; mode = 'ego'; setMode(); draw(); } }
  function draw() {
    const box = document.querySelector('#c-rgraph'), narrow = box.clientWidth < 600, h = narrow ? 440 : (mode === 'map' ? 620 : 540);
    const G = mode === 'ego' ? egoGraph(center, narrow) : mapGraph(narrow);
    const [s, w] = svg(box, h); s.setAttribute('role', 'group'); s.setAttribute('aria-label', mode === 'ego' ? `Граф рифм вокруг слова «${center}»` : 'Карта рифм Бродского');
    const P = layout(G, w, h), fam = mode === 'map' ? families(G) : null;
    const maxE = Math.max(1, ...G.E.map(e => e[2])), maxW = Math.max(1, ...G.N.map(x => WT.get(x) || 1));
    const gE = el('g', {}, s), gN = el('g', {}, s), nb = G.N.map(() => new Set());
    const lines = G.E.map(([i, j, n]) => { nb[i].add(j); nb[j].add(i);
      return el('line', { x1: P[i][0], y1: P[i][1], x2: P[j][0], y2: P[j][1], stroke: css('--axis'), 'stroke-width': (0.7 + 2.6 * Math.sqrt(n / maxE)).toFixed(2), 'stroke-opacity': 0.8,
        'data-tip': `${esc(G.N[i])} — ${esc(G.N[j])}: ${fmt(n)} ${plr(n, 'раз', 'раза', 'раз')}` }, gE); });
    const famCol = f => f >= 0 ? css('--g' + (f + 1)) : css('--neutral-bar');
    const labelled = new Set(mode === 'map' ? G.N.map((x, i) => i).sort((a, b) => WT.get(G.N[b]) - WT.get(G.N[a])).slice(0, narrow ? 24 : 160) : G.N.map((x, i) => i));
    const groups = G.N.map((word, i) => {
      const ring = G.ring[i], deg = ADJ.get(word) ? ADJ.get(word).size : 0, tot = WT.get(word) || 0;
      const g = el('g', { class: 'clickable', tabindex: 0, role: 'button', 'aria-label': `${word}: ${deg} ${plr(deg, 'партнёр', 'партнёра', 'партнёров')}`,
        'data-tip': `<b>${esc(word)}</b><br>${fmt(deg)} ${plr(deg, 'слово', 'слова', 'слов')} в рифму, ${fmt(tot)} ${plr(tot, 'рифма', 'рифмы', 'рифм')}` }, gN);
      const r = ring === 0 ? 10 : mode === 'map' ? 3 + 7 * Math.sqrt(tot / maxW) : ring === 1 ? 6 : 4;
      const fill = ring === 0 ? css('--mark') : mode === 'map' ? famCol(fam[i]) : ring === 1 ? css('--s1') : css('--neutral-bar');
      el('circle', { cx: P[i][0], cy: P[i][1], r: r.toFixed(1), fill, stroke: css('--surface'), 'stroke-width': 1.5 }, g);
      if (labelled.has(i)) {
        const fs = ring === 0 ? 19 : mode === 'map' ? (tot > maxW * 0.45 ? 14 : 12) : ring === 1 ? 14 : 12;
        txt(g, P[i][0], P[i][1] - r - 4, word, { 'text-anchor': 'middle', 'font-size': fs, 'font-weight': ring === 0 ? 700 : 400,
          fill: ring === 2 ? css('--muted') : css('--ink'), stroke: css('--surface'), 'stroke-width': 3.5, 'paint-order': 'stroke', 'stroke-linejoin': 'round',
          style: `font-family:var(--f-body)` });
      }
      g.addEventListener('click', () => focus(word));
      g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); focus(word); } });
      g.addEventListener('pointerenter', () => hilite(i)); g.addEventListener('pointerleave', () => hilite(-1));
      g.addEventListener('focus', () => hilite(i)); g.addEventListener('blur', () => hilite(-1));
      return g;
    });
    function hilite(i) {
      lines.forEach((ln, e) => { const [a, b] = G.E[e]; ln.setAttribute('stroke-opacity', i < 0 || a === i || b === i ? 0.8 : 0.08); ln.setAttribute('stroke', i >= 0 && (a === i || b === i) ? css('--mark') : css('--axis')); });
      groups.forEach((g, j) => { g.style.opacity = i < 0 || j === i || nb[i].has(j) ? '' : 0.25; });
    }
    const nE = G.E.length, u = document.querySelector('#rg-u'), lg = document.querySelector('#rg-legend'), note = document.querySelector('#rg-note');
    if (mode === 'ego') {
      const deg = ADJ.get(center) ? ADJ.get(center).size : 0;
      u.textContent = `«${center}»: ${fmt(deg)} ${plr(deg, 'слово', 'слова', 'слов')} в рифму`;
      lg.innerHTML = `<span><i style="background:${css('--mark')}"></i>слово в центре</span><span><i style="background:${css('--s1')}"></i>рифмуется с ним</span><span><i style="background:${css('--neutral-bar')}"></i>рифмы его рифм</span>`;
      note.textContent = 'Линия — пара рифм в стихах Бродского: чем толще, тем чаще. Нажмите на слово, чтобы поставить его в центр; словарь выше откроет его рифмы.';
    } else {
      u.textContent = `${fmt(G.N.length)} самых рифмуемых слов, ${fmt(nE)} ${plr(nE, 'пара', 'пары', 'пар')}`;
      const fams = []; fam.forEach((f, i) => { if (f >= 0) (fams[f] = fams[f] || []).push(i); });
      lg.innerHTML = fams.map((ids, f) => ids ? `<span><i style="background:${famCol(f)}"></i>${ids.sort((a, b) => WT.get(G.N[b]) - WT.get(G.N[a])).slice(0, 3).map(i => esc(G.N[i])).join(', ')}</span>` : '').join('');
      note.textContent = `Цвет — «семья»: слова, которые рифмуются в основном друг с другом. Размер точки — сколько раз слово стоит в рифме. Данные — словарь рифм: ${nDict >= VS.rhyme_dict_size ? 'полный, ' + fmt(nDict) + ' ' + plr(nDict, 'слово', 'слова', 'слов') + ' с рифмой' : fmt(nDict) + ' самых рифмуемых слов из ' + fmt(VS.rhyme_dict_size)}, и их пары. Нажмите на слово, чтобы увидеть его окружение.`;
    }
  }
  function setMode() { seg(document.querySelector('#rg-mode'), [['ego', 'Вокруг слова'], ['map', 'Карта рифм']], mode, v => { mode = v; draw(); }); }
  setMode();

  // словарь рифм и граф показывают одно слово
  const rdOpen0 = rdOpen;
  rdOpen = function (word) { rdOpen0(word); const k = RDN[norm(word)]; if (k && k !== center) { center = k; if (mode !== 'ego') { mode = 'ego'; setMode(); } draw(); } };
  chart(draw, document.querySelector('#c-rgraph'));
})();
