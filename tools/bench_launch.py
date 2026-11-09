"""Measure launch overhead with empty slots and with real binaries copied but execution disabled.
Run from the repository root: ../.venv/bin/python tools/bench_launch.py
"""
import argparse, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import fw
from cq import ComputeQueue, Launch
from llama1b import Llama1B


def copied_noop(dev, launch):
  """Clone a descriptor, retaining every code transfer but zeroing its active-role masks."""
  header = list(struct.unpack('<8I', dev.pci_dev.read(dev.cq_core, launch.addr, 32)))
  payload = bytearray(header[3])
  dev.copyout(payload, header[4] | header[5] << 32)
  offset = launch.addr + 32 + 4 * header[1]
  for _ in range(header[6]):
    src, dst, size, nrects = struct.unpack('<4I', dev.pci_dev.read(dev.cq_core, offset, 16))
    if dst == fw.LAUNCH: payload[src:src + size] = bytes(size)
    offset += 16 + 4 * nrects
  descriptor = bytearray(dev.pci_dev.read(dev.cq_core, launch.addr, offset - launch.addr))
  addr = dev.upload(payload)
  struct.pack_into('<II', descriptor, 16, addr & 0xFFFFFFFF, addr >> 32)
  at = dev.descriptor_top
  assert at + len(descriptor) <= fw.DESCRIPTOR_END
  dev.pci_dev.write(dev.cq_core, at, descriptor)
  dev.descriptor_top = (at + len(descriptor) + 63) & -64
  return Launch(at, launch.args_size)


def measure(m, launches, reps):
  d = m.dev
  q = ComputeQueue().timestamp(d.signal(240))
  for launch in launches: q.exec(launch, m.args_base)
  q.timestamp(d.signal(241))
  graph = d.capture(q)
  samples = []
  for _ in range(reps + 2):
    d.replay(graph)
    samples.append((d.read_signal(241)[1] - d.read_signal(240)[1]) * m.ns_per_tick / 1000 / len(launches))
  return float(np.median(samples[2:]))


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument('--reps', type=int, default=30)
  a = ap.parse_args()
  m = Llama1B()
  try:
    m._upload_args(1, 1)
    copied = {name: copied_noop(m.dev, launch) for name, launch in m.prog.items()}
    print('program       payload_B  multicasts   empty_us  code_copy_us  extra_us')
    for name, launch in m.prog.items():
      empty = measure(m, [m.noop[name]] * 32, a.reps)
      full = measure(m, [copied[name]] * 32, a.reps)
      print(f'{name:12} {launch.payload_bytes:10} {launch.multicasts:11} {empty:10.3f} {full:13.3f} {full-empty:9.3f}', flush=True)
    for label, programs in [('empty', m.noop), ('copied', copied)]:
      t = measure(m, [programs[name] for name, _ in m.launches], a.reps)
      print(f'{label}: {t:.3f} us/EXEC, {83*t:.3f} us/token', flush=True)
    ref = json.loads((Path(__file__).resolve().parents[1] / 'kernels/llama1b/reference.json').read_text())
    for steps in (64, 1, 64):
      gen, stats = m.generate(ref['prompt_ids'], steps)
      assert gen == ref['generated_ids'][:steps]
      print(f'real decode: {steps} tokens match, {stats["period_us"]:.3f} us/token', flush=True)
  finally: m.close()

if __name__ == '__main__': main()
