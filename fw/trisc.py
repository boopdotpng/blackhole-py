from __future__ import annotations
from asm import Kernel
from dsl import Reg, ra, sp, t0, t1, t2, t3, t4, zero

TRISC_STACK_TOP = 0xFFB00FF0
SUBORDINATE_SYNC = 0x68
RUN_SYNC_MSG_GO = 0x80
RUN_SYNC_MSG_DONE = 0x00

LAUNCH = 0x70
LAUNCH_KERNEL_CONFIG_BASE = 0
LAUNCH_KERNEL_TEXT_OFFSET = 44
LAUNCH_ENABLES = 76


def write8(fw: Kernel, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sb(value, addr, 0)


def read32(fw: Kernel, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  return fw.lw(rd, addr, 0)


def wait8(fw: Kernel, addr: int, value: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  fw.li(ptr, addr)
  fw.li(expected, value)
  start = fw._new_label("wait8")
  fw.label(start)
  fw.lbu(actual, ptr, 0)
  fw.bne(actual, expected, start)
  return fw


def setup_stack(fw: Kernel):
  return fw.li(sp, TRISC_STACK_TOP)


def signal_subordinate_done(fw: Kernel, role: int):
  return write8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_DONE)


def wait_subordinate_go(fw: Kernel, role: int):
  return wait8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_GO)


def launch_kernel_enabled(fw: Kernel, role: int, *, enabled: Reg = t0, mask: Reg = t1):
  read32(fw, enabled, LAUNCH + LAUNCH_ENABLES)
  fw.li(mask, 1 << role)
  return fw.and_(enabled, enabled, mask)


def run_launch_kernel(fw: Kernel, role: int, *, launch: Reg = t0, config_base: Reg = t1,
                      offset: Reg = t2, entry: Reg = t3, enabled: Reg = t4):
  skip = fw._new_label("skip_kernel")
  launch_kernel_enabled(fw, role, enabled=enabled, mask=offset)
  fw.beq(enabled, zero, skip)
  fw.li(launch, LAUNCH)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lw(offset, launch, LAUNCH_KERNEL_TEXT_OFFSET + 4 * role)
  fw.add(entry, config_base, offset)
  fw.jalr(ra, entry, 0)
  fw.label(skip)
  return fw

def build(trisc_id: int) -> Kernel:
  if trisc_id not in (0, 1, 2):
    raise ValueError(f"unknown TRISC id {trisc_id!r}")
  role = 2 + trisc_id
  fw = Kernel.firmware(f"trisc{trisc_id}")
  setup_stack(fw)
  signal_subordinate_done(fw, role)
  fw.label("run_loop")
  wait_subordinate_go(fw, role)
  run_launch_kernel(fw, role)
  signal_subordinate_done(fw, role)
  fw.j("run_loop")
  return fw

def build_trisc0() -> Kernel:
  return build(0)

def build_trisc1() -> Kernel:
  return build(1)

def build_trisc2() -> Kernel:
  return build(2)
