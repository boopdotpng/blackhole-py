from __future__ import annotations

from dsl import (
  TTATGETM, TTATRELM, TTDMANOP, TTNOP, TTRMWCIB0, TTRMWCIB1, TTRMWCIB2,
  TTRMWCIB3, TTSETADCXX, TTSETADCXY, TTSETADCZW, TTSETDMAREG, TTSTALLWAIT,
  TTWRCFG, t1, t6,
)
from program import Dtype
from ttk.mailbox import TriscLocalMem as TLM
from ttk.tensix import Cfg, GprPack, TensixStall, TensixWait, ThreadCfg

# --- Packer data-format word (ttsim data/bh/tensix_regs.json, cfg word 70) ---
# THCON_SEC0_REG1_1 packs the pack in/out formats:
#   bit0 = Disable_zero_compress, bits[7:4] = Out_data_format,
#   bits[11:8] = In_data_format (both == Dtype.value).
# For Float16_b (5): 0x1 | 5<<4 | 5<<8 == 0x551.
_PACK_DISABLE_ZERO_COMPRESS = 0x1


def _pack_data_format(dtype: Dtype) -> int:
  return _PACK_DISABLE_ZERO_COMPRESS | (dtype.value << 4) | (dtype.value << 8)


# Structural pack-config constants (not yet decoded to named fields).
_EXP_SECTION_SIZE = 0x00040000  # REG1 Exp_section_size = 4 (word 68); also GprPack EXP0
_THCON_SEC0_REG1_1_RESERVED = 0x00000000
_PACK_COUNTERS = 0x00001000
_PCK_EDGE = 0x0000FFFF
_DEST_OFFSET_HI = 512
_TILE_FACE_R_DIM = 16
_TILE_NUM_FACES = 4
_ADDR_MOD_PACK = (260, 10272, 4384)  # SEC0/SEC1/SEC2 pack address modes


class Pack:
  """Pack-thread (TRISC2) configuration helpers, bound to a kernel builder.

  Tier-2 intent over Tier-1 ops, same composition shape as ``Unpack``: stored
  ``self.k`` is the kernel, no inheritance. ``dtype`` drives the src/dst format
  writes and the packer data-format word; the remaining structural words are
  named constants pending full field decode."""

  def __init__(self, kernel):
    self.k = kernel

  def _state_formats(self, k, dtype: Dtype):
    k.write_repeated_bytes(TLM.TRISC2_PACK_TILE_FACE_R_DIM, _TILE_FACE_R_DIM, 8)
    k.write_repeated_bytes(TLM.TRISC2_PACK_TILE_NUM_FACES, _TILE_NUM_FACES, 8)
    k.write32(TLM.TRISC2_PACK_PARTIAL_FACE_SEC1, 0)
    k.write_repeated_bytes(TLM.TRISC2_PACK_SRC_FORMAT, dtype.value, 16)
    k.write_repeated_bytes(TLM.TRISC2_PACK_DST_FORMAT, dtype.value, 16)

  def _dest_addr_dmaregs(self, k):
    # SETDMAREG block driving the THCON dest-addr config (re-issued after MOP).
    k.emit(TTSETDMAREG(0, 0, 0, 56))
    k.emit(TTSETDMAREG(0, 32, 0, 57))
    k.emit(TTSETDMAREG(0, 512, 0, 58))
    k.emit(TTSETDMAREG(0, 2048, 0, 59))
    k.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))
    k.emit(TTWRCFG(28, 0, 12))
    k.emit(TTWRCFG(29, 0, 13))
    k.emit(TTNOP())
    k.emit(TTNOP())

  def _alu_acc_rmw(self, k):
    k.emit(TTATGETM(0))
    for inst in (
      TTRMWCIB3(Mask=0x1E, Data=0x0A, CfgRegAddr=Cfg.ALU.addr32),
      TTRMWCIB0(Mask=0xFC, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
      TTRMWCIB1(Mask=0xFF, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
      TTRMWCIB2(Mask=0x3F, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
    ):
      k.push_tensix(inst)
    k.emit(TTATRELM(0))

  def _pack_cfg(self, k, dtype: Dtype, out_cb: int):
    k.write32(Cfg.THCON_SEC0_REG1, _EXP_SECTION_SIZE)
    k.write32(Cfg.THCON_SEC0_REG1_1, _pack_data_format(dtype))
    k.write32(Cfg.PCK_DEST_RD_CTRL, 0)
    for off in range(4):
      k.write32(GprPack.DEST_OFFSET_LO + off * 4, 0)
      k.write32(GprPack.DEST_OFFSET_HI + off * 4, _DEST_OFFSET_HI)
    k.write32(GprPack.EXP0_SEC_SIZE_BFP, _EXP_SECTION_SIZE)
    for reg in (Cfg.PACK_COUNTERS_SEC0, Cfg.PACK_COUNTERS_SEC1,
                Cfg.PACK_COUNTERS_SEC2, Cfg.PACK_COUNTERS_SEC3):
      k.write32(reg, _PACK_COUNTERS)
    k.write32(Cfg.PCK_EDGE, _PCK_EDGE)
    k.write32(Cfg.TILE_ROW_SET_MAPPING_0, 0)
    # Packer tile/page size comes from TRISC local CB state (16B units).
    k.cb_iface(k.data["cb_interface"], out_cb, out=t6)
    k.lw(t1, t6, 8)
    k.write32(GprPack.TILE_HEADER, t1)
    k.write32(GprPack.TILE_HEADER_1, 0)
    k.write32(GprPack.TILE_HEADER_2, 0)
    k.write32(GprPack.TILE_HEADER_3, 0)

  def init(self, *, dtype: Dtype = Dtype.Float16_b, out_cb: int, mop_cfg):
    """Configure the packer: local format state, ALU-acc RMW, pack cfg regs and
    tile header for ``dtype``/``out_cb``, the pack MOP template, and the dest /
    output address setup. Mirrors the TRISC2 init block of add1 exactly."""
    k = self.k

    self._state_formats(k, dtype)
    self._dest_addr_dmaregs(k)
    self._alu_acc_rmw(k)
    self._pack_cfg(k, dtype, out_cb)

    k.emit(TTSETADCXX(4, 15, 0))
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC0, _ADDR_MOD_PACK[0])
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC1, _ADDR_MOD_PACK[1])
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC2, _ADDR_MOD_PACK[2])

    k.mop_sync(2, tmp=t1)
    k.write_mop_cfg(mop_cfg, 2)

    self._dest_addr_dmaregs(k)
    k.emit(TTSETADCXX(4, 15, 0))
    k.write32(k.data["dest_offset_id"], 0)

    # Output addr config setup.
    k.emit(TTSTALLWAIT(TensixStall.TDMA | TensixStall.THCON, TensixWait.PACK0))
    k.emit(TTSETDMAREG(0, 0, 0, 16))
    k.emit(TTSETDMAREG(0, 0, 0, 17))
    k.emit(TTSETDMAREG(0, 512, 0, 18))
    k.emit(TTSETDMAREG(0, 0, 0, 19))
    k.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))
    k.emit(TTWRCFG(4, 1, 180))
    k.emit(TTDMANOP())
    k.emit(TTDMANOP())

    k.emit(TTSETADCXY(4, 0, 0, 0, 0, 0xB))
    k.emit(TTSETADCZW(4, 0, 0, 0, 0, 0xF))
    return k
