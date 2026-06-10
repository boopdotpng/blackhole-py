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
from device import Device
from drisc_gddr_dma_poc import (
  DMA_CTRL_ATTRS_BURST_255, RESULT_MAGIC, STATUS_DONE, STATUS_STARTED,
  TX_CTRL_TRANSFER_ATTRIBUTES, emit_poll_status,
)
from drisc_gddr_to_worker_poc import (
  ACK_SCRATCH_ADDR, MAX_NOC_CHUNK_BYTES, RESULT_ADDR, RESULT_WORDS,
  emit_init_drisc_noc_cmd_bufs, emit_local_noc_coord, emit_posted_writes_flushed,
  emit_set_drisc_noc2axi_mode_all, emit_set_drisc_stream_mode_all,
)
from drisc_hello import (
  DRISC_FW_BASE, DRISC_L1_NOC_ALIAS, DRISC_RESET_PC, RegWindow,
  SOFT_RESET_0, SOFT_RESET_BRISC, select_dram_core,
)
from dsl import a0, a1, a2, a3, a4, a5, a6, s0, s1, s2, s6, s7, t0, t1, t2, t3, t4, t5, t6, zero
from pcie import TLBWindow
from program import Dtype, Program
from ttk import Cb, Noc
from ttk.drisc import pattern, read_drisc_words, start_drisc, wait_drisc
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC, noc_xy
from ttk.tensix import TensixL1


TILE_BYTES = Dtype.Float16_b.tile_size
POC_MAGIC = RESULT_MAGIC ^ 0x43424452  # "RDBC", distinguish direct-CB POC
REQUEST_ADDR = 0x100000
REQUEST_STATUS = REQUEST_ADDR + 0x00
REQUEST_DST = REQUEST_ADDR + 0x10
REQUEST_SIZE = REQUEST_ADDR + 0x20
REQUEST_WORKER_STATUS = REQUEST_ADDR + 0x30
REQ_EMPTY = 0
REQ_READY = 1
REQ_DONE = 2
WORKER_DONE = 3


class WorkerCbKernel(KernelBase, Cb):
  pass


class DriscCbKernel(KernelBase, Noc):
  pass


def emit_dma_read_to_stage(fw: KernelBase, *, gddr_addr: int, size: int, stream: int):
  if size <= 0 or size % 16:
    raise ValueError("size must be a positive multiple of 16")
  fw.write32(TX_CTRL_TRANSFER_ATTRIBUTES, DMA_CTRL_ATTRS_BURST_255, tmp_addr=t0, tmp_val=t1)
  from drisc_gddr_dma_poc import TX_READ_DST, TX_READ_SRC_HI, TX_READ_SRC_LO, TX_STREAM_STATUS, TX_TRANSFER_ATTRIBUTES, DMA_READ_STATUS_MASK, STAGE_ADDR, stream_reg
  fw.write32(stream_reg(stream, TX_READ_SRC_LO), gddr_addr & 0xFFFFFFFF, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_SRC_HI), (gddr_addr >> 32) & 0xFFFFFFFF, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_DST), STAGE_ADDR, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_TRANSFER_ATTRIBUTES), 0x83000000 | (size >> 4), tmp_addr=t0, tmp_val=t1)
  return emit_poll_status(fw, stream=stream, mask=DMA_READ_STATUS_MASK, timeout_iters=20_000_000)


def emit_remote_read_word(fw: DriscCbKernel, *, noc: int, worker_coord: int, remote_addr: int, ret_coord, out):
  fw.li(a0, remote_addr)
  fw.li(a1, worker_coord)
  fw.li(a2, 16)
  fw.read32(s7, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(s7, s7, 1)
  fw.noc_read(noc, 1, a0, 0, a1, ACK_SCRATCH_ADDR, a2, ret_coord=ret_coord, a=t0, v=t1)
  fw.noc_reads_flushed(noc, s7, addr=t0, val=t1)
  return fw.read32(out, ACK_SCRATCH_ADDR, tmp_addr=t0)


def emit_stage_write_to_cb(fw: DriscCbKernel, *, noc: int, size: int, worker_coord: int, dst_reg):
  from drisc_gddr_dma_poc import STAGE_ADDR
  chunks = (size + MAX_NOC_CHUNK_BYTES - 1) // MAX_NOC_CHUNK_BYTES
  fw.read32(t6, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(t6, t6, chunks)
  for off in range(0, size, MAX_NOC_CHUNK_BYTES):
    chunk = min(MAX_NOC_CHUNK_BYTES, size - off)
    if off:
      fw.li(t5, off)
      fw.li(a2, STAGE_ADDR)
      fw.add(a2, a2, t5)
      fw.add(a3, dst_reg, t5)
    else:
      fw.li(a2, STAGE_ADDR)
      fw.mv(a3, dst_reg)
    fw.li(a4, worker_coord)
    fw.li(a5, chunk)
    fw.noc_write(noc, 0, a2, a3, 0, a4, a5, posted=True, a=t3, v=t4)
  return emit_posted_writes_flushed(fw, noc=noc, target=t6, addr=t3, val=t4)


def emit_remote_status_done(fw: DriscCbKernel, *, noc: int, worker_coord: int):
  fw.write32(ACK_SCRATCH_ADDR + 0x10, REQ_DONE, tmp_addr=t3, tmp_val=t4)
  for off in (0x14, 0x18, 0x1C):
    fw.write32(ACK_SCRATCH_ADDR + off, 0, tmp_addr=t3, tmp_val=t4)
  fw.read32(t6, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(t6, t6, 1)
  fw.li(a2, ACK_SCRATCH_ADDR + 0x10)
  fw.li(a3, REQUEST_STATUS)
  fw.li(a4, worker_coord)
  fw.li(a5, 16)
  fw.noc_write(noc, 0, a2, a3, 0, a4, a5, posted=True, a=t3, v=t4)
  return emit_posted_writes_flushed(fw, noc=noc, target=t6, addr=t3, val=t4)


def build_drisc_feeder(*, gddr_addr: int, size: int, worker_coord: int, noc: int, ctrl_noc: int, stream: int) -> bytes:
  if size <= 0 or size % 16:
    raise ValueError("size must be a positive multiple of 16")
  if noc not in (0, 1):
    raise ValueError("noc must be 0 or 1")
  if ctrl_noc not in (0, 1):
    raise ValueError("ctrl_noc must be 0 or 1")
  if stream not in (0, 1):
    raise ValueError("stream must be 0 or 1")
  from drisc_gddr_dma_poc import STAGE_ADDR
  if size > ACK_SCRATCH_ADDR - STAGE_ADDR:
    raise ValueError(f"size must fit DRISC staging region, max {ACK_SCRATCH_ADDR - STAGE_ADDR}")

  fw = DriscCbKernel(base_addr=DRISC_FW_BASE)
  for idx, value in enumerate((POC_MAGIC, size, gddr_addr & 0xFFFFFFFF, (gddr_addr >> 32) & 0xFFFFFFFF, REQUEST_ADDR, worker_coord, STATUS_STARTED, 0)):
    fw.write32(RESULT_ADDR + idx * 4, value, tmp_addr=t0, tmp_val=t1)

  emit_set_drisc_stream_mode_all(fw)
  emit_init_drisc_noc_cmd_bufs(fw)
  emit_local_noc_coord(fw, noc=ctrl_noc, out=s6)

  poll = fw._new_label("wait_worker_request")
  fw.label(poll)
  emit_remote_read_word(fw, noc=ctrl_noc, worker_coord=worker_coord, remote_addr=REQUEST_STATUS, ret_coord=s6, out=s0)
  fw.li(t0, REQ_READY)
  fw.bne(s0, t0, poll)

  emit_remote_read_word(fw, noc=ctrl_noc, worker_coord=worker_coord, remote_addr=REQUEST_DST, ret_coord=s6, out=s1)
  emit_remote_read_word(fw, noc=ctrl_noc, worker_coord=worker_coord, remote_addr=REQUEST_SIZE, ret_coord=s6, out=s2)
  emit_dma_read_to_stage(fw, gddr_addr=gddr_addr, size=size, stream=stream)
  emit_stage_write_to_cb(fw, noc=noc, size=size, worker_coord=worker_coord, dst_reg=s1)
  emit_remote_status_done(fw, noc=ctrl_noc, worker_coord=worker_coord)

  emit_set_drisc_noc2axi_mode_all(fw)
  fw.write32(RESULT_ADDR + 6 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  spin = fw._new_label("drisc_cb_done_spin")
  fw.label(spin)
  fw.j(spin)
  return fw.compile()[0].data


def build_worker(*, size: int, pages: int) -> WorkerCbKernel:
  fw = WorkerCbKernel()
  fw.write32(REQUEST_STATUS, REQ_EMPTY, tmp_addr=t0, tmp_val=t1)
  fw.write32(REQUEST_WORKER_STATUS, STATUS_STARTED, tmp_addr=t0, tmp_val=t1)
  fw.cb_reserve_back(BM.CB_INTERFACE, 0, pages)
  fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=s0)
  fw.write32(REQUEST_DST, s0, tmp_addr=t0, tmp_val=t1)
  fw.write32(REQUEST_SIZE, size, tmp_addr=t0, tmp_val=t1)
  fw.write32(REQUEST_STATUS, REQ_READY, tmp_addr=t0, tmp_val=t1)
  wait = fw._new_label("wait_drisc_done")
  fw.label(wait)
  fw.read32(t0, REQUEST_STATUS, tmp_addr=t1)
  fw.li(t2, REQ_DONE)
  fw.bne(t0, t2, wait)
  fw.cb_push_back(BM.CB_INTERFACE, 0, pages)
  fw.write32(REQUEST_WORKER_STATUS, WORKER_DONE, tmp_addr=t0, tmp_val=t1)
  return fw.ret()


def main():
  parser = argparse.ArgumentParser(description="POC: DRISC DMA writes directly into a worker CB; BRISC owns CB metadata.")
  parser.add_argument("--bank", type=int, default=0)
  parser.add_argument("--endpoint", type=int, default=0)
  parser.add_argument("--worker-index", type=int, default=0)
  parser.add_argument("--gddr-addr", type=lambda s: int(s, 0), default=0x100000)
  parser.add_argument("--tiles", type=int, default=8)
  parser.add_argument("--noc", type=int, default=0)
  parser.add_argument("--ctrl-noc", type=int, default=0)
  parser.add_argument("--stream", type=int, default=0)
  parser.add_argument("--timeout", type=float, default=5.0)
  args = parser.parse_args()

  if args.tiles <= 0:
    raise ValueError("--tiles must be positive")
  size = args.tiles * TILE_BYTES
  os.environ.pop("TT_USB", None)
  device = Device()
  try:
    if args.worker_index < 0 or args.worker_index >= len(device.cores):
      raise ValueError(f"--worker-index must be in [0, {len(device.cores) - 1}]")
    worker_core = device.cores[args.worker_index]
    worker_coord = noc_xy(*worker_core)
    dram_core = select_dram_core(device.dev, args.bank, args.endpoint)
    data = pattern(size, 0x4D)

    device.dev.set_power_state(True)
    try:
      with TLBWindow(device.dev, start=dram_core, addr=0) as gddr:
        gddr.write(args.gddr_addr, data)
      start_drisc(
        dram_core,
        build_drisc_feeder(
          gddr_addr=args.gddr_addr, size=size, worker_coord=worker_coord,
          noc=args.noc, ctrl_noc=args.ctrl_noc, stream=args.stream,
        ),
        device.dev,
      )
    finally:
      device.dev.set_power_state(False)

    empty = KernelBase()
    program = Program(
      brisc=build_worker(size=size, pages=args.tiles),
      ncrisc=empty,
      trisc0=empty,
      trisc1=empty,
      trisc2=empty,
      cbs=[(0, TILE_BYTES, args.tiles)],
      num_cores=1,
    )
    program.name = "drisc_cb_direct_poc"
    try:
      device.run(program)
    except TimeoutError:
      device.dev.set_power_state(True)
      try:
        words = read_drisc_words(dram_core, device.dev)
        with TLBWindow(device.dev, start=worker_core) as worker_l1:
          req_status = struct.unpack("<I", worker_l1.read(REQUEST_STATUS, 4))[0]
          req_dst = struct.unpack("<I", worker_l1.read(REQUEST_DST, 4))[0]
          worker_status = struct.unpack("<I", worker_l1.read(REQUEST_WORKER_STATUS, 4))[0]
        print(
          f"direct-cb-timeout req_status={req_status} req_dst=0x{req_dst:x} "
          f"worker_status={worker_status} drisc_words={[hex(w) for w in words]}",
          file=sys.stderr,
        )
      finally:
        device.dev.set_power_state(False)
      raise

    device.dev.set_power_state(True)
    try:
      wait_drisc(dram_core, device.dev, args.timeout, magic=POC_MAGIC, label="DRISC direct-CB feeder")
      with TLBWindow(device.dev, start=worker_core) as worker_l1:
        dst = struct.unpack("<I", worker_l1.read(REQUEST_DST, 4))[0]
        worker_status = struct.unpack("<I", worker_l1.read(REQUEST_WORKER_STATUS, 4))[0]
        got = worker_l1.read(dst, size)
    finally:
      device.dev.set_power_state(False)
  finally:
    device.close()

  ok = got == data
  mismatch = next((idx for idx, (actual, expected) in enumerate(zip(got, data)) if actual != expected), -1)
  print(
    f"dram_core={dram_core} worker_core={worker_core} tiles={args.tiles} size={size} "
    f"noc={args.noc} ctrl_noc={args.ctrl_noc} worker_status={worker_status} cb_dst=0x{dst:x} "
    f"ok={ok} mismatch={mismatch} got0={got[:16].hex()} exp0={data[:16].hex()}"
  )
  if not ok or worker_status != WORKER_DONE:
    raise SystemExit(1)


if __name__ == "__main__":
  main()
