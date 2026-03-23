"""Thin CLI REPL frontend over the structured debug session API."""

from __future__ import annotations

import json
import shlex

from debug.session import DebugSession


class DebugRepl:
  """Interactive text frontend for a ``DebugSession``."""

  def __init__(self, session: DebugSession):
    self.session = session
    self._last_command = "status"

  def _print_location(self, result: dict):
    exact = "exact" if result.get("exact") else "approx"
    line = result.get("line")
    if line is None:
      print(f"  debug: {exact} PC {result['pc']} -> {result['function']} @ {result['file']}")
    else:
      print(f"  debug: {exact} PC {result['pc']} -> {result['function']} @ {result['file']}:{line}")
    if result.get("asm"):
      print(f"  debug: asm: {result['asm']}")
    for source in result.get("source_context", []):
      marker = ">" if source["current"] else " "
      print(f"  debug: {marker} {source['line']:4d} | {source['text']}")

  def _print_status(self, state: dict):
    print(
      f"  debug: {state['risc']}@({state['core'][0]},{state['core'][1]}) "
      f"mode={state['mode']} halted={state['risc_halted']} pause={state['kernel_paused']}"
    )
    if state.get("pc") is not None:
      tag = "exact" if state.get("pc_exact") else "approx"
      print(f"  debug: pc ({tag}) = {state['pc']}")
    fifo = state["fifo"]
    for tid, info in fifo["threads"].items():
      print(f"  debug: thread {tid} FIFO: {info['state']}")
    print(f"  debug: raw INSTRN_BUF_STATUS = {fifo['raw']}")

  def _print_regs(self, result: dict):
    print(f"  debug: pc = {result['pc']}")
    for register in result["registers"]:
      print(f"  debug: x{register['index']:<2d} ({register['name']:4s}) = {register['hex']}")

  def _print_memory(self, result: dict):
    print(f"  debug: memory at {result['address']}, {result['count']} words")
    for row in result["rows"]:
      print(f"  debug: {row['address']}: {' '.join(word[2:] for word in row['words'])}  {row['ascii']}")

  def _print_rows(self, result: dict, label: str):
    method = result.get("method")
    suffix = "" if method is None else f" via {method}"
    print(f"  debug: {label}{suffix}")
    for row in result["rows"]:
      print(f"  debug: row {row['row']:4d}: {row['formatted']}")
    note = result.get("note")
    if note:
      print(f"  debug: note: {note}")

  def _print_tensix_state(self, result: dict):
    print(f"  debug: tensix state group={result['group']}")
    for group_name, group_payload in result["groups"].items():
      print(f"  debug: [{group_name}]")
      if group_payload.get("error"):
        print(f"  debug: error: {group_payload['error']}")
        continue
      for section in group_payload.get("sections", []):
        print(f"  debug:   {section['name']}")
        for row_index, row in enumerate(section["rows"]):
          parts = [f"{field}={value['formatted']}" for field, value in row.items()]
          print(f"  debug:     row {row_index}: {' '.join(parts)}")

  def _print_result(self, payload: dict):
    if not payload["ok"]:
      print(f"  debug: error: {payload['error']}")
      return
    command = payload["command"]
    result = payload["result"]
    if command == "status":
      self._print_status(payload["state"])
    elif command in ("halt_risc", "step_risc", "next_risc", "read_location"):
      if result.get("done"):
        print("  debug: program completed")
      else:
        self._print_location(result)
    elif command == "continue_risc":
      print("  debug: continued")
    elif command == "read_gprs":
      self._print_regs(result)
    elif command == "read_memory":
      self._print_memory(result)
    elif command == "run_to_kernel_pause":
      if result.get("done"):
        print("  debug: program completed before DEBUG_PAUSE()")
      else:
        print("  debug: hit DEBUG_PAUSE() — kernel is spinning and FIFOs can drain")
        if result.get("location"):
          self._print_location(result["location"])
        self._print_status(payload["state"])
    elif command == "release_kernel_pause":
      print("  debug: released DEBUG_PAUSE()")
    elif command == "read_dest":
      self._print_rows(result, f"dst tile {result['tile']}")
    elif command == "read_srca":
      self._print_rows(result, "srcA")
    elif command == "read_fifo_status":
      self._print_status(payload["state"])
    elif command == "read_tensix_state":
      self._print_tensix_state(result)
    elif command == "shutdown_session":
      print("  debug: shutdown requested")
    else:
      print(json.dumps(payload, indent=2))

  @staticmethod
  def _help():
    print("  debug: commands:")
    print("    status|st                  show current debugger state")
    print("    halt                       DR-halt the target RISC")
    print("    continue|c                continue a DR-halted RISC")
    print("    step|s                    single-step the halted RISC")
    print("    next|n                    step over calls on the halted RISC")
    print("    where|w                   show current location (exact if halted)")
    print("    regs|gpr                  dump GPRs (requires halt)")
    print("    mem <addr> [count]        dump memory words (requires halt)")
    print("    pause [timeout]           run until DEBUG_PAUSE() spin-loop")
    print("    release                   clear DEBUG_PAUSE_FLAG and resume kernel")
    print("    fifo                      show instruction FIFO status")
    print("    tensix [group]            dump tensix state (all|alu|pack|unpack|gpr|rwc|adc)")
    print("    dest [tile] [rows] [cols] [array|dr]")
    print("    srca [start_row] [num_rows]   read SrcA during DEBUG_PAUSE()")
    print("    quit|q                    exit debugger")

  def _dispatch(self, raw: str) -> dict:
    parts = shlex.split(raw)
    if not parts:
      return self.session.execute("status")
    command = parts[0]
    if command in ("status", "st"):
      return self.session.execute("status")
    if command == "halt":
      return self.session.execute("halt_risc")
    if command in ("continue", "c"):
      return self.session.execute("continue_risc")
    if command in ("step", "s"):
      return self.session.execute("step_risc")
    if command in ("next", "n"):
      return self.session.execute("next_risc")
    if command in ("where", "w", "pc"):
      return self.session.execute("read_location")
    if command in ("regs", "gpr"):
      return self.session.execute("read_gprs")
    if command == "mem":
      addr = int(parts[1], 0) if len(parts) > 1 else 0
      count = int(parts[2], 0) if len(parts) > 2 else 64
      return self.session.execute("read_memory", {"addr": addr, "count": count})
    if command in ("pause", "run-to-pause"):
      timeout = float(parts[1]) if len(parts) > 1 else 5.0
      return self.session.execute("run_to_kernel_pause", {"timeout": timeout})
    if command in ("release", "resume"):
      return self.session.execute("release_kernel_pause")
    if command == "fifo":
      return self.session.execute("read_fifo_status")
    if command == "tensix":
      group = parts[1] if len(parts) > 1 else "all"
      return self.session.execute("read_tensix_state", {"group": group})
    if command == "dest":
      tile = int(parts[1], 0) if len(parts) > 1 else 0
      rows = int(parts[2], 0) if len(parts) > 2 else 4
      cols = int(parts[3], 0) if len(parts) > 3 else 8
      method = parts[4] if len(parts) > 4 else "array"
      return self.session.execute("read_dest", {
        "tile": tile,
        "rows": rows,
        "cols": cols,
        "method": method,
      })
    if command == "srca":
      start_row = int(parts[1], 0) if len(parts) > 1 else 0
      num_rows = int(parts[2], 0) if len(parts) > 2 else 4
      return self.session.execute("read_srca", {
        "start_row": start_row,
        "num_rows": num_rows,
      })
    if command in ("quit", "q"):
      return self.session.execute("shutdown_session")
    if command in ("help", "h", "?"):
      self._help()
      return {"ok": True, "command": "help", "result": {}, "state": self.session.snapshot()}
    return {"ok": False, "command": command, "error": f"unknown command {command!r}", "state": self.session.snapshot()}

  def run(self):
    self._print_result(self.session.execute("read_location"))
    self._help()
    while not self.session.wait_for_shutdown(timeout=0.0):
      try:
        raw = input("(bhdbg) ").strip()
      except EOFError:
        raw = "quit"
      command_line = raw or self._last_command
      payload = self._dispatch(command_line)
      if payload["command"] != "help":
        self._last_command = command_line
      self._print_result(payload)
      if payload["command"] == "shutdown_session":
        return
