#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_hop_sweep as hop_sweep  # noqa: E402
import riscv_noc_mcast_one_way_latency as mcast  # noqa: E402
import riscv_noc_mcast_vc_linked as linked  # noqa: E402
from ttk.addrs import Core
from ttk.noc import NOC


ROW_X = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14)


def parse_counts(text: str) -> tuple[int, ...]:
  counts = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive receiver counts")
  return counts


def row_receivers(source: Core, count: int) -> tuple[Core, ...]:
  sx, sy = source
  candidates = [(x, sy) for x in ROW_X if x != sx]
  if count > len(candidates):
    raise ValueError(f"row source {source} supports at most {len(candidates)} receivers, got {count}")
  return tuple(candidates[:count])


def u64_span(values: list[int]) -> int:
  return max(values) - min(values) if values else 0


def mean_cycle_delta(a: list[int], b: list[int]) -> float:
  return statistics.fmean([x - y for x, y in zip(a, b)])


def format_row(*, noc: int, major: str, receivers: tuple[Core, ...], rect: mcast.McastRect,
               packet_bytes: int, iters: int, depth: int, path_reserve: bool,
               sender: linked.SenderResult, receiver_results: list[linked.ReceiverResult]) -> str:
  total_packets = iters * depth
  source_bytes = total_packets * packet_bytes
  delivered_bytes = source_bytes * len(receivers)
  source_window = max(sender.sent) - min(sender.issue)
  receiver_last = [r.seen[-1] for r in receiver_results]
  receiver_window = max(receiver_last) - min(sender.issue)
  source_bpc = source_bytes / source_window if source_window > 0 else 0.0
  delivered_bpc = delivered_bytes / receiver_window if receiver_window > 0 else 0.0
  req_cyc = total_packets / source_window if source_window > 0 else 0.0
  expected_reqs = total_packets
  bad_counter = int(sender.counter_delta != expected_reqs)
  first_seen = [r.seen[0] for r in receiver_results]
  avg_first_seen = mean_cycle_delta(first_seen, [sender.issue[0]] * len(first_seen))
  avg_last_seen = mean_cycle_delta(receiver_last, [sender.issue[0]] * len(receiver_last))
  max_polls = max((r.poll_iters for r in receiver_results), default=0)
  return (
    f"| {noc} | {major} | {int(path_reserve)} | {len(receivers)} | "
    f"`{rect.x0},{rect.y0}->{rect.x1},{rect.y1}` | {packet_bytes} | {iters} | {depth} | "
    f"{source_bpc:.3f} | {delivered_bpc:.3f} | {req_cyc:.5f} | "
    f"{avg_first_seen:.1f} | {avg_last_seen:.1f} | {bad_counter} | {max_polls} |"
  )


def main() -> None:
  parser = argparse.ArgumentParser(description="Blackhole NoC multicast throughput sweep.")
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x", "y"))
  parser.add_argument("--source", type=harness.parse_core, default=(1, 4))
  parser.add_argument("--counts", type=parse_counts, default=parse_counts("1,2,4,8,11"))
  parser.add_argument("--sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("64,256,1024,4096,16384"))
  parser.add_argument("--iters", type=int, default=256)
  parser.add_argument("--depths", type=linked.parse_depths, default=linked.parse_depths("1,4"))
  parser.add_argument("--no-path-reserve", action="store_true")
  args = parser.parse_args()
  if args.iters <= 0:
    raise ValueError("--iters must be positive")

  path_reserve = not args.no_path_reserve
  lines = [
    "| noc | major | reserve | dests | rect | packet B | iters | depth | source B/cyc | delivered B/cyc | req/cyc | avg first seen cyc | avg last seen cyc | bad counter | max recv polls |",
    "|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  with harness.open_device() as device:
    core_set = set(device.cores)
    if args.source not in core_set:
      raise ValueError(f"source {args.source} is not a program core")
    cmap = mcast.read_tensix_coordinate_map(device)
    for count in args.counts:
      receivers = row_receivers(args.source, count)
      missing = sorted(set(receivers) - core_set)
      if missing:
        raise ValueError(f"unavailable receivers for count {count}: {missing}")
      for noc in args.nocs:
        rect = mcast.logical_rect_for_physical_span(receivers, noc=noc, cmap=cmap)
        for major in args.majors:
          for packet_bytes in args.sizes:
            for depth in args.depths:
              if linked.SRC_BASE + depth * linked.SLOT_STRIDE > linked.RESULT_BASE:
                raise ValueError(f"depth {depth} exceeds scratch space before RESULT_BASE")
              if packet_bytes > NOC.MAX_BURST_SIZE:
                raise ValueError(f"packet size {packet_bytes} exceeds max burst")
              linked.clear_and_seed(device, args.source, receivers, packet_bytes, depth, args.iters)
              device.run(linked.LinkedMcastProgram(
                noc=noc,
                major=major,
                packet_bytes=packet_bytes,
                iters=args.iters,
                depth=depth,
                source=args.source,
                receivers=receivers,
                rect=rect,
                path_reserve=path_reserve,
                start_delay=0,
                inter_delay=0,
              ))
              sender = linked.parse_sender(device, args.source, args.iters)
              receiver_results = [linked.parse_receiver(device, receiver, args.iters) for receiver in receivers]
              lines.append(format_row(
                noc=noc,
                major=major,
                receivers=receivers,
                rect=rect,
                packet_bytes=packet_bytes,
                iters=args.iters,
                depth=depth,
                path_reserve=path_reserve,
                sender=sender,
                receiver_results=receiver_results,
              ))
  print("\n".join(lines))


if __name__ == "__main__":
  main()
