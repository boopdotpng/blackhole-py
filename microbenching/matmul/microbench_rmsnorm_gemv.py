#!/usr/bin/env python3
"""Staged device RMSNorm producer into skinny GEMV.

This connects the current RMSNorm pieces without host arithmetic:

  x -> device inv_rms reduction
  norm_w * inv_rms -> device norm_scale vector
  x * norm_scale -> tilized M=1 GEMV A buffer
  GEMV(A, W)

The launches are intentionally separate for now. The point of this proof is
device residency for the RMSNorm scalar and scale vector; launch minimization
can fold these stages once the data contract is stable.
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
import microbench_eltwise_bcast as bcast  # noqa: E402
import microbench_eltwise_binary as elw  # noqa: E402
import microbench_rmsnorm_inv as rms  # noqa: E402
import numpy as np

from dsl import a0, a1, a2, a5, s0, s1, s2, s3, s4, s5, t0, t1, t2, t4, t5, t6, zero
from examples import add1  # noqa: E402
from examples.add1 import Brisc, CB_DEPTH, OUT_CB, TILE_BYTES  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC  # noqa: E402

TILE = 32


def vector_to_row_tiles(vec: np.ndarray, k_padded: int) -> np.ndarray:
  tiles = np.zeros((k_padded // TILE, TILE, TILE), dtype=np.float32)
  v = np.zeros(k_padded, dtype=np.float32)
  v[:vec.size] = vec
  for tile in range(k_padded // TILE):
    tiles[tile, 0, :] = v[tile * TILE:(tile + 1) * TILE]
  return tiles


def vector_to_footprint_tiles(vec: np.ndarray) -> np.ndarray:
  if vec.size % TILE:
    raise ValueError("footprint vector length must be a multiple of 32")
  tiles = np.zeros((vec.size // TILE, TILE, TILE), dtype=np.float32)
  for tile in range(vec.size // TILE):
    rms.footprint_put(tiles[tile], vec[tile * TILE:(tile + 1) * TILE])
  return tiles


def brisc_two_source(*, b_fixed: bool) -> Brisc:
  """BRISC feeder for eltwise AB where A and B live in separate buffers."""
  fw = Brisc()
  # RTAs: A base, B base, base tile offset, tiles, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4))
  for addr in (
    elw.SYNC_TRISC_START, elw.SYNC_READ, elw.SYNC_DONE0, elw.SYNC_DONE1,
    add1.SYNC_DONE2, elw.SYNC_TRISC_INIT, elw.SYNC_TRISC_INIT + 4,
    elw.SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(elw.SYNC_TRISC_START, 0x00010101)

  with fw.tile_loop("brisc"):
    for cb in (0, 1):
      fw.cb_reserve_back(BM.CB_INTERFACE, cb)
      fw.mv(a0, s0 if cb == 0 else s1)
      if cb == 0:
        fw.add(a1, s2, s5)
      elif b_fixed:
        fw.li(a1, 0)
      else:
        fw.add(a1, s2, s5)
      fw.mv(a2, s4)
      fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
      fw.local_noc0_coord(a5)
      fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      fw.addi(t4, t4, 1)
      fw.cb_write_ptr(BM.CB_INTERFACE, cb, out=t5)
      fw.li(t6, TILE_BYTES)
      fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
      fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
      fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      wait = fw._new_label(f"brisc_read_wait{cb}")
      fw.label(wait)
      fw.lw(t1, t0, 0)
      fw.bltu(t1, t4, wait)
      fw.fence()
      fw.cb_push_back(BM.CB_INTERFACE, cb)
    fw.addi(t2, s5, 1)
    fw.signal_sync(elw.SYNC_READ, t2)
  return fw


def build_two_source_bcast(
    op: str,
    variant: str,
    a_addr: int,
    b_addr: int,
    dst_addr: int,
    num_banks: int,
    *,
    core,
    tiles: int,
    b_fixed: bool = False,
) -> Program:
  unpack_mop, math_fn, ab, runs, between, post = bcast.VARIANTS[variant]
  brisc_fw = brisc_two_source(b_fixed=b_fixed)
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = elw.trisc0(unpack_mop)
  trisc1_fw = elw.trisc1(
    op,
    math_mop=math_fn(op),
    addr_mod_ab=ab,
    mop_runs=runs,
    between_runs=between,
    post_mop=post,
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
  prog.name = f"two_src_{variant}_{op}"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="staged device RMSNorm -> GEMV proof; needs device")
  p.add_argument("--k", type=int, default=2048)
  p.add_argument("--n", type=int, default=3072)
  p.add_argument("--eps", type=float, default=1.0e-5)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()
  if args.k % TILE:
    raise ValueError("--k must be a multiple of 32")

  rng = np.random.default_rng(83)
  x = rng.uniform(-2.0, 2.0, size=args.k).astype(np.float32)
  norm_w = rng.uniform(0.5, 1.5, size=args.k).astype(np.float32)
  w = rng.uniform(-0.5, 0.5, size=(args.k, args.n)).astype(np.float32)
  x_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(x), x.shape)
  norm_w_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(norm_w), norm_w.shape)
  w_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(w), w.shape)
  inv_ref = np.float32(1.0 / np.sqrt(np.mean(x_bf16.astype(np.float32) ** 2) + np.float32(args.eps)))
  normed_ref = mm.from_bf16_device_bytes(
    mm.to_bf16_device_bytes(x_bf16 * norm_w_bf16 * inv_ref), (args.k,))

  with harness.open_device() as device:
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    ys = sorted({y for _, y in device.cores})[:1]
    cores = [c for c in device.cores if c[1] in ys]
    chunks = mm.plan_output_chunks(1, args.k, args.n, cores, num_banks)
    if len(chunks) != 1:
      raise ValueError(f"this proof expects one GEMV chunk, got {len(chunks)}")
    chunk = chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(1, args.k, args.n, chunks)
    k_tiles = Kp // TILE

    x_rms_buf = device.alloc_write(
      rms.to_bf16_bytes(vector_to_footprint_tiles(x_bf16)),
      dtype=Dtype.Float16_b,
      shape=(args.k // TILE, TILE, TILE),
      name="rmsgemv_x_rms",
    )
    x_row_buf = device.alloc_write(
      elw.to_bf16_bytes(vector_to_row_tiles(x_bf16, Kp)),
      dtype=Dtype.Float16_b,
      shape=(k_tiles, TILE, TILE),
      name="rmsgemv_x_row",
    )
    norm_w_buf = device.alloc_write(
      elw.to_bf16_bytes(vector_to_row_tiles(norm_w_bf16, Kp)),
      dtype=Dtype.Float16_b,
      shape=(k_tiles, TILE, TILE),
      name="rmsgemv_norm_w",
    )

    partials = args.k // TILE
    partial1_tiles = partials // TILE
    partial1_buf = device.dram.alloc(partial1_tiles, dtype=Dtype.Float16_b, name="rmsgemv_partial1")
    partial2_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, name="rmsgemv_partial2")
    inv_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, shape=(1, TILE, TILE), name="rmsgemv_inv")
    scale_buf = device.dram.alloc(k_tiles, dtype=Dtype.Float16_b,
                                  shape=(k_tiles, TILE, TILE), name="rmsgemv_scale")
    a_buf = device.dram.alloc((Mp // TILE) * (Kp // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Kp), name="rmsgemv_a")
    device.dram_write(a_buf, b"\0" * (Mp * Kp * 2))

    wp = np.zeros((Kp, Np), dtype=np.float32)
    wp[:args.k, :args.n] = w_bf16
    b_buf = device.alloc_write(mm.to_bf16_device_bytes(wp), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="rmsgemv_w")
    c_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Np), name="rmsgemv_c")

    rms1 = rms.build_reduce_program(x_rms_buf.addr, partial1_buf.addr, num_banks, core=core,
                                    tiles=partials, square=True, compact=True)
    rms1.name = "rmsgemv_sumsq_partials"
    rms2 = rms.build_reduce_program(partial1_buf.addr, partial2_buf.addr, num_banks, core=core,
                                    tiles=partial1_tiles, square=False, compact=True)
    rms2.name = "rmsgemv_reduce_partials"
    rms3 = rms.build_reduce_program(partial2_buf.addr, inv_buf.addr, num_banks, core=core,
                                    tiles=1, square=False, compact=False,
                                    final=True, k=args.k, eps=args.eps)
    rms3.name = "rmsgemv_inv"
    scale_prog = build_two_source_bcast(
      "mul", "scalar", norm_w_buf.addr, inv_buf.addr, scale_buf.addr,
      num_banks, core=core, tiles=k_tiles, b_fixed=True)
    scale_prog.name = "rmsgemv_norm_w_times_inv"
    norm_prog = build_two_source_bcast(
      "mul", "row", x_row_buf.addr, scale_buf.addr, a_buf.addr,
      num_banks, core=core, tiles=k_tiles, b_fixed=False)
    norm_prog.name = "rmsgemv_x_times_scale_to_a"
    layout = mm.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    gemv_prog = mm.build_program(chunk.plan, a_buf.addr, b_buf.addr, c_buf.addr, num_banks, layout)
    gemv_prog.name = "rmsgemv_gemv"

    times = []
    for _ in range(args.runs):
      device.dram_write(partial1_buf, b"\0" * partial1_buf.size)
      device.dram_write(partial2_buf, b"\0" * partial2_buf.size)
      for prog in (rms1, rms2, rms3, scale_prog, norm_prog, gemv_prog):
        times.extend(device.run(prog))
    inv_raw = device.dram_read(inv_buf)
    a_raw = device.dram_read(a_buf)
    c_raw = device.dram_read(c_buf)

  inv_tile = rms.from_bf16_bytes(inv_raw, (1, TILE, TILE))[0]
  inv_got = float(rms.footprint_values(inv_tile)[0])
  got_a = mm.from_bf16_device_bytes(a_raw, (Mp, Kp))
  expected_a = np.zeros((Mp, Kp), dtype=np.float32)
  expected_a[0, :args.k] = normed_ref
  a_ok = bool(np.allclose(got_a, expected_a, atol=7.5e-2, rtol=7.5e-2))
  pcc, rel_l2 = mm.validate(got_a[:1, :args.k], w_bf16[:, :args.n], c_raw, 1, args.n, Mp, Np)
  ok = a_ok and pcc >= mm.PCC_THRESHOLD and rel_l2 <= mm.REL_L2_THRESHOLD

  print("staged device RMSNorm -> GEMV")
  print(f"  K={args.k} N={args.n} runs={args.runs} eps={args.eps:g}")
  if times:
    print(f"  launches={6 * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  inv_rms device={inv_got:.6f} ref={float(inv_ref):.6f}")
  print(f"  A buffer: {'PASS' if a_ok else 'FAIL'}")
  print(f"  GEMV: pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
