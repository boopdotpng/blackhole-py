"""Completed scalar/control timing slopes; reserve the card with tt-device-queue.

TIMING_OUTPUT uses the same JSONL format as test_instruction_timing.py.
Scalar ALU sinks are checked, including same-bank versus cross-bank operands.
"""
import hashlib
from pathlib import Path
from statistics import median
from struct import unpack

import pytest
from asm import Asm
from firmware.consts import TensixMMIO
from ttko.isa import R, Tensix as TT
from tests.isa.test_scalar import set_gpr, result
from tests.movement.unpacker.unpack import pc_sync, stall, Stall, Wait
from tests.profiler import Profiler
from tests.timing.test_instruction_timing import BODY, COUNTS, SINK, save

OPS = ('ADDDMAREG', 'SUBDMAREG', 'MULDMAREG', 'BITWOPDMAREG', 'SHIFTDMAREG', 'CMPDMAREG')
CASES = [(op, mode) for op in OPS for mode in ('immediate', 'same_bank', 'cross_bank')]
CASES += [(op, 'default') for op in ('NOP', 'DMANOP', 'SETDMAREG')]


def build(op, mode, iterations, role='trisc1'):
    k = Asm(role)
    right = 4 if mode == 'cross_bank' else 1
    set_gpr(k, 0, 3)
    set_gpr(k, right, 1)
    stall(k, Stall.SYNC, Wait.THCON)
    pc_sync(k)
    counter, sink = k.reg(2)
    k.li(counter, iterations)
    p = Profiler(k)
    p.record('body')
    k.label('loop')
    for _ in range(BODY):
        if op in OPS:
            args = [int(mode == 'immediate')]
            if op in ('BITWOPDMAREG', 'SHIFTDMAREG', 'CMPDMAREG'): args.append(0)
            args.extend((0, 1 if mode == 'immediate' else right, 0))
            k.emit(getattr(TT, 'TT' + op)(*args))
        elif op == 'SETDMAREG': k.emit(TT.TTSETDMAREG(0, 3, 0, 0))
        else: k.emit(getattr(TT, 'TT' + op)())
    k.addi(counter, counter, -1)
    k.bne(counter, R.ZERO, 'loop')
    stall(k, Stall.SYNC, Wait.THCON)
    pc_sync(k)
    k.read(sink, TensixMMIO.REGFILE_BASE)
    k.write(SINK, sink)
    k.fence()
    p.record('body')
    expected = 3
    if op in OPS:
        for _ in range(BODY * iterations): expected = result(op, 0, expected, 1)
    return k.lower(), p, expected


@pytest.mark.parametrize('op,mode', CASES)
@pytest.mark.parametrize('role', ('trisc0', 'trisc1', 'trisc2'))
def test_tensix_control_timing(bh, request, op, mode, role):
    points = []
    for iterations in COUNTS:
        image, p, expected = build(op, mode, iterations, role)
        samples = []
        for sample in range(8):
            bh.launch({role: image}, l1={SINK: bytes(4)}, profiler=p)
            assert unpack('<I', bh.read_l1(bh.core, SINK, 4))[0] == expected
            if sample: samples.append(p.last['body'])
        points.append(dict(iterations=iterations, body_operations=BODY * iterations,
                           raw_cycles=samples, min=min(samples), median=median(samples), max=max(samples),
                           image_bytes=len(image), image_sha256=hashlib.sha256(image).hexdigest()))
    save(dict(family='tensix_control', instruction=op, case=op + '_' + mode, role=role,
              card=request.config.getoption('--bh-device'), core=list(bh.core), core_index=bh.core_index,
              points=points, body_size=BODY, warmup_launches=1, samples_per_point=7,
              adjacent_slopes_cycles_per_body_op=[
                  (b['median'] - a['median']) / (b['body_operations'] - a['body_operations'])
                  for a, b in zip(points, points[1:])],
              semantics='mode 0 ALU dependent chain; final GPR sink checked',
              completion='THCON STALLWAIT + PC sync + GPR read + sink + fence',
              loop='16 body operations + addi/bne; no baseline subtraction',
              source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
