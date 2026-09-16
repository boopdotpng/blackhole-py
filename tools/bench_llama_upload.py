"""Measure full Llama checkpoint preparation, staging and upload on device 0.

Includes weight reads, preparation, pinned-memory copies and transfer completion,
plus RoPE/KV initialization. Excludes device boot, allocation and kernel build.
OS file caches are left intact. GB/s uses decimal GB and all uploaded bytes.
"""
import argparse
import json
from statistics import median

from examples.llama3 import Llama3Decode, Llama3Kernels


class UploadOnly(Llama3Decode):
  def _build_programs(self): pass


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, default=0)
  parser.add_argument('--dtype', choices=('fp8', 'bf16'), default='fp8')
  parser.add_argument('--repeats', type=int, default=3)
  args = parser.parse_args()
  if args.repeats < 1: parser.error('--repeats must be positive')
  durations = []
  for repeat in range(args.repeats):
    model = UploadOnly(device_index=args.device, kernels=Llama3Kernels('8b', args.dtype))
    try:
      profile = model.profile
      size = profile['dram_upload_bytes']
      elapsed = profile['weight_upload_total_s']
      durations.append(elapsed)
      print(json.dumps({'repeat': repeat, **profile, 'full_upload_GBs': size / elapsed / 1e9}), flush=True)
    finally:
      model.close()
  elapsed = median(durations)
  print(f'median: {size / 1e9:.3f} GB / {elapsed:.3f} s = {size / elapsed / 1e9:.3f} GB/s')


if __name__ == '__main__':
  main()
