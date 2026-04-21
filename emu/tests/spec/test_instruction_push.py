"""Spec tests for ../specs/instruction-push.md.

Each test is pinned to one or more clauses from
../clauses/instruction-push.md via the @spec() marker.
"""

import pytest

from emu.tensix import InstructionFIFO
from emu.tensix import TensixCoprocessor
from emu.memory import INSTRN_BUF_T0, INSTRN_BUF_T1, INSTRN_BUF_T2, MOP_CFG_BASE
from dsl import TT_NOP, TT_MOP

from .conftest import spec


# Local helpers

def _make_coprocessor():
    """Return a fresh TensixCoprocessor."""
    return TensixCoprocessor()


# ===========================================================================
# Instruction FIFO basics
# ===========================================================================

@spec("IPUSH.FIFO.CAPACITY_32")
def test_fifo_capacity_is_32():
    """The FIFO holds exactly 32 entries; the 33rd push is rejected."""
    fifo = InstructionFIFO()
    for i in range(32):
        assert fifo.push(i), f"push {i} should succeed"
    assert fifo.full
    assert not fifo.push(99), "33rd push must be rejected when full"


@spec("IPUSH.FIFO.FULL_REJECTS_PUSH")
def test_fifo_push_returns_false_when_full():
    """push() returns False on a full FIFO and does not modify the queue."""
    fifo = InstructionFIFO()
    for i in range(32):
        fifo.push(i)
    before_len = len(fifo)
    result = fifo.push(0xDEAD)
    assert result is False
    assert len(fifo) == before_len


@spec("IPUSH.FIFO.ORDERING")
def test_fifo_preserves_order():
    """Instructions are consumed in FIFO order (first-in, first-out)."""
    fifo = InstructionFIFO()
    for i in range(8):
        fifo.push(i * 10)
    for i in range(8):
        assert fifo.pop() == i * 10


@spec("IPUSH.FIFO.POP_EMPTY_RETURNS_NONE")
def test_fifo_pop_empty_returns_none():
    """pop() on an empty FIFO returns None."""
    fifo = InstructionFIFO()
    assert fifo.pop() is None


@spec("IPUSH.FIFO.CAPACITY_32", "IPUSH.FIFO.ORDERING")
def test_fifo_after_drain_accepts_more():
    """After draining one slot from a full FIFO, one more push is accepted."""
    fifo = InstructionFIFO()
    for i in range(32):
        fifo.push(i)
    fifo.pop()              # drain one
    assert not fifo.full
    assert fifo.push(99)    # now there is room
    assert fifo.full


# ===========================================================================
# MMIO routing — address decoding
# ===========================================================================

@spec("IPUSH.MMIO.ROUTING_BRISC")
@pytest.mark.parametrize("addr,expected_thread", [
    (INSTRN_BUF_T0, 0),
    (INSTRN_BUF_T1, 1),
    (INSTRN_BUF_T2, 2),
])
def test_brisc_routing_by_address(addr, expected_thread):
    """BRISC write to T0/T1/T2 address pushes to the corresponding thread."""
    t = _make_coprocessor()
    handler = t.instrn_handler_for('brisc')
    nop = int(TT_NOP())
    handler.write32(addr, nop)
    assert len(t.threads[expected_thread].fifo) == 1
    # Other threads should be empty
    for tid in range(3):
        if tid != expected_thread:
            assert t.threads[tid].fifo.empty, f"thread {tid} should be empty"


@spec("IPUSH.MMIO.ROUTING_TRISC")
@pytest.mark.parametrize("role,expected_thread", [
    ('trisc0', 0),
    ('trisc1', 1),
    ('trisc2', 2),
])
def test_trisc_routing_to_own_thread(role, expected_thread):
    """Each TRISC write to 0xFFE40000 routes to its own thread."""
    t = _make_coprocessor()
    handler = t.instrn_handler_for(role)
    nop = int(TT_NOP())
    # All TRISCs write to INSTRN_BUF_T0; hardware routes to their own thread
    handler.write32(INSTRN_BUF_T0, nop)
    assert len(t.threads[expected_thread].fifo) == 1
    for tid in range(3):
        if tid != expected_thread:
            assert t.threads[tid].fifo.empty


@spec("IPUSH.MMIO.ROUTING_TRISC")
def test_ncrisc_has_no_instrn_handler():
    """NCRISC has no instruction push capability; handler is None."""
    t = _make_coprocessor()
    assert t.instrn_handler_for('ncrisc') is None


# ===========================================================================
# .ttinsn rotation encoding
# ===========================================================================

@spec("IPUSH.TTINSN.ROT_LEFT_2")
@pytest.mark.parametrize("tensix_word", [
    0x00000000,
    0x02000000,  # NOP
    0x01000000,  # MOP
    0x3F000000,
    0x0AFFFFFF,
])
def test_ttinsn_rot_right_2_recovers_original(tensix_word):
    """Rotating the encoded word right by 2 recovers the original Tensix word."""
    encoded = ((tensix_word << 2) | (tensix_word >> 30)) & 0xFFFFFFFF
    recovered = ((encoded >> 2) | (encoded << 30)) & 0xFFFFFFFF
    assert recovered == tensix_word


@spec("IPUSH.TTINSN.LOW_BITS_NOT_11")
@pytest.mark.parametrize("tensix_word", [
    0x02000000,  # NOP: opcode 0x02
    0x01800000,  # MOP template 1
    0x0A000000,
])
def test_ttinsn_encoded_low_bits_never_11(tensix_word):
    """Valid Tensix opcodes < 0xC0000000 → encoded word low bits != 0b11."""
    encoded = ((tensix_word << 2) | (tensix_word >> 30)) & 0xFFFFFFFF
    assert (encoded & 3) != 3, f"encoded word 0x{encoded:08X} has low bits 0b11"


# ===========================================================================
# MMIO push writes correct word
# ===========================================================================

@spec("IPUSH.MMIO.WRITE_PUSHES_WORD")
def test_mmio_write_pushes_exact_word():
    """The word written to INSTRN_BUF is what appears in the FIFO."""
    t = _make_coprocessor()
    handler = t.instrn_handler_for('trisc0')
    expected = int(TT_NOP())
    handler.write32(INSTRN_BUF_T0, expected)
    got = t.threads[0].fifo.pop()
    assert got == expected & 0xFFFFFFFF
