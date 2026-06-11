#!/usr/bin/env python3
"""Stage live KV-cache rows into the attention GEMV inputs.

This is the device-side layout bridge for decode attention:

  k_cache[head, pos, dim] row-major -> K^T[dim, pos] GEMV B buffer
  v_cache[head, pos, dim] row-major -> V[pos, dim] GEMV B buffer

It intentionally stays as a BRISC/NOC staging program separate from the score
GEMV, softmax, and weighted-V GEMV programs. That gives the decode path a
stable multi-program attention boundary before considering preamble-style
fusion.
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

from asm import KernelBase  # noqa: E402
from dsl import a0, a1, a2, a5, s0, s1, s2, s3, s4, s5, t0, t1, t2, t3, t4, t5, t6, zero  # noqa: E402
from examples import add1  # noqa: E402
from examples.add1 import Brisc  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.mailbox import NcriscMailbox as NM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402

TILE = 32
HEAD_DIM = 64
PAGE = Dtype.Float16_b.tile_size
ROW_BYTES = HEAD_DIM * Dtype.Float16_b.bpe
ROWS_PER_PAGE = PAGE // ROW_BYTES
SRC_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
DST_L1 = SRC_L1 + PAGE


def packed_elem_offset(row: int, col: int) -> int:
  face = (row // 16) * 2 + (col // 16)
  elem = face * 16 * 16 + (row % 16) * 16 + (col % 16)
  return elem * 2


def bf16_array_scale_pow2_down(a: np.ndarray, shift: int) -> np.ndarray:
  if shift <= 0:
    return a.copy()
  if shift > 8:
    raise ValueError("bf16 scale shift must be in 0..8")
  bits = np.frombuffer(mm.to_bf16_device_bytes(a), dtype=np.uint16).copy()
  exp = bits & np.uint16(0x7F80)
  exp_delta = np.uint16(shift << 7)
  normal = exp > exp_delta
  bits[normal] = (bits[normal] - exp_delta).astype(np.uint16)
  bits[~normal] = bits[~normal] & np.uint16(0x8000)
  return mm.from_bf16_device_bytes(bits.tobytes(), a.shape)


def emit_read_page(fw: Brisc, *, base_reg, page_reg, l1_dst: int,
                   bank_table: int = BM.DRAM_BANK_TO_NOC_XY,
                   noc_id: int = 0,
                   x_addr: int = BM.MY_X,
                   y_addr: int = BM.MY_Y) -> None:
  fw.mv(a0, base_reg)
  fw.mv(a1, page_reg)
  fw.mv(a2, s3)
  fw.dram_tile_addr_from(bank_table, 0)
  fw.local_noc0_coord(a5, x_addr=x_addr, y_addr=y_addr)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (noc_id << NOC.INSTANCE_OFFSET_BIT))
  fw.addi(t4, t4, 1)
  fw.li(t2, l1_dst)
  fw.li(t6, PAGE)
  fw.noc_read(noc_id, 1, a0, 0, a2, t2, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(noc_id, t4, addr=t0, val=t1)


def emit_write_l1_page(fw: Brisc, *, page: int, l1_src: int,
                       bank_table: int = BM.DRAM_BANK_TO_NOC_XY,
                       noc_id: int = 0,
                       x_addr: int = BM.MY_X,
                       y_addr: int = BM.MY_Y) -> None:
  fw.mv(a0, s1)
  fw.li(a1, page)
  fw.mv(a2, s3)
  fw.dram_tile_addr_from(bank_table, 0)
  fw.local_noc0_coord(a5, x_addr=x_addr, y_addr=y_addr)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (noc_id << NOC.INSTANCE_OFFSET_BIT))
  fw.addi(t4, t4, 1)
  fw.li(t2, l1_src)
  fw.li(t6, PAGE)
  fw.noc_write(noc_id, 0, t2, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(noc_id, t4, addr=t0, val=t1)


def emit_zero_dst(fw: Brisc, *, pages: int) -> None:
  loop = fw._new_label("zero_dst_loop")
  fw.li(t0, DST_L1)
  fw.li(t1, DST_L1 + pages * PAGE)
  fw.label(loop)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.bltu(t0, t1, loop)


def emit_bf16_reg_scale_pow2_down(fw: Brisc, value_reg, *, shift: int) -> None:
  if shift <= 0:
    return
  if shift > 8:
    raise ValueError("bf16 scale shift must be in 0..8")
  exp_delta = shift << 7
  normal = fw._new_label("bf16_scale_normal")
  done = fw._new_label("bf16_scale_done")
  fw.li(t1, 0x7F80)
  fw.and_(t2, value_reg, t1)
  fw.li(t1, exp_delta)
  fw.bltu(t1, t2, normal)
  fw.li(t1, 0x8000)
  fw.and_(value_reg, value_reg, t1)
  fw.j(done)
  fw.label(normal)
  fw.addi(value_reg, value_reg, -exp_delta)
  fw.label(done)


def stage_kernel(*, seq: int, max_seq: int, n_cols: int, dst_pages: int) -> Brisc:
  if seq != TILE:
    raise ValueError("this first bridge handles exactly one sequence tile")
  if max_seq % TILE:
    raise ValueError("max_seq must keep head cache regions tile-aligned")
  if n_cols % TILE:
    raise ValueError("GEMV B columns must be tile-aligned")

  fw = Brisc()
  # RTAs: K-cache base, staged K^T destination base, head, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3))
  emit_zero_dst(fw, pages=dst_pages)

  src_pages_per_head = (max_seq // TILE) * (HEAD_DIM // TILE)
  dst_col_tiles = n_cols // TILE
  for dim_tile in range(HEAD_DIM // TILE):
    fw.li(t0, src_pages_per_head)
    fw.mul(t0, s2, t0)
    fw.addi(t0, t0, dim_tile)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=SRC_L1)

    dst_page = dim_tile * dst_col_tiles
    for seq_row in range(TILE):
      for dim_col in range(TILE):
        src_off = packed_elem_offset(seq_row, dim_col)
        dst_off = dst_page * PAGE + packed_elem_offset(dim_col, seq_row)
        fw.li(t1, SRC_L1)
        fw.lhu(t0, t1, src_off)
        fw.li(t2, DST_L1 + dst_off)
        fw.sh(t0, t2, 0)

  for page in range(dst_pages):
    emit_write_l1_page(fw, page=page, l1_src=DST_L1 + page * PAGE)
  fw.ret()
  return fw


def v_stage_kernel(*, seq: int, max_seq: int, n_cols: int, dst_pages: int) -> Brisc:
  if seq != TILE:
    raise ValueError("this first bridge handles exactly one sequence tile")
  if max_seq % TILE:
    raise ValueError("max_seq must keep head cache regions tile-aligned")
  if n_cols % TILE:
    raise ValueError("GEMV B columns must be tile-aligned")

  fw = Brisc()
  # RTAs: V-cache base, staged V destination base, head, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3))
  emit_zero_dst(fw, pages=dst_pages)

  src_pages_per_head = (max_seq // TILE) * (HEAD_DIM // TILE)
  for dim_tile in range(HEAD_DIM // TILE):
    fw.li(t0, src_pages_per_head)
    fw.mul(t0, s2, t0)
    fw.addi(t0, t0, dim_tile)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=SRC_L1)
    emit_write_l1_page(fw, page=dim_tile, l1_src=SRC_L1)
  fw.ret()
  return fw


def rowmajor_stage_kernel(*, seq: int, max_seq: int, n_cols: int, dst_pages: int,
                          seq_start: int = 0,
                          dst_seq_start: int = 0,
                          k_scale_pow2_down: int = 0,
                          zero_dst_pages: bool = True) -> Brisc:
  if seq != TILE:
    raise ValueError("this first bridge handles exactly one sequence tile")
  if seq_start % ROWS_PER_PAGE:
    raise ValueError("seq_start must be row-cache page-aligned")
  if dst_seq_start % ROWS_PER_PAGE:
    raise ValueError("dst_seq_start must be row-cache page-aligned")
  if seq_start < 0 or seq_start + seq > max_seq:
    raise ValueError("seq_start/seq must select rows inside max_seq")
  if dst_seq_start < 0 or dst_seq_start + seq > n_cols:
    raise ValueError("dst_seq_start/seq must select columns inside n_cols")
  if max_seq % ROWS_PER_PAGE:
    raise ValueError("max_seq must keep head cache regions page-aligned")
  if n_cols % TILE:
    raise ValueError("GEMV B columns must be tile-aligned")

  fw = Brisc()
  # RTAs: row-major K-cache base, staged K^T destination base, head, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3))
  if zero_dst_pages:
    emit_zero_dst(fw, pages=dst_pages)

  src_pages_per_head = max_seq // ROWS_PER_PAGE
  dst_col_tiles = n_cols // TILE
  touched_pages = sorted({
      (dim // TILE) * dst_col_tiles + (seq_col // TILE)
      for seq_col in range(dst_seq_start, dst_seq_start + seq)
      for dim in range(HEAD_DIM)
  })
  start_page_in_head = seq_start // ROWS_PER_PAGE
  for src_page_in_head in range(seq // ROWS_PER_PAGE):
    fw.li(t0, src_pages_per_head)
    fw.mul(t0, s2, t0)
    fw.addi(t0, t0, start_page_in_head + src_page_in_head)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=SRC_L1)

    for row_in_page in range(ROWS_PER_PAGE):
      seq_col = dst_seq_start + src_page_in_head * ROWS_PER_PAGE + row_in_page
      for dim in range(HEAD_DIM):
        src_off = row_in_page * ROW_BYTES + dim * Dtype.Float16_b.bpe
        dst_page = (dim // TILE) * dst_col_tiles + (seq_col // TILE)
        dst_off = dst_page * PAGE + packed_elem_offset(dim % TILE, seq_col % TILE)
        fw.li(t1, SRC_L1)
        fw.lhu(t0, t1, src_off)
        emit_bf16_reg_scale_pow2_down(fw, t0, shift=k_scale_pow2_down)
        fw.li(t2, DST_L1 + dst_off)
        fw.sh(t0, t2, 0)

  for page in (range(dst_pages) if zero_dst_pages else touched_pages):
    emit_write_l1_page(fw, page=page, l1_src=DST_L1 + page * PAGE)
  fw.ret()
  return fw


def rowmajor_v_stage_kernel(*, seq: int, max_seq: int, n_cols: int, dst_pages: int,
                            seq_start: int = 0,
                            dst_seq_start: int = 0,
                            zero_dst_pages: bool = True) -> Brisc:
  if seq != TILE:
    raise ValueError("this first bridge handles exactly one sequence tile")
  if seq_start % ROWS_PER_PAGE:
    raise ValueError("seq_start must be row-cache page-aligned")
  if dst_seq_start % ROWS_PER_PAGE:
    raise ValueError("dst_seq_start must be row-cache page-aligned")
  if seq_start < 0 or seq_start + seq > max_seq:
    raise ValueError("seq_start/seq must select rows inside max_seq")
  if dst_seq_start < 0 or dst_seq_start + seq > n_cols:
    raise ValueError("dst_seq_start/seq must select rows inside n_cols")
  if max_seq % ROWS_PER_PAGE:
    raise ValueError("max_seq must keep head cache regions page-aligned")
  if n_cols % TILE:
    raise ValueError("GEMV B columns must be tile-aligned")

  fw = Brisc()
  # RTAs: row-major V-cache base, staged V destination base, head, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3))
  if zero_dst_pages:
    emit_zero_dst(fw, pages=dst_pages)

  src_pages_per_head = max_seq // ROWS_PER_PAGE
  dst_col_tiles = n_cols // TILE
  touched_pages = sorted({
      (seq_row // TILE) * dst_col_tiles + (dim // TILE)
      for seq_row in range(dst_seq_start, dst_seq_start + seq)
      for dim in range(HEAD_DIM)
  })
  start_page_in_head = seq_start // ROWS_PER_PAGE
  for src_page_in_head in range(seq // ROWS_PER_PAGE):
    fw.li(t0, src_pages_per_head)
    fw.mul(t0, s2, t0)
    fw.addi(t0, t0, start_page_in_head + src_page_in_head)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=SRC_L1)

    for row_in_page in range(ROWS_PER_PAGE):
      seq_row = dst_seq_start + src_page_in_head * ROWS_PER_PAGE + row_in_page
      for dim in range(HEAD_DIM):
        src_off = row_in_page * ROW_BYTES + dim * Dtype.Float16_b.bpe
        dst_page = (seq_row // TILE) * dst_col_tiles + (dim // TILE)
        dst_off = dst_page * PAGE + packed_elem_offset(seq_row % TILE, dim % TILE)
        fw.li(t1, SRC_L1)
        fw.lhu(t0, t1, src_off)
        fw.li(t2, DST_L1 + dst_off)
        fw.sh(t0, t2, 0)

  for page in (range(dst_pages) if zero_dst_pages else touched_pages):
    emit_write_l1_page(fw, page=page, l1_src=DST_L1 + page * PAGE)
  fw.ret()
  return fw


def rowmajor_kv_stage_kernel(*, seq: int, max_seq: int, k_n_cols: int, v_n_cols: int,
                             k_dst_pages: int, v_dst_pages: int,
                             seq_start: int = 0,
                             dst_seq_start: int = 0,
                             k_scale_pow2_down: int = 0,
                             zero_dst_pages: bool = True) -> Brisc:
  if seq != TILE:
    raise ValueError("this first bridge handles exactly one sequence tile")
  if seq_start % ROWS_PER_PAGE:
    raise ValueError("seq_start must be row-cache page-aligned")
  if dst_seq_start % ROWS_PER_PAGE:
    raise ValueError("dst_seq_start must be row-cache page-aligned")
  if seq_start < 0 or seq_start + seq > max_seq:
    raise ValueError("seq_start/seq must select rows inside max_seq")
  if dst_seq_start < 0 or dst_seq_start + seq > min(k_n_cols, v_n_cols):
    raise ValueError("dst_seq_start/seq must select rows/columns inside K/V destinations")
  if max_seq % ROWS_PER_PAGE:
    raise ValueError("max_seq must keep head cache regions page-aligned")
  if k_n_cols % TILE or v_n_cols % TILE:
    raise ValueError("GEMV B columns must be tile-aligned")

  fw = Brisc()
  # RTAs: K src, K^T dst, head, banks, V src, V dst.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5))
  emit_rowmajor_kv_stage_body(
      fw, seq=seq, max_seq=max_seq, k_n_cols=k_n_cols, v_n_cols=v_n_cols,
      k_dst_pages=k_dst_pages, v_dst_pages=v_dst_pages,
      seq_start=seq_start, dst_seq_start=dst_seq_start,
      k_scale_pow2_down=k_scale_pow2_down,
      zero_dst_pages=zero_dst_pages)
  fw.ret()
  return fw


def emit_rowmajor_kv_stage_body(fw, *, seq: int, max_seq: int, k_n_cols: int, v_n_cols: int,
                                k_dst_pages: int, v_dst_pages: int,
                                seq_start: int = 0,
                                dst_seq_start: int = 0,
                                k_scale_pow2_down: int = 0,
                                zero_dst_pages: bool = True,
                                bank_table: int = BM.DRAM_BANK_TO_NOC_XY,
                                noc_id: int = 0,
                                x_addr: int = BM.MY_X,
                                y_addr: int = BM.MY_Y) -> None:
  if seq != TILE:
    raise ValueError("this first bridge handles exactly one sequence tile")
  if seq_start % ROWS_PER_PAGE:
    raise ValueError("seq_start must be row-cache page-aligned")
  if dst_seq_start % ROWS_PER_PAGE:
    raise ValueError("dst_seq_start must be row-cache page-aligned")
  if seq_start < 0 or seq_start + seq > max_seq:
    raise ValueError("seq_start/seq must select rows inside max_seq")
  if dst_seq_start < 0 or dst_seq_start + seq > min(k_n_cols, v_n_cols):
    raise ValueError("dst_seq_start/seq must select rows/columns inside K/V destinations")
  if max_seq % ROWS_PER_PAGE:
    raise ValueError("max_seq must keep head cache regions page-aligned")
  if k_n_cols % TILE or v_n_cols % TILE:
    raise ValueError("GEMV B columns must be tile-aligned")

  src_pages_per_head = max_seq // ROWS_PER_PAGE
  k_dst_col_tiles = k_n_cols // TILE
  k_touched_pages = sorted({
      (dim // TILE) * k_dst_col_tiles + (seq_col // TILE)
      for seq_col in range(dst_seq_start, dst_seq_start + seq)
      for dim in range(HEAD_DIM)
  })
  if zero_dst_pages:
    emit_zero_dst(fw, pages=k_dst_pages)
  start_page_in_head = seq_start // ROWS_PER_PAGE
  for src_page_in_head in range(seq // ROWS_PER_PAGE):
    fw.li(t0, src_pages_per_head)
    fw.mul(t0, s2, t0)
    fw.addi(t0, t0, start_page_in_head + src_page_in_head)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=SRC_L1,
                   bank_table=bank_table, noc_id=noc_id, x_addr=x_addr, y_addr=y_addr)

    for row_in_page in range(ROWS_PER_PAGE):
      seq_col = dst_seq_start + src_page_in_head * ROWS_PER_PAGE + row_in_page
      for dim in range(HEAD_DIM):
        src_off = row_in_page * ROW_BYTES + dim * Dtype.Float16_b.bpe
        dst_page = (dim // TILE) * k_dst_col_tiles + (seq_col // TILE)
        dst_off = dst_page * PAGE + packed_elem_offset(dim % TILE, seq_col % TILE)
        fw.li(t1, SRC_L1)
        fw.lhu(t0, t1, src_off)
        emit_bf16_reg_scale_pow2_down(fw, t0, shift=k_scale_pow2_down)
        fw.li(t2, DST_L1 + dst_off)
        fw.sh(t0, t2, 0)

  for page in (range(k_dst_pages) if zero_dst_pages else k_touched_pages):
    emit_write_l1_page(fw, page=page, l1_src=DST_L1 + page * PAGE,
                       bank_table=bank_table, noc_id=noc_id, x_addr=x_addr, y_addr=y_addr)

  fw.mv(s0, s4)  # V-cache source
  fw.mv(s1, s5)  # V destination
  v_dst_col_tiles = v_n_cols // TILE
  v_touched_pages = sorted({
      (seq_row // TILE) * v_dst_col_tiles + (dim // TILE)
      for seq_row in range(dst_seq_start, dst_seq_start + seq)
      for dim in range(HEAD_DIM)
  })
  if zero_dst_pages:
    emit_zero_dst(fw, pages=v_dst_pages)
  for src_page_in_head in range(seq // ROWS_PER_PAGE):
    fw.li(t0, src_pages_per_head)
    fw.mul(t0, s2, t0)
    fw.addi(t0, t0, start_page_in_head + src_page_in_head)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=SRC_L1,
                   bank_table=bank_table, noc_id=noc_id, x_addr=x_addr, y_addr=y_addr)

    for row_in_page in range(ROWS_PER_PAGE):
      seq_row = dst_seq_start + src_page_in_head * ROWS_PER_PAGE + row_in_page
      for dim in range(HEAD_DIM):
        src_off = row_in_page * ROW_BYTES + dim * Dtype.Float16_b.bpe
        dst_page = (seq_row // TILE) * v_dst_col_tiles + (dim // TILE)
        dst_off = dst_page * PAGE + packed_elem_offset(seq_row % TILE, dim % TILE)
        fw.li(t1, SRC_L1)
        fw.lhu(t0, t1, src_off)
        fw.li(t2, DST_L1 + dst_off)
        fw.sh(t0, t2, 0)

  for page in (range(v_dst_pages) if zero_dst_pages else v_touched_pages):
    emit_write_l1_page(fw, page=page, l1_src=DST_L1 + page * PAGE,
                       bank_table=bank_table, noc_id=noc_id, x_addr=x_addr, y_addr=y_addr)


def emit_rowmajor_kv_stage_preamble(fw, *, seq: int, max_seq: int,
                                    k_n_cols: int, v_n_cols: int,
                                    k_dst_pages: int, v_dst_pages: int,
                                    rta_offset: int,
                                    seq_start: int = 0,
                                    dst_seq_start: int = 0,
                                    k_scale_pow2_down: int = 0,
                                    zero_dst_pages: bool = True,
                                    rta_ptr_addr: int = BM.RTA_L1_BASE_PTR,
                                    bank_table: int = BM.DRAM_BANK_TO_NOC_XY,
                                    noc_id: int = 0,
                                    x_addr: int = BM.MY_X,
                                    y_addr: int = BM.MY_Y) -> None:
  # Extra RTAs: K src, K^T dst, head, bank count, V src, V dst.
  fw.read32(t0, rta_ptr_addr)
  for i, reg in enumerate((s0, s1, s2, s3, s4, s5)):
    fw.lw(reg, t0, (rta_offset + i) * 4)
  emit_rowmajor_kv_stage_body(
      fw, seq=seq, max_seq=max_seq, k_n_cols=k_n_cols, v_n_cols=v_n_cols,
      k_dst_pages=k_dst_pages, v_dst_pages=v_dst_pages, seq_start=seq_start,
      dst_seq_start=dst_seq_start,
      k_scale_pow2_down=k_scale_pow2_down,
      zero_dst_pages=zero_dst_pages,
      bank_table=bank_table, noc_id=noc_id, x_addr=x_addr, y_addr=y_addr)


def build_stage_program(k_cache_addr: int, dst_addr: int, head: int, num_banks: int,
                        *, core, seq: int, max_seq: int, n_cols: int,
                        dst_pages: int) -> Program:
  brisc_fw = stage_kernel(seq=seq, max_seq=max_seq, n_cols=n_cols, dst_pages=dst_pages)
  brisc_fw.rta(lambda _x, _y: [k_cache_addr, dst_addr, head, num_banks])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_k_cache_to_kt"
  return prog


def build_v_stage_program(v_cache_addr: int, dst_addr: int, head: int, num_banks: int,
                          *, core, seq: int, max_seq: int, n_cols: int,
                          dst_pages: int) -> Program:
  brisc_fw = v_stage_kernel(seq=seq, max_seq=max_seq, n_cols=n_cols, dst_pages=dst_pages)
  brisc_fw.rta(lambda _x, _y: [v_cache_addr, dst_addr, head, num_banks])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_v_cache_to_v"
  return prog


def build_rowmajor_stage_program(k_cache_addr: int, dst_addr: int, head: int, num_banks: int,
                                 *, core, seq: int, max_seq: int, n_cols: int,
                                 dst_pages: int, seq_start: int = 0,
                                 dst_seq_start: int = 0,
                                 k_scale_pow2_down: int = 0,
                                 zero_dst_pages: bool = True) -> Program:
  brisc_fw = rowmajor_stage_kernel(
      seq=seq, max_seq=max_seq, n_cols=n_cols, dst_pages=dst_pages,
      seq_start=seq_start, dst_seq_start=dst_seq_start,
      k_scale_pow2_down=k_scale_pow2_down,
      zero_dst_pages=zero_dst_pages)
  brisc_fw.rta(lambda _x, _y: [k_cache_addr, dst_addr, head, num_banks])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_rowmajor_k_cache_to_kt"
  return prog


def build_rowmajor_v_stage_program(v_cache_addr: int, dst_addr: int, head: int, num_banks: int,
                                   *, core, seq: int, max_seq: int, n_cols: int,
                                   dst_pages: int, seq_start: int = 0,
                                   dst_seq_start: int = 0,
                                   zero_dst_pages: bool = True) -> Program:
  brisc_fw = rowmajor_v_stage_kernel(
      seq=seq, max_seq=max_seq, n_cols=n_cols, dst_pages=dst_pages,
      seq_start=seq_start, dst_seq_start=dst_seq_start,
      zero_dst_pages=zero_dst_pages)
  brisc_fw.rta(lambda _x, _y: [v_cache_addr, dst_addr, head, num_banks])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_rowmajor_v_cache_to_v"
  return prog


def build_rowmajor_kv_stage_program(k_cache_addr: int, k_dst_addr: int,
                                    v_cache_addr: int, v_dst_addr: int,
                                    head: int, num_banks: int, *, core,
                                    seq: int, max_seq: int,
                                    k_n_cols: int, v_n_cols: int,
                                    k_dst_pages: int, v_dst_pages: int,
                                    seq_start: int = 0,
                                    dst_seq_start: int = 0,
                                    k_scale_pow2_down: int = 0,
                                    zero_dst_pages: bool = True) -> Program:
  brisc_fw = rowmajor_kv_stage_kernel(
      seq=seq, max_seq=max_seq, k_n_cols=k_n_cols, v_n_cols=v_n_cols,
      k_dst_pages=k_dst_pages, v_dst_pages=v_dst_pages,
      seq_start=seq_start, dst_seq_start=dst_seq_start,
      k_scale_pow2_down=k_scale_pow2_down,
      zero_dst_pages=zero_dst_pages)
  brisc_fw.rta(lambda _x, _y: [k_cache_addr, k_dst_addr, head, num_banks, v_cache_addr, v_dst_addr])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_rowmajor_kv_cache_to_kt_v"
  return prog


def _emit_scale_bf16_pow2_down(fw: Brisc, tile_ptr, *, rows: int, shift: int) -> None:
  if shift <= 0:
    return
  exp_delta = shift << 7
  row_loop = fw._new_label("score_scale_row")
  row_done = fw._new_label("score_scale_row_done")
  fw.li(t3, 0)
  fw.label(row_loop)
  fw.li(t1, rows)
  fw.beq(t3, t1, row_done)
  for face in (0, 1):
    elem_loop = fw._new_label("score_scale_elem")
    elem_done = fw._new_label("score_scale_elem_done")
    normal = fw._new_label("score_scale_normal")
    done = fw._new_label("score_scale_done")
    fw.li(t4, face * 16 * 16 * 2)
    fw.add(t4, tile_ptr, t4)
    fw.slli(t6, t3, 5)
    fw.add(t4, t4, t6)
    fw.li(t6, 16)
    fw.label(elem_loop)
    fw.beq(t6, zero, elem_done)
    fw.lhu(t0, t4, 0)
    fw.li(t1, 0x7F80)
    fw.and_(t2, t0, t1)
    fw.li(t1, exp_delta)
    fw.bltu(t1, t2, normal)
    fw.li(t1, 0x8000)
    fw.and_(t0, t0, t1)
    fw.j(done)
    fw.label(normal)
    fw.addi(t0, t0, -exp_delta)
    fw.label(done)
    fw.sh(t0, t4, 0)
    fw.addi(t4, t4, 2)
    fw.addi(t6, t6, -1)
    fw.j(elem_loop)
    fw.label(elem_done)
  fw.addi(t3, t3, 1)
  fw.j(row_loop)
  fw.label(row_done)


def masked_softmax_brisc(*, pos: int, mask_rows: int = 1,
                         score_scale_pow2_down: int = 0) -> Brisc:
  if not 1 <= mask_rows <= TILE:
    raise ValueError("mask_rows must select 1..32 tile rows")
  if score_scale_pow2_down < 0 or score_scale_pow2_down > 8:
    raise ValueError("score_scale_pow2_down must be in 0..8")
  fw = Brisc()
  # RTAs: scores base, first tile offset, tiles, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    add1.SYNC_TRISC_START, add1.SYNC_READ, add1.SYNC_DONE0, add1.SYNC_DONE1,
    add1.SYNC_DONE2, add1.SYNC_TRISC_INIT, add1.SYNC_TRISC_INIT + 4,
    add1.SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
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
    fw.li(t6, PAGE)
    fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
    fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    read_wait = fw._new_label("brisc_read_wait")
    fw.label(read_wait)
    fw.lw(t1, t0, 0)
    fw.bltu(t1, t4, read_wait)
    fw.fence()

    _emit_scale_bf16_pow2_down(
        fw, t5, rows=mask_rows, shift=score_scale_pow2_down)

    if pos < TILE - 1:
      skip_mask = fw._new_label("skip_causal_mask")
      fw.bne(s5, zero, skip_mask)
      fw.li(t0, 0xC2C8)  # bf16(-100.0), enough to zero masked exp terms.
      for row in range(mask_rows):
        for col in range(pos + 1, TILE):
          fw.addi(t2, t5, packed_elem_offset(row, col))
          fw.sh(t0, t2, 0)
      fw.label(skip_mask)

    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(add1.SYNC_READ, t2)
  return fw


def build_masked_softmax_program(src_addr: int, dst_addr: int, num_banks: int, *,
                                 core, tiles: int, pos: int,
                                 mask_rows: int = 1,
                                 score_scale_pow2_down: int = 0) -> Program:
  brisc_fw = masked_softmax_brisc(
      pos=pos, mask_rows=mask_rows,
      score_scale_pow2_down=score_scale_pow2_down)
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = add1.trisc0()
  trisc1_fw = softmax.trisc1()
  trisc2_fw = add1.trisc2()
  brisc_fw.rta(lambda _x, _y: [src_addr, 0, tiles, num_banks])
  ncrisc_fw.rta(lambda _x, _y: [dst_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])
  prog = Program(
    brisc=brisc_fw, ncrisc=ncrisc_fw,
    trisc0=trisc0_fw, trisc1=trisc1_fw, trisc2=trisc2_fw,
    cbs=[(0, PAGE, add1.CB_DEPTH), (add1.OUT_CB, PAGE, add1.CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_masked_softmax"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="stage KV cache into attention GEMV inputs; needs device")
  p.add_argument("--head-dim", type=int, default=HEAD_DIM)
  p.add_argument("--heads", type=int, default=8)
  p.add_argument("--head", type=int, default=3)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--seq", type=int, default=32)
  p.add_argument("--seq-start", type=int, default=0,
                 help="row-major cache start position for the staged 32-token tile")
  p.add_argument("--dst-seq-start", type=int, default=None,
                 help="destination sequence offset inside staged K^T/V buffers; defaults to 0")
  p.add_argument("--total-seq", type=int, default=None,
                 help="total staged attention width/depth; defaults to --seq")
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--row-major-cache", action="store_true",
                 help="stage from the raw row-major KV-cache layout used by examples/llama3.py")
  p.add_argument("--fuse-kv-stage", action="store_true",
                 help="with --row-major-cache, stage K^T and V in one launch")
  p.add_argument("--score-scale-pow2-down", type=int, default=0,
                 help="scale scores by 2^-N in the softmax BRISC feeder")
  p.add_argument("--k-scale-pow2-down", type=int, default=0,
                 help="scale staged K values by 2^-N before score GEMV")
  p.add_argument("--score-only", action="store_true",
                 help="stop after K/V staging and score GEMV; useful before cross-tile softmax exists")
  p.add_argument("--stage-prefix", action="store_true",
                 help="with --score-only, stage every 32-token tile from 0..total_seq before score GEMV")
  p.add_argument("--verbose", action="store_true")
  args = p.parse_args()
  total_seq = args.total_seq if args.total_seq is not None else args.seq
  dst_seq_start = args.dst_seq_start if args.dst_seq_start is not None else 0
  score_only = bool(args.score_only or args.stage_prefix or total_seq != args.seq)
  if args.head_dim != HEAD_DIM:
    raise ValueError("this bridge currently assumes head_dim=64")
  if args.seq != TILE:
    raise ValueError("this first proof expects --seq 32; longer seq needs cross-tile softmax")
  if total_seq % TILE:
    raise ValueError("--total-seq must be tile-aligned")
  if args.max_seq < args.seq:
    raise ValueError("--max-seq must be >= --seq")
  if not 0 <= args.head < args.heads:
    raise ValueError("--head must select one of --heads")
  if args.seq_start % ROWS_PER_PAGE:
    raise ValueError("--seq-start must be row-cache page-aligned")
  if dst_seq_start % ROWS_PER_PAGE:
    raise ValueError("--dst-seq-start must be row-cache page-aligned")
  if args.seq_start < 0 or args.seq_start + args.seq > args.max_seq:
    raise ValueError("--seq-start + --seq must fit inside --max-seq")
  if dst_seq_start < 0 or dst_seq_start + args.seq > total_seq:
    raise ValueError("--dst-seq-start + --seq must fit inside --total-seq")
  if args.stage_prefix and (not args.row_major_cache or total_seq > args.max_seq):
    raise ValueError("--stage-prefix requires --row-major-cache and --total-seq <= --max-seq")
  local_pos = args.pos - args.seq_start
  if score_only:
    if not 0 <= args.pos < total_seq:
      raise ValueError("--pos must select a position inside --total-seq")
  elif not 0 <= local_pos < args.seq:
    raise ValueError("--pos must select a live position inside the staged sequence tile")
  if args.max_seq % TILE:
    raise ValueError("--max-seq must keep each head cache region tile-aligned")

  rng = np.random.default_rng(223)
  q = rng.uniform(-0.5, 0.5, size=(1, args.head_dim)).astype(np.float32)
  k_cache = rng.uniform(-0.5, 0.5, size=(args.heads, args.max_seq, args.head_dim)).astype(np.float32)
  v_cache = rng.uniform(-0.5, 0.5, size=(args.heads, args.max_seq, args.head_dim)).astype(np.float32)
  q = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(q), q.shape)
  k_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(k_cache), k_cache.shape)
  v_cache = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(v_cache), v_cache.shape)

  stage_spans = (
      [(start, start) for start in range(0, total_seq, TILE)]
      if args.stage_prefix else
      [(args.seq_start, dst_seq_start)]
  )
  ref_b = np.zeros((args.head_dim, total_seq), dtype=np.float32)
  v_expected_rows = np.zeros((total_seq, args.head_dim), dtype=np.float32)
  for src_start, dst_start in stage_spans:
    k_rows = k_cache[args.head, src_start:src_start + args.seq, :]
    staged_k_rows = bf16_array_scale_pow2_down(k_rows, args.k_scale_pow2_down)
    v_rows = v_cache[args.head, src_start:src_start + args.seq, :]
    ref_b[:args.head_dim, dst_start:dst_start + args.seq] = staged_k_rows.T
    v_expected_rows[dst_start:dst_start + args.seq, :] = v_rows
  ref_scores_all = (q @ ref_b[:args.head_dim, :total_seq]).reshape(-1)
  ref_scores = ref_scores_all.copy()
  if not score_only:
    ref_scores[local_pos + 1:] = -100.0

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    chunks = mm.plan_output_chunks(1, args.head_dim, total_seq, cores, nb)
    Mp, Kp, Np = mm.global_padded_shape(1, args.head_dim, args.seq, chunks)
    if Kp != args.head_dim:
      raise RuntimeError(f"unexpected K padding for this proof: Kp={Kp}")
    dst_pages = (Kp * Np * 2) // PAGE
    tiles = (Mp // TILE) * (Np // TILE)
    v_chunks = mm.plan_output_chunks(1, total_seq, args.head_dim, cores, nb)
    if len(chunks) != 1 or len(v_chunks) != 1:
      raise ValueError("this first proof expects one GEMV chunk for scores and V")
    VMp, VKp, VNp = mm.global_padded_shape(1, args.seq, args.head_dim, v_chunks)
    if VMp != Mp or VKp > Np:
      raise ValueError(f"softmax output shape {(Mp, Np)} cannot feed V GEMV {(VMp, VKp)}")
    v_dst_pages = (VKp * VNp * 2) // PAGE

    a_padded = np.zeros((Mp, Kp), dtype=np.float32)
    a_padded[:1, :args.head_dim] = q
    b_expected = np.zeros((Kp, Np), dtype=np.float32)
    b_expected[:args.head_dim, :total_seq] = ref_b[:args.head_dim, :total_seq]
    v_expected = np.zeros((VKp, VNp), dtype=np.float32)
    v_expected[:total_seq, :args.head_dim] = v_expected_rows

    q_buf = device.alloc_write(mm.to_bf16_device_bytes(a_padded), dtype=Dtype.Float16_b,
                               shape=(Mp, Kp), name="attn_q")
    if args.row_major_cache:
      cache_pages = (args.heads * args.max_seq * args.head_dim * Dtype.Float16_b.bpe) // PAGE
      k_cache_buf = device.dram.alloc(cache_pages, dtype=Dtype.Float16_b, name="k_cache_rowmajor")
      v_cache_buf = device.dram.alloc(cache_pages, dtype=Dtype.Float16_b, name="v_cache_rowmajor")
      device.dram_write(k_cache_buf, mm.to_bf16_device_bytes(k_cache))
      device.dram_write(v_cache_buf, mm.to_bf16_device_bytes(v_cache))
    else:
      k_cache_buf = device.alloc_write(mm.to_bf16_device_bytes(k_cache), dtype=Dtype.Float16_b,
                                       shape=k_cache.shape, name="k_cache")
      v_cache_buf = device.alloc_write(mm.to_bf16_device_bytes(v_cache), dtype=Dtype.Float16_b,
                                       shape=v_cache.shape, name="v_cache")
    b_buf = device.dram.alloc(dst_pages, dtype=Dtype.Float16_b, shape=(Kp, Np), name="attn_k_t")
    v_buf = device.dram.alloc(v_dst_pages, dtype=Dtype.Float16_b, shape=(VKp, VNp), name="attn_v")
    scores_buf = device.dram.alloc(tiles, dtype=Dtype.Float16_b, shape=(Mp, Np), name="attn_scores")
    probs_buf = device.dram.alloc(tiles, dtype=Dtype.Float16_b,
                                  shape=(tiles, TILE, TILE), name="attn_probs")
    ctx_buf = device.dram.alloc((VMp // TILE) * (VNp // TILE), dtype=Dtype.Float16_b,
                                shape=(VMp, VNp), name="attn_ctx")

    if args.fuse_kv_stage and not args.row_major_cache:
      raise ValueError("--fuse-kv-stage is only defined for --row-major-cache")
    stage_programs = []
    if args.fuse_kv_stage:
      for stage_i, (src_start, dst_start) in enumerate(stage_spans):
        stage_prog = build_rowmajor_kv_stage_program(
          k_cache_buf.addr, b_buf.addr, v_cache_buf.addr, v_buf.addr,
          args.head, nb, core=core, seq=args.seq, max_seq=args.max_seq,
          k_n_cols=Np, v_n_cols=VNp, k_dst_pages=dst_pages, v_dst_pages=v_dst_pages,
          seq_start=src_start, dst_seq_start=dst_start,
          k_scale_pow2_down=args.k_scale_pow2_down,
          zero_dst_pages=(stage_i == 0),
        )
        stage_prog.name = (
            f"attn_rowmajor_kv_cache_to_kt_v_s{src_start}_d{dst_start}"
            if args.stage_prefix else stage_prog.name)
        stage_programs.append(stage_prog)
    else:
      k_builder = build_rowmajor_stage_program if args.row_major_cache else build_stage_program
      v_builder = build_rowmajor_v_stage_program if args.row_major_cache else build_v_stage_program
      if not args.row_major_cache and args.k_scale_pow2_down:
        raise ValueError("--k-scale-pow2-down is only implemented for --row-major-cache")
      for stage_i, (src_start, dst_start) in enumerate(stage_spans):
        stage_kwargs = {"seq_start": src_start} if args.row_major_cache else {}
        if args.row_major_cache:
          stage_kwargs["k_scale_pow2_down"] = args.k_scale_pow2_down
          stage_kwargs["dst_seq_start"] = dst_start
          stage_kwargs["zero_dst_pages"] = stage_i == 0
        stage_prog = k_builder(
          k_cache_buf.addr, b_buf.addr, args.head, nb, core=core,
          seq=args.seq, max_seq=args.max_seq, n_cols=Np, dst_pages=dst_pages,
          **stage_kwargs,
        )
        v_stage_prog = v_builder(
          v_cache_buf.addr, v_buf.addr, args.head, nb, core=core,
          seq=args.seq, max_seq=args.max_seq, n_cols=VNp, dst_pages=v_dst_pages,
          **stage_kwargs,
        )
        if args.stage_prefix:
          stage_prog.name = f"attn_rowmajor_k_cache_to_kt_s{src_start}_d{dst_start}"
          v_stage_prog.name = f"attn_rowmajor_v_cache_to_v_s{src_start}_d{dst_start}"
        stage_programs.extend((stage_prog, v_stage_prog))
    layout_base = dict(a_row_stride=Kp // TILE, b_row_stride=Np // TILE, c_row_stride=Np // TILE)
    gemv_progs = []
    for i, chunk in enumerate(chunks):
      layout = mm.TensorLayout(
        m_tile_offset=chunk.m_tile_offset,
        n_tile_offset=chunk.n_tile_offset,
        **layout_base,
      )
      prog = mm.build_program(chunk.plan, q_buf.addr, b_buf.addr, scores_buf.addr, nb, layout)
      prog.name = "attn_staged_score_gemv" if len(chunks) == 1 else f"attn_staged_score_gemv_c{i}"
      gemv_progs.append(prog)
    softmax_prog = build_masked_softmax_program(
        scores_buf.addr, probs_buf.addr, nb, core=core, tiles=tiles, pos=local_pos,
        score_scale_pow2_down=args.score_scale_pow2_down)
    softmax_prog.name = "attn_staged_score_softmax"
    v_chunk = v_chunks[0]
    v_layout = mm.TensorLayout(
      m_tile_offset=v_chunk.m_tile_offset,
      n_tile_offset=v_chunk.n_tile_offset,
      a_row_stride=Np // TILE,
      b_row_stride=VNp // TILE,
      c_row_stride=VNp // TILE,
    )
    v_prog = mm.build_program(v_chunk.plan, probs_buf.addr, v_buf.addr, ctx_buf.addr, nb, v_layout)
    v_prog.name = "attn_staged_weighted_v_gemv"
    if score_only:
      programs = (*stage_programs, *gemv_progs)
    else:
      if len(stage_programs) not in (1, 2):
        raise ValueError("attention-chain mode expects one staged tile")
      programs = (
        (*stage_programs, *gemv_progs, softmax_prog, v_prog)
      )

    times = []
    for _ in range(args.runs):
      for prog in programs:
        if args.verbose:
          print(f"  running {prog.name}", flush=True)
        times.extend(device.run(prog))

    staged_raw = device.dram_read(b_buf)
    staged_v_raw = device.dram_read(v_buf)
    scores_raw = device.dram_read(scores_buf)
    probs_raw = device.dram_read(probs_buf) if not score_only else None
    ctx_raw = device.dram_read(ctx_buf) if not score_only else None

  staged_ok = staged_raw == mm.to_bf16_device_bytes(b_expected)
  staged_v_ok = staged_v_raw == mm.to_bf16_device_bytes(v_expected)
  score_matrix = mm.from_bf16_device_bytes(scores_raw, (Mp, Np))
  scores = score_matrix[0, :total_seq]
  if score_only:
    probs = ref_probs = ctx = ref_ctx = None
    prob_ok = ctx_ok = causal_ok = True
    score_ok = bool(np.allclose(scores, ref_scores_all[:total_seq], atol=1.0e-1, rtol=1.0e-1))
  else:
    prob_matrix = mm.from_bf16_device_bytes(probs_raw, (Mp, Np))
    ctx_matrix = mm.from_bf16_device_bytes(ctx_raw, (VMp, VNp))
    probs = prob_matrix[0, :args.seq]
    ctx = ctx_matrix[0, :args.head_dim]
    ref_softmax_input = np.zeros((tiles, TILE, TILE), dtype=np.float32)
    softmax_scores = scores[:args.seq].copy()
    if args.score_scale_pow2_down:
      softmax_scores = mm.from_bf16_device_bytes(
          mm.to_bf16_device_bytes(softmax_scores / np.float32(1 << args.score_scale_pow2_down)),
          softmax_scores.shape)
    ref_softmax_input[0, 0, :args.seq] = softmax_scores
    ref_softmax_input[0, 0, local_pos + 1:args.seq] = -100.0
    ref_prob_tiles = softmax.ref_softmax(ref_softmax_input)
    ref_probs = mm.from_bf16_device_bytes(softmax.to_bf16_bytes(ref_prob_tiles), (Mp, Np))[0, :args.seq]
    ref_ctx = (ref_probs.reshape(1, args.seq) @ v_rows).reshape(-1)
    score_ok = bool(np.allclose(scores[:local_pos + 1], ref_scores_all[:local_pos + 1], atol=1.0e-1, rtol=1.0e-1))
    prob_ok = bool(np.allclose(probs, ref_probs, atol=softmax.ATOL, rtol=softmax.RTOL))
    ctx_ok = bool(np.allclose(ctx, ref_ctx, atol=1.0e-1, rtol=1.0e-1))
    causal_ok = bool(np.allclose(probs[local_pos + 1:args.seq], 0.0, atol=softmax.ATOL, rtol=softmax.RTOL))
  ok = staged_ok and staged_v_ok and score_ok and prob_ok and causal_ok and ctx_ok

  print("attention KV-cache stage -> score GEMV + softmax + weighted V")
  cache_layout = "row-major" if args.row_major_cache else "tilized"
  print(f"  heads={args.heads} head={args.head} head_dim={args.head_dim} seq_start={args.seq_start} dst_seq_start={dst_seq_start} seq={args.seq} total_seq={total_seq} pos={args.pos} max_seq={args.max_seq}")
  print(f"  cache_layout={cache_layout} kv_stage={'fused' if args.fuse_kv_stage else 'split'} k_scale=2^-{args.k_scale_pow2_down} score_scale=2^-{args.score_scale_pow2_down}")
  print(f"  mode={'score-only' if score_only else 'attention-chain'}")
  if args.stage_prefix:
    print(f"  staged_prefix_tiles={len(stage_spans)}")
  print(f"  runs={args.runs} k_staged_pages={dst_pages} v_staged_pages={v_dst_pages} score_tiles={tiles}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  staged K^T bytes: {'PASS' if staged_ok else 'FAIL'}")
  print(f"  staged V bytes: {'PASS' if staged_v_ok else 'FAIL'}")
  print(f"  scores: {'PASS' if score_ok else 'FAIL'}")
  if score_only:
    print("  causal mask: SKIP (cross-tile softmax not implemented)")
    print("  softmax(row0, causal/scaled): SKIP (cross-tile softmax not implemented)")
    print("  weighted V: SKIP (cross-tile softmax not implemented)")
  else:
    print(f"  causal mask: {'PASS' if causal_ok else 'FAIL'}")
    print(f"  softmax(row0, causal/scaled): {'PASS' if prob_ok else 'FAIL'}")
    print(f"  weighted V: {'PASS' if ctx_ok else 'FAIL'}")
  if not staged_ok:
    got = np.frombuffer(staged_raw, dtype=np.uint16)
    exp = np.frombuffer(mm.to_bf16_device_bytes(b_expected), dtype=np.uint16)
    bad = np.flatnonzero(got != exp)
    i = int(bad[0]) if bad.size else -1
    print(f"    first staged mismatch elem={i} got=0x{int(got[i]):04x} exp=0x{int(exp[i]):04x}")
    print("    first staged elems:",
          " ".join(f"{j}:0x{int(got[j]):04x}/0x{int(exp[j]):04x}" for j in range(min(16, got.size))))
  if not staged_v_ok:
    got = np.frombuffer(staged_v_raw, dtype=np.uint16)
    exp = np.frombuffer(mm.to_bf16_device_bytes(v_expected), dtype=np.uint16)
    bad = np.flatnonzero(got != exp)
    i = int(bad[0]) if bad.size else -1
    print(f"    first staged-V mismatch elem={i} got=0x{int(got[i]):04x} exp=0x{int(exp[i]):04x}")
  if not score_ok:
    score_end = total_seq if score_only else local_pos + 1
    diff = np.abs(scores[:score_end] - ref_scores_all[:score_end])
    i = int(np.argmax(diff))
    print(f"    score max diff i={i} got={float(scores[i]):.6g} ref={float(ref_scores_all[i]):.6g}")
  if not score_only and not causal_ok:
    tail = probs[local_pos + 1:args.seq]
    i = int(np.argmax(np.abs(tail))) + local_pos + 1 if tail.size else local_pos
    print(f"    causal tail max i={i} prob={float(probs[i]):.6g}")
  if not score_only and not prob_ok:
    diff = np.abs(probs - ref_probs)
    i = int(np.argmax(diff))
    print(f"    prob max diff i={i} got={float(probs[i]):.6g} ref={float(ref_probs[i]):.6g}")
  if not score_only and not ctx_ok:
    diff = np.abs(ctx - ref_ctx)
    i = int(np.argmax(diff))
    print(f"    ctx max diff i={i} got={float(ctx[i]):.6g} ref={float(ref_ctx[i]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
