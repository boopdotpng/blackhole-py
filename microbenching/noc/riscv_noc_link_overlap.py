#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_aggregate as aggregate  # noqa: E402
from device import Device  # noqa: E402
from microbenching.models.noc_scheduler import (  # noqa: E402
  Calibration,
  Endpoint,
  Transaction,
  _physical_path_links,
  schedule,
)
from ttk.addrs import Core  # noqa: E402
from ttk.blackhole_coords import (  # noqa: E402
  TensixCoordinateMap,
  tensix_coordinate_map,
  translated_tensix_to_raw_noc0,
)
from ttk.noc import NOC  # noqa: E402


ENABLED_TENSIX_COL_TAG = 34


@dataclass(frozen=True)
class MappedCore:
  translated: Core
  raw0: Core


@dataclass(frozen=True)
class Case:
  name: str
  pairs: list[aggregate.Pair]
  raw_pairs: list[tuple[Core, Core]]
  shared_link: tuple[Core, Core] | None = None


def read_tensix_coordinate_map(device: Device) -> TensixCoordinateMap:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  return tensix_coordinate_map(enabled)


def usable_mapped_cores(device: Device, cmap: TensixCoordinateMap) -> list[MappedCore]:
  reserved = {
    getattr(device.board_info, "dispatch_core", None),
    getattr(device.board_info, "prefetch_core", None),
  }
  out = []
  for core in sorted(set(device.cores) - {core for core in reserved if core is not None}):
    try:
      raw0 = translated_tensix_to_raw_noc0(core, cmap)
    except ValueError:
      continue
    out.append(MappedCore(core, raw0))
  return out


def _fmt_core(core: Core) -> str:
  return f"{core[0]},{core[1]}"


def _fmt_link(link: tuple[Core, Core] | None) -> str:
  if link is None:
    return "-"
  return f"{_fmt_core(link[0])}->{_fmt_core(link[1])}"


def _link_set(raw_src: Core, raw_dst: Core, *, noc: int, route_order: str) -> set[tuple[Core, Core]]:
  return set(_physical_path_links(raw_src, raw_dst, noc, route_order=route_order))


def _candidate_pairs(mapped: list[MappedCore], *, noc: int, route_order: str) -> list[tuple[aggregate.Pair, Core, Core, set[tuple[Core, Core]]]]:
  candidates = []
  for src in mapped:
    for dst in mapped:
      if src.translated == dst.translated:
        continue
      links = _link_set(src.raw0, dst.raw0, noc=noc, route_order=route_order)
      if not links:
        continue
      candidates.append((aggregate.Pair(src.translated, dst.translated), src.raw0, dst.raw0, links))
  return candidates


def select_shared_link_case(mapped: list[MappedCore], *, noc: int, route_order: str, count: int) -> Case:
  by_link: dict[tuple[Core, Core], list[tuple[aggregate.Pair, Core, Core, set[tuple[Core, Core]]]]] = {}
  for item in _candidate_pairs(mapped, noc=noc, route_order=route_order):
    pair, raw_src, raw_dst, links = item
    # Same-row streams make the path shape easy to reason about and avoid
    # fitting turn behavior at the same time as link contention.
    if raw_src[1] != raw_dst[1]:
      continue
    for link in links:
      by_link.setdefault(link, []).append(item)

  best_link = None
  best_pick = []
  best_score = None
  for link, items in by_link.items():
    used: set[Core] = set()
    pick = []
    for item in sorted(items, key=lambda it: (len(it[3]), it[1], it[2])):
      pair, raw_src, raw_dst, _links = item
      if pair.source in used or pair.target in used:
        continue
      used.add(pair.source)
      used.add(pair.target)
      pick.append(item)
      if len(pick) == count:
        break
    if len(pick) < count:
      continue
    total_links = len(set().union(*(item[3] for item in pick)))
    score = (-len(pick), total_links, link)
    if best_score is None or score < best_score:
      best_score = score
      best_link = link
      best_pick = pick

  if len(best_pick) < count or best_link is None:
    raise ValueError(f"could not find {count} unique-endpoint streams sharing one directed link")

  return Case(
    name="shared-link",
    pairs=[item[0] for item in best_pick],
    raw_pairs=[(item[1], item[2]) for item in best_pick],
    shared_link=best_link,
  )


def select_parallel_case(mapped: list[MappedCore], shared: Case, *, noc: int, route_order: str, count: int) -> Case:
  raw_src0, raw_dst0 = shared.raw_pairs[0]
  rows = sorted({core.raw0[1] for core in mapped})
  by_raw = {core.raw0: core.translated for core in mapped}
  used_links: set[tuple[Core, Core]] = set()
  pairs: list[aggregate.Pair] = []
  raw_pairs: list[tuple[Core, Core]] = []
  for y in rows:
    raw_src = (raw_src0[0], y)
    raw_dst = (raw_dst0[0], y)
    if raw_src not in by_raw or raw_dst not in by_raw:
      continue
    links = _link_set(raw_src, raw_dst, noc=noc, route_order=route_order)
    if used_links & links:
      continue
    used_links |= links
    pairs.append(aggregate.Pair(by_raw[raw_src], by_raw[raw_dst]))
    raw_pairs.append((raw_src, raw_dst))
    if len(pairs) == count:
      break
  if len(pairs) < count:
    raise ValueError(f"could not find {count} parallel non-overlapping streams matching {shared.raw_pairs[0]}")
  return Case(name="parallel", pairs=pairs, raw_pairs=raw_pairs)


def predict(case: Case, *, noc: int, route_order: str, stream_bytes: int, cal: Calibration):
  txns = []
  for i, (raw_src, raw_dst) in enumerate(case.raw_pairs):
    txns.append(Transaction(
      name=f"{case.name}{i}",
      op="write",
      noc=noc,
      initiator=Endpoint("l1", raw_src, label=f"{case.name}.src{i}@{_fmt_core(raw_src)}"),
      target=Endpoint("l1", raw_dst, label=f"{case.name}.dst{i}@{_fmt_core(raw_dst)}"),
      bytes=stream_bytes,
      packet_bytes=NOC.MAX_BURST_SIZE,
      route_order=route_order,
    ))
  est = schedule(txns, cal)
  total_bytes = len(txns) * stream_bytes
  bpc = total_bytes / est.cycles if est.cycles > 0 else 0.0
  return est.cycles, bpc, est.resource_hotspots(3)


def summarize_case(case: Case, *, noc: int, route_order: str, stream_bytes: int,
                   senders: list[aggregate.CoreResult], receivers: list[aggregate.CoreResult],
                   cal: Calibration) -> str:
  starts = [result.start for result in senders]
  acks = [result.end for result in senders]
  observed = [result.start for result in receivers]
  total_bytes = len(case.pairs) * stream_bytes
  sender_window = max(acks) - min(starts)
  observed_window = max(observed) - min(starts)
  sender_bpc = total_bytes / sender_window if sender_window > 0 else 0.0
  observed_bpc = total_bytes / observed_window if observed_window > 0 else 0.0
  bad_sentinels = sum(result.words[11] != aggregate.observe.expected_sentinel(stream_bytes) for result in receivers)
  bad_acks = sum(((result.counter_after - result.counter_before) & 0xFFFFFFFF) != stream_bytes // NOC.MAX_BURST_SIZE for result in senders)
  pred_cycles, pred_bpc, hotspots = predict(case, noc=noc, route_order=route_order, stream_bytes=stream_bytes, cal=cal)
  hot = "; ".join(f"{name}={cycles:.0f}" for name, cycles in hotspots)
  raw_pairs = " ".join(f"{_fmt_core(src)}->{_fmt_core(dst)}" for src, dst in case.raw_pairs)
  return (
    f"| {case.name} | {noc} | {route_order} | {len(case.pairs)} | `{_fmt_link(case.shared_link)}` | "
    f"`{raw_pairs}` | {total_bytes / (1024 * 1024):.1f} | "
    f"{sender_window} | {sender_bpc:.3f} | {observed_window} | {observed_bpc:.3f} | "
    f"{pred_cycles:.1f} | {pred_bpc:.3f} | `{hot}` | {bad_acks} | {bad_sentinels} |"
  )


def run_case(device: Device, case: Case, *, noc: int, stream_bytes: int):
  return aggregate.run_once(device, case.pairs, noc=noc, stream_bytes=stream_bytes)


def main():
  parser = argparse.ArgumentParser(description="Calibrate NoC directed-link overlap using harvested-aware L1 write streams.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--route-order", choices=("xy", "yx"), default="xy")
  parser.add_argument("--counts", type=aggregate.parse_counts, default=aggregate.parse_counts("1,2,4,6"))
  parser.add_argument("--bytes", type=int, default=1024 * 1024, help="payload bytes per sender; multiple of 16 KiB")
  parser.add_argument("--link-bpc", type=float, default=Calibration().link_bpc, help="scheduler link bandwidth calibration")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-link-overlap.md"))
  args = parser.parse_args()
  if args.bytes <= 0 or args.bytes % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes must be a positive multiple of 16 KiB")
  if args.bytes > aggregate.observe.RESULT_BASE - aggregate.observe.STREAM_BASE:
    raise ValueError(f"--bytes must fit below result range; max is {aggregate.observe.RESULT_BASE - aggregate.observe.STREAM_BASE}")

  cal = Calibration(link_bpc=args.link_bpc)
  lines = [
    "| case | noc | route | streams | shared physical link | raw physical streams | total MiB | sender cyc | sender B/cyc | observed cyc | observed B/cyc | model cyc | model B/cyc | model hotspots | bad ack rows | bad sentinel rows |",
    "|---|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|",
  ]
  metadata: list[str] = []
  with harness.open_device() as device:
    cmap = read_tensix_coordinate_map(device)
    mapped = usable_mapped_cores(device, cmap)
    metadata.extend([
      f"ENABLED_TENSIX_COL: `0x{cmap.enabled_tensix_col:08x}`",
      f"Harvested raw Tensix columns: `{list(cmap.harvested_raw_x)}`",
      f"Live raw Tensix columns: `{list(cmap.live_raw_x)}`",
      f"Scheduler link_bpc used for prediction: `{args.link_bpc}`",
    ])
    for count in args.counts:
      shared = select_shared_link_case(mapped, noc=args.noc, route_order=args.route_order, count=count)
      parallel = select_parallel_case(mapped, shared, noc=args.noc, route_order=args.route_order, count=count)
      for case in (parallel, shared):
        senders, receivers = run_case(device, case, noc=args.noc, stream_bytes=args.bytes)
        lines.append(summarize_case(
          case,
          noc=args.noc,
          route_order=args.route_order,
          stream_bytes=args.bytes,
          senders=senders,
          receivers=receivers,
          cal=cal,
        ))

  table = "\n".join(lines)
  print("\n".join(f"- {line}" for line in metadata))
  print()
  print(table)
  if not args.no_report:
    harness.append_report(args.report, None, [
      *metadata,
      f"NoC: `{args.noc}`",
      f"Route order assumption: `{args.route_order}`",
      f"Bytes per sender: `{args.bytes}`",
    ], table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
