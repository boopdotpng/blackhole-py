#!/usr/bin/env python3
"""Benchmark: DMA copy 512 MB sysmem <-> interleaved DRAM via fast dispatch."""
import os, time
import numpy as np

from device import Device, Dtype

SIZE_MB = int(os.environ.get("SIZE_MB", "512"))
ITERS = int(os.environ.get("ITERS", "3"))

def main():
  device = Device()
  try:
    size_bytes = SIZE_MB * 1024 * 1024
    tile_size = Dtype.Float16_b.tile_size  # 2048
    num_tiles = size_bytes // tile_size
    num_cores = len(device.cores)

    print(f"DMA bandwidth benchmark: {SIZE_MB} MB ({num_tiles} tiles), {num_cores} cores, {ITERS} iterations")

    # Allocate DRAM buffer (no shape = no tilize/untilize on host)
    buf = device.dram.alloc(num_tiles, Dtype.Float16_b, name="bw_test")
    data = np.random.randint(0, 65536, size=size_bytes // 2, dtype=np.uint16).tobytes()

    # Warmup
    device.dram_write(buf, data)
    device.dram_read(buf)

    # Benchmark fill (host -> device)
    fill_times = []
    for i in range(ITERS):
      t0 = time.perf_counter()
      device.dram_write(buf, data)
      t1 = time.perf_counter()
      fill_times.append(t1 - t0)

    # Benchmark drain (device -> host)
    drain_times = []
    for i in range(ITERS):
      t0 = time.perf_counter()
      result = device.dram_read(buf)
      t1 = time.perf_counter()
      drain_times.append(t1 - t0)

    # Verify round-trip
    if result != data:
      mismatches = sum(1 for a, b in zip(data, result) if a != b)
      raise SystemExit(f"FAIL: {mismatches} byte mismatches in round-trip")
    print("PASS: round-trip data integrity verified")

    def report(label, times):
      for i, t in enumerate(times):
        bw = SIZE_MB / t / 1024
        print(f"  [{i}] {t * 1e6:,.0f} us  ({bw:.2f} GB/s)")
      best = min(times)
      bw = SIZE_MB / best / 1024
      print(f"  best: {best * 1e6:,.0f} us  ({bw:.2f} GB/s)")

    print(f"\nFill (host -> DRAM) {SIZE_MB} MB:")
    report("fill", fill_times)
    print(f"\nDrain (DRAM -> host) {SIZE_MB} MB:")
    report("drain", drain_times)

  finally:
    device.close()

if __name__ == "__main__":
  main()
