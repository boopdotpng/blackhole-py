from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from asm import Kernel
from ttk.addrs import TensixMMIO


OLD_BLACKHOLE_PY = Path(__file__).resolve().parents[1] / "blackhole-py-old"
DISASMS = Path(__file__).resolve().parent / "firmware" / "disasms"
TARGETS = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
FIRMWARE_SCRATCH_BASE = {
  "brisc": 0x82B0,
  "ncrisc": 0xA2B0,
  "trisc0": 0xC2B0,
  "trisc1": 0xD2B0,
  "trisc2": 0xE2B0,
}

def _parse_int(value):
  if isinstance(value, int):
    return value
  return int(value, 0)

def build_all(disasms: Path = DISASMS) -> dict[str, Kernel]:
  """Load checked-in C++ resident firmware PT_LOADs as asm.Kernel objects."""
  result: dict[str, Kernel] = {}
  for target in TARGETS:
    manifest = json.loads((disasms / f"{target}.seg.json").read_text())
    kernel = Kernel()
    for seg in manifest["segments"]:
      data = (disasms / seg["bin"]).read_bytes()
      memsz = _parse_int(seg.get("memsz", len(data)))
      if len(data) < memsz:
        data = data + b"\0" * (memsz - len(data))
      if not data:
        continue
      addr = _parse_int(seg["paddr"])
      if TensixMMIO.LOCAL_RAM_START <= addr <= TensixMMIO.LOCAL_RAM_END:
        addr = FIRMWARE_SCRATCH_BASE[target] + (addr - TensixMMIO.LOCAL_RAM_START)
      kernel.segment(addr, data, label=f"{target}.seg{seg['index']}")
    result[target] = kernel
  return result

def _with_old_path():
  old = Path(__file__).resolve().parent.parent / "blackhole-py-old"
  if not old.is_dir():
    raise FileNotFoundError(f"missing old compiler path: {old}")
  sys.path.insert(0, str(old))
  return old

def _fw_to_kernel(target: str, compiled: Any) -> Kernel:
  kernel = Kernel()
  for seg in compiled.segments:
    data = seg.data
    if len(data) < seg.memsz:
      data = data + b"\0" * (seg.memsz - len(data))
    if not data:
      continue
    addr = seg.paddr
    if TensixMMIO.LOCAL_RAM_START <= addr <= TensixMMIO.LOCAL_RAM_END:
      addr = FIRMWARE_SCRATCH_BASE[target] + (addr - TensixMMIO.LOCAL_RAM_START)
    kernel.segment(addr, data, label=f"{target}.compiled")
  return kernel

def build_from_old_compiler(
  num_dram_banks: int,
  num_l1_banks: int,
  prefetch_core: tuple[int, int],
  dispatch_core: tuple[int, int],
) -> dict[str, Kernel]:
  """Compile the known-good C++ resident firmware from blackhole-py-old."""
  _with_old_path()
  from compiler import compile_firmware

  compiled = compile_firmware(num_dram_banks, num_l1_banks, prefetch_core, dispatch_core)
  return {target: _fw_to_kernel(target, compiled[target]) for target in TARGETS}

def build_ret_compute_kernels(
  num_dram_banks: int,
  num_l1_banks: int,
  prefetch_core: tuple[int, int],
  dispatch_core: tuple[int, int],
) -> tuple[Kernel, Kernel, Kernel]:
  """Compile C++ compute wrappers whose MAIN returns immediately."""
  _with_old_path()
  from compiler import Compiler
  from dispatch import Program as OldProgram

  compiler = Compiler(num_dram_banks, num_l1_banks, prefetch_core, dispatch_core)
  old_program = OldProgram(cores=1, reader_kernel="", compute_kernel="", writer_kernel="", cbs=[])
  source = '#include "compute_kernel_api/common.h"\nnamespace NAMESPACE { void MAIN { return; } }\n'
  compiled = compiler.compile_compute(source, old_program)
  kernels = []
  for i, kernel in enumerate(compiled):
    kernels.append(Kernel().segment(0, kernel.xip, label=f"ret_trisc{i}"))
  return tuple(kernels)
