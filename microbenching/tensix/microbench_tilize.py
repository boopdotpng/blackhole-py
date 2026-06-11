#!/usr/bin/env python3
"""Blackhole on-device tilize microbench (#8): unpacker tileize_mode.

Tilize via the dedicated hardware path (LLK _llk_unpack_tilize_): the unpacker
reads a 32-row row-major block straight from CB0 and emits a tile to SrcA per
UNPACR, with tileize_mode striding each 1x16 row by the block row pitch:
  THCON_SEC0_REG2 word0 = out_fmt|throttle | tileize_mode<<9 | (row_bytes>>4)<<16
  Tile_x_dim=1024, TileDescriptor x=1024/z=1, SETADCXX 1023 -> whole tile/UNPACR
  per-tile base = block_base + tile_index*64B (in 16B units)
Math = 8x MOVA2D copy (SrcA->dest, single Dvalid: clear AB only at end);
Pack/drain = add1 unchanged. Output validated byte-exact vs host tilize().

Untilize is host-only (final readback boundary). The +1.0 of add1 is dropped.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import numpy as np

from device import Device
from dram import tilize
from dsl import (
  TTMOP, TTMOVA2D, TTNOP, TTSEMGET, TTSEMPOST, TTSEMWAIT, TTSETADCXX,
  TTSETADCZW, TTSETRWC, TTSTALLWAIT, TTUNPACR, TTZEROACC,
  a0, a1, a2, a5, s0, s2, s3, s4, s5, t0, t1, t2, t3, t4, t5, t6, zero,
)
from program import Dtype, Program
from ttk.mailbox import BriscMailbox as BM, TriscLocalMem as TLM
from ttk.tensix import Cfg, MopCfg, TensixRegs, TensixSem, TensixSemWait, TensixStall, TensixWait, ThreadCfg
from ttk.noc import NOC

from examples import add1
from examples.add1 import (
  Brisc, CB_DEPTH, OUT_CB, STALL_MATH_PACK_ROOM, SYNC, SYNC_DONE0, SYNC_DONE1,
  SYNC_READ, SYNC_TRISC_INIT, SYNC_TRISC_START, TILE_BYTES, Trisc,
  WAIT_MATH_AND_SFPU, write_trisc1_dest_offset_instr, _UNPACK_NOP,
)

TILE = 32
DTYPE = Dtype.Float16_b
DBG_L1 = 0x12D000

# one UNPACR per FACE: 256 datums (16 rows x 16 cols0-15 of the strided block),
# SrcA Dvalid per face -- exactly add1's unpack cadence, so math/pack are add1's.
UNPACK_TILIZE_FACE_MOP = MopCfg(
  loop_outer=1, loop_inner=1,
  template=[
    TTUNPACR(AddrMode=1, OvrdThreadId=1, SetDatValid=1, Last=1),
    TTNOP(), TTNOP(),
    _UNPACK_NOP,
    TTNOP(), TTNOP(), TTNOP(),
  ],
)


def trisc0(ct_dim: int, shift_hi: int | None = None) -> Trisc:
  """add1 trisc0 with tileize-mode row stride; one UNPACR per FACE, base =
  block_base + tile*64B + (f&1)*32B + (f>>1)*16 rows. Everything else add1."""
  fw = Trisc(0, SYNC)
  fw.prologue()
  fw.unpack.init(dtype=DTYPE, tile_bytes=TILE_BYTES, mop_cfg=UNPACK_TILIZE_FACE_MOP)
  # tileize override: ONLY tileize_mode + row stride; default 0x0001 -> 256 B
  row_bytes = ct_dim * TILE * 2
  hi = (row_bytes >> 8) if shift_hi is None else shift_hi
  fw.write32(Cfg.THCON_SEC0_REG2, 0x25 | (1 << 9) | (hi << 16))
  fw.init_barrier()

  face_rows_units = 16 * row_bytes // 16   # 16 block rows in 16B units

  with fw.tile_loop():
    fw.cb_wait_front(fw.data["cb_interface"], 0)
    fw.cb_read_ptr(fw.data["cb_interface"], 0, out=s0)
    fw.emit(TTSETADCZW(3, 0, 0, 0, 0, 15))

    for f in range(4):
      wait_unp = fw._new_label(f"wait_unpack_ctx{f}")
      wait_done = fw._new_label(f"wait_unpack_ctx_done{f}")
      fw.li(t0, TensixRegs.PC_UNPACK_SYNC)
      fw.label(wait_unp)
      fw.lw(t1, t0, 0)
      fw.andi(t1, t1, 0xFE)
      fw.beq(t1, zero, wait_done)
      fw.fence()
      fw.j(wait_unp)
      fw.label(wait_done)

      fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
      fw.li(t2, TensixRegs.CFG_BASE + 76 * 4)
      cfg_done = fw._new_label(f"cfg_addr_done{f}")
      fw.beq(t1, zero, cfg_done)
      fw.addi(t2, t2, 4)
      fw.label(cfg_done)
      fw.li(t3, ct_dim)
      fw.remu(t3, s5, t3)
      fw.slli(t3, t3, 2)
      fw.add(t3, t3, s0)
      off = -1 + (f & 1) * 2 + (f >> 1) * face_rows_units
      fw.addi(t3, t3, off)
      fw.sw(t3, t2, 0)
      fw.write32(TensixRegs.PC_UNPACK_SYNC, 0)

      fw.emit(TTSTALLWAIT(TensixStall.UNPACK, TensixWait.TRISC_CFG))
      fw.emit(TTMOP(1, 0, 0))
      fw.emit(TTSEMGET(TensixSem.mask(TensixSem.UNPACK_SYNC)))
      fw.read32(t1, TLM.TRISC0_UNPACK_CFG_CONTEXT)
      fw.li(t2, 1)
      fw.sub(t2, t2, t1)
      fw.write32(TLM.TRISC0_UNPACK_CFG_CONTEXT, t2)
      ctx1 = fw._new_label(f"set_ctx1_{f}")
      ctx_set = fw._new_label(f"ctx_set_{f}")
      fw.beq(t1, zero, ctx1)
      fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
      fw.j(ctx_set)
      fw.label(ctx1)
      fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
      fw.label(ctx_set)

    fw.li(t3, ct_dim)
    fw.remu(t3, s5, t3)
    fw.addi(t3, t3, 1)
    fw.li(t2, ct_dim)
    skip = fw._new_label("no_pop")
    fw.bne(t3, t2, skip)
    fw.cb_pop_front(fw.data["cb_interface"], 0, tensix_ack=True)
    fw.label(skip)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE0, t2)
  return fw


def trisc1() -> Trisc:
  """add1 trisc1 with the SFPU +1 replaced by the whole-tile MOVA2D copy MOP."""
  fw = Trisc(1, SYNC)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=add1.MATH_MOP_CFG)
  fw.init_barrier()
  with fw.tile_loop():
    fw.emit(TTSEMWAIT(STALL_MATH_PACK_ROOM, TensixSem.mask(TensixSem.MATH_PACK),
                      TensixSemWait.STALL_ON_MAX))
    fw.read32(t1, fw.data["dest_offset_id"])
    write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTZEROACC(3, 0, 0, 1, 0))
    fw.emit(TTSTALLWAIT(TensixStall.MATH, TensixWait.SRCA_VLD | TensixWait.SRCB_VLD))
    fw.emit(TTMOP(1, 0, 0))
    fw.push_tensix(TTSETRWC(3, 3, 0, 0, 0, 0xF))   # clear AB + counters once per tile
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
  return fw


def brisc(ct_dim: int) -> Brisc:
  """Read ct_dim sequential DRAM pages (one row-major block) per CB0 page."""
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))   # s3 = num blocks
  for addr in (SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, add1.SYNC_DONE2,
               SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    fw.cb_reserve_back(BM.CB_INTERFACE, 0)
    fw.cb_write_ptr(BM.CB_INTERFACE, 0, out=t5)
    for p in range(ct_dim):
      fw.li(a1, ct_dim)
      fw.mul(a1, a1, s5)
      fw.addi(a1, a1, p)
      fw.add(a1, a1, s2)
      fw.mv(a0, s0)
      fw.mv(a2, s4)
      fw.dram_tile_addr_from(BM.DRAM_BANK_TO_NOC_XY, 0)
      fw.local_noc0_coord(a5)
      fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      fw.addi(t4, t4, 1)
      fw.li(t6, TILE_BYTES)
      fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
      fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      wait = fw._new_label(f"brisc_read_wait{p}")
      fw.label(wait)
      fw.lw(t1, t0, 0)
      fw.bltu(t1, t4, wait)
      fw.fence()
      fw.addi(t5, t5, TILE_BYTES // 2)
      fw.addi(t5, t5, TILE_BYTES // 2)
    fw.cb_push_back(BM.CB_INTERFACE, 0)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_READ, t2)
  return fw


def build_program(src_addr: int, dst_addr: int, num_banks: int, *, core, ct_dim: int, blocks: int,
                  shift_hi: int | None = None) -> Program:
  brisc_fw = brisc(ct_dim)
  ncrisc_fw = add1.ncrisc(num_banks)
  trisc0_fw = trisc0(ct_dim, shift_hi)
  trisc1_fw = trisc1()
  trisc2_fw = add1.trisc2()
  tiles = ct_dim * blocks
  brisc_fw.rta(lambda x, y: [src_addr, 0, blocks, num_banks])
  ncrisc_fw.rta(lambda x, y: [dst_addr, 0, tiles, num_banks])
  for fw in (trisc0_fw, trisc1_fw, trisc2_fw):
    fw.rta(lambda _x, _y: [tiles])
  prog = Program(
    brisc=brisc_fw, ncrisc=ncrisc_fw,
    trisc0=trisc0_fw, trisc1=trisc1_fw, trisc2=trisc2_fw,
    cbs=[(0, ct_dim * TILE_BYTES, 4), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "tilize"
  return prog


def main() -> int:
  import argparse
  p = argparse.ArgumentParser(description="on-device tilize microbench; needs device")
  p.add_argument("--ct", type=int, default=4, help="tiles per block row (block = 32 x ct*32)")
  p.add_argument("--blocks", type=int, default=1)
  p.add_argument("--dump", action="store_true", help="map got elems to src positions")
  p.add_argument("--shift-hi", type=lambda s: int(s, 0), default=None,
                 help="override REG2[31:16] shift nibbles (e.g. 0x4444, 0x1111)")
  args = p.parse_args()
  ct, blocks = args.ct, args.blocks

  rng = np.random.default_rng(13)
  src = rng.integers(0, 1 << 16, (blocks, TILE, ct * TILE), dtype=np.uint16)  # raw bf16 bits

  with harness.open_device() as device:
    core = device.cores[0]
    nb = len(device.dram.bank_tiles)
    src_buf = device.alloc_write(src.tobytes(), dtype=DTYPE, shape=(blocks * ct, TILE, TILE), name="til_src")
    dst_buf = device.dram.alloc(blocks * ct, dtype=DTYPE, shape=(blocks * ct, TILE, TILE), name="til_dst")
    prog = build_program(src_buf.addr, dst_buf.addr, nb, core=core, ct_dim=ct, blocks=blocks,
                         shift_hi=args.shift_hi)
    device.run(prog)
    got = np.frombuffer(device.dram_read(dst_buf), dtype=np.uint16)
    if args.dump:
      dbg = harness.read_window(device, core, DBG_L1, 8)
      reg2, desc = int.from_bytes(dbg[:4], "little"), int.from_bytes(dbg[4:], "little")
      print(f"  REG2=0x{reg2:08x} (want tileize bit9 + shift nibbles) TileDesc=0x{desc:08x}")

  ref = np.frombuffer(
    b"".join(tilize(src[b].tobytes(), 2, (TILE, ct * TILE)) for b in range(blocks)), dtype=np.uint16)
  ok = bool(np.array_equal(got, ref))
  print("on-device tilize microbench (unpacker tileize_mode)")
  print(f"  block=32x{ct * TILE} bf16, blocks={blocks}, tiles={ct * blocks}")
  if not ok:
    bad = np.flatnonzero(got != ref)
    print(f"  mismatched elems: {bad.size}/{got.size}, first at {bad[:8].tolist()}")
    print(f"  got {got[bad[:4]].tolist()} ref {ref[bad[:4]].tolist()}")
    if args.dump:
      flat = src[0].ravel()
      pos = {int(v): i for i, v in enumerate(flat)}          # values are ~unique
      for row in range(64):                                  # all 64 rows of tile0
        idxs = [pos.get(int(v), -1) for v in got[row * 16:(row + 1) * 16]]
        starts = idxs[0]
        contig = all(idxs[i] == idxs[0] + i for i in range(16) if idxs[i] != -1)
        print(f"  got[r{row:2}] start={starts:5d} contig={contig} {idxs if not contig else ''}")
  print("PASS" if ok else "FAIL")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
