from enum import IntEnum

from fw.consts import TensixMMIO
from isa import Tensix as TT
from ttk import Dst
from ttk.mop import LoopTemplate, Mop, Replay
from ttk.sync import Sem, SemWait, Stall, Wait, sem_post, sem_wait, stall, sync


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

_ELWISE = {"add": TT.TTELWADD, "sub": TT.TTELWSUB, "mul": TT.TTELWMUL}

class Fpu:
  def __init__(self, kernel, dst: Dst):
    if kernel.role != "trisc1": raise RuntimeError("FPU must run on trisc1")
    self.k, self.dst, self._mop = kernel, dst, Mop(kernel, 1)
    self._matmul_replay = None

  def _issue(self, word):
    self.k.emit(word)
    return self

  def _set_thread_cfg(self, register, value):
    return self._issue(TT.TTSETC16(int(register), int(value)))

  def _set_addr_mod(self, slot, *, srca=0, srcb=0,
                    srca_clear=False, srca_carry=False,
                    srcb_clear=False, srcb_carry=False, dest=0,
                    dest_clear=False, dest_carry=False,
                    dest_carry_to_carry=False,
                    fidelity_increment=0, fidelity_clear=False):
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
      int(dest_carry_to_carry) << 12 |
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

  def copy_a_tiles(self, *, dst_tiles):
    """Copy a sequence of SrcA tiles while retaining common FPU setup."""
    dst_tiles = tuple(dst_tiles)
    if not dst_tiles: raise ValueError("copy_a_tiles requires at least one tile")
    for tile in dst_tiles: self.dst.check(tile)
    self._wait_for_dst()
    for register, value in (
      (_ADDR_MOD_AB + 2, 8),
      (_ADDR_MOD_DST + 2, 8),
      (_ADDR_MOD_BIAS + 2, 0),
    ): self._set_thread_cfg(register, value)
    instruction = TT.TTMOVA2D(0, 0, 2, 2, 0)
    self._mop.configure(_tile_mop(instruction, 3))
    for tile in dst_tiles:
      self._configure_dst(tile)
      self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
      stall(self.k, Stall.MATH, Wait.SRCA_VLD)
      self._mop.run()
      self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self

  def binary(self, operation, *, dst_tile, accumulate=False, broadcast=Broadcast.NONE):
    if operation not in _ELWISE: raise ValueError(f"unknown FPU operation {operation!r}")
    broadcast = Broadcast(broadcast)
    if operation == "mul":
      return self._mul_hifi2(
        dst_tile=dst_tile, accumulate=accumulate, broadcast=broadcast,
      )
    return self._run(
      dst_tile, _ELWISE[operation](0, int(accumulate), broadcast, 2, 0),
      source_a=True, source_b=True, release=3, broadcast=broadcast,
    )

  def _mul_hifi2(self, *, dst_tile, accumulate, broadcast):
    """Run both BF16 ELWMUL fidelity phases into FP32 Dst.

    ELWMUL always adds its partial product to Dst. HiFi2 therefore marks the
    target tile undefined first unless the caller explicitly requests
    accumulation, then executes fidelity phases 0 and 1 for each face.
    There is deliberately no LoFi ELWMUL path.
    """
    self.dst.require_fp32()
    self._wait_for_dst()
    self._configure_dst(dst_tile)

    srcb_step = 8 if broadcast in (Broadcast.NONE, Broadcast.COLUMN) else 0
    self._set_addr_mod(0, srca=8, srcb=srcb_step, dest=8)
    self._set_addr_mod(1)
    self._set_addr_mod(
      2, srca_clear=True, srcb_clear=True, dest_carry=True,
      fidelity_increment=1,
    )
    self._set_addr_mod(
      3, srca_clear=True, srcb_clear=True, dest=8,
      dest_carry_to_carry=True, fidelity_clear=True,
    )

    if not accumulate:
      # In FP32 mode a tile has four independently valid 16-row faces.
      for face in range(4):
        self._issue(TT.TTZEROACC(1, 1, 0, 1, dst_tile * 4 + face))

    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
    clear_sources = (
      1 if broadcast in (Broadcast.COLUMN, Broadcast.SCALAR) else 3
    )
    multiply = TT.TTELWMUL(0, 0, int(broadcast), 0, 0)
    last_phase = TT.TTELWMUL(0, 0, int(broadcast), 2, 0)
    last_face = TT.TTELWMUL(clear_sources, 0, int(broadcast), 3, 0)
    self._mop.configure(LoopTemplate(
      outer=2, inner=2, loop=multiply,
      # LoopTemplate.last maps to MOP's last-outer register, while
      # outer_last maps to its last-inner register.
      last=last_face, outer_last=last_phase,
    ))

    if broadcast is Broadcast.COLUMN:
      for _ in range(2):
        self._mop.run(); self._mop.run()
        self._issue(TT.TTSETRWC(2, 0, 0, 0, 0, 0))
    else:
      for _ in range(4): self._mop.run()
      if broadcast is Broadcast.SCALAR:
        self._issue(TT.TTSETRWC(2, 0, 0, 0, 0, 4))

    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self

  def matmul(self, *, dst_tile, accumulate=False, right_transpose=False):
    self.dst.require_fp32()
    self._wait_for_dst()
    self._configure_dst(dst_tile)

    # MVMUL computes D = SrcB @ SrcA in four 16x16 face products. Each
    # instruction produces eight destination rows; these modifiers traverse
    # both K faces and all four output faces before resetting for the next
    # fidelity phase.
    self._set_addr_mod(0, srcb=8, dest=8)
    self._set_addr_mod(
      1, srca=32 if right_transpose else 16,
      srcb_carry=True, dest=8,
    )
    self._set_addr_mod(
      2, srca_carry=True, srcb=32, srcb_carry=True, dest=8,
    )
    self._set_addr_mod(
      4, srca=16 if right_transpose else 32, srca_carry=True,
      srcb=48, srcb_carry=True, dest_carry=True,
    )
    self._set_addr_mod(
      5, srca_clear=True, srca_carry=True,
      srcb_clear=True, srcb_carry=True,
      dest_clear=True, dest_carry=True,
      fidelity_increment=1,
    )

    if not accumulate:
      self._issue(
        TT.TTZEROACC(3, int(self.dst.fp32), 0, 1, dst_tile * 4),
      )
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    if self._matmul_replay is None:
      modes = (0, 1, 0, 2, 0, 1, 0, 4, 0, 1, 0, 2, 0, 1, 0, 5)
      words = tuple(TT.TTMVMUL(0, 0, mode, 0) for mode in modes)
      start = self._mop.state.replay.allocate(
        len(words), lower=16, upper=32,
      )
      self._matmul_replay = (
        Replay(start, words[:8]), Replay(start + 8, words[8:]),
      )
      for replay in self._matmul_replay: self._mop.load(replay)
      sync(self.k)

    # One MOP iteration executes all 16 face products. HiFi2 always adds a
    # second iteration for its second fidelity phase. Split replays keep MOP-to-Replay
    # FIFO pressure bounded; they are adjacent and contain no throttle NOPs.
    first, second = self._matmul_replay
    clear_a = TT.TTSETRWC(1, 0, 0, 0, 0, 0xF)
    self._mop.configure(LoopTemplate(
      outer=1, inner=2,
      loop=first.play_word(), alternate=second.play_word(),
      end0=clear_a, last=second.play_word(), outer_last=second.play_word(),
    ))
    self._mop.run()
    self._issue(TT.TTSETRWC(2, 0, 0, 0, 0, 0xF))
    return self

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
      # Negate as 0 - scalar. Unlike multiply, ELWSUB has no fidelity phases.
      self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
      self._issue(TT.TTMOVD2B(0, 0, 0, 0, 0))
      self._issue(TT.TTGATESRCRST(1, 1))
      self._issue(TT.TTZEROSRC(0, 1, 0, 1))
      self._issue(TT.TTZEROACC(0, 0, 0, 0, 0))
      self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
      self._issue(TT.TTELWSUB(3, 0, 0, 0, 0))
    self._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    return self
