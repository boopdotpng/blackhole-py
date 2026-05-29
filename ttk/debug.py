from __future__ import annotations

import atexit
import struct
import sys
from dataclasses import dataclass
from dsl import Reg, t0, t1, t2, t3, t4, t5
from ttk.addrs import Dram, NocCfg, noc_xy

@dataclass(frozen=True)
class DebugEvent:
  index: int
  kind: str
  address: int
  name: str
  value: str | None = None

@dataclass(frozen=True)
class DebugRange:
  index: int
  kind: str
  address: int
  size: int
  name: str
  bank: int | None = None
  tile: int = 0

def _read_bytes(win, addr: int, size: int) -> bytes:
  return bytes(win.mm[addr + i] for i in range(size))

def _format_words(data: bytes, base: int, *, max_words: int = 64) -> list[str]:
  lines = []
  words = (len(data) + 3) // 4
  shown = min(words, max_words)
  for i in range(shown):
    chunk = data[i * 4 : i * 4 + 4].ljust(4, b"\0")
    word = struct.unpack("<I", chunk)[0]
    lines.append(f"    0x{base + i * 4:x}: 0x{word:08x}")
  if words > shown:
    lines.append(f"    ... {words - shown} more words")
  return lines

def print_debug_postmortem(
  core: tuple[int, int],
  addrs: set[int],
  events: list[DebugEvent] | None = None,
  ranges: list[DebugRange] | None = None,
  *,
  file=None,
):
  from pcie import PCIDevice, TLBWindow

  if not addrs and not ranges:
    return

  out = sys.stdout if file is None else file
  dev = PCIDevice(use_vfio=False)
  try:
    with TLBWindow(dev, core) as win:
      words = {}
      for addr in sorted(addrs):
        data = bytes(win.mm[addr + i] for i in range(4))
        words[addr] = struct.unpack("<I", data)[0]
      l1_ranges = []
      dram_ranges = []
      for item in ranges or []:
        if item.kind == "dram":
          x = Dram.BANK_X[item.bank or 0]
          y = Dram.BANK_TILE_YS[item.bank or 0][item.tile]
          win.target((x, y))
          dram_ranges.append((item, _read_bytes(win, item.address, item.size)))
        else:
          win.target(core)
          l1_ranges.append((item, _read_bytes(win, item.address, item.size)))
      print_debug_values(core, words, events or [], l1_ranges, dram_ranges, file=out)
  finally:
    dev.close()

def print_debug_values(
  core: tuple[int, int],
  words: dict[int, int],
  events: list[DebugEvent],
  l1_ranges: list[tuple[DebugRange, bytes]] | None = None,
  dram_ranges: list[tuple[DebugRange, bytes]] | None = None,
  *,
  file=None,
):
  if not words and not l1_ranges and not dram_ranges:
    return

  out = sys.stdout if file is None else file
  print(f"debug core {core}", file=out)

  breadcrumbs = [event for event in events if event.kind == "breadcrumb"]
  if breadcrumbs:
    print("breadcrumbs", file=out)
    by_index = {event.index: event for event in breadcrumbs}
    for addr in sorted({event.address for event in breadcrumbs}):
      event = by_index.get(words.get(addr))
      name = event.name if event is not None else "not reached"
      print(f"  {name} @ 0x{addr:x}", file=out)

  writes = [event for event in events if event.kind == "debug_write"]
  if writes:
    print("debug writes", file=out)
    for event in writes:
      word = words.get(event.address)
      if word is None:
        continue
      print(f"  {event.name} = 0x{word:08x} @ 0x{event.address:x}", file=out)

  known_addrs = {event.address for event in events}
  other_addrs = sorted(set(words) - known_addrs)
  if other_addrs:
    print("debug addresses", file=out)
    for addr in other_addrs:
      print(f"  0x{addr:x} = 0x{words[addr]:08x}", file=out)

  if l1_ranges:
    print("debug l1 ranges", file=out)
    for item, data in l1_ranges:
      print(f"  {item.name} @ 0x{item.address:x} ({item.size} bytes)", file=out)
      for line in _format_words(data, item.address):
        print(line, file=out)

  if dram_ranges:
    print("debug dram ranges", file=out)
    for item, data in dram_ranges:
      print(
        f"  {item.name} bank{item.bank}/tile{item.tile} @ 0x{item.address:x} "
        f"({item.size} bytes)",
        file=out,
      )
      for line in _format_words(data, item.address):
        print(line, file=out)

class Debug:
  _debug_postmortem_registered = False
  _debug_addrs: set[int] = set()
  _debug_counter = 0
  _debug_events: list[DebugEvent] = []
  _debug_ranges: list[DebugRange] = []

  @classmethod
  def note_debug_addr(cls, addr: int):
    cls._debug_addrs.add(addr)
    cls.register_debug_postmortem()

  @classmethod
  def register_debug_postmortem(cls):
    if cls._debug_postmortem_registered:
      return
    cls._debug_postmortem_registered = True

    def run_postmortem():
      if not cls._debug_addrs:
        return
      core = (1, 2)
      try:
        print_debug_postmortem(
          core,
          cls._debug_addrs,
          cls._debug_events,
          cls._debug_ranges,
          file=sys.stderr,
        )
      except Exception as exc:
        print(f"debug postmortem failed: {exc}", file=sys.stderr)

    atexit.register(run_postmortem)

  @classmethod
  def print_debug_legend(cls, *, file=None):
    if not cls._debug_events:
      return
    out = sys.stdout if file is None else file
    breadcrumbs = [event for event in cls._debug_events if event.kind == "breadcrumb"]
    writes = [event for event in cls._debug_events if event.kind == "debug_write"]
    ranges = cls._debug_ranges
    if breadcrumbs:
      print("breadcrumbs", file=out)
      for event in breadcrumbs:
        print(f"  {event.index}: {event.name} @ 0x{event.address:x}", file=out)
    if writes:
      print("debug writes", file=out)
      for event in writes:
        value = "" if event.value is None else f" = {event.value}"
        print(f"  {event.name}{value} @ 0x{event.address:x}", file=out)
    if ranges:
      print("debug ranges", file=out)
      for item in ranges:
        where = f"bank{item.bank}/tile{item.tile}" if item.kind == "dram" else "l1"
        print(f"  {item.index}: {item.name} {where} @ 0x{item.address:x} ({item.size} bytes)", file=out)

  @staticmethod
  def next_debug_value() -> int:
    Debug._debug_counter += 1
    return Debug._debug_counter

  @staticmethod
  def _debug_value_text(value: int | Reg) -> str:
    if isinstance(value, int):
      return f"0x{value & 0xFFFFFFFF:08x}"
    return repr(value)

  def breadcrumb(self, address: int, name: str):
    value = self.next_debug_value()
    Debug._debug_events.append(DebugEvent(value, "breadcrumb", address, name))
    self.note_debug_addr(address)
    return self.write32(address, value)

  def debug_write(
    self,
    address: int,
    value: int | Reg,
    *,
    name: str,
    tmp_addr: Reg = t0,
    tmp_val: Reg = t1,
  ):
    event = self.next_debug_value()
    Debug._debug_events.append(
      DebugEvent(event, "debug_write", address, name, self._debug_value_text(value))
    )
    self.note_debug_addr(address)
    return self.write32(address, value, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def debug_l1_range(self, address: int, size: int, *, name: str):
    event = self.next_debug_value()
    Debug._debug_ranges.append(DebugRange(event, "l1", address, size, name))
    self.register_debug_postmortem()
    return self

  def debug_copy_l1_range(
    self,
    dst: int | Reg,
    src: int | Reg,
    size: int | Reg,
    *,
    name: str,
    dst_addr: int | None = None,
    dst_reg: Reg = t0,
    src_reg: Reg = t1,
    value: Reg = t2,
    count: Reg = t3,
  ):
    if dst_addr is not None and isinstance(size, int):
      self.debug_l1_range(dst_addr, size, name=name)
    elif isinstance(dst, int) and isinstance(size, int):
      self.debug_l1_range(dst, size, name=name)
    return self.copy_words(dst, src, size, dst_reg=dst_reg, src_reg=src_reg, value=value, count=count)

  def debug_dram_write32(
    self,
    address: int,
    value: int | Reg,
    *,
    name: str,
    bank: int = 0,
    tile: int = 0,
    noc: int = 0,
    buf: int = NocCfg.NCRISC_WR_CMD_BUF,
    scratch: int = 0x19080,
    src_reg: Reg = t2,
    dst_reg: Reg = t3,
    coord_reg: Reg = t4,
    len_reg: Reg = t5,
    tmp_addr: Reg = t0,
    tmp_val: Reg = t1,
  ):
    # Only call this from BRISC/NCRISC after their NOC command buffers are initialized.
    # TRISC kernels should dump to L1 and let host or a NOC-owning RISC read it back.
    event = self.next_debug_value()
    Debug._debug_ranges.append(DebugRange(event, "dram", address, 4, name, bank=bank, tile=tile))
    self.register_debug_postmortem()
    self.write32(scratch, value, tmp_addr=tmp_addr, tmp_val=tmp_val)
    self.li(src_reg, scratch)
    self.li(dst_reg, address)
    self.li(coord_reg, noc_xy(Dram.BANK_X[bank], Dram.BANK_TILE_YS[bank][tile]))
    self.li(len_reg, 4)
    return self.noc_write(noc, buf, src_reg, dst_reg, 0, coord_reg, len_reg, posted=False, a=tmp_addr, v=tmp_val)

  def debug_dram_range(
    self,
    address: int,
    size: int,
    *,
    name: str,
    bank: int = 0,
    tile: int = 0,
  ):
    event = self.next_debug_value()
    Debug._debug_ranges.append(DebugRange(event, "dram", address, size, name, bank=bank, tile=tile))
    self.register_debug_postmortem()
    return self

  def debug_dram_write_range(
    self,
    src: int | Reg,
    address: int,
    size: int | Reg,
    *,
    name: str,
    bank: int = 0,
    tile: int = 0,
    noc: int = 0,
    buf: int = NocCfg.NCRISC_WR_CMD_BUF,
    src_reg: Reg = t2,
    dst_reg: Reg = t3,
    coord_reg: Reg = t4,
    len_reg: Reg = t5,
    tmp_addr: Reg = t0,
    tmp_val: Reg = t1,
  ):
    # Only call this from BRISC/NCRISC after their NOC command buffers are initialized.
    # TRISC kernels should dump to L1 and let host or a NOC-owning RISC read it back.
    if isinstance(size, int):
      self.debug_dram_range(address, size, name=name, bank=bank, tile=tile)
    if isinstance(src, int):
      self.li(src_reg, src)
      src = src_reg
    self.li(dst_reg, address)
    self.li(coord_reg, noc_xy(Dram.BANK_X[bank], Dram.BANK_TILE_YS[bank][tile]))
    if isinstance(size, int):
      self.li(len_reg, size)
      size = len_reg
    return self.noc_write(noc, buf, src, dst_reg, 0, coord_reg, size, posted=False, a=tmp_addr, v=tmp_val)
