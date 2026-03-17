# debug/multi.py - Multi-core debug operations (scan, snapshot, bulk halt/resume)
#
# Operates across all 118 worker cores using a single shared TLBWindow
# that gets retargeted per core. Designed to be fast for scanning PCs
# and status across the full grid.

from __future__ import annotations
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from hw import TLBWindow, Core

from debug.regs import (
  DEBUG_REGS_BASE, DEBUG_TLB_BASE,
  DBG_BUS_CTRL, DBG_BUS_RD_DATA, dbg_bus_cntl, PC_SIGNALS,
  RISC_DBG_CNTL_0, RISC_DBG_CNTL_1, RISC_DBG_STATUS_0, RISC_DBG_STATUS_1,
  STATUS_0_READ_VALID, CNTL0_READ,
  DR_STATUS, DR_COMMAND, CMD_DEBUG_MODE, CMD_HALT, CMD_CONTINUE,
  STATUS_HALTED, STATUS_PC_WATCHPOINT_HIT, STATUS_MEM_WATCHPOINT_HIT,
  STATUS_EBREAK_HIT, RISC_SEL,
)

ALL_RISCS = ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc")
DEBUGGABLE_RISCS = ("brisc", "trisc0", "trisc1", "trisc2")


class CoreStatus:
  """Status snapshot for one RISC on one core."""
  __slots__ = ("core", "risc", "pc", "halted", "breakpoint", "watchpoint", "ebreak")

  def __init__(self, core: tuple[int, int], risc: str, pc: int = 0,
               halted: bool = False, breakpoint: bool = False,
               watchpoint: bool = False, ebreak: bool = False):
    self.core = core
    self.risc = risc
    self.pc = pc
    self.halted = halted
    self.breakpoint = breakpoint
    self.watchpoint = watchpoint
    self.ebreak = ebreak

  @property
  def state(self) -> str:
    if self.ebreak:    return "EBREAK"
    if self.breakpoint: return "BREAK"
    if self.watchpoint: return "WATCH"
    if self.halted:    return "HALTED"
    return "RUNNING"

  def __repr__(self):
    return f"({self.core[0]:2d},{self.core[1]:2d}) {self.risc:7s} 0x{self.pc:08x} [{self.state}]"


class MultiCoreDebugger:
  """Fast multi-core debug operations across all worker cores.

  Uses a single TLBWindow, retargeted per core. Each operation
  (scan, halt_all, resume_all) sweeps the full grid.
  """

  def __init__(self, tlb: TLBWindow, cores: list[tuple[int, int]]):
    self.tlb = tlb
    self.cores = cores

  def _target_core(self, core: tuple[int, int]):
    from hw import NocOrdering
    self.tlb.target(core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)

  def _off(self, addr: int) -> int:
    return addr - DEBUG_TLB_BASE

  # -- fast PC scan (non-intrusive, uses debug bus) ------------------------ #

  def scan_pcs(self, riscs: tuple[str, ...] = ALL_RISCS) -> list[CoreStatus]:
    """Read PCs for all cores via debug bus. Non-intrusive, no halting.

    Returns one CoreStatus per (core, risc) pair. Fast: ~1-2ms for all
    118 cores x 5 RISCs (590 reads).
    """
    results = []
    for core in self.cores:
      self._target_core(core)
      for risc in riscs:
        sig = PC_SIGNALS[risc]
        cntl = dbg_bus_cntl(sig["sig_sel"], sig["daisy_sel"], sig["rd_sel"])
        self.tlb.write32(self._off(DBG_BUS_CTRL), cntl)
        raw = self.tlb.read32(self._off(DBG_BUS_RD_DATA))
        pc = raw & sig["mask"]
        # ncrisc top-bit fixup
        if risc == "ncrisc" and pc & 0xF0000000 == 0x70000000:
          pc |= 0x80000000
        results.append(CoreStatus(core, risc, pc=pc))
    return results

  def scan_pcs_compact(self, riscs: tuple[str, ...] = ALL_RISCS) -> dict[tuple[int, int], dict[str, int]]:
    """Scan all PCs, return as {core: {risc: pc}}."""
    out: dict[tuple[int, int], dict[str, int]] = {}
    for st in self.scan_pcs(riscs):
      out.setdefault(st.core, {})[st.risc] = st.pc
    return out

  # -- snapshot (halt all, read status + PCs, optionally resume) ----------- #

  def snapshot(self, riscs: tuple[str, ...] = DEBUGGABLE_RISCS) -> list[CoreStatus]:
    """Halt all debuggable RISCs, read status + PC for each. Does NOT resume.

    Call resume_all() when done inspecting.
    NCRISC is included in results (PC via debug bus) but not halted.
    """
    # phase 1: send halt command to all debuggable RISCs on all cores
    for core in self.cores:
      self._target_core(core)
      for risc in riscs:
        if risc == "ncrisc":
          continue
        cntl0_write = 0x80010000 | (RISC_SEL[risc] << 17)
        self.tlb.write32(self._off(RISC_DBG_CNTL_1), CMD_DEBUG_MODE | CMD_HALT)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_write | DR_COMMAND)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)

    # phase 2: wait briefly for all to halt
    time.sleep(0.001)

    # phase 3: read status and PCs
    results = []
    for core in self.cores:
      self._target_core(core)
      for risc in riscs:
        if risc == "ncrisc":
          # read PC via debug bus only
          sig = PC_SIGNALS["ncrisc"]
          cntl = dbg_bus_cntl(sig["sig_sel"], sig["daisy_sel"], sig["rd_sel"])
          self.tlb.write32(self._off(DBG_BUS_CTRL), cntl)
          raw = self.tlb.read32(self._off(DBG_BUS_RD_DATA))
          pc = raw & sig["mask"]
          if pc & 0xF0000000 == 0x70000000:
            pc |= 0x80000000
          results.append(CoreStatus(core, "ncrisc", pc=pc))
          continue

        # read DR(0) = status
        cntl0_read = 0x80000000 | (RISC_SEL[risc] << 17)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_read | DR_STATUS)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)
        # brief wait for read valid
        for _ in range(100):
          s0 = self.tlb.read32(self._off(RISC_DBG_STATUS_0))
          if s0 & STATUS_0_READ_VALID:
            break
        status = self.tlb.read32(self._off(RISC_DBG_STATUS_1))

        # read PC via debug bus (faster than DR protocol for PC)
        sig = PC_SIGNALS[risc]
        cntl = dbg_bus_cntl(sig["sig_sel"], sig["daisy_sel"], sig["rd_sel"])
        self.tlb.write32(self._off(DBG_BUS_CTRL), cntl)
        pc = self.tlb.read32(self._off(DBG_BUS_RD_DATA)) & sig["mask"]

        results.append(CoreStatus(
          core, risc, pc=pc,
          halted=bool(status & STATUS_HALTED),
          breakpoint=bool(status & STATUS_PC_WATCHPOINT_HIT),
          watchpoint=bool(status & STATUS_MEM_WATCHPOINT_HIT),
          ebreak=bool(status & STATUS_EBREAK_HIT),
        ))

    return results

  # -- bulk halt / resume -------------------------------------------------- #

  def halt_all(self, riscs: tuple[str, ...] = DEBUGGABLE_RISCS):
    """Halt all debuggable RISCs on all cores."""
    for core in self.cores:
      self._target_core(core)
      for risc in riscs:
        if risc == "ncrisc":
          continue
        cntl0_write = 0x80010000 | (RISC_SEL[risc] << 17)
        self.tlb.write32(self._off(RISC_DBG_CNTL_1), CMD_DEBUG_MODE | CMD_HALT)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_write | DR_COMMAND)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)

  def resume_all(self, riscs: tuple[str, ...] = DEBUGGABLE_RISCS):
    """Resume all debuggable RISCs on all cores."""
    for core in self.cores:
      self._target_core(core)
      for risc in riscs:
        if risc == "ncrisc":
          continue
        cntl0_write = 0x80010000 | (RISC_SEL[risc] << 17)
        self.tlb.write32(self._off(RISC_DBG_CNTL_1), CMD_DEBUG_MODE | CMD_CONTINUE)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_write | DR_COMMAND)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)

  # -- set breakpoint on all cores ----------------------------------------- #

  def set_breakpoint_all(self, risc: str, index: int, pc_addr: int):
    """Set a PC breakpoint on every core for the given RISC.

    Useful for breaking at kernel entry on whichever core gets there first.
    """
    if risc not in RISC_SEL:
      raise ValueError(f"cannot set breakpoint on {risc}")
    from debug.regs import DR_WATCHPOINT_BASE, DR_WATCHPOINT_SETTINGS, WP_PC_BREAK
    for core in self.cores:
      self._target_core(core)
      rid = RISC_SEL[risc]
      cntl0_write = 0x80010000 | (rid << 17)

      # write DR(10+index) = pc_addr
      self.tlb.write32(self._off(RISC_DBG_CNTL_1), pc_addr)
      self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_write | (DR_WATCHPOINT_BASE + index))
      self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)

      # read current DR(5) settings
      cntl0_read = 0x80000000 | (rid << 17)
      self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_read | DR_WATCHPOINT_SETTINGS)
      self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)
      for _ in range(100):
        if self.tlb.read32(self._off(RISC_DBG_STATUS_0)) & STATUS_0_READ_VALID:
          break
      settings = self.tlb.read32(self._off(RISC_DBG_STATUS_1))

      # update mode for this watchpoint index
      shift = index * 4
      settings = (settings & ~(0xF << shift)) | (WP_PC_BREAK << shift)
      self.tlb.write32(self._off(RISC_DBG_CNTL_1), settings)
      self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_write | DR_WATCHPOINT_SETTINGS)
      self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)

  def clear_breakpoints_all(self):
    """Clear all breakpoints on all cores."""
    from debug.regs import DR_WATCHPOINT_SETTINGS, DR_WATCHPOINT_BASE
    for core in self.cores:
      self._target_core(core)
      for risc in DEBUGGABLE_RISCS:
        rid = RISC_SEL[risc]
        cntl0_write = 0x80010000 | (rid << 17)
        # zero DR(5)
        self.tlb.write32(self._off(RISC_DBG_CNTL_1), 0)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_write | DR_WATCHPOINT_SETTINGS)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)

  # -- wait for any core to hit breakpoint --------------------------------- #

  def wait_breakpoint(self, risc: str, timeout: float = 30.0) -> CoreStatus | None:
    """Poll all cores until one hits a breakpoint on the given RISC.

    Returns the CoreStatus of the first core that hit, or None on timeout.
    Non-intrusive: reads status via DR protocol without halting.
    """
    if risc not in RISC_SEL:
      raise ValueError(f"cannot poll {risc}")
    rid = RISC_SEL[risc]
    cntl0_read = 0x80000000 | (rid << 17)
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
      for core in self.cores:
        self._target_core(core)
        # read DR(0) status
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), cntl0_read | DR_STATUS)
        self.tlb.write32(self._off(RISC_DBG_CNTL_0), 0)
        for _ in range(50):
          if self.tlb.read32(self._off(RISC_DBG_STATUS_0)) & STATUS_0_READ_VALID:
            break
        status = self.tlb.read32(self._off(RISC_DBG_STATUS_1))

        if status & STATUS_HALTED:
          # read PC
          sig = PC_SIGNALS[risc]
          cntl = dbg_bus_cntl(sig["sig_sel"], sig["daisy_sel"], sig["rd_sel"])
          self.tlb.write32(self._off(DBG_BUS_CTRL), cntl)
          pc = self.tlb.read32(self._off(DBG_BUS_RD_DATA)) & sig["mask"]
          return CoreStatus(
            core, risc, pc=pc, halted=True,
            breakpoint=bool(status & STATUS_PC_WATCHPOINT_HIT),
            watchpoint=bool(status & STATUS_MEM_WATCHPOINT_HIT),
            ebreak=bool(status & STATUS_EBREAK_HIT),
          )
      time.sleep(0.0005)  # 500us between sweeps

    return None


def format_scan(statuses: list[CoreStatus], elfs=None) -> str:
  """Format scan results for display.

  Groups by core, one line per core showing all RISC PCs.
  """
  from debug.source import ElfStore
  by_core: dict[tuple[int, int], list[CoreStatus]] = {}
  for st in statuses:
    by_core.setdefault(st.core, []).append(st)

  lines = []
  for core in sorted(by_core):
    riscs = by_core[core]
    parts = []
    state = "RUNNING"
    for st in riscs:
      if st.risc == "ncrisc":
        parts.append(f"nc=0x{st.pc:05x}")
      else:
        short = st.risc[0] + st.risc[-1]  # b=brisc, t0/t1/t2
        parts.append(f"{short}=0x{st.pc:05x}")
      if st.state != "RUNNING":
        state = st.state
    line = f"  ({core[0]:2d},{core[1]:2d}) {' '.join(parts)}  [{state}]"
    lines.append(line)
  return "\n".join(lines)


def format_snapshot(statuses: list[CoreStatus], elfs=None) -> str:
  """Format snapshot results with per-RISC detail."""
  by_core: dict[tuple[int, int], list[CoreStatus]] = {}
  for st in statuses:
    by_core.setdefault(st.core, []).append(st)

  lines = []
  for core in sorted(by_core):
    riscs = by_core[core]
    core_states = [st.state for st in riscs]
    summary = "HALTED" if all(s in ("HALTED", "BREAK", "WATCH", "EBREAK") for s in core_states) else "MIXED"
    lines.append(f"  ({core[0]:2d},{core[1]:2d}) [{summary}]")
    for st in riscs:
      loc = ""
      if elfs and st.risc in elfs.elfs:
        loc = f"  {elfs.resolve(st.risc, st.pc)}"
      lines.append(f"    {st.risc:7s} 0x{st.pc:08x} [{st.state:7s}]{loc}")
  return "\n".join(lines)
