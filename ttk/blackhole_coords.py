from __future__ import annotations

from dataclasses import dataclass

Core = tuple[int, int]

GRID_W = 17
GRID_H = 12
TENSIX_Y = tuple(range(2, 12))
T6_X_LOCATIONS = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16)
HARVESTING_NOC_LOCATIONS = (1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10)


@dataclass(frozen=True)
class TensixCoordinateMap:
  enabled_tensix_col: int
  physical_harvesting_mask: int
  sorted_harvesting_mask: int
  harvested_raw_x: tuple[int, ...]
  live_raw_x: tuple[int, ...]
  translated_live_x: tuple[int, ...]
  translated_to_raw_x: dict[int, int]
  raw_to_translated_x: dict[int, int]
  translated_harvested_to_raw_x: dict[int, int]


def noc1_raw_coord(noc0_coord: Core) -> Core:
  return (GRID_W - 1 - noc0_coord[0], GRID_H - 1 - noc0_coord[1])


def raw_coord_for_noc(noc0_coord: Core, noc: int) -> Core:
  if noc == 0:
    return noc0_coord
  if noc == 1:
    return noc1_raw_coord(noc0_coord)
  raise ValueError(f"noc must be 0 or 1, got {noc}")


def shuffle_tensix_harvesting_mask(physical_layout_mask: int) -> int:
  sorted_locations = sorted(HARVESTING_NOC_LOCATIONS)
  out = 0
  pos = 0
  mask = physical_layout_mask & ((1 << len(HARVESTING_NOC_LOCATIONS)) - 1)
  while mask:
    if mask & 1:
      raw_x = HARVESTING_NOC_LOCATIONS[pos]
      out |= 1 << sorted_locations.index(raw_x)
    mask >>= 1
    pos += 1
  return out


def tensix_coordinate_map(enabled_tensix_col: int) -> TensixCoordinateMap:
  physical_mask = (~enabled_tensix_col) & ((1 << len(HARVESTING_NOC_LOCATIONS)) - 1)
  sorted_mask = shuffle_tensix_harvesting_mask(physical_mask)
  harvested_raw_x = tuple(
    x for i, x in enumerate(T6_X_LOCATIONS)
    if sorted_mask & (1 << i)
  )
  live_raw_x = tuple(x for x in T6_X_LOCATIONS if x not in harvested_raw_x)
  translated_live_x = T6_X_LOCATIONS[:len(live_raw_x)]
  translated_to_raw_x = dict(zip(translated_live_x, live_raw_x))
  raw_to_translated_x = {raw_x: tx for tx, raw_x in translated_to_raw_x.items()}

  harvested_sorted_indices = [
    i for i, x in enumerate(T6_X_LOCATIONS)
    if x in harvested_raw_x
  ]
  harvested_sorted_indices.sort(key=lambda i: HARVESTING_NOC_LOCATIONS.index(T6_X_LOCATIONS[i]))
  translated_harvested_to_raw_x = {}
  translated_i = len(T6_X_LOCATIONS) - 1
  for raw_i in harvested_sorted_indices:
    translated_harvested_to_raw_x[T6_X_LOCATIONS[translated_i]] = T6_X_LOCATIONS[raw_i]
    translated_i -= 1

  return TensixCoordinateMap(
    enabled_tensix_col=enabled_tensix_col,
    physical_harvesting_mask=physical_mask,
    sorted_harvesting_mask=sorted_mask,
    harvested_raw_x=harvested_raw_x,
    live_raw_x=live_raw_x,
    translated_live_x=translated_live_x,
    translated_to_raw_x=translated_to_raw_x,
    raw_to_translated_x=raw_to_translated_x,
    translated_harvested_to_raw_x=translated_harvested_to_raw_x,
  )


def translated_tensix_to_raw_noc0(coord: Core, coord_map: TensixCoordinateMap) -> Core:
  x, y = coord
  if y not in TENSIX_Y:
    raise ValueError(f"translated Tensix y must be in {TENSIX_Y[0]}..{TENSIX_Y[-1]}, got {coord}")
  if x in coord_map.translated_to_raw_x:
    return (coord_map.translated_to_raw_x[x], y)
  if x in coord_map.translated_harvested_to_raw_x:
    return (coord_map.translated_harvested_to_raw_x[x], y)
  raise ValueError(f"translated Tensix x is not mapped on this device: {coord}")


def translated_live_tensix_cores(coord_map: TensixCoordinateMap) -> list[Core]:
  return [(x, y) for y in TENSIX_Y for x in coord_map.translated_live_x]


def live_raw_tensix_cores(coord_map: TensixCoordinateMap) -> list[Core]:
  return [(x, y) for y in TENSIX_Y for x in coord_map.live_raw_x]


def raw_tensix_to_translated_noc0(coord: Core, coord_map: TensixCoordinateMap) -> Core:
  x, y = coord
  if y not in TENSIX_Y:
    raise ValueError(f"raw Tensix y must be in {TENSIX_Y[0]}..{TENSIX_Y[-1]}, got {coord}")
  if x not in coord_map.raw_to_translated_x:
    raise ValueError(f"raw Tensix coord is not a live worker column: {coord}")
  return (coord_map.raw_to_translated_x[x], y)


def directional_torus_hops(src: Core, dst: Core, noc: int) -> tuple[int, int, int]:
  if noc not in (0, 1):
    raise ValueError(f"noc must be 0 or 1, got {noc}")
  sx, sy = src
  dx, dy = dst
  x_hops = (dx - sx) % GRID_W
  y_hops = (dy - sy) % GRID_H
  return x_hops + y_hops, x_hops, y_hops
