#!/usr/bin/env python3
"""Device RMSNorm scale bridge into skinny GEMV.

This removes the remaining host ``norm_scale = norm_w * inv_rms`` cheat from
the norm-scale GEMV proof. The staged device path is:

  1. device RMSNorm reduction computes inv_rms
  2. row-broadcast mul computes x * norm_w per K tile
  3. scalar-broadcast mul applies the device-produced inv_rms into GEMV's A
  4. skinny GEMV consumes the normalized A buffer

The stages are separate launches on purpose: this is about device residency and
stable composition first. Later we can fuse the easy producer boundaries.
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

from dsl import a0, a1, a2, a5, s0, s1, s3, s4, s5, t0, t1, t4, t5, t6, zero  # noqa: E402
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


def brisc_two_sources_fixed_b() -> Brisc:
  """Read A tile i into CB0 and the same scalar tile 0 into CB1 each loop."""
  fw = Brisc()
  # RTAs: A base, scalar/B base, tiles, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s3, s4))
  for addr in (
    elw.SYNC_TRISC_START, elw.SYNC_READ, elw.SYNC_DONE0, elw.SYNC_DONE1, add1.SYNC_DONE2,
    elw.SYNC_TRISC_INIT, elw.SYNC_TRISC_INIT + 4, elw.SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(elw.SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    for cb, base_reg, page_reg in ((0, s0, s5), (1, s1, zero)):
      fw.cb_reserve_back(BM.CB_INTERFACE, cb)
      fw.mv(a0, base_reg)
      fw.mv(a1, page_reg)
      fw.mv(a2, s4)
      fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
      fw.local_noc0_coord(a5)
      fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      fw.addi(t4, t4, 1)
      fw.cb_write_ptr(BM.CB_INTERFACE, cb, out=t5)
      fw.li(t6, TILE_BYTES)
      fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
      fw.noc_reads_flushed(0, t4, addr=t0, val=t1)
      fw.cb_push_back(BM.CB_INTERFACE, cb)
    fw.addi(t1, s5, 1)
    fw.signal_sync(elw.SYNC_READ, t1)
  return fw


def build_scalar_from_single_tile(a_addr: int, scalar_addr: int, dst_addr: int, num_banks: int,
                                  *, core, tiles: int) -> Program:
  brisc_fw = brisc_two_sources_fixed_b()
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = elw.trisc0(bcast.UNPACK_SCALAR_MOP)
  trisc1_fw = elw.trisc1(
    "mul",
    math_mop=bcast.math_scalar_mop("mul"),
    addr_mod_ab=0x0008,
    mop_runs=1,
    between_runs=None,
    post_mop=bcast.SETRWC_CLR_B_SETD,
  )
  trisc2_fw = add1.trisc2()
  brisc_fw.rta(lambda _x, _y: [a_addr, scalar_addr, tiles, num_banks])
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
  prog.name = "apply_inv_rms_to_a"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="device RMSNorm scale bridge into GEMV; needs device")
  p.add_argument("--k", type=int, default=2048)
  p.add_argument("--n", type=int, default=3072)
  p.add_argument("--eps", type=float, default=1.0e-5)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()
  if args.k % 32 != 0 or (args.k // 32) % 32 != 0:
    raise ValueError("this proof expects K multiple of 1024")

  rng = np.random.default_rng(83)
  x = rng.uniform(-2.0, 2.0, size=args.k).astype(np.float32)
  norm_w = rng.uniform(0.5, 1.5, size=args.k).astype(np.float32)
  w = rng.uniform(-0.5, 0.5, size=(args.k, args.n)).astype(np.float32)

  x_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(x), x.shape)
  norm_w_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(norm_w), norm_w.shape)
  w_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(w), w.shape)

  partials = args.k // 32
  rms_src = np.zeros((partials, TILE, TILE), dtype=np.float32)
  for i in range(partials):
    rms.footprint_put(rms_src[i], x_bf16[i * 32:(i + 1) * 32])
  ref_inv = np.float32(1.0 / np.sqrt(np.mean(x_bf16.astype(np.float32) ** 2) + np.float32(args.eps)))

  with harness.open_device() as device:
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    ys = sorted({y for _, y in device.cores})[:1]
    cores = [c for c in device.cores if c[1] in ys]
    chunks = mm.plan_output_chunks(1, args.k, args.n, cores, num_banks)
    if len(chunks) != 1:
      raise ValueError(f"this bridge bench expects one output chunk, got {len(chunks)}")
    chunk = chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(1, args.k, args.n, chunks)

    rms_src_buf = device.alloc_write(rms.to_bf16_bytes(rms_src), dtype=Dtype.Float16_b,
                                     shape=rms_src.shape, name="rms_x")
    partial1_tiles = partials // 32
    partial1_buf = device.dram.alloc(partial1_tiles, dtype=Dtype.Float16_b, name="rms_partial1")
    partial2_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, name="rms_partial2")
    inv_buf = device.dram.alloc(1, dtype=Dtype.Float16_b, shape=(1, TILE, TILE), name="rms_inv")

    prog1 = rms.build_reduce_program(rms_src_buf.addr, partial1_buf.addr, num_banks, core=core,
                                     tiles=partials, square=True, compact=True)
    prog1.name = "rms_sumsq_partials"
    prog2 = rms.build_reduce_program(partial1_buf.addr, partial2_buf.addr, num_banks, core=core,
                                     tiles=partial1_tiles, square=False, compact=True)
    prog2.name = "rms_reduce_partials"
    prog3 = rms.build_reduce_program(partial2_buf.addr, inv_buf.addr, num_banks, core=core,
                                     tiles=1, square=False, compact=False,
                                     final=True, k=args.k, eps=args.eps)
    prog3.name = "rms_inv"

    x_tiles = vector_to_row_tiles(x_bf16, Kp)
    nw_tiles = vector_to_row_tiles(norm_w_bf16, Kp)
    src = np.empty((2 * (Kp // TILE), TILE, TILE), dtype=np.float32)
    src[0::2] = x_tiles
    src[1::2] = nw_tiles
    xw_src_buf = device.alloc_write(elw.to_bf16_bytes(src), dtype=Dtype.Float16_b,
                                    shape=src.shape, name="rms_x_normw_src")
    xw_buf = device.dram.alloc(Kp // TILE, dtype=Dtype.Float16_b,
                               shape=(Kp // TILE, TILE, TILE), name="rms_xw")
    xw_prog = bcast.base.build_program(
      "mul", xw_src_buf.addr, xw_buf.addr, num_banks,
      core=core, tiles=Kp // TILE,
      unpack_mop=bcast.UNPACK_ROW_MOP,
      trisc1_kwargs=dict(
        math_mop=bcast.math_row_mop("mul"),
        addr_mod_ab=0x0008,
        mop_runs=1,
        between_runs=None,
        post_mop=None,
      ),
    )
    xw_prog.name = "rms_x_times_normw"

    a_buf = device.dram.alloc((Mp // TILE) * (Kp // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Kp), name="rmsnorm_a")
    apply_inv_prog = build_scalar_from_single_tile(xw_buf.addr, inv_buf.addr, a_buf.addr, num_banks,
                                                   core=core, tiles=Kp // TILE)

    wp = np.zeros((Kp, Np), dtype=np.float32)
    wp[:args.k, :args.n] = w_bf16
    b_buf = device.alloc_write(mm.to_bf16_device_bytes(wp), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="rmsnorm_w")
    c_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Np), name="rmsnorm_c")
    layout = mm.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    gemv_prog = mm.build_program(chunk.plan, a_buf.addr, b_buf.addr, c_buf.addr, num_banks, layout)
    gemv_prog.name = "rmsnorm_gemv"

    times = []
    for _ in range(args.runs):
      device.dram_write(partial1_buf, b"\0" * partial1_buf.size)
      device.dram_write(partial2_buf, b"\0" * partial2_buf.size)
      device.dram_write(a_buf, b"\0" * a_buf.size)
      for prog in (prog1, prog2, prog3, xw_prog, apply_inv_prog, gemv_prog):
        times.extend(device.run(prog))
    inv_raw = device.dram_read(inv_buf)
    a_raw = device.dram_read(a_buf)
    c_raw = device.dram_read(c_buf)

  inv_tile = rms.from_bf16_bytes(inv_raw, (1, TILE, TILE))[0]
  got_inv = float(rms.footprint_values(inv_tile)[0])
  inv_rel = abs(got_inv - float(ref_inv)) / max(abs(float(ref_inv)), 1.0e-12)
  got_a = mm.from_bf16_device_bytes(a_raw, (Mp, Kp))
  expected_a = np.zeros((Mp, Kp), dtype=np.float32)
  expected_a[0, :args.k] = mm.from_bf16_device_bytes(
    mm.to_bf16_device_bytes(x_bf16 * norm_w_bf16 * np.float32(got_inv)), (args.k,))
  a_ok = bool(np.allclose(got_a, expected_a, atol=8.0e-2, rtol=8.0e-2))
  pcc, rel_l2 = mm.validate(got_a[:1, :args.k], w_bf16[:, :args.n], c_raw, 1, args.n, Mp, Np)
  ok = inv_rel <= 5.0e-2 and a_ok and pcc >= mm.PCC_THRESHOLD and rel_l2 <= mm.REL_L2_THRESHOLD

  print("RMSNorm scale -> GEMV device bridge")
  print(f"  K={args.k} N={args.n} runs={args.runs}")
  if times:
    print(f"  launches={6 * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  inv_rms got={got_inv:.6f} ref={float(ref_inv):.6f} rel={inv_rel:.6f}")
  print(f"  A buffer: {'PASS' if a_ok else 'FAIL'}")
  print(f"  GEMV: pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
