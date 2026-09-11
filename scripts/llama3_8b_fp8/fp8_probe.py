"""Validate E4M3 pack/unpack contracts on card 1, including subnormal flushing."""
import json
from pathlib import Path
import numpy as np
from ttko.device import Device
from ttko.program import Program, DType
from ttko.unpack import UnpackTarget
from examples.llama3_8b_fp8 import _round_fp8_program
from fp8 import encode, decode


def main():
  d=Device(1)
  results=[]
  try:
    d.init_device(); cores=(d.pcie.cores[50],)
    values=np.resize(decode(np.arange(127,dtype=np.uint8)),1024)
    values[512:]*=-1
    for src,dst in ((DType.FP8,DType.F32),(DType.F32,DType.FP8)):
      x=d.dram.buffer('x',src,(1024,),None,cores=cores)
      y=d.dram.buffer('y',dst,(1024,),None,cores=cores)
      p=Program(cores,x,y,fp32_dst=True)
      a,b=p.cb(src),p.cb(dst)
      p.brisc.noc.read_tiles_into_cb(x,(0,),a)
      p.unpack.move(a,UnpackTarget.SRCA)
      p.fpu.copy_a_tiles(dst_tiles=(0,))
      if dst is DType.FP8:p.sfpu.map(_round_fp8_program(dst),tile=0)
      p.sfpu.publish()
      p.pack.move(b,tile=0)
      p.ncrisc.noc.write_from_cb(b,y,0)
      d.write(x,x.from_numpy(values));d.run(p)
      actual=y.to_numpy(d.read(y))
      # MOVA2D under FP32 accumulation preserves the FP16 exponent encoding.
      # Arithmetic kernels use ELWMUL/MVMUL instead, which interpret it directly.
      if src is DType.FP8: actual*=2.**112
      expected=np.where(np.abs(values)<2.**-6,np.copysign(0.,values),values)
      np.testing.assert_array_equal(actual,expected)
      results.append({'source':src.name,'target':dst.name,'max_error':float(np.max(np.abs(actual-expected)))})
    Path('validation/fp8-format.json').write_text(json.dumps({'device':1,'checks':results},indent=2)+'\n')
    print(results)
  finally:d.close()

if __name__=='__main__':main()
