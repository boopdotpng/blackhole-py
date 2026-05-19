#!/usr/bin/env python3
"""Read a compact set of Tensix L1/MMIO breadcrumbs after a failed run."""
from __future__ import annotations

import argparse
import struct

from ttk.addrs import TensixL1, TensixMMIO
from pcie import PCIDevice, TLBWindow


def parse_core(value: str) -> tuple[int, int]:
  x, y = value.split(",", 1)
  return int(x, 0), int(y, 0)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--core", default="1,2", type=parse_core)
  parser.add_argument("--bytes", default=32, type=int)
  args = parser.parse_args()

  core = args.core
  dev = PCIDevice(use_vfio=False)
  try:
    with TLBWindow(dev, core) as win:
      def blob(addr: int, size: int | None = None) -> bytes:
        n = args.bytes if size is None else size
        return bytes(win.mm[addr + i] for i in range(n))

      def word(addr: int) -> int:
        return struct.unpack("<I", blob(addr, 4))[0]

      print(f"core {core}")
      print(f"boot_word: 0x{word(0):08x}")
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
        ("fw_debug", 0x19000, 64),
      ]:
        print(f"{name} 0x{addr:x}: {blob(addr, size).hex()}")

    mmio_base = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0 & ~((1 << 21) - 1)
    with TLBWindow(dev, core, addr=mmio_base) as win:
      for name, addr in [
        ("soft_reset", TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0),
        ("trisc0_pc", TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC),
        ("trisc1_pc", TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC),
        ("trisc2_pc", TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC),
        ("ncrisc_pc", TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC),
      ]:
        print(f"{name} 0x{addr:x}: 0x{win.read32(addr - mmio_base):08x}")
  finally:
    dev.close()


if __name__ == "__main__":
  main()
