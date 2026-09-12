"""Independent per-lane movement/predicate proofs with full-Dst poison guards."""
import json
from statistics import median
from struct import pack, unpack

import pytest

from asm import Asm
from fw.consts import TensixL1
from isa import Tensix as TT
from tests.profiler import Profiler
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, Sem, SemWait, Stall, _set_thread_cfg, configure_fp32_dst,
  emit_unpack_to_dst, pc_sync, publish_dst, sem_get, sem_post, sem_wait,
)
from tests.operation_pocs.sfpu_movement import emitters as sf

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
OUTPUT = INPUT + 65536
N = 8192
K = 16
MASKS = [0, 0xffffffff, 0x55555555, 0xaaaaaaaa] + [1 << i for i in range(32)]


def lane_index(position, lane):
  return (position // 2) * 64 + (lane // 8) * 16 + (lane % 8) * 2 + position % 2


def fixture(*, accumulated_control=False):
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  count = loader.reg()
  loader.li(count, N * 4)
  emit_unpack_to_dst(loader, INPUT, count, 0, 0)
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  configure_fp32_dst(math, 0)
  for register in (12, 28, 47):
    _set_thread_cfg(math, register, 0)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  sf.predicate(math)
  sf.drain(math)
  profiler = Profiler(math)
  if accumulated_control:
    for _ in range(4):
      profiler.accumulate('control')
      sf.drain(math)
      profiler.accumulate('control')
  else:
    profiler.record('control')
    sf.drain(math)
    profiler.record('control')
  values = [float(10000 + i) for i in range(N)]
  return loader, math, packer, profiler, values


def finish(bh, request, kernels, profiler, initial, expected, case, repetitions):
  loader, math, packer = kernels
  sf.drain(math)
  pc_sync(math)
  publish_dst(math)
  count = packer.reg()
  packer.li(count, N)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  images = {k.role: k.lower() for k in kernels}
  l1 = {INPUT: pack(f'<{N}f', *initial), OUTPUT: bytes([0xa5]) * (N * 4 + 64)}
  samples = []
  for iteration in range(8):  # One warmup, seven retained independent launches.
    bh.launch(images, l1=l1, profiler=profiler)
    actual = unpack(f'<{N}I', bh.read_l1(bh.core, OUTPUT, N * 4))
    desired = unpack(f'<{N}I', pack(f'<{N}f', *expected))
    mismatch = [(i, hex(a), hex(e)) for i, (a, e) in enumerate(zip(actual, desired)) if a != e]
    assert not mismatch, mismatch[:20]
    assert bh.read_l1(bh.core, OUTPUT + N * 4, 64) == bytes([0xa5]) * 64
    if iteration:
      samples.append(dict(profiler.last))
  result = dict(case=case, device=request.config.getoption('--bh-device'),
                core=bh.core, core_index=bh.core_index, dtype='FP32', N=128,
                warmup=1, samples=samples, K=repetitions,
                summary={label: dict(min=min(s[label] for s in samples),
                                    median=median(s[label] for s in samples),
                                    max=max(s[label] for s in samples),
                                    median_per_op=median(s[label] for s in samples) / repetitions.get(label, 1))
                         for label in samples[0]})
  print('SFPU_RESULT ' + json.dumps(result, sort_keys=True))


@pytest.mark.parametrize('start', (0, 14, 126))
def test_load_lane_mapping(bh, request, start):
  loader, math, packer, p, initial = fixture()
  expected = initial.copy()
  p.record('load')
  for _ in range(K):
    for position in range(4):
      sf.load(math, position, start, position=position)
  sf.drain(math)
  p.record('load')
  # Independent stores: values in even columns, physical lane*2 tags in odd.
  sf.copy(math, 4, 15)
  for position in range(4):
    base = 28 * 128 + position * 64
    math.emit(TT.TTSFPSTORE(position, 3, 0, base // 16))
    math.emit(TT.TTSFPSTORE(4, 4, 0, base // 16 + 2))
    for lane in range(32):
      element = (lane // 8) * 16 + (lane % 8) * 2
      expected[base + element] = initial[start // 2 * 128 + lane_index(position, lane)]
      expected[base + element + 1] = unpack('<f', pack('<I', lane * 2))[0]
  finish(bh, request, (loader, math, packer), p, initial, expected,
         f'load:allocation={start}:all_positions:independent_lane_tags', {'load': K * 4})


@pytest.mark.parametrize('operation', ('store', 'loadi', 'copy', 'zero', 'one', 'l8', 'l15'))
@pytest.mark.parametrize('start', (0, 126))
def test_movement(bh, request, operation, start):
  loader, math, packer, p, initial = fixture()
  expected = initial.copy()
  sf.load(math, 1, start)
  sf.loadi(math, 0, -7.125)
  label = operation
  p.record(label)
  for _ in range(K):
    if operation == 'store':
      for position in range(4): sf.store(math, 1, start, position=position)
    elif operation == 'loadi': sf.loadi(math, 0, 1.234567)
    elif operation == 'copy': sf.copy(math, 0, 1)
    else: sf.copy(math, 0, {'zero': 9, 'one': 10, 'l8': 8, 'l15': 15}[operation])
  sf.drain(math)
  p.record(label)
  if operation != 'store':
    for position in range(4): sf.store(math, 0, start, position=position, raw=operation == 'l15')
  for position in range(4):
    for lane in range(32):
      index = start // 2 * 128 + lane_index(position, lane)
      if operation in ('copy', 'store'): value = initial[start // 2 * 128 + lane_index(0, lane)]
      elif operation == 'loadi': value = unpack('<f', pack('<f', 1.234567))[0]
      elif operation == 'zero': value = 0.
      elif operation == 'one': value = 1.
      elif operation == 'l8': value = unpack('<f', pack('<f', .8373))[0]
      else: value = unpack('<f', pack('<I', lane * 2))[0]
      expected[index] = value
  finish(bh, request, (loader, math, packer), p, initial, expected,
         f'{operation}:allocation={start}:all_positions', {label: K * (4 if operation == 'store' else 1)})


@pytest.mark.parametrize('mask', MASKS, ids=lambda m: f'{m:08x}')
@pytest.mark.parametrize('kind', ('load', 'store', 'add', 'loadi', 'copy'))
def test_predicate(bh, request, mask, kind):
  loader, math, packer, p, initial = fixture(accumulated_control=True)
  expected = initial.copy()
  start = 126 if mask & 1 else 14
  for position in range(4):
    sf.predicate(math)
    if kind in ('load', 'loadi', 'copy'): sf.loadi(math, 0, -100.)
    else: sf.load(math, 0, start, position=position)
    if kind == 'store': math.emit(TT.TTSFPADDI(0x40a0, 0, 0))
    if kind == 'copy': sf.load(math, 1, start, position=position)
    # Complete predicate+masked operation cost, including scratch construction/drain.
    # Begin from an all-off predecessor to prove mask replacement restores lanes.
    sf.predicate(math, 0)
    label = f'predicate_and_masked_{kind}'
    p.accumulate(label)
    sf.predicate(math, mask)
    if kind == 'load': sf.load(math, 0, start, position=position)
    elif kind == 'store': sf.store(math, 0, start, position=position)
    elif kind == 'loadi': sf.loadi(math, 0, 1.234567)
    elif kind == 'copy': sf.copy(math, 0, 1)
    else: math.emit(TT.TTSFPADDI(0x40a0, 0, 0))
    sf.drain(math)
    p.accumulate(label)
    p.accumulate('reset')
    sf.predicate(math)
    sf.drain(math)
    p.accumulate('reset')
    if kind != 'store': sf.store(math, 0, start, position=position)
    for lane in range(32):
      index = start // 2 * 128 + lane_index(position, lane)
      active = bool(mask & (1 << lane))
      if kind in ('load', 'copy'): expected[index] = initial[index] if active else -100.
      elif kind == 'loadi': expected[index] = unpack('<f', pack('<f', 1.234567))[0] if active else -100.
      else: expected[index] = initial[index] + (5 if active else 0)
  # Consecutive unmasked operation makes reset visible separately from stores.
  sf.loadi(math, 2, 77.)
  sf.store(math, 2, 60)
  for lane in range(32): expected[30 * 128 + lane_index(0, lane)] = 77.
  finish(bh, request, (loader, math, packer), p, initial, expected,
         f'predicate:{mask:08x}:{kind}:allocation={start}', {label: 4, 'reset': 4, 'control': 4})


@pytest.mark.parametrize('source', range(16))
def test_registers_and_aliases(bh, request, source):
  loader, math, packer, p, initial = fixture()
  expected = initial.copy()
  if source < 8:
    sf.load(math, source, 14)
    vector = [initial[7 * 128 + lane_index(0, lane)] for lane in range(32)]
  elif source in (11, 12, 13, 14):
    # Configuration is explicit fixture state; these are not immutable constants.
    sf.load(math, 0, 14)
    math.emit(TT.TTSFPCONFIG(0, source, 0))
    vector = [initial[7 * 128 + lane_index(0, lane % 8)] for lane in range(32)]
  elif source == 15:
    vector = [unpack('<f', pack('<I', lane * 2))[0] for lane in range(32)]
  else:
    vector = [unpack('<f', pack('<f', {8: .8373, 9: 0., 10: 1.}[source]))[0]] * 32
  sf.drain(math)
  p.record('copy_all_writable')
  # Include self-copy. Once a source is copied, it has the same vector throughout.
  for destination in range(8): sf.copy(math, destination, source)
  sf.drain(math)
  p.record('copy_all_writable')
  for destination in range(8):
    sf.store(math, destination, 32 + destination * 2, raw=source == 15)
    for lane in range(32):
      expected[(16 + destination) * 128 + lane_index(0, lane)] = vector[lane]
  # Direct public store from each exposed register, with l12-l15 adapter scratch.
  p.record('store_exposed_register')
  sf.store(math, source, 80, raw=source == 15)
  sf.drain(math)
  p.record('store_exposed_register')
  for lane in range(32): expected[40 * 128 + lane_index(0, lane)] = vector[lane]
  finish(bh, request, (loader, math, packer), p, initial, expected,
         f'register:l{source}:copy_to_l0_l7:alias:store',
         {'copy_all_writable': 8, 'store_exposed_register': 1})


@pytest.mark.parametrize('bits', (0, 0x80000000, 1, 0x80000001, 0x007fffff,
                                 0x00800000, 0x3f800001, 0xc0012345,
                                 0x7f7fffff, 0x7f800000, 0xff800000, 0x7fc12345))
@pytest.mark.parametrize('raw', (False, True))
def test_immediate_and_store_bits(bh, request, bits, raw):
  loader, math, packer, p, initial = fixture()
  expected = initial.copy()
  p.record('loadi')
  for _ in range(K): sf.loadi(math, 7, unpack('<f', pack('<I', bits))[0])
  sf.drain(math)
  p.record('loadi')
  p.record('store')
  for _ in range(K):
    for position in range(4):
      sf.store(math, 7, 124, block=1, blocks=2, position=position, raw=raw)
  sf.drain(math)
  p.record('store')
  result_bits = bits if raw or bits & 0x7f800000 else bits & 0x80000000
  value = unpack('<f', pack('<I', result_bits))[0]
  expected[63 * 128:] = [value] * 128
  finish(bh, request, (loader, math, packer), p, initial, expected,
         f'bits:{bits:08x}:raw_store={raw}:allocation=124:block=1', {'loadi': K, 'store': K * 4})
