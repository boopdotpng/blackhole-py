from __future__ import annotations

from asm import Kernel

NCRISC_STACK_TOP = 0xFFB01FF0


def build() -> Kernel:
  fw = Kernel.firmware("ncrisc")
  fw.setup_stack(NCRISC_STACK_TOP)
  fw.signal_subordinate_done(1)
  fw.label("run_loop")
  fw.wait_subordinate_go(1)
  fw.run_launch_kernel(1)
  fw.signal_subordinate_done(1)
  fw.j("run_loop")
  return fw
