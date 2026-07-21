import argparse
import numpy as np
import struct

from device import Device
from program import Buffer, Const, DType, Program
from isa import R, Tensix as TT
from ttk.sfpu import LaneConfig, LReg, SfpuFormat, SfpuProgram
from ttk.sync import Sem, SemWait, Stall, Wait, sem_wait, stall
from ttk.unpack import UnpackTarget


VOCAB_SIZE = 128256
EMBED_DIM = 2048
PREFILL_BUCKET = 1024
RMSNORM_BUCKETS = (1, 128, 256, 512, 1024)
EMBEDDING_TILES = EMBED_DIM // 1024
LLAMA_CORES = 118
TOKENS_PER_CORE, NINE_TOKEN_CORES = divmod(PREFILL_BUCKET, LLAMA_CORES)
CORE_TOKEN_COUNTS = (
  (TOKENS_PER_CORE + 1,) * NINE_TOKEN_CORES +
  (TOKENS_PER_CORE,) * (LLAMA_CORES - NINE_TOKEN_CORES)
)


def _rmsnorm_bucket(valid_s):
  if not 0 < valid_s <= PREFILL_BUCKET:
    raise ValueError(f"valid_s must be in 1..{PREFILL_BUCKET}")
  return next(bucket for bucket in RMSNORM_BUCKETS if valid_s <= bucket)


def _token_counts(items, cores):
  per_core, extra = divmod(items, cores)
  return tuple(
    per_core + (index < extra) for index in range(cores)
  )


def _sfpu_float_words(register, value):
  bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
  return (
    TT.TTSFPLOADI(register, 10, bits & 0xffff),
    TT.TTSFPLOADI(register, 8, bits >> 16),
  )


def _sfpu_add(words, left, right, output):
  words.extend((TT.TTSFPADD(LReg.ONE, left, right, output, 0), TT.TTSFPNOP()))


def _sfpu_mul(words, left, right, output, modifier=0):
  words.extend((TT.TTSFPMUL(left, right, LReg.ZERO, output, modifier), TT.TTSFPNOP()))


def _rms_square_accumulate(*, reset):
  setup = _sfpu_float_words(LReg.L7, 0.0) if reset else ()
  return SfpuProgram(tuple(setup), (
    TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0), TT.TTSFPNOP(),
    TT.TTSFPMUL(LReg.L0, LReg.L0, LReg.ZERO, LReg.L0, 0), TT.TTSFPNOP(),
    TT.TTSFPADD(LReg.ONE, LReg.L7, LReg.L0, LReg.L7, 0), TT.TTSFPNOP(),
  ))


def _rms_finalize_scale():
  """Reduce 32 accumulator lanes and leave reciprocal RMS in L0."""
  words = [
    TT.TTSFPMOV(0, LReg.L7, LReg.L0, 0), TT.TTSFPNOP(),
    TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0), TT.TTSFPNOP(),
  ]
  for _ in range(7):
    words.extend((
      TT.TTSFPSHFT2(0, LReg.L0, LReg.L2, 3), TT.TTSFPNOP(),
      TT.TTSFPADD(LReg.ONE, LReg.L1, LReg.L2, LReg.L1, 0), TT.TTSFPNOP(),
      TT.TTSFPMOV(0, LReg.L2, LReg.L0, 0), TT.TTSFPNOP(),
    ))
  words.extend((TT.TTSFPMOV(0, LReg.L1, LReg.L0, 0), TT.TTSFPNOP()))
  # Copy the four eight-lane row sums, then transpose the four identical
  # registers. L0..L3 become broadcasts of rows 0..3 respectively.
  for register in (LReg.L1, LReg.L2, LReg.L3):
    words.extend((TT.TTSFPMOV(0, LReg.L0, register, 0), TT.TTSFPNOP()))
  words.extend((TT.TTSFPTRANSP(0, 0, 0, 0), TT.TTSFPNOP()))
  for register in (LReg.L1, LReg.L2, LReg.L3):
    _sfpu_add(words, LReg.L0, register, LReg.L0)

  words.extend(_sfpu_float_words(LReg.L4, 1.0 / EMBED_DIM))
  _sfpu_mul(words, LReg.L0, LReg.L4, LReg.L0)
  words.extend(_sfpu_float_words(LReg.L4, 1e-5))
  _sfpu_add(words, LReg.L0, LReg.L4, LReg.L0)

  # Accurate Blackhole reciprocal square root for finite positive FP32 L0.
  x, y, temporary, c1, c2, half = (
    LReg.L6, LReg.L1, LReg.L2, LReg.L3, LReg.L4, LReg.L5,
  )
  words.extend((
    TT.TTSFPMOV(0, LReg.L0, x, 0), TT.TTSFPNOP(),
    TT.TTSFPMOV(0, x, y, 0), TT.TTSFPNOP(),
    TT.TTSFPSHFT(0xfff, LReg.ZERO, y, 1), TT.TTSFPNOP(),
  ))
  magic = 0x5f1110a0
  words.extend((
    TT.TTSFPLOADI(temporary, 10, magic & 0xffff),
    TT.TTSFPLOADI(temporary, 8, magic >> 16),
    TT.TTSFPIADD(0, temporary, y, 6), TT.TTSFPNOP(),
  ))
  _sfpu_mul(words, x, y, temporary)
  _sfpu_mul(words, y, temporary, temporary, 1)
  words.extend(_sfpu_float_words(c1, 2.2825186))
  words.extend(_sfpu_float_words(c2, 2.2533049))
  _sfpu_add(words, c2, temporary, c2)
  words.extend((TT.TTSFPMAD(temporary, c2, c1, temporary, 0), TT.TTSFPNOP()))
  _sfpu_mul(words, y, temporary, y)
  _sfpu_mul(words, x, y, temporary)
  _sfpu_mul(words, y, temporary, temporary, 1)
  _sfpu_add(words, LReg.ONE, temporary, temporary)
  words.extend(_sfpu_float_words(half, 0.5))
  _sfpu_mul(words, y, half, half)
  words.extend((TT.TTSFPMAD(temporary, half, y, LReg.L0, 0), TT.TTSFPNOP()))
  return SfpuProgram((), tuple(words))


def _rms_apply_weight():
  """Apply the live FP32 RMS scale and the gamma tile two Dst slots ahead."""
  nop = TT.TTSFPNOP()
  return SfpuProgram((), (
    TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, 0),
    TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, 128), nop, nop,
    TT.TTSFPMUL(LReg.L1, LReg.L0, LReg.ZERO, LReg.L1, 0), nop, nop, nop,
    TT.TTSFPMUL(LReg.L1, LReg.L2, LReg.ZERO, LReg.L1, 0), nop, nop, nop,
    TT.TTSFPSTORE(LReg.L1, SfpuFormat.FP32, 7, 0), nop,
  ))


def _rms_map_acquired(sfpu, program):
  start, body = sfpu._prepare(program)
  for word in program.setup_words: sfpu._issue(word)
  if start is not None: sfpu._configure_replay_mop(start, len(body))
  sfpu._run_faces(start, body, 4)
  sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _rms_select_tile(sfpu, tile):
  sfpu._configure_dst(tile, LaneConfig())
  stall(sfpu.k, Stall.SFPU, Wait.MATH)


def _rmsnorm_one_token(sfpu):
  """Normalize Dst 0/1 and apply gamma from Dst 2/3, all in FP32."""
  sem_wait(
    sfpu.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
    Stall.SYNC | Stall.MATH | Stall.SFPU,
  )
  _rms_select_tile(sfpu, 0)
  _rms_map_acquired(sfpu, _rms_square_accumulate(reset=True))
  _rms_select_tile(sfpu, 1)
  _rms_map_acquired(sfpu, _rms_square_accumulate(reset=False))
  for word in _rms_finalize_scale().words: sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)

  apply = _rms_apply_weight()
  _rms_select_tile(sfpu, 0)
  _rms_map_acquired(sfpu, apply)
  _rms_select_tile(sfpu, 1)
  _rms_map_acquired(sfpu, apply)
  sfpu.publish()


def _load_local_count(kernel, program, valid_s, token_start,
                      token_capacity, count, start):
  """Emit count = clamp(valid_s - token_start, 0, token_capacity)."""
  kernel.read(start, program.param_addr(token_start))
  with kernel.scope():
    valid, capacity = kernel.reg(2, exclude=(count, start))
    kernel.read(valid, program.param_addr(valid_s))
    kernel.li(capacity, token_capacity)
    kernel.li(count, 0)
    done = kernel._new_label("embedding_local_count_done")
    kernel.bgeu(start, valid, done)
    kernel.sub(count, valid, start)
    kernel.bltu(count, capacity, done)
    kernel.mv(count, capacity)
    kernel.label(done)


def _load_tiled_u32(kernel, tile_l1, logical_index, output):
  """Load a logical element from a 32x32 face-tilized U32 tile in L1."""
  # Physical face order is TL, TR, BL, BR, with 16x16 elements per face.
  with kernel.scope():
    row, column, physical, scratch, address = kernel.reg(
      5, exclude=(logical_index, output),
    )
    kernel.srli(row, logical_index, 5)
    kernel.andi(column, logical_index, 31)

    kernel.srli(scratch, row, 4)
    kernel.slli(physical, scratch, 9)     # bottom faces start at element 512
    kernel.srli(scratch, column, 4)
    kernel.slli(scratch, scratch, 8)     # right faces start at element 256
    kernel.add(physical, physical, scratch)
    kernel.andi(scratch, row, 15)
    kernel.slli(scratch, scratch, 4)
    kernel.add(physical, physical, scratch)
    kernel.andi(scratch, column, 15)
    kernel.add(physical, physical, scratch)

    kernel.slli(physical, physical, 2)   # U32 byte offset
    kernel.li(address, tile_l1)
    kernel.add(address, address, physical)
    kernel.lw(output, address)


def _specialize_token_counts(build, cores, token_counts):
  """Combine compile-time loop-count variants into one heterogeneous launch."""
  variants = {count: build(count) for count in sorted(set(token_counts))}
  lowered = {count: program.lower() for count, program in variants.items()}
  combined = variants[max(variants)]
  combined._kernels = {
    core: dict(lowered[count][core])
    for core, count in zip(cores, token_counts)
  }
  return combined


def _embedding_program(
  token_ids, embedding_weight, output, *, token_capacity,
):
  valid_s = Const("valid_s", PREFILL_BUCKET)
  token_start = Const("token_start", output.item_starts)
  p = Program(
    output.cores, token_ids, embedding_weight, output, valid_s, token_start,
  )

  # BRISC reads the one token-ID tile once, then produces embedding tiles.
  # Four CB slots hold two complete embedding rows, allowing BRISC/NCRISC to
  # overlap once the NOC helpers support multiple outstanding transactions.
  ids_l1 = p.l1(token_ids.tile_size, alignment=16)
  embedding_cb = p.cb(DType.BF16, depth=4)

  brisc = p.brisc
  with brisc.scope():
    local_count, start = brisc.reg(2)
    _load_local_count(
      brisc, p, valid_s, token_start, token_capacity, local_count, start,
    )
    finished = brisc._new_label("embedding_brisc_finished")
    brisc.beq(local_count, R.ZERO, finished)
    brisc.noc.read_tile(token_ids, 0, ids_l1)

    for local_token in brisc.range(local_count):
      with brisc.scope():
        global_token, token_id = brisc.reg(2)
        brisc.add(global_token, start, local_token)
        _load_tiled_u32(brisc, ids_l1, global_token, token_id)
        for row_tile in brisc.range(EMBEDDING_TILES):
          with brisc.scope():
            source_tile = brisc.reg(exclude=(token_id, row_tile))
            brisc.slli(source_tile, token_id, 1)
            brisc.add(source_tile, source_tile, row_tile)
            brisc.noc.read_into_cb(
              embedding_weight, source_tile, embedding_cb,
            )
    brisc.label(finished)

  # NCRISC drains the CB into this core's contiguous output-token shard.
  ncrisc = p.ncrisc
  with ncrisc.scope():
    local_count, start = ncrisc.reg(2)
    _load_local_count(
      ncrisc, p, valid_s, token_start, token_capacity, local_count, start,
    )
    for local_token in ncrisc.range(local_count):
      for row_tile in ncrisc.range(EMBEDDING_TILES):
        with ncrisc.scope():
          output_tile = ncrisc.reg(exclude=(local_token, row_tile))
          ncrisc.slli(output_tile, local_token, 1)
          ncrisc.add(output_tile, output_tile, row_tile)
          ncrisc.noc.write_from_cb(
            embedding_cb, output, output_tile,
          )
  return p


def embedding(token_ids: Buffer, embedding_weight: Buffer,
              output: Buffer) -> Program:
  """Gather up to 1024 embedding rows over 118 cores (80x9, then 38x8).

  Logical operation:
    output[:valid_s, :] = embedding_weight[token_ids[:valid_s], :]

  `valid_s` is a runtime Program parameter. The two inputs use one global tile
  namespace, while output is sharded into contiguous token ranges over cores.
  """
  if token_ids.dtype is not DType.U32:
    raise ValueError("embedding token IDs must be U32")
  if token_ids.shape != (PREFILL_BUCKET,) or token_ids.tiles != 1:
    raise ValueError(
      f"embedding token IDs must have shape ({PREFILL_BUCKET},)",
    )
  if not token_ids.global_address:
    raise ValueError("embedding token IDs must be globally addressed")
  if embedding_weight.dtype is not DType.BF16:
    raise ValueError("embedding weights must be BF16")
  if (
    len(embedding_weight.shape) != 2 or
    embedding_weight.shape[1] != EMBED_DIM or
    embedding_weight.axis != 0 or
    embedding_weight.tiles_per_item != EMBEDDING_TILES
  ):
    raise ValueError(
      f"embedding weights must have shape (vocab, {EMBED_DIM}) with axis=0",
    )
  if not embedding_weight.global_address:
    raise ValueError("embedding weights must be globally addressed")
  if (
    output.dtype is not DType.BF16 or
    output.shape != (PREFILL_BUCKET, EMBED_DIM) or
    output.axis != 0 or
    output.tiles_per_item != EMBEDDING_TILES or
    len(output.cores) != LLAMA_CORES or
    output.item_counts != CORE_TOKEN_COUNTS
  ):
    raise ValueError(
      f"embedding output must be BF16[{PREFILL_BUCKET}, {EMBED_DIM}] "
      f"sharded 9 tokens on {NINE_TOKEN_CORES} cores and 8 tokens on "
      f"{LLAMA_CORES - NINE_TOKEN_CORES} cores",
    )
  return _specialize_token_counts(
    lambda count: _embedding_program(
      token_ids, embedding_weight, output, token_capacity=count,
    ),
    output.cores, output.item_counts,
  )


def _validate_fused_rmsnorm(x, weight, output):
  bucket = x.shape[0] if len(x.shape) == 2 else None
  expected_cores = 1 if bucket == 1 else LLAMA_CORES
  expected_counts = (
    _token_counts(bucket, expected_cores)
    if bucket in RMSNORM_BUCKETS else None
  )
  for name, buffer in (("x", x), ("output", output)):
    if (
      buffer.dtype is not DType.BF16 or
      buffer.shape != (bucket, EMBED_DIM) or
      bucket not in RMSNORM_BUCKETS or
      buffer.axis != 0 or buffer.tiles_per_item != EMBEDDING_TILES or
      len(buffer.cores) != expected_cores or
      buffer.item_counts != expected_counts
    ):
      raise ValueError(
        f"fused RMSNorm {name} must be BF16[bucket, {EMBED_DIM}] with "
        f"bucket in {RMSNORM_BUCKETS}, using one core for bucket 1 and "
        f"{LLAMA_CORES} cores for prefill buckets",
      )
  if x.cores != output.cores or x.item_starts != output.item_starts:
    raise ValueError("fused RMSNorm input and output must use identical shards")
  if (
    weight.dtype is not DType.BF16 or weight.shape != (EMBED_DIM,) or
    weight.tiles != EMBEDDING_TILES or not weight.global_address
  ):
    raise ValueError(
      f"fused RMSNorm weight must be globally addressed BF16[{EMBED_DIM}]",
    )


def _rmsnorm_fused_program(
  x: Buffer, weight: Buffer, output: Buffer, *, token_capacity,
) -> Program:
  valid_s = Const("valid_s", x.shape[0])
  token_start = Const("token_start", x.item_starts)
  p = Program(
    x.cores, x, weight, output, valid_s, token_start, fp32_dst=True,
  )
  x_cb = p.cb(DType.BF16, depth=4)
  output_cb = p.cb(DType.BF16, depth=4)
  gamma_l1 = p.l1(EMBEDDING_TILES * weight.tile_size, alignment=16)
  decode = x.shape[0] == 1

  # Gamma is shared model state. Fetch its two tiles once into persistent L1.
  for tile in range(EMBEDDING_TILES):
    p.brisc.noc.read_tile(
      weight, tile, gamma_l1 + tile * weight.tile_size,
    )

  def read_token(local_token):
    for tile in range(EMBEDDING_TILES):
      if type(local_token) is int:
        p.brisc.noc.read_into_cb(
          x, local_token * EMBEDDING_TILES + tile, x_cb,
        )
      else:
        with p.brisc.scope():
          source_tile = p.brisc.reg(exclude=local_token)
          p.brisc.slli(source_tile, local_token, 1)
          if tile: p.brisc.addi(source_tile, source_tile, tile)
          p.brisc.noc.read_into_cb(x, source_tile, x_cb)

  if decode:
    read_token(0)
  else:
    with p.brisc.scope():
      local_count, start = p.brisc.reg(2)
      _load_local_count(
        p.brisc, p, valid_s, token_start, token_capacity,
        local_count, start,
      )
      for local_token in p.brisc.range(local_count):
        read_token(local_token)

  def unpack_token():
    for _ in range(EMBEDDING_TILES):
      p.unpack.move(x_cb, UnpackTarget.SRCA)
    for tile in range(EMBEDDING_TILES):
      p.unpack.move_l1(
        weight.dtype, gamma_l1 + tile * weight.tile_size,
      )

  if decode:
    unpack_token()
  else:
    with p.trisc0.scope():
      local_count, start = p.trisc0.reg(2)
      _load_local_count(
        p.trisc0, p, valid_s, token_start, token_capacity,
        local_count, start,
      )
      for _ in p.trisc0.range(local_count): unpack_token()

  def compute_token():
    for tile in range(2 * EMBEDDING_TILES):
      p.fpu.copy_a(dst_tile=tile)
    _rmsnorm_one_token(p.sfpu)

  if decode:
    compute_token()
  else:
    with p.trisc1.scope():
      local_count, start = p.trisc1.reg(2)
      _load_local_count(
        p.trisc1, p, valid_s, token_start, token_capacity,
        local_count, start,
      )
      for _ in p.trisc1.range(local_count): compute_token()

  def pack_token():
    p.pack.move_tiles(output_cb, tiles=(0, 1))

  if decode:
    pack_token()
  else:
    with p.trisc2.scope():
      local_count, start = p.trisc2.reg(2)
      _load_local_count(
        p.trisc2, p, valid_s, token_start, token_capacity,
        local_count, start,
      )
      for _ in p.trisc2.range(local_count): pack_token()

  def write_token(local_token):
    for tile in range(EMBEDDING_TILES):
      if type(local_token) is int:
        p.ncrisc.noc.write_from_cb(
          output_cb, output, local_token * EMBEDDING_TILES + tile,
        )
      else:
        with p.ncrisc.scope():
          output_tile = p.ncrisc.reg(exclude=local_token)
          p.ncrisc.slli(output_tile, local_token, 1)
          if tile: p.ncrisc.addi(output_tile, output_tile, tile)
          p.ncrisc.noc.write_from_cb(output_cb, output, output_tile)

  if decode:
    write_token(0)
  else:
    with p.ncrisc.scope():
      local_count, start = p.ncrisc.reg(2)
      _load_local_count(
        p.ncrisc, p, valid_s, token_start, token_capacity,
        local_count, start,
      )
      for local_token in p.ncrisc.range(local_count):
        write_token(local_token)
  return p


def rmsnorm(x: Buffer, weight: Buffer, output: Buffer) -> Program:
  """Fused FP32 RMSNorm for one-token decode or bucketed prefill."""
  _validate_fused_rmsnorm(x, weight, output)
  return _specialize_token_counts(
    lambda count: _rmsnorm_fused_program(
      x, weight, output, token_capacity=count,
    ),
    x.cores, x.item_counts,
  )


def run_embedding_hardware(seq_len=200, vocab_size=257,
                           safetensor_path=None, repeats=5):
  if not 0 < seq_len <= PREFILL_BUCKET:
    raise ValueError(f"seq_len must be in 1..{PREFILL_BUCKET}")
  if repeats < 1: raise ValueError("repeats must be positive")
  if safetensor_path is not None: vocab_size = VOCAB_SIZE
  if not 1 < vocab_size <= VOCAB_SIZE:
    raise ValueError(f"vocab_size must be in 2..{VOCAB_SIZE}")

  device = Device()
  try:
    device.init_device()
    token_ids = device.dram.buffer(
      "token_ids", DType.U32, (PREFILL_BUCKET,), global_address=True,
    )
    embedding_weight = device.dram.buffer(
      "embedding_weight", DType.BF16, (vocab_size, EMBED_DIM), axis=0,
      global_address=True,
    )
    output = device.dram.buffer(
      "embedding_output", DType.BF16, (PREFILL_BUCKET, EMBED_DIM), axis=0,
      cores=device.dram.cores[:LLAMA_CORES],
    )

    rng = np.random.default_rng(0)
    ids = np.zeros(PREFILL_BUCKET, dtype=np.uint32)
    ids[:seq_len] = rng.integers(0, vocab_size, size=seq_len, dtype=np.uint32)
    boundary_ids = np.asarray((0, 1, vocab_size - 2, vocab_size - 1), dtype=np.uint32)
    ids[:min(seq_len, len(boundary_ids))] = boundary_ids[:seq_len]

    ids_data = token_ids.from_numpy(ids)
    if safetensor_path is None:
      rows = np.arange(vocab_size, dtype=np.float32)[:, None]
      columns = np.arange(EMBED_DIM, dtype=np.float32)[None, :]
      weights = ((rows * 17 + columns * 3) % 251 - 125) / 32
      weights_data = embedding_weight.from_numpy(weights)
    else:
      weights_data = embedding_weight.from_safetensor(
        "model.embed_tokens.weight", safetensor_path,
      )

    device.write(token_ids, ids_data)
    device.write(embedding_weight, weights_data)
    program = embedding(token_ids, embedding_weight, output)
    device.queue(program, params={"valid_s": seq_len})
    readback = device.queue_read(output)
    timestamps = device.run(timeout=5.0)
    actual = readback.result()

    row_bytes = EMBED_DIM * DType.BF16.itemsize
    for token in range(seq_len):
      actual_row = actual[token * row_bytes:(token + 1) * row_bytes]
      weight_row = int(ids[token]) * row_bytes
      expected_row = weights_data[weight_row:weight_row + row_bytes]
      if actual_row != expected_row:
        byte = next(
          index for index, pair in enumerate(zip(actual_row, expected_row))
          if pair[0] != pair[1]
        )
        raise AssertionError(
          f"embedding mismatch at token {token}, feature {byte//2}: "
          f"id={int(ids[token])}, byte_in_row={byte}",
        )

    samples = [timestamps[-1].us]
    for _ in range(repeats - 1):
      samples.append(device.run(
        program, params={"valid_s": seq_len}, timeout=5.0,
      )[-1].us)
    kernel_us = float(np.median(samples))
    bytes_moved = seq_len * EMBED_DIM * DType.BF16.itemsize * 2
    print("PASS llama3 embedding")
    print(f"weights: {safetensor_path or 'synthetic'}")
    print(f"tokens: {seq_len}")
    print(f"cores: {len(output.cores)}")
    print(f"latency us: min={min(samples):.3f}, median={kernel_us:.3f}")
    print(f"effective read+write bandwidth: {bytes_moved/kernel_us/1e3:.3f} GB/s")
  finally:
    device.close()


def run_rmsnorm_hardware(
  valid_s=1024, bucket=None, repeats=5,
  safetensor_path="weights/model.safetensors",
):
  if repeats < 1: raise ValueError("repeats must be positive")
  selected_bucket = _rmsnorm_bucket(valid_s) if bucket is None else bucket
  if selected_bucket not in RMSNORM_BUCKETS:
    raise ValueError(f"bucket must be one of {RMSNORM_BUCKETS}")
  if not 0 < valid_s <= selected_bucket:
    raise ValueError("valid_s must be positive and no larger than bucket")
  if selected_bucket == 1 and valid_s != 1:
    raise ValueError("the decode bucket contains exactly one token")

  device = Device()
  try:
    device.init_device()
    core_count = 1 if selected_bucket == 1 else LLAMA_CORES
    cores = device.dram.cores[:core_count]
    shape = (selected_bucket, EMBED_DIM)
    x = device.dram.buffer(
      "rmsnorm_x", DType.BF16, shape, axis=0, cores=cores,
    )
    weight = device.dram.buffer(
      "rmsnorm_weight", DType.BF16, (EMBED_DIM,),
      global_address=True,
    )
    output = device.dram.buffer(
      "rmsnorm_output", DType.BF16, shape, axis=0, cores=cores,
    )

    rng = np.random.default_rng(1)
    values = rng.normal(0, 0.25, x.shape).astype(np.float32)
    x_data = x.from_numpy(values)
    weight_data = weight.from_safetensor(
      "model.layers.0.input_layernorm.weight", safetensor_path,
    )

    # CPU oracle: BF16 storage -> one fused FP32 expression -> one BF16 cast.
    xf = x.to_numpy(x_data)
    xf.flags.writeable = False
    wf = weight.to_numpy(weight_data)
    squares = np.multiply(xf, xf, dtype=np.float32)
    mean_square = np.sum(squares, axis=1, dtype=np.float32) * np.float32(
      1.0 / EMBED_DIM,
    )
    scale = np.float32(1.0) / np.sqrt(
      mean_square + np.float32(1e-5),
    )
    expected = output.to_numpy(output.from_numpy(
      np.multiply(
        np.multiply(xf, scale[:, None], dtype=np.float32),
        wf[None, :], dtype=np.float32,
      ),
    ))

    device.write(x, x_data)
    device.write(weight, weight_data)
    program = rmsnorm(x, weight, output)
    device.queue(program, params={"valid_s": valid_s})
    readback = device.queue_read(output)
    samples = [device.run(timeout=5.0)[-1].us]
    actual = output.to_numpy(readback.result())

    actual_valid, expected_valid = actual[:valid_s], expected[:valid_s]
    difference = np.subtract(actual_valid, expected_valid, dtype=np.float32)
    error = np.abs(difference)
    relative_l2 = float(
      np.linalg.norm(difference) /
      (np.linalg.norm(expected_valid) + 1e-12),
    )
    pcc = float(np.corrcoef(
      actual_valid.reshape(-1), expected_valid.reshape(-1),
    )[0, 1])
    exact = int(np.count_nonzero(actual_valid == expected_valid))
    if (
      not np.all(np.isfinite(actual_valid)) or
      float(error.max()) > 0.05 or relative_l2 > 0.01 or pcc < 0.999
    ):
      token, feature = np.unravel_index(int(error.argmax()), error.shape)
      raise AssertionError(
        f"RMSNorm mismatch at token {token}, feature {feature}: "
        f"actual={actual_valid[token, feature]}, "
        f"expected={expected_valid[token, feature]}, "
        f"max_abs={error.max()}, relative_l2={relative_l2}, PCC={pcc}",
      )
    for _ in range(repeats - 1):
      samples.append(device.run(
        program, params={"valid_s": valid_s}, timeout=5.0,
      )[-1].us)

    print("PASS llama3 RMSNorm")
    print("weight: model.layers.0.input_layernorm.weight")
    print(f"valid_s: {valid_s}")
    print(f"bucket: {selected_bucket}")
    print(f"cores: {core_count}")
    print(f"tokens/core: min={min(x.item_counts)}, max={max(x.item_counts)}")
    print(f"exact BF16 values: {exact}/{expected_valid.size}")
    print(f"max abs error: {error.max():.6g}")
    print(f"relative L2: {relative_l2:.6g}")
    print(f"PCC: {pcc:.9f}")
    print(f"latency us: min={min(samples):.3f}, median={np.median(samples):.3f}")
  finally:
    device.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--seq-len", type=int, default=200)
  parser.add_argument("--vocab-size", type=int, default=257)
  parser.add_argument(
    "--safetensor", nargs="?", const="weights/model.safetensors",
    help="load model.embed_tokens.weight from this file",
  )
  parser.add_argument(
    "--rmsnorm", action="store_true",
  )
  parser.add_argument("--bucket", type=int, choices=RMSNORM_BUCKETS)
  parser.add_argument("--repeats", type=int, default=5)
  args = parser.parse_args()
  if args.rmsnorm:
    run_rmsnorm_hardware(
      args.seq_len, args.bucket, args.repeats,
      args.safetensor or "weights/model.safetensors",
    )
  else:
    run_embedding_hardware(
      args.seq_len, args.vocab_size, args.safetensor, args.repeats,
    )
