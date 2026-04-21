"""Spec tests for ../specs/specialty-fpu-operations.md.

All opcodes covered here are NOT implemented in the emulator's TRISC1Decoder.
Each test is marked xfail(strict=True) pointing to fpu.py / trisc1.py as the
location where the implementation would need to go.

Layout:
  - Neutered instructions (CONV3S1/S2, APOOL3S1/S2, MPOOL3S1/S2)
  - DOTPV (backward-compat MVMUL)
  - GAPOOL (half-height matmul)
  - GATESRCRST (operand-cache invalidate)
  - CLREXPHIST (exponent histogram reset)
  - SHIFTXA / SHIFTXB (lane shift ops)
"""

import pytest
from emu.dsl import decode_tensix
from emu.tensix import TensixCoprocessor
from emu.tensix.fpu import _float_to_19bit, _dest_to_float

from .conftest import spec


def _make_coproc():
  return TensixCoprocessor()


# ===========================================================================
# Neutered instructions — dispatch without error, Dst unchanged (passing tests)
#
# These opcodes are hardware-neutered (no-op by hardware design).  The
# emulator's silent-ignore of unknown opcodes matches the spec expectation:
# no state change, no exception.  These are therefore PASSING tests.
# ===========================================================================

@spec("SFPU.CONV3S1.NEUTERED")
def test_conv3s1_is_noop():
  """CONV3S1 (0x22) neutered: dispatches without error, Dst unchanged."""
  c = _make_coproc()
  c.dest.bits[0][0] = 0x1234
  c.dest.valid[0] = True
  word = (0x22 << 24) | 0
  c.push_instruction(1, word)
  c.step()   # must not raise
  assert c.dest.bits[0][0] == 0x1234


@spec("SFPU.CONV3S2.NEUTERED")
def test_conv3s2_is_noop():
  """CONV3S2 (0x23) neutered: dispatches without error."""
  c = _make_coproc()
  c.dest.bits[0][0] = 0xABCD
  c.dest.valid[0] = True
  word = (0x23 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  assert c.dest.bits[0][0] == 0xABCD


@spec("SFPU.APOOL3S1.NEUTERED")
def test_apool3s1_is_noop():
  """APOOL3S1 (0x25) neutered: Dst unchanged."""
  c = _make_coproc()
  c.dest.bits[0][0] = 0xFEED
  c.dest.valid[0] = True
  word = (0x25 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  assert c.dest.bits[0][0] == 0xFEED


@spec("SFPU.APOOL3S2.NEUTERED")
def test_apool3s2_is_noop():
  """APOOL3S2 (0x32) neutered: Dst unchanged."""
  c = _make_coproc()
  c.dest.bits[0][0] = 0xDEAD
  c.dest.valid[0] = True
  word = (0x32 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  assert c.dest.bits[0][0] == 0xDEAD


@spec("SFPU.MPOOL3S1.NEUTERED")
def test_mpool3s1_is_noop():
  """MPOOL3S1 (0x24) neutered: side-effects only, no data change."""
  c = _make_coproc()
  c.dest.bits[0][0] = 0x1111
  c.dest.valid[0] = True
  word = (0x24 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  assert c.dest.bits[0][0] == 0x1111


@spec("SFPU.MPOOL3S2.NEUTERED")
def test_mpool3s2_is_noop():
  """MPOOL3S2 (0x31) neutered: side-effects only."""
  c = _make_coproc()
  c.dest.bits[0][0] = 0x2222
  c.dest.valid[0] = True
  word = (0x31 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  assert c.dest.bits[0][0] == 0x2222


# ===========================================================================
# DOTPV — backward-compatible MVMUL
# ===========================================================================

@spec("SFPU.DOTPV.IDENTICAL_TO_MVMUL")
def test_dotpv_behaves_like_mvmul():
  """DOTPV (0x29) identical to MVMUL without broadcast; produces matmul result."""
  c = _make_coproc()
  srca_bank = c.srca.banks[c.srca.fpu_bank]
  srcb_bank = c.srcb.banks[c.srcb.fpu_bank]
  for r in range(16):
    srca_bank.rows[r][r] = _float_to_19bit(1.0)
  for r in range(8):
    for col in range(16):
      srcb_bank.rows[r][col] = _float_to_19bit(2.0)
  word = (0x29 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  assert c.dest.valid[0]
  assert abs(_dest_to_float(c.dest.bits[0][0]) - 2.0) < 0.2


# ===========================================================================
# GAPOOL — half-height matmul
# ===========================================================================

@spec("SFPU.GAPOOL.HALF_HEIGHT_MVMUL")
def test_gapool_4_row_output():
  """GAPOOL (0x34): produces 4-row output (not 8 like MVMUL)."""
  c = _make_coproc()
  srca_bank = c.srca.banks[c.srca.fpu_bank]
  srcb_bank = c.srcb.banks[c.srcb.fpu_bank]
  for r in range(16):
    srca_bank.rows[r][r] = _float_to_19bit(1.0)
  for r in range(4):
    for col in range(16):
      srcb_bank.rows[r][col] = _float_to_19bit(3.0)
  word = (0x34 << 24) | 0
  c.push_instruction(1, word)
  c.step()
  # Only rows 0..3 should be written
  for r in range(4):
    assert c.dest.valid[r]
  for r in range(4, 8):
    assert not c.dest.valid[r]


# ===========================================================================
# GATESRCRST — SrcB operand-cache invalidate
# ===========================================================================

@spec("SFPU.GATESRCRST.INVALIDATES_SRCB_CACHE")
def test_gatesrcrst_dispatches():
  """GATESRCRST (0x35): invalidates SrcB operand cache — not modeled in emulator."""
  pytest.fail(
    "SFPU.GATESRCRST.INVALIDATES_SRCB_CACHE not implemented: "
    "emulator has no operand cache; GATESRCRST is silently ignored")


# ===========================================================================
# CLREXPHIST — exponent histogram reset
# ===========================================================================

@spec("SFPU.CLREXPHIST.RESETS_HISTOGRAMS")
def test_clrexphist_dispatches():
  """CLREXPHIST (0x21): resets exponent histogram — not modeled in emulator."""
  pytest.fail(
    "SFPU.CLREXPHIST.RESETS_HISTOGRAMS not implemented: "
    "emulator has no exponent histogram state; CLREXPHIST is silently ignored")


# ===========================================================================
# SHIFTXA / SHIFTXB — lane-shift ops
# ===========================================================================

@spec("SFPU.SHIFTXA.SHIFTS_16_SRCA_ROWS")
def test_shiftxa_shifts_right():
  """SHIFTXA direction=2 (right): col 0 filled with 0; others shift right."""
  c = _make_coproc()
  bank = c.srca.banks[c.srca.fpu_bank]
  for col in range(16):
    bank.rows[0][col] = _float_to_19bit(float(col + 1))
  word = (0x17 << 24) | 2   # direction=right
  c.push_instruction(1, word)
  c.step()
  # After shift right: col 0 = 0, col 1 = old col 0 = 1.0, col 15 = old col 14
  from emu.tensix.fpu import _19bit_to_float
  assert bank.rows[0][0] == 0
  assert abs(_19bit_to_float(bank.rows[0][1]) - 1.0) < 0.5


@spec("SFPU.SHIFTXB.SHIFTS_ONE_SRCB_ROW")
def test_shiftxb_shift_with_zero():
  """SHIFTXB ShiftInZero=1: shifts row left, rightmost lane filled with 0."""
  c = _make_coproc()
  bank = c.srcb.banks[c.srcb.fpu_bank]
  for col in range(16):
    bank.rows[0][col] = _float_to_19bit(float(col + 1))
  # SHIFTXB: addr_mode=0, ShiftInZero=1, SrcRow=0
  word = (0x18 << 24) | (1 << 10)
  c.push_instruction(1, word)
  c.step()
  from emu.tensix.fpu import _19bit_to_float
  # After left shift: col 0 = old col 1 = 2.0; col 15 = 0
  assert abs(_19bit_to_float(bank.rows[0][0]) - 2.0) < 0.5
  assert bank.rows[0][15] == 0
