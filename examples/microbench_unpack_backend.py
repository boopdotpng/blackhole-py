#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.dont_write_bytecode = True

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import matmul_peak as matmul

from asm import KernelBase
from device import Device
from dsl import (
  TTMOP, TTSEMINIT, TTSETADCXX, TTSETADCZW, TTSETRWC, TTSTALLWAIT, TTREPLAY,
  a0, a1, a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from pcie import TLBWindow
from program import Dtype, Program
from ttk.debug import DebugRange
from ttk.mailbox import TriscLocalMem as TLM
from ttk.tensix import Cfg, TensixL1, TensixMMIO, TensixRegs, TensixSem, TensixStall, TensixWait, ThreadCfg


Core = tuple[int, int]

RESULT_BASE = 0x128000
DONE_FLAG = RESULT_BASE - 4
HEADER_WORDS = 16
RECORD_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
RECORD_SIZE = RECORD_WORDS * 4
RESULT_MAGIC = 0x55424D48  # "UBMH"
RECORD_MAGIC = 0x55424D52  # "UBMR"
STATUS_STARTED = 0x7100B001
STATUS_DONE = 0x7100D00D

TILE_BYTES = Dtype.Float16_b.tile_size
SCRATCH0 = TensixL1.DATA_BUFFER_SPACE_BASE + 0x20000
SCRATCH1 = SCRATCH0 + 0x40000
THCON_SEC0_REG3 = TensixRegs.CFG_BASE + matmul.THCON_SEC0_REG3_BASE_ADDR32 * 4
THCON_SEC1_REG3 = TensixRegs.CFG_BASE + matmul.THCON_SEC1_REG3_BASE_ADDR32 * 4
DEFAULT_BWS = (1, 2, 3, 4, 5, 6)
CLEAR_VALID_WORD = TTSETRWC(clear_ab_vld=3, BitMask=3)


@dataclass(frozen=True)
class BenchSpec:
  name: str
  group: str
  bw: int
  rows_per_iter: int
  subblocks_per_iter: int
  unpack_tiles_per_iter: int
  include_in_summary: bool = True


@dataclass(frozen=True)
class Record:
  test_id: int
  name: str
  group: str
  bw: int
  iterations: int
  rows_per_iter: int
  subblocks_per_iter: int
  unpack_tiles_per_iter: int
  start: int
  end: int
  cycles: int
  sink: int

  @property
  def cycles_per_iter(self) -> float:
    return self.cycles / self.iterations


def parse_core(s: str) -> Core:
  try:
    x, y = s.split(",", 1)
    return int(x, 0), int(y, 0)
  except ValueError as e:
    raise argparse.ArgumentTypeError("core must be X,Y") from e


def debug_ranges(specs: tuple[BenchSpec, ...]) -> tuple[DebugRange, ...]:
  size = HEADER_SIZE + len(specs) * RECORD_SIZE
  return (DebugRange(0, "l1", RESULT_BASE, size, "unpack_backend_microbench_results"),)


def result_size(specs: tuple[BenchSpec, ...]) -> int:
  return debug_ranges(specs)[0].size


def read_wall_clock(fw: KernelBase, lo, hi, *, addr=a7, hi2=a6):
  retry = fw._new_label("wall_clock_retry")
  fw.li(addr, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.label(retry)
  fw.lw(hi, addr, 0)
  fw.lw(lo, addr, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L - TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.lw(hi2, addr, 0)
  fw.bne(hi, hi2, retry)
  return fw


def emit_header(fw: KernelBase, *, specs: tuple[BenchSpec, ...], iterations: int, status: int):
  fw.li(s2, RESULT_BASE)
  values = (
    RESULT_MAGIC, len(specs), RECORD_WORDS, status, iterations, RESULT_BASE, result_size(specs), TILE_BYTES,
  )
  for off, value in enumerate(values):
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
  sink=s6,
):
  fw.li(s2, RESULT_BASE + HEADER_SIZE + test_id * RECORD_SIZE)
  values = (
    RECORD_MAGIC,
    test_id,
    spec.bw,
    iterations,
    spec.rows_per_iter,
    spec.subblocks_per_iter,
    spec.unpack_tiles_per_iter,
  )
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi, sink), start=len(values)):
    fw.sw(reg, s2, off * 4)
  fw.sw(zero, s2, 12 * 4)
  fw.sw(zero, s2, 13 * 4)
  fw.sw(zero, s2, 14 * 4)
  fw.sw(zero, s2, 15 * 4)
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


def emit_cfg_context_flip(fw: matmul.MatmulTrisc, *, sec0: bool, write_sync: bool):
  fw.lw(t2, s11, 0)
  fw.mv(t3, s4 if sec0 else s5)
  ctx_ready = fw._new_label("cfg_context_ready")
  fw.beq(t2, zero, ctx_ready)
  fw.addi(t3, t3, 4)
  fw.label(ctx_ready)
  fw.sw(a1 if sec0 else a0, t3, 0)
  if write_sync:
    fw.sw(zero, s7, 0)
  fw.li(t3, 1)
  fw.sub(t3, t3, t2)
  fw.sw(t3, s11, 0)
  ctx0 = fw._new_label("set_unpack_ctx0")
  done = fw._new_label("set_unpack_ctx_done")
  fw.beq(t2, zero, ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.j(done)
  fw.label(ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
  fw.label(done)
  return fw


def emit_toggle_unpack_context_only(fw: matmul.MatmulTrisc):
  fw.lw(t2, s11, 0)
  fw.li(t3, 1)
  fw.sub(t3, t3, t2)
  fw.sw(t3, s11, 0)
  ctx0 = fw._new_label("toggle_ctx0")
  done = fw._new_label("toggle_ctx_done")
  fw.beq(t2, zero, ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.j(done)
  fw.label(ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
  fw.label(done)
  return fw


def emit_matmul_unpack_row(fw: matmul.MatmulTrisc, in0_index, in1_index, *, clear_valid: bool):
  emit_wait_pc_unpack_ready(fw)
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

  fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
  fw.emit(matmul.MATMUL_UNPACK_SRCB_LOAD)
  ctx1 = fw._new_label("mop_ctx1")
  ctx_done = fw._new_label("mop_ctx_done")
  fw.bne(t2, zero, ctx1)
  fw.emit(TTMOP(0, 1, 0))
  fw.j(ctx_done)
  fw.label(ctx1)
  fw.emit(TTMOP(0, 1, 0xFF))
  fw.label(ctx_done)
  fw.emit(matmul.TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
  if clear_valid:
    fw.emit(CLEAR_VALID_WORD)

  fw.li(t3, 1)
  fw.sub(t3, t3, t2)
  fw.sw(t3, s11, 0)
  ctx0 = fw._new_label("row_set_ctx0")
  done = fw._new_label("row_set_ctx_done")
  fw.beq(t2, zero, ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.j(done)
  fw.label(ctx0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
  fw.label(done)
  return fw


def emit_reload_tile(fw: matmul.MatmulTrisc, tile_index: int, *, clear_valid: bool):
  emit_wait_pc_unpack_ready(fw)
  fw.li(t4, tile_index)
  fw.mul(a0, t4, a4)
  fw.add(a0, a0, s0)
  fw.addi(a0, a0, -1)
  fw.lw(t2, s11, 0)
  fw.mv(t3, s4)
  sec0_ready = fw._new_label("reload_sec0_ready")
  fw.beq(t2, zero, sec0_ready)
  fw.addi(t3, t3, 4)
  fw.label(sec0_ready)
  fw.sw(a0, t3, 0)
  fw.sw(zero, s7, 0)
  fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
  fw.emit(TTMOP(1, 0, 0))
  fw.emit(matmul.TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
  if clear_valid:
    fw.emit(CLEAR_VALID_WORD)
  emit_toggle_unpack_context_only(fw)
  return fw


def emit_reload_recfg_2x2(fw: matmul.MatmulTrisc, *, clear_valid: bool):
  fw.push_tensix(matmul.TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32))
  fw.emit(TTSETADCXX(1, 255, 0))
  fw.write_mop_cfg(matmul.MATMUL_RELOAD_UNPACK_MOP_CFG, 0)
  for tile_index in range(4):
    fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    emit_reload_tile(fw, tile_index, clear_valid=clear_valid)
  fw.tensix_sync(0)
  fw.push_tensix(matmul.TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32))
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  fw.emit(TTSETADCXX(1, 1023, 0))
  fw.emit(TTSETADCXX(2, 1023, 0))
  fw.write_mop_cfg(matmul.MATMUL_UNPACK_AB_MOP_CFG, 0)
  return fw


def emit_subblock(fw: matmul.MatmulTrisc, bw: int, *, clear_valid: bool):
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  for inner in range(bw):
    fw.li(s9, inner)
    fw.li(s10, inner * 2)
    emit_matmul_unpack_row(fw, s9, s10, clear_valid=clear_valid)
    fw.li(s9, bw + inner)
    emit_matmul_unpack_row(fw, s9, s10, clear_valid=clear_valid)
  return fw


def build_specs(bws: tuple[int, ...], *, include_reload: bool) -> tuple[BenchSpec, ...]:
  specs = [
    BenchSpec("empty", "baseline", 0, 0, 0, 0, False),
    BenchSpec("pc_unpack_sync_poll", "sync", 0, 0, 0, 0, False),
    BenchSpec("pc_unpack_sync_write", "sync", 0, 0, 0, 0, False),
    BenchSpec("cfg_context_flip_setc16", "cfg", 0, 0, 0, 0, False),
    BenchSpec("stallwait_unpack_trisc_cfg", "sync", 0, 0, 0, 0, False),
    BenchSpec("matmul_unpack_row", "row", 1, 1, 0, 3),
  ]
  for bw in bws:
    rows = bw * 2
    specs.append(BenchSpec(f"matmul_2x2_bw{bw}", "subblock", bw, rows, 1, rows * 3))
  if include_reload:
    specs.append(BenchSpec("reload_recfg_2x2", "reload", 0, 4, 1, 4))
  return tuple(specs)


def filter_specs(specs: tuple[BenchSpec, ...], only: str | None) -> tuple[BenchSpec, ...]:
  if not only:
    return specs
  wanted = {name.strip() for name in only.split(",") if name.strip()}
  if "empty" not in wanted:
    wanted.add("empty")
  filtered = tuple(spec for spec in specs if spec.name in wanted)
  missing = wanted - {spec.name for spec in filtered}
  if missing:
    raise ValueError("--only named unknown tests: " + ", ".join(sorted(missing)))
  return filtered


def emit_spec_body(fw: matmul.MatmulTrisc, spec: BenchSpec, *, clear_valid: bool):
  if spec.name == "empty":
    fw.addi(s6, s6, 1)
  elif spec.name == "pc_unpack_sync_poll":
    emit_wait_pc_unpack_ready(fw)
  elif spec.name == "pc_unpack_sync_write":
    fw.sw(zero, s7, 0)
  elif spec.name == "cfg_context_flip_setc16":
    emit_toggle_unpack_context_only(fw)
  elif spec.name == "stallwait_unpack_trisc_cfg":
    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
  elif spec.name == "matmul_unpack_row":
    fw.li(s9, 0)
    fw.li(s10, 0)
    emit_matmul_unpack_row(fw, s9, s10, clear_valid=clear_valid)
  elif spec.name.startswith("matmul_2x2_bw"):
    emit_subblock(fw, spec.bw, clear_valid=clear_valid)
  elif spec.name == "reload_recfg_2x2":
    emit_reload_recfg_2x2(fw, clear_valid=clear_valid)
  else:
    raise ValueError(spec.name)
  return fw


def emit_timed_loop(
  fw: matmul.MatmulTrisc,
  *,
  test_id: int,
  spec: BenchSpec,
  iterations: int,
  clear_valid: bool,
):
  fw.li(s6, 0x55420000 | test_id)
  fw.li(a4, TILE_BYTES)
  fw.li(a5, TILE_BYTES)
  fw.li(s4, THCON_SEC0_REG3)
  fw.li(s5, THCON_SEC1_REG3)
  fw.li(s7, TensixRegs.PC_UNPACK_SYNC)
  fw.li(s11, TLM.TRISC0_UNPACK_CFG_CONTEXT)
  read_wall_clock(fw, a2, a3)
  fw.li(s8, iterations)
  loop = fw._new_label(f"bench_{spec.name}")
  done = fw._new_label(f"bench_{spec.name}_done")
  fw.label(loop)
  fw.beq(s8, zero, done)
  emit_spec_body(fw, spec, clear_valid=clear_valid)
  fw.addi(s8, s8, -1)
  fw.j(loop)
  fw.label(done)
  read_wall_clock(fw, a4, a5)
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
  return fw


def emit_unpack_setup(fw: matmul.MatmulTrisc):
  fw.unpack.init(dtype=Dtype.Float16_b, tile_bytes=TILE_BYTES, mop_cfg=matmul.MATMUL_UNPACK_AB_MOP_CFG)
  fw.emit(TTSETADCXX(1, 1023, 0))
  fw.emit(TTSETADCXX(2, 1023, 0))
  fw.emit(TTREPLAY(0, len(matmul.MATMUL_UNPACK_REPLAY0_LOAD), 0, 1))
  for word in matmul.MATMUL_UNPACK_REPLAY0_LOAD:
    fw.emit(word)
  fw.emit(TTREPLAY(6, len(matmul.MATMUL_UNPACK_REPLAY1_LOAD), 0, 1))
  for word in matmul.MATMUL_UNPACK_REPLAY1_LOAD:
    fw.emit(word)
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.UNPACK_SYNC), init_value=0, max_value=2))
  fw.tensix_sync(0)
  fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, 0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.li(s0, SCRATCH0)
  fw.li(s1, SCRATCH1)
  fw.li(a4, TILE_BYTES)
  fw.li(a5, TILE_BYTES)
  fw.li(s7, TensixRegs.PC_UNPACK_SYNC)
  fw.li(s11, TLM.TRISC0_UNPACK_CFG_CONTEXT)
  fw.li(s4, THCON_SEC0_REG3)
  fw.li(s5, THCON_SEC1_REG3)
  fw.li(a0, SCRATCH0 - 1)
  fw.li(a1, SCRATCH1 - 1)
  return fw


def build_bench_kernel(specs: tuple[BenchSpec, ...], iterations: int, *, clear_valid: bool) -> KernelBase:
  fw = matmul.MatmulTrisc(0)
  fw.write32(DONE_FLAG, 0)
  emit_header(fw, specs=specs, iterations=iterations, status=STATUS_STARTED)
  emit_unpack_setup(fw)
  for test_id, spec in enumerate(specs):
    emit_timed_loop(fw, test_id=test_id, spec=spec, iterations=iterations, clear_valid=clear_valid)
  fw.write32(DONE_FLAG, 1)
  emit_header(fw, specs=specs, iterations=iterations, status=STATUS_DONE)
  return fw.ret()


def build_trisc1_clear_kernel() -> KernelBase:
  fw = matmul.MatmulTrisc(1)
  fw.li(s0, DONE_FLAG)
  loop = fw._new_label("clear_valid_loop")
  done = fw._new_label("clear_valid_done")
  fw.label(loop)
  fw.lw(t0, s0, 0)
  fw.bne(t0, zero, done)
  fw.emit(CLEAR_VALID_WORD)
  fw.j(loop)
  fw.label(done)
  return fw.ret()


def build_program(
  specs: tuple[BenchSpec, ...],
  iterations: int,
  *,
  clear_valid: bool,
  trisc1_clear: bool,
) -> Program:
  empty = KernelBase().ret()
  program = Program(
    brisc=empty,
    ncrisc=empty,
    trisc0=build_bench_kernel(specs, iterations, clear_valid=clear_valid),
    trisc1=build_trisc1_clear_kernel() if trisc1_clear else empty,
    trisc2=empty,
    num_cores=1,
  )
  program.name = "microbench_unpack_backend"
  return program


def clear_results(device: Device, core: Core, specs: tuple[BenchSpec, ...]):
  result_range = debug_ranges(specs)[0]
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=core) as win:
      win.write(result_range.address, b"\0" * result_range.size)
  finally:
    device.dev.set_power_state(False)


def read_results(device: Device, core: Core, specs: tuple[BenchSpec, ...]) -> bytes:
  result_range = debug_ranges(specs)[0]
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=core) as win:
      blob = win.read(result_range.address, result_range.size)
  finally:
    device.dev.set_power_state(False)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly")
  return blob


def parse_results(blob: bytes, specs: tuple[BenchSpec, ...]) -> list[Record]:
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{header[0]:08x}")
  if header[3] != STATUS_DONE:
    raise RuntimeError(f"benchmark did not finish, status=0x{header[3]:08x}")
  records = []
  for test_id, spec in enumerate(specs):
    off = HEADER_SIZE + test_id * RECORD_SIZE
    words = struct.unpack_from("<" + "I" * RECORD_WORDS, blob, off)
    if words[0] != RECORD_MAGIC:
      raise RuntimeError(f"{spec.name}: bad record magic 0x{words[0]:08x}")
    start = words[7] | (words[8] << 32)
    end = words[9] | (words[10] << 32)
    records.append(Record(
      test_id=words[1],
      name=spec.name,
      group=spec.group,
      bw=words[2],
      iterations=words[3],
      rows_per_iter=words[4],
      subblocks_per_iter=words[5],
      unpack_tiles_per_iter=words[6],
      start=start,
      end=end,
      cycles=(end - start) & ((1 << 64) - 1),
      sink=words[11],
    ))
  return records


def adjusted(records: list[Record], record: Record) -> float:
  empty = records[0].cycles_per_iter
  return record.cycles_per_iter - empty


def fmt(x: float) -> str:
  return f"{x:.2f}"


def format_raw_table(records: list[Record], *, aiclk_mhz: float) -> str:
  lines = [
    "| test | group | bw | cycles | cyc/iter | adj cyc/iter | us/iter | sink |",
    "|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  for r in records:
    adj = adjusted(records, r)
    lines.append(
      f"| {r.name} | {r.group} | {r.bw} | {r.cycles} | {fmt(r.cycles_per_iter)} | "
      f"{fmt(adj)} | {adj / aiclk_mhz:.4f} | 0x{r.sink:08x} |"
    )
  return "\n".join(lines)


def format_derived_table(records: list[Record], *, aiclk_mhz: float) -> str:
  lines = [
    "| test | bw | adj cyc/iter | cyc/row | cyc/subblock | cyc/unpack tile | us/subblock |",
    "|---|---:|---:|---:|---:|---:|---:|",
  ]
  for r in records:
    if r.group not in {"row", "subblock", "reload"}:
      continue
    adj = adjusted(records, r)
    row = adj / r.rows_per_iter if r.rows_per_iter else 0.0
    subblock = adj / r.subblocks_per_iter if r.subblocks_per_iter else 0.0
    tile = adj / r.unpack_tiles_per_iter if r.unpack_tiles_per_iter else 0.0
    lines.append(
      f"| {r.name} | {r.bw} | {fmt(adj)} | {fmt(row)} | {fmt(subblock)} | "
      f"{fmt(tile)} | {subblock / aiclk_mhz:.4f} |"
    )
  return "\n".join(lines)


def proposed_constants(records: list[Record]) -> dict[str, float]:
  by_name = {r.name: r for r in records}
  bw4 = adjusted(records, by_name["matmul_2x2_bw4"]) if "matmul_2x2_bw4" in by_name else 0.0
  if "matmul_unpack_row" in by_name:
    row = adjusted(records, by_name["matmul_unpack_row"])
  elif bw4:
    row = bw4 / 8.0
  else:
    row_records = [r for r in records if r.rows_per_iter]
    row = adjusted(records, row_records[0]) / row_records[0].rows_per_iter if row_records else 0.0
  if not bw4:
    bw4 = row * 8
  reload = adjusted(records, by_name["reload_recfg_2x2"]) if "reload_recfg_2x2" in by_name else 0.0
  return {
    "UNPACK_BACKEND_ROW_CYCLES": row,
    "UNPACK_BACKEND_2X2_BW4_CYCLES": bw4,
    "UNPACK_BACKEND_RELOAD_2X2_CYCLES": reload,
    "UNPACK_BACKEND_CLEAR_VALID_GUARD_CYCLES": 1.25,
  }


def write_report(
  path: Path,
  *,
  argv: list[str],
  core: Core,
  iterations: int,
  specs: tuple[BenchSpec, ...],
  records: list[Record],
  aiclk_mhz: float,
  clear_valid: bool,
  trisc1_clear: bool,
):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  constants = proposed_constants(records)
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", encoding="utf-8") as f:
    f.write("# Unpack Backend Microbenchmark\n\n")
    f.write(f"Generated: `{now}`\n\n")
    f.write("## Command\n\n")
    f.write("```bash\n")
    f.write("PYTHONDONTWRITEBYTECODE=1 " + " ".join(argv) + "\n")
    f.write("```\n\n")
    f.write("## Setup\n\n")
    f.write(f"- Core: logical `{core[0]},{core[1]}`\n")
    f.write(f"- Iterations per test: `{iterations}`\n")
    f.write(f"- AICLK for us conversion: `{aiclk_mhz:.1f}` MHz\n")
    f.write(f"- Clear-valid guard after unpack rows: `{'on' if clear_valid else 'off'}`\n")
    f.write(f"- TRISC1 clear-valid companion: `{'on' if trisc1_clear else 'off'}`\n")
    f.write("- Timed role: TRISC0. BRISC/NCRISC/TRISC2 kernels are empty; optional TRISC1 only clears SRCA/SRCB valid state outside the timed region.\n")
    f.write("- Unpack setup mirrors `examples/matmul_peak.py`: `Unpack.init`, two replay payload loads at slots 0/6, `MATMUL_UNPACK_AB_MOP_CFG`, `TTUNPACR`, `TTMOP`, `PC_UNPACK_SYNC`, and cfg context flipping through `UNPACK_MISC_CFG_CfgContext`.\n")
    f.write("- Scratch tile addresses are L1-only synthetic pages; the benchmark measures backend/control cost, not DRAM/NOC feed cost.\n\n")
    f.write("Debug L1 ranges:\n")
    for item in debug_ranges(specs):
      f.write(f"- `{item.name}` at `0x{item.address:x}` ({item.size} bytes)\n")
    f.write("\n")
    f.write("## Raw Cycles\n\n")
    f.write(format_raw_table(records, aiclk_mhz=aiclk_mhz))
    f.write("\n\n")
    f.write("## Derived Costs\n\n")
    f.write(format_derived_table(records, aiclk_mhz=aiclk_mhz))
    f.write("\n\n")
    f.write("## Proposed `examples/program_timing_model.py` Constants\n\n")
    f.write("| constant | cycles | note |\n")
    f.write("|---|---:|---|\n")
    f.write(f"| `UNPACK_BACKEND_ROW_CYCLES` | {constants['UNPACK_BACKEND_ROW_CYCLES']:.1f} | One matmul-style TRISC0 unpack row: poll `PC_UNPACK_SYNC`, write two cfg base regs, `TTUNPACR`, `TTMOP`, `TTSEMGET`, cfg flip. |\n")
    f.write(f"| `UNPACK_BACKEND_2X2_BW4_CYCLES` | {constants['UNPACK_BACKEND_2X2_BW4_CYCLES']:.1f} | One 2x2 output subblock at bw=4, eight unpack rows. |\n")
    f.write(f"| `UNPACK_BACKEND_RELOAD_2X2_CYCLES` | {constants['UNPACK_BACKEND_RELOAD_2X2_CYCLES']:.1f} | Reload-unpack 2x2 path including reload MOP reconfig and restore to AB MOP. |\n")
    f.write("| `UNPACK_BACKEND_CLEAR_VALID_GUARD_CYCLES` | 1.25 | Bookkeeping guard used by this isolated benchmark; do not charge it separately when modeling the real matmul math consumer. |\n\n")
    f.write("For matmul shapes with fixed 2x2 output subblocks, model the TRISC0 unpack backend as:\n\n")
    f.write("```text\n")
    f.write("unpack_cycles_per_subblock(bw) = UNPACK_BACKEND_ROW_CYCLES * (2 * bw)\n")
    f.write("reload_cycles_per_last_k_subblock = UNPACK_BACKEND_RELOAD_2X2_CYCLES\n")
    f.write("```\n\n")
    f.write("The measured subblock rows above are better calibration points than the linear formula when exact bw is known.\n\n")
    f.write("## Limitations\n\n")
    f.write("- This is a single-core, TRISC0-only microbench. It intentionally excludes BRISC/NCRISC feed pressure, math MOP overlap, pack pressure, and real CB wait/pop traffic.\n")
    f.write("- The TRISC1 clear-valid companion is a proxy for math-side consumption. It prevents isolated unpack rows from backing up, but it is not a full math MOP and can slightly change backend pressure.\n")
    f.write("- The optional TRISC0 clear-valid guard is off for the reported run unless explicitly enabled; if enabled, it is included in measured cycles and should not be charged in the matmul timing model.\n")
    f.write("- Tile contents are synthetic L1 scratch pages. The benchmark exercises unpack backend control and L1 reads, not DRAM or NOC delivery.\n")
    f.write("- Reload-unpack is feasible here only as a control-path proxy: no cb24 producer is active, so the measured row path skips CB wait/pop and uses scratch tile bases.\n")
    f.write("- Cycle-to-us conversion assumes the default `1350 MHz` AICLK unless overridden on the command line.\n")


def main() -> None:
  parser = argparse.ArgumentParser(description="Microbenchmark Blackhole TRISC0 unpack backend/control costs.")
  parser.add_argument("--core", type=parse_core, default=None, help="logical Tensix core X,Y; default: first device core")
  parser.add_argument("--iters", type=int, default=5, help="iterations per timed test")
  parser.add_argument("--bw", type=int, nargs="+", default=list(DEFAULT_BWS), help="in0 block widths to test")
  parser.add_argument("--aiclk-mhz", type=float, default=1350.0, help="AICLK used for us conversion")
  parser.add_argument("--no-reload", action="store_true", help="skip reload-unpack proxy test")
  parser.add_argument("--clear-valid", action="store_true", help="emit a TRISC0-side clear-valid guard after unpack rows")
  parser.add_argument("--no-trisc1-clear", action="store_true", help="disable the companion TRISC1 clear-valid loop")
  parser.add_argument("--only", default="matmul_2x2_bw4", help="comma-separated test names to run; empty is always included")
  parser.add_argument("--no-report", action="store_true", help="do not write the markdown report")
  parser.add_argument("--report", type=Path, default=Path("docs/unpack-backend-microbench.md"), help="markdown report path")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")
  bws = tuple(args.bw)
  if any(bw <= 0 for bw in bws):
    raise ValueError("--bw values must be positive")

  specs = filter_specs(build_specs(bws, include_reload=not args.no_reload), args.only)
  os.environ.setdefault("TT_USB", "1")
  device = Device()
  try:
    core = args.core or device.cores[0]
    clear_results(device, core, specs)
    device.run(build_program(
      specs,
      args.iters,
      clear_valid=args.clear_valid,
      trisc1_clear=not args.no_trisc1_clear,
    ))
    records = parse_results(read_results(device, core, specs), specs)
  finally:
    device.close()

  print(format_raw_table(records, aiclk_mhz=args.aiclk_mhz))
  print()
  print(format_derived_table(records, aiclk_mhz=args.aiclk_mhz))
  if not args.no_report:
    write_report(
      args.report,
      argv=sys.argv,
      core=core,
      iterations=args.iters,
      specs=specs,
      records=records,
      aiclk_mhz=args.aiclk_mhz,
      clear_valid=args.clear_valid,
      trisc1_clear=not args.no_trisc1_clear,
    )
    print(f"\nwrote {args.report}")


if __name__ == "__main__":
  main()
