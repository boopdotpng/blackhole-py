
"""Helpers for launching raw-kernel test cases in the emulator."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, Iterable

from emu.scratch import (
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
  RAW_TRISC2_FW_BASE,
  RAW_TRISC_KERNEL_BASES,
  SUBORDINATE_SYNC,
  CB0_BASE_L1,
  CB0_NUM_PAGES,
  CB16_BASE_L1,
  CB16_NUM_PAGES,
  DEFAULT_TENSOR_TILES,
  INPUT_PATTERN,
  TILE_BYTES,
  ScratchDramAllocator,
  ScratchDramBuffer,
  compare_tile_prefixes,
  load_raw_compute_kernels,
  load_raw_dataflow_kernels,
  pack_words,
  patch_raw_compute_ldm,
  raw_kernel_main_base,
  scratch_boot,
  seed_raw_dataflow_ldm,
  setup_add1_runtime,
  split_tile_work,
  tensix_idle,
  verify_runtime_setup,
  verify_tile_runtime,
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
class CbConfig:
  cb: int
  addr: int
  size: int
  pages: int
  page_size: int


@dataclass(frozen=True)
class DmCbInterface:
  role: str
  base: int
  config: CbConfig


@dataclass(frozen=True)
class TriscCbInterface:
  role: str
  config: CbConfig
  tiles_received: int = 0


@dataclass(frozen=True)
class TileLaunch:
  core: tuple[int, int]
  kernel_bases: dict[str, int]
  rtas: dict[int, list[int] | bytes]
  cb_configs: tuple[CbConfig, ...] = ()
  dm_cb_interfaces: tuple[DmCbInterface, ...] = ()
  trisc_cb_interfaces: tuple[TriscCbInterface, ...] = ()
  fw_bases: dict[str, int] | None = None
  boot_before_config: bool = True
  before_boot: Callable | None = None
  after_boot: Callable | None = None


@dataclass(frozen=True)
class KernelLaunchResult:
  steps: int
  done_cycles: dict[tuple[int, int], int]


@dataclass(frozen=True)
class Add1KernelResult:
  output: bytes
  expected: bytes
  steps: int


def write_cb_configs(tile, configs: Iterable[CbConfig], cb_config_base: int):
  for config in configs:
    base = cb_config_base + config.cb * CB_CONFIG_BYTES
    tile.l1.write32(base + 0, config.addr)
    tile.l1.write32(base + 4, config.size)
    tile.l1.write32(base + 8, config.pages)
    tile.l1.write32(base + 12, config.page_size)


def write_tile_rtas(tile, rtas: dict[int, list[int] | bytes]):
  for base, payload in rtas.items():
    data = payload if isinstance(payload, bytes) else pack_words(payload)
    tile.l1.load(base, data)


def run_kernel_launch(
    dev: Device,
    specs: Iterable[TileLaunch],
    *,
    max_steps: int = MAX_RUN_STEPS,
    cb_config_base: int = CB_CONFIG_BASE,
) -> KernelLaunchResult:
  specs = tuple(specs)
  tiles = [dev.tiles[spec.core] for spec in specs]

  for tile, spec in zip(tiles, specs, strict=True):
    if spec.before_boot is not None:
      spec.before_boot(dev, tile, spec)
    if spec.boot_before_config:
      scratch_boot(tile, spec.kernel_bases, fw_bases=spec.fw_bases)
    write_tile_rtas(tile, spec.rtas)
    write_cb_configs(tile, spec.cb_configs, cb_config_base)
    for interface in spec.dm_cb_interfaces:
      core = getattr(tile, interface.role)
      config = interface.config
      write_dm_cb_interface_to_ldm(
        core, interface.base, config.cb, config.addr, config.size,
        config.pages, config.page_size)
    for interface in spec.trisc_cb_interfaces:
      core = getattr(tile, interface.role)
      config = interface.config
      write_trisc_cb_interface(
        core, config.cb, config.addr, config.size, config.pages,
        config.page_size, tiles_received=interface.tiles_received)
    if spec.after_boot is not None:
      spec.after_boot(dev, tile, spec)
    if not spec.boot_before_config:
      scratch_boot(tile, spec.kernel_bases, fw_bases=spec.fw_bases)

  for tile in tiles:
    tile.l1.write8(GO_MESSAGES + 3, RUN_MSG_GO)

  done_cycles: dict[tuple[int, int], int] = {}

  def all_workers_done() -> bool:
    cycle = dev.elapsed_cycles
    for tile in tiles:
      core = (tile.x, tile.y)
      if (core not in done_cycles
          and tile.l1.read8(GO_MESSAGES + 3) == RUN_MSG_DONE
          and tensix_idle(tile)):
        done_cycles[core] = cycle
    return len(done_cycles) == len(tiles)

  steps = dev.run_until(all_workers_done, max_steps, tiles=tiles)

  for tile in tiles:
    sync = tile.l1.read32(SUBORDINATE_SYNC)
    if sync != 0:
      raise AssertionError(
        f"tile ({tile.x},{tile.y}) subordinate sync is 0x{sync:08x}")

  return KernelLaunchResult(steps=steps, done_cycles=done_cycles)


def run_add1_raw_kernel(*, core_count: int) -> Add1KernelResult:
  num_tiles = DEFAULT_TENSOR_TILES
  dev = Device(
    harvested_banks=HARVESTED_DRAM_BANKS,
    core_count=core_count,
    boot_firmware=False,
  )
  tiles = list(dev.tiles.values())
  if num_tiles < len(tiles):
    raise ValueError(
      f"fixed tensor tile count {num_tiles} is smaller than CORES={len(tiles)}")

  kernel_bases = {
    "brisc": raw_kernel_main_base("brisc"),
    "ncrisc": raw_kernel_main_base("ncrisc"),
    **RAW_TRISC_KERNEL_BASES,
  }
  alloc, src, dst, src_data, exp_data = setup_add1_runtime(
    dev, num_tiles, INPUT_PATTERN)
  verify_runtime_setup(alloc, src, src_data)

  cb_configs = (
    CbConfig(0, CB0_BASE_L1, TILE_BYTES * CB0_NUM_PAGES,
             CB0_NUM_PAGES, TILE_BYTES),
    CbConfig(16, CB16_BASE_L1, TILE_BYTES * CB16_NUM_PAGES,
             CB16_NUM_PAGES, TILE_BYTES),
  )

  launches = []
  for tile, (tile_offset, tile_count) in zip(
      tiles, split_tile_work(num_tiles, len(tiles)), strict=True):
    def prepare_add1_tile(dev: Device, tile, spec: TileLaunch,
                          tile_count: int = tile_count):
      load_raw_dataflow_kernels(dev, tile)
      load_raw_compute_kernels(tile, tile_count)

    def verify_add1_tile(dev: Device, tile, spec: TileLaunch,
                         tile_offset: int = tile_offset,
                         tile_count: int = tile_count):
      verify_tile_runtime(tile, src, dst, tile_offset, tile_count)

    launches.append(TileLaunch(
      core=(tile.x, tile.y),
      kernel_bases=kernel_bases,
      rtas={
        KERNEL_CONFIG_BASE + 0x000: [src.addr, tile_offset, tile_count],
        KERNEL_CONFIG_BASE + 0x040: [dst.addr, tile_offset, tile_count],
        TRISC_RTA_BASE: [tile_count],
      },
      cb_configs=cb_configs,
      fw_bases={"trisc2": RAW_TRISC2_FW_BASE},
      before_boot=prepare_add1_tile,
      after_boot=verify_add1_tile,
    ))

  result = run_kernel_launch(dev, launches)
  got = alloc.read(dst)
  mismatch = compare_tile_prefixes(got, exp_data, num_tiles, TILE_BYTES)
  if mismatch is not None:
    idx, got_window, exp_window = mismatch
    raise AssertionError(
      "raw output DRAM mismatch: "
      f"byte={idx} got={got_window.hex()} expected={exp_window.hex()}")

  return Add1KernelResult(output=got, expected=exp_data, steps=result.steps)


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


def cb_configs_from_records(
    records: dict[int, tuple[int, int, int, int]],
) -> tuple[CbConfig, ...]:
  return tuple(
    CbConfig(cb=cb, addr=addr, size=size, pages=pages, page_size=page_size)
    for cb, (addr, size, pages, page_size) in records.items()
  )


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

  records = cb_records(case)
  cb_configs = cb_configs_from_records(records)

  def prepare_raw_tile(dev: Device, tile, spec: TileLaunch):
    load_raw_dataflow_kernels(dev, tile)
    if reader_stem:
      seed_raw_dataflow_ldm(dev, tile)
    patch_raw_compute_ldm(tile, num_tiles)

  dm_interfaces = ()
  if reader_stem:
    dm_interfaces = tuple(
      interface
      for config in cb_configs
      for interface in (
        DmCbInterface("brisc", RAW_DF_BRISC_CB_INTERFACE_LDM, config),
        DmCbInterface("ncrisc", RAW_DF_NCRISC_CB_INTERFACE_LDM, config),
      )
    )

  trisc_interfaces = ()
  if case.binary:
    trisc_interfaces = tuple(
      TriscCbInterface(role, config)
      for role in ("trisc0", "trisc2")
      for config in cb_configs
    )
  elif case.reader_src is not None or case.cb0 != 0 or case.cb_out != 16 or case.cb_pages != 2:
    by_cb = {config.cb: config for config in cb_configs}
    trisc_interfaces = (
      TriscCbInterface("trisc0", by_cb[case.cb0]),
      TriscCbInterface("trisc2", by_cb[case.cb_out]),
    )

  bases = {}

  def load_raw_tile_kernels(dev: Device, tile, spec: TileLaunch):
    spec.kernel_bases.update({
      "brisc": load_kernel_stem(tile, "brisc", reader_stem)
        if reader_stem else raw_kernel_main_base("brisc"),
      "ncrisc": load_kernel_stem(tile, "ncrisc", writer_stem)
        if writer_stem else raw_kernel_main_base("ncrisc"),
    })
    for role in ("trisc0", "trisc1", "trisc2"):
      spec.kernel_bases[role] = load_kernel_stem(
        tile, role, f"{case.name}_{role}.kernel")

  result = run_kernel_launch(
    dev,
    (
      TileLaunch(
        core=(tile.x, tile.y),
        kernel_bases=bases,
        rtas={
          KERNEL_CONFIG_BASE + 0x000:
            [src0.addr, src1.addr, 0, num_tiles] if src1
            else [src0.addr, 0, num_tiles],
          KERNEL_CONFIG_BASE + 0x040: [dst.addr, 0, num_tiles],
          TRISC_RTA_BASE: [num_tiles],
        },
        cb_configs=cb_configs,
        dm_cb_interfaces=dm_interfaces,
        trisc_cb_interfaces=trisc_interfaces,
        boot_before_config=False,
        before_boot=prepare_raw_tile,
        after_boot=load_raw_tile_kernels,
      ),
    ),
  )
  return RawKernelResult(output=alloc.read(dst), steps=result.steps)
