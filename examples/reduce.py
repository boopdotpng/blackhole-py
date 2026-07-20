import argparse
import numpy as np

from device import Device
from program import Buffer, DType, Program
from ttk.fpu import Broadcast


SHAPE = (32, 32)


def _reduce(src: Buffer, dst: Buffer, operation: str) -> Program:
  buffers = (src, dst)
  if any(buffer.dtype is not DType.BF16 for buffer in buffers):
    raise ValueError("reduce example requires BF16 buffers")
  if any(buffer.shape != SHAPE or buffer.tiles != 1 for buffer in buffers):
    raise ValueError(f"reduce example requires one {SHAPE} tile per buffer")
  if any(buffer.cores != src.cores for buffer in buffers[1:]):
    raise ValueError("reduce example buffers must use the same cores")

  p = Program(src.cores, *buffers)
  input_cb = p.cb(src.dtype)
  output_cb = p.cb(dst.dtype)

  p.brisc.noc.read_into_cb(src, 0, input_cb)

  getattr(p.ops, operation)(input_cb, output_cb, dst_tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def reduce_sum(src: Buffer, dst: Buffer) -> Program:
  return _reduce(src, dst, "reduce_sum")


def reduce_max(src: Buffer, dst: Buffer) -> Program:
  return _reduce(src, dst, "reduce_max")


def reduce_min(src: Buffer, dst: Buffer) -> Program:
  return _reduce(src, dst, "reduce_min")


def row_sum(src: Buffer, dst: Buffer) -> Program:
  return _reduce(src, dst, "row_sum")


def row_max(src: Buffer, dst: Buffer) -> Program:
  return _reduce(src, dst, "row_max")


def row_max_sub(src: Buffer, dst: Buffer) -> Program:
  p = Program(src.cores, src, dst)
  input_cb = p.cb(src.dtype)
  reduced_cb = p.cb.internal("row_max_sub.reduced", src.dtype, depth=1)
  output_cb = p.cb(dst.dtype)
  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.ops.row_max(input_cb, reduced_cb, dst_tile=0)
  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.unpack.move_pair(input_cb, reduced_cb)
  p.fpu.sub(dst_tile=0, broadcast=Broadcast.COLUMN).publish()
  p.pack.move(output_cb, tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def _expected(values):
  sums = np.zeros(SHAPE, dtype=np.float32)
  maxima = np.zeros(SHAPE, dtype=np.float32)
  minima = np.zeros(SHAPE, dtype=np.float32)
  row_sums = np.zeros(SHAPE, dtype=np.float32)
  row_maxima = np.zeros(SHAPE, dtype=np.float32)
  sums[0, 0] = np.sum(values, dtype=np.float32)
  maxima[0, 0] = np.max(values)
  minima[0, 0] = np.min(values)
  row_sums[:, 0] = np.sum(values, axis=1, dtype=np.float32)
  row_maxima[:, 0] = np.max(values, axis=1)
  return {
    "sum": sums,
    "max": maxima,
    "min": minima,
    "row_sum": row_sums,
    "row_max": row_maxima,
  }


def _tile_bytes(buffer, values):
  return buffer.tile_data(buffer.from_numpy(values))


def _read_tile(device, buffer):
  return buffer.to_numpy(buffer.tile_data(device.read(buffer), inverse=True))


def run_hardware(operation):
  builders = {
    "sum": reduce_sum,
    "max": reduce_max,
    "min": reduce_min,
    "row_sum": row_sum,
    "row_max": row_max,
    "row_max_sub": row_max_sub,
  }
  if operation not in builders:
    raise ValueError(f"unknown reduction operation {operation!r}")
  device = Device()
  try:
    device.init_device()
    src = device.dram.buffer("src", DType.BF16, SHAPE)
    dst = device.dram.buffer(f"{operation}_dst", DType.BF16, SHAPE)

    rows, columns = np.indices(SHAPE)
    if operation.startswith("row_"):
      values = (2 * rows + columns / 16).astype(np.float32)
    else:
      values = ((3 * rows + 5 * columns) % 17 - 8).astype(np.float32)
    values = src.to_numpy(src.from_numpy(values))
    if operation == "row_max_sub":
      expected_values = values - np.max(values, axis=1, keepdims=True)
    else:
      expected_values = _expected(values)[operation]
    expected = dst.to_numpy(dst.from_numpy(expected_values))

    device.write(src, _tile_bytes(src, values))
    timestamps = device.run(builders[operation](src, dst))
    actual = _read_tile(device, dst)
    comparison = (
      np.array_equal(actual[:, 0], expected[:, 0])
      if operation in ("row_sum", "row_max") else
      np.array_equal(actual, expected)
    )
    if not comparison:
      error = np.abs(actual - expected)
      if operation in ("row_sum", "row_max"):
        row, column = int(error[:, 0].argmax()), 0
      else:
        row, column = np.unravel_index(int(error.argmax()), SHAPE)
      raise AssertionError(
        f"{operation} mismatch at ({row}, {column}): "
        f"actual={actual[row, column]} expected={expected[row, column]}; "
        f"nonzero={np.argwhere(actual)} values={actual[actual != 0]}"
      )

    print(f"PASS reduce_{operation}")
    print(f"kernel: {timestamps[-1].us:.3f} us")
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--operation",
    choices=("sum", "max", "min", "row_sum", "row_max", "row_max_sub"),
    required=True,
  )
  run_hardware(parser.parse_args().operation)
