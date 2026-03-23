"""Blackhole debug-bus helpers."""

from __future__ import annotations

import time

from debug.regs import DBG_BUS_CTRL, DBG_BUS_RD_DATA, DEBUG_TLB_BASE, PC_SIGNALS, dbg_bus_cntl


class DebugBus:
  SETTLE_TIME = 0.00001

  def __init__(self, tlb, core):
    self.tlb = tlb
    self.core = core

  def _target_debug_regs(self):
    from hw import NocOrdering

    self.tlb.target(self.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)

  @staticmethod
  def _offset(addr: int) -> int:
    return addr - DEBUG_TLB_BASE

  def read_signal(self, sig_sel: int, daisy_sel: int, rd_sel: int) -> int:
    self._target_debug_regs()
    self.tlb.write32(self._offset(DBG_BUS_CTRL), dbg_bus_cntl(sig_sel, daisy_sel, rd_sel))
    time.sleep(self.SETTLE_TIME)
    return self.tlb.read32(self._offset(DBG_BUS_RD_DATA))

  def read_pc(self, risc: str) -> int:
    signal = PC_SIGNALS[risc]
    raw = self.read_signal(signal["sig_sel"], signal["daisy_sel"], signal["rd_sel"])
    return raw & signal["mask"]
