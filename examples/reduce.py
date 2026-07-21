import argparse
import numpy as np

from device import Device
from program import Buffer, DType, Program
from ttk.sfpu import SfpuFormat


SHAPE = (32, 32)
REDUCTIONS = ("sum", "max", "min", "row_sum", "row_max")
OPERATIONS = (*REDUCTIONS, "row_max_sub", "row_add", "row_mul",
              "row_sum_pair", "row_max_pair", "row_sum_sfpu")
ROW_OUTPUTS = ("row_sum", "row_max", "row_sum_pair", "row_max_pair", "row_sum_sfpu")


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

  if operation == "min": p.ops.reduce_min(input_cb, output_cb)
  elif operation.startswith("row_"):
    p.ops.reduce_rows(input_cb, output_cb, maximum=operation == "row_max")
  else: p.ops.reduce(input_cb, output_cb, maximum=operation == "max")
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def row_max_sub(src: Buffer, dst: Buffer) -> Program:
  p = Program(src.cores, src, dst, fp32_dst=True)
  input_cb = p.cb(src.dtype)
  reduced_cb = p.cb.internal("row_max_sub.reduced", src.dtype, depth=1)
  output_cb = p.cb(dst.dtype)
  # Keep a second copy queued for the direct data-minus-row-values operation.
  # The row maximum is never expanded into a full broadcast tile.
  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.ops.reduce_rows(input_cb, reduced_cb, maximum=True)
  p.ops.binary_rows(input_cb, reduced_cb, output_cb, operation="sub")
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def row_binary(src: Buffer, rows: Buffer, dst: Buffer, operation: str) -> Program:
  p = Program(src.cores, src, rows, dst, fp32_dst=True)
  input_cb = p.cb(src.dtype)
  rows_cb = p.cb(rows.dtype)
  output_cb = p.cb(dst.dtype)
  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.brisc.noc.read_into_cb(rows, 0, rows_cb)
  p.ops.binary_rows(input_cb, rows_cb, output_cb, operation=operation)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def row_pair(left: Buffer, right: Buffer, dst: Buffer, *, maximum) -> Program:
  p = Program(left.cores, left, right, dst, fp32_dst=True)
  input_cb = p.cb(left.dtype)
  output_cb = p.cb(dst.dtype)
  p.brisc.noc.read_into_cb(left, 0, input_cb)
  p.brisc.noc.read_into_cb(right, 0, input_cb)
  p.ops.accumulate_rows(input_cb, maximum=maximum)
  p.ops.accumulate_rows(input_cb, maximum=maximum)
  p.ops.store_row_values(output_cb, dst_tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def row_sum_sfpu(src: Buffer, dst: Buffer) -> Program:
  p = Program(src.cores, src, dst, fp32_dst=True)
  input_cb = p.cb(src.dtype)
  output_cb = p.cb(dst.dtype)

  builder = p.sfpu.program()
  value = builder.load(format=SfpuFormat.FP32)
  builder.add_scalar(value, 1.0)
  builder.store(value, format=SfpuFormat.FP32)
  sfpu_program = builder.finish()

  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.ops.accumulate_rows(input_cb)
  p.sfpu.map(sfpu_program, tile=0, region="column")
  p.ops.store_row_values(output_cb, dst_tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def _expected(values, operation):
  expected = np.zeros(SHAPE, dtype=np.float32)
  if operation == "sum": expected[0, 0] = np.sum(values, dtype=np.float32)
  elif operation == "max": expected[0, 0] = np.max(values)
  elif operation == "min": expected[0, 0] = np.min(values)
  elif operation == "row_sum": expected[:, 0] = np.sum(values, axis=1, dtype=np.float32)
  elif operation == "row_max": expected[:, 0] = np.max(values, axis=1)
  else: raise ValueError(f"unknown reduction {operation!r}")
  return expected


def run_hardware(operation):
  if operation not in OPERATIONS:
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
      expected_values = _expected(values, "row_sum")
      expected_values[:, 0] += 1.0
    else:
      expected_values = _expected(values, operation)
    expected = dst.to_numpy(dst.from_numpy(expected_values))

    device.write(src, src.from_numpy(values))
    if operation in ("row_add", "row_mul"):
      row_buffer = device.dram.buffer("row_values", DType.BF16, SHAPE)
      device.write(row_buffer, row_buffer.from_numpy(row_values))
      program = row_binary(src, row_buffer, dst, operation.removeprefix("row_"))
    elif operation in ("row_sum_pair", "row_max_pair"):
      right = device.dram.buffer("right", DType.BF16, SHAPE)
      device.write(right, right.from_numpy(right_values))
      program = row_pair(src, right, dst, maximum=operation == "row_max_pair")
    elif operation == "row_sum_sfpu":
      program = row_sum_sfpu(src, dst)
    elif operation == "row_max_sub":
      program = row_max_sub(src, dst)
    else:
      program = _reduce(src, dst, operation)
    device.queue(program)
    readback = device.queue_read(dst)
    timestamps = device.run()
    actual = dst.to_numpy(readback.result())
    comparison = (
      np.array_equal(actual[:, 0], expected[:, 0])
      if operation in ROW_OUTPUTS else
      np.array_equal(actual, expected)
    )
    if not comparison:
      error = np.abs(actual - expected)
      if operation in ROW_OUTPUTS:
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
    choices=OPERATIONS,
    required=True,
  )
  run_hardware(parser.parse_args().operation)
