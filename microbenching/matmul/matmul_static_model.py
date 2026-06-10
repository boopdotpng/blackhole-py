#!/usr/bin/env python3
from __future__ import annotations

import sys as _bs_sys
from pathlib import Path as _bs_Path
_bs_sys.path.insert(0, str(_bs_Path(__file__).resolve().parents[1]))
import _bench_path  # noqa: F401
import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import matmul_peak as base
import matmul_peak_drisc as drisc

from pcie import P100_TENSIX_X


AICLK_MHZ = 1350.0
TILE_BYTES = base.TILE_BYTES

# Hardware measurements from docs/*.md. These are intentionally conservative
# component models, not fitted end-to-end matmul numbers.
DRISC_DMA_GBPS = 59.6
PEER_L1_STREAM_BPC = 64.0
DRAM_WRITE_GBPS = 245.7

# Fitted from the unperturbed MATMUL_PROFILE=1 DRISC 5000^3 runs:
# trisc2 max ~1182.4 us, 27*8*8 subblocks/core.
TRISC_CYCLES_PER_SUBBLOCK = 924.0
OUTPUT_TAIL_US = 60.0


def p100_fast_cores() -> list[tuple[int, int]]:
  cores = [(x, y) for x in P100_TENSIX_X for y in range(2, 12)]
  return [core for core in cores if core not in {(P100_TENSIX_X[-1], 2), (P100_TENSIX_X[-1], 3)}]


def us_from_gbps(byte_count: int, gbps: float) -> float:
  return byte_count / (gbps * 1000.0)


def us_from_bpc(byte_count: int, bpc: float, aiclk_mhz: float) -> float:
  return byte_count / (bpc * aiclk_mhz)


def fmt_mib(x: int) -> str:
  return f"{x / (1 << 20):.2f} MiB"


def print_model(args) -> None:
  cores = p100_fast_cores()
  if args.drisc:
    plan = drisc.plan_matmul_drisc(args.M, args.K, args.N, cores, args.max_feeders)
    name = "drisc"
  else:
    plan = base.plan_matmul(args.M, args.K, args.N, cores)
    name = "worker"

  subblocks_per_core = plan.num_blocks * plan.in0_num_subblocks * plan.in1_num_subblocks
  math_mops_per_subblock = plan.in0_block_w * plan.out_subblock_num_tiles
  math_mops_per_core = subblocks_per_core * math_mops_per_subblock
  pack_tiles_per_core = subblocks_per_core * plan.out_subblock_num_tiles
  final_output_tiles_per_core = plan.out_block_num_tiles

  a_bytes = plan.num_rows * plan.in0_block_num_tiles * plan.num_blocks * TILE_BYTES
  b_bytes = plan.num_cols * plan.in1_block_num_tiles * plan.num_blocks * TILE_BYTES
  a_mcast_bytes = a_bytes if plan.num_cols > 1 else 0
  b_mcast_bytes = b_bytes if plan.num_rows > 1 else 0
  c_bytes = plan.mt * plan.nt * TILE_BYTES

  if args.drisc:
    split_noc0 = a_bytes + a_mcast_bytes
    split_noc1 = b_bytes + b_mcast_bytes + c_bytes
    balanced_noc0 = a_bytes + b_bytes + a_mcast_bytes
    balanced_noc1 = b_mcast_bytes + c_bytes
  else:
    split_noc0 = a_bytes + a_mcast_bytes
    split_noc1 = b_bytes + b_mcast_bytes + c_bytes
    balanced_noc0 = split_noc0
    balanced_noc1 = split_noc1

  per_a_feeder = plan.in0_block_num_tiles * plan.num_blocks * TILE_BYTES
  per_b_feeder = plan.in1_block_num_tiles * plan.num_blocks * TILE_BYTES
  raw_a_dma_us = us_from_gbps(per_a_feeder, args.drisc_dma_gbps)
  raw_b_dma_us = us_from_gbps(per_b_feeder, args.drisc_dma_gbps)
  raw_a_stage_us = us_from_bpc(per_a_feeder, args.peer_l1_stream_bpc, args.aiclk_mhz)
  raw_b_stage_us = us_from_bpc(per_b_feeder, args.peer_l1_stream_bpc, args.aiclk_mhz)
  raw_c_write_us = us_from_gbps(c_bytes, args.dram_write_gbps)

  trisc_us = subblocks_per_core * args.trisc_cycles_per_subblock / args.aiclk_mhz
  est_total_us = trisc_us + args.output_tail_us

  print(f"Matmul static model ({name})")
  print(f"  shape: M={args.M} N={args.N} K={args.K}")
  print(
    f"  plan: grid={plan.num_rows}x{plan.num_cols} cores={plan.active_core_count} "
    f"Mt/Kt/Nt={plan.mt}/{plan.kt}/{plan.nt} per_core={plan.per_core_m}x{plan.per_core_n} "
    f"bw={plan.in0_block_w} blocks={plan.num_blocks}"
  )
  print(
    f"  per-core dynamic: subblocks={subblocks_per_core:,} math_mops={math_mops_per_core:,} "
    f"pack_tiles={pack_tiles_per_core:,} final_output_tiles={final_output_tiles_per_core:,}"
  )
  print(
    f"  partial-pack multiplier: {pack_tiles_per_core / max(1, final_output_tiles_per_core):.1f}x "
    f"packed tiles per final output tile"
  )
  print("  traffic:")
  print(f"    A feed={fmt_mib(a_bytes)} B feed={fmt_mib(b_bytes)} A mcast={fmt_mib(a_mcast_bytes)} B mcast={fmt_mib(b_mcast_bytes)} C out={fmt_mib(c_bytes)}")
  print(f"    split NoC bytes:    NoC0={fmt_mib(split_noc0)} NoC1={fmt_mib(split_noc1)}")
  if args.drisc:
    print(f"    balanced NoC bytes: NoC0={fmt_mib(balanced_noc0)} NoC1={fmt_mib(balanced_noc1)}")
  print("  microbench lower bounds:")
  print(f"    per-A-feeder DRISC DMA @ {args.drisc_dma_gbps:g} GB/s: {raw_a_dma_us:.1f} us")
  print(f"    per-B-feeder DRISC DMA @ {args.drisc_dma_gbps:g} GB/s: {raw_b_dma_us:.1f} us")
  print(f"    per-A-feeder L1 stream @ {args.peer_l1_stream_bpc:g} B/cyc: {raw_a_stage_us:.1f} us")
  print(f"    per-B-feeder L1 stream @ {args.peer_l1_stream_bpc:g} B/cyc: {raw_b_stage_us:.1f} us")
  print(f"    aggregate C write @ {args.dram_write_gbps:g} GB/s: {raw_c_write_us:.1f} us")
  print("  calibrated backend:")
  print(f"    TRISC subblock cost={args.trisc_cycles_per_subblock:.1f} cyc -> {trisc_us:.1f} us")
  print(f"    + output tail estimate={args.output_tail_us:.1f} us -> total {est_total_us:.1f} us")


def main() -> None:
  parser = argparse.ArgumentParser(description="Static matmul model using current plan counts and microbench constants.")
  parser.add_argument("M", type=int, nargs="?", default=5000)
  parser.add_argument("N", type=int, nargs="?", default=5000)
  parser.add_argument("K", type=int, nargs="?", default=5000)
  parser.add_argument("--drisc", action="store_true", help="model examples/matmul_peak_drisc.py planner")
  parser.add_argument("--max-feeders", type=int, default=20)
  parser.add_argument("--aiclk-mhz", type=float, default=AICLK_MHZ)
  parser.add_argument("--drisc-dma-gbps", type=float, default=DRISC_DMA_GBPS)
  parser.add_argument("--peer-l1-stream-bpc", type=float, default=PEER_L1_STREAM_BPC)
  parser.add_argument("--dram-write-gbps", type=float, default=DRAM_WRITE_GBPS)
  parser.add_argument("--trisc-cycles-per-subblock", type=float, default=TRISC_CYCLES_PER_SUBBLOCK)
  parser.add_argument("--output-tail-us", type=float, default=OUTPUT_TAIL_US)
  args = parser.parse_args()
  print_model(args)


if __name__ == "__main__":
  main()
