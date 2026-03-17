# debug/source.py - ELF source mapping via addr2line / objdump / c++filt
#
# Maps PC addresses to source file:line and provides disassembly.
# Uses the SFPI toolchain binaries in tt-metal-deps/sfpi-toolchain/bin/.

from __future__ import annotations
import subprocess, os, tempfile, re
from pathlib import Path
from functools import lru_cache

_REPO = Path(__file__).resolve().parent.parent
_TOOLCHAIN = _REPO / "tt-metal-deps" / "sfpi-toolchain" / "bin"
_ADDR2LINE = _TOOLCHAIN / "riscv-tt-elf-addr2line"
_OBJDUMP   = _TOOLCHAIN / "riscv-tt-elf-objdump"
_CXXFILT   = _TOOLCHAIN / "riscv-tt-elf-c++filt"
_READELF   = _TOOLCHAIN / "riscv-tt-elf-readelf"


class ElfInfo:
  """Parsed debug info for a single ELF binary.

  Caches addr2line results and disassembly. Constructed from raw ELF bytes
  (written to a temp file for toolchain access).
  """

  def __init__(self, elf_bytes: bytes, name: str = "kernel"):
    self.name = name
    self._tmpdir = tempfile.mkdtemp(prefix=f"tt-dbg-{name}-")
    self._elf_path = Path(self._tmpdir) / f"{name}.elf"
    self._elf_path.write_bytes(elf_bytes)
    self._disasm_cache: dict[int, tuple[str, str]] | None = None  # addr -> (hex, asm)
    self._source_cache: dict[int, tuple[str, int, str]] = {}  # addr -> (file, line, func)
    self._source_lines_cache: dict[str, list[str]] = {}  # filepath -> lines
    self._addr2line_ok = _ADDR2LINE.is_file()
    self._objdump_ok = _OBJDUMP.is_file()
    # runtime offset: runtime_PC = elf_PC + _addr_offset
    # set by hook.py once we know where the kernel text is loaded in L1
    self._addr_offset: int = 0

  def set_runtime_offset(self, runtime_text_base: int, elf_text_base: int):
    """Set the offset between runtime L1 addresses and ELF link addresses.

    After this, addr2line/disasm_at will automatically translate runtime
    PCs to ELF PCs before lookup.
    """
    self._addr_offset = runtime_text_base - elf_text_base

  def to_elf_pc(self, runtime_pc: int) -> int:
    """Convert a runtime PC to the corresponding ELF address."""
    return runtime_pc - self._addr_offset

  def to_runtime_pc(self, elf_pc: int) -> int:
    """Convert an ELF address to the corresponding runtime PC."""
    return elf_pc + self._addr_offset

  def close(self):
    import shutil
    shutil.rmtree(self._tmpdir, ignore_errors=True)

  def __del__(self):
    self.close()

  # -- addr2line: PC -> (file, line, function) ----------------------------- #

  def addr2line(self, pc: int) -> tuple[str, int, str]:
    """Resolve a runtime PC to (source_file, line_number, function_name).

    Automatically translates runtime PC to ELF PC before lookup.
    Returns ("??", 0, "??") if debug info is unavailable.
    """
    if pc in self._source_cache:
      return self._source_cache[pc]
    elf_pc = self.to_elf_pc(pc)
    result = self._raw_addr2line(elf_pc)
    self._source_cache[pc] = result
    return result

  def _raw_addr2line(self, pc: int) -> tuple[str, int, str]:
    if not self._addr2line_ok:
      return ("??", 0, "??")
    try:
      out = subprocess.run(
        [str(_ADDR2LINE), "-e", str(self._elf_path), "-f", "-C", f"0x{pc:x}"],
        capture_output=True, text=True, timeout=5,
      )
      lines = out.stdout.strip().split("\n")
      if len(lines) >= 2:
        func = lines[0].strip()
        loc = lines[1].strip()
        if ":" in loc:
          filepath, linestr = loc.rsplit(":", 1)
          lineno = int(linestr) if linestr.isdigit() else 0
          return (filepath, lineno, func)
      return ("??", 0, "??")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
      return ("??", 0, "??")

  def batch_addr2line(self, pcs: list[int]) -> dict[int, tuple[str, int, str]]:
    """Resolve multiple runtime PCs in one subprocess call (much faster)."""
    if not self._addr2line_ok or not pcs:
      return {pc: ("??", 0, "??") for pc in pcs}
    uncached = [pc for pc in pcs if pc not in self._source_cache]
    if uncached:
      addrs = "\n".join(f"0x{self.to_elf_pc(pc):x}" for pc in uncached)
      try:
        out = subprocess.run(
          [str(_ADDR2LINE), "-e", str(self._elf_path), "-f", "-C"],
          input=addrs, capture_output=True, text=True, timeout=10,
        )
        lines = out.stdout.strip().split("\n")
        # output is pairs: function\nlocation
        for i in range(0, len(lines) - 1, 2):
          if i // 2 >= len(uncached):
            break
          pc = uncached[i // 2]
          func = lines[i].strip()
          loc = lines[i + 1].strip()
          if ":" in loc:
            filepath, linestr = loc.rsplit(":", 1)
            lineno = int(linestr) if linestr.isdigit() else 0
            self._source_cache[pc] = (filepath, lineno, func)
          else:
            self._source_cache[pc] = ("??", 0, func)
      except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        for pc in uncached:
          self._source_cache[pc] = ("??", 0, "??")
    return {pc: self._source_cache.get(pc, ("??", 0, "??")) for pc in pcs}

  # -- source file reading ------------------------------------------------- #

  def get_source_context(self, filepath: str, lineno: int, context: int = 5) -> list[tuple[int, str, bool]]:
    """Read source lines around a location.

    Returns [(line_number, line_text, is_current_line), ...].
    """
    if filepath == "??" or lineno == 0:
      return []
    lines = self._read_source_file(filepath)
    if not lines:
      return []
    start = max(0, lineno - context - 1)
    end = min(len(lines), lineno + context)
    return [(i + 1, lines[i], i + 1 == lineno) for i in range(start, end)]

  def _read_source_file(self, filepath: str) -> list[str]:
    if filepath in self._source_lines_cache:
      return self._source_lines_cache[filepath]
    try:
      text = Path(filepath).read_text()
      lines = text.splitlines()
      self._source_lines_cache[filepath] = lines
      return lines
    except (FileNotFoundError, OSError, PermissionError):
      self._source_lines_cache[filepath] = []
      return []

  # -- disassembly --------------------------------------------------------- #

  def disassemble(self) -> dict[int, tuple[str, str]]:
    """Full disassembly: {address: (hex_bytes, asm_text)}.

    Cached after first call.
    """
    if self._disasm_cache is not None:
      return self._disasm_cache
    self._disasm_cache = {}
    if not self._objdump_ok:
      return self._disasm_cache
    try:
      out = subprocess.run(
        [str(_OBJDUMP), "-d", "--no-show-raw-insn", str(self._elf_path)],
        capture_output=True, text=True, timeout=30,
      )
      # parse lines like: "    3840:	jal	ra,38c4 <main>"
      pattern = re.compile(r'^\s*([0-9a-f]+):\s+(.+)$')
      for line in out.stdout.splitlines():
        m = pattern.match(line)
        if m:
          addr = int(m.group(1), 16)
          asm = m.group(2).strip()
          self._disasm_cache[addr] = ("", asm)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
      pass
    return self._disasm_cache

  def disasm_at(self, pc: int, context: int = 5) -> list[tuple[int, str, bool]]:
    """Disassembly lines around a runtime PC.

    Returns [(runtime_address, asm_text, is_current), ...].
    Internally translates to ELF addresses for lookup, then back
    to runtime addresses for display.
    """
    disasm = self.disassemble()
    addrs = sorted(disasm.keys())
    if not addrs:
      return [(pc, "<no disassembly available>", True)]
    elf_pc = self.to_elf_pc(pc)
    # find closest ELF address <= elf_pc
    idx = _bisect_right(addrs, elf_pc) - 1
    if idx < 0:
      idx = 0
    start = max(0, idx - context)
    end = min(len(addrs), idx + context + 1)
    off = self._addr_offset
    return [(addrs[i] + off, disasm[addrs[i]][1], addrs[i] == elf_pc) for i in range(start, end)]

  # -- combined source + disasm view --------------------------------------- #

  def format_location(self, pc: int, context: int = 5) -> str:
    """Format source + disassembly around a PC for display."""
    filepath, lineno, func = self.addr2line(pc)

    lines = []
    lines.append(f"  {func}() at {filepath}:{lineno}")
    lines.append("")

    # source context
    src = self.get_source_context(filepath, lineno, context)
    if src:
      lines.append("  Source:")
      for ln, text, current in src:
        marker = ">" if current else " "
        lines.append(f"  {marker} {ln:4d} | {text}")
      lines.append("")

    # disassembly context
    disasm = self.disasm_at(pc, context)
    if disasm:
      lines.append("  Disassembly:")
      for addr, asm, current in disasm:
        marker = ">" if current else " "
        lines.append(f"  {marker} 0x{addr:06x}: {asm}")

    return "\n".join(lines)


  # -- symbol lookup ------------------------------------------------------- #

  def find_symbol(self, name: str) -> int | None:
    """Find a symbol's address by name (exact match, demangled).

    Uses readelf -s + c++filt. Returns the address or None.
    """
    if not _READELF.is_file():
      return None
    try:
      out = subprocess.run(
        [str(_READELF), "-s", "-W", str(self._elf_path)],
        capture_output=True, text=True, timeout=10,
      )
      # lines like:   42: 00008abc    24 FUNC    GLOBAL DEFAULT    1 _Z11kernel_mainv
      for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 8 and parts[3] == "FUNC":
          sym_addr = int(parts[1], 16)
          sym_name = parts[7]
          # try demangling
          demangled = self._demangle(sym_name)
          if name in demangled or name == sym_name:
            return sym_addr
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
      pass
    return None

  def find_symbols(self, pattern: str = "") -> dict[str, int]:
    """Find all FUNC symbols, optionally filtered by substring. Returns {name: addr}."""
    if not _READELF.is_file():
      return {}
    try:
      out = subprocess.run(
        [str(_READELF), "-s", "-W", str(self._elf_path)],
        capture_output=True, text=True, timeout=10,
      )
      syms: dict[str, int] = {}
      for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 8 and parts[3] == "FUNC":
          addr = int(parts[1], 16)
          if addr == 0:
            continue
          name = self._demangle(parts[7])
          if not pattern or pattern in name:
            syms[name] = addr
      return syms
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
      return {}

  def entry_pc(self) -> int | None:
    """Find the user kernel entry point.

    Searches for kernel_main (dataflow) or math_main/run_kernel (compute).
    Returns the address, or None if not found.
    """
    for name in ("kernel_main", "math_main", "run_kernel", "_start"):
      addr = self.find_symbol(name)
      if addr is not None and addr != 0:
        return addr
    return None

  def _demangle(self, mangled: str) -> str:
    if not _CXXFILT.is_file() or not mangled.startswith("_Z"):
      return mangled
    try:
      out = subprocess.run(
        [str(_CXXFILT), mangled],
        capture_output=True, text=True, timeout=2,
      )
      return out.stdout.strip() or mangled
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
      return mangled


class ElfStore:
  """Manages ElfInfo objects for all kernel ELFs in a debug session.

  Maps (risc_name) -> ElfInfo. Populated when kernels are compiled
  with debug info.
  """

  def __init__(self):
    self.elfs: dict[str, ElfInfo] = {}

  def add(self, risc: str, elf_bytes: bytes):
    if risc in self.elfs:
      self.elfs[risc].close()
    self.elfs[risc] = ElfInfo(elf_bytes, name=risc)

  def get(self, risc: str) -> ElfInfo | None:
    return self.elfs.get(risc)

  def resolve(self, risc: str, pc: int) -> str:
    """One-line summary: func() at file:line"""
    info = self.get(risc)
    if info is None:
      return f"0x{pc:08x} (no ELF)"
    filepath, lineno, func = info.addr2line(pc)
    if filepath == "??":
      return f"0x{pc:08x} (no debug info)"
    short = Path(filepath).name
    return f"{func}() at {short}:{lineno}"

  def close(self):
    for elf in self.elfs.values():
      elf.close()
    self.elfs.clear()


def _bisect_right(a: list[int], x: int) -> int:
  lo, hi = 0, len(a)
  while lo < hi:
    mid = (lo + hi) // 2
    if a[mid] <= x:
      lo = mid + 1
    else:
      hi = mid
  return lo
