#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))
if str(EXAMPLES) not in sys.path:
  sys.path.insert(0, str(EXAMPLES))

from program import Dtype  # noqa: E402
from program import Program  # noqa: E402
from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  TTDMANOP, TTELWMUL, TTINCRWC, TTMOP, TTMOVA2D, TTNOP, TTPACR, TTREPLAY,
  TTSEMGET, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSETADC, TTSETADCZW, TTSETDMAREG,
  TTSTALLWAIT, TTSTOREREG, TTUNPACR, TTUNPACR_NOP, TTWRCFG, TTZEROACC,
  TTSFPADDI, TTSFPADD, TTSFPCOMPC, TTSFPDIVP2, TTSFPENCC, TTSFPIADD,
  TTSFPLOAD, TTSFPLOADI, TTSFPMAD, TTSFPMOV, TTSFPMUL, TTSFPNOP, TTSFPSHFT,
  TTSFPSETCC, TTSFPSTORE, Reg,
  a0, a1, a2, a5, ra, s0, s1, s2, s3, s4, s5, s6, s7, s8, sp,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from ttk import Cb, Noc, Tensix  # noqa: E402
from ttk.cb import CB, CircularBuffer  # noqa: E402
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM, TriscLocalMem as TLM, TriscMailbox  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.sfpu import LReg, Sfpu, f32_bits  # noqa: E402
from ttk.tensix import Cfg, MopCfg, TensixL1, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait, ThreadCfg  # noqa: E402
import matmul_peak as mm  # noqa: E402


EMB_DIM = 2048
ROWS = 32
TILE = 32
DTYPE = Dtype.Float16_b
NORM_EPS = 1e-5
NORM_EPS_BF16_IMM = ((f32_bits(NORM_EPS) + 0x8000) >> 16) & 0xFFFF

# Bringup decomposition for a single Llama row:
#   2048 hidden elements = two 1024-element chunks.
# Each chunk is 32 TT tiles wide if the row block is represented as a 32x2048
# tile row.  The mean does not need to spill to DRAM: reduce x*x over width on
# the compute core using AVG + REDUCE_ROW, then keep the one-column result for
# rsqrt and broadcast multiply.
CHUNK_ELEMS = 1024
CHUNKS = EMB_DIM // CHUNK_ELEMS
COL_TILES = EMB_DIM // TILE
CHUNK_COL_TILES = CHUNK_ELEMS // TILE
TILE_BYTES = DTYPE.tile_size
OUT_CB = 16
CB_DEPTH = 16

SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
SYNC_L1 = SCRATCH_L1 + 0x24000
SYNC_TRISC_START = SYNC_L1
SYNC_READ = SYNC_L1 + 4
SYNC_DONE0 = SYNC_L1 + 8
SYNC_DONE1 = SYNC_L1 + 12
SYNC_DONE2 = SYNC_L1 + 16
SYNC_TRISC_INIT = SYNC_L1 + 20
SYNC = mm.RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)

STALL_MATH_PACK_ROOM = TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU
STALL_MATH_PACK_DATA = TensixStall.TDMA
WAIT_MATH_AND_SFPU = TensixWait.MATH | TensixWait.SFPU
WAIT_THCON_AND_PACK = TensixWait.THCON | TensixWait.PACK0

UNPACK_SRC_A = TTUNPACR(0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1)
UNPACK_SRC_B = TTUNPACR(1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1)
UNPACK_NOP = TTUNPACR_NOP(Unpacker_Select=1, Set_Dvalid=1, Unpack_Pop=1)
MATH_MOVA2D = TTMOVA2D(addr_mode=2, instr_mod=2)

UNPACK_NONE_MOP = MopCfg(
  loop_outer=2,
  loop_inner=2,
  template=[TTNOP(), TTNOP(), TTNOP(), UNPACK_SRC_A, UNPACK_SRC_B, UNPACK_SRC_B, UNPACK_SRC_B],
)
UNPACK_ROW_MOP = MopCfg(
  loop_outer=2,
  loop_inner=2,
  template=[TTNOP(), TTSETADCZW(2, 0, 0, 0, 0, 1), TTNOP(), UNPACK_SRC_B, UNPACK_SRC_A, UNPACK_SRC_A, UNPACK_SRC_A],
)
UNPACK_COL_MOP = MopCfg(
  loop_outer=2,
  loop_inner=2,
  template=[UNPACK_SRC_B, TTSETADCZW(2, 0, 0, 0, 2, 1), TTNOP(), UNPACK_SRC_A, TTNOP(), UNPACK_SRC_A, UNPACK_SRC_A],
)
UNPACK_SINGLE_MOP = MopCfg(
  loop_outer=4,
  loop_inner=1,
  template=[
    TTUNPACR(AddrMode=1, OvrdThreadId=1, SetDatValid=1, Last=1),
    TTNOP(), TTNOP(),
    UNPACK_NOP,
    TTNOP(),
    UNPACK_NOP,
    UNPACK_NOP,
  ],
)
MATH_MOVA2D_MOP = MopCfg(
  loop_outer=4,
  loop_inner=2,
  template=[
    TTNOP(),
    TTSETRWC(clear_ab_vld=3, BitMask=3),
    TTNOP(),
    MATH_MOVA2D,
    TTNOP(),
    MATH_MOVA2D,
    MATH_MOVA2D,
  ],
)

PACK_MOP_CFG = MopCfg(
  loop_outer=4,
  loop_inner=4,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    TTPACR(), TTNOP(), TTPACR(AddrMode=1, Last=1), TTPACR(AddrMode=2),
  ],
)

BCAST_NONE = 0
BCAST_COL = 1
BCAST_ROW = 2
SETRWC_CLR_AB = TTSETRWC(3, 3, 0, 0, 0, 3)
SETRWC_CLR_A = TTSETRWC(1, 3, 0, 0, 0, 3)
SETRWC_CLR_B_BETWEEN = TTSETRWC(2, 0, 0, 0, 0, 0)
SETRWC_CLR_B_SETD = TTSETRWC(2, 0, 0, 0, 0, 4)
ELW_ADDR_MOD = 2


class _RoleKernel(KernelBase):
  def _loop_epilogue(self):
    return self.ret()

  @contextmanager
  def tile_loop(self, name: str, *, count: Reg = s3, counter: Reg = s5) -> Iterator[None]:
    self.li(counter, 0)
    self.label(f"{name}_loop")
    self.beq(counter, count, f"{name}_done")
    yield
    self.addi(counter, counter, 1)
    self.j(f"{name}_loop")
    self.label(f"{name}_done")
    self._loop_epilogue()


class Trisc(_RoleKernel, Tensix, Cb):
  NUM_TRISC = 3

  def __init__(self, thread_id: int, sync=SYNC, *, base_addr: int = 0):
    super().__init__(base_addr=base_addr)
    self.thread_id = thread_id
    self.sync = sync
    self.data = TriscMailbox.DATA1 if thread_id == 1 else TriscMailbox.DATA_COMMON
    from ttk.math import Math
    from ttk.pack import Pack
    from ttk.unpack import Unpack
    self.unpack = Unpack(self)
    self.pack = Pack(self)
    self.math = Math(self)

  def prologue(self):
    self.addi(sp, sp, -16)
    self.sw(ra, sp, 12)
    self.read32(t0, self.data["rta_l1_base"])
    self.lw(s3, t0, 0)
    self.wait8(self.sync.start + self.thread_id, 1)
    self.write8(self.sync.start + self.thread_id, 0)
    return self

  def init_barrier(self):
    self.write32(self.sync.trisc_init + self.thread_id * 4, 1)
    self.fence()
    self.li(t1, 1)
    for init_id in range(self.NUM_TRISC):
      self.wait_sync_value(self.sync.trisc_init + init_id * 4, t1, actual=t2)
    return self

  def _loop_epilogue(self):
    return self.ret_kernel()

  def tile_loop(self, *, count: Reg = s3, counter: Reg = s5) -> Iterator[None]:
    return super().tile_loop(f"trisc{self.thread_id}", count=count, counter=counter)


class Brisc(_RoleKernel, Noc, Cb):
  pass


class Ncrisc(_RoleKernel, Noc, Cb):
  pass


def _elwmul_math_mop(bcast: int) -> tuple[MopCfg, int, int, object | None, object | None]:
  if bcast == BCAST_NONE:
    e = TTELWMUL(0, 0, BCAST_NONE, ELW_ADDR_MOD, 0)
    return (
      MopCfg(loop_outer=4, loop_inner=2, template=[TTNOP(), SETRWC_CLR_AB, TTNOP(), e, TTNOP(), e, e]),
      0x0808,
      1,
      None,
      None,
    )
  if bcast == BCAST_COL:
    e = TTELWMUL(0, 0, BCAST_COL, ELW_ADDR_MOD, 0)
    return (
      MopCfg(loop_outer=2, loop_inner=2, template=[TTNOP(), SETRWC_CLR_A, TTNOP(), e, TTNOP(), e, e]),
      0x0808,
      2,
      SETRWC_CLR_B_BETWEEN,
      SETRWC_CLR_B_SETD,
    )
  if bcast == BCAST_ROW:
    e = TTELWMUL(0, 0, BCAST_ROW, ELW_ADDR_MOD, 0)
    return (
      MopCfg(loop_outer=4, loop_inner=2, template=[TTNOP(), SETRWC_CLR_AB, TTNOP(), e, TTNOP(), e, e]),
      0x0008,
      1,
      None,
      None,
    )
  raise ValueError(f"unsupported bcast mode {bcast}")


def _unpack_mop_for_bcast(bcast: int) -> MopCfg:
  if bcast == BCAST_NONE:
    return UNPACK_NONE_MOP
  if bcast == BCAST_COL:
    return UNPACK_COL_MOP
  if bcast == BCAST_ROW:
    return UNPACK_ROW_MOP
  raise ValueError(f"unsupported bcast mode {bcast}")


def _write_trisc1_dest_offset_instr(fw, offset_id=t1, instr=t2, base=t3):
  fw.sltu(instr, zero, offset_id)
  fw.slli(instr, instr, 9)
  fw.li(base, 0xB2010000)
  fw.add(instr, instr, base)
  return fw.write32(TensixRegs.INSTRN_BUF_BASE, instr, tmp_addr=t0)


def _dram_tile_addr_static_bytes(fw, bank_coords: list[int]):
  fw.mv(t0, a1)
  fw.remu(a1, t0, a2)
  fw.divu(t0, t0, a2)
  fw.li(t1, TILE_BYTES)
  fw.mul(t0, t0, t1)
  fw.add(a0, a0, t0)
  fw.li(a2, bank_coords[0])
  for bank, coord in enumerate(bank_coords[1:], start=1):
    next_bank = fw._new_label("dram_static_bank")
    fw.li(t1, bank)
    fw.bne(a1, t1, next_bank)
    fw.li(a2, coord)
    fw.label(next_bank)
  return fw


def _tile_index(fw, base: Reg, stride: Reg, *, out: Reg = a1):
  fw.mul(out, s5, stride)
  return fw.add(out, base, out)


def _elwmul_brisc(dram_bank_coords: list[int], b_tile_policy: str) -> Brisc:
  if b_tile_policy not in ("same", "linear", "fixed"):
    raise ValueError("b_tile_policy must be same, linear, or fixed")
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s6, s7, s8))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)

  with fw.tile_loop("brisc", count=s4):
    for cb_id in (0, 1):
      fw.cb_reserve_back(BM.CB_INTERFACE, cb_id)
      if cb_id == 0:
        fw.mv(a0, s0)
        _tile_index(fw, s1, s7)
      else:
        fw.mv(a0, s2)
        if b_tile_policy == "same":
          _tile_index(fw, s1, s7)
        elif b_tile_policy == "linear":
          _tile_index(fw, s3, s8)
        else:
          fw.mv(a1, s3)
      fw.mv(a2, s6)
      _dram_tile_addr_static_bytes(fw, dram_bank_coords)
      fw.local_noc0_coord(a5)
      fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      fw.addi(t4, t4, 1)
      fw.cb_write_ptr(BM.CB_INTERFACE, cb_id, out=t5)
      fw.li(t6, TILE_BYTES)
      fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
      fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
      fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      wait = fw._new_label("brisc_read_wait")
      fw.label(wait)
      fw.lw(t1, t0, 0)
      fw.bltu(t1, t4, wait)
      fw.fence()
      fw.cb_push_back(BM.CB_INTERFACE, cb_id)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_READ, t2)
  return fw


def _elwmul_ncrisc(dram_bank_coords: list[int]) -> Ncrisc:
  fw = Ncrisc()
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4, s6))
  with fw.tile_loop("ncrisc", count=s3):
    fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
    _tile_index(fw, s2, s6)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    _dram_tile_addr_static_bytes(fw, dram_bank_coords)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
    fw.addi(t4, t4, 1)
    fw.cb_read_ptr(NM.CB_INTERFACE, OUT_CB, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_write(1, 0, t5, a0, 0, a2, t6, a=t0, v=t1)
    fw.noc_write_barrier(1, t4, addr=t0, val=t1)
    fw.cb_pop_front(NM.CB_INTERFACE, OUT_CB)
  return fw


def _elwmul_trisc0(bcast: int) -> Trisc:
  fw = Trisc(0, SYNC)
  fw.prologue()
  fw.unpack.init(dtype=DTYPE, tile_bytes=TILE_BYTES, mop_cfg=_unpack_mop_for_bcast(bcast))
  fw.init_barrier()
  sec0 = Cfg.THCON_SEC0_REG3_Base_address.addr32
  sec1 = Cfg.THCON_SEC1_REG3_Base_address.addr32

  with fw.tile_loop():
    fw.cb_wait_front(fw.data["cb_interface"], 0)
    fw.cb_wait_front(fw.data["cb_interface"], 1)
    fw.cb_read_ptr(fw.data["cb_interface"], 0, out=s0)
    fw.cb_read_ptr(fw.data["cb_interface"], 1, out=s1)
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
    fw.li(t2, TensixRegs.CFG_BASE + sec0 * 4)
    a_done = fw._new_label("sec0_done")
    fw.beq(t1, zero, a_done)
    fw.addi(t2, t2, 4)
    fw.label(a_done)
    fw.addi(t3, s0, -1)
    fw.sw(t3, t2, 0)
    fw.li(t2, TensixRegs.CFG_BASE + sec1 * 4)
    b_done = fw._new_label("sec1_done")
    fw.beq(t1, zero, b_done)
    fw.addi(t2, t2, 4)
    fw.label(b_done)
    fw.addi(t3, s1, -1)
    fw.sw(t3, t2, 0)
    fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
    fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, t2)
    ctx1 = fw._new_label("set_ctx1")
    ctx_set = fw._new_label("ctx_set")
    fw.beq(t1, zero, ctx1)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
    fw.j(ctx_set)
    fw.label(ctx1)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
    fw.label(ctx_set)
    fw.cb_pop_front(fw.data["cb_interface"], 0, tensix_ack=True)
    fw.cb_pop_front(fw.data["cb_interface"], 1, tensix_ack=True)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE0, t2)
  return fw


def _elwmul_trisc1(bcast: int) -> Trisc:
  math_mop, addr_mod_ab, mop_runs, between_runs, post_mop = _elwmul_math_mop(bcast)
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=math_mop)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC2_Src, addr_mod_ab)
  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    _write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTZEROACC(3, 0, 0, 1, 0))
    fw.emit(TTSTALLWAIT(TensixStall.MATH, TensixWait.SRCA_VLD | TensixWait.SRCB_VLD))
    for run in range(mop_runs):
      if run and between_runs is not None:
        fw.emit(between_runs)
      fw.emit(TTMOP(1, 0, 0))
    if post_mop is not None:
      fw.emit(post_mop)
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
    _write_trisc1_dest_offset_instr(fw, t2, t1, t3)
  return fw


def _elwmul_trisc2() -> Trisc:
  fw = Trisc(2, SYNC)
  fw.prologue()
  fw.pack.init(dtype=DTYPE, out_cb=OUT_CB, mop_cfg=PACK_MOP_CFG)
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
    fw.cb_iface(fw.data["cb_interface"], OUT_CB, out=t6)
    fw.lw(t1, t6, 24)
    fw.cb_counter_high(t1, t1)
    fw.slli(t1, t1, 8)
    fw.li(t2, TTSETDMAREG(0, 0, 0, 48).raw_word())
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
    fw.emit(TTSTALLWAIT(TensixStall.THCON, TensixWait.PACK0))
    fw.push_tensix(TTSTOREREG(24, ((CB.SYNC_TILES_RECEIVED_BASE + OUT_CB * CB.SYNC_STRIDE) >> 2) & 0x3FFFF))
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


def _unary_brisc(dram_bank_coords: list[int]) -> Brisc:
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)

  with fw.tile_loop("brisc", count=s2):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.mv(a0, s0)
    _tile_index(fw, s1, s4)
    fw.mv(a2, s3)
    _dram_tile_addr_static_bytes(fw, dram_bank_coords)
    fw.local_noc0_coord(a5)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.addi(t4, t4, 1)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
    fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    wait = fw._new_label("brisc_read_wait")
    fw.label(wait)
    fw.lw(t1, t0, 0)
    fw.bltu(t1, t4, wait)
    fw.fence()
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_READ, t2)
  return fw


def _rsqrt_trisc0() -> Trisc:
  fw = Trisc(0, SYNC)
  fw.prologue()
  fw.unpack.init(dtype=DTYPE, tile_bytes=TILE_BYTES, mop_cfg=UNPACK_SINGLE_MOP)
  fw.init_barrier()

  with fw.tile_loop():
    fw.cb_wait_front(fw.data["cb_interface"], 0)
    fw.cb_read_ptr(fw.data["cb_interface"], 0, out=s0)
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
    fw.li(t2, TensixRegs.CFG_BASE + Cfg.THCON_SEC0_REG3_Base_address.addr32 * 4)
    cfg_addr_done = fw._new_label("trisc0_cfg_addr_done")
    fw.beq(t1, zero, cfg_addr_done)
    fw.addi(t2, t2, 4)
    fw.label(cfg_addr_done)
    fw.addi(t3, s0, -1)
    fw.sw(t3, t2, 0)
    fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
    fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, t2)
    ctx1 = fw._new_label("set_ctx1")
    ctx_set = fw._new_label("ctx_set")
    fw.beq(t1, zero, ctx1)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
    fw.j(ctx_set)
    fw.label(ctx1)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
    fw.label(ctx_set)
    fw.cb_pop_front(fw.data["cb_interface"], 0, tensix_ack=True)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE0, t2)
  return fw


def _emit_rsqrt_eps_replay_row(fw: Trisc) -> Trisc:
  # Blackhole ckernel_sfpu_rsqrt.h calculate_rsqrt, with an extra bf16 eps add
  # after loading the DST row group into L1.
  fw.emit(TTREPLAY(0, 32, 1, 1))
  fw.emit(TTSFPLOAD(int(LReg.L1), 0, 7, 0))
  fw.emit(TTSFPADDI(NORM_EPS_BF16_IMM, int(LReg.L1), 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPSHFT(0xFFF, int(LReg.L1), int(LReg.L0), 5))
  fw.emit(TTSFPIADD(0x000, int(LReg.PRGM0), int(LReg.L0), 6))
  fw.emit(TTSFPMUL(int(LReg.L1), int(LReg.L0), int(LReg.CONST_0), int(LReg.L2), 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMUL(int(LReg.L0), int(LReg.L2), int(LReg.CONST_0), int(LReg.L2), 1))
  fw.emit(TTSFPLOADI(int(LReg.L3), 0, 32640))
  fw.emit(TTSFPADD(int(LReg.CONST_1), int(LReg.PRGM2), int(LReg.L2), int(LReg.L4), 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMAD(int(LReg.L2), int(LReg.L4), int(LReg.PRGM1), int(LReg.L2), 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMUL(int(LReg.L0), int(LReg.L2), int(LReg.CONST_0), int(LReg.L0), 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMUL(int(LReg.L1), int(LReg.L0), int(LReg.CONST_0), int(LReg.L2), 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPMAD(int(LReg.L0), int(LReg.L2), int(LReg.CONST_1), int(LReg.L2), 1))
  fw.emit(TTSFPDIVP2(0xFFF, int(LReg.L0), int(LReg.L5), 1))
  fw.emit(TTSFPMOV(0x000, int(LReg.L1), int(LReg.L4), 2))
  fw.emit(TTSFPIADD(0x000, int(LReg.L3), int(LReg.L4), 6))
  fw.emit(TTSFPSETCC(0x000, int(LReg.L4), 0, 2))
  fw.emit(TTSFPSETCC(0x000, int(LReg.L1), 0, 2))
  fw.emit(TTSFPMAD(int(LReg.L2), int(LReg.L5), int(LReg.L0), int(LReg.L0), 0))
  fw.emit(TTSFPCOMPC(0, 0, 0, 0))
  fw.emit(TTSFPMOV(0x000, int(LReg.L4), int(LReg.L0), 0))
  fw.emit(TTSFPENCC(0x003, 0, 0, 10))
  fw.emit(TTSFPSETCC(0x000, int(LReg.L1), 0, 0))
  fw.emit(TTSFPLOADI(int(LReg.L0), 0, 32704))
  fw.emit(TTSFPENCC(0x003, 0, 0, 10))
  fw.emit(TTSFPSTORE(int(LReg.L0), 0, 7, 0))
  fw.emit(TTINCRWC(0, 2, 0, 0))
  for _ in range(7):
    fw.emit(TTREPLAY(0, 32, 0, 0))
  fw.emit(TTSETRWC(0, 4, 8, 0, 0, 4))
  return fw.emit(TTSETRWC(0, 4, 8, 0, 0, 4))


def _rsqrt_trisc1() -> Trisc:
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=MATH_MOVA2D_MOP)
  sfpu = Sfpu(fw)
  sfpu.load_imm32(LReg.L0, 0x5F1110A0)
  sfpu.set_config_from_l0(LReg.PRGM0)
  sfpu.set_program_const(LReg.PRGM1, 2.2825186)
  sfpu.set_program_const(LReg.PRGM2, 2.2533049)
  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    _write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    _write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    for _ in range(4):
      _emit_rsqrt_eps_replay_row(fw)
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
    _write_trisc1_dest_offset_instr(fw, t2, t1, t3)
  return fw


def _build_rsqrt_program(
  in_addr: int,
  out_addr: int,
  num_banks: int,
  *,
  core: tuple[int, int],
  tiles: int,
  in_base: int = 0,
  out_base: int = 0,
  in_stride: int = 1,
  out_stride: int = 1,
  dram_bank_coords_noc0: list[int] | None = None,
  dram_bank_coords_noc1: list[int] | None = None,
) -> Program:
  if dram_bank_coords_noc0 is None:
    dram_bank_coords_noc0 = mm.p100_dram_bank_endpoint_coords(None, 0)[:num_banks]
  if dram_bank_coords_noc1 is None:
    dram_bank_coords_noc1 = mm.p100_dram_bank_endpoint_coords(None, 1)[:num_banks]
  brisc_fw = _unary_brisc(dram_bank_coords_noc0)
  ncrisc_fw = _elwmul_ncrisc(dram_bank_coords_noc1)
  trisc0_fw = _rsqrt_trisc0()
  trisc1_fw = _rsqrt_trisc1()
  trisc2_fw = _elwmul_trisc2()

  brisc_fw.rta(lambda _x, _y: [in_addr, in_base, tiles, num_banks, in_stride])
  ncrisc_fw.rta(lambda _x, _y: [out_addr, out_base, tiles, num_banks, out_stride])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "llama3_rmsnorm_rsqrt"
  return prog


def _build_elwmul_program(
  a_addr: int,
  b_addr: int,
  out_addr: int,
  num_banks: int,
  *,
  core: tuple[int, int],
  tiles: int,
  bcast: int,
  b_tile_policy: str,
  a_base: int = 0,
  b_base: int = 0,
  out_base: int = 0,
  a_stride: int = 1,
  b_stride: int = 1,
  out_stride: int = 1,
  dram_bank_coords_noc0: list[int] | None = None,
  dram_bank_coords_noc1: list[int] | None = None,
) -> Program:
  if dram_bank_coords_noc0 is None:
    dram_bank_coords_noc0 = mm.p100_dram_bank_endpoint_coords(None, 0)[:num_banks]
  if dram_bank_coords_noc1 is None:
    dram_bank_coords_noc1 = mm.p100_dram_bank_endpoint_coords(None, 1)[:num_banks]
  brisc_fw = _elwmul_brisc(dram_bank_coords_noc0, b_tile_policy)
  ncrisc_fw = _elwmul_ncrisc(dram_bank_coords_noc1)
  trisc0_fw = _elwmul_trisc0(bcast)
  trisc1_fw = _elwmul_trisc1(bcast)
  trisc2_fw = _elwmul_trisc2()

  brisc_fw.rta(lambda _x, _y: [a_addr, a_base, b_addr, b_base, tiles, num_banks, a_stride, b_stride])
  ncrisc_fw.rta(lambda _x, _y: [out_addr, out_base, tiles, num_banks, out_stride])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (1, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "llama3_rmsnorm_elwmul"
  return prog


@dataclass(frozen=True)
class ReduceRowMeanPlan:
  """The TT-side shape of the RMSNorm mean-of-squares step.

  TT-Metal's reduce helpers use the matmul path for SUM/AVG + REDUCE_ROW.  That
  means the scaler tile is not row-0 filled like ordinary reduce_tile; it is
  col-0 filled.  For RMSNorm over width=2048, each tile contributes
  sum(x^2 tile row) * (1 / 2048), accumulated in DST column 0.
  """

  width: int = EMB_DIM
  col_tiles: int = COL_TILES
  chunk_elems: int = CHUNK_ELEMS
  chunk_col_tiles: int = CHUNK_COL_TILES
  chunks: int = CHUNKS
  reduce_dim: str = "REDUCE_ROW"
  pool_type: str = "AVG"
  scaler_layout: str = "col0"

  @property
  def scaler(self) -> float:
    return 1.0 / float(self.width)


def bf16_round(x: np.ndarray) -> np.ndarray:
  """Round through bf16 using the same helper path as the matmul bringup."""
  return mm.from_device_bytes(mm.to_device_bytes(x, DTYPE), DTYPE, x.shape)


def rmsnorm_reference(x: np.ndarray, weight: np.ndarray, eps: float = NORM_EPS) -> np.ndarray:
  if x.shape[-1] != EMB_DIM:
    raise ValueError(f"x last dim must be {EMB_DIM}, got {x.shape[-1]}")
  if weight.shape != (EMB_DIM,):
    raise ValueError(f"weight must have shape ({EMB_DIM},), got {weight.shape}")
  x32 = x.astype(np.float32, copy=False)
  w32 = weight.astype(np.float32, copy=False)
  inv_rms = 1.0 / np.sqrt(np.mean(x32 * x32, axis=-1, keepdims=True) + np.float32(eps))
  return (x32 * inv_rms * w32).astype(np.float32)


def rmsnorm_two_chunk_reference(x: np.ndarray, weight: np.ndarray, eps: float = NORM_EPS) -> np.ndarray:
  """Same math as rmsnorm_reference, staged as two 1024-element partial means."""
  if x.shape[-1] != EMB_DIM:
    raise ValueError(f"x last dim must be {EMB_DIM}, got {x.shape[-1]}")
  x32 = x.astype(np.float32, copy=False)
  chunks = x32.reshape(*x32.shape[:-1], CHUNKS, CHUNK_ELEMS)
  partial_means = np.mean(chunks * chunks, axis=-1)
  mean_square = np.mean(partial_means, axis=-1, keepdims=True)
  inv_rms = 1.0 / np.sqrt(mean_square + np.float32(eps))
  return (x32 * inv_rms * weight.astype(np.float32, copy=False)).astype(np.float32)


def reduce_row_avg_scaler_tile(width: int = EMB_DIM) -> np.ndarray:
  """Return the row-major view of the col-0 scaler tile for AVG+REDUCE_ROW."""
  if width <= 0:
    raise ValueError("width must be positive")
  tile = np.zeros((TILE, TILE), dtype=np.float32)
  tile[:, 0] = np.float32(1.0 / float(width))
  return tile


def reduce_row_avg_scaler_matrix(width: int = EMB_DIM, out_cols: int = TILE) -> np.ndarray:
  """Matmul-reduce scaler: `(width, 32)` with only output column 0 nonzero."""
  if width != EMB_DIM:
    raise ValueError(f"this bringup is hardcoded for width={EMB_DIM}")
  scaler = np.zeros((width, out_cols), dtype=np.float32)
  scaler[:, 0] = np.float32(1.0 / float(width))
  return bf16_round(scaler)


def make_inputs(seed: int = 0, rows: int = ROWS) -> tuple[np.ndarray, np.ndarray]:
  rng = np.random.default_rng(seed)
  x = rng.normal(0.0, 0.2, size=(rows, EMB_DIM)).astype(np.float32)
  weight = rng.normal(1.0, 0.02, size=(EMB_DIM,)).astype(np.float32)
  return bf16_round(x), bf16_round(weight)


def check_result(got: np.ndarray, ref: np.ndarray, *, max_abs: float, max_rel_l2: float) -> tuple[float, float]:
  if not np.isfinite(got).all():
    raise AssertionError("RMSNorm output contains non-finite values")
  diff = got.astype(np.float64, copy=True) - ref.astype(np.float64, copy=True)
  abs_err = np.abs(diff)
  rel_l2 = float(np.linalg.norm(diff.reshape(-1)) / (np.linalg.norm(ref.astype(np.float64, copy=False).reshape(-1)) + 1e-12))
  worst = float(np.max(abs_err))
  if worst > max_abs or rel_l2 > max_rel_l2:
    idx = tuple(int(i) for i in np.unravel_index(int(np.argmax(abs_err)), abs_err.shape))
    raise AssertionError(
      f"RMSNorm mismatch max_abs={worst:.6g} rel_l2={rel_l2:.6g} "
      f"worst={idx} got={got[idx]:.8g} ref={ref[idx]:.8g}"
    )
  return worst, rel_l2


def run_host_test(seed: int, rows: int, max_abs: float, max_rel_l2: float) -> None:
  x, weight = make_inputs(seed, rows)
  ref = rmsnorm_reference(x, weight)
  got = rmsnorm_two_chunk_reference(x, weight)
  worst, rel_l2 = check_result(got, ref, max_abs=max_abs, max_rel_l2=max_rel_l2)
  print(f"host-rmsnorm-two-chunk: ok rows={rows} max_abs={worst:.6g} rel_l2={rel_l2:.6g}")


def _ceil32(x: int) -> int:
  return ((x + TILE - 1) // TILE) * TILE


def _alloc_matrix(device: Device, data: np.ndarray, name: str):
  rows, cols = map(_ceil32, data.shape)
  padded = np.zeros((rows, cols), dtype=np.float32)
  padded[:data.shape[0], :data.shape[1]] = data.astype(np.float32, copy=False)
  return device.alloc_write(mm.to_device_bytes(padded, DTYPE), dtype=DTYPE, shape=padded.shape, name=name), padded


def _alloc_empty(device: Device, shape: tuple[int, int], name: str):
  rows, cols = map(_ceil32, shape)
  return device.dram.alloc((rows // TILE) * (cols // TILE), dtype=DTYPE, shape=(rows, cols), name=name)


def _run_matmul(
  device: Device,
  *,
  a_buf,
  b_buf,
  c_buf,
  m: int,
  k: int,
  n: int,
  cores: list[tuple[int, int]],
  name: str,
) -> list[dict]:
  num_banks = len(device.dram.bank_tiles)
  chunks = mm.plan_output_chunks(m, k, n, cores, num_banks)
  mp, kp, npad = mm.global_padded_shape(m, k, n, chunks)
  if a_buf.shape != (mp, kp):
    raise ValueError(f"{name}: A shape {a_buf.shape} does not match padded {(mp, kp)}")
  if b_buf.shape != (kp, npad):
    raise ValueError(f"{name}: B shape {b_buf.shape} does not match padded {(kp, npad)}")
  if c_buf.shape != (mp, npad):
    raise ValueError(f"{name}: C shape {c_buf.shape} does not match padded {(mp, npad)}")

  layout_base = dict(a_row_stride=kp // TILE, b_row_stride=npad // TILE, c_row_stride=npad // TILE)
  coords0 = mm.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0)[:num_banks]
  coords1 = mm.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1)[:num_banks]
  timings = []
  for idx, chunk in enumerate(chunks):
    layout = mm.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      **layout_base,
    )
    prog = mm.build_program(
      chunk.plan,
      a_buf.addr,
      b_buf.addr,
      c_buf.addr,
      num_banks,
      layout,
      dram_bank_coords_noc0=coords0,
      dram_bank_coords_noc1=coords1,
    )
    prog.name = name if len(chunks) == 1 else f"{name}_chunk{idx}"
    timings.extend(device.run(prog))
  return timings


def _read_matrix(device: Device, buf, shape: tuple[int, int]) -> np.ndarray:
  full = mm.from_device_bytes(device.dram_read(buf), buf.dtype, buf.shape)
  return np.array(full[:shape[0], :shape[1]], dtype=np.float32, copy=True)


def _run_elwmul_device(
  device: Device,
  a_buf,
  b_buf,
  out_buf,
  *,
  tiles: int,
  bcast: int,
  b_tile_policy: str,
  name: str,
  a_base: int = 0,
  b_base: int = 0,
  out_base: int = 0,
  a_stride: int = 1,
  b_stride: int = 1,
  out_stride: int = 1,
):
  num_banks = len(device.dram.bank_tiles)
  core = device.cores[0]
  prog = _build_elwmul_program(
    a_buf.addr,
    b_buf.addr,
    out_buf.addr,
    num_banks,
    core=core,
    tiles=tiles,
    bcast=bcast,
    b_tile_policy=b_tile_policy,
    a_base=a_base,
    b_base=b_base,
    out_base=out_base,
    a_stride=a_stride,
    b_stride=b_stride,
    out_stride=out_stride,
    dram_bank_coords_noc0=mm.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0)[:num_banks],
    dram_bank_coords_noc1=mm.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1)[:num_banks],
  )
  prog.name = name
  return device.run(prog)


def _run_rsqrt_device(
  device: Device,
  in_buf,
  out_buf,
  *,
  tiles: int,
  name: str,
  in_base: int = 0,
  out_base: int = 0,
  in_stride: int = 1,
  out_stride: int = 1,
):
  num_banks = len(device.dram.bank_tiles)
  core = device.cores[0]
  prog = _build_rsqrt_program(
    in_buf.addr,
    out_buf.addr,
    num_banks,
    core=core,
    tiles=tiles,
    in_base=in_base,
    out_base=out_base,
    in_stride=in_stride,
    out_stride=out_stride,
    dram_bank_coords_noc0=mm.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0)[:num_banks],
    dram_bank_coords_noc1=mm.p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1)[:num_banks],
  )
  prog.name = name
  return device.run(prog)


def _crumb(msg: str) -> None:
  print(f"[rmsnorm] {msg}", flush=True)


def run_rsqrt_device_test(seed: int, max_abs: float, max_rel_l2: float) -> None:
  rng = np.random.default_rng(seed)
  x = bf16_round(rng.uniform(0.02, 4.0, size=(TILE, TILE)).astype(np.float32))
  ref = bf16_round((1.0 / np.sqrt(x + np.float32(NORM_EPS))).astype(np.float32))
  _crumb(f"rsqrt-device-test seed={seed}")
  device = Device()
  try:
    in_buf, _ = _alloc_matrix(device, x, "rsqrt_in")
    out_buf = _alloc_empty(device, (TILE, TILE), "rsqrt_out")
    _crumb("launch rsqrt eps tile")
    _run_rsqrt_device(device, in_buf, out_buf, tiles=1, name="rmsnorm_rsqrt_eps")
    got = _read_matrix(device, out_buf, (TILE, TILE))
    worst, rel_l2 = check_result(got, ref, max_abs=max_abs, max_rel_l2=max_rel_l2)
    print(f"rsqrt-device: ok max_abs={worst:.6g} rel_l2={rel_l2:.6g}")
  finally:
    device.close()


def run_broadcast_device_test(seed: int, max_abs: float, max_rel_l2: float) -> None:
  rng = np.random.default_rng(seed)
  a = bf16_round(rng.uniform(-2.0, 2.0, size=(TILE, TILE)).astype(np.float32))
  b = bf16_round(rng.uniform(0.25, 2.0, size=(TILE, TILE)).astype(np.float32))
  cases = (
    ("none", BCAST_NONE, "linear", bf16_round(a * b)),
    ("col", BCAST_COL, "fixed", bf16_round(a * b[:, :1])),
    ("row", BCAST_ROW, "fixed", bf16_round(a * b[:1, :])),
  )

  _crumb(f"broadcast-device-test seed={seed}")
  device = Device()
  try:
    a_buf, _ = _alloc_matrix(device, a, "bcast_a")
    b_buf, _ = _alloc_matrix(device, b, "bcast_b")
    out_buf = _alloc_empty(device, (TILE, TILE), "bcast_out")
    for name, bcast, policy, ref in cases:
      _crumb(f"launch bcast {name}")
      _run_elwmul_device(
        device,
        a_buf,
        b_buf,
        out_buf,
        tiles=1,
        bcast=bcast,
        b_tile_policy=policy,
        name=f"rmsnorm_bcast_{name}",
      )
      got = _read_matrix(device, out_buf, (TILE, TILE))
      worst, rel_l2 = check_result(got, ref, max_abs=max_abs, max_rel_l2=max_rel_l2)
      print(f"broadcast-{name}: ok max_abs={worst:.6g} rel_l2={rel_l2:.6g}")
  finally:
    device.close()


def run_rmsnorm_device_pipeline_test(seed: int, max_abs: float, max_rel_l2: float) -> None:
  mm.configure_numeric_path(input_dtype=DTYPE, output_dtype=DTYPE, intermediate_dtype=DTYPE)
  x, weight = make_inputs(seed, ROWS)
  ref_full = rmsnorm_reference(x, weight)
  _crumb(f"rmsnorm-device-pipeline seed={seed} rows={ROWS} tiles={COL_TILES}")

  device = Device()
  try:
    run_cores = [device.cores[0]]
    num_banks = len(device.dram.bank_tiles)
    chunks = mm.plan_output_chunks(ROWS, EMB_DIM, TILE, run_cores, num_banks)
    mp, kp, npad = mm.global_padded_shape(ROWS, EMB_DIM, TILE, chunks)
    _crumb(f"planned padded shapes x=({mp},{kp}) mean=({mp},{npad})")

    x_pad = np.zeros((mp, kp), dtype=np.float32)
    x_pad[:ROWS, :EMB_DIM] = x
    zero_x = np.zeros((mp, kp), dtype=np.float32)
    scaler_pad = np.zeros((kp, npad), dtype=np.float32)
    scaler_pad[:EMB_DIM, 0] = np.float32(1.0 / float(EMB_DIM))
    scaler_pad = bf16_round(scaler_pad)

    gamma_pad = np.zeros((mp, kp), dtype=np.float32)
    gamma_pad[0, :EMB_DIM] = weight
    gamma_pad = bf16_round(gamma_pad)

    _crumb("allocating pipeline buffers")
    x_buf = device.alloc_write(mm.to_device_bytes(x_pad, DTYPE), dtype=DTYPE, shape=x_pad.shape, name="rmsnorm_x")
    x2_buf = device.alloc_write(mm.to_device_bytes(zero_x, DTYPE), dtype=DTYPE, shape=zero_x.shape, name="rmsnorm_x2")
    scaler_buf = device.alloc_write(mm.to_device_bytes(scaler_pad, DTYPE), dtype=DTYPE, shape=scaler_pad.shape, name="rmsnorm_reduce_scaler")
    mean_buf = _alloc_empty(device, (mp, npad), "rmsnorm_mean")
    inv_tile_buf = _alloc_empty(device, (TILE, TILE), "rmsnorm_inv")
    tmp_buf = device.alloc_write(mm.to_device_bytes(zero_x, DTYPE), dtype=DTYPE, shape=zero_x.shape, name="rmsnorm_normed")
    gamma_buf = device.alloc_write(mm.to_device_bytes(gamma_pad, DTYPE), dtype=DTYPE, shape=gamma_pad.shape, name="rmsnorm_gamma")
    out_buf = device.alloc_write(mm.to_device_bytes(zero_x, DTYPE), dtype=DTYPE, shape=zero_x.shape, name="rmsnorm_out")

    _crumb("device square x*x")
    _run_elwmul_device(
      device,
      x_buf,
      x_buf,
      x2_buf,
      tiles=COL_TILES,
      bcast=BCAST_NONE,
      b_tile_policy="same",
      name="rmsnorm_square",
    )

    _crumb("device mean over hidden width")
    _run_matmul(
      device,
      a_buf=x2_buf,
      b_buf=scaler_buf,
      c_buf=mean_buf,
      m=mp,
      k=kp,
      n=npad,
      cores=run_cores,
      name="rmsnorm_mean_x2_reduce_row",
    )
    mean_full = _read_matrix(device, mean_buf, (ROWS, TILE))
    mean = mean_full[:, :1]

    _crumb("device eps + rsqrt(mean)")
    _run_rsqrt_device(
      device,
      mean_buf,
      inv_tile_buf,
      tiles=1,
      name="rmsnorm_rsqrt_mean",
    )

    _crumb("device col-broadcast x * inv_rms")
    _run_elwmul_device(
      device,
      x_buf,
      inv_tile_buf,
      tmp_buf,
      tiles=COL_TILES,
      bcast=BCAST_COL,
      b_tile_policy="fixed",
      name="rmsnorm_mul_inv",
    )

    _crumb("device row-broadcast normed * gamma")
    _run_elwmul_device(
      device,
      tmp_buf,
      gamma_buf,
      out_buf,
      tiles=COL_TILES,
      bcast=BCAST_ROW,
      b_tile_policy="linear",
      name="rmsnorm_mul_gamma",
    )

    got = _read_matrix(device, out_buf, (ROWS, EMB_DIM))
    # The current standalone ELWMUL path uses LoFi multiplication. Compare
    # against the mathematical reference with LoFi-sized tolerance for now.
    worst, rel_l2 = check_result(got, ref_full, max_abs=max_abs, max_rel_l2=max_rel_l2)
    mean_ref = np.mean(x.astype(np.float32) * x.astype(np.float32), axis=-1, keepdims=True)
    mean_worst, mean_rel = check_result(mean, mean_ref, max_abs=2e-2, max_rel_l2=8e-2)
    print(
      f"rmsnorm-device-pipeline: ok max_abs={worst:.6g} rel_l2={rel_l2:.6g} "
      f"mean_max_abs={mean_worst:.6g} mean_rel_l2={mean_rel:.6g}"
    )
  finally:
    device.close()


def run_mean_device_test(seed: int, rows: int, max_abs: float, max_rel_l2: float) -> None:
  if rows <= 0 or rows > ROWS:
    raise ValueError(f"--rows must be in [1, {ROWS}] for this first-cut device test")
  _crumb(f"mean-device-test seed={seed} rows={rows}")
  mm.configure_numeric_path(input_dtype=DTYPE, output_dtype=DTYPE, intermediate_dtype=DTYPE)
  x, _weight = make_inputs(seed, ROWS)
  x = x[:rows]
  x2 = bf16_round(x * x)
  logical_scaler = reduce_row_avg_scaler_matrix()
  expected_full = bf16_round(x2 @ logical_scaler)
  expected_mean = expected_full[:, :1]

  _crumb("opening device")
  device = Device()
  try:
    run_cores = [device.cores[0]]
    num_banks = len(device.dram.bank_tiles)
    chunks = mm.plan_output_chunks(ROWS, EMB_DIM, TILE, run_cores, num_banks)
    mp, kp, npad = mm.global_padded_shape(ROWS, EMB_DIM, TILE, chunks)
    _crumb(f"planned matmul mp={mp} kp={kp} npad={npad} cores={run_cores} banks={num_banks}")

    x2_pad = np.zeros((mp, kp), dtype=np.float32)
    x2_pad[:rows, :EMB_DIM] = x2
    scaler_pad = np.zeros((kp, npad), dtype=np.float32)
    scaler_pad[:EMB_DIM, 0] = np.float32(1.0 / float(EMB_DIM))
    scaler_pad = bf16_round(scaler_pad)

    _crumb("allocating DRAM buffers")
    x2_buf = device.alloc_write(mm.to_device_bytes(x2_pad, DTYPE), dtype=DTYPE, shape=x2_pad.shape, name="rmsnorm_x2")
    scaler_buf = device.alloc_write(
      mm.to_device_bytes(scaler_pad, DTYPE),
      dtype=DTYPE,
      shape=scaler_pad.shape,
      name="rmsnorm_reduce_scaler",
    )
    out_buf = _alloc_empty(device, (mp, npad), "rmsnorm_mean")
    _crumb(f"buffers x2=0x{x2_buf.addr:x} scaler=0x{scaler_buf.addr:x} out=0x{out_buf.addr:x}")
    _crumb("launching rmsnorm_mean_x2_reduce_row")
    timings = _run_matmul(
      device,
      a_buf=x2_buf,
      b_buf=scaler_buf,
      c_buf=out_buf,
      m=mp,
      k=kp,
      n=npad,
      cores=run_cores,
      name="rmsnorm_mean_x2_reduce_row",
    )
    _crumb("reading output")
    got_full = _read_matrix(device, out_buf, (rows, TILE))
    got_mean = got_full[:, :1]
    _crumb("checking output")
    worst, rel_l2 = check_result(got_mean, expected_mean, max_abs=max_abs, max_rel_l2=max_rel_l2)
    nonzero_tail = float(np.max(np.abs(got_full[:, 1:]))) if got_full.shape[1] > 1 else 0.0
    print(
      f"device-mean-x2: ok rows={rows} max_abs={worst:.6g} "
      f"rel_l2={rel_l2:.6g} tail_max={nonzero_tail:.6g}"
    )
    for timing in timings:
      name = f"{timing['name']}: " if timing.get("name") else ""
      print(f"  {name}{timing['us']:,.1f} us")
  finally:
    device.close()


def print_mean_plan() -> None:
  plan = ReduceRowMeanPlan()
  scaler = reduce_row_avg_scaler_tile(plan.width)
  print("mean-of-squares plan:")
  print(f"  x*x: bf16 inputs, fp32 DST accumulation")
  print(f"  reduce: PoolType::{plan.pool_type}, ReduceDim::{plan.reduce_dim}")
  print(f"  width: {plan.width} elements = {plan.col_tiles} TT col tiles")
  print(f"  bringup chunks: {plan.chunks} x {plan.chunk_elems} elements ({plan.chunk_col_tiles} col tiles/chunk)")
  print(f"  scaler: {plan.scaler:.9g}, layout={plan.scaler_layout}, nonzero entries={np.count_nonzero(scaler)}")
  print("  no DRAM round-trip is needed for the mean; keep the reduced column in DST/L1 for eps+rsqrt+broadcast")


def main() -> None:
  parser = argparse.ArgumentParser(description="Bringup Llama 3.2 1B RMSNorm mean/reduce path.")
  subparsers = parser.add_subparsers(dest="command")

  host = subparsers.add_parser("host-test", help="validate the two-1024-element mean decomposition")
  host.add_argument("--seed", type=int, default=0)
  host.add_argument("--rows", type=int, default=ROWS)
  host.add_argument("--max-abs", type=float, default=1e-6)
  host.add_argument("--max-rel-l2", type=float, default=1e-7)

  mean_device = subparsers.add_parser("mean-device-test", help="run the x^2 width mean on device using matmul-reduce")
  mean_device.add_argument("--seed", type=int, default=0)
  mean_device.add_argument("--rows", type=int, default=ROWS)
  mean_device.add_argument("--max-abs", type=float, default=5e-4)
  mean_device.add_argument("--max-rel-l2", type=float, default=5e-3)

  bcast_device = subparsers.add_parser("broadcast-device-test", help="verify standalone ELWMUL broadcast kernels")
  bcast_device.add_argument("--seed", type=int, default=0)
  bcast_device.add_argument("--max-abs", type=float, default=2.5e-1)
  bcast_device.add_argument("--max-rel-l2", type=float, default=8e-2)

  rsqrt_device = subparsers.add_parser("rsqrt-device-test", help="verify standalone SFPU eps+rsqrt tile kernel")
  rsqrt_device.add_argument("--seed", type=int, default=0)
  rsqrt_device.add_argument("--max-abs", type=float, default=8e-3)
  rsqrt_device.add_argument("--max-rel-l2", type=float, default=8e-3)

  pipeline = subparsers.add_parser("rmsnorm-device-test", help="run staged RMSNorm with device square/mean/rsqrt/broadcast")
  pipeline.add_argument("--seed", type=int, default=0)
  pipeline.add_argument("--max-abs", type=float, default=4e-1)
  pipeline.add_argument("--max-rel-l2", type=float, default=1.2e-1)

  subparsers.add_parser("mean-plan", help="print the Tenstorrent reduce plan for the mean")

  args = parser.parse_args()
  if args.command in (None, "host-test"):
    run_host_test(
      seed=getattr(args, "seed", 0),
      rows=getattr(args, "rows", ROWS),
      max_abs=getattr(args, "max_abs", 1e-6),
      max_rel_l2=getattr(args, "max_rel_l2", 1e-7),
    )
  elif args.command == "mean-plan":
    print_mean_plan()
  elif args.command == "mean-device-test":
    run_mean_device_test(
      seed=args.seed,
      rows=args.rows,
      max_abs=args.max_abs,
      max_rel_l2=args.max_rel_l2,
    )
  elif args.command == "broadcast-device-test":
    run_broadcast_device_test(
      seed=args.seed,
      max_abs=args.max_abs,
      max_rel_l2=args.max_rel_l2,
    )
  elif args.command == "rsqrt-device-test":
    run_rsqrt_device_test(
      seed=args.seed,
      max_abs=args.max_abs,
      max_rel_l2=args.max_rel_l2,
    )
  elif args.command == "rmsnorm-device-test":
    run_rmsnorm_device_pipeline_test(
      seed=args.seed,
      max_abs=args.max_abs,
      max_rel_l2=args.max_rel_l2,
    )


if __name__ == "__main__":
  main()
