#!/usr/bin/env python3
"""Blackhole SFPU reduce microbench: scalar sum, scalar max, per-row max.

Same scaffold as microbench_sfpu_transcendental.py (single core, TRISC1 SFPU
through the add1 five-RISC pipeline, bf16 storage):

  sum32   emit_sum_reduce_32        sum of 32-lane footprint -> L0 lane 0
  max8x4  emit_horizontal_reduce_max  per-8-lane-row max -> lane 0 of each row
  rowmax  emit_reduce_row_max_tile  per-row max of a 32x32 tile -> column 0
                                    (rest of tile is scratch: odd cols clobbered)

These helpers were validated by the llama RMSNorm/argmax POCs but never
device-run standalone; --iters N adds an issue-side wall-clock timing loop.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
import numpy as np

from device import Device
from dsl import (
  TTINCRWC, TTSFPLOAD, TTSFPMOV, TTSFPNOP, TTSFPSTORE, TTSTALLWAIT,
  a2, a3, a4, a5, s8, zero,
)
from program import Dtype
from ttk.tensix import TensixStall
from ttk.sfpu import (
  emit_horizontal_reduce_max,
  emit_reduce_row_max_tile,
  emit_sum_reduce_32,
)

from examples import add1
from examples.add1 import WAIT_MATH_AND_SFPU


TILE = 32
DTYPE = Dtype.Float16_b
ATOL = 2.0e-3
RTOL = 2.0e-2

RESULT_ADDR = 0x12D000  # same scratch region the other tensix benches use
AICLK_MHZ = 800.0


def to_bf16(x: np.ndarray) -> np.ndarray:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return ((u >> 16).astype("<u4") << 16).view("<f4")


def to_bf16_bytes(x: np.ndarray) -> bytes:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return (u >> 16).astype("<u2").tobytes()


def from_bf16_bytes(raw: bytes, shape: tuple[int, ...]) -> np.ndarray:
  u16 = np.frombuffer(raw, dtype="<u2")
  return (u16.astype("<u4") << 16).view("<f4").reshape(shape)


def footprint_tile(values: np.ndarray) -> np.ndarray:
  tile = np.zeros((TILE, TILE), dtype=np.float32)
  for lane, value in enumerate(values.astype(np.float32)):
    row = lane // 8
    col = (lane & 7) * 2
    tile[row, col] = value
  return to_bf16(tile)


def footprint_values(tile: np.ndarray) -> np.ndarray:
  out = np.empty(32, dtype=np.float32)
  for lane in range(32):
    row = lane // 8
    col = (lane & 7) * 2
    out[lane] = tile[row, col]
  return out


# ---------------------------------------------------------------- op bodies

def _op_sum32(fw):
  """Sum L0's 32 lanes; result in L0 (lane 0 validated). Clobbers L0..L3."""
  emit_sum_reduce_32(fw)


def _op_max8x4(fw):
  """Per-8-lane-row max of L0; row max lands in lane 0 of each row (lanes 0,
  8, 16, 24). The helper reduces L0 and L4 in parallel, so mirror L0 into L4
  first; clobbers L1/L5."""
  fw.emit(TTSFPMOV(0, 0, 4, 0))
  emit_horizontal_reduce_max(fw)


def make_group_footprint(op):
  """LOAD group -> op -> STORE group; one op body per call (4 calls/tile)."""
  def footprint(fw):
    fw.emit(TTSFPLOAD(0, 0, 7, 0))
    op(fw)
    fw.emit(TTSFPSTORE(0, 0, 7, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTINCRWC(0, 2, 0, 0))
    return fw
  return footprint


def make_group_timed_footprint(op, iterations: int):
  """RISC counter loop around one op body; wall-clock cycles -> L1."""
  def footprint(fw):
    fw.emit(TTSFPLOAD(0, 0, 7, 0))
    harness.read_wall_clock(fw, a2, a3)
    loop = fw._new_label("reduce_timed")
    done = fw._new_label("reduce_timed_done")
    fw.li(s8, iterations)
    fw.label(loop)
    fw.beq(s8, zero, done)
    op(fw)
    fw.addi(s8, s8, -1)
    fw.j(loop)
    fw.label(done)
    fw.push_tensix(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))
    harness.read_wall_clock(fw, a4, a5)
    fw.sub(a4, a4, a2)
    fw.li(a5, RESULT_ADDR)
    fw.sw(a4, a5, 0)
    fw.emit(TTSFPSTORE(0, 0, 7, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTINCRWC(0, 2, 0, 0))
    return fw
  return footprint


def rowmax_footprint(fw):
  """Whole-tile per-row max; absolute dest offsets, idempotent across the 4
  body calls per tile."""
  return emit_reduce_row_max_tile(fw)


def make_rowmax_timed_footprint(iterations: int):
  def footprint(fw):
    harness.read_wall_clock(fw, a2, a3)
    loop = fw._new_label("rowmax_timed")
    done = fw._new_label("rowmax_timed_done")
    fw.li(s8, iterations)
    fw.label(loop)
    fw.beq(s8, zero, done)
    emit_reduce_row_max_tile(fw)
    fw.addi(s8, s8, -1)
    fw.j(loop)
    fw.label(done)
    fw.push_tensix(TTSTALLWAIT(TensixStall.SYNC, WAIT_MATH_AND_SFPU))
    harness.read_wall_clock(fw, a4, a5)
    fw.sub(a4, a4, a2)
    fw.li(a5, RESULT_ADDR)
    fw.sw(a4, a5, 0)
    return fw
  return footprint


# ----------------------------------------------------------------- pipeline

def run_tile(device: Device, name: str, src_tile: np.ndarray, body) -> np.ndarray:
  src_buf = device.alloc_write(
    to_bf16_bytes(src_tile),
    dtype=DTYPE,
    shape=(1, TILE, TILE),
    name=f"{name}_src",
  )
  dst_buf = device.dram.alloc(1, dtype=DTYPE, shape=(1, TILE, TILE), name=f"{name}_dst")

  old_body = add1.math_add1_replay_row
  add1.math_add1_replay_row = body
  try:
    prog = add1.build_program(
      src_buf.addr,
      dst_buf.addr,
      len(device.dram.bank_tiles),
      cores=device.cores[:1],
      tiles_per_core=1,
    )
    prog.name = f"microbench_reduce_{name}"
    device.run(prog)
  finally:
    add1.math_add1_replay_row = old_body

  return from_bf16_bytes(device.dram_read(dst_buf), (1, TILE, TILE))[0]


def check(name: str, got: np.ndarray, ref: np.ndarray) -> bool:
  got = np.atleast_1d(np.asarray(got, dtype=np.float32))
  ref = np.atleast_1d(np.asarray(ref, dtype=np.float32))
  max_abs = float(np.max(np.abs(got - ref)))
  max_rel = float(np.max(np.abs(got - ref) / np.maximum(np.abs(ref), 1.0e-12)))
  ok = bool(np.allclose(got, ref, atol=ATOL, rtol=RTOL))
  print(f"  {name}: {'PASS' if ok else 'FAIL'} max_abs={max_abs:.6g} max_rel={max_rel:.6g}")
  if not ok:
    print(f"    got[:8]={got.ravel()[:8].tolist()}")
    print(f"    ref[:8]={ref.ravel()[:8].tolist()}")
  return ok


def main() -> int:
  import argparse
  parser = argparse.ArgumentParser(
    description="SFPU reduce (sum32/max32/rowmax) microbench; needs device")
  parser.add_argument("--iters", type=int, default=0,
                      help="extra timed run per op: RISC loop of N op bodies on TRISC1, "
                           "wall-clock cycles read back from L1")
  args = parser.parse_args()

  rng = np.random.default_rng(7)
  vals = to_bf16(rng.uniform(-2.0, 2.0, 32).astype(np.float32))
  tile_in = to_bf16(rng.uniform(-2.0, 2.0, (TILE, TILE)).astype(np.float32))

  ok = True
  cycles = {}
  with harness.open_device() as device:
    core = device.cores[0]

    # sum32: scalar sum of the 32-lane footprint, validated at lane 0.
    got = run_tile(device, "sum32", footprint_tile(vals),
                   make_group_footprint(_op_sum32))
    ok &= check("sum32 lane0", footprint_values(got)[0], np.sum(vals))

    # max8x4: per-8-lane-row max, validated at lane 0 of each row.
    got = run_tile(device, "max8x4", footprint_tile(vals),
                   make_group_footprint(_op_max8x4))
    row_max = vals.reshape(4, 8).max(axis=1)
    ok &= check("max8x4 row-lane0", footprint_values(got)[[0, 8, 16, 24]], row_max)

    # rowmax: per-row max in column 0; the rest of the tile is scratch
    # (the 32-lane stores clobber odd columns), so only col0 is checked.
    got = run_tile(device, "rowmax", tile_in, rowmax_footprint)
    ok &= check("rowmax col0", got[:, 0], np.max(tile_in, axis=1))

    if args.iters > 0:
      timed = [
        ("sum32", footprint_tile(vals),
         make_group_timed_footprint(_op_sum32, args.iters), 32),
        ("max8x4", footprint_tile(vals),
         make_group_timed_footprint(_op_max8x4, args.iters), 32),
        ("rowmax", tile_in, make_rowmax_timed_footprint(args.iters), TILE * TILE),
      ]
      for name, src, body, elems in timed:
        harness.clear_window(device, core, [(RESULT_ADDR, 4)])
        run_tile(device, f"{name}_t", src, body)
        raw = harness.read_window(device, core, RESULT_ADDR, 4)
        cycles[name] = (int.from_bytes(raw, "little"), elems)

  print("SFPU reduce microbench")
  print(f"  dtype={DTYPE.name} tile=32x32 iters={args.iters}")
  for name, (total, elems) in cycles.items():
    cyc = total / args.iters
    print(f"    {name}: {total} cyc / {args.iters} iters -> {cyc:.1f} cyc/op"
          f" ({elems} elems) = {cyc / elems:.2f} cyc/elem")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
