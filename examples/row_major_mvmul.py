"""Row-major 64x16 @ 64x16.T using native MVMUL panels.

The two DRAM operands and the 64x64 DRAM result are all ordinary row-major
buffers.  The unpacker copies the left operand to SrcB unchanged and performs
four independent 16x16 transposes while loading the right operand to SrcA.
The math MOP then issues:

  SrcB[8x16] @ SrcA[16x16] -> Dst[8x16]

for all 8x4 output panels.  Finally, NCRISC scatters the four ordinary packed
32x32 Dst tiles into a dense row-major 64x64 output buffer.
"""

import argparse

import numpy as np

from asm import Cond
from device import Device
from fw.consts import TensixMMIO
from isa import R, Tensix as TT
from program import DType, Program
from ttk.cb import CB
from ttk.mop import LoopTemplate, Replay
from ttk.sync import Stall, Wait, stall, sync


M, K, N = 64, 16, 64
MVMUL_FLOPS = 2 * 8 * 16 * 16
SPATIAL_ISSUES = M // 8 * N // 16
FIDELITY_PHASES = 2
ISSUES_PER_GRAM = SPATIAL_ISSUES * FIDELITY_PHASES
USEFUL_FLOPS_PER_GRAM = 2 * M * N * K
DEVICE_HZ = 1_350_000_000


def bf16_truncate(values):
  values = np.asarray(values, dtype=np.float32)
  return ((values.view(np.uint32) >> 16) << 16).view(np.float32)


def _dst_rows_for_first_column_panel():
  """Dst offsets for output[:, 0:16], arranged as four 32x32 tiles."""
  rows = []
  for m_block in range(M // 8):
    tile_row = m_block // 4
    face_row = m_block % 4 // 2
    half_row = m_block & 1
    tile = tile_row * 2
    face = face_row * 2
    rows.append(tile * 64 + face * 16 + half_row * 8)
  return tuple(rows)


def _mvmul_replay(start, dst_rows, final_addr_mod):
  words = [
    TT.TTMVMUL(0, 0, 0 if index != len(dst_rows) - 1 else final_addr_mod, row)
    for index, row in enumerate(dst_rows)
  ]
  return Replay(start, words)


def row_major_gram_math(p, *, repeats, timing_l1):
  """Configure one MOP for a complete HiFi2 64x16 Gram operation."""
  fpu, k = p.fpu, p.trisc1
  fpu._wait_for_dst()
  fpu._configure_dst(0)

  # Within a 16-column output panel, walk all eight SrcB 8x16 blocks.
  fpu._set_addr_mod(0, srcb=8)

  # After columns 0:16 and 32:48, move to the next SrcA panel and to the
  # horizontally adjacent Dst face.  Dst_Cr remains the start of the current
  # pair of output-column panels.
  fpu._set_addr_mod(
    1, srca=16, srcb_clear=True, dest=16,
  )

  # After columns 16:32, advance Dst_Cr to the next pair of 32x32 tiles.
  fpu._set_addr_mod(
    2, srca=16, srcb_clear=True, dest=64, dest_carry=True,
  )

  # End fidelity phase zero.  Reset the spatial counters, select address
  # modifiers 4..7, and advance to fidelity phase one.
  fpu._set_addr_mod(
    3, srca_clear=True, srcb_clear=True, dest_clear=True,
    fidelity_increment=1, bias_increment=1,
  )

  # The upper modifier bank repeats the spatial schedule for phase one.
  fpu._set_addr_mod(4, srcb=8)
  fpu._set_addr_mod(
    5, srca=16, srcb_clear=True, dest=16,
  )
  fpu._set_addr_mod(
    6, srca=16, srcb_clear=True, dest=64, dest_carry=True,
  )

  # End phase one with every counter, including the extra modifier-bank bit
  # and fidelity phase, restored.  This makes the MOP safely repeatable.
  fpu._set_addr_mod(
    7, srca_clear=True, srcb_clear=True, dest_clear=True,
    fidelity_clear=True, bias_clear=True,
  )

  dst_rows = _dst_rows_for_first_column_panel()
  replay_a = _mvmul_replay(0, dst_rows, 1)
  replay_b = _mvmul_replay(8, dst_rows, 2)
  replay_c = _mvmul_replay(16, dst_rows, 3)

  # One MOP expands to A, B, A, C:
  #   A: columns  0:16, Dst += 16
  #   B: columns 16:32, Dst_Cr += 64
  #   A: columns 32:48, Dst += 16
  #   C: columns 48:64, reset the phase's counters
  #
  # Calling it twice selects modifier banks 0..3 and 4..7 respectively.
  fpu._mop.configure(LoopTemplate(
    outer=2, inner=1,
    loop=replay_a, alternate=replay_b,
    last=replay_c, outer_last=replay_b,
  ))
  sync(k)

  fpu._issue(TT.TTZEROACC(3, 1, 0, 1, 0))
  fpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))

  # Keep source-valid waits and initial Dst clearing outside the measured
  # interval.  The timing therefore covers the repeated MOP expansions and
  # matrix-unit completion, with only a fixed synchronization tail.
  stall(k, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
  stall(k, Stall.SYNC, Wait.MATH)
  sync(k)

  with k.scope():
    started, finished, elapsed = k.reg(3)
    k.read(started, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)

    for _ in k.range(repeats):
      fpu._mop.run()
      fpu._mop.run()

    stall(k, Stall.SYNC, Wait.MATH)
    sync(k)
    k.read(finished, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
    k.sub(elapsed, finished, started)
    k.write(timing_l1, elapsed)
    k.write(timing_l1 + 4, repeats)
    k.write(timing_l1 + 8, ISSUES_PER_GRAM)
    k.write(timing_l1 + 12, USEFUL_FLOPS_PER_GRAM)

  fpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  fpu.publish()


def scatter_packed_64x64(p, packed_cb, output):
  """Scatter four face-packed 32x32 tiles to a dense 64x64 DRAM buffer."""
  k, noc = p.ncrisc, p.ncrisc.noc
  CB.wait_front(k, packed_cb, 4)
  with k.scope():
    packed_base = k.reg()
    CB.get_read_ptr(k, packed_cb, packed_base)

    # A dense 64x64 Buffer consists of four consecutive 16x64 chunks.
    # For each chunk and 16-column block, copy sixteen 32-byte face rows.
    with noc.transaction() as transaction:
      for row_chunk in range(4):
        with k.scope():
          target_base, target_coordinate = noc._dram_tile(output, row_chunk)
          tile_row, face_row = divmod(row_chunk, 2)
          for column_chunk in range(4):
            tile_column, face_column = divmod(column_chunk, 2)
            packed_tile = tile_row * 2 + tile_column
            packed_face = face_row * 2 + face_column
            source_offset = (
              packed_tile * packed_cb.tile_size +
              packed_face * 16 * 16 * packed_cb.dtype.itemsize
            )
            with k.scope():
              source, target, rows = k.reg(3)
              k.li(source, source_offset)
              k.add(source, source, packed_base)
              k.li(target, column_chunk * 16 * output.dtype.itemsize)
              k.add(target, target, target_base)
              k.li(rows, 16)
              with k.loop(Cond(rows, "!=", R.ZERO)):
                transaction.write(
                  source, target, target_coordinate,
                  16 * output.dtype.itemsize, posted=False,
                )
                k.addi(source, source, 16 * output.dtype.itemsize)
                k.addi(target, target, N * output.dtype.itemsize)
                k.addi(rows, rows, -1)
  CB.pop_front(k, packed_cb, 4)


def write_timing(p, timing_l1, timing):
  noc = p.ncrisc.noc
  with p.ncrisc.scope():
    target, coordinate = noc._dram_tile(timing, 0)
    noc.write(timing_l1, target, coordinate, 16, posted=False)


def build_program(left, right, output, timing, *, repeats):
  p = Program(left.cores, left, right, output, timing, fp32_dst=True)
  left_cb = p.cb(DType.BF16, depth=1)
  right_cb = p.cb(DType.BF16, depth=1)
  packed_cb = p.cb(DType.BF16, depth=4)
  timing_l1 = p.l1(16, alignment=16)

  p.brisc.noc.read_into_cb(left, 0, left_cb)
  p.brisc.noc.read_into_cb(right, 0, right_cb)
  p.unpack.move_matmul(left_cb, right_cb, right_transpose=True)
  row_major_gram_math(p, repeats=repeats, timing_l1=timing_l1)
  p.pack.move_tiles(packed_cb, tiles=(0, 1, 2, 3))
  scatter_packed_64x64(p, packed_cb, output)
  write_timing(p, timing_l1, timing)
  return p


def make_inputs():
  left = np.arange(M * K, dtype=np.float32).reshape(M, K)
  # A different, visibly structured matrix makes panel/order mistakes obvious.
  right = (
    np.arange(M * K, dtype=np.float32).reshape(M, K)[:, ::-1] + 1
  )
  return left, right


def error_summary(actual, expected):
  absolute = np.abs(actual - expected)
  relative = absolute / np.maximum(np.abs(expected), 1.0)
  return absolute.max(), relative.max()


def run(benchmark_repeats):
  host_left, host_right = make_inputs()
  device = Device()
  try:
    device.init_device()
    core = (device.dram.cores[0],)
    left = device.dram.buffer(
      "row_major_left", DType.BF16, (M, K),
      cores=core,
    )
    right = device.dram.buffer(
      "row_major_right", DType.BF16, (M, K),
      cores=core,
    )
    validation_output = device.dram.buffer(
      "row_major_validation_output", DType.BF16, (M, N),
      cores=core,
    )
    validation_timing = device.dram.buffer(
      "row_major_validation_timing", DType.U32, (4,),
      cores=core,
    )
    benchmark_output = device.dram.buffer(
      "row_major_benchmark_output", DType.BF16, (M, N),
      cores=core,
    )
    benchmark_timing = device.dram.buffer(
      "row_major_benchmark_timing", DType.U32, (4,),
      cores=core,
    )

    left_bytes = left.from_numpy(host_left)
    right_bytes = right.from_numpy(host_right)
    stored_left = left.to_numpy(left_bytes)
    stored_right = right.to_numpy(right_bytes)
    device.write(left, left_bytes)
    device.write(right, right_bytes)

    validation = build_program(
      left, right, validation_output, validation_timing, repeats=1,
    )
    benchmark = build_program(
      left, right, benchmark_output, benchmark_timing,
      repeats=benchmark_repeats,
    )
    device.run(validation, benchmark, timeout=30.0)

    actual = validation_output.to_numpy(
      device.read(validation_output, timeout=30.0),
    )
    timing_words = validation_timing.to_numpy(
      device.read(validation_timing, timeout=30.0),
    )
    benchmark_words = benchmark_timing.to_numpy(
      device.read(benchmark_timing, timeout=30.0),
    )

    reference = bf16_truncate(stored_left @ stored_right.T)
    max_absolute, max_relative = error_summary(actual, reference)

    elapsed_cycles = int(benchmark_words[0])
    measured_repeats = int(benchmark_words[1])
    measured_issues = int(benchmark_words[2])
    measured_flops = int(benchmark_words[3])
    cycles_per_gram = elapsed_cycles / measured_repeats
    issues_per_cycle = measured_repeats * measured_issues / elapsed_cycles
    useful_tflops = (
      measured_repeats * measured_flops * DEVICE_HZ /
      elapsed_cycles / 1e12
    )
    ideal_tflops = USEFUL_FLOPS_PER_GRAM * DEVICE_HZ / (
      ISSUES_PER_GRAM * 1e12
    )

    np.set_printoptions(linewidth=180, suppress=True, precision=1)
    print("Dense row-major input shapes:")
    print(f"  left  {stored_left.shape}")
    print(f"  right {stored_right.shape}")
    print(f"  output {actual.shape}")
    print()
    print("left[0:2]:")
    print(stored_left[:2])
    print("right[0:2]:")
    print(stored_right[:2])
    print()
    print("hardware output[0:8, 0:8]:")
    print(actual[:8, :8])
    print("CPU BF16-truncated reference[0:8, 0:8]:")
    print(reference[:8, :8])
    print()
    print(f"validation timer: {int(timing_words[0])} cycles")
    print(f"max absolute error: {max_absolute:.1f}")
    print(f"max relative error: {max_relative:.6f}")
    print()
    print("MVMUL-only benchmark:")
    print(f"  repetitions:             {measured_repeats}")
    print(f"  MVMUL issues/Gram:       {measured_issues}")
    print(f"  elapsed cycles:          {elapsed_cycles}")
    print(f"  cycles/Gram:             {cycles_per_gram:.4f}")
    print(f"  MVMUL issues/cycle:      {issues_per_cycle:.6f}")
    print(f"  issue-slot utilization:  {issues_per_cycle * 100:.3f}%")
    print(f"  useful HiFi2 TFLOP/s:    {useful_tflops:.6f}")
    print(f"  ideal at 1.35 GHz:       {ideal_tflops:.6f} TFLOP/s")
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--benchmark-repeats", type=int, default=16,
  )
  args = parser.parse_args()
  if args.benchmark_repeats < 1:
    parser.error("--benchmark-repeats must be positive")
  run(args.benchmark_repeats)
