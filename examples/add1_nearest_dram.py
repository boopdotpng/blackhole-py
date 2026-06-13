#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import add1


def main() -> None:
  parser = add1.make_argparser()
  parser.set_defaults(read_endpoint_mode="nearest", write_endpoint_mode="nearest")
  args = parser.parse_args()
  if args.tiles_per_core <= 0:
    raise ValueError("--tiles-per-core must be positive")

  device = add1.Device()
  try:
    cores, use_grid = add1.select_cores(device, args.cores, args.core)
    if args.core_count is not None:
      if args.core_count <= 0:
        raise ValueError("--core-count must be positive")
      cores = cores[:args.core_count]

    num_banks = len(device.dram.bank_tiles)
    layout = device.dev.telemetry_layout()
    enabled_tensix_col = device.dev.telemetry_tag(layout, 34)
    if enabled_tensix_col is None:
      raise RuntimeError("nearest DRAM endpoint mode needs ENABLED_TENSIX_COL telemetry")

    nearest_read = add1.nearest_dram_endpoint_coords_for_cores(
      cores,
      harvested_dram_bank=device.board_info.harvested_dram_bank,
      enabled_tensix_col=enabled_tensix_col,
      num_banks=num_banks,
      noc=0,
    )
    nearest_write = add1.nearest_dram_endpoint_coords_for_cores(
      cores,
      harvested_dram_bank=device.board_info.harvested_dram_bank,
      enabled_tensix_col=enabled_tensix_col,
      num_banks=num_banks,
      noc=1,
    )

    n_tiles = len(cores) * args.tiles_per_core
    alloc_tiles = add1.allocation_tiles_for(len(cores), args.tiles_per_core, num_banks, args.bank_mode)
    src_rm = add1.make_input(n_tiles)
    src_buf = device.dram.alloc(alloc_tiles, dtype=add1.Dtype.Float16_b, shape=(alloc_tiles, 32, 32), name="src_nearest")
    src_payload = bytearray(src_buf.size)
    for src_tile, dst_tile in enumerate(add1.logical_tile_ids(len(cores), args.tiles_per_core, num_banks, args.bank_mode)):
      src_payload[dst_tile * add1.TILE_BYTES:(dst_tile + 1) * add1.TILE_BYTES] = src_rm[src_tile * add1.TILE_BYTES:(src_tile + 1) * add1.TILE_BYTES]
    device.dram_write(src_buf, bytes(src_payload))
    dst_buf = device.dram.alloc(alloc_tiles, dtype=add1.Dtype.Float16_b, shape=(alloc_tiles, 32, 32), name="dst_nearest")

    prog = add1.build_program(
      src_buf.addr,
      dst_buf.addr,
      num_banks,
      cores=cores,
      tiles_per_core=args.tiles_per_core,
      dram_bank_coords_noc0=add1.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0),
      dram_bank_coords_noc1=add1.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1),
      read_endpoint_mode=args.read_endpoint_mode,
      write_endpoint_mode=args.write_endpoint_mode,
      nearest_read_coords=nearest_read if args.read_endpoint_mode == "nearest" else None,
      nearest_write_coords=nearest_write if args.write_endpoint_mode == "nearest" else None,
      bank_mode=args.bank_mode,
      use_grid=use_grid,
    )
    timings = device.run(prog)
    if not args.no_verify:
      out = device.dram_read(dst_buf)
      add1.verify_output_tiles(
        out, src_rm,
        core_count=len(cores), tiles_per_core=args.tiles_per_core,
        num_banks=num_banks, bank_mode=args.bank_mode,
      )

    total_bytes = n_tiles * add1.TILE_BYTES
    print(
      f"PASS add1_nearest_dram bank_mode={args.bank_mode} read_endpoint={args.read_endpoint_mode} "
      f"write_endpoint={args.write_endpoint_mode} {len(cores)} cores x {args.tiles_per_core} tiles/core = {n_tiles} tiles"
    )
    for timing in timings:
      name = f"{timing['name']}: " if timing["name"] else ""
      us = timing["us"]
      gbps = (total_bytes * 3) / (us * 1e-6) / 1e9 if us > 0 else 0.0
      print(f"  {name}{us:,.1f} us, {gbps:.1f} GB/s effective add1 traffic")
  finally:
    device.close()


if __name__ == "__main__":
  main()
