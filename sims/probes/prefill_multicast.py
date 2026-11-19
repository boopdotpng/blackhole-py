"""Hold the projection and worker placement fixed while changing how operands reach worker L1."""
import argparse
from pathlib import Path
from statistics import median
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ops_blackhole import BlackholeComputeQueue
from ttrv import Device


def measure(device):
  width = 4096
  workers = min(130, len(device.dev.workers) // 10 * 10)
  rng = np.random.default_rng(42)

  def bf16_values(count):
    magnitude = rng.integers(0, 127, size=count, dtype=np.uint16) + 0x3b80
    return magnitude | (rng.integers(0, 2, size=count, dtype=np.uint16) << 15)

  weights = device.empty(width * width, "bf16", tiles_per_page=4).copy_from(bf16_values(width * width))
  x = device.array(bf16_values(320 * width), "bf16")
  output = device.empty(320 * width, "bf16")
  stamps = device.zeros((8, 4), "u64", host=True)
  dev = device.dev
  for panels in (2, 5, 10):
    reference = None
    for share_a, share_w in ((1, 0), (1, 1), (0, 0), (0, 1)):
      kernel = device.kernel(ROOT / "examples/nanbeige/projection.ttrv", K=width, N=width, BITS=16, GROUP=4,
                             WORKERS=workers, PREFILL=1, TILE_ROWS=32, SHORT_M=0, PANELS=panels,
                             SHARE_A=share_a, SHARE_W=share_w)
      output.copy_from(np.full(output.shape, 0x7fc1, np.uint16))
      with device.graph() as launch:
        kernel(x=x, weights=weights, output=output, rows=32)
      queue = BlackholeComputeQueue()
      for i in range(8):
        queue.exec(kernel.program, launch.graph.base, profile=stamps.addr + 32 * i)
      queue.signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
      device.synchronize()
      values = output.numpy()[:32 * panels * width]
      if reference is None: reference = values
      if np.any(values == 0x7fc1) or not np.array_equal(reference, values):
        raise ValueError(f"output mismatch with {panels} panels, SHARE_A={share_a}, SHARE_W={share_w}")
      ticks = stamps.numpy()[1:]
      print(f"{panels * 32} tokens, {workers} workers, SHARE_A={share_a}, SHARE_W={share_w}, "
            f"{median(ticks[:, 3] - ticks[:, 1]):,.0f} cycles", flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--device", type=int, required=True)
  card = Device(ap.parse_args().device)
  try: measure(card)
  finally: card.close()
