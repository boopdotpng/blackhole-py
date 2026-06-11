#!/usr/bin/env python3
"""GQA-group multi-tile attention score proof.

This is the first full-history decode building block beyond the current
block-local integration path:

  grouped Q/RoPE once
  for each live 32-token history tile:
    row-major K/V stage as the synchronized score-GEMV preamble
    grouped score GEMV writes that tile's score rows
  current tile causal score mask writes -100 after pos % 32

It intentionally stops before softmax. Existing softmax normalizes one
32-token tile at a time; full-history attention needs a separate device-side
global softmax/accumulator across these score tiles.
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
import microbench_attention_gqa_group as gqa  # noqa: E402
import microbench_attention_k_stage as kvstage  # noqa: E402
import microbench_attention_q_rope_stage as qrope  # noqa: E402
import microbench_rope_k_scatter as rope  # noqa: E402
import numpy as np

from asm import KernelBase  # noqa: E402
from dsl import s0, s1, s2, s3, s4, s5, s6, t0, t1, t2, zero  # noqa: E402
from examples.add1 import Brisc  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.mailbox import NcriscMailbox as NM  # noqa: E402

TILE = 32
HEAD_DIM = 64
GROUP = 4
PAGE = Dtype.Float16_b.tile_size
MASK_BF16 = 0xC2C8  # bf16(-100.0), matching the current softmax feeder mask.


def build_causal_score_mask_program(score_addr: int, num_banks: int, *, core,
                                    pos: int, mask_rows: int = GROUP,
                                    page: int = 0) -> Program:
  if not 0 <= pos < TILE:
    raise ValueError("pos must be local to one 32-token tile")
  if not 1 <= mask_rows <= TILE:
    raise ValueError("mask_rows must select 1..32 tile rows")
  fw = Brisc()
  # RTAs: score tile base, same base as write destination, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s3))
  fw.li(t2, page)
  kvstage.emit_read_page(fw, base_reg=s0, page_reg=t2, l1_dst=kvstage.DST_L1)
  if pos < TILE - 1:
    fw.li(t0, MASK_BF16)
    for row in range(mask_rows):
      for col in range(pos + 1, TILE):
        fw.li(t1, kvstage.DST_L1 + kvstage.packed_elem_offset(row, col))
        fw.sh(t0, t1, 0)
  kvstage.emit_write_l1_page(fw, page=page, l1_src=kvstage.DST_L1)
  fw.ret()
  fw.rta(lambda _x, _y: [score_addr, score_addr, num_banks])
  prog = Program(brisc=fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = f"attn_gqa_causal_score_mask_p{pos}"
  return prog


def _emit_bf16_order_key(fw: Brisc, value_reg, key_reg) -> None:
  negative = fw._new_label("bf16_key_negative")
  done = fw._new_label("bf16_key_done")
  fw.li(t2, 0x8000)
  fw.and_(key_reg, value_reg, t2)
  fw.bne(key_reg, zero, negative)
  fw.or_(key_reg, value_reg, t2)
  fw.j(done)
  fw.label(negative)
  fw.li(t2, 0xFFFF)
  fw.xor(key_reg, value_reg, t2)
  fw.label(done)


def build_global_score_rowmax_program(score_addrs: list[int], dst_addr: int,
                                      num_banks: int, *, core,
                                      rows: int = GROUP) -> Program:
  if not 1 <= len(score_addrs) <= 3:
    raise ValueError("rowmax proof supports 1..3 score tiles")
  if not 1 <= rows <= TILE:
    raise ValueError("rows must select 1..32 score rows")
  fw = Brisc()
  # RTAs: score tile 0, score tile 1, score tile 2, rowmax dst, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s4, s3))
  kvstage.emit_zero_dst(fw, pages=1)
  src_regs = (s0, s1, s2)[:len(score_addrs)]
  for row in range(rows):
    fw.li(s5, 0xFF80)  # bf16(-inf)
    fw.li(s6, 0)
    for src_reg in src_regs:
      fw.li(t2, 0)
      kvstage.emit_read_page(fw, base_reg=src_reg, page_reg=t2, l1_dst=kvstage.SRC_L1)
      for col in range(TILE):
        fw.li(t2, kvstage.SRC_L1 + kvstage.packed_elem_offset(row, col))
        fw.lhu(t0, t2, 0)
        _emit_bf16_order_key(fw, t0, t1)
        keep = fw._new_label("rowmax_keep")
        fw.bgeu(s6, t1, keep)
        fw.mv(s5, t0)
        fw.mv(s6, t1)
        fw.label(keep)
    fw.li(t2, kvstage.DST_L1 + kvstage.packed_elem_offset(row, 0))
    fw.sh(s5, t2, 0)
  fw.mv(s1, s4)
  kvstage.emit_write_l1_page(fw, page=0, l1_src=kvstage.DST_L1)
  fw.ret()
  padded = [*score_addrs, 0, 0][:3]
  fw.rta(lambda _x, _y: [*padded, dst_addr, num_banks])
  prog = Program(brisc=fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_gqa_global_score_rowmax"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="GQA multi-tile score proof; needs device")
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--heads", type=int, default=32)
  p.add_argument("--kv-heads", type=int, default=8)
  p.add_argument("--kv-head", type=int, default=1)
  p.add_argument("--max-seq", type=int, default=96)
  p.add_argument("--pos", type=int, default=47)
  p.add_argument("--k-scale-pow2-down", type=int, default=3)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--verbose", action="store_true")
  args = p.parse_args()

  if args.heads * HEAD_DIM != args.dim:
    raise ValueError("heads * 64 must equal dim")
  if args.kv_heads * HEAD_DIM != args.kv_dim:
    raise ValueError("kv-heads * 64 must equal kv_dim")
  if args.heads // args.kv_heads != GROUP or args.heads % args.kv_heads:
    raise ValueError("this proof expects exactly four Q heads per KV head")
  if not 0 <= args.kv_head < args.kv_heads:
    raise ValueError("--kv-head must select a KV head")
  if args.max_seq % kvstage.ROWS_PER_PAGE:
    raise ValueError("--max-seq must be row-cache page-aligned")
  if not 0 <= args.pos < args.max_seq:
    raise ValueError("--pos must be inside --max-seq")
  live_tiles = args.pos // TILE + 1
  if live_tiles < 2:
    raise ValueError("use pos >= 32 so this actually proves multiple history tiles")

  q_base = args.kv_head * GROUP
  rng = np.random.default_rng(269)
  qkv_n = args.dim + 2 * args.kv_dim
  qkv_n_padded = ((qkv_n + TILE - 1) // TILE) * TILE
  qkv = rope.to_bf16(rng.uniform(-2.0, 2.0, size=qkv_n_padded).astype(np.float32))
  cos_table = rope.to_bf16(rng.uniform(-1.0, 1.0, size=(args.max_seq, TILE)).astype(np.float32))
  sin_table = rope.to_bf16(rng.uniform(-1.0, 1.0, size=(args.max_seq, TILE)).astype(np.float32))
  cos = cos_table[args.pos]
  sin = sin_table[args.pos]
  q_rot = np.zeros((GROUP, HEAD_DIM), dtype=np.float32)
  for row in range(GROUP):
    q = qkv[(q_base + row) * HEAD_DIM:(q_base + row + 1) * HEAD_DIM]
    q_rot[row] = gqa.rotate_q(q, cos, sin)

  k_cache = rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32)
  v_cache = rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32)
  k_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(k_cache), k_cache.shape)
  v_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(v_cache), v_cache.shape)
  staged_k = kvstage.bf16_array_scale_pow2_down(
      k_cache[args.kv_head, :live_tiles * TILE, :], args.k_scale_pow2_down)
  ref_scores_raw = q_rot @ staged_k.T
  ref_scores = ref_scores_raw.copy()
  ref_scores[:, args.pos + 1:] = np.float32(-100.0)

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    score_chunks = mm.plan_output_chunks(GROUP, HEAD_DIM, TILE, cores, nb)
    if len(score_chunks) != 1:
      raise ValueError("this proof expects one grouped score GEMV chunk")
    score_chunk = score_chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(GROUP, HEAD_DIM, TILE, score_chunks)
    if Kp != HEAD_DIM or Np < TILE:
      raise RuntimeError(f"unexpected score shape {(Mp, Kp, Np)}")
    score_tiles = (Mp // TILE) * (Np // TILE)
    a_pages = (Mp // TILE) * (Kp // TILE)
    k_t_pages = (Kp * Np * Dtype.Float16_b.bpe) // PAGE
    v_pages = (TILE * HEAD_DIM * Dtype.Float16_b.bpe) // PAGE

    c = np.zeros((TILE, qkv_n_padded), dtype=np.float32)
    c[0, :] = qkv
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
    a_buf = device.dram.alloc(a_pages, dtype=Dtype.Float16_b, shape=(Mp, Kp),
                              name="attn_q_group_a")
    cache_pages = (args.kv_heads * args.max_seq * HEAD_DIM * Dtype.Float16_b.bpe) // PAGE
    k_cache_buf = device.dram.alloc(cache_pages, dtype=Dtype.Float16_b, name="k_cache_rowmajor")
    v_cache_buf = device.dram.alloc(cache_pages, dtype=Dtype.Float16_b, name="v_cache_rowmajor")
    device.dram_write(k_cache_buf, mm.to_bf16_device_bytes(k_cache))
    device.dram_write(v_cache_buf, mm.to_bf16_device_bytes(v_cache))
    k_t_buf = device.dram.alloc(k_t_pages, dtype=Dtype.Float16_b,
                                shape=(Kp, Np), name="attn_k_t")
    v_buf = device.dram.alloc(v_pages, dtype=Dtype.Float16_b,
                              shape=(TILE, HEAD_DIM), name="attn_v")
    score_bufs = [
      device.dram.alloc(score_tiles, dtype=Dtype.Float16_b,
                        shape=(Mp, Np), name=f"attn_scores_tile{tile}")
      for tile in range(live_tiles)
    ]
    rowmax_buf = device.dram.alloc(1, dtype=Dtype.Float16_b,
                                   shape=(1, TILE, TILE), name="attn_score_rowmax")
    for buf in (q_rope_src_buf, a_buf, k_t_buf, v_buf, *score_bufs, rowmax_buf):
      device.dram_write(buf, b"\0" * buf.size)

    q_prog = qrope.build_q_rope_group_stage_to_a_program(
        c_buf.addr, cos_buf.addr, sin_buf.addr, q_rope_src_buf.addr, a_buf.addr,
        q_base, args.pos, nb, core=core, group=GROUP)
    q_prog.name = f"attn_gqa_q{q_base}_q{q_base + GROUP - 1}_stage_rope_to_a"

    score_layout = mm.TensorLayout(
      m_tile_offset=score_chunk.m_tile_offset,
      n_tile_offset=score_chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    score_programs = []
    for tile in range(live_tiles):
      seq_start = tile * TILE
      score_writer_rta_count = len(
          mm.writer_args(score_chunk.plan, k_t_buf.addr, score_bufs[tile].addr, core, nb, score_layout))

      def _score_writer_preamble(fw, _plan, seq_start=seq_start):
        kvstage.emit_rowmajor_kv_stage_preamble(
          fw, seq=TILE, max_seq=args.max_seq,
          k_n_cols=Np, v_n_cols=HEAD_DIM,
          k_dst_pages=k_t_pages, v_dst_pages=v_pages,
          rta_offset=score_writer_rta_count,
          seq_start=seq_start,
          k_scale_pow2_down=args.k_scale_pow2_down,
          rta_ptr_addr=NM.RTA_L1_BASE_PTR,
          bank_table=NM.DRAM_BANK_TO_NOC_XY,
          noc_id=1,
          x_addr=NM.MY_X,
          y_addr=NM.MY_Y)
        gqa.emit_signal_kv_score_preamble(fw)

      prog = mm.build_program(
        score_chunk.plan, a_buf.addr, k_t_buf.addr, score_bufs[tile].addr, nb, score_layout,
        reader_preamble=gqa.emit_wait_for_kv_score_preamble,
        writer_preamble=_score_writer_preamble,
        writer_arg_extra=lambda _x, _y: [
          k_cache_buf.addr, k_t_buf.addr, args.kv_head, nb, v_cache_buf.addr, v_buf.addr,
        ])
      prog.name = f"attn_gqa_t{tile}_score_gemv_kv_preamble"
      score_programs.append(prog)

    mask_prog = build_causal_score_mask_program(
        score_bufs[-1].addr, nb, core=core, pos=args.pos % TILE, mask_rows=GROUP)
    rowmax_prog = build_global_score_rowmax_program(
        [buf.addr for buf in score_bufs], rowmax_buf.addr, nb, core=core, rows=GROUP)
    programs = (q_prog, *score_programs, mask_prog, rowmax_prog)
    times = []
    for _ in range(args.runs):
      for prog in programs:
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        times.extend(device.run(prog))

    a_raw = device.dram_read(a_buf)
    score_raws = [device.dram_read(buf) for buf in score_bufs]
    rowmax_raw = device.dram_read(rowmax_buf)

  a_expected = np.zeros((Mp, Kp), dtype=np.float32)
  a_expected[:GROUP, :HEAD_DIM] = q_rot
  a_ok = bool(np.allclose(mm.from_bf16_device_bytes(a_raw, (Mp, Kp)),
                          a_expected, atol=5.0e-2, rtol=5.0e-2))
  scores_by_tile = [
    mm.from_bf16_device_bytes(raw, (Mp, Np))[:GROUP, :TILE]
    for raw in score_raws
  ]
  scores = np.concatenate(scores_by_tile, axis=1)
  score_ok = bool(np.allclose(scores, ref_scores, atol=1.0e-1, rtol=1.0e-1))
  future = scores[:, args.pos + 1:]
  causal_ok = bool(np.allclose(future, -100.0, atol=1.0e-3, rtol=1.0e-3))
  rowmax_tile = mm.from_bf16_device_bytes(rowmax_raw, (TILE, TILE))
  rowmax_got = rowmax_tile[:GROUP, 0]
  rowmax_ref = scores.max(axis=1)
  rowmax_ok = bool(np.array_equal(
      np.frombuffer(mm.to_bf16_device_bytes(rowmax_got), dtype=np.uint16),
      np.frombuffer(mm.to_bf16_device_bytes(rowmax_ref), dtype=np.uint16)))
  ok = a_ok and score_ok and causal_ok and rowmax_ok

  print("GQA-group multi-tile score proof")
  print(f"  kv_head={args.kv_head} q_heads={q_base}..{q_base + GROUP - 1} "
        f"pos={args.pos} live_tiles={live_tiles} k_scale=2^-{args.k_scale_pow2_down} runs={args.runs}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  grouped Q A rows: {'PASS' if a_ok else 'FAIL'}")
  print(f"  multi-tile causal grouped scores: {'PASS' if score_ok else 'FAIL'}")
  print(f"  current-tile causal mask: {'PASS' if causal_ok else 'FAIL'}")
  print(f"  global row max: {'PASS' if rowmax_ok else 'FAIL'}")
  if not score_ok:
    diff = np.abs(scores - ref_scores)
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    score max diff row={r} col={c} got={float(scores[r, c]):.6g} "
          f"ref={float(ref_scores[r, c]):.6g}")
  if not causal_ok and future.size:
    diff = np.abs(future - np.float32(-100.0))
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    future mask max diff row={r} col={args.pos + 1 + c} "
          f"got={float(future[r, c]):.6g}")
  if not rowmax_ok:
    for row in range(GROUP):
      print(f"    rowmax row={row} got={float(rowmax_got[row]):.6g} "
            f"ref={float(rowmax_ref[row]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
