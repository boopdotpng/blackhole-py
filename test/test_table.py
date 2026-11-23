"""Exercise resident tables and graph replay on a single card."""
from pathlib import Path
import numpy as np
from ttrv import Device, Var

def check(index):
  d = Device(index)
  try:
    n = len(d.dev.workers)
    out = d.zeros(n * 16, "u32", host=True)
    k = d.kernel("""
const N = 8
grid N
param out: u32[], host
param value: u32
l1 data: u32[16]
fn brisc() {
    data[0] = core.id + value
    noc.write out[core.id * 16], data, n=1, wait
}
""", N=n)
    with d.graph() as g:
      for _ in range(1000): k(out=out, value=4)
      k(out=out, value=Var("v"))
    for v in (7, 3, 0):
      g(v=v).wait()
      np.testing.assert_array_equal(out.numpy()[::16], np.arange(n) + v)
    # Two disjoint worker ranges can produce the same L1 address in parallel.
    # Their consumer is a separate resident image and must see both writes.
    local = d.local(64)
    producer = """
const N = 1
const CORE_BASE = 0
const SLOT = 0
grid N
param seed: u32
l1 shard: u32[16], at=SLOT
fn ncrisc() { shard[0] = seed + core.id }
"""
    low = d.kernel(producer, N=n//2, SLOT=local)
    high = d.kernel(producer, N=n-n//2, CORE_BASE=n//2, SLOT=local)
    read = d.kernel("""
const N = 1
const SLOT = 0
grid N
param out: u32[], host
l1 shard: u32[16], at=SLOT
fn brisc() { noc.write out[core.id * 16], shard, n=1, wait }
""", N=n, SLOT=local)
    with d.graph() as fork:
      low(seed=Var("lo"), _async=True)
      high(seed=Var("hi"))
      read(out=out)
    for lo, hi in ((42, 70), (21, 34)):
      fork(lo=lo, hi=hi).wait()
      np.testing.assert_array_equal(out.numpy()[::16], np.r_[lo + np.arange(n//2), hi + np.arange(n-n//2)])
    with d.graph() as split:
      k(out=out, value=Var("prefix"))
      k(out=out, value=Var("suffix"))
    first, last = split.split(1)
    for graph, args, expected in ((first, {"prefix": 11}, 11), (last, {"suffix": 22}, 22),
                                  (split, {"prefix": 1, "suffix": 33}, 33)):
      graph(**args).wait()
      np.testing.assert_array_equal(out.numpy()[::16], np.arange(n) + expected)
  finally: d.close()

def test_resident_replay():
  import pytest
  if not Path("/dev/tenstorrent/0").exists(): pytest.skip("Blackhole card 0 is unavailable")
  check(0)

if __name__ == "__main__":
  import sys
  check(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
