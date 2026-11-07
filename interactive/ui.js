// Shared browser UI pieces for the packer and unpacker explorers.
(function () {
"use strict";
const T = window.TT;

function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") e.className = v; else if (k === "html") e.innerHTML = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) e.append(c.nodeType ? c : document.createTextNode(String(c)));
  return e;
}
function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }

// colour hue for a datum identified by its source index (row = idx >> 4)
function hue(src) { if (src == null) return 0; const row = Math.floor(src / 16), col = src % 16; return ((row % 64) * 5.55 + col * 0.35) % 360; }

function store(key, value) { try { if (value === undefined) return JSON.parse(localStorage.getItem(key) || "null"); localStorage.setItem(key, JSON.stringify(value)); } catch (e) { return null; } }

// ***** tooltip *****
const tip = el("div", {class: "tip", hidden: true});
document.addEventListener("DOMContentLoaded", () => document.body.append(tip));
let tipFn = null;
function setTipSource(fn) { tipFn = fn; }
document.addEventListener("mouseover", e => {
  const t = e.target.closest("[data-tip],[data-i],[data-a]");
  if (!t) { tip.hidden = true; return; }
  const text = t.dataset.tip || (tipFn && tipFn(t));
  if (!text) { tip.hidden = true; return; }
  tip.textContent = text; tip.hidden = false;
});
document.addEventListener("mousemove", e => {
  if (tip.hidden) return;
  const w = tip.offsetWidth, h = tip.offsetHeight;
  let x = e.clientX + 14, y = e.clientY + 16;
  if (x + w > innerWidth - 8) x = e.clientX - w - 14;
  if (y + h > innerHeight - 8) y = e.clientY - h - 12;
  tip.style.left = Math.max(4, x) + "px"; tip.style.top = Math.max(4, y) + "px";
});
document.addEventListener("mouseleave", () => tip.hidden = true);

// ***** config form *****
// fields: [{g, s?, key, type, raw, doc, conf, opts?}], scopes: {ctx: {count, label}, am: {count, label}}
function configPanel(root, fields, getCfg, getDefaults, {scopes, rawName, onChange, open = []}) {
  const sel = {...Object.fromEntries(Object.keys(scopes).map(k => [k, 0])), ...(store(location.pathname + ":cfgsel") || {})};
  for (const k of Object.keys(scopes)) if (!(sel[k] < scopes[k].count)) sel[k] = 0;
  const openGroups = new Set(store(location.pathname + ":open") || open);
  function value(f) { const c = getCfg(); return f.s ? c[f.s][sel[f.s]][f.key] : c[f.key]; }
  function dvalue(f) { const d = getDefaults(); return f.s ? d[f.s][sel[f.s]][f.key] : d[f.key]; }
  function set(f, v) { const c = getCfg(); if (f.s) c[f.s][sel[f.s]][f.key] = v; else c[f.key] = v; onChange(); }
  function input(f) {
    const v = value(f), id = `cfg-${f.s || "g"}-${f.key}`;
    switch (f.type) {
    case "bool": return el("input", {type: "checkbox", id, checked: !!v, onchange: e => set(f, e.target.checked)});
    case "int": return el("input", {type: "number", id, value: v, step: 1, onchange: e => set(f, Number(e.target.value) || 0)});
    case "hex": case "map": return el("input", {type: "text", id, class: f.type === "map" ? "wide" : "", value: T.hex(v), spellcheck: "false",
      onchange: e => { const n = T.parseNum(e.target.value.trim()); if (n === null) { e.target.value = T.hex(value(f)); return; } set(f, n >>> 0); }});
    case "fmt": return el("select", {id, onchange: e => set(f, Number(e.target.value))},
      Object.values(T.FORMATS).map(F => el("option", {value: F.code, selected: F.code === v}, `${F.name} (${F.llk}, ${F.code})`)));
    case "enum": return el("select", {id, onchange: e => { const o = f.opts.find(o => String(o[0]) === e.target.value); set(f, o[0]); }},
      f.opts.map(([k, l]) => el("option", {value: k, selected: k === v}, l)));
    case "pattern": return el("select", {id, onchange: e => set(f, e.target.value)},
      Object.entries(T.PATTERNS).map(([k, p]) => el("option", {value: k, selected: k === v}, p.label)));
    }
  }
  function confTag(c) { return c === "hw" ? el("span", {class: "tag hw", "data-tip": "Confirmed on card 0 by blackhole-py-rewrite/tests/hw"}, "on hw") : c === "inf" ? el("span", {class: "tag inf", "data-tip": "Inferred, not probed on hardware"}, "inferred") : c === "sim" ? el("span", {class: "tag"}, "explorer") : null; }
  function render() {
    root.replaceChildren();
    const groups = [];
    for (const f of fields) { let g = groups.find(g => g.name === f.g); if (!g) groups.push(g = {name: f.g, s: f.s, fields: []}); g.fields.push(f); }
    for (const g of groups) {
      const det = el("details", {open: openGroups.has(g.name), ontoggle: e => { e.target.open ? openGroups.add(g.name) : openGroups.delete(g.name); store(location.pathname + ":open", [...openGroups]); }});
      const changed = g.fields.filter(f => JSON.stringify(value(f)) !== JSON.stringify(dvalue(f))).length;
      det.append(el("summary", {}, el("span", {}, g.name, g.s ? el("span", {class: "tag", style: "margin-left:6px"}, `${scopes[g.s].label} ${sel[g.s]}`) : null),
        changed ? el("span", {class: "tag", style: "color:var(--hot)"}, `${changed} changed`) : null));
      if (g.s) {
        const sc = scopes[g.s];
        det.append(el("div", {class: "grp-note"}, sc.note));
        det.append(el("div", {class: "ctx-tabs", role: "group", "aria-label": sc.label},
          Array.from({length: sc.count}, (_, i) => el("button", {type: "button", "aria-pressed": String(i === sel[g.s]), onclick: () => { sel[g.s] = i; store(location.pathname + ":cfgsel", sel); render(); }}, `${sc.short}${i}`))));
      }
      for (const f of g.fields) {
        const changedF = JSON.stringify(value(f)) !== JSON.stringify(dvalue(f));
        const id = `cfg-${f.s || "g"}-${f.key}`;
        const row = el("div", {class: "field" + (changedF ? " changed" : "")},
          el("label", {for: id}, f.label || f.key.replace(/_/g, " "), " ", confTag(f.conf)), input(f),
          el("div", {class: "raw"}, rawName ? rawName(f, f.s ? sel[f.s] : 0) : f.raw, f.s ? "" : ""),
          f.doc ? el("div", {class: "doc"}, f.doc) : null);
        if (f.type === "map") row.append(el("div", {class: "raw"}, "by position 0→15: " + Array.from({length: 16}, (_, i) => value(f) >> (2 * i) & 3).join(" ")));
        if (f.type === "hex" && /mask/.test(f.key) && !/downsample/.test(f.key)) row.append(el("div", {class: "raw"}, "columns 0→15: " + Array.from({length: 16}, (_, i) => value(f) >> i & 1 ? "■" : "·").join("")));
        if (f.type === "hex" && f.key === "downsample_mask") row.append(el("div", {class: "raw"}, "keep datum 0→15: " + Array.from({length: 16}, (_, i) => (value(f) || 0xFFFF) >> i & 1 ? "■" : "·").join("")));
        if (f.extra) { const x = f.extra(getCfg(), sel); if (x) row.append(el("div", {class: "raw"}, x)); }
        det.append(row);
      }
      root.append(det);
    }
  }
  render();
  return {render, sel};
}

// ***** stepper *****
function stepper(root, {onStep}) {
  const range = el("input", {type: "range", min: 0, max: 0, value: 0, id: "step-range", "aria-label": "Instructions executed"});
  const pos = el("span", {class: "pos"});
  let n = 0, cur = 0;
  const go = v => { cur = Math.max(0, Math.min(n, v)); range.value = cur; pos.textContent = `${cur}/${n}`; onStep(cur); };
  root.append(
    el("button", {class: "btn", type: "button", "data-tip": "Reset (Home)", onclick: () => go(0)}, "«"),
    el("button", {class: "btn", type: "button", "data-tip": "Back one instruction (←)", onclick: () => go(cur - 1)}, "◀"),
    range,
    el("button", {class: "btn", type: "button", "data-tip": "Run one instruction (→)", onclick: () => go(cur + 1)}, "▶"),
    el("button", {class: "btn", type: "button", "data-tip": "Run to the end (End)", onclick: () => go(n)}, "»"),
    pos);
  range.addEventListener("input", () => go(Number(range.value)));
  document.addEventListener("keydown", e => {
    if (e.target.closest("input,textarea,select")) return;
    if (e.key === "ArrowRight") { go(cur + 1); e.preventDefault(); }
    else if (e.key === "ArrowLeft") { go(cur - 1); e.preventDefault(); }
    else if (e.key === "Home") go(0); else if (e.key === "End") go(n);
  });
  return {setMax(m, keep) { n = m; range.max = m; go(keep ? Math.min(cur, m) : m); }, go, get cur() { return cur; }, get n() { return n; }};
}

// ***** step list *****
function stepList(root, program, cur, steps, onPick) {
  const html = program.map((ins, i) => {
    const st = steps[i];
    const cls = i === cur - 1 ? "cur" : i < cur ? "done" : "";
    return `<div class="${cls}${st && st.error ? " err" : ""}" data-k="${i + 1}"><span class="n">${i + 1}</span><span>${esc(ins.raw.replace(/#.*/, "").replace(/\s+x\d+(?=\s|$)/i, "").trim())}${ins.rep ? ` <span class="c">· ${ins.rep}</span>` : ""}</span></div>`;
  }).join("");
  root.innerHTML = html || `<div class="hint" style="padding:6px 8px">No instructions.</div>`;
  root.onclick = e => { const d = e.target.closest("[data-k]"); if (d) onPick(Number(d.dataset.k)); };
  const c = root.querySelector(".cur"); if (c) { const r = root.getBoundingClientRect(), cr = c.getBoundingClientRect(); if (cr.top < r.top || cr.bottom > r.bottom) root.scrollTop += cr.top - r.top - r.height / 2; }
}

function renderTrace(root, step) {
  if (!step) { root.innerHTML = `<span class="c">Step forward to run the first instruction. Each step shows the address math it did.</span>`; return; }
  root.innerHTML = step.trace.map(([c, s]) => c ? `<span class="${c}">${esc(s)}</span>` : esc(s)).join("\n");
}

// counters table: rows = channels/things, cols = X Y Z W (+ carry)
function counterTable(root, rows, prev) {
  const cols = ["X", "Y", "Z", "W"];
  let h = `<table class="counters"><thead><tr><th></th>${cols.map(c => `<th>${c}</th>`).join("")}</tr></thead><tbody>`;
  for (const r of rows) {
    h += `<tr><th style="text-align:left" ${r.tip ? `data-tip="${esc(r.tip)}"` : ""}>${esc(r.label)}</th>` + cols.map(c => {
      const v = r.v[c], p = r.p ? r.p[c] : v;
      return `<td class="${v !== p ? "changed" : ""}">${v ?? "·"}</td>`;
    }).join("") + "</tr>";
  }
  root.innerHTML = h + "</tbody></table>";
}

// L1 byte view over the given address set. byteInfo(addr) -> {cls, h, label, parts:[{h,label}], title}
function l1View(root, addrs, byteInfo, {sections = [], maxRows = 400, hot = new Set(), sel = null, pending = []} = {}) {
  const rowsSet = new Set();
  for (const a of addrs) rowsSet.add(a >> 4);
  for (const p of pending) rowsSet.add(p >> 4);
  const rows = [...rowsSet].sort((a, b) => a - b);
  if (!rows.length) { root.innerHTML = `<div class="hint">Nothing written yet.</div>`; return; }
  const secAt = new Map(sections.map(s => [s.start >> 4, s]));
  const pend = new Set(pending);
  let h = `<div class="l1"><span></span>${Array.from({length: 16}, (_, i) => `<span class="ra" style="text-align:center;padding:0">${i.toString(16).toUpperCase()}</span>`).join("")}`;
  let prev = null, shown = 0;
  for (const r of rows) {
    if (shown >= maxRows) { h += `<div class="sec">… ${rows.length - shown} more rows not shown</div>`; break; }
    if (prev !== null && r !== prev + 1) h += `<div class="sec">… gap of ${(r - prev - 1) * 16} bytes …</div>`;
    const s = secAt.get(r); if (s) h += `<div class="sec">${esc(s.name)} · ${T.hex(s.start)}${s.end != null ? "–" + T.hex(s.end - 1) : ""}</div>`;
    h += `<span class="ra">${T.hex(r * 16, 5)}</span>`;
    for (let c = 0; c < 16; c++) {
      const a = r * 16 + c, info = byteInfo(a);
      const extra = (hot.has(a) ? " hot" : "") + (sel === a ? " sel" : "") + (pend.has(a) ? " pend" : "");
      if (info.parts) h += `<span class="byte split${extra}" data-a="${a}">${info.parts.map(p => `<span class="${p.cls || ""}" style="--h:${p.h}">${esc(p.label ?? "")}</span>`).join("")}</span>`;
      else h += `<span class="byte ${info.cls}${extra}" data-a="${a}" style="--h:${info.h ?? 0}">${esc(info.label ?? "")}</span>`;
    }
    prev = r; shown++;
  }
  root.innerHTML = h + "</div>";
}

// datum grid: rows x 16 columns. cell(row, col) -> {cls, h, label, i}
function datumGrid(root, {rowStart, rowCount, cell, rowLabel = r => r, colLabel = c => c, cols = 16, wide = false, groupEvery = 0}) {
  let h = `<div class="grid${wide ? " wide" : ""}" style="grid-template-columns:auto repeat(${cols}, max-content)"><span></span>`;
  for (let c = 0; c < cols; c++) h += `<span class="cl">${colLabel(c)}</span>`;
  for (let r = rowStart; r < rowStart + rowCount; r++) {
    if (groupEvery && r > rowStart && (r - rowStart) % groupEvery === 0) h += `<span style="grid-column:1/-1;height:3px"></span>`;
    h += `<span class="rl">${rowLabel(r)}</span>`;
    for (let c = 0; c < cols; c++) { const x = cell(r, c); h += `<span class="cell ${x.cls}" data-i="${x.i}" style="--h:${x.h ?? 0}">${esc(x.label ?? "")}</span>`; }
  }
  root.innerHTML = h + "</div>";
}

function labelOf(mode, v, src) {
  switch (mode) {
    case "value": { const s = T.fmtNum(v); return s.length > 5 ? s.replace(/\.?0+e/, "e").slice(0, 5) : s; }
    case "row": return src == null ? "" : String(src >> 4);
    case "col": return src == null ? "" : String(src & 15);
    default: return "";
  }
}

window.UI = {el, esc, hue, store, setTipSource, configPanel, stepper, stepList, renderTrace, counterTable, l1View, datumGrid, labelOf};
})();
