#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
from asm import KernelBase
from device import Device
from drisc_gddr_dma_poc import (
  DEBUG_CLOCK_MHZ, DMA_CTRL_ATTRS_BURST_255, DMA_READ_STATUS_MASK, RESULT_MAGIC,
  STATUS_DONE, STATUS_STARTED, STATUS_TIMEOUT, STAGE_ADDR,
  TX_CTRL_TRANSFER_ATTRIBUTES, TX_READ_DST, TX_READ_SRC_HI, TX_READ_SRC_LO,
  TX_STREAM_STATUS, TX_TRANSFER_ATTRIBUTES, emit_poll_status, emit_read_wall_clock,
  build_dma_kernel, emit_dma_once, launch_drisc as launch_dma_poc, OP_READ, stream_reg,
)
from drisc_gddr_to_worker_poc import (
  ACK_SCRATCH_ADDR, MAX_NOC_CHUNK_BYTES, emit_dma_read_reg, emit_dma_read_wait_n,
  emit_init_drisc_noc_cmd_bufs, emit_posted_writes_flushed,
  emit_set_drisc_noc2axi_mode_all, emit_set_drisc_stream_mode_all,
  build_kernel as build_stage_poc_kernel, launch_drisc as launch_stage_poc,
)
from drisc_hello import (
  DRISC_FW_BASE, DRISC_L1_NOC_ALIAS, DRISC_RESET_PC, RegWindow,
  SOFT_RESET_0, SOFT_RESET_BRISC, select_dram_core,
)
from dsl import a0, a1, a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, s11, t0, t1, t2, t3, t4, t5, t6, zero
from pcie import PCIDevice, TLBWindow
from program import Dtype, Program
from ttk.mailbox import NcriscMailbox as NM
from ttk.noc import NOC, Noc, noc_xy
from ttk.tensix import TensixL1


DRISC_RESULT_ADDR = 0x1F000
DRISC_RESULT_WORDS = 16
DRISC_MAGIC = RESULT_MAGIC

NCRISC_RESULT_ADDR = 0x160000
NCRISC_RESULT_WORDS = 24
NCRISC_MAGIC = 0x43575254  # "CWRT"

MODE_DMA = 1
MODE_DMA2 = 2
MODE_STAGE = 3
MODE_SERIAL = 4
MODE_PIPE = 5
MODE_PIPE2 = 6
MODE_NAMES = {
  MODE_DMA: "drisc_dma",
  MODE_DMA2: "drisc_dma_2stream",
  MODE_STAGE: "drisc_stage",
  MODE_SERIAL: "drisc_dma_stage_serial",
  MODE_PIPE: "drisc_dma_stage_pipe",
  MODE_PIPE2: "drisc_dma_stage_pipe_2stream",
}

TILE_BYTES = Dtype.Float16_b.tile_size
DEFAULT_GDDR_ADDR = 0x100000
DEFAULT_WORKER_ADDR = TensixL1.DATA_BUFFER_SPACE_BASE
DEFAULT_NCRISC_TILES = 1024
DEFAULT_DRISC_PAGES = 32


class DriscOverlapKernel(KernelBase, Noc):
  pass


class OutputWriteKernel(KernelBase, Noc):
  def rta_ptr(self, mailbox_addr: int, *, out=s11):
    return self.read32(out, mailbox_addr)

  def arg(self, dst, index: int, *, ptr=s11):
    return self.lw(dst, ptr, index * 4)


@dataclass(frozen=True)
class BenchRow:
  mode: str
  page_bytes: int
  pages: int
  total_bytes: int
  cycles: int
  issue_cycles: int
  tail_cycles: int
  bytes_per_cycle: float
  gbps: float
  ok: bool
  detail: str


def _u64(words: tuple[int, ...], lo: int) -> int:
  return words[lo] | (words[lo + 1] << 32)


def _delta(start: int, end: int) -> int:
  return (end - start) & ((1 << 64) - 1)


def _gbps(byte_count: int, cycles: int) -> float:
  return (byte_count / cycles) * DEBUG_CLOCK_MHZ / 1000.0 if cycles else 0.0


def pattern(size: int, seed: int) -> bytes:
  return bytes(((i * 17 + seed) ^ (i >> 4)) & 0xFF for i in range(size))


def emit_drisc_header(fw: KernelBase, *, mode: int, page_size: int, pages: int, gddr_addr: int, status: int):
  for idx, value in enumerate((
    DRISC_MAGIC, mode, page_size, gddr_addr & 0xFFFFFFFF, (gddr_addr >> 32) & 0xFFFFFFFF, STAGE_ADDR, status, pages,
  )):
    fw.write32(DRISC_RESULT_ADDR + idx * 4, value, tmp_addr=t0, tmp_val=t1)
  for idx in range(8, DRISC_RESULT_WORDS):
    fw.write32(DRISC_RESULT_ADDR + idx * 4, 0, tmp_addr=t0, tmp_val=t1)
  return fw


def emit_dma_read_start(fw: KernelBase, *, src_lo, src_hi: int, dst_l1, size: int, stream: int):
  fw.write32(stream_reg(stream, TX_READ_SRC_LO), src_lo, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_SRC_HI), src_hi, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_DST), dst_l1, tmp_addr=t0, tmp_val=t1)
  return fw.write32(stream_reg(stream, TX_TRANSFER_ATTRIBUTES), 0x83000000 | (size >> 4), tmp_addr=t0, tmp_val=t1)


def emit_stage_slot_for_page(fw: KernelBase, *, page_reg, page_size: int, slots: int, out):
  fw.li(t0, slots)
  fw.remu(out, page_reg, t0)
  fw.li(t0, page_size)
  fw.mul(out, out, t0)
  fw.li(t0, STAGE_ADDR)
  return fw.add(out, out, t0)


def emit_worker_dst_for_page(fw: KernelBase, *, page_reg, page_size: int, ring_pages: int, worker_addr: int, out):
  fw.li(t0, ring_pages)
  fw.remu(out, page_reg, t0)
  fw.li(t0, page_size)
  fw.mul(out, out, t0)
  fw.li(t0, worker_addr)
  return fw.add(out, out, t0)


def emit_stage_write_reg(
  fw: DriscOverlapKernel, *, noc: int, page_size: int, src_reg, dst_reg, worker_coord: int,
):
  chunks = (page_size + MAX_NOC_CHUNK_BYTES - 1) // MAX_NOC_CHUNK_BYTES
  fw.read32(s0, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(s0, s0, chunks)
  for off in range(0, page_size, MAX_NOC_CHUNK_BYTES):
    chunk = min(MAX_NOC_CHUNK_BYTES, page_size - off)
    if off:
      fw.li(t5, off)
      fw.add(a2, src_reg, t5)
      fw.add(a3, dst_reg, t5)
    else:
      fw.mv(a2, src_reg)
      fw.mv(a3, dst_reg)
    fw.li(a4, worker_coord)
    fw.li(a5, chunk)
    fw.noc_write(noc, 0, a2, a3, 0, a4, a5, posted=True, a=t3, v=t4)
  return emit_posted_writes_flushed(fw, noc=noc, target=s0, addr=t3, val=t4)


def emit_stage_current_page(
  fw: DriscOverlapKernel, *, noc: int, page_size: int, ring_pages: int, worker_addr: int,
  worker_coord: int, page_reg, stage_slots: int,
):
  emit_stage_slot_for_page(fw, page_reg=page_reg, page_size=page_size, slots=stage_slots, out=s4)
  emit_worker_dst_for_page(fw, page_reg=page_reg, page_size=page_size, ring_pages=ring_pages, worker_addr=worker_addr, out=s5)
  return emit_stage_write_reg(fw, noc=noc, page_size=page_size, src_reg=s4, dst_reg=s5, worker_coord=worker_coord)


def emit_finish_drisc(fw: KernelBase, *, mode: int):
  emit_read_wall_clock(fw, a4, a5)
  fw.write32(DRISC_RESULT_ADDR + 6 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  fw.read32(t1, stream_reg(0, TX_STREAM_STATUS), tmp_addr=t0)
  fw.write32(DRISC_RESULT_ADDR + 8 * 4, t1, tmp_addr=t0, tmp_val=t2)
  fw.read32(t1, stream_reg(1, TX_STREAM_STATUS), tmp_addr=t0)
  fw.write32(DRISC_RESULT_ADDR + 15 * 4, t1, tmp_addr=t0, tmp_val=t2)
  for idx, reg in enumerate((a2, a3, a6, a7, a4, a5), start=9):
    fw.write32(DRISC_RESULT_ADDR + idx * 4, reg, tmp_addr=t0, tmp_val=t2)
  spin = fw._new_label(f"drisc_mode_{mode}_done_spin")
  fw.label(spin)
  return fw.j(spin)


def build_drisc_kernel(
  *, mode: int, gddr_addr: int, page_size: int, pages: int, worker_addr: int,
  worker_coord: int, noc: int, ring_pages: int,
) -> bytes:
  if mode not in MODE_NAMES:
    raise ValueError(f"unknown mode {mode}")
  if page_size <= 0 or page_size % 16:
    raise ValueError("page_size must be a positive multiple of 16")
  if pages <= 0:
    raise ValueError("pages must be positive")
  if noc not in (0, 1):
    raise ValueError("noc must be 0 or 1")
  if ring_pages <= 0:
    raise ValueError("ring_pages must be positive")
  stage_slots = 4 if mode == MODE_PIPE2 else 2
  if mode in (MODE_DMA, MODE_STAGE):
    stage_slots = 1
  if STAGE_ADDR + stage_slots * page_size > ACK_SCRATCH_ADDR:
    raise ValueError(f"{stage_slots} stage slots of {page_size} bytes do not fit DRISC L1")
  if mode in (MODE_DMA2, MODE_PIPE2) and pages % 2:
    raise ValueError("two-stream modes require an even page count")
  total_bytes = page_size * pages
  if (gddr_addr & 0xFFFFFFFF) + total_bytes >= (1 << 32):
    raise ValueError("this focused harness requires the GDDR span to stay within one 32-bit low-address window")

  fw = DriscOverlapKernel(base_addr=DRISC_FW_BASE)
  emit_drisc_header(fw, mode=mode, page_size=page_size, pages=pages, gddr_addr=gddr_addr, status=STATUS_STARTED)
  fw.write32(TX_CTRL_TRANSFER_ATTRIBUTES, DMA_CTRL_ATTRS_BURST_255, tmp_addr=t0, tmp_val=t1)
  fw.write32(DRISC_RESULT_ADDR + 15 * 4, 0xD0000001, tmp_addr=t0, tmp_val=t1)
  if mode in (MODE_STAGE, MODE_SERIAL, MODE_PIPE, MODE_PIPE2):
    emit_set_drisc_stream_mode_all(fw)
    emit_init_drisc_noc_cmd_bufs(fw)
  fw.write32(DRISC_RESULT_ADDR + 15 * 4, 0xD0000002, tmp_addr=t0, tmp_val=t1)
  emit_read_wall_clock(fw, a2, a3)
  fw.write32(DRISC_RESULT_ADDR + 15 * 4, 0xD0000003, tmp_addr=t0, tmp_val=t1)
  gddr_hi = (gddr_addr >> 32) & 0xFFFFFFFF

  if mode == MODE_DMA:
    for page in range(pages):
      if page == 0:
        fw.write32(DRISC_RESULT_ADDR + 15 * 4, 0xD0000010, tmp_addr=t0, tmp_val=t1)
      emit_dma_once(fw, op=OP_READ, gddr_addr=gddr_addr + page * page_size, size=page_size, stream=0)

  elif mode == MODE_DMA2:
    for page in range(0, pages, 2):
      emit_dma_read_start(fw, src_lo=gddr_addr + page * page_size, src_hi=gddr_hi, dst_l1=STAGE_ADDR, size=page_size, stream=0)
      emit_dma_read_start(fw, src_lo=gddr_addr + (page + 1) * page_size, src_hi=gddr_hi, dst_l1=STAGE_ADDR + page_size, size=page_size, stream=1)
      emit_poll_status(fw, stream=0, mask=DMA_READ_STATUS_MASK, timeout_iters=20_000_000)
      emit_poll_status(fw, stream=1, mask=DMA_READ_STATUS_MASK, timeout_iters=20_000_000)

  elif mode == MODE_STAGE:
    for page in range(pages):
      dst_page = page % ring_pages
      fw.li(s4, STAGE_ADDR)
      fw.li(s5, worker_addr + dst_page * page_size)
      emit_stage_write_reg(fw, noc=noc, page_size=page_size, src_reg=s4, dst_reg=s5, worker_coord=worker_coord)

  elif mode == MODE_SERIAL:
    for page in range(pages):
      slot = page & 1
      dst_page = page % ring_pages
      emit_dma_read_start(
        fw, src_lo=gddr_addr + page * page_size, src_hi=gddr_hi,
        dst_l1=STAGE_ADDR + slot * page_size, size=page_size, stream=0,
      )
      emit_poll_status(fw, stream=0, mask=DMA_READ_STATUS_MASK, timeout_iters=20_000_000)
      fw.li(s4, STAGE_ADDR + slot * page_size)
      fw.li(s5, worker_addr + dst_page * page_size)
      emit_stage_write_reg(fw, noc=noc, page_size=page_size, src_reg=s4, dst_reg=s5, worker_coord=worker_coord)

  elif mode == MODE_PIPE:
    emit_dma_read_start(fw, src_lo=gddr_addr, src_hi=gddr_hi, dst_l1=STAGE_ADDR, size=page_size, stream=0)
    for page in range(pages):
      if page + 1 < pages:
        next_slot = (page + 1) & 1
        emit_dma_read_start(
          fw, src_lo=gddr_addr + (page + 1) * page_size, src_hi=gddr_hi,
          dst_l1=STAGE_ADDR + next_slot * page_size, size=page_size, stream=0,
        )
        emit_dma_read_wait_n(fw, stream=0, max_outstanding=1)
      else:
        emit_dma_read_wait_n(fw, stream=0, max_outstanding=0)
      slot = page & 1
      dst_page = page % ring_pages
      fw.li(s4, STAGE_ADDR + slot * page_size)
      fw.li(s5, worker_addr + dst_page * page_size)
      emit_stage_write_reg(fw, noc=noc, page_size=page_size, src_reg=s4, dst_reg=s5, worker_coord=worker_coord)

  elif mode == MODE_PIPE2:
    emit_dma_read_start(fw, src_lo=gddr_addr, src_hi=gddr_hi, dst_l1=STAGE_ADDR, size=page_size, stream=0)
    emit_dma_read_start(fw, src_lo=gddr_addr + page_size, src_hi=gddr_hi, dst_l1=STAGE_ADDR + page_size, size=page_size, stream=1)
    for page in range(pages):
      if page + 2 < pages:
        next_page = page + 2
        next_stream = next_page & 1
        emit_dma_read_start(
          fw, src_lo=gddr_addr + next_page * page_size, src_hi=gddr_hi,
          dst_l1=STAGE_ADDR + (next_page & 3) * page_size, size=page_size, stream=next_stream,
        )
      stream = page & 1
      emit_poll_status(fw, stream=stream, mask=DMA_READ_STATUS_MASK, timeout_iters=20_000_000)
      slot = page & 3
      dst_page = page % ring_pages
      fw.li(s4, STAGE_ADDR + slot * page_size)
      fw.li(s5, worker_addr + dst_page * page_size)
      emit_stage_write_reg(fw, noc=noc, page_size=page_size, src_reg=s4, dst_reg=s5, worker_coord=worker_coord)

  emit_read_wall_clock(fw, a6, a7)
  if mode in (MODE_STAGE, MODE_SERIAL, MODE_PIPE, MODE_PIPE2):
    emit_set_drisc_noc2axi_mode_all(fw)
  emit_finish_drisc(fw, mode=mode)
  return fw.compile()[0].data


def launch_drisc(l1: TLBWindow, regs: RegWindow, code: bytes, timeout: float) -> tuple[int, ...]:
  l1.write(DRISC_RESULT_ADDR, b"\0" * (DRISC_RESULT_WORDS * 4))
  l1.write(DRISC_FW_BASE, code)
  reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
  regs.write32(DRISC_RESET_PC, DRISC_FW_BASE)
  time.sleep(0.01)
  regs.write32(SOFT_RESET_0, reset_state & ~SOFT_RESET_BRISC)

  deadline = time.time() + timeout
  words = (0,) * DRISC_RESULT_WORDS
  while time.time() < deadline:
    words = struct.unpack("<" + "I" * DRISC_RESULT_WORDS, l1.read(DRISC_RESULT_ADDR, DRISC_RESULT_WORDS * 4))
    if words[0] == DRISC_MAGIC and words[6] in (STATUS_DONE, STATUS_TIMEOUT):
      break
    time.sleep(0.001)

  live0 = regs.read32(stream_reg(0, TX_STREAM_STATUS))
  live1 = regs.read32(stream_reg(1, TX_STREAM_STATUS))
  final_reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, final_reset_state | SOFT_RESET_BRISC)
  if words[0] != DRISC_MAGIC or words[6] != STATUS_DONE:
    aux = struct.unpack("<" + "I" * 16, l1.read(0x1F000, 16 * 4))
    raise TimeoutError(
      f"DRISC benchmark did not finish; words={[hex(w) for w in words[:16]]} "
      f"aux={[hex(w) for w in aux]} live_stream0=0x{live0:08x} live_stream1=0x{live1:08x}"
    )
  return words


def run_drisc_case(args: argparse.Namespace, mode: int) -> BenchRow:
  os.environ.pop("TT_USB", None)
  dev = PCIDevice(use_vfio=True)
  dram_core = select_dram_core(dev, args.bank, args.endpoint)
  info = dev.board_info(fast_dispatch=True)
  worker_core = info.program_cores[args.worker_index]
  worker_coord = noc_xy(*worker_core)
  worker_span = args.ring_pages * args.page_size
  stage_slots = 4 if mode == MODE_PIPE2 else 2
  if mode in (MODE_DMA, MODE_STAGE):
    stage_slots = 1

  dev.set_power_state(True)
  try:
    gddr = TLBWindow(dev, start=dram_core, addr=0)
    drisc_l1 = TLBWindow(dev, start=dram_core, addr=DRISC_L1_NOC_ALIAS)
    worker_l1 = TLBWindow(dev, start=worker_core)
    regs = RegWindow(dev, dram_core)
    try:
      if mode != MODE_STAGE:
        total = args.page_size * args.pages
        gddr.write(args.gddr_addr, pattern(total, 0x34))
      drisc_l1.write(STAGE_ADDR, pattern(stage_slots * args.page_size, 0x87))
      if mode != MODE_DMA and mode != MODE_DMA2:
        worker_l1.write(args.worker_addr, b"\0" * worker_span)
      if mode == MODE_DMA:
        words = launch_dma_poc(
          dev, dram_core, drisc_l1, regs,
          build_dma_kernel(op=OP_READ, gddr_addr=args.gddr_addr, size=args.page_size, iterations=args.pages),
          args.timeout,
        )
        ok = words[6] == STATUS_DONE and drisc_l1.read(STAGE_ADDR, args.page_size) == pattern(args.page_size, 0x34)
      elif mode == MODE_STAGE:
        words = launch_stage_poc(
          dram_core, drisc_l1, regs,
          build_stage_poc_kernel(
            gddr_addr=args.gddr_addr,
            size=args.page_size * args.pages,
            worker_addr=args.worker_addr,
            worker_coord=worker_coord,
            noc=args.noc,
            stream=0,
            skip_dma=True,
          ),
          args.timeout,
        )
        ok = words[6] == STATUS_DONE and worker_l1.read(args.worker_addr, min(args.page_size, 64)) != (b"\0" * min(args.page_size, 64))
      else:
        words = launch_drisc(
          drisc_l1,
          regs,
          build_drisc_kernel(
            mode=mode,
            gddr_addr=args.gddr_addr,
            page_size=args.page_size,
            pages=args.pages,
            worker_addr=args.worker_addr,
            worker_coord=worker_coord,
            noc=args.noc,
            ring_pages=args.ring_pages,
          ),
          args.timeout,
        )
        ok = words[6] == STATUS_DONE
        if mode not in (MODE_DMA, MODE_DMA2):
          ok = ok and worker_l1.read(args.worker_addr, min(args.page_size, 64)) != (b"\0" * min(args.page_size, 64))
    finally:
      regs.close()
      worker_l1.close()
      drisc_l1.close()
      gddr.close()
  finally:
    dev.set_power_state(False)
    dev.close()

  if mode == MODE_DMA:
    start = _u64(words, 9)
    issue_done = _u64(words, 11)
    end = issue_done
  elif mode == MODE_STAGE:
    start = issue_done = end = 0
  else:
    start = _u64(words, 9)
    issue_done = _u64(words, 11)
    end = _u64(words, 13)
  cycles = _delta(start, end)
  issue_cycles = _delta(start, issue_done)
  tail_cycles = _delta(issue_done, end)
  total_bytes = args.page_size * args.pages
  return BenchRow(
    mode=MODE_NAMES[mode],
    page_bytes=args.page_size,
    pages=args.pages,
    total_bytes=total_bytes,
    cycles=cycles,
    issue_cycles=issue_cycles,
    tail_cycles=tail_cycles,
    bytes_per_cycle=total_bytes / cycles if cycles else 0.0,
    gbps=_gbps(total_bytes, cycles),
    ok=ok,
    detail=f"dram_core={dram_core} worker_core={worker_core} noc={args.noc} stream0=0x{words[8]:08x} stream1=0x{words[15]:08x}",
  )


def emit_ncrisc_result_header(fw: KernelBase, *, tile_count: int, status: int):
  for idx, value in enumerate((NCRISC_MAGIC, tile_count, TILE_BYTES, status, 0, 0, 0, 0)):
    fw.write32(NCRISC_RESULT_ADDR + idx * 4, value, tmp_addr=t0, tmp_val=t1)
  for idx in range(8, NCRISC_RESULT_WORDS):
    fw.write32(NCRISC_RESULT_ADDR + idx * 4, 0, tmp_addr=t0, tmp_val=t1)
  return fw


def emit_output_write_state_setup(fw: OutputWriteKernel):
  fw.noc_wait_cmd_ready(1, 0, addr=t0, val=t1)
  fw.noc_cmd_reg(1, 0, NOC.CTRL, NOC.CMD_WR_FIELD, addr=t0, tmp=t1)
  fw.noc_cmd_reg(1, 0, NOC.RET_ADDR_MID, 0, addr=t0, tmp=t1)
  fw.li(t6, TILE_BYTES)
  fw.noc_cmd_reg(1, 0, NOC.AT_LEN_BE, t6, addr=t0, tmp=t1)
  return fw.noc_cmd_reg(1, 0, NOC.AT_LEN_BE_1, 0, addr=t0, tmp=t1)


def emit_output_write_stateful(fw: OutputWriteKernel, *, src, dst_lo, dst_coord):
  fw.noc_wait_cmd_ready(1, 0, addr=t0, val=a5)
  fw.noc_cmd_reg(1, 0, NOC.TARG_ADDR_LO, src, addr=t0, tmp=a5)
  fw.noc_cmd_reg(1, 0, NOC.RET_ADDR_LO, dst_lo, addr=t0, tmp=a5)
  fw.noc_cmd_reg(1, 0, NOC.RET_ADDR_COORDINATE, dst_coord, addr=t0, tmp=a5)
  return fw.noc_cmd_reg(1, 0, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=t0, tmp=a5)


def build_ncrisc_output_kernel(*, tile_count: int, source_tiles: int) -> OutputWriteKernel:
  if tile_count <= 0:
    raise ValueError("tile_count must be positive")
  if source_tiles <= 0:
    raise ValueError("source_tiles must be positive")
  src_span = source_tiles * TILE_BYTES
  if DEFAULT_WORKER_ADDR + src_span >= NCRISC_RESULT_ADDR:
    raise ValueError("source tile ring overlaps NCRISC result area")

  fw = OutputWriteKernel()
  fw.rta_ptr(NM.RTA_L1_BASE_PTR)
  emit_ncrisc_result_header(fw, tile_count=tile_count, status=STATUS_STARTED)
  fw.arg(s0, 0)  # DRAM base address.
  fw.arg(s1, 1)  # C logical tile start.
  fw.arg(s2, 2)  # DRAM bank count.
  fw.arg(s3, 3)  # tile count.

  fw.li(t0, DEFAULT_WORKER_ADDR)
  fw.li(t1, src_span // 4)
  fw.li(t2, 0xC0000000)
  seed_loop = fw._new_label("seed_src")
  seed_done = fw._new_label("seed_src_done")
  fw.label(seed_loop)
  fw.beq(t1, zero, seed_done)
  fw.sw(t2, t0, 0)
  fw.addi(t0, t0, 4)
  fw.addi(t2, t2, 4)
  fw.addi(t1, t1, -1)
  fw.j(seed_loop)
  fw.label(seed_done)
  fw.fence()

  emit_output_write_state_setup(fw)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(s7, t0, 0)
  fw.add(s7, s7, s3)
  emit_read_wall_clock(fw, a2, a3)
  fw.li(s4, 0)
  issue_loop = fw._new_label("output_issue")
  issue_done = fw._new_label("output_issue_done")
  fw.label(issue_loop)
  fw.bgeu(s4, s3, issue_done)
  fw.mv(a0, s0)
  fw.add(a1, s1, s4)
  fw.mv(a2, s2)
  fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)
  fw.li(t0, source_tiles)
  fw.remu(t1, s4, t0)
  fw.li(t0, TILE_BYTES)
  fw.mul(t1, t1, t0)
  fw.li(t0, DEFAULT_WORKER_ADDR)
  fw.add(t5, t0, t1)
  emit_output_write_stateful(fw, src=t5, dst_lo=a0, dst_coord=a2)
  fw.addi(s4, s4, 1)
  fw.j(issue_loop)
  fw.label(issue_done)
  emit_read_wall_clock(fw, a6, a7)
  fw.noc_write_barrier(1, s7)
  emit_read_wall_clock(fw, a4, a5)
  fw.write32(NCRISC_RESULT_ADDR + 3 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(t1, t0, 0)
  fw.write32(NCRISC_RESULT_ADDR + 4 * 4, t1, tmp_addr=t0, tmp_val=t2)
  for idx, reg in enumerate((a2, a3, a6, a7, a4, a5), start=8):
    fw.write32(NCRISC_RESULT_ADDR + idx * 4, reg, tmp_addr=t0, tmp_val=t2)
  return fw.ret()


def build_ncrisc_program(*, c_addr: int, tile_count: int, num_banks: int, source_tiles: int) -> Program:
  empty = KernelBase().ret()
  ncrisc = build_ncrisc_output_kernel(tile_count=tile_count, source_tiles=source_tiles)
  ncrisc.rta(lambda _x, _y: [c_addr, 0, num_banks, tile_count])
  program = Program(
    brisc=empty,
    ncrisc=ncrisc,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    num_cores=1,
  )
  program.name = f"microbench_ncrisc_output_tiles{tile_count}"
  return program


def run_ncrisc_output_case(args: argparse.Namespace) -> BenchRow:
  os.environ.pop("TT_USB", None)
  with harness.open_device() as device:
    c_buf = device.dram.alloc(args.ncrisc_tiles, Dtype.Float16_b, name="ncrisc_output_microbench")
    core = device.cores[0]
    with TLBWindow(device.dev, start=core) as win:
      win.write(NCRISC_RESULT_ADDR, b"\0" * (NCRISC_RESULT_WORDS * 4))
    timings = device.run(build_ncrisc_program(
      c_addr=c_buf.addr,
      tile_count=args.ncrisc_tiles,
      num_banks=len(device.dram.bank_tiles),
      source_tiles=args.source_tiles,
    ))
    with TLBWindow(device.dev, start=core) as win:
      words = struct.unpack("<" + "I" * NCRISC_RESULT_WORDS, win.read(NCRISC_RESULT_ADDR, NCRISC_RESULT_WORDS * 4))

  if words[0] != NCRISC_MAGIC or words[3] != STATUS_DONE:
    raise RuntimeError(f"NCRISC output benchmark failed; words={[hex(w) for w in words[:16]]}")
  start = _u64(words, 8)
  issue_done = _u64(words, 10)
  end = _u64(words, 12)
  cycles = _delta(start, end)
  issue_cycles = _delta(start, issue_done)
  tail_cycles = _delta(issue_done, end)
  total_bytes = args.ncrisc_tiles * TILE_BYTES
  detail = f"core={core} noc=1 ack_counter={words[4]}"
  if timings:
    detail += f" host_run_us={sum(t['us'] for t in timings):.1f}"
  return BenchRow(
    mode="ncrisc_output_stateful",
    page_bytes=TILE_BYTES,
    pages=args.ncrisc_tiles,
    total_bytes=total_bytes,
    cycles=cycles,
    issue_cycles=issue_cycles,
    tail_cycles=tail_cycles,
    bytes_per_cycle=total_bytes / cycles if cycles else 0.0,
    gbps=_gbps(total_bytes, cycles),
    ok=True,
    detail=detail,
  )


def print_rows(rows: list[BenchRow]) -> None:
  print("| mode | page B | pages | MiB | cycles | issue cyc | tail cyc | B/cyc | GB/s | ok | detail |")
  print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
  for row in rows:
    print(
      f"| {row.mode} | {row.page_bytes} | {row.pages} | {row.total_bytes / (1024 * 1024):.2f} | "
      f"{row.cycles} | {row.issue_cycles} | {row.tail_cycles} | {row.bytes_per_cycle:.3f} | "
      f"{row.gbps:.1f} | {row.ok} | {row.detail} |"
    )


def parse_modes(text: str) -> list[int]:
  by_name = {name: mode for mode, name in MODE_NAMES.items()}
  aliases = {
    "dma": MODE_DMA,
    "dma2": MODE_DMA2,
    "stage": MODE_STAGE,
    "serial": MODE_SERIAL,
    "pipe": MODE_PIPE,
    "pipe2": MODE_PIPE2,
  }
  out = []
  for item in text.split(","):
    item = item.strip()
    if not item:
      continue
    if item in by_name:
      out.append(by_name[item])
    elif item in aliases:
      out.append(aliases[item])
    else:
      raise argparse.ArgumentTypeError(f"unknown DRISC mode {item!r}")
  return out


def main() -> None:
  parser = argparse.ArgumentParser(description="Focused Blackhole DRISC DMA/staging overlap and NCRISC C-output write microbench.")
  parser.add_argument("--bank", type=int, default=0)
  parser.add_argument("--endpoint", type=int, default=0)
  parser.add_argument("--worker-index", type=int, default=0)
  parser.add_argument("--gddr-addr", type=lambda s: int(s, 0), default=DEFAULT_GDDR_ADDR)
  parser.add_argument("--worker-addr", type=lambda s: int(s, 0), default=DEFAULT_WORKER_ADDR)
  parser.add_argument("--page-size", type=int, default=TILE_BYTES)
  parser.add_argument("--pages", type=int, default=DEFAULT_DRISC_PAGES)
  parser.add_argument("--ring-pages", type=int, default=32)
  parser.add_argument("--noc", type=int, default=0)
  parser.add_argument("--timeout", type=float, default=10.0)
  parser.add_argument("--modes", type=parse_modes, default=parse_modes("dma,stage"))
  parser.add_argument("--ncrisc-output", action="store_true")
  parser.add_argument("--ncrisc-tiles", type=int, default=DEFAULT_NCRISC_TILES)
  parser.add_argument("--source-tiles", type=int, default=16)
  parser.add_argument("--only", choices=("all", "drisc", "ncrisc"), default="drisc")
  args = parser.parse_args()

  if args.worker_addr + args.ring_pages * args.page_size > TensixL1.SIZE:
    raise ValueError("worker ring does not fit L1")
  rows: list[BenchRow] = []
  if args.only in ("all", "drisc"):
    for mode in args.modes:
      rows.append(run_drisc_case(args, mode))
  if args.only in ("all", "ncrisc") or args.ncrisc_output:
    rows.append(run_ncrisc_output_case(args))
  print_rows(rows)


if __name__ == "__main__":
  main()
