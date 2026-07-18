from asm import Asm
from fw.consts import Firmware, FirmwareControl, RunState, TensixL1

def build_ncrisc():
  fw = Asm.firmware("ncrisc")
  fw.setup_stack(Firmware.NCRISC_STACK_TOP)
  fw.configure_csr()

  fw.signal8(FirmwareControl.SUBORDINATE_SYNC, RunState.BOOT_READY)

  fw.label("run_loop")
  fw.wait8(FirmwareControl.SUBORDINATE_SYNC, RunState.GO)
  fw.call_fixed_kernel(TensixL1.WORKER_TEXT_BASE["ncrisc"])
  fw.signal8(FirmwareControl.SUBORDINATE_SYNC, RunState.DONE)
  fw.j("run_loop")
  return fw
