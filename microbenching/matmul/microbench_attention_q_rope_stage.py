#!/usr/bin/env python3
"""Stage and RoPE-rotate one Q head into attention score GEMV A.

This bridges the remaining Q-side host fallback before attention integration:

  QKV C row0 Q head + cos/sin[pos] -> RoPE SFPU -> score_gemv_A row0

The proof keeps Q staging and RoPE as separate programs for stability. K^T is
supplied in GEMV layout so the final score GEMV validates that the rotated Q
buffer can be consumed directly by attention.
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
import microbench_rope_k_scatter as rope  # noqa: E402
import numpy as np

from asm import KernelBase  # noqa: E402
from dsl import a0, a1, a2, a3, a5, s0, s1, s2, s3, s4, s5, s6, s7, t0, t1, t2, t3, t4, t5, t6, zero  # noqa: E402
from examples import add1  # noqa: E402
from examples.add1 import CB_DEPTH, OUT_CB, TILE_BYTES, Brisc  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402

TILE = 32
HEAD_DIM = 64
PAGE = Dtype.Float16_b.tile_size
SRC_Q0_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
SRC_Q1_L1 = SRC_Q0_L1 + PAGE
COS_L1 = SRC_Q1_L1 + PAGE
SIN_L1 = COS_L1 + PAGE
DST_L1 = SIN_L1 + PAGE
SCRATCH_L1 = add1.SYNC_L1 + 0x100
TILE_ROW0_COL16_OFF = 16 * 16 * 2


def row0_offset(lane: int) -> int:
  if lane < 16:
    return lane * 2
  return TILE_ROW0_COL16_OFF + (lane - 16) * 2


def row_tile_table(x: np.ndarray) -> np.ndarray:
  tiles = np.zeros((x.shape[0], TILE, TILE), dtype=np.float32)
  tiles[:, 0, :] = x
  return tiles


def emit_read_page(fw: Brisc, *, base_reg, page_reg, bank_reg, l1_dst: int) -> None:
  fw.mv(a0, base_reg)
  fw.mv(a1, page_reg)
  fw.mv(a2, bank_reg)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, l1_dst)
  fw.li(t6, PAGE)
  fw.noc_read(0, 1, a0, 0, a2, t2, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(0, t4, addr=t0, val=t1)


def emit_write_page(fw: Brisc, *, dst_base_reg, page: int, bank_reg, l1_src: int = DST_L1) -> None:
  fw.mv(a0, dst_base_reg)
  fw.li(a1, page)
  fw.mv(a2, bank_reg)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, l1_src)
  fw.li(t6, PAGE)
  fw.noc_write(0, 0, t2, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(0, t4, addr=t0, val=t1)


def emit_zero_l1(fw: Brisc, *, base: int, pages: int) -> None:
  loop = fw._new_label("zero_l1_loop")
  fw.li(t0, base)
  fw.li(t1, base + pages * PAGE)
  fw.label(loop)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.bltu(t0, t1, loop)


def emit_copy_group(fw: Brisc, *, src_l1: int, dst_base_row: int) -> None:
  for lane in range(TILE):
    row = dst_base_row + lane // 8
    col = (lane & 7) * 2
    fw.li(t1, src_l1)
    fw.lhu(t0, t1, row0_offset(lane))
    fw.li(t2, DST_L1 + rope.packed_elem_offset(row, col))
    fw.sh(t0, t2, 0)


def emit_q_rope_src_stage_body(fw: Brisc) -> None:
  emit_read_page(fw, base_reg=s0, page_reg=s4, bank_reg=a3, l1_dst=SRC_Q0_L1)
  fw.addi(t0, s4, 1)
  emit_read_page(fw, base_reg=s0, page_reg=t0, bank_reg=a3, l1_dst=SRC_Q1_L1)
  emit_read_page(fw, base_reg=s1, page_reg=s5, bank_reg=a3, l1_dst=COS_L1)
  emit_read_page(fw, base_reg=s2, page_reg=s5, bank_reg=a3, l1_dst=SIN_L1)

  emit_zero_l1(fw, base=DST_L1, pages=1)
  emit_copy_group(fw, src_l1=SRC_Q0_L1, dst_base_row=rope.X1_OFF)
  emit_copy_group(fw, src_l1=SRC_Q1_L1, dst_base_row=rope.X2_OFF)
  emit_copy_group(fw, src_l1=COS_L1, dst_base_row=rope.COS_OFF)
  emit_copy_group(fw, src_l1=SIN_L1, dst_base_row=rope.SIN_OFF)
  emit_write_page(fw, dst_base_reg=s3, page=0, bank_reg=a3)


def q_rope_src_stage_kernel() -> Brisc:
  fw = Brisc()
  # RTAs: QKV C base, cos table base, sin table base, RoPE src dst, q_start_tile, pos, banks.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5, a3))
  emit_q_rope_src_stage_body(fw)
  fw.ret()
  return fw


def build_q_rope_src_stage_program(c_addr: int, cos_addr: int, sin_addr: int, dst_addr: int,
                                   q_head: int, pos: int, num_banks: int, *, core) -> Program:
  brisc_fw = q_rope_src_stage_kernel()
  brisc_fw.rta(lambda _x, _y: [
    c_addr, cos_addr, sin_addr, dst_addr,
    q_head * (HEAD_DIM // TILE),
    pos() if callable(pos) else pos,
    num_banks,
  ])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_q_rope_src_stage"
  return prog


def row_tile_offset(row: int, lane: int) -> int:
  return rope.packed_elem_offset(row, lane)


def emit_compact_group_to_row_tile(fw, *, l1_tile, base_row: int,
                                   scratch_page: int, dst_row: int = 0) -> None:
  for lane in range(TILE):
    row = base_row + lane // 8
    col = (lane & 7) * 2
    fw.lhu(t1, l1_tile, rope.packed_elem_offset(row, col))
    fw.li(t2, SCRATCH_L1 + scratch_page * PAGE + row_tile_offset(dst_row, lane))
    fw.sh(t1, t2, 0)


def emit_compact_group_to_dynamic_row_tile(fw, *, l1_tile, base_row: int,
                                           scratch_page: int, dst_row_reg) -> None:
  """Compact a RoPE footprint group into a dynamic row inside scratch pages 0/1."""
  for lane in range(TILE):
    row = base_row + lane // 8
    col = (lane & 7) * 2
    row0_off = row_tile_offset(0, lane)
    fw.lhu(t1, l1_tile, rope.packed_elem_offset(row, col))
    fw.slli(t3, dst_row_reg, 5)  # rows 0..15 are 32 bytes apart in packed tiles.
    fw.li(t2, SCRATCH_L1 + scratch_page * PAGE + row0_off)
    fw.add(t2, t2, t3)
    fw.sh(t1, t2, 0)


def emit_read_a_page_to_scratch(fw, *, page: int) -> None:
  fw.mv(a0, s0)
  fw.li(a1, page)
  fw.mv(a2, s4)
  fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s4)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(a3, SCRATCH_L1 + page * PAGE)
  fw.li(t6, PAGE)
  fw.noc_read(0, 1, a0, 0, a2, a3, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(0, t4, addr=t0, val=t1)


def ncrisc_q_to_a(*, dst_row: int = 0, preserve_a: bool = False) -> add1.Ncrisc:
  if not 0 <= dst_row < TILE:
    raise ValueError("dst_row must select a row inside the destination tile")
  if preserve_a:
    raise ValueError("preserve_a read-modify-write is not stable; assemble grouped Q rows separately")
  fw = add1.Ncrisc()
  # RTAs: attention A base, tiles, bank count.
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s3, s4))
  with fw.tile_loop("ncrisc"):
    fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
    fw.cb_read_ptr(NM.CB_INTERFACE, OUT_CB, out=t5)

    # The loop runs once today; fill A pages 0/1 with rotated x1/x2.
    if preserve_a:
      for page in range(2):
        emit_read_a_page_to_scratch(fw, page=page)
    else:
      fw.li(t0, SCRATCH_L1)
      fw.li(t1, SCRATCH_L1 + 2 * PAGE)
      fw.label("q_a_zero_loop")
      fw.sw(zero, t0, 0)
      fw.addi(t0, t0, 4)
      fw.bltu(t0, t1, "q_a_zero_loop")
    emit_compact_group_to_row_tile(
        fw, l1_tile=t5, base_row=rope.X1_OFF, scratch_page=0, dst_row=dst_row)
    emit_compact_group_to_row_tile(
        fw, l1_tile=t5, base_row=rope.X2_OFF, scratch_page=1, dst_row=dst_row)

    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
    fw.addi(t4, t4, 2)
    for page in range(2):
      fw.mv(a0, s0)
      fw.li(a1, page)
      fw.mv(a2, s4)
      fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s4)
      fw.li(a3, SCRATCH_L1 + page * PAGE)
      fw.li(a5, PAGE)
      fw.noc_write(1, 0, a3, a0, 0, a2, a5, a=t0, v=t1)
    fw.noc_write_barrier(1, t4, addr=t0, val=t1)
    fw.cb_pop_front(NM.CB_INTERFACE, OUT_CB)
  return fw


def build_q_rope_to_a_program(src_addr: int, a_addr: int, num_banks: int, *,
                              core, dst_row: int = 0,
                              preserve_a: bool = False) -> Program:
  brisc_fw = add1.brisc()
  ncrisc_fw = ncrisc_q_to_a(dst_row=dst_row, preserve_a=preserve_a)
  trisc0_fw = add1.trisc0()
  trisc1_fw = rope.trisc1_rope()
  trisc2_fw = add1.trisc2()

  brisc_fw.rta(lambda _x, _y: [src_addr, 0, 1, num_banks])
  ncrisc_fw.rta(lambda _x, _y: [a_addr, 1, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [1])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_q_rope_to_score_a"
  return prog


def ncrisc_group_q_to_a() -> add1.Ncrisc:
  fw = add1.Ncrisc()
  # RTAs: grouped attention A base, Q rows, bank count.
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s3, s4))

  fw.li(t0, SCRATCH_L1)
  fw.li(t1, SCRATCH_L1 + 2 * PAGE)
  fw.label("group_q_a_zero_loop")
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.bltu(t0, t1, "group_q_a_zero_loop")

  fw.li(s5, 0)
  fw.label("group_q_a_loop")
  fw.beq(s5, s3, "group_q_a_write")
  fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
  fw.cb_read_ptr(NM.CB_INTERFACE, OUT_CB, out=t5)
  emit_compact_group_to_dynamic_row_tile(
      fw, l1_tile=t5, base_row=rope.X1_OFF, scratch_page=0, dst_row_reg=s5)
  emit_compact_group_to_dynamic_row_tile(
      fw, l1_tile=t5, base_row=rope.X2_OFF, scratch_page=1, dst_row_reg=s5)
  fw.cb_pop_front(NM.CB_INTERFACE, OUT_CB)
  fw.addi(s5, s5, 1)
  fw.j("group_q_a_loop")

  fw.label("group_q_a_write")
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.addi(t4, t4, 2)
  for page in range(2):
    fw.mv(a0, s0)
    fw.li(a1, page)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s4)
    fw.li(a3, SCRATCH_L1 + page * PAGE)
    fw.li(a5, PAGE)
    fw.noc_write(1, 0, a3, a0, 0, a2, a5, a=t0, v=t1)
  fw.noc_write_barrier(1, t4, addr=t0, val=t1)
  fw.ret()
  return fw


def q_rope_group_stage_to_a_brisc(group: int = 4) -> Brisc:
  fw = Brisc()
  # RTAs: QKV C base, cos table base, sin table base, RoPE src dst, q_base_tile, pos, banks.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5, a3))
  for addr in (
    add1.SYNC_TRISC_START, add1.SYNC_READ, add1.SYNC_DONE0, add1.SYNC_DONE1,
    add1.SYNC_DONE2, add1.SYNC_TRISC_INIT, add1.SYNC_TRISC_INIT + 4,
    add1.SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(add1.SYNC_TRISC_START, 0x00010101)

  fw.mv(s7, s4)
  fw.li(s6, 0)
  fw.label("brisc_group_q_loop")
  fw.li(t0, group)
  fw.beq(s6, t0, "brisc_group_q_done")

  fw.slli(t0, s6, 1)  # HEAD_DIM / TILE pages per Q head.
  fw.add(s4, s7, t0)
  emit_q_rope_src_stage_body(fw)

  # Reuse the standard add1 reader protocol, feeding the staged RoPE source tile.
  fw.cb_reserve_back(BM.CB_INTERFACE, 0)
  fw.li(a1, 0)
  fw.mv(a0, s3)
  fw.mv(a2, a3)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
  fw.li(t6, TILE_BYTES)
  fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.label("brisc_group_q_read_wait")
  fw.lw(t1, t0, 0)
  fw.bltu(t1, t4, "brisc_group_q_read_wait")
  fw.fence()
  fw.cb_push_back(BM.CB_INTERFACE, 0)
  fw.addi(t2, s6, 1)
  fw.signal_sync(add1.SYNC_READ, t2)

  fw.addi(s6, s6, 1)
  fw.j("brisc_group_q_loop")
  fw.label("brisc_group_q_done")
  fw.ret()
  return fw


def build_q_rope_group_stage_to_a_program(c_addr: int, cos_addr: int, sin_addr: int,
                                          src_addr: int, a_addr: int, q_base: int,
                                          pos: int, num_banks: int, *, core,
                                          group: int = 4) -> Program:
  if group != 4:
    raise ValueError("grouped Q RoPE proof currently expects four Q heads")
  brisc_fw = q_rope_group_stage_to_a_brisc(group=group)
  ncrisc_fw = ncrisc_group_q_to_a()
  trisc0_fw = add1.trisc0()
  trisc1_fw = rope.trisc1_rope()
  trisc2_fw = add1.trisc2()

  brisc_fw.rta(lambda _x, _y: [
    c_addr, cos_addr, sin_addr, src_addr,
    q_base * (HEAD_DIM // TILE),
    pos() if callable(pos) else pos,
    num_banks,
  ])
  ncrisc_fw.rta(lambda _x, _y: [a_addr, group, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [group])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_q_group_stage_rope_to_score_a"
  return prog


def q_rope_stage_to_a_brisc() -> Brisc:
  fw = Brisc()
  # RTAs: QKV C base, cos table base, sin table base, RoPE src dst, q_start_tile, pos, banks.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5, a3))
  for addr in (
    add1.SYNC_TRISC_START, add1.SYNC_READ, add1.SYNC_DONE0, add1.SYNC_DONE1,
    add1.SYNC_DONE2, add1.SYNC_TRISC_INIT, add1.SYNC_TRISC_INIT + 4,
    add1.SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)

  emit_q_rope_src_stage_body(fw)

  # Reuse the standard add1 reader protocol, but feed the tile staged above.
  fw.mv(s0, s3)
  fw.li(s2, 0)
  fw.li(s3, 1)
  fw.mv(s4, a3)
  fw.write32(add1.SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.add(a1, s2, s5)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.local_noc0_coord(a5)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.addi(t4, t4, 1)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
    fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.label("brisc_read_wait")
    fw.lw(t1, t0, 0)
    fw.bltu(t1, t4, "brisc_read_wait")
    fw.fence()
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(add1.SYNC_READ, t2)
  return fw


def build_q_rope_stage_to_a_program(c_addr: int, cos_addr: int, sin_addr: int,
                                    src_addr: int, a_addr: int, q_head: int,
                                    pos: int, num_banks: int, *, core,
                                    dst_row: int = 0,
                                    preserve_a: bool = False) -> Program:
  brisc_fw = q_rope_stage_to_a_brisc()
  ncrisc_fw = ncrisc_q_to_a(dst_row=dst_row, preserve_a=preserve_a)
  trisc0_fw = add1.trisc0()
  trisc1_fw = rope.trisc1_rope()
  trisc2_fw = add1.trisc2()

  brisc_fw.rta(lambda _x, _y: [
    c_addr, cos_addr, sin_addr, src_addr,
    q_head * (HEAD_DIM // TILE),
    pos() if callable(pos) else pos,
    num_banks,
  ])
  ncrisc_fw.rta(lambda _x, _y: [a_addr, 1, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [1])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_q_stage_rope_to_score_a"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="stage + RoPE Q head into attention A; needs device")
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--head-dim", type=int, default=HEAD_DIM)
  p.add_argument("--heads", type=int, default=32)
  p.add_argument("--q-head", type=int, default=7)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--seq", type=int, default=32)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--split", action="store_true", help="run old two-launch Q-stage + Q-RoPE path")
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
  if args.pos >= args.max_seq:
    raise ValueError("--pos must be < --max-seq")

  rng = np.random.default_rng(233)
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
  k_t = rope.to_bf16(rng.uniform(-0.5, 0.5, size=(HEAD_DIM, args.seq)).astype(np.float32))
  ref_scores = (q_rot.reshape(1, HEAD_DIM) @ k_t).reshape(-1)

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
    a_expected[0, :HEAD_DIM] = q_rot
    b_padded = np.zeros((Kp, Np), dtype=np.float32)
    b_padded[:HEAD_DIM, :args.seq] = k_t

    c_buf = device.alloc_write(mm.to_bf16_device_bytes(c), dtype=Dtype.Float16_b,
                               shape=c.shape, name="qkv_c")
    cos_buf = device.alloc_write(rope.to_bf16_bytes(row_tile_table(cos_table)),
                                 dtype=Dtype.Float16_b,
                                 shape=(args.max_seq, TILE, TILE), name="cos_rows")
    sin_buf = device.alloc_write(rope.to_bf16_bytes(row_tile_table(sin_table)),
                                 dtype=Dtype.Float16_b,
                                 shape=(args.max_seq, TILE, TILE), name="sin_rows")
    rope_src_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, shape=(1, TILE, TILE), name="q_rope_src")
    a_buf = device.dram.alloc((Mp // TILE) * (Kp // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Kp), name="attn_q_a")
    b_buf = device.alloc_write(mm.to_bf16_device_bytes(b_padded), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="attn_k_t")
    scores_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b,
                                   shape=(Mp, Np), name="attn_scores")
    device.dram_write(rope_src_buf, b"\0" * rope_src_buf.size)
    device.dram_write(a_buf, b"\0" * a_buf.size)

    if args.split:
      stage_prog = build_q_rope_src_stage_program(
        c_buf.addr, cos_buf.addr, sin_buf.addr, rope_src_buf.addr,
        args.q_head, args.pos, nb, core=core,
      )
      rope_prog = build_q_rope_to_a_program(rope_src_buf.addr, a_buf.addr, nb, core=core)
      q_programs = (stage_prog, rope_prog)
    else:
      fused_prog = build_q_rope_stage_to_a_program(
        c_buf.addr, cos_buf.addr, sin_buf.addr, rope_src_buf.addr, a_buf.addr,
        args.q_head, args.pos, nb, core=core,
      )
      q_programs = (fused_prog,)
    layout = mm.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    score_prog = mm.build_program(chunk.plan, a_buf.addr, b_buf.addr, scores_buf.addr, nb, layout)
    score_prog.name = "attn_q_rope_score_gemv"
    programs = (*q_programs, score_prog)

    times = []
    for _ in range(args.runs):
      for prog in programs:
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        times.extend(device.run(prog))

    src_raw = device.dram_read(rope_src_buf)
    a_raw = device.dram_read(a_buf)
    scores_raw = device.dram_read(scores_buf)

  expected_src = np.zeros((1, TILE, TILE), dtype=np.float32)
  rope.footprint_put(expected_src[0], rope.X1_OFF, q[:32])
  rope.footprint_put(expected_src[0], rope.X2_OFF, q[32:])
  rope.footprint_put(expected_src[0], rope.COS_OFF, cos)
  rope.footprint_put(expected_src[0], rope.SIN_OFF, sin)
  src_ok = src_raw == rope.to_bf16_bytes(expected_src)
  staged_ok = bool(np.allclose(
    mm.from_bf16_device_bytes(a_raw, (Mp, Kp)), a_expected, atol=5.0e-2, rtol=5.0e-2))
  score_matrix = mm.from_bf16_device_bytes(scores_raw, (Mp, Np))
  scores = score_matrix[0, :args.seq]
  score_ok = bool(np.allclose(scores, ref_scores, atol=1.0e-1, rtol=1.0e-1))
  ok = src_ok and staged_ok and score_ok

  print("attention Q stage + RoPE -> score GEMV")
  print(f"  mode={'split' if args.split else 'fused'}")
  print(f"  q_head={args.q_head} pos={args.pos} head_dim={args.head_dim} seq={args.seq} runs={args.runs}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  RoPE source footprint: {'PASS' if src_ok else 'FAIL'}")
  print(f"  rotated Q A: {'PASS' if staged_ok else 'FAIL'}")
  print(f"  scores: {'PASS' if score_ok else 'FAIL'}")
  if not staged_ok:
    got = mm.from_bf16_device_bytes(a_raw, (Mp, Kp))[0, :HEAD_DIM]
    diff = np.abs(got - q_rot)
    i = int(np.argmax(diff))
    print(f"    Q max diff i={i} got={float(got[i]):.6g} ref={float(q_rot[i]):.6g}")
  if not score_ok:
    diff = np.abs(scores - ref_scores)
    i = int(np.argmax(diff))
    print(f"    score max diff i={i} got={float(scores[i]):.6g} ref={float(ref_scores[i]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
