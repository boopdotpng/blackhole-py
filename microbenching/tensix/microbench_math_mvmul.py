#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import statistics
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
import matmul_peak as matmul

from asm import KernelBase
from device import Device
from dsl import (
  TTMOP, TTMVMUL, TTNOP, TTREPLAY, TTSEMGET, TTSEMINIT, TTSEMPOST, TTSETRWC,
  TTSEMWAIT, TTSETADCXX, TTSETADCZW, TTSTALLWAIT,
  a0, a1, a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk.debug import DebugRange
from ttk.cb import CB
from ttk.mailbox import TriscLocalMem as TLM
from ttk.tensix import Cfg, MopCfg, TensixL1, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait, ThreadCfg


AICLK_MHZ = 800.0
RESULT_BASE = 0x12D000
CONTROL_BASE = RESULT_BASE + 0x1000
READY_FLAG = CONTROL_BASE + 0x00
PRODUCED_COUNT = CONTROL_BASE + 0x04
MATH_DONE_COUNT = CONTROL_BASE + 0x08
PACK_DONE_COUNT = CONTROL_BASE + 0x0C
DEBUG_TRISC0 = CONTROL_BASE + 0x10
DEBUG_TRISC1 = CONTROL_BASE + 0x20
DEBUG_TRISC2 = CONTROL_BASE + 0x30
HEADER_WORDS = 16
RECORD_WORDS = 20
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x4D564D48  # "HMVM"
RECORD_MAGIC = 0x4D564D52  # "RMVM"
STATUS_STARTED = 0x4D560001
STATUS_DONE = 0x4D56D00D
OUT_CB = 0
OUT_CB_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
SCRATCH_A = TensixL1.DATA_BUFFER_SPACE_BASE + 0x90000
SCRATCH_B = SCRATCH_A + 0x20000
THCON_SEC0_REG3 = TensixRegs.CFG_BASE + matmul.THCON_SEC0_REG3_BASE_ADDR32 * 4
THCON_SEC1_REG3 = TensixRegs.CFG_BASE + matmul.THCON_SEC1_REG3_BASE_ADDR32 * 4

METHOD_ISSUE = 0
METHOD_LATENCY = 1
METHOD_THROUGHPUT = 2
METHOD_BASELINE = 3
METHOD_NAMES = {
  METHOD_ISSUE: "issue",
  METHOD_LATENCY: "latency",
  METHOD_THROUGHPUT: "throughput",
  METHOD_BASELINE: "baseline",
}

VARIANT_THROTTLE0 = 0
VARIANT_THROTTLED = 1
VARIANT_NAMES = {
  VARIANT_THROTTLE0: "throttle0",
  VARIANT_THROTTLED: "throttled",
}


@dataclass(frozen=True)
class BenchSpec:
  name: str
  method: int
  out_h: int
  out_w: int
  variant: int = VARIANT_THROTTLE0
  dtype: Dtype = Dtype.Float16_b
  instr_mod19: int = 0

  @property
  def output_tiles(self) -> int:
    return self.out_h * self.out_w

  @property
  def shape(self) -> str:
    return "none" if self.output_tiles == 0 else f"{self.out_h}x{self.out_w}"

  @property
  def mvmuls_per_iter(self) -> int:
    if self.output_tiles == 0:
      return 0
    per_tile = 16 if self.variant == VARIANT_THROTTLE0 else 6
    return self.output_tiles * per_tile

  @property
  def tile_bytes(self) -> int:
    return self.dtype.tile_size


SPECS = (
  BenchSpec("empty", METHOD_BASELINE, 0, 0),
  BenchSpec("mvmul_issue", METHOD_ISSUE, 1, 1),
  BenchSpec("mvmul_latency", METHOD_LATENCY, 1, 1),
  BenchSpec("mvmul_throughput", METHOD_THROUGHPUT, 1, 1),
  BenchSpec("subblock2x2_issue", METHOD_ISSUE, 2, 2),
  BenchSpec("subblock2x2_latency", METHOD_LATENCY, 2, 2),
  BenchSpec("subblock2x2_throughput", METHOD_THROUGHPUT, 2, 2),
)


@dataclass(frozen=True)
class Record:
  test_id: int
  name: str
  method: int
  shape: str
  variant: int
  iterations: int
  output_tiles: int
  mvmuls_per_iter: int
  dtype: Dtype
  instr_mod19: int
  start: int
  end: int
  cycles: int
  produced: int
  packed: int
  sink: int

  @property
  def cycles_per_iter(self) -> float:
    return self.cycles / self.iterations


def result_size() -> int:
  return HEADER_SIZE + RECORD_SIZE


def debug_ranges() -> tuple[DebugRange, ...]:
  return (
    DebugRange(0, "l1", RESULT_BASE, result_size(), "math_mvmul_microbench_results"),
    DebugRange(1, "l1", CONTROL_BASE, 64, "math_mvmul_microbench_control"),
  )


def tiny_plan(out_h: int, out_w: int, *, cb16_pages: int) -> matmul.MatmulPlan:
  tiles = max(1, out_h * out_w)
  return matmul.MatmulPlan(
    rows=(out_h or 1,), cols=(out_w or 1,), mt=out_h or 1, kt=1, nt=out_w or 1,
    per_core_m=out_h or 1, per_core_n=out_w or 1, in0_block_w=1, num_blocks=1,
    out_subblock_h=out_h or 1, out_subblock_w=out_w or 1,
    in0_num_subblocks=1, in1_num_subblocks=1,
    in0_block_num_tiles=max(1, out_h), in0_subblock_num_tiles=max(1, out_h),
    in1_block_num_tiles=max(1, out_w), in1_per_core_w=max(1, out_w),
    out_subblock_num_tiles=tiles, out_block_num_tiles=tiles,
    cb0_pages=tiles, cb1_pages=tiles, cb16_pages=cb16_pages, cb24_pages=tiles,
  )


def mvmul_instr(*, addr_mode: int = 0, instr_mod19: int = 0):
  return TTMVMUL(instr_mod19=instr_mod19, addr_mode=addr_mode)


def math_replay_load(spec: BenchSpec) -> list:
  if spec.variant == VARIANT_THROTTLE0:
    return [
      mvmul_instr(instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=1, instr_mod19=spec.instr_mod19),
      mvmul_instr(instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=2, instr_mod19=spec.instr_mod19),
      mvmul_instr(instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=1, instr_mod19=spec.instr_mod19),
      mvmul_instr(instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=4, instr_mod19=spec.instr_mod19),
      mvmul_instr(instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=1, instr_mod19=spec.instr_mod19),
      mvmul_instr(instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=2, instr_mod19=spec.instr_mod19),
      mvmul_instr(instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=1, instr_mod19=spec.instr_mod19),
      mvmul_instr(instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=5, instr_mod19=spec.instr_mod19),
    ]
  return [
    TTNOP(), TTNOP(), mvmul_instr(instr_mod19=spec.instr_mod19),
    TTNOP(), TTNOP(), mvmul_instr(addr_mode=1, instr_mod19=spec.instr_mod19),
    TTNOP(), TTNOP(), mvmul_instr(instr_mod19=spec.instr_mod19),
    TTNOP(), TTNOP(),
  ]


def math_mop_cfg(spec: BenchSpec) -> MopCfg:
  if spec.variant == VARIANT_THROTTLE0:
    return matmul.MATMUL_MATH_MOP_CFG_THROTTLE0
  return MopCfg(
    loop_outer=2, loop_inner=2,
    template=[
      TTNOP(), TTNOP(), TTNOP(),
      TTREPLAY(16, 11),
      mvmul_instr(addr_mode=2, instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=5, instr_mod19=spec.instr_mod19),
      mvmul_instr(addr_mode=4, instr_mod19=spec.instr_mod19),
    ],
  )


def active_iterations(spec: BenchSpec, requested: int) -> int:
  if spec.method == METHOD_LATENCY:
    return 1
  return requested


def emit_header(fw: KernelBase, *, test_id: int, iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, test_id, len(SPECS), status, iterations, RESULT_BASE, result_size(),
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_record(
  fw: KernelBase,
  *,
  test_id: int,
  spec: BenchSpec,
  iterations: int,
  start_lo,
  start_hi,
  end_lo,
  end_hi,
):
  fw.li(s2, RESULT_BASE + HEADER_SIZE)
  for off, value in enumerate((
    RECORD_MAGIC,
    test_id,
    spec.method,
    spec.variant,
    iterations,
    spec.out_h,
    spec.out_w,
    spec.output_tiles,
    spec.mvmuls_per_iter,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi), start=9):
    fw.sw(reg, s2, off * 4)
  fw.read32(t0, PRODUCED_COUNT)
  fw.sw(t0, s2, 13 * 4)
  fw.read32(t0, PACK_DONE_COUNT)
  fw.sw(t0, s2, 14 * 4)
  fw.li(t0, 0x4D560000 | test_id)
  fw.sw(t0, s2, 15 * 4)
  fw.li(t0, spec.dtype.value)
  fw.sw(t0, s2, 16 * 4)
  fw.li(t0, spec.instr_mod19)
  fw.sw(t0, s2, 17 * 4)
  fw.sw(zero, s2, 18 * 4)
  fw.sw(zero, s2, 19 * 4)
  return fw


def emit_wait_eq(fw: KernelBase, addr: int, value: int, *, ptr=t6, tmp=t5):
  loop = fw._new_label("wait_eq")
  done = fw._new_label("wait_eq_done")
  fw.li(ptr, addr)
  fw.li(t4, value)
  fw.label(loop)
  fw.lw(tmp, ptr, 0)
  fw.beq(tmp, t4, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  return fw


def emit_wait_counter_gt(fw: KernelBase, addr: int, current_reg, *, ptr=t6, tmp=t5):
  loop = fw._new_label("wait_counter_gt")
  done = fw._new_label("wait_counter_gt_done")
  fw.li(ptr, addr)
  fw.label(loop)
  fw.lw(tmp, ptr, 0)
  fw.bltu(current_reg, tmp, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  return fw


def emit_inc_word(fw: KernelBase, addr: int, *, ptr=t6, tmp=t5):
  fw.li(ptr, addr)
  fw.lw(tmp, ptr, 0)
  fw.addi(tmp, tmp, 1)
  fw.sw(tmp, ptr, 0)
  return fw.fence()


def emit_mark(fw: KernelBase, addr: int, code: int):
  fw.li(t0, code)
  fw.write32(addr, t0, tmp_addr=t1)
  return fw.fence()


def emit_unpack_setup(fw: matmul.MatmulTrisc, plan: matmul.MatmulPlan, spec: BenchSpec):
  fw.unpack.init(dtype=spec.dtype, tile_bytes=spec.tile_bytes, mop_cfg=matmul.MATMUL_UNPACK_AB_MOP_CFG)
  fw.emit(TTSETADCXX(1, 1023, 0))
  fw.emit(TTSETADCXX(2, 1023, 0))
  matmul._emit_trisc0_unpack_replay_init(fw, plan)
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.UNPACK_SYNC), init_value=0, max_value=2))
  fw.tensix_sync(0)
  fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, 0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.li(s0, SCRATCH_A)
  fw.li(s1, SCRATCH_B)
  fw.li(a4, spec.tile_bytes)
  fw.li(a5, spec.tile_bytes)
  fw.li(s7, TensixRegs.PC_UNPACK_SYNC)
  fw.li(s11, TLM.TRISC0_UNPACK_CFG_CONTEXT)
  fw.li(s4, THCON_SEC0_REG3)
  fw.li(s5, THCON_SEC1_REG3)
  return fw


def emit_wait_pc_unpack_ready(fw: matmul.MatmulTrisc):
  wait = fw._new_label("wait_unpack_ctx")
  done = fw._new_label("wait_unpack_ctx_done")
  fw.label(wait)
  fw.lw(t1, s7, 0)
  fw.andi(t1, t1, 0xFE)
  fw.beq(t1, zero, done)
  fw.fence()
  fw.j(wait)
  fw.label(done)
  return fw


def emit_unpack_row(fw: matmul.MatmulTrisc, in0_index, in1_index, *, mop_loop_count: int):
  emit_mark(fw, DEBUG_TRISC0, 0xE101)
  emit_wait_pc_unpack_ready(fw)
  emit_mark(fw, DEBUG_TRISC0, 0xE102)
  fw.mul(a0, in0_index, a4)
  fw.add(a0, a0, s0)
  fw.addi(a0, a0, -1)
  fw.mul(a1, in1_index, a5)
  fw.add(a1, a1, s1)
  fw.addi(a1, a1, -1)

  fw.lw(t2, s11, 0)
  fw.mv(t3, s4)
  sec0_ready = fw._new_label("sec0_ready")
  fw.beq(t2, zero, sec0_ready)
  fw.addi(t3, t3, 4)
  fw.label(sec0_ready)
  fw.sw(a1, t3, 0)

  fw.mv(t3, s5)
  sec1_ready = fw._new_label("sec1_ready")
  fw.beq(t2, zero, sec1_ready)
  fw.addi(t3, t3, 4)
  fw.label(sec1_ready)
  fw.sw(a0, t3, 0)
  fw.sw(zero, s7, 0)

  emit_mark(fw, DEBUG_TRISC0, 0xE103)
  fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
  emit_mark(fw, DEBUG_TRISC0, 0xE104)
  fw.emit(matmul.MATMUL_UNPACK_SRCB_LOAD)
  ctx1 = fw._new_label("unpack_mop_ctx1")
  ctx_done = fw._new_label("unpack_mop_done")
  fw.bne(t2, zero, ctx1)
  fw.emit(TTMOP(0, mop_loop_count, 0))
  fw.j(ctx_done)
  fw.label(ctx1)
  fw.emit(TTMOP(0, mop_loop_count, 0xFF))
  fw.label(ctx_done)
  emit_mark(fw, DEBUG_TRISC0, 0xE105)
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
  emit_mark(fw, DEBUG_TRISC0, 0xE106)
  fw.li(t3, 1)
  fw.sub(t3, t3, t2)
  fw.sw(t3, s11, 0)
  ctx0 = fw._new_label("unpack_ctx0")
  done = fw._new_label("unpack_ctx_done")
  fw.beq(t2, zero, ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.j(done)
  fw.label(ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
  fw.label(done)
  return fw


def emit_unpack_subblock(fw: matmul.MatmulTrisc, spec: BenchSpec):
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  mop_loop_count = max(0, spec.out_w - 1)
  for row in range(spec.out_h):
    fw.li(s9, row)
    fw.li(s10, 0)
    emit_unpack_row(fw, s9, s10, mop_loop_count=mop_loop_count)
  return fw


def emit_math_init(fw: matmul.MatmulTrisc, spec: BenchSpec):
  emit_mark(fw, DEBUG_TRISC1, 0xF010)
  fw.math._local_state(fw, spec.dtype)
  emit_mark(fw, DEBUG_TRISC1, 0xF011)
  replay_load = math_replay_load(spec)
  mop_cfg = math_mop_cfg(spec)
  matmul.matmul_math_addrmod_init(fw)
  fw.emit(TTREPLAY(16, len(replay_load), 0, 1))
  for word in replay_load:
    fw.emit(word)
  fw.tensix_sync(1)
  fw.wait_mmio_low_byte_zero(TensixRegs.pc_buf_sem(TensixSem.MATH_PACK))
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.MATH_PACK), init_value=0, max_value=2))
  matmul.matmul_math_addrmod_init(fw)
  fw.emit(TTREPLAY(16, len(replay_load), 0, 1))
  for word in replay_load:
    fw.emit(word)
  fw.write_mop_cfg(mop_cfg, 1)
  emit_mark(fw, DEBUG_TRISC1, 0xF012)
  return fw


def emit_math_body(fw: matmul.MatmulTrisc, spec: BenchSpec):
  emit_mark(fw, DEBUG_TRISC1, 0xF101)
  matmul.emit_math_dst_base_addr(fw, t3)
  for tile_index in range(spec.output_tiles):
    fw.mv(t1, t3)
    if tile_index:
      fw.addi(t1, t1, tile_index * 64)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    if spec.variant == VARIANT_THROTTLE0:
      fw.emit(TTMOP(1, 0, 0))
      if tile_index % spec.out_w == spec.out_w - 1:
        fw.emit(TTSETRWC(2, 0, 0, 0, 0, 15))
    else:
      fw.emit(TTMOP(1, 0, 0))
      fw.emit(TTMOP(1, 0, 0))
      fw.emit(TTSETRWC(1, 0, 0, 0, 0, 15))
      if tile_index % spec.out_w == spec.out_w - 1:
        fw.emit(TTSETRWC(2, 0, 0, 0, 0, 15))
  emit_mark(fw, DEBUG_TRISC1, 0xF102)
  return fw


def emit_math_commit(fw: matmul.MatmulTrisc):
  emit_mark(fw, DEBUG_TRISC1, 0xF201)
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  emit_mark(fw, DEBUG_TRISC1, 0xF202)
  fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_PACK)))
  emit_mark(fw, DEBUG_TRISC1, 0xF203)
  fw.tensix_sync(1)
  emit_mark(fw, DEBUG_TRISC1, 0xF204)
  fw.read32(t1, fw.data["dest_offset_id"])
  fw.li(t2, 1)
  fw.sub(t2, t2, t1)
  fw.write32(fw.data["dest_offset_id"], t2)
  emit_mark(fw, DEBUG_TRISC1, 0xF205)
  return fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.MATH | TensixWait.SFPU))


def build_trisc0(spec: BenchSpec, iterations: int, plan: matmul.MatmulPlan) -> KernelBase:
  if spec.method == METHOD_BASELINE:
    return build_idle_trisc(0)
  fw = matmul.MatmulTrisc(0)
  fw.prologue()
  emit_mark(fw, DEBUG_TRISC0, 0xE000)
  emit_unpack_setup(fw, plan, spec)
  emit_mark(fw, DEBUG_TRISC0, 0xE010)
  fw.init_barrier()
  emit_mark(fw, DEBUG_TRISC0, 0xE020)
  fw.li(s8, iterations)
  loop = fw._new_label("produce_loop")
  done = fw._new_label("produce_done")
  fw.label(loop)
  fw.beq(s8, zero, done)
  emit_mark(fw, DEBUG_TRISC0, 0xE100)
  emit_unpack_subblock(fw, spec)
  emit_mark(fw, DEBUG_TRISC0, 0xE110)
  emit_inc_word(fw, PRODUCED_COUNT)
  fw.addi(s8, s8, -1)
  fw.j(loop)
  fw.label(done)
  emit_mark(fw, DEBUG_TRISC0, 0xEFFF)
  return fw.ret_kernel()


def build_trisc1(spec: BenchSpec, test_id: int, iterations: int) -> KernelBase:
  fw = matmul.MatmulTrisc(1)
  fw.prologue()
  emit_mark(fw, DEBUG_TRISC1, 0xF000)
  emit_header(fw, test_id=test_id, iterations=iterations, status=STATUS_STARTED)
  for addr in (
    READY_FLAG, PRODUCED_COUNT, MATH_DONE_COUNT, PACK_DONE_COUNT,
    DEBUG_TRISC0, DEBUG_TRISC1, DEBUG_TRISC2,
  ):
    fw.write32(addr, 0)
  fw.fence()
  if spec.method != METHOD_BASELINE:
    emit_math_init(fw, spec)
  fw.init_barrier()
  emit_mark(fw, DEBUG_TRISC1, 0xF020)
  fw.write32(READY_FLAG, 1)

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s8, iterations)
  fw.li(s6, 0)
  loop = fw._new_label("math_loop")
  done = fw._new_label("math_done")
  fw.label(loop)
  fw.beq(s8, zero, done)
  if spec.method == METHOD_BASELINE:
    fw.addi(s1, s1, 1)
  else:
    emit_mark(fw, DEBUG_TRISC1, 0xF100)
    emit_wait_counter_gt(fw, PRODUCED_COUNT, s6)
    emit_mark(fw, DEBUG_TRISC1, 0xF110)
    if spec.method in (METHOD_ISSUE, METHOD_LATENCY):
      harness.read_wall_clock(fw, a2, a3)
    elif spec.method == METHOD_THROUGHPUT:
      skip_start = fw._new_label("throughput_start_already_set")
      fw.bne(s6, zero, skip_start)
      harness.read_wall_clock(fw, a2, a3)
      fw.label(skip_start)
    if spec.method == METHOD_LATENCY:
      emit_math_body(fw, spec)
      emit_math_commit(fw)
      harness.read_wall_clock(fw, a4, a5)
    elif spec.method == METHOD_ISSUE:
      emit_math_body(fw, spec)
      harness.read_wall_clock(fw, a4, a5)
      emit_math_commit(fw)
    else:
      emit_math_body(fw, spec)
      emit_math_commit(fw)
    emit_inc_word(fw, MATH_DONE_COUNT)
    fw.addi(s6, s6, 1)
  fw.addi(s8, s8, -1)
  fw.j(loop)
  fw.label(done)
  if spec.method in (METHOD_BASELINE, METHOD_THROUGHPUT):
    harness.read_wall_clock(fw, a4, a5)
  if spec.method != METHOD_BASELINE:
    emit_mark(fw, DEBUG_TRISC1, 0xF300)
    emit_wait_eq(fw, PACK_DONE_COUNT, iterations)
    emit_mark(fw, DEBUG_TRISC1, 0xF301)
  emit_record(
    fw,
    test_id=test_id,
    spec=spec,
    iterations=iterations,
    start_lo=a2,
    start_hi=a3,
    end_lo=a4,
    end_hi=a5,
  )
  emit_header(fw, test_id=test_id, iterations=iterations, status=STATUS_DONE)
  return fw.ret_kernel()


def emit_runtime_cb_setup(fw: matmul.MatmulTrisc, cb_index: int, *, pages: int, tile_bytes: int):
  iface = fw.data["cb_interface"] + cb_index * CB.LOCAL_INTERFACE_SIZE
  limit = OUT_CB_BASE + tile_bytes * pages
  for off, value in enumerate((
    OUT_CB_BASE,
    limit,
    tile_bytes,
    pages,
    OUT_CB_BASE,
    OUT_CB_BASE,
    0,
    0,
  )):
    fw.li(t0, value)
    fw.write32(iface + off * 4, t0, tmp_addr=t1)
  fw.write32(CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE, 0)
  fw.write32(CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE, 0)
  return fw


def build_trisc2(spec: BenchSpec, iterations: int, plan: matmul.MatmulPlan) -> KernelBase:
  if spec.method == METHOD_BASELINE:
    return build_idle_trisc(2)
  fw = matmul.MatmulTrisc(2)
  fw.prologue()
  emit_mark(fw, DEBUG_TRISC2, 0xD000)
  emit_runtime_cb_setup(fw, OUT_CB, pages=plan.cb16_pages, tile_bytes=spec.tile_bytes)
  emit_mark(fw, DEBUG_TRISC2, 0xD010)
  fw.pack.init(dtype=spec.dtype, out_cb=OUT_CB, mop_cfg=matmul.MATMUL_PACK_MOP_CFG)
  emit_mark(fw, DEBUG_TRISC2, 0xD011)
  fw.init_barrier()
  emit_mark(fw, DEBUG_TRISC2, 0xD020)
  fw.li(s8, iterations)
  loop = fw._new_label("pack_loop")
  done = fw._new_label("pack_done")
  fw.label(loop)
  fw.beq(s8, zero, done)
  emit_mark(fw, DEBUG_TRISC2, 0xD100)
  fw.emit(TTSEMWAIT(
    matmul.STALL_MATH_PACK_DATA,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_ZERO,
  ))
  emit_mark(fw, DEBUG_TRISC2, 0xD101)
  matmul.emit_pack_tile_to_cb(fw, plan, OUT_CB)
  emit_mark(fw, DEBUG_TRISC2, 0xD102)
  emit_inc_word(fw, PACK_DONE_COUNT)
  fw.addi(s8, s8, -1)
  fw.j(loop)
  fw.label(done)
  emit_mark(fw, DEBUG_TRISC2, 0xDFFF)
  return fw.ret_kernel()


def build_idle_trisc(thread_id: int) -> KernelBase:
  fw = matmul.MatmulTrisc(thread_id)
  fw.prologue()
  fw.init_barrier()
  return fw.ret_kernel()


def build_brisc_release() -> KernelBase:
  fw = matmul.MatmulKernel()
  fw.release_triscs()
  return fw.ret()


def build_program(spec: BenchSpec, test_id: int, iterations: int) -> Program:
  plan = tiny_plan(spec.out_h, spec.out_w, cb16_pages=max(2 * max(1, iterations) * max(1, spec.output_tiles), 4))
  program = Program(
    brisc=build_brisc_release(),
    ncrisc=KernelBase().ret(),
    trisc0=build_trisc0(spec, iterations, plan),
    trisc1=build_trisc1(spec, test_id, iterations),
    trisc2=build_trisc2(spec, iterations, plan),
    cbs=[],
    semaphores=matmul.NUM_SEMAPHORES,
    num_cores=1,
  )
  program.name = f"microbench_math_mvmul:{spec.name}"
  return program


def clear_results(device: Device, core: tuple[int, int]):
  ranges = debug_ranges()
  with harness.device_window(device, core) as win:
    for item in ranges:
      win.write(item.address, b"\0" * item.size)


def read_results(device: Device, core: tuple[int, int]) -> bytes:
  result_range = debug_ranges()[0]
  with harness.device_window(device, core) as win:
    blob = win.read(result_range.address, result_range.size)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly")
  return blob


def read_l1_words(device: Device, core: tuple[int, int], addr: int, count: int) -> tuple[int, ...]:
  with harness.device_window(device, core) as win:
    blob = win.read(addr, count * 4)
  return struct.unpack("<" + "I" * count, blob)


def print_debug_snapshot(device: Device, core: tuple[int, int], spec: BenchSpec):
  try:
    header = read_l1_words(device, core, RESULT_BASE, HEADER_WORDS)
    control = read_l1_words(device, core, CONTROL_BASE, 16)
  except Exception as e:  # noqa: BLE001 - best-effort failure telemetry
    print(f"{spec.name}: debug snapshot unavailable: {e}", flush=True)
    return
  print(
    f"{spec.name}: header magic=0x{header[0]:08x} status=0x{header[4]:08x} "
    f"ready={control[0]} produced={control[1]} math_done={control[2]} packed={control[3]}",
    flush=True,
  )
  print(
    f"{spec.name}: breadcrumbs trisc0=0x{control[4]:08x} "
    f"trisc1=0x{control[8]:08x} trisc2=0x{control[12]:08x}",
    flush=True,
  )


def parse_result(blob: bytes, spec: BenchSpec) -> Record:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"{spec.name}: bad result magic 0x{header[0]:08x}")
  if header[4] != STATUS_DONE:
    raise RuntimeError(f"{spec.name}: benchmark did not finish, status=0x{header[4]:08x}")
  words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, HEADER_SIZE)
  if words[0] != RECORD_MAGIC:
    raise RuntimeError(f"{spec.name}: bad record magic 0x{words[0]:08x}")
  start = words[9] | (words[10] << 32)
  end = words[11] | (words[12] << 32)
  return Record(
    test_id=words[1],
    name=spec.name,
    method=words[2],
    shape=spec.shape,
    variant=words[3],
    iterations=words[4],
    output_tiles=words[7],
    mvmuls_per_iter=words[8],
    dtype=Dtype(words[16]),
    instr_mod19=words[17],
    start=start,
    end=end,
    cycles=(end - start) & ((1 << 64) - 1),
    produced=words[13],
    packed=words[14],
    sink=words[15],
  )


def adjusted(records: list[Record], record: Record) -> float:
  empty = next((r.cycles_per_iter for r in records if r.name == "empty"), 0.0)
  return record.cycles_per_iter - empty


def format_table(records: list[Record]) -> str:
  lines = [
    "| test | dtype | im19 | method | shape | variant | iters | cyc/iter | adj cyc/iter | cyc/tile | cyc/MVMUL | produced | packed |",
    "|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for record in records:
    adj = adjusted(records, record)
    tile = adj / record.output_tiles if record.output_tiles else 0.0
    mvmul = adj / record.mvmuls_per_iter if record.mvmuls_per_iter else 0.0
    lines.append(
      f"| {record.name} | {record.dtype.name} | {record.instr_mod19} | "
      f"{METHOD_NAMES.get(record.method, str(record.method))} | {record.shape} | "
      f"{VARIANT_NAMES.get(record.variant, str(record.variant))} | {record.iterations} | "
      f"{record.cycles_per_iter:.2f} | {adj:.2f} | {tile:.2f} | {mvmul:.2f} | "
      f"{record.produced} | {record.packed} |"
    )
  return "\n".join(lines)


def append_report(path: Path, *, core: tuple[int, int], command: str, records: list[Record]):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- Command: `{command}`\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write("- Scaffold: TRISC0 unpack from L1 scratch, TRISC1 math, TRISC2 pack to CB16\n")
    f.write("- Math body: `matmul_peak` addr-mod/replay setup with sweepable `TTMVMUL.instr_mod19`\n")
    f.write("- Baseline subtraction: adjusted rows subtract the `empty` loop cycles per iteration\n\n")
    f.write(format_table(records))
    f.write("\n")


def run_selected(device: Device, core: tuple[int, int], requested_iters: int, specs: list[BenchSpec]) -> list[Record]:
  records: list[Record] = []
  for test_id, spec in enumerate(specs):
    iterations = active_iterations(spec, requested_iters)
    print(f"running {spec.name} iters={iterations}", flush=True)
    clear_results(device, core)
    try:
      device.run(build_program(spec, test_id, iterations))
    except Exception:
      print_debug_snapshot(device, core, spec)
      raise
    records.append(parse_result(read_results(device, core), spec))
  return records


def build_only(specs: list[BenchSpec], requested_iters: int) -> None:
  for test_id, spec in enumerate(specs):
    program = build_program(spec, test_id, active_iterations(spec, requested_iters))
    program.layout(core_xy=(0, 0))
    for kernel in program.kernel_map.values():
      kernel.compile()
    print(f"built {spec.name}")


def dtype_from_name(text: str) -> Dtype:
  try:
    return Dtype[text]
  except KeyError as exc:
    choices = ", ".join(dtype.name for dtype in Dtype)
    raise argparse.ArgumentTypeError(f"unknown dtype {text!r}; choices: {choices}") from exc


def parse_int_list(text: str) -> tuple[int, ...]:
  values = tuple(int(part.strip(), 0) for part in text.split(",") if part.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected at least one integer")
  return values


def with_modes(specs: list[BenchSpec], *, dtype: Dtype, instr_mods: tuple[int, ...]) -> list[BenchSpec]:
  out: list[BenchSpec] = []
  for spec in specs:
    if spec.method == METHOD_BASELINE:
      out.append(BenchSpec(spec.name, spec.method, spec.out_h, spec.out_w, spec.variant, dtype, 0))
      continue
    for instr_mod in instr_mods:
      if not 0 <= instr_mod <= 7:
        raise ValueError(f"instr_mod19 must fit 3 bits, got {instr_mod}")
      name = spec.name if len(instr_mods) == 1 else f"{spec.name}_im{instr_mod}"
      out.append(BenchSpec(name, spec.method, spec.out_h, spec.out_w, spec.variant, dtype, instr_mod))
  return out


def main() -> None:
  parser = argparse.ArgumentParser(description="Microbenchmark Tensix MVMUL/math in a minimal unpack->math->pack scaffold.")
  parser.add_argument("--core", type=harness.parse_core, default=None, help="logical Tensix core X,Y; default: first program core")
  parser.add_argument("--iters", type=int, default=4, help="iterations for issue/throughput rows; latency rows force 1")
  parser.add_argument("--only", nargs="+", default=None, help="optional subset of spec names")
  parser.add_argument("--dtype", type=dtype_from_name, default=Dtype.Float16_b, help="unpack/math/pack dtype for SrcA/SrcB/DST")
  parser.add_argument("--instr-mods", type=parse_int_list, default=(0,), help="comma-separated TTMVMUL instr_mod19 values to sweep (0..7)")
  parser.add_argument("--build-only", action="store_true", help="compile/layout programs without opening the device")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/math-mvmul.md")
  parser.add_argument("--report", type=Path, default=harness.doc_path("tensix", "math-mvmul.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  selected = list(SPECS)
  if args.only:
    by_name = {spec.name: spec for spec in SPECS}
    missing = [name for name in args.only if name not in by_name]
    if missing:
      raise ValueError("unknown spec(s): " + ", ".join(missing))
    selected = [by_name[name] for name in args.only]
    if "empty" not in args.only:
      selected.insert(0, by_name["empty"])
  selected = with_modes(selected, dtype=args.dtype, instr_mods=args.instr_mods)

  if args.build_only:
    build_only(selected, args.iters)
    return

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    records = run_selected(device, core, args.iters, selected)

  print(format_table(records))
  mvmul_rows = [adjusted(records, r) / r.mvmuls_per_iter for r in records if r.mvmuls_per_iter]
  if mvmul_rows:
    print(f"\nmean adjusted cycles/MVMUL across measured rows: {statistics.mean(mvmul_rows):.2f}")
  if not args.no_report:
    append_report(args.report, core=core, command=" ".join(sys.argv), records=records)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
