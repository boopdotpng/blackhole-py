from __future__ import annotations

from dsl import (
  TTATGETM, TTATRELM, TTDMANOP, TTNOP, TTRMWCIB0, TTRMWCIB1, TTRMWCIB2,
  TTRMWCIB3, TTSETADCXX, TTSETADCXY, TTSETADCZW, TTSETDMAREG, TTSTALLWAIT,
  TTWRCFG, t1, t6,
)
from program import Dtype
from ttk.mailbox import TriscLocalMem as TLM
from ttk.tensix import Cfg, GprPack, TensixStall, TensixWait, ThreadCfg

# --- Packer data-format word (Blackhole cfg word 70) ---
# THCON_SEC0_REG1_1 packs the pack in/out formats:
#   bit0 = Disable_zero_compress, bits[7:4] = Out_data_format,
#   bits[11:8] = In_data_format (both == Dtype.value).
# For Float16_b (5): 0x1 | 5<<4 | 5<<8 == 0x551.
_PACK_DISABLE_ZERO_COMPRESS = 0x1

# PCK_DEST_RD_CTRL (cfg word 18): Read_32b_data (bit0) makes PACK read full
# 32-bit (fp32) data out of DST -- required when the math thread accumulates in
# fp32 (Dst32). Round_10b_mant (bit3) rounds the fp32 mantissa to fp16's 10
# bits on store; bf16's 7+1-bit mantissa truncates fine without it.
_PCK_READ_32B = 0x1
_PCK_ROUND_10B = 0x8


def _pack_data_format(dtype: Dtype) -> int:
  return _PACK_DISABLE_ZERO_COMPRESS | (dtype.value << 4) | (dtype.value << 8)


def pck_dest_rd_ctrl(dtype: Dtype, *, fp32_dest: bool) -> int:
  if not fp32_dest:
    return 0
  return _PCK_READ_32B | (_PCK_ROUND_10B if dtype is Dtype.Float16 else 0)


def _packer_stride_words(dtype: Dtype) -> tuple[int, int]:
  x_stride = 4 if dtype in (Dtype.Float32, Dtype.Int32, Dtype.UInt32) else 2 if dtype is Dtype.Float16 else 1
  y_stride = 16 * x_stride
  z_stride = 16 * y_stride
  w_stride = 4 * 16 * 16 * x_stride
  return y_stride << 16, z_stride | (w_stride << 16)


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

  def _set_strides(self, k, dtype: Dtype, *, fp32_dest: bool = False):
    src_dtype = Dtype.Float32 if fp32_dest else dtype
    xy0, zw0 = _packer_stride_words(src_dtype)
    k.write32(Cfg.PCK0_ADDR_CTRL_XY_REG_0, xy0)
    k.write32(Cfg.PCK0_ADDR_CTRL_ZW_REG_0, zw0)

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

  def set_format(self, dtype: Dtype, *, fp32_dest: bool = False, out_cb: int | None = None):
    """Runtime-reconfigure the packer's data format. The EFFECTIVE pack output
    format comes from the TRISC2 TLM format mailbox (read by the pack pipeline),
    not only the THCON cfg reg -- so rewrite both. Masked-RMW the THCON format
    nibbles (Out=byte0[7:4], In=byte1[3:0]) so the L1-acc/zero-flag bits sharing
    THCON_SEC0_REG1_1 are preserved. Use case: packing matmul partials to a
    non-operand-format intermediate CB (the fp16 packer L1-acc HW bug dodge)."""
    k = self.k
    k.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.PACK0))
    fmt = dtype.value & 0xF
    k.write_repeated_bytes(TLM.TRISC2_PACK_SRC_FORMAT, fmt, 16)
    k.write_repeated_bytes(TLM.TRISC2_PACK_DST_FORMAT, fmt, 16)
    for reg in (
      Cfg.THCON_SEC0_REG1_1,
      Cfg.THCON_SEC0_REG8_1,
      Cfg.THCON_SEC1_REG1_1,
      Cfg.THCON_SEC1_REG8_1,
    ):
      k.push_tensix(TTRMWCIB0(Mask=0xF0, Data=(fmt << 4) & 0xF0, CfgRegAddr=reg.addr32))
      k.push_tensix(TTRMWCIB1(Mask=0x0F, Data=fmt, CfgRegAddr=reg.addr32))
    if out_cb is not None:
      k.cb_iface(k.data["cb_interface"], out_cb, out=t6)
      k.lw(t1, t6, 8)
      k.write32(GprPack.TILE_HEADER, t1)
    k.write32(Cfg.PCK_DEST_RD_CTRL, pck_dest_rd_ctrl(dtype, fp32_dest=fp32_dest))
    self._set_strides(k, dtype, fp32_dest=fp32_dest)
    return k

  def _pack_cfg(self, k, dtype: Dtype, out_cb: int, fp32_dest: bool = False):
    k.write32(Cfg.THCON_SEC0_REG1, _EXP_SECTION_SIZE)
    k.write32(Cfg.THCON_SEC0_REG1_1, _pack_data_format(dtype))
    k.write32(Cfg.PCK_DEST_RD_CTRL, pck_dest_rd_ctrl(dtype, fp32_dest=fp32_dest))
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
    self._set_strides(k, dtype, fp32_dest=fp32_dest)

  def init(self, *, dtype: Dtype = Dtype.Float16_b, out_cb: int, mop_cfg, fp32_dest: bool = False):
    """Configure the packer: local format state, ALU-acc RMW, pack cfg regs and
    tile header for ``dtype``/``out_cb``, the pack MOP template, and the dest /
    output address setup. Mirrors the TRISC2 init block of add1 exactly.
    ``fp32_dest=True`` makes PACK read fp32 out of DST -- pair it with
    ``Unpack.init(fp32_dest=True)``."""
    k = self.k

    self._state_formats(k, dtype)
    self._dest_addr_dmaregs(k)
    self._alu_acc_rmw(k)
    self._pack_cfg(k, dtype, out_cb, fp32_dest=fp32_dest)

    k.emit(TTSETADCXX(4, 15, 0))
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC0, _ADDR_MOD_PACK[0])
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC1, _ADDR_MOD_PACK[1])
    k.setc16(ThreadCfg.ADDR_MOD_PACK_SEC2, _ADDR_MOD_PACK[2])

    k.mop_sync(2, tmp=t1)
    k.write_mop_cfg(mop_cfg, 2)

    self._dest_addr_dmaregs(k)
    k.emit(TTSETADCXX(4, 15, 0))
    k.write32(k.data["dest_offset_id"], 0)

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
