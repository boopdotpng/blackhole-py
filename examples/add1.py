#!/usr/bin/env python3
from __future__ import annotations

import struct
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from device import Device
from dsl import (
  TTATGETM, TTATRELM, TTDMANOP, TTINCRWC, TTMOP, TTNOP, TTREPLAY, TTSETADC,
  TTSEMGET, TTSEMINIT, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSFPADDI, TTSFPCONFIG,
  TTSFPLOAD, TTSFPLOADI, TTSFPNOP, TTSFPSTORE, TTSETADCXX, TTSETADCXY, TTSETADCZW,
  TTSETC16, TTSETDMAREG, TTSTALLWAIT, TTSTOREREG, TTWRCFG, TTZEROACC, TTZEROSRC,
  a0, a1, a2, a5, ra, s0, s2, s3, s4, s5, sp, t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk.addrs import (
  BriscMailbox as BM, CircularBuffer as CB, NcriscMailbox as NM, NOC, TensixL1, TriscMailbox as TM,
)
from ttk.tensix import TensixRegs, TensixSem

TILE_BYTES = Dtype.Float16_b.tile_size
CB_DEPTH = 2
TARGET_CORE = (1, 2)
TILES_PER_CORE = 1
OUT_CB = 16
_RUN_EPOCH = 0
SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
SYNC_L1 = SCRATCH_L1 + 0x10000
SYNC_OUT_RESERVED = SYNC_L1
SYNC_READ = SYNC_L1 + 4
SYNC_DONE0 = SYNC_L1 + 8
SYNC_DONE1 = SYNC_L1 + 12
SYNC_DONE2 = SYNC_L1 + 16
SYNC_TRISC_INIT = SYNC_L1 + 20
SYNC_TENSIX_INIT_ONCE = SYNC_L1 + 32
SYNC_CLOCK_START_LO = SYNC_L1 + 44
SYNC_CLOCK_START_HI = SYNC_L1 + 48
SYNC_CLOCK_END_LO = SYNC_L1 + 52
SYNC_CLOCK_END_HI = SYNC_L1 + 56
TRISC0_UNP_CFG_CONTEXT = 0xFFB00420
TRISC1_UNPACK_TILE_NUM_FACES = 0xFFB00020
TRISC1_UNPACK_DST_FORMAT = TRISC1_UNPACK_TILE_NUM_FACES + 32
TRISC1_UNPACK_SRC_FORMAT = TRISC1_UNPACK_TILE_NUM_FACES + 160
TRISC2_PACK_TILE_FACE_R_DIM = 0xFFB00820
TRISC2_PACK_TILE_NUM_FACES = TRISC2_PACK_TILE_FACE_R_DIM + 32
TRISC2_PACK_PARTIAL_FACE = TRISC2_PACK_TILE_FACE_R_DIM + 64
TRISC2_PACK_SRC_FORMAT = TRISC2_PACK_TILE_FACE_R_DIM + 96
TRISC2_PACK_DST_FORMAT = TRISC2_PACK_TILE_FACE_R_DIM + 128
TENSIX_MOP_CFG = 0xFFB80000
TENSIX_PC_BUF_SYNC = 0xFFE80004
TENSIX_PC_BUF_MOP_SYNC = 0xFFE80008
TENSIX_PC_UNPACK_SYNC = 0xFFE80034
PCBUF_SEM_BASE = 0xFFE80020
PACK_MOP_CFG = [
  4, 4, 0x02000000, 0x02000000, 0x02000000,
  0x41000000, 0x02000000, 0x41008001, 0x41010000,
]
UNPACK_MOP_CFG = [
  4, 1, 0x420080C1, 0x02000000, 0x02000000,
  0x43800101, 0x02000000, 0x43800101, 0x43800101,
]
MATH_MOP_CFG = [
  4, 2, 0x02000000, 0x37C00003, 0x02000000,
  0x1200A000, 0x02000000, 0x1200A000, 0x1200A000,
]


def _bf16(x: float) -> int:
  return struct.unpack("<I", struct.pack("<f", x))[0] >> 16


def _f32(x: int) -> float:
  return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]


def _seed_src_tensor(num_tiles: int) -> bytes:
  return b"".join(_bf16(float(i)).to_bytes(2, "little") for i in range(num_tiles * 32 * 32))


def _expected_add1(src: bytes) -> bytes:
  out = bytearray(len(src))
  for i in range(0, len(src), 2):
    x = int.from_bytes(src[i : i + 2], "little")
    y = _bf16(_f32(x) + 1.0)
    out[i : i + 2] = y.to_bytes(2, "little")
  return bytes(out)


def _first_mismatch(got: bytes, exp: bytes) -> int | None:
  return next((i for i, (g, e) in enumerate(zip(got, exp)) if g != e), None)


def _local_noc0_coord(fw: Kernel, out=a5):
  fw.read8(t0, BM.MY_X, tmp_addr=t2)
  fw.read8(t1, BM.MY_Y, tmp_addr=t2)
  fw.slli(t1, t1, 6)
  fw.or_(out, t0, t1)


def _read_rta_from(fw: Kernel, rta_ptr_addr: int, regs):
  fw.read32(t0, rta_ptr_addr)
  for i, reg in enumerate(regs):
    fw.lw(reg, t0, i * 4)


def _dram_tile_addr_from(fw: Kernel, table_base: int, noc_table_offset: int = 0):
  fw.mv(t0, a1)
  fw.remu(a1, t0, a2)
  fw.divu(t0, t0, a2)
  fw.slli(t0, t0, 11)
  fw.add(a0, a0, t0)
  fw.addi(t1, a1, noc_table_offset)
  fw.slli(t1, t1, 1)
  fw.li(t2, table_base)
  fw.add(t2, t2, t1)
  fw.lhu(a2, t2, 0)


def _wait_sync_value(fw: Kernel, addr: int, value_reg, *, ptr=t0, actual=t1):
  done = fw._new_label("wait_sync_done")
  loop = fw._new_label("wait_sync")
  fw.li(ptr, addr)
  fw.label(loop)
  fw.lw(actual, ptr, 0)
  fw.beq(actual, value_reg, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  fw.fence()


def _wait_sync_at_least(fw: Kernel, addr: int, value_reg, *, ptr=t0, actual=t1):
  done = fw._new_label("wait_sync_at_least_done")
  loop = fw._new_label("wait_sync_at_least")
  fw.li(ptr, addr)
  fw.label(loop)
  fw.lw(actual, ptr, 0)
  fw.bge(actual, value_reg, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  fw.fence()


def _signal_sync(fw: Kernel, addr: int, value_reg):
  fw.write32(addr, value_reg, tmp_addr=t0, tmp_val=t1)


def _cb_iface(fw: Kernel, interface_base: int, cb_index: int, *, out=t6):
  fw.li(out, interface_base + cb_index * CB.LOCAL_INTERFACE_SIZE)


def _cb_counter_low(fw: Kernel, out, counter_reg):
  fw.slli(out, counter_reg, 16)
  fw.srli(out, out, 16)


def _cb_counter_high(fw: Kernel, out, counter_reg):
  fw.srli(out, counter_reg, 16)


def _cb_reserve_back(fw: Kernel, interface_base: int, cb_index: int):
  iface, received, acked, free_pages, num_pages = t6, t5, t4, t3, t2
  _cb_iface(fw, interface_base, cb_index, out=iface)
  fw.lw(received, iface, 24)
  _cb_counter_high(fw, received, received)
  loop = fw._new_label("cb_reserve")
  done = fw._new_label("cb_reserve_done")
  fw.label(loop)
  fw.li(acked, CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE)
  fw.lhu(acked, acked, 0)
  fw.sub(free_pages, received, acked)
  fw.lw(num_pages, iface, 12)
  fw.sub(free_pages, num_pages, free_pages)
  fw.li(num_pages, 1)
  fw.bge(free_pages, num_pages, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  fw.fence()


def _cb_push_back(fw: Kernel, interface_base: int, cb_index: int):
  iface, ptr, tmp, counter, acked, received = t6, t5, t4, t3, t2, t1
  _cb_iface(fw, interface_base, cb_index, out=iface)
  fw.lw(ptr, iface, 20)
  fw.lw(tmp, iface, 8)
  fw.add(ptr, ptr, tmp)
  fw.lw(tmp, iface, 4)
  no_wrap = fw._new_label("cb_push_no_wrap")
  fw.bltu(ptr, tmp, no_wrap)
  fw.lw(tmp, iface, 0)
  fw.sub(ptr, ptr, tmp)
  fw.label(no_wrap)
  fw.sw(ptr, iface, 20)

  fw.lw(counter, iface, 24)
  _cb_counter_low(fw, acked, counter)
  _cb_counter_high(fw, received, counter)
  fw.addi(received, received, 1)
  fw.slli(received, received, 16)
  fw.or_(counter, received, acked)
  fw.sw(counter, iface, 24)
  fw.srli(received, received, 16)
  fw.li(tmp, CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE)
  fw.sw(received, tmp, 0)
  fw.fence()


def _cb_wait_front(fw: Kernel, interface_base: int, cb_index: int):
  iface, counter, acked, received, available, need = t6, t5, t4, t3, t2, t1
  _cb_iface(fw, interface_base, cb_index, out=iface)
  fw.lw(counter, iface, 24)
  _cb_counter_low(fw, acked, counter)
  loop = fw._new_label("cb_wait_front")
  done = fw._new_label("cb_wait_front_done")
  fw.label(loop)
  fw.li(received, CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE)
  fw.lhu(received, received, 0)
  fw.sub(available, received, acked)
  fw.li(need, 1)
  fw.bgeu(available, need, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  fw.fence()


def _cb_pop_front(fw: Kernel, interface_base: int, cb_index: int, *, tensix_ack: bool = False):
  iface, ptr, tmp, counter, acked, received = t6, t5, t4, t3, t2, t1
  _cb_iface(fw, interface_base, cb_index, out=iface)
  fw.lw(counter, iface, 24)
  _cb_counter_low(fw, acked, counter)
  _cb_counter_high(fw, received, counter)
  fw.addi(acked, acked, 1)
  _cb_counter_low(fw, acked, acked)
  fw.slli(received, received, 16)
  fw.or_(counter, received, acked)
  fw.sw(counter, iface, 24)
  fw.li(tmp, CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE)
  fw.sw(acked, tmp, 0)
  if tensix_ack:
    fw.slli(tmp, acked, 8)
    fw.li(ptr, TTSETDMAREG(0, 0, 0, 8).raw_word())
    fw.add(tmp, tmp, ptr)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, tmp, tmp_addr=ptr, tmp_val=t0)
    _push_tensix(fw, TTSTALLWAIT(32, 6))
    _write_tensix_instr_word(
      fw,
      TTSTOREREG(4, ((CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE) >> 2) & 0x3FFFF).raw_word(),
    )

  fw.lw(ptr, iface, 16)
  fw.lw(tmp, iface, 8)
  fw.add(ptr, ptr, tmp)
  fw.lw(tmp, iface, 4)
  no_wrap = fw._new_label("cb_pop_no_wrap")
  fw.bltu(ptr, tmp, no_wrap)
  fw.lw(tmp, iface, 0)
  fw.sub(ptr, ptr, tmp)
  fw.label(no_wrap)
  fw.sw(ptr, iface, 16)
  fw.fence()


def _cb_write_ptr(fw: Kernel, interface_base: int, cb_index: int, *, out=t5, shift_to_bytes: bool = False):
  _cb_iface(fw, interface_base, cb_index, out=t6)
  fw.lw(out, t6, 20)
  if shift_to_bytes:
    fw.slli(out, out, 4)


def _cb_read_ptr(fw: Kernel, interface_base: int, cb_index: int, *, out=t5, shift_to_bytes: bool = False):
  _cb_iface(fw, interface_base, cb_index, out=t6)
  fw.lw(out, t6, 16)
  if shift_to_bytes:
    fw.slli(out, out, 4)


def _tt_raw(inst) -> int:
  return inst.raw_word() if hasattr(inst, "raw_word") else int(inst) & 0xFFFFFFFF


def _push_tensix(fw: Kernel, inst, *, tmp_addr=t0, tmp_val=t1):
  fw.emit(inst)


def _write_tensix_instr_word(fw: Kernel, word: int | object, *, tmp_addr=t0, tmp_val=t1):
  # Runtime instruction-buffer writes take raw Tensix words. The RISC-V
  # inline rotation only applies when TTInst objects are embedded in the
  # kernel instruction stream via fw.emit(...).
  fw.write32(TensixRegs.INSTRN_BUF_BASE, _tt_raw(word), tmp_addr=tmp_addr, tmp_val=tmp_val)


def _mop_sync(fw: Kernel, trisc_id: int = 0, *, tmp=t0):
  fw.write32(TENSIX_PC_BUF_MOP_SYNC, 0, tmp_addr=t0, tmp_val=t1)
  fw.read32(tmp, TENSIX_PC_BUF_MOP_SYNC, tmp_addr=t1)
  fw.and_(zero, zero, tmp)


def _write_mop_cfg(fw: Kernel, words: list[int], trisc_id: int = 0, *, ptr=t0, tmp=t1):
  _mop_sync(fw, trisc_id, tmp=tmp)
  fw.li(ptr, TENSIX_MOP_CFG)
  for i, word in enumerate(words):
    fw.li(tmp, word)
    fw.sw(tmp, ptr, i * 4)


def _ret_kernel(fw: Kernel):
  fw.lw(ra, sp, 12)
  fw.addi(sp, sp, 16)
  fw.ret()


def _tensix_sync(fw: Kernel, trisc_id: int = 0, *, tmp=t0):
  fw.write32(TENSIX_PC_BUF_SYNC, 0, tmp_addr=t0, tmp_val=t1)
  fw.read32(tmp, TENSIX_PC_BUF_SYNC, tmp_addr=t1)
  fw.and_(zero, zero, tmp)


def _write_repeated_bytes(fw: Kernel, addr: int, value: int, count_words: int, *, ptr=t0, tmp=t1):
  byte = value & 0xFF
  fw.li(ptr, addr)
  fw.li(tmp, byte | (byte << 8) | (byte << 16) | (byte << 24))
  for i in range(count_words):
    fw.sw(tmp, ptr, i * 4)


def _math_direct_mova2d_init(fw: Kernel):
  _push_tensix(fw, TTSETC16(15, 0))
  _push_tensix(fw, TTSETC16(31, 0))
  _push_tensix(fw, TTSETC16(50, 0))
  _push_tensix(fw, TTSETC16(12, 1))
  _push_tensix(fw, TTSETC16(28, 1))
  _push_tensix(fw, TTSETC16(47, 0))
  _push_tensix(fw, TTSETC16(14, 8))
  _push_tensix(fw, TTSETC16(30, 8))
  _push_tensix(fw, TTSETC16(49, 0))
  _push_tensix(fw, TTSETC16(7, 0))
  _push_tensix(fw, TTSETRWC(0, 0, 0, 0, 0, 15))


def _math_add1_replay_row(fw: Kernel):
  _push_tensix(fw, TTREPLAY(0, 5, 1, 1))
  _push_tensix(fw, TTSFPLOAD(0, 0, 7, 0))
  _push_tensix(fw, TTSFPADDI(0x3F80, 0, 0))
  _push_tensix(fw, TTSFPNOP())
  _push_tensix(fw, TTSFPSTORE(0, 0, 7, 0))
  _push_tensix(fw, TTINCRWC(0, 2, 0, 0))
  for _ in range(7):
    _push_tensix(fw, TTREPLAY(0, 5, 0, 0))
  _push_tensix(fw, TTSETRWC(0, 4, 8, 0, 0, 4))
  _push_tensix(fw, TTSETRWC(0, 4, 8, 0, 0, 4))


def _write_trisc1_dest_offset_instr(fw: Kernel, offset_id=t1, instr=t2, base=t3):
  fw.sltu(instr, zero, offset_id)
  fw.slli(instr, instr, 9)
  fw.li(base, 0xB2010000)
  fw.add(instr, instr, base)
  fw.write32(TensixRegs.INSTRN_BUF_BASE, instr, tmp_addr=t0)


def _wait_mmio_low_byte_zero(fw: Kernel, addr: int, *, ptr=t0, tmp=t1):
  done = fw._new_label("wait_mmio_zero_done")
  loop = fw._new_label("wait_mmio_zero")
  fw.li(ptr, addr)
  fw.label(loop)
  fw.lw(tmp, ptr, 0)
  fw.andi(tmp, tmp, 0xFF)
  fw.beq(tmp, zero, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)


def _init_trisc0_unpack(fw: Kernel):
  # The old add1 unpacker path configured CB0 as 4 faces of Float16_b.
  _push_tensix(fw, TTZEROSRC(0, 0, 1, 3))
  fw.write32(TM.DATA_COMMON["cfg_state_id"], 0, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETC16(0, 0))

  wait_unp = fw._new_label("init_wait_unpack_ctx")
  wait_unp_done = fw._new_label("init_wait_unpack_ctx_done")
  fw.li(t0, TENSIX_PC_UNPACK_SYNC)
  fw.label(wait_unp)
  fw.lw(t1, t0, 0)
  fw.andi(t1, t1, 0xFF)
  fw.beq(t1, zero, wait_unp_done)
  fw.fence()
  fw.j(wait_unp)
  fw.label(wait_unp_done)

  _push_tensix(fw, TTSETADCXY(3, 0, 0, 0, 0, 0xB))
  _push_tensix(fw, TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  fw.write32(TensixRegs.CFG_BASE + 57 * 4, 0x00000200, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 59 * 4, 0x00000200, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTATGETM(0))
  unpack_rmw_words = [
    0xB3FF0000, 0xB47F0000, 0xB3070001, 0xB4800001, 0xB5010001,
    0xB6600001, 0xB3010102,
  ]
  for raw in unpack_rmw_words:
    _write_tensix_instr_word(fw, raw)
  _push_tensix(fw, TTATRELM(0))
  fw.write32(TensixRegs.CFG_BASE + 64 * 4, 0x00000015, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 65 * 4, 0x00040001, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 112 * 4, 0x01000015, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 113 * 4, 0x00040001, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 72 * 4, 0x00000025, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 73 * 4, 0x000F000F, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 120 * 4, 0x00000025, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 121 * 4, 0x000F000F, tmp_addr=t0, tmp_val=t1)
  _write_tensix_instr_word(fw, TTSETADCXX(1, 255, 0))
  _write_tensix_instr_word(fw, TTSETADCXX(2, 255, 0))
  fw.write32(TensixRegs.CFG_BASE + 84 * 4, 0x00400040, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 86 * 4, 0x01000100, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 160, 0x01000100, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 164, 0x00800080, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 168, 0x00400040, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 172, 0x00200020, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 176, 0x00100010, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETC16(5, 4))
  fw.write32(TRISC0_UNP_CFG_CONTEXT, 0, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETC16(41, 0))
  page_size_16b = TILE_BYTES >> 4
  for raw in (
    0x45000048 + (page_size_16b << 8),
    0x4500004A + (page_size_16b << 8),
    0xB4010048,
  ):
    _write_tensix_instr_word(fw, raw)
  _push_tensix(fw, TTSETADCXX(1, 255, 0))
  _write_tensix_instr_word(fw, 0xB4010048)
  _push_tensix(fw, TTSETADCXX(1, 255, 0))
  _write_mop_cfg(fw, UNPACK_MOP_CFG, 0)
  _tensix_sync(fw, 0)


def _init_trisc1_math(fw: Kernel):
  # Old tt-metal TRISC1 reaches math init after CRT/kernel prologue and PC-buffer
  # synchronization. This lean kernel can arrive immediately after launch, and
  # fresh slow-dispatch reopens can wedge if math/MOP state is programmed too
  # early. Keep a short deterministic settling delay before the math prologue.
  fw.delay_cycles(50)
  _write_repeated_bytes(fw, TRISC1_UNPACK_TILE_NUM_FACES, 4, 8)
  fw.write32(TRISC1_UNPACK_DST_FORMAT, Dtype.Float16_b.value, tmp_addr=t0, tmp_val=t1)
  fw.write32(TRISC1_UNPACK_SRC_FORMAT, Dtype.Float16_b.value, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETC16(13, 0))
  _push_tensix(fw, TTSETC16(29, 0))
  _push_tensix(fw, TTSETC16(48, 0))
  _push_tensix(fw, TTZEROACC(3, 0, 0, 1, 0))
  _math_direct_mova2d_init(fw)
  _write_mop_cfg(fw, MATH_MOP_CFG, 1)
  _tensix_sync(fw, 1)
  _wait_mmio_low_byte_zero(fw, PCBUF_SEM_BASE + 4)
  _push_tensix(fw, TTSEMINIT(sem_sel=2, init_value=0, max_value=2))
  _write_tensix_instr_word(fw, TTSETC16(1, 0))
  _write_tensix_instr_word(fw, 0xB30808DC)
  fw.write32(TM.DATA1["dest_offset_id"], 0, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSTALLWAIT(128, 16))
  _write_tensix_instr_word(fw, 0xB6800001)
  _math_direct_mova2d_init(fw)
  _write_mop_cfg(fw, MATH_MOP_CFG, 1)
  _push_tensix(fw, TTSFPLOADI(0, 0, 10))
  _push_tensix(fw, TTSFPLOADI(0, 0, 8))
  _push_tensix(fw, TTSFPCONFIG(0, 15, 1))
  _push_tensix(fw, TTSETC16(19, 0))
  _push_tensix(fw, TTSETC16(35, 0))
  _push_tensix(fw, TTSETC16(54, 0))
  _push_tensix(fw, TTSETRWC(0, 0, 0, 0, 0, 15))


def _init_trisc2_pack(fw: Kernel):
  # Mirror add1_compute_trisc2.kernel.dis from blackhole-py-old (6a80..6d68).
  # blackhole-py-only state setup (TRISC2 mailbox regs not visible in OLD asm):
  _write_repeated_bytes(fw, TRISC2_PACK_TILE_FACE_R_DIM, 16, 8)
  _write_repeated_bytes(fw, TRISC2_PACK_TILE_NUM_FACES, 4, 8)
  fw.write32(TRISC2_PACK_PARTIAL_FACE + 16, 0, tmp_addr=t0, tmp_val=t1)
  _write_repeated_bytes(fw, TRISC2_PACK_SRC_FORMAT, Dtype.Float16_b.value, 16)
  _write_repeated_bytes(fw, TRISC2_PACK_DST_FORMAT, Dtype.Float16_b.value, 16)

  # First SETDMAREG block (OLD 6ba8..6be0).
  _push_tensix(fw, TTSETDMAREG(0, 0, 0, 56))
  _push_tensix(fw, TTSETDMAREG(0, 32, 0, 57))
  _push_tensix(fw, TTSETDMAREG(0, 512, 0, 58))
  _push_tensix(fw, TTSETDMAREG(0, 2048, 0, 59))
  _push_tensix(fw, TTSTALLWAIT(128, 1))
  _push_tensix(fw, TTWRCFG(28, 0, 12))
  _push_tensix(fw, TTWRCFG(29, 0, 13))
  _push_tensix(fw, TTNOP())
  _push_tensix(fw, TTNOP())

  # Atomic config RMW (OLD 6be4..6c18).
  _push_tensix(fw, TTATGETM(0))
  for raw in (0xB61E0A01, 0xB3FC0002, 0xB4FF0002, 0xB53F0002):
    _write_tensix_instr_word(fw, raw)
  _push_tensix(fw, TTATRELM(0))

  # CFG/REGFILE pack config (OLD 6c1c..6c74).
  # `lui a1,0x40` -> a1 = 0x40 << 12 = 0x00040000 (not 0x00400000).
  fw.write32(TensixRegs.CFG_BASE + 68 * 4, 0x00040000, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 70 * 4, 0x00000551, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 18 * 4, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 208, 0x00040000, tmp_addr=t0, tmp_val=t1)
  # OLD writes `sw a1, 112..124(a5)` -> CFG words 28..31 (not 112..115).
  for cfg_word in (28, 29, 30, 31):
    fw.write32(TensixRegs.CFG_BASE + cfg_word * 4, 0x00001000, tmp_addr=t0, tmp_val=t1)
  # OLD: `sw t1, 96(a5)` -> CFG word 24.
  fw.write32(TensixRegs.CFG_BASE + 24 * 4, 0x0000FFFF, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 20 * 4, 0, tmp_addr=t0, tmp_val=t1)
  # Packer tile/page size comes from TRISC local CB state, already shifted to 16B units.
  _cb_iface(fw, TM.DATA_COMMON["cb_interface"], OUT_CB, out=t6)
  fw.lw(t1, t6, 8)
  fw.write32(TensixRegs.REGFILE_BASE + 64, t1, tmp_addr=t0)
  fw.write32(TensixRegs.REGFILE_BASE + 68, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 72, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 76, 0, tmp_addr=t0, tmp_val=t1)

  # First TTSETADCXX (OLD 6c84..6c8c, raw 0x5E803C00 = TTSETADCXX(4, 15, 0)).
  _push_tensix(fw, TTSETADCXX(4, 15, 0))

  # SETC16 37/38/39 (OLD 6c90..6c98). MUST come AFTER first TTSETADCXX.
  _push_tensix(fw, TTSETC16(37, 260))
  _push_tensix(fw, TTSETC16(38, 10272))
  _push_tensix(fw, TTSETC16(39, 4384))

  # MOP sync + MOP_CFG load (OLD 6c9c..6cf0).
  _mop_sync(fw, 2, tmp=t1)
  _write_mop_cfg(fw, PACK_MOP_CFG, 2)

  # Second SETDMAREG block (OLD 6cf4..6d14). Must be re-issued after MOP_CFG store.
  _push_tensix(fw, TTSETDMAREG(0, 0, 0, 56))
  _push_tensix(fw, TTSETDMAREG(0, 32, 0, 57))
  _push_tensix(fw, TTSETDMAREG(0, 512, 0, 58))
  _push_tensix(fw, TTSETDMAREG(0, 2048, 0, 59))
  _push_tensix(fw, TTSTALLWAIT(128, 1))
  _push_tensix(fw, TTWRCFG(28, 0, 12))
  _push_tensix(fw, TTWRCFG(29, 0, 13))
  _push_tensix(fw, TTNOP())
  _push_tensix(fw, TTNOP())

  # Second TTSETADCXX (OLD 6d18).
  _push_tensix(fw, TTSETADCXX(4, 15, 0))

  # dest_offset_id := 0 (OLD 6d1c..6d34).
  fw.write32(TM.DATA_COMMON["dest_offset_id"], 0, tmp_addr=t0, tmp_val=t1)

  # Output addr config setup (OLD 6d38..6d60).
  _push_tensix(fw, TTSTALLWAIT(33, 8))
  _push_tensix(fw, TTSETDMAREG(0, 0, 0, 16))
  _push_tensix(fw, TTSETDMAREG(0, 0, 0, 17))
  _push_tensix(fw, TTSETDMAREG(0, 512, 0, 18))
  _push_tensix(fw, TTSETDMAREG(0, 0, 0, 19))
  _push_tensix(fw, TTSTALLWAIT(128, 1))
  _push_tensix(fw, TTWRCFG(4, 1, 180))
  _push_tensix(fw, TTDMANOP())
  _push_tensix(fw, TTDMANOP())

  # ADCXY/ZW (OLD 6d64..6d68) - issued AFTER WRCFG(8,1,180) + DMANOPs.
  _push_tensix(fw, TTSETADCXY(4, 0, 0, 0, 0, 0xB))
  _push_tensix(fw, TTSETADCZW(4, 0, 0, 0, 0, 0xF))


def add1_brisc_reader() -> Kernel:
  fw = Kernel()
  _read_rta_from(fw, BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4, t6))
  for addr in (
    SYNC_OUT_RESERVED, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
    SYNC_CLOCK_START_LO, SYNC_CLOCK_START_HI, SYNC_CLOCK_END_LO, SYNC_CLOCK_END_HI,
  ):
    fw.write32(addr, 0, tmp_addr=t0, tmp_val=t1)
  fw.debug_write_wall_clock(SYNC_CLOCK_START_LO, SYNC_CLOCK_START_HI, name="add1_start")
  fw.write32(SYNC_OUT_RESERVED, t6, tmp_addr=t0, tmp_val=t1)
  fw.li(s5, 0)
  fw.label("brisc_loop")
  fw.beq(s5, s3, "brisc_done")
  _cb_reserve_back(fw, BM.CB_INTERFACE, 0)
  fw.add(a1, s2, s5)
  fw.mv(a0, s0)
  fw.mv(a2, s4)
  _dram_tile_addr_from(fw, BM.DRAM_BANK_TO_NOC_XY, 0)
  _local_noc0_coord(fw, a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  _cb_write_ptr(fw, BM.CB_INTERFACE, 0, out=t5)
  fw.li(t6, TILE_BYTES)
  fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.label("brisc_read_wait")
  fw.lw(t1, t0, 0)
  fw.bltu(t1, t4, "brisc_read_wait")
  fw.fence()
  _cb_push_back(fw, BM.CB_INTERFACE, 0)
  fw.addi(t2, s5, 1)
  _signal_sync(fw, SYNC_READ, t2)
  fw.addi(s5, s5, 1)
  fw.j("brisc_loop")
  fw.label("brisc_done")
  fw.ret()
  return fw


def add1_ncrisc_writer(num_banks: int) -> Kernel:
  fw = Kernel()
  _read_rta_from(fw, NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  fw.li(s5, 0)
  fw.label("ncrisc_loop")
  fw.beq(s5, s3, "ncrisc_done")
  _cb_wait_front(fw, NM.CB_INTERFACE, OUT_CB)
  fw.add(a1, s2, s5)
  fw.mv(a0, s0)
  fw.mv(a2, s4)
  _dram_tile_addr_from(fw, NM.DRAM_BANK_TO_NOC_XY, num_banks)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.addi(t4, t4, 1)
  _cb_read_ptr(fw, NM.CB_INTERFACE, OUT_CB, out=t5)
  fw.li(t6, TILE_BYTES)
  fw.noc_write(1, 0, t5, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(1, t4, addr=t0, val=t1)
  _cb_pop_front(fw, NM.CB_INTERFACE, OUT_CB)
  fw.addi(s5, s5, 1)
  fw.j("ncrisc_loop")
  fw.label("ncrisc_done")
  fw.debug_write_wall_clock(SYNC_CLOCK_END_LO, SYNC_CLOCK_END_HI, name="add1_end")
  fw.ret()
  return fw


def add1_trisc_compute(trisc_id: int) -> Kernel:
  data = TM.DATA1 if trisc_id == 1 else TM.DATA_COMMON
  fw = Kernel()
  fw.addi(sp, sp, -16)
  fw.sw(ra, sp, 12)
  fw.read32(t0, data["rta_l1_base"])
  fw.lw(s3, t0, 0)
  fw.lw(t6, t0, 4)
  fw.mv(t1, t6)
  _wait_sync_value(fw, SYNC_OUT_RESERVED, t1, actual=t2)

  if trisc_id == 0:
    # Device open/firmware upload resets the RISC runtime, but old add1 did not
    # rely on that to sanitize Tensix datapath state. Re-run the unpack prologue
    # before each tile loop so previous kernels or reopen state cannot leak in.
    fw.write32(TM.DATA_COMMON["cfg_state_id"], 0, tmp_addr=t0, tmp_val=t1)
    _push_tensix(fw, TTSETC16(0, 0))
    fw.write32(TRISC0_UNP_CFG_CONTEXT, 0, tmp_addr=t0, tmp_val=t1)
    _push_tensix(fw, TTSETC16(41, 0))
    _init_trisc0_unpack(fw)
  elif trisc_id == 1:
    _init_trisc1_math(fw)
  else:
    _init_trisc2_pack(fw)

  fw.write32(SYNC_TRISC_INIT + trisc_id * 4, 1, tmp_addr=t0, tmp_val=t1)
  fw.fence()

  fw.li(t1, 1)
  for init_id in range(3):
    _wait_sync_value(fw, SYNC_TRISC_INIT + init_id * 4, t1, actual=t2)
  if trisc_id == 1:
    fw.li(s5, 0)
    fw.label("trisc1_loop")
    fw.beq(s5, s3, "trisc1_done")
    _push_tensix(fw, TTSEMWAIT(322, 2, 2))
    fw.read32(t1, TM.DATA1["dest_offset_id"], tmp_addr=t0)
    _write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    _push_tensix(fw, TTMOP(1, 0, 0))
    _push_tensix(fw, TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, TM.DATA1["dest_offset_id"], tmp_addr=t0)
    _write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    _push_tensix(fw, TTSTALLWAIT(0x100, 0x10))
    for _ in range(4):
      _math_add1_replay_row(fw)
    _write_tensix_instr_word(fw, TTSETRWC(0, 0, 0, 0, 0, 4))
    _write_tensix_instr_word(fw, TTSTALLWAIT(2, 2064))
    _push_tensix(fw, TTSEMPOST(2))
    fw.addi(t2, s5, 1)
    _signal_sync(fw, SYNC_DONE1, t2)
    fw.read32(t1, TM.DATA1["dest_offset_id"], tmp_addr=t0)
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(TM.DATA1["dest_offset_id"], t2, tmp_addr=t0, tmp_val=t3)
    _push_tensix(fw, TTSTALLWAIT(128, 2064))
    _write_trisc1_dest_offset_instr(fw, t2, t1, t3)
    fw.addi(s5, s5, 1)
    fw.j("trisc1_loop")
    fw.label("trisc1_done")
    _ret_kernel(fw)
    return fw

  if trisc_id == 2:
    fw.li(s5, 0)
    fw.label("trisc2_loop")
    fw.beq(s5, s3, "trisc2_done")
    _push_tensix(fw, TTSEMWAIT(1, 2, 1))
    _cb_reserve_back(fw, data["cb_interface"], OUT_CB)
    _cb_write_ptr(fw, data["cb_interface"], OUT_CB, out=s0)
    fw.slli(t4, s0, 4)
    fw.addi(s0, s0, -1)
    _push_tensix(fw, TTSETADC(4, 0, 3, 0))
    fw.slli(t1, s0, 8)
    fw.li(t2, 0x00FFFF00)
    fw.and_(t1, t1, t2)
    fw.li(t2, 0x45000018)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    fw.srli(t1, s0, 16)
    fw.slli(t1, t1, 8)
    fw.li(t2, 0x00800000)
    fw.or_(t1, t1, t2)
    fw.li(t2, 0x45000019)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    _push_tensix(fw, TTSTALLWAIT(128, 9))
    _push_tensix(fw, TTWRCFG(12, 0, 69))
    fw.srli(t1, s0, 16)
    fw.slli(t1, t1, 8)
    fw.li(t2, 0x45000019)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    _push_tensix(fw, TTDMANOP())
    _push_tensix(fw, TTMOP(1, 0, 0))
    _tensix_sync(fw, 2, tmp=t1)
    _push_tensix(fw, TTSETADCZW(4, 0, 0, 0, 0, 5))
    _cb_push_back(fw, data["cb_interface"], OUT_CB)
    # OLD 6e7c..6e8c: push SYNC_TILES_RECEIVED via Tensix.
    # DMAREG[48] := received_count from local output CB state, then
    # TTSTOREREG(TdmaDataRegIndex=24, RegAddr=0x1600A) writes the 32-bit GPR
    # pair {DMAREG[48],DMAREG[49]} to SYNC_TILES_RECEIVED[OUT_CB].
    _cb_iface(fw, data["cb_interface"], OUT_CB, out=t6)
    fw.lw(t1, t6, 24)
    _cb_counter_high(fw, t1, t1)
    fw.slli(t1, t1, 8)
    fw.li(t2, TTSETDMAREG(0, 0, 0, 48).raw_word())
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    _push_tensix(fw, TTSTALLWAIT(32, 8))
    _write_tensix_instr_word(
      fw,
      TTSTOREREG(24, ((CB.SYNC_TILES_RECEIVED_BASE + OUT_CB * CB.SYNC_STRIDE) >> 2) & 0x3FFFF),
    )
    _push_tensix(fw, TTSTALLWAIT(64, 8))
    fw.read32(t1, TM.DATA_COMMON["dest_offset_id"], tmp_addr=t0)
    fw.andi(t2, t1, 1)
    fw.li(t3, 0x10104000)
    fw.add(t2, t2, t3)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t2, tmp_addr=t0)
    _push_tensix(fw, TTSEMGET(2))
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(TM.DATA_COMMON["dest_offset_id"], t2, tmp_addr=t0, tmp_val=t3)
    fw.sltu(t1, zero, t1)
    fw.slli(t1, t1, 2)
    fw.addi(t1, t1, 4)
    fw.slli(t1, t1, 16)
    fw.li(t2, 0xB00080B4)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    _push_tensix(fw, TTDMANOP())
    _push_tensix(fw, TTDMANOP())
    fw.addi(t2, s5, 1)
    _signal_sync(fw, SYNC_DONE2, t2)
    fw.addi(s5, s5, 1)
    fw.j("trisc2_loop")
    fw.label("trisc2_done")
    _ret_kernel(fw)
    return fw

  fw.li(s5, 0)
  fw.label("trisc_loop")
  fw.beq(s5, s3, "trisc_done")
  fw.addi(t2, s5, 1)
  _cb_wait_front(fw, data["cb_interface"], 0)
  _cb_read_ptr(fw, data["cb_interface"], 0, out=s0)
  _cb_iface(fw, data["cb_interface"], 0, out=t6)
  fw.lw(t1, t6, 8)
  _push_tensix(fw, TTSETADCZW(3, 0, 0, 0, 0, 15))

  wait_unp = fw._new_label("wait_unpack_ctx")
  wait_unp_done = fw._new_label("wait_unpack_ctx_done")
  fw.li(t0, TENSIX_PC_UNPACK_SYNC)
  fw.label(wait_unp)
  fw.lw(t1, t0, 0)
  fw.andi(t1, t1, 0xFE)
  fw.beq(t1, zero, wait_unp_done)
  fw.fence()
  fw.j(wait_unp)
  fw.label(wait_unp_done)

  fw.read32(t1, TRISC0_UNP_CFG_CONTEXT, tmp_addr=t0)
  fw.li(t2, TensixRegs.CFG_BASE + 76 * 4)
  cfg_addr_done = fw._new_label("trisc0_cfg_addr_done")
  fw.beq(t1, zero, cfg_addr_done)
  fw.addi(t2, t2, 4)
  fw.label(cfg_addr_done)
  fw.addi(t3, s0, -1)
  fw.sw(t3, t2, 0)
  fw.lw(t1, t2, 0)
  fw.write32(TENSIX_PC_UNPACK_SYNC, 0, tmp_addr=t0, tmp_val=t1)

  _push_tensix(fw, TTSTALLWAIT(8, 1024))
  _push_tensix(fw, TTMOP(1, 0, 0))
  _push_tensix(fw, TTSEMGET(32))
  fw.read32(t1, TRISC0_UNP_CFG_CONTEXT, tmp_addr=t0)
  fw.li(t2, 1)
  fw.sub(t2, t2, t1)
  fw.write32(TRISC0_UNP_CFG_CONTEXT, t2, tmp_addr=t0, tmp_val=t3)
  fw.beq(t1, zero, "trisc0_set_ctx1")
  _push_tensix(fw, TTSETC16(41, 0))
  fw.j("trisc0_ctx_set")
  fw.label("trisc0_set_ctx1")
  _push_tensix(fw, TTSETC16(41, 257))
  fw.label("trisc0_ctx_set")
  _cb_pop_front(fw, data["cb_interface"], 0, tensix_ack=True)
  fw.addi(t2, s5, 1)
  _signal_sync(fw, SYNC_DONE0, t2)

  fw.addi(s5, s5, 1)
  fw.j("trisc_loop")
  fw.label("trisc_done")
  _ret_kernel(fw)
  return fw


def build_program(src_addr: int, dst_addr: int, num_banks: int, cores: list[tuple[int, int]] | None = None) -> Program:
  global _RUN_EPOCH
  _RUN_EPOCH = (_RUN_EPOCH + 1) & 0xFFFFFFFF
  run_epoch = _RUN_EPOCH
  tiles_per_core = TILES_PER_CORE
  if cores is None:
    cores = [TARGET_CORE]
  core_index = {core: i for i, core in enumerate(cores)}
  rows = tuple(sorted({y for _, y in cores}))
  cols = tuple(sorted({x for x, _ in cores}))

  def tile_offset(x: int, y: int) -> int:
    return core_index[(x, y)] * tiles_per_core

  def brisc_rtas(x: int, y: int) -> list[int]:
    return [src_addr, tile_offset(x, y), tiles_per_core, num_banks, run_epoch]

  def ncrisc_rtas(x: int, y: int) -> list[int]:
    return [dst_addr, tile_offset(x, y), tiles_per_core, num_banks]

  def trisc_rtas(_x: int, _y: int) -> list[int]:
    return [tiles_per_core, run_epoch]

  brisc = add1_brisc_reader()
  ncrisc = add1_ncrisc_writer(num_banks)
  trisc0 = add1_trisc_compute(0)
  trisc1 = add1_trisc_compute(1)
  trisc2 = add1_trisc_compute(2)
  brisc.rta(brisc_rtas)
  ncrisc.rta(ncrisc_rtas)
  trisc0.rta(trisc_rtas)
  trisc1.rta(trisc_rtas)
  trisc2.rta(trisc_rtas)
  prog = Program(
    brisc=brisc,
    ncrisc=ncrisc,
    trisc0=trisc0,
    trisc1=trisc1,
    trisc2=trisc2,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
    grid=(rows, cols),
  )
  prog.name = "add1"
  return prog


def main():
  device = Device()
  try:
    n_tiles = TILES_PER_CORE
    src_rm = _seed_src_tensor(n_tiles)
    src_buf = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="src")
    dst_buf = device.dram.alloc(n_tiles, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="dst")
    prog = build_program(src_buf.addr, dst_buf.addr, len(device.dram.bank_tiles))
    timings = device.run(prog)
    out = device.dram_read(dst_buf)
    exp = _expected_add1(src_rm)
    mismatch = _first_mismatch(out, exp)
    if mismatch is not None:
      got = out[mismatch:mismatch + 32].hex()
      want = exp[mismatch:mismatch + 32].hex()
      raise AssertionError(f"mismatch byte={mismatch} got={got} exp={want}")
    print(f"PASS add1 {n_tiles} tile on core {TARGET_CORE}")
    for i, timing in enumerate(timings):
      print(f"  [{i}] {timing['name']} {timing['us']:,.1f} us")
  finally:
    device.close()


if __name__ == "__main__":
  main()
