#!/usr/bin/env python3
"""Dump SFPU LRegs with a TRISC1-only kernel.

Path:
  1. TRISC1 initializes math/SFPU state.
  2. The kernel seeds L0..L7.
  3. SFPSTORE writes each LReg into a 4-row logical Dest band.
  4. TRISC1 reads Dest through DBG_ARRAY_RD_* and stores raw rows to L1.
  5. The host reads and decodes that L1 window.

This avoids add1 dataflow, pack, CBs, NOC, and DRAM. It is a semantic/debug
probe for LReg contents and the SFPSTORE/Dest footprint, not a timing bench.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import numpy as np

from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  TTNOP,
  TTSETRWC,
  TTSTALLWAIT,
  TTSFPLOADI,
  TTSFPNOP,
  TTSFPSTORE,
  s2,
  t0,
  t1,
  zero,
)
from program import Dtype, Program  # noqa: E402
from ttk.math import Math  # noqa: E402
from ttk.sfpu import sfpu_load_fp32_const  # noqa: E402
from ttk.tensix import MopCfg, Tensix, TensixMMIO, TensixStall, TensixWait  # noqa: E402


RESULT_BASE = 0x12D000
READBACK_BASE = RESULT_BASE + 0x100
RESULT_MAGIC = 0x4C524748  # "HGRL"
STATUS_STARTED = 0x17E60001
STATUS_DONE = 0x17E6D00D
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4

LREGS = 8
LANES = 32
ROWS_PER_LREG = 4
DEST_ROWS = LREGS * ROWS_PER_LREG
READBACK_ROWS = 64
READBACK32_ROWS = 16
DEST_ROW_WORDS = 8
DEST_ROW_BYTES = DEST_ROW_WORDS * 4
READBACK_SLOT_BYTES = READBACK_ROWS * DEST_ROW_BYTES
READBACK32_SLOT_BYTES = READBACK32_ROWS * DEST_ROW_BYTES
MAX_READBACK_BYTES = max(READBACK_SLOT_BYTES, LREGS * READBACK32_SLOT_BYTES)

SFPU_FMT_BF16 = 2
SFPU_FMT_BOB32 = 4
SFPU_FMT_RAW32 = 7
FORMAT_CHOICES = ("bf16", "bob32", "raw32")
RAWBITS_VALUES = (
  0x00000000,
  0x3F800000,
  0xBF800000,
  0x12345678,
  0xDEADBEEF,
  0x80000001,
  0x7FC01234,
  0xCAFEBABE,
)
ADDR_MOD = 7
DBG_ARRAY_ID_DEST = 2
RISCV_DEBUG_REG_DBG_ARRAY_RD_EN = 0xFFB12060
RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD = 0xFFB12064
RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA = 0xFFB1206C

NOOP_MOP_CFG = MopCfg(loop_outer=1, loop_inner=1, template=[TTNOP()])
DEFAULT_RAW_LOAD_GAP = 1


class LregDumpKernel(KernelBase, Tensix):
  pass


def bf16_bits(value: float) -> int:
  word = struct.unpack("<I", struct.pack("<f", float(value)))[0]
  return (word >> 16) & 0xFFFF


def bf16_to_f32(bits: np.ndarray) -> np.ndarray:
  return (bits.astype("<u4") << 16).view("<f4")


def dst_decode_bf16(encoded: np.ndarray) -> np.ndarray:
  """Decode Dest's 16-bit internal BF16 layout into ordinary BF16 bits."""
  x = encoded.astype("<u2")
  exp = x & np.uint16(0x00FF)
  man = (x >> np.uint16(8)) & np.uint16(0x007F)
  sign = x & np.uint16(0x8000)
  return (sign | (exp << np.uint16(7)) | man).astype("<u2")


def dst32b_adjust_row(row: int) -> int:
  return ((row & 0x1F8) << 1) | (row & 0x207)


def dst_decode_fp32(encoded: np.ndarray) -> np.ndarray:
  x = encoded.astype("<u4")
  hi = dst_decode_bf16((x >> np.uint32(16)).astype("<u2")).astype("<u4")
  lo = x & np.uint32(0xFFFF)
  return ((hi << np.uint32(16)) | lo).astype("<u4")


def fp32_from_bits(bits: np.ndarray) -> np.ndarray:
  return bits.astype("<u4").view("<f4")


def sfpu_fmt_value(fmt: str) -> int:
  if fmt == "bf16":
    return SFPU_FMT_BF16
  if fmt == "bob32":
    return SFPU_FMT_BOB32
  if fmt == "raw32":
    return SFPU_FMT_RAW32
  raise ValueError(fmt)


def readback_bytes_for_fmt(fmt: str) -> int:
  return READBACK_SLOT_BYTES if fmt == "bf16" else LREGS * READBACK32_SLOT_BYTES


def readback_rows_for_fmt(fmt: str) -> int:
  return READBACK_ROWS if fmt == "bf16" else READBACK32_ROWS


def readback_slot_bytes_for_fmt(fmt: str) -> int:
  return READBACK_SLOT_BYTES if fmt == "bf16" else READBACK32_SLOT_BYTES


def debug_ranges() -> tuple[tuple[int, int], ...]:
  return (
    (RESULT_BASE, HEADER_SIZE),
    (READBACK_BASE, MAX_READBACK_BYTES),
  )


def emit_header(
  fw: KernelBase, *, status: int, readback_bytes: int, readback_rows: int, readback_slots: int
):
  values = (
    RESULT_MAGIC,
    1,
    status,
    READBACK_BASE,
    readback_bytes,
    readback_rows,
    DEST_ROW_BYTES,
    LREGS,
    LANES,
    readback_slots,
    0,
    0,
    0,
    0,
    0,
    0,
  )
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  return fw


def emit_drain(fw: LregDumpKernel):
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.SFPU))
  return fw.tensix_sync(1, tmp=t1)


def emit_sfpu_nops(fw: LregDumpKernel, count: int):
  for _ in range(count):
    fw.emit(TTSFPNOP())
  return fw


def emit_seed_lregs(fw: LregDumpKernel, setup: str, *, raw_load_gap: int):
  if setup == "constants":
    for lreg in range(LREGS):
      sfpu_load_fp32_const(fw, lreg, float(lreg))
    return fw
  if setup == "sentinels":
    values = (0.0, 1.0, -1.0, 2.0, 0.5, -0.5, 16.0, -16.0)
    for lreg, value in enumerate(values):
      sfpu_load_fp32_const(fw, lreg, value)
    return fw
  if setup == "rawbits":
    for lreg, value in enumerate(RAWBITS_VALUES):
      fw.emit(TTSFPLOADI(lreg, 8, value >> 16))
      emit_sfpu_nops(fw, raw_load_gap)
      fw.emit(TTSFPLOADI(lreg, 10, value & 0xFFFF))
      emit_sfpu_nops(fw, raw_load_gap)
    return fw
  raise ValueError(setup)


def emit_store_lregs_to_dest(fw: LregDumpKernel, *, sfpu_fmt: int = SFPU_FMT_BF16, addr_mod: int = ADDR_MOD):
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))
  for lreg in range(LREGS):
    fw.emit(TTSFPSTORE(lreg, sfpu_fmt, addr_mod, lreg * ROWS_PER_LREG))
  fw.emit(TTSFPNOP())
  return emit_drain(fw)


def emit_store_lreg_to_dest0(fw: LregDumpKernel, lreg: int, *, sfpu_fmt: int, addr_mod: int = ADDR_MOD):
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))
  fw.emit(TTSFPSTORE(lreg, sfpu_fmt, addr_mod, 0))
  fw.emit(TTSFPNOP())
  return emit_drain(fw)


def emit_dest_to_l1_readback(fw: LregDumpKernel, *, base: int = READBACK_BASE, rows: int = READBACK_ROWS):
  fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_EN, 1)
  for row in range(rows):
    for sel in range(DEST_ROW_WORDS):
      cmd = (DBG_ARRAY_ID_DEST << 16) | (sel << 12) | row
      fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD, cmd)
      fw.delay_cycles(5)
      fw.read32(t1, RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA)
      fw.write32(base + row * DEST_ROW_BYTES + sel * 4, t1)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD, 0)
  fw.write32(RISCV_DEBUG_REG_DBG_ARRAY_RD_EN, 0)
  return fw.write32(TensixMMIO.RISCV_DEBUG_REG_DEST_CG_CTRL, 0)


def build_kernel(*, setup: str, fmt: str, raw_load_gap: int) -> LregDumpKernel:
  fw = LregDumpKernel()
  fw.math = Math(fw)
  fw.data = {"dest_offset_id": 0xFFB00080}
  readback_bytes = readback_bytes_for_fmt(fmt)
  readback_rows = readback_rows_for_fmt(fmt)
  readback_slot_bytes = readback_slot_bytes_for_fmt(fmt)
  readback_slots = 1 if fmt == "bf16" else LREGS

  emit_header(
    fw,
    status=STATUS_STARTED,
    readback_bytes=readback_bytes,
    readback_rows=readback_rows,
    readback_slots=readback_slots,
  )
  fw.write32(fw.data["dest_offset_id"], 0)
  fw.math.init(dtype=Dtype.Float16_b, mop_cfg=NOOP_MOP_CFG)
  emit_drain(fw)
  emit_seed_lregs(fw, setup, raw_load_gap=raw_load_gap)
  sfpu_fmt = sfpu_fmt_value(fmt)
  if fmt == "bf16":
    emit_store_lregs_to_dest(fw, sfpu_fmt=sfpu_fmt)
    emit_dest_to_l1_readback(fw, rows=readback_rows)
  else:
    for lreg in range(LREGS):
      emit_store_lreg_to_dest0(fw, lreg, sfpu_fmt=sfpu_fmt)
      emit_dest_to_l1_readback(fw, base=READBACK_BASE + lreg * readback_slot_bytes, rows=readback_rows)
  emit_header(
    fw,
    status=STATUS_DONE,
    readback_bytes=readback_bytes,
    readback_rows=readback_rows,
    readback_slots=readback_slots,
  )
  return fw.ret()


def build_program(*, setup: str, fmt: str, raw_load_gap: int = DEFAULT_RAW_LOAD_GAP) -> Program:
  empty = KernelBase()
  prog = Program(
    brisc=empty,
    ncrisc=empty,
    trisc0=empty,
    trisc1=build_kernel(setup=setup, fmt=fmt, raw_load_gap=raw_load_gap),
    trisc2=empty,
    num_cores=1,
  )
  prog.name = f"microbench_sfpu_lreg_dump:{setup}:{fmt}"
  return prog


def clear_results(device: Device, core: tuple[int, int]):
  harness.clear_window(device, core, debug_ranges())


def read_results(device: Device, core: tuple[int, int]) -> tuple[bytes, bytes]:
  header = harness.read_window(device, core, RESULT_BASE, HEADER_SIZE)
  words = struct.unpack("<" + "I" * HEADER_WORDS, header)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{words[0]:08x}")
  if words[2] != STATUS_DONE:
    raise RuntimeError(f"kernel did not finish, status=0x{words[2]:08x}")
  raw = harness.read_window(device, core, READBACK_BASE, words[4])
  return header, raw


def run_dump(device: Device, *, setup: str, fmt: str, raw_load_gap: int, core: tuple[int, int]) -> bytes:
  clear_results(device, core)
  device.run(build_program(setup=setup, fmt=fmt, raw_load_gap=raw_load_gap))
  _, raw = read_results(device, core)
  return raw


def decode_lreg_lanes(raw: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
  words = np.frombuffer(raw, dtype="<u4").reshape(READBACK_ROWS, DEST_ROW_WORDS)
  halfwords = words.view("<u2").reshape(READBACK_ROWS, DEST_ROW_WORDS * 2)
  encoded = np.empty((LREGS, LANES), dtype="<u2")
  for lreg in range(LREGS):
    base = lreg * ROWS_PER_LREG
    for lane in range(LANES):
      row = base + lane // 8
      col = (lane & 7) * 2
      encoded[lreg, lane] = halfwords[row, col]
  bits = dst_decode_bf16(encoded)
  return encoded, bits, bf16_to_f32(bits)


def decode_lreg_lanes32(raw: bytes, *, fmt: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
  encoded = np.empty((LREGS, LANES), dtype="<u4")
  for lreg in range(LREGS):
    slot = raw[lreg * READBACK32_SLOT_BYTES : (lreg + 1) * READBACK32_SLOT_BYTES]
    words = np.frombuffer(slot, dtype="<u4").reshape(READBACK32_ROWS, DEST_ROW_WORDS)
    halfwords = words.view("<u2").reshape(READBACK32_ROWS, DEST_ROW_WORDS * 2)
    for lane in range(LANES):
      logical_row = lane // 8
      row = dst32b_adjust_row(logical_row)
      col = (lane & 7) * 2
      hi = np.uint32(halfwords[row, col])
      lo = np.uint32(halfwords[row + 8, col])
      encoded[lreg, lane] = (hi << np.uint32(16)) | lo
  bits = dst_decode_fp32(encoded) if fmt == "bob32" else encoded
  return encoded, bits, fp32_from_bits(bits)


def print_dump(raw: bytes, *, setup: str, fmt: str, full: bool, rows: bool):
  shown = LANES if full else 8
  print("SFPU LReg dump")
  print(f"  path=TRISC1 SFPSTORE({fmt})->Dest->L1 lanes=32")
  if fmt == "bf16":
    encoded, bits, vals = decode_lreg_lanes(raw)
    for lreg in range(LREGS):
      val_text = ", ".join(f"{float(v):.7g}" for v in vals[lreg, :shown])
      bit_text = ", ".join(f"{int(b):04x}" for b in bits[lreg, :shown])
      dst_text = ", ".join(f"{int(b):04x}" for b in encoded[lreg, :shown])
      suffix = "" if full else ", ..."
      print(f"L{lreg}: values=[{val_text}{suffix}] bf16=[{bit_text}{suffix}] dst16=[{dst_text}{suffix}]")
  else:
    encoded, bits, vals = decode_lreg_lanes32(raw, fmt=fmt)
    if setup == "rawbits":
      expected = np.array(RAWBITS_VALUES, dtype="<u4")[:, None]
      decoded_ok = bool(np.all(bits == expected))
      print(f"  decoded_u32_match_rawbits={decoded_ok}")
      group_ok = [bool(np.all(bits[:, group * 8 : (group + 1) * 8] == expected)) for group in range(4)]
      print(f"  decoded_u32_match_rawbits_by_lane8={group_ok}")
      if fmt == "raw32":
        raw_ok = bool(np.all(encoded == expected))
        print(f"  raw_dst32_match_rawbits={raw_ok}")
        raw_group_ok = [
          bool(np.all(encoded[:, group * 8 : (group + 1) * 8] == expected)) for group in range(4)
        ]
        print(f"  raw_dst32_match_rawbits_by_lane8={raw_group_ok}")
    for lreg in range(LREGS):
      val_text = ", ".join(f"{float(v):.7g}" for v in vals[lreg, :shown])
      bit_text = ", ".join(f"{int(b):08x}" for b in bits[lreg, :shown])
      dst_text = ", ".join(f"{int(b):08x}" for b in encoded[lreg, :shown])
      suffix = "" if full else ", ..."
      label = "dst32" if fmt == "bob32" else "raw_dst32"
      print(f"L{lreg}: f32=[{val_text}{suffix}] u32=[{bit_text}{suffix}] {label}=[{dst_text}{suffix}]")
  if rows:
    print("Raw Dest rows as u32:")
    slots = 1 if fmt == "bf16" else LREGS
    slot_rows = readback_rows_for_fmt(fmt)
    slot_bytes = readback_slot_bytes_for_fmt(fmt)
    for slot_id in range(slots):
      slot = raw[slot_id * slot_bytes : (slot_id + 1) * slot_bytes]
      words = np.frombuffer(slot, dtype="<u4").reshape(slot_rows, DEST_ROW_WORDS)
      if slots > 1:
        print(f"slot L{slot_id}:")
      for row, row_words in enumerate(words):
        word_text = " ".join(f"{int(w):08x}" for w in row_words)
        print(f"row {row:02d}: {word_text}")


def build_only(setup: str, fmt: str, raw_load_gap: int):
  prog = build_program(setup=setup, fmt=fmt, raw_load_gap=raw_load_gap)
  trisc1_bytes = sum(len(seg.data) for seg in prog.trisc1.compile())
  print(
    f"build ok: setup={setup} fmt={fmt} raw_load_gap={raw_load_gap} "
    f"trisc1_bytes={trisc1_bytes} readback_bytes={readback_bytes_for_fmt(fmt)}"
  )


def main() -> int:
  parser = argparse.ArgumentParser(description="Dump SFPU LRegs with a TRISC1-only kernel.")
  parser.add_argument("--setup", choices=("constants", "sentinels", "rawbits"), default="constants")
  parser.add_argument("--fmt", choices=FORMAT_CHOICES, default="bf16")
  parser.add_argument("--core", type=harness.parse_core, default=None)
  parser.add_argument("--full", action="store_true", help="print all 32 lanes per LReg")
  parser.add_argument("--rows", action="store_true", help="also print raw Dest rows as u32 words")
  parser.add_argument("--raw-load-gap", type=int, default=DEFAULT_RAW_LOAD_GAP)
  parser.add_argument("--build-only", action="store_true")
  args = parser.parse_args()

  if args.build_only:
    build_only(args.setup, args.fmt, args.raw_load_gap)
    return 0

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    raw = run_dump(device, setup=args.setup, fmt=args.fmt, raw_load_gap=args.raw_load_gap, core=core)
  print_dump(raw, setup=args.setup, fmt=args.fmt, full=args.full, rows=args.rows)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
