#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_contention_probe as probe  # noqa: E402
from asm import KernelBase  # noqa: E402
from program import DevMsgs, Program, Run, UnicastWrite  # noqa: E402
from ttk.addrs import Core, noc_xy  # noqa: E402
from ttk.mailbox import BriscMailbox as BM, NcriscMailbox as NM  # noqa: E402
from ttk.noc import NOC  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402


@dataclass(frozen=True)
class CrossStream:
  name: str
  source: Core
  target: Core
  noc: int
  result_base: int


@dataclass(frozen=True)
class Case:
  name: str
  streams: tuple[CrossStream, CrossStream]


class CrossNocL1Program:
  def __init__(self, streams: list[CrossStream], *, stream_bytes: int, repeats: int):
    self.streams = list(streams)
    self.stream_bytes = stream_bytes
    self.repeats = repeats
    self.name = f"riscv_noc_cross_endpoint_interference:streams{len(streams)}"

  def _kernel(self, stream: CrossStream, *, ncrisc: bool):
    return probe.build_stream_kernel(
      noc=stream.noc,
      role=probe.ROLE_WRITER,
      stream_bytes=self.stream_bytes,
      repeats=self.repeats,
      result_base=stream.result_base,
      rta_ptr=NM.RTA_L1_BASE_PTR if ncrisc else BM.RTA_L1_BASE_PTR,
      my_x_addr=NM.MY_X if ncrisc else BM.MY_X,
      my_y_addr=NM.MY_Y if ncrisc else BM.MY_Y,
    )

  def lower(self, cores: list[Core] | None = None, *, dispatch_mode=DevMsgs.DISPATCH_MODE_HOST, host_assigned_id=0):
    per_core_segments = {}
    target_cores = sorted({stream.source for stream in self.streams} | {stream.target for stream in self.streams})
    by_source: dict[Core, list[CrossStream]] = {}
    for stream in self.streams:
      by_source.setdefault(stream.source, []).append(stream)
    for source, streams in by_source.items():
      if len(streams) > 2:
        raise ValueError(f"{source}: at most two active streams per source core are supported")
      ordered = sorted(streams, key=lambda stream: stream.noc)
      brisc = self._kernel(ordered[0], ncrisc=False)
      brisc.rta(lambda _x, _y, target=ordered[0].target: [noc_xy(*target)])
      ncrisc = KernelBase()
      if len(ordered) == 2:
        ncrisc = self._kernel(ordered[1], ncrisc=True)
        ncrisc.rta(lambda _x, _y, target=ordered[1].target: [noc_xy(*target)])
      per_core_segments[source] = probe.one_core_program(brisc, ncrisc=ncrisc).layout(
        core_xy=source, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )
    for target in sorted({stream.target for stream in self.streams} - set(by_source)):
      per_core_segments[target] = probe.one_core_program(KernelBase().ret()).layout(
        core_xy=target, dispatch_mode=dispatch_mode, host_assigned_id=host_assigned_id,
      )

    reset_blob = struct.pack("<BBBB", 0, 0, 0, DevMsgs.RUN_MSG_RESET_READ_PTR_FROM_HOST)
    commands = [
      UnicastWrite(target_cores, TensixL1.GO_MSG, [reset_blob] * len(target_cores)),
      UnicastWrite(target_cores, TensixL1.GO_MSG_INDEX, [b"\0\0\0\0"] * len(target_cores)),
    ]
    for core in target_cores:
      for segment in per_core_segments[core]:
        commands.append(UnicastWrite([core], segment.addr, [segment.data]))
    commands.append(Run(target_cores))
    return commands


def _fmt_core(core: Core) -> str:
  return f"{core[0]},{core[1]}"


def default_cases() -> dict[str, Case]:
  return {
    "same-l1-target": Case("same-l1-target", (
      CrossStream("noc0", (1, 4), (4, 4), 0, probe.RESULT_BASE),
      CrossStream("noc1", (10, 4), (4, 4), 1, probe.RESULT_BASE),
    )),
    "same-l1-source": Case("same-l1-source", (
      CrossStream("noc0", (4, 4), (7, 4), 0, probe.RESULT_BASE),
      CrossStream("noc1", (4, 4), (1, 4), 1, probe.RESULT_BASE + probe.RESULT_STRIDE),
    )),
    "disjoint-l1": Case("disjoint-l1", (
      CrossStream("noc0", (1, 5), (4, 5), 0, probe.RESULT_BASE),
      CrossStream("noc1", (13, 6), (10, 6), 1, probe.RESULT_BASE),
    )),
  }


def parse_cases(text: str) -> tuple[str, ...]:
  names = tuple(item.strip() for item in text.split(",") if item.strip())
  if not names:
    raise argparse.ArgumentTypeError("expected comma-separated case names")
  valid = set(default_cases())
  bad = sorted(set(names) - valid)
  if bad:
    raise argparse.ArgumentTypeError(f"unknown cases: {', '.join(bad)}")
  return names


def validate_case(case: Case, cores: set[Core]):
  used = {stream.source for stream in case.streams} | {stream.target for stream in case.streams}
  missing = sorted(used - cores)
  if missing:
    raise ValueError(f"case {case.name} uses unavailable cores: {missing}")
  if any(stream.noc not in (0, 1) for stream in case.streams):
    raise ValueError(f"case {case.name}: NoC ids must be 0 or 1")
  per_source: dict[Core, list[CrossStream]] = {}
  for stream in case.streams:
    per_source.setdefault(stream.source, []).append(stream)
  for source, streams in per_source.items():
    if len(streams) == 2 and streams[0].result_base == streams[1].result_base:
      raise ValueError(f"case {case.name}: same-source streams at {source} need distinct result bases")


def run_streams(device, streams: list[CrossStream], *, stream_bytes: int, repeats: int,
                dry_run: bool, gate_delay_cycles: int):
  all_cores = sorted({stream.source for stream in streams} | {stream.target for stream in streams})
  if not dry_run:
    probe.clear_cores(
      device,
      all_cores,
      stream_bytes=stream_bytes,
      source_cores={stream.source for stream in streams},
      target_cores={stream.target for stream in streams},
    )
  program = CrossNocL1Program(streams, stream_bytes=stream_bytes, repeats=repeats)
  probe.maybe_run(device, program, all_cores, dry_run=dry_run, gate_delay_cycles=gate_delay_cycles)
  if dry_run:
    return []
  return [
    probe.read_result(device, stream.source, result_base=stream.result_base, name=stream.name)
    for stream in streams
  ]


def aggregate_window(results: list[probe.Result]) -> tuple[int, float]:
  start = min(result.start for result in results)
  end = max(result.end for result in results)
  cycles = end - start
  total_bytes = sum(result.bytes_or_iters for result in results)
  return cycles, total_bytes / cycles if cycles > 0 else 0.0


def stream_label(stream: CrossStream) -> str:
  return f"NoC{stream.noc} `{_fmt_core(stream.source)}->{_fmt_core(stream.target)}`"


def result_cell(result: probe.Result | None, *, dry_run: bool) -> str:
  if dry_run:
    return "dry-run"
  assert result is not None
  return f"{result.bytes_per_cycle():.3f} ({result.counter_delta})"


def main():
  parser = argparse.ArgumentParser(description="Run simultaneous NoC0+NoC1 peer-L1 endpoint interference cases.")
  parser.add_argument("--cases", type=parse_cases, default=parse_cases("same-l1-target,same-l1-source,disjoint-l1"))
  parser.add_argument("--bytes", type=int, default=256 * 1024, help="bytes per stream repeat; multiple of 16 KiB")
  parser.add_argument("--repeats", type=int, default=2)
  parser.add_argument("--gate-delay-cycles", type=int, default=200_000_000)
  parser.add_argument("--dry-run", action="store_true")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-cross-endpoint-interference.md"))
  args = parser.parse_args()
  probe.validate_bytes(args.bytes)
  if args.repeats <= 0:
    raise ValueError("--repeats must be positive")
  if args.gate_delay_cycles < 0:
    raise ValueError("--gate-delay-cycles must be non-negative")

  cases = default_cases()
  rows = [
    "| case | stream A | stream B | A alone B/cyc (ctr) | B alone B/cyc (ctr) | A mixed B/cyc (ctr) | B mixed B/cyc (ctr) | mixed aggregate B/cyc | mixed window cyc |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|",
  ]
  device_cm = _null_device() if args.dry_run else harness.open_device()
  with device_cm as device:
    core_set = set(probe.usable_cores(device if not args.dry_run else None))
    for case_name in args.cases:
      case = cases[case_name]
      validate_case(case, core_set)
      a, b = case.streams
      a_alone = run_streams(
        device, [a], stream_bytes=args.bytes, repeats=args.repeats,
        dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles,
      )
      b_alone = run_streams(
        device, [b], stream_bytes=args.bytes, repeats=args.repeats,
        dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles,
      )
      mixed = run_streams(
        device, [a, b], stream_bytes=args.bytes, repeats=args.repeats,
        dry_run=args.dry_run, gate_delay_cycles=args.gate_delay_cycles,
      )
      if args.dry_run:
        agg_bpc = "dry-run"
        window = "dry-run"
      else:
        window_i, agg = aggregate_window(mixed)
        agg_bpc = f"{agg:.3f}"
        window = str(window_i)
      rows.append(
        f"| {case.name} | {stream_label(a)} | {stream_label(b)} | "
        f"{result_cell(a_alone[0] if a_alone else None, dry_run=args.dry_run)} | "
        f"{result_cell(b_alone[0] if b_alone else None, dry_run=args.dry_run)} | "
        f"{result_cell(mixed[0] if mixed else None, dry_run=args.dry_run)} | "
        f"{result_cell(mixed[1] if mixed else None, dry_run=args.dry_run)} | "
        f"{agg_bpc} | {window} |"
      )

  table = "\n".join(rows)
  print(table)
  if not args.no_report and not args.dry_run:
    harness.append_report(args.report, "L1 cross-NoC endpoint interference", [
      f"Bytes per stream repeat: `{args.bytes}`",
      f"Repeats: `{args.repeats}`",
      f"Start gate lead: `{args.gate_delay_cycles}` cycles",
      "Traffic: two peer-L1 nonposted write streams, one on NoC0 and one on NoC1",
      "Counters: parentheses show per-stream NIU write-ack counter delta",
    ], table)
    print(f"\nappended {args.report}")


class _null_device:
  def __enter__(self):
    return None

  def __exit__(self, exc_type, exc, tb):
    return False


if __name__ == "__main__":
  main()
