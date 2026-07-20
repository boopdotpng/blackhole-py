from enum import IntEnum

from fw.consts import TensixMMIO
from isa import R, Tensix as TT
from ttk.cb import CB
from ttk import DType
from ttk.dst import Dst
from ttk.mop import LoopTemplate, MaskTemplate, Mop, NOP
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
_REDUCE_MOP = MaskTemplate(
  a0=TT.TTUNPACR_NOP(0, 0, 0, 0, 0, 0, 0, 0, 1),
  a1=_unpacr(UNPACKER0), a2=NOP, a3=NOP,
  b=_unpacr(UNPACKER1), skip_a0=NOP, skip_b=NOP,
)
_TILIZE_MOPS = (
  LoopTemplate(outer=1, inner=1, start=_unpacr(UNPACKER0), loop=_SRCB_DVALID),
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
    raise ValueError("Blackhole tilize is supported only by unpacker 0")
  return (_TILIZE_MOPS if tilize else _MOPS)[target]

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
                  tile, x_dim=None, transpose=False, whole_tile=False):
    k = self.k
    descriptor_x_dim = (
      x_dim if x_dim is not None else
      1024 if tilize else 0 if engine == UNPACKER0 else 256
    )
    descriptor = (
      input_format | 0x10 | descriptor_x_dim << 16,
      (4 | 1 << 16) if whole_tile else (1 | (1 if tilize else 4) << 16),
      0, 0,
    )
    shift = 2 * input_format.itemsize
    word0 = 0x20 | output_format
    if tilize: word0 |= 1 << 9 | shift << 16 | shift << 20
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
                 whole_tile=False):
    input_format = cb.dtype
    output_format = DType.BF16 if input_format == DType.F32 and target != UnpackTarget.DST else input_format
    engine = int(target == UnpackTarget.SRCB)
    self._wait_config_idle()
    self._set_thread_cfg(0, 0)
    self._write_mode(
      engine, input_format, output_format, target, tilize, tile,
      transpose=transpose, whole_tile=whole_tile,
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
                    commit=True, configure_mop=True):
    engine = int(target == UnpackTarget.SRCB)
    self._wait_config_idle()
    self._set_thread_cfg(0, 0)
    self._write_mode(
      engine, dtype, dtype, target, False, None, x_dim=x_dim,
    )
    base = (address >> 4) - 1
    self.k.write(int(_BASE[engine]), base)
    self.k.write(int(_BASE[engine]) + 4, base)
    if commit: self._commit_config(_BASE[engine])
    if configure_mop:
      self._mop.configure(_select_mop(target, False))
    return engine

  def _run(self, cb, target, tilize, tile, mop=None):
    engine = self._configure(cb, target, tilize, tile, mop)
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

  def _move(self, source_cb, target, tilize, tile, mop=None):
    if target == UnpackTarget.DST: self.dst.check(tile)
    _select_mop(target, tilize)  # Validate before emitting CB operations.
    CB.wait_front(self.k, source_cb)
    if target != UnpackTarget.DST:
      stall(self.k, Stall.UNPACK, Wait.SRCB_CLR if target == UnpackTarget.SRCB else Wait.SRCA_CLR)
    self._run(source_cb, target, tilize, tile, mop)
    CB.pop_front(self.k, source_cb)
    return self

  def move(self, source_cb, target, tilize=False, *, tile=None):
    return self._move(source_cb, target, tilize, tile)

  def move_pair(self, source_a_cb, source_b_cb):
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
    self._mop.configure(_PAIR_MOP)
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
    """Unpack a CB tile into SrcA and a same-format L1 tile into SrcB."""
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

  def move_reduce(self, source_cb, scaler_address, *, scaler_rows=4,
                  transpose=False):
    if source_cb.dtype is not DType.BF16:
      raise ValueError("reduce unpack currently requires BF16 input")
    if type(scaler_rows) is not int or not 1 <= scaler_rows <= 16:
      raise ValueError("reduce scaler_rows must be in range 1..16")
    scaler_values = scaler_rows * 16
    CB.wait_front(self.k, source_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False, transpose=transpose,
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

  def move_reduce_row(self, source_cb, scaler_address):
    """Load one BF16 tile transposed for a row pool and one scaler face."""
    if source_cb.dtype is not DType.BF16:
      raise ValueError("row reduce unpack currently requires BF16 input")
    CB.wait_front(self.k, source_cb)
    stall(self.k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    self._configure(
      source_cb, UnpackTarget.SRCA, False, None,
      commit=False, configure_mop=False, transpose=True, whole_tile=True,
    )
    self._configure_l1(
      DType.BF16, UnpackTarget.SRCB, scaler_address, 256,
      commit=False, configure_mop=False,
    )
    self._commit_config(_BASE[UNPACKER0])
    self._issue(TT.TTSETADCXX(1, 1023, 0))
    self._issue(TT.TTSETADCXX(2, 255, 0))
    self._issue(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(self.k, Stall.UNPACK, Wait.TRISC_CFG)
    self._issue(_unpacr(UNPACKER1))
    self._issue(_unpacr(UNPACKER0))
    stall(self.k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(self.k, Sem.UNPACK_SYNC); sync(self.k)
    CB.pop_front(self.k, source_cb)
    return self
