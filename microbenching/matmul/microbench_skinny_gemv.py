#!/usr/bin/env python3
"""Skinny GEMV (M=1) microbench — the llama batch-1 decode regime.

Every decode-loop projection is x[1,K] @ W[K,N]: each weight byte is read from
DRAM once, used for one MAC, discarded (~1 FLOP/byte bf16). The metric here is
NOT TFLOPs but % of DRAM bandwidth — time/token ~= weight bytes / GB/s.

Reuses matmul_peak's planner/dataflow at M=1 (host pads x to one 32-row tile).
Weight traffic is already minimal there: NCRISC senders read each B tile from
GDDR exactly once per column and mcast down, so padded-M rows cost no extra
DRAM reads.

Shapes are the Llama 3.2 1B projections (dim=2048, kv 512, ffn 8192,
vocab 128256). --runs N timed launches per shape; result includes a projected
decode tok/s from total model bytes / measured GB/s.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Fast dispatch by default: device.run timings (this bench's metric) need the
# CQ path; harness would default TT_USB=1. Env still wins.
os.environ.setdefault("TT_USB", "0")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402,F401  (path bootstrap)
import numpy as np

import matmul_peak as base
from matmul_peak import TILE, TensorLayout, tflops
from program import Dtype

# Llama 3.2 1B decode projections (per token, M=1).
SHAPES = (
  ("wqkv_q", 2048, 2048),    # Wq
  ("wqkv_kv", 2048, 512),    # Wk / Wv (GQA)
  ("ffn_gate", 2048, 8192),  # Wgate / Wup
  ("ffn_down", 8192, 2048),  # Wdown
  ("logits", 2048, 128256),  # tied-embedding head
)
DRAM_PEAK_GBPS = 448.0       # GDDR6 theoretical (8 ch)
DRAM_MEASURED_GBPS = 305.0   # best measured worker-NoC roof (microbenching/todo.md)
MODEL_GB = 2.47              # ~1.24B params, bf16


def run_gemv(device, K: int, N: int, runs: int, grid_rows: int = 1):
  M = 1
  num_banks = len(device.dram.bank_tiles)
  # M=1 only needs one row of cores (pcm is already padded to 2 tiles); more
  # rows just write padded output rows back to DRAM, polluting the BW metric.
  ys = sorted({y for _, y in device.cores})[:grid_rows]
  cores = [c for c in device.cores if c[1] in ys]
  chunks = base.plan_output_chunks(M, K, N, cores, num_banks)
  Mp, Kp, Np = base.global_padded_shape(M, K, N, chunks)

  a_ref, b_ref = base.make_inputs(M, K, N)
  a_padded = np.zeros((Mp, Kp), dtype=np.float32)
  b_padded = np.zeros((Kp, Np), dtype=np.float32)
  a_padded[:M, :K] = a_ref
  b_padded[:K, :N] = b_ref

  a_buf = device.alloc_write(base.to_bf16_device_bytes(a_padded), dtype=Dtype.Float16_b, shape=(Mp, Kp), name="x")
  b_buf = device.alloc_write(base.to_bf16_device_bytes(b_padded), dtype=Dtype.Float16_b, shape=(Kp, Np), name="W")
  c_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b, shape=(Mp, Np), name="out")

  layout_base = dict(a_row_stride=Kp // TILE, b_row_stride=Np // TILE, c_row_stride=Np // TILE)
  run_times_us = []
  for _run in range(runs):
    run_timings = []
    for i, chunk in enumerate(chunks):
      if i and not device.fast_dispatch:
        device._upload_firmware()
      layout = TensorLayout(m_tile_offset=chunk.m_tile_offset, n_tile_offset=chunk.n_tile_offset, **layout_base)
      prog = base.build_program(chunk.plan, a_buf.addr, b_buf.addr, c_buf.addr, num_banks, layout)
      prog.name = f"gemv_K{K}_N{N}" if len(chunks) == 1 else f"gemv_K{K}_N{N}_chunk{i}"
      run_timings.extend(device.run(prog))
    run_times_us.append(sum(t["us"] for t in run_timings))

  c_raw = device.dram_read(c_buf)
  pcc, rel_l2 = base.validate(a_ref, b_ref, c_raw, M, N, Mp, Np)
  avg_us = sum(run_times_us) / len(run_times_us)
  return avg_us, Kp, Np, len(chunks), pcc, rel_l2


def main() -> int:
  parser = argparse.ArgumentParser(description="skinny GEMV (M=1) DRAM-bandwidth microbench; needs device")
  parser.add_argument("--runs", type=int, default=5)
  parser.add_argument("--rows", type=int, default=1, help="core grid rows (1 = pure GEMV regime)")
  parser.add_argument("--shapes", default="", help="comma-separated subset of shape names")
  args = parser.parse_args()
  pick = set(args.shapes.split(",")) if args.shapes else None
  shapes = [s for s in SHAPES if pick is None or s[0] in pick]

  ok = True
  rows = []
  # Fresh Device per shape: back-to-back programs with different CB layouts in
  # one session corrupt outputs and wedge the CQ (seen 2026-06-09).
  for name, K, N in shapes:
    with harness.open_device() as device:
      try:
        avg_us, Kp, Np, nchunks, pcc, rel_l2 = run_gemv(device, K, N, args.runs, args.rows)
      except AssertionError as e:
        print(f"  {name}: FAIL {e}")
        ok = False
        continue
      gb = Kp * Np * 2 / 1e9          # actual weight DRAM traffic (padded)
      gbs = gb * 1e6 / avg_us
      rows.append((name, K, N, nchunks, avg_us, gbs, pcc, rel_l2))

  print("skinny GEMV microbench (M=1, bf16 weights)")
  print(f"  runs={args.runs}  DRAM peak={DRAM_PEAK_GBPS:.0f} GB/s theoretical / {DRAM_MEASURED_GBPS:.0f} measured roof")
  print("  shape          K      N  chunks    us    GB/s  %theory  %meas  GFLOP/s  pcc")
  for name, K, N, nchunks, avg_us, gbs, pcc, rel_l2 in rows:
    print(
      f"  {name:<12}{K:>6}{N:>7}{nchunks:>6}{avg_us:>8.1f}{gbs:>8.1f}"
      f"{100 * gbs / DRAM_PEAK_GBPS:>8.1f}{100 * gbs / DRAM_MEASURED_GBPS:>7.1f}"
      f"{tflops(1, N, K, avg_us) * 1000:>9.1f}  {pcc:.4f}"
    )
  if rows:
    tot_gb = sum(K * N * 2 / 1e9 for _, K, N, *_ in rows)
    tot_us = sum(r[4] for r in rows)
    blend = tot_gb * 1e6 / tot_us
    print(f"  blended: {blend:.1f} GB/s -> projected decode ~{blend / MODEL_GB:.0f} tok/s ({MODEL_GB} GB bf16 model)")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
