#!/usr/bin/env python3
from __future__ import annotations
import argparse
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import numpy as np
from asm import KernelBase
from device import Device
from dsl import (
  TTATGETM, TTATRELM, TTDMANOP, TTMOP, TTMOVA2D, TTNOP, TTPACR,
  TTRMWCIB0, TTRMWCIB1, TTRMWCIB2, TTRMWCIB3, TTSETADC,
  TTSEMGET, TTSEMINIT, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSFPCONFIG,
  TTSFPLOADI, TTSETADCXX, TTSETADCXY, TTSETADCZW,
  TTINCRWC, TTREPLAY, TTSFPADDI, TTSFPLOAD, TTSFPNOP, TTSFPSTORE,
  TTSETC16, TTSETDMAREG, TTSTALLWAIT, TTSTOREREG, TTUNPACR, TTUNPACR_NOP,
  TTWRCFG, TTZEROACC, TTZEROSRC, Reg,
  a0, a1, a2, a5, ra, s0, s2, s3, s4, s5, s6, s7, s8, sp, t0, t1, t2, t3, t4, t5, t6, zero,
)
from matmul_peak import RiscSync
from program import Dtype, Program
from ttk.addrs import Dram, noc_xy, p100_dram_bank_base_coords, p100_dram_bank_endpoint_coords
from ttk.blackhole_coords import directional_torus_hops, raw_coord_for_noc, tensix_coordinate_map, translated_tensix_to_raw_noc0
from ttk import Cb, Noc, Tensix
from ttk.cb import CircularBuffer as CB
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM, TriscLocalMem as TLM, TriscMailbox
from ttk.noc import NOC
from ttk.tensix import (
  Cfg, GprPack, GprUnpack, MopCfg, TensixL1, TensixRegs, TensixSem,
  TensixSemWait, TensixStall, TensixWait, ThreadCfg,
)


class _RoleKernel(KernelBase):
  """Shared scaffolding for the per-thread role kernels: the standard
  ``count``-driven tile loop. Subclasses pick their own mixin set and override
  ``_loop_epilogue`` to emit the right return sequence."""

  def _loop_epilogue(self):
    return self.ret()

  @contextmanager
  def tile_loop(self, name: str, *, count: Reg = s3, counter: Reg = s5) -> Iterator[None]:
    """Emit ``for counter in range(count)`` around the yielded body, closing
    with the role's epilogue. ``count`` is loaded by the kernel prologue
    (typically the per-core tile count in s3)."""
    self.li(counter, 0)
    self.label(f"{name}_loop")
    self.beq(counter, count, f"{name}_done")
    yield
    self.addi(counter, counter, 1)
    self.j(f"{name}_loop")
    self.label(f"{name}_done")
    self._loop_epilogue()


class Trisc(_RoleKernel, Tensix, Cb):
  """Compute-thread kernel (unpack / math / pack). Composes the Tensix and CB
  helpers — no NOC, since TRISCs never drive the NOC directly. Provides the
  prologue / init-barrier / tile-loop scaffolding common to every TRISC so a
  concrete kernel only fills in its op-specific config and loop body."""

  NUM_TRISC = 3

  def __init__(self, thread_id: int, sync: RiscSync, *, base_addr: int = 0):
    super().__init__(base_addr=base_addr)
    self.thread_id = thread_id
    self.sync = sync
    # DATA1 has a distinct mailbox layout; TRISC0/2 share DATA_COMMON.
    self.data = TriscMailbox.DATA1 if thread_id == 1 else TriscMailbox.DATA_COMMON
    # Tier-2 bound helpers (composition, not inheritance).
    from ttk.math import Math
    from ttk.pack import Pack
    from ttk.unpack import Unpack
    self.unpack = Unpack(self)
    self.pack = Pack(self)
    self.math = Math(self)

  def prologue(self):
    """Stack frame, load per-core tile count into s3, then wait for BRISC's
    start signal and clear it."""
    self.addi(sp, sp, -16)
    self.sw(ra, sp, 12)
    self.read32(t0, self.data["rta_l1_base"])
    self.lw(s3, t0, 0)
    self.wait8(self.sync.start + self.thread_id, 1)
    self.write8(self.sync.start + self.thread_id, 0)
    return self

  def init_barrier(self):
    """Publish this thread's init-done flag, then wait for all TRISCs."""
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
  """Reader-thread kernel: NOC + CB helpers, no Tensix config."""


class Ncrisc(_RoleKernel, Noc, Cb):
  """Writer-thread kernel: NOC + CB helpers, no Tensix config."""

TILE_BYTES = Dtype.Float16_b.tile_size
CB_DEPTH = 16
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

  fw.unpack.init(dtype=Dtype.Float16_b, tile_bytes=TILE_BYTES, mop_cfg=UNPACK_MOP_CFG)

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

def math_add1_replay_row(fw):
  """add1's compute core: SFPU load -> +1.0 (0x3F80) -> store, replayed across a
  face. This is the op-specific body of the math thread, not a ttk primitive."""
  fw.emit(TTREPLAY(0, 5, 1, 1))
  fw.emit(TTSFPLOAD(0, 0, 7, 0))
  fw.emit(TTSFPADDI(0x3F80, 0, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTSFPSTORE(0, 0, 7, 0))
  fw.emit(TTINCRWC(0, 2, 0, 0))
  for _ in range(7):
    fw.emit(TTREPLAY(0, 5, 0, 0))
  fw.emit(TTSETRWC(0, 4, 8, 0, 0, 4))
  return fw.emit(TTSETRWC(0, 4, 8, 0, 0, 4))


def write_trisc1_dest_offset_instr(fw, offset_id=t1, instr=t2, base=t3):
  """Patch the math dest base-address instruction for the current double-buffer
  half (dest_offset_id 0/1). Specific to add1's math<->pack dest ping-pong."""
  fw.sltu(instr, zero, offset_id)
  fw.slli(instr, instr, 9)
  fw.li(base, 0xB2010000)
  fw.add(instr, instr, base)
  return fw.write32(TensixRegs.INSTRN_BUF_BASE, instr, tmp_addr=t0)


def trisc1() -> Trisc:
  fw = Trisc(1, SYNC)
  fw.prologue()

  fw.math.init(dtype=Dtype.Float16_b, mop_cfg=MATH_MOP_CFG)

  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    for _ in range(4):
      math_add1_replay_row(fw)
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
  return fw


def trisc2() -> Trisc:
  fw = Trisc(2, SYNC)
  fw.prologue()

  fw.pack.init(dtype=Dtype.Float16_b, out_cb=OUT_CB, mop_cfg=PACK_MOP_CFG)

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


def dram_tile_addr_static_endpoint(fw: Brisc | Ncrisc, endpoint_coords: list[list[int]]):
  fw.mv(t0, a1)
  fw.remu(a1, t0, a2)
  fw.divu(t0, t0, a2)
  fw.slli(t0, t0, 11)
  fw.add(a0, a0, t0)
  fw.li(a2, endpoint_coords[0][0])
  for bank, coords in enumerate(endpoint_coords):
    for endpoint, coord in enumerate(coords):
      next_coord = fw._new_label("dram_endpoint_coord")
      fw.li(t1, bank)
      fw.bne(a1, t1, next_coord)
      fw.li(t1, endpoint)
      fw.bne(s7, t1, next_coord)
      fw.li(a2, coord)
      fw.label(next_coord)
  return fw


def dram_tile_addr_rta_coords(fw: Brisc | Ncrisc, *, coord_offset_words: int):
  fw.mv(t0, a1)
  fw.remu(a1, t0, a2)
  fw.divu(t0, t0, a2)
  fw.slli(t0, t0, 11)
  fw.add(a0, a0, t0)
  fw.slli(t1, a1, 2)
  fw.add(t1, s8, t1)
  return fw.lw(a2, t1, coord_offset_words * 4)


def brisc(dram_bank_coords: list[int], dram_bank_endpoint_coords: list[list[int]] | None = None,
          *, rta_coord_table: bool = False) -> Brisc:
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4, s6, s7))
  if rta_coord_table:
    fw.read32(s8, BM.RTA_L1_BASE_PTR)
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
    if rta_coord_table:
      dram_tile_addr_rta_coords(fw, coord_offset_words=6)
    elif dram_bank_endpoint_coords is None:
      fw.dram_tile_addr_static(dram_bank_coords)
    else:
      dram_tile_addr_static_endpoint(fw, dram_bank_endpoint_coords)
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


def ncrisc(dram_bank_coords: list[int], dram_bank_endpoint_coords: list[list[int]] | None = None,
           *, rta_coord_table: bool = False) -> Ncrisc:
  fw = Ncrisc()
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4, s6, s7))
  if rta_coord_table:
    fw.read32(s8, NM.RTA_L1_BASE_PTR)
  with fw.tile_loop("ncrisc"):
    fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
    fw.mul(a1, s5, s6)
    fw.add(a1, s2, a1)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    if rta_coord_table:
      dram_tile_addr_rta_coords(fw, coord_offset_words=6)
    elif dram_bank_endpoint_coords is None:
      fw.dram_tile_addr_static(dram_bank_coords)
    else:
      dram_tile_addr_static_endpoint(fw, dram_bank_endpoint_coords)
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
  dram_bank_coords_noc0: list[int] | None = None,
  dram_bank_coords_noc1: list[int] | None = None,
  dram_bank_endpoint_coords_noc0: list[list[int]] | None = None,
  dram_bank_endpoint_coords_noc1: list[list[int]] | None = None,
  read_endpoint_mode: str = "preferred",
  write_endpoint_mode: str = "preferred",
  nearest_read_coords: dict[tuple[int, int], list[int]] | None = None,
  nearest_write_coords: dict[tuple[int, int], list[int]] | None = None,
  bank_mode: str = "spread",
  use_grid: bool = True,
) -> Program:
  if cores is None:
    cores = [TARGET_CORE]
  if dram_bank_coords_noc0 is None:
    dram_bank_coords_noc0 = p100_dram_bank_endpoint_coords(None, 0)[:num_banks]
  if dram_bank_coords_noc1 is None:
    dram_bank_coords_noc1 = p100_dram_bank_endpoint_coords(None, 1)[:num_banks]
  if dram_bank_endpoint_coords_noc0 is None:
    dram_bank_endpoint_coords_noc0 = p100_dram_bank_endpoint_coord_table(None, num_banks)
  if dram_bank_endpoint_coords_noc1 is None:
    dram_bank_endpoint_coords_noc1 = p100_dram_bank_endpoint_coord_table(None, num_banks)
  core_index = {core: i for i, core in enumerate(cores)}
  if bank_mode not in ("spread", "local"):
    raise ValueError("bank_mode must be 'spread' or 'local'")
  if read_endpoint_mode not in ("preferred", "split3", "nearest"):
    raise ValueError("read_endpoint_mode must be 'preferred', 'split3', or 'nearest'")
  if write_endpoint_mode not in ("preferred", "split3", "nearest"):
    raise ValueError("write_endpoint_mode must be 'preferred', 'split3', or 'nearest'")
  if read_endpoint_mode == "nearest" and nearest_read_coords is None:
    raise ValueError("read_endpoint_mode='nearest' needs nearest_read_coords")
  if write_endpoint_mode == "nearest" and nearest_write_coords is None:
    raise ValueError("write_endpoint_mode='nearest' needs nearest_write_coords")

  def tile_base_and_stride(core: tuple[int, int]) -> tuple[int, int]:
    idx = core_index[core]
    if bank_mode == "spread":
      return base_tile_offset + idx * tiles_per_core, 1
    bank = idx % num_banks
    page = (idx // num_banks) * tiles_per_core
    return base_tile_offset + bank + page * num_banks, num_banks

  brisc_fw = brisc(
    dram_bank_coords_noc0,
    dram_bank_endpoint_coords_noc0 if read_endpoint_mode == "split3" else None,
    rta_coord_table=read_endpoint_mode == "nearest",
  )
  ncrisc_fw = ncrisc(
    dram_bank_coords_noc1,
    dram_bank_endpoint_coords_noc1 if write_endpoint_mode == "split3" else None,
    rta_coord_table=write_endpoint_mode == "nearest",
  )
  trisc0_fw = trisc0()
  trisc1_fw = trisc1()
  trisc2_fw = trisc2()
  def brisc_args(x, y):
    core = (x, y)
    args = [
      src_addr, tile_base_and_stride(core)[0], tiles_per_core, num_banks,
      tile_base_and_stride(core)[1], core_index[core] % 3,
    ]
    if read_endpoint_mode == "nearest":
      args.extend(nearest_read_coords[core])
    return args

  def ncrisc_args(x, y):
    core = (x, y)
    args = [
      dst_addr, tile_base_and_stride(core)[0], tiles_per_core, num_banks,
      tile_base_and_stride(core)[1], core_index[core] % 3,
    ]
    if write_endpoint_mode == "nearest":
      args.extend(nearest_write_coords[core])
    return args

  brisc_fw.rta(brisc_args)
  ncrisc_fw.rta(ncrisc_args)
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
  else:
    prog.num_cores = len(cores)
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
  parser.add_argument("--core-count", type=int, default=None,
                      help="limit selected cores to the first N cores")
  parser.add_argument("--bank-mode", choices=("spread", "local"), default="spread",
                      help="spread round-robins each core across DRAM banks; local pins each core to one bank")
  parser.add_argument("--read-endpoint-mode", choices=("preferred", "split3", "nearest"), default="preferred",
                      help="DRAM endpoint selection for BRISC reads")
  parser.add_argument("--write-endpoint-mode", choices=("preferred", "split3", "nearest"), default="preferred",
                      help="DRAM endpoint selection for NCRISC writes")
  parser.add_argument("--no-verify", action="store_true",
                      help="skip host readback/compare of the output buffer")
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
  values = np.arange(n_tiles * 32 * 32, dtype="<f4")
  return (values.view("<u4") >> 16).astype("<u2").tobytes()

def make_expected(src_rm: bytes) -> bytes:
  src = np.frombuffer(src_rm, dtype="<u2").astype("<u4") << 16
  out = (src.view("<f4") + np.float32(1.0)).view("<u4")
  return (out >> 16).astype("<u2").tobytes()

def p100_dram_bank_endpoint_coord_table(harvested_dram_bank: int | None, num_banks: int) -> list[list[int]]:
  bank_base = p100_dram_bank_base_coords(harvested_dram_bank)
  return [[noc_xy(bank_base[bank][0], bank_base[bank][1] + endpoint) for endpoint in range(3)] for bank in range(num_banks)]

def nearest_dram_endpoint_coords_for_cores(
  cores: list[tuple[int, int]], *, harvested_dram_bank: int | None, enabled_tensix_col: int,
  num_banks: int, noc: int,
) -> dict[tuple[int, int], list[int]]:
  cmap = tensix_coordinate_map(enabled_tensix_col)
  endpoint_table = p100_dram_bank_endpoint_coord_table(harvested_dram_bank, num_banks)
  out: dict[tuple[int, int], list[int]] = {}
  for core in cores:
    raw_core_noc0 = translated_tensix_to_raw_noc0(core, cmap)
    raw_core = raw_coord_for_noc(raw_core_noc0, noc)
    coords = []
    for bank in range(num_banks):
      candidates = []
      for endpoint, virtual_coord in enumerate(endpoint_table[bank]):
        raw_dram_noc0 = (Dram.BANK_X[bank], Dram.BANK_TILE_YS[bank][endpoint])
        raw_dram = raw_coord_for_noc(raw_dram_noc0, noc)
        total_hops, x_hops, y_hops = directional_torus_hops(raw_core, raw_dram, noc)
        candidates.append((total_hops, y_hops, x_hops, endpoint, virtual_coord))
      coords.append(min(candidates)[4])
    out[core] = coords
  return out

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

def verify_output_tiles(out: bytes, src_rm: bytes, *, core_count: int, tiles_per_core: int, num_banks: int, bank_mode: str):
  exp = make_expected(src_rm)
  tile_ids = logical_tile_ids(core_count, tiles_per_core, num_banks, bank_mode)
  for src_tile, dst_tile in enumerate(tile_ids):
    src_off = src_tile * TILE_BYTES
    dst_off = dst_tile * TILE_BYTES
    got = out[dst_off:dst_off + TILE_BYTES]
    want = exp[src_off:src_off + TILE_BYTES]
    if got != want:
      mismatch = next(i for i, (g, e) in enumerate(zip(got, want)) if g != e)
      abs_mismatch = dst_off + mismatch
      got_bytes = got[mismatch:mismatch + 32].hex()
      want_bytes = want[mismatch:mismatch + 32].hex()
      raise AssertionError(f"mismatch byte={abs_mismatch} got={got_bytes} exp={want_bytes}")

def main():
  args = make_argparser().parse_args()
  if args.tiles_per_core <= 0:
    raise ValueError("--tiles-per-core must be positive")

  device = Device()
  try:
    cores, use_grid = select_cores(device, args.cores, args.core)
    if args.core_count is not None:
      if args.core_count <= 0:
        raise ValueError("--core-count must be positive")
      cores = cores[:args.core_count]
    num_banks = len(device.dram.bank_tiles)
    layout = device.dev.telemetry_layout()
    enabled_tensix_col = device.dev.telemetry_tag(layout, 34)
    if enabled_tensix_col is None and (args.read_endpoint_mode == "nearest" or args.write_endpoint_mode == "nearest"):
      raise RuntimeError("nearest endpoint mode needs ENABLED_TENSIX_COL telemetry")
    nearest_read = None
    nearest_write = None
    if args.read_endpoint_mode == "nearest":
      nearest_read = nearest_dram_endpoint_coords_for_cores(
        cores, harvested_dram_bank=device.board_info.harvested_dram_bank,
        enabled_tensix_col=enabled_tensix_col, num_banks=num_banks, noc=0,
      )
    if args.write_endpoint_mode == "nearest":
      nearest_write = nearest_dram_endpoint_coords_for_cores(
        cores, harvested_dram_bank=device.board_info.harvested_dram_bank,
        enabled_tensix_col=enabled_tensix_col, num_banks=num_banks, noc=1,
      )
    n_tiles = len(cores) * args.tiles_per_core
    alloc_tiles = allocation_tiles_for(len(cores), args.tiles_per_core, num_banks, args.bank_mode)
    src_rm = make_input(n_tiles)
    src_buf = device.dram.alloc(alloc_tiles, dtype=Dtype.Float16_b, shape=(alloc_tiles, 32, 32), name="src")
    src_payload = bytearray(src_buf.size)
    for src_tile, dst_tile in enumerate(logical_tile_ids(len(cores), args.tiles_per_core, num_banks, args.bank_mode)):
      src_payload[dst_tile * TILE_BYTES:(dst_tile + 1) * TILE_BYTES] = src_rm[src_tile * TILE_BYTES:(src_tile + 1) * TILE_BYTES]
    device.dram_write(src_buf, bytes(src_payload))
    dst_buf = device.dram.alloc(alloc_tiles, dtype=Dtype.Float16_b, shape=(alloc_tiles, 32, 32), name="dst")
    prog = build_program(
      src_buf.addr,
      dst_buf.addr,
      num_banks,
      cores=cores,
      tiles_per_core=args.tiles_per_core,
      dram_bank_coords_noc0=p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 0),
      dram_bank_coords_noc1=p100_dram_bank_endpoint_coords(device.board_info.harvested_dram_bank, 1),
      dram_bank_endpoint_coords_noc0=p100_dram_bank_endpoint_coord_table(device.board_info.harvested_dram_bank, num_banks),
      dram_bank_endpoint_coords_noc1=p100_dram_bank_endpoint_coord_table(device.board_info.harvested_dram_bank, num_banks),
      read_endpoint_mode=args.read_endpoint_mode,
      write_endpoint_mode=args.write_endpoint_mode,
      nearest_read_coords=nearest_read,
      nearest_write_coords=nearest_write,
      bank_mode=args.bank_mode,
      use_grid=use_grid,
    )
    timings = device.run(prog)
    if not args.no_verify:
      out = device.dram_read(dst_buf)
      verify_output_tiles(
        out, src_rm,
        core_count=len(cores), tiles_per_core=args.tiles_per_core,
        num_banks=num_banks, bank_mode=args.bank_mode,
      )
    total_bytes = n_tiles * TILE_BYTES
    print(
      f"PASS add1 bank_mode={args.bank_mode} read_endpoint={args.read_endpoint_mode} "
      f"write_endpoint={args.write_endpoint_mode} {len(cores)} cores x {args.tiles_per_core} tiles/core = {n_tiles} tiles"
    )
    for timing in timings:
      name = f"{timing['name']}: " if timing["name"] else ""
      us = timing["us"]
      gbps = (total_bytes * 3) / (us * 1e-6) / 1e9 if us > 0 else 0.0
      print(f"  {name}{us:,.1f} us, {gbps:.1f} GB/s effective add1 traffic")
  finally:
    device.close()


if __name__ == "__main__":
  main()
