"""Spec tests for ../specs/fpu-operations.md.

Each test is pinned to one or more clauses from
../clauses/fpu-operations.md via the @spec() marker.

Layout:
  - 19-bit float format conversions
  - ZEROACC modes
  - ZEROSRC modes
  - MVMUL (mat-vec multiply)
  - ELWADD (element-wise add)
  - GMPOOL (global max pool)
  - MOVB2D (SrcB -> Dest)
  - MOVD2A / MOVD2B (Dest -> Src)
  - CLEARDVALID / TRNSPSRCB
  - Dispatcher (TRISC1 opcode routing)
"""

import math
import struct

import pytest
from emu.dsl import decode_tensix
from emu.tensix import TensixCoprocessor
from emu.tensix.fpu import FPU, _19bit_to_float, _float_to_19bit, _float_to_dest, _dest_to_float
from emu.tensix.regfile import SrcRegFile, DestRegFile
from emu.tensix.rwc import RWCState

from .conftest import spec


# Helpers

def _make_fpu():
  srca = SrcRegFile("SrcA")
  srcb = SrcRegFile("SrcB")
  dest = DestRegFile()
  return FPU(srca, srcb, dest), srca, srcb, dest


def _f2b(f):
  return struct.unpack('I', struct.pack('f', float(f)))[0]


def _b2f(b):
  return struct.unpack('f', struct.pack('I', b & 0xFFFFFFFF))[0]


# ===========================================================================
# 19-bit float format
# ===========================================================================

@spec("FPU.FMT.19BIT_LAYOUT", "FPU.FMT.19BIT_TO_FLOAT")
def test_19bit_to_float_layout():
  """sign=bit18, mantissa=bits[17:8], exponent=bits[7:0] maps correctly to FP32."""
  # Build a known 19-bit value: sign=0, mantissa=0x200 (bit 17), exponent=0x7F (bias 127)
  # => 1.0 * 2^(127-127) = 1.0
  # mantissa = 0x200 means bit 17 of 19-bit = bit 9 of mantissa field
  # In FP32: mantissa << 13 = 0x200 << 13 = 0x100_0000, exp=0x7F => bits[22:13] = 0x200
  # Actually let's use a simple case: 2.0 = 0x40000000 in FP32
  # sign=0, exp=0x80 (128), mant=0
  val_fp32 = _f2b(2.0)
  val_19 = _float_to_19bit(2.0)
  assert (val_19 >> 18) & 1 == 0             # sign=0
  assert val_19 & 0xFF == 0x80               # exponent=128
  result = _19bit_to_float(val_19)
  assert abs(result - 2.0) < 1e-5


@spec("FPU.FMT.FLOAT_TO_19BIT")
def test_float_to_19bit_roundtrip():
  """ieee_to_shuffled truncates mantissa to 10 bits; roundtrip preserves sign/exp and top bits."""
  for val in [1.0, -1.0, 0.5, 4.0, -3.14]:
    v19 = _float_to_19bit(val)
    back = _19bit_to_float(v19)
    # Precision loss acceptable (10 vs 23 mantissa bits), but exponent and sign must match
    if val != 0:
      assert math.copysign(1, back) == math.copysign(1, val)
      # Relative error should be small for representable values
      assert abs(back - val) / abs(val) < 0.01


@spec("FPU.FMT.19BIT_NEG_INF")
def test_19bit_neg_inf():
  """Negative-infinity in 19-bit: sign=1, mant=0, exp=0xFF."""
  from emu.tensix.fpu import _NEG_INF_19BIT
  assert (_NEG_INF_19BIT >> 18) & 1 == 1    # sign=1
  assert _NEG_INF_19BIT & 0xFF == 0xFF       # exp=0xFF
  assert (_NEG_INF_19BIT >> 8) & 0x3FF == 0 # mant=0
  assert _19bit_to_float(_NEG_INF_19BIT) == float('-inf')


@spec("FPU.FMT.19BIT_TO_FLOAT")
def test_19bit_nan_encodes():
  """NaN roundtrip through 19-bit encoding — does not preserve NaN (emulator divergence)."""
  val_19 = _float_to_19bit(float('nan'))
  back = _19bit_to_float(val_19)
  assert math.isnan(back)


# ===========================================================================
# ZEROACC
# ===========================================================================

@spec("FPU.ZEROACC.CLR_SPECIFIC", "FPU.ZEROACC.CLEARS_VALID_NOT_BITS")
def test_zeroacc_clr_specific():
  """clear_mode=0: clears valid bit for one row; DstBits unchanged."""
  fpu, _, _, dest = _make_fpu()
  dest.bits[42][0] = 0xDEAD
  dest.valid[42] = True
  # ZEROACC CLR_SPECIFIC = clear_mode=0, where=42
  word = (0x10 << 24) | (0 << 19) | 42
  fpu.zeroacc(decode_tensix(word))
  assert not dest.valid[42]
  assert dest.bits[42][0] == 0xDEAD   # bits untouched


@spec("FPU.ZEROACC.CLR_16")
def test_zeroacc_clr_16():
  """clear_mode=1: clears 16 consecutive rows starting at where."""
  fpu, _, _, dest = _make_fpu()
  for r in range(1024):
    dest.valid[r] = True
  word = (0x10 << 24) | (1 << 19) | 5   # start=5, clear rows 5..20
  fpu.zeroacc(decode_tensix(word))
  for r in range(5, 21):
    assert not dest.valid[r], f"row {r} should be cleared"
  assert dest.valid[4]   # untouched before
  assert dest.valid[21]  # untouched after


@spec("FPU.ZEROACC.CLR_HALF")
def test_zeroacc_clr_half_low():
  """clear_mode=2, where&1=0: clears rows 0-511."""
  fpu, _, _, dest = _make_fpu()
  for r in range(1024):
    dest.valid[r] = True
  word = (0x10 << 24) | (2 << 19) | 0   # where=0 → low half
  fpu.zeroacc(decode_tensix(word))
  assert not any(dest.valid[:512])
  assert all(dest.valid[512:])


@spec("FPU.ZEROACC.CLR_HALF")
def test_zeroacc_clr_half_high():
  """clear_mode=2, where&1=1: clears rows 512-1023."""
  fpu, _, _, dest = _make_fpu()
  for r in range(1024):
    dest.valid[r] = True
  word = (0x10 << 24) | (2 << 19) | 1   # where=1 → high half
  fpu.zeroacc(decode_tensix(word))
  assert all(dest.valid[:512])
  assert not any(dest.valid[512:])


@spec("FPU.ZEROACC.CLR_ALL")
def test_zeroacc_clr_all():
  """clear_mode=3: clears all 1024 valid bits."""
  fpu, _, _, dest = _make_fpu()
  for r in range(1024):
    dest.valid[r] = True
  word = (0x10 << 24) | (3 << 19)
  fpu.zeroacc(decode_tensix(word))
  assert not any(dest.valid)


# ===========================================================================
# ZEROSRC
# ===========================================================================

@spec("FPU.ZEROSRC.CLR_SRCA_ZERO")
def test_zerosrc_srca_zero():
  """ZEROSRC src_mask=1, write_mode=0: fills FPU SrcA bank with 0."""
  fpu, srca, _, _ = _make_fpu()
  bank = srca.banks[srca.fpu_bank]
  bank.rows[3][7] = 0xABCDE  # some non-zero value
  word = (0x11 << 24) | (0 << 3) | 1   # write_mode=0, src_mask=1
  fpu.zerosrc(decode_tensix(word))
  assert bank.rows[3][7] == 0


@spec("FPU.ZEROSRC.CLR_SRCA_NEG_INF")
def test_zerosrc_srca_neg_inf():
  """ZEROSRC src_mask=1, write_mode=1: fills SrcA bank with -inf."""
  fpu, srca, _, _ = _make_fpu()
  bank = srca.banks[srca.fpu_bank]
  word = (0x11 << 24) | (1 << 3) | 1   # write_mode=1, src_mask=1
  fpu.zerosrc(decode_tensix(word))
  assert _19bit_to_float(bank.rows[0][0]) == float('-inf')
  assert _19bit_to_float(bank.rows[63][15]) == float('-inf')


@spec("FPU.ZEROSRC.CLR_SRCB_ZERO")
def test_zerosrc_srcb_zero():
  """ZEROSRC src_mask=2: fills SrcB bank with 0 (never -inf)."""
  fpu, _, srcb, _ = _make_fpu()
  bank = srcb.banks[srcb.fpu_bank]
  bank.rows[0][0] = 0xBEEF
  word = (0x11 << 24) | (1 << 3) | 2   # write_mode=1, src_mask=2 (srcb only)
  fpu.zerosrc(decode_tensix(word))
  assert bank.rows[0][0] == 0    # SrcB always gets zero


# ===========================================================================
# MVMUL
# ===========================================================================

@spec("FPU.MVMUL.DST_EQUALS_SRCB_AT_SRCA", "FPU.MVMUL.SETS_DEST_VALID")
def test_mvmul_basic():
  """MVMUL: Dst += SrcB @ SrcA; dest rows marked valid."""
  fpu, srca, srcb, dest = _make_fpu()
  rwc = RWCState()
  srca_bank = srca.banks[srca.fpu_bank]
  srcb_bank = srcb.banks[srcb.fpu_bank]
  # Identity-like SrcA: diagonal 1.0
  for r in range(16):
    for c in range(16):
      srca_bank.rows[r][c] = _float_to_19bit(1.0 if r == c else 0.0)
  # SrcB: each row = constant value (row+1)
  for r in range(8):
    for c in range(16):
      srcb_bank.rows[r][c] = _float_to_19bit(float(r + 1))
  word = (0x26 << 24) | 0
  fpu.mvmul(decode_tensix(word), rwc)
  for r in range(8):
    assert dest.valid[r]
    expected = float(r + 1)
    actual = _dest_to_float(dest.bits[r][r])
    assert abs(actual - expected) < 0.2, f"row {r}: {actual} != {expected}"


@spec("FPU.MVMUL.ACCUMULATES_INTO_DEST")
def test_mvmul_accumulates():
  """MVMUL accumulates into already-valid dest rows."""
  fpu, srca, srcb, dest = _make_fpu()
  rwc = RWCState()
  srca_bank = srca.banks[srca.fpu_bank]
  srcb_bank = srcb.banks[srcb.fpu_bank]
  for r in range(16):
    srca_bank.rows[r][r] = _float_to_19bit(1.0)
  for r in range(8):
    for c in range(16):
      srcb_bank.rows[r][c] = _float_to_19bit(1.0)
  word = (0x26 << 24) | 0
  fpu.mvmul(decode_tensix(word), rwc)
  first = _dest_to_float(dest.bits[0][0])
  fpu.mvmul(decode_tensix(word), rwc)
  second = _dest_to_float(dest.bits[0][0])
  assert abs(second - first * 2) < 0.2   # accumulation doubled the value


@spec("FPU.MVMUL.RWC_ADDRESSING")
def test_mvmul_rwc_dst_offset():
  """MVMUL: d.dst + rwc.d*16 selects the dest row base."""
  fpu, srca, srcb, dest = _make_fpu()
  rwc = RWCState()
  rwc.d = 2   # dest base = 2*16 = 32
  srca_bank = srca.banks[srca.fpu_bank]
  srcb_bank = srcb.banks[srcb.fpu_bank]
  for r in range(16):
    srca_bank.rows[r][r] = _float_to_19bit(1.0)
  for r in range(8):
    for c in range(16):
      srcb_bank.rows[r][c] = _float_to_19bit(5.0)
  # dst field=0, rwc.d=2 -> dst_base=32
  word = (0x26 << 24) | 0
  fpu.mvmul(decode_tensix(word), rwc)
  for r in range(8):
    assert dest.valid[32 + r]


# ===========================================================================
# ELWADD
# ===========================================================================

@spec("FPU.ELWADD.ELEMENT_WISE_ADD", "FPU.ELWADD.SETS_DEST_VALID")
def test_elwadd_simple():
  """ELWADD: element-wise SrcA + SrcB into Dest (no accumulation)."""
  fpu, srca, srcb, dest = _make_fpu()
  rwc = RWCState()
  srca_bank = srca.banks[srca.fpu_bank]
  srcb_bank = srcb.banks[srcb.fpu_bank]
  for col in range(16):
    srca_bank.rows[0][col] = _float_to_19bit(float(col))
    srcb_bank.rows[0][col] = _float_to_19bit(float(col * 10))
  word = (0x28 << 24) | (0 << 21) | 0
  fpu.elwadd(decode_tensix(word), rwc)
  for col in range(16):
    expected = float(col * 11)
    actual = _dest_to_float(dest.bits[0][col])
    assert abs(actual - expected) < 0.01, f"col {col}: {actual} != {expected}"
    assert dest.valid[0]


@spec("FPU.ELWADD.DEST_ACCUM_EN")
def test_elwadd_accumulate():
  """ELWADD dest_accum_en=1: adds prior valid dest value to result."""
  fpu, srca, srcb, dest = _make_fpu()
  rwc = RWCState()
  dest.bits[0][0] = _float_to_dest(100.0)
  dest.valid[0] = True
  srca.banks[srca.fpu_bank].rows[0][0] = _float_to_19bit(1.0)
  srcb.banks[srcb.fpu_bank].rows[0][0] = _float_to_19bit(2.0)
  word = (0x28 << 24) | (1 << 21) | 0   # dest_accum_en=1
  fpu.elwadd(decode_tensix(word), rwc)
  actual = _dest_to_float(dest.bits[0][0])
  assert abs(actual - 103.0) < 0.01


@spec("FPU.ELWADD.RWC_ADDRESSING")
def test_elwadd_rwc_dest_offset():
  """ELWADD uses d.dst + rwc.d*16 to pick the destination row base."""
  fpu, srca, srcb, dest = _make_fpu()
  rwc = RWCState()
  rwc.d = 1   # dest base = 1*16 = 16
  srca_bank = srca.banks[srca.fpu_bank]
  srcb_bank = srcb.banks[srcb.fpu_bank]
  for r in range(16):
    for c in range(16):
      srca_bank.rows[r][c] = _float_to_19bit(1.0)
      srcb_bank.rows[r][c] = _float_to_19bit(1.0)
  word = (0x28 << 24) | 0
  fpu.elwadd(decode_tensix(word), rwc)
  for r in range(16):
    assert dest.valid[16 + r]
  assert not dest.valid[0]  # row 0 not written


# ===========================================================================
# GMPOOL
# ===========================================================================

@spec("FPU.GMPOOL.COLUMN_WISE_MAX", "FPU.GMPOOL.INITIALIZES_ON_INVALID",
      "FPU.GMPOOL.SETS_DEST_VALID")
def test_gmpool_first_pass():
  """GMPOOL first pass (invalid dest): initializes from SrcA column max."""
  fpu, srca, _, dest = _make_fpu()
  rwc = RWCState()
  srca_bank = srca.banks[srca.fpu_bank]
  # Row 0 col 0 = 5.0; row 1 col 0 = 3.0; max = 5.0
  srca_bank.rows[0][0] = _float_to_19bit(5.0)
  srca_bank.rows[1][0] = _float_to_19bit(3.0)
  word = (0x33 << 24) | 0
  fpu.gmpool(decode_tensix(word), rwc)
  assert dest.valid[0]
  assert abs(_dest_to_float(dest.bits[0][0]) - 5.0) < 0.1


@spec("FPU.GMPOOL.ACCUMULATES_MAX")
def test_gmpool_accumulate_max():
  """GMPOOL second pass: keeps max of new SrcA values and prior dest value."""
  fpu, srca, _, dest = _make_fpu()
  rwc = RWCState()
  srca_bank = srca.banks[srca.fpu_bank]
  srca_bank.rows[0][0] = _float_to_19bit(1.0)
  word = (0x33 << 24) | 0
  fpu.gmpool(decode_tensix(word), rwc)
  # First pass: dest[0][0] = 1.0
  srca_bank.rows[0][0] = _float_to_19bit(7.0)
  fpu.gmpool(decode_tensix(word), rwc)
  # Second pass: max(1.0, 7.0) = 7.0
  assert abs(_dest_to_float(dest.bits[0][0]) - 7.0) < 0.1


@spec("FPU.GMPOOL.ACCUMULATES_MAX")
def test_gmpool_keeps_higher_dest():
  """GMPOOL: keeps prior dest value when it exceeds new SrcA value."""
  fpu, srca, _, dest = _make_fpu()
  rwc = RWCState()
  srca_bank = srca.banks[srca.fpu_bank]
  srca_bank.rows[0][1] = _float_to_19bit(10.0)
  word = (0x33 << 24) | 0
  fpu.gmpool(decode_tensix(word), rwc)
  assert abs(_dest_to_float(dest.bits[0][1]) - 10.0) < 0.1
  # Now SrcA has a smaller value
  srca_bank.rows[0][1] = _float_to_19bit(2.0)
  fpu.gmpool(decode_tensix(word), rwc)
  # max(10.0, 2.0) = 10.0 — dest unchanged
  assert abs(_dest_to_float(dest.bits[0][1]) - 10.0) < 0.1


# ===========================================================================
# MOVB2D
# ===========================================================================

@spec("FPU.MOVB2D.MOV_1_ROW", "FPU.MOVB2D.CONVERTS_19BIT_TO_DEST",
      "FPU.MOVB2D.SETS_DEST_VALID")
def test_movb2d_1_row():
  """MOVB2D instr_mod=0: copies 1 SrcB row to Dest, converting 19-bit to FP32."""
  fpu, _, srcb, dest = _make_fpu()
  rwc = RWCState()
  srcb_bank = srcb.banks[srcb.fpu_bank]
  srcb_bank.rows[0][0] = _float_to_19bit(42.0)
  srcb_bank.rows[0][1] = _float_to_19bit(99.0)
  # MOVB2D: src=0, dst=0, instr_mod=0 (1 row)
  word = (0x13 << 24) | (0 << 17) | (0 << 11) | 0
  fpu.movb2d(decode_tensix(word), rwc)
  assert dest.valid[0]
  assert abs(_dest_to_float(dest.bits[0][0]) - 42.0) < 0.5
  assert abs(_dest_to_float(dest.bits[0][1]) - 99.0) < 0.5


@spec("FPU.MOVB2D.MOV_4_ROWS")
def test_movb2d_4_rows():
  """MOVB2D instr_mod=1: copies 4 SrcB rows to Dest."""
  fpu, _, srcb, dest = _make_fpu()
  rwc = RWCState()
  srcb_bank = srcb.banks[srcb.fpu_bank]
  for r in range(4):
    srcb_bank.rows[r][0] = _float_to_19bit(float(r + 10))
  word = (0x13 << 24) | (0 << 17) | (1 << 11) | 0   # instr_mod=1 -> 4 rows
  fpu.movb2d(decode_tensix(word), rwc)
  for r in range(4):
    assert dest.valid[r]
    assert abs(_dest_to_float(dest.bits[r][0]) - float(r + 10)) < 0.5


@spec("FPU.MOVB2D.MOV_8_ROWS")
def test_movb2d_8_rows():
  """MOVB2D instr_mod=2: copies 8 SrcB rows to Dest."""
  fpu, _, srcb, dest = _make_fpu()
  rwc = RWCState()
  srcb_bank = srcb.banks[srcb.fpu_bank]
  for r in range(8):
    srcb_bank.rows[r][0] = _float_to_19bit(float(r + 1))
  word = (0x13 << 24) | (0 << 17) | (2 << 11) | 0   # instr_mod=2 -> 8 rows
  fpu.movb2d(decode_tensix(word), rwc)
  for r in range(8):
    assert dest.valid[r]


# ===========================================================================
# MOVD2A / MOVD2B
# ===========================================================================

@spec("FPU.MOVD2A.MOV_1_ROW", "FPU.MOVD2A.CONVERTS_DEST_TO_19BIT")
def test_movd2a_1_row():
  """MOVD2A instr_mod=0: copies 1 Dest row to SrcA, converting FP32 to 19-bit."""
  fpu, srca, _, dest = _make_fpu()
  rwc = RWCState()
  dest.bits[0][0] = _float_to_dest(77.0)
  dest.valid[0] = True
  # MOVD2A: src=0, dst=0, instr_mod=0 (1 row)
  word = (0x08 << 24) | (0 << 17) | (0 << 12) | 0
  fpu.movd2a(decode_tensix(word), rwc)
  srca_bank = srca.banks[srca.fpu_bank]
  actual = _19bit_to_float(srca_bank.rows[0][0])
  assert abs(actual - 77.0) < 1.5   # some precision loss in 19-bit


@spec("FPU.MOVD2A.READS_ZERO_WHEN_INVALID")
def test_movd2a_reads_zero_from_invalid():
  """MOVD2A: reads 0.0 from invalid dest rows."""
  fpu, srca, _, dest = _make_fpu()
  rwc = RWCState()
  dest.bits[0][0] = _float_to_dest(100.0)  # bits set but valid=False
  dest.valid[0] = False
  word = (0x08 << 24) | 0
  fpu.movd2a(decode_tensix(word), rwc)
  srca_bank = srca.banks[srca.fpu_bank]
  actual = _19bit_to_float(srca_bank.rows[0][0])
  assert actual == 0.0


@spec("FPU.MOVD2B.MOVES_TO_SRCB")
def test_movd2b_1_row():
  """MOVD2B instr_mod=0: copies 1 Dest row to SrcB."""
  fpu, _, srcb, dest = _make_fpu()
  rwc = RWCState()
  dest.bits[0][0] = _float_to_dest(55.0)
  dest.valid[0] = True
  word = (0x0A << 24) | (0 << 17) | (0 << 12) | 0
  fpu.movd2b(decode_tensix(word), rwc)
  srcb_bank = srcb.banks[srcb.fpu_bank]
  actual = _19bit_to_float(srcb_bank.rows[0][0])
  assert abs(actual - 55.0) < 1.5


# ===========================================================================
# CLEARDVALID
# ===========================================================================

@spec("FPU.CLEARDVALID.RELEASES_SRCA")
def test_cleardvalid_srca():
  """CLEARDVALID bit0: releases SrcA bank from matrix_unit back to unpackers."""
  fpu, srca, _, _ = _make_fpu()
  srca.flip_to_fpu()
  assert srca.banks[0].allowed_client == "matrix_unit"
  word = (0x36 << 24) | (1 << 22)   # cleardvalid bit 0
  fpu.cleardvalid(decode_tensix(word))
  assert srca.banks[0].allowed_client == "unpackers"


@spec("FPU.CLEARDVALID.RELEASES_SRCB")
def test_cleardvalid_srcb():
  """CLEARDVALID bit1: releases SrcB bank back to unpackers."""
  fpu, _, srcb, _ = _make_fpu()
  srcb.flip_to_fpu()
  assert srcb.banks[0].allowed_client == "matrix_unit"
  word = (0x36 << 24) | (2 << 22)   # cleardvalid bit 1
  fpu.cleardvalid(decode_tensix(word))
  assert srcb.banks[0].allowed_client == "unpackers"


# ===========================================================================
# TRNSPSRCB
# ===========================================================================

@spec("FPU.TRNSPSRCB.TRANSPOSES_ROWS_16_31", "FPU.TRNSPSRCB.ROWS_0_15_UNCHANGED")
def test_trnspsrcb():
  """TRNSPSRCB: transposes rows 16–31 in place; rows 0–15 are unchanged."""
  fpu, _, srcb, _ = _make_fpu()
  bank = srcb.banks[srcb.fpu_bank]
  # Set rows 16-31 to pattern: bank[16+r][c] = r*16 + c
  for r in range(16):
    for c in range(16):
      bank.rows[16 + r][c] = r * 16 + c
  # Set rows 0-15 to sentinels
  for r in range(16):
    for c in range(16):
      bank.rows[r][c] = 0xBEEF
  word = (0x16 << 24)
  fpu.trnspsrcb(decode_tensix(word))
  # After transpose: bank[16+r][c] should equal c*16 + r
  for r in range(16):
    for c in range(16):
      assert bank.rows[16 + r][c] == c * 16 + r
  # Rows 0–15 untouched
  for r in range(16):
    assert bank.rows[r][0] == 0xBEEF


# ===========================================================================
# TRISC1 dispatcher
# ===========================================================================

@spec("FPU.ZEROACC.CLR_ALL", "FPU.MVMUL.DISPATCHED_BY_TRISC1")
def test_trisc1_zeroacc_pipeline():
  """ZEROACC CLR_ALL dispatched through TRISC1 pipeline clears all dest valid bits."""
  c = TensixCoprocessor()
  for r in range(100):
    c.dest.valid[r] = True
  word = (0x10 << 24) | (3 << 19)
  c.push_instruction(1, word)
  c.step()
  assert not any(c.dest.valid)


@spec("FPU.ELWADD.DISPATCHED_BY_TRISC1")
def test_trisc1_elwadd_pipeline():
  """ELWADD dispatched through TRISC1 pipeline writes correct sum to Dest."""
  c = TensixCoprocessor()
  c.srca.banks[c.srca.fpu_bank].rows[0][0] = _float_to_19bit(3.0)
  c.srcb.banks[c.srcb.fpu_bank].rows[0][0] = _float_to_19bit(7.0)
  word = (0x28 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  assert abs(_dest_to_float(c.dest.bits[0][0]) - 10.0) < 0.1


@spec("FPU.GMPOOL.DISPATCHED_BY_TRISC1")
def test_trisc1_gmpool_pipeline():
  """GMPOOL dispatched through TRISC1 pipeline computes column max."""
  c = TensixCoprocessor()
  c.srca.banks[c.srca.fpu_bank].rows[0][5] = _float_to_19bit(99.0)
  c.srca.banks[c.srca.fpu_bank].rows[1][5] = _float_to_19bit(42.0)
  word = (0x33 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  assert abs(_dest_to_float(c.dest.bits[0][5]) - 99.0) < 0.5


@spec("FPU.SETRWC.DISPATCHED_BY_TRISC1")
def test_trisc1_setrwc_pipeline():
  """SETRWC dispatched via TRISC1 sets the correct rwc.d value."""
  c = TensixCoprocessor()
  word = (0x37 << 24) | (0 << 22) | (0 << 18) | (5 << 14) | (0 << 10) | (0 << 6) | 0x04
  c.push_instruction(1, word)
  c.step()
  assert c.rwc[1].d == 5


@spec("FPU.INCRWC.DISPATCHED_BY_TRISC1")
def test_trisc1_incrwc_pipeline():
  """INCRWC dispatched via TRISC1 increments the rwc.a counter."""
  c = TensixCoprocessor()
  # INCRWC: a+=3
  word = (0x38 << 24) | (0 << 18) | (0 << 14) | (0 << 10) | (3 << 6)
  c.push_instruction(1, word)
  c.step()
  assert c.rwc[1].a == 3
