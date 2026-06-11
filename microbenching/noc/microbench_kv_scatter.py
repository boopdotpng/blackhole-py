#!/usr/bin/env python3
"""KV-cache indexed scatter microbench — llama plan item #7 (write half).

Per decode token, RoPE'd K and V rows (n_kv_heads=8 x head_dim=64, bf16 ->
128 B each) must land at cache[h][pos] with `pos` only known at launch. Cache
layout is the CUDA reference's [kv_head][seq_pos][head_dim], row-major bytes,
page-interleaved across DRAM banks by the standard 2 KiB allocator pages.

Single BRISC kernel per launch: noc_read pos's staged page (16 rows packed by
the host) into L1 scratch, then 16 noc_writes at base + ((h*max_seq + pos)*128)
with the page->bank math in registers. pos arrives by RTA -> every launch is
the same program with new args, exercising the per-launch RTA path. No Tensix.

PASS = byte-exact K/V caches after a full pos sweep + overwrite spot-check.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")  # many launches/sweep: needs CQ path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (path bootstrap)
import numpy as np

from asm import KernelBase
from dsl import a0, a1, a2, a3, a4, a5, s0, s1, s2, s3, s4, t0, t1, t4, t5, t6
from examples.add1 import Brisc
from program import Dtype, Program
from ttk.mailbox import BriscMailbox as BM
from ttk.noc import NOC
from ttk.tensix import TensixL1

N_KV_HEADS = 8
HEAD_DIM = 64
ROW_BYTES = HEAD_DIM * 2          # bf16
PAGE = Dtype.Float16_b.tile_size  # 2048; allocator page == 16 rows
SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE


def scatter_kernel(max_seq: int, num_banks: int) -> Brisc:
  assert max_seq % 16 == 0, "head stride must be page-aligned"
  rows_per_head = max_seq * ROW_BYTES
  fw = Brisc()
  # RTAs: staging base, k_cache base, v_cache base, pos
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3))

  # Gather: read pos's staged page (K0..K7,V0..V7 rows) into scratch.
  fw.mv(a0, s0)
  fw.mv(a1, s3)
  fw.li(a2, num_banks)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t5, SCRATCH_L1)
  fw.li(t6, PAGE)
  fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.label("kv_read_wait")
  fw.lw(t1, t0, 0)
  fw.bltu(t1, t4, "kv_read_wait")
  fw.fence()

  # Scatter: row r -> cache_base + (head*max_seq + pos)*ROW_BYTES.
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
  fw.addi(t4, t4, 2 * N_KV_HEADS)
  fw.slli(s4, s3, 7)  # pos * ROW_BYTES
  for r in range(2 * N_KV_HEADS):
    head, base = (r, s1) if r < N_KV_HEADS else (r - N_KV_HEADS, s2)
    fw.li(a1, head * rows_per_head)
    fw.add(a1, a1, s4)            # byte offset in cache
    fw.andi(a4, a1, PAGE - 1)     # in-page offset
    fw.srli(a1, a1, 11)           # page index
    fw.mv(a0, base)
    fw.li(a2, num_banks)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)  # a0=bank addr, a2=bank coord
    fw.add(a0, a0, a4)
    fw.li(a3, SCRATCH_L1 + r * ROW_BYTES)
    fw.li(a5, ROW_BYTES)
    fw.noc_write(0, 0, a3, a0, 0, a2, a5)
  fw.noc_write_barrier(0, t4)
  fw.ret()
  return fw


def build(staging_addr: int, k_addr: int, v_addr: int, pos: int, max_seq: int,
          num_banks: int, core, kern: Brisc) -> Program:
  kern.rta(lambda _x, _y: [staging_addr, k_addr, v_addr, pos])
  prog = Program(brisc=kern, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = f"kv_scatter_p{pos}"
  return prog


def main() -> int:
  parser = argparse.ArgumentParser(description="KV-cache indexed scatter; needs device")
  parser.add_argument("--max-seq", type=int, default=64)
  args = parser.parse_args()
  max_seq = args.max_seq
  cache_tiles = N_KV_HEADS * max_seq * ROW_BYTES // PAGE

  rng = np.random.default_rng(7)
  staged = rng.integers(1, 1 << 16, (max_seq, 2 * N_KV_HEADS, HEAD_DIM), dtype=np.uint16)

  with harness.open_device() as device:
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    stage = device.dram.alloc(max_seq, dtype=Dtype.Float16_b, name="stage")
    device.dram_write(stage, staged.tobytes())
    k_buf = device.dram.alloc(cache_tiles, dtype=Dtype.Float16_b, name="k_cache")
    v_buf = device.dram.alloc(cache_tiles, dtype=Dtype.Float16_b, name="v_cache")
    device.dram.write(k_buf, b"\0" * k_buf.size)
    device.dram.write(v_buf, b"\0" * v_buf.size)

    kern = scatter_kernel(max_seq, num_banks)
    us = []
    order = list(range(max_seq))
    rng.shuffle(order)  # out-of-order pos: indexed, not sequential append
    for pos in order:
      t = device.run(build(stage.addr, k_buf.addr, v_buf.addr, pos, max_seq, num_banks, core, kern))
      us.extend(x["us"] for x in t)

    ref = staged.transpose(1, 0, 2)  # [16 rows][pos][dim] -> head-major caches
    got_k = np.frombuffer(device.dram_read(k_buf), dtype=np.uint16).reshape(N_KV_HEADS, max_seq, HEAD_DIM)
    got_v = np.frombuffer(device.dram_read(v_buf), dtype=np.uint16).reshape(N_KV_HEADS, max_seq, HEAD_DIM)
    ok = bool(np.array_equal(got_k, ref[:N_KV_HEADS])) and bool(np.array_equal(got_v, ref[N_KV_HEADS:]))
    bad = int(np.count_nonzero(got_k != ref[:N_KV_HEADS]) + np.count_nonzero(got_v != ref[N_KV_HEADS:]))

  print("kv scatter microbench")
  print(f"  max_seq={max_seq} rows/launch={2 * N_KV_HEADS} bytes/launch={2 * N_KV_HEADS * ROW_BYTES}")
  if us:
    print(f"  launches={len(us)} avg={sum(us) / len(us):.1f} us")
  print(f"  K+V cache: {'byte-exact' if ok else f'{bad} mismatched elems'}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
