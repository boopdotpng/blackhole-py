#!/usr/bin/env python3
from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("TT_USB", "1")

from asm import Kernel
from device import Device
from pcie import TLBWindow
from dsl import (
  TTATGETM, TTATRELM, TTCLEARDVALID, TTDMANOP, TTINCRWC, TTINSN, TTMOP, TTNOP, TTREPLAY, TTSEMGET,
  TTSEMINIT, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSFPADD, TTSFPCONFIG, TTSFPENCC, TTSFPLOAD,
  TTSFPLOADI, TTSFPNOP, TTSFPSTORE, TTSETADC, TTSETADCXX,
  TTSETADCXY, TTSETADCZW, TTSETC16, TTSETDMAREG, TTSTALLWAIT, TTSTOREREG,
  TTWRCFG, TTZEROACC, TTZEROSRC, a0, a1, a2, a5, ra, s0, s1, s2, s3, s4, s5,
  sp, t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk.addrs import BriscMailbox as BM, CircularBuffer as CB, Mailbox, NcriscMailbox as NM, NOC, TensixL1, TriscMailbox as TM
from ttk.tensix import TensixRegs

TILE_BYTES = Dtype.Float16_b.tile_size
CB_DEPTH = 2
SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
INPUT_L1 = SCRATCH_L1
OUTPUT_L1 = INPUT_L1 + TILE_BYTES * CB_DEPTH
SYNC_L1 = SCRATCH_L1 + 0x10000
SYNC_OUT_RESERVED = SYNC_L1
SYNC_READ = SYNC_L1 + 4
SYNC_DONE0 = SYNC_L1 + 8
SYNC_DONE1 = SYNC_L1 + 12
SYNC_DONE2 = SYNC_L1 + 16
SYNC_TRISC_INIT = SYNC_L1 + 20
TRISC0_UNP_CFG_CONTEXT = 0xFFB00820
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
RISCV_DEBUG_REG_DBG_FEATURE_DISABLE = 0xFFB12068
DBG_BASE = 0x19000
DBG_TRISC0 = DBG_BASE + 0x00
DBG_TRISC1 = DBG_BASE + 0x04
DBG_TRISC2 = DBG_BASE + 0x08
DBG_BRISC = DBG_BASE + 0x0C
DBG_SEMS0 = DBG_BASE + 0x10
DBG_SEMS1 = DBG_BASE + 0x14
DBG_SEMS2 = DBG_BASE + 0x18
DBG_QSTATUS0 = DBG_BASE + 0x20
DBG_BSTATUS0 = DBG_BASE + 0x24
DBG_UNPACK_SYNC0 = DBG_BASE + 0x28
DBG_QSTATUS1 = DBG_BASE + 0x30
DBG_BSTATUS1 = DBG_BASE + 0x34
DBG_UNPACK_SYNC1 = DBG_BASE + 0x38
PCBUF_SEM_BASE = 0xFFE80020
UNPACK_MOP_CFG = [
  4, 1, 0x420080C1, 0x02000000, 0x02000000,
  0x43800101, 0x02000000, 0x43800101, 0x43800101,
]
MATH_DATACOPY_MOP_CFG = [
  4, 2, 0x02000000, 0x37C00003, 0x02000000,
  0x1200A000, 0x02000000, 0x1200A000, 0x1200A000,
]
PACK_MOP_CFG = [
  4, 4, 0x02000000, 0x02000000, 0x02000000,
  0x41000000, 0x02000000, 0x41008001, 0x41010000,
]
SFPU_ADD1_REPLAY = TTREPLAY(0, 5, 0, 0).raw_word()
SFPU_ADD1_RECORD = TTREPLAY(0, 5, 0, 1)
SFPU_ADD1_MOP_CFG = [
  1, 32, 0x02000000, 0x02000000, 0x02000000,
  SFPU_ADD1_REPLAY, 0x02000000, SFPU_ADD1_REPLAY, SFPU_ADD1_REPLAY,
]


def _sfpu_add1_mop_cfg() -> list[int]:
  cfg = list(SFPU_ADD1_MOP_CFG)
  if "TT_DEBUG_SFPU_MOP_ITERS" in os.environ:
    cfg[1] = int(os.environ["TT_DEBUG_SFPU_MOP_ITERS"], 0)
  return cfg


def _bf16(x: float) -> int:
  return struct.unpack("<I", struct.pack("<f", x))[0] >> 16


def _f32(x: int) -> float:
  return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]


def _format_bf16_ints(data: bytes, count: int) -> str:
  return " ".join(
    str(int(_f32(int.from_bytes(data[i : i + 2], "little"))))
    for i in range(0, min(len(data), count * 2), 2)
  )


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


def _debug_postmortem_existing_device(device: Device):
  if not os.environ.get("TT_DEBUG_POSTMORTEM_CORE"):
    return
  x, y = os.environ["TT_DEBUG_POSTMORTEM_CORE"].split(",", 1)
  core = (int(x, 0), int(y, 0))
  addrs = sorted(addr for addr in Kernel._debug_addrs if 0 <= addr < TensixL1.SIZE)
  if not addrs:
    return
  with TLBWindow(device.dev, core) as win:
    print(f"debug postmortem core {core}", file=sys.stderr)
    for addr in addrs:
      data = bytes(win.mm[addr + i] for i in range(4))
      word = struct.unpack("<I", data)[0]
      print(f"0x{addr:x}: 0x{word:08x}", file=sys.stderr)


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
  fw.sh(received, tmp, 0)
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
  fw.sh(acked, tmp, 0)
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


def _fill_l1_tile_words(fw: Kernel, base_reg, word_value: int, *, count_reg=t4, val_reg=t6):
  fw.li(count_reg, TILE_BYTES // 4)
  fw.li(val_reg, word_value)
  loop = fw._new_label("fill_l1_tile")
  done = fw._new_label("fill_l1_tile_done")
  fw.label(loop)
  fw.beq(count_reg, zero, done)
  fw.sw(val_reg, base_reg, 0)
  fw.addi(base_reg, base_reg, 4)
  fw.addi(count_reg, count_reg, -1)
  fw.j(loop)
  fw.label(done)


def _tt_raw(inst) -> int:
  return inst.raw_word() if hasattr(inst, "raw_word") else int(inst) & 0xFFFFFFFF


def _push_tensix(fw: Kernel, inst, *, tmp_addr=t0, tmp_val=t1):
  fw.emit(inst)


def _write_tensix_instr_word(fw: Kernel, word: int | object, *, tmp_addr=t0, tmp_val=t1):
  fw.write32(TensixRegs.INSTRN_BUF_BASE, _tt_raw(word), tmp_addr=tmp_addr, tmp_val=tmp_val)


def _snapshot_pcbuf_sems(fw: Kernel, addr: int, *, base=t0, word=t1, tmp=t2):
  fw.note_debug_addr(addr)
  fw.li(base, PCBUF_SEM_BASE)
  fw.lw(word, base, 4)       # MATH_PACK, semaphore 1.
  fw.lw(tmp, base, 8)        # UNPACK_TO_DEST, semaphore 2.
  fw.slli(tmp, tmp, 8)
  fw.or_(word, word, tmp)
  fw.lw(tmp, base, 20)       # UNPACK_SYNC, semaphore 5.
  fw.slli(tmp, tmp, 16)
  fw.or_(word, word, tmp)
  fw.lw(tmp, base, 28)       # MATH_DONE, semaphore 7.
  fw.slli(tmp, tmp, 24)
  fw.or_(word, word, tmp)
  fw.write32(addr, word, tmp_addr=base, tmp_val=tmp)


def _snapshot_tensix_status(fw: Kernel, q_addr: int, b_addr: int, sync_addr: int):
  # dsl encodes CSR immediates as signed 12-bit values; these are 0xBC0/0xBC1.
  fw.csrrs(t1, zero, -0x440)
  fw.write32(q_addr, t1, tmp_addr=t0, tmp_val=t2)
  fw.csrrs(t1, zero, -0x43F)
  fw.write32(b_addr, t1, tmp_addr=t0, tmp_val=t2)
  fw.read32(t1, TENSIX_PC_UNPACK_SYNC, tmp_addr=t0)
  fw.write32(sync_addr, t1, tmp_addr=t0, tmp_val=t2)


def _pc_buf_addr(trisc_id: int, offset: int) -> int:
  return 0xFFE80000 + trisc_id * 0x10000 + offset


def _mop_sync(fw: Kernel, trisc_id: int = 0, *, tmp=t0):
  fw.write32(TENSIX_PC_BUF_MOP_SYNC, 0, tmp_addr=t0, tmp_val=t1)
  fw.read32(tmp, TENSIX_PC_BUF_MOP_SYNC, tmp_addr=t1)
  fw.and_(zero, zero, tmp)


def _tensix_sync(fw: Kernel, trisc_id: int = 0, *, tmp=t0):
  fw.write32(TENSIX_PC_BUF_SYNC, 0, tmp_addr=t0, tmp_val=t1)
  fw.read32(tmp, TENSIX_PC_BUF_SYNC, tmp_addr=t1)
  fw.and_(zero, zero, tmp)


def _write_mop_cfg(fw: Kernel, words: list[int], trisc_id: int = 0, *, ptr=t0, tmp=t1):
  _mop_sync(fw, trisc_id, tmp=tmp)
  fw.li(ptr, TENSIX_MOP_CFG)
  for i, word in enumerate(words):
    fw.li(tmp, word)
    fw.sw(tmp, ptr, i * 4)


def _write_repeated_bytes(fw: Kernel, addr: int, value: int, count_words: int, *, ptr=t0, tmp=t1):
  byte = value & 0xFF
  fw.li(ptr, addr)
  fw.li(tmp, byte | (byte << 8) | (byte << 16) | (byte << 24))
  for i in range(count_words):
    fw.sw(tmp, ptr, i * 4)


def _math_datacopy_init(fw: Kernel):
  _push_tensix(fw, TTSETC16(15, 0))
  _push_tensix(fw, TTSETC16(31, 0))
  _push_tensix(fw, TTSETC16(50, 0))
  _push_tensix(fw, TTSETC16(12, 1))
  _push_tensix(fw, TTSETC16(28, 1))
  _push_tensix(fw, TTSETC16(47, 0))
  _push_tensix(fw, TTSETC16(14, 8))
  _push_tensix(fw, TTSETC16(30, 8))
  _push_tensix(fw, TTSETC16(49, 0))
  _write_mop_cfg(fw, MATH_DATACOPY_MOP_CFG, 1)
  _push_tensix(fw, TTSETC16(7, 0))
  if os.environ.get("TT_DEBUG_CLEAR_DVALID_INIT"):
    _push_tensix(fw, TTCLEARDVALID(1, 0))
  _push_tensix(fw, TTSETRWC(0, 0, 0, 0, 0, 15))


def _record_sfpu_add1_replay(fw: Kernel):
  fw.emit(
    0x10000144,  # ttreplay 0,5,0,1
    0xC0038001,  # sfpload  L0, 0, 0, 7
    0x14280402,  # sfpadd   L0, L10, L0, L1, 0
    0x3C000002,  # sfpnop
    0xC8038001,  # sfpstore L0, 0, 0, 7
    0xE0020000,  # ttincrwc 0, 2, 0, 0
  )
  _tensix_sync(fw, 1)


def _sfpu_add1_face_loop(fw: Kernel):
  # These are the RVTT custom instruction encodings from the old add1 TRISC1
  # kernel, not INSTRN_BUF Tensix words. Emitting them directly avoids flooding
  # the coprocessor instruction FIFO from RISC-V.
  def one_face(iters: int):
    loop = fw._new_label("sfpu_add1")
    done = fw._new_label("sfpu_add1_done")
    fw.li(a5, iters)
    fw.label(loop)
    fw.beq(a5, zero, done)
    fw.emit(
      0xC0038001,  # sfpload  L0, 0, 0, 7
      0x14280402,  # sfpadd   L0, L10, L0, L1, 0
      0x3C000002,  # sfpnop
      0xC8038001,  # sfpstore L0, 0, 0, 7
      0xE0020000,  # ttincrwc 0, 2, 0, 0
    )
    fw.addi(a5, a5, -1)
    fw.j(loop)
    fw.label(done)

  if "TT_DEBUG_SFPU_ITERS" in os.environ:
    one_face(int(os.environ["TT_DEBUG_SFPU_ITERS"], 0))
    return

  for _ in range(4):
    one_face(4)
    fw.delay_cycles(64, count=t2)
    one_face(4)
    fw.delay_cycles(64, count=t2)
    fw.emit(
      0xDC480010,  # ttsetrwc 0,4,8,0,0,4
      0xDC480010,  # ttsetrwc 0,4,8,0,0,4
    )


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
  if os.environ.get("TT_DEBUG_CLEAR_DVALID_UNPACK_INIT"):
    _push_tensix(fw, TTCLEARDVALID(3, 0))
  fw.write32(TM.DATA_COMMON["cfg_state_id"], 0, tmp_addr=t0, tmp_val=t1)

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
    0xB3010102, 0xB5400047, 0xB5400077,
  ]
  if os.environ.get("TT_DEBUG_UNPACK_EXACT_RMWCIB3"):
    unpack_rmw_words.insert(5, 0xB6600001)
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
  _push_tensix(fw, TTSETADCXX(1, 255, 0))
  _push_tensix(fw, TTSETADCXX(2, 255, 0))
  fw.write32(TensixRegs.CFG_BASE + 84 * 4, 0x00400040, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 86 * 4, 0x01000100, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 160, 0x01000100, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 164, 0x00800080, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 168, 0x00400040, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 172, 0x00200020, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 176, 0x00100010, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETC16(5, 4))
  fw.write32(TensixRegs.CFG_BASE + 200 * 4, 0x00000100, tmp_addr=t0, tmp_val=t1)
  fw.write32(TRISC0_UNP_CFG_CONTEXT, 0, tmp_addr=t0, tmp_val=t1)
  if os.environ.get("TT_DEBUG_INIT_UNPACK_SYNC_SEM"):
    _push_tensix(fw, TTSEMINIT(sem_sel=1 << 5, init_value=0, max_value=2))
  _push_tensix(fw, TTSETC16(41, 0))
  page_size_16b = TILE_BYTES >> 4
  for raw in (
    0x45000048 + (page_size_16b << 8),
    0x4500004A + (page_size_16b << 8),
    0xB4010048,
  ):
    _write_tensix_instr_word(fw, raw)
  _push_tensix(fw, TTSETADCXX(1, 255, 0))
  _write_mop_cfg(fw, UNPACK_MOP_CFG, 0)
  _write_tensix_instr_word(fw, 0xB4010048)
  _push_tensix(fw, TTSETADCXX(1, 255, 0))
  _tensix_sync(fw, 0)
  _write_mop_cfg(fw, UNPACK_MOP_CFG, 0)


def _init_trisc1_math(fw: Kernel):
  _write_repeated_bytes(fw, TRISC1_UNPACK_TILE_NUM_FACES, 4, 8)
  fw.write32(TRISC1_UNPACK_DST_FORMAT, Dtype.Float16_b.value, tmp_addr=t0, tmp_val=t1)
  fw.write32(TRISC1_UNPACK_SRC_FORMAT, Dtype.Float16_b.value, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSFPENCC(3, 0, 0, 10))
  _push_tensix(fw, TTNOP())
  _push_tensix(fw, TTSFPLOADI(0, 0, 0xBF80))
  _push_tensix(fw, TTSFPCONFIG(0, 11, 0))
  _push_tensix(fw, TTSETC16(13, 0))
  _push_tensix(fw, TTSETC16(29, 0))
  _push_tensix(fw, TTSETC16(48, 0))
  _push_tensix(fw, TTZEROACC(3, 0, 0, 1, 0))
  _math_datacopy_init(fw)
  _tensix_sync(fw, 1)
  _wait_mmio_low_byte_zero(fw, PCBUF_SEM_BASE + 4)
  _push_tensix(fw, TTSEMINIT(sem_sel=2, init_value=0, max_value=2))
  fw.write32(TM.DATA1["dest_offset_id"], 0, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETC16(1, 0))
  _write_tensix_instr_word(fw, 0xB30808DC)
  _push_tensix(fw, TTSTALLWAIT(128, 16))
  _write_tensix_instr_word(fw, 0xB6800001)
  _push_tensix(fw, TTSFPCONFIG(0, 15, 1))
  _push_tensix(fw, TTSFPLOADI(1, 10, 0))
  _push_tensix(fw, TTSFPLOADI(1, 8, 0x3F80))
  if os.environ.get("TT_DEBUG_SFPU_REPLAY_MOP") or os.environ.get("TT_DEBUG_SFPU_DIRECT_REPLAY"):
    _record_sfpu_add1_replay(fw)
    _write_mop_cfg(fw, _sfpu_add1_mop_cfg(), 1)
  _push_tensix(fw, TTSETC16(19, 0))
  _push_tensix(fw, TTSETC16(35, 0))
  _push_tensix(fw, TTSETC16(54, 0))
  _push_tensix(fw, TTSETRWC(0, 0, 0, 0, 0, 15))


def _init_trisc2_pack(fw: Kernel):
  _write_repeated_bytes(fw, TRISC2_PACK_TILE_FACE_R_DIM, 16, 8)
  _write_repeated_bytes(fw, TRISC2_PACK_TILE_NUM_FACES, 4, 8)
  fw.write32(TRISC2_PACK_PARTIAL_FACE + 16, 0, tmp_addr=t0, tmp_val=t1)
  _write_repeated_bytes(fw, TRISC2_PACK_SRC_FORMAT, Dtype.Float16_b.value, 16)
  _write_repeated_bytes(fw, TRISC2_PACK_DST_FORMAT, Dtype.Float16_b.value, 16)
  _push_tensix(fw, TTSETC16(37, 260))
  _push_tensix(fw, TTSETC16(38, 10272))
  _push_tensix(fw, TTSETC16(39, 4384))
  _mop_sync(fw, 2, tmp=t1)
  _write_mop_cfg(fw, PACK_MOP_CFG, 2)
  _push_tensix(fw, TTSETDMAREG(0, 0, 0, 56))
  _push_tensix(fw, TTSETDMAREG(0, 32, 0, 57))
  _push_tensix(fw, TTSETDMAREG(0, 512, 0, 58))
  _push_tensix(fw, TTSETDMAREG(0, 2048, 0, 59))
  _push_tensix(fw, TTSTALLWAIT(128, 1))
  _push_tensix(fw, TTWRCFG(28, 0, 12))
  _push_tensix(fw, TTWRCFG(29, 0, 13))
  _push_tensix(fw, TTNOP())
  _push_tensix(fw, TTNOP())
  _push_tensix(fw, TTATGETM(0))
  for raw in (0xB61E0A01, 0xB3FC0002, 0xB4FF0002, 0xB53F0002):
    _write_tensix_instr_word(fw, raw)
  _push_tensix(fw, TTATRELM(0))
  fw.write32(TensixRegs.CFG_BASE + 68 * 4, 0x00400000, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 70 * 4, 0x00000551, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 18 * 4, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 208, 0x00400000, tmp_addr=t0, tmp_val=t1)
  for cfg_addr in (112, 113, 114, 115):
    fw.write32(TensixRegs.CFG_BASE + cfg_addr * 4, 0x00001000, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 96 * 4, 0x0000FFFF, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.CFG_BASE + 20 * 4, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 64, TILE_BYTES, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 68, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 72, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(TensixRegs.REGFILE_BASE + 76, 0, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETADCXX(4, 15, 0))
  _push_tensix(fw, TTSETADCXY(4, 0, 0, 0, 0, 0xB))
  _push_tensix(fw, TTSETADCZW(4, 0, 0, 0, 0, 0xF))
  fw.write32(TM.DATA_COMMON["dest_offset_id"], 0, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSTALLWAIT(33, 8))
  _push_tensix(fw, TTSETDMAREG(0, 0, 0, 8))
  _push_tensix(fw, TTSETDMAREG(0, 512, 0, 16))
  _push_tensix(fw, TTSTALLWAIT(128, 1))
  _push_tensix(fw, TTWRCFG(8, 1, 180))
  _push_tensix(fw, TTDMANOP())
  _push_tensix(fw, TTDMANOP())


def add1_brisc_reader() -> Kernel:
  fw = Kernel()
  fw.breadcrumb(DBG_BRISC, 0x3000)
  for addr in (
    SYNC_OUT_RESERVED, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(SYNC_OUT_RESERVED, 1, tmp_addr=t0, tmp_val=t1)
  _read_rta_from(fw, BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  fw.li(s5, 0)
  fw.label("brisc_loop")
  fw.breadcrumb(DBG_BRISC, 0x3001)
  fw.beq(s5, s3, "brisc_done")
  _cb_reserve_back(fw, BM.CB_INTERFACE, 0)
  fw.breadcrumb(DBG_BRISC, 0x3002)
  if os.environ.get("TT_DEBUG_L1_IO"):
    _cb_write_ptr(fw, BM.CB_INTERFACE, 0, out=t5)
    fw.write32(DBG_SEMS0, t5, tmp_addr=t0, tmp_val=t1)
    _fill_l1_tile_words(fw, t5, 0)
    fw.fence()
    fw.breadcrumb(DBG_BRISC, 0x3003)
  else:
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
  fw.breadcrumb(DBG_BRISC, 0x3004)
  fw.addi(t2, s5, 1)
  _signal_sync(fw, SYNC_READ, t2)
  fw.addi(s5, s5, 1)
  fw.j("brisc_loop")
  fw.label("brisc_done")
  fw.breadcrumb(DBG_BRISC, 0x3005)
  fw.ret()
  return fw


def add1_ncrisc_writer(num_banks: int) -> Kernel:
  fw = Kernel()
  _read_rta_from(fw, NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  fw.li(s5, 0)
  fw.label("ncrisc_loop")
  fw.beq(s5, s3, "ncrisc_done")
  _cb_wait_front(fw, NM.CB_INTERFACE, 16)
  if not os.environ.get("TT_DEBUG_L1_IO"):
    fw.add(a1, s2, s5)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    _dram_tile_addr_from(fw, NM.DRAM_BANK_TO_NOC_XY, num_banks)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
    fw.addi(t4, t4, 1)
    _cb_read_ptr(fw, NM.CB_INTERFACE, 16, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_write(1, 0, t5, a0, 0, a2, t6, a=t0, v=t1)
    fw.noc_write_barrier(1, t4, addr=t0, val=t1)
  _cb_pop_front(fw, NM.CB_INTERFACE, 16)
  fw.addi(s5, s5, 1)
  fw.j("ncrisc_loop")
  fw.label("ncrisc_done")
  fw.ret()
  return fw


def add1_trisc_compute(trisc_id: int) -> Kernel:
  data = TM.DATA1 if trisc_id == 1 else TM.DATA_COMMON
  fw = Kernel()
  fw.addi(sp, sp, -16)
  fw.sw(ra, sp, 12)
  fw.read32(t0, data["rta_l1_base"])
  fw.lw(s3, t0, 0)
  fw.li(t1, 1)
  _wait_sync_value(fw, SYNC_OUT_RESERVED, t1, actual=t2)

  if trisc_id == 0:
    fw.breadcrumb(DBG_TRISC0, 0x1000)
    fw.write32(
      RISCV_DEBUG_REG_DBG_FEATURE_DISABLE,
      (1 << 11) if os.environ.get("TT_DEBUG_UNPACK_FEATURE_DISABLE_11") else 0,
      tmp_addr=t0,
      tmp_val=t1,
    )
    _init_trisc0_unpack(fw)
    fw.breadcrumb(DBG_TRISC0, 0x1001)
  elif trisc_id == 1:
    fw.breadcrumb(DBG_TRISC1, 0x1100)
    _init_trisc1_math(fw)
    fw.breadcrumb(DBG_TRISC1, 0x1101)
  else:
    fw.breadcrumb(DBG_TRISC2, 0x1200)
    _init_trisc2_pack(fw)
    fw.breadcrumb(DBG_TRISC2, 0x1201)

  fw.li(t0, SYNC_TRISC_INIT + trisc_id * 4)
  fw.li(t1, 1)
  fw.sw(t1, t0, 0)
  fw.fence()
  if trisc_id == 0:
    fw.breadcrumb(DBG_TRISC0, 0x1002)
  elif trisc_id == 1:
    fw.breadcrumb(DBG_TRISC1, 0x1102)
  else:
    fw.breadcrumb(DBG_TRISC2, 0x1202)
  fw.li(t1, 1)
  for init_id in range(3):
    _wait_sync_value(fw, SYNC_TRISC_INIT + init_id * 4, t1, actual=t2)

  fw.li(s5, 0)
  fw.label("trisc_loop")
  fw.beq(s5, s3, "trisc_done")
  fw.addi(t2, s5, 1)
  if trisc_id == 0:
    fw.breadcrumb(DBG_TRISC0, 0x2000)
    _cb_wait_front(fw, data["cb_interface"], 0)
    fw.breadcrumb(DBG_TRISC0, 0x2001)
    _cb_read_ptr(fw, data["cb_interface"], 0, out=s0)
    if not os.environ.get("TT_DEBUG_UNPACK_NO_PREDEC"):
      fw.addi(s0, s0, -1)
    fw.write32(DBG_SEMS0, s0, tmp_addr=t0, tmp_val=t1)
    _cb_iface(fw, data["cb_interface"], 0, out=t6)
    fw.lw(t1, t6, 8)
    fw.write32(DBG_SEMS1, t1, tmp_addr=t0, tmp_val=t2)
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
    fw.breadcrumb(DBG_TRISC0, 0x2002)

    fw.read32(t1, TRISC0_UNP_CFG_CONTEXT, tmp_addr=t0)
    fw.li(t2, TensixRegs.CFG_BASE + 76 * 4)
    fw.beq(t1, zero, "trisc0_cfg_addr")
    fw.li(t2, TensixRegs.CFG_BASE + 0x380 + 77 * 4)
    fw.label("trisc0_cfg_addr")
    fw.sw(s0, t2, 0)
    fw.lw(t1, t2, 0)
    fw.write32(DBG_SEMS2, t1, tmp_addr=t0, tmp_val=t3)
    fw.write32(TENSIX_PC_UNPACK_SYNC, 0, tmp_addr=t0, tmp_val=t1)
    _push_tensix(fw, TTSTALLWAIT(8, 1024))
    if os.environ.get("TT_DEBUG_SYNC_AFTER_UNPACK_STALL"):
      _tensix_sync(fw, 0)
      fw.breadcrumb(DBG_TRISC0, 0x2009)
    if os.environ.get("TT_DEBUG_UNPACK_STATUS"):
      _snapshot_tensix_status(fw, DBG_QSTATUS0, DBG_BSTATUS0, DBG_UNPACK_SYNC0)
    if os.environ.get("TT_DEBUG_DIRECT_UNPACK"):
      _write_tensix_instr_word(fw, 0x420080C1)
      for _ in range(4):
        _write_tensix_instr_word(fw, 0x43800101)
    elif os.environ.get("TT_DEBUG_UNPACK_NO_DVALID"):
      _write_tensix_instr_word(fw, 0x42008081)
    elif os.environ.get("TT_DEBUG_UNPACK_NOP_SRCA"):
      _write_tensix_instr_word(fw, 0x43000101)
    elif os.environ.get("TT_DEBUG_UNPACK_NOP_ONLY"):
      _write_tensix_instr_word(fw, 0x43800101)
    else:
      if os.environ.get("TT_DEBUG_UNPACK_PRECLEAR_SRCA"):
        _write_tensix_instr_word(fw, 0x43000101)
      _write_mop_cfg(fw, UNPACK_MOP_CFG, 0)
      _push_tensix(fw, TTMOP(1, 0, 0))
    fw.breadcrumb(DBG_TRISC0, 0x2003)
    if os.environ.get("TT_DEBUG_FORCE_UNPACK_TO_DEST_POST"):
      _push_tensix(fw, TTSEMPOST(4))
      fw.breadcrumb(DBG_TRISC0, 0x2010)
    if os.environ.get("TT_DEBUG_UNPACK_STATUS"):
      _snapshot_tensix_status(fw, DBG_QSTATUS1, DBG_BSTATUS1, DBG_UNPACK_SYNC1)
    if os.environ.get("TT_DEBUG_SYNC_AFTER_UNPACK_MOP"):
      _tensix_sync(fw, 0)
      fw.breadcrumb(DBG_TRISC0, 0x2008)
    _push_tensix(fw, TTSEMGET(32))
    fw.breadcrumb(DBG_TRISC0, 0x2005)
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
    fw.breadcrumb(DBG_TRISC0, 0x2006)
    _cb_pop_front(fw, data["cb_interface"], 0, tensix_ack=True)
    fw.breadcrumb(DBG_TRISC0, 0x2007)
    fw.addi(t2, s5, 1)
    _signal_sync(fw, SYNC_DONE0, t2)
    fw.breadcrumb(DBG_TRISC0, 0x2004)
  elif trisc_id == 1:
    if os.environ.get("TT_DEBUG_UNPACK_ONLY"):
      fw.addi(t2, s5, 1)
      _signal_sync(fw, SYNC_DONE1, t2)
      fw.breadcrumb(DBG_TRISC1, 0x2190)
      fw.addi(s5, s5, 1)
      fw.j("trisc_loop")
    fw.breadcrumb(DBG_TRISC1, 0x2100)
    fw.breadcrumb(DBG_TRISC1, 0x2101)
    if os.environ.get("TT_DEBUG_WAIT_TRISC0_DONE_BEFORE_MATH"):
      fw.addi(t2, s5, 1)
      _wait_sync_value(fw, SYNC_DONE0, t2)
      fw.breadcrumb(DBG_TRISC1, 0x2106)
    if os.environ.get("TT_DEBUG_PCBUF_SEMS"):
      _snapshot_pcbuf_sems(fw, DBG_QSTATUS1)
    if os.environ.get("TT_DEBUG_NO_PACK"):
      fw.breadcrumb(DBG_TRISC1, 0x2180)
    else:
      fw.emit(0x9A84002A)  # ttsemwait 322,2,2
    fw.breadcrumb(DBG_TRISC1, 0x2102)
    if os.environ.get("TT_DEBUG_PCBUF_SEMS"):
      _tensix_sync(fw, 1)
      _snapshot_pcbuf_sems(fw, DBG_BSTATUS1)
    if os.environ.get("TT_DEBUG_SYNC_AFTER_SEMWAIT"):
      _tensix_sync(fw, 1)
      fw.breadcrumb(DBG_TRISC1, 0x2105)
    fw.read32(t1, TM.DATA1["dest_offset_id"], tmp_addr=t0)
    fw.sltu(t1, zero, t1)
    fw.slli(t1, t1, 9)
    fw.li(t2, 0xB2010000)
    fw.add(t1, t1, t2)
    fw.breadcrumb(DBG_TRISC1, 0x2110)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    fw.breadcrumb(DBG_TRISC1, 0x2111)
    if os.environ.get("TT_DEBUG_SYNC_AFTER_DEST_SET"):
      _tensix_sync(fw, 1)
      fw.breadcrumb(DBG_TRISC1, 0x2114)
    if os.environ.get("TT_DEBUG_SKIP_MATH_DATACOPY"):
      fw.breadcrumb(DBG_TRISC1, 0x2116)
    elif os.environ.get("TT_DEBUG_DIRECT_MATH_DATACOPY"):
      mova2d = 0x0900A000 if os.environ.get("TT_DEBUG_MOVDBGA2D") else 0x1200A000
      for _ in range(4):
        _write_tensix_instr_word(fw, mova2d)
        _write_tensix_instr_word(fw, mova2d)
        _write_tensix_instr_word(fw, 0x37C00003)
    else:
      _write_mop_cfg(fw, MATH_DATACOPY_MOP_CFG, 1)
      fw.emit(0x06000000)  # ttmop 1,0,0
    fw.breadcrumb(DBG_TRISC1, 0x2112)
    if os.environ.get("TT_DEBUG_PCBUF_SEMS"):
      _snapshot_pcbuf_sems(fw, DBG_UNPACK_SYNC1)
    if os.environ.get("TT_DEBUG_SYNC_AFTER_MATH_MOP"):
      _tensix_sync(fw, 1)
      fw.breadcrumb(DBG_TRISC1, 0x2115)
    fw.emit(0xDC000010)  # ttsetrwc 0,0,0,0,0,4
    fw.breadcrumb(DBG_TRISC1, 0x2113)
    if os.environ.get("TT_DEBUG_STOP_AFTER_MATH_DATACOPY"):
      fw.addi(t2, s5, 1)
      _signal_sync(fw, SYNC_DONE1, t2)
      fw.breadcrumb(DBG_TRISC1, 0x2191)
      fw.addi(s5, s5, 1)
      fw.j("trisc_loop")
    fw.read32(t1, TM.DATA1["dest_offset_id"], tmp_addr=t0)
    fw.sltu(t1, zero, t1)
    fw.slli(t1, t1, 9)
    fw.li(t2, 0xB2010000)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    fw.emit(0x8A000042)  # ttstallwait 256,16
    if os.environ.get("TT_DEBUG_SFPU_STORE_CONST"):
      fw.breadcrumb(DBG_TRISC1, 0x2140)
      _write_tensix_instr_word(fw, TTSFPLOADI(0, 10, 0))
      _write_tensix_instr_word(fw, TTSFPLOADI(0, 8, 0x3F80))
      store_mod0 = 2 if os.environ.get("TT_DEBUG_SFPU_STORE_BF16") else 0
      _push_tensix(fw, TTSFPSTORE(0, store_mod0, 7, 0))
      fw.breadcrumb(DBG_TRISC1, 0x2141)
      if os.environ.get("TT_DEBUG_SYNC_AFTER_SFPU_MOP"):
        _tensix_sync(fw, 1)
        fw.breadcrumb(DBG_TRISC1, 0x2142)
      _push_tensix(fw, TTINCRWC(0, 2, 0, 0))
      fw.j("trisc1_sfpu_done")
    if os.environ.get("TT_DEBUG_SFPU_REPLAY_MOP"):
      _write_mop_cfg(fw, _sfpu_add1_mop_cfg(), 1)
      fw.breadcrumb(DBG_TRISC1, 0x2130)
      fw.emit(0x06000000)  # ttmop 1,0,0
    elif os.environ.get("TT_DEBUG_SFPU_DIRECT_REPLAY"):
      fw.breadcrumb(DBG_TRISC1, 0x2130)
      fw.emit(0x10000140)  # ttreplay 0,5,0,0
    else:
      fw.breadcrumb(DBG_TRISC1, 0x2130)
      _sfpu_add1_face_loop(fw)
    fw.breadcrumb(DBG_TRISC1, 0x2131)
    if os.environ.get("TT_DEBUG_SYNC_AFTER_SFPU_MOP_EXPAND"):
      _mop_sync(fw, 1)
      fw.breadcrumb(DBG_TRISC1, 0x2132)
    if os.environ.get("TT_DEBUG_SYNC_AFTER_SFPU_MOP"):
      _tensix_sync(fw, 1)
      fw.breadcrumb(DBG_TRISC1, 0x2133)
    if os.environ.get("TT_DEBUG_STOP_AFTER_SFPU"):
      fw.addi(t2, s5, 1)
      _signal_sync(fw, SYNC_DONE1, t2)
      fw.breadcrumb(DBG_TRISC1, 0x2192)
      fw.addi(s5, s5, 1)
      fw.j("trisc_loop")
    fw.label("trisc1_sfpu_done")
    fw.breadcrumb(DBG_TRISC1, 0x2124)
    fw.emit(0xDC000010)  # ttsetrwc 0,0,0,0,0,4
    fw.emit(0x88042042)  # ttstallwait 2,2064
    fw.emit(0x90000022)  # ttsempost 2
    fw.breadcrumb(DBG_TRISC1, 0x2103)
    fw.read32(t1, TM.DATA1["dest_offset_id"], tmp_addr=t0)
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(TM.DATA1["dest_offset_id"], t2, tmp_addr=t0, tmp_val=t3)
    fw.emit(0x89002042)  # ttstallwait 128,2064
    fw.addi(t1, t1, -1)
    fw.sltu(t1, zero, t1)
    fw.slli(t1, t1, 9)
    fw.li(t2, 0xB2010000)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    fw.addi(t2, s5, 1)
    _signal_sync(fw, SYNC_DONE1, t2)
    fw.breadcrumb(DBG_TRISC1, 0x2104)
  elif trisc_id == 2:
    if os.environ.get("TT_DEBUG_UNPACK_ONLY"):
      fw.addi(t2, s5, 1)
      _signal_sync(fw, SYNC_DONE2, t2)
      fw.breadcrumb(DBG_TRISC2, 0x2290)
      fw.addi(s5, s5, 1)
      fw.j("trisc_loop")
    fw.breadcrumb(DBG_TRISC2, 0x2200)
    fw.breadcrumb(DBG_TRISC2, 0x2201)
    _push_tensix(fw, TTSEMWAIT(1, 2, 1))
    fw.breadcrumb(DBG_TRISC2, 0x2202)
    _cb_reserve_back(fw, data["cb_interface"], 16)
    fw.breadcrumb(DBG_TRISC2, 0x2203)
    _cb_write_ptr(fw, data["cb_interface"], 16, out=s0)
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
    fw.breadcrumb(DBG_TRISC2, 0x2204)
    _push_tensix(fw, TTSETADCZW(4, 0, 0, 0, 0, 5))
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
    fw.addi(t1, t1, -1)
    fw.sltiu(t1, t1, 1)
    fw.sub(t1, zero, t1)
    fw.andi(t1, t1, -4)
    fw.addi(t1, t1, 8)
    fw.slli(t1, t1, 16)
    fw.li(t2, 0xB00080B4)
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    _push_tensix(fw, TTDMANOP())
    _push_tensix(fw, TTDMANOP())
    if os.environ.get("TT_DEBUG_SYNC_AFTER_PACK"):
      _tensix_sync(fw, 2)
      fw.breadcrumb(DBG_TRISC2, 0x2208)
    _cb_push_back(fw, data["cb_interface"], 16)
    fw.breadcrumb(DBG_TRISC2, 0x2205)
    fw.breadcrumb(DBG_TRISC2, 0x2206)
  fw.addi(s5, s5, 1)
  fw.j("trisc_loop")
  fw.label("trisc_done")
  fw.lw(ra, sp, 12)
  fw.addi(sp, sp, 16)
  fw.ret()
  return fw


def build_program(src_addr: int, dst_addr: int, tiles_per_core: int, num_cores: int, num_banks: int) -> Program:
  def rtas_for_core(core_index: int):
    def brisc_rtas(_x: int, _y: int) -> list[int]:
      return [src_addr, core_index * tiles_per_core, tiles_per_core, num_banks]
    def ncrisc_rtas(_x: int, _y: int) -> list[int]:
      return [dst_addr, core_index * tiles_per_core, tiles_per_core, num_banks]
    def trisc_rtas(_x: int, _y: int) -> list[int]:
      return [tiles_per_core]
    return {
      "brisc": brisc_rtas,
      "ncrisc": ncrisc_rtas,
      "trisc0": trisc_rtas,
      "trisc1": trisc_rtas,
      "trisc2": trisc_rtas,
    }

  ret = lambda: Kernel().ret()
  brisc = add1_brisc_reader()
  ncrisc = add1_ncrisc_writer(num_banks)
  trisc0 = add1_trisc_compute(0)
  trisc1 = add1_trisc_compute(1)
  trisc2 = add1_trisc_compute(2)
  if os.environ.get("TT_DEBUG_ADD1_BRISC_ONLY"):
    ncrisc, trisc0, trisc1, trisc2 = ret(), ret(), ret(), ret()
  if os.environ.get("TT_DEBUG_ADD1_NO_TRISC"):
    trisc0, trisc1, trisc2 = ret(), ret(), ret()
  if os.environ.get("TT_DEBUG_NO_PACK"):
    ncrisc, trisc2 = ret(), ret()
  if os.environ.get("TT_DEBUG_UNPACK_ONLY"):
    ncrisc = ret()
  for role, fn in rtas_for_core(0).items():
    {"brisc": brisc, "ncrisc": ncrisc, "trisc0": trisc0, "trisc1": trisc1, "trisc2": trisc2}[role].rta(fn)
  prog = Program(
    num_cores=num_cores,
    brisc=brisc,
    ncrisc=ncrisc,
    trisc0=trisc0,
    trisc1=trisc1,
    trisc2=trisc2,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (16, TILE_BYTES, CB_DEPTH)],
  )
  prog.name = "add1"

  old_layout = prog._layout_core

  def layout_core(*, core_xy=None, dispatch_mode=0, host_assigned_id=0):
    if core_xy is not None:
      cores = getattr(prog, "_add1_target_cores", [core_xy])
      idx = cores.index(core_xy) if core_xy in cores else 0
      for role, fn in rtas_for_core(idx).items():
        getattr(prog, role).rta(fn)
    return old_layout(core_xy=core_xy, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)

  old_target = prog._target_cores

  def target_cores(cores):
    target = old_target(cores)
    prog._add1_target_cores = target
    return target

  prog._target_cores = target_cores
  prog._layout_core = layout_core
  return prog


def main():
  if os.environ.get("TT_DEBUG_L1_IO"):
    os.environ.setdefault("TT_DEBUG_KEEP_POWER", "1")
  for addr in (
    INPUT_L1, INPUT_L1 + 4, OUTPUT_L1, OUTPUT_L1 + 4,
    DBG_BRISC,
    DBG_SEMS0, DBG_SEMS1, DBG_SEMS2,
    DBG_QSTATUS0, DBG_BSTATUS0, DBG_UNPACK_SYNC0,
    DBG_QSTATUS1, DBG_BSTATUS1, DBG_UNPACK_SYNC1,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
    Mailbox.SUBORDINATE_SYNC,
  ):
    Kernel.note_debug_addr(addr)

  device = Device()
  try:
    num_cores = int(os.environ.get("CORES", str(len(device.cores))))
    tiles_per_core = int(os.environ.get("TILES", "4"))
    print_n = 8
    n_tiles = num_cores * tiles_per_core

    if os.environ.get("TT_DEBUG_L1_IO"):
      src_rm = b"\0" * (n_tiles * TILE_BYTES)
      prog = build_program(0, 0, tiles_per_core, num_cores, 1)
    else:
      src_rm = _seed_src_tensor(n_tiles)
      src_buf = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="src")
      dst_buf = device.dram.alloc(n_tiles, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="dst")
      num_banks = len(device.dram.bank_tiles)
      prog = build_program(src_buf.addr, dst_buf.addr, tiles_per_core, num_cores, num_banks)
    try:
      timings = device.run(prog)
    except Exception:
      _debug_postmortem_existing_device(device)
      raise
    if os.environ.get("TT_DEBUG_L1_IO"):
      with TLBWindow(device.dev, device.cores[0]) as win:
        out = bytes(win.mm[OUTPUT_L1 + i] for i in range(n_tiles * TILE_BYTES))
    else:
      out = device.dram_read(dst_buf)
    exp = _expected_add1(src_rm)
    mismatch = _first_mismatch(out, exp)

    print(f"input first {print_n}: {_format_bf16_ints(src_rm, print_n)}")
    print(f"output first {print_n}: {_format_bf16_ints(out, print_n)}")
    print(f"expect first {print_n}: {_format_bf16_ints(exp, print_n)}")
    if mismatch is None:
      print(f"PASS add1 {n_tiles} tiles across {num_cores} cores")
    else:
      print(
        f"mismatch byte={mismatch} "
        f"got={out[mismatch:mismatch + 32].hex()} "
        f"exp={exp[mismatch:mismatch + 32].hex()}"
      )
    for i, timing in enumerate(timings):
      print(f"  [{i}] {timing['name']} {timing['us']:,.1f} us")
  finally:
    device.close()


if __name__ == "__main__":
  main()
