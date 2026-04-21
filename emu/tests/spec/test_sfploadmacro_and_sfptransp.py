"""Spec tests for ../specs/sfploadmacro-and-sfptransp.md.

Each test is pinned to one or more clauses from
../clauses/sfploadmacro-and-sfptransp.md via the @spec() marker.

SFPLOADMACRO deviations:
  - Sub-unit scheduling, delay counting, LoadMacroConfig are all unimplemented.
  - Emulator dispatches SFPLOADMACRO as plain SFPLOAD only.

SFPTRANSP deviations:
  - Not implemented at all in the emulator (no sfptransp method in sfpu.py,
    not dispatched in trisc1.py). All SFPTRANSP tests xfail.
"""

import pytest

from emu.tensix import SFPU, _to_float, _to_bits, POS_INF, NEG_INF, CONST_ONE
from emu.tensix import DestRegFile
from dsl import decode_tensix
from emu.tensix import RWCState
from emu.tensix import TensixCoprocessor

from .conftest import spec


# Helpers

def _make():
  dest = DestRegFile()
  return SFPU(dest), dest


def _f2b(f):
  import struct
  return struct.unpack('I', struct.pack('f', f))[0]


def _b2f(b):
  import struct
  return struct.unpack('f', struct.pack('I', b & 0xFFFFFFFF))[0]


# ===========================================================================
# SFPLOADMACRO: load part
# ===========================================================================

@spec("SFPLM.LOAD_PART")
def test_sfploadmacro_executes_sfpload():
  """SFPLOADMACRO dispatched as SFPLOAD: Dst row is moved to LReg[vd]."""
  c = TensixCoprocessor()
  rwc = c.rwc[1]
  # Write a known pattern into Dest row 0
  for col in range(16):
    c.dest.bits[0][col] = _f2b(float(col * 10))
    c.dest.valid[0] = True
  # Push SFPLOADMACRO (opcode 0x93) targeting LReg[0], row 0
  # trisc1.py dispatches SFPLOADMACRO → sfpload(d, rwc)
  # Encoding: opcode 0x93, lreg_ind=0, instr_mod0=0, addr_mode=0, dest_reg_addr=0
  word = (0x93 << 24) | (0 << 20) | (0 << 16) | (0 << 13) | 0
  c.push_instruction(1, word)
  c.step()
  # Verify Dest row loaded into LReg[0] via the load part
  for lane in range(16):
    assert c.sfpu.lregs[0][lane] == _f2b(float(lane * 10)), f"lane {lane}"


@spec("SFPLM.SCHEDULE_IGNORED")
def test_sfploadmacro_schedules_subunit():
  """After SFPLOADMACRO, a sub-unit instruction should execute at delay=0."""
  # This test exercises the sub-unit scheduling path:
  # Configure Sequence[0] to schedule SFPARECIP at delay 0 on the Simple sub-unit.
  # After SFPLOADMACRO, LReg[vd] should contain the reciprocal of the loaded value.
  import struct
  c = TensixCoprocessor()
  # Write 4.0 into Dest row 0
  c.dest.bits[0][0] = _f2b(4.0)
  c.dest.valid[0] = True
  # Configure LoadMacroConfig.Sequence[0] to schedule SFPARECIP at delay 0:
  # seq_byte = (delay=0) << 3 | selector=4 (InstructionTemplate[0])
  # InstructionTemplate[0] = SFPARECIP instruction (opcode 0x99, VC=0, VD=0, Mod1=0)
  recip_insn = (0x99 << 24) | (0 << 8) | (0 << 4) | 0
  # SFPCONFIG VD=0 (InstructionTemplate[0]) = recip_insn would set the template.
  # This requires LoadMacroConfig to be implemented, which it isn't.
  # Push SFPLOADMACRO
  word = (0x93 << 24) | (0 << 20) | (0 << 16) | 0
  c.push_instruction(1, word)
  c.step()
  # After the macro, LReg[0][0] should be 1/4.0 = 0.25 if scheduling worked
  assert abs(_b2f(c.sfpu.lregs[0][0]) - 0.25) < 0.01


@spec("SFPLM.LREG16_WRITABLE_VIA_MACRO")
def test_lreg16_not_writable_by_regular_instruction():
  """Regular SFPLOADI to VD=16 is silently ignored — LReg[16] unchanged.

  The emulator correctly rejects VD=16 via _is_writable() (which only allows
  indices 0-7 and 11-14). This matches the spec's restriction that LReg[16]
  is writable only via SFPLOADMACRO sub-unit scheduling.
  """
  sfpu, _ = _make()
  original = sfpu.lregs[16][0]
  word = (0x71 << 24) | (16 << 20) | (4 << 16) | 0xABCD
  sfpu.sfploadi(decode_tensix(word))
  assert sfpu.lregs[16][0] == original


# ===========================================================================
# SFPTRANSP: all xfail because not implemented
# ===========================================================================

@spec("SFPTR.TWO_GROUPS",
      "SFPTR.SWAP_RULE")
def test_sfptransp_basic_swap():
  """SFPTRANSP swaps LReg[i][j*8+c] with LReg[j][i*8+c] for i>j, per column c."""
  sfpu, _ = _make()
  # Set up a pattern in LReg[0..3] group:
  # LReg[r][lane] = r * 100 + lane (distinct values for each reg+lane pair)
  for r in range(4):
    for lane in range(32):
      sfpu.lregs[r][lane] = r * 100 + lane
  # Save pre-transpose state
  before = [[sfpu.lregs[r][lane] for lane in range(32)] for r in range(4)]
  # Execute SFPTRANSP (if implemented, requires dispatching opcode 0x8C)
  # Since it's not in trisc1.py, simulate via a hypothetical method call:
  # sfpu.sfptransp(...) — this method doesn't exist, so the test should fail.
  sfpu.sfptransp(type('D', (), {'lreg_dest': 0, 'instr_mod1': 0})())  # will raise AttributeError
  # After transpose, check swap rule for group 0:
  # LReg[base+i][j*8+c] should equal old LReg[base+j][i*8+c]
  for col in range(8):
    for i in range(4):
      for j in range(i):
        lane_ij = j * 8 + col
        lane_ji = i * 8 + col
        assert sfpu.lregs[i][lane_ij] == before[j][lane_ji], (
          f"After transp: LReg[{i}][{lane_ij}] should be old LReg[{j}][{lane_ji}]"
        )
        assert sfpu.lregs[j][lane_ji] == before[i][lane_ij], (
          f"After transp: LReg[{j}][{lane_ji}] should be old LReg[{i}][{lane_ij}]"
        )


@spec("SFPTR.LANE_ENABLED_GUARD")
def test_sfptransp_respects_lane_enabled():
  """SFPTRANSP only overwrites LReg[base+i][j*8+c] if LaneEnabled[j*8+c]."""
  sfpu, _ = _make()
  sfpu.use_lane_flags = True
  sfpu.lane_flags = [True] * 32
  sfpu.lane_flags[0] = False  # disable lane 0 (col 0, row 0 of LReg[0])
  for r in range(4):
    for lane in range(32):
      sfpu.lregs[r][lane] = r * 100 + lane
  original_r0_lane0 = sfpu.lregs[0][0]  # should be preserved (lane 0 disabled)
  sfpu.sfptransp(type('D', (), {'lreg_dest': 0, 'instr_mod1': 0})())
  # LReg[1][0] (j=0, col=0 for i=1 swap) should NOT be overwritten because lane 0 disabled
  assert sfpu.lregs[0][0] == original_r0_lane0


@spec("SFPTR.DOUBLE_TRANSPOSE_IDENTITY")
def test_sfptransp_double_is_identity():
  """Applying SFPTRANSP twice restores the original LReg state."""
  sfpu, _ = _make()
  # Seed distinct values
  for r in range(8):
    for lane in range(32):
      sfpu.lregs[r][lane] = r * 1000 + lane + 1
  original = [[sfpu.lregs[r][lane] for lane in range(32)] for r in range(8)]
  d = type('D', (), {'lreg_dest': 0, 'instr_mod1': 0})()
  sfpu.sfptransp(d)  # first transpose
  sfpu.sfptransp(d)  # second transpose — should restore
  for r in range(8):
    for lane in range(32):
      assert sfpu.lregs[r][lane] == original[r][lane], (
        f"LReg[{r}][{lane}] not restored after double-transpose"
      )
