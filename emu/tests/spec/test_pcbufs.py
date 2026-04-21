"""Spec tests for ../specs/pcbufs.md.

Each test is pinned to one or more clauses from
../clauses/pcbufs.md via the @spec() marker.
"""

import pytest

from emu.tensix import TensixCoprocessor
from emu.memory import (
    PCBUF_T0, PCBUF_T1, PCBUF_T2, PCBUF_STRIDE,
    PCBUF_FIFO_POP, PCBUF_COPROC_DONE, PCBUF_MOP_DONE,
    PCBUF_SEM_BASE,
    Semaphores,
    _SEM_WIN_LO,
)

from .conftest import spec


# Helpers

def _make_t():
    return TensixCoprocessor()


# ===========================================================================
# Address map
# ===========================================================================

@spec("PCBUF.ADDR.T0")
def test_pcbuf_t0_address():
    """PCBuf[0] is at 0xFFE80000."""
    assert PCBUF_T0 == 0xFFE80000


@spec("PCBUF.ADDR.T1")
def test_pcbuf_t1_address():
    """PCBuf[1] is at 0xFFE90000."""
    assert PCBUF_T1 == 0xFFE90000


@spec("PCBUF.ADDR.T2")
def test_pcbuf_t2_address():
    """PCBuf[2] is at 0xFFEA0000."""
    assert PCBUF_T2 == 0xFFEA0000


@spec("PCBUF.ADDR.STRIDE")
def test_pcbuf_stride():
    """PCBuf stride is 0x10000."""
    assert PCBUF_STRIDE == 0x10000
    assert PCBUF_T1 - PCBUF_T0 == PCBUF_STRIDE
    assert PCBUF_T2 - PCBUF_T1 == PCBUF_STRIDE


# ===========================================================================
# Memory-map offsets
# ===========================================================================

@spec("PCBUF.MMAP.OFFSET_00_FIFO_POP")
def test_pcbuf_fifo_pop_offset():
    """Offset 0x00 is the FIFO pop address."""
    assert PCBUF_FIFO_POP == 0x00


@spec("PCBUF.MMAP.OFFSET_04_COPROC_DONE")
def test_pcbuf_coproc_done_offset():
    """Offset 0x04 is CoprocessorDoneCheck."""
    assert PCBUF_COPROC_DONE == 0x04


@spec("PCBUF.MMAP.OFFSET_08_MOP_DONE")
def test_pcbuf_mop_done_offset():
    """Offset 0x08 is MOPExpanderDoneCheck."""
    assert PCBUF_MOP_DONE == 0x08


@spec("PCBUF.MMAP.OFFSET_20_SEM_WINDOW")
def test_pcbuf_sem_base_offset():
    """Offset 0x20 is the start of the semaphore window."""
    assert PCBUF_SEM_BASE == 0x20


@spec("PCBUF.MMAP.OFFSET_20_SEM_WINDOW")
def test_pcbuf_sem_window_spans_8_words():
    """Semaphore window covers 8 words: offsets 0x20..0x3C."""
    assert PCBUF_SEM_BASE == 0x20
    assert PCBUF_SEM_BASE + 7 * 4 == 0x3C


@spec("PCBUF.MMAP.OFFSET_20_SEM_WINDOW")
def test_pcbuf_sem_window_same_base_all_triscss():
    """All TRISCs access semaphores at 0xFFE80020 (same shared window)."""
    # The spec says all three TRISCs read the same semaphore window at the same
    # base address; we verify the constant matches the arithmetic.
    assert _SEM_WIN_LO == PCBUF_T0 + PCBUF_SEM_BASE


# ===========================================================================
# Semaphore window — read/write
# ===========================================================================

@spec("PCBUF.SEM.READ_RETURNS_VALUE")
@pytest.mark.parametrize("sem_idx", range(8))
def test_sem_read_returns_value(sem_idx):
    """Reading semaphore window word i returns the current semaphore value."""
    sems = Semaphores()
    sems.init(sem_idx, sem_idx + 1, 15)
    addr = _SEM_WIN_LO + sem_idx * 4
    assert sems.read32(addr) == sem_idx + 1


@spec("PCBUF.SEM.WRITE_0_IS_POST")
@pytest.mark.parametrize("sem_idx", range(8))
def test_sem_write_even_value_is_post(sem_idx):
    """Write with bit 0 == 0 performs SEMPOST (increments value)."""
    sems = Semaphores()
    sems.init(sem_idx, 0, 5)
    addr = _SEM_WIN_LO + sem_idx * 4
    sems.write32(addr, 0)   # bit 0 == 0 → SEMPOST
    assert sems.value[sem_idx] == 1


@spec("PCBUF.SEM.WRITE_1_IS_GET")
@pytest.mark.parametrize("sem_idx", range(8))
def test_sem_write_odd_value_is_get(sem_idx):
    """Write with bit 0 == 1 performs SEMGET (decrements value)."""
    sems = Semaphores()
    sems.init(sem_idx, 3, 5)
    addr = _SEM_WIN_LO + sem_idx * 4
    sems.write32(addr, 1)   # bit 0 == 1 → SEMGET
    assert sems.value[sem_idx] == 2


@spec("PCBUF.SEM.READ_RETURNS_VALUE", "PCBUF.SEM.WRITE_0_IS_POST")
def test_sem_post_multiple_times():
    """Multiple writes with bit0=0 increment semaphore, saturating at max."""
    sems = Semaphores()
    sems.init(0, 0, 3)
    addr = _SEM_WIN_LO
    for _ in range(5):
        sems.write32(addr, 0)
    assert sems.value[0] == 3  # saturated at max=3


@spec("PCBUF.SEM.READ_RETURNS_VALUE", "PCBUF.SEM.WRITE_1_IS_GET")
def test_sem_get_floors_at_zero():
    """SEMGET floors at 0."""
    sems = Semaphores()
    sems.init(0, 1, 5)
    addr = _SEM_WIN_LO
    sems.write32(addr, 1)  # SEMGET → 0
    sems.write32(addr, 1)  # SEMGET → still 0 (floor)
    assert sems.value[0] == 0


# ===========================================================================
# Emulator: read_pcbuf returns zero immediately
# ===========================================================================

@spec("PCBUF.EMU.READ_PCBUF_RETURNS_ZERO")
@pytest.mark.parametrize("thread_id", [0, 1, 2])
@pytest.mark.parametrize("offset", [PCBUF_COPROC_DONE, PCBUF_MOP_DONE])
def test_read_pcbuf_returns_zero(thread_id, offset):
    """read_pcbuf() returns 0 immediately in functional emulation."""
    t = _make_t()
    assert t.read_pcbuf(thread_id, offset) == 0


@spec("PCBUF.EMU.READ_PCBUF_RETURNS_ZERO")
def test_read_pcbuf_coproc_done_always_zero():
    """CoprocessorDoneCheck (offset 0x04) always returns 0 in emulator."""
    t = _make_t()
    # Even with instructions in the FIFO, read_pcbuf returns 0 immediately
    from emu.dsl import TT_NOP
    t.push_instruction(0, int(TT_NOP()))
    assert t.read_pcbuf(0, PCBUF_COPROC_DONE) == 0


# ===========================================================================
# Address consistency
# ===========================================================================

@spec("PCBUF.ADDR.T0", "PCBUF.MMAP.OFFSET_20_SEM_WINDOW")
def test_sem_window_lo_matches_pcbuf_t0_plus_sem_base():
    """_SEM_WIN_LO == PCBUF_T0 + PCBUF_SEM_BASE."""
    assert _SEM_WIN_LO == PCBUF_T0 + PCBUF_SEM_BASE
    assert _SEM_WIN_LO == 0xFFE80020
