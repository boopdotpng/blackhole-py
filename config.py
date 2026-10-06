# Hardware configuration state, one frozen dataclass per config space.
#
# A config object says what state a later instruction *requires*, not how to write it:
#   UnpackerCfg(unpacker=0, src_format=DataFormat.FLOAT16_B, tilize=True)
# Fields left as None are "don't care". writes() turns an object into {(space, scope, addr): (value, mask)}, so a
# later pass can track what each register already holds, drop writes that change nothing, and merge partial
# requirements on the same word. Lowering picks the instruction: SETC16 for THREAD, RMWCIB/WRCFG/sw for SHARED,
# sw for MMIO, SFPCONFIG for SFPU, REPLAY load for REPLAY, SEMINIT for SEM.
#
# Every readable field lists the raw register field(s) it lands in. Raw names are the cfg_defines.h names (grep
# them in tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h); REGS at the bottom is generated from
# that header and pins each one to (space, addr32, shift, width). Names that cfg_defines.h does not split into
# fields (tile descriptor, MOP, NoC, ...) are added by hand in MANUAL_REGS.
#
# Per-index fields: F(name_for_index0, name_for_index1, ...) picks by the class's INDEX key field (unpacker 0/1,
# packer 0..3, addr-mod slot 0..7). A tuple of names writes the same value to each (blackhole-py always mirrors
# config contexts 0 and 1, so the cntx0/cntx1 pairs are one field).
from __future__ import annotations
from dataclasses import dataclass, field, fields
from enum import Enum, IntEnum, auto

class Space(Enum):
  THREAD = auto()   # per-thread config registers, 16-bit, write-only, set by SETC16. Unset fields in a written register are 0.
  SHARED = auto()   # shared config registers at 0xFFEF0000 + 4*addr32, two state banks selected by THREAD CFG_STATE_ID
  MMIO = auto()     # memory-mapped registers / L1 seen by one RISC (MOP_CFG, NoC command buffers, mailboxes)
  GPR = auto()      # Tensix thread GPRs (regfile at 0xFFE00000), sources for WRCFG
  SFPU = auto()     # SFPU config slots written by SFPCONFIG: 0-3 macro instructions, 4-7 macro sequences, 8 misc, 12-14 constants, 15 lane config
  REPLAY = auto()   # replay buffer, addr = slot 0..31, value = Tensix instruction word
  SEM = auto()      # Tensix semaphore init/max. Invalidated by every SEMPOST/SEMGET.

class Thread(IntEnum): UNPACK = 0; MATH = 1; PACK = 2; READ = 3; WRITE = 4  # READ = BRISC, WRITE = NCRISC

PER_THREAD = {Space.THREAD, Space.MMIO, Space.GPR, Space.SFPU, Space.REPLAY}

class DataFormat(IntEnum):  # tensix_types.h DataFormat. Registers hold the low 4 bits.
  FLOAT32 = 0; FLOAT16 = 1; BFP8 = 2; BFP4 = 3; TF32 = 4; FLOAT16_B = 5; BFP8_B = 6; BFP4_B = 7
  INT32 = 8; UINT16 = 9; LF8 = 10; BFP2 = 11; INT8 = 14; BFP2_B = 15; UINT32 = 24; FP8_E4M3 = 26; UINT8 = 30

@dataclass(frozen=True)
class Loc:
  space: Space
  addr: int
  shift: int
  width: int

def F(*per_index, default=None):
  """A config field. per_index: one raw name (or tuple of mirrored names, or None = absent) per INDEX value."""
  return field(default=default, metadata={"locs": per_index})

def K():
  """A key field: identifies which instance of the space this is, never written."""
  return field(metadata={"key": True})

def per(fmt, n): return tuple(fmt.format(i=i) for i in range(n))

def l1_addr(byte_addr: int) -> int: return (byte_addr >> 4) - 1  # unpacker/packer L1 address fields: 16B units, minus one

class Config:
  INDEX: str | None = None  # the key field that selects among per-index raw names
  SCOPE: Thread | None = None  # fixed owning thread for per-thread spaces, else the `thread` key field

  def base(self) -> int: return 0  # added to MMIO addresses (NoC buffer, CB slot)
  def scope(self): return getattr(self, "thread", self.SCOPE)
  def key(self): return (type(self),) + tuple(getattr(self, f.name) for f in fields(self) if f.metadata.get("key"))

  def index(self) -> int: return getattr(self, self.INDEX) if self.INDEX else 0

  def locs(self, f) -> tuple[Loc, ...]: return self._resolve(f.name, f.metadata["locs"])
  def _resolve(self, name, per_index) -> tuple[Loc, ...]:
    names = per_index[self.index()] if len(per_index) > 1 else per_index[0]
    if names is None: raise ValueError(f"{type(self).__name__}.{name} does not exist for {self.key()[1:]}")
    return tuple(REGS[n] for n in ((names,) if isinstance(names, str) else names))

  # FIXED = {name: (raw name, value or fn(self) -> value)}: fields that exist in hardware but are pinned to the value
  # blackhole-py uses. They are not constructor args; they are written whenever another field of the same register is.
  FIXED: dict = {}

  def _user_values(self):
    for f in fields(self):
      if "locs" in f.metadata and (v := getattr(self, f.name)) is not None: yield f.name, self.locs(f), v

  def values(self):
    user = list(self._user_values())
    yield from user
    touched = {(l.space, l.addr) for _, locs, _ in user for l in locs}
    for name, (raw, v) in self.FIXED.items():
      locs = self._resolve(name, (raw,))
      if any((l.space, l.addr) in touched for l in locs): yield name, locs, v(self) if callable(v) else v

  def writes(self) -> dict[tuple[Space, Thread | None, int], tuple[int, int]]:
    out: dict = {}
    for name, locs, v in self.values():
      v = int(v) & 0xF if isinstance(v, DataFormat) else int(v.value if isinstance(v, Enum) and not isinstance(v, int) else v)
      for loc in locs:
        if not 0 <= v < 1 << loc.width: raise ValueError(f"{type(self).__name__}.{name}={v} does not fit in {loc.width} bits")
        k = (loc.space, self.scope() if loc.space in PER_THREAD else None, loc.addr + (self.base() if loc.space is Space.MMIO else 0))
        value, mask = out.get(k, (0, 0))
        out[k] = (value | v << loc.shift, mask | ((1 << loc.width) - 1) << loc.shift)
    for k in out:  # SETC16 writes the whole 16-bit register
      if k[0] is Space.THREAD: out[k] = (out[k][0], 0xFFFF)
    return out

  def merge(self, other: Config) -> Config:
    """Combine two requirements on the same instance; conflicting fields raise."""
    assert self.key() == other.key(), f"{self.key()} vs {other.key()}"
    new = {}
    for f in fields(self):
      a, b = getattr(self, f.name), getattr(other, f.name)
      if a is not None and b is not None and a != b and "locs" in f.metadata: raise ValueError(f"{type(self).__name__}.{f.name}: {a} vs {b}")
      new[f.name] = a if a is not None else b
    return type(self)(**new)

# ***** unpacker (one per source: 0 = SrcA or Dest, 1 = SrcB) *****
#
# Shared config has two banks (Config[0], Config[1]); each Tensix thread reads the bank named by its ThreadCfg.state_id.
# Registers at addr32 >= GLOBAL_CFG_BASE have one copy. On top of that the unpacker has config *contexts*: an UNPACR
# picks one (its cfg_ctx operand + ThreadCfg.unpack{n}_context, or the auto-incrementing context counter), so a kernel
# can rewrite context k+1 while the unpacker is still running on context k and then switch with no stall.
# Unpacker 0 has 8 contexts, unpacker 1 has 2. Some per-context registers only have 4 copies: contexts 4-7 share them
# with contexts 0-3 (noted per field).

GLOBAL_CFG_BASE = 180  # cfg_defines GLOBAL_CFGREG_BASE_ADDR32
def banked(addr32: int) -> bool: return addr32 < GLOBAL_CFG_BASE

@dataclass(frozen=True)
class UnpackerCfg(Config):
  """State of one unpacker that every context shares."""
  INDEX, SCOPE = "unpacker", Thread.UNPACK
  unpacker: int = K()
  # tile descriptor: what is in L1
  src_format: DataFormat | None = F("TILE_DESC0_in_data_format", "TILE_DESC1_in_data_format")
  uncompressed: bool | None = F("TILE_DESC0_uncompressed", "TILE_DESC1_uncompressed")  # 1 = no zero-compression row pointers in L1
  blobs_per_xy_plane: int | None = F("TILE_DESC0_blobs_per_xy_plane", "TILE_DESC1_blobs_per_xy_plane")
  in_x_dim: int | None = F("TILE_DESC0_x_dim", "TILE_DESC1_x_dim")  # datums per row in L1 (1024 tilize, 256 one face, ...)
  in_y_dim: int | None = F("TILE_DESC0_y_dim", "TILE_DESC1_y_dim")
  in_z_dim: int | None = F("TILE_DESC0_z_dim", "TILE_DESC1_z_dim")  # faces
  in_w_dim: int | None = F("TILE_DESC0_w_dim", "TILE_DESC1_w_dim")
  # unpack config: what lands in the register file
  dst_format: DataFormat | None = F("THCON_SEC0_REG2_Out_data_format", "THCON_SEC1_REG2_Out_data_format")
  throttle_mode: int | None = F("THCON_SEC0_REG2_Throttle_mode", "THCON_SEC1_REG2_Throttle_mode")  # blackhole-py uses 2
  context_count: int | None = F("THCON_SEC0_REG2_Context_count", "THCON_SEC1_REG2_Context_count")  # log2 of contexts the counter cycles
  transpose_xy: bool | None = F("THCON_SEC0_REG2_Haloize_mode", "THCON_SEC1_REG2_Haloize_mode")  # "haloize": transpose each face
  tilize: bool | None = F("THCON_SEC0_REG2_Tileize_mode", "THCON_SEC1_REG2_Tileize_mode")  # row-major L1 -> tiled register file
  src_reg_set_update: bool | None = F("THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd", "THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd")
  upsample_rate: int | None = F("THCON_SEC0_REG2_Upsample_rate", "THCON_SEC1_REG2_Upsample_rate")
  upsample_interleave: bool | None = F("THCON_SEC0_REG2_Upsample_and_interleave", "THCON_SEC1_REG2_Upsample_and_interleave")
  per_context_formats: bool | None = F("THCON_SEC0_REG2_Ovrd_data_format", "THCON_SEC1_REG2_Ovrd_data_format")  # use UnpackerContext formats
  force_shared_exp: bool | None = F("THCON_SEC0_REG2_Force_shared_exp", "THCON_SEC1_REG2_Force_shared_exp")
  limit_address: int | None = F("THCON_SEC0_REG2_Unpack_limit_address", "THCON_SEC1_REG2_Unpack_limit_address")  # L1 ring end, 16B units
  fifo_size: int | None = F("THCON_SEC0_REG2_Unpack_fifo_size", "THCON_SEC1_REG2_Unpack_fifo_size")  # L1 ring size, 16B units
  fp8_e4m3: bool | None = F("THCON_SEC0_REG1_Unp_LF8_4b_exp", "THCON_SEC1_REG1_Unp_LF8_4b_exp")  # LF8 with 4-bit exponent
  # address-counter strides. channel 0 walks L1 (in), channel 1 walks the register file (out). bytes
  in_x_stride: int | None = F("UNP0_ADDR_CTRL_XY_REG_0_Xstride", "UNP1_ADDR_CTRL_XY_REG_0_Xstride")
  in_y_stride: int | None = F("UNP0_ADDR_CTRL_XY_REG_0_Ystride", "UNP1_ADDR_CTRL_XY_REG_0_Ystride")
  in_z_stride: int | None = F("UNP0_ADDR_CTRL_ZW_REG_0_Zstride", "UNP1_ADDR_CTRL_ZW_REG_0_Zstride")
  in_w_stride: int | None = F("UNP0_ADDR_CTRL_ZW_REG_0_Wstride", "UNP1_ADDR_CTRL_ZW_REG_0_Wstride")
  out_x_stride: int | None = F("UNP0_ADDR_CTRL_XY_REG_1_Xstride", "UNP1_ADDR_CTRL_XY_REG_1_Xstride")
  out_y_stride: int | None = F("UNP0_ADDR_CTRL_XY_REG_1_Ystride", "UNP1_ADDR_CTRL_XY_REG_1_Ystride")
  out_z_stride: int | None = F("UNP0_ADDR_CTRL_ZW_REG_1_Zstride", "UNP1_ADDR_CTRL_ZW_REG_1_Zstride")
  out_w_stride: int | None = F("UNP0_ADDR_CTRL_ZW_REG_1_Wstride", "UNP1_ADDR_CTRL_ZW_REG_1_Wstride")
  in_counter_base: int | None = F("UNP0_ADDR_BASE_REG_0_Base", "UNP1_ADDR_BASE_REG_0_Base")
  out_counter_base: int | None = F("UNP0_ADDR_BASE_REG_1_Base", "UNP1_ADDR_BASE_REG_1_Base")
  add_dest_addr_counter: bool | None = F("UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr", "UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr")
  forced_shared_exp: int | None = F("UNP0_FORCED_SHARED_EXP_shared_exp", "UNP1_FORCED_SHARED_EXP_shared_exp")
  nop_clear_value: int | None = F("UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val", "UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val")  # UNPACR_NOP clear value

def _uctx(fmt, *, four=False):
  """Raw names per (unpacker, context), index = unpacker * 8 + context. four: only contexts 0-3 exist, 4-7 alias them."""
  out = []
  for u in (0, 1):
    for c in range(8):
      out.append(None if u == 1 and c >= 2 else fmt(f"THCON_SEC{u}", c & 3 if four else c))
  return F(*out)

def _base(sec, c): return f"{sec}_REG3_Base_address" if c == 0 else f"{sec}_REG3_Base_cntx{c}_address" if c < 4 else f"{sec}_REG4_Base_cntx{c}_address"
def _offset(sec, c): return f"{sec}_REG7_Offset_address" if c == 0 else f"{sec}_REG7_Offset_cntx{c}_address"

@dataclass(frozen=True)
class UnpackerContext(Config):
  """One unpacker config context: the per-move state an UNPACR selects with its cfg_ctx operand."""
  SCOPE = Thread.UNPACK
  unpacker: int = K()
  context: int = K()   # 0..7 for unpacker 0, 0..1 for unpacker 1
  def index(self): return self.unpacker * 8 + self.context
  l1_base: int | None = _uctx(_base)  # l1_addr(byte address) of the tile
  offset_address: int | None = _uctx(_offset, four=True)  # added to l1_base, 16B units
  dest_address: int | None = _uctx(lambda s, c: f"{s}_REG5_Dest_cntx{c}_address", four=True)  # register-file row (unpacker 0)
  tile_x_dim: int | None = _uctx(lambda s, c: f"{s}_REG5_Tile_x_dim_cntx{c}", four=True)  # datums per unpack row burst
  shift_amount: int | None = _uctx(lambda s, c: f"{s}_REG2_Shift_amount_cntx{c}", four=True)
  disable_zero_compress: bool | None = _uctx(lambda s, c: f"{s}_REG2_Disable_zero_compress_cntx{c}")
  to_dest: bool | None = _uctx(lambda s, c: f"{s}_REG2_Unpack_if_sel_cntx{c}")  # unpack straight into Dest
  src_format: DataFormat | None = _uctx(lambda s, c: f"{s}_REG7_Unpack_data_format_cntx{c}")  # only with UnpackerCfg.per_context_formats
  dst_format: DataFormat | None = _uctx(lambda s, c: f"{s}_REG7_Unpack_out_data_format_cntx{c}")

# ***** packer *****
#
# Blackhole has one packer (tt-llk NUM_PACKERS = 1) and four config sections. PACR's cfg_ctx operand picks the
# section, and PACR ctx_ctrl=1 cycles through all four automatically, so they act as packer config contexts the same
# way unpacker contexts do. Confirmed on hardware by tests/hw/test_contexts.py.

_PACK_SEC = ("THCON_SEC0_REG1", "THCON_SEC0_REG8", "THCON_SEC1_REG1", "THCON_SEC1_REG8")
def _pk(field_name, *, only=None):
  return F(*(f"{sec}_{field_name}" if only is None or i in only else None for i, sec in enumerate(_PACK_SEC)))

@dataclass(frozen=True)
class PackerContext(Config):
  INDEX, SCOPE = "context", Thread.PACK
  context: int = K()  # 0..3
  src_format: DataFormat | None = _pk("In_data_format")   # format the packer converts from (BF16 even for fp32 Dest;
                                                         # the read width is PackCommonCfg.read_32b_dest, strides must match)
  dst_format: DataFormat | None = _pk("Out_data_format")  # L1 format it writes
  fp8_e4m3: bool | None = _pk("Pac_LF8_4b_exp", only=(0, 2))
  l1_dest: int | None = _pk("L1_Dest_addr")  # l1_addr(byte address); set per tile
  row_start_section_size: int | None = _pk("Row_start_section_size")
  exp_section_size: int | None = _pk("Exp_section_size")  # BFP exponent section; 4 for non-BFP output in blackhole-py
  disable_zero_compress: bool | None = _pk("Disable_zero_compress")
  disable_zero_flags: bool | None = _pk("Disable_pack_zero_flags")
  add_l1_dest_offset: bool | None = _pk("Add_l1_dest_addr_offset")
  disable_shared_exp_assembler: bool | None = _pk("Dis_shared_exp_assembler")
  enable_out_fifo: bool | None = _pk("Enable_out_fifo")
  sub_tile_header_size: bool | None = _pk("Sub_l1_tile_header_size")
  add_tile_header_size: bool | None = _pk("Add_tile_header_size")
  source_interface: int | None = _pk("Source_interface_selection")
  l1_source_addr: int | None = _pk("L1_source_addr")
  downsample_mask: int | None = _pk("Downsample_mask")
  downsample_rate: int | None = _pk("Downsample_rate")
  l1_accumulate: bool | None = _pk("Pack_L1_Acc")  # add into L1 instead of overwrite
  exp_threshold_enable: bool | None = _pk("Exp_threshold_en")
  exp_threshold: int | None = _pk("Exp_threshold")
  # per-packer counters / edge / Dest offset
  edge_mask: int | None = F(*per("PCK_EDGE_OFFSET_SEC{i}_mask", 4))  # 16-bit per-datum row mask; 0xFFFF = whole row
  packs_per_xy_plane: int | None = F(*per("PACK_COUNTERS_SEC{i}_pack_per_xy_plane", 4))
  reads_per_xy_plane: int | None = F(*per("PACK_COUNTERS_SEC{i}_pack_reads_per_xy_plane", 4))  # 16 tile pack, 1 row pack
  xys_per_tile: int | None = F(*per("PACK_COUNTERS_SEC{i}_pack_xys_per_tile", 4))
  yz_transposed: bool | None = F(*per("PACK_COUNTERS_SEC{i}_pack_yz_transposed", 4))
  auto_context_inc_xys: int | None = F(*per("PACK_COUNTERS_SEC{i}_auto_ctxt_inc_xys_cnt", 4))
  dest_row_offset: int | None = F(*per("DEST_TARGET_REG_CFG_PACK_SEC{i}_Offset", 4))  # first Dest row this context reads
  dest_z_offset: int | None = F(*per("DEST_TARGET_REG_CFG_PACK_SEC{i}_ZOffset", 4))

@dataclass(frozen=True)
class PackCommonCfg(Config):  # shared by all packers
  SCOPE = Thread.PACK
  read_32b_dest: bool | None = F("PCK_DEST_RD_CTRL_Read_32b_data")  # Dest holds fp32 / int32
  read_unsigned: bool | None = F("PCK_DEST_RD_CTRL_Read_unsigned")
  read_int8: bool | None = F("PCK_DEST_RD_CTRL_Read_int8")
  round_10b_mantissa: bool | None = F("PCK_DEST_RD_CTRL_Round_10b_mant")  # needed for FP8 E4M3 output
  # channel 0 walks Dest (in), channel 1 walks L1 (out)
  in_x_stride: int | None = F("PCK0_ADDR_CTRL_XY_REG_0_Xstride")
  in_y_stride: int | None = F("PCK0_ADDR_CTRL_XY_REG_0_Ystride")
  in_z_stride: int | None = F("PCK0_ADDR_CTRL_ZW_REG_0_Zstride")
  in_w_stride: int | None = F("PCK0_ADDR_CTRL_ZW_REG_0_Wstride")
  out_x_stride: int | None = F("PCK0_ADDR_CTRL_XY_REG_1_Xstride")
  out_y_stride: int | None = F("PCK0_ADDR_CTRL_XY_REG_1_Ystride")
  out_z_stride: int | None = F("PCK0_ADDR_CTRL_ZW_REG_1_Zstride")
  out_w_stride: int | None = F("PCK0_ADDR_CTRL_ZW_REG_1_Wstride")
  in_counter_base: int | None = F("PCK0_ADDR_BASE_REG_0_Base")
  out_counter_base: int | None = F("PCK0_ADDR_BASE_REG_1_Base")
  row_set_mapping_0: int | None = F("TILE_ROW_SET_MAPPING_0")  # 16 x 2-bit: which row set each Dest row group uses
  row_set_mapping_1: int | None = F("TILE_ROW_SET_MAPPING_1")
  face_set_select: int | None = F("PCK_EDGE_TILE_FACE_SET_SELECT_select")
  face_set_select_enable: bool | None = F("PCK_EDGE_TILE_FACE_SET_SELECT_enable")

# ***** math: ALU formats, accumulation, ReLU, Dest access *****

@dataclass(frozen=True)
class AluCfg(Config):
  SCOPE = Thread.MATH
  srca_format: DataFormat | None = F("ALU_FORMAT_SPEC_REG0_SrcA")
  srcb_format: DataFormat | None = F("ALU_FORMAT_SPEC_REG1_SrcB")
  dest_format: DataFormat | None = F("ALU_FORMAT_SPEC_REG2_Dstacc")
  srca_unsigned: bool | None = F("ALU_FORMAT_SPEC_REG0_SrcAUnsigned")
  srcb_unsigned: bool | None = F("ALU_FORMAT_SPEC_REG0_SrcBUnsigned")
  srca_format_override: DataFormat | None = F("ALU_FORMAT_SPEC_REG_SrcA_val")  # used only when srca_override
  srca_override: bool | None = F("ALU_FORMAT_SPEC_REG_SrcA_override")
  srcb_format_override: DataFormat | None = F("ALU_FORMAT_SPEC_REG_SrcB_val")
  srcb_override: bool | None = F("ALU_FORMAT_SPEC_REG_SrcB_override")
  dest_format_override: DataFormat | None = F("ALU_FORMAT_SPEC_REG_Dstacc_val")
  dest_override: bool | None = F("ALU_FORMAT_SPEC_REG_Dstacc_override")
  fp32_dest: bool | None = F("ALU_ACC_CTRL_Fp32_enabled")  # Dest accumulates in fp32 (half the rows)
  sfpu_fp32: bool | None = F("ALU_ACC_CTRL_SFPU_Fp32_enabled")  # SFPU loads/stores Dest as fp32
  int8_math: bool | None = F("ALU_ACC_CTRL_INT8_math_enabled")
  fpu_stochastic_round: bool | None = F("ALU_ROUNDING_MODE_Fpu_srnd_en")
  gasket_stochastic_round: bool | None = F("ALU_ROUNDING_MODE_Gasket_srnd_en")
  packer_stochastic_round: bool | None = F("ALU_ROUNDING_MODE_Packer_srnd_en")
  round_gs_lf: bool | None = F("ALU_ROUNDING_MODE_GS_LF")
  round_bfp8_hf: bool | None = F("ALU_ROUNDING_MODE_Bfp8_HF")
  disable_src_zero_flags: bool | None = F("ALU_ACC_CTRL_Zero_Flag_disabled_src")
  disable_dest_zero_flags: bool | None = F("ALU_ACC_CTRL_Zero_Flag_disabled_dst")
  relu_mode: int | None = F("STACC_RELU_ApplyRelu")  # applied by the packer: 0 off, 1 zero below 0, 2/3 threshold modes
  relu_threshold: int | None = F("STACC_RELU_ReluThreshold")

@dataclass(frozen=True)
class DestAccessCfg(Config):
  SCOPE = Thread.MATH
  swizzle_32b: bool | None = F("DEST_ACCESS_CFG_swizzle_32b")
  remap_addrs: bool | None = F("DEST_ACCESS_CFG_remap_addrs")  # swizzle + remap = strided reads (blackhole-py writes 3)
  disable_write_bypass: bool | None = F("DEST_ACCESS_CFG_disable_full_write_dest_q_bypass")
  zeroacc_absolute_tile: bool | None = F("DEST_ACCESS_CFG_zeroacc_absolute_tile_mode")  # ZEROACC dest_row is a tile index

# ***** per-thread config (SETC16) *****

@dataclass(frozen=True)
class ThreadCfg(Config):
  thread: Thread = K()
  state_id: int | None = F("CFG_STATE_ID_StateID")  # which SHARED bank this thread reads
  math_dest_offset: int | None = F("DEST_TARGET_REG_CFG_MATH_Offset")  # Dest row base for FPU/SFPU ops
  srca_bank: int | None = F("SRCA_SET_Base")  # SrcA bank/row base used by moves; blackhole-py: 4 normally, 0 for unpack-to-Dest
  srca_bank_override: bool | None = F("SRCA_SET_SetOvrdWithAddr")
  keep_srca_dvalid: bool | None = F("CLR_DVALID_SrcA_Disable")
  keep_srcb_dvalid: bool | None = F("CLR_DVALID_SrcB_Disable")
  unpack0_context: int | None = F("UNPACK_MISC_CFG_CfgContextOffset_0")
  unpack0_context_reset: bool | None = F("UNPACK_MISC_CFG_CfgContextCntReset_0")
  unpack0_context_inc: bool | None = F("UNPACK_MISC_CFG_CfgContextCntInc_0")
  unpack1_context: int | None = F("UNPACK_MISC_CFG_CfgContextOffset_1")
  unpack1_context_reset: bool | None = F("UNPACK_MISC_CFG_CfgContextCntReset_1")
  unpack1_context_inc: bool | None = F("UNPACK_MISC_CFG_CfgContextCntInc_1")

@dataclass(frozen=True)
class AddrMod(Config):
  """One of 8 ADDR_MOD slots: how SrcA/SrcB/Dest/fidelity counters move after an FPU op that names this slot."""
  INDEX = "slot"
  thread: Thread = K()
  slot: int = K()
  srca_incr: int = F(*per("ADDR_MOD_AB_SEC{i}_SrcAIncr", 8), default=0)
  srca_carry: bool = F(*per("ADDR_MOD_AB_SEC{i}_SrcACR", 8), default=False)  # also add to the carry register
  srca_clear: bool = F(*per("ADDR_MOD_AB_SEC{i}_SrcAClear", 8), default=False)
  srcb_incr: int = F(*per("ADDR_MOD_AB_SEC{i}_SrcBIncr", 8), default=0)
  srcb_carry: bool = F(*per("ADDR_MOD_AB_SEC{i}_SrcBCR", 8), default=False)
  srcb_clear: bool = F(*per("ADDR_MOD_AB_SEC{i}_SrcBClear", 8), default=False)
  dest_incr: int = F(*per("ADDR_MOD_DST_SEC{i}_DestIncr", 8), default=0)
  dest_carry: bool = F(*per("ADDR_MOD_DST_SEC{i}_DestCR", 8), default=False)
  dest_clear: bool = F(*per("ADDR_MOD_DST_SEC{i}_DestClear", 8), default=False)
  dest_counter_to_carry: bool = F(*per("ADDR_MOD_DST_SEC{i}_DestCToCR", 8), default=False)
  fidelity_incr: int = F(*per("ADDR_MOD_DST_SEC{i}_FidelityIncr", 8), default=0)
  fidelity_clear: bool = F(*per("ADDR_MOD_DST_SEC{i}_FidelityClear", 8), default=False)
  bias_incr: int = F(*per("ADDR_MOD_BIAS_SEC{i}_BiasIncr", 8), default=0)
  bias_clear: bool = F(*per("ADDR_MOD_BIAS_SEC{i}_BiasClear", 8), default=False)

@dataclass(frozen=True)
class PackAddrMod(Config):
  """One of 3 packer ADDR_MOD slots (PACR addr_mod): how the Dest y/z (src) and L1 y/z (dst) counters move."""
  INDEX, SCOPE = "slot", Thread.PACK
  slot: int = K()
  y_src_incr: int = F(*per("ADDR_MOD_PACK_SEC{i}_YsrcIncr", 3), default=0)
  y_src_carry: bool = F(*per("ADDR_MOD_PACK_SEC{i}_YsrcCR", 3), default=False)
  y_src_clear: bool = F(*per("ADDR_MOD_PACK_SEC{i}_YsrcClear", 3), default=False)
  y_dst_incr: int = F(*per("ADDR_MOD_PACK_SEC{i}_YdstIncr", 3), default=0)
  y_dst_carry: bool = F(*per("ADDR_MOD_PACK_SEC{i}_YdstCR", 3), default=False)
  y_dst_clear: bool = F(*per("ADDR_MOD_PACK_SEC{i}_YdstClear", 3), default=False)
  z_src_incr: int = F(*per("ADDR_MOD_PACK_SEC{i}_ZsrcIncr", 3), default=0)
  z_src_clear: bool = F(*per("ADDR_MOD_PACK_SEC{i}_ZsrcClear", 3), default=False)
  z_dst_incr: int = F(*per("ADDR_MOD_PACK_SEC{i}_ZdstIncr", 3), default=0)
  z_dst_clear: bool = F(*per("ADDR_MOD_PACK_SEC{i}_ZdstClear", 3), default=False)

# ***** MOP expander and replay buffer (per thread) *****

@dataclass(frozen=True)
class MopLoop(Config):
  """MOP template 1 (MOP template=1): a double loop. Slots are Tensix instruction words (TTREPLAY to run a replay range)."""
  thread: Thread = K()
  outer_count: int | None = F("MOP_CFG_0")
  inner_count: int | None = F("MOP_CFG_1")
  start: int | None = F("MOP_CFG_2")       # once, before the loops
  end_inner_0: int | None = F("MOP_CFG_3")  # after each inner loop
  end_inner_1: int | None = F("MOP_CFG_4")
  body: int | None = F("MOP_CFG_5")         # inner loop body
  body_alt: int | None = F("MOP_CFG_6")     # alternates with body on odd iterations
  last_inner: int | None = F("MOP_CFG_7")   # replaces body on the last inner iteration
  last_outer: int | None = F("MOP_CFG_8")   # replaces body on the very last iteration

@dataclass(frozen=True)
class MopMask(Config):
  """MOP template 0: unpack loop driven by a 32-bit zmask (MOP mask_lo / MOP_CFG mask_hi). Each bit runs the a slots or the skip slot."""
  thread: Thread = K()
  flags: int | None = F("MOP_CFG_1")    # bit 0: run b after a; bit 1: run a1..a3 too (ttko MaskTemplate derives this)
  b: int | None = F("MOP_CFG_2")
  a0: int | None = F("MOP_CFG_3")
  a1: int | None = F("MOP_CFG_4")
  a2: int | None = F("MOP_CFG_5")
  a3: int | None = F("MOP_CFG_6")
  skip_a0: int | None = F("MOP_CFG_7")
  skip_b: int | None = F("MOP_CFG_8")

@dataclass(frozen=True)
class ReplaySlots(Config):
  """Replay buffer contents: slots start .. start+len(words)-1 hold these Tensix words."""
  thread: Thread = K()
  start: int = K()
  words: tuple[int, ...] = ()
  def writes(self):
    if not 0 <= self.start and self.start + len(self.words) <= 32: raise ValueError("replay buffer has 32 slots")
    return {(Space.REPLAY, self.thread, self.start + i): (w, 0xFFFFFFFF) for i, w in enumerate(self.words)}

# ***** SFPU (math thread) *****

@dataclass(frozen=True)
class SfpuLaneCfg(Config):
  SCOPE = Thread.MATH
  enable_fp16_infinity: bool | None = F("SFPU_LANE_enable_fp16_infinity")
  disable_backdoor_load: bool | None = F("SFPU_LANE_disable_backdoor_load")
  enable_dest_index: bool | None = F("SFPU_LANE_enable_destination_index")
  capture_default_dest_index: bool | None = F("SFPU_LANE_capture_default_destination_index")
  block_dest_write: bool | None = F("SFPU_LANE_block_destination_write")
  block_dest_read: bool | None = F("SFPU_LANE_block_destination_read")
  dest_read_column_exchange: bool | None = F("SFPU_LANE_destination_read_column_exchange")
  dest_write_column_exchange: bool | None = F("SFPU_LANE_destination_write_column_exchange")
  exchange_srcb_srcc: bool | None = F("SFPU_LANE_exchange_srcb_srcc")
  block_dest_move: int | None = F("SFPU_LANE_block_destination_move")
  row_mask: int | None = F("SFPU_LANE_row_mask")

@dataclass(frozen=True)
class SfpuConstant(Config):
  """Programmable constant LReg 12..14 (CONFIG0..2), loaded with SFPLOADI into L0 then SFPCONFIG(.., index, 0)."""
  SCOPE = Thread.MATH
  index: int = K()
  value: int | None = None
  def writes(self): return {(Space.SFPU, Thread.MATH, self.index): (self.value, 0xFFFFFFFF)} if self.value is not None else {}

@dataclass(frozen=True)
class SfpuMacro(Config):
  """SFPLOADMACRO programming: instruction templates (slots 0-3), sequences (4-7) and the misc word (8)."""
  SCOPE = Thread.MATH
  slot: int = K()   # 0..8, the SFPCONFIG config_reg
  value: int | None = None
  def writes(self): return {(Space.SFPU, Thread.MATH, self.slot): (self.value, 0xFFFFFFFF)} if self.value is not None else {}

# ***** sync *****

@dataclass(frozen=True)
class SemInit(Config):
  """Tensix semaphore 0..7 bounds. SEMINIT also sets the value, so this is only redundant until the next SEMPOST/SEMGET."""
  sem: int = K()
  init: int | None = None
  max: int | None = None
  def writes(self): return {(Space.SEM, None, self.sem): ((self.init or 0) | (self.max or 0) << 4, 0xFF)}

# ***** GPRs used as constant sources (tile header, face dims, exp section size) *****

@dataclass(frozen=True)
class Gpr(Config):
  thread: Thread = K()
  index: int = K()
  value: int | None = None
  def writes(self): return {(Space.GPR, self.thread, self.index): (self.value, 0xFFFFFFFF)} if self.value is not None else {}

# ***** NoC command buffer (READ / WRITE RISCs) *****

class NocCmd(IntEnum): READ = 0; ATOMIC = 1; WRITE = 2

@dataclass(frozen=True)
class NocCmdBuf(Config):
  """Resident state of one NIU command buffer. Kicking it (NOC_CMD_CTRL = 1) is a separate op and never deduped."""
  thread: Thread = K()   # Thread.READ or Thread.WRITE
  noc: int = K()         # 0 or 1
  buf: int = K()         # 0..3; blackhole-py: 0 write, 1 read, 2 reg write, 3 atomic
  def base(self): return 0xFFB20000 + (self.noc << 16) + (self.buf << 11)
  # NOC_CTRL: what kind of packet
  cmd: NocCmd | None = F("NOC_CTRL_cmd")
  posted: bool | None = None  # write without waiting for the ack (lowers to resp_marked = not posted); reads/atomics never posted
  inline: bool | None = F("NOC_CTRL_wr_inline")  # write at_data instead of reading a source
  multicast: bool | None = F("NOC_CTRL_brcst_packet")
  linked: bool | None = F("NOC_CTRL_vc_linked")  # keep the multicast path open for the next packet
  # addresses: target = the far side (source of reads, destination of writes); return = the local side
  targ_addr: int | None = F("NOC_TARG_ADDR_LO")
  targ_addr_mid: int | None = F("NOC_TARG_ADDR_MID")
  targ_coord: int | None = F("NOC_TARG_ADDR_HI")       # x | y << 6, or a multicast rectangle
  ret_addr: int | None = F("NOC_RET_ADDR_LO")
  ret_addr_mid: int | None = F("NOC_RET_ADDR_MID")
  ret_coord: int | None = F("NOC_RET_ADDR_HI")
  transaction_id: int | None = F("NOC_PACKET_TAG_transaction_id")
  length: int | None = F("NOC_AT_LEN_BE")              # bytes, or the atomic opcode word
  at_data: int | None = F("NOC_AT_DATA")               # inline value / atomic increment

  def _user_values(self):
    yield from super()._user_values()
    if self.cmd is not None:
      yield "posted", self._resolve("posted", ("NOC_CTRL_resp_marked",)), int(not (self.posted and self.cmd is NocCmd.WRITE))

  # exist in hardware but make no measurable difference in kernels: pinned to ttko.noc.NoC's policy
  FIXED = {
    "static_vc": ("NOC_CTRL_vc_static", 1),
    "vc": ("NOC_CTRL_static_vc", lambda c: 4 if c.multicast else 1),
    "byte_enable": ("NOC_CTRL_wr_be", 0),
    "path_reserve": ("NOC_CTRL_path_reserve", 0),
    "drop_read_ack": ("NOC_CTRL_mem_rd_drop_ack", 0),
    "multicast_along_y": ("NOC_CTRL_brcst_xy", 0),
    "multicast_include_sender": ("NOC_CTRL_brcst_src_include", 0),
    "priority": ("NOC_CTRL_arb_priority", 0),
    "l1_accumulate": ("NOC_CTRL_l1_acc_at_en", 0),
    "length_hi": ("NOC_AT_LEN_BE_1", 0),
  }

# ***** locations that cfg_defines.h does not provide *****

def _tile_desc(n, base):
  w = lambda word, shift, width: Loc(Space.SHARED, base + word, shift, width)
  return {f"TILE_DESC{n}_in_data_format": w(0, 0, 4), f"TILE_DESC{n}_uncompressed": w(0, 4, 1),
          f"TILE_DESC{n}_blobs_per_xy_plane": w(0, 8, 4), f"TILE_DESC{n}_x_dim": w(0, 16, 16),
          f"TILE_DESC{n}_y_dim": w(1, 0, 16), f"TILE_DESC{n}_z_dim": w(1, 16, 16), f"TILE_DESC{n}_w_dim": w(2, 0, 16)}

_LANE = ("enable_fp16_infinity", "disable_backdoor_load", "enable_destination_index", "capture_default_destination_index",
         "block_destination_write", "block_destination_read", "destination_read_column_exchange", "destination_write_column_exchange",
         "exchange_srcb_srcc")
_NOC_CTRL = {"cmd": (0, 2), "wr_be": (2, 1), "wr_inline": (3, 1), "resp_marked": (4, 1), "brcst_packet": (5, 1), "vc_linked": (6, 1),
             "vc_static": (7, 1), "path_reserve": (8, 1), "mem_rd_drop_ack": (9, 1), "static_vc": (13, 3), "brcst_xy": (16, 1),
             "brcst_src_include": (17, 1), "arb_priority": (27, 4), "l1_acc_at_en": (31, 1)}
_NOC_REGS = {"NOC_TARG_ADDR_LO": 0x0, "NOC_TARG_ADDR_MID": 0x4, "NOC_TARG_ADDR_HI": 0x8, "NOC_RET_ADDR_LO": 0xC, "NOC_RET_ADDR_MID": 0x10,
             "NOC_RET_ADDR_HI": 0x14, "NOC_AT_LEN_BE": 0x20, "NOC_AT_LEN_BE_1": 0x24, "NOC_AT_DATA": 0x28}

MANUAL_REGS = {
  **_tile_desc(0, 64), **_tile_desc(1, 112),
  "TILE_ROW_SET_MAPPING_0": Loc(Space.SHARED, 20, 0, 32), "TILE_ROW_SET_MAPPING_1": Loc(Space.SHARED, 21, 0, 32),
  **{f"MOP_CFG_{i}": Loc(Space.MMIO, 0xFFB80000 + 4 * i, 0, 32) for i in range(9)},
  **{f"SFPU_LANE_{n}": Loc(Space.SFPU, 15, i, 1) for i, n in enumerate(_LANE)},
  "SFPU_LANE_block_destination_move": Loc(Space.SFPU, 15, 9, 2), "SFPU_LANE_row_mask": Loc(Space.SFPU, 15, 12, 4),
  **{f"NOC_CTRL_{n}": Loc(Space.MMIO, 0x1C, s, w) for n, (s, w) in _NOC_CTRL.items()},
  **{n: Loc(Space.MMIO, off, 0, 32) for n, off in _NOC_REGS.items()},
  "NOC_PACKET_TAG_transaction_id": Loc(Space.MMIO, 0x18, 10, 4),
}

# generated from cfg_defines.h by tools/gen_config_regs.py: raw name -> (space, addr32, shift, width)
_CFG_DEFINES = {
  "ADDR_MOD_AB_SEC0_SrcACR": ("thread", 12, 6, 1),
  "ADDR_MOD_AB_SEC0_SrcAClear": ("thread", 12, 7, 1),
  "ADDR_MOD_AB_SEC0_SrcAIncr": ("thread", 12, 0, 6),
  "ADDR_MOD_AB_SEC0_SrcBCR": ("thread", 12, 14, 1),
  "ADDR_MOD_AB_SEC0_SrcBClear": ("thread", 12, 15, 1),
  "ADDR_MOD_AB_SEC0_SrcBIncr": ("thread", 12, 8, 6),
  "ADDR_MOD_AB_SEC1_SrcACR": ("thread", 13, 6, 1),
  "ADDR_MOD_AB_SEC1_SrcAClear": ("thread", 13, 7, 1),
  "ADDR_MOD_AB_SEC1_SrcAIncr": ("thread", 13, 0, 6),
  "ADDR_MOD_AB_SEC1_SrcBCR": ("thread", 13, 14, 1),
  "ADDR_MOD_AB_SEC1_SrcBClear": ("thread", 13, 15, 1),
  "ADDR_MOD_AB_SEC1_SrcBIncr": ("thread", 13, 8, 6),
  "ADDR_MOD_AB_SEC2_SrcACR": ("thread", 14, 6, 1),
  "ADDR_MOD_AB_SEC2_SrcAClear": ("thread", 14, 7, 1),
  "ADDR_MOD_AB_SEC2_SrcAIncr": ("thread", 14, 0, 6),
  "ADDR_MOD_AB_SEC2_SrcBCR": ("thread", 14, 14, 1),
  "ADDR_MOD_AB_SEC2_SrcBClear": ("thread", 14, 15, 1),
  "ADDR_MOD_AB_SEC2_SrcBIncr": ("thread", 14, 8, 6),
  "ADDR_MOD_AB_SEC3_SrcACR": ("thread", 15, 6, 1),
  "ADDR_MOD_AB_SEC3_SrcAClear": ("thread", 15, 7, 1),
  "ADDR_MOD_AB_SEC3_SrcAIncr": ("thread", 15, 0, 6),
  "ADDR_MOD_AB_SEC3_SrcBCR": ("thread", 15, 14, 1),
  "ADDR_MOD_AB_SEC3_SrcBClear": ("thread", 15, 15, 1),
  "ADDR_MOD_AB_SEC3_SrcBIncr": ("thread", 15, 8, 6),
  "ADDR_MOD_AB_SEC4_SrcACR": ("thread", 16, 6, 1),
  "ADDR_MOD_AB_SEC4_SrcAClear": ("thread", 16, 7, 1),
  "ADDR_MOD_AB_SEC4_SrcAIncr": ("thread", 16, 0, 6),
  "ADDR_MOD_AB_SEC4_SrcBCR": ("thread", 16, 14, 1),
  "ADDR_MOD_AB_SEC4_SrcBClear": ("thread", 16, 15, 1),
  "ADDR_MOD_AB_SEC4_SrcBIncr": ("thread", 16, 8, 6),
  "ADDR_MOD_AB_SEC5_SrcACR": ("thread", 17, 6, 1),
  "ADDR_MOD_AB_SEC5_SrcAClear": ("thread", 17, 7, 1),
  "ADDR_MOD_AB_SEC5_SrcAIncr": ("thread", 17, 0, 6),
  "ADDR_MOD_AB_SEC5_SrcBCR": ("thread", 17, 14, 1),
  "ADDR_MOD_AB_SEC5_SrcBClear": ("thread", 17, 15, 1),
  "ADDR_MOD_AB_SEC5_SrcBIncr": ("thread", 17, 8, 6),
  "ADDR_MOD_AB_SEC6_SrcACR": ("thread", 18, 6, 1),
  "ADDR_MOD_AB_SEC6_SrcAClear": ("thread", 18, 7, 1),
  "ADDR_MOD_AB_SEC6_SrcAIncr": ("thread", 18, 0, 6),
  "ADDR_MOD_AB_SEC6_SrcBCR": ("thread", 18, 14, 1),
  "ADDR_MOD_AB_SEC6_SrcBClear": ("thread", 18, 15, 1),
  "ADDR_MOD_AB_SEC6_SrcBIncr": ("thread", 18, 8, 6),
  "ADDR_MOD_AB_SEC7_SrcACR": ("thread", 19, 6, 1),
  "ADDR_MOD_AB_SEC7_SrcAClear": ("thread", 19, 7, 1),
  "ADDR_MOD_AB_SEC7_SrcAIncr": ("thread", 19, 0, 6),
  "ADDR_MOD_AB_SEC7_SrcBCR": ("thread", 19, 14, 1),
  "ADDR_MOD_AB_SEC7_SrcBClear": ("thread", 19, 15, 1),
  "ADDR_MOD_AB_SEC7_SrcBIncr": ("thread", 19, 8, 6),
  "ADDR_MOD_BIAS_SEC0_BiasClear": ("thread", 47, 4, 1),
  "ADDR_MOD_BIAS_SEC0_BiasIncr": ("thread", 47, 0, 4),
  "ADDR_MOD_BIAS_SEC1_BiasClear": ("thread", 48, 4, 1),
  "ADDR_MOD_BIAS_SEC1_BiasIncr": ("thread", 48, 0, 4),
  "ADDR_MOD_BIAS_SEC2_BiasClear": ("thread", 49, 4, 1),
  "ADDR_MOD_BIAS_SEC2_BiasIncr": ("thread", 49, 0, 4),
  "ADDR_MOD_BIAS_SEC3_BiasClear": ("thread", 50, 4, 1),
  "ADDR_MOD_BIAS_SEC3_BiasIncr": ("thread", 50, 0, 4),
  "ADDR_MOD_BIAS_SEC4_BiasClear": ("thread", 51, 4, 1),
  "ADDR_MOD_BIAS_SEC4_BiasIncr": ("thread", 51, 0, 4),
  "ADDR_MOD_BIAS_SEC5_BiasClear": ("thread", 52, 4, 1),
  "ADDR_MOD_BIAS_SEC5_BiasIncr": ("thread", 52, 0, 4),
  "ADDR_MOD_BIAS_SEC6_BiasClear": ("thread", 53, 4, 1),
  "ADDR_MOD_BIAS_SEC6_BiasIncr": ("thread", 53, 0, 4),
  "ADDR_MOD_BIAS_SEC7_BiasClear": ("thread", 54, 4, 1),
  "ADDR_MOD_BIAS_SEC7_BiasIncr": ("thread", 54, 0, 4),
  "ADDR_MOD_DST_SEC0_DestCR": ("thread", 28, 10, 1),
  "ADDR_MOD_DST_SEC0_DestCToCR": ("thread", 28, 12, 1),
  "ADDR_MOD_DST_SEC0_DestClear": ("thread", 28, 11, 1),
  "ADDR_MOD_DST_SEC0_DestIncr": ("thread", 28, 0, 10),
  "ADDR_MOD_DST_SEC0_FidelityClear": ("thread", 28, 15, 1),
  "ADDR_MOD_DST_SEC0_FidelityIncr": ("thread", 28, 13, 2),
  "ADDR_MOD_DST_SEC1_DestCR": ("thread", 29, 10, 1),
  "ADDR_MOD_DST_SEC1_DestCToCR": ("thread", 29, 12, 1),
  "ADDR_MOD_DST_SEC1_DestClear": ("thread", 29, 11, 1),
  "ADDR_MOD_DST_SEC1_DestIncr": ("thread", 29, 0, 10),
  "ADDR_MOD_DST_SEC1_FidelityClear": ("thread", 29, 15, 1),
  "ADDR_MOD_DST_SEC1_FidelityIncr": ("thread", 29, 13, 2),
  "ADDR_MOD_DST_SEC2_DestCR": ("thread", 30, 10, 1),
  "ADDR_MOD_DST_SEC2_DestCToCR": ("thread", 30, 12, 1),
  "ADDR_MOD_DST_SEC2_DestClear": ("thread", 30, 11, 1),
  "ADDR_MOD_DST_SEC2_DestIncr": ("thread", 30, 0, 10),
  "ADDR_MOD_DST_SEC2_FidelityClear": ("thread", 30, 15, 1),
  "ADDR_MOD_DST_SEC2_FidelityIncr": ("thread", 30, 13, 2),
  "ADDR_MOD_DST_SEC3_DestCR": ("thread", 31, 10, 1),
  "ADDR_MOD_DST_SEC3_DestCToCR": ("thread", 31, 12, 1),
  "ADDR_MOD_DST_SEC3_DestClear": ("thread", 31, 11, 1),
  "ADDR_MOD_DST_SEC3_DestIncr": ("thread", 31, 0, 10),
  "ADDR_MOD_DST_SEC3_FidelityClear": ("thread", 31, 15, 1),
  "ADDR_MOD_DST_SEC3_FidelityIncr": ("thread", 31, 13, 2),
  "ADDR_MOD_DST_SEC4_DestCR": ("thread", 32, 10, 1),
  "ADDR_MOD_DST_SEC4_DestCToCR": ("thread", 32, 12, 1),
  "ADDR_MOD_DST_SEC4_DestClear": ("thread", 32, 11, 1),
  "ADDR_MOD_DST_SEC4_DestIncr": ("thread", 32, 0, 10),
  "ADDR_MOD_DST_SEC4_FidelityClear": ("thread", 32, 15, 1),
  "ADDR_MOD_DST_SEC4_FidelityIncr": ("thread", 32, 13, 2),
  "ADDR_MOD_DST_SEC5_DestCR": ("thread", 33, 10, 1),
  "ADDR_MOD_DST_SEC5_DestCToCR": ("thread", 33, 12, 1),
  "ADDR_MOD_DST_SEC5_DestClear": ("thread", 33, 11, 1),
  "ADDR_MOD_DST_SEC5_DestIncr": ("thread", 33, 0, 10),
  "ADDR_MOD_DST_SEC5_FidelityClear": ("thread", 33, 15, 1),
  "ADDR_MOD_DST_SEC5_FidelityIncr": ("thread", 33, 13, 2),
  "ADDR_MOD_DST_SEC6_DestCR": ("thread", 34, 10, 1),
  "ADDR_MOD_DST_SEC6_DestCToCR": ("thread", 34, 12, 1),
  "ADDR_MOD_DST_SEC6_DestClear": ("thread", 34, 11, 1),
  "ADDR_MOD_DST_SEC6_DestIncr": ("thread", 34, 0, 10),
  "ADDR_MOD_DST_SEC6_FidelityClear": ("thread", 34, 15, 1),
  "ADDR_MOD_DST_SEC6_FidelityIncr": ("thread", 34, 13, 2),
  "ADDR_MOD_DST_SEC7_DestCR": ("thread", 35, 10, 1),
  "ADDR_MOD_DST_SEC7_DestCToCR": ("thread", 35, 12, 1),
  "ADDR_MOD_DST_SEC7_DestClear": ("thread", 35, 11, 1),
  "ADDR_MOD_DST_SEC7_DestIncr": ("thread", 35, 0, 10),
  "ADDR_MOD_DST_SEC7_FidelityClear": ("thread", 35, 15, 1),
  "ADDR_MOD_DST_SEC7_FidelityIncr": ("thread", 35, 13, 2),
  "ADDR_MOD_PACK_SEC0_YdstCR": ("thread", 37, 10, 1),
  "ADDR_MOD_PACK_SEC0_YdstClear": ("thread", 37, 11, 1),
  "ADDR_MOD_PACK_SEC0_YdstIncr": ("thread", 37, 6, 4),
  "ADDR_MOD_PACK_SEC0_YsrcCR": ("thread", 37, 4, 1),
  "ADDR_MOD_PACK_SEC0_YsrcClear": ("thread", 37, 5, 1),
  "ADDR_MOD_PACK_SEC0_YsrcIncr": ("thread", 37, 0, 4),
  "ADDR_MOD_PACK_SEC0_ZdstClear": ("thread", 37, 15, 1),
  "ADDR_MOD_PACK_SEC0_ZdstIncr": ("thread", 37, 14, 1),
  "ADDR_MOD_PACK_SEC0_ZsrcClear": ("thread", 37, 13, 1),
  "ADDR_MOD_PACK_SEC0_ZsrcIncr": ("thread", 37, 12, 1),
  "ADDR_MOD_PACK_SEC1_YdstCR": ("thread", 38, 10, 1),
  "ADDR_MOD_PACK_SEC1_YdstClear": ("thread", 38, 11, 1),
  "ADDR_MOD_PACK_SEC1_YdstIncr": ("thread", 38, 6, 4),
  "ADDR_MOD_PACK_SEC1_YsrcCR": ("thread", 38, 4, 1),
  "ADDR_MOD_PACK_SEC1_YsrcClear": ("thread", 38, 5, 1),
  "ADDR_MOD_PACK_SEC1_YsrcIncr": ("thread", 38, 0, 4),
  "ADDR_MOD_PACK_SEC1_ZdstClear": ("thread", 38, 15, 1),
  "ADDR_MOD_PACK_SEC1_ZdstIncr": ("thread", 38, 14, 1),
  "ADDR_MOD_PACK_SEC1_ZsrcClear": ("thread", 38, 13, 1),
  "ADDR_MOD_PACK_SEC1_ZsrcIncr": ("thread", 38, 12, 1),
  "ADDR_MOD_PACK_SEC2_YdstCR": ("thread", 39, 10, 1),
  "ADDR_MOD_PACK_SEC2_YdstClear": ("thread", 39, 11, 1),
  "ADDR_MOD_PACK_SEC2_YdstIncr": ("thread", 39, 6, 4),
  "ADDR_MOD_PACK_SEC2_YsrcCR": ("thread", 39, 4, 1),
  "ADDR_MOD_PACK_SEC2_YsrcClear": ("thread", 39, 5, 1),
  "ADDR_MOD_PACK_SEC2_YsrcIncr": ("thread", 39, 0, 4),
  "ADDR_MOD_PACK_SEC2_ZdstClear": ("thread", 39, 15, 1),
  "ADDR_MOD_PACK_SEC2_ZdstIncr": ("thread", 39, 14, 1),
  "ADDR_MOD_PACK_SEC2_ZsrcClear": ("thread", 39, 13, 1),
  "ADDR_MOD_PACK_SEC2_ZsrcIncr": ("thread", 39, 12, 1),
  "ALU_ACC_CTRL_Fp32_enabled": ("shared", 1, 29, 1),
  "ALU_ACC_CTRL_INT8_math_enabled": ("shared", 1, 31, 1),
  "ALU_ACC_CTRL_SFPU_Fp32_enabled": ("shared", 1, 30, 1),
  "ALU_ACC_CTRL_Zero_Flag_disabled_dst": ("shared", 2, 1, 1),
  "ALU_ACC_CTRL_Zero_Flag_disabled_src": ("shared", 2, 0, 1),
  "ALU_FORMAT_SPEC_REG0_SrcA": ("shared", 1, 17, 4),
  "ALU_FORMAT_SPEC_REG0_SrcAUnsigned": ("shared", 1, 15, 1),
  "ALU_FORMAT_SPEC_REG0_SrcBUnsigned": ("shared", 1, 16, 1),
  "ALU_FORMAT_SPEC_REG1_SrcB": ("shared", 1, 21, 4),
  "ALU_FORMAT_SPEC_REG2_Dstacc": ("shared", 1, 25, 4),
  "ALU_FORMAT_SPEC_REG_Dstacc_override": ("shared", 0, 14, 1),
  "ALU_FORMAT_SPEC_REG_Dstacc_val": ("shared", 0, 10, 4),
  "ALU_FORMAT_SPEC_REG_SrcA_override": ("shared", 0, 4, 1),
  "ALU_FORMAT_SPEC_REG_SrcA_val": ("shared", 0, 0, 4),
  "ALU_FORMAT_SPEC_REG_SrcB_override": ("shared", 0, 9, 1),
  "ALU_FORMAT_SPEC_REG_SrcB_val": ("shared", 0, 5, 4),
  "ALU_ROUNDING_MODE_Bfp8_HF": ("shared", 1, 14, 1),
  "ALU_ROUNDING_MODE_Fpu_srnd_en": ("shared", 1, 0, 1),
  "ALU_ROUNDING_MODE_GS_LF": ("shared", 1, 13, 1),
  "ALU_ROUNDING_MODE_Gasket_srnd_en": ("shared", 1, 1, 1),
  "ALU_ROUNDING_MODE_Packer_srnd_en": ("shared", 1, 2, 1),
  "CFG_STATE_ID_StateID": ("thread", 0, 0, 1),
  "CLR_DVALID_SrcA_Disable": ("thread", 7, 0, 1),
  "CLR_DVALID_SrcB_Disable": ("thread", 7, 1, 1),
  "DEST_ACCESS_CFG_disable_full_write_dest_q_bypass": ("shared", 220, 2, 1),
  "DEST_ACCESS_CFG_remap_addrs": ("shared", 220, 1, 1),
  "DEST_ACCESS_CFG_swizzle_32b": ("shared", 220, 0, 1),
  "DEST_ACCESS_CFG_zeroacc_absolute_tile_mode": ("shared", 220, 3, 1),
  "DEST_TARGET_REG_CFG_MATH_Offset": ("thread", 1, 0, 12),
  "DEST_TARGET_REG_CFG_PACK_SEC0_Offset": ("shared", 180, 0, 12),
  "DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset": ("shared", 180, 12, 6),
  "DEST_TARGET_REG_CFG_PACK_SEC1_Offset": ("shared", 181, 0, 12),
  "DEST_TARGET_REG_CFG_PACK_SEC1_ZOffset": ("shared", 181, 12, 6),
  "DEST_TARGET_REG_CFG_PACK_SEC2_Offset": ("shared", 182, 0, 12),
  "DEST_TARGET_REG_CFG_PACK_SEC2_ZOffset": ("shared", 182, 12, 6),
  "DEST_TARGET_REG_CFG_PACK_SEC3_Offset": ("shared", 183, 0, 12),
  "DEST_TARGET_REG_CFG_PACK_SEC3_ZOffset": ("shared", 183, 12, 6),
  "PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt": ("shared", 28, 24, 8),
  "PACK_COUNTERS_SEC0_pack_per_xy_plane": ("shared", 28, 0, 8),
  "PACK_COUNTERS_SEC0_pack_reads_per_xy_plane": ("shared", 28, 8, 8),
  "PACK_COUNTERS_SEC0_pack_xys_per_tile": ("shared", 28, 16, 7),
  "PACK_COUNTERS_SEC0_pack_yz_transposed": ("shared", 28, 23, 1),
  "PACK_COUNTERS_SEC1_auto_ctxt_inc_xys_cnt": ("shared", 29, 24, 8),
  "PACK_COUNTERS_SEC1_pack_per_xy_plane": ("shared", 29, 0, 8),
  "PACK_COUNTERS_SEC1_pack_reads_per_xy_plane": ("shared", 29, 8, 8),
  "PACK_COUNTERS_SEC1_pack_xys_per_tile": ("shared", 29, 16, 7),
  "PACK_COUNTERS_SEC1_pack_yz_transposed": ("shared", 29, 23, 1),
  "PACK_COUNTERS_SEC2_auto_ctxt_inc_xys_cnt": ("shared", 30, 24, 8),
  "PACK_COUNTERS_SEC2_pack_per_xy_plane": ("shared", 30, 0, 8),
  "PACK_COUNTERS_SEC2_pack_reads_per_xy_plane": ("shared", 30, 8, 8),
  "PACK_COUNTERS_SEC2_pack_xys_per_tile": ("shared", 30, 16, 7),
  "PACK_COUNTERS_SEC2_pack_yz_transposed": ("shared", 30, 23, 1),
  "PACK_COUNTERS_SEC3_auto_ctxt_inc_xys_cnt": ("shared", 31, 24, 8),
  "PACK_COUNTERS_SEC3_pack_per_xy_plane": ("shared", 31, 0, 8),
  "PACK_COUNTERS_SEC3_pack_reads_per_xy_plane": ("shared", 31, 8, 8),
  "PACK_COUNTERS_SEC3_pack_xys_per_tile": ("shared", 31, 16, 7),
  "PACK_COUNTERS_SEC3_pack_yz_transposed": ("shared", 31, 23, 1),
  "PCK0_ADDR_BASE_REG_0_Base": ("shared", 16, 0, 18),
  "PCK0_ADDR_BASE_REG_1_Base": ("shared", 17, 0, 18),
  "PCK0_ADDR_CTRL_XY_REG_0_Xstride": ("shared", 12, 0, 16),
  "PCK0_ADDR_CTRL_XY_REG_0_Ystride": ("shared", 12, 16, 16),
  "PCK0_ADDR_CTRL_XY_REG_1_Xstride": ("shared", 14, 0, 16),
  "PCK0_ADDR_CTRL_XY_REG_1_Ystride": ("shared", 14, 16, 16),
  "PCK0_ADDR_CTRL_ZW_REG_0_Wstride": ("shared", 13, 16, 16),
  "PCK0_ADDR_CTRL_ZW_REG_0_Zstride": ("shared", 13, 0, 16),
  "PCK0_ADDR_CTRL_ZW_REG_1_Wstride": ("shared", 15, 16, 16),
  "PCK0_ADDR_CTRL_ZW_REG_1_Zstride": ("shared", 15, 0, 16),
  "PCK_DEST_RD_CTRL_Read_32b_data": ("shared", 18, 0, 1),
  "PCK_DEST_RD_CTRL_Read_int8": ("shared", 18, 2, 1),
  "PCK_DEST_RD_CTRL_Read_unsigned": ("shared", 18, 1, 1),
  "PCK_DEST_RD_CTRL_Round_10b_mant": ("shared", 18, 3, 1),
  "PCK_EDGE_OFFSET_SEC0_mask": ("shared", 24, 0, 16),
  "PCK_EDGE_OFFSET_SEC1_mask": ("shared", 25, 0, 16),
  "PCK_EDGE_OFFSET_SEC2_mask": ("shared", 26, 0, 16),
  "PCK_EDGE_OFFSET_SEC3_mask": ("shared", 27, 0, 16),
  "PCK_EDGE_TILE_FACE_SET_SELECT_enable": ("shared", 19, 8, 1),
  "PCK_EDGE_TILE_FACE_SET_SELECT_select": ("shared", 19, 0, 8),
  "SRCA_SET_Base": ("thread", 5, 0, 2),
  "SRCA_SET_SetOvrdWithAddr": ("thread", 5, 2, 1),
  "STACC_RELU_ApplyRelu": ("shared", 2, 2, 4),
  "STACC_RELU_ReluThreshold": ("shared", 2, 6, 16),
  "THCON_SEC0_REG1_Add_l1_dest_addr_offset": ("shared", 70, 1, 1),
  "THCON_SEC0_REG1_Add_tile_header_size": ("shared", 70, 22, 1),
  "THCON_SEC0_REG1_Dis_shared_exp_assembler": ("shared", 70, 12, 1),
  "THCON_SEC0_REG1_Disable_pack_zero_flags": ("shared", 70, 2, 1),
  "THCON_SEC0_REG1_Disable_zero_compress": ("shared", 70, 0, 1),
  "THCON_SEC0_REG1_Downsample_mask": ("shared", 71, 0, 16),
  "THCON_SEC0_REG1_Downsample_rate": ("shared", 71, 16, 3),
  "THCON_SEC0_REG1_Enable_out_fifo": ("shared", 70, 14, 1),
  "THCON_SEC0_REG1_Exp_section_size": ("shared", 68, 16, 16),
  "THCON_SEC0_REG1_Exp_threshold": ("shared", 71, 24, 8),
  "THCON_SEC0_REG1_Exp_threshold_en": ("shared", 71, 20, 1),
  "THCON_SEC0_REG1_In_data_format": ("shared", 70, 8, 4),
  "THCON_SEC0_REG1_L1_Dest_addr": ("shared", 69, 0, 32),
  "THCON_SEC0_REG1_L1_source_addr": ("shared", 70, 24, 8),
  "THCON_SEC0_REG1_Out_data_format": ("shared", 70, 4, 4),
  "THCON_SEC0_REG1_Pac_LF8_4b_exp": ("shared", 71, 23, 1),
  "THCON_SEC0_REG1_Pack_L1_Acc": ("shared", 71, 19, 1),
  "THCON_SEC0_REG1_Row_start_section_size": ("shared", 68, 0, 16),
  "THCON_SEC0_REG1_Source_interface_selection": ("shared", 70, 16, 1),
  "THCON_SEC0_REG1_Sub_l1_tile_header_size": ("shared", 70, 15, 1),
  "THCON_SEC0_REG1_Unp_LF8_4b_exp": ("shared", 71, 22, 1),
  "THCON_SEC0_REG2_Context_count": ("shared", 72, 6, 2),
  "THCON_SEC0_REG2_Disable_zero_compress_cntx0": ("shared", 73, 0, 1),
  "THCON_SEC0_REG2_Disable_zero_compress_cntx1": ("shared", 73, 1, 1),
  "THCON_SEC0_REG2_Disable_zero_compress_cntx2": ("shared", 73, 2, 1),
  "THCON_SEC0_REG2_Disable_zero_compress_cntx3": ("shared", 73, 3, 1),
  "THCON_SEC0_REG2_Disable_zero_compress_cntx4": ("shared", 73, 16, 1),
  "THCON_SEC0_REG2_Disable_zero_compress_cntx5": ("shared", 73, 17, 1),
  "THCON_SEC0_REG2_Disable_zero_compress_cntx6": ("shared", 73, 18, 1),
  "THCON_SEC0_REG2_Disable_zero_compress_cntx7": ("shared", 73, 19, 1),
  "THCON_SEC0_REG2_Force_shared_exp": ("shared", 73, 8, 1),
  "THCON_SEC0_REG2_Haloize_mode": ("shared", 72, 8, 1),
  "THCON_SEC0_REG2_Out_data_format": ("shared", 72, 0, 4),
  "THCON_SEC0_REG2_Ovrd_data_format": ("shared", 72, 14, 1),
  "THCON_SEC0_REG2_Shift_amount_cntx0": ("shared", 72, 16, 4),
  "THCON_SEC0_REG2_Shift_amount_cntx1": ("shared", 72, 20, 4),
  "THCON_SEC0_REG2_Shift_amount_cntx2": ("shared", 72, 24, 4),
  "THCON_SEC0_REG2_Shift_amount_cntx3": ("shared", 72, 28, 4),
  "THCON_SEC0_REG2_Throttle_mode": ("shared", 72, 4, 2),
  "THCON_SEC0_REG2_Tileize_mode": ("shared", 72, 9, 1),
  "THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd": ("shared", 72, 10, 1),
  "THCON_SEC0_REG2_Unpack_fifo_size": ("shared", 75, 0, 17),
  "THCON_SEC0_REG2_Unpack_if_sel_cntx0": ("shared", 73, 4, 1),
  "THCON_SEC0_REG2_Unpack_if_sel_cntx1": ("shared", 73, 5, 1),
  "THCON_SEC0_REG2_Unpack_if_sel_cntx2": ("shared", 73, 6, 1),
  "THCON_SEC0_REG2_Unpack_if_sel_cntx3": ("shared", 73, 7, 1),
  "THCON_SEC0_REG2_Unpack_if_sel_cntx4": ("shared", 73, 20, 1),
  "THCON_SEC0_REG2_Unpack_if_sel_cntx5": ("shared", 73, 21, 1),
  "THCON_SEC0_REG2_Unpack_if_sel_cntx6": ("shared", 73, 22, 1),
  "THCON_SEC0_REG2_Unpack_if_sel_cntx7": ("shared", 73, 23, 1),
  "THCON_SEC0_REG2_Unpack_limit_address": ("shared", 74, 0, 17),
  "THCON_SEC0_REG2_Upsample_and_interleave": ("shared", 72, 15, 1),
  "THCON_SEC0_REG2_Upsample_rate": ("shared", 72, 12, 2),
  "THCON_SEC0_REG3_Base_address": ("shared", 76, 0, 32),
  "THCON_SEC0_REG3_Base_cntx1_address": ("shared", 77, 0, 32),
  "THCON_SEC0_REG3_Base_cntx2_address": ("shared", 78, 0, 32),
  "THCON_SEC0_REG3_Base_cntx3_address": ("shared", 79, 0, 32),
  "THCON_SEC0_REG4_Base_cntx4_address": ("shared", 80, 0, 32),
  "THCON_SEC0_REG4_Base_cntx5_address": ("shared", 81, 0, 32),
  "THCON_SEC0_REG4_Base_cntx6_address": ("shared", 82, 0, 32),
  "THCON_SEC0_REG4_Base_cntx7_address": ("shared", 83, 0, 32),
  "THCON_SEC0_REG5_Dest_cntx0_address": ("shared", 84, 0, 16),
  "THCON_SEC0_REG5_Dest_cntx1_address": ("shared", 84, 16, 16),
  "THCON_SEC0_REG5_Dest_cntx2_address": ("shared", 85, 0, 16),
  "THCON_SEC0_REG5_Dest_cntx3_address": ("shared", 85, 16, 16),
  "THCON_SEC0_REG5_Tile_x_dim_cntx0": ("shared", 86, 0, 16),
  "THCON_SEC0_REG5_Tile_x_dim_cntx1": ("shared", 86, 16, 16),
  "THCON_SEC0_REG5_Tile_x_dim_cntx2": ("shared", 87, 0, 16),
  "THCON_SEC0_REG5_Tile_x_dim_cntx3": ("shared", 87, 16, 16),
  "THCON_SEC0_REG7_Offset_address": ("shared", 92, 0, 16),
  "THCON_SEC0_REG7_Offset_cntx1_address": ("shared", 93, 0, 16),
  "THCON_SEC0_REG7_Offset_cntx2_address": ("shared", 94, 0, 16),
  "THCON_SEC0_REG7_Offset_cntx3_address": ("shared", 95, 0, 16),
  "THCON_SEC0_REG7_Unpack_data_format_cntx0": ("shared", 92, 16, 4),
  "THCON_SEC0_REG7_Unpack_data_format_cntx1": ("shared", 93, 16, 4),
  "THCON_SEC0_REG7_Unpack_data_format_cntx2": ("shared", 94, 16, 4),
  "THCON_SEC0_REG7_Unpack_data_format_cntx3": ("shared", 95, 16, 4),
  "THCON_SEC0_REG7_Unpack_data_format_cntx4": ("shared", 92, 24, 4),
  "THCON_SEC0_REG7_Unpack_data_format_cntx5": ("shared", 93, 24, 4),
  "THCON_SEC0_REG7_Unpack_data_format_cntx6": ("shared", 94, 24, 4),
  "THCON_SEC0_REG7_Unpack_data_format_cntx7": ("shared", 95, 24, 4),
  "THCON_SEC0_REG7_Unpack_out_data_format_cntx0": ("shared", 92, 20, 4),
  "THCON_SEC0_REG7_Unpack_out_data_format_cntx1": ("shared", 93, 20, 4),
  "THCON_SEC0_REG7_Unpack_out_data_format_cntx2": ("shared", 94, 20, 4),
  "THCON_SEC0_REG7_Unpack_out_data_format_cntx3": ("shared", 95, 20, 4),
  "THCON_SEC0_REG7_Unpack_out_data_format_cntx4": ("shared", 92, 28, 4),
  "THCON_SEC0_REG7_Unpack_out_data_format_cntx5": ("shared", 93, 28, 4),
  "THCON_SEC0_REG7_Unpack_out_data_format_cntx6": ("shared", 94, 28, 4),
  "THCON_SEC0_REG7_Unpack_out_data_format_cntx7": ("shared", 95, 28, 4),
  "THCON_SEC0_REG8_Add_l1_dest_addr_offset": ("shared", 98, 1, 1),
  "THCON_SEC0_REG8_Add_tile_header_size": ("shared", 98, 17, 1),
  "THCON_SEC0_REG8_Dis_shared_exp_assembler": ("shared", 98, 12, 1),
  "THCON_SEC0_REG8_Disable_pack_zero_flags": ("shared", 98, 2, 1),
  "THCON_SEC0_REG8_Disable_zero_compress": ("shared", 98, 0, 1),
  "THCON_SEC0_REG8_Downsample_mask": ("shared", 99, 0, 16),
  "THCON_SEC0_REG8_Downsample_rate": ("shared", 99, 16, 3),
  "THCON_SEC0_REG8_Enable_out_fifo": ("shared", 98, 14, 1),
  "THCON_SEC0_REG8_Exp_section_size": ("shared", 96, 16, 16),
  "THCON_SEC0_REG8_Exp_threshold": ("shared", 99, 24, 8),
  "THCON_SEC0_REG8_Exp_threshold_en": ("shared", 99, 20, 1),
  "THCON_SEC0_REG8_In_data_format": ("shared", 98, 8, 4),
  "THCON_SEC0_REG8_L1_Dest_addr": ("shared", 97, 0, 32),
  "THCON_SEC0_REG8_L1_source_addr": ("shared", 98, 24, 8),
  "THCON_SEC0_REG8_Out_data_format": ("shared", 98, 4, 4),
  "THCON_SEC0_REG8_Pack_L1_Acc": ("shared", 99, 19, 1),
  "THCON_SEC0_REG8_Row_start_section_size": ("shared", 96, 0, 16),
  "THCON_SEC0_REG8_Source_interface_selection": ("shared", 98, 16, 1),
  "THCON_SEC0_REG8_Sub_l1_tile_header_size": ("shared", 98, 15, 1),
  "THCON_SEC1_REG1_Add_l1_dest_addr_offset": ("shared", 118, 1, 1),
  "THCON_SEC1_REG1_Add_tile_header_size": ("shared", 118, 22, 1),
  "THCON_SEC1_REG1_Dis_shared_exp_assembler": ("shared", 118, 12, 1),
  "THCON_SEC1_REG1_Disable_pack_zero_flags": ("shared", 118, 2, 1),
  "THCON_SEC1_REG1_Disable_zero_compress": ("shared", 118, 0, 1),
  "THCON_SEC1_REG1_Downsample_mask": ("shared", 119, 0, 16),
  "THCON_SEC1_REG1_Downsample_rate": ("shared", 119, 16, 3),
  "THCON_SEC1_REG1_Enable_out_fifo": ("shared", 118, 14, 1),
  "THCON_SEC1_REG1_Exp_section_size": ("shared", 116, 16, 16),
  "THCON_SEC1_REG1_Exp_threshold": ("shared", 119, 24, 8),
  "THCON_SEC1_REG1_Exp_threshold_en": ("shared", 119, 20, 1),
  "THCON_SEC1_REG1_In_data_format": ("shared", 118, 8, 4),
  "THCON_SEC1_REG1_L1_Dest_addr": ("shared", 117, 0, 32),
  "THCON_SEC1_REG1_L1_source_addr": ("shared", 118, 24, 8),
  "THCON_SEC1_REG1_Out_data_format": ("shared", 118, 4, 4),
  "THCON_SEC1_REG1_Pac_LF8_4b_exp": ("shared", 119, 23, 1),
  "THCON_SEC1_REG1_Pack_L1_Acc": ("shared", 119, 19, 1),
  "THCON_SEC1_REG1_Row_start_section_size": ("shared", 116, 0, 16),
  "THCON_SEC1_REG1_Source_interface_selection": ("shared", 118, 16, 1),
  "THCON_SEC1_REG1_Sub_l1_tile_header_size": ("shared", 118, 15, 1),
  "THCON_SEC1_REG1_Unp_LF8_4b_exp": ("shared", 119, 22, 1),
  "THCON_SEC1_REG2_Context_count": ("shared", 120, 6, 2),
  "THCON_SEC1_REG2_Disable_zero_compress_cntx0": ("shared", 121, 0, 1),
  "THCON_SEC1_REG2_Disable_zero_compress_cntx1": ("shared", 121, 1, 1),
  "THCON_SEC1_REG2_Force_shared_exp": ("shared", 121, 8, 1),
  "THCON_SEC1_REG2_Haloize_mode": ("shared", 120, 8, 1),
  "THCON_SEC1_REG2_Out_data_format": ("shared", 120, 0, 4),
  "THCON_SEC1_REG2_Ovrd_data_format": ("shared", 120, 14, 1),
  "THCON_SEC1_REG2_Shift_amount_cntx0": ("shared", 120, 16, 4),
  "THCON_SEC1_REG2_Shift_amount_cntx1": ("shared", 120, 20, 4),
  "THCON_SEC1_REG2_Throttle_mode": ("shared", 120, 4, 2),
  "THCON_SEC1_REG2_Tileize_mode": ("shared", 120, 9, 1),
  "THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd": ("shared", 120, 10, 1),
  "THCON_SEC1_REG2_Unpack_fifo_size": ("shared", 123, 0, 17),
  "THCON_SEC1_REG2_Unpack_if_sel_cntx0": ("shared", 121, 4, 1),
  "THCON_SEC1_REG2_Unpack_if_sel_cntx1": ("shared", 121, 5, 1),
  "THCON_SEC1_REG2_Unpack_limit_address": ("shared", 122, 0, 17),
  "THCON_SEC1_REG2_Upsample_and_interleave": ("shared", 120, 15, 1),
  "THCON_SEC1_REG2_Upsample_rate": ("shared", 120, 12, 2),
  "THCON_SEC1_REG3_Base_address": ("shared", 124, 0, 32),
  "THCON_SEC1_REG3_Base_cntx1_address": ("shared", 125, 0, 32),
  "THCON_SEC1_REG5_Dest_cntx0_address": ("shared", 132, 0, 16),
  "THCON_SEC1_REG5_Dest_cntx1_address": ("shared", 132, 16, 16),
  "THCON_SEC1_REG5_Tile_x_dim_cntx0": ("shared", 134, 0, 16),
  "THCON_SEC1_REG5_Tile_x_dim_cntx1": ("shared", 134, 16, 16),
  "THCON_SEC1_REG7_Offset_address": ("shared", 140, 0, 16),
  "THCON_SEC1_REG7_Offset_cntx1_address": ("shared", 141, 0, 16),
  "THCON_SEC1_REG7_Unpack_data_format_cntx0": ("shared", 140, 16, 4),
  "THCON_SEC1_REG7_Unpack_data_format_cntx1": ("shared", 141, 16, 4),
  "THCON_SEC1_REG7_Unpack_out_data_format_cntx0": ("shared", 140, 20, 4),
  "THCON_SEC1_REG7_Unpack_out_data_format_cntx1": ("shared", 141, 20, 4),
  "THCON_SEC1_REG8_Add_l1_dest_addr_offset": ("shared", 146, 1, 1),
  "THCON_SEC1_REG8_Add_tile_header_size": ("shared", 146, 17, 1),
  "THCON_SEC1_REG8_Dis_shared_exp_assembler": ("shared", 146, 12, 1),
  "THCON_SEC1_REG8_Disable_pack_zero_flags": ("shared", 146, 2, 1),
  "THCON_SEC1_REG8_Disable_zero_compress": ("shared", 146, 0, 1),
  "THCON_SEC1_REG8_Downsample_mask": ("shared", 147, 0, 16),
  "THCON_SEC1_REG8_Downsample_rate": ("shared", 147, 16, 3),
  "THCON_SEC1_REG8_Enable_out_fifo": ("shared", 146, 14, 1),
  "THCON_SEC1_REG8_Exp_section_size": ("shared", 144, 16, 16),
  "THCON_SEC1_REG8_Exp_threshold": ("shared", 147, 24, 8),
  "THCON_SEC1_REG8_Exp_threshold_en": ("shared", 147, 20, 1),
  "THCON_SEC1_REG8_In_data_format": ("shared", 146, 8, 4),
  "THCON_SEC1_REG8_L1_Dest_addr": ("shared", 145, 0, 32),
  "THCON_SEC1_REG8_L1_source_addr": ("shared", 146, 24, 8),
  "THCON_SEC1_REG8_Out_data_format": ("shared", 146, 4, 4),
  "THCON_SEC1_REG8_Pack_L1_Acc": ("shared", 147, 19, 1),
  "THCON_SEC1_REG8_Row_start_section_size": ("shared", 144, 0, 16),
  "THCON_SEC1_REG8_Source_interface_selection": ("shared", 146, 16, 1),
  "THCON_SEC1_REG8_Sub_l1_tile_header_size": ("shared", 146, 15, 1),
  "UNP0_ADDR_BASE_REG_0_Base": ("shared", 48, 0, 18),
  "UNP0_ADDR_BASE_REG_1_Base": ("shared", 49, 0, 18),
  "UNP0_ADDR_CTRL_XY_REG_0_Xstride": ("shared", 44, 0, 16),
  "UNP0_ADDR_CTRL_XY_REG_0_Ystride": ("shared", 44, 16, 16),
  "UNP0_ADDR_CTRL_XY_REG_1_Xstride": ("shared", 56, 0, 16),
  "UNP0_ADDR_CTRL_XY_REG_1_Ystride": ("shared", 56, 16, 16),
  "UNP0_ADDR_CTRL_ZW_REG_0_Wstride": ("shared", 45, 16, 16),
  "UNP0_ADDR_CTRL_ZW_REG_0_Zstride": ("shared", 45, 0, 16),
  "UNP0_ADDR_CTRL_ZW_REG_1_Wstride": ("shared", 57, 16, 16),
  "UNP0_ADDR_CTRL_ZW_REG_1_Zstride": ("shared", 57, 0, 16),
  "UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr": ("shared", 50, 8, 1),
  "UNP0_FORCED_SHARED_EXP_shared_exp": ("shared", 50, 0, 8),
  "UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val": ("shared", 53, 0, 32),
  "UNP1_ADDR_BASE_REG_0_Base": ("shared", 60, 0, 18),
  "UNP1_ADDR_BASE_REG_1_Base": ("shared", 61, 0, 18),
  "UNP1_ADDR_CTRL_XY_REG_0_Xstride": ("shared", 46, 0, 16),
  "UNP1_ADDR_CTRL_XY_REG_0_Ystride": ("shared", 46, 16, 16),
  "UNP1_ADDR_CTRL_XY_REG_1_Xstride": ("shared", 58, 0, 16),
  "UNP1_ADDR_CTRL_XY_REG_1_Ystride": ("shared", 58, 16, 16),
  "UNP1_ADDR_CTRL_ZW_REG_0_Wstride": ("shared", 47, 16, 16),
  "UNP1_ADDR_CTRL_ZW_REG_0_Zstride": ("shared", 47, 0, 16),
  "UNP1_ADDR_CTRL_ZW_REG_1_Wstride": ("shared", 59, 16, 16),
  "UNP1_ADDR_CTRL_ZW_REG_1_Zstride": ("shared", 59, 0, 16),
  "UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr": ("shared", 62, 8, 1),
  "UNP1_FORCED_SHARED_EXP_shared_exp": ("shared", 62, 0, 8),
  "UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val": ("shared", 63, 0, 32),
  "UNPACK_MISC_CFG_CfgContextCntInc_0": ("thread", 41, 5, 1),
  "UNPACK_MISC_CFG_CfgContextCntInc_1": ("thread", 41, 13, 1),
  "UNPACK_MISC_CFG_CfgContextCntReset_0": ("thread", 41, 4, 1),
  "UNPACK_MISC_CFG_CfgContextCntReset_1": ("thread", 41, 12, 1),
  "UNPACK_MISC_CFG_CfgContextOffset_0": ("thread", 41, 0, 4),
  "UNPACK_MISC_CFG_CfgContextOffset_1": ("thread", 41, 8, 4),
}
# --- end generated ---

REGS = {**{n: Loc(Space[s.upper()], a, sh, w) for n, (s, a, sh, w) in _CFG_DEFINES.items()}, **MANUAL_REGS}
