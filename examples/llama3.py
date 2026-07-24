from pathlib import Path

import argparse
import math
import numpy as np
import struct
import time

from asm import Cond
from cq import UnicastWrite, mcast_coords, noc_coord
from device import Device
from fw.consts import CQConfig, TensixL1
from pcie import P100_WORKER_CORES
from program import Buffer, Const, DType, Program, rectangles
from isa import R, Tensix as TT
from ttk.cb import CB
from ttk.sfpu import (
  LaneConfig, LReg, SfpuFormat, SfpuProgram, SfpuProgramBuilder,
)
from ttk.sync import Sem, SemWait, Stall, Wait, sem_get, sem_wait, stall
from ttk.unpack import UnpackTarget


VOCAB_SIZE = 128256
EMBED_DIM = 2048
PREFILL_CAPACITY = 1024
EMBEDDING_TILES = EMBED_DIM // 1024
LLAMA_CORES = 118
LLAMA_LAYERS = 16
EOS_TOKEN_IDS = frozenset((128001, 128008, 128009))
TOKENS_PER_CORE, NINE_TOKEN_CORES = divmod(PREFILL_CAPACITY, LLAMA_CORES)
CORE_TOKEN_COUNTS = (
  (TOKENS_PER_CORE + 1,) * NINE_TOKEN_CORES +
  (TOKENS_PER_CORE,) * (LLAMA_CORES - NINE_TOKEN_CORES)
)
Q_PROJ_DIM = 2048
KV_PROJ_DIM = 512
MLP_DIM = 8192
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
GQA_CONTEXT_SHAPE = (1, EMBED_DIM)
GQA_ROW_CHUNKS = (0, 2, 16, 18)


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


def _store_tiled_u32(kernel, tile_l1, logical_index, value):
  """Store one logical U32 element into a face-tilized tile in L1."""
  with kernel.scope():
    row, column, physical, scratch, address = kernel.reg(
      5, exclude=(logical_index, value),
    )
    kernel.srli(row, logical_index, 5)
    kernel.andi(column, logical_index, 31)

    kernel.srli(scratch, row, 4)
    kernel.slli(physical, scratch, 9)
    kernel.srli(scratch, column, 4)
    kernel.slli(scratch, scratch, 8)
    kernel.add(physical, physical, scratch)
    kernel.andi(scratch, row, 15)
    kernel.slli(scratch, scratch, 4)
    kernel.add(physical, physical, scratch)
    kernel.andi(scratch, column, 15)
    kernel.add(physical, physical, scratch)

    kernel.slli(physical, physical, 2)
    kernel.li(address, tile_l1)
    kernel.add(address, address, physical)
    kernel.sw(value, address)


def _load_tiled_bf16(kernel, tiles_l1, logical_index, output):
  """Load a logical BF16 element from consecutive face-tilized L1 tiles."""
  with kernel.scope():
    tile, within, row, column, physical, scratch, address = kernel.reg(
      7, exclude=(logical_index, output),
    )
    kernel.srli(tile, logical_index, 10)
    kernel.andi(within, logical_index, 1023)
    kernel.srli(row, within, 5)
    kernel.andi(column, within, 31)

    kernel.srli(scratch, row, 4)
    kernel.slli(physical, scratch, 9)
    kernel.srli(scratch, column, 4)
    kernel.slli(scratch, scratch, 8)
    kernel.add(physical, physical, scratch)
    kernel.andi(scratch, row, 15)
    kernel.slli(scratch, scratch, 4)
    kernel.add(physical, physical, scratch)
    kernel.andi(scratch, column, 15)
    kernel.add(physical, physical, scratch)

    kernel.slli(tile, tile, 11)
    kernel.slli(physical, physical, 1)
    kernel.add(physical, physical, tile)
    kernel.li(address, tiles_l1)
    kernel.add(address, address, physical)
    kernel.lhu(output, address)


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
  input_dim = x.shape[1]
  input_tiles = input_dim // 1024
  # Token 0 starts at the allocation base. Expose its 2 or 8 physical tiles
  # through one global view so every projection core can replicate it.
  token = Buffer(
    f"{x.name}_decode_token", x.addr, x.dtype, (input_dim,), None,
    (x.cores[0],), x.banks, global_address=True,
  )
  p = Program(weight.cores, token, weight, output, fp32_dst=True)
  weight_cb = p.cb(DType.BF16, depth=4)
  scalar_cb = p.cb(DType.BF16, depth=2)
  token_l1 = p.l1(input_tiles * token.tile_size, alignment=16)
  compact_l1 = p.l1(
    output.tiles_per_item * output.tile_size, alignment=16,
  )

  p.brisc.noc.read_tiles(token, tuple(
    (tile, token_l1 + tile * token.tile_size)
    for tile in range(input_tiles)
  ))
  for local_row in p.brisc.range(local_rows):
    if input_tiles == 2:
      with p.brisc.scope():
        first, second = p.brisc.reg(2, exclude=local_row)
        p.brisc.slli(first, local_row, 1)
        p.brisc.addi(second, first, 1)
        p.brisc.noc.read_tiles_into_cb(weight, (first, second), weight_cb)
    else:
      for input_tile in range(input_tiles):
        with p.brisc.scope():
          tile, stride = p.brisc.reg(2, exclude=local_row)
          p.brisc.li(stride, input_tiles)
          p.brisc.mul(tile, local_row, stride)
          if input_tile: p.brisc.addi(tile, tile, input_tile)
          p.brisc.noc.read_into_cb(weight, tile, weight_cb)

  for _ in p.trisc0.range(local_rows):
    for input_tile in range(input_tiles):
      p.unpack.move_l1_pair(
        weight_cb, token_l1 + input_tile * token.tile_size,
      )

  accumulate_first = _dot_accumulate(reset=True)
  accumulate_next = _dot_accumulate(reset=False)
  finalize = _dot_finalize()
  for _ in p.trisc1.range(local_rows):
    for input_tile in range(input_tiles):
      p.fpu.binary("mul", dst_tile=0)
      _rms_select_tile(p.sfpu, 0)
      _rms_map_acquired(
        p.sfpu, accumulate_first if input_tile == 0 else accumulate_next,
      )
    _rms_select_tile(p.sfpu, 0)
    for word in finalize.words: p.sfpu._issue(word)
    stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
    p.sfpu.publish()

  for _ in p.trisc2.range(local_rows):
    p.pack.move_scalar(scalar_cb, tile=0)

  # One scalar pack occupies a tile. Compact local results into ordinary
  # face-tilized storage before writing the core's output shard.
  p.ncrisc.zero_words(
    compact_l1, output.tiles_per_item * output.tile_size // 4,
  )
  for local_row in p.ncrisc.range(local_rows):
    CB.wait_front(p.ncrisc, scalar_cb)
    with p.ncrisc.scope():
      source, value, row, column, byte_offset, target = p.ncrisc.reg(
        6, exclude=local_row,
      )
      CB.get_read_ptr(p.ncrisc, scalar_cb, source)
      p.ncrisc.read(value, source, bytes=2)
      p.ncrisc.srli(row, local_row, 5)
      p.ncrisc.andi(column, local_row, 31)
      with p.ncrisc.scope():
        tile, within_row, face = p.ncrisc.reg(
          3, exclude=(row, column, byte_offset),
        )
        p.ncrisc.srli(tile, row, 5)
        p.ncrisc.slli(byte_offset, tile, 11)
        p.ncrisc.andi(within_row, row, 31)
        p.ncrisc.srli(face, within_row, 4)
        p.ncrisc.slli(face, face, 10)
        p.ncrisc.add(byte_offset, byte_offset, face)
        p.ncrisc.andi(within_row, within_row, 15)
        p.ncrisc.slli(within_row, within_row, 5)
        p.ncrisc.add(byte_offset, byte_offset, within_row)
        p.ncrisc.srli(face, column, 4)
        p.ncrisc.slli(face, face, 9)
        p.ncrisc.add(byte_offset, byte_offset, face)
      p.ncrisc.andi(column, column, 15)
      p.ncrisc.slli(column, column, 1)
      p.ncrisc.add(byte_offset, byte_offset, column)
      p.ncrisc.li(target, compact_l1)
      p.ncrisc.add(target, target, byte_offset)
      p.ncrisc.write(target, value, bytes=2)
    CB.pop_front(p.ncrisc, scalar_cb)
  for tile in range(output.tiles_per_item):
    with p.ncrisc.scope():
      target_address, target_coordinate = p.ncrisc.noc._dram_tile(
        output, tile,
      )
      p.ncrisc.noc.write(
        compact_l1 + tile * output.tile_size,
        target_address, target_coordinate, output.tile_size, posted=False,
      )
  return p


def decode_projection(x: Buffer, weight: Buffer, output: Buffer) -> Program:
  """Compute one bias-free HF Linear as ``weight @ x`` over 118 cores.

  Hugging Face stores Linear weights as ``[out_features, in_features]``.
  Each core owns a contiguous set of output rows and computes the complete
  2048- or 8192-element dot product for every row. The compact output has logical shape
  ``[118, max_rows_per_core]``: one tile per core, with padding only in the
  final slot of smaller shards.
  """
  valid_x_shapes = (
    (1, EMBED_DIM), (PREFILL_CAPACITY, EMBED_DIM), (1, MLP_DIM),
  )
  if (
    x.dtype is not DType.BF16 or x.shape not in valid_x_shapes or
    x.axis != 0 or x.tiles_per_item != x.shape[1] // 1024
  ):
    raise ValueError(
      "decode projection x must be BF16[1,2048], BF16[1024,2048], "
      "or BF16[1,8192], axis=0",
    )
  valid_weight_shapes = (
    (Q_PROJ_DIM, EMBED_DIM), (KV_PROJ_DIM, EMBED_DIM),
    (MLP_DIM, EMBED_DIM), (EMBED_DIM, MLP_DIM),
    (VOCAB_SIZE, EMBED_DIM),
  )
  if (
    weight.dtype is not DType.BF16 or weight.shape not in valid_weight_shapes or
    weight.shape[1] != x.shape[1] or weight.axis != 0 or
    weight.tiles_per_item != x.shape[1] // 1024 or
    len(weight.cores) != LLAMA_CORES
  ):
    raise ValueError(
      "decode projection weight must be one of the supported Llama Q/K/V, "
      "o_proj, gate/up, down, or tied LM-head projection shapes, "
      "axis=0 over 118 cores",
    )
  expected_shape = (LLAMA_CORES, weight.items_per_core)
  if (
    output.dtype is not DType.BF16 or output.shape != expected_shape or
    output.axis != 0 or output.cores != weight.cores or
    output.item_counts != (1,) * LLAMA_CORES
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


def decode_argmax(
  logits: Buffer, output: Buffer, token_history: Buffer, host_output=None,
) -> Program:
  """Reduce logits, publish the winner, and append it to token history."""
  if (
    logits.dtype is not DType.BF16 or logits.axis != 0 or
    len(logits.cores) != LLAMA_CORES or logits.tiles_per_item != 2
  ):
    raise ValueError("argmax expects two compact BF16 logit tiles per core")
  if (
    output.dtype is not DType.U32 or output.shape != (1,) or
    not output.global_address
  ):
    raise ValueError("argmax output must be a global U32[1] buffer")
  if (
    token_history.dtype is not DType.U32 or
    token_history.shape != (ROPE_CACHE_TOKENS,) or
    not token_history.global_address
  ):
    raise ValueError(
      f"argmax token history must be global U32[{ROPE_CACHE_TOKENS}]",
    )

  local_counts = _token_counts(VOCAB_SIZE, len(logits.cores))
  local_starts, cursor = [], 0
  for count in local_counts:
    local_starts.append(cursor)
    cursor += count
  starts = Const("argmax_start", tuple(local_starts))
  counts = Const("argmax_count", local_counts)
  indices = Const("argmax_core", tuple(range(len(logits.cores))))
  write_pos = Const("write_pos", 1)
  write_token = Const("write_token", 1)
  host_address = (
    None if host_output is None else Const("argmax_host_address", host_output)
  )
  p = Program(
    logits.cores, logits, output, token_history,
    starts, counts, indices, write_pos, write_token,
    *((host_address,) if host_address is not None else ()),
  )
  logits_l1 = p.l1(logits.tiles_per_item * logits.tile_size, alignment=16)
  history_l1 = p.l1(token_history.tile_size, alignment=16)
  local = p.l1(16, alignment=16)
  runtime_l1 = p.l1(32, alignment=16)
  partials = p.l1(len(logits.cores) * 16, alignment=16)
  p.launch = (
    UnicastWrite(
      (logits.cores[0],), partials,
      (bytes(len(logits.cores) * 16),),
    ),
  )

  p.brisc.noc.read_tiles(logits, tuple(
    (tile, logits_l1 + tile * logits.tile_size)
    for tile in range(logits.tiles_per_item)
  ))
  with p.brisc.scope():
    count, start, core_index = p.brisc.reg(3)
    p.brisc.read(count, p.param_addr(counts))
    p.brisc.read(start, p.param_addr(starts))
    p.brisc.read(core_index, p.param_addr(indices))
    best_key, best_id, value, key, token, mask = p.brisc.reg(6)
    p.brisc.li(best_key, 0)
    p.brisc.li(best_id, 0)
    p.brisc.li(mask, 0x8000)
    for logical in p.brisc.range(count):
      _load_tiled_bf16(p.brisc, logits_l1, logical, value)
      with p.brisc.scope():
        sign = p.brisc.reg(exclude=(value, key, mask))
        positive = p.brisc._new_label("argmax_positive")
        keyed = p.brisc._new_label("argmax_keyed")
        p.brisc.and_(sign, value, mask)
        p.brisc.beq(sign, R.ZERO, positive)
        p.brisc.xori(key, value, -1)
        p.brisc.slli(key, key, 16)
        p.brisc.srli(key, key, 16)
        p.brisc.j(keyed)
        p.brisc.label(positive)
        p.brisc.xor(key, value, mask)
        p.brisc.label(keyed)
      skip = p.brisc._new_label("argmax_skip")
      p.brisc.bgeu(best_key, key, skip)
      p.brisc.mv(best_key, key)
      p.brisc.add(token, start, logical)
      p.brisc.mv(best_id, token)
      p.brisc.label(skip)

    p.brisc.write(local, best_key)
    p.brisc.write(local + 4, best_id)
    p.brisc.write(local + 8, 1)
    with p.brisc.scope():
      target, stride, base = p.brisc.reg(3, exclude=core_index)
      p.brisc.li(stride, 16)
      p.brisc.mul(target, core_index, stride)
      p.brisc.li(base, partials)
      p.brisc.add(target, target, base)
      p.brisc.noc.write(
        local, target, noc_coord(logits.cores[0]), 12, posted=False,
      )

    reducer_done = p.brisc._new_label("argmax_reducer_done")
    p.brisc.bne(core_index, R.ZERO, reducer_done)
    p.brisc.li(best_key, 0)
    p.brisc.li(best_id, 0)
    for index in p.brisc.range(len(logits.cores)):
      with p.brisc.scope():
        address, stride, ready, candidate_key, candidate_id, base = (
          p.brisc.reg(6)
        )
        p.brisc.li(stride, 16)
        p.brisc.mul(address, index, stride)
        p.brisc.li(base, partials)
        p.brisc.add(address, address, base)
        wait = p.brisc._new_label("argmax_wait_partial")
        ready_label = p.brisc._new_label("argmax_partial_ready")
        p.brisc.label(wait)
        p.brisc.lw(ready, address, 8)
        p.brisc.bne(ready, R.ZERO, ready_label)
        p.brisc.fence()
        p.brisc.j(wait)
        p.brisc.label(ready_label)
        p.brisc.lw(candidate_key, address, 0)
        p.brisc.lw(candidate_id, address, 4)
        skip = p.brisc._new_label("argmax_skip_partial")
        p.brisc.bgeu(best_key, candidate_key, skip)
        p.brisc.mv(best_key, candidate_key)
        p.brisc.mv(best_id, candidate_id)
        p.brisc.label(skip)
    # Scalar NoC writes require a 16-byte-aligned source address.
    p.brisc.write(local, best_id)
    if host_address is None:
      with p.brisc.scope():
        target_address, target_coordinate = p.brisc.noc._dram_tile(output, 0)
        p.brisc.noc.write(
          local, target_address, target_coordinate, 4, posted=False,
        )
    else:
      with p.brisc.scope():
        target_address, position, marker = p.brisc.reg(3)
        p.brisc.read(target_address, p.param_addr(host_address))
        p.brisc.read(position, p.param_addr(write_pos))
        p.brisc.slli(marker, position, 4)
        p.brisc.add(target_address, target_address, marker)
        p.brisc.addi(marker, position, 1)
        p.brisc.write(local + 4, marker)
        p.brisc.noc.write(
          local, target_address, CQConfig.PCIE_COORD, 16,
          target_middle_address=CQConfig.PCIE_MID, posted=False,
        )
    history_done = p.brisc._new_label("argmax_history_done")
    with p.brisc.scope():
      position, tile, within, enabled = p.brisc.reg(4)
      p.brisc.read(enabled, p.param_addr(write_token))
      p.brisc.beq(enabled, R.ZERO, history_done)
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.srli(tile, position, 10)
      p.brisc.andi(within, position, 1023)
      p.brisc.noc.read_tile(token_history, tile, history_l1)
      _store_tiled_u32(p.brisc, history_l1, within, best_id)
      target_address, target_coordinate = p.brisc.noc._dram_tile(
        token_history, tile,
      )
      p.brisc.noc.write(
        history_l1, target_address, target_coordinate,
        token_history.tile_size, posted=False,
      )
    p.brisc.label(history_done)

    # Prepare the next token's compact runtime state on device. Host-driven
    # replay may overwrite it, while autonomous replay can consume it directly.
    with p.brisc.scope():
      position, value = p.brisc.reg(2)
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.write(runtime_l1, position)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE, position)
      p.brisc.addi(value, position, 1)
      p.brisc.write(runtime_l1 + 4, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 4, value)
      p.brisc.write(runtime_l1 + 8, 1)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 8, 1)
      p.brisc.write(runtime_l1 + 12, position)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 12, position)
      p.brisc.srli(value, position, 5)
      p.brisc.addi(value, value, 1)
      p.brisc.write(runtime_l1 + 16, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 16, value)
      p.brisc.andi(value, position, 31)
      p.brisc.addi(value, value, 1)
      p.brisc.write(runtime_l1 + 20, value)
      p.brisc.write(TensixL1.RUNTIME_PARAM_BASE + 20, value)
      for rect in rectangles(logits.cores):
        start, end = mcast_coords(rect)
        p.brisc.noc.multicast_write(
          runtime_l1, TensixL1.RUNTIME_PARAM_BASE, start, end, 24,
        )
    p.brisc.label(reducer_done)
  return p


def _decode_projection_residual_program(
  cores, compact, residual, output, *, head,
):
  """Gather one compact 64-value slice, add residual, and scatter it dense."""
  p = Program(cores, compact, residual, output)
  projection_cb = p.cb(DType.BF16, depth=1)
  residual_cb = p.cb(DType.BF16, depth=1)
  result = p.cb(DType.BF16, depth=1)
  feature_locations = tuple(
    _compact_projection_location(head * HEAD_DIM + index, query=True)
    for index in range(HEAD_DIM)
  )
  source_tiles = tuple(dict.fromkeys(tile for tile, _ in feature_locations))
  source_tile_indices = {
    tile: index for index, tile in enumerate(source_tiles)
  }
  compact_l1 = p.l1(len(source_tiles) * compact.tile_size, alignment=16)
  residual_l1 = p.l1(residual.tile_size, alignment=16)

  CB.reserve_back(p.brisc, projection_cb)
  CB.reserve_back(p.brisc, residual_cb)
  with p.brisc.noc.transaction() as transaction:
    for index, tile in enumerate(source_tiles):
      with p.brisc.scope():
        source_address, source_coordinate = p.brisc.noc._dram_tile(
          compact, tile,
        )
        transaction.read(
          source_address, source_coordinate,
          compact_l1 + index * compact.tile_size, compact.tile_size,
        )
    with p.brisc.scope():
      source_address, source_coordinate = p.brisc.noc._dram_tile(
        residual, head // 16,
      )
      transaction.read(
        source_address, source_coordinate, residual_l1, residual.tile_size,
      )

  # Operand 0 is the projection head reconstructed from compact scalar slots.
  for index, (tile, slot) in enumerate(feature_locations):
    with p.brisc.scope():
      value = p.brisc.reg()
      source = (
        compact_l1 + source_tile_indices[tile] * compact.tile_size +
        _compact_slot_byte_offset(slot)
      )
      p.brisc.read(value, source, bytes=2)
      p.brisc.write(
        projection_cb.addr + _bf16_tile_byte_offset(index), value, bytes=2,
      )

  # Operand 1 contains the matching two rows of the dense residual tile.
  first_residual_row = 2 * (head % 16)
  for feature_half in range(2):
    source_row = first_residual_row + feature_half
    target_row = feature_half
    for face in range(2):
      _copy_l1_words(
        p.brisc,
        residual_l1 + _bf16_tile_byte_offset(source_row * 32 + face * 16),
        residual_cb.addr +
        _bf16_tile_byte_offset(target_row * 32 + face * 16),
        8,
      )
  CB.push_back(p.brisc, projection_cb)
  CB.push_back(p.brisc, residual_cb)

  p.unpack.move_pair(projection_cb, residual_cb)
  p.fpu.binary("add", dst_tile=0).publish()
  p.pack.move(result, tile=0)

  # Scatter the two 32-feature result rows into the dense [1, 2048] output.
  CB.wait_front(p.ncrisc, result)
  with p.ncrisc.scope():
    source = p.ncrisc.reg()
    CB.get_read_ptr(p.ncrisc, result, source)
    target_address, target_coordinate = p.ncrisc.noc._dram_tile(
      output, head // 16,
    )
    with p.ncrisc.noc.transaction() as transaction:
      for feature_half in range(2):
        target_row = 2 * (head % 16) + feature_half
        for face in range(2):
          with p.ncrisc.scope():
            source_segment, target_segment = p.ncrisc.reg(
              2, exclude=(source, target_address),
            )
            p.ncrisc.mv(source_segment, source)
            source_offset = _bf16_tile_byte_offset(
              feature_half * 32 + face * 16,
            )
            if source_offset:
              p.ncrisc.addi(source_segment, source_segment, source_offset)
            p.ncrisc.mv(target_segment, target_address)
            target_offset = _bf16_tile_byte_offset(
              target_row * 32 + face * 16,
            )
            if target_offset:
              p.ncrisc.addi(target_segment, target_segment, target_offset)
            transaction.write(
              source_segment, target_segment, target_coordinate, 32,
              posted=False,
            )
  CB.pop_front(p.ncrisc, result)
  return p


def decode_projection_residual(
  compact: Buffer, residual: Buffer, output: Buffer,
) -> Program:
  """Reassemble a 2048-row decode projection and fuse its residual add."""
  if (
    compact.dtype is not DType.BF16 or
    compact.shape != (LLAMA_CORES, 18) or compact.axis != 0 or
    compact.item_counts != (1,) * LLAMA_CORES or
    len(compact.cores) != LLAMA_CORES
  ):
    raise ValueError(
      f"projection residual input must be compact BF16[{LLAMA_CORES}, 18]",
    )
  for buffer, name in ((residual, "residual"), (output, "output")):
    if (
      buffer.dtype is not DType.BF16 or buffer.shape != (1, EMBED_DIM) or
      buffer.axis != 0 or not buffer.global_address or
      buffer.tiles_per_item != EMBEDDING_TILES
    ):
      raise ValueError(
        f"projection residual {name} must be global BF16[1, {EMBED_DIM}]",
      )

  cores = compact.cores[:Q_HEADS]
  compact_tiles = _global_tile_view(
    compact, "projection_residual_compact_tiles",
  )
  variants = tuple(
    _decode_projection_residual_program(
      cores, compact_tiles, residual, output, head=head,
    )
    for head in range(Q_HEADS)
  )
  lowered = tuple(program.lower() for program in variants)
  combined = variants[0]
  combined._kernels = {
    core: dict(images[core])
    for core, images in zip(cores, lowered)
  }
  return combined


def decode_swiglu(gate: Buffer, up: Buffer, hidden: Buffer) -> Program:
  """Compute compact BF16 ``silu(gate) * up`` on all projection cores."""
  expected_shape = (LLAMA_CORES, (MLP_DIM + LLAMA_CORES - 1) // LLAMA_CORES)
  for buffer, name in ((gate, "gate"), (up, "up"), (hidden, "hidden")):
    if (
      buffer.dtype is not DType.BF16 or buffer.shape != expected_shape or
      buffer.axis != 0 or len(buffer.cores) != LLAMA_CORES or
      buffer.item_counts != (1,) * LLAMA_CORES or buffer.tiles_per_item != 1
    ):
      raise ValueError(
        f"decode SwiGLU {name} must be compact BF16{expected_shape}",
      )
  if gate.cores != up.cores or gate.cores != hidden.cores:
    raise ValueError("decode SwiGLU buffers must use identical cores")

  p = Program(gate.cores, gate, up, hidden, fp32_dst=True)
  gate_cb = p.cb(DType.BF16, depth=1)
  up_cb = p.cb(DType.BF16, depth=1)
  output_cb = p.cb(DType.BF16, depth=1)
  p.brisc.noc.read_into_cb(gate, 0, gate_cb)
  p.brisc.noc.read_into_cb(up, 0, up_cb)
  p.unpack.move(gate_cb, UnpackTarget.SRCA)
  p.unpack.move(up_cb, UnpackTarget.SRCA)
  p.fpu.copy_a_tiles(dst_tiles=(0, 1))

  exponent = p.sfpu.program()
  value = exponent.load(format=SfpuFormat.FP32, offset=0)
  exponent.store(value, format=SfpuFormat.FP32, offset=128)
  exponent.neg(value, into=value)
  exponent.exp(value, into=value)
  exponent.store(value, format=SfpuFormat.FP32, offset=0)
  p.sfpu.map(exponent.finish(), tile=0)

  combine = p.sfpu.program()
  denominator = combine.load(format=SfpuFormat.FP32, offset=0)
  combine.add_scalar(denominator, 1.0, into=denominator)
  combine.reciprocal(denominator, into=denominator)
  original = combine.load(format=SfpuFormat.FP32, offset=128)
  up_value = combine.load(format=SfpuFormat.FP32, offset=64)
  combine.mul(original, denominator, into=original)
  combine.mul(original, up_value, into=original)
  combine.store(original, format=SfpuFormat.FP32, offset=0)
  p.sfpu.map(combine.finish(), tile=0).publish()

  p.pack.move(output_cb, tile=0)
  p.ncrisc.noc.write_from_cb(output_cb, hidden, 0)
  return p


def _compact_feature_location(feature, total_features):
  counts = _token_counts(total_features, LLAMA_CORES)
  cursor = 0
  for core, count in enumerate(counts):
    if feature < cursor + count: return core, feature - cursor
    cursor += count
  raise ValueError("compact feature index is out of range")


def _decode_compact_to_dense_program(
  cores, compact, output, *, blocks,
):
  p = Program(cores, compact, output)
  for block in blocks:
    locations = tuple(
      _compact_feature_location(block * HEAD_DIM + index, MLP_DIM)
      for index in range(HEAD_DIM)
    )
    source_tiles = tuple(dict.fromkeys(tile for tile, _ in locations))
    source_indices = {tile: index for index, tile in enumerate(source_tiles)}
    sources_l1 = p.l1(len(source_tiles) * compact.tile_size, alignment=16)
    result_l1 = p.l1(compact.tile_size, alignment=16)
    p.brisc.zero_words(result_l1, compact.tile_size // 4)
    with p.brisc.noc.transaction() as transaction:
      for index, tile in enumerate(source_tiles):
        with p.brisc.scope():
          source_address, source_coordinate = p.brisc.noc._dram_tile(
            compact, tile,
          )
          transaction.read(
            source_address, source_coordinate,
            sources_l1 + index * compact.tile_size, compact.tile_size,
          )
    for index, (tile, slot) in enumerate(locations):
      with p.brisc.scope():
        value = p.brisc.reg()
        p.brisc.read(
          value,
          sources_l1 + source_indices[tile] * compact.tile_size +
          _bf16_tile_byte_offset(slot),
          bytes=2,
        )
        p.brisc.write(
          result_l1 + _bf16_tile_byte_offset(index), value, bytes=2,
        )

    target_tile = block // 16
    target_first_row = 2 * (block % 16)
    with p.brisc.scope():
      target_address, target_coordinate = p.brisc.noc._dram_tile(
        output, target_tile,
      )
      with p.brisc.noc.transaction() as transaction:
        for feature_half in range(2):
          for face in range(2):
            source_offset = _bf16_tile_byte_offset(
              feature_half * 32 + face * 16,
            )
            target_offset = _bf16_tile_byte_offset(
              (target_first_row + feature_half) * 32 + face * 16,
            )
            with p.brisc.scope():
              target_segment = p.brisc.reg(exclude=target_address)
              p.brisc.mv(target_segment, target_address)
              if target_offset:
                p.brisc.addi(target_segment, target_segment, target_offset)
              transaction.write(
                result_l1 + source_offset, target_segment,
                target_coordinate, 32, posted=False,
              )
  return p


def decode_compact_to_dense(compact: Buffer, output: Buffer) -> Program:
  """Reassemble compact 118-core MLP state into global BF16[1,8192]."""
  expected_shape = (LLAMA_CORES, (MLP_DIM + LLAMA_CORES - 1) // LLAMA_CORES)
  if (
    compact.dtype is not DType.BF16 or compact.shape != expected_shape or
    compact.axis != 0 or len(compact.cores) != LLAMA_CORES or
    compact.item_counts != (1,) * LLAMA_CORES or compact.tiles_per_item != 1
  ):
    raise ValueError(
      f"compact MLP input must be BF16{expected_shape} over {LLAMA_CORES} cores",
    )
  if (
    output.dtype is not DType.BF16 or output.shape != (1, MLP_DIM) or
    output.axis != 0 or not output.global_address or
    output.tiles_per_item != MLP_DIM // 1024
  ):
    raise ValueError(f"dense MLP output must be global BF16[1, {MLP_DIM}]")

  block_count = MLP_DIM // HEAD_DIM
  cores = P100_WORKER_CORES[:min(block_count, len(P100_WORKER_CORES))]
  compact_tiles = _global_tile_view(compact, "mlp_compact_tiles")
  counts = _token_counts(block_count, len(cores))
  starts, start = [], 0
  for count in counts:
    starts.append(start)
    start += count
  variants = tuple(
    _decode_compact_to_dense_program(
      cores, compact_tiles, output,
      blocks=tuple(range(start, start + count)),
    )
    for start, count in zip(starts, counts)
  )
  lowered = tuple(program.lower() for program in variants)
  combined = variants[0]
  combined._kernels = {
    core: dict(images[core])
    for core, images in zip(cores, lowered)
  }
  return combined


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


def _gqa_exp_program(*, value_offset):
  builder = SfpuProgramBuilder()
  value = builder.load(format=SfpuFormat.FP32, offset=value_offset)
  builder.exp(value, into=value)
  builder.store(value, format=SfpuFormat.FP32, offset=value_offset)
  return builder.finish()


def _gqa_normalize_program(*, output_offset, sum_offset):
  builder = SfpuProgramBuilder()
  output = builder.load(format=SfpuFormat.FP32, offset=output_offset)
  denominator = builder.load(format=SfpuFormat.FP32, offset=sum_offset)
  builder.reciprocal(denominator, into=denominator)
  builder.mul(output, denominator, into=output)
  builder.store(output, format=SfpuFormat.FP32, offset=output_offset)
  return builder.finish()


def _gqa_issue_program(sfpu, program):
  """Run one explicitly addressed 4x8 SFPU footprint."""
  _rms_select_tile(sfpu, 0)
  for word in (*program.setup_words, *program.words): sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _gqa_online_update(sfpu):
  """Update m/l/P/O for rows 0..3 after one score matmul."""
  score, output0, output1, maximum, total, alpha = range(0, 6 * 64, 64)
  words = []
  words.extend(_sfpu_float_words(LReg.L4, HEAD_DIM ** -0.5))
  for register, chunk in zip(
    (LReg.L0, LReg.L1, LReg.L2, LReg.L3), GQA_ROW_CHUNKS,
  ):
    words.append(TT.TTSFPLOAD(register, SfpuFormat.FP32, 7, score + chunk))
    _sfpu_mul(words, register, LReg.L4, register)
    words.append(TT.TTSFPSTORE(register, SfpuFormat.FP32, 7, score + chunk))

  # L0 becomes a broadcast maximum for each of the four live rows.
  for left, right in ((LReg.L0, LReg.L2), (LReg.L1, LReg.L3),
                      (LReg.L0, LReg.L1)):
    words.extend((TT.TTSFPSWAP(0, left, right, 1), TT.TTSFPNOP()))
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
      ))
    words.extend((TT.TTSFPSWAP(0, LReg.L0, LReg.L1, 1), TT.TTSFPNOP()))

  words.append(TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, maximum))
  words.append(TT.TTSFPMOV(0, LReg.L2, LReg.L3, 0))
  # SFPSWAP leaves max(VC, VD) in VC, hence the new maximum remains in L0.
  words.extend((TT.TTSFPSWAP(0, LReg.L0, LReg.L2, 1), TT.TTSFPNOP()))
  for chunk in GQA_ROW_CHUNKS:
    words.append(TT.TTSFPSTORE(
      LReg.L0, SfpuFormat.FP32, 7, maximum + chunk,
    ))
  words.extend((
    TT.TTSFPMAD(LReg.L0, LReg.NEG_ONE, LReg.L3, LReg.L5, 0),
    TT.TTSFPNOP(),
  ))
  for chunk in GQA_ROW_CHUNKS:
    words.append(TT.TTSFPSTORE(
      LReg.L5, SfpuFormat.FP32, 7, alpha + chunk,
    ))
  for word in words: sfpu._issue(word)

  # Shift scores separately so the exp program can reuse its LRegs without a
  # load/subtract lifetime crossing the programmable-constant setup.
  words = []
  for chunk in GQA_ROW_CHUNKS:
    words.extend((
      TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, score + chunk),
      TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, maximum + chunk),
      TT.TTSFPMAD(LReg.L1, LReg.NEG_ONE, LReg.L0, LReg.L0, 0),
      TT.TTSFPNOP(),
      TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, score + chunk),
    ))
  for word in words: sfpu._issue(word)

  # alpha = exp(m_old - m_new), and P = exp(score - m_new).
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)
  for chunk in GQA_ROW_CHUNKS:
    _gqa_issue_program(sfpu, _gqa_exp_program(value_offset=alpha + chunk))
  for chunk in GQA_ROW_CHUNKS:
    _gqa_issue_program(sfpu, _gqa_exp_program(value_offset=score + chunk))

  # l_new = l_old * alpha + sum(P).  Horizontal reduction is independent in
  # each eight-lane subgroup, one subgroup per live query row.
  words = [
    TT.TTSFPLOAD(register, SfpuFormat.FP32, 7, score + chunk)
    for register, chunk in zip(
      (LReg.L0, LReg.L1, LReg.L2, LReg.L3), GQA_ROW_CHUNKS,
    )
  ]
  _sfpu_add(words, LReg.L0, LReg.L2, LReg.L0)
  _sfpu_add(words, LReg.L1, LReg.L3, LReg.L1)
  _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
      ))
    _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  words.extend((
    TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, total),
    TT.TTSFPLOAD(LReg.L3, SfpuFormat.FP32, 7, alpha),
    TT.TTSFPMAD(LReg.L2, LReg.L3, LReg.L0, LReg.L0, 0),
    TT.TTSFPNOP(),
  ))
  for chunk in GQA_ROW_CHUNKS:
    words.append(TT.TTSFPSTORE(
      LReg.L0, SfpuFormat.FP32, 7, total + chunk,
    ))

  # Rescale the persistent FP32 context before accumulating this block's PV.
  for output in (output0, output1):
    for chunk in GQA_ROW_CHUNKS:
      words.extend((
        TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, output + chunk),
        TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, alpha + chunk),
      ))
      _sfpu_mul(words, LReg.L0, LReg.L1, LReg.L0)
      words.append(TT.TTSFPSTORE(
        LReg.L0, SfpuFormat.FP32, 7, output + chunk,
      ))
  for word in words: sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def gqa_attention_fused(
  q: Buffer, key_cache: Buffer, value_cache: Buffer, context: Buffer,
) -> Program:
  """Fused streaming decode GQA: scaled QK, online softmax, and PV."""
  if (
    q.dtype is not DType.BF16 or q.shape != (Q_HEADS, HEAD_DIM) or
    q.axis != 0 or not q.global_address or q.tiles_per_item != 1
  ):
    raise ValueError(
      f"GQA q must be global BF16[{Q_HEADS}, {HEAD_DIM}] with axis=0",
    )
  for cache, name in ((key_cache, "key_cache"),
                      (value_cache, "value_cache")):
    if (
      cache.dtype is not DType.BF16 or
      cache.shape != KV_CACHE_STORAGE_SHAPE or cache.axis != 0 or
      not cache.global_address or
      cache.tiles_per_item != KV_CACHE_TILES_PER_HEAD
    ):
      raise ValueError(
        f"GQA {name} must be global BF16{KV_CACHE_STORAGE_SHAPE} "
        "with axis=0",
      )
  if (
    context.dtype is not DType.BF16 or context.shape != GQA_CONTEXT_SHAPE or
    context.axis != 0 or not context.global_address or
    context.tiles_per_item != EMBEDDING_TILES
  ):
    raise ValueError(
      f"GQA context must be global BF16{GQA_CONTEXT_SHAPE} with axis=0",
    )

  kv_blocks = Const("kv_blocks", 1)
  valid_columns = Const("valid_columns", 1)
  kv_head = Const("kv_head", tuple(range(KV_HEADS)))
  p = Program(
    P100_WORKER_CORES[:KV_HEADS], q, key_cache, value_cache, context,
    kv_blocks, valid_columns, kv_head, fp32_dst=True,
  )
  query_cb = p.cb(DType.BF16, depth=4)
  key_cb = p.cb(DType.BF16, depth=4)
  value_cb = p.cb(DType.BF16, depth=4)
  probability_cb = p.cb(DType.BF16, depth=2)
  mask_cb = p.cb(DType.F32, depth=1)
  zero_cb = p.cb(DType.F32, depth=1)
  context_cb = p.cb(DType.BF16, depth=2)
  query_heads_l1 = p.l1(GQA_GROUP_SIZE * q.tile_size, alignment=16)
  query_low_l1 = p.l1(q.tile_size, alignment=16)
  query_high_l1 = p.l1(q.tile_size, alignment=16)

  # BRISC creates one reusable 0/-inf tail tile, gathers Q once, then streams
  # each matching K/V pair.  Two Q copies and two packed-P copies are needed
  # because the two feature halves are separate matrix multiplies.
  p.brisc.zero_words(query_low_l1, q.tile_size // 4)
  p.brisc.zero_words(query_high_l1, q.tile_size // 4)
  with p.brisc.scope():
    head, block_count, tail = p.brisc.reg(3)
    p.brisc.read(head, p.param_addr(kv_head))
    p.brisc.read(block_count, p.param_addr(kv_blocks))
    p.brisc.read(tail, p.param_addr(valid_columns))

    CB.reserve_back(p.brisc, zero_cb)
    with p.brisc.scope():
      target = p.brisc.reg()
      CB.get_write_ptr(p.brisc, zero_cb, target)
      with p.brisc.scope():
        pointer, remaining = p.brisc.reg(2, exclude=target)
        p.brisc.mv(pointer, target)
        p.brisc.li(remaining, zero_cb.tile_size // 4)
        clear = p.brisc._new_label("gqa_clear_zero")
        cleared = p.brisc._new_label("gqa_zero_cleared")
        p.brisc.label(clear)
        p.brisc.beq(remaining, R.ZERO, cleared)
        p.brisc.sw(R.ZERO, pointer)
        p.brisc.addi(pointer, pointer, 4)
        p.brisc.addi(remaining, remaining, -1)
        p.brisc.j(clear)
        p.brisc.label(cleared)
    CB.push_back(p.brisc, zero_cb)

    CB.reserve_back(p.brisc, mask_cb)
    with p.brisc.scope():
      target = p.brisc.reg()
      CB.get_write_ptr(p.brisc, mask_cb, target)
      with p.brisc.scope():
        pointer, remaining = p.brisc.reg(2, exclude=target)
        p.brisc.mv(pointer, target)
        p.brisc.li(remaining, mask_cb.tile_size // 4)
        clear = p.brisc._new_label("gqa_clear_mask")
        cleared = p.brisc._new_label("gqa_mask_cleared")
        p.brisc.label(clear)
        p.brisc.beq(remaining, R.ZERO, cleared)
        p.brisc.sw(R.ZERO, pointer)
        p.brisc.addi(pointer, pointer, 4)
        p.brisc.addi(remaining, remaining, -1)
        p.brisc.j(clear)
        p.brisc.label(cleared)
      with p.brisc.scope():
        column, limit, negative_infinity = p.brisc.reg(3)
        p.brisc.mv(column, tail)
        p.brisc.li(limit, KV_CACHE_TOKEN_BLOCK)
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
    CB.push_back(p.brisc, mask_cb)

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
        low, high, tile_bytes = p.brisc.reg(3)
        CB.get_write_ptr(p.brisc, query_cb, low)
        p.brisc.li(tile_bytes, query_cb.tile_size)
        p.brisc.add(high, low, tile_bytes)
        _copy_l1_words(p.brisc, query_low_l1, low, q.tile_size // 4)
        _copy_l1_words(p.brisc, query_high_l1, high, q.tile_size // 4)
      CB.push_back(p.brisc, query_cb, 2)
      with p.brisc.scope():
        first, second, block_offset = p.brisc.reg(3, exclude=(head, block))
        p.brisc.slli(first, head, 9)
        p.brisc.slli(block_offset, block, 1)
        p.brisc.add(first, first, block_offset)
        p.brisc.addi(second, first, 1)
        p.brisc.noc.read_tiles_into_cb(key_cache, (first, second), key_cb)
        p.brisc.noc.read_tiles_into_cb(
          value_cache, (first, second), value_cb,
        )

  with p.trisc0.scope():
    block_count, last_block = p.trisc0.reg(2)
    p.trisc0.read(block_count, p.param_addr(kv_blocks))
    p.trisc0.addi(last_block, block_count, -1)
    for block in p.trisc0.range(block_count):
      p.unpack.move_matmul(query_cb, key_cb, right_transpose=True)
      p.unpack.move_matmul(query_cb, key_cb, right_transpose=True)
      no_mask = p.trisc0._new_label("gqa_unpack_no_mask")
      p.trisc0.bne(block, last_block, no_mask)
      p.unpack.move_pair(zero_cb, mask_cb)
      p.trisc0.label(no_mask)
      p.unpack.move_matmul(probability_cb, value_cb)
      p.unpack.move_matmul(probability_cb, value_cb)

  zero = p.sfpu.program()
  value = zero.load_float(0.0)
  zero.store(value, format=SfpuFormat.FP32)
  zero = zero.finish()
  one = p.sfpu.program()
  value = one.load_float(1.0)
  one.store(value, format=SfpuFormat.FP32)
  one = one.finish()
  with p.trisc1.scope():
    block_count, last_block = p.trisc1.reg(2)
    p.trisc1.read(block_count, p.param_addr(kv_blocks))
    p.trisc1.addi(last_block, block_count, -1)
    # Dst1/2 are persistent O, Dst3 is m, Dst4 is l, and Dst5 is alpha.
    for tile in (1, 2, 3, 5): p.sfpu.map(zero, tile=tile)
    # Keep inactive rows finite when the row mapper traverses the top half.
    # Only the four live rows are overwritten with the online initial state.
    p.sfpu.map(one, tile=4)
    _rms_select_tile(p.sfpu, 0)
    for word in _sfpu_float_words(LReg.L0, float("-inf")):
      p.sfpu._issue(word)
    for chunk in GQA_ROW_CHUNKS:
      p.sfpu._issue(TT.TTSFPSTORE(
        LReg.L0, SfpuFormat.FP32, 7, 3 * 64 + chunk,
      ))
    for word in _sfpu_float_words(LReg.L0, 0.0): p.sfpu._issue(word)
    for chunk in GQA_ROW_CHUNKS:
      p.sfpu._issue(TT.TTSFPSTORE(
        LReg.L0, SfpuFormat.FP32, 7, 4 * 64 + chunk,
      ))
    stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)

    for block in p.trisc1.range(block_count):
      p.fpu.matmul(dst_tile=0, right_transpose=True)
      p.fpu.matmul(dst_tile=0, accumulate=True, right_transpose=True)
      unmasked = p.trisc1._new_label("gqa_score_unmasked")
      p.trisc1.bne(block, last_block, unmasked)
      p.fpu.binary("add", dst_tile=0, accumulate=True)
      p.trisc1.label(unmasked)
      _rms_select_tile(p.sfpu, 0)
      _gqa_online_update(p.sfpu)
      p.sfpu.publish()
      p.fpu.matmul(dst_tile=1, accumulate=True)
      p.fpu.matmul(dst_tile=2, accumulate=True)

    _rms_select_tile(p.sfpu, 0)
    for output in (64, 128):
      for chunk in GQA_ROW_CHUNKS:
        _gqa_issue_program(p.sfpu, _gqa_normalize_program(
          output_offset=output + chunk, sum_offset=4 * 64 + chunk,
        ))
    p.sfpu.publish()

  # Pack P twice while retaining Dst1..5.  The final context handoff uses the
  # ordinary full-Dst release after both output tiles have been packed.
  with p.trisc2.scope():
    block_count = p.trisc2.reg()
    p.trisc2.read(block_count, p.param_addr(kv_blocks))
    for _ in p.trisc2.range(block_count):
      sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
      p.pack._move_acquired(probability_cb, 0, False)
      p.pack._move_acquired(probability_cb, 0, False)
      sem_get(p.trisc2, Sem.MATH_PACK)
    p.pack.move_tiles(context_cb, tiles=(1, 2))

  # Each worker owns four adjacent heads.  Scatter its [4,64] packed rows into
  # the two dense context tiles consumed directly by the output projection.
  with p.ncrisc.scope():
    head = p.ncrisc.reg()
    p.ncrisc.read(head, p.param_addr(kv_head))
    CB.wait_front(p.ncrisc, context_cb, 2)
    with p.ncrisc.scope():
      source0, source1, tile_bytes, target_tile = p.ncrisc.reg(4, exclude=head)
      CB.get_read_ptr(p.ncrisc, context_cb, source0)
      p.ncrisc.li(tile_bytes, context_cb.tile_size)
      p.ncrisc.add(source1, source0, tile_bytes)
      p.ncrisc.srli(target_tile, head, 2)
      target_address, target_coordinate = p.ncrisc.noc._dram_tile(
        context, target_tile,
      )
      with p.ncrisc.noc.transaction() as transaction:
        for group_row in range(GQA_GROUP_SIZE):
          for feature_half, source_base in enumerate((source0, source1)):
            logical_row = group_row * 2 + feature_half
            for face_delta in (0, 512):
              with p.ncrisc.scope():
                source_address, target_offset, target = p.ncrisc.reg(
                  3, exclude=(head, source_base, target_address),
                )
                p.ncrisc.mv(source_address, source_base)
                p.ncrisc.addi(
                  source_address, source_address,
                  group_row * 32 + face_delta,
                )
                p.ncrisc.andi(target_offset, head, 3)
                p.ncrisc.slli(target_offset, target_offset, 3)
                if logical_row:
                  p.ncrisc.addi(target_offset, target_offset, logical_row)
                with p.ncrisc.scope():
                  bottom, within = p.ncrisc.reg(
                    2, exclude=target_offset,
                  )
                  p.ncrisc.srli(bottom, target_offset, 4)
                  p.ncrisc.slli(bottom, bottom, 10)
                  p.ncrisc.andi(within, target_offset, 15)
                  p.ncrisc.slli(within, within, 5)
                  p.ncrisc.add(target_offset, bottom, within)
                if face_delta:
                  p.ncrisc.addi(target_offset, target_offset, 512)
                p.ncrisc.add(target, target_address, target_offset)
                transaction.write(
                  source_address, target, target_coordinate, 32,
                  posted=False,
                )
    CB.pop_front(p.ncrisc, context_cb, 2)
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


def decode_embedding(
  token_id: Buffer, embedding_weight: Buffer, output: Buffer,
) -> Program:
  """Gather one embedding row directly into global BF16[1, 2048]."""
  if (
    token_id.dtype is not DType.U32 or
    token_id.shape not in ((1,), (ROPE_CACHE_TOKENS,)) or
    not token_id.global_address
  ):
    raise ValueError(
      f"decode token IDs must be global U32[1] or U32[{ROPE_CACHE_TOKENS}]",
    )
  if (
    embedding_weight.dtype is not DType.BF16 or
    embedding_weight.shape != (VOCAB_SIZE, EMBED_DIM) or
    embedding_weight.axis != 0 or
    embedding_weight.tiles_per_item != EMBEDDING_TILES or
    not embedding_weight.global_address
  ):
    raise ValueError(
      f"decode embedding weight must be global "
      f"BF16[{VOCAB_SIZE}, {EMBED_DIM}]",
    )
  if (
    output.dtype is not DType.BF16 or output.shape != (1, EMBED_DIM) or
    output.axis != 0 or output.tiles_per_item != EMBEDDING_TILES or
    not output.global_address
  ):
    raise ValueError(
      f"decode embedding output must be global BF16[1, {EMBED_DIM}]",
    )

  token_pos = Const("token_pos", 0)
  p = Program(
    output.cores, token_id, embedding_weight, output, token_pos,
  )
  ids_l1 = p.l1(token_id.tile_size, alignment=16)
  embedding_cb = p.cb(DType.BF16, depth=EMBEDDING_TILES)
  with p.brisc.scope():
    position, tile, within, token = p.brisc.reg(4)
    p.brisc.read(position, p.param_addr(token_pos))
    p.brisc.srli(tile, position, 10)
    p.brisc.andi(within, position, 1023)
    p.brisc.noc.read_tile(token_id, tile, ids_l1)
    _load_tiled_u32(p.brisc, ids_l1, within, token)
    for row_tile in range(EMBEDDING_TILES):
      with p.brisc.scope():
        source_tile = p.brisc.reg(exclude=token)
        p.brisc.slli(source_tile, token, 1)
        if row_tile: p.brisc.addi(source_tile, source_tile, row_tile)
        p.brisc.noc.read_into_cb(
          embedding_weight, source_tile, embedding_cb,
        )
  p.ncrisc.noc.write_tiles_from_cb(
    embedding_cb, output, tuple(range(EMBEDDING_TILES)),
  )
  return p


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


class Llama3Decode:
  """Resident-weight, batch-1 Llama 3.2 1B decode runtime."""

  def __init__(self, safetensor_path="weights/model.safetensors"):
    self.safetensor_path = str(safetensor_path)
    self.host_result_read_us = 0.0
    self.host_result_reads = 0
    self.device = Device()
    self.device.init_device()
    try:
      self._allocate()
      self._upload_weights()
      self._build_programs()
    except Exception:
      self.close()
      raise

  def _allocate(self):
    device = self.device
    cores = device.dram.cores[:LLAMA_CORES]
    global_buffer = lambda name, dtype, shape, axis=0: device.dram.buffer(
      name, dtype, shape, axis=axis, global_address=True,
    )

    self.token_history = global_buffer(
      "e2e_token_history", DType.U32, (ROPE_CACHE_TOKENS,), None,
    )
    self.next_token = global_buffer(
      "e2e_next_token", DType.U32, (1,), None,
    )
    self.embedding_weight = global_buffer(
      "e2e_embedding_weight", DType.BF16, (VOCAB_SIZE, EMBED_DIM),
    )
    self.lm_weight = device.dram.buffer(
      "e2e_lm_weight", DType.BF16, (VOCAB_SIZE, EMBED_DIM),
      axis=0, cores=cores,
    )
    self.cos = global_buffer(
      "e2e_rope_cos", DType.BF16, (ROPE_CACHE_TOKENS, HEAD_DIM), None,
    )
    self.sin = global_buffer(
      "e2e_rope_sin", DType.BF16, (ROPE_CACHE_TOKENS, HEAD_DIM), None,
    )

    self.x_a = global_buffer(
      "e2e_x_a", DType.BF16, (1, EMBED_DIM),
    )
    self.x_b = global_buffer(
      "e2e_x_b", DType.BF16, (1, EMBED_DIM),
    )
    self.normalized = global_buffer(
      "e2e_normalized", DType.BF16, (1, EMBED_DIM),
    )
    self.q_compact = device.dram.buffer(
      "e2e_q_compact", DType.BF16, (LLAMA_CORES, 18),
      axis=0, cores=cores,
    )
    self.k_compact = device.dram.buffer(
      "e2e_k_compact", DType.BF16, (LLAMA_CORES, 5),
      axis=0, cores=cores,
    )
    self.v_compact = device.dram.buffer(
      "e2e_v_compact", DType.BF16, (LLAMA_CORES, 5),
      axis=0, cores=cores,
    )
    self.q_heads = global_buffer(
      "e2e_q_heads", DType.BF16, (Q_HEADS, HEAD_DIM),
    )
    self.k_heads = global_buffer(
      "e2e_k_heads", DType.BF16, (KV_HEADS, HEAD_DIM),
    )
    self.v_heads = global_buffer(
      "e2e_v_heads", DType.BF16, (KV_HEADS, HEAD_DIM),
    )
    self.context = global_buffer(
      "e2e_context", DType.BF16, GQA_CONTEXT_SHAPE,
    )
    mlp_compact_shape = (
      LLAMA_CORES, (MLP_DIM + LLAMA_CORES - 1) // LLAMA_CORES,
    )
    self.gate = device.dram.buffer(
      "e2e_gate", DType.BF16, mlp_compact_shape, axis=0, cores=cores,
    )
    self.up = device.dram.buffer(
      "e2e_up", DType.BF16, mlp_compact_shape, axis=0, cores=cores,
    )
    self.hidden = device.dram.buffer(
      "e2e_hidden", DType.BF16, mlp_compact_shape, axis=0, cores=cores,
    )
    self.hidden_dense = global_buffer(
      "e2e_hidden_dense", DType.BF16, (1, MLP_DIM),
    )
    self.logits = device.dram.buffer(
      "e2e_logits", DType.BF16,
      (LLAMA_CORES, self.lm_weight.items_per_core),
      axis=0, cores=cores,
    )

    self.layers = []
    for layer in range(LLAMA_LAYERS):
      prefix = f"e2e_l{layer}"
      weights = {
        "input_norm": global_buffer(
          f"{prefix}_input_norm", DType.BF16, (EMBED_DIM,), None,
        ),
        "post_norm": global_buffer(
          f"{prefix}_post_norm", DType.BF16, (EMBED_DIM,), None,
        ),
        "q": device.dram.buffer(
          f"{prefix}_q", DType.BF16, (Q_PROJ_DIM, EMBED_DIM),
          axis=0, cores=cores,
        ),
        "k": device.dram.buffer(
          f"{prefix}_k", DType.BF16, (KV_PROJ_DIM, EMBED_DIM),
          axis=0, cores=cores,
        ),
        "v": device.dram.buffer(
          f"{prefix}_v", DType.BF16, (KV_PROJ_DIM, EMBED_DIM),
          axis=0, cores=cores,
        ),
        "o": device.dram.buffer(
          f"{prefix}_o", DType.BF16, (EMBED_DIM, EMBED_DIM),
          axis=0, cores=cores,
        ),
        "gate": device.dram.buffer(
          f"{prefix}_gate", DType.BF16, (MLP_DIM, EMBED_DIM),
          axis=0, cores=cores,
        ),
        "up": device.dram.buffer(
          f"{prefix}_up", DType.BF16, (MLP_DIM, EMBED_DIM),
          axis=0, cores=cores,
        ),
        "down": device.dram.buffer(
          f"{prefix}_down", DType.BF16, (EMBED_DIM, MLP_DIM),
          axis=0, cores=cores,
        ),
      }
      key_cache = global_buffer(
        f"{prefix}_key_cache", DType.BF16, KV_CACHE_STORAGE_SHAPE,
      )
      value_cache = global_buffer(
        f"{prefix}_value_cache", DType.BF16, KV_CACHE_STORAGE_SHAPE,
      )
      self.layers.append({
        "weights": weights,
        "key_cache": key_cache,
        "value_cache": value_cache,
      })
    self.final_norm = global_buffer(
      "e2e_final_norm", DType.BF16, (EMBED_DIM,), None,
    )

  def _upload(self, buffer, tensor):
    data = buffer.from_safetensor(tensor, self.safetensor_path)
    self.device.write(buffer, data)

  def _upload_weights(self):
    embedding_data = self.embedding_weight.from_safetensor(
      "model.embed_tokens.weight", self.safetensor_path,
    )
    self.device.write(self.embedding_weight, embedding_data)
    self.device.run(timeout=60.0)
    self.device.write(self.lm_weight, embedding_data)
    self.device.run(timeout=60.0)
    del embedding_data

    cos_values, sin_values = rope_table()
    self.device.write(self.cos, _bf16_rne_bytes(cos_values))
    self.device.write(self.sin, _bf16_rne_bytes(sin_values))
    self.device.run(timeout=30.0)
    del cos_values, sin_values

    for index, layer in enumerate(self.layers):
      weights = layer["weights"]
      prefix = f"model.layers.{index}"
      tensors = {
        "input_norm": f"{prefix}.input_layernorm.weight",
        "post_norm": f"{prefix}.post_attention_layernorm.weight",
        "q": f"{prefix}.self_attn.q_proj.weight",
        "k": f"{prefix}.self_attn.k_proj.weight",
        "v": f"{prefix}.self_attn.v_proj.weight",
        "o": f"{prefix}.self_attn.o_proj.weight",
        "gate": f"{prefix}.mlp.gate_proj.weight",
        "up": f"{prefix}.mlp.up_proj.weight",
        "down": f"{prefix}.mlp.down_proj.weight",
      }
      for name, tensor in tensors.items():
        self._upload(weights[name], tensor)
      cache_zeros = bytes(
        math.prod(KV_CACHE_STORAGE_SHAPE) * DType.BF16.itemsize,
      )
      self.device.write(layer["key_cache"], cache_zeros)
      self.device.write(layer["value_cache"], cache_zeros)
      self.device.run(timeout=60.0)
    self._upload(self.final_norm, "model.norm.weight")
    self.device.run(timeout=30.0)

  def _build_programs(self):
    weights = self.layers[0]["weights"]
    q_projection = decode_projection(
      self.normalized, weights["q"], self.q_compact,
    )
    self.programs = {
      "embedding": decode_embedding(
        self.token_history, self.embedding_weight, self.x_a,
      ),
      "rms": rmsnorm(self.x_a, weights["input_norm"], self.normalized),
      "q": q_projection,
      "k": decode_projection(
        self.normalized, weights["k"], self.k_compact,
      ),
      "rope": decode_rope(
        self.q_compact, self.k_compact, self.v_compact,
        self.cos, self.sin, self.q_heads, self.k_heads, self.v_heads,
      ),
      "cache": kv_cache_write(
        self.k_heads, self.v_heads,
        self.layers[0]["key_cache"], self.layers[0]["value_cache"],
      ),
      "attention": gqa_attention_fused(
        self.q_heads, self.layers[0]["key_cache"],
        self.layers[0]["value_cache"], self.context,
      ),
      "residual": decode_projection_residual(
        self.q_compact, self.x_a, self.x_b,
      ),
      "gate": decode_projection(
        self.normalized, weights["gate"], self.gate,
      ),
      "swiglu": decode_swiglu(self.gate, self.up, self.hidden),
      "dense": decode_compact_to_dense(self.hidden, self.hidden_dense),
      "down": decode_projection(
        self.hidden_dense, weights["down"], self.q_compact,
      ),
      "lm": decode_projection(
        self.normalized, self.lm_weight, self.logits,
      ),
      "argmax": decode_argmax(
        self.logits, self.next_token, self.token_history,
        self.device.cq.noc + self.device.cq.live,
      ),
    }
    self.q_projection_input = q_projection.param(
      f"{self.normalized.name}_decode_token",
    )
    self.context_projection_input = Buffer(
      "e2e_context_decode_token", self.context.addr, self.context.dtype,
      (EMBED_DIM,), None, (self.context.cores[0],), self.context.banks,
      global_address=True,
    )
    self.device.cache_kernels(self.programs.values())
    self._queue("embedding")
    for layer in range(LLAMA_LAYERS):
      self._queue_layer(layer, 0)
    template_norm = self.layers[0]["weights"]["input_norm"]
    self._queue("rms", ((template_norm, self.final_norm),))
    self._queue("lm")
    self._queue("argmax")
    self.decode_trace = self.device.capture_trace((
      "token_pos", "write_pos", "write_token", "start_pos",
      "kv_blocks", "valid_columns",
    ))

  def _queue(self, name, replacements=(), constants=None):
    params = {source: target for source, target in replacements}
    if constants: params.update(constants)
    self.device.queue(self.programs[name], params=params)

  def _queue_layer(self, index, position):
    layer = self.layers[index]
    weights = layer["weights"]
    template = self.layers[0]
    template_weights = template["weights"]
    blocks = position // KV_CACHE_TOKEN_BLOCK + 1
    tail = position % KV_CACHE_TOKEN_BLOCK + 1

    self._queue("rms", (
      (self.x_a, self.x_a),
      (template_weights["input_norm"], weights["input_norm"]),
    ))
    self._queue("q", ((template_weights["q"], weights["q"]),))
    self._queue("k", ((template_weights["k"], weights["k"]),))
    self._queue("k", (
      (template_weights["k"], weights["v"]),
      (self.k_compact, self.v_compact),
    ))
    self._queue("rope", constants={"start_pos": position})
    self._queue("cache", (
      (template["key_cache"], layer["key_cache"]),
      (template["value_cache"], layer["value_cache"]),
    ), {"start_pos": position})
    self._queue("attention", (
      (template["key_cache"], layer["key_cache"]),
      (template["value_cache"], layer["value_cache"]),
    ), {"kv_blocks": blocks, "valid_columns": tail})
    self._queue("q", (
      (self.q_projection_input, self.context_projection_input),
      (template_weights["q"], weights["o"]),
    ))
    self._queue("residual")
    self._queue("rms", (
      (self.x_a, self.x_b),
      (template_weights["input_norm"], weights["post_norm"]),
    ))
    self._queue("gate", ((template_weights["gate"], weights["gate"]),))
    self._queue("gate", (
      (template_weights["gate"], weights["up"]),
      (self.gate, self.up),
    ))
    self._queue("swiglu")
    self._queue("dense")
    self._queue("down", ((template_weights["down"], weights["down"]),))
    self._queue("residual", (
      (self.x_a, self.x_b),
      (self.x_b, self.x_a),
    ))

  def load_tokens(self, tokens):
    """Upload the initial prompt once into the resident token history."""
    tokens = np.asarray(tokens, dtype=np.uint32).reshape(-1)
    if not 0 < len(tokens) < ROPE_CACHE_TOKENS:
      raise ValueError(
        f"prompt token count must be in 1..{ROPE_CACHE_TOKENS - 1}",
      )
    if np.any(tokens >= VOCAB_SIZE):
      raise ValueError(f"prompt tokens must be in 0..{VOCAB_SIZE - 1}")
    history = np.zeros(ROPE_CACHE_TOKENS, dtype=np.uint32)
    history[:len(tokens)] = tokens
    self.device.write(
      self.token_history, self.token_history.from_numpy(history),
    )
    self.device.run(timeout=30.0)

  def decode(self, position, *, logits=True, append=True):
    """Consume one token at ``position`` and optionally return greedy next ID."""
    if not 0 <= position < ROPE_CACHE_TOKENS - 1:
      raise ValueError(
        f"decode position must be in 0..{ROPE_CACHE_TOKENS - 2}",
      )
    started = time.monotonic()
    self.decode_trace.replay({
      "token_pos": position,
      "write_pos": position + 1,
      "write_token": int(append),
      "start_pos": position,
      "kv_blocks": position // KV_CACHE_TOKEN_BLOCK + 1,
      "valid_columns": position % KV_CACHE_TOKEN_BLOCK + 1,
    }, timeout=30.0)
    device_us = (time.monotonic() - started) * 1e6

    if not logits: return None, device_us
    read_started = time.perf_counter_ns()
    live = self.device.cq.live + (position + 1) * 16
    token, marker = struct.unpack(
      "<II", self.device.pcie.sysmem.read(live, 8),
    )
    self.host_result_read_us += (
      time.perf_counter_ns() - read_started
    ) / 1e3
    self.host_result_reads += 1
    if marker != position + 2:
      raise RuntimeError(
        f"live token slot {position + 1} was not published",
      )
    return token, device_us

  def close(self):
    if getattr(self, "device", None) is not None:
      self.device.close()
      self.device = None


def run_decode_e2e(
  prompt="The capital of France is", steps=None,
  safetensor_path="weights/model.safetensors",
  tokenizer_path="weights",
):
  """Run prompt ingestion and greedy generation entirely through decode."""
  if steps is not None and steps < 1:
    raise ValueError("steps must be positive")
  from transformers import AutoTokenizer, TextStreamer

  tokenizer = AutoTokenizer.from_pretrained(
    str(Path(tokenizer_path)), local_files_only=True,
  )
  if tokenizer.chat_template is None:
    raise ValueError("the Instruct tokenizer is missing its chat template")
  prompt_ids = tokenizer.apply_chat_template(
    ({"role": "user", "content": prompt},),
    tokenize=True, add_generation_prompt=True,
  )
  # Newer transformers return a BatchEncoding instead of a flat ID list.
  if not isinstance(prompt_ids, list):
    prompt_ids = prompt_ids["input_ids"]
    if prompt_ids and isinstance(prompt_ids[0], list): prompt_ids = prompt_ids[0]
  if not prompt_ids:
    raise ValueError("prompt tokenization produced no tokens")
  max_steps = ROPE_CACHE_TOKENS - len(prompt_ids)
  if max_steps < 1:
    raise ValueError("prompt leaves no room for decode generation")
  if steps is None:
    steps = max_steps
  elif steps > max_steps:
    raise ValueError("prompt plus generation exceeds the 8192-token cache")

  runtime = Llama3Decode(safetensor_path)
  generation_seconds = 0.0
  generation_replays = 0
  generated = []
  streamer = TextStreamer(
    tokenizer, skip_prompt=False, skip_special_tokens=True,
    clean_up_tokenization_spaces=False,
  )
  try:
    runtime.load_tokens(prompt_ids)
    next_token = None
    for position in range(len(prompt_ids)):
      last_prompt_token = position == len(prompt_ids) - 1
      if last_prompt_token: token_started = time.monotonic()
      next_token, _ = runtime.decode(
        position, logits=last_prompt_token, append=last_prompt_token,
      )
      if last_prompt_token:
        generation_seconds += time.monotonic() - token_started
        generation_replays += 1

    for step in range(steps):
      generated.append(next_token)
      streamer.put(np.asarray([next_token], dtype=np.int64))
      if next_token in EOS_TOKEN_IDS or step + 1 == steps: break
      position = len(prompt_ids) + step
      token_started = time.monotonic()
      next_token, _ = runtime.decode(position, logits=True)
      generation_seconds += time.monotonic() - token_started
      generation_replays += 1
    streamer.end()
  finally:
    runtime.close()

  print(f"{generation_replays / generation_seconds:.2f} tok/s")


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


def run_decode_endpoints_hardware(
  safetensor_path="weights/model.safetensors", token=128000,
):
  """Validate one-token embedding and the tied full-vocabulary projection."""
  if not 0 <= token < VOCAB_SIZE:
    raise ValueError(f"token must be in 0..{VOCAB_SIZE - 1}")
  device = Device()
  try:
    device.init_device()
    cores = device.dram.cores[:LLAMA_CORES]
    token_id = device.dram.buffer(
      "decode_token_id", DType.U32, (1,), global_address=True,
    )
    embedding_weight = device.dram.buffer(
      "decode_embedding_weight", DType.BF16,
      (VOCAB_SIZE, EMBED_DIM), axis=0, global_address=True,
    )
    activation = device.dram.buffer(
      "decode_embedding_output", DType.BF16, (1, EMBED_DIM),
      axis=0, global_address=True,
    )
    lm_weight = device.dram.buffer(
      "decode_lm_weight", DType.BF16, (VOCAB_SIZE, EMBED_DIM),
      axis=0, cores=cores,
    )
    logits = device.dram.buffer(
      "decode_logits", DType.BF16,
      (LLAMA_CORES, lm_weight.items_per_core), axis=0, cores=cores,
    )

    weight_data = embedding_weight.from_safetensor(
      "model.embed_tokens.weight", safetensor_path,
    )
    device.write(embedding_weight, weight_data)
    device.run(timeout=30.0)
    device.write(lm_weight, weight_data)
    device.run(timeout=30.0)
    device.write(
      token_id, token_id.from_numpy(np.asarray([token], dtype=np.uint32)),
    )
    embed_program = decode_embedding(
      token_id, embedding_weight, activation,
    )
    lm_program = decode_projection(activation, lm_weight, logits)
    device.queue(embed_program)
    embedding_readback = device.queue_read(activation)
    embed_timestamps = device.run(timeout=10.0)

    row_bytes = EMBED_DIM * DType.BF16.itemsize
    expected_embedding = weight_data[
      token * row_bytes:(token + 1) * row_bytes
    ]
    if embedding_readback.result() != expected_embedding:
      actual_embedding = activation.to_numpy(
        embedding_readback.result(),
      ).reshape(-1)
      expected_values = embedding_weight.to_numpy(
        expected_embedding,
      ).reshape(-1)
      feature = int(np.abs(actual_embedding - expected_values).argmax())
      raise AssertionError(
        f"decode embedding mismatch at feature {feature}: "
        f"actual={actual_embedding[feature]}, "
        f"expected={expected_values[feature]}",
      )

    device.queue(lm_program)
    logits_readback = device.queue_read(logits)
    lm_timestamps = device.run(timeout=30.0)
    actual = _projection_values(
      logits, logits_readback.result(), lm_weight.item_counts,
    )
    activation_values = activation.to_numpy(
      embedding_readback.result(),
    ).reshape(-1)
    sample_rows = np.unique(np.linspace(
      0, VOCAB_SIZE - 1, 65, dtype=np.int64,
    ))
    weight_words = np.frombuffer(weight_data, dtype="<u2").reshape(
      VOCAB_SIZE, EMBED_DIM,
    )
    sample_weights = (
      weight_words[sample_rows].astype(np.uint32) << 16
    ).view(np.float32)
    expected = np.sum(
      np.multiply(
        sample_weights, activation_values[None, :], dtype=np.float32,
      ),
      axis=1, dtype=np.float32,
    )
    difference = np.subtract(actual[sample_rows], expected, dtype=np.float32)
    relative_l2 = float(
      np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
    )
    pcc = float(np.corrcoef(actual[sample_rows], expected)[0, 1])
    if (
      not np.all(np.isfinite(actual)) or relative_l2 > 0.02 or pcc < 0.999
    ):
      sample = int(np.abs(difference).argmax())
      row = int(sample_rows[sample])
      raise AssertionError(
        f"tied LM head mismatch at row {row}: actual={actual[row]}, "
        f"expected={expected[sample]}, relative_l2={relative_l2}, PCC={pcc}",
      )

    print("PASS llama3 decode embedding + tied LM head")
    print(f"token: {token}")
    print(f"embedding: {embed_timestamps[-1].us:.3f} us, bit-exact")
    print(
      f"LM head: {lm_timestamps[-1].us:.3f} us, "
      f"sampled relative L2={relative_l2:.6g}, PCC={pcc:.9f}",
    )
    print(f"host argmax token: {int(np.argmax(actual))}")
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


def run_decode_gqa_attention_hardware(tokens=127, repeats=1):
  """Validate fused decode GQA without score/probability DRAM tensors."""
  if not 1 <= tokens <= ROPE_CACHE_TOKENS:
    raise ValueError(f"tokens must be in 1..{ROPE_CACHE_TOKENS}")
  if repeats < 1: raise ValueError("repeats must be positive")
  blocks = (tokens + KV_CACHE_TOKEN_BLOCK - 1) // KV_CACHE_TOKEN_BLOCK
  tail = (tokens - 1) % KV_CACHE_TOKEN_BLOCK + 1

  device = Device()
  try:
    device.init_device()
    q = device.dram.buffer(
      "attention_q", DType.BF16, (Q_HEADS, HEAD_DIM), axis=0,
      global_address=True,
    )
    key_cache = device.dram.buffer(
      "attention_key_cache", DType.BF16, KV_CACHE_STORAGE_SHAPE,
      axis=0, global_address=True,
    )
    value_cache = device.dram.buffer(
      "attention_value_cache", DType.BF16, KV_CACHE_STORAGE_SHAPE,
      axis=0, global_address=True,
    )
    context = device.dram.buffer(
      "attention_context", DType.BF16, GQA_CONTEXT_SHAPE,
      axis=0, global_address=True,
    )

    rng = np.random.default_rng(8)
    q_values = rng.normal(0, 0.25, q.shape).astype(np.float32)
    key_values = rng.normal(
      0, 0.25, (KV_HEADS, tokens, HEAD_DIM),
    ).astype(np.float32)
    value_values = rng.normal(
      0, 0.25, (KV_HEADS, tokens, HEAD_DIM),
    ).astype(np.float32)
    key_storage = np.zeros(KV_CACHE_STORAGE_SHAPE, dtype=np.float32)
    value_storage = np.zeros(KV_CACHE_STORAGE_SHAPE, dtype=np.float32)
    for head in range(KV_HEADS):
      for block in range(blocks):
        start, end = block * 32, min((block + 1) * 32, tokens)
        for feature_half in range(KV_CACHE_FEATURE_TILES):
          tile = block * KV_CACHE_FEATURE_TILES + feature_half
          features = slice(feature_half * 32, (feature_half + 1) * 32)
          key_storage[head, tile].reshape(32, 32)[:end - start] = (
            key_values[head, start:end, features]
          )
          value_storage[head, tile].reshape(32, 32)[:end - start] = (
            value_values[head, start:end, features]
          )

    q_data = q.from_numpy(q_values)
    key_data = key_cache.from_numpy(key_storage)
    value_data = value_cache.from_numpy(value_storage)
    q_reference = q.to_numpy(q_data)
    key_reference = key_cache.to_numpy(key_data)
    value_reference = value_cache.to_numpy(value_data)

    expected = np.empty((Q_HEADS, HEAD_DIM), dtype=np.float32)
    for kv_head_index in range(KV_HEADS):
      keys = np.concatenate([
        key_reference[kv_head_index, block * 2].reshape(32, 32)
        for block in range(blocks)
      ], axis=0)[:tokens]
      keys_high = np.concatenate([
        key_reference[kv_head_index, block * 2 + 1].reshape(32, 32)
        for block in range(blocks)
      ], axis=0)[:tokens]
      keys = np.concatenate((keys, keys_high), axis=1)
      values = np.concatenate([
        np.concatenate((
          value_reference[kv_head_index, block * 2].reshape(32, 32),
          value_reference[kv_head_index, block * 2 + 1].reshape(32, 32),
        ), axis=1)
        for block in range(blocks)
      ], axis=0)[:tokens]
      query_start = kv_head_index * GQA_GROUP_SIZE
      queries = q_reference[query_start:query_start + GQA_GROUP_SIZE]
      scores = (queries @ keys.T) * np.float32(HEAD_DIM ** -0.5)
      running_max = np.full((GQA_GROUP_SIZE, 1), -np.inf, dtype=np.float32)
      running_sum = np.zeros((GQA_GROUP_SIZE, 1), dtype=np.float32)
      output = np.zeros((GQA_GROUP_SIZE, HEAD_DIM), dtype=np.float32)
      for block in range(blocks):
        start, end = block * 32, min((block + 1) * 32, tokens)
        block_scores = scores[:, start:end]
        block_max = np.max(block_scores, axis=1, keepdims=True)
        new_max = np.maximum(running_max, block_max)
        alpha = np.exp(running_max - new_max, dtype=np.float32)
        probability = np.exp(block_scores - new_max, dtype=np.float32)
        probability_words = np.frombuffer(
          _bf16_rne_bytes(probability), dtype="<u2",
        ).astype(np.uint32)
        probability_bf16 = (probability_words << 16).view(np.float32).reshape(
          probability.shape,
        )
        output = output * alpha + probability_bf16 @ values[start:end]
        running_sum = running_sum * alpha + np.sum(
          probability, axis=1, keepdims=True, dtype=np.float32,
        )
        running_max = new_max
      expected[query_start:query_start + GQA_GROUP_SIZE] = output / running_sum
    expected_words = np.frombuffer(
      _bf16_rne_bytes(expected), dtype="<u2",
    ).astype(np.uint32)
    expected = (expected_words << 16).view(np.float32).reshape(expected.shape)

    device.write(q, q_data)
    device.write(key_cache, key_data)
    device.write(value_cache, value_data)
    device.write(
      context,
      context.from_numpy(np.full(GQA_CONTEXT_SHAPE, -0.5, dtype=np.float32)),
    )
    program = gqa_attention_fused(q, key_cache, value_cache, context)
    params = {"kv_blocks": blocks, "valid_columns": tail}
    device.queue(program, params=params)
    readback = device.queue_read(context)
    timestamps = device.run(timeout=10.0)
    samples = [timestamps[-1].us]
    actual = context.to_numpy(readback.result()).reshape(Q_HEADS, HEAD_DIM)

    difference = np.subtract(actual, expected, dtype=np.float32)
    error = np.abs(difference)
    relative_l2 = float(
      np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
    )
    pcc = float(np.corrcoef(actual.reshape(-1), expected.reshape(-1))[0, 1])
    if (
      not np.all(np.isfinite(actual)) or float(error.max()) > 0.003 or
      relative_l2 > 0.15 or pcc < 0.99
    ):
      query_head, feature = np.unravel_index(int(error.argmax()), error.shape)
      raise AssertionError(
        f"fused GQA mismatch at head {query_head}, feature {feature}: "
        f"actual={actual[query_head, feature]}, "
        f"expected={expected[query_head, feature]}, max_abs={error.max()}, "
        f"relative_l2={relative_l2}, PCC={pcc}",
      )

    for _ in range(repeats - 1):
      samples.append(device.run(program, params=params, timeout=10.0)[-1].us)
    print("PASS llama3 fused decode GQA attention")
    print(f"logical operation: [32,64] x [8,{tokens},64] -> [1,2048]")
    print(f"workers: {KV_HEADS}, history blocks: {blocks}, tail: {tail}")
    print(f"max abs error: {error.max():.6g}")
    print(f"relative L2: {relative_l2:.6g}, PCC: {pcc:.9f}")
    print(
      f"latency us: min={min(samples):.3f}, median={np.median(samples):.3f}, "
      f"max={max(samples):.3f}",
    )
  finally:
    device.close()


def run_decode_mlp_up_hardware(
  safetensor_path="weights/model.safetensors", repeats=1,
):
  """Validate 2048->8192 gate/up projections and compact SwiGLU."""
  if repeats < 1: raise ValueError("repeats must be positive")
  device = Device()
  try:
    device.init_device()
    cores = device.dram.cores[:LLAMA_CORES]
    x = device.dram.buffer(
      "mlp_x", DType.BF16, (1, EMBED_DIM), axis=0,
      global_address=True,
    )
    specs = (
      ("gate", "model.layers.0.mlp.gate_proj.weight"),
      ("up", "model.layers.0.mlp.up_proj.weight"),
    )
    weights, outputs, programs, weight_data = {}, {}, {}, {}
    for name, tensor in specs:
      weight = device.dram.buffer(
        f"mlp_{name}_weight", DType.BF16, (MLP_DIM, EMBED_DIM),
        axis=0, cores=cores,
      )
      output = device.dram.buffer(
        f"mlp_{name}_compact", DType.BF16,
        (LLAMA_CORES, weight.items_per_core), axis=0, cores=cores,
      )
      weights[name], outputs[name] = weight, output
      weight_data[name] = weight.from_safetensor(tensor, safetensor_path)
      programs[name] = decode_projection(x, weight, output)
    hidden = device.dram.buffer(
      "mlp_hidden_compact", DType.BF16, outputs["gate"].shape,
      axis=0, cores=cores,
    )
    swiglu_program = decode_swiglu(outputs["gate"], outputs["up"], hidden)
    dense_hidden = device.dram.buffer(
      "mlp_hidden_dense", DType.BF16, (1, MLP_DIM), axis=0,
      global_address=True,
    )
    reassembly_program = decode_compact_to_dense(hidden, dense_hidden)

    rng = np.random.default_rng(10)
    x_data = x.from_numpy(
      rng.normal(0, 0.25, x.shape).astype(np.float32),
    )
    x_reference = x.to_numpy(x_data).reshape(-1)
    references = {
      name: np.sum(
        np.multiply(
          weights[name].to_numpy(weight_data[name]), x_reference[None, :],
          dtype=np.float32,
        ),
        axis=1, dtype=np.float32,
      )
      for name, _ in specs
    }

    device.write(x, x_data)
    for name, _ in specs: device.write(weights[name], weight_data[name])
    device.write(
      dense_hidden,
      dense_hidden.from_numpy(np.full(
        dense_hidden.shape, -0.5, dtype=np.float32,
      )),
    )
    for name, _ in specs: device.queue(programs[name])
    device.queue(swiglu_program)
    device.queue(reassembly_program)
    readbacks = {
      name: device.queue_read(outputs[name]) for name, _ in specs
    }
    hidden_readback = device.queue_read(hidden)
    dense_readback = device.queue_read(dense_hidden)
    timestamps = device.run(timeout=15.0)

    actuals, metrics = {}, {}
    for name, _ in specs:
      actual = _projection_values(
        outputs[name], readbacks[name].result(), weights[name].item_counts,
      )
      difference = np.subtract(actual, references[name], dtype=np.float32)
      relative_l2 = float(
        np.linalg.norm(difference) /
        (np.linalg.norm(references[name]) + 1e-12),
      )
      pcc = float(np.corrcoef(actual, references[name])[0, 1])
      if (
        not np.all(np.isfinite(actual)) or relative_l2 > 0.02 or pcc < 0.999
      ):
        row = int(np.abs(difference).argmax())
        raise AssertionError(
          f"MLP {name} mismatch at row {row}: actual={actual[row]}, "
          f"expected={references[name][row]}, "
          f"relative_l2={relative_l2}, PCC={pcc}",
        )
      actuals[name] = actual
      metrics[name] = relative_l2, pcc

    gate_actual, up_actual = actuals["gate"], actuals["up"]
    activated = np.multiply(
      gate_actual,
      np.reciprocal(
        np.float32(1.0) + np.exp(-gate_actual, dtype=np.float32),
        dtype=np.float32,
      ),
      dtype=np.float32,
    )
    hidden_values = np.multiply(activated, up_actual, dtype=np.float32)
    expected_words = np.frombuffer(
      _bf16_rne_bytes(hidden_values), dtype="<u2",
    ).astype(np.uint32)
    expected = (expected_words << 16).view(np.float32)
    actual = _projection_values(
      hidden, hidden_readback.result(), weights["gate"].item_counts,
    )
    difference = np.subtract(actual, expected, dtype=np.float32)
    error = np.abs(difference)
    relative_l2 = float(
      np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
    )
    pcc = float(np.corrcoef(actual, expected)[0, 1])
    if (
      not np.all(np.isfinite(actual)) or float(error.max()) > 0.02 or
      relative_l2 > 0.02 or pcc < 0.999
    ):
      feature = int(error.argmax())
      raise AssertionError(
        f"SwiGLU mismatch at feature {feature}: actual={actual[feature]}, "
        f"expected={expected[feature]}, max_abs={error.max()}, "
        f"relative_l2={relative_l2}, PCC={pcc}",
      )
    dense_actual = dense_hidden.to_numpy(dense_readback.result()).reshape(-1)
    if not np.array_equal(dense_actual, actual):
      feature = int(np.abs(dense_actual - actual).argmax())
      raise AssertionError(
        f"MLP compact reassembly mismatch at feature {feature}: "
        f"actual={dense_actual[feature]}, expected={actual[feature]}",
      )

    samples = {"gate": [timestamps[0].us], "up": [timestamps[1].us],
               "swiglu": [timestamps[2].us], "reassembly": [timestamps[3].us]}
    for _ in range(repeats - 1):
      for name, _ in specs:
        samples[name].append(device.run(programs[name], timeout=15.0)[-1].us)
      samples["swiglu"].append(device.run(
        swiglu_program, timeout=10.0,
      )[-1].us)
      samples["reassembly"].append(device.run(
        reassembly_program, timeout=10.0,
      )[-1].us)
    print("PASS llama3 decode gate/up + SwiGLU")
    for name, _ in specs:
      rel, corr = metrics[name]
      print(
        f"{name}: median={np.median(samples[name]):.3f} us, "
        f"relative L2={rel:.6g}, PCC={corr:.9f}",
      )
    print(
      f"SwiGLU: median={np.median(samples['swiglu']):.3f} us, "
      f"max_abs={error.max():.6g}, relative L2={relative_l2:.6g}, "
      f"PCC={pcc:.9f}",
    )
    print(
      f"compact -> dense: median={np.median(samples['reassembly']):.3f} us, "
      "bit-exact",
    )
  finally:
    device.close()


def run_decode_mlp_down_hardware(
  safetensor_path="weights/model.safetensors", repeats=1,
):
  """Validate the 8192->2048 down projection and fused residual add."""
  if repeats < 1: raise ValueError("repeats must be positive")
  device = Device()
  try:
    device.init_device()
    cores = device.dram.cores[:LLAMA_CORES]
    hidden = device.dram.buffer(
      "mlp_down_hidden", DType.BF16, (1, MLP_DIM), axis=0,
      global_address=True,
    )
    residual = device.dram.buffer(
      "mlp_down_residual", DType.BF16, (1, EMBED_DIM), axis=0,
      global_address=True,
    )
    weight = device.dram.buffer(
      "mlp_down_weight", DType.BF16, (EMBED_DIM, MLP_DIM),
      axis=0, cores=cores,
    )
    compact = device.dram.buffer(
      "mlp_down_compact", DType.BF16, (LLAMA_CORES, 18),
      axis=0, cores=cores,
    )
    output = device.dram.buffer(
      "mlp_down_output", DType.BF16, (1, EMBED_DIM), axis=0,
      global_address=True,
    )

    rng = np.random.default_rng(11)
    hidden_data = hidden.from_numpy(
      rng.normal(0, 0.05, hidden.shape).astype(np.float32),
    )
    residual_data = residual.from_numpy(
      rng.normal(0, 0.25, residual.shape).astype(np.float32),
    )
    weight_data = weight.from_safetensor(
      "model.layers.0.mlp.down_proj.weight", safetensor_path,
    )
    hidden_reference = hidden.to_numpy(hidden_data).reshape(-1)
    residual_reference = residual.to_numpy(residual_data).reshape(-1)
    projection_reference = np.sum(
      np.multiply(
        weight.to_numpy(weight_data), hidden_reference[None, :],
        dtype=np.float32,
      ),
      axis=1, dtype=np.float32,
    )

    projection_program = decode_projection(hidden, weight, compact)
    residual_program = decode_projection_residual(
      compact, residual, output,
    )
    device.write(hidden, hidden_data)
    device.write(residual, residual_data)
    device.write(weight, weight_data)
    device.queue(projection_program)
    device.queue(residual_program)
    compact_readback = device.queue_read(compact)
    output_readback = device.queue_read(output)
    timestamps = device.run(timeout=15.0)

    projection_actual = _projection_values(
      compact, compact_readback.result(), weight.item_counts,
    )
    projection_difference = np.subtract(
      projection_actual, projection_reference, dtype=np.float32,
    )
    projection_relative_l2 = float(
      np.linalg.norm(projection_difference) /
      (np.linalg.norm(projection_reference) + 1e-12),
    )
    projection_pcc = float(np.corrcoef(
      projection_actual, projection_reference,
    )[0, 1])
    if (
      not np.all(np.isfinite(projection_actual)) or
      projection_relative_l2 > 0.03 or projection_pcc < 0.999
    ):
      row = int(np.abs(projection_difference).argmax())
      raise AssertionError(
        f"down_proj mismatch at row {row}: "
        f"actual={projection_actual[row]}, "
        f"expected={projection_reference[row]}, "
        f"relative_l2={projection_relative_l2}, PCC={projection_pcc}",
      )

    summed = np.add(
      projection_actual, residual_reference, dtype=np.float32,
    ).reshape(output.shape)
    expected_words = np.frombuffer(
      _bf16_rne_bytes(summed), dtype="<u2",
    ).astype(np.uint32)
    expected = (expected_words << 16).view(np.float32).reshape(-1)
    actual = output.to_numpy(output_readback.result()).reshape(-1)
    difference = np.subtract(actual, expected, dtype=np.float32)
    error = np.abs(difference)
    relative_l2 = float(
      np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
    )
    pcc = float(np.corrcoef(actual, expected)[0, 1])
    if (
      not np.all(np.isfinite(actual)) or float(error.max()) > 0.005 or
      relative_l2 > 0.01 or pcc < 0.9999
    ):
      feature = int(error.argmax())
      raise AssertionError(
        f"down_proj residual mismatch at feature {feature}: "
        f"actual={actual[feature]}, expected={expected[feature]}, "
        f"max_abs={error.max()}, relative_l2={relative_l2}, PCC={pcc}",
      )

    projection_samples = [timestamps[0].us]
    residual_samples = [timestamps[1].us]
    for _ in range(repeats - 1):
      projection_samples.append(device.run(
        projection_program, timeout=15.0,
      )[-1].us)
      residual_samples.append(device.run(
        residual_program, timeout=10.0,
      )[-1].us)
    print("PASS llama3 decode down_proj + residual")
    print(f"weights: {safetensor_path}")
    print(
      f"down_proj: median={np.median(projection_samples):.3f} us, "
      f"relative L2={projection_relative_l2:.6g}, "
      f"PCC={projection_pcc:.9f}",
    )
    print(
      f"reassembly + residual: median={np.median(residual_samples):.3f} us, "
      f"max_abs={error.max():.6g}, relative L2={relative_l2:.6g}, "
      f"PCC={pcc:.9f}",
    )
  finally:
    device.close()


def run_decode_o_proj_hardware(
  safetensor_path="weights/model.safetensors", repeats=1,
):
  """Validate o_proj followed by compact reassembly and residual add."""
  if repeats < 1: raise ValueError("repeats must be positive")
  device = Device()
  try:
    device.init_device()
    cores = device.dram.cores[:LLAMA_CORES]
    context = device.dram.buffer(
      "o_proj_context", DType.BF16, (1, EMBED_DIM), axis=0,
      global_address=True,
    )
    residual = device.dram.buffer(
      "o_proj_residual", DType.BF16, (1, EMBED_DIM), axis=0,
      global_address=True,
    )
    weight = device.dram.buffer(
      "o_proj_weight", DType.BF16, (EMBED_DIM, EMBED_DIM), axis=0,
      cores=cores,
    )
    compact = device.dram.buffer(
      "o_proj_compact", DType.BF16, (LLAMA_CORES, 18), axis=0,
      cores=cores,
    )
    output = device.dram.buffer(
      "o_proj_output", DType.BF16, (1, EMBED_DIM), axis=0,
      global_address=True,
    )

    rng = np.random.default_rng(9)
    context_data = context.from_numpy(
      rng.normal(0, 0.05, context.shape).astype(np.float32),
    )
    residual_data = residual.from_numpy(
      rng.normal(0, 0.25, residual.shape).astype(np.float32),
    )
    weight_data = weight.from_safetensor(
      "model.layers.0.self_attn.o_proj.weight", safetensor_path,
    )
    context_reference = context.to_numpy(context_data).reshape(-1)
    residual_reference = residual.to_numpy(residual_data).reshape(-1)
    projection_reference = np.sum(
      np.multiply(
        weight.to_numpy(weight_data), context_reference[None, :],
        dtype=np.float32,
      ),
      axis=1, dtype=np.float32,
    )

    projection_program = decode_projection(context, weight, compact)
    residual_program = decode_projection_residual(compact, residual, output)
    device.write(context, context_data)
    device.write(residual, residual_data)
    device.write(weight, weight_data)
    device.write(
      output,
      output.from_numpy(np.full(output.shape, -0.5, dtype=np.float32)),
    )
    device.queue(projection_program)
    device.queue(residual_program)
    compact_readback = device.queue_read(compact)
    output_readback = device.queue_read(output)
    timestamps = device.run(timeout=10.0)

    projection_actual = _projection_values(
      compact, compact_readback.result(), weight.item_counts,
    )
    projection_difference = np.subtract(
      projection_actual, projection_reference, dtype=np.float32,
    )
    projection_relative_l2 = float(
      np.linalg.norm(projection_difference) /
      (np.linalg.norm(projection_reference) + 1e-12),
    )
    projection_pcc = float(np.corrcoef(
      projection_actual, projection_reference,
    )[0, 1])
    if (
      not np.all(np.isfinite(projection_actual)) or
      projection_relative_l2 > 0.02 or projection_pcc < 0.999
    ):
      row = int(np.abs(projection_difference).argmax())
      raise AssertionError(
        f"o_proj mismatch at row {row}: actual={projection_actual[row]}, "
        f"expected={projection_reference[row]}, "
        f"relative_l2={projection_relative_l2}, PCC={projection_pcc}",
      )

    # Use the actual compact projection to isolate reassembly/add correctness.
    summed = np.add(
      projection_actual, residual_reference, dtype=np.float32,
    ).reshape(output.shape)
    expected_words = np.frombuffer(
      _bf16_rne_bytes(summed), dtype="<u2",
    ).astype(np.uint32)
    expected = (expected_words << 16).view(np.float32).reshape(-1)
    actual = output.to_numpy(output_readback.result()).reshape(-1)
    difference = np.subtract(actual, expected, dtype=np.float32)
    error = np.abs(difference)
    relative_l2 = float(
      np.linalg.norm(difference) / (np.linalg.norm(expected) + 1e-12),
    )
    pcc = float(np.corrcoef(actual, expected)[0, 1])
    if (
      not np.all(np.isfinite(actual)) or float(error.max()) > 0.005 or
      relative_l2 > 0.01 or pcc < 0.9999
    ):
      feature = int(error.argmax())
      raise AssertionError(
        f"o_proj residual mismatch at feature {feature}: "
        f"actual={actual[feature]}, expected={expected[feature]}, "
        f"max_abs={error.max()}, relative_l2={relative_l2}, PCC={pcc}",
      )

    projection_samples = [timestamps[0].us]
    residual_samples = [timestamps[1].us]
    for _ in range(repeats - 1):
      projection_samples.append(device.run(
        projection_program, timeout=10.0,
      )[-1].us)
      residual_samples.append(device.run(
        residual_program, timeout=10.0,
      )[-1].us)
    print("PASS llama3 decode o_proj + residual")
    print(f"weights: {safetensor_path}")
    print(
      f"o_proj: median={np.median(projection_samples):.3f} us, "
      f"relative L2={projection_relative_l2:.6g}, "
      f"PCC={projection_pcc:.9f}",
    )
    print(
      f"reassembly + residual: median={np.median(residual_samples):.3f} us, "
      f"max_abs={error.max():.6g}, relative L2={relative_l2:.6g}, "
      f"PCC={pcc:.9f}",
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
    "--prompt",
    help="run end-to-end generation from this prompt (an empty prompt is valid)",
  )
  parser.add_argument(
    "--steps", type=int,
    help="optional generation cap; default runs until EOS/context limit",
  )
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
  parser.add_argument("--endpoints", action="store_true")
  parser.add_argument("--e2e", action="store_true")
  parser.add_argument("--rope", action="store_true")
  parser.add_argument("--kv-cache", action="store_true")
  parser.add_argument("--attention", action="store_true")
  parser.add_argument("--o-proj", action="store_true")
  parser.add_argument("--mlp-up", action="store_true")
  parser.add_argument("--mlp-down", action="store_true")
  parser.add_argument("--decode", action="store_true")
  parser.add_argument("--core-start", type=int, default=0)
  parser.add_argument("--repeats", type=int, default=5)
  args = parser.parse_args()
  if args.attention:
    run_decode_gqa_attention_hardware(args.seq_len, args.repeats)
  elif args.e2e or args.prompt is not None:
    run_decode_e2e(
      (
        "The capital of France is"
        if args.prompt is None else args.prompt
      ),
      args.steps,
      args.safetensor or "weights/model.safetensors",
    )
  elif args.o_proj:
    run_decode_o_proj_hardware(
      args.safetensor or "weights/model.safetensors", args.repeats,
    )
  elif args.mlp_up:
    run_decode_mlp_up_hardware(
      args.safetensor or "weights/model.safetensors", args.repeats,
    )
  elif args.mlp_down:
    run_decode_mlp_down_hardware(
      args.safetensor or "weights/model.safetensors", args.repeats,
    )
  elif args.kv_cache:
    run_decode_kv_cache_hardware(repeats=args.repeats)
  elif args.rope:
    run_decode_rope_hardware(repeats=args.repeats)
  elif args.rope_cache:
    run_rope_cache_hardware()
  elif args.endpoints:
    run_decode_endpoints_hardware(
      args.safetensor or "weights/model.safetensors",
    )
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
