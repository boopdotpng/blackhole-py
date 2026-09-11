"""Signed values, zeros, and BF16 rounding boundaries on measured emitters."""
from struct import pack
import pytest
from tests.movement.unpacker import unpack as u
from tests.operation_pocs.transport import test_transport as p, test_source as s, test_dst as d

# Finite normalized values, signed zero and both directions of halfway rounding.
EDGES = [0,0x80000000,0x3f800000,0xbf800000,0x3f808000,0x3f818000,
         0xbf808000,0xbf818000,0x00800000,0x80800000,0x477f0000,0xc77f0000]
WORDS = (EDGES * 11)[:128]

def rounded_bf16(word):
  if word & 0x7fffffff == 0: return 0  # BF16 pack canonicalizes signed zero.
  return ((word + 0x8000) >> 16) & 0xffff

@pytest.mark.parametrize('fmt',[u.BF16,u.F32])
@pytest.mark.parametrize('operation',['pack','dst','srcA','srcB'])
def test_signed_and_rounding_edges(bh,fmt,operation):
  slot=7 if operation.startswith('src') else 31
  a=[0x4000+i%128 for i in range(1024)];b=[0x4200+i%128 for i in range(1024)]
  source_words=[0x43000000+i*1031 for i in range(8192)]
  source_bytes=pack('<8192I',*source_words)
  short=pack('<128H',*[x>>16 for x in WORDS]) if fmt==u.BF16 else pack('<128I',*WORDS)
  if operation=='pack': images,profile=p.pack_images(slot,fmt)
  elif operation=='dst': images,profile=d.dst_images(slot,fmt)
  else: images,profile=s.source_images(u.UnpackTarget.SRCA if operation=='srcA' else u.UnpackTarget.SRCB,slot,fmt)
  cycles=[];control=[]
  for iteration in range(8):
    if operation=='pack':
      words=source_words.copy();words[slot*128:slot*128+128]=WORDS
      expected=pack('<128H',*[rounded_bf16(x) for x in WORDS]) if fmt==u.BF16 else pack('<128I',*WORDS)
      bh.launch(images,params=(128,),l1={p.INPUT:pack('<8192I',*words),p.OUTPUT-64:b'\xa5'*704,p.SCRATCH-64:b'\xa5'*704},profiler=profile)
      assert bh.read_l1(bh.core,p.OUTPUT-64,704)==b'\xa5'*64+expected+b'\xa5'*(640-len(expected))
      assert bh.read_l1(bh.core,p.OBSERVE,32768)==pack('<8192I',*words)
      label='pack complete'
    elif operation=='dst':
      expected=source_words.copy();expected[slot*128:slot*128+128]=[x&0xffff0000 for x in WORDS] if fmt==u.BF16 else WORDS
      bh.launch(images,params=(128,),l1={d.INPUT:source_bytes,d.A:pack('<1024H',*a),d.B:pack('<1024H',*b),d.SHORT:short},profiler=profile)
      assert bh.read_l1(bh.core,d.OUTPUT,32768)==pack('<8192I',*expected)
      assert bh.read_l1(bh.core,d.SOURCE_OUT,8192)==pack('<2048I',*[x<<16 for x in a+b])
      label='unpack Dst complete'
    else:
      expected_a=a.copy();expected_b=b.copy()
      (expected_a if operation=='srcA' else expected_b)[slot*128:slot*128+128]=[0 if x & 0x7fffffff == 0 else x>>16 for x in WORDS]
      bh.launch(images,params=(128,),l1={s.A:pack('<1024H',*a),s.B:pack('<1024H',*b),s.DST_INPUT:source_bytes,s.INPUT:short},profiler=profile)
      assert bh.read_l1(bh.core,s.DST_OUTPUT,32768)==source_bytes
      assert bh.read_l1(bh.core,s.OUTPUT,8192)==pack('<2048I',*[x<<16 for x in expected_a+expected_b])
      label='unpack complete'
    if iteration:cycles.append(profile.last[label]);control.append(profile.last['empty'])
  p.evidence(bh,operation+' signed edges',fmt,slot,128,cycles)
  p.evidence(bh,operation+' edges marker control',fmt,slot,128,control)
