from contextlib import contextmanager

from fw.consts import TensixMMIO
from isa import Tensix as TT
from ttk.dst import Dst, DstTile
from ttk.mop import LoopTemplate, Mop
from ttk.sync import Sem, SemWait, Stall, Wait, sem_post, sem_wait, stall


_CFG_STATE_ID = 0
_DST_ROW_BASE = 1
_ALU_CONFIG = TensixMMIO.CFG_BASE + 4
_ADDR_MOD_AB, _ADDR_MOD_DST, _ADDR_MOD_BIAS = 12, 28, 47


def _tile_mop(instruction, release):
  return LoopTemplate(
    outer=4, inner=2, loop=instruction,
    end0=TT.TTSETRWC(release, 0, 0, 0, 0, 3),
    last=instruction, outer_last=instruction,
  )


class Fpu:
  """Tile-level interface to the matrix unit on TRISC1."""

  def __init__(self, kernel, dst: Dst):
    if kernel.role != "trisc1": raise RuntimeError("FPU must run on trisc1")
    self.k, self.dst, self._mop = kernel, dst, Mop(kernel, 1)
    self._active: DstTile | None = None

  def _issue(self, word):
    self.k.emit(word)
    return self

  def _set_thread_cfg(self, register, value):
    return self._issue(TT.TTSETC16(int(register), int(value)))

  def _rmw_cfg_byte(self, register, byte, mask, data):
    if type(byte) is not int or not 0 <= byte < 4:
      raise ValueError("CFG byte index must be in range 0..3")
    if any(type(value) is not int or not 0 <= value < 256 for value in (mask, data)):
      raise ValueError("CFG RMW mask and data must fit in one byte")
    opcode = (TT.TTRMWCIB0, TT.TTRMWCIB1, TT.TTRMWCIB2, TT.TTRMWCIB3)[byte]
    address = (int(register) - TensixMMIO.CFG_BASE) >> 2
    return self._issue(opcode(mask, data & mask, address))

  def _select(self, tile):
    tile = self.dst.check(tile)
    self._set_thread_cfg(_CFG_STATE_ID, 0)
    self._set_thread_cfg(_DST_ROW_BASE, tile.row_base)
    stall(self.k, Stall.CFG, Wait.MATH | Wait.SFPU)
    self._rmw_cfg_byte(_ALU_CONFIG, 3, 0x20, 0x20 if tile.fp32 else 0)
    return tile

  def _destination(self, tile):
    tile = self.dst.check(tile)
    if self._active is not None and tile != self._active:
      raise ValueError("FPU operation must write the acquired Dst tile")
    return self._select(tile)

  def acquire(self, tile):
    tile = self.dst.check(tile)
    if self._active is not None: raise RuntimeError("a Dst tile is already acquired")
    sem_wait(
      self.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
      Stall.SYNC | Stall.MATH | Stall.SFPU,
    )
    self._active = self._select(tile)
    return tile

  def publish(self, tile=None):
    if self._active is None: raise RuntimeError("no Dst tile is acquired")
    if tile is not None and self.dst.check(tile) != self._active:
      raise ValueError("cannot publish a different Dst tile")
    stall(self.k, Stall.SYNC, Wait.MATH | Wait.SFPU)
    self._set_thread_cfg(_DST_ROW_BASE, 0)
    sem_post(self.k, Sem.MATH_PACK)
    self._active = None
    return self

  @contextmanager
  def tile(self, tile):
    self.acquire(tile)
    try: yield tile
    finally: self.publish(tile)

  def _run(self, tile, instruction, *, source_a, source_b, release):
    self._destination(tile)
    source = (8 if source_a else 0) | ((8 if source_b else 0) << 8)
    destination = 8
    for register, value in (
      (_ADDR_MOD_AB + 2, source),
      (_ADDR_MOD_DST + 2, destination),
      (_ADDR_MOD_BIAS + 2, 0),
    ): self._set_thread_cfg(register, value)
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    waits = (Wait.SRCA_VLD if source_a else 0) | (Wait.SRCB_VLD if source_b else 0)
    if waits: stall(self.k, Stall.MATH, waits)
    self._mop.configure(_tile_mop(instruction, release)).run()
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self

  def copy_a(self, tile):
    # The unary SrcA unpack path also advances an empty SrcB bank, so release both.
    return self._run(tile, TT.TTMOVA2D(0, 0, 2, 2, 0),
                     source_a=True, source_b=False, release=3)

  def copy_b(self, tile):
    return self._run(tile, TT.TTMOVB2D(0, 0, 2, 2, 0),
                     source_a=False, source_b=True, release=2)

  def add(self, tile, *, accumulate=False):
    return self._run(tile, TT.TTELWADD(0, int(accumulate), 0, 2, 0),
                     source_a=True, source_b=True, release=3)

  def sub(self, tile, *, accumulate=False):
    return self._run(tile, TT.TTELWSUB(0, int(accumulate), 0, 2, 0),
                     source_a=True, source_b=True, release=3)

  def mul(self, tile, *, accumulate=False):
    return self._run(tile, TT.TTELWMUL(0, int(accumulate), 0, 2, 0),
                     source_a=True, source_b=True, release=3)
