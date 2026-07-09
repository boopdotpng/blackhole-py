#!/usr/bin/env python3
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))
if str(EXAMPLES) not in sys.path:
  sys.path.insert(0, str(EXAMPLES))

from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  TTDMANOP, TTELWMUL, TTMOP, TTMOVA2D, TTMOVD2A, TTNOP, TTPACR, TTRMWCIB0,
  TTSEMGET, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSETADC, TTSETADCZW, TTSETDMAREG,
  TTSTALLWAIT, TTSTOREREG, TTSFPLOAD, TTSFPMUL, TTSFPSTORE, TTSFPADD,
  TTSFPMOV, TTSFPSHFT2, TTUNPACR, TTUNPACR_NOP, TTWRCFG, TTZEROACC,
  Reg, ra, s0, s1, s2, s3, s4, s5, s6, s7, sp, t0, t1, t2, t3, t4, t5,
  t6, a0, a1, a2, a5, zero,
)
from matmul_peak import RiscSync  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk import Cb, Noc, Tensix  # noqa: E402
from ttk.addrs import p100_dram_bank_endpoint_coords  # noqa: E402
from ttk.cb import CircularBuffer as CB  # noqa: E402
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM, TriscLocalMem as TLM, TriscMailbox  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.sfpu import LReg, sfpu_load_fp32_const, sfpu_rsqrt_positive  # noqa: E402
from ttk.tensix import Cfg, MopCfg, TensixL1, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait, ThreadCfg  # noqa: E402


ROWS = 32
EMB_DIM = 2048
TILE = 32
COL_TILES = EMB_DIM // TILE
DTYPE = Dtype.Float16_b
TILE_BYTES = DTYPE.tile_size
MEAN_SCALE = 1.0 / EMB_DIM
NORM_EPS = 1e-5

X_CB = 0
WEIGHT_CB = 1
OUT_CB = 16
CB_DEPTH = 8

SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
SYNC_L1 = SCRATCH_L1 + 0x24000
SYNC_TRISC_START = SYNC_L1
SYNC_TRISC_INIT = SYNC_L1 + 20
SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)
UNPACK_TMP_LO_GPR = 0x12
UNPACK_TMP_LO_GPR_MMIO = TensixRegs.REGFILE_BASE + UNPACK_TMP_LO_GPR * 4
UNPACK_TO_DEST_ADDR_MAILBOX = 0x17A2C0
UNPACK_FP32_Z_STRIDE = 8 * 16 * 4
WORK_DST_BASE = 0
# Keep the persistent FP32 row-scale tile away from the BF16 direct-to-Dst work
# tile. The Dst16 and Dst32 views alias nonlinearly; final-pass x reloads at
# WORK_DST_BASE preserve rows 0..7 of an FP32 tile at 256 but corrupt later row
# groups. The far FP32 slot survives the reload.
ACC_DST_BASE = 768
# SFPLOAD/SFPSTORE Mod0 format. Blackhole ISA docs define these in
# tt-isa-documentation/.../BlackholeA0/.../SFPLOAD.md and SFPSTORE.md.
#   2 = MOD0_FMT_BF16: read Dst16b BF16 and promote each lane to FP32 LReg.
#   3 = MOD0_FMT_FP32: read/write Dst32b FP32.
# The original "unpack BF16 then pack as FP32" path was bogus: PACK was just
# interpreting Dst16b storage through the Dst32b view. Promotion has to happen
# through SFPU LRegs, then SFPSTORE writes real FP32 values back into Dst32b.
SFPU_LOAD_STORE_FP32 = 3
SFPU_LOAD_BF16 = 2

UNPACK_X_TO_DST_MOP_CFG = MopCfg(
  loop_outer=4,
  loop_inner=1,
  template=[
    TTUNPACR(AddrMode=0x11, OvrdThreadId=1, SetDatValid=0, Last=1),
    TTNOP(), TTNOP(), TTNOP(), TTNOP(), TTNOP(), TTNOP(),
  ],
)
_MATH_MOVA2D = TTMOVA2D(addr_mode=2, instr_mod=2)
MATH_MOP_CFG = MopCfg(
  loop_outer=4,
  loop_inner=2,
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
PACK_MOP_CFG = MopCfg(
  loop_outer=4,
  loop_inner=4,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    TTPACR(),
    TTNOP(),
    TTPACR(AddrMode=1, Last=1),
    TTPACR(AddrMode=2),
  ],
)
UNPACK_SRC_B = TTUNPACR(1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1)
UNPACK_SRCA_DUMMY_DVALID = TTUNPACR_NOP(Unpacker_Select=0, Set_Dvalid=1, Unpack_Pop=1)
UNPACK_WEIGHT_ROW_BCAST_MOP_CFG = MopCfg(
  loop_outer=2,
  loop_inner=2,
  template=[
    TTNOP(), TTSETADCZW(2, 0, 0, 0, 0, 1), TTNOP(),
    UNPACK_SRC_B, UNPACK_SRCA_DUMMY_DVALID,
    UNPACK_SRCA_DUMMY_DVALID, UNPACK_SRCA_DUMMY_DVALID,
  ],
)
BCAST_ROW = 2
ELW_ADDR_MOD_ROW = 0
ELW_ADDR_MOD_FIDELITY = 2
ELW_ADDR_MOD_FACE = 3
ELWMUL_ROW_HIFI2_MOP_CFG = MopCfg(
  # HiFi2 ELWMUL performs two fidelity phases over one 16x16 face. For ROW
  # broadcast, SrcB's row is held fixed while SrcA/Dst walk the two 8-row FPU
  # chunks in that face. Runtime calls this MOP once per face.
  loop_outer=2,
  loop_inner=2,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    TTELWMUL(0, 0, BCAST_ROW, ELW_ADDR_MOD_ROW, 0),
    TTNOP(),
    # MopCfg slots 5/6 are ckernel_template's last_outer/last_inner
    # instructions. Last outer clears SrcA/SrcB valid and advances to the next
    # face; last inner only advances the fidelity phase and carry register.
    TTELWMUL(3, 0, BCAST_ROW, ELW_ADDR_MOD_FACE, 0),
    TTELWMUL(0, 0, BCAST_ROW, ELW_ADDR_MOD_FIDELITY, 0),
  ],
)
STALL_MATH_PACK_ROOM = TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU
STALL_MATH_PACK_DATA = TensixStall.TDMA
WAIT_MATH_AND_SFPU = TensixWait.MATH | TensixWait.SFPU
WAIT_THCON_AND_PACK = TensixWait.THCON | TensixWait.PACK0


class _RoleKernel(KernelBase):
  def _loop_epilogue(self):
    return self.ret()

  @contextmanager
  def tile_loop(self, name: str, *, count: Reg, counter: Reg = s5, epilogue: bool = True) -> Iterator[None]:
    self.li(counter, 0)
    self.label(f"{name}_loop")
    self.beq(counter, count, f"{name}_done")
    yield
    self.addi(counter, counter, 1)
    self.j(f"{name}_loop")
    self.label(f"{name}_done")
    if epilogue:
      self._loop_epilogue()


class Brisc(_RoleKernel, Noc, Cb):
  pass


class Ncrisc(_RoleKernel, Noc, Cb):
  pass


class Trisc(_RoleKernel, Tensix, Cb):
  NUM_TRISC = 3

  def __init__(self, thread_id: int, sync: RiscSync = SYNC, *, base_addr: int = 0):
    super().__init__(base_addr=base_addr)
    self.thread_id = thread_id
    self.sync = sync
    self.data = TriscMailbox.DATA1 if thread_id == 1 else TriscMailbox.DATA_COMMON
    from ttk.math import Math
    from ttk.pack import Pack
    from ttk.unpack import Unpack
    self.math = Math(self)
    self.pack = Pack(self)
    self.unpack = Unpack(self)

  def prologue(self):
    self.addi(sp, sp, -16)
    self.sw(ra, sp, 12)
    self.read32(t0, self.data["rta_l1_base"])
    self.lw(s3, t0, 0)
    self.wait8(self.sync.start + self.thread_id, 1)
    self.write8(self.sync.start + self.thread_id, 0)
    return self

  def _loop_epilogue(self):
    return self.ret_kernel()

  def init_barrier(self):
    self.write32(self.sync.trisc_init + self.thread_id * 4, 1)
    self.fence()
    self.li(t1, 1)
    for init_id in range(self.NUM_TRISC):
      self.wait_sync_value(self.sync.trisc_init + init_id * 4, t1, actual=t4)
    return self

  def tile_loop(self, *, count: Reg = s3, counter: Reg = s5, epilogue: bool = True) -> Iterator[None]:
    return super().tile_loop(f"trisc{self.thread_id}", count=count, counter=counter, epilogue=epilogue)


def _trisc0_set_unpack_to_dest_ctx0(fw: Trisc) -> Trisc:
  # Each unpacker engine has two override config contexts. For unpacker 0 they
  # are SEC0 ctx0 and SEC0 ctx1; the selected context comes from
  # UNPACK_MISC_CFG_CfgContextOffset_0 when TTUNPACR uses OvrdThreadId=1.
  #
  # This RMSNorm bring-up path is fully serialized: we wait for unpacker 0 to be
  # idle before changing the base address and issuing the next UNPACR. Since the
  # tile shape and direct-to-DST mode are identical for every input tile, ctx1
  # buys us nothing here. Keep ctx0 selected and update only ctx0's per-tile
  # input base below; that removes ctx ping-pong from the failure surface.
  #
  # Unpack.init seeds THCON_SEC0_REG5_Dest_cntx to 0x00400040. That register
  # packs both ctx0/ctx1 destination bases:
  #   low  16 bits: ctx0 destination address
  #   high 16 bits: ctx1 destination address
  # Unpacker 0 subtracts 64 from the computed direct-DST address internally, so
  # the initialized ctx0 value 64 means "start at logical DST offset 0". The
  # the current reduction path always uses that fixed destination, so leave
  # Dest_cntx alone and only toggle the direct-to-DST select bit.
  #
  # Direct-to-DST for this ctx0 override path is bit 4 (0x10). Hardware checks
  # showed that 0x20/0x40/0x80 alone do not produce visible Dst writes here;
  # 0xF0 only appeared to work because it included 0x10.
  #
  # Important direct-to-DST limitation: issuing the four 16x16 UNPACRs
  # back-to-back, either through the MOP above or as four explicit instructions,
  # leaves only the final quadrant visible in Dst. Inserting
  # TTSTALLWAIT(..., UNPACK0) after each UNPACR preserves all 1024 values. This
  # smells like an unpack-to-Dst pipeline/scoreboard limitation, not a normal
  # instruction-consumption issue. Unpacker1 does not support this direct-Dst
  # path, so the serialized unpacker0 sequence is the working path.
  fw.push_tensix(TTRMWCIB0(Mask=0x10, Data=0x10, CfgRegAddr=Cfg.THCON_SEC0_REG2_1.addr32))
  return fw


def _trisc0_restore_unpack_to_dest_ctx0(fw: Trisc) -> Trisc:
  fw.push_tensix(TTRMWCIB0(Mask=0x10, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2_1.addr32))
  return fw


def _trisc0_write_unpack_dest_ctx0(fw: Trisc, dest_offset: Reg) -> Trisc:
  # Direct-to-Dst ctx0 wants the same +64-byte bias as the default 0x00400040
  # setup: logical Dst offset 0 is programmed as 64. The mailbox carries the
  # logical SFPLOAD/SFPSTORE offset (0, 256, 512, ...), so convert it here and
  # write both ctx halves to keep the dormant ctx1 value harmless.
  fw.addi(dest_offset, dest_offset, 4)
  fw.slli(dest_offset, dest_offset, 4)
  fw.slli(t1, dest_offset, 16)
  fw.or_(t1, t1, dest_offset)
  fw.write32(UNPACK_TMP_LO_GPR_MMIO, t1)
  fw.emit(TTWRCFG(UNPACK_TMP_LO_GPR, 0, Cfg.THCON_SEC0_REG5_Dest_cntx.addr32))
  return fw


def _trisc0_write_unpack_z_stride(fw: Trisc, stride: int) -> Trisc:
  fw.write32(UNPACK_TMP_LO_GPR_MMIO, stride)
  fw.emit(TTWRCFG(UNPACK_TMP_LO_GPR, 0, Cfg.UNP0_ADDR_CTRL_ZW_REG_1.addr32))
  return fw


def _trisc0_unpack_cb_to_dst(fw: Trisc, cb_id: int) -> None:
  fw.cb_wait_front(fw.data["cb_interface"], cb_id)
  fw.cb_read_ptr(fw.data["cb_interface"], cb_id, out=s0)
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

  # Keep unpacker 0 on SEC0 ctx0 for every tile. The CB read pointer still
  # changes because X_CB is a circular buffer with multiple pages: BRISC pushes
  # tile 0 into page 0, tile 1 into page 1, and so on until the ring wraps.
  # UNPACR's input base must point at the current front page, so update ctx0's
  # Base_address from the live CB read pointer each iteration.
  fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, 0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.li(t2, TensixRegs.CFG_BASE + Cfg.THCON_SEC0_REG3_Base_address.addr32 * 4)
  fw.addi(t3, s0, -1)
  fw.sw(t3, t2, 0)
  fw.lw(t1, t2, 0)
  fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

  fw.read32(t4, UNPACK_TO_DEST_ADDR_MAILBOX)
  _trisc0_write_unpack_dest_ctx0(fw, t4)
  # Direct-to-DST is enabled only around this UNPACR. Leaving it enabled after
  # the unpack interferes with the later math/pack phase on this bring-up path.
  # The important simplification is that the selected unpack config remains
  # ctx0; we are not alternating to ctx1 between tiles.
  fw.setc16(ThreadCfg.SRCA_SET, 0)
  _trisc0_set_unpack_to_dest_ctx0(fw)
  fw.emit(TTSEMWAIT(
    TensixStall.UNPACK,
    TensixSem.mask(TensixSem.MATH_DONE),
    TensixSemWait.STALL_ON_ZERO,
  ))
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.MATH_DONE)))
  fw.emit(TTSEMWAIT(
    TensixStall.UNPACK,
    TensixSem.mask(TensixSem.UNPACK_TO_DEST),
    TensixSemWait.STALL_ON_MAX,
  ))
  fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
  for _ in range(4):
    fw.emit(TTUNPACR(AddrMode=0x11, OvrdThreadId=1, SetDatValid=0, Last=1))
    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.UNPACK0))
  fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.THCON | TensixWait.UNPACK0))
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
  _trisc0_restore_unpack_to_dest_ctx0(fw)
  fw.setc16(ThreadCfg.SRCA_SET, 4)
  fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.UNPACK_TO_DEST)))
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.cb_pop_front(fw.data["cb_interface"], cb_id, tensix_ack=True)


def _trisc0_unpack_weight_to_srcb(fw: Trisc, cb_id: int) -> None:
  fw.cb_wait_front(fw.data["cb_interface"], cb_id)
  fw.cb_read_ptr(fw.data["cb_interface"], cb_id, out=s1)
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 15))

  wait_unp = fw._new_label("wait_weight_unpack_ctx")
  wait_unp_done = fw._new_label("wait_weight_unpack_ctx_done")
  fw.li(t0, TensixRegs.PC_UNPACK_SYNC)
  fw.label(wait_unp)
  fw.lw(t1, t0, 0)
  fw.andi(t1, t1, 0xFE)
  fw.beq(t1, zero, wait_unp_done)
  fw.fence()
  fw.j(wait_unp)
  fw.label(wait_unp_done)

  fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, 0)
  fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
  fw.li(t2, TensixRegs.CFG_BASE + Cfg.THCON_SEC1_REG3_Base_address.addr32 * 4)
  fw.addi(t3, s1, -1)
  fw.sw(t3, t2, 0)
  fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

  fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
  fw.write_mop_cfg(UNPACK_WEIGHT_ROW_BCAST_MOP_CFG, 0)
  fw.emit(TTMOP(1, 0, 0))
  fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.THCON | TensixWait.UNPACK0 | TensixWait.UNPACK1))
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
  fw.cb_pop_front(fw.data["cb_interface"], cb_id, tensix_ack=True)


def trisc0_reduce_pass() -> Trisc:
  fw = Trisc(0, SYNC)
  fw.prologue()
  fw.unpack.init(dtype=DTYPE, tile_bytes=TILE_BYTES, mop_cfg=UNPACK_X_TO_DST_MOP_CFG, fp32_dest=True)
  _trisc0_write_unpack_z_stride(fw, UNPACK_FP32_Z_STRIDE)
  fw.init_barrier()

  fw.li(s5, 0)
  fw.label("trisc0_reduce_loop")
  fw.beq(s5, s3, "trisc0_reduce_done")
  _trisc0_unpack_cb_to_dst(fw, X_CB)
  fw.addi(s5, s5, 1)
  fw.j("trisc0_reduce_loop")
  fw.label("trisc0_reduce_done")

  fw.li(s5, 0)
  fw.label("trisc0_final_loop")
  fw.beq(s5, s3, "trisc0_final_done")
  _trisc0_unpack_cb_to_dst(fw, X_CB)
  _trisc0_unpack_weight_to_srcb(fw, WEIGHT_CB)
  fw.addi(s5, s5, 1)
  fw.j("trisc0_final_loop")
  fw.label("trisc0_final_done")
  fw.ret_kernel()
  return fw


def _write_trisc1_dest_offset_instr(fw: Trisc, offset_id=t1, instr=t2, base=t3) -> Trisc:
  fw.sltu(instr, zero, offset_id)
  fw.slli(instr, instr, 9)
  fw.li(base, 0xB2010000)
  fw.add(instr, instr, base)
  return fw.write32(TensixRegs.INSTRN_BUF_BASE, instr, tmp_addr=t0)


def _trisc1_request_unpack_to_dst(fw: Trisc, dst_base: int) -> Trisc:
  fw.li(t1, dst_base)
  fw.write32(UNPACK_TO_DEST_ADDR_MAILBOX, t1)
  fw.fence()
  fw.emit(TTSEMWAIT(
    TensixStall.SYNC,
    TensixSem.mask(TensixSem.MATH_DONE),
    TensixSemWait.STALL_ON_MAX,
  ))
  fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_DONE)))
  fw.emit(TTSEMWAIT(
    TensixStall.SYNC,
    TensixSem.mask(TensixSem.UNPACK_TO_DEST),
    TensixSemWait.STALL_ON_ZERO,
  ))
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_TO_DEST)))
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))
  return fw


def _sfpu_add_into(fw: Trisc, dst: int | LReg, src: int | LReg) -> Trisc:
  return fw.emit(TTSFPADD(int(dst), int(LReg.CONST_1), int(src), int(dst), 0))


def _sfpu_square_lreg(fw: Trisc, lreg: int | LReg) -> Trisc:
  return fw.emit(TTSFPMUL(int(lreg), int(lreg), int(LReg.CONST_0), int(lreg), 0))


def _sfpu_horizontal_reduce_pair(fw: Trisc) -> Trisc:
  """L0/L4 each hold 8 column-lane partials; fold lanes into column 0."""
  fw.emit(TTSFPMOV(0, int(LReg.L0), int(LReg.L1), 0))
  fw.emit(TTSFPMOV(0, int(LReg.L4), int(LReg.L5), 0))
  for _ in range(4):
    fw.emit(TTSFPSHFT2(0, int(LReg.L1), int(LReg.L1), 3))
    fw.emit(TTSFPSHFT2(0, int(LReg.L5), int(LReg.L5), 3))
  _sfpu_add_into(fw, LReg.L0, LReg.L1)
  _sfpu_add_into(fw, LReg.L4, LReg.L5)

  fw.emit(TTSFPMOV(0, int(LReg.L0), int(LReg.L1), 0))
  fw.emit(TTSFPMOV(0, int(LReg.L4), int(LReg.L5), 0))
  for _ in range(2):
    fw.emit(TTSFPSHFT2(0, int(LReg.L1), int(LReg.L1), 3))
    fw.emit(TTSFPSHFT2(0, int(LReg.L5), int(LReg.L5), 3))
  _sfpu_add_into(fw, LReg.L0, LReg.L1)
  _sfpu_add_into(fw, LReg.L4, LReg.L5)

  fw.emit(TTSFPMOV(0, int(LReg.L0), int(LReg.L1), 0))
  fw.emit(TTSFPMOV(0, int(LReg.L4), int(LReg.L5), 0))
  fw.emit(TTSFPSHFT2(0, int(LReg.L1), int(LReg.L1), 3))
  fw.emit(TTSFPSHFT2(0, int(LReg.L5), int(LReg.L5), 3))
  _sfpu_add_into(fw, LReg.L0, LReg.L1)
  return _sfpu_add_into(fw, LReg.L4, LReg.L5)


def _sfpu_load_square_reduce_row_pair(
  fw: Trisc,
  *,
  work_base: int,
  face_pair_base: int,
  row_offset_first: int,
  row_offset_second: int,
) -> tuple[int, int]:
  """Load two 4-row groups, square, and reduce each group across 32 columns.

  On return, L0 and L4 hold the reduced row partials. Each LREG is a 4x8
  vector, so this covers eight physical rows: L0 for the first 4-row group
  and L4 for the second.
  """
  rows_per_face = 16
  group_a_base = work_base + face_pair_base + row_offset_first
  group_b_base = work_base + face_pair_base + row_offset_second

  fw.emit(TTSFPLOAD(int(LReg.L0), SFPU_LOAD_BF16, 7, group_a_base))
  fw.emit(TTSFPLOAD(int(LReg.L1), SFPU_LOAD_BF16, 7, group_a_base + 2))
  fw.emit(TTSFPLOAD(int(LReg.L2), SFPU_LOAD_BF16, 7, group_a_base + rows_per_face))
  fw.emit(TTSFPLOAD(int(LReg.L3), SFPU_LOAD_BF16, 7, group_a_base + rows_per_face + 2))
  fw.emit(TTSFPLOAD(int(LReg.L4), SFPU_LOAD_BF16, 7, group_b_base))
  fw.emit(TTSFPLOAD(int(LReg.L5), SFPU_LOAD_BF16, 7, group_b_base + 2))
  fw.emit(TTSFPLOAD(int(LReg.L6), SFPU_LOAD_BF16, 7, group_b_base + rows_per_face))
  fw.emit(TTSFPLOAD(int(LReg.L7), SFPU_LOAD_BF16, 7, group_b_base + rows_per_face + 2))

  for reg in (LReg.L0, LReg.L1, LReg.L2, LReg.L3, LReg.L4, LReg.L5, LReg.L6, LReg.L7):
    _sfpu_square_lreg(fw, reg)

  _sfpu_add_into(fw, LReg.L2, LReg.L3)
  _sfpu_add_into(fw, LReg.L6, LReg.L7)
  _sfpu_add_into(fw, LReg.L1, LReg.L2)
  _sfpu_add_into(fw, LReg.L5, LReg.L6)
  _sfpu_add_into(fw, LReg.L0, LReg.L1)
  _sfpu_add_into(fw, LReg.L4, LReg.L5)
  _sfpu_horizontal_reduce_pair(fw)
  return face_pair_base + row_offset_first, face_pair_base + row_offset_second


def _sfpu_store_row_pair_to_acc(fw: Trisc, *, acc_base: int, first_off: int, second_off: int) -> Trisc:
  fw.emit(TTSFPSTORE(int(LReg.L0), SFPU_LOAD_STORE_FP32, 7, acc_base + first_off))
  return fw.emit(TTSFPSTORE(int(LReg.L4), SFPU_LOAD_STORE_FP32, 7, acc_base + second_off))


def _sfpu_accumulate_row_pair(fw: Trisc, *, acc_base: int, first_off: int, second_off: int) -> Trisc:
  fw.emit(TTSFPLOAD(int(LReg.L1), SFPU_LOAD_STORE_FP32, 7, acc_base + first_off))
  fw.emit(TTSFPLOAD(int(LReg.L5), SFPU_LOAD_STORE_FP32, 7, acc_base + second_off))
  _sfpu_add_into(fw, LReg.L0, LReg.L1)
  _sfpu_add_into(fw, LReg.L4, LReg.L5)
  return _sfpu_store_row_pair_to_acc(fw, acc_base=acc_base, first_off=first_off, second_off=second_off)


def _sfpu_scale_accumulator(
  fw: Trisc,
  *,
  acc_base: int = ACC_DST_BASE,
  scale: float = MEAN_SCALE,
) -> Trisc:
  """Scale the row-reduction accumulator in place.

  This is the `.mean(axis=-1)` step after all column-tile partial sums have
  been accumulated: mean(x*x) = sum(x*x) / EMB_DIM.
  """
  sfpu_load_fp32_const(fw, int(LReg.L7), scale)
  rows_per_face = 16
  for face_pair in range(2):
    face_pair_base = face_pair * 2 * rows_per_face
    for row_group in range(2):
      for row_offset in (row_group * 8, row_group * 8 + 4):
        off = acc_base + face_pair_base + row_offset
        fw.emit(TTSFPLOAD(int(LReg.L0), SFPU_LOAD_STORE_FP32, 7, off))
        fw.emit(TTSFPMUL(int(LReg.L0), int(LReg.L7), int(LReg.CONST_0), int(LReg.L0), 0))
        fw.emit(TTSFPSTORE(int(LReg.L0), SFPU_LOAD_STORE_FP32, 7, off))
  return fw


def _sfpu_add_accumulator_eps(
  fw: Trisc,
  *,
  acc_base: int = ACC_DST_BASE,
  eps: float = NORM_EPS,
) -> Trisc:
  """Add RMSNorm epsilon to the f32 row-mean accumulator in place."""
  sfpu_load_fp32_const(fw, int(LReg.L7), eps)
  rows_per_face = 16
  for face_pair in range(2):
    face_pair_base = face_pair * 2 * rows_per_face
    for row_group in range(2):
      for row_offset in (row_group * 8, row_group * 8 + 4):
        off = acc_base + face_pair_base + row_offset
        fw.emit(TTSFPLOAD(int(LReg.L0), SFPU_LOAD_STORE_FP32, 7, off))
        _sfpu_add_into(fw, LReg.L0, LReg.L7)
        fw.emit(TTSFPSTORE(int(LReg.L0), SFPU_LOAD_STORE_FP32, 7, off))
  return fw


def _sfpu_rsqrt_accumulator(fw: Trisc, *, acc_base: int = ACC_DST_BASE) -> Trisc:
  """Apply rsqrt to the f32 row accumulator in place."""
  rows_per_face = 16
  for face_pair in range(2):
    face_pair_base = face_pair * 2 * rows_per_face
    for row_group in range(2):
      for row_offset in (row_group * 8, row_group * 8 + 4):
        off = acc_base + face_pair_base + row_offset
        fw.emit(TTSFPLOAD(int(LReg.L0), SFPU_LOAD_STORE_FP32, 7, off))
        sfpu_rsqrt_positive(fw, int(LReg.L0), int(LReg.L0))
        fw.emit(TTSFPSTORE(int(LReg.L0), SFPU_LOAD_STORE_FP32, 7, off))
  return fw


def _sfpu_reduce_square_tile_into_acc(fw: Trisc, *, first_tile: bool) -> Trisc:
  """Square/reduce the current work tile and update the persistent accumulator.

  WORK_DST_BASE holds the just-unpacked x tile. ACC_DST_BASE holds a f32 tile
  whose meaningful values are the REDUCE_ROW column-0 row groups.
  """
  rows_per_face = 16
  for face_pair in range(2):
    face_pair_base = face_pair * 2 * rows_per_face
    for row_group in range(2):
      row_offset_first = row_group * 8
      row_offset_second = row_offset_first + 4
      first_off, second_off = _sfpu_load_square_reduce_row_pair(
        fw,
        work_base=WORK_DST_BASE,
        face_pair_base=face_pair_base,
        row_offset_first=row_offset_first,
        row_offset_second=row_offset_second,
      )
      if first_tile:
        _sfpu_store_row_pair_to_acc(fw, acc_base=ACC_DST_BASE, first_off=first_off, second_off=second_off)
      else:
        _sfpu_accumulate_row_pair(fw, acc_base=ACC_DST_BASE, first_off=first_off, second_off=second_off)
  return fw


def _sfpu_mul_x_scale_tile(
  fw: Trisc,
  *,
  x_base: int = WORK_DST_BASE,
  acc_base: int = ACC_DST_BASE,
  out_base: int = WORK_DST_BASE,
) -> Trisc:
  """Compute one output tile: out = x * rsqrt(row_mean + eps).

  x is a BF16 tile in the Dst16b view. The row scale is the FP32 accumulator
  tile produced by the reduction pass. Results are rounded back into the BF16
  Dst view, matching the Python `(xf * scale).cast(dtype)` boundary.
  """
  rows_per_face = 16
  chunks = (0, 2, rows_per_face, rows_per_face + 2)
  for face_pair in range(2):
    face_pair_base = face_pair * 2 * rows_per_face
    for row_group in range(2):
      for row_offset in (row_group * 8, row_group * 8 + 4):
        scale_off = acc_base + face_pair_base + row_offset
        for chunk in chunks:
          off = face_pair_base + row_offset + chunk
          fw.emit(TTSFPLOAD(int(LReg.L0), SFPU_LOAD_BF16, 7, x_base + off))
          fw.emit(TTSFPLOAD(int(LReg.L2), SFPU_LOAD_STORE_FP32, 7, scale_off))
          fw.emit(TTSFPMUL(int(LReg.L0), int(LReg.L2), int(LReg.CONST_0), int(LReg.L0), 0))
          fw.emit(TTSFPSTORE(int(LReg.L0), SFPU_LOAD_BF16, 7, out_base + off))
  return fw


def _configure_elwmul_row_hifi2(fw: Trisc) -> Trisc:
  fw.write_mop_cfg(ELWMUL_ROW_HIFI2_MOP_CFG, 1)
  # TT-LLK eltwise_binary_configure_addrmod<ELWMUL, ROW, HiFi2>:
  #   sec0: SrcA += 8, SrcB += 0, Dst += 8
  #   sec2: clear SrcA/SrcB, carry Dst, fidelity += 1
  #   sec3: clear SrcA/SrcB, Dst += 8, copy carry to current, fidelity = 0
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC0_Src, 0x0008)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC0, 0x0008)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC0_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC2_Src, 0x8080)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC2, 0x2400)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC2_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC3_Src, 0x8080)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC3, 0x9008)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC3_Bias, 0)
  return fw


def _move_dst_face_to_srca(fw: Trisc) -> Trisc:
  # TT-LLK move_d2a_fixed_face(ADDR_MOD_1). Dst RWC selects which 16-row face
  # is copied; the HiFi2 MOP advances it to the next face after each run.
  fw.emit(TTSTALLWAIT(TensixStall.MATH, TensixWait.SRCA_VLD))
  for row in range(16):
    fw.emit(TTMOVD2A(0, row, 1, 0, row))
  return fw


def _elwmul_weight_from_dst_reuse(fw: Trisc) -> Trisc:
  """Final RMSNorm multiply: Dst(tmp bf16) * SrcB(weight row) -> Dst(out bf16)."""
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))
  fw.emit(TTSTALLWAIT(TensixStall.MATH, TensixWait.SRCB_VLD))
  for face in range(4):
    _move_dst_face_to_srca(fw)
    fw.emit(TTZEROACC(1, 0, 0, 1, face))
    fw.emit(TTMOP(1, 0, 0))
  return fw


def trisc1_rsqrt_pass() -> Trisc:
  """TRISC1 phase: reduction, rsqrt, then first RMSNorm multiply.

  This computes sum(x*x) over the 64 column tiles for each of the 32 rows. It
  keeps only row partials in the accumulator DST tile, then computes
  rsqrt(mean(x*x) + NORM_EPS). The final loop reloads x tiles, multiplies them
  by that row scale in FP32, and hands each output tile to TRISC2 for BF16
  packing.
  """
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=MATH_MOP_CFG)
  _configure_elwmul_row_hifi2(fw)
  fw.init_barrier()

  with fw.tile_loop(epilogue=False):
    _trisc1_request_unpack_to_dst(fw, WORK_DST_BASE)
    fw.li(t1, 0)
    _write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))

    not_first = fw._new_label("trisc1_reduce_not_first")
    reduce_done = fw._new_label("trisc1_reduce_done")
    fw.bne(s5, zero, not_first)
    _sfpu_reduce_square_tile_into_acc(fw, first_tile=True)
    fw.j(reduce_done)
    fw.label(not_first)
    _sfpu_reduce_square_tile_into_acc(fw, first_tile=False)
    fw.label(reduce_done)

    fw.push_tensix(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.push_tensix(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
  fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
  _sfpu_scale_accumulator(fw)
  _sfpu_add_accumulator_eps(fw)
  _sfpu_rsqrt_accumulator(fw)
  fw.push_tensix(TTSETRWC(0, 0, 0, 0, 0, 4))
  fw.push_tensix(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))

  fw.li(s5, 0)
  fw.label("trisc1_final_loop")
  fw.beq(s5, s3, "trisc1_final_done")
  fw.emit(TTSEMWAIT(
    TensixStall.SYNC,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_MAX,
  ))
  _trisc1_request_unpack_to_dst(fw, WORK_DST_BASE)
  fw.li(t1, 0)
  _write_trisc1_dest_offset_instr(fw, t1, t2, t3)
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
  fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
  _sfpu_mul_x_scale_tile(fw)
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))
  _elwmul_weight_from_dst_reuse(fw)
  fw.push_tensix(TTSETRWC(0, 0, 0, 0, 0, 15))
  fw.push_tensix(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))
  fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_PACK)))
  fw.addi(s5, s5, 1)
  fw.j("trisc1_final_loop")
  fw.label("trisc1_final_done")
  fw.ret_kernel()
  return fw


def trisc2_pack_accumulator(dst_base: int = WORK_DST_BASE) -> Trisc:
  fw = Trisc(2, SYNC)
  fw.prologue()
  fw.pack.init(dtype=DTYPE, out_cb=OUT_CB, mop_cfg=PACK_MOP_CFG, fp32_dest=False)
  fw.init_barrier()

  fw.li(s5, 0)
  fw.label("trisc2_pack_loop")
  fw.beq(s5, s3, "trisc2_pack_done")
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

  fw.li(t2, dst_base)
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
  fw.push_tensix(
    TTSTOREREG(24, ((CB.SYNC_TILES_RECEIVED_BASE + OUT_CB * CB.SYNC_STRIDE) >> 2) & 0x3FFFF),
  )
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.PACK0))
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.MATH_PACK)))
  fw.addi(s5, s5, 1)
  fw.j("trisc2_pack_loop")
  fw.label("trisc2_pack_done")
  fw.ret_kernel()
  return fw


def _dram_tile_addr(fw: Brisc | Ncrisc, bank_coords: list[int], *, base: Reg, tile: Reg, num_banks: Reg, stride: Reg) -> None:
  fw.mul(a1, tile, stride)
  fw.add(a1, base, a1)
  fw.mv(t0, a1)
  fw.remu(a1, t0, num_banks)
  fw.divu(t0, t0, num_banks)
  fw.slli(t0, t0, 11)
  fw.add(a0, a0, t0)
  fw.li(a2, bank_coords[0])
  for bank, coord in enumerate(bank_coords[1:], start=1):
    next_bank = fw._new_label("dram_bank")
    fw.li(t1, bank)
    fw.bne(a1, t1, next_bank)
    fw.li(a2, coord)
    fw.label(next_bank)


def _read_dram_tile_to_cb(
  fw: Brisc,
  cb_id: int,
  bank_coords: list[int],
  *,
  addr: Reg,
  base: Reg,
  tile: Reg,
  num_banks: Reg,
  stride: Reg,
) -> None:
  fw.cb_reserve_back(BM.CB_INTERFACE, cb_id)
  fw.mv(a0, addr)
  _dram_tile_addr(fw, bank_coords, base=base, tile=tile, num_banks=num_banks, stride=stride)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.cb_write_ptr(BM.CB_INTERFACE, cb_id, out=t5)
  fw.li(t6, TILE_BYTES)
  fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  wait = fw._new_label("read_wait")
  fw.label(wait)
  fw.lw(t1, t0, 0)
  fw.bltu(t1, t4, wait)
  fw.fence()
  fw.cb_push_back(BM.CB_INTERFACE, cb_id)


def brisc(dram_bank_coords: list[int]) -> Brisc:
  """Reader.

  Runtime args:
    0 x_addr
    1 x_base_tile
    2 weight_addr
    3 weight_base_tile
    4 col_tiles
    5 num_banks
    6 stride_tiles
  """
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s6, s7))
  for addr in (SYNC_TRISC_START, SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)

  with fw.tile_loop("brisc_reduce_read", count=s4, epilogue=False):
    _read_dram_tile_to_cb(
      fw,
      X_CB,
      dram_bank_coords,
      addr=s0,
      base=s1,
      tile=s5,
      num_banks=s6,
      stride=s7,
    )
  with fw.tile_loop("brisc_final_read", count=s4):
    _read_dram_tile_to_cb(
      fw,
      X_CB,
      dram_bank_coords,
      addr=s0,
      base=s1,
      tile=s5,
      num_banks=s6,
      stride=s7,
    )
    _read_dram_tile_to_cb(
      fw,
      WEIGHT_CB,
      dram_bank_coords,
      addr=s2,
      base=s3,
      tile=s5,
      num_banks=s6,
      stride=s7,
    )
  return fw


def ncrisc(dram_bank_coords: list[int]) -> Ncrisc:
  """Writer.

  Runtime args:
    0 out_addr
    1 out_base_tile
    2 col_tiles
    3 num_banks
    4 out_stride_tiles

  For in-place RMSNorm, pass the same address/base/stride as x:
    out_addr == x_addr
    out_base_tile == x_base_tile
    out_stride_tiles == x_stride_tiles
  """
  fw = Ncrisc()
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4))
  with fw.tile_loop("ncrisc_write", count=s2):
    fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
    fw.mv(a0, s0)
    _dram_tile_addr(fw, dram_bank_coords, base=s1, tile=s5, num_banks=s3, stride=s4)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
    fw.addi(t4, t4, 1)
    fw.cb_read_ptr(NM.CB_INTERFACE, OUT_CB, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_write(1, 0, t5, a0, 0, a2, t6, a=t0, v=t1)
    fw.noc_write_barrier(1, t4, addr=t0, val=t1)
    fw.cb_pop_front(NM.CB_INTERFACE, OUT_CB)
  return fw


def build_program(
  x_addr: int,
  weight_addr: int,
  out_addr: int,
  num_banks: int,
  *,
  core: tuple[int, int] = (1, 2),
  x_base_tile: int = 0,
  weight_base_tile: int = 0,
  out_base_tile: int = 0,
  stride_tiles: int = 1,
  out_stride_tiles: int = 1,
  col_tiles: int = COL_TILES,
  dram_bank_coords_noc0: list[int] | None = None,
  dram_bank_coords_noc1: list[int] | None = None,
) -> Program:
  if dram_bank_coords_noc0 is None:
    dram_bank_coords_noc0 = p100_dram_bank_endpoint_coords(None, 0)[:num_banks]
  if dram_bank_coords_noc1 is None:
    dram_bank_coords_noc1 = p100_dram_bank_endpoint_coords(None, 1)[:num_banks]

  brisc_fw = brisc(dram_bank_coords_noc0)
  ncrisc_fw = ncrisc(dram_bank_coords_noc1)
  trisc0_fw = trisc0_reduce_pass()
  trisc1_fw = trisc1_rsqrt_pass()
  trisc2_fw = trisc2_pack_accumulator()

  brisc_fw.rta(lambda _x, _y: [x_addr, x_base_tile, weight_addr, weight_base_tile, col_tiles, num_banks, stride_tiles])
  ncrisc_fw.rta(lambda _x, _y: [out_addr, out_base_tile, col_tiles, num_banks, out_stride_tiles])
  trisc0_fw.rta(lambda _x, _y: [col_tiles])
  trisc1_fw.rta(lambda _x, _y: [col_tiles])
  trisc2_fw.rta(lambda _x, _y: [col_tiles])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(X_CB, TILE_BYTES, CB_DEPTH), (WEIGHT_CB, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, 2)],
    core_order=(core,),
  )
  prog.name = "llama3_rmsnorm"
  return prog


def _to_bf16_bytes(x: np.ndarray) -> bytes:
  bits = np.asarray(x, dtype="<f4").view("<u4")
  return (bits >> 16).astype("<u2").tobytes()


def _bf16_to_f32(x: np.ndarray) -> np.ndarray:
  bits = np.asarray(x, dtype="<u2").astype("<u4") << 16
  return bits.view("<f4")


def run() -> None:
  rng = np.random.default_rng(0)
  x = rng.normal(0.0, 0.25, size=(ROWS, EMB_DIM)).astype(np.float32)
  weight_vec = rng.normal(1.0, 0.1, size=(EMB_DIM,)).astype(np.float32)
  weight_tiles = np.zeros((ROWS, EMB_DIM), dtype=np.float32)
  # ROW broadcast is per 16x16 face, so each vertical face group needs the
  # weight row in its local row 0. For a 32-row tile that means rows 0 and 16.
  weight_tiles[0:ROWS:16, :] = weight_vec
  x_bf16 = _bf16_to_f32(np.frombuffer(_to_bf16_bytes(x), dtype="<u2")).reshape(ROWS, EMB_DIM)
  weight_bf16 = _bf16_to_f32(np.frombuffer(_to_bf16_bytes(weight_vec), dtype="<u2"))
  scale = np.sum(x_bf16 * x_bf16, axis=1, dtype=np.float32)
  scale *= np.float32(MEAN_SCALE)
  scale += np.float32(NORM_EPS)
  scale = np.reciprocal(np.sqrt(scale, dtype=np.float32), dtype=np.float32)
  tmp_expected = _bf16_to_f32(np.frombuffer(_to_bf16_bytes(x_bf16 * scale[:, None]), dtype="<u2")).reshape(ROWS, EMB_DIM)
  expected = _bf16_to_f32(np.frombuffer(_to_bf16_bytes(tmp_expected * weight_bf16[None, :]), dtype="<u2")).reshape(ROWS, EMB_DIM)

  device = Device()
  try:
    num_banks = len(device.dram.bank_tiles)
    x_buf = device.dram.alloc(COL_TILES, DTYPE, shape=(ROWS, EMB_DIM), name="rmsnorm_x")
    weight_buf = device.dram.alloc(COL_TILES, DTYPE, shape=(ROWS, EMB_DIM), name="rmsnorm_weight_row")
    out_buf = device.dram.alloc(COL_TILES, DTYPE, shape=(ROWS, EMB_DIM), name="rmsnorm_out")
    device.dram_write(x_buf, _to_bf16_bytes(x))
    device.dram_write(weight_buf, _to_bf16_bytes(weight_tiles))

    dram_bank_coords_noc0 = p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0)
    dram_bank_coords_noc1 = p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1)
    prog = build_program(
      x_buf.addr,
      weight_buf.addr,
      out_buf.addr,
      num_banks,
      dram_bank_coords_noc0=dram_bank_coords_noc0,
      dram_bank_coords_noc1=dram_bank_coords_noc1,
    )
    timings = device.run(prog)
    got = _bf16_to_f32(np.frombuffer(device.dram_read(out_buf), dtype="<u2")).reshape(ROWS, EMB_DIM)
    abs_err = np.abs(got - expected)
    max_abs = float(np.max(abs_err))
    mean_abs = float(np.mean(abs_err))
    rel_l2 = float(np.linalg.norm(got - expected) / max(np.linalg.norm(expected), 1e-12))
    worst_flat = int(np.argmax(abs_err))
    worst_row, worst_col = np.unravel_index(worst_flat, abs_err.shape)
    tolerance = 0.05
    if not np.isfinite(got).all() or max_abs > tolerance:
      for i in range(min(8, ROWS)):
        print(
          f"row {i:02d} col 0: got={got[i, 0]:.8f} "
          f"expected={expected[i, 0]:.8f} err={abs_err[i, 0]:.8f}"
        )
      raise AssertionError(
        f"rmsnorm mismatch max_abs={max_abs:.6g} mean_abs={mean_abs:.6g} rel_l2={rel_l2:.6g} "
        f"worst=({worst_row},{worst_col}) got={got[worst_row, worst_col]:.8f} "
        f"expected={expected[worst_row, worst_col]:.8f}"
      )
    print(
      f"PASS rmsnorm hifi2: max_abs={max_abs:.6g} "
      f"mean_abs={mean_abs:.6g} rel_l2={rel_l2:.6g} worst=({worst_row},{worst_col})"
    )
    for timing in timings:
      name = f"{timing['name']}: " if timing["name"] else ""
      print(f"  {name}{timing['us']:,.1f} us")
  finally:
    device.close()


def main() -> None:
  run()


if __name__ == "__main__":
  main()
