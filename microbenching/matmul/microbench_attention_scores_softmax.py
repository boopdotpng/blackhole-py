#!/usr/bin/env python3
"""Device attention score + softmax + weighted-V proof.

This is the first attention-path bridge for Llama decode:

  q[1, head_dim] @ K^T[head_dim, seq] -> scores[1, seq]
  -> softmax(scores) -> probs[1, seq] @ V[seq, head_dim]

It uses the existing skinny GEMV path for scores and the validated 32x32
softmax composite for probabilities, then another skinny GEMV for the weighted
V sum. The live row-major KV-cache layout is not consumed yet; this proves the
attention math boundary on device before the next cache-layout staging step.
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
import microbench_softmax as softmax  # noqa: E402
import numpy as np

from program import Dtype  # noqa: E402

TILE = 32


def main() -> int:
  p = argparse.ArgumentParser(description="device attention scores + softmax; needs device")
  p.add_argument("--head-dim", type=int, default=64)
  p.add_argument("--seq", type=int, default=32)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--verbose", action="store_true")
  args = p.parse_args()
  if args.head_dim % TILE:
    raise ValueError("--head-dim must be a multiple of 32")
  if args.seq != TILE:
    raise ValueError("this first proof expects --seq 32; longer seq needs cross-tile softmax")

  rng = np.random.default_rng(211)
  q = rng.uniform(-0.5, 0.5, size=(1, args.head_dim)).astype(np.float32)
  k_cache = rng.uniform(-0.5, 0.5, size=(args.seq, args.head_dim)).astype(np.float32)
  v_cache = rng.uniform(-0.5, 0.5, size=(args.seq, args.head_dim)).astype(np.float32)
  q = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(q), q.shape)
  k_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(k_cache), k_cache.shape)
  v_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(v_cache), v_cache.shape)
  scale = np.float32(1.0 / np.sqrt(args.head_dim))
  # Fold attention's scale into the staged K^T input for this proof. Live-cache
  # integration still needs device-side staging of K rows into scaled scores.
  b = (k_cache.T * scale).copy()
  ref_scores = (q @ b).reshape(-1)

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    chunks = mm.plan_output_chunks(1, args.head_dim, args.seq, cores, nb)
    Mp, Kp, Np = mm.global_padded_shape(1, args.head_dim, args.seq, chunks)
    tiles = (Mp // TILE) * (Np // TILE)
    v_chunks = mm.plan_output_chunks(1, args.seq, args.head_dim, cores, nb)
    if len(chunks) != 1 or len(v_chunks) != 1:
      raise ValueError("this first proof expects one GEMV chunk for scores and V")
    VMp, VKp, VNp = mm.global_padded_shape(1, args.seq, args.head_dim, v_chunks)
    if VMp != Mp or VKp > Np:
      raise ValueError(f"softmax output shape {(Mp, Np)} cannot feed V GEMV {(VMp, VKp)}")

    a_padded = np.zeros((Mp, Kp), dtype=np.float32)
    b_padded = np.zeros((Kp, Np), dtype=np.float32)
    v_padded = np.zeros((VKp, VNp), dtype=np.float32)
    a_padded[:1, :args.head_dim] = q
    b_padded[:args.head_dim, :args.seq] = b
    v_padded[:args.seq, :args.head_dim] = v_cache

    a_buf = device.alloc_write(mm.to_bf16_device_bytes(a_padded), dtype=Dtype.Float16_b,
                               shape=(Mp, Kp), name="attn_q")
    b_buf = device.alloc_write(mm.to_bf16_device_bytes(b_padded), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="attn_k_t")
    v_buf = device.alloc_write(mm.to_bf16_device_bytes(v_padded), dtype=Dtype.Float16_b,
                               shape=(VKp, VNp), name="attn_v")
    scores_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b,
                                   shape=(Mp, Np), name="attn_scores")
    probs_buf = device.dram.alloc(tiles, dtype=Dtype.Float16_b,
                                  shape=(tiles, TILE, TILE), name="attn_probs")
    ctx_buf = device.dram.alloc((VMp // TILE) * (VNp // TILE), dtype=Dtype.Float16_b,
                                shape=(VMp, VNp), name="attn_ctx")

    layout_base = dict(a_row_stride=Kp // TILE, b_row_stride=Np // TILE, c_row_stride=Np // TILE)
    gemv_progs = []
    for i, chunk in enumerate(chunks):
      layout = mm.TensorLayout(
        m_tile_offset=chunk.m_tile_offset,
        n_tile_offset=chunk.n_tile_offset,
        **layout_base,
      )
      prog = mm.build_program(chunk.plan, a_buf.addr, b_buf.addr, scores_buf.addr, nb, layout)
      prog.name = "attn_score_gemv" if len(chunks) == 1 else f"attn_score_gemv_c{i}"
      gemv_progs.append(prog)
    softmax_prog = softmax.build_program(scores_buf.addr, probs_buf.addr, nb, core=core, tiles=tiles)
    softmax_prog.name = "attn_score_softmax"
    v_chunk = v_chunks[0]
    v_layout = mm.TensorLayout(
      m_tile_offset=v_chunk.m_tile_offset,
      n_tile_offset=v_chunk.n_tile_offset,
      # probs_buf is padded by the score GEMV/softmax shape, so its row stride
      # can be wider than the logical V-GEMV K dimension.
      a_row_stride=Np // TILE,
      b_row_stride=VNp // TILE,
      c_row_stride=VNp // TILE,
    )
    v_prog = mm.build_program(v_chunk.plan, probs_buf.addr, v_buf.addr, ctx_buf.addr, nb, v_layout)
    v_prog.name = "attn_weighted_v_gemv"

    times = []
    for _ in range(args.runs):
      for prog in (*gemv_progs, softmax_prog, v_prog):
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        times.extend(device.run(prog))

    scores_raw = device.dram_read(scores_buf)
    probs_raw = device.dram_read(probs_buf)
    ctx_raw = device.dram_read(ctx_buf)

  score_matrix = mm.from_bf16_device_bytes(scores_raw, (Mp, Np))
  prob_matrix = mm.from_bf16_device_bytes(probs_raw, (Mp, Np))
  ctx_matrix = mm.from_bf16_device_bytes(ctx_raw, (VMp, VNp))
  scores = score_matrix[0, :args.seq]
  probs = prob_matrix[0, :args.seq]
  ctx = ctx_matrix[0, :args.head_dim]
  ref_prob_tiles = softmax.ref_softmax(softmax.from_bf16_bytes(scores_raw, (tiles, TILE, TILE)))
  ref_unscaled_probs = mm.from_bf16_device_bytes(
      softmax.to_bf16_bytes(ref_prob_tiles), (Mp, Np))[0, :args.seq]
  ref_ctx = (ref_unscaled_probs.reshape(1, args.seq) @ v_cache).reshape(-1)
  score_ok = bool(np.allclose(scores, ref_scores, atol=1.0e-1, rtol=1.0e-1))
  prob_ok = bool(np.allclose(probs, ref_unscaled_probs, atol=softmax.ATOL, rtol=softmax.RTOL))
  ctx_ok = bool(np.allclose(ctx, ref_ctx, atol=1.0e-1, rtol=1.0e-1))
  ok = score_ok and prob_ok and ctx_ok

  print("attention score + softmax + weighted-V device proof")
  print(f"  head_dim={args.head_dim} seq={args.seq} runs={args.runs} tiles={tiles}")
  if times:
    print(f"  launches={(len(gemv_progs) + 2) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  scores: {'PASS' if score_ok else 'FAIL'}")
  print(f"  softmax(row0, scaled): {'PASS' if prob_ok else 'FAIL'}")
  print(f"  weighted V: {'PASS' if ctx_ok else 'FAIL'}")
  if not score_ok:
    diff = np.abs(scores - ref_scores)
    i = int(np.argmax(diff))
    print(f"    score max diff i={i} got={float(scores[i]):.6g} ref={float(ref_scores[i]):.6g}")
  if not prob_ok:
    diff = np.abs(probs - ref_unscaled_probs)
    i = int(np.argmax(diff))
    print(f"    prob max diff i={i} got={float(probs[i]):.6g} ref={float(ref_unscaled_probs[i]):.6g}")
  if not ctx_ok:
    diff = np.abs(ctx - ref_ctx)
    i = int(np.argmax(diff))
    print(f"    ctx max diff i={i} got={float(ctx[i]):.6g} ref={float(ref_ctx[i]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
