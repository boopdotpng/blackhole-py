import numpy as np
import pytest
from tests.compute.fpu.test_matmul_peak_fp32 import run_case
@pytest.mark.parametrize('rows,cols', [(32,128),(64,128),(32,256),(65,129)])
def test_probe(bh, monkeypatch, rows, cols):
  rng=np.random.default_rng(7)
  a=rng.uniform(-1,1,(rows,257)).astype(np.float32)
  b=rng.uniform(-1,1,(257,cols)).astype(np.float32)
  for actual,ref in run_case(bh,monkeypatch,a,b,dtype='bf16'):
    assert np.linalg.norm(actual-ref)/np.linalg.norm(ref)<.02
