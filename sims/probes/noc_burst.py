"""Measure per-worker completion times for one burst of TTRV reads or writes.

The default has every BRISC read the same region through the ordinary TTRV lowering. Buffer addresses
stay fixed across grid sizes. Each interval includes kernel entry through return.
"""

import argparse
import gzip
import json
from pathlib import Path

from role_cycles import Device, case, firmware_fingerprint


def source(workers, size, stride=0, ports="default", op="read", role="brisc", dtype="u32"):
  index = f"core.id * {stride}" if stride else "0"
  port = "" if ports == "default" else ", port=" + ("core.id % 3" if ports == "striped" else ports)
  count = size // (2 if dtype == "bf16" else 4)
  remote = f"input[{index}]"
  operands = f"result, {remote}" if op == "read" else f"{remote}, result"
  return f"""grid {workers}
param input: {dtype}[]
l1 result: {dtype}[{count}]
fn {role}() {{
  noc.{op} {operands}, n={count}{port}, wait
}}
"""


def main():
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--grids", type=int, nargs="+", default=[1, 4, 10, 20, 40, 88])
  ap.add_argument("--bytes", type=int, nargs="+", default=[64, 2048])
  ap.add_argument("--op", choices=["read", "write"], default="read")
  ap.add_argument("--role", choices=["brisc", "ncrisc"], default="brisc")
  ap.add_argument("--dtype", choices=["bf16", "u32"], default="u32")
  ap.add_argument("--ports", choices=["default", "0", "1", "2", "striped"], default="default")
  ap.add_argument("--stride", type=int, default=0, help="distance between worker addresses in elements")
  ap.add_argument("--repeats", type=int, default=41)
  ap.add_argument("--samples", type=int, default=5)
  ap.add_argument("--output", required=True, type=Path)
  a = ap.parse_args()
  width = 2 if a.dtype == "bf16" else 4
  if (
    a.stride < 0
    or a.stride * width % 64
    or any(n <= 0 or n % 4 for n in a.bytes)
    or min(a.samples, a.repeats) < 1
    or any(n not in range(1, 139) for n in a.grids)
  ):
    ap.error(
      "expected positive repetitions, 64-byte-aligned strides, aligned transfer sizes and grids of 1 to 138 workers"
    )
  dev = Device(a.device)
  try:
    args = {"input": dev.zeros(max(a.bytes) // width + (max(a.grids) - 1) * a.stride, a.dtype)}
    with gzip.open(a.output, "xt") as out:
      for size in a.bytes:
        for n in a.grids:
          row = case(
            dev, f"burst-{size}", source(n, size, a.stride, a.ports, a.op, a.role, a.dtype), args, a.repeats, a.samples
          )
          row.update(
            card=a.device,
            firmware_sha256=firmware_fingerprint(),
            size=size,
            stride=a.stride,
            ports=a.ports,
            op=a.op,
            role=a.role,
            dtype=a.dtype,
          )
          print(json.dumps(row), file=out, flush=True)
          print(f"{size} B, {n} workers", flush=True)
  finally:
    dev.close()


if __name__ == "__main__":
  main()
