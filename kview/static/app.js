"use strict";
const $ = s => document.querySelector(s);
const hex = n => "0x" + (n >>> 0).toString(16);
const fmtSize = n => n >= 1 << 30 ? +(n / 2 ** 30).toFixed(1) + " GiB" : n >= 1 << 20 ? +(n / 2 ** 20).toFixed(1) + " MiB" : n >= 1 << 10 ? +(n / 1024).toFixed(1) + " KiB" : n + " B";
const hex8 = n => (n >>> 0).toString(16).padStart(8, "0");
const ROLE_SHORT = { brisc: "br", ncrisc: "nc", trisc0: "t0", trisc1: "t1", trisc2: "t2" };
const ROLE_JOB = { brisc: "data movement, NoC 0", ncrisc: "data movement, NoC 1", trisc0: "unpack thread", trisc1: "math thread", trisc2: "pack thread" };

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) el.append(kid);
  return el;
}

const S = {
  index: null, isa: null, model: null, program: null, file: null, kernel: null, sel: null,
  rowEl: new Map(), lazy: new Map(), byPc: new Map(), refs: new Map(), jumps: new Map(), text: new Map(),
  hits: [], hitSet: new Set(), kernels: new Map(), pickParam: null,
};

// ---------------------------------------------------------------------------------------------------------------- data
async function api(path) {
  const r = await fetch(path);
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}
const curModel = () => S.index.models.find(m => m.id === S.model);
const curProgram = () => curModel()?.programs.find(p => p.name === S.program);

async function loadKernel(model, program, file) {
  const key = `${model}/${program}/${file}`;
  if (!S.kernels.has(key)) S.kernels.set(key, await api(`/api/kernel?model=${model}&program=${program}&file=${file}`));
  return S.kernels.get(key);
}

// ------------------------------------------------------------------------------------------------------------- routing
function parseHash() {
  const m = location.hash.match(/^#\/([^/@]+)(?:\/([^/@]+))?(?:\/([^/@]+))?(?:@([0-9a-f]+))?/);
  return m ? { model: m[1], program: m[2], file: m[3], pc: m[4] != null ? parseInt(m[4], 16) : null } : {};
}
function makeHash(model, program, file, pc) {
  return "#/" + model + (program ? "/" + program : "") + (file ? "/" + file : "") + (pc != null ? "@" + pc.toString(16) : "");
}
function go(model, program, file, pc) {
  history.pushState(null, "", makeHash(model, program, file, pc));
  route();
}
async function route() {
  let { model, program, file, pc } = parseHash();
  const models = S.index.models;
  if (!models.some(m => m.id === model)) model = models[0].id;
  const mm = models.find(m => m.id === model);
  if (!mm.programs.some(p => p.name === program)) { program = mm.programs[0].name; file = null; }
  const pp = mm.programs.find(p => p.name === program);
  if (file && !pp.kernels.some(k => k.file === file)) file = null;
  const changed = model !== S.model || program !== S.program || file !== S.file;
  Object.assign(S, { model, program, file });
  renderRail();
  if (!file) { S.kernel = null; S.sel = null; renderOverview(); renderOutline(); renderCrumbs(); return; }
  if (changed || !S.kernel) {
    try { S.kernel = await loadKernel(model, program, file); }
    catch (e) { $("#view").replaceChildren(h("div", { id: "overview" }, h("h2", {}, "Could not decode this kernel"), h("p", { class: "lede" }, String(e.message)))); return; }
    indexKernel();
    renderCrumbs(); renderListing(); renderOutline(); runFind(false);
    $("#view").scrollTop = 0;
  }
  select(pc, { scroll: pc != null, flash: pc != null });
}

// ---------------------------------------------------------------------------------------------------------------- rail
function renderRail() {
  const mm = curModel();
  $("#models").replaceChildren(...S.index.models.map(m =>
    h("button", { role: "tab", "aria-selected": String(m.id === S.model), title: m.note, onclick: () => go(m.id, S.program, S.file) }, m.model)));
  const stages = mm.sequence.map(stage => {
    const box = h("div", { class: "stage" + (stage.times > 1 ? " loop" : "") });
    if (stage.times > 1) box.append(h("div", { class: "stage-note" }, `repeated for each of ${stage.times} layers`));
    for (const name of stage.names) box.append(progRow(mm.programs.find(p => p.name === name)));
    return box;
  });
  $("#pipeline").replaceChildren(h("div", { class: "stage-note" }, "One token, in launch order"), ...stages);
}
function progRow(p) {
  const chips = Object.keys(ROLE_SHORT).flatMap(role => {
    const ks = p.kernels.filter(k => k.role === role);
    if (!ks.length) return [h("span", { class: "chip none" }, ROLE_SHORT[role])];
    return ks.map(k => h("button", {
      class: "chip" + (k.variant != null ? " var" : "") + (S.program === p.name && S.file === k.file ? " cur" : ""),
      title: `${p.name} / ${k.file}: ${ROLE_JOB[role]}, ${k.size} bytes, ${k.cores.length} cores`,
      onclick: () => go(S.model, p.name, k.file),
    }, ROLE_SHORT[role], k.variant != null ? h("sub", {}, String(k.variant)) : null));
  });
  return h("div", { class: "prog" + (S.program === p.name ? " cur" : "") },
    h("a", { title: `${p.name}: parameters, cores and kernels`, onclick: () => go(S.model, p.name) }, p.name), h("div", { class: "chips" }, chips));
}

function renderCrumbs() {
  const p = curProgram(), box = $("#crumbs");
  if (!S.file) {
    box.replaceChildren(h("span", { class: "title" }, S.program), h("span", { class: "meta" }, `${p.cores.length} cores, launched ${p.launches}× per token`));
    $("#tools").style.display = "none";
    return;
  }
  $("#tools").style.display = "";
  const k = p.kernels.find(k => k.file === S.file), K = S.kernel;
  const counts = { rv: 0, tt: 0, data: 0 };
  for (const r of K.rows) counts[r.kind]++;
  box.replaceChildren(
    h("span", { class: "title" }, h("span", { class: "jump", onclick: () => go(S.model, S.program) }, S.program), h("span", { class: "sep" }, "/"), S.file),
    h("span", { class: "meta" }, `${ROLE_JOB[k.role]}  ·  ${K.size} bytes  ·  ${counts.rv} RISC-V, ${counts.tt} Tensix${counts.data ? `, ${counts.data} data words` : ""}  ·  ${k.cores.length} cores`),
    h("div", { class: "roles" }, p.kernels.map(o => h("button", { class: o.file === S.file ? "cur" : "", title: ROLE_JOB[o.role], onclick: () => go(S.model, S.program, o.file) }, o.file))));
}

// ------------------------------------------------------------------------------------------------------------- listing
function rowText(row) {
  const ops = row.kind === "tt" ? row.args.map(a => `${a[0]}=${a[1]}`).join(", ") : (row.operands || "") + (row.tlabel || "");
  const ann = row.ann.map(a => a[0] === "store" ? `${a[1]} ← ${a[2]}` : a[1]).join("; ");
  return `${row.pc.toString(16)} ${row.op} ${ops} ${ann} ${row.label || ""} ${row.func ? row.func.title || "" : ""}`;
}
function indexKernel() {
  const K = S.kernel;
  S.byPc = new Map(); S.refs = new Map(); S.jumps = new Map(); S.text = new Map();
  for (const row of K.rows) {
    S.byPc.set(row.pc, row);
    S.text.set(row.pc, rowText(row).toLowerCase());
    if (row.sym) { if (!S.refs.has(row.sym)) S.refs.set(row.sym, []); S.refs.get(row.sym).push(row); }
    if (row.target != null && row.back != null) { if (!S.jumps.has(row.target)) S.jumps.set(row.target, []); S.jumps.get(row.target).push(row); }
  }
}
function foldKey(row) {
  if (row.label || row.func || row.target != null || row.ret) return null;
  return `${row.kind}|${row.op}|${row.kind === "tt" ? row.tword : row.operands}|${JSON.stringify(row.ann)}`;
}
function fold(rows, keys, lo, hi) {
  const out = [];
  let i = lo;
  while (i < hi) {
    let best = null;
    if (keys[i] != null) {
      for (let p = 1; p <= 64 && i + 2 * p <= hi; p++) {
        let reps = 1;
        scan: while (i + (reps + 1) * p <= hi) {
          for (let k = 0; k < p; k++) if (keys[i + k] == null || keys[i + k] !== keys[i + reps * p + k]) break scan;
          reps++;
        }
        if (reps >= (p === 1 ? 3 : 2) && (!best || reps * p > best.reps * best.p)) best = { p, reps };
      }
    }
    if (best) { out.push({ rep: true, i, p: best.p, reps: best.reps }); i += best.p * best.reps; }
    else { out.push({ i }); i++; }
  }
  return out;
}
function nmClass(name) {
  if (/^(param |&)/.test(name)) return "nm param";
  if (/^\[?(cb\d|CB\d|cb@)/.test(name)) return "nm cb";
  if (/^NOC/.test(name)) return "nm noc";
  if (/^(cfg|thread_cfg|MOP_CFG|INSTRN|GPR|PC_BUF|semaphore)/.test(name)) return "nm tensix";
  if (/^\[?local/.test(name)) return "nm local";
  return "nm";
}
function annNodes(row) {
  const out = [];
  for (const a of row.ann) {
    if (out.length) out.push(h("span", { class: "sepr" }, ";"));
    const [kind, x, y] = a;
    if (kind === "gist") out.push(h("span", { class: "gist" }, x));
    else if (kind === "store") out.push(h("span", { class: nmClass(x) }, x), h("span", { class: "arrow" }, " ← "), h("span", { class: "v" }, String(y)));
    else if (kind === "load") out.push(h("span", { class: "v" }, (row.operands || "").split(",")[0]), h("span", { class: "arrow" }, " ← "), h("span", { class: nmClass(x) }, x));
    else if (kind === "val") { const [v, name] = x.split("  "); out.push(h("span", { class: name ? "" : "v" }, v), name ? h("span", { class: nmClass(name) }, "  " + name) : null); }
    else if (kind === "call") out.push(h("span", { class: "callt" }, x));
    else if (kind === "field") out.push(h("span", { class: "fieldt" }, x));
    else out.push(h("span", { class: "notet" }, x));
  }
  return out;
}
function opsNode(row) {
  if (row.kind === "tt") {
    const title = row.args.map(a => `${a[0]} = ${a[1]}${a[2] ? "  (" + a[2] + ")" : ""}`).join("\n");
    return h("span", { class: "ops", title }, row.args.flatMap((a, i) => [i ? ", " : "", a[0] + "=", h("b", {}, String(a[1]))]));
  }
  const kids = [row.operands || ""];
  if (row.tlabel && row.target != null && row.back != null || row.call) kids.push(h("span", { class: "jump", "data-target": row.target }, row.tlabel));
  return h("span", { class: "ops" }, kids);
}
function rowNodes(row) {
  const out = [];
  if (row.func) {
    const f = row.func;
    out.push(h("div", { class: "fnhead", "data-pc": row.pc },
      h("span", { class: "name" }, f.name), f.title ? h("span", { class: "title" }, f.title) : null,
      h("span", { class: "meta" }, `${f.size} instructions` + (f.args.length ? `, reads ${f.args.map(a => "x" + a).join(" ")}` : "") +
        `, called from ${f.callers.length} place${f.callers.length === 1 ? "" : "s"}`),
      h("span", { class: "from meta" }, f.callers.slice(0, 12).map(pc => h("a", { class: "jump", "data-target": pc }, pc.toString(16) + " ")))));
  } else if (row.label) {
    const from = S.jumps.get(row.pc) || [];
    out.push(h("div", { class: "label" }, h("span", { class: "name" }, row.label + ":"),
      h("span", { class: "from" }, from.length ? "from " : "", from.slice(0, 10).map(r => h("a", { "data-target": r.pc }, r.pc.toString(16))))));
  }
  const el = h("div", { class: `row k-${row.kind}` + (row.dim ? " dimmed" : "") + (S.hitSet.has(row.pc) ? " hit" : ""), "data-pc": row.pc },
    h("span", { class: "pc" }, row.pc.toString(16)), h("span", { class: "word" }, hex8(row.word)),
    h("span", { class: "op" }, row.op), opsNode(row), h("span", { class: "ann" }, annNodes(row)));
  S.rowEl.set(row.pc, el);
  out.push(el);
  return out;
}
function build(parent, rows, keys, lo, hi, doFold) {
  const items = doFold ? fold(rows, keys, lo, hi) : Array.from({ length: hi - lo }, (_, k) => ({ i: lo + k }));
  for (const it of items) {
    if (!it.rep) { parent.append(...rowNodes(rows[it.i])); continue; }
    const n = it.p * it.reps, first = rows[it.i], last = rows[it.i + n - 1];
    const rest = h("div", { hidden: true });
    const btn = h("button", {}, "show all");
    const expand = () => {
      if (!rest.dataset.done) { build(rest, rows, keys, it.i + it.p, it.i + n, false); rest.dataset.done = "1"; }
      rest.hidden = false; btn.textContent = "collapse"; markSame(); drawArrows();
    };
    btn.onclick = () => { if (rest.hidden) expand(); else { rest.hidden = true; btn.textContent = "show all"; drawArrows(); } };
    for (let j = it.i + it.p; j < it.i + n; j++) S.lazy.set(rows[j].pc, expand);
    const box = h("div", { class: "rep" }, h("div", { class: "rep-head" }, h("b", {}, "× " + it.reps),
      (it.p === 1 ? "the same instruction" : `the same ${it.p} instructions`) + `, ${first.pc.toString(16)} to ${last.pc.toString(16)}`, btn));
    build(box, rows, keys, it.i, it.i + it.p, true);
    box.append(rest);
    parent.append(box);
  }
}
function renderListing() {
  const K = S.kernel, rows = K.rows;
  S.rowEl = new Map(); S.lazy = new Map();
  const root = h("div", { id: "listing", class: $("#words").checked ? "show-words" : "" });
  root.append(document.createElementNS("http://www.w3.org/2000/svg", "svg"));
  root.firstChild.id = "arrows";
  const keys = rows.map(foldKey);
  build(root, rows, keys, 0, rows.length, $("#fold").checked);
  root.append(h("div", { class: "endnote" }, `${K.size.toString(16)}:  j FW_${K.role.toUpperCase()}+4    return to firmware, linked when the kernel is installed`));
  $("#view").replaceChildren(root);
  drawArrows();
}
function reveal(pc) {
  if (!S.rowEl.has(pc) && S.lazy.has(pc)) S.lazy.get(pc)();
  let el = S.rowEl.get(pc);
  for (let guard = 0; el && !el.offsetParent && guard < 4; guard++) {  // inside a collapsed block
    const hiddenBox = el.closest("[hidden]");
    if (!hiddenBox) break;
    hiddenBox.hidden = false;
    const btn = hiddenBox.parentElement.querySelector(":scope > .rep-head button");
    if (btn) btn.textContent = "collapse";
  }
  return el;
}
function drawArrows() {
  const svg = $("#arrows"), L = $("#listing");
  if (!svg || !S.kernel) return;
  svg.setAttribute("height", 0);  // so the old height does not hold the listing open while it is measured
  const edges = [];
  for (const row of S.kernel.rows) {
    if (row.back == null || row.target == null) continue;
    const a = S.rowEl.get(row.pc), b = S.rowEl.get(row.target);
    if (!a || !b || !a.offsetParent || !b.offsetParent) continue;
    edges.push({ from: row.pc, to: row.target, y1: a.offsetTop + a.offsetHeight / 2, y2: b.offsetTop + b.offsetHeight / 2, back: row.back });
  }
  edges.sort((p, q) => Math.abs(p.y2 - p.y1) - Math.abs(q.y2 - q.y1));
  const lanes = [];
  let d = "";
  const paths = [];
  for (const e of edges) {
    const lo = Math.min(e.y1, e.y2), hi = Math.max(e.y1, e.y2);
    let lane = 0;
    while (lane < 6 && (lanes[lane] || []).some(([a, b]) => lo <= b + 3 && hi >= a - 3)) lane++;
    if (lane === 6) continue;
    (lanes[lane] = lanes[lane] || []).push([lo, hi]);
    const x = 40 - lane * 6;
    paths.push(`<path class="${e.back ? "back" : "fwd"}" data-from="${e.from}" data-to="${e.to}" d="M47 ${e.y1} H${x} V${e.y2} H47 m-4 -3 l4 3 l-4 3"/>`);
  }
  svg.setAttribute("height", L.scrollHeight);
  svg.setAttribute("width", 48);
  svg.innerHTML = paths.join("");
  hotArrows();
}
function hotArrows() {
  for (const p of document.querySelectorAll("#arrows path")) p.classList.toggle("hot", S.sel != null && (+p.dataset.from === S.sel || +p.dataset.to === S.sel));
}

// ----------------------------------------------------------------------------------------------------------- selection
function markSame() {
  for (const el of document.querySelectorAll(".row.same")) el.classList.remove("same");
  const row = S.byPc.get(S.sel);
  if (!row || !row.sym) return;
  for (const r of S.refs.get(row.sym) || []) S.rowEl.get(r.pc)?.classList.add("same");
}
function select(pc, opts = {}) {
  document.querySelector(".row.sel")?.classList.remove("sel");
  S.sel = pc != null && S.byPc.has(pc) ? pc : null;
  if (S.sel != null) {
    const el = reveal(S.sel);
    if (el) {
      el.classList.add("sel");
      if (opts.scroll) el.scrollIntoView({ block: "center" });
      if (opts.flash) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
    }
    if (opts.scroll) drawArrows();
  }
  markSame(); hotArrows(); markOutline();
  if (!opts.keepSide) renderSide();
  const want = makeHash(S.model, S.program, S.file, S.sel);
  if (location.hash !== want) history.replaceState(null, "", want);
}
function jumpTo(pc) {  // keeps the place you came from in browser history
  if (!S.byPc.has(pc)) return;
  history.pushState(null, "", makeHash(S.model, S.program, S.file, pc));
  select(pc, { scroll: true, flash: true });
}
function visibleRows() { return [...document.querySelectorAll("#listing .row")].filter(e => e.offsetParent); }
function step(delta) {
  const els = visibleRows();
  if (!els.length) return;
  let i = els.findIndex(e => +e.dataset.pc === S.sel);
  i = i < 0 ? 0 : Math.max(0, Math.min(els.length - 1, i + delta));
  select(+els[i].dataset.pc);
  els[i].scrollIntoView({ block: "nearest" });
}

// ---------------------------------------------------------------------------------------------------------------- side
const refLink = (r, cls) => h("a", { onclick: () => jumpTo(r.pc) }, h("span", { class: "pc" }, r.pc.toString(16)), h("span", { class: "t " + (cls || "") }, rowText(r).replace(/^\S+ /, "")));
function ttBlock(d, heading) {
  const doc = S.isa[d.op] || {};
  const meaning = Object.fromEntries((doc.fields || []).map(f => [f.name, f]));
  const out = [h("h3", {}, heading)];
  out.push(h("p", { class: "big" }, h("b", {}, d.op), doc.title ? "  " + doc.title : ""));
  if (doc.summary) out.push(h("p", { class: "sub" }, doc.summary));
  if (d.args.length) out.push(h("table", { class: "t" }, h("tr", {}, h("th", {}, "field"), h("th", {}, "bits"), h("th", {}, "value"), h("th", {}, "meaning")),
    d.args.map(([name, value, label]) => h("tr", {}, h("td", {}, name), h("td", { class: "bits" }, meaning[name] ? `${meaning[name].hi}:${meaning[name].lo}` : ""),
      h("td", {}, String(value), value > 9 ? h("span", { class: "bits" }, " " + hex(value)) : null),
      h("td", {}, label ? h("div", {}, label) : null, meaning[name]?.meaning ? h("div", { class: "mean" }, meaning[name].meaning) : null)))));
  if (doc.constants?.length) out.push(h("details", {}, h("summary", { class: "sub" }, "Named constants"), h("ul", {}, doc.constants.map(c => h("li", { class: "big" }, c)))));
  if (doc.notes?.length) out.push(h("details", { open: d.args.length < 6 }, h("summary", { class: "sub" }, "Notes from the instruction reference"), h("ul", {}, doc.notes.map(n => h("li", {}, n)))));
  if (doc.manual) out.push(h("p", {}, h("a", { class: "ext", href: doc.manual, target: "_blank", rel: "noopener" }, "Open the ISA manual page")));
  return out;
}
function configBlock(c) {
  return [h("h3", {}, `Configuration register ${c.group}[${c.index}], ${c.bank}`),
    c.fields.length ? h("table", { class: "t" }, h("tr", {}, h("th", {}, "bits"), h("th", {}, "field"), h("th", {}, "value")),
      c.fields.map(f => h("tr", {}, h("td", { class: "bits" }, f.hi === f.lo ? String(f.lo) : `${f.hi}:${f.lo}`), h("td", {}, f.name),
        h("td", {}, f.value == null ? h("span", { class: "sub" }, "set at run time") : String(f.value), f.label ? h("div", { class: "mean" }, f.label) : null, f.partial ? h("div", { class: "mean" }, "only the masked bits change") : null))))
      : h("p", { class: "sub" }, "No field names are known for this word.")];
}
function expandBlock(x) {
  const item = it => h("div", {}, it.times ? h("span", { class: "x" }, `× ${it.times}  `) : null, it.slot != null ? h("span", { class: "g" }, `[${it.slot}] `) : null,
    h("b", {}, it.op), " ", h("span", { class: "g" }, it.gist || it.text), it.sub ? h("div", { class: "subx" }, it.sub.map(item)) : null);
  return [h("h3", {}, x.kind === "mop" ? "What this MOP expands to" : "What this replay plays"),
    x.note ? h("p", { class: "sub" }, x.note + (x.total ? `, ${x.total} instructions in total` : "")) : null,
    h("div", { class: "exp" }, x.items.map(item)),
    h("p", { class: "mean" }, "Worked out from the template and replay writes that come before this row in the listing, so it is only right if no other path reprograms them.")];
}
function paramBlock(name) {
  const p = curProgram().params.find(q => q.name === name);
  if (!p) return [];
  const out = [h("h3", {}, `Launch parameter ${name}`),
    h("div", { class: "kv" }, h("span", { class: "k" }, "kind"), h("span", {}, p.kind === "uniform" ? "uniform, the same on every core, sent with each launch" : "per core, read from the core's resident table"),
      h("span", { class: "k" }, "L1 address"), h("span", {}, hex(p.addr)))];
  if (p.kind === "per-core") {
    const vs = p.per_core, lo = Math.min(...vs), hi = Math.max(...vs);
    out.push(h("p", { class: "sub" }, p.varies ? `Differs between cores: ${lo > 99999 ? hex(lo) : lo} to ${hi > 99999 ? hex(hi) : hi} over ${vs.length} cores.` : "The same on every core."));
  } else if (p.varies) out.push(h("p", { class: "sub" }, `Changes between the ${curProgram().launches} launches of one token. First values:`));
  out.push(h("table", { class: "t" }, p.values.slice(0, 8).map(v => h("tr", {}, h("td", {}, v.text), h("td", { class: "note" }, v.note)))));
  if (p.combined) out.push(h("p", { class: "sub" }, `Together with its partner word this loads ${p.combined.name} as an FP32 constant: ${p.combined.values.slice(0, 6).join(", ")}${p.combined.values.length > 6 ? ", …" : ""}`));
  return out;
}
function renderSide() {
  const side = $("#side-body");
  if (!S.kernel) return;
  const row = S.byPc.get(S.sel);
  if (!row) return side.replaceChildren(...kernelSummary());
  const out = [h("h2", {}, row.op + " " + (row.kind === "tt" ? "" : (row.operands || "") + (row.tlabel || ""))),
    h("p", { class: "sub big" }, `pc ${hex(row.pc)}   word ${hex8(row.word)}` + (row.kind === "tt" ? `   Tensix ${hex8(row.tword)}` : ""))];
  if (row.ann.length) out.push(h("div", { class: "gistbox" }, row.ann.map(a => h("div", {}, annNodes({ ...row, ann: [a] })))));
  if (row.func) out.push(h("p", { class: "sub" }, `Entry of ${row.func.name}` + (row.func.title ? `: ${row.func.title}.` : ".")));
  if (row.kind === "rv" && rvMeaning(row)) out.push(h("p", { class: "sub" }, rvMeaning(row)));
  if (row.kind === "tt") out.push(...ttBlock(row, "Tensix instruction"));
  if (row.kind === "data" && row.detail?.table) out.push(h("h3", {}, "Embedded data"), h("p", { class: "sub" }, `Part of the table at ${hex(row.detail.table.start)}: 16-bit NoC coordinates (x | y << 6), one per DRAM bank, indexed by the bank a tile lives in.`));
  if (row.mem) {
    const m = row.mem;
    out.push(h("h3", {}, m.rw === "w" ? `Stores ${m.width * 8} bits to` : `Loads ${m.width * 8} bits from`));
    if (m.name) out.push(h("p", { class: "big" }, h("span", { class: nmClass(m.name) }, m.name)), h("div", { class: "kv" },
      h("span", { class: "k" }, "address"), h("span", {}, hex8(m.addr) + (m.approx ? " plus a run-time offset" : "")), h("span", { class: "k" }, "region"), h("span", {}, m.region),
      m.value != null ? [h("span", { class: "k" }, "value"), h("span", {}, typeof m.value === "number" ? `${hex8(m.value)}  (${m.value})` : String(m.value))] : null),
      m.desc ? h("p", { class: "sub" }, m.desc) : null);
    else out.push(h("p", { class: "sub" }, m.expr ? `Address computed at run time: ${m.expr}` : "The address depends on register values that are only known at run time."));
  }
  if (row.embedded) out.push(...ttBlock(row.embedded, row.mem.name.startsWith("MOP_CFG") ? "Instruction placed in the MOP template" : "Instruction pushed to the Tensix thread"));
  if (row.config) out.push(...configBlock(row.config));
  if (row.expand) out.push(...expandBlock(row.expand));
  if (row.sym?.startsWith("param:")) out.push(...paramBlock(row.sym.slice(6)));
  if (row.call && S.byPc.get(row.target)?.func) {
    const f = S.byPc.get(row.target).func;
    out.push(h("h3", {}, "Calls"), h("div", { class: "refs" }, h("a", { onclick: () => jumpTo(f.pc) }, h("span", { class: "pc" }, f.pc.toString(16)), h("span", { class: "t" }, `${f.name}  ${f.title || ""}`))));
  }
  if (row.regs) out.push(h("h3", {}, "Register values going in"), h("div", { class: "kv" }, Object.entries(row.regs).flatMap(([r, v]) => [h("span", { class: "k" }, r), h("span", {}, typeof v === "number" ? `${hex8(v)}  (${v})` : String(v))])));
  const from = S.jumps.get(row.pc);
  if (from?.length) out.push(h("h3", {}, `Jumps that land here (${from.length})`), h("div", { class: "refs" }, from.map(r => refLink(r))));
  if (row.func?.callers.length) out.push(h("h3", {}, `Called from (${row.func.callers.length})`), h("div", { class: "refs" }, row.func.callers.map(pc => refLink(S.byPc.get(pc)))));
  const refs = row.sym ? (S.refs.get(row.sym) || []).filter(r => r.pc !== row.pc) : [];
  if (refs.length) out.push(h("h3", {}, `Other rows in this kernel that touch it (${refs.length})`),
    h("div", { class: "refs" }, refs.slice(0, 80).map(r => refLink(r, r.mem?.rw === "w" || r.config ? "w" : r.mem ? "r" : ""))));
  side.replaceChildren(...out);
  side.scrollTop = 0;
}
function kernelSummary() {
  const K = S.kernel, p = curProgram();
  const used = [...S.refs.keys()].filter(k => k.startsWith("param:")).map(k => k.slice(6));
  const out = [h("h2", {}, `${S.program} / ${S.file}`), h("p", { class: "sub" }, S.index.roles[K.role] || K.role),
    h("p", { class: "sub" }, "Select a row to see what it does: decoded fields, the register it touches, and every other row that touches the same thing.")];
  if (used.length) out.push(h("h3", {}, "Launch parameters this kernel reads"), h("table", { class: "t" }, used.map(name => {
    const q = p.params.find(x => x.name === name), first = S.refs.get("param:" + name)[0];
    return h("tr", { class: "pick", onclick: () => jumpTo(first.pc) }, h("td", {}, hex(q.addr)), h("td", {}, h("span", { class: "nm param" }, name)),
      h("td", { class: "note" }, (q.kind === "per-core" ? "per core" : q.varies ? "per layer" : q.values[0]?.kind === "dynamic" ? "per token" : "fixed") + (q.values[0]?.note && q.kind !== "per-core" ? ": " + q.values[0].note : "")));
  })));
  const cbs = Object.entries(K.cbs);
  if (cbs.length) out.push(h("h3", {}, "Circular buffers"), h("table", { class: "t" }, h("tr", {}, h("th", {}, "CB"), h("th", {}, "L1 base"), h("th", {}, "this RISC is the")),
    cbs.map(([i, cb]) => h("tr", {}, h("td", {}, h("span", { class: "nm cb" }, "CB" + i)), h("td", {}, hex(cb.base)), h("td", { class: "note" }, cb.sides.join(" and "))))),
    h("p", { class: "mean" }, "Matched from the pointer and count each kernel keeps in private memory and the shared tile counters it updates."));
  if (K.funcs.length) out.push(h("h3", {}, "Subroutines"), h("div", { class: "refs" }, K.funcs.map(f => h("a", { onclick: () => jumpTo(f.pc) }, h("span", { class: "pc" }, f.pc.toString(16)), h("span", { class: "t" }, `${f.title || f.name}  (${f.callers.length}×)`)))));
  out.push(h("h3", {}, "Keys"), h("div", { class: "kv" },
    ...[["↑ ↓ or j k", "move between rows"], ["Enter", "follow a jump or call"], ["Backspace", "go back to where you jumped from"], ["/", "find in this kernel, Enter for the next match"],
      ["Ctrl K or g", "jump to any kernel, subroutine, label or pc"], ["[ ]", "previous or next RISC of this program"], ["b  i", "hide or show the kernel list, this panel"], ["Esc", "clear the selection"]]
      .flatMap(([k, v]) => [h("span", { class: "k" }, k), h("span", { class: "sub", style: "font-family:var(--sans)" }, v)])));
  return out;
}
function loopText(head) {
  const end = Math.max(...S.jumps.get(head.pc).filter(r => r.back).map(r => r.pc));
  const cond = head.ann.find(a => a[0] === "note" && a[1].startsWith("if "));
  if (cond) return "loop until " + cond[1].slice(3);
  for (let pc = head.pc; pc <= end; pc += 4) {
    const r = S.byPc.get(pc);
    for (const a of r?.ann || []) {
      if (a[0] === "load") return "loop: poll " + a[1];
      if (a[0] === "store") return "loop: write " + a[1];
      if (a[0] === "call") return "loop: " + a[1];
      if (a[0] === "gist") return "loop: " + r.op + " …";
    }
  }
  return "loop";
}
function rvMeaning(row) {
  const o = (row.operands || "").split(",").map(x => x.trim()), [a, b, c] = o;
  const bin = { add: "+", sub: "-", mul: "×", divu: "÷ (unsigned)", remu: "mod (unsigned)", and: "&", or: "|", xor: "^", sll: "<<", srl: ">>", addi: "+", andi: "&", ori: "|", xori: "^", slli: "<<", srli: ">> (logical)", srai: ">> (arithmetic)" }[row.op];
  if (bin) return `${a} = ${b} ${bin} ${c}`;
  const t = { lui: `${a} = ${b} << 12 (upper 20 bits; the next addi usually fills in the rest)`, auipc: `${a} = pc + (${b} << 12): an address relative to this instruction, used to reach data inside the image`,
    li: `${a} = ${b}`, mv: `${a} = ${b}`, sltu: `${a} = ${b} < ${c} ? 1 : 0 (unsigned)`, sltiu: `${a} = ${b} < ${c} ? 1 : 0 (unsigned)`, min: `${a} = min(${b}, ${c}) (signed)`,
    fence: "RISC-V memory fence. The kernels use it after polling or writing shared state so stores and loads are not reordered around it",
    ret: "return to the caller (jalr x0, 0(x1))", call: "call: x1 = return address, jump to the subroutine", j: "unconditional jump",
    beq: "branch if equal", bne: "branch if not equal", blt: "branch if less than (signed)", bge: "branch if greater or equal (signed)", bltu: "branch if less than (unsigned)", bgeu: "branch if greater or equal (unsigned)" }[row.op];
  return t || "";
}
function renderOutline() {
  const box = $("#outline");
  if (!S.kernel) return box.replaceChildren(h("div", { class: "empty" }, "Open one of the five RISC kernels of a program to see its subroutines and loops here."));
  const items = [];
  for (const row of S.kernel.rows) {
    if (row.func) items.push(h("a", { class: "fn", "data-pc": row.pc, title: row.func.title || row.func.name, onclick: () => jumpTo(row.pc) }, h("span", { class: "pc" }, row.pc.toString(16)), h("span", { class: "t" }, row.func.title || row.func.name)));
    else if (row.label && (S.jumps.get(row.pc) || []).some(r => r.back)) {
      const text = loopText(row);
      items.push(h("a", { class: "loop", "data-pc": row.pc, title: text, onclick: () => jumpTo(row.pc) }, h("span", { class: "pc" }, row.pc.toString(16)), h("span", { class: "t" }, text)));
    } else if (row.label?.startsWith("tbl_")) items.push(h("a", { "data-pc": row.pc, onclick: () => jumpTo(row.pc) }, h("span", { class: "pc" }, row.pc.toString(16)), h("span", { class: "t" }, "DRAM bank coordinate table")));
  }
  box.replaceChildren(...(items.length ? items : [h("div", { class: "empty" }, "Straight-line code: no loops or subroutines.")]));
  markOutline();
}
function markOutline() {  // the outline entry the selected row falls under
  let here = null;
  for (const a of document.querySelectorAll("#outline a[data-pc]")) { a.classList.remove("here"); if (S.sel != null && +a.dataset.pc <= S.sel) here = a; }
  if (here) { here.classList.add("here"); here.scrollIntoView({ block: "nearest" }); }
}

// ------------------------------------------------------------------------------------------------------------ overview
function renderOverview() {
  const mm = curModel(), p = curProgram();
  const variantOf = new Map();
  for (const k of p.kernels) if (k.variant != null && k.role === "brisc") for (const c of k.cores) variantOf.set(c.join(), k.variant);
  const pick = S.pickParam && p.params.find(q => q.name === S.pickParam && q.kind === "per-core");
  const inProg = new Map(p.cores.map((c, i) => [c.join(), i]));
  const xs = Array.from({ length: 16 }, (_, i) => i + 1), ys = Array.from({ length: 10 }, (_, i) => i + 2);
  const base = pick ? Math.min(...pick.per_core) : 0;
  const cell = (x, y) => {
    if (x === 8 || x === 9) return h("div", { class: "c gap" });
    const i = inProg.get(`${x},${y}`);
    if (i == null) return h("div", { class: "c", title: `(${x},${y}) not used by ${p.name}` });
    const tip = `(${x},${y})\n` + p.params.filter(q => q.kind === "per-core").map(q => `${q.name} = ${q.per_core[i] > 99999 ? hex(q.per_core[i]) : q.per_core[i]}`).join("\n");
    const text = pick ? (base > 99999 ? "+" + (pick.per_core[i] - base) : String(pick.per_core[i])) : "";
    return h("div", { class: "c on" + (variantOf.get(`${x},${y}`) ? " v1" : ""), title: tip }, text);
  };
  const grid = h("div", { class: "grid", style: "grid-template-columns: repeat(17, max-content)" },
    h("div", { class: "c ax" }), xs.map(x => h("div", { class: "c ax" }, x === 8 || x === 9 ? "" : String(x))),
    ys.map(y => [h("div", { class: "c ax" }, String(y)), xs.map(x => cell(x, y))]));
  const valueCell = q => q.kind === "per-core"
    ? (q.varies ? `${Math.min(...q.per_core) > 99999 ? hex(Math.min(...q.per_core)) : Math.min(...q.per_core)} … ${Math.max(...q.per_core) > 99999 ? hex(Math.max(...q.per_core)) : Math.max(...q.per_core)}` : q.values[0].text)
    : q.values[0]?.text + (q.varies ? "  …" : "");
  const noteCell = q => (q.combined ? `${q.combined.name} = ${q.combined.values.slice(0, 3).join(", ")}${q.combined.values.length > 3 ? ", …" : ""}; ` : "") + (q.values[0]?.note || "") +
    (q.kind === "uniform" && q.varies ? `  (changes per layer, ${q.values.length}${q.values.length === 40 ? "+" : ""} distinct values)` : "");
  const view = h("div", { id: "overview" },
    h("h2", {}, p.name),
    h("p", { class: "lede" }, `Runs on ${p.cores.length} Tensix cores, launched ${p.launches} time${p.launches === 1 ? "" : "s"} per token. Each core runs up to five kernels at once, one per RISC-V: two move data over the NoC, three drive the Tensix unpack, math and pack threads.`),
    h("h3", {}, "Kernels"),
    h("div", { class: "kcards" }, p.kernels.map(k => h("button", { class: "kcard", onclick: () => go(S.model, p.name, k.file) },
      h("div", { class: "r" }, k.file), h("div", { class: "d" }, ROLE_JOB[k.role]), h("div", { class: "d" }, `${k.size} bytes, ${k.size / 4} words` + (k.variant != null ? `, ${k.cores.length} cores` : ""))))),
    h("h3", {}, "Launch parameters"),
    h("table", { class: "t" }, h("tr", {}, h("th", {}, "L1 address"), h("th", {}, "name"), h("th", {}, "scope"), h("th", {}, "value"), h("th", {}, "what it is")),
      p.params.map(q => h("tr", { class: q.kind === "per-core" ? "pick" + (S.pickParam === q.name ? " on" : "") : "", title: q.kind === "per-core" ? "Show this value on the core map" : null,
        onclick: q.kind === "per-core" ? () => { S.pickParam = S.pickParam === q.name ? null : q.name; renderOverview(); } : null },
        h("td", {}, hex(q.addr)), h("td", {}, h("span", { class: "nm param" }, q.name)), h("td", { class: "scope" }, q.kind === "uniform" ? "every core" : "per core"),
        h("td", {}, valueCell(q)), h("td", { class: "note" }, noteCell(q))))),
    h("p", { class: "gridnote" }, "DRAM addresses are per-bank offsets; the low three bits pick the bank the first tile sits in. Click a per-core row to see its values on the map."),
    h("h3", {}, "Cores" + (pick ? `, showing ${pick.name}` + (base > 99999 ? ` relative to ${hex(base)}` : "") : "")),
    grid,
    h("p", { class: "gridnote" }, "NoC coordinates, x across and y down. Columns 8 and 9 are not Tensix." + (variantOf.size ? " The two colours are the two BRISC/NCRISC image variants." : "")),
    h("h3", {}, "L1 layout shared by every kernel of this model"),
    h("table", { class: "t" }, [["FW_BRISC … FW_TRISC2", hex(S.index.abi.FW_BRISC ?? 0x20), "resident firmware, one image per RISC"],
      ["L1_PARAM_BASE", hex(mm.layout.l1_param_base), "uniform parameters, 16 words"],
      ["code slot 0, slot 1", `${hex(S.index.abi.CODE_BRISC ?? 0x800)}, ${hex((S.index.abi.CODE_BRISC ?? 0x800) + (S.index.abi.SLOT_STRIDE ?? 0x7040))}`, "kernel images, double buffered; kernels are position independent"],
      ["per-core tables", hex(mm.layout.static_base), `0x40 bytes per program; ${p.name} is table ${p.k} at ${hex(mm.layout.static_base + 0x40 * p.k)}`],
      ...mm.persistent.map(x => [x.name, hex(x.addr), `${x.size} bytes that survive across launches`]),
      ["kernel data", hex(mm.layout.l1_data_base), "circular buffers and scratch tiles, up to the top of L1 (0x180000)"]]
      .map(([a, b, c]) => h("tr", {}, h("td", {}, a), h("td", {}, b), h("td", { class: "note" }, c)))));
  $("#view").replaceChildren(view);
  $("#view").scrollTop = 0;
  $("#side-body").replaceChildren(h("h2", {}, mm.id), h("p", { class: "sub" }, mm.note || ""),
    h("h3", {}, "DRAM buffers the kernels pass around"),
    h("table", { class: "t buffers" }, mm.buffers.map(b => h("tr", { title: `${b.size} bytes` + (b.src ? `\n${b.src}` : "") }, h("td", {}, hex(b.addr)), h("td", { class: "name" }, b.name), h("td", { class: "size" }, fmtSize(b.size))))));
}

// ---------------------------------------------------------------------------------------------------------------- find
function runFind(moveToFirst) {
  const q = $("#find").value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  for (const el of document.querySelectorAll(".row.hit")) el.classList.remove("hit");
  S.hits = []; S.hitSet = new Set();
  if (q.length && S.kernel) {
    for (const row of S.kernel.rows) if (q.every(w => S.text.get(row.pc).includes(w))) { S.hits.push(row.pc); S.hitSet.add(row.pc); S.rowEl.get(row.pc)?.classList.add("hit"); }
  }
  $("#find-count").textContent = q.length ? `${S.hits.length} found` : "";
  if (moveToFirst && S.hits.length) nextHit(1, true);
}
function nextHit(dir, fromTop) {
  if (!S.hits.length) return;
  let i = fromTop ? 0 : S.hits.findIndex(pc => dir > 0 ? pc > (S.sel ?? -1) : pc >= (S.sel ?? Infinity));
  if (!fromTop) i = dir > 0 ? (i < 0 ? 0 : i) : ((i < 0 ? S.hits.length : i) - 1 + S.hits.length) % S.hits.length;
  select(S.hits[i], { scroll: true });
  $("#find-count").textContent = `${i + 1} of ${S.hits.length}`;
}
async function findEverywhere() {
  const q = $("#find").value.trim();
  if (!q) return;
  const side = $("#side-body");
  side.replaceChildren(h("h2", {}, `Searching every kernel of ${S.model}…`));
  const hits = await api(`/api/search?model=${S.model}&q=${encodeURIComponent(q)}`);
  side.replaceChildren(h("h2", {}, `“${q}” in ${S.model}`), h("p", { class: "sub" }, hits.length ? `${hits.length}${hits.length >= 400 ? "+" : ""} rows` : "Nothing matches. Try fewer words; every word has to appear in the row."),
    h("div", { class: "hits" }, hits.map(x => h("a", { title: x.text, onclick: async () => { history.pushState(null, "", makeHash(S.model, x.program, x.file, x.pc)); await route(); } },
      h("span", { class: "k" }, `${x.program}/${x.file}`), h("span", { class: "pc" }, x.pc.toString(16)), h("span", { class: "t" }, x.text)))));
}

// ------------------------------------------------------------------------------------------------------------- palette
let palItems = [], palAt = 0;
function paletteSource() {
  const out = [];
  const mm = curModel();
  if (S.kernel) {
    for (const f of S.kernel.funcs) out.push({ kind: "sub", text: `${f.title || f.name}`, where: f.pc.toString(16), run: () => jumpTo(f.pc) });
    for (const [sym, rows] of S.refs) if (sym.startsWith("param:")) out.push({ kind: "param", text: sym.slice(6), where: `${rows.length} rows`, run: () => jumpTo(rows[0].pc) });
    for (const row of S.kernel.rows) if (row.label && !row.func) out.push({ kind: "label", text: row.label, where: row.pc.toString(16), run: () => jumpTo(row.pc) });
  }
  for (const p of mm.programs) {
    out.push({ kind: "program", text: p.name, where: "overview", run: () => go(S.model, p.name) });
    for (const k of p.kernels) out.push({ kind: "kernel", text: `${p.name} / ${k.file}`, where: `${ROLE_JOB[k.role]} (${ROLE_SHORT[k.role]})`, run: () => go(S.model, p.name, k.file) });
  }
  for (const m of S.index.models) if (m.id !== S.model) out.push({ kind: "model", text: m.id, where: "same kernel, other model", run: () => go(m.id, S.program, S.file) });
  return out;
}
function paletteFilter() {
  const q = $("#palette-in").value.trim().toLowerCase();
  const words = q.split(/\s+/).filter(Boolean);
  palItems = paletteSource().filter(it => words.every(w => (it.kind + " " + it.text + " " + it.where).toLowerCase().includes(w)));
  const pc = /^(0x|@)?[0-9a-f]+$/.test(q) ? parseInt(q.replace(/^(0x|@)/, ""), 16) & ~3 : null;
  if (pc != null && S.byPc.has(pc)) palItems.unshift({ kind: "pc", text: `go to ${hex(pc)}`, where: rowText(S.byPc.get(pc)).slice(0, 60), run: () => jumpTo(pc) });
  palItems = palItems.slice(0, 80);
  palAt = 0;
  paletteDraw();
}
function paletteDraw() {
  $("#palette-list").replaceChildren(...palItems.map((it, i) => h("div", { class: i === palAt ? "cur" : "", onclick: () => paletteRun(i) },
    h("span", { class: "kind" }, it.kind), h("span", {}, it.text), h("span", { class: "where" }, it.where))));
  $("#palette-list").children[palAt]?.scrollIntoView({ block: "nearest" });
}
function paletteOpen() { $("#palette").hidden = false; $("#palette-in").value = ""; paletteFilter(); $("#palette-in").focus(); }
function paletteClose() { $("#palette").hidden = true; $("#view").focus(); }
function paletteRun(i) { const it = palItems[i]; paletteClose(); if (it) it.run(); }

// -------------------------------------------------------------------------------------------------------------- panels
const PANEL = { rail: { min: 180, max: 480, def: 270 }, side: { min: 260, max: 760, def: 340 } };
function panelState() {
  try { return JSON.parse(localStorage.getItem("kview-panels")) || {}; } catch { return {}; }
}
function applyPanels() {
  const st = panelState(), app = $("#app");
  for (const name of Object.keys(PANEL)) {
    const w = Math.max(PANEL[name].min, Math.min(PANEL[name].max, st[name + "W"] || PANEL[name].def));
    app.style.setProperty(`--${name}-w`, w + "px");
    app.classList.toggle("no-" + name, !!st[name + "Hidden"]);
    $("#toggle-" + name).classList.toggle("off", !!st[name + "Hidden"]);
  }
}
function savePanels(patch) { localStorage.setItem("kview-panels", JSON.stringify({ ...panelState(), ...patch })); applyPanels(); }
function togglePanel(name) { savePanels({ [name + "Hidden"]: !panelState()[name + "Hidden"] }); }
function wirePanels() {
  applyPanels();
  $("#toggle-rail").addEventListener("click", () => togglePanel("rail"));
  $("#toggle-side").addEventListener("click", () => togglePanel("side"));
  for (const grip of document.querySelectorAll(".grip")) {
    const name = grip.dataset.panel;
    grip.addEventListener("dblclick", () => togglePanel(name));
    grip.addEventListener("pointerdown", e => {
      e.preventDefault();
      grip.setPointerCapture(e.pointerId);
      grip.classList.add("on"); $("#app").classList.add("dragging");
      const { min, max } = PANEL[name];
      let w = null;
      const move = ev => {
        w = Math.round(Math.max(min, Math.min(max, name === "rail" ? ev.clientX : innerWidth - ev.clientX)));
        $("#app").style.setProperty(`--${name}-w`, w + "px");
      };
      const up = () => {
        grip.removeEventListener("pointermove", move); grip.removeEventListener("pointerup", up);
        grip.classList.remove("on"); $("#app").classList.remove("dragging");
        if (w != null) savePanels({ [name + "W"]: w });
      };
      grip.addEventListener("pointermove", move); grip.addEventListener("pointerup", up);
    });
  }
  // rows wrap to the width of the listing, so the jump arrows have to follow any change in it
  let queued = false, lastW = 0;
  new ResizeObserver(([e]) => {
    if (Math.abs(e.contentRect.width - lastW) < 1 || queued) return;
    lastW = e.contentRect.width; queued = true;
    requestAnimationFrame(() => { queued = false; drawArrows(); });
  }).observe($("#view"));
}

// -------------------------------------------------------------------------------------------------------------- events
function wire() {
  wirePanels();
  $("#view").addEventListener("click", e => {
    const t = e.target.closest("[data-target]");
    if (t) { jumpTo(+t.dataset.target); return; }
    const row = e.target.closest(".row");
    if (row) select(+row.dataset.pc);
  });
  $("#view").addEventListener("dblclick", e => {
    const row = e.target.closest(".row");
    const r = row && S.byPc.get(+row.dataset.pc);
    if (r && r.target != null) jumpTo(r.target);
  });
  $("#fold").addEventListener("change", () => { renderListing(); select(S.sel, { scroll: true, keepSide: true }); });
  $("#words").addEventListener("change", () => { $("#listing")?.classList.toggle("show-words", $("#words").checked); });
  $("#find").addEventListener("input", () => runFind(false));
  $("#find").addEventListener("keydown", e => {
    if (e.key === "Enter") { if ($("#find-all").checked) findEverywhere(); else nextHit(e.shiftKey ? -1 : 1); }
    if (e.key === "Escape") { $("#find").value = ""; runFind(false); $("#view").focus(); }
  });
  $("#open-palette").addEventListener("click", paletteOpen);
  $("#palette").addEventListener("click", e => { if (e.target.id === "palette") paletteClose(); });
  $("#palette-in").addEventListener("input", paletteFilter);
  $("#palette-in").addEventListener("keydown", e => {
    if (e.key === "ArrowDown") { palAt = Math.min(palItems.length - 1, palAt + 1); paletteDraw(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { palAt = Math.max(0, palAt - 1); paletteDraw(); e.preventDefault(); }
    else if (e.key === "Enter") paletteRun(palAt);
    else if (e.key === "Escape") paletteClose();
  });
  $("#theme").addEventListener("click", () => {
    const light = document.documentElement.classList.toggle("light");
    localStorage.setItem("kview-theme", light ? "light" : "dark");
  });
  window.addEventListener("popstate", route);
  document.addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); paletteOpen(); return; }
    if (e.target.matches?.("input, textarea") || !$("#palette").hidden || e.ctrlKey || e.metaKey || e.altKey) return;
    const row = S.byPc.get(S.sel);
    if (e.key === "g") { e.preventDefault(); paletteOpen(); }
    else if (e.key === "b") togglePanel("rail");
    else if (e.key === "i") togglePanel("side");
    else if (e.key === "/") { e.preventDefault(); $("#find").focus(); $("#find").select(); }
    else if (!S.kernel) return;
    else if (e.key === "j" || e.key === "ArrowDown") { e.preventDefault(); step(1); }
    else if (e.key === "k" || e.key === "ArrowUp") { e.preventDefault(); step(-1); }
    else if (e.key === "PageDown") { e.preventDefault(); step(25); }
    else if (e.key === "PageUp") { e.preventDefault(); step(-25); }
    else if (e.key === "Enter" && row && row.target != null) jumpTo(row.target);
    else if (e.key === "Backspace") { e.preventDefault(); history.back(); }
    else if (e.key === "n") nextHit(1);
    else if (e.key === "N") nextHit(-1);
    else if (e.key === "Escape") select(null);
    else if (e.key === "[" || e.key === "]") {
      const ks = curProgram().kernels, i = ks.findIndex(k => k.file === S.file);
      const next = ks[(i + (e.key === "]" ? 1 : ks.length - 1)) % ks.length];
      go(S.model, S.program, next.file);
    }
  });
}

async function main() {
  if (localStorage.getItem("kview-theme") === "light") document.documentElement.classList.add("light");
  wire();
  try { [S.index, S.isa] = await Promise.all([api("/api/index"), api("/api/isa")]); }
  catch (e) { $("#view").replaceChildren(h("div", { id: "overview" }, h("h2", {}, "The reader's server is not answering"), h("p", { class: "lede" }, "Start it with python kview/serve.py and reload. " + e.message))); return; }
  await route();
}
main();
