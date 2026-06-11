#!/usr/bin/env python3
"""RoPE + K-cache scatter composite proof.

This is the K-side companion to the QKV V-cache tail fusion. V can be scattered
directly from QKV output, but K must be RoPE-rotated first. This bench stages
one K head per tile as four SFPU footprints (x1, x2, cos, sin), runs the
validated RoPE SFPU sequence, then has NCRISC compact the rotated x1/x2 lanes
from the packed output tile into ``k_cache[head, pos]``.

It is intentionally a small single-core composite proof, not the final
multi-head integration kernel.
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
  TTMOP, TTSEMPOST, TTSETRWC, TTSEMWAIT, TTSTALLWAIT,
  a0, a1, a2, a3, a4, a5, s0, s2, s3, s4, s5, t0, t1, t2, t4, t5, t6,
)
from examples import add1  # noqa: E402
from examples.add1 import (
  Brisc, CB_DEPTH, OUT_CB, STALL_MATH_PACK_ROOM, SYNC, SYNC_DONE1, TILE_BYTES,
  Trisc, WAIT_MATH_AND_SFPU, write_trisc1_dest_offset_instr,
)
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import NcriscMailbox as NM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.sfpu import rope_rotate_row_seq  # noqa: E402
from ttk.tensix import TensixL1, TensixSem, TensixSemWait, TensixStall, TensixWait  # noqa: E402

TILE = 32
HEAD_DIM = 64
ROW_BYTES = HEAD_DIM * 2
PAGE = Dtype.Float16_b.tile_size

X1_OFF = 0
X2_OFF = 4
COS_OFF = 8
SIN_OFF = 12
SCRATCH_L1 = add1.SYNC_L1 + 0x100


def to_bf16(x: np.ndarray) -> np.ndarray:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return ((u >> 16).astype("<u4") << 16).view("<f4")


def to_bf16_bytes(x: np.ndarray) -> bytes:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return (u >> 16).astype("<u2").tobytes()


def from_bf16_u16(u16: np.ndarray) -> np.ndarray:
  return (u16.astype("<u4") << 16).view("<f4")


def footprint_put(tile: np.ndarray, base: int, values: np.ndarray) -> None:
  for lane, value in enumerate(values.astype(np.float32)):
    row = base + lane // 8
    col = (lane & 7) * 2
    tile[row, col] = value


def packed_elem_offset(row: int, col: int) -> int:
  face = (row // 16) * 2 + (col // 16)
  elem = face * 16 * 16 + (row % 16) * 16 + (col % 16)
  return elem * 2


def trisc1_rope() -> Trisc:
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
    write_trisc1_dest_offset_instr(fw, t1, t2, t4)
    fw.emit(TTMOP(1, 0, 0))  # SrcA tile -> dest rows 0..31.
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t4)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    for inst in rope_rotate_row_seq(x1_addr=X1_OFF, x2_addr=X2_OFF, cos_addr=COS_OFF, sin_addr=SIN_OFF):
      fw.emit(inst)
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
    write_trisc1_dest_offset_instr(fw, t2, t1, t4)
  return fw


def emit_compact_group(fw, *, l1_tile, base_row: int, scratch_off: int) -> None:
  for lane in range(32):
    row = base_row + lane // 8
    col = (lane & 7) * 2
    fw.lhu(t1, l1_tile, packed_elem_offset(row, col))
    fw.li(t2, SCRATCH_L1 + scratch_off + lane * 2)
    fw.sh(t1, t2, 0)


def ncrisc_k_scatter(max_seq: int) -> add1.Ncrisc:
  rows_per_head = max_seq * ROW_BYTES
  fw = add1.Ncrisc()
  # RTAs: cache base, pos, tiles/heads, bank count.
  fw.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  with fw.tile_loop("ncrisc"):
    fw.cb_wait_front(NM.CB_INTERFACE, OUT_CB)
    fw.cb_read_ptr(NM.CB_INTERFACE, OUT_CB, out=t5)

    emit_compact_group(fw, l1_tile=t5, base_row=X1_OFF, scratch_off=0)
    emit_compact_group(fw, l1_tile=t5, base_row=X2_OFF, scratch_off=64)

    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT))
    fw.addi(t4, t4, 1)
    fw.li(a1, rows_per_head)
    fw.mul(a1, a1, s5)
    fw.slli(a4, s2, 7)  # pos * 128 bytes.
    fw.add(a1, a1, a4)
    fw.andi(a4, a1, PAGE - 1)
    fw.srli(a1, a1, 11)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s4)
    fw.add(a0, a0, a4)
    fw.li(a3, SCRATCH_L1)
    fw.li(a5, ROW_BYTES)
    fw.noc_write(1, 0, a3, a0, 0, a2, a5, a=t0, v=t1)
    fw.noc_write_barrier(1, t4, addr=t0, val=t1)
    fw.cb_pop_front(NM.CB_INTERFACE, OUT_CB)
  return fw


def build_program(src_addr: int, cache_addr: int, pos: int, max_seq: int,
                  num_banks: int, *, core, heads: int) -> Program:
  brisc_fw = add1.brisc()
  ncrisc_fw = ncrisc_k_scatter(max_seq)
  trisc0_fw = add1.trisc0()
  trisc1_fw = trisc1_rope()
  trisc2_fw = add1.trisc2()

  brisc_fw.rta(lambda _x, _y: [src_addr, 0, heads, num_banks])
  ncrisc_fw.rta(lambda _x, _y: [cache_addr, pos() if callable(pos) else pos, heads, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [heads])

  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "rope_k_scatter"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="RoPE + K-cache scatter composite; needs device")
  p.add_argument("--heads", type=int, default=8)
  p.add_argument("--max-seq", type=int, default=64)
  p.add_argument("--pos", type=int, default=17)
  p.add_argument("--runs", type=int, default=1)
  args = p.parse_args()
  if args.max_seq % (PAGE // ROW_BYTES) != 0:
    raise ValueError("--max-seq must keep each head cache region page-aligned")
  if args.pos >= args.max_seq:
    raise ValueError("--pos must be < --max-seq")

  rng = np.random.default_rng(61)
  k = to_bf16(rng.uniform(-2.0, 2.0, size=(args.heads, HEAD_DIM)).astype(np.float32))
  cos = to_bf16(rng.uniform(-1.0, 1.0, size=(args.heads, HEAD_DIM // 2)).astype(np.float32))
  sin = to_bf16(rng.uniform(-1.0, 1.0, size=(args.heads, HEAD_DIM // 2)).astype(np.float32))
  src = np.zeros((args.heads, TILE, TILE), dtype=np.float32)
  for h in range(args.heads):
    footprint_put(src[h], X1_OFF, k[h, :32])
    footprint_put(src[h], X2_OFF, k[h, 32:])
    footprint_put(src[h], COS_OFF, cos[h])
    footprint_put(src[h], SIN_OFF, sin[h])

  ref = np.empty_like(k)
  ref[:, :32] = k[:, :32] * cos - k[:, 32:] * sin
  ref[:, 32:] = k[:, 32:] * cos + k[:, :32] * sin
  ref_bf16 = to_bf16(ref)

  with harness.open_device() as device:
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    src_buf = device.alloc_write(to_bf16_bytes(src), dtype=Dtype.Float16_b,
                                 shape=src.shape, name="rope_k_src")
    cache_tiles = args.heads * args.max_seq * ROW_BYTES // PAGE
    k_buf = device.dram.alloc(cache_tiles, dtype=Dtype.Float16_b, name="k_cache")
    device.dram_write(k_buf, b"\0" * k_buf.size)
    prog = build_program(src_buf.addr, k_buf.addr, args.pos, args.max_seq,
                         num_banks, core=core, heads=args.heads)
    timings = []
    for _ in range(args.runs):
      timings.extend(device.run(prog))
    raw = device.dram_read(k_buf)

  got_u16 = np.frombuffer(raw, dtype=np.uint16).reshape(args.heads, args.max_seq, HEAD_DIM)
  got = from_bf16_u16(got_u16[:, args.pos, :])
  untouched = bool(np.all(got_u16[:, :args.pos, :] == 0) and np.all(got_u16[:, args.pos + 1:, :] == 0))
  ok_vals = bool(np.allclose(got, ref_bf16, atol=5.0e-2, rtol=5.0e-2))
  ok = ok_vals and untouched

  print("RoPE + K-cache scatter composite")
  print(f"  heads={args.heads} pos={args.pos} max_seq={args.max_seq} runs={args.runs}")
  if timings:
    print(f"  launch avg={sum(t['us'] for t in timings) / len(timings):.1f} us")
  print(f"  K cache row: {'PASS' if ok_vals else 'FAIL'}")
  if not ok_vals:
    diff = np.abs(got - ref_bf16)
    h, d = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    max diff head={h} dim={d} got={float(got[h, d]):.6g} ref={float(ref_bf16[h, d]):.6g}")
    print(f"    got head0[:8]={got[0, :8].tolist()}")
    print(f"    ref head0[:8]={ref_bf16[0, :8].tolist()}")
  print(f"  untouched rows: {'PASS' if untouched else 'FAIL'}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
