from asm import Asm
from isa import R
from cq import DISPATCH_DONE_COUNT
from fw.consts import CQConfig, Firmware, FirmwareControl, RunState, TensixL1, TensixMMIO
from ttk.noc import NOC_CFG_BASE, NOC_INSTANCE_OFFSET_BIT, NocCfg
from ttk.tensix import Tensix
from ttk.cb import CB

def _enable_clock_gating(fw):
  for noc in range(2):
    for register in (NocCfg.NIU_CFG_0, NocCfg.ROUTER_CFG_0):
      addr = NOC_CFG_BASE + (noc << NOC_INSTANCE_OFFSET_BIT) + register * 4
      fw.update32(addr, set_bits=1)
  return fw

def _notify_dispatch(fw):
  with fw.scope():
    x_addr, y_addr = Firmware.NOC_COORDINATE_BASE["brisc"]
    local, tmp = fw.reg(2)
    fw.load(local, x_addr + 1, bytes=1)
    fw.load(tmp, y_addr + 1, bytes=1)
    fw.slli(tmp, tmp, 6); fw.or_(local, local, tmp)
    noc = fw.noc(1).initialize(local)
    with noc.atomic_batch(count=1) as atomics:
      atomics.issue(DISPATCH_DONE_COUNT, CQConfig.DISPATCH_COORD)
  return fw

def build_brisc():
  fw = Asm.firmware("brisc")
  fw.configure_csr()
  fw.setup_stack(Firmware.BRISC_STACK_TOP)

  fw.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, Firmware.TEXT["ncrisc"][0])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, Firmware.TEXT["trisc0"][0])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, Firmware.TEXT["trisc1"][0])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, Firmware.TEXT["trisc2"][0])
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE, 0b111)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE, 1)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.write32(TensixMMIO.RISCV_TDMA_REG_CLK_GATE_EN, 0x3F)
  _enable_clock_gating(fw)
  fw.zero_words(TensixL1.MEM_ZEROS_BASE, TensixL1.MEM_ZEROS_SIZE // 4)
  fw.invalidate_risc_caches()
  fw.jal(R.RA, "reset_tensix")
  for index in (0, 1):
    fw.noc(index).store_risc_coordinates(*Firmware.NOC_COORDINATE_BASE["brisc"])
  fw.write32(TensixMMIO.NCRISC_HALT_RESUME_ADDR, 0)
  fw.jal(R.RA, "init_nocs")
  fw.invalidate_risc_caches()

  fw.write32(FirmwareControl.SUBORDINATE_SYNC, RunState.ALL_INIT)
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, 0)
  for role in range(1, 5):
    fw.wait8(FirmwareControl.SUBORDINATE_SYNC + role - 1, RunState.BOOT_READY)

  fw.label("run_loop")
  fw.wait8(FirmwareControl.GO_SIGNAL, RunState.GO)
  fw.jal(R.RA, "reset_tensix")
  fw.jal(R.RA, "init_nocs")

  fw.invalidate_risc_caches()
  fw.signal_range(FirmwareControl.SUBORDINATE_SYNC, range(4), RunState.GO)
  fw.call_fixed_kernel(TensixL1.WORKER_TEXT_BASE["brisc"])
  for role in range(1, 5):
    fw.wait8(FirmwareControl.SUBORDINATE_SYNC + role - 1, RunState.DONE)
  fw.signal8(FirmwareControl.GO_SIGNAL, RunState.DONE)
  _notify_dispatch(fw)
  fw.j("run_loop")

  fw.label("reset_tensix")
  Tensix.reset_hardware(fw)
  CB.setup_local_cbs(fw)
  fw.jalr(R.ZERO, R.RA)

  fw.label("init_nocs")
  for index in (0, 1):
    fw.noc(index).init_firmware()
  fw.jalr(R.ZERO, R.RA)
  return fw
