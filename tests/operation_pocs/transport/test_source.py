"""Selected source allocations, poisoned guards and runtime prefix sweep."""
import os
from struct import pack
import pytest
from asm import Asm
from ttko.isa import Tensix as TT
from tests.profiler import Profiler
from tests.operation_pocs.transport.observation import copy_source
from tests.movement.unpacker import unpack as u
from tests.operation_pocs.transport.ops import unpack_source, unpack_source_scatter
from tests.operation_pocs.transport.test_transport import runtime, evidence, BASE

A, B, INPUT = BASE, BASE + 4096, BASE + 8192
SCRATCH, OUTPUT = BASE + 0x3000, BASE + 0x4000
DST_INPUT, DST_OUTPUT = BASE + 0x8000, BASE + 0x10000


def seed_source(k, target, address, *, publish=False):
  engine = int(target == u.UnpackTarget.SRCB)
  u.configure_unpacker(k, engine, address, u.BF16, target)
  k.emit(TT.TTSETADCXX(engine+1, 1023, 0))
  k.emit(TT.TTSETADCZW(3,0,0,0,0,0xF))
  k.emit(TT.TTUNPACR(engine, 0, 0, 0, 0, 1, int(publish), 0, 0, 0, 0, 0, 1))
  u.stall(k, u.Stall.UNPACK, u.Wait.UNPACK1 if engine else u.Wait.UNPACK0)
  u.sem_get(k, u.Sem.UNPACK_SYNC)
  u.pc_sync(k)


def source_images(target, slot, fmt, capacity=128, *, segments=None, native=False):
  loader, math, packer = [Asm(role) for role in ('trisc0','trisc1','trisc2')]
  size = loader.reg(); loader.li(size, 4096 if segments is None else 32768)
  for tile in (range(8) if segments is None else (0,)):
    u.emit_unpack_to_dst(loader, DST_INPUT + tile * 4096, size, tile, 0)
    u.sem_post(math, u.Sem.MATH_DONE)
    u.sem_wait(math, u.Sem.UNPACK_TO_DEST, u.SemWait.ON_ZERO, u.Stall.SYNC)
    u.sem_get(math, u.Sem.UNPACK_TO_DEST)
  seed_source(loader, u.UnpackTarget.SRCA, A, publish=(target == u.UnpackTarget.SRCB))
  seed_source(loader, u.UnpackTarget.SRCB, B, publish=(target == u.UnpackTarget.SRCA))
  count = runtime(loader)
  profile = Profiler(loader)
  profile.record('empty'); profile.record('empty')
  profile.record('unpack complete')
  if native:
    assert segments and all(n == capacity for _, n in segments)
    unpack_source_scatter(loader, target=target, source=INPUT, slots=tuple(slot for slot, _ in segments),
                          input_format=fmt, capacity=capacity)
  elif segments is None:
    unpack_source(loader, target=target, slot=slot, source=INPUT, count=count,
                  scratch=SCRATCH, input_format=fmt, capacity=capacity, profile=profile)
  else:
    offset = 0
    for index, (destination, n) in enumerate(segments):
      loader.li(count, n)
      unpack_source(loader, target=target, slot=destination, source=INPUT + offset, count=count,
                    scratch=SCRATCH, input_format=fmt, capacity=capacity,
                    publish=index == len(segments) - 1)
      offset += n * (2 if fmt == u.BF16 else 4)
  profile.record('unpack complete')
  u.pc_sync(loader)
  u.sem_post(loader, u.Sem.UNPACK_TO_DEST)
  u.sem_wait(math, u.Sem.UNPACK_TO_DEST, u.SemWait.ON_ZERO, u.Stall.SYNC)
  u.sem_get(math, u.Sem.UNPACK_TO_DEST)
  u.publish_dst(math)
  u.sem_wait(math, u.Sem.MATH_DONE, u.SemWait.ON_ZERO, u.Stall.SYNC)
  u.sem_get(math, u.Sem.MATH_DONE)
  copy_source(math, u.UnpackTarget.SRCA, 0)
  u.pc_sync(math)
  copy_source(math, u.UnpackTarget.SRCB, 1)
  math.emit(TT.TTSETRWC(3,0,0,0,0,0xF))
  u.publish_dst(math)
  u.pc_sync(math)
  for tile in range(8):
    u.emit_pack_dst(packer, tile, DST_OUTPUT + tile * 4096, u.F32,
                    configure=(tile == 0), wait_for_dst=(tile == 0))
  u.finish_pack(packer)
  u.sem_post(packer, u.Sem.MATH_DONE)
  u.emit_pack_dst(packer, 0, OUTPUT, u.F32)
  u.emit_pack_dst(packer, 1, OUTPUT+4096, u.F32, configure=False, wait_for_dst=False)
  u.finish_pack(packer)
  u.pc_sync(packer)
  return {k.role:k.lower() for k in (loader,math,packer)}, profile


@pytest.mark.parametrize('target,slot,capacity', [
  (u.UnpackTarget.SRCA,0,128), (u.UnpackTarget.SRCA,7,128),
  (u.UnpackTarget.SRCB,0,128), (u.UnpackTarget.SRCB,7,128),
  (u.UnpackTarget.SRCA,0,256), (u.UnpackTarget.SRCA,6,256)])
@pytest.mark.parametrize('fmt',[u.BF16,u.F32])
def test_source_prefixes(bh,target,slot,capacity,fmt):
  images,profile=source_images(target,slot,fmt,capacity)
  a=[0x4000+i%256 for i in range(1024)]
  b=[0x4200+i%256 for i in range(1024)]
  dst_poison=pack('<8192I', *[0x43000000 + i * 1031 for i in range(8192)])
  words=[((0x3F00+i%128)<<16)|((i*1031)&65535) for i in range(capacity)]
  lengths=[capacity] if capacity==256 else [int(x) for x in os.getenv('TRANSPORT_LENGTHS',','.join(map(str,range(1,129)))).split(',')]
  for n in lengths:
    expected_a, expected_b=a.copy(),b.copy()
    expected = expected_a if target==u.UnpackTarget.SRCA else expected_b
    expected[slot*128:slot*128+capacity]=[x>>16 for x in words[:n]]+[0]*(capacity-n)
    source=pack(f'<{n}H',*[x>>16 for x in words[:n]]) if fmt==u.BF16 else pack(f'<{n}I',*words[:n])
    samples=[]; controls=[]; staging=[]
    for iteration in range(8):
      poison=b'\xA5' if iteration%2 else b'\x5A'
      bh.launch(images,params=(n,),l1={A:pack('<1024H',*a),B:pack('<1024H',*b),
                  DST_INPUT:dst_poison,DST_OUTPUT:poison*32832,
                  INPUT:source+poison*64,SCRATCH-64:poison*(capacity*4+192),OUTPUT:poison*8256},profiler=profile)
      assert bh.read_l1(bh.core,DST_OUTPUT,32768)==dst_poison
      assert bh.read_l1(bh.core,DST_OUTPUT+32768,64)==poison*64
      actual=bh.read_l1(bh.core,OUTPUT,8192)
      want=pack('<2048I',*[x<<16 for x in expected_a+expected_b])
      assert actual==want
      assert bh.read_l1(bh.core,SCRATCH-64,64)==poison*64
      assert bh.read_l1(bh.core,SCRATCH+capacity*(2 if fmt==u.BF16 else 4)+64,64)==poison*64
      assert bh.read_l1(bh.core,OUTPUT+8192,64)==poison*64
      if iteration:
        samples.append(profile.last['unpack complete']); controls.append(profile.last['empty'])
        staging.append(profile.last['stage and zero fill'])
    evidence(bh,target.name,fmt,slot,n,samples)
    evidence(bh,'marker control',fmt,slot,n,controls)
    evidence(bh,'stage and zero fill',fmt,slot,n,staging)
