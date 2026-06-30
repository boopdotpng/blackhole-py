#!/usr/bin/env python3
from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ttk.addrs import Core, Dram  # noqa: E402
from ttk.blackhole_coords import (  # noqa: E402
  GRID_H,
  GRID_W,
  TensixCoordinateMap,
  live_raw_tensix_cores,
  tensix_coordinate_map,
  translated_live_tensix_cores,
  translated_tensix_to_raw_noc0,
)


MAX_PACKET_BYTES = 16 * 1024
MCAST_WRITE_OPS = {"mcast_write", "multicast_write", "sem_mcast_set"}
ATOMIC_OPS = {"atomic_inc", "semaphore_inc", "sem_inc", "noc_semaphore_inc"}


def _walk_axis(start: int, stop: int, size: int, step: int):
  cur = start
  while cur != stop:
    cur = (cur + step) % size
    yield cur


def _physical_path(src: Core, dst: Core, noc: int, *, route_order: str) -> list[Core]:
  sx, sy = src
  dx, dy = dst
  if not (0 <= sx < GRID_W and 0 <= dx < GRID_W and 0 <= sy < GRID_H and 0 <= dy < GRID_H):
    raise ValueError(f"physical route coordinates must fit {GRID_W}x{GRID_H}, got {src}->{dst}")
  if route_order not in ("xy", "yx"):
    raise ValueError(f"route_order must be 'xy' or 'yx', got {route_order!r}")
  step = 1 if noc == 0 else -1
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
  return path


def _physical_path_links(src: Core, dst: Core, noc: int, *, route_order: str) -> list[tuple[Core, Core]]:
  path = _physical_path(src, dst, noc, route_order=route_order)
  return list(zip(path, path[1:]))


@dataclass(frozen=True)
class Calibration:
  """Measured constants for Blackhole P100a NoC scheduling.

  Units are NoC/AI clock cycles and bytes/cycle unless otherwise noted.
  These defaults are deliberately conservative and should be updated from
  device-specific microbench output.
  """

  clock_mhz: float = 1350.0
  max_packet_bytes: int = MAX_PACKET_BYTES
  packet_issue_cycles: float = 8.0
  packet_base_latency_cycles: float = 45.0
  hop_latency_cycles: float = 9.0
  link_bpc: float = 61.2
  l1_ingress_bpc: float = 63.1
  dram_endpoint_read_bpc: float = 47.3
  dram_endpoint_write_bpc: float = 47.3
  dram_read_noc0_bpc: float = 275.6
  dram_read_noc1_bpc: float = 164.7
  dram_write_noc0_bpc: float = 119.8
  dram_write_noc1_bpc: float = 253.6
  mcast_path_reserve_cycles: float = 18.0  # local-dir 1-receiver mcast vs unicast delta (job 091ae992)
  read_request_bytes: int = 64
  atomic_request_bytes: int = 64
  atomic_response_bytes: int = 64
  atomic_target_cycles: float = 12.0  # K=8 saturated same-target ~0.08 ops/cyc (atomic-calibration)
  niu_cmd_bufs: int = 1
  niu_total_cmd_bufs: int = 4
  cmd_buf_hold_cycles: float = 45.0
  route_order: str = "xy"

  @classmethod
  def from_dict(cls, data: dict[str, Any] | None) -> "Calibration":
    if not data:
      return cls()
    allowed = {field.name for field in cls.__dataclass_fields__.values()}
    unknown = sorted(set(data) - allowed)
    if unknown:
      raise ValueError(f"unknown calibration keys: {', '.join(unknown)}")
    return cls(**data)


@dataclass(frozen=True)
class Endpoint:
  kind: str
  coord: Core
  label: str = ""
  bank: int | None = None
  endpoint: int | None = None
  space: str = "route"

  @property
  def name(self) -> str:
    if self.label:
      return self.label
    if self.bank is not None:
      suffix = "" if self.endpoint is None else f".e{self.endpoint}"
      return f"{self.kind}.b{self.bank}{suffix}@{self.coord[0]},{self.coord[1]}"
    return f"{self.kind}@{self.coord[0]},{self.coord[1]}"

  @property
  def resource_id(self) -> str:
    if self.bank is not None:
      suffix = "" if self.endpoint is None else f".e{self.endpoint}"
      return f"{self.kind}.b{self.bank}{suffix}@{self.coord[0]},{self.coord[1]}"
    return f"{self.kind}@{self.coord[0]},{self.coord[1]}"


@dataclass(frozen=True)
class Transaction:
  name: str
  op: str
  noc: int
  initiator: Endpoint
  target: Endpoint
  bytes: int
  start_cycle: float = 0.0
  packet_bytes: int | None = None
  count: int = 1
  route_order: str | None = None
  mcast_targets: tuple[Endpoint, ...] = ()
  mcast_major: str = "x"
  path_reserve: bool = False
  vc_linked: bool = False
  cmd_buf: int | None = None
  depends_on: tuple[str, ...] = ()
  issue_stream: str = ""


@dataclass
class PacketEstimate:
  transaction: str
  packet_index: int
  noc: int
  payload_src: str
  payload_dst: str
  bytes: int
  delivered_bytes: int
  start_cycle: float
  end_cycle: float
  hops: int
  resources: list[str]
  resource_cycles: dict[str, float]
  resource_offsets: dict[str, float]
  resource_uses: dict[str, list[dict[str, float]]]

  @property
  def cycles(self) -> float:
    return self.end_cycle - self.start_cycle


@dataclass
class DependencyEdge:
  predecessor: str
  successor: str
  kind: str
  issue_stream: str = ""


@dataclass
class ScheduleEstimate:
  packets: list[PacketEstimate]
  resource_available: dict[str, float]
  slot_available: dict[str, list[float]]
  transaction_completion: dict[str, float]
  transaction_dependencies: dict[str, list[str]]
  dependency_edges: list[DependencyEdge]
  calibration: Calibration
  cycle_count: float = 0.0

  @property
  def cycles(self) -> float:
    return max(self.cycle_count, max((pkt.end_cycle for pkt in self.packets), default=0.0))

  @property
  def us(self) -> float:
    return self.cycles / self.calibration.clock_mhz

  def resource_hotspots(self, limit: int = 12) -> list[tuple[str, float]]:
    busy: dict[str, float] = {}
    for pkt in self.packets:
      for res, cycles in pkt.resource_cycles.items():
        busy[res] = busy.get(res, 0.0) + cycles
    return sorted(busy.items(), key=lambda item: item[1], reverse=True)[:limit]

  def transaction_summaries(self) -> list[dict[str, Any]]:
    grouped: dict[str, list[PacketEstimate]] = {}
    for pkt in self.packets:
      grouped.setdefault(pkt.transaction, []).append(pkt)
    out = []
    for name, pkts in grouped.items():
      start = min(pkt.start_cycle for pkt in pkts)
      end = max(pkt.end_cycle for pkt in pkts)
      cycles = end - start
      total_bytes = sum(pkt.bytes for pkt in pkts)
      delivered_bytes = sum(pkt.delivered_bytes for pkt in pkts)
      busy: dict[str, float] = {}
      for pkt in pkts:
        for res, res_cycles in pkt.resource_cycles.items():
          busy[res] = busy.get(res, 0.0) + res_cycles
      out.append({
        "transaction": name,
        "packets": len(pkts),
        "bytes": total_bytes,
        "delivered_bytes": delivered_bytes,
        "start_cycle": start,
        "end_cycle": end,
        "cycles": cycles,
        "bpc": total_bytes / cycles if cycles > 0 else 0.0,
        "delivered_bpc": delivered_bytes / cycles if cycles > 0 else 0.0,
        "hotspots": [
          {"resource": res, "busy_cycles": cycles}
          for res, cycles in sorted(busy.items(), key=lambda item: item[1], reverse=True)[:5]
        ],
      })
    return sorted(out, key=lambda row: (row["start_cycle"], row["transaction"]))


@dataclass
class _ResourceTimeline:
  calibration: Calibration
  available: dict[str, float] = field(default_factory=dict)
  slot_available: dict[str, list[float]] = field(default_factory=dict)

  def _capacity(self, name: str) -> int:
    if name.startswith("cmd_buf_pool:"):
      return self.calibration.niu_cmd_bufs
    return 1

  def _slots(self, name: str) -> list[float]:
    slots = self.slot_available.get(name)
    if slots is None:
      slots = [0.0] * self._capacity(name)
      self.slot_available[name] = slots
    return slots

  def ready_at(self, resources: dict[str, "ResourceUse | list[ResourceUse]"], earliest: float) -> float:
    t = earliest
    for name, uses in resources.items():
      capacity = self._capacity(name)
      for use in _resource_use_list(uses):
        if capacity == 1:
          t = max(t, self.available.get(name, 0.0) - use.offset)
        else:
          t = max(t, min(self._slots(name)) - use.offset)
    return t

  def reserve(self, resources: dict[str, "ResourceUse | list[ResourceUse]"], start: float):
    for name, uses in resources.items():
      capacity = self._capacity(name)
      if capacity == 1:
        current = self.available.get(name, 0.0)
        self.available[name] = max(current, *(start + use.offset + use.cycles for use in _resource_use_list(uses)))
        continue
      slots = self._slots(name)
      for use in sorted(_resource_use_list(uses), key=lambda item: item.offset):
        idx = min(range(len(slots)), key=lambda i: slots[i])
        slots[idx] = max(slots[idx], start + use.offset) + use.cycles


@dataclass(frozen=True)
class ResourceUse:
  cycles: float
  offset: float = 0.0


def _add_resource(resources: dict[str, list[ResourceUse]], name: str, use: ResourceUse):
  resources.setdefault(name, []).append(use)


def _resource_use_list(uses: ResourceUse | list[ResourceUse]) -> list[ResourceUse]:
  if isinstance(uses, ResourceUse):
    return [uses]
  return uses


def _resource_cycles_summary(resources: dict[str, ResourceUse | list[ResourceUse]]) -> dict[str, float]:
  return {name: sum(use.cycles for use in _resource_use_list(uses)) for name, uses in sorted(resources.items())}


def _resource_offsets_summary(resources: dict[str, ResourceUse | list[ResourceUse]]) -> dict[str, float]:
  return {name: min(use.offset for use in _resource_use_list(uses)) for name, uses in sorted(resources.items())}


def _resource_uses_summary(resources: dict[str, ResourceUse | list[ResourceUse]]) -> dict[str, list[dict[str, float]]]:
  return {
    name: [
      {"offset": use.offset, "cycles": use.cycles}
      for use in sorted(_resource_use_list(uses), key=lambda item: item.offset)
    ]
    for name, uses in sorted(resources.items())
  }


def _add_niu_command_resources(resources: dict[str, list[ResourceUse]], txn: Transaction, bytes_: int, cal: Calibration):
  initiator = txn.initiator.resource_id
  _add_resource(resources, f"niu:noc{txn.noc}:{initiator}", ResourceUse(_resource_cycles("niu:", bytes_, cal), 0.0))
  if txn.cmd_buf is None:
    res = f"cmd_buf_pool:noc{txn.noc}:{initiator}"
  else:
    if txn.cmd_buf < 0 or txn.cmd_buf >= cal.niu_total_cmd_bufs:
      raise ValueError(f"{txn.name}: cmd_buf must be in 0..{cal.niu_total_cmd_bufs - 1}, got {txn.cmd_buf}")
    res = f"cmd_buf:noc{txn.noc}:{initiator}:b{txn.cmd_buf}"
  _add_resource(resources, res, ResourceUse(max(cal.packet_issue_cycles, cal.cmd_buf_hold_cycles), 0.0))


@dataclass(order=True)
class _StreamState:
  sort_key: tuple[float, int]
  order: int
  txn: Transaction = field(compare=False)
  packet_bytes: int = field(compare=False)
  packets_per_rep: int = field(compare=False)
  total_packets: int = field(compare=False)
  next_packet: int = field(default=0, compare=False)

  @property
  def next_ready(self) -> float:
    return self.sort_key[0]

  @property
  def done(self) -> bool:
    return self.next_packet >= self.total_packets

  def packet_size(self) -> int:
    chunk = self.next_packet % self.packets_per_rep
    remaining = self.txn.bytes - chunk * self.packet_bytes
    return min(self.packet_bytes, remaining)

  def advance(self, next_ready: float):
    self.next_packet += 1
    self.sort_key = (next_ready, self.order)


def _coord(value: Any) -> Core:
  if not isinstance(value, (list, tuple)) or len(value) != 2:
    raise ValueError(f"coordinate must be [x, y], got {value!r}")
  return int(value[0]), int(value[1])


def _dram_endpoint_coord(bank: int, endpoint: int, harvested_dram_bank: int | None) -> Core:
  if bank < 0 or bank >= Dram.BANK_COUNT:
    raise ValueError(f"bank must be in 0..{Dram.BANK_COUNT - 1}, got {bank}")
  if endpoint < 0 or endpoint >= Dram.TILES_PER_BANK:
    raise ValueError(f"endpoint must be in 0..{Dram.TILES_PER_BANK - 1}, got {endpoint}")
  # The programmed DRAM bank table may expose translated endpoint coordinates
  # like x=17/18,y>=12. Those are not useful for route distance/contention.
  # The scheduler uses the physical DRAM router tile for the logical bank.
  physical_bank = bank
  if harvested_dram_bank is not None and bank >= harvested_dram_bank:
    physical_bank = bank + 1
  return Dram.BANK_X[physical_bank], Dram.BANK_TILE_YS[physical_bank][endpoint]


def _endpoint_from_dict(
  data: dict[str, Any],
  *,
  harvested_dram_bank: int | None,
  coord_map: TensixCoordinateMap | None,
) -> Endpoint:
  kind = str(data.get("kind", "l1"))
  space = str(data.get("space", "route"))
  bank = data.get("bank")
  endpoint = data.get("endpoint")

  if kind == "dram" and "coord" not in data:
    if bank is None:
      raise ValueError("dram endpoints need either coord or bank")
    endpoint_i = int(0 if endpoint is None else endpoint)
    coord = _dram_endpoint_coord(int(bank), endpoint_i, harvested_dram_bank)
    return Endpoint(kind=kind, coord=coord, label=str(data.get("label", "")), bank=int(bank), endpoint=endpoint_i, space="route")

  coord = _coord(data["coord"])
  if space == "translated_tensix_noc0":
    if coord_map is None:
      raise ValueError("translated_tensix_noc0 endpoint requires enabled_tensix_col in the spec")
    coord = translated_tensix_to_raw_noc0(coord, coord_map)
    space = "route"
  elif space != "route":
    raise ValueError(f"unknown endpoint coordinate space {space!r}")

  return Endpoint(
    kind=kind,
    coord=coord,
    label=str(data.get("label", "")),
    bank=None if bank is None else int(bank),
    endpoint=None if endpoint is None else int(endpoint),
    space=space,
  )


def _is_mcast_op(op: str) -> bool:
  return op.lower() in MCAST_WRITE_OPS


def _is_atomic_op(op: str) -> bool:
  return op.lower() in ATOMIC_OPS


def _string_tuple(value: Any) -> tuple[str, ...]:
  if value is None:
    return ()
  if isinstance(value, str):
    return (value,)
  if isinstance(value, (list, tuple)):
    return tuple(str(item) for item in value)
  raise ValueError(f"expected string or list of strings, got {value!r}")


def _rect_targets_from_dict(
  data: Any,
  *,
  harvested_dram_bank: int | None,
  coord_map: TensixCoordinateMap | None,
) -> tuple[Endpoint, ...]:
  if isinstance(data, dict):
    if "x0" in data:
      x0, y0, x1, y1 = int(data["x0"]), int(data["y0"]), int(data["x1"]), int(data["y1"])
    elif "start" in data and "end" in data:
      x0, y0 = _coord(data["start"])
      x1, y1 = _coord(data["end"])
    else:
      raise ValueError("rect must contain x0/y0/x1/y1 or start/end")
    kind = str(data.get("kind", "l1"))
    space = str(data.get("space", "route"))
    label = str(data.get("label", "mcast"))
  elif isinstance(data, (list, tuple)) and len(data) == 4:
    x0, y0, x1, y1 = (int(v) for v in data)
    kind = "l1"
    space = "route"
    label = "mcast"
  else:
    raise ValueError(f"rect must be an object or [x0, y0, x1, y1], got {data!r}")

  if x1 < x0 or y1 < y0:
    raise ValueError(f"multicast rectangles must be non-wrapping and ordered, got {(x0, y0, x1, y1)}")

  targets = []
  for y in range(y0, y1 + 1):
    for x in range(x0, x1 + 1):
      targets.append(_endpoint_from_dict(
        {"kind": kind, "space": space, "coord": [x, y], "label": f"{label}@{x},{y}"},
        harvested_dram_bank=harvested_dram_bank,
        coord_map=coord_map,
      ))
  return tuple(targets)


def _transactions_from_dict(spec: dict[str, Any]) -> tuple[list[Transaction], Calibration]:
  cal = Calibration.from_dict(spec.get("calibration"))
  harvested_dram_bank = spec.get("harvested_dram_bank")
  if harvested_dram_bank is not None:
    harvested_dram_bank = int(harvested_dram_bank)
  enabled_tensix_col = spec.get("enabled_tensix_col")
  coord_map = None if enabled_tensix_col is None else tensix_coordinate_map(int(enabled_tensix_col))

  txns = []
  for i, item in enumerate(spec.get("transactions", [])):
    op = str(item["op"])
    initiator = _endpoint_from_dict(item["initiator"], harvested_dram_bank=harvested_dram_bank, coord_map=coord_map)
    mcast_targets: tuple[Endpoint, ...] = ()
    if _is_mcast_op(op):
      if "targets" in item:
        mcast_targets = tuple(
          _endpoint_from_dict(target, harvested_dram_bank=harvested_dram_bank, coord_map=coord_map)
          for target in item["targets"]
        )
      elif "rect" in item:
        mcast_targets = _rect_targets_from_dict(
          item["rect"],
          harvested_dram_bank=harvested_dram_bank,
          coord_map=coord_map,
        )
      elif "target_rect" in item:
        mcast_targets = _rect_targets_from_dict(
          item["target_rect"],
          harvested_dram_bank=harvested_dram_bank,
          coord_map=coord_map,
        )
      if not mcast_targets and "target" not in item:
        raise ValueError(f"{item.get('name', f'txn{i}')}: multicast transaction needs target, targets, or rect")

    target = _endpoint_from_dict(item["target"], harvested_dram_bank=harvested_dram_bank, coord_map=coord_map) if "target" in item else mcast_targets[0]
    if _is_mcast_op(op) and not mcast_targets:
      mcast_targets = (target,)
    default_bytes = 4 if _is_atomic_op(op) else None
    if default_bytes is None and "bytes" not in item:
      raise ValueError(f"{item.get('name', f'txn{i}')}: transaction needs bytes")
    txns.append(Transaction(
      name=str(item.get("name", f"txn{i}")),
      op=op,
      noc=int(item.get("noc", 0)),
      initiator=initiator,
      target=target,
      bytes=int(item.get("bytes", default_bytes)),
      start_cycle=float(item.get("start_cycle", 0.0)),
      packet_bytes=None if item.get("packet_bytes") is None else int(item["packet_bytes"]),
      count=int(item.get("count", 1)),
      route_order=None if item.get("route_order") is None else str(item["route_order"]),
      mcast_targets=mcast_targets,
      mcast_major=str(item.get("mcast_major", item.get("major", "x"))),
      path_reserve=bool(item.get("path_reserve", False)),
      vc_linked=bool(item.get("vc_linked", False)),
      cmd_buf=None if item.get("cmd_buf") is None else int(item["cmd_buf"]),
      depends_on=_string_tuple(item.get("depends_on")),
      issue_stream=str(item.get("issue_stream", item.get("stream", "")) or ""),
    ))
  return txns, cal


def payload_endpoints(txn: Transaction) -> tuple[Endpoint, Endpoint]:
  """Return the dominant payload route for the transaction.

  For NoC reads, the requester sends a small command and the payload returns
  from target to initiator. `packet_resources` models the request leg as a
  small one-flit path and uses this helper only for the dominant payload route.
  """

  op = txn.op.lower()
  if op in ("write", "l1_write", "dram_write"):
    return txn.initiator, txn.target
  if op in ("read", "l1_read", "dram_read"):
    return txn.target, txn.initiator
  raise ValueError(f"unknown op {txn.op!r}")


def _mcast_route_order(txn: Transaction, cal: Calibration) -> str:
  if txn.route_order is not None:
    return txn.route_order
  major = txn.mcast_major.lower()
  if major == "x":
    return "xy"
  if major == "y":
    return "yx"
  raise ValueError(f"{txn.name}: multicast major must be 'x' or 'y', got {txn.mcast_major!r}")


def _mcast_tree_links(
  src: Core,
  targets: tuple[Endpoint, ...],
  noc: int,
  *,
  route_order: str,
) -> tuple[dict[tuple[Core, Core], int], int]:
  """Approximate a multicast tree as the union of major-axis physical paths.

  Hardware multicast is not N independent unicasts: shared trunk links carry
  the source payload once, then routers fan out. The exact router tree is still
  being inferred, so the scheduler uses the union of per-receiver major-axis
  paths as a conservative first-order tree. Link offsets use the earliest hop
  where that link appears in any receiver path.
  """

  link_hops: dict[tuple[Core, Core], int] = {}
  max_hops = 0
  for target in targets:
    links = _physical_path_links(src, target.coord, noc, route_order=route_order)
    max_hops = max(max_hops, len(links))
    for hop_i, link in enumerate(links):
      if link not in link_hops or hop_i < link_hops[link]:
        link_hops[link] = hop_i
  return link_hops, max_hops


def _resource_cycles(name: str, bytes_: int, cal: Calibration) -> float:
  if name.startswith("niu:"):
    return cal.packet_issue_cycles
  if name.startswith("link:"):
    return bytes_ / cal.link_bpc
  if name.startswith("l1_in:"):
    return bytes_ / cal.l1_ingress_bpc
  if name.startswith("dram_read:"):
    return bytes_ / cal.dram_endpoint_read_bpc
  if name.startswith("dram_write:"):
    return bytes_ / cal.dram_endpoint_write_bpc
  if name.startswith("dram_read_fabric:noc0"):
    return bytes_ / cal.dram_read_noc0_bpc
  if name.startswith("dram_read_fabric:noc1"):
    return bytes_ / cal.dram_read_noc1_bpc
  if name.startswith("dram_write_fabric:noc0"):
    return bytes_ / cal.dram_write_noc0_bpc
  if name.startswith("dram_write_fabric:noc1"):
    return bytes_ / cal.dram_write_noc1_bpc
  if name.startswith("mcast_path_reserve:"):
    return cal.mcast_path_reserve_cycles
  if name.startswith("atomic_target:"):
    return cal.atomic_target_cycles
  raise ValueError(f"no bandwidth calibration for resource {name!r}")


def packet_resources(txn: Transaction, bytes_: int, cal: Calibration) -> tuple[dict[str, list[ResourceUse]], Endpoint, Endpoint, int]:
  if _is_atomic_op(txn.op):
    if txn.target.kind != "l1":
      raise ValueError(f"{txn.name}: atomic/semaphore targets must be L1 endpoints")
    route_order = txn.route_order or cal.route_order
    resources: dict[str, list[ResourceUse]] = {}
    _add_niu_command_resources(resources, txn, bytes_, cal)

    req_links = _physical_path_links(txn.initiator.coord, txn.target.coord, txn.noc, route_order=route_order)
    for hop_i, (a, b) in enumerate(req_links):
      res = f"link:noc{txn.noc}:{a[0]},{a[1]}->{b[0]},{b[1]}"
      _add_resource(resources, res, ResourceUse(_resource_cycles("link:", cal.atomic_request_bytes, cal), hop_i * cal.hop_latency_cycles))

    target_offset = len(req_links) * cal.hop_latency_cycles
    target_res = f"atomic_target:{txn.target.resource_id}"
    _add_resource(resources, target_res, ResourceUse(_resource_cycles(target_res, bytes_, cal), target_offset))

    resp_links = _physical_path_links(txn.target.coord, txn.initiator.coord, txn.noc, route_order=route_order)
    response_offset = target_offset + cal.atomic_target_cycles
    for hop_i, (a, b) in enumerate(resp_links):
      res = f"link:noc{txn.noc}:{a[0]},{a[1]}->{b[0]},{b[1]}"
      offset = response_offset + hop_i * cal.hop_latency_cycles
      _add_resource(resources, res, ResourceUse(_resource_cycles("link:", cal.atomic_response_bytes, cal), offset))

    resp_res = f"atomic_resp_in:{txn.initiator.resource_id}"
    _add_resource(resources, resp_res, ResourceUse(
      _resource_cycles("l1_in:", cal.atomic_response_bytes, cal),
      response_offset + len(resp_links) * cal.hop_latency_cycles,
    ))
    return resources, txn.initiator, txn.initiator, len(req_links) + len(resp_links)

  if _is_mcast_op(txn.op):
    if not txn.mcast_targets:
      raise ValueError(f"{txn.name}: multicast transaction has no targets")
    if any(target.kind != "l1" for target in txn.mcast_targets):
      raise ValueError(f"{txn.name}: multicast targets must be L1 endpoints")

    route_order = _mcast_route_order(txn, cal)
    resources: dict[str, list[ResourceUse]] = {}
    _add_niu_command_resources(resources, txn, bytes_, cal)
    if txn.path_reserve:
      res = f"mcast_path_reserve:noc{txn.noc}"
      _add_resource(resources, res, ResourceUse(_resource_cycles(res, bytes_, cal), 0.0))

    link_hops, max_hops = _mcast_tree_links(txn.initiator.coord, txn.mcast_targets, txn.noc, route_order=route_order)
    for (a, b), hop_i in sorted(link_hops.items(), key=lambda item: (item[1], item[0])):
      res = f"link:noc{txn.noc}:{a[0]},{a[1]}->{b[0]},{b[1]}"
      _add_resource(resources, res, ResourceUse(_resource_cycles("link:", bytes_, cal), hop_i * cal.hop_latency_cycles))

    for target in txn.mcast_targets:
      path = _physical_path(txn.initiator.coord, target.coord, txn.noc, route_order=route_order)
      res = f"l1_in:{target.resource_id}"
      _add_resource(resources, res, ResourceUse(_resource_cycles("l1_in:", bytes_, cal), (len(path) - 1) * cal.hop_latency_cycles))

    dst = Endpoint("mcast", txn.initiator.coord, label=f"mcast[{len(txn.mcast_targets)}]")
    return resources, txn.initiator, dst, max_hops

  src, dst = payload_endpoints(txn)
  route_order = txn.route_order or cal.route_order
  resources: dict[str, list[ResourceUse]] = {}
  _add_niu_command_resources(resources, txn, bytes_, cal)

  payload_offset = 0.0
  if txn.op.lower() in ("read", "l1_read", "dram_read"):
    request_links = _physical_path_links(txn.initiator.coord, txn.target.coord, txn.noc, route_order=route_order)
    for hop_i, (a, b) in enumerate(request_links):
      res = f"link:noc{txn.noc}:{a[0]},{a[1]}->{b[0]},{b[1]}"
      _add_resource(resources, res, ResourceUse(_resource_cycles("link:", cal.read_request_bytes, cal), hop_i * cal.hop_latency_cycles))
    payload_offset = len(request_links) * cal.hop_latency_cycles

  links = _physical_path_links(src.coord, dst.coord, txn.noc, route_order=route_order)
  for hop_i, (a, b) in enumerate(links):
    res = f"link:noc{txn.noc}:{a[0]},{a[1]}->{b[0]},{b[1]}"
    _add_resource(resources, res, ResourceUse(_resource_cycles("link:", bytes_, cal), payload_offset + hop_i * cal.hop_latency_cycles))

  if dst.kind == "l1":
    res = f"l1_in:{dst.resource_id}"
    _add_resource(resources, res, ResourceUse(_resource_cycles("l1_in:", bytes_, cal), payload_offset + len(links) * cal.hop_latency_cycles))
  elif dst.kind == "dram":
    res = f"dram_write:{dst.resource_id}"
    _add_resource(resources, res, ResourceUse(_resource_cycles("dram_write:", bytes_, cal), payload_offset + len(links) * cal.hop_latency_cycles))
    fabric = f"dram_write_fabric:noc{txn.noc}"
    _add_resource(resources, fabric, ResourceUse(_resource_cycles(fabric, bytes_, cal), 0.0))

  if src.kind == "dram":
    res = f"dram_read:{src.resource_id}"
    _add_resource(resources, res, ResourceUse(_resource_cycles("dram_read:", bytes_, cal), payload_offset))
    fabric = f"dram_read_fabric:noc{txn.noc}"
    _add_resource(resources, fabric, ResourceUse(_resource_cycles(fabric, bytes_, cal), payload_offset))

  request_hops = int(payload_offset / cal.hop_latency_cycles) if cal.hop_latency_cycles > 0 else 0
  return resources, src, dst, request_hops + len(links)


def schedule(
  transactions: list[Transaction],
  cal: Calibration | None = None,
  *,
  record_packets: bool = True,
) -> ScheduleEstimate:
  cal = cal or Calibration()
  if cal.niu_cmd_bufs <= 0:
    raise ValueError(f"niu_cmd_bufs must be positive, got {cal.niu_cmd_bufs}")
  if cal.niu_total_cmd_bufs <= 0:
    raise ValueError(f"niu_total_cmd_bufs must be positive, got {cal.niu_total_cmd_bufs}")
  if cal.cmd_buf_hold_cycles < 0:
    raise ValueError(f"cmd_buf_hold_cycles must be non-negative, got {cal.cmd_buf_hold_cycles}")
  timelines = _ResourceTimeline(calibration=cal)
  packets: list[PacketEstimate] = []
  cycle_count = 0.0
  transaction_completion: dict[str, float] = {}
  dependents: dict[str, list[_StreamState]] = {}
  remaining_deps: dict[int, set[str]] = {}
  candidate_heap: list[tuple[float, int, int, _StreamState]] = []
  resource_cache: dict[tuple[int, int], tuple[dict[str, list[ResourceUse]], Endpoint, Endpoint, int]] = {}
  candidate_serial = 0

  seen_names: set[str] = set()
  duplicate_names: set[str] = set()
  for txn in transactions:
    if txn.name in seen_names:
      duplicate_names.add(txn.name)
    seen_names.add(txn.name)
  if duplicate_names:
    raise ValueError(f"transaction names must be unique, duplicates: {', '.join(sorted(duplicate_names))}")
  name_set = seen_names

  deps_by_order: list[set[str]] = [set(txn.depends_on) for txn in transactions]
  dependency_edges: list[DependencyEdge] = []
  for txn in transactions:
    for dep in txn.depends_on:
      dependency_edges.append(DependencyEdge(dep, txn.name, "explicit"))
  previous_in_stream: dict[str, str] = {}
  for order, txn in enumerate(transactions):
    if not txn.issue_stream:
      continue
    if txn.issue_stream in previous_in_stream:
      predecessor = previous_in_stream[txn.issue_stream]
      deps_by_order[order].add(predecessor)
      dependency_edges.append(DependencyEdge(predecessor, txn.name, "issue_stream", txn.issue_stream))
    previous_in_stream[txn.issue_stream] = txn.name
  transaction_dependencies = {
    txn.name: sorted(deps)
    for txn, deps in zip(transactions, deps_by_order, strict=True)
  }

  def candidate_for(state: _StreamState) -> tuple[float, int, int, _StreamState]:
    nonlocal candidate_serial
    n = state.packet_size()
    cache_key = (state.order, n)
    if cache_key not in resource_cache:
      resource_cache[cache_key] = packet_resources(state.txn, n, cal)
    resources, _src, _dst, _hops = resource_cache[cache_key]
    start = timelines.ready_at(resources, state.next_ready)
    candidate_serial += 1
    return (start, state.order, candidate_serial, state)

  for order, txn in enumerate(transactions):
    if txn.noc not in (0, 1):
      raise ValueError(f"{txn.name}: noc must be 0 or 1")
    if txn.bytes <= 0:
      raise ValueError(f"{txn.name}: bytes must be positive")
    if txn.count <= 0:
      raise ValueError(f"{txn.name}: count must be positive")
    packet_bytes = txn.packet_bytes or cal.max_packet_bytes
    if packet_bytes <= 0 or packet_bytes > cal.max_packet_bytes:
      raise ValueError(f"{txn.name}: packet_bytes must be in 1..{cal.max_packet_bytes}")
    packets_per_rep = math.ceil(txn.bytes / packet_bytes)
    total_packets = packets_per_rep * txn.count
    state = _StreamState(
      sort_key=(txn.start_cycle, order),
      order=order,
      txn=txn,
      packet_bytes=packet_bytes,
      packets_per_rep=packets_per_rep,
      total_packets=total_packets,
    )
    deps = deps_by_order[order]
    if txn.name in deps:
      raise ValueError(f"{txn.name}: transaction cannot depend on itself")
    unknown_deps = sorted(deps - name_set)
    if unknown_deps:
      raise ValueError(f"{txn.name}: unknown dependencies: {', '.join(unknown_deps)}")
    remaining_deps[order] = set(deps)
    for dep in deps:
      dependents.setdefault(dep, []).append(state)
    if not deps:
      heapq.heappush(candidate_heap, candidate_for(state))

  while candidate_heap:
    candidate_start, _order, _serial, state = heapq.heappop(candidate_heap)
    txn = state.txn
    n = state.packet_size()
    cache_key = (state.order, n)
    resources, src, dst, hops = resource_cache[cache_key]
    start = timelines.ready_at(resources, state.next_ready)
    if start > candidate_start:
      heapq.heappush(candidate_heap, candidate_for(state))
      continue

    timelines.reserve(resources, start)
    pipe_cycles = max(
      (use.offset + use.cycles for uses in resources.values() for use in _resource_use_list(uses)),
      default=0.0,
    )
    end = start + cal.packet_base_latency_cycles + pipe_cycles
    cycle_count = max(cycle_count, end)
    if record_packets:
      packets.append(PacketEstimate(
        transaction=txn.name,
        packet_index=state.next_packet,
        noc=txn.noc,
        payload_src=src.name,
        payload_dst=dst.name,
        bytes=n,
        delivered_bytes=n * len(txn.mcast_targets) if _is_mcast_op(txn.op) else n,
        start_cycle=start,
        end_cycle=end,
        hops=hops,
        resources=sorted(resources),
        resource_cycles=_resource_cycles_summary(resources),
        resource_offsets=_resource_offsets_summary(resources),
        resource_uses=_resource_uses_summary(resources),
    ))
    state.advance(start + cal.packet_issue_cycles)
    if not state.done:
      heapq.heappush(candidate_heap, candidate_for(state))
    else:
      transaction_completion[txn.name] = end
      for waiting in dependents.get(txn.name, ()):
        deps = remaining_deps[waiting.order]
        deps.discard(txn.name)
        waiting.sort_key = (max(waiting.next_ready, end), waiting.order)
        if not deps:
          heapq.heappush(candidate_heap, candidate_for(waiting))

  if len(transaction_completion) != len(transactions):
    waiting = {
      transactions[order].name: sorted(deps)
      for order, deps in remaining_deps.items()
      if deps
    }
    raise ValueError(f"dependency cycle or unsatisfied dependency: {waiting}")

  return ScheduleEstimate(
    packets=packets,
    resource_available=dict(timelines.available),
    slot_available={name: list(slots) for name, slots in timelines.slot_available.items()},
    transaction_completion=transaction_completion,
    transaction_dependencies=transaction_dependencies,
    dependency_edges=dependency_edges,
    calibration=cal,
    cycle_count=cycle_count,
  )


def estimate_to_dict(est: ScheduleEstimate) -> dict[str, Any]:
  return {
    "cycles": est.cycles,
    "us": est.us,
    "packet_count": len(est.packets),
    "hotspots": [{"resource": name, "busy_score_cycles": cycles} for name, cycles in est.resource_hotspots()],
    "slot_available": est.slot_available,
    "transaction_completion": est.transaction_completion,
    "transaction_dependencies": est.transaction_dependencies,
    "dependency_edges": [
      {
        "predecessor": edge.predecessor,
        "successor": edge.successor,
        "kind": edge.kind,
        "issue_stream": edge.issue_stream,
      }
      for edge in est.dependency_edges
    ],
    "transactions": est.transaction_summaries(),
    "packets": [
      {
        "transaction": pkt.transaction,
        "packet_index": pkt.packet_index,
        "noc": pkt.noc,
        "payload_src": pkt.payload_src,
        "payload_dst": pkt.payload_dst,
        "bytes": pkt.bytes,
        "delivered_bytes": pkt.delivered_bytes,
        "start_cycle": pkt.start_cycle,
        "end_cycle": pkt.end_cycle,
        "hops": pkt.hops,
        "resources": pkt.resources,
        "resource_cycles": pkt.resource_cycles,
        "resource_offsets": pkt.resource_offsets,
        "resource_uses": pkt.resource_uses,
      }
      for pkt in est.packets
    ],
  }


def _demo_spec() -> dict[str, Any]:
  return {
    "calibration": {},
    "transactions": [
      {
        "name": "dram-read-b0-to-core",
        "op": "read",
        "noc": 0,
        "bytes": 1024 * 1024,
        "route_order": "xy",
        "initiator": {"kind": "l1", "coord": [1, 2], "label": "core1,2"},
        "target": {"kind": "dram", "bank": 0, "endpoint": 2},
      },
      {
        "name": "dram-write-core-to-b0",
        "op": "write",
        "noc": 1,
        "bytes": 1024 * 1024,
        "route_order": "yx",
        "initiator": {"kind": "l1", "coord": [1, 2], "label": "core1,2"},
        "target": {"kind": "dram", "bank": 0, "endpoint": 1},
      },
      {
        "name": "sem-inc-core-to-core",
        "op": "semaphore_inc",
        "noc": 0,
        "count": 8,
        "initiator": {"kind": "l1", "coord": [1, 2], "label": "core1,2"},
        "target": {"kind": "l1", "coord": [4, 2], "label": "sem-owner"},
      },
    ],
  }


def _self_test():
  cal = Calibration()
  packet_bytes = cal.max_packet_bytes
  single = schedule([
    Transaction("single", "write", 0, Endpoint("l1", (1, 2), "a"), Endpoint("l1", (2, 2), "b"), packet_bytes * 4),
  ], cal)
  disjoint = schedule([
    Transaction("a", "write", 0, Endpoint("l1", (1, 2), "a0"), Endpoint("l1", (2, 2), "a1"), packet_bytes * 4),
    Transaction("b", "write", 0, Endpoint("l1", (4, 2), "b0"), Endpoint("l1", (5, 2), "b1"), packet_bytes * 4),
  ], cal)
  assert abs(disjoint.cycles - single.cycles) < 1e-6, (disjoint.cycles, single.cycles)

  dependent = schedule([
    Transaction("dep-a", "write", 0, Endpoint("l1", (1, 2), "da0"), Endpoint("l1", (2, 2), "da1"), packet_bytes),
    Transaction("dep-b", "write", 0, Endpoint("l1", (4, 2), "db0"), Endpoint("l1", (5, 2), "db1"), packet_bytes, depends_on=("dep-a",)),
  ], cal)
  dep_b_start = min(pkt.start_cycle for pkt in dependent.packets if pkt.transaction == "dep-b")
  assert dep_b_start >= dependent.transaction_completion["dep-a"]
  assert dependent.cycles > schedule([
    Transaction("free-a", "write", 0, Endpoint("l1", (1, 2), "fa0"), Endpoint("l1", (2, 2), "fa1"), packet_bytes),
    Transaction("free-b", "write", 0, Endpoint("l1", (4, 2), "fb0"), Endpoint("l1", (5, 2), "fb1"), packet_bytes),
  ], cal).cycles

  stream_ordered = schedule([
    Transaction("stream-a", "write", 0, Endpoint("l1", (1, 2), "sa0"), Endpoint("l1", (2, 2), "sa1"), packet_bytes, issue_stream="risc0"),
    Transaction("stream-b", "write", 0, Endpoint("l1", (4, 2), "sb0"), Endpoint("l1", (5, 2), "sb1"), packet_bytes, issue_stream="risc0"),
  ], cal)
  stream_b_start = min(pkt.start_cycle for pkt in stream_ordered.packets if pkt.transaction == "stream-b")
  assert stream_b_start >= stream_ordered.transaction_completion["stream-a"]
  assert stream_ordered.transaction_dependencies["stream-b"] == ["stream-a"]
  assert any(
    edge.predecessor == "stream-a"
    and edge.successor == "stream-b"
    and edge.kind == "issue_stream"
    and edge.issue_stream == "risc0"
    for edge in stream_ordered.dependency_edges
  )
  stream_parallel = schedule([
    Transaction("stream-free-a", "write", 0, Endpoint("l1", (1, 2), "sfa0"), Endpoint("l1", (2, 2), "sfa1"), packet_bytes, issue_stream="risc0"),
    Transaction("stream-free-b", "write", 0, Endpoint("l1", (4, 2), "sfb0"), Endpoint("l1", (5, 2), "sfb1"), packet_bytes, issue_stream="risc1"),
  ], cal)
  assert stream_ordered.cycles > stream_parallel.cycles

  try:
    schedule([
      Transaction("cycle-a", "write", 0, Endpoint("l1", (1, 2), "ca0"), Endpoint("l1", (2, 2), "ca1"), 4, depends_on=("cycle-b",)),
      Transaction("cycle-b", "write", 0, Endpoint("l1", (4, 2), "cb0"), Endpoint("l1", (5, 2), "cb1"), 4, depends_on=("cycle-a",)),
    ], cal)
  except ValueError as exc:
    assert "dependency cycle" in str(exc)
  else:
    raise AssertionError("dependency cycle was not rejected")

  shared = schedule([
    Transaction(f"w{i}", "write", 0, Endpoint("l1", (1 + i, 2), f"s{i}"), Endpoint("l1", (10, 2), "dst"), packet_bytes * 2)
    for i in range(4)
  ], cal)
  assert sorted({pkt.transaction for pkt in shared.packets}) == ["w0", "w1", "w2", "w3"]
  assert shared.cycles > single.cycles * 1.5
  assert any(name == "l1_in:l1@10,2" for name, _cycles in shared.resource_hotspots(8))

  alias_cal = Calibration(
    packet_issue_cycles=1.0,
    packet_base_latency_cycles=0.0,
    hop_latency_cycles=0.0,
    link_bpc=1e9,
    l1_ingress_bpc=64.0,
    cmd_buf_hold_cycles=1.0,
  )
  same_target_different_labels = schedule([
    Transaction("alias-a", "write", 0, Endpoint("l1", (1, 2), "alias-src-a"), Endpoint("l1", (10, 2), "alias-dst-a"), packet_bytes * 2),
    Transaction("alias-b", "write", 0, Endpoint("l1", (1, 3), "alias-src-b"), Endpoint("l1", (10, 2), "alias-dst-b"), packet_bytes * 2),
  ], alias_cal)
  different_targets = schedule([
    Transaction("alias-free-a", "write", 0, Endpoint("l1", (1, 2), "alias-free-src-a"), Endpoint("l1", (10, 2), "alias-free-dst-a"), packet_bytes * 2),
    Transaction("alias-free-b", "write", 0, Endpoint("l1", (1, 3), "alias-free-src-b"), Endpoint("l1", (10, 3), "alias-free-dst-b"), packet_bytes * 2),
  ], alias_cal)
  assert same_target_different_labels.cycles > different_targets.cycles * 1.5
  assert any(name == "l1_in:l1@10,2" for name, _cycles in same_target_different_labels.resource_hotspots(8))

  cmd_cal = Calibration(
    packet_issue_cycles=1.0,
    packet_base_latency_cycles=0.0,
    hop_latency_cycles=1.0,
    link_bpc=1e9,
    l1_ingress_bpc=1e9,
    niu_cmd_bufs=2,
    cmd_buf_hold_cycles=20.0,
  )
  cmd_src = Endpoint("l1", (1, 2), "cmd-src")
  cmd_pool = schedule([
    Transaction("cmd-pool", "write", 0, cmd_src, cmd_src, 4, count=5),
  ], cmd_cal)
  assert [pkt.start_cycle for pkt in cmd_pool.packets] == [0.0, 1.0, 20.0, 21.0, 40.0]
  assert "cmd_buf_pool:noc0:l1@1,2" in cmd_pool.slot_available

  cmd_one = schedule([
    Transaction("cmd-one", "write", 0, cmd_src, cmd_src, 4, count=3, cmd_buf=0),
  ], cmd_cal)
  assert [pkt.start_cycle for pkt in cmd_one.packets] == [0.0, 20.0, 40.0]
  assert any("cmd_buf:noc0:l1@1,2:b0" in pkt.resources for pkt in cmd_one.packets)

  read_txn = Transaction("read", "read", 0, Endpoint("l1", (1, 2), "reader"), Endpoint("dram", (0, 11), bank=0, endpoint=2), packet_bytes)
  resources, src, dst, hops = packet_resources(read_txn, packet_bytes, cal)
  assert src.kind == "dram" and dst.kind == "l1" and hops > 0
  assert any(name.startswith("dram_read:") for name in resources)
  assert "dram_read_fabric:noc0" in resources
  assert any(name.startswith("l1_in:") for name in resources)
  assert "link:noc0:1,2->2,2" in resources  # request leg from reader toward DRAM
  assert "link:noc0:0,11->1,11" in resources  # payload leg from DRAM toward reader
  read_est = schedule([read_txn], cal)
  read_pkt = read_est.packets[0]
  assert read_pkt.resource_offsets["dram_read:dram.b0.e2@0,11"] > 0
  assert read_pkt.resource_uses["dram_read:dram.b0.e2@0,11"][0]["offset"] == read_pkt.resource_offsets["dram_read:dram.b0.e2@0,11"]

  write_txn = Transaction("write", "write", 1, Endpoint("l1", (1, 2), "writer"), Endpoint("dram", (0, 1), bank=0, endpoint=1), packet_bytes)
  resources, src, dst, hops = packet_resources(write_txn, packet_bytes, cal)
  assert src.kind == "l1" and dst.kind == "dram" and hops > 0
  assert any(name.startswith("dram_write:") for name in resources)
  assert "dram_write_fabric:noc1" in resources

  mcast_txn = Transaction(
    "mcast",
    "mcast_write",
    0,
    Endpoint("l1", (1, 2), "sender"),
    Endpoint("l1", (3, 2), "r0"),
    packet_bytes,
    mcast_targets=(Endpoint("l1", (3, 2), "r0"), Endpoint("l1", (3, 3), "r1")),
    mcast_major="x",
  )
  resources, src, dst, hops = packet_resources(mcast_txn, packet_bytes, cal)
  assert src.name == "sender" and dst.name == "mcast[2]" and hops == 3
  assert "link:noc0:1,2->2,2" in resources
  assert "link:noc0:2,2->3,2" in resources
  assert "link:noc0:3,2->3,3" in resources
  assert len([name for name in resources if name.startswith("l1_in:")]) == 2
  est = schedule([mcast_txn], cal)
  assert est.transaction_summaries()[0]["delivered_bytes"] == packet_bytes * 2

  atomic_txn = Transaction(
    "atomic",
    "atomic_inc",
    0,
    Endpoint("l1", (1, 2), "atomic-src"),
    Endpoint("l1", (4, 2), "atomic-dst"),
    4,
    count=3,
  )
  resources, src, dst, hops = packet_resources(atomic_txn, 4, cal)
  assert src.name == "atomic-src" and dst.name == "atomic-src" and hops > 0
  assert "atomic_target:l1@4,2" in resources
  assert "atomic_resp_in:l1@1,2" in resources
  assert any(name.startswith("link:noc0:") for name in resources)
  est = schedule([atomic_txn], cal)
  assert len(est.packets) == 3

  atomic_spec = {
    "transactions": [{
      "name": "atomic-default-bytes",
      "op": "semaphore_inc",
      "noc": 0,
      "count": 2,
      "initiator": {"kind": "l1", "coord": [1, 2], "label": "src"},
      "target": {"kind": "l1", "coord": [2, 2], "label": "dst"},
    }],
  }
  txns, _ = _transactions_from_dict(atomic_spec)
  assert txns[0].bytes == 4 and txns[0].count == 2

  dep_spec = {
    "transactions": [
      {
        "name": "json-a",
        "op": "write",
        "noc": 0,
        "bytes": 4,
        "initiator": {"kind": "l1", "coord": [1, 2]},
        "target": {"kind": "l1", "coord": [2, 2]},
      },
      {
        "name": "json-b",
        "op": "write",
        "noc": 0,
        "bytes": 4,
        "depends_on": "json-a",
        "issue_stream": "json-risc0",
        "initiator": {"kind": "l1", "coord": [4, 2]},
        "target": {"kind": "l1", "coord": [5, 2]},
      },
      {
        "name": "json-c",
        "op": "write",
        "noc": 0,
        "bytes": 4,
        "depends_on": ["json-a", "json-b"],
        "stream": "json-risc0",
        "initiator": {"kind": "l1", "coord": [7, 2]},
        "target": {"kind": "l1", "coord": [8, 2]},
      },
    ],
  }
  txns, _ = _transactions_from_dict(dep_spec)
  assert txns[1].depends_on == ("json-a",)
  assert txns[2].depends_on == ("json-a", "json-b")
  assert txns[1].issue_stream == "json-risc0"
  assert txns[2].issue_stream == "json-risc0"

  spec = {
    "enabled_tensix_col": 15351,
    "transactions": [{
      "name": "harvested",
      "op": "write",
      "noc": 0,
      "bytes": packet_bytes,
      "initiator": {"kind": "l1", "space": "translated_tensix_noc0", "coord": [6, 2], "label": "friendly6"},
      "target": {"kind": "l1", "coord": [10, 2], "label": "target"},
    }],
  }
  txns, _ = _transactions_from_dict(spec)
  assert txns[0].initiator.coord == (7, 2)

  cmap = tensix_coordinate_map(15351)
  assert cmap.harvested_raw_x == (6, 15)
  assert cmap.live_raw_x == (1, 2, 3, 4, 5, 7, 10, 11, 12, 13, 14, 16)
  assert cmap.translated_live_x == (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14)
  assert translated_tensix_to_raw_noc0((6, 2), cmap) == (7, 2)
  assert translated_tensix_to_raw_noc0((14, 2), cmap) == (16, 2)
  assert (6, 2) not in live_raw_tensix_cores(cmap)
  assert (15, 2) not in live_raw_tensix_cores(cmap)
  assert (6, 2) in translated_live_tensix_cores(cmap)


def main():
  parser = argparse.ArgumentParser(description="Estimate Blackhole NoC transaction cycles and contention.")
  parser.add_argument("spec", nargs="?", type=Path, help="JSON spec. If omitted, a small demo is used.")
  parser.add_argument("--json", action="store_true", help="print full JSON output")
  parser.add_argument("--hotspots", type=int, default=12, help="number of resource hotspots to print")
  parser.add_argument("--self-test", action="store_true", help="run scheduler invariants and exit")
  args = parser.parse_args()

  if args.self_test:
    _self_test()
    print("self-test passed")
    return

  spec = _demo_spec() if args.spec is None else json.loads(args.spec.read_text())
  txns, cal = _transactions_from_dict(spec)
  est = schedule(txns, cal)
  if args.json:
    print(json.dumps(estimate_to_dict(est), indent=2, sort_keys=True))
    return

  print(f"estimated cycles: {est.cycles:.1f}")
  print(f"estimated time:   {est.us:.3f} us @ {cal.clock_mhz:.1f} MHz")
  print(f"packets:          {len(est.packets)}")
  print("hotspots:")
  for name, cycles in est.resource_hotspots(args.hotspots):
    print(f"  {cycles:10.1f}  {name}")


if __name__ == "__main__":
  main()
