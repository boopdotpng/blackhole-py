import pytest
from emu.tensix import (
  SyncUnit, GPRFile, ConfigUnit, ScalarUnit, TensixCoprocessor,
  Semaphores,
)
from dsl import (
  decode_tensix,
  TT_SEMINIT, TT_SEMPOST, TT_SEMGET,
  TT_SETC16, TT_WRCFG, TT_RDCFG,
  TT_SETDMAREG, TT_ADDDMAREG,
  TT_RMWCIB0, TT_RMWCIB1,
)


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
    post = decode_tensix(int(TT_SEMPOST(sem_sel=0x02)))
    get = decode_tensix(int(TT_SEMGET(sem_sel=0x02)))

    # Post past max → saturates at 3
    for _ in range(4):
      sync.execute_sempost(post)
    assert sems.value[1] == 3

    # Get past 0 → floors at 0
    for _ in range(4):
      sync.execute_semget(get)
    assert sems.value[1] == 0

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

  @pytest.mark.parametrize("insn,byte_index,addr,init,mask,data,expected", [
    (TT_RMWCIB0, 0, 42, 0xFF00FF00, 0x0F, 0xAB, 0xFF00FF0B),
    (TT_RMWCIB1, 1, 10, 0x00FF0000, 0xFF, 0x42, 0x00FF4200),
  ])
  def test_rmwcib(self, insn, byte_index, addr, init, mask, data, expected):
    gpr = GPRFile()
    cu = ConfigUnit(gpr)
    cu.cfg[0][addr] = init
    word = int(insn(Mask=mask, Data=data, CfgRegAddr=addr))
    cu.execute_rmwcib(decode_tensix(word), byte_index=byte_index)
    assert cu.cfg[0][addr] == expected


# ============================================================================
# Scalar Unit
# ============================================================================

class TestScalarUnit:
  # 16-bit immediate spans bits [23:8]: SigSelSize (2 bits) | SigSel (14 bits)
  @pytest.mark.parametrize("imm16,reg_idx_16b,check_reg,check_32", [
    (0x1234, 10, None, None),     # reg 5, low half → read16
    (0xABCD, 11, 5, 0xABCD0000),  # reg 5, high half → read32
  ])
  def test_setdmareg(self, imm16, reg_idx_16b, check_reg, check_32):
    gpr = GPRFile()
    su = ScalarUnit(gpr)
    word = int(TT_SETDMAREG(Payload_SigSelSize=imm16 >> 14,
                 Payload_SigSel=imm16 & 0x3FFF,
                 SetSignalsMode=0, RegIndex16b=reg_idx_16b))
    su.execute_setdmareg(decode_tensix(word), thread_id=0)
    if check_reg is None:
      assert gpr.read16(0, reg_idx_16b) == imm16
    else:
      assert gpr.read32(0, check_reg) == check_32

  @pytest.mark.parametrize("opb_is_const,opb,expected", [
    (0, 2, 300),  # OpA[1]=100 + OpB[2]=200
    (1, 7, 107),  # OpA[1]=100 + const 7
  ])
  def test_adddmareg(self, opb_is_const, opb, expected):
    gpr = GPRFile()
    su = ScalarUnit(gpr)
    gpr.write32(0, 1, 100)
    gpr.write32(0, 2, 200)
    word = int(TT_ADDDMAREG(OpBisConst=opb_is_const, ResultRegIndex=3,
                 OpBRegIndex=opb, OpARegIndex=1))
    su.execute_adddmareg(decode_tensix(word), thread_id=0)
    assert gpr.read32(0, 3) == expected


# ============================================================================
# Full Coprocessor Integration (config/scalar portions only)
# ============================================================================

class TestTensixCoprocessor:
  def test_setc16_through_pipeline(self):
    t = TensixCoprocessor()
    word = int(TT_SETC16(setc16_reg=12, setc16_value=0x4321))
    t.push_instruction(1, word)
    t.step()
    assert t.config_unit.thread_cfg[1][12] == 0x4321

  def test_setdmareg_through_pipeline(self):
    t = TensixCoprocessor()
    # 16-bit immediate spans bits [23:8]: SigSelSize (2 bits) | SigSel (14 bits)
    # 0x5678 = (0b01 << 14) | 0x1678
    word = int(TT_SETDMAREG(Payload_SigSelSize=0x5678 >> 14, Payload_SigSel=0x5678 & 0x3FFF,
                 SetSignalsMode=0, RegIndex16b=4))
    t.push_instruction(2, word)
    t.step()
    assert t.gpr.read16(2, 4) == 0x5678
