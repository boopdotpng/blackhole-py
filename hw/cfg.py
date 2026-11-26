# Tensix config register fields. Per-field notes: docs/notes.toml
from enum import Enum, IntEnum
from dataclasses import dataclass
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

def _t(word: int, shift: int, width: int, name: str) -> Field: return Field(T, word, shift, width, name)
def _c(word: int, shift: int, width: int, name: str) -> Field: return Field(C, word, shift, width, name)

# ---- ThreadConfig (per TRISC, written whole-word with SETC16) ----

@dataclass(frozen=True)
class AddrMod:
  # one of 8 math RWC address-modifier slots; ThreadConfig words 12+s and 28+s
  srca_incr: Field; srca_cr: Field; srca_clear: Field
  srcb_incr: Field; srcb_cr: Field; srcb_clear: Field
  dst_incr: Field; dst_cr: Field; dst_clear: Field; dst_c_to_cr: Field
  fidelity_incr: Field; fidelity_clear: Field
  words: tuple[int, int]

  @property
  def incr(self) -> tuple[Field, ...]: return (self.srca_incr, self.srcb_incr, self.dst_incr, self.fidelity_incr)
  @property
  def clear(self) -> tuple[Field, ...]: return (self.srca_clear, self.srcb_clear, self.dst_clear, self.fidelity_clear)
  @property
  def cr(self) -> tuple[Field, ...]: return (self.srca_cr, self.srcb_cr, self.dst_cr)

  @staticmethod
  def slot(s: int) -> AddrMod:
    a, d, p = 12 + s, 28 + s, f"addr_mod[{s}]"
    return AddrMod(
      srca_incr=_t(a, 0, 6, f"{p}.srca_incr"), srca_cr=_t(a, 6, 1, f"{p}.srca_cr"), srca_clear=_t(a, 7, 1, f"{p}.srca_clear"),
      srcb_incr=_t(a, 8, 6, f"{p}.srcb_incr"), srcb_cr=_t(a, 14, 1, f"{p}.srcb_cr"), srcb_clear=_t(a, 15, 1, f"{p}.srcb_clear"),
      dst_incr=_t(d, 0, 10, f"{p}.dst_incr"), dst_cr=_t(d, 10, 1, f"{p}.dst_cr"), dst_clear=_t(d, 11, 1, f"{p}.dst_clear"),
      dst_c_to_cr=_t(d, 12, 1, f"{p}.dst_c_to_cr"),
      fidelity_incr=_t(d, 13, 2, f"{p}.fidelity_incr"), fidelity_clear=_t(d, 15, 1, f"{p}.fidelity_clear"),
      words=(a, d),
    )

@dataclass(frozen=True)
class PackAddrMod:
  # one of 4 packer ADC address-modifier slots; ThreadConfig word 37+s
  ysrc_incr: Field; ysrc_cr: Field; ysrc_clear: Field
  ydst_incr: Field; ydst_cr: Field; ydst_clear: Field
  zsrc_incr: Field; zsrc_clear: Field
  zdst_incr: Field; zdst_clear: Field

  @staticmethod
  def slot(s: int) -> PackAddrMod:
    w, p = 37 + s, f"pack_addr_mod[{s}]"
    return PackAddrMod(
      ysrc_incr=_t(w, 0, 4, f"{p}.ysrc_incr"), ysrc_cr=_t(w, 4, 1, f"{p}.ysrc_cr"), ysrc_clear=_t(w, 5, 1, f"{p}.ysrc_clear"),
      ydst_incr=_t(w, 6, 4, f"{p}.ydst_incr"), ydst_cr=_t(w, 10, 1, f"{p}.ydst_cr"), ydst_clear=_t(w, 11, 1, f"{p}.ydst_clear"),
      zsrc_incr=_t(w, 12, 1, f"{p}.zsrc_incr"), zsrc_clear=_t(w, 13, 1, f"{p}.zsrc_clear"),
      zdst_incr=_t(w, 14, 1, f"{p}.zdst_incr"), zdst_clear=_t(w, 15, 1, f"{p}.zdst_clear"),
    )

@dataclass(frozen=True)
class ThreadCfg:
  cfg_bank: Field
  dst_offset: Field
  disable_implied_srca: Field
  sfpu_dst_fmt_en: Field
  sfpu_dst_fmt: Field
  srca_override_addr: Field
  disable_clr_dvalid_a: Field
  disable_clr_dvalid_b: Field
  fidelity_phase: Field
  unpack_ctx_offset: tuple[Field, Field]  # per unpacker
  unpack_ctx_reset: tuple[Field, Field]
  unpack_ctx_inc: tuple[Field, Field]
  addr_mod: tuple[AddrMod, ...]
  pack_addr_mod: tuple[PackAddrMod, ...]

THREAD = ThreadCfg(
  cfg_bank=_t(0, 0, 1, "thread.cfg_bank"),
  dst_offset=_t(1, 0, 12, "thread.dst_offset"),
  disable_implied_srca=_t(2, 0, 1, "thread.disable_implied_srca"),
  sfpu_dst_fmt_en=_t(4, 0, 1, "thread.sfpu_dst_fmt_en"),
  sfpu_dst_fmt=_t(4, 1, 4, "thread.sfpu_dst_fmt"),
  srca_override_addr=_t(5, 2, 1, "thread.srca_override_addr"),
  disable_clr_dvalid_a=_t(7, 0, 1, "thread.disable_clr_dvalid_a"),
  disable_clr_dvalid_b=_t(7, 1, 1, "thread.disable_clr_dvalid_b"),
  fidelity_phase=_t(11, 0, 2, "thread.fidelity_phase"),
  unpack_ctx_offset=tuple(_t(41, 8 * i, 4, f"thread.unpack_ctx_offset[{i}]") for i in range(2)),
  unpack_ctx_reset=tuple(_t(41, 4 + 8 * i, 1, f"thread.unpack_ctx_reset[{i}]") for i in range(2)),
  unpack_ctx_inc=tuple(_t(41, 5 + 8 * i, 1, f"thread.unpack_ctx_inc[{i}]") for i in range(2)),
  addr_mod=tuple(AddrMod.slot(s) for s in range(8)),
  pack_addr_mod=tuple(PackAddrMod.slot(s) for s in range(4)),
)
ADDR_MOD, PACK_ADDR_MOD = THREAD.addr_mod, THREAD.pack_addr_mod

# ---- Config (shared; RMWCIB, WRCFG, or MMIO at TENSIX_CFG) ----

@dataclass(frozen=True)
class MathCfg:
  srca_fmt: Field
  srcb_fmt: Field
  dst_fmt: Field
  fp32_dst_acc: Field
  sfpu_fp32_acc: Field
  relu_mode: Field
  relu_threshold: Field
  state_reset: Field

MATH = MathCfg(
  srca_fmt=_c(1, 17, 4, "math.srca_fmt"),
  srcb_fmt=_c(1, 21, 4, "math.srcb_fmt"),
  dst_fmt=_c(1, 25, 4, "math.dst_fmt"),
  fp32_dst_acc=_c(1, 29, 1, "math.fp32_dst_acc"),
  sfpu_fp32_acc=_c(1, 30, 1, "math.sfpu_fp32_acc"),
  relu_mode=_c(2, 2, 2, "math.relu_mode"),
  relu_threshold=_c(2, 6, 16, "math.relu_threshold"),
  state_reset=_c(4, 0, 1, "math.state_reset"),
)

UNPACK_A_CONTEXTS, UNPACK_B_CONTEXTS = 8, 2  # unpacker 1 on contexts 2..7 hangs the card

@dataclass(frozen=True)
class UnpackerCfg:
  in_fmt: Field
  uncompressed: Field
  x_dim: Field
  y_dim: Field
  z_dim: Field
  w_dim: Field
  out_fmt: Field
  lf8_e4m3: Field
  transpose: Field
  tileize_mode: Field
  tileize_row_pitch: Field
  override_fmt: Field
  force_shared_exp: Field
  shared_exp: Field
  add_dst_addr_cntr: Field
  row_stride: Field
  face_stride: Field
  context_count: Field
  context_count_en: Field
  context_reset: Field                   # ThreadConfig, aliases THREAD.unpack_ctx_reset[i]
  disable_zero_compress: tuple[Field, ...]  # per context
  unpack_to_dst: tuple[Field, ...]
  context_in_fmt: tuple[Field, ...]
  context_out_fmt: tuple[Field, ...]
  base_addr: tuple[Field, ...]
  offset_addr: tuple[Field, ...]
  dst_addr: tuple[Field, ...]
  tile_x_dim: tuple[Field, ...]

  @staticmethod
  def unit(i: int) -> UnpackerCfg:
    sec, p, n = 64 + 48 * i, f"unpack[{i}]", UNPACK_B_CONTEXTS if i else UNPACK_A_CONTEXTS
    xy, zw, e = (56, 57, 50) if i == 0 else (58, 59, 62)
    return UnpackerCfg(
      in_fmt=_c(sec, 0, 4, f"{p}.in_fmt"),
      uncompressed=_c(sec, 4, 1, f"{p}.uncompressed"),
      x_dim=_c(sec, 16, 16, f"{p}.x_dim"),
      y_dim=_c(sec + 1, 0, 16, f"{p}.y_dim"),
      z_dim=_c(sec + 1, 16, 16, f"{p}.z_dim"),
      w_dim=_c(sec + 2, 0, 16, f"{p}.w_dim"),
      out_fmt=_c(sec + 8, 0, 4, f"{p}.out_fmt"),
      lf8_e4m3=_c(sec + 7, 22, 1, f"{p}.lf8_e4m3"),
      transpose=_c(sec + 8, 8, 1, f"{p}.transpose"),
      tileize_mode=_c(sec + 8, 9, 1, f"{p}.tileize_mode"),
      tileize_row_pitch=_c(sec + 8, 16, 12, f"{p}.tileize_row_pitch"),
      override_fmt=_c(sec + 8, 14, 1, f"{p}.override_fmt"),
      force_shared_exp=_c(sec + 9, 8, 1, f"{p}.force_shared_exp"),
      shared_exp=_c(e, 0, 8, f"{p}.shared_exp"),
      add_dst_addr_cntr=_c(e, 8, 1, f"{p}.add_dst_addr_cntr"),
      row_stride=_c(xy, 16, 16, f"{p}.row_stride"),
      face_stride=_c(zw, 0, 16, f"{p}.face_stride"),
      context_count=_c(sec + 9, 9, 3, f"{p}.context_count"),
      context_count_en=_c(sec + 9, 12, 1, f"{p}.context_count_en"),
      context_reset=THREAD.unpack_ctx_reset[i],
      disable_zero_compress=tuple(_c(sec + 9, (c & 3) + (c >> 2) * 16, 1, f"{p}.disable_zero_compress[{c}]") for c in range(8)),
      unpack_to_dst=tuple(_c(sec + 9, 4 + (c & 3) + (c >> 2) * 16, 1, f"{p}.unpack_to_dst[{c}]") for c in range(8)),
      context_in_fmt=tuple(_c(sec + 28 + (c & 3), 16 + (c >> 2) * 8, 4, f"{p}.context_in_fmt[{c}]") for c in range(n)),
      context_out_fmt=tuple(_c(sec + 28 + (c & 3), 20 + (c >> 2) * 8, 4, f"{p}.context_out_fmt[{c}]") for c in range(n)),
      base_addr=tuple(_c(sec + 12 + c, 0, 32, f"{p}.base_addr[{c}]") for c in range(n)),
      offset_addr=tuple(_c(sec + 28 + c, 0, 16, f"{p}.offset_addr[{c}]") for c in range(min(n, 4))),
      dst_addr=tuple(_c(sec + 20 + (c >> 1), (c & 1) * 16, 16, f"{p}.dst_addr[{c}]") for c in range(4)),
      tile_x_dim=tuple(_c(sec + 22 + (c >> 1), (c & 1) * 16, 16, f"{p}.tile_x_dim[{c}]") for c in range(4)),
    )

UNPACK = (UnpackerCfg.unit(0), UnpackerCfg.unit(1))

PACK_CONTEXTS = 4

@dataclass(frozen=True)
class PackContext:
  exp_section_size: Field
  l1_dest_addr: Field
  disable_zero_compress: Field
  out_fmt: Field
  in_fmt: Field
  l1_acc: Field
  downsample_mask: Field
  pack_per_xy_plane: Field
  pack_reads_per_xy_plane: Field
  pack_xys_per_tile: Field
  dst_target_offset: Field

  @staticmethod
  def unit(c: int) -> PackContext:
    r, w, p = (68, 96, 116, 144)[c], 28 + c, f"pack.ctx[{c}]"
    return PackContext(
      exp_section_size=_c(r, 16, 16, f"{p}.exp_section_size"),
      l1_dest_addr=_c(r + 1, 0, 32, f"{p}.l1_dest_addr"),
      disable_zero_compress=_c(r + 2, 0, 1, f"{p}.disable_zero_compress"),
      out_fmt=_c(r + 2, 4, 4, f"{p}.out_fmt"),
      in_fmt=_c(r + 2, 8, 4, f"{p}.in_fmt"),
      l1_acc=_c(r + 3, 19, 1, f"{p}.l1_acc"),
      downsample_mask=_c(r + 3, 0, 16, f"{p}.downsample_mask"),
      pack_per_xy_plane=_c(w, 0, 8, f"{p}.pack_per_xy_plane"),
      pack_reads_per_xy_plane=_c(w, 8, 8, f"{p}.pack_reads_per_xy_plane"),
      pack_xys_per_tile=_c(w, 16, 7, f"{p}.pack_xys_per_tile"),
      dst_target_offset=_c(180 + c, 0, 12, f"{p}.dst_target_offset"),
    )

@dataclass(frozen=True)
class PackerCfg:
  lf8_e4m3: Field
  read_32b: Field
  y_stride: Field
  z_stride: Field
  w_stride: Field
  l1_y_stride: Field
  l1_z_stride: Field
  l1_w_stride: Field
  edge_mode: Field
  row_set_select: Field
  face_set_select: Field
  face_set_en: Field
  ctx: tuple[PackContext, ...]
  edge_mask: tuple[Field, ...]
  row_set_mapping: tuple[Field, ...]
  face_set_mapping: tuple[Field, ...]

PACK = PackerCfg(
  lf8_e4m3=_c(71, 23, 1, "pack.lf8_e4m3"),
  read_32b=_c(18, 0, 1, "pack.read_32b"),
  y_stride=_c(12, 16, 16, "pack.y_stride"),
  z_stride=_c(13, 0, 16, "pack.z_stride"),
  w_stride=_c(13, 16, 16, "pack.w_stride"),
  l1_y_stride=_c(14, 16, 16, "pack.l1_y_stride"),
  l1_z_stride=_c(15, 0, 16, "pack.l1_z_stride"),
  l1_w_stride=_c(15, 16, 16, "pack.l1_w_stride"),
  edge_mode=_c(24, 16, 1, "pack.edge_mode"),
  row_set_select=_c(24, 17, 8, "pack.row_set_select"),
  face_set_select=_c(19, 0, 8, "pack.face_set_select"),
  face_set_en=_c(19, 8, 1, "pack.face_set_en"),
  ctx=tuple(PackContext.unit(c) for c in range(PACK_CONTEXTS)),
  edge_mask=tuple(_c(24 + s, 0, 16, f"pack.edge_mask[{s}]") for s in range(4)),
  row_set_mapping=tuple(_c(20 + s, 0, 32, f"pack.row_set_mapping[{s}]") for s in range(4)),
  face_set_mapping=tuple(_c(36 + s, 0, 32, f"pack.face_set_mapping[{s}]") for s in range(4)),
)

@dataclass(frozen=True)
class GlobalCfg:
  icache_invalidate: Field
  prefetch_trisc: Field
  prefetch_brisc: Field
  prefetch_ncrisc: Field
  prefetch_max_req: Field
  zeroacc_abs_tile_mode: Field
  scratch: tuple[Field, ...]

GLOBAL = GlobalCfg(
  icache_invalidate=_c(185, 0, 5, "global.icache_invalidate"),
  prefetch_trisc=_c(208, 0, 3, "global.prefetch_trisc"),
  prefetch_brisc=_c(208, 3, 1, "global.prefetch_brisc"),
  prefetch_ncrisc=_c(208, 4, 1, "global.prefetch_ncrisc"),
  prefetch_max_req=_c(208, 5, 8, "global.prefetch_max_req"),
  zeroacc_abs_tile_mode=_c(220, 3, 1, "global.zeroacc_abs_tile_mode"),
  scratch=tuple(_c(209 + i, 0, 32, f"global.scratch[{i}]") for i in range(3)),
)

@dataclass(frozen=True)
class MoverCfg:
  src_addr: Field
  dst_addr: Field
  size: Field
  direction: Field

MOVER = MoverCfg(
  src_addr=_c(88, 0, 32, "mover.src_addr"),
  dst_addr=_c(89, 0, 32, "mover.dst_addr"),
  size=_c(90, 0, 30, "mover.size"),
  direction=_c(90, 30, 2, "mover.direction"),
)
