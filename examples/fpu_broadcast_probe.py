"""Expose Blackhole FPU broadcast addressing with row-major DRAM buffers."""

import argparse

import numpy as np

from device import Device
from program import DType, Program
from ttk.fpu import Broadcast


PHYSICAL_SHAPE = (64, 16)


def bf16_truncate(values):
  values = np.asarray(values, dtype=np.float32)
  return ((values.view(np.uint32) >> 16) << 16).view(np.float32)


def broadcast_add(left, right, output, mode):
  p = Program(left.cores, left, right, output, fp32_dst=True)
  left_cb = p.cb(DType.BF16, depth=1)
  right_cb = p.cb(DType.BF16, depth=1)
  output_cb = p.cb(DType.BF16, depth=1)

  p.brisc.noc.read_into_cb(left, 0, left_cb)
  p.brisc.noc.read_into_cb(right, 0, right_cb)
  if mode is Broadcast.COLUMN:
    p.unpack.move_pair_rows(left_cb, right_cb)
  else:
    p.unpack.move_pair(left_cb, right_cb)
  p.fpu.binary("add", dst_tile=0, broadcast=mode).publish()
  p.pack.move(output_cb, tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, output, 0)
  return p


def run(mode):
  host_left = np.zeros(PHYSICAL_SHAPE, dtype=np.float32)
  host_right = np.arange(np.prod(PHYSICAL_SHAPE), dtype=np.float32).reshape(
    PHYSICAL_SHAPE,
  )

  device = Device()
  try:
    device.init_device()
    core = (device.dram.cores[0],)
    left = device.dram.buffer(
      "broadcast_left", DType.BF16, PHYSICAL_SHAPE,
      cores=core,
    )
    right = device.dram.buffer(
      "broadcast_right", DType.BF16, PHYSICAL_SHAPE,
      cores=core,
    )
    output = device.dram.buffer(
      f"broadcast_{mode.name.lower()}", DType.BF16, PHYSICAL_SHAPE,
      cores=core,
    )

    left_bytes = left.from_numpy(host_left)
    right_bytes = right.from_numpy(host_right)
    stored_right = right.to_numpy(right_bytes)
    device.write(left, left_bytes)
    device.write(right, right_bytes)
    device.run(broadcast_add(left, right, output, mode), timeout=30.0)

    np.set_printoptions(linewidth=180, suppress=True, precision=1)
    actual = output.to_numpy(device.read(output, timeout=30.0))
    print(f"{mode.name} ({int(mode)}):")
    print("  first two rows of each physical 16x16 face:")
    print(actual[[0, 1, 16, 17, 32, 33, 48, 49]])
    print("  first column:")
    print(actual[:, 0].reshape(8, 8))
    print()

    print("Stored BF16 SrcB first row of each physical face:")
    print(stored_right[[0, 16, 32, 48]])
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "mode", choices=tuple(mode.name.lower() for mode in Broadcast),
  )
  args = parser.parse_args()
  run(Broadcast[args.mode.upper()])
