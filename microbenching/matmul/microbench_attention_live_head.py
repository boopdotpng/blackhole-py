#!/usr/bin/env python3
"""Compose the live-cache one-head attention decode path.

This proof wires the Q-side and KV-side bridges together without pretending
attention has to be one program:

  QKV C row -> Q RoPE -> score GEMV A
  live K cache -> K^T score GEMV B
  score GEMV -> causal masked softmax
  live V cache -> weighted-V GEMV B
  probs @ V -> context head directly in the Wo GEMV input row

It is the closest pre-driver attention contract: all Q/K/V inputs are consumed
from device-resident decode layouts, and only validation reads back to host.
Scores are intentionally unscaled here; scale placement remains a separate
correctness/stability step.
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
import microbench_attention_k_stage as kvstage  # noqa: E402
import microbench_attention_q_rope_stage as qrope  # noqa: E402
import microbench_rope_k_scatter as rope  # noqa: E402
import microbench_softmax as softmax  # noqa: E402
import numpy as np

from dsl import a0, a1, a2, a5, s8, s11, t0, t1, t2, t6  # noqa: E402
from program import Dtype  # noqa: E402
from ttk.mailbox import NcriscMailbox as NM  # noqa: E402

TILE = 32
HEAD_DIM = 64
PAGE = Dtype.Float16_b.tile_size
ROW_HALF_BYTES = 16 * 2
TILE_ROW0_COL16_OFF = 16 * 16 * 2


def make_wo_input_hook(*, q_head: int):
  """Copy only weighted-V row 0 into the full-width, prezeroed Wo input."""
  head_tile = q_head * (HEAD_DIM // TILE)

  def hook(fw, plan, *, tile_page, l1_tile):
    del plan
    done = fw._new_label("wo_input_hook_done")
    fw.li(t0, HEAD_DIM // TILE)
    fw.bgeu(tile_page, t0, done)

    fw.li(a1, head_tile)
    fw.add(a1, a1, tile_page)
    fw.rta_ptr(NM.RTA_L1_BASE_PTR, out=t2)
    fw.arg(a0, 31, ptr=t2)  # Wo input base
    fw.mv(a2, s11)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)

    fw.mv(t6, l1_tile)
    fw.li(a5, ROW_HALF_BYTES)
    fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
    fw.li(t6, TILE_ROW0_COL16_OFF)
    fw.add(t6, l1_tile, t6)
    fw.addi(a0, a0, TILE_ROW0_COL16_OFF)
    fw.li(a5, ROW_HALF_BYTES)
    fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
    fw.addi(s8, s8, 2)
    mm.emit_output_write_state_setup(fw)
    fw.label(done)

  return hook


def main() -> int:
  p = argparse.ArgumentParser(description="live one-head attention chain; needs device")
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--heads", type=int, default=32)
  p.add_argument("--kv-heads", type=int, default=8)
  p.add_argument("--q-head", type=int, default=7)
  p.add_argument("--head-dim", type=int, default=HEAD_DIM)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--seq", type=int, default=32)
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--row-major-cache", action="store_true",
                 help="use the raw row-major KV-cache layout written by the Llama driver")
  p.add_argument("--verbose", action="store_true")
  args = p.parse_args()
  if args.head_dim != HEAD_DIM:
    raise ValueError("this proof currently assumes head_dim=64")
  if args.heads * args.head_dim != args.dim:
    raise ValueError("heads * head_dim must equal dim")
  if args.kv_heads * args.head_dim != args.kv_dim:
    raise ValueError("kv_heads * head_dim must equal kv_dim")
  if args.heads % args.kv_heads:
    raise ValueError("heads must be divisible by kv_heads")
  if not 0 <= args.q_head < args.heads:
    raise ValueError("--q-head must select one Q head")
  if args.seq != TILE:
    raise ValueError("this first proof expects --seq 32")
  if not 0 <= args.pos < args.seq:
    raise ValueError("--pos must select a live position inside --seq")
  if args.max_seq < args.seq or args.max_seq % TILE:
    raise ValueError("--max-seq must be >= --seq and tile-aligned")

  group = args.heads // args.kv_heads
  kv_head = args.q_head // group
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

  k_cache = rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32)
  v_cache = rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32)
  k_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(k_cache), k_cache.shape)
  v_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(v_cache), v_cache.shape)
  ref_scores_all = (q_rot.reshape(1, HEAD_DIM) @ k_cache[kv_head, :args.seq, :].T).reshape(-1)

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    score_chunks = mm.plan_output_chunks(1, HEAD_DIM, args.seq, cores, nb)
    v_chunks = mm.plan_output_chunks(1, args.seq, HEAD_DIM, cores, nb)
    if len(score_chunks) != 1 or len(v_chunks) != 1:
      raise ValueError("this first proof expects one score GEMV chunk and one V GEMV chunk")
    score_chunk = score_chunks[0]
    v_chunk = v_chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(1, HEAD_DIM, args.seq, score_chunks)
    VMp, VKp, VNp = mm.global_padded_shape(1, args.seq, HEAD_DIM, v_chunks)
    if Kp != HEAD_DIM or VMp != Mp or VKp > Np:
      raise RuntimeError(f"unexpected attention shapes score={(Mp, Kp, Np)} v={(VMp, VKp, VNp)}")
    score_tiles = (Mp // TILE) * (Np // TILE)
    wo_n_tiles = args.dim // TILE
    a_pages = (Mp // TILE) * (Kp // TILE)
    k_t_pages = (Kp * Np * 2) // PAGE
    v_pages = (VKp * VNp * 2) // PAGE
    wo_pages = (Mp // TILE) * wo_n_tiles

    c = np.zeros((TILE, qkv_n_padded), dtype=np.float32)
    c[0, :] = qkv
    a_expected = np.zeros((Mp, Kp), dtype=np.float32)
    a_expected[0, :HEAD_DIM] = q_rot
    k_t_expected = np.zeros((Kp, Np), dtype=np.float32)
    k_t_expected[:HEAD_DIM, :args.seq] = k_cache[kv_head, :args.seq, :].T
    v_expected = np.zeros((VKp, VNp), dtype=np.float32)
    v_expected[:args.seq, :HEAD_DIM] = v_cache[kv_head, :args.seq, :]

    c_buf = device.alloc_write(mm.to_bf16_device_bytes(c), dtype=Dtype.Float16_b,
                               shape=c.shape, name="qkv_c")
    cos_buf = device.alloc_write(rope.to_bf16_bytes(qrope.row_tile_table(cos_table)),
                                 dtype=Dtype.Float16_b,
                                 shape=(args.max_seq, TILE, TILE), name="cos_rows")
    sin_buf = device.alloc_write(rope.to_bf16_bytes(qrope.row_tile_table(sin_table)),
                                 dtype=Dtype.Float16_b,
                                 shape=(args.max_seq, TILE, TILE), name="sin_rows")
    q_rope_src_buf = device.dram.alloc(1, dtype=Dtype.Float16_b,
                                       shape=(1, TILE, TILE), name="q_rope_src")
    a_buf = device.dram.alloc(a_pages, dtype=Dtype.Float16_b, shape=(Mp, Kp), name="attn_q_a")
    if args.row_major_cache:
      cache_pages = (args.kv_heads * args.max_seq * HEAD_DIM * Dtype.Float16_b.bpe) // PAGE
      k_cache_buf = device.dram.alloc(cache_pages, dtype=Dtype.Float16_b, name="k_cache_rowmajor")
      v_cache_buf = device.dram.alloc(cache_pages, dtype=Dtype.Float16_b, name="v_cache_rowmajor")
      device.dram_write(k_cache_buf, mm.to_bf16_device_bytes(k_cache))
      device.dram_write(v_cache_buf, mm.to_bf16_device_bytes(v_cache))
    else:
      k_cache_buf = device.alloc_write(mm.to_bf16_device_bytes(k_cache), dtype=Dtype.Float16_b,
                                       shape=k_cache.shape, name="k_cache")
      v_cache_buf = device.alloc_write(mm.to_bf16_device_bytes(v_cache), dtype=Dtype.Float16_b,
                                       shape=v_cache.shape, name="v_cache")
    k_t_buf = device.dram.alloc(k_t_pages, dtype=Dtype.Float16_b, shape=(Kp, Np), name="attn_k_t")
    v_buf = device.dram.alloc(v_pages, dtype=Dtype.Float16_b, shape=(VKp, VNp), name="attn_v")
    scores_buf = device.dram.alloc(score_tiles, dtype=Dtype.Float16_b,
                                   shape=(Mp, Np), name="attn_scores")
    probs_buf = device.dram.alloc(score_tiles, dtype=Dtype.Float16_b,
                                  shape=(score_tiles, TILE, TILE), name="attn_probs")
    ctx_buf = device.dram.alloc((VMp // TILE) * (VNp // TILE), dtype=Dtype.Float16_b,
                                shape=(VMp, VNp), name="attn_ctx")
    wo_in_buf = device.dram.alloc(wo_pages, dtype=Dtype.Float16_b,
                                  shape=(Mp, args.dim), name="wo_input")
    for buf in (q_rope_src_buf, a_buf, k_t_buf, v_buf, scores_buf, probs_buf, ctx_buf, wo_in_buf):
      device.dram_write(buf, b"\0" * buf.size)

    q_stage_prog = qrope.build_q_rope_src_stage_program(
      c_buf.addr, cos_buf.addr, sin_buf.addr, q_rope_src_buf.addr,
      args.q_head, args.pos, nb, core=core)
    q_rope_prog = qrope.build_q_rope_to_a_program(q_rope_src_buf.addr, a_buf.addr, nb, core=core)
    k_builder = kvstage.build_rowmajor_stage_program if args.row_major_cache else kvstage.build_stage_program
    v_builder = kvstage.build_rowmajor_v_stage_program if args.row_major_cache else kvstage.build_v_stage_program
    k_stage_prog = k_builder(
      k_cache_buf.addr, k_t_buf.addr, kv_head, nb, core=core,
      seq=args.seq, max_seq=args.max_seq, n_cols=Np, dst_pages=k_t_pages)
    score_layout = mm.TensorLayout(
      m_tile_offset=score_chunk.m_tile_offset,
      n_tile_offset=score_chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    score_prog = mm.build_program(
      score_chunk.plan, a_buf.addr, k_t_buf.addr, scores_buf.addr, nb, score_layout)
    score_prog.name = "attn_live_score_gemv"
    softmax_prog = kvstage.build_masked_softmax_program(
      scores_buf.addr, probs_buf.addr, nb, core=core, tiles=score_tiles, pos=args.pos)
    softmax_prog.name = "attn_live_masked_softmax"
    v_stage_prog = v_builder(
      v_cache_buf.addr, v_buf.addr, kv_head, nb, core=core,
      seq=args.seq, max_seq=args.max_seq, n_cols=VNp, dst_pages=v_pages)
    v_layout = mm.TensorLayout(
      m_tile_offset=v_chunk.m_tile_offset,
      n_tile_offset=v_chunk.n_tile_offset,
      a_row_stride=Np // TILE,
      b_row_stride=VNp // TILE,
      c_row_stride=VNp // TILE,
    )
    v_prog = mm.build_program(
      v_chunk.plan, probs_buf.addr, v_buf.addr, ctx_buf.addr, nb, v_layout,
      output_tile_hook=make_wo_input_hook(q_head=args.q_head),
      writer_arg_extra=lambda _x, _y: [wo_in_buf.addr],
    )
    v_prog.name = "attn_live_weighted_v_to_wo_input"
    programs = (q_stage_prog, q_rope_prog, k_stage_prog, score_prog,
                softmax_prog, v_stage_prog, v_prog)

    timings = []
    for _ in range(args.runs):
      for prog in programs:
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        timings.extend(device.run(prog))

    q_src_raw = device.dram_read(q_rope_src_buf)
    a_raw = device.dram_read(a_buf)
    k_t_raw = device.dram_read(k_t_buf)
    v_raw = device.dram_read(v_buf)
    scores_raw = device.dram_read(scores_buf)
    probs_raw = device.dram_read(probs_buf)
    ctx_raw = device.dram_read(ctx_buf)
    wo_raw = device.dram_read(wo_in_buf)

  expected_q_src = np.zeros((1, TILE, TILE), dtype=np.float32)
  rope.footprint_put(expected_q_src[0], rope.X1_OFF, q[:32])
  rope.footprint_put(expected_q_src[0], rope.X2_OFF, q[32:])
  rope.footprint_put(expected_q_src[0], rope.COS_OFF, cos)
  rope.footprint_put(expected_q_src[0], rope.SIN_OFF, sin)
  q_src_ok = q_src_raw == rope.to_bf16_bytes(expected_q_src)
  q_ok = bool(np.allclose(
    mm.from_bf16_device_bytes(a_raw, (Mp, Kp)), a_expected, atol=5.0e-2, rtol=5.0e-2))
  k_ok = k_t_raw == mm.to_bf16_device_bytes(k_t_expected)
  v_ok = v_raw == mm.to_bf16_device_bytes(v_expected)

  scores = mm.from_bf16_device_bytes(scores_raw, (Mp, Np))[0, :args.seq]
  probs = mm.from_bf16_device_bytes(probs_raw, (Mp, Np))[0, :args.seq]
  ctx = mm.from_bf16_device_bytes(ctx_raw, (VMp, VNp))[0, :HEAD_DIM]
  wo_matrix = mm.from_bf16_device_bytes(wo_raw, (Mp, args.dim))
  ref_softmax_input = np.zeros((score_tiles, TILE, TILE), dtype=np.float32)
  ref_softmax_input[0, 0, :args.seq] = scores
  ref_softmax_input[0, 0, args.pos + 1:args.seq] = -100.0
  ref_prob_tiles = softmax.ref_softmax(ref_softmax_input)
  ref_probs = mm.from_bf16_device_bytes(softmax.to_bf16_bytes(ref_prob_tiles), (Mp, Np))[0, :args.seq]
  ref_ctx = (ref_probs.reshape(1, args.seq) @ v_cache[kv_head, :args.seq, :]).reshape(-1)
  score_ok = bool(np.allclose(scores[:args.pos + 1], ref_scores_all[:args.pos + 1],
                              atol=1.0e-1, rtol=1.0e-1))
  causal_ok = bool(np.allclose(probs[args.pos + 1:args.seq], 0.0,
                               atol=softmax.ATOL, rtol=softmax.RTOL))
  prob_ok = bool(np.allclose(probs, ref_probs, atol=softmax.ATOL, rtol=softmax.RTOL))
  ctx_ok = bool(np.allclose(ctx, ref_ctx, atol=1.0e-1, rtol=1.0e-1))
  wo_expected = np.zeros((Mp, args.dim), dtype=np.float32)
  wo_expected[0, args.q_head * HEAD_DIM:(args.q_head + 1) * HEAD_DIM] = ctx
  wo_layout_ok = bool(np.array_equal(
    np.frombuffer(mm.to_bf16_device_bytes(wo_matrix), dtype=np.uint16),
    np.frombuffer(mm.to_bf16_device_bytes(wo_expected), dtype=np.uint16),
  ))
  ok = q_src_ok and q_ok and k_ok and v_ok and score_ok and causal_ok and prob_ok and ctx_ok and wo_layout_ok

  print("live one-head attention chain")
  print(f"  q_head={args.q_head} kv_head={kv_head} pos={args.pos} seq={args.seq} runs={args.runs}")
  print(f"  cache_layout={'row-major' if args.row_major_cache else 'tilized'}")
  if timings:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in timings) / len(timings):.1f} us")
  print(f"  Q RoPE source: {'PASS' if q_src_ok else 'FAIL'}")
  print(f"  rotated Q A: {'PASS' if q_ok else 'FAIL'}")
  print(f"  staged K^T: {'PASS' if k_ok else 'FAIL'}")
  print(f"  staged V: {'PASS' if v_ok else 'FAIL'}")
  print(f"  scores: {'PASS' if score_ok else 'FAIL'}")
  print(f"  causal mask: {'PASS' if causal_ok else 'FAIL'}")
  print(f"  softmax: {'PASS' if prob_ok else 'FAIL'}")
  print(f"  weighted V: {'PASS' if ctx_ok else 'FAIL'}")
  print(f"  Wo input placement: {'PASS' if wo_layout_ok else 'FAIL'}")
  if not q_ok:
    got = mm.from_bf16_device_bytes(a_raw, (Mp, Kp))[0, :HEAD_DIM]
    diff = np.abs(got - q_rot)
    i = int(np.argmax(diff))
    print(f"    Q max diff i={i} got={float(got[i]):.6g} ref={float(q_rot[i]):.6g}")
  if not score_ok:
    diff = np.abs(scores[:args.pos + 1] - ref_scores_all[:args.pos + 1])
    i = int(np.argmax(diff))
    print(f"    score max diff i={i} got={float(scores[i]):.6g} ref={float(ref_scores_all[i]):.6g}")
  if not ctx_ok:
    diff = np.abs(ctx - ref_ctx)
    i = int(np.argmax(diff))
    print(f"    ctx max diff i={i} got={float(ctx[i]):.6g} ref={float(ref_ctx[i]):.6g}")
  if not wo_layout_ok:
    diff = np.abs(wo_matrix - wo_expected)
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    Wo input stray value row={r} col={c} got={float(wo_matrix[r, c]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
