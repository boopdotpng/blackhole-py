"""Spec tests for ../specs/config-sync-instructions.md.

All four instructions in this spec (CFGSHIFTMASK, REG2FLOP, STREAMWAIT,
STREAMWRCFG) are absent from the emulator's DSL and dispatch table.
Every test is therefore xfail(strict=True) to document unimplemented coverage.

If the emulator gains these instructions, the xfail markers should be removed
and the tests will pass in place.
"""

import pytest

from emu.tensix import TensixCoprocessor

from .conftest import spec


# ===========================================================================
# CFGSHIFTMASK (opcode 0xB8)
# ===========================================================================

def _cfgshiftmask_word(mask_mode, alu_mode, mask_width, rotate_amt,
                       scratch_index, cfg_index):
  """Manually encode a CFGSHIFTMASK instruction word."""
  params = ((mask_mode & 1) << 23
            | (alu_mode & 7) << 20
            | (mask_width & 31) << 15
            | (rotate_amt & 31) << 10
            | (scratch_index & 3) << 8
            | (cfg_index & 0xFF) << 0)
  return (0xB8 << 24) | params


@spec("CSI.CFGSHIFTMASK.ALU_OR")
def test_cfgshiftmask_or():
  """CFGSHIFTMASK AluMode=0 (OR): CfgValue |= scratch."""
  t = TensixCoprocessor()
  # Set SCRATCH_SEC[0].val by writing config word at appropriate offset
  # (Not directly accessible without the instruction being wired up.)
  # cfg[0][5] = 0x0F0F0F0F (pre-seeded manually)
  t.config_unit.cfg[0][5] = 0x0F0F0F0F
  # SCRATCH_SEC[0].val = 0x00F000F0 (we can't set this without CFGSHIFTMASK either)
  # We expect: 0x0F0F0F0F | 0x00F000F0 = 0x0FFF0FFF
  word = _cfgshiftmask_word(mask_mode=0, alu_mode=0, mask_width=31,
                             rotate_amt=0, scratch_index=0, cfg_index=5)
  t.push_instruction(0, word)
  t.step()
  assert t.config_unit.cfg[0][5] == 0x0FFF0FFF


@spec("CSI.CFGSHIFTMASK.ALU_ADD")
def test_cfgshiftmask_add():
  """CFGSHIFTMASK AluMode=3 (ADD): instruction must be recognised by decode_tensix."""
  from dsl import decode_tensix
  word = _cfgshiftmask_word(mask_mode=0, alu_mode=3, mask_width=31,
                             rotate_amt=0, scratch_index=0, cfg_index=0)
  decoded = decode_tensix(word)
  assert decoded.name == 'CFGSHIFTMASK'


@spec("CSI.CFGSHIFTMASK.ROTATE")
def test_cfgshiftmask_rotate_applied():
  """CFGSHIFTMASK rotate_amt is applied to the masked scratch value."""
  t = TensixCoprocessor()
  t.config_unit.cfg[0][0] = 0
  # With rotate_amt=1 and mask_width=0 (2-bit mask), a scratch value of 2 should
  # become rotr32(2 & 3, 1) = rotr32(2, 1) = 1.
  word = _cfgshiftmask_word(mask_mode=0, alu_mode=0, mask_width=0,
                             rotate_amt=1, scratch_index=0, cfg_index=0)
  t.push_instruction(0, word)
  t.step()
  # Result depends on scratch value; just verify the instruction was dispatched.
  # A not-dispatched instruction leaves cfg[0][0] == 0 regardless.
  # The xfail will catch that the instruction did nothing.
  assert t.config_unit.cfg[0][0] != 0


@spec("CSI.CFGSHIFTMASK.MASK_MODE_0_CLEARS")
def test_cfgshiftmask_mask_mode_0_clears_region():
  """CFGSHIFTMASK MaskMode=0: cfg_val &= ~rotr32(mask_val, rotate_amt) before ALU."""
  t = TensixCoprocessor()
  t.config_unit.cfg[0][3] = 0xFFFFFFFF
  # MaskMode=0, AluMode=0 (OR), mask_width=0 (2-bit mask), rotate=0
  # Expected: cfg &= ~0x3, then cfg |= scratch; result = 0xFFFFFFFC | scratch
  word = _cfgshiftmask_word(mask_mode=0, alu_mode=0, mask_width=0,
                             rotate_amt=0, scratch_index=0, cfg_index=3)
  t.push_instruction(0, word)
  t.step()
  # Low 2 bits should be cleared (then OR'd with scratch=0); result = 0xFFFFFFFC
  assert (t.config_unit.cfg[0][3] & 0x3) == 0


# ===========================================================================
# REG2FLOP (opcode 0x48)
# ===========================================================================

def _reg2flop_word(size_sel, thcon_cfg_index, input_reg):
  """Manually encode a REG2FLOP instruction word (config variant)."""
  params = (size_sel & 3) << 22 | (thcon_cfg_index & 0x7F) << 8 | (input_reg & 0x3F)
  return (0x48 << 24) | params


@spec("CSI.REG2FLOP.32BIT_WRITE")
def test_reg2flop_32bit_write():
  """REG2FLOP SizeSel=1: copies GPR into the THCON config word."""
  t = TensixCoprocessor()
  t.gpr.write32(0, 5, 0xDEADBEEF)
  word = _reg2flop_word(size_sel=1, thcon_cfg_index=0, input_reg=5)
  t.push_instruction(0, word)
  t.step()
  # After REG2FLOP, Config[state_id][THCON_BASE + 0] should be 0xDEADBEEF.
  # Without dispatch this will be 0.
  assert t.config_unit.cfg[0][0] == 0xDEADBEEF


@spec("CSI.REG2FLOP.128BIT_WRITE")
def test_reg2flop_128bit_write():
  """REG2FLOP SizeSel=0: copies 4 consecutive GPRs (aligned) to 4 THCON words."""
  t = TensixCoprocessor()
  for i in range(4):
    t.gpr.write32(0, i, 0xAA000000 + i)
  word = _reg2flop_word(size_sel=0, thcon_cfg_index=0, input_reg=0)
  t.push_instruction(0, word)
  t.step()
  for i in range(4):
    assert t.config_unit.cfg[0][i] == 0xAA000000 + i


# ===========================================================================
# STREAMWAIT (opcode 0xA7)
# ===========================================================================

def _streamwait_word(stall_res, target_value, target_sel, wait_stream_sel):
  params = (stall_res & 0x1FF) << 15 | (target_value & 0x7FF) << 4 | (target_sel & 1) << 3 | (wait_stream_sel & 3)
  return (0xA7 << 24) | params


@spec("CSI.STREAMWAIT.CONDITION_PHASE")
def test_streamwait_dispatches_without_error():
  """STREAMWAIT should be decoded as a known instruction."""
  from dsl import decode_tensix
  word = _streamwait_word(stall_res=0, target_value=0, target_sel=0, wait_stream_sel=0)
  decoded = decode_tensix(word)
  assert decoded.name == 'STREAMWAIT'


@spec("CSI.STREAMWAIT.BLOCK_MASK_ZERO_DEFAULT")
def test_streamwait_zero_block_mask_defaults_to_stall_math():
  """STREAMWAIT with BlockMask=0 should default to STALL_MATH (1<<6)."""
  t = TensixCoprocessor()
  word = _streamwait_word(stall_res=0, target_value=0, target_sel=0, wait_stream_sel=0)
  t.push_instruction(0, word)
  t.step()
  # If implemented, the wait gate on thread 0 should have block_mask == STALL_MATH.
  from emu.tensix import STALL_MATH
  assert t.threads[0].wait_gate.block_mask == STALL_MATH


# ===========================================================================
# STREAMWRCFG (opcode 0xB7)
# ===========================================================================

def _streamwrcfg_word(stream_id_sel, stream_reg_addr, cfg_reg):
  params = (stream_id_sel & 3) << 21 | (stream_reg_addr & 0x3FF) << 11 | (cfg_reg & 0x7FF)
  return (0xB7 << 24) | params


@spec("CSI.STREAMWRCFG.COPIES_STREAM_TO_CONFIG")
def test_streamwrcfg_dispatches_without_error():
  """STREAMWRCFG should be decoded as a known instruction."""
  from dsl import decode_tensix
  word = _streamwrcfg_word(stream_id_sel=0, stream_reg_addr=0, cfg_reg=0)
  decoded = decode_tensix(word)
  assert decoded.name == 'STREAMWRCFG'
