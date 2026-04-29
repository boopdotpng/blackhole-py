#!/usr/bin/env python3
"""Scratch emulator-native dispatch harness for raw matmul_peak kernels.

This loads the checked-in raw PT_LOAD segment bins from firmware/disasms and
launches a 2x2 matmul grid directly in the emulator.  The chosen dimensions
match the fixed matmul_compute.cpp that produced the raw TRISC binaries:

  C[512,512] = A[512,256] @ B[256,512]

Each core computes an 8x8 tile output block.  BRISC runs the reader/mcast
kernel, NCRISC runs the writer/mcast/output kernel, and TRISC0/1/2 run the
raw matmul compute kernels.
"""

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from add1_emu import (
  DISASMS,
  HARVESTED_DRAM_BANKS,
  MAX_RUN_STEPS,
  RAW_DF_BRISC_CB_INTERFACE_LDM,
  RAW_DF_BRISC_DRAM_NOC_XY_LDM,
  RAW_DF_BRISC_DRAM_OFFSET_LDM,
  RAW_DF_NCRISC_CB_INTERFACE_LDM,
  RAW_DF_NCRISC_DRAM_NOC_XY_LDM,
  RAW_DF_NCRISC_DRAM_OFFSET_LDM,
  ScratchDramAllocator,
  ScratchDramBuffer,
  dram_noc_xy,
  pack_words,
  scratch_boot,
  tensix_idle,
  timeout_diagnostics,
  write_dm_cb_interface_to_ldm,
  write_trisc_cb_interface,
)
from dram import tilize, untilize
from dispatch import Dtype, MathFidelity
from emu.device import Device, RUN_MSG_DONE, RUN_MSG_GO
from emu.memory import (
  DATA_BUFFER_SPACE_BASE,
  GO_MESSAGES,
  KERNEL_CONFIG_BASE,
  LDM_BASE,
  LDM_END_8K,
  SUBORDINATE_SYNC,
)
from emu.runtime import RuntimeLayout
from examples.matmul_peak import (
  MatmulPlan,
  _from_device_bytes,
  _host_input_dtype,
  _make_inputs,
  _to_device_bytes,
  _validate,
  build_matmul_program,
)


TILE_BYTES = Dtype.Float16_b.tile_size
M, K, N = 256, 128, 256
TENSIX_X = (1, 2)
TENSIX_Y = (2, 3)
MAX_STEPS = int(os.environ.get("MAX_STEPS", str(MAX_RUN_STEPS * 20)))

BRISC_SEM_L1_BASE_LDM = 0x478
NCRISC_SEM_L1_BASE_LDM = 0x45C

TEXT_BASES = {
  "brisc": 0x00009600,
  "ncrisc": 0x0000A600,
  "trisc0": 0x0000B600,
  "trisc1": 0x0000C600,
  "trisc2": 0x0000D600,
}

MATMUL_PLAN = MatmulPlan(
  rows=(2,),
  cols=(1, 2, 3, 4, 5, 6, 7),
  mt=8,
  kt=4,
  nt=14,
  per_core_m=8,
  per_core_n=2,
  in0_block_w=4,
  out_subblock_h=4,
  out_subblock_w=2,
  out_subblock_num_tiles=8,
  num_blocks=1,
  in0_num_subblocks=2,
  in1_num_subblocks=1,
  in0_block_num_tiles=32,
  in0_subblock_num_tiles=16,
  in1_block_num_tiles=8,
  in1_per_core_w=2,
  out_block_num_tiles=16,
  cb0_pages=64,
  cb1_pages=16,
  cb16_pages=16,
  cb24_pages=16,
)

@dataclass(frozen=True)
class RoleKernels:
  brisc_stem: str
  ncrisc_stem: str


@dataclass(frozen=True)
class ScratchLayout(RuntimeLayout):
  pass


def align16(value: int) -> int:
  return (value + 15) & ~15


def build_scratch_layout(
    args_by_core: dict[tuple[int, int], tuple[list[int], list[int]]],
) -> ScratchLayout:
  reader_bytes = max(len(args[0]) for args in args_by_core.values()) * 4
  writer_bytes = max(len(args[1]) for args in args_by_core.values()) * 4
  rta_total = reader_bytes + writer_bytes
  sem_off = align16(rta_total)
  cb_off = align16(sem_off + 4 * 16)
  return ScratchLayout(
    kernel_config_base=KERNEL_CONFIG_BASE,
    reader_rta_base=KERNEL_CONFIG_BASE,
    writer_rta_base=KERNEL_CONFIG_BASE + reader_bytes,
    compute_rta_base=KERNEL_CONFIG_BASE + rta_total,
    semaphore_base=KERNEL_CONFIG_BASE + sem_off,
    cb_config_base=KERNEL_CONFIG_BASE + cb_off,
  )


def bf16_words(data: bytes, count: int = 16) -> str:
  return " ".join(
    f"{int.from_bytes(data[i:i + 2], 'little'):04x}"
    for i in range(0, min(len(data), count * 2), 2)
  )


def bf16_values(data: bytes, shape: tuple[int, int], count: int = 16) -> list[float]:
  return _from_device_bytes(data, shape).astype(np.float32).reshape(-1)[:count].tolist()


def raw_symbol_addr(stem: str,
                    symbols: tuple[str, ...] = ("_Z11kernel_mainv",
                                                "kernel_main()")) -> int:
  text = (DISASMS / f"{stem}.dis").read_text()
  for symbol in symbols:
    m = re.search(rf"^([0-9a-f]+) <{re.escape(symbol)}>:", text, re.MULTILINE)
    if m:
      return int(m.group(1), 16)
  raise ValueError(f"{stem}: missing symbols {', '.join(symbols)}")


def load_rx_segment_relocated(tile, role: str, stem: str) -> tuple[int, int]:
  manifest = json.loads((DISASMS / f"{stem}.seg.json").read_text())
  rx = [seg for seg in manifest["segments"] if "X" in seg["perms"]]
  if len(rx) != 1:
    raise AssertionError(f"{stem}: expected one RX segment, got {rx}")
  seg = rx[0]
  data = (DISASMS / seg["bin"]).read_bytes()
  memsz = int(seg["memsz"])
  if len(data) < memsz:
    data += b"\0" * (memsz - len(data))
  base = TEXT_BASES[role]
  tile.l1.load(base, data)
  return base, int(seg["vaddr"], 16)


def load_rw_segments_to_ldm(tile, role: str, stem: str):
  manifest = json.loads((DISASMS / f"{stem}.seg.json").read_text())
  core = getattr(tile, role)
  for seg in manifest["segments"]:
    if "X" in seg["perms"]:
      continue
    data = (DISASMS / seg["bin"]).read_bytes()
    memsz = int(seg["memsz"])
    if len(data) < memsz:
      data += b"\0" * (memsz - len(data))
    vaddr = int(seg["vaddr"], 16)
    if LDM_BASE <= vaddr <= LDM_END_8K and memsz:
      core.ldm.load(vaddr - LDM_BASE, data)


def load_dataflow_kernel(tile, role: str, stem: str) -> int:
  text_base, text_vaddr = load_rx_segment_relocated(tile, role, stem)
  load_rw_segments_to_ldm(tile, role, stem)
  return text_base + (raw_symbol_addr(stem) - text_vaddr)


def load_compute_kernel(tile, role: str, stem: str) -> int:
  text_base, text_vaddr = load_rx_segment_relocated(tile, role, stem)
  load_rw_segments_to_ldm(tile, role, stem)
  return text_base + (raw_symbol_addr(stem, ("run_kernel()",)) - text_vaddr)


def cb_layout(plan: MatmulPlan) -> dict[int, tuple[int, int, int]]:
  addr = DATA_BUFFER_SPACE_BASE
  out = {}
  for idx, pages in (
      (0, plan.cb0_pages),
      (1, plan.cb1_pages),
      (16, plan.cb16_pages),
      (24, plan.cb24_pages),
  ):
    if idx == 24:
      out[idx] = out[16]
      continue
    size = pages * TILE_BYTES
    out[idx] = (addr, size, pages)
    addr += size
  return out


def write_cb_config(tile, layout: ScratchLayout,
                    cb_map: dict[int, tuple[int, int, int]]):
  for idx, (addr, size, pages) in cb_map.items():
    base = layout.cb_config_addr(idx)
    tile.l1.write32(base + 0, addr)
    tile.l1.write32(base + 4, size)
    tile.l1.write32(base + 8, pages)
    tile.l1.write32(base + 12, TILE_BYTES)


def seed_dataflow_ldm(dev: Device, tile,
                      cb_layout: dict[int, tuple[int, int, int]],
                      layout: ScratchLayout):
  tile.brisc.ldm.write32(0x10, layout.reader_rta_base)
  tile.brisc.ldm.write32(BRISC_SEM_L1_BASE_LDM, layout.semaphore_base)
  tile.ncrisc.ldm.write32(0x34, layout.writer_rta_base)
  tile.ncrisc.ldm.write32(NCRISC_SEM_L1_BASE_LDM, layout.semaphore_base)

  for cb in (0, 1, 16, 24):
    addr, size, pages = cb_layout[cb]
    write_dm_cb_interface_to_ldm(
      tile.brisc, RAW_DF_BRISC_CB_INTERFACE_LDM, cb, addr, size, pages,
      TILE_BYTES)
    write_dm_cb_interface_to_ldm(
      tile.ncrisc, RAW_DF_NCRISC_CB_INTERFACE_LDM, cb, addr, size, pages,
      TILE_BYTES)

  num_banks = dev.dram.num_banks
  for bank_idx in range(num_banks):
    tile.brisc.ldm.write16(RAW_DF_BRISC_DRAM_NOC_XY_LDM + bank_idx * 2,
                           dram_noc_xy(dev, bank_idx, noc_id=0))
    tile.brisc.ldm.write32(RAW_DF_BRISC_DRAM_OFFSET_LDM + bank_idx * 4, 0)
    tile.ncrisc.ldm.write16(
      RAW_DF_NCRISC_DRAM_NOC_XY_LDM + (num_banks + bank_idx) * 2,
      dram_noc_xy(dev, bank_idx, noc_id=1))
    tile.ncrisc.ldm.write32(RAW_DF_NCRISC_DRAM_OFFSET_LDM + bank_idx * 4, 0)


def patch_compute_ldm(tile, cb_layout: dict[int, tuple[int, int, int]],
                      layout: ScratchLayout):
  for core in (tile.trisc0, tile.trisc2):
    core.ldm.write32(0x08, layout.cb_config_base)
    core.ldm.write32(0x10, KERNEL_CONFIG_BASE)
    core.ldm.write32(0x14, layout.trisc_rta_base)
    core.ldm.write32(0x1C, 0)
  tile.trisc1.ldm.write32(0x0C, KERNEL_CONFIG_BASE)
  tile.trisc1.ldm.write32(0x10, layout.trisc_rta_base)
  tile.trisc1.ldm.write32(0x18, 0)

  for core in (tile.trisc0, tile.trisc2):
    for cb in (0, 1, 16, 24):
      addr, size, pages = cb_layout[cb]
      write_trisc_cb_interface(core, cb, addr, size, pages, TILE_BYTES)


def write_rtas(tile, reader_args: list[int], writer_args: list[int],
               layout: ScratchLayout):
  tile.l1.load(layout.reader_rta_base, pack_words(reader_args))
  tile.l1.load(layout.writer_rta_base, pack_words(writer_args))
  tile.l1.load(layout.trisc_rta_base, b"\0" * 16)
  tile.l1.load(layout.semaphore_base, b"\0" * (4 * 16))


def make_buffers(dev: Device, plan: MatmulPlan):
  alloc = ScratchDramAllocator(dev)
  a_src, b_src = _make_inputs(M, K, N)
  Mp, Kp, Np = plan.mt * 32, plan.kt * 32, plan.nt * 32
  if (M, K) != (Mp, Kp):
    a_padded = np.zeros((Mp, Kp), dtype=_host_input_dtype())
    a_padded[:M, :K] = a_src
  else:
    a_padded = a_src
  if (K, N) != (Kp, Np):
    b_padded = np.zeros((Kp, Np), dtype=_host_input_dtype())
    b_padded[:K, :N] = b_src
  else:
    b_padded = b_src
  a_bytes = _to_device_bytes(a_padded)
  b_bytes = _to_device_bytes(b_padded)
  a_tiled = tilize(a_bytes, Dtype.Float16_b.bpe, (Mp, Kp))
  b_tiled = tilize(b_bytes, Dtype.Float16_b.bpe, (Kp, Np))
  a_buf = alloc.alloc_write(a_tiled, name="A")
  b_buf = alloc.alloc_write(b_tiled, name="B")
  c_buf = alloc.alloc(plan.mt * plan.nt, name="C")
  return alloc, a_buf, b_buf, c_buf, a_src, b_src


def program_args(plan: MatmulPlan, a: ScratchDramBuffer,
                 b: ScratchDramBuffer, c: ScratchDramBuffer):
  # Build only to reuse matmul_peak's exact RTA lambdas.  The raw checked-in
  # kernels are loaded from PT_LOAD bins below.
  prog = build_matmul_program(
    plan, a, b, c, io_dtype=Dtype.Float16_b,
    math_fidelity=MathFidelity.HiFi2, f32_acc=False)
  cores = plan.active_cores()
  n = len(cores)
  return {
    core: (
      prog.reader_args(i, core, n),  # physical BRISC reader/mcast args
      prog.writer_args(i, core, n),  # physical NCRISC writer/mcast args
    )
    for i, core in enumerate(cores)
  }


def role_kernels(core: tuple[int, int], plan: MatmulPlan) -> RoleKernels:
  rows, cols = plan.rows, plan.cols
  x, y = core
  if y == rows[0] and x == cols[0]:
    return RoleKernels("matmul_reader_sender_brisc.kernel",
                       "matmul_writer_sender_ncrisc.kernel")
  if y == rows[0]:
    return RoleKernels("matmul_reader_recv_brisc.kernel",
                       "matmul_writer_sender_ncrisc.kernel")
  if x == cols[0]:
    return RoleKernels("matmul_reader_sender_brisc.kernel",
                       "matmul_writer_recv_ncrisc.kernel")
  return RoleKernels("matmul_reader_recv_brisc.kernel",
                     "matmul_writer_recv_ncrisc.kernel")


def validate_output(alloc: ScratchDramAllocator, c_buf: ScratchDramBuffer,
                    a_src: np.ndarray, b_src: np.ndarray, plan: MatmulPlan):
  Mp, Np = plan.mt * 32, plan.nt * 32
  c_tiled = alloc.read(c_buf)
  c_raw = untilize(c_tiled, Dtype.Float16_b.bpe, (Mp, Np))
  _validate(
    _from_device_bytes(_to_device_bytes(a_src), (M, K)),
    _from_device_bytes(_to_device_bytes(b_src), (K, N)),
    c_raw, M, N, Mp, Np)
  return c_raw


def main():
  dev = Device(harvested_banks=HARVESTED_DRAM_BANKS,
               cores=MATMUL_PLAN.active_cores(),
               boot_firmware=False)
  plan = MATMUL_PLAN
  cb_map = cb_layout(plan)
  tiles = [dev.tiles[core] for core in plan.active_cores()]

  alloc, a_buf, b_buf, c_buf, a_src, b_src = make_buffers(dev, plan)
  args_by_core = program_args(plan, a_buf, b_buf, c_buf)
  scratch_layout = build_scratch_layout(args_by_core)
  dev.set_runtime_layout(scratch_layout)

  for tile in tiles:
    core_xy = (tile.x, tile.y)
    kernels = role_kernels(core_xy, plan)
    brisc_main = load_dataflow_kernel(tile, "brisc", kernels.brisc_stem)
    ncrisc_main = load_dataflow_kernel(tile, "ncrisc", kernels.ncrisc_stem)
    trisc0_main = load_compute_kernel(
      tile, "trisc0", "matmul_compute_trisc0.kernel")
    trisc1_main = load_compute_kernel(
      tile, "trisc1", "matmul_compute_trisc1.kernel")
    trisc2_main = load_compute_kernel(
      tile, "trisc2", "matmul_compute_trisc2.kernel")
    scratch_boot(
      tile,
      kernel_bases={
        "brisc": brisc_main,
        "ncrisc": ncrisc_main,
        "trisc0": trisc0_main,
        "trisc1": trisc1_main,
        "trisc2": trisc2_main,
      },
    )
    reader_args, writer_args = args_by_core[core_xy]
    write_rtas(tile, reader_args, writer_args, scratch_layout)
    write_cb_config(tile, scratch_layout, cb_map)
    seed_dataflow_ldm(dev, tile, cb_map, scratch_layout)
    patch_compute_ldm(tile, cb_map, scratch_layout)

  for tile in tiles:
    tile.l1.write8(GO_MESSAGES + 3, RUN_MSG_GO)

  try:
    steps = dev.run_until(
      lambda: all(
        tile.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE and tensix_idle(tile)
        for tile in tiles),
      MAX_STEPS,
      tiles=tiles)
  except TimeoutError as e:
    print(f"RUN TIMEOUT: {e}\n{timeout_diagnostics(tiles)}",
          file=sys.stderr, flush=True)
    return 1
  except Exception as e:
    print(f"RUN ERROR: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    return 1

  for tile in tiles:
    sync = tile.l1.read32(SUBORDINATE_SYNC)
    if sync != 0:
      print(
        f"FAIL: tile ({tile.x},{tile.y}) subordinate sync is 0x{sync:08x}",
        file=sys.stderr)
      return 1

  try:
    c_raw = validate_output(alloc, c_buf, a_src, b_src, plan)
  except SystemExit as e:
    print(f"VALIDATION ERROR: {e}", file=sys.stderr)
    got = alloc.read(c_buf)
    print(f"  output bf16 first 16: {bf16_words(got)}", file=sys.stderr)
    return 1

  gflops = 2 * M * K * N / max(steps, 1)
  print(
    f"matmul_peak raw-kernel emulation: pass\n"
    f"  shape: C[{M},{N}] = A[{M},{K}] @ B[{K},{N}]\n"
    f"  grid: {len(plan.rows)}x{len(plan.cols)} cores {plan.active_cores()}\n"
    f"  kernels: raw PT_LOAD bins from firmware/disasms\n"
    f"  steps: {steps} emulated device ticks, nominal {gflops:.2f} flop/tick\n"
    f"  output bf16 first 16: {bf16_words(tilize(c_raw, 2, (plan.mt * 32, plan.nt * 32)))}\n"
    f"  output values first 16: {bf16_values(c_raw, (plan.mt * 32, plan.nt * 32))}",
    flush=True)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
