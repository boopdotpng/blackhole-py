"""Llama 3 batch-1 decode and chunked prefill on Blackhole.

One set of kernel builders supports Llama 3.2 1B BF16 and Llama 3 8B
BF16/published FP8. Run ``python -m examples.llama3 --help`` for switches.
"""

from pathlib import Path
from dataclasses import replace
from copy import copy
from examples.rmsnorm_hybrid import emit_rmsnorm, enabled as hybrid_rmsnorm_enabled

import argparse
import math
import os
import numpy as np
import struct
import time

from asm import Cond
from cq import UnicastWrite, mcast_coords, noc_coord
from device import TensorDevice as Device
from firmware.consts import CQConfig, TensixL1, TensixMMIO, KERNEL_ROLES
from pcie import P100_WORKER_CORES, TLBWindow
from program import Buffer, Const, DType, TensorProgram as Program, rectangles
from ttko.isa import R, RV32, Tensix as TT
from ttko import Dst, l1
from ttko.fpu import Fpu
from ttko.pack import Pack
from ttko.cb import CB
from ttko.sfpu import (
  LaneConfig, LReg, SfpuFormat, SfpuProgram, SfpuProgramBuilder,
)
from ttko.shard import specialize
from ttko.mop import LoopTemplate
from ttko.sync import Sem, SemWait, Stall, Wait, sem_get, sem_wait, stall
from ttko.unpack import UnpackTarget


class Llama3Kernels:
  """Shared kernel builders with independent per-model dimensions and formats."""

  VOCAB_SIZE = 128256
  Q_HEADS = 32
  KV_HEADS = 8
  ROPE_CORES = Q_HEADS + KV_HEADS
  ROPE_CACHE_TOKENS = 8192
  ROPE_THETA = 500000.0
  ROPE_LOW_FREQ_FACTOR = 1.0
  ROPE_HIGH_FREQ_FACTOR = 4.0
  ROPE_ORIGINAL_MAX_POSITION_EMBEDDINGS = 8192
  KV_CACHE_TOKEN_BLOCK = 32
  KV_CACHE_TIME_BLOCKS = ROPE_CACHE_TOKENS // KV_CACHE_TOKEN_BLOCK
  GQA_GROUP_SIZE = Q_HEADS // KV_HEADS
  GQA_ROW_CHUNKS = (0, 2, 16, 18)
  ACTIVATION_DTYPE = DType.FP8

  def __init__(self, model="1b", dtype="bf16", *, projection_cores=None,
               attention_dtype=None, fp8_fidelity=None, noc_split_x=None):
    if projection_cores is None and model == "8b":
      value = os.environ.get("LLAMA_PROJECTION_CORES")
      projection_cores = None if value is None else int(value)
    if attention_dtype is None:
      attention_dtype = os.environ.get("LLAMA_ATTENTION_DTYPE", "bf16") if dtype == "fp8" else "bf16"
    if fp8_fidelity is None:
      fp8_fidelity = int(os.environ.get("LLAMA_FP8_FIDELITY", "1")) if dtype == "fp8" else 1
    if noc_split_x is None and dtype == "fp8":
      value = os.environ.get("LLAMA_NOC_SPLIT_X")
      noc_split_x = None if value is None else int(value)
    if model not in ("1b", "8b"): raise ValueError("model must be 1b or 8b")
    if dtype not in ("bf16", "fp8"): raise ValueError("dtype must be bf16 or fp8")
    if model == "1b" and dtype == "fp8": raise ValueError("FP8 requires the published 8B checkpoint")
    if attention_dtype not in ("bf16", "fp8"): raise ValueError("attention dtype must be bf16 or fp8")
    if dtype != "fp8" and attention_dtype == "fp8": raise ValueError("FP8 attention requires FP8 mode")
    if fp8_fidelity not in (1, 2): raise ValueError("FP8 fidelity must be 1 or 2")
    self.model, self.dtype = model, dtype
    self.EMBED_DIM = 2048 if model == "1b" else 4096
    self.EMBEDDING_TILES = self.EMBED_DIM // 1024
    self.EMBEDDING_TILES_SHIFT = self.EMBEDDING_TILES.bit_length() - 1
    self.LLAMA_LAYERS = 16 if model == "1b" else 32
    self.HEAD_DIM = 64 if model == "1b" else 128
    self.Q_PROJ_DIM = self.EMBED_DIM
    self.KV_PROJ_DIM = self.KV_HEADS * self.HEAD_DIM
    self.MLP_DIM = 8192 if model == "1b" else 14336
    self.ROPE_FACTOR = 32.0 if model == "1b" else 1.0
    self.EOS_TOKEN_IDS = frozenset((128001, 128008, 128009) if model == "1b" else (128001, 128009))
    self.KV_CACHE_FEATURE_TILES = self.HEAD_DIM // 32
    self.KV_CACHE_TILES_PER_HEAD = self.KV_CACHE_TIME_BLOCKS * self.KV_CACHE_FEATURE_TILES
    self.KV_CACHE_STORAGE_SHAPE = (self.KV_HEADS, self.KV_CACHE_TILES_PER_HEAD, 1024)
    self.GQA_CONTEXT_SHAPE = (1, self.EMBED_DIM)
    self.LLAMA_CORES = (117 if model == "1b" else 96 if dtype == "fp8" else 88) if projection_cores is None else projection_cores
    if self.LLAMA_CORES not in (80, 88, 96, 104, 112, 117):
      raise ValueError("projection cores must be 80, 88, 96, 104, 112, or 117")
    self.PROJECTION_NOC_SPLIT_X = (10 if dtype == "fp8" else 7) if noc_split_x is None else noc_split_x
    self.WEIGHT_DTYPE = DType.FP8 if dtype == "fp8" else DType.BF16
    self.ATTENTION_DTYPE = DType.FP8 if attention_dtype == "fp8" else DType.BF16
    self.FP8_FIDELITY = fp8_fidelity
    self.attention_cores = 16 if model == "1b" else 32
    self.checkpoint = "weights/llama3-1b" if model == "1b" else f"weights/llama3-8b-{dtype}"

  # Host tables and shared code-generation helpers

  def rope_table(self,
    max_seq_len=ROPE_CACHE_TOKENS, head_dim=None,
    rope_theta=ROPE_THETA, rope_factor=None,
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
    head_dim = self.HEAD_DIM if head_dim is None else head_dim
    rope_factor = self.ROPE_FACTOR if rope_factor is None else rope_factor
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


  def _bf16_rne_bytes(self, values):
    """Cast finite FP32 values to BF16 with round-to-nearest-even."""
    words = np.ascontiguousarray(values, dtype="<f4").view(np.uint32)
    rounded = words + np.uint32(0x7fff) + ((words >> 16) & np.uint32(1))
    return (rounded >> 16).astype("<u2").tobytes()


  def _token_counts(self, items, cores):
    per_core, extra = divmod(items, cores)
    return tuple(per_core + (index < extra) for index in range(cores))


  def _sfpu_float_words(self, register, value):
    bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
    return (
      TT.TTSFPLOADI(register, 10, bits & 0xffff),
      TT.TTSFPLOADI(register, 8, bits >> 16),
    )


  def _sfpu_add(self, words, left, right, output):
    words.extend((TT.TTSFPADD(LReg.ONE, left, right, output, 0), TT.TTSFPNOP()))


  def _sfpu_mul(self, words, left, right, output, modifier=0):
    words.extend((TT.TTSFPMUL(left, right, LReg.ZERO, output, modifier), TT.TTSFPNOP()))


  def _rms_square_accumulate(self, *, reset):
    # BF16 immediate zero expands to FP32 +0 in every enabled lane.
    setup = (TT.TTSFPLOADI(LReg.L0, 0, 0),) if reset else ()
    return SfpuProgram(tuple(setup), (
      TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, 0),
      TT.TTSFPMAD(LReg.L1, LReg.L1, LReg.L0, LReg.L0, 0),
    ))


  def _rms_finalize_scale(self):
    """Reduce the 32 accumulator lanes in L0 and leave reciprocal RMS there."""
    words = []
    # Butterfly-reduce each independent eight-lane SFPU row. Cyclic rotations
    # make the final sum a broadcast, which the transpose below needs.
    for rotations in (4, 2, 1):
      words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
      for _ in range(rotations):
        words.extend((
          TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
        ))
      self._sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
    # Copy the four eight-lane row sums, then transpose the four identical
    # registers. L0..L3 become broadcasts of rows 0..3 respectively.
    for register in (LReg.L1, LReg.L2, LReg.L3):
      words.append(TT.TTSFPMOV(0, LReg.L0, register, 0))
    words.append(TT.TTSFPTRANSP(0, 0, 0, 0))
    for register in (LReg.L1, LReg.L2, LReg.L3):
      self._sfpu_add(words, LReg.L0, register, LReg.L0)

    words.extend(self._sfpu_float_words(LReg.L4, 1.0 / self.EMBED_DIM))
    words.append(TT.TTSFPMUL(LReg.L0, LReg.L4, LReg.ZERO, LReg.L0, 0))
    words.extend(self._sfpu_float_words(LReg.L4, 1e-5))
    self._sfpu_add(words, LReg.L0, LReg.L4, LReg.L0)

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
    self._sfpu_mul(words, x, y, temporary)
    words.append(TT.TTSFPMUL(y, temporary, LReg.ZERO, temporary, 1))
    words.extend(self._sfpu_float_words(c1, 2.2825186))
    words.extend(self._sfpu_float_words(c2, 2.2533049))
    self._sfpu_add(words, c2, temporary, c2)
    words.extend((TT.TTSFPMAD(temporary, c2, c1, temporary, 0), TT.TTSFPNOP()))
    self._sfpu_mul(words, y, temporary, y)
    self._sfpu_mul(words, x, y, temporary)
    self._sfpu_mul(words, y, temporary, temporary, 1)
    words.append(TT.TTSFPADD(
      LReg.ONE, LReg.ONE, temporary, temporary, 0,
    ))
    words.extend(self._sfpu_float_words(half, 0.5))
    self._sfpu_mul(words, y, half, half)
    words.append(TT.TTSFPMAD(temporary, half, y, LReg.L0, 0))
    return SfpuProgram((), tuple(words))


  def _rms_apply_weight_pair(self):
    """Apply RMS scale and gamma to two independent 32-lane footprints."""
    return SfpuProgram((), (
      TT.TTSFPLOADMACRO(LReg.L1, SfpuFormat.DEFAULT, 7, 0),
      TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, self.EMBEDDING_TILES * 64),
      TT.TTSFPLOADMACRO(LReg.L3, SfpuFormat.DEFAULT, 7, 2),
      TT.TTSFPLOAD(LReg.L4, SfpuFormat.FP32, 7, self.EMBEDDING_TILES * 64 + 2),
      TT.TTSFPMUL(LReg.L1, LReg.L2, LReg.ZERO, LReg.L1, 0),
      TT.TTSFPMUL(LReg.L3, LReg.L4, LReg.ZERO, LReg.L3, 0),
      TT.TTSFPSTORE(LReg.L1, SfpuFormat.FP32, 7, 0),
      TT.TTSFPSTORE(LReg.L3, SfpuFormat.FP32, 7, 2),
      TT.TTINCRWC(0, 2, 0, 0),
    ))


  def _rms_setup_apply_macro(self, sfpu):
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


  def _rms_map_acquired(self, sfpu, program, *, iterations=8):
    start, body = sfpu._prepare(program)
    for word in program.setup_words: sfpu._issue(word)
    if start is not None:
      sfpu._configure_replay_mop(start, len(body), iterations)
    sfpu._run_faces(start, body, 4, iterations)
    sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
    stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


  def _rms_select_tile(self, sfpu, tile):
    sfpu._configure_dst(tile, LaneConfig())
    stall(sfpu.k, Stall.SFPU, Wait.MATH)


  def _rmsnorm_one_token(self, sfpu, *, fp8=False, scale=None):
    """Normalize the token tiles and apply gamma, all in FP32."""
    sem_wait(
      sfpu.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
      Stall.SYNC | Stall.MATH | Stall.SFPU,
    )
    for tile in range(self.EMBEDDING_TILES):
      self._rms_select_tile(sfpu, tile)
      self._rms_map_acquired(sfpu, self._rms_square_accumulate(reset=tile == 0))
    for word in self._rms_finalize_scale().words: sfpu._issue(word)
    stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)

    apply = self._rms_apply_weight_pair()
    for tile in range(self.EMBEDDING_TILES):
      self._rms_select_tile(sfpu, tile)
      self._rms_map_acquired(sfpu, apply, iterations=4)
    if scale is not None: scale()
    if fp8:
      for tile in range(self.EMBEDDING_TILES): sfpu.map(self._round_fp8_program(), tile=tile)
    sfpu.publish()


  def _round_fp8_program(self, dtype=None):
    """Round FP32 mantissas to E4M3 before the truncating hardware packer."""
    dtype = self.ACTIVATION_DTYPE if dtype is None else dtype
    shift = 20
    maximum = 0x43e00000
    setup = []
    for reg, bits in ((LReg.L1, (1 << (shift - 1)) - 1), (LReg.L2, 1), (LReg.L3, (0xffffffff << shift) & 0xffffffff),
                      (LReg.L5, maximum), (LReg.L6, maximum | 0x80000000)):
      setup.extend((TT.TTSFPLOADI(reg, 10, bits & 0xffff), TT.TTSFPLOADI(reg, 8, bits >> 16)))
    return SfpuProgram(tuple(setup), (
      TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0),
      TT.TTSFPMOV(0, LReg.L0, LReg.L4, 0),
      TT.TTSFPSHFT((-shift) & 0xfff, 0, LReg.L4, 1),
      TT.TTSFPAND(0, LReg.L2, LReg.L4, 0),
      TT.TTSFPIADD(0, LReg.L1, LReg.L4, 4),
      TT.TTSFPIADD(0, LReg.L4, LReg.L0, 4),
      TT.TTSFPAND(0, LReg.L3, LReg.L0, 0),
      TT.TTSFPMOV(0, LReg.L5, LReg.L7, 0),
      TT.TTSFPSWAP(0, LReg.L7, LReg.L0, 1), TT.TTSFPNOP(),
      TT.TTSFPMOV(0, LReg.L6, LReg.L7, 0),
      TT.TTSFPSWAP(0, LReg.L0, LReg.L7, 1), TT.TTSFPNOP(),
      # Explicitly flush subnormals: the native unpacker is not IEEE there.
      TT.TTSFPABS(0, LReg.L0, LReg.L4, 1),
      TT.TTSFPLOADI(LReg.L7, 10, 0), TT.TTSFPLOADI(LReg.L7, 8, 0x3c80),
      TT.TTSFPIADD(0, LReg.L4, LReg.L7, 6),
      TT.TTSFPSHFT((-31) & 0xfff, 0, LReg.L7, 1),
      TT.TTSFPIADD(0xfff, LReg.L7, LReg.L7, 5),
      TT.TTSFPAND(0, LReg.L7, LReg.L0, 0),
      TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0),
    ))


  def _dot_accumulate(self, *, reset):
    """Accumulate one FP32 product tile into the persistent SFPU L7 lanes."""
    setup = self._sfpu_float_words(LReg.L7, 0.0) if reset else ()
    return SfpuProgram(tuple(setup), (
      TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0),
      TT.TTSFPMAD(LReg.L0, LReg.ONE, LReg.L7, LReg.L7, 0),
    ))


  def _dot_finalize(self):
    """Reduce the 32 SFPU accumulator lanes and store one scalar in Dst 0."""
    words = [TT.TTSFPMOV(0, LReg.L7, LReg.L0, 0)]
    for rotations in (4, 2, 1):
      words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
      for _ in range(rotations):
        words.extend((
          TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
        ))
      self._sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
    for register in (LReg.L1, LReg.L2, LReg.L3):
      words.append(TT.TTSFPMOV(0, LReg.L0, register, 0))
    words.append(TT.TTSFPTRANSP(0, 0, 0, 0))
    for register in (LReg.L1, LReg.L2, LReg.L3):
      self._sfpu_add(words, LReg.L0, register, LReg.L0)
    words.extend((
      TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0),
      TT.TTSFPNOP(),
    ))
    return SfpuProgram((), tuple(words))


  # Linear projections: generic GEMV and fused Q/K/V

  def _projection_read_weights(self, p, projections, row_starts, rotations, read_noc, weight_cb, input_tiles):
    for (weight, _, local_rows), row_start, rotation in zip(
      projections, row_starts, rotations,
    ):
      if rotation is None:
        for local_row in p.brisc.range(local_rows):
          source_row = local_row
          if row_start is not None:
            source_row = p.brisc.reg(exclude=local_row)
            p.brisc.read(source_row, p.param_addr(row_start))
            p.brisc.add(source_row, source_row, local_row)
          with p.brisc.scope():
            first, scale = p.brisc.reg(2, exclude=source_row)
            p.brisc.li(scale, input_tiles)
            p.brisc.mul(first, source_row, scale)
            # One tile at a time bounds register use for the 14-tile MLP input.
            for index in range(input_tiles):
              with p.brisc.scope():
                tile = p.brisc.reg(exclude=first)
                p.brisc.addi(tile, first, index)
                p.brisc.noc_at(read_noc).read_tiles_into_cb(weight, (tile,), weight_cb)
      else:
        # Consecutive rows repeat their bank pattern after this many rows.
        # Unroll one period so every request's bank is a compile-time constant;
        # only its address within that bank advances at runtime.
        noc = p.brisc.noc_at(read_noc)
        period = weight.banks // math.gcd(input_tiles, weight.banks)
        with p.brisc.scope():
          base = p.brisc.reg()
          p.brisc.read(base, p.param_addr(weight))
          p.brisc.andi(base, base, -8)
          if row_start is not None:
            with p.brisc.scope():
              start, divisor = p.brisc.reg(2, exclude=base)
              p.brisc.read(start, p.param_addr(row_start))
              p.brisc.li(divisor, input_tiles)
              p.brisc.mul(start, start, divisor)
              p.brisc.li(divisor, weight.banks)
              p.brisc.divu(start, start, divisor)
              p.brisc.slli(start, start, weight.tile_size.bit_length() - 1)
              p.brisc.add(base, base, start)

          def read_row(row, group):
            CB.reserve_back(p.brisc, weight_cb, input_tiles)
            with noc.transaction() as transaction:
              for index in range(input_tiles):
                offset = rotation + row * input_tiles + index
                with p.brisc.scope():
                  address, target, delta = p.brisc.reg(
                    3, exclude=(base, group) if isinstance(group, R) else base,
                  )
                  if isinstance(group, R):
                    p.brisc.li(
                      delta, period * input_tiles // weight.banks * weight.tile_size,
                    )
                    p.brisc.mul(address, group, delta)
                    p.brisc.add(address, address, base)
                  else:
                    p.brisc.mv(address, base)
                  p.brisc.li(delta, (offset // weight.banks) * weight.tile_size)
                  p.brisc.add(address, address, delta)
                  CB.get_write_ptr(p.brisc, weight_cb, target)
                  if index:
                    p.brisc.li(delta, index * weight.tile_size)
                    p.brisc.add(target, target, delta)
                  coordinate = noc.coordinate(
                    *weight.dram_endpoints[offset % weight.banks][read_noc],
                  )
                  transaction.read(address, coordinate, target, weight.tile_size)
            CB.push_back(p.brisc, weight_cb, input_tiles)

          for group in p.brisc.range(local_rows // period):
            for row in range(period): read_row(row, group)
          for row in range(local_rows // period * period, local_rows):
            read_row(row, None)


  def _scale_constants(self, name, value):
    return tuple(Const(f"{name}_{part}", word) for part, word in enumerate(self._sfpu_float_words(LReg.L6, value)))


  def _load_scale(self, p, name):
    # Parameter words are complete SFPLOADI instructions: no CPU float work per token.
    stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
    with p.trisc1.scope():
      word = p.trisc1.reg()
      for part in range(2):
        p.trisc1.read(word, p.param_addr(p.param(f"{name}_{part}")))
        p.trisc1.write(TensixMMIO.INSTRN_BUF_BASE, word)


  def _scale_input(self, p, tiles):
    self._load_scale(p, "input_scale")
    words = [TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0)]
    self._sfpu_mul(words, LReg.L0, LReg.L6, LReg.L0)
    words.append(TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0))
    for tile in tiles: p.sfpu.map(SfpuProgram((), tuple(words)), tile=tile)


  def _projection_dot_math(self, p, projections, input_tiles):
    # The FPU and SFPU operate on the same Dst tile throughout this kernel.
    # Keep the multiply MOP resident; issue SFPU replay directly so the two
    # engines do not rewrite their shared MOP configuration for every tile.
    fpu, sfpu = p.fpu, p.sfpu
    fpu._configure_dst(0)
    sfpu._configure_dst(0, LaneConfig())
    fpu._set_addr_mod(0, srca=8, srcb=8, dest=8)
    fpu._set_addr_mod(1)
    fpu._set_addr_mod(2, srca_clear=True, srcb_clear=True,
                      dest_carry=True, fidelity_increment=1)
    fpu._set_addr_mod(3, srca_clear=True, srcb_clear=True, dest=8,
                      dest_carry_to_carry=True, fidelity_clear=True)
    fpu._mop.configure(LoopTemplate(
      outer=self.FP8_FIDELITY if projections[0][0].dtype is DType.FP8 else 2, inner=2, loop=TT.TTELWMUL(0, 0, 0, 0, 0),
      last=TT.TTELWMUL(3, 0, 0, 3, 0),
      outer_last=TT.TTELWMUL(0, 0, 0, 2, 0),
    ))
    accumulate = self._dot_accumulate(reset=False)
    replay_start, replay_body = sfpu._prepare(accumulate)
    assert replay_start is not None
    finalize = self._dot_finalize()
    for projection_index, (_, _, local_rows) in enumerate(projections):
      for _ in p.trisc1.range(local_rows):
        fpu._wait_for_dst()
        for word in self._sfpu_float_words(LReg.L7, 0.0): sfpu._issue(word)
        for input_tile in range(input_tiles):
          for face in range(4):
            fpu._issue(TT.TTZEROACC(1, 1, 0, 1, face))
          fpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
          stall(p.trisc1, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
          for _ in range(4): fpu._mop.run()
          fpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
          stall(p.trisc1, Stall.SFPU, Wait.MATH)
          for _ in range(4):
            for _ in range(8):
              sfpu._issue(TT.TTREPLAY(replay_start, len(replay_body), 0, 0))
            sfpu._issue(TT.TTSETRWC(0, 4, 8, 0, 0, 4))
            sfpu._issue(TT.TTSETRWC(0, 4, 8, 0, 0, 4))
          sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
          stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
        for word in finalize.words[:-2]: sfpu._issue(word)
        if projections[0][0].dtype.is_fp8:
          self._load_scale(p, f"output_scale_{projection_index}")
          words = []
          self._sfpu_mul(words, LReg.L0, LReg.L6, LReg.L0)
          for word in words: sfpu._issue(word)
        for word in finalize.words[-2:]: sfpu._issue(word)
        sfpu.publish()


  def _decode_projections_program(self,
    x, projections, read_noc, rotations, *, swiglu_output=None,
    residual=None, dense_output=None, norm_weight=None, eth_output=None,
  ):
    """GEMV with optional local RMSNorm and SwiGLU/residual epilogues."""
    dense_output = swiglu_output if swiglu_output is not None else dense_output
    if any(weight.tilized != x.tilized for weight, _, _ in projections):
      raise ValueError("projection weights and activation must have the same element order")
    if norm_weight is not None and norm_weight.tilized != x.tilized:
      raise ValueError("projection norm and activation must have the same element order")
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
      tilized=x.tilized, dram_endpoints=x.dram_endpoints,
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
      projections[0][0].cores, token, *parameters,
      *(self._scale_constants("input_scale", 1.) if projections[0][0].dtype.is_fp8 else ()),
      *(param for i in range(len(projections)) for param in (self._scale_constants(f"output_scale_{i}", 1/256) if projections[0][0].dtype.is_fp8 else ())),
      *((dense_output, Const("dense_start", projections[0][0].item_starts))
        if dense_output is not None else ()),
      *((residual,) if residual is not None else ()),
      *((norm_weight,) if norm_weight is not None else ()),
      *((Const("collective_base", 0), Const("collective_offset", 1),
         Const("tp_worker_index", tuple(range(len(projections[0][0].cores)))))
        if eth_output is not None else ()), fp32_dst=True,
    )
    weight_cb = p.cb(projections[0][0].dtype, depth=2 * input_tiles)
    scalar_dtype = projections[0][1].dtype
    scalar_cb = p.cb(scalar_dtype, depth=2)
    operand_dtype = self.ACTIVATION_DTYPE if weight_cb.dtype.is_fp8 else DType.BF16
    convert_input = operand_dtype.is_fp8 and not token.dtype.is_fp8
    normalized_cb = p.cb(operand_dtype, depth=input_tiles) if norm_weight is not None or convert_input else None
    token_l1 = normalized_cb.addr if normalized_cb is not None else p.l1(
      input_tiles * token.tile_size, alignment=16)
    compact_cbs = tuple(
      p.cb(output.dtype, depth=output.tiles_per_item) for _, output, _ in projections
    )
    compact_l1 = tuple(cb.addr for cb in compact_cbs)

    if norm_weight is None and convert_input:
      incoming = p.cb(token.dtype, depth=2)
      for tile in range(input_tiles):
        p.brisc.noc_at(read_noc).read_tiles_into_cb(token, (tile,), incoming)
      for _ in p.trisc0.range(input_tiles): p.unpack.move(incoming, UnpackTarget.SRCA)
      for _ in p.trisc1.range(input_tiles):
        p.fpu.copy_a_tiles(dst_tiles=(0,))
        self._scale_input(p, (0,))
        p.sfpu.map(self._round_fp8_program(), tile=0).publish()
      for _ in p.trisc2.range(input_tiles): p.pack.move(normalized_cb, tile=0)
      CB.wait_front(p.brisc, normalized_cb, input_tiles)
    elif norm_weight is None:
      p.brisc.noc_at(read_noc).read_tiles(token, tuple(
        (tile, token_l1 + tile * token.tile_size)
        for tile in range(input_tiles)
      ))
    else:
      if input_dim != self.EMBED_DIM: raise ValueError(f"fused RMSNorm requires a {self.EMBED_DIM}-element token")
      if not operand_dtype.is_fp8 and hybrid_rmsnorm_enabled():
        emit_rmsnorm(p, token, norm_weight, normalized_cb,
                     tiles=self.EMBEDDING_TILES, finalize=self._rms_finalize_scale(), read_noc=read_noc)
      else:
        operands = p.cb(DType.BF16, depth=2 * self.EMBEDDING_TILES)
        for buffer in (token, norm_weight):
          p.brisc.noc_at(read_noc).read_tiles_into_cb(buffer, tuple(range(self.EMBEDDING_TILES)), operands)
        for _ in range(2 * self.EMBEDDING_TILES): p.unpack.move(operands, UnpackTarget.SRCA)
        self._rms_setup_apply_macro(p.sfpu)
        p.fpu.copy_a_tiles(dst_tiles=range(2 * self.EMBEDDING_TILES))
        self._rmsnorm_one_token(p.sfpu, fp8=operand_dtype.is_fp8,
                           scale=(lambda: self._scale_input(p, range(self.EMBEDDING_TILES))) if operand_dtype.is_fp8 else None)
        p.pack.move_tiles(normalized_cb, tiles=tuple(range(self.EMBEDDING_TILES)))
      # Keep the rounded BF16 token in local L1 for all projection rows.
      CB.wait_front(p.brisc, normalized_cb, self.EMBEDDING_TILES)
    if residual is not None:
      residual_l1 = p.l1(residual.tiles * residual.tile_size, alignment=16)
      p.brisc.noc_at(read_noc).read_tiles(residual, tuple(
        (tile, residual_l1 + tile * residual.tile_size) for tile in range(residual.tiles)
      ))
    self._projection_read_weights(p, projections, row_starts, rotations, read_noc, weight_cb, input_tiles)

    p.unpack.prepare_l1_pair_formats(weight_cb.dtype, operand_dtype)
    for _, _, local_rows in projections:
      for _ in p.trisc0.range(local_rows):
        for input_tile in range(input_tiles):
          p.unpack.move_l1_pair(
            weight_cb, token_l1 + input_tile * (1024 * operand_dtype.itemsize),
            configure_format=False, source_b_dtype=operand_dtype,
          )

    self._projection_dot_math(p, projections, input_tiles)

    p.pack._configure(scalar_cb, True, True)
    for _, _, local_rows in projections:
      for _ in p.trisc2.range(local_rows):
        sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
        p.pack._move_acquired(scalar_cb, 0, True, configure=False)
        p.pack._release_dst()

    for target_l1, (_, output, local_rows) in zip(
      compact_l1, projections,
    ):
      self._zero_l1_words(p.ncrisc, target_l1, output.tiles_per_item * output.tile_size // 4)
      for local_row in p.ncrisc.range(local_rows):
        CB.wait_front(p.ncrisc, scalar_cb)
        with p.ncrisc.scope():
          source, value, byte_offset, target = p.ncrisc.reg(4, exclude=local_row)
          CB.get_read_ptr(p.ncrisc, scalar_cb, source)
          p.ncrisc.read(value, source, bytes=scalar_dtype.itemsize)
          self._tile_offset(p.ncrisc, local_row, byte_offset, scalar_dtype)
          p.ncrisc.li(target, target_l1)
          p.ncrisc.add(target, target, byte_offset)
          p.ncrisc.write(target, value, bytes=scalar_dtype.itemsize)
        CB.pop_front(p.ncrisc, scalar_cb)
      if dense_output is not None:
        CB.push_back(p.ncrisc, compact_cbs[compact_l1.index(target_l1)])
        continue
      for tile in range(output.tiles_per_item):
        with p.ncrisc.scope():
          target_address, target_coordinate = p.ncrisc.noc_at(1-read_noc)._dram_tile(
            output, tile,
          )
          p.ncrisc.noc_at(1-read_noc).write(
            target_l1 + tile * output.tile_size,
            target_address, target_coordinate,
            output.tile_size, posted=False,
          )
    if swiglu_output is not None:
      output_cb = p.cb(swiglu_output.dtype, depth=1)
      for cb in compact_cbs: p.unpack.move(cb, UnpackTarget.SRCA)
      self._swiglu_math(p, fp8=swiglu_output.dtype.is_fp8)
      p.pack.move(output_cb, tile=0)
      self._scatter_dense(p, output_cb, swiglu_output, projections[0][2], read_noc=1-read_noc)
    elif residual is not None:
      residual_cb = p.cb(DType.BF16, depth=1)
      output_cb = p.cb(DType.BF16, depth=1)
      # The reader finishes residual DMA before delivering any projection row.
      # Consuming all scalar rows above makes that L1 data safe to gather here.
      with p.ncrisc.scope():
        start = p.ncrisc.reg()
        p.ncrisc.read(start, p.param_addr(p.param("dense_start")))
        for index in p.ncrisc.range(projections[0][2]):
          with p.ncrisc.scope():
            feature, src, dst, value = p.ncrisc.reg(4, exclude=(start, index))
            p.ncrisc.add(feature, start, index)
            self._dense_offset(p.ncrisc, residual, feature, src)
            self._add_constant(p.ncrisc, src, residual_l1)
            p.ncrisc.read(value, src, bytes=2)
            self._tile_offset(p.ncrisc, index, dst)
            self._add_constant(p.ncrisc, dst, residual_cb.addr)
            p.ncrisc.write(dst, value, bytes=2)
      CB.push_back(p.ncrisc, residual_cb)
      p.unpack.move_pair(compact_cbs[0], residual_cb)
      # Match the original residual kernel's BF16 destination arithmetic.
      Fpu(p.trisc1, Dst(False)).binary("add", dst_tile=0).publish()
      Pack(p.trisc2, Dst(False)).move(output_cb, tile=0)
      self._scatter_dense(p, output_cb, dense_output, projections[0][2], read_noc=1-read_noc)
    elif dense_output is not None:
      self._scatter_dense(p, compact_cbs[0], dense_output, projections[0][2], read_noc=1-read_noc, eth_output=eth_output)
    return p


  def _decode_fused_projections(self,
    x, projections, *, swiglu_output=None, residual=None,
    dense_output=None, norm_weight=None, eth_output=None,
  ):
    """Specialize row counts, bank rotations, and read NoC for each core."""
    weights = tuple(weight for weight, _ in projections)
    # Split traffic spatially across the two NoCs. The writer uses the other
    # NIU so its transaction IDs cannot collide with the reader's IDs. On the
    # seven-bank topology retain the compact generic reader: unrolling its
    # longer bank period would overflow the resident kernel arena.
    keys = tuple(
      (tuple(weight.item_counts[index] for weight in weights),
       int(core[0] >= self.PROJECTION_NOC_SPLIT_X),
       tuple(((weight.item_starts[index] * weight.tiles_per_item)
              if weight.global_address else weight.tile_starts[index]) % weight.banks
             if weight.banks == 8 else None for weight in weights))
      for index, core in enumerate(weights[0].cores)
    )
    return specialize(
      lambda key: self._decode_projections_program(
        x, tuple((weight, output, count)
                 for (weight, output), count in zip(projections, key[0])),
        key[1], key[2], swiglu_output=swiglu_output,
        residual=residual, dense_output=dense_output, norm_weight=norm_weight, eth_output=eth_output,
      ),
      weights[0].cores, keys,
    )


  def decode_projection(self, x: Buffer, weight: Buffer, output: Buffer) -> Program:
    """Compute BF16 weight @ x into compact per-core scalar slots."""
    return self._decode_fused_projections(x, ((weight, output),))


  def decode_qkv_projection(self,
    x: Buffer, q_weight: Buffer, k_weight: Buffer, v_weight: Buffer,
    q_output: Buffer, k_output: Buffer, v_output: Buffer,
  ) -> Program:
    """Fuse decode Q/K/V while preserving their existing per-core layouts."""
    return self._decode_fused_projections(x, (
      (q_weight, q_output), (k_weight, k_output), (v_weight, v_output),
    ))


  def decode_argmax(self,
    logits: Buffer, token_history: Buffer, host_output: int,
  ) -> Program:
    """Reduce logits, publish the winner, and append it to token history."""
    local_counts = self._token_counts(self.VOCAB_SIZE, len(logits.cores))
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
        p.brisc.slli(within, within, 2)
        self._add_constant(p.brisc, within, history_l1)
        p.brisc.write(within, best_id)
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


  def _decode_projection_residual_program(self,
    cores, compact, residual, output, *, head,
  ):
    """Gather one compact 128-value slice, add residual, and scatter it dense."""
    p = Program(cores, compact, residual, output)
    projection_cb = p.cb(DType.BF16, depth=1)
    residual_cb = p.cb(DType.BF16, depth=1)
    result = p.cb(DType.BF16, depth=1)
    feature_locations = tuple(
      self._compact_projection_location(head * self.HEAD_DIM + index, query=True)
      for index in range(self.HEAD_DIM)
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
          residual, head // (1024 // self.HEAD_DIM),
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
          self._compact_slot_byte_offset(slot)
        )
        p.brisc.read(value, source, bytes=2)
        p.brisc.write(
          projection_cb.addr + self._bf16_tile_byte_offset(index), value, bytes=2,
        )

    # Operand 1 contains the matching two rows of the dense residual tile.
    first_residual_row = self.KV_CACHE_FEATURE_TILES * (head % (1024 // self.HEAD_DIM))
    for feature_half in range(self.KV_CACHE_FEATURE_TILES):
      source_row = first_residual_row + feature_half
      target_row = feature_half
      for face in range(2):
        l1.copy_words(
          p.brisc,
          residual_l1 + self._dense_byte_offset(residual, source_row * 32 + face * 16),
          residual_cb.addr +
          self._bf16_tile_byte_offset(target_row * 32 + face * 16),
          8,
        )
    CB.push_back(p.brisc, projection_cb)
    CB.push_back(p.brisc, residual_cb)

    p.unpack.move_pair(projection_cb, residual_cb)
    p.fpu.binary("add", dst_tile=0).publish()
    p.pack.move(result, tile=0)

    # Scatter the two 32-feature result rows into the dense [1, 4096] output.
    CB.wait_front(p.ncrisc, result)
    with p.ncrisc.scope():
      source = p.ncrisc.reg()
      CB.get_read_ptr(p.ncrisc, result, source)
      target_address, target_coordinate = p.ncrisc.noc._dram_tile(
        output, head // (1024 // self.HEAD_DIM),
      )
      with p.ncrisc.noc.transaction() as transaction:
        for feature_half in range(self.KV_CACHE_FEATURE_TILES):
          target_row = self.KV_CACHE_FEATURE_TILES * (head % (1024 // self.HEAD_DIM)) + feature_half
          for face in range(2):
            with p.ncrisc.scope():
              source_segment, target_segment = p.ncrisc.reg(
                2, exclude=(source, target_address),
              )
              p.ncrisc.mv(source_segment, source)
              source_offset = self._bf16_tile_byte_offset(
                feature_half * 32 + face * 16,
              )
              if source_offset:
                p.ncrisc.addi(source_segment, source_segment, source_offset)
              p.ncrisc.mv(target_segment, target_address)
              target_offset = self._dense_byte_offset(
                output, target_row * 32 + face * 16,
              )
              if target_offset:
                p.ncrisc.addi(target_segment, target_segment, target_offset)
              transaction.write(
                source_segment, target_segment, target_coordinate, 32,
                posted=False,
              )
    CB.pop_front(p.ncrisc, result)
    return p


  def decode_projection_residual(self,
    compact: Buffer, residual: Buffer, output: Buffer,
  ) -> Program:
    """Reassemble a 4096-row decode projection and fuse its residual add."""
    cores = compact.cores[:self.Q_HEADS]
    compact_tiles = self._global_tile_view(
      compact, "projection_residual_compact_tiles",
    )
    variants = tuple(
      self._decode_projection_residual_program(
        cores, compact_tiles, residual, output, head=head,
      )
      for head in range(self.Q_HEADS)
    )
    lowered = tuple(program.lower() for program in variants)
    combined = variants[0]
    combined._kernels = {
      core: dict(images[core])
      for core, images in zip(cores, lowered)
    }
    return combined


  def _swiglu_math(self, p, *, fp8=False):
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
    p.sfpu.map(combine.finish(), tile=0)
    if fp8: p.sfpu.map(self._round_fp8_program(), tile=0)
    p.sfpu.publish()


  def decode_swiglu(self, gate: Buffer, up: Buffer, hidden: Buffer) -> Program:
    """Compute compact BF16 ``silu(gate) * up`` on all projection cores."""
    p = Program(gate.cores, gate, up, hidden, fp32_dst=True)
    gate_cb = p.cb(DType.BF16, depth=1)
    up_cb = p.cb(DType.BF16, depth=1)
    output_cb = p.cb(DType.BF16, depth=1)
    p.brisc.noc.read_into_cb(gate, 0, gate_cb)
    p.brisc.noc.read_into_cb(up, 0, up_cb)
    p.unpack.move(gate_cb, UnpackTarget.SRCA)
    p.unpack.move(up_cb, UnpackTarget.SRCA)
    self._swiglu_math(p)

    p.pack.move(output_cb, tile=0)
    p.ncrisc.noc.write_from_cb(output_cb, hidden, 0)
    return p


  def _zero_l1_words(self, k, address, count):
    """Clear tile scratch with eight stores per loop iteration."""
    if count == 0: return
    if count % 8: raise ValueError("scratch clear requires a multiple of eight words")
    with k.scope():
      pointer, remaining = k.reg(2, exclude=address if isinstance(address, R) else ())
      if isinstance(address, R): k.mv(pointer, address)
      else: k.li(pointer, address)
      k.li(remaining, count)
      loop = k._new_label("clear_scratch")
      k.label(loop)
      for i in range(8): k.sw(R.ZERO, pointer, i * 4)
      k.addi(pointer, pointer, 32)
      k.addi(remaining, remaining, -8)
      k.bne(remaining, R.ZERO, loop)


  def _scatter_dense(self, p, cb, output, count, *, read_noc=0, eth_output=None):
    """Scatter disjoint feature shards with matching L1/DRAM byte alignment."""
    k = p.ncrisc
    size = output.dtype.itemsize
    shift = size.bit_length() - 1
    noc = k.noc_at(read_noc)
    dense = p.l1(output.tiles * output.tile_size, alignment=16)
    CB.wait_front(k, cb)
    with k.scope():
      start, source = k.reg(2)
      k.read(start, p.param_addr(p.param("dense_start")))
      CB.get_read_ptr(k, cb, source)
      for index in k.range(count):
        with k.scope():
          feature, src, dst, value = k.reg(4, exclude=(start, source, index))
          k.add(feature, start, index)
          self._tile_offset(k, index, src, output.dtype)
          k.add(src, source, src)
          k.read(value, src, bytes=size)
          self._dense_offset(k, output, feature, dst)
          self._add_constant(k, dst, dense)
          k.write(dst, value, bytes=size)
      with k.scope():
        feature, end = k.reg(2, exclude=start)
        k.mv(feature, start)
        k.addi(end, start, count)
        loop = k._new_label("dense_scatter")
        k.label(loop)
        with k.scope():
          tile, offset, length, limit, src, dst = k.reg(6, exclude=(feature, end))
          k.srli(tile, feature, 10)
          if eth_output is None:
            address, coordinate = noc._dram_tile(output, tile)
          else:
            address = k.reg(exclude=(feature, end))
            k.slli(address, tile, output.tile_size.bit_length() - 1)
            self._add_constant(k, address, eth_output[2])
            coordinate = noc.coordinate(*eth_output[:2])
          self._dense_offset(k, output, feature, offset)
          k.li(src, dense)
          k.add(src, src, offset)
          if output.tile_size <= 2048:
            k.andi(offset, offset, output.tile_size - 1)
          else:
            k.slli(offset, offset, 20)
            k.srli(offset, offset, 20)
          k.add(dst, address, offset)
          k.andi(length, feature, 15)
          k.li(limit, 16)
          k.sub(length, limit, length)
          k.sub(limit, end, feature)
          enough = k._new_label("dense_chunk")
          k.bgeu(limit, length, enough)
          k.mv(length, limit)
          k.label(enough)
          k.add(feature, feature, length)
          k.slli(length, length, shift)
          noc.write(src, dst, coordinate, length, posted=False)
        k.bltu(feature, end, loop)
    CB.pop_front(k, cb)
    if eth_output is not None:
      flag = p.l1(16, alignment=16)
      with k.scope():
        sequence, offset, worker, target, source = k.reg(5)
        k.read(sequence, p.param_addr(p.param("collective_base")))
        k.read(offset, p.param_addr(p.param("collective_offset")))
        k.add(sequence, sequence, offset)
        k.read(worker, p.param_addr(p.param("tp_worker_index")))
        k.andi(source, worker, 3)
        k.slli(source, source, 2)
        self._add_constant(k, source, flag)
        k.write(source, sequence)
        k.slli(target, worker, 2)
        self._add_constant(k, target, eth_output[3])
        noc.write(source, target, noc.coordinate(*eth_output[:2]), 4, posted=False)


  def _add_constant(self, k, reg, value):
    with k.scope():
      delta = k.reg(exclude=reg)
      k.li(delta, value)
      k.add(reg, reg, delta)


  def _dense_offset(self, k, buffer, index, output):
    if buffer.tilized:
      self._tile_offset(k, index, output, buffer.dtype)
    else:
      k.slli(output, index, buffer.dtype.itemsize.bit_length() - 1)


  def _tile_offset(self, k, index, output, dtype=DType.BF16):
    # Logical feature -> byte offset in face-tilized BF16 storage.
    with k.scope():
      tmp = k.reg(exclude=(index, output))
      k.andi(output, index, 15)
      k.slli(output, output, 1)
      k.andi(tmp, index, 16)
      k.slli(tmp, tmp, 5)
      k.or_(output, output, tmp)
      k.andi(tmp, index, 480)
      k.or_(output, output, tmp)
      k.srli(tmp, index, 9)
      k.slli(tmp, tmp, 10)
      k.or_(output, output, tmp)
      if dtype.itemsize == 1: k.srli(output, output, 1)
      elif dtype.itemsize == 4: k.slli(output, output, 1)


  def _compact_feature_location(self, feature, total_features):
    counts = self._token_counts(total_features, self.LLAMA_CORES)
    cursor = 0
    for core, count in enumerate(counts):
      if feature < cursor + count: return core, feature - cursor
      cursor += count
    raise ValueError("compact feature index is out of range")


  def _decode_compact_to_dense_program(self,
    cores, compact, output, *, blocks,
  ):
    p = Program(cores, compact, output)
    for block in blocks:
      locations = tuple(
        self._compact_feature_location(block * self.HEAD_DIM + index, self.MLP_DIM)
        for index in range(self.HEAD_DIM)
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
            self._bf16_tile_byte_offset(slot),
            bytes=2,
          )
          p.brisc.write(
            result_l1 + self._bf16_tile_byte_offset(index), value, bytes=2,
          )

      target_tile = block // (1024 // self.HEAD_DIM)
      target_first_row = self.KV_CACHE_FEATURE_TILES * (block % (1024 // self.HEAD_DIM))
      with p.brisc.scope():
        target_address, target_coordinate = p.brisc.noc._dram_tile(
          output, target_tile,
        )
        with p.brisc.noc.transaction() as transaction:
          for feature_half in range(self.KV_CACHE_FEATURE_TILES):
            for face in range(2):
              source_offset = self._bf16_tile_byte_offset(
                feature_half * 32 + face * 16,
              )
              target_offset = self._dense_byte_offset(
                output, (target_first_row + feature_half) * 32 + face * 16,
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


  def decode_compact_to_dense(self, compact: Buffer, output: Buffer) -> Program:
    """Reassemble compact 117-core MLP state into global BF16[1,14336]."""
    block_count = self.MLP_DIM // self.HEAD_DIM
    cores = P100_WORKER_CORES[:min(block_count, len(P100_WORKER_CORES))]
    compact_tiles = self._global_tile_view(compact, "mlp_compact_tiles")
    counts = self._token_counts(block_count, len(cores))
    starts, start = [], 0
    for count in counts:
      starts.append(start)
      start += count
    variants = tuple(
      self._decode_compact_to_dense_program(
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


  def _bf16_tile_byte_offset(self, index):
    """Physical byte offset of a logical BF16 element in a face-tilized tile."""
    row, column = divmod(index, 32)
    face = (row // 16) * 2 + column // 16
    return face * 512 + (row % 16) * 32 + (column % 16) * 2


  def _dense_byte_offset(self, buffer, index):
    """Address dense vectors independently of transient packed compute tiles."""
    return (self._bf16_tile_byte_offset(index) // 2 if buffer.tilized else index) * buffer.dtype.itemsize


  def _compact_projection_location(self, feature, *, query):
    return self._compact_feature_location(
      feature, self.Q_PROJ_DIM if query else self.KV_PROJ_DIM,
    )


  def _compact_slot_byte_offset(self, slot):
    return self._bf16_tile_byte_offset(slot)


  def _decode_rope_program(self,
    cores, q, k, v, cos, sin, q_output, k_output, v_output, start_pos,
    *, query, head, key_cache=None, value_cache=None,
  ):
    p = Program(
      cores, q, k, v, cos, sin, q_output, k_output, v_output, start_pos,
      *((key_cache, value_cache) if key_cache is not None else ()),
    )
    operands = p.cb(DType.BF16, depth=4)
    result = p.cb(DType.BF16, depth=1)
    feature_locations = tuple(
      self._compact_projection_location(
        head * self.HEAD_DIM + index, query=query,
      )
      for index in range(self.HEAD_DIM)
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
      p.brisc.srli(table_tile, position, (1024 // self.HEAD_DIM).bit_length() - 1)
      p.brisc.andi(table_row_offset, position, 1024 // self.HEAD_DIM - 1)
      if cos.tilized:
        p.brisc.slli(table_row_offset, table_row_offset, self.KV_CACHE_FEATURE_TILES.bit_length() - 1)
        with p.brisc.scope():
          face, row = p.brisc.reg(2, exclude=table_row_offset)
          p.brisc.srli(face, table_row_offset, 4)
          p.brisc.slli(face, face, 10)
          p.brisc.andi(row, table_row_offset, 15)
          p.brisc.slli(row, row, 5)
          p.brisc.add(table_row_offset, face, row)
      else:
        p.brisc.slli(table_row_offset, table_row_offset, self.HEAD_DIM.bit_length())

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
              self._compact_slot_byte_offset(slot)
            )
            source_address = (
              source_tiles_l1 +
              compact_offset
            )
            p.brisc.read(value, source_address, bytes=2)
            p.brisc.write(
              operands.addr + self._bf16_tile_byte_offset(index), value, bytes=2,
            )
            rotated_index = index + self.HEAD_DIM // 2 if index < self.HEAD_DIM // 2 else index - self.HEAD_DIM // 2
            if index >= self.HEAD_DIM // 2: p.brisc.xor(value, value, sign)
            p.brisc.write(
              operands.addr + operands.tile_size +
              self._bf16_tile_byte_offset(rotated_index),
              value, bytes=2,
            )
            if not query:
              v_value = p.brisc.reg(exclude=(sign, value))
              p.brisc.read(
                v_value, v_source_tiles_l1 + compact_offset, bytes=2,
              )
              p.brisc.write(
                v_head_l1 + self._bf16_tile_byte_offset(index),
                v_value, bytes=2,
              )

      # Extract the runtime position from each table tile into a normal output
      # tile. A cache tile holds 8 positions, each spanning four logical rows.
      for table_l1, operand_tile in ((cos_tile_l1, 2), (sin_tile_l1, 3)):
        for source_delta, target_offset in (
          (self._dense_byte_offset(cos, i), self._bf16_tile_byte_offset(i))
          for i in range(0, self.HEAD_DIM, 16)
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

      if not query and key_cache is None:
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
    if query or key_cache is None:
      p.ncrisc.noc.write_from_cb(result, q_output if query else k_output, head)
    else:
      CB.wait_front(p.ncrisc, result)
      self._append_cache_rows(p, result.addr, v_head_l1, key_cache, value_cache, start_pos, head)
      CB.pop_front(p.ncrisc, result)
    return p


  def _append_cache_rows(self, p, k_l1, v_l1, key_cache, value_cache, start_pos, head):
    """Write this head's new K/V directly from RoPE's local L1 buffers."""
    size = key_cache.dtype.itemsize
    shift = size.bit_length() - 1
    k = p.ncrisc
    with k.scope():
      position, block, row = k.reg(3)
      k.read(position, p.param_addr(start_pos))
      k.srli(block, position, 5)
      k.slli(block, block, (self.KV_CACHE_FEATURE_TILES.bit_length() - 1))
      self._add_constant(k, block, head * self.KV_CACHE_TILES_PER_HEAD)
      k.andi(row, position, 15)
      k.slli(row, row, 4 + shift)
      with k.scope():
        bottom = k.reg(exclude=(position, row))
        k.andi(bottom, position, 16)
        k.slli(bottom, bottom, 5 + shift)
        k.add(row, row, bottom)
      for half in range(self.KV_CACHE_FEATURE_TILES):
        with k.scope():
          tile = k.reg(exclude=(block, row))
          k.addi(tile, block, half)
          for cache, source in ((key_cache, k_l1), (value_cache, v_l1)):
            address, coordinate = k.noc._dram_tile(cache, tile)
            with k.noc.transaction() as transaction:
              for face in range(2):
                with k.scope():
                  target = k.reg(exclude=(address, row))
                  k.add(target, address, row)
                  if face: k.addi(target, target, 256 * size)
                  transaction.write(source + half * 16 * size + face * 256 * size,
                                    target, coordinate, 16 * size, posted=False)


  def _global_tile_view(self, buffer, name):
    return Buffer(
      name, buffer.addr, buffer.dtype, (buffer.physical_tiles, 1024), 0,
      (buffer.cores[0],), buffer.banks, global_address=True,
      tilized=buffer.tilized, dram_endpoints=buffer.dram_endpoints,
    )


  def decode_rope(self, q: Buffer, k: Buffer, v: Buffer, cos: Buffer, sin: Buffer,
                  q_output: Buffer, k_output: Buffer,
                  v_output: Buffer, *, key_cache=None, value_cache=None) -> Program:
    """Apply Q/K RoPE and reassemble V together in one 40-core launch."""
    cores = q.cores[:self.ROPE_CORES]
    q_tiles, k_tiles, v_tiles = (
      self._global_tile_view(q, "rope_q_compact_tiles"),
      self._global_tile_view(k, "rope_k_compact_tiles"),
      self._global_tile_view(v, "rope_v_compact_tiles"),
    )
    start_pos = Const("start_pos", 0)
    specifications = (
      *((True, head) for head in range(self.Q_HEADS)),
      *((False, head) for head in range(self.KV_HEADS)),
    )
    variants = [
      self._decode_rope_program(
        cores, q_tiles, k_tiles, v_tiles, cos, sin,
        q_output, k_output, v_output, start_pos, query=query, head=head,
        key_cache=key_cache, value_cache=value_cache,
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


  def kv_cache_write(self, k: Buffer, v: Buffer, key_cache: Buffer,
                     value_cache: Buffer) -> Program:
    """Copy one decoded K/V token into standard 2-D cache tiles.

    The logical ``[8, 8192, 128]`` cache is physically
    ``[8, 256 time blocks, 4 feature tiles, 32, 32]``.  Eight BRISCs run
    independently, one per KV head, and update one row in each feature tile.
    Other cache positions are never read or overwritten.
    """
    start_pos = Const("start_pos", 0)
    head_index = Const("head_index", tuple(range(self.KV_HEADS)))
    p = Program(
      P100_WORKER_CORES[:self.KV_HEADS],
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
        p.brisc.slli(cache_tile, head, self.KV_CACHE_TILES_PER_HEAD.bit_length() - 1)
        with p.brisc.scope():
          block_tiles = p.brisc.reg(exclude=(cache_tile, time_block))
          p.brisc.slli(block_tiles, time_block, self.KV_CACHE_FEATURE_TILES.bit_length() - 1)
          p.brisc.add(cache_tile, cache_tile, block_tiles)

        for feature_half, source_offsets in enumerate((i * 32, i * 32 + 512) for i in range(self.KV_CACHE_FEATURE_TILES)):
          with p.brisc.scope():
            target_tile = p.brisc.reg(exclude=(cache_tile, row_offset))
            p.brisc.mv(target_tile, cache_tile)
            if feature_half: p.brisc.addi(target_tile, target_tile, feature_half)
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


  def _gqa_exp_program(self, *, value_offset):
    builder = SfpuProgramBuilder()
    value = builder.load(format=SfpuFormat.FP32, offset=value_offset)
    builder.exp(value, into=value)
    builder.store(value, format=SfpuFormat.FP32, offset=value_offset)
    return builder.finish()


  def _gqa_normalize_program(self, *, output_offset, sum_offset):
    builder = SfpuProgramBuilder()
    output = builder.load(format=SfpuFormat.FP32, offset=output_offset)
    denominator = builder.load(format=SfpuFormat.FP32, offset=sum_offset)
    builder.reciprocal(denominator, into=denominator)
    builder.mul(output, denominator, into=output)
    builder.store(output, format=SfpuFormat.FP32, offset=output_offset)
    return builder.finish()


  def _gqa_issue_program(self, sfpu, program):
    """Run one explicitly addressed 4x8 SFPU footprint."""
    self._rms_select_tile(sfpu, 0)
    for word in (*program.setup_words, *program.words): sfpu._issue(word)
    stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


  def _gqa_online_update(self, sfpu, row_chunks=GQA_ROW_CHUNKS):
    """Update m/l/P/O for rows 0..3 after one score matmul."""
    score = 0
    maximum, total, alpha = ((self.KV_CACHE_FEATURE_TILES + i) * 64 for i in (1, 2, 3))
    words = []
    words.extend(self._sfpu_float_words(LReg.L4, self.HEAD_DIM ** -0.5))
    for register, chunk in zip(
      (LReg.L0, LReg.L1, LReg.L2, LReg.L3), row_chunks,
    ):
      words.append(TT.TTSFPLOAD(register, SfpuFormat.FP32, 7, score + chunk))
      self._sfpu_mul(words, register, LReg.L4, register)
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
    for chunk in row_chunks:
      words.append(TT.TTSFPSTORE(
        LReg.L0, SfpuFormat.FP32, 7, maximum + chunk,
      ))
    words.extend((
      TT.TTSFPMAD(LReg.L0, LReg.NEG_ONE, LReg.L3, LReg.L5, 0),
      TT.TTSFPNOP(),
    ))
    for chunk in row_chunks:
      words.append(TT.TTSFPSTORE(
        LReg.L5, SfpuFormat.FP32, 7, alpha + chunk,
      ))
    for word in words: sfpu._issue(word)

    # Shift scores separately so the exp program can reuse its LRegs without a
    # load/subtract lifetime crossing the programmable-constant setup.
    words = []
    for chunk in row_chunks:
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
    for chunk in row_chunks:
      self._gqa_issue_program(sfpu, self._gqa_exp_program(value_offset=alpha + chunk))
    for chunk in row_chunks:
      self._gqa_issue_program(sfpu, self._gqa_exp_program(value_offset=score + chunk))

    # l_new = l_old * alpha + sum(P).  Horizontal reduction is independent in
    # each eight-lane subgroup, one subgroup per live query row.
    words = [
      TT.TTSFPLOAD(register, SfpuFormat.FP32, 7, score + chunk)
      for register, chunk in zip(
        (LReg.L0, LReg.L1, LReg.L2, LReg.L3), row_chunks,
      )
    ]
    self._sfpu_add(words, LReg.L0, LReg.L2, LReg.L0)
    self._sfpu_add(words, LReg.L1, LReg.L3, LReg.L1)
    self._sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
    for rotations in (4, 2, 1):
      words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
      for _ in range(rotations):
        words.extend((
          TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3), TT.TTSFPNOP(),
        ))
      self._sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
    words.extend((
      TT.TTSFPLOAD(LReg.L2, SfpuFormat.FP32, 7, total),
      TT.TTSFPLOAD(LReg.L3, SfpuFormat.FP32, 7, alpha),
      TT.TTSFPMAD(LReg.L2, LReg.L3, LReg.L0, LReg.L0, 0),
      TT.TTSFPNOP(),
    ))
    for chunk in row_chunks:
      words.append(TT.TTSFPSTORE(
        LReg.L0, SfpuFormat.FP32, 7, total + chunk,
      ))

    # Rescale the persistent FP32 context before accumulating this block's PV.
    for output in range(64, (self.KV_CACHE_FEATURE_TILES + 1) * 64, 64):
      for chunk in row_chunks:
        words.extend((
          TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, output + chunk),
          TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, alpha + chunk),
        ))
        self._sfpu_mul(words, LReg.L0, LReg.L1, LReg.L0)
        words.append(TT.TTSFPSTORE(
          LReg.L0, SfpuFormat.FP32, 7, output + chunk,
        ))
    for word in words: sfpu._issue(word)
    stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


  def _prepare_attention_rope(self, p, inputs, key_cache, value_cache, start_pos, head, query_cb, group_size):
    """Rotate a worker's Q heads and their K in one tile; retain Q in L1.

    At 16/32 workers, workers sharing a KV head write identical cache bytes.
    Each waits for its own acknowledged writes before reading that cache row.
    """
    q, k, v, cos, sin = inputs
    operands = p.cb(DType.BF16, depth=4)
    fp8 = query_cb.dtype.is_fp8
    result = p.cb(query_cb.dtype, depth=2 if fp8 else 1)
    value_operand = p.cb(DType.BF16, depth=1) if fp8 else None
    packed_offset = lambda index: self._bf16_tile_byte_offset(index) // (2 if fp8 else 1)
    ready = p.cb(DType.BF16, depth=1)
    # Fixed allocation sizes make CB addresses identical in all head variants.
    # A TP shard has fewer KV rows per worker, so one head spans more tiles.
    staging_tiles = max(20, math.ceil(self.HEAD_DIM / min(self._token_counts(self.KV_PROJ_DIM, self.LLAMA_CORES))) + 1)
    source_l1 = p.l1(staging_tiles * q.tile_size, alignment=16)
    v_l1 = p.l1(staging_tiles * v.tile_size, alignment=16)
    v_head = p.l1(v.tile_size, alignment=16)
    cos_l1 = p.l1(cos.tile_size, alignment=16)
    sin_l1 = p.l1(sin.tile_size, alignment=16)
    with p.brisc.scope():
      position, tile, row = p.brisc.reg(3)
      p.brisc.read(position, p.param_addr(start_pos))
      p.brisc.srli(tile, position, (1024 // self.HEAD_DIM).bit_length() - 1)
      p.brisc.andi(row, position, (1024 // self.HEAD_DIM) - 1)
      p.brisc.slli(row, row, self.HEAD_DIM.bit_length() - 1)
      if cos.tilized:
        # A table token is four logical rows, or 128 BF16 elements.
        with p.brisc.scope():
          upper = p.brisc.reg(exclude=row)
          p.brisc.andi(upper, row, 512)
          p.brisc.slli(upper, upper, 1)
          p.brisc.andi(row, row, 511)
          p.brisc.add(row, row, upper)
      else:
        p.brisc.slli(row, row, 1)
      for table, target in ((cos, cos_l1), (sin, sin_l1)):
        p.brisc.noc.read_tile(table, tile, target)
      for group in range(group_size + 1):
        is_query = group < group_size
        first = ((head * group_size + group) if is_query else head // (4 // group_size)) * self.HEAD_DIM
        locations = tuple(self._compact_projection_location(first + i, query=is_query)
                          for i in range(self.HEAD_DIM))
        tiles = tuple(dict.fromkeys(t for t, _ in locations))
        source = q if is_query else k
        with p.brisc.noc.transaction() as transaction:
          for i, source_tile in enumerate(tiles):
            with p.brisc.scope():
              address, coordinate = p.brisc.noc._dram_tile(source, source_tile)
              transaction.read(address, coordinate, source_l1 + i * source.tile_size, source.tile_size)
            if not is_query:
              with p.brisc.scope():
                address, coordinate = p.brisc.noc._dram_tile(v, source_tile)
                transaction.read(address, coordinate, v_l1 + i * v.tile_size, v.tile_size)
        with p.brisc.scope():
          sign = p.brisc.reg()
          p.brisc.li(sign, 0x8000)
          for i, (source_tile, slot) in enumerate(locations):
            source_offset = tiles.index(source_tile) * source.tile_size + self._compact_slot_byte_offset(slot)
            with p.brisc.scope():
              value = p.brisc.reg(exclude=sign)
              p.brisc.read(value, source_l1 + source_offset, bytes=2)
              p.brisc.write(operands.addr + self._bf16_tile_byte_offset(group * self.HEAD_DIM + i), value, bytes=2)
              if i >= self.HEAD_DIM // 2: p.brisc.xor(value, value, sign)
              rotated = group * self.HEAD_DIM + (i + self.HEAD_DIM // 2 if i < self.HEAD_DIM // 2 else i - self.HEAD_DIM // 2)
              p.brisc.write(operands.addr + operands.tile_size + self._bf16_tile_byte_offset(rotated), value, bytes=2)
              if not is_query:
                p.brisc.read(value, v_l1 + source_offset, bytes=2)
                p.brisc.write(v_head + self._bf16_tile_byte_offset(i), value, bytes=2)
        for table, operand in ((cos_l1, 2), (sin_l1, 3)):
          for i in range(0, self.HEAD_DIM, 16):
            with p.brisc.scope():
              offset = p.brisc.reg(exclude=row)
              p.brisc.addi(offset, row, self._dense_byte_offset(cos, i))
              l1.copy_words(p.brisc, table,
                            operands.addr + operand * operands.tile_size + self._bf16_tile_byte_offset(group * self.HEAD_DIM + i),
                            8, source_offset=offset, unroll=8)
    if fp8:
      l1.copy_words(p.brisc, v_head, value_operand.addr, v.tile_size // 4)
      CB.push_back(p.brisc, value_operand)
    CB.push_back(p.brisc, operands, 4)
    for _ in range(4): p.unpack.move(operands, UnpackTarget.SRCA)
    if fp8: p.unpack.move(value_operand, UnpackTarget.SRCA)
    p.fpu.copy_a_tiles(dst_tiles=range(5 if fp8 else 4))
    sfpu = p.sfpu.program()
    x = sfpu.load(offset=0)
    rotated = sfpu.load(offset=64)
    cosine = sfpu.load(offset=128)
    sine = sfpu.load(offset=192)
    product = sfpu.mul(x, cosine)
    value = sfpu.mad(rotated, sine, product)
    sfpu.round_bf16(value, into=value)
    sfpu.store(value, offset=0)
    p.sfpu.map(sfpu.finish(), tile=0)
    if fp8:
      for tile in (0, 4): p.sfpu.map(self._round_fp8_program(), tile=tile)
    p.sfpu.publish()
    p.pack.move_tiles(result, tiles=(0, 4) if fp8 else (0,))
    CB.wait_front(p.ncrisc, result, 2 if fp8 else 1)
    self._zero_l1_words(p.ncrisc, query_cb.addr, query_cb.size // 4)
    for group in range(group_size):
      for half in range(self.KV_CACHE_FEATURE_TILES):
        for face in range(2):
          l1.copy_words(p.ncrisc,
                        result.addr + packed_offset(group * self.HEAD_DIM + half * 32 + face * 16),
                        query_cb.addr + half * query_cb.tile_size + packed_offset(group * 32 + face * 16),
                        4 if fp8 else 8, unroll=4 if fp8 else 8)
    self._append_cache_rows(p, result.addr + packed_offset(group_size * self.HEAD_DIM), result.addr + result.tile_size if fp8 else v_head,
                       key_cache, value_cache, start_pos, head // (4 // group_size))
    CB.pop_front(p.ncrisc, result, 2 if fp8 else 1)
    CB.push_back(p.ncrisc, ready)
    # All dependencies are within this KV group; there is no global barrier.
    CB.wait_front(p.brisc, ready)


  # Streaming grouped-query attention

  def gqa_attention_fused(self, q, key_cache, value_cache, context, *, rope_inputs=None, attention_cores=None):
    attention_cores = self.attention_cores if attention_cores is None else attention_cores
    if attention_cores not in (8, 16, 32): raise ValueError("attention cores must be 8, 16, or 32")
    group_size = self.Q_HEADS // attention_cores
    inputs = None if rope_inputs is None else tuple(self._global_tile_view(b, f"attention_{b.name}") for b in rope_inputs[:3]) + tuple(rope_inputs[3:])
    return specialize(
      lambda head: self._gqa_attention_program(q, key_cache, value_cache, context, rope_inputs=inputs, head_index=head, group_size=group_size),
      P100_WORKER_CORES[:attention_cores], tuple(range(attention_cores)),
    )


  def _gqa_attention_program(self,
    q: Buffer, key_cache: Buffer, value_cache: Buffer, context: Buffer,
    *, rope_inputs=None, head_index=None, group_size=4,
  ) -> Program:
    """Fused streaming decode GQA: scaled QK, online softmax, and PV."""
    # These chunks span both column faces as well as the live row pairs.
    # Retain the complete footprint even when fewer query rows are active.
    row_chunks = self.GQA_ROW_CHUNKS
    group_shift = group_size.bit_length() - 1
    kv_blocks = Const("kv_blocks", 1)
    valid_columns = Const("valid_columns", 1)
    kv_head = Const("kv_head", tuple(range(self.Q_HEADS // group_size)))
    start_pos = Const("start_pos", 0)
    p = Program(
      P100_WORKER_CORES[:self.Q_HEADS // group_size], q, key_cache, value_cache, context,
      kv_blocks, valid_columns,
      *((kv_head,) if rope_inputs is None else (*rope_inputs, start_pos)), fp32_dst=True,
    )
    # FPU matmul owns replay slots 16..31; SFPU shares the physical replay RAM.
    p.sfpu._mop.state.replay.used.update(range(16, 32))
    query_cb = p.cb(key_cache.dtype, depth=self.KV_CACHE_FEATURE_TILES)
    key_cb = p.cb(key_cache.dtype, depth=2 * self.KV_CACHE_FEATURE_TILES)
    value_cb = p.cb(key_cache.dtype, depth=2 * self.KV_CACHE_FEATURE_TILES)
    probability_cb = p.cb(key_cache.dtype, depth=self.KV_CACHE_FEATURE_TILES)
    mask_cb = p.cb(DType.F32, depth=1)
    zero_cb = p.cb(DType.F32, depth=1)
    context_cb = p.cb(context.dtype, depth=self.KV_CACHE_FEATURE_TILES)
    if rope_inputs is not None:
      self._prepare_attention_rope(p, rope_inputs, key_cache, value_cache, start_pos, head_index, query_cb, group_size)
    else:
      query_heads_l1 = p.l1(group_size * q.tile_size, alignment=16)
      self._zero_l1_words(p.brisc, query_cb.addr, query_cb.size // 4)
      for group_row in range(group_size):
        source = query_heads_l1 + group_row * q.tile_size
        p.brisc.noc.read_tile(q, head_index * group_size + group_row, source)
        for feature in range(self.KV_CACHE_FEATURE_TILES):
          for face in range(2):
            l1.copy_words(p.brisc, source,
              query_cb.addr + feature * query_cb.tile_size + self._bf16_tile_byte_offset(group_row * 32 + face * 16),
              8, source_offset=self._bf16_tile_byte_offset(feature * 32 + face * 16))

    with p.brisc.scope():
      head, block_count, tail = p.brisc.reg(3)
      if head_index is None: p.brisc.read(head, p.param_addr(kv_head))
      else: p.brisc.li(head, head_index)
      p.brisc.read(block_count, p.param_addr(kv_blocks))
      p.brisc.read(tail, p.param_addr(valid_columns))

      CB.reserve_back(p.brisc, zero_cb)
      with p.brisc.scope():
        target = p.brisc.reg()
        CB.get_write_ptr(p.brisc, zero_cb, target)
        self._zero_l1_words(p.brisc, target, zero_cb.tile_size // 4)
      CB.push_back(p.brisc, zero_cb)

      CB.reserve_back(p.brisc, mask_cb)
      with p.brisc.scope():
        target = p.brisc.reg()
        CB.get_write_ptr(p.brisc, mask_cb, target)
        self._zero_l1_words(p.brisc, target, mask_cb.tile_size // 4)
        with p.brisc.scope():
          column, limit, negative_infinity = p.brisc.reg(3)
          p.brisc.mv(column, tail)
          p.brisc.li(limit, self.KV_CACHE_TOKEN_BLOCK)
          p.brisc.li(negative_infinity, 0xff800000)
          with p.brisc.loop(Cond(column, "<u", limit)):
            with p.brisc.scope():
              face_offset, within_face, offset = p.brisc.reg(3)
              p.brisc.srli(face_offset, column, 4)
              p.brisc.slli(face_offset, face_offset, 10)
              p.brisc.andi(within_face, column, 15)
              p.brisc.slli(within_face, within_face, 2)
              p.brisc.add(offset, face_offset, within_face)
              for row in range(group_size):
                with p.brisc.scope():
                  address = p.brisc.reg(exclude=(target, offset))
                  p.brisc.add(address, target, offset)
                  if row: p.brisc.addi(address, address, row * 64)
                  p.brisc.sw(negative_infinity, address)
            p.brisc.addi(column, column, 1)
      CB.push_back(p.brisc, mask_cb)

      for block in p.brisc.range(block_count):
        CB.reserve_back(p.brisc, query_cb, self.KV_CACHE_FEATURE_TILES)
        CB.push_back(p.brisc, query_cb, self.KV_CACHE_FEATURE_TILES)
        with p.brisc.scope():
          first, block_offset = p.brisc.reg(2, exclude=(head, block))
          p.brisc.srli(first, head, 2 - group_shift)
          p.brisc.slli(first, first, self.KV_CACHE_TILES_PER_HEAD.bit_length() - 1)
          p.brisc.slli(block_offset, block, self.KV_CACHE_FEATURE_TILES.bit_length() - 1)
          p.brisc.add(first, first, block_offset)
          for cache, cb in ((key_cache, key_cb), (value_cache, value_cb)):
            for feature in range(self.KV_CACHE_FEATURE_TILES):
              with p.brisc.scope():
                tile = p.brisc.reg(exclude=first)
                p.brisc.addi(tile, first, feature)
                p.brisc.noc.read_tiles_into_cb(cache, (tile,), cb)

    with p.trisc0.scope():
      block_count, last_block = p.trisc0.reg(2)
      p.trisc0.read(block_count, p.param_addr(kv_blocks))
      p.trisc0.addi(last_block, block_count, -1)
      for block in p.trisc0.range(block_count):
        for feature in range(self.KV_CACHE_FEATURE_TILES):
          p.unpack.move_matmul(query_cb, key_cb, right_transpose=True)
        no_mask = p.trisc0._new_label("gqa_unpack_no_mask")
        p.trisc0.bne(block, last_block, no_mask)
        p.unpack.move_pair(zero_cb, mask_cb)
        p.trisc0.label(no_mask)
        for feature in range(self.KV_CACHE_FEATURE_TILES):
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
      # Context occupies one Dst tile per feature tile, followed by m, l, alpha.
      for tile in (*range(1, self.KV_CACHE_FEATURE_TILES + 2), self.KV_CACHE_FEATURE_TILES + 3): p.sfpu.map(zero, tile=tile)
      # Keep inactive rows finite when the row mapper traverses the top half.
      # Only the four live rows are overwritten with the online initial state.
      p.sfpu.map(one, tile=self.KV_CACHE_FEATURE_TILES + 2)
      self._rms_select_tile(p.sfpu, 0)
      for word in self._sfpu_float_words(LReg.L0, float("-inf")):
        p.sfpu._issue(word)
      for chunk in row_chunks:
        p.sfpu._issue(TT.TTSFPSTORE(
          LReg.L0, SfpuFormat.FP32, 7, (self.KV_CACHE_FEATURE_TILES + 1) * 64 + chunk,
        ))
      for word in self._sfpu_float_words(LReg.L0, 0.0): p.sfpu._issue(word)
      for chunk in row_chunks:
        p.sfpu._issue(TT.TTSFPSTORE(
          LReg.L0, SfpuFormat.FP32, 7, (self.KV_CACHE_FEATURE_TILES + 2) * 64 + chunk,
        ))
      stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)

      for block in p.trisc1.range(block_count):
        for feature in range(self.KV_CACHE_FEATURE_TILES):
          p.fpu.matmul(dst_tile=0, accumulate=feature != 0, right_transpose=True, fidelity=self.FP8_FIDELITY if key_cache.dtype.is_fp8 else 2)
        unmasked = p.trisc1._new_label("gqa_score_unmasked")
        p.trisc1.bne(block, last_block, unmasked)
        p.fpu.binary("add", dst_tile=0, accumulate=True)
        p.trisc1.label(unmasked)
        self._rms_select_tile(p.sfpu, 0)
        self._gqa_online_update(p.sfpu, row_chunks)
        if key_cache.dtype.is_fp8: p.sfpu.map(self._round_fp8_program(), tile=0)
        p.sfpu.publish()
        for tile in range(1, self.KV_CACHE_FEATURE_TILES + 1):
          p.fpu.matmul(dst_tile=tile, accumulate=True, fidelity=self.FP8_FIDELITY if key_cache.dtype.is_fp8 else 2)

      self._rms_select_tile(p.sfpu, 0)
      for output in range(64, (self.KV_CACHE_FEATURE_TILES + 1) * 64, 64):
        for chunk in row_chunks:
          self._gqa_issue_program(p.sfpu, self._gqa_normalize_program(
            output_offset=output + chunk, sum_offset=(self.KV_CACHE_FEATURE_TILES + 2) * 64 + chunk,
          ))
      if context.dtype.is_fp8:
        for tile in range(1, self.KV_CACHE_FEATURE_TILES + 1): p.sfpu.map(self._round_fp8_program(), tile=tile)
      p.sfpu.publish()

    # Pack one P copy per feature tile while retaining the online state.
    # Release Dst after all context tiles have been packed.
    with p.trisc2.scope():
      block_count = p.trisc2.reg()
      p.trisc2.read(block_count, p.param_addr(kv_blocks))
      for _ in p.trisc2.range(block_count):
        sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
        for _ in range(self.KV_CACHE_FEATURE_TILES):
          p.pack._move_acquired(probability_cb, 0, False)
        sem_get(p.trisc2, Sem.MATH_PACK)
      p.pack.move_tiles(context_cb, tiles=tuple(range(1, self.KV_CACHE_FEATURE_TILES + 1)))

    # Each specialized worker scatters its query heads into dense context.
    CB.wait_front(p.ncrisc, context_cb, self.KV_CACHE_FEATURE_TILES)
    for group_row in range(group_size):
      for feature in range(self.KV_CACHE_FEATURE_TILES):
        first_element = (head_index * group_size + group_row) * self.HEAD_DIM + feature * 32
        with p.ncrisc.scope():
          target_address, target_coordinate = p.ncrisc.noc._dram_tile(context, first_element // 1024)
          with p.ncrisc.noc.transaction() as transaction:
            for face in range(2):
              with p.ncrisc.scope():
                target = p.ncrisc.reg(exclude=target_address)
                p.ncrisc.mv(target, target_address)
                self._add_constant(p.ncrisc, target, self._dense_byte_offset(context, first_element % 1024 + face * 16))
                transaction.write(
                  context_cb.addr + feature * context_cb.tile_size + self._bf16_tile_byte_offset(group_row * 32 + face * 16) * context.dtype.itemsize // 2,
                  target, target_coordinate, 16 * context.dtype.itemsize, posted=False,
                )
    CB.pop_front(p.ncrisc, context_cb, self.KV_CACHE_FEATURE_TILES)
    return p


  # Token embedding and RMSNorm

  def decode_embedding(self,
    token_id: Buffer, embedding_weight: Buffer, output: Buffer,
  ) -> Program:
    """Gather one embedding row on one core.

      token_id          flat U32[8192]       global; `token_pos` selects the ID
      embedding_weight  BF16[128256, 4096]    global, 4 tiles per vocabulary row
      output            BF16[1, 4096]         global, 4 tiles

    Logical operation:
      output[0, :] = embedding_weight[token_id[token_pos], :]
    """
    token_pos = Const("token_pos", 0)
    p = Program(
      output.cores, token_id, embedding_weight, output, token_pos,
    )
    ids_l1 = p.l1(token_id.tile_size, alignment=16)
    embedding_cb = p.cb(DType.BF16, depth=self.EMBEDDING_TILES)
    with p.brisc.scope():
      position, tile, within, token = p.brisc.reg(4)
      p.brisc.read(position, p.param_addr(token_pos))
      p.brisc.srli(tile, position, 10)          # 1024 flat token IDs per DRAM page
      p.brisc.andi(within, position, 1023)
      p.brisc.noc.read_tile(token_id, tile, ids_l1)
      p.brisc.slli(within, within, 2)
      self._add_constant(p.brisc, within, ids_l1)
      p.brisc.read(token, within)
      for row_tile in range(self.EMBEDDING_TILES):
        with p.brisc.scope():
          # weight tile index = token * EMBEDDING_TILES + row_tile
          source_tile = p.brisc.reg(exclude=token)
          p.brisc.slli(source_tile, token, self.EMBEDDING_TILES_SHIFT)
          if row_tile: p.brisc.addi(source_tile, source_tile, row_tile)
          p.brisc.noc.read_into_cb(
            embedding_weight, source_tile, embedding_cb,
          )
    p.ncrisc.noc.write_tiles_from_cb(
      embedding_cb, output, tuple(range(self.EMBEDDING_TILES)),
    )
    return p


  def rmsnorm(self, x: Buffer, weight: Buffer, output: Buffer) -> Program:
    """Normalize one decode token and apply the learned scale."""
    if x.tilized != weight.tilized or x.tilized != output.tilized:
      raise ValueError("RMSNorm operands must have the same element order")
    p = Program(x.cores, x, weight, output, fp32_dst=True)
    if hybrid_rmsnorm_enabled():
      output_cb = p.cb(DType.BF16, depth=self.EMBEDDING_TILES)
      emit_rmsnorm(p, x, weight, output_cb, tiles=self.EMBEDDING_TILES,
                   finalize=self._rms_finalize_scale())
    else:
      x_cb = p.cb(DType.BF16, depth=4)
      output_cb = p.cb(DType.BF16, depth=4)
      gamma_l1 = p.l1(self.EMBEDDING_TILES * weight.tile_size, alignment=16)

      p.brisc.noc.read_tiles(weight, tuple(
        (tile, gamma_l1 + tile * weight.tile_size)
        for tile in range(self.EMBEDDING_TILES)
      ))
      p.brisc.noc.read_tiles_into_cb(x, tuple(range(self.EMBEDDING_TILES)), x_cb)
      for _ in range(self.EMBEDDING_TILES):
        p.unpack.move(x_cb, UnpackTarget.SRCA)
      for tile in range(self.EMBEDDING_TILES):
        p.unpack.move_l1(weight.dtype, gamma_l1 + tile * weight.tile_size)
      self._rms_setup_apply_macro(p.sfpu)
      p.fpu.copy_a_tiles(dst_tiles=range(2 * self.EMBEDDING_TILES))
      self._rmsnorm_one_token(p.sfpu)
      p.pack.move_tiles(output_cb, tiles=tuple(range(self.EMBEDDING_TILES)))
    p.ncrisc.noc.write_tiles_from_cb(
      output_cb, output, tuple(range(self.EMBEDDING_TILES)),
    )
    return p


  # Prompt ingestion and greedy generation

  def run_decode_e2e(self,
    prompt="The capital of France is", steps=None,
    safetensor_path=None,
    tokenizer_path=None,
    profile=False,
    device_index=0,
    attention_cores=None,
    prefill=False,
    prefill_chunk_size=4,
  ):
    """Run greedy generation with optional chunked 8B BF16 prefill."""
    if prefill and (self.model != "8b" or self.dtype != "bf16"):
      raise ValueError("chunked prefill supports 8B BF16 only")
    safetensor_path = self.checkpoint if safetensor_path is None else safetensor_path
    if tokenizer_path is None:
      checkpoint_path = Path(safetensor_path)
      tokenizer_path = checkpoint_path.parent if checkpoint_path.is_file() else checkpoint_path
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
    max_steps = self.ROPE_CACHE_TOKENS - len(prompt_ids)
    if max_steps < 1:
      raise ValueError("prompt leaves no room for decode generation")
    if steps is None:
      steps = max_steps
    elif steps > max_steps:
      raise ValueError("prompt plus generation exceeds the 8192-token cache")

    runtime = Llama3Decode(safetensor_path, device_index, attention_cores=attention_cores, kernels=self)
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
      if prefill:
        next_token, _ = runtime.prefill(prompt_ids, chunk_size=prefill_chunk_size)
      else:
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
        if next_token in self.EOS_TOKEN_IDS or step + 1 == steps: break
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

    if generation_replays:
      print(f"{generation_replays / generation_seconds:.2f} decode tok/s")
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
        f"  host read/stage      {startup['weight_stage_s'] * 1e3:9.2f} ms"
      )
      upload_gb = startup["dram_upload_bytes"] / 1e9
      upload_s = startup["weight_upload_total_s"]
      print(
        f"  full weight upload   {upload_s * 1e3:9.2f} ms  "
        f"({upload_gb:.3f} GB, {upload_gb / upload_s:.2f} GB/s, includes prepare/stage)"
      )
      print(
        f"  upload wait/submit   {startup['upload_wait_s'] * 1e3:9.2f} / "
        f"{startup['upload_submit_s'] * 1e3:.2f} ms (overlapped transfers)"
      )
      print(
        f"  program build        {startup['program_build_s'] * 1e3:9.2f} ms"
      )
      print(
        f"prompt {'prefill' if prefill else 'decode'}         {prompt_seconds * 1e3:9.2f} ms  "
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


  # Chunked BF16 prefill kernels

  def prefill_projection(self, x, weight, output, count):
    """Compute count independent BF16 matrix-vector products, reusing weights.

    x contains bank-aligned, row-major token slabs; output contains the existing
    per-worker compact fragments in token slabs. Dot products accumulate FP32
    and round to BF16 exactly where decode rounds its projection output.
    """
    return self.prefill_projections(x, ((weight, output),), count)


  def prefill_projections(self, x, projections, count, norm_weight=None):
    """Grouped QKV or gate/up with one local RMSNorm per token and worker."""
    projections = tuple(projections)
    if not 1 <= len(projections) <= 3:
      raise ValueError("prefill supports one to three grouped projections")
    if type(count) is not int or not 1 <= count <= x.capacity:
      raise ValueError("invalid prefill token count")
    weights = tuple(weight for weight, _ in projections)
    for weight, output in projections:
      if (weight.dtype is not DType.BF16 or not weight.global_address or weight.tilized or
          x.prototype.dtype is not DType.BF16 or x.prototype.tilized):
        raise ValueError("prefill requires global row-major BF16 weights and inputs")
      if weight.shape[1] != x.prototype.shape[-1] or weight.shape[1] % 1024:
        raise ValueError("projection input dimension must match complete BF16 pages")
      if (weight.cores != weights[0].cores or output.prototype.cores != weight.cores or
          output.prototype.dtype is not DType.BF16 or not output.prototype.tilized or
          output.prototype.tiles_per_core != 1 or weight.items_per_core > 1024 or
          count > output.capacity):
        raise ValueError("invalid prefill projection output layout or capacity")
    if norm_weight is not None and (norm_weight.shape != (self.EMBED_DIM,) or
        norm_weight.dtype is not DType.BF16 or norm_weight.tilized):
      raise ValueError("prefill RMSNorm requires a row-major BF16 scale vector")
    keys = tuple((tuple(weight.item_counts[i] for weight in weights),
                  int(core[0] >= self.PROJECTION_NOC_SPLIT_X),
                  tuple((weight.item_starts[i] * weight.tiles_per_item) % weight.banks
                        if weight.banks == 8 else None for weight in weights))
                 for i, core in enumerate(weights[0].cores))
    return specialize(lambda key: self._projection_program(x, projections, count, norm_weight, *key),
                      weights[0].cores, keys)


  def _projection_program(self, x, projections, count, norm_weight, rows, read_noc, rotations):
    input_tiles = projections[0][0].shape[1] // 1024
    row_starts = tuple(Const(weight.name + "_prefill_row_start", weight.item_starts)
                       for weight, _ in projections)
    out_tile = Const("prefill_output_tile", tuple(range(len(projections[0][0].cores))))
    params = tuple(param for (weight, output), start in zip(projections, row_starts)
                   for param in (weight, output.storage, start))
    p = Program(projections[0][0].cores, x.storage, *params, out_tile,
                *((norm_weight,) if norm_weight is not None else ()), fp32_dst=True)
    inputs = p.cb(DType.BF16, depth=count * input_tiles)
    weights = p.cb(DType.BF16, depth=2 * input_tiles)
    scalar = p.cb(DType.BF16, depth=2)
    compact = p.l1(count * 2048, alignment=16)
    # Hold normalized input rows in L1 while streaming the entire weight group.
    operands = p.cb(DType.BF16, depth=2 * input_tiles) if norm_weight is not None else inputs
    for token in p.brisc.range(count):
      for tile in range(input_tiles):
        with p.brisc.scope():
          index, stride = p.brisc.reg(2, exclude=token)
          p.brisc.li(stride, x.stride)
          p.brisc.mul(index, token, stride)
          if tile: p.brisc.addi(index, index, tile)
          p.brisc.noc_at(read_noc).read_into_cb(x.storage, index, operands)
      if norm_weight is not None:
        p.brisc.noc_at(read_noc).read_tiles_into_cb(norm_weight, tuple(range(input_tiles)), operands)
    if norm_weight is not None:
      if input_tiles != self.EMBEDDING_TILES: raise ValueError(f"fused RMSNorm requires {self.EMBED_DIM} features")
      for _ in p.trisc0.range(count):
        for _ in range(2 * input_tiles): p.unpack.move(operands, UnpackTarget.SRCA)
      self._rms_setup_apply_macro(p.sfpu)
      for _ in p.trisc1.range(count):
        p.fpu.copy_a_tiles(dst_tiles=range(2 * input_tiles))
        self._rmsnorm_one_token(p.sfpu)
      for _ in p.trisc2.range(count):
        p.pack.move_tiles(inputs, tiles=tuple(range(input_tiles)))
    expanded = tuple((weight, output.prototype, size)
                     for (weight, output), size in zip(projections, rows))
    self._projection_read_weights(p, expanded, row_starts, rotations, read_noc, weights, input_tiles)
    CB.wait_front(p.trisc0, inputs, count * input_tiles)
    p.unpack.prepare_l1_pair_formats(DType.BF16)
    for _ in p.trisc0.range(sum(rows)):
      CB.wait_front(p.trisc0, weights, input_tiles)
      for token in p.trisc0.range(count):
        for tile in range(input_tiles):
          with p.trisc0.scope():
            address, stride = p.trisc0.reg(2, exclude=token)
            p.trisc0.li(stride, input_tiles * 2048)
            p.trisc0.mul(address, token, stride)
            self._add_constant(p.trisc0, address, inputs.addr + tile * 2048)
            p.unpack.move_l1_pair(weights, address,
              configure_format=False, tile_offset=tile, pop=False)
      CB.pop_front(p.trisc0, weights, input_tiles)
    self._projection_dot_math(p, ((projections[0][0], projections[0][1].prototype, sum(rows) * count),), input_tiles)
    p.pack._configure(scalar, True, True)
    for _ in p.trisc2.range(sum(rows) * count):
      sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
      p.pack._move_acquired(scalar, 0, True, configure=False)
      p.pack._release_dst()
    for (_, output), size in zip(projections, rows):
      self._zero_l1_words(p.ncrisc, compact, count * 512)
      for row in p.ncrisc.range(size):
        for token in p.ncrisc.range(count):
          CB.wait_front(p.ncrisc, scalar)
          with p.ncrisc.scope():
            source, value, target, offset = p.ncrisc.reg(4, exclude=(row, token))
            CB.get_read_ptr(p.ncrisc, scalar, source)
            p.ncrisc.read(value, source, bytes=2)
            self._tile_offset(p.ncrisc, row, target)
            p.ncrisc.slli(offset, token, 11)
            p.ncrisc.add(target, target, offset)
            self._add_constant(p.ncrisc, target, compact)
            p.ncrisc.write(target, value, bytes=2)
          CB.pop_front(p.ncrisc, scalar)
      for token in p.ncrisc.range(count):
        with p.ncrisc.scope():
          tile, stride, offset, source = p.ncrisc.reg(4, exclude=token)
          p.ncrisc.read(tile, p.param_addr(out_tile))
          p.ncrisc.li(stride, output.stride)
          p.ncrisc.mul(offset, token, stride)
          p.ncrisc.add(tile, tile, offset)
          p.ncrisc.slli(source, token, 11)
          self._add_constant(p.ncrisc, source, compact)
          address, coordinate = p.ncrisc.noc_at(1-read_noc)._dram_tile(output.storage, tile)
          p.ncrisc.noc_at(1-read_noc).write(source, address, coordinate, 2048, posted=False)
    return p


  def prefill_swiglu(self, gate, up, output):
    """SwiGLU and compact-to-dense scatter in a single launch."""
    counts = self._token_counts(self.MLP_DIM, len(gate.cores))
    starts, start = [], 0
    for count in counts:
      starts.append(start)
      start += count
    def build(count):
      p = Program(gate.cores, gate, up, output, Const("dense_start", tuple(starts)), fp32_dst=True)
      a, b, result = (p.cb(DType.BF16, depth=1) for _ in range(3))
      p.brisc.noc.read_into_cb(gate, 0, a)
      p.brisc.noc.read_into_cb(up, 0, b)
      p.unpack.move(a, UnpackTarget.SRCA)
      p.unpack.move(b, UnpackTarget.SRCA)
      self._swiglu_math(p)
      p.pack.move(result, tile=0)
      self._scatter_dense(p, result, output, count, read_noc=1)
      return p
    return specialize(build, gate.cores, counts)



class Llama3Decode:
  """Resident-weight, batch-1 decode runtime for a Llama3Kernels configuration."""

  def __init__(self, safetensor_path=None, device_index=0, *, attention_cores=None, kernels=None):
    self.kernels = kernels if kernels is not None else Llama3Kernels()
    safetensor_path = self.kernels.checkpoint if safetensor_path is None else safetensor_path
    attention_cores = self.kernels.attention_cores if attention_cores is None else attention_cores
    if attention_cores not in (8, 16, 32): raise ValueError("attention cores must be 8, 16, or 32")
    self.attention_cores = attention_cores
    from st import Safetensor
    checkpoint = self._checkpoint = Safetensor(safetensor_path)
    self.published_fp8 = checkpoint is not None and "model.layers.0.self_attn.q_proj.input_scale" in checkpoint.tensors
    if self.kernels.WEIGHT_DTYPE.is_fp8 and not self.published_fp8:
      raise ValueError("FP8 mode requires an FP8 checkpoint with stored scales")
    self.checkpoint_scales = {}
    if self.published_fp8:
      if self.kernels.WEIGHT_DTYPE is not DType.FP8: raise ValueError("published FP8 checkpoint requires FP8 weights")
      for name in checkpoint.tensors:
        if name.endswith((".input_scale", ".weight_scale")):
          self.checkpoint_scales[name] = float(np.frombuffer(checkpoint.load(name)[1], dtype="<f4")[0])
    self.safetensor_path = str(safetensor_path)
    self.host_result_read_us = 0.0
    self.host_result_reads = 0
    self.profile = {
      "dram_upload_bytes": 0,
      "weight_prepare_s": 0.0,
      "weight_stage_s": 0.0,
      "upload_wait_s": 0.0,
      "upload_submit_s": 0.0,
    }
    total_started = time.perf_counter()
    started = time.perf_counter()
    self.device = Device(device_index, **({"sysmem_size": 2 << 30} if self.kernels.model == "8b" else {}))
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
    available = device.dram.cores
    if self.kernels.LLAMA_CORES > len(available): raise ValueError("not enough projection workers")
    # Spread projection traffic across both sides of the chip at lower counts.
    cores = tuple(available[index] for index in np.linspace(0, len(available) - 1, self.kernels.LLAMA_CORES, dtype=int))
    global_buffer = lambda name, dtype, shape, axis=0, tilized=True: device.dram.buffer(
      name, dtype, shape, axis=axis, global_address=True, tilized=tilized,
    )

    self._weight_upload_buffers = {}
    def weight_buffer(name, dtype, shape, *, axis, cores):
      # Row ownership is metadata; storage is the checkpoint byte stream.
      storage = global_buffer(name + "_storage", dtype, shape, axis, tilized=False)
      view = replace(storage, name=name, cores=cores)
      self._weight_upload_buffers[view] = storage
      return view

    self.token_history = global_buffer(
      "e2e_token_history", DType.U32, (self.kernels.ROPE_CACHE_TOKENS,), None, tilized=False,
    )
    self.embedding_weight = global_buffer(
      "e2e_embedding_weight", DType.BF16, (self.kernels.VOCAB_SIZE, self.kernels.EMBED_DIM),
      tilized=False,
    )
    # 1B ties the LM head to embeddings; 8B stores an independent projection.
    self.lm_storage = lm_storage = self.embedding_weight if self.kernels.model == "1b" else global_buffer(
      "e2e_lm_storage", DType.BF16, (self.kernels.VOCAB_SIZE, self.kernels.EMBED_DIM), tilized=False)
    self.lm_weight = Buffer(
      "e2e_lm_weight", lm_storage.addr, lm_storage.dtype, lm_storage.shape,
      0, cores, lm_storage.banks, global_address=True,
      tilized=False, dram_endpoints=lm_storage.dram_endpoints,
    )
    self.cos = global_buffer(
      "e2e_rope_cos", DType.BF16, (self.kernels.ROPE_CACHE_TOKENS, self.kernels.HEAD_DIM), None,
      tilized=False,
    )
    self.sin = global_buffer(
      "e2e_rope_sin", DType.BF16, (self.kernels.ROPE_CACHE_TOKENS, self.kernels.HEAD_DIM), None,
      tilized=False,
    )

    self.x_a = global_buffer(
      "e2e_x_a", DType.BF16, (1, self.kernels.EMBED_DIM),
      tilized=False,
    )
    self.x_b = global_buffer(
      "e2e_x_b", DType.BF16, (1, self.kernels.EMBED_DIM),
      tilized=False,
    )
    self.normalized = global_buffer(
      "e2e_normalized", DType.BF16, (1, self.kernels.EMBED_DIM),
      tilized=False,
    )
    self.q_compact = device.dram.buffer(
      "e2e_q_compact", DType.BF16, (self.kernels.LLAMA_CORES, math.ceil(self.kernels.Q_PROJ_DIM / self.kernels.LLAMA_CORES)),
      axis=0, cores=cores,
    )
    self.k_compact = device.dram.buffer(
      "e2e_k_compact", DType.BF16, (self.kernels.LLAMA_CORES, math.ceil(self.kernels.KV_PROJ_DIM / self.kernels.LLAMA_CORES)),
      axis=0, cores=cores,
    )
    self.v_compact = device.dram.buffer(
      "e2e_v_compact", DType.BF16, (self.kernels.LLAMA_CORES, math.ceil(self.kernels.KV_PROJ_DIM / self.kernels.LLAMA_CORES)),
      axis=0, cores=cores,
    )
    self.q_heads = global_buffer(
      "e2e_q_heads", DType.BF16, (self.kernels.Q_HEADS, self.kernels.HEAD_DIM),
    )
    self.k_heads = global_buffer(
      "e2e_k_heads", DType.BF16, (self.kernels.KV_HEADS, self.kernels.HEAD_DIM),
    )
    self.v_heads = global_buffer(
      "e2e_v_heads", DType.BF16, (self.kernels.KV_HEADS, self.kernels.HEAD_DIM),
    )
    self.context = global_buffer(
      "e2e_context", DType.BF16, self.kernels.GQA_CONTEXT_SHAPE,
      tilized=False,
    )
    mlp_compact_shape = (
      self.kernels.LLAMA_CORES, (self.kernels.MLP_DIM + self.kernels.LLAMA_CORES - 1) // self.kernels.LLAMA_CORES,
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
      "e2e_hidden_dense", DType.BF16, (1, self.kernels.MLP_DIM),
      tilized=False,
    )
    self.logits = device.dram.buffer(
      "e2e_logits", DType.BF16,
      (self.kernels.LLAMA_CORES, self.lm_weight.items_per_core),
      axis=0, cores=cores,
    )

    self.layers = []
    for layer in range(self.kernels.LLAMA_LAYERS):
      prefix = f"e2e_l{layer}"
      weights = {
        "input_norm": global_buffer(
          f"{prefix}_input_norm", DType.BF16, (self.kernels.EMBED_DIM,), None, tilized=False,
        ),
        "post_norm": global_buffer(
          f"{prefix}_post_norm", DType.BF16, (self.kernels.EMBED_DIM,), None, tilized=False,
        ),
        "q": weight_buffer(
          f"{prefix}_q", self.kernels.WEIGHT_DTYPE, (self.kernels.Q_PROJ_DIM, self.kernels.EMBED_DIM),
          axis=0, cores=cores,
        ),
        "k": weight_buffer(
          f"{prefix}_k", self.kernels.WEIGHT_DTYPE, (self.kernels.KV_PROJ_DIM, self.kernels.EMBED_DIM),
          axis=0, cores=cores,
        ),
        "v": weight_buffer(
          f"{prefix}_v", self.kernels.WEIGHT_DTYPE, (self.kernels.KV_PROJ_DIM, self.kernels.EMBED_DIM),
          axis=0, cores=cores,
        ),
        "o": weight_buffer(
          f"{prefix}_o", self.kernels.WEIGHT_DTYPE, (self.kernels.EMBED_DIM, self.kernels.Q_PROJ_DIM),
          axis=0, cores=cores,
        ),
        "gate": weight_buffer(
          f"{prefix}_gate", self.kernels.WEIGHT_DTYPE, (self.kernels.MLP_DIM, self.kernels.EMBED_DIM),
          axis=0, cores=cores,
        ),
        "up": weight_buffer(
          f"{prefix}_up", self.kernels.WEIGHT_DTYPE, (self.kernels.MLP_DIM, self.kernels.EMBED_DIM),
          axis=0, cores=cores,
        ),
        "down": weight_buffer(
          f"{prefix}_down", self.kernels.WEIGHT_DTYPE, (self.kernels.EMBED_DIM, self.kernels.MLP_DIM),
          axis=0, cores=cores,
        ),
      }
      key_cache = global_buffer(
        f"{prefix}_key_cache", self.kernels.ATTENTION_DTYPE, self.kernels.KV_CACHE_STORAGE_SHAPE,
      )
      value_cache = global_buffer(
        f"{prefix}_value_cache", self.kernels.ATTENTION_DTYPE, self.kernels.KV_CACHE_STORAGE_SHAPE,
      )
      self.layers.append({
        "weights": weights,
        "key_cache": key_cache,
        "value_cache": value_cache,
      })
    self.final_norm = global_buffer(
      "e2e_final_norm", DType.BF16, (self.kernels.EMBED_DIM,), None, tilized=False,
    )

  def _upload(self, buffer, tensor):
    buffer = self._weight_upload_buffers.get(buffer, buffer)
    started = time.perf_counter()
    buffer.check_safetensor(self._checkpoint.info(tensor))
    if not buffer._raw_global:
      raise ValueError("model uploads require exact global row-major storage")
    self.profile["weight_prepare_s"] += time.perf_counter() - started
    self._uploads.write_from(
      buffer, lambda target, offset: self._checkpoint.readinto(tensor, target, offset),
    )
    self.profile["dram_upload_bytes"] += buffer.size

  def _stage_upload(self, buffer, data, *, physical=False):
    if not physical and not buffer._raw_global:
      raise ValueError("model uploads require exact global row-major storage")
    if len(data) != buffer.size:
      raise ValueError("model upload byte length does not match its storage")
    self._uploads.write(buffer, data)
    self.profile["dram_upload_bytes"] += buffer.size

  def _upload_weights(self):
    with self.device.upload_stream() as uploads:
      self._uploads = uploads
      try:
        self._stage_weights()
      finally:
        del self._uploads
    self.profile["weight_stage_s"] = uploads.copy_s
    self.profile["upload_wait_s"] = uploads.wait_s
    self.profile["upload_submit_s"] = uploads.submit_s

  def _stage_weights(self):
    self._upload(self.embedding_weight, "model.embed_tokens.weight")

    if self.lm_storage is not self.embedding_weight:
      self._upload(self.lm_storage, "lm_head.weight")

    started = time.perf_counter()
    cos_values, sin_values = self.kernels.rope_table()
    cos_data = self.kernels._bf16_rne_bytes(cos_values)
    sin_data = self.kernels._bf16_rne_bytes(sin_values)
    self.profile["weight_prepare_s"] += time.perf_counter() - started
    self._stage_upload(self.cos, cos_data)
    self._stage_upload(self.sin, sin_data)
    del cos_values, sin_values

    cache_zeros = bytes(
      math.prod(self.kernels.KV_CACHE_STORAGE_SHAPE) * self.kernels.ATTENTION_DTYPE.itemsize,
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
      # A cleared cache has identical bytes in every layout.
      self._stage_upload(layer["key_cache"], cache_zeros, physical=True)
      self._stage_upload(layer["value_cache"], cache_zeros, physical=True)
    self._upload(self.final_norm, "model.norm.weight")

  def _build_programs(self):
    self._create_programs()
    self.device.cache_kernels(self.programs.values())
    self._capture_decode_trace()

  def _create_programs(self):
    weights = self.layers[0]["weights"]
    o_projection = self.kernels._decode_fused_projections(
      self.context, ((weights["q"], self.q_compact),),
      residual=self.x_a, dense_output=self.x_b,
    )
    self.programs = {
      "embedding": self.kernels.decode_embedding(
        self.token_history, self.embedding_weight, self.x_a,
      ),
      "o": o_projection,
      "qkv": self.kernels._decode_fused_projections(
        self.x_a, ((weights["q"], self.q_compact),
                   (weights["k"], self.k_compact),
                   (weights["v"], self.v_compact)),
        norm_weight=weights["input_norm"],
      ),
      "attention": self.kernels.gqa_attention_fused(
        self.q_heads, self.layers[0]["key_cache"],
        self.layers[0]["value_cache"], self.context,
        rope_inputs=(self.q_compact, self.k_compact, self.v_compact, self.cos, self.sin),
        attention_cores=self.attention_cores,
      ),
      "gate": self.kernels._decode_fused_projections(self.x_b, (
        (weights["gate"], self.gate), (weights["up"], self.up),
      ), swiglu_output=self.hidden_dense, norm_weight=weights["post_norm"]),
      "down": self.kernels._decode_fused_projections(
        self.hidden_dense, ((weights["down"], self.q_compact),),
        residual=self.x_b, dense_output=self.x_a,
      ),
      "lm": self.kernels._decode_fused_projections(
        self.x_a, ((self.lm_weight, self.logits),), norm_weight=self.final_norm,
      ),
      "argmax": self.kernels.decode_argmax(
        self.logits, self.token_history,
        self.device.cq.noc + self.device.cq.live,
      ),
    }
    self.o_projection_input = o_projection.param(
      f"{self.context.name}_decode_token",
    )
    self.context_projection_input = Buffer(
      "e2e_context_decode_token", self.context.addr, self.context.dtype,
      (self.kernels.EMBED_DIM,), None, (self.context.cores[0],), self.context.banks,
      global_address=True, tilized=self.context.tilized,
      dram_endpoints=self.context.dram_endpoints,
    )


  def _capture_decode_trace(self):
    self._queue("embedding")
    for layer in range(self.kernels.LLAMA_LAYERS):
      self._queue_layer(layer, 0)
    self._queue("lm")
    self._queue("argmax")
    self.decode_launch_count = len(self.device.program_queue)
    self.decode_trace = self.device.capture_trace((
      "token_pos", "write_pos", "write_token", "start_pos",
      "kv_blocks", "valid_columns",
    ))


  def prefill(self, tokens, *, chunk_size=4, append=True):
    """Consume a BS=1 prompt and publish its first greedy continuation.

    Starts a new sequence at position zero. Decode can continue at len(tokens)
    when append=True. Returns (next_token, prefill_wall_us).
    """
    started = time.perf_counter_ns()
    if self.kernels.model != "8b" or self.kernels.dtype != "bf16":
      raise ValueError("chunked prefill supports 8B BF16 only")
    engine = getattr(self, "_prefill", None)
    if engine is None:
      engine = self._prefill = Prefill(self, chunk_size)
    elif chunk_size != engine.chunk_size:
      raise ValueError("prefill chunk size is fixed for the lifetime of a runtime")
    token, _ = engine.run(tokens, append=append)
    wall_us = (time.perf_counter_ns() - started) / 1e3
    engine.profile["wall_us"] = wall_us
    return token, wall_us


  def _queue(self, name, replacements=(), constants=None):
    params = {source: target for source, target in replacements}
    if constants: params.update(constants)
    self.device.queue(self.programs[name], params=params)

  def _projection_scales(self, layer, names):
    if not getattr(self, "published_fp8", False): return {}
    prefixes = [f"model.layers.{layer}.{name}" for name in names]
    inputs = [self.checkpoint_scales[f"{name}.input_scale"] for name in prefixes]
    if any(value != inputs[0] for value in inputs):
      raise ValueError("fused projections require identical calibrated input scales")
    values = {"input_scale": 1 / inputs[0]}
    values.update({f"output_scale_{i}": inputs[0] * self.checkpoint_scales[f"{name}.weight_scale"] for i, name in enumerate(prefixes)})
    return {f"{name}_{part}": word for name, value in values.items() for part, word in enumerate(self.kernels._sfpu_float_words(LReg.L6, value))}

  def _queue_layer(self, index, position):
    layer = self.layers[index]
    weights = layer["weights"]
    template = self.layers[0]
    template_weights = template["weights"]
    blocks = position // self.kernels.KV_CACHE_TOKEN_BLOCK + 1
    tail = position % self.kernels.KV_CACHE_TOKEN_BLOCK + 1

    self._queue("qkv", (
      (template_weights["input_norm"], weights["input_norm"]),
      (template_weights["q"], weights["q"]),
      (template_weights["k"], weights["k"]),
      (template_weights["v"], weights["v"]),
    ), self._projection_scales(index, ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj")))
    self._queue("attention", (
      (template["key_cache"], layer["key_cache"]),
      (template["value_cache"], layer["value_cache"]),
    ), {"start_pos": position, "kv_blocks": blocks, "valid_columns": tail})
    self._queue("o", (
      (self.o_projection_input, self.context_projection_input),
      (template_weights["q"], weights["o"]),
    ), self._projection_scales(index, ("self_attn.o_proj",)))
    self._queue("gate", (
      (template_weights["post_norm"], weights["post_norm"]),
      (template_weights["gate"], weights["gate"]),
      (template_weights["up"], weights["up"]),
    ), self._projection_scales(index, ("mlp.gate_proj", "mlp.up_proj")))
    self._queue("down", ((template_weights["down"], weights["down"]),), self._projection_scales(index, ("mlp.down_proj",)))

  def load_tokens(self, tokens, *, start=0):
    """Update token history from start, preserving the cached prefix in DRAM."""
    tokens = np.asarray(tokens)
    if tokens.ndim != 1 or tokens.dtype.kind not in "iu":
      raise ValueError("prompt tokens must be a one-dimensional integer sequence")
    if not 0 < len(tokens) < self.kernels.ROPE_CACHE_TOKENS:
      raise ValueError(
        f"prompt token count must be in 1..{self.kernels.ROPE_CACHE_TOKENS - 1}",
      )
    if np.any(tokens < 0) or np.any(tokens >= self.kernels.VOCAB_SIZE):
      raise ValueError(f"prompt tokens must be in 0..{self.kernels.VOCAB_SIZE - 1}")
    if not 0 <= start < len(tokens): raise ValueError("start must index a prompt token")
    self.device.run(timeout=30.0)
    history = self.token_history
    data = tokens[start:].astype("<u4", copy=False).tobytes()
    # Token IDs are flat uint32 values in bank-interleaved 4 KiB pages.
    with TLBWindow(self.device.pcie.fd, self.device.pcie.dram_endpoints[0][0]) as window:
      for page in range(start // 1024, (len(tokens) + 1023) // 1024):
        address = history.addr + page // history.banks * history.tile_size
        base = address & -TLBWindow.SIZE
        window.target(base, self.device.pcie.dram_endpoints[page % history.banks][0])
        position, end = max(start, page * 1024), min(len(tokens), (page + 1) * 1024)
        offset = (position % 1024) * 4
        window.write(address - base + offset, data[(position - start) * 4:(end - start) * 4])


  def decode(self, position, *, logits=True, append=True):
    """Consume one token at ``position`` and optionally return greedy next ID."""
    if not 0 <= position < self.kernels.ROPE_CACHE_TOKENS - 1:
      raise ValueError(
        f"decode position must be in 0..{self.kernels.ROPE_CACHE_TOKENS - 2}",
      )
    started = time.perf_counter_ns()
    self.decode_trace.replay({
      "token_pos": position,
      "write_pos": position + 1,
      "write_token": int(append),
      "start_pos": position,
      "kv_blocks": position // self.kernels.KV_CACHE_TOKEN_BLOCK + 1,
      "valid_columns": position % self.kernels.KV_CACHE_TOKEN_BLOCK + 1,
    }, timeout=30.0)
    wall_us = (time.perf_counter_ns() - started) / 1e3

    if not logits: return None, wall_us
    return self._read_token(position + 1), wall_us

  def _read_token(self, write_position):
    read_started = time.perf_counter_ns()
    live = self.device.cq.live + write_position * 16
    token, = struct.unpack("<I", self.device.pcie.sysmem.read(live, 4))
    self.host_result_read_us += (
      time.perf_counter_ns() - read_started
    ) / 1e3
    self.host_result_reads += 1
    return token


  def close(self):
    if getattr(self, "device", None) is not None:
      self.device.close()
      self.device = None



class SequenceBuffer:
  """Bank-aligned token slabs with byte-identical decode buffer views."""
  def __init__(self, device, prototype, capacity):
    self.prototype = prototype
    self.stride = math.ceil(prototype.physical_tiles / prototype.banks) * prototype.banks
    self.storage = device.dram.buffer(
      "prefill_" + prototype.name, prototype.dtype,
      (capacity, self.stride * 1024), axis=0, global_address=True,
      tilized=False,
    )
    self.capacity = capacity

  def view(self, index, prototype=None):
    if not 0 <= index < self.capacity: raise ValueError("token outside scratch capacity")
    prototype = self.prototype if prototype is None else prototype
    return replace(prototype, addr=self.storage.addr +
                   index * self.stride // prototype.banks * prototype.tile_size)



class Prefill:
  """Bounded scratch and layer-major prompt scheduling for one decode runtime."""
  def __init__(self, runtime, chunk_size=4):
    if type(chunk_size) is not int or not 1 <= chunk_size <= 8:
      raise ValueError("prefill chunk size must be in 1..8")
    self.runtime, self.chunk_size = runtime, chunk_size
    self.slabs = {getattr(runtime, name).addr: SequenceBuffer(runtime.device, getattr(runtime, name), chunk_size)
                  for name in ("x_a", "x_b", "q_compact", "k_compact", "v_compact",
                               "context", "gate", "up", "hidden_dense")}
    self.swiglu = runtime.kernels.prefill_swiglu(runtime.gate, runtime.up, runtime.hidden_dense)
    self.projections = {}
    self.profile = {}
    self._cached = False
    self.resident = {}
    for program in runtime.programs.values():
      launch = copy(program)
      launch._kernels = {
        core: {role: RV32().jal(R.ZERO, address - TensixL1.WORKER_TEXT_BASE[role]).to_bytes(4, "little")
               for role, address in zip(KERNEL_ROLES, entries)}
        for core, entries in runtime.device._resident_programs[program].items()
      }
      self.resident[program] = launch

  def _projection(self, name, count):
    key = name, count
    if key not in self.projections:
      r = self.runtime
      names = ("q", "k", "v") if name == "qkv" else ("gate", "up")
      source = r.x_a if name == "qkv" else r.x_b
      norm = "input_norm" if name == "qkv" else "post_norm"
      self.projections[key] = r.kernels.prefill_projections(self.slabs[source.addr], tuple(
        (r.layers[0]["weights"][part], self.slabs[getattr(r, part + "_compact" if name == "qkv" else part).addr])
        for part in names), count, r.layers[0]["weights"][norm])
    return self.projections[key]

  def _cache(self):
    if self._cached: return
    r = self.runtime
    programs = [self._projection(name, count)
                for count in range(1, self.chunk_size + 1)
                for name in ("qkv", "gate_up")]
    programs += [self.swiglu, *self.resident.values()]
    # Keep decode's resident kernels/templates intact. Prefill's larger family
    # of sequence variants lives in the existing DRAM command-record cache.
    if r.device._kernel_cache_buffer is None:
      r.device.cache_programs(programs)
    self._cached = True

  def _queue(self, program, token, replacements=(), constants=None):
    program = self.resident.get(program, program)
    params = dict(replacements)
    # Apply explicit bindings first, then move activation aliases into their
    # token slab. Attention and O projection expose differently named views.
    for source in program.params.values():
      target = params.get(source, source)
      if isinstance(target, Buffer) and target.addr in self.slabs:
        params[source] = self.slabs[target.addr].view(token, target)
    if constants: params.update(constants)
    self.runtime.device.queue(program, params=params, report=False)

  def run(self, tokens, *, append=True):
    r = self.runtime
    started = time.perf_counter()
    # load_tokens validates before modifying device state.
    r.load_tokens(tokens)
    count = len(tokens)
    self._cache()
    execution_started = time.perf_counter()
    launches = 0
    template = r.layers[0]
    tw = template["weights"]
    for start in range(0, count, self.chunk_size):
      live = min(self.chunk_size, count - start)
      for token in range(live):
        self._queue(r.programs["embedding"], token, constants={"token_pos": start + token})
      for layer in r.layers:
        w = layer["weights"]
        r.device.queue(self._projection("qkv", live),
          params={tw[name]: w[name] for name in ("q", "k", "v", "input_norm")}, report=False)
        for token in range(live):
          position = start + token
          self._queue(r.programs["attention"], token,
            ((template["key_cache"], layer["key_cache"]), (template["value_cache"], layer["value_cache"])),
            {"start_pos": position, "kv_blocks": position // 32 + 1, "valid_columns": position % 32 + 1})
          self._queue(r.programs["o"], token,
            ((r.o_projection_input, r.context_projection_input), (tw["q"], w["o"])))
        r.device.queue(self._projection("gate_up", live),
          params={tw[name]: w[name] for name in ("gate", "up", "post_norm")}, report=False)
        for token in range(live):
          self._queue(self.swiglu, token)
          self._queue(r.programs["down"], token, ((tw["down"], w["down"]),))
        # Bound CQ staging and keep kernel uploads out of a giant host queue.
        launches += len(r.device.program_queue)
        r.device.run(timeout=30.0)
      if start + live == count:
        self._queue(r.programs["lm"], live - 1)
        self._queue(r.programs["argmax"], live - 1,
                    constants={"write_pos": count, "write_token": int(append)})
        launches += 2
        r.device.run(timeout=30.0)
    token = r._read_token(count)
    elapsed = (time.perf_counter() - started) * 1e6
    self.profile = {"tokens": count, "chunk_size": self.chunk_size,
                    "launches": launches, "wall_us": elapsed,
                    "execution_us": (time.perf_counter() - execution_started) * 1e6}
    return token, elapsed



def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--model', choices=('1b', '8b'), default='1b')
  parser.add_argument('--dtype', choices=('bf16', 'fp8'), default='bf16',
                      help='checkpoint weight format; FP8 supports 8B only')
  parser.add_argument('--prompt', default='The capital of France is',
                      help='generate from this prompt (an empty prompt is valid)')
  parser.add_argument('--steps', type=int, help='generation cap; default runs until EOS/context limit')
  parser.add_argument('--safetensor', help='checkpoint file/directory; defaults to weights/llama3-<model>[-<dtype>]')
  parser.add_argument('--tokenizer', help='tokenizer directory; defaults to the checkpoint path')
  parser.add_argument('--device', type=int, default=0, help='Tenstorrent device index (default: 0)')
  parser.add_argument('--attention-cores', type=int, choices=(8, 16, 32),
                      help='default: 16 for 1B, 32 for 8B')
  parser.add_argument('--prefill', action='store_true', help='ingest the prompt with chunked 8B BF16 prefill')
  parser.add_argument('--prefill-chunk-size', type=int, choices=range(1, 9), default=4)
  parser.add_argument('--profile', action='store_true', help='print startup, upload, device, and host timing')
  args = parser.parse_args(argv)
  try:
    kernels = Llama3Kernels(args.model, args.dtype)
    if args.prefill and (args.model != '8b' or args.dtype != 'bf16'):
      raise ValueError('chunked prefill supports 8B BF16 only')
    if args.steps is not None and args.steps < 1:
      raise ValueError('steps must be positive')
  except ValueError as error:
    parser.error(str(error))
  kernels.run_decode_e2e(args.prompt, args.steps, args.safetensor, args.tokenizer,
    profile=args.profile, device_index=args.device, attention_cores=args.attention_cores,
    prefill=args.prefill, prefill_chunk_size=args.prefill_chunk_size)


if __name__ == '__main__':
  main()
