#!/usr/bin/env python3
"""Per-tile attention softmax stats for multi-tile/global attention.

For each 32-column score tile, compute on device:

  row_max = max(scores[row, :])
  row_sum = sum(exp(scores[row, :] - row_max))

The output tile stores row_max for rows 0..GROUP-1 and row_sum for
rows GROUP..2*GROUP-1, repeated across the row. This is not final global
softmax yet; it is the device-side partial-stat producer needed by the next
online softmax combiner across history tiles.
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
import microbench_softmax as softmax  # noqa: E402
import numpy as np

from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  TTSEMPOST, TTSEMWAIT, TTSETRWC, TTSFPADD, TTSFPLOAD, TTSFPMAD,
  TTSFPMOV, TTSFPNOP, TTSFPSTORE, TTSFPSHFT2, TTSFPSWAP, TTSTALLWAIT,
  a2, a3, a4, a5, s5, t1, t2, t3, t6,
)
from program import Dtype, Program  # noqa: E402
from ttk.tensix import TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait  # noqa: E402
from ttk.sfpu import SFPSWAP_ALL_ROWS_MAX, sfpu_exp  # noqa: E402

from examples import add1  # noqa: E402
from examples.add1 import (  # noqa: E402
  Brisc, CB_DEPTH, OUT_CB, STALL_MATH_PACK_ROOM, SYNC, SYNC_DONE1,
  TILE_BYTES, Trisc, WAIT_MATH_AND_SFPU, write_trisc1_dest_offset_instr,
)

TILE = 32
GROUP = 4
DTYPE = Dtype.Float16_b
RESULT_ADDR = 0x12D000
FMT, AMOD = 2, 7
COL_OFF = (0, 2, 16, 18)


def _push_off(fw, inst, off_reg):
  fw.li(t1, inst.raw_word())
  fw.add(t1, t1, off_reg)
  fw.sw(t1, t6, 0)


def stats_band(fw, off_reg):
  """Compute row max/sum for rows B..B+3, B in off_reg."""
  for lreg, off in zip(range(4), COL_OFF):
    _push_off(fw, TTSFPLOAD(lreg, FMT, AMOD, off), off_reg)
  for a, b in ((0, 2), (1, 3), (0, 1)):
    fw.emit(TTSFPSWAP(0, a, b, SFPSWAP_ALL_ROWS_MAX))
    fw.emit(TTSFPNOP())
  for k in (4, 2, 1):
    fw.emit(TTSFPMOV(0, 0, 1, 0))
    for _ in range(k):
      fw.emit(TTSFPSHFT2(0, 1, 1, 3))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
    fw.emit(TTSFPNOP())
  fw.emit(TTSFPMOV(0, 0, 7, 0))  # L7 = max broadcast by row.
  for i, off in enumerate(COL_OFF):
    _push_off(fw, TTSFPLOAD(0, FMT, AMOD, off), off_reg)
    fw.emit(TTSFPMAD(7, 10, 0, 0, 1))  # x - max
    fw.emit(TTSFPNOP())
    sfpu_exp(fw, 0, 0, scratch=(1, 2, 3, 4))
    fw.emit(TTSFPMOV(0, 0, 6, 0) if i == 0 else TTSFPADD(10, 6, 0, 6, 0))
    fw.emit(TTSFPNOP())
  fw.emit(TTSFPMOV(0, 6, 1, 0))
  for _ in range(7):
    fw.emit(TTSFPSHFT2(0, 1, 2, 3))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPADD(10, 6, 2, 6, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMOV(0, 2, 1, 0))

  # Store max in rows B..B+3 and sum in rows B+4..B+7.
  for off in COL_OFF:
    _push_off(fw, TTSFPSTORE(7, FMT, AMOD, off), off_reg)
  fw.addi(off_reg, off_reg, GROUP)
  for off in COL_OFF:
    _push_off(fw, TTSFPSTORE(6, FMT, AMOD, off), off_reg)
  fw.addi(off_reg, off_reg, -GROUP)


def trisc1(*, timed: bool = False) -> Trisc:
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
    fw.emit(softmax.TTMOP(1, 0, 0))  # mova2d: SrcA tile -> dest.
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    fw.li(t6, TensixRegs.INSTRN_BUF_BASE)
    fw.li(t2, 0)
    stats_band(fw, t2)
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


def build_program(src_addr: int, dst_addr: int, num_banks: int, *, core,
                  tiles: int, timed: bool = False) -> Program:
  brisc_fw = softmax.brisc()
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = add1.trisc0()
  trisc1_fw = trisc1(timed=timed)
  trisc2_fw = add1.trisc2()
  brisc_fw.rta(lambda _x, _y: [src_addr, 0, tiles, num_banks])
  ncrisc_fw.rta(lambda _x, _y: [dst_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])
  prog = Program(
    brisc=brisc_fw, ncrisc=ncrisc_fw,
    trisc0=trisc0_fw, trisc1=trisc1_fw, trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_global_softmax_tile_stats"
  return prog


def ref_stats(scores: np.ndarray) -> np.ndarray:
  scores = scores.astype(np.float32)
  out = np.zeros_like(scores)
  maxes = scores[:, :GROUP, :].max(axis=-1)
  e = softmax.to_bf16(np.exp(scores[:, :GROUP, :] - maxes[:, :, None]))
  sums = e.sum(axis=-1)
  out[:, :GROUP, :] = maxes[:, :, None]
  out[:, GROUP:2 * GROUP, :] = sums[:, :, None]
  return softmax.to_bf16(out)


def main() -> int:
  p = argparse.ArgumentParser(description="attention per-tile softmax stats; needs device")
  p.add_argument("--tiles", type=int, default=2)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--timed", action="store_true")
  args = p.parse_args()
  if args.tiles < 1:
    raise ValueError("--tiles must be positive")

  rng = np.random.default_rng(293)
  scores = rng.uniform(-5.0, 5.0, size=(args.tiles, TILE, TILE)).astype(np.float32)
  scores = softmax.from_bf16_bytes(softmax.to_bf16_bytes(scores), scores.shape)
  expected = ref_stats(scores)

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    src = device.alloc_write(softmax.to_bf16_bytes(scores), dtype=DTYPE,
                             shape=(args.tiles, TILE, TILE), name="attn_score_tiles")
    dst = device.dram.alloc(args.tiles, dtype=DTYPE,
                            shape=(args.tiles, TILE, TILE), name="attn_score_stats")
    prog = build_program(src.addr, dst.addr, nb, core=core, tiles=args.tiles, timed=args.timed)
    times = []
    for _ in range(args.runs):
      times.extend(device.run(prog))
    raw = device.dram_read(dst)

  got = softmax.from_bf16_bytes(raw, (args.tiles, TILE, TILE))
  max_ok = bool(np.allclose(got[:, :GROUP, :], expected[:, :GROUP, :], atol=1.0e-2, rtol=1.0e-2))
  sum_ok = bool(np.allclose(got[:, GROUP:2 * GROUP, :], expected[:, GROUP:2 * GROUP, :],
                            atol=7.5e-2, rtol=7.5e-2))
  ok = max_ok and sum_ok
  print("attention global-softmax per-tile stats")
  print(f"  tiles={args.tiles} rows={GROUP} runs={args.runs}")
  if times:
    print(f"  launches={args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  row max stats: {'PASS' if max_ok else 'FAIL'}")
  print(f"  exp-sum stats: {'PASS' if sum_ok else 'FAIL'}")
  if not max_ok:
    diff = np.abs(got[:, :GROUP, :] - expected[:, :GROUP, :])
    t, r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    max diff tile={t} row={r} col={c} got={float(got[t, r, c]):.6g} "
          f"ref={float(expected[t, r, c]):.6g}")
  if not sum_ok:
    diff = np.abs(got[:, GROUP:2 * GROUP, :] - expected[:, GROUP:2 * GROUP, :])
    t, r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    rr = r + GROUP
    print(f"    sum diff tile={t} row={rr} col={c} got={float(got[t, rr, c]):.6g} "
          f"ref={float(expected[t, rr, c]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
