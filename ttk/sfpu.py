from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import Enum

from dsl import (
  TTINCRWC,
  TTSETRWC,
  TTSFPADD,
  TTSFPADDI,
  TTSFPARECIP,
  TTSFPCAST,
  TTSFPCONFIG,
  TTSFPEXEXP,
  TTSFPEXMAN,
  TTSFPLOAD,
  TTSFPLOADI,
  TTSFPMAD,
  TTSFPMOV,
  TTSFPMUL,
  TTSFPNOP,
  TTSFPSETEXP,
  TTSFPSHFT,
  TTSFPSHFT2,
  TTSFPSTORE,
  TTSFPSWAP,
  TTSFPTRANSP,
)


class SfpuTranscendentalOp(Enum):
  EXP = "exp"
  RSQRT = "rsqrt"
  RECIP = "recip"
  SIGMOID = "sigmoid"
  SILU = "silu"


@dataclass(frozen=True)
class SfpuTileWalk:
  faces: int = 4
  groups_per_face: int = 8
  load_store_addr_mod: int = 7
  face_advance: int = 4

  @property
  def groups_per_tile(self) -> int:
    return self.faces * self.groups_per_face


DEFAULT_TILE_WALK = SfpuTileWalk()


def fp32_bits(value: float) -> int:
  return struct.unpack("<I", struct.pack("<f", value))[0]


def bf16_imm(value: float) -> int:
  return fp32_bits(value) >> 16


def sfpu_load_fp32_const(fw, lreg: int, value: float):
  """Load an exact fp32 literal into every lane of an SFPU LReg."""
  bits = fp32_bits(value)
  fw.emit(TTSFPLOADI(lreg, 10, bits & 0xFFFF))       # SFPLOADI_MOD0_LOWER
  return fw.emit(TTSFPLOADI(lreg, 8, bits >> 16))    # SFPLOADI_MOD0_UPPER


def _sfpu_scratch_regs(scratch, avoid: set[int], count: int) -> list[int]:
  regs = []
  for reg in scratch:
    if reg in avoid or reg in (8, 9, 10):
      continue
    if not 0 <= reg < 8:
      raise ValueError(f"SFPU scratch LReg must be in [0, 7], got {reg}")
    if reg not in regs:
      regs.append(reg)
    if len(regs) == count:
      return regs
  raise ValueError(f"Need {count} scratch LRegs avoiding {sorted(avoid)}, got {tuple(scratch)}")


def sfpu_exp(fw, src_lreg: int, dst_lreg: int, *, scratch=(1, 2, 3, 4, 5, 6, 7)):
  """Emit the Blackhole bf16-dst natural exp21f SFPU sequence.

  This ports tt-llk's `_sfpu_exp_21f_bf16_`: x is transformed to base-2,
  clamped to [0, 255], split with EXEXP/EXMAN/SHFT, approximated with the
  Moroz degree-2 polynomial, then recombined with SFPSETEXP. LRegs are fp32
  internally; this helper leaves bf16 rounding to the caller's SFPSTORE.
  Device-validated: max_rel ~0.007 over [-10, 2]."""
  c, exp, man, poly = _sfpu_scratch_regs(scratch, {src_lreg, dst_lreg}, 4)

  sfpu_load_fp32_const(fw, c, 1.4426950216293334961)
  fw.emit(TTSFPMUL(src_lreg, c, 9, dst_lreg, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPADDI(bf16_imm(127.0), dst_lreg, 0))
  fw.emit(TTSFPNOP())

  fw.emit(TTSFPLOADI(c, 0, 0))
  fw.emit(TTSFPSWAP(0, dst_lreg, c, 1))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPLOADI(c, 0, bf16_imm(255.0)))
  fw.emit(TTSFPSWAP(0, c, dst_lreg, 1))
  fw.emit(TTSFPNOP())

  fw.emit(TTSFPEXEXP(0, dst_lreg, exp, 0))
  fw.emit(TTSFPEXMAN(0, dst_lreg, man, 0))
  fw.emit(TTSFPSHFT(0, exp, man, 0))
  fw.emit(TTSFPNOP())

  fw.emit(TTSFPEXEXP(0, man, exp, 1))
  fw.emit(TTSFPEXMAN(0, man, man, 1))
  fw.emit(TTSFPCAST(man, man, 0))
  fw.emit(TTSFPNOP())

  sfpu_load_fp32_const(fw, poly, 4.791750143340323e-15)
  fw.emit(TTSFPMUL(poly, man, 9, poly, 0))
  fw.emit(TTSFPNOP())
  sfpu_load_fp32_const(fw, c, 7.839635491371155e-08)
  fw.emit(TTSFPADD(10, poly, c, poly, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMUL(poly, man, 9, poly, 0))
  fw.emit(TTSFPNOP())
  sfpu_load_fp32_const(fw, c, 1.0017248)
  fw.emit(TTSFPADD(10, poly, c, poly, 0))
  fw.emit(TTSFPNOP())

  fw.emit(TTSFPSETEXP(0, poly, exp, 0))
  fw.emit(TTSFPNOP())
  if exp != dst_lreg:
    fw.emit(TTSFPMOV(0, exp, dst_lreg, 0))
  return fw


def sfpu_reciprocal(fw, src_lreg: int, dst_lreg: int, *, scratch=(1, 2, 3, 4, 5, 6, 7), iterations: int = 2):
  """Emit SFPARECIP plus Newton-Raphson reciprocal refinement.

  The update is tt-llk's Blackhole path for normal finite values:
  y = approx_recip(x); repeat t = x*y - 2; y = y*(-t).
  Device-validated: max_rel ~0.006 over [0.25, 64] with 2 iterations."""
  if iterations < 0:
    raise ValueError("iterations must be non-negative")
  x_lreg = src_lreg
  if src_lreg == dst_lreg and iterations:
    x_lreg = _sfpu_scratch_regs(scratch, {src_lreg, dst_lreg}, 1)[0]
    fw.emit(TTSFPMOV(0, src_lreg, x_lreg, 0))
  two, t = _sfpu_scratch_regs(scratch, {src_lreg, dst_lreg, x_lreg}, 2)

  sfpu_load_fp32_const(fw, two, 2.0)
  fw.emit(TTSFPARECIP(0, src_lreg, dst_lreg, 0))
  fw.emit(TTSFPNOP())
  for _ in range(iterations):
    fw.emit(TTSFPMAD(x_lreg, dst_lreg, two, t, 2))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMUL(t, dst_lreg, 9, dst_lreg, 1))
    fw.emit(TTSFPNOP())
  return fw


def emit_rsqrt(fw, src_lreg: int, dst_lreg: int, *, scratch=(1, 2, 3, 4, 5, 6, 7), iterations: int = 5):
  """Emit an SFPU Newton rsqrt sequence, seeded with 1.0.

  This is the near-unit Blackhole path already used by the llama RMSNorm POC:
  ``y = y * (1.5 - 0.5*x*y*y)``. It is suitable for microbenching the iterative
  rsqrt body and validates exactly for x=1.0, but is not a wide-range library
  rsqrt yet.
  """
  if iterations < 0:
    raise ValueError("iterations must be non-negative")
  x_lreg = src_lreg
  if src_lreg == dst_lreg:
    x_lreg = next(reg for reg in scratch if reg != src_lreg)
    fw.emit(TTSFPMOV(0, src_lreg, x_lreg, 0))
  regs = [reg for reg in scratch if reg not in {src_lreg, dst_lreg, x_lreg}]
  if len(regs) < 4:
    raise ValueError("emit_rsqrt needs four scratch LRegs")
  y, half, three_halves, tmp = regs[:4]
  fw.emit(TTSFPLOADI(y, 0, bf16_imm(1.0)))
  fw.emit(TTSFPLOADI(half, 0, bf16_imm(0.5)))
  fw.emit(TTSFPLOADI(three_halves, 0, bf16_imm(1.5)))
  for _ in range(iterations):
    fw.emit(TTSFPMUL(y, y, 9, tmp, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMUL(x_lreg, tmp, 9, tmp, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMUL(half, tmp, 9, tmp, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPADD(10, three_halves, tmp, tmp, 2))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMUL(y, tmp, 9, y, 0))
    fw.emit(TTSFPNOP())
  if y != dst_lreg:
    fw.emit(TTSFPMOV(0, y, dst_lreg, 0))
  return fw


def emit_sigmoid(fw, src_lreg: int, dst_lreg: int, *, scratch=(1, 2, 3, 4, 5, 6, 7)):
  regs = [reg for reg in scratch if reg not in {src_lreg, dst_lreg}]
  if len(regs) < 2:
    raise ValueError("emit_sigmoid needs two scratch LRegs")
  neg_x, one = regs[:2]
  sfpu_load_fp32_const(fw, one, 1.0)
  fw.emit(TTSFPMUL(src_lreg, one, 9, neg_x, 1))
  fw.emit(TTSFPNOP())
  sfpu_exp(fw, neg_x, dst_lreg, scratch=tuple(regs[1:]) + (src_lreg,))
  fw.emit(TTSFPADD(10, dst_lreg, one, dst_lreg, 0))
  fw.emit(TTSFPNOP())
  return sfpu_reciprocal(fw, dst_lreg, dst_lreg, scratch=tuple(regs) + (src_lreg,), iterations=2)


def emit_silu(fw, src_lreg: int, dst_lreg: int, *, scratch=(1, 2, 3, 4, 5, 6, 7)):
  regs = [reg for reg in scratch if reg not in {src_lreg, dst_lreg}]
  if len(regs) < 3:
    raise ValueError("emit_silu needs three scratch LRegs")
  x_copy = regs[0]
  fw.emit(TTSFPMOV(0, src_lreg, x_copy, 0))
  emit_sigmoid(fw, src_lreg, dst_lreg, scratch=tuple(regs[1:]) + (x_copy,))
  fw.emit(TTSFPMUL(x_copy, dst_lreg, 9, dst_lreg, 0))
  return fw.emit(TTSFPNOP())


def emit_transcendental_lreg(
  fw,
  op: SfpuTranscendentalOp | str,
  src_lreg: int = 0,
  dst_lreg: int = 0,
  *,
  scratch=(1, 2, 3, 4, 5, 6, 7),
):
  op = SfpuTranscendentalOp(op)
  if op is SfpuTranscendentalOp.EXP:
    return sfpu_exp(fw, src_lreg, dst_lreg, scratch=scratch)
  if op is SfpuTranscendentalOp.RSQRT:
    return emit_rsqrt(fw, src_lreg, dst_lreg, scratch=scratch)
  if op is SfpuTranscendentalOp.RECIP:
    return sfpu_reciprocal(fw, src_lreg, dst_lreg, scratch=scratch, iterations=2)
  if op is SfpuTranscendentalOp.SIGMOID:
    return emit_sigmoid(fw, src_lreg, dst_lreg, scratch=scratch)
  if op is SfpuTranscendentalOp.SILU:
    return emit_silu(fw, src_lreg, dst_lreg, scratch=scratch)
  raise NotImplementedError(op.value)


def emit_load_op_store_group(
  fw,
  op: SfpuTranscendentalOp | str,
  *,
  value_lreg: int = 0,
  addr_mod: int = DEFAULT_TILE_WALK.load_store_addr_mod,
):
  fw.emit(TTSFPLOAD(value_lreg, 0, addr_mod, 0))
  emit_transcendental_lreg(fw, op, value_lreg, value_lreg)
  fw.emit(TTSFPSTORE(value_lreg, 0, addr_mod, 0))
  fw.emit(TTSFPNOP())
  return fw.emit(TTINCRWC(0, 2, 0, 0))


def emit_transcendental_tile(
  fw,
  op: SfpuTranscendentalOp | str,
  *,
  walk: SfpuTileWalk = DEFAULT_TILE_WALK,
):
  for _face in range(walk.faces):
    for _group in range(walk.groups_per_face):
      emit_load_op_store_group(fw, op, addr_mod=walk.load_store_addr_mod)
    fw.emit(
      TTSETRWC(0, walk.face_advance, 8, 0, 0, walk.face_advance),
      TTSETRWC(0, walk.face_advance, 8, 0, 0, walk.face_advance),
    )
  return fw


# SFPSWAP mod1=1: per-lane compare-and-swap so VD=max, VC=min across all rows.
SFPSWAP_ALL_ROWS_MAX = 1


def emit_sum_reduce_32(fw):
  """Sum the 32 lanes of L0 into every lane of L1 (fp32 accumulate in LRegs).

  Device-validated by the llama RMSNorm POC: rotate-add reduces each 8-lane
  row (SFPSHFT2 mod=3 rotates right by one within the row), then SFPTRANSP
  moves the four row sums into L0..L3 and three adds total them. Clobbers
  L0..L3; the result lands in L1 lane 0 (and L0 after the final add).
  """
  fw.emit(TTSFPMOV(0, 0, 1, 0))       # L1 = row accumulator
  for _ in range(7):
    fw.emit(TTSFPSHFT2(0, 0, 2, 3))   # L2 = rotate-right-1 within each 8-lane row
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPADD(10, 1, 2, 1, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMOV(0, 2, 0, 0))     # rotate source for the next term

  # Transpose the four row sums into L0..L3 row 0, then add them.
  fw.emit(TTSFPMOV(0, 1, 0, 0))
  fw.emit(TTSFPLOADI(1, 2, 0))
  fw.emit(TTSFPLOADI(2, 2, 0))
  fw.emit(TTSFPLOADI(3, 2, 0))
  fw.emit(TTSFPTRANSP(0, 0, 0, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPADD(10, 0, 1, 0, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPADD(10, 0, 2, 0, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPADD(10, 0, 3, 0, 0))
  fw.emit(TTSFPNOP())
  return fw


def emit_horizontal_reduce_max(fw):
  """Blackhole LLK ckernel_sfpu_reduce.h::horizontal_reduce_max, on L0 and L4.

  Butterfly max across the 32-lane footprint via SFPSHFT2 lane shifts +
  SFPSWAP max; leaves the max broadcast in L0/L4. Clobbers L1 and L5."""
  for shifts in (4, 2, 1):
    fw.emit(TTSFPMOV(0, 0, 1, 0))
    fw.emit(TTSFPMOV(0, 4, 5, 0))
    for _ in range(shifts):
      fw.emit(TTSFPSHFT2(0, 1, 1, 4))
      fw.emit(TTSFPSHFT2(0, 5, 5, 4))
    fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
    fw.emit(TTSFPSWAP(0, 4, 5, SFPSWAP_ALL_ROWS_MAX))
  fw.emit(TTSFPSHFT2(0, 0, 0, 3))
  fw.emit(TTSFPSHFT2(0, 4, 4, 3))
  return fw


def emit_reduce_row_max_tile(fw, *, fmt: int = 2, addr_mod: int = 7, tile_row_offset: int = 0):
  """Blackhole LLK perform_reduce_row_max_tile: per-row max over a 32x32 tile.

  Reduces each row's 32 columns with SFPU compare-and-swap plus cross-column
  shifts and stores the row max back to column 0 of the tile in DST.
  Device-validated by the llama argmax POC (bf16, fmt=2). Clobbers L0..L7."""
  fw.emit(TTSFPCONFIG(0, 15, 1))
  for face_pair in range(2):
    base = tile_row_offset + face_pair * 2 * 16
    for row_group in range(2):
      r0 = row_group * 8
      r1 = r0 + 4
      for lreg, off in (
        (0, r0), (1, r0 + 2), (2, 16 + r0), (3, 16 + r0 + 2),
        (4, r1), (5, r1 + 2), (6, 16 + r1), (7, 16 + r1 + 2),
      ):
        fw.emit(TTSFPLOAD(lreg, fmt, addr_mod, base + off))
      for a, b in ((0, 2), (4, 6), (1, 3), (5, 7), (0, 1), (4, 5)):
        fw.emit(TTSFPSWAP(0, a, b, SFPSWAP_ALL_ROWS_MAX))
      emit_horizontal_reduce_max(fw)
      fw.emit(TTSFPSTORE(0, fmt, addr_mod, base + r0))
      fw.emit(TTSFPSTORE(4, fmt, addr_mod, base + r1))
      fw.emit(TTSFPNOP())
  return fw


def rope_rotate_row_seq(*, fmt: int = 2, addr_mod: int = 7,
                        x1_addr: int = 0, x2_addr: int = 64,
                        cos_addr: int = 128, sin_addr: int = 192):
  """One row-group of the RoPE rotation as a replayable instruction list:

    out1 = x1*cos - x2*sin ; out2 = x2*cos + x1*sin

  Operands are four tiles staged in DST at the given offsets (x1, x2, cos,
  sin); results overwrite x1/x2. Device-validated by the llama rope POC
  (bf16, fmt=2). Clobbers L0..L4 and L6; INCRWC advances to the next rows."""
  return [
    TTSFPLOAD(0, fmt, addr_mod, x1_addr),
    TTSFPLOAD(1, fmt, addr_mod, x2_addr),
    TTSFPLOAD(2, fmt, addr_mod, cos_addr),
    TTSFPLOAD(3, fmt, addr_mod, sin_addr),
    TTSFPMUL(0, 2, 9, 4, 0),            # x1 * cos
    TTSFPMAD(1, 3, 4, 6, 1),            # -(x2 * sin) + x1*cos
    TTSFPNOP(),
    TTSFPSTORE(6, fmt, addr_mod, x1_addr),
    TTSFPMUL(1, 2, 9, 4, 0),            # x2 * cos
    TTSFPMAD(0, 3, 4, 6, 0),            # x1*sin + x2*cos
    TTSFPNOP(),
    TTSFPSTORE(6, fmt, addr_mod, x2_addr),
    TTINCRWC(0, 2, 0, 0),
  ]


def emit_constant_tile(
  fw,
  value: float,
  *,
  lreg: int = 0,
  walk: SfpuTileWalk = DEFAULT_TILE_WALK,
):
  for _face in range(walk.faces):
    for _group in range(walk.groups_per_face):
      sfpu_load_fp32_const(fw, lreg, value)
      fw.emit(TTSFPSTORE(lreg, 0, walk.load_store_addr_mod, 0))
      fw.emit(TTSFPNOP())
      fw.emit(TTINCRWC(0, 2, 0, 0))
    fw.emit(
      TTSETRWC(0, walk.face_advance, 8, 0, 0, walk.face_advance),
      TTSETRWC(0, walk.face_advance, 8, 0, 0, walk.face_advance),
    )
  return fw
