#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from microbenching.models.noc_scheduler import (  # noqa: E402
  Calibration,
  Endpoint,
  Transaction,
  _resource_cycles_summary,
  _resource_uses_summary,
  packet_resources,
  schedule,
)
from ttk.addrs import Dram  # noqa: E402
from ttk.blackhole_coords import live_raw_tensix_cores, tensix_coordinate_map  # noqa: E402


DEFAULT_ENABLED_TENSIX_COL = 0x3BF7
DEFAULT_TARGETS = {
  ("read", 0): 254.732,
  ("read", 1): 157.432,
  ("write", 0): 115.992,
  ("write", 1): 234.387,
}


def physical_worker_cores(enabled_tensix_col: int) -> list[tuple[int, int]]:
  return live_raw_tensix_cores(tensix_coordinate_map(enabled_tensix_col))


def route_order_for(op: str, noc: int) -> str:
  # Current best-fit dimension-order assumptions for DRAM spread streams.
  if op == "read":
    return "xy"
  if op == "write":
    return "yx"
  raise ValueError(f"unknown op {op!r}")


def make_dram_spread_transactions(
  *, op: str, noc: int, enabled_tensix_col: int, bytes_per_core: int, core_count: int,
) -> list[Transaction]:
  txns = []
  cores = physical_worker_cores(enabled_tensix_col)[:core_count]
  for idx, core in enumerate(cores):
    bank = idx % 7
    endpoint = idx % Dram.TILES_PER_BANK
    dram = Endpoint(
      "dram",
      (Dram.BANK_X[bank], Dram.BANK_TILE_YS[bank][endpoint]),
      bank=bank,
      endpoint=endpoint,
    )
    l1 = Endpoint("l1", core, label=f"c{core[0]},{core[1]}")
    txns.append(Transaction(
      name=f"{op}{idx}",
      op=op,
      noc=noc,
      initiator=l1,
      target=dram,
      bytes=bytes_per_core,
      packet_bytes=Calibration().max_packet_bytes,
      route_order=route_order_for(op, noc),
    ))
  return txns


def fabric_key(op: str, noc: int) -> str:
  return f"dram_{op}_noc{noc}_bpc"


def with_fabric_cap(cal: Calibration, *, op: str, noc: int, cap: float) -> Calibration:
  return replace(cal, **{fabric_key(op, noc): cap})


def effective_bpc(txns: list[Transaction], cal: Calibration) -> float:
  est = schedule(txns, cal, record_packets=False)
  total_bytes = sum(txn.bytes for txn in txns)
  return total_bytes / est.cycles if est.cycles > 0 else 0.0


def analytic_effective_bpc(txns: list[Transaction], cal: Calibration) -> float:
  busy: dict[str, float] = defaultdict(float)
  tail_cycles = 0.0
  for txn in txns:
    packet_bytes = txn.packet_bytes or cal.max_packet_bytes
    full_packets, remainder = divmod(txn.bytes, packet_bytes)
    sizes: list[tuple[int, int]] = []
    if full_packets:
      sizes.append((packet_bytes, full_packets))
    if remainder:
      sizes.append((remainder, 1))
    for n, repeat in sizes:
      resources, _src, _dst, _hops = packet_resources(txn, n, cal)
      for name, cycles in _resource_cycles_summary(resources).items():
        busy[name] += cycles * repeat
      for uses in _resource_uses_summary(resources).values():
        for use in uses:
          tail_cycles = max(tail_cycles, use["offset"] + use["cycles"])
  cycles = max(busy.values(), default=0.0) + cal.packet_base_latency_cycles + tail_cycles
  total_bytes = sum(txn.bytes for txn in txns)
  return total_bytes / cycles if cycles > 0 else 0.0


def fit_cap(
  txns: list[Transaction], *, op: str, noc: int, target_bpc: float, cal: Calibration,
  iterations: int, fast: bool,
) -> tuple[float, float]:
  estimator = analytic_effective_bpc if fast else effective_bpc
  lo, hi = 1.0, 2000.0
  for _ in range(iterations):
    mid = (lo + hi) / 2.0
    got = estimator(txns, with_fabric_cap(cal, op=op, noc=noc, cap=mid))
    if got < target_bpc:
      lo = mid
    else:
      hi = mid
  cap = (lo + hi) / 2.0
  got = estimator(txns, with_fabric_cap(cal, op=op, noc=noc, cap=cap))
  return cap, got


def parse_cases(text: str) -> list[tuple[str, int]]:
  out = []
  for item in text.split(","):
    item = item.strip()
    if not item:
      continue
    try:
      op, noc_text = item.split(":")
      noc = int(noc_text)
    except ValueError as exc:
      raise argparse.ArgumentTypeError("cases must look like read:0,write:1") from exc
    if op not in ("read", "write") or noc not in (0, 1):
      raise argparse.ArgumentTypeError("cases must use op read/write and noc 0/1")
    out.append((op, noc))
  if not out:
    raise argparse.ArgumentTypeError("empty case list")
  return out


def main():
  parser = argparse.ArgumentParser(description="Fit NoC scheduler DRAM fabric caps against aggregate spread targets.")
  parser.add_argument("--enabled-tensix-col", type=lambda s: int(s, 0), default=DEFAULT_ENABLED_TENSIX_COL)
  parser.add_argument("--bytes-per-core", type=int, default=256 * 1024)
  parser.add_argument("--core-count", type=int, default=118)
  parser.add_argument("--iterations", type=int, default=12)
  parser.add_argument("--cases", type=parse_cases, default=parse_cases("read:0,read:1,write:0,write:1"))
  parser.add_argument("--fast-analytic", action="store_true", help="use resource-busy approximation instead of exact packet scheduling")
  args = parser.parse_args()

  if args.bytes_per_core <= 0 or args.bytes_per_core % Calibration().max_packet_bytes:
    raise ValueError("--bytes-per-core must be a positive multiple of 16 KiB")
  if args.core_count <= 0:
    raise ValueError("--core-count must be positive")
  if args.iterations <= 0:
    raise ValueError("--iterations must be positive")

  mode = "analytic" if args.fast_analytic else "exact"
  print("| op | noc | mode | target B/cyc | fitted cap B/cyc | model B/cyc | model GB/s | bytes/core | cores |")
  print("|---|---:|---|---:|---:|---:|---:|---:|---:|")
  base = Calibration()
  for op, noc in args.cases:
    target = DEFAULT_TARGETS[(op, noc)]
    txns = make_dram_spread_transactions(
      op=op,
      noc=noc,
      enabled_tensix_col=args.enabled_tensix_col,
      bytes_per_core=args.bytes_per_core,
      core_count=args.core_count,
    )
    cap, got = fit_cap(
      txns,
      op=op,
      noc=noc,
      target_bpc=target,
      cal=base,
      iterations=args.iterations,
      fast=args.fast_analytic,
    )
    print(f"| {op} | {noc} | {mode} | {target:.3f} | {cap:.3f} | {got:.3f} | {got * base.clock_mhz / 1000.0:.1f} | {args.bytes_per_core} | {len(txns)} |")


if __name__ == "__main__":
  main()
