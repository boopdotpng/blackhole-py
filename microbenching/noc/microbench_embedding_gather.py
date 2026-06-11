#!/usr/bin/env python3
"""Blackhole embedding-gather microbench (#7): indexed DRAM row gather.

x = table[token] -- the llama3 embed_kernel. Pure data movement: NCRISC reads
the token-id buffer into L1, then per token computes the table page from the
*loaded* id (the new primitive: tile id from data, not from a counter), and
noc_reads the row -> L1 -> noc_writes it to the output row slot.

Layout: table is row-major in interleaved DRAM with the default 2048-byte
page; one row = dim*2/2048 pages (2 pages at dim=2048). Page p lives in bank
p % num_banks at offset (p // num_banks) << 11 -- exactly dram_tile_addr_from.

Modeled on fw/dram.py::build_drain (NCRISC, NOC1, NM mailbox). Validation is
exact bytes (it's a copy).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import numpy as np

from asm import KernelBase, cond
from dsl import a0, a1, a2, s0, s1, s2, s3, s4, s5, s7, s8, s9, s10, s11, t0, t1, t3, t5, t6
from program import Dtype, Program
from ttk import Cb, Noc
from ttk.mailbox import Firmware, NcriscMailbox as NM
from ttk.noc import NOC
from ttk.tensix import TensixL1

PAGE = 2048                       # default interleave page (== bf16 tile bytes)
DTYPE = Dtype.Float16_b
ROW_L1 = TensixL1.DATA_BUFFER_SPACE_BASE          # staged row (pages_per_row pages)
IDX_L1 = TensixL1.DATA_BUFFER_SPACE_BASE + 0x8000  # staged token ids (u32)

RD_STATUS = NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT)
WR_STATUS = NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT)


class EmbedGatherKernel(KernelBase, Noc, Cb):
  pass


def build_gather(pages_per_row: int) -> EmbedGatherKernel:
  """RTAs: s0=table_addr s1=idx_addr s2=out_addr s3=n_tokens s4=num_banks s5=idx_pages."""
  fw = EmbedGatherKernel(base_addr=Firmware.TEXT_BASE["ncrisc"])
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

  def write_page(base_reg, page_reg, l1_src_reg):
    fw.mv(a0, base_reg)
    fw.mv(a1, page_reg)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s4)
    fw.read32(s10, WR_STATUS, tmp_addr=t0)
    fw.addi(s10, s10, 1)
    fw.li(t6, PAGE)
    fw.noc_write(1, 0, l1_src_reg, a0, 0, a2, t6, a=t0, v=t1)
    fw.noc_write_barrier(1, s10, addr=t0, val=t1)

  # stage the token-id buffer into L1 (idx_pages sequential pages)
  fw.li(s8, 0)
  with fw.while_(cond(s8, "<u", s5)):
    fw.slli(t3, s8, 11)
    fw.li(t5, IDX_L1)
    fw.add(t5, t5, t3)
    read_page(s1, s8, t5)
    fw.addi(s8, s8, 1)

  # per token: load id from L1 (the gather), fetch row, store to out slot
  fw.li(s8, 0)
  with fw.while_(cond(s8, "<u", s3)):
    fw.slli(t3, s8, 2)
    fw.li(t5, IDX_L1)
    fw.add(t5, t5, t3)
    fw.lw(s9, t5, 0)                       # s9 = token id (from data!)
    fw.li(t3, pages_per_row)
    fw.mul(s9, s9, t3)                     # s9 = first table page of the row
    fw.li(t3, pages_per_row)
    fw.mul(s11, s8, t3)                    # s11 = first out page of slot s8
    for half in range(pages_per_row):
      fw.li(t5, ROW_L1 + half * PAGE)
      read_page(s0, s9, t5)
      fw.addi(s9, s9, 1)
    for half in range(pages_per_row):
      fw.li(t5, ROW_L1 + half * PAGE)
      write_page(s2, s11, t5)
      fw.addi(s11, s11, 1)
    fw.addi(s8, s8, 1)
  return fw.ret()


def build_program(table_addr, idx_addr, out_addr, n_tokens, num_banks, idx_pages,
                  pages_per_row, *, core) -> Program:
  gather = build_gather(pages_per_row)
  gather.rta(lambda x, y: [table_addr, idx_addr, out_addr, n_tokens, num_banks, idx_pages])
  empty = lambda: KernelBase()  # noqa: E731
  prog = Program(brisc=empty(), ncrisc=gather, trisc0=empty(), trisc1=empty(), trisc2=empty(),
                 cbs=[(0, PAGE, 2)])
  prog.grid = ((core[1],), (core[0],))
  prog.name = "embed_gather"
  return prog


def main() -> int:
  import argparse
  p = argparse.ArgumentParser(description="embedding gather microbench; needs device")
  p.add_argument("--rows", type=int, default=1024, help="vocab rows in table")
  p.add_argument("--dim", type=int, default=2048, help="row width (elements, bf16)")
  p.add_argument("--tokens", type=int, default=64)
  args = p.parse_args()
  assert (args.dim * 2) % PAGE == 0
  pages_per_row = args.dim * 2 // PAGE

  rng = np.random.default_rng(7)
  table = rng.integers(0, 1 << 16, (args.rows, args.dim), dtype=np.uint16)  # raw bf16 bits
  ids = rng.integers(0, args.rows, args.tokens, dtype=np.uint32)
  ids[0], ids[-1] = 0, args.rows - 1                                        # edge rows

  idx_bytes = ids.tobytes()
  idx_pages = (len(idx_bytes) + PAGE - 1) // PAGE
  idx_bytes = idx_bytes.ljust(idx_pages * PAGE, b"\0")

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    table_buf = device.alloc_write(table.tobytes(), dtype=DTYPE,
                                   shape=(args.rows * pages_per_row, 32, 32), name="embed_table")
    idx_buf = device.dram.alloc(idx_pages, dtype=DTYPE, name="embed_idx")
    device.dram_write(idx_buf, idx_bytes)
    out_buf = device.dram.alloc(args.tokens * pages_per_row, dtype=DTYPE,
                                shape=(args.tokens * pages_per_row, 32, 32), name="embed_out")
    prog = build_program(table_buf.addr, idx_buf.addr, out_buf.addr,
                         args.tokens, nb, idx_pages, pages_per_row, core=core)
    device.run(prog)
    got = np.frombuffer(device.dram_read(out_buf), dtype=np.uint16).reshape(args.tokens, args.dim)

  ref = table[ids]
  ok = bool(np.array_equal(got, ref))
  bad = int(np.count_nonzero((got != ref).any(axis=1)))
  print("embedding gather microbench")
  print(f"  rows={args.rows} dim={args.dim} tokens={args.tokens} pages/row={pages_per_row}")
  print(f"  exact-match rows: {args.tokens - bad}/{args.tokens}")
  if not ok:
    i = int(np.argmax((got != ref).any(axis=1)))
    print(f"    first bad token={i} id={int(ids[i])} got[:4]={got[i, :4]} ref[:4]={ref[i, :4]}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
