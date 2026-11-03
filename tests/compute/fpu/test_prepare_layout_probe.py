import numpy as np
from tests.compute.fpu.test_matmul_peak_fp32 import run_case
from examples import matmul_peak as m

def test_layout(bh, monkeypatch):
  a=np.arange(1024,dtype=np.uint32).reshape(32,32)
  a=((a+0x3c00)<<16).view(np.float32)
  b=np.tile(a,(1,4))
  results=list(run_case(bh,monkeypatch,a,b,dtype='bf16'))
  print('ERROR',np.linalg.norm(results[0][0]-results[0][1])/np.linalg.norm(results[0][1]))
  for cb,addr,size,pages in m.asm.CONTEXT['cbs']:
    if cb==2:
      data=np.frombuffer(bh.read_l1(bh.core,addr,2048),'<u2').astype(int)-0x3c00
      expect=np.arange(1024).reshape(32,2,16).transpose(1,0,2).ravel()
      print('MISMATCH',np.where(data!=expect)[0][:40].tolist())
