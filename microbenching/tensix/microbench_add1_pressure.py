#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

from device import Device  # noqa: E402
from examples import add1  # noqa: E402
from program import Dtype  # noqa: E402
from ttk.addrs import p100_dram_bank_endpoint_coords  # noqa: E402
from ttk.blackhole_coords import tensix_coordinate_map, translated_tensix_to_raw_noc0  # noqa: E402


ENABLED_TENSIX_COL_TAG = 34


class SelectedCoreProgram:
  def __init__(self, program, selected_cores: list[tuple[int, int]]):
    self.program = program
    self.selected_cores = selected_cores
    self.name = getattr(program, "name", "")

  def lower(self, cores=None, *, dispatch_mode, host_assigned_id=0):
    return self.program.lower(
      self.selected_cores,
      dispatch_mode=dispatch_mode,
      host_assigned_id=host_assigned_id,
    )


def parse_counts(text: str) -> list[int]:
  counts = [int(item.strip(), 0) for item in text.split(",") if item.strip()]
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive core counts")
  return counts


def parse_modes(text: str) -> list[str]:
  modes = [item.strip() for item in text.split(",") if item.strip()]
  bad = [mode for mode in modes if mode not in ("spread", "local")]
  if bad:
    raise argparse.ArgumentTypeError(f"bad bank mode(s): {','.join(bad)}")
  return modes


def raw_ordered_cores(device: Device, cores: list[tuple[int, int]]) -> list[tuple[int, int]]:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  cmap = tensix_coordinate_map(enabled)
  return sorted(cores, key=lambda core: (translated_tensix_to_raw_noc0(core, cmap)[1], translated_tensix_to_raw_noc0(core, cmap)[0]))


def run_case(device: Device, *, cores: list[tuple[int, int]], tiles_per_core: int, bank_mode: str,
             read_endpoint_mode: str, write_endpoint_mode: str,
             verify: bool) -> tuple[float, float]:
  num_banks = len(device.dram.bank_tiles)
  n_tiles = len(cores) * tiles_per_core
  total_bytes = n_tiles * add1.TILE_BYTES
  src_rm = add1.make_input(n_tiles)
  alloc_tiles = add1.allocation_tiles_for(len(cores), tiles_per_core, num_banks, bank_mode)
  src_buf = device.dram.alloc(alloc_tiles, dtype=Dtype.Float16_b, shape=(alloc_tiles, 32, 32), name=f"add1_src_{bank_mode}_{len(cores)}")
  src_payload = bytearray(src_buf.size)
  for src_tile, dst_tile in enumerate(add1.logical_tile_ids(len(cores), tiles_per_core, num_banks, bank_mode)):
    src_payload[dst_tile * add1.TILE_BYTES:(dst_tile + 1) * add1.TILE_BYTES] = src_rm[src_tile * add1.TILE_BYTES:(src_tile + 1) * add1.TILE_BYTES]
  device.dram_write(src_buf, bytes(src_payload))
  dst_buf = device.dram.alloc(alloc_tiles, dtype=Dtype.Float16_b, shape=(alloc_tiles, 32, 32), name=f"add1_dst_{bank_mode}_{len(cores)}")
  layout = device.dev.telemetry_layout()
  enabled_tensix_col = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled_tensix_col is None and (read_endpoint_mode == "nearest" or write_endpoint_mode == "nearest"):
    raise RuntimeError("nearest endpoint mode needs ENABLED_TENSIX_COL telemetry")
  nearest_read = None
  nearest_write = None
  if read_endpoint_mode == "nearest":
    nearest_read = add1.nearest_dram_endpoint_coords_for_cores(
      cores,
      harvested_dram_bank=device.board_info.harvested_dram_bank,
      enabled_tensix_col=enabled_tensix_col,
      num_banks=num_banks,
      noc=0,
    )
  if write_endpoint_mode == "nearest":
    nearest_write = add1.nearest_dram_endpoint_coords_for_cores(
      cores,
      harvested_dram_bank=device.board_info.harvested_dram_bank,
      enabled_tensix_col=enabled_tensix_col,
      num_banks=num_banks,
      noc=1,
    )
  program = add1.build_program(
    src_buf.addr,
    dst_buf.addr,
    num_banks,
    cores=cores,
    tiles_per_core=tiles_per_core,
    dram_bank_coords_noc0=p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0),
    dram_bank_coords_noc1=p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1),
    dram_bank_endpoint_coords_noc0=add1.p100_dram_bank_endpoint_coord_table(device.board_info.harvested_dram_bank, num_banks),
    dram_bank_endpoint_coords_noc1=add1.p100_dram_bank_endpoint_coord_table(device.board_info.harvested_dram_bank, num_banks),
    read_endpoint_mode=read_endpoint_mode,
    write_endpoint_mode=write_endpoint_mode,
    nearest_read_coords=nearest_read,
    nearest_write_coords=nearest_write,
    bank_mode=bank_mode,
    use_grid=False,
  )
  timings = device.run(SelectedCoreProgram(program, cores))
  us = next((float(timing["us"]) for timing in timings if timing.get("name") == "add1"), float(timings[-1]["us"]))
  if verify:
    out = device.dram_read(dst_buf)
    add1.verify_output_tiles(
      out, src_rm,
      core_count=len(cores), tiles_per_core=tiles_per_core,
      num_banks=num_banks, bank_mode=bank_mode,
    )
  gbps = (total_bytes * 3) / (us * 1e-6) / 1e9 if us > 0 else 0.0
  return us, gbps


def main() -> None:
  parser = argparse.ArgumentParser(description="Sweep add1 all-core DRAM pressure and bank-locality modes.")
  parser.add_argument("--cores", choices=("auto", "program", "worker"), default="program")
  parser.add_argument("--counts", type=parse_counts, default=parse_counts("1,7,14,28,56,118"))
  parser.add_argument("--bank-modes", type=parse_modes, default=parse_modes("spread,local"))
  parser.add_argument("--order", choices=("raw", "translated"), default="raw")
  parser.add_argument("--read-endpoint-mode", choices=("preferred", "split3", "nearest"), default="preferred")
  parser.add_argument("--write-endpoint-mode", choices=("preferred", "split3", "nearest"), default="preferred")
  parser.add_argument("--tiles-per-core", type=int, default=1024)
  parser.add_argument(
    "--target-total-mib",
    type=float,
    default=None,
    help="override --tiles-per-core per count so each run streams about this many MiB per buffer",
  )
  parser.add_argument("--verify", action="store_true")
  args = parser.parse_args()
  if args.tiles_per_core <= 0:
    raise ValueError("--tiles-per-core must be positive")
  if args.target_total_mib is not None and args.target_total_mib <= 0:
    raise ValueError("--target-total-mib must be positive")

  lines = [
    "| bank mode | read endpoint | write endpoint | cores | tiles/core | total tiles | total MiB | us | effective GB/s |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  device = Device()
  try:
    all_cores, _use_grid = add1.select_cores(device, args.cores, add1.TARGET_CORE)
    if args.order == "raw":
      all_cores = raw_ordered_cores(device, all_cores)
    for count in args.counts:
      if count > len(all_cores):
        raise ValueError(f"requested {count} cores, device has {len(all_cores)} selected cores")
      cores = all_cores[:count]
      if args.target_total_mib is None:
        tiles_per_core = args.tiles_per_core
      else:
        target_bytes = int(args.target_total_mib * 1024 * 1024)
        tiles_per_core = max(1, target_bytes // (count * add1.TILE_BYTES))
      for bank_mode in args.bank_modes:
        us, gbps = run_case(
          device,
          cores=cores,
          tiles_per_core=tiles_per_core,
          bank_mode=bank_mode,
          read_endpoint_mode=args.read_endpoint_mode,
          write_endpoint_mode=args.write_endpoint_mode,
          verify=args.verify,
        )
        total_tiles = count * tiles_per_core
        total_mib = total_tiles * add1.TILE_BYTES / (1024 * 1024)
        lines.append(
          f"| {bank_mode} | {args.read_endpoint_mode} | {args.write_endpoint_mode} | {count} | {tiles_per_core} | {total_tiles} | "
          f"{total_mib:.1f} | {us:.1f} | {gbps:.1f} |"
        )
        print("\n".join(lines), flush=True)
  finally:
    device.close()


if __name__ == "__main__":
  main()
