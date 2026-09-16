"""Resident-source FP8/FP16 MVMUL throughput, matching matmul_peak's MAC count.

This is an arithmetic microbenchmark, not a numerical 5000-cubed GEMM.
Loads/setup and validation packing are outside the completed timed interval.
"""
import argparse
import json
from pathlib import Path
from statistics import median
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import numpy as np
from asm import Asm
from cq import McastWrite, Run, rectangles
from device import Device
from program import Program
from pcie import TLBWindow
from ttko.isa import R, Tensix as TT
from tests.movement.test_noc import _record_clock, TIMING_L1_ADDRESS, CB_ADDRESS
from tests.movement.profile_matmul_fp8 import clock_mhz
from tests.movement.unpacker.unpack import (
  FP8_E4M3, FP16, F32, CFG_BASE, PackCfg, Sem, SemWait, Stall, Wait,
  configure_unpack_pair, configure_mop, _mop_loop_words, _unpacr, run_mop,
  stall, pc_sync, sem_get, sem_wait, _set_thread_cfg, _rmw_cfg_byte,
  load_replay, publish_dst, configure_packer,
)
from tests.movement.packer.pack import _configure_row_addressing, _configure_row_mop, _set_dst_position

A, B, OUT, READY = CB_ADDRESS, CB_ADDRESS+2048, CB_ADDRESS+4096, CB_ADDRESS+24576
# Current 5000^3 plan: 504 x 464 outputs per worker, K padded to 5008.
COUNT = (2*504*5008*464)//4096


def images(count):
  u,m,p = (Asm(role) for role in ('trisc0','trisc1','trisc2'))
  configure_unpack_pair(u,A,B,input_format=FP8_E4M3)
  u.emit(TT.TTSETADCXX(3,1023,0))
  configure_mop(u,_mop_loop_words(1,1,start=_unpacr(0),loop=_unpacr(1),last=_unpacr(1),outer_last=_unpacr(1)))
  run_mop(u)
  stall(u,Stall.SYNC,Wait.UNPACK0|Wait.UNPACK1)
  sem_get(u,Sem.UNPACK_SYNC); pc_sync(u)
  u.write(READY,1); u.fence()
  m.wait(READY,1,bytes=4)
  _set_thread_cfg(m,0,0); _set_thread_cfg(m,1,0)
  _rmw_cfg_byte(m,CFG_BASE+4,3,0x20,0)  # FP16 Dst, not FP32
  for reg in (11,12,28,47): _set_thread_cfg(m,reg,0)
  m.emit(TT.TTSETRWC(0,0,0,0,0,15))
  m.emit(TT.TTZEROACC(3,0,0,1,0))
  stall(m,Stall.MATH,Wait.SRCA_VLD|Wait.SRCB_VLD)
  words=[TT.TTMVMUL(0,0,0,i*8) for i in range(32)]
  load_replay(m,0,words)
  repeats,tail=divmod(count,32)
  # Keep the MOP inner count below its hardware field limit. Larger counts
  # silently truncate, so issue multiple 256-replay groups instead.
  groups,remainder=divmod(repeats,256)
  replay=TT.TTREPLAY(0,32,0,0)
  configure_mop(m,_mop_loop_words(1,256 if groups else remainder,loop=replay,last=replay,outer_last=replay))
  stall(m,Stall.SYNC,Wait.MATH); pc_sync(m)
  _record_clock(m,TIMING_L1_ADDRESS)
  if groups:
    remaining=m.reg(); m.li(remaining,groups)
    loop=m._new_label('mvmul_groups'); m.label(loop)
    run_mop(m); m.addi(remaining,remaining,-1); m.bne(remaining,R.ZERO,loop)
    if remainder:
      configure_mop(m,_mop_loop_words(1,remainder,loop=replay,last=replay,outer_last=replay))
      run_mop(m)
  else:
    run_mop(m)
  for word in words[:tail]: m.emit(word)
  stall(m,Stall.SYNC,Wait.MATH); pc_sync(m)
  _record_clock(m,TIMING_L1_ADDRESS+8)
  m.emit(TT.TTSETRWC(3,0,0,0,0,15)); publish_dst(m)
  sem_wait(p,Sem.MATH_PACK,SemWait.ON_ZERO,Stall.TDMA)
  configure_packer(p,F32,source_format=FP16,dst_fp32=False)
  _configure_row_addressing(p); _configure_row_mop(p,64,close=True)
  for tile in range(4):
    pc_sync(p); _set_dst_position(p,tile,0)
    p.write(PackCfg.L1_DESTINATION,((OUT+tile*4096)>>4)-1|0x80000000)
    p.write(PackCfg.DESTINATION_OFFSET,0)
    p.emit(TT.TTSETADCXX(4,15,0)); run_mop(p)
    stall(p,Stall.SYNC,Wait.PACK0); pc_sync(p)
  sem_get(p,Sem.MATH_PACK)
  return {k.role:k.lower() for k in (u,m,p)}


def main():
  parser=argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--device',required=True,type=int)
  parser.add_argument('--cores',nargs='+',type=int,default=[1,110,117])
  parser.add_argument('--counts',nargs='+',type=int,default=[512,COUNT])
  parser.add_argument('--runs',type=int,default=7)
  parser.add_argument('--json',type=Path,required=True)
  args=parser.parse_args()
  if args.runs <= 0 or any(count < 32 for count in args.counts):
    parser.error('runs must be positive and instruction counts at least 32')
  device=Device(args.device); rows=[]
  try:
    device.boot()
    for count in args.counts:
      binary=images(count)
      repeats,tail=divmod(count,32)
      expected=np.repeat(np.array([min(repeats+(i<tail),2048)/256 for i in range(32)],np.float32),128)
      for ncores in args.cores:
        # Match matmul's 10 x 11 grid for the principal comparison.
        cores=tuple((x,y) for y in range(2,12) for x in (*range(1,8),*range(10,14))) if ncores==110 else device.cores[:ncores]
        assert len(cores)==ncores and set(cores)<=set(device.cores)
        program=Program({core:binary for core in cores})
        l1={A:bytes([8])*1024,B:bytes([8])*1024,OUT:bytes([0xa5])*16384,READY:bytes(4)}
        device.cq.submit(program.commands(l1=l1),timeout=10)
        samples=[]
        with TLBWindow(device.pcie.fd,cores[0]) as window:
          mhz=clock_mhz(window)
          for _ in range(args.runs):
            # Reinitialize ready so source configuration precedes math setup.
            device.cq.submit((McastWrite(rectangles(cores),READY,bytes(4)),Run(cores)),timeout=10)
            stamps=[]
            for core in cores:
              window.target(0,core)
              stamps.append(struct.unpack('<QQ',window.read(TIMING_L1_ADDRESS,16)))
              actual=np.frombuffer(window.read(OUT,16384),dtype='<f4')
              assert np.array_equal(actual,expected),(core,count,actual[:16],expected[:16])
            cycles=max(end for _,end in stamps)-min(start for start,_ in stamps)
            samples.append(dict(us=cycles/mhz,tflops=count*4096*ncores*mhz/cycles/1e6,
                max_core_cycles=max(end-start for start,end in stamps),
                skew_cycles=max(start for start,_ in stamps)-min(start for start,_ in stamps)))
        row=dict(cores=ncores,mvmul_per_core=count,aiclk_mhz=mhz,samples=samples,
                 median_us=median(s['us'] for s in samples),median_tflops=median(s['tflops'] for s in samples))
        rows.append(row); print(json.dumps(row),flush=True)
        args.json.write_text(json.dumps(rows,indent=2)+'\n')
  finally: device.close()


if __name__=='__main__': main()
