"""Reusable BF16 matmul planning, data movement, and Tensix emission."""

from dataclasses import dataclass

from isa import R
from program import DType
from ttk.mop import LoopTemplate, MaskTemplate, NOP, Replay
from ttk.noc import NoC
from ttk.tensix import (
  Cfg, TensixRegs, TensixSem, TensixStall, TensixWait, ThreadCfg,
  tt_word,
)


TILE = 32
TILE_BYTES = 2048
SUBBLOCK = 2
K_BLOCK = 4


def _ceil_div(a: int, b: int) -> int:
  return (a + b - 1) // b


def _align_up(value: int, alignment: int) -> int:
  return _ceil_div(value, alignment) * alignment


def _add_constant(k, target: R, value: int):
  if value == 0: return
  if -2048 <= value <= 2047:
    k.addi(target, target, value)
  else:
    with k.scope():
      constant = k.reg(exclude=target); k.li(constant, value); k.add(target, target, constant)


@dataclass(frozen=True)
class MatmulPlan:
  rows: tuple[int, ...]
  cols: tuple[int, ...]
  mt: int
  kt: int
  nt: int
  per_core_m: int
  per_core_n: int
  block_w: int
  num_blocks: int
  subblock_h: int
  subblock_w: int

  @property
  def cores(self): return tuple((x, y) for y in self.rows for x in self.cols)

  @property
  def a_tiles(self): return self.per_core_m * self.block_w

  @property
  def b_tiles(self): return self.block_w * self.per_core_n

  @property
  def a_block_pages(self): return self.a_tiles + 1

  @property
  def b_block_pages(self): return self.b_tiles + 1

  @property
  def output_tiles(self): return self.per_core_m * self.per_core_n

  @property
  def subblock_tiles(self): return self.subblock_h * self.subblock_w

  @property
  def m_subblocks(self): return self.per_core_m // self.subblock_h

  @property
  def n_subblocks(self): return self.per_core_n // self.subblock_w


@dataclass(frozen=True)
class MatmulChunk:
  """One independently scheduled rectangle of a larger output matrix."""

  m0: int
  n0: int
  m: int
  n: int
  plan: MatmulPlan


def plan_matmul(m: int, k: int, n: int, cores) -> MatmulPlan:
  """Choose the largest full worker rectangle whose blocked working set fits L1."""
  if any(type(value) is not int or value <= 0 for value in (m, k, n)):
    raise ValueError("matmul dimensions must be positive integers")
  mt, kt_base, nt = (_ceil_div(value, TILE) for value in (m, k, n))
  block_w = K_BLOCK
  kt = _align_up(kt_base, block_w)
  sbh, sbw = min(SUBBLOCK, mt), min(SUBBLOCK, nt)
  core_set = set(cores)
  xs = tuple(sorted({x for x, _ in core_set}))
  ys = tuple(sorted({y for _, y in core_set}))
  best = None
  best_score = None
  for start in range(len(ys)):
    for stop in range(start + 1, len(ys) + 1):
      rows = ys[start:stop]
      # Keep fan-out inside the contiguous west worker rectangle. Point
      # multicasts across the x=7/10 routing gap and beyond six rows are not
      # reliable on current P100 firmware.
      if len(rows) > 6: continue
      if len(rows) > _ceil_div(mt, sbh): continue
      valid_cols = tuple(x for x in xs if all((x, y) in core_set for y in rows))
      valid_cols = tuple(x for x in valid_cols if x < 8)
      max_cols = min(len(valid_cols), 7, _ceil_div(nt, sbw))
      for count in range(1, max_cols + 1):
        cols = valid_cols[:count]
        pcm = _align_up(_ceil_div(mt, len(rows)), sbh)
        pcn = _align_up(_ceil_div(nt, len(cols)), sbw)
        # Two input blocks allow data movement to overlap compute. Each has a
        # trailing completion page; the single result CB alternates between
        # BF16 partials and the final output.
        l1_pages = 2 * ((pcm * block_w + 1) + (pcn * block_w + 1)) + pcm * pcn
        l1_bytes = l1_pages * TILE_BYTES
        if l1_bytes > 0x140000: continue
        padded_m, padded_n = pcm * len(rows), pcn * len(cols)
        score = (len(rows) * len(cols), -(padded_m * padded_n), -abs(len(rows) - len(cols)))
        if best_score is None or score > best_score:
          best, best_score = (rows, cols, padded_m, padded_n, pcm, pcn), score
  if best is None:
    raise ValueError(f"no blocked matmul plan fits M={m}, K={k}, N={n}")
  rows, cols, mt, nt, pcm, pcn = best
  return MatmulPlan(
    tuple(rows), tuple(cols), mt, kt, nt, pcm, pcn,
    block_w, kt // block_w, sbh, sbw,
  )


def plan_output_chunks(m: int, k: int, n: int, cores) -> tuple[MatmulChunk, ...]:
  """Recursively split an output until every chunk has an L1-resident plan."""
  pending = [(0, 0, m, n)]
  chunks = []
  while pending:
    m0, n0, cm, cn = pending.pop(0)
    try:
      chunks.append(MatmulChunk(m0, n0, cm, cn, plan_matmul(cm, k, cn, cores)))
      continue
    except ValueError:
      pass
    mt, nt = _ceil_div(cm, TILE), _ceil_div(cn, TILE)
    if mt <= 1 and nt <= 1:
      raise ValueError(f"cannot split M={cm}, K={k}, N={cn} into a valid matmul plan")
    if mt >= nt and mt > 1:
      first_tiles = mt // 2
      first = first_tiles * TILE
      pending[0:0] = [(m0, n0, first, cn), (m0 + first, n0, cm - first, cn)]
    else:
      first_tiles = nt // 2
      first = first_tiles * TILE
      pending[0:0] = [(m0, n0, cm, first), (m0, n0 + first, cm, cn - first)]
  return tuple(sorted(chunks, key=lambda chunk: (chunk.m0, chunk.n0)))


def _unpack_replay(context: int):
  base = (Cfg.THCON_SEC0_REG3_Base_address,
          Cfg.THCON_SEC0_REG3_Base_cntx1_address)[context]
  return (
    tt_word("TTUNPACR", 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1),
    tt_word("TTRDCFG", 12, base.addr32),
    tt_word("TTADDDMAREG", 0, 12, 12, 36),
    tt_word("TTSTALLWAIT", TensixStall.CFG, TensixWait.THCON),
    tt_word("TTWRCFG", 12, 0, base.addr32),
    NOP,
  )

UNPACK_CONTEXT0 = Replay(0, _unpack_replay(0))
UNPACK_CONTEXT1 = Replay(6, _unpack_replay(1))
UNPACK_AB_MOP = MaskTemplate(
  a0=UNPACK_CONTEXT0,
  skip_a0=UNPACK_CONTEXT1,
)


MATH_REPLAY = tuple(
  tt_word("TTMVMUL", 0, 0, mode, 0)
  for mode in (0, 1, 0, 2, 0, 1, 0, 4, 0, 1, 0, 2, 0, 1, 0, 5)
)

_UNPACK_CLEAR = tt_word("TTUNPACR_NOP", 1, 0, 0, 1, 0, 0, 0, 0, 1)
RELOAD_UNPACK_MOP = LoopTemplate(
  outer=4, inner=1,
  start=tt_word("TTUNPACR", 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1),
  loop=_UNPACK_CLEAR, last=_UNPACK_CLEAR, outer_last=_UNPACK_CLEAR,
)
_MATH_MOVE = tt_word("TTMOVA2D", 0, 0, 2, 2, 0)
RELOAD_MATH_MOP = LoopTemplate(
  outer=4, inner=2, loop=_MATH_MOVE,
  end0=tt_word("TTSETRWC", 3, 0, 0, 0, 0, 3),
  last=_MATH_MOVE, outer_last=_MATH_MOVE,
)


class Matmul:
  """Emit the five concurrent streams for one blocked BF16 matmul chunk."""

  # Shared per-core argument table.
  A_PAGE, B_PAGE, C_PAGE, A_SENDER, A_SENDER_COORD = range(5)

  def __init__(self, program, plan: MatmulPlan, a, b, output, a_cb, b_cb, output_cb,
               *, m_tile_offset=0, n_tile_offset=0, hifi=False):
    if any(buffer.dtype is not DType.BF16 for buffer in (a, b, output)):
      raise ValueError("matmul requires BF16 buffers")
    self.p, self.plan = program, plan
    self.a, self.b, self.output = a, b, output
    self.a_cb, self.b_cb, self.output_cb = a_cb, b_cb, output_cb
    self.m_tile_offset, self.n_tile_offset = m_tile_offset, n_tile_offset
    self.hifi = bool(hifi)
    self.a_reader = program.brisc.init_cb(a_cb)
    self.a_unpack = program.trisc0.init_cb(a_cb)
    self.b_reader = program.ncrisc.init_cb(b_cb)
    self.b_unpack = program.trisc0.init_cb(b_cb)
    self.output_pack = program.trisc2.init_cb(output_cb)
    self.output_writer = program.ncrisc.init_cb(output_cb)
    self.partial_unpack = program.trisc0.init_cb(output_cb)
    self.a_ready = program.l1(16, name="matmul_a_ready")
    self.b_ready = program.l1(16, name="matmul_b_ready")
    self.a_signal = program.l1(16, name="matmul_a_signal")
    self.b_signal = program.l1(16, name="matmul_b_signal")
    self.output_ready = program.l1(16, name="matmul_output_ready")
    self.unpack_context = program.trisc0.local.alloc(4, name="matmul_unpack_context")
    self.math_dest_offset = program.trisc1.local.alloc(4, name="matmul_math_dest_offset")
    self.pack_dest_offset = program.trisc2.local.alloc(4, name="matmul_pack_dest_offset")
    if a_cb.pages < 2 * plan.a_block_pages or b_cb.pages < 2 * plan.b_block_pages:
      raise ValueError("matmul input CBs require two payload-plus-completion blocks")
    self.a_coord_base = 5
    self.b_sender = self.a_coord_base + len(plan.cols) - 1
    self.b_sender_coord = self.b_sender + 1
    self.b_coord_base = self.b_sender_coord + 1
    self.core_index = self.b_coord_base + len(plan.rows) - 1

  def runtime_args(self):
    args = {}
    for ri, y in enumerate(self.plan.rows):
      for ci, x in enumerate(self.plan.cols):
        core = (x, y)
        row = [0] * max(15, self.core_index + 1)
        a_stride = self.a.padded_shape[1] // TILE
        b_stride = self.b.padded_shape[1] // TILE
        row[self.A_PAGE] = (self.m_tile_offset + ri * self.plan.per_core_m) * a_stride
        row[self.B_PAGE] = self.n_tile_offset + ci * self.plan.per_core_n
        row[self.C_PAGE] = ri * self.plan.per_core_m * self.plan.nt + ci * self.plan.per_core_n
        row[self.A_SENDER] = int(ci == 0)
        row[self.A_SENDER_COORD] = NoC.static_coord(self.plan.cols[0], y)
        for index, receiver_x in enumerate(self.plan.cols[1:]):
          row[self.a_coord_base + index] = NoC.rectangle(
            (self.plan.cols[1], y), (self.plan.cols[-1], y),
          )
        row[self.b_sender] = int(ri == 0)
        row[self.b_sender_coord] = NoC.static_coord(x, self.plan.rows[0])
        for index, receiver_y in enumerate(self.plan.rows[1:]):
          row[self.b_coord_base + index] = NoC.rectangle(
            (x, self.plan.rows[-1]), (x, self.plan.rows[1]),
          )
        row[self.core_index] = ri * len(self.plan.cols) + ci
        args[core] = row
    return args

  @staticmethod
  def _send_payload(noc, cb, coord_arg, size):
    k = noc.asm
    with k.scope():
      source, destination = k.reg(2); coord = k.arg(coord_arg)
      cb.write_ptr(source); k.mv(destination, source)
      noc.multicast_write(source, destination, coord, size)

  @staticmethod
  def _send_signal(noc, address, coord_arg):
    with noc.asm.scope():
      coord = noc.asm.arg(coord_arg)
      noc.multicast_write(address, address, coord, 4)

  def read_a(self):
    """Emit the double-buffered BRISC A reader."""
    plan, k = self.plan, self.p.brisc
    noc = k.noc(0).initialize_from_firmware()
    for block in k.range(plan.num_blocks):
      self.a_reader.reserve_back(plan.a_block_pages)
      with k.scope():
        base_page, destination = k.arg(self.A_PAGE), k.reg()
        self.a_reader.write_ptr(destination)
        for index in k.range(plan.a_tiles):
          with k.scope():
            row, inner, page, dst, offset = k.reg(5, exclude=(block, index))
            k.li(offset, plan.block_w)
            k.divu(row, index, offset); k.remu(inner, index, offset)
            k.li(offset, self.a.padded_shape[1] // TILE); k.mul(page, row, offset)
            k.li(offset, plan.block_w); k.mul(offset, block, offset)
            k.add(page, page, offset); k.add(page, page, inner); k.add(page, page, base_page)
            src, coord = noc.dram_page(self.a, page)
            k.slli(offset, index, 11); k.add(dst, destination, offset)
            noc.read(src, coord, dst, TILE_BYTES)
      self.a_reader.push_back(plan.a_block_pages)
    return self

  def _read_a_distributed(self, noc):
    plan, k = self.plan, self.p.brisc
    k.write32(self.a_ready, 0); k.write32(self.a_signal, 0); k.fence()
    receiver, done = k._new_label("a_receiver"), k._new_label("a_done")
    with k.scope():
      sender = k.arg(self.A_SENDER); k.beq(sender, R.ZERO, receiver)

    for block in k.range(plan.num_blocks):
      self.a_reader.reserve_back(plan.a_block_pages)
      with k.scope():
        base_page, destination = k.arg(self.A_PAGE), k.reg()
        self.a_reader.write_ptr(destination)
        for index in k.range(plan.a_tiles):
          with k.scope():
            row, inner, page, dst, offset = k.reg(5, exclude=(block, index))
            k.li(offset, plan.block_w)
            k.divu(row, index, offset); k.remu(inner, index, offset)
            k.li(offset, self.a.padded_shape[1] // TILE); k.mul(page, row, offset)
            k.li(offset, plan.block_w); k.mul(offset, block, offset)
            k.add(page, page, offset); k.add(page, page, inner); k.add(page, page, base_page)
            src, coord = noc.dram_page(self.a, page)
            k.slli(offset, index, 11); k.add(dst, destination, offset)
            noc.read(src, coord, dst, TILE_BYTES)
      with k.scope():
        actual, expected, scale = k.reg(3, exclude=block)
        k.addi(expected, block, 1); k.li(scale, len(plan.cols) - 1)
        k.mul(expected, expected, scale); k.andi(expected, expected, 31)
        ready = k._new_label("a_wait_ready")
        k.label(ready); k.read32(actual, self.a_ready); k.bne(actual, expected, ready); k.fence()
      self._send_payload(noc, self.a_reader, self.a_coord_base, plan.a_tiles * TILE_BYTES)
      with k.scope():
        signal = k.reg(exclude=block); k.addi(signal, block, 1)
        k.write32(self.a_signal, signal); k.fence()
      self._send_signal(noc, self.a_signal, self.a_coord_base)
      self.a_reader.push_back(plan.a_block_pages)
    k.j(done)

    k.label(receiver)
    for block in k.range(plan.num_blocks):
      self.a_reader.reserve_back(plan.a_block_pages)
      noc.atomic_increment(self.a_ready, k.arg(self.A_SENDER_COORD))
      with k.scope():
        actual, expected = k.reg(2, exclude=block); k.addi(expected, block, 1)
        wait = k._new_label("a_wait_signal")
        k.label(wait); k.read32(actual, self.a_signal); k.bne(actual, expected, wait); k.fence()
      k.delay_cycles(1000)
      self.a_reader.push_back(plan.a_block_pages)
    k.label(done)
    return self

  def read_b_and_write_output(self):
    """Emit the double-buffered NCRISC B reader and final output writes."""
    plan, k = self.plan, self.p.ncrisc
    noc = k.noc(1).initialize_from_firmware()
    k.write32(self.output_ready, 0)
    for block in k.range(plan.num_blocks):
      self.b_reader.reserve_back(plan.b_block_pages)
      with k.scope():
        base_page, destination = k.arg(self.B_PAGE), k.reg()
        self.b_reader.write_ptr(destination)
        for index in k.range(plan.b_tiles):
          with k.scope():
            row, col, page, dst, offset = k.reg(5, exclude=(block, index))
            k.li(offset, plan.per_core_n)
            k.divu(row, index, offset); k.remu(col, index, offset)
            k.li(offset, plan.block_w); k.mul(offset, block, offset); k.add(row, row, offset)
            k.li(offset, self.b.padded_shape[1] // TILE); k.mul(page, row, offset)
            k.add(page, page, col); k.add(page, page, base_page)
            src, coord = noc.dram_page(self.b, page)
            k.slli(offset, index, 11); k.add(dst, destination, offset)
            noc.read(src, coord, dst, TILE_BYTES)
      self.b_reader.push_back(plan.b_block_pages)

    return self._write_output(noc)

  def _read_b_distributed(self, noc):
    plan, k = self.plan, self.p.ncrisc
    k.write32(self.b_ready, 0); k.write32(self.b_signal, 0); k.fence()
    receiver, done = k._new_label("b_receiver"), k._new_label("b_done")
    with k.scope():
      sender = k.arg(self.b_sender); k.beq(sender, R.ZERO, receiver)

    for block in k.range(plan.num_blocks):
      self.b_reader.reserve_back(plan.b_block_pages)
      with k.scope():
        base_page, destination = k.arg(self.B_PAGE), k.reg()
        self.b_reader.write_ptr(destination)
        for index in k.range(plan.b_tiles):
          with k.scope():
            row, col, page, dst, offset = k.reg(5, exclude=(block, index))
            k.li(offset, plan.per_core_n)
            k.divu(row, index, offset); k.remu(col, index, offset)
            k.li(offset, plan.block_w); k.mul(offset, block, offset); k.add(row, row, offset)
            k.li(offset, self.b.padded_shape[1] // TILE); k.mul(page, row, offset)
            k.add(page, page, col); k.add(page, page, base_page)
            src, coord = noc.dram_page(self.b, page)
            k.slli(offset, index, 11); k.add(dst, destination, offset)
            noc.read(src, coord, dst, TILE_BYTES)
      with k.scope():
        actual, expected, scale = k.reg(3, exclude=block)
        k.addi(expected, block, 1); k.li(scale, len(plan.rows) - 1)
        k.mul(expected, expected, scale); k.andi(expected, expected, 31)
        ready = k._new_label("b_wait_ready")
        k.label(ready); k.read32(actual, self.b_ready); k.bne(actual, expected, ready); k.fence()
      self._send_payload(noc, self.b_reader, self.b_coord_base, plan.b_tiles * TILE_BYTES)
      with k.scope():
        signal = k.reg(exclude=block); k.addi(signal, block, 1)
        k.write32(self.b_signal, signal); k.fence()
      self._send_signal(noc, self.b_signal, self.b_coord_base)
      self.b_reader.push_back(plan.b_block_pages)
    k.j(done)

    k.label(receiver)
    for block in k.range(plan.num_blocks):
      self.b_reader.reserve_back(plan.b_block_pages)
      noc.atomic_increment(self.b_ready, k.arg(self.b_sender_coord))
      with k.scope():
        actual, expected = k.reg(2, exclude=block); k.addi(expected, block, 1)
        wait = k._new_label("b_wait_signal")
        k.label(wait); k.read32(actual, self.b_signal); k.bne(actual, expected, wait); k.fence()
      k.delay_cycles(1000)
      self.b_reader.push_back(plan.b_block_pages)
    k.label(done)
    return self

  def _write_output(self, noc):
    plan, k = self.plan, self.p.ncrisc
    k.wait32(self.output_ready, 1)
    self.output_writer.wait_front(plan.output_tiles)
    with k.scope():
      output_base = k.arg(self.C_PAGE); source_base, sequential = k.reg(2)
      self.output_writer.read_ptr(source_base); k.li(sequential, 0)
      for block_m in k.range(plan.m_subblocks):
        for block_n in k.range(plan.n_subblocks):
          for tile_m in range(plan.subblock_h):
            for tile_n in range(plan.subblock_w):
              with k.scope():
                page, source, delta, logical = k.reg(4, exclude=(block_m, block_n, sequential))
                k.li(delta, plan.subblock_h); k.mul(logical, block_m, delta)
                _add_constant(k, logical, tile_m); k.li(delta, plan.nt); k.mul(page, logical, delta)
                k.li(delta, plan.subblock_w); k.mul(logical, block_n, delta)
                k.add(page, page, logical); _add_constant(k, page, tile_n); k.add(page, page, output_base)
                dst, coord = noc.dram_page(self.output, page)
                k.slli(delta, sequential, 11); k.add(source, source_base, delta)
                noc.write(source, dst, coord, TILE_BYTES)
              k.addi(sequential, sequential, 1)
    self.output_writer.pop_front(plan.output_tiles)
    k.delay_cycles(10000)
    return self

  @staticmethod
  def _add_tile_offset(k, address, tile):
    if isinstance(tile, R):
      with k.scope():
        offset = k.reg(exclude=(address, tile)); k.slli(offset, tile, 11); k.add(address, address, offset)
    else:
      _add_constant(k, address, tile * TILE_BYTES)

  def _unpack_tile_row(self, a_tile: int | R, b_tile: int | R):
    k, t = self.p.trisc0, self.p.unpack.tensix
    t.wait_unpack_config_idle()
    with k.scope():
      context, a_addr, b_addr, target = k.reg(4)
      k.read32(context, self.unpack_context)
      self.a_unpack.read_ptr(a_addr); self.b_unpack.read_ptr(b_addr)
      self._add_tile_offset(k, a_addr, a_tile)
      self._add_tile_offset(k, b_addr, b_tile)
      k.srli(a_addr, a_addr, 4); k.addi(a_addr, a_addr, -1)
      k.srli(b_addr, b_addr, 4); k.addi(b_addr, b_addr, -1)

      k.li(target, int(Cfg.THCON_SEC0_REG3_Base_address))
      sec0 = k._new_label("unpack_sec0"); k.beq(context, R.ZERO, sec0)
      k.addi(target, target, 4); k.label(sec0); k.sw(b_addr, target)
      k.li(target, int(Cfg.THCON_SEC1_REG3_Base_address))
      sec1 = k._new_label("unpack_sec1"); k.beq(context, R.ZERO, sec1)
      k.addi(target, target, 4); k.label(sec1); k.sw(a_addr, target)
      k.write32(TensixRegs.PC_UNPACK_SYNC, 0)

      t.stall(TensixStall.UNPACK, TensixWait.TRISC_CFG)
      t.issue(tt_word("TTUNPACR", 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1))
      context1, mop_done = k._new_label("unpack_context1"), k._new_label("unpack_mop_done")
      k.bne(context, R.ZERO, context1)
      t.run_mop(loop_count=self.plan.subblock_w - 1, zmask=0, mop_type=0); k.j(mop_done)
      k.label(context1)
      t.run_mop(loop_count=self.plan.subblock_w - 1, zmask=0xFF, mop_type=0)
      k.label(mop_done)
      t.semaphore_get(TensixSem.UNPACK_SYNC)
      k.xori(context, context, 1); k.write32(self.unpack_context, context)
      cfg1, cfg_done = k._new_label("unpack_cfg1"), k._new_label("unpack_cfg_done")
      k.bne(context, R.ZERO, cfg1)
      t.issue(tt_word("TTSETC16", ThreadCfg.UNPACK_MISC_CFG, 0)); k.j(cfg_done)
      k.label(cfg1); t.issue(tt_word("TTSETC16", ThreadCfg.UNPACK_MISC_CFG, 257))
      k.label(cfg_done)

  def _reload_subblock(self):
    """Unpack one BF16 partial subblock into SrcA for the math thread."""
    k, t, plan = self.p.trisc0, self.p.unpack.tensix, self.plan
    t.issue(tt_word("TTRMWCIB1", 1, 0, Cfg.THCON_SEC0_REG2.addr32))
    t.issue(tt_word("TTSETADCXX", 1, 255, 0)); t.configure_mop(RELOAD_UNPACK_MOP)
    self.partial_unpack.wait_front(plan.subblock_tiles)
    for tile in range(plan.subblock_tiles):
      t.issue(tt_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))
      t.wait_unpack_config_idle()
      with k.scope():
        context, address, target = k.reg(3)
        k.read32(context, self.unpack_context); self.partial_unpack.read_ptr(address)
        _add_constant(k, address, tile * TILE_BYTES)
        k.srli(address, address, 4); k.addi(address, address, -1)
        k.li(target, int(Cfg.THCON_SEC0_REG3_Base_address))
        context1 = k._new_label("reload_context1"); k.beq(context, R.ZERO, context1)
        k.addi(target, target, 4); k.label(context1); k.sw(address, target)
        k.write32(TensixRegs.PC_UNPACK_SYNC, 0)
        t.stall(TensixStall.UNPACK, TensixWait.TRISC_CFG); t.run_mop(mop_type=1)
        t.semaphore_get(TensixSem.UNPACK_SYNC)
        k.xori(context, context, 1); k.write32(self.unpack_context, context)
        cfg1, cfg_done = k._new_label("reload_cfg1"), k._new_label("reload_cfg_done")
        k.bne(context, R.ZERO, cfg1)
        t.issue(tt_word("TTSETC16", ThreadCfg.UNPACK_MISC_CFG, 0)); k.j(cfg_done)
        k.label(cfg1); t.issue(tt_word("TTSETC16", ThreadCfg.UNPACK_MISC_CFG, 257)); k.label(cfg_done)
    t.stall(TensixStall.UNPACK, TensixWait.UNPACK0); t.sync()
    self.partial_unpack.pop_front(plan.subblock_tiles)
    t.issue(tt_word("TTRMWCIB1", 1, 0, Cfg.THCON_SEC0_REG2.addr32))
    t.issue(tt_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))
    t.issue(tt_word("TTSETADCXX", 1, 1023, 0)); t.issue(tt_word("TTSETADCXX", 2, 1023, 0))
    t.configure_mop(UNPACK_AB_MOP)

  def unpack(self):
    """Emit TRISC0's runtime K-block loop and BF16 partial reload."""
    plan, t = self.plan, self.p.unpack.tensix
    self.p.unpack.init(self.a_unpack, mop_cfg=UNPACK_AB_MOP)
    t.issue(tt_word("TTSETADCXX", 1, 1023, 0))
    t.issue(tt_word("TTSETADCXX", 2, 1023, 0))
    t.issue(tt_word("TTSEMINIT", 2, 0, TensixSem.mask(TensixSem.UNPACK_SYNC)))
    self.p.trisc0.write32(self.unpack_context, 0)
    for block in self.p.trisc0.range(plan.num_blocks):
      self.a_unpack.wait_front(plan.a_block_pages); self.b_unpack.wait_front(plan.b_block_pages)
      for block_m in self.p.trisc0.range(plan.m_subblocks):
        for block_n in self.p.trisc0.range(plan.n_subblocks):
          with self.p.trisc0.scope():
            skip_reload = self.p.trisc0._new_label("skip_partial_reload")
            reload = self.p.trisc0._new_label("reload_final_partial")
            last = self.p.trisc0.reg(exclude=block); self.p.trisc0.li(last, plan.num_blocks - 1)
            self.p.trisc0.beq(block, R.ZERO, skip_reload); self.p.trisc0.beq(block, last, reload)
            self.partial_unpack.wait_front(plan.subblock_tiles); self.partial_unpack.pop_front(plan.subblock_tiles)
            self.p.trisc0.j(skip_reload); self.p.trisc0.label(reload); self._reload_subblock()
            self.p.trisc0.label(skip_reload)
          for inner in self.p.trisc0.range(plan.block_w):
            with self.p.trisc0.scope():
              a_base, b_tile, scale = self.p.trisc0.reg(3, exclude=(block_m, block_n, inner))
              self.p.trisc0.li(scale, plan.subblock_h * plan.block_w)
              self.p.trisc0.mul(a_base, block_m, scale); self.p.trisc0.add(a_base, a_base, inner)
              self.p.trisc0.li(scale, plan.subblock_w); self.p.trisc0.mul(b_tile, block_n, scale)
              self.p.trisc0.li(scale, plan.per_core_n); self.p.trisc0.mul(scale, inner, scale)
              self.p.trisc0.add(b_tile, b_tile, scale)
              for row in range(plan.subblock_h):
                with self.p.trisc0.scope():
                  a_tile = self.p.trisc0.reg(exclude=(a_base, b_tile)); self.p.trisc0.mv(a_tile, a_base)
                  _add_constant(self.p.trisc0, a_tile, row * plan.block_w)
                  self._unpack_tile_row(a_tile, b_tile)
      t.stall(TensixStall.UNPACK, TensixWait.UNPACK0 | TensixWait.UNPACK1); t.sync()
      self.a_unpack.pop_front(plan.a_block_pages); self.b_unpack.pop_front(plan.b_block_pages)
    return self

  def multiply(self):
    """Emit TRISC1's replay-driven K-block loop with BF16 partial reload."""
    plan, math = self.plan, self.p.math
    t = math.tensix
    t.set_thread_cfg(ThreadCfg.CFG_STATE_ID, 0)
    math._set_dst_mode(fp32=False)
    t.set_thread_cfg(ThreadCfg.DEST_TARGET_REG_CFG_MATH, 0)
    t.issue(tt_word("TTZEROACC", 3, 0, 0, 1, 0))
    self.p.trisc1.write32(self.math_dest_offset, 0)
    self._configure_matmul_math()
    t.load_replay(MATH_REPLAY, start=16); t.sync()
    t.issue(tt_word("TTSEMINIT", 2, 0, TensixSem.mask(TensixSem.MATH_PACK)))

    for block in self.p.trisc1.range(plan.num_blocks):
      for _block_m in self.p.trisc1.range(plan.m_subblocks):
        for _block_n in self.p.trisc1.range(plan.n_subblocks):
          math.acquire_dst()
          skip_reload = self.p.trisc1._new_label("skip_math_reload")
          with self.p.trisc1.scope():
            last = self.p.trisc1.reg(exclude=block); self.p.trisc1.li(last, plan.num_blocks - 1)
            self.p.trisc1.beq(block, R.ZERO, skip_reload)
            self.p.trisc1.bne(block, last, skip_reload)
          self._reload_math_subblock(); self.p.trisc1.label(skip_reload)
          for _inner in self.p.trisc1.range(plan.block_w):
            for tile in range(plan.subblock_tiles):
              self._set_math_destination(tile)
              t.replay(16, len(MATH_REPLAY))
              if self.hifi: t.replay(16, len(MATH_REPLAY))
              t.issue(tt_word("TTSETRWC", 1, 0, 0, 0, 0, 15))
              if tile % plan.subblock_w == plan.subblock_w - 1:
                t.issue(tt_word("TTSETRWC", 2, 0, 0, 0, 0, 15))
          t.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU)
          math.publish_dst(); t.sync(); self._toggle_dest_offset(self.p.trisc1, self.math_dest_offset)
    return self

  def _configure_matmul_math(self):
    t = self.p.math.tensix
    for reg, value in (
      (ThreadCfg.ADDR_MOD_AB_SEC0, 2048), (ThreadCfg.ADDR_MOD_DST_SEC0, 8),
      (ThreadCfg.ADDR_MOD_BIAS_SEC0, 0), (ThreadCfg.ADDR_MOD_AB_SEC1, 16400),
      (ThreadCfg.ADDR_MOD_DST_SEC1, 8), (ThreadCfg.ADDR_MOD_BIAS_SEC1, 0),
      (ThreadCfg.ADDR_MOD_AB_SEC2, 24640), (ThreadCfg.ADDR_MOD_DST_SEC2, 8),
      (ThreadCfg.ADDR_MOD_BIAS_SEC2, 0), (ThreadCfg.ADDR_MOD_AB_SEC4, 28768),
      (ThreadCfg.ADDR_MOD_DST_SEC4, 1024), (ThreadCfg.ADDR_MOD_BIAS_SEC4, 0),
      (ThreadCfg.ADDR_MOD_AB_SEC5, 49344), (ThreadCfg.ADDR_MOD_DST_SEC5, 11264),
      (ThreadCfg.ADDR_MOD_BIAS_SEC5, 0), (ThreadCfg.ADDR_MOD_AB_SEC6, 49344),
      (ThreadCfg.ADDR_MOD_DST_SEC6, 35840), (ThreadCfg.ADDR_MOD_BIAS_SEC6, 0),
    ): t.set_thread_cfg(reg, value)
    t.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 15))
    return self

  def _reload_math_subblock(self):
    math, t, plan = self.p.math, self.p.math.tensix, self.plan
    math._configure_copy_addressing(); t.configure_mop(RELOAD_MATH_MOP)
    for tile in range(plan.subblock_tiles):
      self._set_math_destination(tile)
      t.run_mop(mop_type=1); t.issue(tt_word("TTSETRWC", 0, 0, 0, 0, 0, 4))
    t.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU); t.sync()
    self._configure_matmul_math()

  def _set_math_destination(self, tile: int):
    k, t = self.p.trisc1, self.p.math.tensix
    with k.scope():
      offset = k.reg(); k.read32(offset, self.math_dest_offset)
      second, done = k._new_label("math_dest_second"), k._new_label("math_dest_done")
      k.bne(offset, R.ZERO, second)
      t.issue(tt_word("TTSETC16", ThreadCfg.DEST_TARGET_REG_CFG_MATH, tile * 64)); k.j(done)
      k.label(second); t.issue(tt_word("TTSETC16", ThreadCfg.DEST_TARGET_REG_CFG_MATH, 512 + tile * 64))
      k.label(done)

  @staticmethod
  def _toggle_dest_offset(k, address):
    with k.scope():
      offset = k.reg(); k.read32(offset, address); k.xori(offset, offset, 1); k.write32(address, offset)

  def _pack_subblock(self):
    k, pack, plan = self.p.trisc2, self.p.pack, self.plan
    t = pack.tensix
    pack.acquire_dst(); self.output_pack.reserve_back(plan.subblock_tiles)
    with k.scope():
      offset = k.reg(); k.read32(offset, self.pack_dest_offset); k.slli(offset, offset, 9)
      for reg in (Cfg.DEST_TARGET_REG_CFG_PACK_SEC0, Cfg.DEST_TARGET_REG_CFG_PACK_SEC1,
                  Cfg.DEST_TARGET_REG_CFG_PACK_SEC2, Cfg.DEST_TARGET_REG_CFG_PACK_SEC3):
        k.write32(int(reg), offset)
    with k.scope():
      base = k.reg(); self.output_pack.write_ptr(base)
      for tile in range(plan.subblock_tiles):
        with k.scope():
          address = k.reg(); k.mv(address, base)
          _add_constant(k, address, tile * TILE_BYTES)
          t.issue(tt_word("TTSETADC", 4, 0, 3, tile))
          transformed, high, high_valid = k.reg(3)
          k.srli(transformed, address, 4); k.addi(transformed, transformed, -1)
          t.set_dma_reg16_from_reg(24, transformed)
          k.srli(high, transformed, 16); k.li(high_valid, 0x8000); k.or_(high_valid, high_valid, high)
          t.set_dma_reg16_from_reg(25, high_valid)
          t.stall(TensixStall.CFG, TensixWait.THCON | TensixWait.PACK0)
          t.write_cfg_from_gpr(12, Cfg.THCON_SEC0_REG1_L1_Dest_addr)
          t.set_dma_reg16_from_reg(25, high); t.dma_nop()
          t.stall(TensixStall.CFG, TensixWait.PACK0); t.run_mop(mop_type=1)
          t.stall(TensixStall.SYNC, TensixWait.PACK0); t.sync()
          t.issue(tt_word("TTSETADCZW", 4, 0, 0, 0, 0, 5))
    self.output_pack.push_back(plan.subblock_tiles)
    t.stall(TensixStall.THCON, TensixWait.PACK0)
    with k.scope():
      offset = k.reg(); k.read32(offset, self.pack_dest_offset)
      second, done = k._new_label("zero_second_dest"), k._new_label("zero_dest_done")
      k.bne(offset, R.ZERO, second); t.issue(tt_word("TTZEROACC", 2, 0, 0, 1, 0)); k.j(done)
      k.label(second); t.issue(tt_word("TTZEROACC", 2, 0, 0, 1, 1)); k.label(done)
    pack.release_dst(); self._toggle_dest_offset(k, self.pack_dest_offset); t.dma_nop(); t.dma_nop()

  def pack(self):
    """Emit TRISC2's partial/final BF16 pack loop."""
    self.p.pack.init(self.output_pack)
    self.p.trisc2.write32(self.pack_dest_offset, 0)
    for block in self.p.trisc2.range(self.plan.num_blocks):
      self._configure_l1_acc(block)
      for _block_m in self.p.trisc2.range(self.plan.m_subblocks):
        for _block_n in self.p.trisc2.range(self.plan.n_subblocks):
          self._pack_subblock()
    self.p.trisc2.write32(self.output_ready, 1)
    return self

  def _configure_l1_acc(self, block):
    k, t = self.p.trisc2, self.p.pack.tensix
    t.stall(TensixStall.CFG, TensixWait.PACK0)
    disable, enabled, done = (
      k._new_label("pack_l1_acc_disable"), k._new_label("pack_l1_acc_enable"),
      k._new_label("pack_l1_acc_done"),
    )
    with k.scope():
      last = k.reg(exclude=block); k.li(last, self.plan.num_blocks - 1)
      k.beq(block, R.ZERO, disable); k.beq(block, last, disable); k.j(enabled)
    k.label(disable)
    t.issue(tt_word("TTRMWCIB0", 0x04, 0x00, Cfg.THCON_SEC0_REG1_1.addr32))
    t.issue(tt_word("TTRMWCIB2", 0x08, 0x00, Cfg.THCON_SEC0_REG1_2.addr32)); k.j(done)
    k.label(enabled)
    t.issue(tt_word("TTRMWCIB0", 0x04, 0x04, Cfg.THCON_SEC0_REG1_1.addr32))
    t.issue(tt_word("TTRMWCIB2", 0x08, 0x08, Cfg.THCON_SEC0_REG1_2.addr32))
    k.label(done)
