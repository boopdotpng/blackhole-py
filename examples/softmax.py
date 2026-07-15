#!/usr/bin/env python3
"""Stable row softmax with FP32 intermediates and BF16 output."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Cond
from program import Buffer, DType, Dram, Program
from ttk.sfpu import LReg, SfpuFormat

TILE = 32
ROWS_PER_CORE = 4
CORES = tuple((1, y) for y in range(2, 10))
GROUP_CHUNKS = (0, 2, 16, 18)
CB_DEPTH = 16
OUTPUT_DEPTH = 96


def _segments(count, size=CB_DEPTH):
  return tuple(min(size, count - start) for start in range(0, count, size))


def _pack_one(p, destination):
  p.pack.acquire_dst()
  destination.reserve_back()
  p.pack.to_cb(synchronize=False)
  destination.push_back()
  p.pack.release_dst()


def _row_base(p, group_addr):
  base = p.trisc1.reg()
  p.trisc1.load(base, group_addr)
  p.trisc1.slli(base, base, 2)
  with p.trisc1.scope():
    split = p.trisc1.reg()
    p.trisc1.li(split, 16)
    with p.trisc1.if_(Cond(base, ">=u", split)):
      p.trisc1.addi(base, base, 16)
  return base


def _load_group(sfpu, base, registers):
  for register, chunk in zip(registers, GROUP_CHUNKS):
    sfpu.load_dst(register, base, format=SfpuFormat.FP32, delta=chunk)


def _reduce_max(sfpu, base):
  _load_group(sfpu, base, (LReg.L0, LReg.L1, LReg.L2, LReg.L3))
  sfpu.maximum_into(LReg.L0, LReg.L2)
  sfpu.maximum_into(LReg.L1, LReg.L3)
  sfpu.maximum_into(LReg.L0, LReg.L1)
  sfpu.horizontal_max()


def _exp_and_sum(sfpu, base):
  for chunk in GROUP_CHUNKS:
    sfpu.load_dst(LReg.L0, base, format=SfpuFormat.FP32, delta=chunk)
    sfpu.move(LReg.L6, LReg.L1)
    sfpu.multiply(LReg.L1, LReg.CONST_NEG1, LReg.L1)
    sfpu.add(LReg.L0, LReg.L1, LReg.L0)
    sfpu.exp(LReg.L0, LReg.L0, scratch=(1, 2, 3, 4, 5))
    sfpu.store_dst(LReg.L0, base, format=SfpuFormat.FP32, delta=chunk)
  _load_group(sfpu, base, (LReg.L0, LReg.L1, LReg.L2, LReg.L3))
  sfpu.add_into(LReg.L2, LReg.L3)
  sfpu.add_into(LReg.L1, LReg.L2)
  sfpu.add_into(LReg.L0, LReg.L1)
  sfpu.horizontal_sum()


def _check_buffers(scores, probabilities, cores):
  if tuple(cores) != CORES:
    raise ValueError(f"softmax currently requires cores {CORES}")
  if scores.dtype is not DType.F32 or probabilities.dtype is not DType.BF16:
    raise ValueError("softmax requires FP32 scores and BF16 probabilities")
  if scores.shape != probabilities.shape or scores.padded_shape != probabilities.padded_shape:
    raise ValueError("scores and probabilities must have matching shapes")
  if (len(scores.padded_shape) != 2 or scores.padded_shape[0] != TILE or
      scores.padded_shape[1] % TILE):
    raise ValueError("softmax tensors must have padded shape (32, multiple_of_32)")
  if not 1 <= scores.pages <= OUTPUT_DEPTH:
    raise ValueError(f"softmax supports 1..{OUTPUT_DEPTH} column tiles")


def _read_scores(p, scores, input_cb):
  reader = p.brisc.init_cb(input_cb)
  noc = p.brisc.noc(0).initialize_from_firmware()
  for _ in range(2):
    for tile in p.brisc.range(scores.pages):
      reader.reserve_back()
      with noc.read_batch() as reads:
        reads.issue_dram(scores, tile, reader)
      reader.push_back()


def _write_probabilities(p, probabilities, output_cb, group_addr):
  writer = p.ncrisc.init_cb(output_cb)
  first_row = p.ncrisc.reg()
  p.ncrisc.load(first_row, group_addr)
  p.ncrisc.slli(first_row, first_row, 2)
  noc = p.ncrisc.noc(1).initialize_from_firmware()
  for tile in p.ncrisc.range(probabilities.pages):
    writer.wait_front()
    with noc.write_ack_batch() as writes:
      writes.issue_dram_tile_rows(
        probabilities, tile, writer, first_row, ROWS_PER_CORE,
      )
    writer.pop_front()


def softmax(scores: Buffer, probabilities: Buffer, *, cores=CORES):
  """Build stable softmax for tiled ``(32, T)`` scores.

  Scores, exponent numerators, reductions, and normalization math remain FP32.
  Only the final probabilities are rounded to BF16.
  """
  cores = tuple(cores)
  _check_buffers(scores, probabilities, cores)
  p = Program(cores, buffers=(scores, probabilities))

  input_cb = p.cb(DType.F32, min(2, scores.pages), name="scores")
  numerator_cbs = tuple(
    p.cb(DType.F32, pages, name=f"fp32_numerators_{index}")
    for index, pages in enumerate(_segments(scores.pages))
  )
  output_cb = p.cb(DType.BF16, probabilities.pages, name="probabilities")
  group_addr = p.scratch(4, name="row_group")
  barriers = tuple(p.scratch(12, name=name) for name in (
    "unpack_configured", "math_configured", "pack_configured",
    "numerators_ready", "output_configured",
  ))
  writes_done = p.scratch(4, name="writes_done")
  p.initialize_scratch(group_addr, range(len(cores)))
  for barrier in barriers:
    p.initialize_scratch_bytes(barrier, bytes(12))
  p.initialize_scratch(writes_done)

  _read_scores(p, scores, input_cb)
  p.brisc.wait32(writes_done, 1)

  input_unpack = p.trisc0.init_cb(input_cb)
  numerator_unpacks = tuple(p.trisc0.init_cb(cb) for cb in numerator_cbs)
  p.unpack.init(input_unpack, fp32_dest=True)
  p.unpack.tensix.sync()
  p.trisc0.risc_barrier(barriers[0], 3, 0)
  p.trisc0.risc_barrier(barriers[1], 3, 0)
  p.trisc0.risc_barrier(barriers[2], 3, 0)
  for _ in p.trisc0.range(scores.pages * 2):
    p.unpack.to_dst(input_unpack)
  p.unpack.finish_to_dst()
  p.trisc0.risc_barrier(barriers[3], 3, 0)
  p.trisc0.risc_barrier(barriers[4], 3, 0)
  for source, pages in zip(numerator_unpacks, _segments(scores.pages)):
    for _ in p.trisc0.range(pages):
      p.unpack.to_dst(source)
  p.unpack.finish_to_dst()

  p.trisc1.risc_barrier(barriers[0], 3, 1)
  p.math.initialize(fp32_dest=True)
  p.math.tensix.sync()
  base, sfpu = _row_base(p, group_addr), p.math.sfpu
  p.trisc1.risc_barrier(barriers[1], 3, 1)
  p.trisc1.risc_barrier(barriers[2], 3, 1)
  p.math.wait_for_direct_unpack()
  with sfpu.tile():
    _reduce_max(sfpu, base)
    sfpu.move(LReg.L0, LReg.L6)
  for _ in p.trisc1.range(scores.pages - 1):
    p.math.wait_for_direct_unpack()
    with sfpu.tile():
      _reduce_max(sfpu, base)
      sfpu.maximum_into(LReg.L6, LReg.L0)
  p.math.acquire_dst()
  p.math.wait_for_direct_unpack()
  with sfpu.tile():
    _exp_and_sum(sfpu, base)
    sfpu.move(LReg.L0, LReg.L7)
  p.math.publish_dst()
  for _ in p.trisc1.range(scores.pages - 1):
    p.math.acquire_dst()
    p.math.wait_for_direct_unpack()
    with sfpu.tile():
      _exp_and_sum(sfpu, base)
      sfpu.add_into(LReg.L7, LReg.L0)
    p.math.publish_dst()
  with sfpu.tile():
    sfpu.reciprocal_positive(
      LReg.L7, LReg.L7, maximum=8192, scratch=(0, 1, 2, 3, 4, 5),
    )
  p.trisc1.risc_barrier(barriers[3], 3, 1)
  p.trisc1.risc_barrier(barriers[4], 3, 1)
  for _ in p.trisc1.range(scores.pages):
    p.math.acquire_dst()
    p.math.wait_for_direct_unpack()
    with sfpu.tile():
      for chunk in GROUP_CHUNKS:
        sfpu.load_dst(LReg.L0, base, format=SfpuFormat.FP32, delta=chunk)
        sfpu.multiply(LReg.L0, LReg.L7, LReg.L0)
        sfpu.store_dst(LReg.L0, base, format=SfpuFormat.FP32, delta=chunk)
    p.math.publish_dst()
  p.math.tensix.sync()

  numerator_packs = tuple(p.trisc2.init_cb(cb) for cb in numerator_cbs)
  output_pack = p.trisc2.init_cb(output_cb)
  p.trisc2.risc_barrier(barriers[0], 3, 2)
  p.trisc2.risc_barrier(barriers[1], 3, 2)
  p.pack.init(numerator_packs[0], fp32_dest=True)
  p.trisc2.risc_barrier(barriers[2], 3, 2)
  for destination, pages in zip(numerator_packs, _segments(scores.pages)):
    p.pack.output_cb = destination
    for _ in p.trisc2.range(pages):
      _pack_one(p, destination)
  p.pack.tensix.sync()
  p.trisc2.risc_barrier(barriers[3], 3, 2)
  p.pack.init(output_pack, fp32_dest=True)
  p.trisc2.risc_barrier(barriers[4], 3, 2)
  for _ in p.trisc2.range(probabilities.pages):
    _pack_one(p, output_pack)
  p.pack.tensix.sync()

  _write_probabilities(p, probabilities, output_cb, group_addr)
  p.ncrisc.write32(writes_done, 1)
  p.ncrisc.fence()
  return p


def show(program):
  sizes = ", ".join(
    f"{role}={len(image)}" for role, image in program.kernels[program.cores[0]].items()
  )
  print(f"CBs={program.cbs}")
  print(f"kernel bytes: {sizes}")


def run_hardware(logical_t=3072, *, seed=0):
  import numpy as np
  from device import Device

  columns = (logical_t + TILE - 1) // TILE * TILE
  rng = np.random.default_rng(seed)
  scores_np = rng.normal(0, 2, (TILE, columns)).astype(np.float32)
  scores_np[:, logical_t:] = -np.inf
  numerator = np.exp(scores_np - np.max(scores_np, axis=1, keepdims=True), dtype=np.float32)
  reference = numerator / np.sum(numerator, axis=1, keepdims=True, dtype=np.float32)
  device = Device()
  try:
    device.init_device()
    scores = device.dram.buffer("scores", DType.F32, scores_np.shape, scores_np.shape)
    probabilities = device.dram.buffer(
      "probabilities", DType.BF16, scores_np.shape, scores_np.shape,
    )
    program = softmax(scores, probabilities)
    device.write(scores, scores.from_numpy(scores_np))
    stamps = device.run(program)
    elapsed = stamps[-1].us
    actual = probabilities.to_numpy(device.read(probabilities))
    actual64, reference64 = actual.astype(np.float64), reference.astype(np.float64)
    difference = actual64 - reference64
    max_abs = float(np.max(np.abs(difference)))
    rel_l2 = float(np.sqrt(np.sum(difference * difference) / np.sum(reference64 * reference64)))
    tail = float(np.max(np.abs(actual[:, logical_t:]))) if logical_t < columns else 0.0
  finally:
    device.close()

  if not np.isfinite(actual).all() or max_abs > 5e-3 or rel_l2 > 1e-2 or tail > 1e-6:
    raise AssertionError(
      f"softmax mismatch: max_abs={max_abs:.6g} rel_l2={rel_l2:.6g} "
      f"tail={tail:.6g}"
    )
  print(f"PASS softmax: shape=(32, {logical_t}) max_abs={max_abs:.6g} rel_l2={rel_l2:.6g}")
  print(f"kernel: {elapsed:.3f} us")
  print(f"88 us target: {'PASS' if elapsed < 88 else 'MISS'} ({88 - elapsed:+.3f} us)")
  show(program)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--run", action="store_true")
  parser.add_argument("--logical-t", type=int, default=3072)
  parser.add_argument("--seed", type=int, default=0)
  args = parser.parse_args()
  if not 1 <= args.logical_t <= OUTPUT_DEPTH * TILE:
    parser.error(f"--logical-t must be in [1, {OUTPUT_DEPTH * TILE}]")
  if args.run:
    return run_hardware(args.logical_t, seed=args.seed)
  columns = (args.logical_t + TILE - 1) // TILE * TILE
  dram = Dram()
  scores = dram.buffer("scores", DType.F32, (TILE, columns), (TILE, columns))
  probabilities = dram.buffer(
    "probabilities", DType.BF16, (TILE, columns), (TILE, columns),
  )
  show(softmax(scores, probabilities))


if __name__ == "__main__":
  main()
