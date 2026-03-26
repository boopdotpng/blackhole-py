"""ELF symbol resolution helpers for the profiler (extracted from deleted debug/symbols.py)."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_TOOLCHAIN = _REPO / "tt-metal-deps" / "sfpi-toolchain" / "bin"
_NM = _TOOLCHAIN / "riscv-tt-elf-nm"
_ADDR2LINE = _TOOLCHAIN / "riscv-tt-elf-addr2line"
_OBJDUMP = _TOOLCHAIN / "riscv-tt-elf-objdump"


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


def _run_tool(tool: Path, args: list[str], elf_bytes: bytes) -> str:
  if not tool.is_file():
    raise FileNotFoundError(f"missing tool {str(tool)}")
  with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as tmp:
    tmp.write(elf_bytes)
    tmp_path = tmp.name
  try:
    return subprocess.run([str(tool), *args, tmp_path], capture_output=True, text=True, check=True).stdout
  finally:
    os.unlink(tmp_path)


def list_symbols(elf_bytes: bytes, demangle: bool = True) -> list[Symbol]:
  args = ["--numeric-sort", "--defined-only"]
  if demangle:
    args.append("--demangle")
  stdout = _run_tool(_NM, args, elf_bytes)
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


def resolve_source_location(elf_bytes: bytes, address: int) -> SourceLocation:
  with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as tmp:
    tmp.write(elf_bytes)
    tmp_path = tmp.name
  try:
    result = subprocess.run(
      [str(_ADDR2LINE), "--demangle", "--functions", "--exe", tmp_path, hex(address)],
      capture_output=True, text=True, check=True,
    )
  finally:
    os.unlink(tmp_path)
  lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
  if len(lines) < 2:
    return SourceLocation(function="??", file="??", line=None)
  function = lines[0]
  file_line = lines[1]
  if ":" not in file_line:
    return SourceLocation(function=function, file=file_line, line=None)
  file_name, line_s = file_line.rsplit(":", 1)
  try:
    line_num = int(line_s)
  except ValueError:
    line_num = None
  return SourceLocation(function=function, file=file_name, line=line_num)


def resolve_assembly_line(elf_bytes: bytes, address: int) -> AssemblyLine | None:
  with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as tmp:
    tmp.write(elf_bytes)
    tmp_path = tmp.name
  try:
    result = subprocess.run(
      [str(_OBJDUMP), "-d", "--demangle", f"--start-address={hex(address)}", f"--stop-address={hex(address + 4)}", tmp_path],
      capture_output=True, text=True, check=True,
    )
  finally:
    os.unlink(tmp_path)
  line_re = re.compile(r"^\s*([0-9a-fA-F]+):\s+(.+)$")
  for line in result.stdout.splitlines():
    match = line_re.match(line)
    if match and int(match.group(1), 16) == address:
      return AssemblyLine(address=address, text=match.group(2).strip())
  return None
