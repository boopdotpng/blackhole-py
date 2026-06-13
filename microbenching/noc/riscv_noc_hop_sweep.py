#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
import riscv_noc_bench as nocbench
from device import Device
from ttk.addrs import Core
from ttk.blackhole_coords import (
  GRID_H, GRID_W, TensixCoordinateMap, raw_coord_for_noc, tensix_coordinate_map,
  translated_tensix_to_raw_noc0,
)

ENABLED_TENSIX_COL_TAG = 34


@dataclass(frozen=True)
class Route:
  raw0_source: Core
  raw0_peer: Core
  raw_source: Core
  raw_peer: Core
  hops: int
  x_hops: int
  y_hops: int
  wraps: int


@dataclass(frozen=True)
class HopRun:
  noc: int
  source: Core
  peer: Core
  route: Route
  records: list[nocbench.Record]


def parse_nocs(text: str) -> tuple[int, ...]:
  nocs = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  if not nocs or any(noc not in (0, 1) for noc in nocs):
    raise argparse.ArgumentTypeError("expected comma-separated NoC ids from {0,1}")
  return nocs


def peer_specs_for_noc(noc: int) -> tuple[nocbench.BenchSpec, ...]:
  specs = [nocbench.BenchSpec("empty", 0, nocbench.OP_EMPTY, 0, 0)]
  specs.extend(spec for spec in nocbench.make_specs("peer") if spec.op != nocbench.OP_EMPTY and spec.noc == noc)
  return tuple(specs)


def rows_by_y(cores: list[Core]) -> dict[int, list[int]]:
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  return {y: sorted(xs) for y, xs in rows.items()}


def choose_row(cores: list[Core], requested_row: int | None) -> tuple[int, list[int]]:
  rows = rows_by_y(cores)
  if requested_row is not None:
    xs = rows.get(requested_row)
    if xs is None:
      raise ValueError(f"no program cores found on logical row {requested_row}")
    if len(xs) < 2:
      raise ValueError(f"logical row {requested_row} has fewer than two program cores")
    return requested_row, xs
  candidates = [(len(xs), -y, y, xs) for y, xs in rows.items() if len(xs) >= 2]
  if not candidates:
    raise ValueError("hop sweep needs at least one logical row with two program cores")
  _, _, y, xs = max(candidates)
  return y, xs


def route_for_pair(source: Core, peer: Core, *, noc: int, cmap: TensixCoordinateMap) -> Route:
  raw0_source = translated_tensix_to_raw_noc0(source, cmap)
  raw0_peer = translated_tensix_to_raw_noc0(peer, cmap)
  raw_source = raw_coord_for_noc(raw0_source, noc)
  raw_peer = raw_coord_for_noc(raw0_peer, noc)
  x_hops = (raw_peer[0] - raw_source[0]) % GRID_W
  y_hops = (raw_peer[1] - raw_source[1]) % GRID_H
  wraps = int(raw_peer[0] < raw_source[0] and x_hops != 0) + int(raw_peer[1] < raw_source[1] and y_hops != 0)
  return Route(
    raw0_source=raw0_source,
    raw0_peer=raw0_peer,
    raw_source=raw_source,
    raw_peer=raw_peer,
    hops=x_hops + y_hops,
    x_hops=x_hops,
    y_hops=y_hops,
    wraps=wraps,
  )


def read_tensix_coordinate_map(device: Device) -> TensixCoordinateMap:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  return tensix_coordinate_map(enabled)


def build_pairs(
  cores: list[Core], *,
  noc: int,
  row: int | None,
  source: Core | None,
  max_hops: int | None,
  cmap: TensixCoordinateMap,
) -> list[tuple[Core, Core, Route]]:
  if source is not None:
    if source not in set(cores):
      raise ValueError(f"--core {source[0]},{source[1]} is not a program core")
    y = source[1]
    xs = rows_by_y(cores).get(y, [])
  else:
    y, xs = choose_row(cores, row)
    source = (xs[0], y) if noc == 0 else (xs[-1], y)

  sx, sy = source
  if noc == 0:
    peers = [(x, sy) for x in xs if x > sx]
  else:
    peers = [(x, sy) for x in reversed(xs) if x < sx]
  pairs = [(source, peer, route_for_pair(source, peer, noc=noc, cmap=cmap)) for peer in peers]
  if max_hops is not None:
    pairs = [pair for pair in pairs if pair[2].hops <= max_hops]
  if not pairs:
    direction = "right" if noc == 0 else "left"
    raise ValueError(f"NoC{noc} sweep from {source} has no same-row peers to the {direction} within hop filter")
  return pairs


def adjusted_by_name(records: list[nocbench.Record]) -> dict[str, float]:
  empty = next(record for record in records if record.op == nocbench.OP_EMPTY)
  empty_cpi = empty.cycles / empty.iterations
  adjusted = {}
  for record in records:
    if record.ops_per_iter:
      adjusted[record.name] = (record.cycles - empty_cpi * record.iterations) / (record.iterations * record.ops_per_iter)
  return adjusted


def format_summary(runs: list[HopRun]) -> str:
  lines = [
    "| noc | source | peer | raw noc0 route | raw noc route | hops | x | y | wraps | read4 cmd | read4 flush | read64 flush | read256 flush | read1024 flush | write4 cmd | write4 barrier | write64 barrier | write256 barrier | write1024 barrier |",
    "|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for run in runs:
    adj = adjusted_by_name(run.records)
    prefix = f"peer_noc{run.noc}"
    def v(suffix: str) -> str:
      return f"{adj[f'{prefix}_{suffix}']:.3f}"
    route = run.route
    lines.append(
      f"| {run.noc} | `{run.source[0]},{run.source[1]}` | `{run.peer[0]},{run.peer[1]}` | "
      f"`{route.raw0_source[0]},{route.raw0_source[1]}->{route.raw0_peer[0]},{route.raw0_peer[1]}` | "
      f"`{route.raw_source[0]},{route.raw_source[1]}->{route.raw_peer[0]},{route.raw_peer[1]}` | "
      f"{route.hops} | {route.x_hops} | {route.y_hops} | {route.wraps} | "
      f"{v('read_4_cmd')} | {v('read_4_flush')} | {v('read_64_flush')} | {v('read_256_flush')} | {v('read_1024_flush')} | "
      f"{v('write_4_cmd')} | {v('write_4_barrier')} | {v('write_64_barrier')} | {v('write_256_barrier')} | {v('write_1024_barrier')} |"
    )
  return "\n".join(lines)


def append_report(path: Path, *, iterations: int, runs: list[HopRun]):
  harness.append_report(path, None, [
    f"Iterations per test: `{iterations}`",
    "Traffic: same-row peer-tile L1 unicast only; no DRAM writes and no multicast",
    "Direction policy: NoC0 sweeps translated peers to the right of the source; NoC1 sweeps translated peers to the left",
    "Hop metadata: translated worker coordinates are decoded through the firmware harvesting map before raw NoC hops/wraps are computed",
  ], format_summary(runs))


def main():
  parser = argparse.ArgumentParser(description="Sweep same-row peer L1 NoC latency by decoded raw NoC hop distance.")
  parser.add_argument("--nocs", type=parse_nocs, default=(0, 1), help="comma-separated NoC ids to sweep, default: 0,1")
  parser.add_argument("--row", type=int, default=None, help="translated row to sweep; default: row with most program cores")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="explicit source core X,Y")
  parser.add_argument("--max-hops", type=int, default=None, help="maximum decoded raw NoC hop distance to include")
  parser.add_argument("--iters", type=int, default=100, help="iterations per timed loop")
  parser.add_argument("--no-report", action="store_true", help="do not append results to docs/noc-hop-sweep.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-hop-sweep.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  if args.max_hops is not None and args.max_hops <= 0:
    raise ValueError("--max-hops must be positive")

  runs: list[HopRun] = []
  with harness.open_device() as device:
    cmap = read_tensix_coordinate_map(device)
    for noc in args.nocs:
      specs = peer_specs_for_noc(noc)
      for source, peer, route in build_pairs(
        device.cores,
        noc=noc,
        row=args.row,
        source=args.core,
        max_hops=args.max_hops,
        cmap=cmap,
      ):
        nocbench.clear_ranges(device, [source, peer], specs)
        device.run(nocbench.build_program(args.iters, specs, source_core=source, peer_core=peer))
        records = nocbench.parse_results(nocbench.read_results(device, source, specs), specs)
        runs.append(HopRun(noc=noc, source=source, peer=peer, route=route, records=records))

  print(format_summary(runs))
  if not args.no_report:
    append_report(args.report, iterations=args.iters, runs=runs)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
