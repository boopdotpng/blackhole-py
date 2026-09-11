"""Compare native FP8 GEMV against its quantized CPU operands on card 1."""
import argparse
import numpy as np
from ttko.device import Device
from ttko.program import DType
from examples.llama3_8b_fp8 import decode_projection, _sfpu_float_words
from ttko.sfpu import LReg
from fp8 import encode, decode

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-scale', type=float, default=0.023668639361858368)
parser.add_argument('--weight-scale', type=float, default=0.0017361111240461469)
args=parser.parse_args()
d=Device(1)
try:
 d.init_device(); cores=(d.dram.cores[50],)
 x=d.dram.buffer('x',DType.BF16,(1,4096),None,cores=cores)
 w=d.dram.buffer('w',DType.FP8,(16,4096),0,cores=cores)
 y=d.dram.buffer('y',DType.BF16,(1,16),0,cores=cores)
 rng=np.random.default_rng(4)
 xv=rng.normal(size=x.shape).astype(np.float32)
 wv=rng.normal(scale=.03,size=w.shape).astype(np.float32)
 p=decode_projection(x,w,y)
 d.write(x,x.from_numpy(xv)); d.write(w,w.from_numpy(wv/args.weight_scale))
 params={f"{name}_{part}": int(word) for name,value in (("input_scale",1/args.input_scale),("output_scale_0",args.input_scale*args.weight_scale)) for part,word in enumerate(_sfpu_float_words(LReg.L6,value))}
 d.run(p,params=params)
 actual=y.to_numpy(d.read(y)).flatten()
 quant=lambda v: np.where(np.abs(v)<.015625,0,decode(encode(v)))
 expected=quant(wv/args.weight_scale)@quant(x.to_numpy(x.from_numpy(xv)).flatten()/args.input_scale)*args.weight_scale*args.input_scale
 print('actual',actual, '\nexpected',expected,flush=True)
 np.testing.assert_allclose(actual,expected,rtol=.03,atol=.03)
finally:d.close()
