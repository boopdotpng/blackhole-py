"""Individual operations; full-Dst fixture poison and independent FP64 oracles."""
import json
import math
from hashlib import sha256
from statistics import median
from struct import pack, unpack
import pytest
from asm import Asm
from isa import Tensix as TT
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, Sem, SemWait, Stall, Wait, _set_thread_cfg, configure_fp32_dst,
  emit_unpack_to_dst, pc_sync, publish_dst, sem_get, sem_post, sem_wait, stall,
)
from tests.profiler import Profiler
from .emit import OPS, arithmetic, drain

INPUT, OUTPUT = 0x50000, 0x60000
SIZE = 8192


@pytest.fixture(scope='module', autouse=True)
def hardware_context(bh, request):
  from fw.build import build
  firmware=build(bh.device.pcie.sysmem.noc_addr >> 32,bh.device.pcie.dram_endpoints)
  print('SFPU_CONTEXT '+json.dumps(dict(device=request.config.getoption('--bh-device'),
    core_index=bh.core_index,core=bh.core,firmware_worker_sha256=[sha256(image).hexdigest() for image in firmware.workers],
    config='FP32 Dst; thread cfg12/28/47=0; RWC=0; architectural L9=0 L10=1')))


def images(op, slots, mask='all', alias='none', mode='refined', k_repeat=1):
  loader, compute, packer = (Asm(r) for r in ('trisc0','trisc1','trisc2'))
  n=loader.reg(); loader.li(n,SIZE*4)
  emit_unpack_to_dst(loader, INPUT,n,0,0)
  compute.emit(TT.TTZEROACC(3,1,0,1,0))  # Fixture only, poison follows.
  stall(compute,Stall.SYNC,Wait.MATH)
  sem_post(compute,Sem.MATH_DONE)
  sem_wait(compute,Sem.UNPACK_TO_DEST,SemWait.ON_ZERO,Stall.SYNC)
  sem_get(compute,Sem.UNPACK_TO_DEST)
  configure_fp32_dst(compute,0)
  for register in (12,28,47): _set_thread_cfg(compute,register,0)
  compute.emit(TT.TTSETRWC(0,0,0,0,0,0xF))
  compute.emit(TT.TTSFPENCC(0,0,0,2))
  p=Profiler(compute)
  drain(compute)
  p.record('empty'); p.record('empty')
  for pos in range(4):
    compute.emit(TT.TTSFPENCC(0,0,0,2))
    for reg,slot in enumerate(slots): compute.emit(TT.TTSFPLOAD(reg,3,0,slot*8+pos*2))
    # Fixture mask allocation slot 31; +-1 values avoid sign-magnitude confusion.
    compute.emit(TT.TTSFPLOAD(7,3,0,31*8+pos*2))
    compute.emit(TT.TTSFPENCC(3,0,0,10))
    compute.emit(TT.TTSFPSETCC(0,7,0,4))
    drain(compute)
    p.accumulate('control')
    drain(compute)
    p.accumulate('control')
    p.accumulate(op)
    for _ in range(k_repeat): arithmetic(compute,op,0,0 if alias in ('other','all') else 1,0 if alias in ('addend','all') else 2,mode=mode)
    drain(compute)
    p.accumulate(op)
    compute.emit(TT.TTSFPENCC(0,0,0,2))
    compute.emit(TT.TTSFPSTORE(0,3,0,slots[0]*8+pos*2))
  drain(compute); publish_dst(compute)
  n=packer.reg(); packer.li(n,SIZE)
  emit_pack_dst_to_cb(packer,0,OUTPUT,n,output_format=F32)
  return {k.role:k.lower() for k in (loader,compute,packer)}, p


def enabled(mask, i):
  lane=(i%64)//2
  return {'all':True,'none':False,'alternating':lane%2==0,'lane17':lane==17}[mask]


def values(op, mode='refined'):
  if op=='exp': return [(-1.99 + i*3.98/127) if mode=='native' else (-80+i*160/127) for i in range(128)]
  if op=='reciprocal': return [(-1 if i%2 else 1)*math.ldexp(1+(i%16)/16, (i//16-4)*20) for i in range(128)]
  return [(-1 if i%3 else 1)*(1+i/16) for i in range(128)]


def f32(x): return unpack('<f',pack('<f',x))[0]


def reference(op,x,y,z):
  return {'add':lambda:x+y,'sub':lambda:x-y,'mul':lambda:x*y,'mad':lambda:x*y+z,
          'neg':lambda:-x,'abs':lambda:abs(x),'exp':lambda:math.exp(x),'reciprocal':lambda:1/x}[op]()


def run(bh,op,slots=(0,17,63),mask='all',alias='none',mode='refined',samples=7,inputs=None,k_repeat=1):
  data=[f32(-30-(i%113)/16) for i in range(SIZE)]
  xs=list(map(f32,values(op,mode) if inputs is None else inputs))
  ys=[f32(.75+i/64) for i in range(128)]
  zs=[f32(-2.5+i/32) for i in range(128)]
  for slot,vs in zip(slots,(xs,ys,zs)): data[slot*128:(slot+1)*128]=vs
  data[31*128:32*128]=[1. if enabled(mask,i) else -1. for i in range(128)]
  imgs,p=images(op,slots,mask,alias,mode,k_repeat)
  times=[]; empty=[]; controls=[]; worst=(0.,0.,0,0.,0.,0.)
  for sample in range(samples+1):
    bh.launch(imgs,l1={INPUT:pack(f'<{SIZE}f',*data),OUTPUT:b'\xa5'*(SIZE*4+64)},profiler=p)
    got=unpack(f'<{SIZE}f',bh.read_l1(bh.core,OUTPUT,SIZE*4))
    assert bh.read_l1(bh.core,OUTPUT+SIZE*4,64)==b'\xa5'*64
    start=slots[0]*128
    assert got[:start]==tuple(data[:start])
    assert got[start+128:]==tuple(data[start+128:])
    for i,x in enumerate(xs):
      target=x
      if enabled(mask,i):
        for _ in range(k_repeat):
          target=reference(op,target,target if alias in ('other','all') else ys[i],target if alias in ('addend','all') else zs[i])
          if op not in ('exp','reciprocal'): target=f32(target)
      actual=got[start+i]
      absolute=abs(actual-target); relative=absolute/abs(target) if target else absolute
      ulps=abs(unpack('<I',pack('<f',actual))[0]-unpack('<I',pack('<f',target))[0])
      if relative>worst[0]: worst=(relative,absolute,ulps,x,actual,target)
      tolerance=(.025 if mode=='native' else 8e-5) if op=='exp' else (.006 if mode=='native' else 3e-7) if op=='reciprocal' else 0
      # MAD is partially fused. Repeated rounded intermediates diverge from
      # the FP64 ideal-FMA oracle; retain exact dyadic single-call assertions,
      # and declare a one-ULP-per-call final bound for this noncanceling chain.
      valid=ulps<=k_repeat if op=='mad' and k_repeat>1 else relative<=tolerance
      assert valid,(op,mode,slots,mask,alias,i,x,actual,target,relative,ulps)
    if sample: times.append(p.last[op]); empty.append(p.last['empty']); controls.append(p.last['control'])
  record=dict(op=op,mode=mode,slots=slots,mask=mask,alias=alias,dtype='fp32',N=128,K=4*k_repeat,warmup=1,raw=times,empty=empty,control=controls,min=min(times),median=median(times),max=max(times),cycles_per_vector=median(times)/(4*k_repeat),worst=worst,core=str(bh.core))
  print('SFPU_RESULT '+json.dumps(record))
  return record


@pytest.mark.parametrize('op',OPS)
def test_operations(bh,op): run(bh,op)


@pytest.mark.parametrize('op',OPS)
@pytest.mark.parametrize('mask',('none','alternating','lane17'))
def test_masks_placement(bh,op,mask): run(bh,op,slots=(63,4,0),mask=mask)


# Binary operations ignore addend: 'all' emits exactly the 'other' kernel.
# Keep 'addend' for their distinct, non-aliased placement at slots (7,0,57).
@pytest.mark.parametrize('op,alias', [
  pytest.param(op, alias, id=f'{alias}-{op}')
  for alias in ('other','addend','all') for op in ('add','sub','mul','mad')
  if alias != 'all' or op == 'mad'
])
def test_aliases(bh,op,alias): run(bh,op,slots=(7,0,57),alias=alias)


@pytest.mark.parametrize('op',('exp','reciprocal'))
def test_native(bh,op): run(bh,op,mode='native')


@pytest.mark.parametrize('op',('add','sub','mul','mad','neg','abs'))
def test_repeated_short_operations(bh,op):
  run(bh,op,k_repeat=16)


@pytest.mark.parametrize('mode',('native','refined'))
@pytest.mark.parametrize('exponent',(-126,-125,-64,-1,0,1,64,124,125))
def test_reciprocal_boundaries(bh,mode,exponent):
  # Every LUT mantissa bin: alternate lower and upper representable boundaries.
  words=[((exponent+127)<<23) | (m<<16) | (65535 if m%2 else 0) for m in range(128)]
  xs=[unpack('<f',pack('<I',w | (0x80000000 if i%3 else 0)))[0] for i,w in enumerate(words)]
  run(bh,'reciprocal',mode=mode,inputs=xs)


@pytest.mark.parametrize('mode',('native','refined'))
def test_exp_boundaries(bh,mode):
  centers=(0.,2**-126,2**-8,.015625,.5,.6953125,1.,1.5,1.99) if mode=='native' else (0.,2**-126,2**-8,.5,1.,2.,8.,32.,64.,80.,87.)
  xs=[]
  for center in centers:
    w=unpack('<I',pack('<f',center))[0]
    for delta in (-1,0,1):
      x=unpack('<f',pack('<I',max(0,w+delta)))[0]
      xs.extend((x,-x))
  run(bh,'exp',mode=mode,inputs=(xs*128)[:128])


# test_native[exp] already measures the native implementation on these inputs.
@pytest.mark.parametrize('mode',('refined',))
def test_exp_same_domain_comparison(bh,mode):
  run(bh,'exp',mode=mode,inputs=values('exp','native'))


@pytest.mark.parametrize('op',('exp','reciprocal'))
@pytest.mark.parametrize('mode',('native','refined'))
def test_exception_characterization(bh,op,mode):
  # A characterization ledger, explicitly NOT a full IEEE semantic pass.
  words=(0,0x80000000,1,0x80000001,0x007fffff,0x807fffff,
         0x00800000,0x80800000,0x7e800000,0xfe800000,
         0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00000,0xffc00000)
  data=[-37.25]*SIZE
  xs=[unpack('<f',pack('<I',w))[0] for w in words]*8
  data[:128]=xs
  data[31*128:32*128]=[1.]*128
  imgs,p=images(op,(0,17,63),mode=mode)
  samples=[]; controls=[]; empty=[]; outputs=[]
  for sample in range(8):
    bh.launch(imgs,l1={INPUT:pack(f'<{SIZE}f',*data),OUTPUT:b'\xa5'*(SIZE*4+64)},profiler=p)
    raw=bh.read_l1(bh.core,OUTPUT,SIZE*4)
    assert raw[512:]==pack(f'<{SIZE-128}f',*data[128:])
    assert bh.read_l1(bh.core,OUTPUT+SIZE*4,64)==b'\xa5'*64
    outputs=list(unpack('<16I',raw[:64]))
    if sample:
      samples.append(p.last[op]); controls.append(p.last['control']); empty.append(p.last['empty'])
  print('SFPU_EXCEPTION '+json.dumps(dict(op=op,mode=mode,dtype='fp32',N=128,slots=(0,17,63),mask='all',alias='none',warmup=1,inputs=[hex(w) for w in words],outputs=[hex(w) for w in outputs],raw=samples,control=controls,empty=empty,min=min(samples),median=median(samples),max=max(samples),K=4,cycles_per_vector=median(samples)/4,core=str(bh.core),semantic_scope='characterization; unsupported inputs do not establish IEEE conformance')))
