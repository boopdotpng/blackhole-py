// Shared model code for the packer and unpacker explorers.
// Pure functions (formats, BFP, compression, the program parser) work in node too: `node test_models.mjs`.
(function (root) {
"use strict";

// ***** data formats *****
// code = the 4-bit value the hardware registers hold (tensix_types.h DataFormat & 0xF)
const FORMATS = {
  0:  {code: 0,  name: "FP32",  llk: "Float32",   bytes: 4,    kind: "float", E: 8, M: 23, bias: 127},
  1:  {code: 1,  name: "FP16",  llk: "Float16",   bytes: 2,    kind: "float", E: 5, M: 10, bias: 15},
  2:  {code: 2,  name: "BFP8a", llk: "Bfp8",      bytes: 1,    kind: "bfp", magBits: 7, expA: true},
  3:  {code: 3,  name: "BFP4a", llk: "Bfp4",      bytes: 0.5,  kind: "bfp", magBits: 3, expA: true},
  4:  {code: 4,  name: "TF32",  llk: "Tf32",      bytes: 4,    kind: "float", E: 8, M: 10, bias: 127},
  5:  {code: 5,  name: "BF16",  llk: "Float16_b", bytes: 2,    kind: "float", E: 8, M: 7, bias: 127},
  6:  {code: 6,  name: "BFP8",  llk: "Bfp8_b",    bytes: 1,    kind: "bfp", magBits: 7, expA: false},
  7:  {code: 7,  name: "BFP4",  llk: "Bfp4_b",    bytes: 0.5,  kind: "bfp", magBits: 3, expA: false},
  8:  {code: 8,  name: "INT32", llk: "Int32",     bytes: 4,    kind: "int", magBits: 31},
  9:  {code: 9,  name: "INT16", llk: "UInt16",    bytes: 2,    kind: "int", magBits: 15},
  10: {code: 10, name: "FP8",   llk: "Lf8",       bytes: 1,    kind: "float", E: 5, M: 2, bias: 15},
  11: {code: 11, name: "BFP2a", llk: "Bfp2",      bytes: 0.25, kind: "bfp", magBits: 1, expA: true},
  14: {code: 14, name: "INT8",  llk: "Int8",      bytes: 1,    kind: "int", magBits: 7},
  15: {code: 15, name: "BFP2",  llk: "Bfp2_b",    bytes: 0.25, kind: "bfp", magBits: 1, expA: false},
};
const E4M3 = {code: 10, name: "FP8 E4M3", llk: "Fp8_e4m3", bytes: 1, kind: "float", E: 4, M: 3, bias: 7, noInf: true};
function fmt(code, e4m3) { return e4m3 && code === 10 ? E4M3 : FORMATS[code]; }
function fmtLabel(code) { const f = FORMATS[code]; return f ? `${f.name} · ${f.llk} · ${code}` : `? ${code}`; }

// round half to even
function rne(v) { const f = Math.floor(v), d = v - f; if (d > 0.5) return f + 1; if (d < 0.5) return f; return f % 2 === 0 ? f : f + 1; }
function ilog2(a) { let e = Math.floor(Math.log2(a)); if (2 ** e > a) e--; if (2 ** (e + 1) <= a) e++; return e; }

// generic small float: E exponent bits, M mantissa bits. round: "rne" | "trunc". sat: clamp overflow to max finite
function encMini(x, E, M, bias, {round = "rne", sat = false, noInf = false} = {}) {
  const S = (x < 0 || Object.is(x, -0)) ? 1 : 0, sign = S * 2 ** (E + M), maxE = (1 << E) - 1;
  const rnd = round === "trunc" ? Math.floor : rne;
  if (Number.isNaN(x)) return noInf ? sign + maxE * 2 ** M + (2 ** M - 1) : maxE * 2 ** M + 2 ** (M - 1);
  const maxFinite = noInf ? maxE * 2 ** M + (2 ** M - 2) : (maxE - 1) * 2 ** M + (2 ** M - 1);
  const a = Math.abs(x);
  if (a === Infinity) return sign + (noInf || sat ? maxFinite : maxE * 2 ** M);
  if (a === 0) return sign;
  let e = ilog2(a), be = e + bias, m;
  if (be <= 0) {
    m = rnd(a / 2 ** (1 - bias - M));
    if (m >= 2 ** M) { be = 1; m = 0; } else return sign + m;
  } else {
    m = rnd((a / 2 ** e - 1) * 2 ** M);
    if (m >= 2 ** M) { m = 0; be++; }
  }
  const v = be * 2 ** M + m;
  if (v > maxFinite) return sign + (noInf || sat ? maxFinite : maxE * 2 ** M);
  return sign + v;
}
function decMini(bits, E, M, bias, {noInf = false} = {}) {
  const S = Math.floor(bits / 2 ** (E + M)) & 1, be = Math.floor(bits / 2 ** M) % 2 ** E, m = bits % 2 ** M, maxE = 2 ** E - 1;
  let v;
  if (be === maxE && !noInf) v = m ? NaN : Infinity;
  else if (noInf && be === maxE && m === 2 ** M - 1) v = NaN;
  else if (be === 0) v = m * 2 ** (1 - bias - M);
  else v = (1 + m / 2 ** M) * 2 ** (be - bias);
  return S ? -v : v;
}
const _f32 = new Float32Array(1), _u32 = new Uint32Array(_f32.buffer);
function f32bits(x) { _f32[0] = x; return _u32[0]; }
function bitsf32(b) { _u32[0] = b >>> 0; return _f32[0]; }

// Encode one datum of a non-BFP format to its stored bits. opts.round, opts.sat
function encode(x, f, opts = {}) {
  if (f.kind === "int") {
    const mag = Math.min(Math.abs(Math.trunc(x)) || 0, 2 ** f.magBits - 1);
    if (opts.unsigned && f.magBits === 7) return Math.min(Math.max(Math.trunc(x) || 0, 0), 255);
    return (x < 0 && mag ? 2 ** f.magBits : 0) + mag;
  }
  if (f.code === 0 && !f.noInf) { return f32bits(x); }
  if (f.code === 4) return encMini(x, 8, 10, 127, opts) * 2 ** 13; // TF32 is stored as 32 bits, low 13 zero
  return encMini(x, f.E, f.M, f.bias, {...opts, noInf: !!f.noInf});
}
function decode(bits, f, opts = {}) {
  if (f.kind === "int") {
    if (opts.unsigned && f.magBits === 7) return bits & 0xff;
    const mag = bits % 2 ** f.magBits; return Math.floor(bits / 2 ** f.magBits) & 1 ? -mag : mag;
  }
  if (f.code === 0) return bitsf32(bits);
  if (f.code === 4) return decMini(Math.floor(bits / 2 ** 13), 8, 10, 127);
  return decMini(bits, f.E, f.M, f.bias, {noInf: !!f.noInf});
}
// value after storing in format f
function quantize(x, f, opts = {}) {
  if (f.kind === "bfp") return bfpBlock([x], f, opts).values[0];
  return decode(encode(x, f, opts), f, opts);
}

// ***** block floating point *****
// One shared exponent per 16 datums. B formats: 8-bit exponent (bias 127). A formats: 5-bit exponent (bias 15).
// A datum is a sign bit + magBits magnitude bits; magnitude m means m * 2^(sharedExp - bias - (magBits - 1)).
// (From the ISA doc's BFP8ToBF16: the decoded value is exact, the leading one is part of the 7 magnitude bits.)
function bfpBlock(values, f, {round = "rne", forcedExp = null} = {}) {
  const bias = f.expA ? 15 : 127, maxExp = f.expA ? 31 : 255, nb = f.magBits;
  const rnd = round === "trunc" ? Math.floor : rne;
  let shared = 0;
  if (forcedExp != null) shared = forcedExp;
  else for (const v of values) {
    const a = Math.abs(v);
    if (!a || !Number.isFinite(a)) { if (a === Infinity) shared = maxExp; continue; }
    shared = Math.max(shared, Math.min(maxExp, Math.max(0, ilog2(a) + bias)));
  }
  const scale = 2 ** (shared - bias - (nb - 1)), maxMag = 2 ** nb - 1;
  const mags = [], signs = [], out = [];
  for (const v of values) {
    const a = Math.abs(v), s = v < 0 ? 1 : 0;
    let m = Number.isFinite(a) ? rnd(a / scale) : maxMag;
    m = Math.min(m, maxMag);
    mags.push(m); signs.push(s);
    out.push((s ? -1 : 1) * m * scale);
  }
  return {exp: shared, mags, signs, values: out, bits: mags.map((m, i) => signs[i] * 2 ** nb + m)};
}
function bfpDecode(bits, exp, f) {
  const bias = f.expA ? 15 : 127, nb = f.magBits, m = bits % 2 ** nb, s = Math.floor(bits / 2 ** nb) & 1;
  if (!m) return s ? -0 : 0;
  return (s ? -1 : 1) * m * 2 ** (exp - bias - (nb - 1));
}

// ***** L1 byte image *****
class L1 {
  // bytes: addr -> byte. tags: addr -> array of 8 tag objects, one per bit, so a byte can hold two BFP4 datums
  constructor() { this.bytes = new Map(); this.tags = new Map(); }
  get(a) { return this.bytes.get(a) ?? 0; }
  has(a) { return this.bytes.has(a); }
  set(a, v, tag) { this.bytes.set(a, v & 0xff); if (tag !== undefined) this.tags.set(a, new Array(8).fill(tag)); }
  tagBits(a, lo, n, tag) { let t = this.tags.get(a); if (!t) { t = new Array(8).fill(null); this.tags.set(a, t); } for (let i = lo; i < lo + n; i++) t[i] = tag; }
  // [{lo, n, tag}] runs of equal tags within a byte
  parts(a) {
    const t = this.tags.get(a); if (!t) return [];
    const out = []; for (let i = 0; i < 8; i++) { if (out.length && out[out.length - 1].tag === t[i]) out[out.length - 1].n++; else out.push({lo: i, n: 1, tag: t[i]}); }
    return out;
  }
  clone() { const c = new L1(); c.bytes = new Map(this.bytes); c.tags = new Map([...this.tags].map(([k, v]) => [k, v.slice()])); return c; }
  // read NumBytes (may be fractional: 0.25, 0.5) at a fractional byte address, LSB-first bits (ISA ReadL1Bytes)
  readBits(addr, nbytes) {
    let bitAddr = Math.round(addr * 8), n = Math.round(nbytes * 8), r = 0;
    for (let i = 0; i < n; i++, bitAddr++) r += ((this.get(bitAddr >> 3) >> (bitAddr & 7)) & 1) * 2 ** i;
    return r;
  }
  writeBits(addr, nbytes, value, tag) {
    let bitAddr = Math.round(addr * 8); const n = Math.round(nbytes * 8);
    for (let i = 0; i < n; i++, bitAddr++) {
      const a = bitAddr >> 3, b = bitAddr & 7, bit = Math.floor(value / 2 ** i) & 1;
      this.bytes.set(a, (this.get(a) & ~(1 << b)) | (bit << b));
      if (tag !== undefined) this.tagBits(a, b, 1, tag);
    }
  }
}

// ***** compression (packer Compression.md / unpacker decompression) *****
// Split one compression row into augmented datums: each kept datum carries a 4-bit count of zeros after it.
// The first and last datum of a row are never elided.
function compressRow(items, isZero) {
  const out = []; let i = 0; const n = items.length;
  while (i < n) {
    let z = 0, j = i + 1;
    while (j < n - 1 && z < 15 && isZero(items[j])) { z++; j++; }
    out.push({item: items[i], zeros: z, skipped: items.slice(i + 1, j)});
    i = j;
  }
  return out;
}

// Serialize a whole tile the way the packer would leave it in L1 (used to build unpacker inputs).
// values: array of numbers in memory order. rowLen: datums per compression row (compressed only).
// Returns {l1, sections:[{name,start,end}], dataStart, expStart, rsiStart, end}
function buildTile(values, f, {addr, compressed = false, rowLen = 16, e4m3 = false, digest = 0, srcIds = null, noExp = false, forcedExp = null} = {}) {
  const l1 = new L1(); const sections = []; let a = addr;
  const tag = (i, extra) => ({src: srcIds ? srcIds[i] : i, ...extra});
  if (digest) { for (let i = 0; i < digest * 16; i++) l1.set(a + i, 0, {kind: "header"}); sections.push({name: "header digest", start: a, end: a + digest * 16}); a += digest * 16; }
  const F = f.kind === "float" && e4m3 ? E4M3 : f;
  // augmented datum list
  let aug, rsi = null;
  if (compressed) {
    aug = []; rsi = [0];
    for (let r = 0; r * rowLen < values.length; r++) {
      const idx = []; for (let i = r * rowLen; i < Math.min(values.length, (r + 1) * rowLen); i++) idx.push(i);
      for (const g of compressRow(idx, i => values[i] === 0)) aug.push({i: g.item, zeros: g.zeros});
      rsi.push(aug.length);
    }
  } else aug = values.map((_, i) => ({i, zeros: 0}));
  const rsiStart = a;
  if (compressed) {
    rsi.forEach((v, k) => { l1.set(a + 2 * k, v & 0xff, {kind: "rsi", k}); l1.set(a + 2 * k + 1, v >> 8, {kind: "rsi", k}); });
    const end = a + Math.ceil(rsi.length * 2 / 16) * 16;
    for (let p = a + rsi.length * 2; p < end; p++) l1.set(p, 0, {kind: "pad"});
    sections.push({name: "row start index", start: a, end}); a = end;
  }
  const expStart = a; let bits = aug.map(g => 0), exps = [];
  if (F.kind === "bfp") {
    // exponents per 16 *augmented* datums (compressed) or per 16 datums (uncompressed)
    for (let b = 0; b < aug.length; b += 16) {
      const blk = bfpBlock(aug.slice(b, b + 16).map(g => values[g.i]), F, {forcedExp});
      exps.push(blk.exp); blk.bits.forEach((v, k) => bits[b + k] = v);
    }
    if (!noExp) {
      const nExp = compressed ? Math.ceil(values.length / 16) : exps.length;
      const end = a + Math.ceil(nExp / 16) * 16;
      for (let k = 0; k < end - a; k++) l1.set(a + k, exps[k] ?? 0, k < exps.length ? {kind: "exp", k, srcs: aug.slice(k * 16, k * 16 + 16).map(g => srcIds ? srcIds[g.i] : g.i)} : {kind: "pad"});
      sections.push({name: "shared exponents", start: a, end}); a = end;
    }
  } else bits = aug.map(g => encode(values[g.i], F));
  const dataStart = a;
  if (!compressed) {
    aug.forEach((g, k) => l1.writeBits(a + k * F.bytes, F.bytes, bits[k], tag(g.i, {kind: "data"})));
    let end = a + aug.length * F.bytes; end = Math.ceil(end / 16) * 16;
    sections.push({name: "datums", start: dataStart, end}); a = end;
  } else {
    for (let g0 = 0; g0 < aug.length; g0 += 32) {
      const grp = aug.slice(g0, g0 + 32);
      grp.forEach((g, k) => l1.writeBits(a + k * F.bytes, F.bytes, bits[g0 + k], tag(g.i, {kind: "data", zeros: g.zeros})));
      a += 32 * F.bytes;
      grp.forEach((g, k) => l1.writeBits(a + k * 0.5, 0.5, g.zeros, {kind: "rle", src: srcIds ? srcIds[g.i] : g.i, zeros: g.zeros}));
      a += 16;
    }
    sections.push({name: "datums + zero counts", start: dataStart, end: a});
  }
  return {l1, sections, dataStart, expStart, rsiStart, end: a, rsi, exps, aug};
}

// ***** program text *****
// One instruction per line:  OP key=value key=value ... [xN]     # comment
// xN repeats the line N times. Values: decimal, 0x hex, 0b binary.
function parseNum(s) {
  const neg = s.startsWith("-"), t = neg ? s.slice(1) : s; let v = null;
  if (/^0x[0-9a-f]+$/i.test(t)) v = parseInt(t.slice(2), 16);
  else if (/^0b[01]+$/i.test(t)) v = parseInt(t.slice(2), 2);
  else if (/^\d+(\.\d+)?(e-?\d+)?$/i.test(t)) v = Number(t);
  return v === null ? null : neg ? -v : v;
}
function parseProgram(text, ops) {
  const out = [], errors = [];
  text.split("\n").forEach((raw, ln) => {
    const line = raw.replace(/#.*/, "").trim();
    if (!line) return;
    const toks = line.split(/\s+/);
    const op = toks[0].toUpperCase();
    let repeat = 1; const args = {}, flags = [];
    for (const t of toks.slice(1)) {
      if (/^x\d+$/i.test(t)) { repeat = parseInt(t.slice(1)); continue; }
      const m = t.match(/^([\w.\[\]]+)=(.+)$/);
      if (m) {
        const n = parseNum(m[2]);
        args[m[1].toLowerCase()] = n === null ? m[2] : n;
      } else flags.push(t.toUpperCase());
    }
    if (!ops[op]) { errors.push({line: ln + 1, msg: `unknown instruction ${op}. Known: ${Object.keys(ops).join(", ")}`}); return; }
    const spec = ops[op];
    for (const k of Object.keys(args)) if (spec.args && !spec.args.includes(k) && !(spec.argPrefix && spec.argPrefix.test(k))) errors.push({line: ln + 1, msg: `${op} has no field ${k}. Fields: ${spec.args.join(" ")}`});
    if (repeat > 4096) { errors.push({line: ln + 1, msg: "repeat count above 4096"}); return; }
    for (let r = 0; r < repeat; r++) out.push({op, args, flags, line: ln + 1, raw: raw.trim(), rep: repeat > 1 ? `${r + 1}/${repeat}` : ""});
  });
  return {program: out, errors};
}

// ***** small helpers for the UI *****
function hex(v, w = 0) { return "0x" + (v >>> 0).toString(16).toUpperCase().padStart(w, "0"); }
function fmtNum(v) {
  if (Number.isNaN(v)) return "NaN";
  if (v === Infinity) return "+inf"; if (v === -Infinity) return "-inf";
  if (Object.is(v, -0)) return "-0";
  if (v === 0) return "0";
  const a = Math.abs(v);
  if (Number.isInteger(v) && a < 1e6) return String(v);
  if (a >= 1e5 || a < 1e-3) return v.toExponential(3);
  return String(+v.toPrecision(5));
}
function mulberry32(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
// value patterns for source data. i = datum index (0..n-1)
const PATTERNS = {
  index: {label: "index (0, 1, 2, …)", fn: (i) => i},
  rows: {label: "row.col (row + col/100)", fn: (i) => Math.floor(i / 16) + (i % 16) / 100},
  signed: {label: "signed (−n … +n)", fn: (i, n) => i - Math.floor(n / 2)},
  random: {label: "random normal-ish", fn: (i, n, r) => +((r() + r() + r() - 1.5) * 4).toFixed(3)},
  sparse: {label: "mostly zeros", fn: (i, n, r) => r() < 0.75 ? 0 : +((r() - 0.5) * 8).toFixed(2)},
  wide: {label: "wide range (2^−20 … 2^20)", fn: (i, n, r) => (r() < 0.5 ? -1 : 1) * 2 ** Math.round(r() * 40 - 20) * (1 + Math.round(r() * 7) / 8)},
  tiny: {label: "tiny + normal mix", fn: (i, n, r) => (i % 4 === 0 ? 1e-6 : 1) * (1 + (i % 16) / 16) * (i % 2 ? -1 : 1)},
};
function pattern(name, n, seed = 1) { const r = mulberry32(seed), p = PATTERNS[name] || PATTERNS.index; return Array.from({length: n}, (_, i) => p.fn(i, n, r)); }

const api = {FORMATS, E4M3, fmt, fmtLabel, rne, ilog2, encMini, decMini, f32bits, bitsf32, encode, decode, quantize,
  bfpBlock, bfpDecode, L1, compressRow, buildTile, parseNum, parseProgram, hex, fmtNum, mulberry32, PATTERNS, pattern};
if (typeof module !== "undefined" && module.exports) module.exports = api; else root.TT = api;
})(typeof window !== "undefined" ? window : globalThis);
