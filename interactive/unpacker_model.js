// Blackhole unpacker model: L1 -> SrcA / SrcB / Dest. Pure simulation, no DOM. Sources:
//   tt-isa-documentation WormholeB0 UNPACR_Regular.md (functional model, incl. its Blackhole branches), Unpackers/README.md,
//   UNPACR_NOP_*.md, UNPACR_IncrementContextCounter.md, ADCs.md, SETADC*.md
//   blackhole-py tests/movement/unpacker/unpack.py (configure_unpacker), blackhole-py-rewrite config.py + tests/hw
(function (root) {
"use strict";
const T = typeof module !== "undefined" && module.exports ? require("./common.js") : root.TT;

// ***** configuration schema *****
// scope "unp": per unpacker (0 = SrcA/Dest, 1 = SrcB). "c0": unpacker 0 contexts (8). "c1": unpacker 1 contexts (2).
const UNP = [
  {g: "Tile descriptor (what is in L1)", key: "src_format", type: "fmt", raw: "TILE_DESC{u}_in_data_format", doc: "Format of the datums in L1 (unless per-context formats is on).", conf: "isa"},
  {g: "Tile descriptor (what is in L1)", key: "uncompressed", type: "bool", raw: "TILE_DESC{u}_uncompressed", doc: "Only used outside multi-context mode; there the context's disable_zero_compress decides.", conf: "isa"},
  {g: "Tile descriptor (what is in L1)", key: "x_dim", type: "int", raw: "TILE_DESC{u}_x_dim", doc: "Datums per row. Unpacker 0 in multi-context mode uses the context's tile_x_dim instead.", conf: "isa"},
  {g: "Tile descriptor (what is in L1)", key: "y_dim", type: "int", raw: "TILE_DESC{u}_y_dim", doc: "Rows per Z plane.", conf: "isa"},
  {g: "Tile descriptor (what is in L1)", key: "z_dim", type: "int", raw: "TILE_DESC{u}_z_dim", doc: "Planes (faces) per W. 0 means 1.", conf: "isa"},
  {g: "Tile descriptor (what is in L1)", key: "w_dim", type: "int", raw: "TILE_DESC{u}_w_dim", doc: "0 means 1.", conf: "isa"},
  {g: "Tile descriptor (what is in L1)", key: "digest_size", type: "int", raw: "TILE_DESC{u}_digest_size", doc: "Header is (1 + digest) × 16 bytes. The 1 is why base fields hold byte/16 − 1.", conf: "isa"},
  {g: "Tile descriptor (what is in L1)", key: "no_bfp_exp_section", type: "bool", raw: "TILE_DESC{u}_no_bfp_exp_section", doc: "BFP4/BFP2 only: there is no exponent section to skip.", conf: "isa"},
  {g: "Unpack config", key: "dst_format", type: "fmt", raw: "THCON_SEC{u}_REG2_Out_data_format", doc: "Format written to the register file. Must equal the L1 format except FP32 → TF32/BF16/FP16.", conf: "isa"},
  {g: "Unpack config", key: "fp8_e4m3", type: "bool", raw: "THCON_SEC{u}_REG1_Unp_LF8_4b_exp", doc: "FP8 input is E4M3 (Blackhole).", conf: "isa"},
  {g: "Unpack config", key: "per_context_formats", type: "bool", raw: "THCON_SEC{u}_REG2_Ovrd_data_format", doc: "Use each context's own in/out formats.", conf: "isa"},
  {g: "Unpack config", key: "tilize", type: "bool", raw: "THCON_SEC{u}_REG2_Tileize_mode", doc: "After each row of datums, jump RowStride bytes (row-major L1 → tiles). RowStride comes from shift_amount of contexts 0, 1, 2.", conf: "isa"},
  {g: "Unpack config", key: "transpose_xy", type: "bool", raw: "THCON_SEC{u}_REG2_Haloize_mode", doc: "Swap row and column inside each 16×16 SrcA block. Ignored by unpacker 1 on current silicon.", conf: "isa"},
  {g: "Unpack config", key: "upsample_rate", type: "int", raw: "THCON_SEC{u}_REG2_Upsample_rate", doc: "0 off; 1, 2, 3 = 1, 3, 7 extra slots after each datum (zeros, or skipped with interleave).", conf: "isa"},
  {g: "Unpack config", key: "upsample_interleave", type: "bool", raw: "THCON_SEC{u}_REG2_Upsample_and_interleave", doc: "Skip the extra slots instead of writing zeros.", conf: "isa"},
  {g: "Unpack config", key: "force_shared_exp", type: "bool", raw: "THCON_SEC{u}_REG2_Force_shared_exp", doc: "BFP: ignore L1 exponents, use forced_shared_exp for every datum.", conf: "isa"},
  {g: "Unpack config", key: "forced_shared_exp", type: "int", raw: "UNP{u}_FORCED_SHARED_EXP_shared_exp", doc: "", conf: "isa"},
  {g: "Unpack config", key: "src_reg_set_update", type: "bool", raw: "THCON_SEC{u}_REG2_Unpack_Src_Reg_Set_Upd", doc: "Without a bank flip, advance the Src write row by 16 after each UNPACR.", conf: "isa"},
  {g: "Unpack config", key: "context_count", type: "int", raw: "THCON_SEC{u}_REG2_Context_count", doc: "The context counter cycles through 2^this contexts.", conf: "isa"},
  {g: "Unpack config", key: "throttle_mode", type: "int", raw: "THCON_SEC{u}_REG2_Throttle_mode", doc: "L1 read speed: 0 = 16 B/cycle, 1 = 32, 2 = 64. Timing is not modeled; affects the SrcA burst check.", conf: "isa"},
  {g: "Unpack config", key: "limit_address", type: "hex", raw: "THCON_SEC{u}_REG2_Unpack_limit_address", doc: "L1 ring end, 16B units. 0 = off.", conf: "isa"},
  {g: "Unpack config", key: "fifo_size", type: "hex", raw: "THCON_SEC{u}_REG2_Unpack_fifo_size", doc: "Subtracted (× 16) when an address passes the limit.", conf: "isa"},
  {g: "Unpack config", key: "src_unsigned", type: "bool", raw: "ALU_FORMAT_SPEC_REG0_Src{A|B}Unsigned", doc: "INT8 input is unsigned.", conf: "isa"},
  {g: "Output address (register file)", key: "out_counter_base", type: "int", raw: "UNP{u}_ADDR_BASE_REG_1_Base", doc: "Bytes. Divided by the output datum size, then 16 datums per row.", conf: "isa"},
  {g: "Output address (register file)", key: "out_y_stride", type: "int", raw: "UNP{u}_ADDR_CTRL_XY_REG_1_Ystride", doc: "Bytes per Y1 step. blackhole-py: 16 × datum size = one row.", conf: "isa"},
  {g: "Output address (register file)", key: "out_z_stride", type: "int", raw: "UNP{u}_ADDR_CTRL_ZW_REG_1_Zstride", doc: "Bytes per Z1 step. blackhole-py: 256 × datum size = one face.", conf: "isa"},
  {g: "Output address (register file)", key: "out_w_stride", type: "int", raw: "UNP{u}_ADDR_CTRL_ZW_REG_1_Wstride", doc: "", conf: "isa"},
  {g: "Output address (register file)", key: "add_dest_addr_counter", type: "bool", raw: "UNP{u}_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr", doc: "Unpacker 0, multi-context, SrcA: add the counters to the context's dest_address (otherwise the counters are ignored).", conf: "isa"},
];
const CTX = [
  {g: "Context", key: "l1_base", type: "hex", raw: "base", doc: "L1 address of the tile, 16B units minus one: the hardware adds 1 + digest.", conf: "hw"},
  {g: "Context", key: "offset_address", type: "hex", raw: "offset", doc: "Added to the base (16B units, low 16 bits). Contexts 4–7 share 0–3's copy.", conf: "isa", four: true},
  {g: "Context", key: "dest_address", type: "int", raw: "REG5_Dest_cntx{c}_address", doc: "Unpacker 0: register-file position in datums. 64 = row 0 (the first 4 rows are an offset the hardware subtracts). Contexts 4–7 share 0–3's.", conf: "isa", four: true, u0: true},
  {g: "Context", key: "tile_x_dim", type: "int", raw: "REG5_Tile_x_dim_cntx{c}", doc: "Unpacker 0: datums per row (replaces the descriptor's x_dim). Contexts 4–7 share 0–3's.", conf: "isa", four: true, u0: true},
  {g: "Context", key: "shift_amount", type: "int", raw: "REG2_Shift_amount_cntx{c}", doc: "Unpacker 0, not tilize: SrcA column shift. In tilize mode contexts 0–2 together form RowStride. Contexts 4–7 share 0–3's.", conf: "isa", four: true},
  {g: "Context", key: "disable_zero_compress", type: "bool", raw: "REG2_Disable_zero_compress_cntx{c}", doc: "1 = the L1 tile is not zero-compressed.", conf: "isa"},
  {g: "Context", key: "to_dest", type: "bool", raw: "REG2_Unpack_if_sel_cntx{c}", doc: "Unpacker 0: write Dest instead of SrcA.", conf: "isa", u0: true},
  {g: "Context", key: "src_format", type: "fmt", raw: "REG7_Unpack_data_format_cntx{c}", doc: "Used when per-context formats is on.", conf: "isa"},
  {g: "Context", key: "dst_format", type: "fmt", raw: "REG7_Unpack_out_data_format_cntx{c}", doc: "Used when per-context formats is on.", conf: "isa"},
];
const THREAD = [
  {g: "Unpack thread (SETC16)", key: "srca_set_base", type: "int", raw: "SRCA_SET_Base", doc: "SrcA row base (× 16) after a bank flip.", conf: "isa"},
  {g: "Unpack thread (SETC16)", key: "srca_override", type: "bool", raw: "SRCA_SET_SetOvrdWithAddr", doc: "SrcA row comes from the address alone (row & 63). blackhole-py sets this (SETC16 SRCA_SET = 4) except for unpack-to-Dest.", conf: "isa"},
  {g: "Unpack thread (SETC16)", key: "srcb_set_base", type: "int", raw: "SRCB_SET_Base", doc: "", conf: "isa"},
  {g: "Unpack thread (SETC16)", key: "ctx_offset_0", type: "int", raw: "UNPACK_MISC_CFG_CfgContextOffset_0", doc: "Added to the UNPACR context number for unpacker 0.", conf: "isa"},
  {g: "Unpack thread (SETC16)", key: "ctx_offset_1", type: "int", raw: "UNPACK_MISC_CFG_CfgContextOffset_1", doc: "", conf: "isa"},
];
const SETUP = [
  {g: "Explorer setup", key: "pattern", type: "pattern", raw: "(explorer)", doc: "Values written into every input tile. Each distinct context address gets its own tile.", conf: "sim"},
  {g: "Explorer setup", key: "seed", type: "int", raw: "(explorer)", doc: "", conf: "sim"},
  {g: "Explorer setup", key: "count", type: "int", raw: "(explorer)", doc: "Datums per input tile. 0 = x_dim × y_dim × z_dim × w_dim of the context.", conf: "sim"},
];
const FIELDS = [
  ...UNP.map(f => ({...f, s: "unp"})),
  ...CTX.map(f => ({...f, g: "Unpacker 0 contexts", s: "c0"})),
  ...CTX.filter(f => !f.u0).map(f => ({...f, g: "Unpacker 1 contexts", s: "c1"})),
  ...THREAD, ...SETUP,
];
function rawName(f, i) {
  if (f.s === "unp") return f.raw.replaceAll("{u}", i).replace("{A|B}", i ? "B" : "A");
  if (f.s === "c0" || f.s === "c1") {
    const u = f.s === "c0" ? 0 : 1, c = f.four ? i & 3 : i, sec = `THCON_SEC${u}`;
    if (f.key === "l1_base") return i === 0 ? `${sec}_REG3_Base_address` : i < 4 ? `${sec}_REG3_Base_cntx${i}_address` : `${sec}_REG4_Base_cntx${i}_address`;
    if (f.key === "offset_address") return c === 0 ? `${sec}_REG7_Offset_address` : `${sec}_REG7_Offset_cntx${c}_address`;
    return `${sec}_${f.raw.replace("{c}", c)}`;
  }
  return f.raw;
}

function defaultUnp(u) {
  return {src_format: 5, uncompressed: true, x_dim: u ? 256 : 0, y_dim: 1, z_dim: 4, w_dim: 0, digest_size: 0, no_bfp_exp_section: false,
    dst_format: 5, fp8_e4m3: false, per_context_formats: false, tilize: false, transpose_xy: false, upsample_rate: 0, upsample_interleave: false,
    force_shared_exp: false, forced_shared_exp: 127, src_reg_set_update: false, context_count: 0, throttle_mode: 2, limit_address: 0, fifo_size: 0,
    src_unsigned: false, out_counter_base: 0, out_y_stride: 32, out_z_stride: 512, out_w_stride: 0, add_dest_addr_counter: u === 0};
}
function defaultCtx(u, base) {
  return {l1_base: (base >> 4) - 1, offset_address: 0, dest_address: u ? 0 : 64, tile_x_dim: 256, shift_amount: 0, disable_zero_compress: true,
    to_dest: false, src_format: 5, dst_format: 5};
}
function defaultConfig() {  // blackhole-py configure_unpacker, BF16 to SrcA / SrcB
  return {unp: [defaultUnp(0), defaultUnp(1)],
    c0: Array.from({length: 8}, () => defaultCtx(0, 0x10000)), c1: Array.from({length: 2}, () => defaultCtx(1, 0x18000)),
    srca_set_base: 0, srca_override: true, srcb_set_base: 0, ctx_offset_0: 0, ctx_offset_1: 0,
    pattern: "rows", seed: 1, count: 0};
}
function cloneConfig(c) { return JSON.parse(JSON.stringify(c)); }
function coerce(old, v) { return typeof old === "boolean" ? !!v : typeof old === "number" ? Number(v) : v; }
// keys: "u0.src_format", "u0c3.l1_base", "u1c1.to_dest", "srca_override"
function locate(cfg, key) {
  let m = key.match(/^u([01])\.(\w+)$/); if (m) return [cfg.unp[+m[1]], m[2]];
  m = key.match(/^u([01])c(\d)\.(\w+)$/);
  if (m) { const arr = cfg["c" + m[1]]; if (+m[2] >= arr.length) throw new Error(`unpacker ${m[1]} has ${arr.length} contexts`); return [arr[+m[2]], m[3]]; }
  return [cfg, key];
}
function setKey(cfg, key, v) { const [o, k] = locate(cfg, key); if (!(k in o) || typeof o[k] === "object") throw new Error(`no config field ${key}`); o[k] = coerce(o[k], v); }
function getKey(cfg, key) { const [o, k] = locate(cfg, key); return o[k]; }

const UARGS = ["u"];
const OPS = {
  UNPACR: {args: ["u", "ctx", "y0", "z0", "y1", "z1", "flip", "zero", "ctr", "multi"], doc: "Unpack. u = unpacker (0: SrcA/Dest, 1: SrcB), ctx = context number, y0/z0 = L1 counter increments after, y1/z1 = register counter increments after, flip = hand the bank to math (set dvalid), zero = write zeros, ctr = use the context counter, multi = multi-context mode (default 1, as blackhole-py)."},
  UNPACR_INC_CTX: {args: UARGS, doc: "Advance the unpacker's context counter (wraps at 2^context_count)."},
  ZEROSRC: {args: ["u", "both", "neginf"], doc: "UNPACR_NOP: clear the unpacker's current Src bank (both = both banks; neginf = SrcA to −inf)."},
  SETDVALID: {args: UARGS, doc: "UNPACR_NOP: hand the current Src bank to math and switch to the other bank."},
  MATH_RELEASE: {args: UARGS, doc: "Stand-in for the math thread: it finished with the oldest bank and gives it back to the unpacker."},
  SETADCXX: {args: ["x0", "x1"], doc: "x0 = first datum, x1 = last datum of a row. Flags U0 / U1 pick the unpacker (default both)."},
  SETADCXY: {args: ["x0", "y0", "x1", "y1"], doc: "Set counters. Flags U0 / U1."},
  SETADCZW: {args: ["z0", "w0", "z1", "w1"], doc: "Set counters. Flags U0 / U1."},
  SETADC: {args: ["ch", "x", "y", "z", "w"], doc: "Set one counter of one channel. Flags U0 / U1."},
  INCADCXY: {args: ["x0", "y0", "x1", "y1"], doc: "Add to counters."},
  INCADCZW: {args: ["z0", "w0", "z1", "w1"], doc: "Add to counters."},
  ADDRCRXY: {args: ["x0", "y0", "x1", "y1"], doc: "Add to the carry register, then copy it to the counter."},
  ADDRCRZW: {args: ["z0", "w0", "z1", "w1"], doc: "Add to the carry register, then copy it to the counter."},
  CFG: {args: [], argPrefix: /^(u[01](c\d)?\.\w+|\w+)$/, doc: "Write config mid-program: u0.src_format=5, u0c1.l1_base=0x10FF, srca_override=0. (In a kernel: a store / WRCFG / SETC16.)"},
};

// ***** input tiles *****
function contextView(cfg, u, c) {  // effective descriptor for (unpacker, context) in multi-context mode
  const U = cfg.unp[u], C = cfg["c" + u][c], C4 = cfg["c" + u][c & 3];
  const inF = U.per_context_formats ? C.src_format : U.src_format;
  return {u, c, base: C.l1_base, offset: C4.offset_address, xdim: u === 0 ? C4.tile_x_dim : U.x_dim, inF,
    compressed: !C.disable_zero_compress};
}
function tileStart(cfg, u, c) { const v = contextView(cfg, u, c); return (v.base + (v.offset & 0xffff) + 1) * 16; }
function buildInputs(cfg0, program) {
  // every distinct (start address) any context points at, across CFG changes in the program
  const seen = new Map();
  const cfg = cloneConfig(cfg0);
  const visit = () => { for (const u of [0, 1]) for (let c = 0; c < cfg["c" + u].length; c++) {
    const a = tileStart(cfg, u, c); if (!seen.has(a)) seen.set(a, {u, c, view: contextView(cfg, u, c), cfg: cloneConfig(cfg)});
  } };
  visit();
  for (const ins of program) if (ins.op === "CFG") { try { for (const [k, v] of Object.entries(ins.args)) setKey(cfg, k, v); } catch (e) {} visit(); }
  const l1 = new T.L1(), buffers = [];
  let k = 0;
  for (const [addr, {u, c, view, cfg: cc}] of [...seen].sort((a, b) => a[0] - b[0])) {
    const U = cc.unp[u];
    const n = cc.count || Math.max(1, (view.xdim || 1) * Math.max(1, U.y_dim) * (U.z_dim || 1) * (U.w_dim || 1));
    const f = T.FORMATS[view.inF] || T.FORMATS[5];
    let vals = T.pattern(cc.pattern, n, cc.seed + k);
    if (cc.pattern === "index") vals = vals.map(v => v + k * 1000);
    const ids = vals.map((_, i) => k * 65536 + i);
    const t = T.buildTile(vals, f, {addr, compressed: view.compressed, rowLen: view.xdim || 16, e4m3: U.fp8_e4m3, digest: U.digest_size, srcIds: ids, noExp: f.kind === "bfp" && f.magBits < 7 && U.no_bfp_exp_section, forcedExp: U.force_shared_exp ? U.forced_shared_exp : null});
    for (const [a, b] of t.l1.bytes) { if (l1.has(a)) continue; l1.bytes.set(a, b); l1.tags.set(a, t.l1.tags.get(a)); }
    buffers.push({k, addr, u, c, n, fmt: f, vals, sections: t.sections.map(s => ({...s, name: `buffer ${k} · ${s.name}`}))});
    k++;
  }
  return {l1, buffers};
}

// ***** the simulation *****
function newAdc() { const ch = () => ({X: 0, Y: 0, Z: 0, W: 0, X_Cr: 0, Y_Cr: 0, Z_Cr: 0, W_Cr: 0}); return [{ch: [ch(), ch()]}, {ch: [ch(), ch()]}]; }
function regFile(rows) { return {v: new Array(rows * 16).fill(null), meta: new Array(rows * 16).fill(null)}; }

function simulate(cfg0, program, upto = Infinity) {
  const cfg = cloneConfig(cfg0);
  const {l1, buffers} = buildInputs(cfg0, program);
  const adc = newAdc();
  const srcA = [regFile(64), regFile(64)], srcB = [regFile(64), regFile(64)], dest = regFile(1024);
  const bankOwner = {A: ["unpacker", "unpacker"], B: ["unpacker", "unpacker"]};  // who may use each bank
  const unpk = [{bank: 0, row: 0, ctr: 0}, {bank: 0, row: 0, ctr: 0}];
  const forward = new Map();  // src id -> [{reg, bank, idx, step}]
  const steps = [];
  let stepNo = 0;
  for (const ins of program) {
    if (stepNo >= upto) break;
    const step = {ins, trace: [], hotL1: new Set(), hotReg: new Set(), error: null, n: stepNo};
    steps.push(step); stepNo++;
    const tr = (c, s) => step.trace.push([c, s]);
    const a = ins.args;
    const targets = ins.flags.includes("U0") && !ins.flags.includes("U1") ? [0] : ins.flags.includes("U1") && !ins.flags.includes("U0") ? [1] : a.u != null ? [a.u] : [0, 1];
    try {
      switch (ins.op) {
      case "SETADCXX":
        for (const u of targets) { if (a.x0 != null) adc[u].ch[0].X = adc[u].ch[0].X_Cr = a.x0; if (a.x1 != null) adc[u].ch[1].X = adc[u].ch[1].X_Cr = a.x1; }
        tr("", `unpacker ${targets.join("+")}: ch0.X = ${adc[targets[0]].ch[0].X} (first datum), ch1.X = ${adc[targets[0]].ch[1].X} (last) → ${adc[targets[0]].ch[1].X - adc[targets[0]].ch[0].X + 1} datums per UNPACR`);
        break;
      case "SETADCXY": case "SETADCZW": case "INCADCXY": case "INCADCZW": case "ADDRCRXY": case "ADDRCRZW": {
        const inc = ins.op.startsWith("INC"), cr = ins.op.startsWith("ADDRCR");
        for (const u of targets) for (const [k, v] of Object.entries(a)) {
          if (k === "u") continue;
          const ch = adc[u].ch[+k[1]], C = k[0].toUpperCase();
          if (inc) ch[C] += v; else if (cr) { ch[C + "_Cr"] += v; ch[C] = ch[C + "_Cr"]; } else { ch[C] = v; ch[C + "_Cr"] = v; }
          tr("", `unpacker ${u} ch${k[1]}.${C} ${inc ? "+= " + v : cr ? "carry += " + v : "= " + v} → ${ch[C]}`);
        }
        break; }
      case "SETADC":
        for (const u of targets) { const ch = adc[u].ch[a.ch ?? 0]; for (const C of ["x", "y", "z", "w"]) if (a[C] != null) { ch[C.toUpperCase()] = ch[C.toUpperCase() + "_Cr"] = a[C]; tr("", `unpacker ${u} ch${a.ch ?? 0}.${C.toUpperCase()} = ${a[C]}`); } }
        break;
      case "CFG":
        for (const [k, v] of Object.entries(a)) { const old = getKey(cfg, k); setKey(cfg, k, v); tr("", `${k}: ${fmtVal(old)} → ${fmtVal(getKey(cfg, k))}`); }
        break;
      case "UNPACR_INC_CTX": {
        const u = a.u ?? 0, U = cfg.unp[u]; let n = unpk[u].ctr + 1; if (n >= 1 << U.context_count) n = 0;
        tr("", `unpacker ${u} context counter ${unpk[u].ctr} → ${n} (wraps at 2^${U.context_count})`); unpk[u].ctr = n; break; }
      case "ZEROSRC": {
        const u = a.u ?? 0, regs = u ? srcB : srcA, R = u ? "B" : "A";
        for (let b = 0; b < 2; b++) if (a.both || b === unpk[u].bank) {
          if (bankOwner[R][b] !== "unpacker") tr("w", `Src${R} bank ${b} belongs to math: the hardware waits for it`);
          regs[b].v.fill(u === 0 && a.neginf ? -Infinity : 0); regs[b].meta.fill(null);
          for (let i = 0; i < 1024; i++) step.hotReg.add(`${R}${b}:${i}`);
          tr("", `Src${R} bank ${b} = ${u === 0 && a.neginf ? "−inf" : "0"}`);
        }
        break; }
      case "SETDVALID": flip(a.u ?? 0, step); break;
      case "MATH_RELEASE": {
        const R = (a.u ?? 0) ? "B" : "A";
        const b = bankOwner[R].indexOf("math");
        if (b < 0) tr("w", `no Src${R} bank is with math`); else { bankOwner[R][b] = "unpacker"; tr("", `math gives Src${R} bank ${b} back to the unpacker`); }
        break; }
      case "UNPACR": unpacr(step, a); break;
      default: throw new Error(`not modeled: ${ins.op}`);
      }
    } catch (e) { step.error = e.message; tr("e", e.message); }
    step.adc = JSON.parse(JSON.stringify(adc));
    step.unpk = JSON.parse(JSON.stringify(unpk));
    step.owner = JSON.parse(JSON.stringify(bankOwner));
  }

  function flip(u, step) {
    const R = u ? "B" : "A";
    const b = unpk[u].bank;
    bankOwner[R][b] = "math";
    unpk[u].bank ^= 1;
    unpk[u].row = (u ? cfg.srcb_set_base : cfg.srca_set_base) << 4;
    step.trace.push(["h", `Src${R} bank ${b} → math (dvalid). Unpacker ${u} now writes bank ${unpk[u].bank}, row ${unpk[u].row}.`]);
  }

  function unpacr(step, a) {
    const tr = (c, s) => step.trace.push([c, s]);
    const u = a.u ?? 0, U = cfg.unp[u], multi = a.multi ?? 1, R = u ? "B" : "A";
    if (u > 1) throw new Error("u is 0 or 1");
    // --- context
    let ctx = 0;
    if (multi) {
      ctx = (a.ctr ? unpk[u].ctr : (a.ctx ?? 0)) + (u ? cfg.ctx_offset_1 : cfg.ctx_offset_0);
      ctx &= 7;
      if (u === 1 && ctx >= 2) throw new Error("unpacker 1 has contexts 0 and 1 only");
    }
    const C = cfg["c" + u][ctx], C4 = cfg["c" + u][ctx & 3];
    tr("h", `UNPACR unpacker ${u} → ${u ? "SrcB" : "SrcA or Dest"}, ${multi ? `context ${ctx}${a.ctr ? " (from the context counter)" : ""}` : "single-context mode (context 0, descriptor fields)"}`);
    const uncompressed = multi ? C.disable_zero_compress : U.uncompressed;
    const xdim = multi && u === 0 ? C4.tile_x_dim : U.x_dim;
    const ydim = U.y_dim, zdim = U.z_dim || 1, wdim = U.w_dim || 1;
    const inCode = multi && U.per_context_formats ? C.src_format : U.src_format;
    const outCode = multi && U.per_context_formats ? C.dst_format : U.dst_format;
    const inF = T.fmt(inCode, U.fp8_e4m3), outF = T.FORMATS[outCode];
    if (!inF || !outF) throw new Error("unknown data format");
    tr("", `tile: x_dim ${xdim}${multi && u === 0 ? ` (context ${ctx & 3}'s tile_x_dim)` : ""}, y ${ydim}, z ${zdim}, w ${wdim}; ${inF.name} in L1 → ${outF.name}${uncompressed ? "" : ", zero-compressed"}`);
    // --- input address
    const baseField = multi && ctx !== 0 ? C.l1_base : cfg["c" + u][0].l1_base;
    const offField = (multi && ctx !== 0 ? C4.offset_address : cfg["c" + u][0].offset_address) & 0xffff;
    let inAddr = (baseField + offField + 1 + U.digest_size) * 16;
    tr("", `L1: (base ${T.hex(baseField)} + offset ${offField} + 1 + digest ${U.digest_size}) × 16 = ${T.hex(inAddr)}`);
    let rowStartAddr = null;
    if (!uncompressed) {
      rowStartAddr = inAddr;
      const nRows = ydim * zdim * wdim;
      inAddr += Math.ceil((nRows + 1) * 2 / 16) * 16;
      tr("", `  skip row start index: ${nRows + 1} × 2 bytes, rounded to 16 → data at ${T.hex(inAddr)}`);
    }
    let expAddr = null;
    if (inF.kind === "bfp" && !U.force_shared_exp) {
      expAddr = inAddr;
      if (inF.magBits === 7 || !U.no_bfp_exp_section) {
        const nExp = Math.ceil(xdim * ydim * zdim * wdim / 16);
        inAddr += Math.ceil(nExp / 16) * 16;
        tr("", `  skip exponent section: ${nExp} exponents (one per 16 datums), rounded to 16 bytes → datums at ${T.hex(inAddr)}`);
      }
    }
    const A = adc[u], ch0 = A.ch[0], ch1 = A.ch[1];
    let first, inNum, decompDrop = 0, decompNum = Infinity;
    if (uncompressed) {
      first = ((ch0.W * zdim + ch0.Z) * ydim + ch0.Y) * xdim + ch0.X;
      inNum = ch1.X + 1 - ch0.X;
      tr("", `first datum = ((W0 ${ch0.W} × z ${zdim} + Z0 ${ch0.Z}) × y ${ydim} + Y0 ${ch0.Y}) × x ${xdim} + X0 ${ch0.X} = ${first}; count = X1 ${ch1.X} + 1 − X0 ${ch0.X} = ${inNum}`);
    } else {
      const rs = rowStartAddr + ((ch0.W * zdim + ch0.Z) * ydim) * 2;
      const rsi = i => l1.readBits(rs + i * 2, 2);
      first = rsi(ch0.Y & 0xff);
      if (ch0.X === 0 && ch1.X === xdim - 1) { inNum = rsi((ch0.Y & 0xff) + 1) - first; tr("", `compressed row ${ch0.Y}: row start index ${first} .. ${first + inNum} → ${inNum} stored datums`); }
      else { decompDrop = ch0.X; decompNum = ch1.X + 1 - decompDrop; inNum = Infinity; tr("", `compressed row ${ch0.Y} from ${first}: drop the first ${decompDrop} expanded datums, keep ${decompNum}`); }
    }
    let dAddr = inAddr, deltaAddr = null;
    if (uncompressed) dAddr += first * inF.bytes;
    else { dAddr += Math.floor(first / 32) * (32 * inF.bytes + 16); deltaAddr = dAddr + 32 * inF.bytes; dAddr += (first % 32) * inF.bytes; deltaAddr += (first % 32) * 0.5; }
    let eAddr = expAddr != null ? expAddr + first / 16 : null;
    const wrap = x => (U.limit_address && x > U.limit_address * 16) ? x - U.fifo_size * 16 : x;
    dAddr = wrap(dAddr); if (eAddr != null) eAddr = wrap(eAddr); if (deltaAddr != null) deltaAddr = wrap(deltaAddr);
    tr("", `  datum ${first} starts at ${T.hex(Math.floor(dAddr))}${dAddr % 1 ? ` bit ${(dAddr % 1) * 8}` : ""}${eAddr != null ? `, its exponent at ${T.hex(Math.floor(eAddr))}` : ""}`);
    const rowWidth = inF.bytes <= 1 ? 16 : 32;  // Blackhole UnpackRowWidth
    let rowStride;
    if (U.tilize) {
      const c0 = cfg["c" + u];
      rowStride = (c0[0].shift_amount << 4) | ((c0[1]?.shift_amount ?? 0) << 8) | ((c0[2]?.shift_amount ?? 0) << 12);
      tr("", `tilize: after every ${rowWidth} datums jump to the next row: RowStride = shift0 ${c0[0].shift_amount}<<4 | shift1<<8 | shift2<<12 = ${rowStride} bytes`);
      if (dAddr % 16) tr("e", "  tilize needs the first datum 16-byte aligned (undefined behaviour)");
    } else rowStride = inF.bytes * rowWidth;
    // --- output address
    const toDst = u === 0 && (multi ? C.to_dest : false);
    const sizeOut = outF.bytes;
    let outB = U.out_counter_base + ch1.Y * U.out_y_stride + ch1.Z * U.out_z_stride + ch1.W * U.out_w_stride;
    let out = outF.bytes === 4 ? outB >> 2 : outF.bytes === 2 ? outB >> 1 : outB;
    tr("", `register: (base ${U.out_counter_base} + Y1 ${ch1.Y}×${U.out_y_stride} + Z1 ${ch1.Z}×${U.out_z_stride} + W1 ${ch1.W}×${U.out_w_stride}) = ${outB} bytes ÷ ${sizeOut} = datum ${out}`);
    if (multi && u === 0) {
      const ca = C4.dest_address;
      if (toDst || U.add_dest_addr_counter) { out += ca; tr("", `  + context ${ctx & 3} dest_address ${ca} = ${out}`); }
      else { out = ca; tr("w", `  = context dest_address ${ca} (add_dest_addr_counter is off, so the counters are ignored)`); }
    }
    if (u === 0 && out < 64) tr("w", "  below 64: the first 4 rows are an offset; these writes are dropped for SrcA");
    const upZeros = (1 << U.upsample_rate) - 1, inter = U.upsample_interleave;
    const colShift = (U.tilize || u === 1) ? 0 : C4.shift_amount;
    const transpose = U.transpose_xy && u === 0;
    if (U.transpose_xy && u === 1) tr("w", "  transpose is ignored by unpacker 1 on current silicon");
    tr("", `→ ${toDst ? "Dest" : `Src${R} bank ${unpk[u].bank}`} starting row ${toDst ? ((out >> 4) - 4) & 0x3ff : u ? (out >> 4) + unpk[u].row : cfg.srca_override ? ((out >> 4) - 4) & 63 : (out >> 4) - 4 + unpk[u].row}, col ${out & 15}` +
      (upZeros ? `; upsample: ${upZeros} ${inter ? "skipped" : "zero"} slot(s) after each datum` : "") + (colShift ? `; column shift ${colShift}` : "") + (transpose ? "; transposed" : ""));
    if (!toDst) {
      if (bankOwner[R][unpk[u].bank] !== "unpacker") { tr("e", `Src${R} bank ${unpk[u].bank} is still with math: the hardware would wait here. Add MATH_RELEASE u=${u}.`); throw new Error(`Src${R} bank ${unpk[u].bank} not free`); }
      if (u === 0 && !cfg.srca_override) tr("w", "  SrcA without SetOvrdWithAddr: rows come from the Src row pointer (ISA doc: no known usage)");
    }
    if (toDst && cfg.srca_override) tr("w", "  unpack-to-Dest with SetOvrdWithAddr set: undefined (blackhole-py clears SRCA_SET for Dest)");
    if (!toDst && u === 0 && inNum > 16 && inNum !== Infinity) {
      let tm = U.throttle_mode; if (inF.bytes === 0.25) tm = 0; else if (U.tilize) tm = 2; else tm = inF.bytes === 1 ? 3 : 2;
      let tb = 16 << tm; if (tm === 2 && inF.bytes >= 2) tb = 128;
      const burst = Math.min(8, Math.max(1, tb / (16 * inF.bytes)));
      const startRow = Math.floor(out / 16) - 4;
      if (startRow & (burst - 1)) tr("w", `  SrcA burst check: start row ${startRow} is not a multiple of ${burst} rows; writes may be dropped`);
    }
    // --- the loop
    const regs = toDst ? null : (u ? srcB : srcA)[unpk[u].bank];
    let written = 0, i = 0;
    const lastSrc = [];
    while (i < inNum && decompNum > 0) {
      const bits = l1.readBits(dAddr, inF.bytes);
      const srcTagParts = l1.tags.get(Math.floor(dAddr)) || [];
      const srcTag = srcTagParts[Math.round((dAddr % 1) * 8)] || null;
      for (let b = Math.floor(dAddr); b < Math.ceil(dAddr + inF.bytes); b++) step.hotL1.add(b);
      const readAt = dAddr;
      dAddr += inF.bytes;
      i++;
      if (i % rowWidth === 0) { dAddr -= inF.bytes * rowWidth; dAddr += rowStride; dAddr = wrap(dAddr); }
      let expBits = null;
      if (inF.kind === "bfp") {
        if (U.force_shared_exp) expBits = U.forced_shared_exp;
        else { expBits = l1.get(Math.floor(eAddr)); step.hotL1.add(Math.floor(eAddr)); eAddr += 1 / 16; if (eAddr % 16 === 0) eAddr = wrap(eAddr); }
      }
      let zerosAfter = 0;
      if (!uncompressed) { zerosAfter = l1.readBits(deltaAddr, 0.5); step.hotL1.add(Math.floor(deltaAddr)); deltaAddr += 0.5; if (deltaAddr % 16 === 0) { dAddr += 16; deltaAddr += 32 * inF.bytes; deltaAddr = wrap(deltaAddr); } }
      // format conversion
      let v = inF.kind === "bfp" ? T.bfpDecode(bits, expBits, inF) : T.decode(bits, inF, {unsigned: U.src_unsigned});
      const raw = v;
      let note = "";
      if (inCode === 0 && outCode !== 0) {
        if (outCode === 5) { let b = T.f32bits(v); if (!(b & 0x7f800000)) b &= 0x80000000; v = T.decMini(b >>> 16, 8, 7, 127); note = "FP32 → BF16: truncate, flush denormals"; }
        else if (outCode === 1) { v = T.quantize(v, T.FORMATS[1]); note = "FP32 → FP16"; }
        else if (outCode === 4) { v = toDst ? v : T.decMini(Math.floor(T.f32bits(v) / 8192), 8, 10, 127); note = toDst ? "TF32 into Dest means FP32" : "FP32 → TF32: drop 13 mantissa bits"; }
        else note = "undefined conversion";
      } else if (inCode !== outCode && !(inF === T.E4M3 && outCode === 10)) note = `undefined: ${inF.name} → ${outF.name} (only FP32 converts)`;
      if (!toDst && (outCode === 0 || outCode === 8)) note = "undefined: 32-bit datums only fit Dest";
      if (a.zero) { v = 0; zerosAfter = 0; }
      const srcId = srcTag && srcTag.src != null ? srcTag.src : null;
      // write datum + decompression zeros + upsample slots
      for (let j = 0; j <= zerosAfter; j++) {
        const val = j ? 0 : v;
        if (decompDrop) { decompDrop--; continue; }
        for (let k = 0; k <= upZeros; k++, out++) {
          if (inter && k !== 0) continue;
          const datum = k ? 0 : val;
          let row = out >> 4, col = out & 15, where;
          if (u === 1) { row += unpk[u].row; if (row >= 64) { tr("e", `SrcB row ${row} ≥ 64: undefined`); continue; } where = {R: "B", b: unpk[u].bank, idx: row * 16 + col}; }
          else if (!toDst) {
            if (row < 4 || col < colShift) continue;
            row -= 4; col -= colShift;
            if (cfg.srca_override) row &= 63; else { if (row >= 16) { tr("e", `SrcA row ${row} ≥ 16 without SetOvrdWithAddr: undefined`); continue; } row += unpk[u].row; }
            if (transpose) { const lo = row & 15; row = (row & ~15) | col; col = lo; }
            where = {R: "A", b: unpk[u].bank, idx: (row & 63) * 16 + col};
          } else { row = (row - 4) & 0x3ff; where = {R: "D", b: 0, idx: row * 16 + col}; }
          const file = where.R === "D" ? dest : (where.R === "A" ? srcA : srcB)[where.b];
          file.v[where.idx] = datum;
          const meta = {src: j || k ? null : srcId, step: step.n, u, ctx, readAt, bits, expBits, raw, v: datum, note, fill: j ? "decompressed zero" : k ? "upsample zero" : null, inF: inF.name, outF: outF.name};
          file.meta[where.idx] = meta;
          step.hotReg.add(`${where.R}${where.b}:${where.idx}`);
          if (meta.src != null) { if (!forward.has(meta.src)) forward.set(meta.src, []); forward.get(meta.src).push({...where, step: step.n}); }
          written++;
        }
        if (--decompNum === 0) break;
      }
    }
    if (toDst) { for (const b of [unpk[0].bank]) { srcA[b].v.fill(undefined); srcA[b].meta.fill({clobbered: true}); } tr("w", `  unpack to Dest also scrambles SrcA bank ${unpk[0].bank} (ISA doc: unpredictable values)`); }
    tr("", `${written} register slots written`);
    // --- counters for the next UNPACR
    if (multi && a.ctr) { let n = ctx + 1; if (n >= 1 << U.context_count) n = 0; unpk[u].ctr = n; tr("", `context counter → ${n}`); }
    ch0.Y += a.y0 ?? 0; ch0.Z += a.z0 ?? 0; ch1.Y += a.y1 ?? 0; ch1.Z += a.z1 ?? 0;
    if (a.y0 || a.z0 || a.y1 || a.z1) tr("", `counters: L1 Y0 ${ch0.Y} Z0 ${ch0.Z}, register Y1 ${ch1.Y} Z1 ${ch1.Z}`);
    if (a.flip) flip(u, step);
    else if (U.src_reg_set_update && !toDst) { unpk[u].row += 16 + ((u ? cfg.srcb_set_base : cfg.srca_set_base) << 4); tr("", `Src row pointer += 16 → ${unpk[u].row}`); }
  }

  return {cfg, l1, buffers, steps, srcA, srcB, dest, forward, adc, unpk, bankOwner};
}
function fmtVal(v) { return typeof v === "number" && Number.isInteger(v) && v > 255 ? T.hex(v) : String(v); }

const api = {FIELDS, OPS, rawName, defaultConfig, cloneConfig, setKey, getKey, simulate, buildInputs, tileStart};
if (typeof module !== "undefined" && module.exports) module.exports = api; else root.UnpackerModel = api;
})(typeof window !== "undefined" ? window : globalThis);
