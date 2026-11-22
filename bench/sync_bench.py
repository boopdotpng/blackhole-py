"""Latency of the decode megakernel's core-to-core sync patterns on all workers (see bench/sync.c).

  python3.14 bench/sync_bench.py"""
import statistics, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fw
from device import Device

ITERS = 2000

def run(dev, mode, nbytes, gen, args, out):
  n = len(dev.workers)
  rect, excl = dev.cover(dev.workers)
  host = dev.host.noc_addr + out
  struct.pack_into("<13I", dev.host.mem, args, mode, ITERS, nbytes, rect, excl, fw.noc(dev.workers[0]),
                   host & 0xFFFFFFFF, host >> 32, gen, 0, 0, 0, 0)
  dev.launch(dev.host.noc_addr + args, 64, sync=True, timeout=30)
  recs = [struct.unpack_from("<3I", dev.host.mem, out + i * 64) for i in range(n)]
  per = sorted(r[0] / ITERS for r in recs)
  summing = statistics.median(r[1] / ITERS for r in recs)
  errors = sum(r[2] for r in recs)
  c, w = struct.unpack_from("<5I", dev.host.mem, out + 55 * 64), struct.unpack_from("<5I", dev.host.mem, out)
  if mode in (3, 4):
    print(f"    coordinator per sync: waiting for slices {c[3] / ITERS:.0f}, multicast {c[4] / ITERS:.0f} cycles")
    print(f"    core 0 per sync: from sending its slice to having the whole vector {w[3] / ITERS:.0f} cycles")
  return statistics.median(per), per[-1], summing, errors

if __name__ == "__main__":
  dev = Device(0)
  try:
    image, pcs, _ = fw.build_worker([Path(__file__).with_name("sync.c")], ("brisc",), dev.dram_banks)
    dev.load(image, pcs)
    n = len(dev.workers)
    out, args = dev.alloc_host(n * 64), dev.alloc_host(64)
    us = lambda c: c / fw.AICLK_MHZ
    slice_of = lambda elems, size: (-(-elems * size // n) + 3) // 4 * 4   # bytes per core, whole words
    # Modes 1 and 2 (every core multicasts) wedge the NoC at >= 16 concurrent senders; they are not run.
    cases = [("barrier_all", 0, 4),
             ("coord gather 4096 bf16", 3, slice_of(4096, 2)),
             ("coord gather 14336 bf16", 3, slice_of(14336, 2)),
             ("all-reduce 4096 fp32", 4, slice_of(4096, 4))]
    print(f"{dev.card.name}: {n} workers, {ITERS} generations per launch, cycles per sync (us at {fw.AICLK_MHZ} MHz)")
    gen = 1
    for name, mode, nbytes in cases:
      med, worst, summing, errors = run(dev, mode, nbytes, gen, args, out)
      gen += ITERS + 2
      extra = f", of which BRISC summing {summing:.0f}" if mode in (2, 4) else ""
      print(f"  {name:24s} {nbytes:4d} B/core: median core {med:7.0f} ({us(med):5.2f} us), slowest {worst:7.0f}{extra}"
            f"{'' if not errors else f'  ERRORS {errors}'}")
  finally: dev.close()
