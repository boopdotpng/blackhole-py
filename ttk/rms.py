"""Reusable FP32 row-reduction and RMS scaling programs for the SFPU."""

import struct

from ttk.sfpu import LReg, SfpuFormat, SfpuProgram
from ttk.tensix import tt_word


BF16 = int(SfpuFormat.BF16)
FP32 = int(SfpuFormat.FP32)
CONST_0 = 9
CONST_1 = 10


class _Builder:
  def __init__(self): self.words = []
  def emit(self, opcode, *args): self.words.append(tt_word(opcode, *args)); return self
  def finish(self): return SfpuProgram(tuple(self.words))


def _load_float(p, reg, value):
  bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
  p.emit("TTSFPLOADI", reg, 10, bits & 0xFFFF)
  p.emit("TTSFPLOADI", reg, 8, bits >> 16)


def _add(p, dst, src): p.emit("TTSFPADD", dst, CONST_1, src, dst, 0)
def _mul(p, lhs, rhs, dst, mod=0): p.emit("TTSFPMUL", lhs, rhs, CONST_0, dst, mod)


def _horizontal_sum_pair(p):
  """Fold the eight lanes in L0 and L4 into lane zero."""
  for shifts in (4, 2, 1):
    p.emit("TTSFPMOV", 0, 0, 1, 0).emit("TTSFPMOV", 0, 4, 5, 0)
    for _ in range(shifts):
      # Blackhole's cross-lane shuffle accepts only an SFPNOP on the next
      # cycle.  Making that bubble explicit is both faster than the automatic
      # interlock and avoids depending on issue timing from the calling RISC.
      p.emit("TTSFPSHFT2", 0, 1, 1, 3).emit("TTSFPNOP")
      p.emit("TTSFPSHFT2", 0, 5, 5, 3).emit("TTSFPNOP")
    _add(p, 0, 1); _add(p, 4, 5)


def row_square_sum(*, input_base=0, accumulator_base=768, accumulate=True):
  """Return a program that adds one BF16 tile's per-row sum-of-squares.

  The persistent accumulator is FP32 even though the source tile is BF16.
  Only the row-reduction slots of the accumulator tile are meaningful.
  """
  p = _Builder()
  for face_pair in range(2):
    face = face_pair * 32
    for row in (0, 8):
      first, second = face + row, face + row + 4
      offsets = (first, first + 2, first + 16, first + 18,
                 second, second + 2, second + 16, second + 18)
      for reg, offset in enumerate(offsets): p.emit("TTSFPLOAD", reg, BF16, 7, input_base + offset)
      for reg in range(8): _mul(p, reg, reg, reg)
      _add(p, 2, 3); _add(p, 6, 7)
      _add(p, 1, 2); _add(p, 5, 6)
      _add(p, 0, 1); _add(p, 4, 5)
      _horizontal_sum_pair(p)
      if accumulate:
        p.emit("TTSFPLOAD", 1, FP32, 7, accumulator_base + first)
        p.emit("TTSFPLOAD", 5, FP32, 7, accumulator_base + second)
        _add(p, 0, 1); _add(p, 4, 5)
      p.emit("TTSFPSTORE", 0, FP32, 7, accumulator_base + first)
      p.emit("TTSFPSTORE", 4, FP32, 7, accumulator_base + second)
  return p.finish()


def _rsqrt_positive(p, src=0, dst=0):
  """Accurate Blackhole rsqrt for a finite positive FP32 LReg."""
  x, y, tmp, c1, c2, half = 6, 1, 2, 3, 4, 5
  p.emit("TTSFPMOV", 0, src, x, 0).emit("TTSFPNOP")
  p.emit("TTSFPMOV", 0, x, y, 0).emit("TTSFPNOP")
  p.emit("TTSFPSHFT", 0xFFF, 0, y, 1).emit("TTSFPNOP")
  bits = 0x5F1110A0
  p.emit("TTSFPLOADI", tmp, 10, bits & 0xFFFF).emit("TTSFPLOADI", tmp, 8, bits >> 16)
  p.emit("TTSFPIADD", 0, tmp, y, 6).emit("TTSFPNOP")
  _mul(p, x, y, tmp); p.emit("TTSFPNOP")
  _mul(p, y, tmp, tmp, 1); p.emit("TTSFPNOP")
  _load_float(p, c1, 2.2825186); _load_float(p, c2, 2.2533049)
  p.emit("TTSFPADD", CONST_1, c2, tmp, c2, 0).emit("TTSFPNOP")
  p.emit("TTSFPMAD", tmp, c2, c1, tmp, 0).emit("TTSFPNOP")
  _mul(p, y, tmp, y); p.emit("TTSFPNOP")
  _mul(p, x, y, tmp); p.emit("TTSFPNOP")
  _mul(p, y, tmp, tmp, 1); p.emit("TTSFPNOP")
  p.emit("TTSFPADD", CONST_1, CONST_1, tmp, tmp, 0).emit("TTSFPNOP")
  _load_float(p, half, 0.5); _mul(p, y, half, half); p.emit("TTSFPNOP")
  p.emit("TTSFPMAD", tmp, half, y, dst, 0).emit("TTSFPNOP")


def finalize_rms(*, accumulator_base=768, width, epsilon):
  """Scale row sums by ``1 / width``, add epsilon, and apply FP32 rsqrt."""
  if type(width) is not int or width <= 0: raise ValueError("RMS width must be positive")
  p = _Builder()
  for face in (0, 32):
    for row in (0, 4, 8, 12):
      offset = accumulator_base + face + row
      # Accurate rsqrt uses every ordinary LReg, so reload these exact FP32
      # constants for each row group instead of silently narrowing them.
      _load_float(p, 7, 1.0 / width); _load_float(p, 6, epsilon)
      p.emit("TTSFPLOAD", 0, FP32, 7, offset)
      _mul(p, 0, 7, 0); _add(p, 0, 6)
      _rsqrt_positive(p)
      p.emit("TTSFPSTORE", 0, FP32, 7, offset)
  return p.finish()


def apply_rms(*, input_base=0, accumulator_base=768, output_base=0):
  """Apply FP32 row scales and round the normalized tile to BF16."""
  p = _Builder()
  chunks = (0, 2, 16, 18)
  for face in (0, 32):
    for row in (0, 4, 8, 12):
      scale = accumulator_base + face + row
      for chunk in chunks:
        offset = face + row + chunk
        p.emit("TTSFPLOAD", 0, BF16, 7, input_base + offset)
        p.emit("TTSFPLOAD", 1, FP32, 7, scale)
        _mul(p, 0, 1, 0)
        p.emit("TTSFPSTORE", 0, BF16, 7, output_base + offset)
  return p.finish()


def token_square_accumulate():
  """Accumulate one complete BF16 tile's squares lane-wise into L7."""
  return SfpuProgram((
    tt_word("TTSFPLOAD", int(LReg.L0), BF16, 7, 0), tt_word("TTSFPNOP"),
    tt_word("TTSFPMUL", int(LReg.L0), int(LReg.L0), CONST_0, int(LReg.L0), 0),
    tt_word("TTSFPNOP"),
    tt_word("TTSFPADD", CONST_1, int(LReg.L7), int(LReg.L0), int(LReg.L7), 0),
    tt_word("TTSFPNOP"), tt_word("TTINCRWC", 0, 2, 0, 0),
  ))


def token_apply_rms_weight(*, input_base=0, weight_base=64, output_base=0,
                           scale=LReg.L0):
  """Apply a live SFPU scalar and an elementwise weight tile to one BF16 tile."""
  nop = tt_word("TTSFPNOP")
  return SfpuProgram((
    tt_word("TTSFPLOAD", int(LReg.L1), BF16, 7, input_base),
    tt_word("TTSFPLOAD", int(LReg.L2), BF16, 7, weight_base), nop, nop,
    tt_word("TTSFPMUL", int(LReg.L1), int(scale), CONST_0, int(LReg.L1), 0),
    nop, nop, nop,
    tt_word("TTSFPMUL", int(LReg.L1), int(LReg.L2), CONST_0, int(LReg.L1), 0),
    nop, nop, nop,
    tt_word("TTSFPSTORE", int(LReg.L1), BF16, 7, output_base),
    nop, tt_word("TTINCRWC", 0, 2, 0, 0),
  ))
