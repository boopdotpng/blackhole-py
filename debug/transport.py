"""Low-level Blackhole DR transport."""

from __future__ import annotations

import time

from debug.regs import (
  CNTL0_TRIGGER,
  DEBUG_TLB_BASE,
  RISC_DBG_CNTL_0,
  RISC_DBG_CNTL_1,
  RISC_DBG_STATUS_0,
  RISC_DBG_STATUS_1,
  RISC_SEL,
  STATUS0_READ_VALID,
  cntl0_value,
)


class DRTransport:
  POLL_INTERVAL = 0.00001
  POLL_TIMEOUT = 0.5

  def __init__(self, tlb, core, risc: str):
    if risc not in RISC_SEL:
      raise ValueError(f"unsupported debug RISC {risc!r}")
    self.tlb = tlb
    self.core = core
    self.risc = risc
    self._target_debug_regs()

  def _target_debug_regs(self):
    from hw import NocOrdering

    self.tlb.target(self.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)

  @staticmethod
  def _offset(addr: int) -> int:
    return addr - DEBUG_TLB_BASE

  def _write_reg(self, addr: int, value: int):
    self.tlb.write32(self._offset(addr), value & 0xFFFFFFFF)

  def _read_reg(self, addr: int) -> int:
    return self.tlb.read32(self._offset(addr))

  def _wait_status0(self, predicate, timeout: float | None = None, description: str = "status0 condition") -> int:
    deadline = time.monotonic() + (self.POLL_TIMEOUT if timeout is None else timeout)
    while True:
      status = self._read_reg(RISC_DBG_STATUS_0)
      if predicate(status):
        return status
      if time.monotonic() > deadline:
        raise TimeoutError(f"timeout waiting for {description} on {self.core} {self.risc}")
      time.sleep(self.POLL_INTERVAL)

  def _wait_trigger(self, expected: bool, timeout: float | None = None) -> int:
    return self._wait_status0(
      lambda status: bool(status & CNTL0_TRIGGER) == expected,
      timeout=timeout,
      description=f"trigger echo == {int(expected)}",
    )

  def _wait_read_valid(self, timeout: float | None = None) -> int:
    return self._wait_status0(
      lambda status: bool(status & CNTL0_TRIGGER) and bool(status & STATUS0_READ_VALID),
      timeout=timeout,
      description="read-valid with trigger echo",
    )

  def write_dr(self, dr_addr: int, value: int, robust: bool = True):
    self._target_debug_regs()
    self._write_reg(RISC_DBG_CNTL_1, value)
    self._write_reg(RISC_DBG_CNTL_0, 0)
    if robust:
      self._wait_trigger(False)
    self._write_reg(RISC_DBG_CNTL_0, cntl0_value(self.risc, dr_addr, is_write=True, trigger=True))
    if robust:
      self._wait_trigger(True)

  def read_dr(self, dr_addr: int, robust: bool = True) -> int:
    self._target_debug_regs()
    self._write_reg(RISC_DBG_CNTL_0, 0)
    if robust:
      self._wait_trigger(False)
    self._write_reg(RISC_DBG_CNTL_0, cntl0_value(self.risc, dr_addr, is_write=False, trigger=True))
    if robust:
      self._wait_read_valid()
    else:
      deadline = time.monotonic() + self.POLL_TIMEOUT
      while not (self._read_reg(RISC_DBG_STATUS_0) & STATUS0_READ_VALID):
        if time.monotonic() > deadline:
          raise TimeoutError(f"timeout waiting for DR({dr_addr}) read-valid on {self.core} {self.risc}")
        time.sleep(self.POLL_INTERVAL)
    return self._read_reg(RISC_DBG_STATUS_1)
