#!/usr/bin/env python3
"""Staged device GEMV -> residual add proof.

This models the two decode residual sites:

  x_next = x_residual + projection(x_in)

GEMV writes its row output to DRAM, then a separate eltwise ADD program streams
the first output row plus a row-tiled residual buffer and writes the next
activation buffer. This intentionally keeps the program boundary explicit; a
later in-GEMV fusion would need a Tensix add path, not just a writer hook.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "microbenching"))
sys.path.insert(0, str(ROOT / "microbenching" / "tensix"))
sys.path.insert(0, str(ROOT / "examples"))

import harness  # noqa: E402,F401
import matmul_peak as mm  # noqa: E402
import microbench_eltwise_binary as elw  # noqa: E402
import microbench_rmsnorm_gemv as rmsgemv  # noqa: E402
import numpy as np

from examples import add1  # noqa: E402
from examples.add1 import CB_DEPTH, OUT_CB, TILE_BYTES  # noqa: E402
from program import Dtype, Program  # noqa: E402

TILE = 32


def row_tiles_to_vector(raw: bytes, tiles: int, n: int) -> np.ndarray:
  data = elw.from_bf16_bytes(raw, (tiles, TILE, TILE))
  return data[:, 0, :].reshape(-1)[:n]


def build_two_source_binary(
    op: str,
    a_addr: int,
    b_addr: int,
    dst_addr: int,
    num_banks: int,
    *,
    core,
    tiles: int,
) -> Program:
  brisc_fw = rmsgemv.brisc_two_source(b_fixed=False)
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = elw.trisc0(elw.UNPACK_AB_MOP_CFG)
  trisc1_fw = elw.trisc1(
    op,
    math_mop=elw.elw_math_mop(op),
    addr_mod_ab=0x0808,
    mop_runs=1,
    between_runs=None,
    post_mop=None,
  )
  trisc2_fw = add1.trisc2()

  brisc_fw.rta(lambda _x, _y: [a_addr, b_addr, 0, tiles, num_banks])
  ncrisc_fw.rta(lambda _x, _y: [dst_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (1, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = f"two_src_{op}"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="staged device GEMV -> residual-add proof; needs device")
  p.add_argument("--k", type=int, default=2048)
  p.add_argument("--n", type=int, default=2048)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()
  if args.k % TILE or args.n % TILE:
    raise ValueError("--k and --n must be multiples of 32")

  rng = np.random.default_rng(91)
  a_ref = rng.uniform(-0.5, 0.5, size=(1, args.k)).astype(np.float32)
  b_ref = rng.uniform(-0.5, 0.5, size=(args.k, args.n)).astype(np.float32)
  residual = rng.uniform(-2.0, 2.0, size=args.n).astype(np.float32)
  a_ref = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(a_ref), a_ref.shape)
  b_ref = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(b_ref), b_ref.shape)
  residual_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(residual), residual.shape)

  with harness.open_device() as device:
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    ys = sorted({y for _, y in device.cores})[:1]
    cores = [c for c in device.cores if c[1] in ys]
    chunks = mm.plan_output_chunks(1, args.k, args.n, cores, num_banks)
    Mp, Kp, Np = mm.global_padded_shape(1, args.k, args.n, chunks)
    out_tiles = Np // TILE

    a_padded = np.zeros((Mp, Kp), dtype=np.float32)
    b_padded = np.zeros((Kp, Np), dtype=np.float32)
    a_padded[:1, :args.k] = a_ref
    b_padded[:args.k, :args.n] = b_ref

    a_buf = device.alloc_write(mm.to_bf16_device_bytes(a_padded), dtype=Dtype.Float16_b,
                               shape=(Mp, Kp), name="resgemv_a")
    b_buf = device.alloc_write(mm.to_bf16_device_bytes(b_padded), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="resgemv_w")
    c_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Np), name="resgemv_c")
    residual_buf = device.alloc_write(
      elw.to_bf16_bytes(rmsgemv.vector_to_row_tiles(residual_bf16, Np)),
      dtype=Dtype.Float16_b,
      shape=(out_tiles, TILE, TILE),
      name="resgemv_residual",
    )
    next_buf = device.dram.alloc(out_tiles, dtype=Dtype.Float16_b,
                                 shape=(out_tiles, TILE, TILE), name="resgemv_next")

    layout_base = dict(a_row_stride=Kp // TILE, b_row_stride=Np // TILE, c_row_stride=Np // TILE)
    gemv_progs = []
    for i, chunk in enumerate(chunks):
      layout = mm.TensorLayout(
        m_tile_offset=chunk.m_tile_offset,
        n_tile_offset=chunk.n_tile_offset,
        **layout_base,
      )
      prog = mm.build_program(chunk.plan, a_buf.addr, b_buf.addr, c_buf.addr, num_banks, layout)
      prog.name = "resgemv_gemv" if len(chunks) == 1 else f"resgemv_gemv_chunk{i}"
      gemv_progs.append(prog)

    add_prog = build_two_source_binary(
      "add", c_buf.addr, residual_buf.addr, next_buf.addr,
      num_banks, core=core, tiles=out_tiles)
    add_prog.name = "resgemv_residual_add"

    times = []
    for _ in range(args.runs):
      for prog in (*gemv_progs, add_prog):
        times.extend(device.run(prog))

    c_raw = device.dram_read(c_buf)
    next_raw = device.dram_read(next_buf)

  pcc, rel_l2 = mm.validate(a_ref, b_ref, c_raw, 1, args.n, Mp, Np)
  c_full = mm.from_bf16_device_bytes(c_raw, (Mp, Np))
  next_got = row_tiles_to_vector(next_raw, out_tiles, args.n)
  next_ref = elw.to_bf16(c_full[0, :args.n] + residual_bf16)
  max_abs = float(np.max(np.abs(next_got - next_ref)))
  atol, rtol = elw.TOL["add"]
  add_ok = bool(np.allclose(next_got, next_ref, atol=atol, rtol=rtol))
  ok = pcc >= mm.PCC_THRESHOLD and rel_l2 <= mm.REL_L2_THRESHOLD and add_ok

  print("staged device GEMV -> residual add")
  print(f"  K={args.k} N={args.n} runs={args.runs} gemv_chunks={len(chunks)}")
  if times:
    print(f"  launches={(len(gemv_progs) + 1) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  GEMV: pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  print(f"  residual add: {'PASS' if add_ok else 'FAIL'} max_abs={max_abs:.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
