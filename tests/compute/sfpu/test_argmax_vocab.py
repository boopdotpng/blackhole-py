"""250k-logit DRAM -> distributed argmax -> one device-side winner."""
import json
from statistics import median
import numpy as np
import pytest
from ttko.isa import R
from tests.movement import noc
from tests.compute.sfpu.test_argmax import INPUT, RESULT, READY, images, encode

PARTIALS=INPUT+65536
FINAL=PARTIALS+4096


def transfer(k,local,remote,coordinate,size,write=False):
    with k.scope():
        cfg=noc.InterleavedConfig((coordinate,),local,1,2048,command_slot=1,tid=3,standalone=True)
        niu,command,src,dst,coord,n=k.reg(6)
        k.li(niu,cfg.niu); k.li(command,cfg.command)
        noc._wait_command_ready(k,command)
        noc._initialize_command(k,command,noc._control(cfg,write=write),cfg.tid)
        here=noc._local_coordinate(k,cfg)
        k.li(src,local if write else remote);k.li(dst,remote if write else local)
        k.li(coord,coordinate);k.li(n,size)
        noc._submit(k,command,source_address=src,source_coordinate=here if write else coord,
                    target_address=dst,target_coordinate=coord if write else here,byte_count=n)
        noc._wait_command_ready(k,command)
        if write:noc._wait_zero(k,niu,noc.STATUS+noc.WRITES_OUTGOING+cfg.tid*4)
        noc._wait_zero(k,niu,noc.STATUS+noc.REQUESTS_OUTSTANDING+cfg.tid*4)


def collect(k,start,slot,cores):
    with k.scope():
        idx,base=k.reg(2);k.read(idx,RESULT+4);k.li(base,start);k.add(idx,idx,base)
        k.write(RESULT+4,idx);k.write(RESULT+8,1);k.fence()
    coordinate=cores[0][0] | cores[0][1]<<6
    transfer(k,RESULT,PARTIALS+slot*16,coordinate,16,True)
    if slot:return
    with k.scope():
        best,index,ptr,key,candidate,ready=k.reg(6)
        k.li(best,0);k.li(index,0x7fffffff);k.li(ptr,PARTIALS)
        for _ in k.range(len(cores)):
            wait=k._new_label('partial');skip=k._new_label('skip');replace=k._new_label('replace')
            k.label(wait);k.lw(ready,ptr,8);k.beq(ready,R.ZERO,wait);k.fence()
            k.lw(key,ptr);k.lw(candidate,ptr,4)
            k.bltu(best,key,replace);k.bne(best,key,skip);k.bgeu(candidate,index,skip)
            k.label(replace);k.mv(best,key);k.mv(index,candidate)
            k.label(skip);k.addi(ptr,ptr,16)
        k.write(FINAL,best);k.write(FINAL+4,index);k.fence()


@pytest.mark.parametrize('case',('random','last','ties'))
def test_vocab_argmax(bh,case):
    count=250_000
    shard=4096
    cores=tuple(bh.device.cores[:(count+shard-1)//shard])
    assert len(cores)==(count+shard-1)//shard
    values=np.random.default_rng(183).normal(size=count).astype('f4')
    if case=='last':values[-1]=100
    if case=='ties':values[:]=-10;values[[3073,8192,249999]]=-1
    payload,words=encode(values,True)
    keys=np.where(words>>15,(~words)&65535,words^0x8000)
    expected=(int(keys.max()),int(keys.argmax()))
    buf=bh.dram_buffer(len(payload),initial=payload)
    variants={}
    for sfpu in (False,True):
        codes={};profiles=[]
        for slot,core in enumerate(cores):
            start=slot*shard;local_count=min(shard,count-start)
            size=(local_count+1023)//1024*2048
            def before(k,start=start,size=size):transfer(k,INPUT,buf.address+start*2,buf.coordinate,size)
            def after(k,start=start,slot=slot):collect(k,start,slot,cores)
            codes[core],p=images(local_count,sfpu=sfpu,before=before,after=after)
            profiles.append(p)
        variants['sfpu' if sfpu else 'brisc']=(codes,profiles[0])
    samples={name:[] for name in variants}
    for repeat in range(5):
        for name in (tuple(variants) if repeat%2 else tuple(variants)[::-1]):
            codes,p=variants[name]
            bh.launch_many_mapped(codes,l1={READY:bytes(16),PARTIALS:bytes(len(cores)*16),FINAL:bytes(16)})
            actual=tuple(np.frombuffer(bh.read_l1(cores[0],FINAL,8),dtype='<u4'))
            assert actual==expected,(name,actual,expected)
            p._report(bh.device,cores[0],bh.timeout)
            if repeat:samples[name].append(p.last['argmax'])
    print('ARGMAX_VOCAB '+json.dumps(dict(case=case,count=count,cores=len(cores),
          source='single-bank DRAM',samples=samples,
          median_cycles={k:median(v) for k,v in samples.items()})))
