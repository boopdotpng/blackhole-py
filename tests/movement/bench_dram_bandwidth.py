"""Compute-free standalone DRAM streams, identical emitter on BRISC/NCRISC.

Run under tt-device-queue with an explicit matching --device. GB/s is decimal,
uses the earliest active start through the latest remote-completed end, and
counts read+write bytes once each for mixed traffic. Host copies are untimed.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from statistics import median
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from asm import Asm
from cq import Run
from device import Device
from pcie import TLBWindow
from program import Program
from tests.movement import test_noc as n
from tests.movement.noc import InterleavedConfig, emit_interleaved_dram_to_l1, emit_l1_to_interleaved_dram
from tests.movement.profile_matmul_fp8 import clock_mhz


def pattern(page_bytes, slot):
  return bytes((i * 131 + i // 251 + 7 + slot * 37) & 255 for i in range(page_bytes))


def chunks(device, buffer):
  unit = buffer.banks * buffer.page_size
  capacity = device.cq.dram_size // unit * unit
  for offset in range(0, buffer.size, capacity):
    size = min(capacity, buffer.size - offset)
    yield offset, replace(buffer, address=buffer.address + offset // buffer.banks,
                          size=size, physical_size=size, page_count=size // buffer.page_size)


def images(endpoints, page_bytes, batch, roles, direction, network, rotation=0):
  result = {}
  for slot, role in enumerate(roles):
    noc = (network + slot) % 2
    read = direction == 'read' or (direction == 'mixed' and slot == 0)
    coordinates = tuple(x | y << 6 for x, y in (pair[noc] for pair in endpoints))
    coordinates = coordinates[rotation:] + coordinates[:rotation]
    config = InterleavedConfig(coordinates, n.CB_ADDRESS + slot * batch * page_bytes,
        batch, page_bytes, noc, command_slot=1 if read else 2,
        batch_pages=batch, standalone=True)
    asm = Asm(role)
    stamp = n.TIMING_L1_ADDRESS + slot * 16
    n._record_clock(asm, stamp)
    emit = emit_interleaved_dram_to_l1 if read else emit_l1_to_interleaved_dram
    emit(asm, config, slot * 2, slot * 2 + 1)
    n._record_clock(asm, stamp + 8)
    result[role] = asm.lower()
  return result


def bench(device, args, count, page, batch, mode, direction, size):
  roles = ('brisc', 'ncrisc') if mode == 'both' else (mode,)
  cores = device.cores[:count]
  banks = len(device.pcie.dram_endpoints)
  # Keep total traffic fixed when comparing one versus two RISCs per worker.
  unit = banks * page * len(roles)
  per_core = (size + unit - 1) // unit * unit
  per_stream = per_core // len(roles)
  total = count * per_core
  buffer = device.alloc_interleaved_dram(total, page_size=page)
  expected = [pattern(page, slot) * (per_stream // page) for slot in range(len(roles))]
  initial = b''.join(expected[slot] if direction == 'read' or (direction == 'mixed' and slot == 0)
                     else bytes([0xa5]) * per_stream
                     for _ in cores for slot in range(len(roles)))
  for offset, part in chunks(device, buffer):
    device.write_dram(part, initial[offset:offset+part.size])
  del initial
  variants = [images(device.pcie.dram_endpoints, page, batch, roles, direction, i % 2,
                     i % banks if args.bank_rotation else 0)
              for i in range(banks if args.bank_rotation else 2)]
  program = Program({core: variants[i % len(variants)] for i, core in enumerate(cores)})
  params = {core: tuple(word for slot in range(len(roles)) for word in
             (buffer.address + (i * per_core + slot * per_stream) // banks, per_stream))
            for i, core in enumerate(cores)}
  l1 = {}
  for slot in range(len(roles)):
    read = direction == 'read' or (direction == 'mixed' and slot == 0)
    l1[n.CB_ADDRESS + slot * batch * page] = (b'\xcc' * (batch * page) if read
                                            else pattern(page, slot) * batch)
  device.cq.submit(program.commands(params=params, l1=l1), timeout=10)
  samples = []
  with TLBWindow(device.pcie.fd, cores[0]) as window:
    mhz = clock_mhz(window)
    for _ in range(args.runs):
      device.cq.submit((Run(cores),), timeout=10)
      stamps = []
      for core in cores:
        window.target(0, core)
        words = struct.unpack('<' + 'Q' * (2 * len(roles)),
                              window.read(n.TIMING_L1_ADDRESS, 16 * len(roles)))
        stamps.extend(zip(words[::2], words[1::2]))
      cycles = max(end for _, end in stamps) - min(start for start, _ in stamps)
      samples.append(dict(us=cycles / mhz, gb_s=total * mhz / cycles / 1000,
                          launch_skew_us=(max(start for start, _ in stamps)-min(start for start, _ in stamps))/mhz))
    # All retained read staging bytes must match; overwritten earlier batches
    # are not retained. Writes are checked in full after remote acknowledgments.
    for core in cores:
      window.target(0, core)
      for slot in range(len(roles)):
        if direction == 'read' or (direction == 'mixed' and slot == 0):
          assert window.read(n.CB_ADDRESS + slot * batch * page, min(batch * page, per_stream)) == \
                 (pattern(page, slot) * batch)[:min(batch * page, per_stream)]
  if direction != 'read':
    actual = b''.join(device.read_dram(part) for _, part in chunks(device, buffer))
    for i in range(count):
      for slot in range(len(roles)):
        start = i * per_core + slot * per_stream
        assert actual[start:start+per_stream] == expected[slot], (i, slot)
  row = dict(cores=count, page_bytes=page, batch=batch, mode=mode, direction=direction,
             bank_rotation=args.bank_rotation,
             bytes_per_core=per_core, total_bytes=total, aiclk_mhz=mhz,
             median_gb_s=median(s['gb_s'] for s in samples), samples=samples)
  print(json.dumps(row), flush=True)
  return row


def main():
  p = argparse.ArgumentParser(description=__doc__)
  p.add_argument('--device', type=int, required=True)
  p.add_argument('--runs', type=int, default=5)
  p.add_argument('--cores', type=int, nargs='+', default=[8, 16, 32, 64, 110, 117])
  p.add_argument('--pages', type=int, nargs='+', default=[2048])
  p.add_argument('--batch', type=int, default=32)
  p.add_argument('--bank-rotation', action='store_true', help='stagger first bank by worker index')
  p.add_argument('--modes', nargs='+', choices=['brisc', 'ncrisc', 'both'], default=['brisc', 'ncrisc', 'both'])
  p.add_argument('--directions', nargs='+', choices=['read', 'write', 'mixed'], default=['read', 'write'])
  p.add_argument('--bytes-per-core', type=int, default=524288)
  p.add_argument('--json', type=Path, required=True)
  args = p.parse_args()
  if args.runs <= 0 or args.bytes_per_core <= 0:
    p.error('runs and byte count must be positive')
  streams = 2 if 'both' in args.modes else 1
  if not 1 <= args.batch <= 128:
    p.error('batch must be between 1 and 128')
  for page in args.pages:
    if not 0 < page <= 16384 or page % 16:
      p.error('page size must be a multiple of 16, at most 16384')
    if n.CB_ADDRESS + streams * args.batch * page > n.TIMING_L1_ADDRESS:
      p.error('staging rings overlap the timing record; reduce --batch')
  rows = []
  device = Device(args.device)
  try:
    device.boot()
    if any(not 0 < count <= len(device.cores) for count in args.cores):
      p.error('invalid worker count')
    for page in args.pages:
      for count in args.cores:
        for mode in args.modes:
          for direction in args.directions:
            if direction == 'mixed' and mode != 'both':
              continue
            rows.append(bench(device, args, count, page, args.batch, mode, direction, args.bytes_per_core))
            args.json.write_text(json.dumps(dict(device=args.device, results=rows), indent=2)+'\n')
  finally:
    device.close()


if __name__ == '__main__':
  main()
