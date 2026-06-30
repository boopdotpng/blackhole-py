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
from device import Device  # noqa: E402
from ttk.addrs import Core  # noqa: E402
from ttk.blackhole_coords import (  # noqa: E402
  GRID_H,
  GRID_W,
  TensixCoordinateMap,
  raw_coord_for_noc,
  tensix_coordinate_map,
  translated_tensix_to_raw_noc0,
)
from ttk.noc import NOC  # noqa: E402


ENABLED_TENSIX_COL_TAG = 34


@dataclass(frozen=True)
class Route:
  source: Core
  target: Core
  raw_source: Core
  raw_target: Core
  path: tuple[Core, ...]
  links: tuple[tuple[Core, Core], ...]


@dataclass(frozen=True)
class PairRoute:
  pair: aggregate.Pair
  route: Route


@dataclass(frozen=True)
class Case:
  name: str
  pairs: tuple[aggregate.Pair, ...]
  routes: tuple[Route, ...]
  note: str


def parse_vcs(text: str) -> tuple[int, ...]:
  values = tuple(int(item.strip(), 0) for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError("expected comma-separated VCs")
  for value in values:
    if not 0 <= value <= 5:
      raise argparse.ArgumentTypeError("VCs must be in [0, 5]")
  return values


def _fmt_core(core: Core) -> str:
  return f"{core[0]},{core[1]}"


def _fmt_pair(pair: aggregate.Pair) -> str:
  return f"{_fmt_core(pair.source)}->{_fmt_core(pair.target)}"


def _walk_axis(start: int, stop: int, size: int, step: int):
  cur = start
  while cur != stop:
    cur = (cur + step) % size
    yield cur


def physical_path(src: Core, dst: Core, *, noc: int, route_order: str) -> tuple[Core, ...]:
  if route_order not in ("xy", "yx"):
    raise ValueError("route_order must be xy or yx")
  step = 1 if noc == 0 else -1
  sx, sy = src
  dx, dy = dst
  path = [(sx, sy)]
  x = sx
  y = sy
  if route_order == "xy":
    for x in _walk_axis(sx, dx, GRID_W, step):
      path.append((x, y))
    for y in _walk_axis(sy, dy, GRID_H, step):
      path.append((x, y))
  else:
    for y in _walk_axis(sy, dy, GRID_H, step):
      path.append((x, y))
    for x in _walk_axis(sx, dx, GRID_W, step):
      path.append((x, y))
  return tuple(path)


def read_tensix_coordinate_map(device: Device) -> TensixCoordinateMap:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  return tensix_coordinate_map(enabled)


def route_for_pair(pair: aggregate.Pair, *, noc: int, cmap: TensixCoordinateMap, route_order: str) -> Route:
  raw0_source = translated_tensix_to_raw_noc0(pair.source, cmap)
  raw0_target = translated_tensix_to_raw_noc0(pair.target, cmap)
  raw_source = raw_coord_for_noc(raw0_source, noc)
  raw_target = raw_coord_for_noc(raw0_target, noc)
  path = physical_path(raw_source, raw_target, noc=noc, route_order=route_order)
  return Route(
    source=pair.source,
    target=pair.target,
    raw_source=raw_source,
    raw_target=raw_target,
    path=path,
    links=tuple(zip(path, path[1:])),
  )


def enumerate_pair_routes(cores: list[Core], *, noc: int, cmap: TensixCoordinateMap,
                          route_order: str) -> list[PairRoute]:
  live_raw_nodes = {
    raw_coord_for_noc(translated_tensix_to_raw_noc0(core, cmap), noc)
    for core in cores
  }
  out = []
  for source in cores:
    for target in cores:
      if source == target:
        continue
      pair = aggregate.Pair(source, target)
      route = route_for_pair(pair, noc=noc, cmap=cmap, route_order=route_order)
      if not route.links:
        continue
      if has_wrap(route):
        continue
      if any(node not in live_raw_nodes for node in route.path):
        continue
      out.append(PairRoute(pair, route))
  return out


def disjoint_program_cores(a: PairRoute, b: PairRoute) -> bool:
  return len({a.pair.source, a.pair.target, b.pair.source, b.pair.target}) == 4


def has_wrap(route: Route) -> bool:
  sx, sy = route.raw_source
  tx, ty = route.raw_target
  return (tx < sx and sx != tx) or (ty < sy and sy != ty)


def choose_cross_case(routes: list[PairRoute]) -> Case:
  by_node: dict[Core, list[PairRoute]] = {}
  for route in routes:
    is_x_axis = route.route.raw_source[1] == route.route.raw_target[1]
    is_y_axis = route.route.raw_source[0] == route.route.raw_target[0]
    if is_x_axis == is_y_axis:
      continue
    for node in route.route.path[1:-1]:
      by_node.setdefault(node, []).append(route)

  candidates = []
  for node, node_routes in by_node.items():
    horizontal = [r for r in node_routes if r.route.raw_source[1] == r.route.raw_target[1]]
    vertical = [r for r in node_routes if r.route.raw_source[0] == r.route.raw_target[0]]
    for a in horizontal:
      for b in vertical:
        if a.pair == b.pair or not disjoint_program_cores(a, b):
          continue
        shared_links = set(a.route.links) & set(b.route.links)
        if shared_links:
          continue
        score = (
          max(len(a.route.links), len(b.route.links)),
          len(a.route.links) + len(b.route.links),
          _fmt_core(node),
          _fmt_pair(a.pair),
          _fmt_pair(b.pair),
        )
        candidates.append((score, a, b, node))
  if not candidates:
    raise ValueError("could not find a two-stream crossing case with no shared directed links")
  _score, a, b, node = min(candidates)
  return Case(
    name="cross-router",
    pairs=(a.pair, b.pair),
    routes=(a.route, b.route),
    note=f"paths share router node raw {_fmt_core(node)} but share 0 directed links; all route nodes are live Tensix raw positions",
  )


def choose_shared_link_case(routes: list[PairRoute]) -> Case:
  by_link: dict[tuple[Core, Core], list[PairRoute]] = {}
  for route in routes:
    for link in route.route.links:
      by_link.setdefault(link, []).append(route)

  candidates = []
  for link, link_routes in by_link.items():
    for i, a in enumerate(link_routes):
      for b in link_routes[i + 1:]:
        if a.pair == b.pair or not disjoint_program_cores(a, b):
          continue
        shared_links = set(a.route.links) & set(b.route.links)
        score = (
          -len(shared_links),
          max(len(a.route.links), len(b.route.links)),
          len(a.route.links) + len(b.route.links),
          _fmt_pair(a.pair),
          _fmt_pair(b.pair),
        )
        candidates.append((score, a, b, link, len(shared_links)))
  if not candidates:
    raise ValueError("could not find a two-stream shared-link case")
  _score, a, b, link, link_count = min(candidates)
  return Case(
    name="shared-link",
    pairs=(a.pair, b.pair),
    routes=(a.route, b.route),
    note=f"paths share {link_count} directed link(s), including raw {_fmt_core(link[0])}->{_fmt_core(link[1])}; all route nodes are live Tensix raw positions",
  )


def singleton_cases(case: Case) -> tuple[Case, Case]:
  return tuple(
    Case(
      name=f"{case.name}-single-{i}",
      pairs=(pair,),
      routes=(route,),
      note="single-stream baseline for paired case",
    )
    for i, (pair, route) in enumerate(zip(case.pairs, case.routes))
  )


def summarize(case: Case, *, noc: int, vc: int, stream_bytes: int,
              senders: list[aggregate.CoreResult], receivers: list[aggregate.CoreResult]) -> str:
  starts = [result.start for result in senders]
  observed = [result.start for result in receivers]
  total_bytes = len(case.pairs) * stream_bytes
  receiver_window = max(observed) - min(starts)
  receiver_bpc = total_bytes / receiver_window if receiver_window > 0 else 0.0
  sender_window = max(result.end for result in senders) - min(starts)
  sender_bpc = total_bytes / sender_window if sender_window > 0 else 0.0
  per_stream = [
    stream_bytes / (receiver.start - sender.start)
    for sender, receiver in zip(senders, receivers)
    if receiver.start > sender.start
  ]
  bad_sentinels = sum(
    receiver.words[11] != aggregate.observe.expected_sentinel(stream_bytes)
    for receiver in receivers
  )
  pairs = " ".join(_fmt_pair(pair) for pair in case.pairs)
  raw_routes = " ".join(f"{_fmt_core(route.raw_source)}->{_fmt_core(route.raw_target)}" for route in case.routes)
  shared_links = len(set(case.routes[0].links) & set(case.routes[1].links)) if len(case.routes) == 2 else 0
  shared_nodes = len(set(case.routes[0].path[1:-1]) & set(case.routes[1].path[1:-1])) if len(case.routes) == 2 else 0
  return (
    f"| {case.name} | {noc} | {vc} | {len(case.pairs)} | `{pairs}` | `{raw_routes}` | "
    f"{shared_nodes} | {shared_links} | {total_bytes / (1024 * 1024):.2f} | "
    f"{sender_window} | {sender_bpc:.3f} | {receiver_window} | {receiver_bpc:.3f} | "
    f"{statistics.fmean(per_stream):.3f} | {min(per_stream):.3f} | {max(per_stream):.3f} | "
    f"{bad_sentinels} | {case.note} |"
  )


def main() -> None:
  parser = argparse.ArgumentParser(description="Compare same-VC streams that share a link vs only cross at a router.")
  parser.add_argument("--noc", type=int, choices=(0, 1), default=0)
  parser.add_argument("--vcs", type=parse_vcs, default=(1,))
  parser.add_argument("--bytes", type=int, default=1024 * 1024, help="payload bytes per sender; multiple of 16 KiB")
  parser.add_argument("--route-order", choices=("xy", "yx"), default="xy")
  parser.add_argument("--dry-run", action="store_true")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-crossing-vc-probe.md"))
  args = parser.parse_args()

  if args.bytes <= 0 or args.bytes % NOC.MAX_BURST_SIZE:
    raise ValueError("--bytes must be a positive multiple of 16 KiB")
  if args.bytes > aggregate.observe.RESULT_BASE - aggregate.observe.STREAM_BASE:
    raise ValueError(f"--bytes must fit below result range; max is {aggregate.observe.RESULT_BASE - aggregate.observe.STREAM_BASE}")

  lines = [
    "| case | noc | vc | streams | pairs | raw routes | shared router nodes | shared directed links | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | per-stream mean B/cyc | per-stream min | per-stream max | bad sentinel rows | note |",
    "|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
  ]

  with harness.open_device() as device:
    cmap = read_tensix_coordinate_map(device)
    pair_routes = enumerate_pair_routes(
      aggregate.usable_program_cores(device), noc=args.noc, cmap=cmap,
      route_order=args.route_order,
    )
    cross = choose_cross_case(pair_routes)
    shared = choose_shared_link_case(pair_routes)
    cases = (*singleton_cases(cross), cross, *singleton_cases(shared), shared)
    if args.dry_run:
      for case in cases:
        print(f"{case.name}: {case.note}")
        for pair, route in zip(case.pairs, case.routes):
          print(f"  {_fmt_pair(pair)} raw {_fmt_core(route.raw_source)}->{_fmt_core(route.raw_target)} links={len(route.links)}")
      return

    for vc in args.vcs:
      for case in cases:
        vcs = [vc] * len(case.pairs)
        senders, receivers = aggregate.run_once(
          device, list(case.pairs), noc=args.noc, stream_bytes=args.bytes,
          vcs=vcs, posted=True,
        )
        lines.append(summarize(
          case, noc=args.noc, vc=vc, stream_bytes=args.bytes,
          senders=senders, receivers=receivers,
        ))

  table = "\n".join(lines)
  print(table)
  if not args.no_report:
    harness.append_report(args.report, "NoC same-VC crossing probe", [
      f"NoC: `{args.noc}`",
      f"VCs: `{','.join(str(vc) for vc in args.vcs)}`",
      f"Bytes per sender: `{args.bytes}`",
      f"Route order assumed for link-set selection: `{args.route_order}`",
      "Traffic: posted unicast writes, all streams in a case use the same static VC",
    ], table)
    print(f"\nappended {args.report}")


if __name__ == "__main__":
  main()
