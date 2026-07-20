"""First SFPU program test: add 1.0 to every value in every tile."""

import argparse

import numpy as np

from device import Device
from program import Buffer, DType, Program
from ttk.sfpu import SfpuFormat
from ttk.unpack import UnpackTarget


def sfpu_add_scalar(src: Buffer, dst: Buffer) -> Program:
  if src.dtype is not DType.BF16 or dst.dtype is not DType.BF16:
    raise ValueError("SFPU add example requires BF16 buffers")
  if src.shape != dst.shape or src.cores != dst.cores:
    raise ValueError("source and destination must have the same shape and cores")

  p = Program(src.cores, src, dst)
  input_cb, output_cb = p.cb(src.dtype), p.cb(dst.dtype)

  # One immutable 32-lane body. map_tile() repeats it eight times per face
  # across all four faces of each tile.
  builder = p.sfpu.program()
  value = builder.load(format=SfpuFormat.BF16)
  builder.add_scalar(value, 1.0)
  builder.store(value, format=SfpuFormat.BF16)
  add_one = builder.finish()

  for tile in p.brisc.range(src.tiles_per_core):
    p.brisc.noc.read_into_cb(src, tile, input_cb)

  for _ in p.trisc0.range(src.tiles_per_core):
    p.unpack.move(input_cb, UnpackTarget.SRCA)

  for _ in p.trisc1.range(src.tiles_per_core):
    p.fpu.copy_a(dst_tile=0)
    p.sfpu.map_tile(add_one, tile=0)
    p.fpu.publish()

  for _ in p.trisc2.range(dst.tiles_per_core):
    p.pack.move(output_cb, tile=0)

  for tile in p.ncrisc.range(dst.tiles_per_core):
    p.ncrisc.noc.write_from_cb(output_cb, dst, tile)

  return p


def run_hardware(tiles=1):
  device = Device()
  try:
    device.init_device()
    total_tiles = tiles * len(device.pcie.cores)
    shape = (32, 32 * total_tiles)
    src = device.dram.buffer("src", DType.BF16, shape)
    dst = device.dram.buffer("dst", DType.BF16, shape)

    values = (
      (np.arange(1024 * total_tiles, dtype=np.float32) % 257) - 128
    ).reshape(shape) / 8
    source = src.from_numpy(values)
    expected = dst.from_numpy(src.to_numpy(source) + 1.0)

    device.write(src, source)
    timestamps = device.run(sfpu_add_scalar(src, dst))
    actual = device.read(dst)

    if actual != expected:
      mismatch = next(
        index for index, pair in enumerate(zip(actual, expected))
        if pair[0] != pair[1]
      )
      raise AssertionError(
        f"mismatch at byte {mismatch}: "
        f"actual={actual[mismatch]:02x} expected={expected[mismatch]:02x}"
      )

    print("PASS sfpu_add_scalar")
    print(f"kernel: {timestamps[-1].us:.3f} us")
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--tiles", type=int, default=1, help="tiles per core")
  args = parser.parse_args()
  if args.tiles <= 0: parser.error("--tiles must be positive")
  run_hardware(args.tiles)
