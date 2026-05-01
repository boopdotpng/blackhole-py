"""Reusable emulator scenarios for tests."""

from __future__ import annotations

from dataclasses import dataclass

import dsl
from emu.device import Device
from emu.kernel_runner import Add1KernelResult, run_add1_raw_kernel
from emu.matmul_peak_runner import run_matmul_peak
from emu.memory import LAUNCH_MSG_RD_PTR


HARVESTED_DRAM_BANKS = [3]


@dataclass(frozen=True)
class FirmwareBootResult:
  core_count: int
  boot_cycles: int
  dispatch_cycles: int
  core_cycles: dict[str, int]
  tile_state: tuple[tuple[tuple[int, int], int, int], ...]


def run_add1(*, cores: int) -> Add1KernelResult:
  return run_add1_raw_kernel(core_count=cores)


def run_matmul_peak_grid() -> int:
  return run_matmul_peak()


def run_firmware_boot(
    *,
    cores: int = 1,
    boot_max_cycles: int = 200000,
    run_max_cycles: int = 200000,
) -> FirmwareBootResult:
  dev = Device(
    harvested_banks=HARVESTED_DRAM_BANKS,
    core_count=cores,
    firmware_boot_max_cycles=boot_max_cycles,
  )
  ret = dsl.pack([dsl.RET()])
  dispatch_cycles = dev.dispatch(
    brisc=ret,
    ncrisc=ret,
    trisc=(ret, ret, ret),
    max_cycles=run_max_cycles,
  )
  return FirmwareBootResult(
    core_count=cores,
    boot_cycles=dev.firmware_boot_cycles,
    dispatch_cycles=dispatch_cycles,
    core_cycles=dict(dev.core_cycles),
    tile_state=tuple(
      ((tile.x, tile.y),
       tile.l1.read8(dev.go_messages_addr + 3),
       tile.l1.read32(LAUNCH_MSG_RD_PTR))
      for tile in dev.tiles.values()
    ),
  )
