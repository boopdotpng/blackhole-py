#!/usr/bin/env python3
from __future__ import annotations

import sys as _bs_sys
from pathlib import Path as _bs_Path
_bs_sys.path.insert(0, str(_bs_Path(__file__).resolve().parents[1]))
import _bench_path  # noqa: F401
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  sys.path.insert(0, str(Path(__file__).resolve().parent))

import matmul_peak as base

from ttk.tensix import TensixL1


AICLK_MHZ = 1350.0
TRISC_CYCLES_PER_SUBBLOCK = 924.0
OUTPUT_TAIL_US = 60.0


@dataclass(frozen=True)
class Candidate:
  pcm: int
  pcn: int
  bw: int
  blocks: int
  rows: int
  cols: int
  waves_m: int
  waves_n: int
  mt: int
  kt: int
  nt: int
  subblocks_per_core_wave: int
  total_us: float
  useful_tflops: float
  padded_tflops: float
  partial_pack_multiplier: float
  l1_bytes: int

  @property
  def waves(self) -> int:
    return self.waves_m * self.waves_n


def ceil_div(a: int, b: int) -> int:
  return (a + b - 1) // b


def align_up(a: int, b: int) -> int:
  return ceil_div(a, b) * b


def tflops(m: int, n: int, k: int, us: float) -> float:
  return (2.0 * m * n * k) / (us * 1.0e6) if us > 0 else 0.0


def candidate_us(c: Candidate, launch_us: float) -> float:
  trisc_us = c.subblocks_per_core_wave * TRISC_CYCLES_PER_SUBBLOCK / AICLK_MHZ
  return c.waves * (trisc_us + OUTPUT_TAIL_US + launch_us)


def sweep(
  *,
  M: int,
  N: int,
  K: int,
  rows: int,
  cols: int,
  max_bw: int,
  max_pcm: int,
  max_pcn: int,
  input_buffer_factor: int,
  launch_us: float,
) -> list[Candidate]:
  mt_base = base._ceil32(M) // base.TILE
  nt_base = base._ceil32(N) // base.TILE
  kt_base = base._ceil32(K) // base.TILE
  l1_data_bytes = TensixL1.SIZE - TensixL1.DATA_BUFFER_SPACE_BASE - base.SYNC_BYTES
  out_subblock_h = base.SUPPORTED_OUT_SUBBLOCK_H
  out_subblock_w = base.SUPPORTED_OUT_SUBBLOCK_W
  out_subblock_tiles = out_subblock_h * out_subblock_w
  candidates: list[Candidate] = []

  for pcm in range(out_subblock_h, max_pcm + 1, out_subblock_h):
    for pcn in range(out_subblock_w, max_pcn + 1, out_subblock_w):
      waves_m = ceil_div(mt_base, rows * pcm)
      waves_n = ceil_div(nt_base, cols * pcn)
      mt = waves_m * rows * pcm
      nt = waves_n * cols * pcn
      for bw in range(1, max_bw + 1):
        kt = align_up(kt_base, bw)
        blocks = kt // bw
        l1_bytes = (
          input_buffer_factor * pcm * bw * base.TILE_BYTES
          + input_buffer_factor * pcn * bw * base.TILE_BYTES
          + pcm * pcn * base.TILE_BYTES
        )
        if l1_bytes > l1_data_bytes:
          continue
        subblocks = blocks * (pcm // out_subblock_h) * (pcn // out_subblock_w)
        packed_tiles = subblocks * out_subblock_tiles
        final_tiles = pcm * pcn
        rough = Candidate(
          pcm=pcm,
          pcn=pcn,
          bw=bw,
          blocks=blocks,
          rows=rows,
          cols=cols,
          waves_m=waves_m,
          waves_n=waves_n,
          mt=mt,
          kt=kt,
          nt=nt,
          subblocks_per_core_wave=subblocks,
          total_us=0.0,
          useful_tflops=0.0,
          padded_tflops=0.0,
          partial_pack_multiplier=packed_tiles / max(1, final_tiles),
          l1_bytes=l1_bytes,
        )
        total_us = candidate_us(rough, launch_us)
        candidates.append(
          Candidate(
            pcm=pcm,
            pcn=pcn,
            bw=bw,
            blocks=blocks,
            rows=rows,
            cols=cols,
            waves_m=waves_m,
            waves_n=waves_n,
            mt=mt,
            kt=kt,
            nt=nt,
            subblocks_per_core_wave=subblocks,
            total_us=total_us,
            useful_tflops=tflops(M, N, K, total_us),
            padded_tflops=tflops(mt * base.TILE, nt * base.TILE, kt * base.TILE, total_us),
            partial_pack_multiplier=packed_tiles / max(1, final_tiles),
            l1_bytes=l1_bytes,
          )
        )

  return sorted(candidates, key=lambda c: (c.total_us, -c.useful_tflops, c.waves, c.pcm * c.pcn))


def print_candidates(name: str, candidates: list[Candidate], top: int, max_bw: int) -> None:
  print(f"Matmul shape sweep ({name})")
  print(
    "  rank est_us useful_TF padded_TF waves shape bw blocks subblocks/wave "
    "packx padded_tiles L1_KiB run_env"
  )
  for rank, c in enumerate(candidates[:top], 1):
    split_axis = "auto"
    if c.waves_m == 1 and c.waves_n > 1:
      split_axis = "n"
    elif c.waves_n == 1 and c.waves_m > 1:
      split_axis = "m"
    env = (
      f"MATMUL_MAX_BW={max_bw} "
      f"MATMUL_MAX_PER_CORE_M={c.pcm} "
      f"MATMUL_MAX_PER_CORE_N={c.pcn} "
      f"MATMUL_SPLIT_AXIS={split_axis}"
    )
    print(
      f"  {rank:>2} {c.total_us:>7.1f} {c.useful_tflops:>9.1f} {c.padded_tflops:>9.1f} "
      f"{c.waves_m}x{c.waves_n} {c.pcm}x{c.pcn} {c.bw:>2} {c.blocks:>2} "
      f"{c.subblocks_per_core_wave:>5} {c.partial_pack_multiplier:>5.1f}x "
      f"{c.mt}x{c.kt}x{c.nt} {c.l1_bytes / 1024:>7.1f} {env}"
    )


def main() -> None:
  parser = argparse.ArgumentParser(description="Brute-force static matmul shape sweep.")
  parser.add_argument("M", type=int, nargs="?", default=5000)
  parser.add_argument("N", type=int, nargs="?", default=5000)
  parser.add_argument("K", type=int, nargs="?", default=5000)
  parser.add_argument("--kind", choices=("worker", "drisc", "both"), default="both")
  parser.add_argument("--max-bw", type=int, default=24)
  parser.add_argument("--max-pcm", type=int, default=32)
  parser.add_argument("--max-pcn", type=int, default=32)
  parser.add_argument("--input-buffer-factor", type=int, default=base.INPUT_BUFFER_FACTOR)
  parser.add_argument("--launch-us", type=float, default=0.0)
  parser.add_argument("--top", type=int, default=20)
  args = parser.parse_args()

  shapes = []
  if args.kind in ("worker", "both"):
    shapes.append(("worker 10x11", 10, 11))
  if args.kind in ("drisc", "both"):
    shapes.append(("drisc 10x10", 10, 10))

  for i, (name, rows, cols) in enumerate(shapes):
    if i:
      print()
    candidates = sweep(
      M=args.M,
      N=args.N,
      K=args.K,
      rows=rows,
      cols=cols,
      max_bw=args.max_bw,
      max_pcm=args.max_pcm,
      max_pcn=args.max_pcn,
      input_buffer_factor=args.input_buffer_factor,
      launch_us=args.launch_us,
    )
    print_candidates(name, candidates, args.top, args.max_bw)


if __name__ == "__main__":
  main()
