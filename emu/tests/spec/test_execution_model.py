"""Spec tests for ../specs/execution-model.md.

Each test is pinned to one or more clauses from
../clauses/execution-model.md via the @spec() marker.
"""

import pytest

from emu.core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from emu.memory import Memory
from emu import dsl

from .conftest import spec


# Helpers

def _run1(insns, pc=0x100):
    """Build a BRISC with in_reset=False and run exactly len(insns) steps."""
    core = BRISC(pc=pc)
    core.in_reset = False
    core.load(pc, insns)
    core.run(len(insns))
    return core


# ===========================================================================
# Core types
# ===========================================================================

@spec("EXEC.CORES.FIVE_PER_TILE")
def test_five_core_classes_exist():
    """Emulator exposes exactly the five RISC-V core classes."""
    for cls in (BRISC, NCRISC, TRISC0, TRISC1, TRISC2):
        c = cls()
        assert c.ROLE is not None
        assert isinstance(c.ROLE, str)


@spec("EXEC.CORES.FIVE_PER_TILE")
@pytest.mark.parametrize("cls,expected_role", [
    (BRISC,  'brisc'),
    (NCRISC, 'ncrisc'),
    (TRISC0, 'trisc0'),
    (TRISC1, 'trisc1'),
    (TRISC2, 'trisc2'),
])
def test_core_roles(cls, expected_role):
    """Each core class reports the correct ROLE string."""
    assert cls.ROLE == expected_role


# ===========================================================================
# in_reset gating
# ===========================================================================

@spec("EXEC.CORES.IN_RESET_SKIP")
def test_in_reset_core_does_not_advance_pc():
    """Core with in_reset=True must not advance PC when step() is called."""
    core = BRISC(pc=0x100)
    assert core.in_reset is True
    core.load(0x100, [dsl.ADDI(dsl.a0, dsl.zero, 42)])
    core.step()
    # PC must not have advanced
    assert core.pc == 0x100
    assert core.regs[dsl.a0] == 0


@spec("EXEC.CORES.IN_RESET_SKIP")
def test_releasing_from_reset_allows_execution():
    """After setting in_reset=False, the next step() executes the instruction."""
    core = BRISC(pc=0x100)
    core.load(0x100, [dsl.ADDI(dsl.a0, dsl.zero, 7)])
    assert core.in_reset is True
    core.step()
    assert core.regs[dsl.a0] == 0  # still blocked

    core.in_reset = False
    core.step()
    assert core.regs[dsl.a0] == 7


# ===========================================================================
# One instruction per step
# ===========================================================================

@spec("EXEC.STEP.ONE_INSN")
def test_step_executes_exactly_one_instruction():
    """step() executes exactly one instruction; run(2) executes two."""
    core = BRISC(pc=0x100)
    core.in_reset = False
    core.load(0x100, [
        dsl.ADDI(dsl.a0, dsl.zero, 1),
        dsl.ADDI(dsl.a1, dsl.zero, 2),
    ])
    core.step()
    assert core.regs[dsl.a0] == 1
    assert core.regs[dsl.a1] == 0  # second insn not yet executed


@spec("EXEC.STEP.PC_ADVANCE")
def test_non_branch_advances_pc_by_4():
    """Non-branch instruction advances PC by exactly 4."""
    core = BRISC(pc=0x200)
    core.in_reset = False
    core.load(0x200, [dsl.ADDI(dsl.a0, dsl.zero, 0)])
    core.step()
    assert core.pc == 0x204


@spec("EXEC.STEP.BRANCH_TAKEN")
def test_taken_branch_sets_pc_to_offset():
    """BEQ with equal operands sets PC = old_PC + imm."""
    core = BRISC(pc=0x100)
    core.in_reset = False
    # BEQ a0, a0, +8 — always taken since a0 == a0
    core.load(0x100, [dsl.BEQ(dsl.a0, dsl.a0, 8)])
    core.step()
    assert core.pc == 0x108


@spec("EXEC.STEP.BRANCH_TAKEN")
def test_not_taken_branch_falls_through():
    """BEQ with unequal operands does NOT jump."""
    core = BRISC(pc=0x100)
    core.in_reset = False
    core.load(0x100, [
        dsl.ADDI(dsl.a0, dsl.zero, 1),
        dsl.ADDI(dsl.a1, dsl.zero, 2),
        dsl.BEQ(dsl.a0, dsl.a1, 8),  # not taken
    ])
    core.run(3)
    assert core.pc == 0x10C  # fell through


@spec("EXEC.STEP.RETURNS_FALSE_ON_STUCK")
def test_step_returns_false_on_infinite_loop():
    """step() returns False when PC does not advance (self-loop)."""
    core = BRISC(pc=0x100)
    core.in_reset = False
    # JAL x0, 0 — jump to self (offset 0, same PC)
    core.load(0x100, [dsl.JAL(dsl.zero, 0)])
    result = core.step()
    assert result is False


@spec("EXEC.STEP.RETURNS_FALSE_ON_STUCK")
def test_step_returns_true_on_normal_advance():
    """step() returns True when PC advances normally."""
    core = BRISC(pc=0x100)
    core.in_reset = False
    core.load(0x100, [dsl.ADDI(dsl.a0, dsl.zero, 0)])
    result = core.step()
    assert result is True


# ===========================================================================
# Register file invariants
# ===========================================================================

@spec("EXEC.REGFILE.X0_IMMUTABLE")
def test_x0_is_hardwired_zero():
    """Register x0 is hardwired to 0; writes are silently discarded."""
    core = _run1([dsl.ADDI(dsl.zero, dsl.zero, 99)])
    assert core.regs[0] == 0


@spec("EXEC.REGFILE.X0_IMMUTABLE")
@pytest.mark.parametrize("insn", [
    dsl.ADDI(dsl.zero, dsl.zero, 42),
    dsl.LUI(dsl.zero, 0xABCDE000),
])
def test_x0_stays_zero_for_various_writes(insn):
    """Any instruction that nominally writes to x0 leaves it as 0."""
    core = _run1([insn])
    assert core.regs[0] == 0


@spec("EXEC.REGFILE.THIRTY_TWO_REGS")
def test_register_file_has_32_entries():
    """The emulator initialises exactly 32 integer registers."""
    core = BRISC()
    assert len(core.regs) == 32


@spec("EXEC.REGFILE.THIRTY_TWO_REGS")
def test_all_registers_start_at_zero():
    """All 32 registers start at 0 on a fresh core."""
    core = BRISC()
    assert all(r == 0 for r in core.regs)


# ===========================================================================
# run() helper
# ===========================================================================

@spec("EXEC.RUN.STOPS_ON_STUCK")
def test_run_exits_early_on_self_loop():
    """run(100) on a self-loop exits after 1 step, not 100."""
    core = BRISC(pc=0x100)
    core.in_reset = False
    core.load(0x100, [dsl.JAL(dsl.zero, 0)])
    steps = core.run(100)
    # run() returns the step count at which it stopped
    assert steps == 1
