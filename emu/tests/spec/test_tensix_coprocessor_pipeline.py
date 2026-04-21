"""Spec tests for ../specs/tensix-coprocessor-pipeline.md.

Each test is pinned to one or more clauses from
../clauses/tensix-coprocessor-pipeline.md via the @spec() marker.
"""

import pytest

from emu.tensix import TensixCoprocessor
from emu.tensix import TensixThread, InstructionFIFO, MOPExpander
from emu.memory import (
    INSTRN_BUF_T0, INSTRN_BUF_T1, INSTRN_BUF_T2,
    MOP_CFG_BASE,
)
from dsl import (
    TT_NOP, TT_MOP, TT_SEMINIT, TT_SEMPOST, TT_SEMGET,
    TT_STALLWAIT, TT_SEMWAIT, TT_SETC16, TT_MVMUL, TT_SETDMAREG,
    decode_tensix,
)

from .conftest import spec


# Helpers

NOP_WORD = int(TT_NOP())


def _make_t():
    return TensixCoprocessor()


# ===========================================================================
# Thread model
# ===========================================================================

@spec("TCP.THREADS.THREE_INDEPENDENT")
def test_coprocessor_has_three_threads():
    """TensixCoprocessor has exactly 3 independent threads."""
    t = _make_t()
    assert len(t.threads) == 3
    for i, thread in enumerate(t.threads):
        assert thread.id == i


@spec("TCP.THREADS.THREE_INDEPENDENT")
def test_each_thread_has_own_fifo_mop_replay_waitgate():
    """Each thread has independent FIFO, MOP Expander, Replay Expander, Wait Gate."""
    t = _make_t()
    for i in range(3):
        th = t.threads[i]
        assert hasattr(th, 'fifo')
        assert hasattr(th, 'mop')
        assert hasattr(th, 'replay')
        assert hasattr(th, 'wait_gate')
        # All objects are distinct instances
        for j in range(3):
            if i != j:
                assert th.fifo is not t.threads[j].fifo
                assert th.mop is not t.threads[j].mop


@spec("TCP.THREADS.INDEPENDENT_STEP")
def test_step_advances_all_three_threads():
    """step() drains one instruction from each non-empty thread."""
    t = _make_t()
    for tid in range(3):
        t.push_instruction(tid, NOP_WORD)
    t.step()
    for tid in range(3):
        assert t.threads[tid].fifo.empty


@spec("TCP.THREADS.INDEPENDENT_STEP")
def test_step_does_not_block_other_threads_when_one_stalls():
    """One thread blocked does not prevent other threads from advancing."""
    t = _make_t()
    from emu.tensix import STALL_MATH, COND_SRCA_VLD
    # Force T0's SrcA FPU bank to wrong owner so its STALLWAIT never releases
    t.srca.banks[t.srca.fpu_bank].allowed_client = "unpackers"
    # Install a stall in T0
    t.threads[0].wait_gate.install_stallwait(STALL_MATH, COND_SRCA_VLD)

    # Push instructions to T1 and T2
    t.push_instruction(1, NOP_WORD)
    t.push_instruction(2, NOP_WORD)

    t.step()

    # T1 and T2 should be drained; T0 still has its gate active
    assert t.threads[1].fifo.empty
    assert t.threads[2].fifo.empty
    assert t.threads[0].wait_gate.opcode == "STALLWAIT"


# ===========================================================================
# RISC-V role mapping
# ===========================================================================

@spec("TCP.ROLES.BRISC_ALL_FIFOS")
@pytest.mark.parametrize("addr,tid", [
    (INSTRN_BUF_T0, 0),
    (INSTRN_BUF_T1, 1),
    (INSTRN_BUF_T2, 2),
])
def test_brisc_can_push_to_all_threads(addr, tid):
    """BRISC can push to T0/T1/T2 via the three instruction buffer addresses."""
    t = _make_t()
    h = t.instrn_handler_for('brisc')
    assert h is not None
    h.write32(addr, NOP_WORD)
    assert len(t.threads[tid].fifo) == 1


@spec("TCP.ROLES.NCRISC_NO_PUSH")
def test_ncrisc_handler_is_none():
    """instrn_handler_for('ncrisc') returns None."""
    t = _make_t()
    assert t.instrn_handler_for('ncrisc') is None


@spec("TCP.ROLES.TRISC_OWN_THREAD")
@pytest.mark.parametrize("role,tid", [
    ('trisc0', 0), ('trisc1', 1), ('trisc2', 2),
])
def test_trisc_pushes_to_own_thread(role, tid):
    """Each TRISC handler pushes only to its own thread."""
    t = _make_t()
    h = t.instrn_handler_for(role)
    h.write32(INSTRN_BUF_T0, NOP_WORD)
    assert len(t.threads[tid].fifo) == 1
    for other in range(3):
        if other != tid:
            assert t.threads[other].fifo.empty


# ===========================================================================
# Instruction encoding
# ===========================================================================

@spec("TCP.ENCODING.32BIT_WORD")
def test_instruction_encoding_opcode_in_high_byte():
    """Tensix instruction: bits[31:24] = opcode, bits[23:0] = parameters."""
    nop = int(TT_NOP())
    assert (nop >> 24) & 0xFF == 0x02
    seminit = int(TT_SEMINIT(max_value=2, init_value=1, sem_sel=0x02))
    assert (seminit >> 24) & 0xFF == 0xA3


# ===========================================================================
# Frontend pipeline ordering
# ===========================================================================

@spec("TCP.PIPELINE.FIFO_MOP_REPLAY_WAIT")
def test_pipeline_order_mop_then_replay():
    """MOP is expanded before REPLAY: a MOP emitting a REPLAY is further expanded."""
    t = _make_t()
    sems = t.semaphores
    sems.init(0, 0, 15)

    # Fill replay buffer slot 0 with SEMPOST
    sempost = int(TT_SEMPOST(sem_sel=0x01))
    t.threads[0].replay.buffer[0] = sempost

    from dsl import TT_REPLAY
    replay_insn = int(TT_REPLAY(start_idx=0, len=1,
                                execute_while_loading=0, load_mode=0))

    # Configure MOP Template 1: outer=1, inner=1, LoopOp=REPLAY(0,1)
    t.write_mop_cfg(0, 0, 1)             # OuterCount=1
    t.write_mop_cfg(0, 1, 1)             # InnerCount=1
    t.write_mop_cfg(0, 2, NOP_WORD)
    t.write_mop_cfg(0, 3, NOP_WORD)
    t.write_mop_cfg(0, 4, NOP_WORD)
    t.write_mop_cfg(0, 5, replay_insn)   # LoopOp = REPLAY
    t.write_mop_cfg(0, 6, NOP_WORD)
    t.write_mop_cfg(0, 7, replay_insn)   # Loop0Last = REPLAY
    t.write_mop_cfg(0, 8, replay_insn)

    t.push_instruction(0, int(TT_MOP(1, 0, 0)))
    for _ in range(20):
        t.step()
    # REPLAY(0,1) expands to SEMPOST → sem[0] gets posted
    assert sems.value[0] >= 1


# ===========================================================================
# Dispatch: NOP, STALLWAIT, SEMWAIT, MUTEX
# ===========================================================================

@spec("TCP.DISPATCH.NOP_PASSTHROUGH")
def test_nop_dispatched_without_side_effects():
    """NOP is consumed on step() without any observable side effect."""
    t = _make_t()
    t.push_instruction(0, NOP_WORD)
    t.step()
    assert t.threads[0].fifo.empty
    # No semaphore changes, no mutex changes
    for v in t.semaphores.value:
        assert v == 0


@spec("TCP.DISPATCH.STALLWAIT_INSTALLS_GATE")
def test_stallwait_dispatch_installs_wait_gate():
    """STALLWAIT dispatched via coprocessor step installs the Wait Gate latch."""
    t = _make_t()
    from emu.tensix import STALL_MATH, COND_SRCA_VLD
    word = int(TT_STALLWAIT(stall_res=STALL_MATH, wait_res=COND_SRCA_VLD))
    t.push_instruction(0, word)
    t.step()
    assert t.threads[0].wait_gate.opcode == "STALLWAIT"
    assert t.threads[0].wait_gate.block_mask == STALL_MATH
    assert t.threads[0].wait_gate.cond_mask == COND_SRCA_VLD


@spec("TCP.DISPATCH.SEMWAIT_INSTALLS_GATE")
def test_semwait_dispatch_installs_semwait_gate():
    """SEMWAIT dispatched via coprocessor step installs the SEMWAIT gate."""
    t = _make_t()
    from emu.tensix import STALL_MATH
    word = int(TT_SEMWAIT(stall_res=STALL_MATH, sem_sel=0x02, wait_sem_cond=0x01))
    t.push_instruction(0, word)
    t.step()
    assert t.threads[0].wait_gate.opcode == "SEMWAIT"
    assert t.threads[0].wait_gate.sem_mask == 0x02
    assert t.threads[0].wait_gate.sem_cond == 0x01


@spec("TCP.DISPATCH.MUTEX_ACQUIRE")
def test_mutex_acquire_and_contention():
    """ATGETM: T0 acquires mutex; T1 is blocked (instruction replayed)."""
    t = _make_t()
    atgetm = (0xA0 << 24) | 0   # mutex index 0
    t.push_instruction(0, atgetm)
    t.step()
    assert t.mutexes[0] == 0  # T0 holds mutex

    t.push_instruction(1, atgetm)
    t.step()
    assert t.mutexes[0] == 0         # T1 blocked, T0 still holds
    assert t.threads[1]._replay_word == atgetm


@spec("TCP.DISPATCH.MUTEX_RELEASE")
def test_mutex_release():
    """ATRELM: T0 releases mutex."""
    t = _make_t()
    atgetm = (0xA0 << 24) | 0
    atrelm = (0xA1 << 24) | 0
    t.push_instruction(0, atgetm)
    t.step()
    assert t.mutexes[0] == 0

    t.push_instruction(0, atrelm)
    t.step()
    assert t.mutexes[0] is None


# ===========================================================================
# MOP config write
# ===========================================================================

@spec("TCP.DISPATCH.MOP_CFG_WRITE")
def test_mop_cfg_write_stores_to_correct_thread():
    """MMIO write to MOP_CFG_BASE sets cfg[i] on the correct thread."""
    t = _make_t()
    for i in range(9):
        t.write_mop_cfg(1, i, 0x200 + i)
    for i in range(9):
        assert t.threads[1].mop.cfg[i] == 0x200 + i
    # Other threads unaffected
    for i in range(9):
        assert t.threads[0].mop.cfg[i] == 0
        assert t.threads[2].mop.cfg[i] == 0


@spec("TCP.DISPATCH.MOP_CFG_WRITE")
def test_mop_handler_none_for_brisc_ncrisc():
    """BRISC and NCRISC have no MOP config handler."""
    t = _make_t()
    assert t.mop_handler_for('brisc') is None
    assert t.mop_handler_for('ncrisc') is None


# ===========================================================================
# Semaphores
# ===========================================================================

@spec("TCP.SEMAPHORE.8_PER_TILE")
def test_semaphore_count():
    """8 hardware semaphores per tile."""
    t = _make_t()
    assert len(t.semaphores.value) == 8
    assert len(t.semaphores.max) == 8


@spec("TCP.SEMAPHORE.BRISC_INIT")
def test_seminit_through_pipeline():
    """SEMINIT dispatched through T0 FIFO initializes the semaphore."""
    t = _make_t()
    word = int(TT_SEMINIT(max_value=3, init_value=2, sem_sel=0x04))  # sem[2]
    t.push_instruction(0, word)
    t.step()
    assert t.semaphores.value[2] == 2
    assert t.semaphores.max[2] == 3


# ===========================================================================
# Address map
# ===========================================================================

@spec("TCP.ADDRMAP.INSTRN_BUF")
def test_instrn_buf_address_map():
    """T0=0xFFE40000, T1=0xFFE50000, T2=0xFFE60000; stride=0x10000."""
    from emu.memory import INSTRN_BUF_T0, INSTRN_BUF_T1, INSTRN_BUF_T2, INSTRN_BUF_STRIDE
    assert INSTRN_BUF_T0 == 0xFFE40000
    assert INSTRN_BUF_T1 == 0xFFE50000
    assert INSTRN_BUF_T2 == 0xFFE60000
    assert INSTRN_BUF_STRIDE == 0x10000


@spec("TCP.ADDRMAP.MOP_CFG_BASE")
def test_mop_cfg_base_address():
    """MOP_CFG_BASE is at 0xFFB80000."""
    assert MOP_CFG_BASE == 0xFFB80000


# ===========================================================================
# Full integration: MOP expansion through coprocessor
# ===========================================================================

@spec("TCP.PIPELINE.FIFO_MOP_REPLAY_WAIT", "TCP.THREADS.INDEPENDENT_STEP")
def test_mop_expansion_full_pipeline():
    """MOP instruction in T0 FIFO expands and dispatches SEMPOSTs end-to-end."""
    t = _make_t()
    sems = t.semaphores
    sems.init(1, 0, 15)

    sempost = int(TT_SEMPOST(sem_sel=0x02))
    t.write_mop_cfg(0, 0, 1)
    t.write_mop_cfg(0, 1, 3)
    t.write_mop_cfg(0, 2, NOP_WORD)
    t.write_mop_cfg(0, 3, NOP_WORD)
    t.write_mop_cfg(0, 4, NOP_WORD)
    t.write_mop_cfg(0, 5, sempost)
    t.write_mop_cfg(0, 6, NOP_WORD)
    t.write_mop_cfg(0, 7, sempost)
    t.write_mop_cfg(0, 8, sempost)

    t.push_instruction(0, int(TT_MOP(1, 0, 0)))
    for _ in range(20):
        t.step()

    assert sems.value[1] == 3
