"""Packer read/add/write accumulation into initialized L1, with guard checks."""
import json
from statistics import median
import numpy as np
import pytest
from asm import Asm
from ttko.isa import Tensix as TT
from tests.movement.unpacker import unpack as u
from tests.movement.packer import pack as p
from tests.profiler import Profiler
from firmware.consts import TensixL1

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
OUTPUT = INPUT + 32768


def images(n, repeats, accumulate, fmt):
    loader, math, packer = (Asm(role) for role in ('trisc0','trisc1','trisc2'))
    count=loader.reg(); loader.li(count,n*4)
    u.emit_unpack_to_dst(loader,INPUT,count,0,0)
    u.sem_post(math,u.Sem.MATH_DONE)
    u.sem_wait(math,u.Sem.UNPACK_TO_DEST,u.SemWait.ON_ZERO,u.Stall.SYNC)
    u.sem_get(math,u.Sem.UNPACK_TO_DEST)
    u.publish_dst(math)
    u.sem_wait(packer,u.Sem.MATH_PACK,u.SemWait.ON_ZERO,u.Stall.TDMA)
    u.configure_packer(packer,fmt)
    p._configure_row_addressing(packer)
    p._configure_row_mop(packer,n//16,close=True)
    # LLK reconfigure_packer_l1_acc: disable generated zero flags as well.
    u.stall(packer,u.Stall.CFG,u.Wait.PACK0)
    u._rmw_cfg_byte(packer,u.CFG_BASE+70*4,0,4,4 if accumulate else 0)
    u._rmw_cfg_byte(packer,u.CFG_BASE+71*4,2,8,8 if accumulate else 0)
    profile=Profiler(packer); u.pc_sync(packer); profile.record('pack')
    for _ in range(repeats):
        p._set_dst_position(packer,0,0)
        packer.write(u.PackCfg.L1_DESTINATION,(OUTPUT>>4)-1 | 0x80000000)
        packer.write(u.PackCfg.DESTINATION_OFFSET,0)
        packer.emit(TT.TTSETADCXX(4,15,0))
        u.run_mop(packer)
        u.stall(packer,u.Stall.SYNC,u.Wait.PACK0)
        u.pc_sync(packer)
    profile.record('pack')
    u._rmw_cfg_byte(packer,u.CFG_BASE+70*4,0,4,0)
    u._rmw_cfg_byte(packer,u.CFG_BASE+71*4,2,8,0)
    u.sem_get(packer,u.Sem.MATH_PACK)
    return {k.role:k.lower() for k in (loader,math,packer)},profile


@pytest.mark.parametrize('fmt',(u.F32,u.BF16))
@pytest.mark.parametrize('n',(16,256,1024))
@pytest.mark.parametrize('repeats',(1,4))
def test_l1_accumulation(bh,n,repeats,fmt):
    x=((np.arange(n)%17)-8).astype('<f4')*.25
    initial=((np.arange(n)%11)-5).astype('<f4')*.5
    x[::16]=0
    if n==1024: x[:256]=0 # A whole zero face must preserve previous L1 values.
    itemsize=4 if fmt==u.F32 else 2
    def encode(v):
        return v.tobytes() if fmt==u.F32 else (v.view('<u4')>>16).astype('<u2').tobytes()
    results={}
    for accumulate in (False,True):
        code,profile=images(n,repeats,accumulate,fmt)
        samples=[]
        for repeat in range(5):
            bh.launch(code,l1={INPUT:x.tobytes(),OUTPUT-64:b'\xa5'*64,
                      OUTPUT:encode(initial)+b'\xa5'*64},profiler=profile)
            expected=initial+repeats*x if accumulate else x
            actual=bh.read_l1(bh.core,OUTPUT,n*itemsize)
            assert actual==encode(expected), (accumulate,fmt,np.frombuffer(actual,dtype='<u4' if fmt==0 else '<u2')[:16])
            assert bh.read_l1(bh.core,OUTPUT-64,64)==b'\xa5'*64
            assert bh.read_l1(bh.core,OUTPUT+n*itemsize,64)==b'\xa5'*64
            if repeat:samples.append(profile.last['pack'])
        results['accumulate' if accumulate else 'overwrite']=median(samples)
    print('PACK_L1_ACC '+json.dumps(dict(n=n,repeats=repeats,fmt=fmt,median_cycles=results)))
