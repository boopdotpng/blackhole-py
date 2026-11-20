"""Compare hardware busy counters and simulator activity for isolated TTRV operations."""

import argparse
from dataclasses import replace
import struct
import gzip
import json
from pathlib import Path

from role_cycles import Device, build, case, firmware_fingerprint, fw, isa


def kernels():
  for n in (64, 128, 256, 512, 1024):
    for unit in ("unpack", "pack"):
      setup, role, op = (
        ("unpack.fmt a, in=bf16", "trisc0", f"unpack.move a, data, n={n}")
        if unit == "unpack"
        else ("pack.fmt in=fp32, out=bf16", "trisc2", f"pack.move data, dst[0], n={n}")
      )
      for count in (1, 16):
        yield (
          f"{unit}-{n}-{count}",
          f"""grid 1
l1 data: bf16[1024]
fn {role}() {{
  {setup}
  loop {count} {{ {op} }}
  tensix.wait
}}
""",
        )
  yield (
    "zero-face",
    """grid 1
fn trisc1() {
  math.fmt dst=fp32, sfp=fp32
  loop 64 { math.zero face=0, fmt=fp32 }
  tensix.wait
}
""",
  )


def fetch_kernels():
  for role in ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2"):
    kernel = build(f"grid 1\nfn {role}() {{ fence }}")
    for n in (32, 128, 512):
      for fences in (False, True):
        words = [isa.rv("fence") if fences and i % 8 == 7 else isa.rv("addi", 5, 5, imm=1) for i in range(n)]
        img = struct.pack(f"<{n}I", *words) + fw.ret(role)
        yield f"fetch-{role}-{n}-{'fenced' if fences else 'addi'}", replace(kernel, images={role: img})


def branch_fetch_kernels(distances):
  # Keep the executed instruction count fixed while moving the taken branch target
  # across cache lines. A jump to the next word is the control for branch cost.
  for role in ("brisc", "ncrisc", "trisc0"):
    template = build(f"grid 1\nfn {role}() {{ fence }}")
    for distance in distances:
      jumps = 24
      words = [isa.rv("addi", 0, 0, imm=0)] * (jumps * distance)
      for index in range(0, len(words), distance):
        words[index] = isa.rv("jal", 0, imm=4 * distance)
      image = struct.pack(f"<{len(words)}I", *words) + fw.ret(role)
      yield f"fetch-jump-{role}-{distance}", replace(template, images={role: image})


def main():
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--fetch", action="store_true", help="measure cold images with and without intervening fences")
  ap.add_argument("--branch-fetch", action="store_true", help="measure first-pass taken jumps at different distances")
  ap.add_argument("--distances", nargs="+", type=int, default=[1, 4, 8, 16, 32], help="taken jump distances in words")
  ap.add_argument("--output", type=Path, required=True)
  a = ap.parse_args()
  if a.branch_fetch and any(d < 1 or 24 * 4 * d + 36 > fw.CODE_SIZE["trisc0"] for d in a.distances):
    ap.error("jump distances must fit in a stamped TRISC image")
  dev = Device(a.device)
  try:
    with gzip.open(a.output, "xt") as out:
      cases = branch_fetch_kernels(a.distances) if a.branch_fetch else fetch_kernels() if a.fetch else kernels()
      for name, source in cases:
        r = case(dev, name, source, {}, 11, counters=True)
        r.update(card=a.device, firmware_sha256=firmware_fingerprint())
        print(json.dumps(r), file=out, flush=True)
        c = r["tiles"][0]["hardware_counters"]
        row = r["cores"][0]
        print(name, row["cycles"], row["measured"], c["unpack"], c["pack"], c["fpu"], row.get("unit_busy"), flush=True)
  finally:
    dev.close()


if __name__ == "__main__":
  main()
