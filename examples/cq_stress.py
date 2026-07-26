"""Stress CQ-native DRAM copies, HCQ signals, and issue-ring wrap."""

import argparse
import time

import numpy as np

from cq import HOST_ISSUE_SIZE
from device import Device
from program import DType


def _payload(index, tiles):
  words = np.arange(tiles * 1024, dtype=np.uint32)
  words = (
    words * np.uint32(0x9e37) +
    np.uint32(index * 0x101 + 0x1234)
  ) & np.uint32(0xffff)
  return words.astype("<u2").tobytes()


def run_hardware(cycles=512, buffers=64):
  if cycles <= 0 or buffers <= 0:
    raise ValueError("cycles and buffers must be positive")

  device = Device()
  try:
    device.init_device()
    specs = tuple(
      (49 + index % 23, index)
      for index in range(buffers)
    )
    tensors = tuple(
      device.dram.buffer(
        f"cq_stress_{index}", DType.BF16, (32, tiles * 32),
        global_address=True, tilized=False,
      )
      for tiles, index in specs
    )
    payloads = tuple(
      _payload(index, tiles) for tiles, index in specs
    )
    bytes_per_cycle = sum(map(len, payloads))
    upload_seconds = read_seconds = 0.0

    for cycle in range(cycles):
      started = time.perf_counter()
      for tensor, payload in zip(tensors, payloads):
        device.write(tensor, payload)
      device.run(timeout=30.0)
      upload_seconds += time.perf_counter() - started

      started = time.perf_counter()
      reads = tuple(device.queue_read(tensor) for tensor in tensors)
      device.run(timeout=30.0)
      read_seconds += time.perf_counter() - started
      for index, (read, expected) in enumerate(zip(reads, payloads)):
        actual = read.result()
        if actual != expected:
          mismatch = next(
            (
              offset for offset, (left, right) in
              enumerate(zip(actual, expected)) if left != right
            ),
            min(len(actual), len(expected)),
          )
          raise AssertionError(
            f"cycle {cycle + 1} buffer {index} differs at byte {mismatch}",
          )

      if (cycle + 1) % min(8, cycles) == 0 or cycle + 1 == cycles:
        print(
          f"cycle={cycle + 1}/{cycles} event={device.cq.event} "
          f"issue_offset={device.cq.issue_write} "
          f"wraps={device.cq.put // HOST_ISSUE_SIZE}",
          flush=True,
        )

    gib = bytes_per_cycle * cycles / (1 << 30)
    print(
      f"PASS uploads={buffers * cycles} "
      f"exact_readbacks={buffers * cycles}",
    )
    print(
      f"bytes={gib:.3f} GiB upload_wall={upload_seconds:.3f}s "
      f"upload_rate={gib / upload_seconds:.2f} GiB/s "
      f"read_wall={read_seconds:.3f}s",
    )
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--cycles", type=int, default=512)
  parser.add_argument("--buffers", type=int, default=64)
  args = parser.parse_args()
  run_hardware(args.cycles, args.buffers)
