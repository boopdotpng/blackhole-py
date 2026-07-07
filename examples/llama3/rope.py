#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  TTDMANOP, TTINCRWC, TTMOP, TTMOVA2D, TTNOP, TTPACR, TTSEMGET, TTSEMPOST,
  TTSEMWAIT, TTSETRWC, TTSETADC, TTSETADCXX, TTSETADCXY, TTSETADCZW,
  TTSETDMAREG, TTSTALLWAIT, TTSTOREREG, TTRMWCIB0, TTSFPLOAD, TTSFPNOP,
  TTSFPSTORE, TTUNPACR, TTUNPACR_NOP, TTWRCFG, Reg,
  a0, a1, a2, a5, ra, s0, s2, s3, s4, s5, s6, sp, t0, t1, t2, t3, t4, t5,
  t6, zero,
)
from program import Dtype, Program  # noqa: E402
from ttk import Cb, Noc, Tensix  # noqa: E402
from ttk.addrs import p100_dram_bank_endpoint_coords  # noqa: E402
from ttk.cb import CircularBuffer as CB  # noqa: E402
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM, TriscLocalMem as TLM, TriscMailbox  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.sfpu import Sfpu, blackhole_sine_reference  # noqa: E402
from ttk.tensix import (  # noqa: E402
  Cfg, MopCfg, TensixL1, TensixRegs, TensixSem, TensixSemWait, TensixStall,
  TensixWait, ThreadCfg,
)


# This file currently has two bringup paths:
#   1. `upload-table` is the practical Llama3 path: NumPy computes the final
#      f32 COS/SIN tables, Device.dram_write tilizes them, and later kernels
#      consume the tiled DRAM buffers by address.
#   2. `sine-test` is the lower-level SFPU path we were using to shake out
#      f32 unpack/SFPU/pack behavior. It intentionally keeps host-side verifier
#      helpers and is not the production RoPE table path.


@dataclass(frozen=True)
class RiscSync:
  start: int
  trisc_init: int


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

  def __init__(self, thread_id: int, sync: RiscSync, *, base_addr: int = 0):
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


DTYPE = Dtype.Float32
TILE_VALUES = 32 * 32
TILE_BYTES = DTYPE.tile_size
CB_DEPTH = 4
TARGET_CORE = (1, 2)
OUT_CB = 16

ROPE_THETA = 500000.0
ROPE_FACTOR = 32.0
ROPE_LOW_FREQ_FACTOR = 1.0
ROPE_HIGH_FREQ_FACTOR = 4.0
ROPE_ORIGINAL_MAX_POSITION_EMBEDDINGS = 8192
ROPE_MAX_SEQ_LEN = 8192
ROPE_HEAD_DIM = 64
ROPE_SHAPE = (ROPE_MAX_SEQ_LEN, ROPE_HEAD_DIM)
ROPE_COL_TILES = ROPE_HEAD_DIM // 32
ROPE_ROW_TILES = ROPE_MAX_SEQ_LEN // 32
ROPE_TABLE_TILES = ROPE_ROW_TILES * ROPE_COL_TILES

SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
SYNC_L1 = SCRATCH_L1 + 0x10000
SYNC_TRISC_START = SYNC_L1
SYNC_READ = SYNC_L1 + 4
SYNC_DONE0 = SYNC_L1 + 8
SYNC_DONE1 = SYNC_L1 + 12
SYNC_DONE2 = SYNC_L1 + 16
SYNC_TRISC_INIT = SYNC_L1 + 20
SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)
UNPACK_TMP_LO_GPR = 0x12
UNPACK_TMP_LO_GPR_MMIO = TensixRegs.REGFILE_BASE + UNPACK_TMP_LO_GPR * 4
UNPACK_TO_DEST_ADDR_MAILBOX = 0x17A2C0
UNPACK_FP32_Z_STRIDE = 8 * 16 * 4

STALL_MATH_PACK_ROOM = TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU
STALL_MATH_PACK_DATA = TensixStall.TDMA
WAIT_MATH_AND_SFPU = TensixWait.MATH | TensixWait.SFPU
WAIT_THCON_AND_PACK = TensixWait.THCON | TensixWait.PACK0

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
    TTUNPACR(AddrMode=0x11, OvrdThreadId=1, SetDatValid=0, Last=1),
    TTNOP(), TTNOP(), TTNOP(), TTNOP(), TTNOP(), TTNOP(),
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


def parse_core(s: str) -> tuple[int, int]:
  try:
    x, y = s.split(",", 1)
    return int(x, 0), int(y, 0)
  except ValueError as e:
    raise argparse.ArgumentTypeError("core must be X,Y") from e


def select_cores(device: Device, mode: str, core: tuple[int, int]) -> list[tuple[int, int]]:
  if mode == "one":
    return [core]
  if mode == "worker":
    if device.fast_dispatch:
      raise RuntimeError("all-worker mode includes command-queue cores; run with TT_USB=1")
    return list(device.board_info.worker_cores)
  if mode == "program" or device.fast_dispatch:
    return list(device.cores)
  return list(device.board_info.worker_cores)


def logical_tile_ids(core_count: int, tiles_per_core: int, num_banks: int, bank_mode: str) -> list[int]:
  ids = []
  for idx in range(core_count):
    if bank_mode == "spread":
      base = idx * tiles_per_core
      stride = 1
    else:
      bank = idx % num_banks
      page = (idx // num_banks) * tiles_per_core
      base = bank + page * num_banks
      stride = num_banks
    ids.extend(base + tile * stride for tile in range(tiles_per_core))
  return ids


def allocation_tiles_for(core_count: int, tiles_per_core: int, num_banks: int, bank_mode: str) -> int:
  return max(logical_tile_ids(core_count, tiles_per_core, num_banks, bank_mode), default=-1) + 1


def dram_tile_addr_static_bytes(fw: Brisc | Ncrisc, bank_coords: list[int]):
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


def trisc0_set_unpack_to_dest_context(fw: Trisc, ctx_reg=t2, dest_byte_addr_reg=t4) -> Trisc:
  ctx0 = fw._new_label("trisc0_unp_to_dest_set_ctx0")
  done = fw._new_label("trisc0_unp_to_dest_set_done")
  fw.beq(ctx_reg, zero, ctx0)
  fw.read32(a1, Cfg.THCON_SEC0_REG5_Dest_cntx, tmp_addr=t6)
  fw.li(t6, 0x0000FFFF)
  fw.and_(a1, a1, t6)
  fw.slli(dest_byte_addr_reg, dest_byte_addr_reg, 16)
  fw.or_(a1, a1, dest_byte_addr_reg)
  fw.write32(UNPACK_TMP_LO_GPR_MMIO, a1, tmp_addr=t6)
  fw.emit(TTWRCFG(UNPACK_TMP_LO_GPR, 0, Cfg.THCON_SEC0_REG5_Dest_cntx.addr32))
  fw.push_tensix(TTRMWCIB0(Mask=0x10, Data=0x10, CfgRegAddr=Cfg.THCON_SEC0_REG2_1.addr32))
  fw.j(done)

  fw.label(ctx0)
  fw.read32(a1, Cfg.THCON_SEC0_REG5_Dest_cntx, tmp_addr=t6)
  fw.li(t6, 0xFFFF0000)
  fw.and_(a1, a1, t6)
  fw.or_(a1, a1, dest_byte_addr_reg)
  fw.write32(UNPACK_TMP_LO_GPR_MMIO, a1, tmp_addr=t6)
  fw.emit(TTWRCFG(UNPACK_TMP_LO_GPR, 0, Cfg.THCON_SEC0_REG5_Dest_cntx.addr32))
  fw.push_tensix(TTRMWCIB0(Mask=0x20, Data=0x20, CfgRegAddr=Cfg.THCON_SEC0_REG2_1.addr32))
  fw.label(done)
  return fw


def trisc0_restore_unpack_to_dest_context(fw: Trisc, ctx_reg=t2) -> Trisc:
  ctx0 = fw._new_label("trisc0_unp_to_dest_restore_ctx0")
  done = fw._new_label("trisc0_unp_to_dest_restore_done")
  fw.beq(ctx_reg, zero, ctx0)
  fw.read32(a1, Cfg.THCON_SEC0_REG5_Dest_cntx, tmp_addr=t6)
  fw.li(t6, 0x0000FFFF)
  fw.and_(a1, a1, t6)
  fw.li(t6, 64 << 16)
  fw.or_(a1, a1, t6)
  fw.write32(UNPACK_TMP_LO_GPR_MMIO, a1, tmp_addr=t6)
  fw.emit(TTWRCFG(UNPACK_TMP_LO_GPR, 0, Cfg.THCON_SEC0_REG5_Dest_cntx.addr32))
  fw.push_tensix(TTRMWCIB0(Mask=0x10, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2_1.addr32))
  fw.j(done)

  fw.label(ctx0)
  fw.read32(a1, Cfg.THCON_SEC0_REG5_Dest_cntx, tmp_addr=t6)
  fw.li(t6, 0xFFFF0000)
  fw.and_(a1, a1, t6)
  fw.ori(a1, a1, 64)
  fw.write32(UNPACK_TMP_LO_GPR_MMIO, a1, tmp_addr=t6)
  fw.emit(TTWRCFG(UNPACK_TMP_LO_GPR, 0, Cfg.THCON_SEC0_REG5_Dest_cntx.addr32))
  fw.push_tensix(TTRMWCIB0(Mask=0x20, Data=0x00, CfgRegAddr=Cfg.THCON_SEC0_REG2_1.addr32))
  fw.label(done)
  return fw


def trisc0_write_unpack_z_stride(fw: Trisc, stride: int) -> Trisc:
  fw.write32(UNPACK_TMP_LO_GPR_MMIO, stride)
  fw.emit(TTWRCFG(UNPACK_TMP_LO_GPR, 0, Cfg.UNP0_ADDR_CTRL_ZW_REG_1.addr32))
  return fw


def trisc0() -> Trisc:
  fw = Trisc(0, SYNC)
  fw.prologue()
  fw.unpack.init(dtype=DTYPE, tile_bytes=TILE_BYTES, mop_cfg=UNPACK_MOP_CFG, fp32_dest=True)
  trisc0_write_unpack_z_stride(fw, UNPACK_FP32_Z_STRIDE)
  fw.init_barrier()

  with fw.tile_loop():
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

    fw.read32(t4, UNPACK_TO_DEST_ADDR_MAILBOX)
    fw.addi(t4, t4, 4)
    fw.slli(t4, t4, 4)
    fw.setc16(ThreadCfg.SRCA_SET, 0)
    trisc0_set_unpack_to_dest_context(fw, ctx_reg=t1, dest_byte_addr_reg=t4)
    fw.emit(TTSEMWAIT(
      TensixStall.UNPACK,
      TensixSem.mask(TensixSem.UNPACK_TO_DEST),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.THCON | TensixWait.UNPACK0))
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
    trisc0_restore_unpack_to_dest_context(fw, ctx_reg=t1)
    fw.setc16(ThreadCfg.SRCA_SET, 4)
    fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.UNPACK_TO_DEST)))
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


def write_trisc1_dest_offset_instr(fw, offset_id=t1, instr=t2, base=t3):
  fw.sltu(instr, zero, offset_id)
  fw.slli(instr, instr, 9)
  fw.li(base, 0xB2010000)
  fw.add(instr, instr, base)
  return fw.write32(TensixRegs.INSTRN_BUF_BASE, instr, tmp_addr=t0)


def math_sine_body(fw):
  sfpu = Sfpu(fw)
  fw.emit(TTSFPLOAD(0, 3, 7, 0))
  sfpu.emit_sine_polynomial_reduced(fp32_dest=True)
  fw.emit(TTSFPSTORE(0, 3, 7, 0))
  fw.emit(TTINCRWC(0, 2, 0, 0))
  return fw


def math_sine_tile(fw):
  for _face in range(4):
    for _row_group in range(8):
      math_sine_body(fw)
    fw.emit(TTSETRWC(0, 4, 8, 0, 0, 4))
    fw.emit(TTSETRWC(0, 4, 8, 0, 0, 4))
  return fw


def trisc1() -> Trisc:
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=MATH_MOP_CFG)
  Sfpu(fw).sine_init()
  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.slli(t1, t1, 9)
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
      TensixSem.mask(TensixSem.MATH_DONE),
      TensixSemWait.STALL_ON_ZERO,
    ))
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.MATH_DONE)))
    fw.emit(TTSEMWAIT(
      TensixStall.SYNC,
      TensixSem.mask(TensixSem.UNPACK_TO_DEST),
      TensixSemWait.STALL_ON_ZERO,
    ))
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_TO_DEST)))
    fw.emit(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    math_sine_tile(fw)
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
    write_trisc1_dest_offset_instr(fw, t2, t1, t3)
    fw.emit(TTSFPNOP())
  return fw


def trisc2() -> Trisc:
  fw = Trisc(2, SYNC)
  fw.prologue()
  fw.pack.init(dtype=DTYPE, out_cb=OUT_CB, mop_cfg=PACK_MOP_CFG, fp32_dest=True)
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


def brisc(dram_bank_coords: list[int]) -> Brisc:
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4, s6))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)

  with fw.tile_loop("brisc"):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.mul(a1, s5, s6)
    fw.add(a1, s2, a1)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    dram_tile_addr_static_bytes(fw, dram_bank_coords)
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


def ncrisc(dram_bank_coords: list[int]) -> Ncrisc:
  fw = Ncrisc()
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4, s6))

  with fw.tile_loop("ncrisc"):
    fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
    fw.mul(a1, s5, s6)
    fw.add(a1, s2, a1)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    dram_tile_addr_static_bytes(fw, dram_bank_coords)
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
  cores: list[tuple[int, int]],
  tiles_per_core: int,
  bank_mode: str,
  dram_bank_coords_noc0: list[int],
  dram_bank_coords_noc1: list[int],
) -> Program:
  core_index = {core: i for i, core in enumerate(cores)}
  if bank_mode not in ("spread", "local"):
    raise ValueError("bank_mode must be 'spread' or 'local'")

  def tile_base_and_stride(core: tuple[int, int]) -> tuple[int, int]:
    idx = core_index[core]
    if bank_mode == "spread":
      return idx * tiles_per_core, 1
    bank = idx % num_banks
    page = (idx // num_banks) * tiles_per_core
    return bank + page * num_banks, num_banks

  brisc_fw = brisc(dram_bank_coords_noc0)
  ncrisc_fw = ncrisc(dram_bank_coords_noc1)
  trisc0_fw = trisc0()
  trisc1_fw = trisc1()
  trisc2_fw = trisc2()

  def brisc_args(x, y):
    core = (x, y)
    base, stride = tile_base_and_stride(core)
    return [src_addr, base, tiles_per_core, num_banks, stride]

  def ncrisc_args(x, y):
    core = (x, y)
    base, stride = tile_base_and_stride(core)
    return [dst_addr, base, tiles_per_core, num_banks, stride]

  brisc_fw.rta(brisc_args)
  ncrisc_fw.rta(ncrisc_args)
  trisc0_fw.rta(lambda _x, _y: [tiles_per_core])
  trisc1_fw.rta(lambda _x, _y: [tiles_per_core])
  trisc2_fw.rta(lambda _x, _y: [tiles_per_core])

  return Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
    core_order=tuple(cores),
  )


def row_major_to_tiled(vals: np.ndarray) -> np.ndarray:
  tiles = np.asarray(vals, dtype=np.float32).reshape(-1, 32, 32)
  tiled = np.empty((tiles.shape[0], 4, 16, 16), dtype=np.float32)
  tiled[:, 0] = tiles[:, :16, :16]
  tiled[:, 1] = tiles[:, :16, 16:]
  tiled[:, 2] = tiles[:, 16:, :16]
  tiled[:, 3] = tiles[:, 16:, 16:]
  return tiled.reshape(-1)


def tiled_to_row_major(vals: np.ndarray) -> np.ndarray:
  faces = np.asarray(vals, dtype=np.float32).reshape(-1, 4, 16, 16)
  tiles = np.empty((faces.shape[0], 32, 32), dtype=np.float32)
  tiles[:, :16, :16] = faces[:, 0]
  tiles[:, :16, 16:] = faces[:, 1]
  tiles[:, 16:, :16] = faces[:, 2]
  tiles[:, 16:, 16:] = faces[:, 3]
  return tiles.reshape(-1)


def make_sine_input(n_tiles: int) -> tuple[np.ndarray, bytes]:
  vals = np.linspace(-np.pi / 2, np.pi / 2, n_tiles * TILE_VALUES, dtype=np.float32)
  tiled = row_major_to_tiled(vals)
  return vals, np.ascontiguousarray(tiled, dtype="<f4").tobytes()


def make_expected(vals: np.ndarray) -> np.ndarray:
  return np.array([blackhole_sine_reference(float(v), fp32_dest=True) for v in vals], dtype=np.float32)


def run_sine_tile_test(args) -> None:
  if args.tiles_per_core <= 0:
    raise ValueError("--tiles-per-core must be positive")
  if args.core_count <= 0:
    raise ValueError("--core-count must be positive")

  device = Device()
  try:
    cores = select_cores(device, args.cores, args.core)[:args.core_count]
    num_banks = len(device.dram.bank_tiles)
    n_tiles = len(cores) * args.tiles_per_core
    alloc_tiles = allocation_tiles_for(len(cores), args.tiles_per_core, num_banks, args.bank_mode)

    vals, src_rm = make_sine_input(n_tiles)
    src_buf = device.dram.alloc(alloc_tiles, dtype=DTYPE, shape=(alloc_tiles, 32, 32), name="sin_src")
    src_payload = bytearray(src_buf.size)
    for src_tile, dst_tile in enumerate(logical_tile_ids(len(cores), args.tiles_per_core, num_banks, args.bank_mode)):
      src_payload[dst_tile * TILE_BYTES:(dst_tile + 1) * TILE_BYTES] = src_rm[src_tile * TILE_BYTES:(src_tile + 1) * TILE_BYTES]
    device.dram_write(src_buf, bytes(src_payload))

    dst_buf = device.dram.alloc(alloc_tiles, dtype=DTYPE, shape=(alloc_tiles, 32, 32), name="sin_dst")
    prog = build_program(
      src_buf.addr,
      dst_buf.addr,
      num_banks,
      cores=cores,
      tiles_per_core=args.tiles_per_core,
      bank_mode=args.bank_mode,
      dram_bank_coords_noc0=p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0),
      dram_bank_coords_noc1=p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1),
    )
    timings = device.run(prog)
    out_raw = device.dram_read(dst_buf)

    got_bytes = bytearray(n_tiles * TILE_BYTES)
    for src_tile, dst_tile in enumerate(logical_tile_ids(len(cores), args.tiles_per_core, num_banks, args.bank_mode)):
      got_bytes[src_tile * TILE_BYTES:(src_tile + 1) * TILE_BYTES] = out_raw[dst_tile * TILE_BYTES:(dst_tile + 1) * TILE_BYTES]

    got_tiled = np.frombuffer(bytes(got_bytes), dtype="<f4")
    got = tiled_to_row_major(got_tiled)
    expected = make_expected(vals)
    abs_err = np.abs(got - expected)
    max_abs = float(np.nanmax(abs_err))
    mean_abs = float(np.nanmean(abs_err))
    worst = int(np.nanargmax(abs_err))

    if not np.isfinite(got).all() or max_abs > args.max_abs:
      if args.dump:
        for i in range(min(args.dump, got.size)):
          print(f"{i:04d}: input={vals[i]: .8f} got={got[i]: .8f} expected={expected[i]: .8f}")
      raise AssertionError(
        f"sine tile mismatch max_abs={max_abs:.6g} mean_abs={mean_abs:.6g} "
        f"worst={worst} input={vals[worst]:.7g} got={got[worst]:.7g} expected={expected[worst]:.7g}"
      )

    print(
      f"PASS sine f32 tile bank_mode={args.bank_mode}: "
      f"{len(cores)} cores x {args.tiles_per_core} tiles/core, "
      f"max_abs={max_abs:.6g} mean_abs={mean_abs:.6g}"
    )
    for timing in timings:
      name = f"{timing['name']}: " if timing["name"] else ""
      print(f"  {name}{timing['us']:,.1f} us")
  finally:
    device.close()


def llama32_1b_rope_tables_numpy() -> tuple[np.ndarray, np.ndarray]:
  freq_idx = np.arange(0, ROPE_HEAD_DIM, 2, dtype=np.float32)
  inv_freq = 1.0 / (np.float32(ROPE_THETA) ** (freq_idx / np.float32(ROPE_HEAD_DIM)))
  wavelen = np.float32(2.0 * np.pi) / inv_freq
  cycles = np.float32(ROPE_ORIGINAL_MAX_POSITION_EMBEDDINGS) / wavelen
  smooth = np.clip(
    (cycles - np.float32(ROPE_LOW_FREQ_FACTOR)) /
    np.float32(ROPE_HIGH_FREQ_FACTOR - ROPE_LOW_FREQ_FACTOR),
    np.float32(0.0),
    np.float32(1.0),
  )
  scale = np.float32(1.0 / ROPE_FACTOR) + smooth * np.float32(1.0 - (1.0 / ROPE_FACTOR))
  inv_freq = inv_freq * scale

  positions = np.arange(ROPE_MAX_SEQ_LEN, dtype=np.float32)[:, None]
  angles = positions * inv_freq[None, :]
  angles = np.repeat(angles, 2, axis=1).astype(np.float32, copy=False)
  return np.cos(angles).astype(np.float32), np.sin(angles).astype(np.float32)


def run_upload_table(args) -> None:
  cos, sin = llama32_1b_rope_tables_numpy()
  device = Device()
  try:
    cos_buf = device.dram.alloc(cos.size // TILE_VALUES, DTYPE, shape=cos.shape, name="cos_table")
    sin_buf = device.dram.alloc(sin.size // TILE_VALUES, DTYPE, shape=sin.shape, name="sin_table")
    device.dram_write(cos_buf, np.ascontiguousarray(cos, dtype="<f4").tobytes())
    device.dram_write(sin_buf, np.ascontiguousarray(sin, dtype="<f4").tobytes())

    manifest = {
      "dtype": "float32",
      "layout": "tt_tiled_32x32_in_dram",
      "shape": list(ROPE_SHAPE),
      "tile_bytes": TILE_BYTES,
      "tiles_per_table": int(cos.size // TILE_VALUES),
      "cos_name": cos_buf.name,
      "cos_addr": int(cos_buf.addr),
      "sin_name": sin_buf.name,
      "sin_addr": int(sin_buf.addr),
      "rope_theta": ROPE_THETA,
      "rope_factor": ROPE_FACTOR,
      "rope_low_freq_factor": ROPE_LOW_FREQ_FACTOR,
      "rope_high_freq_factor": ROPE_HIGH_FREQ_FACTOR,
      "rope_original_max_position_embeddings": ROPE_ORIGINAL_MAX_POSITION_EMBEDDINGS,
    }

    if args.verify:
      got_cos = np.frombuffer(device.dram_read(cos_buf), dtype="<f4").reshape(cos.shape)
      got_sin = np.frombuffer(device.dram_read(sin_buf), dtype="<f4").reshape(sin.shape)
      cos_err = float(np.max(np.abs(got_cos - cos)))
      sin_err = float(np.max(np.abs(got_sin - sin)))
      manifest["verify"] = {"cos_max_abs": cos_err, "sin_max_abs": sin_err}
      if cos_err or sin_err:
        raise AssertionError(f"RoPE readback mismatch cos={cos_err:.6g} sin={sin_err:.6g}")

    text = json.dumps(manifest, indent=2, sort_keys=True)
    print(text)
    if args.manifest:
      Path(args.manifest).write_text(text + "\n")
  finally:
    device.close()


def parse_args():
  parser = argparse.ArgumentParser(description="Llama3 RoPE table upload and SFPU sine bringup.")
  subparsers = parser.add_subparsers(dest="command")
  parser.set_defaults(verify=False, manifest="")

  upload = subparsers.add_parser("upload-table", help="generate final Llama3 f32 COS/SIN tables on host and copy to DRAM")
  upload.add_argument("--verify", action="store_true")
  upload.add_argument("--manifest", default="")

  sine = subparsers.add_parser("sine-test", help="run the lower-level f32 SFPU sine tile verifier")
  sine.add_argument("--tiles-per-core", type=int, default=1)
  sine.add_argument("--cores", choices=("auto", "program", "worker", "one"), default="one")
  sine.add_argument("--core", type=parse_core, default=TARGET_CORE)
  sine.add_argument("--core-count", type=int, default=1)
  sine.add_argument("--bank-mode", choices=("spread", "local"), default="spread")
  sine.add_argument("--max-abs", type=float, default=0.02)
  sine.add_argument("--dump", type=int, default=0)
  return parser.parse_args()


if __name__ == "__main__":
  args = parse_args()
  if args.command in (None, "upload-table"):
    run_upload_table(args)
  elif args.command == "sine-test":
    run_sine_tile_test(args)
