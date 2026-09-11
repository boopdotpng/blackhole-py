"""Measure 1B GEMV pipelines and synthetic limits on a selected card.

Only `real` performs the full projection. `resident_weights` substitutes zero
weights already in L1. Their timings diagnose pipeline limits, not model throughput.
"""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import statistics

import numpy as np

from ttko.device import Device
from examples import llama3_1b as llama3
from ttko.program import Const, DType, Program
from ttko.cb import CB

SHAPES = {
  'o': (2048, (2048,)),
  'qkv': (2048, (2048, 512, 512)),
  'gate': (2048, (8192, 8192)),
  'down': (8192, (2048,)),
  'lm': (2048, (128256,)),
}


def resident_reader(p, projections, row_starts, rotations, read_noc, weight_cb, input_tiles):
  llama3._zero_l1_words(p.brisc, weight_cb.addr, weight_cb.size // 4)
  for _, _, count in projections:
    for _ in p.brisc.range(count):
      CB.reserve_back(p.brisc, weight_cb, input_tiles)
      CB.push_back(p.brisc, weight_cb, input_tiles)


@contextmanager
def mode(name):
  reader = llama3._projection_read_weights
  try:
    if name == 'resident_weights': llama3._projection_read_weights = resident_reader
    yield
  finally:
    llama3._projection_read_weights = reader


def measure(name, args):
  input_dim, output_dims = SHAPES[name]
  device = Device(args.device)
  try:
    device.init_device()
    cores = tuple(device.dram.cores[:117])
    x = device.dram.buffer('x', DType.BF16, (1, input_dim), global_address=True)
    device.write(x, np.full((1, input_dim), 0x3F80, dtype='<u2').tobytes())
    device.run()
    projections = []
    for i, output_dim in enumerate(output_dims):
      w = device.dram.buffer(f'w{i}', DType.BF16, (output_dim, input_dim), axis=0, cores=cores)
      y = device.dram.buffer(f'y{i}', DType.BF16, (len(cores), w.items_per_core), axis=0, cores=cores)
      device.write(w, np.full(w.shape, 0x3C00, dtype='<u2').tobytes())
      device.run(timeout=60)
      projections.append((w, y))
    programs = {}
    for variant in args.modes:
      with mode(variant): programs[variant] = llama3._decode_fused_projections(x, projections)
    noop = Program(cores[:1], Const('probe', 0), images={})
    device.cache_kernels((*programs.values(), noop))
    results = {}
    for variant, program in programs.items():
      print(f"measuring {name}: {variant}", flush=True)
      pair = []
      for copies in (8, 24):
        device.queue(noop)
        for _ in range(copies): device.queue(program)
        pair.append(device.capture_trace(('probe',)))
      medians = []
      for trace in pair:
        samples = []
        for repeat in range(9):
          trace.replay({'probe': 0})
          if repeat >= 2: samples.append(trace.last_profile['device_us'])
        medians.append(statistics.median(samples))
      us = (medians[1] - medians[0]) / 16
      if variant == 'real':
        for w, y in projections:
          values = y.to_numpy(device.read(y))
          for row, count in zip(values, w.item_counts):
            np.testing.assert_array_equal(row[:count], input_dim / 128)
            np.testing.assert_array_equal(row[count:], 0)
      results[variant] = {
        'us': us,
        'effective_weight_GB_s': input_dim * sum(output_dims) * 2 / us / 1000 if variant == 'real' else None,
        'max_kernel_bytes': {role: max(len(images[role]) for images in program.lower().values())
                             for role in program.roles},
      }
    return {'name': name, 'input_dim': input_dim, 'output_dims': output_dims,
            'device': args.device, 'workers': len(cores), 'results': results}
  finally:
    device.close()


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, default=0)
  parser.add_argument('--kernels', nargs='+', choices=tuple(SHAPES), default=list(SHAPES))
  parser.add_argument('--modes', nargs='+', choices=('real', 'resident_weights'),
                      default=['real', 'resident_weights'])
  parser.add_argument('--output', type=Path, required=True)
  args = parser.parse_args()
  results = []
  for name in args.kernels:
    result = measure(name, args)
    print(json.dumps(result), flush=True)
    results.append(result)
    args.output.write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
  main()
