"""Llama 3.2 1B batch-1 decode kernels and resident runtime.

Decode dataflow:

  embedding -> RMSNorm -> fused QKV -> RoPE -> KV append -> GQA attention
            -> O projection + residual -> RMSNorm
            -> gate/up -> SwiGLU -> dense -> down projection + residual
            -> final RMSNorm -> LM head -> argmax/token publication

The file is grouped by kernel family below and contains decode only.
"""

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
from ttk import l1
from ttk.cb import CB
from ttk.sfpu import (
  LaneConfig, LReg, SfpuFormat, SfpuProgram, SfpuProgramBuilder,
)
from ttk.shard import specialize
from ttk.sync import Sem, SemWait, Stall, Wait, sem_get, sem_wait, stall
from ttk.model import UnpackTarget


VOCAB_SIZE = 128256
EMBED_DIM = 2048
EMBEDDING_TILES = EMBED_DIM // 1024
EMBEDDING_TILES_SHIFT = EMBEDDING_TILES.bit_length() - 1  # multiply by a shift
LLAMA_CORES = 117
LLAMA_LAYERS = 16
EOS_TOKEN_IDS = frozenset((128001, 128008, 128009))
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
KV_CACHE_TOKEN_BLOCK = 32
KV_CACHE_TIME_BLOCKS = ROPE_CACHE_TOKENS // KV_CACHE_TOKEN_BLOCK
KV_CACHE_FEATURE_TILES = HEAD_DIM // 32
KV_CACHE_TILES_PER_HEAD = KV_CACHE_TIME_BLOCKS * KV_CACHE_FEATURE_TILES
# Each innermost 1024-element row is one ordinary 32x32 tile.  Keeping this
# This exposes the physical tile order expected by the score matmul.
KV_CACHE_STORAGE_SHAPE = (
  KV_HEADS, KV_CACHE_TILES_PER_HEAD, 32 * 32,
)
GQA_GROUP_SIZE = Q_HEADS // KV_HEADS
GQA_CONTEXT_SHAPE = (1, EMBED_DIM)
GQA_ROW_CHUNKS = (0, 2, 16, 18)


# ---------------------------------------------------------------------------
# Host tables and shared code-generation helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Linear projections: generic GEMV and fused Q/K/V
# ---------------------------------------------------------------------------

def _decode_projections_program(x, projections):
  """Build one launch containing one or more identically shaped GEMV pipes."""
  input_dim = x.shape[1]
  input_tiles = input_dim // 1024
  row_starts = tuple(
    Const(f"{weight.name}_row_start", weight.item_starts)
    if weight.global_address and len(weight.cores) > 1 else None
    for weight, _, _ in projections
  )
  token = Buffer(
    f"{x.name}_decode_token", x.addr, x.dtype, (input_dim,), None,
    (x.cores[0],), x.banks, global_address=True,
    dram_endpoints=x.dram_endpoints,
  )
  parameters = tuple(
    parameter
    for (weight, output, _), row_start in zip(projections, row_starts)
    for parameter in (
      (weight, output) if row_start is None
      else (weight, output, row_start)
    )
  )
  p = Program(
    projections[0][0].cores, token, *parameters, fp32_dst=True,
  )
  weight_cb = p.cb(DType.BF16, depth=4)
  scalar_cb = p.cb(DType.BF16, depth=2)
  token_l1 = p.l1(input_tiles * token.tile_size, alignment=16)
  compact_l1 = tuple(
    p.l1(output.tiles_per_item * output.tile_size, alignment=16)
    for _, output, _ in projections
  )

  p.brisc.noc.read_tiles(token, tuple(
    (tile, token_l1 + tile * token.tile_size)
    for tile in range(input_tiles)
  ))
  for (weight, _, local_rows), row_start in zip(
    projections, row_starts,
  ):
    for local_row in p.brisc.range(local_rows):
      source_row = local_row
      if row_start is not None:
        source_row = p.brisc.reg(exclude=local_row)
        p.brisc.read(source_row, p.param_addr(row_start))
        p.brisc.add(source_row, source_row, local_row)
      if input_tiles == 2:
        with p.brisc.scope():
          first, second = p.brisc.reg(2, exclude=source_row)
          p.brisc.slli(first, source_row, 1)
          p.brisc.addi(second, first, 1)
          p.brisc.noc.read_tiles_into_cb(
            weight, (first, second), weight_cb,
          )
      else:
        for input_tile in range(input_tiles):
          with p.brisc.scope():
            tile, stride = p.brisc.reg(2, exclude=source_row)
            p.brisc.li(stride, input_tiles)
            p.brisc.mul(tile, source_row, stride)
            if input_tile: p.brisc.addi(tile, tile, input_tile)
            p.brisc.noc.read_into_cb(weight, tile, weight_cb)

  for _, _, local_rows in projections:
    for _ in p.trisc0.range(local_rows):
      for input_tile in range(input_tiles):
        p.unpack.move_l1_pair(
          weight_cb, token_l1 + input_tile * token.tile_size,
        )

  accumulate_first = _dot_accumulate(reset=True)
  accumulate_next = _dot_accumulate(reset=False)
  finalize = _dot_finalize()
  for _, _, local_rows in projections:
    for _ in p.trisc1.range(local_rows):
      for input_tile in range(input_tiles):
        p.fpu.binary("mul", dst_tile=0)
        _rms_select_tile(p.sfpu, 0)
        _rms_map_acquired(
          p.sfpu,
          accumulate_first if input_tile == 0 else accumulate_next,
        )
      _rms_select_tile(p.sfpu, 0)
      for word in finalize.words: p.sfpu._issue(word)
      stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
      p.sfpu.publish()

  for _, _, local_rows in projections:
    for _ in p.trisc2.range(local_rows):
      p.pack.move_scalar(scalar_cb, tile=0)

  for target_l1, (_, output, local_rows) in zip(
    compact_l1, projections,
  ):
    p.ncrisc.zero_words(
      target_l1, output.tiles_per_item * output.tile_size // 4,
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
        p.ncrisc.li(target, target_l1)
        p.ncrisc.add(target, target, byte_offset)
        p.ncrisc.write(target, value, bytes=2)
      CB.pop_front(p.ncrisc, scalar_cb)
    for tile in range(output.tiles_per_item):
      with p.ncrisc.scope():
        target_address, target_coordinate = p.ncrisc.noc._dram_tile(
          output, tile,
        )
        p.ncrisc.noc.write(
          target_l1 + tile * output.tile_size,
          target_address, target_coordinate,
          output.tile_size, posted=False,
        )
  return p


def decode_projection(x: Buffer, weight: Buffer, output: Buffer) -> Program:
  """Compute one bias-free HF Linear as ``weight @ x`` over 117 cores.

  Hugging Face stores Linear weights as ``[out_features, in_features]``.
  Each core owns a contiguous set of output rows and computes the complete
  2048- or 8192-element dot product for every row. The compact output has logical shape
  ``[117, max_rows_per_core]``: one tile per core, with padding only in the
  final slot of smaller shards.
  """
  return specialize(
    lambda count: _decode_projections_program(
      x, ((weight, output, count),),
    ),
    weight.cores, weight.item_counts,
  )


def decode_qkv_projection(
  x: Buffer, q_weight: Buffer, k_weight: Buffer, v_weight: Buffer,
  q_output: Buffer, k_output: Buffer, v_output: Buffer,
) -> Program:
  """Fuse decode Q/K/V while preserving their existing per-core layouts."""
  per_core = tuple(zip(
    q_weight.item_counts, k_weight.item_counts, v_weight.item_counts,
  ))
  variants = {
    counts: _decode_projections_program(
      x, (
        (q_weight, q_output, counts[0]),
        (k_weight, k_output, counts[1]),
        (v_weight, v_output, counts[2]),
      ),
    )
    for counts in set(per_core)
  }
  lowered = {
    counts: program.lower() for counts, program in variants.items()
  }
  combined = variants[max(variants)]
  combined._kernels = {
    core: dict(lowered[counts][core])
    for core, counts in zip(q_weight.cores, per_core)
  }
  return combined


# ---------------------------------------------------------------------------
# Vocabulary reduction and device-to-host token publication
# ---------------------------------------------------------------------------

def decode_argmax(
  logits: Buffer, token_history: Buffer, host_output: int,
) -> Program:
  """Reduce logits, publish the winner, and append it to token history."""
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
  host_address = Const("argmax_host_address", host_output)
  p = Program(
    logits.cores, logits, token_history, host_address,
    starts, counts, indices, write_pos, write_token,
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
      l1.load(p.brisc, logits_l1, logical, value, DType.BF16)
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
    with p.brisc.scope():
      target_address, position, offset = p.brisc.reg(3)
      p.brisc.read(target_address, p.param_addr(host_address))
      p.brisc.read(position, p.param_addr(write_pos))
      p.brisc.slli(offset, position, 4)
      p.brisc.add(target_address, target_address, offset)
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
      l1.store(p.brisc, history_l1, within, best_id)
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


# ---------------------------------------------------------------------------
# Residual and MLP layout kernels
# ---------------------------------------------------------------------------

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
      l1.copy_words(
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
  """Reassemble compact 117-core MLP state into global BF16[1,8192]."""
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
  return _compact_feature_location(
    feature, Q_PROJ_DIM if query else KV_PROJ_DIM,
  )


def _compact_slot_byte_offset(slot):
  return slot * 2 if slot < 16 else 512 + (slot - 16) * 2


# ---------------------------------------------------------------------------
# RoPE, KV cache, and grouped-query attention
# ---------------------------------------------------------------------------

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
          l1.copy_words(
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
    tilized=buffer.tilized, dram_endpoints=buffer.dram_endpoints,
  )


def decode_rope(q: Buffer, k: Buffer, v: Buffer, cos: Buffer, sin: Buffer,
                q_output: Buffer, k_output: Buffer,
                v_output: Buffer) -> Program:
  """Apply Q/K RoPE and reassemble V together in one 40-core launch."""
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
        l1.copy_words(
          p.brisc, source, target + target_left, 8,
          source_offset=source_offset,
        )
        l1.copy_words(
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
        l1.copy_words(p.brisc, query_low_l1, low, q.tile_size // 4)
        l1.copy_words(p.brisc, query_high_l1, high, q.tile_size // 4)
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


# ---------------------------------------------------------------------------
# Token embedding and RMSNorm
# ---------------------------------------------------------------------------

def decode_embedding(
  token_id: Buffer, embedding_weight: Buffer, output: Buffer,
) -> Program:
  """Gather one embedding row on one core.

    token_id          U32[1] or U32[8192]   global; `token_pos` selects the row
    embedding_weight  BF16[128256, 2048]    global, 2 tiles per vocabulary row
    output            BF16[1, 2048]         global, 2 tiles

  Logical operation:
    output[0, :] = embedding_weight[token_id[token_pos], :]
  """
  token_pos = Const("token_pos", 0)
  p = Program(
    output.cores, token_id, embedding_weight, output, token_pos,
  )
  ids_l1 = p.l1(token_id.tile_size, alignment=16)
  embedding_cb = p.cb(DType.BF16, depth=EMBEDDING_TILES)
  with p.brisc.scope():
    position, tile, within, token = p.brisc.reg(4)
    p.brisc.read(position, p.param_addr(token_pos))
    p.brisc.srli(tile, position, 10)          # 1024 token IDs per tile
    p.brisc.andi(within, position, 1023)
    p.brisc.noc.read_tile(token_id, tile, ids_l1)
    l1.load(p.brisc, ids_l1, within, token)   # token = token_id[token_pos]
    for row_tile in range(EMBEDDING_TILES):
      with p.brisc.scope():
        # weight tile index = token * EMBEDDING_TILES + row_tile
        source_tile = p.brisc.reg(exclude=token)
        p.brisc.slli(source_tile, token, EMBEDDING_TILES_SHIFT)
        if row_tile: p.brisc.addi(source_tile, source_tile, row_tile)
        p.brisc.noc.read_into_cb(
          embedding_weight, source_tile, embedding_cb,
        )
  p.ncrisc.noc.write_tiles_from_cb(
    embedding_cb, output, tuple(range(EMBEDDING_TILES)),
  )
  return p


def rmsnorm(x: Buffer, weight: Buffer, output: Buffer) -> Program:
  """Normalize one decode token and apply the learned scale."""
  p = Program(x.cores, x, weight, output, fp32_dst=True)
  x_cb = p.cb(DType.BF16, depth=4)
  output_cb = p.cb(DType.BF16, depth=4)
  gamma_l1 = p.l1(EMBEDDING_TILES * weight.tile_size, alignment=16)

  p.brisc.noc.read_tiles(weight, tuple(
    (tile, gamma_l1 + tile * weight.tile_size)
    for tile in range(EMBEDDING_TILES)
  ))
  p.brisc.noc.read_tiles_into_cb(x, (0, 1), x_cb)
  for _ in range(EMBEDDING_TILES):
    p.unpack.move(x_cb, UnpackTarget.SRCA)
  for tile in range(EMBEDDING_TILES):
    p.unpack.move_l1(weight.dtype, gamma_l1 + tile * weight.tile_size)
  _rms_setup_apply_macro(p.sfpu)
  p.fpu.copy_a_tiles(dst_tiles=range(2 * EMBEDDING_TILES))
  _rmsnorm_one_token(p.sfpu)
  p.pack.move_tiles(output_cb, tiles=(0, 1))
  p.ncrisc.noc.write_tiles_from_cb(
    output_cb, output, tuple(range(EMBEDDING_TILES)),
  )
  return p


# ---------------------------------------------------------------------------
# Resident decode runtime and end-to-end driver
# ---------------------------------------------------------------------------

class Llama3Decode:
  """Resident-weight, batch-1 Llama 3.2 1B decode runtime."""

  def __init__(self, safetensor_path="weights/model.safetensors",
               device_index=0):
    self.safetensor_path = str(safetensor_path)
    self.host_result_read_us = 0.0
    self.host_result_reads = 0
    self.profile = {
      "dram_upload_bytes": 0,
      "weight_prepare_s": 0.0,
      "weight_stage_s": 0.0,
      "dram_upload_wall_s": 0.0,
    }
    total_started = time.perf_counter()
    started = time.perf_counter()
    self.device = Device(device_index)
    self.device.init_device()
    self.profile["device_init_s"] = time.perf_counter() - started
    try:
      started = time.perf_counter()
      self._allocate()
      self.profile["allocate_s"] = time.perf_counter() - started
      started = time.perf_counter()
      self._upload_weights()
      self.profile["weight_upload_total_s"] = (
        time.perf_counter() - started
      )
      started = time.perf_counter()
      self._build_programs()
      self.profile["program_build_s"] = time.perf_counter() - started
      self.profile["startup_total_s"] = (
        time.perf_counter() - total_started
      )
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
    self.embedding_weight = global_buffer(
      "e2e_embedding_weight", DType.BF16, (VOCAB_SIZE, EMBED_DIM),
    )
    # The model ties embedding and LM-head weights. This view adds 117-core
    # row-sharding metadata without allocating or uploading a second copy.
    self.lm_weight = Buffer(
      "e2e_lm_weight", self.embedding_weight.addr,
      self.embedding_weight.dtype, self.embedding_weight.shape,
      0, cores, self.embedding_weight.banks, global_address=True,
      tilized=self.embedding_weight.tilized,
      dram_endpoints=self.embedding_weight.dram_endpoints,
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
    started = time.perf_counter()
    data = buffer.from_safetensor(tensor, self.safetensor_path)
    self.profile["weight_prepare_s"] += time.perf_counter() - started
    self._stage_upload(buffer, data)

  def _stage_upload(self, buffer, data):
    started = time.perf_counter()
    self.device.write(buffer, data)
    self.profile["weight_stage_s"] += time.perf_counter() - started
    self.profile["dram_upload_bytes"] += buffer.size

  def _run_uploads(self, timeout):
    started = time.perf_counter()
    result = self.device.run(timeout=timeout)
    self.profile["dram_upload_wall_s"] += time.perf_counter() - started
    return result

  def _upload_weights(self):
    started = time.perf_counter()
    embedding_data = self.embedding_weight.from_safetensor(
      "model.embed_tokens.weight", self.safetensor_path,
    )
    self.profile["weight_prepare_s"] += time.perf_counter() - started
    self._stage_upload(self.embedding_weight, embedding_data)
    self._run_uploads(60.0)
    del embedding_data

    started = time.perf_counter()
    cos_values, sin_values = rope_table()
    cos_data = _bf16_rne_bytes(cos_values)
    sin_data = _bf16_rne_bytes(sin_values)
    self.profile["weight_prepare_s"] += time.perf_counter() - started
    self._stage_upload(self.cos, cos_data)
    self._stage_upload(self.sin, sin_data)
    self._run_uploads(30.0)
    del cos_values, sin_values

    cache_zeros = bytes(
      math.prod(KV_CACHE_STORAGE_SHAPE) * DType.BF16.itemsize,
    )
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
      self._stage_upload(layer["key_cache"], cache_zeros)
      self._stage_upload(layer["value_cache"], cache_zeros)
      self._run_uploads(60.0)
    self._upload(self.final_norm, "model.norm.weight")
    self._run_uploads(30.0)

  def _build_programs(self):
    weights = self.layers[0]["weights"]
    o_projection = decode_projection(
      self.normalized, weights["q"], self.q_compact,
    )
    self.programs = {
      "embedding": decode_embedding(
        self.token_history, self.embedding_weight, self.x_a,
      ),
      "rms": rmsnorm(self.x_a, weights["input_norm"], self.normalized),
      "o": o_projection,
      "qkv": decode_qkv_projection(
        self.normalized,
        weights["q"], weights["k"], weights["v"],
        self.q_compact, self.k_compact, self.v_compact,
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
        self.logits, self.token_history,
        self.device.cq.noc + self.device.cq.live,
      ),
    }
    self.o_projection_input = o_projection.param(
      f"{self.normalized.name}_decode_token",
    )
    self.context_projection_input = Buffer(
      "e2e_context_decode_token", self.context.addr, self.context.dtype,
      (EMBED_DIM,), None, (self.context.cores[0],), self.context.banks,
      global_address=True, dram_endpoints=self.context.dram_endpoints,
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
    self._queue("qkv", (
      (template_weights["q"], weights["q"]),
      (template_weights["k"], weights["k"]),
      (template_weights["v"], weights["v"]),
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
    self._queue("o", (
      (self.o_projection_input, self.context_projection_input),
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
    started = time.perf_counter_ns()
    self.decode_trace.replay({
      "token_pos": position,
      "write_pos": position + 1,
      "write_token": int(append),
      "start_pos": position,
      "kv_blocks": position // KV_CACHE_TOKEN_BLOCK + 1,
      "valid_columns": position % KV_CACHE_TOKEN_BLOCK + 1,
    }, timeout=30.0)
    wall_us = (time.perf_counter_ns() - started) / 1e3

    if not logits: return None, wall_us
    read_started = time.perf_counter_ns()
    live = self.device.cq.live + (position + 1) * 16
    token, = struct.unpack("<I", self.device.pcie.sysmem.read(live, 4))
    self.host_result_read_us += (
      time.perf_counter_ns() - read_started
    ) / 1e3
    self.host_result_reads += 1
    return token, wall_us

  def close(self):
    if getattr(self, "device", None) is not None:
      self.device.close()
      self.device = None


def run_decode_e2e(
  prompt="The capital of France is", steps=None,
  safetensor_path="weights/model.safetensors",
  tokenizer_path="weights",
  profile=False,
  device_index=0,
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

  runtime = Llama3Decode(safetensor_path, device_index)
  generation_seconds = 0.0
  generation_replays = 0
  generation_profiles = []
  generated = []
  stream_us = 0.0
  streamer = TextStreamer(
    tokenizer, skip_prompt=False, skip_special_tokens=True,
    clean_up_tokenization_spaces=False,
  )
  try:
    prompt_started = time.perf_counter()
    runtime.load_tokens(prompt_ids)
    next_token = None
    for position in range(len(prompt_ids)):
      last_prompt_token = position == len(prompt_ids) - 1
      if last_prompt_token: token_started = time.perf_counter_ns()
      read_before = runtime.host_result_read_us
      next_token, replay_wall_us = runtime.decode(
        position, logits=last_prompt_token, append=last_prompt_token,
      )
      if last_prompt_token:
        full_wall_us = (time.perf_counter_ns() - token_started) / 1e3
        generation_seconds += full_wall_us / 1e6
        generation_replays += 1
        generation_profiles.append({
          **runtime.decode_trace.last_profile,
          "replay_wall_us": replay_wall_us,
          "result_read_us": runtime.host_result_read_us - read_before,
          "full_wall_us": full_wall_us,
        })
    prompt_seconds = time.perf_counter() - prompt_started

    for step in range(steps):
      generated.append(next_token)
      stream_started = time.perf_counter_ns()
      streamer.put(np.asarray([next_token], dtype=np.int64))
      stream_us += (time.perf_counter_ns() - stream_started) / 1e3
      if next_token in EOS_TOKEN_IDS or step + 1 == steps: break
      position = len(prompt_ids) + step
      token_started = time.perf_counter_ns()
      read_before = runtime.host_result_read_us
      next_token, replay_wall_us = runtime.decode(
        position, logits=True,
      )
      full_wall_us = (time.perf_counter_ns() - token_started) / 1e3
      generation_seconds += full_wall_us / 1e6
      generation_replays += 1
      generation_profiles.append({
        **runtime.decode_trace.last_profile,
        "replay_wall_us": replay_wall_us,
        "result_read_us": runtime.host_result_read_us - read_before,
        "full_wall_us": full_wall_us,
      })
    streamer.end()
  finally:
    runtime.close()

  print(f"{generation_replays / generation_seconds:.2f} tok/s")
  if profile:
    startup = runtime.profile
    print(
      f"startup total          {startup['startup_total_s'] * 1e3:9.2f} ms"
    )
    print(
      f"  device init          {startup['device_init_s'] * 1e3:9.2f} ms"
    )
    print(
      f"  weight prepare       {startup['weight_prepare_s'] * 1e3:9.2f} ms"
    )
    print(
      f"  host tile/stage      {startup['weight_stage_s'] * 1e3:9.2f} ms"
    )
    upload_gib = startup["dram_upload_bytes"] / (1 << 30)
    upload_s = startup["dram_upload_wall_s"]
    print(
      f"  DRAM upload          {upload_s * 1e3:9.2f} ms  "
      f"({upload_gib:.3f} GiB, {upload_gib / upload_s:.2f} GiB/s)"
    )
    print(
      f"  program build        {startup['program_build_s'] * 1e3:9.2f} ms"
    )
    print(
      f"prompt decode          {prompt_seconds * 1e3:9.2f} ms  "
      f"({len(prompt_ids)} tokens)"
    )
    if generation_profiles:
      def average(name):
        return sum(sample[name] for sample in generation_profiles) / len(
          generation_profiles
        )

      device_us = average("device_us")
      replay_wall_us = average("replay_wall_us")
      full_wall_us = average("full_wall_us")
      print(f"generated-token average ({len(generation_profiles)} replays)")
      print(f"  device/CQ interval   {device_us:9.2f} us")
      print(f"  host replay wall     {replay_wall_us:9.2f} us")
      print(f"  token readback       {average('result_read_us'):9.2f} us")
      print(f"  full decode call     {full_wall_us:9.2f} us")
      print(f"  wall - device        {full_wall_us - device_us:9.2f} us")
      print(
        f"  runtime encode/patch "
        f"{average('runtime_encode_us') + average('runtime_patch_us'):9.2f} us"
      )
      print(
        f"  CQ event/doorbell    "
        f"{average('event_patch_us') + average('queue_slot_wait_us') + average('doorbell_us'):9.2f} us"
      )
      print(
        f"  completion tail      {average('descriptor_drain_us'):9.2f} us"
      )
      print(
        f"  text streaming       {stream_us / max(1, len(generated)):9.2f} us/token"
      )


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--prompt", default="The capital of France is",
    help="generate from this prompt (an empty prompt is valid)",
  )
  parser.add_argument(
    "--steps", type=int,
    help="optional generation cap; default runs until EOS/context limit",
  )
  parser.add_argument("--safetensor", default="weights/model.safetensors")
  parser.add_argument("--tokenizer", default="weights")
  parser.add_argument(
    "--device", type=int, default=0,
    help="Tenstorrent device index (default: 0)",
  )
  parser.add_argument(
    "--profile", action="store_true",
    help="print startup, DRAM-upload, device, and host-loop timing",
  )
  args = parser.parse_args()
  run_decode_e2e(
    args.prompt, args.steps, args.safetensor, args.tokenizer,
    profile=args.profile, device_index=args.device,
  )
