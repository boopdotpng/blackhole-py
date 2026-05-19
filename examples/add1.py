#!/usr/bin/env python3
from __future__ import annotations

import os
import random
import struct
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("TT_USB", "1")

from asm import Kernel
from device import Device
from dsl import a0, a1, a2, a5, ra, s0, s1, s2, s3, s4, s5, sp, t0, t1, t2, t3, t4, t5, t6, zero
from program import Dtype, Program
from ttk.addrs import BriscMailbox as BM, NOC, TensixL1

TILE_BYTES = Dtype.Float16_b.tile_size
SCRATCH_L1 = TensixL1.DATA_BUFFER_SPACE_BASE


def _bf16(x: float) -> int:
  return struct.unpack("<I", struct.pack("<f", x))[0] >> 16


def _f32(x: int) -> float:
  return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]


def _format_bf16_words(data: bytes, count: int = 16) -> str:
  return " ".join(
    f"{int.from_bytes(data[i : i + 2], 'little'):04x}"
    for i in range(0, min(len(data), count * 2), 2)
  )


def _seed_src_tensor(num_tiles: int, pattern: str) -> bytes:
  if pattern == "ordered":
    return b"".join(_bf16(float(i)).to_bytes(2, "little") for i in range(num_tiles * 32 * 32))
  rng = random.Random(42)
  return b"".join(_bf16(rng.random()).to_bytes(2, "little") for _ in range(num_tiles * 32 * 32))


def _expected_add1(src: bytes) -> bytes:
  out = bytearray(len(src))
  for i in range(0, len(src), 2):
    x = int.from_bytes(src[i : i + 2], "little")
    y = _bf16(_f32(x) + 1.0)
    out[i : i + 2] = y.to_bytes(2, "little")
  return bytes(out)


def _first_mismatch(got: bytes, exp: bytes) -> int | None:
  return next((i for i, (g, e) in enumerate(zip(got, exp)) if g != e), None)


def _read_rta(fw: Kernel):
  fw.read32(t0, BM.RTA_L1_BASE_PTR)
  for reg, off in ((s0, 0), (s1, 4), (s2, 8), (s3, 12), (s4, 16)):
    fw.lw(reg, t0, off)


def _local_noc0_coord(fw: Kernel, out=a5):
  fw.read8(t0, BM.MY_X, tmp_addr=t2)
  fw.read8(t1, BM.MY_Y, tmp_addr=t2)
  fw.slli(t1, t1, 6)
  fw.or_(out, t0, t1)


def _dram_tile_addr(fw: Kernel):
  # a0=bank_base, a1=tile_id, a2=num_banks -> a0=bank_addr, a1=bank_idx, a2=bank_noc_xy
  fw.mv(t0, a1)
  fw.remu(a1, t0, a2)
  fw.divu(t0, t0, a2)
  fw.slli(t0, t0, 11)
  fw.add(a0, a0, t0)
  fw.slli(t1, a1, 1)
  fw.li(t2, BM.DRAM_BANK_TO_NOC_XY)
  fw.add(t2, t2, t1)
  fw.lhu(a2, t2, 0)


def _read_tile_fn(fw: Kernel):
  fw.label("read_tile")
  _dram_tile_addr(fw)
  _local_noc0_coord(fw, a5)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t5, SCRATCH_L1)
  fw.li(t6, TILE_BYTES)
  fw.noc_read(0, 1, a0, 0, a2, t5, t6, ret_coord=a5, a=t0, v=t1)
  fw.noc_wait_atomic_responses(0, zero, addr=t0, val=t1)
  fw.li(t0, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED)
  fw.label("read_tile_wait")
  fw.lw(t1, t0, 0)
  fw.bltu(t1, t4, "read_tile_wait")
  fw.fence()
  fw.ret()


def _write_tile_fn(fw: Kernel):
  fw.label("write_tile")
  _dram_tile_addr(fw)
  fw.read32(t4, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED)
  fw.addi(t4, t4, 1)
  fw.li(t5, SCRATCH_L1)
  fw.li(t6, TILE_BYTES)
  fw.noc_write(0, 0, t5, a0, 0, a2, t6, a=t0, v=t1)
  fw.noc_write_barrier(0, t4, addr=t0, val=t1)
  fw.ret()


def _add1_bf16_fn(fw: Kernel):
  fw.label("add1_bf16")
  fw.srli(t0, a0, 7)
  fw.andi(t0, t0, 0xFF)
  fw.li(t1, 255)
  fw.beq(t0, t1, "add1_bf16_done")
  fw.andi(t1, a0, 0x7F)
  fw.ori(t1, t1, 0x80)
  fw.li(t2, 127)
  fw.bltu(t0, t2, "add1_bf16_lt1")
  fw.beq(t0, t2, "add1_bf16_eq1exp")

  fw.sub(t3, t0, t2)
  fw.li(t4, 8)
  fw.bgeu(t3, t4, "add1_bf16_done")
  fw.li(t4, 128)
  fw.srl(t4, t4, t3)
  fw.add(t1, t1, t4)
  fw.li(t4, 256)
  fw.bltu(t1, t4, "add1_bf16_pack_same_exp")
  fw.addi(t0, t0, 1)
  fw.srli(t1, t1, 1)
  fw.j("add1_bf16_pack_same_exp")

  fw.label("add1_bf16_eq1exp")
  fw.addi(t0, t0, 1)
  fw.addi(t1, t1, 128)
  fw.srli(t1, t1, 1)
  fw.j("add1_bf16_pack_same_exp")

  fw.label("add1_bf16_lt1")
  fw.beq(t0, zero, "add1_bf16_one")
  fw.sub(t3, t2, t0)
  fw.srl(t1, t1, t3)
  fw.li(a0, 0x3F80)
  fw.add(a0, a0, t1)
  fw.ret()

  fw.label("add1_bf16_one")
  fw.li(a0, 0x3F80)
  fw.ret()

  fw.label("add1_bf16_pack_same_exp")
  fw.addi(t1, t1, -128)
  fw.slli(t0, t0, 7)
  fw.or_(a0, t0, t1)
  fw.label("add1_bf16_done")
  fw.ret()


def _add_tile_fn(fw: Kernel):
  fw.label("add_tile")
  fw.addi(sp, sp, -16)
  fw.sw(ra, sp, 12)
  fw.sw(s0, sp, 8)
  fw.sw(s1, sp, 4)
  fw.li(s0, SCRATCH_L1)
  fw.li(s1, TILE_BYTES // 2)
  fw.label("add_tile_loop")
  fw.beq(s1, zero, "add_tile_done")
  fw.lhu(a0, s0, 0)
  fw.call("add1_bf16")
  fw.sh(a0, s0, 0)
  fw.addi(s0, s0, 2)
  fw.addi(s1, s1, -1)
  fw.j("add_tile_loop")
  fw.label("add_tile_done")
  fw.lw(s1, sp, 4)
  fw.lw(s0, sp, 8)
  fw.lw(ra, sp, 12)
  fw.addi(sp, sp, 16)
  fw.ret()


def add1_kernel(num_banks: int) -> Kernel:
  def rtas(core_x: int, core_y: int) -> list[int]:
    del core_x, core_y
    return [0, 0, 0, 0, num_banks]

  fw = Kernel(rtas=rtas)
  fw.addi(sp, sp, -32)
  fw.sw(ra, sp, 28)
  fw.sw(s0, sp, 24)
  fw.sw(s1, sp, 20)
  fw.sw(s2, sp, 16)
  fw.sw(s3, sp, 12)
  fw.sw(s4, sp, 8)
  fw.sw(s5, sp, 4)
  _read_rta(fw)
  fw.li(s5, 0)
  fw.label("main_loop")
  fw.beq(s5, s3, "main_done")
  fw.add(a1, s2, s5)
  fw.mv(a0, s0)
  fw.mv(a2, s4)
  fw.call("read_tile")
  fw.call("add_tile")
  fw.add(a1, s2, s5)
  fw.mv(a0, s1)
  fw.mv(a2, s4)
  fw.call("write_tile")
  fw.addi(s5, s5, 1)
  fw.j("main_loop")
  fw.label("main_done")
  fw.lw(s5, sp, 4)
  fw.lw(s4, sp, 8)
  fw.lw(s3, sp, 12)
  fw.lw(s2, sp, 16)
  fw.lw(s1, sp, 20)
  fw.lw(s0, sp, 24)
  fw.lw(ra, sp, 28)
  fw.addi(sp, sp, 32)
  fw.ret()

  _read_tile_fn(fw)
  _write_tile_fn(fw)
  _add_tile_fn(fw)
  _add1_bf16_fn(fw)
  return fw


def build_program(src_addr: int, dst_addr: int, tiles_per_core: int, num_cores: int, num_banks: int) -> Program:
  def rtas_for_core(core_index: int):
    def rtas(_x: int, _y: int) -> list[int]:
      return [src_addr, dst_addr, core_index * tiles_per_core, tiles_per_core, num_banks]
    return rtas

  brisc = add1_kernel(num_banks)
  brisc.rta(lambda _x, _y: [src_addr, dst_addr, 0, tiles_per_core, num_banks])
  prog = Program(
    num_cores=num_cores,
    brisc=brisc,
    ncrisc=Kernel(),
    trisc0=Kernel(),
    trisc1=Kernel(),
    trisc2=Kernel(),
  )
  prog.name = "add1"

  old_layout = prog._layout_core

  def layout_core(*, core_xy=None, dispatch_mode=0, host_assigned_id=0):
    if core_xy is not None:
      cores = getattr(prog, "_add1_target_cores", [core_xy])
      idx = cores.index(core_xy) if core_xy in cores else 0
      brisc.rta(rtas_for_core(idx))
    return old_layout(core_xy=core_xy, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id)

  old_target = prog._target_cores

  def target_cores(cores):
    target = old_target(cores)
    prog._add1_target_cores = target
    return target

  prog._target_cores = target_cores
  prog._layout_core = layout_core
  return prog


def main():
  device = Device()
  try:
    num_cores = int(os.environ.get("CORES", str(len(device.cores))))
    tiles_per_core = int(os.environ.get("TILES", "4"))
    input_pattern = os.environ.get("INPUT_PATTERN", "ordered")
    print_n = int(os.environ.get("PRINT_N", "16"))
    n_tiles = num_cores * tiles_per_core

    src_rm = _seed_src_tensor(n_tiles, input_pattern)
    src_buf = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="src")
    dst_buf = device.dram.alloc(n_tiles, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="dst")
    num_banks = len(device.dram.bank_tiles)

    prog = build_program(src_buf.addr, dst_buf.addr, tiles_per_core, num_cores, num_banks)
    timings = device.run(prog)
    out = device.dram_read(dst_buf)
    exp = _expected_add1(src_rm)
    mismatch = _first_mismatch(out, exp)

    print(f"add1 input pattern: {input_pattern}")
    print(f"output first {print_n}: {_format_bf16_words(out, print_n)}")
    print(f"expect first {print_n}: {_format_bf16_words(exp, print_n)}")
    if mismatch is None:
      print(f"PASS add1 {n_tiles} tiles across {num_cores} cores")
    else:
      print(
        f"mismatch byte={mismatch} "
        f"got={out[mismatch:mismatch + 32].hex()} "
        f"exp={exp[mismatch:mismatch + 32].hex()}"
      )
    for i, timing in enumerate(timings):
      print(f"  [{i}] {timing['name']} {timing['us']:,.1f} us")
  finally:
    device.close()


if __name__ == "__main__":
  main()
