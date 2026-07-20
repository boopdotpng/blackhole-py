import argparse
import numpy as np

from device import Device
from program import Buffer, DType, Program


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


def _expected(values):
  sums = np.zeros(SHAPE, dtype=np.float32)
  maxima = np.zeros(SHAPE, dtype=np.float32)
  minima = np.zeros(SHAPE, dtype=np.float32)
  sums[0, 0] = np.sum(values, dtype=np.float32)
  maxima[0, 0] = np.max(values)
  minima[0, 0] = np.min(values)
  return {"sum": sums, "max": maxima, "min": minima}


def _tile_bytes(buffer, values):
  return buffer.from_numpy(values)


def _read_tile(device, buffer):
  return buffer.to_numpy(device.read(buffer))


def run_hardware(operation):
  builders = {"sum": reduce_sum, "max": reduce_max, "min": reduce_min}
  if operation not in builders:
    raise ValueError("operation must be 'sum', 'max', or 'min'")
  device = Device()
  try:
    device.init_device()
    src = device.dram.buffer("src", DType.BF16, SHAPE)
    dst = device.dram.buffer(f"{operation}_dst", DType.BF16, SHAPE)

    rows, columns = np.indices(SHAPE)
    values = ((3 * rows + 5 * columns) % 17 - 8).astype(np.float32)
    values = src.to_numpy(src.from_numpy(values))
    expected = dst.to_numpy(dst.from_numpy(_expected(values)[operation]))

    device.write(src, _tile_bytes(src, values))
    timestamps = device.run(builders[operation](src, dst))
    actual = _read_tile(device, dst)
    if not np.array_equal(actual, expected):
      error = np.abs(actual - expected)
      row, column = np.unravel_index(int(error.argmax()), SHAPE)
      raise AssertionError(
        f"{operation} mismatch at ({row}, {column}): "
        f"actual={actual[row, column]} expected={expected[row, column]}"
      )

    print(f"PASS reduce_{operation}")
    print(f"kernel: {timestamps[-1].us:.3f} us")
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--operation", choices=("sum", "max", "min"), required=True,
  )
  run_hardware(parser.parse_args().operation)
