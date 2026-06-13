#!/usr/bin/env python3
"""Blackhole eltwise binary microbench: tile+tile add/sub/mul, bf16.

First two-operand pipeline: BRISC feeds tile A into CB0 and tile B into CB1;
TRISC0 unpacks A->SrcA (SEC0) and B->SrcB (SEC1) per LLK llk_unpack_AB;
TRISC1 runs the LLK eltwise-binary math MOP (2 ELW per face, addr_mod srcA=
srcB=dest=8, SETRWC CLR_AB end-op); TRISC2/NCRISC pack+drain as in add1.

LLK reference: tt_llk_blackhole llk_math_eltwise_binary.h / llk_unpack_AB.h
(NONE broadcast, LoFi, face_r_dim=16). --iters N adds a timed stream of N
tiles per op with TRISC1 wall-clock around its tile loop -> cyc/tile.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import numpy as np

from device import Device
from dsl import (
  TTELWADD, TTELWMUL, TTELWSUB, TTMOP, TTNOP, TTSEMGET, TTSEMPOST, TTSEMWAIT,
  TTSETADCZW, TTSETRWC, TTSTALLWAIT, TTUNPACR, TTZEROACC,
  a0, a1, a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk.mailbox import BriscMailbox as BM, TriscLocalMem as TLM
from ttk.tensix import (
  Cfg, MopCfg, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait,
  ThreadCfg,
)
from ttk.noc import NOC

from examples import add1
from examples.add1 import (
  Brisc, CB_DEPTH, OUT_CB, STALL_MATH_PACK_ROOM, TILE_BYTES, Trisc,
  WAIT_MATH_AND_SFPU, write_trisc1_dest_offset_instr,
)
from matmul_peak import RiscSync
from ttk.tensix import TensixL1

# add1 puts its sync words at DATA_BUFFER_SPACE_BASE+0x10000, sized for two
# CBs (2x 32 KiB). This bench adds CB1, so CB16's data lands on those words
# (output tile 0 got done0/done2 flags at +8/+16). Move sync past 3 CBs and
# patch add1's module constants so its trisc2/ncrisc use the same layout.
_SYNC_L1 = TensixL1.DATA_BUFFER_SPACE_BASE + 0x20000
add1.SYNC_L1 = _SYNC_L1
add1.SYNC_TRISC_START = SYNC_TRISC_START = _SYNC_L1
add1.SYNC_READ = SYNC_READ = _SYNC_L1 + 4
add1.SYNC_DONE0 = SYNC_DONE0 = _SYNC_L1 + 8
add1.SYNC_DONE1 = SYNC_DONE1 = _SYNC_L1 + 12
add1.SYNC_DONE2 = _SYNC_L1 + 16
add1.SYNC_TRISC_INIT = SYNC_TRISC_INIT = _SYNC_L1 + 20
add1.SYNC = SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)

TILE = 32
DTYPE = Dtype.Float16_b
RESULT_ADDR = 0x12D000

# --- LLK llk_unpack_AB NONE-bcast: A->SrcA (block 0), B->SrcB (block 1). ---
UNPACK_SRCA = TTUNPACR(0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1)
UNPACK_SRCB = TTUNPACR(1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1)
# outer=2 face-rows, inner=2 face-cols, body = (A, B) alternating; the two
# *Last slots must be SrcB so the final yields stay paired.
UNPACK_AB_MOP_CFG = MopCfg(
  loop_outer=2, loop_inner=2,
  template=[TTNOP(), TTNOP(), TTNOP(), UNPACK_SRCA, UNPACK_SRCB, UNPACK_SRCB, UNPACK_SRCB],
)

# --- LLK llk_math_eltwise_binary NONE-bcast LoFi: 2 ELW per face (8 rows
# each, addr_mod srcA=srcB=dest=8), per-face SETRWC(CLR_AB, CR_AB, SET_AB). ---
ELW_OPS = {"add": TTELWADD, "sub": TTELWSUB, "mul": TTELWMUL}
ELW_ADDR_MOD = 2  # SEC2: mova2d init sets srcA=8 dest=8; we add srcB=8

def elw_math_mop(op: str) -> MopCfg:
  elw = ELW_OPS[op](0, 0, 0, ELW_ADDR_MOD, 0)
  end = TTSETRWC(3, 3, 0, 0, 0, 3)  # CLR_AB | CR_AB | SET_AB
  return MopCfg(loop_outer=4, loop_inner=2,
                template=[TTNOP(), end, TTNOP(), elw, TTNOP(), elw, elw])


def trisc0(unpack_mop: MopCfg = UNPACK_AB_MOP_CFG) -> Trisc:
  """add1's trisc0 with a second CB: A addr -> SEC0 base, B addr -> SEC1."""
  fw = Trisc(0, SYNC)
  fw.prologue()
  fw.unpack.init(dtype=DTYPE, tile_bytes=TILE_BYTES, mop_cfg=unpack_mop)
  fw.init_barrier()

  sec0 = Cfg.THCON_SEC0_REG3_Base_address.addr32
  sec1 = Cfg.THCON_SEC1_REG3_Base_address.addr32

  with fw.tile_loop():
    fw.cb_wait_front(fw.data["cb_interface"], 0)
    fw.cb_wait_front(fw.data["cb_interface"], 1)
    fw.cb_read_ptr(fw.data["cb_interface"], 0, out=s0)
    fw.cb_read_ptr(fw.data["cb_interface"], 1, out=s1)
    fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 15))

    wait_unp = fw._new_label("wait_unpack_ctx")
    wait_unp_done = fw._new_label("wait_unpack_ctx_done")
    fw.li(t0, TensixRegs.PC_UNPACK_SYNC)
    fw.label(wait_unp)
    fw.lw(t1, t0, 0)
    fw.andi(t1, t1, 0xFE)
    fw.beq(t1, zero, wait_unp_done)
    fw.fence()
    fw.j(wait_unp)
    fw.label(wait_unp_done)

    fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
    # SEC0 base (ctx0/ctx1) <- A read ptr - 1
    fw.li(t2, TensixRegs.CFG_BASE + sec0 * 4)
    a_done = fw._new_label("sec0_done")
    fw.beq(t1, zero, a_done)
    fw.addi(t2, t2, 4)
    fw.label(a_done)
    fw.addi(t3, s0, -1)
    fw.sw(t3, t2, 0)
    # SEC1 base (ctx0/ctx1) <- B read ptr - 1
    fw.li(t2, TensixRegs.CFG_BASE + sec1 * 4)
    b_done = fw._new_label("sec1_done")
    fw.beq(t1, zero, b_done)
    fw.addi(t2, t2, 4)
    fw.label(b_done)
    fw.addi(t3, s1, -1)
    fw.sw(t3, t2, 0)
    fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

    fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
    fw.emit(TTMOP(1, 0, 0))
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
    fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, t2)
    ctx1 = fw._new_label("set_ctx1")
    ctx_set = fw._new_label("ctx_set")
    fw.beq(t1, zero, ctx1)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
    fw.j(ctx_set)
    fw.label(ctx1)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
    fw.label(ctx_set)
    fw.cb_pop_front(fw.data["cb_interface"], 0, tensix_ack=True)
    fw.cb_pop_front(fw.data["cb_interface"], 1, tensix_ack=True)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE0, t2)
  return fw


def trisc1(op: str, *, timed: bool = False, math_mop: MopCfg | None = None,
           addr_mod_ab: int = 0x0808, mop_runs: int = 1,
           between_runs=None, post_mop=None) -> Trisc:
  """add1's trisc1 with the ELW MOP instead of MOVA2D+SFPU.

  ``math_mop`` overrides the NONE-bcast template; ``mop_runs``/``between_runs``
  implement the LLK COL-bcast pattern (run per face-row + SETRWC CLR_B);
  ``post_mop`` the SCALAR pattern (SETRWC CLR_B SET_D after the tile)."""
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=math_mop if math_mop is not None else elw_math_mop(op))
  # eltwise binary ADDR_MOD (LLK ADDR_MOD_0): srcA=8, dest=8; srcB advance
  # depends on broadcast type (8 for NONE/COL, 0 for ROW/SCALAR).
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC2_Src, addr_mod_ab)
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
    # Clear this tile's dest half before the ELW MOP (math.init zeroes only
    # once); without this, tile-0 carries stale dest junk in row 0.
    fw.emit(TTZEROACC(3, 0, 0, 1, 0))
    fw.emit(TTSTALLWAIT(TensixStall.MATH, TensixWait.SRCA_VLD | TensixWait.SRCB_VLD))
    for run in range(mop_runs):
      if run and between_runs is not None:
        fw.emit(between_runs)
      fw.emit(TTMOP(1, 0, 0))
    if post_mop is not None:
      fw.emit(post_mop)
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
      # cumulative wall-clock since loop start; the last tile's write is the
      # total stream duration (lo 32 bits only).
      harness.read_wall_clock(fw, a4, a5)
      fw.sub(a4, a4, a2)
      fw.li(a5, RESULT_ADDR)
      fw.sw(a4, a5, 0)
  return fw


def brisc() -> Brisc:
  """add1's brisc reading TWO tiles per iteration: A(2i)->CB0, B(2i+1)->CB1."""
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, add1.SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    for cb, off in ((0, 0), (1, 1)):
      fw.cb_reserve_back(BM.CB_INTERFACE, cb)
      fw.slli(a1, s5, 1)
      fw.add(a1, a1, s2)
      fw.addi(a1, a1, off)
      fw.mv(a0, s0)
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
    fw.signal_sync(SYNC_READ, t2)
  return fw


def build_program(op: str, src_addr: int, dst_addr: int, num_banks: int, *,
                  core, tiles: int, timed: bool = False,
                  unpack_mop: MopCfg = UNPACK_AB_MOP_CFG,
                  trisc1_kwargs: dict | None = None) -> Program:
  brisc_fw = brisc()
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = trisc0(unpack_mop)
  trisc1_fw = trisc1(op, timed=timed, **(trisc1_kwargs or {}))
  trisc2_fw = add1.trisc2()
  brisc_fw.rta(lambda x, y: [src_addr, 0, tiles, num_banks])
  ncrisc_fw.rta(lambda x, y: [dst_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])
  prog = Program(
    brisc=brisc_fw, ncrisc=ncrisc_fw,
    trisc0=trisc0_fw, trisc1=trisc1_fw, trisc2=trisc2_fw,
    cbs=[(0, TILE_BYTES, CB_DEPTH), (1, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = f"eltwise_{op}"
  return prog


def to_bf16(x):
  u = np.asarray(x, dtype="<f4").view("<u4")
  return ((u >> 16) << 16).view("<f4")


def to_bf16_bytes(x):
  return (np.asarray(x, dtype="<f4").view("<u4") >> 16).astype("<u2").tobytes()


def from_bf16_bytes(raw, shape):
  return (np.frombuffer(raw, dtype="<u2").astype("<u4") << 16).view("<f4").reshape(shape)


NUMPY_OP = {"add": np.add, "sub": np.subtract, "mul": np.multiply}
# LoFi mul truncates SrcA/SrcB mantissas to ~5 bits -> up to ~3% low; add/sub
# are exact up to bf16 rounding.
TOL = {"add": (2e-2, 2e-2), "sub": (2e-2, 2e-2), "mul": (5e-2, 5e-2)}


def matches_face_roll(got, ref, *, atol: float, rtol: float) -> bool:
  return bool(np.allclose(got, np.roll(ref, -16, axis=2), atol=atol, rtol=rtol))


def run_op(device: Device, op: str, a, b, *, tiles: int, timed: bool = False,
           name: str | None = None, **build_kwargs):
  n = tiles
  src = np.empty((2 * n, TILE, TILE), dtype=np.float32)
  src[0::2] = a
  src[1::2] = b
  tag = name or f"elw_{op}"
  src_buf = device.alloc_write(to_bf16_bytes(src), dtype=DTYPE,
                               shape=(2 * n, TILE, TILE), name=f"{tag}_src")
  dst_buf = device.dram.alloc(n, dtype=DTYPE, shape=(n, TILE, TILE), name=f"{tag}_dst")
  core = device.cores[0]
  prog = build_program(op, src_buf.addr, dst_buf.addr, len(device.dram.bank_tiles),
                       core=core, tiles=n, timed=timed, **build_kwargs)
  prog.name = tag
  device.run(prog)
  got = from_bf16_bytes(device.dram_read(dst_buf), (n, TILE, TILE))
  return got


def main() -> int:
  import argparse
  parser = argparse.ArgumentParser(description="eltwise binary add/sub/mul microbench; needs device")
  parser.add_argument("--iters", type=int, default=0, help="timed stream of N tiles per op")
  args = parser.parse_args()

  rng = np.random.default_rng(11)
  a = to_bf16(rng.uniform(-2.0, 2.0, (1, TILE, TILE)))
  b = to_bf16(rng.uniform(-2.0, 2.0, (1, TILE, TILE)))

  ok = True
  cycles = {}
  with harness.open_device() as device:
    core = device.cores[0]
    for op in ("add", "sub", "mul"):
      got = run_op(device, op, a, b, tiles=1)
      ref = to_bf16(NUMPY_OP[op](a, b))
      max_abs = float(np.max(np.abs(got - ref)))
      atol, rtol = TOL[op]
      op_ok = bool(np.allclose(got, ref, atol=atol, rtol=rtol))
      print(f"  {op}: {'PASS' if op_ok else 'FAIL'} max_abs={max_abs:.6g}")
      if not op_ok:
        print(f"    got[0,:4]={got[0,0,:4].tolist()} ref[0,:4]={ref[0,0,:4].tolist()}")
        if matches_face_roll(got, ref, atol=atol, rtol=rtol):
          print("    diagnostic: output matches ref rolled left by 16 columns; row-major contract still FAIL")
      ok = ok and op_ok

    if args.iters > 0:
      for op in ("add", "sub", "mul"):
        n = args.iters
        harness.clear_window(device, core, [(RESULT_ADDR, 8)])
        an = to_bf16(rng.uniform(-2.0, 2.0, (n, TILE, TILE)))
        bn = to_bf16(rng.uniform(-2.0, 2.0, (n, TILE, TILE)))
        got = run_op(device, op, an, bn, tiles=n, timed=True)
        ref = to_bf16(NUMPY_OP[op](an, bn))
        atol, rtol = TOL[op]
        s_ok = bool(np.allclose(got, ref, atol=atol, rtol=rtol))
        face_roll_ok = matches_face_roll(got, ref, atol=atol, rtol=rtol)
        raw = harness.read_window(device, core, RESULT_ADDR, 4)
        cycles[op] = (int.from_bytes(raw, "little"), s_ok, face_roll_ok)

  print("eltwise binary microbench")
  print(f"  dtype={DTYPE.name} tile=32x32 iters={args.iters}")
  for op, (total, s_ok, face_roll_ok) in cycles.items():
    print(f"    {op}: {total} cyc / {args.iters} tiles -> {total / args.iters:.1f} cyc/tile"
          f" ({total / args.iters / 1024:.3f} cyc/elem) stream={'PASS' if s_ok else 'FAIL'}")
    if (not s_ok) and face_roll_ok:
      print("      diagnostic: stream output matches ref rolled left by 16 columns")
    ok = ok and s_ok
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
