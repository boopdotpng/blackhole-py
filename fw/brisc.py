from __future__ import annotations

from asm import FIRMWARE_TEXT_BASE, Kernel

BRISC_STACK_TOP = 0xFFB01FF0


def build() -> Kernel:
  fw = Kernel.firmware("brisc")
  fw.setup_stack(BRISC_STACK_TOP)
  fw.set_subordinate_reset_pcs(
    ncrisc=FIRMWARE_TEXT_BASE["ncrisc"],
    trisc0=FIRMWARE_TEXT_BASE["trisc0"],
    trisc1=FIRMWARE_TEXT_BASE["trisc1"],
    trisc2=FIRMWARE_TEXT_BASE["trisc2"],
  )
  fw.deassert_all_riscs()
  for role in (1, 2, 3, 4):
    fw.wait_subordinate_done(role)
  fw.signal_done()

  fw.label("run_loop")
  fw.wait_go()
  for role in (1, 2, 3, 4):
    fw.signal_subordinate_go(role)
  fw.run_launch_kernel(0)
  for role in (1, 2, 3, 4):
    fw.wait_subordinate_done(role)
  fw.signal_done()
  fw.j("run_loop")
  return fw
