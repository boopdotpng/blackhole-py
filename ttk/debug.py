from __future__ import annotations

import atexit
import os
import struct
import sys
from dataclasses import dataclass
from dsl import Reg, t0, t1

@dataclass(frozen=True)
class DebugEvent:
  index: int
  kind: str
  address: int
  name: str
  value: str | None = None

def parse_debug_core(value: str) -> tuple[int, int]:
  x, y = value.split(",", 1)
  return int(x, 0), int(y, 0)

def print_debug_postmortem(
  core: tuple[int, int],
  addrs: set[int],
  events: list[DebugEvent] | None = None,
  *,
  file=None,
):
  from pcie import PCIDevice, TLBWindow

  if not addrs:
    return

  out = sys.stdout if file is None else file
  dev = PCIDevice(use_vfio=False)
  try:
    with TLBWindow(dev, core) as win:
      words = {}
      for addr in sorted(addrs):
        data = bytes(win.mm[addr + i] for i in range(4))
        words[addr] = struct.unpack("<I", data)[0]
      print_debug_values(core, words, events or [], file=out)
  finally:
    dev.close()

def print_debug_values(
  core: tuple[int, int],
  words: dict[int, int],
  events: list[DebugEvent],
  *,
  file=None,
):
  if not words:
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

class Debug:
  _debug_postmortem_registered = False
  _debug_addrs: set[int] = set()
  _debug_counter = 0
  _debug_events: list[DebugEvent] = []

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
      core = parse_debug_core(os.environ.get("TT_DEBUG_POSTMORTEM_CORE", "1,2"))
      try:
        print_debug_postmortem(core, cls._debug_addrs, cls._debug_events, file=sys.stderr)
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
    if breadcrumbs:
      print("breadcrumbs", file=out)
      for event in breadcrumbs:
        print(f"  {event.index}: {event.name} @ 0x{event.address:x}", file=out)
    if writes:
      print("debug writes", file=out)
      for event in writes:
        value = "" if event.value is None else f" = {event.value}"
        print(f"  {event.name}{value} @ 0x{event.address:x}", file=out)

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
