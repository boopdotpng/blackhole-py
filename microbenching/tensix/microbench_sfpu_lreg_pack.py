#!/usr/bin/env python3
"""Dump SFPU LRegs through the real packer path.

This is the complement to microbench_sfpu_lreg_dump.py's debug-array path:

  TRISC1: seed L0..L7 -> SFPSTORE into Dest
  TRISC2: PACK Dest into CB16/L1
  host:   read CB16 payload and untilize the 32x32 tile

The point is to avoid DBG_ARRAY_RD readback, which does not round-trip every
32-bit Dest datum. The first target is raw sentinel preservation.
"""

from __future__ import annotations

import argparse
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import numpy as np

from asm import KernelBase  # noqa: E402
from device import Device  # noqa: E402
from dram import untilize  # noqa: E402
from dsl import (  # noqa: E402
  TTATGETM,
  TTATRELM,
  TTDMANOP,
  TTMOP,
  TTNOP,
  TTPACR,
  TTRMWCIB3,
  TTSETADC,
  TTSETADCZW,
  TTSETDMAREG,
  TTSETRWC,
  TTSTALLWAIT,
  TTSFPLOADI,
  TTSFPNOP,
  TTSFPSTORE,
  TTSEMGET,
  TTSEMPOST,
  TTSEMWAIT,
  TTWRCFG,
  TTZEROACC,
  s0,
  s2,
  t0,
  t1,
  t2,
  t3,
  zero,
)
from program import Dtype, Program  # noqa: E402
from ttk import Cb, Tensix  # noqa: E402
from ttk.cb import CircularBuffer as CB  # noqa: E402
from ttk.mailbox import TriscMailbox  # noqa: E402
from ttk.math import Math  # noqa: E402
from ttk.pack import Pack  # noqa: E402
from ttk.sfpu import sfpu_load_fp32_const  # noqa: E402
from ttk.tensix import (  # noqa: E402
  Cfg,
  MopCfg,
  TensixL1,
  TensixRegs,
  TensixSem,
  TensixSemWait,
  TensixStall,
  TensixWait,
)


RESULT_BASE = 0x12D000
RESULT_MAGIC = 0x4C524750  # "PGRL"
STATUS_STARTED = 0x17E60001
STATUS_PACK_DONE = 0x17E6D00D
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4

SYNC_BASE = RESULT_BASE + 0x80
SYNC_MATH_READY = SYNC_BASE + 0x00
SYNC_PACK_READY = SYNC_BASE + 0x04
SYNC_MATH_STAGE = SYNC_BASE + 0x10
SYNC_PACK_STAGE = SYNC_BASE + 0x14

OUT_CB = 16
OUT_CB_BASE = TensixL1.DATA_BUFFER_SPACE_BASE
LREGS = 8
LANES = 32
ROWS_PER_LREG = 4
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
DEFAULT_RAW_LOAD_GAP = 1
DEFAULT_RAW_LOAD_ORDER = "upper-lower"

SFPU_STORE_MODES = {
  "fp32": 3,
  "int32": 4,
  "raw32": 7,
}
PACK_DTYPES = {
  "fp32": Dtype.Float32,
  "int32": Dtype.Int32,
  "uint32": Dtype.UInt32,
}
SETUPS = ("constants", "sentinels", "rawbits")

NOOP_MOP_CFG = MopCfg(loop_outer=1, loop_inner=1, template=[TTNOP()])
PACK_MOP_CFG = MopCfg(
  loop_outer=4,
  loop_inner=4,
  template=[
    TTNOP(),
    TTNOP(),
    TTNOP(),
    TTPACR(),
    TTNOP(),
    TTPACR(AddrMode=1, Last=1),
    TTPACR(AddrMode=2),
  ],
)


class MathKernel(KernelBase, Tensix):
  pass


class PackKernel(KernelBase, Tensix, Cb):
  pass


def emit_header(fw: KernelBase, *, status: int, tile_bytes: int, sfpu_store: str, pack_dtype: Dtype):
  values = (
    RESULT_MAGIC,
    1,
    status,
    OUT_CB_BASE,
    tile_bytes,
    LREGS,
    LANES,
    SFPU_STORE_MODES[sfpu_store],
    pack_dtype.value,
    0,
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


def emit_enable_dst32(fw: KernelBase):
  fw.emit(TTATGETM(0))
  fw.push_tensix(TTRMWCIB3(Mask=0x60, Data=0x60, CfgRegAddr=Cfg.ALU.addr32))
  fw.emit(TTATRELM(0))
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.MATH))
  fw.emit(TTZEROACC(3, 0, 0, 1, 0))
  fw.emit(TTSTALLWAIT(TensixStall.MATH, TensixWait.MATH))
  return fw


def emit_sfpu_nops(fw: KernelBase, count: int):
  for _ in range(count):
    fw.emit(TTSFPNOP())
  return fw


def emit_seed_lregs(fw: KernelBase, setup: str, *, raw_load_gap: int, raw_load_order: str):
  if setup == "constants":
    for lreg in range(LREGS):
      sfpu_load_fp32_const(fw, lreg, float(lreg))
    return fw
  if setup == "sentinels":
    for lreg, value in enumerate((0.0, 1.0, -1.0, 2.0, 0.5, -0.5, 16.0, -16.0)):
      sfpu_load_fp32_const(fw, lreg, value)
    return fw
  if setup == "rawbits":
    for lreg, value in enumerate(RAWBITS_VALUES):
      if raw_load_order == "upper-lower":
        fw.emit(TTSFPLOADI(lreg, 8, value >> 16))
        emit_sfpu_nops(fw, raw_load_gap)
        fw.emit(TTSFPLOADI(lreg, 10, value & 0xFFFF))
      elif raw_load_order == "lower-upper":
        fw.emit(TTSFPLOADI(lreg, 10, value & 0xFFFF))
        emit_sfpu_nops(fw, raw_load_gap)
        fw.emit(TTSFPLOADI(lreg, 8, value >> 16))
      else:
        raise ValueError(raw_load_order)
      emit_sfpu_nops(fw, raw_load_gap)
    return fw
  raise ValueError(setup)


def emit_store_lregs_to_dest(fw: KernelBase, *, sfpu_store: str):
  fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))
  sfpu_mod = SFPU_STORE_MODES[sfpu_store]
  for lreg in range(LREGS):
    fw.emit(TTSFPSTORE(lreg, sfpu_mod, 7, lreg * ROWS_PER_LREG))
  fw.emit(TTSFPNOP())
  fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
  return fw.tensix_sync(1, tmp=t1)


def build_trisc1(
  *, setup: str, sfpu_store: str, pack_dtype: Dtype, raw_load_gap: int, raw_load_order: str
) -> KernelBase:
  fw = MathKernel()
  fw.math = Math(fw)
  fw.data = TriscMailbox.DATA1
  emit_header(fw, status=STATUS_STARTED, tile_bytes=pack_dtype.tile_size, sfpu_store=sfpu_store, pack_dtype=pack_dtype)
  fw.write32(SYNC_MATH_READY, 0)
  fw.write32(SYNC_PACK_READY, 0)
  fw.write32(SYNC_MATH_STAGE, 0x1100)
  fw.write32(fw.data["dest_offset_id"], 0)

  fw.math.init(dtype=Dtype.Float16_b, mop_cfg=NOOP_MOP_CFG)
  fw.write32(SYNC_MATH_STAGE, 0x1110)
  emit_enable_dst32(fw)
  fw.write32(SYNC_MATH_READY, 1)
  fw.li(t2, 1)
  fw.wait_sync_value(SYNC_PACK_READY, t2, actual=t1)
  fw.write32(SYNC_MATH_STAGE, 0x1120)

  emit_seed_lregs(fw, setup, raw_load_gap=raw_load_gap, raw_load_order=raw_load_order)
  fw.write32(SYNC_MATH_STAGE, 0x1130)
  emit_store_lregs_to_dest(fw, sfpu_store=sfpu_store)
  fw.write32(SYNC_MATH_STAGE, 0x1140)
  fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_PACK)))
  fw.tensix_sync(1, tmp=t1)
  fw.write32(SYNC_MATH_STAGE, 0x1150)
  return fw.ret()


def emit_pack_one_tile(fw: PackKernel):
  fw.write32(SYNC_PACK_STAGE, 0x1230)
  fw.emit(TTSEMWAIT(
    TensixStall.TDMA,
    TensixSem.mask(TensixSem.MATH_PACK),
    TensixSemWait.STALL_ON_ZERO,
  ))
  fw.write32(SYNC_PACK_STAGE, 0x1240)
  fw.cb_reserve_back(fw.data["cb_interface"], OUT_CB)
  fw.cb_write_ptr(fw.data["cb_interface"], OUT_CB, out=s0)
  fw.addi(s0, s0, -1)
  fw.write32(SYNC_PACK_STAGE, 0x1250)

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
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON | TensixWait.PACK0))
  fw.emit(TTWRCFG(12, 0, 69))
  fw.srli(t1, s0, 16)
  fw.slli(t1, t1, 8)
  fw.li(t2, 0x45000019)
  fw.add(t1, t1, t2)
  fw.write32(TensixRegs.INSTRN_BUF_BASE, t1)
  fw.emit(TTDMANOP())

  fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC0, 0)
  fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC1, 0)
  fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC2, 0)
  fw.write32(Cfg.DEST_TARGET_REG_CFG_PACK_SEC3, 0)
  fw.emit(TTSTALLWAIT(TensixStall.CFG, TensixWait.THCON))

  fw.emit(TTMOP(1, 0, 0))
  fw.tensix_sync(2, tmp=t1)
  fw.write32(SYNC_PACK_STAGE, 0x1260)
  fw.emit(TTSETADCZW(4, 0, 0, 0, 0, 5))
  fw.cb_push_back(fw.data["cb_interface"], OUT_CB, tensix_received=True)
  fw.emit(TTSTALLWAIT(TensixStall.SYNC | TensixStall.THCON, TensixWait.PACK0))
  fw.write32(SYNC_PACK_STAGE, 0x1270)
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.MATH_PACK)))
  fw.emit(TTDMANOP())
  fw.emit(TTDMANOP())
  return fw


def build_trisc2(*, sfpu_store: str, pack_dtype: Dtype) -> KernelBase:
  fw = PackKernel()
  fw.pack = Pack(fw)
  fw.data = TriscMailbox.DATA_COMMON
  fw.write32(SYNC_PACK_STAGE, 0x1200)
  fw.pack.init(dtype=pack_dtype, out_cb=OUT_CB, mop_cfg=PACK_MOP_CFG, fp32_dest=True)
  fw.write32(SYNC_PACK_STAGE, 0x1210)
  fw.write32(SYNC_PACK_READY, 1)
  fw.li(t2, 1)
  fw.wait_sync_value(SYNC_MATH_READY, t2, actual=t1)
  fw.write32(SYNC_PACK_STAGE, 0x1220)
  emit_pack_one_tile(fw)
  emit_header(fw, status=STATUS_PACK_DONE, tile_bytes=pack_dtype.tile_size, sfpu_store=sfpu_store, pack_dtype=pack_dtype)
  return fw.ret()


def build_program(
  *, setup: str, sfpu_store: str, pack_dtype: Dtype, raw_load_gap: int, raw_load_order: str
) -> Program:
  empty = KernelBase().ret()
  prog = Program(
    brisc=empty,
    ncrisc=empty,
    trisc0=empty,
    trisc1=build_trisc1(
      setup=setup,
      sfpu_store=sfpu_store,
      pack_dtype=pack_dtype,
      raw_load_gap=raw_load_gap,
      raw_load_order=raw_load_order,
    ),
    trisc2=build_trisc2(sfpu_store=sfpu_store, pack_dtype=pack_dtype),
    cbs=[(OUT_CB, pack_dtype.tile_size, 2)],
    semaphores=2,
    num_cores=1,
  )
  prog.name = f"microbench_sfpu_lreg_pack:{setup}:{sfpu_store}:{pack_dtype.name}"
  return prog


def clear_results(device: Device, core: tuple[int, int], *, tile_bytes: int):
  harness.clear_window(device, core, (
    (RESULT_BASE, 0x100),
    (OUT_CB_BASE, tile_bytes * 2),
  ))


def wait_and_read(device: Device, core: tuple[int, int], *, tile_bytes: int, timeout_s: float) -> tuple[bytes, bytes]:
  deadline = time.perf_counter() + timeout_s
  with harness.device_window(device, core) as win:
    while True:
      header = win.read(RESULT_BASE, HEADER_SIZE)
      words = struct.unpack("<" + "I" * HEADER_WORDS, header)
      if words[0] == RESULT_MAGIC and words[2] == STATUS_PACK_DONE:
        tile = win.read(OUT_CB_BASE, tile_bytes)
        return header, tile
      if time.perf_counter() > deadline:
        raise TimeoutError(f"timeout waiting for pack status; magic=0x{words[0]:08x} status=0x{words[2]:08x}")
      time.sleep(0.001)


def run_pack_dump(
  device: Device,
  *,
  setup: str,
  sfpu_store: str,
  pack_dtype: Dtype,
  raw_load_gap: int,
  raw_load_order: str,
  core: tuple[int, int],
  timeout_s: float,
) -> bytes:
  clear_results(device, core, tile_bytes=pack_dtype.tile_size)
  try:
    device.run(build_program(
      setup=setup,
      sfpu_store=sfpu_store,
      pack_dtype=pack_dtype,
      raw_load_gap=raw_load_gap,
      raw_load_order=raw_load_order,
    ))
  except TimeoutError:
    diag = harness.read_window(device, core, RESULT_BASE, 0xA0)
    words = struct.unpack("<" + "I" * (len(diag) // 4), diag)
    print(
      "timeout_diag "
      f"magic=0x{words[0]:08x} status=0x{words[2]:08x} "
      f"math_ready=0x{words[0x80 // 4]:08x} pack_ready=0x{words[0x84 // 4]:08x} "
      f"math_stage=0x{words[0x90 // 4]:08x} pack_stage=0x{words[0x94 // 4]:08x}",
      file=sys.stderr,
    )
    raise
  _, tile = wait_and_read(device, core, tile_bytes=pack_dtype.tile_size, timeout_s=timeout_s)
  return tile


def untilize_words(tile: bytes, dtype: Dtype) -> np.ndarray:
  raw = untilize(tile, dtype.bpe, (32, 32))
  return np.frombuffer(raw, dtype="<u4").reshape(32, 32)


def expected_rawbits_tile() -> np.ndarray:
  expected = np.zeros((32, 32), dtype="<u4")
  for lreg, value in enumerate(RAWBITS_VALUES):
    expected[lreg * ROWS_PER_LREG : (lreg + 1) * ROWS_PER_LREG, :] = np.uint32(value)
  return expected


def print_pack_dump(tile: bytes, *, setup: str, sfpu_store: str, pack_dtype: Dtype, full: bool):
  words = untilize_words(tile, pack_dtype)
  shown_cols = 32 if full else 8
  print("SFPU LReg pack dump")
  print(f"  path=SFPSTORE({sfpu_store})->Dest->PACK({pack_dtype.name})->CB16/L1")
  print(f"  tile_bytes={len(tile)} untilized_shape=32x32")
  if setup == "rawbits" and pack_dtype in (Dtype.Int32, Dtype.UInt32):
    expected = expected_rawbits_tile()
    match = words == expected
    print(f"  rawbits_match={bool(np.all(match))}")
    print(f"  rawbits_match_by_lreg={[bool(np.all(match[i * ROWS_PER_LREG : (i + 1) * ROWS_PER_LREG, :])) for i in range(LREGS)]}")
  for row in range(32 if full else LREGS * ROWS_PER_LREG):
    row_text = " ".join(f"{int(x):08x}" for x in words[row, :shown_cols])
    suffix = "" if full else " ..."
    print(f"row {row:02d}: {row_text}{suffix}")


def build_only(setup: str, sfpu_store: str, pack_dtype: Dtype, raw_load_gap: int, raw_load_order: str):
  prog = build_program(
    setup=setup,
    sfpu_store=sfpu_store,
    pack_dtype=pack_dtype,
    raw_load_gap=raw_load_gap,
    raw_load_order=raw_load_order,
  )
  trisc1_bytes = sum(len(seg.data) for seg in prog.trisc1.compile())
  trisc2_bytes = sum(len(seg.data) for seg in prog.trisc2.compile())
  print(
    f"build ok: setup={setup} sfpu_store={sfpu_store} pack_dtype={pack_dtype.name} "
    f"raw_load_gap={raw_load_gap} raw_load_order={raw_load_order} "
    f"trisc1_bytes={trisc1_bytes} trisc2_bytes={trisc2_bytes} "
    f"tile_bytes={pack_dtype.tile_size}"
  )


def main() -> int:
  parser = argparse.ArgumentParser(description="Dump SFPU LRegs through Dest->PACK->CB16/L1.")
  parser.add_argument("--setup", choices=SETUPS, default="rawbits")
  parser.add_argument("--sfpu-store", choices=tuple(SFPU_STORE_MODES), default="raw32")
  parser.add_argument("--pack-dtype", choices=tuple(PACK_DTYPES), default="int32")
  parser.add_argument("--raw-load-gap", type=int, default=DEFAULT_RAW_LOAD_GAP)
  parser.add_argument("--raw-load-order", choices=("upper-lower", "lower-upper"), default=DEFAULT_RAW_LOAD_ORDER)
  parser.add_argument("--core", type=harness.parse_core, default=None)
  parser.add_argument("--timeout", type=float, default=2.0)
  parser.add_argument("--full", action="store_true", help="print all 32 rows and columns")
  parser.add_argument("--build-only", action="store_true")
  args = parser.parse_args()

  pack_dtype = PACK_DTYPES[args.pack_dtype]
  if args.build_only:
    build_only(args.setup, args.sfpu_store, pack_dtype, args.raw_load_gap, args.raw_load_order)
    return 0

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    tile = run_pack_dump(
      device,
      setup=args.setup,
      sfpu_store=args.sfpu_store,
      pack_dtype=pack_dtype,
      raw_load_gap=args.raw_load_gap,
      raw_load_order=args.raw_load_order,
      core=core,
      timeout_s=args.timeout,
    )
  print_pack_dump(tile, setup=args.setup, sfpu_store=args.sfpu_store, pack_dtype=pack_dtype, full=args.full)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
