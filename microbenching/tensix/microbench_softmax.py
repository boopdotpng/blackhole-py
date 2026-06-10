#!/usr/bin/env python3
"""Blackhole softmax microbench: per-row softmax of a 32x32 tile, bf16.

Composite of the individually-benched primitives (rowmax 293 cyc/tile, exp 40
cyc/group, sum 51 cyc/group, recip 16 cyc/group): all-SFPU, no SrcB needed,
runs in dest on the add1 single-CB pipeline (mova2d MOP copies the tile to
dest, then TRISC1's SFPU does max-reduce -> exp(x-max) -> sum -> recip-mul
in place; pack drains rows 0..31).

The composite overwrites its input, so it is NOT idempotent across the
4-calls-per-tile math_add1_replay_row hook; this bench uses a custom TRISC1
that runs the body once per tile. The 32 exp groups would not fit the IRAM
unrolled, so the per-band (4 rows x 32 cols) sequence runs in a RISC loop
with the dest offsets of SFPLOAD/SFPSTORE patched in (offset is the low bits
of the raw word). exp(x-max) goes to a scratch tile at dest rows +64 (pack
never sees it).

--iters N adds a timed N-tile stream with wall-clock around TRISC1's loop.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import numpy as np

from device import Device
from dsl import (
  TTMOP, TTSEMPOST, TTSEMWAIT, TTSETRWC, TTSFPADD, TTSFPLOAD, TTSFPMAD,
  TTSFPMOV, TTSFPMUL, TTSFPNOP, TTSFPSHFT2, TTSFPSTORE, TTSFPSWAP,
  TTSTALLWAIT,
  a2, a3, a4, a5, s5, s8, s9, t1, t2, t3, t6, zero,
)
from program import Dtype, Program
from ttk.tensix import (
  TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait,
)
from ttk.sfpu import SFPSWAP_ALL_ROWS_MAX, sfpu_exp, sfpu_reciprocal

from examples import add1
from examples.add1 import (
  Brisc, CB_DEPTH, OUT_CB, STALL_MATH_PACK_ROOM, SYNC, SYNC_DONE0, SYNC_DONE1,
  TILE_BYTES, Trisc, WAIT_MATH_AND_SFPU, write_trisc1_dest_offset_instr,
)

TILE = 32
DTYPE = Dtype.Float16_b
RESULT_ADDR = 0x12D000
FMT, AMOD = 2, 7          # bf16, absolute dest offsets (as rowmax helper)
SCRATCH = 64              # exp(x-max) staging tile, dest rows 64..95
COL_OFF = (0, 2, 16, 18)  # 4-row x 8-col groups: face0 even/odd, face1 even/odd


def _push_off(fw, inst, off_reg):
  """Push a Tensix instr with `off_reg` added to its dest-offset field."""
  fw.li(t1, inst.raw_word())
  fw.add(t1, t1, off_reg)
  fw.sw(t1, t6, 0)


def softmax_band(fw, off_reg):
  """Softmax rows B..B+3 (cols 0..31), B in off_reg. Clobbers L0..L7, t1."""
  for lreg, off in zip(range(4), COL_OFF):
    _push_off(fw, TTSFPLOAD(lreg, FMT, AMOD, off), off_reg)
  for a, b in ((0, 2), (1, 3), (0, 1)):
    fw.emit(TTSFPSWAP(0, a, b, SFPSWAP_ALL_ROWS_MAX))
    fw.emit(TTSFPNOP())
  for k in (4, 2, 1):  # broadcast max across each 8-lane row (rotates, no 0s)
    fw.emit(TTSFPMOV(0, 0, 1, 0))
    for _ in range(k):
      fw.emit(TTSFPSHFT2(0, 1, 1, 3))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
    fw.emit(TTSFPNOP())
  fw.emit(TTSFPMOV(0, 0, 7, 0))  # L7 = row max
  for i, off in enumerate(COL_OFF):
    _push_off(fw, TTSFPLOAD(0, FMT, AMOD, off), off_reg)
    fw.emit(TTSFPMAD(7, 10, 0, 0, 1))  # x - max
    fw.emit(TTSFPNOP())
    sfpu_exp(fw, 0, 0, scratch=(1, 2, 3, 4))  # preserves L6/L7
    _push_off(fw, TTSFPSTORE(0, FMT, AMOD, SCRATCH + off), off_reg)
    fw.emit(TTSFPMOV(0, 0, 6, 0) if i == 0 else TTSFPADD(10, 6, 0, 6, 0))
    fw.emit(TTSFPNOP())
  fw.emit(TTSFPMOV(0, 6, 1, 0))  # rotate-accumulate row sum into all lanes
  for _ in range(7):
    fw.emit(TTSFPSHFT2(0, 1, 2, 3))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPADD(10, 6, 2, 6, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMOV(0, 2, 1, 0))
  sfpu_reciprocal(fw, 6, 6, scratch=(1, 2, 3), iterations=2)
  for off in COL_OFF:
    _push_off(fw, TTSFPLOAD(0, FMT, AMOD, SCRATCH + off), off_reg)
    fw.emit(TTSFPMUL(0, 6, 9, 0, 0))
    fw.emit(TTSFPNOP())
    _push_off(fw, TTSFPSTORE(0, FMT, AMOD, off), off_reg)


def trisc1(*, timed: bool = False) -> Trisc:
  """add1's trisc1 with the softmax body run ONCE per tile (RISC band loop)."""
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=add1.MATH_MOP_CFG)
  fw.init_barrier()

  if timed:
    harness.read_wall_clock(fw, a2, a3)
  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTMOP(1, 0, 0))  # mova2d: SrcA tile -> dest rows 0..31
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    fw.li(t6, TensixRegs.INSTRN_BUF_BASE)
    for fp in (0, 32):  # face-pair band loops: B in {fp, fp+4, fp+8, fp+12}
      loop = fw._new_label(f"band_loop{fp}")
      fw.li(s8, fp)
      fw.li(s9, fp + 16)
      fw.label(loop)
      softmax_band(fw, s8)
      fw.addi(s8, s8, 4)
      fw.blt(s8, s9, loop)
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
    write_trisc1_dest_offset_instr(fw, t2, t1, t3)
    if timed:
      harness.read_wall_clock(fw, a4, a5)
      fw.sub(a4, a4, a2)
      fw.li(a5, RESULT_ADDR)
      fw.sw(a4, a5, 0)
  return fw


def brisc(*, throttle: bool = False) -> Brisc:
  """add1's brisc + optional throttle: math (~2.7k cyc/tile) is slower than
  the DRAM feed here. The throttle was a workaround for cb_pop_front's eager
  RISC ack (acked released pages at TRISC0 issue rate, producer lapped and
  output became softmax of tile i+CB_DEPTH; shift tracked depth exactly at
  4/8/16). Fixed in ttk/cb.py (tensix_ack now defers the ack-publish to the
  STOREREG behind the unpack); throttle=False relies purely on
  cb_reserve_back flow control. Gate (when on): tile i waits until i - done0
  < CB_DEPTH-2."""
  from dsl import a0, a1, s0, s2, s3, s4, t0, t4, t5
  from ttk.mailbox import BriscMailbox as BM
  from ttk.noc import NOC
  from examples.add1 import (
    SYNC_DONE2, SYNC_READ, SYNC_TRISC_INIT, SYNC_TRISC_START,
  )

  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    if throttle:
      # Throttle: don't get more than CB_DEPTH-2 tiles ahead of TRISC0's
      # SYNC_DONE0 (tiles fully unpacked). s5 is the loop counter.
      throttle_loop = fw._new_label("brisc_throttle")
      throttle_ok = fw._new_label("brisc_throttle_ok")
      fw.li(t0, SYNC_DONE0)
      fw.label(throttle_loop)
      fw.lw(t1, t0, 0)
      fw.sub(t1, s5, t1)
      fw.li(t2, CB_DEPTH - 2)
      fw.blt(t1, t2, throttle_ok)
      fw.fence()
      fw.j(throttle_loop)
      fw.label(throttle_ok)

    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.add(a1, s2, s5)
    fw.mv(a0, s0)
    fw.mv(a2, s4)
    fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
    fw.local_noc0_coord(a5)
    fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    fw.addi(t4, t4, 1)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    fw.li(t6, TILE_BYTES)
    fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
    fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
    fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
    read_wait = fw._new_label("brisc_read_wait")
    fw.label(read_wait)
    fw.lw(t1, t0, 0)
    fw.bltu(t1, t4, read_wait)
    fw.fence()
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_READ, t2)
  return fw


def build_program(src_addr: int, dst_addr: int, num_banks: int, *, core,
                  tiles: int, timed: bool = False, throttle: bool = False) -> Program:
  brisc_fw = brisc(throttle=throttle)
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = add1.trisc0()
  trisc1_fw = trisc1(timed=timed)
  trisc2_fw = add1.trisc2()
  brisc_fw.rta(lambda x, y: [src_addr, 0, tiles, num_banks])
  ncrisc_fw.rta(lambda x, y: [dst_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])
  prog = Program(
    brisc=brisc_fw, ncrisc=ncrisc_fw,
    trisc0=trisc0_fw, trisc1=trisc1_fw, trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "softmax"
  return prog


def to_bf16(x):
  u = np.asarray(x, dtype="<f4").view("<u4")
  return ((u >> 16) << 16).view("<f4")


def to_bf16_bytes(x):
  return (np.asarray(x, dtype="<f4").view("<u4") >> 16).astype("<u2").tobytes()


def from_bf16_bytes(raw, shape):
  return (np.frombuffer(raw, dtype="<u2").astype("<u4") << 16).view("<f4").reshape(shape)


def ref_softmax(x):
  x = x.astype(np.float32)
  e = to_bf16(np.exp(x - x.max(axis=-1, keepdims=True)))  # bf16 store of exp
  return to_bf16(e * to_bf16(1.0 / e.sum(axis=-1, keepdims=True)))


def run(device: Device, x, *, tiles: int, timed: bool = False, throttle: bool = False):
  src = device.alloc_write(to_bf16_bytes(x), dtype=DTYPE,
                           shape=(tiles, TILE, TILE), name="softmax_src")
  dst = device.dram.alloc(tiles, dtype=DTYPE, shape=(tiles, TILE, TILE), name="softmax_dst")
  prog = build_program(src.addr, dst.addr, len(device.dram.bank_tiles),
                       core=device.cores[0], tiles=tiles, timed=timed, throttle=throttle)
  device.run(prog)
  return from_bf16_bytes(device.dram_read(dst), (tiles, TILE, TILE))


ATOL, RTOL = 2e-2, 2e-2


def main() -> int:
  import argparse
  parser = argparse.ArgumentParser(description="row softmax composite microbench; needs device")
  parser.add_argument("--iters", type=int, default=0, help="timed stream of N tiles")
  parser.add_argument("--throttle", action="store_true",
                      help="re-enable legacy BRISC SYNC_DONE0 throttle (pre-fix workaround); "
                           "default relies on cb_reserve_back flow control")
  args = parser.parse_args()
  throttle = args.throttle

  rng = np.random.default_rng(17)
  x = to_bf16(rng.uniform(-4.0, 4.0, (1, TILE, TILE)))

  ok = True
  with harness.open_device() as device:
    core = device.cores[0]
    got = run(device, x, tiles=1, throttle=throttle)
    ref = ref_softmax(x)
    max_abs = float(np.max(np.abs(got - ref)))
    rows_ok = bool(np.allclose(got.sum(-1), 1.0, atol=5e-2))
    ok = bool(np.allclose(got, ref, atol=ATOL, rtol=RTOL)) and rows_ok
    print(f"  softmax: {'PASS' if ok else 'FAIL'} max_abs={max_abs:.6g} rowsum1={rows_ok}")
    if not ok:
      print(f"    got[0,:4]={got[0, 0, :4].tolist()}")
      print(f"    ref[0,:4]={ref[0, 0, :4].tolist()}")
      print(f"    rowsum[:4]={got.sum(-1)[0, :4].tolist()}")

    cycles = None
    if args.iters > 0:
      n = args.iters
      harness.clear_window(device, core, [(RESULT_ADDR, 8)])
      xn = to_bf16(rng.uniform(-4.0, 4.0, (n, TILE, TILE)))
      got = run(device, xn, tiles=n, timed=True, throttle=throttle)
      s_ok = bool(np.allclose(got, ref_softmax(xn), atol=ATOL, rtol=RTOL))
      raw = harness.read_window(device, core, RESULT_ADDR, 4)
      cycles = (int.from_bytes(raw, "little"), s_ok)

  print("softmax composite microbench")
  print(f"  dtype={DTYPE.name} tile=32x32 (32 rows x 32 cols) iters={args.iters}")
  if cycles:
    total, s_ok = cycles
    print(f"    {total} cyc / {args.iters} tiles -> {total / args.iters:.1f} cyc/tile"
          f" ({total / args.iters / TILE:.1f} cyc/row) stream={'PASS' if s_ok else 'FAIL'}")
    ok = ok and s_ok
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
