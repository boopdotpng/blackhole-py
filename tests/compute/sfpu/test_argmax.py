"""BF16 SFPU argmax versus the decode BRISC scan, including transport costs."""
import json
from statistics import median

import numpy as np
import pytest

from asm import Asm
from firmware.consts import TensixL1
from ttko.isa import R, Tensix as TT
from ttko import DType, l1
from ttko.argmax import scan_bf16, physical_to_logical
from tests.profiler import Profiler
from tests.compute.fpu.test_rmsnorm_reduce import _unpack_pair_tile, _await_sources
from tests.movement.unpacker import unpack as u
from tests.movement.packer.pack import emit_pack_dst_to_cb

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
CANDIDATES = INPUT + 32768
RESULT = CANDIDATES + 512
READY = RESULT + 16


def encode(values, tilized):
    words = np.asarray(values, dtype='<f4').view('<u4') >> 16
    words = words.astype('<u2')
    padded = np.full((len(words) + 1023) // 1024 * 1024, 0xff80, dtype='<u2')
    padded[:len(words)] = words
    if tilized:
        padded = padded.reshape(-1, 2, 16, 2, 16).transpose(0, 1, 3, 2, 4).copy().ravel()
    return padded.tobytes(), words


def scalar_scan(k, count, *, tilized=True, candidates=False):
    best, best_id, ptr, i, key, index, raw, sign = k.reg(8)
    k.li(best, 0); k.li(best_id, 0x7fffffff); k.li(i, 0)
    k.li(ptr, CANDIDATES if candidates else INPUT)
    loop, skip, replace = (k._new_label(s) for s in ('scan', 'skip', 'replace'))
    k.label(loop)
    if candidates:
        k.lw(key, ptr)
        k.srli(key, key, 15)
        k.lw(raw, ptr, 4)
        physical_to_logical(k, raw, index, tilized=tilized)
        k.addi(ptr, ptr, 8)
    else:
        if tilized:
            l1.load(k, INPUT, i, raw, DType.BF16)
        else:
            k.lhu(raw, ptr)
            k.addi(ptr, ptr, 2)
        positive, keyed = k._new_label('positive'), k._new_label('keyed')
        k.srli(sign, raw, 15)
        k.beq(sign, R.ZERO, positive)
        k.xori(key, raw, -1); k.slli(key, key, 16); k.srli(key, key, 16)
        k.j(keyed)
        k.label(positive)
        k.li(sign, 0x8000); k.xor(key, raw, sign)
        k.label(keyed)
        k.mv(index, i)
    # Same key ordering as decode_argmax, with explicit minimum-index ties.
    k.bltu(best, key, replace)
    k.bne(best, key, skip)
    k.bgeu(index, best_id, skip)
    k.label(replace)
    k.mv(best, key); k.mv(best_id, index)
    k.label(skip)
    k.addi(i, i, 1)
    k.li(sign, 32 if candidates else count)
    k.bltu(i, sign, loop)
    k.write(RESULT, best); k.write(RESULT + 4, best_id); k.fence()


def images(count, *, sfpu, tilized=True, before=None, after=None):
    tiles = (count + 1023) // 1024
    b = Asm('brisc')
    profile = Profiler(b)
    profile.record('argmax')
    if before: before(b)
    if not sfpu:
        scalar_scan(b, count, tilized=tilized)
        if after: after(b)
        profile.record('argmax')
        return {'brisc': b.lower()}, profile
    loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
    b.write(READY, 1); b.fence()
    loader.wait(READY, 1, bytes=4)
    u.configure_fp32_dst(math, 0)
    u._rmw_cfg_byte(math, u.CFG_BASE + 8, 0, 1, 1)
    for r in (12, 28, 47): u._set_thread_cfg(math, r, 0)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
    for tile in range(tiles):
        _unpack_pair_tile(loader, INPUT + tile * 2048, INPUT + tile * 2048)
        _await_sources(math)
        for row in range(0, 64, 8):
            math.emit(TT.TTMOVA2D(0, row, 0, 2, tile * 64 + row))
        math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 15))
        u.stall(math, u.Stall.SYNC, u.Wait.MATH)
    u.stall(math, u.Stall.SFPU, u.Wait.MATH)
    scan_bf16(math, tiles, tilized=tilized)
    # 32 interleaved key/index pairs at physical Dst rows 0..3.
    math.emit(TT.TTSFPSTORE(0, 4, 0, 0))
    math.emit(TT.TTSFPSTORE(4, 4, 0, 2))
    u.publish_dst(math)
    n = packer.reg(); packer.li(n, 64)
    emit_pack_dst_to_cb(packer, 0, CANDIDATES, n, output_format=u.F32)
    packer.write(READY + 4, 1); packer.fence()
    b.wait(READY + 4, 1, bytes=4)
    scalar_scan(b, count, candidates=True, tilized=tilized)
    if after: after(b)
    profile.record('argmax')
    return {k.role: k.lower() for k in (b, loader, math, packer)}, profile


@pytest.mark.parametrize('tilized', (False, True))
@pytest.mark.parametrize('case', ('random', 'negative_ties', 'positive_ties', 'zeros', 'last', 'infinities', 'all_negative_infinity', 'subnormals'))
def test_argmax(bh, case, tilized):
    count = 2049
    values = np.random.default_rng(61).normal(size=count).astype('f4')
    if case.endswith('ties'):
        values[:] = -9
        values[[17, 64, 257, 1024, 2048]] = -1 if case == 'negative_ties' else 7
    elif case == 'zeros':
        values[:] = -0.; values[[17, 64]] = 0.
    elif case == 'last': values[-1] = 100
    elif case == 'infinities': values[:] = -np.inf; values[63] = np.inf
    elif case == 'all_negative_infinity': values[:] = -np.inf
    elif case == 'subnormals':
        values[:] = np.float32(-2**-130); values[257] = np.float32(2**-130)
    payload, words = encode(values, tilized)
    keys = np.where(words >> 15, (~words) & 65535, words ^ 0x8000)
    expected = (int(keys.max()), int(keys.argmax()))
    for sfpu in (False, True):
        code, profile = images(count, sfpu=sfpu, tilized=tilized)
        bh.launch(code, l1={INPUT: payload, READY: bytes(16),
                           CANDIDATES: b'\xa5' * 320, RESULT: b'\xa5' * 16}, profiler=profile)
        actual = tuple(np.frombuffer(bh.read_l1(bh.core, RESULT, 8), dtype='<u4'))
        assert actual == expected, (sfpu, actual, expected)
        assert bh.read_l1(bh.core, CANDIDATES + 256, 64) == b'\xa5' * 64
        assert bh.read_l1(bh.core, RESULT + 8, 8) == b'\xa5' * 8


@pytest.mark.parametrize('count', (1024, 2048, 3072, 4096))
def test_argmax_local_timing(bh, count):
    payload, words = encode(np.random.default_rng(63).normal(size=count), True)
    keys = np.where(words >> 15, (~words) & 65535, words ^ 0x8000)
    expected = (int(keys.max()), int(keys.argmax()))
    variants = {name: images(count, sfpu=name == 'sfpu') for name in ('brisc', 'sfpu')}
    samples = {name: [] for name in variants}
    for repeat in range(9):
        for name in (tuple(variants) if repeat % 2 else tuple(variants)[::-1]):
            code, profile = variants[name]
            bh.launch(code, l1={INPUT: payload, READY: bytes(16)}, profiler=profile)
            assert tuple(np.frombuffer(bh.read_l1(bh.core, RESULT, 8), dtype='<u4')) == expected
            if repeat: samples[name].append(profile.last['argmax'])
    print('ARGMAX_LOCAL ' + json.dumps(dict(count=count, samples=samples,
          median_cycles={name: median(times) for name, times in samples.items()})))


def test_argmax_full_dst(bh):
    values = np.full(8192, -3., dtype='f4')
    values[-1] = 7.
    payload, _ = encode(values, True)
    code, profile = images(len(values), sfpu=True)
    bh.launch(code, l1={INPUT: payload, READY: bytes(16)}, profiler=profile)
    assert tuple(np.frombuffer(bh.read_l1(bh.core, RESULT, 8), dtype='<u4')) == (0xc0e0, 8191)
