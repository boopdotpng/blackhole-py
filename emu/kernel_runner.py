"""Helpers for launching tiny raw-kernel test cases in the emulator.

The firmware image is fixed.  A test case supplies per-core kernel sources,
runtime args, CB layout implied by the input count, and input DRAM buffers.
This module compiles and loads those kernels, boots one Tensix tile, and
returns the output tile bytes for the test to check.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from add1_emu import (
  CB_CONFIG_BASE,
  CB_CONFIG_BYTES,
  DISASMS,
  GO_MESSAGES,
  HARVESTED_DRAM_BANKS,
  KERNEL_CONFIG_BASE,
  LDM_BASE,
  MAX_RUN_STEPS,
  RUN_MSG_DONE,
  RUN_MSG_GO,
  RAW_DF_BRISC_CB_INTERFACE_LDM,
  RAW_DF_NCRISC_CB_INTERFACE_LDM,
  ScratchDramAllocator,
  ScratchDramBuffer,
  load_raw_dataflow_kernels,
  pack_words,
  patch_raw_compute_ldm,
  raw_kernel_main_base,
  scratch_boot,
  seed_raw_dataflow_ldm,
  step_loop,
  tensix_idle,
  write_dm_cb_interface_to_ldm,
  write_trisc_cb_interface,
)
from dispatch import Dtype
from emu.device import Device
from firmware import build_kernels
from firmware.extract_ptload import process as extract_ptload


TRISC_RTA_BASE = KERNEL_CONFIG_BASE + 0x80
TEXT_BASES = {
  "brisc": 0x00009600,
  "ncrisc": 0x0000A600,
  "trisc0": 0x0000B600,
  "trisc1": 0x0000C600,
  "trisc2": 0x0000D600,
}


@dataclass(frozen=True)
class RawKernelCase:
  name: str
  dtype: Dtype
  src0: bytes
  compute_src: str
  src1: bytes | None = None
  reader_src: str | None = None
  writer_src: str | None = None
  cb0: int = 0
  cb1: int = 1
  cb_out: int = 16
  cb_pages: int = 2

  @property
  def binary(self) -> bool:
    return self.src1 is not None

  @property
  def num_tiles(self) -> int:
    if len(self.src0) % self.dtype.tile_size:
      raise ValueError(
        f"{self.name}: src0 length {len(self.src0)} is not tile aligned")
    n = len(self.src0) // self.dtype.tile_size
    if self.src1 is not None and len(self.src1) != len(self.src0):
      raise ValueError(
        f"{self.name}: src1 length {len(self.src1)} does not match src0 length {len(self.src0)}")
    return n


@dataclass(frozen=True)
class RawKernelResult:
  output: bytes
  steps: int


def symbol_addr(stem: str, names: tuple[str, ...]) -> int:
  text = (DISASMS / f"{stem}.dis").read_text()
  for name in names:
    m = re.search(rf"^([0-9a-f]+) <{re.escape(name)}>:", text, re.MULTILINE)
    if m:
      return int(m.group(1), 16)
  raise ValueError(f"{stem}: missing any of {names}")


def ensure_kernel(name: str, target: str, src: str, noc_index: int | None = None) -> str:
  stem = f"{name}_{target}.kernel"
  elf = DISASMS / f"{stem}.elf"
  if not elf.exists():
    build_kernels.build_one(name, target, src, noc_index=noc_index)
  if not (DISASMS / f"{stem}.seg.json").exists():
    extract_ptload(elf)
  return stem


def load_kernel_stem(tile, role: str, stem: str) -> int:
  manifest = json.loads((DISASMS / f"{stem}.seg.json").read_text())
  core = getattr(tile, role)
  rx: tuple[int, int] | None = None
  for seg in manifest["segments"]:
    data = (DISASMS / seg["bin"]).read_bytes()
    memsz = int(seg["memsz"])
    if len(data) < memsz:
      data += b"\0" * (memsz - len(data))
    vaddr = int(seg["vaddr"], 16)
    paddr = int(seg["paddr"], 16)
    if "X" in seg["perms"]:
      rx = (paddr, vaddr)
    if "X" in seg["perms"] and role in TEXT_BASES:
      tile.l1.load(TEXT_BASES[role], data)
    elif LDM_BASE <= vaddr < LDM_BASE + core.LDM_SIZE:
      core.ldm.load(vaddr - LDM_BASE, data)
    else:
      tile.l1.load(paddr, data)
  if rx is None:
    raise ValueError(f"{stem}: missing RX PT_LOAD")
  entry = symbol_addr(stem, ("run_kernel()", "kernel_main()"))
  if role in TEXT_BASES:
    return TEXT_BASES[role] + (entry - rx[1])
  return rx[0] + (entry - rx[1])


def write_rtas(tile, src0: ScratchDramBuffer, src1: ScratchDramBuffer | None,
               dst: ScratchDramBuffer, n: int):
  if src1 is None:
    tile.l1.load(KERNEL_CONFIG_BASE + 0x000, pack_words([src0.addr, 0, n]))
  else:
    tile.l1.load(KERNEL_CONFIG_BASE + 0x000, pack_words([src0.addr, src1.addr, 0, n]))
  tile.l1.load(KERNEL_CONFIG_BASE + 0x040, pack_words([dst.addr, 0, n]))
  tile.l1.load(TRISC_RTA_BASE, pack_words([n]))


def cb_records(case: RawKernelCase) -> dict[int, tuple[int, int, int, int]]:
  if case.cb_pages < 1:
    raise ValueError(f"{case.name}: cb_pages must be >= 1")
  page_size = case.dtype.tile_size
  cb0_size = page_size * case.cb_pages
  cb1_size = page_size * case.cb_pages if case.binary else 0
  cb_out_addr = 0x10000 + cb0_size + cb1_size
  records = {
    case.cb0: (0x10000, cb0_size, case.cb_pages, page_size),
    case.cb_out: (cb_out_addr, page_size * case.cb_pages, case.cb_pages, page_size),
  }
  if case.binary:
    records[case.cb1] = (0x10000 + cb0_size, cb1_size, case.cb_pages, page_size)
  return records


def write_cb_config(tile, case: RawKernelCase):
  for idx, (addr, size, pages, psize) in cb_records(case).items():
    base = CB_CONFIG_BASE + idx * CB_CONFIG_BYTES
    tile.l1.write32(base + 0, addr)
    tile.l1.write32(base + 4, size)
    tile.l1.write32(base + 8, pages)
    tile.l1.write32(base + 12, psize)


def _compile_case(case: RawKernelCase):
  for target in ("trisc0", "trisc1", "trisc2"):
    ensure_kernel(case.name, target, case.compute_src)
  reader_stem = None
  writer_stem = None
  if case.reader_src is not None:
    reader_stem = ensure_kernel(f"{case.name}_reader", "brisc", case.reader_src, noc_index=0)
  if case.writer_src is not None:
    writer_stem = ensure_kernel(f"{case.name}_writer", "ncrisc", case.writer_src, noc_index=1)
  return reader_stem, writer_stem


def run_raw_kernel_case(case: RawKernelCase, *, tiles: int = 1) -> RawKernelResult:
  if tiles != 1:
    raise ValueError("raw kernel cases intentionally run on one tile")

  reader_stem, writer_stem = _compile_case(case)
  dev = Device(harvested_banks=HARVESTED_DRAM_BANKS, core_count=tiles, boot_firmware=False)
  tile = next(iter(dev.tiles.values()))
  alloc = ScratchDramAllocator(dev)
  num_tiles = case.num_tiles
  src0 = alloc.alloc_write(case.src0, name=f"{case.name}_src0")
  src1 = alloc.alloc_write(case.src1, name=f"{case.name}_src1") if case.src1 else None
  dst = alloc.alloc(num_tiles, name=f"{case.name}_dst")

  write_rtas(tile, src0, src1, dst, num_tiles)
  write_cb_config(tile, case)
  load_raw_dataflow_kernels(dev, tile)
  if reader_stem:
    seed_raw_dataflow_ldm(dev, tile)
    for cb, (addr, size, pages, psize) in cb_records(case).items():
      write_dm_cb_interface_to_ldm(
        tile.brisc, RAW_DF_BRISC_CB_INTERFACE_LDM, cb, addr, size, pages, psize)
      write_dm_cb_interface_to_ldm(
        tile.ncrisc, RAW_DF_NCRISC_CB_INTERFACE_LDM, cb, addr, size, pages, psize)
  patch_raw_compute_ldm(tile, num_tiles)
  records = cb_records(case)
  if case.binary:
    for core in (tile.trisc0, tile.trisc2):
      for cb, (addr, size, pages, psize) in records.items():
        write_trisc_cb_interface(core, cb, addr, size, pages, psize)
  elif case.reader_src is not None or case.cb0 != 0 or case.cb_out != 16 or case.cb_pages != 2:
    addr, size, pages, psize = records[case.cb0]
    write_trisc_cb_interface(tile.trisc0, case.cb0, addr, size, pages, psize)
    addr, size, pages, psize = records[case.cb_out]
    write_trisc_cb_interface(tile.trisc2, case.cb_out, addr, size, pages, psize)

  bases = {
    "brisc": load_kernel_stem(tile, "brisc", reader_stem) if reader_stem else raw_kernel_main_base("brisc"),
    "ncrisc": load_kernel_stem(tile, "ncrisc", writer_stem) if writer_stem else raw_kernel_main_base("ncrisc"),
  }
  for role in ("trisc0", "trisc1", "trisc2"):
    bases[role] = load_kernel_stem(tile, role, f"{case.name}_{role}.kernel")

  scratch_boot(tile, bases)
  tile.l1.write8(GO_MESSAGES + 3, RUN_MSG_GO)
  steps = step_loop(
    dev,
    [tile],
    lambda: tile.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE and tensix_idle(tile),
    MAX_RUN_STEPS,
  )
  return RawKernelResult(output=alloc.read(dst), steps=steps)
