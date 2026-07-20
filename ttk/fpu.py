from enum import IntEnum

from fw.consts import TensixMMIO
from isa import Tensix as TT
from ttk.dst import Dst
from ttk.mop import LoopTemplate, Mop
from ttk.sync import Sem, SemWait, Stall, Wait, sem_post, sem_wait, stall


_CFG_STATE_ID = 0
_DST_ROW_BASE = 1
_ALU_CONFIG = TensixMMIO.CFG_BASE + 4
_ADDR_MOD_AB, _ADDR_MOD_DST, _ADDR_MOD_BIAS = 12, 28, 47


class Broadcast(IntEnum):
  NONE = 0
  COLUMN = 1
  ROW = 2
  SCALAR = 3


def _tile_mop(instruction, release):
  return LoopTemplate(
    outer=4, inner=2, loop=instruction,
    end0=TT.TTSETRWC(release, 0, 0, 0, 0, 3),
    last=instruction, outer_last=instruction,
  )


def _column_broadcast_mop(instruction, _release):
  return LoopTemplate(
    outer=2, inner=2, loop=instruction,
    end0=TT.TTSETRWC(1, 3, 0, 0, 0, 3),
    last=instruction, outer_last=instruction,
  )


def _scalar_broadcast_mop(instruction, _release):
  return LoopTemplate(
    outer=4, inner=2, loop=instruction,
    end0=TT.TTSETRWC(1, 3, 0, 0, 0, 3),
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

  def _set_addr_mod(self, slot, *, srca=0, srcb=0,
                    srca_clear=False, srca_carry=False,
                    srcb_clear=False, srcb_carry=False, dest=0,
                    dest_clear=False, dest_carry=False,
                    fidelity_increment=0, fidelity_clear=False):
    """Program one FPU address-modifier slot."""
    if type(slot) is not int or not 0 <= slot < 8:
      raise ValueError("FPU address-modifier slot must be in range 0..7")
    source = (
      (srca & 0x3f) |
      int(srca_carry) << 6 |
      int(srca_clear) << 7 |
      (
        (srcb & 0x3f) |
        int(srcb_carry) << 6 |
        int(srcb_clear) << 7
      ) << 8
    )
    destination = (
      (dest & 0x3ff) |
      int(dest_carry) << 10 |
      int(dest_clear) << 11 |
      (fidelity_increment & 0x3) << 13 |
      int(fidelity_clear) << 15
    )
    self._set_thread_cfg(_ADDR_MOD_AB + slot, source)
    self._set_thread_cfg(_ADDR_MOD_DST + slot, destination)
    self._set_thread_cfg(_ADDR_MOD_BIAS + slot, 0)
    return self

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
           step=8, mop=_tile_mop, broadcast=Broadcast.NONE):
    try:
      broadcast = Broadcast(broadcast)
    except ValueError:
      raise ValueError("invalid FPU broadcast mode") from None
    if broadcast is not Broadcast.NONE and not source_b:
      raise ValueError("FPU broadcast requires SrcB")
    if broadcast is Broadcast.COLUMN:
      mop = _column_broadcast_mop
    elif broadcast is Broadcast.SCALAR:
      mop = _scalar_broadcast_mop
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
    self._mop.configure(mop(instruction, release))
    if broadcast is Broadcast.COLUMN:
      self._mop.run()
      self._issue(TT.TTSETRWC(2, 0, 0, 0, 0, 0))
      self._mop.run()
      self._issue(TT.TTSETRWC(2, 0, 0, 0, 0, 0))
    else:
      self._mop.run()
      if broadcast is Broadcast.SCALAR:
        self._issue(TT.TTSETRWC(2, 0, 0, 0, 0, 0))
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self

  def copy_a(self, *, dst_tile):
    # The unary SrcA unpack path also advances an empty SrcB bank, so release both.
    return self._run(dst_tile, TT.TTMOVA2D(0, 0, 2, 2, 0),
                     source_a=True, source_b=False, release=3)

  def copy_b(self, *, dst_tile):
    return self._run(dst_tile, TT.TTMOVB2D(0, 0, 2, 2, 0),
                     source_a=False, source_b=True, release=2)

  def add(self, *, dst_tile, accumulate=False, broadcast=Broadcast.NONE):
    broadcast = Broadcast(broadcast)
    return self._run(
      dst_tile, TT.TTELWADD(0, int(accumulate), broadcast, 2, 0),
      source_a=True, source_b=True, release=3, broadcast=broadcast,
    )

  def sub(self, *, dst_tile, accumulate=False, broadcast=Broadcast.NONE):
    broadcast = Broadcast(broadcast)
    return self._run(
      dst_tile, TT.TTELWSUB(0, int(accumulate), broadcast, 2, 0),
      source_a=True, source_b=True, release=3, broadcast=broadcast,
    )

  def mul(self, *, dst_tile, accumulate=False, broadcast=Broadcast.NONE):
    broadcast = Broadcast(broadcast)
    return self._run(
      dst_tile, TT.TTELWMUL(0, int(accumulate), broadcast, 2, 0),
      source_a=True, source_b=True, release=3, broadcast=broadcast,
    )

  def _transpose_row_result(self):
    self._issue(TT.TTSETRWC(0, 4, 0, 0, 0, 3))
    self._issue(TT.TTMOVD2B(0, 16, 0, 0, 0))
    self._issue(TT.TTTRNSPSRCB())
    self._issue(TT.TTMOVD2B(0, 16, 0, 0, 0))
    self._issue(TT.TTSETRWC(0, 2, 0, 8, 0, 2))
    self._issue(TT.TTSETRWC(0, 2, 0, 8, 0, 2))
    self._issue(TT.TTZEROSRC(0, 1, 0, 1))
    self._issue(TT.TTELWADD(0, 0, 0, 1, 0))
    self._issue(TT.TTELWADD(0, 0, 0, 1, 0))
    return self

  def reduce_row_max(self, *, dst_tile):
    """Accumulate the maximum of every logical row into a Dst column."""
    self._wait_for_dst()
    self._configure_dst(dst_tile)
    # GMPOOL reduces SrcA columns. Row reduction halo-transposes the operand,
    # then this sequence transposes each pooled face row back into Dst column 0.
    self._set_addr_mod(0, fidelity_clear=True)
    self._set_addr_mod(1, srcb=8, dest=8)
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
    self._issue(TT.TTGMPOOL(3, 1, 0, 0, 0))
    self._issue(TT.TTGMPOOL(0, 1, 0, 0, 0))
    self._transpose_row_result()

    for _ in range(3):
      self._issue(TT.TTSETRWC(0, 4, 8, 0, 0, 4))
    self._issue(TT.TTSETRWC(3, 4, 8, 0, 0, 6))
    self._issue(TT.TTGMPOOL(3, 1, 0, 0, 0))
    self._issue(TT.TTGMPOOL(0, 1, 0, 0, 0))
    self._transpose_row_result()

    self._issue(TT.TTSETRWC(3, 0, 0, 0, 0, 6))
    return self

  def reduce_row_sum(self, *, dst_tile):
    """Accumulate the sum of every logical row into a Dst column."""
    self._wait_for_dst()
    self._configure_dst(dst_tile)
    # SrcA contains a halo-transposed scaler row and SrcB contains data.
    # MVMUL produces eight row sums at a time. The last modifier for each
    # physical face row advances Dst to its lower 16 logical rows.
    self._set_addr_mod(1, srcb=8, fidelity_clear=True)
    self._set_addr_mod(2, srcb_carry=True, fidelity_clear=True)
    self._set_addr_mod(
      3, srcb_carry=True, dest=32, fidelity_clear=True,
    )
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
    for _ in range(2):
      self._issue(TT.TTMVMUL(0, 0, 1, 0))
      self._issue(TT.TTMVMUL(3, 0, 2, 8))
      self._issue(TT.TTMVMUL(0, 0, 1, 0))
      self._issue(TT.TTMVMUL(0, 0, 3, 8))
      self._issue(TT.TTSETRWC(3, 0, 0, 0, 0, 2))
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 6))
    return self

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
      self._issue(TT.TTZEROACC(0, 0, 0, 0, row))
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
      self._issue(TT.TTZEROACC(0, 0, 0, 0, 0))
      self._issue(TT.TTSETRWC(0, 0, 0, 8, 0, 0xF))
      self._issue(TT.TTELWMUL(3, 0, 0, 0, 0))
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self
