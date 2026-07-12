"""Resident NCRISC firmware for the fixed-layout rewrite."""
from asm import KernelBuilder
from fw.consts import Firmware, FirmwareControl, NcriscLocalState, RunSync, TensixL1


def build():
  fw = KernelBuilder.standalone("ncrisc")
  fw.setup_stack(Firmware.NCRISC_STACK_TOP)
  fw.configure_csr()

  for index in (0, 1):
    fw.noc(index).store_risc_coordinates(
      NcriscLocalState.MY_X, NcriscLocalState.MY_Y,
    )

  fw.signal8(FirmwareControl.SUBORDINATE_SYNC, RunSync.BOOT_READY)

  fw.label("run_loop")
  fw.wait8(FirmwareControl.SUBORDINATE_SYNC, RunSync.GO)
  fw.call_fixed_kernel(TensixL1.WORKER_TEXT_BASE["ncrisc"])
  fw.signal8(FirmwareControl.SUBORDINATE_SYNC, RunSync.DONE)
  fw.j("run_loop")
  return fw
