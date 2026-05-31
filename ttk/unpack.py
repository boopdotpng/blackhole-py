from __future__ import annotations

from dsl import (
  TTATGETM, TTATRELM, TTRMWCIB0, TTRMWCIB1, TTRMWCIB2, TTRMWCIB3,
  TTSETADCXX, TTSETADCXY, TTSETADCZW, TTZEROSRC,
)
from program import Dtype
from ttk.mailbox import TriscLocalMem as TLM
from ttk.tensix import Cfg, GprUnpack, TensixRegs, ThreadCfg

# --- Tile-descriptor encoding (ttsim data/bh/tensix_regs.json, cfg word 64) ---
# The low byte of THCON_SEC*_REG0_TileDescriptor packs the source data format:
#   bits[3:0] = in_data_format (== Dtype.value), bit[4] = uncompressed.
# So Float16_b (value 5) uncompressed -> 0x15. Everything above the low byte
# (x/y/z dims) is still opaque here and kept as named layout constants until we
# decode the full descriptor struct.
_DESC_UNCOMPRESSED = 0x10
_DESC_SEC1_X = 0x01000000      # SEC1 carries the tile x-origin in the high byte
_DESC_DIMS = 0x00040001        # REG0_1: blobs/dims (z_dim=4, y_dim=1)
_DESC_REG2 = 0x00000025        # REG2: secondary format/stride descriptor
_DESC_REG2_1 = 0x000F000F      # REG2_1: x/y counts (15,15)
_DEST_CNTX = 0x00400040        # REG5: dest context base/stride
_TILE_X_DIM = 0x01000100       # REG5: tile x dim (256 | 256<<16)

# p_gpr_unpack face-dimension table: face NxM size packed as (N*M)|(N*M)<<16,
# halving 16x16=256 down to 1x16=16. Independent of dtype.
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

  def _tile_descriptor(self, k, dtype: Dtype):
    desc = dtype.value | _DESC_UNCOMPRESSED
    k.write32(Cfg.THCON_SEC0_REG0_TileDescriptor, desc)
    k.write32(Cfg.THCON_SEC0_REG0_TileDescriptor_1, _DESC_DIMS)
    k.write32(Cfg.THCON_SEC1_REG0_TileDescriptor, desc | _DESC_SEC1_X)
    k.write32(Cfg.THCON_SEC1_REG0_TileDescriptor_1, _DESC_DIMS)
    k.write32(Cfg.THCON_SEC0_REG2, _DESC_REG2)
    k.write32(Cfg.THCON_SEC0_REG2_1, _DESC_REG2_1)
    k.write32(Cfg.THCON_SEC1_REG2, _DESC_REG2)
    k.write32(Cfg.THCON_SEC1_REG2_1, _DESC_REG2_1)

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
