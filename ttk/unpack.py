from enum import IntEnum

from fw.consts import TensixMMIO
from isa import R, Tensix as TT
from ttk import Dst, DType
from ttk.cb import CB
from ttk.mop import LoopTemplate, MaskTemplate, Mop, NOP, Replay
from ttk.sync import Sem, SemWait, Stall, Wait, sem_get, sem_post, sem_wait, stall, sync

class UnpackTarget(IntEnum):
  SRCA, SRCB, DST = range(3)

CFG_BASE = TensixMMIO.CFG_BASE

class _Cfg(IntEnum):
  UNPACK0_ADDRESS_XY0 = CFG_BASE + 0xB0; UNPACK0_ADDRESS_ZW0 = CFG_BASE + 0xB4
  UNPACK1_ADDRESS_XY0 = CFG_BASE + 0xB8; UNPACK1_ADDRESS_ZW0 = CFG_BASE + 0xBC
  UNPACK0_MISC = CFG_BASE + 0xC8
  UNPACK0_ADDRESS_XY1 = CFG_BASE + 0xE0; UNPACK0_ADDRESS_ZW1 = CFG_BASE + 0xE4
  UNPACK1_ADDRESS_XY1 = CFG_BASE + 0xE8; UNPACK1_ADDRESS_ZW1 = CFG_BASE + 0xEC
  UNPACK0_TILE_DESCRIPTOR = CFG_BASE + 0x100; UNPACK0_OPTIONS = CFG_BASE + 0x120
  UNPACK0_BASE = CFG_BASE + 0x130; UNPACK0_DESTINATION = CFG_BASE + 0x150
  UNPACK0_X_DIMENSION = CFG_BASE + 0x158
  UNPACK0_OFFSET = CFG_BASE + 0x170
  UNPACK1_TILE_DESCRIPTOR = CFG_BASE + 0x1C0; UNPACK1_OPTIONS = CFG_BASE + 0x1E0
  UNPACK1_BASE = CFG_BASE + 0x1F0

_SRCA_SET, _MISC_CONFIG = 5, 41

# Unpacker 0 writes SrcA or Dst; unpacker 1 writes SrcB.
UNPACKER0, UNPACKER1 = range(2)

def _unpacr(engine, to_dst=False):
  return TT.TTUNPACR(engine, 0x11 if to_dst else 1, 0, 0, 0, 1,
                    int(not to_dst), 0, 0, 0, 0, 0, 1)

def _mop(engine, faces=4, to_dst=False):
  return LoopTemplate(outer=faces, inner=1, start=_unpacr(engine, to_dst), loop=NOP)

_SRCB_DVALID = TT.TTUNPACR_NOP(1, 0, 0, 1, 0, 0, 0, 0, 1)
_MOPS = (
  LoopTemplate(outer=4, inner=1, start=_unpacr(UNPACKER0), loop=_SRCB_DVALID,
               last=_SRCB_DVALID, outer_last=_SRCB_DVALID),
  _mop(UNPACKER1),
  _mop(UNPACKER0, to_dst=True),
)
_PAIR_MOP = LoopTemplate(
  outer=4, inner=1, start=_unpacr(UNPACKER0), loop=_unpacr(UNPACKER1),
  last=_unpacr(UNPACKER1), outer_last=_unpacr(UNPACKER1),
)
_REDUCE_PAIR_REPLAY = Replay(
  0, (_unpacr(UNPACKER0), _unpacr(UNPACKER1)),
)
_REDUCE_PAIR_MOP = LoopTemplate(
  outer=1, inner=4, loop=_REDUCE_PAIR_REPLAY,
  last=_REDUCE_PAIR_REPLAY, outer_last=_REDUCE_PAIR_REPLAY,
)
_COLUMN_PAIR_MOP = LoopTemplate(
  outer=2, inner=2, start=_unpacr(UNPACKER1), loop=_unpacr(UNPACKER0),
  end0=TT.TTSETADCZW(2, 0, 0, 0, 2, 1),
  last=_unpacr(UNPACKER0), outer_last=_unpacr(UNPACKER0),
)
_ROW_PAIR_MOP = LoopTemplate(
  outer=2, inner=2, start=_unpacr(UNPACKER1), loop=_unpacr(UNPACKER0),
  end0=TT.TTSETADCZW(2, 0, 0, 0, 0, 1),
  last=_unpacr(UNPACKER0), outer_last=_unpacr(UNPACKER0),
)
_REDUCE_MOP = MaskTemplate(
  a0=TT.TTUNPACR_NOP(0, 0, 0, 0, 0, 0, 0, 0, 1),
  a1=_unpacr(UNPACKER0), a2=NOP, a3=NOP,
  b=_unpacr(UNPACKER1), skip_a0=NOP, skip_b=NOP,
)
_FAST_TILIZE_MOP = MaskTemplate(
  a0=TT.TTUNPACR(UNPACKER0, 0x11, 0, 0, 0, 1, 0,
                 0, 0, 0, 0, 0, 1),
  # Masked iterations terminate each group of eight reads and publish SrcA.
  skip_a0=TT.TTUNPACR(UNPACKER0, 0x11, 0, 0, 0, 1, 1,
                      0, 0, 0, 0, 0, 1),
)
_TILIZE_MOPS = (
  # One UNPACR consumes all 1024 datums, so the sole iteration is also the last
  # and `loop` never runs -- the SrcB data-valid has to come from `last` and
  # `outer_last`. Math clears both banks, so SrcB is marked valid even though
  # only SrcA is written. Pair this with `fpu.copy_a_tilized`, which expects a
  # single data-valid and undoes the tilizer's stride-2 row order.
  LoopTemplate(outer=1, inner=1, start=_unpacr(UNPACKER0), loop=_SRCB_DVALID,
               last=_SRCB_DVALID, outer_last=_SRCB_DVALID),
  None,
  _mop(UNPACKER0, 1, to_dst=True),
)

_TILE_DESCRIPTOR = (_Cfg.UNPACK0_TILE_DESCRIPTOR, _Cfg.UNPACK1_TILE_DESCRIPTOR)
_OPTIONS = (_Cfg.UNPACK0_OPTIONS, _Cfg.UNPACK1_OPTIONS)
_BASE = (_Cfg.UNPACK0_BASE, _Cfg.UNPACK1_BASE)
_DEST = (_Cfg.UNPACK0_DESTINATION, CFG_BASE + 132 * 4)
_X_DIM = (_Cfg.UNPACK0_X_DIMENSION, CFG_BASE + 134 * 4)
_OFFSET = (_Cfg.UNPACK0_OFFSET, CFG_BASE + 140 * 4)
_ADDR_XY0 = (_Cfg.UNPACK0_ADDRESS_XY0, _Cfg.UNPACK1_ADDRESS_XY0)
_ADDR_ZW0 = (_Cfg.UNPACK0_ADDRESS_ZW0, _Cfg.UNPACK1_ADDRESS_ZW0)
_ADDR_XY1 = (_Cfg.UNPACK0_ADDRESS_XY1, _Cfg.UNPACK1_ADDRESS_XY1)
_ADDR_ZW1 = (_Cfg.UNPACK0_ADDRESS_ZW1, _Cfg.UNPACK1_ADDRESS_ZW1)
_ADDR_BASE0 = (CFG_BASE + 48 * 4, CFG_BASE + 60 * 4)
_ADDR_BASE1 = (CFG_BASE + 49 * 4, CFG_BASE + 61 * 4)
_ADDR_MISC = (_Cfg.UNPACK0_MISC, CFG_BASE + 62 * 4)
_NOP_CLEAR = (CFG_BASE + 53 * 4, CFG_BASE + 63 * 4)
_CONFIG_SYNC = 0xFFE80034

def _select_mop(target, tilize):
  if tilize and target == UnpackTarget.SRCB:
    raise ValueError("tilize into SrcB is not implemented")
  mop = (_TILIZE_MOPS if tilize else _MOPS)[target]
  if mop is None: raise ValueError("unsupported tilize target")
  return mop

class Unpack:
  def __init__(self, kernel, dst: Dst):
    self.k, self.dst, self._mop = kernel, dst, Mop(kernel, 0)

  def _issue(self, word):
    self.k.emit(word)
    return self

  def _set_thread_cfg(self, register, value):
    return self._issue(TT.TTSETC16(int(register), int(value)))

  def _wait_config_idle(self):
    k = self.k
    with k.scope():
      pointer, value = k.reg(2); k.li(pointer, _CONFIG_SYNC)
      again, done = k._new_label("unpack_cfg_idle"), k._new_label("unpack_cfg_ready")
      k.label(again); k.lw(value, pointer, 0); k.andi(value, value, 0xFE)
      k.beq(value, R.ZERO, done); k.fence(); k.j(again); k.label(done)

  def _commit_config(self, register):
    with self.k.scope():
      observed = self.k.reg()
      self.k.read(observed, int(register)); self.k.write(_CONFIG_SYNC, 0)

  def _write_mode(self, engine, input_format, output_format, target, tilize,
                  tile, x_dim=None, transpose=False, row_stride=None):
    k = self.k
    descriptor_x_dim = (
      x_dim if x_dim is not None else
      1024 if tilize else 0 if engine == UNPACKER0 else 256
    )
    descriptor = (
      input_format | 0x10 | descriptor_x_dim << 16,
      1 | (1 if tilize else 4) << 16, 0, 0,
    )
    word0 = 0x20 | output_format
    if tilize:
      # Tileize_mode makes the unpacker gather 32 discontiguous source rows.
      # RowStride is assembled from three 4-bit Shift_amount_cntx fields at
      # bits 16/20/24, contributing at bit positions 4/8/12 respectively --
      # so the register just holds (stride bytes / 16) split into nibbles.
      stride = (
        32 * input_format.itemsize if row_stride is None else row_stride
      )
      if stride <= 0 or stride % 16 or stride > 65520:
        raise ValueError(
          "tilize row stride must be a positive multiple of 16 bytes "
          "no larger than 65520",
        )
      units = stride // 16
      word0 |= (
        1 << 9 | (units & 0xF) << 16
        | (units >> 4 & 0xF) << 20 | (units >> 8 & 0xF) << 24
      )
    if transpose: word0 |= 1 << 8
    options = (word0, 0x03 | (0x30 if target == UnpackTarget.DST else 0), 0, 0)
    for base, words in ((_TILE_DESCRIPTOR[engine], descriptor), (_OPTIONS[engine], options)):
      for index, word in enumerate(words): k.write(int(base) + index * 4, word)

    size = output_format.itemsize
    for register, value in (
      (_ADDR_XY0[engine], 0), (_ADDR_ZW0[engine], 0),
      (_ADDR_XY1[engine], size | 16 * size << 16),
      (_ADDR_ZW1[engine], 256 * size),
      (_ADDR_BASE0[engine], 0), (_ADDR_BASE1[engine], 0),
      (_ADDR_MISC[engine], 0x100 if engine == UNPACKER0 else 0),
      (_NOP_CLEAR[engine], 0),
    ): k.write(int(register), value)

    destination = 64 if engine == UNPACKER0 else 0
    if target == UnpackTarget.DST:
      destination += self.dst.row_base(tile) * 16
    x_dim = x_dim if x_dim is not None else 1024 if tilize else 256
    for register, value in (
      (_DEST[engine], destination | destination << 16),
      (_X_DIM[engine], x_dim | x_dim << 16),
      (_OFFSET[engine], 0), (int(_OFFSET[engine]) + 4, 0),
    ): k.write(int(register), value)

  def _configure(self, cb, target, tilize, tile, mop=None, *,
                 commit=True, configure_mop=True, transpose=False,
                 row_stride=None):
    input_format = cb.dtype
    output_format = DType.BF16 if input_format == DType.F32 and target != UnpackTarget.DST else input_format
    engine = int(target == UnpackTarget.SRCB)
    self._wait_config_idle()
    self._set_thread_cfg(0, 0)
    self._write_mode(
      engine, input_format, output_format, target, tilize, tile,
      transpose=transpose, row_stride=row_stride,
    )
    with self.k.scope():
      address = self.k.reg()
      CB.get_read_ptr(self.k, cb, address)
      self.k.srli(address, address, 4); self.k.addi(address, address, -1)
      self.k.write(int(_BASE[engine]), address)
      self.k.write(int(_BASE[engine]) + 4, address)
    # This stateless path fully drains each move, so context 0 is always free.
    self._issue(TT.TTSETC16(_MISC_CONFIG, 0))
    if engine == UNPACKER0:
      self._issue(TT.TTSETC16(_SRCA_SET, 0 if target == UnpackTarget.DST else 4))
    if commit: self._commit_config(_BASE[engine])
    if configure_mop:
      self._mop.configure(_select_mop(target, tilize) if mop is None else mop)
    return engine

  def _configure_l1(self, dtype, target, address, x_dim, *,
                    commit=True, configure_mop=True, transpose=False):
    engine = int(target == UnpackTarget.SRCB)
    self._wait_config_idle()
    self._set_thread_cfg(0, 0)
    self._write_mode(
      engine, dtype, dtype, target, False, None, x_dim=x_dim,
      transpose=transpose,
    )
    if isinstance(address, R):
      with self.k.scope():
        base = self.k.reg(exclude=address)
        self.k.srli(base, address, 4)
        self.k.addi(base, base, -1)
        self.k.write(int(_BASE[engine]), base)
        self.k.write(int(_BASE[engine]) + 4, base)
    else:
      base = (address >> 4) - 1
      self.k.write(int(_BASE[engine]), base)
      self.k.write(int(_BASE[engine]) + 4, base)
    self._issue(TT.TTSETC16(_MISC_CONFIG, 0))
    if engine == UNPACKER0:
      self._issue(TT.TTSETC16(_SRCA_SET, 4))
    if commit: self._commit_config(_BASE[engine])
    if configure_mop:
      self._mop.configure(_select_mop(target, False))
    return engine

  def _run(self, cb, target, tilize, tile, mop=None, row_stride=None):
    engine = self._configure(
      cb, target, tilize, tile, mop, row_stride=row_stride,
    )
    self._issue(TT.TTSETADCXX(engine + 1, 1023 if tilize else 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    if target == UnpackTarget.DST:
      sem_wait(self.k, Sem.MATH_DONE, SemWait.STALL_ON_ZERO, Stall.UNPACK)
      sem_get(self.k, Sem.MATH_DONE)
      sem_wait(self.k, Sem.UNPACK_TO_DEST, SemWait.STALL_ON_MAX, Stall.UNPACK)
      # Both barriers are required on hardware; without direct-to-Dst serialization
      # the older RMSNorm path observed only the final face.
      stall(self.k, Stall.UNPACK, Wait.TRISC_CFG | Wait.PACK0)
    else: stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    if target == UnpackTarget.DST:
      stall(self.k, Stall.UNPACK, Wait.THCON | Wait.UNPACK0)
    else:
      stall(self.k, Stall.UNPACK, Wait.UNPACK1 if engine == UNPACKER1 else Wait.UNPACK0)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    if target == UnpackTarget.DST:
      self._issue(TT.TTSETC16(_SRCA_SET, 4))
      sem_post(self.k, Sem.UNPACK_TO_DEST)

  def _move(self, source_cb, target, tilize, tile, mop=None,
            row_stride=None):
    if target == UnpackTarget.DST: self.dst.check(tile)
    _select_mop(target, tilize)  # Validate before emitting CB operations.
    CB.wait_front(self.k, source_cb)
    if target != UnpackTarget.DST:
      stall(self.k, Stall.UNPACK, Wait.SRCB_CLR if target == UnpackTarget.SRCB else Wait.SRCA_CLR)
    self._run(source_cb, target, tilize, tile, mop, row_stride)
    CB.pop_front(self.k, source_cb)
    return self

  def move(self, source_cb, target, tilize=False, *, tile=None,
           row_stride=None):
    """Move one tile into SrcA/SrcB/Dst, optionally tilizing on the way.

    `row_stride` is the byte pitch between consecutive source rows and only
    applies when tilizing. It defaults to a packed 32-datum row; pass the
    pitch of the surrounding block to gather a 32-wide column slice out of a
    wider row-major region.
    """
    return self._move(source_cb, target, tilize, tile, row_stride=row_stride)

  def fast_tilize(self, source_cb, *, width_tiles):
    return self.fast_tilize_blocks(
      source_cb, width_tiles=width_tiles, blocks=1,
    )

  def fast_tilize_blocks(self, source_cb, *, width_tiles, blocks):
    """Present one row-major 32-row block to the BH fast-tilize math path.

    Four adjacent output tiles are processed per chunk.  UNPACR reads 128
    BF16 datums from each input row into eight SrcA rows, and publishes after
    every eight rows.  This is the Blackhole LLK workaround for the ordinary
    tilizer's SrcA 16-row-set write hazard. Multiple blocks retain the same
    unpack configuration so producer/consumer staging does not reconfigure
    SrcA while math is still returning banks from the preceding block.
    """
    if source_cb.dtype is not DType.BF16:
      raise ValueError("fast tilize currently requires BF16 input")
    if type(width_tiles) is not int or width_tiles < 4 or width_tiles % 4:
      raise ValueError("fast tilize width must be a positive multiple of 4")
    if source_cb.depth < width_tiles:
      raise ValueError("fast tilize input CB must hold one complete row")
    if type(blocks) is not int or blocks <= 0:
      raise ValueError("fast tilize block count must be positive")

    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR)
    self._configure(
      source_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False,
    )

    # Match the current Blackhole experimental fast-tilize LLK:
    # Tile_x_dim=32, Tile_y_dim=the row width, Tile_z_dim=16, and an
    # eight-SrcA-row (256-byte) CH1 Z stride.
    self.k.write(int(_X_DIM[UNPACKER0]), 32 | 32 << 16)
    self.k.write(
      int(_TILE_DESCRIPTOR[UNPACKER0]) + 4,
      width_tiles | 16 << 16,
    )
    self.k.write(int(_ADDR_ZW1[UNPACKER0]), 256)
    self._mop.configure(_FAST_TILIZE_MOP)
    self._issue(TT.TTSETADCXX(1, 4 * 32 - 1, 0))

    for _ in range(blocks):
      CB.wait_front(self.k, source_cb, width_tiles)
      for chunk in self.k.range(width_tiles // 4):
        with self.k.scope():
          address, offset = self.k.reg(2, exclude=chunk)
          CB.get_read_ptr(self.k, source_cb, address)
          self.k.slli(offset, chunk, 8)
          self.k.add(address, address, offset)
          self.k.srli(address, address, 4)
          self.k.addi(address, address, -1)
          self.k.write(int(_BASE[UNPACKER0]), address)
          self.k.write(int(_BASE[UNPACKER0]) + 4, address)
        self._commit_config(_BASE[UNPACKER0])
        self._issue(TT.TTSETADCXY(1, 0, 0, 0, 0, 0x3))
        self._issue(TT.TTSETADCZW(1, 0, 0, 0, 0, 0xF))
        stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
        self._mop.run(32, 0x80808080)
        stall(self.k, Stall.UNPACK, Wait.UNPACK0)
        sem_get(self.k, Sem.UNPACK_SYNC)
        sync(self.k)
      CB.pop_front(self.k, source_cb, width_tiles)
    return self

  def move_l1(self, dtype, address, target=UnpackTarget.SRCA):
    """Present one face-tilized tile from a persistent L1 address."""
    if not isinstance(dtype, DType):
      raise TypeError("L1 unpack dtype must be a DType")
    if type(address) is not int or address < 0:
      raise ValueError("L1 unpack address must be a non-negative integer")
    if target != UnpackTarget.SRCA:
      raise ValueError("persistent L1 unpack currently supports only SrcA")

    engine = self._configure_l1(dtype, target, address, 256)
    self._issue(TT.TTSETADCXX(engine + 1, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG | Wait.SRCA_CLR)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    return self

  def move_pair(self, source_a_cb, source_b_cb):
    return self._move_pair(source_a_cb, source_b_cb, _PAIR_MOP)

  def move_pair_same(self, source_cb):
    """Present one CB tile as both operands without reading or copying it twice."""
    CB.wait_front(self.k, source_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False,
    )
    self._configure(
      source_cb, UnpackTarget.SRCB, False, None,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(_PAIR_MOP)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC)
    sync(self.k)
    CB.pop_front(self.k, source_cb)
    return self

  def move_matmul(self, left_cb, right_cb, *, right_transpose=False):
    self.dst.require_fp32()
    if left_cb.dtype is not DType.BF16 or right_cb.dtype is not DType.BF16:
      raise ValueError("matmul unpack currently requires BF16 inputs")
    CB.wait_front(self.k, left_cb)
    CB.wait_front(self.k, right_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)

    # MVMUL computes SrcB @ SrcA. Unlike elementwise pair unpack, matmul
    # presents all four faces of each tile in one UNPACR operation.
    self._configure(
      right_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False, transpose=right_transpose,
    )
    self._configure(
      left_cb, UnpackTarget.SRCB, False, None,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._issue(TT.TTSETADCXX(1, 1023, 0))
    self._issue(TT.TTSETADCXX(2, 1023, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._issue(TT.TTUNPACR(
      UNPACKER1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1,
    ))
    self._issue(TT.TTUNPACR(
      UNPACKER0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1,
    ))
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    CB.pop_front(self.k, left_cb)
    CB.pop_front(self.k, right_cb)
    return self

  def move_pair_rows(self, source_a_cb, source_b_cb):
    return self._move_pair(source_a_cb, source_b_cb, _COLUMN_PAIR_MOP)

  def move_pair_rows_persistent(self, source_a_cb, source_b_cb):
    """Column-broadcast SrcB without consuming its persistent CB front tile."""
    CB.wait_front(self.k, source_a_cb)
    CB.wait_front(self.k, source_b_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_a_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False,
    )
    self._configure(
      source_b_cb, UnpackTarget.SRCB, False, None,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(_COLUMN_PAIR_MOP)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC)
    sync(self.k)
    CB.pop_front(self.k, source_a_cb)
    return self

  def move_l1_cb_rows(self, source_a_address, source_b_cb):
    """Column-broadcast a CB row over one persistent full L1 SrcA tile."""
    if type(source_a_address) is not int or source_a_address < 0:
      raise ValueError("persistent L1 tile address must be non-negative")
    CB.wait_front(self.k, source_b_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure_l1(
      DType.BF16, UnpackTarget.SRCA, source_a_address, 256,
      commit=False, configure_mop=False,
    )
    self._configure(
      source_b_cb, UnpackTarget.SRCB, False, None,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(_COLUMN_PAIR_MOP)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC)
    sync(self.k)
    CB.pop_front(self.k, source_b_cb)
    return self

  def move_l1_pair_row_broadcast(
    self, source_a_cb, source_b_address, source_b_dtype=DType.BF16,
  ):
    """Pair a streamed tile with one persistent 32-value SrcB row."""
    if source_b_dtype is not DType.BF16:
      raise ValueError("persistent broadcast rows currently require BF16")
    if not isinstance(source_b_address, (int, R)):
      raise TypeError("persistent broadcast-row address must be int or register")
    CB.wait_front(self.k, source_a_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_a_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False,
    )
    self._configure_l1(
      source_b_dtype, UnpackTarget.SRCB, source_b_address, 256,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(_ROW_PAIR_MOP)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC)
    sync(self.k)
    CB.pop_front(self.k, source_a_cb)
    return self

  def move_l1_pair_rows(self, source_a_cb, source_b_address,
                        source_b_dtype=DType.BF16):
    """Pair a streamed tile with persistent logical-column-0 row values."""
    if source_b_dtype is not DType.BF16:
      raise ValueError("persistent row values currently require BF16")
    if type(source_b_address) is not int or source_b_address < 0:
      raise ValueError("persistent row-value address must be non-negative")
    CB.wait_front(self.k, source_a_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_a_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False,
    )
    self._configure_l1(
      source_b_dtype, UnpackTarget.SRCB, source_b_address, 256,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(_COLUMN_PAIR_MOP)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    CB.pop_front(self.k, source_a_cb)
    return self

  def _move_pair(self, source_a_cb, source_b_cb, mop):
    CB.wait_front(self.k, source_a_cb)
    CB.wait_front(self.k, source_b_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_a_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False,
    )
    self._configure(
      source_b_cb, UnpackTarget.SRCB, False, None,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(mop)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    CB.pop_front(self.k, source_a_cb)
    CB.pop_front(self.k, source_b_cb)
    return self

  def move_l1_pair(self, source_cb, l1_address):
    CB.wait_front(self.k, source_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False,
    )
    self._configure_l1(
      source_cb.dtype, UnpackTarget.SRCB, l1_address, 256,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(_PAIR_MOP)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    CB.pop_front(self.k, source_cb)
    return self

  def move_reduce(self, source_cb, scaler_address, *, scaler_rows=4):
    if source_cb.dtype is not DType.BF16:
      raise ValueError("reduce unpack currently requires BF16 input")
    if type(scaler_rows) is not int or not 1 <= scaler_rows <= 16:
      raise ValueError("reduce scaler_rows must be in range 1..16")
    scaler_values = scaler_rows * 16
    CB.wait_front(self.k, source_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False,
    )
    self._configure_l1(
      DType.BF16, UnpackTarget.SRCB, scaler_address, scaler_values,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(_REDUCE_MOP)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, scaler_values - 1, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run(4)
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    CB.pop_front(self.k, source_cb)
    return self

  def move_row_reduce(self, source_cb, scaler_address, *, maximum):
    if source_cb.dtype not in (DType.BF16, DType.F32):
      raise ValueError("row reduce unpack requires BF16 or F32 input")
    CB.wait_front(self.k, source_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    if maximum:
      # GMPOOL consumes data from SrcA. Haloize transposes each face so its
      # logical rows become the columns reduced by GMPOOL.
      self._configure(
        source_cb, UnpackTarget.SRCA, False, None,
        commit=False, configure_mop=False, transpose=True,
      )
      self._configure_l1(
        DType.BF16, UnpackTarget.SRCB, scaler_address, 256,
        commit=False, configure_mop=False,
      )
    else:
      # MVMUL consumes a halo-transposed scaler column from SrcA and the
      # untransposed data rows from SrcB.
      self._configure_l1(
        DType.BF16, UnpackTarget.SRCA, scaler_address, 256,
        commit=False, configure_mop=False, transpose=True,
      )
      self._configure(
        source_cb, UnpackTarget.SRCB, False, None,
        commit=False, configure_mop=False,
      )
    self._commit_config(_BASE[UNPACKER0])
    self._mop.configure(_REDUCE_PAIR_MOP)
    self._issue(TT.TTSETADCXX(1, 255, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._mop.run()
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    CB.pop_front(self.k, source_cb)
    return self
