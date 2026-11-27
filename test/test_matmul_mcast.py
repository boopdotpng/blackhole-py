"""2D compiler matmuls, tails, fused epilogues, rotating rings, and launch reset."""
import os
from pathlib import Path
import numpy as np
import pytest

from compiler import Tensor, UOp, dtypes, safe_load, lower_tensor, linearize_schedule
from compiler.blackhole.lower import lower_kernel
from compiler.blackhole.mcast import invariant_axis
from test.test_packed_checkpoint import checkpoint


def test_invariance_and_dispatch(monkeypatch):
  wx, wy = UOp.special(13, "worker_x"), UOp.special(10, "worker_y")
  assert invariant_axis(wy * 8192, 13, 10) == "x"
  assert invariant_axis(wx * 4096, 13, 10) == "y"
  assert invariant_axis(wx * 4096 + wy * 8192, 13, 10) == "local"
  x, w = Tensor.buffer("a", (64, 1024), dtypes.bf16), Tensor.buffer("w", (1024, 1024), dtypes.bf16)
  call, = linearize_schedule(lower_tensor(x @ w.T))
  monkeypatch.setenv("BH_MCAST", "1")
  assert lower_kernel(call.kernel, call.args).grid == (13, 2)
  assert lower_kernel(call.kernel, call.args, max_workers=4).grid == (4, 1)
  monkeypatch.setenv("BH_MCAST", "0")
  assert lower_kernel(call.kernel, call.args).grid is None
  monkeypatch.setenv("BH_MCAST", "1")
  call, = linearize_schedule(lower_tensor(Tensor.buffer("decode", (1, 1024), dtypes.bf16) @ w.T))
  assert lower_kernel(call.kernel, call.args).grid is None
  a = Tensor.buffer("batched", (2, 3, 17, 1024), dtypes.bf16)
  call, = linearize_schedule(lower_tensor(a @ w.T))
  assert lower_kernel(call.kernel, call.args).grid == (13, 2)


@pytest.mark.skipif(os.environ.get("BH_HW") != "1", reason="set BH_HW=1 for both P150 cards")
@pytest.mark.parametrize("card", (0, 1))
def test_batched_projections(card, monkeypatch):
  from device import Device
  monkeypatch.setenv("BH_MCAST", "1")
  rng = np.random.default_rng(225)
  dev = Device(card)
  try:
    for shape in ((2, 17, 79), (2, 3, 65, 79)):
      for shared in (False, True):
        a = rng.integers(-2, 3, shape).astype(np.float32) / 32
        wshape = (257, 79) if shared else (*shape[:-2], 257, 79)
        w = rng.integers(-2, 3, wshape).astype(np.float32) / 32
        x, weight = Tensor(a, dtype=dtypes.bf16), Tensor(w, dtype=dtypes.bf16)
        expression = x.matmul(weight.transpose(-1, -2), dtype=dtypes.fp32)
        call, = linearize_schedule(lower_tensor(expression))
        assert lower_kernel(call.kernel, call.args).grid is not None
        expected = a @ w.swapaxes(-1, -2)
        assert np.array_equal(expression.numpy(device=dev), expected), (card, shape, shared)
        residual = rng.integers(-2, 3, expected.shape).astype(np.float32) / 32
        actual = (expression + Tensor(residual)).cast(dtypes.bf16).numpy(device=dev)
        np.testing.assert_allclose(actual, expected + residual, rtol=.004, atol=2e-6)
  finally: dev.close()


@pytest.mark.skipif(os.environ.get("BH_HW") != "1", reason="set BH_HW=1 for both P150 cards")
@pytest.mark.parametrize("card", (0, 1))
def test_shapes_formats_and_fusion(card, monkeypatch, tmp_path):
  from device import Device
  rng = np.random.default_rng(224)
  dev = Device(card)
  try:
    for m, n, k in ((16, 256, 256), (64, 1024, 1024), (65, 257, 79), (641, 1153, 64)):
      a = rng.integers(-1, 2, (m, k)).astype(np.float32)
      w = rng.integers(-2, 3, (n, k)).astype(np.float32)
      ta, tw = Tensor(a, dtype=dtypes.bf16), Tensor(w, dtype=dtypes.bf16)
      for mode in ("0", "1"):
        monkeypatch.setenv("BH_MCAST", mode)
        actual = ta.matmul(tw.T, dtype=dtypes.fp32).numpy(device=dev)
        assert np.array_equal(actual, a @ w.T), (card, mode, m, n, k)
    for bits in (8, 4):
      path = tmp_path / f"{bits}.safetensors"
      w = checkpoint(path, bits, k_tiles=32, n_tiles=32)
      tw = safe_load(path)["weight"]
      a = rng.integers(-1, 2, (64, 1024)).astype(np.float32)
      for mode in ("0", "1"):
        monkeypatch.setenv("BH_MCAST", mode)
        actual = Tensor(a, dtype=dtypes.bf16).matmul(tw.T, dtype=dtypes.fp32).numpy(device=dev)
        assert np.array_equal(actual, a @ w.T), (card, mode, bits)
      monkeypatch.setenv("BH_MCAST", "1")
      a = rng.integers(-1, 2, (2, 17, 1024)).astype(np.float32)
      actual = Tensor(a, dtype=dtypes.bf16).matmul(tw.T, dtype=dtypes.fp32).numpy(device=dev)
      assert np.array_equal(actual, a @ w.T), (card, "batched", bits)
    monkeypatch.setenv("BH_MCAST", "1")
    a = rng.integers(-2, 3, (65, 79)).astype(np.float32) / 32
    gate, up = [rng.integers(-2, 3, (257, 79)).astype(np.float32) / 32 for _ in range(2)]
    residual = rng.integers(-2, 3, (65, 257)).astype(np.float32) / 32
    x, g, u = Tensor(a, dtype=dtypes.bf16), Tensor(gate, dtype=dtypes.bf16), Tensor(up, dtype=dtypes.bf16)
    gv, uv = a @ gate.T, a @ up.T
    expected = gv / (1 + np.exp(-gv)) * uv
    for repeat in range(10):
      actual = (x.matmul(g.T, dtype=dtypes.fp32).silu() * x.matmul(u.T, dtype=dtypes.fp32)).numpy(device=dev)
      np.testing.assert_allclose(actual, expected, rtol=4e-6, atol=3e-7)
    actual = (x.matmul(g.T, dtype=dtypes.fp32) + Tensor(residual)).cast(dtypes.bf16).numpy(device=dev)
    np.testing.assert_allclose(actual, gv + residual, rtol=.004, atol=2e-6)
  finally: dev.close()


@pytest.mark.skipif(os.environ.get("BH_MCAST_REAL") != "1", reason="set BH_MCAST_REAL=1 for real Nanbeige projections")
@pytest.mark.parametrize("card", (0, 1))
def test_real_nanbeige(card, monkeypatch):
  from device import Device
  from compiler.blackhole.runtime import materialize
  from examples.benchmark_matmul_mcast import prepare
  root = Path(__file__).resolve().parents[1]
  tensors = safe_load(root.parent / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors")
  dev = Device(card)
  try:
    gate = tensors["model.layers.0.mlp.gate_proj.weight"]
    up = tensors["model.layers.0.mlp.up_proj.weight"]
    for name, weight, m in (("q_proj", tensors["model.layers.0.self_attn.q_proj.weight"], 128),
                            ("gate_proj", gate, 128), ("swiglu", gate, 64)):
      n, k = weight.shape
      a = np.random.default_rng(35).integers(-16, 17, (m, k)).astype(np.float32) / 64
      x = Tensor(a, dtype=dtypes.bf16)
      expression = x.matmul(weight.T, dtype=dtypes.fp32)
      expected = a @ materialize(weight.uop, dev, 16).numpy().T
      if name == "swiglu":
        expression = expression.silu() * x.matmul(up.T, dtype=dtypes.fp32)
        # Explicit destinations also work with NumPy 1.x on Python 3.14,
        # whose temporary-refcount optimization can alias unary expressions.
        denominator = np.empty_like(expected)
        np.negative(expected, out=denominator)
        np.exp(denominator, out=denominator)
        denominator += 1
        np.divide(expected, denominator, out=expected)
        other = a @ materialize(up.uop, dev, 16).numpy().T
        np.multiply(expected, other, out=expected)
      baseline = None
      for mode in ("0", "1"):
        monkeypatch.setenv("BH_MCAST", mode)
        launch, output, lowered = prepare(dev, expression)
        for _ in range(3): launch()
        actual = output.numpy()
        difference = np.empty_like(expected)
        np.subtract(actual, expected, out=difference)
        error = float(np.linalg.norm(difference) / np.linalg.norm(expected))
        assert error < .002, (card, name, mode, error)
        if baseline is None: baseline = actual
        else:
          delta = float(np.max(abs(actual - baseline)))
          assert np.allclose(actual, baseline, rtol=2e-5, atol=2e-6), (name, delta)
  finally: dev.close()
