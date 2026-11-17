"use strict";
// kperf viewer: one kernel per bundle. Lanes are stacked-share strips (each 0.25 us column split by phase kind),
// folded over every launch; the DRAM panel shares the same x axis. Labels from the bundle are untrusted: textContent only.

const $ = (s) => document.querySelector(s);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const fmt = (x, d = 1) => (x == null || isNaN(x) ? "–" : Number(x).toFixed(d));
const G = 104;  // left gutter (lane names), shared by timeline and DRAM panels
const RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"];

const S = { list: [], kviewPort: 8137, b: null, sel: "typical", metric: "finish", hoverT: null, A: null, streams: null, xmax: 1 };

// ---------- colors
const dark = () => !document.documentElement.classList.contains("light");
function kindColor(k) { return k < 8 ? css(`--k${k}`) : css("--idle"); }
function hex2rgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; }
function seq(t) {  // sequential blue; near-zero recedes into the surface in both themes
  const ramp = dark() ? [...RAMP].reverse() : RAMP;
  t = Math.max(0, Math.min(1, t)) * (ramp.length - 1);
  const i = Math.min(ramp.length - 2, Math.floor(t)), f = t - i, a = hex2rgb(ramp[i]), b = hex2rgb(ramp[i + 1]);
  return `rgb(${a.map((v, j) => Math.round(v + (b[j] - v) * f)).join(",")})`;
}
function scaleBar(node, lo, hi, unit) {
  node.replaceChildren();
  const bar = el("span", "bar");
  const stops = Array.from({ length: 9 }, (_, i) => seq(i / 8)).join(",");
  bar.style.background = `linear-gradient(to right, ${stops})`;
  node.append(el("span", null, `${fmt(lo)}`), bar, el("span", null, `${fmt(hi)} ${unit}`));
}

// ---------- canvas
function canvas(cv, h) {
  const dpr = window.devicePixelRatio || 1, w = cv.clientWidth;
  cv.style.height = h + "px"; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
  const ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.font = `11px ${css("--mono")}`; ctx.textBaseline = "middle";
  return { ctx, w, h };
}
const X = (t, w) => G + (t / S.xmax) * (w - G - 10);
const T = (x, w) => ((x - G) / (w - G - 10)) * S.xmax;
function niceStep(range, n) { const r = range / n, p = 10 ** Math.floor(Math.log10(r)); return [1, 2, 5, 10].map((m) => m * p).find((s) => s >= r); }
function xAxis(ctx, w, y) {
  const step = niceStep(S.xmax, 10);
  ctx.fillStyle = css("--dim"); ctx.strokeStyle = css("--grid"); ctx.textAlign = "center";
  for (let t = 0; t <= S.xmax + 1e-9; t += step) {
    const x = X(t, w); ctx.fillText(`${+t.toFixed(2)}`, x, y + 9);
    ctx.beginPath(); ctx.moveTo(x + 0.5, y - 3); ctx.lineTo(x + 0.5, y); ctx.stroke();
  }
  ctx.textAlign = "left"; ctx.fillText("µs", 4, y + 9);
}

// ---------- tooltip
function tip(ev, head, rows) {
  const t = $("#tip"); t.replaceChildren(el("div", "h", head));
  for (const [color, value, label] of rows) {
    const r = el("div", "r"), ln = el("span", "ln"); ln.style.background = color;
    r.append(ln, el("b", null, value), el("span", null, label)); t.append(r);
  }
  t.hidden = false;
  const x = Math.min(ev.clientX + 14, innerWidth - t.offsetWidth - 8), y = Math.min(ev.clientY + 14, innerHeight - t.offsetHeight - 8);
  t.style.left = x + "px"; t.style.top = y + "px";
}
const untip = () => { $("#tip").hidden = true; };

// ---------- data
async function api(path) { const r = await fetch(path); if (!r.ok) throw new Error(await r.text()); return r.json(); }
// A bundle (kperf/bundle.py): "KPRF" | u32 header length | header JSON | arrays. The folded samples are three columns
// S.A.{bin,label,count}, sorted by core, lane, bin, count descending; a stream [start, end) is one (core or "typical", lane).
const TYPED = { u1: Uint8Array, u2: Uint16Array, u4: Uint32Array };
async function fetchBundle(name) {
  const r = await fetch(`/api/bundle?name=${encodeURIComponent(name)}`); if (!r.ok) throw new Error(await r.text());
  const buf = await r.arrayBuffer(), dv = new DataView(buf);
  if (new TextDecoder().decode(new Uint8Array(buf, 0, 4)) !== "KPRF") throw new Error(`${name}: not a kperf bundle`);
  const n = dv.getUint32(4, true), b = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 8, n))), base = 8 + n;
  b.A = Object.fromEntries(Object.entries(b.arrays).map(([k, [dt, off, len]]) => [k, new TYPED[dt](buf, base + off, len)]));
  b.streamIndex = new Map(b.streams.map(([ck, lane, s, e]) => [`${ck}|${lane}`, [s, e]]));
  return b;
}
function stream(sel, lane) { return S.streams.get(`${sel}|${lane}`) || [0, 0]; }
function eachBin([s, e], fn) {  // fn(bin, i, j): rows [i, j) of the stream fall in that bin
  const B = S.A.bin;
  for (let i = s, j; i < e; i = j) { for (j = i + 1; j < e && B[j] === B[i];) j++; fn(B[i], i, j); }
}
function pairsAt([s, e], bin) {  // [[label, count], ...] of one bin, largest first; null if none
  const B = S.A.bin; let lo = s, hi = e;
  while (lo < hi) { const m = (lo + hi) >> 1; if (B[m] < bin) lo = m + 1; else hi = m; }
  const out = []; for (let i = lo; i < e && B[i] === bin; i++) out.push([S.A.label[i], S.A.count[i]]);
  return out.length ? out : null;
}
function prepare(b) {
  const fin = Object.values(b.core_stats).map((c) => c.finish);
  let last = 0; for (const lane of b.lanes) { const [s, e] = stream("typical", lane); if (e > s) last = Math.max(last, S.A.bin[e - 1]); }
  S.xmax = Math.max(b.launch.p90, Math.max(...fin), (last + 1) * b.bin_us) * 1.02;
  const ck = Object.keys(b.core_stats);
  S.slow = ck.reduce((a, c) => (b.core_stats[c].finish > b.core_stats[a].finish ? c : a), ck[0]);
  S.fast = ck.reduce((a, c) => (b.core_stats[c].finish < b.core_stats[a].finish ? c : a), ck[0]);
}
function laneShare(sel, lane, kinds) {  // share of samples in lane whose label kind is in kinds
  const [s, e] = stream(sel, lane), { label, count } = S.A; let hit = 0, tot = 0;
  for (let i = s; i < e; i++) { tot += count[i]; if (kinds.includes(S.b.labels[label[i]].kind)) hit += count[i]; }
  return tot ? hit / tot : null;
}
const METRICS = {
  finish: { name: "finish time (µs)", unit: "µs", get: (c) => S.b.core_stats[c]?.finish },
  start: { name: "first RISC start (µs)", unit: "µs", get: (c) => S.b.core_stats[c]?.start },
  brisc_dram: { name: "BRISC: waiting on DRAM/NoC (%)", unit: "%", get: (c) => 100 * laneShare(c, "brisc", [1]) },
  trisc0_cb: { name: "TRISC0: waiting on input CB (%)", unit: "%", get: (c) => 100 * laneShare(c, "trisc0", [2]) },
  t1_math: { name: "T1 math: stalled on math (%)", unit: "%", get: (c) => 100 * laneShare(c, "T1 math", [7]) },
  t2_stall: { name: "T2 pack: stalled (%)", unit: "%", get: (c) => 100 * laneShare(c, "T2 pack", [6, 7]) },
  epilogue: { name: "last RISC end − next RISC end (µs)", unit: "µs", get: (c) => {
    const r = Object.values(S.b.core_stats[c]?.roles || {}).map((v) => v[1]).sort((a, z) => z - a); return r.length > 1 ? r[0] - r[1] : null; } },
};

// ---------- DRAM ports: one row per physical tile (bank, port), NoC0 + NoC1 counters summed
function portRows(b) {
  if (!b.dram.ports) return null;
  const rows = {};
  b.dram.port_meta.forEach((m, j) => {
    const k = `${m.tile[0]},${m.tile[1]}`;
    (rows[k] ||= { key: k, bank: m.bank, port: m.port, cols: [null, null] }).cols[m.noc] = j;
  });
  return Object.values(rows).sort((a, z) => a.bank - z.bank || a.port - z.port);
}
function portMean(b, r, a, z, noc) {  // mean GB/s of one tile over bins [a, z); noc null = both
  const js = noc == null ? r.cols : [r.cols[noc]];
  let s = 0, n = 0;
  for (const row of b.dram.ports.slice(a, z)) { s += js.reduce((t, j) => t + (j == null ? 0 : row[j]), 0); n++; }
  return n ? s / n : 0;
}

// ---------- header
function renderStats() {
  const b = S.b, s = $("#stats"); s.replaceChildren();
  const n = Math.round(b.launch.median / b.dram_bin_us), tot = b.dram.total.slice(0, n);
  const mean = tot.reduce((a, x) => a + x, 0) / Math.max(1, tot.length);
  const dramLoss = b.findings.find((f) => f.kind === "dram" && f.est_us != null);
  const tiles = [[`${fmt(b.launch.median, 2)} µs`, `median launch (p10 ${fmt(b.launch.p10)} · p90 ${fmt(b.launch.p90)})`],
    [`${b.cores.length}`, `cores × ${b.launches} launches`],
    [`${fmt(mean, 0)} GB/s`, `DRAM read, ${fmt(100 * mean / b.pin_gbs, 0)}% of pin rate`],
    [dramLoss ? `${fmt(dramLoss.est_us)} µs` : "–", "DRAM below steady state"],
    [`${(b.quality.samples / 1e3).toFixed(0)}k`, `samples, sweep ${fmt(b.quality.sweep_us)} µs${b.quality.pc_launches == null ? "" : `, from ${b.quality.pc_launches} of ${b.launches} launches`}`]];
  for (const [v, l] of tiles) { const d = el("div", "stat"); d.append(el("b", null, v), el("span", null, l)); s.append(d); }
}

// ---------- chip map: the physical NoC grid (17 x 12). On a full 14-column p150a the Tensix coordinates used by the
// runtime are physical. DRAM tiles sit in columns 0 and 9, three NoC ports per controller (bank); per
// boop-docs/measurements/dram-traffic-patterns.md, bank b's ports are rows DRAM_ROWS[b % 4] of column b < 4 ? 0 : 9.
const DRAM_ROWS = [[0, 1, 11], [2, 10, 3], [9, 4, 8], [5, 7, 6]];
const ARC = "8,0";
function renderMap() {
  const b = S.b, cv = $("#map"), m = METRICS[S.metric];
  const COLS = 17, ROWS = 12, w = cv.clientWidth, cell = Math.min(30, (w - 22) / COLS), h = cell * ROWS + 18;
  const { ctx } = canvas(cv, h);
  const kernel = new Set(b.cores.map((c) => c.join(","))), obs = new Set(b.grid.observers.map((c) => c.join(",")));
  const workers = new Set(b.grid.workers.map((c) => c.join(",")));
  const vals = b.cores.map((c) => m.get(c.join(","))).filter((v) => v != null && !isNaN(v));
  const lo = Math.min(...vals), hi = Math.max(...vals);
  scaleBar($("#map-scale"), lo, hi, m.unit);
  S.mapHit = [];
  const at = (x, y) => [22 + x * cell, 16 + y * cell, cell - 2];
  const small = (t, x, y, color) => { ctx.fillStyle = color; ctx.font = `9px ${css("--mono")}`; ctx.fillText(t, x, y); ctx.font = `11px ${css("--mono")}`; };
  ctx.textAlign = "center"; ctx.fillStyle = css("--dim");
  for (let x = 0; x < COLS; x++) ctx.fillText(x, 22 + x * cell + cell / 2, 7);
  for (let y = 0; y < ROWS; y++) ctx.fillText(y, 9, 16 + y * cell + cell / 2);
  // DRAM tiles: colored by their controller's mean read GB/s over the launch (per-controller scale)
  const n = Math.round(b.launch.median / b.dram_bin_us), bankMean = [];
  for (let k = 0; k < 8; k++) { const r = b.dram.banks.slice(0, n).map((row) => row[k]); bankMean.push(r.reduce((a, x) => a + x, 0) / Math.max(1, r.length)); }
  const dramAt = {}, pr = portRows(b), pmap = {};
  for (let bank = 0; bank < 8; bank++) DRAM_ROWS[bank % 4].forEach((row, port) => { dramAt[`${bank < 4 ? 0 : 9},${row}`] = [bank, port]; });
  if (pr) for (const r of pr) pmap[r.key] = portMean(b, r, 0, n);
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) {
    const k = `${x},${y}`, [cx, cy, s] = at(x, y);
    if (dramAt[k]) {
      const [bank, port] = dramAt[k], v = pr ? pmap[k] : bankMean[bank], t = v / 64.3;
      if (pr && v < 1) { ctx.strokeStyle = css("--dim"); ctx.setLineDash([2, 2]); ctx.beginPath(); ctx.roundRect(cx + 0.5, cy + 0.5, s - 1, s - 1, 3); ctx.stroke(); ctx.setLineDash([]); ctx.fillStyle = css("--dim"); }
      else { ctx.fillStyle = seq(t); ctx.beginPath(); ctx.roundRect(cx, cy, s, s, 3); ctx.fill(); ctx.fillStyle = (t > 0.55) === dark() ? "#0b0b0b" : "#ffffff"; }
      ctx.fillText(`D${bank}`, cx + s / 2, cy + s / 2);
      S.mapHit.push({ bank, port, tile: k, x: cx, y: cy, s, v });
    } else if (kernel.has(k)) {
      const v = m.get(k); ctx.fillStyle = v == null || isNaN(v) ? css("--idle") : seq(hi > lo ? (v - lo) / (hi - lo) : 0.5);
      ctx.beginPath(); ctx.roundRect(cx, cy, s, s, 3); ctx.fill();
      S.mapHit.push({ k, x: cx, y: cy, s, v });
    } else if (workers.has(k)) {
      ctx.strokeStyle = css("--line"); ctx.beginPath(); ctx.roundRect(cx + 0.5, cy + 0.5, s - 1, s - 1, 3); ctx.stroke();
      if (obs.has(k)) { ctx.fillStyle = css("--text"); ctx.fillText("◦", cx + s / 2, cy + s / 2); }
      if (k === b.grid.cq.join(",")) small("cq", cx + s / 2, cy + s / 2, css("--faint"));
      if (k === b.grid.dma.join(",")) small("dma", cx + s / 2, cy + s / 2, css("--faint"));
    } else {  // not a Tensix or DRAM tile (Ethernet, ARC, PCIe, ...): drawn as a faint slot
      ctx.fillStyle = css("--line-soft"); ctx.beginPath(); ctx.roundRect(cx + 3, cy + 3, s - 6, s - 6, 2); ctx.fill();
      if (k === ARC) small("arc", cx + s / 2, cy + s / 2, css("--dim"));
    }
    if (k === S.sel) { ctx.strokeStyle = css("--accent"); ctx.lineWidth = 2; ctx.beginPath(); ctx.roundRect(cx - 1, cy - 1, s + 2, s + 2, 4); ctx.stroke(); ctx.lineWidth = 1; }
  }
}
function mapEvent(ev, click) {
  const r = $("#map").getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top;
  const h = S.mapHit.find((c) => x >= c.x && x <= c.x + c.s && y >= c.y && y <= c.y + (c.sh || c.s));
  if (!h) return untip();
  if (h.bank != null && portRows(S.b)) {
    const b = S.b, n = Math.round(b.launch.median / b.dram_bin_us), q = Math.max(1, Math.floor(n / 4)), r = portRows(b).find((x) => x.key === h.tile);
    const row = (label, a, z) => { const n0 = portMean(b, r, a, z, 0), n1 = portMean(b, r, a, z, 1); return [seq((n0 + n1) / 64.3), fmt(n0 + n1, 0), `${label}: NoC0 ${fmt(n0, 0)} + NoC1 ${fmt(n1, 0)}`]; };
    return tip(ev, `DRAM tile ${h.tile}: bank ${h.bank}, port ${h.port} of 3 · read GB/s through this port`,
      [row("whole launch", 0, n), row("first 25%", 0, q), row("middle 50%", q, n - q), row("last 25%", n - q, n)]);
  }
  if (h.bank != null) {
    const b = S.b, n = Math.round(b.launch.median / b.dram_bin_us), q = Math.max(1, Math.floor(n / 4));
    const mean = (a, z) => { const v = b.dram.banks.slice(a, z).map((r) => r[h.bank]); return v.reduce((s, x) => s + x, 0) / Math.max(1, v.length); };
    return tip(ev, `DRAM tile ${h.tile}: bank ${h.bank}, port ${h.port} of 3 · controller read GB/s`, [[seq(mean(0, q) / 64.3), fmt(mean(0, q), 0), "first 25% of the launch"],
      [seq(mean(q, n - q) / 64.3), fmt(mean(q, n - q), 0), "middle 50%"], [seq(mean(n - q, n) / 64.3), fmt(mean(n - q, n), 0), "last 25%"]]);
  }
  if (click) { S.sel = h.k; renderAllSel(); return; }
  const cs = S.b.core_stats[h.k];
  tip(ev, `core ${h.k}`, [[css("--accent"), fmt(h.v, 2), METRICS[S.metric].name],
    ...Object.entries(cs?.roles || {}).map(([r, [s, e]]) => [css("--dim"), fmt(e, 2), `${r} ends (started ${fmt(s, 2)} µs)`])]);
}

// ---------- findings
function renderFindings() {
  const ol = $("#findings"); ol.replaceChildren();
  const order = { dram: 0, balance: 1, tail: 2, pipeline: 3 };
  for (const f of [...S.b.findings].sort((a, z) => (order[a.kind] - order[z.kind]) || ((z.est_us || 0) - (a.est_us || 0)))) {
    const li = el("li"), t = el("div", "t"); t.append(el("span", "tag", f.kind), document.createTextNode(f.title));
    if (f.est_us != null) { t.append(document.createTextNode(" ")); t.append(el("span", "cost", `≈ ${fmt(f.est_us)} µs/launch`)); }
    li.append(t, el("div", "d", f.detail)); ol.append(li);
  }
}

// ---------- timeline
const LANE_H = 20, LANE_GAP = 2;
function renderPick() {
  const p = $("#pick"); p.replaceChildren();
  const opts = [["typical", `typical (all ${S.b.cores.length})`], [S.slow, `slowest ${S.slow}`], [S.fast, `fastest ${S.fast}`]];
  if (!opts.some(([k]) => k === S.sel)) opts.push([S.sel, `core ${S.sel}`]);
  for (const [k, label] of opts) {
    const bt = el("button", null, label); bt.setAttribute("role", "tab"); bt.setAttribute("aria-selected", String(k === S.sel));
    bt.onclick = () => { S.sel = k; renderAllSel(); }; p.append(bt);
  }
  const lg = $("#legend"); lg.replaceChildren();
  [...S.b.kinds.map((n, i) => [i, n]), [8, "idle / firmware"]].forEach(([i, n]) => {
    const k = el("span", "key"), sw = el("span", "sw"); sw.style.background = kindColor(i); k.append(sw, document.createTextNode(n)); lg.append(k);
  });
  const k = el("span", "key"), dash = el("span", "dash"); k.append(dash, document.createTextNode("median launch end")); lg.append(k);
  if (S.sel !== "typical") { const k2 = el("span", "key"), tick = el("span", "tick"); k2.append(tick, document.createTextNode(`core ${S.sel}: each RISC's measured start / end`)); lg.append(k2); }
}
function renderTimeline() {
  const b = S.b, lanes = b.lanes, { label, count } = S.A, cv = $("#tl");
  const { ctx, w, h } = canvas(cv, lanes.length * (LANE_H + LANE_GAP) + 26);
  const minN = S.sel === "typical" ? 6 : 2;
  lanes.forEach((lane, li) => {
    const y0 = li * (LANE_H + LANE_GAP);
    ctx.fillStyle = css("--dim"); ctx.textAlign = "left"; ctx.fillText(lane, 4, y0 + LANE_H / 2);
    ctx.fillStyle = css("--raise"); ctx.fillRect(G, y0, w - G - 10, LANE_H);
    const byKind = new Array(9);
    eachBin(stream(S.sel, lane), (bin, i, j) => {
      byKind.fill(0); let tot = 0;
      for (let r = i; r < j; r++) { byKind[S.b.labels[label[r]].kind] += count[r]; tot += count[r]; }
      if (!tot) return;
      const x0 = X(bin * b.bin_us, w), x1 = X((bin + 1) * b.bin_us, w);
      ctx.globalAlpha = tot < minN ? 0.4 : 1;
      let y = y0;
      for (let k = 0; k < 9; k++) {
        if (!byKind[k]) continue;
        const hh = (byKind[k] / tot) * LANE_H; ctx.fillStyle = kindColor(k); ctx.fillRect(x0, y, x1 - x0 + 0.6, hh); y += hh;
      }
      ctx.globalAlpha = 1;
    });
    if (S.sel !== "typical" && b.core_stats[S.sel]?.roles[lane]) {  // this core's measured span for the lane's RISC
      const [s, e] = b.core_stats[S.sel].roles[lane]; ctx.fillStyle = css("--text");
      ctx.fillRect(X(s, w) - 1, y0 - 1, 2, LANE_H + 2); ctx.fillRect(X(e, w) - 1, y0 - 1, 2, LANE_H + 2);
    }
  });
  const yb = lanes.length * (LANE_H + LANE_GAP);
  ctx.setLineDash([3, 3]); ctx.strokeStyle = css("--dim");
  const xm = X(b.launch.median, w); ctx.beginPath(); ctx.moveTo(xm + 0.5, 0); ctx.lineTo(xm + 0.5, yb); ctx.stroke(); ctx.setLineDash([]);
  xAxis(ctx, w, yb + 4);
  crosshair(ctx, w, yb);
}
function crosshair(ctx, w, h) {
  if (S.hoverT == null) return;
  const x = X(S.hoverT, w); ctx.strokeStyle = css("--text"); ctx.globalAlpha = 0.5;
  ctx.beginPath(); ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, h); ctx.stroke(); ctx.globalAlpha = 1;
}
function kviewLink(l) {
  if (l.pc == null || !l.file) return null;
  return `http://${location.hostname}:${S.kviewPort}/#/llama3-${S.b.model}/${S.b.kernel}/${l.file}@${l.pc.toString(16)}`;
}
function timelineEvent(ev, click) {
  const cv = $("#tl"), r = cv.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top, w = cv.clientWidth;
  const li = Math.floor(y / (LANE_H + LANE_GAP)), lane = S.b.lanes[li];
  if (x < G || !lane) { S.hoverT = null; redrawCross(); return untip(); }
  S.hoverT = T(x, w); redrawCross();
  const bin = Math.floor(S.hoverT / S.b.bin_us), pairs = pairsAt(stream(S.sel, lane), bin);
  if (!pairs) return tip(ev, `${lane} · ${fmt(S.hoverT, 2)} µs`, [[css("--idle"), "–", "not running (no samples)"]]);
  const tot = pairs.reduce((a, p) => a + p[1], 0);
  if (click) { const link = kviewLink(S.b.labels[pairs[0][0]]); if (link) window.open(link, "kview"); return; }
  tip(ev, `${lane} · ${fmt(bin * S.b.bin_us, 2)}–${fmt((bin + 1) * S.b.bin_us, 2)} µs · ${tot} samples${pairs.some(([l]) => S.b.labels[l].pc != null) ? " · click: open in kview" : ""}`,
    pairs.slice(0, 6).map(([l, n]) => [kindColor(S.b.labels[l].kind), `${Math.round(100 * n / tot)}%`, S.b.labels[l].text]));
}

// ---------- DRAM
const LINE_H = 84, HEAT_ROW = 15;
function dramRows(b) {  // [{label, value(binIndex)}] for the heatmap
  const pr = S.dramRows === "ports" && portRows(b);
  if (pr) return pr.map((r) => ({ label: `D${r.bank}.${r.port} ${r.key}`, v: (i) => r.cols.reduce((t, j) => t + (j == null ? 0 : b.dram.ports[i][j]), 0) }));
  return Array.from({ length: 8 }, (_, k) => ({ label: `bank ${k}`, v: (i) => b.dram.banks[i][k] }));
}
function renderDram() {
  const b = S.b, cv = $("#dram"), R = dramRows(b), H = LINE_H + 10 + R.length * HEAT_ROW + 26;
  const { ctx, w } = canvas(cv, H);
  const ymax = b.pin_gbs, Y = (v) => LINE_H - (v / ymax) * (LINE_H - 6);
  ctx.textAlign = "right"; ctx.strokeStyle = css("--grid"); ctx.fillStyle = css("--dim");
  for (const v of [0, 250, 500]) { ctx.beginPath(); ctx.moveTo(G, Y(v) + 0.5); ctx.lineTo(w - 10, Y(v) + 0.5); ctx.stroke(); ctx.fillText(`${v} GB/s`, G - 6, Y(v)); }
  ctx.strokeStyle = css("--k0"); ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.beginPath();
  b.dram.total.forEach((v, i) => { const x = X((i + 0.5) * b.dram_bin_us, w); if (x > w - 10) return; i ? ctx.lineTo(x, Y(v)) : ctx.moveTo(x, Y(v)); });
  ctx.stroke(); ctx.lineWidth = 1;
  const y0 = LINE_H + 10;
  R.forEach((row, k) => {
    ctx.fillStyle = css("--dim"); ctx.textAlign = "right"; ctx.fillText(row.label, G - 6, y0 + k * HEAT_ROW + HEAT_ROW / 2);
    b.dram.banks.forEach((_, i) => {
      const x0 = X(i * b.dram_bin_us, w), x1 = X((i + 1) * b.dram_bin_us, w); if (x0 > w - 10) return;
      ctx.fillStyle = seq(row.v(i) / 64.3); ctx.fillRect(x0, y0 + k * HEAT_ROW, x1 - x0 + 0.6, HEAT_ROW - 1);
    });
  });
  const yh = y0 + R.length * HEAT_ROW;
  const xm = X(b.launch.median, w); ctx.setLineDash([3, 3]); ctx.strokeStyle = css("--dim");
  ctx.beginPath(); ctx.moveTo(xm + 0.5, 0); ctx.lineTo(xm + 0.5, yh); ctx.stroke(); ctx.setLineDash([]);
  xAxis(ctx, w, yh + 4);
  crosshair(ctx, w, yh);
  scaleBar($("#dram-scale"), 0, 64.3, `GB/s per ${S.dramRows === "ports" ? "port" : "bank"} (a controller's pin rate is 64.3)`);
  const dl = b.quality.dram_launches;
  $("#dram-sub").textContent = `all 24 ports, folded over ${dl == null ? b.launches : `${dl} of ${b.launches}`} launches; line = total (one axis, 0–${b.pin_gbs} GB/s pin rate)`;
}
function dramEvent(ev) {
  const cv = $("#dram"), r = cv.getBoundingClientRect(), x = ev.clientX - r.left, w = cv.clientWidth;
  if (x < G) { S.hoverT = null; redrawCross(); return untip(); }
  S.hoverT = T(x, w); redrawCross();
  const i = Math.floor(S.hoverT / S.b.dram_bin_us);
  if (!S.b.dram.banks[i]) return untip();
  const rows = dramRows(S.b).map((r) => [r.v(i), r.label]).filter(([v]) => S.dramRows !== "ports" || v >= 1);
  tip(ev, `${fmt(i * S.b.dram_bin_us, 1)}–${fmt((i + 1) * S.b.dram_bin_us, 1)} µs · DRAM read GB/s${S.dramRows === "ports" ? " (ports with traffic)" : ""}`,
    [[css("--k0"), fmt(S.b.dram.total[i], 0), "total"], ...rows.map(([v, l]) => [seq(v / 64.3), fmt(v, 0), l])]);
}
function redrawCross() { renderTimeline(); renderDram(); }

// ---------- table view (also the accessibility relief: every value without hovering)
function renderTable() {
  const t = $("#table"); t.replaceChildren();
  const head = el("tr"); ["lane", "share", "code region / state", ""].forEach((h) => head.append(el("th", null, h))); t.append(head);
  $("#table-sub").textContent = S.sel === "typical" ? `all ${S.b.cores.length} cores` : `core ${S.sel}`;
  const { label, count } = S.A;
  for (const lane of S.b.lanes) {
    const c = {}, [s, e] = stream(S.sel, lane); let tot = 0;
    for (let i = s; i < e; i++) { c[label[i]] = (c[label[i]] || 0) + count[i]; tot += count[i]; }
    Object.entries(c).sort((a, z) => z[1] - a[1]).slice(0, 5).forEach(([l, n], j) => {
      const L = S.b.labels[+l], tr = el("tr", j ? null : "first");
      tr.append(el("td", "lane", j ? "" : lane));
      const pct = el("td", "num"), m = el("span", "meter"); m.style.width = `${Math.max(2, 60 * n / tot)}px`; m.style.background = kindColor(L.kind);
      pct.append(m, document.createTextNode(`${(100 * n / tot).toFixed(0)}%`));
      const lab = el("td", "lab"), link = kviewLink(L);
      if (link) { const a = el("a", null, L.text); a.href = link; a.target = "kview"; lab.append(a); } else lab.textContent = L.text;
      if (L.insns?.length) lab.title = L.insns.map(([i, k]) => `${k}× ${i}`).join("\n");
      tr.append(pct, lab, el("td", "num", S.b.kinds[L.kind] || "idle")); t.append(tr);
    });
  }
}

// ---------- wiring
function renderAllSel() { renderPick(); renderMap(); renderTimeline(); renderDram(); renderTable(); }
function renderAll() { renderStats(); renderFindings(); renderAllSel(); }
async function load(name) {
  const [b, f] = await Promise.all([fetchBundle(name), api(`/api/findings?name=${encodeURIComponent(name)}`)]);
  b.findings = f; S.b = b; S.A = b.A; S.streams = b.streamIndex; prepare(b);
  if (S.sel !== "typical" && !S.b.core_stats[S.sel]) S.sel = "typical";
  history.replaceState(null, "", `#${name}`); renderAll();
}
async function main() {
  if (localStorage.getItem("kperf-theme") === "light") document.documentElement.classList.add("light");
  $("#theme").onclick = () => { document.documentElement.classList.toggle("light"); localStorage.setItem("kperf-theme", dark() ? "dark" : "light"); if (S.b) renderAll(); };
  const ms = $("#metric"); for (const [k, m] of Object.entries(METRICS)) { const o = el("option", null, m.name); o.value = k; ms.append(o); }
  ms.onchange = () => { S.metric = ms.value; renderMap(); };
  S.dramRows = localStorage.getItem("kperf-dram-rows") || "ports";
  const dr = $("#dram-rows"); dr.value = S.dramRows;
  dr.onchange = () => { S.dramRows = dr.value; localStorage.setItem("kperf-dram-rows", dr.value); renderDram(); };
  const { bundles, kview_port } = await api("/api/bundles"); S.list = bundles; S.kviewPort = kview_port;
  const sel = $("#bundle");
  for (const b of bundles) { const o = el("option", null, `${b.model} · ${b.kernel} L${b.layer}${b.position != null ? ` @${b.position}` : ""} · ${b.median.toFixed(1)} µs · ${b.created.replace("T", " ")}`); o.value = b.name; sel.append(o); }
  sel.onchange = () => load(sel.value);
  $("#map").addEventListener("pointermove", (e) => mapEvent(e, false)); $("#map").addEventListener("click", (e) => mapEvent(e, true));
  $("#map").addEventListener("pointerleave", untip);
  $("#tl").addEventListener("pointermove", (e) => timelineEvent(e, false)); $("#tl").addEventListener("click", (e) => timelineEvent(e, true));
  $("#dram").addEventListener("pointermove", dramEvent);
  for (const id of ["#tl", "#dram"]) $(id).addEventListener("pointerleave", () => { S.hoverT = null; untip(); if (S.b) redrawCross(); });
  let rt; addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => S.b && renderAllSel(), 100); });
  if (!bundles.length) { $("#findings").textContent = "No bundles yet: run python -m kperf.collect --model 1b --kernel o"; return; }
  const want = decodeURIComponent(location.hash.slice(1));
  sel.value = bundles.some((b) => b.name === want) ? want : bundles[0].name;
  await load(sel.value);
}
main().catch((e) => { document.body.prepend(el("pre", null, String(e))); });
