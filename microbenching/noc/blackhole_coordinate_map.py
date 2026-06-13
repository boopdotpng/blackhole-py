#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pcie import PCIDevice  # noqa: E402
from ttk.blackhole_coords import (  # noqa: E402
  T6_X_LOCATIONS,
  directional_torus_hops,
  raw_coord_for_noc,
  tensix_coordinate_map,
  translated_tensix_to_raw_noc0,
)

ENABLED_TENSIX_COL_TAG = 34
NOC_TRANSLATION_TAG = 40


def parse_coord(text: str) -> tuple[int, int]:
  pieces = text.split(",")
  if len(pieces) != 2:
    raise argparse.ArgumentTypeError(f"expected x,y, got {text!r}")
  return int(pieces[0], 0), int(pieces[1], 0)


def read_telemetry(index: int) -> tuple[int, int | None]:
  with PCIDevice(index=index, use_vfio=False) as dev:
    layout = dev.telemetry_layout()
    enabled = dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
    noc_translation = dev.telemetry_tag(layout, NOC_TRANSLATION_TAG)
    if enabled is None:
      raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
    return enabled, noc_translation


def main() -> None:
  parser = argparse.ArgumentParser(description="Decode Blackhole Tensix translated/raw coordinate mapping.")
  parser.add_argument("--device", type=int, default=0)
  parser.add_argument("--enabled-tensix-col", type=lambda s: int(s, 0))
  parser.add_argument("--src", type=parse_coord, help="translated source Tensix coord x,y")
  parser.add_argument("--dst", type=parse_coord, help="translated destination Tensix coord x,y")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  args = parser.parse_args()

  if args.enabled_tensix_col is None:
    enabled, noc_translation = read_telemetry(args.device)
  else:
    enabled, noc_translation = args.enabled_tensix_col, None

  cmap = tensix_coordinate_map(enabled)
  print(f"ENABLED_TENSIX_COL        0x{enabled:08x}")
  if noc_translation is not None:
    print(f"NOC_TRANSLATION          {noc_translation & 0xFFFFFFFF}")
  print(f"physical harvesting mask 0x{cmap.physical_harvesting_mask:04x}")
  print(f"sorted harvesting mask   0x{cmap.sorted_harvesting_mask:04x}")
  print(f"raw Tensix columns       {list(T6_X_LOCATIONS)}")
  print(f"live raw columns         {list(cmap.live_raw_x)}")
  print(f"harvested raw columns    {list(cmap.harvested_raw_x)}")
  print()
  print("translated live x -> raw NoC0 x")
  for tx in cmap.translated_live_x:
    print(f"  {tx:2d} -> {cmap.translated_to_raw_x[tx]:2d}")
  if cmap.translated_harvested_to_raw_x:
    print()
    print("translated hidden/harvested x -> raw NoC0 x")
    for tx, raw_x in sorted(cmap.translated_harvested_to_raw_x.items()):
      print(f"  {tx:2d} -> {raw_x:2d}")

  if args.src is not None or args.dst is not None:
    if args.src is None or args.dst is None:
      raise SystemExit("--src and --dst must be provided together")
    src_raw0 = translated_tensix_to_raw_noc0(args.src, cmap)
    dst_raw0 = translated_tensix_to_raw_noc0(args.dst, cmap)
    src_raw = raw_coord_for_noc(src_raw0, args.noc)
    dst_raw = raw_coord_for_noc(dst_raw0, args.noc)
    total, x_hops, y_hops = directional_torus_hops(src_raw, dst_raw, args.noc)
    print()
    print(f"translated {args.src} -> {args.dst} on noc{args.noc}")
    print(f"raw noc0   {src_raw0} -> {dst_raw0}")
    print(f"raw noc{args.noc}   {src_raw} -> {dst_raw}")
    print(f"hops       total={total} x={x_hops} y={y_hops}")


if __name__ == "__main__":
  main()
