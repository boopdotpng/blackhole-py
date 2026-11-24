"""Blackhole Tensix configuration register map, structured by hardware engine with human-readable names.

Two separate register spaces exist inside each Tensix tile:
  - T (Space.THREAD): per-thread ThreadConfig bank (private to TRISC0/1/2, written whole-word via SETC16).
  - C (Space.CONFIG): shared Config bank (written via RMWCIB masked byte, WRCFG, or MMIO at TENSIX_CFG).

Calling any field produces a checked write descriptor: `PACK.l1_acc(1)`, `UNPACK[0].transpose(1)`.
Fields marked `UNCERTAIN:` have undocumented or unverified Blackhole silicon behavior.
"""
from __future__ import annotations
from dataclasses import dataclass
from .field import Field, Space

T, C = Space.THREAD, Space.CONFIG


def _t(word: int, shift: int, width: int, name: str) -> Field: return Field(T, word, shift, width, name)
def _c(word: int, shift: int, width: int, name: str) -> Field: return Field(C, word, shift, width, name)


# ============================================================================================================
# 1. Per-Thread Config (Space.THREAD, words 0..67, written via SETC16)
# ============================================================================================================

@dataclass(frozen=True)
class MathAddrMod:
  """One of 8 math RWC address-modifier slots (0..7). Slot 0 is conventionally kept all-zero (`hold`).

  Counters are ordered `(srca, srcb, dst, fidelity)` for `incr` and `clear`, and `(srca, srcb, dst)` for `cr`.
  `words` are the 3 ThreadConfig words `(AB, AB2, DST)` rewritten together via SETC16.
  """
  srca_incr: Field; srca_cr: Field; srca_clear: Field; srca_hi_incr: Field
  srcb_incr: Field; srcb_cr: Field; srcb_clear: Field; srcb_hi_incr: Field
  dst_incr: Field;  dst_cr: Field;  dst_clear: Field;  dst_c_to_cr: Field
  fidelity_incr: Field; fidelity_clear: Field
  words: tuple[int, int, int]

  @property
  def incr(self) -> tuple[Field, Field, Field, Field]:
    return (self.srca_incr, self.srcb_incr, self.dst_incr, self.fidelity_incr)

  @property
  def clear(self) -> tuple[Field, Field, Field, Field]:
    return (self.srca_clear, self.srcb_clear, self.dst_clear, self.fidelity_clear)

  @property
  def cr(self) -> tuple[Field, Field, Field]:
    return (self.srca_cr, self.srcb_cr, self.dst_cr)

  @staticmethod
  def slot(s: int) -> MathAddrMod:
    ab, ab2, dst = 12 + s, 20 + s, 28 + s
    return MathAddrMod(
      srca_incr=_t(ab, 0, 6, f"addr_mod[{s}].srca_incr"),
      srca_cr=_t(ab, 6, 1, f"addr_mod[{s}].srca_cr"),
      srca_clear=_t(ab, 7, 1, f"addr_mod[{s}].srca_clear"),
      srca_hi_incr=_t(ab2, 0, 1, f"addr_mod[{s}].srca_hi_incr"),    # UNCERTAIN: high bit of 7-bit SrcA increment?
      srcb_incr=_t(ab, 8, 6, f"addr_mod[{s}].srcb_incr"),
      srcb_cr=_t(ab, 14, 1, f"addr_mod[{s}].srcb_cr"),
      srcb_clear=_t(ab, 15, 1, f"addr_mod[{s}].srcb_clear"),
      srcb_hi_incr=_t(ab2, 1, 1, f"addr_mod[{s}].srcb_hi_incr"),    # UNCERTAIN: high bit of 7-bit SrcB increment?
      dst_incr=_t(dst, 0, 10, f"addr_mod[{s}].dst_incr"),
      dst_cr=_t(dst, 10, 1, f"addr_mod[{s}].dst_cr"),
      dst_clear=_t(dst, 11, 1, f"addr_mod[{s}].dst_clear"),
      dst_c_to_cr=_t(dst, 12, 1, f"addr_mod[{s}].dst_c_to_cr"),
      fidelity_incr=_t(dst, 13, 2, f"addr_mod[{s}].fidelity_incr"),
      fidelity_clear=_t(dst, 15, 1, f"addr_mod[{s}].fidelity_clear"),
      words=(ab, ab2, dst),
    )


@dataclass(frozen=True)
class PackAddrMod:
  """One of 4 packer ADC address-modifier slots (0..3, ThreadConfig words 37..40)."""
  ysrc_incr: Field; ysrc_cr: Field; ysrc_clear: Field
  ydst_incr: Field; ydst_cr: Field; ydst_clear: Field
  zsrc_incr: Field; zsrc_clear: Field
  zdst_incr: Field; zdst_clear: Field

  @staticmethod
  def slot(s: int) -> PackAddrMod:
    w = 37 + s
    return PackAddrMod(
      ysrc_incr=_t(w, 0, 4, f"pack_addr_mod[{s}].ysrc_incr"),
      ysrc_cr=_t(w, 4, 1, f"pack_addr_mod[{s}].ysrc_cr"),
      ysrc_clear=_t(w, 5, 1, f"pack_addr_mod[{s}].ysrc_clear"),
      ydst_incr=_t(w, 6, 4, f"pack_addr_mod[{s}].ydst_incr"),
      ydst_cr=_t(w, 10, 1, f"pack_addr_mod[{s}].ydst_cr"),
      ydst_clear=_t(w, 11, 1, f"pack_addr_mod[{s}].ydst_clear"),
      zsrc_incr=_t(w, 12, 1, f"pack_addr_mod[{s}].zsrc_incr"),
      zsrc_clear=_t(w, 13, 1, f"pack_addr_mod[{s}].zsrc_clear"),
      zdst_incr=_t(w, 14, 1, f"pack_addr_mod[{s}].zdst_incr"),
      zdst_clear=_t(w, 15, 1, f"pack_addr_mod[{s}].zdst_clear"),
    )


@dataclass(frozen=True)
class ThreadCfg:
  """Per-thread Tensix control registers (ThreadConfig words 0..67)."""
  cfg_bank: Field               # active shared Config bank (0 or 1)
  dst_offset: Field             # base Dst row offset for math/SFPU (double-buffer half select)
  disable_implied_srca: Field   # UNCERTAIN: disables implied SrcA format vs ALU_FORMAT_SPEC
  disable_implied_srcb: Field   # UNCERTAIN: disables implied SrcB format vs ALU_FORMAT_SPEC
  sfpu_dst_fmt_en: Field        # enable SFPU Dst format override (set 1 for FP32 Dst)
  sfpu_dst_fmt: Field           # SFPU Dst DataFormat when sfpu_dst_fmt_en=1
  srca_bank: Field              # UNCERTAIN: manual SrcA bank select (0..1)
  srca_override_addr: Field     # 1 = override SrcA/Dst target with unpacker address (toggle around unpack_to_dst)
  srcb_bank: Field              # UNCERTAIN: manual SrcB bank select (0..1)
  disable_clr_dvalid_a: Field   # UNCERTAIN: suppresses SETRWC/CLEARDVALID clearing SrcA dvalid?
  disable_clr_dvalid_b: Field   # UNCERTAIN: suppresses SETRWC/CLEARDVALID clearing SrcB dvalid?
  scbd_32b_en: Field            # UNCERTAIN: 32-bit scoreboard bank mask mode (math)
  pack_scbd_32b_en: Field       # UNCERTAIN: 32-bit scoreboard bank mask mode (pack)
  unpack_scbd_32b_en: Field     # UNCERTAIN: 32-bit scoreboard bank mask mode (unpack)
  fidelity_phase: Field         # initial FPU fidelity phase (0..3)
  sfpu_stack_incr: Field        # UNCERTAIN: SFPU predicate stack auto-increment
  unpack_ctx_offset: tuple[Field, Field]  # per unpacker (0/1) context offset
  unpack_ctx_reset: tuple[Field, Field]   # per unpacker (0/1) reset context counter
  unpack_ctx_inc: tuple[Field, Field]     # per unpacker (0/1) increment context counter
  fp16a_force_en: Field         # UNCERTAIN: forces FP16A mode in FPU
  addr_mod: tuple[MathAddrMod, ...]
  pack_addr_mod: tuple[PackAddrMod, ...]


THREAD = ThreadCfg(
  cfg_bank=_t(0, 0, 1, "thread.cfg_bank"),
  dst_offset=_t(1, 0, 12, "thread.dst_offset"),
  disable_implied_srca=_t(2, 0, 1, "thread.disable_implied_srca"),
  disable_implied_srcb=_t(3, 0, 1, "thread.disable_implied_srcb"),
  sfpu_dst_fmt_en=_t(4, 0, 1, "thread.sfpu_dst_fmt_en"),
  sfpu_dst_fmt=_t(4, 1, 4, "thread.sfpu_dst_fmt"),
  srca_bank=_t(5, 0, 2, "thread.srca_bank"),
  srca_override_addr=_t(5, 2, 1, "thread.srca_override_addr"),
  srcb_bank=_t(6, 0, 2, "thread.srcb_bank"),
  disable_clr_dvalid_a=_t(7, 0, 1, "thread.disable_clr_dvalid_a"),
  disable_clr_dvalid_b=_t(7, 1, 1, "thread.disable_clr_dvalid_b"),
  scbd_32b_en=_t(8, 0, 1, "thread.scbd_32b_en"),
  pack_scbd_32b_en=_t(9, 0, 1, "thread.pack_scbd_32b_en"),
  unpack_scbd_32b_en=_t(10, 0, 1, "thread.unpack_scbd_32b_en"),
  fidelity_phase=_t(11, 0, 2, "thread.fidelity_phase"),
  sfpu_stack_incr=_t(36, 0, 10, "thread.sfpu_stack_incr"),
  unpack_ctx_offset=(_t(41, 0, 4, "thread.unpack_ctx_offset[0]"), _t(41, 8, 4, "thread.unpack_ctx_offset[1]")),
  unpack_ctx_reset=(_t(41, 4, 1, "thread.unpack_ctx_reset[0]"), _t(41, 12, 1, "thread.unpack_ctx_reset[1]")),
  unpack_ctx_inc=(_t(41, 5, 1, "thread.unpack_ctx_inc[0]"), _t(41, 13, 1, "thread.unpack_ctx_inc[1]")),
  fp16a_force_en=_t(55, 0, 1, "thread.fp16a_force_en"),
  addr_mod=tuple(MathAddrMod.slot(s) for s in range(8)),
  pack_addr_mod=tuple(PackAddrMod.slot(s) for s in range(4)),
)


# ============================================================================================================
# 2. Math / FPU / Dst Config (Space.CONFIG, words 0..8)
# ============================================================================================================

@dataclass(frozen=True)
class MathCfg:
  """Shared FPU / SFPU format, rounding, accumulation, and ReLU configuration."""
  # Legacy/override format spec (word 0) — UNCERTAIN: when override=1 takes precedence over REG0/1/2 below
  srca_fmt_ovrd_val: Field; srca_fmt_ovrd: Field
  srcb_fmt_ovrd_val: Field; srcb_fmt_ovrd: Field
  dst_fmt_ovrd_val: Field;  dst_fmt_ovrd: Field
  # Rounding modes (word 1) — UNCERTAIN: exact stochastic rounding behavior & PRNG interaction
  fpu_srnd_en: Field
  gasket_srnd_en: Field
  packer_srnd_en: Field
  bfp8_hf: Field                # UNCERTAIN: BFP8 high-fidelity rounding mode
  # Active ALU formats & accumulation control (word 1)
  srca_unsigned: Field          # UNCERTAIN: unsigned SrcA interpretation for int math
  srcb_unsigned: Field          # UNCERTAIN: unsigned SrcB interpretation for int math
  srca_fmt: Field               # Math engine's view of SrcA DataFormat
  srcb_fmt: Field               # Math engine's view of SrcB DataFormat
  dst_fmt: Field                # Dst accumulator DataFormat (e.g. FLOAT32 or FLOAT16_B)
  fp32_dst_acc: Field           # 1 = 32-bit FP32 Dst accumulation (8 tiles per half)
  sfpu_fp32_acc: Field          # 1 = SFPU reads/writes 32-bit FP32 Dst
  int8_math_en: Field           # UNCERTAIN: enables INT8/INT32 FPU math path
  # Zero flags & hardware ReLU (word 2)
  zero_flag_dis_src: Field      # UNCERTAIN: disables Src zero-flag optimization
  zero_flag_dis_dst: Field      # UNCERTAIN: disables Dst zero-flag optimization
  relu_mode: Field              # UNCERTAIN: hardware ReLU mode enum (STACC_RELU_ApplyRelu)
  relu_threshold: Field         # UNCERTAIN: 16-bit threshold format (BF16 vs FP16 vs int)
  # Dst base / state reset (words 4..7)
  state_reset_en: Field
  dst_offset_en: Field          # UNCERTAIN: global enable vs ThreadCfg.dst_offset
  dst_regw_base: Field          # UNCERTAIN: Dst register-write base offset
  dst_sp_base: Field            # UNCERTAIN: Dst spill/scratchpad base offset


MATH = MathCfg(
  srca_fmt_ovrd_val=_c(0, 0, 4, "math.srca_fmt_ovrd_val"),
  srca_fmt_ovrd=_c(0, 4, 1, "math.srca_fmt_ovrd"),
  srcb_fmt_ovrd_val=_c(0, 5, 4, "math.srcb_fmt_ovrd_val"),
  srcb_fmt_ovrd=_c(0, 9, 1, "math.srcb_fmt_ovrd"),
  dst_fmt_ovrd_val=_c(0, 10, 4, "math.dst_fmt_ovrd_val"),
  dst_fmt_ovrd=_c(0, 14, 1, "math.dst_fmt_ovrd"),
  fpu_srnd_en=_c(1, 0, 1, "math.fpu_srnd_en"),
  gasket_srnd_en=_c(1, 1, 1, "math.gasket_srnd_en"),
  packer_srnd_en=_c(1, 2, 1, "math.packer_srnd_en"),
  bfp8_hf=_c(1, 14, 1, "math.bfp8_hf"),
  srca_unsigned=_c(1, 15, 1, "math.srca_unsigned"),
  srcb_unsigned=_c(1, 16, 1, "math.srcb_unsigned"),
  srca_fmt=_c(1, 17, 4, "math.srca_fmt"),
  srcb_fmt=_c(1, 21, 4, "math.srcb_fmt"),
  dst_fmt=_c(1, 25, 4, "math.dst_fmt"),
  fp32_dst_acc=_c(1, 29, 1, "math.fp32_dst_acc"),
  sfpu_fp32_acc=_c(1, 30, 1, "math.sfpu_fp32_acc"),
  int8_math_en=_c(1, 31, 1, "math.int8_math_en"),
  zero_flag_dis_src=_c(2, 0, 1, "math.zero_flag_dis_src"),
  zero_flag_dis_dst=_c(2, 1, 1, "math.zero_flag_dis_dst"),
  relu_mode=_c(2, 2, 4, "math.relu_mode"),
  relu_threshold=_c(2, 6, 16, "math.relu_threshold"),
  state_reset_en=_c(4, 0, 1, "math.state_reset_en"),
  dst_offset_en=_c(5, 0, 1, "math.dst_offset_en"),
  dst_regw_base=_c(6, 0, 16, "math.dst_regw_base"),
  dst_sp_base=_c(7, 0, 16, "math.dst_sp_base"),
)


# ============================================================================================================
# 3. Unpacker 0 (SrcA) & Unpacker 1 (SrcB) Config (Space.CONFIG, words 44..63 & THCON 64..159)
# ============================================================================================================

UNPACK_A_CONTEXTS, UNPACK_B_CONTEXTS = 8, 2  # Unpacker B on contexts 2..7 hangs the card


@dataclass(frozen=True)
class UnpackerCfg:
  """Configuration for Unpacker 0 (SrcA) or Unpacker 1 (SrcB)."""
  # TileDescriptor (THCON REG0, 128-bit)
  in_fmt: Field                 # L1 source DataFormat
  uncompressed: Field           # UNCERTAIN: 1 = tile has no zero-compression header
  blobs_per_xy_plane: Field     # UNCERTAIN: multi-blob tile descriptor count
  x_dim: Field                  # datums per row of a face (typically 16 or 1024 for flat unpack)
  y_dim: Field                  # rows per face (typically 16 or 1)
  z_dim: Field                  # faces per tile (1..4)
  w_dim: Field                  # tiles (typically 1)
  # Format & mode controls (THCON REG1/REG2)
  out_fmt: Field                # SrcA/SrcB (or Dst) output DataFormat
  lf8_e4m3: Field               # 1 = LF8 input is E4M3 (4-bit exp), 0 = E5M2
  transpose: Field              # 1 = free X/Y face transpose (haloize_mode, Unpacker 0 only!)
  tileize_mode: Field           # UNCERTAIN: hardware row-major -> face tileize during unpack
  upsample_rate: Field          # UNCERTAIN: hardware zero-insertion upsampling rate (0..3)
  upsample_interleave: Field    # UNCERTAIN: interleave mode for hardware upsampling
  throttle_mode: Field          # UNCERTAIN: unpacker pipeline throttle (0..3)
  override_fmt: Field           # 1 = use per-context formats in REG7 instead of REG0/REG2
  force_shared_exp: Field       # 1 = replace BFP shared exponent with `shared_exp`
  shared_exp: Field             # 8-bit forced shared exponent
  add_dst_addr_cntr: Field      # 1 = add ADC counter to Dst target (used for unpack-to-Dst)
  # Strides (UNP{0,1}_ADDR_CTRL)
  src_x_stride: Field; src_y_stride: Field; src_z_stride: Field; src_w_stride: Field   # L1-side strides (REG_0)
  row_stride: Field             # Src/Dst Y stride in bytes (REG_1_Ystride)
  face_stride: Field            # Src/Dst Z stride in bytes (REG_1_Zstride)
  # Paired ALU format in MathCfg
  alu_fmt: Field
  # Multi-context controls (contexts 0..7 for Unpacker 0, 0..1 for Unpacker 1)
  context_count: Field          # active contexts - 1 (when context_count_en=1)
  context_count_en: Field
  context_reset: Field          # Space.THREAD: pulse to reset context counter to 0
  disable_zero_compress: tuple[Field, ...]   # per context 0..7: 1 = disable zero decompression
  unpack_to_dst: tuple[Field, ...]           # per context 0..7: 1 = route Unpacker 0 directly to FP32 Dst
  context_in_fmt: tuple[Field, ...]          # per context: override L1 input format
  context_out_fmt: tuple[Field, ...]         # per context: override Src/Dst output format
  base_addr: tuple[Field, ...]               # per context: L1 address in 16-byte words, minus 1
  dst_addr: tuple[Field, ...]                # per context 0..3: target row offset (Unpacker 0)
  tile_x_dim: tuple[Field, ...]              # per context 0..3: per-context X dim (Unpacker 0)

  @staticmethod
  def unit(i: int) -> UnpackerCfg:
    sec = 64 + 48 * i                        # THCON_SEC0 = 64, THCON_SEC1 = 112
    xy0, zw0 = (44, 45) if i == 0 else (46, 47)
    xy1, zw1 = (56, 57) if i == 0 else (58, 59)
    exp_w = 50 if i == 0 else 62
    n_ctx = UNPACK_B_CONTEXTS if i else UNPACK_A_CONTEXTS
    p = f"unpack[{i}]"
    return UnpackerCfg(
      in_fmt=_c(sec + 0, 0, 4, f"{p}.in_fmt"),
      uncompressed=_c(sec + 0, 4, 1, f"{p}.uncompressed"),
      blobs_per_xy_plane=_c(sec + 0, 8, 4, f"{p}.blobs_per_xy_plane"),
      x_dim=_c(sec + 0, 16, 16, f"{p}.x_dim"),
      y_dim=_c(sec + 1, 0, 16, f"{p}.y_dim"),
      z_dim=_c(sec + 1, 16, 16, f"{p}.z_dim"),
      w_dim=_c(sec + 2, 0, 16, f"{p}.w_dim"),
      out_fmt=_c(sec + 8, 0, 4, f"{p}.out_fmt"),
      lf8_e4m3=_c(sec + 7, 22, 1, f"{p}.lf8_e4m3"),
      transpose=_c(sec + 8, 8, 1, f"{p}.transpose"),
      tileize_mode=_c(sec + 8, 9, 1, f"{p}.tileize_mode"),
      upsample_rate=_c(sec + 8, 12, 2, f"{p}.upsample_rate"),
      upsample_interleave=_c(sec + 8, 15, 1, f"{p}.upsample_interleave"),
      throttle_mode=_c(sec + 8, 4, 2, f"{p}.throttle_mode"),
      override_fmt=_c(sec + 8, 14, 1, f"{p}.override_fmt"),
      force_shared_exp=_c(sec + 9, 8, 1, f"{p}.force_shared_exp"),
      shared_exp=_c(exp_w, 0, 8, f"{p}.shared_exp"),
      add_dst_addr_cntr=_c(exp_w, 8, 1, f"{p}.add_dst_addr_cntr"),
      src_x_stride=_c(xy0, 0, 16, f"{p}.src_x_stride"),
      src_y_stride=_c(xy0, 16, 16, f"{p}.src_y_stride"),
      src_z_stride=_c(zw0, 0, 16, f"{p}.src_z_stride"),
      src_w_stride=_c(zw0, 16, 16, f"{p}.src_w_stride"),
      row_stride=_c(xy1, 16, 16, f"{p}.row_stride"),
      face_stride=_c(zw1, 0, 16, f"{p}.face_stride"),
      alu_fmt=MATH.srcb_fmt if i else MATH.srca_fmt,
      context_count=_c(sec + 9, 9, 3, f"{p}.context_count"),
      context_count_en=_c(sec + 9, 12, 1, f"{p}.context_count_en"),
      context_reset=THREAD.unpack_ctx_reset[i],
      disable_zero_compress=tuple(_c(sec + 9, (c & 3) + (c >> 2) * 16, 1, f"{p}.disable_zero_compress[{c}]") for c in range(8)),
      unpack_to_dst=tuple(_c(sec + 9, 4 + (c & 3) + (c >> 2) * 16, 1, f"{p}.unpack_to_dst[{c}]") for c in range(8)),
      context_in_fmt=tuple(_c(sec + 28 + (c & 3), 16 + (c >> 2) * 8, 4, f"{p}.context_in_fmt[{c}]") for c in range(n_ctx)),
      context_out_fmt=tuple(_c(sec + 28 + (c & 3), 20 + (c >> 2) * 8, 4, f"{p}.context_out_fmt[{c}]") for c in range(n_ctx)),
      base_addr=tuple(_c(sec + 12 + c, 0, 32, f"{p}.base_addr[{c}]") for c in range(n_ctx)),
      dst_addr=tuple(_c(sec + 20 + (c >> 1), (c & 1) * 16, 16, f"{p}.dst_addr[{c}]") for c in range(4)),
      tile_x_dim=tuple(_c(sec + 22 + (c >> 1), (c & 1) * 16, 16, f"{p}.tile_x_dim[{c}]") for c in range(4)),
    )


UNPACK = (UnpackerCfg.unit(0), UnpackerCfg.unit(1))


# ============================================================================================================
# 4. Packer 0 Config (Space.CONFIG, words 12..40 & THCON_SEC0 REG1 words 68..71)
# ============================================================================================================

@dataclass(frozen=True)
class PackerCfg:
  """Configuration for Packer 0 (Dst -> L1, driven by TRISC2)."""
  # THCON_SEC0_REG1 (words 68..71)
  row_start_section_size: Field  # UNCERTAIN: zero-compression row-start header size
  exp_section_size: Field        # BFP shared-exponent section size in 16-byte words (0 for BF16/FP32)
  l1_dest_addr: Field            # L1 destination address in 16-byte words, minus 1 (usually written via WRCFG)
  disable_zero_compress: Field   # 1 = disable zero compression (always set 1 for dense tiles)
  add_l1_dest_offset: Field      # UNCERTAIN: adds ADC L1 offset to l1_dest_addr
  out_fmt: Field                 # L1 output DataFormat
  in_fmt: Field                  # Dst input DataFormat
  lf8_e4m3: Field                # 1 = LF8 output is E4M3 (4-bit exp), 0 = E5M2
  l1_acc: Field                  # 1 = accumulate packed FP32/BF16 output into existing L1 tile (Pack_L1_Acc!)
  downsample_mask: Field         # UNCERTAIN: hardware column downsample bitmask
  downsample_rate: Field         # UNCERTAIN: hardware downsample rate
  # Dst read format control (word 18)
  read_32b: Field                # 1 = read 32-bit FP32/INT32 from Dst
  read_unsigned: Field           # UNCERTAIN: unsigned integer Dst read
  read_int8: Field               # UNCERTAIN: INT8 Dst read
  round_10b_mant: Field          # 1 = round mantissa to 10 bits when packing from FP16
  # Dst-side strides (words 12..13) & L1-side strides (words 14..15)
  x_stride: Field; y_stride: Field; z_stride: Field; w_stride: Field           # Dst strides (bytes)
  l1_x_stride: Field; l1_y_stride: Field; l1_z_stride: Field; l1_w_stride: Field  # UNCERTAIN: L1-side strides (REG_1)
  # Edge masks & tile row/face set mappings (words 19..27, 36..39)
  face_set_select: Field         # UNCERTAIN: multi-face edge mask selection
  face_set_en: Field             # UNCERTAIN: enables per-face edge mask lookup
  edge_mode: Field               # UNCERTAIN: 0 = row-set edge mask mode, 1 = alt mode
  row_set_select: Field          # UNCERTAIN: row-set selector for edge masks
  edge_mask: tuple[Field, ...]   # 4 x 16-bit datum write-enable masks (SEC0..3; 0xFFFF = all 16 datums)
  # Per-plane / per-tile pack counters (word 28, SEC0)
  pack_per_xy_plane: Field       # datums per XY plane (0 = full 16x16 face)
  pack_reads_per_xy_plane: Field # Dst row reads per XY plane (16 for full face)
  pack_xys_per_tile: Field       # XY faces per tile
  pack_yz_transposed: Field      # UNCERTAIN: transposes Y/Z during pack
  # Global Dst target offsets for packer sections 0..3 (words 180..183)
  dst_target_offset: tuple[Field, ...]  # UNCERTAIN: packer Dst base offset vs PCK_DEST_RD_CTRL


PACK = PackerCfg(
  row_start_section_size=_c(68, 0, 16, "pack.row_start_section_size"),
  exp_section_size=_c(68, 16, 16, "pack.exp_section_size"),
  l1_dest_addr=_c(69, 0, 32, "pack.l1_dest_addr"),
  disable_zero_compress=_c(70, 0, 1, "pack.disable_zero_compress"),
  add_l1_dest_offset=_c(70, 1, 1, "pack.add_l1_dest_offset"),
  out_fmt=_c(70, 4, 4, "pack.out_fmt"),
  in_fmt=_c(70, 8, 4, "pack.in_fmt"),
  lf8_e4m3=_c(71, 23, 1, "pack.lf8_e4m3"),
  l1_acc=_c(71, 19, 1, "pack.l1_acc"),
  downsample_mask=_c(71, 0, 16, "pack.downsample_mask"),
  downsample_rate=_c(71, 16, 3, "pack.downsample_rate"),
  read_32b=_c(18, 0, 1, "pack.read_32b"),
  read_unsigned=_c(18, 1, 1, "pack.read_unsigned"),
  read_int8=_c(18, 2, 1, "pack.read_int8"),
  round_10b_mant=_c(18, 3, 1, "pack.round_10b_mant"),
  x_stride=_c(12, 0, 16, "pack.x_stride"),
  y_stride=_c(12, 16, 16, "pack.y_stride"),
  z_stride=_c(13, 0, 16, "pack.z_stride"),
  w_stride=_c(13, 16, 16, "pack.w_stride"),
  l1_x_stride=_c(14, 0, 16, "pack.l1_x_stride"),
  l1_y_stride=_c(14, 16, 16, "pack.l1_y_stride"),
  l1_z_stride=_c(15, 0, 16, "pack.l1_z_stride"),
  l1_w_stride=_c(15, 16, 16, "pack.l1_w_stride"),
  face_set_select=_c(19, 0, 8, "pack.face_set_select"),
  face_set_en=_c(19, 8, 1, "pack.face_set_en"),
  edge_mode=_c(24, 16, 1, "pack.edge_mode"),
  row_set_select=_c(24, 17, 8, "pack.row_set_select"),
  edge_mask=tuple(_c(24 + s, 0, 16, f"pack.edge_mask[{s}]") for s in range(4)),
  pack_per_xy_plane=_c(28, 0, 8, "pack.pack_per_xy_plane"),
  pack_reads_per_xy_plane=_c(28, 8, 8, "pack.pack_reads_per_xy_plane"),
  pack_xys_per_tile=_c(28, 16, 7, "pack.pack_xys_per_tile"),
  pack_yz_transposed=_c(28, 23, 1, "pack.pack_yz_transposed"),
  dst_target_offset=tuple(_c(180 + s, 0, 12, f"pack.dst_target_offset[{s}]") for s in range(4)),
)


# ============================================================================================================
# 5. Global Tile Control & Chicken Bits (Space.CONFIG, words 184..222)
# ============================================================================================================

@dataclass(frozen=True)
class GlobalCfg:
  """Tile-wide RISC control, PRNG, and low-level Tensix bank/scoreboard chicken bits."""
  icache_invalidate: Field         # 5-bit mask: bit0=BRISC, bit1..3=TRISC0..2, bit4=NCRISC
  prng_seed: Field                 # UNCERTAIN: 32-bit LFSR seed for stochastic rounding
  prefetch_trisc: Field            # 3-bit mask enabling TRISC0..2 instruction prefetch
  prefetch_brisc: Field            # enable BRISC instruction prefetch
  prefetch_ncrisc: Field           # enable NCRISC instruction prefetch
  prefetch_max_req: Field          # max outstanding instruction prefetch requests (boot sets 0x11F total)
  # Dst / Src access modes (words 220..222)
  dst_swizzle_32b: Field           # UNCERTAIN: 32-bit Dst lane swizzle mode
  dst_remap_addrs: Field           # UNCERTAIN: Dst address remapping mode
  zeroacc_abs_tile_mode: Field     # UNCERTAIN: whether ZEROACC uses absolute tile index or ignores dst_offset
  srca_single_bank: Field          # UNCERTAIN: lets math view both SrcA banks as one contiguous 128-row bank?
  srcb_single_bank: Field          # UNCERTAIN: lets math view both SrcB banks as one contiguous 128-row bank?
  disable_contig_dvalid_a: Field   # UNCERTAIN: disables contiguous SrcA dvalid phase handling
  disable_contig_dvalid_b: Field   # UNCERTAIN: disables contiguous SrcB dvalid phase handling
  sfpu_scbd_disable: Field         # UNCERTAIN: disables SFPU hardware scoreboard stalling


GLOBAL = GlobalCfg(
  icache_invalidate=_c(185, 0, 5, "global.icache_invalidate"),
  prng_seed=_c(186, 0, 32, "global.prng_seed"),
  prefetch_trisc=_c(208, 0, 3, "global.prefetch_trisc"),
  prefetch_brisc=_c(208, 3, 1, "global.prefetch_brisc"),
  prefetch_ncrisc=_c(208, 4, 1, "global.prefetch_ncrisc"),
  prefetch_max_req=_c(208, 5, 8, "global.prefetch_max_req"),
  dst_swizzle_32b=_c(220, 0, 1, "global.dst_swizzle_32b"),
  dst_remap_addrs=_c(220, 1, 1, "global.dst_remap_addrs"),
  zeroacc_abs_tile_mode=_c(220, 3, 1, "global.zeroacc_abs_tile_mode"),
  srca_single_bank=_c(221, 0, 1, "global.srca_single_bank"),
  srcb_single_bank=_c(221, 1, 1, "global.srcb_single_bank"),
  disable_contig_dvalid_a=_c(221, 2, 1, "global.disable_contig_dvalid_a"),
  disable_contig_dvalid_b=_c(221, 3, 1, "global.disable_contig_dvalid_b"),
  sfpu_scbd_disable=_c(222, 0, 1, "global.sfpu_scbd_disable"),
)

# Convenience aliases matching hw.py
ADDR_MOD = THREAD.addr_mod
PACK_ADDR_MOD = THREAD.pack_addr_mod
