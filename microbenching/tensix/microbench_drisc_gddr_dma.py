#!/usr/bin/env python3
"""Focused Blackhole DRISC GDDR DMA microbench.

This measures only the DRISC DMA engine moving data between GDDR and the DRISC
local L1 staging window. It intentionally excludes the later DRISC-L1 to worker
L1 NoC copy path covered by the overlap/output POCs.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (sets repo/examples paths)
from asm import KernelBase  # noqa: E402
from drisc_gddr_dma_poc import (  # noqa: E402
  DEBUG_CLOCK_MHZ, DMA_CTRL_ATTRS_BURST_255, DMA_READ_STATUS_MASK,
  DMA_WRITE_STATUS_MASK, RESULT_MAGIC, STAGE_ADDR as DEFAULT_STAGE_ADDR, TX_CTRL_TRANSFER_ATTRIBUTES,
  TX_READ_DST, TX_READ_SRC_HI, TX_READ_SRC_LO, TX_STREAM_STATUS, TX_TRANSFER_ATTRIBUTES,
  TX_WRITE_DST_HI, TX_WRITE_DST_LO, TX_WRITE_SRC, OP_READ, OP_WRITE, emit_dma_once,
  DMA_READ_ATTR_BASE, DMA_WRITE_ATTR_BASE, build_dma_kernel, stream_reg,
)
from drisc_hello import select_dram_core  # noqa: E402
from dsl import a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, t0, t1, t2, t3, t4, zero  # noqa: E402
from pcie import PCIDevice, TLBWindow  # noqa: E402
from ttk.drisc import (  # noqa: E402
  DRISC_FW_BASE, DRISC_L1_NOC_ALIAS, DRISC_RESET_PC, RegWindow,
  SOFT_RESET_0, SOFT_RESET_BRISC, launch_drisc as launch_poc_kernel,
)


RESULT_ADDR = 0x1F000
RESULT_WORDS = 32
MAX_STAGE_END = RESULT_ADDR
MAGIC = 0x4447444D  # "MGDD", little-endian.

STATUS_STARTED = 1
STATUS_DONE = 2
STATUS_TIMEOUT = 3

DIR_READ = 1
DIR_WRITE = 2
DIRECTIONS = {"read": DIR_READ, "write": DIR_WRITE}
DIR_NAMES = {v: k for k, v in DIRECTIONS.items()}

MODE_SINGLE = 1
MODE_PIPE = 2
MODE_DUAL = 3
MODES = {"single": MODE_SINGLE, "pipe": MODE_PIPE, "dual": MODE_DUAL}
MODE_NAMES = {v: k for k, v in MODES.items()}

DEFAULT_READ_ATTR_BASE = DMA_READ_ATTR_BASE
DEFAULT_WRITE_ATTR_BASE = DMA_WRITE_ATTR_BASE
DEFAULT_TIMEOUT_ITERS = 20_000_000
TX_CTRL_READ_STATUS = 0xFC001010
TX_CTRL_WRITE_STATUS = 0xFC001014


@dataclass(frozen=True)
class Case:
  direction: int
  mode: int
  page_size: int
  pages: int
  stream: int
  gddr_addr: int
  stage_addr: int
  ctrl_attrs: int
  read_attr_base: int
  write_attr_base: int
  timeout_iters: int
  pipe_depth: int = 2


@dataclass(frozen=True)
class Row:
  direction: str
  mode: str
  page_bytes: int
  pages: int
  total_bytes: int
  stream: str
  cycles: int
  issue_cycles: int
  tail_cycles: int
  bytes_per_cycle: float
  gbps: float
  ok: bool
  detail: str


def pattern(size: int, seed: int) -> bytes:
  return bytes(((i * 29 + seed) ^ (i >> 5) ^ (i >> 11)) & 0xFF for i in range(size))


def _u64(words: tuple[int, ...], lo_idx: int) -> int:
  return words[lo_idx] | (words[lo_idx + 1] << 32)


def _delta(start: int, end: int) -> int:
  return (end - start) & ((1 << 64) - 1)


def _gbps(byte_count: int, cycles: int) -> float:
  return (byte_count / cycles) * DEBUG_CLOCK_MHZ / 1000.0 if cycles else 0.0


def _stream_mask(case: Case) -> int:
  if case.mode == MODE_DUAL:
    return 0x3
  return 1 << case.stream


def _stage_slots(mode: int) -> int:
  if mode in (MODE_DUAL, MODE_PIPE):
    return 2
  return 1


def _case_stage_slots(case: Case) -> int:
  if case.mode == MODE_PIPE:
    return case.pipe_depth
  return _stage_slots(case.mode)


def emit_read_wall_clock(fw: KernelBase, lo, hi, *, addr=a7, hi2=a6):
  retry = fw._new_label("wall_clock_retry")
  fw.li(addr, 0xFFB121F8)
  fw.label(retry)
  fw.lw(hi, addr, 0)
  fw.lw(lo, addr, 0xFFB121F0 - 0xFFB121F8)
  fw.lw(hi2, addr, 0)
  fw.bne(hi, hi2, retry)
  return fw


def emit_header(fw: KernelBase, case: Case):
  values = (
    MAGIC,
    case.direction,
    case.mode,
    case.page_size,
    case.pages,
    case.gddr_addr & 0xFFFFFFFF,
    (case.gddr_addr >> 32) & 0xFFFFFFFF,
    case.stage_addr,
    STATUS_STARTED,
    _stream_mask(case),
    case.ctrl_attrs,
    case.read_attr_base if case.direction == DIR_READ else case.write_attr_base,
  )
  for idx, value in enumerate(values):
    fw.write32(RESULT_ADDR + idx * 4, value, tmp_addr=t0, tmp_val=t1)
  for idx in range(len(values), RESULT_WORDS):
    fw.write32(RESULT_ADDR + idx * 4, 0, tmp_addr=t0, tmp_val=t1)
  return fw


def emit_stream_statuses(fw: KernelBase):
  fw.read32(t1, stream_reg(0, TX_STREAM_STATUS), tmp_addr=t0)
  fw.write32(RESULT_ADDR + 24 * 4, t1, tmp_addr=t0, tmp_val=t2)
  fw.read32(t1, stream_reg(1, TX_STREAM_STATUS), tmp_addr=t0)
  return fw.write32(RESULT_ADDR + 25 * 4, t1, tmp_addr=t0, tmp_val=t2)


def emit_finish(fw: KernelBase):
  emit_read_wall_clock(fw, a4, a5, addr=t4, hi2=t3)
  fw.write32(RESULT_ADDR + 8 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  emit_stream_statuses(fw)
  for idx, reg in enumerate((a2, a3, a6, a7, a4, a5), start=16):
    fw.write32(RESULT_ADDR + idx * 4, reg, tmp_addr=t0, tmp_val=t2)
  done = fw._new_label("dma_done_spin")
  fw.label(done)
  return fw.j(done)


def emit_timeout(fw: KernelBase, *, stream: int, live_status):
  fw.write32(RESULT_ADDR + 8 * 4, STATUS_TIMEOUT, tmp_addr=t4, tmp_val=t1)
  fw.write32(RESULT_ADDR + (24 + stream) * 4, live_status, tmp_addr=t4, tmp_val=t1)
  spin = fw._new_label("dma_timeout_spin")
  fw.label(spin)
  return fw.j(spin)


def emit_poll_status(fw: KernelBase, *, stream: int, mask: int, timeout_iters: int):
  loop = fw._new_label("dma_poll")
  done = fw._new_label("dma_poll_done")
  timeout = fw._new_label("dma_poll_timeout")
  fw.li(t3, timeout_iters)
  fw.li(t2, mask)
  fw.label(loop)
  fw.beq(t3, zero, timeout)
  fw.read32(t0, stream_reg(stream, TX_STREAM_STATUS), tmp_addr=t4)
  fw.and_(t1, t0, t2)
  fw.beq(t1, zero, done)
  fw.addi(t3, t3, -1)
  fw.j(loop)
  fw.label(timeout)
  emit_timeout(fw, stream=stream, live_status=t0)
  fw.label(done)
  return fw


def emit_read_wait_n(fw: KernelBase, *, stream: int, max_outstanding: int):
  loop = fw._new_label("dma_wait_n")
  done = fw._new_label("dma_wait_n_done")
  fw.label(loop)
  fw.read32(t0, stream_reg(stream, TX_STREAM_STATUS), tmp_addr=t1)
  fw.srli(t0, t0, 8)
  fw.andi(t0, t0, 0xFF)
  fw.li(t1, max_outstanding)
  fw.bgeu(t1, t0, done)
  fw.j(loop)
  fw.label(done)
  return fw


def emit_ctrl_ready(fw: KernelBase, *, direction: int):
  loop = fw._new_label("dma_ctrl_ready")
  done = fw._new_label("dma_ctrl_ready_done")
  status_addr = TX_CTRL_READ_STATUS if direction == DIR_READ else TX_CTRL_WRITE_STATUS
  fw.li(t4, status_addr)
  fw.label(loop)
  fw.lw(t0, t4, 0)
  fw.andi(t0, t0, 1)
  fw.bne(t0, zero, done)
  fw.j(loop)
  fw.label(done)
  return fw


def emit_stage_for_index(fw: KernelBase, *, index_reg, slots: int, page_size: int, stage_addr: int, out):
  if slots == 1:
    return fw.li(out, stage_addr)
  fw.andi(out, index_reg, slots - 1)
  fw.li(t1, page_size)
  fw.mul(out, out, t1)
  fw.li(t1, stage_addr)
  return fw.add(out, out, t1)


def emit_dma_start(
  fw: KernelBase, *, direction: int, stream: int, gddr_lo, gddr_hi: int,
  l1_addr, page_size: int, read_attr_base: int, write_attr_base: int,
):
  size_words = page_size >> 4
  emit_ctrl_ready(fw, direction=direction)
  if direction == DIR_READ:
    fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00100 + stream, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_READ_SRC_LO), gddr_lo, tmp_addr=t0, tmp_val=t1)
    fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00110 + stream, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_READ_SRC_HI), gddr_hi, tmp_addr=t0, tmp_val=t1)
    fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00120 + stream, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_READ_DST), l1_addr, tmp_addr=t0, tmp_val=t1)
    fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00130 + stream, tmp_addr=t0, tmp_val=t1)
    return fw.write32(stream_reg(stream, TX_TRANSFER_ATTRIBUTES), read_attr_base | size_words, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00200 + stream, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_WRITE_SRC), l1_addr, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00210 + stream, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_WRITE_DST_LO), gddr_lo, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00220 + stream, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_WRITE_DST_HI), gddr_hi, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00230 + stream, tmp_addr=t0, tmp_val=t1)
  return fw.write32(stream_reg(stream, TX_TRANSFER_ATTRIBUTES), write_attr_base | size_words, tmp_addr=t0, tmp_val=t1)


def emit_single_loop(fw: KernelBase, case: Case):
  fw.li(s0, 0)  # page index
  fw.li(s1, case.pages)
  loop = fw._new_label("single_loop")
  done = fw._new_label("single_done")
  fw.label(loop)
  fw.bgeu(s0, s1, done)
  emit_dma_once(
    fw,
    op=OP_READ if case.direction == DIR_READ else OP_WRITE,
    gddr_addr=case.gddr_addr,
    size=case.page_size,
    stream=case.stream,
  )
  fw.addi(s0, s0, 1)
  fw.j(loop)
  fw.label(done)
  return fw


def emit_pipe_read_loop(fw: KernelBase, case: Case):
  gddr_hi = (case.gddr_addr >> 32) & 0xFFFFFFFF
  fw.li(s0, 0)  # pages issued
  fw.li(s1, case.pages)
  fw.li(s2, case.gddr_addr & 0xFFFFFFFF)  # current GDDR low address
  fw.li(s3, case.pipe_depth - 1)  # stage slot mask
  loop = fw._new_label("pipe_loop")
  done = fw._new_label("pipe_done")
  fw.label(loop)
  fw.bgeu(s0, s1, done)
  emit_read_wait_n(fw, stream=case.stream, max_outstanding=case.pipe_depth - 1)
  fw.and_(s4, s0, s3)
  fw.li(t1, case.page_size)
  fw.mul(s4, s4, t1)
  fw.li(t1, case.stage_addr)
  fw.add(s4, s4, t1)
  emit_dma_start(
    fw, direction=DIR_READ, stream=case.stream, gddr_lo=s2, gddr_hi=gddr_hi,
    l1_addr=s4, page_size=case.page_size, read_attr_base=case.read_attr_base,
    write_attr_base=case.write_attr_base,
  )
  fw.li(t1, case.page_size)
  fw.add(s2, s2, t1)
  fw.addi(s0, s0, 1)
  fw.j(loop)
  fw.label(done)
  return fw


def emit_dual_loop(fw: KernelBase, case: Case):
  mask = DMA_READ_STATUS_MASK if case.direction == DIR_READ else DMA_WRITE_STATUS_MASK
  gddr_hi = (case.gddr_addr >> 32) & 0xFFFFFFFF
  fw.li(s0, 0)  # page index
  fw.li(s1, case.pages)
  loop = fw._new_label("dual_loop")
  done = fw._new_label("dual_done")
  fw.label(loop)
  fw.bgeu(s0, s1, done)
  emit_dma_start(
    fw, direction=case.direction, stream=0, gddr_lo=case.gddr_addr & 0xFFFFFFFF, gddr_hi=gddr_hi,
    l1_addr=case.stage_addr, page_size=case.page_size, read_attr_base=case.read_attr_base,
    write_attr_base=case.write_attr_base,
  )
  emit_dma_start(
    fw, direction=case.direction, stream=1, gddr_lo=(case.gddr_addr + case.page_size) & 0xFFFFFFFF, gddr_hi=gddr_hi,
    l1_addr=case.stage_addr + case.page_size, page_size=case.page_size, read_attr_base=case.read_attr_base,
    write_attr_base=case.write_attr_base,
  )
  emit_poll_status(fw, stream=0, mask=mask, timeout_iters=case.timeout_iters)
  emit_poll_status(fw, stream=1, mask=mask, timeout_iters=case.timeout_iters)
  fw.addi(s0, s0, 2)
  fw.j(loop)
  fw.label(done)
  return fw


def build_kernel(case: Case) -> bytes:
  validate_case(case)
  fw = KernelBase(base_addr=DRISC_FW_BASE)
  emit_header(fw, case)
  fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00001, tmp_addr=t0, tmp_val=t1)
  fw.write32(TX_CTRL_TRANSFER_ATTRIBUTES, case.ctrl_attrs, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00002, tmp_addr=t0, tmp_val=t1)
  emit_read_wall_clock(fw, a2, a3)
  fw.write32(RESULT_ADDR + 15 * 4, 0xD6D00003, tmp_addr=t0, tmp_val=t1)

  if case.mode == MODE_SINGLE:
    emit_single_loop(fw, case)
  elif case.mode == MODE_PIPE:
    if case.direction != DIR_READ:
      raise ValueError("pipe mode is currently read-only")
    emit_pipe_read_loop(fw, case)
    emit_read_wall_clock(fw, a6, a7, addr=t4, hi2=t3)
    emit_poll_status(fw, stream=case.stream, mask=DMA_READ_STATUS_MASK, timeout_iters=case.timeout_iters)
    emit_finish(fw)
    return fw.compile()[0].data
  elif case.mode == MODE_DUAL:
    emit_dual_loop(fw, case)
  else:
    raise ValueError(f"unknown mode {case.mode}")

  emit_read_wall_clock(fw, a6, a7, addr=t4, hi2=t3)
  emit_finish(fw)
  return fw.compile()[0].data


def validate_case(case: Case):
  if case.direction not in DIR_NAMES:
    raise ValueError(f"unknown direction {case.direction}")
  if case.mode not in MODE_NAMES:
    raise ValueError(f"unknown mode {case.mode}")
  if case.page_size <= 0 or case.page_size % 16:
    raise ValueError("page size must be a positive multiple of 16")
  if case.pages <= 0:
    raise ValueError("pages must be positive")
  if case.stream not in (0, 1):
    raise ValueError("stream must be 0 or 1")
  if case.mode == MODE_PIPE and case.direction != DIR_READ:
    raise ValueError("pipe mode is currently read-only")
  if case.mode == MODE_PIPE and (case.pipe_depth < 2 or case.pipe_depth > 255):
    raise ValueError("pipe depth must be in [2, 255]")
  if case.mode == MODE_PIPE and case.pipe_depth & (case.pipe_depth - 1):
    raise ValueError("pipe depth must be a power of two")
  if case.mode == MODE_DUAL and case.pages % 2:
    raise ValueError("dual mode requires an even page count")
  slots = _case_stage_slots(case)
  if case.stage_addr < DRISC_FW_BASE + 0x1000:
    raise ValueError("stage address is too close to DRISC code")
  if case.stage_addr + slots * case.page_size > MAX_STAGE_END:
    raise ValueError(f"{slots} stage slot(s) do not fit before result area 0x{MAX_STAGE_END:x}")
  if case.gddr_addr < 0:
    raise ValueError("GDDR address must be non-negative")
  unique_span = (case.pages if case.mode == MODE_PIPE and case.direction == DIR_READ else slots) * case.page_size
  if (case.gddr_addr & 0xFFFFFFFF) + unique_span >= (1 << 32):
    raise ValueError("this benchmark keeps each GDDR span within one 32-bit low-address window")


def launch_drisc(l1: TLBWindow, regs: RegWindow, code: bytes, timeout: float) -> tuple[int, ...]:
  l1.write(RESULT_ADDR, b"\0" * (RESULT_WORDS * 4))
  l1.write(DRISC_FW_BASE, code)
  reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
  regs.write32(DRISC_RESET_PC, DRISC_FW_BASE)
  time.sleep(0.01)
  regs.write32(SOFT_RESET_0, reset_state & ~SOFT_RESET_BRISC)

  deadline = time.time() + timeout
  words = (0,) * RESULT_WORDS
  while time.time() < deadline:
    words = struct.unpack("<" + "I" * RESULT_WORDS, l1.read(RESULT_ADDR, RESULT_WORDS * 4))
    if words[0] == MAGIC and words[8] in (STATUS_DONE, STATUS_TIMEOUT):
      break
    time.sleep(0.001)

  live0 = regs.read32(stream_reg(0, TX_STREAM_STATUS))
  live1 = regs.read32(stream_reg(1, TX_STREAM_STATUS))
  final_reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, final_reset_state | SOFT_RESET_BRISC)
  if words[0] != MAGIC or words[8] != STATUS_DONE:
    raise TimeoutError(
      f"DRISC GDDR DMA benchmark did not finish; words={[hex(w) for w in words]} "
      f"live_stream0=0x{live0:08x} live_stream1=0x{live1:08x}"
    )
  return struct.unpack("<" + "I" * RESULT_WORDS, l1.read(RESULT_ADDR, RESULT_WORDS * 4))


def seed_for_case(gddr: TLBWindow, drisc_l1: TLBWindow, case: Case):
  slots = _case_stage_slots(case)
  if case.direction == DIR_READ:
    read_pages = case.pages if case.mode == MODE_PIPE else slots
    gddr.write(case.gddr_addr, pattern(read_pages * case.page_size, 0x31))
    drisc_l1.write(case.stage_addr, b"\0" * (slots * case.page_size))
  else:
    for slot in range(slots):
      drisc_l1.write(case.stage_addr + slot * case.page_size, pattern(case.page_size, 0xA0 + slot))
    gddr.write(case.gddr_addr, b"\0" * (slots * case.page_size))


def verify_case(gddr: TLBWindow, drisc_l1: TLBWindow, case: Case) -> tuple[bool, str]:
  if case.direction == DIR_READ:
    slots = _case_stage_slots(case)
    read_pages = case.pages if case.mode == MODE_PIPE else slots
    expected_all = pattern(read_pages * case.page_size, 0x31)
    for slot in range(slots):
      if case.mode == MODE_PIPE:
        if slot >= case.pages:
          continue
        final_page = slot + ((case.pages - 1 - slot) // slots) * slots
        expected_off = final_page * case.page_size
      else:
        final_page = slot
        expected_off = slot * case.page_size
      got = drisc_l1.read(case.stage_addr + slot * case.page_size, case.page_size)
      expected = expected_all[expected_off:expected_off + case.page_size]
      mismatch = next((i for i, (a, b) in enumerate(zip(got, expected)) if a != b), -1)
      if mismatch != -1:
        return False, f"slot={slot} final_page={final_page} mismatch={mismatch}"
    return True, f"checked_slots={slots}"

  slots = _case_stage_slots(case)
  for slot in range(slots):
    got = gddr.read(case.gddr_addr + slot * case.page_size, case.page_size)
    expected = pattern(case.page_size, 0xA0 + slot)
    mismatch = next((i for i, (a, b) in enumerate(zip(got, expected)) if a != b), -1)
    if mismatch != -1:
      return False, f"slot={slot} mismatch={mismatch}"
  return True, f"fixed_slots={slots}"


def run_case(args: argparse.Namespace, case: Case) -> Row:
  os.environ.pop("TT_USB", None)
  dev = PCIDevice(use_vfio=True)
  dram_core = select_dram_core(dev, args.bank, args.endpoint)
  use_poc_kernel = (
    case.mode == MODE_SINGLE
    and case.stage_addr == DEFAULT_STAGE_ADDR
  )
  code = (
    build_dma_kernel(
      op=OP_READ if case.direction == DIR_READ else OP_WRITE,
      gddr_addr=case.gddr_addr,
      size=case.page_size,
      iterations=case.pages,
      stream=case.stream,
      ctrl_attrs=case.ctrl_attrs,
      read_attr_base=case.read_attr_base,
      write_attr_base=case.write_attr_base,
    )
    if use_poc_kernel else build_kernel(case)
  )
  dev.set_power_state(True)
  try:
    gddr = TLBWindow(dev, start=dram_core, addr=0)
    drisc_l1 = TLBWindow(dev, start=dram_core, addr=DRISC_L1_NOC_ALIAS)
    regs = RegWindow(dev, dram_core)
    try:
      seed_for_case(gddr, drisc_l1, case)
      if use_poc_kernel:
        words = launch_poc_kernel(
          dram_core, drisc_l1, regs, code, args.timeout,
          magic=RESULT_MAGIC, label="DRISC GDDR DMA POC kernel",
        )
      else:
        words = launch_drisc(drisc_l1, regs, code, args.timeout)
      ok, verify_detail = verify_case(gddr, drisc_l1, case)
    finally:
      regs.close()
      drisc_l1.close()
      gddr.close()
  finally:
    dev.set_power_state(False)
    dev.close()

  if use_poc_kernel:
    start = _u64(words, 9)
    issue_done = _u64(words, 11)
    end = issue_done
    status0 = words[8] if case.stream == 0 else 0
    status1 = words[8] if case.stream == 1 else 0
  else:
    start = _u64(words, 16)
    issue_done = _u64(words, 18)
    end = _u64(words, 20)
    status0 = words[24]
    status1 = words[25]
  issue_cycles = _delta(start, issue_done)
  tail_cycles = _delta(issue_done, end)
  cycles = _delta(start, end)
  total = case.page_size * case.pages
  stream = "0,1" if case.mode == MODE_DUAL else str(case.stream)
  detail = (
    f"dram_core={dram_core} code_B={len(code)} status0=0x{status0:08x} "
    f"status1=0x{status1:08x} depth={case.pipe_depth if case.mode == MODE_PIPE else 1} "
    f"{'poc_kernel' if use_poc_kernel else 'local_kernel'} {verify_detail}"
  )
  return Row(
    direction=DIR_NAMES[case.direction],
    mode=MODE_NAMES[case.mode],
    page_bytes=case.page_size,
    pages=case.pages,
    total_bytes=total,
    stream=stream,
    cycles=cycles,
    issue_cycles=issue_cycles,
    tail_cycles=tail_cycles,
    bytes_per_cycle=total / cycles if cycles else 0.0,
    gbps=_gbps(total, cycles),
    ok=ok,
    detail=detail,
  )


def parse_int_list(text: str) -> list[int]:
  out = []
  for item in text.split(","):
    item = item.strip()
    if item:
      out.append(int(item, 0))
  if not out:
    raise argparse.ArgumentTypeError("list must not be empty")
  return out


def parse_names(text: str, allowed: dict[str, int], label: str) -> list[int]:
  out = []
  for item in text.split(","):
    item = item.strip()
    if not item:
      continue
    if item == "all":
      return list(allowed.values())
    if item not in allowed:
      raise argparse.ArgumentTypeError(f"unknown {label} {item!r}; choices: {','.join(allowed)}")
    out.append(allowed[item])
  if not out:
    raise argparse.ArgumentTypeError(f"{label} list must not be empty")
  return out


def build_cases(args: argparse.Namespace) -> list[Case]:
  cases = []
  directions = parse_names(args.directions, DIRECTIONS, "direction")
  modes = parse_names(args.modes, MODES, "mode")
  sizes = parse_int_list(args.sizes)
  for direction in directions:
    for mode in modes:
      if mode == MODE_PIPE and direction != DIR_READ:
        continue
      for page_size in sizes:
        pages = args.pages
        if mode == MODE_DUAL and pages % 2:
          pages += 1
        case = Case(
          direction=direction,
          mode=mode,
          page_size=page_size,
          pages=pages,
          stream=args.stream,
          gddr_addr=args.gddr_addr + args.gddr_offset,
          stage_addr=args.stage_addr + args.stage_offset,
          ctrl_attrs=args.ctrl_attrs,
          read_attr_base=args.read_attr_base,
          write_attr_base=args.write_attr_base,
          timeout_iters=args.timeout_iters,
          pipe_depth=args.pipe_depth,
        )
        validate_case(case)
        cases.append(case)
  return cases


def format_rows(rows: list[Row]) -> str:
  lines = [
    "| dir | mode | page B | pages | MiB | stream | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |",
    "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|",
  ]
  for row in rows:
    lines.append(
      f"| {row.direction} | {row.mode} | {row.page_bytes} | {row.pages} | "
      f"{row.total_bytes / (1024 * 1024):.3f} | {row.stream} | {row.cycles} | "
      f"{row.issue_cycles} | {row.tail_cycles} | {row.bytes_per_cycle:.3f} | "
      f"{row.gbps:.1f} | {row.ok} | {row.detail} |"
    )
  return "\n".join(lines)


def self_test() -> None:
  cases = [
    Case(DIR_READ, MODE_SINGLE, 16, 4, 0, 0x100000, DEFAULT_STAGE_ADDR, DMA_CTRL_ATTRS_BURST_255, DEFAULT_READ_ATTR_BASE, DEFAULT_WRITE_ATTR_BASE, 1000),
    Case(DIR_WRITE, MODE_SINGLE, 64, 3, 1, 0x110000, DEFAULT_STAGE_ADDR, DMA_CTRL_ATTRS_BURST_255, DEFAULT_READ_ATTR_BASE, DEFAULT_WRITE_ATTR_BASE, 1000),
    Case(DIR_READ, MODE_PIPE, 256, 6, 0, 0x120000, DEFAULT_STAGE_ADDR, DMA_CTRL_ATTRS_BURST_255, DEFAULT_READ_ATTR_BASE, DEFAULT_WRITE_ATTR_BASE, 1000, 2),
    Case(DIR_READ, MODE_PIPE, 256, 6, 0, 0x120000, DEFAULT_STAGE_ADDR, DMA_CTRL_ATTRS_BURST_255, DEFAULT_READ_ATTR_BASE, DEFAULT_WRITE_ATTR_BASE, 1000, 4),
    Case(DIR_READ, MODE_DUAL, 4096, 8, 0, 0x130000, DEFAULT_STAGE_ADDR, DMA_CTRL_ATTRS_BURST_255, DEFAULT_READ_ATTR_BASE, DEFAULT_WRITE_ATTR_BASE, 1000),
    Case(DIR_WRITE, MODE_DUAL, 4096, 8, 0, 0x140000, DEFAULT_STAGE_ADDR, DMA_CTRL_ATTRS_BURST_255, DEFAULT_READ_ATTR_BASE, DEFAULT_WRITE_ATTR_BASE, 1000),
  ]
  total_code = 0
  for case in cases:
    code = build_kernel(case)
    if not code:
      raise AssertionError(f"empty code for {case}")
    total_code += len(code)
  print(f"self-test passed: compiled {len(cases)} kernels, total_code_B={total_code}")


def main() -> None:
  parser = argparse.ArgumentParser(description="Microbenchmark DRISC GDDR DMA to/from DRISC L1.")
  parser.add_argument("--bank", type=int, default=0)
  parser.add_argument("--endpoint", type=int, default=0)
  parser.add_argument("--gddr-addr", type=lambda s: int(s, 0), default=0x100000)
  parser.add_argument("--gddr-offset", type=lambda s: int(s, 0), default=0)
  parser.add_argument("--stage-addr", type=lambda s: int(s, 0), default=DEFAULT_STAGE_ADDR)
  parser.add_argument("--stage-offset", type=lambda s: int(s, 0), default=0)
  parser.add_argument("--sizes", default="16,32,64,128,256,512,1024,2048,4096,8192,16384")
  parser.add_argument("--pages", type=int, default=256)
  parser.add_argument("--directions", default="read,write", help="comma list: read,write,all")
  parser.add_argument("--modes", default="single", help="comma list: single,pipe,dual,all; pipe/dual are experimental")
  parser.add_argument("--stream", type=int, default=0, help="single-stream id for single/pipe modes")
  parser.add_argument("--pipe-depth", type=int, default=2, help="max same-stream outstanding reads for pipe mode; power of two")
  parser.add_argument("--ctrl-attrs", type=lambda s: int(s, 0), default=DMA_CTRL_ATTRS_BURST_255)
  parser.add_argument("--read-attr-base", type=lambda s: int(s, 0), default=DEFAULT_READ_ATTR_BASE)
  parser.add_argument("--write-attr-base", type=lambda s: int(s, 0), default=DEFAULT_WRITE_ATTR_BASE)
  parser.add_argument("--timeout-iters", type=int, default=DEFAULT_TIMEOUT_ITERS)
  parser.add_argument("--timeout", type=float, default=10.0)
  parser.add_argument("--dry-run", action="store_true", help="compile planned kernels without opening hardware")
  parser.add_argument("--self-test", action="store_true", help="host-only compile checks")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("tensix", "drisc-gddr-dma.md"))
  args = parser.parse_args()

  if args.self_test:
    self_test()
    return

  cases = build_cases(args)
  if args.dry_run:
    total_code = 0
    for case in cases:
      code = build_kernel(case)
      total_code += len(code)
      print(
        f"dry-run dir={DIR_NAMES[case.direction]} mode={MODE_NAMES[case.mode]} "
        f"page={case.page_size} pages={case.pages} stream={case.stream} "
        f"depth={case.pipe_depth if case.mode == MODE_PIPE else 1} code_B={len(code)}"
      )
    print(f"dry-run passed: cases={len(cases)} total_code_B={total_code}")
    return

  rows = [run_case(args, case) for case in cases]
  table = format_rows(rows)
  print(table)
  if not args.no_report:
    args.report.parent.mkdir(parents=True, exist_ok=True)
    harness.append_report(args.report, "DRISC GDDR DMA", [
      f"Command: `{' '.join(sys.argv)}`",
      "Scope: DRISC DMA engine only, GDDR to/from DRISC local L1 staging slots",
      f"Clock assumption: {DEBUG_CLOCK_MHZ:.1f} MHz",
    ], table=table)
    print(f"appended {args.report}")
  if not all(row.ok for row in rows):
    raise SystemExit(1)


if __name__ == "__main__":
  main()
