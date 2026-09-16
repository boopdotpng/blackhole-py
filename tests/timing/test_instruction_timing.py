"""Fixed-body timing slopes for the five-stream predictor.

Run only through tt-device-queue, with --bh-device matching its queue.
TIMING_OUTPUT optionally names a JSONL result file (one file per process).
These are timing probes: scalar sinks are checked; SFPU probes establish
completion/timing, not arithmetic correctness. Existing operation_pocs supply
independent arithmetic oracles. No test asserts a performance threshold.
"""
import hashlib
import json
import os
from pathlib import Path
from statistics import median
from struct import unpack

import pytest
from asm import Asm
from isa import R, RV32, Tensix as TT
from tests.profiler import Profiler
from tests.operation_pocs.sfpu_math.emit import constant, drain

ROLES = ('brisc', 'ncrisc', 'trisc0', 'trisc1', 'trisc2')
COUNTS = (64, 128, 256)
BODY = 16
SINK = 0x70000
RV_CASES = ('empty', 'addi_dep', 'add_dep', 'xor_dep', 'mul_dep', 'mul_ind4',
            'divu_one', 'divu_large', 'remu_large', 'fence', 'csr_cycle',
            'load_l1_hot_dep', 'load_l1_miss_dep', 'store_l1_same',
            'store_l1_coalesced', 'fadd_dep', 'fadd_ind4', 'fmul_dep', 'fmadd_dep')
SF_CASES = ('empty', 'nop', 'loadi', 'mov_dep', 'iadd_dep', 'add_dep', 'add_ind4',
            'mul_dep', 'mul_ind4', 'mad_dep', 'mad_ind4', 'arecip_dep',
            'mul24_dep', 'cast_dep', 'transp', 'swap', 'swap_nop',
            'shuffle', 'shuffle_nop', 'shft2_bit', 'setcc', 'encc', 'dma_nop')


def save(record):
    print('INSTRUCTION_TIMING ' + json.dumps(record, sort_keys=True))
    if name := os.environ.get('TIMING_OUTPUT'):
        with Path(name).open('a') as f:
            f.write(json.dumps(record, sort_keys=True) + '\n')


def rv_body(k, case, x, one, ptr, independent):
    for i in range(BODY):
        if case == 'empty': continue
        if case == 'addi_dep': k.addi(x, x, 1)
        elif case == 'add_dep': k.add(x, x, one)
        elif case == 'xor_dep': k.xor(x, x, one)
        elif case == 'mul_dep': k.mul(x, x, one)
        elif case == 'mul_ind4': k.mul(independent[i % 4], independent[i % 4], one)
        elif case == 'divu_one': k.divu(x, x, one)
        elif case == 'divu_large': k.divu(x, ptr, one)  # invariant 0xffffffff / 3
        elif case == 'remu_large': k.remu(x, ptr, one)
        elif case == 'fence': k.fence()
        elif case == 'csr_cycle': k.csrrs(x, R.ZERO, 0xC00)
        elif case.startswith('load_l1'): k.lw(x, x, 0)  # initialized pointer cycle
        elif case == 'store_l1_same': k.sw(one, ptr, 0)
        elif case == 'store_l1_coalesced': k.sw(one, ptr, (i % 4) * 4)
        elif case.startswith('f'):
            # FP register namespace is independent of assembler integer regs.
            d = (i % 4) if case == 'fadd_ind4' else 0
            if case == 'fmadd_dep':
                # fmadd.s fd, fd, f4, f5, RNE; f4=1, f5=0.
                k.emit((5 << 27) | (4 << 20) | (d << 15) | (d << 7) | 0x43)
            else:
                f7 = 0x08 if case == 'fmul_dep' else 0x00
                k.emit((f7 << 25) | (4 << 20) | (d << 15) | (d << 7) | 0x53)
        else: raise ValueError(case)


def sf_body(k, case):
    for i in range(BODY):
        d = i % 4 if case.endswith('ind4') else 0
        if case == 'empty': continue
        if case == 'nop': word = TT.TTSFPNOP()
        elif case == 'loadi': word = TT.TTSFPLOADI(d, 0, 0x3f80)
        elif case == 'mov_dep': word = TT.TTSFPMOV(0, d, d, 0)
        elif case == 'iadd_dep': word = TT.TTSFPIADD(1, d, d, 0)
        elif case.startswith('add_'): word = TT.TTSFPADD(10, d, 9, d, 0)
        elif case.startswith('mul_'): word = TT.TTSFPMUL(d, 10, 9, d, 0)
        elif case.startswith('mad_'): word = TT.TTSFPMAD(d, 10, 9, d, 0)
        elif case == 'arecip_dep': word = TT.TTSFPARECIP(0, d, d, 0)
        elif case == 'mul24_dep': word = TT.TTSFPMUL24(d, 10, 9, d, 0)
        elif case == 'cast_dep': word = TT.TTSFPCAST(d, d, 0)
        elif case == 'transp': word = TT.TTSFPTRANSP()
        elif case.startswith('swap'): word = TT.TTSFPSWAP(0, 0, 1, 0)
        elif case.startswith('shuffle'): word = TT.TTSFPSHFT2(0, 0, 0, 3)
        elif case == 'shft2_bit': word = TT.TTSFPSHFT2(0, 0, 0, 5)
        elif case == 'setcc': word = TT.TTSFPSETCC(0, 0, 0, 0)
        elif case == 'encc': word = TT.TTSFPENCC(0, 0, 0, 2)
        elif case == 'dma_nop': word = TT.TTDMANOP()
        else: raise ValueError(case)
        k.emit(word)
        if case.endswith('_nop'): k.emit(TT.TTSFPNOP())


def build(role, family, case, count):
    k = Asm(role)
    clear_bits = int(os.environ.get('TIMING_CLEAR_CFG0_BITS', '0'), 0)
    saved_cfg = None
    if clear_bits:
        saved_cfg, mask = k.reg(2)
        k.li(mask, clear_bits)
        k.csrrc(saved_cfg, mask, 0x7c0)
    x, one, ptr, counter = k.reg(4)
    independent = k.reg(4)
    k.li(x, 3); k.li(one, 1); k.li(ptr, SINK + 0x100)
    for reg in independent: k.li(reg, 3)
    if case in ('divu_large', 'remu_large'):
        k.li(ptr, 0xffffffff); k.li(one, 3)
    l1 = {SINK: bytes(32)}
    if case.startswith('load_l1'):
        # Four lines fit the tiny L0; 8 lines exceed it. Pointer recurrence is
        # the actual dependency, no dependent ADDI hidden in the denominator.
        lines = 1 if 'hot' in case else 8
        k.li(x, SINK + 0x100)
        for i in range(lines):
            l1[SINK + 0x100 + i*16] = (SINK + 0x100 + ((i+1) % lines)*16).to_bytes(4, 'little')
    if family == 'sfpu':
        k.emit(TT.TTSFPENCC(0, 0, 0, 2))
        for reg in range(8): constant(k, reg, 1.)
        drain(k)
    elif case.startswith(('fadd', 'fmul', 'fmadd')):
        k.li(R.T0, 0x3f800000)
        for fr in range(5): k.emit((0x78 << 25) | (int(R.T0) << 15) | (fr << 7) | 0x53)
        k.emit((0x78 << 25) | (5 << 7) | 0x53)  # fmv.w.x f5, x0
    k.fence()
    p = Profiler(k)
    k.li(counter, count)
    p.record('body')
    k.label('timed_loop')
    if family == 'riscv': rv_body(k, case, x, one, ptr, independent)
    else: sf_body(k, case)
    k.addi(counter, counter, -1)
    k.bne(counter, R.ZERO, 'timed_loop')
    if family == 'sfpu': drain(k)
    else:
        # Materialize the scalar sink before the stop marker and drain stores.
        # FP result move also forces the final FP computation to complete.
        if case.startswith(('fadd', 'fmul', 'fmadd')):
            k.emit((0x70 << 25) | (int(R.T0) << 7) | 0x53)
            k.write(SINK, R.T0)
        else: k.write(SINK, x)
        k.fence()
    p.record('body')
    if saved_cfg is not None: k.csrrs(R.ZERO, saved_cfg, 0x7c0)
    return k.lower(), p, l1


def measure(bh, request, role, family, case):
    rows = []
    for count in COUNTS:
        image, p, initial = build(role, family, case, count)
        samples = []
        for sample in range(8):
            bh.launch({role: image}, l1=initial, profiler=p)
            sink = unpack('<I', bh.read_l1(bh.core, SINK, 4))[0]
            expected = None
            if case in ('addi_dep', 'add_dep'): expected = 3 + BODY*count
            elif case in ('xor_dep', 'mul_dep', 'mul_ind4', 'divu_one'): expected = 3
            elif case == 'divu_large': expected = 0x55555555
            elif case == 'remu_large': expected = 0
            elif case.startswith('load_l1'): expected = SINK + 0x100
            elif case in ('fmul_dep', 'fmadd_dep'): expected = 0x3f800000
            if family == 'riscv' and expected is not None: assert sink == expected, (case, sink, expected)
            assert p.last['body'] > 0
            if sample: samples.append(p.last['body'])
        rows.append(dict(iterations=count, body_operations=BODY*count, raw_cycles=samples,
                         min=min(samples), median=median(samples), max=max(samples),
                         image_bytes=len(image), image_sha256=hashlib.sha256(image).hexdigest()))
    # Includes amortized two-instruction loop, stalls and queue service. An
    # empty-loop slope is reported separately; subtracting it from SFPU is
    # generally invalid because scalar control can overlap backend work.
    slopes = [(b['median']-a['median'])/(b['body_operations']-a['body_operations'])
              for a,b in zip(rows,rows[1:])]
    save(dict(family=family, case=case, role=role, card=request.config.getoption('--bh-device'),
              core=list(bh.core), core_index=bh.core_index, warmup_launches=1, samples_per_point=7,
              body_size=BODY, points=rows, adjacent_slopes_cycles_per_body_op=slopes,
              semantics='scalar sinks checked where specified; SFPU timing/completion only',
              loop='16 body operations + addi/bne; swap_nop/shuffle_nop add 16 SFPNOPs',
              completion='SFPU STALLWAIT+PC sync; RISC sink+fence',
              clear_cfg0_bits=os.environ.get('TIMING_CLEAR_CFG0_BITS', '0'),
              source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))


@pytest.mark.parametrize('role', ROLES)
@pytest.mark.parametrize('case', RV_CASES)
def test_riscv_timing(bh, request, role, case):
    measure(bh, request, role, 'riscv', case)


@pytest.mark.parametrize('case', SF_CASES)
def test_sfpu_timing(bh, request, case):
    measure(bh, request, 'trisc1', 'sfpu', case)


@pytest.mark.parametrize('role', ROLES)
def test_timing_context(bh, request, role):
    """Capture CSR chicken bits and measure a real local-RAM dependency chain."""
    from firmware import build as build_firmware
    k = Asm(role)
    value, ptr, count = k.reg(3)
    for i, csr in enumerate((0x7c0, 0x7c1, 0x7c2)):
        k.csrrs(value, R.ZERO, csr)
        k.write(SINK + 4*i, value)
    k.fence()
    bh.launch({role: k.lower()}, l1={SINK: bytes(32)})
    csr_values = unpack('<3I', bh.read_l1(bh.core, SINK, 12))
    fw = build_firmware(bh.device.pcie.sysmem.noc_addr >> 32, bh.device.pcie.dram_endpoints)
    points = []
    for iterations in COUNTS:
        k = Asm(role)
        address = k.local.alloc(16)
        x, counter = k.reg(2)
        k.write(address, address)
        k.li(x, address)
        k.li(counter, iterations)
        k.fence()
        p = Profiler(k)
        p.record('local_load')
        k.label('local_loop')
        for _ in range(BODY): k.lw(x, x, 0)
        k.addi(counter, counter, -1)
        k.bne(counter, R.ZERO, 'local_loop')
        k.write(SINK+16, x)
        k.fence()
        p.record('local_load')
        image = k.lower()
        times = []
        for sample in range(8):
            bh.launch({role: image}, profiler=p)
            assert unpack('<I',bh.read_l1(bh.core,SINK+16,4))[0] == address
            if sample: times.append(p.last['local_load'])
        points.append(dict(iterations=iterations, body_operations=BODY*iterations,
                           raw_cycles=times, median=median(times), min=min(times), max=max(times)))
    save(dict(family='context', role=role, card=request.config.getoption('--bh-device'),
              core=list(bh.core), cfg0=hex(csr_values[0]), pmacfg0=hex(csr_values[1]),
              pmacfg1=hex(csr_values[2]), l0_data_disabled=bool(csr_values[0] & 8),
              ttinsn_fusion_disabled=bool(csr_values[0] & (1 << 18)),
              firmware_worker_sha256=[hashlib.sha256(b).hexdigest() for b in fw.workers],
              local_load_points=points,
              local_load_slopes=[(b['median']-a['median'])/(b['body_operations']-a['body_operations'])
                                 for a,b in zip(points,points[1:])]))
