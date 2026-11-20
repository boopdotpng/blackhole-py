"""Measure requester order at one NoC destination independently of DRAM service."""

import argparse
import gzip
import json
import struct
from unittest.mock import patch

from role_cycles import Device, Kernel, build, firmware_fingerprint
from ttrv.cycles import Simulation, _simulate


def tickets(dev, grid, role, target, repeats):
  column, row = target
  source = f"""grid {grid}
l1 ticket: u32[4]
l1 counter: u32[4], keep
fn {role}() {{
  noc.inc remote({column}, {row}, counter), by=1, ret=ticket, wait
}}
"""
  c = build(source)
  run = Kernel(dev, c, "arrival_order")
  loc = run.program.manifest["storage"]
  workers = dev.dev.workers[:grid]
  dst = workers[column * 10 + row]
  host, model = [], []
  for trial in range(repeats):
    dev.dev.iface.write(dst, loc["counter"]["address"], bytes(4))
    run()
    dev.synchronize()
    observed = [struct.unpack("<I", dev.dev.iface.read(xy, loc["ticket"]["address"], 4))[0] for xy in workers]
    if sorted(observed) != list(range(grid)):
      raise RuntimeError("hardware tickets did not form a permutation")
    host.append(observed)
    sim = Simulation()
    with patch("ttrv.cycles.Simulation", return_value=sim):
      _simulate(c, trial=trial, trials=repeats)
    predicted = [
      int.from_bytes(sim.memory(xy).read(c.manifest["storage"]["ticket"]["address"], 4), "little") for xy in workers
    ]
    if sorted(predicted) != list(range(grid)):
      raise RuntimeError("simulated tickets did not form a permutation")
    model.append(predicted)
  return dict(
    grid=grid, role=role, target=dst, workers=workers, observed=host, predicted=model, firmware=firmware_fingerprint()
  )


if __name__ == "__main__":
  p = argparse.ArgumentParser(description=__doc__)
  p.add_argument("--device", type=int, default=0)
  p.add_argument("--grids", nargs="+", type=int, default=[4, 10, 40, 88])
  p.add_argument("--repeats", type=int, default=41)
  p.add_argument("--output", required=True)
  a = p.parse_args()
  if not all(1 <= n <= 138 for n in a.grids) or a.repeats < 1:
    p.error("expected grids of 1 to 138 workers and a positive repeat count")
  dev = Device(a.device)
  try:
    with gzip.open(a.output, "xt") as out:
      for grid in a.grids:
        for role in ("brisc", "ncrisc"):
          for i in (0, grid - 1):
            r = tickets(dev, grid, role, divmod(i, 10), a.repeats)
            r["card"] = a.device
            print(json.dumps(r), file=out, flush=True)
            print(grid, role, i, flush=True)
  finally:
    dev.close()
