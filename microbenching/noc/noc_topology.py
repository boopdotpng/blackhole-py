#!/usr/bin/env python3
from __future__ import annotations

import sys as _bs_sys
from pathlib import Path as _bs_Path
_bs_sys.path.insert(0, str(_bs_Path(__file__).resolve().parents[1]))
import _bench_path  # noqa: F401
from collections.abc import Iterable

Core = tuple[int, int]
Stream = tuple[Core, Core]
Link = tuple[Core, Core]

P100_WORKER_X = (*range(1, 8), *range(10, 15))
P100_WORKER_Y = tuple(range(2, 12))

# Blackhole P100a physical NoC coordinates observed in this tree include
# Tensix workers at x=1..7,10..14, DRAM at x=17,18, and PCIe at (19,24).
ROUTER_X = tuple(range(20))
ROUTER_Y = tuple(range(25))
ROUTER_WIDTH = len(ROUTER_X)
ROUTER_HEIGHT = len(ROUTER_Y)


def _validate_xy(xy: Core) -> Core:
  x, y = xy
  if x not in ROUTER_X or y not in ROUTER_Y:
    raise ValueError(f"router coordinate {xy} outside model grid x=0..19 y=0..24")
  return x, y


def _validate_noc(noc: int) -> int:
  if noc not in (0, 1):
    raise ValueError(f"noc must be 0 or 1, got {noc!r}")
  return noc


def _walk_axis(start: int, stop: int, size: int, step: int) -> Iterable[int]:
  cur = start
  while cur != stop:
    cur = (cur + step) % size
    yield cur


def noc_path(src_xy: Core, dst_xy: Core, noc: int) -> list[Core]:
  """Return the ordered physical router nodes traversed by a unicast packet.

  The model intentionally uses the initial bench-plan assumptions:
  dimension-ordered X-then-Y routing, a physical torus, NoC0 moving in the
  ascending x/y direction, and NoC1 moving in the descending x/y direction.
  The x=8,9 worker gap is represented naturally because router coordinates
  are physical coordinates, not compacted worker-column indices.
  """
  _validate_noc(noc)
  sx, sy = _validate_xy(src_xy)
  dx, dy = _validate_xy(dst_xy)
  step = 1 if noc == 0 else -1

  path = [(sx, sy)]
  x = sx
  for x in _walk_axis(sx, dx, ROUTER_WIDTH, step):
    path.append((x, sy))
  for y in _walk_axis(sy, dy, ROUTER_HEIGHT, step):
    path.append((x, y))
  return path


def noc_hops(src_xy: Core, dst_xy: Core, noc: int) -> int:
  return len(noc_path(src_xy, dst_xy, noc)) - 1


def path_links(src_xy: Core, dst_xy: Core, noc: int) -> list[Link]:
  path = noc_path(src_xy, dst_xy, noc)
  return list(zip(path, path[1:]))


def shared_link(stream_a: Stream, stream_b: Stream, noc: int) -> bool:
  """Return True when two streams traverse at least one same directed link."""
  links_a = set(path_links(stream_a[0], stream_a[1], noc))
  links_b = set(path_links(stream_b[0], stream_b[1], noc))
  return bool(links_a & links_b)


def _fmt_path(path: list[Core]) -> str:
  return " -> ".join(f"({x},{y})" for x, y in path)


def _self_test():
  assert noc_path((1, 2), (3, 2), 0) == [(1, 2), (2, 2), (3, 2)]
  assert noc_path((3, 2), (1, 2), 1) == [(3, 2), (2, 2), (1, 2)]

  gap_path = noc_path((7, 2), (10, 2), 0)
  assert gap_path == [(7, 2), (8, 2), (9, 2), (10, 2)]
  assert noc_hops((7, 2), (10, 2), 0) == 3

  wrap0 = noc_path((14, 2), (1, 2), 0)
  assert wrap0 == [(14, 2), (15, 2), (16, 2), (17, 2), (18, 2), (19, 2), (0, 2), (1, 2)]
  assert noc_hops((14, 2), (1, 2), 0) == 7

  wrap1 = noc_path((1, 2), (14, 2), 1)
  assert wrap1 == [(1, 2), (0, 2), (19, 2), (18, 2), (17, 2), (16, 2), (15, 2), (14, 2)]
  assert noc_hops((1, 2), (14, 2), 1) == 7

  assert shared_link(((1, 2), (4, 2)), ((2, 2), (4, 2)), 0)
  assert not shared_link(((1, 2), (2, 2)), ((3, 2), (4, 2)), 0)


if __name__ == "__main__":
  examples = (
    ((1, 2), (5, 2), 0),
    ((7, 2), (10, 2), 0),
    ((14, 2), (1, 2), 0),
    ((1, 2), (14, 2), 1),
    ((4, 2), (10, 5), 0),
  )
  for src, dst, noc in examples:
    path = noc_path(src, dst, noc)
    print(f"noc{noc} {src}->{dst}: hops={len(path) - 1} path={_fmt_path(path)}")
  _self_test()
  print("self-test passed")
