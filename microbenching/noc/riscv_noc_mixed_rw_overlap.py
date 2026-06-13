#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_contention_probe as probe  # noqa: E402
from ttk.addrs import Core  # noqa: E402
from ttk.noc import NOC  # noqa: E402


@dataclass(frozen=True)
class Case:
  name: str
  read_source: Core
  read_target: Core
  write_source: Core
  write_target: Core


def _fmt_core(core: Core) -> str:
  return f"{core[0]},{core[1]}"


def _cases_for_noc(noc: int) -> list[Case]:
  if noc == 0:
    return [
      Case("independent", (4, 4), (1, 4), (10, 5), (13, 5)),
      Case("shared-payload-link", (4, 4), (1, 4), (2, 4), (5, 4)),
    ]
  if noc == 1:
    return [
      Case("independent", (1, 4), (4, 4), (13, 5), (10, 5)),
      Case("shared-payload-link", (1, 4), (4, 4), (5, 4), (2, 4)),
    ]
  raise ValueError(f"noc must be 0 or 1, got {noc}")


def parse_cases(text: str) -> tuple[str, ...]:
  names = tuple(item.strip() for item in text.split(",") if item.strip())
  if not names:
    raise argparse.ArgumentTypeError("expected comma-separated case names")
  valid = {"independent", "shared-payload-link"}
  bad = sorted(set(names) - valid)
  if bad:
    raise argparse.ArgumentTypeError(f"unknown cases: {', '.join(bad)}")
  return names


def validate_case(case: Case, core_set: set[Core]):
  cores = {case.read_source, case.read_target, case.write_source, case.write_target}
  missing = sorted(cores - core_set)
  if missing:
    raise ValueError(f"case {case.name} uses unavailable cores: {missing}")
  active = [case.read_source, case.write_source]
  if len(set(active)) != len(active):
    raise ValueError(f"case {case.name} needs distinct active source cores")


def stream_pair(case: Case) -> tuple[probe.ActiveStream, probe.ActiveStream]:
  read_stream = probe.ActiveStream(
    "read",
    case.read_source,
    case.read_target,
    probe.ROLE_READER,
    probe.RESULT_BASE,
  )
  write_stream = probe.ActiveStream(
    "write",
    case.write_source,
    case.write_target,
    probe.ROLE_WRITER,
    probe.RESULT_BASE,
  )
  return read_stream, write_stream


def run_streams(device, streams: list[probe.ActiveStream], *, noc: int, stream_bytes: int, repeats: int, gate_delay_cycles: int):
  return probe.run_stream_set(
    device,
    streams,
    noc=noc,
    stream_bytes=stream_bytes,
    repeats=repeats,
    dry_run=False,
    gate_delay_cycles=gate_delay_cycles,
  )


def aggregate_window(results: list[probe.Result]) -> tuple[int, float]:
  start = min(result.start for result in results)
  end = max(result.end for result in results)
  cycles = end - start
  total_bytes = sum(result.bytes_or_iters for result in results)
  return cycles, total_bytes / cycles if cycles > 0 else 0.0


def result_cell(result: probe.Result) -> str:
  return f"{result.bytes_per_cycle():.3f} ({result.counter_delta})"


def main():
  parser = argparse.ArgumentParser(description="Safe mixed read/write NoC overlap probe with distinct active source cores.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--cases", type=parse_cases, default=parse_cases("independent,shared-payload-link"))
  parser.add_argument("--bytes", type=int, default=1024 * 1024, help="bytes per stream repeat; multiple of 16 KiB")
  parser.add_argument("--repeats", type=int, default=1)
  parser.add_argument("--gate-delay-cycles", type=int, default=200_000_000)
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-mixed-rw-overlap.md"))
  args = parser.parse_args()
  probe.validate_bytes(args.bytes)
  if args.repeats <= 0:
    raise ValueError("--repeats must be positive")
  if args.gate_delay_cycles < 0:
    raise ValueError("--gate-delay-cycles must be non-negative")

  rows = [
    "| case | noc | read payload | write payload | read-alone B/cyc | write-alone B/cyc | mixed read B/cyc | mixed write B/cyc | mixed aggregate B/cyc | mixed window cyc |",
    "|---|---:|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  metadata = [
    f"NoC: `{args.noc}`",
    f"Bytes per stream repeat: `{args.bytes}`",
    f"Repeats: `{args.repeats}`",
    f"Start gate lead: `{args.gate_delay_cycles}` cycles",
    "Traffic: one read stream plus one write stream, with distinct active source cores",
  ]

  selected = {case.name: case for case in _cases_for_noc(args.noc)}
  with harness.open_device() as device:
    core_set = set(device.cores)
    for case_name in args.cases:
      case = selected[case_name]
      validate_case(case, core_set)
      read_stream, write_stream = stream_pair(case)
      read_alone = run_streams(
        device,
        [read_stream],
        noc=args.noc,
        stream_bytes=args.bytes,
        repeats=args.repeats,
        gate_delay_cycles=args.gate_delay_cycles,
      )[0]
      write_alone = run_streams(
        device,
        [write_stream],
        noc=args.noc,
        stream_bytes=args.bytes,
        repeats=args.repeats,
        gate_delay_cycles=args.gate_delay_cycles,
      )[0]
      mixed = run_streams(
        device,
        [read_stream, write_stream],
        noc=args.noc,
        stream_bytes=args.bytes,
        repeats=args.repeats,
        gate_delay_cycles=args.gate_delay_cycles,
      )
      mixed_by_role = {result.role: result for result in mixed}
      window_cycles, aggregate_bpc = aggregate_window(mixed)
      rows.append(
        f"| {case.name} | {args.noc} | `{_fmt_core(case.read_target)}->{_fmt_core(case.read_source)}` | "
        f"`{_fmt_core(case.write_source)}->{_fmt_core(case.write_target)}` | "
        f"{read_alone.bytes_per_cycle():.3f} | {write_alone.bytes_per_cycle():.3f} | "
        f"{result_cell(mixed_by_role[probe.ROLE_READER])} | {result_cell(mixed_by_role[probe.ROLE_WRITER])} | "
        f"{aggregate_bpc:.3f} | {window_cycles} |"
      )

  table = "\n".join(rows)
  print("\n".join(f"- {line}" for line in metadata))
  print()
  print(table)
  if not args.no_report:
    harness.append_report(args.report, None, metadata, table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
