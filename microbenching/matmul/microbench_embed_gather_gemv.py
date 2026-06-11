#!/usr/bin/env python3
"""One-launch embedding gather + skinny GEMV proof.

This is the launch-count bridge for Llama decode:

  token id in DRAM -> gather embedding row into tilized M=1 A buffer -> GEMV

The gather runs as a BRISC preamble on the normal matmul A-reader sender core,
before it releases TRISCs. After that, the existing skinny-GEMV dataflow streams
the freshly-written A tiles from DRAM. Receivers and the B/output side stay the
normal matmul_peak kernels.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402,F401
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples"))
import matmul_peak as base  # noqa: E402

from asm import KernelBase
from dsl import (
  a0, a1, a2, a3, a4, a5, a6, a7,
  s0, s1, s2, s3, s4, s6, s7, s8, s9, s10, s11,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC
from ttk.tensix import TensixL1

PAGE = Dtype.Float16_b.tile_size
ROW_HALF_BYTES = 16 * 2
TILE_ROW0_COL16_OFF = 16 * 16 * 2

GATHER_NOC = 0
GATHER_NOC_OFF = GATHER_NOC << NOC.INSTANCE_OFFSET_BIT
RD_STATUS = NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + GATHER_NOC_OFF
WR_STATUS = NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + GATHER_NOC_OFF


def cb_data_bytes(plan: base.MatmulPlan) -> int:
  addr = 0
  shared: dict[int, int] = {}
  for index, pages in (
    (0, plan.cb0_pages),
    (1, plan.cb1_pages),
    (16, plan.cb16_pages),
    (24, plan.cb24_pages),
  ):
    share_with = {16: 24, 24: 16}.get(index)
    if share_with is not None and share_with in shared:
      cb_addr = shared[share_with]
    else:
      cb_addr = addr
      addr += pages * PAGE
    shared[index] = cb_addr
  return addr


def emit_embed_gather_to_a_preamble(
    fw: base.MatmulKernel, *, dim_tiles: int, pages_per_row: int, scratch_l1: int):
  """Append BRISC code that materializes A row 0 in the tilized GEMV input."""
  row_l1 = scratch_l1
  idx_l1 = row_l1 + pages_per_row * PAGE

  def read_page(base_reg, page_reg, l1_dst_reg):
    fw.mv(a0, base_reg)
    fw.mv(a1, page_reg)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.read32(s10, RD_STATUS, tmp_addr=t0)
    fw.addi(s10, s10, 1)
    fw.local_noc0_coord(a5, x_addr=BM.MY_X + GATHER_NOC, y_addr=BM.MY_Y + GATHER_NOC)
    fw.li(t6, PAGE)
    fw.noc_read(GATHER_NOC, 1, a0, 0, a2, l1_dst_reg, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_reads_flushed(GATHER_NOC, s10, addr=t0, val=t1)

  def write_chunk(out_page_reg, out_off: int, l1_src_reg):
    fw.mv(a0, s0)
    fw.mv(a1, out_page_reg)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    if out_off:
      fw.addi(a0, a0, out_off)
    fw.li(t6, ROW_HALF_BYTES)
    fw.noc_write(GATHER_NOC, 0, l1_src_reg, a0, 0, a2, t6, a=t0, v=t1)

  fw.rta_ptr(BM.RTA_L1_BASE_PTR)
  fw.arg(s0, 0)    # A/GEMV input base, destination for the gathered row
  fw.arg(s4, 23)   # DRAM bank count
  fw.arg(s2, 24)   # row-major embedding table base
  fw.arg(s3, 25)   # token-id buffer base

  read_page(s3, zero, idx_l1)
  fw.li(t0, idx_l1)
  fw.lw(s8, t0, 0)                     # token id loaded from device memory
  fw.li(t0, pages_per_row)
  fw.mul(s8, s8, t0)                   # first source row page
  for page in range(pages_per_row):
    fw.li(t5, row_l1 + page * PAGE)
    read_page(s2, s8, t5)
    fw.addi(s8, s8, 1)

  fw.li(s6, 0)
  fw.li(s7, dim_tiles)
  fw.label("embed_gather_tile_loop")
  fw.beq(s6, s7, "embed_gather_done")
  fw.slli(t4, s6, 6)                   # tile * 32 bf16s in the row-major source row
  fw.li(t5, row_l1)
  fw.add(t5, t5, t4)
  fw.mv(s8, s6)                        # output tile page; dram_tile_addr_from clobbers t0..t2

  fw.read32(s10, WR_STATUS, tmp_addr=t0)
  fw.addi(s10, s10, 2)
  write_chunk(s8, 0, t5)
  fw.addi(t5, t5, ROW_HALF_BYTES)
  write_chunk(s8, TILE_ROW0_COL16_OFF, t5)
  fw.noc_write_barrier(GATHER_NOC, s10, addr=t0, val=t1)
  fw.addi(s6, s6, 1)
  fw.j("embed_gather_tile_loop")
  fw.label("embed_gather_done")
  return fw


def matmul_reader_sender_with_embed(plan: base.MatmulPlan, *, dim_tiles: int, pages_per_row: int) -> base.MatmulKernel:
  fw = base.MatmulKernel()
  scratch_l1 = TensixL1.DATA_BUFFER_SPACE_BASE + cb_data_bytes(plan) + 0x2000
  scratch_end = scratch_l1 + pages_per_row * PAGE + PAGE
  if scratch_end > TensixL1.SIZE - base.SYNC_BYTES:
    raise ValueError(f"embed gather scratch exceeds L1: end=0x{scratch_end:x}")
  emit_embed_gather_to_a_preamble(
    fw, dim_tiles=dim_tiles, pages_per_row=pages_per_row, scratch_l1=scratch_l1)
  fw.release_triscs()
  base.emit_profile_stamp(fw, base.PROFILE_BRISC)
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
  base.emit_profile_accum_start(fw, base.PROFILE_TMP_BRISC)
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
      base._move_plus_imm(fw, a1, a6, col)
      fw.arg(a2, 23)
      fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
      fw.local_noc0_coord(a5)
      fw.li(t6, base.TILE_BYTES)
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
  block_bytes = plan.in0_block_num_tiles * base.TILE_BYTES
  fw.addi(a6, a6, base._ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(a0, s9)
  base._emit_mcast_chunks(fw, 0, a0, a5, block_bytes)
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
  fw.addi(a6, a6, base._ceil_div(block_bytes, NOC.MAX_BURST_SIZE))
  fw.mv(a0, s9)
  base._emit_mcast_chunks(fw, 0, a0, a5, block_bytes)
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
  base.emit_profile_accum_end(fw, base.PROFILE_COUNTERS[0][1], base.PROFILE_TMP_BRISC)
  fw.add(s1, s1, s4)
  fw.addi(s6, s6, 1)
  fw.j("reader_sender_block_loop")
  fw.label("reader_sender_done")
  base.emit_profile_stamp(fw, base.PROFILE_BRISC + 8)
  return fw.ret()


def pad_text_to(kernel: KernelBase, target_len: int) -> KernelBase:
  """CQ per-core writes require same-size text payloads for sender/recv roles."""
  while len(kernel.to_bytes()) < target_len:
    kernel.nop()
  if len(kernel.to_bytes()) != target_len:
    raise ValueError("kernel text padding overshot target length")
  return kernel


def build_fused_program(plan: base.MatmulPlan, a_addr: int, b_addr: int, c_addr: int,
                        table_addr: int, idx_addr: int, num_banks: int,
                        dim_tiles: int, pages_per_row: int,
                        layout: base.TensorLayout | None = None) -> Program:
  brisc_sender = matmul_reader_sender_with_embed(plan, dim_tiles=dim_tiles, pages_per_row=pages_per_row)
  brisc_recv = base.matmul_reader_recv()
  pad_text_to(brisc_recv, len(brisc_sender.to_bytes()))
  ncrisc_sender = base.matmul_writer_sender(plan)
  ncrisc_recv = base.matmul_writer_recv(plan)
  trisc0 = base.matmul_trisc0_grouped_k(plan) if base.K_GROUP > 1 else base.matmul_trisc0(plan)
  trisc1 = base.matmul_trisc1_grouped_k(plan) if base.K_GROUP > 1 else base.matmul_trisc1(plan)
  trisc2 = base.matmul_trisc2_grouped_k(plan) if base.K_GROUP > 1 else base.matmul_trisc2(plan)

  brisc_sender.rta(lambda x, y: base.reader_args(plan, a_addr, (x, y), num_banks, layout) + [table_addr, idx_addr])
  brisc_recv.rta(lambda x, y: base.reader_args(plan, a_addr, (x, y), num_banks, layout) + [0, 0])
  ncrisc_sender.rta(lambda x, y: base.writer_args(plan, b_addr, c_addr, (x, y), num_banks, layout))
  ncrisc_recv.rta(lambda x, y: base.writer_args(plan, b_addr, c_addr, (x, y), num_banks, layout))
  trisc0.rta(lambda x, y: base.trisc_args(plan, (x, y)) if base.SKIP_PADDED_N else [])
  trisc1.rta(lambda x, y: base.trisc_args(plan, (x, y)) if base.SKIP_PADDED_N else [])
  trisc2.rta(lambda x, y: base.trisc_args(plan, (x, y)) if base.SKIP_PADDED_N else [])

  prog = Program(
    brisc=brisc_sender,
    brisc_recv=brisc_recv,
    ncrisc=ncrisc_sender,
    ncrisc_recv=ncrisc_recv,
    trisc0=trisc0,
    trisc1=trisc1,
    trisc2=trisc2,
    cbs=[
      (0, base.TILE_BYTES, plan.cb0_pages),
      (1, base.TILE_BYTES, plan.cb1_pages),
      (16, base.TILE_BYTES, plan.cb16_pages),
      (24, base.TILE_BYTES, plan.cb24_pages),
    ],
    semaphores=base.NUM_SEMAPHORES,
    grid=(plan.rows, plan.cols),
  )
  prog.name = f"embed_gather_gemv_{plan.mt * base.TILE}x{plan.kt * base.TILE}x{plan.nt * base.TILE}"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="fused embedding gather + GEMV launch; needs device")
  p.add_argument("--rows", type=int, default=4096, help="embedding table rows")
  p.add_argument("--k", type=int, default=2048)
  p.add_argument("--n", type=int, default=512)
  p.add_argument("--runs", type=int, default=1, help="repeat the same fused launch N times before validation")
  p.add_argument("--pattern", action="store_true", help="use integer bf16-bit pattern table for gather debugging")
  args = p.parse_args()
  if args.k % 1024 != 0:
    raise ValueError("K must be a multiple of 1024 for row-page aligned embedding rows")

  rng = np.random.default_rng(31)
  if args.pattern:
    table_u16 = ((np.arange(args.rows, dtype=np.uint32)[:, None] * 4096 +
                  np.arange(args.k, dtype=np.uint32)[None, :]) & 0xFFFF).astype(np.uint16)
    table_bf16 = (table_u16.astype(np.uint32) << 16).view(np.float32)
    table_bytes = table_u16.tobytes()
  else:
    table = rng.uniform(-0.5, 0.5, size=(args.rows, args.k)).astype(np.float32)
    table_bf16 = base.from_bf16_device_bytes(base.to_bf16_device_bytes(table), table.shape)
    table_bytes = base.to_bf16_device_bytes(table)
  token = np.array([args.rows - 1], dtype=np.uint32)
  b = rng.uniform(-0.5, 0.5, size=(args.k, args.n)).astype(np.float32)
  b = base.from_bf16_device_bytes(base.to_bf16_device_bytes(b), b.shape)

  with harness.open_device() as device:
    num_banks = len(device.dram.bank_tiles)
    ys = sorted({y for _, y in device.cores})[:1]
    cores = [c for c in device.cores if c[1] in ys]
    chunks = base.plan_output_chunks(1, args.k, args.n, cores, num_banks)
    if len(chunks) != 1:
      raise ValueError(f"this proof bench expects one output chunk, got {len(chunks)}")
    chunk = chunks[0]
    Mp, Kp, Np = base.global_padded_shape(1, args.k, args.n, chunks)
    dim_tiles = args.k // base.TILE
    pages_per_row = args.k * 2 // PAGE

    w = np.zeros((Kp, Np), dtype=np.float32)
    w[:args.k, :args.n] = b
    a_buf = device.dram.alloc((Mp // base.TILE) * (Kp // base.TILE),
                              dtype=Dtype.Float16_b, shape=(Mp, Kp), name="fused_x")
    device.dram_write(a_buf, b"\0" * (Mp * Kp * 2))
    b_buf = device.alloc_write(base.to_bf16_device_bytes(w), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="fused_w")
    c_buf = device.dram.alloc((Mp // base.TILE) * (Np // base.TILE),
                              dtype=Dtype.Float16_b, shape=(Mp, Np), name="fused_c")
    table_buf = device.dram.alloc(args.rows * pages_per_row, dtype=Dtype.Float16_b,
                                  name="embed_table_rowmajor")
    device.dram_write(table_buf, table_bytes)
    idx_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, name="token_id")
    device.dram_write(idx_buf, token.tobytes().ljust(PAGE, b"\0"))

    layout = base.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      a_row_stride=Kp // base.TILE,
      b_row_stride=Np // base.TILE,
      c_row_stride=Np // base.TILE,
    )
    prog = build_fused_program(chunk.plan, a_buf.addr, b_buf.addr, c_buf.addr,
                               table_buf.addr, idx_buf.addr, num_banks,
                               dim_tiles, pages_per_row, layout)
    timings = []
    for _ in range(args.runs):
      timings.extend(device.run(prog))
    c_raw = device.dram_read(c_buf)
    gathered = np.frombuffer(device.dram_read(a_buf), dtype=np.uint16).reshape(Mp, Kp)

  expected_a = np.zeros((Mp, Kp), dtype=np.float32)
  expected_a[0, :args.k] = table_bf16[int(token[0])]
  expected_a_u16 = np.frombuffer(base.to_bf16_device_bytes(expected_a), dtype=np.uint16).reshape(Mp, Kp)
  a_ok = bool(np.array_equal(gathered, expected_a_u16))
  try:
    pcc, rel_l2 = base.validate(expected_a[:1, :args.k], b[:, :args.n], c_raw, 1, args.n, Mp, Np)
  except AssertionError:
    c_full = base.from_bf16_device_bytes(c_raw, (Mp, Np))
    got = c_full[:1, :args.n].reshape(-1)
    ref = (expected_a[:1, :args.k] @ b[:, :args.n]).reshape(-1)
    pcc = float(np.corrcoef(got, ref)[0, 1])
    rel_l2 = float(np.linalg.norm(got - ref) / (np.linalg.norm(ref) + 1e-12))
  ok = a_ok and pcc >= base.PCC_THRESHOLD and rel_l2 <= base.REL_L2_THRESHOLD

  print("embed gather + GEMV fused launch")
  print(f"  rows={args.rows} K={args.k} N={args.n} token={int(token[0])}")
  if timings:
    print(f"  launches={len(timings)} avg={sum(t['us'] for t in timings) / len(timings):.1f} us")
  print(f"  gathered A: {'exact' if a_ok else 'MISMATCH'}")
  if not a_ok:
    row = int(np.argmax((gathered != expected_a_u16).any(axis=1)))
    cols = np.flatnonzero(gathered[row] != expected_a_u16[row])
    col = int(cols[0])
    print(f"    first A mismatch row={row} col={col} got={int(gathered[row, col])} ref={int(expected_a_u16[row, col])}")
  print(f"  GEMV: pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
