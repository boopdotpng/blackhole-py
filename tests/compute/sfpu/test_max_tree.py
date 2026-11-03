"""10000-element BF16 max: one core versus a partial-then-combine tree over cores.

Run: tt-device-queue run --device 0 --cwd "$PWD" -- \
  '../.venv/bin/python -m pytest -q -s tests/compute/sfpu/test_max_10k.py --bh-hardware --bh-device 0'

Input is 10 tilized BF16 tiles (padding = -inf). Each core reduces a contiguous
run of tiles, either already resident in L1 or read from DRAM first. With more
than one core, every core NoC-writes its partial to core 0, and core 0 reduces
the partials (the decode_argmax / vocab-argmax combine). The timer is core 0's
BRISC from kernel entry until the final result is in L1. Only the max key is
checked: the per-core local index is meaningless for the GMPOOL path.

Kernels per core:
  gmpool  FPU GMPOOL column maxima accumulated in one Dst row, 16-value BRISC finish
  sfpu    Llama SFPU argmax scan (ttko.argmax.scan_bf16), 32-candidate BRISC finish
  brisc   scalar BRISC scan (single core only, reference)
"""
import json
from statistics import median

import numpy as np
import pytest

from asm import Asm
from ttko.isa import R, Tensix as TT
from ttko.argmax import scan_bf16
from tests.profiler import Profiler
from tests.compute.fpu.test_rmsnorm_reduce import _unpack_pair_tile, _await_sources
from tests.compute.sfpu.test_argmax import INPUT, CANDIDATES, RESULT, READY, encode, scalar_scan
from tests.compute.sfpu.test_argmax_vocab import transfer
from tests.movement.unpacker import unpack as u
from tests.movement.packer.pack import emit_pack_dst_to_cb

PARTIALS = INPUT + 65536
FINAL = PARTIALS + 4096
ONES = FINAL + 4096
DATA = INPUT + 131072  # clear of CANDIDATES/PARTIALS for 20+ tiles
ONES_TILE = np.full(1024, 0x3f80, dtype='<u2').tobytes()
REPEATS = 9


def _finish_fp32(b, n):
    """BRISC max over n FP32 values at CANDIDATES -> BF16 ordered key."""
    best, ptr, i, bits, key, lim, tmp = b.reg(7)
    b.li(best, 0); b.li(ptr, CANDIDATES); b.li(i, 0); b.li(lim, n)
    loop, neg, keyed, skip = (b._new_label(s) for s in ('loop', 'neg', 'keyed', 'skip'))
    b.label(loop)
    b.lw(bits, ptr)
    b.srli(tmp, bits, 31)
    b.bne(tmp, R.ZERO, neg)
    b.li(tmp, 0x80000000); b.or_(key, bits, tmp); b.j(keyed)
    b.label(neg)
    b.xori(key, bits, -1)
    b.label(keyed)
    b.bgeu(best, key, skip)
    b.mv(best, key)
    b.label(skip)
    b.addi(ptr, ptr, 4); b.addi(i, i, 1)
    b.bltu(i, lim, loop)
    b.srli(best, best, 16)
    b.write(RESULT, best); b.write(RESULT + 4, 0); b.fence()


def _combine(b, slot, cores):
    """Every core posts (key, ready) to core 0; core 0 takes the max."""
    if len(cores) == 1:
        with b.scope():
            v = b.reg(); b.read(v, RESULT); b.write(FINAL, v); b.fence()
        return
    with b.scope():
        one = b.reg(); b.li(one, 1); b.write(RESULT + 8, one); b.fence()
    coordinate = cores[0][0] | cores[0][1] << 6
    transfer(b, RESULT, PARTIALS + slot * 16, coordinate, 16, True)
    if slot: return
    with b.scope():
        best, ptr, key, ready = b.reg(4)
        b.li(best, 0); b.li(ptr, PARTIALS)
        for _ in b.range(len(cores)):
            wait, skip = b._new_label('partial'), b._new_label('skip')
            b.label(wait); b.lw(ready, ptr, 8); b.beq(ready, R.ZERO, wait); b.fence()
            b.lw(key, ptr)
            b.bgeu(best, key, skip); b.mv(best, key)
            b.label(skip); b.addi(ptr, ptr, 16)
        b.write(FINAL, best); b.fence()


def core_images(kernel, first, tiles, slot, cores, dram=None, count=None):
    base = DATA + first * 2048
    b = Asm('brisc')
    profile = Profiler(b)
    profile.record('max')
    if dram is not None:
        transfer(b, base, dram.address + first * 2048, dram.coordinate, tiles * 2048)
    if kernel == 'brisc':
        raise ValueError('scalar scan reads INPUT; dropped for multi-size runs')
        _combine(b, slot, cores)
        profile.record('max')
        return {'brisc': b.lower()}, profile
    loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
    b.write(READY, 1); b.fence()
    loader.wait(READY, 1, bytes=4)
    u.configure_fp32_dst(math, 0)
    u._rmw_cfg_byte(math, u.CFG_BASE + 8, 0, 1, 1)
    for r in (12, 28, 47): u._set_thread_cfg(math, r, 0)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
    if kernel == 'sfpu':
        assert tiles <= 8, 'unrolled SFPU scan fits 8 FP32 Dst tiles / TRISC1 text'
        for tile in range(tiles):
            _unpack_pair_tile(loader, base + tile * 2048, base + tile * 2048)
            _await_sources(math)
            for row in range(0, 64, 8):
                math.emit(TT.TTMOVA2D(0, row, 0, 2, tile * 64 + row))
            math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 15))
            u.stall(math, u.Stall.SYNC, u.Wait.MATH)
        u.stall(math, u.Stall.SFPU, u.Wait.MATH)
        scan_bf16(math, tiles)
        math.emit(TT.TTSFPSTORE(0, 4, 0, 0))
        math.emit(TT.TTSFPSTORE(4, 4, 0, 2))
    else:  # gmpool: RISC-V loops keep TRISC text constant in tile count
        for i in loader.range(tiles):
            with loader.scope():
                addr = loader.reg()
                loader.slli(addr, i, 11)
                base_reg = loader.reg(); loader.li(base_reg, base)
                loader.add(addr, addr, base_reg)
                _unpack_pair_tile(loader, addr, ONES)

        def pool_tile(seed):
            _await_sources(math)
            if seed:  # seed Dst row 0 with real data so negatives are exact
                math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
                math.emit(TT.TTMOVA2D(0, 0, 0, 2, 0))
            for a_slot in (0, 2, 4, 6):
                math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
                for _ in range(a_slot): math.emit(TT.TTINCRWC(0, 0, 0, 8))
                math.emit(TT.TTGMPOOL(0, 1, 0, 0, 0))
            math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 15))
            u.stall(math, u.Stall.SYNC, u.Wait.MATH)
        pool_tile(True)
        if tiles > 1:
            for _ in math.range(tiles - 1): pool_tile(False)
    u.publish_dst(math)
    n = packer.reg(); packer.li(n, 64)
    emit_pack_dst_to_cb(packer, 0, CANDIDATES, n, output_format=u.F32)
    packer.write(READY + 4, 1); packer.fence()
    b.wait(READY + 4, 1, bytes=4)
    if kernel == 'sfpu': scalar_scan(b, 32, candidates=True)
    else: _finish_fp32(b, 16)
    _combine(b, slot, cores)
    profile.record('max')
    return {k.role: k.lower() for k in (b, loader, math, packer)}, profile


def build(bh, kernel, per_core, dram, tiles):
    cores = tuple(bh.device.cores[:(tiles + per_core - 1) // per_core])
    codes, profiles = {}, []
    for slot, core in enumerate(cores):
        first = slot * per_core
        codes[core], p = core_images(kernel, first, min(per_core, tiles - first), slot, cores, dram)
        profiles.append(p)
    return cores, codes, profiles[0]


@pytest.mark.parametrize('count', (10_000, 20_000))
def test_max(bh, count):
    tiles = (count + 1023) // 1024
    splits = sorted({(tiles + c - 1) // c for c in (1, 2, 5, 10, 20) if c <= tiles}, reverse=True)
    configs = [('gmpool', t) for t in splits] + [('sfpu', t) for t in splits if t <= 8]
    values = np.random.default_rng(71).normal(size=count).astype('f4')
    values[count - 2223] = 9.5
    payload, words = encode(values, True)
    keys = np.where(words >> 15, (~words) & 65535, words ^ 0x8000)
    expected = int(keys.max())
    dram = bh.dram_buffer(len(payload), initial=payload)
    variants = {}
    for source in ('l1', 'dram'):
        for kernel, per_core in configs:
            name = f'{source}:{kernel}:{(tiles + per_core - 1) // per_core}'
            variants[name] = build(bh, kernel, per_core, dram if source == 'dram' else None, tiles)
    samples = {name: [] for name in variants}
    for repeat in range(REPEATS):
        order = tuple(variants) if repeat % 2 else tuple(variants)[::-1]
        for name in order:
            cores, codes, profile = variants[name]
            l1 = {READY: bytes(16), PARTIALS: bytes(len(cores) * 16), FINAL: b'\xa5' * 16,
                  ONES: ONES_TILE, DATA: b'\x00' * len(payload) if name.startswith('dram') else payload}
            bh.launch_many_mapped(codes, l1=l1)
            got = int(np.frombuffer(bh.read_l1(cores[0], FINAL, 4), dtype='<u4')[0])
            assert got == expected, (name, hex(got), hex(expected))
            profile._report(bh.device, cores[0], bh.timeout)
            if repeat: samples[name].append(profile.last['max'])
    print('MAX_JSON ' + json.dumps(dict(count=count, median={n: median(s) for n, s in samples.items()})))
