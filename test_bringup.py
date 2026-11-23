import os, struct, tempfile, time
from pathlib import Path
import fw
from device import Device, dram_read_cap

if __name__ != "__main__":
  import pytest

  @pytest.fixture(scope="module")
  def dev():
    if not Path("/dev/tenstorrent/0").exists(): pytest.skip("Blackhole card 0 is unavailable")
    device = Device(0)
    try: yield device
    finally: device.close()

def load(dev:Device, src:str, roles=("brisc",)) -> int:
  with tempfile.TemporaryDirectory() as d:
    (p := Path(d) / "kernel.c").write_text(src)
    image, pcs, _ = fw.build_worker([p], roles, dev.dram_banks)
  dev.load(image, pcs)
  return len(image)

def test_dma_roundtrip(dev:Device):
  for page, n in ((4096, (10 << 20) + 4096), (1088, 1088 * dev.dram_banks * 37)):
    src, dst = os.urandom(n), bytearray(n)
    t0 = time.perf_counter()
    addr = dev.allocator.upload(src, page)
    t1 = time.perf_counter()
    dev.allocator.copyout(dst, addr)
    t2 = time.perf_counter()
    assert dst == src, f"DMA roundtrip mismatch with {page} B pages"
    print(f"[PASS] DMA roundtrip, {n / 2**20:.2f} MiB in {page} B pages: in {n / (t1 - t0) / 1e9:.2f} GB/s, out {n / (t2 - t1) / 1e9:.2f} GB/s")

BARRIER = r"""
#include "crt0.h"
#define OUT     0x40000
#define COUNTS  0x40100
#define PARTIAL 0x41000

#ifdef ROLE_BRISC
static u32 epoch = 0;

void brisc_step(void) {
  volatile u32 *arg = (volatile u32 *)STEP_ARGS;
  u32 step = arg[0], rect = arg[1], excl = arg[2], coord0 = arg[3], host_lo = arg[4], host_hi = arg[5];
  u32 id = read32(WORKER_ID), n = read32(NUM_WORKERS);

  write32(OUT, id + step);
  fence();
  noc_write(0, PARTIAL + id * 64, coord0, OUT, 4);
  barrier_all(coord0, rect, excl, n, &epoch);

  if (id == 0) {
    u32 sum = 0;
    for (u32 i = 0; i < n; i++) sum += read32(PARTIAL + i * 64);
    write32(OUT + 0, sum);
    write32(OUT + 4, step);
    write32(OUT + 8, read32(DRAM_BANKS_L1));
    write32(OUT + 12, read32(GRID_COLS_L1));
    fence();
    noc_write_host(0, OUT, host_lo, host_hi, 16);
  }
  barrier_all(coord0, rect, excl, n, &epoch);
}
#endif

#ifdef ROLE_NCRISC
static u32 steps = 0;
void ncrisc_step(void) { write32(COUNTS, ++steps); }
#endif

#ifdef ROLE_TRISC
static u32 steps = 0;
void trisc_step(void) { write32(COUNTS + 4 * (1 + ROLE_TRISC), ++steps); }
#endif
"""

def test_bare_metal_and_barrier(dev:Device, steps:int=5):
  size = load(dev, BARRIER, fw.ROLES)
  rect, excl = dev.cover(dev.workers)
  out, args = dev.alloc_host(steps * 64), dev.alloc_host(steps * 64)
  for s in range(steps):
    host = dev.host.noc_addr + out + s * 64
    struct.pack_into("<6I", dev.host.mem, args + s * 64, s + 1, rect, excl, fw.noc(dev.workers[0]), host & 0xFFFFFFFF, host >> 32)
    dev.launch(dev.host.noc_addr + args + s * 64, 64)
  dev.synchronize()

  n = len(dev.workers)
  for s in range(1, steps + 1):
    got, want = struct.unpack_from("<4I", dev.host.mem, out + (s - 1) * 64), (n * (n - 1) // 2 + n * s, s, dev.dram_banks, dev.cols)
    assert got == want, f"step {s}: got {got}, expected {want}"
  for core in (dev.workers[0], dev.workers[-1]):
    assert (counts := struct.unpack("<4I", dev.card.read(core, 0x40100, 16))) == (steps,) * 4, f"{core} ran steps {counts}"
  print(f"[PASS] 5-RISC kernel, barrier_all() x {steps} steps across {n} workers (code {size} B)")

DRAM_READ = r"""
#include "crt0.h"
#define BUF 0x40000
#define OUT 0x30000

void brisc_step(void) {
  volatile u32 *arg = (volatile u32 *)STEP_ARGS;
  u32 pages = arg[0], page = arg[1], cap = arg[2], host_lo = arg[3], host_hi = arg[4];
  u32 rank = worker_rank_row_major();
  u32 t0 = read32(WALL_CLOCK_L);
  noc_dram_read_stream(rank, dram_stagger_offset(rank), page, pages, BUF, 0x1FFFF, 1, cap);
  noc_wait(0, 1, 1);
  write32(OUT, read32(WALL_CLOCK_L) - t0);
  fence();
  u32 off = rank * 64;
  noc_write_host(0, OUT, host_lo + off, host_hi + (host_lo + off < host_lo), 4);
}
"""

def test_reload_and_dram_bandwidth(dev:Device):
  load(dev, DRAM_READ)
  n, pages, page = len(dev.workers), 4096, 2048
  cycles, args = dev.alloc_host(n * 64), dev.alloc_host(64)
  host = dev.host.noc_addr + cycles
  for cap in (0, dram_read_cap(n)):
    struct.pack_into("<5I", dev.host.mem, args, pages, page, cap, host & 0xFFFFFFFF, host >> 32)
    dev.launch(dev.host.noc_addr + args, 64, sync=True)
    c = sorted(struct.unpack_from("<I", dev.host.mem, cycles + i * 64)[0] for i in range(n))
    gbs = n * pages * page / (c[-1] / (fw.AICLK_MHZ * 1e6)) / 1e9
    print(f"[BENCH] {n} cores reading DRAM in 2 KiB pages, cap {cap}: {gbs:.1f} GB/s, max/med {c[-1] / c[n // 2]:.2f}x, max/min {c[-1] / c[0]:.2f}x")
  pin = dev.dram_banks * 64.325
  assert gbs > 0.9 * pin, f"capped DRAM bandwidth too low: {gbs:.1f} GB/s vs {pin:.1f} GB/s pin"
  assert c[-1] / c[n // 2] < 1.15, f"capped tail too wide: {c[-1] / c[n // 2]:.2f}x"
  print("[PASS] Kernel reload, DRAM bandwidth")

if __name__ == "__main__":
  dev = Device(0)
  try:
    print(f"Opened {dev.card.name}: {dev.cols} cols, {dev.dram_banks} DRAM banks, {len(dev.workers)} workers, DMA core {dev.dma_core}")
    test_dma_roundtrip(dev)
    test_bare_metal_and_barrier(dev)
    test_reload_and_dram_bandwidth(dev)
  finally: dev.close()
