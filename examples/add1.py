#!/usr/bin/env python3
from __future__ import annotations

import struct
import sys
import os
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from device import Device
from pcie import TLBWindow
from dsl import (
  TTATGETM, TTATRELM, TTDMANOP, TTINCRWC, TTMOP, TTMOVA2D, TTNOP, TTPACR, TTSETADC,
  TTSEMGET, TTSEMINIT, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSFPADD, TTSFPCONFIG,
  TTSFPLOAD, TTSFPLOADI, TTSFPSTORE, TTSETADCXX, TTSETADCXY, TTSETADCZW,
  TTSETC16, TTSETDMAREG, TTSTALLWAIT, TTSTOREREG, TTWRCFG,
  TTUNPACR, TTUNPACR_NOP, TTZEROACC, TTZEROSRC, a0, a1, a2, a5, ra,
  s0, s1, s2, s3, s4, s5, sp, t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk.addrs import BriscMailbox as BM, CircularBuffer as CB, NcriscMailbox as NM, NOC, TensixL1, TriscMailbox as TM
from ttk.tensix import TensixRegs, TensixSem

TILE_BYTES = Dtype.Float16_b.tile_size
CB_DEPTH = 2
TARGET_CORE = (1, 2)
TILES_PER_CORE = 1
DEBUG_SKIP_PACK_MOP = os.environ.get("ADD1_DEBUG_SKIP_PACK_MOP") == "1"
SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE
SYNC_L1 = SCRATCH_L1 + 0x10000
SYNC_OUT_RESERVED = SYNC_L1
SYNC_READ = SYNC_L1 + 4
SYNC_DONE0 = SYNC_L1 + 8
SYNC_DONE1 = SYNC_L1 + 12
SYNC_DONE2 = SYNC_L1 + 16
SYNC_TRISC_INIT = SYNC_L1 + 20
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
RISCV_DEBUG_REG_DBG_FEATURE_DISABLE = 0xFFB12068
RISCV_DEBUG_REG_DBG_ARRAY_RD_EN = 0xFFB12060
RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD = 0xFFB12064
RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA = 0xFFB1206C
DBG_BASE = 0x19000
DBG_TRISC0 = DBG_BASE + 0x00
DBG_TRISC1 = DBG_BASE + 0x04
DBG_TRISC2 = DBG_BASE + 0x08
DBG_BRISC = DBG_BASE + 0x0C
DBG_SEMS0 = DBG_BASE + 0x10
DBG_SEMS1 = DBG_BASE + 0x14
DBG_SEMS2 = DBG_BASE + 0x18
DBG_SYNC_READ = DBG_BASE + 0x20
DBG_SYNC_DONE0 = DBG_BASE + 0x24
DBG_SYNC_DONE1 = DBG_BASE + 0x28
DBG_SYNC_DONE2 = DBG_BASE + 0x2C
DBG_SYNC_INIT0 = DBG_BASE + 0x30
DBG_SYNC_INIT1 = DBG_BASE + 0x34
DBG_SYNC_INIT2 = DBG_BASE + 0x38
DBG_NCRISC = DBG_BASE + 0x3C
TRACE_BRISC = DBG_BASE + 0x40
TRACE_TRISC0 = DBG_BASE + 0x44
TRACE_TRISC1 = DBG_BASE + 0x48
TRACE_TRISC2 = DBG_BASE + 0x4C
TRACE_NCRISC = DBG_BASE + 0x50
DBG_TRISC2_PACK_PTR_16B = DBG_BASE + 0x60
DBG_TRISC2_PACK_PTR_BYTES = DBG_BASE + 0x64
DBG_TRISC2_PACK_ADDR_MINUS_ONE = DBG_BASE + 0x68
PCBUF_SEM_BASE = 0xFFE80020
PACK_MOP_CFG = [
  4, 4, 0x02000000, 0x02000000, 0x02000000,
  0x41000000, 0x02000000, 0x41008001, 0x41010000,
]
PACK_DIRECT_WORDS = [
  TTNOP(),
  TTNOP(),
  TTNOP(),
  TTPACR(),
  TTNOP(),
  TTPACR(AddrMode=1, Last=1),
  TTPACR(AddrMode=2),
]
UNPACK_DIRECT_WORDS = [
  TTUNPACR(
    Unpack_block_selection=0,
    AddrMode=1,
    CfgContextCntInc=0,
    CfgContextId=0,
    AddrCntContextId=0,
    OvrdThreadId=1,
    SetDatValid=1,
    srcb_bcast=0,
    ZeroWrite2=0,
    AutoIncContextID=0,
    RowSearch=0,
    SearchCacheFlush=0,
    Last=1,
  ),
  TTNOP(),
  TTNOP(),
  TTUNPACR_NOP(
    Unpacker_Select=1,
    Stream_Id=0,
    Msg_Clr_Cnt=0,
    Set_Dvalid=1,
    Clr_to1_fmt_Ctrl=0,
    Stall_Clr_Cntrl=0,
    Bank_Clr_Ctrl=0,
    Src_ClrVal_Ctrl=0,
    Unpack_Pop=1,
  ),
  TTNOP(),
  TTUNPACR_NOP(
    Unpacker_Select=1,
    Stream_Id=0,
    Msg_Clr_Cnt=0,
    Set_Dvalid=1,
    Clr_to1_fmt_Ctrl=0,
    Stall_Clr_Cntrl=0,
    Bank_Clr_Ctrl=0,
    Src_ClrVal_Ctrl=0,
    Unpack_Pop=1,
  ),
  TTUNPACR_NOP(
    Unpacker_Select=1,
    Stream_Id=0,
    Msg_Clr_Cnt=0,
    Set_Dvalid=1,
    Clr_to1_fmt_Ctrl=0,
    Stall_Clr_Cntrl=0,
    Bank_Clr_Ctrl=0,
    Src_ClrVal_Ctrl=0,
    Unpack_Pop=1,
  ),
]


def _bf16(x: float) -> int:
  return struct.unpack("<I", struct.pack("<f", x))[0] >> 16


def _f32(x: int) -> float:
  return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]


def _dst_bf16(x: int) -> float:
  sign = (x & 0x8000) >> 15
  mantissa = (x & 0x7F00) >> 8
  exponent = x & 0x00FF
  bf16 = (sign << 15) | (exponent << 7) | mantissa
  return struct.unpack(">f", bf16.to_bytes(2, "big") + b"\0\0")[0]


def _format_bf16_ints(data: bytes, count: int) -> str:
  values = []
  for i in range(0, min(len(data), count * 2), 2):
    value = _f32(int.from_bytes(data[i : i + 2], "little"))
    values.append("nan" if value != value else str(int(value)))
  return " ".join(values)


def _print_tile_faces(label: str, data: bytes, *, tile: int = 0, rows_per_face: int = 16, cols: int = 8):
  tile_base = tile * TILE_BYTES
  print(label)
  for face in range(4):
    face_base = tile_base + face * 16 * 16 * 2
    vals = []
    for i in range(cols):
      off = face_base + i * 2
      vals.append(str(int(_f32(int.from_bytes(data[off : off + 2], "little")))))
    print(f"  face{face}: {' '.join(vals)}")


def _read_dst_debug_array_words(device: Device, core: tuple[int, int], rows: int = 16) -> list[list[int]]:
  out: list[list[int]] = []
  base = RISCV_DEBUG_REG_DBG_ARRAY_RD_EN & ~(TLBWindow.SIZE_2M - 1)
  rd_en = RISCV_DEBUG_REG_DBG_ARRAY_RD_EN - base
  rd_cmd = RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD - base
  rd_data = RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA - base
  with TLBWindow(device.dev, core, addr=base) as win:
    win.write32(rd_en, 1)
    try:
      for row in range(rows):
        row_words = []
        base_cmd = row + (2 << 16)  # DEST_ARRAY_ID = 2
        for lane_group in range(8):
          win.write32(rd_cmd, base_cmd + (lane_group << 12))
          row_words.append(win.read32(rd_data))
        out.append(row_words)
    finally:
      win.write32(rd_cmd, 0)
      win.write32(rd_en, 0)
  return out


def _print_dst_debug_rows(label: str, rows: list[list[int]]):
  print(label)
  for row, words in enumerate(rows):
    raw = " ".join(f"{word:08x}" for word in words)
    bf16_le = []
    bf16_be = []
    exalens_bf16 = []
    for word in words:
      for shift in (0, 16):
        value = _f32((word >> shift) & 0xFFFF)
        bf16_le.append("nan" if value != value else str(int(value)))
      for shift in (16, 0):
        value = _f32((word >> shift) & 0xFFFF)
        bf16_be.append("nan" if value != value else str(int(value)))
      raw_bytes = word.to_bytes(4, "big")
      for i in range(0, 4, 2):
        value = _dst_bf16(int.from_bytes(raw_bytes[i : i + 2], "big"))
        exalens_bf16.append("nan" if value != value else str(int(value)))
    print(f"  row{row:02d} raw: {raw}")
    print(f"        bf16 le-halves: {' '.join(bf16_le)}")
    print(f"        bf16 be-halves: {' '.join(bf16_be)}")
    print(f"        tt-exalens bf16: {' '.join(exalens_bf16)}")


def _print_l1_mailbox(device: Device, core: tuple[int, int], label: str):
  print(label)
  with TLBWindow(device.dev, core) as win:
    for addr, name in (
      (0x68, "subordinate_sync"),
      (0x6C, "launch_msg_rd_ptr"),
      (TensixL1.LAUNCH, "launch"),
      (TensixL1.GO_MSG, "go_msg"),
      (TensixL1.GO_MSG_INDEX, "go_msg_index"),
      (SYNC_DONE0, "sync_done0"),
      (SYNC_DONE1, "sync_done1"),
      (SYNC_DONE2, "sync_done2"),
    ):
      print(f"  {name} @ 0x{addr:x}: 0x{win.read32(addr):08x}")


def _read_l1_bytes(device: Device, core: tuple[int, int], addr: int, size: int) -> bytes:
  with TLBWindow(device.dev, core) as win:
    return bytes(win.mm[addr + i] for i in range(size))


def _print_l1_tile_probe(device: Device, core: tuple[int, int], addr: int, label: str):
  data = _read_l1_bytes(device, core, addr, TILE_BYTES)
  words = [int.from_bytes(data[i : i + 4], "little") for i in range(0, 32, 4)]
  nonzero = sum(1 for b in data if b)
  print(f"{label} @ 0x{addr:x}: nonzero_bytes={nonzero}/{len(data)}")
  print("  first words:", " ".join(f"{word:08x}" for word in words))
  _print_tile_faces(f"  {label} faces:", data)


def _print_l1_words_probe(device: Device, core: tuple[int, int], addr: int, label: str, words: int = 32):
  with TLBWindow(device.dev, core) as win:
    values = [win.read32(addr + i * 4) for i in range(words)]
  nonzero = sum(1 for value in values if value)
  print(f"{label} @ 0x{addr:x}: nonzero_words={nonzero}/{words}")
  for row in range(0, words, 8):
    print("  " + " ".join(f"{value:08x}" for value in values[row : row + 8]))


def _read_noc_u32(device: Device, core: tuple[int, int], addr: int) -> int:
  win_size = TLBWindow.SIZE_2M
  base = addr & ~(win_size - 1)
  off = addr - base
  with TLBWindow(device.dev, core, addr=base) as win:
    return win.read32(off)


def _print_noc_u32(device: Device, core: tuple[int, int], addr: int, label: str):
  value = _read_noc_u32(device, core, addr)
  print(f"{label} @ 0x{addr:x}: 0x{value:08x} ({value})")


def _print_cb_sync_probes(device: Device, core: tuple[int, int], label: str):
  for cb_index in (0, 16):
    rcv = CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE
    ack = CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE
    _print_noc_u32(device, core, rcv, f"{label} cb{cb_index} SYNC_TILES_RECEIVED")
    _print_noc_u32(device, core, ack, f"{label} cb{cb_index} SYNC_TILES_ACKED")


def _print_trisc2_pack_debug(device: Device, core: tuple[int, int], label: str):
  for addr, name in (
    (DBG_TRISC2_PACK_PTR_16B, "trisc2_cb16_write_ptr_16b"),
    (DBG_TRISC2_PACK_PTR_BYTES, "trisc2_cb16_write_ptr_bytes"),
    (DBG_TRISC2_PACK_ADDR_MINUS_ONE, "trisc2_pack_addr_minus_one_16b"),
    (TRACE_TRISC2, "trace_trisc2"),
  ):
    _print_noc_u32(device, core, addr, f"{label} {name}")


def _print_cb_interface_probe(device: Device, core: tuple[int, int], interface_base: int, cb_index: int, label: str):
  base = interface_base + cb_index * CB.LOCAL_INTERFACE_SIZE
  for off, name in (
    (8, "fifo_page_size"),
    (16, "fifo_rd_ptr"),
    (20, "fifo_wr_ptr"),
    (24, "tiles_acked_received"),
  ):
    _print_noc_u32(device, core, base + off, f"{label} cb{cb_index} {name}")


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


def _signal_sync(fw: Kernel, addr: int, value_reg):
  fw.write32(addr, value_reg, tmp_addr=t0, tmp_val=t1)


def _debug_sync(fw: Kernel, addr: int, value_reg):
  names = {
    SYNC_READ: ("sync_read", DBG_SYNC_READ),
    SYNC_DONE0: ("sync_done_trisc0", DBG_SYNC_DONE0),
    SYNC_DONE1: ("sync_done_trisc1", DBG_SYNC_DONE1),
    SYNC_DONE2: ("sync_done_trisc2", DBG_SYNC_DONE2),
    SYNC_TRISC_INIT: ("sync_init_trisc0", DBG_SYNC_INIT0),
    SYNC_TRISC_INIT + 4: ("sync_init_trisc1", DBG_SYNC_INIT1),
    SYNC_TRISC_INIT + 8: ("sync_init_trisc2", DBG_SYNC_INIT2),
  }
  name, dbg_addr = names[addr]
  fw.debug_write(dbg_addr, value_reg, name=name, tmp_addr=t0, tmp_val=t1)


def _trace_stage(fw: Kernel, addr: int, name: str, stage: int, tile_reg=s5, *, tmp=t0):
  fw.li(tmp, (stage & 0xFF) << 24)
  fw.or_(tmp, tmp, tile_reg)
  fw.note_debug_addr(addr)
  fw.write32(addr, tmp, tmp_addr=t1, tmp_val=t2)


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


def _write_repeated_words_at_reg(fw: Kernel, addr_reg, value: int, count_words: int, *, tmp=t1):
  fw.li(tmp, value)
  for i in range(count_words):
    fw.sw(tmp, addr_reg, i * 4)


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


def _sfpu_add1_one_iteration(fw: Kernel):
  # Materialize bf16 1.0 in LReg1, then add it to one Dst/SFPU vector.
  _write_tensix_instr_word(fw, TTSFPLOADI(1, 0, 0x3F80))
  _write_tensix_instr_word(fw, TTSETRWC(0, 0, 0, 0, 0, 15))
  _write_tensix_instr_word(fw, TTSFPLOAD(0, 0, 7, 0))
  _write_tensix_instr_word(fw, TTSFPADD(10, 0, 1, 0, 0))
  _write_tensix_instr_word(fw, TTSFPSTORE(0, 0, 7, 0))
  _write_tensix_instr_word(fw, TTINCRWC(0, 2, 0, 0))


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
  _write_tensix_instr_word(fw, 0x5E23FC00)
  _write_tensix_instr_word(fw, 0x5E43FC00)
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
  _tensix_sync(fw, 0)


def _init_trisc1_math(fw: Kernel):
  _write_repeated_bytes(fw, TRISC1_UNPACK_TILE_NUM_FACES, 4, 8)
  fw.write32(TRISC1_UNPACK_DST_FORMAT, Dtype.Float16_b.value, tmp_addr=t0, tmp_val=t1)
  fw.write32(TRISC1_UNPACK_SRC_FORMAT, Dtype.Float16_b.value, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETC16(13, 0))
  _push_tensix(fw, TTSETC16(29, 0))
  _push_tensix(fw, TTSETC16(48, 0))
  _push_tensix(fw, TTZEROACC(3, 0, 0, 1, 0))
  _math_direct_mova2d_init(fw)
  _tensix_sync(fw, 1)
  _wait_mmio_low_byte_zero(fw, PCBUF_SEM_BASE + 4)
  _push_tensix(fw, TTSEMINIT(sem_sel=2, init_value=0, max_value=2))
  fw.write32(TM.DATA1["dest_offset_id"], 0, tmp_addr=t0, tmp_val=t1)
  _push_tensix(fw, TTSETC16(1, 0))
  _write_tensix_instr_word(fw, 0xB30808DC)
  _push_tensix(fw, TTSTALLWAIT(128, 16))
  _write_tensix_instr_word(fw, 0xB6800001)
  _math_direct_mova2d_init(fw)
  _push_tensix(fw, TTSFPCONFIG(0, 15, 1))
  _push_tensix(fw, TTSFPLOADI(1, 0, 0x3F80))
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
  _cb_iface(fw, TM.DATA_COMMON["cb_interface"], 16, out=t6)
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
  _push_tensix(fw, TTSETDMAREG(0, 0, 0, 8))
  _push_tensix(fw, TTSETDMAREG(0, 512, 0, 16))
  _push_tensix(fw, TTSTALLWAIT(128, 1))
  _push_tensix(fw, TTWRCFG(8, 1, 180))
  _push_tensix(fw, TTDMANOP())
  _push_tensix(fw, TTDMANOP())

  # ADCXY/ZW (OLD 6d64..6d68) - issued AFTER WRCFG(8,1,180) + DMANOPs.
  _push_tensix(fw, TTSETADCXY(4, 0, 0, 0, 0, 0xB))
  _push_tensix(fw, TTSETADCZW(4, 0, 0, 0, 0, 0xF))


def add1_brisc_reader() -> Kernel:
  fw = Kernel()
  fw.breadcrumb(DBG_BRISC, "brisc:0x3000")
  for addr in (
    SYNC_OUT_RESERVED, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0, tmp_addr=t0, tmp_val=t1)
  fw.write32(SYNC_OUT_RESERVED, 1, tmp_addr=t0, tmp_val=t1)
  _read_rta_from(fw, BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  fw.li(s5, 0)
  fw.label("brisc_loop")
  fw.breadcrumb(DBG_BRISC, "brisc:0x3001")
  fw.beq(s5, s3, "brisc_done")
  _trace_stage(fw, TRACE_BRISC, "brisc.reserve_cb0", 0x10)
  _cb_reserve_back(fw, BM.CB_INTERFACE, 0)
  fw.breadcrumb(DBG_BRISC, "brisc:0x3002")
  fw.add(a1, s2, s5)
  fw.mv(a0, s0)
  fw.mv(a2, s4)
  _dram_tile_addr_from(fw, BM.DRAM_BANK_TO_NOC_XY, 0)
  _local_noc0_coord(fw, a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  _cb_write_ptr(fw, BM.CB_INTERFACE, 0, out=t5)
  fw.li(t6, TILE_BYTES)
  _trace_stage(fw, TRACE_BRISC, "brisc.noc_read_to_cb0", 0x11)
  fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.label("brisc_read_wait")
  fw.lw(t1, t0, 0)
  fw.bltu(t1, t4, "brisc_read_wait")
  fw.fence()
  _cb_push_back(fw, BM.CB_INTERFACE, 0)
  _trace_stage(fw, TRACE_BRISC, "brisc.cb0_ready", 0x12)
  fw.breadcrumb(DBG_BRISC, "brisc:0x3004")
  fw.addi(t2, s5, 1)
  _signal_sync(fw, SYNC_READ, t2)
  _debug_sync(fw, SYNC_READ, t2)
  fw.addi(s5, s5, 1)
  fw.j("brisc_loop")
  fw.label("brisc_done")
  fw.breadcrumb(DBG_BRISC, "brisc:0x3005")
  fw.ret()
  return fw


def add1_ncrisc_writer(num_banks: int) -> Kernel:
  fw = Kernel()
  fw.breadcrumb(DBG_NCRISC, "ncrisc:0x4000")
  _read_rta_from(fw, NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  fw.li(s5, 0)
  fw.label("ncrisc_loop")
  fw.breadcrumb(DBG_NCRISC, "ncrisc:0x4001")
  fw.beq(s5, s3, "ncrisc_done")
  _trace_stage(fw, TRACE_NCRISC, "ncrisc.wait_cb16", 0x80)
  _cb_wait_front(fw, NM.CB_INTERFACE, 16)
  fw.breadcrumb(DBG_NCRISC, "ncrisc:0x4002")
  fw.add(a1, s2, s5)
  fw.mv(a0, s0)
  fw.mv(a2, s4)
  _dram_tile_addr_from(fw, NM.DRAM_BANK_TO_NOC_XY, num_banks)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
  fw.addi(t4, t4, 1)
  _cb_read_ptr(fw, NM.CB_INTERFACE, 16, out=t5)
  fw.li(t6, TILE_BYTES)
  _trace_stage(fw, TRACE_NCRISC, "ncrisc.noc_write_cb16_to_dram", 0x81)
  fw.noc_write(1, 0, t5, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(1, t4, addr=t0, val=t1)
  fw.breadcrumb(DBG_NCRISC, "ncrisc:0x4003")
  _cb_pop_front(fw, NM.CB_INTERFACE, 16)
  _trace_stage(fw, TRACE_NCRISC, "ncrisc.dram_write_done", 0x82)
  fw.breadcrumb(DBG_NCRISC, "ncrisc:0x4004")
  fw.addi(s5, s5, 1)
  fw.j("ncrisc_loop")
  fw.label("ncrisc_done")
  fw.breadcrumb(DBG_NCRISC, "ncrisc:0x4005")
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
    fw.breadcrumb(DBG_TRISC0, "trisc0:0x1000")
    fw.write32(RISCV_DEBUG_REG_DBG_FEATURE_DISABLE, 0, tmp_addr=t0, tmp_val=t1)
    _init_trisc0_unpack(fw)
    fw.breadcrumb(DBG_TRISC0, "trisc0:0x1001")
  elif trisc_id == 1:
    fw.breadcrumb(DBG_TRISC1, "trisc1:0x1100")
    _init_trisc1_math(fw)
    fw.breadcrumb(DBG_TRISC1, "trisc1:0x1101")
  else:
    fw.breadcrumb(DBG_TRISC2, "trisc2:0x1200")
    _init_trisc2_pack(fw)
    fw.breadcrumb(DBG_TRISC2, "trisc2:0x1201")

  fw.write32(SYNC_TRISC_INIT + trisc_id * 4, 1, tmp_addr=t0, tmp_val=t1)
  _debug_sync(fw, SYNC_TRISC_INIT + trisc_id * 4, t1)
  fw.fence()
  if trisc_id == 0:
    fw.breadcrumb(DBG_TRISC0, "trisc0:0x1002")
  elif trisc_id == 1:
    fw.breadcrumb(DBG_TRISC1, "trisc1:0x1102")
  else:
    fw.breadcrumb(DBG_TRISC2, "trisc2:0x1202")

  fw.li(t1, 1)
  for init_id in range(3):
    _wait_sync_value(fw, SYNC_TRISC_INIT + init_id * 4, t1, actual=t2)
  if trisc_id == 1:
    fw.breadcrumb(DBG_TRISC1, "trisc1:0x2100")
    _trace_stage(fw, TRACE_TRISC1, "trisc1.wait_trisc0_unpack_done", 0x40)
    fw.li(t2, 1)
    _wait_sync_value(fw, SYNC_DONE0, t2)
    fw.breadcrumb(DBG_TRISC1, "trisc1:0x2102")
    fw.write32(TensixRegs.INSTRN_BUF_BASE, 0xB2010000, tmp_addr=t0, tmp_val=t1)
    _trace_stage(fw, TRACE_TRISC1, "trisc1.direct_mova2d_srca_to_dst", 0x41)
    _push_tensix(fw, TTSETRWC(0, 0, 0, 0, 0, 15))
    _push_tensix(fw, TTSTALLWAIT(0x40, 0x80))
    _write_tensix_instr_word(fw, TTMOVA2D(dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0))
    _push_tensix(fw, TTSTALLWAIT(0x40, 0x10))
    _trace_stage(fw, TRACE_TRISC1, "trisc1.direct_mova2d_done", 0x42)
    _trace_stage(fw, TRACE_TRISC1, "trisc1.sfpu_add1_one_iter", 0x43)
    _sfpu_add1_one_iteration(fw)
    _trace_stage(fw, TRACE_TRISC1, "trisc1.sfpu_add1_one_iter_done", 0x44)
    _write_tensix_instr_word(fw, TTSETRWC(0, 0, 0, 0, 0, 4))
    _write_tensix_instr_word(fw, TTSTALLWAIT(2, 2064))
    _push_tensix(fw, TTSEMPOST(2))
    _trace_stage(fw, TRACE_TRISC1, "trisc1.math_pack_sem_posted", 0x45)
    _signal_sync(fw, SYNC_DONE1, t2)
    _debug_sync(fw, SYNC_DONE1, t2)
    fw.breadcrumb(DBG_TRISC1, "trisc1:0x2104")
    _ret_kernel(fw)
    return fw

  if trisc_id == 2:
    fw.breadcrumb(DBG_TRISC2, "trisc2:0x2200")
    _trace_stage(fw, TRACE_TRISC2, "trisc2.wait_math_pack_sem", 0x60)
    _push_tensix(fw, TTSEMWAIT(1, 2, 1))
    _trace_stage(fw, TRACE_TRISC2, "trisc2.reserve_cb16", 0x61)
    _cb_reserve_back(fw, data["cb_interface"], 16)
    fw.breadcrumb(DBG_TRISC2, "trisc2:0x2203")
    _cb_write_ptr(fw, data["cb_interface"], 16, out=s0)
    fw.debug_write(DBG_TRISC2_PACK_PTR_16B, s0, name="trisc2_cb16_write_ptr_16b", tmp_addr=t0, tmp_val=t1)
    fw.slli(t4, s0, 4)
    fw.debug_write(DBG_TRISC2_PACK_PTR_BYTES, t4, name="trisc2_cb16_write_ptr_bytes", tmp_addr=t0, tmp_val=t1)
    _write_repeated_words_at_reg(fw, t4, 0xA5C31610, 32, tmp=t1)
    fw.addi(s0, s0, -1)
    fw.debug_write(DBG_TRISC2_PACK_ADDR_MINUS_ONE, s0, name="trisc2_pack_addr_minus_one_16b", tmp_addr=t0, tmp_val=t1)
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
    if not DEBUG_SKIP_PACK_MOP:
      _push_tensix(fw, TTMOP(1, 0, 0))
    _trace_stage(fw, TRACE_TRISC2, "trisc2.pack_direct_done", 0x62)
    _push_tensix(fw, TTSETADCZW(4, 0, 0, 0, 0, 5))
    _cb_push_back(fw, data["cb_interface"], 16)
    # OLD 6e7c..6e8c: push SYNC_TILES_RECEIVED[CB16] via Tensix.
    # DMAREG[48] := received_count from local CB16 state, then
    # TTSTOREREG(TdmaDataRegIndex=24, RegAddr=0x1600A) writes the 32-bit GPR
    # pair {DMAREG[48],DMAREG[49]} to L1 0xFFB58028 = SYNC_TILES_RECEIVED_BASE
    # + 16 * SYNC_STRIDE.
    _cb_iface(fw, data["cb_interface"], 16, out=t6)
    fw.lw(t1, t6, 24)
    _cb_counter_high(fw, t1, t1)
    fw.slli(t1, t1, 8)
    fw.li(t2, TTSETDMAREG(0, 0, 0, 48).raw_word())
    fw.add(t1, t1, t2)
    fw.write32(TensixRegs.INSTRN_BUF_BASE, t1, tmp_addr=t0)
    _push_tensix(fw, TTSTALLWAIT(32, 8))
    _write_tensix_instr_word(fw, 0x6761600A)  # TTSTOREREG(24, 0x1600A)
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
    _trace_stage(fw, TRACE_TRISC2, "trisc2.cb16_ready", 0x63)
    fw.li(t2, 1)
    _signal_sync(fw, SYNC_DONE2, t2)
    _debug_sync(fw, SYNC_DONE2, t2)
    fw.breadcrumb(DBG_TRISC2, "trisc2:0x2205")
    _ret_kernel(fw)
    return fw

  fw.li(s5, 0)
  fw.label("trisc_loop")
  fw.beq(s5, s3, "trisc_done")
  fw.addi(t2, s5, 1)

  fw.breadcrumb(DBG_TRISC0, "trisc0:0x2000")
  _trace_stage(fw, TRACE_TRISC0, "trisc0.wait_cb0", 0x20)
  _cb_wait_front(fw, data["cb_interface"], 0)
  fw.breadcrumb(DBG_TRISC0, "trisc0:0x2001")
  _cb_read_ptr(fw, data["cb_interface"], 0, out=s0)
  fw.debug_write(DBG_SEMS0, s0, name="trisc0_cb_read_ptr", tmp_addr=t0, tmp_val=t1)
  _cb_iface(fw, data["cb_interface"], 0, out=t6)
  fw.lw(t1, t6, 8)
  fw.debug_write(DBG_SEMS1, t1, name="trisc0_cb_read_limit", tmp_addr=t0, tmp_val=t2)
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
  fw.breadcrumb(DBG_TRISC0, "trisc0:0x2002")

  fw.read32(t1, TRISC0_UNP_CFG_CONTEXT, tmp_addr=t0)
  fw.li(t2, TensixRegs.CFG_BASE + 76 * 4)
  fw.beq(t1, zero, "trisc0_cfg_addr")
  fw.li(t2, TensixRegs.CFG_BASE + 0x380 + 77 * 4)
  fw.label("trisc0_cfg_addr")
  fw.sw(s0, t2, 0)
  fw.lw(t1, t2, 0)
  fw.debug_write(DBG_SEMS2, t1, name="trisc0_unpack_cfg_ptr", tmp_addr=t0, tmp_val=t3)
  fw.write32(TENSIX_PC_UNPACK_SYNC, 0, tmp_addr=t0, tmp_val=t1)

  _push_tensix(fw, TTSTALLWAIT(8, 1024))
  _trace_stage(fw, TRACE_TRISC0, "trisc0.direct_unpack_cb0_to_srca", 0x21)
  for inst in UNPACK_DIRECT_WORDS:
    _write_tensix_instr_word(fw, inst)
  fw.breadcrumb(DBG_TRISC0, "trisc0:0x2003")
  _push_tensix(fw, TTSEMGET(32))
  _trace_stage(fw, TRACE_TRISC0, "trisc0.unpack_done", 0x22)

  fw.breadcrumb(DBG_TRISC0, "trisc0:0x2005")
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
  fw.breadcrumb(DBG_TRISC0, "trisc0:0x2006")
  _cb_pop_front(fw, data["cb_interface"], 0, tensix_ack=True)
  _trace_stage(fw, TRACE_TRISC0, "trisc0.cb0_popped", 0x23)
  fw.breadcrumb(DBG_TRISC0, "trisc0:0x2007")
  fw.addi(t2, s5, 1)
  _signal_sync(fw, SYNC_DONE0, t2)
  _debug_sync(fw, SYNC_DONE0, t2)
  fw.breadcrumb(DBG_TRISC0, "trisc0:0x2004")

  fw.addi(s5, s5, 1)
  fw.j("trisc_loop")
  fw.label("trisc_done")
  if trisc_id == 0:
    fw.breadcrumb(DBG_TRISC0, "trisc0:0x20FF")
  else:
    fw.breadcrumb(DBG_TRISC1, "trisc1:0x21FF")
  _ret_kernel(fw)
  return fw


def build_program(src_addr: int, dst_addr: int, num_banks: int) -> Program:
  tiles_per_core = TILES_PER_CORE

  def brisc_rtas(_x: int, _y: int) -> list[int]:
    return [src_addr, 0, tiles_per_core, num_banks]

  def ncrisc_rtas(_x: int, _y: int) -> list[int]:
    return [dst_addr, 0, tiles_per_core, num_banks]

  def trisc_rtas(_x: int, _y: int) -> list[int]:
    return [tiles_per_core]

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
    cbs=[(0, TILE_BYTES, CB_DEPTH), (16, TILE_BYTES, CB_DEPTH)],
    grid=((TARGET_CORE[1],), (TARGET_CORE[0],)),
  )
  prog.name = "add1"
  return prog


def main():
  device = Device()
  try:
    print_n = 8
    n_tiles = TILES_PER_CORE

    src_rm = _seed_src_tensor(n_tiles)
    src_buf = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="src")
    dst_buf = device.dram.alloc(n_tiles, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="dst")
    num_banks = len(device.dram.bank_tiles)
    prog = build_program(src_buf.addr, dst_buf.addr, num_banks)
    timings = []
    try:
      timings = device.run(prog)
    except TimeoutError:
      _print_l1_mailbox(device, TARGET_CORE, "target core mailbox after timeout:")
      _print_cb_sync_probes(device, TARGET_CORE, "after timeout")
      _print_trisc2_pack_debug(device, TARGET_CORE, "after timeout")
      _print_l1_words_probe(device, TARGET_CORE, SCRATCH_L1, "cb0 page0 first 128B after timeout")
      _print_l1_words_probe(device, TARGET_CORE, SCRATCH_L1 + TILE_BYTES * CB_DEPTH, "cb16 page0 first 128B after timeout")
      dst_rows = _read_dst_debug_array_words(device, TARGET_CORE, rows=16)
      _print_dst_debug_rows("dst debug-array rows 0..15 after timeout:", dst_rows)
      _print_cb_interface_probe(device, TARGET_CORE, TM.DATA_COMMON["cb_interface"], 16, "after timeout")
      raise
      out = device.dram_read(dst_buf)
      exp = _expected_add1(src_rm)
      print("device.run timed out; dumping partial DRAM output before exit")
      print(f"input first {print_n}: {_format_bf16_ints(src_rm, print_n)}")
      print(f"output first {print_n}: {_format_bf16_ints(out, print_n)}")
      print(f"expect first {print_n}: {_format_bf16_ints(exp, print_n)}")
      _print_tile_faces("input tile0 faces:", src_rm)
      _print_tile_faces("output tile0 faces:", out)
      _print_tile_faces("expect tile0 faces:", exp)
      dst_rows = _read_dst_debug_array_words(device, TARGET_CORE, rows=64)
      _print_dst_debug_rows("dst debug-array rows 0..63:", dst_rows)
      raise
    dst_rows = _read_dst_debug_array_words(device, TARGET_CORE, rows=64)
    _print_dst_debug_rows("dst debug-array rows 0..63:", dst_rows)
    _print_l1_tile_probe(device, TARGET_CORE, SCRATCH_L1, "cb0 page0 after run")
    _print_l1_tile_probe(device, TARGET_CORE, SCRATCH_L1 + TILE_BYTES * CB_DEPTH, "cb16 page0 after run")
    out = device.dram_read(dst_buf)
    exp = _expected_add1(src_rm)
    mismatch = _first_mismatch(out, exp)

    print(f"input first {print_n}: {_format_bf16_ints(src_rm, print_n)}")
    print(f"output first {print_n}: {_format_bf16_ints(out, print_n)}")
    print(f"expect first {print_n}: {_format_bf16_ints(exp, print_n)}")
    if mismatch is None:
      print(f"PASS add1 {n_tiles} tile on core {TARGET_CORE}")
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
