"""Benchmark CQ-native DRAM transfer after host tilization/staging."""

import argparse
import statistics
import time

from device import Device
from program import DType


def _rate(size, seconds):
  return size / seconds / 1e9, size / seconds / (1 << 30)


def run(size_mib=256, repeats=5, validate=True):
  if size_mib <= 0 or repeats <= 0:
    raise ValueError("size and repeats must be positive")
  size = size_mib << 20
  if size % 2048:
    raise ValueError("size must be a multiple of one BF16 tile (2048 bytes)")

  device = Device()
  try:
    device.init_device()
    tiles = size // 2048
    buffer = device.dram.buffer(
      "dram_bench", DType.BF16, (32, tiles * 32),
      global_address=True, tilized=False,
    )
    # This copy intentionally precedes the timer: the benchmark starts after
    # host tilization/staging, at CQ submission.
    pattern = bytes(range(256))
    payload = pattern * (size // len(pattern))
    device.pcie.sysmem.write(device.cq.dram, payload)
    upload = device._dram_copy_program(buffer, True, 0)

    samples = []
    for index in range(repeats):
      started = time.perf_counter()
      device.queue(upload, report=False)
      device.run(timeout=120.0)
      elapsed = time.perf_counter() - started
      samples.append(elapsed)
      gb, gib = _rate(size, elapsed)
      print(
        f"upload {index + 1}/{repeats}: {elapsed * 1e3:.3f} ms  "
        f"{gb:.2f} GB/s  {gib:.2f} GiB/s",
        flush=True,
      )

    if validate:
      readback = device.queue_read(buffer)
      device.run(timeout=120.0)
      if readback.result() != payload:
        raise AssertionError("DRAM benchmark readback differs from staged data")
      print("readback: exact match")

    median = statistics.median(samples)
    best = min(samples)
    med_gb, med_gib = _rate(size, median)
    best_gb, best_gib = _rate(size, best)
    print(
      f"median: {median * 1e3:.3f} ms  {med_gb:.2f} GB/s  "
      f"{med_gib:.2f} GiB/s",
    )
    print(
      f"best:   {best * 1e3:.3f} ms  {best_gb:.2f} GB/s  "
      f"{best_gib:.2f} GiB/s",
    )
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--size-mib", type=int, default=256)
  parser.add_argument("--repeats", type=int, default=5)
  parser.add_argument("--no-validate", action="store_true")
  args = parser.parse_args()
  run(args.size_mib, args.repeats, not args.no_validate)
