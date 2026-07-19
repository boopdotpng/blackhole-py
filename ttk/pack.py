from enum import IntEnum

from fw.consts import TensixMMIO
from isa import R, Tensix as TT
from program import DType
from ttk.cb import CB
from ttk.dst import Dst
from ttk.mop import LoopTemplate
from ttk.mop import Mop
from ttk.sync import Sem, SemWait, Stall, Wait, sem_get, sem_wait, stall, sync

class _Cfg(IntEnum):
  ALU_FORMAT = TensixMMIO.CFG_BASE + 4; ACCUMULATION = TensixMMIO.CFG_BASE + 8
  ADDRESS_XY = TensixMMIO.CFG_BASE + 0x30; ADDRESS_ZW = TensixMMIO.CFG_BASE + 0x34
  DESTINATION_READ = TensixMMIO.CFG_BASE + 0x48; TILE_ROW_MAPPING = TensixMMIO.CFG_BASE + 0x50
  EDGE = TensixMMIO.CFG_BASE + 0x60; COUNTERS = TensixMMIO.CFG_BASE + 0x70
  SECTION_SIZES = TensixMMIO.CFG_BASE + 0x110; L1_DESTINATION = TensixMMIO.CFG_BASE + 0x114
  DATA_FORMAT = TensixMMIO.CFG_BASE + 0x118
  DESTINATION_OFFSET = TensixMMIO.CFG_BASE + 0x2D0

_ADDRESS_MODIFIER = 37

def _pack(addr_mode=0, last=False):
  return TT.TTPACR(0, 0, 0, addr_mode, 0, 0, 0, 0, 0, 0, 0, int(last))

_MOP = LoopTemplate(
  outer=4, inner=4, loop=_pack(),
  last=_pack(1, True), outer_last=_pack(2),
)

class Pack:
  def __init__(self, kernel, dst: Dst):
    self.k, self.dst, self._mop = kernel, dst, Mop(kernel, 2)

  def _issue(self, word):
    self.k.emit(word)
    return self

  def _write_cfg(self, register, value):
    self.k.write32(int(register), value)
    return self

  def _rmw_cfg_byte(self, register, byte, mask, data):
    opcode = (TT.TTRMWCIB0, TT.TTRMWCIB1, TT.TTRMWCIB2, TT.TTRMWCIB3)[byte]
    address = (int(register) - TensixMMIO.CFG_BASE) >> 2
    return self._issue(opcode(mask, data & mask, address))

  def _set_thread_cfg(self, register, value):
    return self._issue(TT.TTSETC16(int(register), int(value)))

  def _set_dma_reg16(self, half_register, value):
    k = self.k
    with k.scope():
      instruction, mask, base = k.reg(3, exclude=value)
      k.slli(instruction, value, 8)
      k.li(mask, 0x00FFFF00); k.and_(instruction, instruction, mask)
      k.li(base, TT.TTSETDMAREG(0, 0, 0, half_register))
      k.or_(instruction, instruction, base); k.write32(TensixMMIO.INSTRN_BUF_BASE, instruction)

  @staticmethod
  def _strides(fmt):
    size = fmt.itemsize
    return 16 * size << 16, 256 * size | 1024 * size << 16

  def _configure(self, output_cb, fp32_dest):
    dst, src = output_cb.dtype, DType.F32 if fp32_dest else output_cb.dtype
    self._set_thread_cfg(0, 0)
    self._rmw_cfg_byte(_Cfg.ALU_FORMAT, 3, 0x1E, src << 1)
    for byte, mask in enumerate((0xFC, 0xFF, 0x3F)):
      self._rmw_cfg_byte(_Cfg.ACCUMULATION, byte, mask, 0)
    xy, zw = self._strides(src)
    for reg, value in (
      (_Cfg.SECTION_SIZES, 0x00040000), (_Cfg.DATA_FORMAT, 1 | dst << 4 | src << 8),
      (_Cfg.DESTINATION_READ, int(src == DType.F32)), (_Cfg.ADDRESS_XY, xy),
      (_Cfg.ADDRESS_ZW, zw), (_Cfg.COUNTERS, 0x1000),
      (_Cfg.EDGE, 0xFFFF), (_Cfg.TILE_ROW_MAPPING, 0),
    ): self._write_cfg(reg, value)
    self.k.write32(TensixMMIO.REGFILE_BASE + 16 * 4, output_cb.page_size >> 4)
    self.k.write32(TensixMMIO.REGFILE_BASE + 52 * 4, 0x40000)
    for section, value in enumerate((0x0104, 0x2820, 0x1120)):
      self._set_thread_cfg(_ADDRESS_MODIFIER + section, value)
    self._issue(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xB))
    self._issue(TT.TTSETADCZW(4, 0, 0, 0, 0, 0xF))
    self._mop.configure(_MOP); sync(self.k)

  def _destination(self, source, output_cb):
    with self.k.scope():
      address, high, valid = self.k.reg(3)
      CB.get_write_ptr(self.k, output_cb, address)
      self.k.srli(address, address, 4); self.k.addi(address, address, -1)
      if isinstance(source, R):
        instruction = self.k.reg(exclude=source)
        self.k.li(instruction, TT.TTSETADC(4, 0, 3, 0)); self.k.or_(instruction, instruction, source)
        self.k.write32(TensixMMIO.INSTRN_BUF_BASE, instruction)
      else: self._issue(TT.TTSETADC(4, 0, 3, source))
      self._set_dma_reg16(24, address)
      self.k.srli(high, address, 16); self.k.li(valid, 0x8000); self.k.or_(valid, valid, high)
      self._set_dma_reg16(25, valid); stall(self.k, Stall.CFG, Wait.THCON | Wait.PACK0)
      address = (int(_Cfg.L1_DESTINATION) - TensixMMIO.CFG_BASE) >> 2
      self._issue(TT.TTWRCFG(12, 0, address))
      self._set_dma_reg16(25, high); self._issue(TT.TTDMANOP())

  def move(self, source, output_cb):
    source = self.dst.check(source)
    sem_wait(self.k, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
    CB.reserve_back(self.k, output_cb)
    self._configure(output_cb, source.fp32); self._destination(source.index, output_cb)
    self._issue(TT.TTSETADCXX(4, 15, 0)); self._issue(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
    self._write_cfg(_Cfg.DESTINATION_OFFSET, 0)
    stall(self.k, Stall.CFG, Wait.PACK0); self._mop.run()
    stall(self.k, Stall.SYNC, Wait.PACK0); sync(self.k)
    # Full-Dst handoff: packing is complete, so invalidate Dst before returning
    # ownership to math. FPU assignment writes define it again before SFPU reads.
    self._issue(TT.TTZEROACC(3, int(source.fp32), 0, 0, 0))
    CB.push_back(self.k, output_cb); sem_get(self.k, Sem.MATH_PACK)
    return self
