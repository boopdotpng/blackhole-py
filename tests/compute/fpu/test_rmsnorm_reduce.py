"""BF16 RMSNorm of a synthetic 1024-element token with synthetic BF16 gamma.

  y = x * gamma * rsqrt(mean(x^2) + eps)

Reduction: FPU squares (HiFi4 ELWMUL) accumulate the input BF16 tile into one
FP32 Dst tile.  Then either GAPOOL reduces it (Dst -> SrcA narrows to BF16 or TF32
first, and the fidelity chooses how many SrcA mantissa bits GAPOOL consumes)
or the SFPU reduces it in FP32.  The SFPU adds eps and computes rsqrt; the
scale stays live in SFPU register L7 and is also stored for the host.

Normalize has two lowerings, selected by ``normalize``:
  fpu   x -> SrcA and gamma -> SrcB again, HiFi4 ELWMUL products (exact) land
        in an FP32 Dst tile, then the SFPU multiplies every vector by the
        broadcast scale in place.
  sfpu  x -> SrcA -> MOVA2D -> Dst tile t+1 and gamma -> SrcB -> MOVB2D ->
        Dst tile 5; the SFPU does both multiplies.  The FPU only moves data.
        This is what examples/llama3.py ships.
The packer then converts FP32 Dst to BF16 (round to nearest, ties away) into
a dense row-major L1 buffer.

Input, gamma and output use host PCIe TLB windows; the worker kernel has no
NoC transfers. GAPOOL weights are generated on-device: either RISC-V writes
one BF16 row to L1 and unpacker 1 loads it, or SFPLOADI/SFPSTORE creates a
constant in Dst and MOVD2B copies one row. No host weight buffer is uploaded.
Cycle intervals: "L1 to L1" spans the first unpack through
pack completion; "reduction" starts after the squares are ready and includes
the GAPOOL weight generation/loading and Dst moves; "normalize" spans x/gamma
unpacks through the last SFPU store; "pack" spans Dst publication through the
packer's completion post.  Marker/synchronization overhead is included ("empty"
shows it).
"""
from statistics import median

import numpy as np
import pytest

from asm import Asm
from firmware.consts import TensixL1
from ttko.isa import Tensix as TT
from pcie import TLBWindow
from tests.profiler import PROFILE_L1_BASE, PROFILE_L1_SIZE, Profiler
from tests.compute.fpu.test_mean import _add, _reduce_l0
from tests.movement.packer.pack import (
  _configure_row_addressing, _configure_row_mop, _set_dst_position,
  emit_pack_dst_to_cb,
)
from tests.movement.unpacker.unpack import (
  BF16, CFG_BASE, _rmw_cfg_byte, F32, PackCfg, Sem, SemWait, Stall,
  UnpackTarget, Wait, _mop_loop_words,
  _set_thread_cfg, _unpacr, configure_fp32_dst, configure_mop,
  configure_packer, configure_unpack_pair, configure_unpacker, emit_copy_src_to_dst, pc_sync,
  publish_dst, run_mop, sem_get, sem_post, sem_wait, stall,
)

N = 1024
TILES = N // 1024
TILE_BYTES = 1024 * 2
EPS = 1e-5
SCALE_LREG = 7  # rsqrt result stays live here for the normalize pass
INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
WEIGHTS = INPUT + N * 2
OUTPUT = WEIGHTS + N * 2         # 16 FP32 words; [0] is the scale
GAMMA = OUTPUT + 128
NORMALIZED = GAMMA + N * 2       # N BF16 words, then a 64-byte sentinel
GAMMA_DST_TILE = TILES + 1       # SFPU normalize stages each gamma tile here
REDUCTION_PATHS = (
  "bf16-lofi", "bf16-hifi2", "bf16-hifi4",
  "tf32-lofi", "tf32-hifi2", "tf32-hifi4", "sfpu",
)
INV_N_BF16 = int(np.float32(1 / N).view(np.uint32)) >> 16


def _constant(k, reg, value):
  bits = int(np.float32(value).view(np.uint32))
  k.emit(TT.TTSFPLOADI(reg, 8, bits >> 16))
  k.emit(TT.TTSFPLOADI(reg, 10, bits & 65535))


def _rsqrt(k):
  # Positive finite L0: bit seed followed by three Newton iterations.
  k.emit(TT.TTSFPMOV(0, 0, 6, 0))
  k.emit(TT.TTSFPMOV(0, 0, 1, 0))
  k.emit(TT.TTSFPSHFT(0xfff, 9, 1, 1))
  k.emit(TT.TTSFPLOADI(2, 8, 0x5f37))
  k.emit(TT.TTSFPLOADI(2, 10, 0x59df))
  k.emit(TT.TTSFPIADD(0, 2, 1, 6))
  k.emit(TT.TTSFPMULI(0x3f00, 6, 0))  # x/2
  _constant(k, 3, 1.5)
  for _ in range(3):
    k.emit(TT.TTSFPMUL(1, 1, 9, 2, 0))
    k.emit(TT.TTSFPMAD(6, 2, 3, 2, 1))  # 1.5 - x*y*y/2
    k.emit(TT.TTSFPMUL(1, 2, 9, 1, 0))
  k.emit(TT.TTSFPMOV(0, 1, 0, 0))


def _unpack_pair_tile(loader, address_a, address_b):
  """One 1024-element BF16 tile into SrcA and another into SrcB."""
  sem_wait(loader, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(loader, Sem.MATH_DONE)
  configure_unpack_pair(loader, address_a, address_b)
  loader.emit(TT.TTSETADCXX(3, 1023, 0))
  stall(loader, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
  configure_mop(loader, _mop_loop_words(
    1, 1, start=_unpacr(0), loop=_unpacr(1),
    last=_unpacr(1), outer_last=_unpacr(1),
  ))
  run_mop(loader)
  stall(loader, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
  sem_get(loader, Sem.UNPACK_SYNC)
  pc_sync(loader)
  sem_post(loader, Sem.UNPACK_TO_DEST)


def _await_sources(math):
  """Release the previous sources to the unpacker and wait for the next."""
  stall(math, Stall.SYNC, Wait.MATH | Wait.SFPU)
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  stall(math, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)


def _elwmul_tile(math, dst_row, *, release=3, broadcast=0):
  """Dst[dst_row:+64] += SrcA * SrcB at HiFi4; optionally release banks."""
  # HiFi4 covers both BF16 operands, including the low significand bits of
  # SrcB, so BF16 x BF16 products are exact in FP32 Dst.
  for slot in range(8):
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    for _ in range(slot):
      math.emit(TT.TTINCRWC(0, 0, 0 if broadcast else 8, 8))
    for mode in (0, 0, 0, 1):
      math.emit(TT.TTELWMUL(0, 0, broadcast, mode, dst_row + slot * 8))
  math.emit(TT.TTSETRWC(release, 0, 0, 0, 0, 0xF))


def _unpack_weights(loader, math):
  """RISC-V builds one BF16 row in L1; unpack only that row into SrcB."""
  sem_wait(loader, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(loader, Sem.MATH_DONE)
  pointer, pair = loader.reg(2)
  loader.li(pointer, WEIGHTS)
  loader.li(pair, INV_N_BF16 | INV_N_BF16 << 16)
  for offset in range(0, 32, 4):
    loader.sw(pair, pointer, offset)
  loader.fence()
  configure_unpacker(loader, 1, WEIGHTS, BF16, UnpackTarget.SRCB)
  loader.emit(TT.TTSETADCXX(2, 15, 0))
  loader.emit(TT.TTSETADCZW(2, 0, 0, 0, 0, 0xF))
  stall(loader, Stall.UNPACK, Wait.SRCB_CLR)
  loader.emit(TT.TTUNPACR_NOP(1, 0, 0, 0, 0, 0, 0, 0, 1))
  loader.emit(_unpacr(1))
  stall(loader, Stall.UNPACK, Wait.UNPACK1)
  sem_get(loader, Sem.UNPACK_SYNC)
  pc_sync(loader)
  sem_post(loader, Sem.UNPACK_TO_DEST)

  math.emit(TT.TTSETRWC(2, 0, 0, 0, 0, 0xF))
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  stall(math, Stall.MATH, Wait.SRCB_VLD)


def _sfpu_weights(math):
  """Create a constant vector in Dst, then copy its first row to SrcB."""
  stall(math, Stall.SFPU, Wait.MATH)
  math.emit(TT.TTSFPLOADI(0, 0, INV_N_BF16))
  math.emit(TT.TTSFPSTORE(0, 3, 3, 0))
  math.emit(TT.TTSFPSTORE(0, 3, 3, 2))
  stall(math, Stall.MATH, Wait.SFPU)
  math.emit(TT.TTZEROSRC(0, 1, 0, 2))
  math.emit(TT.TTMOVD2B(0, 0, 3, 0, 0))


def _select_dst_tile(math, tile):
  # DEST_TARGET_REG_CFG_MATH_Offset relocates FPU and SFPU Dst addressing.
  stall(math, Stall.CFG, Wait.MATH | Wait.SFPU)
  _set_thread_cfg(math, 1, tile * 64)


def _sfpu_scale_tiles(math):
  """FPU normalize: every product vector in Dst tiles 1..TILES times L7."""
  stall(math, Stall.SFPU, Wait.MATH)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  for tile in range(1, TILES + 1):
    for position in range(0, 64, 4):
      row = tile * 64 + position
      math.emit(TT.TTSFPLOAD(1, 3, 3, row))
      math.emit(TT.TTSFPLOAD(2, 3, 3, row + 2))
      math.emit(TT.TTSFPMUL(1, SCALE_LREG, 9, 1, 0))
      math.emit(TT.TTSFPMUL(2, SCALE_LREG, 9, 2, 0))
      math.emit(TT.TTSFPSTORE(1, 3, 3, row))
      math.emit(TT.TTSFPSTORE(2, 3, 3, row + 2))


def _sfpu_normalize_tile(math, tile):
  """SFPU normalize: Dst tile ``tile`` *= gamma tile * L7, all in FP32."""
  stall(math, Stall.SFPU, Wait.MATH)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  for position in range(0, 64, 4):
    x, g = tile * 64 + position, GAMMA_DST_TILE * 64 + position
    math.emit(TT.TTSFPLOAD(1, 3, 3, x))
    math.emit(TT.TTSFPLOAD(2, 3, 3, g))
    math.emit(TT.TTSFPLOAD(3, 3, 3, x + 2))
    math.emit(TT.TTSFPLOAD(4, 3, 3, g + 2))
    math.emit(TT.TTSFPMUL(1, 2, 9, 1, 0))
    math.emit(TT.TTSFPMUL(3, 4, 9, 3, 0))
    math.emit(TT.TTSFPMUL(1, SCALE_LREG, 9, 1, 0))
    math.emit(TT.TTSFPMUL(3, SCALE_LREG, 9, 3, 0))
    math.emit(TT.TTSFPSTORE(1, 3, 3, x))
    math.emit(TT.TTSFPSTORE(3, 3, 3, x + 2))


def _pack_normalized(packer):
  """FP32 Dst tiles 1..TILES -> dense BF16 rows at NORMALIZED."""
  # Same per-page sequence as test_q6: configure once, then only move the
  # Dst read position and the L1 destination between MOP runs.
  configure_packer(packer, BF16)
  _configure_row_addressing(packer)
  _configure_row_mop(packer, 64, close=True)
  for tile in range(1, TILES + 1):
    address = NORMALIZED + (tile - 1) * TILE_BYTES
    pc_sync(packer)
    _set_dst_position(packer, tile, 0)
    packer.write(PackCfg.L1_DESTINATION, ((address >> 4) - 1) | 0x80000000)
    packer.write(PackCfg.DESTINATION_OFFSET, 0)
    packer.emit(TT.TTSETADCXX(4, 15, 0))
    run_mop(packer)
    stall(packer, Stall.SYNC, Wait.PACK0)
    pc_sync(packer)


def _images(source_format="tf32", fidelity=2, *, normalize=None, profile=None,
            weights="sfpu"):
  if weights not in ("l1", "sfpu"):
    raise ValueError("weights must be 'l1' or 'sfpu'")
  if normalize not in (None, "fpu", "sfpu", "tf32-broadcast"):
    raise ValueError("unknown normalize lowering")
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  extra = None
  if profile is not None:
    profile.kernel = math
    profile.record("empty")
    profile.record("empty")
    if normalize is not None:
      extra = Profiler(math, l1_address=profile.l1_address - PROFILE_L1_SIZE)
  configure_fp32_dst(math, 0)
  _set_thread_cfg(math, 2, 0)
  _set_thread_cfg(math, 3, 0)
  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))  # Mode 3 invalidates all of Dst.
  _set_thread_cfg(math, 11, 0)
  # Stationary operands: phase advance, phase reset, and no change.
  for mode, phase_bits in ((0, 1 << 13), (1, 1 << 15), (3, 0)):
    _set_thread_cfg(math, 12 + mode, 0)
    _set_thread_cfg(math, 28 + mode, phase_bits)
    _set_thread_cfg(math, 47 + mode, 0)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  math.emit(TT.TTSFPENCC(0, 0, 0, 2))
  math.emit(TT.TTSFPLOADI(0, 2, 0))
  math.emit(TT.TTSFPCONFIG(0, 15, 0))  # Enable Dst/source moves.
  math.emit(TT.TTSFPNOP())

  if profile is not None:
    # Both threads are ready before starting the L1-to-L1 interval.
    pc_sync(loader)
    sem_post(loader, Sem.UNPACK_TO_DEST)
    stall(math, Stall.SYNC, Wait.MATH | Wait.SFPU)
    sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
    sem_get(math, Sem.UNPACK_TO_DEST)
    pc_sync(math)
    profile.record("L1 to L1")

  for tile in range(TILES):
    address = INPUT + tile * TILE_BYTES
    _unpack_pair_tile(loader, address, address)
    _await_sources(math)
    # Keep the last source banks for Dst->SrcA and generated weights.
    _elwmul_tile(math, 0, release=0 if tile == TILES - 1 else 3)

  stall(math, Stall.SYNC, Wait.MATH)
  pc_sync(math)
  if profile is not None:
    profile.record("reduction")

  if source_format == "sfpu":
    stall(math, Stall.SYNC, Wait.MATH)
    pc_sync(math)
    # FPU squares have accumulated into one FP32 Dst tile.
    # Reduce all 32 SFPU vectors without narrowing through SrcA.
    math.emit(TT.TTSFPLOAD(0, 3, 3, 0))
    for position in range(2, 64, 2):
      math.emit(TT.TTSFPLOAD(1, 3, 3, position))
      _add(math, 0, 1, 0)
    _reduce_l0(math)
    math.emit(TT.TTSFPMULI(INV_N_BF16, 0, 0))  # 1/N
  else:
    if source_format == "tf32":
      # Override both math source formats: TF32 (4), with override bits set.
      _rmw_cfg_byte(math, CFG_BASE, 0, 0xff, 0x94)
      _rmw_cfg_byte(math, CFG_BASE, 1, 0x03, 0x02)
      # Blackhole bank-implied BF16 would otherwise override these formats.
      _set_thread_cfg(math, 2, 1)
      _set_thread_cfg(math, 3, 1)
    for row in range(0, 64, 4):
      math.emit(TT.TTMOVD2A(0, row, 3, 2, row))
    if weights == "l1":
      _unpack_weights(loader, math)
    else:
      _sfpu_weights(math)
    math.emit(TT.TTGATESRCRST(1, 1))
    # Squares are now in SrcA. GAPOOL accumulates scaled column sums in Dst.
    math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
    for row in range(0, 64, 16):
      math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
      for _ in range(row // 8):
        math.emit(TT.TTINCRWC(0, 0, 0, 8))
      for mode in (*([0] * (fidelity - 1)), 1):
        math.emit(TT.TTGAPOOL(0, 0, mode, 0, 0))
    stall(math, Stall.SFPU, Wait.MATH)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    math.emit(TT.TTSFPLOAD(0, 3, 3, 0))
    math.emit(TT.TTSFPLOAD(1, 3, 3, 2))
    _add(math, 0, 1, 0)
    # Only SFPU row 0 holds column sums; rows 1..3 are GAPOOL's zero rows.
    # The vertical step is only needed to broadcast the total to all lanes.
    _reduce_l0(math, horizontal=True, vertical=normalize is not None)
  _constant(math, 2, EPS)
  _add(math, 0, 2, 0)
  _rsqrt(math)
  math.emit(TT.TTSFPMOV(0, 0, SCALE_LREG, 0))
  math.emit(TT.TTSFPSTORE(0, 3, 3, 0))
  math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  if profile is not None:
    stall(math, Stall.SYNC, Wait.MATH | Wait.SFPU)
    pc_sync(math)
    profile.record("reduction")

  if normalize is not None:
    if extra is not None:
      extra.record("normalize")
    if source_format == "tf32":
      # Back to bank-implied BF16 sources for the x * gamma products.
      _set_thread_cfg(math, 2, 0)
      _set_thread_cfg(math, 3, 0)
    for tile in range(TILES):
      _unpack_pair_tile(loader, INPUT + tile * TILE_BYTES, GAMMA + tile * TILE_BYTES)
      _await_sources(math)
      if normalize in ("fpu", "tf32-broadcast"):
        _elwmul_tile(math, (tile + 1) * 64,
                     release=0 if normalize == "tf32-broadcast" else 3)
        if normalize == "tf32-broadcast":
          # Test the cost of avoiding the SFPU's per-vector scale multiplies.
          _rmw_cfg_byte(math, CFG_BASE, 0, 0xff, 0x94)
          _rmw_cfg_byte(math, CFG_BASE, 1, 0x03, 0x02)
          _set_thread_cfg(math, 2, 1)
          _set_thread_cfg(math, 3, 1)
          for row in range(0, 64, 4):
            math.emit(TT.TTMOVD2A(0, row, 3, 2, (tile + 1) * 64 + row))
          math.emit(TT.TTMOVD2B(0, 0, 3, 0, 0))
          math.emit(TT.TTGATESRCRST(1, 1))
          for face in range(4):
            math.emit(TT.TTZEROACC(1, 1, 0, 3, (tile + 1) * 4 + face))
          _elwmul_tile(math, (tile + 1) * 64, broadcast=3)
          _set_thread_cfg(math, 2, 0)
          _set_thread_cfg(math, 3, 0)
      else:
        # Copies narrow through TF32, which is exact for BF16 sources.
        # The whole tile occupies one source bank. Release once per tile;
        # emit_copy_src_to_dst's per-face release would wait on absent banks.
        for row in range(0, 64, 4):
          math.emit(TT.TTMOVB2D(0, row, 3, 4, GAMMA_DST_TILE * 64 + row))
        for row in range(0, 64, 8):
          math.emit(TT.TTMOVA2D(0, row, 3, 2, (tile + 1) * 64 + row))
        math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
        _sfpu_normalize_tile(math, tile + 1)
    if normalize == "fpu":
      _sfpu_scale_tiles(math)
    stall(math, Stall.SYNC, Wait.MATH | Wait.SFPU)
    pc_sync(math)
    if extra is not None:
      extra.record("normalize")
      extra.record("pack")
  publish_dst(math)
  count = packer.reg()
  packer.li(count, 16)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  if normalize is not None:
    _pack_normalized(packer)
  if profile is not None:
    # Stop on the packer after output completion, not on a loader-credit sem.
    pc_sync(packer)
    if extra is not None:
      extra.kernel = packer
      extra.record("pack")
    profile.kernel = packer
    profile.record("L1 to L1")
  return {k.role: k.lower() for k in (loader, math, packer)}


def _bf16_round(values):
  """Round FP32 values to BF16 (nearest even), returned as 16-bit words."""
  bits = np.asarray(values, dtype=np.float32).view(np.uint32)
  return ((bits + 0x7fff + ((bits >> 16) & 1)) >> 16).astype('<u2')


def _from_bf16(words):
  return (np.asarray(words).astype(np.uint32) << 16).view(np.float32)


def _gamma():
  # Non-trivial, signed, exactly representable BF16 values (k/64, |k| <= 100).
  return (((np.arange(N) * 37) % 101) / 64 - 0.75).astype(np.float32)


def _preload(bh):
  values = np.arange(N, dtype=np.float32)
  bf16 = _bf16_round(values)
  x = _from_bf16(bf16)
  gamma_bits = _bf16_round(_gamma())
  gamma = _from_bf16(gamma_bits)
  expected = 1 / np.sqrt(np.mean(x.astype(np.float64) ** 2) + EPS)
  with TLBWindow(bh.device.pcie.fd, bh.core) as window:
    window.target(0, bh.core)
    window.write(INPUT, bf16.tobytes())
    window.write(OUTPUT, b'\xa5' * 128)
    window.write(GAMMA, gamma_bits.tobytes())
    window.write(NORMALIZED, b'\xa5' * (N * 2 + 64))
  return x, gamma, expected


def _reduction_path(path):
  if path == "sfpu":
    return "sfpu", 2
  source_format, fidelity = path.split("-")
  return source_format, {"lofi": 1, "hifi2": 2, "hifi4": 4}[fidelity]


def _scale_tolerance(source_format, fidelity):
  if source_format == "sfpu":
    return 1e-6
  return 0.011 if fidelity == 1 else (0.002 if source_format == "bf16" else 0.0003)


def _check_scale(bh, x, expected, source_format, fidelity):
  actual = np.frombuffer(bh.read_l1(bh.core, OUTPUT, 4), dtype='<f4')[0]
  if source_format != "sfpu":
    # MOVD2A truncates to 7 (BF16) or 10 (TF32) fraction bits. GAPOOL
    # consumes only the top 4 in phase 0, and at most 9 from TF32 SrcA even
    # with all phases. B=1/N has no fraction bits, so HiFi2 == HiFi4 here.
    fraction_bits = 4 if fidelity == 1 else (7 if source_format == "bf16" else 9)
    mask = np.uint32((0xffffffff << (23 - fraction_bits)) & 0xffffffff)
    squares = (x * x).reshape(TILES, 1024).sum(axis=0, dtype=np.float32)
    narrowed = (squares.view(np.uint32) & mask).view(np.float32)
    kernel_expected = 1 / np.sqrt(narrowed.astype(np.float64).sum() / N + EPS)
    np.testing.assert_allclose(actual, kernel_expected, rtol=1e-6, atol=0)
  tolerance = _scale_tolerance(source_format, fidelity)
  np.testing.assert_allclose(actual, expected, rtol=tolerance, atol=0)
  assert bh.read_l1(bh.core, OUTPUT + 64, 64) == b'\xa5' * 64
  return actual


def _check_normalized(bh, x, gamma, expected, scale, tolerance):
  """Return the BF16 output as FP32 and the count of bit-exact elements."""
  words = np.frombuffer(bh.read_l1(bh.core, NORMALIZED, N * 2), dtype='<u2')
  assert bh.read_l1(bh.core, NORMALIZED + N * 2, 64) == b'\xa5' * 64
  y = _from_bf16(words)
  # Kernel model: the BF16 x BF16 product is exact in FP32, one FP32 rounding
  # applies the scale, and the packer rounds to BF16 (nearest, ties away).
  # The SFPU multiply may not round to nearest even, which can move a value
  # across a BF16 rounding boundary, so allow one BF16 ulp from the model.
  y32 = ((x * gamma).astype(np.float32) * np.float32(scale)).astype(np.float32)
  model = _from_bf16(((y32.view(np.uint32) + 0x8000) >> 16) & 0xffff)
  magnitude = np.abs(y32.astype(np.float64))
  ulp = np.where(magnitude == 0, 0.0,
                 2.0 ** (np.floor(np.log2(np.where(magnitude == 0, 1, magnitude))) - 7))
  errors = np.abs(y.astype(np.float64) - model.astype(np.float64))
  assert np.all(errors <= ulp), (
    f"{int((errors > ulp).sum())} elements exceed one BF16 ulp from the model"
  )
  exact = int((y == model).sum())
  # End to end: BF16 output rounding plus the reduction path's scale error.
  reference = x.astype(np.float64) * gamma.astype(np.float64) * expected
  np.testing.assert_allclose(y.astype(np.float64), reference,
                             rtol=2 ** -7 + tolerance, atol=0)
  return y, exact


@pytest.mark.parametrize("source_format", ("bf16", "tf32"))
@pytest.mark.parametrize("fidelity", (1, 2, 4), ids=("lofi", "hifi2", "hifi4"))
def test_arange1024_bf16_rmsnorm_reduce(bh, source_format, fidelity):
  images = _images(source_format, fidelity)
  x, _, expected = _preload(bh)
  bh.launch(images)
  actual = _check_scale(bh, x, expected, source_format, fidelity)
  print(f'{source_format} GAPOOL phases={fidelity}: rsqrt={actual:.9g}, '
        f'reference={expected:.9g}, relative error={100 * (actual / expected - 1):+.6f}%')


@pytest.mark.parametrize("normalize", ("fpu", "sfpu"))
@pytest.mark.parametrize("path", REDUCTION_PATHS)
@pytest.mark.parametrize("weights", ("l1", "sfpu"))
def test_arange1024_bf16_rmsnorm(bh, path, normalize, weights):
  source_format, fidelity = _reduction_path(path)
  images = _images(source_format, fidelity, normalize=normalize, weights=weights)
  x, gamma, expected = _preload(bh)
  bh.launch(images)
  scale = _check_scale(bh, x, expected, source_format, fidelity)
  y, exact = _check_normalized(
    bh, x, gamma, expected, scale, _scale_tolerance(source_format, fidelity),
  )
  reference = x.astype(np.float64) * gamma.astype(np.float64) * expected
  nonzero = reference != 0
  worst = np.max(np.abs(y[nonzero] / reference[nonzero] - 1))
  print(f'{weights} weights, {path} reduction, {normalize} normalize: scale relative error='
        f'{100 * (scale / expected - 1):+.6f}%, {exact}/{N} outputs match the '
        f'kernel model bit-exactly, worst output relative error={100 * worst:.4f}%')


def _read_intervals(bh, address, labels):
  stamps = np.frombuffer(
    bh.read_l1(bh.core, address, 8 * len(labels)), dtype='<u4',
  )
  return {
    label: (int(stamps[2 * i + 1]) - int(stamps[2 * i])) & 0xffffffff
    for i, label in enumerate(labels)
  }


def _print_timings(name, error, timings, labels):
  print(f'{name}: relative error={error:+.8f}%; ' + '; '.join(
    f'{label} median={median(s[label] for s in timings)}, '
    f'min={min(s[label] for s in timings)}, '
    f'max={max(s[label] for s in timings)} cycles'
    for label in labels))


@pytest.mark.parametrize("source_format", ("bf16", "tf32"))
def test_rmsnorm_weight_cycles(bh, source_format):
  """Matched HiFi2 GAPOOL + FPU normalize; include on-device weight setup."""
  paths = ("l1", "sfpu")
  profiles = {path: Profiler(None) for path in paths}
  images = {path: _images(source_format, 2, normalize="fpu",
                         weights=path, profile=profiles[path]) for path in paths}
  timings = {path: [] for path in paths}
  errors = {}
  for sample in range(21):
    outputs = {}
    for path in paths[::1 if sample % 2 == 0 else -1]:
      x, gamma, expected = _preload(bh)
      # Poison scratch: the kernel must regenerate weights each launch.
      with TLBWindow(bh.device.pcie.fd, bh.core) as window:
        window.target(0, bh.core)
        window.write(WEIGHTS, b'\xa5' * 32)
      profile = profiles[path]
      profile._validate()
      bh.launch(images[path])
      scale = _check_scale(bh, x, expected, source_format, 2)
      y, _ = _check_normalized(bh, x, gamma, expected, scale,
                               _scale_tolerance(source_format, 2))
      outputs[path] = (scale, y)
      errors[path] = 100 * (scale / expected - 1)
      if sample:
        intervals = _read_intervals(
          bh, profile.l1_address, ("empty", "L1 to L1", "reduction"))
        intervals.update(_read_intervals(
          bh, profile.l1_address - PROFILE_L1_SIZE, ("normalize", "pack")))
        timings[path].append(intervals)
    assert outputs["l1"][0] == outputs["sfpu"][0]
    np.testing.assert_array_equal(outputs["l1"][1], outputs["sfpu"][1])
  for path in paths:
    _print_timings(f'{source_format} HiFi2 GAPOOL, {path} weights', errors[path],
                   timings[path], ("L1 to L1", "reduction", "normalize", "pack", "empty"))


def test_rmsnorm_reduce_cycles(bh):
  # Read wall-clock records over TLB, avoiding Profiler's NoC/DRAM export.
  paths = ("tf32", "sfpu")
  profiles = {path: Profiler(None) for path in paths}
  images = {path: _images(path, profile=profiles[path]) for path in paths}
  timings = {path: [] for path in paths}
  errors = {}
  for sample in range(12):
    # Alternate ordering to reduce drift; first round is warmup.
    for path in paths[::1 if sample % 2 == 0 else -1]:
      _, _, expected = _preload(bh)
      profile = profiles[path]
      profile._validate()
      bh.launch(images[path])
      actual = np.frombuffer(bh.read_l1(bh.core, OUTPUT, 4), dtype='<f4')[0]
      np.testing.assert_allclose(actual, expected,
                                 rtol=1e-6 if path == "sfpu" else 3e-4, atol=0)
      assert bh.read_l1(bh.core, OUTPUT + 64, 64) == b'\xa5' * 64
      errors[path] = 100 * (actual / expected - 1)
      if sample:
        timings[path].append(_read_intervals(
          bh, profile.l1_address, ("empty", "L1 to L1", "reduction"),
        ))
  for path in paths:
    _print_timings(path, errors[path], timings[path],
                   ("L1 to L1", "reduction", "empty"))


def test_rmsnorm_cycles(bh):
  """Every reduction path x both normalize lowerings, end to end."""
  combos = tuple(
    (path, normalize)
    for path in REDUCTION_PATHS for normalize in ("fpu", "sfpu")
  )
  profiles = {combo: Profiler(None) for combo in combos}
  images = {}
  for combo in combos:
    source_format, fidelity = _reduction_path(combo[0])
    images[combo] = _images(
      source_format, fidelity, normalize=combo[1], profile=profiles[combo],
    )
  timings = {combo: [] for combo in combos}
  errors = {}
  for sample in range(8):
    for combo in combos[::1 if sample % 2 == 0 else -1]:
      path, normalize = combo
      source_format, fidelity = _reduction_path(path)
      x, gamma, expected = _preload(bh)
      profile = profiles[combo]
      profile._validate()
      bh.launch(images[combo])
      scale = _check_scale(bh, x, expected, source_format, fidelity)
      y, _ = _check_normalized(
        bh, x, gamma, expected, scale, _scale_tolerance(source_format, fidelity),
      )
      reference = x.astype(np.float64) * gamma.astype(np.float64) * expected
      nonzero = reference != 0
      errors[combo] = 100 * np.max(np.abs(y[nonzero] / reference[nonzero] - 1))
      if sample:
        intervals = _read_intervals(
          bh, profile.l1_address, ("empty", "L1 to L1", "reduction"),
        )
        intervals.update(_read_intervals(
          bh, profile.l1_address - PROFILE_L1_SIZE, ("normalize", "pack"),
        ))
        timings[combo].append(intervals)
  for combo in combos:
    _print_timings(
      f'{combo[0]} reduction + {combo[1]} normalize (worst output)',
      errors[combo], timings[combo],
      ("L1 to L1", "reduction", "normalize", "pack", "empty"),
    )
