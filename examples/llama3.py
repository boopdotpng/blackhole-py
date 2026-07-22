import argparse
import math
import numpy as np
import struct

from asm import Cond
from device import Device
from pcie import P100_WORKER_CORES
from program import Buffer, Const, DType, Program
from isa import R, Tensix as TT
from ttk.cb import CB
from ttk.sfpu import LaneConfig, LReg, SfpuFormat, SfpuProgram
from ttk.sync import Sem, SemWait, Stall, Wait, sem_wait, stall
from ttk.unpack import UnpackTarget


VOCAB_SIZE = 128256
EMBED_DIM = 2048
PREFILL_CAPACITY = 1024
EMBEDDING_TILES = EMBED_DIM // 1024
LLAMA_CORES = 118
TOKENS_PER_CORE, NINE_TOKEN_CORES = divmod(PREFILL_CAPACITY, LLAMA_CORES)
CORE_TOKEN_COUNTS = (
  (TOKENS_PER_CORE + 1,) * NINE_TOKEN_CORES +
  (TOKENS_PER_CORE,) * (LLAMA_CORES - NINE_TOKEN_CORES)
)
Q_PROJ_DIM = 2048
KV_PROJ_DIM = 512
HEAD_DIM = 64
Q_HEADS = Q_PROJ_DIM // HEAD_DIM
KV_HEADS = KV_PROJ_DIM // HEAD_DIM
ROPE_CORES = Q_HEADS + KV_HEADS
ROPE_CACHE_TOKENS = 8192
ROPE_THETA = 500000.0
ROPE_FACTOR = 32.0
ROPE_LOW_FREQ_FACTOR = 1.0
ROPE_HIGH_FREQ_FACTOR = 4.0
ROPE_ORIGINAL_MAX_POSITION_EMBEDDINGS = 8192
KV_CACHE_SHAPE = (KV_HEADS, ROPE_CACHE_TOKENS, HEAD_DIM)
KV_CACHE_TOKEN_BLOCK = 32
KV_CACHE_TIME_BLOCKS = ROPE_CACHE_TOKENS // KV_CACHE_TOKEN_BLOCK
KV_CACHE_FEATURE_TILES = HEAD_DIM // 32
KV_CACHE_TILES_PER_HEAD = KV_CACHE_TIME_BLOCKS * KV_CACHE_FEATURE_TILES
# Each innermost 1024-element row is one ordinary 32x32 tile.  Keeping this
# separate from KV_CACHE_SHAPE makes the logical model shape explicit while
# exposing the exact physical tile order expected by the score matmul.
KV_CACHE_STORAGE_SHAPE = (
  KV_HEADS, KV_CACHE_TILES_PER_HEAD, 32 * 32,
)
GQA_GROUP_SIZE = Q_HEADS // KV_HEADS
GQA_SCORE_SHAPE = (Q_HEADS, ROPE_CACHE_TOKENS)
# One score tile per KV group and 32-token history block.  Only rows 0..3 of
# each tile are live; they correspond to that KV head's four query heads.
GQA_SCORE_STORAGE_SHAPE = (KV_HEADS, KV_CACHE_TIME_BLOCKS, 32 * 32)


def rope_table(
  max_seq_len=ROPE_CACHE_TOKENS, head_dim=HEAD_DIM,
  rope_theta=ROPE_THETA, rope_factor=ROPE_FACTOR,
  rope_low_freq_factor=ROPE_LOW_FREQ_FACTOR,
  rope_high_freq_factor=ROPE_HIGH_FREQ_FACTOR,
  rope_original_max_position_embeddings=(
    ROPE_ORIGINAL_MAX_POSITION_EMBEDDINGS
  ),
):
  """Build Llama 3 cosine and sine tables on the host in FP32.

  The returned ``[position, head_dim]`` arrays duplicate the half-width
  angles exactly as Llama's split-half ``rotate_half`` convention expects.
  They are quantized only when copied into the resident BF16 DRAM buffers.
  """
  if max_seq_len < 1: raise ValueError("max_seq_len must be positive")
  if head_dim < 2 or head_dim % 2:
    raise ValueError("head_dim must be a positive even number")
  if not 0 < rope_low_freq_factor < rope_high_freq_factor:
    raise ValueError("RoPE frequency factors must be positive and ordered")

  dimensions = np.arange(0, head_dim, 2, dtype=np.float32)
  dimensions = np.divide(
    dimensions, np.float32(head_dim), dtype=np.float32,
  )
  inv_freq = np.reciprocal(
    np.power(np.float32(rope_theta), dimensions, dtype=np.float32),
    dtype=np.float32,
  )
  wavelen = np.divide(
    np.float32(2.0 * math.pi), inv_freq, dtype=np.float32,
  )
  cycles = np.divide(
    np.float32(rope_original_max_position_embeddings), wavelen,
    dtype=np.float32,
  )
  smooth = np.clip(
    np.divide(
      cycles - np.float32(rope_low_freq_factor),
      np.float32(rope_high_freq_factor - rope_low_freq_factor),
      dtype=np.float32,
    ),
    np.float32(0.0), np.float32(1.0),
  )
  inverse_factor = np.float32(1.0 / rope_factor)
  inv_freq = np.multiply(
    inv_freq,
    inverse_factor + smooth * (np.float32(1.0) - inverse_factor),
    dtype=np.float32,
  )
  angles = np.multiply(
    np.arange(max_seq_len, dtype=np.float32)[:, None],
    inv_freq[None, :], dtype=np.float32,
  )
  angles = np.tile(angles, (1, 2))
  return (
    np.ascontiguousarray(np.cos(angles), dtype=np.float32),
    np.ascontiguousarray(np.sin(angles), dtype=np.float32),
  )


def _bf16_rne_bytes(values):
  """Cast finite FP32 values to BF16 with round-to-nearest-even."""
  words = np.ascontiguousarray(values, dtype="<f4").view(np.uint32)
  rounded = words + np.uint32(0x7fff) + ((words >> 16) & np.uint32(1))
  return (rounded >> 16).astype("<u2").tobytes()


def upload_rope_cache(device: Device):
  """Queue one-time host-to-DRAM uploads of the fixed 8192-token cache."""
  shape = (ROPE_CACHE_TOKENS, HEAD_DIM)
  cos = device.dram.buffer(
    "rope_cos", DType.BF16, shape, global_address=True,
  )
  sin = device.dram.buffer(
    "rope_sin", DType.BF16, shape, global_address=True,
  )
  cos_values, sin_values = rope_table()
  # This mirrors tinygrad's COS/SIN.cast(dtypes.bfloat16), which uses RNE.
  # Buffer.from_numpy truncates BF16 and remains unchanged for existing users.
  device.write(cos, _bf16_rne_bytes(cos_values))
  device.write(sin, _bf16_rne_bytes(sin_values))
  return cos, sin


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
    TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0),
    TT.TTSFPMAD(LReg.L0, LReg.L0, LReg.L7, LReg.L7, 0),
  ))


def _rms_finalize_scale():
  """Reduce 32 accumulator lanes and leave reciprocal RMS in L0."""
  words = [TT.TTSFPMOV(0, LReg.L7, LReg.L0, 0)]
  # Butterfly-reduce each independent eight-lane SFPU row. Cyclic rotations
  # make the final sum a broadcast, which the transpose below needs.
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
      ))
    _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  # Copy the four eight-lane row sums, then transpose the four identical
  # registers. L0..L3 become broadcasts of rows 0..3 respectively.
  for register in (LReg.L1, LReg.L2, LReg.L3):
    words.append(TT.TTSFPMOV(0, LReg.L0, register, 0))
  words.append(TT.TTSFPTRANSP(0, 0, 0, 0))
  for register in (LReg.L1, LReg.L2, LReg.L3):
    _sfpu_add(words, LReg.L0, register, LReg.L0)

  words.extend(_sfpu_float_words(LReg.L4, 1.0 / EMBED_DIM))
  words.append(TT.TTSFPMUL(LReg.L0, LReg.L4, LReg.ZERO, LReg.L0, 0))
  words.extend(_sfpu_float_words(LReg.L4, 1e-5))
  _sfpu_add(words, LReg.L0, LReg.L4, LReg.L0)

  # Accurate Blackhole reciprocal square root for finite positive FP32 L0.
  x, y, temporary, c1, c2, half = (
    LReg.L6, LReg.L1, LReg.L2, LReg.L3, LReg.L4, LReg.L5,
  )
  words.extend((
    TT.TTSFPMOV(0, LReg.L0, x, 0),
    TT.TTSFPMOV(0, x, y, 0),
    TT.TTSFPSHFT(0xfff, LReg.ZERO, y, 1),
  ))
  magic = 0x5f1110a0
  words.extend((
    TT.TTSFPLOADI(temporary, 10, magic & 0xffff),
    TT.TTSFPLOADI(temporary, 8, magic >> 16),
    TT.TTSFPIADD(0, temporary, y, 6),
  ))
  _sfpu_mul(words, x, y, temporary)
  words.append(TT.TTSFPMUL(y, temporary, LReg.ZERO, temporary, 1))
  words.extend(_sfpu_float_words(c1, 2.2825186))
  words.extend(_sfpu_float_words(c2, 2.2533049))
  _sfpu_add(words, c2, temporary, c2)
  words.extend((TT.TTSFPMAD(temporary, c2, c1, temporary, 0), TT.TTSFPNOP()))
  _sfpu_mul(words, y, temporary, y)
  _sfpu_mul(words, x, y, temporary)
  _sfpu_mul(words, y, temporary, temporary, 1)
  words.append(TT.TTSFPADD(
    LReg.ONE, LReg.ONE, temporary, temporary, 0,
  ))
  words.extend(_sfpu_float_words(half, 0.5))
  _sfpu_mul(words, y, half, half)
  words.append(TT.TTSFPMAD(temporary, half, y, LReg.L0, 0))
  return SfpuProgram((), tuple(words))


def _rms_apply_weight_pair():
  """Apply RMS scale and gamma to two independent 32-lane footprints."""
  return SfpuProgram((), (
    TT.TTSFPLOADMACRO(LReg.L1, SfpuFormat.DEFAULT, 7, 0),
    TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, 128),
    TT.TTSFPLOADMACRO(LReg.L3, SfpuFormat.DEFAULT, 7, 2),
    TT.TTSFPLOAD(LReg.L4, SfpuFormat.FP32, 7, 130),
    TT.TTSFPMUL(LReg.L1, LReg.L2, LReg.ZERO, LReg.L1, 0),
    TT.TTSFPMUL(LReg.L3, LReg.L4, LReg.ZERO, LReg.L3, 0),
    TT.TTSFPSTORE(LReg.L1, SfpuFormat.FP32, 7, 0),
    TT.TTSFPSTORE(LReg.L3, SfpuFormat.FP32, 7, 2),
    TT.TTINCRWC(0, 2, 0, 0),
  ))


def _rms_setup_apply_macro(sfpu):
  """Configure macro 0 to multiply each loaded value by the live L0 scale."""
  sfpu._issue(TT.TTSFPCONFIG(LaneConfig().word(), LReg.LANE_X2, 1))
  sfpu._issue(TT.TTSFPNOP())
  # Backdoor destination CONFIG0 installs this multiply as template slot 0.
  sfpu._issue(TT.TTSFPMUL(
    LReg.L0, LReg.L0, LReg.ZERO, LReg.CONFIG0, 0,
  ))
  # Macro sequence 0, MAD byte: selector 4, delay 0, replace VB with the
  # just-loaded LReg. Other sub-units are disabled.
  sfpu._issue(TT.TTSFPCONFIG(0x8400, 4, 1))
  sfpu._issue(TT.TTSFPCONFIG(0x0f00, 8, 1))


def _rms_map_acquired(sfpu, program, *, iterations=8):
  start, body = sfpu._prepare(program)
  for word in program.setup_words: sfpu._issue(word)
  if start is not None:
    sfpu._configure_replay_mop(start, len(body), iterations)
  sfpu._run_faces(start, body, 4, iterations)
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

  apply = _rms_apply_weight_pair()
  _rms_select_tile(sfpu, 0)
  _rms_map_acquired(sfpu, apply, iterations=4)
  _rms_select_tile(sfpu, 1)
  _rms_map_acquired(sfpu, apply, iterations=4)
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


def _dot_accumulate(*, reset):
  """Accumulate one FP32 product tile into the persistent SFPU L7 lanes."""
  setup = _sfpu_float_words(LReg.L7, 0.0) if reset else ()
  return SfpuProgram(tuple(setup), (
    TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0),
    TT.TTSFPMAD(LReg.L0, LReg.ONE, LReg.L7, LReg.L7, 0),
  ))


def _dot_finalize():
  """Reduce the 32 SFPU accumulator lanes and store one scalar in Dst 0."""
  words = [TT.TTSFPMOV(0, LReg.L7, LReg.L0, 0)]
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
      ))
    _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  for register in (LReg.L1, LReg.L2, LReg.L3):
    words.append(TT.TTSFPMOV(0, LReg.L0, register, 0))
  words.append(TT.TTSFPTRANSP(0, 0, 0, 0))
  for register in (LReg.L1, LReg.L2, LReg.L3):
    _sfpu_add(words, LReg.L0, register, LReg.L0)
  words.extend((
    TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0),
    TT.TTSFPNOP(),
  ))
  return SfpuProgram((), tuple(words))


def _decode_projection_program(x, weight, output, *, local_rows):
  # Token 0 is always the first two physical tiles for both supported RMSNorm
  # layouts. This zero-copy global view makes those same 4 KiB visible to all
  # projection cores; unlike the activation, weight rows remain sharded.
  token = Buffer(
    f"{x.name}_decode_token", x.addr, x.dtype, (EMBED_DIM,), None,
    (x.cores[0],), x.banks, global_address=True,
  )
  p = Program(
    weight.cores, token, weight, output, fp32_dst=True,
  )
  weight_cb = p.cb(DType.BF16, depth=4)
  scalar_cb = p.cb(DType.BF16, depth=2)
  token_l1 = p.l1(EMBEDDING_TILES * token.tile_size, alignment=16)
  compact_l1 = p.l1(output.tile_size, alignment=16)

  # The activation is the replicated operand: every core fetches its two
  # tiles once. Each weight row is already two local tiles in that core's
  # DRAM shard, so no weight broadcast or physical transpose is needed.
  p.brisc.noc.read_tiles(token, tuple(
    (tile, token_l1 + tile * token.tile_size)
    for tile in range(EMBEDDING_TILES)
  ))
  for local_row in p.brisc.range(local_rows):
    with p.brisc.scope():
      first, second = p.brisc.reg(2, exclude=local_row)
      p.brisc.slli(first, local_row, 1)
      p.brisc.addi(second, first, 1)
      p.brisc.noc.read_tiles_into_cb(
        weight, (first, second), weight_cb,
      )

  for _ in p.trisc0.range(local_rows):
    p.unpack.move_l1_pair(weight_cb, token_l1)
    p.unpack.move_l1_pair(weight_cb, token_l1 + token.tile_size)

  accumulate_first = _dot_accumulate(reset=True)
  accumulate_second = _dot_accumulate(reset=False)
  finalize = _dot_finalize()
  for _ in p.trisc1.range(local_rows):
    p.fpu.binary("mul", dst_tile=0)
    _rms_select_tile(p.sfpu, 0)
    _rms_map_acquired(p.sfpu, accumulate_first)
    p.fpu.binary("mul", dst_tile=1)
    _rms_select_tile(p.sfpu, 1)
    _rms_map_acquired(p.sfpu, accumulate_second)
    _rms_select_tile(p.sfpu, 0)
    for word in finalize.words: p.sfpu._issue(word)
    stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
    p.sfpu.publish()

  for _ in p.trisc2.range(local_rows):
    p.pack.move_scalar(scalar_cb, tile=0)

  # One scalar pack still occupies a tile. Compact this core's 4--18 scalar
  # results into logical row 0 of one tile before writing DRAM.
  p.ncrisc.zero_words(compact_l1, output.tile_size // 4)
  for local_row in p.ncrisc.range(local_rows):
    CB.wait_front(p.ncrisc, scalar_cb)
    with p.ncrisc.scope():
      source, value, byte_offset, target = p.ncrisc.reg(
        4, exclude=local_row,
      )
      CB.get_read_ptr(p.ncrisc, scalar_cb, source)
      p.ncrisc.read(value, source, bytes=2)
      p.ncrisc.slli(byte_offset, local_row, 1)
      if output.item_elements > 16:
        with p.ncrisc.scope():
          right_face = p.ncrisc.reg(exclude=(local_row, byte_offset))
          packed = p.ncrisc._new_label("projection_scalar_packed")
          p.ncrisc.li(right_face, 16)
          p.ncrisc.bltu(local_row, right_face, packed)
          # Logical columns 16/17 live at byte 512/514 in the top-right face.
          p.ncrisc.addi(byte_offset, byte_offset, 480)
          p.ncrisc.label(packed)
      p.ncrisc.li(target, compact_l1)
      p.ncrisc.add(target, target, byte_offset)
      p.ncrisc.write(target, value, bytes=2)
    CB.pop_front(p.ncrisc, scalar_cb)
  with p.ncrisc.scope():
    target_address, target_coordinate = p.ncrisc.noc._dram_tile(output, 0)
    p.ncrisc.noc.write(
      compact_l1, target_address, target_coordinate, output.tile_size,
      posted=False,
    )
  return p


def decode_projection(x: Buffer, weight: Buffer, output: Buffer) -> Program:
  """Compute one bias-free HF Linear as ``weight @ x`` over 118 cores.

  Hugging Face stores Linear weights as ``[out_features, in_features]``.
  Each core owns a contiguous set of output rows and computes a 2048-element
  dot product for every row. The compact output has logical shape
  ``[118, max_rows_per_core]``: one tile per core, with padding only in the
  final slot of smaller shards.
  """
  if (
    x.dtype is not DType.BF16 or
    x.shape not in ((1, EMBED_DIM), (PREFILL_CAPACITY, EMBED_DIM)) or
    x.axis != 0 or x.tiles_per_item != EMBEDDING_TILES
  ):
    raise ValueError(
      f"decode projection x must be BF16[1, {EMBED_DIM}] or "
      f"BF16[{PREFILL_CAPACITY}, {EMBED_DIM}] with axis=0",
    )
  if (
    weight.dtype is not DType.BF16 or len(weight.shape) != 2 or
    weight.shape[0] not in (Q_PROJ_DIM, KV_PROJ_DIM) or
    weight.shape[1] != EMBED_DIM or weight.axis != 0 or
    weight.tiles_per_item != EMBEDDING_TILES or
    len(weight.cores) != LLAMA_CORES
  ):
    raise ValueError(
      f"decode projection weight must be BF16[{Q_PROJ_DIM}, {EMBED_DIM}] "
      f"or BF16[{KV_PROJ_DIM}, {EMBED_DIM}], axis=0 over {LLAMA_CORES} cores",
    )
  expected_shape = (LLAMA_CORES, weight.items_per_core)
  if (
    output.dtype is not DType.BF16 or output.shape != expected_shape or
    output.axis != 0 or output.cores != weight.cores or
    output.item_counts != (1,) * LLAMA_CORES or output.tiles_per_item != 1
  ):
    raise ValueError(
      f"decode projection output must be compact BF16{expected_shape}, "
      "axis=0 on the weight cores",
    )
  return _specialize_token_counts(
    lambda count: _decode_projection_program(
      x, weight, output, local_rows=count,
    ),
    weight.cores, weight.item_counts,
  )


def _bf16_tile_byte_offset(index):
  """Physical byte offset of a logical BF16 element in a face-tilized tile."""
  row, column = divmod(index, 32)
  face = (row // 16) * 2 + column // 16
  return face * 512 + (row % 16) * 32 + (column % 16) * 2


def _compact_projection_location(feature, *, query):
  if query:
    if feature < 42 * 18: return divmod(feature, 18)
    core, slot = divmod(feature - 42 * 18, 17)
    return core + 42, slot
  if feature < 40 * 5: return divmod(feature, 5)
  core, slot = divmod(feature - 40 * 5, 4)
  return core + 40, slot


def _compact_slot_byte_offset(slot):
  return slot * 2 if slot < 16 else 512 + (slot - 16) * 2


def _copy_l1_words(kernel, source_base, target_base, words, *,
                    source_offset=None):
  """Emit a small runtime L1 copy."""
  with kernel.scope():
    source, target, remaining, value = kernel.reg(4)
    if isinstance(source_base, R): kernel.mv(source, source_base)
    else: kernel.li(source, source_base)
    if isinstance(source_offset, R): kernel.add(source, source, source_offset)
    elif source_offset: kernel.addi(source, source, source_offset)
    if isinstance(target_base, R): kernel.mv(target, target_base)
    else: kernel.li(target, target_base)
    kernel.li(remaining, words)
    loop = kernel._new_label("rope_l1_copy")
    done = kernel._new_label("rope_l1_copy_done")
    kernel.label(loop)
    kernel.beq(remaining, R.ZERO, done)
    kernel.lw(value, source)
    kernel.sw(value, target)
    kernel.addi(source, source, 4)
    kernel.addi(target, target, 4)
    kernel.addi(remaining, remaining, -1)
    kernel.j(loop)
    kernel.label(done)


def _decode_rope_program(
  cores, q, k, v, cos, sin, q_output, k_output, v_output, start_pos,
  *, query, head,
):
  p = Program(
    cores, q, k, v, cos, sin, q_output, k_output, v_output, start_pos,
  )
  operands = p.cb(DType.BF16, depth=4)
  result = p.cb(DType.BF16, depth=1)
  feature_locations = tuple(
    _compact_projection_location(
      head * HEAD_DIM + index, query=query,
    )
    for index in range(HEAD_DIM)
  )
  source_tiles = tuple(dict.fromkeys(tile for tile, _ in feature_locations))
  source_tile_indices = {
    tile: index for index, tile in enumerate(source_tiles)
  }
  source_tiles_l1 = p.l1(
    len(source_tiles) * q.tile_size,
    alignment=16,
  )
  v_source_tiles_l1 = None if query else p.l1(
    len(source_tiles) * v.tile_size,
    alignment=16,
  )
  v_head_l1 = None if query else p.l1(v_output.tile_size, alignment=16)
  cos_tile_l1 = p.l1(cos.tile_size, alignment=16)
  sin_tile_l1 = p.l1(sin.tile_size, alignment=16)
  source = q if query else k

  # Keep the four BF16 operands in separate, normally tiled Dst tiles. SFPU
  # loads expand them into FP32 lane registers, so both multiplies and the add
  # happen in FP32 even though the final result is rounded back to BF16.
  CB.reserve_back(p.brisc, operands, 4)
  with p.brisc.scope():
    position, table_tile, table_row_offset = p.brisc.reg(3)
    p.brisc.read(position, p.param_addr(start_pos))
    p.brisc.srli(table_tile, position, 4)
    p.brisc.andi(table_row_offset, position, 15)
    p.brisc.slli(table_row_offset, table_row_offset, 1)
    with p.brisc.scope():
      face, row = p.brisc.reg(2, exclude=table_row_offset)
      p.brisc.srli(face, table_row_offset, 4)
      p.brisc.slli(face, face, 10)
      p.brisc.andi(row, table_row_offset, 15)
      p.brisc.slli(row, row, 5)
      p.brisc.add(table_row_offset, face, row)

    with p.brisc.noc.transaction() as transaction:
      for index, tile in enumerate(source_tiles):
        with p.brisc.scope():
          source_address, source_coordinate = p.brisc.noc._dram_tile(
            source, tile,
          )
          transaction.read(
            source_address, source_coordinate,
            source_tiles_l1 + index * source.tile_size, source.tile_size,
          )
        if not query:
          with p.brisc.scope():
            source_address, source_coordinate = p.brisc.noc._dram_tile(
              v, tile,
            )
            transaction.read(
              source_address, source_coordinate,
              v_source_tiles_l1 + index * v.tile_size, v.tile_size,
            )
      for table, target in ((cos, cos_tile_l1), (sin, sin_tile_l1)):
        with p.brisc.scope():
          source_address, source_coordinate = p.brisc.noc._dram_tile(
            table, table_tile,
          )
          transaction.read(
            source_address, source_coordinate, target, table.tile_size,
          )

    # Gather the desired halfwords locally. Full aligned tile reads above are
    # intentional: arbitrary tiny NoC packets are not a sound baseline.
    with p.brisc.scope():
      sign = p.brisc.reg()
      p.brisc.li(sign, 0x8000)
      for index, (tile, slot) in enumerate(feature_locations):
        with p.brisc.scope():
          value = p.brisc.reg(exclude=sign)
          compact_offset = (
            source_tile_indices[tile] * source.tile_size +
            _compact_slot_byte_offset(slot)
          )
          source_address = (
            source_tiles_l1 +
            compact_offset
          )
          p.brisc.read(value, source_address, bytes=2)
          p.brisc.write(
            operands.addr + _bf16_tile_byte_offset(index), value, bytes=2,
          )
          rotated_index = index + 32 if index < 32 else index - 32
          if index >= 32: p.brisc.xor(value, value, sign)
          p.brisc.write(
            operands.addr + operands.tile_size +
            _bf16_tile_byte_offset(rotated_index),
            value, bytes=2,
          )
          if not query:
            v_value = p.brisc.reg(exclude=(sign, value))
            p.brisc.read(
              v_value, v_source_tiles_l1 + compact_offset, bytes=2,
            )
            p.brisc.write(
              v_head_l1 + _bf16_tile_byte_offset(index),
              v_value, bytes=2,
            )

    # Extract the runtime position from each table tile into a normal output
    # tile. A cache tile holds 16 positions, each spanning two logical rows.
    for table_l1, operand_tile in ((cos_tile_l1, 2), (sin_tile_l1, 3)):
      for source_delta, target_offset in (
        (0, 0), (512, 512), (32, 32), (544, 544),
      ):
        with p.brisc.scope():
          source_offset = p.brisc.reg(exclude=table_row_offset)
          p.brisc.mv(source_offset, table_row_offset)
          if source_delta:
            p.brisc.addi(source_offset, source_offset, source_delta)
          _copy_l1_words(
            p.brisc, table_l1,
            operands.addr + operand_tile * operands.tile_size + target_offset,
            8, source_offset=source_offset,
          )

    if not query:
      with p.brisc.scope():
        target_address, target_coordinate = p.brisc.noc._dram_tile(
          v_output, head,
        )
        p.brisc.noc.write(
          v_head_l1, target_address, target_coordinate, v_output.tile_size,
          posted=False,
        )
  CB.push_back(p.brisc, operands, 4)

  for _ in range(4): p.unpack.move(operands, UnpackTarget.SRCA)

  p.fpu.copy_a_tiles(dst_tiles=range(4))
  sfpu = p.sfpu.program()
  x = sfpu.load(offset=0)
  rotated = sfpu.load(offset=64)
  cosine = sfpu.load(offset=128)
  sine = sfpu.load(offset=192)
  product = sfpu.mul(x, cosine)
  output_value = sfpu.mad(rotated, sine, product)
  sfpu.round_bf16(output_value, into=output_value)
  sfpu.store(output_value, offset=0)
  p.sfpu.map(sfpu.finish(), tile=0).publish()

  p.pack.move(result, tile=0)
  p.ncrisc.noc.write_from_cb(
    result, q_output if query else k_output, head,
  )
  return p


def _global_tile_view(buffer, name):
  return Buffer(
    name, buffer.addr, buffer.dtype, (buffer.physical_tiles, 1024), 0,
    (buffer.cores[0],), buffer.banks, global_address=True,
  )


def decode_rope(q: Buffer, k: Buffer, v: Buffer, cos: Buffer, sin: Buffer,
                q_output: Buffer, k_output: Buffer,
                v_output: Buffer) -> Program:
  """Apply Q/K RoPE and reassemble V together in one 40-core launch."""
  if (
    q.dtype is not DType.BF16 or q.shape != (LLAMA_CORES, 18) or
    q.axis != 0 or q.item_counts != (1,) * LLAMA_CORES
  ):
    raise ValueError("decode RoPE q must be compact BF16[118, 18]")
  for source, name in ((k, "k"), (v, "v")):
    if (
      source.dtype is not DType.BF16 or
      source.shape != (LLAMA_CORES, 5) or source.axis != 0 or
      source.item_counts != (1,) * LLAMA_CORES or source.cores != q.cores
    ):
      raise ValueError(
        f"decode RoPE {name} must be compact BF16[118, 5]",
      )
  for table, name in ((cos, "cos"), (sin, "sin")):
    if (
      table.dtype is not DType.BF16 or
      table.shape != (ROPE_CACHE_TOKENS, HEAD_DIM) or
      not table.global_address or table.axis is not None
    ):
      raise ValueError(
        f"decode RoPE {name} must be global BF16"
        f"[{ROPE_CACHE_TOKENS}, {HEAD_DIM}]",
      )
  for output, shape, name in (
    (q_output, (Q_HEADS, HEAD_DIM), "q_output"),
    (k_output, (KV_HEADS, HEAD_DIM), "k_output"),
    (v_output, (KV_HEADS, HEAD_DIM), "v_output"),
  ):
    if (
      output.dtype is not DType.BF16 or output.shape != shape or
      output.axis != 0 or not output.global_address or
      output.tiles_per_item != 1
    ):
      raise ValueError(f"decode RoPE {name} must be global BF16{shape}")

  cores = q.cores[:ROPE_CORES]
  q_tiles, k_tiles, v_tiles = (
    _global_tile_view(q, "rope_q_compact_tiles"),
    _global_tile_view(k, "rope_k_compact_tiles"),
    _global_tile_view(v, "rope_v_compact_tiles"),
  )
  start_pos = Const("start_pos", 0)
  specifications = (
    *((True, head) for head in range(Q_HEADS)),
    *((False, head) for head in range(KV_HEADS)),
  )
  variants = [
    _decode_rope_program(
      cores, q_tiles, k_tiles, v_tiles, cos, sin,
      q_output, k_output, v_output, start_pos, query=query, head=head,
    )
    for query, head in specifications
  ]
  lowered = [program.lower() for program in variants]
  combined = variants[0]
  combined._kernels = {
    core: dict(images[core])
    for core, images in zip(cores, lowered)
  }
  return combined


def kv_cache_write(k: Buffer, v: Buffer, key_cache: Buffer,
                   value_cache: Buffer) -> Program:
  """Copy one decoded K/V token into standard 2-D cache tiles.

  The logical ``[8, 8192, 64]`` cache is physically
  ``[8, 256 time blocks, 2 feature halves, 32, 32]``.  Eight BRISCs run
  independently, one per KV head, and update one row in each feature tile.
  Other cache positions are never read or overwritten.
  """
  for source, name in ((k, "k"), (v, "v")):
    if (
      source.dtype is not DType.BF16 or
      source.shape != (KV_HEADS, HEAD_DIM) or source.axis != 0 or
      not source.global_address or source.tiles_per_item != 1
    ):
      raise ValueError(
        f"kv cache {name} must be global BF16[{KV_HEADS}, {HEAD_DIM}] "
        "with axis=0",
      )
  for cache, name in ((key_cache, "key_cache"),
                      (value_cache, "value_cache")):
    if (
      cache.dtype is not DType.BF16 or
      cache.shape != KV_CACHE_STORAGE_SHAPE or
      cache.axis != 0 or not cache.global_address or
      cache.tiles_per_item != KV_CACHE_TILES_PER_HEAD
    ):
      raise ValueError(
        f"{name} must be global BF16{KV_CACHE_STORAGE_SHAPE} with axis=0",
      )

  start_pos = Const("start_pos", 0)
  head_index = Const("head_index", tuple(range(KV_HEADS)))
  p = Program(
    P100_WORKER_CORES[:KV_HEADS],
    k, v, key_cache, value_cache, start_pos, head_index,
  )
  k_l1 = p.l1(k.tile_size, alignment=16)
  v_l1 = p.l1(v.tile_size, alignment=16)

  with p.brisc.scope():
    position, head, time_block, row_offset = p.brisc.reg(4)
    p.brisc.read(position, p.param_addr(start_pos))
    p.brisc.read(head, p.param_addr(head_index))
    p.brisc.srli(time_block, position, 5)

    # Physical byte offset of this token's row in an ordinary BF16 tile.
    p.brisc.andi(row_offset, position, 15)
    p.brisc.slli(row_offset, row_offset, 5)
    with p.brisc.scope():
      bottom_faces = p.brisc.reg(exclude=(position, row_offset))
      p.brisc.srli(bottom_faces, position, 4)
      p.brisc.andi(bottom_faces, bottom_faces, 1)
      p.brisc.slli(bottom_faces, bottom_faces, 10)
      p.brisc.add(row_offset, row_offset, bottom_faces)

    with p.brisc.noc.transaction() as transaction:
      for source, target in ((k, k_l1), (v, v_l1)):
        with p.brisc.scope():
          source_address, source_coordinate = p.brisc.noc._dram_tile(
            source, head,
          )
          transaction.read(
            source_address, source_coordinate, target, source.tile_size,
          )

    # Tile index is head * 512 + time_block * 2 + feature_half.
    with p.brisc.scope():
      cache_tile = p.brisc.reg(exclude=(head, time_block, row_offset))
      p.brisc.slli(cache_tile, head, 9)
      with p.brisc.scope():
        block_tiles = p.brisc.reg(exclude=(cache_tile, time_block))
        p.brisc.slli(block_tiles, time_block, 1)
        p.brisc.add(cache_tile, cache_tile, block_tiles)

      for feature_half, source_offsets in enumerate(((0, 512), (32, 544))):
        with p.brisc.scope():
          target_tile = p.brisc.reg(exclude=(cache_tile, row_offset))
          p.brisc.mv(target_tile, cache_tile)
          if feature_half: p.brisc.addi(target_tile, target_tile, 1)
          key_address, key_coordinate = p.brisc.noc._dram_tile(
            key_cache, target_tile,
          )
          value_address, value_coordinate = p.brisc.noc._dram_tile(
            value_cache, target_tile,
          )
          with p.brisc.noc.transaction() as transaction:
            for source_offset, target_delta in zip(source_offsets, (0, 512)):
              with p.brisc.scope():
                target_offset, key_target, value_target = p.brisc.reg(
                  3, exclude=row_offset,
                )
                p.brisc.mv(target_offset, row_offset)
                if target_delta:
                  p.brisc.addi(target_offset, target_offset, target_delta)
                # NoC middle-address fields carry upper address bits; byte
                # offsets must be added to the low DRAM address explicitly.
                p.brisc.add(key_target, key_address, target_offset)
                p.brisc.add(value_target, value_address, target_offset)
                transaction.write(
                  k_l1 + source_offset, key_target, key_coordinate, 32,
                  posted=False,
                )
                transaction.write(
                  v_l1 + source_offset, value_target, value_coordinate, 32,
                  posted=False,
                )
  return p


def gqa_scores(q: Buffer, key_cache: Buffer, scores: Buffer) -> Program:
  """Compute decode GQA scores in eight independent KV-head groups.

  Worker ``h`` multiplies query heads ``4*h : 4*h+4`` by key-cache head
  ``h``.  Each 32-token block is two HiFi2 matrix products (one per 32-wide
  feature half) accumulated in FP32 Dst, followed by the exact ``1/8``
  attention scale in SFPU.  The runtime ``kv_blocks`` parameter is
  ``ceil((start_pos + 1) / 32)``.
  """
  if (
    q.dtype is not DType.BF16 or q.shape != (Q_HEADS, HEAD_DIM) or
    q.axis != 0 or not q.global_address or q.tiles_per_item != 1
  ):
    raise ValueError(
      f"GQA q must be global BF16[{Q_HEADS}, {HEAD_DIM}] with axis=0",
    )
  if (
    key_cache.dtype is not DType.BF16 or
    key_cache.shape != KV_CACHE_STORAGE_SHAPE or key_cache.axis != 0 or
    not key_cache.global_address or
    key_cache.tiles_per_item != KV_CACHE_TILES_PER_HEAD
  ):
    raise ValueError(
      f"GQA key_cache must be global BF16{KV_CACHE_STORAGE_SHAPE} "
      "with axis=0",
    )
  if (
    scores.dtype is not DType.F32 or
    scores.shape != GQA_SCORE_STORAGE_SHAPE or scores.axis != 0 or
    not scores.global_address or
    scores.tiles_per_item != KV_CACHE_TIME_BLOCKS
  ):
    raise ValueError(
      f"GQA scores must be global F32{GQA_SCORE_STORAGE_SHAPE} "
      "with axis=0",
    )

  kv_blocks = Const("kv_blocks", 1)
  kv_head = Const("kv_head", tuple(range(KV_HEADS)))
  p = Program(
    P100_WORKER_CORES[:KV_HEADS], q, key_cache, scores,
    kv_blocks, kv_head, fp32_dst=True,
  )
  query_cb = p.cb(DType.BF16, depth=4)
  key_cb = p.cb(DType.BF16, depth=4)
  score_cb = p.cb(DType.F32, depth=2)
  query_heads_l1 = p.l1(GQA_GROUP_SIZE * q.tile_size, alignment=16)
  query_low_l1 = p.l1(q.tile_size, alignment=16)
  query_high_l1 = p.l1(q.tile_size, alignment=16)

  # BRISC gathers four ordinary [1, 64] Q tiles into two [4, 32] tiles once,
  # then streams the matching pair of K tiles for every history block.
  p.brisc.zero_words(query_low_l1, q.tile_size // 4)
  p.brisc.zero_words(query_high_l1, q.tile_size // 4)
  with p.brisc.scope():
    head, block_count = p.brisc.reg(2)
    p.brisc.read(head, p.param_addr(kv_head))
    p.brisc.read(block_count, p.param_addr(kv_blocks))
    with p.brisc.noc.transaction() as transaction:
      for group_row in range(GQA_GROUP_SIZE):
        with p.brisc.scope():
          query_head = p.brisc.reg(exclude=head)
          p.brisc.mv(query_head, head)
          p.brisc.slli(query_head, query_head, 2)
          if group_row: p.brisc.addi(query_head, query_head, group_row)
          source_address, source_coordinate = p.brisc.noc._dram_tile(
            q, query_head,
          )
          transaction.read(
            source_address, source_coordinate,
            query_heads_l1 + group_row * q.tile_size, q.tile_size,
          )

    for group_row in range(GQA_GROUP_SIZE):
      source = query_heads_l1 + group_row * q.tile_size
      target_left = _bf16_tile_byte_offset(group_row * 32)
      target_right = _bf16_tile_byte_offset(group_row * 32 + 16)
      for target, source_offset in (
        (query_low_l1, 0), (query_high_l1, 32),
      ):
        _copy_l1_words(
          p.brisc, source, target + target_left, 8,
          source_offset=source_offset,
        )
        _copy_l1_words(
          p.brisc, source, target + target_right, 8,
          source_offset=source_offset + 512,
        )

    for block in p.brisc.range(block_count):
      CB.reserve_back(p.brisc, query_cb, 2)
      with p.brisc.scope():
        query_low, query_high, tile_bytes = p.brisc.reg(3)
        CB.get_write_ptr(p.brisc, query_cb, query_low)
        p.brisc.li(tile_bytes, query_cb.tile_size)
        p.brisc.add(query_high, query_low, tile_bytes)
        _copy_l1_words(
          p.brisc, query_low_l1, query_low, q.tile_size // 4,
        )
        _copy_l1_words(
          p.brisc, query_high_l1, query_high, q.tile_size // 4,
        )
      CB.push_back(p.brisc, query_cb, 2)
      with p.brisc.scope():
        first, second, block_offset = p.brisc.reg(
          3, exclude=(head, block),
        )
        p.brisc.slli(first, head, 9)
        p.brisc.slli(block_offset, block, 1)
        p.brisc.add(first, first, block_offset)
        p.brisc.addi(second, first, 1)
        p.brisc.noc.read_tiles_into_cb(
          key_cache, (first, second), key_cb,
        )

  with p.trisc0.scope():
    block_count = p.trisc0.reg()
    p.trisc0.read(block_count, p.param_addr(kv_blocks))
    for _ in p.trisc0.range(block_count):
      p.unpack.move_matmul(
        query_cb, key_cb, right_transpose=True,
      )
      p.unpack.move_matmul(
        query_cb, key_cb, right_transpose=True,
      )

  scale = p.sfpu.program()
  score = scale.load(offset=0)
  scale.mul_scalar(score, HEAD_DIM ** -0.5, into=score)
  scale.store(score, offset=0)
  scale = scale.finish()
  with p.trisc1.scope():
    block_count = p.trisc1.reg()
    p.trisc1.read(block_count, p.param_addr(kv_blocks))
    for _ in p.trisc1.range(block_count):
      p.fpu.matmul(dst_tile=0, right_transpose=True)
      p.fpu.matmul(
        dst_tile=0, accumulate=True, right_transpose=True,
      )
      p.sfpu.map(scale, tile=0).publish()

  with p.trisc2.scope():
    block_count = p.trisc2.reg()
    p.trisc2.read(block_count, p.param_addr(kv_blocks))
    for _ in p.trisc2.range(block_count):
      p.pack.move(score_cb, tile=0)

  with p.ncrisc.scope():
    head, block_count = p.ncrisc.reg(2)
    p.ncrisc.read(head, p.param_addr(kv_head))
    p.ncrisc.read(block_count, p.param_addr(kv_blocks))
    for block in p.ncrisc.range(block_count):
      with p.ncrisc.scope():
        output_tile = p.ncrisc.reg(exclude=(head, block))
        p.ncrisc.slli(output_tile, head, 8)
        p.ncrisc.add(output_tile, output_tile, block)
        p.ncrisc.noc.write_from_cb(score_cb, scores, output_tile)
  return p


def gqa_softmax(scores: Buffer, probabilities: Buffer) -> Program:
  """Softmax four decode score rows per KV group over the valid history."""
  if (
    scores.dtype is not DType.F32 or
    scores.shape != GQA_SCORE_STORAGE_SHAPE or scores.axis != 0 or
    not scores.global_address or
    scores.tiles_per_item != KV_CACHE_TIME_BLOCKS
  ):
    raise ValueError(
      f"GQA softmax scores must be global F32{GQA_SCORE_STORAGE_SHAPE} "
      "with axis=0",
    )
  if (
    probabilities.dtype is not DType.BF16 or
    probabilities.shape != GQA_SCORE_STORAGE_SHAPE or
    probabilities.axis != 0 or not probabilities.global_address or
    probabilities.tiles_per_item != KV_CACHE_TIME_BLOCKS
  ):
    raise ValueError(
      f"GQA probabilities must be global BF16{GQA_SCORE_STORAGE_SHAPE} "
      "with axis=0",
    )

  kv_blocks = Const("kv_blocks", 1)
  valid_columns = Const("valid_columns", 1)
  kv_head = Const("kv_head", tuple(range(KV_HEADS)))
  p = Program(
    P100_WORKER_CORES[:KV_HEADS], scores, probabilities,
    kv_blocks, valid_columns, kv_head, fp32_dst=True,
  )
  score_cb = p.cb(DType.F32, depth=4)
  maxima_cb = p.cb(DType.BF16, depth=1)
  # Retain every local exponential tile in L1. TRISC2 republishes the same
  # ring after the sum pass, so normalization does not recompute exp or touch
  # a DRAM scratch tensor.
  exponential_cb = p.cb(DType.BF16, depth=KV_CACHE_TIME_BLOCKS)
  inverse_sum_cb = p.cb(DType.BF16, depth=1)
  probability_cb = p.cb(DType.BF16, depth=4)

  # Stream scores for the max pass and again for score-max/exp. The final tile
  # is modified in its CB slot before publication so invalid history columns
  # are -inf in both passes.
  with p.brisc.scope():
    head, block_count, tail, last_block = p.brisc.reg(4)
    p.brisc.read(head, p.param_addr(kv_head))
    p.brisc.read(block_count, p.param_addr(kv_blocks))
    p.brisc.read(tail, p.param_addr(valid_columns))
    p.brisc.addi(last_block, block_count, -1)
    for _ in range(2):
      for block in p.brisc.range(block_count):
        with p.brisc.scope():
          tile = p.brisc.reg(exclude=(head, block))
          p.brisc.slli(tile, head, 8)
          p.brisc.add(tile, tile, block)
          ordinary = p.brisc._new_label("softmax_ordinary_score")
          ready = p.brisc._new_label("softmax_score_ready")
          p.brisc.bne(block, last_block, ordinary)

          CB.reserve_back(p.brisc, score_cb)
          with p.brisc.scope():
            target = p.brisc.reg()
            CB.get_write_ptr(p.brisc, score_cb, target)
            p.brisc.noc.read_tile(scores, tile, target)
            with p.brisc.scope():
              column, limit, negative_infinity = p.brisc.reg(3)
              p.brisc.mv(column, tail)
              p.brisc.li(limit, 32)
              p.brisc.li(negative_infinity, 0xff800000)
              with p.brisc.loop(Cond(column, "<u", limit)):
                with p.brisc.scope():
                  face_offset, within_face, offset = p.brisc.reg(3)
                  p.brisc.srli(face_offset, column, 4)
                  p.brisc.slli(face_offset, face_offset, 10)
                  p.brisc.andi(within_face, column, 15)
                  p.brisc.slli(within_face, within_face, 2)
                  p.brisc.add(offset, face_offset, within_face)
                  for row in range(GQA_GROUP_SIZE):
                    with p.brisc.scope():
                      address = p.brisc.reg(exclude=(target, offset))
                      p.brisc.add(address, target, offset)
                      if row: p.brisc.addi(address, address, row * 64)
                      p.brisc.sw(negative_infinity, address)
                p.brisc.addi(column, column, 1)
          CB.push_back(p.brisc, score_cb)
          p.brisc.j(ready)

          p.brisc.label(ordinary)
          p.brisc.noc.read_into_cb(scores, tile, score_cb)
          p.brisc.label(ready)

  exponential = p.sfpu.program()
  value = exponential.load(format=SfpuFormat.FP32)
  exponential.exp(value, into=value)
  exponential.store(value, format=SfpuFormat.FP32)
  exponential = exponential.finish()

  reciprocal = p.sfpu.program()
  value = reciprocal.load(format=SfpuFormat.FP32)
  reciprocal.reciprocal(value, into=value)
  reciprocal.store(value, format=SfpuFormat.FP32)
  reciprocal = reciprocal.finish()

  # Unpack: max pass, score-max pass, exponential sum pass, normalize pass.
  with p.trisc0.scope():
    block_count = p.trisc0.reg()
    p.trisc0.read(block_count, p.param_addr(kv_blocks))
    for _ in p.trisc0.range(block_count):
      p.unpack.move_row_reduce(
        score_cb, p.ops._row_scaler_address(), maximum=True,
      )
    CB.wait_front(p.trisc0, maxima_cb)
    for _ in p.trisc0.range(block_count):
      p.unpack.move_l1_pair_rows(score_cb, maxima_cb.addr)
    CB.pop_front(p.trisc0, maxima_cb)
    for _ in p.trisc0.range(block_count):
      p.unpack.move_row_reduce(
        exponential_cb, p.ops._row_scaler_address(), maximum=False,
      )
    CB.wait_front(p.trisc0, inverse_sum_cb)
    for _ in p.trisc0.range(block_count):
      p.unpack.move_l1_pair_rows(exponential_cb, inverse_sum_cb.addr)
    CB.pop_front(p.trisc0, inverse_sum_cb)

  # Math: retain row maxima, exponentiate, sum, invert the sums, normalize.
  with p.trisc1.scope():
    block_count = p.trisc1.reg()
    p.trisc1.read(block_count, p.param_addr(kv_blocks))
    for _ in p.trisc1.range(block_count):
      p.fpu.reduce_row_max(dst_tile=0)
    p.fpu.publish()
    for _ in p.trisc1.range(block_count):
      p.fpu.binary("sub", dst_tile=0)
      p.sfpu.map(exponential, tile=0).publish()
    for _ in p.trisc1.range(block_count):
      p.fpu.reduce_row_sum(dst_tile=0)
    p.sfpu.map(reciprocal, tile=0, region="column").publish()
    for _ in p.trisc1.range(block_count):
      p.fpu.binary("mul", dst_tile=0).publish()

  # Pack exp once, replay its unchanged CB slots, then pack probabilities.
  with p.trisc2.scope():
    block_count = p.trisc2.reg()
    p.trisc2.read(block_count, p.param_addr(kv_blocks))
    p.pack.move(maxima_cb, tile=0)
    for _ in p.trisc2.range(block_count):
      p.pack.move(exponential_cb, tile=0)
    for _ in p.trisc2.range(block_count):
      CB.reserve_back(p.trisc2, exponential_cb)
      CB.push_back(p.trisc2, exponential_cb)
    p.pack.move(inverse_sum_cb, tile=0)
    for _ in p.trisc2.range(block_count):
      p.pack.move(probability_cb, tile=0)

  with p.ncrisc.scope():
    head, block_count = p.ncrisc.reg(2)
    p.ncrisc.read(head, p.param_addr(kv_head))
    p.ncrisc.read(block_count, p.param_addr(kv_blocks))
    for block in p.ncrisc.range(block_count):
      with p.ncrisc.scope():
        output_tile = p.ncrisc.reg(exclude=(head, block))
        p.ncrisc.slli(output_tile, head, 8)
        p.ncrisc.add(output_tile, output_tile, block)
        p.ncrisc.noc.write_from_cb(
          probability_cb, probabilities, output_tile,
        )
  return p


def _embedding_program(
  token_ids, embedding_weight, output, *, token_capacity,
):
  valid_s = Const("valid_s", PREFILL_CAPACITY)
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
  if token_ids.shape != (PREFILL_CAPACITY,) or token_ids.tiles != 1:
    raise ValueError(
      f"embedding token IDs must have shape ({PREFILL_CAPACITY},)",
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
    output.shape != (PREFILL_CAPACITY, EMBED_DIM) or
    output.axis != 0 or
    output.tiles_per_item != EMBEDDING_TILES or
    len(output.cores) != LLAMA_CORES or
    output.item_counts != CORE_TOKEN_COUNTS
  ):
    raise ValueError(
      f"embedding output must be BF16[{PREFILL_CAPACITY}, {EMBED_DIM}] "
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
  capacity = x.shape[0] if len(x.shape) == 2 else None
  expected_cores = 1 if capacity == 1 else LLAMA_CORES
  expected_counts = (
    _token_counts(capacity, expected_cores)
    if capacity in (1, PREFILL_CAPACITY) else None
  )
  for name, buffer in (("x", x), ("output", output)):
    if (
      buffer.dtype is not DType.BF16 or
      buffer.shape != (capacity, EMBED_DIM) or
      capacity not in (1, PREFILL_CAPACITY) or
      buffer.axis != 0 or buffer.tiles_per_item != EMBEDDING_TILES or
      len(buffer.cores) != expected_cores or
      buffer.item_counts != expected_counts
    ):
      raise ValueError(
        f"fused RMSNorm {name} must be BF16[1, {EMBED_DIM}] on one core "
        f"for decode or BF16[{PREFILL_CAPACITY}, {EMBED_DIM}] sharded "
        f"over {LLAMA_CORES} cores for prefill",
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
  overlap_noc = x.shape[0] <= 512

  # Gamma is shared model state. Fetch its two tiles once into persistent L1.
  p.brisc.noc.read_tiles(weight, tuple(
    (tile, gamma_l1 + tile * weight.tile_size)
    for tile in range(EMBEDDING_TILES)
  ))

  def read_token(local_token):
    if type(local_token) is int:
      first = local_token * EMBEDDING_TILES
      if overlap_noc:
        p.brisc.noc.read_tiles_into_cb(x, (first, first + 1), x_cb)
      else:
        for tile in (first, first + 1):
          p.brisc.noc.read_into_cb(x, tile, x_cb)
    else:
      with p.brisc.scope():
        first, second = p.brisc.reg(2, exclude=local_token)
        p.brisc.slli(first, local_token, 1)
        p.brisc.addi(second, first, 1)
        if overlap_noc:
          p.brisc.noc.read_tiles_into_cb(x, (first, second), x_cb)
        else:
          p.brisc.noc.read_into_cb(x, first, x_cb)
          p.brisc.noc.read_into_cb(x, second, x_cb)

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
    p.fpu.copy_a_tiles(dst_tiles=range(2 * EMBEDDING_TILES))
    _rmsnorm_one_token(p.sfpu)

  _rms_setup_apply_macro(p.sfpu)
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
    if type(local_token) is int:
      first = local_token * EMBEDDING_TILES
      p.ncrisc.noc.write_tiles_from_cb(
        output_cb, output, (first, first + 1),
      )
    else:
      with p.ncrisc.scope():
        first, second = p.ncrisc.reg(2, exclude=local_token)
        p.ncrisc.slli(first, local_token, 1)
        p.ncrisc.addi(second, first, 1)
        p.ncrisc.noc.write_tiles_from_cb(
          output_cb, output, (first, second),
        )

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
  """Fused FP32 RMSNorm for one-token decode or fixed-capacity prefill."""
  _validate_fused_rmsnorm(x, weight, output)
  return _specialize_token_counts(
    lambda count: _rmsnorm_fused_program(
      x, weight, output, token_capacity=count,
    ),
    x.cores, x.item_counts,
  )


def run_embedding_hardware(seq_len=200, vocab_size=257,
                           safetensor_path=None, repeats=5):
  if not 0 < seq_len <= PREFILL_CAPACITY:
    raise ValueError(f"seq_len must be in 1..{PREFILL_CAPACITY}")
  if repeats < 1: raise ValueError("repeats must be positive")
  if safetensor_path is not None: vocab_size = VOCAB_SIZE
  if not 1 < vocab_size <= VOCAB_SIZE:
    raise ValueError(f"vocab_size must be in 2..{VOCAB_SIZE}")

  device = Device()
  try:
    device.init_device()
    token_ids = device.dram.buffer(
      "token_ids", DType.U32, (PREFILL_CAPACITY,), global_address=True,
    )
    embedding_weight = device.dram.buffer(
      "embedding_weight", DType.BF16, (vocab_size, EMBED_DIM), axis=0,
      global_address=True,
    )
    output = device.dram.buffer(
      "embedding_output", DType.BF16, (PREFILL_CAPACITY, EMBED_DIM), axis=0,
      cores=device.dram.cores[:LLAMA_CORES],
    )

    rng = np.random.default_rng(0)
    ids = np.zeros(PREFILL_CAPACITY, dtype=np.uint32)
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
  valid_s=1024, repeats=5,
  safetensor_path="weights/model.safetensors",
  core_start=0,
  decode=False,
):
  if repeats < 1: raise ValueError("repeats must be positive")
  if decode:
    if valid_s != 1:
      raise ValueError("decode RMSNorm requires valid_s=1")
    capacity, core_count = 1, 1
  else:
    if not 0 < valid_s <= PREFILL_CAPACITY:
      raise ValueError(f"valid_s must be in 1..{PREFILL_CAPACITY}")
    capacity, core_count = PREFILL_CAPACITY, LLAMA_CORES

  device = Device()
  try:
    device.init_device()
    if not 0 <= core_start <= len(device.dram.cores) - core_count:
      raise ValueError("core range exceeds the available worker cores")
    cores = device.dram.cores[core_start:core_start + core_count]
    shape = (capacity, EMBED_DIM)
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
    print(f"mode: {'decode' if decode else 'prefill'}")
    print(f"valid_s: {valid_s}")
    print(f"capacity: {capacity}")
    print(f"cores: {core_count}")
    print(f"core start: {core_start}")
    print(f"tokens/core: min={min(x.item_counts)}, max={max(x.item_counts)}")
    print(f"exact BF16 values: {exact}/{expected_valid.size}")
    print(f"max abs error: {error.max():.6g}")
    print(f"relative L2: {relative_l2:.6g}")
    print(f"PCC: {pcc:.9f}")
    print(
      f"latency us: min={min(samples):.3f}, "
      f"p10={np.percentile(samples, 10):.3f}, "
      f"median={np.median(samples):.3f}, "
      f"p90={np.percentile(samples, 90):.3f}"
    )
  finally:
    device.close()


def _projection_values(output, data, row_counts):
  compact = output.to_numpy(data)
  return np.concatenate([
    compact[core, :count]
    for core, count in enumerate(row_counts)
  ])


def run_rope_cache_hardware():
  """Validate the one-time host-built Llama 3 RoPE cache upload."""
  device = Device()
  try:
    device.init_device()
    cos, sin = upload_rope_cache(device)
    cos_readback = device.queue_read(cos)
    sin_readback = device.queue_read(sin)
    device.run(timeout=5.0)

    cos_values, sin_values = rope_table()
    expected_cos = cos.to_numpy(_bf16_rne_bytes(cos_values))
    expected_sin = sin.to_numpy(_bf16_rne_bytes(sin_values))
    actual_cos = cos.to_numpy(cos_readback.result())
    actual_sin = sin.to_numpy(sin_readback.result())
    if not np.array_equal(actual_cos, expected_cos):
      position, feature = np.argwhere(actual_cos != expected_cos)[0]
      raise AssertionError(
        f"RoPE cosine upload mismatch at [{position}, {feature}]: "
        f"actual={actual_cos[position, feature]}, "
        f"expected={expected_cos[position, feature]}",
      )
    if not np.array_equal(actual_sin, expected_sin):
      position, feature = np.argwhere(actual_sin != expected_sin)[0]
      raise AssertionError(
        f"RoPE sine upload mismatch at [{position}, {feature}]: "
        f"actual={actual_sin[position, feature]}, "
        f"expected={expected_sin[position, feature]}",
      )

    print("PASS llama3 RoPE cache upload")
    print(f"logical shape: {cos.shape}")
    print(f"dtype in DRAM: {cos.dtype.name}")
    print(f"bytes/table: {cos.size}")
    print("positions/tile: 16")
    print("position p: tile=p//16, tile rows=2*(p%16)..+1")
  finally:
    device.close()


def _compact_projection_data(buffer, values, row_counts):
  compact = np.zeros(buffer.shape, dtype=np.float32)
  start = 0
  for core, count in enumerate(row_counts):
    compact[core, :count] = values[start:start + count]
    start += count
  if start != len(values):
    raise AssertionError("compact projection length mismatch")
  return buffer.from_numpy(compact)


def _rope_reference(values, cosine, sine):
  heads = values.reshape(-1, HEAD_DIM)
  rotated = np.concatenate(
    (-heads[:, HEAD_DIM // 2:], heads[:, :HEAD_DIM // 2]), axis=1,
  )
  return np.add(
    np.multiply(heads, cosine[None, :], dtype=np.float32),
    np.multiply(rotated, sine[None, :], dtype=np.float32),
    dtype=np.float32,
  )


def run_decode_rope_hardware(positions=(0, 1, 127, 8191), repeats=1):
  """Validate fused Q/K RoPE and V reassembly against the host reference."""
  if repeats < 1: raise ValueError("repeats must be positive")
  positions = tuple(positions)
  if not positions or any(not 0 <= p < ROPE_CACHE_TOKENS for p in positions):
    raise ValueError(f"positions must be in 0..{ROPE_CACHE_TOKENS - 1}")

  device = Device()
  try:
    device.init_device()
    cores = device.dram.cores[:LLAMA_CORES]
    q = device.dram.buffer(
      "rope_q_input", DType.BF16, (LLAMA_CORES, 18), axis=0, cores=cores,
    )
    k = device.dram.buffer(
      "rope_k_input", DType.BF16, (LLAMA_CORES, 5), axis=0, cores=cores,
    )
    v = device.dram.buffer(
      "rope_v_input", DType.BF16, (LLAMA_CORES, 5), axis=0, cores=cores,
    )
    q_output = device.dram.buffer(
      "rope_q_output", DType.BF16, (Q_HEADS, HEAD_DIM), axis=0,
      global_address=True,
    )
    k_output = device.dram.buffer(
      "rope_k_output", DType.BF16, (KV_HEADS, HEAD_DIM), axis=0,
      global_address=True,
    )
    v_output = device.dram.buffer(
      "rope_v_output", DType.BF16, (KV_HEADS, HEAD_DIM), axis=0,
      global_address=True,
    )
    cos, sin = upload_rope_cache(device)

    rng = np.random.default_rng(4)
    q_values = rng.normal(0, 0.5, Q_PROJ_DIM).astype(np.float32)
    k_values = rng.normal(0, 0.5, KV_PROJ_DIM).astype(np.float32)
    v_values = rng.normal(0, 0.5, KV_PROJ_DIM).astype(np.float32)
    q_data = _compact_projection_data(
      q, q_values, (18,) * 42 + (17,) * 76,
    )
    k_data = _compact_projection_data(
      k, k_values, (5,) * 40 + (4,) * 78,
    )
    v_data = _compact_projection_data(
      v, v_values, (5,) * 40 + (4,) * 78,
    )
    q_reference_input = _projection_values(
      q, q_data, (18,) * 42 + (17,) * 76,
    )
    k_reference_input = _projection_values(
      k, k_data, (5,) * 40 + (4,) * 78,
    )
    v_reference_input = _projection_values(
      v, v_data, (5,) * 40 + (4,) * 78,
    )
    cos_values, sin_values = rope_table()
    cos_reference = cos.to_numpy(_bf16_rne_bytes(cos_values))
    sin_reference = sin.to_numpy(_bf16_rne_bytes(sin_values))

    device.write(q, q_data)
    device.write(k, k_data)
    device.write(v, v_data)
    program = decode_rope(
      q, k, v, cos, sin, q_output, k_output, v_output,
    )
    metrics, samples = {}, []
    for position in positions:
      device.queue(program, params={"start_pos": position})
      q_readback = device.queue_read(q_output)
      k_readback = device.queue_read(k_output)
      v_readback = device.queue_read(v_output)
      timestamps = device.run(timeout=5.0)
      samples.append(timestamps[-1].us)

      for name, actual, source_values in (
        ("q", q_output.to_numpy(q_readback.result()), q_reference_input),
        ("k", k_output.to_numpy(k_readback.result()), k_reference_input),
        ("v", v_output.to_numpy(v_readback.result()), v_reference_input),
      ):
        expected_values = (
          source_values.reshape(KV_HEADS, HEAD_DIM)
          if name == "v" else
          _rope_reference(
            source_values, cos_reference[position], sin_reference[position],
          )
        )
        expected_buffer = {
          "q": q_output, "k": k_output, "v": v_output,
        }[name]
        expected = expected_buffer.to_numpy(
          _bf16_rne_bytes(expected_values),
        )
        difference = np.subtract(actual, expected, dtype=np.float32)
        error = np.abs(difference)
        relative_l2 = float(
          np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
        )
        if (
          not np.all(np.isfinite(actual)) or
          float(error.max()) > 0.01 or relative_l2 > 0.005
        ):
          head, feature = np.unravel_index(int(error.argmax()), error.shape)
          raise AssertionError(
            f"decode Q/K RoPE + V gather {name} mismatch at position "
            f"{position}, "
            f"head {head}, feature {feature}: actual={actual[head, feature]}, "
            f"expected={expected[head, feature]}, max_abs={error.max()}, "
            f"relative_l2={relative_l2}, actual_min={actual.min()}, "
            f"actual_max={actual.max()}, actual_nonzero={np.count_nonzero(actual)}",
          )
        metrics[position, name] = (
          int(np.count_nonzero(actual == expected)),
          float(error.max()), relative_l2,
        )

    for _ in range(repeats - 1):
      samples.append(device.run(
        program, params={"start_pos": positions[-1]}, timeout=5.0,
      )[-1].us)

    print("PASS llama3 fused decode Q/K RoPE + V reassembly")
    print(f"workers: {ROPE_CORES} ({Q_HEADS} Q + {KV_HEADS} K/V)")
    print(f"positions: {positions}")
    for position in positions:
      for name, elements in (
        ("q", Q_PROJ_DIM), ("k", KV_PROJ_DIM), ("v", KV_PROJ_DIM),
      ):
        exact, max_abs, relative_l2 = metrics[position, name]
        print(
          f"position {position} {name}: exact={exact}/{elements}, "
          f"max_abs={max_abs:.6g}, relative_l2={relative_l2:.6g}",
        )
    print(
      f"latency us: min={min(samples):.3f}, median={np.median(samples):.3f}, "
      f"max={max(samples):.3f}",
    )
  finally:
    device.close()


def run_decode_kv_cache_hardware(
  positions=(0, 1, 15, 16, 31, 32, 127, 8191), repeats=1,
):
  """Validate one-token K/V cache writes and untouched cache contents."""
  if repeats < 1: raise ValueError("repeats must be positive")
  positions = tuple(positions)
  if (
    not positions or len(set(positions)) != len(positions) or
    any(not 0 <= position < ROPE_CACHE_TOKENS for position in positions)
  ):
    raise ValueError(
      f"positions must be unique values in 0..{ROPE_CACHE_TOKENS - 1}",
    )

  device = Device()
  try:
    device.init_device()
    k = device.dram.buffer(
      "decode_cache_k", DType.BF16, (KV_HEADS, HEAD_DIM), axis=0,
      global_address=True,
    )
    v = device.dram.buffer(
      "decode_cache_v", DType.BF16, (KV_HEADS, HEAD_DIM), axis=0,
      global_address=True,
    )
    key_cache = device.dram.buffer(
      "key_cache", DType.BF16, KV_CACHE_STORAGE_SHAPE, axis=0,
      global_address=True,
    )
    value_cache = device.dram.buffer(
      "value_cache", DType.BF16, KV_CACHE_STORAGE_SHAPE, axis=0,
      global_address=True,
    )

    sentinel = np.float32(0.25)
    sentinel_bytes = _bf16_rne_bytes(np.array([sentinel], dtype=np.float32))
    device.write(key_cache, sentinel_bytes * (key_cache.size // 2))
    device.write(value_cache, sentinel_bytes * (value_cache.size // 2))
    device.run(timeout=5.0)

    rng = np.random.default_rng(5)
    expected_rows = {}
    program = kv_cache_write(k, v, key_cache, value_cache)
    samples = []
    for index, position in enumerate(positions):
      k_values = rng.normal(0, 0.5, k.shape).astype(np.float32)
      v_values = rng.normal(0, 0.5, v.shape).astype(np.float32)
      k_data, v_data = k.from_numpy(k_values), v.from_numpy(v_values)
      expected_rows[position] = (
        k.to_numpy(k_data), v.to_numpy(v_data),
      )
      device.write(k, k_data)
      device.write(v, v_data)
      device.queue(program, params={"start_pos": position})
      if index == len(positions) - 1:
        key_readback = device.queue_read(key_cache)
        value_readback = device.queue_read(value_cache)
      samples.append(device.run(timeout=5.0)[-1].us)

    actual_caches = (
      key_cache.to_numpy(key_readback.result()),
      value_cache.to_numpy(value_readback.result()),
    )
    for cache_index, (name, actual) in enumerate(zip(
      ("key", "value"), actual_caches,
    )):
      for position, rows in expected_rows.items():
        expected = rows[cache_index]
        time_block, row = divmod(position, KV_CACHE_TOKEN_BLOCK)
        for feature_half in range(KV_CACHE_FEATURE_TILES):
          tile = time_block * KV_CACHE_FEATURE_TILES + feature_half
          row_values = actual[:, tile, row * 32:(row + 1) * 32]
          expected_values = expected[
            :, feature_half * 32:(feature_half + 1) * 32
          ]
          if not np.array_equal(row_values, expected_values):
            head, feature = np.argwhere(row_values != expected_values)[0]
            raise AssertionError(
              f"{name} cache mismatch at position {position}, head {head}, "
              f"feature {feature_half * 32 + feature}: "
              f"actual={row_values[head, feature]}, "
              f"expected={expected_values[head, feature]}",
            )
          actual[:, tile, row * 32:(row + 1) * 32] = sentinel
      if not np.all(actual == sentinel):
        head, tile, element = np.argwhere(actual != sentinel)[0]
        raise AssertionError(
          f"{name} cache unexpectedly changed at head {head}, tile {tile}, "
          f"element {element}: actual={actual[head, tile, element]}",
        )

    for _ in range(repeats - 1):
      samples.append(device.run(
        program, params={"start_pos": positions[-1]}, timeout=5.0,
      )[-1].us)

    print("PASS llama3 one-token decode K/V cache write")
    print(f"logical cache shape: {KV_CACHE_SHAPE}")
    print(f"tile storage shape: {KV_CACHE_STORAGE_SHAPE}")
    print(f"positions: {positions}")
    print(f"workers: {KV_HEADS} BRISC-only (one per KV head)")
    print(
      f"latency us: min={min(samples):.3f}, median={np.median(samples):.3f}, "
      f"max={max(samples):.3f}",
    )
  finally:
    device.close()


def run_decode_gqa_scores_hardware(tokens=127, repeats=1):
  """Validate Q @ K.T / sqrt(64) for one decode attention step."""
  if not 1 <= tokens <= ROPE_CACHE_TOKENS:
    raise ValueError(
      f"tokens must be in 1..{ROPE_CACHE_TOKENS}",
    )
  if repeats < 1: raise ValueError("repeats must be positive")
  blocks = (tokens + KV_CACHE_TOKEN_BLOCK - 1) // KV_CACHE_TOKEN_BLOCK

  device = Device()
  try:
    device.init_device()
    q = device.dram.buffer(
      "gqa_q", DType.BF16, (Q_HEADS, HEAD_DIM), axis=0,
      global_address=True,
    )
    key_cache = device.dram.buffer(
      "gqa_key_cache", DType.BF16, KV_CACHE_STORAGE_SHAPE, axis=0,
      global_address=True,
    )
    scores = device.dram.buffer(
      "gqa_scores", DType.F32, GQA_SCORE_STORAGE_SHAPE, axis=0,
      global_address=True,
    )

    rng = np.random.default_rng(6)
    q_values = rng.normal(0, 0.25, q.shape).astype(np.float32)
    key_values = rng.normal(
      0, 0.25, (KV_HEADS, tokens, HEAD_DIM),
    ).astype(np.float32)
    cache_values = np.zeros(KV_CACHE_STORAGE_SHAPE, dtype=np.float32)
    for head in range(KV_HEADS):
      for block in range(blocks):
        start, end = block * 32, min((block + 1) * 32, tokens)
        count = end - start
        for feature_half in range(KV_CACHE_FEATURE_TILES):
          tile = block * KV_CACHE_FEATURE_TILES + feature_half
          cache_values[head, tile].reshape(32, 32)[:count] = key_values[
            head, start:end,
            feature_half * 32:(feature_half + 1) * 32,
          ]

    q_data = q.from_numpy(q_values)
    cache_data = key_cache.from_numpy(cache_values)
    q_reference = q.to_numpy(q_data)
    cache_reference = key_cache.to_numpy(cache_data)
    key_reference = np.empty((KV_HEADS, tokens, HEAD_DIM), dtype=np.float32)
    for head in range(KV_HEADS):
      for block in range(blocks):
        start, end = block * 32, min((block + 1) * 32, tokens)
        count = end - start
        for feature_half in range(KV_CACHE_FEATURE_TILES):
          tile = block * KV_CACHE_FEATURE_TILES + feature_half
          key_reference[
            head, start:end,
            feature_half * 32:(feature_half + 1) * 32,
          ] = cache_reference[head, tile].reshape(32, 32)[:count]

    device.write(q, q_data)
    device.write(key_cache, cache_data)
    program = gqa_scores(q, key_cache, scores)
    device.queue(program, params={"kv_blocks": blocks})
    readback = device.queue_read(scores)
    timestamps = device.run(timeout=5.0)
    samples = [timestamps[-1].us]

    score_storage = scores.to_numpy(readback.result())
    actual = np.empty((Q_HEADS, tokens), dtype=np.float32)
    expected = np.empty_like(actual)
    scale = np.float32(HEAD_DIM ** -0.5)
    for head in range(KV_HEADS):
      head_scores = np.concatenate([
        score_storage[head, block].reshape(32, 32)[:GQA_GROUP_SIZE]
        for block in range(blocks)
      ], axis=1)[:, :tokens]
      query_start = head * GQA_GROUP_SIZE
      actual[query_start:query_start + GQA_GROUP_SIZE] = head_scores
      expected[query_start:query_start + GQA_GROUP_SIZE] = (
        q_reference[query_start:query_start + GQA_GROUP_SIZE] @
        key_reference[head].T
      ) * scale

    difference = np.subtract(actual, expected, dtype=np.float32)
    relative_l2 = float(
      np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
    )
    pcc = float(np.corrcoef(actual.reshape(-1), expected.reshape(-1))[0, 1])
    if (
      not np.all(np.isfinite(actual)) or relative_l2 > 0.01 or pcc < 0.999
    ):
      error = np.abs(difference)
      query_head, token = np.unravel_index(int(error.argmax()), error.shape)
      raise AssertionError(
        f"decode GQA score mismatch at query head {query_head}, token {token}: "
        f"actual={actual[query_head, token]}, "
        f"expected={expected[query_head, token]}, "
        f"max_abs={error.max()}, relative_l2={relative_l2}, PCC={pcc}",
      )

    for _ in range(repeats - 1):
      samples.append(device.run(
        program, params={"kv_blocks": blocks}, timeout=5.0,
      )[-1].us)

    print("PASS llama3 decode GQA scores")
    print(f"logical operation: [32, 64] grouped with [8, {tokens}, 64]")
    print(f"output: FP32[32, {tokens}] in {KV_HEADS * blocks} tiles")
    print(f"workers: {KV_HEADS} (one per KV head / four Q heads)")
    print(f"history blocks: {blocks}")
    print(f"relative L2: {relative_l2:.6g}")
    print(f"PCC: {pcc:.9f}")
    print(
      f"latency us: min={min(samples):.3f}, median={np.median(samples):.3f}, "
      f"max={max(samples):.3f}",
    )
  finally:
    device.close()


def run_decode_gqa_softmax_hardware(tokens=127, repeats=1):
  """Validate the eight-worker decode softmax including tail masking."""
  if not 1 <= tokens <= ROPE_CACHE_TOKENS:
    raise ValueError(
      f"tokens must be in 1..{ROPE_CACHE_TOKENS}",
    )
  if repeats < 1: raise ValueError("repeats must be positive")
  blocks = (tokens + KV_CACHE_TOKEN_BLOCK - 1) // KV_CACHE_TOKEN_BLOCK
  tail = (tokens - 1) % KV_CACHE_TOKEN_BLOCK + 1

  device = Device()
  try:
    device.init_device()
    scores = device.dram.buffer(
      "softmax_scores", DType.F32, GQA_SCORE_STORAGE_SHAPE, axis=0,
      global_address=True,
    )
    probabilities = device.dram.buffer(
      "softmax_probabilities", DType.BF16, GQA_SCORE_STORAGE_SHAPE,
      axis=0, global_address=True,
    )

    rng = np.random.default_rng(7)
    logical_scores = rng.normal(
      0, 1.5, (Q_HEADS, tokens),
    ).astype(np.float32)
    score_storage = np.zeros(GQA_SCORE_STORAGE_SHAPE, dtype=np.float32)
    for head in range(KV_HEADS):
      query_start = head * GQA_GROUP_SIZE
      for block in range(blocks):
        start, end = block * 32, min((block + 1) * 32, tokens)
        tile = score_storage[head, block].reshape(32, 32)
        tile[:GQA_GROUP_SIZE, :end - start] = logical_scores[
          query_start:query_start + GQA_GROUP_SIZE, start:end,
        ]
        if block == blocks - 1 and end - start < 32:
          # A large positive padding value proves that the kernel masks the
          # tail before both the maximum and exponential passes.
          tile[:GQA_GROUP_SIZE, end - start:] = np.float32(32.0)

    score_data = scores.from_numpy(score_storage)
    bf16_words = np.frombuffer(
      _bf16_rne_bytes(logical_scores), dtype="<u2",
    ).astype(np.uint32)
    bf16_scores = (bf16_words << 16).view(np.float32).reshape(
      logical_scores.shape,
    )
    shifted = bf16_scores - np.max(bf16_scores, axis=1, keepdims=True)
    expected_values = np.exp(shifted, dtype=np.float32)
    expected_values /= np.sum(
      expected_values, axis=1, keepdims=True, dtype=np.float32,
    )
    expected_words = np.frombuffer(
      _bf16_rne_bytes(expected_values), dtype="<u2",
    ).astype(np.uint32)
    expected = (expected_words << 16).view(np.float32).reshape(
      expected_values.shape,
    )

    sentinel = np.float32(-0.5)
    probability_initial = np.full(
      GQA_SCORE_STORAGE_SHAPE, sentinel, dtype=np.float32,
    )
    device.write(scores, score_data)
    device.write(probabilities, probabilities.from_numpy(probability_initial))
    program = gqa_softmax(scores, probabilities)
    params = {"kv_blocks": blocks, "valid_columns": tail}
    device.queue(program, params=params)
    readback = device.queue_read(probabilities)
    timestamps = device.run(timeout=5.0)
    samples = [timestamps[-1].us]

    probability_storage = probabilities.to_numpy(readback.result())
    actual = np.empty((Q_HEADS, tokens), dtype=np.float32)
    for head in range(KV_HEADS):
      query_start = head * GQA_GROUP_SIZE
      head_probabilities = np.concatenate([
        probability_storage[head, block].reshape(32, 32)[:GQA_GROUP_SIZE]
        for block in range(blocks)
      ], axis=1)
      actual[query_start:query_start + GQA_GROUP_SIZE] = (
        head_probabilities[:, :tokens]
      )
      final_tile = probability_storage[
        head, blocks - 1
      ].reshape(32, 32)[:GQA_GROUP_SIZE]
      if tail < 32 and np.any(final_tile[:, tail:] != 0):
        row, column = np.argwhere(
          final_tile[:, tail:] != 0,
        )[0]
        raise AssertionError(
          f"decode softmax padding is nonzero for KV head {head}, "
          f"row {row}, final-tile column {tail + column}",
        )

    if blocks < KV_CACHE_TIME_BLOCKS:
      untouched = probability_storage[:, blocks:]
      if not np.all(untouched == sentinel):
        head, block, element = np.argwhere(untouched != sentinel)[0]
        raise AssertionError(
          f"decode softmax wrote inactive block {blocks + block}, "
          f"head {head}, element {element}",
        )

    difference = np.subtract(actual, expected, dtype=np.float32)
    error = np.abs(difference)
    relative_l2 = float(
      np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
    )
    expected_flat, actual_flat = expected.reshape(-1), actual.reshape(-1)
    pcc = (
      1.0 if float(np.std(expected_flat)) == 0.0 else
      float(np.corrcoef(actual_flat, expected_flat)[0, 1])
    )
    row_sum_error = float(np.max(np.abs(
      np.sum(actual, axis=1, dtype=np.float32) - np.float32(1.0),
    )))
    if (
      not np.all(np.isfinite(actual)) or float(error.max()) > 0.01 or
      relative_l2 > 0.02 or pcc < 0.999 or row_sum_error > 0.02
    ):
      query_head, token = np.unravel_index(int(error.argmax()), error.shape)
      raise AssertionError(
        f"decode GQA softmax mismatch at query head {query_head}, "
        f"token {token}: actual={actual[query_head, token]}, "
        f"expected={expected[query_head, token]}, max_abs={error.max()}, "
        f"relative_l2={relative_l2}, PCC={pcc}, "
        f"row_sum_error={row_sum_error}",
      )

    for _ in range(repeats - 1):
      samples.append(device.run(
        program, params=params, timeout=5.0,
      )[-1].us)

    print("PASS llama3 decode GQA softmax")
    print(f"logical shape: FP32[32, {tokens}] -> BF16[32, {tokens}]")
    print(f"workers: {KV_HEADS} (four rows per KV head)")
    print(f"history blocks: {blocks}, valid final columns: {tail}")
    print(f"max abs error: {error.max():.6g}")
    print(f"relative L2: {relative_l2:.6g}")
    print(f"PCC: {pcc:.9f}")
    print(f"max row-sum error: {row_sum_error:.6g}")
    print(
      f"latency us: min={min(samples):.3f}, median={np.median(samples):.3f}, "
      f"max={max(samples):.3f}",
    )
  finally:
    device.close()


def run_decode_qkv_hardware(
  safetensor_path="weights/model.safetensors", repeats=1,
):
  """Validate the three layer-0 decode projections from fixed RMS layout."""
  if repeats < 1: raise ValueError("repeats must be positive")
  device = Device()
  try:
    device.init_device()
    cores = device.dram.cores[:LLAMA_CORES]
    x = device.dram.buffer(
      "qkv_x", DType.BF16, (PREFILL_CAPACITY, EMBED_DIM), axis=0,
      cores=cores,
    )
    projection_specs = (
      ("q", Q_PROJ_DIM, "model.layers.0.self_attn.q_proj.weight"),
      ("k", KV_PROJ_DIM, "model.layers.0.self_attn.k_proj.weight"),
      ("v", KV_PROJ_DIM, "model.layers.0.self_attn.v_proj.weight"),
    )
    weights, outputs, programs, weight_data = {}, {}, {}, {}
    for name, rows, tensor_name in projection_specs:
      weight = device.dram.buffer(
        f"{name}_proj_weight", DType.BF16, (rows, EMBED_DIM), axis=0,
        cores=cores,
      )
      output = device.dram.buffer(
        f"{name}_proj_output", DType.BF16,
        (LLAMA_CORES, weight.items_per_core), axis=0, cores=cores,
      )
      weights[name], outputs[name] = weight, output
      weight_data[name] = weight.from_safetensor(
        tensor_name, safetensor_path,
      )
      programs[name] = decode_projection(x, weight, output)

    rng = np.random.default_rng(3)
    values = np.zeros(x.shape, dtype=np.float32)
    values[0] = rng.normal(0, 0.25, EMBED_DIM).astype(np.float32)
    x_data = x.from_numpy(values)
    x_reference = x.to_numpy(x_data)[0]

    device.write(x, x_data)
    for name, _, _ in projection_specs:
      device.write(weights[name], weight_data[name])
    for name, _, _ in projection_specs:
      device.queue(programs[name])
    readbacks = {
      name: device.queue_read(outputs[name])
      for name, _, _ in projection_specs
    }
    timestamps = device.run(timeout=5.0)

    metrics = {}
    for name, _, _ in projection_specs:
      weight = weights[name]
      actual = _projection_values(
        outputs[name], readbacks[name].result(), weight.item_counts,
      )
      expected = np.sum(
        np.multiply(
          weight.to_numpy(weight_data[name]), x_reference[None, :],
          dtype=np.float32,
        ),
        axis=1, dtype=np.float32,
      )
      difference = np.subtract(actual, expected, dtype=np.float32)
      error = np.abs(difference)
      relative_l2 = float(
        np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
      )
      pcc = float(np.corrcoef(actual, expected)[0, 1])
      if (
        not np.all(np.isfinite(actual)) or relative_l2 > 0.05 or pcc < 0.999
      ):
        row = int(error.argmax())
        raise AssertionError(
          f"{name}_proj mismatch at output row {row}: "
          f"actual={actual[row]}, expected={expected[row]}, "
          f"max_abs={error.max()}, relative_l2={relative_l2}, PCC={pcc}",
        )
      metrics[name] = float(error.max()), relative_l2, pcc

    samples = {name: [timestamps[index].us] for index, (name, _, _) in enumerate(projection_specs)}
    for _ in range(repeats - 1):
      for name, _, _ in projection_specs:
        samples[name].append(device.run(programs[name], timeout=5.0)[-1].us)

    print("PASS llama3 decode QKV projections")
    print(f"weights: {safetensor_path}")
    print(f"input: ({PREFILL_CAPACITY}, {EMBED_DIM}), token 0 only")
    print(f"cores: {LLAMA_CORES}")
    for name, rows, _ in projection_specs:
      weight = weights[name]
      max_abs, relative_l2, pcc = metrics[name]
      print(
        f"{name}: ({rows}, {EMBED_DIM}) @ ({EMBED_DIM},) -> ({rows},); "
        f"rows/core={min(weight.item_counts)}..{max(weight.item_counts)}, "
        f"compact={outputs[name].shape}, median={np.median(samples[name]):.3f} us, "
        f"max_abs={max_abs:.6g}, rel_l2={relative_l2:.6g}, PCC={pcc:.9f}"
      )
  finally:
    device.close()


def run_prefill_frontend_hardware(
  valid_s=200, vocab_size=257, embedding_safetensor_path=None,
  rmsnorm_safetensor_path="weights/model.safetensors",
  qkv=False,
):
  """Validate embedding -> RMSNorm, optionally followed by token-0 Q/K/V."""
  if not 0 < valid_s <= PREFILL_CAPACITY:
    raise ValueError(f"valid_s must be in 1..{PREFILL_CAPACITY}")
  if embedding_safetensor_path is not None:
    vocab_size = VOCAB_SIZE
  if not 1 < vocab_size <= VOCAB_SIZE:
    raise ValueError(f"vocab_size must be in 2..{VOCAB_SIZE}")

  device = Device()
  try:
    device.init_device()
    cores = device.dram.cores[:LLAMA_CORES]
    activation_shape = (PREFILL_CAPACITY, EMBED_DIM)
    token_ids = device.dram.buffer(
      "token_ids", DType.U32, (PREFILL_CAPACITY,), global_address=True,
    )
    embedding_weight = device.dram.buffer(
      "embedding_weight", DType.BF16, (vocab_size, EMBED_DIM), axis=0,
      global_address=True,
    )
    embedded = device.dram.buffer(
      "embedded", DType.BF16, activation_shape, axis=0, cores=cores,
    )
    rmsnorm_weight = device.dram.buffer(
      "rmsnorm_weight", DType.BF16, (EMBED_DIM,), global_address=True,
    )
    normalized = device.dram.buffer(
      "normalized", DType.BF16, activation_shape, axis=0, cores=cores,
    )
    projection_specs = (
      ("q", Q_PROJ_DIM, "model.layers.0.self_attn.q_proj.weight"),
      ("k", KV_PROJ_DIM, "model.layers.0.self_attn.k_proj.weight"),
      ("v", KV_PROJ_DIM, "model.layers.0.self_attn.v_proj.weight"),
    ) if qkv else ()
    projection_weights, projection_outputs = {}, {}
    for name, rows, _ in projection_specs:
      weight = device.dram.buffer(
        f"frontend_{name}_weight", DType.BF16, (rows, EMBED_DIM),
        axis=0, cores=cores,
      )
      projection_weights[name] = weight
      projection_outputs[name] = device.dram.buffer(
        f"frontend_{name}_output", DType.BF16,
        (LLAMA_CORES, weight.items_per_core), axis=0, cores=cores,
      )

    if embedded.cores != normalized.cores or embedded.item_starts != normalized.item_starts:
      raise AssertionError("embedding and RMSNorm activation shards differ")

    rng = np.random.default_rng(2)
    ids = np.zeros(PREFILL_CAPACITY, dtype=np.uint32)
    ids[:valid_s] = rng.integers(
      0, vocab_size, size=valid_s, dtype=np.uint32,
    )
    boundary_ids = np.asarray(
      (0, 1, vocab_size - 2, vocab_size - 1), dtype=np.uint32,
    )
    ids[:min(valid_s, len(boundary_ids))] = boundary_ids[:valid_s]
    ids_data = token_ids.from_numpy(ids)

    if embedding_safetensor_path is None:
      rows = np.arange(vocab_size, dtype=np.float32)[:, None]
      columns = np.arange(EMBED_DIM, dtype=np.float32)[None, :]
      embedding_values = ((rows * 17 + columns * 3) % 251 - 125) / 32
      embedding_data = embedding_weight.from_numpy(embedding_values)
    else:
      embedding_data = embedding_weight.from_safetensor(
        "model.embed_tokens.weight", embedding_safetensor_path,
      )
    gamma_data = rmsnorm_weight.from_safetensor(
      "model.layers.0.input_layernorm.weight", rmsnorm_safetensor_path,
    )
    projection_data = {
      name: projection_weights[name].from_safetensor(
        tensor_name, rmsnorm_safetensor_path,
      )
      for name, _, tensor_name in projection_specs
    }

    embedding_reference = embedding_weight.to_numpy(embedding_data)[
      ids[:valid_s]
    ]
    gamma_reference = rmsnorm_weight.to_numpy(gamma_data)
    squares = np.multiply(
      embedding_reference, embedding_reference, dtype=np.float32,
    )
    mean_square = np.sum(squares, axis=1, dtype=np.float32) * np.float32(
      1.0 / EMBED_DIM,
    )
    scale = np.float32(1.0) / np.sqrt(
      mean_square + np.float32(1e-5),
    )
    normalized_values = np.zeros(activation_shape, dtype=np.float32)
    normalized_values[:valid_s] = np.multiply(
      np.multiply(
        embedding_reference, scale[:, None], dtype=np.float32,
      ),
      gamma_reference[None, :], dtype=np.float32,
    )
    normalized_reference = normalized.to_numpy(
      normalized.from_numpy(normalized_values),
    )[:valid_s]

    device.write(token_ids, ids_data)
    device.write(embedding_weight, embedding_data)
    device.write(rmsnorm_weight, gamma_data)
    for name, _, _ in projection_specs:
      device.write(projection_weights[name], projection_data[name])
    device.queue(
      embedding(token_ids, embedding_weight, embedded),
      params={"valid_s": valid_s},
    )
    device.queue(
      rmsnorm(embedded, rmsnorm_weight, normalized),
      params={"valid_s": valid_s},
    )
    for name, _, _ in projection_specs:
      device.queue(decode_projection(
        normalized, projection_weights[name], projection_outputs[name],
      ))
    embedded_readback = device.queue_read(embedded)
    normalized_readback = device.queue_read(normalized)
    projection_readbacks = {
      name: device.queue_read(projection_outputs[name])
      for name, _, _ in projection_specs
    }
    timestamps = device.run(timeout=5.0)

    embedded_actual = embedded.to_numpy(embedded_readback.result())[:valid_s]
    if not np.array_equal(embedded_actual, embedding_reference):
      error = np.abs(embedded_actual - embedding_reference)
      token, feature = np.unravel_index(int(error.argmax()), error.shape)
      raise AssertionError(
        f"frontend embedding mismatch at token {token}, feature {feature}: "
        f"actual={embedded_actual[token, feature]}, "
        f"expected={embedding_reference[token, feature]}",
      )

    normalized_actual = normalized.to_numpy(
      normalized_readback.result(),
    )[:valid_s]
    rms_difference = np.subtract(
      normalized_actual, normalized_reference, dtype=np.float32,
    )
    rms_error = np.abs(rms_difference)
    rms_relative_l2 = float(
      np.linalg.norm(rms_difference) /
      (np.linalg.norm(normalized_reference) + 1e-12),
    )
    rms_pcc = float(np.corrcoef(
      normalized_actual.reshape(-1), normalized_reference.reshape(-1),
    )[0, 1])
    if (
      not np.all(np.isfinite(normalized_actual)) or
      float(rms_error.max()) > 0.05 or
      rms_relative_l2 > 0.01 or rms_pcc < 0.999
    ):
      token, feature = np.unravel_index(
        int(rms_error.argmax()), rms_error.shape,
      )
      raise AssertionError(
        f"frontend RMSNorm mismatch at token {token}, feature {feature}: "
        f"actual={normalized_actual[token, feature]}, "
        f"expected={normalized_reference[token, feature]}, "
        f"max_abs={rms_error.max()}, relative_l2={rms_relative_l2}, "
        f"PCC={rms_pcc}",
      )

    projection_metrics = {}
    for name, _, _ in projection_specs:
      weight = projection_weights[name]
      actual = _projection_values(
        projection_outputs[name], projection_readbacks[name].result(),
        weight.item_counts,
      )
      expected = np.sum(
        np.multiply(
          weight.to_numpy(projection_data[name]),
          normalized_reference[0][None, :], dtype=np.float32,
        ),
        axis=1, dtype=np.float32,
      )
      difference = np.subtract(actual, expected, dtype=np.float32)
      error = np.abs(difference)
      relative_l2 = float(
        np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
      )
      pcc = float(np.corrcoef(actual, expected)[0, 1])
      if (
        not np.all(np.isfinite(actual)) or
        relative_l2 > 0.01 or pcc < 0.9999
      ):
        row = int(error.argmax())
        raise AssertionError(
          f"frontend {name}_proj mismatch at output row {row}: "
          f"actual={actual[row]}, expected={expected[row]}, "
          f"max_abs={error.max()}, relative_l2={relative_l2}, PCC={pcc}",
        )
      projection_metrics[name] = float(error.max()), relative_l2, pcc

    print("PASS llama3 prefill frontend")
    print(f"embedding weights: {embedding_safetensor_path or 'synthetic'}")
    print("RMSNorm weight: model.layers.0.input_layernorm.weight")
    print(f"valid_s: {valid_s}")
    print(f"capacity: {PREFILL_CAPACITY}")
    print(f"cores: {LLAMA_CORES}")
    print(f"tokens/core: min={min(embedded.item_counts)}, max={max(embedded.item_counts)}")
    print(f"embedding kernel: {timestamps[0].us:.3f} us")
    print(f"RMSNorm kernel: {timestamps[1].us:.3f} us")
    print(f"RMSNorm max abs error: {rms_error.max():.6g}")
    print(f"RMSNorm relative L2: {rms_relative_l2:.6g}")
    print(f"RMSNorm PCC: {rms_pcc:.9f}")
    for index, (name, rows, _) in enumerate(projection_specs, start=2):
      max_abs, relative_l2, projection_pcc = projection_metrics[name]
      print(
        f"{name}_proj: ({rows}, {EMBED_DIM}) @ ({EMBED_DIM},), "
        f"kernel={timestamps[index].us:.3f} us, max_abs={max_abs:.6g}, "
        f"relative_l2={relative_l2:.6g}, PCC={projection_pcc:.9f}"
      )
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
  parser.add_argument("--frontend", action="store_true")
  parser.add_argument("--qkv", action="store_true")
  parser.add_argument("--rope-cache", action="store_true")
  parser.add_argument("--rope", action="store_true")
  parser.add_argument("--kv-cache", action="store_true")
  parser.add_argument("--gqa-scores", action="store_true")
  parser.add_argument("--softmax", action="store_true")
  parser.add_argument("--decode", action="store_true")
  parser.add_argument("--core-start", type=int, default=0)
  parser.add_argument("--repeats", type=int, default=5)
  args = parser.parse_args()
  if args.softmax:
    run_decode_gqa_softmax_hardware(args.seq_len, args.repeats)
  elif args.gqa_scores:
    run_decode_gqa_scores_hardware(args.seq_len, args.repeats)
  elif args.kv_cache:
    run_decode_kv_cache_hardware(repeats=args.repeats)
  elif args.rope:
    run_decode_rope_hardware(repeats=args.repeats)
  elif args.rope_cache:
    run_rope_cache_hardware()
  elif args.frontend:
    run_prefill_frontend_hardware(
      args.seq_len,
      args.vocab_size,
      args.safetensor,
      args.safetensor or "weights/model.safetensors",
      args.qkv,
    )
  elif args.qkv:
    run_decode_qkv_hardware(
      args.safetensor or "weights/model.safetensors", args.repeats,
    )
  elif args.rmsnorm:
    run_rmsnorm_hardware(
      args.seq_len, args.repeats,
      args.safetensor or "weights/model.safetensors",
      args.core_start,
      args.decode,
    )
  else:
    run_embedding_hardware(
      args.seq_len, args.vocab_size, args.safetensor, args.repeats,
    )
