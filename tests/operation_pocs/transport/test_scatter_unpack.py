"""Dense L1 streams scattered into owned 128-element source/Dst slots.

Source scatter publishes only its final segment. Dst uses the existing exact
SFPU insertion adapter (not a claim of direct-UNPACR throughput).
"""
from statistics import median
from struct import pack

import pytest

from tests.movement.unpacker import unpack as u
from tests.operation_pocs.transport import test_source as s, test_dst as d


def encode(words, fmt):
  return pack(f'<{len(words)}H', *(w >> 16 for w in words)) if fmt == u.BF16 else pack(f'<{len(words)}I', *words)


SOURCE_CASES = [
  pytest.param(128, (0, 1, 2, 3), (128,) * 4, id='contiguous'),
  pytest.param(128, (7, 0, 5, 2), (128,) * 4, id='irregular'),
  pytest.param(128, (7, 6, 5, 4), (128,) * 4, id='reverse'),
  pytest.param(128, (7, 0, 5, 2), (1, 17, 73, 127), id='short-segments'),
  pytest.param(128, (7, 0, 5, 2, 6, 1, 4, 3), (128,) * 8, id='all-slots'),
]
PAIR_CASES = [
  pytest.param(256, (0, 2), (256, 256), id='pairs-contiguous'),
  pytest.param(256, (6, 0), (256, 256), id='pairs-reverse'),
  pytest.param(256, (6, 0), (129, 255), id='pairs-short'),
]


def run_source(bh, target, fmt, capacity, slots, lengths, *, native=False):
  images, profile = s.source_images(target, slots[0], fmt, capacity, segments=tuple(zip(slots, lengths)), native=native)
  a = [0x4000 + i % 256 for i in range(1024)]
  b = [0x4200 + i % 256 for i in range(1024)]
  words = [(0x3000 + i) << 16 | (i * 1031 & 65535) for i in range(sum(lengths))]
  expected_a, expected_b = a.copy(), b.copy()
  expected = expected_a if target == u.UnpackTarget.SRCA else expected_b
  offset = 0
  for slot, n in zip(slots, lengths):
    expected[slot * 128:slot * 128 + capacity] = [w >> 16 for w in words[offset:offset+n]] + [0] * (capacity-n)
    offset += n
  dst = pack('<8192I', *(0x43000000 + i * 1031 for i in range(8192)))
  source = encode(words, fmt)
  samples = []
  for sample in range(4):
    guard = bytes([0xA5 if sample % 2 else 0x5A]) * 64
    bh.launch(images, l1={s.A: pack('<1024H', *a), s.B: pack('<1024H', *b),
              s.INPUT: source, s.DST_INPUT: dst, s.DST_OUTPUT: guard * 513,
              s.SCRATCH: guard * ((capacity * 4 + 128) // 64), s.OUTPUT: guard * 129}, profiler=profile)
    assert bh.read_l1(bh.core, s.INPUT, len(source)) == source
    assert bh.read_l1(bh.core, s.OUTPUT, 8192) == pack('<2048I', *(w << 16 for w in expected_a + expected_b))
    assert bh.read_l1(bh.core, s.OUTPUT + 8192, 64) == guard
    assert bh.read_l1(bh.core, s.DST_OUTPUT, 32768) == dst
    assert bh.read_l1(bh.core, s.DST_OUTPUT + 32768, 64) == guard
    scratch_end = s.SCRATCH + capacity * (2 if fmt == u.BF16 else 4) + 64
    assert bh.read_l1(bh.core, scratch_end, 64) == guard
    if native:
      assert bh.read_l1(bh.core, s.SCRATCH, capacity * 4 + 128) == guard * ((capacity * 4 + 128) // 64)
    if sample: samples.append(profile.last['unpack complete'])
  print('SCATTER_UNPACK', 'native' if native else 'staged', target.name, fmt, slots, lengths, 'cycles', samples, 'median', median(samples))


@pytest.mark.parametrize('target', (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB))
@pytest.mark.parametrize('fmt', (u.BF16, u.F32))
@pytest.mark.parametrize('capacity,slots,lengths', SOURCE_CASES)
def test_scattered_source_unpack(bh, target, fmt, capacity, slots, lengths):
  run_source(bh, target, fmt, capacity, slots, lengths)


@pytest.mark.parametrize('fmt', (u.BF16, u.F32))
@pytest.mark.parametrize('capacity,slots,lengths', PAIR_CASES)
def test_scattered_matrix_pairs(bh, fmt, capacity, slots, lengths):
  run_source(bh, u.UnpackTarget.SRCA, fmt, capacity, slots, lengths)


@pytest.mark.parametrize('target', (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB))
@pytest.mark.parametrize('fmt', (u.BF16, u.F32))
@pytest.mark.parametrize('capacity,slots,lengths', SOURCE_CASES[:3] + SOURCE_CASES[4:])
def test_native_scattered_source_unpack(bh, target, fmt, capacity, slots, lengths):
  run_source(bh, target, fmt, capacity, slots, lengths, native=True)


@pytest.mark.parametrize('fmt', (u.BF16, u.F32))
@pytest.mark.parametrize('capacity,slots,lengths', PAIR_CASES[:2])
def test_native_scattered_matrix_pairs(bh, fmt, capacity, slots, lengths):
  run_source(bh, u.UnpackTarget.SRCA, fmt, capacity, slots, lengths, native=True)


@pytest.mark.parametrize('fmt', (u.BF16, u.F32))
@pytest.mark.parametrize('slots,lengths', [
  pytest.param((0, 1, 2, 3), (128,) * 4, id='contiguous'),
  pytest.param((63, 0, 31, 4), (128,) * 4, id='irregular'),
  pytest.param((63, 62, 61, 60), (128,) * 4, id='reverse'),
  pytest.param((63, 0, 31, 4), (1, 17, 73, 127), id='short-segments'),
  pytest.param((63, 0, 31, 4, 57, 8), (128,) * 6, id='six-segments'),
])
def test_scattered_dst_unpack(bh, fmt, slots, lengths):
  images, profile = d.dst_images(slots[0], fmt, segments=tuple(zip(slots, lengths)))
  initial = [0x43000000 + i * 1031 for i in range(8192)]
  words = [(0x3000 + i) << 16 | (i * 1031 & 65535) for i in range(sum(lengths))]
  a = [0x4000 + i % 256 for i in range(1024)]
  b = [0x4200 + i % 256 for i in range(1024)]
  expected, offset = initial.copy(), 0
  for slot, n in zip(slots, lengths):
    values = [w & 0xffff0000 if fmt == u.BF16 else w for w in words[offset:offset+n]]
    expected[slot*128:(slot+1)*128] = values + [0] * (128-n)
    offset += n
  source = encode(words, fmt)
  samples = []
  for sample in range(4):
    guard = bytes([0xA5 if sample % 2 else 0x5A]) * 64
    bh.launch(images, l1={d.INPUT: pack('<8192I', *initial), d.A: pack('<1024H', *a), d.B: pack('<1024H', *b),
              d.SHORT-64: guard + source + guard, d.OUTPUT: guard * 513, d.SOURCE_OUT: guard * 129}, profiler=profile)
    assert bh.read_l1(bh.core, d.OUTPUT, 32768) == pack('<8192I', *expected)
    assert bh.read_l1(bh.core, d.OUTPUT + 32768, 64) == guard
    assert bh.read_l1(bh.core, d.SOURCE_OUT, 8192) == pack('<2048I', *(w << 16 for w in a+b))
    assert bh.read_l1(bh.core, d.SOURCE_OUT + 8192, 64) == guard
    assert bh.read_l1(bh.core, d.SHORT-64, len(source)+128) == guard + source + guard
    if sample: samples.append(profile.last['unpack Dst complete'])
  print('SCATTER_UNPACK Dst', fmt, slots, lengths, 'cycles', samples, 'median', median(samples))


def test_scatter_unpack_images_fit_worker_text():
  from fw.consts import TensixL1
  segments = tuple((slot, 128) for slot in (7, 0, 5, 2, 6, 1, 4, 3))
  cases = [s.source_images(target, 7, u.F32, segments=segments, native=native)[0]
           for target in (u.UnpackTarget.SRCA, u.UnpackTarget.SRCB) for native in (False, True)]
  cases.append(d.dst_images(63, u.F32, segments=tuple((slot, 128) for slot in (63, 0, 31, 4, 57, 8)))[0])
  for code in cases:
    assert all(len(image) <= TensixL1.WORKER_TEXT_SIZE[role] for role, image in code.items())
