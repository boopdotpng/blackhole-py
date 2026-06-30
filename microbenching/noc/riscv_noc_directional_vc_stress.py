#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_aggregate as aggregate  # noqa: E402
from ttk.addrs import Core  # noqa: E402
from ttk.noc import NOC  # noqa: E402


VC_CHOICES = ("default", "vc0", "vc1", "vc2", "vc3", "vc4", "vc5", "rr", "split14", "split15")


@dataclass(frozen=True)
class DirectionalCase:
  row: int
  cut: tuple[Core, Core]
  pairs: list[aggregate.Pair]


def parse_cases(text: str) -> tuple[str, ...]:
  values = tuple(item.strip() for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated cases")
  bad = sorted(set(values) - set(VC_CHOICES))
  if bad:
    raise argparse.ArgumentTypeError(f"unknown cases: {', '.join(bad)}")
  return values


def parse_counts(text: str) -> tuple[int, ...]:
  values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not values or any(value <= 0 for value in values):
    raise argparse.ArgumentTypeError("expected comma-separated positive counts")
  return values


def _fmt_core(core: Core) -> str:
  return f"{core[0]},{core[1]}"


def _fmt_pair(pair: aggregate.Pair) -> str:
  return f"{_fmt_core(pair.source)}->{_fmt_core(pair.target)}"


def select_directional_case(cores: list[Core], *, noc: int, row: int | None, count: int | None) -> DirectionalCase:
  rows = aggregate.rows_by_y(cores)
  candidates = []
  for y, xs in rows.items():
    if row is not None and y != row:
      continue
    if len(xs) < 2:
      continue
    ordered = xs if noc == 0 else list(reversed(xs))
    for split in range(1, len(ordered)):
      upstream = ordered[:split]
      downstream = ordered[split:]
      capacity = min(len(upstream), len(downstream))
      if capacity <= 0:
        continue
      if count is not None and capacity < count:
        continue
      chosen_count = capacity if count is None else count
      cut = ((ordered[split - 1], y), (ordered[split], y))
      score = (-chosen_count, y, split)
      candidates.append((score, chosen_count, y, upstream, downstream, cut))
  if not candidates:
    need = "" if count is None else f" with {count} disjoint streams"
    raise ValueError(f"could not find a same-row directional cut{need}")

  _score, chosen_count, y, upstream, downstream, cut = min(candidates)
  sources = upstream[-chosen_count:]
  targets = downstream[:chosen_count]
  pairs = [aggregate.Pair((src, y), (dst, y)) for src, dst in zip(sources, targets)]
  return DirectionalCase(row=y, cut=cut, pairs=pairs)


def limit_streams(case: DirectionalCase, count: int) -> DirectionalCase:
  if count <= 0 or count > len(case.pairs):
    raise ValueError(f"count must be in [1, {len(case.pairs)}] for selected cut")
  return DirectionalCase(row=case.row, cut=case.cut, pairs=case.pairs[-count:])


def vcs_for_case(name: str, count: int) -> list[int | None]:
  if name == "default":
    return [None] * count
  if name.startswith("vc"):
    return [int(name[2:])] * count
  if name == "rr":
    return [i % 6 for i in range(count)]
  if name == "split14":
    return [1 if i % 2 == 0 else 4 for i in range(count)]
  if name == "split15":
    return [1 if i % 2 == 0 else 5 for i in range(count)]
  raise ValueError(f"unknown case {name}")


def vcs_label(vcs: list[int | None]) -> str:
  if all(vc is None for vc in vcs):
    return "default"
  return ",".join("d" if vc is None else str(vc) for vc in vcs)


def summarize(case_name: str, vcs: list[int | None], directional: DirectionalCase, *,
              noc: int, stream_bytes: int, senders: list[aggregate.CoreResult],
              receivers: list[aggregate.CoreResult], posted: bool) -> str:
  starts = [result.start for result in senders]
  acks = [result.end for result in senders]
  observed = [result.start for result in receivers]
  total_bytes = len(directional.pairs) * stream_bytes
  sender_window = max(acks) - min(starts)
  observed_window = max(observed) - min(starts)
  sender_bpc = total_bytes / sender_window if sender_window > 0 else 0.0
  observed_bpc = total_bytes / observed_window if observed_window > 0 else 0.0
  per_stream = [
    stream_bytes / (sender.end - sender.start)
    for sender in senders
    if sender.end > sender.start
  ]
  mean_stream = statistics.fmean(per_stream) if per_stream else 0.0
  min_stream = min(per_stream) if per_stream else 0.0
  max_stream = max(per_stream) if per_stream else 0.0
  expected_chunks = 0 if posted else stream_bytes // NOC.MAX_BURST_SIZE
  bad_acks = sum(((result.counter_after - result.counter_before) & 0xFFFFFFFF) != expected_chunks for result in senders)
  bad_sentinels = sum(result.words[11] != aggregate.observe.expected_sentinel(stream_bytes) for result in receivers)
  pairs = " ".join(_fmt_pair(pair) for pair in directional.pairs)
  cut = f"{_fmt_core(directional.cut[0])}->{_fmt_core(directional.cut[1])}"
  mode = "posted" if posted else "nonposted"
  return (
    f"| {case_name} | {mode} | `{vcs_label(vcs)}` | {noc} | {directional.row} | `{cut}` | "
    f"{len(directional.pairs)} | `{pairs}` | {total_bytes / (1024 * 1024):.2f} | "
    f"{sender_window} | {sender_bpc:.3f} | {observed_window} | {observed_bpc:.3f} | "
    f"{mean_stream:.3f} | {min_stream:.3f} | {max_stream:.3f} | {bad_acks} | {bad_sentinels} |"
  )


def main():
  parser = argparse.ArgumentParser(description="Stress many same-direction NoC write streams crossing one row cut while sweeping static VCs.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--row", type=int, default=None)
  parser.add_argument("--count", type=int, default=None, help="number of disjoint streams; default uses the best row/cut capacity")
  parser.add_argument("--counts", type=parse_counts, default=None, help="comma-separated stream-count sweep on one fixed selected cut")
  parser.add_argument("--bytes", type=int, default=256 * 1024, help="payload bytes per sender; multiple of 16 KiB")
  parser.add_argument("--cases", type=parse_cases, default=parse_cases("default,vc0,vc1,vc2,vc3,vc4,vc5,rr,split14,split15"))
  parser.add_argument("--posted", action="store_true", help="use posted writes and receiver-observed timing")
  parser.add_argument("--dry-run", action="store_true")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-directional-vc-stress.md"))
  args = parser.parse_args()

  if args.count is not None and args.count <= 0:
    raise ValueError("--count must be positive")
  if args.count is not None and args.counts is not None:
    raise ValueError("--count and --counts are mutually exclusive")
  if args.bytes <= 0 or args.bytes % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes must be a positive multiple of 16 KiB")
  if args.bytes > aggregate.observe.RESULT_BASE - aggregate.observe.STREAM_BASE:
    raise ValueError(f"--bytes must fit below result range; max is {aggregate.observe.RESULT_BASE - aggregate.observe.STREAM_BASE}")

  table_lines = [
    "| case | mode | vcs | noc | row | cut | streams | pairs | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | per-stream mean B/cyc | per-stream min | per-stream max | bad ack rows | bad sentinel rows |",
    "|---|---|---|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]

  if args.dry_run:
    with harness.open_device() as device:
      selected = select_directional_case(
        aggregate.usable_program_cores(device), noc=args.noc, row=args.row,
        count=max(args.counts) if args.counts is not None else args.count,
      )
    counts = args.counts or (len(selected.pairs),)
    print(f"NoC{args.noc} row {selected.row} cut {_fmt_core(selected.cut[0])}->{_fmt_core(selected.cut[1])}")
    print("selected pairs:", " ".join(_fmt_pair(pair) for pair in selected.pairs))
    for count in counts:
      directional = limit_streams(selected, count)
      print(f"count {count} pairs:", " ".join(_fmt_pair(pair) for pair in directional.pairs))
      for case_name in args.cases:
        print(f"{case_name}: {vcs_label(vcs_for_case(case_name, len(directional.pairs)))}")
    return

  with harness.open_device() as device:
    selected = select_directional_case(
      aggregate.usable_program_cores(device), noc=args.noc, row=args.row,
      count=max(args.counts) if args.counts is not None else args.count,
    )
    counts = args.counts or (len(selected.pairs),)
    for count in counts:
      directional = limit_streams(selected, count)
      for case_name in args.cases:
        vcs = vcs_for_case(case_name, len(directional.pairs))
        senders, receivers = aggregate.run_once(
          device, directional.pairs, noc=args.noc, stream_bytes=args.bytes, vcs=vcs, posted=args.posted,
        )
        table_lines.append(
          summarize(case_name, vcs, directional, noc=args.noc, stream_bytes=args.bytes,
                    senders=senders, receivers=receivers, posted=args.posted)
        )

  table = "\n".join(table_lines)
  print(table)
  if not args.no_report:
    harness.append_report(args.report, "NoC directional VC stress", [
      f"NoC: `{args.noc}`",
      f"Bytes per sender: `{args.bytes}`",
      f"Write mode: `{'posted' if args.posted else 'nonposted'}`",
      f"Counts: `{','.join(str(count) for count in (args.counts or (len(selected.pairs),)))}`",
      f"Cases: `{','.join(args.cases)}`",
      "Pairing: disjoint same-row streams crossing one directed row cut",
    ], table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
