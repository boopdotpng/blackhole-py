#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))
if str(EXAMPLES) not in sys.path:
  sys.path.insert(0, str(EXAMPLES))

from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  TTELWMUL, TTMOP, TTNOP, TTSEMGET, TTSEMPOST, TTSEMWAIT, TTSETADCZW,
  TTSETRWC, TTSTALLWAIT, TTUNPACR, TTZEROACC,
  a0, a1, a2, a5, s0, s1, s2, s3, s4, s5, t0, t1, t2, t3, t4, t5,
  t6, zero,
)
from matmul_peak import RiscSync  # noqa: E402
from program import Dtype, Program  # noqa: E402
from ttk.addrs import p100_dram_bank_endpoint_coords  # noqa: E402
from ttk.cb import CircularBuffer as CB  # noqa: E402
from ttk.mailbox import BriscMailbox as BM, TriscLocalMem as TLM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import (  # noqa: E402
  Cfg, MopCfg, TensixL1, TensixRegs, TensixSem, TensixSemWait, TensixStall,
  TensixWait, ThreadCfg,
)

import add1  # noqa: E402


TILE = 32
DTYPE = Dtype.Float16_b
TILE_BYTES = DTYPE.tile_size
X_CB = 0
WEIGHT_CB = 1
OUT_CB = 16
CB_DEPTH = 8

SYNC_L1 = TensixL1.DATA_BUFFER_SPACE_BASE + 0x20000
SYNC_TRISC_START = SYNC_L1
SYNC_READ = SYNC_L1 + 4
SYNC_DONE0 = SYNC_L1 + 8
SYNC_DONE1 = SYNC_L1 + 12
SYNC_DONE2 = SYNC_L1 + 16
SYNC_TRISC_INIT = SYNC_L1 + 20
SYNC = RiscSync(start=SYNC_TRISC_START, trisc_init=SYNC_TRISC_INIT)

# add1.trisc2()/ncrisc() close over add1's sync constants, so patch the module
# before reusing those roles with an extra input CB.
add1.SYNC_L1 = SYNC_L1
add1.SYNC_TRISC_START = SYNC_TRISC_START
add1.SYNC_READ = SYNC_READ
add1.SYNC_DONE0 = SYNC_DONE0
add1.SYNC_DONE1 = SYNC_DONE1
add1.SYNC_DONE2 = SYNC_DONE2
add1.SYNC_TRISC_INIT = SYNC_TRISC_INIT
add1.SYNC = SYNC

STALL_MATH_PACK_ROOM = TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU
WAIT_MATH_AND_SFPU = TensixWait.MATH | TensixWait.SFPU

UNPACK_SRCA = TTUNPACR(0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1)
UNPACK_SRCB = TTUNPACR(1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1)
UNPACK_ROW_BCAST_MOP_CFG = MopCfg(
  # LLK BroadcastType::ROW unpack_AB: unpack B, unpack A, and rewind B's
  # Z-counter at the end so the next face row reuses the same weight rows.
  loop_outer=2,
  loop_inner=2,
  template=[
    TTNOP(), TTSETADCZW(2, 0, 0, 0, 0, 1), TTNOP(),
    UNPACK_SRCB, UNPACK_SRCA, UNPACK_SRCA, UNPACK_SRCA,
  ],
)

BCAST_ROW = 2
ELW_ADDR_MOD_ROW = 0
ELW_ADDR_MOD_FIDELITY = 2
ELW_ADDR_MOD_FACE = 3
ELWMUL_ROW_HIFI2_MOP_CFG = MopCfg(
  # TT-LLK eltwise_binary_configure_mop_standard<ELWMUL, ROW, HiFi2> for a
  # 16-row face: two fidelity phases over two 8-row chunks. Runtime runs this
  # MOP once per face.
  loop_outer=2,
  loop_inner=2,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    TTELWMUL(0, 0, BCAST_ROW, ELW_ADDR_MOD_ROW, 0),
    TTNOP(),
    TTELWMUL(3, 0, BCAST_ROW, ELW_ADDR_MOD_FACE, 0),
    TTELWMUL(0, 0, BCAST_ROW, ELW_ADDR_MOD_FIDELITY, 0),
  ],
)


class Trisc(add1.Trisc):
  def __init__(self, thread_id: int):
    super().__init__(thread_id, SYNC)


class Brisc(add1.Brisc):
  pass


def _to_bf16(x) -> np.ndarray:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return ((u >> 16) << 16).view("<f4")


def _to_bf16_bytes(x) -> bytes:
  return (np.asarray(x, dtype="<f4").view("<u4") >> 16).astype("<u2").tobytes()


def _from_bf16_bytes(raw: bytes, shape: tuple[int, ...]) -> np.ndarray:
  return (np.frombuffer(raw, dtype="<u2").astype("<u4") << 16).view("<f4").reshape(shape)


def trisc0() -> Trisc:
  fw = Trisc(0)
  fw.prologue()
  fw.unpack.init(dtype=DTYPE, tile_bytes=TILE_BYTES, mop_cfg=UNPACK_ROW_BCAST_MOP_CFG)
  fw.init_barrier()

  sec0 = Cfg.THCON_SEC0_REG3_Base_address.addr32
  sec1 = Cfg.THCON_SEC1_REG3_Base_address.addr32

  with fw.tile_loop():
    fw.cb_wait_front(fw.data["cb_interface"], X_CB)
    fw.cb_wait_front(fw.data["cb_interface"], WEIGHT_CB)
    fw.cb_read_ptr(fw.data["cb_interface"], X_CB, out=s0)
    fw.cb_read_ptr(fw.data["cb_interface"], WEIGHT_CB, out=s1)
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
    fw.li(t2, TensixRegs.CFG_BASE + sec0 * 4)
    a_done = fw._new_label("sec0_done")
    fw.beq(t1, zero, a_done)
    fw.addi(t2, t2, 4)
    fw.label(a_done)
    fw.addi(t3, s0, -1)
    fw.sw(t3, t2, 0)

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
    set_ctx1 = fw._new_label("set_ctx1")
    ctx_set = fw._new_label("ctx_set")
    fw.beq(t1, zero, set_ctx1)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 0)
    fw.j(ctx_set)
    fw.label(set_ctx1)
    fw.setc16(ThreadCfg.UNPACK_MISC_CFG_CfgContext, 257)
    fw.label(ctx_set)

    fw.cb_pop_front(fw.data["cb_interface"], X_CB, tensix_ack=True)
    fw.cb_pop_front(fw.data["cb_interface"], WEIGHT_CB, tensix_ack=True)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_DONE0, t2)
  return fw


def _configure_elwmul_row_hifi2(fw: Trisc) -> Trisc:
  fw.write_mop_cfg(ELWMUL_ROW_HIFI2_MOP_CFG, 1)
  # TT-LLK eltwise_binary_configure_addrmod<ELWMUL, ROW, HiFi2>.
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC0_Src, 0x0008)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC0, 0x0008)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC0_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC2_Src, 0x8080)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC2, 0x2400)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC2_Bias, 0)
  fw.setc16(ThreadCfg.ADDR_MOD_AB_SEC3_Src, 0x8080)
  fw.setc16(ThreadCfg.ADDR_MOD_DST_SEC3, 0x9008)
  fw.setc16(ThreadCfg.ADDR_MOD_BIAS_SEC3_Bias, 0)
  return fw


def trisc1() -> Trisc:
  fw = Trisc(1)
  fw.prologue()
  fw.math.init(dtype=DTYPE, mop_cfg=ELWMUL_ROW_HIFI2_MOP_CFG)
  _configure_elwmul_row_hifi2(fw)
  fw.init_barrier()

  with fw.tile_loop():
    fw.emit(TTSEMWAIT(
      STALL_MATH_PACK_ROOM,
      TensixSem.mask(TensixSem.MATH_PACK),
      TensixSemWait.STALL_ON_MAX,
    ))
    fw.read32(t1, fw.data["dest_offset_id"])
    add1.write_trisc1_dest_offset_instr(fw, t1, t2, t3)
    fw.emit(TTZEROACC(3, 0, 0, 1, 0))
    fw.emit(TTSTALLWAIT(TensixStall.MATH, TensixWait.SRCA_VLD | TensixWait.SRCB_VLD))
    for _ in range(4):
      fw.emit(TTMOP(1, 0, 0))
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
    add1.write_trisc1_dest_offset_instr(fw, t2, t1, t3)
  return fw


def brisc(dram_bank_coords: list[int]) -> Brisc:
  fw = Brisc()
  fw.read_rta_from(BM.RTA_L1_BASE_PTR, (s0, s2, s3, s4))
  for addr in (
    SYNC_TRISC_START, SYNC_READ, SYNC_DONE0, SYNC_DONE1, SYNC_DONE2,
    SYNC_TRISC_INIT, SYNC_TRISC_INIT + 4, SYNC_TRISC_INIT + 8,
  ):
    fw.write32(addr, 0)
  fw.write32(SYNC_TRISC_START, 0x00010101)
  with fw.tile_loop("brisc"):
    for cb_id, off in ((X_CB, 0), (WEIGHT_CB, 1)):
      fw.cb_reserve_back(BM.CB_INTERFACE, cb_id)
      fw.slli(a1, s5, 1)
      fw.add(a1, a1, s2)
      fw.addi(a1, a1, off)
      fw.mv(a0, s0)
      fw.mv(a2, s4)
      fw.dram_tile_addr_static(dram_bank_coords)
      fw.local_noc0_coord(a5)
      fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      fw.addi(t4, t4, 1)
      fw.cb_write_ptr(BM.CB_INTERFACE, cb_id, out=t5)
      fw.li(t6, TILE_BYTES)
      fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
      fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
      fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
      wait = fw._new_label("brisc_read_wait")
      fw.label(wait)
      fw.lw(t1, t0, 0)
      fw.bltu(t1, t4, wait)
      fw.fence()
      fw.cb_push_back(BM.CB_INTERFACE, cb_id)
    fw.addi(t2, s5, 1)
    fw.signal_sync(SYNC_READ, t2)
  return fw


def build_program(
  src_addr: int,
  dst_addr: int,
  num_banks: int,
  core: tuple[int, int],
  tiles: int,
  *,
  harvested_dram_bank: int | None,
) -> Program:
  brisc_fw = brisc(p100_dram_bank_endpoint_coords(harvested_dram_bank, 0)[:num_banks])
  ncrisc_fw = add1.ncrisc(p100_dram_bank_endpoint_coords(harvested_dram_bank, 1)[:num_banks])
  trisc0_fw = trisc0()
  trisc1_fw = trisc1()
  trisc2_fw = add1.trisc2()

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
    cbs=[(X_CB, TILE_BYTES, CB_DEPTH), (WEIGHT_CB, TILE_BYTES, CB_DEPTH), (OUT_CB, TILE_BYTES, CB_DEPTH)],
  )
  prog.grid = ((core[1],), (core[0],))
  prog.name = "hifi2_eltwise_probe"
  return prog


def main() -> int:
  rng = np.random.default_rng(17)
  tiles = 1
  a = _to_bf16(rng.uniform(-2.0, 2.0, (tiles, TILE, TILE)))
  b = _to_bf16(rng.uniform(0.25, 2.0, (tiles, TILE, TILE)))
  src = np.empty((2 * tiles, TILE, TILE), dtype=np.float32)
  src[0::2] = a
  src[1::2] = b

  device = Device()
  try:
    src_buf = device.alloc_write(_to_bf16_bytes(src), dtype=DTYPE, shape=(2 * tiles, TILE, TILE), name="hifi2_src")
    dst_buf = device.dram.alloc(tiles, dtype=DTYPE, shape=(tiles, TILE, TILE), name="hifi2_dst")
    core = device.cores[0]
    prog = build_program(
      src_buf.addr,
      dst_buf.addr,
      len(device.dram.bank_tiles),
      core,
      tiles,
      harvested_dram_bank=device.board_info.harvested_dram_bank,
    )
    device.run(prog)
    got = _from_bf16_bytes(device.dram_read(dst_buf), (tiles, TILE, TILE))
  finally:
    device.close()

  ref = _to_bf16(a * b[:, 0:1, :])
  abs_err = np.abs(got - ref)
  ok = bool(np.allclose(got, ref, atol=2e-2, rtol=2e-2))
  print(f"{'PASS' if ok else 'FAIL'} hifi2 row-bcast eltwise mul max_abs={float(abs_err.max()):.6g}")
  if not ok:
    worst = np.unravel_index(int(np.argmax(abs_err)), abs_err.shape)
    print(f"  worst={worst} got={float(got[worst]):.8g} ref={float(ref[worst]):.8g}")
    print(f"  got[0,0,:8]={got[0, 0, :8].tolist()}")
    print(f"  ref[0,0,:8]={ref[0, 0, :8].tolist()}")
    print(f"  got[0,16,:8]={got[0, 16, :8].tolist()}")
    print(f"  ref[0,16,:8]={ref[0, 16, :8].tolist()}")
  return 0 if ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
