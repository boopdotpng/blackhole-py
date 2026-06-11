#!/usr/bin/env python3
"""Accumulate multi-tile attention probabilities into grouped context rows.

This is the final standalone full-history attention building block after
multi-tile scores and global softmax probabilities:

  for each live 32-token history tile:
    ctx_partial_t = probs_t @ V_t
  ctx = sum_t ctx_partial_t

The proof intentionally keeps the boundary conservative: reuse the existing
weighted-V GEMV for each tile, then use validated two-source ADD programs to
accumulate the partial context tiles on device.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "microbenching"))
sys.path.insert(0, str(ROOT / "microbenching" / "tensix"))
sys.path.insert(0, str(ROOT / "examples"))

import harness  # noqa: E402,F401
import matmul_peak as mm  # noqa: E402
import microbench_residual_gemv as resgemv  # noqa: E402
import microbench_softmax as softmax  # noqa: E402
import numpy as np

from program import Dtype  # noqa: E402

TILE = 32
GROUP = 4
HEAD_DIM = 64
PAGE = Dtype.Float16_b.tile_size


def ref_probs(logits: np.ndarray) -> np.ndarray:
  logits = logits.astype(np.float32)
  logits = logits - logits.max(axis=(0, 2), keepdims=True)
  e = np.exp(logits)
  probs = e / e.sum(axis=(0, 2), keepdims=True)
  return softmax.from_bf16_bytes(softmax.to_bf16_bytes(probs), probs.shape)


def main() -> int:
  p = argparse.ArgumentParser(description="multi-tile weighted-V accumulation proof; needs device")
  p.add_argument("--tiles", type=int, default=2)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()
  if args.tiles < 1:
    raise ValueError("--tiles must be positive")

  rng = np.random.default_rng(313)
  logits = rng.uniform(-4.0, 4.0, size=(args.tiles, GROUP, TILE)).astype(np.float32)
  probs = ref_probs(logits)
  v_tiles = rng.uniform(-0.5, 0.5, size=(args.tiles, TILE, HEAD_DIM)).astype(np.float32)
  v_tiles = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(v_tiles), v_tiles.shape)

  ref_ctx = np.zeros((GROUP, HEAD_DIM), dtype=np.float32)
  for tile in range(args.tiles):
    ref_ctx += probs[tile] @ v_tiles[tile]

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    v_chunks = mm.plan_output_chunks(GROUP, TILE, HEAD_DIM, cores, nb)
    if len(v_chunks) != 1:
      raise ValueError("this proof expects one weighted-V GEMV chunk")
    v_chunk = v_chunks[0]
    VMp, VKp, VNp = mm.global_padded_shape(GROUP, TILE, HEAD_DIM, v_chunks)
    if VMp < GROUP or VKp != TILE or VNp != HEAD_DIM:
      raise RuntimeError(f"unexpected weighted-V shape {(VMp, VKp, VNp)}")
    ctx_pages = (VMp * VNp * Dtype.Float16_b.bpe) // PAGE
    if ctx_pages * PAGE != VMp * VNp * Dtype.Float16_b.bpe:
      raise RuntimeError("context buffer must be page-aligned")

    prob_bufs = []
    v_bufs = []
    ctx_bufs = []
    for tile in range(args.tiles):
      prob_tile = np.zeros((TILE, TILE), dtype=np.float32)
      prob_tile[:GROUP, :] = probs[tile]
      v_tile = np.zeros((VKp, VNp), dtype=np.float32)
      v_tile[:TILE, :HEAD_DIM] = v_tiles[tile]
      prob_bufs.append(device.alloc_write(mm.to_bf16_device_bytes(prob_tile),
                                          dtype=Dtype.Float16_b,
                                          shape=(TILE, TILE),
                                          name=f"attn_prob_tile_{tile}"))
      v_bufs.append(device.alloc_write(mm.to_bf16_device_bytes(v_tile),
                                       dtype=Dtype.Float16_b,
                                       shape=(VKp, VNp),
                                       name=f"attn_v_tile_{tile}"))
      ctx_buf = device.dram.alloc(ctx_pages, dtype=Dtype.Float16_b,
                                  shape=(VMp, VNp), name=f"attn_ctx_partial_{tile}")
      device.dram_write(ctx_buf, b"\0" * ctx_buf.size)
      ctx_bufs.append(ctx_buf)

    acc_bufs = [
      device.dram.alloc(ctx_pages, dtype=Dtype.Float16_b, shape=(VMp, VNp),
                        name=f"attn_ctx_acc_{i}")
      for i in range(max(1, args.tiles - 1))
    ]
    for buf in acc_bufs:
      device.dram_write(buf, b"\0" * buf.size)

    v_layout = mm.TensorLayout(
      m_tile_offset=v_chunk.m_tile_offset,
      n_tile_offset=v_chunk.n_tile_offset,
      a_row_stride=1,
      b_row_stride=VNp // TILE,
      c_row_stride=VNp // TILE,
    )
    v_programs = []
    for tile in range(args.tiles):
      prog = mm.build_program(
        v_chunk.plan, prob_bufs[tile].addr, v_bufs[tile].addr, ctx_bufs[tile].addr,
        nb, v_layout)
      prog.name = f"attn_multitile_weighted_v_t{tile}"
      v_programs.append(prog)

    add_programs = []
    final_buf = ctx_bufs[0]
    if args.tiles >= 2:
      prog = resgemv.build_two_source_binary(
        "add", ctx_bufs[0].addr, ctx_bufs[1].addr, acc_bufs[0].addr,
        nb, core=core, tiles=ctx_pages)
      prog.name = "attn_ctx_accumulate_t0_t1"
      add_programs.append(prog)
      final_buf = acc_bufs[0]
      for tile in range(2, args.tiles):
        dst = acc_bufs[tile - 1]
        prog = resgemv.build_two_source_binary(
          "add", final_buf.addr, ctx_bufs[tile].addr, dst.addr,
          nb, core=core, tiles=ctx_pages)
        prog.name = f"attn_ctx_accumulate_t{tile}"
        add_programs.append(prog)
        final_buf = dst

    programs = (*v_programs, *add_programs)
    times = []
    for _ in range(args.runs):
      for prog in programs:
        times.extend(device.run(prog))
    ctx_raw = device.dram_read(final_buf)

  full_ctx = mm.from_bf16_device_bytes(ctx_raw, (VMp, VNp))[:, :HEAD_DIM]
  ctx_rows = list(range(GROUP))
  ctx = full_ctx[ctx_rows, :HEAD_DIM]
  ctx_ok = bool(np.allclose(ctx, ref_ctx, atol=1.5e-1, rtol=1.5e-1))
  ok = ctx_ok

  print("attention multi-tile weighted-V accumulation proof")
  print(f"  tiles={args.tiles} rows={GROUP} runs={args.runs}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  weighted-V accumulated context: {'PASS' if ctx_ok else 'FAIL'}")
  if not ctx_ok:
    diff = np.abs(ctx - ref_ctx)
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    ctx max diff row={r} col={c} got={float(ctx[r, c]):.6g} ref={float(ref_ctx[r, c]):.6g}")
    for ref_row in range(GROUP):
      errs = [
        float(np.linalg.norm(full_ctx[row] - ref_ctx[ref_row]) / (np.linalg.norm(ref_ctx[ref_row]) + 1e-12))
        for row in range(VMp)
      ]
      best = int(np.argmin(errs))
      print(f"    ref ctx row {ref_row} best matches output row {best} rel_l2={errs[best]:.4f}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
