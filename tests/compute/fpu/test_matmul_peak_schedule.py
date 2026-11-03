"""Hardware coverage for the FP8 row-MOP schedule: partial M/N/K tiles, several
subblocks and K blocks, FP32 accumulation, and a relaunch."""
import numpy as np
import pytest

from examples import matmul_peak as m
from tests.compute.fpu.test_matmul_peak_fp32 import run_case


@pytest.mark.parametrize('buffers', (1, 2, 4))
def test_fp8_schedule_blocks_edges_and_relaunch(bh, monkeypatch, buffers):
  for name, value in dict(INPUT_BUFFER_FACTOR=2, B_BUFFER_FACTOR=buffers, OVERLAP_BLOCKS=0).items():
    monkeypatch.setattr(m.k, name, value)
  rng = np.random.default_rng(7301)
  a = rng.uniform(-.5, .5, (65, 257)).astype(np.float32)
  b = rng.uniform(-.5, .5, (257, 513)).astype(np.float32)
  for actual, reference in run_case(bh, monkeypatch, a, b, block_k=3, subblock=(1, 4)):
    assert np.isfinite(actual).all()
    assert np.linalg.norm(actual-reference) / np.linalg.norm(reference) < .003


def test_reject_empty_n_pass(monkeypatch):
  for name, value in dict(N_PASSES=2, INPUT_DTYPE=m.k.DType.FP8,
                          SUPPORTED_OUT_SUBBLOCK_H=1, SUPPORTED_OUT_SUBBLOCK_W=4,
                          WRITER_WAVE_ROWS=0).items():
    monkeypatch.setattr(m.k, name, value)
  with pytest.raises(ValueError, match='No valid matmul plan'):
    m.k.plan_matmul(32, 32, 32, [(1, 2)])
