"""Compare prompt kernels with a token-by-token reference across a cache-tile boundary."""
from pathlib import Path

import numpy as np
import pytest

from ttrv import Device

QWEN = Path(__file__).resolve().parents[1] / "examples/qwen38"


@pytest.fixture(scope="module")
def dev():
  if not Path("/dev/tenstorrent/0").exists(): pytest.skip("Blackhole card 0 is unavailable")
  d = Device(0)
  try: yield d
  finally: d.close()


def test_prompt_attention(dev):
  rng = np.random.default_rng(302)
  length, cap = 35, 64
  data = {k: dev.array(rng.normal(size=(length, width)), "bf16") for k, width in
          (("q_in", 12288), ("k_in", 1024), ("v_in", 1024))}
  args = {k: dev.array(rng.uniform(.5, 1.5, 256), "bf16") for k in ("qnorm", "knorm")}
  args.update({k: dev.array(rng.uniform(-1, 1, (cap, 256)), "bf16") for k in ("cos", "sin")})

  def run(groups, phase):
    context = dev.empty((length, 6144), "bf16")
    caches = {k: dev.zeros(cap * 1024, "bf16") for k in ("key_cache", "value_cache")}
    with dev.phase(phase):
      pos = 0
      for rows in groups:
        inputs = {k: v.page_view(2 * pos * v.shape[1], rows * v.shape[1]) for k, v in data.items()}
        out = context.page_view(2 * pos * 6144, rows * 6144)
        kernel = dev.kernel(QWEN / "attention.ttrv", MAX_TOKENS=cap, PARTITIONS=1, PROMPT_ROWS=rows, PACK_CONTEXT=0)
        kernel(**args, **inputs, **caches, context=out, start_pos=pos)
        pos += rows
    return [b.numpy() for b in (context, *caches.values())]

  serial = run([1] * length, "attention-reference")
  batched = run([16, 13, 6], "attention-prompt")
  for got, want in zip(batched, serial): np.testing.assert_array_equal(got, want)


def test_prompt_gdn_state(dev):
  rng = np.random.default_rng(503)
  length = 7
  conv = dev.array(rng.normal(size=(length, 10240)), "bf16")
  ab = dev.array(rng.normal(size=(length, 1024)), "bf16")
  dynamics = dev.array(rng.uniform(-1, 1, 96), "bf16")

  def run(groups, phase):
    state = dev.empty(48 * 128 * 128, "fp32")
    output = dev.empty((length, 6144), "bf16")
    with dev.phase(phase):
      pos = 0
      for rows in groups:
        k = dev.kernel(QWEN / "gdn_state.ttrv", ROWS=rows)
        k(conv=conv.page_view(2 * pos * 10240, rows * 10240), ab=ab.page_view(2 * pos * 1024, rows * 1024),
          output=output.page_view(2 * pos * 6144, rows * 6144), dynamics=dynamics, state=state, pos=pos)
        pos += rows
    return output.numpy(), state.numpy()

  for got, want in zip(run([3, 4], "gdn-prompt"), run([1] * length, "gdn-reference")):
    np.testing.assert_array_equal(got, want)


@pytest.mark.parametrize("width", [128, 5120])
def test_qwen_two_panel_projection_layout(dev, width):
  # SFPU consumers index rows at the padded DRAM pitch, even for a 128-value projection.
  panels, block = 2, 128
  stride = (width + 1023) // 1024 * 1024
  rng = np.random.default_rng(width)
  source = dev.array(rng.normal(size=(panels * 32, stride)), "bf16")
  tiles = dev.empty(panels * 32 * width, "bf16")
  output = dev.zeros(panels * 32 * stride, "bf16")
  options = dict(BLOCK=block, PANELS=panels, WORKERS=min(128, panels * width // block))
  with dev.phase(("qwen-panel-roundtrip", width)):
    dev.kernel(QWEN.parent / "prefill/pack.ttrv", K=width, TILE_ROWS=32, **options)(x=source, output=tiles, rows=32)
    dev.kernel(QWEN.parent / "prefill/unpack.ttrv", N=width, **options)(x=tiles, output=output)
  got = output.numpy().reshape(panels * 32, stride)
  np.testing.assert_array_equal(got[:, :width], source.numpy()[:, :width])
  assert not got[:, width:].any()
