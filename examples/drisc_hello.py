#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import struct
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import KernelBase
from dsl import t0, t1
from pcie import PCIDevice, TLBWindow
from ttk.drisc import (  # noqa: F401  (re-exported for the other DRISC POCs)
  DRISC_FW_BASE, DRISC_L1_NOC_ALIAS, DRISC_RESET_PC, REG_TLB,
  SOFT_RESET_0, SOFT_RESET_BRISC, RegWindow,
)

DRISC_MAGIC_ADDR = 0x1F000


def build_hello(magic: int) -> bytes:
  fw = KernelBase(base_addr=DRISC_FW_BASE)
  loop = fw._new_label("spin")
  fw.li(t0, DRISC_MAGIC_ADDR)
  fw.li(t1, magic)
  fw.sw(t1, t0, 0)
  fw.label(loop)
  fw.j(loop)
  return fw.compile()[0].data


def select_dram_core(dev: PCIDevice, bank: int, endpoint: int) -> tuple[int, int]:
  info = dev.board_info(fast_dispatch=True)
  tiles = [tile for tile in info.dram_tiles if tile[0] == bank]
  if not tiles:
    raise ValueError(f"bank {bank} is not enabled")
  if endpoint < 0 or endpoint >= len(tiles):
    raise ValueError(f"endpoint must be in [0, {len(tiles) - 1}] for bank {bank}")
  _, x, y = tiles[endpoint]
  return x, y


def main():
  parser = argparse.ArgumentParser(description="Minimal Blackhole DRISC launch probe.")
  parser.add_argument("--bank", type=int, default=0)
  parser.add_argument("--endpoint", type=int, default=0)
  parser.add_argument("--magic", type=lambda s: int(s, 0), default=0xD215C003)
  parser.add_argument("--timeout", type=float, default=1.0)
  args = parser.parse_args()

  os.environ.pop("TT_USB", None)
  dev = PCIDevice(use_vfio=True)
  core = select_dram_core(dev, args.bank, args.endpoint)
  code = build_hello(args.magic)

  dev.set_power_state(True)
  try:
    l1 = TLBWindow(dev, start=core, addr=DRISC_L1_NOC_ALIAS)
    regs = RegWindow(dev, core)
    try:
      l1.write(DRISC_MAGIC_ADDR, struct.pack("<I", 0))
      l1.write(DRISC_FW_BASE, code)

      reset_state = regs.read32(SOFT_RESET_0)
      regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
      regs.write32(DRISC_RESET_PC, DRISC_FW_BASE)
      time.sleep(0.01)
      regs.write32(SOFT_RESET_0, reset_state & ~SOFT_RESET_BRISC)

      got = 0
      deadline = time.time() + args.timeout
      while time.time() < deadline:
        got = struct.unpack("<I", l1.read(DRISC_MAGIC_ADDR, 4))[0]
        if got == args.magic:
          break
        time.sleep(0.001)

      final_reset_state = regs.read32(SOFT_RESET_0)
      regs.write32(SOFT_RESET_0, final_reset_state | SOFT_RESET_BRISC)
    finally:
      regs.close()
      l1.close()
  finally:
    dev.set_power_state(False)
    dev.close()

  print(
    f"dram_core={core} code_bytes={len(code)} "
    f"magic=0x{got:08x} ok={got == args.magic}"
  )
  if got != args.magic:
    raise SystemExit(1)


if __name__ == "__main__":
  main()
