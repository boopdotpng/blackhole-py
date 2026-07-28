"""Llama 3.2 1B row-major decode kernels.

This file starts with K0, the single-core embedding lookup + RMSNorm kernel:

  token_id ──gather──> residual_x
                     └──RMSNorm(gamma)──> normalized_x

All DRAM tensors use dense row-major storage.  A 2,048-element BF16 vector is
exactly 4,096 bytes, so K0 views it as two contiguous 1,024-element pages while
it is inside Tensix.  Those pages use the ordinary 32x32 tile datapath, but no
tilization or untilization occurs and there is no vector tail in this kernel.

Core and engine split
---------------------

  launch: 1 worker core
  BRISC:  read the token ID, gather two embedding pages, read two gamma pages
  NCRISC: write the gathered pages to residual_x; later drain normalized_x
  TRISC0: unpack x*1 and x*gamma pairs, or experimental x*x GAPOOL inputs
  TRISC1: HiFi2 FPU multiplies/GAPOOL; SFPU scalar work
  TRISC2: pack two normalized BF16 pages

The wide elementwise products are deliberately on the FPU.  The default
bring-up path uses SFPU reduction; ``--reduction gapool`` selects the current
experimental Dst-reuse GAPOOL port.  Both complete on hardware, but neither
full RMS path is numerically accepted yet; the hardware runner reports and
rejects their current error.

Without arguments this module only lowers on the CPU.  Device access requires
the explicit ``--hardware`` flag.
"""

from dataclasses import dataclass
import argparse
import statistics
import struct
import time

import numpy as np

from device import Device
from fw.consts import TensixMMIO
from isa import Tensix as TT
from pcie import P100_WORKER_CORES
from program import Buffer, Dram, Program
from ttk import DType
from ttk import l1
from ttk.cb import CB
from ttk.sfpu import LaneConfig, LReg, SfpuFormat, SfpuProgram
from ttk.sync import Sem, SemWait, Stall, Wait, sem_wait, stall


VOCAB_SIZE = 128256
EMBED_DIM = 2048
PAGE_ELEMENTS = 1024
VECTOR_PAGES = EMBED_DIM // PAGE_ELEMENTS
RMS_EPS = 1e-5
DEVICE_HZ = 1_350_000_000
K0_CORES = (P100_WORKER_CORES[0],)

assert EMBED_DIM % PAGE_ELEMENTS == 0
assert VECTOR_PAGES == 2


@dataclass(frozen=True)
class Kernel0Buffers:
  """Dense row-major DRAM buffers consumed and produced by K0."""

  token_id: Buffer
  embedding_weight: Buffer
  gamma: Buffer
  residual_x: Buffer
  normalized_x: Buffer


def allocate_kernel0_buffers(dram: Dram) -> Kernel0Buffers:
  """Allocate K0's global tensors without touching the device."""
  options = {"global_address": True, "cores": K0_CORES}
  return Kernel0Buffers(
    token_id=dram.buffer("token_id", DType.U32, (1,), **options),
    embedding_weight=dram.buffer(
      "embedding_weight", DType.BF16, (VOCAB_SIZE, EMBED_DIM), **options,
    ),
    gamma=dram.buffer("gamma", DType.BF16, (EMBED_DIM,), **options),
    residual_x=dram.buffer(
      "residual_x", DType.BF16, (EMBED_DIM,), **options,
    ),
    normalized_x=dram.buffer(
      "normalized_x", DType.BF16, (EMBED_DIM,), **options,
    ),
  )


def _float_words(register, value):
  bits = struct.unpack("<I", struct.pack("<f", float(value)))[0]
  return (
    TT.TTSFPLOADI(register, 10, bits & 0xffff),
    TT.TTSFPLOADI(register, 8, bits >> 16),
  )


def _sfpu_add(words, left, right, output):
  words.extend((
    TT.TTSFPADD(LReg.ONE, left, right, output, 0),
    TT.TTSFPNOP(),
  ))


def _sfpu_mul(words, left, right, output, modifier=0):
  words.extend((
    TT.TTSFPMUL(left, right, LReg.ZERO, output, modifier),
    TT.TTSFPNOP(),
  ))


def _rms_square_accumulate(*, reset):
  """Accumulate one FP32 square tile into persistent SFPU lanes."""
  setup = _float_words(LReg.L7, 0.0) if reset else ()
  return SfpuProgram(tuple(setup), (
    TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0),
    TT.TTSFPMAD(LReg.L0, LReg.ONE, LReg.L7, LReg.L7, 0),
  ))


def _legacy_rms_square_accumulate(*, reset):
  """Square and accumulate an FP32 x tile entirely in SFPU."""
  setup = _float_words(LReg.L7, 0.0) if reset else ()
  return SfpuProgram(tuple(setup), (
    TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0),
    TT.TTSFPMAD(LReg.L0, LReg.L0, LReg.L7, LReg.L7, 0),
  ))


def _rms_finalize_scale():
  """Reduce 2,048 squares and leave rsqrt(mean(square) + eps) in L0."""
  words = [TT.TTSFPMOV(0, LReg.L7, LReg.L0, 0)]

  # Reduce each independent eight-lane SFPU row to a broadcast sum.
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3),
        TT.TTSFPNOP(),
      ))
    _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)

  # Combine the four SFPU rows.  The result remains broadcast in L0.
  for register in (LReg.L1, LReg.L2, LReg.L3):
    words.append(TT.TTSFPMOV(0, LReg.L0, register, 0))
  words.append(TT.TTSFPTRANSP(0, 0, 0, 0))
  for register in (LReg.L1, LReg.L2, LReg.L3):
    _sfpu_add(words, LReg.L0, register, LReg.L0)

  _append_rms_rsqrt(words)
  return SfpuProgram((), tuple(words))


def _append_rms_rsqrt(words):
  """Turn a scalar sum in L0 into reciprocal RMS, retaining it in L0."""
  words.extend(_float_words(LReg.L4, 1.0 / EMBED_DIM))
  words.append(TT.TTSFPMUL(
    LReg.L0, LReg.L4, LReg.ZERO, LReg.L0, 0,
  ))
  words.extend(_float_words(LReg.L4, RMS_EPS))
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
  words.append(TT.TTSFPMUL(
    y, temporary, LReg.ZERO, temporary, 1,
  ))
  words.extend(_float_words(c1, 2.2825186))
  words.extend(_float_words(c2, 2.2533049))
  _sfpu_add(words, c2, temporary, c2)
  words.extend((
    TT.TTSFPMAD(temporary, c2, c1, temporary, 0),
    TT.TTSFPNOP(),
  ))
  _sfpu_mul(words, y, temporary, y)
  _sfpu_mul(words, x, y, temporary)
  _sfpu_mul(words, y, temporary, temporary, 1)
  words.append(TT.TTSFPADD(
    LReg.ONE, LReg.ONE, temporary, temporary, 0,
  ))
  words.extend(_float_words(half, 0.5))
  _sfpu_mul(words, y, half, half)
  words.append(TT.TTSFPMAD(
    temporary, half, y, LReg.L0, 0,
  ))


def _gapool_finalize_scale():
  """Broadcast GAPOOL's scalar sum and retain reciprocal RMS in L0."""
  words = [TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0)]
  words.extend(_gapool_rsqrt_from_l0().words)
  return SfpuProgram((), tuple(words))


def _gapool_rsqrt_from_l0():
  """Broadcast a scalar in L0, then convert it to reciprocal RMS."""
  words = []
  for rotations in (4, 2, 1):
    words.append(TT.TTSFPMOV(0, LReg.L0, LReg.L1, 0))
    for _ in range(rotations):
      words.extend((
        TT.TTSFPSHFT2(0, LReg.L1, LReg.L1, 3),
        TT.TTSFPNOP(),
      ))
    _sfpu_add(words, LReg.L0, LReg.L1, LReg.L0)
  for register in (LReg.L1, LReg.L2, LReg.L3):
    words.append(TT.TTSFPMOV(0, LReg.L0, register, 0))
  words.append(TT.TTSFPTRANSP(0, 0, 0, 0))
  for register in (LReg.L1, LReg.L2, LReg.L3):
    _sfpu_add(words, LReg.L0, register, LReg.L0)

  _append_rms_rsqrt(words)
  return SfpuProgram((), tuple(words))


def _fill_dst(value):
  """Fill the current FP32 Dst tile with a scalar for Dst-reuse setup."""
  return SfpuProgram(_float_words(LReg.L0, value), (
    TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0),
  ))


def _fill_dst_rc_custom(sfpu, value):
  """Emit tt-metal's RC_custom two-vector FP32 fill exactly."""
  for word in _float_words(LReg.L0, value):
    sfpu._issue(word)
  for _ in range(2):
    sfpu._issue(TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0))
    sfpu._issue(TT.TTINCRWC(0, 2, 0, 0))
  sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _rms_apply_live_scale():
  """Multiply one 32-lane FP32 Dst footprint by the live L0 scale."""
  return SfpuProgram((), (
    TT.TTSFPLOAD(LReg.L1, SfpuFormat.FP32, 7, 0),
    TT.TTSFPMUL(LReg.L1, LReg.L0, LReg.ZERO, LReg.L1, 0),
    TT.TTSFPNOP(),
    TT.TTSFPSTORE(LReg.L1, SfpuFormat.FP32, 7, 0),
  ))


def _rms_apply_weight_pair():
  """Apply live RMS scale and gamma from two Dst tiles ahead."""
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


def _setup_apply_macro(sfpu):
  sfpu._issue(TT.TTSFPCONFIG(
    LaneConfig().word(), LReg.LANE_X2, 1,
  ))
  sfpu._issue(TT.TTSFPNOP())
  sfpu._issue(TT.TTSFPMUL(
    LReg.L0, LReg.L0, LReg.ZERO, LReg.CONFIG0, 0,
  ))
  sfpu._issue(TT.TTSFPCONFIG(0x8400, 4, 1))
  sfpu._issue(TT.TTSFPCONFIG(0x0f00, 8, 1))


def _map_acquired(sfpu, program, *, iterations=8):
  """Map an SFPU program while retaining ownership of FP32 Dst."""
  start, body = sfpu._prepare(program)
  for word in program.setup_words:
    sfpu._issue(word)
  if start is not None:
    sfpu._configure_replay_mop(start, len(body), iterations)
  sfpu._run_faces(start, body, 4, iterations)
  sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _select_dst_tile(sfpu, tile):
  sfpu._configure_dst(tile, LaneConfig())
  stall(sfpu.k, Stall.SFPU, Wait.MATH)


def _begin_rms(sfpu):
  """Reduce square tiles Dst[0:2], preserving reciprocal RMS in L0."""
  sem_wait(
    sfpu.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
    Stall.SYNC | Stall.MATH | Stall.SFPU,
  )
  _select_dst_tile(sfpu, 0)
  _map_acquired(sfpu, _rms_square_accumulate(reset=True))
  _select_dst_tile(sfpu, 1)
  _map_acquired(sfpu, _rms_square_accumulate(reset=False))
  for word in _rms_finalize_scale().words:
    sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _finish_rms(sfpu):
  """Scale FP32 x*gamma tiles Dst[0:2] and publish them to TRISC2."""
  apply_scale = _rms_apply_live_scale()
  for tile in range(VECTOR_PAGES):
    _select_dst_tile(sfpu, tile)
    _map_acquired(sfpu, apply_scale)
  sfpu.publish()


def _legacy_rms(sfpu):
  """Tested decode RMS schedule: x/gamma in Dst[0:4], all math in SFPU."""
  sem_wait(
    sfpu.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
    Stall.SYNC | Stall.MATH | Stall.SFPU,
  )
  _select_dst_tile(sfpu, 0)
  _map_acquired(sfpu, _legacy_rms_square_accumulate(reset=True))
  _select_dst_tile(sfpu, 1)
  _map_acquired(sfpu, _legacy_rms_square_accumulate(reset=False))
  for word in _rms_finalize_scale().words:
    sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)

  apply_weight = _rms_apply_weight_pair()
  _select_dst_tile(sfpu, 0)
  _map_acquired(sfpu, apply_weight, iterations=4)
  _select_dst_tile(sfpu, 1)
  _map_acquired(sfpu, apply_weight, iterations=4)
  sfpu.publish()


def _legacy_begin_rms(sfpu):
  """Square/reduce two x tiles in SFPU and retain reciprocal RMS in L0."""
  sem_wait(
    sfpu.k, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
    Stall.SYNC | Stall.MATH | Stall.SFPU,
  )
  _select_dst_tile(sfpu, 0)
  _map_acquired(sfpu, _legacy_rms_square_accumulate(reset=True))
  _select_dst_tile(sfpu, 1)
  _map_acquired(sfpu, _legacy_rms_square_accumulate(reset=False))
  for word in _rms_finalize_scale().words:
    sfpu._issue(word)
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _gapool_square_sum(p):
  """Leave the two-page sum(x*x) in SFPU L0."""
  for page in range(VECTOR_PAGES):
    p.fpu.binary("mul", dst_tile=page)

  # Page 0: materialize the unit scaler in Dst0, move it to SrcB, and reduce
  # into scratch Dst2 so neither the source tile nor scaler staging aliases.
  p.fpu.gapool_reduce_init()
  p.fpu.move_dst_tile_to_srca(dst_tile=0)
  _select_dst_tile(p.sfpu, 0)
  _fill_dst_rc_custom(p.sfpu, 1.0)
  p.fpu.move_dst_tile_to_srcb(dst_tile=0)
  _select_dst_tile(p.sfpu, 2)
  _fill_dst_rc_custom(p.sfpu, 0.0)
  p.fpu.gapool_reduce_column(dst_tile=2)
  p.fpu.gapool_reduce_scalar(dst_tile=2, clear_dvalid=False)
  _select_dst_tile(p.sfpu, 2)
  p.sfpu._issue(TT.TTSFPLOAD(LReg.L7, SfpuFormat.FP32, 7, 0))

  # Page 1: rebuild both source banks.  Page 0's scalar remains live in L7,
  # so Dst0 can safely be reused for the unit scaler.
  p.fpu.gapool_reduce_restart()
  p.fpu.gapool_reduce_init()
  p.fpu.move_dst_tile_to_srca(dst_tile=1)
  _select_dst_tile(p.sfpu, 0)
  _fill_dst_rc_custom(p.sfpu, 1.0)
  p.fpu.move_dst_tile_to_srcb(dst_tile=0)
  _select_dst_tile(p.sfpu, 3)
  _fill_dst_rc_custom(p.sfpu, 0.0)
  p.fpu.gapool_reduce_column(dst_tile=3)
  p.fpu.gapool_reduce_scalar(dst_tile=3)
  _select_dst_tile(p.sfpu, 3)
  p.sfpu._issue(TT.TTSFPLOAD(LReg.L0, SfpuFormat.FP32, 7, 0))
  add_words = []
  _sfpu_add(add_words, LReg.L0, LReg.L7, LReg.L0)
  for word in add_words:
    p.sfpu._issue(word)
  stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _check_kernel0_buffers(buffers):
  expected = (
    ("token_id", buffers.token_id, DType.U32, (1,)),
    (
      "embedding_weight", buffers.embedding_weight, DType.BF16,
      (VOCAB_SIZE, EMBED_DIM),
    ),
    ("gamma", buffers.gamma, DType.BF16, (EMBED_DIM,)),
    ("residual_x", buffers.residual_x, DType.BF16, (EMBED_DIM,)),
    ("normalized_x", buffers.normalized_x, DType.BF16, (EMBED_DIM,)),
  )
  for name, buffer, dtype, shape in expected:
    if buffer.dtype is not dtype or buffer.shape != shape:
      raise ValueError(
        f"{name} must be {dtype.name}{shape}, got "
        f"{buffer.dtype.name}{buffer.shape}",
      )
    if not buffer.global_address:
      raise ValueError(f"{name} must use one global row-major page namespace")
  if any(buffer.cores != K0_CORES for _, buffer, _, _ in expected):
    raise ValueError(f"all K0 buffers must be owned by core {K0_CORES[0]}")


def _write_dense_vector_from_cb(p, source_cb, output):
  """Write four dense 512-element chunks without tilization."""
  chunk_bytes = 512 * output.dtype.itemsize
  CB.wait_front(p.ncrisc, source_cb, VECTOR_PAGES)
  with p.ncrisc.scope():
    source_base = p.ncrisc.reg()
    CB.get_read_ptr(p.ncrisc, source_cb, source_base)
    with p.ncrisc.noc.transaction() as transaction:
      for logical_chunk in range(4):
        source_chunk = logical_chunk
        page, within_page = divmod(logical_chunk, 2)
        with p.ncrisc.scope():
          target, coordinate = p.ncrisc.noc._dram_tile(output, page)
          source = p.ncrisc.reg(
            exclude=(source_base, target, coordinate),
          )
          source_offset = source_chunk * chunk_bytes
          if source_offset <= 2047:
            p.ncrisc.addi(source, source_base, source_offset)
          else:
            offset = p.ncrisc.reg(
              exclude=(source_base, target, coordinate, source),
            )
            p.ncrisc.li(offset, source_offset)
            p.ncrisc.add(source, source_base, offset)
          if within_page:
            p.ncrisc.addi(target, target, chunk_bytes)
          transaction.write(
            source, target, coordinate, chunk_bytes, posted=False,
          )
  CB.pop_front(p.ncrisc, source_cb, VECTOR_PAGES)


def kernel0_embedding_rmsnorm(
  buffers: Kernel0Buffers, *, timing: Buffer | None = None,
  probe: str | None = None, reduction: str = "sfpu",
) -> Program:
  """Build fused single-core embedding gather + RMSNorm.

  Logical operation, with all arithmetic after BF16 loads in FP32:

    residual_x = embedding_weight[token_id]
    inv_rms = rsqrt(sum(residual_x * residual_x) / 2048 + 1e-5)
    normalized_x = (residual_x * gamma) * inv_rms

  The final multiplication order lets HiFi2 ELWMUL perform the wide learned
  weight multiply before the scalar already resident in SFPU L0 is applied.
  """
  _check_kernel0_buffers(buffers)
  if probe not in (None, "copy", "square", "xgamma", "gapool"):
    raise ValueError(
      "probe must be None, 'copy', 'square', 'xgamma', or 'gapool'",
    )
  if reduction not in ("sfpu", "gapool"):
    raise ValueError("reduction must be 'sfpu' or 'gapool'")
  token_id = buffers.token_id
  embedding_weight = buffers.embedding_weight
  gamma = buffers.gamma
  residual_x = buffers.residual_x
  normalized_x = buffers.normalized_x

  if timing is not None and (
    timing.dtype is not DType.U32 or timing.shape != (1,) or
    not timing.global_address or timing.cores != K0_CORES
  ):
    raise ValueError("timing must be global U32[1] owned by the K0 core")
  parameters = (
    token_id, embedding_weight, gamma, residual_x, normalized_x,
    *((timing,) if timing is not None else ()),
  )
  p = Program(K0_CORES, *parameters, fp32_dst=True)

  token_l1 = p.l1(16, alignment=16)
  timing_l1 = p.l1(16, alignment=16) if timing is not None else None
  # Full-page NoC read destinations must begin on a NoC burst boundary.  A
  # merely 16-byte-aligned address is legal for scalar access but causes the
  # read engine to align the page destination down and shift the logical row.
  x_l1 = p.l1(VECTOR_PAGES * embedding_weight.tile_size, alignment=64)
  gamma_l1 = p.l1(VECTOR_PAGES * gamma.tile_size, alignment=64)
  ones_l1 = (
    p.l1(embedding_weight.tile_size, alignment=64)
    if (probe is None and reduction == "sfpu") or probe == "copy" else None
  )
  normalized_cb = p.cb(DType.BF16, depth=VECTOR_PAGES)

  # These one-credit CBs are readiness signals, not data storage.  Separate x
  # and gamma signals let square reduction begin while BRISC fetches gamma;
  # residual_ready lets NCRISC independently consume the same gathered x.
  x_ready = p.cb.internal("k0_x_ready", DType.BF16)
  gamma_ready = p.cb.internal("k0_gamma_ready", DType.BF16)
  residual_ready = p.cb.internal("k0_residual_ready", DType.BF16)

  # BRISC: fetch the scalar token with the minimum aligned NoC transfer, then
  # gather exactly two dense pages.  Gamma is likewise exactly two pages.
  if ones_l1 is not None:
    with p.brisc.scope():
      pointer, remaining, ones = p.brisc.reg(3)
      p.brisc.li(pointer, ones_l1)
      p.brisc.li(remaining, embedding_weight.tile_size // 4)
      p.brisc.li(ones, 0x3f803f80)
      loop = p.brisc._new_label("k0_fill_ones")
      done = p.brisc._new_label("k0_ones_ready")
      p.brisc.label(loop)
      p.brisc.beq(remaining, 0, done)
      p.brisc.sw(ones, pointer, 0)
      p.brisc.addi(pointer, pointer, 4)
      p.brisc.addi(remaining, remaining, -1)
      p.brisc.j(loop)
      p.brisc.label(done)
  if timing_l1 is not None:
    with p.brisc.scope():
      started = p.brisc.reg()
      p.brisc.read(started, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
      l1.store(p.brisc, timing_l1, 0, started)
  CB.reserve_back(p.brisc, x_ready)
  CB.reserve_back(p.brisc, gamma_ready)
  CB.reserve_back(p.brisc, residual_ready)
  with p.brisc.scope():
    source_address, source_coordinate = p.brisc.noc._dram_tile(token_id, 0)
    p.brisc.noc.read(
      source_address, source_coordinate, token_l1, 16,
    )
    token = p.brisc.reg()
    l1.load(p.brisc, token_l1, 0, token)
    with p.brisc.noc.transaction() as transaction:
      for page in range(VECTOR_PAGES):
        with p.brisc.scope():
          source_page = p.brisc.reg(exclude=token)
          p.brisc.slli(source_page, token, 1)
          if page:
            p.brisc.addi(source_page, source_page, page)
          address, coordinate = p.brisc.noc._dram_tile(
            embedding_weight, source_page,
          )
          transaction.read(
            address, coordinate,
            x_l1 + page * embedding_weight.tile_size,
            embedding_weight.tile_size,
          )
  CB.push_back(p.brisc, x_ready)
  CB.push_back(p.brisc, residual_ready)
  p.brisc.noc.read_tiles(gamma, tuple(
    (page, gamma_l1 + page * gamma.tile_size)
    for page in range(VECTOR_PAGES)
  ))
  CB.push_back(p.brisc, gamma_ready)

  # TRISC0: four L1/L1 pair unpacks.  The first pair feeds x*x; after SFPU
  # consumes those results, the second pair feeds x*gamma.  Bring-up probes
  # select just one pair family and bypass SFPU.
  CB.wait_front(p.trisc0, x_ready)
  if probe is None:
    for page in range(VECTOR_PAGES):
      address = x_l1 + page * embedding_weight.tile_size
      p.unpack.move_l1_pair_pair(
        DType.BF16, address, DType.BF16,
        address if reduction == "gapool" else ones_l1,
      )
  elif probe == "copy":
    for page in range(VECTOR_PAGES):
      p.unpack.move_l1_pair_pair(
        DType.BF16, x_l1 + page * embedding_weight.tile_size,
        DType.BF16, ones_l1,
      )
  elif probe != "xgamma":
    for page in range(VECTOR_PAGES):
      address = x_l1 + page * embedding_weight.tile_size
      p.unpack.move_l1_pair_pair(
        DType.BF16, address, DType.BF16, address,
      )
  CB.pop_front(p.trisc0, x_ready)
  if probe == "gapool" or (probe is None and reduction == "gapool"):
    p.unpack.switch_to_mul_reduce()
  CB.wait_front(p.trisc0, gamma_ready)
  if probe is None:
    for page in range(VECTOR_PAGES):
      p.unpack.move_l1_pair_pair(
        DType.BF16, x_l1 + page * embedding_weight.tile_size,
        DType.BF16, gamma_l1 + page * gamma.tile_size,
      )
  elif probe not in ("copy", "square", "gapool"):
    for page in range(VECTOR_PAGES):
      p.unpack.move_l1_pair_pair(
        DType.BF16, x_l1 + page * embedding_weight.tile_size,
        DType.BF16, gamma_l1 + page * gamma.tile_size,
      )
  CB.pop_front(p.trisc0, gamma_ready)

  # TRISC1: HiFi2 does both wide products.  SFPU only performs the cross-page
  # reduction, epsilon + rsqrt, and the final scalar multiplication.
  if probe is None:
    if reduction == "sfpu":
      for page in range(VECTOR_PAGES):
        p.fpu.binary("mul", dst_tile=page)
      _legacy_begin_rms(p.sfpu)
      for page in range(VECTOR_PAGES):
        p.fpu.binary("mul", dst_tile=page)
      _finish_rms(p.sfpu)
    else:
      _gapool_square_sum(p)
      for word in _gapool_rsqrt_from_l0().words:
        p.sfpu._issue(word)
      stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
      for page in range(VECTOR_PAGES):
        p.fpu.binary("mul", dst_tile=page)
      _finish_rms(p.sfpu)
  elif probe == "gapool":
    _gapool_square_sum(p)
    _select_dst_tile(p.sfpu, 0)
    p.sfpu._issue(TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0))
    stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
    p.fpu.publish()
  elif probe == "copy":
    for page in range(VECTOR_PAGES):
      p.fpu.binary("mul", dst_tile=page)
    p.fpu.publish()
  elif probe is not None:
    for page in range(VECTOR_PAGES):
      p.fpu.binary("mul", dst_tile=page)
    p.fpu.publish()

  # TRISC2 packs both FP32 results to BF16.  NCRISC independently preserves x
  # as the residual, then drains the normalized pages when packing completes.
  p.pack.move_tiles(normalized_cb, tiles=range(VECTOR_PAGES))

  CB.wait_front(p.ncrisc, residual_ready)
  with p.ncrisc.noc.transaction() as transaction:
    for page in range(VECTOR_PAGES):
      with p.ncrisc.scope():
        address, coordinate = p.ncrisc.noc._dram_tile(residual_x, page)
        transaction.write(
          x_l1 + page * residual_x.tile_size,
          address, coordinate, residual_x.tile_size, posted=False,
        )
  CB.pop_front(p.ncrisc, residual_ready)
  _write_dense_vector_from_cb(p, normalized_cb, normalized_x)
  if timing_l1 is not None:
    with p.ncrisc.scope():
      started, finished, elapsed = p.ncrisc.reg(3)
      l1.load(p.ncrisc, timing_l1, 0, started)
      p.ncrisc.read(
        finished, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L,
      )
      p.ncrisc.sub(elapsed, finished, started)
      l1.store(p.ncrisc, timing_l1, 0, elapsed)
      address, coordinate = p.ncrisc.noc._dram_tile(timing, 0)
      p.ncrisc.noc.write(
        timing_l1, address, coordinate, 16, posted=False,
      )
  return p


def _format_bytes(count):
  for suffix in ("B", "KiB", "MiB", "GiB"):
    if count < 1024 or suffix == "GiB":
      return f"{count:.0f} {suffix}" if suffix == "B" else f"{count:.2f} {suffix}"
    count /= 1024
  raise AssertionError("unreachable")


def _print_layout(program):
  """Print the explicit K0 launch and engine split."""
  images = program.lower()[K0_CORES[0]]
  print("K0 embedding + RMSNorm")
  print(f"  launch cores: {len(K0_CORES)} {K0_CORES}")
  print("  vector split: 2 contiguous BF16 pages x 1,024 elements; tail 0")
  print("  BRISC: token/gather/gamma reads")
  print("  NCRISC: residual + normalized writes")
  print("  TRISC0: 4 L1/L1 pair unpacks")
  print("  TRISC1: 4 HiFi2 ELWMUL tiles + SFPU reduction/rsqrt/scale")
  print("  TRISC2: 2 FP32-to-BF16 packs")
  print("  lowered images:")
  for role, image in images.items():
    print(f"    {role:7s} {_format_bytes(len(image))}")


def _bf16_to_fp32(data):
  return (
    np.frombuffer(data, dtype="<u2").astype(np.uint32) << 16
  ).view(np.float32)


def _bf16_rne_bytes(values):
  words = np.ascontiguousarray(values, dtype="<f4").view(np.uint32)
  rounded = words + np.uint32(0x7fff) + ((words >> 16) & np.uint32(1))
  return (rounded >> 16).astype("<u2").tobytes()


def run_hardware(
  *, token=42, repeats=20, warmup=5,
  safetensor_path="weights/model.safetensors",
  probe=None, reduction="sfpu",
):
  """Validate and time instrumented K0 on one Blackhole worker."""
  if not 0 <= token < VOCAB_SIZE:
    raise ValueError(f"token must be in 0..{VOCAB_SIZE - 1}")
  if repeats < 1 or warmup < 0:
    raise ValueError("repeats must be positive and warmup non-negative")

  device = Device()
  try:
    device.init_device()
    buffers = allocate_kernel0_buffers(device.dram)
    timing = device.dram.buffer(
      "k0_elapsed_cycles", DType.U32, (1,),
      global_address=True, cores=K0_CORES,
    )

    embedding_data = buffers.embedding_weight.from_safetensor(
      "model.embed_tokens.weight", safetensor_path,
    )
    gamma_data = buffers.gamma.from_safetensor(
      "model.layers.0.input_layernorm.weight", safetensor_path,
    )
    row_bytes = EMBED_DIM * DType.BF16.itemsize
    residual_reference = bytes(
      embedding_data[token * row_bytes:(token + 1) * row_bytes],
    )
    x = _bf16_to_fp32(residual_reference)
    gamma_values = _bf16_to_fp32(gamma_data)
    mean_square = np.sum(
      np.multiply(x, x, dtype=np.float32), dtype=np.float32,
    ) / np.float32(EMBED_DIM)
    inv_rms = np.float32(
      1.0 / np.sqrt(np.float32(mean_square + np.float32(RMS_EPS))),
    )
    if probe == "copy":
      reference_fp32 = x
    elif probe == "square":
      reference_fp32 = np.multiply(x, x, dtype=np.float32)
    elif probe == "xgamma":
      reference_fp32 = np.multiply(x, gamma_values, dtype=np.float32)
    elif probe == "gapool":
      reference_fp32 = np.zeros_like(x)
    else:
      reference_fp32 = np.multiply(
        np.multiply(x, gamma_values, dtype=np.float32),
        inv_rms, dtype=np.float32,
      )
    normalized_reference = _bf16_rne_bytes(reference_fp32)

    device.write(buffers.embedding_weight, embedding_data)
    device.write(buffers.gamma, gamma_data)
    device.write(
      buffers.token_id,
      buffers.token_id.from_numpy(np.asarray([token], dtype=np.uint32)),
    )
    device.run(timeout=60.0)
    del embedding_data, gamma_data

    program = kernel0_embedding_rmsnorm(
      buffers, timing=timing, probe=probe, reduction=reduction,
    )
    device.cache_kernels((program,), timeout=30.0)
    device.run(program, timeout=30.0)

    residual_actual = device.read(buffers.residual_x, timeout=30.0)
    normalized_actual = device.read(buffers.normalized_x, timeout=30.0)
    residual_exact = residual_actual == residual_reference
    actual_values = _bf16_to_fp32(normalized_actual)
    reference_values = _bf16_to_fp32(normalized_reference)
    absolute = np.abs(actual_values - reference_values)
    relative = absolute / np.maximum(np.abs(reference_values), np.float32(1))
    exact_elements = int(np.count_nonzero(
      np.frombuffer(normalized_actual, dtype="<u2") ==
      np.frombuffer(normalized_reference, dtype="<u2"),
    ))

    for _ in range(warmup):
      device.run(program, timeout=30.0)
    cycle_samples = []
    for _ in range(repeats):
      device.run(program, timeout=30.0)
      words = timing.to_numpy(device.read(timing, timeout=30.0))
      cycle_samples.append(int(words[0]))

    device.queue(program)
    trace = device.capture_trace(("token_id",))
    for _ in range(warmup):
      trace.replay(timeout=30.0)
    trace_samples = []
    wall_samples = []
    for _ in range(repeats):
      started = time.perf_counter_ns()
      trace.replay(timeout=30.0)
      wall_samples.append((time.perf_counter_ns() - started) / 1e3)
      trace_samples.append(trace.last_profile["device_us"])

    cycle_us = tuple(cycles / (DEVICE_HZ / 1e6) for cycles in cycle_samples)
    print("Hardware validation:")
    print(
      f"  math path:                "
      f"{probe or f'rmsnorm/{reduction}'}"
    )
    print(f"  token:                    {token}")
    print(f"  residual exact:           {residual_exact}")
    print(
      f"  normalized exact BF16:    {exact_elements}/{EMBED_DIM}"
    )
    print(f"  normalized max abs error: {float(absolute.max()):.8f}")
    print(f"  normalized max rel error: {float(relative.max()):.8f}")
    if probe == "gapool":
      square_sum = float(np.sum(
        np.multiply(x, x, dtype=np.float32), dtype=np.float32,
      ))
      closest = int(np.argmin(np.abs(actual_values - square_sum)))
      nonzero = np.flatnonzero(actual_values)
      print(f"  expected sum(x*x):         {square_sum:.8f}")
      print(
        f"  closest packed value:      output[{closest}]="
        f"{float(actual_values[closest]):.8f}"
      )
      print(f"  nonzero output indices:    {nonzero[:32].tolist()}")
    if not residual_exact:
      residual_words = np.frombuffer(residual_actual, dtype="<u2")
      reference_words = np.frombuffer(residual_reference, dtype="<u2")
      mismatch = np.flatnonzero(residual_words != reference_words)
      print(f"  residual mismatches:      {len(mismatch)}/{EMBED_DIM}")
      print(f"  first mismatch indices:   {mismatch[:16].tolist()}")
      print(
        "  residual actual[0:16]:   "
        f"{_bf16_to_fp32(residual_actual)[:16].tolist()}"
      )
      print(
        "  residual expect[0:16]:   "
        f"{_bf16_to_fp32(residual_reference)[:16].tolist()}"
      )
    if exact_elements != EMBED_DIM:
      print(
        "  normalized actual[0:16]: "
        f"{actual_values[:16].tolist()}"
      )
      print(
        "  normalized expect[0:16]: "
        f"{reference_values[:16].tolist()}"
      )
      for start in range(0, EMBED_DIM, 256):
        stop = start + 256
        chunk_error = np.abs(
          actual_values[start:stop] - reference_values[start:stop],
        )
        print(
          f"  chunk {start:4d}:{stop:4d}: "
          f"actual[0]={float(actual_values[start]): .8f}, "
          f"expect[0]={float(reference_values[start]): .8f}, "
          f"max_abs={float(chunk_error.max()):.8f}"
        )
    print("Hardware timing:")
    print(
      f"  kernel wall-clock median: {statistics.median(cycle_us):.3f} us "
      f"(min {min(cycle_us):.3f}, max {max(cycle_us):.3f})"
    )
    print(
      f"  traced device/CQ median:  {statistics.median(trace_samples):.3f} us "
      f"(min {min(trace_samples):.3f}, max {max(trace_samples):.3f})"
    )
    print(
      f"  replay host-wall median:  {statistics.median(wall_samples):.3f} us"
    )
    if not residual_exact or (
      probe != "gapool" and float(relative.max()) > 0.02
    ):
      raise RuntimeError("K0 hardware result failed validation")
  finally:
    device.close()


def main():
  """Lower K0 on CPU, or explicitly validate and time it on hardware."""
  parser = argparse.ArgumentParser()
  parser.add_argument("--hardware", action="store_true")
  parser.add_argument("--token", type=int, default=42)
  parser.add_argument("--repeats", type=int, default=20)
  parser.add_argument("--warmup", type=int, default=5)
  parser.add_argument(
    "--probe", choices=("copy", "square", "xgamma", "gapool"),
  )
  parser.add_argument(
    "--reduction", choices=("sfpu", "gapool"), default="sfpu",
  )
  parser.add_argument(
    "--safetensor", default="weights/model.safetensors",
  )
  args = parser.parse_args()
  if args.hardware:
    run_hardware(
      token=args.token, repeats=args.repeats, warmup=args.warmup,
      safetensor_path=args.safetensor,
      probe=args.probe,
      reduction=args.reduction,
    )
    return

  dram = Dram()
  buffers = allocate_kernel0_buffers(dram)
  program = kernel0_embedding_rmsnorm(buffers)
  _print_layout(program)


if __name__ == "__main__":
  main()
