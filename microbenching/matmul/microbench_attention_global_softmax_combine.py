#!/usr/bin/env python3
"""Combine per-tile attention softmax stats into global denominators.

Input score tiles -> device stats producer:
  m_i = max(score_tile_i[row, :])
  l_i = sum(exp(score_tile_i[row, :] - m_i))

This proof adds the next device-side step:
  m = max_i(m_i)
  l = sum_i(l_i * exp(m_i - m))

It intentionally stops before probability scaling / weighted-V accumulation.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TT_USB", "0")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "microbenching"))
sys.path.insert(0, str(ROOT / "microbenching" / "matmul"))
sys.path.insert(0, str(ROOT / "microbenching" / "tensix"))
sys.path.insert(0, str(ROOT / "examples"))

import harness  # noqa: E402,F401
import microbench_attention_global_softmax_stats as statsk  # noqa: E402
import microbench_attention_k_stage as kvstage  # noqa: E402
import microbench_softmax as softmax  # noqa: E402
import numpy as np

from asm import KernelBase  # noqa: E402
from dsl import (  # noqa: E402
  TTMOP, TTSEMPOST, TTSEMWAIT, TTSETRWC, TTSFPADD, TTSFPLOAD, TTSFPMAD,
  TTSFPMOV, TTSFPMUL, TTSFPNOP, TTSFPSTORE, TTSFPSHFT2, TTSFPSWAP,
  TTSTALLWAIT,
  a2, a3, a4, a5, s0, s1, s2, s3, s5, t0, t1, t2, t3, t6,
)
from examples import add1  # noqa: E402
from examples.add1 import (  # noqa: E402
  Brisc, CB_DEPTH, OUT_CB, STALL_MATH_PACK_ROOM, SYNC, SYNC_DONE1,
  TILE_BYTES, Trisc, WAIT_MATH_AND_SFPU, write_trisc1_dest_offset_instr,
)
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.sfpu import SFPSWAP_ALL_ROWS_MAX, sfpu_exp  # noqa: E402
from ttk.tensix import TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait  # noqa: E402

TILE = 32
GROUP = 4
DTYPE = Dtype.Float16_b
MASK_BF16 = 0xC2C8  # bf16(-100.0)
RESULT_ADDR = 0x12D000
FMT, AMOD = 2, 7
COL_OFF = (0, 2, 16, 18)


def build_compact_stats_program(stats_addr: int, compact_addr: int,
                                num_banks: int, *, core, tiles: int) -> Program:
  if not 1 <= tiles <= TILE:
    raise ValueError("tiles must fit in one compact stats row")
  fw = Brisc()
  # RTAs: stats base, compact destination, tile count, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3))
  kvstage.emit_zero_dst(fw, pages=1)
  fw.li(t0, MASK_BF16)
  for row in range(GROUP):
    for col in range(TILE):
      fw.li(t1, kvstage.DST_L1 + kvstage.packed_elem_offset(row, col))
      fw.sh(t0, t1, 0)
  for tile in range(tiles):
    fw.li(t2, tile)
    kvstage.emit_read_page(fw, base_reg=s0, page_reg=t2, l1_dst=kvstage.SRC_L1)
    for row in range(GROUP):
      fw.li(t1, kvstage.SRC_L1 + kvstage.packed_elem_offset(row, 0))
      fw.lhu(t0, t1, 0)
      fw.li(t1, kvstage.DST_L1 + kvstage.packed_elem_offset(row, tile))
      fw.sh(t0, t1, 0)
      fw.li(t1, kvstage.SRC_L1 + kvstage.packed_elem_offset(row + GROUP, 0))
      fw.lhu(t0, t1, 0)
      fw.li(t1, kvstage.DST_L1 + kvstage.packed_elem_offset(row + GROUP, tile))
      fw.sh(t0, t1, 0)
  kvstage.emit_write_l1_page(fw, page=0, l1_src=kvstage.DST_L1)
  fw.ret()
  fw.rta(lambda _x, _y: [stats_addr, compact_addr, tiles, num_banks])
  prog = Program(brisc=fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_global_softmax_compact_stats"
  return prog


def _push_off(fw, inst, off_reg):
  fw.li(t1, inst.raw_word())
  fw.add(t1, t1, off_reg)
  fw.sw(t1, t6, 0)


def combine_band(fw, off_reg):
  """Combine rows B..B+3 of compact m_i/l_i stats."""
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
  fw.emit(TTSFPMOV(0, 0, 7, 0))  # L7 = global max per row.

  for i, off in enumerate(COL_OFF):
    _push_off(fw, TTSFPLOAD(0, FMT, AMOD, off), off_reg)
    fw.emit(TTSFPMAD(7, 10, 0, 0, 1))  # m_i - m
    fw.emit(TTSFPNOP())
    sfpu_exp(fw, 0, 0, scratch=(1, 2, 3, 4))
    fw.addi(off_reg, off_reg, GROUP)
    _push_off(fw, TTSFPLOAD(5, FMT, AMOD, off), off_reg)
    fw.addi(off_reg, off_reg, -GROUP)
    fw.emit(TTSFPMUL(0, 5, 9, 0, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMOV(0, 0, 6, 0) if i == 0 else TTSFPADD(10, 6, 0, 6, 0))
    fw.emit(TTSFPNOP())

  fw.emit(TTSFPMOV(0, 6, 1, 0))
  for _ in range(7):
    fw.emit(TTSFPSHFT2(0, 1, 2, 3))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPADD(10, 6, 2, 6, 0))
    fw.emit(TTSFPNOP())
    fw.emit(TTSFPMOV(0, 2, 1, 0))

  for off in COL_OFF:
    _push_off(fw, TTSFPSTORE(7, FMT, AMOD, off), off_reg)
  fw.addi(off_reg, off_reg, GROUP)
  for off in COL_OFF:
    _push_off(fw, TTSFPSTORE(6, FMT, AMOD, off), off_reg)
  fw.addi(off_reg, off_reg, -GROUP)


def combine_trisc1(*, timed: bool = False) -> Trisc:
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
    fw.emit(TTMOP(1, 0, 0))  # mova2d: SrcA tile -> dest.
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    fw.li(t6, TensixRegs.INSTRN_BUF_BASE)
    fw.li(t2, 0)
    combine_band(fw, t2)
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


def build_combine_program(src_addr: int, dst_addr: int, num_banks: int, *,
                          core, timed: bool = False) -> Program:
  brisc_fw = statsk.softmax.brisc()
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = add1.trisc0()
  trisc1_fw = combine_trisc1(timed=timed)
  trisc2_fw = add1.trisc2()
  brisc_fw.rta(lambda _x, _y: [src_addr, 0, 1, num_banks])
  ncrisc_fw.rta(lambda _x, _y: [dst_addr, 0, 1, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [1])
  prog = Program(
    brisc=brisc_fw, ncrisc=ncrisc_fw,
    trisc0=trisc0_fw, trisc1=trisc1_fw, trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_global_softmax_combine_stats"
  return prog


def ref_combined(stats_tiles: np.ndarray) -> np.ndarray:
  stats_tiles = stats_tiles.astype(np.float32)
  m_i = stats_tiles[:, :GROUP, 0]
  l_i = stats_tiles[:, GROUP:2 * GROUP, 0]
  m = m_i.max(axis=0)
  weights = statsk.softmax.to_bf16(np.exp(m_i - m[None, :]))
  denom = np.sum(l_i * weights, axis=0)
  out = np.zeros((TILE, TILE), dtype=np.float32)
  out[:GROUP, :] = m[:, None]
  out[GROUP:2 * GROUP, :] = denom[:, None]
  return statsk.softmax.to_bf16(out)


def main() -> int:
  p = argparse.ArgumentParser(description="combine attention softmax tile stats; needs device")
  p.add_argument("--tiles", type=int, default=2)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--timed", action="store_true")
  args = p.parse_args()
  if not 1 <= args.tiles <= TILE:
    raise ValueError("--tiles must fit in one compact stats tile")

  rng = np.random.default_rng(307)
  scores = rng.uniform(-5.0, 5.0, size=(args.tiles, TILE, TILE)).astype(np.float32)
  scores = statsk.softmax.from_bf16_bytes(statsk.softmax.to_bf16_bytes(scores), scores.shape)
  expected_stats = statsk.ref_stats(scores)
  expected = ref_combined(expected_stats)

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    score_buf = device.alloc_write(statsk.softmax.to_bf16_bytes(scores), dtype=DTYPE,
                                   shape=(args.tiles, TILE, TILE), name="attn_score_tiles")
    stats_buf = device.dram.alloc(args.tiles, dtype=DTYPE,
                                  shape=(args.tiles, TILE, TILE), name="attn_score_stats")
    compact_buf = device.dram.alloc(1, dtype=DTYPE, shape=(TILE, TILE),
                                    name="attn_compact_stats")
    out_buf = device.dram.alloc(1, dtype=DTYPE, shape=(TILE, TILE),
                                name="attn_global_stats")
    stats_prog = statsk.build_program(score_buf.addr, stats_buf.addr, nb, core=core,
                                      tiles=args.tiles, timed=False)
    compact_prog = build_compact_stats_program(stats_buf.addr, compact_buf.addr, nb,
                                               core=core, tiles=args.tiles)
    combine_prog = build_combine_program(compact_buf.addr, out_buf.addr, nb,
                                         core=core, timed=args.timed)
    programs = (stats_prog, compact_prog, combine_prog)
    times = []
    for _ in range(args.runs):
      for prog in programs:
        times.extend(device.run(prog))
    stats_raw = device.dram_read(stats_buf)
    compact_raw = device.dram_read(compact_buf)
    out_raw = device.dram_read(out_buf)

  stats_got = statsk.softmax.from_bf16_bytes(stats_raw, (args.tiles, TILE, TILE))
  compact_got = statsk.softmax.from_bf16_bytes(compact_raw, (TILE, TILE))
  out_got = statsk.softmax.from_bf16_bytes(out_raw, (TILE, TILE))
  stats_ok = bool(np.allclose(stats_got[:, :2 * GROUP, :],
                              expected_stats[:, :2 * GROUP, :],
                              atol=7.5e-2, rtol=7.5e-2))
  compact_ref = np.zeros((TILE, TILE), dtype=np.float32)
  compact_ref[:GROUP, :] = np.float32(-100.0)
  for tile in range(args.tiles):
    compact_ref[:GROUP, tile] = stats_got[tile, :GROUP, 0]
    compact_ref[GROUP:2 * GROUP, tile] = stats_got[tile, GROUP:2 * GROUP, 0]
  compact_ref = statsk.softmax.to_bf16(compact_ref)
  compact_ok = bool(np.allclose(compact_got[:2 * GROUP, :], compact_ref[:2 * GROUP, :],
                                atol=2.0e-2, rtol=2.0e-2))
  max_ok = bool(np.allclose(out_got[:GROUP, :], expected[:GROUP, :],
                            atol=1.0e-2, rtol=1.0e-2))
  denom_ok = bool(np.allclose(out_got[GROUP:2 * GROUP, :], expected[GROUP:2 * GROUP, :],
                              atol=1.5e-1, rtol=1.5e-1))
  ok = stats_ok and compact_ok and max_ok and denom_ok
  print("attention global-softmax stats combiner")
  print(f"  tiles={args.tiles} rows={GROUP} runs={args.runs}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  per-tile stats: {'PASS' if stats_ok else 'FAIL'}")
  print(f"  compact stats tile: {'PASS' if compact_ok else 'FAIL'}")
  print(f"  global max: {'PASS' if max_ok else 'FAIL'}")
  print(f"  global denominator: {'PASS' if denom_ok else 'FAIL'}")
  if not denom_ok:
    diff = np.abs(out_got[GROUP:2 * GROUP, :] - expected[GROUP:2 * GROUP, :])
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    rr = r + GROUP
    print(f"    denom diff row={rr} col={c} got={float(out_got[rr, c]):.6g} "
          f"ref={float(expected[rr, c]):.6g}")
  if not compact_ok:
    diff = np.abs(compact_got[:2 * GROUP, :] - compact_ref[:2 * GROUP, :])
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    compact diff row={r} col={c} got={float(compact_got[r, c]):.6g} "
          f"ref={float(compact_ref[r, c]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
