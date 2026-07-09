from __future__ import annotations

import math
import struct
from enum import IntEnum

from dsl import (
  TTINCRWC, TTSETRWC,
  TTSFPADD, TTSFPADDI, TTSFPARECIP, TTSFPCAST, TTSFPCONFIG, TTSFPEXEXP,
  TTSFPEXMAN, TTSFPIADD, TTSFPLUT, TTSFPLOAD, TTSFPLOADI, TTSFPMAD, TTSFPMOV,
  TTSFPMUL, TTSFPNOP, TTSFPSETEXP, TTSFPSHFT, TTSFPSTORE, TTSFPSWAP,
)


def f32_bits(value: float) -> int:
  return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def f32(value: float) -> float:
  return struct.unpack("<f", struct.pack("<f", float(value)))[0]


class LReg(IntEnum):
  L0 = 0
  L1 = 1
  L2 = 2
  L3 = 3
  L4 = 4
  L5 = 5
  L6 = 6
  L7 = 7
  CONST_0 = 9
  CONST_1 = 10
  CONST_NEG1 = 11
  PRGM0 = 12
  PRGM1 = 13
  PRGM2 = 14


class SfpuLoadIMod(IntEnum):
  FLOATB = 0
  FLOATA = 1
  USHORT = 2
  SHORT = 4
  UPPER = 8
  LOWER = 10


class SfpuConfigDest(IntEnum):
  LREG11 = 11
  LREG12 = 12
  LREG13 = 13
  LREG14 = 14
  SFPU_CTRL = 15


SFPMAD_MOD1_OFFSET_NONE = 0

FRAC_1_PI = f32(0.31830987334251404)
SIN_P0 = f32(float.fromhex("-0x1.92p+1"))
SIN_P1 = f32(float.fromhex("-0x1.fbp-11"))
SIN_P2 = f32(float.fromhex("-0x1.51p-21"))
SIN_P3 = f32(float.fromhex("-0x1.0b4612p-33"))

COS_P0 = f32(float.fromhex("-0x1.92p+0"))
COS_P1 = f32(float.fromhex("-0x1.fbp-12"))
COS_P2 = f32(float.fromhex("-0x1.51p-22"))
COS_P3 = f32(float.fromhex("-0x1.0b4612p-34"))

ROUNDING_BIAS = f32(12582912.0)

SIN_COEFFS_FP32 = (
  f32(float.fromhex("-0x1.55554cp-3")),
  f32(float.fromhex("0x1.110edap-7")),
  f32(float.fromhex("-0x1.9f70fp-13")),
  f32(float.fromhex("0x1.5dc908p-19")),
)
SIN_COEFFS_BF16_DEST = (
  f32(float.fromhex("-0x1.5554a4p-3")),
  f32(float.fromhex("0x1.10c2a2p-7")),
  f32(float.fromhex("-0x1.8b10a4p-13")),
)


def _round_nearest_even(v: float) -> int:
  return int(round(float(v)))


def _sin_poly(a: float, *, fp32_dest: bool = True) -> float:
  a = f32(a)
  s = f32(a * a)
  if fp32_dest:
    c0, c1, c2, c3 = SIN_COEFFS_FP32
    r = f32(c3 * s + c2)
    r = f32(r * s + c1)
  else:
    c0, c1, c2 = SIN_COEFFS_BF16_DEST
    r = f32(c2 * s + c1)
  c = f32(a * s)
  r = f32(r * s + c0)
  return f32(r * c + a)


def blackhole_sine_reference(x: float, *, fp32_dest: bool = True) -> float:
  """Host reference for Blackhole's current SFPU sine algorithm.

  Mirrors ckernel_sfpu_trigonometry.h: four-part Cody-Waite reduction by pi,
  quadrant/sign fold via round(x / pi), then the minimax sine polynomial.
  """
  v = f32(x)
  j_int = _round_nearest_even(f32(v * FRAC_1_PI))
  j = f32(float(j_int))
  a = f32(v + j * SIN_P0)
  a = f32(a + j * SIN_P1)
  a = f32(a + j * SIN_P2)
  a = f32(a + j * SIN_P3)
  if j_int & 1:
    a = f32(-a)
  return _sin_poly(a, fp32_dest=fp32_dest)


def blackhole_cosine_reference(x: float, *, fp32_dest: bool = True) -> float:
  """Host reference for Blackhole's current SFPU cosine algorithm.

  Cosine is reduced to the sine polynomial using an odd pi/2 quadrant index:
  j = 2 * round(x / pi + 0.5) - 1.
  """
  v = f32(x)
  j0 = _round_nearest_even(f32(v * FRAC_1_PI + 0.5))
  j_int = 2 * j0 - 1
  j = f32(float(j_int))
  a = f32(v + j * COS_P0)
  a = f32(a + j * COS_P1)
  a = f32(a + j * COS_P2)
  a = f32(a + j * COS_P3)
  if j0 & 1:
    a = f32(-a)
  return _sin_poly(a, fp32_dest=fp32_dest)


class Sfpu:
  """SFPU helper routines bound to a TRISC math kernel builder.

  This is intentionally a small, explicit layer over dsl.py.  The init methods
  encode the same programmable-constant setup as TT-Metal's Blackhole
  trigonometry LLK.  The polynomial emitter expects its input already range
  reduced into [-pi/2, pi/2] and with the final sign folded into the input.
  The full Cody-Waite reducer needs SFPI disassembly validation before we should
  inline it as raw TTSFP* in this repo.
  """

  def __init__(self, kernel):
    self.k = kernel

  def load_imm32(self, lreg: int | LReg, value: int):
    value &= 0xFFFFFFFF
    self.k.emit(TTSFPLOADI(int(lreg), SfpuLoadIMod.UPPER, value >> 16))
    self.k.emit(TTSFPLOADI(int(lreg), SfpuLoadIMod.LOWER, value & 0xFFFF))
    return self.k

  def load_float(self, lreg: int | LReg, value: float):
    return self.load_imm32(lreg, f32_bits(value))

  def set_config_from_l0(self, dest: int | SfpuConfigDest | LReg):
    self.k.emit(TTSFPCONFIG(0, int(dest), 0))
    return self.k

  def set_program_const(self, dest: int | LReg, value: float):
    self.load_float(LReg.L0, value)
    return self.set_config_from_l0(dest)

  def sine_init(self):
    self.set_program_const(LReg.PRGM0, SIN_P2)
    self.set_program_const(LReg.PRGM1, SIN_P3)
    self.set_program_const(LReg.PRGM2, FRAC_1_PI)
    return self.k

  def cosine_init(self):
    self.set_program_const(LReg.PRGM0, COS_P2)
    self.set_program_const(LReg.PRGM1, COS_P3)
    self.set_program_const(LReg.PRGM2, FRAC_1_PI)
    return self.k

  def emit_mul(self, a: int | LReg, b: int | LReg, out: int | LReg):
    self.k.emit(TTSFPMUL(int(a), int(b), int(LReg.CONST_0), int(out), SFPMAD_MOD1_OFFSET_NONE))
    return self.k

  def emit_mad(self, a: int | LReg, b: int | LReg, c: int | LReg, out: int | LReg):
    self.k.emit(TTSFPMAD(int(a), int(b), int(c), int(out), SFPMAD_MOD1_OFFSET_NONE))
    return self.k

  def sigmoid_appx_init(self):
    """Load Blackhole's LLK approximate-sigmoid LUT constants into L0-L2."""
    self.k.emit(TTSFPLOADI(int(LReg.L0), SfpuLoadIMod.USHORT, 0x3DFF))
    self.k.emit(TTSFPLOADI(int(LReg.L1), SfpuLoadIMod.USHORT, 0x21D8))
    self.k.emit(TTSFPLOADI(int(LReg.L2), SfpuLoadIMod.USHORT, 0xFF10))
    return self.k

  def emit_silu_mul_up_appx_row(
    self,
    *,
    gate_offset: int,
    up_offset: int,
    out_offset: int,
    addr_mode: int = 7,
    gate: int | LReg = LReg.L3,
    up: int | LReg = LReg.L4,
    sig: int | LReg = LReg.L5,
    tmp: int | LReg = LReg.L6,
  ):
    """One SFPU row group of ``silu(gate) * up`` using TT's LUT sigmoid.

    ``gate_offset``/``up_offset``/``out_offset`` are DST-register offsets for
    the current 8-row group. L0-L2 must already contain ``sigmoid_appx_init``'s
    LUT constants.
    """
    self.k.emit(TTSFPLOAD(int(gate), 0, addr_mode, gate_offset))
    self.k.emit(TTSFPLOAD(int(up), 0, addr_mode, up_offset))
    self.k.emit(TTSFPLUT(int(sig), 4, 0))
    self.k.emit(TTSFPADDI(0x3F00, int(sig), 0))  # sigmoid_appx: lut(x) + 0.5
    self.emit_mul(gate, sig, tmp)
    self.emit_mul(tmp, up, tmp)
    self.k.emit(TTSFPSTORE(int(tmp), 0, addr_mode, out_offset))
    self.k.emit(TTSFPNOP())
    return self.k

  def emit_silu_appx_row(
    self,
    *,
    gate_offset: int,
    out_offset: int,
    addr_mode: int = 7,
    gate: int | LReg = LReg.L3,
    sig: int | LReg = LReg.L5,
    tmp: int | LReg = LReg.L6,
  ):
    """One SFPU row group of ``silu(gate)`` using TT's LUT sigmoid.

    ``gate_offset``/``out_offset`` are DST-register offsets for the current
    8-row group. L0-L2 must already contain ``sigmoid_appx_init``'s LUT
    constants.
    """
    self.k.emit(TTSFPLOAD(int(gate), 0, addr_mode, gate_offset))
    self.k.emit(TTSFPLUT(int(sig), 4, 0))
    self.k.emit(TTSFPADDI(0x3F00, int(sig), 0))  # sigmoid_appx: lut(x) + 0.5
    self.emit_mul(gate, sig, tmp)
    self.k.emit(TTSFPSTORE(int(tmp), 0, addr_mode, out_offset))
    self.k.emit(TTSFPNOP())
    return self.k

  def emit_sine_polynomial_reduced(
    self, *,
    a: int | LReg = LReg.L0,
    out: int | LReg = LReg.L0,
    s: int | LReg = LReg.L1,
    r: int | LReg = LReg.L2,
    c: int | LReg = LReg.L3,
    coeff: int | LReg = LReg.L4,
    fp32_dest: bool = True,
  ):
    """Emit the Blackhole sine minimax polynomial for an already-reduced input.

    On entry, ``a`` is the reduced angle with the final sign already applied.
    On exit, ``out`` receives sin(a).  Scratch registers ``s``, ``r``, ``c``,
    and ``coeff`` are clobbered.
    """
    self.emit_mul(a, a, s)

    if fp32_dest:
      c0, c1, c2, c3 = SIN_COEFFS_FP32
      self.load_float(coeff, c3)
      self.load_float(r, c2)
      self.emit_mad(coeff, s, r, r)
      self.load_float(coeff, c1)
      self.emit_mad(r, s, coeff, r)
    else:
      c0, c1, c2 = SIN_COEFFS_BF16_DEST
      self.load_float(r, c2)
      self.load_float(coeff, c1)
      self.emit_mad(r, s, coeff, r)

    self.emit_mul(a, s, c)
    self.load_float(coeff, c0)
    self.emit_mad(r, s, coeff, r)
    self.emit_mad(r, c, a, out)
    self.k.emit(TTSFPNOP())
    return self.k


# ---------------------------------------------------------------------------
# Device-validated transcendental SFPU sequences (exp / reciprocal / sigmoid /
# silu).  Ported from tt-llk's Blackhole bf16-dst paths and validated on device
# by the SFPU transcendental microbench (max_rel ~0.007 for exp over [-10, 2],
# ~0.006 for reciprocal over [0.25, 64]).  These operate purely on LRegs, so the
# caller wraps them with SFPLOAD/SFPSTORE around DEST (see emit_silu_tile).
# ---------------------------------------------------------------------------
def bf16_imm(value: float) -> int:
  return f32_bits(value) >> 16


def sfpu_load_fp32_const(fw, lreg: int, value: float):
  """Load an exact fp32 literal into every lane of an SFPU LReg."""
  bits = f32_bits(value)
  fw.emit(TTSFPLOADI(lreg, int(SfpuLoadIMod.LOWER), bits & 0xFFFF))
  return fw.emit(TTSFPLOADI(lreg, int(SfpuLoadIMod.UPPER), bits >> 16))


def sfpu_load_u32_const(fw, lreg: int, value: int):
  """Load an exact 32-bit bit pattern into every lane of an SFPU LReg."""
  value &= 0xFFFFFFFF
  fw.emit(TTSFPLOADI(lreg, int(SfpuLoadIMod.LOWER), value & 0xFFFF))
  return fw.emit(TTSFPLOADI(lreg, int(SfpuLoadIMod.UPPER), value >> 16))


def _sfpu_scratch_regs(scratch, avoid: set[int], count: int) -> list[int]:
  regs: list[int] = []
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
  """Blackhole bf16-dst natural exp (ports tt-llk `_sfpu_exp_21f_bf16_`)."""
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
  """SFPARECIP seed + Newton-Raphson refinement (tt-llk Blackhole path)."""
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


def sfpu_rsqrt_positive(fw, src_lreg: int, dst_lreg: int, *, scratch=(1, 2, 3, 4, 5, 6, 7)):
  """Blackhole accurate rsqrt core for positive FP32 inputs.

  Mirrors tt-llk's non-legacy ``_calculate_sqrt_body_`` with
  ``RECIPROCAL=true`` and omits the zero/inf/negative special-case branches.
  RMSNorm feeds this with ``mean(x*x)+eps``, so the input is strictly positive
  and finite in the intended path.
  """
  regs = _sfpu_scratch_regs(scratch, {src_lreg, dst_lreg}, 5)
  y, tmp, c1, c2, half = regs

  if src_lreg == dst_lreg:
    x = _sfpu_scratch_regs(scratch, {src_lreg, dst_lreg, y, tmp, c1, c2, half}, 1)[0]
    fw.emit(TTSFPMOV(0, src_lreg, x, 0))
    fw.emit(TTSFPNOP())
  else:
    x = src_lreg

  # y = reinterpret_float(0x5f1110a0 - (reinterpret_uint(x) >> 1))
  fw.emit(TTSFPMOV(0, x, y, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPSHFT(0xFFF, 0, y, 1))  # logical right shift by 1
  fw.emit(TTSFPNOP())
  sfpu_load_u32_const(fw, tmp, 0x5F1110A0)
  fw.emit(TTSFPIADD(0, tmp, y, 6))  # y = magic - y, leave lane flags alone
  fw.emit(TTSFPNOP())

  # Accurate Blackhole refinement:
  #   xy = x*y
  #   c = -y*xy
  #   y = y * (C1 + c * (C2 + c))
  #   xy = x*y
  #   one_minus_xyy = 1 - y*xy
  #   y = one_minus_xyy * (0.5*y) + y
  fw.emit(TTSFPMUL(x, y, int(LReg.CONST_0), tmp, 0))       # tmp = xy
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMUL(y, tmp, int(LReg.CONST_0), tmp, 1))     # tmp = c = -y*xy
  fw.emit(TTSFPNOP())
  sfpu_load_fp32_const(fw, c1, 2.2825186)
  sfpu_load_fp32_const(fw, c2, 2.2533049)
  fw.emit(TTSFPADD(int(LReg.CONST_1), c2, tmp, c2, 0))     # c2 = C2 + c
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMAD(tmp, c2, c1, tmp, 0))                   # tmp = C1 + c*(C2+c)
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMUL(y, tmp, int(LReg.CONST_0), y, 0))       # y refined
  fw.emit(TTSFPNOP())

  fw.emit(TTSFPMUL(x, y, int(LReg.CONST_0), tmp, 0))       # tmp = xy
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMUL(y, tmp, int(LReg.CONST_0), tmp, 1))     # tmp = -y*xy
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPADD(int(LReg.CONST_1), int(LReg.CONST_1), tmp, tmp, 0))  # tmp = 1 - y*xy
  fw.emit(TTSFPNOP())
  sfpu_load_fp32_const(fw, half, 0.5)
  fw.emit(TTSFPMUL(y, half, int(LReg.CONST_0), half, 0))   # half = 0.5*y
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMAD(tmp, half, y, dst_lreg, 0))             # dst = tmp*half + y
  return fw.emit(TTSFPNOP())


def emit_sigmoid(fw, src_lreg: int, dst_lreg: int, *, scratch=(1, 2, 3, 4, 5, 6, 7)):
  """sigmoid(x) = 1 / (1 + exp(-x))."""
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
  """silu(x) = x * sigmoid(x)."""
  regs = [reg for reg in scratch if reg not in {src_lreg, dst_lreg}]
  if len(regs) < 3:
    raise ValueError("emit_silu needs three scratch LRegs")
  x_copy = regs[0]
  fw.emit(TTSFPMOV(0, src_lreg, x_copy, 0))
  emit_sigmoid(fw, src_lreg, dst_lreg, scratch=tuple(regs[1:]) + (x_copy,))
  fw.emit(TTSFPMUL(x_copy, dst_lreg, 9, dst_lreg, 0))
  return fw.emit(TTSFPNOP())


def emit_silu_tile(fw, *, faces: int = 4, groups_per_face: int = 8, addr_mod: int = 7, face_advance: int = 4):
  """DEST <- silu(DEST) over one 32x32 tile (4 faces x 8 row groups)."""
  for _face in range(faces):
    for _group in range(groups_per_face):
      fw.emit(TTSFPLOAD(0, 0, addr_mod, 0))
      emit_silu(fw, 0, 0)
      fw.emit(TTSFPSTORE(0, 0, addr_mod, 0))
      fw.emit(TTSFPNOP())
      fw.emit(TTINCRWC(0, 2, 0, 0))
    fw.emit(TTSETRWC(0, face_advance, 8, 0, 0, face_advance))
    fw.emit(TTSETRWC(0, face_advance, 8, 0, 0, face_advance))
  return fw


__all__ = [
  "FRAC_1_PI", "LReg", "Sfpu", "SfpuConfigDest", "SfpuLoadIMod",
  "blackhole_cosine_reference", "blackhole_sine_reference", "f32", "f32_bits",
  "bf16_imm", "sfpu_load_fp32_const", "sfpu_load_u32_const", "sfpu_exp",
  "sfpu_reciprocal", "sfpu_rsqrt_positive", "emit_sigmoid", "emit_silu",
  "emit_silu_tile",
]
