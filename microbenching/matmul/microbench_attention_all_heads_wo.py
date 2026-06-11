#!/usr/bin/env python3
"""All-head staged attention handoff into the Wo GEMV input.

This composes the one-head live-cache attention proof across every query head:

  QKV C Q head -> Q RoPE -> score GEMV A
  live K cache -> K^T; live V cache -> V
  score GEMV -> causal masked softmax -> weighted V
  weighted-V row0 -> the corresponding slice of the full Wo input row

The point is not launch minimization yet. This proves the driver-facing
contract: all context heads can be assembled in the device-resident row-tiled
input buffer that Wo already consumes.
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
import microbench_attention_live_head as live_head  # noqa: E402
import microbench_attention_q_rope_stage as qrope  # noqa: E402
import microbench_rope_k_scatter as rope  # noqa: E402
import microbench_softmax as softmax  # noqa: E402
import numpy as np

from program import Dtype  # noqa: E402

TILE = 32
HEAD_DIM = 64


def rotated_q(q: np.ndarray, cos: np.ndarray, sin: np.ndarray) -> np.ndarray:
  out = np.empty_like(q)
  out[:32] = q[:32] * cos - q[32:] * sin
  out[32:] = q[32:] * cos + q[:32] * sin
  return rope.to_bf16(out)


def ref_attention_contexts(
    *,
    qkv: np.ndarray,
    cos: np.ndarray,
    sin: np.ndarray,
    k_cache: np.ndarray,
    v_cache: np.ndarray,
    heads: int,
    kv_heads: int,
    seq: int,
    pos: int,
    score_tiles: int,
    score_mp: int,
    score_np: int,
) -> np.ndarray:
  group = heads // kv_heads
  out = np.zeros((heads, HEAD_DIM), dtype=np.float32)
  for q_head in range(heads):
    kv_head = q_head // group
    q = qkv[q_head * HEAD_DIM:(q_head + 1) * HEAD_DIM]
    q_rot = rotated_q(q, cos, sin)
    scores = (q_rot.reshape(1, HEAD_DIM) @ k_cache[kv_head, :seq, :].T).reshape(-1)
    ref_softmax_input = np.zeros((score_tiles, TILE, TILE), dtype=np.float32)
    ref_softmax_input[0, 0, :seq] = scores
    ref_softmax_input[0, 0, pos + 1:seq] = -100.0
    ref_prob_tiles = softmax.ref_softmax(ref_softmax_input)
    probs = mm.from_bf16_device_bytes(
      softmax.to_bf16_bytes(ref_prob_tiles), (score_mp, score_np))[0, :seq]
    out[q_head] = (probs.reshape(1, seq) @ v_cache[kv_head, :seq, :]).reshape(-1)
  return out


def main() -> int:
  p = argparse.ArgumentParser(description="all-head staged attention -> Wo GEMV input; needs device")
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--heads", type=int, default=32)
  p.add_argument("--kv-heads", type=int, default=8)
  p.add_argument("--head-dim", type=int, default=HEAD_DIM)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--seq", type=int, default=32)
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--wo-n", type=int, default=256)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--verbose", action="store_true")
  args = p.parse_args()
  if args.head_dim != HEAD_DIM:
    raise ValueError("this proof currently assumes head_dim=64")
  if args.heads * args.head_dim != args.dim:
    raise ValueError("heads * head_dim must equal dim")
  if args.kv_heads * args.head_dim != args.kv_dim:
    raise ValueError("kv-heads * head_dim must equal kv-dim")
  if args.heads % args.kv_heads:
    raise ValueError("heads must be divisible by kv-heads")
  if args.seq != TILE:
    raise ValueError("this first proof expects --seq 32")
  if not 0 <= args.pos < args.seq:
    raise ValueError("--pos must select a live position inside --seq")
  if args.max_seq < args.seq or args.max_seq % TILE:
    raise ValueError("--max-seq must be >= --seq and tile-aligned")
  if args.wo_n % TILE:
    raise ValueError("--wo-n must be tile-aligned")

  rng = np.random.default_rng(241)
  qkv_n = args.dim + 2 * args.kv_dim
  qkv_n_padded = ((qkv_n + TILE - 1) // TILE) * TILE
  qkv = rope.to_bf16(rng.uniform(-2.0, 2.0, size=qkv_n_padded).astype(np.float32))
  cos_table = rope.to_bf16(rng.uniform(-1.0, 1.0, size=(args.max_seq, TILE)).astype(np.float32))
  sin_table = rope.to_bf16(rng.uniform(-1.0, 1.0, size=(args.max_seq, TILE)).astype(np.float32))
  cos = cos_table[args.pos]
  sin = sin_table[args.pos]

  k_cache = rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32)
  v_cache = rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32)
  k_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(k_cache), k_cache.shape)
  v_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(v_cache), v_cache.shape)
  wo_w = rng.uniform(-0.2, 0.2, size=(args.dim, args.wo_n)).astype(np.float32)
  wo_w = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(wo_w), wo_w.shape)

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]

    score_chunks = mm.plan_output_chunks(1, HEAD_DIM, args.seq, cores, nb)
    v_chunks = mm.plan_output_chunks(1, args.seq, HEAD_DIM, cores, nb)
    wo_chunks = mm.plan_output_chunks(1, args.dim, args.wo_n, cores, nb)
    if len(score_chunks) != 1 or len(v_chunks) != 1:
      raise ValueError("this first proof expects one GEMV chunk for scores and V")

    score_chunk = score_chunks[0]
    v_chunk = v_chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(1, HEAD_DIM, args.seq, score_chunks)
    VMp, VKp, VNp = mm.global_padded_shape(1, args.seq, HEAD_DIM, v_chunks)
    WoMp, WoKp, WoNp = mm.global_padded_shape(1, args.dim, args.wo_n, wo_chunks)
    if Kp != HEAD_DIM or VMp != Mp or VKp > Np:
      raise RuntimeError(f"unexpected attention shapes score={(Mp, Kp, Np)} v={(VMp, VKp, VNp)}")
    if WoMp != Mp or WoKp < args.dim:
      raise RuntimeError(f"unexpected Wo GEMV shape {(WoMp, WoKp, WoNp)} for attention Mp={Mp}")

    score_tiles = (Mp // TILE) * (Np // TILE)
    a_pages = (Mp // TILE) * (Kp // TILE)
    k_t_pages = (Kp * Np * 2) // Dtype.Float16_b.tile_size
    v_pages = (VKp * VNp * 2) // Dtype.Float16_b.tile_size
    ctx_pages = (VMp // TILE) * (VNp // TILE)
    wo_in_pages = (WoMp // TILE) * (WoKp // TILE)
    wo_out_pages = (WoMp // TILE) * (WoNp // TILE)

    c = np.zeros((TILE, qkv_n_padded), dtype=np.float32)
    c[0, :] = qkv
    wo_w_padded = np.zeros((WoKp, WoNp), dtype=np.float32)
    wo_w_padded[:args.dim, :args.wo_n] = wo_w

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
    ctx_buf = device.dram.alloc(ctx_pages, dtype=Dtype.Float16_b, shape=(VMp, VNp), name="attn_ctx")
    wo_in_buf = device.dram.alloc(wo_in_pages, dtype=Dtype.Float16_b,
                                  shape=(WoMp, WoKp), name="wo_input")
    wo_w_buf = device.alloc_write(mm.to_bf16_device_bytes(wo_w_padded), dtype=Dtype.Float16_b,
                                  shape=(WoKp, WoNp), name="wo_w")
    wo_out_buf = device.dram.alloc(wo_out_pages, dtype=Dtype.Float16_b,
                                   shape=(WoMp, WoNp), name="wo_out")
    for buf in (q_rope_src_buf, a_buf, k_t_buf, v_buf, scores_buf, probs_buf,
                ctx_buf, wo_in_buf, wo_out_buf):
      device.dram_write(buf, b"\0" * buf.size)

    score_layout = mm.TensorLayout(
      m_tile_offset=score_chunk.m_tile_offset,
      n_tile_offset=score_chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    v_layout = mm.TensorLayout(
      m_tile_offset=v_chunk.m_tile_offset,
      n_tile_offset=v_chunk.n_tile_offset,
      a_row_stride=Np // TILE,
      b_row_stride=VNp // TILE,
      c_row_stride=VNp // TILE,
    )

    attn_programs = []
    group = args.heads // args.kv_heads
    for q_head in range(args.heads):
      kv_head = q_head // group
      q_stage_prog = qrope.build_q_rope_src_stage_program(
        c_buf.addr, cos_buf.addr, sin_buf.addr, q_rope_src_buf.addr,
        q_head, args.pos, nb, core=core)
      q_stage_prog.name = f"attn_h{q_head}_q_rope_src_stage"
      q_rope_prog = qrope.build_q_rope_to_a_program(q_rope_src_buf.addr, a_buf.addr, nb, core=core)
      q_rope_prog.name = f"attn_h{q_head}_q_rope_to_a"
      k_stage_prog = kvstage.build_stage_program(
        k_cache_buf.addr, k_t_buf.addr, kv_head, nb, core=core,
        seq=args.seq, max_seq=args.max_seq, n_cols=Np, dst_pages=k_t_pages)
      k_stage_prog.name = f"attn_h{q_head}_k_cache_to_kt"
      score_prog = mm.build_program(
        score_chunk.plan, a_buf.addr, k_t_buf.addr, scores_buf.addr, nb, score_layout)
      score_prog.name = f"attn_h{q_head}_score_gemv"
      softmax_prog = kvstage.build_masked_softmax_program(
        scores_buf.addr, probs_buf.addr, nb, core=core, tiles=score_tiles, pos=args.pos)
      softmax_prog.name = f"attn_h{q_head}_masked_softmax"
      v_stage_prog = kvstage.build_v_stage_program(
        v_cache_buf.addr, v_buf.addr, kv_head, nb, core=core,
        seq=args.seq, max_seq=args.max_seq, n_cols=VNp, dst_pages=v_pages)
      v_stage_prog.name = f"attn_h{q_head}_v_cache_to_v"
      v_prog = mm.build_program(
        v_chunk.plan, probs_buf.addr, v_buf.addr, ctx_buf.addr, nb, v_layout,
        output_tile_hook=live_head.make_wo_input_hook(q_head=q_head),
        writer_arg_extra=lambda _x, _y: [wo_in_buf.addr],
      )
      v_prog.name = f"attn_h{q_head}_weighted_v_to_wo"
      attn_programs.extend((
        q_stage_prog, q_rope_prog, k_stage_prog, score_prog,
        softmax_prog, v_stage_prog, v_prog,
      ))

    wo_layout_base = dict(
      a_row_stride=WoKp // TILE,
      b_row_stride=WoNp // TILE,
      c_row_stride=WoNp // TILE,
    )
    wo_programs = []
    for i, chunk in enumerate(wo_chunks):
      layout = mm.TensorLayout(
        m_tile_offset=chunk.m_tile_offset,
        n_tile_offset=chunk.n_tile_offset,
        **wo_layout_base,
      )
      prog = mm.build_program(chunk.plan, wo_in_buf.addr, wo_w_buf.addr, wo_out_buf.addr, nb, layout)
      prog.name = "attn_wo_gemv" if len(wo_chunks) == 1 else f"attn_wo_gemv_chunk{i}"
      wo_programs.append(prog)

    times = []
    for run in range(args.runs):
      if run:
        device.dram_write(wo_in_buf, b"\0" * wo_in_buf.size)
        device.dram_write(wo_out_buf, b"\0" * wo_out_buf.size)
      for prog in (*attn_programs, *wo_programs):
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        times.extend(device.run(prog))

    wo_raw = device.dram_read(wo_in_buf)
    wo_out_raw = device.dram_read(wo_out_buf)

  ref_ctx_heads = ref_attention_contexts(
    qkv=qkv, cos=cos, sin=sin, k_cache=k_cache, v_cache=v_cache,
    heads=args.heads, kv_heads=args.kv_heads, seq=args.seq, pos=args.pos,
    score_tiles=score_tiles, score_mp=Mp, score_np=Np,
  )
  ref_wo = np.zeros((WoMp, WoKp), dtype=np.float32)
  ref_wo[0, :args.dim] = ref_ctx_heads.reshape(-1)
  wo_matrix = mm.from_bf16_device_bytes(wo_raw, (WoMp, WoKp))
  wo_row = wo_matrix[0, :args.dim]
  row_ok = bool(np.allclose(wo_row, ref_wo[0, :args.dim], atol=2.0e-1, rtol=2.0e-1))
  pad_ok = bool(np.count_nonzero(wo_matrix[0, args.dim:]) == 0)
  zero_ok = bool(np.count_nonzero(wo_matrix[1:, :]) == 0)
  try:
    pcc, rel_l2 = mm.validate(wo_matrix[:1, :WoKp], wo_w_padded[:, :args.wo_n],
                              wo_out_raw, 1, args.wo_n, WoMp, WoNp)
    wo_gemv_ok = True
  except AssertionError as exc:
    pcc = 0.0
    rel_l2 = float("inf")
    wo_gemv_ok = False
    wo_gemv_err = str(exc)
  else:
    wo_gemv_err = ""
  ok = row_ok and pad_ok and zero_ok and wo_gemv_ok

  print("all-head staged attention -> Wo input")
  print(f"  heads={args.heads} kv_heads={args.kv_heads} pos={args.pos} seq={args.seq} runs={args.runs}")
  print(f"  Wo GEMV N={args.wo_n} wo_chunks={len(wo_chunks)}")
  if times:
    launches = (len(attn_programs) + len(wo_programs)) * args.runs
  print(f"  launches={launches} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  Wo input row: {'PASS' if row_ok else 'FAIL'}")
  print(f"  Wo input padded K columns zero: {'PASS' if pad_ok else 'FAIL'}")
  print(f"  Wo input padded rows zero: {'PASS' if zero_ok else 'FAIL'}")
  print(f"  Wo GEMV consumes assembled input: {'PASS' if wo_gemv_ok else 'FAIL'}"
        f" pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  if not row_ok:
    diff = np.abs(wo_row - ref_wo[0, :args.dim])
    i = int(np.argmax(diff))
    h = i // HEAD_DIM
    lane = i % HEAD_DIM
    print(f"    Wo row max diff head={h} lane={lane} got={float(wo_row[i]):.6g} "
          f"ref={float(ref_wo[0, i]):.6g}")
  if not zero_ok:
    nz = np.argwhere(wo_matrix[1:, :] != 0)
    r, c = (int(nz[0, 0] + 1), int(nz[0, 1])) if nz.size else (-1, -1)
    print(f"    first nonzero padded entry row={r} col={c} value={float(wo_matrix[r, c]):.6g}")
  if not pad_ok:
    nz = np.flatnonzero(wo_matrix[0, args.dim:] != 0)
    c = int(nz[0] + args.dim) if nz.size else -1
    print(f"    first nonzero padded-K entry col={c} value={float(wo_matrix[0, c]):.6g}")
  if not wo_gemv_ok:
    print(f"    {wo_gemv_err}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
