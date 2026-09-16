"""FP8 matmul: FP32 Dst and L1 partials, including cancellation across K blocks."""
import numpy as np
import pytest

from examples import matmul_peak as m
from cq import McastWrite, Run, rectangles


def run_case(bh, monkeypatch, a, b, *, fp32=True, block_k=1, subblock=(1, 4)):
  k = m.k
  for name, value in dict(INPUT_DTYPE=k.DType.FP8, INPUT_TILE_BYTES=1024,
                          OUTPUT_DTYPE=k.DType.F32 if fp32 else k.DType.F16,
                          TILE_BYTES=4096 if fp32 else 2048, FP32_ACCUM=fp32,
                          SUPPORTED_IN0_BLOCK_WS=(block_k,),
                          SUPPORTED_OUT_SUBBLOCK_H=subblock[0],
                          SUPPORTED_OUT_SUBBLOCK_W=subblock[1], WRITER_WAVE_ROWS=0).items():
    monkeypatch.setattr(k, name, value)
  rows, inner = a.shape
  columns = b.shape[1]
  plan = k.plan_matmul(rows, inner, columns, [bh.core])
  shape = (plan.mt*32, plan.kt*32, plan.nt*32)
  buffers, quantized = [], []
  for values, padded_shape in ((a, shape[:2]), (b, shape[1:])):
    values = m.fp8_decode(m.fp8_encode(values))
    quantized.append(values)
    padded = np.zeros(padded_shape, dtype=np.float32)
    padded[:values.shape[0], :values.shape[1]] = values
    buffer = bh.device.alloc_interleaved_dram(padded.size, page_size=1024)
    bh.device.write_dram(buffer, m.tile_bytes(padded, 'fp8'))
    buffers.append(buffer)
  output = bh.device.alloc_interleaved_dram(shape[0]*shape[2]*(4 if fp32 else 2), page_size=k.TILE_BYTES)
  bh.device.write_dram(output, b'\xa5'*output.size)
  program, commands, _ = m.build(plan, bh.device.pcie.dram_endpoints,
                                 buffers[0].address, buffers[1].address, output.address)
  # Reusing the same L1 partials must overwrite block zero on each invocation.
  for iteration in range(2):
    bh.device.cq.submit(commands if iteration == 0 else (
      McastWrite(rectangles(program.cores), m.asm.SEM_BASE, bytes(128)), Run(program.cores)), timeout=10)
    raw = m.matrix_bytes(bh.device.read_dram(output), shape[0], shape[2], fp32=fp32)
    result = np.frombuffer(raw, dtype='<f4' if fp32 else '<f2').reshape(shape[0], shape[2])
    actual = result[:rows, :columns].astype(np.float32)
    yield actual.copy(), quantized[0] @ quantized[1]


@pytest.mark.parametrize('inner', (32, 64, 96, 257))
@pytest.mark.parametrize('subblock', ((1, 4), (2, 2)))
def test_fp32_matmul_blocks_and_edges(bh, monkeypatch, inner, subblock):
  rng = np.random.default_rng(123)
  a = rng.uniform(-1, 1, (65, inner)).astype(np.float32)
  b = rng.uniform(-1, 1, (inner, 129)).astype(np.float32)
  for actual, reference in run_case(bh, monkeypatch, a, b, subblock=subblock):
    assert np.isfinite(actual).all()
    relative_error = np.linalg.norm(actual-reference) / np.linalg.norm(reference)
    assert relative_error < 0.0003, relative_error


def test_fp32_preserves_small_partials(bh, monkeypatch):
  # Exact E4M3 inputs: 2048 + 2048*(1/64)^2 - 2048 = 0.5.
  # FP16 partial accumulation loses the small term while the running sum is 2048.
  a = np.ones((32, 6144), dtype=np.float32)
  b = np.ones((6144, 128), dtype=np.float32)
  a[:, 2048:4096] = 1/64
  b[2048:4096] = 1/64
  b[4096:] = -1
  for actual, _ in run_case(bh, monkeypatch, a, b, fp32=True, block_k=8):
    np.testing.assert_array_equal(actual, np.full_like(actual, .5))
  for actual, _ in run_case(bh, monkeypatch, a, b, fp32=False, block_k=8):
    assert np.max(np.abs(actual-.5)) >= .25


def test_fp32_exceeds_fp16_range(bh, monkeypatch):
  a = np.full((32, 64), 448, dtype=np.float32)
  b = np.full((64, 128), 448, dtype=np.float32)
  for actual, _ in run_case(bh, monkeypatch, a, b):
    np.testing.assert_array_equal(actual, np.full_like(actual, 64*448*448))
