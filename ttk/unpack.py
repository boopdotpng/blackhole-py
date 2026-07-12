"""Typed TRISC0 unpack configuration and lowering."""
from dataclasses import dataclass
from enum import Enum, IntEnum

from ttk.tensix import (
  Cfg, MopCfg, Tensix, TensixState, UnpackState, TensixStall, TensixWait,
)


# Named MOPs used by the old matmul/RMSNorm kernels.  The replay slots in the
# matmul template are populated by the caller; the ordinary template is the
# same shape as the firmware's unpack_AB setup.
UNPACK_MOP_CFG = MopCfg.unpack_ab()

UNPACK_SRC_A_MOP_CFG = MopCfg.unpack_one(block=0)

UNPACK_SRC_B_MOP_CFG = MopCfg.unpack_one(block=1)

UNPACK_TO_DST_MOP_CFG = MopCfg.direct_to_dst()

# Matmul's intermediate-Dst reload has the same four-face direct-Dst shape as
# RMSNorm, while the SrcA reload uses one ordinary address-mode-1 face.
UNPACK_RELOAD_MOP_CFG = MopCfg.unpack_faces(addr_mode=1)

UNPACK_RELOAD_TO_DST_MOP_CFG = UNPACK_TO_DST_MOP_CFG

UNPACK_ROW_BROADCAST_MOP_CFG = MopCfg.row_broadcast()


class UnpackFormat(IntEnum):
  F32 = 0
  F16 = 1
  BF16 = 5
  BFP4 = 7
  INT32 = 8
  UINT16 = 9
  INT8 = 14
  UINT32 = 24
  UINT8 = 30


class UnpackTarget(Enum):
  SRCA = "srcA"
  SRCB = "srcB"
  DST = "dst"


_UNCOMPRESSED = 0x10
_DESC_DIMS = 0x00040001
_SEC1_X = 0x01000000
_FACE_DIMS = (0x01000100, 0x00800080, 0x00400040, 0x00200020, 0x00100010)
_TILEIZE_BIT = 1 << 9
_HALOIZE_BIT = 1 << 8
_UNPACK_TO_DST_BIT = 1 << 11
_DISABLE_ZERO_COMPRESS_BIT = 1


@dataclass(frozen=True)
class UnpackContext:
  source_addr: int
  input_format: int
  output_format: int
  target: UnpackTarget
  unpacker: int
  tileize: bool = False
  haloize: bool = False
  zero_compression: bool = False
  destination_addr: int = 0


def output_format(fmt: int) -> int:
  """Return the SrcA/SrcB format implied by an unpacked tile."""
  return fmt if fmt in (UnpackFormat.F32, UnpackFormat.F16) else UnpackFormat.BF16


def tile_descriptor(fmt: int) -> int:
  """Encode the Blackhole tile descriptor's format/validity byte."""
  return int(fmt) if fmt == UnpackFormat.BFP4 else int(fmt) | _UNCOMPRESSED


class Unpack:
  """Stateful TRISC0 configuration object.

  ``configure`` is pure with respect to the builder: it returns the register
  image and updates the object only after validation. This makes accidental
  cross-kernel state sharing visible and gives the lowering layer a stable
  diff boundary.
  """
  pipe = 0

  def __init__(self, kernel=None, *, state: TensixState | None = None):
    self.k = kernel
    self.tensix = Tensix(kernel, self.pipe, state) if kernel is not None else None
    self.state = UnpackState()
    self.contexts: dict[int, UnpackContext] = {}
    self.initialized = False
    self._mop_cfg: MopCfg | None = None

  @property
  def mop(self):
    if self.tensix is None: raise RuntimeError("unpack is not attached to a kernel")
    return self.tensix.mop

  def configure(self, fmt: int = UnpackFormat.BF16, *, fp32_dest: bool = False):
    fmt = int(fmt)
    if fmt not in {int(x) for x in UnpackFormat}:
      raise ValueError(f"unsupported Blackhole unpack format: {fmt}")
    next_state = UnpackState(
      src_format=fmt, dst_format=output_format(fmt), fp32_dest=bool(fp32_dest),
      cfg_context=0, srca_set=4, tile_descriptor=tile_descriptor(fmt),
      tile_descriptor_1=_DESC_DIMS,
      sec0_reg2=0x20 | output_format(fmt), sec1_reg2=0x20 | output_format(fmt),
    )
    self.state = next_state
    if self.tensix is not None:
      for register, value in self.register_image().items():
        self.tensix.write_cfg(register, value)
    return self

  def configure_input(self, *, format=UnpackFormat.BF16, tile_bytes: int | None = None,
                      zero_compression: bool | None = None, fp32_dest: bool = False):
    """Configure the unpack input path using intent-level arguments."""
    if tile_bytes is not None and (type(tile_bytes) is not int or tile_bytes <= 0 or tile_bytes % 16):
      raise ValueError("unpack tile_bytes must be a positive multiple of 16")
    return self.configure(format, fp32_dest=fp32_dest)

  def init(self, *, tile_bytes: int, format=UnpackFormat.BF16, mop_cfg=None,
           fp32_dest: bool = False):
    """Initialize invariant unpacker state before CB moves."""
    self.configure_input(format=format, tile_bytes=tile_bytes, fp32_dest=fp32_dest)
    if self.tensix is not None:
      self.tensix.set_thread_cfg(5, 4)
      self._mop_cfg = UNPACK_MOP_CFG if mop_cfg is None else mop_cfg
      self.tensix.mop.configure(self._mop_cfg)
    else:
      self._mop_cfg = UNPACK_MOP_CFG if mop_cfg is None else mop_cfg
    self.initialized = True
    return self

  @staticmethod
  def _cb_info(cb):
    try:
      addr, dtype = cb.addr, cb.dtype
    except AttributeError as exc:
      raise TypeError("source CB must expose addr and dtype") from exc
    return int(addr), int(dtype)

  def configure_context(self, context: int, *, source_cb, target: UnpackTarget,
                        unpacker: int = 0, output_format=None, tileize: bool = False,
                        haloize: bool = False, zero_compression: bool = False,
                        destination_addr: int = 0):
    """Describe one CB-to-register/Dst unpack context."""
    if context not in (0, 1): raise ValueError("unpack context must be 0 or 1")
    if unpacker not in (0, 1): raise ValueError("unpacker must be 0 or 1")
    target = target if isinstance(target, UnpackTarget) else UnpackTarget(target)
    if target is UnpackTarget.DST and unpacker != 0:
      raise ValueError("only unpacker 0 can target Dst")
    if tileize and unpacker != 0:
      raise ValueError("TTSIM does not support tileize on unpacker 1")
    if haloize and target is UnpackTarget.DST:
      raise ValueError("unpack-to-Dst cannot use haloize")
    source_addr, input_format = self._cb_info(source_cb)
    output_format = input_format if output_format is None else int(output_format)
    if input_format not in {int(x) for x in UnpackFormat} or output_format not in {int(x) for x in UnpackFormat}:
      raise ValueError("unsupported unpack format")
    spec = UnpackContext(source_addr, input_format, output_format, target, unpacker,
      tileize, haloize, zero_compression, int(destination_addr))
    self.contexts[context] = spec
    if self.tensix is not None:
      self._lower_context(context, spec)
    return self

  def _lower_context(self, context: int, spec: UnpackContext):
    # CFG contexts are physical shared state, but the semantic interpretation
    # of the loaded tile remains in this UnpackContext.  Track the selected raw
    # context so diffing does not accidentally compare ctx0 and ctx1 together.
    self.tensix.state.set_context(self.pipe, context)
    base = Cfg.THCON_SEC0_REG3_Base_address if spec.unpacker == 0 else Cfg.THCON_SEC1_REG3_Base_address
    base_ctx = Cfg.THCON_SEC0_REG3_Base_cntx1_address if spec.unpacker == 0 else Cfg.THCON_SEC1_REG3_Base_cntx1_address
    offset = Cfg.THCON_SEC0_REG7_Offset_address if spec.unpacker == 0 else Cfg.THCON_SEC1_REG7_Offset_address
    offset_ctx = Cfg.THCON_SEC0_REG7_Offset_cntx1_address if spec.unpacker == 0 else Cfg.THCON_SEC1_REG7_Offset_cntx1_address
    reg2 = (self.state.sec0_reg2 if spec.unpacker == 0 else self.state.sec1_reg2)
    reg2 = (reg2 & ~(_TILEIZE_BIT | _HALOIZE_BIT | _UNPACK_TO_DST_BIT))
    reg2 |= _TILEIZE_BIT if spec.tileize else 0
    reg2 |= _HALOIZE_BIT if spec.haloize else 0
    reg2 |= _UNPACK_TO_DST_BIT if spec.target is UnpackTarget.DST else 0
    if spec.zero_compression: reg2 |= _DISABLE_ZERO_COMPRESS_BIT
    self.tensix.write_cfg(base if context == 0 else base_ctx, spec.source_addr)
    self.tensix.write_cfg(offset if context == 0 else offset_ctx, 0)
    self.tensix.write_cfg(Cfg.THCON_SEC0_REG2 if spec.unpacker == 0 else Cfg.THCON_SEC1_REG2, reg2)
    if spec.unpacker == 0:
      self.tensix.write_cfg(Cfg.THCON_SEC0_REG5_Dest_cntx if context == 0 else Cfg.THCON_SEC0_REG5_Dest_cntx1,
        spec.destination_addr)

  def select_context(self, context: int):
    if context not in self.contexts: raise ValueError(f"unpack context {context} is not configured")
    if self.tensix is not None:
      # The low/high byte selects the override context for unpacker 0/1.
      spec = self.contexts[context]
      value = context if spec.unpacker == 0 else context << 8
      self.tensix.set_thread_cfg(41, value)
    return self

  def move(self, source_cb, *, target: UnpackTarget, context: int = 0,
           unpacker: int | None = None, output_format=None,
           addr_mode: int = 1, srcb_bcast: bool = False,
           use_mop: bool = False, mop_cfg: MopCfg | None = None,
           repeat: int = 1, serialize_dst: bool | None = None):
    """Move one configured CB tile to SrcA, SrcB, or Dst."""
    if not self.initialized: raise RuntimeError("unpack.init() is required before move()")
    if context not in self.contexts: raise ValueError(f"unpack context {context} is not configured")
    spec = self.contexts[context]
    target = target if isinstance(target, UnpackTarget) else UnpackTarget(target)
    if spec.target is not target: raise ValueError("move target differs from configured context")
    if unpacker is not None and unpacker != spec.unpacker: raise ValueError("move unpacker differs from configured context")
    if output_format is not None and int(output_format) != spec.output_format:
      raise ValueError("move output format differs from configured context")
    if not 0 <= addr_mode <= 0xFF or type(repeat) is not int or repeat < 1:
      raise ValueError("invalid unpack address mode or repeat count")
    if srcb_bcast and target is not UnpackTarget.SRCB:
      raise ValueError("srcb_bcast is only valid for SrcB")
    if serialize_dst is None:
      serialize_dst = target is UnpackTarget.DST
    self.select_context(context)
    if self.tensix is not None:
      block = 1 if spec.target is UnpackTarget.SRCB else 0
      set_valid = 0 if spec.target is UnpackTarget.DST else 1
      if use_mop:
        cfg = mop_cfg or self._mop_cfg
        if cfg is None: raise RuntimeError("unpack MOP is not configured")
        self.tensix.mop.configure(cfg)
        self.tensix.mop.run(repeat=repeat, mop_type=1)
      else:
        for _ in range(4 if spec.target is UnpackTarget.DST else repeat):
          self.tensix.push(self.k.tensix_word(
            "TTUNPACR", block, addr_mode, 0, 0, 0, 1, set_valid,
            int(srcb_bcast), 0, 0, 0, 0, 1,
          ))
          # TTSIM and the working RMSNorm kernel both require a scoreboard
          # drain between direct-to-Dst faces; without it only the final face
          # is observable.  It is not needed for SrcA/SrcB.
          if serialize_dst and spec.target is UnpackTarget.DST:
            self.tensix.push(self.k.tensix_word(
              "TTSTALLWAIT", int(TensixStall.UNPACK), int(TensixWait.UNPACK0)))
    return self

  def to_src_a(self, source_cb, *, context: int = 0, **kwargs):
    return self.move(source_cb, target=UnpackTarget.SRCA, context=context, **kwargs)

  def to_src_b(self, source_cb, *, context: int = 0, **kwargs):
    return self.move(source_cb, target=UnpackTarget.SRCB, context=context, **kwargs)

  def to_dst(self, source_cb, *, context: int = 0, **kwargs):
    return self.move(source_cb, target=UnpackTarget.DST, context=context, **kwargs)

  def wait(self):
    if self.tensix is not None:
      self.tensix.push(self.k.tensix_word("TTSTALLWAIT", 0x008, 0x002))
    return self

  def configure_address_counters(self, *, unpacker: int = 0,
                                 x_start: int = 0, x_end: int = 255,
                                 z_start: int = 0, z_end: int = 0,
                                 z_stride: int | None = None):
    """Configure the ADC ranges used by subsequent unpack instructions."""
    if unpacker not in (0, 1): raise ValueError("unpacker must be 0 or 1")
    if not 0 <= x_start <= x_end <= 1023 or not 0 <= z_start <= z_end <= 7:
      raise ValueError("invalid unpack address-counter range")
    if self.tensix is None: return self
    mask = 1 if unpacker == 0 else 2
    self.tensix.push(self.k.tensix_word("TTSETADCXX", mask, x_end, x_start))
    self.tensix.push(self.k.tensix_word("TTSETADCZW", 3, z_end, z_end, z_start, z_start, 0xF))
    if z_stride is not None:
      if type(z_stride) is not int or z_stride < 0: raise ValueError("z_stride must be non-negative")
      reg = Cfg.UNP0_ADDR_CTRL_ZW_REG_1 if unpacker == 0 else Cfg.UNP1_ADDR_CTRL_ZW_REG_1
      self.tensix.write_cfg(reg, z_stride)
    return self

  def load_replay(self, words):
    if self.tensix is not None: self.tensix.mop.load_replay(words)
    return self

  def run(self, *, repeat: int = 1, mop_cfg: MopCfg | None = None):
    if repeat < 1: raise ValueError("repeat must be positive")
    if self.tensix is not None:
      cfg = mop_cfg or self._mop_cfg
      if cfg is None: raise RuntimeError("unpack MOP is not configured")
      self.tensix.mop.configure(cfg)
      self.tensix.mop.run(repeat=repeat)
    return self

  def set_format(self, format):
    return self.configure(format, fp32_dest=self.state.fp32_dest)

  def set_conversion_format(self, src_format, dst_format):
    src_format, dst_format = int(src_format), int(dst_format)
    if src_format not in {int(x) for x in UnpackFormat} or dst_format not in {int(x) for x in UnpackFormat}:
      raise ValueError("unsupported unpack conversion format")
    self.state = UnpackState(
      src_format=src_format, dst_format=output_format(dst_format), fp32_dest=self.state.fp32_dest,
      cfg_context=self.state.cfg_context, srca_set=self.state.srca_set,
      tile_descriptor=tile_descriptor(src_format), tile_descriptor_1=_DESC_DIMS,
      sec0_reg2=0x20 | output_format(dst_format), sec1_reg2=0x20 | output_format(dst_format),
    )
    if self.tensix is not None:
      for register, value in self.register_image().items(): self.tensix.write_cfg(register, value)
    return self

  def register_image(self):
    """Return the MMIO words needed for the stable tile-format state."""
    s = self.state
    return {
      Cfg.THCON_SEC0_REG0_TileDescriptor: s.tile_descriptor,
      Cfg.THCON_SEC0_REG0_TileDescriptor_1: s.tile_descriptor_1,
      Cfg.THCON_SEC1_REG0_TileDescriptor: s.tile_descriptor | _SEC1_X,
      Cfg.THCON_SEC1_REG0_TileDescriptor_1: s.tile_descriptor_1,
      Cfg.THCON_SEC0_REG2: s.sec0_reg2,
      Cfg.THCON_SEC1_REG2: s.sec1_reg2,
    }

  @staticmethod
  def face_dimension_words():
    return _FACE_DIMS
