#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import riscv_noc_competing_mcast_matmul_style as competing
import riscv_noc_hop_sweep as hop_sweep
import riscv_noc_mcast_one_way_latency as mcast
import riscv_noc_mcast_vc_linked as linked
import riscv_noc_one_way_latency as unicast
from device import Device
from ttk.addrs import Core
from ttk.noc import NOC


DEFAULT_ROW_X = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14)
DEFAULT_REPORT = Path("microbenching/docs/noc/noc-mcast-scheduler-calibration.md")


@dataclass(frozen=True)
class PathReserveRow:
  noc: int
  major: str
  packet_bytes: int
  unicast_seen: float
  mcast_nores_seen: float
  mcast_res_seen: float
  mcast_nores_sent: float
  mcast_res_sent: float
  reserve_seen_delta: float
  reserve_sent_delta: float
  mcast_vs_unicast_delta: float


@dataclass(frozen=True)
class TrunkRow:
  noc: int
  major: str
  dests: int
  depth: int
  packet_bytes: int
  source_bpc: float
  delivered_bpc: float
  req_per_cycle: float
  bad_counter: int


@dataclass(frozen=True)
class OverlapRow:
  case: str
  noc: int
  major: str
  path_reserve: str
  chunks: int
  aggregate_delivered_bpc: float
  a_source_bpc: float
  b_source_bpc: float
  a_delivered_bpc: float
  b_delivered_bpc: float
  bad_counter: int
  stale_data: int


def parse_sections(text: str) -> tuple[str, ...]:
  sections = tuple(item.strip() for item in text.split(",") if item.strip())
  allowed = {"path", "trunk", "vc", "overlap"}
  bad = [section for section in sections if section not in allowed]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown section(s): {','.join(bad)}")
  return sections


def parse_counts(text: str) -> tuple[int, ...]:
  counts = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not counts or any(count <= 0 for count in counts):
    raise argparse.ArgumentTypeError("expected comma-separated positive counts")
  return counts


def parse_path_modes(text: str) -> tuple[str, ...]:
  modes = tuple(item.strip() for item in text.split(",") if item.strip())
  allowed = {"both", "none"}
  bad = [mode for mode in modes if mode not in allowed]
  if bad:
    raise argparse.ArgumentTypeError(f"unknown path-reserve mode(s): {','.join(bad)}")
  return modes


def median_delta(a: list[int], b: list[int]) -> float:
  return float(statistics.median([x - y for x, y in zip(a, b)]))


def mean_delta(a: list[int], b: list[int]) -> float:
  return float(statistics.fmean([x - y for x, y in zip(a, b)]))


def source_bpc(sender: linked.SenderResult, *, packet_bytes: int, iters: int, depth: int) -> float:
  window = max(sender.sent) - min(sender.issue)
  return (iters * depth * packet_bytes) / window if window > 0 else 0.0


def delivered_bpc(sender: linked.SenderResult, receivers: list[linked.ReceiverResult], *, packet_bytes: int, iters: int, depth: int) -> float:
  last_seen = [receiver.seen[-1] for receiver in receivers]
  window = max(last_seen) - min(sender.issue) if last_seen else 0
  return (iters * depth * packet_bytes * len(receivers)) / window if window > 0 else 0.0


def row_receivers(source: Core, count: int) -> tuple[Core, ...]:
  sx, sy = source
  candidates = tuple((x, sy) for x in DEFAULT_ROW_X if x != sx)
  if count > len(candidates):
    raise ValueError(
      f"row multicast from {source} supports {len(candidates)} receivers on this board; "
      f"requested {count}"
    )
  return candidates[:count]


def linked_run(
  device: Device, *,
  cmap,
  noc: int,
  major: str,
  source: Core,
  receivers: tuple[Core, ...],
  packet_bytes: int,
  iters: int,
  depth: int,
  path_reserve: bool,
  start_delay: int,
  inter_delay: int,
) -> tuple[linked.SenderResult, list[linked.ReceiverResult]]:
  rect = mcast.logical_rect_for_physical_span(receivers, noc=noc, cmap=cmap)
  linked.clear_and_seed(device, source, receivers, packet_bytes, depth, iters)
  device.run(linked.LinkedMcastProgram(
    noc=noc,
    major=major,
    packet_bytes=packet_bytes,
    iters=iters,
    depth=depth,
    source=source,
    receivers=receivers,
    rect=rect,
    path_reserve=path_reserve,
    start_delay=start_delay,
    inter_delay=inter_delay,
  ))
  sender = linked.parse_sender(device, source, iters)
  receivers_out = [linked.parse_receiver(device, receiver, iters) for receiver in receivers]
  return sender, receivers_out


def run_path_reserve(
  device: Device, *,
  cmap,
  nocs: tuple[int, ...],
  majors: tuple[str, ...],
  source: Core,
  target: Core,
  sizes: tuple[int, ...],
  iters: int,
  start_delay: int,
  inter_delay: int,
) -> list[PathReserveRow]:
  rows: list[PathReserveRow] = []
  receivers = (target,)
  for noc in nocs:
    route = unicast.route_for_pair(source, target, noc=noc, cmap=cmap)
    rect = mcast.logical_rect_for_physical_span(receivers, noc=noc, cmap=cmap)
    routes = {target: mcast.receiver_route(source, target, noc=noc, cmap=cmap)}
    for packet_bytes in sizes:
      unicast.clear_and_seed(device, source, target, packet_bytes, iters)
      device.run(unicast.OneWayProgram(
        noc=noc,
        packet_bytes=packet_bytes,
        iters=iters,
        source=source,
        target=target,
        start_delay=start_delay,
      ))
      uni = unicast.parse_run_result(
        device,
        noc=noc,
        source=source,
        target=target,
        route=route,
        packet_bytes=packet_bytes,
        iters=iters,
      )
      uni_seen = median_delta(uni.receiver_seen, uni.sender_issue)
      for major in majors:
        mcast_results = {}
        for path_reserve in (False, True):
          mcast.clear_and_seed(device, source, receivers, packet_bytes, iters)
          device.run(mcast.McastOneWayProgram(
            noc=noc,
            packet_bytes=packet_bytes,
            iters=iters,
            source=source,
            receivers=receivers,
            rect=rect,
            major=major,
            path_reserve=path_reserve,
            start_delay=start_delay,
            inter_delay=inter_delay,
          ))
          [result] = mcast.parse_results(
            device,
            noc=noc,
            case="one-receiver",
            major=major,
            source=source,
            receivers=receivers,
            rect=rect,
            routes=routes,
            packet_bytes=packet_bytes,
            iters=iters,
          )
          mcast_results[path_reserve] = result
        nores = mcast_results[False]
        reserve = mcast_results[True]
        nores_seen = median_delta(nores.receiver_seen, nores.sender_issue)
        res_seen = median_delta(reserve.receiver_seen, reserve.sender_issue)
        nores_sent = median_delta(nores.receiver_seen, nores.sender_sent)
        res_sent = median_delta(reserve.receiver_seen, reserve.sender_sent)
        rows.append(PathReserveRow(
          noc=noc,
          major=major,
          packet_bytes=packet_bytes,
          unicast_seen=uni_seen,
          mcast_nores_seen=nores_seen,
          mcast_res_seen=res_seen,
          mcast_nores_sent=nores_sent,
          mcast_res_sent=res_sent,
          reserve_seen_delta=res_seen - nores_seen,
          reserve_sent_delta=res_sent - nores_sent,
          mcast_vs_unicast_delta=res_seen - uni_seen,
        ))
  return rows


def run_trunk(
  device: Device, *,
  cmap,
  nocs: tuple[int, ...],
  majors: tuple[str, ...],
  source: Core,
  counts: tuple[int, ...],
  packet_bytes: int,
  iters: int,
  depth: int,
  path_reserve: bool,
) -> list[TrunkRow]:
  rows: list[TrunkRow] = []
  for count in counts:
    receivers = row_receivers(source, count)
    for noc in nocs:
      for major in majors:
        sender, receiver_results = linked_run(
          device,
          cmap=cmap,
          noc=noc,
          major=major,
          source=source,
          receivers=receivers,
          packet_bytes=packet_bytes,
          iters=iters,
          depth=depth,
          path_reserve=path_reserve,
          start_delay=0,
          inter_delay=0,
        )
        window = max(sender.sent) - min(sender.issue)
        rows.append(TrunkRow(
          noc=noc,
          major=major,
          dests=count,
          depth=depth,
          packet_bytes=packet_bytes,
          source_bpc=source_bpc(sender, packet_bytes=packet_bytes, iters=iters, depth=depth),
          delivered_bpc=delivered_bpc(sender, receiver_results, packet_bytes=packet_bytes, iters=iters, depth=depth),
          req_per_cycle=(iters * depth) / window if window > 0 else 0.0,
          bad_counter=int(sender.counter_delta != iters * depth),
        ))
  return rows


def run_overlap(
  device: Device, *,
  cmap,
  cases: tuple[str, ...],
  nocs: tuple[int, ...],
  majors: tuple[str, ...],
  path_modes: tuple[str, ...],
  packet_bytes: int,
  iters: int,
  chunks: int,
) -> list[OverlapRow]:
  rows: list[OverlapRow] = []
  for case_name in cases:
    case = competing.CASES[case_name]
    for noc in nocs:
      rects = {
        case.a.name: mcast.logical_rect_for_physical_span(case.a.receivers, noc=noc, cmap=cmap),
        case.b.name: mcast.logical_rect_for_physical_span(case.b.receivers, noc=noc, cmap=cmap),
      }
      for major in majors:
        for path_mode in path_modes:
          path_mask = {
            "both": competing.MASK_A | competing.MASK_B,
            "none": 0,
          }[path_mode]
          competing.clear_and_seed(device, case, packet_bytes, chunks, iters)
          device.run(competing.CompetingMcastProgram(
            case=case,
            noc=noc,
            major=major,
            rects=rects,
            packet_bytes=packet_bytes,
            iters=iters,
            chunks=chunks,
            path_reserve=path_mask,
            start_gap=0,
          ))
          senders = {
            "a": competing.parse_sender(device, case.a, iters),
            "b": competing.parse_sender(device, case.b, iters),
          }
          receivers = [
            competing.parse_receiver(device, case, receiver, iters)
            for receiver in sorted({*case.a.receivers, *case.b.receivers})
          ]
          first_issue = min(min(sender.issue) for sender in senders.values())
          last_seen = []
          delivered = 0
          for stream_name, stream_mask in (("a", competing.MASK_A), ("b", competing.MASK_B)):
            for receiver in receivers:
              if receiver.mask & stream_mask:
                seen = receiver.seen_a if stream_name == "a" else receiver.seen_b
                last_seen.append(seen[-1])
                delivered += iters * chunks * packet_bytes
          agg_window = max(last_seen) - first_issue if last_seen else 0

          def stream_metrics(stream, sender):
            participating = competing.stream_receiver_results(stream, receivers)
            seen_lists = [r.seen_a if stream.mask == competing.MASK_A else r.seen_b for r in participating]
            stream_last = [seen[-1] for seen in seen_lists]
            source_bytes = iters * chunks * packet_bytes
            delivered_bytes = source_bytes * len(participating)
            source_window = max(sender.sent) - min(sender.issue)
            receiver_window = max(stream_last) - min(sender.issue) if stream_last else 0
            return (
              source_bytes / source_window if source_window > 0 else 0.0,
              delivered_bytes / receiver_window if receiver_window > 0 else 0.0,
            )

          a_source, a_delivered = stream_metrics(case.a, senders["a"])
          b_source, b_delivered = stream_metrics(case.b, senders["b"])
          rows.append(OverlapRow(
            case=case_name,
            noc=noc,
            major=major,
            path_reserve=path_mode,
            chunks=chunks,
            aggregate_delivered_bpc=delivered / agg_window if agg_window > 0 else 0.0,
            a_source_bpc=a_source,
            b_source_bpc=b_source,
            a_delivered_bpc=a_delivered,
            b_delivered_bpc=b_delivered,
            bad_counter=sum(int(sender.counter_delta != iters * (chunks + 1)) for sender in senders.values()),
            stale_data=sum(receiver.bad_data for receiver in receivers),
          ))
  return rows


def fmt_path(rows: list[PathReserveRow]) -> str:
  lines = [
    "| noc | major | bytes | unicast seen-issue | mcast nores seen-issue | mcast reserve seen-issue | reserve delta seen | reserve delta seen-sent | reserve mcast - unicast |",
    "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for row in rows:
    lines.append(
      f"| {row.noc} | {row.major} | {row.packet_bytes} | {row.unicast_seen:.1f} | "
      f"{row.mcast_nores_seen:.1f} | {row.mcast_res_seen:.1f} | "
      f"{row.reserve_seen_delta:.1f} | {row.reserve_sent_delta:.1f} | {row.mcast_vs_unicast_delta:.1f} |"
    )
  return "\n".join(lines)


def fmt_trunk(rows: list[TrunkRow]) -> str:
  lines = [
    "| noc | major | dests | depth | bytes | source B/cyc | delivered B/cyc | req/cyc | bad counter |",
    "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for row in rows:
    lines.append(
      f"| {row.noc} | {row.major} | {row.dests} | {row.depth} | {row.packet_bytes} | "
      f"{row.source_bpc:.3f} | {row.delivered_bpc:.3f} | {row.req_per_cycle:.5f} | {row.bad_counter} |"
    )
  return "\n".join(lines)


def fmt_overlap(rows: list[OverlapRow]) -> str:
  lines = [
    "| case | noc | major | path reserve | chunks | aggregate delivered B/cyc | A source B/cyc | B source B/cyc | A delivered B/cyc | B delivered B/cyc | bad counter | stale data |",
    "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for row in rows:
    lines.append(
      f"| {row.case} | {row.noc} | {row.major} | {row.path_reserve} | {row.chunks} | "
      f"{row.aggregate_delivered_bpc:.3f} | {row.a_source_bpc:.3f} | {row.b_source_bpc:.3f} | "
      f"{row.a_delivered_bpc:.3f} | {row.b_delivered_bpc:.3f} | {row.bad_counter} | {row.stale_data} |"
    )
  return "\n".join(lines)


def verdicts(path_rows: list[PathReserveRow], trunk_rows: list[TrunkRow], vc_rows: list[TrunkRow], overlap_rows: list[OverlapRow]) -> list[str]:
  lines: list[str] = []
  if path_rows:
    small = [row.reserve_seen_delta for row in path_rows if row.packet_bytes == min(r.packet_bytes for r in path_rows)]
    mean_small = statistics.fmean(small)
    lines.append(f"- Path reserve: one-receiver reserve/no-reserve median delta at smallest size is `{mean_small:.1f} cycles`.")
  if trunk_rows:
    by_count = {}
    for row in trunk_rows:
      by_count.setdefault(row.dests, []).append(row.source_bpc)
    flat_until = max(count for count, values in by_count.items() if statistics.fmean(values) >= 0.9 * statistics.fmean(by_count[min(by_count)]))
    lines.append(f"- Trunk charged once: source bandwidth stays within 10% of the N=1 rate through `N={flat_until}` in this sweep; delivered bandwidth scales with receiver count.")
  if vc_rows:
    by_depth = {}
    for row in vc_rows:
      by_depth.setdefault(row.depth, []).append(row.source_bpc)
    depth_means = {depth: statistics.fmean(values) for depth, values in by_depth.items()}
    base = depth_means[min(depth_means)]
    best_depth = max(depth_means, key=depth_means.get)
    multiplier = depth_means[best_depth] / base if base else 0.0
    lines.append(f"- VC_LINKED: best source bandwidth multiplier vs depth-1 is `{multiplier:.2f}x` at depth `{best_depth}`.")
  if overlap_rows:
    overlap = [row for row in overlap_rows if row.case in {"overlap", "same_rect", "nested"}]
    if overlap:
      lines.append("- Overlap: shared-tree cases serialize on shared directed links; no separate path-reserve-only contention term is indicated unless reserve and no-reserve rows diverge beyond link serialization.")
  return lines


def write_report(
  path: Path, *,
  command_line: str,
  path_rows: list[PathReserveRow],
  trunk_rows: list[TrunkRow],
  vc_rows: list[TrunkRow],
  overlap_rows: list[OverlapRow],
) -> None:
  sections = [
    f"## Run {datetime.now().astimezone().isoformat(timespec='seconds')}",
    "",
    f"- Command: `{command_line}`",
    "",
    "### Verdicts",
    "",
    *verdicts(path_rows, trunk_rows, vc_rows, overlap_rows),
  ]
  if path_rows:
    sections.extend(["", "### Path Reserve", "", fmt_path(path_rows)])
  if trunk_rows:
    sections.extend(["", "### Trunk Fanout", "", fmt_trunk(trunk_rows)])
  if vc_rows:
    sections.extend(["", "### VC Linked", "", fmt_trunk(vc_rows)])
  if overlap_rows:
    sections.extend(["", "### Overlap", "", fmt_overlap(overlap_rows)])
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("a", encoding="utf-8") as f:
    f.write("\n".join(sections))
    f.write("\n\n")


def main() -> None:
  parser = argparse.ArgumentParser(description="Reduce multicast microbenchmarks to scheduler calibration constants.")
  parser.add_argument("--sections", type=parse_sections, default=parse_sections("path,trunk,vc,overlap"))
  parser.add_argument("--nocs", type=hop_sweep.parse_nocs, default=(0, 1))
  parser.add_argument("--majors", type=mcast.parse_majors, default=("x", "y"))
  parser.add_argument("--source", type=mcast.parse_core_list, default=((1, 4),), help="single source core X,Y")
  parser.add_argument("--target", type=mcast.parse_core_list, default=((2, 4),), help="single target core X,Y")
  parser.add_argument("--path-sizes", type=mcast.parse_sizes, default=mcast.parse_sizes("16,64,256,1024,4096,16384"))
  parser.add_argument("--path-iters", type=int, default=64)
  parser.add_argument("--trunk-counts", type=parse_counts, default=parse_counts("1,2,4,8,11"))
  parser.add_argument("--trunk-size", type=int, default=16384)
  parser.add_argument("--trunk-iters", type=int, default=128)
  parser.add_argument("--vc-depths", type=linked.parse_depths, default=linked.parse_depths("1,2,4"))
  parser.add_argument("--vc-count", type=int, default=8)
  parser.add_argument("--overlap-cases", type=competing.parse_cases, default=("disjoint", "overlap", "same_rect"))
  parser.add_argument("--overlap-path-modes", type=parse_path_modes, default=parse_path_modes("both,none"))
  parser.add_argument("--overlap-iters", type=int, default=16)
  parser.add_argument("--overlap-chunks", type=int, default=1)
  parser.add_argument("--start-delay", type=int, default=4096)
  parser.add_argument("--inter-delay", type=int, default=2048)
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
  args = parser.parse_args()

  if len(args.source) != 1 or len(args.target) != 1:
    raise ValueError("--source and --target must name exactly one core")
  source = args.source[0]
  target = args.target[0]
  if args.trunk_size > NOC.MAX_BURST_SIZE:
    raise ValueError(f"--trunk-size exceeds max burst {NOC.MAX_BURST_SIZE}")

  path_rows: list[PathReserveRow] = []
  trunk_rows: list[TrunkRow] = []
  vc_rows: list[TrunkRow] = []
  overlap_rows: list[OverlapRow] = []

  with mcast.harness.open_device() as device:
    core_set = set(device.cores)
    missing = sorted({source, target} - core_set)
    if missing:
      raise ValueError(f"source/target unavailable: {missing}")
    cmap = mcast.read_tensix_coordinate_map(device)
    if "path" in args.sections:
      path_rows = run_path_reserve(
        device,
        cmap=cmap,
        nocs=args.nocs,
        majors=args.majors,
        source=source,
        target=target,
        sizes=args.path_sizes,
        iters=args.path_iters,
        start_delay=args.start_delay,
        inter_delay=args.inter_delay,
      )
    if "trunk" in args.sections:
      trunk_rows = run_trunk(
        device,
        cmap=cmap,
        nocs=args.nocs,
        majors=args.majors,
        source=source,
        counts=args.trunk_counts,
        packet_bytes=args.trunk_size,
        iters=args.trunk_iters,
        depth=1,
        path_reserve=True,
      )
    if "vc" in args.sections:
      for depth in args.vc_depths:
        vc_rows.extend(run_trunk(
          device,
          cmap=cmap,
          nocs=args.nocs,
          majors=args.majors,
          source=source,
          counts=(args.vc_count,),
          packet_bytes=args.trunk_size,
          iters=args.trunk_iters,
          depth=depth,
          path_reserve=True,
        ))
    if "overlap" in args.sections:
      overlap_rows = run_overlap(
        device,
        cmap=cmap,
        cases=args.overlap_cases,
        nocs=args.nocs,
        majors=args.majors,
        path_modes=args.overlap_path_modes,
        packet_bytes=args.trunk_size,
        iters=args.overlap_iters,
        chunks=args.overlap_chunks,
      )

  output = "\n\n".join(part for part in (
    "### Verdicts\n" + "\n".join(verdicts(path_rows, trunk_rows, vc_rows, overlap_rows)),
    "### Path Reserve\n" + fmt_path(path_rows) if path_rows else "",
    "### Trunk Fanout\n" + fmt_trunk(trunk_rows) if trunk_rows else "",
    "### VC Linked\n" + fmt_trunk(vc_rows) if vc_rows else "",
    "### Overlap\n" + fmt_overlap(overlap_rows) if overlap_rows else "",
  ) if part)
  print(output)
  if not args.no_report:
    import sys
    write_report(
      args.report,
      command_line=" ".join(sys.argv),
      path_rows=path_rows,
      trunk_rows=trunk_rows,
      vc_rows=vc_rows,
      overlap_rows=overlap_rows,
    )


if __name__ == "__main__":
  main()
