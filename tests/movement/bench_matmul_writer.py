"""Correctness-checked matmul writer A/B benchmark (explicit card required).

Run through tt-device-queue with the same --device. Every variant uses the
normal matmul validation and completion-inclusive device timestamps. The
baseline reconstructs the old output endpoint lookup, without reverting files.
"""
import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from examples import matmul_peak as m
from ttko.isa import R
from ttko.registers import NcriscMailbox as NM

VARIANTS = ('baseline', 'preferred', 'port0', 'port1', 'port2', 'spread',
            'vc_rows', 'vc_dynamic', 'wave1', 'wave2', 'fastaddr')


def benchmark(args, variant, dtype):
  original_address = m.k.MatmulKernel.dram_tile_addr_from
  original_setup = m.k.emit_output_write_state_setup
  original_profile = m.read_profile
  samples = []

  def address(fw, table, offset=0, *, tile_bytes=2048):
    is_output = table == NM.DRAM_BANK_TO_NOC_XY and offset == R.S8
    if is_output and variant == 'baseline':
      offset = 0
    if is_output and variant == 'fastaddr' and len(m.asm.CONTEXT['endpoints']) == 8:
      fw.mv(R.T0, R.A1); fw.andi(R.A1, R.T0, 7); fw.srli(R.T0, R.T0, 3)
      fw.slli(R.T0, R.T0, 11); fw.add(R.A0, R.A0, R.T0)
      fw.add(R.T1, R.A1, offset); fw.slli(R.T1, R.T1, 1)
      fw.li(R.T2, table); fw.add(R.T2, R.T2, R.T1)
      return fw.lhu(R.A2, R.T2, 0)
    return original_address(fw, table, offset, tile_bytes=tile_bytes)

  def setup(fw):
    original_setup(fw)
    if variant == 'vc_rows':
      fw.read32(R.T2, m.k.LaunchL1.GRID_RANK_BASE)
      fw.li(R.T1, 4); fw.remu(R.T2, R.T2, R.T1); fw.slli(R.T2, R.T2, 13)
      fw.li(R.T1, m.k.NOC.CMD_WR_FIELD & ~(7 << 13))
      fw.or_(R.T2, R.T2, R.T1); fw.sw(R.T2, R.GP, 0x1c)
    elif variant == 'vc_dynamic':
      m.k._output_reg(fw, 0x1c, m.k.NOC.CMD_WR_FIELD & ~(1 << 7))
    elif variant.startswith('port') or variant == 'spread':
      for bank, pair in enumerate(m.asm.CONTEXT['endpoints']):
        x = pair[0][0]
        y = 12 + (min(pair[0][1], pair[1][1]) - 12) // 3 * 3
        if variant == 'spread':
          fw.read32(R.T2, m.k.LaunchL1.GRID_RANK_BASE)
          fw.li(R.T1, 3); fw.remu(R.T2, R.T2, R.T1); fw.slli(R.T2, R.T2, 6)
          fw.li(R.T1, x | y << 6); fw.add(R.T1, R.T1, R.T2)
        else:
          fw.li(R.T1, x | (y + int(variant[-1])) << 6)
        for noc in range(2):
          fw.li(R.T0, NM.DRAM_BANK_TO_NOC_XY + (noc*len(m.asm.CONTEXT['endpoints'])+bank)*2)
          fw.sh(R.T1, R.T0, 0)

  def profile(window, cores):
    elapsed, durations = original_profile(window, cores)
    samples.append(dict(total_us=elapsed, **durations))
    return elapsed, durations

  print(f'VARIANT {variant} {dtype}', flush=True)
  with patch.object(m.k.MatmulKernel, 'dram_tile_addr_from', address), \
       patch.object(m.k, 'emit_output_write_state_setup', setup), \
       patch.object(m, 'read_profile', profile):
    m.run(*args.shape, runs=args.runs, device_index=args.device, execute=True,
          profile=True, dtype=dtype, output_noc=args.output_noc,
          writer_wave_rows=int(variant[-1]) if variant.startswith('wave') else 0)
  row = dict(variant=variant, dtype=dtype, device=args.device, shape=args.shape,
             output_noc=args.output_noc, samples=samples,
             mean_us={name: mean(s[name] for s in samples) for name in samples[0]})
  print('RESULT ' + json.dumps(row), flush=True)
  return row


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device', type=int, required=True)
  parser.add_argument('--shape', type=int, nargs=3, default=(5000,5000,5000), metavar=('M','N','K'))
  parser.add_argument('--runs', type=int, default=9)
  parser.add_argument('--dtype', nargs='+', choices=('bf16','fp8'), default=['fp8'])
  parser.add_argument('--output-noc', choices=('split','0','1'), default='split')
  parser.add_argument('--variants', nargs='+', choices=VARIANTS,
                      default=['baseline','preferred','baseline','preferred'])
  parser.add_argument('--json', type=Path)
  args = parser.parse_args()
  rows = [benchmark(args, variant, dtype) for dtype in args.dtype for variant in args.variants]
  if args.json:
    args.json.write_text(json.dumps(rows, indent=2) + '\n')


if __name__ == '__main__':
  main()
