"""Helpers for resolving useful entry symbols from debug ELFs."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Symbol:
  address: int
  kind: str
  name: str


@dataclass(frozen=True)
class SourceLocation:
  function: str
  file: str
  line: int | None


@dataclass(frozen=True)
class AssemblyLine:
  address: int
  text: str


_REPO = Path(__file__).resolve().parent.parent
_TOOLCHAIN = _REPO / "tt-metal-deps" / "sfpi-toolchain" / "bin"
_NM = _TOOLCHAIN / "riscv-tt-elf-nm"
_ADDR2LINE = _TOOLCHAIN / "riscv-tt-elf-addr2line"
_OBJDUMP = _TOOLCHAIN / "riscv-tt-elf-objdump"


def _run_tool(tool: Path, args: list[str], elf_bytes: bytes) -> str:
  if not tool.is_file():
    raise FileNotFoundError(f"missing tool {str(tool)}")
  with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as tmp:
    tmp.write(elf_bytes)
    tmp_path = tmp.name
  try:
    result = subprocess.run([str(tool), *args, tmp_path], capture_output=True, text=True, check=True)
    return result.stdout
  finally:
    os.unlink(tmp_path)


def _run_nm(args: list[str], elf_bytes: bytes) -> str:
  return _run_tool(_NM, args, elf_bytes)


def list_symbols(elf_bytes: bytes, demangle: bool = True) -> list[Symbol]:
  args = ["--numeric-sort", "--defined-only"]
  if demangle:
    args.append("--demangle")
  stdout = _run_nm(args, elf_bytes)
  symbols: list[Symbol] = []
  for line in stdout.splitlines():
    parts = line.strip().split(None, 2)
    if len(parts) != 3:
      continue
    address_s, kind, name = parts
    try:
      address = int(address_s, 16)
    except ValueError:
      continue
    symbols.append(Symbol(address=address, kind=kind, name=name))
  return symbols


def find_symbol(elf_bytes: bytes, predicate, demangle: bool = True) -> Symbol | None:
  for symbol in list_symbols(elf_bytes, demangle=demangle):
    if predicate(symbol):
      return symbol
  return None


def default_entry_symbols(risc: str) -> list[str]:
  if risc == "brisc":
    return ["kernel_main()", "run_kernel()", "_start"]
  if risc == "trisc0":
    return ["chlkc_unpack::unpack_main()", "run_kernel()", "_start"]
  if risc == "trisc1":
    return ["chlkc_math::math_main()", "run_kernel()", "_start"]
  if risc == "trisc2":
    return ["chlkc_pack::pack_main()", "run_kernel()", "_start"]
  if risc == "ncrisc":
    return ["kernel_main()", "_start"]
  raise ValueError(f"unknown risc {risc!r}")


def default_entry_symbol(risc: str) -> str:
  return default_entry_symbols(risc)[0]


def resolve_entry_address(elf_bytes: bytes, risc: str) -> tuple[int, str]:
  symbols = list_symbols(elf_bytes, demangle=True)
  for candidate in default_entry_symbols(risc):
    for symbol in symbols:
      if symbol.name == candidate:
        return symbol.address, symbol.name
  raise LookupError(f"could not resolve a default entry symbol for {risc}")


def resolve_source_location(elf_bytes: bytes, address: int) -> SourceLocation:
  if not _ADDR2LINE.is_file():
    raise FileNotFoundError(f"missing tool {str(_ADDR2LINE)}")
  with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as tmp:
    tmp.write(elf_bytes)
    tmp_path = tmp.name
  try:
    result = subprocess.run(
      [str(_ADDR2LINE), "--demangle", "--functions", "--exe", tmp_path, hex(address)],
      capture_output=True,
      text=True,
      check=True,
    )
    stdout = result.stdout
  finally:
    os.unlink(tmp_path)
  lines = [line.strip() for line in stdout.splitlines() if line.strip()]
  if len(lines) < 2:
    return SourceLocation(function="??", file="??", line=None)
  function = lines[0]
  file_line = lines[1]
  if ":" not in file_line:
    return SourceLocation(function=function, file=file_line, line=None)
  file_name, line_s = file_line.rsplit(":", 1)
  try:
    line = int(line_s)
  except ValueError:
    line = None
  return SourceLocation(function=function, file=file_name, line=line)


def resolve_assembly_line(elf_bytes: bytes, address: int) -> AssemblyLine | None:
  if not _OBJDUMP.is_file():
    raise FileNotFoundError(f"missing tool {str(_OBJDUMP)}")
  with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as tmp:
    tmp.write(elf_bytes)
    tmp_path = tmp.name
  try:
    result = subprocess.run(
      [
        str(_OBJDUMP),
        "-d",
        "--demangle",
        f"--start-address={hex(address)}",
        f"--stop-address={hex(address + 4)}",
        tmp_path,
      ],
      capture_output=True,
      text=True,
      check=True,
    )
    stdout = result.stdout
  finally:
    os.unlink(tmp_path)

  line_re = re.compile(r"^\s*([0-9a-fA-F]+):\s+(.+)$")
  for line in stdout.splitlines():
    match = line_re.match(line)
    if not match:
      continue
    line_addr = int(match.group(1), 16)
    if line_addr == address:
      return AssemblyLine(address=line_addr, text=match.group(2).strip())
  return None
