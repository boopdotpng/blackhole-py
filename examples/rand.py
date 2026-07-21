import argparse

import numpy as np

from device import Device
from program import Buffer, DType, Program


SHAPE = (32, 32)


def rand_fast(dst: Buffer, seed=0) -> Program:
  if dst.dtype is not DType.BF16:
    raise ValueError("rand_fast currently requires a BF16 destination")
  if dst.shape != SHAPE or dst.tiles != 1:
    raise ValueError(f"rand_fast currently generates one {SHAPE} tile")

  p = Program(dst.cores, dst)
  output_cb = p.ops.rand_fast(seed=seed)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def _generate(device, dst, seed):
  device.run(rand_fast(dst, seed))
  return dst.to_numpy(device.read(dst))


def run_hardware(seed=0):
  if not 0 <= seed <= 0xffffffff:
    raise ValueError("seed must be a 32-bit unsigned integer")

  device = Device()
  try:
    device.init_device()
    dst = device.dram.buffer("rand_dst", DType.BF16, SHAPE)
    first = _generate(device, dst, seed)
    replay = _generate(device, dst, seed)
    different = _generate(device, dst, seed ^ 0x9e3779b9)

    if not np.all(np.isfinite(first)):
      raise AssertionError("rand_fast produced a non-finite value")
    if not np.all((0.0 <= first) & (first < 1.0)):
      raise AssertionError(
        f"rand_fast values escaped [0, 1): min={first.min()} max={first.max()}"
      )
    if np.unique(first).size < 32:
      raise AssertionError("rand_fast produced fewer than 32 distinct BF16 values")
    if not np.array_equal(first, replay):
      raise AssertionError("rand_fast did not replay the same seed deterministically")
    if np.array_equal(first, different):
      raise AssertionError("rand_fast produced the same tile for different seeds")

    print("PASS rand_fast")
    print(
      f"seed={seed:#010x} min={first.min():.7f} "
      f"max={first.max():.7f} mean={first.mean():.7f} "
      f"unique={np.unique(first).size}"
    )
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--seed", type=lambda value: int(value, 0), default=0)
  run_hardware(parser.parse_args().seed)
