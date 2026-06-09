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

from asm import KernelBase, boot_jal
from drisc_gddr_dma_poc import (
  DEBUG_CLOCK_MHZ, DMA_READ_STATUS_MASK, DMA_CTRL_ATTRS_BURST_255,
  RESULT_MAGIC, STAGE_ADDR, STATUS_DONE, STATUS_STARTED, STATUS_TIMEOUT,
  TX_CTRL_TRANSFER_ATTRIBUTES, TX_READ_DST, TX_READ_SRC_HI, TX_READ_SRC_LO,
  TX_STREAM_STATUS, TX_TRANSFER_ATTRIBUTES, emit_poll_status, emit_read_wall_clock,
  stream_reg,
)
from drisc_hello import (
  DRISC_FW_BASE, DRISC_L1_NOC_ALIAS, DRISC_RESET_PC, RegWindow,
  SOFT_RESET_0, SOFT_RESET_BRISC, select_dram_core,
)
from dsl import a0, a1, a2, a3, a4, a5, a6, a7, s0, s1, s2, s3, s4, s5, s6, s7, t0, t1, t2, t3, t4, t5, t6, zero
from pcie import PCIDevice, TLBWindow
from ttk.noc import NOC, Noc, NocCfg, noc_xy
from ttk.mailbox import Firmware
from ttk.tensix import TensixL1, TensixMMIO


RESULT_ADDR = 0x1F000
RESULT_WORDS = 16
POC_MAGIC = RESULT_MAGIC ^ 0x57524B52  # distinguish from bare DMA POC
DEFAULT_WORKER_ADDR = TensixL1.DATA_BUFFER_SPACE_BASE
MAX_NOC_CHUNK_BYTES = 8 * 1024
ACK_SCRATCH_ADDR = RESULT_ADDR - 0x100
REMOTE_CB_PAGES_SENT_OFF = 0x00
REMOTE_CB_PAGES_ACKED_OFF = 0x10
REMOTE_CB_WORKER_STATUS_OFF = 0x20
REMOTE_CB_RING_OFF = 0x1000
REMOTE_CB_STATUS_STARTED = 1
REMOTE_CB_STATUS_DONE = 2


class DriscFeedKernel(KernelBase, Noc):
  pass


def pattern(size: int, seed: int) -> bytes:
  return bytes(((i * 29 + seed) ^ (i >> 5)) & 0xFF for i in range(size))


def emit_header(fw: KernelBase, *, size: int, gddr_addr: int, worker_addr: int, worker_coord: int):
  values = (
    POC_MAGIC, size, gddr_addr & 0xFFFFFFFF, (gddr_addr >> 32) & 0xFFFFFFFF,
    worker_addr, worker_coord, STATUS_STARTED, 0,
  )
  for idx, value in enumerate(values):
    fw.write32(RESULT_ADDR + idx * 4, value, tmp_addr=t0, tmp_val=t1)


def emit_set_drisc_stream_mode(fw: KernelBase, noc: int):
  addr = NOC.CFG_BASE + NocCfg.NIU_CFG_0 * 4 + (noc << NOC.INSTANCE_OFFSET_BIT)
  fw.read32(t0, addr, tmp_addr=t1)
  fw.li(t2, ~(1 << 15) & 0xFFFFFFFF)
  fw.and_(t0, t0, t2)
  return fw.write32(addr, t0, tmp_addr=t1, tmp_val=t2)


def emit_set_drisc_noc2axi_mode(fw: KernelBase, noc: int):
  addr = NOC.CFG_BASE + NocCfg.NIU_CFG_0 * 4 + (noc << NOC.INSTANCE_OFFSET_BIT)
  fw.read32(t0, addr, tmp_addr=t1)
  fw.li(t2, 1 << 15)
  fw.or_(t0, t0, t2)
  return fw.write32(addr, t0, tmp_addr=t1, tmp_val=t2)


def emit_set_drisc_stream_mode_all(fw: KernelBase):
  emit_set_drisc_stream_mode(fw, 0)
  return emit_set_drisc_stream_mode(fw, 1)


def emit_set_drisc_noc2axi_mode_all(fw: KernelBase):
  emit_set_drisc_noc2axi_mode(fw, 0)
  return emit_set_drisc_noc2axi_mode(fw, 1)


def emit_dma_read(fw: KernelBase, *, gddr_addr: int, size: int, stream: int):
  if size <= 0 or size % 16:
    raise ValueError("size must be a positive multiple of 16")
  fw.write32(TX_CTRL_TRANSFER_ATTRIBUTES, DMA_CTRL_ATTRS_BURST_255, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_SRC_LO), gddr_addr & 0xFFFFFFFF, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_SRC_HI), (gddr_addr >> 32) & 0xFFFFFFFF, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_DST), STAGE_ADDR, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_TRANSFER_ATTRIBUTES), 0x83000000 | (size >> 4), tmp_addr=t0, tmp_val=t1)
  return emit_poll_status(fw, stream=stream, mask=DMA_READ_STATUS_MASK, timeout_iters=20_000_000)


def emit_dma_read_reg(
  fw: KernelBase, *, src_lo, src_hi: int, dst_l1, size: int, stream: int,
):
  if size <= 0 or size % 16:
    raise ValueError("size must be a positive multiple of 16")
  fw.write32(stream_reg(stream, TX_READ_SRC_LO), src_lo, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_SRC_HI), src_hi, tmp_addr=t0, tmp_val=t1)
  fw.write32(stream_reg(stream, TX_READ_DST), dst_l1, tmp_addr=t0, tmp_val=t1)
  return fw.write32(stream_reg(stream, TX_TRANSFER_ATTRIBUTES), 0x83000000 | (size >> 4), tmp_addr=t0, tmp_val=t1)


def emit_dma_read_wait_n(fw: KernelBase, *, stream: int, max_outstanding: int):
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


def emit_local_noc_coord(fw: KernelBase, *, noc: int, out=a5):
  fw.read32(out, NOC.CFG_BASE + NocCfg.ID_LOGICAL * 4 + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.andi(t1, out, NocCfg.NODE_ID_MASK)
  fw.srli(out, out, NocCfg.ADDR_NODE_ID_BITS)
  fw.andi(out, out, NocCfg.NODE_ID_MASK)
  fw.slli(out, out, NocCfg.ADDR_NODE_ID_BITS)
  return fw.or_(out, out, t1)


def emit_init_drisc_noc_cmd_bufs(fw: DriscFeedKernel):
  packet_tag = NOC.REGS_START_ADDR + 0x18
  for noc in range(2):
    emit_local_noc_coord(fw, noc=noc, out=a5)
    for buf in range(4):
      fw.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, 0, addr=t0, tmp=t1)
      fw.noc_cmd_reg(noc, buf, packet_tag, 0, addr=t0, tmp=t1)
    fw.noc_init_cmd_bufs(
      noc,
      a5,
      atomic_ret_addr=ACK_SCRATCH_ADDR + 8,
      read_ctrl=NocCfg.RD_CMD_FIELD,
      wr_buf=0,
      rd_buf=1,
      wr_reg_buf=2,
      at_buf=3,
      tmp_addr=t0,
      tmp_val=t1,
    )
  return fw


def emit_worker_writes(fw: DriscFeedKernel, *, noc: int, size: int, worker_addr: int, worker_coord: int):
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT))
  fw.lw(s0, t0, 0)
  chunks = (size + MAX_NOC_CHUNK_BYTES - 1) // MAX_NOC_CHUNK_BYTES
  fw.addi(s0, s0, chunks)
  for off in range(0, size, MAX_NOC_CHUNK_BYTES):
    chunk = min(MAX_NOC_CHUNK_BYTES, size - off)
    fw.li(a2, STAGE_ADDR + off)
    fw.li(a3, worker_addr + off)
    fw.li(a4, worker_coord)
    fw.li(a5, chunk)
    fw.noc_write(noc, 0, a2, a3, 0, a4, a5, posted=True, a=t3, v=t4)
  return emit_posted_writes_flushed(fw, noc=noc, target=s0, addr=t3, val=t4)


def emit_posted_writes_flushed(fw: DriscFeedKernel, *, noc: int, target, addr=t0, val=t1):
  fw.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT))
  loop = fw._new_label("posted_wr_flush")
  fw.label(loop)
  fw.lw(val, addr, 0)
  fw.bltu(val, target, loop)
  return fw.fence()


def emit_remote_ack_read(
  fw: DriscFeedKernel, *, noc: int, pages_acked_addr: int, worker_coord: int, ret_coord=a5,
):
  fw.li(a0, pages_acked_addr)
  fw.li(a1, worker_coord)
  fw.li(a2, 16)
  fw.read32(s7, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(s7, s7, 1)
  fw.noc_read(noc, 1, a0, 0, a1, ACK_SCRATCH_ADDR, a2, ret_coord=ret_coord, a=t0, v=t1)
  fw.noc_reads_flushed(noc, s7, addr=t0, val=t1)
  return fw.read32(s7, ACK_SCRATCH_ADDR, tmp_addr=t0)


def emit_remote_cb_page_write(
  fw: DriscFeedKernel, *, noc: int, page_size: int, stage_addr, ring_addr, pages_sent: int | object,
  pages_sent_addr: int, worker_coord: int,
):
  chunks = (page_size + MAX_NOC_CHUNK_BYTES - 1) // MAX_NOC_CHUNK_BYTES
  fw.read32(t6, NOC.STATUS_BASE + NOC.NIU_MST_POSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
  fw.addi(t6, t6, chunks + 1)
  for off in range(0, page_size, MAX_NOC_CHUNK_BYTES):
    chunk = min(MAX_NOC_CHUNK_BYTES, page_size - off)
    if off:
      fw.li(t5, off)
      fw.add(a2, stage_addr, t5)
      fw.add(a3, ring_addr, t5)
    else:
      fw.mv(a2, stage_addr)
      fw.mv(a3, ring_addr)
    fw.li(a4, worker_coord)
    fw.li(a5, chunk)
    fw.noc_write(noc, 0, a2, a3, 0, a4, a5, posted=True, a=t3, v=t4)
  fw.li(a3, pages_sent_addr)
  fw.li(a4, worker_coord)
  fw.write32(ACK_SCRATCH_ADDR + 0x10, pages_sent, tmp_addr=t3, tmp_val=t4)
  for pad_off in (0x14, 0x18, 0x1C):
    fw.write32(ACK_SCRATCH_ADDR + pad_off, 0, tmp_addr=t3, tmp_val=t4)
  fw.li(a2, ACK_SCRATCH_ADDR + 0x10)
  fw.li(a5, 16)
  fw.noc_write(noc, 0, a2, a3, 0, a4, a5, posted=True, a=t3, v=t4)
  return emit_posted_writes_flushed(fw, noc=noc, target=t6, addr=t3, val=t4)


def build_remote_cb_kernel(
  *, gddr_addr: int, size: int, page_size: int, ring_pages: int, worker_addr: int,
  worker_coord: int, noc: int, stream: int,
) -> bytes:
  if size <= 0 or size % page_size:
    raise ValueError("size must be a positive multiple of page_size")
  if page_size <= 0 or page_size % 16:
    raise ValueError("page_size must be a positive multiple of 16")
  if ring_pages < 2:
    raise ValueError("ring_pages must be at least 2")
  if 2 * page_size > ACK_SCRATCH_ADDR - STAGE_ADDR:
    raise ValueError(f"two DMA stage pages must fit DRISC L1, max page_size {(ACK_SCRATCH_ADDR - STAGE_ADDR) // 2}")
  if noc not in (0, 1):
    raise ValueError("noc must be 0 or 1")
  if stream not in (0, 1):
    raise ValueError("stream must be 0 or 1")

  total_pages = size // page_size
  gddr_hi = (gddr_addr >> 32) & 0xFFFFFFFF
  gddr_lo = gddr_addr & 0xFFFFFFFF
  pages_sent_addr = worker_addr + REMOTE_CB_PAGES_SENT_OFF
  pages_acked_addr = worker_addr + REMOTE_CB_PAGES_ACKED_OFF
  ring_base = worker_addr + REMOTE_CB_RING_OFF

  fw = DriscFeedKernel(base_addr=DRISC_FW_BASE)
  emit_header(fw, size=size, gddr_addr=gddr_addr, worker_addr=worker_addr, worker_coord=worker_coord)
  fw.write32(RESULT_ADDR + 7 * 4, page_size, tmp_addr=t0, tmp_val=t1)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000001, tmp_addr=t0, tmp_val=t1)
  fw.write32(TX_CTRL_TRANSFER_ATTRIBUTES, DMA_CTRL_ATTRS_BURST_255, tmp_addr=t0, tmp_val=t1)
  fw.li(a6, 0)
  fw.li(a7, 0)
  emit_set_drisc_stream_mode_all(fw)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000002, tmp_addr=t0, tmp_val=t1)
  emit_init_drisc_noc_cmd_bufs(fw)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000003, tmp_addr=t0, tmp_val=t1)
  emit_local_noc_coord(fw, noc=noc, out=s6)

  # s0 = current page index, s1 = pages sent, s2 = current GDDR low,
  # s3 = current stage slot, s4 = next stage slot, s5 = next GDDR low.
  fw.li(s0, 0)
  fw.li(s1, 0)
  fw.li(s2, gddr_lo)
  fw.li(s3, STAGE_ADDR)
  fw.li(s4, STAGE_ADDR + page_size)
  fw.li(s5, (gddr_lo + page_size) & 0xFFFFFFFF)

  emit_dma_read_reg(fw, src_lo=s2, src_hi=gddr_hi, dst_l1=s3, size=page_size, stream=stream)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000004, tmp_addr=t0, tmp_val=t1)

  loop = fw._new_label("remote_cb_loop")
  done = fw._new_label("remote_cb_done")
  no_next = fw._new_label("remote_cb_no_next")
  reserve_loop = fw._new_label("remote_cb_reserve")
  reserve_done = fw._new_label("remote_cb_reserve_done")
  fw.label(loop)
  fw.write32(RESULT_ADDR + 14 * 4, s0, tmp_addr=t0, tmp_val=t1)
  fw.li(t0, total_pages)
  fw.bgeu(s0, t0, done)

  fw.addi(t0, s0, 1)
  fw.li(t1, total_pages)
  fw.bgeu(t0, t1, no_next)
  emit_dma_read_reg(fw, src_lo=s5, src_hi=gddr_hi, dst_l1=s4, size=page_size, stream=stream)
  fw.label(no_next)

  fw.label(reserve_loop)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000005, tmp_addr=t0, tmp_val=t1)
  emit_remote_ack_read(fw, noc=noc, pages_acked_addr=pages_acked_addr, worker_coord=worker_coord, ret_coord=s6)
  fw.write32(RESULT_ADDR + 15 * 4, s7, tmp_addr=t0, tmp_val=t1)
  fw.sub(t0, s1, s7)
  fw.li(t1, ring_pages)
  fw.bltu(t0, t1, reserve_done)
  fw.j(reserve_loop)
  fw.label(reserve_done)

  fw.addi(t0, s0, 1)
  fw.li(t1, total_pages)
  # Wait for only the current DMA when another is in flight, otherwise drain all reads.
  wait_one = fw._new_label("remote_cb_wait_one")
  wait_done = fw._new_label("remote_cb_wait_done")
  fw.bltu(t0, t1, wait_one)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000006, tmp_addr=t0, tmp_val=t1)
  emit_dma_read_wait_n(fw, stream=stream, max_outstanding=0)
  fw.j(wait_done)
  fw.label(wait_one)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000007, tmp_addr=t0, tmp_val=t1)
  emit_dma_read_wait_n(fw, stream=stream, max_outstanding=1)
  fw.label(wait_done)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000008, tmp_addr=t0, tmp_val=t1)

  fw.li(t0, ring_pages)
  fw.remu(t1, s0, t0)
  fw.li(t2, page_size)
  fw.mul(t1, t1, t2)
  fw.li(t3, ring_base)
  fw.add(t3, t3, t1)
  fw.mv(s7, t3)
  fw.addi(s1, s1, 1)
  emit_remote_cb_page_write(
    fw, noc=noc, page_size=page_size, stage_addr=s3, ring_addr=s7, pages_sent=s1,
    pages_sent_addr=pages_sent_addr, worker_coord=worker_coord,
  )
  fw.write32(RESULT_ADDR + 13 * 4, 0xC1000009, tmp_addr=t0, tmp_val=t1)

  fw.addi(s0, s0, 1)
  fw.mv(t0, s3)
  fw.mv(s3, s4)
  fw.mv(s4, t0)
  fw.li(t0, page_size)
  fw.add(s5, s5, t0)
  fw.j(loop)
  fw.label(done)
  fw.write32(RESULT_ADDR + 13 * 4, 0xC100000A, tmp_addr=t0, tmp_val=t1)
  emit_dma_read_wait_n(fw, stream=stream, max_outstanding=0)
  emit_set_drisc_noc2axi_mode_all(fw)
  fw.li(a2, 0)
  fw.li(a3, 0)
  fw.write32(RESULT_ADDR + 6 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  fw.read32(t1, stream_reg(stream, TX_STREAM_STATUS), tmp_addr=t0)
  fw.write32(RESULT_ADDR + 8 * 4, t1, tmp_addr=t0, tmp_val=t2)
  for idx, reg in enumerate((a6, a7, a2, a3), start=9):
    fw.write32(RESULT_ADDR + idx * 4, reg, tmp_addr=t0, tmp_val=t2)
  spin = fw._new_label("remote_cb_done_spin")
  fw.label(spin)
  fw.j(spin)
  return fw.compile()[0].data


def build_worker_remote_cb_consumer(
  *, total_pages: int, page_size: int, ring_pages: int, worker_addr: int, sink_addr: int,
) -> bytes:
  fw = KernelBase(base_addr=Firmware.TEXT_BASE["brisc"])
  pages_sent_addr = worker_addr + REMOTE_CB_PAGES_SENT_OFF
  pages_acked_addr = worker_addr + REMOTE_CB_PAGES_ACKED_OFF
  status_addr = worker_addr + REMOTE_CB_WORKER_STATUS_OFF
  ring_base = worker_addr + REMOTE_CB_RING_OFF
  fw.write32(status_addr, REMOTE_CB_STATUS_STARTED, tmp_addr=t0, tmp_val=t1)
  fw.li(s0, 0)  # pages_acked
  fw.li(s1, total_pages)
  fw.li(s2, page_size)
  fw.li(s3, ring_pages)
  fw.li(s4, ring_base)
  fw.li(s5, sink_addr)
  fw.li(s6, pages_sent_addr)
  fw.li(s7, pages_acked_addr)

  loop = fw._new_label("worker_rcb_loop")
  done = fw._new_label("worker_rcb_done")
  wait = fw._new_label("worker_rcb_wait")
  copy_loop = fw._new_label("worker_rcb_copy")
  copy_done = fw._new_label("worker_rcb_copy_done")
  fw.label(loop)
  fw.bgeu(s0, s1, done)
  fw.label(wait)
  fw.lw(t0, s6, 0)
  fw.beq(t0, s0, wait)

  fw.remu(t1, s0, s3)
  fw.mul(t1, t1, s2)
  fw.add(t2, s4, t1)
  fw.mul(t3, s0, s2)
  fw.add(t4, s5, t3)
  fw.li(t5, page_size // 4)
  fw.label(copy_loop)
  fw.beq(t5, zero, copy_done)
  fw.lw(t6, t2, 0)
  fw.sw(t6, t4, 0)
  fw.addi(t2, t2, 4)
  fw.addi(t4, t4, 4)
  fw.addi(t5, t5, -1)
  fw.j(copy_loop)
  fw.label(copy_done)
  fw.addi(s0, s0, 1)
  fw.sw(s0, s7, 0)
  fw.j(loop)
  fw.label(done)
  fw.write32(status_addr, REMOTE_CB_STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  spin = fw._new_label("worker_rcb_done_spin")
  fw.label(spin)
  fw.j(spin)
  return fw.compile()[0].data


def build_kernel(
  *, gddr_addr: int, size: int, worker_addr: int, worker_coord: int, noc: int, stream: int, skip_dma: bool = False,
) -> bytes:
  if size <= 0 or size % 16:
    raise ValueError("size must be a positive multiple of 16")
  if size > RESULT_ADDR - STAGE_ADDR:
    raise ValueError(f"size must fit DRISC staging region, max {RESULT_ADDR - STAGE_ADDR}")
  if noc not in (0, 1):
    raise ValueError("noc must be 0 or 1")
  if stream not in (0, 1):
    raise ValueError("stream must be 0 or 1")

  fw = DriscFeedKernel(base_addr=DRISC_FW_BASE)
  emit_header(fw, size=size, gddr_addr=gddr_addr, worker_addr=worker_addr, worker_coord=worker_coord)
  fw.write32(RESULT_ADDR + 13 * 4, 0xD1000001, tmp_addr=t0, tmp_val=t1)
  fw.li(a6, 0)
  fw.li(a7, 0)
  emit_set_drisc_stream_mode_all(fw)
  fw.write32(RESULT_ADDR + 13 * 4, 0xD1000002, tmp_addr=t0, tmp_val=t1)
  emit_init_drisc_noc_cmd_bufs(fw)
  fw.write32(RESULT_ADDR + 13 * 4, 0xD1000003, tmp_addr=t0, tmp_val=t1)
  if not skip_dma:
    emit_dma_read(fw, gddr_addr=gddr_addr, size=size, stream=stream)
  fw.write32(RESULT_ADDR + 13 * 4, 0xD1000004, tmp_addr=t0, tmp_val=t1)
  emit_worker_writes(fw, noc=noc, size=size, worker_addr=worker_addr, worker_coord=worker_coord)
  fw.write32(RESULT_ADDR + 13 * 4, 0xD1000005, tmp_addr=t0, tmp_val=t1)
  emit_set_drisc_noc2axi_mode_all(fw)
  fw.li(a2, 0)
  fw.li(a3, 0)

  fw.write32(RESULT_ADDR + 6 * 4, STATUS_DONE, tmp_addr=t0, tmp_val=t1)
  fw.read32(t1, stream_reg(stream, TX_STREAM_STATUS), tmp_addr=t0)
  fw.write32(RESULT_ADDR + 8 * 4, t1, tmp_addr=t0, tmp_val=t2)
  for idx, reg in enumerate((a6, a7, a2, a3), start=9):
    fw.write32(RESULT_ADDR + idx * 4, reg, tmp_addr=t0, tmp_val=t2)
  spin = fw._new_label("feed_done_spin")
  fw.label(spin)
  fw.j(spin)
  return fw.compile()[0].data


def launch_worker_brisc(core: tuple[int, int], worker_l1: TLBWindow, regs: RegWindow, code: bytes):
  worker_l1.write(0, boot_jal(Firmware.TEXT_BASE["brisc"]))
  worker_l1.write(Firmware.TEXT_BASE["brisc"], code)
  regs.write32(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_ALL)
  time.sleep(0.01)
  regs.write32(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN)


def halt_worker_brisc(regs: RegWindow):
  regs.write32(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_ALL)


def launch_drisc(core: tuple[int, int], l1: TLBWindow, regs: RegWindow, code: bytes, timeout: float):
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
    if words[0] == POC_MAGIC and words[6] in (STATUS_DONE, STATUS_TIMEOUT):
      status = words[6]
      break
    time.sleep(0.001)

  final_reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, final_reset_state | SOFT_RESET_BRISC)
  if status == 0:
    words = struct.unpack("<" + "I" * RESULT_WORDS, l1.read(RESULT_ADDR, RESULT_WORDS * 4))
    raise TimeoutError(f"DRISC feed kernel did not finish on {core}; words={[hex(w) for w in words]}")
  return struct.unpack("<" + "I" * RESULT_WORDS, l1.read(RESULT_ADDR, RESULT_WORDS * 4))


def main():
  parser = argparse.ArgumentParser(description="POC: DRISC DMA from GDDR, then feed worker L1 or a one-receiver remote CB.")
  parser.add_argument("--bank", type=int, default=0)
  parser.add_argument("--endpoint", type=int, default=0)
  parser.add_argument("--worker-index", type=int, default=0)
  parser.add_argument("--gddr-addr", type=lambda s: int(s, 0), default=0x100000)
  parser.add_argument("--worker-addr", type=lambda s: int(s, 0), default=DEFAULT_WORKER_ADDR)
  parser.add_argument("--size", type=int, default=64 * 1024)
  parser.add_argument("--mode", choices=("direct", "remote-cb"), default="direct")
  parser.add_argument("--page-size", type=int, default=16 * 1024)
  parser.add_argument("--ring-pages", type=int, default=2)
  parser.add_argument("--noc", type=int, default=0)
  parser.add_argument("--stream", type=int, default=0)
  parser.add_argument("--no-dma", action="store_true", help="copy preseeded DRISC L1 to worker L1 without GDDR DMA")
  parser.add_argument("--timeout", type=float, default=2.0)
  args = parser.parse_args()

  os.environ.pop("TT_USB", None)
  dev = PCIDevice(use_vfio=True)
  dram_core = select_dram_core(dev, args.bank, args.endpoint)
  info = dev.board_info(fast_dispatch=True)
  if args.worker_index < 0 or args.worker_index >= len(info.program_cores):
    raise ValueError(f"--worker-index must be in [0, {len(info.program_cores) - 1}]")
  worker_core = info.program_cores[args.worker_index]
  worker_coord = noc_xy(*worker_core)
  data = pattern(args.size, 0x5A)
  if args.mode == "remote-cb" and args.no_dma:
    raise ValueError("--no-dma is only supported by --mode direct")
  if args.mode == "remote-cb":
    if args.size % args.page_size:
      raise ValueError("--size must be a multiple of --page-size for remote-cb")
    sink_addr = args.worker_addr + REMOTE_CB_RING_OFF + args.ring_pages * args.page_size
    if sink_addr + args.size > TensixL1.SIZE:
      raise ValueError("remote-cb ring + sink do not fit worker L1")

  dev.set_power_state(True)
  try:
    gddr = TLBWindow(dev, start=dram_core, addr=0)
    drisc_l1 = TLBWindow(dev, start=dram_core, addr=DRISC_L1_NOC_ALIAS)
    worker_l1 = TLBWindow(dev, start=worker_core)
    regs = RegWindow(dev, dram_core)
    try:
      if args.mode == "direct":
        if not args.no_dma:
          gddr.write(args.gddr_addr, data)
        drisc_l1.write(STAGE_ADDR, data if args.no_dma else b"\0" * args.size)
        worker_l1.write(args.worker_addr, b"\0" * args.size)
        words = launch_drisc(
          dram_core, drisc_l1, regs,
          build_kernel(
            gddr_addr=args.gddr_addr,
            size=args.size,
            worker_addr=args.worker_addr,
            worker_coord=worker_coord,
            noc=args.noc,
            stream=args.stream,
            skip_dma=args.no_dma,
          ),
          args.timeout,
        )
        got = worker_l1.read(args.worker_addr, args.size)
        worker_status = 0
      else:
        total_pages = args.size // args.page_size
        sink_addr = args.worker_addr + REMOTE_CB_RING_OFF + args.ring_pages * args.page_size
        worker_span = REMOTE_CB_RING_OFF + args.ring_pages * args.page_size + args.size
        gddr.write(args.gddr_addr, data)
        drisc_l1.write(STAGE_ADDR, b"\0" * (2 * args.page_size))
        worker_l1.write(args.worker_addr, b"\0" * worker_span)
        worker_regs = RegWindow(dev, worker_core)
        try:
          launch_worker_brisc(
            worker_core,
            worker_l1,
            worker_regs,
            build_worker_remote_cb_consumer(
              total_pages=total_pages,
              page_size=args.page_size,
              ring_pages=args.ring_pages,
              worker_addr=args.worker_addr,
              sink_addr=sink_addr,
            ),
          )
          try:
            words = launch_drisc(
              dram_core, drisc_l1, regs,
              build_remote_cb_kernel(
                gddr_addr=args.gddr_addr,
                size=args.size,
                page_size=args.page_size,
                ring_pages=args.ring_pages,
                worker_addr=args.worker_addr,
                worker_coord=worker_coord,
                noc=args.noc,
                stream=args.stream,
              ),
              args.timeout,
            )
          except TimeoutError:
            pages_sent = struct.unpack("<I", worker_l1.read(args.worker_addr + REMOTE_CB_PAGES_SENT_OFF, 4))[0]
            pages_acked = struct.unpack("<I", worker_l1.read(args.worker_addr + REMOTE_CB_PAGES_ACKED_OFF, 4))[0]
            worker_status = struct.unpack("<I", worker_l1.read(args.worker_addr + REMOTE_CB_WORKER_STATUS_OFF, 4))[0]
            print(
              f"remote-cb-timeout worker_status={worker_status} "
              f"pages_sent={pages_sent} pages_acked={pages_acked}",
              file=sys.stderr,
            )
            raise
          got = worker_l1.read(sink_addr, args.size)
          worker_status = struct.unpack("<I", worker_l1.read(args.worker_addr + REMOTE_CB_WORKER_STATUS_OFF, 4))[0]
        finally:
          halt_worker_brisc(worker_regs)
          worker_regs.close()
    finally:
      regs.close()
      worker_l1.close()
      drisc_l1.close()
      gddr.close()
  finally:
    dev.set_power_state(False)
    dev.close()

  cycles = (((words[12] << 32) | words[11]) - ((words[10] << 32) | words[9])) & ((1 << 64) - 1)
  gbps = (args.size / cycles) * DEBUG_CLOCK_MHZ / 1000.0 if cycles else 0.0
  ok = got == data
  mismatch = next((idx for idx, (actual, expected) in enumerate(zip(got, data)) if actual != expected), -1)
  print(
    f"mode={args.mode} dram_core={dram_core} worker_core={worker_core} size={args.size} "
    f"page_size={args.page_size if args.mode == 'remote-cb' else 0} ring_pages={args.ring_pages if args.mode == 'remote-cb' else 0} "
    f"noc={args.noc} no_dma={args.no_dma} status={words[6]} worker_status={worker_status} "
    f"ok={ok} mismatch={mismatch} got0={got[:16].hex()} exp0={data[:16].hex()} "
    f"cycles={cycles} gbps={gbps:.1f} dma_status=0x{words[8]:08x}"
  )
  if not (ok and words[6] == STATUS_DONE and (args.mode != "remote-cb" or worker_status == REMOTE_CB_STATUS_DONE)):
    raise SystemExit(1)


if __name__ == "__main__":
  main()
