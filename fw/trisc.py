from __future__ import annotations
from asm import Kernel

TRISC_STACK_TOP = 0xFFB00FF0

def build(trisc_id: int) -> Kernel:
  if trisc_id not in (0, 1, 2):
    raise ValueError(f"unknown TRISC id {trisc_id!r}")
  role = 2 + trisc_id
  fw = Kernel.firmware(f"trisc{trisc_id}")
  fw.setup_stack(TRISC_STACK_TOP)
  fw.signal_subordinate_done(role)
  fw.label("run_loop")
  fw.wait_subordinate_go(role)
  fw.run_launch_kernel(role)
  fw.signal_subordinate_done(role)
  fw.j("run_loop")
  return fw

def build_trisc0() -> Kernel:
  return build(0)

def build_trisc1() -> Kernel:
  return build(1)

def build_trisc2() -> Kernel:
  return build(2)
