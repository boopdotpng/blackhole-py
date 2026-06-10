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
from dsl import TTINCRWC, TTSFPLOAD, TTSFPNOP, TTSFPSTORE
from program import Dtype
from ttk.sfpu import sfpu_exp, sfpu_reciprocal

from examples import add1


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


def sfpu_exp_footprint(fw):
  fw.emit(TTSFPLOAD(0, 0, 7, 0))
  sfpu_exp(fw, 0, 0, scratch=(1, 2, 3, 4, 5, 6, 7))
  fw.emit(TTSFPSTORE(0, 0, 7, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTINCRWC(0, 2, 0, 0))
  return fw


def sfpu_recip_footprint(fw):
  fw.emit(TTSFPLOAD(0, 0, 7, 0))
  sfpu_reciprocal(fw, 0, 0, scratch=(1, 2, 3, 4, 5, 6, 7), iterations=2)
  fw.emit(TTSFPSTORE(0, 0, 7, 0))
  fw.emit(TTSFPNOP())
  fw.emit(TTINCRWC(0, 2, 0, 0))
  return fw


def run_body(device: Device, name: str, values: np.ndarray, body) -> tuple[np.ndarray, float]:
  src_tile = footprint_tile(values)
  src_buf = device.alloc_write(
    to_bf16_bytes(src_tile),
    dtype=DTYPE,
    shape=(TILE, TILE),
    name=f"{name}_src",
  )
  dst_buf = device.dram.alloc(1, dtype=DTYPE, shape=(TILE, TILE), name=f"{name}_dst")

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
    prog.name = f"microbench_sfpu_{name}"
    elapsed_us = sum(timing["us"] for timing in device.run(prog))
  finally:
    add1.math_add1_replay_row = old_body

  got_tile = from_bf16_bytes(device.dram_read(dst_buf), (TILE, TILE))
  return footprint_values(got_tile), elapsed_us


def check(name: str, got: np.ndarray, ref: np.ndarray) -> tuple[bool, float, float]:
  max_abs = float(np.max(np.abs(got - ref)))
  max_rel = float(np.max(np.abs(got - ref) / np.maximum(np.abs(ref), 1.0e-12)))
  ok = bool(np.allclose(got, ref, atol=ATOL, rtol=RTOL))
  print(f"  {name}: {'PASS' if ok else 'FAIL'} max_abs={max_abs:.6g} max_rel={max_rel:.6g}")
  if not ok:
    print(f"    got[:8]={got[:8].tolist()}")
    print(f"    ref[:8]={ref[:8].tolist()}")
  return ok, max_abs, max_rel


def main() -> int:
  import argparse
  argparse.ArgumentParser(description="SFPU transcendental (exp, recip) microbench; needs device").parse_args()
  exp_in = to_bf16(np.linspace(-10.0, 2.0, 32, dtype=np.float32))
  recip_in = to_bf16(np.geomspace(0.25, 64.0, 32, dtype=np.float32).astype(np.float32))

  with harness.open_device() as device:
    exp_got, exp_us = run_body(device, "exp", exp_in, sfpu_exp_footprint)
    recip_got, recip_us = run_body(device, "recip", recip_in, sfpu_recip_footprint)

  exp_ref = np.exp(exp_in.astype(np.float32))
  recip_ref = np.float32(1.0) / recip_in.astype(np.float32)

  print("SFPU transcendental microbench")
  print(f"  dtype={DTYPE.name} lanes=32 tile=32x32")
  print(f"  device_us: exp={exp_us:.1f} recip={recip_us:.1f}")
  exp_ok, _, _ = check("exp[-10,2]", exp_got, exp_ref)
  recip_ok, _, _ = check("recip[0.25,64]", recip_got, recip_ref)
  ok = exp_ok and recip_ok
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
