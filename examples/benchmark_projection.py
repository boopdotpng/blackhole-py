"""Compile and validate projections from the mixed Nanbeige checkpoint on P150."""
import argparse
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from compiler import Tensor, dtypes, safe_load, lower_tensor, linearize_schedule, unpack_bundle
from compiler.blackhole.lower import lower_kernel, access
from compiler.blackhole.runtime import materialize
from device import Device, FaceBuffer


def benchmark(path, cards, names, repeats):
  records = []
  for index in cards:
    dev = Device(index)
    try:
      tensors = safe_load(path)
      for name in names:
        weight = tensors[name]
        n, k = weight.shape
        # Exactly seven significand bits isolates arithmetic rounding from
        # the deliberate omission of SrcB's low bits in BFP fidelity modes.
        a = (np.random.default_rng(35).uniform(-.25, .25, (1, k)).astype(np.float32).view(np.uint32) & 0xFFFE0000).view(np.float32)
        activation = Tensor(a, dtype=dtypes.bf16)
        expression = activation.matmul(weight.T, dtype=dtypes.fp32)
        call, = linearize_schedule(lower_tensor(expression))
        lowered = lower_kernel(call.kernel, call.args, len(dev.workers))
        buffers = [FaceBuffer(dev, arg.shape, arg.dtype, rows) if arg.op.name == "ALLOC" else materialize(arg, dev, rows)
                   for arg, rows in zip(call.args, lowered.face_rows)]
        output_slot, _ = access(next(u for u in call.kernel.toposort() if u.op.name == "STORE").src[0])
        weight_slot = call.args.index(weight.uop)
        images = unpack_bundle(lowered.program.src[3].arg)
        data = {0x80: struct.pack(f"<{len(buffers)}Q", *(b.addr for b in buffers))}
        timings = []
        for _ in range(repeats):
          start = time.perf_counter()
          dev.run(images, data=data, cores=dev.workers[:lowered.workers])
          dev.synchronize()
          timings.append(time.perf_counter() - start)
        actual = buffers[output_slot].numpy()
        expected = a @ buffers[weight_slot].numpy().T
        error = float(np.linalg.norm(actual - expected) / np.linalg.norm(expected))
        if not error < .002: raise AssertionError(f"{name}: relative L2 error {error}")
        record = dict(card=index, name=name, shape=[n, k], dtype=weight.dtype.name, workers=lowered.workers,
                      launch_seconds=timings, relative_l2=error, max_abs=float(np.max(np.abs(actual - expected))))
        records.append(record)
        print(json.dumps(record), flush=True)
    finally: dev.close()
  return records


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--checkpoint", type=Path, default=ROOT.parent / "weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors")
  parser.add_argument("--card", type=int, choices=(0, 1), action="append")
  parser.add_argument("--weight", action="append")
  parser.add_argument("--repeat", type=int, default=3)
  parser.add_argument("--output", type=Path)
  args = parser.parse_args()
  if args.repeat < 1: parser.error("--repeat must be positive")
  result = benchmark(args.checkpoint, args.card or (0, 1), args.weight or
                     ("model.layers.0.self_attn.k_proj.weight", "model.layers.0.mlp.gate_proj.weight"), args.repeat)
  if args.output: args.output.write_text(json.dumps(result, indent=2) + "\n")
