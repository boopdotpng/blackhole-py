import numpy as np
import argparse
from device import Device
from program import Buffer, DType, Program
from ttk.sfpu import SfpuFormat
from ttk.unpack import UnpackTarget

def add1(src: Buffer, dst: Buffer) -> Program:
  p = Program(src.cores, src, dst)
  input_cb, output_cb = p.cb(src.dtype), p.cb(dst.dtype)

  b = p.sfpu.program()
  value = b.load(format=SfpuFormat.BF16)
  b.add_scalar(value, 1)
  b.store(value, format=SfpuFormat.BF16)
  add_one = b.finish()

  for tile in p.brisc.range(src.tiles_per_core):
    p.brisc.noc.read_into_cb(src, tile, input_cb)

  for _ in p.trisc0.range(src.tiles_per_core):
    p.unpack.move(input_cb, UnpackTarget.SRCA)

  for _ in p.trisc1.range(src.tiles_per_core):
    p.fpu.copy_a(dst_tile=0)
    p.sfpu.map(add_one, tile=0)
    p.fpu.publish()

  for _ in p.trisc2.range(dst.tiles_per_core):
    p.pack.move(output_cb, tile=0)

  for tile in p.ncrisc.range(dst.tiles_per_core):
    p.ncrisc.noc.write_from_cb(output_cb, dst, tile)
  return p

def run_hardware(tiles=2):
  device = Device()
  try:
    device.init_device()
    total_tiles = tiles * len(device.pcie.cores)
    shape = (32, 32 * total_tiles)
    src = device.dram.buffer("src", DType.BF16, shape)
    dst = device.dram.buffer("dst", DType.BF16, shape)
    program = add1(src, dst)
    values = ((np.arange(1024 * total_tiles, dtype=np.float32) % 257) - 128).reshape(shape) / 8
    source = src.from_numpy(values)
    expected = dst.from_numpy(src.to_numpy(source) + 1)
    device.write(src, source)
    device.queue(program)
    output = device.queue_read(dst)
    timestamps = device.run()
    kernel_us = timestamps[-1].us
    actual = output.result()
    if actual != expected:
      mismatch = next(i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
      raise SystemExit(
        f"FAIL at byte {mismatch}: {actual[mismatch]:02x} != {expected[mismatch]:02x}"
      )
    print("PASS")
    print(
      f"{total_tiles * (src.tile_size + dst.tile_size) / kernel_us / 1e3:.3f} GB/s"
    )
  finally: device.close()

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--tiles", type=int, default=2, help="tiles per core")
  args = parser.parse_args()
  if args.tiles <= 0: parser.error("--tiles must be positive")
  run_hardware(args.tiles)
