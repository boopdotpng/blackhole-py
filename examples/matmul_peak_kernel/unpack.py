from __future__ import annotations
from .isa import *
from .registers import *
from .mailbox import BriscMailbox as BM, NcriscMailbox as NM, TriscLocalMem as TLM
_DESC_UNCOMPRESSED = 0x10

_DESC_SEC1_X = 0x01000000

_DESC_DIMS = 0x00040001

_DESC_REG2 = 0x00000025

_DESC_REG2_1 = 0x000F000F

_DEST_CNTX = 0x00400040

_TILE_X_DIM = 0x01000100

_FACE_DIM_TABLE = {
  GprUnpack.FACE_DIM_16x16: 0x01000100,
  GprUnpack.FACE_DIM_8x16: 0x00800080,
  GprUnpack.FACE_DIM_4x16: 0x00400040,
  GprUnpack.FACE_DIM_2x16: 0x00200020,
  GprUnpack.FACE_DIM_1x16: 0x00100010,
}

class Unpack:
  """Unpack-thread (TRISC0) configuration helpers, bound to a kernel builder.

  Operates *on* a kernel (``self.k``) rather than being mixed into it, so the
  dependency on the asm/Tensix surface is explicit and there is no MRO. Tier-2
  intent ("configure the unpacker for this dtype") composed from Tier-1 ops
  (setc16, push_tensix, write_mop_cfg) and raw asm (write32, emit)."""

  def __init__(self, kernel):
    self.k = kernel

  def input_format(self, dtype, engines=(0, 1)):
    # See tests/movement/unpacker/unpack.py: E4M3 expands into FP16 registers.
    k = self.k
    fp8 = dtype == Dtype.Float8_e4m3
    for engine in engines:
      base = int(Cfg.THCON_SEC0_REG0_TileDescriptor) + engine * 0xc0
      k.write32(base, (dtype.value & 15) | 0x10 | (0x01000000 if engine else 0))
      k.write32(base + 4, _DESC_DIMS)
      k.write32(base + 0x20, 0x20 | (dtype.value & 15))
      k.write32(base + 0x24, 3 if fp8 else _DESC_REG2_1)
      if fp8:
        k.write32(int(Cfg.UNP0_ADDR_CTRL_XY_REG_1) + engine * 8, 2 | 32 << 16)
        k.write32(int(Cfg.UNP0_ADDR_CTRL_ZW_REG_1) + engine * 8, 512)
      k.push_tensix(TTRMWCIB2(0x40, 0x40 if fp8 else 0, 71 + engine * 48))

  def _tile_descriptor(self, k, dtype):
    self.input_format(dtype)

  def _alu_format_rmw(self, k):
    # Masked byte RMW of the ALU config regs under the ATGETM/ATRELM mutex.
    k.emit(TTATGETM(0))
    for inst in (
      TTRMWCIB0(Mask=0xFF, Data=0x00, CfgRegAddr=Cfg.ALU_FORMAT_SPEC_REG.addr32),
      TTRMWCIB1(Mask=0x7F, Data=0x00, CfgRegAddr=Cfg.ALU_FORMAT_SPEC_REG.addr32),
      TTRMWCIB0(Mask=0x07, Data=0x00, CfgRegAddr=Cfg.ALU.addr32),
      TTRMWCIB1(Mask=0x80, Data=0x00, CfgRegAddr=Cfg.ALU.addr32),
      TTRMWCIB2(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.ALU.addr32),
      TTRMWCIB3(Mask=0x60, Data=0x00, CfgRegAddr=Cfg.ALU.addr32),
      TTRMWCIB0(Mask=0x01, Data=0x01, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
    ):
      k.push_tensix(inst)
    k.emit(TTATRELM(0))

  def init(self, *, dtype: Dtype = Dtype.Float16_b, tile_bytes: int, mop_cfg):
    """Configure the unpacker: reset cfg context, program the tile descriptor
    and face-dim table for ``dtype``, then load the unpack MOP template.

    Mirrors the TRISC0 init block of add1 exactly; ``dtype`` drives the tile
    descriptor's data-format field."""
    k = self.k

    k.write32(k.data["cfg_state_id"], 0)
    k.setc16(ThreadCfg.CFG_STATE_ID_StateID, 0)
    k.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, 0)
    k.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)

    k.emit(TTZEROSRC(0, 0, 1, 3))
    k.write32(k.data["cfg_state_id"], 0)
    k.setc16(ThreadCfg.CFG_STATE_ID_StateID, 0)

    k.wait_mmio_low_byte_zero(TensixRegs.PC_UNPACK_SYNC)

    k.emit(TTSETADCXY(3, 0, 0, 0, 0, 0xB))
    k.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    k.write32(Cfg.UNP0_ADDR_CTRL_ZW_REG_1, 0x00000200)
    k.write32(Cfg.UNP1_ADDR_CTRL_ZW_REG_1, 0x00000200)

    self._alu_format_rmw(k)
    self._tile_descriptor(k, dtype)

    k.push_tensix(TTSETADCXX(1, 255, 0))
    k.push_tensix(TTSETADCXX(2, 255, 0))
    k.write32(Cfg.THCON_SEC0_REG5_Dest_cntx, _DEST_CNTX)
    k.write32(Cfg.THCON_SEC0_REG5_Tile_x_dim_cntx, _TILE_X_DIM)
    k.write32(Cfg.UNP0, 0x00000100)

    for addr, value in _FACE_DIM_TABLE.items():
      k.write32(addr, value)

    k.setc16(ThreadCfg.SRCA_SET, 4)
    k.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, 0)
    k.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)

    page_size_16b = tile_bytes >> 4
    for raw in (
      0x45000048 + (page_size_16b << 8),
      0x4500004A + (page_size_16b << 8),
      TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32),
    ):
      k.push_tensix(raw)
    k.emit(TTSETADCXX(1, 255, 0))
    k.push_tensix(TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32))
    k.emit(TTSETADCXX(1, 255, 0))

    k.write_mop_cfg(mop_cfg, 0)
    k.tensix_sync(0)
    return k
