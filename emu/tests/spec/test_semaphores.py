"""Spec tests for ../specs/semaphores.md.

Covers the Tensix hardware semaphore model:
  - State invariants (count=8, 4-bit value/max)
  - SEMINIT, SEMPOST, SEMGET via SyncUnit + Semaphores
  - SEMWAIT blocking behaviour via WaitGate
  - PCBuf memory-mapped semaphore window (read, post, get)

Software semaphores (plain L1 words) are not tested here; they are exercised
by the NOC tests since they use L1 reads/writes and NOC atomics.
"""

import pytest

from emu.memory import _SEM_WIN_LO
from emu.tensix import Semaphores, SyncUnit
from emu.tensix import WaitGate
from emu.tensix import TensixCoprocessor, HardwareState
from emu.tensix import SrcRegFile
from dsl import (
  decode_tensix,
  TT_SEMINIT, TT_SEMPOST, TT_SEMGET, TT_SEMWAIT, TT_MVMUL,
)

from .conftest import spec


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def sems():
  return Semaphores()


# ===========================================================================
# Software semaphores (plain L1 words)
# ===========================================================================

@spec("SEM.SW.L1_PLAIN_WORD")
def test_software_semaphores_are_plain_l1_words():
  """Software semaphores are plain uint32_t values in L1: no dedicated
  hardware path, just L1 reads and writes. Incrementing and reading back
  through Memory.read32/write32 works with zero special support."""
  from emu.memory import Memory
  l1 = Memory()
  sem_addr = 0x4000           # arbitrary L1 offset
  # Initial value is 0 (uninitialized L1).
  assert l1.read32(sem_addr) == 0
  # "Post" a software sem by writing its new value.
  l1.write32(sem_addr, 1)
  assert l1.read32(sem_addr) == 1
  # Increment-style post (read-modify-write, as firmware would do).
  l1.write32(sem_addr, l1.read32(sem_addr) + 1)
  assert l1.read32(sem_addr) == 2
  # A software sem is just a uint32_t — full 32-bit range is valid.
  l1.write32(sem_addr, 0xDEADBEEF)
  assert l1.read32(sem_addr) == 0xDEADBEEF


@pytest.fixture
def sync(sems):
  return SyncUnit(sems)


@pytest.fixture
def coprocessor():
  return TensixCoprocessor()


def _hw_state(sems):
  srca = SrcRegFile("SrcA")
  srcb = SrcRegFile("SrcB")
  return HardwareState(sems, srca, srcb)


# ===========================================================================
# State invariants
# ===========================================================================

@spec("SEM.STATE.COUNT_8")
def test_semaphore_count_is_8(sems):
  """There are exactly 8 hardware semaphores."""
  assert len(sems.value) == 8
  assert len(sems.max) == 8


@spec("SEM.STATE.VALUE_RANGE")
def test_seminit_value_clamped_to_4bit(sems, sync):
  """SEMINIT value is clamped to 4 bits (0-15)."""
  word = int(TT_SEMINIT(max_value=15, init_value=15, sem_sel=0x01))
  sync.execute_seminit(decode_tensix(word))
  assert sems.value[0] == 15
  assert sems.max[0] == 15


@spec("SEM.STATE.MAX_RANGE")
def test_seminit_max_clamped_to_4bit(sems, sync):
  """SEMINIT max is clamped to 4 bits (0-15)."""
  word = int(TT_SEMINIT(max_value=15, init_value=0, sem_sel=0x02))
  sync.execute_seminit(decode_tensix(word))
  assert sems.max[1] == 15


# ===========================================================================
# SEMINIT
# ===========================================================================

@spec("SEM.SEMINIT.SETS_VALUE_AND_MAX")
def test_seminit_sets_value_and_max(sems, sync):
  """SEMINIT sets both Value and Max for selected semaphores."""
  word = int(TT_SEMINIT(max_value=5, init_value=3, sem_sel=0x02))
  sync.execute_seminit(decode_tensix(word))
  assert sems.value[1] == 3
  assert sems.max[1] == 5


@spec("SEM.SEMINIT.SEM_SEL_BITMASK")
def test_seminit_bitmask_selects_multiple(sems, sync):
  """SEMINIT sem_sel bitmask initializes all selected semaphores."""
  word = int(TT_SEMINIT(max_value=7, init_value=2, sem_sel=0x05))  # bits 0 and 2
  sync.execute_seminit(decode_tensix(word))
  assert sems.value[0] == 2 and sems.max[0] == 7
  assert sems.value[2] == 2 and sems.max[2] == 7
  assert sems.value[1] == 0  # not selected


@spec("SEM.SEMINIT.SEM_SEL_BITMASK")
def test_seminit_all_eight(sems, sync):
  """SEMINIT sem_sel=0xFF initializes all 8 semaphores."""
  word = int(TT_SEMINIT(max_value=10, init_value=1, sem_sel=0xFF))
  sync.execute_seminit(decode_tensix(word))
  for i in range(8):
    assert sems.value[i] == 1
    assert sems.max[i] == 10


# ===========================================================================
# SEMPOST
# ===========================================================================

@spec("SEM.SEMPOST.INCREMENT")
def test_sempost_increments_value(sems, sync):
  """SEMPOST increments Value by 1."""
  sems.init(1, 0, 5)
  sync.execute_sempost(decode_tensix(int(TT_SEMPOST(sem_sel=0x02))))
  assert sems.value[1] == 1


@spec("SEM.SEMPOST.SATURATES_AT_MAX")
def test_sempost_saturates_at_max(sems, sync):
  """SEMPOST saturates at Max — posting at Max is a no-op."""
  sems.init(0, 3, 3)
  sync.execute_sempost(decode_tensix(int(TT_SEMPOST(sem_sel=0x01))))
  assert sems.value[0] == 3


@spec("SEM.SEMPOST.MULTI_SEM")
def test_sempost_multi_semaphore(sems, sync):
  """SEMPOST with sem_sel bitmask increments multiple semaphores."""
  sems.init(0, 0, 5)
  sems.init(2, 0, 5)
  sync.execute_sempost(decode_tensix(int(TT_SEMPOST(sem_sel=0x05))))  # bits 0 and 2
  assert sems.value[0] == 1
  assert sems.value[2] == 1
  assert sems.value[1] == 0  # untouched


# ===========================================================================
# SEMGET
# ===========================================================================

@spec("SEM.SEMGET.DECREMENT")
def test_semget_decrements_value(sems, sync):
  """SEMGET decrements Value by 1."""
  sems.init(1, 3, 5)
  sync.execute_semget(decode_tensix(int(TT_SEMGET(sem_sel=0x02))))
  assert sems.value[1] == 2


@spec("SEM.SEMGET.FLOORS_AT_ZERO")
def test_semget_floors_at_zero(sems, sync):
  """SEMGET floors at 0 — getting when Value==0 is a no-op."""
  sems.init(0, 0, 5)
  sync.execute_semget(decode_tensix(int(TT_SEMGET(sem_sel=0x01))))
  assert sems.value[0] == 0


@spec("SEM.SEMGET.MULTI_SEM")
def test_semget_multi_semaphore(sems, sync):
  """SEMGET with sem_sel bitmask decrements multiple semaphores."""
  sems.init(3, 2, 5)
  sems.init(5, 4, 5)
  sync.execute_semget(decode_tensix(int(TT_SEMGET(sem_sel=0x28))))  # bits 3 and 5
  assert sems.value[3] == 1
  assert sems.value[5] == 3


# ===========================================================================
# SEMWAIT — blocking behaviour
# ===========================================================================

@spec("SEM.SEMWAIT.STALL_ON_ZERO")
def test_semwait_stall_on_zero_blocks_when_zero(sems):
  """SEMWAIT C0: block while Value == 0; release when Value > 0."""
  sems.init(1, 0, 5)
  wg = WaitGate()
  wg.install_semwait(0x40, 0x02, 0x01)   # block CFG, sem[1], C0
  hw = _hw_state(sems)
  mvmul = int(TT_MVMUL(0, 0, 0, 0))

  assert wg.is_blocking(mvmul, hw, 0)   # one-cycle minimum hold
  assert wg.is_blocking(mvmul, hw, 0)   # value == 0, still blocking

  sems.post(1)                           # value → 1
  assert not wg.is_blocking(mvmul, hw, 0)  # released


@spec("SEM.SEMWAIT.STALL_ON_MAX")
def test_semwait_stall_on_max_blocks_at_max(sems):
  """SEMWAIT C1: block while Value >= Max; release when Value < Max."""
  sems.init(2, 4, 4)
  wg = WaitGate()
  wg.install_semwait(0x40, 0x04, 0x02)   # block CFG, sem[2], C1
  hw = _hw_state(sems)
  mvmul = int(TT_MVMUL(0, 0, 0, 0))

  assert wg.is_blocking(mvmul, hw, 0)   # one-cycle hold
  assert wg.is_blocking(mvmul, hw, 0)   # value >= max, still blocking

  sems.get(2)                            # value → 3
  assert not wg.is_blocking(mvmul, hw, 0)  # released


@spec("SEM.SEMWAIT.BLOCK_MASK")
def test_semwait_block_mask_only_affects_selected_types(sems):
  """SEMWAIT block_mask restricts which instruction types are held."""
  sems.init(0, 0, 5)   # value=0 → stall condition for C0
  wg = WaitGate()
  # Only block MATH instructions (0x40 = STALL_MATH)
  wg.install_semwait(0x40, 0x01, 0x01)
  hw = _hw_state(sems)

  mvmul = int(TT_MVMUL(0, 0, 0, 0))
  wg.is_blocking(mvmul, hw, 0)   # consume one-cycle hold

  # MATH instruction IS blocked by STALL_MATH
  assert wg.is_blocking(mvmul, hw, 0)

  # SETC16 (Config instruction) is NOT blocked by STALL_MATH
  from dsl import TT_SETC16
  setc16 = int(TT_SETC16(0, 0))
  assert not wg.is_blocking(setc16, hw, 0)


# ===========================================================================
# Through the coprocessor pipeline
# ===========================================================================

@spec("SEM.SEMINIT.SETS_VALUE_AND_MAX")
def test_seminit_through_pipeline(coprocessor):
  """SEMINIT dispatched through TensixCoprocessor reaches the Semaphores object."""
  t = coprocessor
  word = int(TT_SEMINIT(max_value=3, init_value=1, sem_sel=0x04))  # sem[2]
  t.push_instruction(0, word)
  t.step()
  assert t.semaphores.value[2] == 1
  assert t.semaphores.max[2] == 3


@spec("SEM.SEMPOST.INCREMENT",
      "SEM.SEMGET.DECREMENT")
def test_sempost_semget_pipeline(coprocessor):
  """SEMPOST and SEMGET through the pipeline alter Value correctly."""
  t = coprocessor
  t.semaphores.init(0, 0, 5)
  t.push_instruction(0, int(TT_SEMPOST(sem_sel=0x01)))
  t.step()
  assert t.semaphores.value[0] == 1
  t.push_instruction(0, int(TT_SEMGET(sem_sel=0x01)))
  t.step()
  assert t.semaphores.value[0] == 0


# ===========================================================================
# PCBuf semaphore window
# ===========================================================================

@spec("SEM.PCBUF.ADDRESS_RANGE")
def test_pcbuf_address_range(sems):
  """Semaphore window starts at 0xFFE80020 (PCBUF_T0 + 0x20)."""
  from emu.memory import PCBUF_T0, PCBUF_SEM_BASE
  assert _SEM_WIN_LO == PCBUF_T0 + PCBUF_SEM_BASE
  assert _SEM_WIN_LO == 0xFFE80020


@spec("SEM.PCBUF.READ_RETURNS_VALUE")
def test_pcbuf_read_returns_value(sems):
  """Read from PCBuf window returns the semaphore Value."""
  sems.init(3, 7, 15)
  addr = _SEM_WIN_LO + 3 * 4
  assert sems.read32(addr) == 7


@spec("SEM.PCBUF.WRITE_POST")
def test_pcbuf_write_post(sems):
  """Write with bit 0 == 0 performs SEMPOST (increments Value)."""
  sems.init(0, 2, 10)
  addr = _SEM_WIN_LO + 0 * 4
  sems.write32(addr, 0)    # bit 0 == 0 → POST
  assert sems.value[0] == 3


@spec("SEM.PCBUF.WRITE_GET")
def test_pcbuf_write_get(sems):
  """Write with bit 0 == 1 performs SEMGET (decrements Value)."""
  sems.init(1, 5, 10)
  addr = _SEM_WIN_LO + 1 * 4
  sems.write32(addr, 1)    # bit 0 == 1 → GET
  assert sems.value[1] == 4


@spec("SEM.PCBUF.READ_RETURNS_VALUE",
      "SEM.PCBUF.WRITE_POST",
      "SEM.PCBUF.WRITE_GET")
def test_pcbuf_all_8_semaphores_addressable(sems):
  """All 8 semaphores are addressable through the PCBuf window."""
  for i in range(8):
    sems.init(i, i, 15)
    addr = _SEM_WIN_LO + i * 4
    assert sems.read32(addr) == i


@spec("SEM.PCBUF.WRITE_POST",
      "SEM.SEMPOST.SATURATES_AT_MAX")
def test_pcbuf_post_saturates_at_max(sems):
  """PCBuf SEMPOST saturates at Max."""
  sems.init(4, 5, 5)
  addr = _SEM_WIN_LO + 4 * 4
  sems.write32(addr, 0)    # POST — already at max
  assert sems.value[4] == 5


@spec("SEM.PCBUF.WRITE_GET",
      "SEM.SEMGET.FLOORS_AT_ZERO")
def test_pcbuf_get_floors_at_zero(sems):
  """PCBuf SEMGET floors at 0."""
  sems.init(5, 0, 5)
  addr = _SEM_WIN_LO + 5 * 4
  sems.write32(addr, 1)    # GET — already at 0
  assert sems.value[5] == 0
