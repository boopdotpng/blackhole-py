"""Structured debug session state and command execution."""

from __future__ import annotations

import struct
import threading
import time
from pathlib import Path

from compiler import iter_pt_load
from debug.debug_bus import DebugBus
from debug.regs import (
  ARRAY_ID_DEST,
  DBG_ARRAY_RD_CMD,
  DBG_ARRAY_RD_DATA,
  DBG_ARRAY_RD_EN,
  DEBUG_TLB_BASE,
  DEST_BASE,
  DEST_CHUNKS_PER_ROW,
  DEST_FP32_ELEMS_PER_ROW,
  DEST_ROW_BYTES,
  DEST_ROWS_PER_TILE,
  DEST_SIZE,
  DEST_TILE_BYTES_BF16,
)
from debug.risc import RiscDebug
from debug.symbols import resolve_assembly_line, resolve_source_location
from debug.tensix import (
  TensixInjector, is_thread_fifo_empty,
  read_srca_row, read_srcb_row, read_lreg,
)
from debug.tensix_state import TensixStateReader
from hw import NocOrdering, TensixL1


class DebugSession:
  """Stateful debugger session for one target RISC/core."""

  DEBUGGABLE_RISCS = ("brisc", "trisc0", "trisc1", "trisc2")
  TEMP_BREAKPOINT_INDEX = 1

  def __init__(
    self,
    win,
    debugger: RiscDebug,
    launch_cores: list[tuple[int, int]],
    target_risc: str,
    elf_bytes: bytes,
    runtime_text_base: int,
    elf_text_base: int,
    program,
    wait_timeout: float = 10.0,
    auto_shutdown_on_done: bool = False,
  ):
    self.win = win
    self.debugger = debugger
    self.debug_bus = DebugBus(win, debugger.core)
    self.launch_cores = launch_cores
    self.target_risc = target_risc
    self.elf_bytes = elf_bytes
    self.runtime_text_base = runtime_text_base
    self.elf_text_base = elf_text_base
    self.program = program
    self.wait_timeout = wait_timeout
    self.auto_shutdown_on_done = auto_shutdown_on_done
    self._text_segments = [segment for segment in iter_pt_load(elf_bytes) if segment.flags & 1]
    self._lock = threading.RLock()
    self._events_cond = threading.Condition(self._lock)
    self._events: list[dict] = []
    self._next_event_seq = 1
    self._shutdown_requested = False
    self._done_notified = False
    if self.auto_shutdown_on_done:
      self._done_watcher = threading.Thread(target=self._watch_for_program_done, daemon=True)
      self._done_watcher.start()

  def _event(self, kind: str, message: str, data: dict | None = None) -> dict:
    entry = {
      "seq": self._next_event_seq,
      "time": time.time(),
      "kind": kind,
      "message": message,
      "data": data or {},
    }
    self._next_event_seq += 1
    self._events.append(entry)
    self._events_cond.notify_all()
    return entry

  def events_since(self, since: int = 0) -> list[dict]:
    with self._lock:
      return [event for event in self._events if event["seq"] > since]

  def wait_for_events(self, since: int = 0, timeout: float = 1.0) -> list[dict]:
    with self._lock:
      deadline = time.monotonic() + timeout
      while True:
        events = [event for event in self._events if event["seq"] > since]
        if events or self._shutdown_requested:
          return events
        remaining = deadline - time.monotonic()
        if remaining <= 0:
          return []
        self._events_cond.wait(timeout=remaining)

  def request_shutdown(self):
    with self._lock:
      if self._shutdown_requested:
        return
      self._shutdown_requested = True
      self._event("session", "shutdown requested")

  def _watch_for_program_done(self):
    while True:
      with self._lock:
        if self._shutdown_requested:
          return
        done = self._is_program_done()
        if done and not self._done_notified:
          self._done_notified = True
          self._event("session", "program completed")
          self._shutdown_requested = True
          self._events_cond.notify_all()
          return
      time.sleep(0.05)

  def wait_for_shutdown(self, timeout: float | None = None) -> bool:
    with self._lock:
      if self._shutdown_requested:
        return True
      deadline = None if timeout is None else time.monotonic() + timeout
      while not self._shutdown_requested:
        remaining = None if deadline is None else max(0.0, deadline - time.monotonic())
        if deadline is not None and remaining == 0.0:
          return False
        self._events_cond.wait(timeout=remaining)
      return True

  def _runtime_pc_to_elf_pc(self, runtime_pc: int) -> int:
    return self.elf_text_base + (runtime_pc - self.runtime_text_base)

  def _instruction_at_runtime_pc(self, runtime_pc: int) -> int:
    elf_pc = self._runtime_pc_to_elf_pc(runtime_pc)
    for segment in self._text_segments:
      start = segment.paddr
      end = segment.paddr + len(segment.data)
      if start <= elf_pc and elf_pc + 4 <= end:
        offset = elf_pc - start
        return struct.unpack_from("<I", segment.data, offset)[0]
    return self.debugger.read_memory(runtime_pc)

  def _source_lines_for_file(self, file_name: str) -> list[str] | None:
    path = Path(file_name)
    if path.name == "kernel_includes.hpp" and getattr(self.program, "compute_kernel", ""):
      return self.program.compute_kernel.splitlines()
    try:
      return path.read_text().splitlines()
    except OSError:
      return None

  def _source_context(self, file_name: str, line: int | None, context: int = 1) -> list[dict]:
    if line is None or line <= 0:
      return []
    lines = self._source_lines_for_file(file_name)
    if not lines:
      return []
    start = max(1, line - context)
    end = min(len(lines), line + context)
    return [
      {
        "line": lineno,
        "text": lines[lineno - 1].rstrip(),
        "current": lineno == line,
      }
      for lineno in range(start, end + 1)
    ]

  @staticmethod
  def _bf16_to_f32(value: int) -> float:
    bits = (value & 0xFFFF) << 16
    return struct.unpack("<f", struct.pack("<I", bits))[0]

  @staticmethod
  def _word_to_f32(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]

  @staticmethod
  def _dest_bf16_to_float(raw16: int) -> float:
    sign = (raw16 & 0x8000) >> 15
    mantissa = (raw16 & 0x7F00) >> 8
    exponent = raw16 & 0xFF
    standard_bf16 = (sign << 15) | (exponent << 7) | mantissa
    fp32_bits = standard_bf16 << 16
    return struct.unpack(">f", fp32_bits.to_bytes(4, "big"))[0]

  def _read_pause_flag(self, core: tuple[int, int] | None = None) -> int:
    self.win.target(core or self.debugger.core, addr=0, mode=NocOrdering.STRICT)
    return self.win.read32(TensixL1.DEBUG_PAUSE_FLAG)

  def _write_pause_flag(self, value: int, core: tuple[int, int] | None = None):
    self.win.target(core or self.debugger.core, addr=0, mode=NocOrdering.STRICT)
    self.win.write32(TensixL1.DEBUG_PAUSE_FLAG, value)

  def clear_pause_flags(self):
    for core in self.launch_cores:
      self._write_pause_flag(0, core=core)

  def _is_program_done(self) -> bool:
    for core in self.launch_cores:
      self.win.target(core)
      if self.win.mm[TensixL1.GO_MSG + 3] != 0:
        return False
    return True

  def is_program_done(self) -> bool:
    with self._lock:
      return self._is_program_done()

  def _fifo_status_raw(self) -> int:
    from debug.tensix import INSTRN_BUF_STATUS

    self.win.target(self.debugger.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)
    return self.win.read32(INSTRN_BUF_STATUS - DEBUG_TLB_BASE)

  def _fifo_status(self) -> dict:
    status = self._fifo_status_raw()
    threads = {}
    for tid in range(3):
      not_full = bool(status & (1 << tid))
      empty = bool(status & (1 << (4 + tid)))
      threads[str(tid)] = {
        "not_full": not_full,
        "empty": empty,
        "state": "empty" if empty else ("not_full" if not_full else "full"),
      }
    return {
      "raw": f"0x{status:08x}",
      "threads": threads,
    }

  def _approx_pc(self) -> int | None:
    try:
      return self.debug_bus.read_pc(self.target_risc)
    except Exception:
      return None

  def _location_payload(self, runtime_pc: int, exact: bool) -> dict:
    elf_pc = self._runtime_pc_to_elf_pc(runtime_pc)
    location = resolve_source_location(self.elf_bytes, elf_pc)
    asm = resolve_assembly_line(self.elf_bytes, elf_pc)
    return {
      "pc": f"0x{runtime_pc:08x}",
      "pc_value": runtime_pc,
      "exact": exact,
      "function": location.function,
      "file": location.file,
      "line": location.line,
      "asm": None if asm is None else asm.text,
      "source_context": self._source_context(location.file, location.line),
    }

  def snapshot(self) -> dict:
    halted = self.debugger.is_halted()
    done = self._is_program_done()
    pause_flag = self._read_pause_flag()
    mode = "done" if done else ("halted" if halted else ("kernel_paused" if pause_flag == 1 else "running"))
    pc_value = None
    pc_exact = False
    if halted:
      try:
        pc_value = self.debugger.read_pc()
        pc_exact = True
      except Exception:
        pc_value = None
    else:
      pc_value = self._approx_pc()
    return {
      "core": list(self.debugger.core),
      "risc": self.target_risc,
      "mode": mode,
      "program_done": done,
      "risc_halted": halted,
      "kernel_paused": pause_flag == 1,
      "pc": None if pc_value is None else f"0x{pc_value:08x}",
      "pc_value": pc_value,
      "pc_exact": pc_exact,
      "fifo": self._fifo_status(),
    }

  def _require_halted(self, operation: str):
    if not self.debugger.is_halted():
      raise RuntimeError(f"{operation} requires the RISC to be DR-halted")

  def _require_kernel_paused(self, operation: str):
    if self.debugger.is_halted():
      if self._read_pause_flag() == 1:
        # DR-halted inside the pause loop — continue so the coprocessor can drain injected instructions
        self.debugger.cont()
        import time; time.sleep(0.05)  # let RISC re-enter pause loop
        self._event("control", f"auto-continued {self.target_risc} into DEBUG_PAUSE() loop for {operation}")
      else:
        raise RuntimeError(f"{operation} requires the kernel to be in DEBUG_PAUSE(), not DR-halted outside the pause loop")
    if self._read_pause_flag() != 1:
      raise RuntimeError(f"{operation} requires the kernel to be in DEBUG_PAUSE()")

  def status(self) -> dict:
    return self.snapshot()

  def halt_risc(self) -> dict:
    self.debugger.halt()
    pc = self.debugger.read_pc()
    self._event("control", f"halted {self.target_risc}", {"pc": pc})
    return self._location_payload(pc, exact=True)

  def continue_risc(self) -> dict:
    if self._read_pause_flag() == 1:
      raise RuntimeError("continue_risc is blocked while DEBUG_PAUSE() is active; use release_kernel_pause")
    self._require_halted("continue_risc")
    self.debugger.cont()
    self._event("control", f"continued {self.target_risc}")
    return {"continued": True}

  @staticmethod
  def _is_call_instruction(instruction: int) -> bool:
    opcode = instruction & 0x7F
    rd = (instruction >> 7) & 0x1F
    funct3 = (instruction >> 12) & 0x7
    if opcode == 0x6F:
      return rd in (1, 5)
    if opcode == 0x67 and funct3 == 0:
      return rd in (1, 5)
    return False

  def step_risc(self) -> dict:
    self._require_halted("step_risc")
    self.debugger.step()
    if self._is_program_done():
      self._event("control", "program completed during step")
      return {"done": True}
    pc = self.debugger.read_pc()
    self._event("control", f"stepped {self.target_risc}", {"pc": pc})
    return self._location_payload(pc, exact=True)

  def _wait_for_halt_or_completion(self) -> tuple[str, int | None]:
    deadline = time.monotonic() + self.wait_timeout
    while True:
      status = self.debugger.read_status()
      if status & 0x1:
        return "halted", status
      if self._is_program_done():
        return "done", None
      if time.monotonic() > deadline:
        raise TimeoutError(f"timeout waiting for {self.target_risc} to halt or complete")
      time.sleep(0.0001)

  def next_risc(self) -> dict:
    self._require_halted("next_risc")
    current_pc = self.debugger.read_pc()
    instruction = self._instruction_at_runtime_pc(current_pc)
    if not self._is_call_instruction(instruction):
      return self.step_risc()
    return_pc = current_pc + 4
    self.debugger.set_pc_breakpoint(self.TEMP_BREAKPOINT_INDEX, return_pc)
    try:
      self.debugger.cont()
      reason, _ = self._wait_for_halt_or_completion()
    finally:
      self.debugger.clear_breakpoint(self.TEMP_BREAKPOINT_INDEX)
    if reason == "done":
      self._event("control", "program completed during next")
      return {"done": True}
    pc = self.debugger.read_pc()
    self._event("control", f"next completed on {self.target_risc}", {"pc": pc})
    return self._location_payload(pc, exact=True)

  def read_location(self) -> dict:
    halted = self.debugger.is_halted()
    pc = self.debugger.read_pc() if halted else self._approx_pc()
    if pc is None:
      raise RuntimeError("unable to determine program counter")
    return self._location_payload(pc, exact=halted)

  def read_gprs(self) -> dict:
    self._require_halted("read_gprs")
    names = [
      "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
      "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
      "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
      "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6",
    ]
    registers = []
    for index, name in enumerate(names):
      value = self.debugger.read_gpr(index)
      registers.append({
        "index": index,
        "name": name,
        "value": value,
        "hex": f"0x{value:08x}",
      })
    pc = self.debugger.read_pc()
    return {
      "pc": f"0x{pc:08x}",
      "pc_value": pc,
      "registers": registers,
    }

  def read_memory(self, addr: int, count: int = 64) -> dict:
    self._require_halted("read_memory")
    addr &= ~3
    words = self.debugger.read_words(addr, count)
    rows = []
    for i in range(0, count, 4):
      row_addr = addr + i * 4
      row_words = words[i:i + 4]
      ascii_str = ""
      for word in row_words:
        for byte_idx in range(4):
          byte = (word >> (byte_idx * 8)) & 0xFF
          ascii_str += chr(byte) if 0x20 <= byte < 0x7F else "."
      rows.append({
        "address": f"0x{row_addr:08x}",
        "address_value": row_addr,
        "words": [f"0x{word:08x}" for word in row_words],
        "word_values": row_words,
        "ascii": ascii_str,
      })
    return {
      "address": f"0x{addr:08x}",
      "address_value": addr,
      "count": count,
      "rows": rows,
    }

  def run_to_kernel_pause(self, timeout: float = 5.0) -> dict:
    self._write_pause_flag(0)
    if self.debugger.is_halted():
      self.debugger.cont()
    deadline = time.monotonic() + timeout
    while True:
      flag = self._read_pause_flag()
      if flag == 1:
        time.sleep(0.05)
        approx_pc = self._approx_pc()
        self._event("pause", "hit DEBUG_PAUSE()", {"pc": approx_pc})
        result = {
          "hit": True,
          "approx_pc": None if approx_pc is None else f"0x{approx_pc:08x}",
          "approx_pc_value": approx_pc,
          "fifo": self._fifo_status(),
        }
        if approx_pc is not None:
          result["location"] = self._location_payload(approx_pc, exact=False)
        return result
      if self._is_program_done():
        self._event("pause", "program completed before DEBUG_PAUSE()")
        return {"hit": False, "done": True}
      if time.monotonic() > deadline:
        raise TimeoutError(f"timeout ({timeout}s) waiting for DEBUG_PAUSE()")
      time.sleep(0.001)

  def release_kernel_pause(self) -> dict:
    self._write_pause_flag(0)
    self._event("pause", "released DEBUG_PAUSE()")
    return {"released": True}

  def _dbg_array_read_row(self, row: int, bank: int = 0, array_id: int = ARRAY_ID_DEST) -> list[int]:
    self.win.target(self.debugger.core, addr=DEBUG_TLB_BASE, mode=NocOrdering.STRICT)
    off = lambda a: a - DEBUG_TLB_BASE
    self.win.write32(off(DBG_ARRAY_RD_EN), 1)
    chunks = []
    for chunk in range(DEST_CHUNKS_PER_ROW):
      cmd = (bank << 19) | (array_id << 16) | (chunk << 12) | (row & 0xFFF)
      self.win.write32(off(DBG_ARRAY_RD_CMD), cmd)
      chunks.append(self.win.read32(off(DBG_ARRAY_RD_DATA)))
    self.win.write32(off(DBG_ARRAY_RD_EN), 0)
    return chunks

  def _read_dst_words_dr(self, offset_bytes: int, count: int) -> list[int]:
    self._require_halted("read_dest(method='dr')")
    return self.debugger.read_words(DEST_BASE + offset_bytes, count)

  def read_dest(self, tile: int = 0, rows: int = 4, cols: int = 8, method: str = "array") -> dict:
    rows = max(1, min(rows, DEST_ROWS_PER_TILE))
    if method == "dr":
      cols = max(1, min(cols, DEST_FP32_ELEMS_PER_ROW))
      start_row = tile * DEST_ROWS_PER_TILE
      words = self._read_dst_words_dr(start_row * DEST_ROW_BYTES, rows * DEST_CHUNKS_PER_ROW)
      result_rows = []
      idx = 0
      for row in range(rows):
        row_words = words[idx:idx + DEST_CHUNKS_PER_ROW]
        values = [self._word_to_f32(row_words[c]) for c in range(cols)]
        result_rows.append({
          "row": start_row + row,
          "values": values,
          "formatted": " ".join(f"{value:8.4f}" for value in values),
        })
        idx += DEST_CHUNKS_PER_ROW
      return {"tile": tile, "method": "dr", "rows": result_rows}

    tile_count = DEST_SIZE // DEST_TILE_BYTES_BF16
    if not 0 <= tile < tile_count:
      raise ValueError(f"tile must be 0..{tile_count - 1}")
    cols = max(1, min(cols, 16))
    start_row = tile * DEST_ROWS_PER_TILE
    result_rows = []
    for row in range(rows):
      chunks = self._dbg_array_read_row(start_row + row, bank=0, array_id=ARRAY_ID_DEST)
      values = []
      for word in chunks:
        hi16 = (word >> 16) & 0xFFFF
        lo16 = word & 0xFFFF
        values.append(self._dest_bf16_to_float(hi16))
        values.append(self._dest_bf16_to_float(lo16))
      view = values[:cols]
      result_rows.append({
        "row": start_row + row,
        "values": view,
        "formatted": " ".join(f"{value:8.4f}" for value in view),
      })
    return {"tile": tile, "method": "array", "rows": result_rows}

  def _get_injector(self) -> TensixInjector:
    if not hasattr(self, "_injector"):
      self._injector = TensixInjector(self.win, self.debugger.core)
    return self._injector

  def _get_tensix_state_reader(self) -> TensixStateReader:
    if not hasattr(self, "_tensix_state_reader"):
      self._tensix_state_reader = TensixStateReader(self.win, self.debugger)
    return self._tensix_state_reader

  def _read_register_rows(self, read_fn, start_row: int, num_rows: int,
                          thread_id: int, label: str) -> dict:
    """Generic helper: read register rows via injection, format as bf16 floats."""
    self._require_kernel_paused(label)
    start_row = max(0, min(start_row, 63))
    num_rows = max(1, min(num_rows, 64 - start_row))
    if not is_thread_fifo_empty(self.win, self.debugger.core, thread_id):
      raise RuntimeError(f"thread {thread_id} FIFO is not empty; wait longer in DEBUG_PAUSE()")
    injector = self._get_injector()
    rows = []
    for row in range(start_row, start_row + num_rows):
      chunks = read_fn(self.win, self.debugger.core, injector, row, thread_id)
      values = []
      for word in chunks:
        hi16 = (word >> 16) & 0xFFFF
        lo16 = word & 0xFFFF
        values.append(self._dest_bf16_to_float(hi16))
        values.append(self._dest_bf16_to_float(lo16))
      rows.append({
        "row": row,
        "values": values[:16],
        "formatted": " ".join(f"{value:8.4f}" for value in values[:16]),
      })
    self._event("inspect", f"read {label}", {"start_row": start_row, "num_rows": num_rows})
    return {"thread_id": thread_id, "rows": rows}

  def read_srca(self, start_row: int = 0, num_rows: int = 4) -> dict:
    return self._read_register_rows(read_srca_row, start_row, num_rows,
                                    thread_id=2, label="SrcA")

  def read_srcb(self, start_row: int = 0, num_rows: int = 4) -> dict:
    return self._read_register_rows(read_srcb_row, start_row, num_rows,
                                    thread_id=1, label="SrcB")

  def read_lregs_cmd(self, num_lregs: int = 16) -> dict:
    self._require_kernel_paused("read_lregs")
    tid = 2
    if not is_thread_fifo_empty(self.win, self.debugger.core, tid):
      raise RuntimeError(f"thread {tid} FIFO is not empty; wait longer in DEBUG_PAUSE()")
    injector = self._get_injector()
    rows = []
    for i in range(max(1, min(num_lregs, 16))):
      chunks = read_lreg(self.win, self.debugger.core, injector, i, tid)
      values = []
      for word in chunks:
        hi16 = (word >> 16) & 0xFFFF
        lo16 = word & 0xFFFF
        values.append(self._dest_bf16_to_float(hi16))
        values.append(self._dest_bf16_to_float(lo16))
      rows.append({
        "row": i,
        "values": values[:16],
        "formatted": " ".join(f"{value:8.4f}" for value in values[:16]),
      })
    self._event("inspect", "read LRegs", {"num_lregs": num_lregs})
    return {"thread_id": tid, "rows": rows}

  def test_inject(self, thread_id: int = 2) -> dict:
    """Diagnostic: inject a single SETRWC (harmless) to verify injection works."""
    self._require_kernel_paused("test_inject")
    from debug.tensix import TT_OP_SETRWC
    injector = self._get_injector()
    fifo_before = self._fifo_status()
    injector.inject(TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF), thread_id)
    fifo_after = self._fifo_status()
    return {"ok": True, "thread_id": thread_id, "fifo_before": fifo_before, "fifo_after": fifo_after}

  def read_fifo_status(self) -> dict:
    return self._fifo_status()

  def read_tensix_state(self, group: str = "all") -> dict:
    result = self._get_tensix_state_reader().read_group(group)
    self._event("inspect", "read tensix state", {"group": group})
    return result

  def cleanup(self):
    with self._lock:
      try:
        self.clear_pause_flags()
      except Exception:
        pass
      for risc_name in self.DEBUGGABLE_RISCS:
        risc = RiscDebug(self.win, self.debugger.core, risc_name)
        try:
          risc.clear_all_breakpoints()
        except Exception:
          pass
        try:
          if risc.is_halted():
            risc.cont()
        except Exception:
          pass
      self._event("session", "cleanup complete")

  def execute(self, command: str, args: dict | None = None) -> dict:
    args = args or {}
    handlers = {
      "status": self.status,
      "halt_risc": self.halt_risc,
      "continue_risc": self.continue_risc,
      "step_risc": self.step_risc,
      "next_risc": self.next_risc,
      "read_location": self.read_location,
      "read_gprs": self.read_gprs,
      "read_memory": lambda: self.read_memory(int(args.get("addr", 0)), int(args.get("count", 64))),
      "run_to_kernel_pause": lambda: self.run_to_kernel_pause(float(args.get("timeout", 5.0))),
      "release_kernel_pause": self.release_kernel_pause,
      "read_dest": lambda: self.read_dest(
        tile=int(args.get("tile", 0)),
        rows=int(args.get("rows", 4)),
        cols=int(args.get("cols", 8)),
        method=str(args.get("method", "array")),
      ),
      "read_srca": lambda: self.read_srca(
        start_row=int(args.get("start_row", 0)),
        num_rows=int(args.get("num_rows", 4)),
      ),
      "read_srcb": lambda: self.read_srcb(
        start_row=int(args.get("start_row", 0)),
        num_rows=int(args.get("num_rows", 4)),
      ),
      "read_lregs": lambda: self.read_lregs_cmd(
        num_lregs=int(args.get("num_lregs", 16)),
      ),
      "test_inject": lambda: self.test_inject(int(args.get("thread_id", 2))),
      "read_fifo_status": self.read_fifo_status,
      "read_tensix_state": lambda: self.read_tensix_state(str(args.get("group", "all"))),
      "shutdown_session": lambda: self._shutdown(),
    }
    with self._lock:
      if command not in handlers:
        payload = {
          "ok": False,
          "command": command,
          "error": f"unknown command {command!r}",
          "state": self.snapshot(),
        }
        self._event("error", payload["error"])
        return payload
      try:
        result = handlers[command]()
        return {
          "ok": True,
          "command": command,
          "result": result,
          "state": self.snapshot(),
        }
      except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        self._event("error", message, {"command": command})
        return {
          "ok": False,
          "command": command,
          "error": message,
          "error_type": exc.__class__.__name__,
          "state": self.snapshot(),
        }

  def _shutdown(self) -> dict:
    self.request_shutdown()
    return {"shutdown": True}
