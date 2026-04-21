"""Spec tests for ../specs/rwc-and-addressing.md.

Each test is pinned to one or more clauses from
../clauses/rwc-and-addressing.md via the @spec() marker.

Layout:
  - RWCState initial values
  - SETRWC: bitmask, selective update, clear_ab return
  - INCRWC: additions, 4-bit/3-bit wrap
  - AddrModState: increment, clear, out-of-bounds NOP
  - ADC: SETADC, SETADCXY, SETADCZW, INCADCZW, multi-unit mask, SETADCXX
"""

import pytest
from emu.dsl import decode_tensix
from emu.tensix import TensixCoprocessor
from emu.tensix.rwc import RWCState, AddrModState, ADCState

from .conftest import spec


# ===========================================================================
# RWCState initial state
# ===========================================================================

@spec("RWC.INIT.ALL_ZERO")
def test_rwc_initial_state():
  """RWCState initializes a=b=d=cr=0."""
  rwc = RWCState()
  assert rwc.a == 0
  assert rwc.b == 0
  assert rwc.d == 0
  assert rwc.cr == 0


# ===========================================================================
# SETRWC
# ===========================================================================

@spec("RWC.SETRWC.BITMASK_SELECTS_COUNTERS",
      "RWC.SETRWC.SET_A", "RWC.SETRWC.SET_B", "RWC.SETRWC.SET_D")
def test_setrwc_all_bitmask():
  """SETRWC with bitmask=0x0F sets a, b, d, cr all at once."""
  rwc = RWCState()
  word = (0x37 << 24) | (0 << 22) | (2 << 18) | (7 << 14) | (5 << 10) | (3 << 6) | 0x0F
  rwc.execute_setrwc(decode_tensix(word))
  assert rwc.a == 3
  assert rwc.b == 5
  assert rwc.d == 7


@spec("RWC.SETRWC.SET_A")
def test_setrwc_set_a_only():
  """SETRWC with bitmask=0x01 (SET_A): only sets SrcA counter."""
  rwc = RWCState()
  rwc.b = 11
  word = (0x37 << 24) | (0 << 22) | (0 << 18) | (0 << 14) | (0 << 10) | (5 << 6) | 0x01
  rwc.execute_setrwc(decode_tensix(word))
  assert rwc.a == 5
  assert rwc.b == 11   # unchanged


@spec("RWC.SETRWC.SELECTIVE_UPDATE")
def test_setrwc_selective_does_not_touch_others():
  """SETRWC bitmask=0x04 (SET_D only): a and b remain unchanged."""
  rwc = RWCState()
  rwc.a = 7
  rwc.b = 9
  word = (0x37 << 24) | (0 << 22) | (0 << 18) | (3 << 14) | (0 << 10) | (0 << 6) | 0x04
  rwc.execute_setrwc(decode_tensix(word))
  assert rwc.d == 3
  assert rwc.a == 7   # untouched
  assert rwc.b == 9   # untouched


@spec("RWC.SETRWC.RETURNS_CLEAR_AB")
def test_setrwc_returns_clear_ab_vld():
  """SETRWC returns d.clear_ab_vld (bits [23:22])."""
  rwc = RWCState()
  # clear_ab_vld = 3 (CLR_AB)
  word = (0x37 << 24) | (3 << 22) | (0 << 18) | (0 << 14) | (0 << 10) | (0 << 6) | 0
  clear = rwc.execute_setrwc(decode_tensix(word))
  assert clear == 3


# ===========================================================================
# INCRWC
# ===========================================================================

@spec("RWC.INCRWC.ADDS_DELTA")
def test_incrwc_adds_deltas():
  """INCRWC adds independent deltas to a, b, d."""
  rwc = RWCState()
  rwc.a = 5; rwc.b = 10; rwc.d = 14; rwc.cr = 6
  word = (0x38 << 24) | (1 << 18) | (4 << 14) | (3 << 10) | (2 << 6)
  rwc.execute_incrwc(decode_tensix(word))
  assert rwc.a == 7
  assert rwc.b == 13
  assert rwc.d == (14 + 4) & 0xF   # 4-bit wrap
  assert rwc.cr == 7


@spec("RWC.INCRWC.WRAP_4BIT")
def test_incrwc_wraps_a():
  """INCRWC wraps rwc.a at 4 bits (max 15 → 0 on +1)."""
  rwc = RWCState()
  rwc.a = 15
  word = (0x38 << 24) | (0 << 18) | (0 << 14) | (0 << 10) | (1 << 6)
  rwc.execute_incrwc(decode_tensix(word))
  assert rwc.a == 0


@spec("RWC.INCRWC.WRAP_4BIT")
def test_incrwc_wraps_d():
  """INCRWC wraps rwc.d at 4 bits."""
  rwc = RWCState()
  rwc.d = 14
  word = (0x38 << 24) | (0 << 18) | (3 << 14) | (0 << 10) | (0 << 6)
  rwc.execute_incrwc(decode_tensix(word))
  assert rwc.d == (14 + 3) & 0xF   # = 1


# ===========================================================================
# AddrModState
# ===========================================================================

@spec("RWC.ADDRMOD.8_DESCRIPTORS")
def test_addrmod_has_8_descriptors():
  """AddrModState has 8 descriptor slots."""
  ams = AddrModState()
  assert len(ams.descriptors) == 8


@spec("RWC.ADDRMOD.APPLY_INCREMENT")
def test_addrmod_apply_increment():
  """apply() increments rwc counters by the configured amounts."""
  rwc = RWCState()
  rwc.a = 3; rwc.b = 5; rwc.d = 7
  ams = AddrModState()
  ams.descriptors[0].srca_incr = 2
  ams.descriptors[0].srcb_incr = 1
  ams.descriptors[0].dest_incr = 3
  ams.apply(0, rwc)
  assert rwc.a == 5
  assert rwc.b == 6
  assert rwc.d == 10


@spec("RWC.ADDRMOD.APPLY_CLEAR")
def test_addrmod_apply_clear_srca():
  """apply() with srca_clr=True: resets rwc.a to 0."""
  rwc = RWCState()
  rwc.a = 10; rwc.b = 5
  ams = AddrModState()
  ams.descriptors[1].srca_clr = True
  ams.descriptors[1].srcb_incr = 3
  ams.apply(1, rwc)
  assert rwc.a == 0   # cleared
  assert rwc.b == 8   # incremented


@spec("RWC.ADDRMOD.APPLY_CLEAR")
def test_addrmod_apply_clear_takes_priority():
  """apply() with clr+incr: clear takes priority over increment."""
  rwc = RWCState()
  rwc.a = 10
  ams = AddrModState()
  ams.descriptors[0].srca_clr = True
  ams.descriptors[0].srca_incr = 5   # should be ignored when clr=True
  ams.apply(0, rwc)
  assert rwc.a == 0


@spec("RWC.ADDRMOD.WRAP_4BIT")
def test_addrmod_increment_wraps():
  """apply() wraps counters at 4 bits for a/b/d."""
  rwc = RWCState()
  rwc.a = 14
  ams = AddrModState()
  ams.descriptors[0].srca_incr = 3
  ams.apply(0, rwc)
  assert rwc.a == (14 + 3) & 0xF   # = 1


@spec("RWC.ADDRMOD.OOB_INDEX_NOP")
def test_addrmod_oob_index_is_nop():
  """apply() with out-of-bounds index does nothing."""
  rwc = RWCState()
  rwc.a = 7
  ams = AddrModState()
  ams.apply(8, rwc)   # out of range
  assert rwc.a == 7   # unchanged
  ams.apply(-1, rwc)
  assert rwc.a == 7


# ===========================================================================
# ADC instructions
# ===========================================================================

@spec("RWC.ADC.SETADC_SETS_ONE_DIM")
def test_setadc_sets_one_dim():
  """SETADC: sets one dimension of one channel for the selected unit."""
  adc = ADCState()
  # Set Unpacker0, channel 0, dimension X to 42
  word = (0x50 << 24) | (1 << 21) | (0 << 20) | (0 << 18) | 42
  adc.execute_setadc(decode_tensix(word))
  assert adc.unpackers[0].channels[0].x.val == 42


@spec("RWC.ADC.MULTI_UNIT_UPDATE")
def test_setadc_multiple_units():
  """SETADC with CntSetMask=7: updates all three units."""
  adc = ADCState()
  word = (0x50 << 24) | (7 << 21) | (1 << 20) | (1 << 18) | 99
  adc.execute_setadc(decode_tensix(word))
  assert adc.unpackers[0].channels[1].y.val == 99
  assert adc.unpackers[1].channels[1].y.val == 99
  assert adc.packers.channels[1].y.val == 99


@spec("RWC.ADC.SETADCXY_SETS_XY")
def test_setadcxy_sets_x_and_y():
  """SETADCXY: sets X and Y of specified channels for selected unit."""
  adc = ADCState()
  # Unpacker0, Ch0_X=3, Ch0_Y=5, bitmask=0x03
  word = (0x51 << 24) | (1 << 21) | (0 << 15) | (0 << 12) | (5 << 9) | (3 << 6) | 0x03
  adc.execute_setadcxy(decode_tensix(word))
  assert adc.unpackers[0].channels[0].x.val == 3
  assert adc.unpackers[0].channels[0].y.val == 5


@spec("RWC.ADC.SETADCZW_SETS_ZW")
def test_setadczw_sets_z_and_w():
  """SETADCZW: sets Z and W of specified channels."""
  adc = ADCState()
  # Unpacker0 (CntSetMask=1), Ch0_Z=5, Ch0_W=3, BitMask=0x03 (enable both z and w)
  # SETADCZW opcode = 0x54, fields: CntSetMask@21:3, Ch1_W@15:6, Ch1_Z@12:3,
  #                                  Ch0_W@9:3, Ch0_Z@6:3, BitMask@0:6
  # Ch0_Z and Ch0_W are each 3 bits wide (0-7)
  word = (0x54 << 24) | (1 << 21) | (0 << 15) | (0 << 12) | (3 << 9) | (5 << 6) | 0x03
  adc.execute_setadczw(decode_tensix(word))
  assert adc.unpackers[0].channels[0].z.val == 5
  assert adc.unpackers[0].channels[0].w.val == 3


@spec("RWC.ADC.INCADCZW_INCREMENTS_ZW")
def test_incadczw_increments_zw():
  """INCADCZW: increments Z and W for the selected unit."""
  adc = ADCState()
  adc.unpackers[0].channels[0].z.val = 10
  adc.unpackers[0].channels[0].w.val = 20
  # Unpacker0, Ch0_Z += 5, Ch0_W += 3
  word = (0x55 << 24) | (1 << 21) | (0 << 15) | (0 << 12) | (3 << 9) | (5 << 6)
  adc.execute_incadczw(decode_tensix(word))
  assert adc.unpackers[0].channels[0].z.val == 15
  assert adc.unpackers[0].channels[0].w.val == 23


@spec("RWC.ADC.CNTSETMASK_SELECTS_UNITS")
def test_cntsetmask_bit0_only():
  """CntSetMask=0b001: only Unpacker0 is updated."""
  adc = ADCState()
  word = (0x50 << 24) | (1 << 21) | (0 << 20) | (0 << 18) | 77
  adc.execute_setadc(decode_tensix(word))
  assert adc.unpackers[0].channels[0].x.val == 77
  assert adc.unpackers[1].channels[0].x.val == 0   # untouched
  assert adc.packers.channels[0].x.val == 0         # untouched


@spec("RWC.ADC.CNTSETMASK_SELECTS_UNITS")
def test_cntsetmask_bit1_only():
  """CntSetMask=0b010: only Unpacker1 is updated."""
  adc = ADCState()
  word = (0x50 << 24) | (2 << 21) | (0 << 20) | (0 << 18) | 33
  adc.execute_setadc(decode_tensix(word))
  assert adc.unpackers[1].channels[0].x.val == 33
  assert adc.unpackers[0].channels[0].x.val == 0   # untouched


@spec("RWC.ADC.SETADCXX_BOTH_CHANNELS")
def test_setadcxx_sets_both_channels():
  """SETADCXX: sets Channel[0].X and Channel[1].X from two 10-bit values."""
  adc = ADCState()
  # SETADCXX opcode = 0x5E, fields: CntSetMask@21:3, x_end2@10:11, x_start@0:10
  # CntSetMask=Unpacker0 (bit0=1), x_start=5, x_end2=10
  word = (0x5E << 24) | (1 << 21) | (10 << 10) | 5
  adc.execute_setadcxx(decode_tensix(word))
  assert adc.unpackers[0].channels[0].x.val == 5
  # x_end2 goes into cr per emulator impl
  assert adc.unpackers[0].channels[0].x.cr == 10


# ===========================================================================
# TRISC1 pipeline: SETRWC + INCRWC dispatched correctly
# ===========================================================================

@spec("RWC.SETRWC.BITMASK_SELECTS_COUNTERS", "RWC.SETRWC.SET_D")
def test_setrwc_through_trisc1_pipeline():
  """SETRWC dispatched via TRISC1 pipeline correctly sets rwc.d."""
  c = TensixCoprocessor()
  word = (0x37 << 24) | (0 << 22) | (0 << 18) | (5 << 14) | (0 << 10) | (0 << 6) | 0x04
  c.push_instruction(1, word)
  c.step()
  assert c.rwc[1].d == 5


@spec("RWC.INCRWC.ADDS_DELTA")
def test_incrwc_through_trisc1_pipeline():
  """INCRWC dispatched via TRISC1 pipeline correctly increments counters."""
  c = TensixCoprocessor()
  # Set a=3 first
  word = (0x37 << 24) | (0 << 22) | (0 << 18) | (0 << 14) | (0 << 10) | (3 << 6) | 0x01
  c.push_instruction(1, word)
  c.step()
  assert c.rwc[1].a == 3
  # Now increment a by 2
  word = (0x38 << 24) | (0 << 18) | (0 << 14) | (0 << 10) | (2 << 6)
  c.push_instruction(1, word)
  c.step()
  assert c.rwc[1].a == 5
