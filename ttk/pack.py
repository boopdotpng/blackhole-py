"""Intent-level TRISC2 packing.

Packing always moves one tile from the shared Dst register file to an output
circular buffer. Format and layout come from the output CB plus shared Dst
state; the raw PACR/MOP/configuration sequence is deliberately hidden.
"""
from dataclasses import dataclass

from ttk.tensix import Cfg, MopCfg, Tensix, TensixState, TensixWait, TensixStall


# This is the hardware pack_tile MOP used by matmul_peak, add1, and RMSNorm.
# It emits one logical 32x32 tile through the four packer faces; it does not
# mean that an entire output CB is copied.
PACK_MOP_CFG = MopCfg.pack_tile()


@dataclass
class PackState:
  source_format: int = 5
  destination_format: int = 5
  fp32_dest: bool = False
  out_cb: object | None = None
  initialized: bool = False
  destination_offset: int = 0


class Pack:
  pipe = 2

  def __init__(self, kernel=None, *, state: TensixState | None = None):
    self.k = kernel
    self.tensix = Tensix(kernel, self.pipe, state) if kernel is not None else None
    self.state = PackState()
    self._mop_cfg = None

  @property
  def mop(self):
    if self.tensix is None: raise RuntimeError("pack is not attached to a kernel")
    return self.tensix.mop

  @staticmethod
  def _cb_info(output_cb):
    try:
      return int(output_cb.addr), int(output_cb.dtype), output_cb
    except AttributeError as exc:
      raise TypeError("output CB must expose addr and dtype") from exc

  @staticmethod
  def _format_word(source: int, destination: int):
    # Disable zero compression, output format in bits 7:4, input in 11:8.
    return 1 | ((destination & 0xF) << 4) | ((source & 0xF) << 8)

  @staticmethod
  def _read_ctrl(source: int, destination: int, fp32_dest: bool):
    # Dst32 requires a full-width Dst read. FP16 additionally needs the
    # Blackhole 10-bit mantissa rounding mode.
    if not fp32_dest:
      return 0
    return 1 | (8 if destination == 1 else 0)

  def _configure_for(self, output_cb, *, source_format: int | None = None,
                     fp32_dest: bool = False):
    _, destination, _ = self._cb_info(output_cb)
    source = destination if source_format is None else int(source_format)
    next_state = PackState(source, destination, bool(fp32_dest), output_cb, True)
    if self.state == next_state:
      return self
    self.state = next_state
    if self.tensix is None:
      return self
    self.tensix.write_cfg(Cfg.THCON_SEC0_REG1, 0x00040000)
    self.tensix.write_cfg(Cfg.THCON_SEC0_REG1_1, self._format_word(source, destination))
    self.tensix.write_cfg(Cfg.PCK_DEST_RD_CTRL, self._read_ctrl(source, destination, fp32_dest))
    self.tensix.write_cfg(Cfg.PCK0_ADDR_CTRL_XY_REG_0, 0x00100000)
    self.tensix.write_cfg(Cfg.PCK0_ADDR_CTRL_ZW_REG_0, 0x01000000)
    self.tensix.write_cfg(Cfg.PACK_COUNTERS_SEC0, 0x1000)
    self.tensix.write_cfg(Cfg.PCK_EDGE, 0xFFFF)
    self.tensix.write_cfg(Cfg.TILE_ROW_SET_MAPPING_0, 0)
    return self

  def init(self, *, output_cb, source_format: int | None = None,
           fp32_dest: bool = False, mop_cfg: MopCfg | None = None,
           destination_offset: int = 0):
    """Internal/lifecycle setup; ordinary code should call :meth:`move`."""
    self._configure_for(output_cb, source_format=source_format, fp32_dest=fp32_dest)
    if type(destination_offset) is not int or destination_offset < 0:
      raise ValueError("destination_offset must be a non-negative Python integer")
    self._mop_cfg = PACK_MOP_CFG if mop_cfg is None else mop_cfg
    if self.tensix is not None: self.tensix.mop.configure(self._mop_cfg)
    return self

  def move(self, output_cb, *, source_format: int | None = None,
           fp32_dest: bool = False, destination_offset: int = 0,
           tile_index: int = 0, mop_cfg: MopCfg | None = None,
           read_interface: int = 0, pack_selection: int = 1,
           x_start: int = 0, x_end: int = 15,
           z_start: int = 0, z_end: int = 0,
           flush: bool = False):
    """Pack one Dst tile into ``output_cb``."""
    self._configure_for(output_cb, source_format=source_format, fp32_dest=fp32_dest)
    if type(destination_offset) is not int or destination_offset < 0:
      raise ValueError("destination_offset must be a non-negative Python integer")
    if type(tile_index) is not int or tile_index < 0:
      raise ValueError("tile_index must be a non-negative Python integer")
    if not 0 <= read_interface <= 15 or pack_selection not in (1, 2, 4):
      raise ValueError("invalid pack interface/selection")
    if not 0 <= x_start <= x_end <= 1023 or not 0 <= z_start <= z_end <= 7:
      raise ValueError("invalid pack address-counter range")
    if self.tensix is None:
      return self
    cfg = PACK_MOP_CFG if mop_cfg is None else mop_cfg
    self.tensix.mop.configure(cfg)
    # The normal tile path uses all four faces.  The public range arguments
    # are still lowered so partial/edge tiles have a first-class path.
    self.tensix.push(self.k.tensix_word("TTSETADCXX", pack_selection, x_end, x_start))
    self.tensix.push(self.k.tensix_word("TTSETADCZW", pack_selection, z_end, z_end, z_start, z_start, 0xF))
    for register in (
      Cfg.DEST_TARGET_REG_CFG_PACK_SEC0,
      Cfg.DEST_TARGET_REG_CFG_PACK_SEC1,
      Cfg.DEST_TARGET_REG_CFG_PACK_SEC2,
      Cfg.DEST_TARGET_REG_CFG_PACK_SEC3,
    ):
      self.tensix.write_cfg(register, destination_offset)
    self.tensix.push(self.k.tensix_word("TTSTALLWAIT", int(TensixStall.CFG), int(TensixWait.PACK0)))
    self.tensix.mop.run(repeat=tile_index + 1, mop_type=1)
    if flush:
      self.tensix.push(self.k.tensix_word("TTPACR", 0, 0, 0, 0, 0, 0, read_interface, 0, 0, 0, 1, 1))
    self.tensix.push(self.k.tensix_word("TTSTALLWAIT", int(TensixStall.SYNC), int(TensixWait.PACK0)))
    return self

  def to_cb(self, output_cb, **kwargs):
    return self.move(output_cb, **kwargs)
