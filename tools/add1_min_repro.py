#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("EMU", "1")
os.environ.setdefault("TT_USB", "1")
sys.path.insert(0, str(ROOT))

from device import Device  # noqa: E402
from examples import add1  # noqa: E402
from pcie import TLBWindow  # noqa: E402
from program import Dtype  # noqa: E402
from ttk.addrs import CircularBuffer as CB, Mailbox, TensixL1  # noqa: E402


def words(data: bytes, offset: int, count: int = 16) -> list[str]:
  return [f"0x{int.from_bytes(data[offset + i:offset + i + 2], 'little'):04x}" for i in range(0, count * 2, 2)]


def print_l1_snapshot(device: Device, core: tuple[int, int]):
  addrs = [
    ("GO_MSG", TensixL1.GO_MSG),
    ("SUBORDINATE_SYNC", Mailbox.SUBORDINATE_SYNC),
    ("SYNC_READ", add1.SYNC_READ),
    ("SYNC_DONE0", add1.SYNC_DONE0),
    ("SYNC_DONE1", add1.SYNC_DONE1),
    ("SYNC_DONE2", add1.SYNC_DONE2),
    ("CB0_ACKED", (CB.SYNC_TILES_ACKED_BASE + 0 * CB.SYNC_STRIDE) & 0x1FFFFF),
    ("CB0_RECEIVED", (CB.SYNC_TILES_RECEIVED_BASE + 0 * CB.SYNC_STRIDE) & 0x1FFFFF),
    ("CBOUT_ACKED", (CB.SYNC_TILES_ACKED_BASE + add1.OUT_CB * CB.SYNC_STRIDE) & 0x1FFFFF),
    ("CBOUT_RECEIVED", (CB.SYNC_TILES_RECEIVED_BASE + add1.OUT_CB * CB.SYNC_STRIDE) & 0x1FFFFF),
  ]
  print("l1 snapshot:")
  with TLBWindow(device.dev, start=core) as win:
    for name, addr in addrs:
      print(f"  {name:16s} l1[{addr:#x}] = 0x{win.read32(addr):08x}")


def main() -> int:
  ap = argparse.ArgumentParser(description="Minimal add1 multi-tile repro.")
  ap.add_argument("--tiles", type=int, default=2)
  ap.add_argument("--core", default=f"{add1.TARGET_CORE[0]},{add1.TARGET_CORE[1]}")
  args = ap.parse_args()

  core = tuple(int(x) for x in args.core.split(",", 1))
  add1.TILES_PER_CORE = args.tiles
  src_rm = add1._seed_src_tensor(args.tiles)
  exp = add1._expected_add1(src_rm)

  device = Device()
  try:
    src = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=(args.tiles, 32, 32), name="src")
    dst = device.dram.alloc(args.tiles, dtype=Dtype.Float16_b, shape=(args.tiles, 32, 32), name="dst")
    timings = device.run(add1.build_program(src.addr, dst.addr, len(device.dram.bank_tiles), cores=[core]))
    out = device.dram_read(dst)

    mismatch = add1._first_mismatch(out, exp)
    print(f"core={core} tiles={args.tiles} timings={[round(t['us'], 1) for t in timings]}")
    for tile in range(args.tiles):
      off = tile * add1.TILE_BYTES
      mark = "*" if mismatch is not None and off <= mismatch < off + add1.TILE_BYTES else " "
      print(f"{mark} tile {tile} got {words(out, off)}")
      print(f"  tile {tile} exp {words(exp, off)}")
    print_l1_snapshot(device, core)
  finally:
    device.close()

  if mismatch is not None:
    print(f"FAIL mismatch byte={mismatch}")
    return 2
  print("PASS")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
