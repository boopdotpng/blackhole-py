from enum import IntEnum

from ttk.mop import LoopTemplate, NOP
from ttk.tensix import (
  CFG_BASE, Cfg, Tensix, TensixSem, TensixSemWait, TensixStall, TensixWait,
  ThreadCfg, tt_word,
)


class UnpackFormat(IntEnum):
  F32 = 0
  BF16 = 5


class UnpackTarget(IntEnum):
  SRCA = 0
  SRCB = 1
  DST = 2


# Unpacker 0 writes SrcA or Dst. Unpacker 1 writes SrcB. Each independently
# selects config context 0 or 1 through one byte of UNPACK_MISC_CFG.
UNPACKER0, UNPACKER1 = 0, 1
CONTEXT0, CONTEXT1 = 0, 1


def _unpacr(engine, *, to_dst=False):
  return tt_word(
    "TTUNPACR", engine, 0x11 if to_dst else 1, 0, 0, 0, 1,
    int(not to_dst), 0, 0, 0, 0, 0, 1,
  )


def _unpack_mop(engine, faces, *, to_dst=False):
  # START executes once per outer iteration. The loop slot is deliberately a
  # NOP: one UNPACR is one face normally and one complete tile when tilizing.
  return LoopTemplate(
    outer=faces, inner=1, start=_unpacr(engine, to_dst=to_dst), loop=NOP,
  )


_SRCB_DVALID = tt_word("TTUNPACR_NOP", 1, 0, 0, 1, 0, 0, 0, 0, 1)
UNPACK_SRCA = LoopTemplate(
  outer=4, inner=1, start=_unpacr(UNPACKER0), loop=_SRCB_DVALID,
  last=_SRCB_DVALID, outer_last=_SRCB_DVALID,
)
UNPACK_SRCB = _unpack_mop(UNPACKER1, 4)
UNPACK_DST = _unpack_mop(UNPACKER0, 4, to_dst=True)
TILIZE_SRCA = LoopTemplate(
  outer=1, inner=1, start=_unpacr(UNPACKER0), loop=_SRCB_DVALID,
)
TILIZE_DST = _unpack_mop(UNPACKER0, 1, to_dst=True)


_TILE_DESCRIPTOR = (
  Cfg.THCON_SEC0_REG0_TileDescriptor,
  Cfg.THCON_SEC1_REG0_TileDescriptor,
)
_OPTIONS = (Cfg.THCON_SEC0_REG2, Cfg.THCON_SEC1_REG2)
_BASE = (
  Cfg.THCON_SEC0_REG3_Base_address,
  Cfg.THCON_SEC1_REG3_Base_address,
)
_DEST = (Cfg.THCON_SEC0_REG5_Dest_cntx01, CFG_BASE + 132 * 4)
_X_DIM = (Cfg.THCON_SEC0_REG5_Tile_x_dim_cntx01, CFG_BASE + 134 * 4)
_OFFSET = (Cfg.THCON_SEC0_REG7_Offset_address, CFG_BASE + 140 * 4)

_ADDR_XY0 = (Cfg.UNP0_ADDR_CTRL_XY_REG_0, Cfg.UNP1_ADDR_CTRL_XY_REG_0)
_ADDR_ZW0 = (Cfg.UNP0_ADDR_CTRL_ZW_REG_0, Cfg.UNP1_ADDR_CTRL_ZW_REG_0)
_ADDR_XY1 = (Cfg.UNP0_ADDR_CTRL_XY_REG_1, Cfg.UNP1_ADDR_CTRL_XY_REG_1)
_ADDR_ZW1 = (Cfg.UNP0_ADDR_CTRL_ZW_REG_1, Cfg.UNP1_ADDR_CTRL_ZW_REG_1)
_ADDR_BASE0 = (CFG_BASE + 48 * 4, CFG_BASE + 60 * 4)
_ADDR_BASE1 = (CFG_BASE + 49 * 4, CFG_BASE + 61 * 4)
_ADDR_MISC = (Cfg.UNP0, CFG_BASE + 62 * 4)
_NOP_CLEAR = (CFG_BASE + 53 * 4, CFG_BASE + 63 * 4)


def _engine(target):
  return UNPACKER1 if target == UnpackTarget.SRCB else UNPACKER0


def _output_format(input_format, target):
  if input_format == UnpackFormat.F32 and target != UnpackTarget.DST:
    return UnpackFormat.BF16
  return input_format


def _descriptor(fmt, engine, tilize):
  x_dim = 1024 if tilize else 0 if engine == UNPACKER0 else 256
  z_dim = 1 if tilize else 4
  return (
    fmt | 0x10 | x_dim << 16,
    1 | z_dim << 16,
    0,
    0,
  )


def _options(input_format, output_format, to_dst, tilize):
  row_bytes = 32 * (4 if input_format == UnpackFormat.F32 else 2)
  shift = row_bytes >> 4
  word0 = 0x20 | output_format
  if tilize: word0 |= 1 << 9 | shift << 16 | shift << 20
  # Only contexts 0 and 1 are enabled. Direct-to-Dst selection is per context.
  word1 = 0x03 | (0x30 if to_dst else 0)
  return word0, word1, 0, 0


def _face_bytes(fmt): return 1024 if fmt == UnpackFormat.F32 else 512


def _destination_strides(fmt):
  datum_bytes = 4 if fmt == UnpackFormat.F32 else 2
  return datum_bytes | 16 * datum_bytes << 16, 256 * datum_bytes


def _mop(target, tilize):
  if tilize:
    if target == UnpackTarget.SRCB:
      raise ValueError("Blackhole tilize is supported only by unpacker 0")
    return TILIZE_DST if target == UnpackTarget.DST else TILIZE_SRCA
  return (UNPACK_SRCA, UNPACK_SRCB, UNPACK_DST)[target]


class Unpack:
  """Move one BF16/F32 CB tile to SrcA, SrcB, or Dst."""

  def __init__(self, kernel): self.k, self.tensix = kernel, Tensix(kernel, 0)

  @staticmethod
  def l1_address(address):
    if type(address) is not int or address < 16 or address & 15:
      raise ValueError("unpack L1 address must be positive and 16-byte aligned")
    return (address >> 4) - 1

  @staticmethod
  def _cb(cb):
    try: fmt = UnpackFormat(int(cb.dtype))
    except (TypeError, ValueError):
      raise ValueError("unpack supports only BF16 and F32") from None
    tile_bytes = 4096 if fmt == UnpackFormat.F32 else 2048
    if int(cb.addr) & 15 or int(cb.page_size) != tile_bytes:
      raise ValueError("unpack CB must be one aligned BF16 or F32 tile per page")
    return fmt

  def _write_mode(self, engine, input_format, output_format, target, tilize):
    k = self.k
    for index, word in enumerate(_descriptor(input_format, engine, tilize)):
      k.write32(int(_TILE_DESCRIPTOR[engine]) + index * 4, word)
    for index, word in enumerate(_options(
      input_format, output_format, target == UnpackTarget.DST, tilize,
    )):
      k.write32(int(_OPTIONS[engine]) + index * 4, word)

    for register in (_ADDR_XY0[engine], _ADDR_ZW0[engine]):
      k.write32(int(register), 0)
    xy_stride, z_stride = _destination_strides(output_format)
    k.write32(int(_ADDR_XY1[engine]), xy_stride)
    k.write32(int(_ADDR_ZW1[engine]), z_stride)
    k.write32(int(_ADDR_BASE0[engine]), 0)
    k.write32(int(_ADDR_BASE1[engine]), 0)
    k.write32(int(_ADDR_MISC[engine]), 0x100 if engine == UNPACKER0 else 0)
    k.write32(int(_NOP_CLEAR[engine]), 0)

    x_dim = 1024 if tilize else 256
    destination = 64 if engine == UNPACKER0 else 0
    k.write32(int(_DEST[engine]), destination | destination << 16)
    k.write32(int(_X_DIM[engine]), x_dim | x_dim << 16)
    k.write32(int(_OFFSET[engine]), 0)
    k.write32(int(_OFFSET[engine]) + 4, 0)

  def _write_bases(self, engine, cb):
    with self.k.scope():
      address = self.k.reg()
      cb.read_ptr(address)
      self.k.srli(address, address, 4)
      self.k.addi(address, address, -1)
      self.k.write32(int(_BASE[engine]), address)
      self.k.write32(int(_BASE[engine]) + 4, address)

  def _configure(self, cb, target, tilize):
    input_format = self._cb(cb)
    output_format, engine = _output_format(input_format, target), _engine(target)
    t = self.tensix

    t.wait_unpack_config_idle()
    t.issue(tt_word("TTSETC16", int(ThreadCfg.CFG_STATE_ID), 0))
    self._write_mode(engine, input_format, output_format, target, tilize)
    self._write_bases(engine, cb)
    # This stateless path fully drains each move, so context 0 is always free.
    t.issue(tt_word("TTSETC16", int(ThreadCfg.UNPACK_MISC_CFG), 0))
    if engine == UNPACKER0:
      t.issue(tt_word(
        "TTSETC16", int(ThreadCfg.SRCA_SET),
        0 if target == UnpackTarget.DST else 4,
      ))
    t.commit_unpack_config(_BASE[engine])
    t.mop.configure(_mop(target, tilize))
    return engine

  def _move_source(self, cb, target, tilize):
    t = self.tensix
    engine = self._configure(cb, target, tilize)
    t.issue(tt_word("TTSETADCXX", engine + 1, 1023 if tilize else 255, 0))
    t.issue(tt_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))
    t.stall(TensixStall.UNPACK, TensixWait.TRISC_CFG)
    t.mop.run()
    t.stall(
      TensixStall.UNPACK,
      TensixWait.UNPACK1 if engine == UNPACKER1 else TensixWait.UNPACK0,
    )
    t.semaphore_get(TensixSem.UNPACK_SYNC)
    t.sync()

  def _move_dst(self, cb, tilize):
    t = self.tensix
    self._configure(cb, UnpackTarget.DST, tilize)
    t.issue(tt_word("TTSETADCXX", 1, 1023 if tilize else 255, 0))
    t.issue(tt_word("TTSETADCZW", 3, 0, 0, 0, 0, 0xF))

    t.semaphore_wait(
      TensixSem.MATH_DONE, TensixSemWait.STALL_ON_ZERO,
      stall=TensixStall.UNPACK,
    )
    t.semaphore_get(TensixSem.MATH_DONE)
    t.semaphore_wait(
      TensixSem.UNPACK_TO_DEST, TensixSemWait.STALL_ON_MAX,
      stall=TensixStall.UNPACK,
    )
    t.stall(TensixStall.UNPACK, TensixWait.TRISC_CFG | TensixWait.PACK0)
    t.mop.run()
    t.stall(TensixStall.UNPACK, TensixWait.THCON | TensixWait.UNPACK0)
    t.semaphore_get(TensixSem.UNPACK_SYNC)
    t.sync()
    t.issue(tt_word("TTSETC16", int(ThreadCfg.SRCA_SET), 4))
    t.semaphore_post(TensixSem.UNPACK_TO_DEST)

  def move(self, source_cb, target, *, tilize=False):
    try: target = UnpackTarget(target)
    except (TypeError, ValueError): raise ValueError("invalid unpack target") from None
    if type(tilize) is not bool: raise TypeError("tilize must be bool")
    _mop(target, tilize)  # Validate before emitting CB operations.

    source_cb.wait_front()
    if target == UnpackTarget.DST:
      self._move_dst(source_cb, tilize)
    else:
      self.tensix.stall(
        TensixStall.UNPACK,
        TensixWait.SRCB_CLR if target == UnpackTarget.SRCB else TensixWait.SRCA_CLR,
      )
      self._move_source(source_cb, target, tilize)
    source_cb.pop_front()
    return self
