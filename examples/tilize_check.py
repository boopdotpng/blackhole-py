"""Does the hardware tilizer produce exactly `Buffer.tile_data`'s permutation?

Everything in the prefill plan rests on that equivalence: prefill embedding
gathers vocabulary rows row-major over the NoC and tilizes them on device, and
the result has to be bit-identical to what the host tilizer produces today, or
every elementwise op downstream silently pairs the wrong elements.

The test is an identity round trip:

    src (tilized=False)     DRAM holds elements in logical order
      -> read_into_cb       verbatim bytes
      -> unpack tilize=True HW permutes row-major -> faces in srcA
      -> copy_a / pack      packer writes face order
      -> dst (tilized=True) host inverse-permutes on readback

If the hardware permutation matches the host one, the two cancel and the output
equals the input. With --no-tilize the unpack step is skipped, nothing cancels,
and the output must NOT match -- that is the control proving the check has teeth.
"""

import argparse
import numpy as np

from device import Device
from program import Buffer, DType, Program
from ttk.unpack import UnpackTarget


def tilize_identity(src: Buffer, dst: Buffer, *, tilize: bool) -> Program:
  p = Program(src.cores, src, dst)
  input_cb, output_cb = p.cb(src.dtype), p.cb(dst.dtype)

  for tile in p.brisc.range(src.tiles_per_core):
    p.brisc.noc.read_into_cb(src, tile, input_cb)

  for _ in p.trisc0.range(src.tiles_per_core):
    p.unpack.move(input_cb, UnpackTarget.SRCA, tilize=tilize)

  for _ in p.trisc1.range(src.tiles_per_core):
    if tilize: p.fpu.copy_a_tilized(dst_tile=0)
    else: p.fpu.copy_a(dst_tile=0)
    p.fpu.publish()

  for _ in p.trisc2.range(dst.tiles_per_core):
    p.pack.move(output_cb, tile=0)

  for tile in p.ncrisc.range(dst.tiles_per_core):
    p.ncrisc.noc.write_from_cb(output_cb, dst, tile)
  return p


def run(tiles=1, mode="tilize"):
  tilize = mode == "tilize"
  device = Device()
  try:
    device.init_device()
    total_tiles = tiles * len(device.pcie.cores)
    shape = (32, 32 * total_tiles)
    # src is row-major on device; dst is ordinary face-tilized storage.
    # "identity" uploads an ordinarily tilized src and skips the device
    # tilize, so both permutations are the host's and the round trip must
    # reproduce the input exactly -- that is what proves the harness can
    # detect agreement at all, which the "control" mode alone cannot.
    src = device.dram.buffer(
      "src", DType.BF16, shape, tilized=mode == "identity",
    )
    dst = device.dram.buffer("dst", DType.BF16, shape)

    values = np.random.default_rng(0).standard_normal(shape, dtype=np.float32)
    source = src.from_numpy(values)
    # Quantize through BF16 so the comparison is exact, not approximate.
    quantized = src.to_numpy(source)
    expected = dst.from_numpy(quantized)

    device.write(src, source)
    device.queue(tilize_identity(src, dst, tilize=tilize))
    output = device.queue_read(dst)
    device.run()
    actual = output.result()

    matched = actual == expected
    if tilize:
      if not matched:
        mismatch = next(
          i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]
        )
        raise SystemExit(
          f"FAIL: hardware tilize does not match tile_data; first differing "
          f"byte {mismatch}: {actual[mismatch]:02x} != {expected[mismatch]:02x}"
        )
      print("PASS: hardware tilize == tile_data permutation")
    elif mode == "identity":
      if not matched:
        mismatch = next(
          i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]
        )
        raise SystemExit(
          f"FAIL: harness is broken -- an unpack/copy/pack round trip with no "
          f"permutation change differs at byte {mismatch}"
        )
      print("PASS (identity): round trip is exact when nothing permutes")
    else:
      if matched:
        raise SystemExit(
          "FAIL: control passed, so the round trip is insensitive to the "
          "permutation and the tilize check proves nothing"
        )
      print("PASS (control): without tilize the round trip does not cancel")
  finally: device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--tiles", type=int, default=1, help="tiles per core")
  parser.add_argument(
    "--mode", choices=("tilize", "control", "identity"), default="tilize",
    help="tilize: the real check; control: row-major src without the tilizing "
         "unpack, which must NOT cancel; identity: tilized src without the "
         "tilizing unpack, which must round trip exactly",
  )
  args = parser.parse_args()
  if args.tiles <= 0: parser.error("--tiles must be positive")
  run(args.tiles, args.mode)
