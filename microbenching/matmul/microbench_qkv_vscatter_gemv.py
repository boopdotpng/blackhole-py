#!/usr/bin/env python3
"""QKV-sized GEMV with a fused V-cache scatter tail.

This is an easy-fusion proof for Llama decode: while the normal skinny-GEMV
NCRISC output writer has each packed QKV output tile in L1, copy row 0 of the V
slice directly into the row-major V cache at [kv_head][pos][head_dim]. K still
needs RoPE before cache write, so it belongs to a later RoPE+K-scatter composite.
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
import matmul_peak as mm  # noqa: E402
import numpy as np

from dsl import a0, a1, a2, a5, s8, s11, t0, t1, t2, t3, t6  # noqa: E402
from program import Dtype  # noqa: E402
from ttk.mailbox import NcriscMailbox as NM  # noqa: E402

TILE = 32
PAGE = Dtype.Float16_b.tile_size
ROW_HALF_BYTES = 16 * 2
TILE_ROW0_COL16_OFF = 16 * 16 * 2


def make_vscatter_hook(*, v_start_tile: int, v_tiles: int, max_seq: int,
                       head_dim: int):
  row_bytes = head_dim * 2
  head_dim_tiles = head_dim // TILE
  if head_dim_tiles != 2:
    raise ValueError("this proof hook assumes head_dim=64, i.e. two 32-wide tiles/head")
  if max_seq % (PAGE // row_bytes) != 0:
    raise ValueError("max_seq must make each head's cache rows page-aligned")

  def hook(fw, plan, *, tile_page, l1_tile):
    del plan
    done = fw._new_label("vscatter_done")
    fw.li(t0, v_start_tile)
    fw.bltu(tile_page, t0, done)
    fw.li(t1, v_start_tile + v_tiles)
    fw.bgeu(tile_page, t1, done)

    # Local V tile index -> cache byte offset:
    #   ((head * max_seq + pos) * row_bytes) + (tile_in_head * 64)
    fw.li(t0, v_start_tile)
    fw.sub(t6, tile_page, t0)
    fw.srli(t1, t6, 1)          # head = local_tile // 2
    fw.li(t2, max_seq * row_bytes)
    fw.mul(t1, t1, t2)
    fw.rta_ptr(NM.RTA_L1_BASE_PTR, out=t2)
    fw.arg(t3, 32, ptr=t2)      # pos
    fw.li(t2, row_bytes)
    fw.mul(t3, t3, t2)
    fw.add(t1, t1, t3)
    fw.andi(t2, t6, 1)          # tile_in_head
    fw.slli(t2, t2, 6)          # * 64 bytes
    fw.add(t1, t1, t2)

    fw.andi(t6, t1, PAGE - 1)
    fw.srli(a1, t1, 11)
    fw.rta_ptr(NM.RTA_L1_BASE_PTR, out=t2)
    fw.arg(a0, 31, ptr=t2)      # V-cache base
    fw.mv(a2, s11)              # DRAM bank count from normal output writer args
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, 0)
    fw.add(a0, a0, t6)

    fw.mv(t6, l1_tile)
    fw.li(a5, ROW_HALF_BYTES)
    fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
    fw.li(t6, TILE_ROW0_COL16_OFF)
    fw.add(t6, l1_tile, t6)
    fw.addi(a0, a0, ROW_HALF_BYTES)
    fw.li(a5, ROW_HALF_BYTES)
    fw.noc_write(mm.OUTPUT_NOC, 0, t6, a0, 0, a2, a5, a=t0, v=t2)
    fw.addi(s8, s8, 2)          # include the two cache writes in the output barrier
    mm.emit_output_write_state_setup(fw)
    fw.label(done)

  return hook


def main() -> int:
  p = argparse.ArgumentParser(description="QKV GEMV with fused V-cache scatter tail; needs device")
  p.add_argument("--k", type=int, default=2048)
  p.add_argument("--n", type=int, default=3072)
  p.add_argument("--dim", type=int, default=2048)
  p.add_argument("--kv-dim", type=int, default=512)
  p.add_argument("--n-kv-heads", type=int, default=8)
  p.add_argument("--head-dim", type=int, default=64)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()

  if args.dim + 2 * args.kv_dim != args.n:
    raise ValueError("--n must equal dim + 2*kv_dim for fused QKV output")
  if args.n_kv_heads * args.head_dim != args.kv_dim:
    raise ValueError("n_kv_heads * head_dim must equal kv_dim")
  if args.pos >= args.max_seq:
    raise ValueError("--pos must be < --max-seq")

  rng = np.random.default_rng(53)
  a = rng.uniform(-2.0, 2.0, size=(1, args.k)).astype(np.float32)
  b = rng.uniform(-0.5, 0.5, size=(args.k, args.n)).astype(np.float32)
  a_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(a), a.shape)
  b_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(b), b.shape)

  with harness.open_device() as device:
    num_banks = len(device.dram.bank_tiles)
    ys = sorted({y for _, y in device.cores})[:1]
    cores = [c for c in device.cores if c[1] in ys]
    chunks = mm.plan_output_chunks(1, args.k, args.n, cores, num_banks)
    if len(chunks) != 1:
      raise ValueError(f"this proof bench expects one output chunk, got {len(chunks)}")
    chunk = chunks[0]
    Mp, Kp, Np = mm.global_padded_shape(1, args.k, args.n, chunks)

    ap = np.zeros((Mp, Kp), dtype=np.float32)
    ap[:1, :args.k] = a_bf16
    bp = np.zeros((Kp, Np), dtype=np.float32)
    bp[:args.k, :args.n] = b_bf16
    a_buf = device.alloc_write(mm.to_bf16_device_bytes(ap), dtype=Dtype.Float16_b,
                               shape=(Mp, Kp), name="qkv_vscatter_a")
    b_buf = device.alloc_write(mm.to_bf16_device_bytes(bp), dtype=Dtype.Float16_b,
                               shape=(Kp, Np), name="qkv_vscatter_w")
    c_buf = device.dram.alloc((Mp // TILE) * (Np // TILE), dtype=Dtype.Float16_b,
                              shape=(Mp, Np), name="qkv_vscatter_c")
    cache_tiles = args.n_kv_heads * args.max_seq * args.head_dim * 2 // PAGE
    v_buf = device.dram.alloc(cache_tiles, dtype=Dtype.Float16_b, name="v_cache")
    device.dram_write(v_buf, b"\0" * v_buf.size)

    layout = mm.TensorLayout(
      m_tile_offset=chunk.m_tile_offset,
      n_tile_offset=chunk.n_tile_offset,
      a_row_stride=Kp // TILE,
      b_row_stride=Np // TILE,
      c_row_stride=Np // TILE,
    )
    v_start_tile = (args.dim + args.kv_dim) // TILE
    hook = make_vscatter_hook(
      v_start_tile=v_start_tile,
      v_tiles=args.kv_dim // TILE,
      max_seq=args.max_seq,
      head_dim=args.head_dim,
    )
    prog = mm.build_program(
      chunk.plan, a_buf.addr, b_buf.addr, c_buf.addr, num_banks, layout,
      output_tile_hook=hook,
      writer_arg_extra=lambda _x, _y: [v_buf.addr, args.pos],
    )
    prog.name = "qkv_gemv_vscatter"

    timings = []
    for _ in range(args.runs):
      timings.extend(device.run(prog))
    c_raw = device.dram_read(c_buf)
    v_raw = device.dram_read(v_buf)

  pcc, rel_l2 = mm.validate(a_bf16, b_bf16, c_raw, 1, args.n, Mp, Np)
  c_u16 = np.frombuffer(c_raw, dtype=np.uint16).reshape(Mp, Np)
  got_v = np.frombuffer(v_raw, dtype=np.uint16).reshape(args.n_kv_heads, args.max_seq, args.head_dim)
  expected_v = c_u16[0, args.dim + args.kv_dim:args.dim + 2 * args.kv_dim].reshape(
    args.n_kv_heads, args.head_dim)
  v_ok = bool(np.array_equal(got_v[:, args.pos, :], expected_v))
  untouched_before = bool(np.all(got_v[:, :args.pos, :] == 0))
  untouched_after = bool(np.all(got_v[:, args.pos + 1:, :] == 0))
  ok = pcc >= mm.PCC_THRESHOLD and rel_l2 <= mm.REL_L2_THRESHOLD and v_ok and untouched_before and untouched_after

  print("QKV GEMV + fused V-cache scatter")
  print(f"  K={args.k} N={args.n} pos={args.pos} max_seq={args.max_seq} runs={args.runs}")
  if timings:
    print(f"  launch avg={sum(t['us'] for t in timings) / len(timings):.1f} us")
  print(f"  GEMV: pcc={pcc:.6f} rel_l2={rel_l2:.6f}")
  print(f"  V cache row: {'PASS' if v_ok else 'FAIL'}")
  if not v_ok:
    diff = got_v[:, args.pos, :] != expected_v
    h, d = np.argwhere(diff)[0]
    print(f"    first mismatch head={int(h)} dim={int(d)} "
          f"got=0x{int(got_v[h, args.pos, d]):04x} ref=0x{int(expected_v[h, d]):04x}")
    print(f"    got head0[:8]={[hex(int(x)) for x in got_v[0, args.pos, :8]]}")
    print(f"    ref head0[:8]={[hex(int(x)) for x in expected_v[0, :8]]}")
  print(f"  V cache untouched rows: {'PASS' if untouched_before and untouched_after else 'FAIL'}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
