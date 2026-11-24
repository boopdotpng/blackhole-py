# Tensix config register fields. Per-field notes: docs/cfg.md
from enum import Enum, IntEnum
from types import SimpleNamespace
from typing import NamedTuple

class Space(Enum):
  THREAD = "ThreadConfig"
  CONFIG = "Config"
T, C = Space.THREAD, Space.CONFIG
TENSIX_CFG = 0xFFEF0000

class Field(NamedTuple):
  space: Space; word: int; shift: int; width: int; name: str
  @property
  def mask(self): return ((1 << self.width) - 1) << self.shift
  def __call__(self, value) -> "Set":
    value = int(value)
    if not 0 <= value < 1 << self.width: raise ValueError(f"{self.name}: {value} does not fit {self.width} bits")
    if self.width > 32: raise ValueError(f"{self.name} spans several words; write its parts")
    return Set(self, value)

class Set(NamedTuple):
  field: Field; value: int
  @property
  def bits(self): return self.value << self.field.shift

def words(sets) -> dict[int, int]:
  out = {}
  for s in sets: out[s.field.word] = out.get(s.field.word, 0) | s.bits
  return out

class DataFormat(IntEnum):
  FLOAT32, FLOAT16, BFP8, BFP4, TF32, FLOAT16_B, BFP8_B, BFP4_B, INT32, UINT16, LF8, BFP2 = range(12)
  INT8, BFP2_B = 14, 15

def _block(space, prefix, table, **extra):
  rows = (r.split() for r in table.replace("\n", ";").split(";") if r.strip())
  return SimpleNamespace(**{n: Field(space, int(w), int(s), int(b), f"{prefix}.{n}") for n, w, s, b in rows}, **extra)

def _arr(space, name, n, f): return tuple(Field(space, *f(i), f"{name}[{i}]") for i in range(n))

def _addr_mod(s):
  a, d = 12 + s, 28 + s
  m = _block(T, f"addr_mod[{s}]", f"""srca_incr {a} 0 6; srca_cr {a} 6 1; srca_clear {a} 7 1
    srcb_incr {a} 8 6; srcb_cr {a} 14 1; srcb_clear {a} 15 1
    dst_incr {d} 0 10; dst_cr {d} 10 1; dst_clear {d} 11 1; dst_c_to_cr {d} 12 1; fidelity_incr {d} 13 2; fidelity_clear {d} 15 1""",
    words=(a, d))
  m.incr = (m.srca_incr, m.srcb_incr, m.dst_incr, m.fidelity_incr)
  m.clear = (m.srca_clear, m.srcb_clear, m.dst_clear, m.fidelity_clear)
  m.cr = (m.srca_cr, m.srcb_cr, m.dst_cr)
  return m

def _pack_addr_mod(s):
  w = 37 + s
  return _block(T, f"pack_addr_mod[{s}]", f"""ysrc_incr {w} 0 4; ysrc_cr {w} 4 1; ysrc_clear {w} 5 1
    ydst_incr {w} 6 4; ydst_cr {w} 10 1; ydst_clear {w} 11 1
    zsrc_incr {w} 12 1; zsrc_clear {w} 13 1; zdst_incr {w} 14 1; zdst_clear {w} 15 1""")

THREAD = _block(T, "thread", """cfg_bank 0 0 1; dst_offset 1 0 12; disable_implied_srca 2 0 1
  sfpu_dst_fmt_en 4 0 1; sfpu_dst_fmt 4 1 4; srca_override_addr 5 2 1
  disable_clr_dvalid_a 7 0 1; disable_clr_dvalid_b 7 1 1; fidelity_phase 11 0 2""",
  unpack_ctx_offset=_arr(T, "thread.unpack_ctx_offset", 2, lambda i: (41, 8 * i, 4)),
  unpack_ctx_reset=_arr(T, "thread.unpack_ctx_reset", 2, lambda i: (41, 4 + 8 * i, 1)),
  unpack_ctx_inc=_arr(T, "thread.unpack_ctx_inc", 2, lambda i: (41, 5 + 8 * i, 1)),
  addr_mod=tuple(_addr_mod(s) for s in range(8)),
  pack_addr_mod=tuple(_pack_addr_mod(s) for s in range(4)))

MATH = _block(C, "math", """srca_fmt 1 17 4; srcb_fmt 1 21 4; dst_fmt 1 25 4; fp32_dst_acc 1 29 1; sfpu_fp32_acc 1 30 1
  relu_mode 2 2 2; relu_threshold 2 6 16; state_reset 4 0 1""")

UNPACK_A_CONTEXTS, UNPACK_B_CONTEXTS = 8, 2  # unpacker 1 on contexts 2..7 hangs the card

def _unpacker(i):
  sec, p, n = 64 + 48 * i, f"unpack[{i}]", UNPACK_B_CONTEXTS if i else UNPACK_A_CONTEXTS
  xy, zw, e = (56, 57, 50) if i == 0 else (58, 59, 62)
  return _block(C, p, f"""in_fmt {sec} 0 4; uncompressed {sec} 4 1; x_dim {sec} 16 16; y_dim {sec+1} 0 16; z_dim {sec+1} 16 16
    w_dim {sec+2} 0 16; out_fmt {sec+8} 0 4; lf8_e4m3 {sec+7} 22 1; transpose {sec+8} 8 1; tileize_mode {sec+8} 9 1
    tileize_row_pitch {sec+8} 16 12; override_fmt {sec+8} 14 1; force_shared_exp {sec+9} 8 1
    shared_exp {e} 0 8; add_dst_addr_cntr {e} 8 1; row_stride {xy} 16 16; face_stride {zw} 0 16
    context_count {sec+9} 9 3; context_count_en {sec+9} 12 1""",
    context_reset=THREAD.unpack_ctx_reset[i],
    disable_zero_compress=_arr(C, f"{p}.disable_zero_compress", 8, lambda c: (sec + 9, (c & 3) + (c >> 2) * 16, 1)),
    unpack_to_dst=_arr(C, f"{p}.unpack_to_dst", 8, lambda c: (sec + 9, 4 + (c & 3) + (c >> 2) * 16, 1)),
    context_in_fmt=_arr(C, f"{p}.context_in_fmt", n, lambda c: (sec + 28 + (c & 3), 16 + (c >> 2) * 8, 4)),
    context_out_fmt=_arr(C, f"{p}.context_out_fmt", n, lambda c: (sec + 28 + (c & 3), 20 + (c >> 2) * 8, 4)),
    base_addr=_arr(C, f"{p}.base_addr", n, lambda c: (sec + 12 + c, 0, 32)),
    offset_addr=_arr(C, f"{p}.offset_addr", min(n, 4), lambda c: (sec + 28 + c, 0, 16)),
    dst_addr=_arr(C, f"{p}.dst_addr", 4, lambda c: (sec + 20 + (c >> 1), (c & 1) * 16, 16)),
    tile_x_dim=_arr(C, f"{p}.tile_x_dim", 4, lambda c: (sec + 22 + (c >> 1), (c & 1) * 16, 16)))
UNPACK = (_unpacker(0), _unpacker(1))

PACK_CONTEXTS = 4

def _pack_ctx(c):
  r, w = (68, 96, 116, 144)[c], 28 + c
  return _block(C, f"pack.ctx[{c}]", f"""exp_section_size {r} 16 16; l1_dest_addr {r+1} 0 32; disable_zero_compress {r+2} 0 1
    out_fmt {r+2} 4 4; in_fmt {r+2} 8 4; l1_acc {r+3} 19 1; downsample_mask {r+3} 0 16
    pack_per_xy_plane {w} 0 8; pack_reads_per_xy_plane {w} 8 8; pack_xys_per_tile {w} 16 7; dst_target_offset {180+c} 0 12""")

PACK = _block(C, "pack", """lf8_e4m3 71 23 1; read_32b 18 0 1; y_stride 12 16 16; z_stride 13 0 16; w_stride 13 16 16
  l1_y_stride 14 16 16; l1_z_stride 15 0 16; l1_w_stride 15 16 16; edge_mode 24 16 1; row_set_select 24 17 8
  face_set_select 19 0 8; face_set_en 19 8 1""",
  ctx=tuple(_pack_ctx(c) for c in range(PACK_CONTEXTS)),
  edge_mask=_arr(C, "pack.edge_mask", 4, lambda s: (24 + s, 0, 16)),
  row_set_mapping=_arr(C, "pack.row_set_mapping", 4, lambda s: (20 + s, 0, 32)),
  face_set_mapping=_arr(C, "pack.face_set_mapping", 4, lambda s: (36 + s, 0, 32)))

GLOBAL = _block(C, "global", """icache_invalidate 185 0 5; prefetch_trisc 208 0 3; prefetch_brisc 208 3 1
  prefetch_ncrisc 208 4 1; prefetch_max_req 208 5 8; zeroacc_abs_tile_mode 220 3 1""",
  scratch=_arr(C, "global.scratch", 3, lambda i: (209 + i, 0, 32)))

MOVER = _block(C, "mover", "src_addr 88 0 32; dst_addr 89 0 32; size 90 0 30; direction 90 30 2")

ADDR_MOD, PACK_ADDR_MOD = THREAD.addr_mod, THREAD.pack_addr_mod
