from __future__ import annotations

import atexit
import os
import struct
import sys

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
        print_debug_postmortem(core, cls._debug_addrs, file=sys.stderr)
      except Exception as exc:
        print(f"debug postmortem failed: {exc}", file=sys.stderr)

    atexit.register(run_postmortem)

  def breadcrumb(self, addr: int, value: int):
    self.note_debug_addr(addr)
    return self.write32(addr, value)
