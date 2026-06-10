#!/usr/bin/env python3
"""Blackhole broadcast eltwise microbench: A op bcast(B), bf16.

Broadcast variants of eltwise binary per LLK (llk_unpack_AB.h /
llk_math_eltwise_binary.h, BroadcastType ROW/COL/SCALAR):

  row     out[r,c] = A[r,c] op B[0,c]   (rmsnorm scale, softmax denominator)
  col     out[r,c] = A[r,c] op B[r,0]
  scalar  out[r,c] = A[r,c] op B[0,0]   (attention 1/sqrt(d))

Differences from NONE bcast: instr_mod19 on the ELW op (1=COL, 2=ROW, 3=ALL),
SrcB addr-mod increment (0 for ROW/SCALAR, 8 for COL), unpack MOP feeds B
faces per the bcast pattern with SETADCZW B-Z-counter resets, and the src
clear becomes CLR_A only for COL/SCALAR (B cleared explicitly after the tile).

Reuses the eltwise-binary scaffold (2-CB add1 pipeline). --iters N adds a
timed N-tile stream per variant.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
import numpy as np

from dsl import TTNOP, TTSETADCZW, TTSETRWC
from ttk.tensix import MopCfg

import microbench_eltwise_binary as base
from microbench_eltwise_binary import (
  DTYPE, ELW_ADDR_MOD, ELW_OPS, RESULT_ADDR, TILE, UNPACK_SRCA, UNPACK_SRCB,
  to_bf16,
)

# SETADCZW(UNP_B=0b010, ...) Z-counter resets, per LLK unpack_AB bcast MOPs.
ZRESET_B = TTSETADCZW(2, 0, 0, 0, 0, 1)       # B z = 0 (ROW: rewind to face 0/1)
ZSET_B2 = TTSETADCZW(2, 0, 0, 0, 2, 1)        # B z = 2 (COL: next face-row)

SETRWC_CLR_AB = TTSETRWC(3, 3, 0, 0, 0, 3)    # CLR_AB | CR_AB | SET_AB
SETRWC_CLR_A = TTSETRWC(1, 3, 0, 0, 0, 3)     # CLR_A  | CR_AB | SET_AB
SETRWC_CLR_B_BETWEEN = TTSETRWC(2, 0, 0, 0, 0, 0)
SETRWC_CLR_B_SETD = TTSETRWC(2, 0, 0, 0, 0, 4)

# instr_mod19 broadcast encodings (p_elwise).
BCAST_COL, BCAST_ROW, BCAST_ALL = 1, 2, 3


def elw(op: str, bcast: int):
  return ELW_OPS[op](0, 0, bcast, ELW_ADDR_MOD, 0)


# ROW: body=(B, A) per face-col, B z rewound each face-row; B never advances
# in math; src clear AB each face.
UNPACK_ROW_MOP = MopCfg(loop_outer=2, loop_inner=2,
                        template=[TTNOP(), ZRESET_B, TTNOP(),
                                  UNPACK_SRCB, UNPACK_SRCA, UNPACK_SRCA, UNPACK_SRCA])

def math_row_mop(op: str) -> MopCfg:
  e = elw(op, BCAST_ROW)
  return MopCfg(loop_outer=4, loop_inner=2,
                template=[TTNOP(), SETRWC_CLR_AB, TTNOP(), e, TTNOP(), e, e])


# COL: one B face per face-row (start op), A faces inner; math instr 1, B
# advances; CLR_A per face, CLR_B between face-rows, MOP run twice.
UNPACK_COL_MOP = MopCfg(loop_outer=2, loop_inner=2,
                        template=[UNPACK_SRCB, ZSET_B2, TTNOP(),
                                  UNPACK_SRCA, TTNOP(), UNPACK_SRCA, UNPACK_SRCA])

def math_col_mop(op: str) -> MopCfg:
  e = elw(op, BCAST_COL)
  return MopCfg(loop_outer=2, loop_inner=2,
                template=[TTNOP(), SETRWC_CLR_A, TTNOP(), e, TTNOP(), e, e])


# SCALAR: B unpacked once, all 4 A faces; CLR_A per face, CLR_B+SET_D after.
UNPACK_SCALAR_MOP = MopCfg(loop_outer=1, loop_inner=4,
                           template=[UNPACK_SRCB, TTNOP(), TTNOP(),
                                     UNPACK_SRCA, TTNOP(), UNPACK_SRCA, UNPACK_SRCA])

def math_scalar_mop(op: str) -> MopCfg:
  e = elw(op, BCAST_ALL)
  return MopCfg(loop_outer=4, loop_inner=2,
                template=[TTNOP(), SETRWC_CLR_A, TTNOP(), e, TTNOP(), e, e])


VARIANTS = {
  # name: (unpack_mop, math_mop_fn, addr_mod_ab, mop_runs, between, post)
  "row": (UNPACK_ROW_MOP, math_row_mop, 0x0008, 1, None, None),
  "col": (UNPACK_COL_MOP, math_col_mop, 0x0808, 2, SETRWC_CLR_B_BETWEEN, SETRWC_CLR_B_SETD),
  "scalar": (UNPACK_SCALAR_MOP, math_scalar_mop, 0x0008, 1, None, SETRWC_CLR_B_SETD),
}


def ref_bcast(op: str, variant: str, a, b):
  fn = {"add": np.add, "mul": np.multiply}[op]
  if variant == "row":
    return to_bf16(fn(a, b[:, 0:1, :]))
  if variant == "col":
    return to_bf16(fn(a, b[:, :, 0:1]))
  return to_bf16(fn(a, b[:, 0:1, 0:1]))


def run_variant(device, op, variant, a, b, *, tiles, timed=False):
  unpack_mop, math_fn, ab, runs, between, post = VARIANTS[variant]
  return base.run_op(
    device, op, a, b, tiles=tiles, timed=timed, name=f"bcast_{variant}_{op}",
    unpack_mop=unpack_mop,
    trisc1_kwargs=dict(math_mop=math_fn(op), addr_mod_ab=ab, mop_runs=runs,
                       between_runs=between, post_mop=post),
  )


def main() -> int:
  import argparse
  parser = argparse.ArgumentParser(description="broadcast eltwise (row/col/scalar) microbench; needs device")
  parser.add_argument("--iters", type=int, default=0)
  args = parser.parse_args()

  rng = np.random.default_rng(13)
  a = to_bf16(rng.uniform(-2.0, 2.0, (1, TILE, TILE)))
  b = to_bf16(rng.uniform(0.25, 2.0, (1, TILE, TILE)))

  ok = True
  cycles = {}
  with harness.open_device() as device:
    core = device.cores[0]
    for variant in ("row", "col", "scalar"):
      for op in ("add", "mul"):
        got = run_variant(device, op, variant, a, b, tiles=1)
        ref = ref_bcast(op, variant, a, b)
        atol, rtol = base.TOL[op]
        v_ok = bool(np.allclose(got, ref, atol=atol, rtol=rtol))
        max_abs = float(np.max(np.abs(got - ref)))
        print(f"  {variant}-{op}: {'PASS' if v_ok else 'FAIL'} max_abs={max_abs:.6g}")
        if not v_ok:
          print(f"    got[0,:4]={got[0,0,:4].tolist()}")
          print(f"    ref[0,:4]={ref[0,0,:4].tolist()}")
          print(f"    got[1,:4]={got[0,1,:4].tolist()}")
          print(f"    ref[1,:4]={ref[0,1,:4].tolist()}")
        ok = ok and v_ok

    if args.iters > 0:
      for variant in ("row", "col", "scalar"):
        n = args.iters
        harness.clear_window(device, core, [(RESULT_ADDR, 8)])
        an = to_bf16(rng.uniform(-2.0, 2.0, (n, TILE, TILE)))
        bn = to_bf16(rng.uniform(0.25, 2.0, (n, TILE, TILE)))
        got = run_variant(device, "mul", variant, an, bn, tiles=n, timed=True)
        ref = ref_bcast("mul", variant, an, bn)
        s_ok = bool(np.allclose(got, ref, atol=5e-2, rtol=5e-2))
        raw = harness.read_window(device, core, RESULT_ADDR, 4)
        cycles[variant] = (int.from_bytes(raw, "little"), s_ok)

  print("broadcast eltwise microbench")
  print(f"  dtype={DTYPE.name} tile=32x32 iters={args.iters}")
  for variant, (total, s_ok) in cycles.items():
    print(f"    {variant}-mul: {total} cyc / {args.iters} tiles -> {total / args.iters:.1f} cyc/tile"
          f" stream={'PASS' if s_ok else 'FAIL'}")
    ok = ok and s_ok
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
