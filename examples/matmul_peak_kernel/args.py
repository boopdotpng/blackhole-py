"""Construct each controller's scratch arguments from common launch data + rank.

The host supplies only common buffers/scalars, one topology map, and runtime
(ri, ci). These scratch tables preserve the existing fixed-register recipes;
no per-core argument table is uploaded or baked into a kernel image.
"""
from firmware.consts import TensixL1
from .asm import ARG_BASE, GRID_BASE
from ttko.isa import R, Tensix as TT


def emit_args(fw, plan, *, reader):
  base = ARG_BASE if reader else ARG_BASE + 128
  def put(index, value): fw.write32(base + index * 4, value)
  def param(index, target): fw.read32(target, TensixL1.PARAM_BASE + index * 4)
  def coord(rank, table, target):
    fw.li(R.T0, table)
    fw.slli(R.T1, rank, 2)
    fw.add(R.T0, R.T0, R.T1)
    fw.lw(target, R.T0, 0)

  fw.read32(R.S0, TensixL1.GRID_RANK_BASE)
  fw.read32(R.S1, TensixL1.GRID_RANK_BASE + 4)
  coord(R.S0, GRID_BASE, R.S2)  # my physical y
  coord(R.S1, GRID_BASE + 256, R.S3)  # my physical x
  fw.read32(R.S4, GRID_BASE + 256)  # A sender x
  fw.read32(R.S5, GRID_BASE)  # B sender y
  if reader:
    values = [0, 0, 1, plan.kt, plan.in0_block_w, plan.in0_block_w,
              plan.per_core_m, plan.in0_block_num_tiles, plan.num_blocks,
              *([0] * 10), 0, 0, 0, 1, 0]
    for index, value in enumerate(values): put(index, value)
    param(0, R.T2); put(0, R.T2)
    fw.li(R.T1, plan.per_core_m * plan.kt)
    fw.mul(R.T2, R.S0, R.T1); put(1, R.T2)
    put(19, R.S4); put(20, R.S2)
    param(3, R.T2); put(23, R.T2)
    # The common column map may be noncontiguous. Split around the non-worker
    # columns just as the original row protocol did, excluding logical ci=0.
    fw.li(R.S6, 1)
    fw.li(R.S7, len(plan.cols))
    loop, east, advance, done = (fw._new_label(n) for n in ('a_rect', 'a_east', 'a_next', 'a_rect_done'))
    fw.label(loop)
    fw.bge(R.S6, R.S7, done)
    coord(R.S6, GRID_BASE + 256, R.S3)
    fw.li(R.T1, 8)
    fw.bge(R.S3, R.T1, east)
    for offset, label in ((9, None), (14, east)):
      if label: fw.label(label)
      fw.read32(R.T2, base + (offset + 4) * 4)
      existing = fw._new_label('rect_existing')
      fw.bne(R.T2, R.ZERO, existing)
      put(offset, R.S3)
      fw.label(existing)
      put(offset + 1, R.S2); put(offset + 2, R.S3); put(offset + 3, R.S2)
      fw.addi(R.T2, R.T2, 1); put(offset + 4, R.T2)
      fw.j(advance)
    fw.label(advance)
    fw.addi(R.S6, R.S6, 1)
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
    param(1, R.T2); put(0, R.T2)
    fw.li(R.T1, plan.per_core_n * plan.n_passes); fw.mul(R.S6, R.S1, R.T1); put(1, R.S6)
    if len(plan.rows) > 1:
      put(9, R.S3); put(11, R.S3)
      fw.read32(R.T2, GRID_BASE + (len(plan.rows) - 1) * 4); put(10, R.T2)
      fw.read32(R.T2, GRID_BASE + 4); put(12, R.T2)
      put(13, len(plan.rows) - 1)
    put(14, R.S3); put(15, R.S5)
    param(2, R.T2); put(18, R.T2)
    fw.li(R.T1, plan.per_core_m * plan.nt)
    fw.mul(R.T2, R.S0, R.T1); fw.add(R.T2, R.T2, R.S6); put(19, R.T2)
    param(3, R.T2); put(29, R.T2)
  return fw.fence()
