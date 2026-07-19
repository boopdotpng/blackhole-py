from enum import IntEnum

from isa import R, Tensix as TT
from program import DType
from ttk.cb import CB
from ttk.mop import LoopTemplate
from ttk.tensix import (
  CFG_BASE, TensixPipe, TensixRegs, TensixSem, TensixSemWait, TensixStall,
  TensixWait, cfg_addr32,
)

class _Cfg(IntEnum):
  ALU_FORMAT = CFG_BASE + 4; ACCUMULATION = CFG_BASE + 8
  ADDRESS_XY = CFG_BASE + 0x30; ADDRESS_ZW = CFG_BASE + 0x34
  DESTINATION_READ = CFG_BASE + 0x48; TILE_ROW_MAPPING = CFG_BASE + 0x50
  EDGE = CFG_BASE + 0x60; COUNTERS = CFG_BASE + 0x70
  SECTION_SIZES = CFG_BASE + 0x110; L1_DESTINATION = CFG_BASE + 0x114
  DATA_FORMAT = CFG_BASE + 0x118
  DESTINATION_OFFSET = CFG_BASE + 0x2D0

_ADDRESS_MODIFIER = 37

def _pack(addr_mode=0, last=False):
  return TT.TTPACR(0, 0, 0, addr_mode, 0, 0, 0, 0, 0, 0, 0, int(last))

_MOP = LoopTemplate(
  outer=4, inner=4, loop=_pack(),
  last=_pack(1, True), outer_last=_pack(2),
)

class Pack:
  def __init__(self, kernel): self.k, self.tensix = kernel, TensixPipe(kernel, 2)

  def _set_dma_reg16(self, half_register, value):
    k = self.k
    with k.scope():
      instruction, mask, base = k.reg(3, exclude=value)
      k.slli(instruction, value, 8)
      k.li(mask, 0x00FFFF00); k.and_(instruction, instruction, mask)
      k.li(base, TT.TTSETDMAREG(0, 0, 0, half_register))
      k.or_(instruction, instruction, base); k.write32(TensixRegs.INSTRN_BUF_BASE, instruction)

  @staticmethod
  def _strides(fmt):
    size = fmt.itemsize
    return 16 * size << 16, 256 * size | 1024 * size << 16

  def _configure(self, output_cb, fp32_dest):
    dst, src, t = output_cb.dtype, DType.F32 if fp32_dest else output_cb.dtype, self.tensix
    t.select_config()
    t.rmw_cfg_byte(_Cfg.ALU_FORMAT, 3, 0x1E, src << 1)
    for byte, mask in enumerate((0xFC, 0xFF, 0x3F)):
      t.rmw_cfg_byte(_Cfg.ACCUMULATION, byte, mask, 0)
    xy, zw = self._strides(src)
    for reg, value in (
      (_Cfg.SECTION_SIZES, 0x00040000), (_Cfg.DATA_FORMAT, 1 | dst << 4 | src << 8),
      (_Cfg.DESTINATION_READ, int(src == DType.F32)), (_Cfg.ADDRESS_XY, xy),
      (_Cfg.ADDRESS_ZW, zw), (_Cfg.COUNTERS, 0x1000),
      (_Cfg.EDGE, 0xFFFF), (_Cfg.TILE_ROW_MAPPING, 0),
    ): t.write_cfg(reg, value)
    self.k.write32(TensixRegs.REGFILE_BASE + 16 * 4, output_cb.page_size >> 4)
    self.k.write32(TensixRegs.REGFILE_BASE + 52 * 4, 0x40000)
    for section, value in enumerate((0x0104, 0x2820, 0x1120)):
      t.set_thread_cfg(_ADDRESS_MODIFIER + section, value)
    t.issue(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xB)); t.issue(TT.TTSETADCZW(4, 0, 0, 0, 0, 0xF))
    t.mop.configure(_MOP); t.sync()

  def _destination(self, source, output_cb):
    t = self.tensix
    with self.k.scope():
      address, high, valid = self.k.reg(3)
      CB.get_write_ptr(self.k, output_cb, address)
      self.k.srli(address, address, 4); self.k.addi(address, address, -1)
      if isinstance(source, R):
        instruction = self.k.reg(exclude=source)
        self.k.li(instruction, TT.TTSETADC(4, 0, 3, 0)); self.k.or_(instruction, instruction, source)
        self.k.write32(TensixRegs.INSTRN_BUF_BASE, instruction)
      else: t.issue(TT.TTSETADC(4, 0, 3, source))
      self._set_dma_reg16(24, address)
      self.k.srli(high, address, 16); self.k.li(valid, 0x8000); self.k.or_(valid, valid, high)
      self._set_dma_reg16(25, valid); t.stall(TensixStall.CFG, TensixWait.THCON | TensixWait.PACK0)
      t.issue(TT.TTWRCFG(12, 0, cfg_addr32(_Cfg.L1_DESTINATION)))
      self._set_dma_reg16(25, high); t.issue(TT.TTDMANOP())

  def move(self, source, output_cb, fp32_dest=False):
    t = self.tensix
    t.semaphore_wait(TensixSem.MATH_PACK, TensixSemWait.STALL_ON_ZERO, stall=TensixStall.TDMA)
    CB.reserve_back(self.k, output_cb)
    self._configure(output_cb, fp32_dest); self._destination(source, output_cb)
    t.issue(TT.TTSETADCXX(4, 15, 0)); t.issue(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
    t.write_cfg(_Cfg.DESTINATION_OFFSET, 0)
    t.stall(TensixStall.CFG, TensixWait.PACK0); t.mop.run()
    t.stall(TensixStall.SYNC, TensixWait.PACK0); t.sync()
    CB.push_back(self.k, output_cb); t.semaphore_get(TensixSem.MATH_PACK)
    return self
