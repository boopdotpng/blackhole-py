"""Measured instruction correctness, independent placement and poison guards."""
import json
from statistics import median
from struct import pack, unpack
import pytest
from tests.operation_pocs.fpu.emit import OPS
from tests.operation_pocs.fpu.fixture import images, INPUT, INPUT_A, INPUT_B, OUTPUT, REPEATS

# All aligned matrix A starts; independent B and first/last physical FP32 Dst.
PLACEMENTS = ((0, 7, 0), (2, 0, 7), (4, 3, 32), (6, 1, 63))
CASES = [
    (op, a, b, d, broadcast, accum, fidelity)
    for op in OPS for a, b, d in (PLACEMENTS if op in ('mvmul','gapool','gmpool') else PLACEMENTS + ((7,6,1),))
    for broadcast in (range(4) if op.startswith('elw') else (0,))
    for accum in ((False, True) if op in ('elwadd', 'elwsub') else (True,))
    for fidelity in ((1, 2) if op == 'mvmul' else (2,))
]

def bf16(value): return unpack('<f', pack('<I', unpack('<I', pack('<f', value))[0] & 0xffff0000))[0]


def inputs(op, a, b, dst, broadcast, accumulate, fidelity):
    # Binary fractions keep exact accumulation. A low mantissa bits exercise
    # HiFi2; LoFi control uses exact powers of two to separate addressing.
    av = [(-1 if i % 5 == 0 else 1) * (1 + (i*13 % 128)/128) for i in range(256)]
    bv = [0.5 + (i*37 % 64)/128 for i in range(128)]
    if fidelity == 1: av = [(-1 if i%5 == 0 else 1)*2. for i in range(256)]; bv = [0.5]*128
    if op == 'gmpool': bv = [1.]*128
    banks = [[bf16(8 + (i%127)/16) for i in range(1024)], [bf16(-8 - (i%127)/16) for i in range(1024)]]
    count = 256 if op in ('mvmul','gapool','gmpool') else 128
    banks[0][a*128:a*128+count] = av[:count]
    banks[1][b*128:(b+1)*128] = bv
    initial = [1 + (i%31)/(512 if op in ('d2a', 'd2b') else 32) for i in range(1024)]
    # Moves from Dst explicitly test narrowing of non-BF16 values.
    expected = initial.copy(); offset = (dst%8)*128
    if op.startswith('elw'):
        for i in range(128):
            row, col = divmod(i, 16)
            value_b = bv[(0 if broadcast&2 else row)*16 + (0 if broadcast&1 else col)]
            value = av[i]+value_b if op == 'elwadd' else av[i]-value_b if op == 'elwsub' else av[i]*value_b
            expected[offset+i] = initial[offset+i] + REPEATS*value if accumulate else value
    elif op in ('mvmul','gapool'):
        for row in range(8 if op == 'mvmul' else 4):
            for col in range(16):
                expected[offset+row*16+col] += REPEATS*sum(bv[row*16+k]*av[k*16+col] for k in range(16))
    elif op == 'gmpool':
        for col in range(16): expected[offset+col] = max(initial[offset+col], *(av[k*16+col] for k in range(16)))
        expected[offset+16:offset+64] = [0.]*48
    elif op == 'zero': expected[offset:offset+128] = [0.]*128
    elif op in ('a2d','b2d'): expected[offset:offset+128] = av[:128] if op == 'a2d' else bv
    elif op == 'd2a': banks[0][a*128:(a+1)*128] = list(map(bf16, initial[offset:offset+128]))
    elif op == 'd2b': banks[1][b*128:(b+1)*128] = list(map(bf16, initial[offset:offset+128]))
    # Build initial source buffers separately, since D2A/B mutate only the oracle.
    physical_a = [bf16(8+(i%127)/16) for i in range(1024)]
    physical_b = [bf16(-8-(i%127)/16) for i in range(1024)]
    physical_a[a*128:a*128+count] = av[:count]; physical_b[b*128:(b+1)*128] = bv
    data = {INPUT: pack('<1024f', *initial), OUTPUT: b'\xa5'*4160}
    for addr, values in ((INPUT_A,physical_a),(INPUT_B,physical_b)):
        data[addr] = pack('<1024H', *(unpack('<I',pack('<f',v))[0]>>16 for v in values))
    return data, expected, banks


@pytest.mark.parametrize('op,a,b,dst,broadcast,accumulate,fidelity', CASES)
def test_operation(bh, request, op, a, b, dst, broadcast, accumulate, fidelity):
    args = (op,a,b,dst,broadcast,accumulate,fidelity)
    data, expected, banks = inputs(*args)
    code, profile = images(*args)
    samples = {label: [] for label in ('operation','complete','control')}
    for sample in range(8): # One warmup, seven retained measured launches.
        bh.launch(code, l1=data, profiler=profile)
        actual = unpack('<1024f',bh.read_l1(bh.core,OUTPUT,4096))
        assert actual == tuple(expected), [(i,x,y) for i,(x,y) in enumerate(zip(actual,expected)) if x!=y][:12]
        assert bh.read_l1(bh.core,OUTPUT+4096,64) == b'\xa5'*64
        if sample:
            for label in samples: samples[label].append(profile.last[label])
    initial = unpack('<1024f', data[INPUT])
    for tile in range(8):
        if tile == dst//8: continue
        code, profile = images(*args, output_tile=tile)
        bh.launch(code,l1=data,profiler=profile)
        assert unpack('<1024f',bh.read_l1(bh.core,OUTPUT,4096)) == initial
    for bank, reference in zip(('a','b'), banks):
        code, profile = images(*args, observe=bank)
        bh.launch(code,l1=data,profiler=profile)
        actual = unpack('<1024f',bh.read_l1(bh.core,OUTPUT,4096))
        assert actual == tuple(reference), (bank, [(i,x,y) for i,(x,y) in enumerate(zip(actual,reference)) if x!=y][:12])
    record = dict(op=op,A=a,B=b,Dst=dst,broadcast=broadcast,accumulate=accumulate,fidelity=fidelity,
                  dtype='BF16 sources/FP32 Dst',N=128,K=REPEATS,raw=samples,
                  device=request.config.getoption('--bh-device'),core_index=bh.core_index,core=list(bh.core),
                  summary={k:dict(min=min(v),median=median(v),max=max(v),median_per_call=median(v)/REPEATS) for k,v in samples.items()})
    print('FPU_RESULT '+json.dumps(record,sort_keys=True))
