"""Spec tests for ../specs/mop-and-replay-expanders.md.

Each test is pinned to one or more clauses from
../clauses/mop-and-replay-expanders.md via the @spec() marker.
Tests for the hardware bug (MOP.T1.HW_BUG_OUTER_COUNT) are included and
expected to pass — the emulator correctly replicates the bug.
"""

import pytest

from emu.tensix import InstructionFIFO, MOPExpander, ReplayExpander
from emu.tensix import TensixCoprocessor
from emu.memory import MOP_CFG_BASE
from dsl import TT_NOP, TT_MOP, TT_REPLAY, TT_SEMPOST, TT_SEMINIT

from .conftest import spec


# Helpers

NOP_WORD = int(TT_NOP())


def _drain(expander, n=200):
    """Drain up to n instructions from a MOPExpander (pass fifo=empty FIFO)."""
    fifo = InstructionFIFO()
    results = []
    for _ in range(n):
        r = expander.next(fifo)
        if r is not None:
            results.append(r)
    return results


def _drain_replay(replay, mop, fifo, n=200):
    """Drain up to n instructions from a ReplayExpander."""
    results = []
    for _ in range(n):
        r = replay.next(mop, fifo)
        if r is not None:
            results.append(r)
    return results


# ===========================================================================
# MOP Expander — opcode detection
# ===========================================================================

@spec("MOP.OPCODE.PASSTHROUGH")
@pytest.mark.parametrize("opcode", [0x00, 0x02, 0xA2, 0xA6, 0x42, 0xFF])
def test_mop_passthrough_non_mop_opcodes(opcode):
    """Instructions with opcodes other than 0x01 and 0x03 pass through unchanged."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    word = opcode << 24
    fifo.push(word)
    got = mop.next(fifo)
    assert got == word


@spec("MOP.OPCODE.MOP_CFG")
def test_mop_cfg_consumed_not_emitted():
    """MOP_CFG (opcode 0x03) is consumed; it does not appear downstream."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop_cfg_word = (0x03 << 24) | 0xABCD
    fifo.push(mop_cfg_word)
    result = mop.next(fifo)
    assert result is None


@spec("MOP.OPCODE.MOP_CFG")
def test_mop_cfg_sets_mask_hi():
    """After MOP_CFG, mask_hi equals word & 0xFFFF."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    fifo.push((0x03 << 24) | 0xDEAD)
    mop.next(fifo)
    assert mop.mask_hi == 0xDEAD


@spec("MOP.OPCODE.MOP")
def test_mop_word_decoded_from_opcode_01():
    """MOP opcode 0x01 triggers expansion rather than pass-through."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    # Minimal Template 1: OuterCount=1, InnerCount=1, all NOP
    mop.cfg = [1, 1, NOP_WORD, NOP_WORD, NOP_WORD,
               0x11000000, NOP_WORD, 0x22000000, 0x33000000]
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(5):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # Should get Loop0Last (only inner, only outer)
    assert results == [0x22000000]


# ===========================================================================
# MOP configuration registers
# ===========================================================================

@spec("MOP.MOPCFG.9_REGS")
def test_mop_cfg_9_registers():
    """MopCfg has exactly 9 registers indexed 0..8."""
    mop = MOPExpander()
    assert len(mop.cfg) == 9


@spec("MOP.MOPCFG.WRITE_ONLY")
def test_mop_cfg_write_only_returns_zero():
    """MopCfg handler read32 returns 0 (write-only)."""
    t = TensixCoprocessor()
    handler = t.mop_handler_for('trisc0')
    # Write something, then read back
    handler.write32(MOP_CFG_BASE, 0xDEADBEEF)
    assert handler.read32(MOP_CFG_BASE) == 0
    assert handler.read16(MOP_CFG_BASE) == 0
    assert handler.read8(MOP_CFG_BASE) == 0


@spec("MOP.MOPCFG.9_REGS")
def test_mop_cfg_handler_indexes_0_through_8():
    """Writing to MOP_CFG_BASE + i*4 for i in 0..8 sets cfg[i]."""
    t = TensixCoprocessor()
    handler = t.mop_handler_for('trisc1')
    for i in range(9):
        handler.write32(MOP_CFG_BASE + i * 4, 0x100 + i)
    for i in range(9):
        assert t.threads[1].mop.cfg[i] == 0x100 + i


# ===========================================================================
# Template 0
# ===========================================================================

@spec("MOP.T0.ITERATION_COUNT")
@pytest.mark.parametrize("count1,expected_iters", [
    (0, 1),
    (1, 2),
    (7, 8),
    (31, 32),
])
def test_template0_iteration_count(count1, expected_iters):
    """Template 0 iterates Count1 + 1 times."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[1] = 0          # Flags: no HasB, no HasA123
    mop.cfg[3] = 0xAA000000  # InsnA0
    mop.cfg[7] = NOP_WORD   # SkipA0
    # Mask = 0 → all 0-bits → all use InsnA0 path
    fifo.push((0x01 << 24) | (0 << 23) | (count1 << 16) | 0)
    results = []
    for _ in range(300):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    assert len(results) == expected_iters


@spec("MOP.T0.MASK_SELECTS_PATH")
def test_template0_mask_zero_bit_emits_insn_a0():
    """Mask bit 0 == 0 → emit InsnA0 for that iteration."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[1] = 0          # Flags: no HasB, no HasA123
    mop.cfg[3] = 0xBB000000  # InsnA0
    mop.cfg[7] = 0xCC000000  # SkipA0
    # Mask = 0b10 → iteration 0 has bit 0 == 0 (InsnA0), iteration 1 has bit 1 == 1 (SkipA0)
    mask_lo = 0b10
    fifo.push((0x01 << 24) | (0 << 23) | (1 << 16) | mask_lo)  # Count1=1
    results = []
    for _ in range(10):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    assert results == [0xBB000000, 0xCC000000]


@spec("MOP.T0.MASK_SELECTS_PATH")
def test_template0_mask_one_bit_emits_skip_a0():
    """Mask bit i == 1 → emit SkipA0 for iteration i."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[1] = 0
    mop.cfg[3] = 0xBB000000  # InsnA0
    mop.cfg[7] = 0xCC000000  # SkipA0
    # Mask = 0b11 → both iterations use SkipA0
    fifo.push((0x01 << 24) | (0 << 23) | (1 << 16) | 0b11)
    results = []
    for _ in range(10):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    assert results == [0xCC000000, 0xCC000000]


@spec("MOP.T0.MASK32_FROM_CFG_AND_MOP")
def test_template0_mask32_combines_mask_hi_and_lo():
    """Full mask = (MaskHi << 16) | MaskLo; iteration 16 uses MaskHi bit 0."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.mask_hi = 0x0001    # bit 16 of full mask = 1 → skip on iter 16
    mop.cfg[1] = 0
    mop.cfg[3] = 0xAA000000  # InsnA0
    mop.cfg[7] = 0xBB000000  # SkipA0
    # Count1=16 → 17 iterations; MaskLo=0 (bits 0-15 all 0 = InsnA0),
    # MaskHi bit 0 = 1 → iteration 16 = SkipA0
    fifo.push((0x01 << 24) | (0 << 23) | (16 << 16) | 0x0000)
    results = []
    for _ in range(50):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    assert len(results) == 17
    assert results[0] == 0xAA000000   # iter 0 (bit 0 == 0)
    assert results[15] == 0xAA000000  # iter 15 (bit 15 == 0)
    assert results[16] == 0xBB000000  # iter 16 (bit 16 == 1 from MaskHi)


@spec("MOP.T0.HAS_B")
def test_template0_has_b_emits_insn_b():
    """HasB=1: InsnB is emitted after InsnA0 on unmasked iterations."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[1] = 1           # HasB=1
    mop.cfg[2] = 0xCC000000  # InsnB
    mop.cfg[3] = 0xAA000000  # InsnA0
    mop.cfg[7] = NOP_WORD    # SkipA0
    mop.cfg[8] = NOP_WORD    # SkipB
    # Mask = 0 → emit path: InsnA0, InsnB
    fifo.push((0x01 << 24) | (0 << 23) | (0 << 16) | 0)
    results = []
    for _ in range(10):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    assert results == [0xAA000000, 0xCC000000]


@spec("MOP.T0.HAS_A123")
def test_template0_has_a123_emits_a1_a2_a3():
    """HasA123=1: InsnA1/A2/A3 are emitted after InsnA0 on unmasked iterations."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[1] = 2           # HasA123=1
    mop.cfg[3] = 0xA0000000  # InsnA0
    mop.cfg[4] = 0xA1000000  # InsnA1
    mop.cfg[5] = 0xA2000000  # InsnA2
    mop.cfg[6] = 0xA3000000  # InsnA3
    mop.cfg[7] = NOP_WORD    # SkipA0
    # Mask = 0 → emit path: InsnA0, InsnA1, InsnA2, InsnA3
    fifo.push((0x01 << 24) | (0 << 23) | (0 << 16) | 0)
    results = []
    for _ in range(10):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    assert results == [0xA0000000, 0xA1000000, 0xA2000000, 0xA3000000]


# ===========================================================================
# Template 1 — basic loop structure
# ===========================================================================

@spec("MOP.T1.OUTER_INNER_LOOP")
def test_template1_outer_inner_count():
    """Template 1: OuterCount * InnerCount inner loop instructions emitted."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 2          # OuterCount=2
    mop.cfg[1] = 3          # InnerCount=3
    mop.cfg[2] = NOP_WORD   # StartOp=NOP (skipped)
    mop.cfg[3] = NOP_WORD   # EndOp0=NOP (skipped)
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = 0xAA000000  # LoopOp
    mop.cfg[6] = NOP_WORD   # LoopOp1=NOP (no alternation)
    mop.cfg[7] = 0xBB000000  # Loop0Last
    mop.cfg[8] = 0xCC000000  # Loop1Last
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(20):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # 2 outer × 3 inner = 6 total
    # j=0: i=0 LoopOp, i=1 LoopOp, i=2(last inner, not last outer) Loop1Last
    # j=1: i=0 LoopOp, i=1 LoopOp, i=2(last inner, last outer) Loop0Last
    assert results == [
        0xAA000000, 0xAA000000, 0xCC000000,
        0xAA000000, 0xAA000000, 0xBB000000,
    ]


@spec("MOP.T1.OUTER_INNER_LOOP")
def test_template1_count_uses_only_7_bits():
    """Only bits [6:0] of cfg[0] and cfg[1] are used (mask & 127)."""
    mop = MOPExpander()
    mop.cfg[0] = 0b1_0000001  # bit 7 set, bits 6:0 = 1 → OuterCount=1
    mop.cfg[1] = 0b1_0000001  # bit 7 set, bits 6:0 = 1 → InnerCount=1
    mop.cfg[2] = NOP_WORD
    mop.cfg[3] = NOP_WORD
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = 0xAA000000
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xBB000000
    mop.cfg[8] = 0xCC000000
    fifo = InstructionFIFO()
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(10):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # 1 outer × 1 inner; last inner of last outer → Loop0Last
    assert results == [0xBB000000]


@spec("MOP.T1.START_OP_EMITTED")
def test_template1_start_op_emitted_per_outer():
    """StartOp is emitted once per outer iteration when non-NOP."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 2          # OuterCount=2
    mop.cfg[1] = 1          # InnerCount=1
    mop.cfg[2] = 0x11000000  # StartOp (non-NOP)
    mop.cfg[3] = NOP_WORD
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = 0xAA000000
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xBB000000
    mop.cfg[8] = 0xCC000000
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(20):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # j=0: StartOp, Loop1Last; j=1: StartOp, Loop0Last
    assert results.count(0x11000000) == 2


@spec("MOP.T1.END_OPS_EMITTED")
def test_template1_end_ops_emitted_per_outer():
    """EndOp0 and EndOp1 are emitted after each inner loop when non-NOP."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 2
    mop.cfg[1] = 1
    mop.cfg[2] = NOP_WORD
    mop.cfg[3] = 0x22000000  # EndOp0
    mop.cfg[4] = 0x33000000  # EndOp1
    mop.cfg[5] = 0xAA000000
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xBB000000
    mop.cfg[8] = 0xCC000000
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(20):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # Each outer iter ends with EndOp0, EndOp1
    assert results.count(0x22000000) == 2
    assert results.count(0x33000000) == 2


@spec("MOP.T1.END_OPS_EMITTED")
def test_template1_end_op1_skipped_if_end_op0_is_nop():
    """EndOp1 is skipped if EndOp0 is NOP."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 1
    mop.cfg[1] = 1
    mop.cfg[2] = NOP_WORD
    mop.cfg[3] = NOP_WORD    # EndOp0=NOP → EndOp1 also skipped
    mop.cfg[4] = 0x44000000  # EndOp1 (should not appear)
    mop.cfg[5] = 0xAA000000
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xBB000000
    mop.cfg[8] = 0xCC000000
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(10):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    assert 0x44000000 not in results


@spec("MOP.T1.LOOP0_LAST_OVERRIDE")
def test_template1_loop0_last_replaces_last_inner_of_last_outer():
    """Loop0Last replaces LoopOp on the last inner of the last outer."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 2
    mop.cfg[1] = 2
    mop.cfg[2] = NOP_WORD
    mop.cfg[3] = NOP_WORD
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = 0xAA000000  # LoopOp
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xBB000000  # Loop0Last
    mop.cfg[8] = 0xCC000000  # Loop1Last
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(20):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # Last element must be Loop0Last
    assert results[-1] == 0xBB000000


@spec("MOP.T1.LOOP1_LAST_OVERRIDE")
def test_template1_loop1_last_replaces_last_inner_of_non_last_outer():
    """Loop1Last replaces LoopOp on the last inner of a non-last outer."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 2
    mop.cfg[1] = 2
    mop.cfg[2] = NOP_WORD
    mop.cfg[3] = NOP_WORD
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = 0xAA000000
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xBB000000  # Loop0Last
    mop.cfg[8] = 0xCC000000  # Loop1Last
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(20):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # j=0: i=0 LoopOp=AA, i=1(last inner, not last outer)→Loop1Last=CC
    # j=1: i=0 LoopOp=AA, i=1(last inner, last outer)→Loop0Last=BB
    assert results == [0xAA000000, 0xCC000000, 0xAA000000, 0xBB000000]


# ===========================================================================
# Template 1 — alternating LoopOp
# ===========================================================================

@spec("MOP.T1.ALTERNATING_LOOP_OP")
def test_template1_alternating_loop_ops_doubles_inner_count():
    """When LoopOp1 is non-NOP, InnerCount doubles and ops alternate."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 1           # OuterCount=1
    mop.cfg[1] = 2           # InnerCount=2 → doubles to 4
    mop.cfg[2] = NOP_WORD
    mop.cfg[3] = NOP_WORD
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = 0xAA000000  # LoopOp
    mop.cfg[6] = 0xBB000000  # LoopOp1 (non-NOP)
    mop.cfg[7] = 0xCC000000  # Loop0Last
    mop.cfg[8] = 0xDD000000  # Loop1Last
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(10):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # InnerCount=4; i=0: AA, i=1: BB, i=2: AA, i=3(last inner, last outer): CC
    assert results == [0xAA000000, 0xBB000000, 0xAA000000, 0xCC000000]


# ===========================================================================
# Template 1 — hardware bug
# ===========================================================================

@spec("MOP.T1.HW_BUG_OUTER_COUNT")
def test_template1_hw_bug_triggers():
    """HW bug: OuterCount=1, NOP StartOp, InnerCount=0, non-NOP EndOp0 → OuterCount += 128."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 1           # OuterCount=1
    mop.cfg[1] = 0           # InnerCount=0
    mop.cfg[2] = NOP_WORD    # StartOp=NOP (trigger condition)
    mop.cfg[3] = 0xBB000000  # EndOp0=non-NOP (trigger condition)
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = 0xCC000000  # LoopOp (irrelevant — inner=0)
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xDD000000
    mop.cfg[8] = 0xEE000000
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(300):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # OuterCount → 129; each outer iteration: no inner loop, just EndOp0
    assert len(results) == 129
    assert all(r == 0xBB000000 for r in results)


@spec("MOP.T1.HW_BUG_OUTER_COUNT")
def test_template1_hw_bug_does_not_trigger_with_non_nop_start():
    """HW bug does NOT trigger if StartOp is non-NOP."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    mop.cfg[0] = 1
    mop.cfg[1] = 0
    mop.cfg[2] = 0x11000000  # StartOp=non-NOP → bug NOT triggered
    mop.cfg[3] = 0xBB000000
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = NOP_WORD
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xDD000000
    mop.cfg[8] = 0xEE000000
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(300):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # OuterCount stays 1; 1 outer × 0 inner = 0 + StartOp + EndOp0
    assert len(results) == 2  # StartOp + EndOp0
    assert results[0] == 0x11000000
    assert results[1] == 0xBB000000


@spec("MOP.T1.HW_BUG_OUTER_COUNT", "MOP.ISNOP.ONLY_OPCODE_02")
def test_template1_hw_bug_dmanop_is_not_nop():
    """HW bug condition: DMANOP (opcode 0x60) as StartOp is NOT treated as NOP → bug not triggered."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    dmanop_word = 0x60000000  # DMANOP opcode
    mop.cfg[0] = 1
    mop.cfg[1] = 0
    mop.cfg[2] = dmanop_word  # StartOp = DMANOP (NOT NOP for IsNop check)
    mop.cfg[3] = 0xBB000000   # EndOp0 non-NOP
    mop.cfg[4] = NOP_WORD
    mop.cfg[5] = NOP_WORD
    mop.cfg[6] = NOP_WORD
    mop.cfg[7] = 0xDD000000
    mop.cfg[8] = 0xEE000000
    fifo.push(int(TT_MOP(1, 0, 0)))
    results = []
    for _ in range(300):
        r = mop.next(fifo)
        if r is not None:
            results.append(r)
    # DMANOP is not plain NOP (0x02) → bug not triggered → OuterCount stays 1
    # 1 outer, 0 inner → emit StartOp(DMANOP) + EndOp0
    assert len(results) == 2
    assert results[0] == dmanop_word
    assert results[1] == 0xBB000000


# ===========================================================================
# IsNop semantics
# ===========================================================================

@spec("MOP.ISNOP.ONLY_OPCODE_02")
@pytest.mark.parametrize("word,should_be_nop", [
    (0x02000000, True),   # plain NOP
    (0x60000000, False),  # DMANOP
    (0x8F000000, False),  # SFPNOP
    (0x00000000, False),  # zero word
    (0x02FFFFFF, True),   # NOP opcode, non-zero params
])
def test_is_nop_only_opcode_02(word, should_be_nop):
    """_is_nop() returns True only for opcode 0x02."""
    from emu.tensix import _is_nop
    assert _is_nop(word) == should_be_nop


# ===========================================================================
# Replay Expander — pass-through
# ===========================================================================

@spec("REPLAY.OPCODE")
def test_replay_opcode_and_field_layout_recognised():
    """REPLAY has opcode 0x04; bits[23:14]=start_idx (low 5 bits used),
    bits[13:4]=len (low 6 bits; 0 means 64), bit[1]=exec_while_loading,
    bit[0]=load_mode. Verify the decoder (a) recognises 0x04 as REPLAY —
    playback emits the recorded buffer — and (b) honours the start_idx
    / len fields by reading those specific slots."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    # Pre-seed buffer with sentinel values at known slots.
    for i in range(32):
        replay.buffer[i] = 0xA0000000 | i
    # REPLAY: start_idx=5, len=3, exec_while_loading=0, load_mode=0 (playback).
    # Layout: opcode<<24 | start_idx<<14 | len<<4 | exec<<1 | load
    start_idx, length = 5, 3
    word = (0x04 << 24) | (start_idx << 14) | (length << 4) | 0
    fifo.push(word)
    # First three replay.next() calls must yield buffer[5], buffer[6], buffer[7].
    got = [replay.next(mop, fifo) for _ in range(3)]
    assert got == [0xA0000000 | 5, 0xA0000000 | 6, 0xA0000000 | 7], \
           f"REPLAY opcode/fields not honoured: got {[hex(g) for g in got]}"


@spec("REPLAY.PASSTHROUGH")
@pytest.mark.parametrize("opcode", [0x00, 0x02, 0xA2, 0xFF])
def test_replay_passthrough_non_replay_opcodes(opcode):
    """Instructions with opcodes other than 0x04 pass through Replay unchanged.

    Note: opcodes 0x01 (MOP) and 0x03 (MOP_CFG) are intercepted by the MOP
    Expander before reaching the Replay Expander, so they are not included here.
    """
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    word = opcode << 24
    fifo.push(word)
    got = replay.next(mop, fifo)
    assert got == word


# ===========================================================================
# Replay Expander — buffer
# ===========================================================================

@spec("REPLAY.BUFFER_32_SLOTS")
def test_replay_buffer_has_32_slots():
    """The replay buffer has exactly 32 slots."""
    replay = ReplayExpander()
    assert len(replay.buffer) == 32


# ===========================================================================
# Replay Expander — record mode
# ===========================================================================

@spec("REPLAY.RECORD.STORES_INSTRUCTIONS")
def test_replay_record_stores_into_buffer():
    """Record mode stores next N instructions into buffer at correct slots."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    record_word = int(TT_REPLAY(start_idx=0, len=3,
                                execute_while_loading=0, load_mode=1))
    fifo.push(record_word)
    fifo.push(0x11000000)
    fifo.push(0x22000000)
    fifo.push(0x33000000)
    for _ in range(10):
        replay.next(mop, fifo)
    assert replay.buffer[0] == 0x11000000
    assert replay.buffer[1] == 0x22000000
    assert replay.buffer[2] == 0x33000000


@spec("REPLAY.RECORD.NO_OUTPUT_WHEN_EXEC_0")
def test_replay_record_no_output_when_exec_0():
    """Record with exec=0 produces no downstream output."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    fifo.push(int(TT_REPLAY(start_idx=0, len=2, execute_while_loading=0, load_mode=1)))
    fifo.push(0xAAAAAAAA)
    fifo.push(0xBBBBBBBB)
    results = []
    for _ in range(10):
        r = replay.next(mop, fifo)
        if r is not None:
            results.append(r)
    assert results == []


@spec("REPLAY.RECORD.EXEC_WHILE_LOADING")
def test_replay_record_exec_1_emits_each_instruction():
    """Record with exec=1 emits each instruction as it is recorded."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    fifo.push(int(TT_REPLAY(start_idx=0, len=2, execute_while_loading=1, load_mode=1)))
    fifo.push(0xAAAAAAAA)
    fifo.push(0xBBBBBBBB)
    results = []
    for _ in range(10):
        r = replay.next(mop, fifo)
        if r is not None:
            results.append(r)
    assert results == [0xAAAAAAAA, 0xBBBBBBBB]


# ===========================================================================
# Replay Expander — playback mode
# ===========================================================================

@spec("REPLAY.PLAYBACK.EMITS_FROM_BUFFER", "REPLAY.RECORD.STORES_INSTRUCTIONS")
def test_replay_record_then_playback():
    """Record then playback emits the stored instructions in order."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    # Record 3 instructions at slot 5
    fifo.push(int(TT_REPLAY(start_idx=5, len=3, execute_while_loading=0, load_mode=1)))
    fifo.push(0x11000000)
    fifo.push(0x22000000)
    fifo.push(0x33000000)
    for _ in range(10):
        replay.next(mop, fifo)

    # Playback
    fifo.push(int(TT_REPLAY(start_idx=5, len=3, execute_while_loading=0, load_mode=0)))
    results = []
    for _ in range(10):
        r = replay.next(mop, fifo)
        if r is not None:
            results.append(r)
    assert results == [0x11000000, 0x22000000, 0x33000000]


@spec("REPLAY.PLAYBACK.WRAP_MOD32")
def test_replay_buffer_wraps_mod32():
    """Replay buffer index wraps mod 32: start=31, len=2 → slots 31 then 0."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    fifo.push(int(TT_REPLAY(start_idx=31, len=2, execute_while_loading=0, load_mode=1)))
    fifo.push(0xAA000000)  # slot 31
    fifo.push(0xBB000000)  # slot 0 (wraps)
    for _ in range(10):
        replay.next(mop, fifo)
    assert replay.buffer[31] == 0xAA000000
    assert replay.buffer[0] == 0xBB000000

    fifo.push(int(TT_REPLAY(start_idx=31, len=2, execute_while_loading=0, load_mode=0)))
    results = []
    for _ in range(10):
        r = replay.next(mop, fifo)
        if r is not None:
            results.append(r)
    assert results == [0xAA000000, 0xBB000000]


@spec("REPLAY.COUNT_ZERO_MEANS_64")
def test_replay_count_zero_means_64():
    """REPLAY len=0 plays back exactly 64 instructions (two passes through buffer)."""
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    for i in range(32):
        replay.buffer[i] = 0x100 + i
    fifo.push(int(TT_REPLAY(start_idx=0, len=0, execute_while_loading=0, load_mode=0)))
    results = []
    for _ in range(70):
        r = replay.next(mop, fifo)
        if r is not None:
            results.append(r)
    assert len(results) == 64
    for i in range(32):
        assert results[i] == 0x100 + i
        assert results[32 + i] == 0x100 + i


# ===========================================================================
# MOP + Replay composition
# ===========================================================================

@spec("MOP.OPCODE.MOP", "REPLAY.PLAYBACK.EMITS_FROM_BUFFER")
def test_mop_emitting_replay_instructions_expanded():
    """A MOP expansion that emits REPLAY instructions is further expanded by Replay."""
    t = TensixCoprocessor()
    sems = t.semaphores
    sems.init(1, 0, 15)

    # Configure MOP Template 1: outer=1, inner=3, LoopOp=SEMPOST
    # (same as integration test in test_tensix.py but expressed through coprocessor)
    nop = int(TT_NOP())
    sempost = int(TT_SEMPOST(sem_sel=0x02))
    t.write_mop_cfg(0, 0, 1)       # OuterCount=1
    t.write_mop_cfg(0, 1, 3)       # InnerCount=3
    t.write_mop_cfg(0, 2, nop)
    t.write_mop_cfg(0, 3, nop)
    t.write_mop_cfg(0, 4, nop)
    t.write_mop_cfg(0, 5, sempost)  # LoopOp = SEMPOST
    t.write_mop_cfg(0, 6, nop)
    t.write_mop_cfg(0, 7, sempost)  # Loop0Last = SEMPOST
    t.write_mop_cfg(0, 8, sempost)  # Loop1Last = SEMPOST
    t.push_instruction(0, int(TT_MOP(1, 0, 0)))

    for _ in range(20):
        t.step()

    # 3 inner iterations → 3 SEMPOSTs → sem[1] value = 3
    assert sems.value[1] == 3
