#!/usr/bin/env python3
from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np

from asm import KernelBase
from device import Device
from dsl import (
  TTDMANOP, TTINSN, TTMOP, TTREPLAY, TTSEMGET, TTSEMINIT, TTSEMPOST, TTSEMWAIT, TTSETRWC,
  TTSETADC, TTSETADCXX, TTSETADCZW, TTSETDMAREG, TTSTALLWAIT, TTPACR, TTRMWCIB0, TTRMWCIB1, TTRMWCIB2, TTWRCFG,
  a0, a1, a2, a3, a4, a5, a6, a7,
  ra,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11,
  sp, t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk import Cb, Debug, Noc, Tensix
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM, TriscLocalMem as TLM, TriscMailbox
from ttk.noc import NOC
from ttk.tensix import Cfg, TensixL1, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait, ThreadCfg


M = 384
K = 384
N = 384
MT = KT = NT = 12
TILE = 32
TILE_BYTES = Dtype.Float16_b.tile_size

ROWS = (2, 3, 4)
COLS = (1, 2, 3)
NUM_SEMAPHORES = 4

PER_CORE_M = 4
PER_CORE_N = 4
IN0_BLOCK_W = 6
NUM_BLOCKS = 2
OUT_SUBBLOCK_H = 2
OUT_SUBBLOCK_W = 2
IN0_NUM_SUBBLOCKS = 2
IN1_NUM_SUBBLOCKS = 2
IN0_BLOCK_NUM_TILES = 24
IN0_SUBBLOCK_NUM_TILES = 12
IN1_BLOCK_NUM_TILES = 24
IN1_PER_CORE_W = 4
OUT_SUBBLOCK_NUM_TILES = 4
OUT_BLOCK_NUM_TILES = 16
CB0_PAGES = 48
CB1_PAGES = 48
CB16_PAGES = 16
CB24_PAGES = 16

PCC_THRESHOLD = 0.995
REL_L2_THRESHOLD = 0.08
VALIDATE_SAMPLES = 64
VALIDATE_SEED = 0
SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
SYNC_TRISC_START = SCRATCH_L1 + 0x10000
SYNC_TRISC_INIT = SYNC_TRISC_START + 16


Core = tuple[int, int]


@dataclass(frozen=True)
class RiscSync:
  start: int
  trisc_init: int


SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)
STALL_MATH_PACK_ROOM = TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU
STALL_MATH_PACK_DATA = TensixStall.TDMA
WAIT_THCON_AND_PACK = TensixWait.THCON | TensixWait.PACK0
THCON_SEC0_REG3_BASE_ADDR32 = 76
THCON_SEC1_REG3_BASE_ADDR32 = 124


# From llk_unpack_AB_matmul_init(ct_dim=2, rt_dim=2, kt_dim=6), no partial
# faces. In reuse-A mode the explicit runtime UNPACR loads in0 into SrcB; the
# MOP replays below load the two in1 tiles into SrcA.
MATMUL_UNPACK_AB_MOP_CFG = [
  0,
  0,
  0,
  0x04000060,  # TTREPLAY(0, 6)
  0,
  0,
  0,
  0x04018060,  # TTREPLAY(6, 6)
  0,
]

# From matmul_compute_trisc2.kernel.dis around 0x819c: pack_tile MOP template.
MATMUL_PACK_MOP_CFG = [
  4, 4,
  0x02000000,  # TTNOP
  0x02000000,  # TTNOP
  0x02000000,  # TTNOP
  0x41000000,  # TTPACR()
  0x02000000,  # TTNOP
  0x41008001,  # TTPACR(AddrMode=1, Last=1)
  0x41010000,  # TTPACR(AddrMode=2)
]

# Throttled HiFi2 matmul replay payload.  The MOP adds the ADDR_MOD_4 and
# ADDR_MOD_5 final MVMULs; these 11 replay slots intentionally carry only the
# three MVMULs from run_throttled_sequence<5>() plus delay NOPs.
MATMUL_MATH_MOP_CFG = [
  2, 2,
  0x02000000,  # TTNOP
  0x02000000,  # TTNOP
  0x02000000,  # TTNOP
  0x040400B0,  # nested replay/MOP status op emitted by llk_math_matmul
  0x26008000,  # TTMVMUL addr-mode variant
  0x26014000,  # TTMVMUL addr-mode variant
  0x26010000,  # TTMVMUL addr-mode variant
]

# From matmul_compute_trisc1.kernel.dis around 0x7864: copy_tile-to-dst MOP
# used for reloading cb24 partials before the second K block accumulates.
MATMUL_MATH_RELOAD_MOP_CFG = [
  4, 2,
  0x02000000,
  0x37C00003,
  0x02000000,
  0x1200A000,
  0x02000000,
  0x1200A000,
  0x1200A000,
]

MATMUL_MATH_REPLAY_LOAD = [
  0x02000000,
  0x02000000,
  0x26000000,
  0x02000000,
  0x02000000,
  0x26004000,
  0x02000000,
  0x02000000,
  0x26000000,
  0x02000000,
  0x02000000,
]

MATMUL_UNPACK_REPLAY0_LOAD = [
  0x420000C1,
  0xB10C004C,
  0x5800C324,
  0xA2400001,
  0xB00C004C,
  0x02000000,
]

MATMUL_UNPACK_REPLAY1_LOAD = [
  0x420000C1,
  0xB10C004D,
  0x5800C324,
  0xA2400001,
  0xB00C004D,
  0x02000000,
]

MATMUL_UNPACK_SRCB_LOAD = 0x428000C1

MATMUL_RELOAD_UNPACK_MOP_CFG = [
  4,
  1,
  0x420080C1,  # TTUNPACR(AddrMode=1, OvrdThreadId=1, SetDatValid=1, Last=1)
  0x02000000,
  0x02000000,
  0x43800101,  # TTUNPACR_NOP(Unpacker_Select=1, Set_Dvalid=1, Unpack_Pop=1)
  0x02000000,
  0x43800101,
  0x43800101,
]


@dataclass(frozen=True)
class FixedPlan:
  rows: tuple[int, ...] = ROWS
  cols: tuple[int, ...] = COLS
  mt: int = MT
  kt: int = KT
  nt: int = NT
  per_core_m: int = PER_CORE_M
  per_core_n: int = PER_CORE_N
  in0_block_w: int = IN0_BLOCK_W
  num_blocks: int = NUM_BLOCKS
  out_subblock_h: int = OUT_SUBBLOCK_H
  out_subblock_w: int = OUT_SUBBLOCK_W
  in0_num_subblocks: int = IN0_NUM_SUBBLOCKS
  in1_num_subblocks: int = IN1_NUM_SUBBLOCKS
  in0_block_num_tiles: int = IN0_BLOCK_NUM_TILES
  in0_subblock_num_tiles: int = IN0_SUBBLOCK_NUM_TILES
  in1_block_num_tiles: int = IN1_BLOCK_NUM_TILES
  in1_per_core_w: int = IN1_PER_CORE_W
  out_subblock_num_tiles: int = OUT_SUBBLOCK_NUM_TILES
  out_block_num_tiles: int = OUT_BLOCK_NUM_TILES
  cb0_pages: int = CB0_PAGES
  cb1_pages: int = CB1_PAGES
  cb16_pages: int = CB16_PAGES
  cb24_pages: int = CB24_PAGES

  def grid(self) -> list[list[Core]]:
    return [[(x, y) for x in self.cols] for y in self.rows]

  def cores(self) -> list[Core]:
    return [core for row in self.grid() for core in row]


PLAN = FixedPlan()


class MatmulKernel(KernelBase, Noc, Cb):
  """Shared base for matmul's hand-written dataflow kernels."""

  def rta_ptr(self, mailbox_addr: int, *, out=s11):
    return self.read32(out, mailbox_addr)

  def arg(self, dst, index: int, *, ptr=s11):
    return self.lw(dst, ptr, index * 4)

  def release_triscs(self):
    for addr in (
      SYNC_TRISC_START,
      SYNC_TRISC_INIT,
      SYNC_TRISC_INIT + 4,
      SYNC_TRISC_INIT + 8,
    ):
      self.write32(addr, 0)
    return self.write32(SYNC_TRISC_START, 0x00010101)


class MatmulTrisc(KernelBase, Tensix, Cb, Debug):
  NUM_TRISC = 3

  def __init__(self, thread_id: int, sync: RiscSync = SYNC, *, base_addr: int = 0):
    super().__init__(base_addr=base_addr)
    self.thread_id = thread_id
    self.sync = sync
    self.data = TriscMailbox.DATA1 if thread_id == 1 else TriscMailbox.DATA_COMMON
    from ttk.math import Math
    from ttk.pack import Pack
    from ttk.unpack import Unpack
    self.unpack = Unpack(self)
    self.math = Math(self)
    self.pack = Pack(self)

  def prologue(self):
    self.addi(sp, sp, -16)
    self.sw(ra, sp, 12)
    self.wait8(self.sync.start + self.thread_id, 1)
    self.write8(self.sync.start + self.thread_id, 0)
    return self

  def init_barrier(self):
    self.write32(self.sync.trisc_init + self.thread_id * 4, 1)
    self.fence()
    self.li(t1, 1)
    for init_id in range(self.NUM_TRISC):
      self.wait_sync_value(self.sync.trisc_init + init_id * 4, t1, actual=t2)
    return self

  def ret_kernel(self):
    self.lw(ra, sp, 12)
    self.addi(sp, sp, 16)
    return self.ret()


def _mcast_rect_args(x_list: list[int], y: int) -> tuple[int, int, int, int, int]:
  if not x_list:
    return (0, 0, 0, 0, 0)
  return (min(x_list), y, max(x_list), y, len(x_list))


def _core_to_rc(plan: FixedPlan) -> dict[Core, tuple[int, int]]:
  grid = plan.grid()
  return {grid[r][c]: (r, c) for r in range(len(plan.rows)) for c in range(len(plan.cols))}


def reader_args(plan: FixedPlan, a_addr: int, core_xy: Core, num_banks: int) -> list[int]:
  core_to_rc = _core_to_rc(plan)
  ri, _ = core_to_rc[core_xy]
  west_cols = [x for x in plan.cols if x < 8]
  east_cols = [x for x in plan.cols if x >= 10]
  w_rect = _mcast_rect_args([c for c in west_cols if c != plan.cols[0]], core_xy[1])
  e_rect = _mcast_rect_args(list(east_cols), core_xy[1])
  sender_xy = plan.grid()[ri][0]
  return [
    a_addr,
    ri * plan.per_core_m * plan.kt,
    1,
    plan.kt,
    plan.in0_block_w,
    plan.in0_block_w,
    plan.per_core_m,
    plan.in0_block_num_tiles,
    plan.num_blocks,
    *w_rect,
    *e_rect,
    sender_xy[0],
    sender_xy[1],
    0,
    1,
    num_banks,
  ]


def writer_args(plan: FixedPlan, b_addr: int, c_addr: int, core_xy: Core, num_banks: int) -> list[int]:
  core_to_rc = _core_to_rc(plan)
  ri, ci = core_to_rc[core_xy]
  recv_ys = list(plan.rows[1:])
  mcast = (core_xy[0], max(recv_ys), core_xy[0], min(recv_ys), len(recv_ys)) if recv_ys else (0, 0, 0, 0, 0)
  sender_xy = plan.grid()[0][ci]
  out_start = ri * plan.per_core_m * plan.nt + ci * plan.per_core_n
  return [
    b_addr,
    ci * plan.per_core_n,
    1,
    plan.nt,
    plan.in0_block_w * plan.nt,
    plan.per_core_n,
    plan.in0_block_w,
    plan.in1_block_num_tiles,
    plan.num_blocks,
    *mcast,
    sender_xy[0],
    sender_xy[1],
    2,
    3,
    c_addr,
    out_start,
    1,
    plan.nt,
    plan.out_subblock_w,
    plan.out_subblock_h * plan.nt,
    plan.out_subblock_w,
    plan.out_subblock_h,
    plan.out_subblock_num_tiles,
    plan.in1_num_subblocks,
    plan.in0_num_subblocks,
    num_banks,
  ]


def matmul_reader_sender() -> MatmulKernel:
  fw = MatmulKernel()
  fw.release_triscs()
  fw.rta_ptr(BM.RTA_L1_BASE_PTR)
  fw.arg(s0, 0)   # A base
  fw.arg(s1, 1)   # current first tile
  fw.arg(s2, 2)   # inner tile stride
  fw.arg(s3, 3)   # row tile stride
  fw.arg(s4, 4)   # next K-block offset
  fw.arg(s6, 6)   # block_h
  fw.arg(s7, 7)   # block_tiles
  fw.arg(s8, 8)   # nblocks
  fw.arg(s9, 18)  # east receiver count
  fw.arg(s10, 9)  # west receiver count, patched below after rect args
  fw.arg(s10, 13)
  fw.add(s10, s10, s9)

  fw.arg(t0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=t6)
  fw.noc_semaphore_set(t6, 1)

  fw.li(s6, 0)
  fw.label("reader_sender_block_loop")
  fw.bne(s6, s8, "reader_sender_block_body")
  fw.j("reader_sender_done")
  fw.label("reader_sender_block_body")
  fw.cb_reserve_back(BM.CB_INTERFACE, 0, s7)
  fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=s9)
  fw.mv(a4, s9)
  fw.li(t5, 0)
  fw.mv(a6, s1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.lw(a7, t0, 0)

  for tile_off in (
    0, 1, 2, 3, 4, 5,
    KT, KT + 1, KT + 2, KT + 3, KT + 4, KT + 5,
    2 * KT, 2 * KT + 1, 2 * KT + 2, 2 * KT + 3, 2 * KT + 4, 2 * KT + 5,
    3 * KT, 3 * KT + 1, 3 * KT + 2, 3 * KT + 3, 3 * KT + 4, 3 * KT + 5,
  ):
    fw.mv(a0, s0)
    if tile_off:
      fw.addi(a1, s1, tile_off)
    else:
      fw.mv(a1, s1)
    fw.arg(a2, 23)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.local_noc0_coord(a5)
    fw.li(t6, TILE_BYTES)
    fw.noc_read(0, 1, a0, 0, a2, a4, t6, ret_coord=a5, a=t3, v=t5)
    fw.add(a4, a4, t6)

  fw.add(a7, a7, s7)
  fw.noc_reads_flushed(0, a7)
  fw.arg(t0, 21)
  fw.sem_addr(BM.SEM_L1_BASE, t0, out=a3)
  fw.noc_semaphore_wait(a3, s10)
  fw.noc_semaphore_set(a3, 0)

  fw.arg(t0, 13)
  fw.beq(t0, zero, "reader_sender_skip_west")
  fw.arg(t1, 9)
  fw.arg(t2, 10)
  fw.arg(t3, 11)
  fw.arg(t5, 12)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT)
  fw.lw(a6, t0, 0)
  fw.addi(a6, a6, 3)
  fw.mv(a0, s9)
  for chunk in range(3):
    fw.li(t5, NOC.MAX_BURST_SIZE)
    fw.noc_write(0, 0, a0, a0, 0, a5, t5, mcast=True, a=t1, v=t2)
    if chunk != 2:
      fw.add(a0, a0, t5)
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

  fw.arg(t0, 18)
  fw.beq(t0, zero, "reader_sender_skip_east")
  fw.arg(t1, 14)
  fw.arg(t2, 15)
  fw.arg(t3, 16)
  fw.arg(t5, 17)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT)
  fw.lw(a6, t0, 0)
  fw.addi(a6, a6, 3)
  fw.mv(a0, s9)
  for chunk in range(3):
    fw.li(t5, NOC.MAX_BURST_SIZE)
    fw.noc_write(0, 0, a0, a0, 0, a5, t5, mcast=True, a=t1, v=t2)
    if chunk != 2:
      fw.add(a0, a0, t5)
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

  fw.cb_push_back(BM.CB_INTERFACE, 0, s7)
  fw.add(s1, s1, s4)
  fw.addi(s6, s6, 1)
  fw.j("reader_sender_block_loop")
  fw.label("reader_sender_done")
  return fw.ret()


def matmul_reader_recv() -> MatmulKernel:
  fw = MatmulKernel()
  fw.release_triscs()
  fw.rta_ptr(BM.RTA_L1_BASE_PTR)
  fw.arg(s7, 7)
  fw.arg(s8, 8)
  fw.li(s0, 0)
  fw.label("reader_recv_block_loop")
  fw.beq(s0, s8, "reader_recv_done")
  fw.cb_reserve_back(BM.CB_INTERFACE, 0, s7)
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
  fw.noc_semaphore_wait(s1, 1)
  fw.cb_push_back(BM.CB_INTERFACE, 0, s7)
  fw.addi(s0, s0, 1)
  fw.j("reader_recv_block_loop")
  fw.label("reader_recv_done")
  return fw.ret()


def matmul_writer_sender() -> MatmulKernel:
  fw = MatmulKernel()
  fw.rta_ptr(NM.RTA_L1_BASE_PTR)
  fw.arg(s0, 0)   # B base
  fw.arg(s1, 1)   # current first tile
  fw.arg(s2, 2)   # inner tile stride
  fw.arg(s3, 3)   # row tile stride
  fw.arg(s4, 4)   # next K-block offset
  fw.arg(s5, 5)   # block_w
  fw.arg(s6, 6)   # block_h
  fw.arg(s7, 7)   # block_tiles
  fw.arg(s8, 8)   # nblocks
  fw.arg(s10, 13) # receiver count

  fw.arg(t0, 17)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=t6)
  fw.noc_semaphore_set(t6, 1)

  fw.li(s6, 0)
  fw.label("writer_sender_block_loop")
  fw.bne(s6, s8, "writer_sender_block_body")
  fw.j("writer_sender_blocks_done")
  fw.label("writer_sender_block_body")
  fw.cb_reserve_back(NM.CB_INTERFACE, 1, s7)
  fw.cb_write_ptr(NM.CB_INTERFACE, 1, out=s9)
  fw.mv(a4, s9)
  fw.mv(a6, s1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(a7, t0, 0)

  for tile_off in (
    0, 1, 2, 3,
    NT, NT + 1, NT + 2, NT + 3,
    2 * NT, 2 * NT + 1, 2 * NT + 2, 2 * NT + 3,
    3 * NT, 3 * NT + 1, 3 * NT + 2, 3 * NT + 3,
    4 * NT, 4 * NT + 1, 4 * NT + 2, 4 * NT + 3,
    5 * NT, 5 * NT + 1, 5 * NT + 2, 5 * NT + 3,
  ):
    fw.mv(a0, s0)
    if tile_off:
      fw.addi(a1, s1, tile_off)
    else:
      fw.mv(a1, s1)
    fw.arg(a2, 29)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, a2)
    fw.local_noc0_coord(a5, x_addr=NM.MY_X, y_addr=NM.MY_Y)
    fw.li(t6, TILE_BYTES)
    fw.noc_read(1, 1, a0, 0, a2, a4, t6, ret_coord=a5, a=t3, v=t5)
    fw.add(a4, a4, t6)

  fw.add(a7, a7, s7)
  fw.noc_reads_flushed(1, a7)
  fw.arg(t0, 16)
  fw.sem_addr(NM.SEM_L1_BASE, t0, out=a3)
  fw.noc_semaphore_wait(a3, s10)
  fw.noc_semaphore_set(a3, 0)

  fw.arg(t0, 13)
  fw.beq(t0, zero, "writer_sender_skip_mcast")
  fw.arg(t1, 9)
  fw.arg(t2, 10)
  fw.arg(t3, 11)
  fw.arg(t5, 12)
  fw.noc_mcast_coord(a5, t1, t2, t3, t5)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(a6, t0, 0)
  fw.addi(a6, a6, 3)
  fw.mv(a0, s9)
  for chunk in range(3):
    fw.li(t5, NOC.MAX_BURST_SIZE)
    fw.noc_write(1, 0, a0, a0, 0, a5, t5, mcast=True, a=t1, v=t2)
    if chunk != 2:
      fw.add(a0, a0, t5)
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

  fw.cb_push_back(NM.CB_INTERFACE, 1, s7)
  fw.add(s1, s1, s4)
  fw.addi(s6, s6, 1)
  fw.j("writer_sender_block_loop")
  fw.label("writer_sender_blocks_done")
  emit_output_writer(fw)
  return fw.ret()


def matmul_writer_recv() -> MatmulKernel:
  fw = MatmulKernel()
  fw.rta_ptr(NM.RTA_L1_BASE_PTR)
  fw.arg(s7, 7)
  fw.arg(s8, 8)
  fw.li(s0, 0)
  fw.label("writer_recv_block_loop")
  fw.beq(s0, s8, "writer_recv_blocks_done")
  fw.cb_reserve_back(NM.CB_INTERFACE, 1, s7)
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
  fw.noc_semaphore_wait(s1, 1)
  fw.cb_push_back(NM.CB_INTERFACE, 1, s7)
  fw.addi(s0, s0, 1)
  fw.j("writer_recv_block_loop")
  fw.label("writer_recv_blocks_done")
  emit_output_writer(fw)
  return fw.ret()


def emit_output_writer(fw: MatmulKernel) -> MatmulKernel:
  fw.arg(s0, 18)  # C base
  fw.arg(s1, 19)  # output tile block start
  fw.arg(a3, 29)  # DRAM bank count

  for sb_base in (0, OUT_SUBBLOCK_W, OUT_SUBBLOCK_H * NT, OUT_SUBBLOCK_H * NT + OUT_SUBBLOCK_W):
    fw.cb_wait_front(NM.CB_INTERFACE, 16, OUT_SUBBLOCK_NUM_TILES)
    fw.cb_read_ptr(NM.CB_INTERFACE, 16, out=a4)
    fw.li(t3, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
    for tile_off in (sb_base, sb_base + 1, sb_base + NT, sb_base + NT + 1):
      fw.lw(s2, t3, 0)
      fw.mv(a0, s0)
      if tile_off:
        fw.addi(a1, s1, tile_off)
      else:
        fw.mv(a1, s1)
      fw.mv(a2, a3)
      fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, a3)
      fw.li(t6, TILE_BYTES)
      fw.noc_write(1, 0, a4, a0, 0, a2, t6, a=t0, v=a5)
      fw.add(a4, a4, t6)
      fw.addi(s2, s2, 1)
      fw.noc_write_barrier(1, s2)
    fw.cb_pop_front(NM.CB_INTERFACE, 16, OUT_SUBBLOCK_NUM_TILES)
  return fw


def emit_trisc0_unpack_row(fw: MatmulTrisc, in0_tile_index: int, in1_tile_index: int) -> MatmulTrisc:
    wait_unp = fw._new_label("wait_unpack_ctx")
    wait_unp_done = fw._new_label("wait_unpack_ctx_done")
    fw.li(t0, TensixRegs.PC_UNPACK_SYNC)
    fw.label(wait_unp)
    fw.lw(t1, t0, 0)
    fw.andi(t1, t1, 0xFE)
    fw.beq(t1, zero, wait_unp_done)
    fw.fence()
    fw.j(wait_unp)
    fw.label(wait_unp_done)

    fw.cb_read_ptr(fw.data["cb_interface"], 0, out=s0)
    fw.cb_iface(fw.data["cb_interface"], 0, out=t6)
    fw.lw(t5, t6, 8)
    fw.li(t4, in0_tile_index)
    fw.mul(a0, t4, t5)
    fw.add(a0, a0, s0)
    fw.addi(a0, a0, -1)

    fw.cb_read_ptr(fw.data["cb_interface"], 1, out=s1)
    fw.cb_iface(fw.data["cb_interface"], 1, out=t6)
    fw.lw(t5, t6, 8)
    fw.li(t4, in1_tile_index)
    fw.mul(a1, t4, t5)
    fw.add(a1, a1, s1)
    fw.addi(a1, a1, -1)

    fw.read32(t2, TLM.TRISC0_UNPACK_CFG_CONTEXT)
    fw.li(t3, TensixRegs.CFG_BASE + THCON_SEC0_REG3_BASE_ADDR32 * 4)
    sec0_ctx_ready = fw._new_label("trisc0_sec0_ctx")
    fw.beq(t2, zero, sec0_ctx_ready)
    fw.addi(t3, t3, 4)
    fw.label(sec0_ctx_ready)
    fw.sw(a1, t3, 0)

    fw.li(t3, TensixRegs.CFG_BASE + THCON_SEC1_REG3_BASE_ADDR32 * 4)
    sec1_ctx_ready = fw._new_label("trisc0_sec1_ctx")
    fw.beq(t2, zero, sec1_ctx_ready)
    fw.addi(t3, t3, 4)
    fw.label(sec1_ctx_ready)
    fw.sw(a0, t3, 0)
    fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
    fw.emit(TTINSN(MATMUL_UNPACK_SRCB_LOAD))
    ctx1 = fw._new_label("trisc0_mop_ctx1")
    ctx_done = fw._new_label("trisc0_mop_done")
    fw.bne(t2, zero, ctx1)
    fw.emit(TTMOP(0, 1, 0))
    fw.j(ctx_done)
    fw.label(ctx1)
    fw.emit(TTMOP(0, 1, 0xFF))
    fw.label(ctx_done)
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
    fw.li(t3, 1)
    fw.sub(t3, t3, t2)
    fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, t3)
    ctx0 = fw._new_label("trisc0_ctx0")
    done = fw._new_label("trisc0_ctx_done")
    fw.beq(t2, zero, ctx0)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
    fw.j(done)
    fw.label(ctx0)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
    fw.label(done)
    return fw


def emit_trisc0_unpack_subblock(fw: MatmulTrisc, in0_offset: int, in1_offset: int) -> MatmulTrisc:
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  for inner in range(IN0_BLOCK_W):
    in1_tile_index = in1_offset + inner * IN1_PER_CORE_W
    for row in range(OUT_SUBBLOCK_H):
      in0_tile_index = in0_offset + row * IN0_BLOCK_W + inner
      emit_trisc0_unpack_row(fw, in0_tile_index, in1_tile_index)
  return fw


def emit_trisc0_reload_subblock(fw: MatmulTrisc) -> MatmulTrisc:
  fw.push_tensix(TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32))
  fw.emit(TTSETADCXX(1, 255, 0))
  fw.write_mop_cfg(MATMUL_RELOAD_UNPACK_MOP_CFG, 0)
  fw.cb_wait_front(fw.data["cb_interface"], 24, OUT_SUBBLOCK_NUM_TILES)
  for tile_index in range(OUT_SUBBLOCK_NUM_TILES):
    fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    wait_unp = fw._new_label("wait_reload_ctx")
    wait_unp_done = fw._new_label("wait_reload_ctx_done")
    fw.li(t0, TensixRegs.PC_UNPACK_SYNC)
    fw.label(wait_unp)
    fw.lw(t1, t0, 0)
    fw.andi(t1, t1, 0xFE)
    fw.beq(t1, zero, wait_unp_done)
    fw.fence()
    fw.j(wait_unp)
    fw.label(wait_unp_done)

    fw.cb_read_ptr(fw.data["cb_interface"], 24, out=s0)
    fw.cb_iface(fw.data["cb_interface"], 24, out=t6)
    fw.lw(t5, t6, 8)
    if tile_index:
      fw.li(t4, tile_index)
      fw.mul(a0, t4, t5)
      fw.add(a0, a0, s0)
    else:
      fw.mv(a0, s0)
    fw.addi(a0, a0, -1)

    fw.read32(t2, TLM.TRISC0_UNPACK_CFG_CONTEXT)
    fw.li(t3, TensixRegs.CFG_BASE + THCON_SEC0_REG3_BASE_ADDR32 * 4)
    sec0_ctx_ready = fw._new_label("trisc0_reload_sec0_ctx")
    fw.beq(t2, zero, sec0_ctx_ready)
    fw.addi(t3, t3, 4)
    fw.label(sec0_ctx_ready)
    fw.sw(a0, t3, 0)
    fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
    fw.li(t3, 1)
    fw.sub(t3, t3, t2)
    fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, t3)
    ctx0 = fw._new_label("trisc0_reload_ctx0")
    done = fw._new_label("trisc0_reload_ctx_done")
    fw.beq(t2, zero, ctx0)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
    fw.j(done)
    fw.label(ctx0)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
    fw.label(done)
  fw.tensix_sync(0)
  fw.cb_pop_front(fw.data["cb_interface"], 24, OUT_SUBBLOCK_NUM_TILES, tensix_ack=True)
  fw.push_tensix(TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32))
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  fw.emit(TTSETADCXX(1, 1023, 0))
  fw.emit(TTSETADCXX(2, 1023, 0))
  fw.write_mop_cfg(MATMUL_UNPACK_AB_MOP_CFG, 0)
  return fw


def matmul_math_init(fw: MatmulTrisc) -> MatmulTrisc:
  fw.math._local_state(fw, Dtype.Float16_b)
  matmul_math_addrmod_init(fw)
  fw.emit(TTREPLAY(16, len(MATMUL_MATH_REPLAY_LOAD), 0, 1))
  for word in MATMUL_MATH_REPLAY_LOAD:
    fw.emit(TTINSN(word))
  fw.write_mop_cfg(MATMUL_MATH_MOP_CFG, 1)
  fw.tensix_sync(1)
  fw.wait_mmio_low_byte_zero(TensixRegs.pc_buf_sem(TensixSem.MATH_PACK))
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.MATH_PACK), init_value=0, max_value=2))
  matmul_math_addrmod_init(fw)
  fw.emit(TTREPLAY(16, len(MATMUL_MATH_REPLAY_LOAD), 0, 1))
  for word in MATMUL_MATH_REPLAY_LOAD:
    fw.emit(TTINSN(word))
  fw.write_mop_cfg(MATMUL_MATH_MOP_CFG, 1)
  return fw


def matmul_math_addrmod_init(fw: MatmulTrisc) -> MatmulTrisc:
  # Full 32x32 bf16 matmul, HiFi2, throttle level 5.
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC0_Src, 2048)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC0, 8)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC0_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC1_Src, 16400)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC1, 8)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC1_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC2_Src, 24640)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC2, 8)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC2_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC4_Src, 28768)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC4, 1024)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC4_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC5_Src, 49344)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC5, 11264)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC5_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC6_Src, 49344)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC6, 35840)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC6_Bias, 0)
  return fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))


def emit_math_dst_write_addr(fw: MatmulTrisc, tile_index: int) -> MatmulTrisc:
  fw.read32(t1, fw.data["dest_offset_id"])
  fw.slli(t1, t1, 9)
  if tile_index:
    fw.addi(t1, t1, tile_index * 64)
  fw.li(t2, 0xB2010000)
  fw.add(t1, t1, t2)
  return fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)


def emit_math_reload_subblock(fw: MatmulTrisc) -> MatmulTrisc:
  fw.math_direct_mova2d_init()
  fw.write_mop_cfg(MATMUL_MATH_RELOAD_MOP_CFG, 1)
  for tile_index in range(OUT_SUBBLOCK_NUM_TILES):
    emit_math_dst_write_addr(fw, tile_index)
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  fw.tensix_sync(1)
  matmul_math_addrmod_init(fw)
  fw.write_mop_cfg(MATMUL_MATH_MOP_CFG, 1)
  return fw


def emit_math_subblock_body(fw: MatmulTrisc, in0_offset: int, in1_offset: int) -> MatmulTrisc:
  for inner in range(IN0_BLOCK_W):
    _ = in0_offset + inner
    _ = in1_offset + inner * IN1_PER_CORE_W
    for tile_index in range(OUT_SUBBLOCK_NUM_TILES):
      emit_math_dst_write_addr(fw, tile_index)
      fw.emit(TTMOP(1, 0, 0))
      fw.emit(TTMOP(1, 0, 0))
      fw.emit(TTSETRWC(1, 0, 0, 0, 0, 15))
      if tile_index & 1:
        fw.emit(TTSETRWC(2, 0, 0, 0, 0, 15))
  return fw


def emit_math_subblock_commit(fw: MatmulTrisc) -> MatmulTrisc:
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_PACK)))
  fw.tensix_sync(1)
  fw.read32(t1, fw.data["dest_offset_id"])
  fw.li(t2, 1)
  fw.sub(t2, t2, t1)
  fw.write32(fw.data["dest_offset_id"], t2)
  return fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.MATH | TensixWait.SFPU))


def emit_math_subblock(fw: MatmulTrisc, in0_offset: int, in1_offset: int) -> MatmulTrisc:
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_ROOM,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  emit_math_subblock_body(fw, in0_offset, in1_offset)
  return emit_math_subblock_commit(fw)


def emit_pack_tile_to_cb(fw: MatmulTrisc, out_cb: int) -> MatmulTrisc:
  fw.cb_reserve_back(fw.data["cb_interface"], out_cb, OUT_SUBBLOCK_NUM_TILES)
  fw.cb_write_ptr(fw.data["cb_interface"], out_cb, out=s0)
  fw.mv(s3, s0)
  fw.cb_iface(fw.data["cb_interface"], out_cb, out=t6)
  fw.lw(s4, t6, 8)
  for tile_index in range(OUT_SUBBLOCK_NUM_TILES):
    if tile_index:
      fw.li(t4, tile_index)
      fw.mul(s0, s4, t4)
      fw.add(s0, s0, s3)
    else:
      fw.mv(s0, s3)
    fw.addi(s0, s0, -1)
    fw.emit(TTSETADC(4, 0, 3, tile_index))
    fw.slli(t1, s0, 8)
    fw.li(t2, 0x00FFFF00)
    fw.and_(t1, t1, t2)
    fw.li(t2, 0x45000018)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.srli(t1, s0, 16)
    fw.slli(t1, t1, 8)
    fw.li(t2, 0x00800000)
    fw.or_(t1, t1, t2)
    fw.li(t2, 0x45000019)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTSTALLWAIT(TensixStall.CFG, WAIT_THCON_AND_PACK))
    fw.emit(TTWRCFG(12, 0, 69))
    fw.srli(t1, s0, 16)
    fw.slli(t1, t1, 8)
    fw.li(t2, 0x45000019)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTDMANOP())

    fw.read32(t1, fw.data["dest_offset_id"])
    fw.li(t2, 0)
    pack_offset_ready = fw._new_label("pack_offset_ready")
    fw.beq(t1, zero, pack_offset_ready)
    fw.li(t2, 512)
    fw.label(pack_offset_ready)
    fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC0, t2)
    fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC1, t2)
    fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC2, t2)
    fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC3, t2)
    fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))
    fw.emit(TTMOP(1, 0, 0))
    fw.tensix_sync(2, tmp=t1)
    fw.emit(TTSETADCZW(4, 0, 0, 0, 0, 5))
  fw.cb_push_back(fw.data["cb_interface"], out_cb, OUT_SUBBLOCK_NUM_TILES, tensix_received=True)
  fw.emit(TTSTALLWAIT(TensixStall.THCON, TensixWait.PACK0))
  fw.read32(t1, fw.data["dest_offset_id"])
  fw.andi(t2, t1, 1)
  fw.li(t3, 0x10104000)
  fw.add(t2, t2, t3)
  fw.write32(TensixRegs.INSTRN_BUF_BASE, t2)
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.MATH_PACK)))
  fw.li(t2, 1)
  fw.sub(t2, t2, t1)
  fw.write32(fw.data["dest_offset_id"], t2)
  fw.emit(TTDMANOP())
  return fw.emit(TTDMANOP())


def emit_pack_reconfig_l1_acc(fw: MatmulTrisc, enabled: bool) -> MatmulTrisc:
  data = 0x04 if enabled else 0x00
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.PACK0))
  fw.push_tensix(TTRMWCIB0(Mask=0x04, Data=data, CfgRegAddr=70))
  fw.push_tensix(TTRMWCIB2(Mask=0x08, Data=(0x08 if enabled else 0x00), CfgRegAddr=71))
  return fw


def matmul_trisc0() -> MatmulTrisc:
  fw = MatmulTrisc(0)
  fw.prologue()
  fw.unpack.init(dtype=Dtype.Float16_b, tile_bytes=TILE_BYTES, mop_cfg=MATMUL_UNPACK_AB_MOP_CFG)
  fw.emit(TTSETADCXX(1, 1023, 0))
  fw.emit(TTSETADCXX(2, 1023, 0))
  fw.emit(TTREPLAY(0, len(MATMUL_UNPACK_REPLAY0_LOAD), 0, 1))
  for word in MATMUL_UNPACK_REPLAY0_LOAD:
    fw.emit(TTINSN(word))
  fw.emit(TTREPLAY(6, len(MATMUL_UNPACK_REPLAY1_LOAD), 0, 1))
  for word in MATMUL_UNPACK_REPLAY1_LOAD:
    fw.emit(TTINSN(word))
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.UNPACK_SYNC), init_value=0, max_value=2))
  fw.init_barrier()
  for block in range(NUM_BLOCKS):
    fw.cb_wait_front(fw.data["cb_interface"], 0, IN0_BLOCK_NUM_TILES)
    fw.cb_wait_front(fw.data["cb_interface"], 1, IN1_BLOCK_NUM_TILES)
    if block == NUM_BLOCKS - 1:
      fw.cb_wait_front(fw.data["cb_interface"], 24, OUT_BLOCK_NUM_TILES)
    for in0_offset in (0, IN0_SUBBLOCK_NUM_TILES):
      for in1_offset in (0, OUT_SUBBLOCK_W):
        if block == NUM_BLOCKS - 1:
          emit_trisc0_reload_subblock(fw)
        emit_trisc0_unpack_subblock(fw, in0_offset, in1_offset)
    fw.cb_pop_front(fw.data["cb_interface"], 0, IN0_BLOCK_NUM_TILES, tensix_ack=True)
    fw.cb_pop_front(fw.data["cb_interface"], 1, IN1_BLOCK_NUM_TILES, tensix_ack=True)
  return fw.ret_kernel()


def matmul_trisc1() -> MatmulTrisc:
  fw = MatmulTrisc(1)
  fw.prologue()
  matmul_math_init(fw)
  fw.init_barrier()
  for block in range(NUM_BLOCKS):
    for in0_offset in (0, IN0_SUBBLOCK_NUM_TILES):
      for in1_offset in (0, OUT_SUBBLOCK_W):
        fw.emit(TTSEMWAIT(
          STALL_MATH_PACK_ROOM,
          TensixSem.mask(TensixSem.MATH_PACK),
          TensixSemWait.STALL_ON_MAX,
        ))
        if block == NUM_BLOCKS - 1:
          emit_math_reload_subblock(fw)
        emit_math_subblock_body(fw, in0_offset, in1_offset)
        emit_math_subblock_commit(fw)
  return fw.ret_kernel()


def matmul_trisc2() -> MatmulTrisc:
  fw = MatmulTrisc(2)
  fw.prologue()
  fw.pack.init(dtype=Dtype.Float16_b, out_cb=16, mop_cfg=MATMUL_PACK_MOP_CFG)
  fw.init_barrier()
  for block in range(NUM_BLOCKS - 1):
    for sb in range(IN0_NUM_SUBBLOCKS * IN1_NUM_SUBBLOCKS):
      fw.emit(TTSEMWAIT(
        STALL_MATH_PACK_DATA,
        TensixSem.mask(TensixSem.MATH_PACK),
        TensixSemWait.STALL_ON_ZERO,
      ))
      if block == 0:
        fw.cb_reserve_back(fw.data["cb_interface"], 16, (sb + 1) * OUT_SUBBLOCK_NUM_TILES)
      emit_pack_reconfig_l1_acc(fw, False)
      emit_pack_tile_to_cb(fw, 24)
  for sb in range(IN0_NUM_SUBBLOCKS * IN1_NUM_SUBBLOCKS):
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_DATA,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_ZERO,
    ))
    emit_pack_reconfig_l1_acc(fw, False)
    emit_pack_tile_to_cb(fw, 16)
  return fw.ret_kernel()


def build_program(a_addr: int, b_addr: int, c_addr: int, num_banks: int, plan: FixedPlan = PLAN) -> Program:
  brisc_sender = matmul_reader_sender()
  brisc_recv = matmul_reader_recv()
  ncrisc_sender = matmul_writer_sender()
  ncrisc_recv = matmul_writer_recv()
  trisc0 = matmul_trisc0()
  trisc1 = matmul_trisc1()
  trisc2 = matmul_trisc2()

  brisc_sender.rta(lambda x, y: reader_args(plan, a_addr, (x, y), num_banks))
  brisc_recv.rta(lambda x, y: reader_args(plan, a_addr, (x, y), num_banks))
  ncrisc_sender.rta(lambda x, y: writer_args(plan, b_addr, c_addr, (x, y), num_banks))
  ncrisc_recv.rta(lambda x, y: writer_args(plan, b_addr, c_addr, (x, y), num_banks))
  trisc0.rta(lambda _x, _y: [])
  trisc1.rta(lambda _x, _y: [])
  trisc2.rta(lambda _x, _y: [])

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
    semaphores=NUM_SEMAPHORES,
    grid=(plan.rows, plan.cols),
  )
  prog.name = f"matmul_{M}x{K}x{N}"
  return prog


def to_bf16_device_bytes(x: np.ndarray) -> bytes:
  u32 = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
  return (u32 >> 16).astype(np.uint16).tobytes()


def from_bf16_device_bytes(data: bytes, shape: tuple[int, ...]) -> np.ndarray:
  u16 = np.frombuffer(data, dtype=np.uint16)
  return (u16.astype(np.uint32) << 16).view(np.float32).reshape(shape)


def make_inputs() -> tuple[np.ndarray, np.ndarray]:
  rng_a = np.random.default_rng(42)
  rng_b = np.random.default_rng(123)
  a = rng_a.uniform(-0.5, 0.5, size=(M, K)).astype(np.float32)
  b = rng_b.uniform(-0.5, 0.5, size=(K, N)).astype(np.float32)
  a = from_bf16_device_bytes(to_bf16_device_bytes(a), (M, K))
  b = from_bf16_device_bytes(to_bf16_device_bytes(b), (K, N))
  return a, b


def sample_coords(m: int, n: int) -> tuple[np.ndarray, np.ndarray]:
  total = m * n
  target = min(total, VALIDATE_SAMPLES)
  fixed = [0, n - 1, (m // 2) * n + (n // 2), (m - 1) * n, total - 1]
  chosen: list[int] = []
  seen: set[int] = set()
  for idx in fixed:
    if 0 <= idx < total and idx not in seen:
      chosen.append(idx)
      seen.add(idx)
      if len(chosen) == target:
        break
  if len(chosen) < target:
    rng = np.random.default_rng(VALIDATE_SEED)
    while len(chosen) < target:
      idx = int(rng.integers(total))
      if idx not in seen:
        chosen.append(idx)
        seen.add(idx)
  flat = np.asarray(chosen, dtype=np.int64)
  return flat // n, flat % n


def validate(a_ref: np.ndarray, b_ref: np.ndarray, c_raw: bytes) -> tuple[float, float]:
  c_got = from_bf16_device_bytes(c_raw, (M, N))
  got_full = c_got.reshape(-1)
  if not np.all(np.isfinite(got_full)):
    bad = int(got_full.size - np.count_nonzero(np.isfinite(got_full)))
    raise AssertionError(f"validation failed: {bad} non-finite outputs")

  sample_rows, sample_cols = sample_coords(M, N)
  row_ids, row_inv = np.unique(sample_rows, return_inverse=True)
  col_ids, col_inv = np.unique(sample_cols, return_inverse=True)
  ref_block = a_ref[row_ids] @ b_ref[:, col_ids]
  ref = ref_block[row_inv, col_inv].astype(np.float32, copy=False).reshape(-1)
  got = c_got[sample_rows, sample_cols].astype(np.float32, copy=False).reshape(-1)

  rel_l2 = float(np.linalg.norm(got - ref) / (np.linalg.norm(ref) + 1e-12))
  max_abs = float(np.max(np.abs(got - ref)))
  ref_std = float(np.std(ref))
  if ref_std < 1e-12:
    pcc = 1.0 if max_abs < 1e-6 else 0.0
  else:
    pcc = float(np.corrcoef(ref, got)[0, 1])
  print(f"Validation ({got.size} samples): PCC={pcc:.6f}, rel_l2={rel_l2:.6f}, max_abs={max_abs:.6f}")
  if pcc < PCC_THRESHOLD or rel_l2 > REL_L2_THRESHOLD:
    raise AssertionError(f"validation failed: PCC={pcc:.6f}, rel_l2={rel_l2:.6f}")
  return pcc, rel_l2


def main() -> None:
  if len(sys.argv) != 1:
    raise SystemExit("Usage: matmul_peak.py")

  a_ref, b_ref = make_inputs()
  device = Device()
  try:
    a_buf = device.alloc_write(to_bf16_device_bytes(a_ref), dtype=Dtype.Float16_b, shape=(M, K), name="A")
    b_buf = device.alloc_write(to_bf16_device_bytes(b_ref), dtype=Dtype.Float16_b, shape=(K, N), name="B")
    c_buf = device.dram.alloc(MT * NT, dtype=Dtype.Float16_b, shape=(M, N), name="C")

    prog = build_program(a_buf.addr, b_buf.addr, c_buf.addr, len(device.dram.bank_tiles))
    timings = device.run(prog)
    c_raw = device.dram_read(c_buf)
    pcc, rel_l2 = validate(a_ref, b_ref, c_raw)

    print(f"PASS matmul_peak {M}x{K}x{N} PCC={pcc:.6f} rel_l2={rel_l2:.6f}")
    for timing in timings:
      name = f"{timing['name']}: " if timing["name"] else ""
      print(f"  {name}{timing['us']:,.1f} us")
  finally:
    device.close()


if __name__ == "__main__":
  main()
