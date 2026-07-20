"""Hardware validation suite for the public SFPU program-builder operations."""

import argparse

import numpy as np

from device import Device
from program import Buffer, DType, Program
from ttk.sfpu import SfpuFormat
from ttk.unpack import UnpackTarget


SHAPE = (32, 32)
EXACT_INPUT = (
  (np.arange(1024, dtype=np.float32) % 65) - 32
).reshape(SHAPE) / 4
EXP_INPUT = np.linspace(-8.0, 5.0, 1024, dtype=np.float32).reshape(SHAPE)
POSITIVE_INPUT = np.geomspace(0.25, 64.0, 1024).astype(np.float32).reshape(SHAPE)


def _build_body(builder, operation, format):
  value = builder.load(format=format)

  if operation == "identity":
    result = value
  elif operation == "load_float":
    result = builder.load_float(1.5, into=value)
  elif operation == "constant":
    constant = builder.constant(1.5)
    result = builder.add(value, constant, into=value)
  elif operation == "move":
    result = builder.move(value)
    builder.free(value)
  elif operation in ("add", "sub", "mul"):
    constant = builder.load_float(2.0)
    result = getattr(builder, operation)(value, constant, into=value)
    builder.free(constant)
  elif operation == "mad":
    two = builder.load_float(2.0)
    one = builder.load_float(1.0)
    result = builder.mad(value, two, one, into=value)
    builder.free(two)
    builder.free(one)
  elif operation in ("mad_negate_product", "mad_negate_addend"):
    two = builder.load_float(2.0)
    one = builder.load_float(1.0)
    result = builder.mad(
      value, two, one, into=value,
      negate_product=operation == "mad_negate_product",
      negate_addend=operation == "mad_negate_addend",
    )
    builder.free(two)
    builder.free(one)
  elif operation == "add_scalar":
    result = builder.add_scalar(value, 1.0)
  elif operation == "out_of_place":
    result = builder.add_scalar(value, 1.0, into=builder.vec("result"))
    builder.free(value)
  elif operation == "mul_scalar":
    result = builder.mul_scalar(value, 2.0)
  elif operation == "long_inline":
    result = value
    for _ in range(17):
      result = builder.add_scalar(result, 0.0)
  elif operation == "neg":
    result = builder.neg(value, into=value)
  elif operation == "exp":
    result = builder.exp(value, into=value)
  elif operation == "reciprocal":
    result = builder.reciprocal(value, into=value)
  elif operation == "rsqrt_positive":
    result = builder.rsqrt_positive(value, into=value)
  else:
    raise ValueError(f"unknown SFPU operation {operation!r}")

  builder.store(result, format=format)
  return builder.finish()


def sfpu_operation(src: Buffer, dst: Buffer, operation: str,
                   region="tile", fp32_dst=False) -> Program:
  if src.dtype is not DType.BF16 or dst.dtype is not DType.BF16:
    raise ValueError("SFPU operation suite requires BF16 buffers")
  if src.shape != SHAPE or dst.shape != SHAPE:
    raise ValueError(f"SFPU operation suite requires one {SHAPE} tile")
  if src.cores != dst.cores:
    raise ValueError("source and destination must use the same cores")
  if region not in ("tile", "row", "column"):
    raise ValueError("region must be tile, row, or column")

  p = Program(src.cores, src, dst, fp32_dst=fp32_dst)
  input_cb, output_cb = p.cb(src.dtype), p.cb(dst.dtype)
  format = SfpuFormat.FP32 if fp32_dst else SfpuFormat.BF16
  sfpu_program = _build_body(p.sfpu.program(), operation, format)

  p.brisc.noc.read_into_cb(src, 0, input_cb)
  p.unpack.move(input_cb, UnpackTarget.SRCA)

  p.fpu.copy_a(dst_tile=0)
  getattr(p.sfpu, f"map_{region}")(sfpu_program, tile=0)
  p.fpu.publish()

  p.pack.move(output_cb, tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def sfpu_offset_pair(src: Buffer, dst: Buffer) -> Program:
  """Add two Dst tiles using offset 64 and store into the second tile."""
  p = Program(src.cores, src, dst)
  input_cb, output_cb = p.cb(src.dtype), p.cb(dst.dtype)

  builder = p.sfpu.program()
  left = builder.load(format=SfpuFormat.BF16, offset=0)
  right = builder.load(format=SfpuFormat.BF16, offset=64)
  builder.add(left, right, into=left)
  builder.store(left, format=SfpuFormat.BF16, offset=64)
  program = builder.finish()

  for tile in p.brisc.range(2):
    p.brisc.noc.read_into_cb(src, tile, input_cb)
  for _ in p.trisc0.range(2):
    p.unpack.move(input_cb, UnpackTarget.SRCA)

  p.fpu.copy_a(dst_tile=0)
  p.fpu.copy_a(dst_tile=1)
  p.sfpu.map_tile(program, tile=0)
  p.fpu.publish()

  p.pack.move(output_cb, tile=1)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def _case(name):
  if name == "load_float":
    return "load_float", "tile", EXACT_INPUT, lambda x: np.full_like(x, 1.5), True, False
  if name == "constant":
    return "constant", "tile", EXACT_INPUT, lambda x: x + 1.5, True, False
  if name == "move":
    return "move", "tile", EXACT_INPUT, lambda x: x, True, False
  if name == "add":
    return "add", "tile", EXACT_INPUT, lambda x: x + 2.0, True, False
  if name == "sub":
    return "sub", "tile", EXACT_INPUT, lambda x: x - 2.0, True, False
  if name == "mul":
    return "mul", "tile", EXACT_INPUT, lambda x: x * 2.0, True, False
  if name == "mad":
    return "mad", "tile", EXACT_INPUT, lambda x: x * 2.0 + 1.0, True, False
  if name == "mad_negate_product":
    return "mad_negate_product", "tile", EXACT_INPUT, lambda x: -x * 2.0 + 1.0, True, False
  if name == "mad_negate_addend":
    return "mad_negate_addend", "tile", EXACT_INPUT, lambda x: x * 2.0 - 1.0, True, False
  if name == "add_scalar":
    return "add_scalar", "tile", EXACT_INPUT, lambda x: x + 1.0, True, False
  if name == "out_of_place":
    return "out_of_place", "tile", EXACT_INPUT, lambda x: x + 1.0, True, False
  if name == "mul_scalar":
    return "mul_scalar", "tile", EXACT_INPUT, lambda x: x * 2.0, True, False
  if name == "long_inline":
    return "long_inline", "tile", EXACT_INPUT, lambda x: x, True, False
  if name == "neg":
    return "neg", "tile", EXACT_INPUT, lambda x: -x, True, False
  if name == "fp32_add":
    return "add_scalar", "tile", EXACT_INPUT, lambda x: x + 1.0, True, True
  if name == "exp":
    return "exp", "tile", EXP_INPUT, np.exp, False, False
  if name == "reciprocal":
    return "reciprocal", "tile", POSITIVE_INPUT, lambda x: 1.0 / x, False, False
  if name == "rsqrt_positive":
    return "rsqrt_positive", "tile", POSITIVE_INPUT, lambda x: 1.0 / np.sqrt(x), False, False
  if name == "map_row":
    return "add_scalar", "row", EXACT_INPUT, lambda x: x + 1.0, True, False
  if name == "map_column":
    return "add_scalar", "column", EXACT_INPUT, lambda x: x + 1.0, True, False
  if name == "identity":
    return "identity", "tile", EXACT_INPUT, lambda x: x, True, False
  raise ValueError(f"unknown SFPU hardware case {name!r}")


CASES = (
  "identity",
  "load_float",
  "constant",
  "move",
  "add",
  "sub",
  "mul",
  "mad",
  "mad_negate_product",
  "mad_negate_addend",
  "add_scalar",
  "out_of_place",
  "mul_scalar",
  "neg",
  "fp32_add",
  "map_row",
  "map_column",
  "exp",
  "reciprocal",
  "rsqrt_positive",
  "long_inline",
  "offset_pair",
)


def _quantize(buffer, values):
  return buffer.to_numpy(buffer.from_numpy(np.asarray(values, dtype=np.float32)))


def _apply_region(source, transformed, region):
  if region == "tile": return transformed
  expected = source.copy()
  if region == "row": expected[:16, :] = transformed[:16, :]
  else: expected[::2, :] = transformed[::2, :]
  return expected


def _write_tile(device, buffer, values):
  device.write(buffer, buffer.tile_data(buffer.from_numpy(values)))


def _read_tile(device, buffer):
  logical = buffer.tile_data(device.read(buffer), inverse=True)
  return buffer.to_numpy(logical)


def _check(name, actual, expected, exact):
  if exact:
    matches = np.array_equal(actual, expected)
  else:
    matches = np.allclose(actual, expected, rtol=0.01, atol=0.001)
  if matches: return

  error = np.abs(actual - expected)
  row, column = np.unravel_index(int(error.argmax()), SHAPE)
  relative = error[row, column] / max(abs(expected[row, column]), 1e-30)
  raise AssertionError(
    f"{name} mismatch at ({row}, {column}): "
    f"actual={actual[row, column]} expected={expected[row, column]} "
    f"abs_error={error[row, column]} relative_error={relative}"
  )


def _run_offset_pair(device):
  src = device.dram.buffer("sfpu_pair_src", DType.BF16, (1, 32, 64), axis=0)
  dst = device.dram.buffer("sfpu_pair_dst", DType.BF16, (1, 32, 32), axis=0)
  left = EXACT_INPUT
  right = np.flip(EXACT_INPUT, axis=1).copy() / 2.0
  values = np.concatenate((left.reshape(-1), right.reshape(-1))).reshape(src.shape)
  source = _quantize(src, values)
  expected = _quantize(dst, left + right)
  device.write(src, src.tile_data(src.from_numpy(source)))
  timestamps = device.run(sfpu_offset_pair(src, dst))
  actual = dst.to_numpy(dst.tile_data(device.read(dst), inverse=True))[0]
  _check("offset_pair", actual, expected[0], exact=True)
  return timestamps


def run_hardware(case_names=CASES):
  device = Device()
  failures = []
  try:
    device.init_device()
    src = device.dram.buffer("sfpu_src", DType.BF16, SHAPE)
    dst = device.dram.buffer("sfpu_dst", DType.BF16, SHAPE)

    for name in case_names:
      if name == "offset_pair":
        try:
          timestamps = _run_offset_pair(device)
          print(f"PASS {name}: {timestamps[-1].us:.3f} us")
        except AssertionError as error:
          failures.append(str(error))
          print(f"FAIL {error}")
        continue

      operation, region, inputs, reference, exact, fp32_dst = _case(name)
      source = _quantize(src, inputs)
      transformed = reference(source)
      expected = _quantize(dst, _apply_region(source, transformed, region))
      _write_tile(device, src, source)

      try:
        timestamps = device.run(
          sfpu_operation(src, dst, operation, region, fp32_dst),
        )
        actual = _read_tile(device, dst)
        _check(name, actual, expected, exact)
        print(f"PASS {name}: {timestamps[-1].us:.3f} us")
      except AssertionError as error:
        failures.append(str(error))
        print(f"FAIL {error}")
  finally:
    device.close()

  if failures:
    raise AssertionError(
      f"{len(failures)} SFPU hardware case(s) failed:\n" +
      "\n".join(failures)
    )


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--operation", choices=("all", *CASES), default="all",
  )
  args = parser.parse_args()
  selected = CASES if args.operation == "all" else (args.operation,)
  run_hardware(selected)
