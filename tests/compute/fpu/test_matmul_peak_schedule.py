"""Hardware coverage for row MOPs, N-pass output overlap, and final L1 accumulation."""
import numpy as np
import pytest

from examples import matmul_peak as m
from tests.compute.fpu.test_matmul_peak_fp32 import run_case


@pytest.mark.parametrize('passes,final_acc,z_addressing,ring', (
  (1, False, False, False), (1, True, False, False),
  (2, False, False, False), (2, True, False, False),
  (2, False, True, False), (2, True, True, False),
  (2, False, False, True),
))
def test_fp8_schedules_blocks_edges_and_relaunch(bh, monkeypatch, passes, final_acc, z_addressing, ring):
  for name, value in dict(ROW_MOP=True, NO_COMMIT_SYNC=True, FAST_READS=True,
                          FAST_ADDR=True, N_PASSES=passes, FINAL_L1_ACC=final_acc,
                          OUTPUT_RING=ring, UNPACK_Z=z_addressing,
                          INPUT_BUFFER_FACTOR=2, B_BUFFER_FACTOR=4,
                          OVERLAP_BLOCKS=0).items():
    monkeypatch.setattr(m.k, name, value)
  rng = np.random.default_rng(7301)
  # Partial M/N/K tiles, multiple subblocks per N pass, and three K blocks.
  a = rng.uniform(-.5, .5, (65, 257)).astype(np.float32)
  b = rng.uniform(-.5, .5, (257, 513)).astype(np.float32)
  for actual, reference in run_case(bh, monkeypatch, a, b, fp32=False,
                                     block_k=3, subblock=(1, 8)):
    assert np.isfinite(actual).all()
    assert np.linalg.norm(actual-reference) / np.linalg.norm(reference) < .015


def test_reject_empty_n_pass(monkeypatch):
  for name, value in dict(N_PASSES=2, INPUT_DTYPE=m.k.DType.FP8,
                          FP32_ACCUM=False, SUPPORTED_OUT_SUBBLOCK_H=1,
                          SUPPORTED_OUT_SUBBLOCK_W=8, WRITER_WAVE_ROWS=0,
                          OUTPUT_RING=False).items():
    monkeypatch.setattr(m.k, name, value)
  with pytest.raises(ValueError, match='No valid matmul plan'):
    m.k.plan_matmul(32, 32, 32, [(1, 2)])
