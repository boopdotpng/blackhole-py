import argparse
import numpy as np

from device import Device
from program import Buffer, DType, Program
from ttk.sfpu import SfpuFormat


SHAPE = (32, 32)


def _reduce(src: Buffer, dst: Buffer, operation: str) -> Program:
  buffers = (src, dst)
  if any(buffer.dtype is not DType.BF16 for buffer in buffers):
    raise ValueError("reduce example requires BF16 buffers")
  if any(buffer.shape != SHAPE or buffer.tiles != 1 for buffer in buffers):
    raise ValueError(f"reduce example requires one {SHAPE} tile per buffer")
  if any(buffer.cores != src.cores for buffer in buffers[1:]):
    raise ValueError("reduce example buffers must use the same cores")

  p = Program(src.cores, *buffers, fp32_dst=True)
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
  p = Program(src.cores, src, dst, fp32_dst=True)
  input_cb = p.cb(src.dtype)
  reduced_cb = p.cb.internal("row_max_sub.reduced", src.dtype, depth=1)
  output_cb = p.cb(dst.dtype)
  # Keep a second copy queued for the direct data-minus-row-values operation.
  # The row maximum is never expanded into a full broadcast tile.
  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.ops.row_max(input_cb, reduced_cb, dst_tile=0)
  p.ops.sub_rows(input_cb, reduced_cb, output_cb, dst_tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def row_binary(src: Buffer, rows: Buffer, dst: Buffer, operation: str) -> Program:
  p = Program(src.cores, src, rows, dst, fp32_dst=True)
  input_cb = p.cb(src.dtype)
  rows_cb = p.cb(rows.dtype)
  output_cb = p.cb(dst.dtype)
  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.brisc.noc.read_into_cb(rows, 0, rows_cb)
  getattr(p.ops, f"{operation}_rows")(
    input_cb, rows_cb, output_cb, dst_tile=0,
  )
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def row_sum_pair(left: Buffer, right: Buffer, dst: Buffer) -> Program:
  p = Program(left.cores, left, right, dst, fp32_dst=True)
  input_cb = p.cb(left.dtype)
  output_cb = p.cb(dst.dtype)
  p.brisc.noc.read_into_cb(left, 0, input_cb)
  p.brisc.noc.read_into_cb(right, 0, input_cb)
  p.ops.accumulate_row_sum(input_cb, dst_tile=0)
  p.ops.accumulate_row_sum(input_cb, dst_tile=0)
  p.ops.store_row_values(output_cb, dst_tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def row_max_pair(left: Buffer, right: Buffer, dst: Buffer) -> Program:
  p = Program(left.cores, left, right, dst, fp32_dst=True)
  input_cb = p.cb(left.dtype)
  output_cb = p.cb(dst.dtype)
  p.brisc.noc.read_into_cb(left, 0, input_cb)
  p.brisc.noc.read_into_cb(right, 0, input_cb)
  p.ops.accumulate_row_max(input_cb, dst_tile=0)
  p.ops.accumulate_row_max(input_cb, dst_tile=0)
  p.ops.store_row_values(output_cb, dst_tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def row_sum_sfpu(src: Buffer, dst: Buffer) -> Program:
  """Reduce rows, transform the 32 live FP32 values with SFPU, then pack."""
  p = Program(src.cores, src, dst, fp32_dst=True)
  input_cb = p.cb(src.dtype)
  output_cb = p.cb(dst.dtype)

  builder = p.sfpu.program()
  value = builder.load(format=SfpuFormat.FP32)
  builder.add_scalar(value, 1.0)
  builder.store(value, format=SfpuFormat.FP32)
  sfpu_program = builder.finish()

  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.ops.accumulate_row_sum(input_cb, dst_tile=0)
  p.sfpu.map_row_values(sfpu_program, tile=0)
  p.ops.store_row_values(output_cb, dst_tile=0)
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
  return buffer.from_numpy(values)


def _read_tile(device, buffer):
  return buffer.to_numpy(device.read(buffer))


def run_hardware(operation):
  builders = {
    "sum": reduce_sum,
    "max": reduce_max,
    "min": reduce_min,
    "row_sum": row_sum,
    "row_max": row_max,
    "row_max_sub": row_max_sub,
    "row_add": None,
    "row_mul": None,
    "row_sum_pair": None,
    "row_max_pair": None,
    "row_sum_sfpu": row_sum_sfpu,
  }
  if operation not in builders:
    raise ValueError(f"unknown reduction operation {operation!r}")
  device = Device()
  try:
    device.init_device()
    src = device.dram.buffer("src", DType.BF16, SHAPE)
    dst = device.dram.buffer(f"{operation}_dst", DType.BF16, SHAPE)

    rows, columns = np.indices(SHAPE)
    if operation == "row_mul":
      # Keep the structural broadcast test exact under LoFi FPU multiply.
      values = (
        (rows % 7) - 3 + (columns % 4) / 4
      ).astype(np.float32)
    elif operation.startswith("row_"):
      # Negative-only maxima verify that an invalid Dst row behaves as -inf.
      values = (2 * rows + columns / 16 - 128).astype(np.float32)
    else:
      values = ((3 * rows + 5 * columns) % 17 - 8).astype(np.float32)
    values = src.to_numpy(src.from_numpy(values))
    if operation == "row_max_sub":
      expected_values = values - np.max(values, axis=1, keepdims=True)
    elif operation in ("row_add", "row_mul"):
      row_values = np.zeros(SHAPE, dtype=np.float32)
      row_values[:, 0] = (
        np.where(rows[:, 0] % 2, 2.0, 0.5)
        if operation == "row_mul" else
        np.arange(1, 33, dtype=np.float32) / 4
      )
      vector = row_values[:, :1]
      expected_values = (
        values + vector if operation == "row_add" else values * vector
      )
    elif operation in ("row_sum_pair", "row_max_pair"):
      right_values = (-rows + columns / 8 + 16).astype(np.float32)
      expected_values = np.zeros(SHAPE, dtype=np.float32)
      if operation == "row_sum_pair":
        expected_values[:, 0] = (
          np.sum(values, axis=1, dtype=np.float32) +
          np.sum(right_values, axis=1, dtype=np.float32)
        )
      else:
        expected_values[:, 0] = np.maximum(
          np.max(values, axis=1), np.max(right_values, axis=1),
        )
    elif operation == "row_sum_sfpu":
      expected_values = _expected(values)["row_sum"]
      expected_values[:, 0] += 1.0
    else:
      expected_values = _expected(values)[operation]
    expected = dst.to_numpy(dst.from_numpy(expected_values))

    device.write(src, _tile_bytes(src, values))
    if operation in ("row_add", "row_mul"):
      row_buffer = device.dram.buffer("row_values", DType.BF16, SHAPE)
      device.write(row_buffer, _tile_bytes(row_buffer, row_values))
      program = row_binary(src, row_buffer, dst, operation.removeprefix("row_"))
    elif operation in ("row_sum_pair", "row_max_pair"):
      right = device.dram.buffer("right", DType.BF16, SHAPE)
      device.write(right, _tile_bytes(right, right_values))
      program = (
        row_sum_pair(src, right, dst)
        if operation == "row_sum_pair" else
        row_max_pair(src, right, dst)
      )
    else:
      program = builders[operation](src, dst)
    timestamps = device.run(program)
    actual = _read_tile(device, dst)
    comparison = (
      np.array_equal(actual[:, 0], expected[:, 0])
      if operation in (
        "row_sum", "row_max", "row_sum_pair", "row_max_pair",
        "row_sum_sfpu",
      ) else
      np.array_equal(actual, expected)
    )
    if not comparison:
      error = np.abs(actual - expected)
      if operation in (
        "row_sum", "row_max", "row_sum_pair", "row_max_pair",
        "row_sum_sfpu",
      ):
        row, column = int(error[:, 0].argmax()), 0
      else:
        row, column = np.unravel_index(int(error.argmax()), SHAPE)
      raise AssertionError(
        f"{operation} mismatch at ({row}, {column}): "
        f"actual={actual[row, column]} expected={expected[row, column]}; "
        f"column0={actual[:, 0].tolist()}"
      )

    print(f"PASS reduce_{operation}")
    print(f"kernel: {timestamps[-1].us:.3f} us")
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--operation",
    choices=(
      "sum", "max", "min", "row_sum", "row_max", "row_max_sub",
      "row_add", "row_mul", "row_sum_pair", "row_max_pair",
      "row_sum_sfpu",
    ),
    required=True,
  )
  run_hardware(parser.parse_args().operation)
