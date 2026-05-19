from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from asm import Kernel

CoreArgs = Callable[[int, int], list[int]]

ROOT = Path(__file__).resolve().parents[1]
DISASMS = ROOT / "firmware" / "disasms"


def kernel_from_ptloads(kind: str, stem: str, rtas: CoreArgs | None = None) -> Kernel:
  """Build an asm.Kernel from checked-in raw PT_LOAD segment bins.

  The old C++ compiler emitted ELF kernels linked at fixed per-processor L1
  addresses.  The new Program API relocates each Kernel as a unit, so we keep
  the original PT_LOAD paddr spacing here and let Program choose the final
  kernel_text_offset.
  """
  manifest_path = DISASMS / f"{stem}.seg.json"
  manifest = json.loads(manifest_path.read_text())
  kernel = Kernel(kind=kind, rtas=rtas)
  for seg in manifest["segments"]:
    data = (DISASMS / seg["bin"]).read_bytes()
    memsz = int(seg["memsz"])
    if len(data) < memsz:
      data = data + b"\0" * (memsz - len(data))
    if not data:
      continue
    kernel.segment(int(seg["paddr"], 16), data, label=f"{stem}.seg{seg['index']}")
  return kernel


def empty_kernel(kind: str) -> Kernel:
  return Kernel(kind=kind)
