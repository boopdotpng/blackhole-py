"""One-token fused RoPE/attention check: with one key the output must equal V."""
import numpy as np
from ttko.device import Device
from examples import llama3_8b_fp8 as m

d=Device(1)
try:
 d.init_device()
 r=m.Llama3Decode.__new__(m.Llama3Decode);r.device=d;r.attention_cores=32;r._allocate()
 rng=np.random.default_rng(14)
 for b in (r.q_compact,r.k_compact,r.v_compact):
  values=rng.normal(size=b.shape).astype(np.float32)
  d.write(b,b.from_numpy(values))
  if b is r.v_compact: vvalues=b.to_numpy(b.from_numpy(values))
 cos,sin=m.rope_table()
 d.write(r.cos,r.cos.from_numpy(cos));d.write(r.sin,r.sin.from_numpy(sin))
 cache=r.layers[0]
 for name in ('key_cache','value_cache'):
  b=cache[name];d.write(b,bytes(np.prod(b.shape)*b.dtype.itemsize))
 d.run()
 p=m.gqa_attention_fused(r.q_heads,cache['key_cache'],cache['value_cache'],r.context,rope_inputs=(r.q_compact,r.k_compact,r.v_compact,r.cos,r.sin),attention_cores=32)
 print('Running',m.ATTENTION_DTYPE,flush=True)
 d.cache_kernels((p,))
 d.queue(p)
 trace=d.capture_trace(("start_pos","kv_blocks","valid_columns"))
 trace.replay({"start_pos":0,"kv_blocks":1,"valid_columns":1}, timeout=5.)
 actual=r.context.to_numpy(d.read(r.context)).flatten()
 vv=np.concatenate([row[:n] for row,n in zip(vvalues,r.layers[0]['weights']['v'].item_counts)])
 expected=np.repeat(vv.reshape(8,128),4,axis=0).flatten()
 print('actual',actual[:16], 'expected',expected[:16],flush=True)
 print('pcc',np.corrcoef(actual,expected)[0,1], 'rmse',np.sqrt(np.mean((actual-expected)**2)),flush=True)
 assert np.isfinite(actual).all() and np.corrcoef(actual,expected)[0,1] > .99
finally:d.close()
