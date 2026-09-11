"""BF16 Dst contract with exactly representable signed integer controls."""
import json
from struct import pack, unpack
from statistics import median
import pytest
from tests.operation_pocs.fpu.fixture import images, INPUT, INPUT_A, INPUT_B, OUTPUT
from tests.operation_pocs.fpu.emit import OPS
from tests.operation_pocs.fpu.test_fpu import bf16

CASES = [(op,a,b,d,mode,accum,fidelity) for op in OPS
         for a,b,d in (((0,7,0),(6,1,127)) if op in ('mvmul','gapool','gmpool') else ((0,7,0),(6,1,127),(7,0,64)))
         for mode in (range(4) if op.startswith('elw') else (0,))
         for accum in ((False,True) if op in ('elwadd','elwsub') else (True,))
         for fidelity in ((1,2) if op=='mvmul' else (2,))]

@pytest.mark.parametrize('op,a,b,dst,broadcast,accumulate,fidelity',CASES)
def test_bf16_dst(bh,request,op,a,b,dst,broadcast,accumulate,fidelity):
    av=[float((i*7+i//16)%5-2) for i in range(1024)]
    bv=[float((i*3+i//16)%3-1) for i in range(1024)]
    if op=='gmpool': bv=[1.]*1024
    initial=av.copy(); expected=initial.copy(); offset=(dst%8)*128
    aa=av[a*128:a*128+256]; bb=bv[b*128:(b+1)*128]
    if op.startswith('elw'):
        for i in range(128):
            row,col=divmod(i,16); v=bb[(0 if broadcast&2 else row)*16+(0 if broadcast&1 else col)]
            value=aa[i]+v if op=='elwadd' else aa[i]-v if op=='elwsub' else aa[i]*v
            expected[offset+i]=(initial[offset+i] if accumulate else 0)+value
    elif op in ('mvmul','gapool'):
        for row in range(8 if op=='mvmul' else 4):
            for col in range(16): expected[offset+row*16+col]+=sum(bb[row*16+k]*aa[k*16+col] for k in range(16))
    elif op=='gmpool':
        for col in range(16): expected[offset+col]=max(initial[offset+col],*(aa[k*16+col] for k in range(16)))
        expected[offset+16:offset+64]=[0.]*48
    elif op=='zero': expected[offset:offset+128]=[0.]*128
    elif op in ('a2d','b2d'): expected[offset:offset+128]=aa[:128] if op=='a2d' else bb
    banks=[av.copy(),bv.copy()]
    if op=='d2a': banks[0][a*128:(a+1)*128]=initial[offset:offset+128]
    if op=='d2b': banks[1][b*128:(b+1)*128]=initial[offset:offset+128]
    encode=lambda xs: pack('<1024H',*(unpack('<I',pack('<f',v))[0]>>16 for v in xs))
    data={INPUT:pack('<1024f',*initial),INPUT_A:encode(av),INPUT_B:encode(bv),OUTPUT:b'\xa5'*4160}
    args=(op,a,b,dst,broadcast,accumulate,fidelity)
    code,profile=images(*args,fp32=False,repeats=1)
    samples={k:[] for k in ('operation','complete','control')}
    def check(reference):
        actual=[unpack('<f',pack('<I',v<<16))[0] for v in unpack('<1024H',bh.read_l1(bh.core,OUTPUT,2048))]
        assert actual==reference, [(i,x,y) for i,(x,y) in enumerate(zip(actual,reference)) if x!=y][:12]
        assert bh.read_l1(bh.core,OUTPUT+2048,64)==b'\xa5'*64
    for sample in range(8):
        bh.launch(code,l1=data,profiler=profile); check(expected)
        if sample:
            for key in samples: samples[key].append(profile.last[key])
    for tile in range(16):
        if tile == dst//8: continue
        code,profile=images(*args,fp32=False,repeats=1,output_tile=tile)
        bh.launch(code,l1=data,profiler=profile);check(initial)
    for bank,reference in zip(('a','b'),banks):
        code,profile=images(*args,fp32=False,repeats=1,observe=bank)
        bh.launch(code,l1=data,profiler=profile);check(reference)
    print('FPU_RESULT '+json.dumps(dict(op=op,A=a,B=b,Dst=dst,broadcast=broadcast,accumulate=accumulate,fidelity=fidelity,
        dtype='BF16 sources/BF16 Dst',N=128,K=1,raw=samples,
        device=request.config.getoption('--bh-device'),core_index=bh.core_index,core=list(bh.core),
        summary={k:dict(min=min(v),median=median(v),max=max(v),median_per_call=median(v)) for k,v in samples.items()}),sort_keys=True))
