from __future__ import annotations
from enum import IntEnum
from firmware.consts import TensixMMIO
from ttko.isa import R, Tensix as TT
from ttko import Dst, DType
from ttko.cb import CB
from ttko.mop import LoopTemplate, Mop
from ttko.sync import Sem, SemWait, Stall, Wait, sem_get, sem_wait, stall, sync
from ttko.registers import Cfg, DType, GprPack, Sem, SemWait, Stall, TensixMMIO, ThreadCfg, Wait, TriscLocalMem as TLM


class _Cfg(IntEnum):
  ALU_FORMAT = TensixMMIO.CFG_BASE + 4; ACCUMULATION = TensixMMIO.CFG_BASE + 8
  ADDRESS_XY = TensixMMIO.CFG_BASE + 0x30; ADDRESS_ZW = TensixMMIO.CFG_BASE + 0x34
  DESTINATION_READ = TensixMMIO.CFG_BASE + 0x48
  TILE_ROW_MAPPING = TensixMMIO.CFG_BASE + 0x50
  TILE_ROW_MAPPING1 = TensixMMIO.CFG_BASE + 0x54
  EDGE = TensixMMIO.CFG_BASE + 0x60; EDGE1 = TensixMMIO.CFG_BASE + 0x64
  COUNTERS = TensixMMIO.CFG_BASE + 0x70
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
    self.k.write(int(register), value)
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
      k.or_(instruction, instruction, base); k.write(TensixMMIO.INSTRN_BUF_BASE, instruction)

  @staticmethod
  def _strides(fmt):
    size = fmt.itemsize
    return 16 * size << 16, 256 * size | 1024 * size << 16

  def _configure(self, output_cb, fp32_dest, scalar):
    dst, src = output_cb.dtype, DType.F32 if fp32_dest else output_cb.dtype
    fp8 = dst.is_fp8
    src = DType.F16 if fp8 else src
    self._set_thread_cfg(0, 0)
    self._issue(TT.TTRMWCIB2(0x80, 0x80 if dst is DType.FP8 else 0, 71))
    self._rmw_cfg_byte(_Cfg.ALU_FORMAT, 3, 0x1E, src << 1)
    for byte, mask in enumerate((0xFC, 0xFF, 0x3F)):
      self._rmw_cfg_byte(_Cfg.ACCUMULATION, byte, mask, 0)
    xy, zw = self._strides(src)
    edge = 1 << 17 if scalar else 0xFFFF
    for reg, value in (
      (_Cfg.SECTION_SIZES, 0 if fp8 else 0x00040000), (_Cfg.DATA_FORMAT, 1 | dst.hw_format << 4 | src << 8),
      (_Cfg.DESTINATION_READ, int(fp32_dest or src == DType.F32) | (8 if fp8 else 0)), (_Cfg.ADDRESS_XY, xy),
      (_Cfg.ADDRESS_ZW, zw), (_Cfg.COUNTERS, 0x1000),
      (_Cfg.EDGE, edge), (_Cfg.EDGE1, int(scalar)),
      (_Cfg.TILE_ROW_MAPPING, 0), (_Cfg.TILE_ROW_MAPPING1, int(scalar)),
    ): self._write_cfg(reg, value)
    self.k.write(TensixMMIO.REGFILE_BASE + 16 * 4, output_cb.tile_size >> 4)
    self.k.write(TensixMMIO.REGFILE_BASE + 52 * 4, 0x40000)
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
        self.k.write(TensixMMIO.INSTRN_BUF_BASE, instruction)
      else: self._issue(TT.TTSETADC(4, 0, 3, source))
      self._set_dma_reg16(24, address)
      self.k.srli(high, address, 16); self.k.li(valid, 0x8000); self.k.or_(valid, valid, high)
      self._set_dma_reg16(25, valid); stall(self.k, Stall.CFG, Wait.THCON | Wait.PACK0)
      address = (int(_Cfg.L1_DESTINATION) - TensixMMIO.CFG_BASE) >> 2
      self._issue(TT.TTWRCFG(12, 0, address))
      self._set_dma_reg16(25, high); self._issue(TT.TTDMANOP())

  def _move_acquired(self, output_cb, tile, scalar, *, configure=True):
    tile = self.dst.check(tile)
    CB.reserve_back(self.k, output_cb)
    if configure: self._configure(output_cb, self.dst.fp32, scalar)
    self._destination(tile, output_cb)
    self._issue(TT.TTSETADCXX(4, 15, 0)); self._issue(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
    self._write_cfg(_Cfg.DESTINATION_OFFSET, 0)
    stall(self.k, Stall.CFG, Wait.PACK0); self._mop.run()
    stall(self.k, Stall.SYNC, Wait.PACK0); sync(self.k)
    CB.push_back(self.k, output_cb)
    return self

  def _release_dst(self):
    # Full-Dst handoff: packing is complete, so invalidate Dst before returning
    # ownership to math. FPU assignment writes define it again before SFPU reads.
    self._issue(TT.TTZEROACC(3, int(self.dst.fp32), 0, 1, 0))
    sem_get(self.k, Sem.MATH_PACK)
    return self

  def _move(self, output_cb, tile, scalar):
    sem_wait(self.k, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
    self._move_acquired(output_cb, tile, scalar)
    self._release_dst()
    return self

  def move(self, output_cb, *, tile):
    return self._move(output_cb, tile, False)

  def move_scalar(self, output_cb, *, tile):
    return self._move(output_cb, tile, True)

  def move_tiles(self, output_cb, *, tiles):
    tiles = tuple(tiles)
    if not tiles: raise ValueError("move_tiles requires at least one Dst tile")
    for tile in tiles: self.dst.check(tile)
    sem_wait(self.k, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
    self._configure(output_cb, self.dst.fp32, False)
    for tile in tiles:
      self._move_acquired(output_cb, tile, False, configure=False)
    self._release_dst()
    return self


_PACK_DISABLE_ZERO_COMPRESS = 0x1

def _pack_data_format(dtype: DType, fp8: bool) -> int:
  return _PACK_DISABLE_ZERO_COMPRESS | (dtype.value << 4) | ((1 if fp8 else dtype.value) << 8)

_EXP_SECTION_SIZE = 0x00040000

_THCON_SEC0_REG1_1_RESERVED = 0x00000000

_PACK_COUNTERS = 0x00001000

_PCK_EDGE = 0x0000FFFF

_DEST_OFFSET_HI = 512

_TILE_FACE_R_DIM = 16

_TILE_NUM_FACES = 4

_ADDR_MOD_PACK = (260, 10272, 4384)

class BlockedPack:
  """Blocked matmul packing; fp32 preserves FP32 Dst and L1 partials."""

  def __init__(self, kernel, *, fp8=False, fp32=False):
    self.k, self.fp8, self.fp32 = kernel, fp8, fp32

  def _state_formats(self, k, dtype: DType):
    k.write_repeated_bytes(TLM.TRISC2_PACK_TILE_FACE_R_DIM, _TILE_FACE_R_DIM, 8)
    k.write_repeated_bytes(TLM.TRISC2_PACK_TILE_NUM_FACES, _TILE_NUM_FACES, 8)
    k.write32(TLM.TRISC2_PACK_PARTIAL_FACE_SEC1, 0)
    k.write_repeated_bytes(TLM.TRISC2_PACK_SRC_FORMAT, dtype.value, 16)
    k.write_repeated_bytes(TLM.TRISC2_PACK_DST_FORMAT, dtype.value, 16)

  def _dest_addr_dmaregs(self, k):
    # SETDMAREG block driving the THCON dest-addr config (re-issued after MOP).
    k.emit(TT.TTSETDMAREG(0, 0, 0, 56))
    k.emit(TT.TTSETDMAREG(0, 64 if self.fp32 else 32, 0, 57))
    k.emit(TT.TTSETDMAREG(0, 1024 if self.fp32 else 512, 0, 58))
    k.emit(TT.TTSETDMAREG(0, 4096 if self.fp32 else 2048, 0, 59))
    k.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.THCON))
    k.emit(TT.TTWRCFG(28, 0, 12))
    k.emit(TT.TTWRCFG(29, 0, 13))
    k.emit(TT.TTNOP())
    k.emit(TT.TTNOP())

  def _alu_acc_rmw(self, k):
    k.emit(TT.TTATGETM(0))
    for inst in (
      TT.TTRMWCIB3(Mask=0x1E, Data=0 if self.fp32 else 0x02 if self.fp8 else 0x0A, CfgRegAddr=Cfg.ALU.addr32),
      TT.TTRMWCIB0(Mask=0xFC, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
      TT.TTRMWCIB1(Mask=0xFF, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
      TT.TTRMWCIB2(Mask=0x3F, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
    ):
      k.push_tensix(inst)
    k.emit(TT.TTATRELM(0))

  def _pack_cfg(self, k, dtype: DType, out_cb: int):
    k.write32(Cfg.THCON_SEC0_REG1, _EXP_SECTION_SIZE)
    k.write32(Cfg.THCON_SEC0_REG1_1, _pack_data_format(dtype, self.fp8 and not self.fp32))
    k.write32(Cfg.PCK_DEST_RD_CTRL, int(self.fp32))
    for off in range(4):
      k.write32(GprPack.DEST_OFFSET_LO + off * 4, 0)
      k.write32(GprPack.DEST_OFFSET_HI + off * 4, 256 if self.fp32 else _DEST_OFFSET_HI)
    k.write32(GprPack.EXP0_SEC_SIZE_BFP, _EXP_SECTION_SIZE)
    for reg in (Cfg.PACK_COUNTERS_SEC0, Cfg.PACK_COUNTERS_SEC1,
                Cfg.PACK_COUNTERS_SEC2, Cfg.PACK_COUNTERS_SEC3):
      k.write32(reg, _PACK_COUNTERS)
    k.write32(Cfg.PCK_EDGE, _PCK_EDGE)
    k.write32(Cfg.TILE_ROW_SET_MAPPING_0, 0)
    # Packer tile/page size comes from TRISC local CB state (16B units).
    k.cb_iface(k.data["cb_interface"], out_cb, out=R.T6)
    k.lw(R.T1, R.T6, 8)
    k.write32(GprPack.TILE_HEADER, R.T1)
    k.write32(GprPack.TILE_HEADER_1, 0)
    k.write32(GprPack.TILE_HEADER_2, 0)
    k.write32(GprPack.TILE_HEADER_3, 0)

  def init(self, *, dtype: DType = DType.BF16, out_cb: int, mop_cfg):
    """Configure the packer: local format state, ALU-acc RMW, pack cfg regs and
    tile header for ``dtype``/``out_cb``, the pack MOP template, and the dest /
    output address setup. """
    k = self.k

    if self.fp32 and dtype != DType.F32:
      raise ValueError("blocked FP32 packing currently requires FP32 output")
    self._state_formats(k, dtype)
    self._dest_addr_dmaregs(k)
    self._alu_acc_rmw(k)
    self._pack_cfg(k, dtype, out_cb)

    k.emit(TT.TTSETADCXX(4, 15, 0))
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC0, _ADDR_MOD_PACK[0])
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC1, _ADDR_MOD_PACK[1])
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC2, _ADDR_MOD_PACK[2])

    k.mop_sync(2, tmp=R.T1)
    k.write_mop_cfg(mop_cfg, 2)

    self._dest_addr_dmaregs(k)
    k.emit(TT.TTSETADCXX(4, 15, 0))
    k.write32(k.data["dest_offset_id"], 0)

    # Output addr config setup.
    k.emit(TT.TTSTALLWAIT(Stall.TDMA | Stall.THCON, Wait.PACK0))
    k.emit(TT.TTSETDMAREG(0, 0, 0, 16))
    k.emit(TT.TTSETDMAREG(0, 0, 0, 17))
    k.emit(TT.TTSETDMAREG(0, 512, 0, 18))
    k.emit(TT.TTSETDMAREG(0, 0, 0, 19))
    k.emit(TT.TTSTALLWAIT(Stall.CFG, Wait.THCON))
    k.emit(TT.TTWRCFG(4, 1, 180))
    k.emit(TT.TTDMANOP())
    k.emit(TT.TTDMANOP())

    k.emit(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xB))
    k.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 0xF))
    return k
