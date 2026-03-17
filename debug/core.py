# debug/core.py - Low-level RISC-V debug register protocol for Blackhole
#
# Implements the DR (Debug Register) read/write protocol over NOC via TLBWindow,
# plus halt/step/continue, GPR access, memory access, and hardware breakpoints.
#
# Reference: tt-isa-documentation/WormholeB0/TensixTile/BabyRISCV/DebugInterface.md
#            tt-exalens/ttexalens/hardware/baby_risc_debug.py

from __future__ import annotations
import time, struct, sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from hw import TLBWindow, Core

from debug.regs import (
  RISC_DBG_CNTL_0, RISC_DBG_CNTL_1, RISC_DBG_STATUS_0, RISC_DBG_STATUS_1,
  STATUS_0_READ_VALID, RISC_SEL, CNTL0_WRITE, CNTL0_READ,
  DR_STATUS, DR_COMMAND, DR_COMMAND_ARG_0, DR_COMMAND_ARG_1,
  DR_COMMAND_RETURN_VALUE, DR_WATCHPOINT_SETTINGS, DR_WATCHPOINT_BASE,
  STATUS_HALTED, STATUS_PC_WATCHPOINT_HIT, STATUS_MEM_WATCHPOINT_HIT,
  STATUS_EBREAK_HIT, CMD_HALT, CMD_STEP, CMD_CONTINUE,
  CMD_READ_REGISTER, CMD_WRITE_REGISTER, CMD_READ_MEMORY, CMD_WRITE_MEMORY,
  CMD_DEBUG_MODE, WP_DISABLED, WP_PC_BREAK, WP_MEM_READ, WP_MEM_WRITE,
  WP_MEM_READ_WRITE, GPR_COUNT, GPR_PC, GPR_NAMES, SOFT_RESET_0,
  SOFT_RESET_BITS, SOFT_RESET_ALL_FULL,
  DBG_BUS_CTRL, DBG_BUS_RD_DATA, dbg_bus_cntl, PC_SIGNALS,
  WALL_CLOCK_L, WALL_CLOCK_H, DEBUG_REGS_BASE,
  DEBUG_TLB_BASE,
)


class RiscDebug:
  """Debug interface for a single RISC-V core on a single Tensix tile.

  Talks to the hardware debug registers via a TLBWindow pointed at the
  target core's NOC coordinate. Only works for brisc/trisc0/trisc1/trisc2
  (ncrisc has no debug hardware).
  """

  MAX_WATCHPOINTS = 8
  DR_POLL_TIMEOUT = 0.5  # seconds
  DR_POLL_INTERVAL = 0.0001  # 100us between polls

  def __init__(self, tlb: TLBWindow, core: Core, risc: str):
    if risc not in RISC_SEL:
      raise ValueError(f"risc must be one of {list(RISC_SEL)}, got {risc!r} (ncrisc has no debug hw)")
    self.tlb = tlb
    self.core = core
    self.risc = risc
    self._cntl0_write = CNTL0_WRITE[risc]
    self._cntl0_read = CNTL0_READ[risc]
    # ensure TLB is pointed at our core
    self._target_debug_regs()

  def _target_debug_regs(self):
    """Point TLB at the 2MB-aligned window containing debug registers."""
    from hw import NocOrdering
    self.tlb.target(self.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)

  def _offset(self, addr: int) -> int:
    """Convert absolute address to TLB offset (relative to 2MB-aligned base)."""
    return addr - DEBUG_TLB_BASE

  # -- raw register access ------------------------------------------------- #

  def _write_reg(self, addr: int, value: int):
    self.tlb.write32(self._offset(addr), value)

  def _read_reg(self, addr: int) -> int:
    return self.tlb.read32(self._offset(addr))

  # -- DR (debug register) protocol ---------------------------------------- #

  def _dr_write(self, dr_addr: int, value: int):
    """Write a value to debug register DR(dr_addr).

    Protocol:
      1. Write value to CNTL_1
      2. Write (CNTL0_WRITE | dr_addr) to CNTL_0  (pulse triggers)
      3. Write 0 to CNTL_0 (de-assert pulse)
    """
    self._write_reg(RISC_DBG_CNTL_1, value & 0xFFFFFFFF)
    self._write_reg(RISC_DBG_CNTL_0, self._cntl0_write | (dr_addr & 0x7FF))
    self._write_reg(RISC_DBG_CNTL_0, 0)

  def _dr_read(self, dr_addr: int) -> int:
    """Read a value from debug register DR(dr_addr).

    Protocol:
      1. Write (CNTL0_READ | dr_addr) to CNTL_0  (pulse triggers)
      2. Write 0 to CNTL_0 (de-assert pulse)
      3. Poll STATUS_0 for read_valid bit
      4. Read result from STATUS_1
    """
    self._write_reg(RISC_DBG_CNTL_0, self._cntl0_read | (dr_addr & 0x7FF))
    self._write_reg(RISC_DBG_CNTL_0, 0)
    deadline = time.monotonic() + self.DR_POLL_TIMEOUT
    while True:
      status = self._read_reg(RISC_DBG_STATUS_0)
      if status & STATUS_0_READ_VALID:
        break
      if time.monotonic() > deadline:
        raise TimeoutError(f"DR read timeout: {self.risc} DR({dr_addr}) on core {self.core}")
      time.sleep(self.DR_POLL_INTERVAL)
    return self._read_reg(RISC_DBG_STATUS_1)

  # -- execution control --------------------------------------------------- #

  def halt(self):
    """Halt the core. Blocks until halted."""
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_HALT)
    self._wait_halted()

  def step(self):
    """Single-step one instruction. Core must be halted.

    Blackhole hardware bug: step must be issued twice.
    """
    self._assert_halted("step")
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_STEP)
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_STEP)  # BH double-step bug
    self._wait_halted()

  def cont(self):
    """Resume execution."""
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_CONTINUE)

  def read_status(self) -> int:
    """Read the status register DR(0)."""
    return self._dr_read(DR_STATUS)

  def is_halted(self) -> bool:
    return bool(self.read_status() & STATUS_HALTED)

  def _wait_halted(self, timeout: float = 1.0):
    deadline = time.monotonic() + timeout
    while True:
      if self.is_halted():
        return
      if time.monotonic() > deadline:
        raise TimeoutError(f"core {self.core} {self.risc} did not halt within {timeout}s")
      time.sleep(self.DR_POLL_INTERVAL)

  def _assert_halted(self, op: str):
    if not self.is_halted():
      raise RuntimeError(f"core {self.core} {self.risc} must be halted for {op}")

  # -- GPR access ---------------------------------------------------------- #

  def read_gpr(self, reg: int) -> int:
    """Read GPR x0..x31 or PC (reg=32). Core must be halted."""
    if reg == GPR_PC:
      return self.read_pc()
    self._assert_halted("read_gpr")
    self._dr_write(DR_COMMAND_ARG_0, reg)
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_READ_REGISTER)
    return self._dr_read(DR_COMMAND_RETURN_VALUE)

  def write_gpr(self, reg: int, value: int):
    """Write GPR x1..x31 or PC (reg=32). Core must be halted."""
    self._assert_halted("write_gpr")
    self._dr_write(DR_COMMAND_ARG_1, value & 0xFFFFFFFF)
    self._dr_write(DR_COMMAND_ARG_0, reg)
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_WRITE_REGISTER)

  def read_all_gprs(self) -> dict[str, int]:
    """Read all 32 GPRs + PC. Core must be halted."""
    self._assert_halted("read_all_gprs")
    regs = {}
    for i in range(GPR_COUNT):
      regs[GPR_NAMES[i]] = self.read_gpr(i)
    regs["pc"] = self.read_pc()
    return regs

  # -- PC access ----------------------------------------------------------- #

  def read_pc(self) -> int:
    """Read the program counter.

    On Blackhole, PC is read via the debug bus (non-intrusive) rather
    than the DR protocol. This works even when the core is running.
    Falls back to DR protocol if debug bus read fails.
    """
    return self.read_pc_debug_bus()

  def read_pc_debug_bus(self) -> int:
    """Read PC via debug bus daisy chain. Non-intrusive."""
    sig = PC_SIGNALS[self.risc]
    cntl = dbg_bus_cntl(sig["sig_sel"], sig["daisy_sel"], sig["rd_sel"])
    self._write_reg(DBG_BUS_CTRL, cntl)
    # small delay for signal to propagate
    time.sleep(0.00001)
    raw = self._read_reg(DBG_BUS_RD_DATA)
    pc = raw & sig["mask"]
    # ncrisc top-bit fixup (not applicable here but keep pattern)
    return pc

  def read_pc_dr(self) -> int:
    """Read PC via DR protocol. Core must be halted."""
    self._assert_halted("read_pc_dr")
    self._dr_write(DR_COMMAND_ARG_0, GPR_PC)
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_READ_REGISTER)
    return self._dr_read(DR_COMMAND_RETURN_VALUE)

  # -- memory access (as the core) ----------------------------------------- #

  def read_memory(self, addr: int) -> int:
    """Read a 32-bit word from the core's address space. Core must be halted.

    This executes a load from the core's perspective, so it can access
    private memory, L1, CFG space, etc.
    """
    self._assert_halted("read_memory")
    self._dr_write(DR_COMMAND_ARG_0, addr)
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_READ_MEMORY)
    return self._dr_read(DR_COMMAND_RETURN_VALUE)

  def write_memory(self, addr: int, value: int):
    """Write a 32-bit word to the core's address space. Core must be halted."""
    self._assert_halted("write_memory")
    self._dr_write(DR_COMMAND_ARG_1, value & 0xFFFFFFFF)
    self._dr_write(DR_COMMAND_ARG_0, addr)
    self._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_WRITE_MEMORY)

  # -- hardware breakpoints / watchpoints ---------------------------------- #

  def set_breakpoint(self, index: int, pc_addr: int):
    """Set a PC breakpoint (instruction breakpoint) at the given address.

    Up to 8 breakpoints (index 0..7).
    """
    if not 0 <= index < self.MAX_WATCHPOINTS:
      raise ValueError(f"breakpoint index must be 0..{self.MAX_WATCHPOINTS - 1}")
    self._set_watchpoint(index, WP_PC_BREAK, pc_addr)

  def set_watchpoint(self, index: int, addr: int, mode: str = "rw"):
    """Set a memory watchpoint.

    mode: "r" = read, "w" = write, "rw" = read or write
    """
    if not 0 <= index < self.MAX_WATCHPOINTS:
      raise ValueError(f"watchpoint index must be 0..{self.MAX_WATCHPOINTS - 1}")
    wp_mode = {"r": WP_MEM_READ, "w": WP_MEM_WRITE, "rw": WP_MEM_READ_WRITE}[mode]
    self._set_watchpoint(index, wp_mode, addr)

  def clear_breakpoint(self, index: int):
    """Clear a breakpoint/watchpoint."""
    self._set_watchpoint(index, WP_DISABLED, 0)

  def clear_all_breakpoints(self):
    """Clear all 8 breakpoints/watchpoints."""
    self._dr_write(DR_WATCHPOINT_SETTINGS, 0)
    for i in range(self.MAX_WATCHPOINTS):
      self._dr_write(DR_WATCHPOINT_BASE + i, 0)

  def _set_watchpoint(self, index: int, mode: int, addr: int):
    self._dr_write(DR_WATCHPOINT_BASE + index, addr)
    settings = self._dr_read(DR_WATCHPOINT_SETTINGS)
    shift = index * 4
    settings = (settings & ~(0xF << shift)) | (mode << shift)
    self._dr_write(DR_WATCHPOINT_SETTINGS, settings)

  # -- wall clock ---------------------------------------------------------- #

  def read_wall_clock(self) -> int:
    """Read the 64-bit wall clock counter."""
    lo = self._read_reg(WALL_CLOCK_L)
    hi = self._read_reg(WALL_CLOCK_H)  # latches on read of _L
    return (hi << 32) | lo


class NcriscDebug:
  """Limited debug interface for NCRISC (no hardware debug registers).

  Can only read PC via debug bus and control via soft reset.
  """

  def __init__(self, tlb: TLBWindow, core: Core):
    self.tlb = tlb
    self.core = core
    self.risc = "ncrisc"
    self._target_debug_regs()

  def _target_debug_regs(self):
    from hw import NocOrdering
    self.tlb.target(self.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)

  def _offset(self, addr: int) -> int:
    return addr - DEBUG_TLB_BASE

  def _write_reg(self, addr: int, value: int):
    self.tlb.write32(self._offset(addr), value)

  def _read_reg(self, addr: int) -> int:
    return self.tlb.read32(self._offset(addr))

  def read_pc(self) -> int:
    """Read NCRISC PC via debug bus (non-intrusive, approximate)."""
    sig = PC_SIGNALS["ncrisc"]
    cntl = dbg_bus_cntl(sig["sig_sel"], sig["daisy_sel"], sig["rd_sel"])
    self._write_reg(DBG_BUS_CTRL, cntl)
    time.sleep(0.00001)
    raw = self._read_reg(DBG_BUS_RD_DATA)
    pc = raw & sig["mask"]
    # top-bit fixup for NCRISC (PC can be in 0x7xxxxxxx range, bit 31 lost)
    if pc & 0xF0000000 == 0x70000000:
      pc |= 0x80000000
    return pc


class TileDebugger:
  """Debug all RISC-V cores on a single Tensix tile.

  Manages halt/resume of all cores together, with individual stepping.
  """

  DEBUGGABLE = ("brisc", "trisc0", "trisc1", "trisc2")

  def __init__(self, tlb: TLBWindow, core: Core):
    self.tlb = tlb
    self.core = core
    self.riscs: dict[str, RiscDebug] = {}
    for risc in self.DEBUGGABLE:
      self.riscs[risc] = RiscDebug(tlb, core, risc)
    self.ncrisc = NcriscDebug(tlb, core)
    # always re-target after constructing all (they share TLB)
    self._current_risc: str | None = None

  def _select(self, risc: str) -> RiscDebug:
    """Select a RISC and ensure TLB is targeted."""
    if risc not in self.riscs:
      raise ValueError(f"cannot debug {risc} (only {list(self.riscs)})")
    rd = self.riscs[risc]
    if self._current_risc != risc:
      rd._target_debug_regs()
      self._current_risc = risc
    return rd

  def halt_all(self):
    """Halt all 4 debuggable RISCs."""
    for risc in self.DEBUGGABLE:
      rd = self._select(risc)
      rd._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_HALT)
    # wait for all to halt
    for risc in self.DEBUGGABLE:
      rd = self._select(risc)
      rd._wait_halted()

  def resume_all(self):
    """Resume all 4 debuggable RISCs."""
    for risc in self.DEBUGGABLE:
      rd = self._select(risc)
      rd._dr_write(DR_COMMAND, CMD_DEBUG_MODE | CMD_CONTINUE)
    self._current_risc = None

  def step(self, risc: str):
    """Single-step one RISC. Others stay halted."""
    rd = self._select(risc)
    rd.step()

  def read_pc(self, risc: str) -> int:
    """Read PC for any RISC (including ncrisc via debug bus)."""
    if risc == "ncrisc":
      self.ncrisc._target_debug_regs()
      self._current_risc = None
      return self.ncrisc.read_pc()
    return self._select(risc).read_pc()

  def read_all_pcs(self) -> dict[str, int]:
    """Read PCs for all 5 RISCs (non-intrusive via debug bus)."""
    pcs = {}
    for risc in (*self.DEBUGGABLE, "ncrisc"):
      pcs[risc] = self.read_pc(risc)
    return pcs

  def read_gprs(self, risc: str) -> dict[str, int]:
    """Read all GPRs + PC for a debuggable RISC. Must be halted."""
    return self._select(risc).read_all_gprs()

  def set_breakpoint(self, risc: str, index: int, pc_addr: int):
    self._select(risc).set_breakpoint(index, pc_addr)

  def clear_breakpoint(self, risc: str, index: int):
    self._select(risc).clear_breakpoint(index)

  def clear_all_breakpoints(self):
    for risc in self.DEBUGGABLE:
      self._select(risc).clear_all_breakpoints()

  def is_halted(self, risc: str) -> bool:
    return self._select(risc).is_halted()

  def read_status(self, risc: str) -> int:
    return self._select(risc).read_status()

  def status_str(self, risc: str) -> str:
    """Human-readable status string."""
    if risc == "ncrisc":
      pc = self.read_pc("ncrisc")
      return f"ncrisc  pc=0x{pc:08x} (debug bus, no halt/step)"
    st = self.read_status(risc)
    pc = self.read_pc(risc)
    flags = []
    if st & STATUS_HALTED:             flags.append("HALTED")
    if st & STATUS_PC_WATCHPOINT_HIT:  flags.append("BREAK")
    if st & STATUS_MEM_WATCHPOINT_HIT: flags.append("WATCH")
    if st & STATUS_EBREAK_HIT:         flags.append("EBREAK")
    if not flags:                      flags.append("RUNNING")
    return f"{risc:7s} pc=0x{pc:08x} [{' '.join(flags)}]"

  def read_wall_clock(self) -> int:
    """Read the tile's 64-bit wall clock."""
    rd = self._select(self.DEBUGGABLE[0])  # any RISC, same register
    return rd.read_wall_clock()
