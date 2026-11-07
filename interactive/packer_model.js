// Blackhole packer model: Dest -> L1. Pure simulation, no DOM. Sources:
//   tt-isa-documentation WormholeB0 PACR.md, Packers/*.md (functional models; Blackhole deltas noted inline)
//   blackhole-py-rewrite config.py + tests/hw/test_contexts.py (what card 0 confirmed)
//   tt-llk tt_llk_blackhole llk_pack.h (how the four read interfaces are used)
(function (root) {
"use strict";
const T = typeof module !== "undefined" && module.exports ? require("./common.js") : root.TT;

const SECTIONS = ["THCON_SEC0_REG1", "THCON_SEC0_REG8", "THCON_SEC1_REG1", "THCON_SEC1_REG8"];

// ***** configuration schema *****
// scope: "shared" (one copy), "ctx" (one per PACR cfg_ctx 0..3), "am" (3 packer ADDR_MOD slots), "setup" (the explorer, not hardware)
// conf: "hw" = confirmed on card 0 by tests/hw, "isa" = ISA doc functional model, "inf" = inferred (tt-llk usage), "sim" = explorer only
const FIELDS = [
  // --- Dest read / early conversion
  {g: "Dest read", key: "read_32b_dest", type: "bool", raw: "PCK_DEST_RD_CTRL_Read_32b_data", doc: "Dest holds 32-bit datums (fp32 Dest). Packer reads 32-bit rows.", conf: "isa"},
  {g: "Dest read", key: "dest_format", type: "fmt", raw: "ALU_FORMAT_SPEC_REG2_Dstacc", doc: "What Dest holds when it is 16-bit. Also decides whether the ReLU threshold is read as FP16 or BF16.", conf: "isa"},
  {g: "Dest read", key: "read_raw", type: "bool", raw: "PCK_DEST_RD_CTRL_Read_int8", doc: "\"Read_raw\" in the ISA doc: early conversion truncates instead of rounding.", conf: "isa"},
  {g: "Dest read", key: "read_unsigned", type: "bool", raw: "PCK_DEST_RD_CTRL_Read_unsigned", doc: "INT8 output is unsigned (UINT8).", conf: "isa"},
  {g: "Dest read", key: "round_10b_mantissa", type: "bool", raw: "PCK_DEST_RD_CTRL_Round_10b_mant", doc: "Round to 10 mantissa bits first (needed for FP8 E4M3 output).", conf: "isa"},
  {g: "Dest read", key: "stochastic_round", type: "bool", raw: "ALU_ROUNDING_MODE_Packer_srnd_en", doc: "Stochastic rounding in the packer (seeded here so runs repeat).", conf: "isa"},
  // --- input address generator (shared strides)
  {g: "Input address (Dest)", key: "in_counter_base", type: "int", raw: "PCK0_ADDR_BASE_REG_0_Base", doc: "Added to every Dest address, in bytes of In_data_format.", conf: "isa"},
  {g: "Input address (Dest)", key: "in_x_stride", type: "int", raw: "PCK0_ADDR_CTRL_XY_REG_0_Xstride", doc: "Only the low 4 bits are used. Sane values: 0 or bytes per datum.", conf: "isa"},
  {g: "Input address (Dest)", key: "in_y_stride", type: "int", raw: "PCK0_ADDR_CTRL_XY_REG_0_Ystride", doc: "Bytes per Y step. 16 × bytes per datum = one Dest row.", conf: "isa"},
  {g: "Input address (Dest)", key: "in_z_stride", type: "int", raw: "PCK0_ADDR_CTRL_ZW_REG_0_Zstride", doc: "Bytes per Z step. 256 × bytes per datum = one face.", conf: "isa"},
  {g: "Input address (Dest)", key: "in_w_stride", type: "int", raw: "PCK0_ADDR_CTRL_ZW_REG_0_Wstride", doc: "Bytes per W step. 1024 × bytes per datum = one tile.", conf: "isa"},
  // --- output address generator (shared strides)
  {g: "Output address (L1)", key: "out_counter_base", type: "int", raw: "PCK0_ADDR_BASE_REG_1_Base", doc: "Bytes, added to the L1 address when a new address is taken.", conf: "isa"},
  {g: "Output address (L1)", key: "out_y_stride", type: "int", raw: "PCK0_ADDR_CTRL_XY_REG_1_Ystride", doc: "Bytes per output Y step. Blackhole uses bytes (16B aligned); Wormhole only 256B steps.", conf: "isa"},
  {g: "Output address (L1)", key: "out_z_stride", type: "int", raw: "PCK0_ADDR_CTRL_ZW_REG_1_Zstride", doc: "", conf: "isa"},
  {g: "Output address (L1)", key: "out_w_stride", type: "int", raw: "PCK0_ADDR_CTRL_ZW_REG_1_Wstride", doc: "", conf: "isa"},
  {g: "Output address (L1)", key: "pack_limit_address", type: "hex", raw: "THCON_SEC0_REG9_Pack_limit_address", doc: "L1 ring buffer end. 0 = off. Address wraps when above limit × 2 + 1 (16B units).", conf: "isa"},
  {g: "Output address (L1)", key: "pack_fifo_size", type: "hex", raw: "THCON_SEC0_REG9_Pack_fifo_size", doc: "Ring size subtracted on wrap (× 2, 16B units).", conf: "isa"},
  // --- edge masks (shared: follow the row set, not the context)
  {g: "Edge masks", key: "edge_mask_0", type: "hex", raw: "PCK_EDGE_OFFSET_SEC0_mask", doc: "16 bits, one per Dest column. 0xFFFF keeps the whole row.", conf: "hw"},
  {g: "Edge masks", key: "edge_mask_1", type: "hex", raw: "PCK_EDGE_OFFSET_SEC1_mask", doc: "", conf: "hw"},
  {g: "Edge masks", key: "edge_mask_2", type: "hex", raw: "PCK_EDGE_OFFSET_SEC2_mask", doc: "", conf: "isa"},
  {g: "Edge masks", key: "edge_mask_3", type: "hex", raw: "PCK_EDGE_OFFSET_SEC3_mask", doc: "", conf: "isa"},
  {g: "Edge masks", key: "edge_mode", type: "enum", opts: [[0, "masked → 0"], [1, "masked → −inf"]], raw: "PCK_EDGE_mode", doc: "What a masked datum becomes.", conf: "isa"},
  {g: "Edge masks", key: "row_set_select_0", type: "int", raw: "PCK_EDGE_tile_row_set_select_0", doc: "Which row-set mapping read interface 0 uses (0..3).", conf: "isa"},
  {g: "Edge masks", key: "row_set_select_1", type: "int", raw: "PCK_EDGE_tile_row_set_select_1", doc: "", conf: "isa"},
  {g: "Edge masks", key: "row_set_select_2", type: "int", raw: "PCK_EDGE_tile_row_set_select_2", doc: "", conf: "isa"},
  {g: "Edge masks", key: "row_set_select_3", type: "int", raw: "PCK_EDGE_tile_row_set_select_3", doc: "", conf: "isa"},
  {g: "Edge masks", key: "row_set_mapping_0", type: "map", raw: "TILE_ROW_SET_MAPPING_0", doc: "2 bits per row position Y (0..15): which edge mask that row uses.", conf: "hw"},
  {g: "Edge masks", key: "row_set_mapping_1", type: "map", raw: "TILE_ROW_SET_MAPPING_1", doc: "", conf: "isa"},
  {g: "Edge masks", key: "row_set_mapping_2", type: "map", raw: "TILE_ROW_SET_MAPPING_2", doc: "", conf: "isa"},
  {g: "Edge masks", key: "row_set_mapping_3", type: "map", raw: "TILE_ROW_SET_MAPPING_3", doc: "", conf: "isa"},
  {g: "Edge masks", key: "face_set_select_enable", type: "bool", raw: "PCK_EDGE_TILE_FACE_SET_SELECT_enable", doc: "Pick the row-set mapping per face (position Z) instead of per interface.", conf: "isa"},
  {g: "Edge masks", key: "face_set_select", type: "hex", raw: "PCK_EDGE_TILE_FACE_SET_SELECT_select", doc: "2 bits per interface: which face-set mapping it uses.", conf: "isa"},
  {g: "Edge masks", key: "face_set_mapping_0", type: "map", raw: "TILE_FACE_SET_MAPPING_0", doc: "2 bits per face position Z: which row-set mapping.", conf: "isa"},
  {g: "Edge masks", key: "face_set_mapping_1", type: "map", raw: "TILE_FACE_SET_MAPPING_1", doc: "", conf: "isa"},
  {g: "Edge masks", key: "face_set_mapping_2", type: "map", raw: "TILE_FACE_SET_MAPPING_2", doc: "", conf: "isa"},
  {g: "Edge masks", key: "face_set_mapping_3", type: "map", raw: "TILE_FACE_SET_MAPPING_3", doc: "", conf: "isa"},
  // --- ReLU, histogram
  {g: "ReLU", key: "relu_mode", type: "enum", opts: [[0, "off"], [1, "x ≤ 0 → 0"], [2, "x ≤ t → 0"], [3, "clamp to [0, t]"]], raw: "STACC_RELU_ApplyRelu", doc: "Applied after early conversion and edge masking.", conf: "isa"},
  {g: "ReLU", key: "relu_threshold", type: "hex", raw: "STACC_RELU_ReluThreshold", doc: "16-bit float bits: BF16 (or FP16 when Dest format is an FP16 family).", conf: "isa"},
  {g: "Exponent histogram", key: "acc_stats", type: "bool", raw: "ENABLE_ACC_STATS_Enable (ThreadConfig)", doc: "Count exponents (low 5 bits) of every datum after ReLU. CLREXPHIST resets.", conf: "isa"},
  // --- per context (PACR cfg_ctx)
  {g: "Formats", s: "ctx", key: "src_format", type: "fmt", raw: "In_data_format", doc: "Format the packer converts from. Also sets bytes per datum for the Dest address (low 2 bits).", conf: "isa"},
  {g: "Formats", s: "ctx", key: "dst_format", type: "fmt", raw: "Out_data_format", doc: "Format written to L1.", conf: "isa"},
  {g: "Formats", s: "ctx", key: "fp8_e4m3", type: "bool", raw: "Pac_LF8_4b_exp", doc: "FP8 output uses E4M3 instead of E5M2.", conf: "isa"},
  {g: "Formats", s: "ctx", key: "exp_threshold_enable", type: "bool", raw: "Exp_threshold_en", doc: "Datums whose exponent is below the threshold become 0.", conf: "isa"},
  {g: "Formats", s: "ctx", key: "exp_threshold", type: "int", raw: "Exp_threshold", doc: "Biased exponent. 113 flushes values too small for BFP-A formats.", conf: "isa"},
  {g: "Formats", s: "ctx", key: "downsample_mask", type: "hex", raw: "Downsample_mask", doc: "Keep datum i of each 16 when bit i is set. 0 or 0xFFFF keeps all.", conf: "isa"},
  {g: "Formats", s: "ctx", key: "disable_zero_compress", type: "bool", raw: "Disable_zero_compress", doc: "1 = write datums as-is. 0 = zero-compress (row start index + 4-bit zero counts).", conf: "isa"},
  {g: "Formats", s: "ctx", key: "l1_accumulate", type: "bool", raw: "Pack_L1_Acc", doc: "Add into what L1 already holds instead of overwriting.", conf: "isa"},
  {g: "L1 destination", s: "ctx", key: "l1_dest", type: "hex", raw: "L1_Dest_addr", doc: "16B units minus one: data lands at (field + 1) × 16 unless the header subtract bit is set.", conf: "hw"},
  {g: "L1 destination", s: "ctx", key: "sub_tile_header_size", type: "bool", raw: "Sub_l1_tile_header_size", doc: "Do not add the +1 (16 bytes) to L1_Dest_addr.", conf: "isa"},
  {g: "L1 destination", s: "ctx", key: "add_l1_dest_offset", type: "bool", raw: "Add_l1_dest_addr_offset", doc: "Also add the l1_dest_addr_offset value below (set by TDMA-RISC in hardware).", conf: "isa"},
  {g: "L1 destination", s: "ctx", key: "l1_dest_offset", type: "hex", raw: "(packer l1_dest_addr_offset, TDMA-RISC)", doc: "16B units.", conf: "isa"},
  {g: "L1 destination", s: "ctx", key: "row_start_section_size", type: "int", raw: "Row_start_section_size", doc: "16B units reserved for the row start index when compressing.", conf: "isa"},
  {g: "L1 destination", s: "ctx", key: "exp_section_size", type: "int", raw: "Exp_section_size", doc: "16B units reserved for BFP exponents. Only applied when Out_data_format has bit 1 set (BFP, FP8, INT8).", conf: "isa"},
  {g: "Dest window", s: "ctx", key: "dest_row_offset", type: "int", raw: "DEST_TARGET_REG_CFG_PACK_SEC{i}_Offset", doc: "Added to every Dest read, in rows.", conf: "hw"},
  {g: "Dest window", s: "ctx", key: "dest_z_offset", type: "int", raw: "DEST_TARGET_REG_CFG_PACK_SEC{i}_ZOffset", doc: "Added to position Z for the face-set mapping.", conf: "isa"},
  {g: "Dest window", s: "ctx", key: "reads_per_xy_plane", type: "int", raw: "PACK_COUNTERS_SEC{i}_pack_reads_per_xy_plane", doc: "Where row position Y wraps (and Z steps). Chooses each row's edge mask.", conf: "hw"},
  {g: "Dest window", s: "ctx", key: "yz_transposed", type: "bool", raw: "PACK_COUNTERS_SEC{i}_pack_yz_transposed", doc: "Row position steps Z first, then Y.", conf: "isa"},
  // --- packer ADDR_MODs (ThreadConfig, SETC16)
  {g: "Address modifiers", s: "am", key: "y_src_incr", type: "int", raw: "ADDR_MOD_PACK_SEC{i}_YsrcIncr", doc: "After the PACR: Dest Y += this.", conf: "hw"},
  {g: "Address modifiers", s: "am", key: "y_src_carry", type: "bool", raw: "ADDR_MOD_PACK_SEC{i}_YsrcCR", doc: "Add to the carry register and copy it to Y.", conf: "isa"},
  {g: "Address modifiers", s: "am", key: "y_src_clear", type: "bool", raw: "ADDR_MOD_PACK_SEC{i}_YsrcClear", doc: "Dest Y = 0.", conf: "hw"},
  {g: "Address modifiers", s: "am", key: "z_src_incr", type: "int", raw: "ADDR_MOD_PACK_SEC{i}_ZsrcIncr", doc: "Dest Z += this (next face).", conf: "hw"},
  {g: "Address modifiers", s: "am", key: "z_src_clear", type: "bool", raw: "ADDR_MOD_PACK_SEC{i}_ZsrcClear", doc: "", conf: "hw"},
  {g: "Address modifiers", s: "am", key: "y_dst_incr", type: "int", raw: "ADDR_MOD_PACK_SEC{i}_YdstIncr", doc: "L1 Y += this.", conf: "isa"},
  {g: "Address modifiers", s: "am", key: "y_dst_carry", type: "bool", raw: "ADDR_MOD_PACK_SEC{i}_YdstCR", doc: "", conf: "isa"},
  {g: "Address modifiers", s: "am", key: "y_dst_clear", type: "bool", raw: "ADDR_MOD_PACK_SEC{i}_YdstClear", doc: "", conf: "isa"},
  {g: "Address modifiers", s: "am", key: "z_dst_incr", type: "int", raw: "ADDR_MOD_PACK_SEC{i}_ZdstIncr", doc: "", conf: "isa"},
  {g: "Address modifiers", s: "am", key: "z_dst_clear", type: "bool", raw: "ADDR_MOD_PACK_SEC{i}_ZdstClear", doc: "", conf: "isa"},
  // --- explorer setup (not hardware)
  {g: "Explorer setup", key: "dest_pattern", type: "pattern", raw: "(explorer)", doc: "Values preloaded into Dest rows 0..255 (4 tiles).", conf: "sim"},
  {g: "Explorer setup", key: "seed", type: "int", raw: "(explorer)", doc: "Seed for random patterns and stochastic rounding.", conf: "sim"},
  {g: "Explorer setup", key: "l1_init", type: "enum", opts: [["empty", "empty"], ["ones", "1.0 in the output format"]], raw: "(explorer)", doc: "What L1 holds before the program (matters for L1 accumulate).", conf: "sim"},
  {g: "Explorer setup", key: "tpg_reset_on_last", type: "bool", raw: "(model assumption)", doc: "Reset the edge-mask row position when a PACR has Last or Flush. Not probed on hardware.", conf: "inf"},
];

const AM_FIELDS = FIELDS.filter(f => f.s === "am").map(f => f.key);
const CTX_FIELDS = FIELDS.filter(f => f.s === "ctx").map(f => f.key);

function rawName(f, i) {
  if (f.s === "ctx") return f.raw.includes("{i}") ? f.raw.replace("{i}", i) : `${SECTIONS[i]}_${f.raw}`;
  if (f.s === "am") return f.raw.replace("{i}", i);
  return f.raw;
}

function defaultCtx() {
  return {src_format: 5, dst_format: 5, fp8_e4m3: false, exp_threshold_enable: false, exp_threshold: 0, downsample_mask: 0,
    disable_zero_compress: true, l1_accumulate: false, l1_dest: (0x20000 >> 4) - 1, sub_tile_header_size: false,
    add_l1_dest_offset: false, l1_dest_offset: 0, row_start_section_size: 0, exp_section_size: 4,
    dest_row_offset: 0, dest_z_offset: 0, reads_per_xy_plane: 16, yz_transposed: false};
}
function amFrom(word) {  // decode a SETC16 ADDR_MOD_PACK value (cfg_defines bit layout)
  return {y_src_incr: word & 15, y_src_carry: !!(word >> 4 & 1), y_src_clear: !!(word >> 5 & 1),
    y_dst_incr: word >> 6 & 15, y_dst_carry: !!(word >> 10 & 1), y_dst_clear: !!(word >> 11 & 1),
    z_src_incr: word >> 12 & 1, z_src_clear: !!(word >> 13 & 1), z_dst_incr: word >> 14 & 1, z_dst_clear: !!(word >> 15 & 1)};
}
function amWord(a) {
  return (a.y_src_incr & 15) | a.y_src_carry << 4 | a.y_src_clear << 5 | (a.y_dst_incr & 15) << 6 | a.y_dst_carry << 10 |
    a.y_dst_clear << 11 | (a.z_src_incr & 1) << 12 | a.z_src_clear << 13 | (a.z_dst_incr & 1) << 14 | a.z_dst_clear << 15;
}
function defaultConfig() {
  return {
    read_32b_dest: true, dest_format: 0, read_raw: false, read_unsigned: false, round_10b_mantissa: false, stochastic_round: false,
    in_counter_base: 0, in_x_stride: 0, in_y_stride: 32, in_z_stride: 512, in_w_stride: 2048,
    out_counter_base: 0, out_y_stride: 0, out_z_stride: 0, out_w_stride: 0, pack_limit_address: 0, pack_fifo_size: 0,
    edge_mask_0: 0xFFFF, edge_mask_1: 0, edge_mask_2: 0, edge_mask_3: 0, edge_mode: 0,
    row_set_select_0: 0, row_set_select_1: 0, row_set_select_2: 0, row_set_select_3: 0,
    row_set_mapping_0: 0, row_set_mapping_1: 0, row_set_mapping_2: 0, row_set_mapping_3: 0,
    face_set_select_enable: false, face_set_select: 0, face_set_mapping_0: 0, face_set_mapping_1: 0, face_set_mapping_2: 0, face_set_mapping_3: 0,
    relu_mode: 0, relu_threshold: 0, acc_stats: false,
    ctx: [0, 1, 2, 3].map(defaultCtx),
    am: [amFrom(0x0104), amFrom(0x2820), amFrom(0x1120)],  // blackhole-py ttko Pack
    dest_pattern: "rows", seed: 1, l1_init: "empty", tpg_reset_on_last: true,
  };
}
function cloneConfig(c) { return JSON.parse(JSON.stringify(c)); }

// key path "ctx1.l1_dest", "am0.y_src_incr", "edge_mask_0"
function setKey(cfg, key, value) {
  let m = key.match(/^ctx(\d)\.(\w+)$/);
  if (m) { if (!(m[2] in cfg.ctx[+m[1]])) throw new Error(`no context field ${m[2]}`); cfg.ctx[+m[1]][m[2]] = coerce(cfg.ctx[+m[1]][m[2]], value); return; }
  m = key.match(/^am(\d)\.(\w+)$/);
  if (m) { if (+m[1] > 2) throw new Error("packer has 3 ADDR_MOD slots (0..2)"); if (!(m[2] in cfg.am[+m[1]])) throw new Error(`no addr-mod field ${m[2]}`); cfg.am[+m[1]][m[2]] = coerce(cfg.am[+m[1]][m[2]], value); return; }
  m = key.match(/^am(\d)$/);
  if (m) { cfg.am[+m[1]] = amFrom(value); return; }
  if (!(key in cfg) || key === "ctx" || key === "am") throw new Error(`no config field ${key}`);
  cfg[key] = coerce(cfg[key], value);
}
function coerce(old, v) { return typeof old === "boolean" ? !!v : typeof old === "number" ? Number(v) : v; }
function getKey(cfg, key) {
  let m = key.match(/^ctx(\d)\.(\w+)$/); if (m) return cfg.ctx[+m[1]][m[2]];
  m = key.match(/^am(\d)\.(\w+)$/); if (m) return cfg.am[+m[1]][m[2]];
  return cfg[key];
}

// ***** instructions *****
const OPS = {
  PACR: {args: ["ctx", "am", "last", "flush", "zero", "concat", "intf"], doc: "Pack. ctx = config context (cfg_ctx, 0..3), am = ADDR_MOD slot (0..2), intf = ReadIntfSel (0 = all four interfaces = 4 Dest rows), last/flush close the output, zero = read zeros, concat = continue the compression row."},
  SETADCXX: {args: ["x0", "x1"], doc: "x0 = first datum of a row (ch0 X), x1 = last datum (ch1 X). Each interface reads x1 − x0 + 1 datums."},
  SETADCXY: {args: ["x0", "y0", "x1", "y1"], doc: "Set any of ch0/ch1 X and Y (and their carry registers)."},
  SETADCZW: {args: ["z0", "w0", "z1", "w1"], doc: "Set any of ch0/ch1 Z and W."},
  SETADC: {args: ["ch", "x", "y", "z", "w"], doc: "Set one counter of one channel, e.g. SETADC ch=0 w=1 picks Dest tile 1."},
  INCADCXY: {args: ["x0", "y0", "x1", "y1"], doc: "Add to counters."},
  INCADCZW: {args: ["z0", "w0", "z1", "w1"], doc: "Add to counters."},
  ADDRCRXY: {args: ["x0", "y0", "x1", "y1"], doc: "Add to the carry register, then copy it to the counter."},
  ADDRCRZW: {args: ["z0", "w0", "z1", "w1"], doc: "Add to the carry register, then copy it to the counter."},
  CFG: {args: [], argPrefix: /^(ctx\d\.\w+|am\d(\.\w+)?|\w+)$/, doc: "Write config mid-program, e.g. CFG ctx1.l1_dest=0x2FFF edge_mask_1=0. (In a kernel: a RISC-V store, WRCFG, RMWCIB or SETC16.)"},
  CLREXPHIST: {args: [], doc: "Reset the exponent histogram."},
};

// ***** the simulation *****
function bytesPerDatum(code) { const lo = code & 3; return lo === 0 ? 4 : lo === 1 ? 2 : 1; }
function xMask(code) { const b = bytesPerDatum(code); return b === 4 ? 3 : b === 2 ? 7 : 15; }
function expOf(v, family8) {  // biased exponent as the packer sees it
  const a = Math.abs(v); if (!a || !Number.isFinite(a)) return a === Infinity ? (family8 ? 255 : 31) : 0;
  const bias = family8 ? 127 : 15, max = family8 ? 255 : 31;
  return Math.max(0, Math.min(max, T.ilog2(a) + bias));
}
function isFp16Family(code) { return [1, 10, 2, 3, 11].includes(code); }
function earlyFormat(c) {  // format datums are held in between early and late conversion
  const f = T.FORMATS[c.src_format];
  if (!f) return T.FORMATS[5];
  if (f.kind === "bfp") return f.expA ? {kind: "float", E: 5, M: 7, bias: 15, name: "E5M7"} : {kind: "float", E: 8, M: 6, bias: 127, name: "E8M6"};
  return f;
}
function q(v, f, opts) { if (f.kind === "float" && !T.FORMATS[f.code]) return T.decMini(T.encMini(v, f.E, f.M, f.bias, opts), f.E, f.M, f.bias); return T.quantize(v, f, opts); }

class Stream {  // one of the packer's three output streams (row start index, exponents, datums)
  constructor(name) { this.name = name; this.addr = null; this.needsNew = true; this.pending = []; this.bits = 0; this.written = 0; }
}

function makeDest(cfg) {
  const n = 1024 * 16, vals = new Array(n).fill(0);
  const pat = T.pattern(cfg.dest_pattern, 256 * 16, cfg.seed);
  const df = cfg.read_32b_dest ? T.FORMATS[0] : (T.FORMATS[cfg.dest_format] || T.FORMATS[5]);
  for (let i = 0; i < pat.length; i++) vals[i] = df.kind === "bfp" ? pat[i] : T.quantize(pat[i], df);
  return vals;
}

function simulate(cfg0, program, upto = Infinity) {
  const cfg = cloneConfig(cfg0);
  const dest = makeDest(cfg);
  const l1 = new T.L1();
  const rnd = T.mulberry32(cfg.seed * 7919 + 1);
  const adc = {ch: [{X: 0, Y: 0, Z: 0, W: 0, X_Cr: 0, Y_Cr: 0, Z_Cr: 0, W_Cr: 0}, {X: 15, Y: 0, Z: 0, W: 0, X_Cr: 15, Y_Cr: 0, Z_Cr: 0, W_Cr: 0}]};
  const tpg = {X: 0, Y: 0, Z: 0};
  const streams = {rsi: new Stream("row start index"), exp: new Stream("exponents"), data: new Stream("datums")};
  const hist = new Array(32).fill(0); let histMax = 0;
  const pk = {rowBuf: [], augQueue: [], dataQueue: [], rsiCount: 0, outFmt: null, ctx: 0, compress: false, rsiStarted: false};
  const journeys = new Map();   // dest index -> [{step, ...}]
  const steps = [];             // per executed instruction: {ins, trace[], hotDest:Set, hotL1:Set, error}
  const l1Init = cfg.l1_init;

  function journey(i, e) { if (!journeys.has(i)) journeys.set(i, []); journeys.get(i).push(e); }

  // --- output streams
  function commitChunk(s, step, final) {
    // write 16 bytes (128 bits) of pending bits at s.addr
    const chunk = [];
    let bits = 0;
    while (s.pending.length && bits + s.pending[0].n <= 128) { const p = s.pending.shift(); chunk.push(p); bits += p.n; }
    if (final) while (bits < 128) { chunk.push({v: 0, n: Math.min(8, 128 - bits), tag: {kind: "pad"}}); bits += Math.min(8, 128 - bits); }
    let bitAddr = s.addr * 8;
    const c = cfg.ctx[pk.ctx];
    for (const p of chunk) {
      let v = p.v;
      if (p.tag.kind === "data" && c.l1_accumulate && p.fmt && p.fmt.kind !== "bfp") {
        const old = l1.has(bitAddr >> 3) ? T.decode(l1.readBits(bitAddr / 8, p.n / 8), p.fmt) : 0;
        const sum = old + T.decode(v, p.fmt);
        v = T.encode(sum, p.fmt);
        p.tag.acc = {old, sum: T.decode(v, p.fmt)};
      }
      l1.writeBits(bitAddr / 8, p.n / 8, v, {...p.tag, step});
      for (let b = bitAddr >> 3; b < (bitAddr + p.n + 7) >> 3; b++) step.hotL1.add(b);
      if (p.tag.kind === "data" && p.tag.src != null) {
        const j = journeys.get(p.tag.src); if (j && j.length) { const last = j[j.length - 1]; last.l1 = (last.l1 || []).concat([{addr: bitAddr / 8, bits: v, nbits: p.n, acc: p.tag.acc}]); }
      }
      bitAddr += p.n;
    }
    s.addr += 16; s.written += 16; s.bits -= Math.min(bits, s.bits);
  }
  function push(s, v, n, tag, step, f) {
    if (s.addr === null) { step.trace.push(["e", `${s.name} stream has no address yet: no PACR has started it`]); return; }
    s.pending.push({v, n, tag, fmt: f}); s.bits += n;
    while (s.bits >= 128) commitChunk(s, step, false);
  }
  function flushStream(s, step) { if (s.addr !== null && s.bits > 0) commitChunk(s, step, true); s.pending = []; s.bits = 0; }

  // late conversion + compression framing for queued datums
  function drain(step, final) {
    const c = cfg.ctx[pk.ctx];
    const f = T.fmt(c.dst_format, c.fp8_e4m3) || T.FORMATS[5];
    const opts = {round: cfg.stochastic_round ? "stoch" : "rne", sat: true, unsigned: cfg.read_unsigned};
    // 1. late conversion (BFP needs 16 at a time)
    while (pk.augQueue.length && (f.kind !== "bfp" || pk.augQueue.length >= 16 || final)) {
      const blk = pk.augQueue.splice(0, f.kind === "bfp" ? 16 : 1);
      if (f.kind === "bfp") {
        const vals = blk.map(d => stoch(d.v, f));
        const b = T.bfpBlock(vals, f);
        push(streams.exp, b.exp, 8, {kind: "exp", srcs: blk.map(d => d.src), exp: b.exp}, step);
        blk.forEach((d, k) => { d.bits = b.bits[k]; d.out = b.values[k]; d.exp = b.exp; });
        step.trace.push(["c", `  BFP block of ${blk.length}: shared exponent ${b.exp} (${f.expA ? "5-bit, bias 15" : "8-bit, bias 127"})`]);
      } else blk.forEach(d => { d.bits = T.encode(stoch(d.v, f), f, opts); d.out = T.decode(d.bits, f, opts); });
      for (const d of blk) {
        const j = journeys.get(d.src); if (j && j.length) Object.assign(j[j.length - 1], {out: d.out, outBits: d.bits, outFmt: f.name, exp: d.exp, zeros: d.zeros});
        pk.dataQueue.push(d);
      }
    }
    // 2. write datums (compressed: groups of 32 datums + 32 four-bit zero counts)
    const nb = f.bytes * 8;
    if (!pk.compress) { for (const d of pk.dataQueue.splice(0)) push(streams.data, d.bits, nb, {kind: "data", src: d.src}, step, f); return; }
    while (pk.dataQueue.length >= 32 || (final && pk.dataQueue.length)) {
      const grp = pk.dataQueue.splice(0, 32);
      grp.forEach(d => push(streams.data, d.bits, nb, {kind: "data", src: d.src, zeros: d.zeros}, step, f));
      for (let k = grp.length; k < 32; k++) push(streams.data, 0, nb, {kind: "pad"}, step);
      grp.forEach(d => push(streams.data, d.zeros, 4, {kind: "rle", src: d.src, zeros: d.zeros}, step));
      for (let k = grp.length; k < 32; k++) push(streams.data, 0, 4, {kind: "pad"}, step);
    }
  }
  function stoch(v, f) {
    if (!cfg.stochastic_round || !Number.isFinite(v) || v === 0) return v;
    // add up to half an output ulp of noise; rounding to nearest then acts stochastically
    const M = f.kind === "bfp" ? f.magBits - 1 : f.M ?? 7; const ulp = 2 ** (T.ilog2(Math.abs(v)) - M);
    return v + (rnd() - 0.5) * ulp;
  }
  function closeRow(step) {
    if (!pk.rowBuf.length) return;
    const aug = T.compressRow(pk.rowBuf, d => d.v === 0 || Object.is(d.v, -0));
    for (const g of aug) { g.item.zeros = g.zeros; for (const s of g.skipped) { const j = journeys.get(s.src); if (j && j.length) j[j.length - 1].elided = true; } pk.augQueue.push(g.item); }
    pk.rsiCount += aug.length;
    push(streams.rsi, pk.rsiCount, 16, {kind: "rsi", value: pk.rsiCount}, step);
    step.trace.push(["c", `  compression row: ${pk.rowBuf.length} datums → ${aug.length} kept (zero runs folded into counts). RSI += ${pk.rsiCount}`]);
    pk.rowBuf = [];
  }

  // initial L1 contents for accumulation demos
  if (l1Init === "ones") {
    const c = cfg.ctx[0], f = T.fmt(c.dst_format, c.fp8_e4m3);
    const start = (c.l1_dest + (c.sub_tile_header_size ? 0 : 1)) * 16;
    if (f && f.kind !== "bfp") for (let i = 0; i < 1024; i++) l1.writeBits(start + i * f.bytes, f.bytes, T.encode(1, f), {kind: "init"});
  }
  let stepNo = 0;
  for (const ins of program) {
    if (stepNo >= upto) break;
    const step = {ins, trace: [], hotDest: new Set(), hotL1: new Set(), error: null, n: stepNo};
    steps.push(step); stepNo++;
    const a = ins.args;
    const tr = (cls, s) => step.trace.push([cls, s]);
    try {
      switch (ins.op) {
      case "SETADCXX": {
        if (a.x0 != null) { adc.ch[0].X = adc.ch[0].X_Cr = a.x0; }
        if (a.x1 != null) { adc.ch[1].X = adc.ch[1].X_Cr = a.x1; }
        tr("", `ch0.X = ${adc.ch[0].X} (first datum), ch1.X = ${adc.ch[1].X} (last datum)\n→ each interface reads ${adc.ch[1].X - adc.ch[0].X + 1} datums`);
        break; }
      case "SETADCXY": case "SETADCZW": case "INCADCXY": case "INCADCZW": case "ADDRCRXY": case "ADDRCRZW": {
        const inc = ins.op.startsWith("INC"), cr = ins.op.startsWith("ADDRCR");
        for (const [k, v] of Object.entries(a)) {
          const ch = adc.ch[+k[1]], C = k[0].toUpperCase();
          if (inc) ch[C] += v; else if (cr) { ch[C + "_Cr"] += v; ch[C] = ch[C + "_Cr"]; } else { ch[C] = v; ch[C + "_Cr"] = v; }
          tr("", `ch${k[1]}.${C} ${inc ? "+= " + v : cr ? "carry += " + v : "= " + v} → ${ch[C]}`);
        }
        break; }
      case "SETADC": {
        const ch = adc.ch[a.ch ?? 0];
        for (const C of ["x", "y", "z", "w"]) if (a[C] != null) { ch[C.toUpperCase()] = ch[C.toUpperCase() + "_Cr"] = a[C]; tr("", `ch${a.ch ?? 0}.${C.toUpperCase()} = ${a[C]}`); }
        break; }
      case "CFG": {
        for (const [k, v] of Object.entries(a)) { const old = getKey(cfg, k); setKey(cfg, k, v); tr("", `${k}: ${fmtVal(old)} → ${fmtVal(getKey(cfg, k))}`); }
        break; }
      case "CLREXPHIST": hist.fill(0); histMax = 0; tr("", "exponent histogram cleared"); break;
      case "PACR": pacr(step, a); break;
      default: throw new Error(`not modeled: ${ins.op}`);
      }
    } catch (e) { step.error = e.message; tr("e", e.message); }
    step.adc = JSON.parse(JSON.stringify(adc));
    step.tpg = {...tpg};
    step.streams = Object.fromEntries(Object.entries(streams).map(([k, s]) => [k, {addr: s.addr, needsNew: s.needsNew, pendingBits: s.bits, written: s.written}]));
  }

  function pacr(step, a) {
    const ctx = a.ctx ?? 0, am = a.am ?? 0, last = !!a.last, flush = !!a.flush, zero = !!a.zero, concat = !!a.concat;
    if (ctx > 3) throw new Error("cfg_ctx is 2 bits: 0..3");
    if (am > 2) throw new Error("the packer has 3 ADDR_MOD slots (0..2)");
    const c = cfg.ctx[ctx];
    const tr = (cls, s) => step.trace.push([cls, s]);
    const intfSel = a.intf ?? 0;
    const intfs = intfSel === 0 ? [0, 1, 2, 3] : [0, 1, 2, 3].filter(i => intfSel >> i & 1);
    tr("h", `PACR cfg_ctx=${ctx} → config section ${ctx} (${SECTIONS[ctx]}): ${T.FORMATS[c.src_format]?.name} → ${T.fmt(c.dst_format, c.fp8_e4m3)?.name}`);
    if (pk.ctx !== ctx && (streams.data.bits || pk.augQueue.length || pk.rowBuf.length)) tr("w", `  note: switched context with output still buffered (model writes it with context ${ctx}'s format)`);
    pk.ctx = ctx;
    pk.compress = !c.disable_zero_compress;
    // --- output address generator (runs at instruction start)
    const ch1 = adc.ch[1];
    let addr16 = c.l1_dest + (c.sub_tile_header_size ? 0 : 1);
    let yzw = cfg.out_counter_base + ch1.Y * cfg.out_y_stride + ch1.Z * cfg.out_z_stride + ch1.W * cfg.out_w_stride;
    const yzw16 = yzw >> 4;
    tr("", `output: L1_Dest_addr ${T.hex(c.l1_dest)} + ${c.sub_tile_header_size ? 0 : 1}${c.sub_tile_header_size ? " (header subtract on)" : " (the +1 that l1_addr's −1 cancels)"}`);
    if (yzw) tr("", `  + (base ${cfg.out_counter_base} + Y1 ${ch1.Y}×${cfg.out_y_stride} + Z1 ${ch1.Z}×${cfg.out_z_stride} + W1 ${ch1.W}×${cfg.out_w_stride}) bytes >> 4 = ${yzw16}`);
    addr16 += yzw16;
    if (c.add_l1_dest_offset) { addr16 += c.l1_dest_offset; tr("", `  + l1_dest_addr_offset ${c.l1_dest_offset}`); }
    if (cfg.pack_limit_address && addr16 > cfg.pack_limit_address * 2 + 1) { addr16 -= cfg.pack_fifo_size * 2; tr("w", `  ring wrap: − fifo_size×2 → ${T.hex(addr16 * 16)}`); }
    const outF = T.fmt(c.dst_format, c.fp8_e4m3) || T.FORMATS[5];
    pk.outFmt = outF;
    const took = [];
    if (pk.compress && streams.rsi.needsNew) {
      streams.rsi.addr = (addr16 & 0x1ffff) << 4; streams.rsi.needsNew = false; took.push(`row start index @ ${T.hex(streams.rsi.addr)}`);
      addr16 += c.row_start_section_size; pk.rsiCount = 0;
      push(streams.rsi, 0, 16, {kind: "rsi", value: 0}, step);
    }
    if ((c.dst_format & 2) && streams.exp.needsNew) {
      streams.exp.addr = (addr16 & 0x1ffff) << 4; streams.exp.needsNew = false;
      if (outF.kind === "bfp") took.push(`exponents @ ${T.hex(streams.exp.addr)}`);
      addr16 += c.exp_section_size;
      if (c.exp_section_size && outF.kind !== "bfp") tr("w", `  Out_data_format has bit 1 set (${outF.name}), so Exp_section_size (${c.exp_section_size}) still shifts the data by ${c.exp_section_size * 16} bytes`);
    }
    if (streams.data.needsNew) { streams.data.addr = (addr16 & 0x1ffff) << 4; streams.data.needsNew = false; took.push(`datums @ ${T.hex(streams.data.addr)}`); }
    tr("", took.length ? `  new address: ${took.join(", ")}` : `  continues at ${T.hex(streams.data.addr + streams.data.bits / 8)} (no Last since the last address was taken)`);

    // --- input address generator
    const ch0 = adc.ch[0], bpd = bytesPerDatum(c.src_format), xm = xMask(c.src_format);
    const byteAddr = cfg.in_counter_base + ch0.X * (cfg.in_x_stride & 15) + ch0.Y * cfg.in_y_stride + ch0.Z * cfg.in_z_stride + ch0.W * cfg.in_w_stride;
    let datum = (Math.floor(byteAddr / bpd) & ~xm) + (ch0.X & xm);
    tr("", `input: (base ${cfg.in_counter_base} + Y ${ch0.Y}×${cfg.in_y_stride} + Z ${ch0.Z}×${cfg.in_z_stride} + W ${ch0.W}×${cfg.in_w_stride}${cfg.in_x_stride & 15 ? ` + X ${ch0.X}×${cfg.in_x_stride & 15}` : ""}) = ${byteAddr} bytes`);
    tr("", `  ÷ ${bpd} bytes/datum (In_data_format low bits) → datum ${datum}${ch0.X & xm ? ` (X ${ch0.X} adds within the row)` : ""}`);
    if (c.dest_row_offset) { datum += c.dest_row_offset * 16; tr("", `  + dest_row_offset ${c.dest_row_offset} rows (context ${ctx}) → datum ${datum}`); }
    const n = flush ? 0 : adc.ch[1].X - ch0.X + 1;
    tr("", `  Dest row ${datum >> 4}, col ${datum & 15}; ${n} datums per interface; interfaces ${intfs.join(",")}${intfs.length > 1 ? " read consecutive rows" : ""}`);
    if (n < 0) tr("e", "  ch1.X < ch0.X: nothing to read");

    // --- per-datum pipeline
    const ef = earlyFormat(c);
    const fam8 = !(ef.E === 5);
    const reluTh = isFp16Family(cfg.dest_format) ? T.decMini(cfg.relu_threshold, 5, 10, 15) : T.decMini(cfg.relu_threshold, 8, 7, 127);
    const ds = c.downsample_mask === 0 ? 0xFFFF : c.downsample_mask;
    const produced = [];
    let masked = 0, relued = 0, thresholded = 0, dropped = 0;
    for (const k of intfs) {
      let dmask = ds;
      const base = datum + 16 * k;
      for (let j = 0; j < Math.max(0, n); j++) {
        const di = (base + j) & 0x3fff;
        const row = di >> 4, col = di & 15;
        let v = zero ? 0 : (dest[di] ?? 0);
        const J = {step: step.n, ctx, k, row, col, read: v};
        if (!zero) step.hotDest.add(di);
        // early conversion
        let opts = {round: cfg.read_raw ? "trunc" : "rne"};
        if (cfg.round_10b_mantissa) v = T.decMini(T.encMini(v, 8, 10, 127), 8, 10, 127);
        v = q(v, ef, opts); J.early = v; J.earlyFmt = ef.name;
        // edge mask: tile position generator
        let b;
        if (cfg.face_set_select_enable) {
          const Z = c.dest_z_offset + tpg.Z, aa = cfg.face_set_select >> (2 * k) & 3;
          b = cfg[`face_set_mapping_${aa}`] >> (2 * (Z & 15)) & 3; J.edgeHow = `face-set ${aa}, Z ${Z} → row-set ${b}`;
        } else { b = cfg[`row_set_select_${k}`] & 3; J.edgeHow = `interface ${k} → row-set ${b}`; }
        const cm = cfg[`row_set_mapping_${b}`] >> (2 * (tpg.Y & 15)) & 3;
        const em = cfg[`edge_mask_${cm}`];
        J.tpg = {...tpg}; J.edge = {mapping: b, mask: cm, bits: em, keep: !!(em >> col & 1)};
        if (!(em >> col & 1)) { v = cfg.edge_mode ? -Infinity : 0; masked++; }
        // advance the tile position generator (uses this context's pack counters)
        tpg.X++;
        if (tpg.X === 16) {
          tpg.X = 0; const R = c.reads_per_xy_plane;
          if (c.yz_transposed) { tpg.Z++; if (tpg.Z === R) { tpg.Z = 0; tpg.Y++; } }
          else { tpg.Y++; if (tpg.Y === R) { tpg.Y = 0; tpg.Z++; } }
          tpg.Y &= 0xff; tpg.Z &= 0xff;
        }
        // ReLU
        const before = v;
        switch (cfg.relu_mode & 3) {
          case 1: v = v <= 0 ? 0 : v; break;
          case 2: v = v <= reluTh ? 0 : v; break;
          case 3: v = v <= 0 ? 0 : v > reluTh ? reluTh : v; break;
        }
        if (v !== before) relued++;
        J.relu = v;
        // exponent histogram
        const ex = expOf(v, fam8);
        if (cfg.acc_stats) hist[ex & 31] = Math.min(255, hist[ex & 31] + 1);
        histMax = Math.max(histMax, ex);
        // exponent thresholding
        if (c.exp_threshold_enable && v !== 0 && ex < c.exp_threshold) { v = 0; thresholded++; J.thresh = true; }
        // downsampling
        const keep = !!(dmask & 1);
        dmask = ((dmask << 15) | (dmask >> 1)) & 0xffff;
        J.down = keep;
        journey(di, J);
        if (!keep) { dropped++; continue; }
        produced.push({v, src: zero ? null : di});
      }
    }
    tr("", `pipeline: ${produced.length} datums out` + [masked && `${masked} edge-masked`, relued && `${relued} changed by ReLU`, thresholded && `${thresholded} below exp threshold`, dropped && `${dropped} dropped by downsample`].filter(Boolean).map(s => ", " + s).join(""));
    tr("c", `  edge-mask row position after: Y ${tpg.Y}, Z ${tpg.Z} (wraps at reads_per_xy_plane ${c.reads_per_xy_plane} of context ${ctx})`);
    // --- compression rows / late conversion / output
    if (pk.compress) { pk.rowBuf.push(...produced); if (!concat) closeRow(step); }
    else pk.augQueue.push(...produced.map(d => ({...d, zeros: 0})));
    drain(step, false);
    // --- AddrMod (counters for the next PACR)
    const A = cfg.am[am];
    const upd = (ch, Ykey, clr, cr, inc) => { if (clr) { ch.Y = 0; ch.Y_Cr = 0; } else if (cr) { ch.Y_Cr += inc; ch.Y = ch.Y_Cr; } else ch.Y += inc; };
    upd(ch0, "Y", A.y_src_clear, A.y_src_carry, A.y_src_incr);
    if (A.z_src_clear) { ch0.Z = 0; ch0.Z_Cr = 0; } else ch0.Z += A.z_src_incr;
    upd(ch1, "Y", A.y_dst_clear, A.y_dst_carry, A.y_dst_incr);
    if (A.z_dst_clear) { ch1.Z = 0; ch1.Z_Cr = 0; } else ch1.Z += A.z_dst_incr;
    tr("", `ADDR_MOD ${am} (${T.hex(amWord(A), 4)}): Dest Y→${ch0.Y} Z→${ch0.Z}, L1 Y→${ch1.Y} Z→${ch1.Z}`);
    if (last || flush) {
      if (pk.compress) { closeRow(step); }
      drain(step, true);
      for (const s of Object.values(streams)) { flushStream(s, step); s.needsNew = true; }
      if (cfg.tpg_reset_on_last) { tpg.X = tpg.Y = tpg.Z = 0; }
      tr("h", `${last ? "Last" : "Flush"}: buffered bytes padded to 16 and written; the next PACR takes a new L1 address`);
    } else if (streams.data.bits) tr("c", `  ${streams.data.bits / 8} bytes wait in the output buffer until 16 collect (or Last)`);
  }

  return {cfg, dest, l1, steps, journeys, hist, histMax, adc, tpg, streams, pending: {data: streams.data.pending.slice(), bits: streams.data.bits}};
}
function fmtVal(v) { return typeof v === "number" && Number.isInteger(v) && v > 255 ? T.hex(v) : String(v); }

const api = {FIELDS, AM_FIELDS, CTX_FIELDS, SECTIONS, OPS, rawName, defaultConfig, cloneConfig, setKey, getKey, amFrom, amWord, simulate, bytesPerDatum};
if (typeof module !== "undefined" && module.exports) module.exports = api; else root.PackerModel = api;
})(typeof window !== "undefined" ? window : globalThis);
