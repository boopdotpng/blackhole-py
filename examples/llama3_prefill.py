"""Llama 3 prefill kernels, built one layout-preserving stage at a time.

Prefill activations use a conventional two-dimensional tile grid.  Tile
``[token_block, feature_block]`` contains 32 tokens by 32 features.  This is
the layout consumed by the RMSNorm, projection, attention, and MLP kernels;
it is deliberately different from decode's two "flat" tiles per token.
"""

import argparse
import numpy as np

from device import Device
from fw.consts import TensixL1, TensixMMIO
from pcie import P100_WORKER_CORES
from program import Buffer, Const, DType, Program
from ttk.cb import CB
from ttk.fpu import Broadcast
from ttk.sfpu import SfpuFormat


PREFILL_BATCH = 1
PREFILL_TOKENS = 2048
EMBED_DIM = 2048
TILE_SIDE = 32
TOKEN_BLOCKS = PREFILL_TOKENS // TILE_SIDE
FEATURE_BLOCKS = EMBED_DIM // TILE_SIDE
PREFILL_CORES = P100_WORKER_CORES[:TOKEN_BLOCKS]

# Buffer currently describes sharding in terms of contiguous logical items.
# Represent the matrix explicitly as its tile grid so each core owns one
# token block and its 64 feature tiles.  The logical matrix is recovered with
# tile_grid_to_matrix().
PREFILL_TILE_GRID_SHAPE = (
  TOKEN_BLOCKS, FEATURE_BLOCKS, TILE_SIDE, TILE_SIDE,
)
PROFILE_WORDS = 16
PROFILE_SHAPE = (TOKEN_BLOCKS, PROFILE_WORDS)
PROFILE_MARKERS = (
  "brisc_start",
  "ids_ready",
  "first_issued",
  "first_ready",
  "gather_issued",
  "gather_done",
  "unpack_start",
  "unpack_done",
  "math_start",
  "math_done",
  "pack_start",
  "pack_done",
  "writer_start",
  "write_done",
)


def matrix_to_tile_grid(values):
  """Convert logical [2048, 2048] values to [token tile, feature tile, r, c]."""
  values = np.asarray(values)
  if values.shape != (PREFILL_TOKENS, EMBED_DIM):
    raise ValueError(
      f"prefill matrix must have shape {(PREFILL_TOKENS, EMBED_DIM)}",
    )
  return values.reshape(
    TOKEN_BLOCKS, TILE_SIDE, FEATURE_BLOCKS, TILE_SIDE,
  ).transpose(0, 2, 1, 3)


def tile_grid_to_matrix(values):
  """Convert [token tile, feature tile, r, c] values to logical [2048, 2048]."""
  values = np.asarray(values)
  if values.shape != PREFILL_TILE_GRID_SHAPE:
    raise ValueError(
      f"prefill tile grid must have shape {PREFILL_TILE_GRID_SHAPE}",
    )
  return values.transpose(0, 2, 1, 3).reshape(PREFILL_TOKENS, EMBED_DIM)


def _validate_embedding_buffers(
  token_ids: Buffer, embedding_weight: Buffer, output: Buffer,
  profile: Buffer | None = None,
):
  if (
    token_ids.dtype is not DType.U32 or
    token_ids.shape != (PREFILL_TOKENS,) or token_ids.axis is not None or
    not token_ids.global_address or token_ids.tilized
  ):
    raise ValueError(
      "prefill token IDs must be row-major global U32[2048]",
    )
  if (
    embedding_weight.dtype is not DType.BF16 or
    len(embedding_weight.shape) != 2 or
    embedding_weight.shape[1] != EMBED_DIM or
    embedding_weight.axis != 0 or
    embedding_weight.tiles_per_item != 2 or
    not embedding_weight.global_address or embedding_weight.tilized
  ):
    raise ValueError(
      "prefill embedding weight must be row-major global "
      "BF16[vocabulary, 2048]",
    )
  if (
    output.dtype is not DType.BF16 or
    output.shape != PREFILL_TILE_GRID_SHAPE or output.axis != 0 or
    output.tilized is not True or output.cores != PREFILL_CORES or
    output.item_counts != (1,) * TOKEN_BLOCKS or
    output.tiles_per_item != FEATURE_BLOCKS
  ):
    raise ValueError(
      "prefill embedding output must be a face-tilized "
      "[64, 64, 32, 32] tile grid, sharded one token block per core",
    )
  if profile is not None and (
    profile.dtype is not DType.U32 or profile.shape != PROFILE_SHAPE or
    profile.axis != 0 or profile.tilized or profile.cores != PREFILL_CORES or
    profile.item_counts != (1,) * TOKEN_BLOCKS
  ):
    raise ValueError(
      "prefill profile must be row-major U32[64, 16], "
      "sharded one row per prefill core",
    )


def _mark(kernel, profile_l1, slot):
  if profile_l1 is None:
    return
  with kernel.scope():
    cycles = kernel.reg()
    kernel.read(cycles, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
    kernel.write(profile_l1 + slot * 4, cycles)


def prefill_embedding(
  token_ids: Buffer, embedding_weight: Buffer, output: Buffer,
  profile: Buffer | None = None,
) -> Program:
  """Gather row-major embeddings into 32-token by 32-feature output tiles.

  Each of 64 cores owns 32 consecutive tokens.  BRISC gathers their 4096-byte
  embedding rows into one contiguous 128 KiB row-major CB.  Blackhole's
  fast-tilize UNPACK/MATH/PACK path transforms four feature tiles per chunk,
  avoiding both scalar data copies and the ordinary tilizer's SrcA write
  hazard.
  """
  _validate_embedding_buffers(
    token_ids, embedding_weight, output, profile,
  )

  token_starts = Const(
    "token_start", tuple(range(0, PREFILL_TOKENS, TILE_SIDE)),
  )
  parameters = (
    token_ids, embedding_weight, output, token_starts,
    *((profile,) if profile is not None else ()),
  )
  p = Program(
    output.cores, *parameters,
    l1_range=(TensixL1.KERNEL_CACHE_END, TensixL1.RUNTIME_PARAM_BASE),
  )
  profile_l1 = (
    p.l1(PROFILE_WORDS * 4, alignment=64)
    if profile is not None else None
  )
  ids_l1 = p.l1(token_ids.tile_size, alignment=64)
  row_major_cb = p.cb(DType.BF16, depth=2 * TILE_SIDE)
  output_cb = p.cb(DType.BF16, depth=8)

  _mark(p.brisc, profile_l1, 0)
  with p.brisc.scope():
    token_start, ids_tile, ids_within, ids_base = p.brisc.reg(4)
    p.brisc.read(token_start, p.param_addr(token_starts))
    p.brisc.li(ids_base, ids_l1)
    p.brisc.srli(ids_tile, token_start, 10)
    p.brisc.andi(ids_within, token_start, 1023)
    p.brisc.noc.read_tile(token_ids, ids_tile, ids_l1)
    _mark(p.brisc, profile_l1, 1)

    for half in range(2):
      CB.reserve_back(p.brisc, row_major_cb, FEATURE_BLOCKS // 2)
      with p.brisc.scope():
        row_major = p.brisc.reg(
          exclude=(token_start, ids_tile, ids_within),
        )
        CB.get_write_ptr(p.brisc, row_major_cb, row_major)
        with p.brisc.noc.transaction() as transaction:
          for row in p.brisc.range(TILE_SIDE):
            with p.brisc.scope():
              id_address, token = p.brisc.reg(
                2, exclude=(token_start, ids_tile, ids_within,
                            ids_base, row_major, row),
              )
              p.brisc.add(id_address, ids_within, row)
              p.brisc.slli(id_address, id_address, 2)
              p.brisc.add(id_address, id_address, ids_base)
              p.brisc.lw(token, id_address)

              with p.brisc.scope():
                source_tile, target = p.brisc.reg(
                  2, exclude=(token, row_major, row),
                )
                p.brisc.slli(source_tile, token, 1)
                if half:
                  p.brisc.addi(source_tile, source_tile, 1)
                source_address, source_coordinate = p.brisc.noc._dram_tile(
                  embedding_weight, source_tile,
                )
                p.brisc.slli(target, row, 11)
                p.brisc.add(target, target, row_major)
                transaction.read(
                  source_address, source_coordinate, target,
                  embedding_weight.tile_size,
                )
          _mark(p.brisc, profile_l1, 2 if half == 0 else 4)
      CB.push_back(p.brisc, row_major_cb, FEATURE_BLOCKS // 2)
      _mark(p.brisc, profile_l1, 3 if half == 0 else 5)

  chunks = FEATURE_BLOCKS // 4
  _mark(p.trisc0, profile_l1, 6)
  p.unpack.fast_tilize_blocks(
    row_major_cb, width_tiles=FEATURE_BLOCKS // 2, blocks=2,
  )
  _mark(p.trisc0, profile_l1, 7)
  _mark(p.trisc1, profile_l1, 8)
  p.fpu.fast_tilize(chunks=chunks)
  _mark(p.trisc1, profile_l1, 9)
  _mark(p.trisc2, profile_l1, 10)
  p.pack.fast_tilize(output_cb, chunks=chunks)
  _mark(p.trisc2, profile_l1, 11)

  _mark(p.ncrisc, profile_l1, 12)
  for first_tile in range(0, FEATURE_BLOCKS, output_cb.depth):
    p.ncrisc.noc.write_tiles_from_cb(
      output_cb, output,
      range(first_tile, first_tile + output_cb.depth),
    )
  _mark(p.ncrisc, profile_l1, 13)
  if profile is not None:
    with p.ncrisc.scope():
      target_address, target_coordinate = p.ncrisc.noc._dram_tile(profile, 0)
      p.ncrisc.noc.write(
        profile_l1, target_address, target_coordinate,
        PROFILE_WORDS * 4, posted=False,
      )
  return p


def _validate_rmsnorm_buffers(
  x: Buffer, weight: Buffer, output: Buffer,
):
  for name, buffer in (("input", x), ("output", output)):
    if (
      buffer.dtype is not DType.BF16 or
      buffer.shape != PREFILL_TILE_GRID_SHAPE or buffer.axis != 0 or
      buffer.tilized is not True or buffer.cores != PREFILL_CORES or
      buffer.item_counts != (1,) * TOKEN_BLOCKS or
      buffer.tiles_per_item != FEATURE_BLOCKS
    ):
      raise ValueError(
        f"prefill RMSNorm {name} must be a face-tilized "
        "[64, 64, 32, 32] tile grid with one token block per core",
      )
  if (
    weight.dtype is not DType.BF16 or weight.shape != (EMBED_DIM,) or
    weight.axis is not None or weight.tiles != 2 or
    not weight.global_address or not weight.tilized
  ):
    raise ValueError(
      "prefill RMSNorm weight must be host-tilized global BF16[2048]",
    )


def prefill_rmsnorm(
  x: Buffer, weight: Buffer, output: Buffer, *, epsilon=1e-5,
) -> Program:
  """Normalize 32 tokens independently on each of 64 token-block cores.

  The math pipe accumulates two 32-tile groups of elementwise squares, adds
  those partials, then row-reduces the resulting 32 columns. A second input
  stream applies the 32 row scales and the selected row of the two-tile gamma
  vector.
  """
  _validate_rmsnorm_buffers(x, weight, output)
  if not isinstance(epsilon, (int, float)) or epsilon <= 0:
    raise ValueError("RMSNorm epsilon must be positive")

  p = Program(
    x.cores, x, weight, output, fp32_dst=True,
    l1_range=(TensixL1.KERNEL_CACHE_END, TensixL1.RUNTIME_PARAM_BASE),
  )
  gamma_l1 = p.l1(weight.tiles * weight.tile_size, alignment=64)
  ones_l1 = p.l1_constant(b"\x80\x3f" * TILE_SIDE * TILE_SIDE)
  input_cb = p.cb(DType.BF16, depth=4)
  partial_a_cb = p.cb(DType.BF16, depth=1)
  partial_b_cb = p.cb(DType.BF16, depth=1)
  square_sum_cb = p.cb(DType.BF16, depth=2)
  scale_column_cb = p.cb(DType.BF16, depth=1)
  scale_cb = p.cb(DType.BF16, depth=FEATURE_BLOCKS)
  scaled_cb = p.cb(DType.BF16, depth=4)
  output_cb = p.cb(DType.BF16, depth=8)

  p.brisc.noc.read_tiles(weight, tuple(
    (tile, gamma_l1 + tile * weight.tile_size)
    for tile in range(weight.tiles)
  ))
  # Pass one feeds the square/reduction pipeline. Pass two naturally blocks
  # behind the four-tile CB until the scale becomes available.
  for _ in range(2):
    for group in p.brisc.range(FEATURE_BLOCKS // input_cb.depth):
      with p.brisc.scope():
        first, second, third, fourth = p.brisc.reg(4, exclude=group)
        p.brisc.slli(first, group, 2)
        p.brisc.addi(second, first, 1)
        p.brisc.addi(third, first, 2)
        p.brisc.addi(fourth, first, 3)
        p.brisc.noc.read_tiles_into_cb(
          x, (first, second, third, fourth), input_cb,
        )

  row_scaler = p.ops._row_scaler_address()
  with p.trisc0.scope():
    for _ in p.trisc0.range(FEATURE_BLOCKS // 2):
      p.unpack.move_pair_same(input_cb)
    for _ in p.trisc0.range(FEATURE_BLOCKS // 2):
      p.unpack.move_pair_same(input_cb)
    p.unpack.move_pair(partial_a_cb, partial_b_cb)
    p.unpack.move_row_reduce(
      square_sum_cb, row_scaler, maximum=False,
    )
    p.unpack.move_l1_cb_rows(ones_l1, scale_column_cb)
    for feature_tile in p.trisc0.range(FEATURE_BLOCKS):
      p.unpack.move_pair(input_cb, scale_cb)
      with p.trisc0.scope():
        gamma_address, row, offset = p.trisc0.reg(
          3, exclude=feature_tile,
        )
        p.trisc0.li(gamma_address, gamma_l1)
        p.trisc0.srli(offset, feature_tile, 5)
        p.trisc0.slli(offset, offset, 11)
        p.trisc0.add(gamma_address, gamma_address, offset)
        p.trisc0.andi(row, feature_tile, 31)
        p.trisc0.srli(offset, row, 4)
        p.trisc0.slli(offset, offset, 10)
        p.trisc0.add(gamma_address, gamma_address, offset)
        p.trisc0.andi(row, row, 15)
        p.trisc0.slli(row, row, 5)
        p.trisc0.add(gamma_address, gamma_address, row)
        p.unpack.move_l1_pair_row_broadcast(
          scaled_cb, gamma_address,
        )

  with p.trisc1.scope():
    p.fpu.binary("mul", dst_tile=0)
    for _ in p.trisc1.range(FEATURE_BLOCKS // 2 - 1):
      p.fpu.binary("mul", dst_tile=0, accumulate=True)
    p.fpu.publish()
    p.fpu.binary("mul", dst_tile=0)
    for _ in p.trisc1.range(FEATURE_BLOCKS // 2 - 1):
      p.fpu.binary("mul", dst_tile=0, accumulate=True)
    p.fpu.publish()
    p.fpu.binary("add", dst_tile=0).publish()
    p.fpu.reduce_row_sum(dst_tile=0)

    builder = p.sfpu.program()
    scale = builder.load(format=SfpuFormat.FP32)
    builder.mul_scalar(scale, 1.0 / EMBED_DIM)
    builder.add_scalar(scale, float(epsilon))
    builder.rsqrt_positive(scale)
    builder.store(scale, format=SfpuFormat.FP32)
    p.sfpu.map(
      builder.finish(), tile=0, region="column",
    ).publish()
    p.fpu.binary(
      "mul", dst_tile=0, broadcast=Broadcast.COLUMN,
    ).publish()

    for _ in p.trisc1.range(FEATURE_BLOCKS):
      p.fpu.binary("mul", dst_tile=0).publish()
      p.fpu.binary(
        "mul", dst_tile=0, broadcast=Broadcast.ROW,
      ).publish()

  with p.trisc2.scope():
    p.pack.move(partial_a_cb, tile=0)
    p.pack.move(partial_b_cb, tile=0)
    p.pack.move(square_sum_cb, tile=0)
    p.pack.move(scale_column_cb, tile=0)
    p.pack.move_repeated(
      scale_cb, tile=0, count=FEATURE_BLOCKS,
    )
    for _ in p.trisc2.range(FEATURE_BLOCKS):
      p.pack.move(scaled_cb, tile=0)
      p.pack.move(output_cb, tile=0)

  for group in p.ncrisc.range(FEATURE_BLOCKS // output_cb.depth):
    with p.ncrisc.scope():
      first = p.ncrisc.reg(exclude=group)
      p.ncrisc.slli(first, group, 3)
      with p.ncrisc.scope():
        tiles = p.ncrisc.reg(output_cb.depth, exclude=(group, first))
        for offset, tile in enumerate(tiles):
          if offset:
            p.ncrisc.addi(tile, first, offset)
          else:
            p.ncrisc.mv(tile, first)
        p.ncrisc.noc.write_tiles_from_cb(
          output_cb, output, tiles,
        )
  return p


def _print_profile(values):
  values = np.asarray(values, dtype=np.uint32)
  raw = values[:, :len(PROFILE_MARKERS)].astype(np.int64)
  elapsed = (raw - raw[:, :1] + (1 << 31)) % (1 << 32) - (1 << 31)
  elapsed_us = elapsed / 1350.0
  print("per-core stage boundaries from BRISC entry (us):")
  for index, name in enumerate(PROFILE_MARKERS):
    samples = elapsed_us[:, index]
    print(
      f"  {name:12s} "
      f"p50={np.percentile(samples, 50):7.3f} "
      f"p95={np.percentile(samples, 95):7.3f} "
      f"max={samples.max():7.3f}",
    )
  print("per-core intervals (us):")
  intervals = (
    ("ids read", 0, 1),
    ("first issue", 1, 2),
    ("first drain", 2, 3),
    ("second issue", 3, 4),
    ("second drain", 4, 5),
    ("tilize tail", 5, 11),
    ("write tail", 11, 13),
    ("worker total", 0, 13),
  )
  for name, start, end in intervals:
    samples = elapsed_us[:, end] - elapsed_us[:, start]
    print(
      f"  {name:12s} "
      f"p50={np.percentile(samples, 50):7.3f} "
      f"p95={np.percentile(samples, 95):7.3f} "
      f"max={samples.max():7.3f}",
    )


def run_hardware(vocabulary=256, *, profile_enabled=False):
  if vocabulary <= 0:
    raise ValueError("validation vocabulary must be positive")

  device = Device()
  try:
    device.init_device()
    token_ids = device.dram.buffer(
      "prefill_token_ids", DType.U32, (PREFILL_TOKENS,), axis=None,
      global_address=True, tilized=False,
    )
    embedding_weight = device.dram.buffer(
      "prefill_embedding_weight", DType.BF16, (vocabulary, EMBED_DIM),
      axis=0, global_address=True, tilized=False,
    )
    output = device.dram.buffer(
      "prefill_embedding_output", DType.BF16, PREFILL_TILE_GRID_SHAPE,
      axis=0, cores=PREFILL_CORES,
    )
    profile = (
      device.dram.buffer(
        "prefill_embedding_profile", DType.U32, PROFILE_SHAPE,
        axis=0, cores=PREFILL_CORES, tilized=False,
      )
      if profile_enabled else None
    )

    ids = (
      np.arange(PREFILL_TOKENS, dtype=np.uint32) * np.uint32(73) + 19
    ) % np.uint32(vocabulary)
    rng = np.random.default_rng(0)
    weights = rng.standard_normal(
      (vocabulary, EMBED_DIM), dtype=np.float32,
    )
    ids_data = token_ids.from_numpy(ids)
    weight_data = embedding_weight.from_numpy(weights)
    quantized_weights = embedding_weight.to_numpy(weight_data)
    expected = output.from_numpy(
      matrix_to_tile_grid(quantized_weights[ids]),
    )

    device.write(token_ids, ids_data)
    device.write(embedding_weight, weight_data)
    if profile is not None:
      device.write(
        profile,
        profile.from_numpy(np.zeros(PROFILE_SHAPE, dtype=np.uint32)),
      )
    device.queue(prefill_embedding(
      token_ids, embedding_weight, output, profile,
    ))
    readback = device.queue_read(output)
    profile_readback = (
      device.queue_read(profile) if profile is not None else None
    )
    timestamps = device.run(timeout=30.0)
    actual = readback.result()
    if actual != expected:
      mismatch = next(
        index for index, pair in enumerate(zip(actual, expected))
        if pair[0] != pair[1]
      )
      raise AssertionError(
        f"prefill embedding mismatch at byte {mismatch}: "
        f"{actual[mismatch]:02x} != {expected[mismatch]:02x}",
      )

    print("PASS prefill embedding")
    print("logical output: BF16[2048, 2048]")
    print("tile layout: [64 token blocks, 64 feature blocks, 32, 32]")
    print(f"kernel: {timestamps[-1].us:.3f} us")
    if profile_readback is not None:
      _print_profile(profile.to_numpy(profile_readback.result()))
  finally:
    device.close()


def run_rmsnorm_hardware(*, epsilon=1e-5, single_core=False):
  device = Device()
  try:
    device.init_device()
    if single_core and hasattr(device.cq, "submit"):
      simulator_submit = device.cq.submit
      device.cq.submit = lambda commands: simulator_submit(
        commands, timeout=10.0,
      )
    x = device.dram.buffer(
      "prefill_rmsnorm_input", DType.BF16, PREFILL_TILE_GRID_SHAPE,
      axis=0, cores=PREFILL_CORES,
    )
    # Gamma remains in the ordinary host-tilized format. It is a global
    # two-tile vector, fetched once into persistent L1 by every worker.
    weight = device.dram.buffer(
      "prefill_rmsnorm_weight", DType.BF16, (EMBED_DIM,),
      axis=None, global_address=True,
    )
    output = device.dram.buffer(
      "prefill_rmsnorm_output", DType.BF16, PREFILL_TILE_GRID_SHAPE,
      axis=0, cores=PREFILL_CORES,
    )

    rng = np.random.default_rng(1)
    input_matrix = rng.standard_normal(
      (PREFILL_TOKENS, EMBED_DIM), dtype=np.float32,
    ) * np.float32(0.5)
    gamma = (
      np.float32(1.0) +
      rng.standard_normal(EMBED_DIM, dtype=np.float32) * np.float32(0.1)
    )
    input_data = x.from_numpy(matrix_to_tile_grid(input_matrix))
    weight_data = weight.from_numpy(gamma)
    quantized_input = tile_grid_to_matrix(x.to_numpy(input_data))
    quantized_gamma = weight.to_numpy(weight_data)
    mean_square = np.mean(
      quantized_input * quantized_input, axis=1, dtype=np.float32,
    )
    expected = (
      quantized_input /
      np.sqrt(mean_square[:, None] + np.float32(epsilon)) *
      quantized_gamma[None, :]
    )

    device.write(x, input_data)
    device.write(weight, weight_data)
    program = prefill_rmsnorm(
      x, weight, output, epsilon=epsilon,
    )
    if single_core:
      # Full-device ttsim is slower than its fixed submission timeout. Keep
      # the production metadata/layout, but execute the identical image on
      # the first shard for cycle-level simulator validation.
      program._cores = program.cores[:1]
    device.queue(program)
    readback = device.queue_read(output)
    timestamps = device.run(timeout=30.0)

    actual = tile_grid_to_matrix(output.to_numpy(readback.result()))
    if not np.all(np.isfinite(actual)):
      bad = tuple(np.argwhere(~np.isfinite(actual))[0])
      raise AssertionError(
        f"prefill RMSNorm produced a non-finite value at {bad}: "
        f"{actual[bad]}",
      )
    checked_tokens = TILE_SIDE if single_core else PREFILL_TOKENS
    actual = actual[:checked_tokens]
    expected = expected[:checked_tokens]
    absolute_error = np.abs(actual - expected)
    relative_error = absolute_error / np.maximum(np.abs(expected), 1e-3)
    if not np.allclose(actual, expected, rtol=3e-2, atol=2e-2):
      bad = np.unravel_index(np.argmax(absolute_error), actual.shape)
      raise AssertionError(
        f"prefill RMSNorm mismatch at {bad}: "
        f"actual={actual[bad]:.7g}, expected={expected[bad]:.7g}, "
        f"max_abs={absolute_error[bad]:.7g}, "
        f"max_rel={relative_error.max():.7g}",
      )

    print("PASS prefill RMSNorm")
    print("logical input/output: BF16[2048, 2048]")
    print("weight: host-tilized global BF16[2048] (2 tiles)")
    print(
      f"error: max_abs={absolute_error.max():.7g}, "
      f"p99_abs={np.percentile(absolute_error, 99):.7g}",
    )
    print(f"kernel: {timestamps[-1].us:.3f} us")
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--operation", choices=("embedding", "rmsnorm"), default="embedding",
    help="prefill kernel to validate",
  )
  parser.add_argument(
    "--vocabulary", type=int, default=256,
    help="number of synthetic embedding rows used for validation",
  )
  parser.add_argument(
    "--profile", action="store_true",
    help="record per-core wall-clock markers for each pipeline stage",
  )
  parser.add_argument(
    "--single-core", action="store_true",
    help=argparse.SUPPRESS,
  )
  args = parser.parse_args()
  if args.operation == "embedding":
    run_hardware(args.vocabulary, profile_enabled=args.profile)
  else:
    run_rmsnorm_hardware(single_core=args.single_core)
