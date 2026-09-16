"""FPU x*gamma; SFPU macros accumulate squares and apply the final scale.

Run on card 1:
  PYTHONPATH=. python3 -m pytest -q -s tests/compute/fpu/test_rmsnorm_hybrid.py \
    --bh-hardware --bh-device=1 --bh-core=2

Dst tile 0 preserves x; tiles 1..T hold FP32 x*gamma, then normalized output.
Both sources are unpacked once per tile. No reduction weights or TF32 moves.
Compare queued, instruction-interleaved, and explicitly serialized schedules.
Queued allows independent engines to proceed without promising actual overlap.
All timings end on the packer after BF16 output is in L1; no host/NoC timing.
The compute interval starts after the first x copy; at 2048 elements it also
includes staging the second tile. L1-to-L1 is the comparable total interval.
The default exports only y and reuses unpack descriptors/MOP across tiles;
the diagnostic/original case retains the FP32 scale export for an ablation.
Square macros are default for batched math; square_macro=False keeps the
explicit load/MAD control. Two accumulator chains use L0/L2 and L1/L3.
Setup has not been moved outside the existing timing interval.
"""
from statistics import median

import numpy as np
import pytest

from asm import Asm
from ttko.isa import Tensix as TT
from pcie import TLBWindow
from tests.profiler import Profiler
from tests.compute.fpu import test_rmsnorm_llama3 as llama
from tests.compute.fpu.test_rmsnorm_reduce import (
  _unpack_pair_tile, _await_sources, _constant, _bf16_round, _from_bf16,
  _read_intervals,
)
from tests.movement.unpacker.unpack import (
  F32, CFG_BASE, Stall, Wait, Sem, SemWait,
  _set_thread_cfg, _rmw_cfg_byte, configure_fp32_dst,
  pc_sync, stall, publish_dst, sem_wait, sem_get, sem_post,
)
from tests.movement.packer.pack import (
  emit_pack_dst_to_cb,
)

INPUT, GAMMA, OUTPUT, SCALE, EPS = llama.INPUT, llama.GAMMA, llama.OUTPUT, llama.SCALE, llama.EPS
SPLIT_SYNC = SCALE + 512


def _configure_apply_macro(m):
  m.emit(TT.TTSFPMUL(0, 0, 9, 12, 0))
  m.emit(TT.TTSFPLOADI(0, 8, 0x1300))
  m.emit(TT.TTSFPLOADI(0, 10, 0x8400))
  m.emit(TT.TTSFPCONFIG(0, 4, 0))
  m.emit(TT.TTSFPCONFIG(3, 8, 1))


def _images(n, *, schedule='queued', diagnostic=False, reuse_unpack=True,
            square_macro=None, prefetch=None, trace=None):
  if n not in (1024, 2048, 3072, 4096):
    raise ValueError('expected 1..4 tiles of 1024 elements')
  if prefetch is None:
    prefetch = reuse_unpack and schedule in ('queued', 'serialized')
  if prefetch and (not reuse_unpack or schedule not in ('queued', 'serialized')):
    raise ValueError('prefetch requires reused unpack configuration and TRISC1 math')
  if schedule not in ('queued', 'interleaved', 'serialized', 'split0', 'split2'):
    raise ValueError('unknown schedule')
  if square_macro is None:
    square_macro = schedule in ('queued', 'serialized')
  if square_macro and schedule not in ('queued', 'serialized'):
    raise ValueError('square macros require batched math on TRISC1')
  tiles = n // 1024
  u, m, p = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  split = schedule in ('split0', 'split2')
  s = u if schedule == 'split0' else p
  profile = Profiler(m)
  configure_fp32_dst(m, 0)
  _rmw_cfg_byte(m, CFG_BASE + 4, 3, 0x40, 0x40)
  m.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  m.emit(TT.TTSFPENCC(0, 0, 0, 2))
  m.emit(TT.TTSFPCONFIG(0, 15, 1))
  m.emit(TT.TTSFPNOP())
  # Each phase traverses all eight independent 8x16 Dst blocks. Sources
  # advance modulo 64; only the final block advances/resets fidelity.
  for mod, step, phase in ((0, 0x808, 0), (1, 0x808, 1 << 13),
                           (2, 0x808, 1 << 15), (3, 0, 0)):
    _set_thread_cfg(m, 12 + mod, step)
    _set_thread_cfg(m, 28 + mod, phase)
    _set_thread_cfg(m, 47 + mod, 0)
  # Macro 0: multiply loaded vector by L0 at t+1, store at t+3.
  # Cycle-based delays, FP32 stores; explicit NOPs drain the final events.
  if square_macro:
    # Two independent accumulator chains ping-pong between L0/L2 and L1/L3.
    # A macro forces VD to the loaded register; VC keeps the prior sum in
    # its partner register. Two cycles separate dependent MAD operations.
    for reg in range(4):
      m.emit(TT.TTSFPMAD(reg, reg, reg ^ 2, 12+reg, 0))
      m.emit(TT.TTSFPCONFIG((0x84+reg) << 8, 4+reg, 1))
    m.emit(TT.TTSFPCONFIG(3, 8, 1))
    _constant(m, 2, 0)
    _constant(m, 3, 0)
  else:
    _configure_apply_macro(m)
  _constant(m, 7, 0)
  pc_sync(u)
  sem_post(u, Sem.UNPACK_TO_DEST)
  sem_wait(m, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(m, Sem.UNPACK_TO_DEST)
  pc_sync(m)
  profile.record('L1 to L1')
  for tile in range(tiles):
    if not reuse_unpack:
      _unpack_pair_tile(u, INPUT + tile*2048, GAMMA + tile*2048)
    else:
      llama._unpack_reused(u, tile, prefetch=prefetch, trace=trace)
    llama._await_unpacked(m, tile, prefetch=prefetch)
    for row in range(0, 64, 8):
      m.emit(TT.TTMOVA2D(0, row, 3, 2, row))
    stall(m, Stall.SFPU, Wait.MATH)
    if trace is not None:
      pc_sync(m)
      llama._timestamp(m, trace + tile*16+8)
    if tile == 0:
      pc_sync(m)
      profile.record('compute')
    if split:
      # Dst scratch is ready; a different Tensix thread owns its own RWCs.
      stall(m, Stall.SYNC, Wait.MATH)
      pc_sync(m)
      m.write(SPLIT_SYNC, tile+1)
      m.fence()
      for register in (1, 15, 31, 50):
        _set_thread_cfg(s, register, 0)
      s.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xf))
      s.wait(SPLIT_SYNC, tile+1, bytes=4)
      for row in range(0, 64, 2):
        s.emit(TT.TTSFPLOAD(0, 3, 3, row))
        s.emit(TT.TTSFPMAD(0, 0, 7, 7, 0))
      stall(s, Stall.SYNC, Wait.SFPU)
      pc_sync(s)
      s.write(SPLIT_SYNC+16, tile+1)
      s.fence()
    m.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    for phase in range(4):
      for slot in range(8):
        mod = 0 if slot < 7 else (1 if phase < 3 else 2)
        m.emit(TT.TTELWMUL(0, 0, 0, mod, (tile+1)*64 + slot*8))
        if schedule == 'interleaved':
          m.emit(TT.TTSFPLOAD(0, 3, 3, 2*(phase*8+slot)))
          m.emit(TT.TTSFPMAD(0, 0, 7, 7, 0))
    if not split and schedule != 'interleaved':
      if schedule == 'serialized':
        stall(m, Stall.SFPU, Wait.MATH)
      for row in range(0, 64, 2):
        if square_macro:
          reg = (row // 2) % 4
          m.emit(TT.TTSFPLOADMACRO((reg << 2) | reg, 3, 3, row))
        else:
          m.emit(TT.TTSFPLOAD(0, 3, 3, row))
          m.emit(TT.TTSFPMAD(0, 0, 7, 7, 0))
      if square_macro:
        for _ in range(3):
          m.emit(TT.TTSFPNOP())
    stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
    if trace is not None:
      pc_sync(m)
      llama._timestamp(m, trace + tile*16+12)
    if split:
      pc_sync(m)
      m.wait(SPLIT_SYNC+16, tile+1, bytes=4)
    m.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  if square_macro:
    m.emit(TT.TTSFPADD(10, 2, 3, 7, 0))
    m.emit(TT.TTSFPNOP())
    # Reconfiguration is deliberately inside the measured compute interval.
    _configure_apply_macro(m)
  # The shared finalizer consumes partial sums in L0.
  m.emit(TT.TTSFPMOV(0, 7, 0, 0))
  llama._finalize(m, n)
  stall(m, Stall.SFPU, Wait.MATH)
  for tile in range(tiles):
    for vector in range(32):
      # Four rotating LRegs leave each vector live through its delayed store.
      reg = 1 + vector % 4
      row = (tile+1)*64 + vector*2
      m.emit(TT.TTSFPLOADMACRO(reg & 3, 3, 3, row | (reg >> 2)))
  for _ in range(4):
    m.emit(TT.TTSFPNOP())
  stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(m)
  profile.record('compute')
  profile.record('pack')
  if diagnostic:
    m.emit(TT.TTSFPSTORE(0, 3, 3, 0))
  publish_dst(m)
  if diagnostic:
    count = p.reg()
    p.li(count, 16)
    emit_pack_dst_to_cb(p, 0, SCALE, count, output_format=F32)
  llama._pack_output(p, tiles, 1, wait=not diagnostic)
  profile.kernel = p
  profile.record('pack')
  profile.record('L1 to L1')
  profile._validate()
  return {k.role: k.lower() for k in (u, m, p)}, profile


@pytest.mark.parametrize('n', (1024, 2048))
@pytest.mark.parametrize('fair', (False, True), ids=('ablations', 'fair'))
def test_hybrid_rmsnorm(bh, n, fair):
  cases = {'llama3': llama._images(n), 'hybrid queued': _images(n, square_macro=False),
           'hybrid macro diagnostic': _images(n, square_macro=True, diagnostic=True),
           'hybrid original': _images(n, diagnostic=True, reuse_unpack=False, square_macro=False),
           'hybrid no export': _images(n, reuse_unpack=False, square_macro=False),
           'hybrid interleaved': _images(n, schedule='interleaved'),
           'hybrid serialized': _images(n, schedule='serialized', square_macro=False)}
  if fair:
    cases = {'llama3 output-only': llama._images(n, diagnostic=False, reuse_unpack=True, prefetch=True),
             'hybrid queued': _images(n, square_macro=False),
             'hybrid square macro': _images(n, square_macro=True),
             'hybrid split0': _images(n, schedule='split0'),
             'hybrid split2': _images(n, schedule='split2')}
  rng = np.random.default_rng(42)
  inputs = {'arange': np.arange(n), 'normal': rng.normal(size=n),
            'small': rng.normal(size=n)*1e-4, 'zero': np.zeros(n),
            'outlier': np.concatenate(([100.0], rng.normal(size=n-1)))}
  gb = _bf16_round(rng.uniform(-1.5, 1.5, n))
  gamma = _from_bf16(gb).astype(np.float64)
  times = {name: [] for name in cases}
  worst = {name: [0.0, 0.0] for name in cases}
  for kind, values in inputs.items():
    xb = _bf16_round(values)
    x = _from_bf16(xb).astype(np.float64)
    scale_ref = 1 / np.sqrt(np.mean(x*x)+EPS)
    ref = x*gamma*scale_ref
    for sample in range((101 if fair else 21) if kind == 'normal' else 1):
      for name in tuple(cases)[::1 if sample % 2 == 0 else -1]:
        with TLBWindow(bh.device.pcie.fd, bh.core) as w:
          w.target(0, bh.core)
          w.write(INPUT, xb.tobytes())
          w.write(GAMMA, gb.tobytes())
          w.write(OUTPUT, b'\xa5'*(n*2+64))
          w.write(SCALE, b'\xa5'*128)
          w.write(SPLIT_SYNC, bytes(32))
        images, profile = cases[name]
        bh.launch(images)
        scale = np.frombuffer(bh.read_l1(bh.core, SCALE, 4), dtype='<f4')[0]
        y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, OUTPUT, n*2), dtype='<u2'))
        assert bh.read_l1(bh.core, OUTPUT+n*2, 64) == b'\xa5'*64
        assert bh.read_l1(bh.core, SCALE+64, 64) == b'\xa5'*64
        diagnostic = name in ('llama3', 'hybrid original', 'hybrid macro diagnostic')
        if diagnostic:
          np.testing.assert_allclose(scale, scale_ref, rtol=2e-5, atol=0, err_msg=name)
        else:
          assert bh.read_l1(bh.core, SCALE, 128) == b'\xa5'*128
        np.testing.assert_allclose(y, ref, rtol=0.004, atol=1e-7, err_msg=name)
        nz = ref != 0
        error = np.max(np.abs(y[nz]/ref[nz]-1)) if np.any(nz) else 0
        if diagnostic:
          worst[name][0] = max(worst[name][0], abs(scale/scale_ref-1))
        worst[name][1] = max(worst[name][1], error)
        if kind == 'normal' and sample:
          times[name].append(_read_intervals(bh, profile.l1_address,
                                            ('L1 to L1', 'compute', 'pack')))
  for name in cases:
    print(f'N={n} {name}: ' + '; '.join(
      f'{label} median={median(t[label] for t in times[name])}, '
      f'min={min(t[label] for t in times[name])}, max={max(t[label] for t in times[name])}'
      for label in ('L1 to L1', 'compute', 'pack')) +
      f' cycles; ' +
      (f'worst scale error={100*worst[name][0]:.7f}%, '
       if name in ('llama3', 'hybrid original', 'hybrid macro diagnostic') else 'scale not exported; ') +
      f'worst output error={100*worst[name][1]:.5f}%')
  if fair:
    baseline = median(t['L1 to L1'] for t in times['llama3 output-only'])
    for name in tuple(cases)[1:]:
      hybrid = median(t['L1 to L1'] for t in times[name])
      print(f'N={n} fair {name}: {baseline/hybrid:.3f}x speedup; '
            f'{100*(1-hybrid/baseline):.2f}% fewer L1-to-L1 cycles')


@pytest.mark.parametrize('n', (1024, 2048))
def test_square_macro_precision(bh, n):
  """Check changed summation order across seeds and dynamic ranges."""
  variants = {macro: _images(n, diagnostic=True, square_macro=macro)
              for macro in (False, True)}
  worst_scale, worst_output = 0.0, 0.0
  for seed in range(12):
    rng = np.random.default_rng(seed)
    amplitude = (1e-8, 1e-4, 1., 1e4, 1e8, None)[seed % 6]
    x = rng.normal(size=n)
    x *= rng.lognormal(0, 5, n) if amplitude is None else amplitude
    xb = _bf16_round(x)
    gb = _bf16_round(rng.uniform(-2, 2, n))
    x, gamma = _from_bf16(xb).astype(np.float64), _from_bf16(gb).astype(np.float64)
    scale_ref = 1 / np.sqrt(np.mean(x*x)+EPS)
    ref = x*gamma*scale_ref
    for macro, (images, _) in variants.items():
      bh.launch(images, l1={INPUT: xb.tobytes(), GAMMA: gb.tobytes(),
                           OUTPUT: b'\xa5'*(2*n+64), SCALE: b'\xa5'*128})
      scale = np.frombuffer(bh.read_l1(bh.core, SCALE, 4), dtype='<f4')[0]
      y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, OUTPUT, 2*n), dtype='<u2'))
      np.testing.assert_allclose(scale, scale_ref, rtol=2e-5, atol=0, err_msg=str((seed, macro)))
      np.testing.assert_allclose(y, ref, rtol=0.004, atol=1e-7, err_msg=str((seed, macro)))
      assert bh.read_l1(bh.core, OUTPUT+2*n, 64) == b'\xa5'*64
      assert bh.read_l1(bh.core, SCALE+64, 64) == b'\xa5'*64
      if macro:
        worst_scale = max(worst_scale, abs(scale/scale_ref-1))
        nz = ref != 0
        worst_output = max(worst_output, np.max(np.abs(y[nz]/ref[nz]-1)))
  print(f'N={n} macro precision: worst scale={100*worst_scale:.7f}%, '
        f'worst output={100*worst_output:.5f}%')


@pytest.mark.parametrize('n', (1024, 2048, 3072, 4096))
def test_unpack_prefetch(bh, n):
  """Same macro math/packing, only the next-tile unpack dependency changes."""
  variants = {enabled: _images(n, prefetch=enabled) for enabled in (False, True)}
  timings = {enabled: [] for enabled in variants}
  rng = np.random.default_rng(84)
  inputs = {'normal': rng.normal(size=n), 'arange': np.arange(n),
            'small': rng.normal(size=n)*1e-5, 'zero': np.zeros(n),
            'outliers': rng.normal(size=n)}
  # Different magnitudes in every tile catch incorrect bank reuse/order.
  for tile in range(n//1024):
    inputs['outliers'][tile*1024] = (tile+1)*100
    inputs['normal'][tile*1024:(tile+1)*1024] *= 2**tile
  gb = _bf16_round(rng.uniform(-2, 2, n))
  gamma = _from_bf16(gb).astype(np.float64)
  worst = 0.
  for kind, values in inputs.items():
    xb = _bf16_round(values)
    x = _from_bf16(xb).astype(np.float64)
    ref = x*gamma / np.sqrt(np.mean(x*x)+EPS)
    for sample in range(102 if kind == 'normal' else 1):
      outputs = {}
      for enabled in (False, True)[::1 if sample % 2 == 0 else -1]:
        images, profile = variants[enabled]
        bh.launch(images, l1={INPUT: xb.tobytes(), GAMMA: gb.tobytes(),
                             OUTPUT: b'\xa5'*(2*n+64), SCALE: b'\xa5'*128})
        outputs[enabled] = bh.read_l1(bh.core, OUTPUT, 2*n)
        y = _from_bf16(np.frombuffer(outputs[enabled], dtype='<u2'))
        np.testing.assert_allclose(y, ref, rtol=0.004, atol=1e-7,
                                   err_msg=str((n, kind, enabled)))
        assert bh.read_l1(bh.core, OUTPUT+2*n, 64) == b'\xa5'*64
        assert bh.read_l1(bh.core, SCALE, 128) == b'\xa5'*128
        nz = ref != 0
        if np.any(nz):
          worst = max(worst, np.max(np.abs(y[nz]/ref[nz]-1)))
        if kind == 'normal' and sample >= 2:
          timings[enabled].append(_read_intervals(bh, profile.l1_address,
                                                 ('L1 to L1', 'compute', 'pack')))
      assert outputs[False] == outputs[True], (n, kind, 'prefetch changed output bits')
  for enabled in timings:
    print(f'N={n} prefetch={enabled}: ' + '; '.join(
      f'{label} median={median(t[label] for t in timings[enabled])}, '
      f'min={min(t[label] for t in timings[enabled])}, max={max(t[label] for t in timings[enabled])}'
      for label in ('L1 to L1', 'compute', 'pack')) + f'; worst error={100*worst:.5f}%')


def test_unpack_prefetch_timeline(bh):
  trace = SPLIT_SYNC+256
  xb = _bf16_round(np.ones(4096))
  for enabled in (False, True):
    images, _ = _images(4096, prefetch=enabled, trace=trace)
    bh.launch(images, l1={INPUT: xb.tobytes(), GAMMA: xb.tobytes(), trace: bytes(64)})
    y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, OUTPUT, 8192), dtype='<u2'))
    np.testing.assert_array_equal(y, 1)
    raw = np.frombuffer(bh.read_l1(bh.core, trace, 64), dtype='<u4').reshape(4,4)
    relative = (raw.astype(np.int64)-int(raw[0,0])) % (1 << 32)
    print(f'prefetch={enabled}: tile [unpack start/end, math start/end] cycles={relative.tolist()}')
