#!/usr/bin/env python3
"""Device RMSNorm inverse-scalar reduction proof.

The norm-scale GEMV bridge still uses a host-produced ``inv_rms``. This bench
keeps the whole scalar calculation on device for a Llama-sized K=2048 vector:

  1. 64 tiles: sum x^2 over each 32-lane footprint -> packed partial tiles.
  2. 2 tiles: sum 32 partials each -> one packed final-partial tile.
  3. 1 tile: sum two partials, multiply by 1/K, add eps, rsqrt -> inv_rms.

The reductions are intentionally staged as separate programs; the goal here is
device residency and stable long-running behavior, not the final minimum-launch
RMSNorm kernel.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "microbenching"))
sys.path.insert(0, str(ROOT / "examples"))

import harness  # noqa: E402,F401
import numpy as np

from dsl import (
  TTMOP, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSFPADD, TTSFPLOAD, TTSFPMUL,
  TTSFPNOP, TTSFPSTORE, TTSTALLWAIT,
  a0, a1, a2, a4, a5, s0, s2, s3, s4, s5, t0, t1, t2, t3, t4, t5, t6, zero,
)
from examples import add1  # noqa: E402
from examples.add1 import (
  CB_DEPTH, OUT_CB, STALL_MATH_PACK_ROOM, SYNC, SYNC_DONE1, TILE_BYTES, Trisc,
  WAIT_MATH_AND_SFPU, write_trisc1_dest_offset_instr,
)
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.sfpu import emit_rsqrt, emit_sum_reduce_32, sfpu_load_fp32_const  # noqa: E402
from ttk.tensix import TensixSem, TensixSemWait, TensixStall, TensixWait  # noqa: E402

TILE = 32
PAGE = Dtype.Float16_b.tile_size


def to_bf16(x: np.ndarray) -> np.ndarray:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return ((u >> 16).astype("<u4") << 16).view("<f4")


def to_bf16_bytes(x: np.ndarray) -> bytes:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return (u >> 16).astype("<u2").tobytes()


def from_bf16_bytes(raw: bytes, shape: tuple[int, ...]) -> np.ndarray:
  return (np.frombuffer(raw, dtype="<u2").astype("<u4") << 16).view("<f4").reshape(shape)


def footprint_put(tile: np.ndarray, values: np.ndarray) -> None:
  for lane, value in enumerate(values.astype(np.float32)):
    row = lane // 8
    col = (lane & 7) * 2
    tile[row, col] = value


def footprint_values(tile: np.ndarray) -> np.ndarray:
  out = np.empty(32, dtype=np.float32)
  for lane in range(32):
    row = lane // 8
    col = (lane & 7) * 2
    out[lane] = tile[row, col]
  return out


def trisc1_reduce(
    *,
    square: bool,
    final: bool = False,
    k: int = 2048,
    eps: float = 1.0e-5,
    square_scale: float = 1.0,
    final_output_scale: float = 1.0,
) -> Trisc:
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=Dtype.Float16_b, mop_cfg=add1.MATH_MOP_CFG)
  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTMOP(1, 0, 0))  # SrcA tile -> dest.
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))

    fw.emit(TTSFPLOAD(0, 0, 7, 0))
    if square and square_scale != 1.0:
      sfpu_load_fp32_const(fw, 2, square_scale)
      fw.emit(TTSFPMUL(0, 2, 9, 0, 0))
      fw.emit(TTSFPNOP())
    if square:
      fw.emit(TTSFPMUL(0, 0, 9, 0, 0))
      fw.emit(TTSFPNOP())
    emit_sum_reduce_32(fw)
    if final:
      sfpu_load_fp32_const(fw, 2, 1.0 / float(k))
      fw.emit(TTSFPMUL(0, 2, 9, 0, 0))
      fw.emit(TTSFPNOP())
      sfpu_load_fp32_const(fw, 2, eps)
      fw.emit(TTSFPADD(10, 0, 2, 0, 0))
      fw.emit(TTSFPNOP())
      emit_rsqrt(fw, 0, 0, scratch=(1, 2, 3, 4, 5, 6, 7), iterations=5)
      if final_output_scale != 1.0:
        sfpu_load_fp32_const(fw, 2, final_output_scale)
        fw.emit(TTSFPMUL(0, 2, 9, 0, 0))
        fw.emit(TTSFPNOP())
    fw.emit(TTSFPSTORE(0, 0, 7, 0))
    fw.emit(TTSFPNOP())

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


def compact_offset_for_lane(fw, lane_reg, out_reg) -> None:
  fw.srli(out_reg, lane_reg, 3)
  fw.slli(out_reg, out_reg, 5)
  fw.andi(t2, lane_reg, 7)
  fw.slli(t2, t2, 2)
  fw.add(out_reg, out_reg, t2)


def ncrisc_compact() -> add1.Ncrisc:
  fw = add1.Ncrisc()
  # RTAs: dst base, dst base tile, tiles, bank count.
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  with fw.tile_loop("ncrisc"):
    fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
    fw.cb_read_ptr(NM.CB_INTERFACE, OUT_CB, out=t5)

    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
    fw.addi(t4, t4, 1)
    fw.srli(a1, s5, 5)
    fw.add(a1, a1, s2)
    fw.andi(t3, s5, 31)
    compact_offset_for_lane(fw, t3, a4)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s4)
    fw.add(a0, a0, a4)
    fw.li(a5, 2)
    fw.noc_write(1, 0, t5, a0, 0, a2, a5, a=t0, v=t1)
    fw.noc_write_barrier(1, t4, addr=t0, val=t1)
    fw.cb_pop_front(NM.CB_INTERFACE, OUT_CB)
  return fw


def brisc_reduce(reader_preamble=None) -> add1.Brisc:
  fw = add1.Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    add1.SYNC_TRISC_START, add1.SYNC_READ, add1.SYNC_DONE0, add1.SYNC_DONE1, add1.SYNC_DONE2,
    add1.SYNC_TRISC_INIT, add1.SYNC_TRISC_INIT + 4, add1.SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  if reader_preamble is not None:
    reader_preamble(fw)
  fw.write32(add1.SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.add(a1, s2, s5)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
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
    fw.signal_sync(add1.SYNC_READ, t2)
  return fw


def build_reduce_program(src_addr: int, dst_addr: int, num_banks: int, *,
                         core, tiles: int, square: bool, compact: bool,
                         final: bool = False, k: int = 2048, eps: float = 1.0e-5,
                         square_scale: float = 1.0,
                         final_output_scale: float = 1.0,
                         reader_preamble=None,
                         reader_arg_extra=None) -> Program:
  brisc_fw = brisc_reduce(reader_preamble)
  ncrisc_fw = ncrisc_compact() if compact else add1.ncrisc(num_banks)
  trisc0_fw = add1.trisc0()
  trisc1_fw = trisc1_reduce(
    square=square,
    final=final,
    k=k,
    eps=eps,
    square_scale=square_scale,
    final_output_scale=final_output_scale,
  )
  trisc2_fw = add1.trisc2()

  brisc_fw.rta(lambda x, y: [src_addr, 0, tiles, num_banks] + (
      list(reader_arg_extra(x, y)) if callable(reader_arg_extra) else list(reader_arg_extra or [])))
  ncrisc_fw.rta(lambda _x, _y: [dst_addr, 0, tiles, num_banks])
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
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="device RMSNorm inv_rms reduction proof; needs device")
  p.add_argument("--k", type=int, default=2048)
  p.add_argument("--eps", type=float, default=1.0e-5)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()
  if args.k % 32 != 0:
    raise ValueError("--k must be a multiple of 32")
  partials = args.k // 32
  if partials % 32 != 0:
    raise ValueError("this staged proof expects k/32 to be a multiple of 32")

  rng = np.random.default_rng(73)
  x = to_bf16(rng.uniform(-2.0, 2.0, size=args.k).astype(np.float32))
  src = np.zeros((partials, TILE, TILE), dtype=np.float32)
  for i in range(partials):
    footprint_put(src[i], x[i * 32:(i + 1) * 32])

  ref = np.float32(1.0 / np.sqrt(np.mean(x.astype(np.float32) ** 2) + np.float32(args.eps)))

  with harness.open_device() as device:
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    src_buf = device.alloc_write(to_bf16_bytes(src), dtype=Dtype.Float16_b,
                                 shape=src.shape, name="rms_x")
    partial1_tiles = partials // 32
    partial1_buf = device.dram.alloc(partial1_tiles, dtype=Dtype.Float16_b, name="rms_partial1")
    partial2_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, name="rms_partial2")
    inv_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, shape=(1, TILE, TILE), name="rms_inv")
    device.dram_write(partial1_buf, b"\0" * partial1_buf.size)
    device.dram_write(partial2_buf, b"\0" * partial2_buf.size)

    prog1 = build_reduce_program(src_buf.addr, partial1_buf.addr, num_banks, core=core,
                                 tiles=partials, square=True, compact=True)
    prog1.name = "rms_sumsq_partials"
    prog2 = build_reduce_program(partial1_buf.addr, partial2_buf.addr, num_banks, core=core,
                                 tiles=partial1_tiles, square=False, compact=True)
    prog2.name = "rms_reduce_partials"
    prog3 = build_reduce_program(partial2_buf.addr, inv_buf.addr, num_banks, core=core,
                                 tiles=1, square=False, compact=False,
                                 final=True, k=args.k, eps=args.eps)
    prog3.name = "rms_inv"

    times = []
    for _ in range(args.runs):
      device.dram_write(partial1_buf, b"\0" * partial1_buf.size)
      device.dram_write(partial2_buf, b"\0" * partial2_buf.size)
      for prog in (prog1, prog2, prog3):
        times.extend(device.run(prog))
    raw = device.dram_read(inv_buf)

  inv_tile = from_bf16_bytes(raw, (1, TILE, TILE))[0]
  got = float(footprint_values(inv_tile)[0])
  rel = abs(got - float(ref)) / max(abs(float(ref)), 1.0e-12)
  ok = rel <= 5.0e-2

  print("RMSNorm inv_rms device reduction")
  print(f"  K={args.k} partials={partials} runs={args.runs} eps={args.eps:g}")
  if times:
    print(f"  launches={3 * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  inv_rms got={got:.6f} ref={float(ref):.6f} rel={rel:.6f}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
