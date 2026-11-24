"""Blackhole Tensix configuration fields the compiler writes, grouped by hardware engine with human-readable names.

Two separate register spaces exist inside each Tensix tile:
  - T (Space.THREAD): per-thread ThreadConfig bank (private to TRISC0/1/2, written whole-word via SETC16).
  - C (Space.CONFIG): shared Config bank (written via RMWCIB masked byte, WRCFG, or MMIO at TENSIX_CFG).

Calling any field produces a checked write descriptor: `PACK.ctx[0].l1_acc(1)`, `UNPACK[0].transpose(1)`.

This is a subset of tt-metal's blackhole/cfg_defines.h: the fields ttrv programs today, plus the ones worth lowering
to later. Comments say what the silicon does, as measured on a p150 by the cfgprobe runs of 2026-11-23 or as
exercised by every ttrv kernel. Fields that were probed and left out (no effect, or nothing a lowering would want)
are listed at the bottom so their bits stay known.

DataFormat codes are 4 bits wide in every format field. Code 30 (UInt8) does not fit and wedged a core.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class Space(Enum):
  THREAD = "ThreadConfig"  # per Tensix thread, written whole-word with SETC16
  CONFIG = "Config"        # shared, written with RMWCIB (masked byte), WRCFG, or MMIO at TENSIX_CFG


class Field(NamedTuple):
  space: Space
  word: int
  shift: int
  width: int
  name: str

  @property
  def mask(self): return ((1 << self.width) - 1) << self.shift

  def __call__(self, value) -> "Set":
    value = int(value)
    if not 0 <= value < 1 << self.width:
      raise ValueError(f"{self.name}: {value} does not fit {self.width} bits")
    if self.width > 32:
      raise ValueError(f"{self.name} spans several words; write its parts")
    return Set(self, value)


class Set(NamedTuple):
  field: Field
  value: int

  @property
  def bits(self): return self.value << self.field.shift


def words(sets) -> dict[int, int]:
  out = {}
  for s in sets:
    out[s.field.word] = out.get(s.field.word, 0) | s.bits
  return out


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
  `words` are the 2 ThreadConfig words `(AB, DST)` a slot is programmed through; SETC16 replaces a whole word.
  The slot's third word (AB2, 20 + slot) only holds the +64 bit of each Src increment. That bit matters only when
  both Src banks are merged into one 128-row bank, which nothing here does, so it stays 0 from boot.
  """
  srca_incr: Field; srca_cr: Field; srca_clear: Field
  srcb_incr: Field; srcb_cr: Field; srcb_clear: Field
  dst_incr: Field;  dst_cr: Field;  dst_clear: Field;  dst_c_to_cr: Field
  fidelity_incr: Field; fidelity_clear: Field
  words: tuple[int, int]

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
    ab, dst = 12 + s, 28 + s
    return MathAddrMod(
      srca_incr=_t(ab, 0, 6, f"addr_mod[{s}].srca_incr"),
      srca_cr=_t(ab, 6, 1, f"addr_mod[{s}].srca_cr"),
      srca_clear=_t(ab, 7, 1, f"addr_mod[{s}].srca_clear"),
      srcb_incr=_t(ab, 8, 6, f"addr_mod[{s}].srcb_incr"),
      srcb_cr=_t(ab, 14, 1, f"addr_mod[{s}].srcb_cr"),
      srcb_clear=_t(ab, 15, 1, f"addr_mod[{s}].srcb_clear"),
      dst_incr=_t(dst, 0, 10, f"addr_mod[{s}].dst_incr"),
      dst_cr=_t(dst, 10, 1, f"addr_mod[{s}].dst_cr"),
      dst_clear=_t(dst, 11, 1, f"addr_mod[{s}].dst_clear"),
      dst_c_to_cr=_t(dst, 12, 1, f"addr_mod[{s}].dst_c_to_cr"),
      fidelity_incr=_t(dst, 13, 2, f"addr_mod[{s}].fidelity_incr"),
      fidelity_clear=_t(dst, 15, 1, f"addr_mod[{s}].fidelity_clear"),
      words=(ab, dst),
    )


@dataclass(frozen=True)
class PackAddrMod:
  """One of 4 packer ADC address-modifier slots (0..3, ThreadConfig words 37..40), selected by PACR AddrMode.
  `src` counters address Dst (channel 0), `dst` counters address L1 (channel 1)."""
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
  """Per-thread Tensix control registers (ThreadConfig words 0..67). Boot zeroes every word."""
  cfg_bank: Field               # which of the two shared Config banks this thread reads (0 or 1)
  dst_offset: Field             # Dst row offset added to every FPU and SFPU Dst address (picks the Dst half)
  disable_implied_srca: Field   # 0: the FPU uses the SrcA format the unpacker handed over with the bank, and
                                #    MATH.srca_fmt is ignored. 1: the FPU uses MATH.srca_fmt instead.
  sfpu_dst_fmt_en: Field        # 1 = SFPLOAD/SFPSTORE in DEFAULT mode use sfpu_dst_fmt (ttrv always sets it)
  sfpu_dst_fmt: Field           # SFPU Dst DataFormat when sfpu_dst_fmt_en=1
  srca_override_addr: Field     # 1: unpacker 0 takes its SrcA row from the output address (row & 63). Every unpack
                                #    to SrcA needs this; with 0 it comes out corrupted. 0: the row comes from the
                                #    SrcRow counter, which an unpack straight to Dst needs. So it is 1 by default
                                #    and toggled to 0 around each unpack to Dst.
  disable_clr_dvalid_a: Field   # 1: a clear-dvalid of SrcA still flips the bank but leaves it with math, so later
  disable_clr_dvalid_b: Field   #    passes reuse the same data without waiting (98 vs ~46k cycles). The unpacker
                                #    then blocks on that bank until it is really released. Same for SrcB.
  fidelity_phase: Field         # fidelity phase added to the FPU's fidelity counter (0..3)
  unpack_ctx_offset: tuple[Field, Field]  # per unpacker (0/1): added to the config context an UNPACR selects
  unpack_ctx_reset: tuple[Field, Field]   # per unpacker (0/1): reset the context counter
  unpack_ctx_inc: tuple[Field, Field]     # per unpacker (0/1): increment the context counter
  addr_mod: tuple[MathAddrMod, ...]
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
  unpack_ctx_offset=(_t(41, 0, 4, "thread.unpack_ctx_offset[0]"), _t(41, 8, 4, "thread.unpack_ctx_offset[1]")),
  unpack_ctx_reset=(_t(41, 4, 1, "thread.unpack_ctx_reset[0]"), _t(41, 12, 1, "thread.unpack_ctx_reset[1]")),
  unpack_ctx_inc=(_t(41, 5, 1, "thread.unpack_ctx_inc[0]"), _t(41, 13, 1, "thread.unpack_ctx_inc[1]")),
  addr_mod=tuple(MathAddrMod.slot(s) for s in range(8)),
  pack_addr_mod=tuple(PackAddrMod.slot(s) for s in range(4)),
)


# ============================================================================================================
# 2. Math / FPU / Dst Config (Space.CONFIG, words 1..4)
# ============================================================================================================

@dataclass(frozen=True)
class MathCfg:
  """Shared FPU / SFPU formats and Dst accumulation width, plus the ReLU the packer applies on the way out."""
  # ALU formats (word 1)
  srca_fmt: Field               # SrcA DataFormat for the FPU. Read only when THREAD.disable_implied_srca=1;
                                # otherwise the FPU takes the format the unpacker handed over, for both operands.
  srcb_fmt: Field               # The FPU ignores this (it follows SrcA). It only picks FP16 vs BF16 decoding for
                                # SFPLOAD in DEFAULT mode when sfpu_fp32_acc and sfpu_dst_fmt_en are both 0.
  dst_fmt: Field                # Dst accumulator DataFormat (FLOAT32 or FLOAT16_B)
  fp32_dst_acc: Field           # 1 = the FPU accumulates into 32-bit Dst rows (8 tiles per Dst half)
  sfpu_fp32_acc: Field          # 1 = the SFPU reads and writes 32-bit Dst rows
  # ReLU (word 2). The packer applies it to the datums it reads; Dst itself is not changed.
  relu_mode: Field              # 0 off, 1 max(x, 0), 2 zero where x <= threshold, 3 min(x, threshold).
                                # The register field is 4 bits wide ([5:2]) but only these low 2 bits are read.
  relu_threshold: Field         # threshold as 16 bits in the packer's in_fmt: a BF16 pattern for in_fmt FLOAT16_B
                                # and FLOAT32, an FP16 pattern for FLOAT16 (where one mode-2 run gave NaNs,
                                # unexplained; we do not use FP16).
  # State reset (word 4)
  state_reset: Field            # Any MMIO write to this word, whatever the value, instantly zeroes words 0..179 of
                                # that Config bank (180+ and the other bank are kept). Boot uses it. An RMWCIB to
                                # the word just stores the bit and resets nothing.


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


# ============================================================================================================
# 3. Unpacker 0 (SrcA) & Unpacker 1 (SrcB) Config (Space.CONFIG, words 50..62 & THCON 64..159)
# ============================================================================================================

UNPACK_A_CONTEXTS, UNPACK_B_CONTEXTS = 8, 2  # Unpacker B on contexts 2..7 hangs the card


@dataclass(frozen=True)
class UnpackerCfg:
  """Configuration for Unpacker 0 (SrcA, or straight to Dst) or Unpacker 1 (SrcB).

  Two combinations hang the unpacker: plain data with zero-decompression left enabled, and BFP8 in L1 unpacked
  into a FLOAT16_B Src. The Src format an unpack hands over is the format the FPU then uses (see MATH.srca_fmt).

  Contexts. Each UNPACR names a context, and the per-context formats, base and offset apply to that instruction with
  no reconfiguration in between (measured, contexts 0, 1, 2 and 5). row_stride and face_stride are not per context,
  so the contexts used in one stream must produce the same Src datum width: BF16 (2 bytes) alternating with BFP8
  (1 byte) comes out wrong for one of them, with no error. A context kept for unpack-to-Dst needs 4-byte strides and
  THREAD.srca_override_addr=0, so both still have to be toggled around it.

  Reading consecutive tiles without rewriting base_addr: step offset_addr (any format), or let the channel-0 Z
  counter run past z_dim (BF16 only; see isa.UNPACR).
  """
  # TileDescriptor (THCON REG0, 128-bit)
  in_fmt: Field                 # L1 source DataFormat
  uncompressed: Field           # 1 = the tile has no zero-compression. Read only by single-context UNPACRs;
                                # with contexts enabled disable_zero_compress[ctx] decides. 0 on plain data hangs.
  x_dim: Field                  # datums per row of a face (typically 16 or 1024 for flat unpack)
  y_dim: Field                  # rows per face (typically 16 or 1)
  z_dim: Field                  # faces per tile (1..4)
  w_dim: Field                  # tiles (typically 1)
  # Format & mode controls (THCON REG1/REG2)
  out_fmt: Field                # SrcA/SrcB (or Dst) output DataFormat
  lf8_e4m3: Field               # 1 = LF8 input is E4M3 (4-bit exp), 0 = E5M2
  transpose: Field              # 1 = free X/Y face transpose (haloize_mode, Unpacker 0 only!)
  tileize_mode: Field           # 1 = gather rows of 32 datums from row-major L1 data, one row every
                                # tileize_row_pitch. Not a full tilizer: the rows still arrive in row-major
                                # order, so the four faces need reordering. Measured for inputs 32/64/96 wide.
  tileize_row_pitch: Field      # L1 distance between gathered rows, in 16-byte units (input width * datum bytes
                                # / 16; 8, 16 and 24 measured). cfg_defines.h names these 12 bits as three 4-bit
                                # Shift_amount_cntx fields, but they are one number, not per-context values.
  override_fmt: Field           # 1 = use per-context formats in REG7 instead of REG0/REG2
  force_shared_exp: Field       # 1 = replace BFP shared exponent with `shared_exp`
  shared_exp: Field             # 8-bit forced shared exponent
  add_dst_addr_cntr: Field      # 1 = add ADC counter to Dst target (used for unpack-to-Dst)
  # Strides (UNP{0,1}_ADDR_CTRL)
  row_stride: Field             # Src/Dst Y stride in bytes (REG_1_Ystride). The L1 side has no strides: the read
                                # position is the datum index the channel-0 ADC counters give (see isa.UNPACR).
  face_stride: Field            # Src/Dst Z stride in bytes (REG_1_Zstride)
  # Multi-context controls (contexts 0..7 for Unpacker 0, 0..1 for Unpacker 1)
  context_count: Field          # active contexts - 1 (when context_count_en=1)
  context_count_en: Field
  context_reset: Field          # Space.THREAD: pulse to reset context counter to 0
  disable_zero_compress: tuple[Field, ...]   # per context 0..7: 1 = plain data. 0 on plain data hangs.
  unpack_to_dst: tuple[Field, ...]           # per context 0..7: 1 = route Unpacker 0 directly to FP32 Dst
  context_in_fmt: tuple[Field, ...]          # per context: override L1 input format
  context_out_fmt: tuple[Field, ...]         # per context: override Src/Dst output format
  base_addr: tuple[Field, ...]               # per context: L1 address in 16-byte words, minus 1
  offset_addr: tuple[Field, ...]             # 4 x 16 bits, added to base_addr in 16-byte words. Context c uses
                                             # entry c & 3. Two RMWCIBs between tiles move the read position with no
                                             # stall (BF16 and BFP8; 4 BFP8 tiles in 621 cycles against 708 with a
                                             # base rewrite per tile).
  dst_addr: tuple[Field, ...]                # per context 0..3: target row offset (Unpacker 0)
  tile_x_dim: tuple[Field, ...]              # per context 0..3: per-context X dim (Unpacker 0)

  @staticmethod
  def unit(i: int) -> UnpackerCfg:
    sec = 64 + 48 * i                        # THCON_SEC0 = 64, THCON_SEC1 = 112
    xy1, zw1 = (56, 57) if i == 0 else (58, 59)
    exp_w = 50 if i == 0 else 62
    n_ctx = UNPACK_B_CONTEXTS if i else UNPACK_A_CONTEXTS
    p = f"unpack[{i}]"
    return UnpackerCfg(
      in_fmt=_c(sec + 0, 0, 4, f"{p}.in_fmt"),
      uncompressed=_c(sec + 0, 4, 1, f"{p}.uncompressed"),
      x_dim=_c(sec + 0, 16, 16, f"{p}.x_dim"),
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
      shared_exp=_c(exp_w, 0, 8, f"{p}.shared_exp"),
      add_dst_addr_cntr=_c(exp_w, 8, 1, f"{p}.add_dst_addr_cntr"),
      row_stride=_c(xy1, 16, 16, f"{p}.row_stride"),
      face_stride=_c(zw1, 0, 16, f"{p}.face_stride"),
      context_count=_c(sec + 9, 9, 3, f"{p}.context_count"),
      context_count_en=_c(sec + 9, 12, 1, f"{p}.context_count_en"),
      context_reset=THREAD.unpack_ctx_reset[i],
      disable_zero_compress=tuple(_c(sec + 9, (c & 3) + (c >> 2) * 16, 1, f"{p}.disable_zero_compress[{c}]") for c in range(8)),
      unpack_to_dst=tuple(_c(sec + 9, 4 + (c & 3) + (c >> 2) * 16, 1, f"{p}.unpack_to_dst[{c}]") for c in range(8)),
      context_in_fmt=tuple(_c(sec + 28 + (c & 3), 16 + (c >> 2) * 8, 4, f"{p}.context_in_fmt[{c}]") for c in range(n_ctx)),
      context_out_fmt=tuple(_c(sec + 28 + (c & 3), 20 + (c >> 2) * 8, 4, f"{p}.context_out_fmt[{c}]") for c in range(n_ctx)),
      base_addr=tuple(_c(sec + 12 + c, 0, 32, f"{p}.base_addr[{c}]") for c in range(n_ctx)),
      offset_addr=tuple(_c(sec + 28 + c, 0, 16, f"{p}.offset_addr[{c}]") for c in range(min(n_ctx, 4))),
      dst_addr=tuple(_c(sec + 20 + (c >> 1), (c & 1) * 16, 16, f"{p}.dst_addr[{c}]") for c in range(4)),
      tile_x_dim=tuple(_c(sec + 22 + (c >> 1), (c & 1) * 16, 16, f"{p}.tile_x_dim[{c}]") for c in range(4)),
    )


UNPACK = (UnpackerCfg.unit(0), UnpackerCfg.unit(1))


# ============================================================================================================
# 4. Packer Config (Space.CONFIG, words 12..39, the four THCON REG1/REG8 blocks, Dst offsets 180..183)
# ============================================================================================================

PACK_CONTEXTS = 4


@dataclass(frozen=True)
class PackCtx:
  """One of the packer's 4 configuration contexts. Every PACR runs in one: the one its CfgContext field names, or the
  packer's context counter, which steps after each tile (isa.PACR CtxtCtrl). Four output addresses, format pairs,
  exponent section sizes, l1_acc settings and Dst offsets can therefore stay programmed at once and be chosen per
  PACR with no config write (measured for all four contexts in one stream). The Dst strides (PACK.y_stride /
  z_stride / w_stride) are not per context, so the contexts used in one stream need in_fmts of the same width:
  mixing widths gives garbage with no error. ttrv uses context 0 only."""
  exp_section_size: Field        # BFP shared-exponent section size in 16-byte words (0 for BF16/FP32)
  l1_dest_addr: Field            # L1 destination address in 16-byte words, minus 1 (usually written via WRCFG)
  disable_zero_compress: Field   # 1 = disable zero compression (always set 1 for dense tiles)
  out_fmt: Field                 # L1 output DataFormat
  in_fmt: Field                  # the packer's intermediate DataFormat: Dst is first converted to in_fmt, then to
                                 # out_fmt. FP32 Dst packed to BF16 truncates with in_fmt=FLOAT32 (what ttrv does)
                                 # and rounds to nearest (ties away from zero) with in_fmt=FLOAT16_B, at no cost.
  l1_acc: Field                  # 1 = add each datum to what L1 already holds, after format conversion: FP32 is
                                 # bit-exact, BF16 gives bf16(L1) + bf16(datum) rounded to nearest even. It can
                                 # stay set across packs (three packs gave y + 3x exactly). Not for BFP output.
  downsample_mask: Field         # of every 16 datums, keep the ones whose bit is set and write them back to back.
                                 # 0 and 0xFFFF both keep everything.
  pack_per_xy_plane: Field       # datums per XY plane (0 = full 16x16 face)
  pack_reads_per_xy_plane: Field # Dst row reads per XY plane (16 for full face)
  pack_xys_per_tile: Field       # XY faces per tile
  dst_target_offset: Field       # Dst row the packer starts reading at. THREAD.dst_offset and the other math-side
                                 # Dst offsets do not apply to the packer.

  @staticmethod
  def context(c: int) -> PackCtx:
    reg = (68, 96, 116, 144)[c]              # THCON_SEC0_REG1, SEC0_REG8, SEC1_REG1, SEC1_REG8
    p = f"pack.ctx[{c}]"
    return PackCtx(
      exp_section_size=_c(reg, 16, 16, f"{p}.exp_section_size"),
      l1_dest_addr=_c(reg + 1, 0, 32, f"{p}.l1_dest_addr"),
      disable_zero_compress=_c(reg + 2, 0, 1, f"{p}.disable_zero_compress"),
      out_fmt=_c(reg + 2, 4, 4, f"{p}.out_fmt"),
      in_fmt=_c(reg + 2, 8, 4, f"{p}.in_fmt"),
      l1_acc=_c(reg + 3, 19, 1, f"{p}.l1_acc"),
      downsample_mask=_c(reg + 3, 0, 16, f"{p}.downsample_mask"),
      pack_per_xy_plane=_c(28 + c, 0, 8, f"{p}.pack_per_xy_plane"),
      pack_reads_per_xy_plane=_c(28 + c, 8, 8, f"{p}.pack_reads_per_xy_plane"),
      pack_xys_per_tile=_c(28 + c, 16, 7, f"{p}.pack_xys_per_tile"),
      dst_target_offset=_c(180 + c, 0, 12, f"{p}.dst_target_offset"),
    )


@dataclass(frozen=True)
class PackerCfg:
  """Configuration for the packer (Dst -> L1, driven by TRISC2). Blackhole has one packer.

  A datum goes Dst -> in_fmt -> ReLU (cfg.MATH) -> edge mask -> downsample -> out_fmt -> L1 (optionally added to L1).
  """
  ctx: tuple[PackCtx, ...]       # per-context fields: output address, formats, l1_acc, counters, Dst offset
  # Shared by all contexts
  lf8_e4m3: Field                # 1 = LF8 output is E4M3 (4-bit exp), 0 = E5M2
  read_32b: Field                # 1 = read 32-bit FP32/INT32 from Dst
  # Dst-side strides (words 12..13) & L1-side strides (words 14..15), all in bytes
  y_stride: Field; z_stride: Field; w_stride: Field   # Dst bytes per row / face / tile of the packer's Dst ADC
  l1_y_stride: Field; l1_z_stride: Field; l1_w_stride: Field
                                 # L1 bytes (multiples of 16) the output address moves per Y / Z / W step of the L1
                                 # ADC: a tile is written at (l1_dest_addr + 1) * 16 + Y * l1_y_stride
                                 # + Z * l1_z_stride + W * l1_w_stride. Read only when a PACR starts a new address,
                                 # that is the first PACR after one with Last=1; inside one stream they are ignored.
                                 # Self-advance (measured): write l1_dest_addr once, set l1_z_stride to the tile's
                                 # size in L1 (4096 FP32, 2048 BF16, 1088 BFP8) and give the tile's Last PACR a
                                 # PackAddrMod slot with ydst_clear and zdst_incr=1. Output is exact, and
                                 # byte-identical to ttrv's for BFP8. Per tile, issued from a MOP, against
                                 # rewriting the address: FP32 76 -> 50 cycles, BF16 66 -> 34..39, BFP8 78 -> 51.
                                 # zdst_clear returns to the base. Stepping Y instead (ydst_cr + ydst_incr=1,
                                 # l1_y_stride = tile size) works the same. isa.INCADCZW / INCADCXY step the same
                                 # counters from the instruction stream, and can step the Dst tile with them.
  # Edge masks (words 19..27, 36..39), as tt-isa-documentation Packers/EdgeMasking.md. A masked datum is still
  # written to L1, as 0 or as -inf. The row's mask is edge_mask[row_set_mapping[b][row]], where b is this
  # context's row_set_select, or face_set_mapping[face_set_select][face] when face_set_en=1.
  edge_mask: tuple[Field, ...]         # 4 x 16-bit keep masks, bit = column (0xFFFF keeps all 16 datums)
  edge_mode: Field                     # what a masked datum becomes: 0 = 0.0, 1 = -inf
  row_set_mapping: tuple[Field, ...]   # 4 x 32 bits: 2 bits per row 0..15, naming the edge_mask for that row
  row_set_select: Field                # 2 bits per PACR context: which row_set_mapping applies
  face_set_mapping: tuple[Field, ...]  # 4 x 32 bits: 2 bits per face 0..15, naming the row_set_mapping
  face_set_select: Field               # 2 bits per PACR context: which face_set_mapping applies
  face_set_en: Field                   # 1 = choose the row mapping per face; row_set_select is then ignored


PACK = PackerCfg(
  ctx=tuple(PackCtx.context(c) for c in range(PACK_CONTEXTS)),
  lf8_e4m3=_c(71, 23, 1, "pack.lf8_e4m3"),
  read_32b=_c(18, 0, 1, "pack.read_32b"),
  y_stride=_c(12, 16, 16, "pack.y_stride"),
  z_stride=_c(13, 0, 16, "pack.z_stride"),
  w_stride=_c(13, 16, 16, "pack.w_stride"),
  l1_y_stride=_c(14, 16, 16, "pack.l1_y_stride"),
  l1_z_stride=_c(15, 0, 16, "pack.l1_z_stride"),
  l1_w_stride=_c(15, 16, 16, "pack.l1_w_stride"),
  edge_mask=tuple(_c(24 + s, 0, 16, f"pack.edge_mask[{s}]") for s in range(4)),
  edge_mode=_c(24, 16, 1, "pack.edge_mode"),
  row_set_mapping=tuple(_c(20 + s, 0, 32, f"pack.row_set_mapping[{s}]") for s in range(4)),
  row_set_select=_c(24, 17, 8, "pack.row_set_select"),
  face_set_mapping=tuple(_c(36 + s, 0, 32, f"pack.face_set_mapping[{s}]") for s in range(4)),
  face_set_select=_c(19, 0, 8, "pack.face_set_select"),
  face_set_en=_c(19, 8, 1, "pack.face_set_en"),
)


# ============================================================================================================
# 5. Global Tile Control (Space.CONFIG, words 184..222)
# ============================================================================================================

@dataclass(frozen=True)
class GlobalCfg:
  """Tile-wide RISC control and Dst access mode. These words survive MATH.state_reset."""
  icache_invalidate: Field         # 5-bit mask: bit0=BRISC, bit1..3=TRISC0..2, bit4=NCRISC
  prefetch_trisc: Field            # 3-bit mask enabling TRISC0..2 instruction prefetch
  prefetch_brisc: Field            # enable BRISC instruction prefetch
  prefetch_ncrisc: Field           # enable NCRISC instruction prefetch
  prefetch_max_req: Field          # max outstanding instruction prefetch requests (boot sets 0x11F total)
  scratch: tuple[Field, ...]       # 3 free 32-bit words. CFGSHIFTMASK adds / ORs one into another Config word in
                                   # the instruction stream, which is how a REPLAY body steps an address
                                   # (measured). Its scratch_sel=3 reads scratch[TRISC number]. Never make a
                                   # scratch word the target of a CFGSHIFTMASK.
  zeroacc_abs_tile_mode: Field     # 0: ZEROACC's face index counts from the Dst half THREAD.dst_offset points
                                   #    into. 1: it counts from Dst row 0.


GLOBAL = GlobalCfg(
  icache_invalidate=_c(185, 0, 5, "global.icache_invalidate"),
  prefetch_trisc=_c(208, 0, 3, "global.prefetch_trisc"),
  prefetch_brisc=_c(208, 3, 1, "global.prefetch_brisc"),
  prefetch_ncrisc=_c(208, 4, 1, "global.prefetch_ncrisc"),
  prefetch_max_req=_c(208, 5, 8, "global.prefetch_max_req"),
  scratch=tuple(_c(209 + i, 0, 32, f"global.scratch[{i}]") for i in range(3)),
  zeroacc_abs_tile_mode=_c(220, 3, 1, "global.zeroacc_abs_tile_mode"),
)



@dataclass(frozen=True)
class MoverCfg:
  """The mover XMOV starts (THCON_SEC0_REG6, words 88..90): an asynchronous copy or zero-fill in 16-byte units.
  Measured: both are exact with no overrun. A 64 KB copy runs at 11.3 bytes per cycle and a zero-fill at 14.1
  (10.2 and 13.1 for 4 KB)."""
  src_addr: Field                  # L1 source address in 16-byte units
  dst_addr: Field                  # destination address in 16-byte units
  size: Field                      # length in 16-byte units (16 bits are read)
  direction: Field                 # 0 = zero-fill L1, 3 = L1 to L1 (both measured). 1 and 2 target config /
                                   # NCRISC code memory and are not for us.


MOVER = MoverCfg(
  src_addr=_c(88, 0, 32, "mover.src_addr"),
  dst_addr=_c(89, 0, 32, "mover.dst_addr"),
  size=_c(90, 0, 30, "mover.size"),
  direction=_c(90, 30, 2, "mover.direction"),
)

# Convenience aliases
ADDR_MOD = THREAD.addr_mod
PACK_ADDR_MOD = THREAD.pack_addr_mod


# ============================================================================================================
# Probed and left out (cfgprobe 2026-11-23). T = ThreadConfig word, C = Config word. Leave them all 0.
# ============================================================================================================
#
# No effect seen:
#   T3[0]        disable_implied_srcb       the FPU takes its format from SrcA only
#   T5[1:0]      srca_bank                  no effect, full row map checked (all values, both banks, set during
#                        math or during the unpack)
#   T8/T9/T10[0] scbd_32b_en (math / pack / unpack)   no change in results or timing
#   C0[14:10]    dst_fmt_ovrd (+val)
#   C1[13], [14] GS_LF, bfp8_hf
#   C5[0]        dst_offset_en              the packer's Dst offset applies either way
#   C14[15:0]    l1_x_stride                no role in the packer's output address
#   C64[11:8]    blobs_per_xy_plane         (unpacker, uncompressed data)
#   C70[1]       add_l1_dest_offset         adds a TDMA-RISC offset register that is 0 after reset
#   C71[18:16]   downsample_rate
#   C180[17:12]  packer ZOffset             no data effect; it offsets the face index used by edge masks
#   C222[0]      sfpu_scbd_disable          tested within one thread only
#
# Only partly understood:
#   T6[1:0]      srcb_bank                  not a bank select: non-zero values shift math's SrcB reads by 16-row
#                        groups, some groups read as zeros, and the effect carries into the next bank's pass. No
#                        model fits every case (cfgprobe FINDINGS2_card0.md has the maps). Keep 0; boot zeroes it.
#   C0[9:5]      srcb_fmt_ovrd (+val)       replaces MATH.srcb_fmt, which itself barely matters
#   C221[3:2]    disable_contig_dvalid_a/b  only matters with single_bank: the 128-row view starts at the current bank
#
# Measured, but nothing a lowering wants:
#   T36[9:0] + C7[15:0]  sfpu_stack_incr + dst_sp_base   an SFPU stack in Dst: SFPSTORE in INT32_ALL mode writes at
#                        Sp + base then Sp += incr; SFPLOAD in that mode does Sp -= incr then reads. Sp survives
#                        reloads.
#   T55[0]       fp16a_force_en             FP16-style math and FP16 writes into 16-bit Dst rows, even with fp32_dst_acc
#   T(20+slot)[1:0]      addr_mod srca/srcb_hi_incr      +64 on the Src increment, for single_bank only
#   C0[4:0]      srca_fmt_ovrd (+val)       replaces MATH.srca_fmt, again only when disable_implied_srca=1
#   C1[0]        fpu_srnd_en                stochastic rounding of FPU writes to Dst
#   C1[1]        gasket_srnd_en             stochastic rounding of the packer's Dst -> BF16 stage (in_fmt=FLOAT16_B)
#   C1[2]        packer_srnd_en             stochastic rounding of BFP output mantissas only
#   C186         prng_seed                  does not make any of the above repeatable from run to run
#   C1[16:15]    srca/srcb_unsigned         read by the unpacker, not by math: INT8 bytes unpack as 0..255
#   C1[31]       int8_math_en               exact integer adds: INT8 Src into a sign-magnitude int32 Dst
#   C2[0]        zero_flag_dis_src          zeros in SrcB read as 2^-15 in FP16-style multiplies
#   C2[1]        zero_flag_dis_dst          the FPU reads the old contents of rows ZEROACC just cleared
#   C6[15:0]     dst_regw_base              row offset on FPU Dst writes (aligned to 8) and SFPU accesses; not packer
#   C18[1], [2]  read_unsigned, read_int8   INT8 output saturation (signed +-127 / unsigned 255); forced truncation
#   C28[23]      pack_yz_transposed         edge masks pick by face instead of by row; no addressing effect
#   C68[15:0]    row_start_section_size     shifts the output by N x 16 bytes, with zero compression on only
#   C72[5:4] + C70[3]    throttle_mode + its override   ignored without the override; with it an FP32 tile unpacks in
#                        256/128/71/71 cycles for modes 0..3. The default is already 71, so there is nothing to gain.
#   C72[13:12], [15]     upsample_rate, upsample_interleave   insert 2^r - 1 zeros after each datum, or skip those slots
#   C220[0], [1] dst_swizzle_32b, dst_remap_addrs   remap Dst rows as the ISA docs say; FPU, packer and RISC all agree
#   C221[1:0]    srca/srcb_single_bank      math sees both banks as one 128-row Src. A pass then needs both banks valid
#                        and releases both, so a pipeline handing over one tile per pass deadlocks.
#
# Never probed, and nothing here writes them:
#   C12[15:0]    packer Dst x_stride
#   C18[3]       round_10b_mant             ttrv set it only when packing from FP16 Dst, a format we dropped
#   C44..C47     unpacker ADDR_CTRL REG_0 strides   the ISA docs give them no role: the L1 side has no strides
