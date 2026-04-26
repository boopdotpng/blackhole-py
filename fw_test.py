#!/usr/bin/env python3
"""Real-firmware bring-up test for emu.

Boots the checked-in firmware PT_LOAD images, then dispatches tiny raw kernel
payloads that just return.  This is a firmware/control-flow test, not a Tensix
compute test.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

import dsl
from emu.memory import LAUNCH_MSG_RD_PTR
from emu.device import Device


HARVESTED_DRAM_BANKS = [3]
BOOT_MAX_CYCLES = int(os.environ.get("BOOT_MAX_CYCLES", "200000"))
RUN_MAX_CYCLES = int(os.environ.get("RUN_MAX_CYCLES", "200000"))


def ret_kernel() -> bytes:
  return dsl.pack([dsl.RET()])


def main() -> int:
  core_count = int(os.environ.get("CORES", "1"))
  try:
    dev = Device(
      harvested_banks=HARVESTED_DRAM_BANKS,
      core_count=core_count,
      firmware_boot_max_cycles=BOOT_MAX_CYCLES,
    )
  except Exception as e:
    print(f"BOOT FAIL: {type(e).__name__}: {e}", file=sys.stderr)
    return 1
  tiles = list(dev.tiles.values())

  ret = ret_kernel()
  try:
    run_cycles = dev.dispatch(
      brisc=ret,
      ncrisc=ret,
      trisc=(ret, ret, ret),
      max_cycles=RUN_MAX_CYCLES,
    )
  except Exception as e:
    print(f"DISPATCH FAIL: {type(e).__name__}: {e}", file=sys.stderr)
    return 1

  print("fw_test: pass")
  print(f"  cores         : {core_count}")
  print(f"  boot cycles   : {dev.firmware_boot_cycles}")
  print(f"  dispatch cycles: {run_cycles}")
  print(f"  total cycles  : {dev.core_cycles}")
  for tile in tiles:
    print(
      f"  tile ({tile.x},{tile.y}): "
      f"go=0x{tile.l1.read8(dev.go_messages_addr + 3):02x} "
      f"rdptr={tile.l1.read32(LAUNCH_MSG_RD_PTR)}"
    )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
