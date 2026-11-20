"""Per-worker time for the projections' weight stream alone: every BRISC reads its rows of one DRAM matrix.

Each worker reads rows first..first + count of a [ROWS, DIM] BF16 matrix, one row per request group, waiting for
each row before the next, exactly as the projection kernels' BRISC does, without any Tensix work. Variants change
the row size, the port choice and the worker count. The result keeps every hardware repetition per worker.
"""

import argparse
import gzip
import json
from pathlib import Path

from role_cycles import Device, case, firmware_fingerprint


def source(workers, rows, dim, port):
  port = {"striped": "core.id % 3", "column": "core.id / 10 % 3"}.get(port, port)
  return f"""grid {workers}
param w: bf16[]
l1 row_buf: bf16[{dim}]
shared {{ first, count = split({rows}) }}
fn brisc() {{
  for row in first..first + count {{
    noc.read row_buf, w[row * {dim}], n={dim}, port={port}, wait
  }}
}}
"""


def fanin(workers, reads, port):
  """Every worker reads its own run of 2 KiB pages, all on DRAM bank 0 (every 8th page), one at a time."""
  port = {"striped": "core.id % 3"}.get(port, port)
  return f"""grid {workers}
param w: bf16[]
l1 row_buf: bf16[1024]
fn brisc() {{
  for j in 0..{reads} {{
    noc.read row_buf, w[(core.id * {reads} + j) * 8192], n=1024, port={port}, wait
  }}
}}
"""


FANIN = {f"bank0-{n}": (n, 16, "striped") for n in (1, 2, 4, 8, 16, 44, 88)}

CASES = {
  # name: (workers, rows, dim, port)
  "lm-1b": (88, 88 * 48, 2048, "striped"),
  "lm-8b": (88, 88 * 24, 4096, "striped"),
  "port0": (88, 88 * 48, 2048, "0"),
  "column": (88, 88 * 48, 2048, "column"),
  "half": (44, 44 * 48, 2048, "striped"),
  "short": (88, 88 * 8, 2048, "striped"),
  **{f"rows{n}": (88, 88 * n, 2048, "striped") for n in (1, 2, 4, 16)},
  "rows4-solo": (1, 4, 2048, "striped"),
  "rows16-solo": (1, 16, 2048, "striped"),
}


def main():
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--cases", nargs="+", default=list(CASES), choices=list(CASES) + list(FANIN))
  ap.add_argument("--repeats", type=int, default=15)
  ap.add_argument("--output", required=True, type=Path)
  a = ap.parse_args()
  dev = Device(a.device)
  try:
    with gzip.open(a.output, "xt") as out:
      for name in a.cases:
        if name in FANIN:
          workers, reads, port = FANIN[name]
          text, elements = fanin(workers, reads, port), workers * reads * 8192
        else:
          workers, rows, dim, port = CASES[name]
          text, elements = source(workers, rows, dim, port), rows * dim
        args = {"w": dev.zeros(elements, "bf16")}
        row = case(dev, name, text, args, a.repeats)
        row.update(card=a.device, firmware_sha256=firmware_fingerprint(), source=text, w=args["w"].addr)
        print(json.dumps(row), file=out, flush=True)
        print(name, flush=True)
  finally:
    dev.close()


if __name__ == "__main__":
  main()
