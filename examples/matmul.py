import argparse
import numpy as np

from device import Device
from program import Buffer, DType, Program


SHAPE = (32, 32)


def matmul(left: Buffer, right: Buffer, output: Buffer, *,
           right_transpose=False) -> Program:
  buffers = (left, right, output)
  if left.dtype is not DType.BF16 or right.dtype is not DType.BF16:
    raise ValueError("matmul example requires BF16 inputs")
  if output.dtype not in (DType.BF16, DType.F32):
    raise ValueError("matmul example requires a BF16 or F32 output")
  if any(buffer.shape != SHAPE or buffer.tiles != 1 for buffer in buffers):
    raise ValueError(f"matmul example requires one {SHAPE} tile per buffer")
  if any(buffer.cores != left.cores for buffer in buffers[1:]):
    raise ValueError("matmul example buffers must use the same core")

  p = Program(left.cores, *buffers)
  left_cb, right_cb = p.cb(left.dtype), p.cb(right.dtype)
  output_cb = p.cb(output.dtype)

  p.brisc.noc.read_into_cb(left, 0, left_cb)
  p.brisc.noc.read_into_cb(right, 0, right_cb)

  p.unpack.move_matmul(
    left_cb, right_cb, right_transpose=right_transpose,
  )
  p.fpu.matmul(
    dst_tile=0, right_transpose=right_transpose,
  ).publish()
  p.pack.move(output_cb, tile=0)

  p.ncrisc.noc.write_from_cb(output_cb, output, 0)
  return p


def _quality(actual, expected):
  actual = actual.astype(np.float32, copy=False).reshape(-1)
  expected = expected.astype(np.float32, copy=False).reshape(-1)
  relative_l2 = float(
    np.linalg.norm(actual - expected) / (np.linalg.norm(expected) + 1e-12)
  )
  pcc = float(np.corrcoef(actual, expected)[0, 1])
  return pcc, relative_l2


_FIDELITY_MASKS = (
  (0b11111000000, 0b11111110000),
  (0b00000111110, 0b11111110000),
)


def _fidelity_part(values, mask):
  bits = values.astype(np.float32, copy=False).view(np.uint32)
  bf16 = bits >> 16
  exponent = ((bf16 >> 7) & 0xFF).astype(np.int32) - 127
  mantissa = (((bf16 & 0x7F) << 3) | 0x400) & mask
  magnitude = np.ldexp(mantissa.astype(np.float32) / 1024.0, exponent)
  return np.where(bf16 >> 15, -magnitude, magnitude)


def _fidelity_reference(left, right):
  result = np.zeros(SHAPE, dtype=np.float32)
  for srca_mask, srcb_mask in _FIDELITY_MASKS:
    # MVMUL computes SrcB @ SrcA: left is SrcB and right is SrcA.
    result += (
      _fidelity_part(left, srcb_mask) @
      _fidelity_part(right, srca_mask)
    )
  return result


def run_hardware(*, f32_output=False, right_transpose=False):
  device = Device()
  try:
    device.init_device()
    left = device.dram.buffer("left", DType.BF16, SHAPE)
    right = device.dram.buffer("right", DType.BF16, SHAPE)
    output_dtype = DType.F32 if f32_output else DType.BF16
    output = device.dram.buffer("output", output_dtype, SHAPE)

    rng = np.random.default_rng(0)
    left_values = rng.uniform(-0.25, 0.25, size=SHAPE).astype(np.float32)
    right_values = rng.uniform(-0.25, 0.25, size=SHAPE).astype(np.float32)
    left_data, right_data = (
      left.from_numpy(left_values), right.from_numpy(right_values),
    )
    left_reference = left.to_numpy(left_data)
    right_reference = right.to_numpy(right_data)
    exact = left_reference @ (
      right_reference.T if right_transpose else right_reference
    )
    fidelity_expected = _fidelity_reference(
      left_reference,
      right_reference.T if right_transpose else right_reference,
    )

    device.write(left, left_data)
    device.write(right, right_data)
    device.queue(matmul(
      left, right, output, right_transpose=right_transpose,
    ))
    readback = device.queue_read(output)
    timestamps = device.run(timeout=5.0)
    actual = output.to_numpy(readback.result())

    pcc, relative_l2 = _quality(actual, exact)
    model_pcc, model_relative_l2 = _quality(actual, fidelity_expected)
    minimum_pcc = 0.9999
    maximum_relative_l2 = 0.01
    maximum_model_relative_l2 = 0.0005 if f32_output else maximum_relative_l2
    if (
      not np.all(np.isfinite(actual)) or
      pcc < minimum_pcc or relative_l2 > maximum_relative_l2
      or model_relative_l2 > maximum_model_relative_l2
    ):
      error = np.abs(actual - fidelity_expected)
      row, column = np.unravel_index(int(error.argmax()), SHAPE)
      raise AssertionError(
        f"matmul mismatch at ({row}, {column}): "
        f"actual={actual[row, column]} "
        f"fidelity_expected={fidelity_expected[row, column]}; "
        f"model PCC={model_pcc:.6f} "
        f"model relative L2={model_relative_l2:.6f}"
      )

    print("PASS matmul")
    print("fidelity: HiFi2")
    print("accumulation: FP32")
    print(f"output: {'F32' if f32_output else 'BF16'}")
    print(f"right transpose: {right_transpose}")
    print(f"kernel: {timestamps[-1].us:.3f} us")
    print(f"exact PCC: {pcc:.6f}")
    print(f"exact relative L2: {relative_l2:.6f}")
    print(f"fidelity-model PCC: {model_pcc:.6f}")
    print(f"fidelity-model relative L2: {model_relative_l2:.6f}")
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--f32-output", action="store_true")
  parser.add_argument("--transpose-right", action="store_true")
  args = parser.parse_args()
  run_hardware(
    f32_output=args.f32_output, right_transpose=args.transpose_right,
  )
