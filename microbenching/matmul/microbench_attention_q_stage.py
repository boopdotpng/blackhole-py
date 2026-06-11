#!/usr/bin/env python3
"""Stage a Q head from QKV GEMV output into attention score GEMV A.

The integrated decode path currently reads QKV back to host before splitting Q.
This bridge proves the device-side handoff for one Q head:

  qkv_c[row0, q_head*64:(q_head+1)*64] -> score_gemv_A[row0, :64]

It intentionally leaves Q RoPE for the next bridge. K^T is supplied in GEMV
layout here so this proof only exercises the QKV-C-buffer -> attention-A
handoff plus score GEMV consumption.
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
import numpy as np

from asm import KernelBase  # noqa: E402
from dsl import a0, a1, a2, a5, s0, s1, s2, s3, t0, t1, t2, t4, t5, t6, zero  # noqa: E402
from examples.add1 import Brisc  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402

TILE = 32
HEAD_DIM = 64
PAGE = Dtype.Float16_b.tile_size
SRC_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
DST_L1 = SRC_L1 + PAGE
TILE_ROW0_COL16_OFF = 16 * 16 * 2


def row0_offset(lane: int) -> int:
  if lane < 16:
    return lane * 2
  return TILE_ROW0_COL16_OFF + (lane - 16) * 2


def emit_read_page(fw: Brisc, *, base_reg, page_reg, l1_dst: int) -> None:
  fw.mv(a0, base_reg)
  fw.mv(a1, page_reg)
  fw.mv(a2, s3)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, l1_dst)
  fw.li(t6, PAGE)
  fw.noc_read(0, 1, a0, 0, a2, t2, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(0, t4, addr=t0, val=t1)


def emit_write_page(fw: Brisc, *, page: int) -> None:
  fw.mv(a0, s1)
  fw.li(a1, page)
  fw.mv(a2, s3)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, DST_L1 + page * PAGE)
  fw.li(t6, PAGE)
  fw.noc_write(0, 0, t2, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(0, t4, addr=t0, val=t1)


def emit_zero_dst(fw: Brisc, *, pages: int) -> None:
  loop = fw._new_label("zero_dst_loop")
  fw.li(t0, DST_L1)
  fw.li(t1, DST_L1 + pages * PAGE)
  fw.label(loop)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.bltu(t0, t1, loop)


def q_stage_kernel(*, q_head: int, a_pages: int) -> Brisc:
  fw = Brisc()
  # RTAs: QKV C base, attention A destination base, q_start_tile, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3))
  emit_zero_dst(fw, pages=a_pages)

  for tile in range(HEAD_DIM // TILE):
    fw.addi(t0, s2, tile)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=SRC_L1)
    for lane in range(TILE):
      fw.li(t1, SRC_L1)
      fw.lhu(t0, t1, row0_offset(lane))
      fw.li(t2, DST_L1 + tile * PAGE + row0_offset(lane))
      fw.sh(t0, t2, 0)

  for page in range(a_pages):
    emit_write_page(fw, page=page)
  fw.ret()
  return fw


def build_q_stage_program(c_addr: int, a_addr: int, q_head: int, num_banks: int,
                          *, core, a_pages: int) -> Program:
  brisc_fw = q_stage_kernel(q_head=q_head, a_pages=a_pages)
  brisc_fw.rta(lambda _x, _y: [c_addr, a_addr, q_head * (HEAD_DIM // TILE), num_banks])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_qkv_q_to_score_a"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="stage Q head from QKV C into attention A; needs device")
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--head-dim", type=int, default=HEAD_DIM)
  p.add_argument("--heads", type=int, default=32)
  p.add_argument("--q-head", type=int, default=7)
  p.add_argument("--seq", type=int, default=32)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--verbose", action="store_true")
  args = p.parse_args()
  if args.head_dim != HEAD_DIM:
    raise ValueError("this proof currently assumes head_dim=64")
  if args.heads * args.head_dim != args.dim:
    raise ValueError("heads * head_dim must equal dim")
  if not 0 <= args.q_head < args.heads:
    raise ValueError("--q-head must select one Q head")
  if args.seq != TILE:
    raise ValueError("this first proof expects --seq 32")

  rng = np.random.default_rng(229)
  qkv_n = args.dim + 2 * args.kv_dim
  qkv_n_padded = ((qkv_n + TILE - 1) // TILE) * TILE
  qkv = rng.uniform(-2.0, 2.0, size=qkv_n_padded).astype(np.float32)
  qkv = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(qkv), qkv.shape)
  q = qkv[args.q_head * HEAD_DIM:(args.q_head + 1) * HEAD_DIM]
  k_t = rng.uniform(-0.5, 0.5, size=(HEAD_DIM, args.seq)).astype(np.float32)
  k_t = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(k_t), k_t.shape)
  ref_scores = (q.reshape(1, HEAD_DIM) @ k_t).reshape(-1)

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    chunks = mm.plan_output_chunks(1, HEAD_DIM, args.seq, cores, nb)
    if len(chunks) != 1:
      raise ValueError("this first proof expects one score GEMV chunk")
    chunk = chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(1, HEAD_DIM, args.seq, chunks)
    if Kp != HEAD_DIM:
      raise RuntimeError(f"unexpected K padding: Kp={Kp}")

    c = np.zeros((TILE, qkv_n_padded), dtype=np.float32)
    c[0, :] = qkv
    a_expected = np.zeros((Mp, Kp), dtype=np.float32)
    a_expected[0, :HEAD_DIM] = q
    b_padded = np.zeros((Kp, Np), dtype=np.float32)
    b_padded[:HEAD_DIM, :args.seq] = k_t

    c_buf = device.alloc_write(mm.to_bf16_device_bytes(c), dtype=Dtype.Float16_b,
                               shape=c.shape, name="qkv_c")
    a_buf = device.dram.alloc((Mp // TILE) * (Kp // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Kp), name="attn_q_a")
    b_buf = device.alloc_write(mm.to_bf16_device_bytes(b_padded), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="attn_k_t")
    scores_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b,
                                   shape=(Mp, Np), name="attn_scores")
    q_stage_prog = build_q_stage_program(
      c_buf.addr, a_buf.addr, args.q_head, nb, core=core,
      a_pages=(Mp // TILE) * (Kp // TILE),
    )
    layout = mm.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    score_prog = mm.build_program(chunk.plan, a_buf.addr, b_buf.addr, scores_buf.addr, nb, layout)
    score_prog.name = "attn_q_staged_score_gemv"
    programs = (q_stage_prog, score_prog)

    times = []
    for _ in range(args.runs):
      for prog in programs:
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        times.extend(device.run(prog))

    a_raw = device.dram_read(a_buf)
    scores_raw = device.dram_read(scores_buf)

  staged_ok = a_raw == mm.to_bf16_device_bytes(a_expected)
  score_matrix = mm.from_bf16_device_bytes(scores_raw, (Mp, Np))
  scores = score_matrix[0, :args.seq]
  score_ok = bool(np.allclose(scores, ref_scores, atol=1.0e-1, rtol=1.0e-1))
  ok = staged_ok and score_ok

  print("attention Q stage -> score GEMV")
  print(f"  q_head={args.q_head} head_dim={args.head_dim} seq={args.seq} runs={args.runs}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  staged Q A bytes: {'PASS' if staged_ok else 'FAIL'}")
  print(f"  scores: {'PASS' if score_ok else 'FAIL'}")
  if not staged_ok:
    got = np.frombuffer(a_raw, dtype=np.uint16)
    exp = np.frombuffer(mm.to_bf16_device_bytes(a_expected), dtype=np.uint16)
    bad = np.flatnonzero(got != exp)
    i = int(bad[0]) if bad.size else -1
    print(f"    first staged-Q mismatch elem={i} got=0x{int(got[i]):04x} exp=0x{int(exp[i]):04x}")
  if not score_ok:
    diff = np.abs(scores - ref_scores)
    i = int(np.argmax(diff))
    print(f"    score max diff i={i} got={float(scores[i]):.6g} ref={float(ref_scores[i]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
