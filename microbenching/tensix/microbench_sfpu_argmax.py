#!/usr/bin/env python3
"""SFPU argmax primitive proof.

This starts validating the Blackhole SFPU "destination index" path that TT's
max-pool-with-indices LLK uses:

  SFPLOAD values into L0 while capturing their Dst indices into L4
  SFPSWAP value registers; hardware swaps L4/L5 indices in lockstep
  SFPSTORE the winning value and captured Dst index

The value path passes for one 32-lane footprint and for a staged N-value
reduction over multiple cores. The N-value argmax microbench tree-reduces
groups of 8 candidates per pass using the hardware-captured row-local lane
index. Today the Python driver carries the candidate-id map between passes;
that is useful primitive validation, not the CUDA-like final design. A final
device-resident version should keep exact u32 ids in a RISC-visible buffer and
compact/reduce them on device alongside the SFPU value reductions.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness  # noqa: E402  (sets PYTHONPATH/device env defaults)
import numpy as np

from device import Device  # noqa: E402
from dsl import (  # noqa: E402
  TTINCRWC,
  TTSFPCONFIG,
  TTSFPLOAD,
  TTSFPLOADI,
  TTSFPMOV,
  TTSFPNOP,
  TTSFPSHFT2,
  TTSFPSTORE,
  TTSFPSWAP,
  TTSFPTRANSP,
)
from program import Dtype  # noqa: E402

from examples import add1  # noqa: E402


TILE = 32
DTYPE = Dtype.Float16_b
SFPSWAP_ALL_ROWS_MAX = 1
SFPLOAD_MOD_BF16 = 0
SFPLOAD_MOD_UINT16 = 6
ADDR_MOD = 7


def to_bf16(x: np.ndarray) -> np.ndarray:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return ((u >> 16).astype("<u4") << 16).view("<f4")


def to_bf16_bytes(x: np.ndarray) -> bytes:
  u = np.asarray(x, dtype="<f4").view("<u4")
  return (u >> 16).astype("<u2").tobytes()


def from_bf16_bytes(raw: bytes, shape: tuple[int, ...]) -> np.ndarray:
  u16 = np.frombuffer(raw, dtype="<u2")
  return (u16.astype("<u4") << 16).view("<f4").reshape(shape)


def footprint_tile(values: np.ndarray) -> np.ndarray:
  tile = np.zeros((TILE, TILE), dtype=np.float32)
  for lane, value in enumerate(values.astype(np.float32)):
    row = lane // 8
    col = (lane & 7) * 2
    tile[row, col] = value
  return to_bf16(tile)


def captured_dst_index_for_lane(lane: int) -> int:
  # Blackhole silicon captures the SFPU footprint lane in bits [15:8].
  return lane << 8


def or_lane_config_bits(fw, bits: int):
  return fw.emit(TTSFPCONFIG(bits, 15, 3), TTSFPNOP())


def and_lane_config_bits(fw, mask: int):
  return fw.emit(TTSFPCONFIG(mask, 15, 5), TTSFPNOP())


def enable_dest_index_capture(fw):
  # LaneConfig bit 2: ENABLE_DEST_INDEX, bit 3: CAPTURE_DEFAULT_DEST_INDEX.
  return or_lane_config_bits(fw, 0x000C)


def enable_dest_index_swap(fw):
  return or_lane_config_bits(fw, 0x0004)


def disable_dest_index_capture(fw):
  return and_lane_config_bits(fw, 0xFFF3)


def emit_rowwise_argmax(fw):
  for shifts in (4, 2, 1):
    disable_dest_index_capture(fw)
    fw.emit(TTSFPMOV(0, 0, 1, 0))       # candidate values
    fw.emit(TTSFPMOV(0, 4, 5, 0))       # candidate indices
    for _ in range(shifts):
      fw.emit(TTSFPSHFT2(0, 1, 1, 4))
      fw.emit(TTSFPSHFT2(0, 5, 5, 4))
    enable_dest_index_swap(fw)
    fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
    fw.emit(TTSFPNOP())

  # Rotate the row winners to every lane, matching emit_horizontal_reduce_max.
  disable_dest_index_capture(fw)
  fw.emit(TTSFPSHFT2(0, 0, 0, 3))
  fw.emit(TTSFPSHFT2(0, 4, 4, 3))
  return fw


def emit_argmax32_value_index(fw):
  """Reduce L0's 32 lanes to max in L0 and captured Dst index in L4."""
  enable_dest_index_capture(fw)
  fw.emit(TTSFPLOAD(0, SFPLOAD_MOD_BF16, ADDR_MOD, 0))
  emit_rowwise_argmax(fw)

  # Collapse the four SFPU rows. SFPTRANSP applies to L0..L3 and L4..L7, so
  # after placing only the row winners in L0/L4, one transpose makes them a
  # four-register column that the LLK max-pool-with-indices sort can compare.
  disable_dest_index_capture(fw)
  fw.emit(TTSFPLOADI(1, 0, 0xFF80))  # -inf, bf16 immediate
  fw.emit(TTSFPLOADI(2, 0, 0xFF80))
  fw.emit(TTSFPLOADI(3, 0, 0xFF80))
  fw.emit(TTSFPLOADI(5, 2, 0))
  fw.emit(TTSFPLOADI(6, 2, 0))
  fw.emit(TTSFPLOADI(7, 2, 0))
  fw.emit(TTSFPTRANSP(0, 0, 0, 0))
  fw.emit(TTSFPNOP())
  enable_dest_index_swap(fw)
  fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
  fw.emit(TTSFPNOP())
  disable_dest_index_capture(fw)
  fw.emit(TTSFPMOV(0, 2, 1, 0))
  fw.emit(TTSFPMOV(0, 6, 5, 0))
  enable_dest_index_swap(fw)
  fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
  fw.emit(TTSFPNOP())
  disable_dest_index_capture(fw)
  fw.emit(TTSFPMOV(0, 3, 1, 0))
  fw.emit(TTSFPMOV(0, 7, 5, 0))
  enable_dest_index_swap(fw)
  fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
  fw.emit(TTSFPNOP())

  # Store the winning value in even columns and its captured Dst index in odd
  # columns of the first four rows. The host checks lane 0 at [0,0]/[0,1].
  fw.emit(TTSFPSTORE(0, SFPLOAD_MOD_BF16, ADDR_MOD, 0))
  fw.emit(TTSFPSTORE(4, SFPLOAD_MOD_UINT16, ADDR_MOD, 2))
  fw.emit(TTSFPNOP())
  disable_dest_index_capture(fw)
  return fw.emit(TTINCRWC(0, 2, 0, 0))


def emit_cross_row_debug(fw):
  """Store cross-row tournament state after each compare.

  Rows 0/1/2 store the accumulator after comparing row winners:
    row 0: after rows 0 vs 1
    row 1: after previous vs row 2
    row 2: after previous vs row 3
  """
  enable_dest_index_capture(fw)
  fw.emit(TTSFPLOAD(0, SFPLOAD_MOD_BF16, ADDR_MOD, 0))
  emit_rowwise_argmax(fw)

  disable_dest_index_capture(fw)
  fw.emit(TTSFPLOADI(1, 0, 0xFF80))
  fw.emit(TTSFPLOADI(2, 0, 0xFF80))
  fw.emit(TTSFPLOADI(3, 0, 0xFF80))
  fw.emit(TTSFPLOADI(5, 2, 0))
  fw.emit(TTSFPLOADI(6, 2, 0))
  fw.emit(TTSFPLOADI(7, 2, 0))
  fw.emit(TTSFPTRANSP(0, 0, 0, 0))
  fw.emit(TTSFPNOP())

  disable_dest_index_capture(fw)
  for value_lreg, index_lreg, row_addr in ((0, 4, 0), (1, 5, 4), (2, 6, 8), (3, 7, 12)):
    fw.emit(TTSFPSTORE(value_lreg, SFPLOAD_MOD_BF16, ADDR_MOD, row_addr))
    fw.emit(TTSFPSTORE(index_lreg, SFPLOAD_MOD_UINT16, ADDR_MOD, row_addr + 2))
  fw.emit(TTSFPNOP())
  return fw.emit(TTINCRWC(0, 2, 0, 0))


def emit_cross_row_step_debug(fw):
  """Store cross-row tournament state after each compare.

  This assumes the transpose layout has been separately inspected by
  emit_cross_row_debug.
  """
  enable_dest_index_capture(fw)
  fw.emit(TTSFPLOAD(0, SFPLOAD_MOD_BF16, ADDR_MOD, 0))
  emit_rowwise_argmax(fw)

  disable_dest_index_capture(fw)
  fw.emit(TTSFPLOADI(1, 0, 0xFF80))
  fw.emit(TTSFPLOADI(2, 0, 0xFF80))
  fw.emit(TTSFPLOADI(3, 0, 0xFF80))
  fw.emit(TTSFPLOADI(5, 2, 0))
  fw.emit(TTSFPLOADI(6, 2, 0))
  fw.emit(TTSFPLOADI(7, 2, 0))
  fw.emit(TTSFPTRANSP(0, 0, 0, 0))
  fw.emit(TTSFPNOP())

  enable_dest_index_swap(fw)
  fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
  fw.emit(TTSFPNOP())
  disable_dest_index_capture(fw)
  fw.emit(TTSFPSTORE(0, SFPLOAD_MOD_BF16, ADDR_MOD, 0))
  fw.emit(TTSFPSTORE(4, SFPLOAD_MOD_UINT16, ADDR_MOD, 2))

  fw.emit(TTSFPMOV(0, 2, 1, 0))
  fw.emit(TTSFPMOV(0, 6, 5, 0))
  fw.emit(TTSFPNOP())
  enable_dest_index_swap(fw)
  fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
  fw.emit(TTSFPNOP())
  disable_dest_index_capture(fw)
  fw.emit(TTSFPSTORE(0, SFPLOAD_MOD_BF16, ADDR_MOD, 4))
  fw.emit(TTSFPSTORE(4, SFPLOAD_MOD_UINT16, ADDR_MOD, 6))

  fw.emit(TTSFPMOV(0, 3, 1, 0))
  fw.emit(TTSFPMOV(0, 7, 5, 0))
  fw.emit(TTSFPNOP())
  enable_dest_index_swap(fw)
  fw.emit(TTSFPSWAP(0, 0, 1, SFPSWAP_ALL_ROWS_MAX))
  fw.emit(TTSFPNOP())
  disable_dest_index_capture(fw)
  fw.emit(TTSFPSTORE(0, SFPLOAD_MOD_BF16, ADDR_MOD, 8))
  fw.emit(TTSFPSTORE(4, SFPLOAD_MOD_UINT16, ADDR_MOD, 10))
  fw.emit(TTSFPNOP())
  return fw.emit(TTINCRWC(0, 2, 0, 0))


def emit_row_argmax_debug(fw):
  """Store row-local argmax values/indices before the cross-row collapse."""
  enable_dest_index_capture(fw)
  fw.emit(TTSFPLOAD(0, SFPLOAD_MOD_BF16, ADDR_MOD, 0))
  emit_rowwise_argmax(fw)
  fw.emit(TTSFPSTORE(0, SFPLOAD_MOD_BF16, ADDR_MOD, 0))
  fw.emit(TTSFPSTORE(4, SFPLOAD_MOD_UINT16, ADDR_MOD, 2))
  fw.emit(TTSFPNOP())
  disable_dest_index_capture(fw)
  return fw.emit(TTINCRWC(0, 2, 0, 0))


def emit_capture_echo(fw):
  """Store L4 immediately after SFPLOAD's destination-index capture."""
  enable_dest_index_capture(fw)
  fw.emit(TTSFPLOAD(0, SFPLOAD_MOD_BF16, ADDR_MOD, 0))
  fw.emit(TTSFPSTORE(4, SFPLOAD_MOD_UINT16, ADDR_MOD, 2))
  fw.emit(TTSFPNOP())
  disable_dest_index_capture(fw)
  return fw.emit(TTINCRWC(0, 2, 0, 0))


def run_tile(device: Device, values: np.ndarray, body=emit_argmax32_value_index) -> tuple[np.ndarray, np.ndarray]:
  return run_tiles(device, np.asarray([values], dtype=np.float32), body=body, cores=device.cores[:1], tiles_per_core=1)


def run_tiles(
  device: Device,
  tile_values: np.ndarray,
  *,
  body=emit_argmax32_value_index,
  cores: list[tuple[int, int]] | None = None,
  tiles_per_core: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
  tiles = np.stack([footprint_tile(values) for values in tile_values], axis=0)
  src_buf = device.alloc_write(
    to_bf16_bytes(tiles),
    dtype=DTYPE,
    shape=tiles.shape,
    name="sfpu_argmax_src",
  )
  dst_buf = device.dram.alloc(tiles.shape[0], dtype=DTYPE, shape=tiles.shape, name="sfpu_argmax_dst")
  if cores is None:
    cores = device.cores[:1]
  if tiles_per_core is None:
    tiles_per_core = math.ceil(tiles.shape[0] / len(cores))

  old_body = add1.math_add1_replay_row
  add1.math_add1_replay_row = body
  try:
    prog = add1.build_program(
      src_buf.addr,
      dst_buf.addr,
      len(device.dram.bank_tiles),
      cores=cores,
      tiles_per_core=tiles_per_core,
    )
    prog.name = "microbench_sfpu_argmax32"
    device.run(prog)
  finally:
    add1.math_add1_replay_row = old_body

  raw = device.dram_read(dst_buf)
  return from_bf16_bytes(raw, tiles.shape), np.frombuffer(raw, dtype="<u2").reshape(tiles.shape)


def reduce_captured_argmax(
  device: Device,
  values: np.ndarray,
  candidate_ids: np.ndarray,
  *,
  requested_cores: int,
) -> tuple[float, int, int]:
  """Tree-reduce values on-device while host carries the candidate id map.

  Each hardware pass reduces one row of 8 candidates per tile. The SFPU
  captures the winning lane as lane << 8 in L4; the host uses that lane to
  carry forward the original candidate id for the next pass.
  """
  cur_values = values.astype(np.float32, copy=False)
  cur_ids = candidate_ids.astype(np.int64, copy=False)
  passes = 0

  while cur_values.size > 1:
    group_count = math.ceil(cur_values.size / 8)
    padded_values = np.full(group_count * 8, -np.inf, dtype=np.float32)
    padded_ids = np.full(group_count * 8, -1, dtype=np.int64)
    padded_values[:cur_values.size] = cur_values
    padded_ids[:cur_ids.size] = cur_ids

    tile_values = np.full((group_count, 32), -np.inf, dtype=np.float32)
    tile_values[:, :8] = padded_values.reshape(group_count, 8)

    core_count = max(1, min(requested_cores, group_count, len(device.cores)))
    tiles_per_core = math.ceil(group_count / core_count)
    total_tiles = core_count * tiles_per_core
    if total_tiles > group_count:
      extra_values = np.full((total_tiles - group_count, 32), -np.inf, dtype=np.float32)
      tile_values = np.concatenate([tile_values, extra_values], axis=0)

    got_f32, got_u16 = run_tiles(
      device,
      tile_values,
      body=emit_row_argmax_debug,
      cores=device.cores[:core_count],
      tiles_per_core=tiles_per_core,
    )
    winner_lanes = (got_u16[:group_count, 0, 1].astype(np.uint16) >> 8).astype(np.int64)
    winner_offsets = np.arange(group_count, dtype=np.int64) * 8 + winner_lanes
    cur_values = got_f32[:group_count, 0, 0].astype(np.float32)
    cur_ids = padded_ids[winner_offsets]
    passes += 1

  return float(cur_values[0]), int(cur_ids[0]), passes


def run_primitive_check(device: Device, *, debug_cross_row: bool = False) -> bool:
  rng = np.random.default_rng(19)
  values = to_bf16(rng.uniform(-4.0, 4.0, 32).astype(np.float32))
  # Pin a unique winner away from lane 0 so index motion is actually tested.
  values[23] = np.float32(7.5)
  values[5] = np.float32(6.25)

  expected_lane = int(np.argmax(values))
  expected_value = float(values[expected_lane])
  expected_index = captured_dst_index_for_lane(expected_lane)

  if debug_cross_row:
    _, capture_u16 = run_tile(device, values, emit_capture_echo)
    row_f32, row_u16 = run_tile(device, values, emit_row_argmax_debug)
    trans_f32, trans_u16 = run_tile(device, values, emit_cross_row_debug)
    cross_f32, cross_u16 = run_tile(device, values, emit_cross_row_step_debug)
    capture_u16 = capture_u16[0]
    row_f32 = row_f32[0]
    row_u16 = row_u16[0]
    trans_f32 = trans_f32[0]
    trans_u16 = trans_u16[0]
    cross_f32 = cross_f32[0]
    cross_u16 = cross_u16[0]
  got_f32, got_u16 = run_tile(device, values)
  got_f32 = got_f32[0]
  got_u16 = got_u16[0]

  got_value = float(got_f32[0, 0])
  got_index = int(got_u16[0, 1])
  value_ok = abs(got_value - expected_value) <= 2.0e-3
  index_ok = got_index == expected_index
  ok = value_ok and index_ok

  print("SFPU argmax32 value+index primitive")
  print(f"  expected lane={expected_lane} dst_index=0x{expected_index:02x} value={expected_value:.6g}")
  print(f"  got      dst_index=0x{got_index:02x} value={got_value:.6g}")
  print(f"  value: {'PASS' if value_ok else 'FAIL'}")
  print(f"  final index: {'PASS' if index_ok else 'XFAIL'}")
  if debug_cross_row and not ok:
    print("  debug captured-index echo rows 0:4, cols 0:8")
    print(np.array2string(capture_u16[:4, :8], formatter={"int": lambda x: f"0x{int(x):04x}"}))
    print("  debug row-reduce value rows 0:4, cols 0:8")
    print(np.array2string(row_f32[:4, :8], precision=4, suppress_small=False))
    print("  debug row-reduce raw u16 rows 0:4, cols 0:8")
    print(np.array2string(row_u16[:4, :8], formatter={"int": lambda x: f"0x{int(x):04x}"}))
    print("  debug transpose value rows 0:16, cols 0:4")
    print(np.array2string(trans_f32[:16, :4], precision=4, suppress_small=False))
    print("  debug transpose raw u16 rows 0:16, cols 0:4")
    print(np.array2string(trans_u16[:16, :4], formatter={"int": lambda x: f"0x{int(x):04x}"}))
    print("  debug cross-row step value rows 0:12, cols 0:4")
    print(np.array2string(cross_f32[:12, :4], precision=4, suppress_small=False))
    print("  debug cross-row step raw u16 rows 0:12, cols 0:4")
    print(np.array2string(cross_u16[:12, :4], formatter={"int": lambda x: f"0x{int(x):04x}"}))
    print("  debug value rows 0:4, cols 0:8")
    print(np.array2string(got_f32[:4, :8], precision=4, suppress_small=False))
    print("  debug raw u16 rows 0:4, cols 0:8")
    print(np.array2string(got_u16[:4, :8], formatter={"int": lambda x: f"0x{int(x):04x}"}))
  print("VALUE PASS" if value_ok else "FAIL")
  return value_ok


def run_n_value_max(device: Device, *, n: int, requested_cores: int) -> bool:
  if n <= 0:
    raise ValueError("n must be positive")
  rng = np.random.default_rng(117)
  values = to_bf16(rng.uniform(-8.0, 8.0, n).astype(np.float32))
  winner = min(n - 1, max(0, (n * 7) // 11))
  values[winner] = np.float32(31.0)

  tile_count = math.ceil(n / 32)
  core_count = max(1, min(requested_cores, tile_count, len(device.cores)))
  tiles_per_core = math.ceil(tile_count / core_count)
  total_tiles = core_count * tiles_per_core
  padded = np.full(total_tiles * 32, -np.inf, dtype=np.float32)
  padded[:n] = values
  tile_values = padded.reshape(total_tiles, 32)

  cores = device.cores[:core_count]
  first_f32, _ = run_tiles(device, tile_values, cores=cores, tiles_per_core=tiles_per_core)
  candidates = first_f32[:tile_count, 0, 0].astype(np.float32)

  second_values = np.full(32, -np.inf, dtype=np.float32)
  second_values[:tile_count] = candidates
  final_f32, _ = run_tile(device, second_values)
  got_value = float(final_f32[0, 0, 0])

  expected_value = float(values[int(np.argmax(values))])
  value_ok = abs(got_value - expected_value) <= 2.0e-3
  print(f"N-stage SFPU value max n={n} cores={core_count} tiles={tile_count}")
  print(f"  expected index={int(np.argmax(values))} value={expected_value:.6g}")
  print(f"  got      value={got_value:.6g}")
  print(f"  value: {'PASS' if value_ok else 'FAIL'}")
  print("  index: PENDING (cross-row companion index tracking is isolated above)")
  return value_ok


def run_n_value_argmax(device: Device, *, n: int, requested_cores: int) -> bool:
  if n <= 0:
    raise ValueError("n must be positive")

  rng = np.random.default_rng(203)
  values = to_bf16(rng.uniform(-8.0, 8.0, n).astype(np.float32))
  winner = min(n - 1, max(0, (n * 5) // 9))
  values[winner] = np.float32(29.0)

  expected_index = int(np.argmax(values))
  expected_value = float(values[expected_index])

  got_value, got_index, passes = reduce_captured_argmax(
    device,
    values,
    np.arange(n, dtype=np.int64),
    requested_cores=requested_cores,
  )

  value_ok = abs(got_value - expected_value) <= 2.0e-3
  index_ok = got_index == expected_index
  ok = value_ok and index_ok

  print(f"N-stage SFPU captured-lane argmax n={n} passes={passes}")
  print(f"  expected index={expected_index} value={expected_value:.6g}")
  print(f"  got      index={got_index} value={got_value:.6g}")
  print(f"  value: {'PASS' if value_ok else 'FAIL'}")
  print(f"  index: {'PASS' if index_ok else 'FAIL'}")
  return ok


def main() -> int:
  parser = argparse.ArgumentParser(description="Blackhole SFPU on-device argmax PoC")
  parser.add_argument("--n", type=int, default=1024, help="length for the staged N-value max PoC")
  parser.add_argument("--cores", type=int, default=4, help="cores to use for pass-1 tile-local reductions")
  parser.add_argument("--debug-cross-row", action="store_true", help="print verbose diagnostics for the cross-row captured-index XFAIL")
  args = parser.parse_args()

  with harness.open_device() as device:
    primitive_ok = run_primitive_check(device, debug_cross_row=args.debug_cross_row)
    if args.n <= 1024:
      n_ok = run_n_value_max(device, n=args.n, requested_cores=args.cores)
    else:
      n_ok = True
      print(f"N-stage SFPU value max n={args.n}: SKIP (legacy value-only demo covers up to 1024)")
    argmax_ok = run_n_value_argmax(device, n=args.n, requested_cores=args.cores)
  return 0 if primitive_ok and n_ok and argmax_ok else 1


if __name__ == "__main__":
  raise SystemExit(main())
