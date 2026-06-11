#!/usr/bin/env python3
"""Device norm-scale bridge into skinny GEMV.

Llama's normalized projections consume:

  xn[i] = x[i] * norm_w[i] * inv_rms

The final fused kernel should compute inv_rms on device too. This bench proves
the next handoff: a device broadcast-mul stream writes ``x * norm_scale`` into
the exact tilized M=1 A-buffer layout consumed by the existing skinny GEMV.

For now ``norm_scale`` is supplied as a vector (norm_w * inv_rms). That keeps
the focus on removing host ``normed()`` materialization and the host GEMV-input
upload; the remaining RMS reduction can be swapped in as the producer of
``norm_scale``/scalar later.
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
import microbench_eltwise_bcast as bcast  # noqa: E402
import microbench_eltwise_binary as elw  # noqa: E402
import matmul_peak as mm  # noqa: E402
import numpy as np

from program import Dtype

TILE = 32


def vector_to_row_tiles(vec: np.ndarray, k_padded: int) -> np.ndarray:
  """Return tiles with vector chunks in row 0 and padded rows zero."""
  tiles = np.zeros((k_padded // TILE, TILE, TILE), dtype=np.float32)
  v = np.zeros(k_padded, dtype=np.float32)
  v[:vec.size] = vec
  for tile in range(k_padded // TILE):
    tiles[tile, 0, :] = v[tile * TILE:(tile + 1) * TILE]
  return tiles


def main() -> int:
  p = argparse.ArgumentParser(description="device norm-scale bridge into GEMV; needs device")
  p.add_argument("--k", type=int, default=2048)
  p.add_argument("--n", type=int, default=3072)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()

  rng = np.random.default_rng(41)
  x = rng.uniform(-2.0, 2.0, size=args.k).astype(np.float32)
  norm_w = rng.uniform(0.5, 1.5, size=args.k).astype(np.float32)
  # Use a plausible RMS scalar range, but keep it host-supplied in this bridge.
  inv_rms = np.float32(1.0 / np.sqrt(np.mean(x.astype(np.float32) ** 2) + 1.0e-5))
  norm_scale = (norm_w * inv_rms).astype(np.float32)
  w = rng.uniform(-0.5, 0.5, size=(args.k, args.n)).astype(np.float32)

  x_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(x), x.shape)
  scale_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(norm_scale), norm_scale.shape)
  w_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(w), w.shape)

  with harness.open_device() as device:
    num_banks = len(device.dram.bank_tiles)
    ys = sorted({y for _, y in device.cores})[:1]
    cores = [c for c in device.cores if c[1] in ys]
    chunks = mm.plan_output_chunks(1, args.k, args.n, cores, num_banks)
    if len(chunks) != 1:
      raise ValueError(f"this bridge bench expects one output chunk, got {len(chunks)}")
    chunk = chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(1, args.k, args.n, chunks)

    x_tiles = vector_to_row_tiles(x_bf16, Kp)
    scale_tiles = vector_to_row_tiles(scale_bf16, Kp)
    src = np.empty((2 * (Kp // TILE), TILE, TILE), dtype=np.float32)
    src[0::2] = x_tiles
    src[1::2] = scale_tiles
    src_buf = device.alloc_write(elw.to_bf16_bytes(src), dtype=Dtype.Float16_b,
                                 shape=src.shape, name="normscale_src")
    a_buf = device.dram.alloc((Mp // TILE) * (Kp // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Kp), name="normscale_a")
    device.dram_write(a_buf, b"\0" * (Mp * Kp * 2))

    scale_prog = bcast.base.build_program(
      "mul", src_buf.addr, a_buf.addr, num_banks,
      core=device.cores[0], tiles=Kp // TILE,
      unpack_mop=bcast.UNPACK_ROW_MOP,
      trisc1_kwargs=dict(
        math_mop=bcast.math_row_mop("mul"),
        addr_mod_ab=0x0008,
        mop_runs=1,
        between_runs=None,
        post_mop=None,
      ),
    )
    scale_prog.name = "normscale_to_a"

    wp = np.zeros((Kp, Np), dtype=np.float32)
    wp[:args.k, :args.n] = w_bf16
    b_buf = device.alloc_write(mm.to_bf16_device_bytes(wp), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="normscale_w")
    c_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Np), name="normscale_c")
    layout = mm.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    gemv_prog = mm.build_program(chunk.plan, a_buf.addr, b_buf.addr, c_buf.addr, num_banks, layout)
    gemv_prog.name = "normscale_gemv"

    scale_times, gemv_times = [], []
    for _ in range(args.runs):
      scale_times.extend(device.run(scale_prog))
      gemv_times.extend(device.run(gemv_prog))
    a_raw = device.dram_read(a_buf)
    c_raw = device.dram_read(c_buf)

  expected_a = np.zeros((Mp, Kp), dtype=np.float32)
  expected_a[0, :args.k] = mm.from_bf16_device_bytes(
    mm.to_bf16_device_bytes(x_bf16 * scale_bf16), (args.k,))
  got_a = mm.from_bf16_device_bytes(a_raw, (Mp, Kp))
  # LoFi eltwise mul is known to be a few percent low; check accordingly.
  a_ok = bool(np.allclose(got_a, expected_a, atol=5.0e-2, rtol=5.0e-2))
  ref_in = got_a[:1, :args.k]
  pcc, rel_l2 = mm.validate(ref_in, w_bf16[:, :args.n], c_raw, 1, args.n, Mp, Np)
  ok = a_ok and pcc >= mm.PCC_THRESHOLD and rel_l2 <= mm.REL_L2_THRESHOLD

  print("norm-scale -> GEMV bridge")
  print(f"  K={args.k} N={args.n} runs={args.runs} inv_rms={float(inv_rms):.6f}")
  if scale_times:
    print(f"  scale avg={sum(t['us'] for t in scale_times) / len(scale_times):.1f} us")
  if gemv_times:
    print(f"  gemv avg={sum(t['us'] for t in gemv_times) / len(gemv_times):.1f} us")
  print(f"  A buffer: {'PASS' if a_ok else 'FAIL'}")
  print(f"  GEMV: pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
