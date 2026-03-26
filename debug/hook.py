"""DEBUG=1 integration for the Blackhole debugger session."""

from __future__ import annotations

import os
import time

from compiler import iter_pt_load
from debug.risc import RiscDebug
from debug.server import serve as serve_debug_api
from debug.session import DebugSession
from debug.symbols import resolve_entry_address, resolve_source_location
from dispatch import DevMsgs, GoMsg, Launch, LaunchMsg, Write, _KernelConfigMsg, mcast_rects
from hw import TLBWindow, TensixL1

_TARGET_RISC = "trisc1"
_TARGET_CORE_INDEX = int(os.environ.get("DEBUG_CORE_INDEX", "0"))
_BREAKPOINT_INDEX = 0
_WAIT_TIMEOUT = 10.0


def _write_phase(win: TLBWindow, ir_commands) -> list[tuple[int, int]]:
  launch_cores: list[tuple[int, int]] | None = None
  for cmd in ir_commands:
    match cmd:
      case Write(cores=cores, addr=addr, data=data) if isinstance(data, list):
        for core, blob in zip(cores, data):
          win.target(core)
          win.write(addr, blob)
      case Write(cores=cores, addr=addr, data=data):
        for x0, x1, y0, y1 in mcast_rects(cores):
          win.target((x0, y0), (x1, y1))
          win.write(addr, data)
      case Launch(cores=cores):
        launch_cores = list(cores)
  return launch_cores or []


def _send_go(win: TLBWindow, cores: list[tuple[int, int]]):
  go = GoMsg()
  go.bits.signal = DevMsgs.RUN_MSG_GO
  go_blob = int(go.all).to_bytes(4, "little")
  for x0, x1, y0, y1 in mcast_rects(cores):
    win.target((x0, y0), (x1, y1))
    win.mm[TensixL1.GO_MSG:TensixL1.GO_MSG + 4] = go_blob


def _launch_kernel_text_offset_offset() -> int:
  return LaunchMsg.kernel_config.offset + _KernelConfigMsg.kernel_text_offset.offset


def _read_launch_kernel_text_offset(win: TLBWindow, core: tuple[int, int], processor_index: int) -> int:
  win.target(core)
  offset = _launch_kernel_text_offset_offset() + processor_index * 4
  return win.read32(TensixL1.LAUNCH + offset)


def _elf_text_base(elf_bytes: bytes) -> int:
  text_segments = [segment for segment in iter_pt_load(elf_bytes) if segment.flags & 1]
  if not text_segments:
    raise RuntimeError("no executable PT_LOAD segment found in debug ELF")
  return text_segments[0].paddr


def _wait_breakpoint(debugger: RiscDebug, timeout: float) -> int:
  deadline = time.monotonic() + timeout
  while True:
    status = debugger.read_status()
    if status & 0x1:
      return status
    if time.monotonic() > deadline:
      raise TimeoutError(f"timeout waiting for {_TARGET_RISC} breakpoint on core {debugger.core}")
    time.sleep(0.0001)


def _read_halt_pc(debugger: RiscDebug) -> int | None:
  try:
    return debugger.read_pc()
  except Exception as exc:
    print(f"  debug: DR PC read failed: {exc}")
    return None


def _wait_completion(win: TLBWindow, cores: list[tuple[int, int]], timeout: float = 10.0):
  for core in cores:
    win.target(core)
    deadline = time.monotonic() + timeout
    while win.mm[TensixL1.GO_MSG + 3] != DevMsgs.RUN_MSG_DONE:
      if time.monotonic() > deadline:
        raise TimeoutError(f"timeout waiting for core ({core[0]},{core[1]}) to finish")
      time.sleep(0.001)


def _clear_pause_flags(win: TLBWindow, cores: list[tuple[int, int]]):
  for core in cores:
    win.target(core)
    win.write32(TensixL1.DEBUG_PAUSE_FLAG, 0)


def _launch_frontend(session: DebugSession):
  port = int(os.environ.get("DEBUG_SERVER_PORT", "0"))
  serve_debug_api(session, port=port)


def debug_dispatch(device, ir_commands, program=None, writer=None, reader=None, compute=None):
  if compute is None or len(compute) < 2 or compute[1] is None or compute[1].elf_bytes is None:
    raise RuntimeError("DEBUG=1 trisc1 debugging requires a compute kernel ELF with debug info")

  launch_probe_core = device.cores[0]
  target_core = device.cores[_TARGET_CORE_INDEX]
  trisc1_elf = compute[1].elf_bytes
  elf_entry, symbol_name = resolve_entry_address(trisc1_elf, _TARGET_RISC)
  elf_text_base = _elf_text_base(trisc1_elf)
  entry_offset = elf_entry - elf_text_base

  print(f"  debug: target core ({target_core[0]},{target_core[1]}) {_TARGET_RISC}")
  print(f"  debug: resolved {symbol_name} at ELF 0x{elf_entry:08x} (text+0x{entry_offset:x})")

  with TLBWindow(device.fd, start=launch_probe_core) as win:
    launch_cores = _write_phase(win, ir_commands)
    if not launch_cores:
      raise RuntimeError("debug dispatch did not find a Launch command")
    if target_core not in launch_cores:
      raise RuntimeError(
        f"default debug core ({target_core[0]},{target_core[1]}) is not part of this launch"
      )

    runtime_text_offset = _read_launch_kernel_text_offset(win, target_core, 3)
    if runtime_text_offset == 0:
      raise RuntimeError(f"no runtime text offset for {_TARGET_RISC} on core {target_core}")
    runtime_text_base = TensixL1.KERNEL_CONFIG_BASE + runtime_text_offset
    runtime_entry = runtime_text_base + entry_offset
    print(
      f"  debug: {_TARGET_RISC} runtime text base 0x{runtime_text_base:06x}, "
      f"breakpoint at 0x{runtime_entry:06x}"
    )

    debugger = RiscDebug(win, target_core, _TARGET_RISC)

    auto_offset = os.environ.get("DEBUG_BREAK_OFFSET")
    if auto_offset is not None:
      initial_break = runtime_text_base + int(auto_offset, 0)
      elf_target = elf_text_base + int(auto_offset, 0)
      loc = resolve_source_location(trisc1_elf, elf_target)
      print(f"  debug: using DEBUG_BREAK_OFFSET=0x{int(auto_offset, 0):x} as initial breakpoint")
      print(f"  debug: target: {loc.function} @ {loc.file}:{loc.line}")
    else:
      initial_break = runtime_entry

    debugger.set_pc_breakpoint(_BREAKPOINT_INDEX, initial_break)
    print(f"  debug: armed breakpoint at 0x{initial_break:06x} on {_TARGET_RISC}")

    _clear_pause_flags(win, launch_cores)
    print("  debug: cleared DEBUG_PAUSE_FLAG on launch cores")

    _send_go(win, launch_cores)
    print(f"  debug: GO sent, waiting for {_TARGET_RISC} breakpoint...")
    status = _wait_breakpoint(debugger, _WAIT_TIMEOUT)

    dr_pc = _read_halt_pc(debugger)
    print(
      f"  debug: halted {_TARGET_RISC} on core ({target_core[0]},{target_core[1]}) "
      f"status=0x{status:08x}"
    )
    if dr_pc is not None:
      print(f"  debug: DR PC        = 0x{dr_pc:08x}")
    if debugger.is_breakpoint_hit():
      print("  debug: stop reason = PC breakpoint")
    else:
      print("  debug: stop reason = halted (non-breakpoint reason unknown)")
    debugger.clear_breakpoint(_BREAKPOINT_INDEX)

    session = DebugSession(
      win=win,
      debugger=debugger,
      launch_cores=launch_cores,
      target_risc=_TARGET_RISC,
      elf_bytes=trisc1_elf,
      runtime_text_base=runtime_text_base,
      elf_text_base=elf_text_base,
      program=program,
      wait_timeout=_WAIT_TIMEOUT,
      auto_shutdown_on_done=os.environ.get("DEBUG_SERVER") == "1",
    )

    try:
      _launch_frontend(session)
    finally:
      session.cleanup()
      _clear_pause_flags(win, launch_cores)
      _wait_completion(win, launch_cores, timeout=_WAIT_TIMEOUT)
      print("  debug: program completed")
