#!/usr/bin/env python3
from __future__ import annotations
import struct
import sys
import time
import matmul_peak as base
import numpy as np

base.MATH_BACKEND = "direct"
base.MATH_FIDELITY = "hifi2" if base.HIFI else "lofi"
base.EXPERIMENTAL_THROTTLE0 = True
base.SUPPORTED_OUT_SUBBLOCK_H = 8
base.SUPPORTED_OUT_SUBBLOCK_W = 1

from asm import KernelBase
from device import Device
from dram import tilize
from drisc_gddr_dma_poc import (
  DMA_CTRL_ATTRS_BURST_255, RESULT_MAGIC, STATUS_DONE, STATUS_STARTED,
  TX_CTRL_TRANSFER_ATTRIBUTES,
)
from drisc_gddr_to_worker_poc import (
  ACK_SCRATCH_ADDR, MAX_NOC_CHUNK_BYTES, RESULT_ADDR, RESULT_WORDS,
  emit_dma_read_reg, emit_dma_read_wait_n, emit_init_drisc_noc_cmd_bufs,
  emit_local_noc_coord, emit_posted_writes_flushed,
  emit_set_drisc_noc2axi_mode_all, emit_set_drisc_stream_mode_all,
)
from drisc_hello import DRISC_FW_BASE, DRISC_L1_NOC_ALIAS, DRISC_RESET_PC, RegWindow, SOFT_RESET_0, SOFT_RESET_BRISC
from dsl import a0, a1, a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, t0, t1, t2, t3, t4, t5, t6, zero
from pcie import TLBWindow
from program import Dtype, Program
from ttk import Noc
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM
from ttk.noc import NOC, noc_xy
from ttk.tensix import TensixL1, TensixMMIO


POC_MAGIC = RESULT_MAGIC ^ 0x4D4D4452  # "RDMM"
TILE_BYTES = base.TILE_BYTES
REQUEST_A = 0x178000
REQUEST_B = 0x179000
DEBUG_BRISC = 0x17A000
DEBUG_NCRISC = 0x17A100
REQ_STATUS = 0x00
REQ_DST = 0x10
REQ_SIZE = 0x20
REQ_SEQ = 0x30
REQ_EMPTY = 0
REQ_READY = 1
REQ_DONE = 2
DRISC_CHUNK_TILES = 6
DRISC_CHUNK_BYTES = DRISC_CHUNK_TILES * TILE_BYTES
FEEDER_GDDR_BASE = 0x10000000
RUNS = base.RUNS
PAYLOAD_NOC_MODE = "split"
USE_ALL_FEEDERS = True
FIXED_5000_PLAN = True
FIXED_5000_N_CHUNKS = 1
FIXED_5000_M_SPLIT_ALL_CORES = False
ACCEPT_CORRUPT_FEEDER_HEADER = False
POLL_FINAL_FEEDER_STATUS = True
ALLOW_FEEDER_TIMEOUT_AFTER_WORKERS_DONE = False
PROFILE_BRISC = base.PROFILE_BASE + 3 * base.PROFILE_RECORD_BYTES
PROFILE_NCRISC = base.PROFILE_BASE + 4 * base.PROFILE_RECORD_BYTES
PROFILE_FEEDER_FIRST_READY_WORD = 8
PROFILE_FEEDER_DONE_WORD = 10


class DriscMatmulFeeder(KernelBase, Noc):
  pass


def _debug_mark(fw: base.MatmulKernel, base_addr: int, code: int, block_reg=s6):
  return fw


def _profile_stamp(fw: KernelBase, addr: int):
  return fw


def _profile_result_stamp(fw: KernelBase, word_index: int):
  return fw


def _request_and_wait(fw: base.MatmulKernel, *, request_addr: int, dst, size: int, seq):
  fw.write32(request_addr + REQ_STATUS, REQ_EMPTY, tmp_addr=t0, tmp_val=t1)
  fw.write32(request_addr + REQ_DST, dst, tmp_addr=t0, tmp_val=t1)
  fw.write32(request_addr + REQ_SIZE, size, tmp_addr=t0, tmp_val=t1)
  fw.write32(request_addr + REQ_SEQ, seq, tmp_addr=t0, tmp_val=t1)
  fw.write32(request_addr + REQ_STATUS, REQ_READY, tmp_addr=t0, tmp_val=t1)
  wait = fw._new_label("wait_drisc_feed")
  fw.label(wait)
  fw.read32(t0, request_addr + REQ_STATUS, tmp_addr=t1)
  fw.li(t2, REQ_DONE)
  fw.bne(t0, t2, wait)
  fw.read32(t0, request_addr + REQ_SEQ, tmp_addr=t1)
  fw.bne(t0, seq, wait)
  return fw


def matmul_reader_sender_drisc(plan: base.MatmulPlan) -> base.MatmulKernel:
  fw = base.MatmulKernel()
  fw.release_triscs()
  fw.rta_ptr(BM.RTA_L1_BASE_PTR)
  fw.arg(s7, 7)   # block_tiles
  fw.arg(s8, 8)   # nblocks
  fw.arg(s9, 18)  # east receiver count
  fw.arg(s10, 13)
  fw.add(s10, s10, s9)

  fw.write32(REQUEST_A + REQ_STATUS, REQ_EMPTY, tmp_addr=t0, tmp_val=t1)
  fw.arg(t0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=t6)
  fw.noc_semaphore_set(t6, 1)

  fw.li(s6, 0)
  _profile_stamp(fw, PROFILE_BRISC)
  _debug_mark(fw, DEBUG_BRISC, 0xA000)
  fw.label("reader_sender_block_loop")
  fw.bne(s6, s8, "reader_sender_block_body")
  fw.j("reader_sender_done")
  fw.label("reader_sender_block_body")
  _debug_mark(fw, DEBUG_BRISC, 0xA001)
  fw.cb_reserve_back(BM.CB_INTERFACE, 0, s7)
  _debug_mark(fw, DEBUG_BRISC, 0xA002)
  fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=s9)
  block_bytes = plan.in0_block_num_tiles * TILE_BYTES
  _request_and_wait(fw, request_addr=REQUEST_A, dst=s9, size=block_bytes, seq=s6)
  _debug_mark(fw, DEBUG_BRISC, 0xA003)

  fw.arg(t0, 21)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=a3)
  fw.noc_semaphore_wait(a3, s10)
  fw.noc_semaphore_set(a3, 0)
  _debug_mark(fw, DEBUG_BRISC, 0xA004)

  fw.arg(t0, 13)
  fw.beq(t0, zero, "reader_sender_skip_west")
  fw.arg(t1, 9)
  fw.arg(t2, 10)
  fw.arg(t3, 11)
  fw.arg(t5, 12)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT)
  fw.lw(a6, t0, 0)
  fw.addi(a6, a6, base._ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(a0, s9)
  base._emit_mcast_chunks(fw, 0, a0, a5, block_bytes)
  fw.noc_nonposted_writes_flushed(0, a6)
  fw.arg(t0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=a4)
  fw.arg(t1, 9)
  fw.arg(t2, 10)
  fw.arg(t3, 11)
  fw.arg(t5, 12)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.noc_semaphore_set_multicast(0, 0, a4, a5, 1, t0, a=t1, v=t2)
  fw.label("reader_sender_skip_west")
  _debug_mark(fw, DEBUG_BRISC, 0xA005)

  fw.arg(t0, 18)
  fw.beq(t0, zero, "reader_sender_skip_east")
  fw.arg(t1, 14)
  fw.arg(t2, 15)
  fw.arg(t3, 16)
  fw.arg(t5, 17)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT)
  fw.lw(a6, t0, 0)
  fw.addi(a6, a6, base._ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(a0, s9)
  base._emit_mcast_chunks(fw, 0, a0, a5, block_bytes)
  fw.noc_nonposted_writes_flushed(0, a6)
  fw.arg(t0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=a4)
  fw.arg(t1, 14)
  fw.arg(t2, 15)
  fw.arg(t3, 16)
  fw.arg(t5, 17)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.noc_semaphore_set_multicast(0, 0, a4, a5, 1, t0, a=t1, v=t2)
  fw.label("reader_sender_skip_east")
  _debug_mark(fw, DEBUG_BRISC, 0xA006)

  fw.cb_push_back(BM.CB_INTERFACE, 0, s7)
  _debug_mark(fw, DEBUG_BRISC, 0xA007)
  fw.addi(s6, s6, 1)
  fw.j("reader_sender_block_loop")
  fw.label("reader_sender_done")
  _debug_mark(fw, DEBUG_BRISC, 0xA0FF)
  _profile_stamp(fw, PROFILE_BRISC + 8)
  return fw.ret()


def matmul_reader_recv_drisc() -> base.MatmulKernel:
  fw = base.MatmulKernel()
  fw.release_triscs()
  fw.rta_ptr(BM.RTA_L1_BASE_PTR)
  fw.arg(s7, 7)
  fw.arg(s8, 8)
  fw.li(s0, 0)
  _profile_stamp(fw, PROFILE_BRISC)
  _debug_mark(fw, DEBUG_BRISC, 0xC000, block_reg=s0)
  fw.label("reader_recv_block_loop")
  fw.beq(s0, s8, "reader_recv_done")
  _debug_mark(fw, DEBUG_BRISC, 0xC001, block_reg=s0)
  fw.cb_reserve_back(BM.CB_INTERFACE, 0, s7)
  _debug_mark(fw, DEBUG_BRISC, 0xC002, block_reg=s0)
  fw.arg(t0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=s1)
  fw.noc_semaphore_set(s1, 0)
  fw.arg(t0, 21)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=s2)
  fw.arg(t1, 19)
  fw.arg(t2, 20)
  fw.noc_coord(a5, t1, t2)
  fw.local_noc0_coord(a6)
  fw.noc_semaphore_inc(0, 3, s2, a5, 1, ret_coord=a6, a=t3, v=t4)
  _debug_mark(fw, DEBUG_BRISC, 0xC003, block_reg=s0)
  fw.noc_semaphore_wait(s1, 1)
  _debug_mark(fw, DEBUG_BRISC, 0xC004, block_reg=s0)
  fw.cb_push_back(BM.CB_INTERFACE, 0, s7)
  _debug_mark(fw, DEBUG_BRISC, 0xC005, block_reg=s0)
  fw.addi(s0, s0, 1)
  fw.j("reader_recv_block_loop")
  fw.label("reader_recv_done")
  _debug_mark(fw, DEBUG_BRISC, 0xC0FF, block_reg=s0)
  _profile_stamp(fw, PROFILE_BRISC + 8)
  return fw.ret()


def matmul_writer_sender_drisc(plan: base.MatmulPlan) -> base.MatmulKernel:
  fw = base.MatmulKernel()
  fw.rta_ptr(NM.RTA_L1_BASE_PTR)
  fw.arg(s7, 7)   # block_tiles
  fw.arg(s8, 8)   # nblocks
  fw.arg(s10, 13) # receiver count

  fw.write32(REQUEST_B + REQ_STATUS, REQ_EMPTY, tmp_addr=t0, tmp_val=t1)
  fw.arg(t0, 17)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=t6)
  fw.noc_semaphore_set(t6, 1)

  fw.li(s6, 0)
  _profile_stamp(fw, PROFILE_NCRISC)
  _debug_mark(fw, DEBUG_NCRISC, 0xB000)
  fw.label("writer_sender_block_loop")
  fw.bne(s6, s8, "writer_sender_block_body")
  fw.j("writer_sender_blocks_done")
  fw.label("writer_sender_block_body")
  _debug_mark(fw, DEBUG_NCRISC, 0xB001)
  fw.cb_reserve_back(NM.CB_INTERFACE, 1, s7)
  _debug_mark(fw, DEBUG_NCRISC, 0xB002)
  fw.cb_write_ptr(NM.CB_INTERFACE, 1, out=s9)
  block_bytes = plan.in1_block_num_tiles * TILE_BYTES
  _request_and_wait(fw, request_addr=REQUEST_B, dst=s9, size=block_bytes, seq=s6)
  _debug_mark(fw, DEBUG_NCRISC, 0xB003)

  fw.arg(t0, 16)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=a3)
  fw.noc_semaphore_wait(a3, s10)
  fw.noc_semaphore_set(a3, 0)
  _debug_mark(fw, DEBUG_NCRISC, 0xB004)

  fw.arg(t0, 13)
  fw.beq(t0, zero, "writer_sender_skip_mcast")
  fw.arg(t1, 9)
  fw.arg(t2, 10)
  fw.arg(t3, 11)
  fw.arg(t5, 12)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(a6, t0, 0)
  fw.addi(a6, a6, base._ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(a0, s9)
  base._emit_mcast_chunks(fw, 1, a0, a5, block_bytes)
  fw.noc_nonposted_writes_flushed(1, a6)
  fw.arg(t0, 17)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=a4)
  fw.arg(t1, 9)
  fw.arg(t2, 10)
  fw.arg(t3, 11)
  fw.arg(t5, 12)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.noc_semaphore_set_multicast(1, 0, a4, a5, 1, t0, a=t1, v=t2)
  fw.label("writer_sender_skip_mcast")
  _debug_mark(fw, DEBUG_NCRISC, 0xB005)

  fw.cb_push_back(NM.CB_INTERFACE, 1, s7)
  _debug_mark(fw, DEBUG_NCRISC, 0xB006)
  fw.addi(s6, s6, 1)
  fw.j("writer_sender_block_loop")
  fw.label("writer_sender_blocks_done")
  _debug_mark(fw, DEBUG_NCRISC, 0xB0FE)
  base.emit_output_writer(fw, plan)
  _debug_mark(fw, DEBUG_NCRISC, 0xB0FF)
  _profile_stamp(fw, PROFILE_NCRISC + 8)
  return fw.ret()


def matmul_writer_recv_drisc(plan: base.MatmulPlan) -> base.MatmulKernel:
  fw = base.MatmulKernel()
  fw.rta_ptr(NM.RTA_L1_BASE_PTR)
  fw.arg(s7, 7)
  fw.arg(s8, 8)
  fw.li(s0, 0)
  _profile_stamp(fw, PROFILE_NCRISC)
  _debug_mark(fw, DEBUG_NCRISC, 0xD000, block_reg=s0)
  fw.label("writer_recv_block_loop")
  fw.beq(s0, s8, "writer_recv_blocks_done")
  _debug_mark(fw, DEBUG_NCRISC, 0xD001, block_reg=s0)
  fw.cb_reserve_back(NM.CB_INTERFACE, 1, s7)
  _debug_mark(fw, DEBUG_NCRISC, 0xD002, block_reg=s0)
  fw.arg(t0, 17)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=s1)
  fw.noc_semaphore_set(s1, 0)
  fw.arg(t0, 16)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=s2)
  fw.arg(t1, 14)
  fw.arg(t2, 15)
  fw.noc_coord(a5, t1, t2)
  fw.local_noc0_coord(a6, x_addr=NM.MY_X, y_addr=NM.MY_Y)
  fw.noc_semaphore_inc(1, 3, s2, a5, 1, ret_coord=a6, a=t3, v=t4)
  _debug_mark(fw, DEBUG_NCRISC, 0xD003, block_reg=s0)
  fw.noc_semaphore_wait(s1, 1)
  _debug_mark(fw, DEBUG_NCRISC, 0xD004, block_reg=s0)
  fw.cb_push_back(NM.CB_INTERFACE, 1, s7)
  _debug_mark(fw, DEBUG_NCRISC, 0xD005, block_reg=s0)
  fw.addi(s0, s0, 1)
  fw.j("writer_recv_block_loop")
  fw.label("writer_recv_blocks_done")
  _debug_mark(fw, DEBUG_NCRISC, 0xD0FE, block_reg=s0)
  base.emit_output_writer(fw, plan)
  _debug_mark(fw, DEBUG_NCRISC, 0xD0FF, block_reg=s0)
  _profile_stamp(fw, PROFILE_NCRISC + 8)
  return fw.ret()


def build_program_drisc(plan: base.MatmulPlan, c_addr: int, num_banks: int, layout: base.TensorLayout | None = None) -> Program:
  brisc_sender = matmul_reader_sender_drisc(plan)
  ncrisc_sender = matmul_writer_sender_drisc(plan)
  brisc_recv = matmul_reader_recv_drisc()
  ncrisc_recv = matmul_writer_recv_drisc(plan)
  trisc0 = base.matmul_trisc0_grouped_k(plan) if base.K_GROUP > 1 else base.matmul_trisc0(plan)
  trisc1 = base.matmul_trisc1_grouped_k(plan) if base.K_GROUP > 1 else base.matmul_trisc1(plan)
  trisc2 = base.matmul_trisc2_grouped_k(plan) if base.K_GROUP > 1 else base.matmul_trisc2(plan)

  brisc_sender.rta(lambda x, y: base.reader_args(plan, 0, (x, y), num_banks, layout))
  brisc_recv.rta(lambda x, y: base.reader_args(plan, 0, (x, y), num_banks, layout))
  ncrisc_sender.rta(lambda x, y: base.writer_args(plan, 0, c_addr, (x, y), num_banks, layout))
  ncrisc_recv.rta(lambda x, y: base.writer_args(plan, 0, c_addr, (x, y), num_banks, layout))
  trisc0.rta(lambda x, y: base.trisc_args(plan, (x, y)) if base.SKIP_PADDED_N else [])
  trisc1.rta(lambda x, y: base.trisc_args(plan, (x, y)) if base.SKIP_PADDED_N else [])
  trisc2.rta(lambda x, y: base.trisc_args(plan, (x, y)) if base.SKIP_PADDED_N else [])

  prog = Program(
    brisc=brisc_sender,
    brisc_recv=brisc_recv,
    ncrisc=ncrisc_sender,
    ncrisc_recv=ncrisc_recv,
    trisc0=trisc0,
    trisc1=trisc1,
    trisc2=trisc2,
    cbs=[
      (0, TILE_BYTES, plan.cb0_pages),
      (1, TILE_BYTES, plan.cb1_pages),
      (16, TILE_BYTES, plan.cb16_pages),
      (24, TILE_BYTES, plan.cb24_pages),
    ],
    semaphores=base.NUM_SEMAPHORES,
    grid=(plan.rows, plan.cols),
  )
  prog.name = f"matmul_drisc_{plan.mt * base.TILE}x{plan.kt * base.TILE}x{plan.nt * base.TILE}"
  return prog


def fixed_5000_plan_drisc(
  M: int, K: int, N: int, cores: list[base.Core], max_feeders: int,
  *, rows: tuple[int, ...] | None = None, cols: tuple[int, ...] | None = None,
) -> base.MatmulPlan:
  if K != 5000 or not (0 < M <= 5000) or not (0 < N <= 5000):
    raise ValueError("fixed 5000 DRISC plan only supports K=5000 with M,N up to 5000")
  ordered = sorted(set(cores), key=lambda xy: (xy[0], xy[1]))
  core_set = frozenset(ordered)
  rows = rows or tuple(range(2, 12))
  cols = cols or tuple(x for x in range(1, 14) if x not in (8, 9))
  if max_feeders < len(rows) + len(cols):
    raise ValueError(f"fixed 5000 DRISC plan needs {len(rows) + len(cols)} feeders, got {max_feeders}")
  missing = [(x, y) for y in rows for x in cols if (x, y) not in core_set]
  if missing:
    raise ValueError(f"fixed 5000 DRISC plan missing worker cores: {missing[:8]}")
  sbh = base.SUPPORTED_OUT_SUBBLOCK_H
  sbw = base.SUPPORTED_OUT_SUBBLOCK_W
  mt_base = base._ceil32(M) // base.TILE
  kt_base = base._ceil32(K) // base.TILE
  nt_base = base._ceil32(N) // base.TILE
  pcm = base._align_up(base._ceil_div(mt_base, len(rows)), sbh)
  pcn = base._align_up(base._ceil_div(nt_base, len(cols)), sbw)
  bw = 6
  kt = base._align_up(kt_base, bw)
  mt = len(rows) * pcm
  nt = len(cols) * pcn
  out_tiles = pcm * pcn
  out_cb_pages = sbh * sbw if base.STREAM_PARTIAL_CB24 else out_tiles
  return base.MatmulPlan(
    rows=rows, cols=cols, mt=mt, kt=kt, nt=nt,
    per_core_m=pcm, per_core_n=pcn, in0_block_w=bw, num_blocks=kt // bw,
    out_subblock_h=sbh, out_subblock_w=sbw,
    in0_num_subblocks=pcm // sbh, in1_num_subblocks=pcn // sbw,
    in0_block_num_tiles=pcm * bw, in0_subblock_num_tiles=sbh * bw,
    in1_block_num_tiles=pcn * bw, in1_per_core_w=pcn,
    out_subblock_num_tiles=sbh * sbw, out_block_num_tiles=out_tiles,
    cb0_pages=base.INPUT_BUFFER_FACTOR * pcm * bw,
    cb1_pages=base.INPUT_BUFFER_FACTOR * pcn * bw,
    cb16_pages=out_cb_pages, cb24_pages=out_cb_pages,
    logical_mt=mt_base, logical_nt=nt_base,
  )


def plan_matmul_drisc(M: int, K: int, N: int, cores: list[base.Core], max_feeders: int) -> base.MatmulPlan:
  if FIXED_5000_PLAN and M == 5000 and K == 5000 and 0 < N <= 5000:
    return fixed_5000_plan_drisc(M, K, N, cores, max_feeders)
  mt_base = base._ceil32(M) // base.TILE
  kt_base = base._ceil32(K) // base.TILE
  nt_base = base._ceil32(N) // base.TILE
  sbh = base.SUPPORTED_OUT_SUBBLOCK_H
  sbw = base.SUPPORTED_OUT_SUBBLOCK_W

  ordered = sorted(set(cores), key=lambda xy: (xy[0], xy[1]))
  if not ordered:
    raise SystemExit("No cores")
  core_set = frozenset(ordered)
  xs = tuple(sorted({x for x, _ in ordered}))
  ys = tuple(sorted({y for _, y in ordered}))
  l1_data_bytes = TensixL1.SIZE - TensixL1.DATA_BUFFER_SPACE_BASE - base.SYNC_BYTES

  def fits_l1(pcm: int, pcn: int, bw: int) -> bool:
    cb0 = base.INPUT_BUFFER_FACTOR * pcm * bw * TILE_BYTES
    cb1 = base.INPUT_BUFFER_FACTOR * pcn * bw * TILE_BYTES
    cb_out = pcm * pcn * TILE_BYTES
    return cb0 + cb1 + cb_out <= l1_data_bytes

  best: tuple | None = None
  best_score: tuple[int, ...] | None = None
  for bw in base.SUPPORTED_IN0_BLOCK_WS:
    kt = base._align_up(kt_base, bw)
    k_pad_tiles = kt - kt_base
    k_pad_permille = base._ceil_div(k_pad_tiles * 1000, kt_base)
    bw_score = bw if k_pad_permille <= (150 if kt_base >= 16 else 0) else -k_pad_tiles
    for y_start in range(len(ys)):
      for y_stop in range(y_start + 1, len(ys) + 1):
        rows = ys[y_start:y_stop]
        valid_cols = [x for x in xs if all((x, y) in core_set for y in rows)]
        if not valid_cols:
          continue
        for nc in range(1, len(valid_cols) + 1):
          cols = tuple(valid_cols[:nc])
          nr = len(rows)
          if nr + nc > max_feeders:
            continue
          pcm = base._align_up(base._ceil_div(mt_base, nr), sbh)
          pcn = base._align_up(base._ceil_div(nt_base, nc), sbw)
          if base.MAX_PER_CORE_M and pcm > base.MAX_PER_CORE_M:
            continue
          if base.MAX_PER_CORE_N and pcn > base.MAX_PER_CORE_N:
            continue
          mt = nr * pcm
          nt = nc * pcn
          if not fits_l1(pcm, pcn, bw):
            continue
          out_tiles = pcm * pcn
          score = (nr * nc, -(mt * nt), -out_tiles, bw_score, -k_pad_permille, bw, -abs(nr - nc), nc)
          if best_score is None or score > best_score:
            best = (rows, cols, mt, kt, nt, pcm, pcn, bw)
            best_score = score

  if best is None:
    raise ValueError(f"No valid DRISC matmul plan for Mt={mt_base} Kt={kt_base} Nt={nt_base} feeders={max_feeders}")
  rows, cols, mt, kt, nt, pcm, pcn, bw = best
  out_tiles = pcm * pcn
  out_cb_pages = plan_out_subblock_pages = sbh * sbw if base.STREAM_PARTIAL_CB24 else out_tiles
  return base.MatmulPlan(
    rows=tuple(rows), cols=tuple(cols), mt=mt, kt=kt, nt=nt,
    per_core_m=pcm, per_core_n=pcn, in0_block_w=bw, num_blocks=kt // bw,
    out_subblock_h=sbh, out_subblock_w=sbw,
    in0_num_subblocks=pcm // sbh, in1_num_subblocks=pcn // sbw,
    in0_block_num_tiles=pcm * bw, in0_subblock_num_tiles=sbh * bw,
    in1_block_num_tiles=pcn * bw, in1_per_core_w=pcn,
    out_subblock_num_tiles=sbh * sbw, out_block_num_tiles=out_tiles,
    cb0_pages=base.INPUT_BUFFER_FACTOR * pcm * bw, cb1_pages=base.INPUT_BUFFER_FACTOR * pcn * bw,
    cb16_pages=out_cb_pages, cb24_pages=plan_out_subblock_pages,
    logical_mt=mt_base, logical_nt=nt_base,
  )


def _buildable_plan_drisc(
  M: int, K: int, N: int, cores: list[base.Core], num_banks: int, max_feeders: int
) -> base.MatmulPlan:
  plan = plan_matmul_drisc(M, K, N, cores, max_feeders)
  build_program_drisc(plan, 0, num_banks).layout(core_xy=plan.cores()[0])
  return plan


def plan_output_chunks_drisc(
  M: int, K: int, N: int, cores: list[base.Core], num_banks: int, max_feeders: int
) -> list[base.MatmulChunk]:
  if FIXED_5000_PLAN and FIXED_5000_M_SPLIT_ALL_CORES and (M, K, N) == (5000, 5000, 5000):
    specs = (
      (0, 1024, tuple(range(2, 4)), tuple(x for x in range(1, 14) if x not in (8, 9))),
      (1024, 3976, tuple(range(4, 12)), tuple(x for x in range(1, 15) if x not in (8, 9))),
    )
    chunks = []
    for m0, logical_m, rows, cols in specs:
      plan = fixed_5000_plan_drisc(logical_m, K, N, cores, max_feeders, rows=rows, cols=cols)
      build_program_drisc(plan, 0, num_banks).layout(core_xy=plan.cores()[0])
      chunks.append(base.MatmulChunk(m0=m0, n0=0, m=logical_m, n=N, plan=plan))
    return chunks

  if FIXED_5000_PLAN and (M, K, N) == (5000, 5000, 5000) and FIXED_5000_N_CHUNKS > 1:
    nt = base._ceil32(N) // base.TILE
    chunks = []
    n0_tiles = 0
    for idx in range(FIXED_5000_N_CHUNKS):
      remaining_tiles = nt - n0_tiles
      remaining_chunks = FIXED_5000_N_CHUNKS - idx
      chunk_tiles = base._ceil_div(remaining_tiles, remaining_chunks)
      n0 = n0_tiles * base.TILE
      logical_n = min(N - n0, chunk_tiles * base.TILE)
      plan = fixed_5000_plan_drisc(M, K, logical_n, cores, max_feeders)
      build_program_drisc(plan, 0, num_banks).layout(core_xy=plan.cores()[0])
      chunks.append(base.MatmulChunk(m0=0, n0=n0, m=M, n=logical_n, plan=plan))
      n0_tiles += chunk_tiles
    return chunks

  chunks: list[base.MatmulChunk] = []

  def visit(m0: int, m: int, n0: int, n: int) -> None:
    try:
      chunks.append(base.MatmulChunk(m0=m0, n0=n0, m=m, n=n, plan=_buildable_plan_drisc(m, K, n, cores, num_banks, max_feeders)))
      return
    except ValueError:
      pass

    split_m = base._split_length(m)
    split_n = base._split_length(n)
    if split_m == 0 and split_n == 0:
      raise ValueError(f"No tiled DRISC matmul plan for M={m} K={K} N={n} feeders={max_feeders}")

    split_m_first = (
      split_n == 0
      or base.SPLIT_AXIS == "m"
      or (base.SPLIT_AXIS == "auto" and split_m != 0 and m >= n)
    )
    if split_m_first:
      visit(m0, split_m, n0, n)
      visit(m0 + split_m, m - split_m, n0, n)
    else:
      visit(m0, m, n0, split_n)
      visit(m0, m, n0 + split_n, n - split_n)

  visit(0, M, 0, N)
  return chunks


def _emit_remote_read_word(fw: DriscMatmulFeeder, *, noc: int, worker_coord: int, request_addr: int, ret_coord, out):
  fw.li(a0, request_addr)
  fw.li(a1, worker_coord)
  fw.li(a2, 16)
  fw.read32(s7, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(s7, s7, 1)
  fw.noc_read(noc, 1, a0, 0, a1, ACK_SCRATCH_ADDR, a2, ret_coord=ret_coord, a=t0, v=t1)
  fw.noc_reads_flushed(noc, s7, addr=t0, val=t1)
  return fw.read32(out, ACK_SCRATCH_ADDR, tmp_addr=t0)


def _emit_stage_write(fw: DriscMatmulFeeder, *, noc: int, chunk_bytes: int, worker_coord: int, dst_reg):
  from drisc_gddr_dma_poc import STAGE_ADDR
  chunks = base._ceil_div(chunk_bytes, MAX_NOC_CHUNK_BYTES)
  fw.read32(t6, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(t6, t6, chunks)
  for off in range(0, chunk_bytes, MAX_NOC_CHUNK_BYTES):
    n = min(MAX_NOC_CHUNK_BYTES, chunk_bytes - off)
    if off:
      fw.li(t5, off)
      fw.li(a2, STAGE_ADDR)
      fw.add(a2, a2, t5)
      fw.add(a3, dst_reg, t5)
    else:
      fw.li(a2, STAGE_ADDR)
      fw.mv(a3, dst_reg)
    fw.li(a4, worker_coord)
    fw.li(a5, n)
    fw.noc_write(noc, 0, a2, a3, 0, a4, a5, posted=True, a=t3, v=t4)
  return emit_posted_writes_flushed(fw, noc=noc, target=t6, addr=t3, val=t4)


def _emit_remote_write_word16(fw: DriscMatmulFeeder, *, noc: int, worker_coord: int, remote_addr: int, value):
  fw.write32(ACK_SCRATCH_ADDR + 0x10, value, tmp_addr=t3, tmp_val=t4)
  for off in (0x14, 0x18, 0x1C):
    fw.write32(ACK_SCRATCH_ADDR + off, 0, tmp_addr=t3, tmp_val=t4)
  fw.read32(t6, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(t6, t6, 1)
  fw.li(a2, ACK_SCRATCH_ADDR + 0x10)
  fw.li(a3, remote_addr)
  fw.li(a4, worker_coord)
  fw.li(a5, 16)
  fw.noc_write(noc, 0, a2, a3, 0, a4, a5, posted=True, a=t3, v=t4)
  return emit_posted_writes_flushed(fw, noc=noc, target=t6, addr=t3, val=t4)


def _emit_status_done(fw: DriscMatmulFeeder, *, noc: int, worker_coord: int, request_addr: int, seq):
  _emit_remote_write_word16(fw, noc=noc, worker_coord=worker_coord, remote_addr=request_addr + REQ_SEQ, value=seq)
  return _emit_remote_write_word16(fw, noc=noc, worker_coord=worker_coord, remote_addr=request_addr + REQ_STATUS, value=REQ_DONE)


def build_drisc_stream_feeder(
  *, gddr_addr: int, block_bytes: int, num_blocks: int, worker_coord: int,
  request_addr: int, noc: int, ctrl_noc: int, stream: int,
) -> bytes:
  from drisc_gddr_dma_poc import STAGE_ADDR
  if DRISC_CHUNK_BYTES > ACK_SCRATCH_ADDR - STAGE_ADDR:
    raise ValueError("DRISC_CHUNK_BYTES does not fit staging region")
  fw = DriscMatmulFeeder(base_addr=DRISC_FW_BASE)
  for idx, value in enumerate((POC_MAGIC, block_bytes, gddr_addr & 0xFFFFFFFF, (gddr_addr >> 32) & 0xFFFFFFFF, request_addr, worker_coord, STATUS_STARTED, num_blocks)):
    fw.write32(RESULT_ADDR + idx * 4, value, tmp_addr=t0, tmp_val=t1)
  fw.write32(TX_CTRL_TRANSFER_ATTRIBUTES, DMA_CTRL_ATTRS_BURST_255, tmp_addr=t0, tmp_val=t1)
  emit_set_drisc_stream_mode_all(fw)
  emit_init_drisc_noc_cmd_bufs(fw)
  emit_local_noc_coord(fw, noc=ctrl_noc, out=s6)

  gddr_hi = (gddr_addr >> 32) & 0xFFFFFFFF
  fw.li(s0, 0)  # block index
  fw.li(s3, gddr_addr & 0xFFFFFFFF)
  loop = fw._new_label("feed_block_loop")
  body = fw._new_label("feed_block_body")
  done = fw._new_label("feed_done")
  poll = fw._new_label("feed_poll")
  fw.label(loop)
  fw.li(t0, num_blocks)
  fw.bltu(s0, t0, body)
  fw.j(done)
  fw.label(body)
  fw.label(poll)
  _emit_remote_read_word(fw, noc=ctrl_noc, worker_coord=worker_coord, request_addr=request_addr + REQ_STATUS, ret_coord=s6, out=s1)
  fw.li(t0, REQ_READY)
  fw.bne(s1, t0, poll)
  _emit_remote_read_word(fw, noc=ctrl_noc, worker_coord=worker_coord, request_addr=request_addr + REQ_SEQ, ret_coord=s6, out=s4)
  fw.bne(s4, s0, poll)
  first_ready_done = fw._new_label("feed_first_ready_done")
  fw.bne(s0, zero, first_ready_done)
  _profile_result_stamp(fw, PROFILE_FEEDER_FIRST_READY_WORD)
  fw.label(first_ready_done)
  _emit_remote_read_word(fw, noc=ctrl_noc, worker_coord=worker_coord, request_addr=request_addr + REQ_DST, ret_coord=s6, out=s2)

  for off in range(0, block_bytes, DRISC_CHUNK_BYTES):
    chunk_bytes = min(DRISC_CHUNK_BYTES, block_bytes - off)
    emit_dma_read_reg(fw, src_lo=s3, src_hi=gddr_hi, dst_l1=STAGE_ADDR, size=chunk_bytes, stream=stream)
    emit_dma_read_wait_n(fw, stream=stream, max_outstanding=0)
    if off:
      fw.li(t0, off)
      fw.add(s5, s2, t0)
    else:
      fw.mv(s5, s2)
    _emit_stage_write(fw, noc=noc, chunk_bytes=chunk_bytes, worker_coord=worker_coord, dst_reg=s5)
    fw.li(t0, chunk_bytes)
    fw.add(s3, s3, t0)
  _emit_status_done(fw, noc=ctrl_noc, worker_coord=worker_coord, request_addr=request_addr, seq=s0)
  if POLL_FINAL_FEEDER_STATUS:
    not_final = fw._new_label("feed_not_final_status")
    status_visible = fw._new_label("feed_final_status_visible")
    fw.li(t0, num_blocks - 1)
    fw.bne(s0, t0, not_final)
    fw.label(status_visible)
    _emit_remote_read_word(fw, noc=ctrl_noc, worker_coord=worker_coord, request_addr=request_addr + REQ_STATUS, ret_coord=s6, out=t0)
    fw.li(t1, REQ_DONE)
    fw.bne(t0, t1, status_visible)
    fw.label(not_final)
  fw.addi(s0, s0, 1)
  fw.j(loop)
  fw.label(done)
  _profile_result_stamp(fw, PROFILE_FEEDER_DONE_WORD)
  emit_set_drisc_noc2axi_mode_all(fw)
  fw.write32(RESULT_ADDR + 6 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  spin = fw._new_label("feed_done_spin")
  fw.label(spin)
  fw.j(spin)
  return fw.compile()[0].data


def start_drisc(core: tuple[int, int], code: bytes, dev):
  with TLBWindow(dev, start=core, addr=DRISC_L1_NOC_ALIAS) as l1:
    regs = RegWindow(dev, core)
    try:
      l1.write(RESULT_ADDR, b"\0" * (RESULT_WORDS * 4))
      l1.write(DRISC_FW_BASE, code)
      reset_state = regs.read32(SOFT_RESET_0)
      regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
      regs.write32(DRISC_RESET_PC, DRISC_FW_BASE)
      time.sleep(0.01)
      regs.write32(SOFT_RESET_0, reset_state & ~SOFT_RESET_BRISC)
    finally:
      regs.close()


def wait_drisc(core: tuple[int, int], dev, timeout: float) -> tuple[int, ...]:
  with TLBWindow(dev, start=core, addr=DRISC_L1_NOC_ALIAS) as l1:
    regs = RegWindow(dev, core)
    deadline = time.time() + timeout
    words = (0,) * RESULT_WORDS
    try:
      while time.time() < deadline:
        words = struct.unpack("<" + "I" * RESULT_WORDS, l1.read(RESULT_ADDR, RESULT_WORDS * 4))
        if words[6] == STATUS_DONE and (words[0] == POC_MAGIC or ACCEPT_CORRUPT_FEEDER_HEADER):
          break
        time.sleep(0.001)
      reset_state = regs.read32(SOFT_RESET_0)
      regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
      if words[6] != STATUS_DONE or (words[0] != POC_MAGIC and not ACCEPT_CORRUPT_FEEDER_HEADER):
        raise TimeoutError(f"DRISC matmul feeder did not finish on {core}; words={[hex(w) for w in words]}")
      return words
    finally:
      regs.close()


def read_drisc_words(core: tuple[int, int], dev) -> tuple[int, ...]:
  with TLBWindow(dev, start=core, addr=DRISC_L1_NOC_ALIAS) as l1:
    return struct.unpack("<" + "I" * RESULT_WORDS, l1.read(RESULT_ADDR, RESULT_WORDS * 4))


def _tile_stream(tiled: bytes, tile_indices: list[int]) -> bytes:
  view = memoryview(tiled)
  return b"".join(bytes(view[i * TILE_BYTES:(i + 1) * TILE_BYTES]) for i in tile_indices)


def _a_sender_indices(plan: base.MatmulPlan, layout: base.TensorLayout, row_index: int) -> list[int]:
  out = []
  row0 = layout.m_tile_offset + row_index * plan.per_core_m
  for block in range(plan.num_blocks):
    k0 = block * plan.in0_block_w
    for row in range(plan.per_core_m):
      base_idx = (row0 + row) * layout.a_row_stride + k0
      for col in range(plan.in0_block_w):
        out.append(base_idx + col)
  return out


def _b_sender_indices(plan: base.MatmulPlan, layout: base.TensorLayout, col_index: int) -> list[int]:
  out = []
  col0 = layout.n_tile_offset + col_index * plan.per_core_n
  for block in range(plan.num_blocks):
    k0 = block * plan.in0_block_w
    for row in range(plan.in0_block_w):
      base_idx = (k0 + row) * layout.b_row_stride + col0
      for col in range(plan.per_core_n):
        out.append(base_idx + col)
  return out


def main() -> None:
  if len(sys.argv) == 1:
    M = N = K = 5000
  elif len(sys.argv) == 4:
    M, N, K = (int(arg) for arg in sys.argv[1:])
  else:
    raise SystemExit("Usage: matmul_peak_drisc.py [M N K]")
  device = Device()
  try:
    num_banks = len(device.dram.bank_tiles)
    feeder_tiles = list(device.board_info.dram_tiles)
    if not USE_ALL_FEEDERS:
      feeder_tiles = [tile for tile in feeder_tiles if (tile[1], tile[2]) != (0, 0)]
    chunks = plan_output_chunks_drisc(M, K, N, device.cores, num_banks, len(feeder_tiles))
    Mp, Kp, Np = base.global_padded_shape(M, K, N, chunks)

    a_ref, b_ref = base.make_inputs(M, K, N)
    a_padded = np.zeros((Mp, Kp), dtype=np.float32)
    b_padded = np.zeros((Kp, Np), dtype=np.float32)
    a_padded[:M, :K] = a_ref
    b_padded[:K, :N] = b_ref
    a_tiled = tilize(base.to_bf16_device_bytes(a_padded), Dtype.Float16_b.bpe, (Mp, Kp))
    b_tiled = tilize(base.to_bf16_device_bytes(b_padded), Dtype.Float16_b.bpe, (Kp, Np))
    c_buf = device.dram.alloc((Mp // base.TILE) * (Np // base.TILE), dtype=Dtype.Float16_b, shape=(Mp, Np), name="C")

    run_times_us = []
    for _run in range(RUNS):
      run_timings = []
      for chunk_idx, chunk in enumerate(chunks):
        plan = chunk.plan
        layout = base.TensorLayout(
          m_tile_offset=chunk.m_tile_offset,
          n_tile_offset=chunk.n_tile_offset,
          a_row_stride=Kp // base.TILE,
          b_row_stride=Np // base.TILE,
          c_row_stride=Np // base.TILE,
        )
        sender_cores = [(plan.cols[0], y) for y in plan.rows] + [(x, plan.rows[0]) for x in plan.cols]
        chunk_feeder_tiles = feeder_tiles[:len(sender_cores)]
        if len(chunk_feeder_tiles) < len(sender_cores):
          raise SystemExit(f"need {len(sender_cores)} DRAM feeder tiles, have {len(chunk_feeder_tiles)}")

        block_a = plan.in0_block_num_tiles * TILE_BYTES
        block_b = plan.in1_block_num_tiles * TILE_BYTES
        feeders = []
        gddr_cursor = FEEDER_GDDR_BASE
        for i, worker_core in enumerate(sender_cores):
          is_a = i < plan.num_rows
          role_index = i if is_a else i - plan.num_rows
          tile_indices = (
            _a_sender_indices(plan, layout, role_index) if is_a
            else _b_sender_indices(plan, layout, role_index)
          )
          stream_data = _tile_stream(a_tiled if is_a else b_tiled, tile_indices)
          bank, x, y = chunk_feeder_tiles[i]
          dram_core = (x, y)
          gddr_addr = gddr_cursor
          gddr_cursor += base._align_up(len(stream_data), 64)
          with TLBWindow(device.dev, start=dram_core, addr=0, size=TLBWindow.SIZE_4G, wc=True) as gddr:
            gddr.write(gddr_addr, stream_data)
          request_addr = REQUEST_A if is_a else REQUEST_B
          payload_noc = 0 if PAYLOAD_NOC_MODE == "balanced" or is_a else 1
          code = build_drisc_stream_feeder(
            gddr_addr=gddr_addr,
            block_bytes=block_a if is_a else block_b,
            num_blocks=plan.num_blocks,
            worker_coord=noc_xy(*worker_core),
            request_addr=request_addr,
            noc=payload_noc,
            ctrl_noc=0,
            stream=0,
          )
          start_drisc(dram_core, code, device.dev)
          feeders.append((dram_core, "A" if is_a else "B", worker_core, len(stream_data), bank, request_addr))

        prog = build_program_drisc(plan, c_buf.addr, num_banks, layout)
        prog.name = f"matmul_drisc_M{M}_N{N}_K{K}_chunk{chunk_idx}"
        try:
          run_timings.extend(device.run(prog))
        except TimeoutError:
          for idx, (dram_core, role, worker_core, size, bank, request_addr) in enumerate(feeders):
            words = read_drisc_words(dram_core, device.dev)
            with TLBWindow(device.dev, start=worker_core) as worker_l1:
              req_status = struct.unpack("<I", worker_l1.read(request_addr + REQ_STATUS, 4))[0]
              req_dst = struct.unpack("<I", worker_l1.read(request_addr + REQ_DST, 4))[0]
              req_seq = struct.unpack("<I", worker_l1.read(request_addr + REQ_SEQ, 4))[0]
            print(
              f"feeder-timeout chunk={chunk_idx} idx={idx} role={role} bank={bank} dram_core={dram_core} worker={worker_core} "
              f"stream={size} req_status={req_status} req_seq={req_seq} req_dst=0x{req_dst:x} "
              f"drisc_words={[hex(w) for w in words]}",
              file=sys.stderr,
            )
          raise

        try:
          for dram_core, _role, _worker_core, _size, _bank, _request_addr in feeders:
            wait_drisc(dram_core, device.dev, timeout=10.0)
        except TimeoutError as exc:
          print(f"feeder-wait-timeout chunk={chunk_idx}: {exc}", file=sys.stderr)
          feeder_states = []
          for idx, (dram_core, role, worker_core, size, bank, request_addr) in enumerate(feeders):
            words = read_drisc_words(dram_core, device.dev)
            with TLBWindow(device.dev, start=worker_core) as worker_l1:
              req_status = struct.unpack("<I", worker_l1.read(request_addr + REQ_STATUS, 4))[0]
              req_dst = struct.unpack("<I", worker_l1.read(request_addr + REQ_DST, 4))[0]
              req_seq = struct.unpack("<I", worker_l1.read(request_addr + REQ_SEQ, 4))[0]
            feeder_states.append((words, req_status, req_seq))
            print(
              f"feeder-wait-debug chunk={chunk_idx} idx={idx} role={role} bank={bank} dram_core={dram_core} worker={worker_core} "
              f"stream={size} req_status={req_status} req_seq={req_seq} req_dst=0x{req_dst:x} "
              f"drisc_words={[hex(w) for w in words]}",
              file=sys.stderr,
            )
          workers_done = all(req_status == REQ_DONE and req_seq == plan.num_blocks - 1 for _words, req_status, req_seq in feeder_states)
          if not ALLOW_FEEDER_TIMEOUT_AFTER_WORKERS_DONE or not workers_done:
            raise
          print(
            f"feeder-wait-timeout chunk={chunk_idx}: continuing because all worker requests reached final REQ_DONE",
            file=sys.stderr,
          )
      if run_timings:
        run_times_us.append(sum(timing["us"] for timing in run_timings))

    c_raw = device.dram_read(c_buf)
    base.validate(a_ref, b_ref, c_raw, M, N, Mp, Np)
    if not run_times_us:
      raise RuntimeError("DRISC matmul timing is unavailable without fast dispatch")
    avg_us = sum(run_times_us) / len(run_times_us)
    print("matmul_peak_drisc:")
    print(f"  runs: {len(run_times_us)}")
    print(f"  shape: {M}x{K}x{N}")
    print(f"  padded: {Mp}x{Kp}x{Np}")
    print(f"  kernel_avg: {avg_us:,.1f} us")
    print(f"  throughput: {base.tflops(Mp, Np, Kp, avg_us):.2f} TFLOP/s")
  finally:
    device.close()


if __name__ == "__main__":
  main()
