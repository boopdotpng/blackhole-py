"""The article's 2048-element SFPU and HiFi4 hybrid RMSNorm, timed alike.

Math is explicitly issued in both variants: no SFPLOADMACRO, replay, or math
MOP. Both use the same unpack/pack MOPs, source-bank prefetch, FP32 Dst,
single-chain square accumulation, reduction, rsqrt, and BF16 output rounding.
SFPU: x at rows 0:128, gamma at 128:256, output at 256:384.
Hybrid: scratch at 0:64, products/output at 64:192.

L1-to-L1 includes configuration, unpack, moves, math, synchronization and
packing. Stage+math excludes initial math configuration but includes unpack
and moves in BOTH variants. Pack includes publication and pack configuration.
No host, firmware launch, or DRAM/NoC transfer time is included. Timestamp
overhead is retained. The two inner intervals are not an exact decomposition.
"""
from statistics import median

import numpy as np

from asm import Asm
from ttko.isa import Tensix as TT
from tests.profiler import Profiler
from tests.compute.fpu import test_rmsnorm_llama3 as shared
from tests.compute.fpu.test_rmsnorm_reduce import _bf16_round, _from_bf16, _read_intervals
from tests.movement.unpacker.unpack import (
  CFG_BASE, Stall, Wait, _set_thread_cfg, _rmw_cfg_byte,
  configure_fp32_dst, pc_sync, stall, publish_dst,
)

N = 2048
LABELS = ('L1 to L1', 'stage+math', 'pack')


def _squares(m, first, last):
  for row in range(first, last, 2):
    m.emit(TT.TTSFPLOAD(1, 3, 3, row))
    m.emit(TT.TTSFPMAD(1, 1, 0, 0, 0))


def _images(hybrid):
  u, m, p = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  profile = Profiler(m)
  pc_sync(m)
  profile.record('L1 to L1')
  configure_fp32_dst(m, 0)
  _rmw_cfg_byte(m, CFG_BASE + 4, 3, 0x40, 0x40)
  m.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  m.emit(TT.TTSFPENCC(0, 0, 0, 2))
  m.emit(TT.TTSFPCONFIG(0, 15, 1))
  m.emit(TT.TTSFPNOP())
  # Stationary addressing for explicit SFPU loads and source-to-Dst moves.
  for register in (15, 31, 50):
    _set_thread_cfg(m, register, 0)
  if hybrid:
    for mod, phase in ((0, 0), (1, 1 << 13), (2, 1 << 15)):
      _set_thread_cfg(m, 12 + mod, 0x808)
      _set_thread_cfg(m, 28 + mod, phase)
      _set_thread_cfg(m, 47 + mod, 0)
  m.emit(TT.TTSFPLOADI(0, 0, 0))
  pc_sync(m)
  profile.record('stage+math')
  for tile in range(2):
    shared._unpack_reused(u, tile, prefetch=True)
    shared._await_unpacked(m, tile, prefetch=True)
    base = 0 if hybrid else tile*64
    for row in range(0, 64, 8):
      m.emit(TT.TTMOVA2D(0, row, 3, 2, base + row))
    if hybrid:
      stall(m, Stall.SFPU, Wait.MATH)
      m.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
      for phase in range(4):
        for slot in range(8):
          mod = 0 if slot < 7 else (1 if phase < 3 else 2)
          m.emit(TT.TTELWMUL(0, 0, 0, mod, (tile+1)*64 + slot*8))
      # Independent engines may overlap; no claim of full overlap.
      _squares(m, 0, 64)
      stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
    else:
      for row in range(0, 64, 4):
        m.emit(TT.TTMOVB2D(0, row, 3, 4, 128 + tile*64 + row))
    m.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
  if not hybrid:
    _squares(m, 0, 128)
  shared._finalize(m, N)
  m.emit(TT.TTSFPNOP())
  for row in range(0, 128, 2):
    m.emit(TT.TTSFPLOAD(1, 3, 3, row + (64 if hybrid else 0)))
    if not hybrid:
      m.emit(TT.TTSFPLOAD(2, 3, 3, row + 128))
    shared._mul(m, 1, 0, 1)
    if not hybrid:
      shared._mul(m, 1, 2, 1)
    m.emit(TT.TTSFPSTORE(1, 3, 3, row + (64 if hybrid else 256)))
  stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(m)
  profile.record('stage+math')
  profile.record('pack')
  publish_dst(m)
  shared._pack_output(p, 2, 1 if hybrid else 4)
  profile.kernel = p
  profile.record('pack')
  profile.record('L1 to L1')
  profile._validate()
  return {k.role: k.lower() for k in (u, m, p)}, profile


def test_blog_comparison(bh):
  cases = {name: _images(hybrid) for name, hybrid in (('SFPU', False), ('hybrid HiFi4', True))}
  rng = np.random.default_rng(42)
  inputs = {'normal': rng.normal(size=N), 'arange': np.arange(N),
            'small': rng.normal(size=N)*1e-4, 'zero': np.zeros(N),
            'outlier': np.concatenate(([100.], rng.normal(size=N-1)))}
  gb = _bf16_round(rng.uniform(-1.5, 1.5, N))
  gamma = _from_bf16(gb).astype(np.float64)
  times = {name: [] for name in cases}
  worst = {name: 0. for name in cases}
  differing = {}
  for kind, values in inputs.items():
    xb = _bf16_round(values)
    x = _from_bf16(xb).astype(np.float64)
    ref = x*gamma / np.sqrt(np.mean(x*x) + shared.EPS)
    for sample in range(102 if kind == 'normal' else 1):
      outputs = {}
      for name in tuple(cases)[::1 if sample % 2 == 0 else -1]:
        images, profile = cases[name]
        bh.launch(images, l1={shared.INPUT: xb.tobytes(), shared.GAMMA: gb.tobytes(),
                             shared.OUTPUT: b'\xa5'*(2*N+64), shared.SCALE: b'\xa5'*128})
        outputs[name] = np.frombuffer(bh.read_l1(bh.core, shared.OUTPUT, 2*N), dtype='<u2')
        y = _from_bf16(outputs[name])
        np.testing.assert_allclose(y, ref, rtol=0.004, atol=1e-7, err_msg=f'{name}/{kind}')
        assert bh.read_l1(bh.core, shared.OUTPUT+2*N, 64) == b'\xa5'*64
        assert bh.read_l1(bh.core, shared.SCALE, 128) == b'\xa5'*128
        nz = ref != 0
        if np.any(nz):
          worst[name] = max(worst[name], float(np.max(np.abs(y[nz]/ref[nz]-1))))
        if kind == 'normal' and sample >= 2:
          times[name].append(_read_intervals(bh, profile.l1_address, LABELS))
      differing[kind] = int(np.count_nonzero(outputs['SFPU'] != outputs['hybrid HiFi4']))
  print(f'\nN={N}; core={bh.core}; 2 warmups + 100 timed samples')
  for name in cases:
    print(f'{name}: ' + '; '.join(
      f'{label} median={median(t[label] for t in times[name])}, '
      f'min={min(t[label] for t in times[name])}, max={max(t[label] for t in times[name])}'
      for label in LABELS) + f' cycles; worst output relative error={100*worst[name]:.6f}%')
  baseline, hybrid = (median(t['L1 to L1'] for t in times[name]) for name in cases)
  print(f'Hybrid: {baseline/hybrid:.3f}x speedup, {100*(1-hybrid/baseline):.2f}% fewer cycles')
  print(f'BF16 output differences out of {N}: {differing}')


def test_matched_optimized_comparison(bh):
  """All totals start before math setup and finish after BF16 packing."""
  from tests.compute.fpu.test_rmsnorm_hybrid import _images as optimized
  cases = {'article SFPU': _images(False), 'article hybrid HiFi4': _images(True),
           'optimized hybrid HiFi4': optimized(N, include_setup=True),
           'optimized hybrid HiFi3': optimized(N, include_setup=True, fidelity=3),
           'optimized hybrid HiFi4 MOP': optimized(N, include_setup=True, elwmul_mop=True)}
  rng = np.random.default_rng(42)
  xb, gb = _bf16_round(rng.normal(size=N)), _bf16_round(rng.uniform(-2, 2, N))
  x, gamma = _from_bf16(xb).astype(np.float64), _from_bf16(gb).astype(np.float64)
  ref = x*gamma / np.sqrt(np.mean(x*x)+shared.EPS)
  times = {name: [] for name in cases}
  for sample in range(102):
    for name in tuple(cases)[::1 if sample % 2 == 0 else -1]:
      images, profile = cases[name]
      bh.launch(images, l1={shared.INPUT: xb.tobytes(), shared.GAMMA: gb.tobytes(),
                           shared.OUTPUT: b'\xa5'*(2*N+64), shared.SCALE: b'\xa5'*128})
      y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, shared.OUTPUT, 2*N), dtype='<u2'))
      np.testing.assert_allclose(y, ref, rtol=0.0045, atol=1e-7, err_msg=name)
      assert bh.read_l1(bh.core, shared.OUTPUT+2*N, 64) == b'\xa5'*64
      assert bh.read_l1(bh.core, shared.SCALE, 128) == b'\xa5'*128
      if sample >= 2:
        times[name].append(_read_intervals(bh, profile.l1_address, ('L1 to L1',))['L1 to L1'])
  for name, samples in times.items():
    print(f'N={N} {name}: setup-inclusive L1 to L1 median={median(samples)}, '
          f'min={min(samples)}, max={max(samples)} cycles')
