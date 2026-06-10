#!/usr/bin/env python3
from __future__ import annotations

import sys as _bs_sys
from pathlib import Path as _bs_Path
_bs_sys.path.insert(0, str(_bs_Path(__file__).resolve().parents[1]))
import _bench_path  # noqa: F401
import argparse
import math
from dataclasses import dataclass

from pcie import P100_TENSIX_X, P150_TENSIX_X

TILE = 32
TILE_BYTES = 2048
SUBBLOCK_H = 2
SUBBLOCK_W = 2
SUPPORTED_BW = (1, 2, 3, 4, 5, 6)


@dataclass(frozen=True)
class Group:
  rows: tuple[int, ...]
  cols: tuple[int, ...]
  m_tiles: tuple[int, ...]
  n_tiles: tuple[int, ...]

  @property
  def cores(self) -> int:
    return len(self.rows) * len(self.cols)

  @property
  def padded_m(self) -> int:
    return sum(self.m_tiles)

  @property
  def padded_n(self) -> int:
    return sum(self.n_tiles)


@dataclass(frozen=True)
class Candidate:
  name: str
  split: str
  bw: int
  kt: int
  groups: tuple[Group, ...]
  est_cycles: float
  compute_cycles: float
  feed_cycles: float
  output_cycles: float
  dram_read_cycles: float
  noc_mcast_cycles: float

  @property
  def cores(self) -> int:
    return sum(g.cores for g in self.groups)

  @property
  def padded_m(self) -> int:
    return sum(g.padded_m for g in self.groups)

  @property
  def padded_n(self) -> int:
    return max(g.padded_n for g in self.groups)

  def est_us(self, aiclk_mhz: float) -> float:
    return self.est_cycles / aiclk_mhz


def ceil_div(a: int, b: int) -> int:
  return (a + b - 1) // b


def align_up(x: int, a: int) -> int:
  return ceil_div(x, a) * a


def split_uniform(total: int, parts: int, align: int) -> tuple[int, ...]:
  return (align_up(ceil_div(total, parts), align),) * parts


def split_balanced(total: int, parts: int, align: int) -> tuple[int, ...]:
  """Minimize max shard, then reduce padding while keeping shards balanced."""
  q = align_up(ceil_div(total, parts), align)
  sizes = [q] * parts
  surplus = sum(sizes) - total
  i = parts - 1
  while surplus >= align and i >= 0:
    sizes[i] -= align
    surplus -= align
    i -= 1
  return tuple(sizes)


def split_edge(total: int, parts: int, align: int) -> tuple[int, ...]:
  """Keep all but the last shard equal; put the remainder on the edge shard."""
  q = align_up(ceil_div(total, parts), align)
  sizes = [q] * parts
  used = q * (parts - 1)
  tail = max(align, align_up(total - used, align))
  if tail > q:
    return split_balanced(total, parts, align)
  sizes[-1] = tail
  return tuple(sizes)


def split_tiles(total: int, parts: int, align: int, mode: str) -> tuple[int, ...]:
  if mode == "uniform":
    return split_uniform(total, parts, align)
  if mode == "balanced":
    return split_balanced(total, parts, align)
  if mode == "edge":
    return split_edge(total, parts, align)
  raise ValueError(mode)


def p100_cores(fast: bool) -> list[tuple[int, int]]:
  workers = [(x, y) for x in P100_TENSIX_X for y in range(2, 12)]
  if not fast:
    return workers
  return [core for core in workers if core not in {(P100_TENSIX_X[-1], 2), (P100_TENSIX_X[-1], 3)}]


def p150_cores(fast: bool) -> list[tuple[int, int]]:
  workers = [(x, y) for x in P150_TENSIX_X for y in range(2, 12)]
  if not fast:
    return workers
  return [core for core in workers if core not in {(P150_TENSIX_X[-1], 2), (P150_TENSIX_X[-1], 3)}]


def l1_fits(max_m: int, max_n: int, bw: int, l1_bytes: int) -> bool:
  cb0 = 2 * max_m * bw * TILE_BYTES
  cb1 = 2 * max_n * bw * TILE_BYTES
  cb_out = max_m * max_n * TILE_BYTES
  return cb0 + cb1 + cb_out <= l1_bytes


def estimate(
  groups: tuple[Group, ...],
  kt: int,
  bw: int,
  *,
  math_cycles_per_tile: float,
  dram_read_bpc: float,
  dram_write_bpc: float,
  noc_mcast_bpc: float,
  dual_noc: bool,
) -> tuple[float, float, float, float, float, float]:
  compute = 0.0
  total_dram_read_bytes = 0
  total_output_bytes = 0
  a_mcast_cycles = 0.0
  b_mcast_cycles = 0.0
  for g in groups:
    total_dram_read_bytes += (g.padded_m + g.padded_n) * kt * TILE_BYTES
    total_output_bytes += g.padded_m * g.padded_n * TILE_BYTES
    for m in g.m_tiles:
      a_bytes = m * kt * TILE_BYTES
      a_receivers = max(0, len(g.cols) - 1)
      if a_receivers:
        a_mcast_cycles += a_bytes / noc_mcast_bpc
    for n in g.n_tiles:
      b_bytes = n * kt * TILE_BYTES
      b_receivers = max(0, len(g.rows) - 1)
      if b_receivers:
        b_mcast_cycles += b_bytes / noc_mcast_bpc
    for m in g.m_tiles:
      for n in g.n_tiles:
        compute = max(compute, m * n * kt * math_cycles_per_tile)
  dram_read = total_dram_read_bytes / dram_read_bpc
  noc_mcast = max(a_mcast_cycles, b_mcast_cycles) if dual_noc else a_mcast_cycles + b_mcast_cycles
  output = total_output_bytes / dram_write_bpc
  feed = max(dram_read, noc_mcast)
  total = max(compute, feed, output)
  return total, compute, feed, output, dram_read, noc_mcast


def make_candidate(
  name: str,
  split: str,
  bw: int,
  kt: int,
  groups: tuple[Group, ...],
  args,
) -> Candidate | None:
  max_m = max(max(g.m_tiles) for g in groups)
  max_n = max(max(g.n_tiles) for g in groups)
  if not l1_fits(max_m, max_n, bw, args.l1_bytes):
    return None
  est, comp, feed, out, dram_read, noc_mcast = estimate(
    groups,
    kt,
    bw,
    math_cycles_per_tile=args.math_cycles_per_tile,
    dram_read_bpc=args.dram_read_gbs / args.aiclk_mhz * 1000.0,
    dram_write_bpc=args.dram_write_gbs / args.aiclk_mhz * 1000.0,
    noc_mcast_bpc=args.noc_mcast_bpc,
    dual_noc=args.dual_noc,
  )
  return Candidate(name, split, bw, kt, groups, est, comp, feed, out, dram_read, noc_mcast)


def dense_candidates(mt: int, kt_base: int, nt: int, cores: list[tuple[int, int]], args) -> list[Candidate]:
  out: list[Candidate] = []
  core_set = frozenset(cores)
  xs = tuple(sorted({x for x, _ in cores}))
  ys = tuple(sorted({y for _, y in cores}))
  for split in args.splits:
    for bw in SUPPORTED_BW:
      kt = align_up(kt_base, bw)
      for y0 in range(len(ys)):
        for y1 in range(y0 + 1, len(ys) + 1):
          rows = ys[y0:y1]
          valid_cols = tuple(x for x in xs if all((x, y) in core_set for y in rows))
          for nc in range(1, len(valid_cols) + 1):
            cols = valid_cols[:nc]
            m_tiles = split_tiles(mt, len(rows), SUBBLOCK_H, split)
            n_tiles = split_tiles(nt, len(cols), SUBBLOCK_W, split)
            cand = make_candidate(
              "dense", split, bw, kt,
              (Group(tuple(rows), tuple(cols), m_tiles, n_tiles),),
              args,
            )
            if cand is not None:
              out.append(cand)
  return out


def two_row_group_candidates(mt: int, kt_base: int, nt: int, cores: list[tuple[int, int]], args) -> list[Candidate]:
  out: list[Candidate] = []
  core_set = frozenset(cores)
  xs = tuple(sorted({x for x, _ in cores}))
  ys = tuple(sorted({y for _, y in cores}))
  if len(ys) < 2:
    return out
  all_m = {split: split_tiles(mt, len(ys), SUBBLOCK_H, split) for split in args.splits}
  for split in args.splits:
    for bw in SUPPORTED_BW:
      kt = align_up(kt_base, bw)
      for cut in range(1, len(ys)):
        group_rows = (ys[:cut], ys[cut:])
        groups = []
        for rows in group_rows:
          cols = tuple(x for x in xs if all((x, y) in core_set for y in rows))
          if not cols:
            break
          row_offset = ys.index(rows[0])
          m_tiles = all_m[split][row_offset:row_offset + len(rows)]
          n_tiles = split_tiles(nt, len(cols), SUBBLOCK_W, split)
          groups.append(Group(tuple(rows), cols, m_tiles, n_tiles))
        if len(groups) != 2:
          continue
        cand = make_candidate("two-row-groups", split, bw, kt, tuple(groups), args)
        if cand is not None:
          out.append(cand)
  return out


def tflops(flops: int, cycles: float, aiclk_mhz: float) -> float:
  seconds = cycles / (aiclk_mhz * 1e6)
  return flops / seconds / 1e12


def print_candidate(c: Candidate, args):
  aiclk_mhz = args.aiclk_mhz
  bottleneck = max(
    (("compute", c.compute_cycles), ("feed", c.feed_cycles), ("output", c.output_cycles)),
    key=lambda item: item[1],
  )[0]
  useful_flops = 2 * args.M * args.N * args.K
  padded_flops = 2 * (c.padded_m * TILE) * (c.kt * TILE) * (c.padded_n * TILE)
  print(
    f"{c.name:14s} split={c.split:8s} cores={c.cores:3d} "
    f"padded={c.padded_m * TILE}x{c.kt * TILE}x{c.padded_n * TILE} "
    f"bw={c.bw} est={c.est_us(aiclk_mhz):8.1f} us "
    f"compute={c.compute_cycles / aiclk_mhz:8.1f} feed={c.feed_cycles / aiclk_mhz:7.1f} "
    f"out={c.output_cycles / aiclk_mhz:6.1f} bottleneck={bottleneck}"
  )
  print(
    f"  feed detail: dram-read={c.dram_read_cycles / aiclk_mhz:.1f} us "
    f"noc-mcast={c.noc_mcast_cycles / aiclk_mhz:.1f} us "
    f"tflops useful={tflops(useful_flops, c.est_cycles, aiclk_mhz):.1f} "
    f"padded={tflops(padded_flops, c.est_cycles, aiclk_mhz):.1f}"
  )
  for i, g in enumerate(c.groups):
    print(
      f"  group {i}: rows={g.rows} cols={g.cols} "
      f"Mtiles={g.m_tiles} Ntiles={g.n_tiles}"
    )


def main():
  ap = argparse.ArgumentParser(description="Deterministic matmul layout solver for Blackhole peak experiments.")
  ap.add_argument("M", type=int, nargs="?", default=5000)
  ap.add_argument("N", type=int, nargs="?", default=5000)
  ap.add_argument("K", type=int, nargs="?", default=5000)
  ap.add_argument("--board", choices=("p100a", "p150"), default="p100a")
  ap.add_argument("--dispatch", choices=("fast", "slow"), default="fast")
  ap.add_argument("--splits", nargs="+", choices=("uniform", "balanced", "edge"), default=["uniform", "balanced", "edge"])
  ap.add_argument("--top", type=int, default=12)
  ap.add_argument("--core-max", action="store_true", help="only print candidates that use the maximum modeled core count")
  ap.add_argument("--min-cores", type=int, default=1)
  ap.add_argument("--aiclk-mhz", type=float, default=1350.0)
  ap.add_argument("--math-model", choices=("calibrated", "mvmul"), default="calibrated")
  ap.add_argument("--math-cycles-per-tile", type=float, default=49.3,
                  help="calibrated cycles per 32x32x32 output-tile step")
  ap.add_argument("--mvmul-cycles", type=float, default=16.0)
  ap.add_argument("--mvmuls-per-tile-step", type=float, default=8.0,
                  help="architectural MVMUL count per 32x32x32 tile product")
  ap.add_argument("--dram-read-gbs", type=float, default=420.0)
  ap.add_argument("--dram-write-gbs", type=float, default=450.0)
  ap.add_argument("--noc-mcast-bpc", type=float, default=64.0)
  ap.add_argument("--single-noc", dest="dual_noc", action="store_false",
                  help="charge A and B multicast serially instead of splitting over two NoCs")
  ap.set_defaults(dual_noc=True)
  ap.add_argument("--l1-bytes", type=int, default=1048576 - 0x20000 - 64,
                  help="usable worker L1 bytes for CBs, matching matmul planner")
  args = ap.parse_args()
  if args.math_model == "mvmul":
    args.math_cycles_per_tile = args.mvmuls_per_tile_step * args.mvmul_cycles

  cores = (p100_cores if args.board == "p100a" else p150_cores)(args.dispatch == "fast")
  mt = align_up(args.M, TILE) // TILE
  nt = align_up(args.N, TILE) // TILE
  kt = align_up(args.K, TILE) // TILE
  candidates = dense_candidates(mt, kt, nt, cores, args)
  candidates += two_row_group_candidates(mt, kt, nt, cores, args)
  candidates = [c for c in candidates if c.cores >= args.min_cores]
  if args.core_max and candidates:
    max_cores = max(c.cores for c in candidates)
    candidates = [c for c in candidates if c.cores == max_cores]
  candidates.sort(key=lambda c: (c.est_cycles, -c.cores, c.padded_m * c.padded_n))

  print(f"shape={args.M}x{args.K}x{args.N} tiled={mt}x{kt}x{nt} cores_available={len(cores)}")
  print(f"model: math={args.math_cycles_per_tile} cyc/tile-step ({args.math_model}), aiclk={args.aiclk_mhz} MHz")
  print(
    f"bandwidth: dram-read={args.dram_read_gbs} GB/s dram-write={args.dram_write_gbs} GB/s "
    f"noc-mcast={args.noc_mcast_bpc} B/cyc dual_noc={args.dual_noc}"
  )
  print()
  for c in candidates[:args.top]:
    print_candidate(c, args)


if __name__ == "__main__":
  main()
