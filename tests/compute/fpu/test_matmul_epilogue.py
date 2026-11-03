"""The matmul epilogue: FP32 accumulators -> row-major BF16 rows in DRAM.

The last subblock is the one most exposed to ordering bugs (clearing the Dst
remap while its PACRs still read Dst corrupted rows 4..31 of exactly that
subblock), so every case checks every row, including partial M and N edges.
"""
import numpy as np
import pytest

from tests.compute.fpu.test_matmul_peak_fp32 import run_case


@pytest.mark.parametrize('rows,inner,cols,block_k', (
  (96, 64, 128, 1), (160, 64, 128, 1), (256, 64, 128, 1), (64, 64, 256, 1),
  (104, 1024, 96, 8), (40, 64, 96, 1),
))
def test_every_row_including_the_last_subblock(bh, monkeypatch, rows, inner, cols, block_k):
  rng = np.random.default_rng(5)
  a = rng.uniform(-1, 1, (rows, inner)).astype(np.float32)
  b = rng.uniform(-1, 1, (inner, cols)).astype(np.float32)
  for actual, reference in run_case(bh, monkeypatch, a, b, block_k=block_k):
    row_error = np.abs(actual - reference).max(axis=1) / np.abs(reference).max()
    assert not np.nonzero(row_error > 0.01)[0].size, np.nonzero(row_error > 0.01)[0]


def test_row_identity_exact(bh, monkeypatch):
  """C[r, c] = r is exact in BF16, so each output row names its source row."""
  a = np.zeros((128, 32), dtype=np.float32); a[:, 0] = np.arange(128)
  b = np.zeros((32, 128), dtype=np.float32); b[0, :] = 1
  for actual, _ in run_case(bh, monkeypatch, a, b, dtype='bf16'):
    np.testing.assert_array_equal(actual, np.repeat(np.arange(128, dtype=np.float32)[:, None], 128, axis=1))
