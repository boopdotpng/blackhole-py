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
import riscv_noc_arb_priority_order as order  # noqa: E402
from device import Device  # noqa: E402
from ttk.addrs import Core  # noqa: E402
from ttk.noc import NOC  # noqa: E402


@dataclass(frozen=True)
class VictimCase:
  row: int
  cut: tuple[Core, Core]
  victim: aggregate.Pair
  interferers: list[aggregate.Pair]


@dataclass(frozen=True)
class Trial:
  mode: str
  victim_priority: int
  background_priority: int | None
  repeat: int
  victim_sender_cycles: int
  victim_receiver_cycles: int
  victim_done_delta: int
  victim_seen_delta: int
  start_skew: int
  ready_avg: float
  ready_max: int
  ack_delta: int
  marker: int


def parse_priorities(text: str) -> tuple[int, ...]:
  values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated priority values")
  for value in values:
    if not 0 <= value <= 15:
      raise argparse.ArgumentTypeError("priorities must be in [0, 15]")
  return values


def choose_case(cores: list[Core], *, noc: int, row: int | None, interferers: int) -> VictimCase:
  candidates = []
  for y, xs in aggregate.rows_by_y(cores).items():
    if row is not None and y != row:
      continue
    ordered = xs if noc == 0 else list(reversed(xs))
    for split in range(1, len(ordered)):
      upstream = ordered[:split]
      downstream = ordered[split:]
      if len(upstream) < interferers + 1 or len(downstream) < interferers + 1:
        continue
      victim = aggregate.Pair((upstream[0], y), (downstream[-1], y))
      bg_sources = upstream[-interferers:]
      bg_targets = downstream[:interferers]
      pairs = [aggregate.Pair((src, y), (dst, y)) for src, dst in zip(bg_sources, bg_targets)]
      if victim.source in [pair.source for pair in pairs] or victim.target in [pair.target for pair in pairs]:
        continue
      cut = ((ordered[split - 1], y), (ordered[split], y))
      victim_distance = abs(victim.target[0] - victim.source[0])
      bg_distances = [abs(pair.target[0] - pair.source[0]) for pair in pairs]
      bg_spread = max(bg_distances) - min(bg_distances) if bg_distances else 0
      # Prefer a central-ish cut with a long victim path and balanced nearby interferers.
      edge_slack = min(len(upstream), len(downstream))
      candidates.append((-edge_slack, bg_spread, -victim_distance, y, split, cut, victim, pairs))
  if not candidates:
    raise ValueError(f"could not find a row cut with {interferers} disjoint interferers")
  _slack, _spread, _distance, y, _split, cut, victim, pairs = min(candidates)
  return VictimCase(row=y, cut=cut, victim=victim, interferers=pairs)


def result_metrics(*, mode: str, victim_priority: int, background_priority: int | None,
                   repeat: int, senders: list[order.Result], receivers: list[order.Result],
                   packets: int) -> Trial:
  victim_sender = senders[0]
  victim_receiver = receivers[0]
  start0 = min(sender.start for sender in senders)
  start1 = max(sender.start for sender in senders)
  commands = packets + 1
  ready_total = victim_sender.words[14] | (victim_sender.words[15] << 32)
  return Trial(
    mode=mode,
    victim_priority=victim_priority,
    background_priority=background_priority,
    repeat=repeat,
    victim_sender_cycles=victim_sender.end - victim_sender.start,
    victim_receiver_cycles=victim_receiver.observed - victim_sender.start,
    victim_done_delta=victim_sender.end - start0,
    victim_seen_delta=victim_receiver.observed - start0,
    start_skew=start1 - start0,
    ready_avg=ready_total / commands,
    ready_max=victim_sender.words[16],
    ack_delta=(victim_sender.words[13] - victim_sender.words[12]) & 0xFFFFFFFF,
    marker=victim_receiver.words[17],
  )


def run_trial(device: Device, *, case: VictimCase, noc: int, victim_priority: int,
              background_priority: int | None, interferers: int, packets: int,
              packet_bytes: int, static_vc: int | None, posted: bool,
              repeat: int) -> Trial:
  pairs = [case.victim]
  priorities = [victim_priority]
  if background_priority is not None:
    pairs.extend(case.interferers[:interferers])
    priorities.extend([background_priority] * interferers)
  trids = tuple(range(len(pairs)))
  order.seed(device, pairs, trids=trids)
  device.run(order.ArbPriorityProgram(
    pairs=pairs, noc=noc, priorities=tuple(priorities), trids=trids,
    packets=packets, packet_bytes=packet_bytes, static_vc=static_vc, posted=posted,
  ))
  senders = [order.read_result(device, pair.source, order.ROLE_SENDER) for pair in pairs]
  receivers = [order.read_result(device, pair.target, order.ROLE_RECEIVER) for pair in pairs]
  return result_metrics(
    mode="contended" if background_priority is not None else "baseline",
    victim_priority=victim_priority,
    background_priority=background_priority,
    repeat=repeat,
    senders=senders,
    receivers=receivers,
    packets=packets,
  )


def mean(values: list[int | float]) -> float:
  return statistics.fmean(values) if values else 0.0


def summarize_trials(trials: list[Trial], *, total_bytes: int) -> list[str]:
  rows = [
    "| mode | victim priority | background priority | repeats | victim sender cyc | victim receiver cyc | victim B/cyc | done delta | seen delta | start skew | ready avg | ready max | ack delta | marker |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  groups: dict[tuple[str, int, int | None], list[Trial]] = {}
  for trial in trials:
    groups.setdefault((trial.mode, trial.victim_priority, trial.background_priority), []).append(trial)
  for key in sorted(groups, key=lambda item: (item[1], item[0], -1 if item[2] is None else item[2])):
    mode, victim_priority, background_priority = key
    group = groups[key]
    sender_cycles = mean([trial.victim_sender_cycles for trial in group])
    receiver_cycles = mean([trial.victim_receiver_cycles for trial in group])
    bpc = total_bytes / sender_cycles if sender_cycles > 0 else 0.0
    rows.append(
      f"| {mode} | {victim_priority} | {'' if background_priority is None else background_priority} | {len(group)} | "
      f"{sender_cycles:.1f} | {receiver_cycles:.1f} | {bpc:.3f} | "
      f"{mean([trial.victim_done_delta for trial in group]):.1f} | "
      f"{mean([trial.victim_seen_delta for trial in group]):.1f} | "
      f"{mean([trial.start_skew for trial in group]):.1f} | "
      f"{mean([trial.ready_avg for trial in group]):.2f} | "
      f"{max(trial.ready_max for trial in group)} | "
      f"{mean([trial.ack_delta for trial in group]):.1f} | "
      f"0x{group[-1].marker:08x} |"
    )
  return rows


def slowdown_rows(trials: list[Trial]) -> list[str]:
  rows = [
    "| victim priority | background priority | sender slowdown | receiver slowdown | sender delta cyc | receiver delta cyc |",
    "|---:|---:|---:|---:|---:|---:|",
  ]
  groups: dict[tuple[str, int, int | None], list[Trial]] = {}
  for trial in trials:
    groups.setdefault((trial.mode, trial.victim_priority, trial.background_priority), []).append(trial)
  for victim_priority in sorted({trial.victim_priority for trial in trials}):
    baseline = groups.get(("baseline", victim_priority, None))
    if not baseline:
      continue
    base_sender = mean([trial.victim_sender_cycles for trial in baseline])
    base_receiver = mean([trial.victim_receiver_cycles for trial in baseline])
    for key in sorted(k for k in groups if k[0] == "contended" and k[1] == victim_priority):
      _mode, _vp, background_priority = key
      group = groups[key]
      cont_sender = mean([trial.victim_sender_cycles for trial in group])
      cont_receiver = mean([trial.victim_receiver_cycles for trial in group])
      rows.append(
        f"| {victim_priority} | {background_priority} | "
        f"{cont_sender / base_sender:.3f} | {cont_receiver / base_receiver:.3f} | "
        f"{cont_sender - base_sender:.1f} | {cont_receiver - base_receiver:.1f} |"
      )
  return rows


def main():
  parser = argparse.ArgumentParser(description="Victim/interferer NoC arbitration priority probe on one shared row cut.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--row", type=int, default=None)
  parser.add_argument("--interferers", type=int, default=3)
  parser.add_argument("--victim-priorities", type=parse_priorities, default=parse_priorities("1,2,3,4,5,6,7,8,9,10,11,12,13,14,15"))
  parser.add_argument("--background-priorities", type=parse_priorities, default=parse_priorities("8"))
  parser.add_argument("--packets", type=int, default=128)
  parser.add_argument("--bytes", type=int, default=NOC.MAX_BURST_SIZE)
  parser.add_argument("--static-vc", type=int, default=1, help="pin all streams to this static VC")
  parser.add_argument("--dynamic-vc", action="store_true", help="clear CMD_VC_STATIC and let the NoC allocate VCs")
  parser.add_argument("--posted", action="store_true")
  parser.add_argument("--repeat", type=int, default=1)
  parser.add_argument("--no-baseline", action="store_true")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-vc-command-flags.md"))
  args = parser.parse_args()

  if args.interferers <= 0:
    raise ValueError("--interferers must be positive")
  if args.packets <= 0:
    raise ValueError("--packets must be positive")
  if args.bytes <= 0 or args.bytes > NOC.MAX_BURST_SIZE or args.bytes % 4:
    raise ValueError(f"--bytes must be a 4-byte multiple in [4, {NOC.MAX_BURST_SIZE}]")
  if args.repeat <= 0:
    raise ValueError("--repeat must be positive")
  static_vc = None if args.dynamic_vc else args.static_vc
  if static_vc is not None and not 0 <= static_vc <= 5:
    raise ValueError("--static-vc must be in [0, 5]")

  trials: list[Trial] = []
  with harness.open_device() as device:
    case = choose_case(aggregate.usable_program_cores(device), noc=args.noc, row=args.row, interferers=args.interferers)
    for repeat in range(args.repeat):
      for victim_priority in args.victim_priorities:
        if not args.no_baseline:
          trials.append(run_trial(
            device, case=case, noc=args.noc, victim_priority=victim_priority,
            background_priority=None, interferers=args.interferers, packets=args.packets,
            packet_bytes=args.bytes, static_vc=static_vc, posted=args.posted, repeat=repeat,
          ))
        for background_priority in args.background_priorities:
          trials.append(run_trial(
            device, case=case, noc=args.noc, victim_priority=victim_priority,
            background_priority=background_priority, interferers=args.interferers, packets=args.packets,
            packet_bytes=args.bytes, static_vc=static_vc, posted=args.posted, repeat=repeat,
          ))

  total_bytes = args.bytes * args.packets
  summary = [
    f"NoC: `{args.noc}`; row: `{case.row}`; cut: `{case.cut[0][0]},{case.cut[0][1]}->{case.cut[1][0]},{case.cut[1][1]}`",
    f"Victim: `{case.victim.source[0]},{case.victim.source[1]}->{case.victim.target[0]},{case.victim.target[1]}`",
    "Interferers: `" + " ".join(f"{p.source[0]},{p.source[1]}->{p.target[0]},{p.target[1]}" for p in case.interferers[:args.interferers]) + "`",
    f"Static VC: `{static_vc}`; dynamic VC: `{static_vc is None}`; posted: `{args.posted}`",
    f"Packets/stream: `{args.packets}`; bytes/packet: `{args.bytes}`; victim priorities: `{','.join(str(p) for p in args.victim_priorities)}`; background priorities: `{','.join(str(p) for p in args.background_priorities)}`",
  ]
  detail_table = "\n".join(summarize_trials(trials, total_bytes=total_bytes))
  slowdown_table = "\n".join(slowdown_rows(trials))
  print("\n".join(f"- {item}" for item in summary))
  print()
  print(slowdown_table)
  print()
  print(detail_table)

  if not args.no_report:
    harness.append_report(
      args.report,
      "NoC arbitration priority victim/interferer",
      summary + [
        "This bench isolates one victim stream and same-cut background streams. The intended clean setting is static VC enabled so the flows share a known VC.",
        "`0` remains supported by the CLI, but tt-metal documents it as round-robin/no-priority rather than a numeric priority below `1`.",
      ],
      slowdown_table + "\n\n" + detail_table,
    )
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
