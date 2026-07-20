from fw.consts import TensixMMIO
from isa import Tensix as TT
from ttk.dst import Dst
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

  def _issue(self, word):
    self.k.emit(word)
    return self

  def _set_thread_cfg(self, register, value):
    return self._issue(TT.TTSETC16(int(register), int(value)))

  def _rmw_cfg_byte(self, register, byte, mask, data):
    opcode = (TT.TTRMWCIB0, TT.TTRMWCIB1, TT.TTRMWCIB2, TT.TTRMWCIB3)[byte]
    address = (int(register) - TensixMMIO.CFG_BASE) >> 2
    return self._issue(opcode(mask, data & mask, address))

  def _configure_dst(self, dst_tile):
    self._set_thread_cfg(_CFG_STATE_ID, 0)
    self._set_thread_cfg(_DST_ROW_BASE, self.dst.row_base(dst_tile))
    stall(self.k, Stall.CFG, Wait.MATH | Wait.SFPU)
    self._rmw_cfg_byte(_ALU_CONFIG, 3, 0x20, 0x20 if self.dst.fp32 else 0)
    return self

  def _wait_for_dst(self):
    sem_wait(
      self.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
      Stall.SYNC | Stall.MATH | Stall.SFPU,
    )
    return self

  def publish(self):
    stall(self.k, Stall.SYNC, Wait.MATH | Wait.SFPU)
    sem_post(self.k, Sem.MATH_PACK)
    return self

  def _run(self, dst_tile, instruction, *, source_a, source_b, release,
           step=8, mop=_tile_mop):
    self._wait_for_dst()
    self._configure_dst(dst_tile)
    source = (step if source_a else 0) | ((step if source_b else 0) << 8)
    for register, value in (
      (_ADDR_MOD_AB + 2, source),
      (_ADDR_MOD_DST + 2, step),
      (_ADDR_MOD_BIAS + 2, 0),
    ): self._set_thread_cfg(register, value)
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    waits = (Wait.SRCA_VLD if source_a else 0) | (Wait.SRCB_VLD if source_b else 0)
    if waits: stall(self.k, Stall.MATH, waits)
    self._mop.configure(mop(instruction, release)).run()
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self

  def copy_a(self, *, dst_tile):
    # The unary SrcA unpack path also advances an empty SrcB bank, so release both.
    return self._run(dst_tile, TT.TTMOVA2D(0, 0, 2, 2, 0),
                     source_a=True, source_b=False, release=3)

  def copy_b(self, *, dst_tile):
    return self._run(dst_tile, TT.TTMOVB2D(0, 0, 2, 2, 0),
                     source_a=False, source_b=True, release=2)

  def add(self, *, dst_tile, accumulate=False):
    return self._run(dst_tile, TT.TTELWADD(0, int(accumulate), 0, 2, 0),
                     source_a=True, source_b=True, release=3)

  def sub(self, *, dst_tile, accumulate=False):
    return self._run(dst_tile, TT.TTELWSUB(0, int(accumulate), 0, 2, 0),
                     source_a=True, source_b=True, release=3)

  def mul(self, *, dst_tile, accumulate=False):
    return self._run(dst_tile, TT.TTELWMUL(0, int(accumulate), 0, 2, 0),
                     source_a=True, source_b=True, release=3)

  def pool_scalar(self, *, dst_tile, maximum, negate=False):
    """Pool four faces and their columns into Dst[0, 0]."""
    if negate and not maximum:
      raise ValueError("in-place scalar negation requires max pooling")
    self._wait_for_dst()
    self._configure_dst(dst_tile)
    for register in (_ADDR_MOD_AB, _ADDR_MOD_DST, _ADDR_MOD_BIAS):
      self._set_thread_cfg(register, 0)
    # Scalar packing reads the first row of each physical face. Pooling writes
    # only face 0, so clear all four source rows before reusing Dst.
    for row in (0, 16, 32, 48):
      self._issue(TT.TTZEROACC(0, int(self.dst.fp32), 0, 0, row))
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
    pool = TT.TTGMPOOL if maximum else TT.TTGAPOOL
    for _ in range(3): self._issue(pool(3, 1, 0, 0, 4))
    self._issue(pool(0, 1, 0, 0, 4))

    self._issue(TT.TTSETRWC(0, 4, 0, 0, 0, 3))
    self._issue(TT.TTMOVD2B(0, 16, 0, 0, 4))
    self._issue(TT.TTGATESRCRST(1, 1))
    self._issue(TT.TTTRNSPSRCB())
    self._issue(TT.TTGATESRCRST(1, 1))
    for row in range(0, 16, 4):
      self._issue(TT.TTMOVB2A(row, 0, 2, 16 + row))
    self._issue(TT.TTGATESRCRST(1, 1))
    self._issue(TT.TTZEROACC(0, 0, 0, 0, 4))
    self._issue(pool(0 if negate else 3, 1, 0, 0, 0))
    if negate:
      # GMPOOL does not consume SrcB. The reduction unpacker can therefore
      # leave -1 in SrcB rows 8-15 while the scalar is copied back to SrcA.
      self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
      self._issue(TT.TTMOVD2A(0, 0, 0, 0, 0))
      self._issue(TT.TTGATESRCRST(1, 1))
      self._issue(TT.TTZEROACC(0, int(self.dst.fp32), 0, 0, 0))
      self._issue(TT.TTSETRWC(0, 0, 0, 8, 0, 0xF))
      self._issue(TT.TTELWMUL(3, 0, 0, 0, 0))
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self
