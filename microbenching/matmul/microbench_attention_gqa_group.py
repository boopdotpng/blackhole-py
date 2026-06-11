#!/usr/bin/env python3
"""One GQA-group staged attention proof.

This is the next launch-reduction boundary after fusing Q-stage+Q-RoPE:

  stage K once for one KV head
  stage V once for one KV head
  stage+RoPE four Q heads into rows 0..3 of one score-GEMV A buffer
  score GEMV produces four score rows
  one masked softmax handles those rows
  one weighted-V GEMV produces four context rows
  the writer hook places those rows into the matching Wo input slices

By default the four Q-stage/RoPE rows are produced by one grouped Q program.
Use --split-q to keep the older four-Q-launch + assemble path for comparison.
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

from asm import KernelBase  # noqa: E402
from dsl import a0, a1, a2, a5, s0, s1, s2, s3, s4, s5, s8, s11, t0, t1, t2, t4, t5, t6, zero  # noqa: E402
from examples.add1 import Brisc  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.mailbox import NcriscMailbox as NM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402

TILE = 32
HEAD_DIM = 64
GROUP = 4
PAGE = Dtype.Float16_b.tile_size
ROW_HALF_BYTES = 16 * Dtype.Float16_b.bpe
TILE_ROW0_COL16_OFF = 16 * 16 * Dtype.Float16_b.bpe
SRC_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
DST_L1 = SRC_L1 + PAGE
KV_SCORE_SYNC_SEM = 2


def make_group_wo_input_hook(*, q_base: int, rows: int = GROUP, src_row_stride: int = 2):
  """Copy weighted-V rows 0..rows-1 into full-width Wo input row slices."""

  def hook(fw, plan, *, tile_page, l1_tile):
    del plan
    done = fw._new_label("wo_group_hook_done")
    fw.li(t0, HEAD_DIM // TILE)
    fw.bgeu(tile_page, t0, done)

    for row in range(rows):
      src_row = row * src_row_stride
      dst_head_tile = (q_base + row) * (HEAD_DIM // TILE)
      for half, src_col in enumerate((0, 16)):
        fw.li(a1, dst_head_tile)
        fw.add(a1, a1, tile_page)
        fw.rta_ptr(NM.RTA_L1_BASE_PTR, out=t2)
        fw.arg(a0, 31, ptr=t2)  # Wo input base
        fw.mv(a2, s11)
        fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)
        if half:
          fw.addi(a0, a0, TILE_ROW0_COL16_OFF)
        src_off = kvstage.packed_elem_offset(src_row, src_col)
        fw.li(t6, src_off)
        fw.add(t6, l1_tile, t6)
        fw.li(a5, ROW_HALF_BYTES)
        fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
      fw.addi(s8, s8, 2)
    mm.emit_output_write_state_setup(fw)
    fw.label(done)

  return hook


def rotate_q(q: np.ndarray, cos: np.ndarray, sin: np.ndarray) -> np.ndarray:
  out = np.empty_like(q)
  out[:32] = q[:32] * cos - q[32:] * sin
  out[32:] = q[32:] * cos + q[:32] * sin
  return rope.to_bf16(out)


def _emit_read_tmp_page(fw: Brisc, *, base_reg, page: int, l1_dst: int) -> None:
  fw.mv(a0, base_reg)
  fw.li(a1, page)
  fw.mv(a2, s5)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, l1_dst)
  fw.li(t6, PAGE)
  fw.noc_read(0, 1, a0, 0, a2, t2, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(0, t4, addr=t0, val=t1)


def _emit_write_group_page(fw: Brisc, *, page: int, l1_src: int) -> None:
  fw.mv(a0, s4)
  fw.li(a1, page)
  fw.mv(a2, s5)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, l1_src)
  fw.li(t6, PAGE)
  fw.noc_write(0, 0, t2, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(0, t4, addr=t0, val=t1)


def build_group_q_assemble_program(tmp_addrs: list[int], dst_addr: int,
                                   num_banks: int, *, core) -> Program:
  if len(tmp_addrs) != GROUP:
    raise ValueError("expected one temporary Q A buffer per GQA row")
  fw = Brisc()
  # RTAs: tmp0, tmp1, tmp2, tmp3, grouped A dst, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5))

  fw.li(t0, DST_L1)
  fw.li(t1, DST_L1 + (HEAD_DIM // TILE) * PAGE)
  zero_loop = fw._new_label("gqa_q_asm_zero")
  fw.label(zero_loop)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.bltu(t0, t1, zero_loop)

  src_regs = (s0, s1, s2, s3)
  for row, src_reg in enumerate(src_regs):
    for page in range(HEAD_DIM // TILE):
      _emit_read_tmp_page(fw, base_reg=src_reg, page=page, l1_dst=SRC_L1)
      for lane in range(TILE):
        fw.li(t5, SRC_L1)
        fw.lhu(t0, t5, kvstage.packed_elem_offset(0, lane))
        fw.li(t2, DST_L1 + page * PAGE + kvstage.packed_elem_offset(row, lane))
        fw.sh(t0, t2, 0)

  for page in range(HEAD_DIM // TILE):
    _emit_write_group_page(fw, page=page, l1_src=DST_L1 + page * PAGE)
  fw.ret()

  fw.rta(lambda _x, _y: [*tmp_addrs, dst_addr, num_banks])
  prog = Program(brisc=fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_gqa_q_rows_to_group_a"
  return prog


def emit_wait_for_kv_score_preamble(fw, _plan) -> None:
  fw.li(t0, KV_SCORE_SYNC_SEM)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=t6)
  fw.noc_semaphore_wait(t6, 1)
  fw.noc_semaphore_set(t6, 0)


def emit_signal_kv_score_preamble(fw) -> None:
  fw.li(t0, KV_SCORE_SYNC_SEM)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=t6)
  fw.noc_semaphore_set(t6, 1)


def main() -> int:
  p = argparse.ArgumentParser(description="one GQA-group attention proof; needs device")
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--heads", type=int, default=32)
  p.add_argument("--kv-heads", type=int, default=8)
  p.add_argument("--kv-head", type=int, default=1)
  p.add_argument("--head-dim", type=int, default=HEAD_DIM)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--seq", type=int, default=32)
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--split-q", action="store_true", help="use four Q/RoPE launches plus row assembly")
  p.add_argument("--fuse-kv-score", action="store_true",
                 help="stage row-major K/V as a BRISC preamble inside the score GEMV")
  p.add_argument("--score-scale-pow2-down", type=int, default=0,
                 help="scale scores by 2^-N in the softmax BRISC feeder")
  p.add_argument("--k-scale-pow2-down", type=int, default=0,
                 help="scale staged K by 2^-N before the score GEMV")
  p.add_argument("--verbose", action="store_true")
  args = p.parse_args()
  if args.head_dim != HEAD_DIM:
    raise ValueError("this proof currently assumes head_dim=64")
  if args.heads * args.head_dim != args.dim:
    raise ValueError("heads * head_dim must equal dim")
  if args.kv_heads * args.head_dim != args.kv_dim:
    raise ValueError("kv-heads * head_dim must equal kv-dim")
  if args.heads // args.kv_heads != GROUP or args.heads % args.kv_heads:
    raise ValueError("this proof expects exactly four Q heads per KV head")
  if not 0 <= args.kv_head < args.kv_heads:
    raise ValueError("--kv-head must select a KV head")
  if args.seq != TILE:
    raise ValueError("this first proof expects --seq 32")
  if not 0 <= args.pos < args.seq:
    raise ValueError("--pos must select a live position inside --seq")
  if args.max_seq < args.seq or args.max_seq % kvstage.ROWS_PER_PAGE:
    raise ValueError("--max-seq must be >= --seq and row-cache page-aligned")

  q_base = args.kv_head * GROUP
  rng = np.random.default_rng(251)
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
    q_rot[row] = rotate_q(q, cos, sin)

  k_cache = rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32)
  v_cache = rng.uniform(-0.5, 0.5, size=(args.kv_heads, args.max_seq, HEAD_DIM)).astype(np.float32)
  k_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(k_cache), k_cache.shape)
  v_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(v_cache), v_cache.shape)
  staged_k_rows = kvstage.bf16_array_scale_pow2_down(
      k_cache[args.kv_head, :args.seq, :], args.k_scale_pow2_down)
  ref_scores = q_rot @ staged_k_rows.T

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    score_chunks = mm.plan_output_chunks(GROUP, HEAD_DIM, args.seq, cores, nb)
    v_chunks = mm.plan_output_chunks(GROUP, args.seq, HEAD_DIM, cores, nb)
    if len(score_chunks) != 1 or len(v_chunks) != 1:
      raise ValueError("this proof expects one score GEMV chunk and one V GEMV chunk")
    score_chunk = score_chunks[0]
    v_chunk = v_chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(GROUP, HEAD_DIM, args.seq, score_chunks)
    VMp, VKp, VNp = mm.global_padded_shape(GROUP, args.seq, HEAD_DIM, v_chunks)
    if Kp != HEAD_DIM or VMp != Mp or VKp > Np:
      raise RuntimeError(f"unexpected attention shapes score={(Mp, Kp, Np)} v={(VMp, VKp, VNp)}")

    score_tiles = (Mp // TILE) * (Np // TILE)
    a_pages = (Mp // TILE) * (Kp // TILE)
    k_t_pages = (Kp * Np * Dtype.Float16_b.bpe) // PAGE
    v_pages = (VKp * VNp * Dtype.Float16_b.bpe) // PAGE
    ctx_pages = (VMp // TILE) * (VNp // TILE)
    wo_pages = (Mp // TILE) * (args.dim // TILE)

    c = np.zeros((TILE, qkv_n_padded), dtype=np.float32)
    c[0, :] = qkv
    a_expected = np.zeros((Mp, Kp), dtype=np.float32)
    a_expected[:GROUP, :HEAD_DIM] = q_rot
    k_t_expected = np.zeros((Kp, Np), dtype=np.float32)
    k_t_expected[:HEAD_DIM, :args.seq] = staged_k_rows.T
    v_expected = np.zeros((VKp, VNp), dtype=np.float32)
    v_expected[:args.seq, :HEAD_DIM] = v_cache[args.kv_head, :args.seq, :]

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
    q_tmp_bufs = []
    if args.split_q:
      q_tmp_bufs = [
        device.dram.alloc(HEAD_DIM // TILE, dtype=Dtype.Float16_b,
                          shape=(TILE, HEAD_DIM), name=f"attn_q_tmp_{row}")
        for row in range(GROUP)
      ]
    a_buf = device.dram.alloc(a_pages, dtype=Dtype.Float16_b, shape=(Mp, Kp), name="attn_q_group_a")
    cache_pages = (args.kv_heads * args.max_seq * HEAD_DIM * Dtype.Float16_b.bpe) // PAGE
    k_cache_buf = device.dram.alloc(cache_pages, dtype=Dtype.Float16_b, name="k_cache_rowmajor")
    v_cache_buf = device.dram.alloc(cache_pages, dtype=Dtype.Float16_b, name="v_cache_rowmajor")
    device.dram_write(k_cache_buf, mm.to_bf16_device_bytes(k_cache))
    device.dram_write(v_cache_buf, mm.to_bf16_device_bytes(v_cache))
    k_t_buf = device.dram.alloc(k_t_pages, dtype=Dtype.Float16_b, shape=(Kp, Np), name="attn_k_t")
    v_buf = device.dram.alloc(v_pages, dtype=Dtype.Float16_b, shape=(VKp, VNp), name="attn_v")
    scores_buf = device.dram.alloc(score_tiles, dtype=Dtype.Float16_b,
                                   shape=(Mp, Np), name="attn_scores")
    probs_buf = device.dram.alloc(score_tiles, dtype=Dtype.Float16_b,
                                  shape=(score_tiles, TILE, TILE), name="attn_probs")
    ctx_buf = device.dram.alloc(ctx_pages, dtype=Dtype.Float16_b,
                                shape=(VMp, VNp), name="attn_ctx")
    wo_in_buf = device.dram.alloc(wo_pages, dtype=Dtype.Float16_b,
                                  shape=(Mp, args.dim), name="wo_input")
    for buf in (q_rope_src_buf, *q_tmp_bufs, a_buf, k_t_buf, v_buf, scores_buf, probs_buf,
                ctx_buf, wo_in_buf):
      device.dram_write(buf, b"\0" * buf.size)

    q_programs = []
    if args.split_q:
      for row in range(GROUP):
        prog = qrope.build_q_rope_stage_to_a_program(
          c_buf.addr, cos_buf.addr, sin_buf.addr, q_rope_src_buf.addr, q_tmp_bufs[row].addr,
          q_base + row, args.pos, nb, core=core)
        prog.name = f"attn_gqa_q{q_base + row}_stage_rope_to_a"
        q_programs.append(prog)
      q_assemble_prog = build_group_q_assemble_program(
        [buf.addr for buf in q_tmp_bufs], a_buf.addr, nb, core=core)
      q_programs.append(q_assemble_prog)
    else:
      q_group_prog = qrope.build_q_rope_group_stage_to_a_program(
        c_buf.addr, cos_buf.addr, sin_buf.addr, q_rope_src_buf.addr, a_buf.addr,
        q_base, args.pos, nb, core=core, group=GROUP)
      q_group_prog.name = f"attn_gqa_q{q_base}_q{q_base + GROUP - 1}_stage_rope_to_a"
      q_programs.append(q_group_prog)
    score_layout = mm.TensorLayout(
      m_tile_offset=score_chunk.m_tile_offset,
      n_tile_offset=score_chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    score_writer_rta_count = len(mm.writer_args(score_chunk.plan, k_t_buf.addr, scores_buf.addr, core, nb, score_layout))
    score_reader_preamble = None
    score_writer_preamble = None
    score_writer_extra = None
    if args.fuse_kv_score:
      score_reader_preamble = emit_wait_for_kv_score_preamble
      def _score_writer_preamble(fw, _plan):
        kvstage.emit_rowmajor_kv_stage_preamble(
          fw, seq=args.seq, max_seq=args.max_seq,
          k_n_cols=Np, v_n_cols=VNp, k_dst_pages=k_t_pages, v_dst_pages=v_pages,
          rta_offset=score_writer_rta_count,
          k_scale_pow2_down=args.k_scale_pow2_down,
          rta_ptr_addr=NM.RTA_L1_BASE_PTR,
          bank_table=NM.DRAM_BANK_TO_NOC_XY, noc_id=1, x_addr=NM.MY_X, y_addr=NM.MY_Y)
        emit_signal_kv_score_preamble(fw)
      score_writer_preamble = _score_writer_preamble
      score_writer_extra = lambda _x, _y: [
        k_cache_buf.addr, k_t_buf.addr, args.kv_head, nb, v_cache_buf.addr, v_buf.addr,
      ]
    else:
      kv_stage_prog = kvstage.build_rowmajor_kv_stage_program(
        k_cache_buf.addr, k_t_buf.addr, v_cache_buf.addr, v_buf.addr,
        args.kv_head, nb, core=core, seq=args.seq, max_seq=args.max_seq,
        k_n_cols=Np, v_n_cols=VNp, k_dst_pages=k_t_pages, v_dst_pages=v_pages,
        k_scale_pow2_down=args.k_scale_pow2_down)
      kv_stage_prog.name = "attn_gqa_kv_to_kt_v"

    score_prog = mm.build_program(
      score_chunk.plan, a_buf.addr, k_t_buf.addr, scores_buf.addr, nb, score_layout,
      reader_preamble=score_reader_preamble,
      writer_preamble=score_writer_preamble,
      writer_arg_extra=score_writer_extra)
    score_prog.name = "attn_gqa_score_gemv_kv_preamble" if args.fuse_kv_score else "attn_gqa_score_gemv"
    softmax_prog = kvstage.build_masked_softmax_program(
      scores_buf.addr, probs_buf.addr, nb, core=core,
      tiles=score_tiles, pos=args.pos, mask_rows=GROUP,
      score_scale_pow2_down=args.score_scale_pow2_down)
    softmax_prog.name = "attn_gqa_masked_softmax"
    v_layout = mm.TensorLayout(
      m_tile_offset=v_chunk.m_tile_offset,
      n_tile_offset=v_chunk.n_tile_offset,
      a_row_stride=Np // TILE,
      b_row_stride=VNp // TILE,
      c_row_stride=VNp // TILE,
    )
    v_prog = mm.build_program(
      v_chunk.plan, probs_buf.addr, v_buf.addr, ctx_buf.addr, nb, v_layout,
      output_tile_hook=make_group_wo_input_hook(q_base=q_base),
      writer_arg_extra=lambda _x, _y: [wo_in_buf.addr],
    )
    v_prog.name = "attn_gqa_weighted_v_to_wo"
    programs = (
      (*q_programs, score_prog, softmax_prog, v_prog)
      if args.fuse_kv_score else
      (*q_programs, kv_stage_prog, score_prog, softmax_prog, v_prog)
    )

    times = []
    for run in range(args.runs):
      device.dram_write(a_buf, b"\0" * a_buf.size)
      device.dram_write(wo_in_buf, b"\0" * wo_in_buf.size)
      for prog in programs:
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        times.extend(device.run(prog))

    a_raw = device.dram_read(a_buf)
    k_t_raw = device.dram_read(k_t_buf)
    v_raw = device.dram_read(v_buf)
    scores_raw = device.dram_read(scores_buf)
    probs_raw = device.dram_read(probs_buf)
    ctx_raw = device.dram_read(ctx_buf)
    wo_raw = device.dram_read(wo_in_buf)

  a_ok = bool(np.allclose(mm.from_bf16_device_bytes(a_raw, (Mp, Kp)),
                          a_expected, atol=5.0e-2, rtol=5.0e-2))
  k_ok = k_t_raw == mm.to_bf16_device_bytes(k_t_expected)
  v_ok = v_raw == mm.to_bf16_device_bytes(v_expected)
  scores = mm.from_bf16_device_bytes(scores_raw, (Mp, Np))[:GROUP, :args.seq]
  score_ok = bool(np.allclose(scores, ref_scores, atol=1.0e-1, rtol=1.0e-1))

  ref_softmax_input = np.zeros((score_tiles, TILE, TILE), dtype=np.float32)
  softmax_scores = ref_scores.copy()
  if args.score_scale_pow2_down:
    softmax_scores = mm.from_bf16_device_bytes(
        mm.to_bf16_device_bytes(softmax_scores / np.float32(1 << args.score_scale_pow2_down)),
        softmax_scores.shape)
  ref_softmax_input[0, :GROUP, :args.seq] = softmax_scores
  ref_softmax_input[0, :GROUP, args.pos + 1:args.seq] = -100.0
  ref_prob_tiles = softmax.ref_softmax(ref_softmax_input)
  ref_probs = mm.from_bf16_device_bytes(softmax.to_bf16_bytes(ref_prob_tiles), (Mp, Np))[:GROUP, :args.seq]
  probs = mm.from_bf16_device_bytes(probs_raw, (Mp, Np))[:GROUP, :args.seq]
  prob_ok = bool(np.allclose(probs, ref_probs, atol=softmax.ATOL, rtol=softmax.RTOL))
  causal_ok = bool(np.allclose(probs[:, args.pos + 1:args.seq],
                               ref_probs[:, args.pos + 1:args.seq],
                               atol=softmax.ATOL, rtol=softmax.RTOL))
  ref_ctx = ref_probs @ v_cache[args.kv_head, :args.seq, :]
  full_ctx = mm.from_bf16_device_bytes(ctx_raw, (VMp, VNp))[:, :HEAD_DIM]
  ctx_rows = [row * 2 for row in range(GROUP)]
  ctx = full_ctx[ctx_rows, :HEAD_DIM]
  ctx_ok = bool(np.allclose(ctx, ref_ctx, atol=1.0e-1, rtol=1.0e-1))

  wo = mm.from_bf16_device_bytes(wo_raw, (Mp, args.dim))
  wo_expected = np.zeros((Mp, args.dim), dtype=np.float32)
  for row in range(GROUP):
    start = (q_base + row) * HEAD_DIM
    wo_expected[0, start:start + HEAD_DIM] = ctx[row]
  wo_ok = bool(np.allclose(wo, wo_expected, atol=1.0e-3, rtol=1.0e-3))
  ok = a_ok and k_ok and v_ok and score_ok and prob_ok and causal_ok and ctx_ok and wo_ok

  print("GQA-group staged attention proof")
  print(f"  q_mode={'split' if args.split_q else 'grouped'}")
  print(f"  kv_score={'fused-preamble' if args.fuse_kv_score else 'separate-stage'} k_scale=2^-{args.k_scale_pow2_down} score_scale=2^-{args.score_scale_pow2_down}")
  print(f"  kv_head={args.kv_head} q_heads={q_base}..{q_base + GROUP - 1} pos={args.pos} seq={args.seq} runs={args.runs}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  grouped Q A rows: {'PASS' if a_ok else 'FAIL'}")
  print(f"  staged K^T: {'PASS' if k_ok else 'FAIL'}")
  print(f"  staged V: {'PASS' if v_ok else 'FAIL'}")
  print(f"  grouped scores: {'PASS' if score_ok else 'FAIL'}")
  print(f"  grouped causal mask: {'PASS' if causal_ok else 'FAIL'}")
  print(f"  grouped softmax: {'PASS' if prob_ok else 'FAIL'}")
  print(f"  grouped weighted V: {'PASS' if ctx_ok else 'FAIL'}")
  print(f"  grouped Wo placement: {'PASS' if wo_ok else 'FAIL'}")
  if not score_ok:
    diff = np.abs(scores - ref_scores)
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    score max diff row={r} col={c} got={float(scores[r, c]):.6g} ref={float(ref_scores[r, c]):.6g}")
    for row in range(GROUP):
      row_diff = np.abs(scores[row] - ref_scores[row])
      row_max = int(np.argmax(row_diff))
      row_rel = float(np.linalg.norm(scores[row] - ref_scores[row]) /
                      (np.linalg.norm(ref_scores[row]) + 1e-12))
      nonzero = int(np.count_nonzero(scores[row]))
      print(f"    score row {row}: max_col={row_max} max_diff={float(row_diff[row_max]):.6g} "
            f"rel_l2={row_rel:.4f} nonzero={nonzero}/{args.seq}")
  if not ctx_ok:
    diff = np.abs(ctx - ref_ctx)
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    ctx max diff row={r} col={c} got={float(ctx[r, c]):.6g} ref={float(ref_ctx[r, c]):.6g}")
    for ref_row in range(GROUP):
      errs = [
        float(np.linalg.norm(full_ctx[row] - ref_ctx[ref_row]) / (np.linalg.norm(ref_ctx[ref_row]) + 1e-12))
        for row in range(min(TILE, VMp))
      ]
      best = int(np.argmin(errs))
      print(f"    ref ctx row {ref_row} best matches output row {best} rel_l2={errs[best]:.4f}")
      even = ref_row * 2
      if even < VMp:
        print(f"      output row {even} rel_l2={errs[even]:.4f}")
  if not wo_ok:
    diff = np.abs(wo - wo_expected)
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    Wo max diff row={r} col={c} got={float(wo[r, c]):.6g} ref={float(wo_expected[r, c]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
