#!/usr/bin/env python3
"""Scale multi-tile attention scores into global-softmax probabilities.

The previous proof computes global softmax stats on device:

  m = max_t max(score_t[row, :])
  l = sum_t sum(exp(score_t[row, :] - m))

This proof adds the next device-side step for each score tile:

  prob_t[row, col] = exp(score_t[row, col] - m[row]) / l[row]

It intentionally stops before weighted-V accumulation. The probability output
is in the same tiled score/probability layout the existing weighted-V GEMV path
already consumes.
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
import matmul_peak as mm  # noqa: E402
import microbench_attention_global_softmax_combine as comb  # noqa: E402
import microbench_attention_global_softmax_stats as statsk  # noqa: E402
import microbench_attention_k_stage as kvstage  # noqa: E402
import microbench_softmax as softmax  # noqa: E402
import numpy as np

from dsl import (  # noqa: E402
  TTMOP, TTSEMPOST, TTSEMWAIT, TTSETRWC, TTSFPLOAD, TTSFPLOADI, TTSFPMAD,
  TTSFPMUL, TTSFPNOP, TTSFPSTORE, TTSTALLWAIT,
  a0, a1, a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, t0, t1, t2, t3, t4, t5, t6,
  zero,
)
from asm import KernelBase  # noqa: E402
from examples import add1  # noqa: E402
from examples.add1 import (  # noqa: E402
  Brisc, CB_DEPTH, OUT_CB, STALL_MATH_PACK_ROOM, SYNC, SYNC_DONE0, SYNC_DONE1,
  SYNC_DONE2, SYNC_READ, SYNC_TRISC_INIT, SYNC_TRISC_START, TILE_BYTES, Trisc,
  WAIT_MATH_AND_SFPU, write_trisc1_dest_offset_instr,
)
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.sfpu import sfpu_exp, sfpu_reciprocal  # noqa: E402
from ttk.tensix import TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait  # noqa: E402

TILE = 32
GROUP = 4
DTYPE = Dtype.Float16_b
RESULT_ADDR = 0x12D000
FMT, AMOD = 2, 7
COL_OFF = (0, 2, 16, 18)


def _read_tile_to_l1(fw: Brisc, *, base_reg, page_reg, l1_dst_reg, num_banks_reg) -> None:
  fw.mv(a0, base_reg)
  fw.mv(a1, page_reg)
  fw.mv(a2, num_banks_reg)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t6, TILE_BYTES)
  fw.noc_read(0, 1, a0, 0, a2, l1_dst_reg, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  wait = fw._new_label("read_tile_wait")
  fw.label(wait)
  fw.lw(t1, t0, 0)
  fw.bltu(t1, t4, wait)
  fw.fence()


def brisc_with_global_stats() -> Brisc:
  """Feed one synthesized tile per score tile.

  Rows 0..3 are the score rows. Rows 4..7 hold the global max rows and rows
  8..11 hold the global denominator rows, copied from the one-tile global-stat
  buffer. TRISC1 then has everything it needs in dest.
  """
  fw = Brisc()
  # RTAs: score base, global-stat base, tile count, bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)

  with fw.tile_loop("brisc"):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    _read_tile_to_l1(fw, base_reg=s0, page_reg=s5, l1_dst_reg=t5, num_banks_reg=s4)
    fw.li(t2, 0)
    fw.li(t6, kvstage.SRC_L1)
    _read_tile_to_l1(fw, base_reg=s2, page_reg=t2, l1_dst_reg=t6, num_banks_reg=s4)
    for row in range(GROUP):
      for col in range(TILE):
        stat_off = kvstage.packed_elem_offset(row, col)
        dst_off = kvstage.packed_elem_offset(row + GROUP, col)
        fw.lhu(t0, t6, stat_off)
        fw.sh(t0, t5, dst_off)
        stat_off = kvstage.packed_elem_offset(row + GROUP, col)
        dst_off = kvstage.packed_elem_offset(row + 2 * GROUP, col)
        fw.lhu(t0, t6, stat_off)
        fw.sh(t0, t5, dst_off)
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_READ, t2)
  return fw


def _push_off(fw, inst, off_reg):
  fw.li(t1, inst.raw_word())
  fw.add(t1, t1, off_reg)
  fw.sw(t1, t6, 0)


def prob_band(fw, off_reg):
  """Compute probability rows B..B+3 from synthesized score/stat rows."""
  for off in COL_OFF:
    _push_off(fw, TTSFPLOAD(0, FMT, AMOD, off), off_reg)
    fw.addi(off_reg, off_reg, GROUP)
    _push_off(fw, TTSFPLOAD(7, FMT, AMOD, off), off_reg)
    fw.addi(off_reg, off_reg, GROUP)
    _push_off(fw, TTSFPLOAD(6, FMT, AMOD, off), off_reg)
    fw.addi(off_reg, off_reg, -2 * GROUP)
    fw.emit(TTSFPMAD(7, 10, 0, 0, 1))  # score - global max
    fw.emit(TTSFPNOP())
    sfpu_exp(fw, 0, 0, scratch=(1, 2, 3, 4))
    sfpu_reciprocal(fw, 6, 6, scratch=(1, 2, 3), iterations=2)
    fw.emit(TTSFPMUL(0, 6, 9, 0, 0))
    fw.emit(TTSFPNOP())
    _push_off(fw, TTSFPSTORE(0, FMT, AMOD, off), off_reg)


def zero_padding_rows(fw, off_reg):
  fw.emit(TTSFPLOADI(0, 0, 0))
  for row_off in (4, 8, 12, 32, 36, 40, 44):
    fw.li(off_reg, row_off)
    for off in COL_OFF:
      _push_off(fw, TTSFPSTORE(0, FMT, AMOD, off), off_reg)


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
    fw.emit(TTMOP(1, 0, 0))  # mova2d: SrcA tile -> dest.
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 4))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTSTALLWAIT(TensixStall.SFPU, TensixWait.MATH))
    fw.li(t6, TensixRegs.INSTRN_BUF_BASE)
    fw.li(t2, 0)
    prob_band(fw, t2)
    zero_padding_rows(fw, t2)
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


def build_program(score_addr: int, global_stats_addr: int, dst_addr: int,
                  num_banks: int, *, core, tiles: int,
                  timed: bool = False) -> Program:
  brisc_fw = brisc_with_global_stats()
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = add1.trisc0()
  trisc1_fw = trisc1(timed=timed)
  trisc2_fw = add1.trisc2()
  brisc_fw.rta(lambda _x, _y: [score_addr, global_stats_addr, tiles, num_banks])
  ncrisc_fw.rta(lambda _x, _y: [dst_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])
  prog = Program(
    brisc=brisc_fw, ncrisc=ncrisc_fw,
    trisc0=trisc0_fw, trisc1=trisc1_fw, trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_global_softmax_probs"
  return prog


def build_prob_gemv_a_compact_program(prob_addr: int, dst_addr: int,
                                      num_banks: int, *, core,
                                      tiles: int, k_cols: int,
                                      dst_pages: int) -> Program:
  if tiles < 1:
    raise ValueError("tiles must be positive")
  total_seq = tiles * TILE
  if k_cols < total_seq or k_cols % TILE:
    raise ValueError("k_cols must cover all live probability columns")
  fw = Brisc()
  # RTAs: probability tile-list base, GEMV-A row-major destination, tile count,
  # bank count.
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s2, s3))
  kvstage.emit_zero_dst(fw, pages=dst_pages)
  for tile in range(tiles):
    fw.li(t2, tile)
    kvstage.emit_read_page(fw, base_reg=s0, page_reg=t2, l1_dst=kvstage.SRC_L1)
    for row in range(GROUP):
      for col in range(TILE):
        linear = row * k_cols + tile * TILE + col
        dst_page = linear // (TILE * TILE)
        dst_off = (linear % (TILE * TILE)) * DTYPE.bpe
        fw.li(t1, kvstage.SRC_L1 + (row * TILE + col) * DTYPE.bpe)
        fw.lhu(t0, t1, 0)
        fw.li(t1, kvstage.DST_L1 + dst_page * TILE_BYTES + dst_off)
        fw.sh(t0, t1, 0)
  for page in range(dst_pages):
    kvstage.emit_write_l1_page(fw, page=page, l1_src=kvstage.DST_L1 + page * TILE_BYTES)
  fw.ret()
  fw.rta(lambda _x, _y: [prob_addr, dst_addr, tiles, num_banks])
  prog = Program(brisc=fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = "attn_global_probs_to_gemv_a"
  return prog


def ref_probs(scores: np.ndarray, global_stats: np.ndarray) -> np.ndarray:
  scores = scores.astype(np.float32)
  stats = global_stats.astype(np.float32)
  out = np.zeros_like(scores)
  maxes = stats[:GROUP, 0]
  denoms = stats[GROUP:2 * GROUP, 0]
  e = softmax.to_bf16(np.exp(scores[:, :GROUP, :] - maxes[None, :, None]))
  out[:, :GROUP, :] = softmax.to_bf16(e / denoms[None, :, None])
  return softmax.to_bf16(out)


def main() -> int:
  p = argparse.ArgumentParser(description="attention global-softmax probability proof; needs device")
  p.add_argument("--tiles", type=int, default=2)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--weighted-v", action="store_true",
                 help="also run one existing GEMV over all live probability tiles and V rows")
  p.add_argument("--host-prob-a", action="store_true",
                 help=argparse.SUPPRESS)
  p.add_argument("--timed", action="store_true")
  args = p.parse_args()
  if args.tiles < 1:
    raise ValueError("--tiles must be positive")

  rng = np.random.default_rng(311)
  scores = rng.uniform(-5.0, 5.0, size=(args.tiles, TILE, TILE)).astype(np.float32)
  scores = softmax.from_bf16_bytes(softmax.to_bf16_bytes(scores), scores.shape)
  expected_stats = statsk.ref_stats(scores)
  expected_global = comb.ref_combined(expected_stats)
  expected_probs = ref_probs(scores, expected_global)
  total_seq = args.tiles * TILE
  expected_prob_a_logical = np.zeros((GROUP, total_seq), dtype=np.float32)
  expected_prob_a_logical[:, :] = np.concatenate(
      [expected_probs[tile, :GROUP, :] for tile in range(args.tiles)], axis=1)
  v_rows = softmax.to_bf16(rng.uniform(-2.0, 2.0, size=(total_seq, TILE * 2)).astype(np.float32))
  expected_ctx = expected_prob_a_logical @ v_rows[:, :TILE * 2]

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    cores = [core]
    v_chunks = mm.plan_output_chunks(GROUP, total_seq, TILE * 2, cores, nb)
    if args.weighted_v and len(v_chunks) != 1:
      raise ValueError("weighted-V proof expects one GEMV chunk")
    v_chunk = v_chunks[0] if args.weighted_v else None
    VMp = VKp = VNp = ctx_pages = v_pages = a_pages = None
    if args.weighted_v:
      VMp, VKp, VNp = mm.global_padded_shape(GROUP, total_seq, TILE * 2, v_chunks)
      a_pages = (VMp * VKp * DTYPE.bpe) // TILE_BYTES
      v_pages = (VKp * VNp * DTYPE.bpe) // TILE_BYTES
      ctx_pages = (VMp // TILE) * (VNp // TILE)
    score_buf = device.alloc_write(softmax.to_bf16_bytes(scores), dtype=DTYPE,
                                   shape=(args.tiles, TILE, TILE), name="attn_score_tiles")
    stats_buf = device.dram.alloc(args.tiles, dtype=DTYPE,
                                  shape=(args.tiles, TILE, TILE), name="attn_score_stats")
    compact_buf = device.dram.alloc(1, dtype=DTYPE, shape=(TILE, TILE),
                                    name="attn_compact_stats")
    global_buf = device.dram.alloc(1, dtype=DTYPE, shape=(TILE, TILE),
                                   name="attn_global_stats")
    prob_buf = device.dram.alloc(args.tiles, dtype=DTYPE,
                                 shape=(args.tiles, TILE, TILE), name="attn_probs")
    prob_a_buf = v_buf = ctx_buf = None
    expected_prob_a = None
    if args.weighted_v:
      expected_prob_a = np.zeros((VMp, VKp), dtype=np.float32)
      expected_prob_a[:GROUP, :total_seq] = expected_prob_a_logical
      prob_a_buf = device.dram.alloc(a_pages, dtype=DTYPE,
                                     shape=(VMp, VKp), name="attn_probs_gemv_a")
      if args.host_prob_a:
        device.dram_write(prob_a_buf, mm.to_bf16_device_bytes(expected_prob_a))
      else:
        device.dram_write(prob_a_buf, b"\0" * prob_a_buf.size)
      v_expected = np.zeros((VKp, VNp), dtype=np.float32)
      v_expected[:total_seq, :TILE * 2] = v_rows
      v_buf = device.alloc_write(mm.to_bf16_device_bytes(v_expected), dtype=DTYPE,
                                 shape=(VKp, VNp), name="attn_v")
      ctx_buf = device.dram.alloc(ctx_pages, dtype=DTYPE,
                                  shape=(VMp, VNp), name="attn_ctx")
      device.dram_write(ctx_buf, b"\0" * ctx_buf.size)
    stats_prog = statsk.build_program(score_buf.addr, stats_buf.addr, nb, core=core,
                                      tiles=args.tiles, timed=False)
    compact_prog = comb.build_compact_stats_program(stats_buf.addr, compact_buf.addr, nb,
                                                    core=core, tiles=args.tiles)
    combine_prog = comb.build_combine_program(compact_buf.addr, global_buf.addr, nb,
                                              core=core, timed=False)
    prob_prog = build_program(score_buf.addr, global_buf.addr, prob_buf.addr, nb,
                              core=core, tiles=args.tiles, timed=args.timed)
    programs = [stats_prog, compact_prog, combine_prog, prob_prog]
    if args.weighted_v:
      if not args.host_prob_a:
        prob_a_prog = build_prob_gemv_a_compact_program(
            prob_buf.addr, prob_a_buf.addr, nb, core=core, tiles=args.tiles,
            k_cols=VKp, dst_pages=a_pages)
        programs.append(prob_a_prog)
      v_layout = mm.TensorLayout(
        m_tile_offset=v_chunk.m_tile_offset,
        n_tile_offset=v_chunk.n_tile_offset,
        a_row_stride=total_seq // TILE,
        b_row_stride=VNp // TILE,
        c_row_stride=VNp // TILE,
      )
      v_prog = mm.build_program(v_chunk.plan, prob_a_buf.addr, v_buf.addr, ctx_buf.addr, nb, v_layout)
      v_prog.name = "attn_global_weighted_v"
      programs.append(v_prog)
    times = []
    for _ in range(args.runs):
      for prog in programs:
        times.extend(device.run(prog))
    global_raw = device.dram_read(global_buf)
    prob_raw = device.dram_read(prob_buf)
    prob_a_raw = device.dram_read(prob_a_buf) if args.weighted_v else None
    ctx_raw = device.dram_read(ctx_buf) if args.weighted_v else None

  global_got = softmax.from_bf16_bytes(global_raw, (TILE, TILE))
  probs_got = softmax.from_bf16_bytes(prob_raw, (args.tiles, TILE, TILE))
  global_ok = bool(np.allclose(global_got[:2 * GROUP, :], expected_global[:2 * GROUP, :],
                               atol=1.5e-1, rtol=1.5e-1))
  prob_ok = bool(np.allclose(probs_got[:, :GROUP, :], expected_probs[:, :GROUP, :],
                             atol=5.0e-2, rtol=5.0e-2))
  rowsum = probs_got[:, :GROUP, :].sum(axis=(0, 2))
  rowsum_ok = bool(np.allclose(rowsum, np.ones(GROUP, dtype=np.float32),
                               atol=1.25e-1, rtol=1.25e-1))
  ctx_ok = True
  compact_ok = True
  ctx = None
  if args.weighted_v:
    prob_a_got = mm.from_bf16_device_bytes(prob_a_raw, (VMp, VKp))
    compact_ok = bool(np.allclose(prob_a_got, expected_prob_a, atol=5.0e-2, rtol=5.0e-2))
    full_ctx = mm.from_bf16_device_bytes(ctx_raw, (VMp, VNp))[:, :TILE * 2]
    ctx = full_ctx[:GROUP, :TILE * 2]
    ctx_ok = bool(np.allclose(ctx, expected_ctx, atol=1.0e-1, rtol=1.0e-1))
  ok = global_ok and prob_ok and rowsum_ok and compact_ok and ctx_ok
  print("attention global-softmax probability proof")
  print(f"  tiles={args.tiles} rows={GROUP} runs={args.runs}")
  if args.weighted_v:
    print(f"  weighted_v padded={VMp}x{VKp}x{VNp}")
  if times:
    print(f"  launches={len(programs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  global stats: {'PASS' if global_ok else 'FAIL'}")
  print(f"  probabilities: {'PASS' if prob_ok else 'FAIL'}")
  print(f"  probability row sums: {'PASS' if rowsum_ok else 'FAIL'} {rowsum.tolist()}")
  if args.weighted_v:
    print(f"  probability GEMV-A compact: {'PASS' if compact_ok else 'FAIL'}")
    print(f"  weighted V GEMV: {'PASS' if ctx_ok else 'FAIL'}")
  if not prob_ok:
    diff = np.abs(probs_got[:, :GROUP, :] - expected_probs[:, :GROUP, :])
    t, r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    prob diff tile={t} row={r} col={c} got={float(probs_got[t, r, c]):.6g} "
          f"ref={float(expected_probs[t, r, c]):.6g}")
  if args.weighted_v and not ctx_ok:
    diff = np.abs(ctx - expected_ctx)
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    ctx diff row={r} col={c} got={float(ctx[r, c]):.6g} "
          f"ref={float(expected_ctx[r, c]):.6g}")
    full_ctx = mm.from_bf16_device_bytes(ctx_raw, (VMp, VNp))[:, :TILE * 2]
    for phys in range(8):
      scores = [
        float(np.max(np.abs(full_ctx[phys] - expected_ctx[ref])))
        for ref in range(GROUP)
      ]
      best = int(np.argmin(scores))
      print(f"    phys row {phys}: best_ref={best} max_abs={scores[best]:.6g} "
            f"first4={full_ctx[phys, :4].tolist()}")
  if args.weighted_v and not compact_ok:
    diff = np.abs(prob_a_got - expected_prob_a)
    r, c = np.unravel_index(int(np.argmax(diff)), diff.shape)
    print(f"    compact diff row={r} col={c} got={float(prob_a_got[r, c]):.6g} "
          f"ref={float(expected_prob_a[r, c]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
