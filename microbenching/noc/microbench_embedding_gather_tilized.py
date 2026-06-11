#!/usr/bin/env python3
"""Embedding gather directly into the skinny-GEMV tilized input layout.

The earlier embedding gather validates the data-dependent DRAM row read, but it
writes a row-major output row. Llama decode wants the selected embedding to feed
the existing M=1 GEMV path, whose input buffer is a padded 32 x dim tilized
matrix with only row 0 populated.

This kernel reads token ids from device memory, gathers row-major bf16
embedding rows, and writes each row into row 0 of a tilized 32-row output slot.
The caller keeps the output pre-zeroed so padded rows stay zero.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import numpy as np

from asm import KernelBase, cond
from dsl import (
  a0, a1, a2,
  s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11,
  t0, t1, t2, t3, t4, t5, t6,
)
from program import Dtype, Program
from ttk import Cb, Noc
from ttk.mailbox import Firmware, NcriscMailbox as NM
from ttk.noc import NOC
from ttk.tensix import TensixL1

PAGE = Dtype.Float16_b.tile_size
ROW_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
IDX_L1 = TensixL1.DATA_BUFFER_SPACE_BASE + 0x8000
ROW_HALF_BYTES = 16 * 2
TILE_ROW0_COL16_OFF = 16 * 16 * 2

RD_STATUS = NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT)
WR_STATUS = NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT)


class EmbedGatherTilizedKernel(KernelBase, Noc, Cb):
  pass


def build_gather_tilized(dim_tiles: int, pages_per_row: int) -> EmbedGatherTilizedKernel:
  """RTAs: table_addr, idx_addr, out_addr, n_tokens, num_banks, idx_pages."""
  fw = EmbedGatherTilizedKernel(base_addr=Firmware.TEXT_BASE["ncrisc"])
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5))
  fw.local_noc0_coord(s7, x_addr=NM.MY_X + 1, y_addr=NM.MY_Y + 1)

  def read_page(base_reg, page_reg, l1_dst_reg):
    fw.mv(a0, base_reg)
    fw.mv(a1, page_reg)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s4)
    fw.read32(s10, RD_STATUS, tmp_addr=t0)
    fw.addi(s10, s10, 1)
    fw.li(t6, PAGE)
    fw.noc_read(1, 1, a0, 0, a2, l1_dst_reg, t6, ret_coord=s7, a=t0, v=t1)
    fw.noc_reads_flushed(1, s10, addr=t0, val=t1)

  def write_chunk(out_page_reg, out_off: int, l1_src_reg):
    fw.mv(a0, s2)
    fw.mv(a1, out_page_reg)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s4)
    if out_off:
      fw.addi(a0, a0, out_off)
    fw.li(t6, ROW_HALF_BYTES)
    fw.noc_write(1, 0, l1_src_reg, a0, 0, a2, t6, a=t0, v=t1)

  # Stage token ids once; each id is then loaded from L1, not from an RTA.
  fw.li(s8, 0)
  with fw.while_(cond(s8, "<u", s5)):
    fw.slli(t3, s8, 11)
    fw.li(t5, IDX_L1)
    fw.add(t5, t5, t3)
    read_page(s1, s8, t5)
    fw.addi(s8, s8, 1)

  fw.li(s8, 0)  # token slot
  with fw.while_(cond(s8, "<u", s3)):
    fw.slli(t3, s8, 2)
    fw.li(t5, IDX_L1)
    fw.add(t5, t5, t3)
    fw.lw(s9, t5, 0)                    # token id

    fw.li(t3, pages_per_row)
    fw.mul(s9, s9, t3)                  # first source row page
    for page in range(pages_per_row):
      fw.li(t5, ROW_L1 + page * PAGE)
      read_page(s0, s9, t5)
      fw.addi(s9, s9, 1)

    fw.li(t3, dim_tiles)
    fw.mul(s11, s8, t3)                 # first output tile page for this slot
    fw.li(s6, 0)                        # column tile
    with fw.while_(cond(s6, "<u", t3)):
      fw.slli(t4, s6, 6)                # source byte offset: tile * 32 bf16s
      fw.li(t5, ROW_L1)
      fw.add(t5, t5, t4)
      fw.add(s9, s11, s6)               # output tile page; dram_tile_addr_from clobbers t0..t2

      fw.read32(s10, WR_STATUS, tmp_addr=t0)
      fw.addi(s10, s10, 2)
      write_chunk(s9, 0, t5)
      fw.addi(t5, t5, ROW_HALF_BYTES)
      write_chunk(s9, TILE_ROW0_COL16_OFF, t5)
      fw.noc_write_barrier(1, s10, addr=t0, val=t1)
      fw.addi(s6, s6, 1)

    fw.addi(s8, s8, 1)
  return fw.ret()


def build_program(table_addr: int, idx_addr: int, out_addr: int, n_tokens: int,
                  num_banks: int, idx_pages: int, dim_tiles: int,
                  pages_per_row: int, *, core) -> Program:
  gather = build_gather_tilized(dim_tiles, pages_per_row)
  gather.rta(lambda _x, _y: [table_addr, idx_addr, out_addr, n_tokens, num_banks, idx_pages])
  empty = lambda: KernelBase()  # noqa: E731
  prog = Program(brisc=empty(), ncrisc=gather, trisc0=empty(), trisc1=empty(), trisc2=empty(),
                 cbs=[(0, PAGE, 2)])
  prog.grid = ((core[1],), (core[0],))
  prog.name = "embed_gather_tilized"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="embedding gather into tilized GEMV input; needs device")
  p.add_argument("--rows", type=int, default=4096, help="vocab rows in table")
  p.add_argument("--dim", type=int, default=2048, help="embedding width, bf16 elements")
  p.add_argument("--tokens", type=int, default=16)
  args = p.parse_args()
  if args.dim % 1024 != 0:
    raise ValueError("dim must be a multiple of 1024 so rows align to DRAM pages")
  if args.dim % 32 != 0:
    raise ValueError("dim must be a multiple of 32 for tilized output")

  pages_per_row = args.dim * 2 // PAGE
  dim_tiles = args.dim // 32

  rng = np.random.default_rng(11)
  table = rng.integers(0, 1 << 16, (args.rows, args.dim), dtype=np.uint16)
  ids = rng.integers(0, args.rows, args.tokens, dtype=np.uint32)
  ids[0], ids[-1] = 0, args.rows - 1

  idx_bytes = ids.tobytes()
  idx_pages = (len(idx_bytes) + PAGE - 1) // PAGE
  idx_bytes = idx_bytes.ljust(idx_pages * PAGE, b"\0")

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)

    table_buf = device.dram.alloc(table.nbytes // PAGE, dtype=Dtype.Float16_b, name="embed_table_rowmajor")
    device.dram_write(table_buf, table.tobytes())
    idx_buf = device.dram.alloc(idx_pages, dtype=Dtype.Float16_b, name="embed_idx")
    device.dram_write(idx_buf, idx_bytes)
    out_shape = (args.tokens * 32, args.dim)
    out_buf = device.dram.alloc(args.tokens * dim_tiles, dtype=Dtype.Float16_b,
                                shape=out_shape, name="embed_x_tilized")
    device.dram_write(out_buf, b"\0" * (args.tokens * args.dim * 32 * 2))

    prog = build_program(table_buf.addr, idx_buf.addr, out_buf.addr, args.tokens, nb,
                         idx_pages, dim_tiles, pages_per_row, core=core)
    timings = device.run(prog)
    got = np.frombuffer(device.dram_read(out_buf), dtype=np.uint16).reshape(out_shape)

  ref = np.zeros(out_shape, dtype=np.uint16)
  ref[0::32, :] = table[ids]
  ok = bool(np.array_equal(got, ref))
  bad_rows = int(np.count_nonzero((got != ref).any(axis=1)))

  print("embedding gather tilized microbench")
  print(f"  rows={args.rows} dim={args.dim} tokens={args.tokens} dim_tiles={dim_tiles}")
  if timings:
    print(f"  launch={sum(t['us'] for t in timings):.1f} us")
  print(f"  untilized output rows exact: {out_shape[0] - bad_rows}/{out_shape[0]}")
  if not ok:
    row = int(np.argmax((got != ref).any(axis=1)))
    cols = np.flatnonzero(got[row] != ref[row])
    col = int(cols[0])
    print(f"    first bad row={row} col={col} bad_cols={cols[:12].tolist()}")
    lo, hi = max(0, col - 4), min(args.dim, col + 12)
    print(f"    got[{lo}:{hi}]={got[row, lo:hi].tolist()}")
    print(f"    ref[{lo}:{hi}]={ref[row, lo:hi].tolist()}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
