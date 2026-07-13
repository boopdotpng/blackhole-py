from asm import KernelBuilder
from isa import R
from cq import DISPATCH_DONE_COUNT
from fw.consts import BriscLocalState, CQ, Firmware, FirmwareControl, RunMsg, RunSync, TensixL1, TensixMMIO
from ttk.noc import NOC_CFG_BASE, NOC_INSTANCE_OFFSET_BIT, NocCfg
from ttk.tensix import Tensix

def _enable_clock_gating(fw):
  for noc in range(2):
    for register in (NocCfg.NIU_CFG_0, NocCfg.ROUTER_CFG_0):
      addr = NOC_CFG_BASE + (noc << NOC_INSTANCE_OFFSET_BIT) + register * 4
      fw.update32(addr, set_bits=1)
  return fw

def _notify_dispatch(fw):
  with fw.scope():
    local, tmp = fw.reg(2)
    fw.load(local, BriscLocalState.MY_X + 1, bytes=1)
    fw.load(tmp, BriscLocalState.MY_Y + 1, bytes=1)
    fw.slli(tmp, tmp, 6); fw.or_(local, local, tmp)
    noc = fw.noc(1).initialize(local)
    with fw.scope():
      with noc.atomic_batch(count=1) as atomics:
        atomics.issue(DISPATCH_DONE_COUNT, CQ.DISPATCH_COORD)
  return fw

def build():
  fw = KernelBuilder.standalone("brisc")
  fw.configure_csr()
  fw.setup_stack(Firmware.BRISC_STACK_TOP)

  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.write32(TensixMMIO.RISCV_TDMA_REG_CLK_GATE_EN, 0x3F)
  _enable_clock_gating(fw)
  fw.zero_words(TensixL1.MEM_ZEROS_BASE, TensixL1.MEM_ZEROS_SIZE // 4)
  fw.invalidate_risc_caches()
  fw.jal(R.RA, "reset_tensix")
  for index in (0, 1):
    fw.noc(index).store_risc_coordinates(
      BriscLocalState.MY_X, BriscLocalState.MY_Y,
    )
  fw.write32(TensixMMIO.NCRISC_HALT_RESUME_ADDR, 0)
  fw.jal(R.RA, "init_nocs")
  fw.invalidate_risc_caches()

  fw.write32(FirmwareControl.SUBORDINATE_SYNC, RunSync.ALL_INIT)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, 0)
  for role in range(1, 5):
    fw.wait8(FirmwareControl.SUBORDINATE_SYNC + role - 1, RunSync.BOOT_READY)

  fw.signal8(FirmwareControl.GO_SIGNAL, RunMsg.DONE)
  fw.label("run_loop")
  fw.wait8(FirmwareControl.GO_SIGNAL, RunMsg.GO)
  fw.jal(R.RA, "reset_tensix")
  fw.jal(R.RA, "init_nocs")

  fw.invalidate_risc_caches()
  fw.signal_range(FirmwareControl.SUBORDINATE_SYNC, range(4), RunSync.GO)
  fw.call_fixed_kernel(TensixL1.WORKER_TEXT_BASE["brisc"])
  for role in range(1, 5):
    fw.wait8(FirmwareControl.SUBORDINATE_SYNC + role - 1, RunSync.DONE)
  fw.signal8(FirmwareControl.GO_SIGNAL, RunMsg.DONE)
  _notify_dispatch(fw)
  fw.j("run_loop")

  fw.label("reset_tensix")
  Tensix.reset_hardware(fw)
  fw.jalr(R.ZERO, R.RA)

  fw.label("init_nocs")
  for index in (0, 1):
    fw.noc(index).init_resident()
  fw.jalr(R.ZERO, R.RA)
  return fw
