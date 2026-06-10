#!/usr/bin/env python3
from __future__ import annotations

import sys
import os
import struct
from dataclasses import dataclass

import numpy as np

from asm import KernelBase
from device import Device
from dsl import (
  TTADDDMAREG, TTDMANOP, TTMOP, TTMOVA2D, TTMULDMAREG, TTMVMUL, TTNOP, TTPACR, TTRDCFG, TTREPLAY,
  TTRMWCIB0, TTRMWCIB1, TTRMWCIB2, TTRMWCIB3, TTSEMGET, TTSEMINIT, TTSEMPOST, TTSEMWAIT, TTSETADC,
  TTSETADCXX, TTSETADCZW, TTSETC16, TTSETDMAREG, TTSETRWC, TTSTALLWAIT, TTUNPACR, TTUNPACR_NOP,
  TTWRCFG, TTZEROACC,
  a0, a1, a2, a3, a4, a5, a6, a7,
  ra,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11,
  sp, t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from pcie import TLBWindow
from ttk import Cb, Noc, Tensix
from ttk.cb import CB as CBRegs
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM, TriscLocalMem as TLM, TriscMailbox
from ttk.noc import NOC
from ttk.tensix import Cfg, MopCfg, TensixL1, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait, ThreadCfg


TILE = 32
TILE_BYTES = Dtype.Float16_b.tile_size
INPUT_DTYPE = Dtype.Float16_b
INPUT_TILE_BYTES = INPUT_DTYPE.tile_size

NUM_SEMAPHORES = 4
RUNS = 5
MAX_IN0_BLOCK_W = 6
INPUT_BUFFER_FACTOR = 2
MAX_PER_CORE_M = 0
MAX_PER_CORE_N = 0
SPLIT_AXIS = "auto"
K_GROUP = 1
OUTPUT_NOC = 1
OUTPUT_STAGGER_ITERS = 0
STREAM_PARTIAL_CB24 = False
MATH_BACKEND = "mop"
HIFI = os.environ.get("HIFI", "") == "1"
MATH_FIDELITY = "hifi2"
SKIP_PADDED_N = False
ENABLE_BREADCRUMBS = os.environ.get("BREADCRUMBS", "") == "1"
SUPPORTED_IN0_BLOCK_WS = tuple(range(1, MAX_IN0_BLOCK_W + 1))
SUPPORTED_OUT_SUBBLOCK_H = 2
SUPPORTED_OUT_SUBBLOCK_W = 2

PCC_THRESHOLD = 0.995
REL_L2_THRESHOLD = 0.10
VALIDATE_SAMPLES = 64
VALIDATE_SEED = 0
SYNC_BYTES = 0x100
SYNC_TRISC_START = TensixL1.SIZE - SYNC_BYTES
SYNC_TRISC_INIT = SYNC_TRISC_START + 16
# Byte-triplet BRISC writes to SYNC_TRISC_START to release the three TRISCs
# (one 0x01 release byte per TRISC; each clears its own byte after starting).
TRISC_START_RELEASE = 0x00010101


Core = tuple[int, int]


@dataclass(frozen=True)
class RiscSync:
  start: int
  trisc_init: int


SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)
STALL_MATH_PACK_ROOM = TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU
STALL_MATH_PACK_DATA = TensixStall.TDMA
WAIT_THCON_AND_PACK = TensixWait.THCON | TensixWait.PACK0
THCON_SEC0_REG3_BASE_ADDR32 = Cfg.THCON_SEC0_REG3_Base_address.addr32
THCON_SEC1_REG3_BASE_ADDR32 = Cfg.THCON_SEC1_REG3_Base_address.addr32
THCON_SEC0_REG3_BASE_CNTX1_ADDR32 = Cfg.THCON_SEC0_REG3_Base_cntx1_address.addr32
THCON_SEC1_REG3_BASE_CNTX1_ADDR32 = Cfg.THCON_SEC1_REG3_Base_cntx1_address.addr32
UNPACK_TMP_LO_GPR = 0x12
UNPACK_TILE_SIZE_A_GPR = 0x24
UNPACK_TILE_SIZE_B_GPR = 0x25
UNPACK_KT_DIM_GPR = 0x26
UNPACK_KT_DIM_GPR_16B = UNPACK_KT_DIM_GPR * 2
EXPERIMENTAL_THROTTLE0 = False
PROFILE_BASE = 0x17B000
PROFILE_RECORD_BYTES = 0x20
PROFILE_TRISC0 = PROFILE_BASE + 0x00
PROFILE_TRISC1 = PROFILE_BASE + PROFILE_RECORD_BYTES
PROFILE_TRISC2 = PROFILE_BASE + 2 * PROFILE_RECORD_BYTES
PROFILE_BRISC = PROFILE_BASE + 3 * PROFILE_RECORD_BYTES
PROFILE_NCRISC = PROFILE_BASE + 4 * PROFILE_RECORD_BYTES
PROFILE_NCRISC_INPUT = PROFILE_BASE + 5 * PROFILE_RECORD_BYTES
PROFILE_NCRISC_OUTPUT = PROFILE_BASE + 6 * PROFILE_RECORD_BYTES
PROFILE_NAMES = (
  ("brisc", PROFILE_BRISC),
  ("ncrisc", PROFILE_NCRISC),
  ("ncrisc_input", PROFILE_NCRISC_INPUT),
  ("ncrisc_output", PROFILE_NCRISC_OUTPUT),
  ("trisc0", PROFILE_TRISC0),
  ("trisc1", PROFILE_TRISC1),
  ("trisc2", PROFILE_TRISC2),
)
PROFILE_TMP_BRISC = PROFILE_BASE + 0x100
PROFILE_TMP_NCRISC = PROFILE_BASE + 0x104
PROFILE_TMP_TRISC0 = PROFILE_BASE + 0x108
PROFILE_TMP_TRISC1 = PROFILE_BASE + 0x10C
PROFILE_TMP_TRISC2 = PROFILE_BASE + 0x110
PROFILE_TMP_NCRISC_PHASE = PROFILE_BASE + 0x114
PROFILE_COUNTER_BASE = PROFILE_BASE + 0x120
PROFILE_COUNTERS = (
  ("brisc_input", PROFILE_COUNTER_BASE + 0x00),
  ("ncrisc_input", PROFILE_COUNTER_BASE + 0x04),
  ("ncrisc_output", PROFILE_COUNTER_BASE + 0x08),
  ("trisc0_cb_in", PROFILE_COUNTER_BASE + 0x0C),
  ("trisc0_unpack_ctx", PROFILE_COUNTER_BASE + 0x10),
  ("trisc1_pack_room", PROFILE_COUNTER_BASE + 0x14),
  ("trisc1_math_sync", PROFILE_COUNTER_BASE + 0x18),
  ("trisc2_pack_data", PROFILE_COUNTER_BASE + 0x1C),
  ("trisc2_pack_body", PROFILE_COUNTER_BASE + 0x20),
  ("ncrisc_output_wait", PROFILE_COUNTER_BASE + 0x24),
  ("ncrisc_output_issue", PROFILE_COUNTER_BASE + 0x28),
  ("ncrisc_output_barrier_pop", PROFILE_COUNTER_BASE + 0x2C),
)
DEBUG_TRISC0 = 0x17A200
DEBUG_TRISC1 = 0x17A240
DEBUG_TRISC2 = 0x17A280
DEBUG_NCRISC_OUTPUT = 0x17A180
MEM_L1_ARC_FW_SCRATCH = 16
MATH_THROTTLED_MOP_STATUS = 0xFFB00020


def math_mode_label() -> str:
  fidelity = f"/{MATH_FIDELITY}"
  if MATH_BACKEND == "direct":
    return f"direct-no-delay{fidelity}"
  mode = "mop-no-delay" if EXPERIMENTAL_THROTTLE0 else "mop-throttled"
  return f"{mode}{fidelity}"


# MOP (macro-op) expander templates and replay-buffer payloads, written in the
# add1 example's style: named instruction builders instead of raw hex words.
# A MopCfg expands a 7-slot template under two loop counts; write_mop_cfg /
# *.init accept the MopCfg directly (see ttk.tensix.MopCfg). Reusable slots:
_UNPACK_NOP = TTUNPACR_NOP(Unpacker_Select=1, Set_Dvalid=1, Unpack_Pop=1)
_MATH_MOVA2D = TTMOVA2D(addr_mode=2, instr_mod=2)


def MOP_REPLAY(start_idx: int, length: int) -> int:
  if start_idx < 16:
    raise ValueError("math MOP replay encoding is only validated here for replay slots >= 16")
  return TTREPLAY(start_idx, length).raw_word()

# From llk_unpack_AB_matmul_init(ct_dim=2, rt_dim=2, kt_dim=6), no partial
# faces. In reuse-A mode the explicit runtime UNPACR loads in0 into SrcB; the
# two MOP replay slots below load the two in1 tiles into SrcA. The empty (zero)
# slots are stepped over by the expander (both loop counts are 0).
MATMUL_UNPACK_AB_MOP_CFG = MopCfg(
  loop_outer=0, loop_inner=0,
  template=[0, TTREPLAY(0, 6), 0, 0, 0, TTREPLAY(6, 6), 0],
)

# From matmul_compute_trisc2.kernel.dis around 0x819c: pack_tile MOP template.
MATMUL_PACK_MOP_CFG = MopCfg(
  loop_outer=4, loop_inner=4,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    TTPACR(),
    TTNOP(),
    TTPACR(AddrMode=1, Last=1),
    TTPACR(AddrMode=2),
  ],
)

# THROTTLE0 means TT-Metal throttle level 0 here: no inserted delay NOPs.
MATMUL_MATH_MOP_CFG_THROTTLE0 = MopCfg(
  loop_outer=1, loop_inner=2,
  template=[
    TTNOP(),
    TTSETRWC(1, 0, 0, 0, 0, 15),
    TTNOP(),
    MOP_REPLAY(16, 16),
    TTNOP(),
    MOP_REPLAY(16, 16),
    MOP_REPLAY(16, 16),
  ],
)

# THROTTLE0 means TT-Metal throttle level 0 here: no inserted delay NOPs.
MATMUL_MATH_MOP_CFG_THROTTLE0_REUSE_B = MopCfg(
  loop_outer=2, loop_inner=2,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    MOP_REPLAY(16, 11),
    TTNOP(),
    TTMVMUL(addr_mode=5),
    TTMVMUL(addr_mode=4),
  ],
)

# Throttled HiFi2 matmul MOP. The expander adds the ADDR_MOD_4/ADDR_MOD_5 final
# MVMULs; these slots carry the nested replay trigger plus the three throttled
# MVMULs from run_throttled_sequence<5>().
MATMUL_MATH_MOP_CFG = MopCfg(
  loop_outer=2, loop_inner=2,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    TTREPLAY(16, 11),
    TTMVMUL(addr_mode=2),
    TTMVMUL(addr_mode=5),
    TTMVMUL(addr_mode=4),
  ],
)

# From matmul_compute_trisc1.kernel.dis around 0x7864: copy_tile-to-dst MOP
# used for reloading cb24 partials before the second K block accumulates.
MATMUL_MATH_RELOAD_MOP_CFG = MopCfg(
  loop_outer=4, loop_inner=2,
  template=[
    TTNOP(),
    TTSETRWC(clear_ab_vld=3, BitMask=3),
    TTNOP(),
    _MATH_MOVA2D,
    TTNOP(),
    _MATH_MOVA2D,
    _MATH_MOVA2D,
  ],
)

# THROTTLE0 means TT-Metal throttle level 0 here: 16 consecutive MVMULs.
MATMUL_MATH_REPLAY_LOAD_THROTTLE0 = [
  TTMVMUL(),
  TTMVMUL(addr_mode=1),
  TTMVMUL(),
  TTMVMUL(addr_mode=2),
  TTMVMUL(),
  TTMVMUL(addr_mode=1),
  TTMVMUL(),
  TTMVMUL(addr_mode=4),
  TTMVMUL(),
  TTMVMUL(addr_mode=1),
  TTMVMUL(),
  TTMVMUL(addr_mode=2),
  TTMVMUL(),
  TTMVMUL(addr_mode=1),
  TTMVMUL(),
  TTMVMUL(addr_mode=5),
]

# Replay payload loaded into the math replay buffer: three throttled MVMULs
# (addr-mode 0, 1, 0) interleaved with delay NOPs.
MATMUL_MATH_REPLAY_LOAD = [
  TTNOP(), TTNOP(), TTMVMUL(),
  TTNOP(), TTNOP(), TTMVMUL(addr_mode=1),
  TTNOP(), TTNOP(), TTMVMUL(),
  TTNOP(), TTNOP(),
]

# Unpacker replay payloads for the two cfg contexts (THCON_SEC*_REG3 base addr32
# 0x4C / 0x4D): read cfg -> add dma reg -> stall on CFG/THCON -> write cfg back.
MATMUL_UNPACK_REPLAY0_LOAD = [
  TTUNPACR(OvrdThreadId=1, SetDatValid=1, Last=1),
  TTRDCFG(0xC, THCON_SEC0_REG3_BASE_ADDR32),
  TTADDDMAREG(0, 0xC, 0xC, UNPACK_TILE_SIZE_A_GPR),
  TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON),
  TTWRCFG(0xC, 0, THCON_SEC0_REG3_BASE_ADDR32),
  TTNOP(),
]

MATMUL_UNPACK_REPLAY1_LOAD = [
  TTUNPACR(OvrdThreadId=1, SetDatValid=1, Last=1),
  TTRDCFG(0xC, THCON_SEC0_REG3_BASE_CNTX1_ADDR32),
  TTADDDMAREG(0, 0xC, 0xC, UNPACK_TILE_SIZE_A_GPR),
  TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON),
  TTWRCFG(0xC, 0, THCON_SEC0_REG3_BASE_CNTX1_ADDR32),
  TTNOP(),
]

MATMUL_UNPACK_REPLAY_SRCB0_LOAD = [
  TTUNPACR(Unpack_block_selection=1, OvrdThreadId=1, SetDatValid=1, Last=1),
  TTRDCFG(0xC, THCON_SEC1_REG3_BASE_ADDR32),
  TTADDDMAREG(0, 0xC, 0xC, UNPACK_TMP_LO_GPR),
  TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON),
  TTWRCFG(0xC, 0, THCON_SEC1_REG3_BASE_ADDR32),
  TTNOP(),
]

MATMUL_UNPACK_REPLAY_SRCB1_LOAD = [
  TTUNPACR(Unpack_block_selection=1, OvrdThreadId=1, SetDatValid=1, Last=1),
  TTRDCFG(0xC, THCON_SEC1_REG3_BASE_CNTX1_ADDR32),
  TTADDDMAREG(0, 0xC, 0xC, UNPACK_TMP_LO_GPR),
  TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON),
  TTWRCFG(0xC, 0, THCON_SEC1_REG3_BASE_CNTX1_ADDR32),
  TTNOP(),
]

# Runtime UNPACR that loads in1 into SrcA.
MATMUL_UNPACK_SRCA_LOAD = TTUNPACR(OvrdThreadId=1, SetDatValid=1, Last=1)

# Runtime UNPACR that loads in0 into SrcB (block-selection bit set).
MATMUL_UNPACK_SRCB_LOAD = TTUNPACR(
  Unpack_block_selection=1, OvrdThreadId=1, SetDatValid=1, Last=1,
)


def _plan_reuses_a(plan: MatmulPlan) -> bool:
  return plan.out_subblock_w >= plan.out_subblock_h


def _emit_trisc0_unpack_replay_init(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  if _plan_reuses_a(plan):
    replay0 = MATMUL_UNPACK_REPLAY0_LOAD
    replay1 = MATMUL_UNPACK_REPLAY1_LOAD
  else:
    fw.emit(TTSETDMAREG(0, plan.in0_block_w, 0, UNPACK_KT_DIM_GPR_16B))
    fw.emit(TTMULDMAREG(0, UNPACK_TMP_LO_GPR, UNPACK_TILE_SIZE_B_GPR, UNPACK_KT_DIM_GPR))
    replay0 = MATMUL_UNPACK_REPLAY_SRCB0_LOAD
    replay1 = MATMUL_UNPACK_REPLAY_SRCB1_LOAD
  fw.emit(TTREPLAY(0, len(replay0), 0, 1))
  for word in replay0:
    fw.emit(word)
  fw.emit(TTREPLAY(6, len(replay1), 0, 1))
  for word in replay1:
    fw.emit(word)
  return fw

MATMUL_RELOAD_UNPACK_MOP_CFG = MopCfg(
  loop_outer=4, loop_inner=1,
  template=[
    TTUNPACR(AddrMode=1, OvrdThreadId=1, SetDatValid=1, Last=1),
    TTNOP(), TTNOP(),
    _UNPACK_NOP,
    TTNOP(),
    _UNPACK_NOP,
    _UNPACK_NOP,
  ],
)


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
  logical_mt: int = 0
  logical_nt: int = 0

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
    cb0 = INPUT_BUFFER_FACTOR * pcm * bw * TILE_BYTES
    cb1 = INPUT_BUFFER_FACTOR * pcn * bw * TILE_BYTES
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
          if MAX_PER_CORE_M and pcm > MAX_PER_CORE_M:
            continue
          if MAX_PER_CORE_N and pcn > MAX_PER_CORE_N:
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
    cb0_pages=INPUT_BUFFER_FACTOR * pcm * bw, cb1_pages=INPUT_BUFFER_FACTOR * pcn * bw,
    cb16_pages=out_tiles, cb24_pages=out_tiles,
    logical_mt=mt_base, logical_nt=nt_base,
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
    return self.write32(SYNC_TRISC_START, TRISC_START_RELEASE)


class MatmulTrisc(KernelBase, Tensix, Cb):
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
    _valid_in1_subblocks(plan, core_xy),
  ]


def _valid_in1_subblocks(plan: MatmulPlan, core_xy: Core) -> int:
  if not SKIP_PADDED_N:
    return plan.in1_num_subblocks
  _, ci = _core_to_rc(plan)[core_xy]
  logical_nt = plan.logical_nt or plan.nt
  local_valid_tiles = max(0, min(plan.per_core_n, logical_nt - ci * plan.per_core_n))
  return min(plan.in1_num_subblocks, _ceil_div(local_valid_tiles, plan.out_subblock_w))


def trisc_args(plan: MatmulPlan, core_xy: Core) -> list[int]:
  return [_valid_in1_subblocks(plan, core_xy)]


def _emit_trisc_valid_in1(fw: MatmulTrisc, out=t0) -> MatmulTrisc:
  fw.read32(out, fw.data["rta_l1_base"], tmp_addr=t1)
  return fw.lw(out, out, 0)


def _emit_trisc_valid_subblocks(fw: MatmulTrisc, plan: MatmulPlan, out=t0) -> MatmulTrisc:
  _emit_trisc_valid_in1(fw, out)
  fw.li(t1, plan.in0_num_subblocks)
  return fw.mul(out, out, t1)


def _emit_trisc_valid_cb24_tiles(fw: MatmulTrisc, plan: MatmulPlan, out=t0) -> MatmulTrisc:
  _emit_trisc_valid_in1(fw, out)
  fw.li(t1, plan.in0_num_subblocks * plan.out_subblock_num_tiles)
  return fw.mul(out, out, t1)


def _emit_trisc2_pad_cb24_to_full_block(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  _emit_trisc_valid_cb24_tiles(fw, plan, s7)
  fw.li(t0, plan.out_block_num_tiles)
  fw.sub(s7, t0, s7)
  done = fw._new_label("trisc2_skip_pad_cb24_done")
  fw.beq(s7, zero, done)
  fw.cb_reserve_back(fw.data["cb_interface"], 24, s7)
  fw.cb_push_back(fw.data["cb_interface"], 24, s7, tensix_received=True)
  fw.label(done)
  return fw


def _emit_mcast_chunks(fw: MatmulKernel, noc_id: int, src_addr, coord, total_bytes: int, *, tmp=t5):
  chunks = _ceil_div(total_bytes, NOC.MAX_BURST_SIZE)
  for chunk in range(chunks):
    size = min(NOC.MAX_BURST_SIZE, total_bytes - chunk * NOC.MAX_BURST_SIZE)
    fw.li(tmp, size)
    fw.noc_write(noc_id, 0, src_addr, src_addr, 0, coord, tmp, mcast=True, a=t1, v=t2)
    if chunk != chunks - 1:
      fw.add(src_addr, src_addr, tmp)
  return chunks


def emit_output_write_state_setup(fw: MatmulKernel) -> MatmulKernel:
  fw.noc_wait_cmd_ready(OUTPUT_NOC, 0, addr=t0, val=t1)
  fw.noc_cmd_reg(OUTPUT_NOC, 0, NOC.CTRL, NOC.CMD_WR_FIELD, addr=t0, tmp=t1)
  fw.noc_cmd_reg(OUTPUT_NOC, 0, NOC.RET_ADDR_MID, 0, addr=t0, tmp=t1)
  fw.li(t6, TILE_BYTES)
  fw.noc_cmd_reg(OUTPUT_NOC, 0, NOC.AT_LEN_BE, t6, addr=t0, tmp=t1)
  return fw.noc_cmd_reg(OUTPUT_NOC, 0, NOC.AT_LEN_BE_1, 0, addr=t0, tmp=t1)


def emit_output_write_stateful(fw: MatmulKernel, src, dst_lo, dst_coord) -> MatmulKernel:
  fw.noc_wait_cmd_ready(OUTPUT_NOC, 0, addr=t0, val=a5)
  fw.noc_cmd_reg(OUTPUT_NOC, 0, NOC.TARG_ADDR_LO, src, addr=t0, tmp=a5)
  fw.noc_cmd_reg(OUTPUT_NOC, 0, NOC.RET_ADDR_LO, dst_lo, addr=t0, tmp=a5)
  fw.noc_cmd_reg(OUTPUT_NOC, 0, NOC.RET_ADDR_COORDINATE, dst_coord, addr=t0, tmp=a5)
  return fw.noc_cmd_reg(OUTPUT_NOC, 0, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=t0, tmp=a5)


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


PROFILE_STAMPS = os.environ.get("MATMUL_PROFILE", "") == "1"


def emit_profile_stamp(fw: KernelBase, addr: int):
  if not PROFILE_STAMPS:
    return fw
  from ttk.tensix import TensixMMIO as _MMIO
  fw.li(t1, _MMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.lw(t2, t1, 0)
  fw.li(t0, addr)
  fw.sw(t2, t0, 0)
  fw.lw(t2, t1, 8)
  fw.sw(t2, t0, 4)
  return fw


def emit_progress_mark(fw: KernelBase, addr: int, code: int, block_reg=s6, i0_reg=s4, i1_reg=s5):
  if not ENABLE_BREADCRUMBS:
    return fw
  fw.write32(addr + 0, code, tmp_addr=t0, tmp_val=t1)
  fw.write32(addr + 4, block_reg, tmp_addr=t0, tmp_val=t1)
  fw.write32(addr + 8, i0_reg, tmp_addr=t0, tmp_val=t1)
  fw.write32(addr + 12, i1_reg, tmp_addr=t0, tmp_val=t1)
  return fw


def emit_cb_debug_snapshot(fw: KernelBase, addr: int, cb_index: int, code: int):
  emit_progress_mark(fw, addr, code)
  return fw


def emit_output_launch_stagger(fw: KernelBase):
  if OUTPUT_STAGGER_ITERS == 0:
    return fw
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB105, block_reg=s10, i0_reg=s9, i1_reg=s1)
  fw.read32(t0, NM.MY_X, tmp_addr=t2)
  fw.read32(t1, NM.MY_Y, tmp_addr=t2)
  fw.add(t0, t0, t1)
  fw.li(t1, OUTPUT_STAGGER_ITERS)
  fw.mul(t0, t0, t1)
  delay_loop = fw._new_label("output_launch_stagger")
  delay_done = fw._new_label("output_launch_stagger_done")
  fw.label(delay_loop)
  fw.beq(t0, zero, delay_done)
  fw.addi(t0, t0, -1)
  fw.j(delay_loop)
  fw.label(delay_done)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB106, block_reg=s10, i0_reg=s9, i1_reg=s1)
  return fw


def emit_profile_accum_start(fw: KernelBase, tmp_addr: int):
  if not PROFILE_STAMPS:
    return fw
  from ttk.tensix import TensixMMIO as _MMIO
  fw.li(t1, _MMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.lw(t2, t1, 0)
  fw.li(t0, tmp_addr)
  fw.sw(t2, t0, 0)
  return fw


def emit_profile_accum_end(fw: KernelBase, counter_addr: int, tmp_addr: int):
  if not PROFILE_STAMPS:
    return fw
  from ttk.tensix import TensixMMIO as _MMIO
  fw.li(t1, _MMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  fw.lw(t2, t1, 0)
  fw.li(t0, tmp_addr)
  fw.lw(t1, t0, 0)
  fw.sub(t2, t2, t1)
  fw.li(t0, counter_addr)
  fw.lw(t1, t0, 0)
  fw.add(t2, t2, t1)
  fw.sw(t2, t0, 0)
  return fw


def matmul_reader_sender(plan: MatmulPlan) -> MatmulKernel:
  fw = MatmulKernel()
  fw.release_triscs()
  emit_profile_stamp(fw, PROFILE_BRISC)
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
  emit_profile_accum_start(fw, PROFILE_TMP_BRISC)
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
  emit_profile_accum_end(fw, PROFILE_COUNTERS[0][1], PROFILE_TMP_BRISC)
  fw.add(s1, s1, s4)
  fw.addi(s6, s6, 1)
  fw.j("reader_sender_block_loop")
  fw.label("reader_sender_done")
  emit_profile_stamp(fw, PROFILE_BRISC + 8)
  return fw.ret()


def matmul_reader_recv() -> MatmulKernel:
  fw = MatmulKernel()
  fw.release_triscs()
  emit_profile_stamp(fw, PROFILE_BRISC)
  fw.rta_ptr(BM.RTA_L1_BASE_PTR)
  fw.arg(s7, 7)
  fw.arg(s8, 8)
  fw.li(s0, 0)
  fw.label("reader_recv_block_loop")
  fw.beq(s0, s8, "reader_recv_done")
  emit_profile_accum_start(fw, PROFILE_TMP_BRISC)
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
  emit_profile_accum_end(fw, PROFILE_COUNTERS[0][1], PROFILE_TMP_BRISC)
  fw.addi(s0, s0, 1)
  fw.j("reader_recv_block_loop")
  fw.label("reader_recv_done")
  emit_profile_stamp(fw, PROFILE_BRISC + 8)
  return fw.ret()


def matmul_writer_sender(plan: MatmulPlan) -> MatmulKernel:
  fw = MatmulKernel()
  emit_profile_stamp(fw, PROFILE_NCRISC)
  emit_profile_stamp(fw, PROFILE_NCRISC_INPUT)
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
  emit_profile_accum_start(fw, PROFILE_TMP_NCRISC)
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
  emit_profile_accum_end(fw, PROFILE_COUNTERS[1][1], PROFILE_TMP_NCRISC)
  fw.add(s1, s1, s4)
  fw.addi(s6, s6, 1)
  fw.j("writer_sender_block_loop")
  fw.label("writer_sender_blocks_done")
  emit_profile_stamp(fw, PROFILE_NCRISC_INPUT + 8)
  emit_output_writer(fw, plan)
  emit_profile_stamp(fw, PROFILE_NCRISC + 8)
  return fw.ret()


def matmul_writer_recv(plan: MatmulPlan) -> MatmulKernel:
  fw = MatmulKernel()
  emit_profile_stamp(fw, PROFILE_NCRISC)
  emit_profile_stamp(fw, PROFILE_NCRISC_INPUT)
  fw.rta_ptr(NM.RTA_L1_BASE_PTR)
  fw.arg(s7, 7)
  fw.arg(s8, 8)
  fw.li(s0, 0)
  fw.label("writer_recv_block_loop")
  fw.beq(s0, s8, "writer_recv_blocks_done")
  emit_profile_accum_start(fw, PROFILE_TMP_NCRISC)
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
  emit_profile_accum_end(fw, PROFILE_COUNTERS[1][1], PROFILE_TMP_NCRISC)
  fw.addi(s0, s0, 1)
  fw.j("writer_recv_block_loop")
  fw.label("writer_recv_blocks_done")
  emit_profile_stamp(fw, PROFILE_NCRISC_INPUT + 8)
  emit_output_writer(fw, plan)
  emit_profile_stamp(fw, PROFILE_NCRISC + 8)
  return fw.ret()


def emit_output_writer(fw: MatmulKernel, plan: MatmulPlan) -> MatmulKernel:
  emit_profile_stamp(fw, PROFILE_NCRISC_OUTPUT)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB100, block_reg=s10, i0_reg=s9, i1_reg=s1)
  emit_profile_accum_start(fw, PROFILE_TMP_NCRISC)
  emit_output_write_state_setup(fw)
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
  emit_output_launch_stagger(fw)

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
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB110, block_reg=s10, i0_reg=s9, i1_reg=s1)
  fw.mv(a6, s1)  # current subblock tile start
  if SKIP_PADDED_N:
    fw.arg(s9, 30)  # valid subblock columns
  else:
    fw.li(s9, plan.in1_num_subblocks)

  fw.label(sbw_loop)
  fw.beq(s9, zero, sbw_done)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB120, block_reg=s10, i0_reg=s9, i1_reg=a6)
  emit_cb_debug_snapshot(fw, DEBUG_NCRISC_OUTPUT + 0x40, 16, 0xB121)
  emit_profile_accum_start(fw, PROFILE_TMP_NCRISC_PHASE)
  fw.cb_wait_front(NM.CB_INTERFACE, 16, plan.out_subblock_num_tiles)
  emit_cb_debug_snapshot(fw, DEBUG_NCRISC_OUTPUT + 0x40, 16, 0xB131)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB130, block_reg=s10, i0_reg=s9, i1_reg=a6)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[9][1], PROFILE_TMP_NCRISC_PHASE)
  emit_profile_accum_start(fw, PROFILE_TMP_NCRISC_PHASE)
  fw.cb_read_ptr(NM.CB_INTERFACE, 16, out=t5)
  fw.li(t3, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (OUTPUT_NOC << NOC.INSTANCE_OFFSET_BIT))
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
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB132, block_reg=s10, i0_reg=a3, i1_reg=a4)
  fw.mv(a0, s0)
  fw.mv(a1, t4)
  fw.mv(a2, s11)
  fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)
  emit_output_write_stateful(fw, t5, a0, a2)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB133, block_reg=s10, i0_reg=a3, i1_reg=a4)
  fw.li(t6, TILE_BYTES)
  fw.add(t5, t5, t6)
  fw.add(t4, t4, s2)
  fw.addi(a4, a4, -1)
  fw.j(w_loop)
  fw.label(w_done)

  fw.add(a7, a7, s3)
  fw.addi(a3, a3, -1)
  fw.j(h_loop)
  fw.label(h_done)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB135, block_reg=s10, i0_reg=s9, i1_reg=a6)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[10][1], PROFILE_TMP_NCRISC_PHASE)

  emit_profile_accum_start(fw, PROFILE_TMP_NCRISC_PHASE)
  fw.noc_write_barrier(OUTPUT_NOC, s8)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB140, block_reg=s10, i0_reg=s9, i1_reg=a6)
  fw.cb_pop_front(NM.CB_INTERFACE, 16, plan.out_subblock_num_tiles)
  emit_cb_debug_snapshot(fw, DEBUG_NCRISC_OUTPUT + 0x40, 16, 0xB151)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB150, block_reg=s10, i0_reg=s9, i1_reg=a6)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[11][1], PROFILE_TMP_NCRISC_PHASE)
  fw.add(a6, a6, s4)
  fw.addi(s9, s9, -1)
  fw.j(sbw_loop)
  fw.label(sbw_done)

  fw.add(s1, s1, s5)
  fw.addi(s10, s10, -1)
  fw.j(sbh_loop)
  fw.label(sbh_done)
  emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB1FF, block_reg=s10, i0_reg=s9, i1_reg=s1)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[2][1], PROFILE_TMP_NCRISC)
  emit_profile_stamp(fw, PROFILE_NCRISC_OUTPUT + 8)
  return fw


def emit_trisc0_unpack_row(
  fw: MatmulTrisc,
  in0_tile_index: int,
  in1_tile_index: int,
  *,
  mop_loop_count: int = 1,
  explicit_load=MATMUL_UNPACK_SRCB_LOAD,
) -> MatmulTrisc:
    emit_profile_accum_start(fw, PROFILE_TMP_TRISC0)
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
    emit_profile_accum_end(fw, PROFILE_COUNTERS[4][1], PROFILE_TMP_TRISC0)

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
    fw.emit(explicit_load)
    ctx1 = fw._new_label("trisc0_mop_ctx1")
    ctx_done = fw._new_label("trisc0_mop_done")
    fw.bne(t2, zero, ctx1)
    fw.emit(TTMOP(0, mop_loop_count, 0))
    fw.j(ctx_done)
    fw.label(ctx1)
    fw.emit(TTMOP(0, mop_loop_count, 0xFF))
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


def emit_trisc0_unpack_row_reg(
  fw: MatmulTrisc,
  in0_tile_index,
  in1_tile_index,
  *,
  mop_loop_count: int = 1,
  explicit_load=MATMUL_UNPACK_SRCB_LOAD,
) -> MatmulTrisc:
    emit_profile_accum_start(fw, PROFILE_TMP_TRISC0)
    wait_unp = fw._new_label("wait_unpack_ctx")
    wait_unp_done = fw._new_label("wait_unpack_ctx_done")
    fw.label(wait_unp)
    fw.lw(t1, s7, 0)
    fw.andi(t1, t1, 0xFE)
    fw.beq(t1, zero, wait_unp_done)
    fw.fence()
    fw.j(wait_unp)
    fw.label(wait_unp_done)
    emit_profile_accum_end(fw, PROFILE_COUNTERS[4][1], PROFILE_TMP_TRISC0)

    fw.mul(a0, in0_tile_index, a4)
    fw.add(a0, a0, s0)
    fw.addi(a0, a0, -1)

    fw.mul(a1, in1_tile_index, a5)
    fw.add(a1, a1, s1)
    fw.addi(a1, a1, -1)

    fw.lw(t2, s11, 0)
    fw.mv(t3, a2)
    sec0_ctx_ready = fw._new_label("trisc0_sec0_ctx")
    fw.beq(t2, zero, sec0_ctx_ready)
    fw.addi(t3, t3, 4)
    fw.label(sec0_ctx_ready)
    fw.sw(a1, t3, 0)

    fw.mv(t3, a3)
    sec1_ctx_ready = fw._new_label("trisc0_sec1_ctx")
    fw.beq(t2, zero, sec1_ctx_ready)
    fw.addi(t3, t3, 4)
    fw.label(sec1_ctx_ready)
    fw.sw(a0, t3, 0)
    fw.sw(zero, s7, 0)

    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
    fw.emit(explicit_load)
    ctx1 = fw._new_label("trisc0_mop_ctx1")
    ctx_done = fw._new_label("trisc0_mop_done")
    fw.bne(t2, zero, ctx1)
    fw.emit(TTMOP(0, mop_loop_count, 0))
    fw.j(ctx_done)
    fw.label(ctx1)
    fw.emit(TTMOP(0, mop_loop_count, 0xFF))
    fw.label(ctx_done)
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
    fw.li(t3, 1)
    fw.sub(t3, t3, t2)
    fw.sw(t3, s11, 0)
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
  if _plan_reuses_a(plan):
    mop_loop_count = plan.out_subblock_w - 1
    for inner in range(plan.in0_block_w):
      in1_tile_index = in1_offset + inner * plan.in1_per_core_w
      for row in range(plan.out_subblock_h):
        in0_tile_index = in0_offset + row * plan.in0_block_w + inner
        emit_trisc0_unpack_row(fw, in0_tile_index, in1_tile_index, mop_loop_count=mop_loop_count)
  else:
    mop_loop_count = plan.out_subblock_h - 1
    for inner in range(plan.in0_block_w):
      in0_tile_index = in0_offset + inner
      for col in range(plan.out_subblock_w):
        in1_tile_index = in1_offset + inner * plan.in1_per_core_w + col
        emit_trisc0_unpack_row(
          fw, in0_tile_index, in1_tile_index,
          mop_loop_count=mop_loop_count, explicit_load=MATMUL_UNPACK_SRCA_LOAD,
        )
  return fw


def emit_trisc0_unpack_subblock_reg(
  fw: MatmulTrisc, plan: MatmulPlan, in0_offset, in1_offset,
  *, in0_block_base_tiles: int = 0, in1_block_base_tiles: int = 0,
) -> MatmulTrisc:
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  fw.cb_read_ptr(fw.data["cb_interface"], 0, out=s0)
  fw.cb_iface(fw.data["cb_interface"], 0, out=t6)
  fw.lw(a4, t6, 8)
  fw.cb_read_ptr(fw.data["cb_interface"], 1, out=s1)
  fw.cb_iface(fw.data["cb_interface"], 1, out=t6)
  fw.lw(a5, t6, 8)
  fw.li(s7, TensixRegs.PC_UNPACK_SYNC)
  fw.li(s11, TLM.TRISC0_UNPACK_CFG_CONTEXT)
  fw.li(a2, TensixRegs.CFG_BASE + THCON_SEC0_REG3_BASE_ADDR32 * 4)
  fw.li(a3, TensixRegs.CFG_BASE + THCON_SEC1_REG3_BASE_ADDR32 * 4)
  if _plan_reuses_a(plan):
    mop_loop_count = plan.out_subblock_w - 1
    for inner in range(plan.in0_block_w):
      _move_plus_imm(fw, s10, in1_offset, in1_block_base_tiles + inner * plan.in1_per_core_w)
      for row in range(plan.out_subblock_h):
        _move_plus_imm(fw, s9, in0_offset, in0_block_base_tiles + row * plan.in0_block_w + inner)
        emit_trisc0_unpack_row_reg(fw, s9, s10, mop_loop_count=mop_loop_count)
  else:
    mop_loop_count = plan.out_subblock_h - 1
    for inner in range(plan.in0_block_w):
      _move_plus_imm(fw, s9, in0_offset, in0_block_base_tiles + inner)
      for col in range(plan.out_subblock_w):
        _move_plus_imm(fw, s10, in1_offset, in1_block_base_tiles + inner * plan.in1_per_core_w + col)
        emit_trisc0_unpack_row_reg(
          fw, s9, s10,
          mop_loop_count=mop_loop_count, explicit_load=MATMUL_UNPACK_SRCA_LOAD,
        )
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


def _math_mop_cfg(plan: MatmulPlan) -> MopCfg:
  if EXPERIMENTAL_THROTTLE0:
    return MATMUL_MATH_MOP_CFG_THROTTLE0 if _plan_reuses_a(plan) else MATMUL_MATH_MOP_CFG_THROTTLE0_REUSE_B
  return MATMUL_MATH_MOP_CFG


def _math_replay_load(plan: MatmulPlan) -> list:
  if EXPERIMENTAL_THROTTLE0 and _plan_reuses_a(plan):
    return MATMUL_MATH_REPLAY_LOAD_THROTTLE0
  return MATMUL_MATH_REPLAY_LOAD


def matmul_math_init(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  fw.math._local_state(fw, Dtype.Float16_b)
  replay_load = _math_replay_load(plan)
  mop_cfg = _math_mop_cfg(plan)
  if MATH_BACKEND == "direct":
    replay_load = MATMUL_MATH_REPLAY_LOAD_THROTTLE0
  matmul_math_addrmod_init(fw)
  fw.emit(TTREPLAY(16, len(replay_load), 0, 1))
  for word in replay_load:
    fw.emit(word)
  if MATH_BACKEND != "direct":
    fw.write_mop_cfg(MATMUL_MATH_RELOAD_MOP_CFG, 1)
  fw.tensix_sync(1)
  fw.wait_mmio_low_byte_zero(TensixRegs.pc_buf_sem(TensixSem.MATH_PACK))
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.MATH_PACK), init_value=0, max_value=2))
  matmul_math_addrmod_init(fw)
  fw.emit(TTREPLAY(16, len(replay_load), 0, 1))
  for word in replay_load:
    fw.emit(word)
  if MATH_BACKEND != "direct":
    fw.write_mop_cfg(mop_cfg, 1)
  if EXPERIMENTAL_THROTTLE0 and MATH_BACKEND != "direct":
    fw.write32(MATH_THROTTLED_MOP_STATUS, 0)
  return fw


def emit_math_program_mop(fw: MatmulTrisc, mop_cfg: MopCfg, replay_load: list) -> MatmulTrisc:
  matmul_math_addrmod_init(fw)
  fw.emit(TTREPLAY(16, len(replay_load), 0, 1))
  for word in replay_load:
    fw.emit(word)
  fw.write_mop_cfg(mop_cfg, 1)
  return fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))


def emit_math_dynamic_throttle_update(fw: MatmulTrisc) -> MatmulTrisc:
  want_throttle = fw._new_label("math_want_throttle")
  done = fw._new_label("math_throttle_done")
  already_zero = fw._new_label("math_throttle_already_zero")
  already_one = fw._new_label("math_throttle_already_one")

  fw.read32(t4, MEM_L1_ARC_FW_SCRATCH)
  fw.andi(t4, t4, 1)
  fw.read32(t5, MATH_THROTTLED_MOP_STATUS)
  fw.bne(t4, zero, want_throttle)

  fw.beq(t5, zero, already_zero)
  emit_math_program_mop(fw, MATMUL_MATH_MOP_CFG_THROTTLE0, MATMUL_MATH_REPLAY_LOAD_THROTTLE0)
  fw.write32(MATH_THROTTLED_MOP_STATUS, 0)
  fw.label(already_zero)
  fw.j(done)

  fw.label(want_throttle)
  fw.li(t6, 1)
  fw.beq(t5, t6, already_one)
  emit_math_program_mop(fw, MATMUL_MATH_MOP_CFG, MATMUL_MATH_REPLAY_LOAD)
  fw.write32(MATH_THROTTLED_MOP_STATUS, 1)
  fw.label(already_one)

  fw.label(done)
  return fw


def matmul_math_addrmod_init(fw: MatmulTrisc) -> MatmulTrisc:
  # Full 32x32 bf16 matmul, HiFi2.
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
  fw.li(t2, TTSETC16(ThreadCfg.DEST_TARGET_REG_CFG_MATH_Offset, 0).raw_word())  # base; addr bits added in
  fw.add(t1, t1, t2)
  return fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)


def emit_math_dst_base_addr(fw: MatmulTrisc, out_reg=t1) -> MatmulTrisc:
  fw.read32(out_reg, fw.data["dest_offset_id"])
  fw.slli(out_reg, out_reg, 9)
  fw.li(t2, TTSETC16(ThreadCfg.DEST_TARGET_REG_CFG_MATH_Offset, 0).raw_word())  # base; addr bits added in
  fw.add(out_reg, out_reg, t2)
  return fw


def emit_math_reload_subblock(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  fw.math_direct_mova2d_init()
  fw.write_mop_cfg(MATMUL_MATH_RELOAD_MOP_CFG, 1)
  emit_math_dst_base_addr(fw, t1)
  for tile_index in range(plan.out_subblock_num_tiles):
    if tile_index:
      fw.addi(t1, t1, 64)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  fw.tensix_sync(1)
  matmul_math_addrmod_init(fw)
  if MATH_BACKEND != "direct":
    fw.write_mop_cfg(_math_mop_cfg(plan), 1)
  return fw


def emit_math_direct_tile(fw: MatmulTrisc) -> MatmulTrisc:
  # Direct full-tile matmul: replay the 16-MVMUL body once per fidelity phase.
  fw.emit(TTREPLAY(16, len(MATMUL_MATH_REPLAY_LOAD_THROTTLE0)))
  if MATH_FIDELITY == "hifi2":
    fw.emit(TTREPLAY(16, len(MATMUL_MATH_REPLAY_LOAD_THROTTLE0)))
  return fw


def emit_math_subblock_body(fw: MatmulTrisc, plan: MatmulPlan, in0_offset: int, in1_offset: int) -> MatmulTrisc:
  emit_math_dst_base_addr(fw, t3)
  reuse_a = _plan_reuses_a(plan)
  if reuse_a:
    tile_order = list(range(plan.out_subblock_num_tiles))
  else:
    tile_order = [
      row * plan.out_subblock_w + col
      for col in range(plan.out_subblock_w)
      for row in range(plan.out_subblock_h)
    ]
  for inner in range(plan.in0_block_w):
    _ = in0_offset + inner
    _ = in1_offset + inner * plan.in1_per_core_w
    for order_index, tile_index in enumerate(tile_order):
      fw.mv(t1, t3)
      if tile_index:
        fw.addi(t1, t1, tile_index * 64)
      fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
      if MATH_BACKEND == "direct":
        emit_math_direct_tile(fw)
        if reuse_a:
          fw.emit(TTSETRWC(1, 0, 0, 0, 0, 15))
      elif EXPERIMENTAL_THROTTLE0:
        fw.emit(TTMOP(1, 0, 0))
      else:
        fw.emit(TTMOP(1, 0, 0))
        fw.emit(TTMOP(1, 0, 0))
        if reuse_a:
          fw.emit(TTSETRWC(1, 0, 0, 0, 0, 15))
      if reuse_a and tile_index % plan.out_subblock_w == plan.out_subblock_w - 1:
        fw.emit(TTSETRWC(2, 0, 0, 0, 0, 15))
      elif not reuse_a:
        end_col = order_index % plan.out_subblock_h == plan.out_subblock_h - 1
        if EXPERIMENTAL_THROTTLE0 and MATH_BACKEND != "direct":
          fw.emit(TTSETRWC(2, 0, 0, 0, 0, 15))
          if end_col:
            fw.emit(TTSETRWC(1, 0, 0, 0, 0, 15))
        else:
          fw.emit(TTSETRWC(3 if end_col else 2, 0, 0, 0, 0, 15))
  return fw


def emit_math_subblock_commit(fw: MatmulTrisc) -> MatmulTrisc:
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC1)
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_PACK)))
  fw.tensix_sync(1)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[6][1], PROFILE_TMP_TRISC1)
  fw.read32(t1, fw.data["dest_offset_id"])
  fw.li(t2, 1)
  fw.sub(t2, t2, t1)
  fw.write32(fw.data["dest_offset_id"], t2)
  return fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.MATH | TensixWait.SFPU))


def emit_math_group_inner_sync(fw: MatmulTrisc) -> MatmulTrisc:
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  return fw.tensix_sync(1)


def emit_math_subblock(fw: MatmulTrisc, plan: MatmulPlan, in0_offset: int, in1_offset: int) -> MatmulTrisc:
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_ROOM,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  emit_math_subblock_body(fw, plan, in0_offset, in1_offset)
  return emit_math_subblock_commit(fw)


def emit_pack_tile_to_cb(fw: MatmulTrisc, plan: MatmulPlan, out_cb: int) -> MatmulTrisc:
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC2)
  fw.cb_reserve_back(fw.data["cb_interface"], out_cb, plan.out_subblock_num_tiles)
  fw.cb_write_ptr(fw.data["cb_interface"], out_cb, out=s0)
  fw.mv(s3, s0)
  fw.cb_iface(fw.data["cb_interface"], out_cb, out=t6)
  fw.lw(s4, t6, 8)
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
  fw.mv(s0, s3)
  fw.addi(s0, s0, -1)
  for tile_index in range(plan.out_subblock_num_tiles):
    if tile_index:
      fw.add(s0, s0, s4)
    fw.emit(TTSETADC(4, 0, 3, tile_index))
    fw.slli(t1, s0, 8)
    fw.li(t2, 0x00FFFF00)
    fw.and_(t1, t1, t2)
    fw.li(t2, TTSETDMAREG(0, 0, 0, 24).raw_word())  # SETDMAREG[24] base; low addr bits added in
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.srli(t1, s0, 16)
    fw.slli(t1, t1, 8)
    fw.li(t2, 0x00800000)
    fw.or_(t1, t1, t2)
    fw.li(t2, TTSETDMAREG(0, 0, 0, 25).raw_word())  # SETDMAREG[25] base; high addr bits added in
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTSTALLWAIT(TensixStall.CFG, WAIT_THCON_AND_PACK))
    fw.emit(TTWRCFG(12, 0, Cfg.THCON_SEC0_REG1_L1_Dest_addr.addr32))
    fw.srli(t1, s0, 16)
    fw.slli(t1, t1, 8)
    fw.li(t2, TTSETDMAREG(0, 0, 0, 25).raw_word())  # SETDMAREG[25] base; high addr bits added in
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTDMANOP())

    fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))
    fw.emit(TTMOP(1, 0, 0))
    fw.tensix_sync(2, tmp=t1)
    fw.emit(TTSETADCZW(4, 0, 0, 0, 0, 5))
  fw.cb_push_back(fw.data["cb_interface"], out_cb, plan.out_subblock_num_tiles, tensix_received=True)
  fw.emit(TTSTALLWAIT(TensixStall.THCON, TensixWait.PACK0))
  fw.read32(t1, fw.data["dest_offset_id"])
  fw.andi(t2, t1, 1)
  fw.li(t3, TTZEROACC(2, 0, 0, 1).raw_word())  # ZEROACC base; dest-offset parity bit added in
  fw.add(t2, t2, t3)
  fw.write32(TensixRegs.INSTRN_BUF_BASE, t2)
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.MATH_PACK)))
  fw.li(t2, 1)
  fw.sub(t2, t2, t1)
  fw.write32(fw.data["dest_offset_id"], t2)
  fw.emit(TTDMANOP())
  fw.emit(TTDMANOP())
  emit_profile_accum_end(fw, PROFILE_COUNTERS[8][1], PROFILE_TMP_TRISC2)
  return fw


def emit_pack_reconfig_l1_acc(fw: MatmulTrisc, enabled: bool) -> MatmulTrisc:
  disable_zero_flags = 0x04 if enabled else 0x00
  pack_l1_acc = 0x08 if enabled else 0x00
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.PACK0))
  regs = [
    (Cfg.THCON_SEC0_REG1_1, Cfg.THCON_SEC0_REG1_2),
    (Cfg.THCON_SEC0_REG8_1, Cfg.THCON_SEC0_REG8_2),
    (Cfg.THCON_SEC1_REG1_1, Cfg.THCON_SEC1_REG1_2),
    (Cfg.THCON_SEC1_REG8_1, Cfg.THCON_SEC1_REG8_2),
  ]
  for flags_reg, acc_reg in regs:
    fw.push_tensix(TTRMWCIB0(Mask=0x04, Data=disable_zero_flags, CfgRegAddr=flags_reg.addr32))
    fw.push_tensix(TTRMWCIB2(Mask=0x08, Data=pack_l1_acc, CfgRegAddr=acc_reg.addr32))
  return fw


def emit_pack_reconfig_l1_acc_for_partial_block(fw: MatmulTrisc, block_reg) -> MatmulTrisc:
  not_block0 = fw._new_label("pack_l1_acc_not_block0")
  done = fw._new_label("pack_l1_acc_done")
  fw.bne(block_reg, zero, not_block0)
  emit_pack_reconfig_l1_acc(fw, False)
  fw.j(done)
  fw.label(not_block0)
  fw.li(t0, 1)
  fw.bne(block_reg, t0, done)
  emit_pack_reconfig_l1_acc(fw, True)
  fw.label(done)
  return fw


def matmul_trisc0(plan: MatmulPlan) -> MatmulTrisc:
  fw = MatmulTrisc(0)
  fw.prologue()
  fw.unpack.init(dtype=INPUT_DTYPE, tile_bytes=INPUT_TILE_BYTES, mop_cfg=MATMUL_UNPACK_AB_MOP_CFG)
  fw.emit(TTSETADCXX(1, 1023, 0))
  fw.emit(TTSETADCXX(2, 1023, 0))
  _emit_trisc0_unpack_replay_init(fw, plan)
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.UNPACK_SYNC), init_value=0, max_value=2))
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC0)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE000)
  fw.li(s6, 0)
  fw.li(s8, plan.num_blocks)
  block_loop = fw._new_label("trisc0_block_loop")
  block_done = fw._new_label("trisc0_block_done")
  fw.label(block_loop)
  _jump_if_equal(fw, s6, s8, block_done, "trisc0_block_body")
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE100)
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC0)
  fw.cb_wait_front(fw.data["cb_interface"], 0, plan.in0_block_num_tiles)
  fw.cb_wait_front(fw.data["cb_interface"], 1, plan.in1_block_num_tiles)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE110)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[3][1], PROFILE_TMP_TRISC0)

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
  if SKIP_PADDED_N:
    _emit_trisc_valid_in1(fw, t0)
    _jump_if_ge(fw, s5, t0, i1_done, "trisc0_i1_body")
  else:
    fw.li(t0, plan.in1_num_subblocks)
    _jump_if_ge(fw, s5, t0, i1_done, "trisc0_i1_body")
  fw.li(t0, plan.in0_subblock_num_tiles)
  fw.mul(s2, s4, t0)
  fw.li(t0, plan.out_subblock_w)
  fw.mul(s3, s5, t0)
  if plan.num_blocks > 1:
    not_reload = fw._new_label("trisc0_not_reload")
    fw.li(t0, plan.num_blocks - 1)
    fw.bne(s6, t0, not_reload)
    emit_progress_mark(fw, DEBUG_TRISC0, 0xE130)
    emit_trisc0_reload_subblock(fw, plan)
    emit_progress_mark(fw, DEBUG_TRISC0, 0xE131)
    fw.label(not_reload)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE140)
  emit_trisc0_unpack_subblock_reg(fw, plan, s2, s3)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE141)
  fw.addi(s5, s5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(s4, s4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)
  if plan.num_blocks > 2:
    skip_partial_pop = fw._new_label("trisc0_skip_partial_pop")
    fw.li(t0, plan.num_blocks - 2)
    fw.bge(s6, t0, skip_partial_pop)
    if SKIP_PADDED_N:
      fw.cb_wait_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
      fw.cb_pop_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
    else:
      fw.cb_wait_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
      fw.cb_pop_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
    fw.label(skip_partial_pop)
  fw.cb_pop_front(fw.data["cb_interface"], 0, plan.in0_block_num_tiles, tensix_ack=True)
  fw.cb_pop_front(fw.data["cb_interface"], 1, plan.in1_block_num_tiles, tensix_ack=True)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE1FF)
  fw.addi(s6, s6, 1)
  fw.j(block_loop)
  fw.label(block_done)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE2FF)
  emit_profile_stamp(fw, PROFILE_TRISC0 + 8)
  return fw.ret_kernel()


def matmul_trisc1(plan: MatmulPlan) -> MatmulTrisc:
  fw = MatmulTrisc(1)
  fw.prologue()
  matmul_math_init(fw, plan)
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC1)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF000)
  fw.li(s6, 0)
  fw.li(s8, plan.num_blocks)
  block_loop = fw._new_label("trisc1_block_loop")
  block_done = fw._new_label("trisc1_block_done")
  fw.label(block_loop)
  _jump_if_equal(fw, s6, s8, block_done, "trisc1_block_body")
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF100)
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
  if SKIP_PADDED_N:
    _emit_trisc_valid_in1(fw, t0)
    _jump_if_ge(fw, s5, t0, i1_done, "trisc1_i1_body")
  else:
    fw.li(t0, plan.in1_num_subblocks)
    _jump_if_ge(fw, s5, t0, i1_done, "trisc1_i1_body")
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC1)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF110)
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_ROOM,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF111)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[5][1], PROFILE_TMP_TRISC1)
  if plan.num_blocks > 1:
    not_reload = fw._new_label("trisc1_not_reload")
    fw.li(t0, plan.num_blocks - 1)
    fw.bne(s6, t0, not_reload)
    emit_progress_mark(fw, DEBUG_TRISC1, 0xF130)
    emit_math_reload_subblock(fw, plan)
    emit_progress_mark(fw, DEBUG_TRISC1, 0xF131)
    fw.label(not_reload)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF140)
  emit_math_subblock_body(fw, plan, 0, 0)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF141)
  emit_math_subblock_commit(fw)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF150)
  fw.addi(s5, s5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(s4, s4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF1FF)
  fw.addi(s6, s6, 1)
  fw.j(block_loop)
  fw.label(block_done)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF2FF)
  emit_profile_stamp(fw, PROFILE_TRISC1 + 8)
  return fw.ret_kernel()


def matmul_trisc2(plan: MatmulPlan) -> MatmulTrisc:
  fw = MatmulTrisc(2)
  fw.prologue()
  fw.pack.init(dtype=Dtype.Float16_b, out_cb=16, mop_cfg=MATMUL_PACK_MOP_CFG)
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC2)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD000)
  num_subblocks = plan.in0_num_subblocks * plan.in1_num_subblocks
  if plan.num_blocks > 1:
    fw.li(s6, 0)
    partial_block_loop = fw._new_label("trisc2_partial_block_loop")
    partial_block_done = fw._new_label("trisc2_partial_block_done")
    fw.label(partial_block_loop)
    fw.li(t0, plan.num_blocks - 1)
    _jump_if_ge(fw, s6, t0, partial_block_done, "trisc2_partial_block_body")
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD100, block_reg=s6, i0_reg=s5, i1_reg=s5)
    emit_pack_reconfig_l1_acc_for_partial_block(fw, s6)
    fw.li(s5, 0)
    partial_sb_loop = fw._new_label("trisc2_partial_sb_loop")
    partial_sb_done = fw._new_label("trisc2_partial_sb_done")
    fw.label(partial_sb_loop)
    if SKIP_PADDED_N:
      _emit_trisc_valid_subblocks(fw, plan, t0)
      _jump_if_ge(fw, s5, t0, partial_sb_done, "trisc2_partial_sb_body")
    else:
      fw.li(t0, num_subblocks)
      _jump_if_ge(fw, s5, t0, partial_sb_done, "trisc2_partial_sb_body")
    emit_profile_accum_start(fw, PROFILE_TMP_TRISC2)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD120, block_reg=s6, i0_reg=s5, i1_reg=s5)
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_DATA,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_ZERO,
    ))
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD121, block_reg=s6, i0_reg=s5, i1_reg=s5)
    emit_profile_accum_end(fw, PROFILE_COUNTERS[7][1], PROFILE_TMP_TRISC2)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD130, block_reg=s6, i0_reg=s5, i1_reg=s5)
    emit_pack_tile_to_cb(fw, plan, 24)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD131, block_reg=s6, i0_reg=s5, i1_reg=s5)
    fw.addi(s5, s5, 1)
    fw.j(partial_sb_loop)
    fw.label(partial_sb_done)
    if SKIP_PADDED_N:
      _emit_trisc2_pad_cb24_to_full_block(fw, plan)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD1FF, block_reg=s6, i0_reg=s5, i1_reg=s5)
    fw.addi(s6, s6, 1)
    fw.j(partial_block_loop)
    fw.label(partial_block_done)

  fw.li(s5, 0)
  final_sb_loop = fw._new_label("trisc2_final_sb_loop")
  final_sb_done = fw._new_label("trisc2_final_sb_done")
  fw.label(final_sb_loop)
  if SKIP_PADDED_N:
    _emit_trisc_valid_subblocks(fw, plan, t0)
    _jump_if_ge(fw, s5, t0, final_sb_done, "trisc2_final_sb_body")
  else:
    fw.li(t0, num_subblocks)
    _jump_if_ge(fw, s5, t0, final_sb_done, "trisc2_final_sb_body")
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC2)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD220, block_reg=s6, i0_reg=s5, i1_reg=s5)
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_DATA,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_ZERO,
  ))
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD221, block_reg=s6, i0_reg=s5, i1_reg=s5)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[7][1], PROFILE_TMP_TRISC2)
  emit_pack_reconfig_l1_acc(fw, False)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD230, block_reg=s6, i0_reg=s5, i1_reg=s5)
  emit_pack_tile_to_cb(fw, plan, 16)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD231, block_reg=s6, i0_reg=s5, i1_reg=s5)
  fw.addi(s5, s5, 1)
  fw.j(final_sb_loop)
  fw.label(final_sb_done)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD2FF, block_reg=s6, i0_reg=s5, i1_reg=s5)
  emit_profile_stamp(fw, PROFILE_TRISC2 + 8)
  return fw.ret_kernel()


def _grouped_k_counts(plan: MatmulPlan) -> tuple[int, int]:
  if K_GROUP == 1:
    return 0, 0
  partial_blocks = plan.num_blocks - 1
  if partial_blocks <= 0:
    raise ValueError("grouped-K needs at least two K blocks")
  return partial_blocks // K_GROUP, partial_blocks % K_GROUP


def _check_grouped_k_plan(plan: MatmulPlan) -> int:
  partial_groups, partial_remainder = _grouped_k_counts(plan)
  if partial_remainder:
    raise ValueError(
      f"K_GROUP={K_GROUP} requires (num_blocks - 1) divisible by the group size, got {plan.num_blocks}"
    )
  return partial_groups


def matmul_trisc0_grouped_k(plan: MatmulPlan) -> MatmulTrisc:
  partial_groups, partial_remainder = _grouped_k_counts(plan)
  if partial_remainder:
    raise ValueError(
      f"K_GROUP={K_GROUP} requires (num_blocks - 1) divisible by the group size, got {plan.num_blocks}"
    )
  fw = MatmulTrisc(0)
  fw.prologue()
  fw.unpack.init(dtype=INPUT_DTYPE, tile_bytes=INPUT_TILE_BYTES, mop_cfg=MATMUL_UNPACK_AB_MOP_CFG)
  fw.emit(TTSETADCXX(1, 1023, 0))
  fw.emit(TTSETADCXX(2, 1023, 0))
  _emit_trisc0_unpack_replay_init(fw, plan)
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.UNPACK_SYNC), init_value=0, max_value=2))
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC0)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE000)

  fw.li(s6, 0)
  group_loop = fw._new_label("trisc0_group_loop")
  group_done = fw._new_label("trisc0_group_done")
  fw.label(group_loop)
  fw.li(t0, partial_groups)
  _jump_if_ge(fw, s6, t0, group_done, "trisc0_group_body")
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE100)
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC0)
  fw.cb_wait_front(fw.data["cb_interface"], 0, K_GROUP * plan.in0_block_num_tiles)
  fw.cb_wait_front(fw.data["cb_interface"], 1, K_GROUP * plan.in1_block_num_tiles)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[3][1], PROFILE_TMP_TRISC0)

  fw.li(s4, 0)
  i0_loop = fw._new_label("trisc0_group_i0_loop")
  i0_done = fw._new_label("trisc0_group_i0_done")
  fw.label(i0_loop)
  fw.li(t0, plan.in0_num_subblocks)
  _jump_if_ge(fw, s4, t0, i0_done, "trisc0_group_i0_body")
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE110)
  fw.li(s5, 0)
  i1_loop = fw._new_label("trisc0_group_i1_loop")
  i1_done = fw._new_label("trisc0_group_i1_done")
  fw.label(i1_loop)
  fw.li(t0, plan.in1_num_subblocks)
  _jump_if_ge(fw, s5, t0, i1_done, "trisc0_group_i1_body")
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE120)
  fw.li(t0, plan.in0_subblock_num_tiles)
  fw.mul(s2, s4, t0)
  fw.li(t0, plan.out_subblock_w)
  fw.mul(s3, s5, t0)
  if STREAM_PARTIAL_CB24:
    skip_reload = fw._new_label("trisc0_group_skip_stream_reload")
    fw.beq(s6, zero, skip_reload)
    emit_trisc0_reload_subblock(fw, plan)
    fw.label(skip_reload)
  for kg in range(K_GROUP):
    if INPUT_BUFFER_FACTOR == 3 and K_GROUP == 2 and kg == 1:
      wrapped = fw._new_label("trisc0_group_wrapped_input")
      done_wrap = fw._new_label("trisc0_group_wrapped_input_done")
      fw.li(t0, 3)
      fw.remu(t1, s6, t0)
      fw.li(t0, 1)
      fw.beq(t1, t0, wrapped)
      emit_trisc0_unpack_subblock_reg(
        fw, plan, s2, s3,
        in0_block_base_tiles=plan.in0_block_num_tiles,
        in1_block_base_tiles=plan.in1_block_num_tiles,
      )
      fw.j(done_wrap)
      fw.label(wrapped)
      emit_trisc0_unpack_subblock_reg(
        fw, plan, s2, s3,
        in0_block_base_tiles=-2 * plan.in0_block_num_tiles,
        in1_block_base_tiles=-2 * plan.in1_block_num_tiles,
      )
      fw.label(done_wrap)
    else:
      emit_trisc0_unpack_subblock_reg(
        fw, plan, s2, s3,
        in0_block_base_tiles=kg * plan.in0_block_num_tiles,
        in1_block_base_tiles=kg * plan.in1_block_num_tiles,
      )
  fw.addi(s5, s5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(s4, s4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)
  if partial_groups > 1 and not STREAM_PARTIAL_CB24:
    skip_partial_pop = fw._new_label("trisc0_group_skip_partial_pop")
    fw.li(t0, partial_groups - 1)
    fw.bge(s6, t0, skip_partial_pop)
    fw.cb_wait_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
    fw.cb_pop_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
    fw.label(skip_partial_pop)
  fw.cb_pop_front(fw.data["cb_interface"], 0, K_GROUP * plan.in0_block_num_tiles, tensix_ack=True)
  fw.cb_pop_front(fw.data["cb_interface"], 1, K_GROUP * plan.in1_block_num_tiles, tensix_ack=True)
  fw.addi(s6, s6, 1)
  fw.j(group_loop)
  fw.label(group_done)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE200)

  emit_profile_accum_start(fw, PROFILE_TMP_TRISC0)
  fw.cb_wait_front(fw.data["cb_interface"], 0, plan.in0_block_num_tiles)
  fw.cb_wait_front(fw.data["cb_interface"], 1, plan.in1_block_num_tiles)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[3][1], PROFILE_TMP_TRISC0)
  fw.li(s4, 0)
  final_i0_loop = fw._new_label("trisc0_final_i0_loop")
  final_i0_done = fw._new_label("trisc0_final_i0_done")
  fw.label(final_i0_loop)
  fw.li(t0, plan.in0_num_subblocks)
  _jump_if_ge(fw, s4, t0, final_i0_done, "trisc0_final_i0_body")
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE210)
  fw.li(s5, 0)
  final_i1_loop = fw._new_label("trisc0_final_i1_loop")
  final_i1_done = fw._new_label("trisc0_final_i1_done")
  fw.label(final_i1_loop)
  fw.li(t0, plan.in1_num_subblocks)
  _jump_if_ge(fw, s5, t0, final_i1_done, "trisc0_final_i1_body")
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE220)
  fw.li(t0, plan.in0_subblock_num_tiles)
  fw.mul(s2, s4, t0)
  fw.li(t0, plan.out_subblock_w)
  fw.mul(s3, s5, t0)
  emit_trisc0_reload_subblock(fw, plan)
  emit_trisc0_unpack_subblock_reg(fw, plan, s2, s3)
  fw.addi(s5, s5, 1)
  fw.j(final_i1_loop)
  fw.label(final_i1_done)
  fw.addi(s4, s4, 1)
  fw.j(final_i0_loop)
  fw.label(final_i0_done)
  fw.cb_pop_front(fw.data["cb_interface"], 0, plan.in0_block_num_tiles, tensix_ack=True)
  fw.cb_pop_front(fw.data["cb_interface"], 1, plan.in1_block_num_tiles, tensix_ack=True)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE2FF)
  emit_profile_stamp(fw, PROFILE_TRISC0 + 8)
  return fw.ret_kernel()


def matmul_trisc1_grouped_k(plan: MatmulPlan) -> MatmulTrisc:
  partial_groups = _check_grouped_k_plan(plan)
  fw = MatmulTrisc(1)
  fw.prologue()
  matmul_math_init(fw, plan)
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC1)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF000)

  fw.li(s6, 0)
  group_loop = fw._new_label("trisc1_group_loop")
  group_done = fw._new_label("trisc1_group_done")
  fw.label(group_loop)
  fw.li(t0, partial_groups)
  _jump_if_ge(fw, s6, t0, group_done, "trisc1_group_body")
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF100)
  fw.li(s4, 0)
  i0_loop = fw._new_label("trisc1_group_i0_loop")
  i0_done = fw._new_label("trisc1_group_i0_done")
  fw.label(i0_loop)
  fw.li(t0, plan.in0_num_subblocks)
  _jump_if_ge(fw, s4, t0, i0_done, "trisc1_group_i0_body")
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF110)
  fw.li(s5, 0)
  i1_loop = fw._new_label("trisc1_group_i1_loop")
  i1_done = fw._new_label("trisc1_group_i1_done")
  fw.label(i1_loop)
  fw.li(t0, plan.in1_num_subblocks)
  _jump_if_ge(fw, s5, t0, i1_done, "trisc1_group_i1_body")
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF120)
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC1)
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_ROOM,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  emit_profile_accum_end(fw, PROFILE_COUNTERS[5][1], PROFILE_TMP_TRISC1)
  for kg in range(K_GROUP):
    emit_math_subblock_body(fw, plan, 0, 0)
    if kg != K_GROUP - 1:
      emit_math_group_inner_sync(fw)
  emit_math_subblock_commit(fw)
  fw.addi(s5, s5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(s4, s4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)
  fw.addi(s6, s6, 1)
  fw.j(group_loop)
  fw.label(group_done)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF200)

  fw.li(s4, 0)
  final_i0_loop = fw._new_label("trisc1_final_i0_loop")
  final_i0_done = fw._new_label("trisc1_final_i0_done")
  fw.label(final_i0_loop)
  fw.li(t0, plan.in0_num_subblocks)
  _jump_if_ge(fw, s4, t0, final_i0_done, "trisc1_final_i0_body")
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF210)
  fw.li(s5, 0)
  final_i1_loop = fw._new_label("trisc1_final_i1_loop")
  final_i1_done = fw._new_label("trisc1_final_i1_done")
  fw.label(final_i1_loop)
  fw.li(t0, plan.in1_num_subblocks)
  _jump_if_ge(fw, s5, t0, final_i1_done, "trisc1_final_i1_body")
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF220)
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC1)
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_ROOM,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  emit_profile_accum_end(fw, PROFILE_COUNTERS[5][1], PROFILE_TMP_TRISC1)
  emit_math_reload_subblock(fw, plan)
  emit_math_subblock_body(fw, plan, 0, 0)
  emit_math_subblock_commit(fw)
  fw.addi(s5, s5, 1)
  fw.j(final_i1_loop)
  fw.label(final_i1_done)
  fw.addi(s4, s4, 1)
  fw.j(final_i0_loop)
  fw.label(final_i0_done)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF2FF)
  emit_profile_stamp(fw, PROFILE_TRISC1 + 8)
  return fw.ret_kernel()


def matmul_trisc2_grouped_k(plan: MatmulPlan) -> MatmulTrisc:
  partial_groups = _check_grouped_k_plan(plan)
  fw = MatmulTrisc(2)
  fw.prologue()
  fw.pack.init(dtype=Dtype.Float16_b, out_cb=16, mop_cfg=MATMUL_PACK_MOP_CFG)
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC2)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD000)
  num_subblocks = plan.in0_num_subblocks * plan.in1_num_subblocks

  fw.li(s6, 0)
  partial_group_loop = fw._new_label("trisc2_partial_group_loop")
  partial_group_done = fw._new_label("trisc2_partial_group_done")
  fw.label(partial_group_loop)
  fw.li(t0, partial_groups)
  _jump_if_ge(fw, s6, t0, partial_group_done, "trisc2_partial_group_body")
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD100)
  emit_pack_reconfig_l1_acc_for_partial_block(fw, s6)
  fw.li(s5, 0)
  partial_sb_loop = fw._new_label("trisc2_group_partial_sb_loop")
  partial_sb_done = fw._new_label("trisc2_group_partial_sb_done")
  fw.label(partial_sb_loop)
  fw.li(t0, num_subblocks)
  _jump_if_ge(fw, s5, t0, partial_sb_done, "trisc2_group_partial_sb_body")
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD120)
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC2)
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_DATA,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_ZERO,
  ))
  emit_profile_accum_end(fw, PROFILE_COUNTERS[7][1], PROFILE_TMP_TRISC2)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD130)
  emit_pack_tile_to_cb(fw, plan, 24)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD140)
  fw.addi(s5, s5, 1)
  fw.j(partial_sb_loop)
  fw.label(partial_sb_done)
  fw.addi(s6, s6, 1)
  fw.j(partial_group_loop)
  fw.label(partial_group_done)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD200)

  fw.li(s5, 0)
  final_sb_loop = fw._new_label("trisc2_group_final_sb_loop")
  final_sb_done = fw._new_label("trisc2_group_final_sb_done")
  fw.label(final_sb_loop)
  fw.li(t0, num_subblocks)
  _jump_if_ge(fw, s5, t0, final_sb_done, "trisc2_group_final_sb_body")
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD220)
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC2)
  fw.emit(TTSEMWAIT(
    STALL_MATH_PACK_DATA,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_ZERO,
  ))
  emit_profile_accum_end(fw, PROFILE_COUNTERS[7][1], PROFILE_TMP_TRISC2)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD230)
  emit_pack_reconfig_l1_acc(fw, False)
  emit_pack_tile_to_cb(fw, plan, 16)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD240)
  fw.addi(s5, s5, 1)
  fw.j(final_sb_loop)
  fw.label(final_sb_done)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD2FF)
  emit_profile_stamp(fw, PROFILE_TRISC2 + 8)
  return fw.ret_kernel()


def build_program(
  plan: MatmulPlan, a_addr: int, b_addr: int, c_addr: int, num_banks: int,
  layout: TensorLayout | None = None,
) -> Program:
  brisc_sender = matmul_reader_sender(plan)
  brisc_recv = matmul_reader_recv()
  ncrisc_sender = matmul_writer_sender(plan)
  ncrisc_recv = matmul_writer_recv(plan)
  trisc0 = matmul_trisc0_grouped_k(plan) if K_GROUP > 1 else matmul_trisc0(plan)
  trisc1 = matmul_trisc1_grouped_k(plan) if K_GROUP > 1 else matmul_trisc1(plan)
  trisc2 = matmul_trisc2_grouped_k(plan) if K_GROUP > 1 else matmul_trisc2(plan)

  brisc_sender.rta(lambda x, y: reader_args(plan, a_addr, (x, y), num_banks, layout))
  brisc_recv.rta(lambda x, y: reader_args(plan, a_addr, (x, y), num_banks, layout))
  ncrisc_sender.rta(lambda x, y: writer_args(plan, b_addr, c_addr, (x, y), num_banks, layout))
  ncrisc_recv.rta(lambda x, y: writer_args(plan, b_addr, c_addr, (x, y), num_banks, layout))
  trisc0.rta(lambda x, y: trisc_args(plan, (x, y)) if SKIP_PADDED_N else [])
  trisc1.rta(lambda x, y: trisc_args(plan, (x, y)) if SKIP_PADDED_N else [])
  trisc2.rta(lambda x, y: trisc_args(plan, (x, y)) if SKIP_PADDED_N else [])

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

    split_m_first = (
      split_n == 0
      or SPLIT_AXIS == "m"
      or (SPLIT_AXIS == "auto" and split_m != 0 and m >= n)
    )
    if split_m_first:
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

    a_ref, b_ref = make_inputs(M, K, N)
    a_padded = np.zeros((Mp, Kp), dtype=np.float32)
    b_padded = np.zeros((Kp, Np), dtype=np.float32)
    a_padded[:M, :K] = a_ref
    b_padded[:K, :N] = b_ref

    a_buf = device.alloc_write(to_bf16_device_bytes(a_padded), dtype=Dtype.Float16_b, shape=(Mp, Kp), name="A")
    b_buf = device.alloc_write(to_bf16_device_bytes(b_padded), dtype=Dtype.Float16_b, shape=(Kp, Np), name="B")
    c_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b, shape=(Mp, Np), name="C")

    layout_base = dict(a_row_stride=Kp // TILE, b_row_stride=Np // TILE, c_row_stride=Np // TILE)
    run_times_us = []
    for _run in range(RUNS):
      run_timings = []
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
        run_timings.extend(device.run(prog))
      if run_timings:
        run_times_us.append(sum(timing["us"] for timing in run_timings))
    c_raw = device.dram_read(c_buf)
    validate(a_ref, b_ref, c_raw, M, N, Mp, Np)

    if not run_times_us:
      raise RuntimeError("matmul timing is unavailable without fast dispatch")
    avg_us = sum(run_times_us) / len(run_times_us)
    print("matmul_peak:")
    print(f"  runs: {len(run_times_us)}")
    print(f"  shape: {M}x{K}x{N}")
    print(f"  padded: {Mp}x{Kp}x{Np}")
    print(f"  kernel_avg: {avg_us:,.1f} us")
    print(f"  throughput: {tflops(Mp, Np, Kp, avg_us):.2f} TFLOP/s")
  finally:
    device.close()


if __name__ == "__main__":
  main()
