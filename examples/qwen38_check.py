"""Check the Tensix Qwen3.8 decode kernels (examples/qwen38/*.ttrv) against numpy models of the C kernels' math.

Each kernel runs alone on random inputs over several tokens, so a failure names the kernel and the position:
  conv       gdn_conv.ttrv    causal conv + SiLU, history ring (positions 0..2 read no history)
  state      gdn_state.ttrv   GDN recurrence; also checks the FP32 state against an FP64 state
  out        gdn_out.ttrv     gated RMSNorm
  pipeline   all three stages against frozen C outputs and recurrent state, including a fresh sequence at position 0
  attention  attention.ttrv   q/k RMSNorm, partial RoPE, KV append, attention, output gate

  python examples/qwen38_check.py --device 0
  python examples/qwen38_check.py --device 0 --only attention --tokens 200   # > 128 tokens uses 4 cache partitions
"""

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ttrv.runtime import Device  # noqa: E402

HERE = Path(__file__).with_name("qwen38")


def bf16(x):
  """Round to the nearest BF16 value (ties to even), as float32."""
  u = np.array(x, np.float32, ndmin=1).view(np.uint32)
  r = (u + np.uint32(0x7FFF) + (u >> np.uint32(16) & np.uint32(1))) & np.uint32(0xFFFF0000)
  return r.view(np.float32).reshape(np.shape(x))


def bits(x):
  """BF16 bit patterns of x, for Buffer.copy_from."""
  return (bf16(x).view(np.uint32) >> 16).astype(np.uint16)


def floats(buffer):
  return (buffer.numpy().astype(np.uint32) << 16).view(np.float32)


def unpack_rows(x):
  """Projection input order -> dense: in each 512-element block, 16 low values of each 32-group, then 16 high."""
  b = x.reshape(-1, 2, 16, 16)  # block, half, group, value
  return b.transpose(0, 2, 1, 3).reshape(x.shape)


def state_matrix(buffer):
  # Stored as [head, half, value parity, key pair, value lane, key parity].
  tiles = buffer.numpy().reshape(48, 2, 2, 64, 32, 2)
  return tiles.transpose(0, 3, 5, 1, 4, 2).reshape(48, 128, 128)


def sigmoid(x):
  return 1 / (1 + np.exp(-x))


def gdn_exp(x):
  # The C worker rounds its float-to-integer conversion to nearest even, including the signed half.
  x = np.asarray(x, dtype=np.float64)
  bounded = np.clip(x, -80, 80)
  n = np.rint(bounded * np.float32(1.44269504) + np.where(bounded < 0, -0.5, 0.5))
  r = bounded - n * np.float32(0.69314718)
  p = 1 + r * (1 + r * (0.5 + r * (1 / 6 + r * (1 / 24 + r / 120))))
  return np.where(x < -80, 0, np.ldexp(p, n.astype(int)))


def gdn_sigmoid(x):
  return 1 / (1 + gdn_exp(-x))


def gdn_softplus(x):
  t = gdn_exp(-abs(x))
  y = t / (2 + t)
  s = y * y
  return max(x, 0) + 2 * y * (1 + s * (1/3 + s * (1/5 + s * (1/7 + s/9))))


class Report:
  def __init__(self):
    self.failed = []

  def __call__(self, name, got, want, tol):
    scale = max(float(np.abs(want).max()), 1e-30)
    err = float(np.abs(np.asarray(got, np.float64) - want).max()) / scale
    bad = not np.isfinite(got).all() or err > tol
    if bad:
      self.failed.append(name)
    print(f"{'FAIL' if bad else 'ok  '} {name}: max error {err:.2e} of max |ref| {scale:.3g} (tolerance {tol:.0e})")


# ---- conv

def check_conv(dev, rng, tokens, report):
  C = 10240
  kernel = dev.kernel(HERE / "gdn_conv.ttrv")
  raws = bf16(rng.standard_normal((tokens, C)).astype(np.float32))
  taps = bf16(rng.standard_normal((4, C)).astype(np.float32) * 0.5)
  qkv, out = dev.empty(C, "bf16"), dev.empty(C, "bf16")
  history = dev.array(np.full(4 * C, 1e4, np.float32), "bf16")  # garbage: tokens before 0 must read as zero
  w = dev.array(taps, "bf16")
  for pos in range(tokens):
    qkv.copy_from(bits(raws[pos]))
    kernel(qkv=qkv, taps=w, history=history, output=out, pos=pos)
    x = raws[pos] * taps[3]
    for i in range(3):
      if pos - 3 + i >= 0:
        x = x + raws[pos - 3 + i] * taps[i]
    report(f"conv pos {pos}", floats(out), bf16(x * gdn_sigmoid(x)), 6e-3)


# ---- GDN state

def check_state(dev, rng, tokens, report):
  kernel = dev.kernel(HERE / "gdn_state.ttrv")
  ab = bf16(rng.standard_normal(128).astype(np.float32) * 2)
  expa = bf16(0.02 + rng.random(48).astype(np.float32) * 2)
  expa[::7] = bf16(np.float32(2e-3))  # slow-decay heads: rounding in the state would accumulate here
  dtb = bf16(rng.standard_normal(48).astype(np.float32) * 0.5)
  conv, output = dev.empty(10240, "bf16"), dev.empty(48 * 128, "bf16")
  state = dev.empty(48 * 128 * 128, "fp32")
  abuf, dyn = dev.array(ab, "bf16"), dev.array(np.r_[expa, dtb], "bf16")
  S = np.zeros((48, 128, 128))
  for pos in range(tokens):
    x = bf16(rng.standard_normal(10240).astype(np.float32) * 0.5)
    conv.copy_from(bits(x))
    kernel(conv=conv, ab=abuf, dynamics=dyn, state=state, output=output, pos=pos)
    want = np.empty((48, 128))
    for h in range(48):
      q, k = x[(h // 3) * 128 :][:128].astype(np.float64), x[2048 + (h // 3) * 128 :][:128].astype(np.float64)
      v = x[4096 + h * 128 :][:128]
      q = q / np.sqrt(q @ q + 1e-6) / np.sqrt(128)
      k = k / np.sqrt(k @ k + 1e-6)
      decay = gdn_exp(-float(expa[h]) * gdn_softplus(float(ab[h]) + float(dtb[h])))
      beta = gdn_sigmoid(float(ab[64 + h]))
      delta = beta * (v - decay * (k @ S[h]))
      S[h] = decay * S[h] + np.outer(k, delta)
      want[h] = q @ S[h]
    report(f"state out pos {pos}", floats(output).reshape(48, 128), want, 4e-3)
  report(f"state after {tokens} tokens", state_matrix(state), S, 1e-5)


# ---- gated norm

def check_out(dev, rng, report):
  kernel = dev.kernel(HERE / "gdn_out.ttrv")
  x = bf16(rng.standard_normal((48, 128)).astype(np.float32))
  z = bf16(rng.standard_normal((48, 128)).astype(np.float32) * 2)
  w = bf16(1 + rng.standard_normal(128).astype(np.float32) * 0.1)
  output = dev.empty(48 * 128, "bf16")
  kernel(x=dev.array(x, "bf16"), z=dev.array(z, "bf16"), gamma=dev.array(np.tile(w, 8), "bf16"), output=output)
  inv = 1 / np.sqrt((x.astype(np.float64) ** 2).mean(1, keepdims=True) + 1e-6)
  report("gated norm", unpack_rows(floats(output)).reshape(48, 128), x * inv * w * z * gdn_sigmoid(z), 4e-3)


# Frozen samples from the original C worker, including its rounding and projection layout.
# Check two channels and two state entries per head across startup, ring wrap, and replay at pos 0.
def pipeline_inputs():
  rng = np.random.default_rng(812)
  def rand(shape, scale=1):
    return bf16(rng.standard_normal(shape).astype(np.float32) * scale)
  taps, gamma = rand((10240, 4), 0.7), rand(128)
  dynamics = np.r_[bf16(np.exp(rand(48))), rand(48)]
  def tokens():
    for pos in (*range(32), 0):
      yield pos, rand(10240), rand(6144, 3), rand(128, 2)
    # Empty key/query heads and saturated gates exercise zero norms and both exp clamps.
    raw, gate, coeff = rand(10240), rand(6144), rand(128)
    raw[:128] = raw[2048:2176] = 0
    gate[::5], gate[1::5] = -100, 100
    coeff[::3], coeff[1::3] = -100, 100
    yield 0, raw, gate, coeff
  return taps, gamma, dynamics, tokens()


def sample_pipeline(context, state):
  h = np.arange(48)[:, None]
  v = (13 * h + np.array([7, 85])) % 128
  k = (29 * h + np.array([33, 112])) % 128
  return context[h, v], state[h, k, v]


def check_pipeline(dev, report):
  taps, gamma, dynamics, tokens = pipeline_inputs()
  conv, state, out = [dev.kernel(HERE / f"gdn_{name}.ttrv") for name in ("conv", "state", "out")]
  def buf(n):
    return dev.empty(n, "bf16")
  x, z, ab, convolved, heads, context = map(buf, (10240, 6144, 128, 10240, 6144, 6144))
  hist = buf(4 * 10240)
  matrix = dev.empty(48 * 128 * 128, "fp32")
  w, g, dyn = [dev.array(t, "bf16") for t in (taps.T.copy(), np.tile(gamma, 8), dynamics)]
  with np.load(HERE / "gdn_reference.npz") as reference:
    for step, (pos, raw, gate, coeff) in enumerate(tokens):
      for buffer, value in ((x, raw), (z, gate), (ab, coeff)):
        buffer.copy_from(bits(value))
      conv(qkv=x, taps=w, history=hist, output=convolved, pos=pos)
      state(conv=convolved, ab=ab, dynamics=dyn, state=matrix, output=heads, pos=pos)
      out(x=heads, z=z, gamma=g, output=context)
      if f"{step}_state" in reference:
        c, s = sample_pipeline(unpack_rows(floats(context)).reshape(48, 128), state_matrix(matrix))
        report(f"C context step {step}", c, reference[f"{step}_context"], 1e-3)
        report(f"C state step {step}", s, reference[f"{step}_state"], 1e-5)


# ---- attention

def check_attention(dev, rng, tokens, report):
  cap = (tokens + 31) // 32 * 32
  kernel = dev.kernel(HERE / "attention.ttrv", MAX_TOKENS=cap)
  theta = 1e7
  angle = np.arange(cap, dtype=np.float32)[:, None] * theta ** (-np.arange(0, 64, 2, dtype=np.float32) / 64)
  c, s = bf16(np.cos(angle)), bf16(np.sin(angle))
  cos = dev.array(np.concatenate((c, c, np.ones((cap, 192), np.float32)), 1), "bf16")
  sin = dev.array(np.concatenate((-s, s, np.zeros((cap, 192), np.float32)), 1), "bf16")
  gq = bf16(1 + rng.standard_normal(256).astype(np.float32) * 0.1)
  gk = bf16(1 + rng.standard_normal(256).astype(np.float32) * 0.1)
  q_in, k_in, v_in = dev.empty(24 * 512, "bf16"), dev.empty(1024, "bf16"), dev.empty(1024, "bf16")
  keys, values = dev.zeros(cap * 1024, "bf16"), dev.zeros(cap * 1024, "bf16")
  context = dev.empty(24 * 256, "bf16")
  qn, kn = dev.array(gq, "bf16"), dev.array(gk, "bf16")

  def norm_rope(x, g, pos):  # normalized and rotated rows of 256
    x = bf16(x / np.sqrt((x.astype(np.float64) ** 2).mean(-1, keepdims=True) + 1e-6) * g)
    a, b = x[..., :32].copy(), x[..., 32:64].copy()
    x[..., :32] = bf16(a * c[pos] - b * s[pos])
    x[..., 32:64] = bf16(b * c[pos] + a * s[pos])
    return x

  cache_k, cache_v = [], []
  for pos in range(tokens):
    qg = bf16(rng.standard_normal((24, 512)).astype(np.float32))
    k = bf16(rng.standard_normal((4, 256)).astype(np.float32))
    v = bf16(rng.standard_normal((4, 256)).astype(np.float32))
    for buffer, data in ((q_in, qg), (k_in, k), (v_in, v)):
      buffer.copy_from(bits(data))
    kernel(q_in=q_in, k_in=k_in, v_in=v_in, qnorm=qn, knorm=kn, cos=cos, sin=sin, key_cache=keys,
           value_cache=values, context=context, start_pos=pos)
    q = norm_rope(qg[:, :256], gq, pos)
    cache_k.append(norm_rope(k, gk, pos))
    cache_v.append(v)
    K, V = np.stack(cache_k, 1), np.stack(cache_v, 1)  # [4, pos + 1, 256]
    want = np.empty((24, 256))
    for j in range(24):
      scores = K[j // 6] @ q[j].astype(np.float64) / 16
      p = np.exp(scores - scores.max())
      want[j] = (p @ V[j // 6]) / p.sum() * sigmoid(qg[j, 256:].astype(np.float64))
    report(f"attention pos {pos}", unpack_rows(floats(context)).reshape(24, 256), want, 3e-2)


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--only", choices=("conv", "state", "out", "pipeline", "attention"), action="append")
  ap.add_argument("--tokens", type=int, default=40, help="positions per sequential check")
  args = ap.parse_args()
  if args.tokens < 1: ap.error("--tokens must be positive")
  only = set(args.only or ("conv", "state", "out", "pipeline", "attention"))
  rng = np.random.default_rng(0)
  report = Report()
  dev = Device(args.device)
  try:
    if "conv" in only:
      check_conv(dev, rng, min(args.tokens, 8), report)
    if "out" in only:
      check_out(dev, rng, report)
    if "state" in only:
      check_state(dev, rng, args.tokens, report)
    if "pipeline" in only:
      check_pipeline(dev, report)
    if "attention" in only:
      check_attention(dev, rng, args.tokens, report)
  finally:
    dev.close()
  print(f"{len(report.failed)} failed" if report.failed else "all passed")
  sys.exit(1 if report.failed else 0)
