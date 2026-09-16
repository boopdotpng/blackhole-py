"""Capture per-core FP8/FP16 matmul timelines without adding device instructions."""
import argparse
import json
import struct
import sys
from pathlib import Path
from statistics import mean
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from examples import matmul_peak as m


def clock_mhz(window):
  arc = (8, 0)
  window.target(0x80000000, arc)
  telemetry, = struct.unpack('<I', window.read(0x30434, 4))
  window.target(telemetry & -window.SIZE, arc)
  offset = telemetry % window.SIZE
  count, = struct.unpack('<I', window.read(offset + 4, 4))
  if not 0 < count <= 256:
    raise ValueError('invalid telemetry table')
  entries = struct.unpack(f'<{count}I', window.read(offset + 8, count * 4))
  tags = {entry & 65535: entry >> 16 for entry in entries}
  return struct.unpack('<I', window.read(offset + 8 + count*4 + tags[14]*4, 4))[0]


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', required=True, type=int)
  parser.add_argument('--runs', type=int, default=9)
  parser.add_argument('--json', required=True, type=Path)
  args = parser.parse_args()
  samples = []
  original = m.read_profile

  def profile(window, cores):
    elapsed, durations = original(window, cores)
    frequency = clock_mhz(window)
    if frequency != 1350:
      raise ValueError(f'Existing timestamp conversion assumes 1350 MHz, got {frequency}')
    records = []
    for core in cores:
      window.target(0, core)
      times = {name: struct.unpack('<QQ', window.read(addr, 16))
               for name, addr in m.k.PROFILE_NAMES}
      records.append({'core': core, 'cycles': times})
    start = min(r['cycles']['brisc'][0] for r in records)
    math_end = max(r['cycles']['trisc1'][1] for r in records)
    pack_end = max(r['cycles']['trisc2'][1] for r in records)
    finish = max(r['cycles']['ncrisc'][1] for r in records)
    sample = dict(total_us=elapsed, aiclk_mhz=frequency, role_max_us=durations,
                  math_finished_us=(math_end-start)/frequency,
                  pack_finished_us=(pack_end-start)/frequency,
                  output_tail_us=(finish-pack_end)/frequency, cores=records)
    samples.append(sample)
    return elapsed, durations

  with patch.object(m, 'read_profile', profile):
    m.run(5000, 5000, 5000, runs=args.runs, device_index=args.device,
          execute=True, profile=True, dtype='fp8', accumulation='fp16')
  summary = {key: mean(s[key] for s in samples) for key in
             ('total_us', 'math_finished_us', 'pack_finished_us', 'output_tail_us')}
  summary['logical_tflops'] = 250e3 / summary['total_us']
  summary['roles_us'] = {key: mean(s['role_max_us'][key] for s in samples)
                         for key in samples[0]['role_max_us']}
  args.json.write_text(json.dumps(dict(device=args.device, shape=[5000]*3,
      summary=summary, samples=samples), indent=2) + '\n')
  print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
  main()
