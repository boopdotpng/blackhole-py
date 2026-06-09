#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import struct
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

from asm import KernelBase
from dsl import a2, a3, a4, a5, a6, a7, s0, s1, t0, t1, t2, t3, t4, t5, zero
from drisc_hello import (
  DRISC_FW_BASE, DRISC_L1_NOC_ALIAS, DRISC_RESET_PC, RegWindow,
  SOFT_RESET_0, SOFT_RESET_BRISC, select_dram_core,
)
from pcie import PCIDevice, TLBWindow


RESULT_ADDR = 0x1F000
STAGE_ADDR = 0x6000
MAX_STAGE_BYTES = RESULT_ADDR - STAGE_ADDR
RESULT_WORDS = 16
RESULT_MAGIC = 0x444D4150  # "DMAP"
STATUS_STARTED = 1
STATUS_DONE = 2
STATUS_TIMEOUT = 3

OP_READ = 1
OP_WRITE = 2

TX_STREAM_BASE = 0xFC000000
TX_STREAM_SIZE = 0x100
TX_CTRL_BASE = 0xFC001000

TX_CTRL_TRANSFER_ATTRIBUTES = TX_CTRL_BASE + 0x04

TX_STREAM_STATUS = 0x00
TX_WRITE_SRC = 0x10
TX_WRITE_DST_LO = 0x14
TX_WRITE_DST_HI = 0x18
TX_READ_SRC_LO = 0x30
TX_READ_SRC_HI = 0x34
TX_READ_DST = 0x38
TX_TRANSFER_ATTRIBUTES = 0x50

DMA_CTRL_ATTRS_BURST_255 = 0x0003FF01
DMA_READ_STATUS_MASK = 0x0000FF10
DMA_WRITE_STATUS_MASK = 0xF00F0009
DEBUG_CLOCK_MHZ = 1350.0
RISCV_DEBUG_REG_WALL_CLOCK_L = 0xFFB121F0
RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F8


def stream_reg(stream: int, offset: int) -> int:
  return TX_STREAM_BASE + stream * TX_STREAM_SIZE + offset


def emit_read_wall_clock(fw: KernelBase, lo, hi, *, addr=a7, hi2=a6):
  retry = fw._new_label("wall_clock_retry")
  fw.li(addr, RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.label(retry)
  fw.lw(hi, addr, 0)
  fw.lw(lo, addr, RISCV_DEBUG_REG_WALL_CLOCK_L - RISCV_DEBUG_REG_WALL_CLOCK_H)
  fw.lw(hi2, addr, 0)
  fw.bne(hi, hi2, retry)
  return fw


def emit_result_header(
  fw: KernelBase, *, op: int, size: int, gddr_addr: int, status: int, iterations: int,
):
  values = (
    RESULT_MAGIC, op, size, gddr_addr & 0xFFFFFFFF,
    (gddr_addr >> 32) & 0xFFFFFFFF, STAGE_ADDR, status, iterations,
  )
  for idx, value in enumerate(values):
    fw.write32(RESULT_ADDR + idx * 4, value, tmp_addr=t0, tmp_val=t1)


def emit_poll_status(fw: KernelBase, *, stream: int, mask: int, timeout_iters: int):
  loop = fw._new_label("dma_poll")
  done = fw._new_label("dma_poll_done")
  timeout = fw._new_label("dma_poll_timeout")
  fw.li(t3, timeout_iters)
  fw.li(t2, mask)
  fw.label(loop)
  fw.beq(t3, zero, timeout)
  fw.read32(t0, stream_reg(stream, TX_STREAM_STATUS), tmp_addr=t4)
  fw.and_(t0, t0, t2)
  fw.beq(t0, zero, done)
  fw.addi(t3, t3, -1)
  fw.j(loop)
  fw.label(timeout)
  fw.write32(RESULT_ADDR + 6 * 4, STATUS_TIMEOUT, tmp_addr=t4, tmp_val=t1)
  fw.write32(RESULT_ADDR + 8 * 4, t0, tmp_addr=t4, tmp_val=t1)
  spin = fw._new_label("dma_timeout_spin")
  fw.label(spin)
  fw.j(spin)
  fw.label(done)


def emit_dma_once(fw: KernelBase, *, op: int, gddr_addr, size: int, stream: int):
  size_words = size >> 4
  if op == OP_READ:
    fw.write32(stream_reg(stream, TX_READ_SRC_LO), gddr_addr & 0xFFFFFFFF, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_READ_SRC_HI), (gddr_addr >> 32) & 0xFFFFFFFF, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_READ_DST), STAGE_ADDR, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_TRANSFER_ATTRIBUTES), 0x83000000 | size_words, tmp_addr=t0, tmp_val=t1)
    emit_poll_status(fw, stream=stream, mask=DMA_READ_STATUS_MASK, timeout_iters=20_000_000)
  else:
    fw.write32(stream_reg(stream, TX_WRITE_SRC), STAGE_ADDR, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_WRITE_DST_LO), gddr_addr & 0xFFFFFFFF, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_WRITE_DST_HI), (gddr_addr >> 32) & 0xFFFFFFFF, tmp_addr=t0, tmp_val=t1)
    fw.write32(stream_reg(stream, TX_TRANSFER_ATTRIBUTES), 0x10000000 | size_words, tmp_addr=t0, tmp_val=t1)
    emit_poll_status(fw, stream=stream, mask=DMA_WRITE_STATUS_MASK, timeout_iters=20_000_000)


def build_dma_kernel(*, op: int, gddr_addr: int, size: int, iterations: int = 1, stream: int = 0) -> bytes:
  if op not in (OP_READ, OP_WRITE):
    raise ValueError(f"bad op {op}")
  if size <= 0 or size % 16:
    raise ValueError("size must be a positive multiple of 16")
  if size > MAX_STAGE_BYTES:
    raise ValueError(f"size must fit DRISC stage buffer, max {MAX_STAGE_BYTES}")
  if iterations <= 0:
    raise ValueError("iterations must be positive")

  fw = KernelBase(base_addr=DRISC_FW_BASE)
  emit_result_header(fw, op=op, size=size, gddr_addr=gddr_addr, status=STATUS_STARTED, iterations=iterations)
  fw.write32(TX_CTRL_TRANSFER_ATTRIBUTES, DMA_CTRL_ATTRS_BURST_255, tmp_addr=t0, tmp_val=t1)

  emit_read_wall_clock(fw, a2, a3)
  fw.li(s0, iterations)
  loop = fw._new_label("dma_loop")
  done = fw._new_label("dma_loop_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  emit_dma_once(fw, op=op, gddr_addr=gddr_addr, size=size, stream=stream)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  emit_read_wall_clock(fw, a4, a5)

  fw.write32(RESULT_ADDR + 6 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  fw.read32(t1, stream_reg(stream, TX_STREAM_STATUS), tmp_addr=t0)
  fw.write32(RESULT_ADDR + 8 * 4, t1, tmp_addr=t0, tmp_val=t2)
  for idx, reg in enumerate((a2, a3, a4, a5), start=9):
    fw.write32(RESULT_ADDR + idx * 4, reg, tmp_addr=t0, tmp_val=t2)
  spin = fw._new_label("dma_done_spin")
  fw.label(spin)
  fw.j(spin)
  return fw.compile()[0].data


def pattern(size: int, seed: int) -> bytes:
  return bytes(((i * 37 + seed) ^ (i >> 3)) & 0xFF for i in range(size))


def launch_drisc(dev: PCIDevice, core: tuple[int, int], l1: TLBWindow, regs: RegWindow, code: bytes, timeout: float):
  l1.write(RESULT_ADDR, b"\0" * (RESULT_WORDS * 4))
  l1.write(DRISC_FW_BASE, code)
  reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
  regs.write32(DRISC_RESET_PC, DRISC_FW_BASE)
  time.sleep(0.01)
  regs.write32(SOFT_RESET_0, reset_state & ~SOFT_RESET_BRISC)

  status = 0
  deadline = time.time() + timeout
  while time.time() < deadline:
    words = struct.unpack("<" + "I" * RESULT_WORDS, l1.read(RESULT_ADDR, RESULT_WORDS * 4))
    if words[0] == RESULT_MAGIC and words[6] in (STATUS_DONE, STATUS_TIMEOUT):
      status = words[6]
      break
    time.sleep(0.001)

  final_reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, final_reset_state | SOFT_RESET_BRISC)
  if status == 0:
    raise TimeoutError(f"DRISC DMA kernel did not finish on {core}")
  return struct.unpack("<" + "I" * RESULT_WORDS, l1.read(RESULT_ADDR, RESULT_WORDS * 4))


def main():
  parser = argparse.ArgumentParser(description="Proof of concept for Blackhole DRISC GDDR DMA.")
  parser.add_argument("--bank", type=int, default=0)
  parser.add_argument("--endpoint", type=int, default=0)
  parser.add_argument("--gddr-addr", type=lambda s: int(s, 0), default=0x100000)
  parser.add_argument("--size", type=int, default=MAX_STAGE_BYTES & ~0xF)
  parser.add_argument("--iters", type=int, default=1024)
  parser.add_argument("--timeout", type=float, default=2.0)
  args = parser.parse_args()
  if args.size <= 0 or args.size % 16:
    raise ValueError("--size must be a positive multiple of 16")
  if args.size > MAX_STAGE_BYTES:
    raise ValueError(f"--size must fit the DRISC staging region, max {MAX_STAGE_BYTES}")
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  os.environ.pop("TT_USB", None)
  dev = PCIDevice(use_vfio=True)
  core = select_dram_core(dev, args.bank, args.endpoint)
  read_src = args.gddr_addr
  write_dst = args.gddr_addr + ((args.size + 0xFFF) & ~0xFFF)
  read_data = pattern(args.size, 0x31)
  write_data = pattern(args.size, 0xA7)

  dev.set_power_state(True)
  try:
    gddr = TLBWindow(dev, start=core, addr=0)
    l1 = TLBWindow(dev, start=core, addr=DRISC_L1_NOC_ALIAS)
    regs = RegWindow(dev, core)
    try:
      gddr.write(read_src, read_data)
      l1.write(STAGE_ADDR, b"\0" * args.size)
      words_read = launch_drisc(
        dev, core, l1, regs,
        build_dma_kernel(op=OP_READ, gddr_addr=read_src, size=args.size, iterations=args.iters),
        args.timeout,
      )
      l1_after_read = l1.read(STAGE_ADDR, args.size)

      l1.write(STAGE_ADDR, write_data)
      gddr.write(write_dst, b"\0" * args.size)
      words_write = launch_drisc(
        dev, core, l1, regs,
        build_dma_kernel(op=OP_WRITE, gddr_addr=write_dst, size=args.size, iterations=args.iters),
        args.timeout,
      )
      gddr_after_write = gddr.read(write_dst, args.size)
    finally:
      regs.close()
      l1.close()
      gddr.close()
  finally:
    dev.set_power_state(False)
    dev.close()

  read_ok = l1_after_read == read_data
  write_ok = gddr_after_write == write_data
  read_cycles = ((words_read[12] << 32) | words_read[11]) - ((words_read[10] << 32) | words_read[9])
  write_cycles = ((words_write[12] << 32) | words_write[11]) - ((words_write[10] << 32) | words_write[9])
  read_cycles &= (1 << 64) - 1
  write_cycles &= (1 << 64) - 1
  total_bytes = args.size * args.iters
  read_gbps = (total_bytes / read_cycles) * DEBUG_CLOCK_MHZ / 1000.0 if read_cycles else 0.0
  write_gbps = (total_bytes / write_cycles) * DEBUG_CLOCK_MHZ / 1000.0 if write_cycles else 0.0
  print(
    f"dram_core={core} size={args.size} iters={args.iters} total_bytes={total_bytes} read_status={words_read[6]} "
    f"write_status={words_write[6]} read_ok={read_ok} write_ok={write_ok} "
    f"read_cycles={read_cycles} write_cycles={write_cycles} "
    f"read_gbps={read_gbps:.1f} write_gbps={write_gbps:.1f} "
    f"read_dma_status=0x{words_read[8]:08x} write_dma_status=0x{words_write[8]:08x}"
  )
  if not (read_ok and write_ok and words_read[6] == STATUS_DONE and words_write[6] == STATUS_DONE):
    raise SystemExit(1)


if __name__ == "__main__":
  main()
