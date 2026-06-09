#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import statistics
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import riscv_core_bench as corebench
from asm import KernelBase
from device import Device
from dsl import a2, a3, s0, s1, s2, t0, zero
from pcie import TLBWindow
from program import Program
from ttk.addrs import Core
from ttk.tensix import TensixMMIO


RESULT_BASE = 0x118000
HEADER_WORDS = 16
HEADER_SIZE = HEADER_WORDS * 4
SAMPLE_SIZE = 8
RESULT_MAGIC = 0x52435743  # "RCWC"
STATUS_STARTED = 0x57000001
STATUS_DONE = 0x5700D00D


@dataclass(frozen=True)
class ClockStats:
  core_a: Core
  core_b: Core
  samples: int
  deltas: list[int]
  periods_a: list[int]
  periods_b: list[int]


def result_size(samples: int) -> int:
  return HEADER_SIZE + samples * SAMPLE_SIZE


def emit_header(fw: KernelBase, *, samples: int, status: int):
  fw.li(s2, RESULT_BASE)
  for off, value in enumerate((
    RESULT_MAGIC, 1, samples, status, RESULT_BASE, SAMPLE_SIZE,
    TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H,
  )):
    fw.li(t0, value)
    fw.sw(t0, s2, off * 4)
  for off in range(8, HEADER_WORDS):
    fw.sw(zero, s2, off * 4)
  return fw


def build_kernel(samples: int) -> KernelBase:
  fw = KernelBase()
  emit_header(fw, samples=samples, status=STATUS_STARTED)
  fw.li(s2, RESULT_BASE + HEADER_SIZE)
  fw.li(s0, samples)
  loop = fw._new_label("clock_sample")
  done = fw._new_label("clock_sample_done")
  fw.label(loop)
  fw.beq(s0, zero, done)
  corebench.read_wall_clock(fw, a2, a3)
  fw.sw(a2, s2, 0)
  fw.sw(a3, s2, 4)
  fw.addi(s2, s2, SAMPLE_SIZE)
  fw.addi(s0, s0, -1)
  fw.j(loop)
  fw.label(done)
  emit_header(fw, samples=samples, status=STATUS_DONE)
  return fw.ret()


def build_program(samples: int, core_a: Core, core_b: Core) -> Program:
  if core_a[1] != core_b[1]:
    raise ValueError("this initial skew probe needs same-row cores")
  empty = KernelBase()
  kernel = build_kernel(samples)
  cols = tuple(sorted((core_a[0], core_b[0])))
  program = Program(
    brisc=kernel,
    ncrisc=empty,
    trisc0=empty,
    trisc1=empty,
    trisc2=empty,
    grid=((core_a[1],), cols),
  )
  program.name = "riscv_wall_clock_skew:brisc_pair"
  return program


def clear_results(device: Device, cores: list[Core], samples: int):
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=cores[0]) as win:
      for target in cores:
        win.target(target)
        win.write(RESULT_BASE, b"\0" * result_size(samples))
  finally:
    device.dev.set_power_state(False)


def read_core_samples(device: Device, target: Core, samples: int) -> list[int]:
  device.dev.set_power_state(True)
  try:
    with TLBWindow(device.dev, start=target) as win:
      blob = win.read(RESULT_BASE, result_size(samples))
  finally:
    device.dev.set_power_state(False)
  if blob and all(b == 0xFF for b in blob):
    raise RuntimeError("L1 readback returned all 0xff; device is not responding cleanly")
  header = struct.unpack_from("<" + "I" * HEADER_WORDS, blob, 0)
  if header[0] != RESULT_MAGIC:
    raise RuntimeError(f"{target}: bad result magic 0x{header[0]:08x}")
  if header[3] != STATUS_DONE:
    raise RuntimeError(f"{target}: benchmark did not finish, status=0x{header[3]:08x}")
  if header[2] != samples:
    raise RuntimeError(f"{target}: expected {samples} samples, got {header[2]}")
  out = []
  for i in range(samples):
    lo, hi = struct.unpack_from("<II", blob, HEADER_SIZE + i * SAMPLE_SIZE)
    out.append(lo | (hi << 32))
  return out


def summarize_ints(values: list[int]) -> str:
  if not values:
    return "n/a"
  return (
    f"min={min(values)} avg={statistics.fmean(values):.3f} "
    f"median={statistics.median(values):.3f} max={max(values)}"
  )


def compute_stats(core_a: Core, core_b: Core, samples_a: list[int], samples_b: list[int]) -> ClockStats:
  if len(samples_a) != len(samples_b):
    raise ValueError("sample length mismatch")
  deltas = [b - a for a, b in zip(samples_a, samples_b)]
  periods_a = [b - a for a, b in zip(samples_a, samples_a[1:])]
  periods_b = [b - a for a, b in zip(samples_b, samples_b[1:])]
  return ClockStats(core_a, core_b, len(samples_a), deltas, periods_a, periods_b)


def format_summary(stats: ClockStats) -> str:
  jitter = max(stats.deltas) - min(stats.deltas) if stats.deltas else 0
  lines = [
    f"Core A: `{stats.core_a[0]},{stats.core_a[1]}`",
    f"Core B: `{stats.core_b[0]},{stats.core_b[1]}`",
    f"Samples: `{stats.samples}`",
    f"B - A timestamp delta: {summarize_ints(stats.deltas)}",
    f"B - A delta span: `{jitter}` cycles",
    f"Core A sample period: {summarize_ints(stats.periods_a)}",
    f"Core B sample period: {summarize_ints(stats.periods_b)}",
  ]
  return "\n".join(lines)


def append_report(path: Path, stats: ClockStats):
  with path.open("a", encoding="utf-8") as f:
    f.write("\n## Run\n\n")
    f.write(format_summary(stats))
    f.write("\n")


def select_default_pair(cores: list[Core]) -> tuple[Core, Core]:
  rows: dict[int, list[int]] = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  for y, xs in sorted(rows.items()):
    xs = sorted(xs)
    if len(xs) >= 2:
      return (xs[0], y), (xs[1], y)
  raise ValueError("need at least two same-row program cores")


def main():
  parser = argparse.ArgumentParser(description="Measure cross-core WALL_CLOCK_L/H sample stability.")
  parser.add_argument("--core-a", type=corebench.parse_core, default=None, help="first same-row core X,Y")
  parser.add_argument("--core-b", type=corebench.parse_core, default=None, help="second same-row core X,Y")
  parser.add_argument("--samples", type=int, default=4096, help="timestamp samples per core")
  parser.add_argument("--no-report", action="store_true", help="do not append docs/wall-clock-skew.md")
  parser.add_argument("--report", type=Path, default=Path("docs/wall-clock-skew.md"), help="markdown report path")
  args = parser.parse_args()
  if args.samples <= 1:
    raise ValueError("--samples must be greater than 1")

  os.environ.setdefault("TT_USB", "1")
  device = Device()
  try:
    if args.core_a is None or args.core_b is None:
      core_a, core_b = select_default_pair(device.cores)
    else:
      core_a, core_b = args.core_a, args.core_b
    if core_a not in set(device.cores) or core_b not in set(device.cores):
      raise ValueError("selected cores must be program cores")
    clear_results(device, [core_a, core_b], args.samples)
    device.run(build_program(args.samples, core_a, core_b))
    samples_a = read_core_samples(device, core_a, args.samples)
    samples_b = read_core_samples(device, core_b, args.samples)
  finally:
    device.close()

  stats = compute_stats(core_a, core_b, samples_a, samples_b)
  print(format_summary(stats))
  if not args.no_report:
    append_report(args.report, stats)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
