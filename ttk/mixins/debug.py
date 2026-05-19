from __future__ import annotations

import atexit
import os
import struct
import sys

from ttk.addrs import Firmware, TensixL1, TensixMMIO


def parse_debug_core(value: str) -> tuple[int, int]:
  x, y = value.split(",", 1)
  return int(x, 0), int(y, 0)


def print_debug_postmortem(core: tuple[int, int] = (1, 2), byte_count: int = 32, *,
                           file=None):
  from pcie import PCIDevice, TLBWindow

  out = sys.stdout if file is None else file
  dev = PCIDevice(use_vfio=False)
  try:
    with TLBWindow(dev, core) as win:
      def blob(addr: int, size: int | None = None) -> bytes:
        n = byte_count if size is None else size
        return bytes(win.mm[addr + i] for i in range(n))

      def word(addr: int) -> int:
        return struct.unpack("<I", blob(addr, 4))[0]

      print(f"debug postmortem core {core}", file=out)
      print(f"boot_word: 0x{word(0):08x}", file=out)
      for name, addr, size in [
        ("boot", 0x0, 16),
        ("sync", 0x68, 16),
        ("launch", TensixL1.LAUNCH, 64),
        ("go", TensixL1.GO_MSG, 16),
        ("go_index", TensixL1.GO_MSG_INDEX, 16),
        ("brisc_text", 0x3840, 16),
        ("brisc_local", TensixL1.BRISC_INIT_LOCAL_L1_BASE_SCRATCH, 32),
        ("ncrisc_text", 0x5440, 16),
        ("ncrisc_local", TensixL1.NCRISC_INIT_LOCAL_L1_BASE_SCRATCH, 32),
        ("trisc0_text", 0x5A40, 16),
        ("trisc0_local", TensixL1.TRISC0_INIT_LOCAL_L1_BASE_SCRATCH, 32),
        ("trisc1_text", 0x6040, 16),
        ("trisc1_local", TensixL1.TRISC1_INIT_LOCAL_L1_BASE_SCRATCH, 32),
        ("trisc2_text", 0x6640, 16),
        ("trisc2_local", TensixL1.TRISC2_INIT_LOCAL_L1_BASE_SCRATCH, 32),
        ("bank_table", TensixL1.MEM_BANK_TO_NOC_SCRATCH, 64),
        ("logical_to_virtual", TensixL1.LOGICAL_TO_VIRTUAL_SCRATCH, 64),
        ("fw_debug", Firmware.FW_DEBUG, 64),
      ]:
        print(f"{name} 0x{addr:x}: {blob(addr, size).hex()}", file=out)

    mmio_base = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 & ~((1 << 21) - 1)
    with TLBWindow(dev, core, addr=mmio_base) as win:
      for name, addr in [
        ("soft_reset", TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0),
        ("trisc0_pc", TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC),
        ("trisc1_pc", TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC),
        ("trisc2_pc", TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC),
        ("ncrisc_pc", TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC),
      ]:
        print(f"{name} 0x{addr:x}: 0x{win.read32(addr - mmio_base):08x}", file=out)
  finally:
    dev.close()


class DebugMixin:
  _debug_postmortem_registered = False

  @classmethod
  def register_debug_postmortem(cls):
    if cls._debug_postmortem_registered:
      return
    cls._debug_postmortem_registered = True
    if os.environ.get("TT_DEBUG_POSTMORTEM", "1") == "0":
      return

    def run_postmortem():
      core = parse_debug_core(os.environ.get("TT_DEBUG_POSTMORTEM_CORE", "1,2"))
      byte_count = int(os.environ.get("TT_DEBUG_POSTMORTEM_BYTES", "32"), 0)
      try:
        print_debug_postmortem(core, byte_count, file=sys.stderr)
      except Exception as exc:
        print(f"debug postmortem failed: {exc}", file=sys.stderr)

    atexit.register(run_postmortem)

  def breadcrumb(self, value: int, offset: int = 0):
    self.register_debug_postmortem()
    return self.write32(Firmware.FW_DEBUG + offset, value)
