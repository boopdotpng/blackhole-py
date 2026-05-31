#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from device import Device
from dsl import (
  TTATGETM, TTATRELM, TTDMANOP, TTMOP, TTMOVA2D, TTNOP, TTPACR,
  TTRMWCIB0, TTRMWCIB1, TTRMWCIB2, TTRMWCIB3, TTSETADC,
  TTSEMGET, TTSEMINIT, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSFPCONFIG,
  TTSFPLOADI, TTSETADCXX, TTSETADCXY, TTSETADCZW,
  TTSETC16, TTSETDMAREG, TTSTALLWAIT, TTSTOREREG, TTUNPACR, TTUNPACR_NOP,
  TTWRCFG, TTZEROACC, TTZEROSRC,
  a0, a1, a2, a5, s0, s2, s3, s4, s5, t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk.addrs import (
  BriscMailbox as BM, CircularBuffer as CB, NcriscMailbox as NM, NOC, TensixL1,
  TriscLocalMem as TLM,
)
from ttk.kernel import Brisc, Ncrisc, RiscSync, Trisc
from ttk.tensix import (
  Cfg, GprPack, GprUnpack, MopCfg, TensixRegs, TensixSem, TensixSemWait,
  TensixStall, TensixWait, ThreadCfg,
)

TILE_BYTES = Dtype.Float16_b.tile_size
CB_DEPTH = 4
TARGET_CORE = (1, 2)
DEFAULT_TILES_PER_CORE = 10
OUT_CB = 16
SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
SYNC_L1 = SCRATCH_L1 + 0x10000
SYNC_TRISC_START = SYNC_L1
SYNC_READ = SYNC_L1 + 4
SYNC_DONE0 = SYNC_L1 + 8
SYNC_DONE1 = SYNC_L1 + 12
SYNC_DONE2 = SYNC_L1 + 16
SYNC_TRISC_INIT = SYNC_L1 + 20
# Start/init handshake layout shared by BRISC (driver) and the three TRISCs.
SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)
STALL_MATH_PACK_ROOM = TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU
STALL_MATH_PACK_DATA = TensixStall.TDMA
WAIT_MATH_AND_SFPU = TensixWait.MATH | TensixWait.SFPU
WAIT_THCON_AND_PACK = TensixWait.THCON | TensixWait.PACK0
# MOP (macro-op) expander templates: two loop counts + 7 Tensix instruction
# slots the expander replays. See ttk.tensix.MopCfg.
_UNPACK_NOP = TTUNPACR_NOP(Unpacker_Select=1, Set_Dvalid=1, Unpack_Pop=1)
_MATH_MOVA2D = TTMOVA2D(addr_mode=2, instr_mod=2)

PACK_MOP_CFG = MopCfg(
  loop_outer=4, loop_inner=4,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    TTPACR(),
    TTNOP(),
    TTPACR(AddrMode=1, Last=1),
    TTPACR(AddrMode=2),
  ],
)
UNPACK_MOP_CFG = MopCfg(
  loop_outer=4, loop_inner=1,
  template=[
    TTUNPACR(AddrMode=1, OvrdThreadId=1, SetDatValid=1, Last=1),
    TTNOP(), TTNOP(),
    _UNPACK_NOP,
    TTNOP(),
    _UNPACK_NOP,
    _UNPACK_NOP,
  ],
)
MATH_MOP_CFG = MopCfg(
  loop_outer=4, loop_inner=2,
  template=[
    TTNOP(),
    TTSETRWC(clear_ab_vld=3, BitMask=3),
    TTNOP(),
    _MATH_MOVA2D,
    TTNOP(),
    _MATH_MOVA2D,
    _MATH_MOVA2D,
  ],
)

def trisc0() -> Trisc:
  fw = Trisc(0, SYNC)
  fw.prologue()

  fw.write32(fw.data["cfg_state_id"], 0)
  fw.setc16(ThreadCfg.CFG_STATE_ID_StateID, 0)
  fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, 0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)

  # The old add1 unpacker path configured CB0 as 4 faces of Float16_b.
  fw.emit(TTZEROSRC(0, 0, 1, 3))
  fw.write32(fw.data["cfg_state_id"], 0)
  fw.setc16(ThreadCfg.CFG_STATE_ID_StateID, 0)

  wait_unp = fw._new_label("init_wait_unpack_ctx")
  wait_unp_done = fw._new_label("init_wait_unpack_ctx_done")
  fw.li(t0, TensixRegs.PC_UNPACK_SYNC)
  fw.label(wait_unp)
  fw.lw(t1, t0, 0)
  fw.andi(t1, t1, 0xFF)
  fw.beq(t1, zero, wait_unp_done)
  fw.fence()
  fw.j(wait_unp)
  fw.label(wait_unp_done)

  fw.emit(TTSETADCXY(3, 0, 0, 0, 0, 0xB))
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  fw.write32(Cfg.UNP0_ADDR_CTRL_ZW_REG_1, 0x00000200)
  fw.write32(Cfg.UNP1_ADDR_CTRL_ZW_REG_1, 0x00000200)
  fw.emit(TTATGETM(0))
  # Masked byte RMW of the ALU config regs under the ATGETM/ATRELM mutex.
  unpack_rmw = [
    TTRMWCIB0(Mask=0xFF, Data=0x00, CfgRegAddr=Cfg.ALU_FORMAT_SPEC_REG.addr32),
    TTRMWCIB1(Mask=0x7F, Data=0x00, CfgRegAddr=Cfg.ALU_FORMAT_SPEC_REG.addr32),
    TTRMWCIB0(Mask=0x07, Data=0x00, CfgRegAddr=Cfg.ALU.addr32),
    TTRMWCIB1(Mask=0x80, Data=0x00, CfgRegAddr=Cfg.ALU.addr32),
    TTRMWCIB2(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.ALU.addr32),
    TTRMWCIB3(Mask=0x60, Data=0x00, CfgRegAddr=Cfg.ALU.addr32),
    TTRMWCIB0(Mask=0x01, Data=0x01, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
  ]
  for inst in unpack_rmw:
    fw.push_tensix(inst)
  fw.emit(TTATRELM(0))
  fw.write32(Cfg.THCON_SEC0_REG0_TileDescriptor, 0x00000015)
  fw.write32(Cfg.THCON_SEC0_REG0_TileDescriptor_1, 0x00040001)
  fw.write32(Cfg.THCON_SEC1_REG0_TileDescriptor, 0x01000015)
  fw.write32(Cfg.THCON_SEC1_REG0_TileDescriptor_1, 0x00040001)
  fw.write32(Cfg.THCON_SEC0_REG2, 0x00000025)
  fw.write32(Cfg.THCON_SEC0_REG2_1, 0x000F000F)
  fw.write32(Cfg.THCON_SEC1_REG2, 0x00000025)
  fw.write32(Cfg.THCON_SEC1_REG2_1, 0x000F000F)
  fw.push_tensix(TTSETADCXX(1, 255, 0))
  fw.push_tensix(TTSETADCXX(2, 255, 0))
  fw.write32(Cfg.THCON_SEC0_REG5_Dest_cntx, 0x00400040)
  fw.write32(Cfg.THCON_SEC0_REG5_Tile_x_dim_cntx, 0x01000100)
  # Unpacker face-dimension table (p_gpr_unpack): face size NxM packed as
  # (N*M) | (N*M)<<16, halving from 16x16=256 down to 1x16=16.
  fw.write32(GprUnpack.FACE_DIM_16x16, 0x01000100)
  fw.write32(GprUnpack.FACE_DIM_8x16, 0x00800080)
  fw.write32(GprUnpack.FACE_DIM_4x16, 0x00400040)
  fw.write32(GprUnpack.FACE_DIM_2x16, 0x00200020)
  fw.write32(GprUnpack.FACE_DIM_1x16, 0x00100010)
  fw.setc16(ThreadCfg.SRCA_SET, 4)
  fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, 0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  page_size_16b = TILE_BYTES >> 4
  for raw in (
    0x45000048 + (page_size_16b << 8),
    0x4500004A + (page_size_16b << 8),
    TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32),
  ):
    fw.push_tensix(raw)
  fw.emit(TTSETADCXX(1, 255, 0))
  fw.push_tensix(TTRMWCIB1(Mask=0x01, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2.addr32))
  fw.emit(TTSETADCXX(1, 255, 0))
  fw.write_mop_cfg(UNPACK_MOP_CFG, 0)
  fw.tensix_sync(0)

  fw.init_barrier()

  with fw.tile_loop():
    fw.addi(t2, s5, 1)
    fw.cb_wait_front(fw.data["cb_interface"], 0)
    fw.cb_read_ptr(fw.data["cb_interface"], 0, out=s0)
    fw.cb_iface(fw.data["cb_interface"], 0, out=t6)
    fw.lw(t1, t6, 8)
    fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 15))

    wait_unp = fw._new_label("wait_unpack_ctx")
    wait_unp_done = fw._new_label("wait_unpack_ctx_done")
    fw.li(t0, TensixRegs.PC_UNPACK_SYNC)
    fw.label(wait_unp)
    fw.lw(t1, t0, 0)
    fw.andi(t1, t1, 0xFE)
    fw.beq(t1, zero, wait_unp_done)
    fw.fence()
    fw.j(wait_unp)
    fw.label(wait_unp_done)

    fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
    fw.li(t2, TensixRegs.CFG_BASE + 76 * 4)
    cfg_addr_done = fw._new_label("trisc0_cfg_addr_done")
    fw.beq(t1, zero, cfg_addr_done)
    fw.addi(t2, t2, 4)
    fw.label(cfg_addr_done)
    fw.addi(t3, s0, -1)
    fw.sw(t3, t2, 0)
    fw.lw(t1, t2, 0)
    fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
    fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, t2)
    fw.beq(t1, zero, "trisc0_set_ctx1")
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
    fw.j("trisc0_ctx_set")
    fw.label("trisc0_set_ctx1")
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
    fw.label("trisc0_ctx_set")
    fw.cb_pop_front(fw.data["cb_interface"], 0, tensix_ack=True)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE0, t2)
  return fw

def trisc1() -> Trisc:
  fw = Trisc(1, SYNC)
  fw.prologue()

  # Match the other TRISC prologues: make the initial context writes visible,
  # then wait until the unpack side reports its context is idle.
  fw.tensix_sync(1)
  fw.write_repeated_bytes(TLM.TRISC1_UNPACK_TILE_NUM_FACES, 4, 8)
  fw.write32(TLM.TRISC1_UNPACK_DST_FORMAT, Dtype.Float16_b.value)
  fw.write32(TLM.TRISC1_UNPACK_SRC_FORMAT, Dtype.Float16_b.value)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC1_Src, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC1, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC1_Bias, 0)
  fw.emit(TTZEROACC(3, 0, 0, 1, 0))
  fw.wait_mmio_low_byte_zero(TensixRegs.PC_UNPACK_SYNC)
  fw.math_direct_mova2d_init()
  fw.write_mop_cfg(MATH_MOP_CFG, 1)
  fw.tensix_sync(1)
  fw.wait_mmio_low_byte_zero(TensixRegs.pc_buf_sem(TensixSem.MATH_PACK))
  fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.MATH_PACK), init_value=0, max_value=1))
  fw.push_tensix(TTSETC16(ThreadCfg.DEST_TARGET_REG_CFG_MATH_Offset, 0))
  fw.push_tensix(TTRMWCIB0(Mask=0x08, Data=0x08, CfgRegAddr=Cfg.DEST_ACCESS_CFG.addr32))
  fw.write32(fw.data["dest_offset_id"], 0)
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.MATH))
  fw.push_tensix(TTRMWCIB3(Mask=0x80, Data=0x00, CfgRegAddr=Cfg.ALU.addr32))
  fw.math_direct_mova2d_init()
  fw.write_mop_cfg(MATH_MOP_CFG, 1)
  fw.emit(TTSFPLOADI(0, 0, 10))
  fw.emit(TTSFPLOADI(0, 0, 8))
  fw.emit(TTSFPCONFIG(0, 15, 1))
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC7_Src, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC7, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC7_Bias, 0)
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))

  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.write_trisc1_dest_offset_instr(t1, t2, t3)
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.write_trisc1_dest_offset_instr(t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    for _ in range(4):
      fw.math_add1_replay_row()
    fw.push_tensix(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.push_tensix(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))
    fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_PACK)))
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE1, t2)
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(fw.data["dest_offset_id"], t2)
    fw.emit(TTSTALLWAIT(TensixStall.CFG, WAIT_MATH_AND_SFPU))
    fw.write_trisc1_dest_offset_instr(t2, t1, t3)
  return fw


def trisc2() -> Trisc:
  fw = Trisc(2, SYNC)
  fw.prologue()

  # Mirror add1_compute_trisc2.kernel.dis from blackhole-py-old (6a80..6d68).
  # blackhole-py-only state setup (TRISC2 mailbox regs not visible in OLD asm):
  fw.write_repeated_bytes(TLM.TRISC2_PACK_TILE_FACE_R_DIM, 16, 8)
  fw.write_repeated_bytes(TLM.TRISC2_PACK_TILE_NUM_FACES, 4, 8)
  fw.write32(TLM.TRISC2_PACK_PARTIAL_FACE_SEC1, 0)
  fw.write_repeated_bytes(TLM.TRISC2_PACK_SRC_FORMAT, Dtype.Float16_b.value, 16)
  fw.write_repeated_bytes(TLM.TRISC2_PACK_DST_FORMAT, Dtype.Float16_b.value, 16)

  # First SETDMAREG block (OLD 6ba8..6be0).
  fw.emit(TTSETDMAREG(0, 0, 0, 56))
  fw.emit(TTSETDMAREG(0, 32, 0, 57))
  fw.emit(TTSETDMAREG(0, 512, 0, 58))
  fw.emit(TTSETDMAREG(0, 2048, 0, 59))
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))
  fw.emit(TTWRCFG(28, 0, 12))
  fw.emit(TTWRCFG(29, 0, 13))
  fw.emit(TTNOP())
  fw.emit(TTNOP())

  # Atomic config RMW (OLD 6be4..6c18).
  fw.emit(TTATGETM(0))
  for inst in (
    TTRMWCIB3(Mask=0x1E, Data=0x0A, CfgRegAddr=Cfg.ALU.addr32),
    TTRMWCIB0(Mask=0xFC, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
    TTRMWCIB1(Mask=0xFF, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
    TTRMWCIB2(Mask=0x3F, Data=0x00, CfgRegAddr=Cfg.ALU_ACC_CTRL_Zero_Flag_disabled_src.addr32),
  ):
    fw.push_tensix(inst)
  fw.emit(TTATRELM(0))

  # CFG/REGFILE pack config (OLD 6c1c..6c74).
  # `lui a1,0x40` -> a1 = 0x40 << 12 = 0x00040000 (not 0x00400000).
  fw.write32(Cfg.THCON_SEC0_REG1, 0x00040000)
  fw.write32(Cfg.THCON_SEC0_REG1_1, 0x00000551)
  fw.write32(Cfg.PCK_DEST_RD_CTRL, 0)
  for off in range(4):
    fw.write32(GprPack.DEST_OFFSET_LO + off * 4, 0)
    fw.write32(GprPack.DEST_OFFSET_HI + off * 4, 512)
  fw.write32(GprPack.EXP0_SEC_SIZE_BFP, 0x00040000)
  # OLD writes `sw a1, 112..124(a5)` -> CFG words 28..31 (not 112..115).
  for reg in (Cfg.PACK_COUNTERS_SEC0, Cfg.PACK_COUNTERS_SEC1,
              Cfg.PACK_COUNTERS_SEC2, Cfg.PACK_COUNTERS_SEC3):
    fw.write32(reg, 0x00001000)
  # OLD: `sw t1, 96(a5)` -> CFG word 24.
  fw.write32(Cfg.PCK_EDGE, 0x0000FFFF)
  fw.write32(Cfg.TILE_ROW_SET_MAPPING_0, 0)
  # Packer tile/page size comes from TRISC local CB state, already shifted to 16B units.
  fw.cb_iface(fw.data["cb_interface"], OUT_CB, out=t6)
  fw.lw(t1, t6, 8)
  fw.write32(GprPack.TILE_HEADER, t1)
  fw.write32(GprPack.TILE_HEADER_1, 0)
  fw.write32(GprPack.TILE_HEADER_2, 0)
  fw.write32(GprPack.TILE_HEADER_3, 0)

  # First TTSETADCXX (OLD 6c84..6c8c, raw 0x5E803C00 = TTSETADCXX(4, 15, 0)).
  fw.emit(TTSETADCXX(4, 15, 0))

  # SETC16 37/38/39 (OLD 6c90..6c98). MUST come AFTER first TTSETADCXX.
  fw.setc16(ThreadCfg.ADDR_MOD_PACK_SEC0, 260)
  fw.setc16(ThreadCfg.ADDR_MOD_PACK_SEC1, 10272)
  fw.setc16(ThreadCfg.ADDR_MOD_PACK_SEC2, 4384)

  # MOP sync + MOP_CFG load (OLD 6c9c..6cf0).
  fw.mop_sync(2, tmp=t1)
  fw.write_mop_cfg(PACK_MOP_CFG, 2)

  # Second SETDMAREG block (OLD 6cf4..6d14). Must be re-issued after MOP_CFG store.
  fw.emit(TTSETDMAREG(0, 0, 0, 56))
  fw.emit(TTSETDMAREG(0, 32, 0, 57))
  fw.emit(TTSETDMAREG(0, 512, 0, 58))
  fw.emit(TTSETDMAREG(0, 2048, 0, 59))
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))
  fw.emit(TTWRCFG(28, 0, 12))
  fw.emit(TTWRCFG(29, 0, 13))
  fw.emit(TTNOP())
  fw.emit(TTNOP())

  # Second TTSETADCXX (OLD 6d18).
  fw.emit(TTSETADCXX(4, 15, 0))

  # dest_offset_id := 0 (OLD 6d1c..6d34).
  fw.write32(fw.data["dest_offset_id"], 0)

  # Output addr config setup (OLD 6d38..6d60).
  fw.emit(TTSTALLWAIT(TensixStall.TDMA | TensixStall.THCON, TensixWait.PACK0))
  fw.emit(TTSETDMAREG(0, 0, 0, 16))
  fw.emit(TTSETDMAREG(0, 0, 0, 17))
  fw.emit(TTSETDMAREG(0, 512, 0, 18))
  fw.emit(TTSETDMAREG(0, 0, 0, 19))
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))
  fw.emit(TTWRCFG(4, 1, 180))
  fw.emit(TTDMANOP())
  fw.emit(TTDMANOP())

  # ADCXY/ZW (OLD 6d64..6d68) - issued AFTER WRCFG(8,1,180) + DMANOPs.
  fw.emit(TTSETADCXY(4, 0, 0, 0, 0, 0xB))
  fw.emit(TTSETADCZW(4, 0, 0, 0, 0, 0xF))

  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_DATA,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_ZERO,
    ))
    fw.cb_reserve_back(fw.data["cb_interface"], OUT_CB)
    fw.cb_write_ptr(fw.data["cb_interface"], OUT_CB, out=s0)
    fw.slli(t4, s0, 4)
    fw.addi(s0, s0, -1)
    fw.emit(TTSETADC(4, 0, 3, 0))
    fw.slli(t1, s0, 8)
    fw.li(t2, 0x00FFFF00)
    fw.and_(t1, t1, t2)
    fw.li(t2, 0x45000018)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.srli(t1, s0, 16)
    fw.slli(t1, t1, 8)
    fw.li(t2, 0x00800000)
    fw.or_(t1, t1, t2)
    fw.li(t2, 0x45000019)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTSTALLWAIT(TensixStall.CFG, WAIT_THCON_AND_PACK))
    fw.emit(TTWRCFG(12, 0, 69))
    fw.srli(t1, s0, 16)
    fw.slli(t1, t1, 8)
    fw.li(t2, 0x45000019)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTDMANOP())
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.li(t2, 0)
    pack_offset_ready = fw._new_label("pack_offset_ready")
    fw.beq(t1, zero, pack_offset_ready)
    fw.li(t2, 512)
    fw.label(pack_offset_ready)
    fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC0, t2)
    fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC1, t2)
    fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC2, t2)
    fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC3, t2)
    fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))
    fw.emit(TTMOP(1, 0, 0))
    fw.tensix_sync(2, tmp=t1)
    fw.emit(TTSETADCZW(4, 0, 0, 0, 0, 5))
    fw.cb_push_back(fw.data["cb_interface"], OUT_CB)
    # OLD 6e7c..6e8c: push SYNC_TILES_RECEIVED via Tensix.
    # DMAREG[48] := received_count from local output CB state, then
    # TTSTOREREG(TdmaDataRegIndex=24, RegAddr=0x1600A) writes the 32-bit GPR
    # pair {DMAREG[48],DMAREG[49]} to SYNC_TILES_RECEIVED[OUT_CB].
    fw.cb_iface(fw.data["cb_interface"], OUT_CB, out=t6)
    fw.lw(t1, t6, 24)
    fw.cb_counter_high(t1, t1)
    fw.slli(t1, t1, 8)
    fw.li(t2, TTSETDMAREG(0, 0, 0, 48).raw_word())
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTSTALLWAIT(TensixStall.THCON, TensixWait.PACK0))
    fw.push_tensix(
      TTSTOREREG(24, ((CB.SYNC_TILES_RECEIVED_BASE + OUT_CB * CB.SYNC_STRIDE) >> 2) & 0x3FFFF),
    )
    fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.PACK0))
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.andi(t2, t1, 1)
    fw.li(t3, 0x10104000)
    fw.add(t2, t2, t3)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t2)
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.MATH_PACK)))
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(fw.data["dest_offset_id"], t2)
    fw.emit(TTDMANOP())
    fw.emit(TTDMANOP())
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE2, t2)
  return fw


def brisc() -> Brisc:
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.add(a1, s2, s5)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.local_noc0_coord(a5)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.addi(t4, t4, 1)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
    fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.label("brisc_read_wait")
    fw.lw(t1, t0, 0)
    fw.bltu(t1, t4, "brisc_read_wait")
    fw.fence()
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_READ, t2)
  return fw


def ncrisc(num_banks: int) -> Ncrisc:
  fw = Ncrisc()
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  with fw.tile_loop("ncrisc"):
    fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
    fw.add(a1, s2, s5)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, num_banks)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
    fw.addi(t4, t4, 1)
    fw.cb_read_ptr(NM.CB_INTERFACE, OUT_CB, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_write(1, 0, t5, a0, 0, a2, t6, a=t0, v=t1)
    fw.noc_write_barrier(1, t4, addr=t0, val=t1)
    fw.cb_pop_front(NM.CB_INTERFACE, OUT_CB)
  return fw

def build_program(
  src_addr: int,
  dst_addr: int,
  num_banks: int,
  *,
  cores: list[tuple[int, int]] | None = None,
  tiles_per_core: int = DEFAULT_TILES_PER_CORE,
  base_tile_offset: int = 0,
  use_grid: bool = True,
) -> Program:
  if cores is None:
    cores = [TARGET_CORE]
  core_index = {core: i for i, core in enumerate(cores)}

  brisc_fw = brisc()
  ncrisc_fw = ncrisc(num_banks)
  trisc0_fw = trisc0()
  trisc1_fw = trisc1()
  trisc2_fw = trisc2()
  brisc_fw.rta(lambda x, y: [src_addr, base_tile_offset + core_index[(x, y)] * tiles_per_core, tiles_per_core, num_banks])
  ncrisc_fw.rta(lambda x, y: [dst_addr, base_tile_offset + core_index[(x, y)] * tiles_per_core, tiles_per_core, num_banks])
  trisc0_fw.rta(lambda _x, _y: [tiles_per_core])
  trisc1_fw.rta(lambda _x, _y: [tiles_per_core])
  trisc2_fw.rta(lambda _x, _y: [tiles_per_core])
  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  if use_grid:
    rows = tuple(sorted({y for _, y in cores}))
    cols = tuple(sorted({x for x, _ in cores}))
    prog.grid = (rows, cols)
  prog.name = "add1"
  return prog

def parse_core(s: str) -> tuple[int, int]:
  try:
    x, y = s.split(",", 1)
    return int(x, 0), int(y, 0)
  except ValueError as e:
    raise argparse.ArgumentTypeError("core must be X,Y") from e

def make_argparser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description="Run add1 on one or many Blackhole Tensix cores.")
  parser.add_argument("--tiles-per-core", type=int, default=DEFAULT_TILES_PER_CORE,
                      help=f"tiles processed by each core (default: {DEFAULT_TILES_PER_CORE})")
  parser.add_argument("--cores", choices=("auto", "program", "worker", "one"), default="auto",
                      help="auto/program use safe dispatchable cores; worker includes CQ cores and needs TT_USB=1")
  parser.add_argument("--core", type=parse_core, default=TARGET_CORE,
                      help=f"core for --cores one, as X,Y (default: {TARGET_CORE[0]},{TARGET_CORE[1]})")
  return parser

def select_cores(device: Device, mode: str, core: tuple[int, int]) -> tuple[list[tuple[int, int]], bool]:
  if mode == "one":
    return [core], True
  if mode == "worker":
    if device.fast_dispatch:
      raise RuntimeError("literal all-worker stress includes command-queue cores; run with TT_USB=1 --cores worker")
    return list(device.board_info.worker_cores), False
  if mode == "program" or device.fast_dispatch:
    return list(device.cores), False
  return list(device.board_info.worker_cores), False

def make_input(n_tiles: int) -> bytes:
  src_rm = bytearray()
  for i in range(n_tiles * 32 * 32):
    src_rm += (struct.unpack("<I", struct.pack("<f", float(i)))[0] >> 16).to_bytes(2, "little")
  return bytes(src_rm)

def make_expected(src_rm: bytes) -> bytes:
  exp = bytearray(len(src_rm))
  for i in range(0, len(src_rm), 2):
    x = int.from_bytes(src_rm[i : i + 2], "little")
    y = struct.unpack("<I", struct.pack("<f", struct.unpack("<f", struct.pack("<I", x << 16))[0] + 1.0))[0] >> 16
    exp[i : i + 2] = y.to_bytes(2, "little")
  return bytes(exp)

def main():
  args = make_argparser().parse_args()
  if args.tiles_per_core <= 0:
    raise ValueError("--tiles-per-core must be positive")

  device = Device()
  try:
    cores, use_grid = select_cores(device, args.cores, args.core)
    n_tiles = len(cores) * args.tiles_per_core
    src_rm = make_input(n_tiles)
    src_buf = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="src")
    dst_buf = device.dram.alloc(n_tiles, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="dst")
    prog = build_program(
      src_buf.addr,
      dst_buf.addr,
      len(device.dram.bank_tiles),
      cores=cores,
      tiles_per_core=args.tiles_per_core,
      use_grid=use_grid,
    )
    timings = device.run(prog)
    out = device.dram_read(dst_buf)
    exp = make_expected(src_rm)
    mismatch = next((i for i, (g, e) in enumerate(zip(out, exp)) if g != e), None)
    if mismatch is not None:
      got = out[mismatch:mismatch + 32].hex()
      want = exp[mismatch:mismatch + 32].hex()
      raise AssertionError(f"mismatch byte={mismatch} got={got} exp={want}")
    print(f"PASS add1 {len(cores)} cores x {args.tiles_per_core} tiles/core = {n_tiles} tiles")
    for timing in timings:
      name = f"{timing['name']}: " if timing["name"] else ""
      print(f"  {name}{timing['us']:,.1f} us")
  finally:
    device.close()


if __name__ == "__main__":
  main()
