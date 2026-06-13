#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from microbenching.models.noc_scheduler import (  # noqa: E402
  Calibration,
  _dram_endpoint_coord,
  _physical_path,
  schedule,
)
from ttk.addrs import Core, Dram  # noqa: E402
from ttk.blackhole_coords import (  # noqa: E402
  TensixCoordinateMap,
  live_raw_tensix_cores,
  tensix_coordinate_map,
  translated_live_tensix_cores,
  translated_tensix_to_raw_noc0,
)


def _coord(value: Any) -> Core:
  if not isinstance(value, (list, tuple)) or len(value) != 2:
    raise ValueError(f"coordinate must be [x, y], got {value!r}")
  return int(value[0]), int(value[1])


def _coord_key(coord: Core) -> list[int]:
  return [int(coord[0]), int(coord[1])]


def _logical_bank_count(harvested_dram_bank: int | None) -> int:
  return Dram.BANK_COUNT if harvested_dram_bank is None else Dram.BANK_COUNT - 1


def _banks(value: Any, harvested_dram_bank: int | None) -> list[int]:
  bank_count = _logical_bank_count(harvested_dram_bank)
  if value is None or value == "all":
    return list(range(bank_count))
  if isinstance(value, int):
    banks = list(range(value))
  else:
    banks = [int(item) for item in value]
  bad = [bank for bank in banks if bank < 0 or bank >= bank_count]
  if bad:
    raise ValueError(f"DRAM bank(s) outside logical range 0..{bank_count - 1}: {bad}")
  return banks


def _core_endpoint(core: Core, *, space: str, label: str) -> dict[str, Any]:
  return {"kind": "l1", "space": space, "coord": _coord_key(core), "label": label}


def _format_template(template: Any, **values: Any) -> str:
  if template is None:
    return ""
  return str(template).format(**values)


def _issue_stream(pattern: dict[str, Any], **values: Any) -> str:
  template = pattern.get("issue_stream", pattern.get("stream"))
  return _format_template(template, **values)


def _raw_for_core(core: Core, *, space: str, cmap: TensixCoordinateMap | None) -> Core:
  if space == "route":
    return core
  if space == "translated_tensix_noc0":
    if cmap is None:
      raise ValueError("translated core space needs enabled_tensix_col")
    return translated_tensix_to_raw_noc0(core, cmap)
  raise ValueError(f"unknown core coordinate space {space!r}")


def _select_cores(pattern: dict[str, Any], *, cmap: TensixCoordinateMap | None) -> tuple[list[Core], str]:
  space = str(pattern.get("core_space", "translated_tensix_noc0"))
  cores_spec = pattern.get("cores", "live")
  if cores_spec in ("live", "translated_live"):
    if cmap is None:
      raise ValueError("live/translated_live cores need enabled_tensix_col")
    cores = translated_live_tensix_cores(cmap)
    space = "translated_tensix_noc0"
  elif cores_spec == "live_raw":
    if cmap is None:
      raise ValueError("live_raw cores need enabled_tensix_col")
    cores = live_raw_tensix_cores(cmap)
    space = "route"
  elif isinstance(cores_spec, list):
    cores = [_coord(item) for item in cores_spec]
  else:
    raise ValueError(f"unknown cores selector {cores_spec!r}")

  excluded = {_coord(item) for item in pattern.get("exclude", [])}
  cores = [core for core in cores if core not in excluded]
  offset = int(pattern.get("core_offset", 0))
  if offset:
    cores = cores[offset:]
  count = pattern.get("core_count")
  if count is not None:
    cores = cores[:int(count)]
  if not cores:
    raise ValueError(f"{pattern.get('name', 'pattern')}: no cores selected")
  return cores, space


def _route_order(pattern: dict[str, Any], cal: Calibration) -> str:
  return str(pattern.get("route_order", cal.route_order))


def _dram_payload_hops(core_raw: Core, *, op: str, noc: int, route_order: str,
                       bank: int, endpoint: int, harvested_dram_bank: int | None) -> int:
  dram_raw = _dram_endpoint_coord(bank, endpoint, harvested_dram_bank)
  if op in ("read", "dram_read", "l1_read"):
    src, dst = dram_raw, core_raw
  elif op in ("write", "dram_write", "l1_write"):
    src, dst = core_raw, dram_raw
  else:
    raise ValueError(f"nearest DRAM selection only supports read/write ops, got {op!r}")
  return len(_physical_path(src, dst, noc, route_order=route_order)) - 1


def _choose_dram_endpoint(
  core_raw: Core,
  *,
  op: str,
  noc: int,
  route_order: str,
  banks: list[int],
  bank_mode: str,
  endpoint_mode: str | int,
  index: int,
  bytes_: int,
  endpoint_load: dict[tuple[int, int], int],
  balance_hop_slack: int,
  harvested_dram_bank: int | None,
) -> tuple[int, int]:
  def metric(bank: int, endpoint: int) -> tuple[int, int, int]:
    return (
      _dram_payload_hops(
        core_raw,
        op=op,
        noc=noc,
        route_order=route_order,
        bank=bank,
        endpoint=endpoint,
        harvested_dram_bank=harvested_dram_bank,
      ),
      bank,
      endpoint,
    )

  if bank_mode in ("nearest", "nearest_balanced", "balanced"):
    candidate_banks = banks
  elif bank_mode == "round_robin":
    candidate_banks = [banks[index % len(banks)]]
  else:
    raise ValueError(f"bank_mode must be round_robin, nearest, nearest_balanced, or balanced, got {bank_mode!r}")

  if endpoint_mode == "nearest":
    candidates = [(bank, endpoint) for bank in candidate_banks for endpoint in range(Dram.TILES_PER_BANK)]
  else:
    if endpoint_mode == "split3":
      endpoint = index % Dram.TILES_PER_BANK
    else:
      endpoint = int(endpoint_mode)
    if endpoint < 0 or endpoint >= Dram.TILES_PER_BANK:
      raise ValueError(f"endpoint must be in 0..{Dram.TILES_PER_BANK - 1}, got {endpoint}")
    candidates = [(bank, endpoint) for bank in candidate_banks]

  if bank_mode == "balanced":
    chosen = min(candidates, key=lambda item: (endpoint_load.get(item, 0), metric(item[0], item[1])))
  elif bank_mode == "nearest_balanced":
    min_hops = min(metric(bank, endpoint)[0] for bank, endpoint in candidates)
    eligible = [
      (bank, endpoint)
      for bank, endpoint in candidates
      if metric(bank, endpoint)[0] <= min_hops + balance_hop_slack
    ]
    chosen = min(eligible, key=lambda item: (endpoint_load.get(item, 0), metric(item[0], item[1])))
  elif bank_mode == "nearest":
    chosen = min(candidates, key=lambda item: metric(item[0], item[1]))
  else:
    chosen = min(candidates, key=lambda item: metric(item[0], item[1]))

  endpoint_load[chosen] = endpoint_load.get(chosen, 0) + bytes_
  return chosen


def _expand_dram_stream(
  pattern: dict[str, Any],
  *,
  cmap: TensixCoordinateMap | None,
  harvested_dram_bank: int | None,
  cal: Calibration,
) -> list[dict[str, Any]]:
  name = str(pattern.get("name", "dram-stream"))
  op = str(pattern["op"])
  noc = int(pattern.get("noc", 0))
  route_order = _route_order(pattern, cal)
  bytes_per_core = int(pattern.get("bytes_per_core", pattern.get("bytes", 0)))
  if bytes_per_core <= 0:
    raise ValueError(f"{name}: bytes_per_core must be positive")
  packet_bytes = int(pattern.get("packet_bytes", cal.max_packet_bytes))
  count = int(pattern.get("count", 1))
  cores, core_space = _select_cores(pattern, cmap=cmap)
  banks = _banks(pattern.get("banks"), harvested_dram_bank)
  bank_mode = str(pattern.get("bank_mode", "round_robin"))
  endpoint_mode = pattern.get("endpoint_mode", "split3")
  balance_hop_slack = int(pattern.get("balance_hop_slack", 2))
  if balance_hop_slack < 0:
    raise ValueError(f"{name}: balance_hop_slack must be non-negative")
  endpoint_load: dict[tuple[int, int], int] = {}

  txns = []
  for i, core in enumerate(cores):
    raw = _raw_for_core(core, space=core_space, cmap=cmap)
    bank, endpoint = _choose_dram_endpoint(
      raw,
      op=op,
      noc=noc,
      route_order=route_order,
      banks=banks,
      bank_mode=bank_mode,
      endpoint_mode=endpoint_mode,
      index=i,
      bytes_=bytes_per_core * count,
      endpoint_load=endpoint_load,
      balance_hop_slack=balance_hop_slack,
      harvested_dram_bank=harvested_dram_bank,
    )
    l1 = _core_endpoint(core, space=core_space, label=f"{name}.c{core[0]},{core[1]}")
    dram = {"kind": "dram", "bank": bank, "endpoint": endpoint, "label": f"{name}.b{bank}.e{endpoint}"}
    txns.append({
      "name": f"{name}.{i}",
      "op": op,
      "noc": noc,
      "issue_stream": _issue_stream(
        pattern,
        name=name,
        op=op,
        noc=noc,
        i=i,
        x=core[0],
        y=core[1],
        raw_x=raw[0],
        raw_y=raw[1],
        bank=bank,
        endpoint=endpoint,
      ),
      "bytes": bytes_per_core,
      "packet_bytes": packet_bytes,
      "count": count,
      "route_order": route_order,
      "initiator": l1,
      "target": dram,
    })
  return txns


def _expand_unicast_pairs(pattern: dict[str, Any], *, cmap: TensixCoordinateMap | None, cal: Calibration) -> list[dict[str, Any]]:
  name = str(pattern.get("name", "unicast"))
  op = str(pattern.get("op", "write"))
  noc = int(pattern.get("noc", 0))
  route_order = _route_order(pattern, cal)
  space = str(pattern.get("space", "translated_tensix_noc0"))
  bytes_ = int(pattern.get("bytes", 0))
  if bytes_ <= 0:
    raise ValueError(f"{name}: bytes must be positive")
  pairs = pattern.get("pairs")
  if not isinstance(pairs, list) or not pairs:
    raise ValueError(f"{name}: pairs must be a non-empty list")
  out = []
  for i, pair in enumerate(pairs):
    if isinstance(pair, dict):
      src = _coord(pair["source"])
      dst = _coord(pair["target"])
      pair_bytes = int(pair.get("bytes", bytes_))
    else:
      src = _coord(pair[0])
      dst = _coord(pair[1])
      pair_bytes = bytes_
    raw_src = _raw_for_core(src, space=space, cmap=cmap)
    raw_dst = _raw_for_core(dst, space=space, cmap=cmap)
    out.append({
      "name": f"{name}.{i}",
      "op": op,
      "noc": noc,
      "issue_stream": _issue_stream(
        pattern,
        name=name,
        op=op,
        noc=noc,
        i=i,
        sx=src[0],
        sy=src[1],
        tx=dst[0],
        ty=dst[1],
        raw_sx=raw_src[0],
        raw_sy=raw_src[1],
        raw_tx=raw_dst[0],
        raw_ty=raw_dst[1],
      ),
      "bytes": pair_bytes,
      "packet_bytes": int(pattern.get("packet_bytes", cal.max_packet_bytes)),
      "route_order": route_order,
      "initiator": _core_endpoint(src, space=space, label=f"{name}.src{i}"),
      "target": _core_endpoint(dst, space=space, label=f"{name}.dst{i}"),
    })
  return out


def _expand_mcast_rect(pattern: dict[str, Any], *, cmap: TensixCoordinateMap | None, cal: Calibration) -> list[dict[str, Any]]:
  name = str(pattern.get("name", "mcast"))
  space = str(pattern.get("space", "translated_tensix_noc0"))
  source = _coord(pattern["source"])
  raw_source = _raw_for_core(source, space=space, cmap=cmap)
  rect = pattern["rect"]
  if isinstance(rect, dict):
    target_rect = dict(rect)
  else:
    x0, y0, x1, y1 = [int(value) for value in rect]
    target_rect = {"x0": x0, "y0": y0, "x1": x1, "y1": y1}
  target_rect.setdefault("kind", "l1")
  target_rect.setdefault("space", space)
  target_rect.setdefault("label", name)
  return [{
    "name": name,
    "op": str(pattern.get("op", "mcast_write")),
    "noc": int(pattern.get("noc", 0)),
    "issue_stream": _issue_stream(
      pattern,
      name=name,
      op=str(pattern.get("op", "mcast_write")),
      noc=int(pattern.get("noc", 0)),
      sx=source[0],
      sy=source[1],
      raw_sx=raw_source[0],
      raw_sy=raw_source[1],
    ),
    "bytes": int(pattern["bytes"]),
    "packet_bytes": int(pattern.get("packet_bytes", cal.max_packet_bytes)),
    "route_order": pattern.get("route_order"),
    "mcast_major": pattern.get("mcast_major", pattern.get("major", "x")),
    "path_reserve": bool(pattern.get("path_reserve", False)),
    "vc_linked": bool(pattern.get("vc_linked", False)),
    "initiator": _core_endpoint(source, space=space, label=f"{name}.src"),
    "rect": target_rect,
  }]


def expand_spec(spec: dict[str, Any]) -> dict[str, Any]:
  cal = Calibration.from_dict(spec.get("calibration"))
  enabled_tensix_col = spec.get("enabled_tensix_col")
  cmap = None if enabled_tensix_col is None else tensix_coordinate_map(int(enabled_tensix_col))
  harvested_dram_bank = spec.get("harvested_dram_bank")
  if harvested_dram_bank is not None:
    harvested_dram_bank = int(harvested_dram_bank)

  out = {
    key: value
    for key, value in spec.items()
    if key not in ("patterns", "transactions")
  }
  out["transactions"] = list(spec.get("transactions", []))
  for pattern in spec.get("patterns", []):
    kind = str(pattern.get("kind", pattern.get("type", "dram_stream")))
    if kind == "dram_stream":
      out["transactions"].extend(_expand_dram_stream(
        pattern,
        cmap=cmap,
        harvested_dram_bank=harvested_dram_bank,
        cal=cal,
      ))
    elif kind == "unicast_pairs":
      out["transactions"].extend(_expand_unicast_pairs(pattern, cmap=cmap, cal=cal))
    elif kind == "mcast_rect":
      out["transactions"].extend(_expand_mcast_rect(pattern, cmap=cmap, cal=cal))
    else:
      raise ValueError(f"unknown pattern kind {kind!r}")
  return out


def _self_test():
  spec = {
    "enabled_tensix_col": 0x3BF7,
    "harvested_dram_bank": 7,
    "patterns": [
      {
        "kind": "dram_stream",
        "name": "read-near",
        "op": "read",
        "noc": 0,
        "cores": "translated_live",
        "core_count": 4,
        "bytes_per_core": 32768,
        "issue_stream": "core-{x}-{y}",
        "bank_mode": "nearest",
        "endpoint_mode": "nearest",
        "route_order": "xy",
      },
      {
        "kind": "dram_stream",
        "name": "write-near",
        "op": "write",
        "noc": 1,
        "cores": "translated_live",
        "core_count": 4,
        "bytes_per_core": 32768,
        "stream": "core-{raw_x}-{raw_y}",
        "bank_mode": "nearest",
        "endpoint_mode": "nearest",
        "route_order": "yx",
      },
      {
        "kind": "unicast_pairs",
        "name": "pairs",
        "noc": 1,
        "bytes": 16384,
        "space": "translated_tensix_noc0",
        "pairs": [[[6, 2], [7, 2]]],
      },
      {
        "kind": "mcast_rect",
        "name": "fanout",
        "noc": 0,
        "source": [1, 2],
        "rect": [1, 2, 2, 3],
        "bytes": 16384,
      },
    ],
  }
  expanded = expand_spec(spec)
  assert len(expanded["transactions"]) == 10
  assert expanded["transactions"][0]["initiator"]["coord"] == [1, 2]
  assert expanded["transactions"][0]["initiator"]["space"] == "translated_tensix_noc0"
  assert expanded["transactions"][0]["issue_stream"] == "core-1-2"
  assert expanded["transactions"][4]["issue_stream"] == "core-1-2"
  assert expanded["transactions"][8]["initiator"]["coord"] == [6, 2]
  assert expanded["transactions"][9]["rect"]["space"] == "translated_tensix_noc0"

  from microbenching.models.noc_scheduler import _transactions_from_dict  # noqa: PLC0415

  txns, parsed_cal = _transactions_from_dict(expanded)
  est = schedule(txns, parsed_cal)
  assert est.cycles > 0
  write0_start = min(pkt.start_cycle for pkt in est.packets if pkt.transaction == "write-near.0")
  assert write0_start >= est.transaction_completion["read-near.0"]

  rr_endpoint = expand_spec({
    "enabled_tensix_col": 0x3BF7,
    "harvested_dram_bank": 7,
    "patterns": [{
      "kind": "dram_stream",
      "name": "rr",
      "op": "read",
      "noc": 0,
      "cores": [[1, 2]],
      "bytes_per_core": 16384,
      "bank_mode": "round_robin",
      "banks": [0],
      "endpoint_mode": "nearest",
      "route_order": "xy",
    }],
  })
  assert rr_endpoint["transactions"][0]["target"]["endpoint"] == 1

  balanced = expand_spec({
    "enabled_tensix_col": 0x3BF7,
    "harvested_dram_bank": 7,
    "patterns": [{
      "kind": "dram_stream",
      "name": "balanced",
      "op": "read",
      "noc": 0,
      "cores": "translated_live",
      "core_count": 24,
      "bytes_per_core": 16384,
      "bank_mode": "nearest_balanced",
      "endpoint_mode": "nearest",
      "balance_hop_slack": 2,
      "route_order": "xy",
    }],
  })
  used_endpoints = {
    (txn["target"]["bank"], txn["target"]["endpoint"])
    for txn in balanced["transactions"]
  }
  assert len(used_endpoints) > 1


def main():
  parser = argparse.ArgumentParser(description="Expand compact NoC workload patterns into scheduler JSON.")
  parser.add_argument("spec", nargs="?", type=Path, help="compact workload JSON; omitted with --self-test")
  parser.add_argument("-o", "--output", type=Path, help="write expanded scheduler JSON here")
  parser.add_argument("--estimate", action="store_true", help="also run the scheduler and print a short estimate")
  parser.add_argument("--self-test", action="store_true", help="run expansion invariants and exit")
  args = parser.parse_args()

  if args.self_test:
    _self_test()
    print("self-test passed")
    return
  if args.spec is None:
    raise SystemExit("spec is required unless --self-test is used")

  expanded = expand_spec(json.loads(args.spec.read_text()))
  text = json.dumps(expanded, indent=2, sort_keys=True) + "\n"
  if args.output is None:
    print(text, end="")
  else:
    args.output.write_text(text)

  if args.estimate:
    from microbenching.models.noc_scheduler import _transactions_from_dict  # noqa: PLC0415

    txns, cal = _transactions_from_dict(expanded)
    est = schedule(txns, cal, record_packets=False)
    print(f"estimated cycles: {est.cycles:.1f}", file=sys.stderr)
    print(f"estimated time:   {est.us:.3f} us @ {cal.clock_mhz:.1f} MHz", file=sys.stderr)
    print(f"transactions:     {len(txns)}", file=sys.stderr)


if __name__ == "__main__":
  main()
