#!/usr/bin/env python3
"""One-head staged device attention from QKV C and live K/V caches.

This composes the previously isolated bridges:

  QKV C Q head -> Q RoPE -> score GEMV A
  live K cache -> K^T score GEMV B
  scores -> softmax
  live V cache -> weighted-V GEMV B
  probs @ V -> context head

It is intentionally one head and one sequence tile. The point is proving the
device-resident attention handoff chain before integrating multi-head/GQA into
``examples/llama3.py``.
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
sys.path.insert(0, str(ROOT / "examples"))

import harness  # noqa: E402,F401
import matmul_peak as mm  # noqa: E402
import microbench_attention_k_stage as kvstage  # noqa: E402
import microbench_attention_q_rope_stage as qrope  # noqa: E402
import microbench_rope_k_scatter as rope  # noqa: E402
import microbench_softmax as softmax  # noqa: E402
import numpy as np

from program import Dtype  # noqa: E402

TILE = 32
HEAD_DIM = 64
PAGE = Dtype.Float16_b.tile_size


def main() -> int:
  p = argparse.ArgumentParser(description="one-head staged device attention; needs device")
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--heads", type=int, default=32)
  p.add_argument("--kv-heads", type=int, default=8)
  p.add_argument("--q-head", type=int, default=7)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--seq", type=int, default=32)
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--verbose", action="store_true")
  args = p.parse_args()
  if args.heads * HEAD_DIM != args.dim:
    raise ValueError("heads * 64 must equal dim")
  if args.kv_heads * HEAD_DIM != args.kv_dim:
    raise ValueError("kv-heads * 64 must equal kv-dim")
  if not 0 <= args.q_head < args.heads:
    raise ValueError("--q-head must select one query head")
  if args.seq != TILE:
    raise ValueError("this first proof expects --seq 32")
  if args.max_seq < args.seq or args.max_seq % TILE:
    raise ValueError("--max-seq must be a multiple of 32 and >= seq")
  if args.pos >= args.max_seq:
    raise ValueError("--pos must be < --max-seq")
  kv_head = args.q_head // (args.heads // args.kv_heads)

  rng = np.random.default_rng(239)
  qkv_n = args.dim + 2 * args.kv_dim
  qkv_n_padded = ((qkv_n + TILE - 1) // TILE) * TILE
  qkv = rope.to_bf16(rng.uniform(-2.0, 2.0, size=qkv_n_padded).astype(np.float32))
  q = qkv[args.q_head * HEAD_DIM:(args.q_head + 1) * HEAD_DIM]
  cos_table = rope.to_bf16(rng.uniform(-1.0, 1.0, size=(args.max_seq, TILE)).astype(np.float32))
  sin_table = rope.to_bf16(rng.uniform(-1.0, 1.0, size=(args.max_seq, TILE)).astype(np.float32))
  cos = cos_table[args.pos]
  sin = sin_table[args.pos]
  q_rot = np.empty_like(q)
  q_rot[:32] = q[:32] * cos - q[32:] * sin
  q_rot[32:] = q[32:] * cos + q[:32] * sin
  q_rot = rope.to_bf16(q_rot)
  k_cache = rope.to_bf16(
      rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32))
  v_cache = rope.to_bf16(
      rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32))
  ref_scores = (q_rot.reshape(1, HEAD_DIM) @ k_cache[kv_head, :args.seq, :].T).reshape(-1)

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    chunks = mm.plan_output_chunks(1, HEAD_DIM, args.seq, cores, nb)
    if len(chunks) != 1:
      raise ValueError("this first proof expects one score GEMV chunk")
    chunk = chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(1, HEAD_DIM, args.seq, chunks)
    tiles = (Mp // TILE) * (Np // TILE)
    if Kp != HEAD_DIM:
      raise RuntimeError(f"unexpected K padding: Kp={Kp}")
    v_chunks = mm.plan_output_chunks(1, args.seq, HEAD_DIM, cores, nb)
    if len(v_chunks) != 1:
      raise ValueError("this first proof expects one weighted-V GEMV chunk")
    v_chunk = v_chunks[0]
    VMp, VKp, VNp = mm.global_padded_shape(1, args.seq, HEAD_DIM, v_chunks)
    if VMp != Mp or VKp > Np:
      raise ValueError(f"softmax output shape {(Mp, Np)} cannot feed V GEMV {(VMp, VKp)}")

    c = np.zeros((TILE, qkv_n_padded), dtype=np.float32)
    c[0, :] = qkv
    k_expected = np.zeros((Kp, Np), dtype=np.float32)
    k_expected[:HEAD_DIM, :args.seq] = k_cache[kv_head, :args.seq, :].T
    v_expected = np.zeros((VKp, VNp), dtype=np.float32)
    v_expected[:args.seq, :HEAD_DIM] = v_cache[kv_head, :args.seq, :]
    a_expected = np.zeros((Mp, Kp), dtype=np.float32)
    a_expected[0, :HEAD_DIM] = q_rot

    c_buf = device.alloc_write(mm.to_bf16_device_bytes(c), dtype=Dtype.Float16_b,
                               shape=c.shape, name="qkv_c")
    cos_buf = device.alloc_write(rope.to_bf16_bytes(qrope.row_tile_table(cos_table)),
                                 dtype=Dtype.Float16_b,
                                 shape=(args.max_seq, TILE, TILE), name="cos_rows")
    sin_buf = device.alloc_write(rope.to_bf16_bytes(qrope.row_tile_table(sin_table)),
                                 dtype=Dtype.Float16_b,
                                 shape=(args.max_seq, TILE, TILE), name="sin_rows")
    k_cache_buf = device.alloc_write(mm.to_bf16_device_bytes(k_cache), dtype=Dtype.Float16_b,
                                     shape=k_cache.shape, name="k_cache")
    v_cache_buf = device.alloc_write(mm.to_bf16_device_bytes(v_cache), dtype=Dtype.Float16_b,
                                     shape=v_cache.shape, name="v_cache")
    rope_src_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, shape=(1, TILE, TILE), name="q_rope_src")
    a_buf = device.dram.alloc((Mp // TILE) * (Kp // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Kp), name="attn_q_a")
    k_t_buf = device.dram.alloc((Kp * Np * 2) // PAGE, dtype=Dtype.Float16_b,
                                shape=(Kp, Np), name="attn_k_t")
    v_buf = device.dram.alloc((VKp * VNp * 2) // PAGE, dtype=Dtype.Float16_b,
                              shape=(VKp, VNp), name="attn_v")
    scores_buf = device.dram.alloc(tiles, dtype=Dtype.Float16_b, shape=(Mp, Np), name="attn_scores")
    probs_buf = device.dram.alloc(tiles, dtype=Dtype.Float16_b,
                                  shape=(tiles, TILE, TILE), name="attn_probs")
    ctx_buf = device.dram.alloc((VMp // TILE) * (VNp // TILE), dtype=Dtype.Float16_b,
                                shape=(VMp, VNp), name="attn_ctx")
    device.dram_write(rope_src_buf, b"\0" * rope_src_buf.size)
    device.dram_write(a_buf, b"\0" * a_buf.size)

    q_stage_prog = qrope.build_q_rope_src_stage_program(
      c_buf.addr, cos_buf.addr, sin_buf.addr, rope_src_buf.addr,
      args.q_head, args.pos, nb, core=core)
    q_rope_prog = qrope.build_q_rope_to_a_program(rope_src_buf.addr, a_buf.addr, nb, core=core)
    k_stage_prog = kvstage.build_stage_program(
      k_cache_buf.addr, k_t_buf.addr, kv_head, nb, core=core,
      seq=args.seq, max_seq=args.max_seq, n_cols=Np, dst_pages=(Kp * Np * 2) // PAGE)
    score_layout = mm.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    score_prog = mm.build_program(chunk.plan, a_buf.addr, k_t_buf.addr, scores_buf.addr, nb, score_layout)
    score_prog.name = "attn_full_score_gemv"
    softmax_prog = softmax.build_program(scores_buf.addr, probs_buf.addr, nb, core=core, tiles=tiles)
    softmax_prog.name = "attn_full_softmax"
    v_stage_prog = kvstage.build_v_stage_program(
      v_cache_buf.addr, v_buf.addr, kv_head, nb, core=core,
      seq=args.seq, max_seq=args.max_seq, n_cols=VNp, dst_pages=(VKp * VNp * 2) // PAGE)
    v_layout = mm.TensorLayout(
      m_tile_offset=v_chunk.m_tile_offset,
      n_tile_offset=v_chunk.n_tile_offset,
      a_row_stride=Np // TILE,
      b_row_stride=VNp // TILE,
      c_row_stride=VNp // TILE,
    )
    v_prog = mm.build_program(v_chunk.plan, probs_buf.addr, v_buf.addr, ctx_buf.addr, nb, v_layout)
    v_prog.name = "attn_full_weighted_v_gemv"
    programs = (q_stage_prog, q_rope_prog, k_stage_prog, score_prog, softmax_prog, v_stage_prog, v_prog)

    times = []
    for _ in range(args.runs):
      for prog in programs:
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        times.extend(device.run(prog))

    a_raw = device.dram_read(a_buf)
    k_raw = device.dram_read(k_t_buf)
    v_raw = device.dram_read(v_buf)
    scores_raw = device.dram_read(scores_buf)
    probs_raw = device.dram_read(probs_buf)
    ctx_raw = device.dram_read(ctx_buf)

  q_ok = bool(np.allclose(mm.from_bf16_device_bytes(a_raw, (Mp, Kp)), a_expected,
                          atol=5.0e-2, rtol=5.0e-2))
  k_ok = k_raw == mm.to_bf16_device_bytes(k_expected)
  v_ok = v_raw == mm.to_bf16_device_bytes(v_expected)
  score_matrix = mm.from_bf16_device_bytes(scores_raw, (Mp, Np))
  scores = score_matrix[0, :args.seq]
  score_ok = bool(np.allclose(scores, ref_scores, atol=1.0e-1, rtol=1.0e-1))
  ref_prob_tiles = softmax.ref_softmax(softmax.from_bf16_bytes(scores_raw, (tiles, TILE, TILE)))
  ref_probs = mm.from_bf16_device_bytes(softmax.to_bf16_bytes(ref_prob_tiles), (Mp, Np))[0, :args.seq]
  probs = mm.from_bf16_device_bytes(probs_raw, (Mp, Np))[0, :args.seq]
  prob_ok = bool(np.allclose(probs, ref_probs, atol=softmax.ATOL, rtol=softmax.RTOL))
  ref_ctx = (ref_probs.reshape(1, args.seq) @ v_cache[kv_head, :args.seq, :]).reshape(-1)
  ctx = mm.from_bf16_device_bytes(ctx_raw, (VMp, VNp))[0, :HEAD_DIM]
  ctx_ok = bool(np.allclose(ctx, ref_ctx, atol=1.0e-1, rtol=1.0e-1))
  ok = q_ok and k_ok and v_ok and score_ok and prob_ok and ctx_ok

  print("full staged one-head attention")
  print(f"  q_head={args.q_head} kv_head={kv_head} pos={args.pos} seq={args.seq} runs={args.runs}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  Q RoPE A: {'PASS' if q_ok else 'FAIL'}")
  print(f"  staged K^T: {'PASS' if k_ok else 'FAIL'}")
  print(f"  staged V: {'PASS' if v_ok else 'FAIL'}")
  print(f"  scores: {'PASS' if score_ok else 'FAIL'}")
  print(f"  softmax: {'PASS' if prob_ok else 'FAIL'}")
  print(f"  weighted V: {'PASS' if ctx_ok else 'FAIL'}")
  if not score_ok:
    diff = np.abs(scores - ref_scores)
    i = int(np.argmax(diff))
    print(f"    score max diff i={i} got={float(scores[i]):.6g} ref={float(ref_scores[i]):.6g}")
  if not ctx_ok:
    diff = np.abs(ctx - ref_ctx)
    i = int(np.argmax(diff))
    print(f"    ctx max diff i={i} got={float(ctx[i]):.6g} ref={float(ref_ctx[i]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
