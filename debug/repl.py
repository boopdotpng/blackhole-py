# debug/repl.py - Interactive command-line debugger for Blackhole Tensix cores
#
# Usage (standalone):
#   from debug.repl import DebugSession
#   sess = DebugSession(fd, core=(3, 4))
#   sess.repl()
#
# Usage (from device.run() with DEBUG=1):
#   The device integration will call sess.attach_breakpoints() before dispatch
#   and sess.repl() after the breakpoint hits.

from __future__ import annotations
import cmd, sys, struct, traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from hw import TLBWindow, Core

from debug.core import TileDebugger, RiscDebug
from debug.inspect import TileInspector
from debug.source import ElfStore, ElfInfo
from debug.multi import MultiCoreDebugger, format_scan, format_snapshot
from debug.regs import GPR_NAMES, GPR_COUNT


class DebugSession:
  """Manages state for a debug session on one or more cores."""

  def __init__(self, fd: int, cores: list[tuple[int, int]] | None = None,
               core: tuple[int, int] | None = None):
    from hw import TLBWindow
    if core is not None and cores is None:
      cores = [core]
    if not cores:
      raise ValueError("must specify at least one core")
    self.fd = fd
    self.cores = cores
    self.current_core = cores[0]
    self.current_risc = "trisc1"  # default to math core (most interesting)
    # one TLB shared for debug (re-targeted as needed)
    self._tlb = TLBWindow(fd, self.current_core)
    self.debugger = TileDebugger(self._tlb, self.current_core)
    self.inspector = TileInspector(self._tlb, self.current_core)
    self.multi = MultiCoreDebugger(self._tlb, self.cores)
    self.elfs = ElfStore()

  def switch_core(self, core: tuple[int, int]):
    """Switch to debugging a different core."""
    if core not in self.cores:
      raise ValueError(f"core {core} not in session cores {self.cores}")
    self.current_core = core
    self.debugger = TileDebugger(self._tlb, core)
    self.inspector = TileInspector(self._tlb, core)

  def switch_risc(self, risc: str):
    """Switch focus to a different RISC on the current core."""
    valid = ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc")
    if risc not in valid:
      raise ValueError(f"risc must be one of {valid}")
    self.current_risc = risc

  def add_elf(self, risc: str, elf_bytes: bytes):
    """Register an ELF for source-level debugging."""
    self.elfs.add(risc, elf_bytes)

  def close(self):
    self.elfs.close()
    self._tlb.close()

  def repl(self):
    """Enter the interactive debugger REPL."""
    DebugREPL(self).cmdloop()


class DebugREPL(cmd.Cmd):
  """Interactive debugger command processor."""

  intro = (
    "\n"
    "  Blackhole RISC-V Debugger\n"
    "  Type 'help' for commands, 'quit' to exit.\n"
  )

  def __init__(self, session: DebugSession):
    super().__init__()
    self.session = session
    self._update_prompt()

  def _update_prompt(self):
    s = self.session
    x, y = s.current_core
    self.prompt = f"(dbg {s.current_risc}@{x},{y}) "

  def _dbg(self) -> TileDebugger:
    return self.session.debugger

  def _insp(self) -> TileInspector:
    return self.session.inspector

  def _elf(self) -> ElfInfo | None:
    return self.session.elfs.get(self.session.current_risc)

  # -- execution control --------------------------------------------------- #

  def do_halt(self, arg):
    """Halt all debuggable RISCs on the current core."""
    self._dbg().halt_all()
    print("  all cores halted")
    self._show_status()

  def do_step(self, arg):
    """Single-step the current RISC [or: step <risc>]."""
    risc = arg.strip() or self.session.current_risc
    if risc == "ncrisc":
      print("  error: ncrisc has no debug hardware (cannot step)")
      return
    try:
      self._dbg().step(risc)
    except RuntimeError as e:
      print(f"  error: {e}")
      return
    self._show_location(risc)

  def do_s(self, arg):
    """Alias for step."""
    self.do_step(arg)

  def do_cont(self, arg):
    """Resume all RISCs on the current core."""
    self._dbg().resume_all()
    print("  resumed")

  def do_c(self, arg):
    """Alias for cont."""
    self.do_cont(arg)

  def do_status(self, arg):
    """Show halt/running status of all RISCs."""
    self._show_status()

  def do_st(self, arg):
    """Alias for status."""
    self.do_status(arg)

  # -- register inspection ------------------------------------------------- #

  def do_regs(self, arg):
    """Show all GPRs for the current RISC [or: regs <risc>]."""
    risc = arg.strip() or self.session.current_risc
    if risc == "ncrisc":
      print("  error: ncrisc has no debug hardware (cannot read GPRs)")
      return
    try:
      gprs = self._dbg().read_gprs(risc)
    except RuntimeError as e:
      print(f"  error: {e}")
      return
    print(f"  {risc} registers:")
    for i in range(0, GPR_COUNT, 4):
      parts = []
      for j in range(4):
        if i + j < GPR_COUNT:
          name = GPR_NAMES[i + j]
          val = gprs[name]
          parts.append(f"{name:4s}=0x{val:08x}")
      print(f"    {' '.join(parts)}")
    print(f"    {'pc':4s}=0x{gprs['pc']:08x}")

  def do_pc(self, arg):
    """Show PC for all RISCs (non-intrusive via debug bus)."""
    pcs = self._dbg().read_all_pcs()
    for risc, pc in pcs.items():
      loc = self.session.elfs.resolve(risc, pc)
      marker = " *" if risc == self.session.current_risc else ""
      print(f"  {risc:7s} 0x{pc:08x}  {loc}{marker}")

  # -- source / disassembly ------------------------------------------------ #

  def do_where(self, arg):
    """Show source + disassembly at current PC [or: where <risc>]."""
    risc = arg.strip() or self.session.current_risc
    pc = self._dbg().read_pc(risc)
    elf = self.session.elfs.get(risc)
    if elf:
      print(elf.format_location(pc))
    else:
      print(f"  {risc} pc=0x{pc:08x} (no ELF loaded)")

  def do_w(self, arg):
    """Alias for where."""
    self.do_where(arg)

  def do_list(self, arg):
    """List source around current PC [or: list <risc>]."""
    risc = arg.strip() or self.session.current_risc
    pc = self._dbg().read_pc(risc)
    elf = self.session.elfs.get(risc)
    if not elf:
      print(f"  no ELF for {risc}")
      return
    filepath, lineno, func = elf.addr2line(pc)
    src = elf.get_source_context(filepath, lineno, context=10)
    if not src:
      print(f"  no source for 0x{pc:08x}")
      return
    print(f"  {func}() at {filepath}:{lineno}")
    for ln, text, current in src:
      marker = ">" if current else " "
      print(f"  {marker} {ln:4d} | {text}")

  def do_disasm(self, arg):
    """Show disassembly around current PC [or: disasm <risc>]."""
    risc = arg.strip() or self.session.current_risc
    pc = self._dbg().read_pc(risc)
    elf = self.session.elfs.get(risc)
    if not elf:
      print(f"  no ELF for {risc}")
      return
    disasm = elf.disasm_at(pc, context=10)
    for addr, asm, current in disasm:
      marker = ">" if current else " "
      print(f"  {marker} 0x{addr:06x}: {asm}")

  # -- memory inspection --------------------------------------------------- #

  def do_l1(self, arg):
    """Dump L1 memory: l1 <addr> [count]  (hex, default 64 bytes)."""
    parts = arg.strip().split()
    if not parts:
      print("  usage: l1 <addr> [count]")
      return
    try:
      addr = int(parts[0], 0)
      count = int(parts[1], 0) if len(parts) > 1 else 64
    except ValueError:
      print("  usage: l1 <hex_addr> [count]")
      return
    try:
      print(self._insp().dump_l1(addr, count))
    except Exception as e:
      print(f"  error: {e}")

  def do_read(self, arg):
    """Read a word from a core's address space: read <addr>  (requires halt)."""
    parts = arg.strip().split()
    if not parts:
      print("  usage: read <addr>")
      return
    risc = self.session.current_risc
    if risc == "ncrisc":
      print("  error: ncrisc has no debug hardware")
      return
    try:
      addr = int(parts[0], 0)
      rd = self._dbg()._select(risc)
      val = rd.read_memory(addr)
      print(f"  [{risc}] 0x{addr:08x} = 0x{val:08x} ({val})")
    except Exception as e:
      print(f"  error: {e}")

  # -- Tensix compute state ------------------------------------------------ #

  def do_dest(self, arg):
    """Dump dest register tile: dest [tile]  (default tile 0)."""
    tile = 0
    if arg.strip():
      try:
        tile = int(arg.strip(), 0)
      except ValueError:
        print("  usage: dest [tile_index]")
        return
    try:
      print(self._insp().dump_dest_summary(tile))
    except Exception as e:
      print(f"  error: {e}")

  def do_srca(self, arg):
    """Dump SrcA register: srca [num_rows] (requires math halted, uses injection)."""
    num_rows = 4
    if arg.strip():
      try:
        num_rows = int(arg.strip(), 0)
      except ValueError:
        print("  usage: srca [num_rows]")
        return
    try:
      print(self._insp().dump_srca(num_rows=num_rows))
    except Exception as e:
      print(f"  error: {e}")

  def do_srcb(self, arg):
    """Dump SrcB register: srcb [bank] [num_rows]  (bank 0 or 1)."""
    bank, num_rows = 0, 4
    parts = arg.strip().split()
    try:
      if len(parts) >= 1:
        bank = int(parts[0], 0)
      if len(parts) >= 2:
        num_rows = int(parts[1], 0)
    except ValueError:
      print("  usage: srcb [bank] [num_rows]")
      return
    try:
      print(self._insp().dump_srcb(bank=bank, num_rows=num_rows))
    except Exception as e:
      print(f"  error: {e}")

  def do_lregs(self, arg):
    """Dump SFPU LRegs (requires math core halted)."""
    try:
      print(self._insp().dump_lregs())
    except Exception as e:
      print(f"  error: {e}")

  def do_lreg(self, arg):
    """Dump a single LReg: lreg <index>  (all 32 lanes)."""
    if not arg.strip():
      print("  usage: lreg <index>")
      return
    try:
      idx = int(arg.strip(), 0)
      lanes = self._insp().read_lreg(idx)
      print(f"  LR{idx} (32 lanes):")
      for i in range(0, 32, 8):
        vals = " ".join(f"{v:10.6f}" for v in lanes[i:i+8])
        print(f"    [{i:2d}-{i+7:2d}]: {vals}")
    except Exception as e:
      print(f"  error: {e}")

  def do_cfg(self, arg):
    """Read a CFG register: cfg <index>."""
    if not arg.strip():
      print("  usage: cfg <index>")
      return
    try:
      idx = int(arg.strip(), 0)
      val = self._insp().read_cfg(idx)
      print(f"  CFG[{idx}] = 0x{val:08x} ({val})")
    except Exception as e:
      print(f"  error: {e}")

  def do_clock(self, arg):
    """Read the tile wall clock (64-bit cycle counter)."""
    try:
      clk = self._dbg().read_wall_clock()
      print(f"  wall clock: {clk} cycles (0x{clk:016x})")
    except Exception as e:
      print(f"  error: {e}")

  def do_fpu(self, arg):
    """Read FPU sticky bits (NaN/Inf/denorm flags)."""
    try:
      bits = self._insp().read_fpu_sticky_bits()
      print(f"  FPU sticky bits: 0x{bits:08x}")
    except Exception as e:
      print(f"  error: {e}")

  # -- breakpoints --------------------------------------------------------- #

  def do_break(self, arg):
    """Set breakpoint: break <addr> [index]  (default index 0)."""
    parts = arg.strip().split()
    if not parts:
      print("  usage: break <addr> [index]")
      return
    risc = self.session.current_risc
    if risc == "ncrisc":
      print("  error: ncrisc has no debug hardware")
      return
    try:
      addr = int(parts[0], 0)
      idx = int(parts[1], 0) if len(parts) > 1 else 0
      self._dbg().set_breakpoint(risc, idx, addr)
      print(f"  breakpoint {idx} set at 0x{addr:08x} on {risc}")
    except Exception as e:
      print(f"  error: {e}")

  def do_b(self, arg):
    """Alias for break."""
    self.do_break(arg)

  def do_watch(self, arg):
    """Set memory watchpoint: watch <addr> [r|w|rw] [index]."""
    parts = arg.strip().split()
    if not parts:
      print("  usage: watch <addr> [r|w|rw] [index]")
      return
    risc = self.session.current_risc
    if risc == "ncrisc":
      print("  error: ncrisc has no debug hardware")
      return
    try:
      addr = int(parts[0], 0)
      mode = parts[1] if len(parts) > 1 else "rw"
      idx = int(parts[2], 0) if len(parts) > 2 else 0
      self._dbg()._select(risc).set_watchpoint(idx, addr, mode)
      print(f"  watchpoint {idx} ({mode}) at 0x{addr:08x} on {risc}")
    except Exception as e:
      print(f"  error: {e}")

  def do_clearbreak(self, arg):
    """Clear breakpoint: clearbreak [index | all]."""
    risc = self.session.current_risc
    if risc == "ncrisc":
      print("  error: ncrisc has no debug hardware")
      return
    if arg.strip() == "all":
      self._dbg().clear_all_breakpoints()
      print("  all breakpoints cleared")
      return
    try:
      idx = int(arg.strip(), 0) if arg.strip() else 0
      self._dbg().clear_breakpoint(risc, idx)
      print(f"  breakpoint {idx} cleared on {risc}")
    except Exception as e:
      print(f"  error: {e}")

  # -- core/risc selection ------------------------------------------------- #

  def do_core(self, arg):
    """Switch core: core <x>,<y>  or list available cores."""
    if not arg.strip():
      for c in self.session.cores:
        marker = " *" if c == self.session.current_core else ""
        print(f"  ({c[0]},{c[1]}){marker}")
      return
    try:
      parts = arg.strip().replace(" ", "").split(",")
      core = (int(parts[0]), int(parts[1]))
      self.session.switch_core(core)
      print(f"  switched to core ({core[0]},{core[1]})")
      self._update_prompt()
    except Exception as e:
      print(f"  error: {e}")

  def do_risc(self, arg):
    """Switch RISC: risc <name>  (brisc/trisc0/trisc1/trisc2/ncrisc)."""
    if not arg.strip():
      for r in ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc"):
        marker = " *" if r == self.session.current_risc else ""
        hw = "" if r != "ncrisc" else " (no debug hw)"
        print(f"  {r}{marker}{hw}")
      return
    try:
      self.session.switch_risc(arg.strip())
      self._update_prompt()
    except Exception as e:
      print(f"  error: {e}")

  # -- multi-core operations ------------------------------------------------ #

  def do_scan(self, arg):
    """Scan all cores' PCs via debug bus (non-intrusive, fast).

    Shows one line per core with all RISC PCs. Optional: scan <risc>
    to only scan one RISC type (faster).
    """
    riscs = ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc")
    if arg.strip() and arg.strip() in riscs:
      riscs = (arg.strip(),)
    try:
      t0 = __import__("time").monotonic()
      statuses = self.session.multi.scan_pcs(riscs)
      dt = __import__("time").monotonic() - t0
      print(format_scan(statuses, self.session.elfs))
      print(f"  ({len(statuses)} reads in {dt*1000:.1f}ms)")
    except Exception as e:
      print(f"  error: {e}")

  def do_snapshot(self, arg):
    """Halt ALL cores, read status + PCs, show full state.

    Does NOT auto-resume. Use 'resume-all' when done.
    """
    try:
      t0 = __import__("time").monotonic()
      # include ncrisc in results
      riscs = ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc")
      statuses = self.session.multi.snapshot(riscs)
      dt = __import__("time").monotonic() - t0
      print(format_snapshot(statuses, self.session.elfs))
      n_cores = len(self.session.cores)
      print(f"  ({n_cores} cores halted + scanned in {dt*1000:.1f}ms)")
      print(f"  use 'resume-all' to continue execution")
    except Exception as e:
      print(f"  error: {e}")

  def do_haltall(self, arg):
    """Halt all debuggable RISCs on ALL cores."""
    self.session.multi.halt_all()
    print(f"  halted all {len(self.session.cores)} cores")

  def do_resumeall(self, arg):
    """Resume all debuggable RISCs on ALL cores."""
    self.session.multi.resume_all()
    print(f"  resumed all {len(self.session.cores)} cores")

  def do_breakall(self, arg):
    """Set a breakpoint on ALL cores: breakall <addr> [index].

    Sets the breakpoint for the currently selected RISC on every core.
    Useful for catching kernel entry on whichever core runs first.
    """
    parts = arg.strip().split()
    if not parts:
      print("  usage: breakall <addr> [index]")
      return
    risc = self.session.current_risc
    if risc == "ncrisc":
      print("  error: ncrisc has no debug hardware")
      return
    try:
      addr = int(parts[0], 0)
      idx = int(parts[1], 0) if len(parts) > 1 else 0
      self.session.multi.set_breakpoint_all(risc, idx, addr)
      print(f"  breakpoint {idx} at 0x{addr:08x} set on {risc} across {len(self.session.cores)} cores")
    except Exception as e:
      print(f"  error: {e}")

  def do_clearall(self, arg):
    """Clear all breakpoints on ALL cores."""
    self.session.multi.clear_breakpoints_all()
    print(f"  all breakpoints cleared on {len(self.session.cores)} cores")

  def do_waitbreak(self, arg):
    """Wait for any core to hit a breakpoint: waitbreak [timeout_secs].

    Polls all cores until one halts. Switches focus to that core.
    """
    timeout = 30.0
    if arg.strip():
      try:
        timeout = float(arg.strip())
      except ValueError:
        print("  usage: waitbreak [timeout_secs]")
        return
    risc = self.session.current_risc
    if risc == "ncrisc":
      print("  error: ncrisc has no debug hardware")
      return
    print(f"  waiting for {risc} breakpoint hit (timeout {timeout}s)...")
    try:
      st = self.session.multi.wait_breakpoint(risc, timeout)
      if st is None:
        print("  timeout: no breakpoint hit")
        return
      print(f"  hit on core ({st.core[0]},{st.core[1]}) at 0x{st.pc:08x} [{st.state}]")
      self.session.switch_core(st.core)
      self._update_prompt()
      self._show_location(risc)
    except Exception as e:
      print(f"  error: {e}")

  # -- utilities ----------------------------------------------------------- #

  def do_quit(self, arg):
    """Exit the debugger."""
    print("  exiting debugger")
    return True

  def do_q(self, arg):
    """Alias for quit."""
    return self.do_quit(arg)

  def do_EOF(self, arg):
    """Handle Ctrl-D."""
    print()
    return self.do_quit(arg)

  def default(self, line):
    """Handle unknown commands."""
    print(f"  unknown command: {line}")
    print("  type 'help' for available commands")

  def emptyline(self):
    """Repeat last command on empty line (like GDB)."""
    if self.lastcmd:
      return self.onecmd(self.lastcmd)

  # -- helpers ------------------------------------------------------------- #

  def _show_status(self):
    for risc in ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc"):
      print(f"  {self._dbg().status_str(risc)}")

  def _show_location(self, risc: str):
    pc = self._dbg().read_pc(risc)
    loc = self.session.elfs.resolve(risc, pc)
    elf = self.session.elfs.get(risc)
    print(f"  {risc} pc=0x{pc:08x}  {loc}")
    if elf:
      filepath, lineno, func = elf.addr2line(pc)
      src = elf.get_source_context(filepath, lineno, context=3)
      for ln, text, current in src:
        marker = ">" if current else " "
        print(f"  {marker} {ln:4d} | {text}")
