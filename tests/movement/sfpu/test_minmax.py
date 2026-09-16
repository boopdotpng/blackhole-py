"""SFPSWAP value/index selection, ties, masks and automatic Dst index capture."""
import struct

import pytest

from ttko.isa import Tensix as TT
from tests.operation_pocs.sfpu_movement import emitters as sf
from tests.operation_pocs.sfpu_movement.test_operations import fixture, finish, lane_index


MIN_MASKS = (0, 0xffffffff, 0x0000ffff, 0x00ff00ff, 0xff0000ff,
             0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000, 0)


def bits(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


def order(x):
    word = bits(x)
    return (~word & 0xffffffff) if word >> 31 else word ^ 0x80000000


@pytest.mark.parametrize('mode', range(10))
@pytest.mark.parametrize('indices,invert,mask', (
    (False, False, 0xffffffff), (True, False, 0xffffffff),
    (True, True, 0x55555555),
))
def test_swap_modes(bh, request, mode, indices, invert, mask):
    u, m, p, profile, initial = fixture()
    # Equal positive/negative values and both zero signs distinguish tie rules.
    left = [(-3., -3., 3., 3., -0., 0., -9., 9.)[i % 8] for i in range(32)]
    right = [(-3., -2., 3., 2., 0., -0., 9., -9.)[i % 8] for i in range(32)]
    for lane in range(32):
        initial[lane_index(0, lane)] = left[lane]
        initial[lane_index(1, lane)] = right[lane]
    expected = initial.copy()
    sf.load(m, 0, 0, position=0)
    sf.load(m, 1, 0, position=1)
    m.emit(TT.TTSFPLOADI(4, 2, 11))
    m.emit(TT.TTSFPLOADI(5, 2, 22))
    sf.predicate(m, mask, scratch=(2, 3))
    m.emit(TT.TTSFPCONFIG((4 if indices else 0) | (256 if invert else 0), 15, 1))
    profile.record('swap')
    m.emit(TT.TTSFPSWAP(0, 0, 1, mode))
    m.emit(TT.TTSFPNOP())
    sf.drain(m)
    profile.record('swap')
    # TEN-2932: clear index mode before arithmetic writes to L4/L5.
    sf.predicate(m, None, scratch=(2, 3))
    m.emit(TT.TTSFPCONFIG(0, 15, 1))
    m.emit(TT.TTSFPCAST(4, 4, 0))
    m.emit(TT.TTSFPCAST(5, 5, 0))
    for reg, pos in ((0, 0), (1, 1), (4, 2), (5, 3)):
        sf.store(m, reg, 2, position=pos)
    for lane, (a, b) in enumerate(zip(left, right)):
        swap = True if mode == 0 else order(a) < order(b) or (bits(a) == bits(b) and bits(a) >> 31)
        if mode:
            swap ^= not bool(MIN_MASKS[mode] >> lane & 1)
            swap ^= invert
        swap = bool(swap and mask >> lane & 1)
        vals = (b if swap else a, a if swap else b,
                float(22 if indices and swap else 11), float(11 if indices and swap else 22))
        for pos, value in enumerate(vals):
            expected[128 + lane_index(pos, lane)] = value
    finish(bh, request, (u, m, p), profile, initial, expected,
           f'swap:{mode}:indices={indices}:invert={invert}:mask={mask:x}', {'swap': 1})


@pytest.mark.parametrize('row', (0, 2, 30, 128, 510))
def test_capture_dst_indices(bh, request, row):
    u, m, p, profile, initial = fixture()
    expected = initial.copy()
    m.emit(TT.TTSFPCONFIG(12, 15, 1))
    profile.record('capture')
    m.emit(TT.TTSFPLOAD(0, 3, 0, row))
    sf.drain(m)
    profile.record('capture')
    m.emit(TT.TTSFPCONFIG(0, 15, 1))
    m.emit(TT.TTSFPCAST(4, 4, 0))
    sf.store(m, 4, 2)
    for lane in range(32):
        # FP32 consumes paired physical rows; captured index uses physical row.
        r = (row & ~3) + lane // 8
        c = (lane % 8) * 2 + ((row >> 1) & 1)
        expected[128 + lane_index(0, lane)] = float(r * 16 + c)
    finish(bh, request, (u, m, p), profile, initial, expected,
           f'capture:{row}', {'capture': 1})
