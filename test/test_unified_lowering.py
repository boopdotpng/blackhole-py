import os
import numpy as np
import pytest
from compiler import Ops, Tensor, UOp, dtypes, lower_tensor, linearize_schedule
from compiler.blackhole.fpu import match_reductions, MatchedMvmul, MatchedRowReduce
from compiler.blackhole.lower import lower_kernel


def test_match_range_membership_with_symbolic_offsets(monkeypatch):
  import compiler.blackhole.lower as lower
  m, n, k = [UOp.range(extent, i) for i, extent in enumerate((8, 32, 17))]
  offset = UOp.variable('offset', 0, 16)
  a = UOp.param(0, dtypes.bf16, shape=(8, 64)).index(m * 64 + k + offset).load().cast(dtypes.fp32)
  b = UOp.param(1, dtypes.bf16, shape=(32, 64)).index(n * 64 + k + offset).load().cast(dtypes.fp32)
  red = (a * b).reduce(k)
  monkeypatch.setattr(lower, 'affine', lambda *args, **kwargs: pytest.fail('matching must not inspect address strides'))
  match = match_reductions(UOp.sink(red))[red]
  assert isinstance(match, MatchedMvmul)
  assert match.k_axes == (k,) and set(match.m_axes + match.n_axes) == {m, n}
  square = (a * a).reduce(k)
  assert isinstance(match_reductions(UOp.sink(square))[square], MatchedRowReduce)


def test_runtime_rhs_layout():
  x = Tensor.buffer('x', (8, 16), dtypes.bf16)
  w = Tensor.buffer('w', (32, 16), dtypes.bf16)
  call, = linearize_schedule(lower_tensor(x @ w.T))
  args = tuple(UOp.alloc(arg.shape, arg.dtype) for arg in call.args)
  result = lower_kernel(call.kernel, args)
  assert result.face_rows == (8,) * len(args)
  assert result.grid is None


@pytest.mark.skipif(os.environ.get('BH_HW') != '1', reason='requires both cards')
@pytest.mark.parametrize('card', (0, 1))
def test_composed_matmul_and_broadcasts(card, monkeypatch):
  from device import Device
  rng = np.random.default_rng(171)
  a = rng.integers(-2, 3, (33, 32)).astype(np.float32) / 8
  w = rng.integers(-2, 3, (65, 32)).astype(np.float32) / 8
  bias = rng.integers(-2, 3, (65,)).astype(np.float32) / 8
  residual = rng.integers(-2, 3, (33, 65)).astype(np.float32) / 8
  dev = Device(card)
  try:
    for mode in ('0', '1'):
      monkeypatch.setenv('BH_MCAST', mode)
      x, weight = Tensor(a, dtype=dtypes.bf16), Tensor(w, dtype=dtypes.bf16)
      value = x.matmul(weight.T, dtype=dtypes.fp32) + Tensor(bias, dtype=dtypes.bf16) + Tensor(residual)
      np.testing.assert_array_equal(value.numpy(device=dev), a @ w.T + bias + residual)
  finally: dev.close()


@pytest.mark.skipif(os.environ.get('BH_HW') != '1', reason='requires both cards')
@pytest.mark.parametrize('card', (0, 1))
def test_matmul_softmax_composition(card, monkeypatch):
  from device import Device
  monkeypatch.setenv('BH_MCAST', '0')
  rng = np.random.default_rng(172)
  a = rng.integers(-2, 3, (9, 16)).astype(np.float32) / 8
  w = rng.integers(-2, 3, (17, 16)).astype(np.float32) / 8
  dev = Device(card)
  try:
    scores = Tensor(a, dtype=dtypes.bf16).matmul(Tensor(w, dtype=dtypes.bf16).T, dtype=dtypes.fp32) * .5
    value = scores.softmax(-1)
    expected = a @ w.T * .5
    expected = np.exp(expected - expected.max(-1, keepdims=True))
    expected /= expected.sum(-1, keepdims=True)
    np.testing.assert_allclose(value.numpy(device=dev), expected, rtol=5e-6, atol=1e-6)
  finally: dev.close()


@pytest.mark.skipif(os.environ.get('BH_HW') != '1', reason='requires a card')
def test_degenerate_contraction_and_bounded_reduction():
  from compiler import Variable
  from device import Device
  rng = np.random.default_rng(173)
  a = rng.integers(-2, 3, (9, 32)).astype(np.float32)
  b = rng.integers(-2, 3, (32, 1)).astype(np.float32)
  dev = Device(1)
  try:
    x = Tensor(a, dtype=dtypes.bf16)
    np.testing.assert_array_equal(x.matmul(Tensor(b, dtype=dtypes.bf16), dtype=dtypes.fp32).numpy(device=dev), a @ b)
    width = Variable('width', 1, 31)
    for n in (1, 17, 31):
      value = x[:, :width.bind(n)].float().sum(-1, keepdim=True)
      np.testing.assert_array_equal(value.numpy(device=dev), a[:, :n].sum(-1, keepdims=True))
  finally: dev.close()


@pytest.mark.skipif(os.environ.get('BH_HW') != '1', reason='requires a card')
def test_explicit_row_stage():
  import struct
  from compiler import unpack_bundle
  from device import Device, FaceBuffer
  output, source = [UOp.param(i, dtypes.fp32, shape=(9, 17)) for i in range(2)]
  row, col, k = UOp.range(9, 0), UOp.range(17, 1), UOp.range(17, 2)
  stage = UOp.alloc((9, 1), dtypes.fp32, space='l1')
  stored = stage.index(row).store(source.index(row * 17 + k).load().reduce(k))
  value = source.index(row * 17 + col).load() * stage.after(stored).index(row).load()
  kernel = UOp.sink(output.index(row * 17 + col).store(value).end(row, col))
  lowered = lower_kernel(kernel, (output, source))
  values = (np.arange(153) % 7 - 3).astype(np.float32).reshape(9, 17)
  dev = Device(1)
  try:
    out, inp = [FaceBuffer(dev, (9, 17), dtypes.fp32) for _ in range(2)]
    inp.copy_from_raw(values.tobytes())
    dev.run(unpack_bundle(lowered.program.src[3].arg), data={0x80: struct.pack('<2Q', out.addr, inp.addr)},
            cores=dev.workers[:lowered.workers])
    dev.synchronize()
    np.testing.assert_array_equal(out.numpy(), values * values.sum(-1, keepdims=True))
  finally: dev.close()


@pytest.mark.parametrize('reverse', (False, True))
def test_weight_layout_follows_output_column(reverse):
  out = UOp.param(0, dtypes.fp32, shape=(32, 64))
  act = UOp.param(1, dtypes.bf16, shape=(32, 48))
  weight = UOp.param(2, dtypes.bf16, shape=(64, 48))
  m, n, k = [UOp.range(bound, i) for i, bound in enumerate((32, 64, 48))]
  a = act.index(m * 48 + k).load().cast(dtypes.fp32)
  w = weight.index(n * 48 + k).load().cast(dtypes.fp32)
  dot = (w * a if reverse else a * w).reduce(k)
  kernel = UOp.sink(out.index(m * 64 + n).store(dot).end(m, n))
  result = lower_kernel(kernel, (out, act, weight))
  assert result.face_rows == (8, 8, 16)
  assert result.grid == (1, 1)


@pytest.mark.skipif(os.environ.get('BH_HW') != '1', reason='requires a card')
def test_reduction_cast_roundtrip():
  from device import Device
  dev = Device(0)
  try:
    x = np.full((8, 16), np.float32(1.0031))
    value = Tensor(x).sum(-1, keepdim=True).cast(dtypes.bf16).cast(dtypes.fp32)
    np.testing.assert_array_equal(value.numpy(device=dev), np.full((8, 1), 16., np.float32))
  finally: dev.close()
