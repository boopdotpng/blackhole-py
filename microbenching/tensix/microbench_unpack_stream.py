#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402

import numpy as np

from asm import KernelBase
from device import Device
from dram import tilize
from dsl import (
  TTMOP, TTSEMGET, TTSETADCZW, TTSETRWC, TTSTALLWAIT,
  a0, a1, a2, a3, a4, a5, s0, s2, s3, s4, s5,
  t0, t1, t2, t3, t4, t5, t6, zero,
)
from examples import add1
from examples.add1 import Brisc, Trisc
from matmul_peak import RiscSync
from program import Dtype, Program
from ttk.mailbox import BriscMailbox as BM, TriscLocalMem as TLM
from ttk.noc import NOC
from ttk.tensix import Cfg, TensixL1, TensixRegs, TensixSem, TensixStall, TensixWait, ThreadCfg


RESULT_BASE = 0x12E000
PROGRESS_BASE = RESULT_BASE + 0x100
RESULT_MAGIC = 0x55505348  # "HSPU"
STATUS_STARTED = 0x7100B001
STATUS_DONE = 0x7100D00D
RESULT_WORDS = 16
CB_DEPTH = 16
SYNC_L1 = 0x120000
SYNC_TRISC_START = SYNC_L1
SYNC_READ = SYNC_L1 + 4
SYNC_DONE0 = SYNC_L1 + 8
SYNC_DONE1 = SYNC_L1 + 12
SYNC_TRISC_INIT = SYNC_L1 + 20
SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)

DTYPES = {
  "bf16": Dtype.Float16_b,
  "fp16": Dtype.Float16,
  "fp32": Dtype.Float32,
}


def write_result(fw: KernelBase, *, dtype: Dtype, tiles: int, status: int, start_lo=zero, start_hi=zero, end_lo=zero, end_hi=zero):
  fw.li(s2, RESULT_BASE)
  values = (
    RESULT_MAGIC,
    status,
    dtype.value,
    dtype.tile_size,
    tiles,
    CB_DEPTH,
  )
  for off, value in enumerate(values):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off, reg in enumerate((start_lo, start_hi, end_lo, end_hi), start=len(values)):
    fw.sw(reg, s2, off * 4)
  for off in range(10, RESULT_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def mark(fw: KernelBase, code: int):
  fw.li(t0, code)
  fw.write32(PROGRESS_BASE, t0, tmp_addr=t1, tmp_val=t2)
  return fw


def brisc(tile_bytes: int) -> Brisc:
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)
  mark(fw, 0xB000)
  with fw.tile_loop("brisc"):
    mark(fw, 0xB100)
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.add(a1, s5, s2)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.local_noc0_coord(a5)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.addi(t4, t4, 1)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    fw.li(t6, tile_bytes)
    fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
    fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    wait = fw._new_label("brisc_read_wait")
    fw.label(wait)
    fw.lw(t1, t0, 0)
    fw.bltu(t1, t4, wait)
    fw.fence()
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    mark(fw, 0xB200)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_READ, t2)
  return fw


def trisc0(dtype: Dtype, tiles: int) -> Trisc:
  fw = Trisc(0, SYNC)
  fw.prologue()
  write_result(fw, dtype=dtype, tiles=tiles, status=STATUS_STARTED)
  fw.unpack.init(dtype=dtype, tile_bytes=dtype.tile_size, mop_cfg=add1.UNPACK_MOP_CFG)
  fw.init_barrier()
  mark(fw, 0xC000)

  harness.read_wall_clock(fw, a2, a3)
  fw.li(s5, 0)
  loop = fw._new_label("trisc0_unpack_stream")
  done = fw._new_label("trisc0_unpack_stream_done")
  fw.label(loop)
  fw.beq(s5, s3, done)
  mark(fw, 0xC100)
  fw.cb_wait_front(fw.data["cb_interface"], 0)
  mark(fw, 0xC200)
  fw.cb_read_ptr(fw.data["cb_interface"], 0, out=s0)
  fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 15))

  wait_unp = fw._new_label("wait_unpack_ctx")
  wait_done = fw._new_label("wait_unpack_ctx_done")
  fw.li(t0, TensixRegs.PC_UNPACK_SYNC)
  fw.label(wait_unp)
  fw.lw(t1, t0, 0)
  fw.andi(t1, t1, 0xFE)
  fw.beq(t1, zero, wait_done)
  fw.fence()
  fw.j(wait_unp)
  fw.label(wait_done)

  fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
  fw.li(t2, TensixRegs.CFG_BASE + Cfg.THCON_SEC0_REG3_Base_address.addr32 * 4)
  cfg_addr_done = fw._new_label("cfg_addr_done")
  fw.beq(t1, zero, cfg_addr_done)
  fw.addi(t2, t2, 4)
  fw.label(cfg_addr_done)
  fw.addi(t3, s0, -1)
  fw.sw(t3, t2, 0)
  fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

  fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
  mark(fw, 0xC300)
  fw.emit(TTMOP(1, 0, 0))
  mark(fw, 0xC400)
  fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
  mark(fw, 0xC500)
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
  mark(fw, 0xC600)
  fw.addi(t2, s5, 1)
  fw.signal_sync(SYNC_DONE0, t2)
  fw.addi(s5, s5, 1)
  fw.j(loop)
  fw.label(done)
  mark(fw, 0xCFFF)
  harness.read_wall_clock(fw, a4, a5)
  write_result(fw, dtype=dtype, tiles=tiles, status=STATUS_DONE, start_lo=a2, start_hi=a3, end_lo=a4, end_hi=a5)
  return fw.ret_kernel()


def trisc1_consumer(dtype: Dtype) -> Trisc:
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=dtype, mop_cfg=add1.MATH_MOP_CFG)
  fw.init_barrier()
  mark(fw, 0xD000)
  with fw.tile_loop():
    mark(fw, 0xD100)
    fw.emit(TTMOP(1, 0, 0))
    mark(fw, 0xD200)
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH))
    mark(fw, 0xD300)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE1, t2)
  return fw


def trisc2_idle() -> Trisc:
  fw = Trisc(2, SYNC)
  fw.prologue()
  fw.init_barrier()
  mark(fw, 0xE000)
  return fw.ret_kernel()


def build_program(src_addr: int, num_banks: int, *, core, dtype: Dtype, tiles: int) -> Program:
  brisc_fw = brisc(dtype.tile_size)
  trisc0_fw = trisc0(dtype, tiles)
  trisc1_fw = trisc1_consumer(dtype)
  trisc2_fw = trisc2_idle()
  brisc_fw.rta(lambda _x, _y: [src_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw):
    fw.rta(lambda _x, _y: [tiles])
  trisc2_fw.rta(lambda _x, _y: [])
  program = Program(
    brisc=brisc_fw,
    ncrisc=KernelBase().ret(),
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, dtype.tile_size, CB_DEPTH)],
  )
  program.grid = ((core[1],), (core[0],))
  program.name = f"unpack_stream:{dtype.name}"
  return program


def make_payload(dtype: Dtype, tiles: int) -> bytes:
  if dtype is Dtype.Float32:
    values = np.arange(tiles * 32 * 32, dtype="<u4") ^ np.uint32(0x3F800000)
    return values.tobytes()
  values = (np.arange(tiles * 32 * 32, dtype="<u2") * np.uint16(17)) ^ np.uint16(0x5A5A)
  return values.tobytes()


def expected_cb_payload(payload: bytes, dtype: Dtype, tiles: int) -> bytes:
  return tilize(payload, dtype.bpe, (tiles, 32, 32))


def parse_result(blob: bytes):
  words = struct.unpack("<" + "I" * RESULT_WORDS, blob)
  if words[0] != RESULT_MAGIC:
    raise RuntimeError(f"bad result magic 0x{words[0]:08x}")
  if words[1] != STATUS_DONE:
    raise RuntimeError(f"benchmark did not finish, status=0x{words[1]:08x}")
  start = words[6] | (words[7] << 32)
  end = words[8] | (words[9] << 32)
  cycles = (end - start) & ((1 << 64) - 1)
  return {
    "dtype_value": words[2],
    "tile_bytes": words[3],
    "tiles": words[4],
    "cycles": cycles,
    "cycles_per_tile": cycles / words[4],
  }


def main() -> int:
  parser = argparse.ArgumentParser(description="Time real CB0 -> unpack -> SrcA streams on one Blackhole Tensix core.")
  parser.add_argument("--dtype", choices=tuple(DTYPES), nargs="+", default=["bf16"])
  parser.add_argument("--tiles", type=int, nargs="+", default=[8])
  parser.add_argument("--core", type=harness.parse_core, default=None)
  parser.add_argument("--dump-cb", action="store_true", help="dump/compare first CB0 bytes after unpack")
  args = parser.parse_args()
  if any(tiles <= 0 for tiles in args.tiles):
    raise ValueError("--tiles must be positive")

  with harness.open_device() as device:
    core = args.core or device.cores[0]
    print("| dtype | tile_bytes | tiles | cycles | cycles/tile |")
    print("|---|---:|---:|---:|---:|")
    for dtype_name in args.dtype:
      dtype = DTYPES[dtype_name]
      for tiles in args.tiles:
        payload = make_payload(dtype, tiles)
        tiled_payload = expected_cb_payload(payload, dtype, tiles)
        src_buf = device.alloc_write(payload, dtype=dtype, shape=(tiles, 32, 32), name=f"unpack_{dtype_name}_src")
        cb_span = dtype.tile_size * min(tiles, CB_DEPTH)
        before = b""
        if args.dump_cb:
          harness.clear_window(device, core, [(TensixL1.DATA_BUFFER_SPACE_BASE, cb_span), (RESULT_BASE, RESULT_WORDS * 4)])
          before = harness.read_window(device, core, TensixL1.DATA_BUFFER_SPACE_BASE, min(64, cb_span))
        else:
          harness.clear_window(device, core, [(RESULT_BASE, RESULT_WORDS * 4)])
        try:
          device.run(build_program(src_buf.addr, len(device.dram.bank_tiles), core=core, dtype=dtype, tiles=tiles))
        except TimeoutError:
          progress = harness.read_window(device, core, PROGRESS_BASE, 4)
          result_blob = harness.read_window(device, core, RESULT_BASE, RESULT_WORDS * 4)
          sync_blob = harness.read_window(device, core, SYNC_L1, 32)
          print(f"timeout progress=0x{int.from_bytes(progress, 'little'):08x}")
          print(f"timeout result={result_blob.hex()}")
          print(f"timeout sync={sync_blob.hex()}")
          raise
        result = parse_result(harness.read_window(device, core, RESULT_BASE, RESULT_WORDS * 4))
        print(
          f"| {dtype_name} | {result['tile_bytes']} | {result['tiles']} | "
          f"{result['cycles']} | {result['cycles_per_tile']:.2f} |"
        )
        if args.dump_cb:
          after = harness.read_window(device, core, TensixL1.DATA_BUFFER_SPACE_BASE, min(64, cb_span))
          expected = tiled_payload[:len(after)]
          print(f"  cb0 before[0:{len(before)}]={before.hex()}")
          print(f"  cb0 after [0:{len(after)}]={after.hex()}")
          print(f"  src  expect[0:{len(expected)}]={expected.hex()}")
          print(f"  cb0_after_matches_source={after == expected}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
