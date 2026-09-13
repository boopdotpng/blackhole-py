"""Construct each controller's scratch arguments from common launch data + rank.

The host supplies only common buffers/scalars, one topology map, and runtime
(ri, ci). These scratch tables preserve the existing fixed-register recipes;
no per-core argument table is uploaded or baked into a kernel image.
"""
from fw.consts import TensixL1
from .asm import ARG_BASE, GRID_BASE
from .isa import *


def emit_args(fw, plan, *, reader):
  base = ARG_BASE if reader else ARG_BASE + 128
  def put(index, value): fw.write32(base + index * 4, value)
  def param(index, target): fw.read32(target, TensixL1.PARAM_BASE + index * 4)
  def coord(rank, table, target):
    fw.li(t0, table)
    fw.slli(t1, rank, 2)
    fw.add(t0, t0, t1)
    fw.lw(target, t0, 0)

  fw.read32(s0, TensixL1.GRID_RANK_BASE)
  fw.read32(s1, TensixL1.GRID_RANK_BASE + 4)
  coord(s0, GRID_BASE, s2)  # my physical y
  coord(s1, GRID_BASE + 256, s3)  # my physical x
  fw.read32(s4, GRID_BASE + 256)  # A sender x
  fw.read32(s5, GRID_BASE)  # B sender y
  if reader:
    values = [0, 0, 1, plan.kt, plan.in0_block_w, plan.in0_block_w,
              plan.per_core_m, plan.in0_block_num_tiles, plan.num_blocks,
              *([0] * 10), 0, 0, 0, 1, 0]
    for index, value in enumerate(values): put(index, value)
    param(0, t2); put(0, t2)
    fw.li(t1, plan.per_core_m * plan.kt)
    fw.mul(t2, s0, t1); put(1, t2)
    put(19, s4); put(20, s2)
    param(3, t2); put(23, t2)
    # The common column map may be noncontiguous. Split around the non-worker
    # columns just as the original row protocol did, excluding logical ci=0.
    fw.li(s6, 1)
    fw.li(s7, len(plan.cols))
    loop, east, advance, done = (fw._new_label(n) for n in ('a_rect', 'a_east', 'a_next', 'a_rect_done'))
    fw.label(loop)
    fw.bge(s6, s7, done)
    coord(s6, GRID_BASE + 256, s3)
    fw.li(t1, 8)
    fw.bge(s3, t1, east)
    for offset, label in ((9, None), (14, east)):
      if label: fw.label(label)
      fw.read32(t2, base + (offset + 4) * 4)
      existing = fw._new_label('rect_existing')
      fw.bne(t2, zero, existing)
      put(offset, s3)
      fw.label(existing)
      put(offset + 1, s2); put(offset + 2, s3); put(offset + 3, s2)
      fw.addi(t2, t2, 1); put(offset + 4, t2)
      fw.j(advance)
    fw.label(advance)
    fw.addi(s6, s6, 1)
    fw.j(loop)
    fw.label(done)
  else:
    values = [0, 0, 1, plan.nt, plan.in0_block_w * plan.nt,
              plan.per_core_n, plan.in0_block_w, plan.in1_block_num_tiles,
              plan.num_blocks, *([0] * 7), 2, 3, 0, 0, 1, plan.nt,
              plan.out_subblock_w, plan.out_subblock_h * plan.nt,
              plan.out_subblock_w, plan.out_subblock_h, plan.out_subblock_num_tiles,
              plan.in1_num_subblocks, plan.in0_num_subblocks, 0, plan.in1_num_subblocks]
    for index, value in enumerate(values): put(index, value)
    param(1, t2); put(0, t2)
    fw.li(t1, plan.per_core_n); fw.mul(s6, s1, t1); put(1, s6)
    if len(plan.rows) > 1:
      put(9, s3); put(11, s3)
      fw.read32(t2, GRID_BASE + (len(plan.rows) - 1) * 4); put(10, t2)
      fw.read32(t2, GRID_BASE + 4); put(12, t2)
      put(13, len(plan.rows) - 1)
    put(14, s3); put(15, s5)
    param(2, t2); put(18, t2)
    fw.li(t1, plan.per_core_m * plan.nt)
    fw.mul(t2, s0, t1); fw.add(t2, t2, s6); put(19, t2)
    param(3, t2); put(29, t2)
  return fw.fence()
