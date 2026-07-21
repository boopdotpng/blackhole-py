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
  p.sfpu.map(sfpu_program, tile=0, region=region)
  p.fpu.publish()

  p.pack.move(output_cb, tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


def sfpu_offset_pair(src: Buffer, dst: Buffer) -> Program:
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
  p.sfpu.map(program, tile=0)
  p.fpu.publish()

  p.pack.move(output_cb, tile=1)
  p.ncrisc.noc.write_from_cb(output_cb, dst, 0)
  return p


CASE_CONFIG = {
  "identity": ("identity", "tile", EXACT_INPUT, lambda x: x, True, False),
  "load_float": ("load_float", "tile", EXACT_INPUT, lambda x: np.full_like(x, 1.5), True, False),
  "constant": ("constant", "tile", EXACT_INPUT, lambda x: x + 1.5, True, False),
  "move": ("move", "tile", EXACT_INPUT, lambda x: x, True, False),
  "add": ("add", "tile", EXACT_INPUT, lambda x: x + 2, True, False),
  "sub": ("sub", "tile", EXACT_INPUT, lambda x: x - 2, True, False),
  "mul": ("mul", "tile", EXACT_INPUT, lambda x: x * 2, True, False),
  "mad": ("mad", "tile", EXACT_INPUT, lambda x: x * 2 + 1, True, False),
  "mad_negate_product": ("mad_negate_product", "tile", EXACT_INPUT, lambda x: -x * 2 + 1, True, False),
  "mad_negate_addend": ("mad_negate_addend", "tile", EXACT_INPUT, lambda x: x * 2 - 1, True, False),
  "add_scalar": ("add_scalar", "tile", EXACT_INPUT, lambda x: x + 1, True, False),
  "out_of_place": ("out_of_place", "tile", EXACT_INPUT, lambda x: x + 1, True, False),
  "mul_scalar": ("mul_scalar", "tile", EXACT_INPUT, lambda x: x * 2, True, False),
  "long_inline": ("long_inline", "tile", EXACT_INPUT, lambda x: x, True, False),
  "neg": ("neg", "tile", EXACT_INPUT, lambda x: -x, True, False),
  "fp32_add": ("add_scalar", "tile", EXACT_INPUT, lambda x: x + 1, True, True),
  "map_row": ("add_scalar", "row", EXACT_INPUT, lambda x: x + 1, True, False),
  "map_column": ("add_scalar", "column", EXACT_INPUT, lambda x: x + 1, True, False),
  "exp": ("exp", "tile", EXP_INPUT, np.exp, False, False),
  "reciprocal": ("reciprocal", "tile", POSITIVE_INPUT, lambda x: 1 / x, False, False),
  "rsqrt_positive": ("rsqrt_positive", "tile", POSITIVE_INPUT, lambda x: 1 / np.sqrt(x), False, False),
}
CASES = (*CASE_CONFIG, "offset_pair")


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


def _read_tile(readback, buffer):
  logical = buffer.tile_data(readback.result(), inverse=True)
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


def _queue_offset_pair(device):
  src = device.dram.buffer("sfpu_pair_src", DType.BF16, (1, 32, 64), axis=0)
  dst = device.dram.buffer("sfpu_pair_dst", DType.BF16, (1, 32, 32), axis=0)
  left = EXACT_INPUT
  right = np.flip(EXACT_INPUT, axis=1).copy() / 2.0
  values = np.concatenate((left.reshape(-1), right.reshape(-1))).reshape(src.shape)
  source = _quantize(src, values)
  expected = _quantize(dst, left + right)
  device.write(src, src.tile_data(src.from_numpy(source)))
  device.queue(sfpu_offset_pair(src, dst))
  return dst, device.queue_read(dst), expected[0], True, True


def run_hardware(case_names=CASES):
  device = Device()
  failures = []
  try:
    device.init_device()
    jobs = []
    for name in case_names:
      if name == "offset_pair":
        jobs.append((name, *_queue_offset_pair(device)))
        continue

      src = device.dram.buffer(f"sfpu_{name}_src", DType.BF16, SHAPE)
      dst = device.dram.buffer(f"sfpu_{name}_dst", DType.BF16, SHAPE)
      operation, region, inputs, reference, exact, fp32_dst = CASE_CONFIG[name]
      source = _quantize(src, inputs)
      transformed = reference(source)
      expected = _quantize(dst, _apply_region(source, transformed, region))
      _write_tile(device, src, source)
      device.queue(sfpu_operation(src, dst, operation, region, fp32_dst))
      jobs.append((name, dst, device.queue_read(dst), expected, exact, False))

    timestamps = device.run()
    for timestamp, (name, dst, readback, expected, exact, first) in zip(timestamps, jobs):
      try:
        actual = _read_tile(readback, dst)
        if first: actual = actual[0]
        _check(name, actual, expected, exact)
        print(f"PASS {name}: {timestamp.us:.3f} us")
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
