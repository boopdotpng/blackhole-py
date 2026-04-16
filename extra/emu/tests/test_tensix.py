import pytest
from ..tensix.frontend import (
  InstructionFIFO, MOPExpander, ReplayExpander, WaitGate, TensixThread,
  STALL_MATH, STALL_CFG, STALL_SYNC, STALL_SFPU,
  COND_SRCA_VLD, COND_SRCB_VLD, COND_SRCA_CLR,
)
from ..tensix.sync import SyncUnit
from ..tensix.config import GPRFile, ConfigUnit, ScalarUnit
from ..tensix.regfile import SrcRegFile, DestRegFile
from ..tensix import TensixCoprocessor, HardwareState
from ..memory import Semaphores
from ..dsl import (
  decode_tensix,
  TT_NOP, TT_MOP, TT_REPLAY, TT_SEMINIT, TT_SEMPOST, TT_SEMGET,
  TT_STALLWAIT, TT_SEMWAIT, TT_SETC16, TT_WRCFG, TT_RDCFG,
  TT_SETDMAREG, TT_ADDDMAREG, TT_DMANOP, TT_MVMUL, TT_ZEROACC,
  TT_RMWCIB0, TT_RMWCIB1,
)


# ============================================================================
# Instruction FIFO
# ============================================================================

class TestInstructionFIFO:
  def test_push_pop(self):
    fifo = InstructionFIFO()
    assert fifo.empty
    assert fifo.push(0xDEADBEEF)
    assert not fifo.empty
    assert fifo.pop() == 0xDEADBEEF
    assert fifo.empty

  def test_ordering(self):
    fifo = InstructionFIFO()
    for i in range(5):
      fifo.push(i)
    for i in range(5):
      assert fifo.pop() == i

  def test_capacity_32(self):
    fifo = InstructionFIFO()
    for i in range(32):
      assert fifo.push(i)
    assert fifo.full
    assert not fifo.push(99)  # rejected
    assert fifo.pop() == 0    # drain one
    assert fifo.push(99)      # now room

  def test_pop_empty(self):
    fifo = InstructionFIFO()
    assert fifo.pop() is None


# ============================================================================
# MOP Expander
# ============================================================================

class TestMOPExpander:
  def test_passthrough(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    nop = int(TT_NOP())
    fifo.push(nop)
    assert mop.next(fifo) == nop

  def test_mop_cfg_consumed(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    # MOP_CFG opcode = 0x03, sets mask_hi
    mop_cfg_word = (0x03 << 24) | 0xABCD
    fifo.push(mop_cfg_word)
    assert mop.next(fifo) is None  # consumed
    assert mop.mask_hi == 0xABCD

  def test_template1_simple(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    nop = int(TT_NOP())
    loop0_last = 0x11111111
    loop1_last = 0x22222222

    mop.cfg[0] = 1             # OuterCount = 1
    mop.cfg[1] = 2             # InnerCount = 2
    mop.cfg[2] = nop           # StartOp = NOP (skipped)
    mop.cfg[3] = nop           # EndOp0 = NOP (skipped)
    mop.cfg[4] = nop           # EndOp1 = NOP (skipped)
    mop.cfg[5] = 0xAAAAAAAA    # LoopOp
    mop.cfg[6] = nop           # LoopOp1 = NOP (no alternation)
    mop.cfg[7] = loop0_last    # Loop0Last
    mop.cfg[8] = loop1_last    # Loop1Last

    # Issue MOP(Template=1, Count1=0, MaskLo=0)
    mop_word = int(TT_MOP(1, 0, 0))
    fifo.push(mop_word)

    # Outer=1, Inner=2:
    #   i=0: not last inner → emit LoopOp
    #   i=1: last inner AND last outer → emit Loop0Last
    results = []
    for _ in range(10):
      r = mop.next(fifo)
      if r is not None:
        results.append(r)
    assert results == [0xAAAAAAAA, loop0_last]

  def test_template1_with_startop_endop(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    nop = int(TT_NOP())

    mop.cfg[0] = 2             # OuterCount = 2
    mop.cfg[1] = 1             # InnerCount = 1
    mop.cfg[2] = 0x11000000    # StartOp (non-NOP)
    mop.cfg[3] = 0x22000000    # EndOp0 (non-NOP)
    mop.cfg[4] = nop           # EndOp1 = NOP (skipped)
    mop.cfg[5] = 0x33000000    # LoopOp
    mop.cfg[6] = nop           # LoopOp1 = NOP
    mop.cfg[7] = 0x44000000    # Loop0Last
    mop.cfg[8] = 0x55000000    # Loop1Last

    fifo.push(int(TT_MOP(1, 0, 0)))

    results = []
    for _ in range(20):
      r = mop.next(fifo)
      if r is not None:
        results.append(r)

    # Outer=2, Inner=1:
    # j=0: StartOp, i=0 (last inner, not last outer) → Loop1Last, EndOp0
    # j=1: StartOp, i=0 (last inner, last outer) → Loop0Last, EndOp0
    assert results == [
      0x11000000,  # StartOp
      0x55000000,  # Loop1Last (j=0, i=0: last inner, not last outer)
      0x22000000,  # EndOp0
      0x11000000,  # StartOp
      0x44000000,  # Loop0Last (j=1, i=0: last inner, last outer)
      0x22000000,  # EndOp0
    ]

  def test_template1_hw_bug(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    nop = int(TT_NOP())

    mop.cfg[0] = 1             # OuterCount = 1
    mop.cfg[1] = 0             # InnerCount = 0
    mop.cfg[2] = nop           # StartOp = NOP (trigger condition)
    mop.cfg[3] = 0xBB000000    # EndOp0 = non-NOP (trigger condition)
    mop.cfg[4] = nop           # EndOp1
    mop.cfg[5] = 0xCC000000    # LoopOp
    mop.cfg[6] = nop           # LoopOp1
    mop.cfg[7] = 0xDD000000    # Loop0Last
    mop.cfg[8] = 0xEE000000    # Loop1Last

    fifo.push(int(TT_MOP(1, 0, 0)))

    results = []
    for _ in range(300):
      r = mop.next(fifo)
      if r is not None:
        results.append(r)

    # OuterCount becomes 1+128=129, InnerCount=0
    # Each outer iteration: no inner loop, just EndOp0
    # 129 iterations of EndOp0
    assert len(results) == 129
    assert all(r == 0xBB000000 for r in results)

  def test_template1_alternating_loop_ops(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    nop = int(TT_NOP())

    mop.cfg[0] = 1             # OuterCount = 1
    mop.cfg[1] = 2             # InnerCount = 2 (doubles to 4)
    mop.cfg[2] = nop           # StartOp
    mop.cfg[3] = nop           # EndOp0
    mop.cfg[4] = nop           # EndOp1
    mop.cfg[5] = 0xAA000000    # LoopOp
    mop.cfg[6] = 0xBB000000    # LoopOp1 (non-NOP → alternation enabled)
    mop.cfg[7] = 0xCC000000    # Loop0Last
    mop.cfg[8] = 0xDD000000    # Loop1Last

    fifo.push(int(TT_MOP(1, 0, 0)))

    results = []
    for _ in range(10):
      r = mop.next(fifo)
      if r is not None:
        results.append(r)

    # InnerCount doubles to 4. Alternates LoopOp/LoopOp1:
    # i=0: not last → LoopOp=0xAA
    # i=1: not last → LoopOp1=0xBB (after XOR flip)
    # i=2: not last → LoopOp=0xAA (after XOR flip back)
    # i=3: last inner, last outer → Loop0Last=0xCC
    assert results == [0xAA000000, 0xBB000000, 0xAA000000, 0xCC000000]


# ============================================================================
# Replay Expander
# ============================================================================

class TestReplayExpander:
  def test_passthrough(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()
    nop = int(TT_NOP())
    fifo.push(nop)
    assert replay.next(mop, fifo) == nop

  def test_record_and_playback(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()

    # Record 3 instructions starting at slot 0
    record_word = int(TT_REPLAY(start_idx=0, len=3, execute_while_loading=0, load_mode=1))
    fifo.push(record_word)
    fifo.push(0x11111111)
    fifo.push(0x22222222)
    fifo.push(0x33333333)

    # Consume the REPLAY (record mode) + 3 instructions
    results = []
    for _ in range(10):
      r = replay.next(mop, fifo)
      if r is not None:
        results.append(r)
    # Record without execute → no output
    assert results == []

    # Now playback from slot 0, length 3
    play_word = int(TT_REPLAY(start_idx=0, len=3, execute_while_loading=0, load_mode=0))
    fifo.push(play_word)

    results = []
    for _ in range(10):
      r = replay.next(mop, fifo)
      if r is not None:
        results.append(r)
    assert results == [0x11111111, 0x22222222, 0x33333333]

  def test_record_with_execute(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()

    # Record 2 instructions with execute_while_loading=1
    record_word = int(TT_REPLAY(start_idx=0, len=2, execute_while_loading=1, load_mode=1))
    fifo.push(record_word)
    fifo.push(0xAAAAAAAA)
    fifo.push(0xBBBBBBBB)

    results = []
    for _ in range(10):
      r = replay.next(mop, fifo)
      if r is not None:
        results.append(r)
    # Both emitted during recording
    assert results == [0xAAAAAAAA, 0xBBBBBBBB]

  def test_buffer_wraps_mod32(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()

    # Record at slot 31, length 2 → wraps to slot 0
    record_word = int(TT_REPLAY(start_idx=31, len=2, execute_while_loading=0, load_mode=1))
    fifo.push(record_word)
    fifo.push(0x11111111)  # slot 31
    fifo.push(0x22222222)  # slot 0 (wraps)

    for _ in range(10):
      replay.next(mop, fifo)

    # Playback
    play_word = int(TT_REPLAY(start_idx=31, len=2, execute_while_loading=0, load_mode=0))
    fifo.push(play_word)

    results = []
    for _ in range(10):
      r = replay.next(mop, fifo)
      if r is not None:
        results.append(r)
    assert results == [0x11111111, 0x22222222]

  def test_count_zero_means_64(self):
    fifo = InstructionFIFO()
    mop = MOPExpander()
    replay = ReplayExpander()

    # Pre-fill buffer with known values
    for i in range(32):
      replay.buffer[i] = 0x100 + i

    # Playback with len=0 → 64 instructions (wraps buffer twice)
    play_word = int(TT_REPLAY(start_idx=0, len=0, execute_while_loading=0, load_mode=0))
    fifo.push(play_word)

    results = []
    for _ in range(70):
      r = replay.next(mop, fifo)
      if r is not None:
        results.append(r)
    assert len(results) == 64
    # First 32 = buffer[0..31], next 32 = buffer[0..31] again
    for i in range(32):
      assert results[i] == 0x100 + i
      assert results[32 + i] == 0x100 + i


# ============================================================================
# Wait Gate
# ============================================================================

class TestWaitGate:
  def _make_hw_state(self, srca_fpu_owner="matrix_unit", srcb_fpu_owner="matrix_unit",
             srca_unp_owner="unpackers", srcb_unp_owner="unpackers"):
    sems = Semaphores()
    srca = SrcRegFile("SrcA")
    srcb = SrcRegFile("SrcB")
    # Separate fpu_bank and unpack_bank so owners don't alias
    # (both default to 0; after the first double-buffer flip they differ)
    srca.fpu_bank = 0; srca.unpack_bank = 1
    srcb.fpu_bank = 0; srcb.unpack_bank = 1
    srca.banks[0].allowed_client = srca_fpu_owner
    srca.banks[1].allowed_client = srca_unp_owner
    srcb.banks[0].allowed_client = srcb_fpu_owner
    srcb.banks[1].allowed_client = srcb_unp_owner
    return HardwareState(sems, srca, srcb)

  def test_no_wait_passes(self):
    wg = WaitGate()
    hw = self._make_hw_state()
    nop = int(TT_NOP())
    assert not wg.is_blocking(nop, hw, 0)

  def test_stallwait_one_cycle_hold(self):
    wg = WaitGate()
    # STALL_MATH, wait for SRCA_VLD (C7) — but SrcA is already owned by matrix_unit
    wg.install_stallwait(STALL_MATH, COND_SRCA_VLD)
    hw = self._make_hw_state(srca_fpu_owner="matrix_unit")
    mvmul = int(TT_MVMUL(0, 0, 0, 0))
    # First check: always held (one-cycle minimum)
    assert wg.is_blocking(mvmul, hw, 0)
    # Second check: condition is met, should release
    assert not wg.is_blocking(mvmul, hw, 0)

  def test_stallwait_blocks_until_condition_met(self):
    wg = WaitGate()
    wg.install_stallwait(STALL_MATH, COND_SRCA_VLD)
    # SrcA FPU bank NOT owned by matrix_unit → condition active
    hw = self._make_hw_state(srca_fpu_owner="unpackers")
    mvmul = int(TT_MVMUL(0, 0, 0, 0))
    assert wg.is_blocking(mvmul, hw, 0)  # one-cycle hold
    assert wg.is_blocking(mvmul, hw, 0)  # still waiting (condition not met)
    # Now change ownership
    hw2 = self._make_hw_state(srca_fpu_owner="matrix_unit")
    assert not wg.is_blocking(mvmul, hw2, 0)  # released

  def test_stallwait_default_substitution(self):
    wg = WaitGate()
    wg.install_stallwait(0, 0)
    assert wg.block_mask == STALL_MATH
    assert wg.cond_mask == 0x0F

  def test_semwait_stall_on_zero(self):
    sems = Semaphores()
    sems.init(1, 0, 2)  # sem[1]: value=0, max=2
    srca = SrcRegFile("SrcA")
    srcb = SrcRegFile("SrcB")
    hw = HardwareState(sems, srca, srcb)

    wg = WaitGate()
    # Wait on sem[1], STALL_ON_ZERO
    wg.install_semwait(STALL_MATH, 0x02, 0x01)  # sem_sel=bit1, cond=C0
    mvmul = int(TT_MVMUL(0, 0, 0, 0))
    assert wg.is_blocking(mvmul, hw, 0)  # one-cycle hold
    assert wg.is_blocking(mvmul, hw, 0)  # value==0, still waiting

    sems.post(1)  # value → 1
    assert not wg.is_blocking(mvmul, hw, 0)  # released

  def test_semwait_stall_on_max(self):
    sems = Semaphores()
    sems.init(1, 2, 2)  # sem[1]: value=2, max=2
    srca = SrcRegFile("SrcA")
    srcb = SrcRegFile("SrcB")
    hw = HardwareState(sems, srca, srcb)

    wg = WaitGate()
    wg.install_semwait(STALL_MATH, 0x02, 0x02)  # sem_sel=bit1, cond=C1
    mvmul = int(TT_MVMUL(0, 0, 0, 0))
    assert wg.is_blocking(mvmul, hw, 0)  # one-cycle hold
    assert wg.is_blocking(mvmul, hw, 0)  # value>=max, still waiting

    sems.get(1)  # value → 1
    assert not wg.is_blocking(mvmul, hw, 0)  # released

  def test_unblocked_category_passes(self):
    wg = WaitGate()
    # Block only MATH, wait on SRCA_VLD (condition will never be met)
    wg.install_stallwait(STALL_MATH, COND_SRCA_VLD)
    hw = self._make_hw_state(srca_fpu_owner="unpackers")
    wg.is_blocking(0, hw, 0)  # consume one-cycle hold

    # A config instruction (STALL_CFG) is not blocked by STALL_MATH
    setc16 = int(TT_SETC16(0, 0))
    assert not wg.is_blocking(setc16, hw, 0)

    # But a math instruction IS blocked
    mvmul = int(TT_MVMUL(0, 0, 0, 0))
    assert wg.is_blocking(mvmul, hw, 0)


# ============================================================================
# Sync Unit
# ============================================================================

class TestSyncUnit:
  def test_seminit(self):
    sems = Semaphores()
    sync = SyncUnit(sems)
    # SEMINIT: max=2, init=0, sem_sel=bit1 (semaphore 1)
    word = int(TT_SEMINIT(max_value=2, init_value=0, sem_sel=0x02))
    sync.execute_seminit(decode_tensix(word))
    assert sems.value[1] == 0
    assert sems.max[1] == 2

  def test_sempost_semget(self):
    sems = Semaphores()
    sync = SyncUnit(sems)
    sems.init(1, 0, 3)

    sync.execute_sempost(decode_tensix(int(TT_SEMPOST(sem_sel=0x02))))  # post sem[1]
    assert sems.value[1] == 1
    sync.execute_sempost(decode_tensix(int(TT_SEMPOST(sem_sel=0x02))))
    assert sems.value[1] == 2
    sync.execute_sempost(decode_tensix(int(TT_SEMPOST(sem_sel=0x02))))
    assert sems.value[1] == 3
    sync.execute_sempost(decode_tensix(int(TT_SEMPOST(sem_sel=0x02))))
    assert sems.value[1] == 3  # capped at max

    sync.execute_semget(decode_tensix(int(TT_SEMGET(sem_sel=0x02))))
    assert sems.value[1] == 2
    sync.execute_semget(decode_tensix(int(TT_SEMGET(sem_sel=0x02))))
    sync.execute_semget(decode_tensix(int(TT_SEMGET(sem_sel=0x02))))
    assert sems.value[1] == 0
    sync.execute_semget(decode_tensix(int(TT_SEMGET(sem_sel=0x02))))
    assert sems.value[1] == 0  # floored at 0

  def test_multiple_semaphores(self):
    sems = Semaphores()
    sync = SyncUnit(sems)
    # Init sem[0] and sem[2] simultaneously
    word = int(TT_SEMINIT(max_value=5, init_value=3, sem_sel=0x05))  # bits 0 and 2
    sync.execute_seminit(decode_tensix(word))
    assert sems.value[0] == 3
    assert sems.max[0] == 5
    assert sems.value[2] == 3
    assert sems.max[2] == 5
    assert sems.value[1] == 0  # untouched


# ============================================================================
# GPR File
# ============================================================================

class TestGPRFile:
  def test_read_write_32(self):
    gpr = GPRFile()
    gpr.write32(0, 5, 0xDEADBEEF)
    assert gpr.read32(0, 5) == 0xDEADBEEF
    assert gpr.read32(1, 5) == 0  # different thread

  def test_read_write_16_halves(self):
    gpr = GPRFile()
    gpr.write32(0, 0, 0)
    # Write low half (reg_index_16b = reg<<1 | 0)
    gpr.write16(0, 0 << 1 | 0, 0x1234)  # reg 0, low half
    assert gpr.read32(0, 0) == 0x00001234
    # Write high half (reg_index_16b = reg<<1 | 1)
    gpr.write16(0, 0 << 1 | 1, 0xABCD)  # reg 0, high half
    assert gpr.read32(0, 0) == 0xABCD1234
    # Read back halves
    assert gpr.read16(0, 0 << 1 | 0) == 0x1234
    assert gpr.read16(0, 0 << 1 | 1) == 0xABCD


# ============================================================================
# Config Unit
# ============================================================================

class TestConfigUnit:
  def test_setc16(self):
    gpr = GPRFile()
    cu = ConfigUnit(gpr)
    word = int(TT_SETC16(setc16_reg=12, setc16_value=0x1234))
    cu.execute_setc16(decode_tensix(word), thread_id=1)
    assert cu.thread_cfg[1][12] == 0x1234

  def test_wrcfg_rdcfg_roundtrip(self):
    gpr = GPRFile()
    cu = ConfigUnit(gpr)
    # Write a value to GPR
    gpr.write32(0, 10, 0xCAFEBABE)
    # WRCFG: GprAddress=10, wr128b=0, CfgReg=(addr32=50)<<2 = 200
    word = int(TT_WRCFG(GprAddress=10, wr128b=0, CfgReg=50 << 2))
    cu.execute_wrcfg(decode_tensix(word), thread_id=0)
    assert cu.cfg[0][50] == 0xCAFEBABE

    # RDCFG: read it back into GPR 20
    word = int(TT_RDCFG(GprAddress=20, CfgReg=50 << 2))
    cu.execute_rdcfg(decode_tensix(word), thread_id=0)
    assert gpr.read32(0, 20) == 0xCAFEBABE

  def test_rmwcib0(self):
    gpr = GPRFile()
    cu = ConfigUnit(gpr)
    cu.cfg[0][42] = 0xFF00FF00
    # RMWCIB0: modify byte 0 — mask=0x0F, data=0xAB, addr32=42
    word = int(TT_RMWCIB0(Mask=0x0F, Data=0xAB, CfgRegAddr=42))
    cu.execute_rmwcib(decode_tensix(word), byte_index=0)
    # Byte 0: old=0x00, mask=0x0F → bits 3:0 become 0xB
    assert cu.cfg[0][42] == 0xFF00FF0B

  def test_rmwcib1(self):
    gpr = GPRFile()
    cu = ConfigUnit(gpr)
    cu.cfg[0][10] = 0x00FF0000
    # RMWCIB1: modify byte 1 — mask=0xFF, data=0x42, addr32=10
    word = int(TT_RMWCIB1(Mask=0xFF, Data=0x42, CfgRegAddr=10))
    cu.execute_rmwcib(decode_tensix(word), byte_index=1)
    assert cu.cfg[0][10] == 0x00FF4200


# ============================================================================
# Scalar Unit
# ============================================================================

class TestScalarUnit:
  def test_setdmareg(self):
    gpr = GPRFile()
    su = ScalarUnit(gpr)
    # Write 0x1234 to reg 5, low half: RegIndex16b = 5<<1|0 = 10
    word = int(TT_SETDMAREG(Payload_SigSelSize=0, Payload_SigSel=0x1234,
                 SetSignalsMode=0, RegIndex16b=10))
    su.execute_setdmareg(decode_tensix(word), thread_id=0)
    assert gpr.read16(0, 10) == 0x1234

  def test_setdmareg_high_half(self):
    gpr = GPRFile()
    su = ScalarUnit(gpr)
    gpr.write32(0, 5, 0)
    # Write 0xABCD to reg 5, high half: RegIndex16b = 5<<1|1 = 11
    # 16-bit immediate spans bits [23:8]: SigSelSize (2 bits) | SigSel (14 bits)
    # 0xABCD = (0b10 << 14) | 0x2BCD
    word = int(TT_SETDMAREG(Payload_SigSelSize=0xABCD >> 14, Payload_SigSel=0xABCD & 0x3FFF,
                 SetSignalsMode=0, RegIndex16b=11))
    su.execute_setdmareg(decode_tensix(word), thread_id=0)
    assert gpr.read32(0, 5) == 0xABCD0000

  def test_adddmareg(self):
    gpr = GPRFile()
    su = ScalarUnit(gpr)
    gpr.write32(0, 1, 100)
    gpr.write32(0, 2, 200)
    # Result[3] = OpA[1] + OpB[2]
    word = int(TT_ADDDMAREG(OpBisConst=0, ResultRegIndex=3,
                 OpBRegIndex=2, OpARegIndex=1))
    su.execute_adddmareg(decode_tensix(word), thread_id=0)
    assert gpr.read32(0, 3) == 300

  def test_adddmareg_const(self):
    gpr = GPRFile()
    su = ScalarUnit(gpr)
    gpr.write32(0, 1, 100)
    # Result[3] = OpA[1] + 7 (const)
    word = int(TT_ADDDMAREG(OpBisConst=1, ResultRegIndex=3,
                 OpBRegIndex=7, OpARegIndex=1))
    su.execute_adddmareg(decode_tensix(word), thread_id=0)
    assert gpr.read32(0, 3) == 107


# ============================================================================
# Register Files
# ============================================================================

class TestRegFiles:
  def test_src_bank_ownership(self):
    src = SrcRegFile("SrcA")
    assert src.banks[0].allowed_client == "unpackers"
    assert src.banks[1].allowed_client == "unpackers"
    src.flip_to_fpu()
    assert src.banks[0].allowed_client == "matrix_unit"
    assert src.unpack_bank == 1
    src.release_from_fpu()
    assert src.banks[0].allowed_client == "unpackers"
    assert src.fpu_bank == 1

  def test_dest_clear_all(self):
    dest = DestRegFile()
    dest.valid[0] = True
    dest.valid[512] = True
    dest.clear_all()
    assert not any(dest.valid)

  def test_dest_clear_half(self):
    dest = DestRegFile()
    for i in range(1024):
      dest.valid[i] = True
    dest.clear_half(0)  # clear rows 0-511
    assert not dest.valid[0]
    assert not dest.valid[511]
    assert dest.valid[512]
    assert dest.valid[1023]


# ============================================================================
# Full Coprocessor Integration
# ============================================================================

class TestTensixCoprocessor:
  def test_push_and_step_nop(self):
    t = TensixCoprocessor()
    sems = t.semaphores
    nop = int(TT_NOP())
    assert t.push_instruction(0, nop)
    t.step()
    assert t.threads[0].fifo.empty

  def test_seminit_through_pipeline(self):
    t = TensixCoprocessor()
    sems = t.semaphores
    word = int(TT_SEMINIT(max_value=2, init_value=1, sem_sel=0x02))
    t.push_instruction(0, word)
    t.step()
    assert sems.value[1] == 1
    assert sems.max[1] == 2

  def test_mutex_acquire_release(self):
    t = TensixCoprocessor()
    sems = t.semaphores
    # T0 acquires mutex 0
    atgetm = (0xA0 << 24) | 0
    t.push_instruction(0, atgetm)
    t.step()
    assert t.mutexes[0] == 0  # owned by thread 0

    # T1 tries to acquire same mutex — blocked
    t.push_instruction(1, atgetm)
    t.step()
    assert t.mutexes[0] == 0  # still owned by T0
    # T1's FIFO should have the instruction back for retry
    assert t.threads[1]._replay_word == atgetm

    # T0 releases — T1's replayed ATGETM immediately acquires in the same step
    # (step() processes threads in order: T0 releases, then T1 retries and succeeds)
    atrelm = (0xA1 << 24) | 0
    t.push_instruction(0, atrelm)
    t.step()
    assert t.mutexes[0] == 1  # T1 acquired

  def test_mop_config_write(self):
    t = TensixCoprocessor()
    sems = t.semaphores
    t.write_mop_cfg(1, 5, 0x12345678)
    assert t.threads[1].mop.cfg[5] == 0x12345678

  def test_setc16_through_pipeline(self):
    t = TensixCoprocessor()
    sems = t.semaphores
    word = int(TT_SETC16(setc16_reg=12, setc16_value=0x4321))
    t.push_instruction(1, word)
    t.step()
    assert t.config_unit.thread_cfg[1][12] == 0x4321

  def test_setdmareg_through_pipeline(self):
    t = TensixCoprocessor()
    sems = t.semaphores
    # 16-bit immediate spans bits [23:8]: SigSelSize (2 bits) | SigSel (14 bits)
    # 0x5678 = (0b01 << 14) | 0x1678
    word = int(TT_SETDMAREG(Payload_SigSelSize=0x5678 >> 14, Payload_SigSel=0x5678 & 0x3FFF,
                 SetSignalsMode=0, RegIndex16b=4))
    t.push_instruction(2, word)
    t.step()
    assert t.gpr.read16(2, 4) == 0x5678

  def test_mop_expansion_through_pipeline(self):
    t = TensixCoprocessor()
    sems = t.semaphores
    sems.init(1, 0, 15)

    # Configure MOP Template 1: outer=1, inner=3
    t.write_mop_cfg(0, 0, 1)   # OuterCount=1
    t.write_mop_cfg(0, 1, 3)   # InnerCount=3
    nop = int(TT_NOP())
    t.write_mop_cfg(0, 2, nop)  # StartOp=NOP
    t.write_mop_cfg(0, 3, nop)  # EndOp0=NOP
    t.write_mop_cfg(0, 4, nop)  # EndOp1=NOP
    # LoopOp = SEMPOST sem[1]
    sempost = int(TT_SEMPOST(sem_sel=0x02))
    t.write_mop_cfg(0, 5, sempost)  # LoopOp
    t.write_mop_cfg(0, 6, nop)     # LoopOp1=NOP
    t.write_mop_cfg(0, 7, sempost)  # Loop0Last = also SEMPOST
    t.write_mop_cfg(0, 8, sempost)  # Loop1Last

    # Push MOP
    mop = int(TT_MOP(mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0))
    t.push_instruction(0, mop)

    # Step enough times for expansion + dispatch
    for _ in range(20):
      t.step()

    # 3 inner iterations → 3 SEMPOSTs → sem[1] = 3
    assert sems.value[1] == 3
