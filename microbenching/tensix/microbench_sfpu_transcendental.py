#!/usr/bin/env python3
"""Blackhole SFPU exp/reciprocal microbench.

Storage dtype is bf16 (`Dtype.Float16_b`) in one 32x32 tile. The tested values
occupy the first 32-lane SFPU load/store footprint (rows 0..3, even columns);
the helpers run on TRISC1's SFPU through the add1.py five-RISC pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (does sys.path + TT_USB bootstrap on import)
import numpy as np

from device import Device
from dsl import (
  TTINCRWC, TTSFPLOAD, TTSFPNOP, TTSFPSTORE, TTSTALLWAIT,
  a2, a3, a4, a5, s8, zero,
)
from program import Dtype
from ttk.tensix import TensixStall
from ttk.sfpu import emit_rsqrt, emit_sigmoid, emit_silu, sfpu_exp, sfpu_reciprocal

from examples import add1
from examples.add1 import WAIT_MATH_AND_SFPU


TILE = 32
DTYPE = Dtype.Float16_b
ATOL = 2.0e-3
RTOL = 2.0e-2


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


def _op_exp(fw):
  sfpu_exp(fw, 0, 0, scratch=(1, 2, 3, 4, 5, 6, 7))


def _op_recip(fw):
  sfpu_reciprocal(fw, 0, 0, scratch=(1, 2, 3, 4, 5, 6, 7), iterations=2)


def _op_rsqrt(fw):
  emit_rsqrt(fw, 0, 0, scratch=(1, 2, 3, 4, 5, 6, 7), iterations=5)


def _op_sigmoid(fw):
  emit_sigmoid(fw, 0, 0, scratch=(1, 2, 3, 4, 5, 6, 7))


def _op_silu(fw):
  emit_silu(fw, 0, 0, scratch=(1, 2, 3, 4, 5, 6, 7))


def make_footprint(op, repeat: int = 1):
  """LOAD, then `repeat` op bodies LReg0->LReg0 (idempotence not required for
  timing; correctness is asserted only at repeat=1), then STORE."""
  def footprint(fw):
    fw.emit(TTSFPLOAD(0, 0, 7, 0))
    for _ in range(repeat):
      op(fw)
    fw.emit(TTSFPSTORE(0, 0, 7, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTINCRWC(0, 2, 0, 0))
    return fw
  return footprint


OPS = {
  "exp": _op_exp,
  "recip": _op_recip,
  "rsqrt": _op_rsqrt,
  "sigmoid": _op_sigmoid,
  "silu": _op_silu,
}

RESULT_ADDR = 0x12D000  # same scratch region the other tensix benches use


def make_timed_footprint(op, iterations: int):
  """RISC counter loop around one op body; wall-clock delta (cycles) -> L1.

  Timing is issue-side: once the Tensix FIFO backpressures, RISC push rate
  tracks SFPU throughput; the trailing STALLWAIT drains MATH|SFPU before the
  end-of-window clock read. Use a single tile (body runs 4x/tile; the record
  is rewritten with the same measurement each time).
  """
  def footprint(fw):
    fw.emit(TTSFPLOAD(0, 0, 7, 0))
    harness.read_wall_clock(fw, a2, a3)
    loop = fw._new_label("sfpu_timed")
    done = fw._new_label("sfpu_timed_done")
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


def run_body(device: Device, name: str, values: np.ndarray, body,
             n_tiles: int = 1) -> tuple[np.ndarray, float]:
  src_tile = footprint_tile(values)
  src_rm = to_bf16_bytes(src_tile) * n_tiles
  src_buf = device.alloc_write(
    src_rm,
    dtype=DTYPE,
    shape=(n_tiles, TILE, TILE),
    name=f"{name}_src",
  )
  dst_buf = device.dram.alloc(n_tiles, dtype=DTYPE, shape=(n_tiles, TILE, TILE), name=f"{name}_dst")

  old_body = add1.math_add1_replay_row
  add1.math_add1_replay_row = body
  try:
    prog = add1.build_program(
      src_buf.addr,
      dst_buf.addr,
      len(device.dram.bank_tiles),
      cores=device.cores[:1],
      tiles_per_core=n_tiles,
    )
    prog.name = f"microbench_sfpu_{name}"
    elapsed_us = sum(timing["us"] for timing in device.run(prog))
  finally:
    add1.math_add1_replay_row = old_body

  got = from_bf16_bytes(device.dram_read(dst_buf), (n_tiles, TILE, TILE))
  return footprint_values(got[0]), elapsed_us


def check(name: str, got: np.ndarray, ref: np.ndarray) -> tuple[bool, float, float]:
  max_abs = float(np.max(np.abs(got - ref)))
  max_rel = float(np.max(np.abs(got - ref) / np.maximum(np.abs(ref), 1.0e-12)))
  ok = bool(np.allclose(got, ref, atol=ATOL, rtol=RTOL))
  print(f"  {name}: {'PASS' if ok else 'FAIL'} max_abs={max_abs:.6g} max_rel={max_rel:.6g}")
  if not ok:
    print(f"    got[:8]={got[:8].tolist()}")
    print(f"    ref[:8]={ref[:8].tolist()}")
  return ok, max_abs, max_rel


AICLK_MHZ = 800.0


def main() -> int:
  import argparse
  parser = argparse.ArgumentParser(
    description="SFPU transcendental (exp/recip/rsqrt/sigmoid/silu) microbench; needs device")
  parser.add_argument("--iters", type=int, default=0,
                      help="extra timed run per op: RISC loop of N op bodies on TRISC1, "
                           "wall-clock cycles read back from L1")
  args = parser.parse_args()

  f32 = lambda a: a.astype(np.float32)
  exp_in = to_bf16(np.linspace(-10.0, 2.0, 32, dtype=np.float32))
  recip_in = to_bf16(np.geomspace(0.25, 64.0, 32, dtype=np.float32).astype(np.float32))
  rsqrt_in = to_bf16(np.linspace(0.5, 2.0, 32, dtype=np.float32))  # near-unit Newton path
  sigmoid_in = to_bf16(np.linspace(-4.0, 4.0, 32, dtype=np.float32))
  cases = [
    ("exp[-10,2]", "exp", exp_in, np.exp(f32(exp_in))),
    ("recip[0.25,64]", "recip", recip_in, np.float32(1.0) / f32(recip_in)),
    ("rsqrt[0.5,2]", "rsqrt", rsqrt_in, np.float32(1.0) / np.sqrt(f32(rsqrt_in))),
    ("sigmoid[-4,4]", "sigmoid", sigmoid_in,
     np.float32(1.0) / (np.float32(1.0) + np.exp(-f32(sigmoid_in)))),
    ("silu[-4,4]", "silu", sigmoid_in,
     f32(sigmoid_in) / (np.float32(1.0) + np.exp(-f32(sigmoid_in)))),
  ]

  results = []
  with harness.open_device() as device:
    core = device.cores[0]
    for label, op_name, vals, ref in cases:
      got, _ = run_body(device, op_name, vals, make_footprint(OPS[op_name], 1))
      cycles = None
      if args.iters > 0:
        harness.clear_window(device, core, [(RESULT_ADDR, 4)])
        run_body(device, f"{op_name}_t", vals, make_timed_footprint(OPS[op_name], args.iters))
        raw = harness.read_window(device, core, RESULT_ADDR, 4)
        cycles = int.from_bytes(raw, "little")
      results.append((label, op_name, got, ref, cycles))

  print("SFPU transcendental microbench")
  print(f"  dtype={DTYPE.name} lanes=32 tile=32x32 iters={args.iters}")
  ok = True
  for label, op_name, got, ref, cycles in results:
    case_ok, _, _ = check(label, got, ref)
    ok = ok and case_ok
    if cycles is not None:
      cyc = cycles / args.iters
      print(f"    {op_name}: {cycles} cyc / {args.iters} iters"
            f" -> {cyc:.1f} cyc/op (32 lanes) = {cyc / 32:.2f} cyc/elem"
            f" = {cyc * 32:.0f} cyc/tile (32 groups)")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
