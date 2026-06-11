#!/usr/bin/env python3
"""Embedding gather into the two staged RMSNorm input layouts.

Device decode currently starts with a host embedding row, then host-side writes
materialize both layouts that DeviceNormGemv consumes:

  - x_row: one row-tiled M=1 GEMV input tile per 32 elements
  - x_rms: one SFPU 32-lane footprint tile per 32 elements

This proof stages the handoff on device:

  1. gather token id -> row-tiled GEMV/RMSNorm input layout
  2. convert row-tiled layout -> RMS SFPU footprint layout

Attention is still host-side in the integrated driver, but this removes the
token -> embedding -> norm-input host materialization shape.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "microbenching"))
sys.path.insert(0, str(ROOT / "microbenching" / "matmul"))
sys.path.insert(0, str(ROOT / "microbenching" / "tensix"))

import harness  # noqa: E402,F401
import numpy as np

from program import Dtype  # noqa: E402

import microbench_embedding_gather_tilized as gather_tilized  # noqa: E402
import microbench_swiglu_bridge as swiglu_bridge  # noqa: E402

TILE = 32
PAGE = Dtype.Float16_b.tile_size


def vector_to_footprint_tiles_u16(vec: np.ndarray) -> np.ndarray:
  tiles = np.zeros((vec.size // TILE, TILE, TILE), dtype=np.uint16)
  for tile in range(vec.size // TILE):
    for lane, value in enumerate(vec[tile * TILE:(tile + 1) * TILE]):
      row = lane // 8
      col = (lane & 7) * 2
      tiles[tile, row, col] = value
  return tiles


def main() -> int:
  p = argparse.ArgumentParser(description="embedding gather into DeviceNormGemv inputs; needs device")
  p.add_argument("--rows", type=int, default=4096, help="vocab rows in table")
  p.add_argument("--dim", type=int, default=2048, help="embedding width, bf16 elements")
  p.add_argument("--tokens", type=int, default=8)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()
  if args.dim % 1024 != 0:
    raise ValueError("dim must be a multiple of 1024 so rows align to DRAM pages")
  if args.dim % TILE != 0:
    raise ValueError("dim must be a multiple of 32")

  pages_per_row = args.dim * 2 // PAGE
  dim_tiles = args.dim // TILE
  rng = np.random.default_rng(113)
  table = rng.integers(0, 1 << 16, (args.rows, args.dim), dtype=np.uint16)
  ids = rng.integers(0, args.rows, args.tokens, dtype=np.uint32)
  ids[0], ids[-1] = 0, args.rows - 1

  idx_bytes = ids.tobytes()
  idx_pages = (len(idx_bytes) + PAGE - 1) // PAGE
  idx_bytes = idx_bytes.ljust(idx_pages * PAGE, b"\0")

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    table_buf = device.dram.alloc(table.nbytes // PAGE, dtype=Dtype.Float16_b, name="embed_table_rowmajor")
    device.dram_write(table_buf, table.tobytes())
    idx_buf = device.dram.alloc(idx_pages, dtype=Dtype.Float16_b, name="embed_idx")
    device.dram_write(idx_buf, idx_bytes)
    row_shape = (args.tokens * TILE, args.dim)
    row_buf = device.dram.alloc(args.tokens * dim_tiles, dtype=Dtype.Float16_b,
                                shape=row_shape, name="embed_x_row")
    rms_buf = device.dram.alloc(args.tokens * dim_tiles, dtype=Dtype.Float16_b,
                                shape=(args.tokens * dim_tiles, TILE, TILE),
                                name="embed_x_rms")
    device.dram_write(row_buf, b"\0" * row_buf.size)
    device.dram_write(rms_buf, b"\0" * rms_buf.size)
    gather_prog = gather_tilized.build_program(
        table_buf.addr, idx_buf.addr, row_buf.addr, args.tokens, nb,
        idx_pages, dim_tiles, pages_per_row, core=core)
    gather_prog.name = "embed_gather_norm_row"
    rms_prog = swiglu_bridge.build_convert_program(
        "row_to_fp", row_buf.addr, rms_buf.addr, nb, core=core,
        tiles=args.tokens * dim_tiles)
    rms_prog.name = "embed_gather_norm_row_to_fp"
    timings = []
    for _ in range(args.runs):
      device.dram_write(row_buf, b"\0" * row_buf.size)
      device.dram_write(rms_buf, b"\0" * rms_buf.size)
      for prog in (gather_prog, rms_prog):
        timings.extend(device.run(prog))
    row_raw = device.dram_read(row_buf)
    rms_raw = device.dram_read(rms_buf)

  row_got = np.frombuffer(row_raw, dtype=np.uint16).reshape(row_shape)
  row_ref = np.zeros(row_shape, dtype=np.uint16)
  row_ref[0::TILE, :] = table[ids]
  row_ok = bool(np.array_equal(row_got, row_ref))

  rms_ref = np.zeros((args.tokens * dim_tiles, TILE, TILE), dtype=np.uint16)
  for slot, token in enumerate(ids):
    rms_ref[slot * dim_tiles:(slot + 1) * dim_tiles] = vector_to_footprint_tiles_u16(table[token])
  rms_got = np.frombuffer(rms_raw, dtype=np.uint16).reshape(rms_ref.shape)
  rms_ok = bool(np.array_equal(rms_got, rms_ref))

  print("embedding gather into norm inputs")
  print(f"  rows={args.rows} dim={args.dim} tokens={args.tokens} runs={args.runs} dim_tiles={dim_tiles}")
  if timings:
    print(f"  launches={2 * args.runs} avg={sum(t['us'] for t in timings) / len(timings):.1f} us")
  print(f"  row layout: {'PASS' if row_ok else 'FAIL'}")
  print(f"  rms footprint layout: {'PASS' if rms_ok else 'FAIL'}")
  for label, got, ref in (("row", row_got, row_ref), ("rms", rms_got, rms_ref)):
    if not np.array_equal(got, ref):
      flat = np.flatnonzero(got.reshape(-1) != ref.reshape(-1))
      i = int(flat[0])
      print(f"    {label} first bad flat={i} got={int(got.reshape(-1)[i])} ref={int(ref.reshape(-1)[i])}")
      if label == "rms":
        got0 = got.reshape((-1, TILE, TILE))[i // (TILE * TILE)]
        ref0 = ref.reshape((-1, TILE, TILE))[i // (TILE * TILE)]
        print(f"    rms got row0 even cols={got0[0, :16:2].tolist()}")
        print(f"    rms ref row0 even cols={ref0[0, :16:2].tolist()}")
        print(f"    rms got row0 cols0..15={got0[0, :16].tolist()}")
        print(f"    rms ref row0 cols0..15={ref0[0, :16].tolist()}")
  print("PASS" if row_ok and rms_ok else "FAIL")
  return 0 if row_ok and rms_ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
