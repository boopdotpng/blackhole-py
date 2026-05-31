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


TILE = 32
TILE_BYTES = Dtype.Float16_b.tile_size

NUM_SEMAPHORES = 4
SUPPORTED_IN0_BLOCK_WS = (1, 2, 3, 4, 5, 6)
SUPPORTED_OUT_SUBBLOCK_H = 2
SUPPORTED_OUT_SUBBLOCK_W = 2

PCC_THRESHOLD = 0.995
REL_L2_THRESHOLD = 0.10
VALIDATE_SAMPLES = 64
VALIDATE_SEED = 0
SYNC_BYTES = 0x100
SYNC_TRISC_START = TensixL1.SIZE - SYNC_BYTES
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


def _ceil_div(a: int, b: int) -> int:
  return (a + b - 1) // b


def _ceil32(x: int) -> int:
  return (x + TILE - 1) & ~(TILE - 1)


def _align_up(x: int, align: int) -> int:
  return _ceil_div(x, align) * align


@dataclass(frozen=True)
class MatmulPlan:
  rows: tuple[int, ...]
  cols: tuple[int, ...]
  mt: int
  kt: int
  nt: int
  per_core_m: int
  per_core_n: int
  in0_block_w: int
  num_blocks: int
  out_subblock_h: int
  out_subblock_w: int
  in0_num_subblocks: int
  in1_num_subblocks: int
  in0_block_num_tiles: int
  in0_subblock_num_tiles: int
  in1_block_num_tiles: int
  in1_per_core_w: int
  out_subblock_num_tiles: int
  out_block_num_tiles: int
  cb0_pages: int
  cb1_pages: int
  cb16_pages: int
  cb24_pages: int

  def grid(self) -> list[list[Core]]:
    return [[(x, y) for x in self.cols] for y in self.rows]

  def cores(self) -> list[Core]:
    return [core for row in self.grid() for core in row]

  @property
  def num_rows(self) -> int:
    return len(self.rows)

  @property
  def num_cols(self) -> int:
    return len(self.cols)

  @property
  def active_core_count(self) -> int:
    return self.num_rows * self.num_cols

  def in0_offsets(self) -> tuple[int, ...]:
    return tuple(sb * self.in0_subblock_num_tiles for sb in range(self.in0_num_subblocks))

  def in1_offsets(self) -> tuple[int, ...]:
    return tuple(sb * self.out_subblock_w for sb in range(self.in1_num_subblocks))

  def output_subblock_bases(self) -> tuple[int, ...]:
    bases = []
    for sbh in range(self.in0_num_subblocks):
      for sbw in range(self.in1_num_subblocks):
        bases.append(sbh * self.out_subblock_h * self.nt + sbw * self.out_subblock_w)
    return tuple(bases)

  def output_tile_offsets(self, sb_base: int) -> tuple[int, ...]:
    offsets = []
    for h in range(self.out_subblock_h):
      for w in range(self.out_subblock_w):
        offsets.append(sb_base + h * self.nt + w)
    return tuple(offsets)


@dataclass(frozen=True)
class TensorLayout:
  m_tile_offset: int
  n_tile_offset: int
  a_row_stride: int
  b_row_stride: int
  c_row_stride: int


@dataclass(frozen=True)
class MatmulChunk:
  m0: int
  n0: int
  m: int
  n: int
  plan: MatmulPlan

  @property
  def m_tile_offset(self) -> int:
    return self.m0 // TILE

  @property
  def n_tile_offset(self) -> int:
    return self.n0 // TILE


def plan_matmul(M: int, K: int, N: int, cores: list[Core]) -> MatmulPlan:
  mt_base = _ceil32(M) // TILE
  kt_base = _ceil32(K) // TILE
  nt_base = _ceil32(N) // TILE
  sbh = SUPPORTED_OUT_SUBBLOCK_H
  sbw = SUPPORTED_OUT_SUBBLOCK_W

  ordered = sorted(set(cores), key=lambda xy: (xy[0], xy[1]))
  if not ordered:
    raise SystemExit("No cores")
  core_set = frozenset(ordered)
  xs = tuple(sorted({x for x, _ in ordered}))
  ys = tuple(sorted({y for _, y in ordered}))
  l1_data_bytes = TensixL1.SIZE - TensixL1.DATA_BUFFER_SPACE_BASE - SYNC_BYTES

  def fits_l1(pcm: int, pcn: int, bw: int) -> bool:
    cb0 = 2 * pcm * bw * TILE_BYTES
    cb1 = 2 * pcn * bw * TILE_BYTES
    cb_out = pcm * pcn * TILE_BYTES
    return cb0 + cb1 + cb_out <= l1_data_bytes

  best: tuple | None = None
  best_score: tuple[int, ...] | None = None
  for bw in SUPPORTED_IN0_BLOCK_WS:
    kt = _align_up(kt_base, bw)
    k_pad_tiles = kt - kt_base
    k_pad_permille = _ceil_div(k_pad_tiles * 1000, kt_base)
    # For big K, a few padded tiles are worth paying for a wider inner block.
    # For small K, avoid large relative padding unless a wider block is exact.
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
          pcm = _align_up(_ceil_div(mt_base, nr), sbh)
          pcn = _align_up(_ceil_div(nt_base, nc), sbw)
          mt = nr * pcm
          nt = nc * pcn
          if not fits_l1(pcm, pcn, bw):
            continue
          out_tiles = pcm * pcn
          score = (-(mt * nt), nr * nc, -out_tiles, bw_score, -k_pad_permille, bw, -abs(nr - nc), nc)
          if best_score is None or score > best_score:
            best = (rows, cols, mt, kt, nt, pcm, pcn, bw)
            best_score = score

  if best is None:
    raise ValueError(f"No valid matmul plan for Mt={mt_base} Kt={kt_base} Nt={nt_base}")
  rows, cols, mt, kt, nt, pcm, pcn, bw = best
  out_tiles = pcm * pcn
  return MatmulPlan(
    rows=tuple(rows), cols=tuple(cols), mt=mt, kt=kt, nt=nt,
    per_core_m=pcm, per_core_n=pcn, in0_block_w=bw, num_blocks=kt // bw,
    out_subblock_h=sbh, out_subblock_w=sbw,
    in0_num_subblocks=pcm // sbh, in1_num_subblocks=pcn // sbw,
    in0_block_num_tiles=pcm * bw, in0_subblock_num_tiles=sbh * bw,
    in1_block_num_tiles=pcn * bw, in1_per_core_w=pcn,
    out_subblock_num_tiles=sbh * sbw, out_block_num_tiles=out_tiles,
    cb0_pages=2 * pcm * bw, cb1_pages=2 * pcn * bw,
    cb16_pages=out_tiles, cb24_pages=out_tiles,
  )


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


def _core_to_rc(plan: MatmulPlan) -> dict[Core, tuple[int, int]]:
  grid = plan.grid()
  return {grid[r][c]: (r, c) for r in range(len(plan.rows)) for c in range(len(plan.cols))}


def reader_args(plan: MatmulPlan, a_addr: int, core_xy: Core, num_banks: int, layout: TensorLayout | None = None) -> list[int]:
  layout = layout or TensorLayout(0, 0, plan.kt, plan.nt, plan.nt)
  core_to_rc = _core_to_rc(plan)
  ri, _ = core_to_rc[core_xy]
  west_cols = [x for x in plan.cols if x < 8]
  east_cols = [x for x in plan.cols if x >= 10]
  w_rect = _mcast_rect_args([c for c in west_cols if c != plan.cols[0]], core_xy[1])
  e_rect = _mcast_rect_args(list(east_cols), core_xy[1])
  sender_xy = plan.grid()[ri][0]
  return [
    a_addr,
    (layout.m_tile_offset + ri * plan.per_core_m) * layout.a_row_stride,
    1,
    layout.a_row_stride,
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


def writer_args(
  plan: MatmulPlan, b_addr: int, c_addr: int, core_xy: Core, num_banks: int,
  layout: TensorLayout | None = None,
) -> list[int]:
  layout = layout or TensorLayout(0, 0, plan.kt, plan.nt, plan.nt)
  core_to_rc = _core_to_rc(plan)
  ri, ci = core_to_rc[core_xy]
  recv_ys = list(plan.rows[1:])
  mcast = (core_xy[0], max(recv_ys), core_xy[0], min(recv_ys), len(recv_ys)) if recv_ys else (0, 0, 0, 0, 0)
  sender_xy = plan.grid()[0][ci]
  out_start = (layout.m_tile_offset + ri * plan.per_core_m) * layout.c_row_stride + layout.n_tile_offset + ci * plan.per_core_n
  return [
    b_addr,
    layout.n_tile_offset + ci * plan.per_core_n,
    1,
    layout.b_row_stride,
    plan.in0_block_w * layout.b_row_stride,
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
    layout.c_row_stride,
    plan.out_subblock_w,
    plan.out_subblock_h * layout.c_row_stride,
    plan.out_subblock_w,
    plan.out_subblock_h,
    plan.out_subblock_num_tiles,
    plan.in1_num_subblocks,
    plan.in0_num_subblocks,
    num_banks,
  ]


def _emit_mcast_chunks(fw: MatmulKernel, noc_id: int, src_addr, coord, total_bytes: int, *, tmp=t5):
  chunks = _ceil_div(total_bytes, NOC.MAX_BURST_SIZE)
  for chunk in range(chunks):
    size = min(NOC.MAX_BURST_SIZE, total_bytes - chunk * NOC.MAX_BURST_SIZE)
    fw.li(tmp, size)
    fw.noc_write(noc_id, 0, src_addr, src_addr, 0, coord, tmp, mcast=True, a=t1, v=t2)
    if chunk != chunks - 1:
      fw.add(src_addr, src_addr, tmp)
  return chunks


def _move_plus_imm(fw: KernelBase, dst, src, imm: int, *, tmp=t4):
  if imm == 0:
    return fw.mv(dst, src)
  if -2048 <= imm <= 2047:
    return fw.addi(dst, src, imm)
  fw.li(tmp, imm)
  return fw.add(dst, src, tmp)


def _jump_if_equal(fw: KernelBase, lhs, rhs, done: str, prefix: str):
  cont = fw._new_label(prefix)
  fw.bne(lhs, rhs, cont)
  fw.j(done)
  fw.label(cont)
  return fw


def _jump_if_ge(fw: KernelBase, lhs, rhs, done: str, prefix: str):
  cont = fw._new_label(prefix)
  fw.blt(lhs, rhs, cont)
  fw.j(done)
  fw.label(cont)
  return fw


def matmul_reader_sender(plan: MatmulPlan) -> MatmulKernel:
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

  fw.mv(a6, s1)
  for row in range(plan.per_core_m):
    for col in range(plan.in0_block_w):
      fw.mv(a0, s0)
      _move_plus_imm(fw, a1, a6, col)
      fw.arg(a2, 23)
      fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
      fw.local_noc0_coord(a5)
      fw.li(t6, TILE_BYTES)
      fw.noc_read(0, 1, a0, 0, a2, a4, t6, ret_coord=a5, a=t3, v=t5)
      fw.add(a4, a4, t6)
    fw.add(a6, a6, s3)

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
  block_bytes = plan.in0_block_num_tiles * TILE_BYTES
  fw.addi(a6, a6, _ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(a0, s9)
  _emit_mcast_chunks(fw, 0, a0, a5, block_bytes)
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
  fw.addi(a6, a6, _ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(a0, s9)
  _emit_mcast_chunks(fw, 0, a0, a5, block_bytes)
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


def matmul_writer_sender(plan: MatmulPlan) -> MatmulKernel:
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

  fw.mv(a6, s1)
  for row in range(plan.in0_block_w):
    for col in range(plan.per_core_n):
      fw.mv(a0, s0)
      _move_plus_imm(fw, a1, a6, col)
      fw.arg(a2, 29)
      fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, a2)
      fw.local_noc0_coord(a5, x_addr=NM.MY_X, y_addr=NM.MY_Y)
      fw.li(t6, TILE_BYTES)
      fw.noc_read(1, 1, a0, 0, a2, a4, t6, ret_coord=a5, a=t3, v=t5)
      fw.add(a4, a4, t6)
    fw.add(a6, a6, s3)

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
  block_bytes = plan.in1_block_num_tiles * TILE_BYTES
  fw.addi(a6, a6, _ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(a0, s9)
  _emit_mcast_chunks(fw, 1, a0, a5, block_bytes)
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
  emit_output_writer(fw, plan)
  return fw.ret()


def matmul_writer_recv(plan: MatmulPlan) -> MatmulKernel:
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
  emit_output_writer(fw, plan)
  return fw.ret()


def emit_output_writer(fw: MatmulKernel, plan: MatmulPlan) -> MatmulKernel:
  fw.arg(s0, 18)  # C base
  fw.arg(s1, 19)   # current subblock row start
  fw.arg(s2, 20)   # output tile stride W
  fw.arg(s3, 21)   # output tile stride H
  fw.arg(s4, 22)   # next subblock W
  fw.arg(s5, 23)   # next subblock H
  fw.arg(s6, 24)   # subblock W
  fw.arg(s7, 25)   # subblock H
  fw.arg(s10, 28)  # subblock rows remaining
  fw.arg(s11, 29)  # DRAM bank count

  sbh_loop = fw._new_label("output_sbh_loop")
  sbh_done = fw._new_label("output_sbh_done")
  sbw_loop = fw._new_label("output_sbw_loop")
  sbw_done = fw._new_label("output_sbw_done")
  h_loop = fw._new_label("output_h_loop")
  h_done = fw._new_label("output_h_done")
  w_loop = fw._new_label("output_w_loop")
  w_done = fw._new_label("output_w_done")

  fw.label(sbh_loop)
  fw.beq(s10, zero, sbh_done)
  fw.mv(a6, s1)  # current subblock tile start
  fw.li(s9, plan.in1_num_subblocks)

  fw.label(sbw_loop)
  fw.beq(s9, zero, sbw_done)
  fw.cb_wait_front(NM.CB_INTERFACE, 16, plan.out_subblock_num_tiles)
  fw.cb_read_ptr(NM.CB_INTERFACE, 16, out=t5)
  fw.li(t3, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(s8, t3, 0)
  fw.addi(s8, s8, plan.out_subblock_num_tiles)
  fw.mv(a7, a6)  # current output row start
  fw.mv(a3, s7)

  fw.label(h_loop)
  fw.beq(a3, zero, h_done)
  fw.mv(t4, a7)
  fw.mv(a4, s6)

  fw.label(w_loop)
  fw.beq(a4, zero, w_done)
  fw.mv(a0, s0)
  fw.mv(a1, t4)
  fw.mv(a2, s11)
  fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)
  fw.li(t6, TILE_BYTES)
  fw.noc_write(1, 0, t5, a0, 0, a2, t6, a=t0, v=a5)
  fw.add(t5, t5, t6)
  fw.add(t4, t4, s2)
  fw.addi(a4, a4, -1)
  fw.j(w_loop)
  fw.label(w_done)

  fw.add(a7, a7, s3)
  fw.addi(a3, a3, -1)
  fw.j(h_loop)
  fw.label(h_done)

  fw.noc_write_barrier(1, s8)
  fw.cb_pop_front(NM.CB_INTERFACE, 16, plan.out_subblock_num_tiles)
  fw.add(a6, a6, s4)
  fw.addi(s9, s9, -1)
  fw.j(sbw_loop)
  fw.label(sbw_done)

  fw.add(s1, s1, s5)
  fw.addi(s10, s10, -1)
  fw.j(sbh_loop)
  fw.label(sbh_done)
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


def emit_trisc0_unpack_row_reg(fw: MatmulTrisc, in0_tile_index, in1_tile_index) -> MatmulTrisc:
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
    fw.mul(a0, in0_tile_index, t5)
    fw.add(a0, a0, s0)
    fw.addi(a0, a0, -1)

    fw.cb_read_ptr(fw.data["cb_interface"], 1, out=s1)
    fw.cb_iface(fw.data["cb_interface"], 1, out=t6)
    fw.lw(t5, t6, 8)
    fw.mul(a1, in1_tile_index, t5)
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


def emit_trisc0_unpack_subblock(fw: MatmulTrisc, plan: MatmulPlan, in0_offset: int, in1_offset: int) -> MatmulTrisc:
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  for inner in range(plan.in0_block_w):
    in1_tile_index = in1_offset + inner * plan.in1_per_core_w
    for row in range(plan.out_subblock_h):
      in0_tile_index = in0_offset + row * plan.in0_block_w + inner
      emit_trisc0_unpack_row(fw, in0_tile_index, in1_tile_index)
  return fw


def emit_trisc0_unpack_subblock_reg(fw: MatmulTrisc, plan: MatmulPlan, in0_offset, in1_offset) -> MatmulTrisc:
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  for inner in range(plan.in0_block_w):
    _move_plus_imm(fw, s10, in1_offset, inner * plan.in1_per_core_w)
    for row in range(plan.out_subblock_h):
      _move_plus_imm(fw, s9, in0_offset, row * plan.in0_block_w + inner)
      emit_trisc0_unpack_row_reg(fw, s9, s10)
  return fw


def emit_trisc0_reload_subblock(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  fw.push_tensix(TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32))
  fw.emit(TTSETADCXX(1, 255, 0))
  fw.write_mop_cfg(MATMUL_RELOAD_UNPACK_MOP_CFG, 0)
  fw.cb_wait_front(fw.data["cb_interface"], 24, plan.out_subblock_num_tiles)
  for tile_index in range(plan.out_subblock_num_tiles):
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
  fw.cb_pop_front(fw.data["cb_interface"], 24, plan.out_subblock_num_tiles, tensix_ack=True)
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


def emit_math_reload_subblock(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  fw.math_direct_mova2d_init()
  fw.write_mop_cfg(MATMUL_MATH_RELOAD_MOP_CFG, 1)
  for tile_index in range(plan.out_subblock_num_tiles):
    emit_math_dst_write_addr(fw, tile_index)
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  fw.tensix_sync(1)
  matmul_math_addrmod_init(fw)
  fw.write_mop_cfg(MATMUL_MATH_MOP_CFG, 1)
  return fw


def emit_math_subblock_body(fw: MatmulTrisc, plan: MatmulPlan, in0_offset: int, in1_offset: int) -> MatmulTrisc:
  for inner in range(plan.in0_block_w):
    _ = in0_offset + inner
    _ = in1_offset + inner * plan.in1_per_core_w
    for tile_index in range(plan.out_subblock_num_tiles):
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


def emit_math_subblock(fw: MatmulTrisc, plan: MatmulPlan, in0_offset: int, in1_offset: int) -> MatmulTrisc:
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_ROOM,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  emit_math_subblock_body(fw, plan, in0_offset, in1_offset)
  return emit_math_subblock_commit(fw)


def emit_pack_tile_to_cb(fw: MatmulTrisc, plan: MatmulPlan, out_cb: int) -> MatmulTrisc:
  fw.cb_reserve_back(fw.data["cb_interface"], out_cb, plan.out_subblock_num_tiles)
  fw.cb_write_ptr(fw.data["cb_interface"], out_cb, out=s0)
  fw.mv(s3, s0)
  fw.cb_iface(fw.data["cb_interface"], out_cb, out=t6)
  fw.lw(s4, t6, 8)
  for tile_index in range(plan.out_subblock_num_tiles):
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
  fw.cb_push_back(fw.data["cb_interface"], out_cb, plan.out_subblock_num_tiles, tensix_received=True)
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


def matmul_trisc0(plan: MatmulPlan) -> MatmulTrisc:
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
  fw.li(s6, 0)
  fw.li(s8, plan.num_blocks)
  block_loop = fw._new_label("trisc0_block_loop")
  block_done = fw._new_label("trisc0_block_done")
  fw.label(block_loop)
  _jump_if_equal(fw, s6, s8, block_done, "trisc0_block_body")
  fw.cb_wait_front(fw.data["cb_interface"], 0, plan.in0_block_num_tiles)
  fw.cb_wait_front(fw.data["cb_interface"], 1, plan.in1_block_num_tiles)
  if plan.num_blocks > 1:
    not_reload_wait = fw._new_label("trisc0_not_reload_wait")
    fw.beq(s6, zero, not_reload_wait)
    fw.cb_wait_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
    fw.label(not_reload_wait)

  fw.li(s4, 0)
  i0_loop = fw._new_label("trisc0_i0_loop")
  i0_done = fw._new_label("trisc0_i0_done")
  fw.label(i0_loop)
  fw.li(t0, plan.in0_num_subblocks)
  _jump_if_ge(fw, s4, t0, i0_done, "trisc0_i0_body")
  fw.li(s5, 0)
  i1_loop = fw._new_label("trisc0_i1_loop")
  i1_done = fw._new_label("trisc0_i1_done")
  fw.label(i1_loop)
  fw.li(t0, plan.in1_num_subblocks)
  _jump_if_ge(fw, s5, t0, i1_done, "trisc0_i1_body")
  fw.li(t0, plan.in0_subblock_num_tiles)
  fw.mul(s2, s4, t0)
  fw.li(t0, plan.out_subblock_w)
  fw.mul(s3, s5, t0)
  if plan.num_blocks > 1:
    not_reload = fw._new_label("trisc0_not_reload")
    fw.beq(s6, zero, not_reload)
    emit_trisc0_reload_subblock(fw, plan)
    fw.label(not_reload)
  emit_trisc0_unpack_subblock_reg(fw, plan, s2, s3)
  fw.addi(s5, s5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(s4, s4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)
  fw.cb_pop_front(fw.data["cb_interface"], 0, plan.in0_block_num_tiles, tensix_ack=True)
  fw.cb_pop_front(fw.data["cb_interface"], 1, plan.in1_block_num_tiles, tensix_ack=True)
  fw.addi(s6, s6, 1)
  fw.j(block_loop)
  fw.label(block_done)
  return fw.ret_kernel()


def matmul_trisc1(plan: MatmulPlan) -> MatmulTrisc:
  fw = MatmulTrisc(1)
  fw.prologue()
  matmul_math_init(fw)
  fw.init_barrier()
  fw.li(s6, 0)
  fw.li(s8, plan.num_blocks)
  block_loop = fw._new_label("trisc1_block_loop")
  block_done = fw._new_label("trisc1_block_done")
  fw.label(block_loop)
  _jump_if_equal(fw, s6, s8, block_done, "trisc1_block_body")
  fw.li(s4, 0)
  i0_loop = fw._new_label("trisc1_i0_loop")
  i0_done = fw._new_label("trisc1_i0_done")
  fw.label(i0_loop)
  fw.li(t0, plan.in0_num_subblocks)
  _jump_if_ge(fw, s4, t0, i0_done, "trisc1_i0_body")
  fw.li(s5, 0)
  i1_loop = fw._new_label("trisc1_i1_loop")
  i1_done = fw._new_label("trisc1_i1_done")
  fw.label(i1_loop)
  fw.li(t0, plan.in1_num_subblocks)
  _jump_if_ge(fw, s5, t0, i1_done, "trisc1_i1_body")
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_ROOM,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  if plan.num_blocks > 1:
    not_reload = fw._new_label("trisc1_not_reload")
    fw.beq(s6, zero, not_reload)
    emit_math_reload_subblock(fw, plan)
    fw.label(not_reload)
  emit_math_subblock_body(fw, plan, 0, 0)
  emit_math_subblock_commit(fw)
  fw.addi(s5, s5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(s4, s4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)
  fw.addi(s6, s6, 1)
  fw.j(block_loop)
  fw.label(block_done)
  return fw.ret_kernel()


def matmul_trisc2(plan: MatmulPlan) -> MatmulTrisc:
  fw = MatmulTrisc(2)
  fw.prologue()
  fw.pack.init(dtype=Dtype.Float16_b, out_cb=16, mop_cfg=MATMUL_PACK_MOP_CFG)
  fw.init_barrier()
  num_subblocks = plan.in0_num_subblocks * plan.in1_num_subblocks
  if plan.num_blocks > 1:
    fw.li(s6, 0)
    partial_block_loop = fw._new_label("trisc2_partial_block_loop")
    partial_block_done = fw._new_label("trisc2_partial_block_done")
    fw.label(partial_block_loop)
    fw.li(t0, plan.num_blocks - 1)
    _jump_if_ge(fw, s6, t0, partial_block_done, "trisc2_partial_block_body")
    fw.li(s5, 0)
    partial_sb_loop = fw._new_label("trisc2_partial_sb_loop")
    partial_sb_done = fw._new_label("trisc2_partial_sb_done")
    fw.label(partial_sb_loop)
    fw.li(t0, num_subblocks)
    _jump_if_ge(fw, s5, t0, partial_sb_done, "trisc2_partial_sb_body")
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_DATA,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_ZERO,
    ))
    not_first_block = fw._new_label("trisc2_not_first_block")
    fw.bne(s6, zero, not_first_block)
    fw.addi(s7, s5, 1)
    fw.li(t0, plan.out_subblock_num_tiles)
    fw.mul(s7, s7, t0)
    fw.cb_reserve_back(fw.data["cb_interface"], 16, s7)
    fw.label(not_first_block)
    emit_pack_reconfig_l1_acc(fw, False)
    emit_pack_tile_to_cb(fw, plan, 24)
    fw.addi(s5, s5, 1)
    fw.j(partial_sb_loop)
    fw.label(partial_sb_done)
    fw.addi(s6, s6, 1)
    fw.j(partial_block_loop)
    fw.label(partial_block_done)

  fw.li(s5, 0)
  final_sb_loop = fw._new_label("trisc2_final_sb_loop")
  final_sb_done = fw._new_label("trisc2_final_sb_done")
  fw.label(final_sb_loop)
  fw.li(t0, num_subblocks)
  _jump_if_ge(fw, s5, t0, final_sb_done, "trisc2_final_sb_body")
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_DATA,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_ZERO,
  ))
  emit_pack_reconfig_l1_acc(fw, False)
  emit_pack_tile_to_cb(fw, plan, 16)
  fw.addi(s5, s5, 1)
  fw.j(final_sb_loop)
  fw.label(final_sb_done)
  return fw.ret_kernel()


def build_program(
  plan: MatmulPlan, a_addr: int, b_addr: int, c_addr: int, num_banks: int,
  layout: TensorLayout | None = None,
) -> Program:
  brisc_sender = matmul_reader_sender(plan)
  brisc_recv = matmul_reader_recv()
  ncrisc_sender = matmul_writer_sender(plan)
  ncrisc_recv = matmul_writer_recv(plan)
  trisc0 = matmul_trisc0(plan)
  trisc1 = matmul_trisc1(plan)
  trisc2 = matmul_trisc2(plan)

  brisc_sender.rta(lambda x, y: reader_args(plan, a_addr, (x, y), num_banks, layout))
  brisc_recv.rta(lambda x, y: reader_args(plan, a_addr, (x, y), num_banks, layout))
  ncrisc_sender.rta(lambda x, y: writer_args(plan, b_addr, c_addr, (x, y), num_banks, layout))
  ncrisc_recv.rta(lambda x, y: writer_args(plan, b_addr, c_addr, (x, y), num_banks, layout))
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
  prog.name = f"matmul_{plan.mt * TILE}x{plan.kt * TILE}x{plan.nt * TILE}"
  return prog


def _split_length(x: int) -> int:
  if x <= TILE:
    return 0
  tiles = _ceil_div(x, TILE)
  split = max(1, tiles // 2) * TILE
  if split >= x:
    split = (tiles - 1) * TILE
  return split


def _buildable_plan(M: int, K: int, N: int, cores: list[Core], num_banks: int) -> MatmulPlan:
  plan = plan_matmul(M, K, N, cores)
  build_program(plan, 0, 0, 0, num_banks).layout(core_xy=plan.cores()[0])
  return plan


def plan_output_chunks(M: int, K: int, N: int, cores: list[Core], num_banks: int) -> list[MatmulChunk]:
  chunks: list[MatmulChunk] = []

  def visit(m0: int, m: int, n0: int, n: int) -> None:
    try:
      chunks.append(MatmulChunk(m0=m0, n0=n0, m=m, n=n, plan=_buildable_plan(m, K, n, cores, num_banks)))
      return
    except ValueError:
      pass

    split_m = _split_length(m)
    split_n = _split_length(n)
    if split_m == 0 and split_n == 0:
      raise ValueError(f"No tiled matmul plan for M={m} K={K} N={n}")

    if split_n == 0 or (split_m != 0 and m >= n):
      visit(m0, split_m, n0, n)
      visit(m0 + split_m, m - split_m, n0, n)
    else:
      visit(m0, m, n0, split_n)
      visit(m0, m, n0 + split_n, n - split_n)

  visit(0, M, 0, N)
  return chunks


def global_padded_shape(M: int, K: int, N: int, chunks: list[MatmulChunk]) -> tuple[int, int, int]:
  mt = max(_ceil32(M) // TILE, *(chunk.m_tile_offset + chunk.plan.mt for chunk in chunks))
  kt = max(_ceil32(K) // TILE, *(chunk.plan.kt for chunk in chunks))
  nt = max(_ceil32(N) // TILE, *(chunk.n_tile_offset + chunk.plan.nt for chunk in chunks))
  return mt * TILE, kt * TILE, nt * TILE


def to_bf16_device_bytes(x: np.ndarray) -> bytes:
  u32 = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
  return (u32 >> 16).astype(np.uint16).tobytes()


def from_bf16_device_bytes(data: bytes, shape: tuple[int, ...]) -> np.ndarray:
  u16 = np.frombuffer(data, dtype=np.uint16)
  return (u16.astype(np.uint32) << 16).view(np.float32).reshape(shape)


def make_inputs(M: int, K: int, N: int) -> tuple[np.ndarray, np.ndarray]:
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


def validate(a_ref: np.ndarray, b_ref: np.ndarray, c_raw: bytes, M: int, N: int, Mp: int, Np: int) -> tuple[float, float]:
  c_full = from_bf16_device_bytes(c_raw, (Mp, Np))
  c_got = c_full[:M, :N]
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


def tflops(m: int, n: int, k: int, us: float) -> float:
  return (2.0 * m * n * k) / (us * 1.0e6) if us > 0 else 0.0


def main() -> None:
  if len(sys.argv) == 1:
    M = K = N = 384
  elif len(sys.argv) == 4:
    M, N, K = (int(arg) for arg in sys.argv[1:])
  else:
    raise SystemExit("Usage: matmul_peak.py [M N K]")
  if M <= 0 or N <= 0 or K <= 0:
    raise SystemExit("M, N, and K must be positive")

  device = Device()
  try:
    num_banks = len(device.dram.bank_tiles)
    chunks = plan_output_chunks(M, K, N, device.cores, num_banks)
    Mp, Kp, Np = global_padded_shape(M, K, N, chunks)
    first = chunks[0].plan
    print(f"Matmul Peak: C[{M},{N}] = A[{M},{K}] @ B[{K},{N}]")
    if (M, K, N) != (Mp, Kp, Np):
      print(f"  padded: A[{Mp},{Kp}] @ B[{Kp},{Np}] -> C[{Mp},{Np}]")
    if len(chunks) == 1:
      print(f"  Mt={first.mt} Kt={first.kt} Nt={first.nt} grid={first.num_rows}x{first.num_cols}")
      print(
        f"  per_core_M={first.per_core_m} per_core_N={first.per_core_n} "
        f"in0_block_w={first.in0_block_w} num_blocks={first.num_blocks}"
      )
      print(f"  subblock: {first.out_subblock_h}h x {first.out_subblock_w}w = {first.out_subblock_num_tiles} tiles")
      print(f"  cores: {first.active_core_count} ({len(device.cores)} available)")
    else:
      print(f"  launches: {len(chunks)} output chunks")
      for i, chunk in enumerate(chunks[:8]):
        plan = chunk.plan
        print(
          f"    chunk {i}: C[{chunk.m0}:{chunk.m0 + chunk.m}, {chunk.n0}:{chunk.n0 + chunk.n}] "
          f"Mt={plan.mt} Kt={plan.kt} Nt={plan.nt} grid={plan.num_rows}x{plan.num_cols} "
          f"per_core={plan.per_core_m}x{plan.per_core_n} bw={plan.in0_block_w}"
        )
      if len(chunks) > 8:
        print(f"    ... {len(chunks) - 8} more chunks")

    a_ref, b_ref = make_inputs(M, K, N)
    a_padded = np.zeros((Mp, Kp), dtype=np.float32)
    b_padded = np.zeros((Kp, Np), dtype=np.float32)
    a_padded[:M, :K] = a_ref
    b_padded[:K, :N] = b_ref

    a_buf = device.alloc_write(to_bf16_device_bytes(a_padded), dtype=Dtype.Float16_b, shape=(Mp, Kp), name="A")
    b_buf = device.alloc_write(to_bf16_device_bytes(b_padded), dtype=Dtype.Float16_b, shape=(Kp, Np), name="B")
    c_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b, shape=(Mp, Np), name="C")

    layout_base = dict(a_row_stride=Kp // TILE, b_row_stride=Np // TILE, c_row_stride=Np // TILE)
    timings = []
    for i, chunk in enumerate(chunks):
      if i and not device.fast_dispatch:
        device._upload_firmware()
      layout = TensorLayout(
        m_tile_offset=chunk.m_tile_offset,
        n_tile_offset=chunk.n_tile_offset,
        **layout_base,
      )
      prog = build_program(chunk.plan, a_buf.addr, b_buf.addr, c_buf.addr, num_banks, layout)
      prog.name = f"matmul_M{M}_N{N}_K{K}" if len(chunks) == 1 else f"matmul_M{M}_N{N}_K{K}_chunk{i}"
      timings.extend(device.run(prog))
    c_raw = device.dram_read(c_buf)
    pcc, rel_l2 = validate(a_ref, b_ref, c_raw, M, N, Mp, Np)

    print(f"PASS matmul_peak M={M} N={N} K={K} PCC={pcc:.6f} rel_l2={rel_l2:.6f}")
    if device.fast_dispatch and timings:
      print("Timing:")
      for timing in timings:
        name = f"{timing['name']}: " if timing["name"] else ""
        print(f"  {name}{timing['us']:,.1f} us")
      total_us = sum(timing["us"] for timing in timings)
      print(f"  aggregate: {total_us:,.1f} us, {tflops(Mp, Np, Kp, total_us):.2f} TFLOP/s")
  finally:
    device.close()


if __name__ == "__main__":
  main()
