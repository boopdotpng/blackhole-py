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

def print_debug_postmortem(core: tuple[int, int], addrs: set[int], *, file=None):
  from pcie import PCIDevice, TLBWindow

  if not addrs:
    return

  out = sys.stdout if file is None else file
  dev = PCIDevice(use_vfio=False)
  try:
    with TLBWindow(dev, core) as win:
      print(f"debug postmortem core {core}", file=out)
      for addr in sorted(addrs):
        data = bytes(win.mm[addr + i] for i in range(4))
        word = struct.unpack("<I", data)[0]
        print(f"0x{addr:x}: 0x{word:08x}", file=out)
  finally:
    dev.close()

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
        cls.print_debug_legend(file=sys.stderr)
        print_debug_postmortem(core, cls._debug_addrs, file=sys.stderr)
      except Exception as exc:
        print(f"debug postmortem failed: {exc}", file=sys.stderr)

    atexit.register(run_postmortem)

  @classmethod
  def print_debug_legend(cls, *, file=None):
    if not cls._debug_events:
      return
    out = sys.stdout if file is None else file
    print("debug trace legend", file=out)
    for event in cls._debug_events:
      suffix = "" if event.value is None else f" = {event.value}"
      if event.kind == "breadcrumb":
        print(f"{event.index}: breadcrumb {event.name}", file=out)
      else:
        print(
          f"{event.index}: {event.kind} {event.name} @ 0x{event.address:x}{suffix}",
          file=out,
        )

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
    name: str = "debug_write",
    tmp_addr: Reg = t0,
    tmp_val: Reg = t1,
  ):
    event = self.next_debug_value()
    Debug._debug_events.append(
      DebugEvent(event, "debug_write", address, name, self._debug_value_text(value))
    )
    self.note_debug_addr(address)
    return self.write32(address, value, tmp_addr=tmp_addr, tmp_val=tmp_val)
