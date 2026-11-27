"""Compare native 1D and 2D matmul launches, excluding compilation and upload."""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from compiler import Tensor, dtypes, safe_load, lower_tensor, linearize_schedule, unpack_bundle
from compiler.blackhole.lower import lower_kernel, access
from compiler.blackhole.runtime import materialize
from device import Device, FaceBuffer


def prepare(dev, expression):
  call, = linearize_schedule(lower_tensor(expression))
  lowered = lower_kernel(call.kernel, call.args, len(dev.workers), (dev.cols - 1, 10))
  buffers = [FaceBuffer(dev, arg.shape, arg.dtype, rows) if arg.op.name == "ALLOC" else materialize(arg, dev, rows)
             for arg, rows in zip(call.args, lowered.face_rows)]
  output, _ = access(next(u for u in call.kernel.toposort() if u.op.name == "STORE").src[0])
  images = unpack_bundle(lowered.program.src[3].arg)
  data = {0x80: struct.pack(f"<{len(buffers)}Q", *(b.addr for b in buffers))}
  cores = dev.worker_grid(*lowered.grid) if lowered.grid else dev.workers[:lowered.workers]
  def launch():
    start = time.perf_counter()
    dev.run(images, data=data, cores=cores)
    dev.synchronize(120)
    return time.perf_counter() - start
  return launch, buffers[output], lowered


def synthetic_weight(path, n, k, dtype):
  if dtype == "bf16":
    np.full((n, k), 0x3D00, np.uint16).tofile(path)
    return Tensor.from_disk(path, shape=(n, k), dtype=dtypes.bf16)
  bits = int(dtype[3:])
  raw = np.full((k // 32, n // 32, 64 + 1024 * bits // 8), 0x11 if bits == 4 else 1, np.uint8)
  raw[..., :64] = 120 + bits
  header = {"__metadata__": {"blackhole.layout": "kn_tiles_32x32_v1", "blackhole.formats": json.dumps({"weight": f"bfp{bits}_b"})},
            "weight": {"dtype": "U8", "shape": list(raw.shape), "data_offsets": [0, raw.nbytes]}}
  encoded = json.dumps(header).encode()
  with path.open("wb") as f:
    f.write(len(encoded).to_bytes(8, "little")); f.write(encoded); f.write(memoryview(raw).cast("B"))
  return safe_load(path)["weight"]


def benchmark(args):
  records = []
  dev = Device(args.card)
  try:
    with tempfile.TemporaryDirectory(prefix="bh-mcast-bench-") as directory:
      for n in args.n:
        for dtype in args.formats:
          weight = synthetic_weight(Path(directory) / f"{n}-{dtype}.safetensors", n, args.k, dtype)
          for m in args.m:
            a = np.random.default_rng(m).integers(-2, 3, (m, args.k)).astype(np.float32) / 32
            # Values are exactly representable in BF16; stage raw bits without
            # building millions of Python scalar objects in Tensor's converter.
            activation_path = Path(directory) / f"a-{m}.bf16"
            (a.view(np.uint32) >> 16).astype(np.uint16).tofile(activation_path)
            activation = Tensor.from_disk(activation_path, shape=a.shape, dtype=dtypes.bf16)
            for mode in (0, 1):
              os.environ["BH_MCAST"] = str(mode)
              launch, output, lowered = prepare(dev, activation.matmul(weight.T, dtype=dtypes.fp32))
              launch()  # warm firmware/image caches
              timings = [launch() for _ in range(args.repeat)]
              actual = output.numpy()
              expected = np.broadcast_to(a.sum(axis=-1, keepdims=True) / 32, actual.shape)
              if not np.array_equal(actual, expected): raise AssertionError((m, n, dtype, mode, float(np.max(abs(actual - expected)))))
              seconds = float(np.median(timings))
              record = dict(card=args.card, m=m, n=n, k=args.k, dtype=dtype, mcast=mode, grid=lowered.grid,
                            workers=lowered.workers, seconds=timings, median_seconds=seconds,
                            tflops=2 * m * n * args.k / seconds / 1e12)
              records.append(record)
              print(json.dumps(record), flush=True)
              if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(records, indent=2) + "\n")
  finally: dev.close()


if __name__ == "__main__":
  p = argparse.ArgumentParser(description=__doc__)
  p.add_argument("--card", type=int, default=0)
  p.add_argument("--m", type=int, nargs="+", default=[64, 128, 256, 512, 1024])
  p.add_argument("--n", type=int, nargs="+", default=[7168, 22016])
  p.add_argument("--k", type=int, default=7168)
  p.add_argument("--formats", nargs="+", choices=["bf16", "bfp8", "bfp4"], default=["bf16", "bfp8", "bfp4"])
  p.add_argument("--repeat", type=int, default=3)
  p.add_argument("--output", type=Path, default=None)
  args = p.parse_args()
  if args.k % 32 or any(n % 32 for n in args.n) or args.repeat < 1: p.error("K/N must be multiples of 32; repeat must be positive")
  benchmark(args)
