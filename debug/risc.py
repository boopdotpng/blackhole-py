"""Per-RISC Blackhole debug control built on top of DR transport."""

from __future__ import annotations

import time

from debug.regs import (
  CMD_CONTINUE,
  CMD_DEBUG_MODE,
  CMD_HALT,
  CMD_READ_MEMORY,
  CMD_READ_REGISTER,
  CMD_STEP,
  CMD_WRITE_MEMORY,
  CMD_WRITE_REGISTER,
  DR_COMMAND,
  DR_COMMAND_ARG_0,
  DR_COMMAND_ARG_1,
  DR_COMMAND_RETURN_VALUE,
  DR_STATUS,
  DR_WATCHPOINT_BASE,
  DR_WATCHPOINT_SETTINGS,
  GPR_COUNT,
  GPR_PC,
  STATUS_EBREAK_HIT,
  STATUS_HALTED,
  STATUS_MEM_WATCHPOINT_HIT,
  STATUS_PC_WATCHPOINT_HIT,
  WP_DISABLED,
  WP_MASK,
  WP_PC_BREAK,
)
from debug.transport import DRTransport


class RiscDebug:
  POLL_INTERVAL = 0.00005
  HALT_TIMEOUT = 1.0

  def __init__(self, tlb, core, risc: str):
    self.transport = DRTransport(tlb, core, risc)
    self.tlb = tlb
    self.core = core
    self.risc = risc

  def read_status(self) -> int:
    return self.transport.read_dr(DR_STATUS)

  def is_halted(self) -> bool:
    return bool(self.read_status() & STATUS_HALTED)

  def is_breakpoint_hit(self) -> bool:
    return bool(self.read_status() & STATUS_PC_WATCHPOINT_HIT)

  def is_watchpoint_hit(self) -> bool:
    return bool(self.read_status() & STATUS_MEM_WATCHPOINT_HIT)

  def is_ebreak_hit(self) -> bool:
    return bool(self.read_status() & STATUS_EBREAK_HIT)

  def wait_halted(self, timeout: float | None = None):
    deadline = time.monotonic() + (self.HALT_TIMEOUT if timeout is None else timeout)
    while True:
      if self.is_halted():
        return
      if time.monotonic() > deadline:
        raise TimeoutError(f"core {self.core} {self.risc} did not halt")
      time.sleep(self.POLL_INTERVAL)

  def assert_halted(self, operation: str = "operation"):
    if not self.is_halted():
      raise RuntimeError(f"core {self.core} {self.risc} must be halted for {operation}")

  def halt(self):
    self.transport.write_dr(DR_COMMAND, CMD_DEBUG_MODE | CMD_HALT)
    self.wait_halted()

  def cont(self):
    self.transport.write_dr(DR_COMMAND, CMD_DEBUG_MODE | CMD_CONTINUE)

  def step(self):
    self.assert_halted("step")
    self.transport.write_dr(DR_COMMAND, CMD_DEBUG_MODE | CMD_STEP)
    self.transport.write_dr(DR_COMMAND, CMD_DEBUG_MODE | CMD_STEP)
    self.wait_halted()

  def read_gpr(self, register_index: int) -> int:
    if not 0 <= register_index <= GPR_PC:
      raise ValueError(f"invalid register index {register_index}")
    self.assert_halted("read_gpr")
    self.transport.write_dr(DR_COMMAND_ARG_0, register_index)
    self.transport.write_dr(DR_COMMAND, CMD_DEBUG_MODE | CMD_READ_REGISTER)
    return self.transport.read_dr(DR_COMMAND_RETURN_VALUE)

  def read_all_gprs(self) -> list[int]:
    self.assert_halted("read_all_gprs")
    return [self.read_gpr(i) for i in range(GPR_COUNT + 1)]

  def read_pc(self) -> int:
    return self.read_gpr(GPR_PC)

  def write_gpr(self, register_index: int, value: int):
    if not 0 <= register_index <= GPR_PC:
      raise ValueError(f"invalid register index {register_index}")
    self.assert_halted("write_gpr")
    self.transport.write_dr(DR_COMMAND_ARG_1, value)
    self.transport.write_dr(DR_COMMAND_ARG_0, register_index)
    self.transport.write_dr(DR_COMMAND, CMD_DEBUG_MODE | CMD_WRITE_REGISTER)

  def read_memory(self, address: int) -> int:
    self.assert_halted("read_memory")
    self.transport.write_dr(DR_COMMAND_ARG_0, address)
    self.transport.write_dr(DR_COMMAND, CMD_DEBUG_MODE | CMD_READ_MEMORY)
    return self.transport.read_dr(DR_COMMAND_RETURN_VALUE)

  def read_words(self, address: int, count: int) -> list[int]:
    self.assert_halted("read_words")
    return [self.read_memory(address + i * 4) for i in range(count)]

  def write_memory(self, address: int, value: int):
    self.assert_halted("write_memory")
    self.transport.write_dr(DR_COMMAND_ARG_1, value)
    self.transport.write_dr(DR_COMMAND_ARG_0, address)
    self.transport.write_dr(DR_COMMAND, CMD_DEBUG_MODE | CMD_WRITE_MEMORY)

  def _update_watchpoint_setting(self, index: int, mode: int):
    if not 0 <= index < 8:
      raise ValueError(f"invalid watchpoint index {index}")
    if not 0 <= mode <= WP_MASK:
      raise ValueError(f"invalid watchpoint mode {mode}")
    settings = self.transport.read_dr(DR_WATCHPOINT_SETTINGS)
    shift = index * 4
    settings = (settings & ~(WP_MASK << shift)) | (mode << shift)
    self.transport.write_dr(DR_WATCHPOINT_SETTINGS, settings)

  def set_pc_breakpoint(self, index: int, address: int):
    self.transport.write_dr(DR_WATCHPOINT_BASE + index, address)
    self._update_watchpoint_setting(index, WP_PC_BREAK)

  def clear_breakpoint(self, index: int):
    self._update_watchpoint_setting(index, WP_DISABLED)

  def clear_all_breakpoints(self):
    for index in range(8):
      self._update_watchpoint_setting(index, WP_DISABLED)
