"""Native FP8 tile matrix multiplication on card 1."""
import numpy as np
from ttko.device import Device
from ttko.program import DType, Program

d=Device(1)
try:
 d.init_device();cores=(d.dram.cores[50],)
 a=d.dram.buffer('a',DType.FP8,(32,32),None,cores=cores)
 b=d.dram.buffer('b',DType.FP8,(32,32),None,cores=cores)
 c=d.dram.buffer('c',DType.F32,(32,32),None,cores=cores)
 p=Program(cores,a,b,c,fp32_dst=True)
 ac,bc,cc=p.cb(a.dtype),p.cb(b.dtype),p.cb(c.dtype)
 p.brisc.noc.read_tiles_into_cb(a,(0,),ac);p.brisc.noc.read_tiles_into_cb(b,(0,),bc)
 p.unpack.move_matmul(ac,bc,right_transpose=True)
 p.fpu.matmul(dst_tile=0,right_transpose=True).publish()
 p.pack.move(cc,tile=0);p.ncrisc.noc.write_from_cb(cc,c,0)
 rng=np.random.default_rng(55)
 av=a.to_numpy(a.from_numpy(rng.normal(size=a.shape)))
 bv=b.to_numpy(b.from_numpy(rng.normal(size=b.shape)))
 d.write(a,a.from_numpy(av));d.write(b,b.from_numpy(bv));d.run(p)
 actual=c.to_numpy(d.read(c))
 av=np.where(np.abs(av)<.015625,0,av);bv=np.where(np.abs(bv)<.015625,0,bv)
 expected=av@bv.T
 print(actual[:2,:8],expected[:2,:8],flush=True)
 np.testing.assert_allclose(actual,expected,rtol=.01,atol=.01)
finally:d.close()
