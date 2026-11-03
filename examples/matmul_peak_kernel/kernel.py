"""Blocked multicast matmul, with optional FP8 row-MOP and N-pass schedules."""
from __future__ import annotations
import os, sys, struct
from dataclasses import dataclass, replace
import numpy as np
from ttko.isa import R, Tensix as TT
from ttko.registers import Cfg, DType, Sem, SemWait, Stall, TensixL1, TensixMMIO, TensixRegs, ThreadCfg, TriscMailbox, Wait
from ttko.registers import BriscMailbox as BM, NcriscMailbox as NM, TriscLocalMem as TLM
from .asm import KernelBase, A_DONE
from firmware.consts import TensixL1 as LaunchL1
from ttko.noc import NocOps, NOC
from ttko.cb import CircularBufferOps, CB as CBRegs
from ttko.tensix import TensixOps
from ttko.mop import LoopTemplate
from .prepare import block as prepare_block
from . import epilogue
TILE = 32
CODE_BASE = 0x12000
CB_STORAGE_BASE = 0x1E000  # 48 KiB for the five resident controller images
CB_STORAGE_END = 0x17D000  # launch tables (asm.ARG_BASE), then diagnostics
TILE_BYTES = DType.F32.tile_size   # CB16 holds FP32 accumulator tiles
INPUT_DTYPE = DType.BF16
INPUT_TILE_BYTES = INPUT_DTYPE.tile_size
OUTPUT_DTYPE = DType.F32
# Accumulation is always FP32: four tiles per Dst half, partials kept by FP32
# L1 packing.
# MVMUL fidelity phases. FP8 is exact at 1; BF16 is exact at 4.
FIDELITY = 2
# The epilogue rounds the FP32 accumulators to BF16 and writes row-major rows.
RESULT_DTYPE = DType.BF16


MAX_IN0_BLOCK_W = 6
INPUT_BUFFER_FACTOR = int(os.environ.get("MATMUL_A_BUFFERS", "2"))


WRITER_WAVE_ROWS = 0


ENABLE_BREADCRUMBS = os.environ.get("BREADCRUMBS", "") == "1"

# Unrolled per-bank row reader. The builder falls back to the generic reader
# when the unrolled code does not fit the code region (or K-block width is odd).
FAST_READS = True
PACK_DEST_OFFSET_GPR = 44

OVERLAP_BLOCKS = int(os.environ.get("MATMUL_OVERLAP_BLOCKS", "0"))
N_PASSES = int(os.environ.get("MATMUL_N_PASSES", "1"))
# Which per-core output dimension the passes split. 'm' re-reads B (long DRAM
# row segments) instead of A (K-block-wide, short segments) on every pass.
PASS_AXIS = os.environ.get("MATMUL_PASS_AXIS", "n")
B_BUFFER_FACTOR = int(os.environ.get("MATMUL_B_BUFFERS", "2"))
# Per-controller pass indices and the NCRISC's saved input-reader registers.
PASS_BASE = 0x17DD00
ROW_MOP = os.environ.get("MATMUL_ROW_MOP", "0") == "1"

def use_row_mop():
  return ROW_MOP

# One unpack MOP per 1xW FP8 subblock: the unpackers' address counters walk
# K (B: channel-0 W, A: channel-0 Y), instead of a RISC round trip per K row.
def batched_unpack(plan):
  return INPUT_DTYPE == DType.FP8 and use_row_mop() and plan.out_subblock_h == 1

# Replay slots on TRISC0 for the batched FP8 unpack.
REPLAY_B_TILE, REPLAY_A_TILE, REPLAY_K_STEP = 0, 3, 6


SUPPORTED_IN0_BLOCK_WS = tuple(range(1, MAX_IN0_BLOCK_W + 1))
SUPPORTED_OUT_SUBBLOCK_H = 2
SUPPORTED_OUT_SUBBLOCK_W = 4
PCC_THRESHOLD = 0.995
REL_L2_THRESHOLD = 0.10
VALIDATE_SAMPLES = 1024
VALIDATE_SEED = 0
SYNC_BYTES = 0x100
SYNC_TRISC_START = TensixL1.SIZE - SYNC_BYTES
SYNC_TRISC_INIT = SYNC_TRISC_START + 16
TRISC_START_RELEASE = 0x00010101
Core = tuple[int, int]

@dataclass(frozen=True)
class RiscSync:
  start: int
  trisc_init: int

SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)
STALL_MATH_PACK_ROOM = Stall.SYNC | Stall.MATH | Stall.SFPU
STALL_MATH_PACK_DATA = Stall.TDMA
WAIT_THCON_AND_PACK = Wait.THCON | Wait.PACK0
THCON_SEC0_REG3_BASE_ADDR32 = Cfg.THCON_SEC0_REG3_Base_address.addr32
THCON_SEC1_REG3_BASE_ADDR32 = Cfg.THCON_SEC1_REG3_Base_address.addr32
THCON_SEC0_REG3_BASE_CNTX1_ADDR32 = Cfg.THCON_SEC0_REG3_Base_cntx1_address.addr32
THCON_SEC1_REG3_BASE_CNTX1_ADDR32 = Cfg.THCON_SEC1_REG3_Base_cntx1_address.addr32


PROFILE_BASE = 0x17EE00
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
PROFILE_TMP_TRISC0_SUB = PROFILE_BASE + 0x118

# 0: counters compiled out. 1: per-block/per-subblock hooks. 2: also the per-row
# unpack-context wait on TRISC0 (adds ~20 cycles per 64-cycle row; perturbs).
PROFILE_LEVEL = int(os.environ.get("MATMUL_PROFILE_COUNTERS", "0") or 0)
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
  ("trisc0_unpack_body", PROFILE_COUNTER_BASE + 0x30),
  ("trisc0_prepare", PROFILE_COUNTER_BASE + 0x34),
  ("trisc1_prepare", PROFILE_COUNTER_BASE + 0x38),
  ("trisc2_prepare", PROFILE_COUNTER_BASE + 0x3c),
  ("prepare_setup", PROFILE_COUNTER_BASE + 0x40),
  ("prepare_copy", PROFILE_COUNTER_BASE + 0x44),
  ("prepare_restore", PROFILE_COUNTER_BASE + 0x48),
)
PROFILE_COUNTER_BYTES = 0x60
DEBUG_TRISC0 = 0x17E000
DEBUG_TRISC1 = 0x17E040
DEBUG_TRISC2 = 0x17E080
DEBUG_NCRISC_OUTPUT = 0x17DF80
MEM_L1_ARC_FW_SCRATCH = 16
MATH_THROTTLED_MOP_STATUS = 0xFFB00020


_UNPACK_NOP = TT.TTUNPACR_NOP(Unpacker_Select=1, Set_Dvalid=1, Unpack_Pop=1)
_MATH_MOVA2D = TT.TTMOVA2D(addr_mode=2, instr_mod=2)

def MOP_REPLAY(start_idx: int, length: int) -> int:
  if start_idx < 16:
    raise ValueError("math MOP replay encoding is only validated here for replay slots >= 16")
  return TT.TTREPLAY(start_idx, length)

MATMUL_PACK_MOP_CFG = LoopTemplate(outer=4, inner=4, start=TT.TTNOP(), end0=TT.TTNOP(), end1=TT.TTNOP(), loop=TT.TTPACR(), alternate=TT.TTNOP(), last=TT.TTPACR(AddrMode=1, Last=1), outer_last=TT.TTPACR(AddrMode=2))
def matmul_pack_mop_cfg():
  if INPUT_DTYPE == DType.FP8: return MATMUL_PACK_MOP_CFG
  return LoopTemplate(outer=1, inner=4, loop=TT.TTREPLAY(20,4),
                      last=TT.TTREPLAY(24,4), outer_last=TT.TTREPLAY(24,4),
                      end0=TT.TTREPLAY(16,4), end1=TT.TTINCADCZW(4,0,0,1,0))


MATMUL_MATH_MOP_CFG = LoopTemplate(outer=1, inner=2, start=TT.TTNOP(), end0=TT.TTSETRWC(1, 0, 0, 0, 0, 15), end1=TT.TTNOP(), loop=MOP_REPLAY(16, 16), alternate=TT.TTNOP(), last=MOP_REPLAY(16, 16), outer_last=MOP_REPLAY(16, 16))


MATMUL_MATH_REPLAY_LOAD = [
  TT.TTMVMUL(),
  TT.TTMVMUL(addr_mode=1),
  TT.TTMVMUL(),
  TT.TTMVMUL(addr_mode=2),
  TT.TTMVMUL(),
  TT.TTMVMUL(addr_mode=1),
  TT.TTMVMUL(),
  TT.TTMVMUL(addr_mode=4),
  TT.TTMVMUL(),
  TT.TTMVMUL(addr_mode=1),
  TT.TTMVMUL(),
  TT.TTMVMUL(addr_mode=2),
  TT.TTMVMUL(),
  TT.TTMVMUL(addr_mode=1),
  TT.TTMVMUL(),
  TT.TTMVMUL(addr_mode=5),
]


def row_major_unpack_ops(engine):
  reset = TT.TTSETADCZW(engine + 1, 0, 0, 0, 0, 15)
  if INPUT_DTYPE == DType.FP8:
    # Only channel 1 (Src rows) restarts per tile; channel 0 Z/W is never
    # incremented per tile, and the batched path uses channel-0 W for K.
    reset = TT.TTSETADCZW(engine + 1, 0, 0, 0, 0, 0b0100)
    # Tileize gathers a complete 32x16 panel per instruction.
    return [reset,
            TT.TTUNPACR(engine, 0x14, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1),
            TT.TTUNPACR(engine, 0x14, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1)]
  # BH tileize reads 32 BF16 datums at a time. Gather 16 instead, using
  # descriptor Z to stride over L1 rows and CH1 Z to write consecutive Src rows.
  # Slots 0..15 hold eight row reads per engine; math owns slots 16..31.
  panel = [TT.TTREPLAY(engine * 8, 8)] * 4 + [
    TT.TTSETADCZW(engine + 1, 0, 0, 0, 0, 1),
    TT.TTINCADCXY(engine + 1, 0, 0, 1, 0)]
  return [reset, *panel, *([TT.TTREPLAY(engine * 8, 8)] * 3),
          TT.TTREPLAY(engine * 8, 7),
          TT.TTUNPACR(engine, 0x11, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1),
          TT.TTINCADCXY(engine + 1, 0, 0, 1, 0)]


def row_major_unpack_config(fw, plan):
  fp8 = INPUT_DTYPE == DType.FP8
  for engine, width in ((0, plan.per_core_n), (1, plan.in0_block_w)):
    pitch = input_row_pitch(width)
    fw.emit(TT.TTSETADCXX(engine + 1, 511 if fp8 else 15, 0))
    base = int(Cfg.THCON_SEC0_REG0_TileDescriptor) + engine * 0xc0
    fw.write32(base, 0x10 | INPUT_DTYPE.value | 16 << 16)
    if fp8 and engine == 0 and batched_unpack(plan):
      # FirstDatum = ((W*Zdim + Z)*Ydim + Y)*16: W advances 32 rows * pitch.
      assert pitch % 64 == 0 and pitch // 64 < 256
      fw.write32(base + 4, 128 | (pitch // 64) << 16)
    else:
      fw.write32(base + 4, (1 if fp8 else pitch // 32) | 1 << 16)
    fw.write32(base + 0x58, 16 | 16 << 16)
    fw.write32(base + 0x20, 0x20 | INPUT_DTYPE.value | (1 << 9 | (pitch // 16) << 16 if fp8 else 0))
    fw.write32(int(Cfg.UNP0_ADDR_CTRL_ZW_REG_1) + engine * 8, 512 if fp8 else 32)


def unpack_mop_cfg(plan=None):
  if plan is not None and batched_unpack(plan):
    # outer = K tiles, inner = B tiles; counts are overridden per MOP issue.
    return LoopTemplate(outer=plan.in0_block_w, inner=plan.out_subblock_w,
                        start=TT.TTREPLAY(REPLAY_A_TILE, 3), loop=TT.TTREPLAY(REPLAY_B_TILE, 3),
                        last=TT.TTREPLAY(REPLAY_B_TILE, 3), outer_last=TT.TTREPLAY(REPLAY_B_TILE, 3),
                        end0=TT.TTREPLAY(REPLAY_K_STEP, 2))
  if INPUT_DTYPE == DType.BF16:
    return LoopTemplate(outer=0, inner=0, start=0, end0=TT.TTREPLAY(0, 6), end1=0,
                        loop=0, alternate=0, last=TT.TTREPLAY(6, 6), outer_last=0)
  from ttko.mop import MaskTemplate
  return MaskTemplate(a0=TT.TTREPLAY(0, 3), skip_a0=TT.TTREPLAY(0, 3)).words()


def _emit_trisc0_unpack_replay_init(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  if INPUT_DTYPE == DType.FP8:
    fw.emit(TT.TTREPLAY(REPLAY_B_TILE, 3, 0, 1))
    for word in row_major_unpack_ops(0): fw.emit(word)
    if batched_unpack(plan):
      fw.emit(TT.TTREPLAY(REPLAY_A_TILE, 3, 0, 1))
      for word in row_major_unpack_ops(1): fw.emit(word)
      fw.emit(TT.TTREPLAY(REPLAY_K_STEP, 2, 0, 1))
      fw.emit(TT.TTSETADCXY(1, 0, 0, 0, 0, 0b0010))  # B: back to the first N panel
      fw.emit(TT.TTINCADCZW(1, 0, 0, 1, 0))          # B: next 32 K rows
  else:
    for slot, address in ((0, THCON_SEC0_REG3_BASE_ADDR32), (6, THCON_SEC0_REG3_BASE_CNTX1_ADDR32)):
      fw.emit(TT.TTREPLAY(slot, 6, 0, 1))
      for word in (TT.TTUNPACR(OvrdThreadId=1, SetDatValid=1, Last=1),
                   TT.TTRDCFG(0xC, address), TT.TTADDDMAREG(0, 0xC, 0xC, 0x24),
                   TT.TTSTALLWAIT(Stall.CFG, Wait.THCON), TT.TTWRCFG(0xC, 0, address), TT.TTNOP()):
        fw.emit(word)
    fw.emit(TT.TTREPLAY(12, 8, 0, 1))
    for row in range(8):
      fw.emit(TT.TTUNPACR(0, 0x11, 0, 0, 0, 1, int(row==7), 0, 0, 0, 0, 0, 1))
  return fw



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
  n_passes: int = 1
  pass_axis: str = 'n'
  logical_mt: int = 0
  logical_nt: int = 0
  m_extent: int = 0
  n_extent: int = 0
  k_extent: int = 0

  def grid(self) -> list[list[Core]]:
    return [[(x, y) for x in self.cols] for y in self.rows]

  def cores(self) -> list[Core]:
    return [core for row in self.grid() for core in row]


def input_row_pitch(width):
  row_bytes = width * 32 * INPUT_DTYPE.itemsize
  # An odd FP8 block can begin 32 bytes into an aligned NoC read.
  pitch = _align_up(row_bytes + (32 if INPUT_DTYPE == DType.FP8 and width % 2 else 0), 64)
  # Consecutive tilize rows must spread across L1 banks, rather than aliasing
  # the same banks on every read. One cache-line gap avoids that bottleneck.
  return pitch + (64 if INPUT_DTYPE == DType.FP8 and pitch % 256 == 0 else 0)


def input_page_bytes(width):
  header = 64 if width % 2 else 0
  return _align_up(_ceil_div(32 * input_row_pitch(width) + header, width), 64)


def input_dram_columns(columns):
  # Keep the physical row stride page-aligned: all rows of a block then share
  # the same page split and NoC alignment. This pads bytes; it does not tile.
  return _align_up(columns, 1024)


def plan_matmul(M: int, K: int, N: int, cores: list[Core]) -> MatmulPlan:
  if N_PASSES not in (1, 2, 4) or min(INPUT_BUFFER_FACTOR, B_BUFFER_FACTOR) < 1 or OVERLAP_BLOCKS < 0:
    raise ValueError("N passes must be 1, 2, or 4; input buffers must be positive; overlap blocks must be nonnegative")
  if N_PASSES > 1 and WRITER_WAVE_ROWS:
    raise ValueError("passes require no writer waves")
  if PASS_AXIS not in ('m', 'n'):
    raise ValueError("pass axis must be 'm' or 'n'")
  m_passes, n_passes = (N_PASSES, 1) if PASS_AXIS == 'm' else (1, N_PASSES)
  # FP32 partials always accumulate in L1, inside the output storage, so
  # every pass keeps its own output slice.
  mt_base = _ceil32(M) // TILE
  kt_base = _ceil32(K) // TILE
  nt_base = _ceil32(N) // TILE
  sbh = SUPPORTED_OUT_SUBBLOCK_H
  sbw = SUPPORTED_OUT_SUBBLOCK_W
  if sbh > sbw:
    raise ValueError("subblock height must not exceed its width")

  ordered = sorted(set(cores), key=lambda xy: (xy[0], xy[1]))
  if not ordered:
    raise SystemExit("No cores")
  core_set = frozenset(ordered)
  xs = tuple(sorted({x for x, _ in ordered}))
  ys = tuple(sorted({y for _, y in ordered}))
  if sbh * sbw > 4:
    raise ValueError("FP32 double buffering supports at most four Dst tiles per subblock")
  l1_data_bytes = CB_STORAGE_END - CB_STORAGE_BASE

  def fits_l1(pcm: int, pcn: int, bw: int) -> bool:
    if pcn % (sbw * n_passes) or pcm % (sbh * m_passes):
      return False
    cb0 = INPUT_BUFFER_FACTOR * (pcm // m_passes) * bw * input_page_bytes(bw)
    cb1 = B_BUFFER_FACTOR * (pcn // n_passes) * bw * input_page_bytes(pcn // n_passes)
    cb_out = pcm * pcn * TILE_BYTES
    prepared = (pcm // m_passes + pcn // n_passes) * bw * INPUT_TILE_BYTES if INPUT_DTYPE == DType.BF16 else 0
    return cb0 + cb1 + cb_out + prepared <= l1_data_bytes

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
          if nr > _ceil_div(M, 8) or nc > _ceil_div(N, 16):
            continue
          pcm = _align_up(_ceil_div(mt_base, nr), sbh * m_passes)
          pcn = _align_up(_ceil_div(nt_base, nc), sbw * n_passes)
          if n_passes > 1 and _ceil_div(N, nc * 16) * 16 <= (n_passes - 1) * (pcn // n_passes) * TILE:
            continue  # Every pass must contain at least one logical output tile.
          if m_passes > 1 and _ceil_div(M, nr * 8) * 8 <= (m_passes - 1) * (pcm // m_passes) * TILE:
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
    cb0_pages=INPUT_BUFFER_FACTOR * (pcm // m_passes) * bw, cb1_pages=B_BUFFER_FACTOR * (pcn // n_passes) * bw,
    cb16_pages=out_tiles, cb24_pages=out_tiles // N_PASSES,
    n_passes=N_PASSES, pass_axis=PASS_AXIS,
    logical_mt=mt_base, logical_nt=nt_base,
    m_extent=_ceil_div(M, len(rows)*8)*8,
    n_extent=_ceil_div(N, len(cols)*16)*16,
    k_extent=_align_up(K, 16),
  )

class MatmulKernel(KernelBase, NocOps, CircularBufferOps):
  """Shared base for matmul's hand-written dataflow kernels."""

  def dram_tile_addr_from(self, table_base, noc_table_offset=0, *, tile_bytes=2048):
    from .asm import CONTEXT
    banks = len(CONTEXT['endpoints'])
    if banks != 8:
      return super().dram_tile_addr_from(table_base, noc_table_offset, tile_bytes=tile_bytes)
    self.srli(R.T0, R.A1, 3)
    self.andi(R.A1, R.A1, 7)
    self.slli(R.T0, R.T0, tile_bytes.bit_length() - 1)
    self.add(R.A0, R.A0, R.T0)
    if isinstance(noc_table_offset, R):
      self.add(R.T1, R.A1, noc_table_offset)
    else:
      self.addi(R.T1, R.A1, noc_table_offset)
    self.slli(R.T1, R.T1, 1)
    self.li(R.T2, table_base)
    self.add(R.T2, R.T2, R.T1)
    return self.lhu(R.A2, R.T2, 0)

  def rta_ptr(self, mailbox_addr: int, *, out=R.S11):
    return self.read32(out, mailbox_addr)

  def arg(self, dst, index: int, *, ptr=R.S11):
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

class MatmulTrisc(KernelBase, TensixOps, CircularBufferOps):
  NUM_TRISC = 3

  def __init__(self, thread_id: int, sync: RiscSync = SYNC, *, base_addr: int = 0):
    super().__init__(role=f"trisc{thread_id}")
    self.thread_id = thread_id
    self.sync = sync
    self.data = TriscMailbox.DATA1 if thread_id == 1 else TriscMailbox.DATA_COMMON
    from ttko.fpu import BlockedMath
    from ttko.pack import BlockedPack
    from ttko.unpack import BlockedUnpack
    self.unpack = BlockedUnpack(self)
    self.math = BlockedMath(self)
    self.pack = BlockedPack(self, fp8=INPUT_DTYPE == DType.FP8, fp32=True)

  def prologue(self):
    self.write32(PASS_BASE + 96 + self.thread_id * 4, 0)
    self.addi(R.SP, R.SP, -16)
    self.sw(R.RA, R.SP, 12)
    self.wait8(self.sync.start + self.thread_id, 1)
    self.write8(self.sync.start + self.thread_id, 0)
    return self

  def init_barrier(self):
    self.write32(self.sync.trisc_init + self.thread_id * 4, 1)
    self.fence()
    self.li(R.T1, 1)
    for init_id in range(self.NUM_TRISC):
      self.wait_sync_value(self.sync.trisc_init + init_id * 4, R.T1, actual=R.T2)
    return self

  def ret_kernel(self):
    self.emit(TT.TTSTALLWAIT(Stall.SYNC, (Wait.UNPACK0 | Wait.UNPACK1, Wait.MATH | Wait.SFPU, Wait.PACK0 | Wait.THCON)[self.thread_id]))
    self.tensix_sync(self.thread_id)
    self.lw(R.RA, R.SP, 12)
    self.addi(R.SP, R.SP, 16)
    return self.ret()


def _emit_mcast_chunks(fw: MatmulKernel, noc_id: int, src_addr, coord, total_bytes: int, *, tmp=R.T5):
  chunks = _ceil_div(total_bytes, NOC.MAX_BURST_SIZE)
  for chunk in range(chunks):
    size = min(NOC.MAX_BURST_SIZE, total_bytes - chunk * NOC.MAX_BURST_SIZE)
    fw.li(tmp, size)
    fw.noc_write(noc_id, 0, src_addr, src_addr, 0, coord, tmp, mcast=True, a=R.T1, v=R.T2)
    if chunk != chunks - 1:
      fw.add(src_addr, src_addr, tmp)
  return chunks

def _output_wait_ready(fw, val=R.T1):
  loop = fw._new_label('output_ready')
  fw.label(loop)
  fw.lw(val, R.GP, 0x40)
  fw.bne(val, R.ZERO, loop)


def _output_reg(fw, offset, value, tmp=R.T1):
  if not isinstance(value, R):
    fw.li(tmp, value)
    value = tmp
  return fw.sw(value, R.GP, offset)


def output_pending(fw, out):
  if N_PASSES > 1:
    fw.li(R.T0, 0x1000)
    fw.sub(R.T0, R.GP, R.T0)
    fw.lw(out, R.T0, 0x248)
  else:
    fw.lw(out, R.GP, 0x248)


def emit_output_write_state_setup(fw: MatmulKernel, length: int = 0) -> MatmulKernel:
  _output_wait_ready(fw)
  _output_reg(fw, 0x18, 2 << 10)
  _output_reg(fw, 0x1c, NOC.CMD_WR_FIELD)
  _output_reg(fw, 0x10, 0)
  _output_reg(fw, 0x20, length or TILE_BYTES)
  return _output_reg(fw, 0x24, 0)


def emit_output_write_stateful(fw: MatmulKernel, src, dst_lo, dst_coord) -> MatmulKernel:
  # GP is the runtime-selected NoC's command-buffer base, reserved by Asm.
  # Keep the TID counter within the hardware's unambiguous half range.
  issue = fw._new_label("output_issue_safe")
  fw.li(R.T6, 129)
  fw.label(issue)
  output_pending(fw, R.A5)
  fw.bgeu(R.A5, R.T6, issue)
  _output_wait_ready(fw, val=R.A5)
  _output_reg(fw, 0x00, src, tmp=R.A5)
  _output_reg(fw, 0x0c, dst_lo, tmp=R.A5)
  _output_reg(fw, 0x14, dst_coord, tmp=R.A5)
  return _output_reg(fw, 0x40, NOC.CTRL_SEND_REQ, tmp=R.A5)


def _move_plus_imm(fw: KernelBase, dst, src, imm: int, *, tmp=R.T4):
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

def emit_profile_stamp(fw: KernelBase, addr: int):
  if fw.role.startswith('trisc') and addr in (PROFILE_TRISC0, PROFILE_TRISC1, PROFILE_TRISC2):
    fw.csrrs(R.T1, R.ZERO, 0x7c0)
    fw.write32(addr + 16, R.T1)
  fw.read32(R.T1, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L, tmp_addr=R.T0)
  fw.write32(addr, R.T1, tmp_addr=R.T0)
  fw.read32(R.T1, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H, tmp_addr=R.T0)
  fw.write32(addr + 4, R.T1, tmp_addr=R.T0)
  return fw

def emit_progress_mark(fw: KernelBase, addr: int, code: int, block_reg=R.S6, i0_reg=R.S4, i1_reg=R.S5):
  if not ENABLE_BREADCRUMBS:
    return fw
  fw.write32(addr + 0, code, tmp_addr=R.T0, tmp_val=R.T1)
  fw.write32(addr + 4, block_reg, tmp_addr=R.T0, tmp_val=R.T1)
  fw.write32(addr + 8, i0_reg, tmp_addr=R.T0, tmp_val=R.T1)
  fw.write32(addr + 12, i1_reg, tmp_addr=R.T0, tmp_val=R.T1)
  return fw

def emit_cb_debug_snapshot(fw: KernelBase, addr: int, cb_index: int, code: int):
  emit_progress_mark(fw, addr, code)
  return fw


def emit_profile_accum_start(fw: KernelBase, tmp_addr: int, *, level: int = 1):
  if PROFILE_LEVEL < level:
    return fw
  fw.read32(R.T1, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L, tmp_addr=R.T0)
  return fw.write32(tmp_addr, R.T1, tmp_addr=R.T0)

def emit_profile_accum_end(fw: KernelBase, counter_addr: int, tmp_addr: int, *, level: int = 1):
  if PROFILE_LEVEL < level:
    return fw
  fw.read32(R.T1, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L, tmp_addr=R.T0)
  fw.read32(R.T2, tmp_addr, tmp_addr=R.T0)
  fw.sub(R.T1, R.T1, R.T2)
  fw.read32(R.T2, counter_addr, tmp_addr=R.T0)
  fw.add(R.T1, R.T1, R.T2)
  return fw.write32(counter_addr, R.T1, tmp_addr=R.T0)

def pass_address(fw):
  return PASS_BASE + {'brisc': 0, 'ncrisc': 4, 'trisc0': 8, 'trisc1': 12, 'trisc2': 16}[fw.role]


def begin_passes(fw, plan):
  if plan.n_passes == 1:
    return None
  label = fw._new_label('n_pass')
  fw.write32(pass_address(fw), 0)
  fw.label(label)
  if plan.n_passes > 1 and fw.role in ('trisc0','trisc2'):
    from .asm import CONTEXT
    base = next(address for index,address,_,_ in CONTEXT['cbs'] if index == 16)
    fw.read32(R.T1, pass_address(fw))
    fw.li(R.T2, plan.out_block_num_tiles * TILE_BYTES // 16)
    fw.mul(R.T1, R.T1, R.T2)
    fw.li(R.T3, base // 16)
    fw.add(R.T1, R.T1, R.T3)
    fw.cb_iface(fw.data['cb_interface'], 24, out=R.T6)
    fw.sw(R.T1, R.T6, 16)
    fw.sw(R.T1, R.T6, 20)
    fw.add(R.T1, R.T1, R.T2)
    fw.sw(R.T1, R.T6, 4)
  return label


def end_passes(fw, plan, label):
  if label is None:
    return
  fw.read32(R.T1, pass_address(fw))
  fw.addi(R.T1, R.T1, 1)
  fw.write32(pass_address(fw), R.T1)
  fw.li(R.T2, plan.n_passes)
  fw.blt(R.T1, R.T2, label)


def matmul_reader(plan: MatmulPlan) -> MatmulKernel:
  from .args import emit_args
  fw = MatmulKernel(role="brisc")
  fw.row_major_plan = plan
  emit_profile_stamp(fw, PROFILE_BRISC)
  emit_args(fw, plan, reader=True)
  fw.release_triscs()
  pass_loop = begin_passes(fw, plan)
  fw.rta_ptr(BM.RTA_L1_BASE_PTR)
  fw.read32(R.T1, LaunchL1.GRID_RANK_BASE + 4)
  sender, done = fw._new_label('a_sender'), fw._new_label('a_done')
  fw.beq(R.T1, R.ZERO, sender)
  emit_reader_recv(fw)
  fw.j(done)
  fw.label(sender)
  emit_reader_sender(fw, plan)
  fw.label(done)
  if plan.n_passes > 1 and plan.pass_axis == 'm':
    fw.rta_ptr(BM.RTA_L1_BASE_PTR)
    fw.arg(R.T1, 1)
    _move_plus_imm(fw, R.T1, R.T1, plan.per_core_m * plan.kt, tmp=R.T2)
    fw.sw(R.T1, R.S11, 4)
  end_passes(fw, plan, pass_loop)
  emit_profile_stamp(fw, PROFILE_BRISC + 8)
  fw.write32(A_DONE, 1)
  fw.fence()
  return fw.ret()


def matmul_writer(plan: MatmulPlan) -> MatmulKernel:
  from .args import emit_args
  fw = MatmulKernel(role="ncrisc")
  fw.row_major_plan = plan
  emit_profile_stamp(fw, PROFILE_NCRISC)
  emit_profile_stamp(fw, PROFILE_NCRISC_INPUT)
  emit_args(fw, plan, reader=False)
  pass_loop = begin_passes(fw, plan)
  if plan.n_passes > 1:
    fw.write32(PASS_BASE + 24, 0)
  fw.rta_ptr(NM.RTA_L1_BASE_PTR)
  fw.read32(R.T1, LaunchL1.GRID_RANK_BASE)
  sender, done = fw._new_label('b_sender'), fw._new_label('b_done')
  fw.beq(R.T1, R.ZERO, sender)
  emit_writer_recv(fw, plan)
  fw.j(done)
  fw.label(sender)
  emit_writer_sender(fw, plan)
  fw.label(done)
  emit_profile_stamp(fw, PROFILE_NCRISC_INPUT + 8)
  if plan.n_passes > 1:
    if plan.pass_axis == 'n':
      fw.rta_ptr(NM.RTA_L1_BASE_PTR)
      fw.arg(R.T1, 1)
      fw.addi(R.T1, R.T1, plan.per_core_n)
      fw.sw(R.T1, R.S11, 4)
  else:
    emit_output_writer(fw, plan)
  end_passes(fw, plan, pass_loop)
  if plan.n_passes > 1:
    fw.rta_ptr(NM.RTA_L1_BASE_PTR)
    emit_output_writer(fw, plan)
  emit_profile_stamp(fw, PROFILE_NCRISC + 8)
  return fw.ret()


def emit_input_read_setup(fw, noc):
  if not FAST_READS:
    return
  fw.li(R.GP, NOC.REGS_START_ADDR + (noc << 16) + (1 << 11))
  _output_wait_ready(fw)
  fw.local_noc0_coord(R.A5, x_addr=BM.MY_X if noc == 0 else NM.MY_X,
                      y_addr=BM.MY_Y if noc == 0 else NM.MY_Y)
  for offset, value in ((0x1c,NOC.CMD_RD_FIELD),(0x10,0),(0x14,R.A5),
                        (0x04,0),(0x24,0)):
    _output_reg(fw, offset, value)


def emit_input_read(fw, noc):
  if not FAST_READS:
    fw.local_noc0_coord(R.A5, x_addr=BM.MY_X if noc == 0 else NM.MY_X,
                        y_addr=BM.MY_Y if noc == 0 else NM.MY_Y)
    fw.noc_read(noc, 1, R.A0, 0, R.A2, R.A4, R.T6, ret_coord=R.A5, a=R.T3, v=R.T5)
  else:
    _output_wait_ready(fw, val=R.T3)
    for offset, value in ((0x00,R.A0),(0x08,R.A2),(0x0c,R.A4),(0x20,R.T6),(0x40,NOC.CTRL_SEND_REQ)):
      _output_reg(fw, offset, value)
  fw.add(R.A4, R.A4, R.T6)


def emit_row_major_block_read(fw, noc, width):
  """Read aligned row spans directly into input CBs, without element copies."""
  from .asm import CONTEXT
  mailbox = BM if noc == 0 else NM
  banks_arg = 23 if noc == 0 else 29
  pitch = input_row_pitch(width)
  item_shift = INPUT_DTYPE.itemsize.bit_length() - 1
  fw.divu(R.T1, R.A6, R.S3)
  fw.remu(R.T2, R.A6, R.S3)
  fw.slli(R.T1, R.T1, 5)
  fw.slli(R.T0, R.S3, 5 + item_shift)
  fw.addi(R.T0, R.T0, INPUT_TILE_BYTES - 1)
  fw.andi(R.T0, R.T0, -INPUT_TILE_BYTES)
  fw.mul(R.T1, R.T1, R.T0)
  fw.slli(R.T2, R.T2, 5 + item_shift)
  fw.add(R.T4, R.T1, R.T2)
  fw.mv(R.S2, R.A4)
  if width % 2:
    fw.andi(R.T0, R.T4, 63)
    fw.addi(R.T0, R.T0, 64)
    fw.sw(R.T0, R.A4, 0)
    fw.addi(R.A4, R.A4, 64)
  if FAST_READS and width <= 32 and width % 2 == 0:
    plan = fw.row_major_plan
    global_pitch = _align_up((plan.nt if noc else plan.kt) * 32 * INPUT_DTYPE.itemsize, INPUT_TILE_BYTES)
    if len(CONTEXT['endpoints']) == 8:
      # Eight rows repeat the DRAM-bank pattern. Resolve the starting bank
      # once, then issue that sequence without per-row divides or table loads.
      fw.mv(R.A5, R.T4)
      fw.li(R.A1, 0)
      chunk = fw._new_label('raw_row_chunk')
      fw.label(chunk)
      fw.add(R.T4, R.A5, R.A1)
      fw.add(R.A4, R.S2, R.A1)
      fw.andi(R.T5, R.T4, INPUT_TILE_BYTES - 1)
      fw.li(R.T6, INPUT_TILE_BYTES)
      fw.sub(R.T6, R.T6, R.T5)
      fw.li(R.T1, width * 32 * INPUT_DTYPE.itemsize)
      fw.sub(R.T1, R.T1, R.A1)
      full = fw._new_label('raw_chunk_full')
      fw.bgeu(R.T1, R.T6, full)
      fw.mv(R.T6, R.T1)
      fw.label(full)
      _output_wait_ready(fw)
      _output_reg(fw, 0x20, R.T6)
      fw.srli(R.T0, R.T4, INPUT_TILE_BYTES.bit_length() - 1)
      fw.andi(R.T0, R.T0, 7)
      fw.andi(R.T5, R.T4, INPUT_TILE_BYTES - 1)
      fw.srli(R.T4, R.T4, INPUT_TILE_BYTES.bit_length() + 2)
      fw.slli(R.T4, R.T4, INPUT_TILE_BYTES.bit_length() - 1)
      fw.add(R.T4, R.T4, R.T5)
      fw.add(R.T4, R.T4, R.S0)
      fw.li(R.TP, NOC.CTRL_SEND_REQ)
      fw.li(R.A3, 4)
      done = fw._new_label('row_banks_done')
      for bank in range(8):
        next_bank = fw._new_label('next_row_bank')
        if bank < 7:
          fw.li(R.T1, bank)
          fw.bne(R.T0, R.T1, next_bank)
        loop = fw._new_label('eight_rows')
        fw.label(loop)
        for row in range(8):
          page = bank + row * (global_pitch // INPUT_TILE_BYTES)
          x, y = CONTEXT['endpoints'][page % 8][noc]
          _move_plus_imm(fw, R.A0, R.T4, (page // 8) * INPUT_TILE_BYTES, tmp=R.T1)
          fw.li(R.A2, x | y << 6)
          _output_wait_ready(fw, val=R.T3)
          for offset, value in ((0x00,R.A0),(0x08,R.A2),(0x0c,R.A4),(0x40,R.TP)):
            _output_reg(fw, offset, value)
          _move_plus_imm(fw, R.A4, R.A4, pitch, tmp=R.T1)
        _move_plus_imm(fw, R.T4, R.T4, global_pitch, tmp=R.T1)
        fw.addi(R.A3, R.A3, -1)
        fw.bne(R.A3, R.ZERO, loop)
        fw.j(done)
        fw.label(next_bank)
      fw.label(done)
      fw.addi(R.A7, R.A7, 32)
      fw.add(R.A1, R.A1, R.T6)
      fw.li(R.T0, width * 32 * INPUT_DTYPE.itemsize)
      fw.bltu(R.A1, R.T0, chunk)
      _move_plus_imm(fw, R.A4, R.S2, width * input_page_bytes(width))
      return

  fw.li(R.A3, 32)
  row, chunk = fw._new_label('input_row'), fw._new_label('input_page')
  fw.label(row)
  fw.li(R.TP, 0)
  fw.label(chunk)
  fw.andi(R.T0, R.T4, -64)
  fw.add(R.T0, R.T0, R.TP)
  fw.andi(R.T5, R.T0, INPUT_TILE_BYTES - 1)
  fw.li(R.T6, INPUT_TILE_BYTES)
  fw.sub(R.T6, R.T6, R.T5)
  fw.andi(R.T2, R.T4, 63)
  fw.li(R.T1, width * 32 * INPUT_DTYPE.itemsize + 63)
  fw.add(R.T1, R.T1, R.T2)
  fw.andi(R.T1, R.T1, -64)
  fw.sub(R.T1, R.T1, R.TP)
  full = fw._new_label('input_full_page')
  fw.bgeu(R.T1, R.T6, full)
  fw.mv(R.T6, R.T1)
  fw.label(full)
  fw.srli(R.A1, R.T0, INPUT_TILE_BYTES.bit_length() - 1)
  fw.mv(R.A0, R.S0)
  fw.arg(R.A2, banks_arg)
  fw.dram_tile_addr_from(mailbox.DRAM_BANK_TO_NOC_XY,
                         R.A2 if noc else 0, tile_bytes=INPUT_TILE_BYTES)
  fw.add(R.A0, R.A0, R.T5)
  emit_input_read(fw, noc)
  fw.addi(R.A7, R.A7, 1)
  fw.add(R.TP, R.TP, R.T6)
  fw.andi(R.T0, R.T4, 63)
  fw.li(R.T1, width * 32 * INPUT_DTYPE.itemsize + 63)
  fw.add(R.T0, R.T0, R.T1)
  fw.andi(R.T0, R.T0, -64)
  fw.bltu(R.TP, R.T0, chunk)
  fw.li(R.T1, pitch)
  fw.sub(R.T1, R.T1, R.T0)
  fw.add(R.A4, R.A4, R.T1)
  fw.slli(R.T0, R.S3, 5 + item_shift)
  fw.addi(R.T0, R.T0, INPUT_TILE_BYTES - 1)
  fw.andi(R.T0, R.T0, -INPUT_TILE_BYTES)
  fw.add(R.T4, R.T4, R.T0)
  fw.addi(R.A3, R.A3, -1)
  fw.bne(R.A3, R.ZERO, row)
  _move_plus_imm(fw, R.A4, R.S2, width * input_page_bytes(width))
  return

def emit_reader_sender(fw: MatmulKernel, plan: MatmulPlan) -> MatmulKernel:
  fw.arg(R.S0, 0)   # A base
  fw.arg(R.S1, 1)   # current first tile
  fw.arg(R.S3, 3)   # row tile stride
  fw.arg(R.S4, 4)   # next K-block offset
  fw.arg(R.S6, 6)   # block_h
  fw.arg(R.S7, 7)   # block_tiles
  fw.arg(R.S8, 8)   # nblocks
  fw.arg(R.S9, 18)  # east receiver count
  fw.arg(R.S10, 9)  # west receiver count, patched below after rect args
  fw.arg(R.S10, 13)
  fw.add(R.S10, R.S10, R.S9)

  fw.arg(R.T0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, R.T0, out=R.T6)
  fw.noc_semaphore_set(R.T6, 1)

  emit_input_read_setup(fw, 0)
  fw.li(R.S6, 0)
  fw.label("reader_sender_block_loop")
  fw.bne(R.S6, R.S8, "reader_sender_block_body")
  fw.j("reader_sender_done")
  fw.label("reader_sender_block_body")
  emit_profile_accum_start(fw, PROFILE_TMP_BRISC)
  fw.cb_reserve_back(BM.CB_INTERFACE, 0, R.S7)
  fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=R.S9)
  fw.mv(R.A4, R.S9)
  fw.li(R.T5, 0)
  fw.mv(R.A6, R.S1)
  fw.li(R.T0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.lw(R.A7, R.T0, 0)

  fw.mv(R.A6, R.S1)
  fw.li(R.S5, plan.per_core_m)
  fw.label('reader_tile_rows')
  emit_row_major_block_read(fw, 0, plan.in0_block_w)
  fw.add(R.A6, R.A6, R.S3)
  fw.addi(R.S5,R.S5,-1)
  fw.bne(R.S5,R.ZERO,'reader_tile_rows')

  fw.noc_reads_flushed(0, R.A7)
  fw.arg(R.T0, 21)
  fw.sem_addr(BM.SEM_L1_BASE, R.T0, out=R.A3)
  fw.noc_semaphore_wait(R.A3, R.S10)
  fw.noc_semaphore_set(R.A3, 0)

  fw.arg(R.T0, 13)
  fw.beq(R.T0, R.ZERO, "reader_sender_skip_west")
  fw.arg(R.T1, 9)
  fw.arg(R.T2, 10)
  fw.arg(R.T3, 11)
  fw.arg(R.T5, 12)
  fw.noc_mcast_coord(R.A5, R.T1, R.T2, R.T3, R.T5)
  fw.li(R.T0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT)
  fw.lw(R.A6, R.T0, 0)
  block_bytes = plan.in0_block_num_tiles * input_page_bytes(plan.in0_block_w)
  fw.addi(R.A6, R.A6, _ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(R.A0, R.S9)
  _emit_mcast_chunks(fw, 0, R.A0, R.A5, block_bytes)
  fw.noc_nonposted_writes_flushed(0, R.A6)
  fw.arg(R.T0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, R.T0, out=R.A4)
  fw.arg(R.T1, 9)
  fw.arg(R.T2, 10)
  fw.arg(R.T3, 11)
  fw.arg(R.T5, 12)
  fw.noc_mcast_coord(R.A5, R.T1, R.T2, R.T3, R.T5)
  fw.noc_semaphore_set_multicast(0, 0, R.A4, R.A5, 1, R.T0, a=R.T1, v=R.T2)
  fw.label("reader_sender_skip_west")

  fw.arg(R.T0, 18)
  fw.beq(R.T0, R.ZERO, "reader_sender_skip_east")
  fw.arg(R.T1, 14)
  fw.arg(R.T2, 15)
  fw.arg(R.T3, 16)
  fw.arg(R.T5, 17)
  fw.noc_mcast_coord(R.A5, R.T1, R.T2, R.T3, R.T5)
  fw.li(R.T0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT)
  fw.lw(R.A6, R.T0, 0)
  fw.addi(R.A6, R.A6, _ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(R.A0, R.S9)
  _emit_mcast_chunks(fw, 0, R.A0, R.A5, block_bytes)
  fw.noc_nonposted_writes_flushed(0, R.A6)
  fw.arg(R.T0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, R.T0, out=R.A4)
  fw.arg(R.T1, 14)
  fw.arg(R.T2, 15)
  fw.arg(R.T3, 16)
  fw.arg(R.T5, 17)
  fw.noc_mcast_coord(R.A5, R.T1, R.T2, R.T3, R.T5)
  fw.noc_semaphore_set_multicast(0, 0, R.A4, R.A5, 1, R.T0, a=R.T1, v=R.T2)
  fw.label("reader_sender_skip_east")

  fw.cb_push_back(BM.CB_INTERFACE, 0, R.S7)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[0][1], PROFILE_TMP_BRISC)
  fw.add(R.S1, R.S1, R.S4)
  fw.addi(R.S6, R.S6, 1)
  fw.j("reader_sender_block_loop")
  fw.label("reader_sender_done")
  fw.fence()
  return fw

def emit_reader_recv(fw: MatmulKernel) -> MatmulKernel:
  fw.arg(R.S7, 7)
  fw.arg(R.S8, 8)
  fw.li(R.S0, 0)
  fw.label("reader_recv_block_loop")
  fw.beq(R.S0, R.S8, "reader_recv_done")
  emit_profile_accum_start(fw, PROFILE_TMP_BRISC)
  fw.cb_reserve_back(BM.CB_INTERFACE, 0, R.S7)
  fw.arg(R.T0, 22)
  fw.sem_addr(BM.SEM_L1_BASE, R.T0, out=R.S1)
  fw.noc_semaphore_set(R.S1, 0)
  fw.arg(R.T0, 21)
  fw.sem_addr(BM.SEM_L1_BASE, R.T0, out=R.S2)
  fw.arg(R.T1, 19)
  fw.arg(R.T2, 20)
  fw.noc_coord(R.A5, R.T1, R.T2)
  fw.local_noc0_coord(R.A6)
  fw.noc_semaphore_inc(0, 3, R.S2, R.A5, 1, ret_coord=R.A6, a=R.T3, v=R.T4)
  fw.noc_semaphore_wait(R.S1, 1)
  fw.cb_push_back(BM.CB_INTERFACE, 0, R.S7)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[0][1], PROFILE_TMP_BRISC)
  fw.addi(R.S0, R.S0, 1)
  fw.j("reader_recv_block_loop")
  fw.label("reader_recv_done")
  fw.fence()
  return fw

def emit_writer_sender(fw: MatmulKernel, plan: MatmulPlan) -> MatmulKernel:
  fw.arg(R.S0, 0)   # B base
  fw.arg(R.S1, 1)   # current first tile
  fw.arg(R.S3, 3)   # row tile stride
  fw.arg(R.S4, 4)   # next K-block offset
  fw.arg(R.S5, 5)   # block_w
  fw.arg(R.S6, 6)   # block_h
  fw.arg(R.S7, 7)   # block_tiles
  fw.arg(R.S8, 8)   # nblocks
  fw.arg(R.S10, 13) # receiver count

  fw.arg(R.T0, 17)
  fw.sem_addr(NM.SEM_L1_BASE, R.T0, out=R.T6)
  fw.noc_semaphore_set(R.T6, 1)

  emit_input_read_setup(fw, 1)
  fw.li(R.S6, 0)
  fw.label("writer_sender_block_loop")
  fw.bne(R.S6, R.S8, "writer_sender_block_body")
  fw.j("writer_sender_blocks_done")
  fw.label("writer_sender_block_body")
  emit_profile_accum_start(fw, PROFILE_TMP_NCRISC)
  fw.cb_reserve_back(NM.CB_INTERFACE, 1, R.S7)
  fw.cb_write_ptr(NM.CB_INTERFACE, 1, out=R.S9)
  fw.mv(R.A4, R.S9)
  fw.mv(R.A6, R.S1)
  fw.li(R.T0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(R.A7, R.T0, 0)

  fw.mv(R.A6, R.S1)
  fw.li(R.S5, plan.in0_block_w)
  fw.label('writer_tile_rows')
  emit_row_major_block_read(fw, 1, plan.per_core_n)
  fw.add(R.A6, R.A6, R.S3)
  fw.addi(R.S5,R.S5,-1)
  fw.bne(R.S5,R.ZERO,'writer_tile_rows')

  fw.noc_reads_flushed(1, R.A7)
  fw.arg(R.T0, 16)
  fw.sem_addr(NM.SEM_L1_BASE, R.T0, out=R.A3)
  fw.noc_semaphore_wait(R.A3, R.S10)
  fw.noc_semaphore_set(R.A3, 0)

  fw.arg(R.T0, 13)
  fw.beq(R.T0, R.ZERO, "writer_sender_skip_mcast")
  fw.arg(R.T1, 9)
  fw.arg(R.T2, 10)
  fw.arg(R.T3, 11)
  fw.arg(R.T5, 12)
  fw.noc_mcast_coord(R.A5, R.T1, R.T2, R.T3, R.T5)
  fw.li(R.T0, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(R.A6, R.T0, 0)
  block_bytes = plan.in1_block_num_tiles * input_page_bytes(plan.per_core_n)
  fw.addi(R.A6, R.A6, _ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(R.A0, R.S9)
  _emit_mcast_chunks(fw, 1, R.A0, R.A5, block_bytes)
  fw.noc_nonposted_writes_flushed(1, R.A6)
  fw.arg(R.T0, 17)
  fw.sem_addr(NM.SEM_L1_BASE, R.T0, out=R.A4)
  fw.arg(R.T1, 9)
  fw.arg(R.T2, 10)
  fw.arg(R.T3, 11)
  fw.arg(R.T5, 12)
  fw.noc_mcast_coord(R.A5, R.T1, R.T2, R.T3, R.T5)
  fw.noc_semaphore_set_multicast(1, 0, R.A4, R.A5, 1, R.T0, a=R.T1, v=R.T2)
  fw.label("writer_sender_skip_mcast")

  fw.cb_push_back(NM.CB_INTERFACE, 1, R.S7)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[1][1], PROFILE_TMP_NCRISC)
  fw.add(R.S1, R.S1, R.S4)
  emit_overlap_output(fw, plan, R.S6)
  fw.addi(R.S6, R.S6, 1)
  fw.j("writer_sender_block_loop")
  fw.label("writer_sender_blocks_done")
  return fw

def emit_writer_recv(fw: MatmulKernel, plan: MatmulPlan) -> MatmulKernel:
  fw.arg(R.S7, 7)
  fw.arg(R.S8, 8)
  fw.li(R.S0, 0)
  fw.label("writer_recv_block_loop")
  fw.beq(R.S0, R.S8, "writer_recv_blocks_done")
  emit_profile_accum_start(fw, PROFILE_TMP_NCRISC)
  fw.cb_reserve_back(NM.CB_INTERFACE, 1, R.S7)
  fw.arg(R.T0, 17)
  fw.sem_addr(NM.SEM_L1_BASE, R.T0, out=R.S1)
  fw.noc_semaphore_set(R.S1, 0)
  fw.arg(R.T0, 16)
  fw.sem_addr(NM.SEM_L1_BASE, R.T0, out=R.S2)
  fw.arg(R.T1, 14)
  fw.arg(R.T2, 15)
  fw.noc_coord(R.A5, R.T1, R.T2)
  fw.local_noc0_coord(R.A6, x_addr=NM.MY_X, y_addr=NM.MY_Y)
  fw.noc_semaphore_inc(1, 3, R.S2, R.A5, 1, ret_coord=R.A6, a=R.T3, v=R.T4)
  fw.noc_semaphore_wait(R.S1, 1)
  fw.cb_push_back(NM.CB_INTERFACE, 1, R.S7)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[1][1], PROFILE_TMP_NCRISC)
  emit_overlap_output(fw, plan, R.S0)
  fw.addi(R.S0, R.S0, 1)
  fw.j("writer_recv_block_loop")
  fw.label("writer_recv_blocks_done")
  return fw

def emit_overlap_output(fw, plan, block_reg):
  if plan.n_passes == 1:
    return
  from dataclasses import replace
  from .asm import ARG_BASE
  done = fw._new_label('overlap_done')
  fw.read32(R.T1, pass_address(fw))
  fw.beq(R.T1, R.ZERO, done)
  # Feed this input block, then retire its share of the previous pass's rows.
  fw.addi(R.T1, block_reg, 1)
  fw.li(R.T2, plan.in0_num_subblocks)
  fw.mul(R.T1, R.T1, R.T2)
  fw.li(R.T2, OVERLAP_BLOCKS or plan.num_blocks)
  fw.divu(R.T1, R.T1, R.T2)
  fw.li(R.T2, plan.in0_num_subblocks)
  budget_ready = fw._new_label('overlap_budget_ready')
  fw.blt(R.T1, R.T2, budget_ready)
  fw.mv(R.T1, R.T2)
  fw.label(budget_ready)
  fw.write32(PASS_BASE + 28, R.T1)
  saved = (R.S0,R.S1,R.S2,R.S3,R.S4,R.S5,R.S6,R.S7,R.S8,R.S9,R.S10,R.S11,R.GP)
  for i, reg in enumerate(saved):
    fw.write32(PASS_BASE + 32 + i*4, reg)
  loop = fw._new_label('overlap_row')
  restore = fw._new_label('overlap_restore')
  fw.label(loop)
  fw.read32(R.T1, PASS_BASE + 24)
  fw.read32(R.T2, PASS_BASE + 28)
  fw.bge(R.T1, R.T2, restore)
  fw.rta_ptr(NM.RTA_L1_BASE_PTR)
  fw.write32(ARG_BASE + 128 + 28*4, 1)
  emit_output_writer(fw, replace(plan, in0_num_subblocks=1), row_chunk=True)
  fw.read32(R.T1, PASS_BASE + 24)
  fw.addi(R.T1, R.T1, 1)
  fw.write32(PASS_BASE + 24, R.T1)
  fw.j(loop)
  fw.label(restore)
  fw.write32(ARG_BASE + 128 + 28*4, plan.in0_num_subblocks)
  for i, reg in enumerate(saved):
    fw.read32(reg, PASS_BASE + 32 + i*4)
  fw.label(done)


def emit_output_writer(fw: MatmulKernel, plan: MatmulPlan, *, row_chunk=False) -> MatmulKernel:
  from .writers import wait_turn, finish
  observer = False
  cb_interface = BM.CB_INTERFACE if observer else NM.CB_INTERFACE
  # params[4]: 0/1 selects a fixed NoC; 2 selects logical-column parity.
  fw.read32(R.T3, LaunchL1.PARAM_BASE + 16)
  selected = fw._new_label('output_noc_selected')
  fw.li(R.T4, 2)
  fw.bne(R.T3, R.T4, selected)
  fw.read32(R.T3, LaunchL1.GRID_RANK_BASE + 4)
  fw.andi(R.T3, R.T3, 1)
  fw.xori(R.T3, R.T3, 1)
  fw.label(selected)
  fw.mv(R.S8, R.T3)  # Preserve output NoC for its preferred DRAM-port table.
  fw.slli(R.GP, R.T3, 16)
  fw.li(R.T0, NOC.REGS_START_ADDR + (0x1000 if plan.n_passes > 1 else 0))
  fw.add(R.GP, R.GP, R.T0)
  ready = fw._new_label('output_noc_ready')
  if plan.n_passes == 1:
    fw.bne(R.T3, R.ZERO, ready)
    fw.li(R.T3, 1)
    fw.wait_sync_value(A_DONE, R.T3, actual=R.T4)
  fw.label(ready)
  wait_turn(fw, plan, WRITER_WAVE_ROWS)
  if not observer: emit_profile_stamp(fw, PROFILE_NCRISC_OUTPUT)
  if not observer: emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB100, block_reg=R.S10, i0_reg=R.S9, i1_reg=R.S1)
  if not observer: emit_profile_accum_start(fw, PROFILE_TMP_NCRISC)
  from . import epilogue
  epilogue.writer(fw, plan)
  _output_wait_ready(fw)
  if not row_chunk:
    drain = fw._new_label('output_drain')
    fw.label(drain)
    output_pending(fw, R.T4)
    fw.bne(R.T4, R.ZERO, drain)
  fw.fence()
  if not observer: emit_progress_mark(fw, DEBUG_NCRISC_OUTPUT, 0xB1FF, block_reg=R.S10, i0_reg=R.S9, i1_reg=R.S1)
  if not observer: emit_profile_accum_end(fw, PROFILE_COUNTERS[2][1], PROFILE_TMP_NCRISC)
  if not observer: emit_profile_stamp(fw, PROFILE_NCRISC_OUTPUT + 8)
  finish(fw, plan, WRITER_WAVE_ROWS)
  if plan.n_passes > 1:
    fw.rta_ptr(NM.RTA_L1_BASE_PTR)
    fw.arg(R.T1, 19)
    if row_chunk:
      _move_plus_imm(fw, R.T1, R.T1, plan.out_subblock_h * plan.nt)
      if plan.pass_axis == 'n':
        # Once the previous pass is drained, return to the next N slice's first row.
        fw.read32(R.T2, PASS_BASE + 24)
        fw.li(R.T3, plan.per_core_m // plan.out_subblock_h - 1)
        more = fw._new_label('output_more_rows')
        fw.bne(R.T2, R.T3, more)
        _move_plus_imm(fw, R.T1, R.T1, plan.per_core_n - plan.per_core_m * plan.nt)
        fw.label(more)
    elif plan.pass_axis == 'm':
      _move_plus_imm(fw, R.T1, R.T1, plan.per_core_m * plan.nt)
    else:
      fw.addi(R.T1, R.T1, plan.per_core_n)
    fw.sw(R.T1, R.S11, 19 * 4)
  return fw


def emit_trisc0_unpack_row_reg(
  fw: MatmulTrisc,
  in0_tile_index,
  in1_tile_index,
  *,
  mop_loop_count: int = 1,
) -> MatmulTrisc:
    emit_profile_accum_start(fw, PROFILE_TMP_TRISC0, level=2)
    wait_unp = fw._new_label("wait_unpack_ctx")
    wait_unp_done = fw._new_label("wait_unpack_ctx_done")
    fw.label(wait_unp)
    fw.lw(R.T1, R.S7, 0)
    fw.andi(R.T1, R.T1, 0xFE)
    fw.beq(R.T1, R.ZERO, wait_unp_done)
    fw.fence()
    fw.j(wait_unp)
    fw.label(wait_unp_done)
    emit_profile_accum_end(fw, PROFILE_COUNTERS[4][1], PROFILE_TMP_TRISC0, level=2)

    if INPUT_DTYPE == DType.BF16:
      fw.slli(R.A0, in0_tile_index, 7)
      fw.add(R.A0, R.A0, R.S0)
      fw.addi(R.A0, R.A0, -1)
      fw.slli(R.A1, in1_tile_index, 7)
      fw.add(R.A1, R.A1, R.S1)
      fw.addi(R.A1, R.A1, -1)
    else:
      plan = fw.row_major_plan
      inner, row = fw.row_major_inner_row
      a_stride = plan.in0_block_w * input_page_bytes(plan.in0_block_w) // 16
      b_stride = plan.per_core_n * input_page_bytes(plan.per_core_n) // 16
      fw.li(R.T0, plan.out_subblock_h * a_stride)
      fw.mul(R.A0, R.S4, R.T0)
      fw.add(R.A0, R.A0, R.S0)
      _move_plus_imm(fw, R.A0, R.A0, row * a_stride + inner * 2 * INPUT_DTYPE.itemsize - 1)
      fw.li(R.T0, plan.out_subblock_w * 2 * INPUT_DTYPE.itemsize)
      fw.mul(R.A1, R.S5, R.T0)
      fw.add(R.A1, R.A1, R.S1)
      _move_plus_imm(fw, R.A1, R.A1, inner * b_stride - 1)

    fw.lw(R.T2, R.S11, 0)
    fw.mv(R.T3, R.A2)
    sec0_ctx_ready = fw._new_label("trisc0_sec0_ctx")
    fw.beq(R.T2, R.ZERO, sec0_ctx_ready)
    fw.addi(R.T3, R.T3, 4)
    fw.label(sec0_ctx_ready)
    fw.sw(R.A1, R.T3, 0)

    fw.mv(R.T3, R.A3)
    sec1_ctx_ready = fw._new_label("trisc0_sec1_ctx")
    fw.beq(R.T2, R.ZERO, sec1_ctx_ready)
    fw.addi(R.T3, R.T3, 4)
    fw.label(sec1_ctx_ready)
    fw.sw(R.A0, R.T3, 0)
    fw.sw(R.ZERO, R.S7, 0)

    fw.emit(TT.TTSTALLWAIT(Stall.UNPACK, Wait.TRISC_CFG))
    if INPUT_DTYPE == DType.BF16:
      fw.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 15))
      fw.emit(TT.TTUNPACR(1, OvrdThreadId=1, SetDatValid=1, Last=1))
    else:
      fw.emit(TT.TTSETADCXY(3, 0, 0, 0, 0, 10))
      for word in row_major_unpack_ops(1): fw.emit(word)
    ctx1 = fw._new_label("trisc0_mop_ctx1")
    ctx_done = fw._new_label("trisc0_mop_done")
    fw.bne(R.T2, R.ZERO, ctx1)
    fw.emit(TT.TTMOP(0, mop_loop_count, 0))
    fw.j(ctx_done)
    fw.label(ctx1)
    fw.emit(TT.TTMOP(0, mop_loop_count, 0xFF))
    fw.label(ctx_done)
    fw.emit(TT.TTSEMGET(Sem.mask(Sem.UNPACK_SYNC)))
    fw.li(R.T3, 1)
    fw.sub(R.T3, R.T3, R.T2)
    fw.sw(R.T3, R.S11, 0)
    ctx0 = fw._new_label("trisc0_ctx0")
    done = fw._new_label("trisc0_ctx_done")
    fw.beq(R.T2, R.ZERO, ctx0)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
    fw.j(done)
    fw.label(ctx0)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
    fw.label(done)
    return fw


def emit_trisc0_unpack_subblock_reg(
  fw: MatmulTrisc, plan: MatmulPlan, in0_offset, in1_offset,
  *, in0_block_base_tiles: int = 0, in1_block_base_tiles: int = 0,
) -> MatmulTrisc:
  fw.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  if INPUT_DTYPE == DType.BF16:
    fw.cb_wait_front(fw.data["cb_interface"], 2, plan.in0_block_num_tiles)
    fw.cb_wait_front(fw.data["cb_interface"], 3, plan.in1_block_num_tiles)
  fw.cb_read_ptr(fw.data["cb_interface"], 2 if INPUT_DTYPE == DType.BF16 else 0, out=R.S0)
  fw.cb_iface(fw.data["cb_interface"], 2 if INPUT_DTYPE == DType.BF16 else 0, out=R.T6)
  fw.lw(R.A4, R.T6, 8)
  fw.cb_read_ptr(fw.data["cb_interface"], 3 if INPUT_DTYPE == DType.BF16 else 1, out=R.S1)
  fw.cb_iface(fw.data["cb_interface"], 3 if INPUT_DTYPE == DType.BF16 else 1, out=R.T6)
  fw.lw(R.A5, R.T6, 8)
  for base, width in ((R.S0, plan.in0_block_w), (R.S1, plan.per_core_n)):
    if INPUT_DTYPE == DType.BF16 or width % 2 == 0: continue
    fw.slli(R.T0, base, 4)
    fw.lw(R.T1, R.T0, 0)
    fw.srli(R.T1, R.T1, 4)
    fw.add(base, base, R.T1)
  fw.li(R.S7, TensixRegs.PC_UNPACK_SYNC)
  fw.li(R.S11, TLM.TRISC0_UNPACK_CFG_CONTEXT)
  fw.li(R.A2, TensixRegs.CFG_BASE + THCON_SEC0_REG3_BASE_ADDR32 * 4)
  fw.li(R.A3, TensixRegs.CFG_BASE + THCON_SEC1_REG3_BASE_ADDR32 * 4)
  if batched_unpack(plan):
    return emit_trisc0_unpack_subblock_batched(fw, plan, in0_offset)
  m_reg = R.S4
  if plan.n_passes > 1 and plan.pass_axis == 'm':
    fw.read32(R.T0, pass_address(fw))
    fw.li(R.T1, plan.in0_num_subblocks)
    fw.mul(R.T0, R.T0, R.T1)
    fw.add(R.A6, R.S4, R.T0)
    m_reg = R.A6
  def skip_tail(reg, extent, block, offset, done):
    full, tail = divmod(extent, block)
    if tail and offset*32 >= tail:
      fw.li(R.T0, full)
      fw.bge(reg, R.T0, done)

  for inner in range(plan.in0_block_w):
    skip_inner = fw._new_label('unpack_skip_inner')
    skip_tail(R.S6, plan.k_extent, plan.in0_block_w*32, inner, skip_inner)
    _move_plus_imm(fw, R.S10, in1_offset, in1_block_base_tiles + inner*plan.in1_per_core_w)
    for row in range(plan.out_subblock_h):
      fw.row_major_inner_row = inner, row
      skip_row = fw._new_label('unpack_skip_row')
      skip_tail(m_reg, plan.m_extent, plan.out_subblock_h*32, row, skip_row)
      _move_plus_imm(fw, R.S9, in0_offset, in0_block_base_tiles + row*plan.in0_block_w + inner)
      full, tail = divmod(plan.n_extent, plan.out_subblock_w*32)
      tail_tiles = _ceil_div(tail,32)
      if tail and tail_tiles != plan.out_subblock_w:
        normal = fw._new_label('unpack_full_width')
        n_pass = plan.n_passes > 1 and plan.pass_axis == 'n'
        if n_pass:
          fw.read32(R.T0, pass_address(fw))
          fw.li(R.T1, plan.in1_num_subblocks)
          fw.mul(R.T0, R.T0, R.T1)
          fw.add(R.T2, R.S5, R.T0)
        fw.li(R.T0,full)
        fw.blt(R.T2 if n_pass else R.S5,R.T0,normal)
        emit_trisc0_unpack_row_reg(fw,R.S9,R.S10,mop_loop_count=tail_tiles-1)
        fw.j(skip_row)
        fw.label(normal)
      emit_trisc0_unpack_row_reg(fw,R.S9,R.S10,mop_loop_count=plan.out_subblock_w-1)
      fw.label(skip_row)
    fw.label(skip_inner)
  return fw

def emit_trisc0_unpack_subblock_batched(fw: MatmulTrisc, plan: MatmulPlan, in0_offset) -> MatmulTrisc:
  """Unpack a whole 1xW subblock (all K tiles of this block) with one MOP."""
  a_stride = plan.in0_block_w * input_page_bytes(plan.in0_block_w) // 16
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC0, level=2)
  wait, ready = fw._new_label("batched_ctx"), fw._new_label("batched_ctx_ready")
  fw.label(wait)
  fw.lw(R.T1, R.S7, 0)
  fw.andi(R.T1, R.T1, 0xFE)
  fw.beq(R.T1, R.ZERO, ready)
  fw.fence()
  fw.j(wait)
  fw.label(ready)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[4][1], PROFILE_TMP_TRISC0, level=2)
  # A: first K tile of this subblock row; B: first N tile of this subblock.
  fw.li(R.T0, a_stride)
  fw.mul(R.A0, R.S4, R.T0)
  fw.add(R.A0, R.A0, R.S0)
  fw.addi(R.A0, R.A0, -1)
  fw.slli(R.A1, R.S5, (plan.out_subblock_w * 2 * INPUT_DTYPE.itemsize).bit_length() - 1)
  fw.add(R.A1, R.A1, R.S1)
  fw.addi(R.A1, R.A1, -1)
  fw.lw(R.T2, R.S11, 0)
  fw.slli(R.T3, R.T2, 2)
  fw.add(R.T4, R.A2, R.T3)
  fw.sw(R.A1, R.T4, 0)
  fw.add(R.T4, R.A3, R.T3)
  fw.sw(R.A0, R.T4, 0)
  fw.sw(R.ZERO, R.S7, 0)
  fw.emit(TT.TTSTALLWAIT(Stall.UNPACK, Wait.TRISC_CFG))
  fw.emit(TT.TTSETADCXY(3, 0, 0, 0, 0, 0b1010))
  fw.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0b1111))
  # MOP counts: K tiles (outer, bits 19:10) and N tiles (inner, bits 9:0).
  kfull, ktail = divmod(plan.k_extent, plan.in0_block_w * 32)
  nfull, ntail = divmod(plan.n_extent, plan.out_subblock_w * 32)
  k_options = [(None, plan.in0_block_w)]
  if ktail and _ceil_div(ktail, 32) != plan.in0_block_w:
    k_options = [(kfull, _ceil_div(ktail, 32)), (None, plan.in0_block_w)]
  n_options = [(None, plan.out_subblock_w)]
  if ntail and _ceil_div(ntail, 32) != plan.out_subblock_w:
    n_options = [(nfull, _ceil_div(ntail, 32)), (None, plan.out_subblock_w)]
  n_pass = plan.n_passes > 1 and plan.pass_axis == 'n'
  if n_pass and len(n_options) > 1:
    fw.read32(R.T0, pass_address(fw))
    fw.li(R.T1, plan.in1_num_subblocks)
    fw.mul(R.T0, R.T0, R.T1)
    fw.add(R.T5, R.S5, R.T0)
  n_reg = R.T5 if n_pass else R.S5
  issued = fw._new_label("batched_mop_issued")
  for k_limit, k_count in k_options:
    k_next = fw._new_label("batched_k")
    if k_limit is not None:
      fw.li(R.T0, k_limit)
      fw.blt(R.S6, R.T0, k_next)
    for n_limit, n_count in n_options:
      n_next = fw._new_label("batched_n")
      if n_limit is not None:
        fw.li(R.T0, n_limit)
        fw.blt(n_reg, R.T0, n_next)
      fw.emit(TT.TTMOP(1, 0, k_count << 10 | n_count))
      fw.j(issued)
      fw.label(n_next)
    fw.label(k_next)
  fw.label(issued)
  fw.emit(TT.TTSEMGET(Sem.mask(Sem.UNPACK_SYNC)))
  fw.li(R.T3, 1)
  fw.sub(R.T3, R.T3, R.T2)
  fw.sw(R.T3, R.S11, 0)
  ctx0, done = fw._new_label("batched_ctx0"), fw._new_label("batched_ctx_done")
  fw.beq(R.T2, R.ZERO, ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.j(done)
  fw.label(ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
  fw.label(done)
  return fw


def _math_mop_cfg(plan: MatmulPlan) -> LoopTemplate:
  if use_row_mop() and INPUT_DTYPE == DType.BF16:
    return LoopTemplate(outer=plan.out_subblock_w, inner=FIDELITY,
                        loop=MOP_REPLAY(16, 16), last=MOP_REPLAY(16, 15),
                        outer_last=MOP_REPLAY(16, 15),
                        end0=TT.TTMVMUL(clear_dvalid=1, addr_mode=6))
  if use_row_mop():
    return LoopTemplate(outer=1, inner=plan.out_subblock_w,
                        loop=MOP_REPLAY(16, 15),
                        alternate=TT.TTMVMUL(clear_dvalid=1, addr_mode=5),
                        last=TT.TTMVMUL(clear_dvalid=1, addr_mode=6),
                        outer_last=TT.TTMVMUL(clear_dvalid=3, addr_mode=6))
  # HiFi4 retains both BF16 operands' low mantissa bits; FP8 is exact at 1.
  return replace(MATMUL_MATH_MOP_CFG, inner=FIDELITY)


def matmul_math_init(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  fw.write32(fw.data["dest_offset_id"], 0)
  fw.math._local_state(fw, DType.BF16)
  replay_load = MATMUL_MATH_REPLAY_LOAD
  mop_cfg = _math_mop_cfg(plan)
  matmul_math_addrmod_init(fw)
  fw.emit(TT.TTREPLAY(16, len(replay_load), 0, 1))
  for word in replay_load:
    fw.emit(word)
  fw.tensix_sync(1)
  fw.wait_mmio_low_byte_zero(TensixRegs.pc_buf_sem(Sem.MATH_PACK))
  fw.emit(TT.TTSEMINIT(sem_sel=Sem.mask(Sem.MATH_PACK), init_value=0, max_value=2))
  matmul_math_addrmod_init(fw)
  fw.emit(TT.TTREPLAY(16, len(replay_load), 0, 1))
  for word in replay_load:
    fw.emit(word)
  fw.write_mop_cfg(mop_cfg, 1)
  if INPUT_DTYPE == DType.BF16:
    fw.emit(TT.TTREPLAY(0, 9, 0, 1))
    for _ in range(8): fw.emit(TT.TTMOVA2D(instr_mod=2))
    fw.emit(TT.TTSETRWC(1, 0, 0, 0, 0, 1))
  fw.write32(MATH_THROTTLED_MOP_STATUS, 0)
  return fw


def matmul_math_addrmod_init(fw: MatmulTrisc) -> MatmulTrisc:
  for slot, fidelity in ((3, 1 << 13), (7, 1 << 15)):
    fw.setc16(12 + slot, 8 << 8 if slot == 7 else 0)
    fw.setc16(28 + slot, fidelity)
    fw.setc16(47 + slot, 0)
  # Sources contain consecutive 32x16 column panels; Dst retains four faces.
  # SrcA (B): N advances 32 rows, K advances 16. SrcB (A): M advances
  # 16 rows between output faces, then K advances to the next 32-row panel.
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC0_Src, 2048)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC0, 8)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC0_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC1_Src, 32 | (1 << 14))
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC1, 8)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC1_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC2_Src, (1 << 6) | (16 << 8) | (1 << 14))
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC2, 8)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC2_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC4_Src, 16 | (1 << 6) | (16 << 8) | (1 << 14))
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC4, 1024)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC4_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC5_Src, 49344)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC5, 11264)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC5_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC6_Src, 49344)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC6, 35840)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC6_Bias, 0)
  if use_row_mop():
    # Carry tracks the tile base; mode 4 returns to it halfway through a tile.
    fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC5, 64 | (1 << 10) | (1 << 15))
    fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC6, (1 << 11) | (1 << 15))
    if INPUT_DTYPE == DType.BF16:
      fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC5, (1 << 10) | (1 << 13))
      fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC6, 64 | (1 << 10) | (1 << 15))
  return fw.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))


def emit_math_dst_base_addr(fw: MatmulTrisc, out_reg=R.T1) -> MatmulTrisc:
  fw.read32(out_reg, fw.data["dest_offset_id"])
  fw.slli(out_reg, out_reg, 8)  # FP32 Dst half: 256 rows
  fw.li(R.T2, TT.TTSETC16(ThreadCfg.DEST_TARGET_REG_CFG_MATH_Offset, 0))  # base; addr bits added in
  fw.add(out_reg, out_reg, R.T2)
  return fw

def emit_math_subblock_body(fw: MatmulTrisc, plan: MatmulPlan) -> MatmulTrisc:
  emit_math_dst_base_addr(fw, R.T3)
  edge, done = fw._new_label('edge_subblock'), fw._new_label('subblock_done')
  for reg, extent, block in ((R.S4, plan.m_extent, plan.out_subblock_h*32),
                             (R.S5, plan.n_extent, plan.out_subblock_w*32),
                             (R.S6, plan.k_extent, plan.in0_block_w*32)):
    fw.li(R.T0, extent // block)
    fw.bge(reg, R.T0, edge)
  if use_row_mop():
    batch_k = INPUT_DTYPE == DType.FP8 and plan.out_subblock_h == 1
    for inner in range(1 if batch_k else plan.in0_block_w):
      for row in range(plan.out_subblock_h):
        fw.mv(R.T1, R.T3)
        if row:
          fw.addi(R.T1, R.T1, row * plan.out_subblock_w * 64)
        fw.write32(TensixRegs.INSTRN_BUF_BASE, R.T1)
        fw.emit(TT.TTMOP(1, 0, plan.in0_block_w << 10 if batch_k else 0))
        fw.emit(TT.TTSETRWC(2, 0, 0, 0, 0, 15))
    fw.j(done)
    fw.label(edge)
    from .edges import emit_subblock
    emit_subblock(fw, plan)
    fw.label(done)
    return fw
  tile_order = list(range(plan.out_subblock_num_tiles))
  for inner in range(plan.in0_block_w):
    for tile_index in tile_order:
      fw.mv(R.T1, R.T3)
      if tile_index:
        fw.addi(R.T1, R.T1, tile_index * 64)
      fw.write32(TensixRegs.INSTRN_BUF_BASE, R.T1)
      fw.emit(TT.TTMOP(1, 0, 0))
      if tile_index % plan.out_subblock_w == plan.out_subblock_w - 1:
        fw.emit(TT.TTSETRWC(2, 0, 0, 0, 0, 15))
  fw.j(done)
  fw.label(edge)
  from .edges import emit_subblock
  emit_subblock(fw, plan)
  fw.label(done)
  return fw

def emit_math_subblock_commit(fw: MatmulTrisc) -> MatmulTrisc:
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC1)
  fw.emit(TT.TTSTALLWAIT(Stall.SYNC, Wait.MATH | Wait.SFPU))
  fw.emit(TT.TTSEMPOST(Sem.mask(Sem.MATH_PACK)))
  emit_profile_accum_end(fw, PROFILE_COUNTERS[6][1], PROFILE_TMP_TRISC1)
  fw.read32(R.T1, fw.data["dest_offset_id"])
  fw.li(R.T2, 1)
  fw.sub(R.T2, R.T2, R.T1)
  fw.write32(fw.data["dest_offset_id"], R.T2)
  return fw.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.MATH | Wait.SFPU))


def emit_pack_tile_to_cb(fw: MatmulTrisc, plan: MatmulPlan, out_cb: int, *, fp32=None, tilize=False) -> MatmulTrisc:
  fp32 = True if fp32 is None else fp32
  tilize = tilize or INPUT_DTYPE == DType.BF16
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC2)
  fw.cb_reserve_back(fw.data["cb_interface"], out_cb, plan.out_subblock_num_tiles)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD132)
  fw.cb_write_ptr(fw.data["cb_interface"], out_cb, out=R.S0)
  fw.mv(R.S3, R.S0)
  fw.cb_iface(fw.data["cb_interface"], out_cb, out=R.T6)
  fw.lw(R.S4, R.T6, 8)
  fw.read32(R.T1, fw.data["dest_offset_id"])
  fw.li(R.T2, 0)
  pack_offset_ready = fw._new_label("pack_offset_ready")
  fw.beq(R.T1, R.ZERO, pack_offset_ready)
  fw.li(R.T2, 256 if fp32 else 512)
  fw.label(pack_offset_ready)
  # Earlier PACRs may still be reading Dst: order the Dst-offset change
  # behind them in the pack thread instead of storing from the RISC.
  fw.slli(R.T2, R.T2, 8)
  fw.li(R.T3, TT.TTSETDMAREG(0, 0, 0, 2 * PACK_DEST_OFFSET_GPR))
  fw.add(R.T2, R.T2, R.T3)
  fw.write32(TensixRegs.INSTRN_BUF_BASE, R.T2)
  fw.emit(TT.TTSETDMAREG(0, 0, 0, 2 * PACK_DEST_OFFSET_GPR + 1))
  fw.emit(TT.TTSTALLWAIT(Stall.CFG, WAIT_THCON_AND_PACK))
  for reg in (Cfg.DEST_TARGET_REG_CFG_PACK_SEC0, Cfg.DEST_TARGET_REG_CFG_PACK_SEC1,
              Cfg.DEST_TARGET_REG_CFG_PACK_SEC2, Cfg.DEST_TARGET_REG_CFG_PACK_SEC3):
    fw.emit(TT.TTWRCFG(PACK_DEST_OFFSET_GPR, 0, reg.addr32))
  fw.mv(R.S0, R.S3)
  fw.addi(R.S0, R.S0, -1)
  for tile_index in range(1 if tilize else plan.out_subblock_num_tiles):
    if tile_index:
      fw.add(R.S0, R.S0, R.S4)
    fw.emit(TT.TTSETADC(4, 0, 3, tile_index))
    fw.slli(R.T1, R.S0, 8)
    fw.li(R.T2, 0x00FFFF00)
    fw.and_(R.T1, R.T1, R.T2)
    fw.li(R.T2, TT.TTSETDMAREG(0, 0, 0, 24))  # SETDMAREG[24] base; low addr bits added in
    fw.add(R.T1, R.T1, R.T2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, R.T1)
    fw.srli(R.T1, R.S0, 16)
    fw.slli(R.T1, R.T1, 8)
    fw.li(R.T2, 0x00800000)
    fw.or_(R.T1, R.T1, R.T2)
    fw.li(R.T2, TT.TTSETDMAREG(0, 0, 0, 25))  # SETDMAREG[25] base; high addr bits added in
    fw.add(R.T1, R.T1, R.T2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, R.T1)
    # The packer latches its L1 destination when a PACR starts, so (as in
    # tt-metal's program_packer_destination) only THCON must drain here.
    fw.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.THCON))
    fw.emit(TT.TTWRCFG(12, 0, Cfg.THCON_SEC0_REG1_L1_Dest_addr.addr32))
    fw.srli(R.T1, R.S0, 16)
    fw.slli(R.T1, R.T1, 8)
    fw.li(R.T2, TT.TTSETDMAREG(0, 0, 0, 25))  # SETDMAREG[25] base; high addr bits added in
    fw.add(R.T1, R.T1, R.T2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, R.T1)
    fw.emit(TT.TTDMANOP())

    fw.emit(TT.TTMOP(1, 0, plan.out_subblock_num_tiles << 10 if tilize else 0))
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD133 + tile_index)
    fw.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
  fw.cb_push_back(fw.data["cb_interface"], out_cb, plan.out_subblock_num_tiles, tensix_received=True)
  # ZEROACC is a Matrix Unit instruction: gate MATH, not THCON, on the packer.
  fw.emit(TT.TTSTALLWAIT(Stall.MATH, Wait.PACK0))
  fw.read32(R.T1, fw.data["dest_offset_id"])
  fw.andi(R.T2, R.T1, 1)
  fw.li(R.T3, TT.TTZEROACC(2, int(fp32), 0, 1))  # ZEROACC base; dest-offset parity bit added in
  fw.add(R.T2, R.T2, R.T3)
  fw.write32(TensixRegs.INSTRN_BUF_BASE, R.T2)
  fw.emit(TT.TTSEMGET(Sem.mask(Sem.MATH_PACK)))
  fw.li(R.T2, 1)
  fw.sub(R.T2, R.T2, R.T1)
  fw.write32(fw.data["dest_offset_id"], R.T2)
  fw.emit(TT.TTDMANOP())
  fw.emit(TT.TTDMANOP())
  emit_profile_accum_end(fw, PROFILE_COUNTERS[8][1], PROFILE_TMP_TRISC2)
  return fw

def emit_pack_reconfig_l1_acc(fw: MatmulTrisc, enabled: bool) -> MatmulTrisc:
  disable_zero_flags = 0x04 if enabled else 0x00
  pack_l1_acc = 0x08 if enabled else 0x00
  fw.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.PACK0))
  regs = [
    (Cfg.THCON_SEC0_REG1_1, Cfg.THCON_SEC0_REG1_2),
    (Cfg.THCON_SEC0_REG8_1, Cfg.THCON_SEC0_REG8_2),
    (Cfg.THCON_SEC1_REG1_1, Cfg.THCON_SEC1_REG1_2),
    (Cfg.THCON_SEC1_REG8_1, Cfg.THCON_SEC1_REG8_2),
  ]
  for flags_reg, acc_reg in regs:
    fw.push_tensix(TT.TTRMWCIB0(Mask=0x04, Data=disable_zero_flags, CfgRegAddr=flags_reg.addr32))
    fw.push_tensix(TT.TTRMWCIB2(Mask=0x08, Data=pack_l1_acc, CfgRegAddr=acc_reg.addr32))
  return fw

def emit_pack_reconfig_l1_acc_for_partial_block(fw: MatmulTrisc, block_reg) -> MatmulTrisc:
  not_block0 = fw._new_label("pack_l1_acc_not_block0")
  done = fw._new_label("pack_l1_acc_done")
  fw.bne(block_reg, R.ZERO, not_block0)
  emit_pack_reconfig_l1_acc(fw, False)
  fw.j(done)
  fw.label(not_block0)
  if INPUT_DTYPE == DType.FP8:
    fw.li(R.T0, 1)
    fw.bne(block_reg, R.T0, done)
  emit_pack_reconfig_l1_acc(fw, True)
  fw.label(done)
  return fw

def matmul_trisc0(plan: MatmulPlan) -> MatmulTrisc:
  fw = MatmulTrisc(0)
  fw.row_major_plan = plan
  fw.prologue()
  fw.unpack.init(dtype=INPUT_DTYPE, tile_bytes=INPUT_TILE_BYTES, mop_cfg=unpack_mop_cfg(plan))
  fw.emit(TT.TTSETADCXX(1, 1023, 0))
  fw.emit(TT.TTSETADCXX(2, 1023, 0))
  fw.push_tensix(TT.TTRMWCIB3(Mask=0x20, Data=0x20, CfgRegAddr=Cfg.ALU.addr32))  # FP32 Dst
  if INPUT_DTYPE == DType.FP8: row_major_unpack_config(fw, plan)
  _emit_trisc0_unpack_replay_init(fw, plan)
  fw.emit(TT.TTSEMINIT(sem_sel=Sem.mask(Sem.UNPACK_SYNC), init_value=0, max_value=2))
  epilogue.init(fw)
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC0)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE000)
  pass_loop = begin_passes(fw, plan)
  fw.li(R.S6, 0)
  fw.li(R.S8, plan.num_blocks)
  block_loop = fw._new_label("trisc0_block_loop")
  block_done = fw._new_label("trisc0_block_done")
  fw.label(block_loop)
  _jump_if_equal(fw, R.S6, R.S8, block_done, "trisc0_block_body")
  prepare_block(fw, plan)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE100)
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC0)
  if INPUT_DTYPE == DType.FP8:
    fw.cb_wait_front(fw.data["cb_interface"], 0, plan.in0_block_num_tiles)
    fw.cb_wait_front(fw.data["cb_interface"], 1, plan.in1_block_num_tiles)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE110)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[3][1], PROFILE_TMP_TRISC0)

  fw.li(R.S4, 0)
  i0_loop = fw._new_label("trisc0_i0_loop")
  i0_done = fw._new_label("trisc0_i0_done")
  fw.label(i0_loop)
  fw.li(R.T0, plan.in0_num_subblocks)
  _jump_if_ge(fw, R.S4, R.T0, i0_done, "trisc0_i0_body")
  fw.li(R.S5, 0)
  i1_loop = fw._new_label("trisc0_i1_loop")
  i1_done = fw._new_label("trisc0_i1_done")
  fw.label(i1_loop)
  fw.li(R.T0, plan.in1_num_subblocks)
  _jump_if_ge(fw, R.S5, R.T0, i1_done, "trisc0_i1_body")
  fw.li(R.T0, plan.in0_subblock_num_tiles)
  fw.mul(R.S2, R.S4, R.T0)
  fw.li(R.T0, plan.out_subblock_w)
  fw.mul(R.S3, R.S5, R.T0)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE140)
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC0_SUB)
  emit_trisc0_unpack_subblock_reg(fw, plan, R.S2, R.S3)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[12][1], PROFILE_TMP_TRISC0_SUB)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE141)
  fw.addi(R.S5, R.S5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(R.S4, R.S4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)
  # Final L1 accumulation releases every intermediate CB24 block.
  if plan.num_blocks > 1:
    skip_partial_pop = fw._new_label("trisc0_skip_partial_pop")
    fw.li(R.T0, plan.num_blocks - 1)
    fw.bge(R.S6, R.T0, skip_partial_pop)
    fw.read32(R.T1, CBRegs.SYNC_TILES_RECEIVED_BASE + 24 * CBRegs.SYNC_STRIDE)
    fw.write32(PASS_BASE + 128, R.T1)
    fw.read32(R.T1, CBRegs.SYNC_TILES_ACKED_BASE + 24 * CBRegs.SYNC_STRIDE)
    fw.write32(PASS_BASE + 132, R.T1)
    fw.cb_wait_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
    fw.cb_pop_front(fw.data["cb_interface"], 24, plan.out_block_num_tiles)
    fw.label(skip_partial_pop)
  if INPUT_DTYPE == DType.BF16:
    fw.tensix_sync(0)
    fw.cb_pop_front(fw.data["cb_interface"], 2, plan.in0_block_num_tiles)
    fw.cb_pop_front(fw.data["cb_interface"], 3, plan.in1_block_num_tiles)
  if INPUT_DTYPE == DType.FP8:
    fw.cb_pop_front(fw.data["cb_interface"], 0, plan.in0_block_num_tiles, tensix_ack=True)
    fw.cb_pop_front(fw.data["cb_interface"], 1, plan.in1_block_num_tiles, tensix_ack=True)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE1FF)
  fw.addi(R.S6, R.S6, 1)
  fw.j(block_loop)
  fw.label(block_done)
  epilogue.trisc0(fw, plan)
  emit_progress_mark(fw, DEBUG_TRISC0, 0xE2FF)
  end_passes(fw, plan, pass_loop)
  emit_profile_stamp(fw, PROFILE_TRISC0 + 8)
  return fw.ret_kernel()

def matmul_trisc1(plan: MatmulPlan) -> MatmulTrisc:
  fw = MatmulTrisc(1)
  fw.prologue()
  matmul_math_init(fw, plan)
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC1)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF000)
  pass_loop = begin_passes(fw, plan)
  fw.li(R.S6, 0)
  fw.li(R.S8, plan.num_blocks)
  block_loop = fw._new_label("trisc1_block_loop")
  block_done = fw._new_label("trisc1_block_done")
  fw.label(block_loop)
  _jump_if_equal(fw, R.S6, R.S8, block_done, "trisc1_block_body")
  prepare_block(fw, plan)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF100)
  fw.li(R.S4, 0)
  i0_loop = fw._new_label("trisc1_i0_loop")
  i0_done = fw._new_label("trisc1_i0_done")
  fw.label(i0_loop)
  fw.li(R.T0, plan.in0_num_subblocks)
  _jump_if_ge(fw, R.S4, R.T0, i0_done, "trisc1_i0_body")
  fw.li(R.S5, 0)
  i1_loop = fw._new_label("trisc1_i1_loop")
  i1_done = fw._new_label("trisc1_i1_done")
  fw.label(i1_loop)
  fw.li(R.T0, plan.in1_num_subblocks)
  _jump_if_ge(fw, R.S5, R.T0, i1_done, "trisc1_i1_body")
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC1)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF110)
  fw.emit(TT.TTSEMWAIT(
    STALL_MATH_PACK_ROOM,
    Sem.mask(Sem.MATH_PACK),
    SemWait.STALL_ON_MAX,
  ))
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF111)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[5][1], PROFILE_TMP_TRISC1)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF140)
  pass_reg, pass_count = (R.S4, plan.in0_num_subblocks) if plan.pass_axis == 'm' else (R.S5, plan.in1_num_subblocks)
  if plan.n_passes > 1:
    fw.read32(R.T0, pass_address(fw))
    fw.li(R.T1, pass_count)
    fw.mul(R.T0, R.T0, R.T1)
    fw.add(pass_reg, pass_reg, R.T0)
  emit_math_subblock_body(fw, plan)
  if plan.n_passes > 1:
    fw.read32(R.T0, pass_address(fw))
    fw.li(R.T1, pass_count)
    fw.mul(R.T0, R.T0, R.T1)
    fw.sub(pass_reg, pass_reg, R.T0)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF141)
  emit_math_subblock_commit(fw)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF150)
  fw.addi(R.S5, R.S5, 1)
  fw.j(i1_loop)
  fw.label(i1_done)
  fw.addi(R.S4, R.S4, 1)
  fw.j(i0_loop)
  fw.label(i0_done)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF1FF)
  fw.addi(R.S6, R.S6, 1)
  fw.j(block_loop)
  fw.label(block_done)
  emit_progress_mark(fw, DEBUG_TRISC1, 0xF2FF)
  end_passes(fw, plan, pass_loop)
  emit_profile_stamp(fw, PROFILE_TRISC1 + 8)
  finish = fw._new_label('finish_math')
  fw.j(finish)
  from .edges import emit_functions
  emit_functions(fw, plan)
  fw.label(finish)
  return fw.ret_kernel()

def matmul_trisc2(plan: MatmulPlan) -> MatmulTrisc:
  fw = MatmulTrisc(2)
  fw.prologue()
  fw.pack.init(dtype=OUTPUT_DTYPE, out_cb=16, mop_cfg=matmul_pack_mop_cfg())
  fw.init_barrier()
  emit_profile_stamp(fw, PROFILE_TRISC2)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD000)
  pass_loop = begin_passes(fw, plan)
  num_subblocks = plan.in0_num_subblocks * plan.in1_num_subblocks
  if plan.num_blocks > 1:
    fw.li(R.S6, 0)
    partial_block_loop = fw._new_label("trisc2_partial_block_loop")
    partial_block_done = fw._new_label("trisc2_partial_block_done")
    fw.label(partial_block_loop)
    fw.li(R.T0, plan.num_blocks - 1)
    _jump_if_ge(fw, R.S6, R.T0, partial_block_done, "trisc2_partial_block_body")
    prepare_block(fw, plan)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD100, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
    emit_pack_reconfig_l1_acc_for_partial_block(fw, R.S6)
    fw.li(R.S5, 0)
    partial_sb_loop = fw._new_label("trisc2_partial_sb_loop")
    partial_sb_done = fw._new_label("trisc2_partial_sb_done")
    fw.label(partial_sb_loop)
    fw.li(R.T0, num_subblocks)
    _jump_if_ge(fw, R.S5, R.T0, partial_sb_done, "trisc2_partial_sb_body")
    emit_profile_accum_start(fw, PROFILE_TMP_TRISC2)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD120, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
    fw.emit(TT.TTSEMWAIT(
      STALL_MATH_PACK_DATA,
      Sem.mask(Sem.MATH_PACK),
      SemWait.STALL_ON_ZERO,
    ))
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD121, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
    emit_profile_accum_end(fw, PROFILE_COUNTERS[7][1], PROFILE_TMP_TRISC2)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD130, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
    emit_pack_tile_to_cb(fw, plan, 24)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD131, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
    fw.addi(R.S5, R.S5, 1)
    fw.j(partial_sb_loop)
    fw.label(partial_sb_done)
    emit_progress_mark(fw, DEBUG_TRISC2, 0xD1FF, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
    fw.addi(R.S6, R.S6, 1)
    fw.j(partial_block_loop)
    fw.label(partial_block_done)

  fw.li(R.S6, plan.num_blocks - 1)
  prepare_block(fw, plan)
  fw.li(R.S5, 0)
  final_sb_loop = fw._new_label("trisc2_final_sb_loop")
  final_sb_done = fw._new_label("trisc2_final_sb_done")
  fw.label(final_sb_loop)
  fw.li(R.T0, num_subblocks)
  _jump_if_ge(fw, R.S5, R.T0, final_sb_done, "trisc2_final_sb_body")
  emit_profile_accum_start(fw, PROFILE_TMP_TRISC2)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD220, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
  fw.emit(TT.TTSEMWAIT(
    STALL_MATH_PACK_DATA,
    Sem.mask(Sem.MATH_PACK),
    SemWait.STALL_ON_ZERO,
  ))
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD221, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
  emit_profile_accum_end(fw, PROFILE_COUNTERS[7][1], PROFILE_TMP_TRISC2)
  # Optionally include the final block directly in the L1 partials.
  emit_pack_reconfig_l1_acc(fw, plan.num_blocks > 1)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD230, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
  emit_pack_tile_to_cb(fw, plan, 16)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD231, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
  fw.addi(R.S5, R.S5, 1)
  fw.j(final_sb_loop)
  fw.label(final_sb_done)
  epilogue.trisc2(fw, plan)
  emit_progress_mark(fw, DEBUG_TRISC2, 0xD2FF, block_reg=R.S6, i0_reg=R.S5, i1_reg=R.S5)
  end_passes(fw, plan, pass_loop)
  emit_profile_stamp(fw, PROFILE_TRISC2 + 8)
  return fw.ret_kernel()


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

def validate(a_ref: np.ndarray, b_ref: np.ndarray, c_raw: bytes, M: int, N: int, Mp: int, Np: int, *, full=False) -> tuple[float, float]:
  c_full = from_bf16_device_bytes(c_raw, (Mp, Np))   # RESULT_DTYPE: BF16
  c_got = c_full[:M, :N]
  got_full = c_got.reshape(-1)
  if not np.all(np.isfinite(got_full)):
    bad = int(got_full.size - np.count_nonzero(np.isfinite(got_full)))
    raise AssertionError(f"validation failed: {bad} non-finite outputs")

  sample_rows, sample_cols = sample_coords(M, N)
  if full or M * N <= 1_000_000 or os.environ.get("MATMUL_VALIDATE_FULL", "0") == "1":
    ref = (a_ref @ b_ref).reshape(-1)
    got = c_got.reshape(-1)
  else:
    ref = np.einsum('ij,ji->i', a_ref[sample_rows], b_ref[:, sample_cols])
    got = c_got[sample_rows, sample_cols]

  rel_l2 = float(np.linalg.norm(got - ref) / (np.linalg.norm(ref) + 1e-12))
  max_abs = float(np.max(np.abs(got - ref)))
  ref_std = float(np.std(ref))
  if ref_std < 1e-12:
    pcc = 1.0 if max_abs < 1e-6 else 0.0
  else:
    pcc = float(np.corrcoef(ref, got)[0, 1])
  # The BF16 result rounding alone contributes ~1.1e-3 relative L2. Exact
  # products (FP8 at one phase, BF16 at HiFi4) add only FP32 summation error;
  # fewer BF16 phases drop low mantissa bits of one operand (~3.5e-3 more).
  exact = INPUT_DTYPE == DType.FP8 or FIDELITY == 4
  error_limit = 0.002 if exact else 0.01
  if not np.isfinite(pcc) or not np.isfinite(rel_l2) or pcc < PCC_THRESHOLD or rel_l2 > error_limit:
    raise AssertionError(f"validation failed: PCC={pcc:.6f}, rel_l2={rel_l2:.6f}")
  return pcc, rel_l2

def tflops(m: int, n: int, k: int, us: float) -> float:
  return (2.0 * m * n * k) / (us * 1.0e6) if us > 0 else 0.0
