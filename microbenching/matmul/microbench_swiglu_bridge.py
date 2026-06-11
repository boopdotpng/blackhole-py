#!/usr/bin/env python3
"""Device SwiGLU bridge proof.

Gate/up GEMVs produce row-tiled M=1 outputs: one tile per 32 hidden elements,
with only row 0 meaningful. The SFPU silu helper operates on sparse 32-lane
footprints, so the original proof staged:

  gate row tiles -> SFPU footprints -> silu footprints -> row tiles
  silu(gate) row tiles * up row tiles -> swiglu row tiles

The current default fuses row->footprint and SiLU into one program, then keeps
footprint->row and the final row-tiled multiply as separate simple programs.
The result is the row-tiled activation layout that Wdown GEMV already consumes.
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
import microbench_qkv_kstage_rope_scatter as kstage  # noqa: E402
import microbench_residual_gemv as resgemv  # noqa: E402
import microbench_sfpu_transcendental as sfpu  # noqa: E402
import numpy as np

from asm import KernelBase  # noqa: E402
from dsl import a0, a1, a2, a5, s0, s1, s2, s3, s4, s5, t0, t1, t2, t4, t5, t6, zero  # noqa: E402
from examples import add1  # noqa: E402
from examples.add1 import Brisc, CB_DEPTH, OUT_CB, TILE_BYTES  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.mailbox import BriscMailbox as BM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402

TILE = 32
PAGE = Dtype.Float16_b.tile_size
# The fused row->SiLU program has live CB0/CB16 storage, so keep the BRISC
# rearrange scratch above add1's CB footprint and sync words.
SRC_L1 = add1.SYNC_L1 + 0x1000
DST_L1 = SRC_L1 + PAGE


def vector_to_row_tiles(vec: np.ndarray, n_padded: int) -> np.ndarray:
  tiles = np.zeros((n_padded // TILE, TILE, TILE), dtype=np.float32)
  v = np.zeros(n_padded, dtype=np.float32)
  v[:vec.size] = vec
  for tile in range(n_padded // TILE):
    tiles[tile, 0, :] = v[tile * TILE:(tile + 1) * TILE]
  return tiles


def row_tiles_to_vector(raw: bytes, tiles: int, n: int) -> np.ndarray:
  data = elw.from_bf16_bytes(raw, (tiles, TILE, TILE))
  return data[:, 0, :].reshape(-1)[:n]


def footprint_values(raw: bytes, tiles: int, n: int) -> np.ndarray:
  data = elw.from_bf16_bytes(raw, (tiles, TILE, TILE))
  out = np.empty(tiles * TILE, dtype=np.float32)
  for tile in range(tiles):
    out[tile * TILE:(tile + 1) * TILE] = sfpu.footprint_values(data[tile])
  return out[:n]


def emit_read_page(fw: Brisc, src_base, page_reg) -> None:
  fw.mv(a0, src_base)
  fw.mv(a1, page_reg)
  fw.mv(a2, s4)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, SRC_L1)
  fw.li(t6, PAGE)
  fw.noc_read(0, 1, a0, 0, a2, t2, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_reads_flushed(0, t4, addr=t0, val=t1)


def emit_write_page(fw: Brisc, dst_base, page_reg) -> None:
  fw.mv(a0, dst_base)
  fw.mv(a1, page_reg)
  fw.mv(a2, s4)
  fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
  fw.local_noc0_coord(a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t2, DST_L1)
  fw.li(t6, PAGE)
  fw.noc_write(0, 0, t2, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(0, t4, addr=t0, val=t1)


def emit_zero_dst(fw: Brisc) -> None:
  loop = fw._new_label("zero_dst")
  fw.li(t0, DST_L1)
  fw.li(t1, DST_L1 + PAGE)
  fw.label(loop)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.bltu(t0, t1, loop)


def emit_row_to_footprint(fw: Brisc) -> None:
  for lane in range(TILE):
    row = lane // 8
    col = (lane & 7) * 2
    fw.li(t1, SRC_L1)
    fw.lhu(t0, t1, kstage.row0_offset(lane))
    fw.li(t2, DST_L1 + kstage.rope.packed_elem_offset(row, col))
    fw.sh(t0, t2, 0)


def emit_footprint_to_row(fw: Brisc) -> None:
  for lane in range(TILE):
    row = lane // 8
    col = (lane & 7) * 2
    fw.li(t1, SRC_L1)
    fw.lhu(t0, t1, kstage.rope.packed_elem_offset(row, col))
    fw.li(t2, DST_L1 + kstage.row0_offset(lane))
    fw.sh(t0, t2, 0)


def emit_row_to_footprint_preamble_from_rta(fw: Brisc, *, rta_index: int = 4) -> None:
  """Convert row-tiled source from an extra RTA into the normal source buffer."""
  fw.read32(t0, BM.RTA_L1_BASE_PTR)
  fw.lw(s1, t0, rta_index * 4)
  start = fw._new_label("row_to_fp_preamble")
  done = fw._new_label("row_to_fp_preamble_done")
  fw.li(s5, 0)
  fw.label(start)
  fw.beq(s5, s3, done)
  emit_read_page(fw, s1, s5)
  emit_zero_dst(fw)
  emit_row_to_footprint(fw)
  emit_write_page(fw, s0, s5)
  fw.addi(s5, s5, 1)
  fw.j(start)
  fw.label(done)


def emit_l1_tile_copy(fw: Brisc, src_l1: int, dst_reg) -> None:
  loop = fw._new_label("l1_tile_copy")
  fw.li(t0, src_l1)
  fw.li(t1, src_l1 + PAGE)
  fw.label(loop)
  fw.lw(t2, t0, 0)
  fw.sw(t2, dst_reg, 0)
  fw.addi(t0, t0, 4)
  fw.addi(dst_reg, dst_reg, 4)
  fw.bltu(t0, t1, loop)


def row_silu_brisc() -> Brisc:
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    add1.SYNC_TRISC_START, add1.SYNC_READ, add1.SYNC_DONE0, add1.SYNC_DONE1, add1.SYNC_DONE2,
    add1.SYNC_TRISC_INIT, add1.SYNC_TRISC_INIT + 4, add1.SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(add1.SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.add(a1, s2, s5)
    emit_read_page(fw, s0, a1)
    emit_zero_dst(fw)
    emit_row_to_footprint(fw)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    emit_l1_tile_copy(fw, DST_L1, t5)
    fw.fence()
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(add1.SYNC_READ, t2)
  return fw


def build_row_silu_program(src_addr: int, dst_addr: int, num_banks: int,
                           *, core, tiles: int) -> Program:
  old_body = add1.math_add1_replay_row
  add1.math_add1_replay_row = sfpu.make_footprint(sfpu.OPS["silu"], 1)
  try:
    trisc0_fw = add1.trisc0()
    trisc1_fw = add1.trisc1()
    trisc2_fw = add1.trisc2()
  finally:
    add1.math_add1_replay_row = old_body
  brisc_fw = row_silu_brisc()
  ncrisc_fw = add1.ncrisc(num_banks)
  brisc_fw.rta(lambda _x, _y: [src_addr, 0, tiles, num_banks])
  ncrisc_fw.rta(lambda _x, _y: [dst_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])
  prog = Program(
    brisc=brisc_fw,
    ncrisc=ncrisc_fw,
    trisc0=trisc0_fw,
    trisc1=trisc1_fw,
    trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "row_silu_footprint"
  return prog


def convert_kernel(direction: str) -> Brisc:
  if direction not in {"row_to_fp", "fp_to_row"}:
    raise ValueError(direction)
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s1, s3, s4))
  with fw.tile_loop("convert"):
    emit_read_page(fw, s0, s5)
    emit_zero_dst(fw)
    if direction == "row_to_fp":
      emit_row_to_footprint(fw)
    else:
      emit_footprint_to_row(fw)
    emit_write_page(fw, s1, s5)
  return fw


def build_convert_program(direction: str, src_addr: int, dst_addr: int, num_banks: int,
                          *, core, tiles: int) -> Program:
  brisc_fw = convert_kernel(direction)
  brisc_fw.rta(lambda _x, _y: [src_addr, dst_addr, tiles, num_banks])
  prog = Program(brisc=brisc_fw, ncrisc=KernelBase(), trisc0=KernelBase(),
                 trisc1=KernelBase(), trisc2=KernelBase())
  prog.grid = ((core[1],), (core[0],))
  prog.name = direction
  return prog


def build_silu_program(src_addr: int, dst_addr: int, num_banks: int, *, core, tiles: int) -> Program:
  old_body = add1.math_add1_replay_row
  add1.math_add1_replay_row = sfpu.make_footprint(sfpu.OPS["silu"], 1)
  try:
    prog = add1.build_program(src_addr, dst_addr, num_banks, cores=[core], tiles_per_core=tiles)
  finally:
    add1.math_add1_replay_row = old_body
  prog.name = "silu_footprint"
  return prog


def main() -> int:
  p = argparse.ArgumentParser(description="device SwiGLU bridge; needs device")
  p.add_argument("--hidden", type=int, default=8192)
  p.add_argument("--runs", type=int, default=1)
  p.add_argument("--split", action="store_true", help="run the old 4-launch staged path")
  args = p.parse_args()
  if args.hidden % TILE:
    raise ValueError("--hidden must be a multiple of 32")

  rng = np.random.default_rng(107)
  gate = rng.uniform(-4.0, 4.0, size=args.hidden).astype(np.float32)
  up = rng.uniform(-2.0, 2.0, size=args.hidden).astype(np.float32)
  gate_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(gate), gate.shape)
  up_bf16 = mm.from_bf16_device_bytes(mm.to_bf16_device_bytes(up), up.shape)
  tiles = args.hidden // TILE

  with harness.open_device() as device:
    core = device.cores[0]
    num_banks = len(device.dram.bank_tiles)
    gate_row = device.alloc_write(elw.to_bf16_bytes(vector_to_row_tiles(gate_bf16, args.hidden)),
                                  dtype=Dtype.Float16_b,
                                  shape=(tiles, TILE, TILE), name="swiglu_gate_row")
    up_row = device.alloc_write(elw.to_bf16_bytes(vector_to_row_tiles(up_bf16, args.hidden)),
                                dtype=Dtype.Float16_b,
                                shape=(tiles, TILE, TILE), name="swiglu_up_row")
    silu_row = device.dram.alloc(tiles, dtype=Dtype.Float16_b,
                                 shape=(tiles, TILE, TILE), name="swiglu_silu_row")
    out_row = device.dram.alloc(tiles, dtype=Dtype.Float16_b,
                                shape=(tiles, TILE, TILE), name="swiglu_out_row")

    if args.split:
      gate_fp = device.dram.alloc(tiles, dtype=Dtype.Float16_b,
                                  shape=(tiles, TILE, TILE), name="swiglu_gate_fp")
      silu_fp = device.dram.alloc(tiles, dtype=Dtype.Float16_b,
                                  shape=(tiles, TILE, TILE), name="swiglu_silu_fp")
      progs = [
        build_convert_program("row_to_fp", gate_row.addr, gate_fp.addr, num_banks, core=core, tiles=tiles),
        build_silu_program(gate_fp.addr, silu_fp.addr, num_banks, core=core, tiles=tiles),
        build_convert_program("fp_to_row", silu_fp.addr, silu_row.addr, num_banks, core=core, tiles=tiles),
      ]
    else:
      gate_fp = None
      silu_fp = device.dram.alloc(tiles, dtype=Dtype.Float16_b,
                                  shape=(tiles, TILE, TILE), name="swiglu_silu_fp")
      progs = [
        build_row_silu_program(gate_row.addr, silu_fp.addr, num_banks, core=core, tiles=tiles),
        build_convert_program("fp_to_row", silu_fp.addr, silu_row.addr, num_banks, core=core, tiles=tiles),
      ]
    mul_prog = resgemv.build_two_source_binary("mul", silu_row.addr, up_row.addr, out_row.addr,
                                               num_banks, core=core, tiles=tiles)
    mul_prog.name = "swiglu_mul"
    progs.append(mul_prog)
    times = []
    for _ in range(args.runs):
      for prog in progs:
        times.extend(device.run(prog))
    gate_fp_raw = device.dram_read(gate_fp) if gate_fp is not None else None
    silu_fp_raw = device.dram_read(silu_fp) if silu_fp is not None else None
    silu_row_raw = device.dram_read(silu_row)
    out_raw = device.dram_read(out_row)

  gate_fp_vals = footprint_values(gate_fp_raw, tiles, args.hidden) if gate_fp_raw is not None else None
  silu_fp_vals = footprint_values(silu_fp_raw, tiles, args.hidden) if silu_fp_raw is not None else None
  silu_row_vals = row_tiles_to_vector(silu_row_raw, tiles, args.hidden)
  got = row_tiles_to_vector(out_raw, tiles, args.hidden)
  ref_silu = gate_bf16 / (1.0 + np.exp(-gate_bf16))
  ref = elw.to_bf16(ref_silu * up_bf16)
  if gate_fp_vals is None:
    stage_ok = True
  else:
    stage_ok = bool(np.array_equal(
      np.frombuffer(mm.to_bf16_device_bytes(gate_fp_vals), dtype=np.uint16),
      np.frombuffer(mm.to_bf16_device_bytes(gate_bf16), dtype=np.uint16),
    ))
  silu_ref = elw.to_bf16(ref_silu)
  silu_ok = bool(np.allclose(
    silu_fp_vals if silu_fp_vals is not None else silu_row_vals,
    silu_ref,
    atol=5.0e-2,
    rtol=5.0e-2,
  ))
  swiglu_ok = bool(np.allclose(got, ref, atol=8.0e-2, rtol=8.0e-2))
  ok = stage_ok and silu_ok and swiglu_ok

  mode = "split" if args.split else "row_silu_fused"
  print("device SwiGLU bridge")
  print(f"  hidden={args.hidden} runs={args.runs}")
  print(f"  mode={mode}")
  if times:
    print(f"  launches={len(progs) * args.runs} avg={sum(t['us'] for t in times) / len(times):.1f} us")
  print(f"  row->footprint: {'PASS' if stage_ok else 'FAIL'}")
  print(f"  silu: {'PASS' if silu_ok else 'FAIL'}")
  print(f"  swiglu row: {'PASS' if swiglu_ok else 'FAIL'}")
  if not silu_ok:
    silu_got = silu_fp_vals if silu_fp_vals is not None else silu_row_vals
    diff = np.abs(silu_got - silu_ref)
    i = int(np.argmax(diff))
    print(f"    silu max diff i={i} got={float(silu_got[i]):.6g} ref={float(silu_ref[i]):.6g} gate={float(gate_bf16[i]):.6g}")
    tile = (i // TILE) * TILE
    print(f"    silu got[{tile}:{tile + 8}]={[float(x) for x in silu_got[tile:tile + 8]]}")
    print(f"    silu ref[{tile}:{tile + 8}]={[float(x) for x in silu_ref[tile:tile + 8]]}")
  if not swiglu_ok:
    diff = np.abs(got - ref)
    i = int(np.argmax(diff))
    print(f"    max diff i={i} got={float(got[i]):.6g} ref={float(ref[i]):.6g}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
