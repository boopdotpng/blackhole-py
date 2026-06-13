#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402
import riscv_noc_contention_probe as probe  # noqa: E402
from device import Device  # noqa: E402
from microbenching.models.noc_scheduler import (  # noqa: E402
  _dram_endpoint_coord,
  _physical_path_links,
)
from ttk.addrs import Core, Dram  # noqa: E402
from ttk.blackhole_coords import (  # noqa: E402
  HARVESTING_NOC_LOCATIONS,
  T6_X_LOCATIONS,
  TensixCoordinateMap,
  tensix_coordinate_map,
  translated_tensix_to_raw_noc0,
)
from ttk.noc import NOC  # noqa: E402


ENABLED_TENSIX_COL_TAG = 34
QUADRANT_SIGNS = {
  "ne": (1, 1),
  "nw": (-1, 1),
  "sw": (-1, -1),
  "se": (1, -1),
}
OP_ROLE = {
  "write": probe.ROLE_WRITER,
  "read": probe.ROLE_READER,
}


@dataclass(frozen=True)
class MappedCore:
  translated: Core
  raw0: Core


@dataclass(frozen=True)
class Payload:
  source: MappedCore
  target: MappedCore

  @property
  def raw_pair(self) -> tuple[Core, Core]:
    return self.source.raw0, self.target.raw0


@dataclass(frozen=True)
class RouteCase:
  name: str
  quadrant: str
  noc: int
  victim: Payload
  xy_adversary: Payload
  yx_adversary: Payload


@dataclass(frozen=True)
class CaseResult:
  case: RouteCase
  op: str
  baseline_bpc: float
  xy_victim_bpc: float
  yx_victim_bpc: float
  xy_adversary_bpc: float
  yx_adversary_bpc: float
  baseline_counter: int
  xy_counter: int
  yx_counter: int

  @property
  def xy_ratio(self) -> float:
    return self.xy_victim_bpc / self.baseline_bpc if self.baseline_bpc else 0.0

  @property
  def yx_ratio(self) -> float:
    return self.yx_victim_bpc / self.baseline_bpc if self.baseline_bpc else 0.0

  @property
  def vote(self) -> str:
    if self.xy_ratio < self.yx_ratio * 0.85:
      return "xy"
    if self.yx_ratio < self.xy_ratio * 0.85:
      return "yx"
    return "inconclusive"


@dataclass(frozen=True)
class DramRouteCase:
  op: str
  noc: int
  quadrant: str
  worker: MappedCore
  bank: int
  endpoint: int
  dram_coord: Core
  xy_hops: int
  yx_hops: int
  xy_unique: int
  yx_unique: int


def _fmt_core(core: Core) -> str:
  return f"{core[0]},{core[1]}"


def _fmt_payload(payload: Payload) -> str:
  return f"{_fmt_core(payload.source.translated)}->{_fmt_core(payload.target.translated)}"


def _fmt_raw_payload(payload: Payload) -> str:
  return f"{_fmt_core(payload.source.raw0)}->{_fmt_core(payload.target.raw0)}"


def _parse_csv_choices(text: str, valid: set[str], label: str) -> tuple[str, ...]:
  values = tuple(item.strip().lower() for item in text.split(",") if item.strip())
  if not values:
    raise argparse.ArgumentTypeError(f"--{label} selected no values")
  bad = sorted(set(values) - valid)
  if bad:
    raise argparse.ArgumentTypeError(f"unknown {label}: {', '.join(bad)}")
  return values


def parse_nocs(text: str) -> tuple[int, ...]:
  try:
    nocs = tuple(int(item.strip()) for item in text.split(",") if item.strip())
  except ValueError as e:
    raise argparse.ArgumentTypeError("--nocs must be comma-separated integers") from e
  if not nocs:
    raise argparse.ArgumentTypeError("--nocs selected no values")
  bad = sorted(set(nocs) - {0, 1})
  if bad:
    raise argparse.ArgumentTypeError(f"--nocs must contain only 0 and/or 1, got {bad}")
  return nocs


def parse_ops(text: str) -> tuple[str, ...]:
  return _parse_csv_choices(text, set(OP_ROLE), "ops")


def parse_quadrants(text: str) -> tuple[str, ...]:
  return _parse_csv_choices(text, set(QUADRANT_SIGNS), "quadrants")


def read_tensix_coordinate_map(device: Device) -> TensixCoordinateMap:
  layout = device.dev.telemetry_layout()
  enabled = device.dev.telemetry_tag(layout, ENABLED_TENSIX_COL_TAG)
  if enabled is None:
    raise RuntimeError("ENABLED_TENSIX_COL telemetry is unavailable")
  return tensix_coordinate_map(enabled)


def synthetic_coordinate_map() -> TensixCoordinateMap:
  return tensix_coordinate_map((1 << len(HARVESTING_NOC_LOCATIONS)) - 1)


def usable_mapped_cores(device: Device | None, cmap: TensixCoordinateMap) -> list[MappedCore]:
  if device is None:
    cores = [(x, y) for y in range(2, 12) for x in T6_X_LOCATIONS if x not in (15, 16)]
    reserved: set[Core] = set()
  else:
    reserved = {
      getattr(device.board_info, "dispatch_core", None),
      getattr(device.board_info, "prefetch_core", None),
    }
    cores = sorted(set(device.cores) - {core for core in reserved if core is not None})
  out = []
  for core in cores:
    try:
      raw0 = translated_tensix_to_raw_noc0(core, cmap)
    except ValueError:
      continue
    out.append(MappedCore(core, raw0))
  return sorted(out, key=lambda core: (core.raw0[1], core.raw0[0], core.translated))


def _links(payload: Payload, noc: int, route_order: str) -> set[tuple[Core, Core]]:
  return set(_physical_path_links(payload.source.raw0, payload.target.raw0, noc, route_order=route_order))


def _axis_adversary_candidates(
  mapped: list[MappedCore],
  *,
  victim: Payload,
  noc: int,
  axis: str,
  want_links: set[tuple[Core, Core]],
  avoid_links: set[tuple[Core, Core]],
) -> list[tuple[int, Payload, int]]:
  blocked = {victim.source.translated, victim.target.translated}
  out = []
  for src in mapped:
    if src.translated in blocked:
      continue
    for dst in mapped:
      if dst.translated in blocked or dst.translated == src.translated:
        continue
      if axis == "x" and src.raw0[1] != dst.raw0[1]:
        continue
      if axis == "y" and src.raw0[0] != dst.raw0[0]:
        continue
      payload = Payload(src, dst)
      links = _links(payload, noc, "xy")
      hit = len(links & want_links)
      if hit == 0 or links & avoid_links:
        continue
      out.append((len(links), payload, -hit))
  return sorted(out, key=lambda item: (item[0], item[2], item[1].source.raw0, item[1].target.raw0))


def _quadrant(src: Core, dst: Core) -> str | None:
  dx = dst[0] - src[0]
  dy = dst[1] - src[1]
  if dx == 0 or dy == 0:
    return None
  sx = 1 if dx > 0 else -1
  sy = 1 if dy > 0 else -1
  for name, signs in QUADRANT_SIGNS.items():
    if signs == (sx, sy):
      return name
  return None


def _victim_candidates(mapped: list[MappedCore], *, quadrant: str, noc: int) -> list[tuple[int, Payload]]:
  out = []
  for src in mapped:
    for dst in mapped:
      if src.translated == dst.translated:
        continue
      if _quadrant(src.raw0, dst.raw0) != quadrant:
        continue
      payload = Payload(src, dst)
      xy = _links(payload, noc, "xy")
      yx = _links(payload, noc, "yx")
      xy_unique = xy - yx
      yx_unique = yx - xy
      if not xy_unique or not yx_unique:
        continue
      hops = len(xy)
      # Prefer compact, nontrivial diagonals with enough room for a crossing
      # stream, then stable low-coordinate placements for reproducibility.
      if hops < 4:
        continue
      out.append((hops, payload))
  return sorted(out, key=lambda item: (item[0], item[1].source.raw0, item[1].target.raw0))


def select_route_case(mapped: list[MappedCore], *, quadrant: str, noc: int) -> RouteCase:
  for _hops, victim in _victim_candidates(mapped, quadrant=quadrant, noc=noc):
    xy_links = _links(victim, noc, "xy")
    yx_links = _links(victim, noc, "yx")
    xy_unique = xy_links - yx_links
    yx_unique = yx_links - xy_links
    xy_adv = _axis_adversary_candidates(
      mapped, victim=victim, noc=noc, axis="x", want_links=xy_unique, avoid_links=yx_unique
    )
    yx_adv = _axis_adversary_candidates(
      mapped, victim=victim, noc=noc, axis="y", want_links=yx_unique, avoid_links=xy_unique
    )
    if not xy_adv or not yx_adv:
      continue
    xy_payload = xy_adv[0][1]
    yx_payload = next(
      (item[1] for item in yx_adv if {
        item[1].source.translated, item[1].target.translated,
      }.isdisjoint({xy_payload.source.translated, xy_payload.target.translated})),
      None,
    )
    if yx_payload is None:
      continue
    return RouteCase(
      name=f"q{quadrant}_noc{noc}_{_fmt_core(victim.source.raw0)}_to_{_fmt_core(victim.target.raw0)}",
      quadrant=quadrant,
      noc=noc,
      victim=victim,
      xy_adversary=xy_payload,
      yx_adversary=yx_payload,
    )
  raise ValueError(f"could not build route tomography case for quadrant {quadrant!r} on NoC{noc}")


def build_route_cases(mapped: list[MappedCore], *, nocs: tuple[int, ...], quadrants: tuple[str, ...]) -> list[RouteCase]:
  cases = []
  for noc in nocs:
    for quadrant in quadrants:
      cases.append(select_route_case(mapped, quadrant=quadrant, noc=noc))
  return cases


def _stream_for_payload(name: str, payload: Payload, *, op: str, result_base: int) -> probe.ActiveStream:
  role = OP_ROLE[op]
  if op == "write":
    active_source = payload.source.translated
    target = payload.target.translated
  elif op == "read":
    # For reads, the dominant payload returns from target to initiator. Keep the
    # generated payload direction identical to the write case by swapping the
    # active requester and target.
    active_source = payload.target.translated
    target = payload.source.translated
  else:
    raise ValueError(f"unsupported op {op!r}")
  return probe.ActiveStream(name, active_source, target, role, result_base)


def _run_streams(
  device: Device,
  streams: list[probe.ActiveStream],
  *,
  noc: int,
  stream_bytes: int,
  repeats: int,
  gate_delay_cycles: int,
) -> dict[str, probe.Result]:
  results = probe.run_stream_set(
    device,
    streams,
    noc=noc,
    stream_bytes=stream_bytes,
    repeats=repeats,
    dry_run=False,
    gate_delay_cycles=gate_delay_cycles,
  )
  return {result.name: result for result in results}


def run_route_case(
  device: Device,
  case: RouteCase,
  *,
  op: str,
  stream_bytes: int,
  repeats: int,
  gate_delay_cycles: int,
) -> CaseResult:
  baseline_stream = _stream_for_payload("victim", case.victim, op=op, result_base=probe.RESULT_BASE)
  xy_streams = [
    _stream_for_payload("victim", case.victim, op=op, result_base=probe.RESULT_BASE),
    _stream_for_payload("xy_adversary", case.xy_adversary, op=op, result_base=probe.RESULT_BASE),
  ]
  yx_streams = [
    _stream_for_payload("victim", case.victim, op=op, result_base=probe.RESULT_BASE),
    _stream_for_payload("yx_adversary", case.yx_adversary, op=op, result_base=probe.RESULT_BASE),
  ]
  baseline = _run_streams(
    device, [baseline_stream], noc=case.noc, stream_bytes=stream_bytes,
    repeats=repeats, gate_delay_cycles=gate_delay_cycles,
  )["victim"]
  xy = _run_streams(
    device, xy_streams, noc=case.noc, stream_bytes=stream_bytes,
    repeats=repeats, gate_delay_cycles=gate_delay_cycles,
  )
  yx = _run_streams(
    device, yx_streams, noc=case.noc, stream_bytes=stream_bytes,
    repeats=repeats, gate_delay_cycles=gate_delay_cycles,
  )
  return CaseResult(
    case=case,
    op=op,
    baseline_bpc=baseline.bytes_per_cycle(),
    xy_victim_bpc=xy["victim"].bytes_per_cycle(),
    yx_victim_bpc=yx["victim"].bytes_per_cycle(),
    xy_adversary_bpc=xy["xy_adversary"].bytes_per_cycle(),
    yx_adversary_bpc=yx["yx_adversary"].bytes_per_cycle(),
    baseline_counter=baseline.counter_delta,
    xy_counter=xy["victim"].counter_delta,
    yx_counter=yx["victim"].counter_delta,
  )


def route_case_table(cases: list[RouteCase]) -> str:
  lines = [
    "| case | noc | quadrant | victim translated | victim raw | xy adversary translated/raw | yx adversary translated/raw | xy-only links | yx-only links |",
    "|---|---:|---|---|---|---|---|---:|---:|",
  ]
  for case in cases:
    xy = _links(case.victim, case.noc, "xy")
    yx = _links(case.victim, case.noc, "yx")
    lines.append(
      f"| {case.name} | {case.noc} | {case.quadrant} | `{_fmt_payload(case.victim)}` | "
      f"`{_fmt_raw_payload(case.victim)}` | `{_fmt_payload(case.xy_adversary)}` / `{_fmt_raw_payload(case.xy_adversary)}` | "
      f"`{_fmt_payload(case.yx_adversary)}` / `{_fmt_raw_payload(case.yx_adversary)}` | "
      f"{len(xy - yx)} | {len(yx - xy)} |"
    )
  return "\n".join(lines)


def result_table(results: list[CaseResult]) -> str:
  lines = [
    "| op | noc | quadrant | victim raw | baseline B/cyc | xy-cross victim B/cyc | yx-cross victim B/cyc | xy ratio | yx ratio | vote | counters base/xy/yx | adversary B/cyc xy/yx |",
    "|---|---:|---|---|---:|---:|---:|---:|---:|---|---|---|",
  ]
  for result in results:
    case = result.case
    lines.append(
      f"| {result.op} | {case.noc} | {case.quadrant} | `{_fmt_raw_payload(case.victim)}` | "
      f"{result.baseline_bpc:.3f} | {result.xy_victim_bpc:.3f} | {result.yx_victim_bpc:.3f} | "
      f"{result.xy_ratio:.3f} | {result.yx_ratio:.3f} | {result.vote} | "
      f"{result.baseline_counter}/{result.xy_counter}/{result.yx_counter} | "
      f"{result.xy_adversary_bpc:.3f}/{result.yx_adversary_bpc:.3f} |"
    )
  return "\n".join(lines)


def summarize_votes(results: list[CaseResult]) -> list[str]:
  lines = []
  grouped: dict[tuple[int, str], list[CaseResult]] = {}
  for result in results:
    grouped.setdefault((result.case.noc, result.op), []).append(result)
  for (noc, op), group in sorted(grouped.items()):
    votes = {vote: sum(1 for result in group if result.vote == vote) for vote in ("xy", "yx", "inconclusive")}
    mean_xy = sum(result.xy_ratio for result in group) / len(group)
    mean_yx = sum(result.yx_ratio for result in group) / len(group)
    winner = "xy" if votes["xy"] > votes["yx"] else "yx" if votes["yx"] > votes["xy"] else "inconclusive"
    lines.append(
      f"- NoC{noc} {op}: votes xy/yx/inconclusive = "
      f"`{votes['xy']}/{votes['yx']}/{votes['inconclusive']}`, mean victim ratios xy/yx = "
      f"`{mean_xy:.3f}/{mean_yx:.3f}`, route-order readout `{winner}`."
    )
  return lines


def scheduler_implications(results: list[CaseResult]) -> list[str]:
  implications = []
  grouped: dict[tuple[int, str], list[CaseResult]] = {}
  for result in results:
    grouped.setdefault((result.case.noc, result.op), []).append(result)
  for (noc, op), group in sorted(grouped.items()):
    decisive = [result.vote for result in group if result.vote in ("xy", "yx")]
    unique = sorted(set(decisive))
    if len(unique) == 1:
      implications.append(
        f"- Scheduler implication: this subset supports `route_order=\"{unique[0]}\"` for NoC{noc} L1 {op} payloads."
      )
    elif not decisive:
      implications.append(
        f"- Scheduler implication: NoC{noc} L1 {op} payload route order remains inconclusive from this subset."
      )
    else:
      implications.append(
        f"- Scheduler implication: NoC{noc} L1 {op} payloads produced mixed route-order votes; keep per-transaction overrides."
      )
  if implications:
    implications.append("- Scheduler constants: no bandwidth or latency constants are changed by this route-order run.")
  return implications


def _dram_payload_endpoints(worker: MappedCore, dram_coord: Core, op: str) -> tuple[Core, Core]:
  if op == "dram_write":
    return worker.raw0, dram_coord
  if op == "dram_read":
    return dram_coord, worker.raw0
  raise ValueError(f"unsupported DRAM op {op!r}")


def build_dram_route_cases(
  mapped: list[MappedCore],
  *,
  nocs: tuple[int, ...],
  quadrants: tuple[str, ...],
  harvested_dram_bank: int | None,
) -> list[DramRouteCase]:
  out = []
  bank_count = Dram.BANK_COUNT if harvested_dram_bank is None else Dram.BANK_COUNT - 1
  for noc in nocs:
    for op in ("dram_read", "dram_write"):
      for quadrant in quadrants:
        best = None
        for worker in mapped:
          for bank in range(bank_count):
            for endpoint in range(Dram.TILES_PER_BANK):
              dram_coord = _dram_endpoint_coord(bank, endpoint, harvested_dram_bank)
              payload_src, payload_dst = _dram_payload_endpoints(worker, dram_coord, op)
              if _quadrant(payload_src, payload_dst) != quadrant:
                continue
              xy = set(_physical_path_links(payload_src, payload_dst, noc, route_order="xy"))
              yx = set(_physical_path_links(payload_src, payload_dst, noc, route_order="yx"))
              if not xy or not yx:
                continue
              score = (abs(len(xy) - 6), bank, endpoint, worker.raw0)
              item = DramRouteCase(
                op=op,
                noc=noc,
                quadrant=quadrant,
                worker=worker,
                bank=bank,
                endpoint=endpoint,
                dram_coord=dram_coord,
                xy_hops=len(xy),
                yx_hops=len(yx),
                xy_unique=len(xy - yx),
                yx_unique=len(yx - xy),
              )
              if best is None or score < best[0]:
                best = (score, item)
        if best is not None:
          out.append(best[1])
  return out


def dram_case_table(cases: list[DramRouteCase]) -> str:
  lines = [
    "| op | noc | quadrant | worker translated/raw | bank | endpoint | dram router | hops xy/yx | unique links xy/yx |",
    "|---|---:|---|---|---:|---:|---|---:|---:|",
  ]
  for case in cases:
    lines.append(
      f"| {case.op} | {case.noc} | {case.quadrant} | "
      f"`{_fmt_core(case.worker.translated)}` / `{_fmt_core(case.worker.raw0)}` | "
      f"{case.bank} | {case.endpoint} | `{_fmt_core(case.dram_coord)}` | "
      f"{case.xy_hops}/{case.yx_hops} | {case.xy_unique}/{case.yx_unique} |"
    )
  return "\n".join(lines)


def append_report(
  path: Path,
  *,
  args,
  cmap: TensixCoordinateMap,
  cases: list[RouteCase],
  results: list[CaseResult],
  dram_cases: list[DramRouteCase],
):
  now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
  with path.open("a", encoding="utf-8") as f:
    f.write(f"\n## Run {now}\n\n")
    f.write(f"- NoCs: `{','.join(str(noc) for noc in args.nocs)}`\n")
    f.write(f"- Ops: `{','.join(args.ops)}`\n")
    f.write(f"- Quadrants requested: `{','.join(args.quadrants)}`\n")
    f.write(f"- Bytes per stream repeat: `{args.bytes}`\n")
    f.write(f"- Repeats: `{args.repeats}`\n")
    f.write(f"- Start gate lead: `{args.gate_delay_cycles}` cycles\n")
    f.write(f"- ENABLED_TENSIX_COL: `0x{cmap.enabled_tensix_col:08x}`\n")
    f.write(f"- Harvested raw Tensix columns: `{list(cmap.harvested_raw_x)}`\n")
    f.write("- Traffic: L1 write/read route tomography runs one victim alone, then victim plus an X-leg adversary, then victim plus a Y-leg adversary.\n")
    f.write("- Interpretation: the adversary that slows the victim more identifies the route-order leg used by the payload.\n\n")
    f.write("Full L1 route-order matrix command:\n\n")
    f.write("```bash\n")
    f.write("PYTHONPATH=. python3 microbenching/noc/riscv_noc_route_tomography.py --nocs 0,1 --ops write,read --quadrants ne,nw,sw,se --include-dram-model\n")
    f.write("```\n\n")
    f.write("Generated L1 cases:\n\n")
    f.write(route_case_table(cases))
    f.write("\n\n")
    if results:
      f.write("Measured L1 results:\n\n")
      f.write(result_table(results))
      f.write("\n\n")
      for line in summarize_votes(results):
        f.write(line)
        f.write("\n")
      for line in scheduler_implications(results):
        f.write(line)
        f.write("\n")
      f.write("\n")
    if dram_cases:
      f.write("Generated DRAM endpoint route cases (model coverage; run `riscv_dram_noc_bench.py` for endpoint bandwidth):\n\n")
      f.write(dram_case_table(dram_cases))
      f.write("\n")


def main():
  parser = argparse.ArgumentParser(description="Generate and run Blackhole NoC route-order tomography cases.")
  parser.add_argument("--nocs", type=parse_nocs, default=(0, 1), help="comma-separated NoC ids")
  parser.add_argument("--ops", type=parse_ops, default=("write", "read"), help="comma-separated L1 ops: write,read")
  parser.add_argument("--quadrants", type=parse_quadrants, default=("ne", "nw", "sw", "se"))
  parser.add_argument("--bytes", type=int, default=256 * 1024, help="bytes per stream repeat; multiple of 16 KiB")
  parser.add_argument("--repeats", type=int, default=2)
  parser.add_argument("--gate-delay-cycles", type=int, default=200_000_000)
  parser.add_argument("--max-cases", type=int, default=0, help="limit L1 cases after generation; 0 means all")
  parser.add_argument("--include-dram-model", action="store_true", help="include generated DRAM endpoint route rows in the report")
  parser.add_argument("--dry-run", action="store_true", help="generate cases and lower programs without opening hardware")
  parser.add_argument("--no-report", action="store_true")
  parser.add_argument("--report", type=Path, default=harness.doc_path("noc", "noc-route-tomography.md"))
  args = parser.parse_args()

  try:
    probe.validate_bytes(args.bytes)
  except ValueError as e:
    parser.error(str(e))
  if args.repeats <= 0:
    parser.error("--repeats must be positive")
  if args.gate_delay_cycles < 0:
    parser.error("--gate-delay-cycles must be non-negative")
  if args.max_cases < 0:
    parser.error("--max-cases must be non-negative")

  results: list[CaseResult] = []
  device = None if args.dry_run else Device()
  try:
    cmap = synthetic_coordinate_map() if args.dry_run else read_tensix_coordinate_map(device)
    mapped = usable_mapped_cores(device, cmap)
    cases = build_route_cases(mapped, nocs=args.nocs, quadrants=args.quadrants)
    if args.max_cases:
      cases = cases[:args.max_cases]
    harvested_dram_bank = None if device is None else device.board_info.harvested_dram_bank
    dram_cases = build_dram_route_cases(
      mapped, nocs=args.nocs, quadrants=args.quadrants, harvested_dram_bank=harvested_dram_bank
    ) if args.include_dram_model else []

    print(route_case_table(cases))
    if dram_cases:
      print()
      print(dram_case_table(dram_cases))

    if args.dry_run:
      for case in cases:
        for op in args.ops:
          streams = [
            _stream_for_payload("victim", case.victim, op=op, result_base=probe.RESULT_BASE),
            _stream_for_payload("xy_adversary", case.xy_adversary, op=op, result_base=probe.RESULT_BASE),
          ]
          probe.MultiCoreProgram(streams, noc=case.noc, stream_bytes=args.bytes, repeats=args.repeats).lower(
            sorted({stream.source for stream in streams} | {stream.target for stream in streams})
          )
      print("\ndry-run lowering passed")
      return

    assert device is not None
    for case in cases:
      for op in args.ops:
        results.append(run_route_case(
          device,
          case,
          op=op,
          stream_bytes=args.bytes,
          repeats=args.repeats,
          gate_delay_cycles=args.gate_delay_cycles,
        ))

    print()
    print(result_table(results))
    for line in summarize_votes(results):
      print(line)
    for line in scheduler_implications(results):
      print(line)
    if not args.no_report:
      append_report(args.report, args=args, cmap=cmap, cases=cases, results=results, dram_cases=dram_cases)
      print(f"\nappended {args.report}")
  finally:
    if device is not None:
      device.close()


if __name__ == "__main__":
  main()
