#!/usr/bin/env python3
"""Stage QKV K output into the RoPE+K-cache scatter composite.

QKV GEMV writes K in the normal M=1 matmul output layout: one tile per
32-column slice, with only row 0 meaningful. The existing RoPE+K scatter proof
expects one tile per KV head with four sparse SFPU footprints:

  x1 rows 0..3, x2 rows 4..7, cos rows 8..11, sin rows 12..15

This bench fills that missing device bridge with a BRISC/NOC staging program,
then runs the existing Tensix RoPE+K scatter program. It proves K cache mutation
can stay device-side after QKV without host-side RoPE math.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "microbenching"))
sys.path.insert(0, str(ROOT / "microbenching" / "tensix"))
sys.path.insert(0, str(ROOT / "examples"))

import harness  # noqa: E402,F401
import matmul_peak as mm  # noqa: E402
import microbench_rope_k_scatter as rope  # noqa: E402
import numpy as np

from asm import KernelBase  # noqa: E402
from dsl import a0, a1, a2, a5, s0, s1, s2, s3, s4, s5, t0, t1, t2, t4, t5, t6, zero  # noqa: E402
from examples import add1  # noqa: E402
from examples.add1 import Brisc, CB_DEPTH, OUT_CB, TILE_BYTES  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402

TILE = 32
PAGE = Dtype.Float16_b.tile_size
HEAD_DIM = 64
ROW_BYTES = HEAD_DIM * 2
ROW_HALF_BYTES = 16 * 2
TILE_ROW0_COL16_OFF = 16 * 16 * 2

K0_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
K1_L1 = K0_L1 + PAGE
COS_L1 = K1_L1 + PAGE
SIN_L1 = COS_L1 + PAGE
DST_L1 = SIN_L1 + PAGE


def row0_offset(lane: int) -> int:
  if lane < 16:
    return lane * 2
  return TILE_ROW0_COL16_OFF + (lane - 16) * 2


def row_tile_table(x: np.ndarray) -> np.ndarray:
  tiles = np.zeros((x.shape[0], TILE, TILE), dtype=np.float32)
  tiles[:, 0, :] = x
  return tiles


def emit_read_page(fw: Brisc, *, base_reg, page_reg, l1_dst: int) -> None:
  fw.mv(a0, base_reg)
  fw.mv(a1, page_reg)
  fw.mv(a2, s5)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, l1_dst)
  fw.li(t6, PAGE)
  fw.noc_read(0, 1, a0, 0, a2, t2, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(0, t4, addr=t0, val=t1)


def emit_write_page(fw: Brisc, *, page_reg) -> None:
  fw.mv(a0, s3)
  fw.mv(a1, page_reg)
  fw.mv(a2, s5)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, DST_L1)
  fw.li(t6, PAGE)
  fw.noc_write(0, 0, t2, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(0, t4, addr=t0, val=t1)


def emit_zero_dst(fw: Brisc) -> None:
  loop = fw._new_label("zero_dst_loop")
  fw.li(t0, DST_L1)
  fw.li(t1, DST_L1 + PAGE)
  fw.label(loop)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.bltu(t0, t1, loop)


def emit_copy_group(fw: Brisc, *, src_l1: int, dst_base_row: int) -> None:
  for lane in range(TILE):
    row = dst_base_row + lane // 8
    col = (lane & 7) * 2
    fw.li(t1, src_l1)
    fw.lhu(t0, t1, row0_offset(lane))
    fw.li(t2, DST_L1 + rope.packed_elem_offset(row, col))
    fw.sh(t0, t2, 0)


def emit_k_stage_body(fw: Brisc, *, heads: int, k_start_tile: int) -> Brisc:
  for head in range(heads):
    fw.li(t0, k_start_tile + head * 2)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=K0_L1)
    fw.li(t0, k_start_tile + head * 2 + 1)
    emit_read_page(fw, base_reg=s0, page_reg=t0, l1_dst=K1_L1)
    emit_read_page(fw, base_reg=s1, page_reg=s4, l1_dst=COS_L1)
    emit_read_page(fw, base_reg=s2, page_reg=s4, l1_dst=SIN_L1)

    emit_zero_dst(fw)
    emit_copy_group(fw, src_l1=K0_L1, dst_base_row=rope.X1_OFF)
    emit_copy_group(fw, src_l1=K1_L1, dst_base_row=rope.X2_OFF)
    emit_copy_group(fw, src_l1=COS_L1, dst_base_row=rope.COS_OFF)
    emit_copy_group(fw, src_l1=SIN_L1, dst_base_row=rope.SIN_OFF)
    fw.li(t0, head)
    emit_write_page(fw, page_reg=t0)
  return fw


def k_stage_kernel(*, heads: int, k_start_tile: int) -> Brisc:
  fw = Brisc()
  # RTAs: QKV C base, cos table base, sin table base, RoPE src base, pos, banks.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5))
  emit_k_stage_body(fw, heads=heads, k_start_tile=k_start_tile)

  fw.ret()
  return fw


def build_stage_program(c_addr: int, cos_addr: int, sin_addr: int, dst_addr: int,
                        pos: int, num_banks: int, *, core, heads: int,
                        k_start_tile: int) -> Program:
  brisc_fw = k_stage_kernel(heads=heads, k_start_tile=k_start_tile)
  brisc_fw.rta(lambda _x, _y: [
    c_addr, cos_addr, sin_addr, dst_addr,
    pos() if callable(pos) else pos,
    num_banks,
  ])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "qkv_k_stage_rope_src"
  return prog


def k_stage_then_rope_reader_kernel(*, heads: int, k_start_tile: int) -> Brisc:
  fw = Brisc()
  # RTAs: QKV C base, cos table base, sin table base, RoPE src base, pos, banks.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5))
  for addr in (
    add1.SYNC_TRISC_START, add1.SYNC_READ, add1.SYNC_DONE0, add1.SYNC_DONE1, add1.SYNC_DONE2,
    add1.SYNC_TRISC_INIT, add1.SYNC_TRISC_INIT + 4, add1.SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  emit_k_stage_body(fw, heads=heads, k_start_tile=k_start_tile)

  fw.write32(add1.SYNC_TRISC_START, 0x00010101)
  fw.mv(s0, s3)       # staged RoPE source base
  fw.li(s2, 0)        # first source tile
  fw.li(s3, heads)    # tiles/heads
  # s5 still holds DRAM bank count from the stage RTAs; add1.brisc uses s4.
  fw.mv(s4, s5)
  with fw.tile_loop("brisc"):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.add(a1, s2, s5)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.local_noc0_coord(a5)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.addi(t4, t4, 1)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
    fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.label("brisc_read_wait")
    fw.lw(t1, t0, 0)
    fw.bltu(t1, t4, "brisc_read_wait")
    fw.fence()
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(add1.SYNC_READ, t2)
  return fw


def build_stage_rope_program(c_addr: int, cos_addr: int, sin_addr: int,
                             src_addr: int, cache_addr: int, pos: int,
                             max_seq: int, num_banks: int, *, core,
                             heads: int, k_start_tile: int) -> Program:
  brisc_fw = k_stage_then_rope_reader_kernel(heads=heads, k_start_tile=k_start_tile)
  ncrisc_fw = rope.ncrisc_k_scatter(max_seq)
  trisc0_fw = add1.trisc0()
  trisc1_fw = rope.trisc1_rope()
  trisc2_fw = add1.trisc2()

  brisc_fw.rta(lambda _x, _y: [
    c_addr, cos_addr, sin_addr, src_addr,
    pos() if callable(pos) else pos,
    num_banks,
  ])
  ncrisc_fw.rta(lambda _x, _y: [
    cache_addr,
    pos() if callable(pos) else pos,
    heads,
    num_banks,
  ])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [heads])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "qkv_k_stage_rope_scatter"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="QKV K stage into RoPE+K scatter; needs device")
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--heads", type=int, default=8)
  p.add_argument("--head-dim", type=int, default=64)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--split", action="store_true", help="run the old stage + RoPE two-launch path")
  args = p.parse_args()
  if args.head_dim != HEAD_DIM:
    raise ValueError("this bridge currently assumes head_dim=64")
  if args.heads * args.head_dim != args.kv_dim:
    raise ValueError("heads * head_dim must equal kv_dim")
  if args.max_seq % (PAGE // ROW_BYTES) != 0:
    raise ValueError("--max-seq must keep each head cache region page-aligned")
  if args.pos >= args.max_seq:
    raise ValueError("--pos must be < --max-seq")

  rng = np.random.default_rng(97)
  n = args.dim + 2 * args.kv_dim
  npad = ((n + TILE - 1) // TILE) * TILE
  qkv = rope.to_bf16(rng.uniform(-2.0, 2.0, size=(npad,)).astype(np.float32))
  qkv[args.dim + args.kv_dim:n] = 0.0  # V slice irrelevant here; keep it quiet.
  cos_table = rope.to_bf16(rng.uniform(-1.0, 1.0, size=(args.max_seq, TILE)).astype(np.float32))
  sin_table = rope.to_bf16(rng.uniform(-1.0, 1.0, size=(args.max_seq, TILE)).astype(np.float32))

  c = np.zeros((TILE, npad), dtype=np.float32)
  c[0, :] = qkv
  k = qkv[args.dim:args.dim + args.kv_dim].reshape(args.heads, args.head_dim)
  cos = cos_table[args.pos]
  sin = sin_table[args.pos]
  ref = np.empty_like(k)
  ref[:, :32] = k[:, :32] * cos - k[:, 32:] * sin
  ref[:, 32:] = k[:, 32:] * cos + k[:, :32] * sin
  ref_bf16 = rope.to_bf16(ref)

  with harness.open_device() as device:
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    c_buf = device.alloc_write(mm.to_bf16_device_bytes(c), dtype=Dtype.Float16_b,
                               shape=c.shape, name="qkv_c")
    cos_buf = device.alloc_write(rope.to_bf16_bytes(row_tile_table(cos_table)),
                                 dtype=Dtype.Float16_b,
                                 shape=(args.max_seq, TILE, TILE), name="cos_rows")
    sin_buf = device.alloc_write(rope.to_bf16_bytes(row_tile_table(sin_table)),
                                 dtype=Dtype.Float16_b,
                                 shape=(args.max_seq, TILE, TILE), name="sin_rows")
    rope_src_buf = device.dram.alloc(args.heads, dtype=Dtype.Float16_b,
                                     shape=(args.heads, TILE, TILE), name="rope_src")
    k_cache_tiles = args.heads * args.max_seq * ROW_BYTES // PAGE
    k_cache_buf = device.dram.alloc(k_cache_tiles, dtype=Dtype.Float16_b, name="k_cache")
    device.dram_write(rope_src_buf, b"\0" * rope_src_buf.size)
    device.dram_write(k_cache_buf, b"\0" * k_cache_buf.size)

    if args.split:
      stage_prog = build_stage_program(
        c_buf.addr, cos_buf.addr, sin_buf.addr, rope_src_buf.addr,
        args.pos, num_banks, core=core, heads=args.heads,
        k_start_tile=args.dim // TILE,
      )
      rope_prog = rope.build_program(
        rope_src_buf.addr, k_cache_buf.addr, args.pos, args.max_seq,
        num_banks, core=core, heads=args.heads,
      )
      programs = (stage_prog, rope_prog)
    else:
      combined_prog = build_stage_rope_program(
        c_buf.addr, cos_buf.addr, sin_buf.addr, rope_src_buf.addr, k_cache_buf.addr,
        args.pos, args.max_seq, num_banks, core=core, heads=args.heads,
        k_start_tile=args.dim // TILE,
      )
      programs = (combined_prog,)
    timings = []
    for _ in range(args.runs):
      for prog in programs:
        timings.extend(device.run(prog))
    src_raw = device.dram_read(rope_src_buf)
    cache_raw = device.dram_read(k_cache_buf)

  got_src = np.frombuffer(src_raw, dtype=np.uint16).reshape(args.heads, TILE, TILE)
  src_ok = True
  expected_src = np.zeros((args.heads, TILE, TILE), dtype=np.float32)
  for h in range(args.heads):
    rope.footprint_put(expected_src[h], rope.X1_OFF, k[h, :32])
    rope.footprint_put(expected_src[h], rope.X2_OFF, k[h, 32:])
    rope.footprint_put(expected_src[h], rope.COS_OFF, cos)
    rope.footprint_put(expected_src[h], rope.SIN_OFF, sin)
  expected_src_u16 = np.frombuffer(rope.to_bf16_bytes(expected_src), dtype=np.uint16).reshape(
    args.heads, TILE, TILE)
  src_ok = bool(np.array_equal(got_src, expected_src_u16))

  got_u16 = np.frombuffer(cache_raw, dtype=np.uint16).reshape(args.heads, args.max_seq, args.head_dim)
  got = rope.from_bf16_u16(got_u16[:, args.pos, :])
  untouched = bool(np.all(got_u16[:, :args.pos, :] == 0) and np.all(got_u16[:, args.pos + 1:, :] == 0))
  cache_ok = bool(np.allclose(got, ref_bf16, atol=5.0e-2, rtol=5.0e-2))
  ok = src_ok and cache_ok and untouched

  mode = "split" if args.split else "combined"
  print("QKV K stage -> RoPE + K-cache scatter")
  print(f"  heads={args.heads} pos={args.pos} max_seq={args.max_seq} runs={args.runs}")
  print(f"  mode={mode}")
  if timings:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in timings) / len(timings):.1f} us")
  print(f"  RoPE source footprint: {'PASS' if src_ok else 'FAIL'}")
  print(f"  K cache row: {'PASS' if cache_ok else 'FAIL'}")
  if not cache_ok:
    diff = np.abs(got - ref_bf16)
    h, d = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    max diff head={h} dim={d} got={float(got[h, d]):.6g} ref={float(ref_bf16[h, d]):.6g}")
  print(f"  untouched rows: {'PASS' if untouched else 'FAIL'}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
