"""Dependent FPU -> SFPU pipeline: one versus two outstanding Dst sections.

SyncHalf-style semaphore ownership, with explicit alternating half addresses.
Unlike independent-stream probes, SFPU checks every produced section's values.
"""
import hashlib
import json
import os
from pathlib import Path
from statistics import median
from struct import unpack

import numpy as np
import pytest
from asm import Asm
from ttko.isa import R, Tensix as TT
from tests.profiler import Profiler
from tests.timing import test_fpu_sfpu_interleave as probe
from tests.movement.unpacker import unpack as u
from tests.movement.packer.pack import _configure_row_addressing, _configure_row_mop, _set_dst_position
from tests.operation_pocs.sfpu_math.emit import constant
from tests.movement.test_noc import _record_clock


def images(batch, rounds, capacity):
    loader, math, packer = (Asm(r) for r in ('trisc0', 'trisc1', 'trisc2'))
    u.configure_unpack_pair(loader, probe.A, probe.B)
    loader.emit(TT.TTSETADCXX(3, 1023, 0))
    u.configure_mop(loader, u._mop_loop_words(1, 1, start=u._unpacr(0), loop=u._unpacr(1),
                    last=u._unpacr(1), outer_last=u._unpacr(1)))
    u.run_mop(loader)
    u.stall(loader, u.Stall.SYNC, u.Wait.UNPACK0 | u.Wait.UNPACK1)
    u.sem_get(loader, u.Sem.UNPACK_SYNC)
    u.pc_sync(loader)
    loader.write(probe.READY, 1)
    loader.fence()
    math.wait(probe.READY, 1, bytes=4)
    u.configure_fp32_dst(math, 0)
    for k in (math, loader):
        for register in (0, 1, 11, 12, 28, 47): u._set_thread_cfg(k, register, 0)
        k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
    math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
    u.stall(math, u.Stall.MATH, u.Wait.SRCA_VLD | u.Wait.SRCB_VLD)
    for tile in (0, 4, 2):
        for row in range(tile*64, tile*64+64, 8): math.emit(TT.TTMOVA2D(0, 0, 0, 2, row))
    u.stall(math, u.Stall.SFPU, u.Wait.MATH)
    math.emit(TT.TTSFPENCC(0, 0, 0, 2))
    for d in range(8): constant(math, d, 0.)
    math.emit(TT.TTSEMINIT(capacity, 0, 1 << 0))
    u.stall(math, u.Stall.SYNC, u.Wait.MATH | u.Wait.SFPU)
    u.pc_sync(math)
    loader.write(probe.READY+12, 1)
    loader.fence()
    loader.wait(probe.READY+4, 1, bytes=4)
    sc = loader.reg()
    loader.li(sc, rounds)
    _record_clock(loader, probe.STAMPS+16)
    loader.label('consume')
    for tile in (0, 4):
        u.sem_wait(loader, 0, u.SemWait.ON_ZERO, u.Stall.SFPU | u.Stall.SYNC)
        for i in range(batch):
            d = i % 4
            loader.emit(TT.TTSFPLOAD(d, 3, 0, tile*64+2*(i % 32)))
            loader.emit(TT.TTSFPMAD(d, d, d+4, d+4, 0))
        u.stall(loader, u.Stall.SYNC, u.Wait.SFPU)
        u.sem_get(loader, 0)  # Release only after all reads/accumulations complete.
    loader.addi(sc, sc, -1)
    loader.bne(sc, R.ZERO, 'consume')
    u.pc_sync(loader)
    _record_clock(loader, probe.STAMPS+24)
    loader.write(probe.READY+8, 1)
    loader.fence()
    math.wait(probe.READY+12, 1, bytes=4)
    mc = math.reg()
    math.li(mc, rounds)
    profile = Profiler(math)
    profile.record('pipeline')
    _record_clock(math, probe.STAMPS)
    math.write(probe.READY+4, 1)
    math.fence()
    math.label('produce')
    for tile in (0, 4):
        u.sem_wait(math, 0, u.SemWait.ON_MAX, u.Stall.MATH | u.Stall.SYNC)
        for i in range(batch): math.emit(TT.TTELWMUL(0, 0, 0, 0, tile*64+8*(i % 8)))
        u.stall(math, u.Stall.SYNC, u.Wait.MATH)
        u.sem_post(math, 0)  # Publish only completed FPU output.
    math.addi(mc, mc, -1)
    math.bne(mc, R.ZERO, 'produce')
    u.pc_sync(math)
    _record_clock(math, probe.STAMPS+8)
    math.wait(probe.READY+8, 1, bytes=4)
    profile.record('pipeline')
    for d in range(4): math.emit(TT.TTSFPSTORE(d+4, 3, 0, 128+2*d))
    u.stall(math, u.Stall.SYNC, u.Wait.SFPU)
    u.pc_sync(math)
    math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 15))
    u.publish_dst(math)
    u.sem_wait(packer, u.Sem.MATH_PACK, u.SemWait.ON_ZERO, u.Stall.TDMA)
    u.configure_packer(packer, u.F32)
    _configure_row_addressing(packer)
    _configure_row_mop(packer, 64, close=True)
    for index, tile in enumerate((0, 4, 2)):
        u.pc_sync(packer)
        _set_dst_position(packer, tile, 0)
        packer.write(u.PackCfg.L1_DESTINATION, ((probe.OUTPUT+index*4096) >> 4)-1 | 0x80000000)
        packer.write(u.PackCfg.DESTINATION_OFFSET, 0)
        packer.emit(TT.TTSETADCXX(4, 15, 0))
        u.run_mop(packer)
        u.stall(packer, u.Stall.SYNC, u.Wait.PACK0)
        u.pc_sync(packer)
    u.sem_get(packer, u.Sem.MATH_PACK)
    return {k.role: k.lower() for k in (loader, math, packer)}, profile


@pytest.mark.parametrize('capacity', (1, 2))
@pytest.mark.parametrize('batch', (8, 16, 32, 64, 128))
def test_dst_half_pipeline(bh, request, capacity, batch):
    points = []
    for rounds in (4, 16, 64):
        binary, profile = images(batch, rounds, capacity)
        expected = np.float32(0)
        for r in range(1, rounds+1):
            value = 1/64 + r*batch/8/4096
            for _ in range(2*batch//4): expected = np.float32(float(expected)+value*value)
        samples = []
        for sample in range(6):
            bh.launch(binary, l1=probe.initial(), profiler=profile)
            values = unpack('<3072f', bh.read_l1(bh.core, probe.OUTPUT, 3*4096))
            assert values[:2048] == (value,)*2048
            assert values[2048:2176] == (float(expected),)*128, (values[2048], expected)
            assert bh.read_l1(bh.core, probe.OUTPUT+3*4096, 64) == b'\xa5'*64
            if sample:
                ms, me, ss, se = unpack('<4Q', bh.read_l1(bh.core, probe.STAMPS, 32))
                samples.append(dict(total=profile.last['pipeline'], math=me-ms, sfpu=se-ss,
                                    global_cycles=max(me,se)-min(ms,ss)))
        points.append(dict(rounds=rounds, work_items=2*batch*rounds, samples=samples,
                           median=median(s['total'] for s in samples),
                           image_sha256={k:hashlib.sha256(v).hexdigest() for k,v in binary.items()}))
    row = dict(capacity=capacity, batch=batch, points=points, core=list(bh.core),
               card=request.config.getoption('--bh-device'),
               source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               cycles_per_work_item=[(b['median']-a['median'])/(b['work_items']-a['work_items'])
                                     for a,b in zip(points,points[1:])])
    print(json.dumps(row))
    if output := os.environ.get('DST_HALF_OUTPUT'):
        with Path(output).open('a') as f: f.write(json.dumps(row)+'\n')
