#!/usr/bin/env python3
"""Render Python-built firmware as simple Markdown disassembly.

Usage:
  python3 -m fw.view brisc | glow -
  python3 -m fw.view all > fw.md
"""
from __future__ import annotations

import argparse
import asm
import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from dsl import zero
from l1 import TensixL1, TensixMMIO


@dataclass(frozen=True)
class Symbol:
  value: int
  name: str


@dataclass(frozen=True)
class Region:
  lo: int
  hi: int
  name: str

  def contains(self, value: int) -> bool:
    return self.lo <= value <= self.hi


def _builders() -> dict[str, Callable[[], Kernel]]:
  fw_init = importlib.import_module("fw")
  trisc = importlib.import_module("fw.trisc")
  cq = importlib.import_module("fw.cq")
  builders = {
    "brisc": fw_init.build_brisc,
    "ncrisc": fw_init.build_ncrisc,
    "trisc0": trisc.build_trisc0,
    "trisc1": trisc.build_trisc1,
    "trisc2": trisc.build_trisc2,
    "cq_prefetch": cq.build_prefetch,
    "cq_dispatch": cq.build_dispatch,
    "cq_dispatch_s_ncrisc": cq.build_dispatch_subordinate,
  }
  builders["all"] = lambda: None  # marker; expanded by main()
  return builders


def _symbol_modules(target: str, kind: str) -> list[ModuleType]:
  modules = {
    "brisc": importlib.import_module("fw.brisc"),
    "ncrisc": importlib.import_module("fw.ncrisc"),
    "trisc": importlib.import_module("fw.trisc"),
    "cq": importlib.import_module("fw.cq"),
  }
  order = []
  if target.startswith("cq_"):
    order.append("cq")
  if kind.startswith("trisc"):
    order.append("trisc")
  else:
    order.append(kind)
  order += ["brisc", "ncrisc", "trisc", "cq"]
  seen = set()
  out = []
  for name in order:
    if name not in seen and name in modules:
      out.append(modules[name])
      seen.add(name)
  return out


def _symbols(target: str, kind: str) -> dict[int, str]:
  names: dict[int, list[str]] = {}
  for module in _symbol_modules(target, kind):
    for name, value in vars(module).items():
      if name.isupper() and isinstance(value, int):
        names.setdefault(value & 0xFFFFFFFF, []).append(name)
  symbols = {value: _pick_symbol(candidates, target, kind) for value, candidates in names.items()}
  symbols.setdefault(TensixMMIO.LOCAL_RAM_START, "LOCAL_RAM_START")
  symbols.setdefault(TensixMMIO.LOCAL_RAM_END, "LOCAL_RAM_END")
  symbols.setdefault(TensixMMIO.LOCAL_RAM_END + 1, "LOCAL_RAM_END+1")
  for cls_name, cls in (("TensixL1", TensixL1), ("TensixMMIO", TensixMMIO)):
    for attr, value in vars(cls).items():
      if attr.isupper() and isinstance(value, int):
        symbols.setdefault(value & 0xFFFFFFFF, f"{cls_name}.{attr}")
  for kind, value in asm.FIRMWARE_TEXT_BASE.items():
    symbols.setdefault(value, f"{kind}.text")
  for kind, value in asm.FIRMWARE_SCRATCH_BASE.items():
    symbols.setdefault(value, f"{kind}.scratch")
  return symbols


def _pick_symbol(names: list[str], target: str, kind: str) -> str:
  # Prefer address-like names when many constants share the same value.
  address_words = ("ADDR", "BASE", "PTR", "REG", "LAUNCH", "CQ", "NOC", "STREAM", "SEM")
  prefixes = [kind.upper()]
  if kind.startswith("trisc"):
    prefixes.insert(0, kind.upper())
    prefixes.append("TRISC")
  if target.startswith("cq_"):
    prefixes.insert(0, "CQ")
  ranked = sorted(
    names,
    key=lambda n: (
      not any(n.startswith(prefix) for prefix in prefixes),
      not any(word in n for word in address_words),
      len(n),
      n,
    ),
  )
  return ranked[0]


def _address_symbols(symbols: dict[int, str]) -> list[Symbol]:
  address_words = (
    "ADDR", "BASE", "PTR", "REG", "LAUNCH", "CQ", "NOC", "STREAM", "SEM",
    "DISPATCH", "PREFETCH", "COMPLETION", "GO", "CB", "L1", "DRAM",
  )
  out = []
  for value, name in symbols.items():
    if _looks_addressish(name, value, address_words):
      out.append(Symbol(value, name))
  return sorted(out, key=lambda s: s.value)


def _looks_addressish(name: str, value: int, address_words: tuple[str, ...]) -> bool:
  if value >= 0xFF000000:
    return True
  if "." in name:
    return True
  non_address_words = ("SIZE", "MASK", "FIELD", "SHIFT", "CMD", "VALUE", "INC", "COUNT", "NUM")
  if any(word in name for word in non_address_words):
    return False
  return any(word in name for word in address_words)


def _regions() -> list[Region]:
  return [
    Region(0x00000000, TensixL1.SIZE - 1, "L1"),
    Region(TensixL1.LAUNCH, TensixL1.LAUNCH + 0x5f, "L1.LAUNCH"),
    Region(TensixL1.GO_MSG, TensixL1.GO_MSG + 0x33, "L1.GO_MESSAGES"),
    Region(TensixL1.KERNEL_CONFIG_BASE, TensixL1.KERNEL_CONFIG_BASE + 0x2fff, "L1.KERNEL_CONFIG"),
    Region(TensixL1.DATA_BUFFER_SPACE_BASE, TensixL1.SIZE - 1, "L1.DATA_BUFFER_SPACE"),
    Region(TensixMMIO.LOCAL_RAM_START, TensixMMIO.LOCAL_RAM_END, "RISC_LOCAL_RAM"),
    Region(TensixMMIO.LOCAL_RAM_END + 1, TensixMMIO.LOCAL_RAM_END + 1, "RISC_LOCAL_RAM_END+1"),
    Region(0xFFB10000, 0xFFB12FFF, "RISCV_DEBUG/RESET"),
    Region(0xFFB20000, 0xFFB2FFFF, "NOC0"),
    Region(0xFFB30000, 0xFFB3FFFF, "NOC1"),
    Region(0xFFB40000, 0xFFB7FFFF, "STREAM_REGS"),
    Region(0xFFEF0000, 0xFFEFFFFF, "TENSIX_CFG"),
    Region(0xFFE40000, 0xFFE7FFFF, "TENSIX_INSTRN_BUF"),
  ]


def _format_symbol(value: int, symbols: dict[int, str], address_symbols: list[Symbol], regions: list[Region]) -> str | None:
  value &= 0xFFFFFFFF
  region = _format_region(value, regions)
  if value in symbols:
    return _join_symbol_region(symbols[value], region)
  best = None
  for sym in address_symbols:
    if sym.value <= value:
      best = sym
    else:
      break
  symbolic = None
  if best is not None:
    offset = value - best.value
    if offset <= 0x200:
      symbolic = f"{best.name}+0x{offset:x}"
  return _join_symbol_region(symbolic, region)


def _format_address(value: int, symbols: dict[int, str], address_symbols: list[Symbol], regions: list[Region]) -> str | None:
  value &= 0xFFFFFFFF
  region = _format_region(value, regions)
  exact = symbols.get(value)
  if exact and (
    region
    or _looks_addressish(
      exact,
      value,
      ("ADDR", "BASE", "PTR", "REG", "LAUNCH", "CQ", "NOC", "STREAM", "SEM", "DISPATCH", "PREFETCH", "COMPLETION", "GO", "CB", "L1", "DRAM"),
    )
  ):
    return _join_symbol_region(exact, region)
  best = None
  for sym in address_symbols:
    if sym.value <= value:
      best = sym
    else:
      break
  symbolic = None
  if best is not None:
    offset = value - best.value
    if offset <= 0x200:
      symbolic = f"{best.name}+0x{offset:x}"
  return _join_symbol_region(symbolic, region)


def _format_region(value: int, regions: list[Region]) -> str | None:
  matches = [region for region in regions if region.contains(value)]
  if not matches:
    return None
  region = min(matches, key=lambda r: r.hi - r.lo)
  offset = value - region.lo
  if offset == 0:
    return region.name
  return f"{region.name}+0x{offset:x}"


def _join_symbol_region(symbol: str | None, region: str | None) -> str | None:
  if symbol and region and symbol != region:
    return f"{symbol} ({region})"
  return symbol or region


def _labels_by_pc(kernel: Kernel) -> dict[int, list[str]]:
  out: dict[int, list[str]] = {}
  for name, pc in kernel.labels.items():
    out.setdefault(pc, []).append(name)
  return out


def _word(kernel: Kernel, item: object) -> int:
  inst = kernel._resolve(item)
  return inst.to_word() if hasattr(inst, "to_word") else int(inst)


def _dec_hex(value: int) -> str:
  return f"{value} (`0x{value:x}`)"


def _segment_flags(seg_label: str) -> str:
  if seg_label.endswith(".text") or seg_label == "text":
    return "RX"
  return "RW"


def _instruction_comments(
  inst: object,
  regs: dict[int, int],
  symbols: dict[int, str],
  address_symbols: list[Symbol],
  regions: list[Region],
) -> list[str]:
  comments = []
  name = getattr(inst, "name", None)
  if name in {"lw", "lbu", "lhu", "sw", "sb", "sh"}:
    base = regs.get(int(inst.rs1))
    if base is not None:
      addr = (base + inst.imm) & 0xFFFFFFFF
      sym = _format_address(addr, symbols, address_symbols, regions)
      if sym:
        comments.append(f"[{sym}]")
    if name in {"sw", "sb", "sh"}:
      value = regs.get(int(inst.rs2))
      if value is not None:
        sym = _format_symbol(value, symbols, address_symbols, regions)
        if sym:
          comments.append(f"value={sym}")
  elif name in {"lui", "addi"}:
    rd = getattr(inst, "rd", None)
    if rd is not None:
      value = _next_reg_value(inst, regs)
      if value is not None:
        sym = _format_address(value, symbols, address_symbols, regions)
        if sym:
          comments.append(f"{rd}={sym}")
  return comments


def _next_reg_value(inst: object, regs: dict[int, int]) -> int | None:
  name = getattr(inst, "name", None)
  if name == "lui":
    return (inst.imm << 12) & 0xFFFFFFFF
  if name == "addi":
    if inst.rs1 == zero:
      return inst.imm & 0xFFFFFFFF
    base = regs.get(int(inst.rs1))
    if base is not None:
      return (base + inst.imm) & 0xFFFFFFFF
  return None


def _update_regs(inst: object, regs: dict[int, int]) -> None:
  rd = getattr(inst, "rd", None)
  if rd is None or rd == zero:
    return
  value = _next_reg_value(inst, regs)
  if value is None:
    regs.pop(int(rd), None)
  else:
    regs[int(rd)] = value


def render_kernel(name: str, kernel: Kernel) -> str:
  labels_by_pc = _labels_by_pc(kernel)
  segments = kernel.compile()
  symbols = _symbols(name, kernel.kind)
  address_symbols = _address_symbols(symbols)
  regions = _regions()
  regs: dict[int, int] = {}
  lines = [
    f"# {name}",
    "",
    "## Summary",
    "",
    "| field | value |",
    "| --- | ---: |",
    f"| kind | `{kernel.kind}` |",
    f"| base | `0x{kernel.base:x}` |",
    f"| instructions | {len(kernel.items)} |",
    f"| text bytes | {_dec_hex(len(kernel.to_bytes()))} |",
    "",
    "## Segments",
    "",
    "| label | address | size | flags |",
    "| --- | ---: | ---: | --- |",
  ]

  for seg in segments:
    label = seg.label or "text"
    lines.append(f"| `{label}` | `0x{seg.addr:x}` | {_dec_hex(len(seg.data))} | `{_segment_flags(label)}` |")
  lines += [
    "",
    "## Disassembly",
    "",
    "```python",
    f"; {name}: blackhole-py firmware",
    "",
  ]

  for idx, item in enumerate(kernel.items):
    pc = kernel.base + 4 * idx
    inst = kernel._resolve(item)
    for label in sorted(labels_by_pc.get(pc, [])):
      lines.append(f"{label}:")
    comments = _instruction_comments(inst, regs, symbols, address_symbols, regions)
    suffix = f"  # {', '.join(comments)}" if comments else ""
    lines.append(f"  {pc:08x}:  {_word(kernel, item):08x}  {kernel._repr_item(item)}{suffix}")
    _update_regs(inst, regs)

  for label in sorted(labels_by_pc.get(kernel.pc, [])):
    lines.append(f"{label}:")

  lines.append("```")
  return "\n".join(lines).rstrip() + "\n"


def build_target(name: str) -> Kernel:
  builders = _builders()
  if name not in builders or name == "all":
    known = ", ".join(sorted(k for k in builders if k != "all"))
    raise SystemExit(f"unknown firmware target {name!r}; choose one of: {known}, all")
  return builders[name]()


def main(argv: list[str] | None = None) -> int:
  builders = _builders()
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("target", nargs="?", default="all", choices=sorted(builders))
  args = parser.parse_args(argv)

  targets = [k for k in builders if k != "all"] if args.target == "all" else [args.target]
  docs = [render_kernel(target, build_target(target)) for target in targets]
  print("\n---\n\n".join(docs), end="")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
