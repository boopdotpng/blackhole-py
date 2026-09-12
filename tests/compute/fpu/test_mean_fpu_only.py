"""1024-element mean with GAPOOL for both reductions; inspect physical Dst rows.

Run with --bh-hardware -s to print the intermediate row and final scalar.
The shared emitter uses SFPU instructions only for lane configuration, never
for arithmetic here. Inputs and source round trips use TF32; Dst uses FP32.
"""
from struct import pack, unpack

import pytest
import numpy as np

from tests.compute.fpu.test_sum_finish import INPUT, WEIGHTS, OUTPUT, _images


@pytest.mark.parametrize("pattern", ("arange", "impulse"))
def test_mean_fpu_only(bh, pattern):
  values = list(map(float, range(1024))) if pattern == "arange" else [0.] * 1024
  if pattern == "impulse":
    values[37 * 16 + 11] = 1024.  # Input row 37, column 11.

  # SrcB row 0 supplies the first-stage scaling weights. Its scratch block
  # (rows 16..31) holds a column of ones for the second-stage SrcA operand.
  weights = [0.] * 1024
  weights[:16] = [1 / 1024] * 16
  for row in range(16, 32):
    weights[row * 16] = 1.

  for finish in (False, True):
    images, _ = _images("gapool", "fpu-row", finish_reduction=finish,
                        output_elements=64)
    bh.launch(images, l1={
      INPUT: pack("<1024f", *values),
      WEIGHTS: pack("<1024f", *weights),
      OUTPUT: b"\xa5" * 320,
    })
    # Packer exports physical Dst rows 0..3 in row-major order.
    actual = unpack("<64f", bh.read_l1(bh.core, OUTPUT, 256))
    expected = [0.] * 64
    if finish:
      expected[0] = sum(values) / 1024
    else:
      expected[:16] = [sum(values[c::16]) / 1024 for c in range(16)]
    assert actual == tuple(expected)
    assert bh.read_l1(bh.core, OUTPUT + 256, 64) == b"\xa5" * 64
    stage = "final mean" if finish else "scaled column sums"
    print(f"{pattern}, {stage}: Dst row 0 = {list(actual[:16])}; rows 1..3 = zero")


@pytest.mark.parametrize("pattern", ("small-increment", "cancellation", "random-positive"))
def test_mean_tf32_recopy_precision(bh, pattern):
  # Multiples of 1/512 near one are exact even in the first-stage SrcA
  # multiplier's nine fraction bits. First-stage sums also remain exact FP32.
  if pattern == "random-positive":
    rng = np.random.default_rng(20260911)
    values = (rng.integers(512, 1024, size=1024) / 512).astype(np.float32)
  elif pattern == "small-increment":
    values = np.ones(1024, dtype=np.float32)
    values[0] += 1 / 512
  else:
    values = np.zeros((64, 16), dtype=np.float32)
    values[:, 0], values[:, 1] = 1., -1.
    values[0, 0] += 1 / 512
    values = values.ravel()
  weights = np.zeros((64, 16), dtype=np.float32)
  weights[0, :] = 1 / 1024
  weights[16:32, 0] = 1.
  reference = float(values.astype(np.float64).mean())
  partials = (values.reshape(64, 16).sum(axis=0) / 1024).astype(np.float32)
  # MOVD2B truncates FP32 to TF32: retain ten fraction bits, discard thirteen.
  recopied = (partials.view(np.uint32) & np.uint32(0xffffe000)).view(np.float32)
  predicted = float(recopied.astype(np.float64).sum())
  results = {}
  for finish in ("sfpu", "fpu-row"):
    images, _ = _images("gapool", finish)
    bh.launch(images, l1={INPUT: values.tobytes(), WEIGHTS: weights.tobytes(),
                         OUTPUT: b"\xa5" * 128})
    actual = unpack("<f", bh.read_l1(bh.core, OUTPUT, 4))[0]
    assert actual == (reference if finish == "sfpu" else predicted)
    assert bh.read_l1(bh.core, OUTPUT + 64, 64) == b"\xa5" * 64
    results[finish] = actual
  error = abs(results['fpu-row'] - reference)
  print(f"{pattern}: FP64 mean={reference:.12g}, SFPU finish={results['sfpu']:.12g}, "
        f"TF32 FPU finish={results['fpu-row']:.12g}, abs error={error:.12g}, "
        f"relative error={error / abs(reference):.9%}")
