"""Raw port of examples/llama3.py's SFPU RMSNorm, at 1024 and 2048 elements.

Keep x and gamma in FP32 Dst, accumulate squares in L0, reduce the lanes,
refine reciprocal sqrt, then apply scale with SFPLOADMACRO and multiply gamma.
The arithmetic/rsqrt/macro match llama3; transport uses the raw test harness.
Timing includes L1 unpack/copy and BF16 packing, but excludes host/DRAM/NoC.
"""
from statistics import median

import numpy as np
import pytest

from asm import Asm
from ttko.isa import Tensix as TT
from pcie import TLBWindow
from tests.profiler import Profiler
from tests.compute.fpu.test_rmsnorm_reduce import (
  _unpack_pair_tile, _await_sources, _constant, _bf16_round, _from_bf16,
  _read_intervals,
)
from tests.movement.unpacker.unpack import (
  BF16, F32, CFG_BASE, PackCfg, Stall, Wait, Sem, SemWait,
  _set_thread_cfg, _rmw_cfg_byte, configure_fp32_dst, configure_packer,
  pc_sync, stall, publish_dst, sem_wait, sem_get, sem_post,
  configure_mop, _mop_loop_words, load_replay, run_mop,
  configure_unpack_pair, _unpacr, _set_unpack_base,
)
from tests.movement.packer.pack import (
  emit_pack_dst_to_cb, _configure_row_addressing, _configure_row_mop,
  _set_dst_position,
)
from firmware.consts import TensixL1, TensixMMIO

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
GAMMA = INPUT + 8192
OUTPUT = GAMMA + 8192
SCALE = OUTPUT + 8192 + 64
EPS = 1e-5


def _add(k, a, b, out):
  k.emit(TT.TTSFPADD(10, a, b, out, 0))
  k.emit(TT.TTSFPNOP())


def _mul(k, a, b, out, modifier=0):
  k.emit(TT.TTSFPMUL(a, b, 9, out, modifier))
  k.emit(TT.TTSFPNOP())


def _finalize(k, n):
  # Copied from llama3's _rms_finalize_scale; only EMBED_DIM is parameterized.
  for rotations in (4, 2, 1):
    k.emit(TT.TTSFPMOV(0, 0, 1, 0))
    for _ in range(rotations):
      k.emit(TT.TTSFPSHFT2(0, 1, 1, 3))
      k.emit(TT.TTSFPNOP())
    _add(k, 0, 1, 0)
  for reg in (1, 2, 3):
    k.emit(TT.TTSFPMOV(0, 0, reg, 0))
  k.emit(TT.TTSFPTRANSP(0, 0, 0, 0))
  for reg in (1, 2, 3):
    _add(k, 0, reg, 0)
  _constant(k, 4, 1 / n)
  k.emit(TT.TTSFPMUL(0, 4, 9, 0, 0))
  _constant(k, 4, EPS)
  _add(k, 0, 4, 0)
  k.emit(TT.TTSFPMOV(0, 0, 6, 0))
  k.emit(TT.TTSFPMOV(0, 6, 1, 0))
  k.emit(TT.TTSFPSHFT(0xfff, 9, 1, 1))
  k.emit(TT.TTSFPLOADI(2, 10, 0x10a0))
  k.emit(TT.TTSFPLOADI(2, 8, 0x5f11))
  k.emit(TT.TTSFPIADD(0, 2, 1, 6))
  _mul(k, 6, 1, 2)
  k.emit(TT.TTSFPMUL(1, 2, 9, 2, 1))
  _constant(k, 3, 2.2825186)
  _constant(k, 4, 2.2533049)
  _add(k, 4, 2, 4)
  k.emit(TT.TTSFPMAD(2, 4, 3, 2, 0))
  k.emit(TT.TTSFPNOP())
  _mul(k, 1, 2, 1)
  _mul(k, 6, 1, 2)
  _mul(k, 1, 2, 2, 1)
  k.emit(TT.TTSFPADD(10, 10, 2, 2, 0))
  _constant(k, 5, 0.5)
  _mul(k, 1, 5, 5)
  k.emit(TT.TTSFPMAD(2, 5, 1, 0, 0))


def _map(k, body, *, iterations, initialize=True):
  """llama3's replay/MOP schedule: four separate one-face expansions."""
  body = (*body, TT.TTINCRWC(0, 2, 0, 0))
  if initialize:
    load_replay(k, 0, body)
  replay = TT.TTREPLAY(0, len(body), 0, 0)
  face_step = TT.TTSETRWC(0, 4, 8, 0, 0, 4)
  configure_mop(k, _mop_loop_words(1, iterations, loop=replay,
    end0=face_step, end1=face_step, last=replay, outer_last=replay))
  for _ in range(4):
    run_mop(k)
  k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
  stall(k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def _timestamp(k, address):
  value = k.reg()
  k.read(value, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  k.write(address, value)


def _unpack_reused(u, tile, *, prefetch=False, trace=None):
  """Shared transport for the fair llama3/hybrid comparison."""
  if not prefetch or tile == 0:
    # Also block SEMGET/subsequent waits: a wait that blocks only UNPACK can
    # be replaced before UNPACR reaches it, accidentally bypassing the credit.
    sem_wait(u, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK | Stall.SYNC)
    sem_get(u, Sem.MATH_DONE)
  if tile == 0:
    configure_unpack_pair(u, INPUT, GAMMA)
    u.emit(TT.TTSETADCXX(3, 1023, 0))
    configure_mop(u, _mop_loop_words(
      1, 1, start=_unpacr(0), loop=_unpacr(1),
      last=_unpacr(1), outer_last=_unpacr(1)))
  else:
    _set_unpack_base(u, 0, INPUT + tile*2048)
    _set_unpack_base(u, 1, GAMMA + tile*2048)
    u.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  stall(u, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
  if trace is not None:
    pc_sync(u)
    _timestamp(u, trace + tile*16)
  run_mop(u)
  stall(u, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
  sem_get(u, Sem.UNPACK_SYNC)
  pc_sync(u)
  if trace is not None:
    _timestamp(u, trace + tile*16+4)
  if prefetch:
    # One pending notification is enough; the hardware's source-bank valid
    # bits keep the unpacker from overwriting either bank while math owns it.
    sem_wait(u, Sem.UNPACK_TO_DEST, SemWait.ON_MAX, Stall.SYNC)
  sem_post(u, Sem.UNPACK_TO_DEST)


def _pack_output(p, tiles, first_tile, *, wait=True):
  """Identical output-only BF16 packing, with algorithm-specific Dst base."""
  if wait:
    sem_wait(p, Sem.MATH_PACK, SemWait.ON_ZERO, Stall.TDMA)
  configure_packer(p, BF16)
  _configure_row_addressing(p)
  _configure_row_mop(p, 64, close=True)
  for tile in range(tiles):
    pc_sync(p)
    _set_dst_position(p, first_tile + tile, 0)
    p.write(PackCfg.L1_DESTINATION, ((OUTPUT + tile*2048) >> 4)-1 | 0x80000000)
    p.write(PackCfg.DESTINATION_OFFSET, 0)
    p.emit(TT.TTSETADCXX(4, 15, 0))
    run_mop(p)
    stall(p, Stall.SYNC, Wait.PACK0)
    pc_sync(p)
  if wait:
    sem_get(p, Sem.MATH_PACK)


def _await_unpacked(m, tile, *, prefetch=False):
  if not prefetch:
    _await_sources(m)
    return
  if tile == 0:
    sem_post(m, Sem.MATH_DONE)
  sem_wait(m, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(m, Sem.UNPACK_TO_DEST)
  stall(m, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)


def _images(n, *, diagnostic=True, reuse_unpack=False, prefetch=False):
  if n not in (1024, 2048, 3072, 4096):
    raise ValueError('expected 1..4 tiles')
  if prefetch and not reuse_unpack:
    raise ValueError('prefetch requires reused unpack configuration')
  tiles = n // 1024
  u, m, p = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  profile = Profiler(m)
  configure_fp32_dst(m, 0)
  _rmw_cfg_byte(m, CFG_BASE + 4, 3, 0x40, 0x40)
  m.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  m.emit(TT.TTSFPENCC(0, 0, 0, 2))
  m.emit(TT.TTSFPCONFIG(0, 15, 1))
  m.emit(TT.TTSFPNOP())
  # Same load-times-scale macro as llama3, with the scale live in L0.
  m.emit(TT.TTSFPMUL(0, 0, 9, 12, 0))
  m.emit(TT.TTSFPCONFIG(0x8400, 4, 1))
  m.emit(TT.TTSFPCONFIG(0x0f00, 8, 1))
  # Stationary moves; SFPU vectors advance through explicit INCRWC in replay.
  for mod in (3, 7):
    _set_thread_cfg(m, 12 + mod, 0)
    _set_thread_cfg(m, 28 + mod, 0)
    _set_thread_cfg(m, 47 + mod, 0)
  pc_sync(u)
  sem_post(u, Sem.UNPACK_TO_DEST)
  sem_wait(m, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(m, Sem.UNPACK_TO_DEST)
  pc_sync(m)
  profile.record('L1 to L1')
  for tile in range(tiles):
    if reuse_unpack:
      _unpack_reused(u, tile, prefetch=prefetch)
    else:
      _unpack_pair_tile(u, INPUT + tile * 2048, GAMMA + tile * 2048)
    _await_unpacked(m, tile, prefetch=prefetch)
    for row in range(0, 64, 8):
      m.emit(TT.TTMOVA2D(0, row, 3, 2, tile * 64 + row))
    for row in range(0, 64, 4):
      m.emit(TT.TTMOVB2D(0, row, 3, 4, (tiles + tile) * 64 + row))
    m.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(m)
  profile.record('compute')
  m.emit(TT.TTSFPLOADI(0, 0, 0))  # BF16 immediate zero -> FP32 +0 in all lanes.
  # The production two-instruction accumulation body, replayed per face.
  for tile in range(tiles):
    _set_thread_cfg(m, 1, tile * 64)
    m.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    _map(m, (TT.TTSFPLOAD(1, 3, 7, 0),
             TT.TTSFPMAD(1, 1, 0, 0, 0)), iterations=8, initialize=tile == 0)
  _finalize(m, n)
  # Copy the production load macro / paired gamma multiply sequence.
  for tile in range(tiles):
    _set_thread_cfg(m, 1, tile * 64)
    m.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    _map(m, (
      TT.TTSFPLOADMACRO(1, 0, 7, 0),
      TT.TTSFPLOAD(2, 3, 7, tiles * 64),
      TT.TTSFPLOADMACRO(3, 0, 7, 2),
      TT.TTSFPLOAD(4, 3, 7, tiles * 64 + 2),
      TT.TTSFPMUL(1, 2, 9, 1, 0),
      TT.TTSFPMUL(3, 4, 9, 3, 0),
      TT.TTSFPSTORE(1, 3, 7, 0),
      TT.TTSFPSTORE(3, 3, 7, 2),
      TT.TTINCRWC(0, 2, 0, 0),
    ), iterations=4, initialize=tile == 0)
  stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(m)
  profile.record('compute')
  profile.record('pack')
  if diagnostic:
    _set_thread_cfg(m, 1, 0)
    m.emit(TT.TTSFPSTORE(0, 3, 3, tiles * 64))
  publish_dst(m)
  if diagnostic:
    count = p.reg()
    p.li(count, 16)
    emit_pack_dst_to_cb(p, tiles, SCALE, count, output_format=F32)
  _pack_output(p, tiles, 0, wait=not diagnostic)
  # Both RISCs read the same core wall clock. Stop on the packer itself,
  # after PACK0 drains, so completion cannot be confused with loader credits.
  profile.kernel = p
  profile.record('pack')
  profile.record('L1 to L1')
  profile._validate()
  return {k.role: k.lower() for k in (u, m, p)}, profile


@pytest.mark.parametrize('n', (1024, 2048))
def test_llama3_rmsnorm(bh, n):
  images, profile = _images(n)
  rng = np.random.default_rng(42)
  samples = {
    'arange': np.arange(n, dtype=np.float32),
    'normal': rng.normal(size=n).astype(np.float32),
    'small': (rng.normal(size=n) * 1e-4).astype(np.float32),
    'zero': np.zeros(n, dtype=np.float32),
    'outlier': np.concatenate(([100.0], rng.normal(size=n-1))).astype(np.float32),
  }
  gamma_bits = _bf16_round(rng.uniform(0.5, 1.5, n).astype(np.float32))
  gamma = _from_bf16(gamma_bits).astype(np.float64)
  timings = []
  for name, values in samples.items():
    bits = _bf16_round(values)
    x = _from_bf16(bits).astype(np.float64)
    expected_scale = 1 / np.sqrt(np.mean(x*x) + EPS)
    ref = x * gamma * expected_scale
    for sample in range(11 if name == 'normal' else 1):
      with TLBWindow(bh.device.pcie.fd, bh.core) as w:
        w.target(0, bh.core)
        w.write(INPUT, bits.tobytes())
        w.write(GAMMA, gamma_bits.tobytes())
        w.write(OUTPUT, b'\xa5' * (n*2 + 64))
        w.write(SCALE, b'\xa5' * 128)
      bh.launch(images)
      scale = np.frombuffer(bh.read_l1(bh.core, SCALE, 4), dtype='<f4')[0]
      y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, OUTPUT, n*2), dtype='<u2'))
      assert bh.read_l1(bh.core, OUTPUT+n*2, 64) == b'\xa5'*64
      assert bh.read_l1(bh.core, SCALE+64, 64) == b'\xa5'*64
      np.testing.assert_allclose(scale, expected_scale, rtol=2e-5, atol=0)
      np.testing.assert_allclose(y, ref, rtol=0.008, atol=1e-7)
      if name == 'normal' and sample:
        timings.append(_read_intervals(bh, profile.l1_address, ('L1 to L1', 'compute', 'pack')))
    nz = ref != 0
    worst = np.max(np.abs(y[nz]/ref[nz]-1)) if np.any(nz) else 0
    print(f'N={n} {name}: scale error={100*(scale/expected_scale-1):+.7f}%, '
          f'worst output error={100*worst:.5f}%')
  print(f'N={n}: ' + '; '.join(f'{label} median={median(t[label] for t in timings)}, '
        f'min={min(t[label] for t in timings)}, max={max(t[label] for t in timings)} cycles'
        for label in ('L1 to L1', 'compute', 'pack')))


def test_rmsnorm_side_by_side(bh):
  """Identical 1024-element normal inputs, alternating order, full output timing."""
  from tests.compute.fpu import test_rmsnorm_reduce as gap
  cases = {'llama3': _images(1024)}
  for weights, normalize in (('l1', 'fpu'), ('sfpu', 'fpu'),
                             ('sfpu', 'sfpu'), ('sfpu', 'tf32-broadcast')):
    profile = Profiler(None)
    name = f'GAPOOL TF32 / {weights} weights / {normalize} normalize'
    cases[name] = (gap._images('tf32', 2, normalize=normalize,
                               weights=weights, profile=profile), profile)
  rng = np.random.default_rng(42)
  xb = _bf16_round(rng.normal(size=1024).astype(np.float32))
  gb = _bf16_round(rng.uniform(0.5, 1.5, 1024).astype(np.float32))
  x, g = _from_bf16(xb).astype(np.float64), _from_bf16(gb).astype(np.float64)
  scale_ref = 1 / np.sqrt(np.mean(x*x) + EPS)
  ref = x * g * scale_ref
  times, errors = {name: [] for name in cases}, {}
  for sample in range(21):
    for name in tuple(cases)[::1 if sample % 2 == 0 else -1]:
      baseline = name == 'llama3'
      addresses = ((INPUT, GAMMA, OUTPUT, SCALE) if baseline else
                   (gap.INPUT, gap.GAMMA, gap.NORMALIZED, gap.OUTPUT))
      a, b, out, scale_addr = addresses
      with TLBWindow(bh.device.pcie.fd, bh.core) as w:
        w.target(0, bh.core)
        w.write(a, xb.tobytes())
        w.write(b, gb.tobytes())
        w.write(out, b'\xa5' * (2048 + 64))
        w.write(scale_addr, b'\xa5' * 128)
      images, profile = cases[name]
      bh.launch(images)
      scale = np.frombuffer(bh.read_l1(bh.core, scale_addr, 4), dtype='<f4')[0]
      y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, out, 2048), dtype='<u2'))
      assert bh.read_l1(bh.core, out+2048, 64) == b'\xa5'*64
      np.testing.assert_allclose(y, ref, rtol=0.008, atol=1e-7)
      np.testing.assert_allclose(scale, scale_ref, rtol=2e-5 if baseline else 3e-4)
      labels = ('L1 to L1', 'compute', 'pack') if baseline else ('empty', 'L1 to L1', 'reduction')
      if sample:
        times[name].append(_read_intervals(bh, profile.l1_address, labels)['L1 to L1'])
      errors[name] = (100*abs(scale/scale_ref-1), 100*np.max(np.abs(y/ref-1)))
  for name in cases:
    print(f'{name}: median={median(times[name])}, min={min(times[name])}, '
          f'max={max(times[name])} cycles; scale error={errors[name][0]:.7f}%, '
          f'worst output error={errors[name][1]:.5f}%')
