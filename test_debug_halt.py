#!/usr/bin/env python3
"""Quick smoke test: boot firmware, halt BRISC, read GPRs + PC."""
import os, sys
sys.path.insert(0, ".")

from hw import TLBWindow, TileGrid, TensixMMIO, NocOrdering, align_down
from debug.core import TileDebugger
from debug.inspect import TileInspector

fd = os.open("/dev/tenstorrent/0", os.O_RDWR)
core = TileGrid.WORKER_CORES[0]
print(f"target core: ({core[0]},{core[1]})")

# boot firmware on this core by running a trivial program via slow dispatch
os.environ["TT_USB"] = "1"
from device import Device
dev = Device()
from dispatch import Program
prog = Program(cores=1, reader_kernel="", writer_kernel="", compute_kernel="", cbs=[], name="nop")
dev.queue(prog)
dev.run()
print("firmware booted")

# now the firmware is idling in its go-wait loop
tlb = TLBWindow(fd, core)
dbg = TileDebugger(tlb, core)

# scan PCs before halt (non-intrusive)
print("\n--- PCs (debug bus, non-intrusive) ---")
pcs = dbg.read_all_pcs()
for risc, pc in pcs.items():
  print(f"  {risc:7s} 0x{pc:08x}")

# halt all
print("\n--- halting all ---")
dbg.halt_all()
for risc in ("brisc", "trisc0", "trisc1", "trisc2", "ncrisc"):
  print(f"  {dbg.status_str(risc)}")

# read BRISC GPRs
print("\n--- BRISC GPRs ---")
gprs = dbg.read_gprs("brisc")
for i in range(0, 32, 4):
  parts = []
  for j in range(4):
    from debug.regs import GPR_NAMES
    name = GPR_NAMES[i + j]
    parts.append(f"{name:4s}=0x{gprs[name]:08x}")
  print(f"  {' '.join(parts)}")
print(f"  {'pc':4s}=0x{gprs['pc']:08x}")

# read wall clock
clk = dbg.read_wall_clock()
print(f"\n--- wall clock: {clk:,} cycles ---")

# read L1
insp = TileInspector(tlb, core)
print("\n--- L1 @ 0x000 (first 64 bytes) ---")
print(insp.dump_l1(0x0, 64))

# resume
print("\n--- resuming ---")
dbg.resume_all()
print("done")

tlb.close()
dev.close()
