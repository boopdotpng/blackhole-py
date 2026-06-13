#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
from pcie import TLBWindow  # noqa: E402


NIU_BASE = (0xFFB20000, 0xFFB30000)
TLB_ALIGN = TLBWindow.SIZE_2M


def align_down(value: int, align: int) -> int:
  return value & ~(align - 1)


def parse_table(words: list[int]) -> list[int]:
  out: list[int] = []
  for word in words:
    for _ in range(6):
      out.append(word & 0x1F)
      word >>= 5
      if len(out) == 32:
        return out
  return out


def read_u32(win: TLBWindow, addr: int, base: int) -> int:
  return struct.unpack("<I", win.read(addr - base, 4))[0]


def dump_noc(device, core: tuple[int, int], noc: int) -> str:
  niu = NIU_BASE[noc]
  base = align_down(niu, TLB_ALIGN)
  with TLBWindow(device.dev, start=core, addr=base) as win:
    niu_cfg_0 = read_u32(win, niu + 0x100, base)
    x_words = [read_u32(win, niu + 0x118 + i * 4, base) for i in range(6)]
    y_words = [read_u32(win, niu + 0x130 + i * 4, base) for i in range(6)]
    id_logical = read_u32(win, niu + 0x148, base)
    col_mask = read_u32(win, niu + 0x150, base)
    row_mask = read_u32(win, niu + 0x154, base)
    ddr_words = [read_u32(win, niu + 0x158 + i * 4, base) for i in range(6)]
    ddr_col_swap = read_u32(win, niu + 0x170, base)

  lx = id_logical & 0x3F
  ly = (id_logical >> 6) & 0x3F
  lines = [
    f"core={core[0]},{core[1]} noc{noc} niu_base=0x{niu:08x}",
    f"  NIU_CFG_0                    0x{niu_cfg_0:08x} translate={(niu_cfg_0 >> 14) & 1}",
    f"  NOC_ID_LOGICAL               0x{id_logical:08x} x={lx} y={ly}",
    f"  NOC_ID_TRANSLATE_COL_MASK    0x{col_mask:08x}",
    f"  NOC_ID_TRANSLATE_ROW_MASK    0x{row_mask:08x}",
    "  NOC_X_ID_TRANSLATE_TABLE[]  " + " ".join(f"0x{w:08x}" for w in x_words),
    "  NOC_Y_ID_TRANSLATE_TABLE[]  " + " ".join(f"0x{w:08x}" for w in y_words),
    "  DDR_COORD_TRANSLATE_TABLE[] " + " ".join(f"0x{w:08x}" for w in ddr_words),
    f"  DDR_COORD_TRANSLATE_COL_SWAP 0x{ddr_col_swap:08x}",
    f"  decoded x table              {parse_table(x_words)}",
    f"  decoded y table              {parse_table(y_words)}",
    f"  decoded ddr table            {parse_table(ddr_words)}",
  ]
  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="Read Blackhole NIU coordinate-translation registers.")
  parser.add_argument("--core", type=harness.parse_core, default=(1, 2))
  parser.add_argument("--nocs", default="0,1")
  args = parser.parse_args()
  nocs = tuple(int(item.strip(), 0) for item in args.nocs.split(",") if item.strip())
  with harness.open_device() as device:
    if args.core not in set(device.board_info.worker_cores):
      raise ValueError(f"--core {args.core} is not a worker core")
    for noc in nocs:
      if noc not in (0, 1):
        raise ValueError(f"noc must be 0 or 1, got {noc}")
      print(dump_noc(device, args.core, noc))


if __name__ == "__main__":
  main()
