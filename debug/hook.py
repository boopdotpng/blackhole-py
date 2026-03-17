# debug/hook.py - Runtime integration for DEBUG=1
#
# Hooks into the dispatch flow to:
#   1. Collect ELF bytes from compiled kernels
#   2. Set breakpoints at kernel entry (kernel_main / math_main)
#   3. Wait for a core to hit the breakpoint
#   4. Drop into the interactive REPL
#
# Usage from device.py:
#   if DEBUG:
#     from debug.hook import debug_dispatch
#     debug_dispatch(device, program, compiled_kernels)

from __future__ import annotations
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from device import Device
  from dispatch import Program
  from compiler import CompiledKernel

from debug.repl import DebugSession
from debug.source import ElfInfo


# map processor index -> (risc_name for debug, risc_name for breakpoint)
_PROC_MAP = {
  0: "brisc",
  1: "ncrisc",
  2: "trisc0",
  3: "trisc1",
  4: "trisc2",
}

# which RISC to break on by default (math core is most interesting)
_DEFAULT_BREAK_RISC = "trisc1"


def debug_dispatch(device, ir_commands, writer=None, reader=None, compute=None):
  """Hook called after IR is built but before dispatch.

  Sets up debug session, finds kernel entry points from ELFs,
  sets breakpoints, dispatches, waits for breakpoint hit,
  then drops into the REPL.
  """
  cores = device.cores

  # collect ELF bytes from compiled kernels
  elf_map: dict[str, bytes] = {}  # risc_name -> elf_bytes
  if writer and writer.elf_bytes:
    elf_map["brisc"] = writer.elf_bytes
  if reader and reader.elf_bytes:
    elf_map["ncrisc"] = reader.elf_bytes
  if compute:
    for i, kernel in enumerate(compute):
      if kernel.elf_bytes:
        elf_map[f"trisc{i}"] = kernel.elf_bytes

  if not elf_map:
    print("  debug: no ELFs with debug info found (compile with DEBUG=1)")
    return

  # find kernel entry points
  # The ELF symbols give us the offset of _start/kernel_main RELATIVE to the
  # start of the kernel text segment. At runtime, the kernel text is loaded at
  # KERNEL_CONFIG_BASE + kernel_text_offset[proc_idx]. So the actual breakpoint
  # address = kernel_text_base + (symbol_addr - elf_text_base).
  #
  # For now we break at the START of the kernel text (the _start wrapper).
  # The runtime address comes from build_payload's kernel_text_offset, which
  # we compute by re-running the same layout logic.
  from compiler import iter_pt_load
  elf_text_bases: dict[str, int] = {}  # risc -> ELF text segment paddr
  elf_entry_offsets: dict[str, int] = {}  # risc -> offset of entry within text
  for risc, elf_bytes in elf_map.items():
    info = ElfInfo(elf_bytes, name=risc)
    # get the text segment base from the ELF
    text_segs = [s for s in iter_pt_load(elf_bytes) if s.flags & 1]  # executable
    if text_segs:
      elf_text_bases[risc] = text_segs[0].paddr
    entry_addr = info.entry_pc()
    if entry_addr is not None and risc in elf_text_bases:
      elf_entry_offsets[risc] = entry_addr - elf_text_bases[risc]
      print(f"  debug: {risc} kernel entry at ELF addr 0x{entry_addr:08x} (offset +0x{elf_entry_offsets[risc]:x})")
    else:
      # fallback: break at the very start of the kernel text (offset 0)
      elf_entry_offsets[risc] = 0
      print(f"  debug: {risc} breaking at kernel text start (offset +0x0)")

  if not elf_entry_offsets:
    print("  debug: no kernel entry points found, skipping debug")
    return

  # decide which RISC to break on
  break_risc = _DEFAULT_BREAK_RISC
  if break_risc not in elf_entry_offsets:
    for r in ("trisc1", "trisc0", "trisc2", "brisc"):
      if r in elf_entry_offsets:
        break_risc = r
        break

  if break_risc == "ncrisc":
    print("  debug: cannot set breakpoint on ncrisc (no debug hardware)")
    print("  debug: falling back to scan-only mode")
    break_risc = None

  # create debug session
  sess = DebugSession(fd=device.fd, cores=cores)
  for risc, elf_bytes in elf_map.items():
    sess.add_elf(risc, elf_bytes)

  # dispatch: write data to L1, then read kernel_text_offset to compute
  # breakpoint addresses, set breakpoints, THEN send go signal
  from dispatch import Write, Launch, GoMsg, DevMsgs, mcast_rects
  from hw import TLBWindow, TensixL1
  import struct as _struct, ctypes

  print("  debug: dispatching program (write phase)...")
  launch_cores = None
  with TLBWindow(device.fd, start=cores[0]) as win:
    for cmd in ir_commands:
      match cmd:
        case Write(cores=wc, addr=addr, data=data) if isinstance(data, list):
          for core, d in zip(wc, data):
            win.target(core)
            win.write(addr, d)
        case Write(cores=wc, addr=addr, data=data):
          for x0, x1, y0, y1 in mcast_rects(wc):
            win.target((x0, y0), (x1, y1))
            win.write(addr, data)
        case Launch(cores=lc):
          launch_cores = lc
          # DON'T send go signal yet -- set breakpoints first

  # read kernel_text_offset from L1 (written by the Write phase above)
  # KernelConfigMsg layout: kernel_config_base[3xu32] + sem_offset[3xu16] +
  #   local_cb_offset[u16] + remote_cb_offset[u16] + rta_offset[5x4] +
  #   mode[u8] + pad[u8] = 44 bytes, then kernel_text_offset[5xu32]
  KTEXT_OFF_OFFSET = 44  # byte offset of kernel_text_offset within LaunchMsg
  entry_points: dict[str, int] = {}
  insp = sess.inspector
  proc_names = ["brisc", "ncrisc", "trisc0", "trisc1", "trisc2"]
  for proc_idx in range(5):
    ktext_off = insp.read_l1_u32(TensixL1.LAUNCH + KTEXT_OFF_OFFSET + proc_idx * 4)
    risc = proc_names[proc_idx]
    if ktext_off == 0:
      continue
    runtime_base = TensixL1.KERNEL_CONFIG_BASE + ktext_off
    entry_offset = elf_entry_offsets.get(risc, 0)
    entry_addr = runtime_base + entry_offset
    entry_points[risc] = entry_addr
    print(f"  debug: {risc:7s} kernel_text L1=0x{runtime_base:06x} entry=0x{entry_addr:06x} (offset +0x{entry_offset:x})")

  # set runtime offsets on ElfInfo objects so addr2line can translate PCs
  for risc in elf_text_bases:
    elf_info = sess.elfs.get(risc)
    if elf_info and risc in entry_points:
      runtime_base = entry_points[risc] - elf_entry_offsets.get(risc, 0)
      elf_info.set_runtime_offset(runtime_base, elf_text_bases[risc])

  if break_risc and break_risc in entry_points:
    bp_addr = entry_points[break_risc]
    print(f"  debug: setting breakpoint on {break_risc} at 0x{bp_addr:06x} on all {len(cores)} cores")
    sess.multi.set_breakpoint_all(break_risc, 0, bp_addr)
    sess.switch_risc(break_risc)

  # NOW send the go signal
  print("  debug: sending go signal...")
  with TLBWindow(device.fd, start=cores[0]) as win:
    if launch_cores:
      go = GoMsg()
      go.bits.signal = DevMsgs.RUN_MSG_GO
      go_blob = _struct.pack("<I", go.all)
      for x0, x1, y0, y1 in mcast_rects(launch_cores):
        win.target((x0, y0), (x1, y1))
        win.uc[TensixL1.GO_MSG:TensixL1.GO_MSG + 4] = go_blob

  if break_risc and break_risc in entry_points:
    print(f"  debug: waiting for {break_risc} breakpoint hit...")
    st = sess.multi.wait_breakpoint(break_risc, timeout=10.0)
    if st is None:
      print("  debug: timeout, halting first core for inspection")
      sess.switch_core(cores[0])
      sess.debugger.halt_all()
    else:
      print(f"  debug: hit on core ({st.core[0]},{st.core[1]}) at 0x{st.pc:08x}")
      sess.switch_core(st.core)
      sess.debugger.halt_all()

  # enter REPL
  print("  debug: entering debugger (type 'help' for commands)")
  sess.repl()

  # cleanup: clear breakpoints, resume, wait for completion
  print("  debug: cleaning up...")
  sess.multi.clear_breakpoints_all()
  sess.multi.resume_all()

  if launch_cores:
    print("  debug: waiting for program completion...")
    import time as _time
    with TLBWindow(device.fd, start=cores[0]) as win:
      for x, y in launch_cores:
        win.target((x, y))
        deadline = _time.perf_counter() + 10.0
        while win.uc[TensixL1.GO_MSG + 3] != DevMsgs.RUN_MSG_DONE:
          if _time.perf_counter() > deadline:
            print(f"  debug: timeout waiting for core ({x},{y}) to finish")
            break
          _time.sleep(0.001)

  sess.close()
  print("  debug: done")
