import sys, time, struct
sys.path.insert(0, __import__('os').path.dirname(__file__))
from dramx import Bench, ep
from cq import Run
from pcie import TLBWindow
from tests.movement import test_noc as n
from tests.movement.profile_matmul_fp8 import clock_mhz
b = Bench(0)
try:
  base = b.region(200 << 20)
  # one bank (bank 2), 12 cores, NoC0 reads over 3 ports, long: 12 x 2 x 8 MiB = 192 MiB
  plan = {}; k = 0
  for core in b.cores[:12]:
    plan[core] = [dict(slot=s, dir='read', noc=s, coords=[ep(2, k % 3)], addr=base + (k := k + 1) * (8 << 20), bytes=8 << 20) for s in (0, 1)]
  b.run(plan, runs=1, label='warm')
  for _ in range(3):
    t0 = time.perf_counter(); b.d.cq.submit((Run(tuple(plan)),), timeout=30); t1 = time.perf_counter()
    st = []
    with TLBWindow(b.d.pcie.fd, b.cores[0]) as w:
      mhz = clock_mhz(w)
      for core in plan:
        w.target(0, core); st += list(zip(*[iter(struct.unpack('<4Q', w.read(n.TIMING_L1_ADDRESS, 32)))] * 2))
    dev_us = (max(e for _, e in st) - min(s for s, _ in st)) / mhz
    host_us = (t1 - t0) * 1e6
    tot = 12 * 2 * (8 << 20)
    print(f'device {dev_us:.0f} us -> {tot/dev_us/1000:.1f} GB/s | host submit->done {host_us:.0f} us -> {tot/host_us/1000:.1f} GB/s (includes dispatch)')
finally:
  b.close()
