"""Isolate the weight-upload transport on device 0 (no checkpoint required).

Run: ../.venv/bin/python -m tools.bench_weight_upload
Transfer timing excludes host staging; every page size gets full readback.
"""
import argparse
import random
from statistics import median
import time

from cq import DramCopy
from device import Device


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, default=0)
  parser.add_argument('--mib', type=int, default=128)
  parser.add_argument('--samples', type=int, default=7)
  parser.add_argument('--copies', type=int, default=8)
  args = parser.parse_args()
  if min(args.mib, args.samples, args.copies) <= 0:
    parser.error('size, samples, and copies must be positive')
  size = args.mib << 20
  data = random.Random(42).randbytes(size)
  device = Device(args.device, sysmem_size=size + (8 << 20))
  try:
    device.boot()
    banks = len(device.pcie.dram_endpoints)
    print(f'device={args.device} card={device.pcie.card_type} banks={banks}')
    print('page bytes | upload GB/s | GiB/s | stage ms | readback')
    for page in (1024, 2048, 4096, 8192, 16384):
      buffer = device.alloc_interleaved_dram(size, page_size=page)
      started = time.perf_counter()
      device.pcie.sysmem.write(device.cq.dram, data)
      staging = time.perf_counter() - started
      command = DramCopy(buffer.address, device.pcie.sysmem.noc_addr + device.cq.dram,
                         page, buffer.page_count, banks)
      device.cq.submit((command,))
      durations = []
      for _ in range(args.samples):
        started = time.perf_counter()
        device.cq.submit((command,) * args.copies)
        durations.append(time.perf_counter() - started)
      rate = size * args.copies / median(durations)
      if device.read_dram(buffer) != data:
        raise RuntimeError(f'readback mismatch for page size {page}')
      print(f'{page:10} | {rate / 1e9:11.2f} | {rate / (1 << 30):5.2f} | '
            f'{staging * 1e3:8.2f} | PASS', flush=True)
  finally:
    device.close()


if __name__ == '__main__':
  main()
