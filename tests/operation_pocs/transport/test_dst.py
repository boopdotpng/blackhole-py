"""Exact L1->Dst preservation through SFPU lane insertion."""
import os
from struct import pack
import pytest
from asm import Asm
from tests.profiler import Profiler
from tests.operation_pocs.transport.observation import copy_source
from tests.movement.unpacker import unpack as u
from tests.operation_pocs.transport.dst import unpack_dst
from tests.operation_pocs.transport.test_transport import BASE, runtime, evidence

INPUT=BASE
A=BASE+0x8000
B=BASE+0x9000
SHORT=BASE+0xA000
OUTPUT=BASE+0xB000
SOURCE_OUT=BASE+0x14000


def dst_images(slot,fmt, *, segments=None):
  loader,math,packer=[Asm(role) for role in ('trisc0','trisc1','trisc2')]
  size=loader.reg(); loader.li(size,4096 if segments is None else 32768)
  for tile in (range(8) if segments is None else (0,)):
    u.emit_unpack_to_dst(loader,INPUT+tile*4096,size,tile,0)
    u.sem_post(math,u.Sem.MATH_DONE)
    u.sem_wait(math,u.Sem.UNPACK_TO_DEST,u.SemWait.ON_ZERO,u.Stall.SYNC)
    u.sem_get(math,u.Sem.UNPACK_TO_DEST)
  u.configure_unpack_pair(loader,A,B)
  loader.emit(__import__('isa').Tensix.TTSETADCXX(3,1023,0))
  u.configure_mop(loader,u._mop_loop_words(1,1,start=u._unpacr(0),loop=u._unpacr(1),last=u._unpacr(1),outer_last=u._unpacr(1)))
  u.run_mop(loader)
  u.stall(loader,u.Stall.UNPACK,u.Wait.UNPACK0|u.Wait.UNPACK1)
  u.sem_get(loader,u.Sem.UNPACK_SYNC)
  u.pc_sync(loader)
  u.stall(math,u.Stall.MATH,u.Wait.SRCA_VLD|u.Wait.SRCB_VLD)
  u.pc_sync(math)
  count=runtime(math)
  profile=Profiler(math)
  profile.record('empty');profile.record('empty')
  profile.record('unpack Dst complete')
  if segments is None:
    unpack_dst(math,dst_slot=slot,source=SHORT,count=count,input_format=fmt)
  else:
    offset = 0
    for destination, n in segments:
      math.li(count, n)
      unpack_dst(math,dst_slot=destination,source=SHORT+offset,count=count,input_format=fmt)
      offset += n * (2 if fmt == u.BF16 else 4)
  profile.record('unpack Dst complete')
  u.publish_dst(math)
  # Wait until packer has captured every Dst allocation before observation scratch.
  u.sem_wait(math,u.Sem.MATH_DONE,u.SemWait.ON_ZERO,u.Stall.SYNC)
  u.sem_get(math,u.Sem.MATH_DONE)
  copy_source(math,u.UnpackTarget.SRCA,0)
  copy_source(math,u.UnpackTarget.SRCB,1)
  math.emit(__import__('isa').Tensix.TTSETRWC(3,0,0,0,0,0xF))
  u.publish_dst(math)
  for tile in range(8):
    u.emit_pack_dst(packer,tile,OUTPUT+tile*4096,u.F32,configure=(tile==0),wait_for_dst=(tile==0))
  u.finish_pack(packer)
  u.sem_post(packer,u.Sem.MATH_DONE)
  u.emit_pack_dst(packer,0,SOURCE_OUT,u.F32)
  u.emit_pack_dst(packer,1,SOURCE_OUT+4096,u.F32,configure=False,wait_for_dst=False)
  u.finish_pack(packer)
  return {k.role:k.lower() for k in (loader,math,packer)},profile


@pytest.mark.parametrize('slot',[0,31,63])
@pytest.mark.parametrize('fmt',[u.BF16,u.F32])
def test_dst_prefixes(bh,slot,fmt):
  images,profile=dst_images(slot,fmt)
  words=[((0x4100+i%128)<<16)|((i*1031)&65535) for i in range(8192)]
  a=[0x4000+i%256 for i in range(1024)]; b=[0x4200+i%256 for i in range(1024)]
  short=[((0x3F00+i)<<16)|((i*1031)&65535) for i in range(128)]
  lengths=[int(x) for x in os.getenv('TRANSPORT_LENGTHS',','.join(map(str,range(1,129)))).split(',')]
  for n in lengths:
    expected=words.copy()
    expected[slot*128:slot*128+128]=[x&0xffff0000 if fmt==u.BF16 else x for x in short[:n]]+[0]*(128-n)
    source=pack(f'<{n}H',*[x>>16 for x in short[:n]]) if fmt==u.BF16 else pack(f'<{n}I',*short[:n])
    samples=[]; controls=[]
    for iteration in range(8):
      poison=b'\xA5' if iteration%2 else b'\x5A'
      bh.launch(images,params=(n,),l1={INPUT:pack('<8192I',*words),A:pack('<1024H',*a),B:pack('<1024H',*b),
                  SHORT:source+poison*64,OUTPUT:poison*32832,SOURCE_OUT:poison*8256},profiler=profile)
      assert bh.read_l1(bh.core,OUTPUT,32768)==pack('<8192I',*expected)
      assert bh.read_l1(bh.core,SOURCE_OUT,8192)==pack('<2048I',*[x<<16 for x in a+b])
      assert bh.read_l1(bh.core,OUTPUT+32768,64)==poison*64
      assert bh.read_l1(bh.core,SOURCE_OUT+8192,64)==poison*64
      if iteration:
        samples.append(profile.last['unpack Dst complete']);controls.append(profile.last['empty'])
    evidence(bh,'unpack Dst SFPU',fmt,slot,n,samples)
    evidence(bh,'marker control',fmt,slot,n,controls)
