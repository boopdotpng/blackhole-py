"""Instrument the fused RMSNorm boundary; excludes following projection math."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import statistics
import struct
from fw.consts import TensixL1, TensixMMIO
from pcie import TLBWindow
from ttko.sync import sync


def main():
  os.environ['LLAMA_RMSNORM'] = 'hybrid'
  parser = argparse.ArgumentParser()
  parser.add_argument('--device', type=int, required=True)
  parser.add_argument('--weights', required=True)
  parser.add_argument('--attention-cores', type=int, required=True)
  parser.add_argument('--output', default='validation/rmsnorm_stages_projection.json')
  args = parser.parse_args()
  report = {}
  for kind, path in (('reference', 'validation/rmsnorm_reference.py'),
                     ('hybrid', 'examples/llama3_8b.py')):
    profiles = []
    addresses = {}
    def stamp(p, end=False):
      if not end:
        # Item-count variants of one heterogeneous launch share the address.
        key = tuple(p.params)
        if key not in addresses:
          addresses[key] = TensixL1.DATA_BUFFER_SPACE_END-4096+32*len(addresses)
        p._rms_profile = addresses[key]
        profiles.append(p)
      for i, k in enumerate((p.trisc0, p.trisc1, p.trisc2)):
        sync(k)
        with k.scope():
          value = k.reg()
          k.read(value, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
          k.write(p._rms_profile+8*i+4*end, value)
          k.fence()
    def dot_stamp(p, end=False):
      if not hasattr(p, '_rms_profile'): return
      k = p.trisc1
      sync(k)
      with k.scope():
        value = k.reg()
        k.read(value, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
        k.write(p._rms_profile+24+4*end, value)
        k.fence()
    source = Path(path).read_text()
    anchor = '    if input_dim != EMBED_DIM: raise ValueError('
    pos = source.index(anchor)
    line_end = source.index('\n', pos)
    source = source[:line_end+1] + '    _stamp(p)\n' + source[line_end+1:]
    source = source.replace('    # Keep the rounded BF16 token', '    _stamp(p, True)\n    # Keep the rounded BF16 token', 1)
    source = source.replace('def _projection_dot_math(p, projections, input_tiles):',
                            'def _projection_dot_math(p, projections, input_tiles):\n  _dot_stamp(p)', 1)
    source = source.replace('\n\ndef _decode_projections_program(',
                            '\n  _dot_stamp(p, True)\n\ndef _decode_projections_program(', 1)
    spec = importlib.util.spec_from_file_location('profile_' + kind, path)
    module = importlib.util.module_from_spec(spec)
    module._stamp = stamp
    module._dot_stamp = dot_stamp
    exec(compile(source, path, 'exec'), module.__dict__)
    runtime = module.Llama3Decode(args.weights, args.device, attention_cores=args.attention_cores)
    try:
      for p in profiles:
        assert p._l1.next < TensixL1.DATA_BUFFER_SPACE_END-4096
      runtime.load_tokens([128000, 9906])
      samples = {name: [] for name, p in runtime.programs.items() if p in profiles}
      for repeat in range(8):
        runtime.decode(0, append=False)
        if repeat < 2: continue
        with TLBWindow(runtime.device.pcie.fd, runtime.device.pcie.cores[0]) as win:
          for name, p in runtime.programs.items():
            if p not in profiles: continue
            # All participating cores, including the slowest one.
            values = []
            for core in p.cores:
              win.target(0, core)
              raw = struct.unpack('<8I', win.read(p._rms_profile, 32))
              values.append([(raw[1]-raw[0])%2**32, (raw[3]-raw[2])%2**32,
                             (raw[5]-raw[4])%2**32, (raw[5]-raw[2])%2**32,
                             (raw[7]-raw[6])%2**32])
            samples[name].append(values)
      summary = {}
      for name, runs in samples.items():
        summary[name] = {label: statistics.median(max(row[i] for row in run) for run in runs)
          for i,label in enumerate(('unpack', 'math', 'pack_thread', 'math_start_to_pack_end', 'projection_math'))}
        print(kind, name, summary[name], flush=True)
      report[kind] = {'summary_cycles': summary, 'samples': samples}
    finally:
      runtime.close()
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
  main()
