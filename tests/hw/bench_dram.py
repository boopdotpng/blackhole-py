"""Hardware: DRAM bandwidth with every worker streaming on BRISC (NoC 0) and/or NCRISC (NoC 1).
PYTHONPATH=. python3 tests/hw/bench_dram.py

Both NoCs use the same tile of each bank. Measured 2026-10-07 on p150a: sending NoC 1 to the bank's other tile changed
nothing for NoC 0 read + NoC 1 write (418 vs 425 GB/s) or for the COPY queue, and only helped read + read (+14%) and
write + write (+9%), so the firmware and runtime keep one tile per bank."""
import os, struct, time
import fw
from cq import ComputeQueue, kernargs, program
from device import Device

HERE = os.path.dirname(__file__)
BYTES, REPS = 16 << 20, 2
IDLE, READ, WRITE = 0, 1, 2

def run(d, prog, brisc, ncrisc, page, sig):
  (blob, sizes), args = prog, kernargs(d.workers, prog[1], struct.pack("<5I", BYTES, brisc, ncrisc, page.bit_length() - 1, REPS))
  p, a = d.alloc(len(blob)), d.alloc(len(args))
  d.write(p, blob); d.write(a, args)
  best = float("inf")
  for i in range(3):
    st = time.perf_counter()
    ComputeQueue().exec(d.sysmem(p), len(blob), d.sysmem(a), len(args)).signal(d.signal(sig), i + 1).submit(d.compute)
    d.wait(sig, i + 1, timeout=30)
    best = min(best, time.perf_counter() - st)
  return best

def main():
  names = {IDLE: "-", READ: "read", WRITE: "write"}
  with Device(0) as d:
    assert d.alloc_dram(1) == 0 and 2 * 256 * 2 * BYTES <= d.dram_size  # every core's slot fits
    src, banks = os.path.join(HERE, "kernel_dram_stream.c"), len(d.pcie.dram)
    prog = program({r: fw.compile(src, *fw.KERNEL[r], banks, TT_FW_RISC=i) for i, r in enumerate(("brisc", "ncrisc"))})
    base, sig = run(d, prog, IDLE, IDLE, 2048, 1), 1
    print(f"{len(d.workers)} cores, {BYTES * REPS >> 20} MB per active RISC, empty exec {base * 1e6:.0f} us")
    print(f"{'page':>5} {'brisc/noc0':>11} {'ncrisc/noc1':>12} {'GB/s':>7}")
    for page in (1024, 2048, 4096):
      for b, n in ((READ, IDLE), (IDLE, READ), (IDLE, WRITE), (READ, WRITE), (READ, READ), (WRITE, WRITE)):
        total = len(d.workers) * BYTES * REPS * ((b != IDLE) + (n != IDLE))
        print(f"{page:>5} {names[b]:>11} {names[n]:>12} {total / (run(d, prog, b, n, page, sig := sig + 1) - base) / 1e9:>7.1f}")

if __name__ == "__main__": main()
