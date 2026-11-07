"""Hardware: boot the queue firmware on /dev/tenstorrent/0 and drive both queues. python3 -m pytest tests/hw/test_cq.py -s"""
import ctypes, mmap, os, struct, time
import numpy as np
import pytest
import fw
from cq import ComputeQueue, CopyQueue, dram, kernargs, program
from device import Device
from pcie import WINDOWS

HERE = os.path.dirname(__file__)
OUT = 0x100000

@pytest.fixture(scope="module")
def d():
  with Device(0) as d: yield d

def pinned(d, size):  # a page-aligned host buffer pinned for the card: (numpy view, NoC address, unpin)
  m = mmap.mmap(-1, size)
  a = np.frombuffer(m, np.uint8)
  addr = ctypes.addressof(ctypes.c_char.from_buffer(m))
  return a, d.pin(addr, size), lambda: d.unpin(addr, size)

def test_copy(d):
  n = 3 << 20
  (src, s, s_unpin), (dst, t, t_unpin) = pinned(d, n), pinned(d, n)
  src[:] = np.frombuffer(os.urandom(n), np.uint8)
  st = time.perf_counter()
  CopyQueue().copy(dram(0, 2048), s, n).copy(t, dram(0, 2048), n).timestamp(d.signal(0)).signal(d.signal(0), 1).submit(d.copy)
  stamp = d.wait(0, 1)
  print(f"\n3 MiB up + down: {(time.perf_counter() - st) * 1e3:.2f} ms, timestamp {stamp}")
  assert np.array_equal(src, dst) and stamp
  s_unpin(); t_unpin()

def test_copy_odd(d):  # addresses are 64-byte aligned, lengths and DRAM page offsets are not page multiples
  (src, s, s_unpin), (dst, t, t_unpin) = pinned(d, 300 << 10), pinned(d, 400 << 10)
  src[:] = np.frombuffer(os.urandom(300 << 10), np.uint8)
  q = CopyQueue().copy(dram(64 * 1001, 2048), s + 64, 290001).copy(t + 128, dram(64 * 1001, 2048), 290001).copy(t + 300032, s, 77)
  q.signal(d.signal(1), 7).submit(d.copy)
  d.wait(1, 7)
  assert np.array_equal(dst[128:128 + 290001], src[64:64 + 290001]) and np.array_equal(dst[300032:300109], src[:77])
  assert not dst[:128].any() and not dst[128 + 290001:300032].any()
  s_unpin(); t_unpin()

@pytest.mark.parametrize("size,offset", [(64, 0), (100, 64), (5 << 20, 4096 + 64), (200 << 20, 0), ((200 << 20) + 192, 128)])
def test_copyin_copyout(d, size, offset):  # host buffers start mid-page; aligned ones are pinned in place, others bounce
  data = np.random.randint(0, 256, size + offset, dtype=np.uint8)[offset:]
  out = np.empty(size + 3, np.uint8)[3:]  # never 64-byte aligned: copyout bounces
  d.copyin(dram(1 << 20, 2048), data)
  d.copyout(out, dram(1 << 20, 2048))
  assert np.array_equal(data, out)

def test_copyin_bytes(d):  # read-only sources bounce too
  data = os.urandom(10000)
  out = np.empty(10000, np.uint8)
  d.copyin(dram(0, 2048), data); d.copyout(out, dram(0, 2048))
  assert out.tobytes() == data

def test_transfer_speed(d):
  G = 1 << 30
  (a := np.frombuffer(mmap.mmap(-1, G), np.uint8))[:] = 7
  for name, f in (("copyin ", lambda: d.copyin(dram(0, 2048), a)), ("copyout", lambda: d.copyout(a, dram(0, 2048)))):
    best = min((st := time.perf_counter(), f(), time.perf_counter() - st)[2] for _ in range(3))
    print(f"\n{name} 1 GiB, pinned in place ({WINDOWS} windows): {G / best / 1e9:.1f} GB/s", end="")

def launch(d, value):
  brisc = fw.compile(os.path.join(HERE, "kernel_inc.c"), *fw.KERNEL["brisc"])
  prog, sizes = program({"brisc": brisc})
  args = kernargs(d.workers, sizes, struct.pack("<I", value))
  p, a = d.alloc(len(prog)), d.alloc(len(args))
  d.write(p, prog); d.write(a, args)
  return d.sysmem(p), len(prog), d.sysmem(a), len(args)

def test_exec(d):
  prog, size, args, asize = launch(d, 41)
  st = time.perf_counter()
  ComputeQueue().exec(prog, size, args, asize).signal(d.signal(2), 1).submit(d.compute)
  d.wait(2, 1)
  print(f"\nexec on {len(d.workers)} cores: {(time.perf_counter() - st) * 1e6:.0f} us")
  assert {d.pcie.read32(c, OUT) for c in d.workers} == {42}

def test_cross_queue(d):
  prog, size, args, asize = launch(d, 99)
  ComputeQueue().wait(d.signal(3), 1).exec(prog, size, args, asize).signal(d.signal(4), 1).submit(d.compute)
  time.sleep(0.05)
  assert d.read_signal(4)[0] == 0, "compute ran before its wait was satisfied"
  CopyQueue().signal(d.signal(3), 1).submit(d.copy)
  d.wait(4, 1)
  assert {d.pcie.read32(c, OUT) for c in d.workers} == {100}

def test_many(d):
  q = ComputeQueue()
  for i in range(1, 5001): q.signal(d.signal(5), i)  # 5000 packets, more than one ring
  q.submit(d.compute)
  d.wait(5, 5000)

@pytest.mark.parametrize("page", [1024, 2048, 4096])
def test_dram_pages(d, page):  # page p of a buffer sits in bank p % banks at (p // banks) * page, read back over the TLB
  banks, off = len(d.pcie.dram), d.alloc_dram(3 * len(d.pcie.dram) * page + 100)
  data = np.random.randint(0, 256, 3 * banks * page + 100, dtype=np.uint8)
  d.copyin(dram(off, page), data)
  for p in range(3 * banks + 1):
    n = min(page, len(data) - p * page)
    got = d.pcie.read(d.pcie.dram[p % banks], off // banks + p // banks * page, n)
    assert got == data[p * page:p * page + n].tobytes(), f"page {p}"

def test_dram_alloc_mixed_pages(d):  # buffers of different page sizes never overlap
  sizes = [(5000, 1024), (70000, 4096), (3, 2048), (1 << 20, 1024)]
  bufs = [(d.alloc_dram(n), n, page, np.random.randint(0, 256, n, dtype=np.uint8)) for n, page in sizes]
  for off, n, page, data in bufs: d.copyin(dram(off, page), data)
  for off, n, page, data in bufs:
    out = np.empty(n, np.uint8)
    d.copyout(out, dram(off, page))
    assert np.array_equal(out, data)
