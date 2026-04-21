"""Spec tests for ../specs/additional-scalar-unit-instructions.md.

SHIFTDMAREG, BITWOPDMAREG, CMPDMAREG, and FLUSHDMA are all absent from the
emulator's DSL (dsl.py) and dispatch table (tensix/__init__.py). Every test
in this file is xfail(strict=True) to document the unimplemented coverage.
"""

import pytest

from .conftest import spec


# ===========================================================================
# SHIFTDMAREG
# ===========================================================================

@spec("ASUI.SHIFTDMAREG.LEFT")
def test_shiftdmareg_left():
  """SHIFTDMAREG Mode=0: Result = (Left << Right) & 0xFFFFFFFF."""
  from emu.tensix import GPRFile, ScalarUnit
  gpr = GPRFile()
  gpr.write32(0, 1, 0x00000001)
  gpr.write32(0, 2, 4)
  # encode: opcode=0x5C, Mode=0, result=3, opB=2, opA=1
  word = (0x5C << 24) | (0 << 18) | (3 << 12) | (2 << 6) | 1
  from dsl import decode_tensix
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 0x00000001)
  t.gpr.write32(0, 2, 4)
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 3) == 0x10   # 1 << 4


@spec("ASUI.SHIFTDMAREG.RIGHT")
def test_shiftdmareg_right():
  """SHIFTDMAREG Mode=1: Result = Left >> Right (unsigned)."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 0x80000000)
  t.gpr.write32(0, 2, 3)
  # encode: opcode=0x5C, Mode=1 at [20:18], result=3, opB=2, opA=1
  word = (0x5C << 24) | (1 << 18) | (3 << 12) | (2 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 3) == 0x10000000  # 0x80000000 >> 3


@spec("ASUI.SHIFTDMAREG.IMMEDIATE_5BIT")
def test_shiftdmareg_left_immediate():
  """SHIFTDMAREG with OpBisConst=1: shift amount is 5-bit immediate."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 1)
  # encode: opcode=0x5C, OpBisConst=1 at [23], Mode=0, result=2, opB_imm=8, opA=1
  word = (0x5C << 24) | (1 << 23) | (0 << 18) | (2 << 12) | (8 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 2) == 256  # 1 << 8


# ===========================================================================
# BITWOPDMAREG
# ===========================================================================

@spec("ASUI.BITWOPDMAREG.AND")
def test_bitwopdmareg_and():
  """BITWOPDMAREG OpSel=0: Result = A & B."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 0xFF00FF00)
  t.gpr.write32(0, 2, 0xF0F0F0F0)
  word = (0x5B << 24) | (0 << 18) | (3 << 12) | (2 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 3) == 0xF000F000


@spec("ASUI.BITWOPDMAREG.OR")
def test_bitwopdmareg_or():
  """BITWOPDMAREG OpSel=1: Result = A | B."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 0x0F0F0F0F)
  t.gpr.write32(0, 2, 0xF0F0F0F0)
  # OpSel=1 at [20:18]
  word = (0x5B << 24) | (1 << 18) | (3 << 12) | (2 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 3) == 0xFFFFFFFF


@spec("ASUI.BITWOPDMAREG.XOR")
def test_bitwopdmareg_xor():
  """BITWOPDMAREG OpSel=2: Result = A ^ B."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 0xAAAAAAAA)
  t.gpr.write32(0, 2, 0x55555555)
  # OpSel=2 at [20:18]
  word = (0x5B << 24) | (2 << 18) | (3 << 12) | (2 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 3) == 0xFFFFFFFF


@spec("ASUI.BITWOPDMAREG.IMMEDIATE_6BIT")
def test_bitwopdmareg_and_immediate():
  """BITWOPDMAREG OpBisConst=1: B is a 6-bit immediate."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 0xFF)
  # AND with immediate 0x0F (OpSel=0, OpBisConst=1, opB_imm=0x0F)
  word = (0x5B << 24) | (1 << 23) | (0 << 18) | (2 << 12) | (0x0F << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 2) == 0x0F


# ===========================================================================
# CMPDMAREG
# ===========================================================================

@spec("ASUI.CMPDMAREG.GT", "ASUI.CMPDMAREG.UNSIGNED")
def test_cmpdmareg_gt_true():
  """CMPDMAREG OpSel=0 (GT): result=1 when A > B (unsigned)."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 100)
  t.gpr.write32(0, 2, 50)
  word = (0x5D << 24) | (0 << 18) | (3 << 12) | (2 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 3) == 1


@spec("ASUI.CMPDMAREG.GT")
def test_cmpdmareg_gt_false():
  """CMPDMAREG OpSel=0 (GT): result=0 when A <= B (uses case where emulator default != expected)."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  # Pre-seed result reg with non-zero so we can detect no-op vs correct result
  t.gpr.write32(0, 3, 0xDEAD)
  t.gpr.write32(0, 1, 50)
  t.gpr.write32(0, 2, 100)
  word = (0x5D << 24) | (0 << 18) | (3 << 12) | (2 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  # Correct result: 50 > 100 is False → 0
  # Without dispatch, GPR 3 stays 0xDEAD (the no-op case).
  # So this assertion fails when not dispatched (xfail), passes when implemented.
  assert t.gpr.read32(0, 3) == 0


@spec("ASUI.CMPDMAREG.LT")
def test_cmpdmareg_lt():
  """CMPDMAREG OpSel=1 (LT): result=1 when A < B."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 7)
  t.gpr.write32(0, 2, 8)
  # OpSel=1
  word = (0x5D << 24) | (1 << 18) | (3 << 12) | (2 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 3) == 1


@spec("ASUI.CMPDMAREG.EQ")
def test_cmpdmareg_eq():
  """CMPDMAREG OpSel=2 (EQ): result=1 when A == B."""
  from emu.tensix import TensixCoprocessor
  t = TensixCoprocessor()
  t.gpr.write32(0, 1, 42)
  t.gpr.write32(0, 2, 42)
  # OpSel=2
  word = (0x5D << 24) | (2 << 18) | (3 << 12) | (2 << 6) | 1
  t.push_instruction(0, word)
  t.step()
  assert t.gpr.read32(0, 3) == 1


# ===========================================================================
# FLUSHDMA
# ===========================================================================

@spec("ASUI.FLUSHDMA.CONDITION_MASK")
def test_flushdma_zero_mask_defaults_to_all():
  """FLUSHDMA with mask=0 defaults to 0xF; instruction must be recognised and dispatched."""
  from emu.tensix import TensixCoprocessor
  from dsl import decode_tensix
  t = TensixCoprocessor()
  # opcode=0x46, ConditionMask=0 (defaults to 0xF per spec)
  word = (0x46 << 24) | 0
  t.push_instruction(0, word)
  t.step()
  # If FLUSHDMA were properly implemented and recognised, decode_tensix should
  # return a decoded object with name 'FLUSHDMA' rather than 'UNKNOWN_0x46'.
  decoded = decode_tensix(word)
  assert decoded.name == 'FLUSHDMA'
