"""Fixed-work FPU/SFPU burst sweep with checked results and completed timing.

Run through tt-device-queue; INTERLEAVE_OUTPUT optionally appends JSONL evidence.
Batch is FPU instructions then SFPU work items (load_mad has two instructions).
All source loads, configuration, initialization and output packing are untimed.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from struct import pack, unpack

import pytest
from asm import Asm
from ttko.isa import R, Tensix as TT
from tests.profiler import Profiler
from tests.movement.unpacker import unpack as u
from tests.movement.packer.pack import _configure_row_addressing, _configure_row_mop, _set_dst_position
from tests.operation_pocs.sfpu_math.emit import constant
from tests.movement.test_noc import _record_clock

A, B, READY, OUTPUT = 0x40000, 0x40800, 0x41000, 0x42000
STAMPS = 0x41100
BODY = 64
BATCHES = (1, 2, 4, 8, 16, 32, 64)
COUNTS = (16, 32, 64)
SF_CASES = ('nop', 'loadi', 'add', 'mad', 'load', 'store', 'load_mad')


def body_words(fpu, sfpu, batch, size=BODY, *, gap_fpu=0, gap_sfpu=0, scratch_tile=1, fpu_tile=0):
    """Same per-engine order and operands in every schedule; only merge order varies."""
    words = []
    for start in range(0, size, batch):
        for i in range(start, min(start + batch, size)):
            dst = fpu_tile*64 + (i % 8) * 8  # Eight independent 8x16 blocks.
            if fpu == 'mvmul': word = TT.TTMVMUL(0, 0, 0, dst)
            elif fpu == 'elwmul': word = TT.TTELWMUL(0, 0, 0, 0, dst)
            elif fpu == 'setrwc': word = TT.TTSETRWC(0, 0, 0, 0, 0, 15)
            elif fpu == 'incrwc': word = TT.TTINCRWC(0, 0, 0, 0)
            elif fpu == 'clrexphist': word = TT.TTCLREXPHIST()
            else: raise ValueError(fpu)
            words.append(word)
        words.extend(TT.TTNOP() for _ in range(gap_fpu))
        for i in range(start, min(start + batch, size)):
            d = i % 4
            address = scratch_tile*64 + 2 * (i % 32)
            if sfpu == 'nop': words.append(TT.TTSFPNOP())
            elif sfpu == 'loadi': words.append(TT.TTSFPLOADI(d, 0, 0x3f80))
            elif sfpu == 'add': words.append(TT.TTSFPADDI(0x3f80, d, 0))
            elif sfpu == 'mad': words.append(TT.TTSFPMAD(10, 10, d, d, 0))
            elif sfpu == 'load': words.append(TT.TTSFPLOAD(d, 3, 0, address))
            elif sfpu == 'load_zero': words.append(TT.TTSFPLOAD(d, 11, 0, address))
            elif sfpu == 'store': words.append(TT.TTSFPSTORE(d, 3, 0, address))
            elif sfpu == 'load_mad':
                words.extend((TT.TTSFPLOAD(d, 3, 0, address), TT.TTSFPMAD(d, d, d + 4, d + 4, 0)))
            else: raise ValueError(sfpu)
        words.extend(TT.TTNOP() for _ in range(gap_sfpu))
    return words


def images(fpu, sfpu, batch, repeats, *, feed='inline', gap_fpu=0, gap_sfpu=0, scratch_tile=1, fpu_tile=0):
    loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
    u.configure_unpack_pair(loader, A, B)
    loader.emit(TT.TTSETADCXX(3, 1023, 0))
    u.configure_mop(loader, u._mop_loop_words(1, 1, start=u._unpacr(0),
                    loop=u._unpacr(1), last=u._unpacr(1), outer_last=u._unpacr(1)))
    u.run_mop(loader)
    u.stall(loader, u.Stall.SYNC, u.Wait.UNPACK0 | u.Wait.UNPACK1)
    u.sem_get(loader, u.Sem.UNPACK_SYNC)
    u.pc_sync(loader)
    loader.write(READY, 1)
    loader.fence()
    math.wait(READY, 1, bytes=4)
    u.configure_fp32_dst(math, 0)
    for register in (11, 12, 28, 47): u._set_thread_cfg(math, register, 0)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
    math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
    u.stall(math, u.Stall.MATH, u.Wait.SRCA_VLD | u.Wait.SRCB_VLD)
    # Fully define rows before SFPU partial-column stores. ZEROACC alone does
    # not provide defined storage for SFPU accesses according to the ISA.
    for tile in (fpu_tile, scratch_tile, 2):
        for row in range(tile*64, tile*64+64, 8): math.emit(TT.TTMOVA2D(0, 0, 0, 2, row))
    u.stall(math, u.Stall.SFPU, u.Wait.MATH)
    math.emit(TT.TTSFPENCC(0, 0, 0, 2))
    for reg in range(8): constant(math, reg, 0.)
    constant(math, 0, 2.)
    for address in range(scratch_tile*64, scratch_tile*64+64, 2): math.emit(TT.TTSFPSTORE(0, 3, 0, address))
    constant(math, 0, 0.)
    u.stall(math, u.Stall.MATH, u.Wait.SRCA_VLD | u.Wait.SRCB_VLD)
    u.stall(math, u.Stall.SYNC, u.Wait.MATH | u.Wait.SFPU)
    u.pc_sync(math)
    words = body_words(fpu, sfpu, batch, gap_fpu=gap_fpu, gap_sfpu=gap_sfpu, scratch_tile=scratch_tile, fpu_tile=fpu_tile)
    if feed == 'fpu_only': words = [w for w in words if int(w) >> 24 < 0x70]
    if feed == 'sfpu_only': words = [w for w in words if int(w) >> 24 >= 0x70]
    split = feed.startswith(('split', 'handoff'))
    handoff = feed.startswith('handoff')
    if split:
        worker = loader if feed.endswith('0') else packer
        for register in (0, 1, 12, 28, 47): u._set_thread_cfg(worker, register, 0)
        worker.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
        u.pc_sync(worker)
        worker.write(READY + 12, 1)
        worker.fence()
        worker.wait(READY + 4, 1, bytes=4)
        scounter = worker.reg()
        worker.li(scounter, repeats)
        _record_clock(worker, STAMPS + 16)
        worker.label('sf_loop')
        for start in range(0, BODY, batch):
            if handoff:
                u.sem_wait(worker, 0, u.SemWait.ON_ZERO, u.Stall.SFPU | u.Stall.SYNC)
                u.sem_get(worker, 0)
            # Work order is the same as the merged stream.
            sf_words = [w for w in words if int(w) >> 24 >= 0x70]
            stride = 2 if sfpu == 'load_mad' else 1
            for word in sf_words[start*stride:(start+batch)*stride]: worker.emit(word)
            if handoff:
                u.stall(worker, u.Stall.SYNC, u.Wait.SFPU)
                u.sem_post(worker, 3)
        worker.addi(scounter, scounter, -1)
        worker.bne(scounter, R.ZERO, 'sf_loop')
        u.stall(worker, u.Stall.SYNC, u.Wait.SFPU)
        u.pc_sync(worker)
        _record_clock(worker, STAMPS + 24)
        worker.write(READY + 8, 1)
        worker.fence()
        math.emit(TT.TTSEMINIT(1, 0, (1 << 0) | (1 << 3)))
        u.pc_sync(math)
        math.wait(READY + 12, 1, bytes=4)
    if feed == 'replay':
        # Keep eight independent FPU destinations even at batch=1. All loaded
        # SFPU addresses contain the same checked constant. Replay capacity=32.
        span = max(8, batch)
        replay_words = body_words(fpu, sfpu, batch, span, scratch_tile=scratch_tile, fpu_tile=fpu_tile)
        u.load_replay(math, 0, replay_words)
    elif feed not in ('inline', 'fpu_only', 'sfpu_only') and not split: raise ValueError(feed)
    counter = math.reg()
    math.li(counter, repeats)
    profile = Profiler(math)
    profile.record('mixed')
    if split:
        _record_clock(math, STAMPS)
        math.write(READY + 4, 1)
        math.fence()
    math.label('mixed_loop')
    if split:
        fpu_words = [w for w in words if int(w) >> 24 < 0x70]
        for start in range(0, BODY, batch):
            for word in fpu_words[start:start+batch]: math.emit(word)
            if handoff:
                u.stall(math, u.Stall.SYNC, u.Wait.MATH)
                u.sem_post(math, 0)
                u.sem_wait(math, 3, u.SemWait.ON_ZERO, u.Stall.MATH | u.Stall.SYNC)
                u.sem_get(math, 3)
    elif feed == 'replay':
        for _ in range(BODY // span): math.emit(TT.TTREPLAY(0, len(replay_words), 0, 0))
    else:
        for word in words: math.emit(word)
    math.addi(counter, counter, -1)
    math.bne(counter, R.ZERO, 'mixed_loop')
    u.stall(math, u.Stall.SYNC, u.Wait.MATH | u.Wait.SFPU)
    u.pc_sync(math)
    if split:
        _record_clock(math, STAMPS + 8)
        math.wait(READY + 8, 1, bytes=4)
    profile.record('mixed')
    # Observe the final four SFPU chains in the first 128 values of tile 2.
    for d in range(4): math.emit(TT.TTSFPSTORE(d + (4 if sfpu == 'load_mad' else 0), 3, 0, 128 + 2*d))
    u.stall(math, u.Stall.SYNC, u.Wait.SFPU)
    u.pc_sync(math)
    math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 15))
    u.publish_dst(math)
    u.sem_wait(packer, u.Sem.MATH_PACK, u.SemWait.ON_ZERO, u.Stall.TDMA)
    u.configure_packer(packer, u.F32)
    _configure_row_addressing(packer)
    _configure_row_mop(packer, 64, close=True)
    for index, tile in enumerate((fpu_tile, scratch_tile, 2)):
        u.pc_sync(packer)
        _set_dst_position(packer, tile, 0)
        packer.write(u.PackCfg.L1_DESTINATION, ((OUTPUT + index*4096) >> 4) - 1 | 0x80000000)
        packer.write(u.PackCfg.DESTINATION_OFFSET, 0)
        packer.emit(TT.TTSETADCXX(4, 15, 0))
        u.run_mop(packer)
        u.stall(packer, u.Stall.SYNC, u.Wait.PACK0)
        u.pc_sync(packer)
    u.sem_get(packer, u.Sem.MATH_PACK)
    body_count = len(words) + (8 * (BODY // batch) if handoff else 0)
    return {k.role: k.lower() for k in (loader, math, packer)}, profile, body_count


def initial():
    return {A: pack('<1024H', *([0x3c80]*1024)), B: pack('<1024H', *([0x3c80]*1024)),
            READY: bytes(16), STAMPS: bytes(32), OUTPUT: b'\xa5' * (3*4096 + 64)}


def validate(bh, fpu, sfpu, repeats, feed='inline'):
    values = unpack('<3072f', bh.read_l1(bh.core, OUTPUT, 3*4096))
    # A=B=1/64. Exactly representable accumulations, no FP16 saturation plateau.
    fpu_value = 1/64 + (BODY * repeats / 8 / (256 if fpu == 'mvmul' else 4096)
                        if fpu in ('mvmul', 'elwmul') and feed != 'sfpu_only' else 0)
    assert values[:1024] == (fpu_value,) * 1024, (fpu, sfpu, repeats, values[:16], fpu_value)
    scratch = 0. if sfpu == 'store' and feed != 'fpu_only' else 2.
    assert values[1024:2048] == (scratch,) * 1024, (sfpu, 'scratch')
    sf_value = {'nop': 0., 'loadi': 1., 'add': BODY*repeats/4,
                'mad': BODY*repeats/4, 'load': 2., 'load_zero': 0., 'store': 0., 'load_mad': BODY*repeats}[sfpu]
    if feed == 'fpu_only': sf_value = 0.
    assert values[2048:2176] == (sf_value,) * 128, (sfpu, values[2048:2064], sf_value)
    assert bh.read_l1(bh.core, OUTPUT + 3*4096, 64) == b'\xa5' * 64


@pytest.mark.parametrize('batch', BATCHES)
@pytest.mark.parametrize('sfpu', SF_CASES)
@pytest.mark.parametrize('fpu', ('mvmul', 'elwmul'))
def test_fpu_sfpu_interleave(bh, request, fpu, sfpu, batch):
    measure(bh, request, fpu, sfpu, batch)


def measure(bh, request, fpu, sfpu, batch, feed='inline', gap_fpu=0, gap_sfpu=0, scratch_tile=1,
            counts=COUNTS, fpu_tile=0):
    points = []
    for repeats in counts:
        binary, profile, body_instructions = images(fpu, sfpu, batch, repeats, feed=feed,
                                                   gap_fpu=gap_fpu, gap_sfpu=gap_sfpu, scratch_tile=scratch_tile, fpu_tile=fpu_tile)
        samples = []
        thread_samples = []
        for sample in range(6):
            bh.launch(binary, l1=initial(), profiler=profile)
            validate(bh, fpu, sfpu, repeats, feed=feed)
            if sample:
                samples.append(profile.last['mixed'])
                if feed.startswith(('split', 'handoff')):
                    ms, me, ss, se = unpack('<4Q', bh.read_l1(bh.core, STAMPS, 32))
                    thread_samples.append(dict(math_cycles=me-ms, sfpu_cycles=se-ss,
                                               global_cycles=max(me,se)-min(ms,ss), sfpu_start_skew=ss-ms))
        points.append(dict(repeats=repeats, work_items=BODY*repeats,
                           fpu_instructions=0 if feed == 'sfpu_only' else BODY*repeats,
                           sfpu_work_items=0 if feed == 'fpu_only' else BODY*repeats,
                           body_instructions=body_instructions*repeats,
                           raw_cycles=samples, median=median(samples), min=min(samples), max=max(samples),
                           image_sha256={role: hashlib.sha256(image).hexdigest() for role,image in binary.items()}))
        if thread_samples: points[-1]['thread_samples'] = thread_samples
    row = dict(fpu=fpu, sfpu=sfpu, batch=batch, feed=feed, gap_fpu=gap_fpu, gap_sfpu=gap_sfpu,
               scratch_tile=scratch_tile, fpu_tile=fpu_tile,
               repeat_counts=list(counts), recorded_at=datetime.now(timezone.utc).isoformat(),
               card=request.config.getoption('--bh-device'),
               core=list(bh.core), core_index=bh.core_index, role='trisc1', points=points,
               cycles_per_work_item=[(b['median']-a['median'])/(b['work_items']-a['work_items'])
                   for a,b in zip(points,points[1:])],
               source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    print('FPU_SFPU_INTERLEAVE ' + json.dumps(row, sort_keys=True))
    if output := os.environ.get('INTERLEAVE_OUTPUT'):
        with Path(output).open('a') as f: f.write(json.dumps(row, sort_keys=True)+'\n')


@pytest.mark.parametrize('batch', (1, 2, 4, 8))
@pytest.mark.parametrize('sfpu', ('load', 'load_mad', 'mad'))
def test_interleave_replay(bh, request, sfpu, batch):
    measure(bh, request, 'elwmul', sfpu, batch, feed='replay')


@pytest.mark.parametrize('batch', (1, 2, 4, 8, 32))
@pytest.mark.parametrize('fpu', ('setrwc', 'incrwc', 'clrexphist'))
def test_interleave_address_controls(bh, request, fpu, batch):
    measure(bh, request, fpu, 'load', batch)


@pytest.mark.parametrize('feed', ('split0', 'split2', 'handoff0', 'handoff2'))
@pytest.mark.parametrize('batch', (1, 4, 16, 32, 64))
@pytest.mark.parametrize('sfpu', ('load', 'load_mad', 'mad'))
def test_interleave_threads(bh, request, sfpu, batch, feed):
    measure(bh, request, 'elwmul', sfpu, batch, feed=feed)


@pytest.mark.parametrize('gap', (1, 2, 4, 5, 6, 7, 8))
@pytest.mark.parametrize('direction', ('fpu', 'sfpu', 'both'))
def test_interleave_spacing(bh, request, direction, gap):
    measure(bh, request, 'elwmul', 'load', 8,
            gap_fpu=gap if direction in ('fpu', 'both') else 0,
            gap_sfpu=gap if direction in ('sfpu', 'both') else 0)


@pytest.mark.parametrize('batch', (1, 2, 4, 8, 32, 64))
def test_interleave_zero_load(bh, request, batch):
    measure(bh, request, 'elwmul', 'load_zero', batch)


@pytest.mark.parametrize('fpu', ('clrexphist', 'incrwc'))
@pytest.mark.parametrize('sfpu', ('load', 'load_mad'))
def test_interleave_thread_controls(bh, request, fpu, sfpu):
    measure(bh, request, fpu, sfpu, 32, feed='split0')


@pytest.mark.parametrize('sfpu', ('load', 'load_mad', 'mad', 'load_zero'))
@pytest.mark.parametrize('feed', ('fpu_only', 'sfpu_only', 'split0', 'split2'))
def test_interleave_isolated(bh, request, sfpu, feed):
    measure(bh, request, 'elwmul', sfpu, 32, feed=feed)


@pytest.mark.parametrize('fpu_tile,scratch_tile', ((0, 3), (0, 4), (0, 7), (4, 1), (4, 5), (4, 7)))
@pytest.mark.parametrize('feed', ('inline', 'split0', 'split2'))
@pytest.mark.parametrize('sfpu', ('load', 'load_mad'))
@pytest.mark.parametrize('batch', (1, 32))
def test_interleave_dst_placement(bh, request, sfpu, batch, feed, scratch_tile, fpu_tile):
    measure(bh, request, 'elwmul', sfpu, batch, feed=feed, scratch_tile=scratch_tile, fpu_tile=fpu_tile)


@pytest.mark.parametrize('feed', ('inline', 'split0', 'split2', 'handoff0', 'handoff2'))
@pytest.mark.parametrize('scratch_tile', (1, 4))
def test_interleave_short_handoffs(bh, request, feed, scratch_tile):
    measure(bh, request, 'elwmul', 'load_mad', 32, feed=feed, counts=(1, 2, 4), scratch_tile=scratch_tile)


def test_interleave_schedules_preserve_work():
    # Decode raw opcode bytes; each schedule must preserve both per-engine streams.
    for fpu in ('mvmul', 'elwmul'):
        for sfpu in SF_CASES:
            def split(words):
                return ([int(w) for w in words if int(w) >> 24 < 0x70],
                        [int(w) for w in words if int(w) >> 24 >= 0x70])
            baseline = split(body_words(fpu, sfpu, 1))
            for batch in BATCHES: assert split(body_words(fpu, sfpu, batch)) == baseline
