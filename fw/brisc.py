from __future__ import annotations

from asm import FIRMWARE_TEXT_BASE, Kernel
from dsl import Reg, ra, sp, t0, t1, t2, t3, t4, zero

BRISC_STACK_TOP = 0xFFB01FF0
NCRISC_RESET_PC = 0xFFB12238
TRISC0_RESET_PC = 0xFFB12228
TRISC1_RESET_PC = 0xFFB1222C
TRISC2_RESET_PC = 0xFFB12230
TRISC_RESET_PC_OVERRIDE = 0xFFB12234
NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C
SOFT_RESET_0 = 0xFFB121B0

GO_SIGNAL = 0x373
SUBORDINATE_SYNC = 0x68
RUN_MSG_GO = 0x80
RUN_MSG_DONE = 0x00
RUN_SYNC_MSG_GO = 0x80
RUN_SYNC_MSG_DONE = 0x00

LAUNCH = 0x70
LAUNCH_KERNEL_CONFIG_BASE = 0
LAUNCH_KERNEL_TEXT_OFFSET = 44
LAUNCH_ENABLES = 76


def write32(fw: Kernel, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sw(value, addr, 0)


def read32(fw: Kernel, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  return fw.lw(rd, addr, 0)


def write8(fw: Kernel, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sb(value, addr, 0)


def wait8(fw: Kernel, addr: int, value: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  fw.li(ptr, addr)
  fw.li(expected, value)
  start = fw._new_label("wait8")
  fw.label(start)
  fw.lbu(actual, ptr, 0)
  fw.bne(actual, expected, start)
  return fw


def setup_stack(fw: Kernel):
  return fw.li(sp, BRISC_STACK_TOP)


def set_subordinate_reset_pcs(fw: Kernel):
  write32(fw, NCRISC_RESET_PC, FIRMWARE_TEXT_BASE["ncrisc"])
  write32(fw, TRISC0_RESET_PC, FIRMWARE_TEXT_BASE["trisc0"])
  write32(fw, TRISC1_RESET_PC, FIRMWARE_TEXT_BASE["trisc1"])
  write32(fw, TRISC2_RESET_PC, FIRMWARE_TEXT_BASE["trisc2"])
  write32(fw, TRISC_RESET_PC_OVERRIDE, 0b111)
  write32(fw, NCRISC_RESET_PC_OVERRIDE, 1)
  return fw


def deassert_all_riscs(fw: Kernel):
  return write32(fw, SOFT_RESET_0, 0)


def signal8(fw: Kernel, addr: int, value: int):
  return write8(fw, addr, value)


def wait_go(fw: Kernel):
  return wait8(fw, GO_SIGNAL, RUN_MSG_GO)


def signal_done(fw: Kernel):
  return signal8(fw, GO_SIGNAL, RUN_MSG_DONE)


def signal_subordinate_go(fw: Kernel, role: int):
  return signal8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_GO)


def wait_subordinate_done(fw: Kernel, role: int):
  return wait8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_DONE)


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


def build() -> Kernel:
  fw = Kernel.firmware("brisc")
  setup_stack(fw)
  set_subordinate_reset_pcs(fw)
  deassert_all_riscs(fw)
  for role in (1, 2, 3, 4):
    wait_subordinate_done(fw, role)
  signal_done(fw)

  fw.label("run_loop")
  wait_go(fw)
  for role in (1, 2, 3, 4):
    signal_subordinate_go(fw, role)
  run_launch_kernel(fw, 0)
  for role in (1, 2, 3, 4):
    wait_subordinate_done(fw, role)
  signal_done(fw)
  fw.j("run_loop")
  return fw
