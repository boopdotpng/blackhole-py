"""Trace one Llama 3 8B decode layer through tinygrad on the NULL device (nothing computes) and list where the
multi-device machinery puts cross-shard communication. Cores are modelled as sharded devices.

  DEV=NULL PYTHONPATH=../tinygrad SHARD_KVCACHE=1 python3.14 trace/llama_sync.py [megatron|output]"""
import sys
from collections import Counter
from tinygrad import Tensor, Device, dtypes
from tinygrad.uop.ops import Ops
from extra.models.llama import TransformerBlock, precompute_freqs_cis

N = 8  # shards; must divide the 8 KV heads. Sync points don't depend on N.
DIM, HIDDEN, HEADS, KV_HEADS, CTX = 4096, 14336, 32, 8, 1024
plan = sys.argv[1] if len(sys.argv) > 1 else "megatron"
# device chosen by DEV=NULL in the environment
devs = tuple(f"NULL:{i}" for i in range(N))

blk = TransformerBlock(DIM, HIDDEN, HEADS, KV_HEADS, 1e-5, CTX)
a, f = blk.attention, blk.feed_forward
row = 1 if plan == "megatron" else 0          # megatron: o and down shard their input axis (partial sums)
for lin, ax in ((a.wq, 0), (a.wk, 0), (a.wv, 0), (a.wo, row), (f.w1, 0), (f.w3, 0), (f.w2, row)):
  lin.weight = Tensor.empty(*lin.weight.shape, dtype=dtypes.bfloat16).shard(devs, ax)
for norm in (blk.attention_norm, blk.ffn_norm): norm.weight = Tensor.empty(DIM, dtype=dtypes.bfloat16).shard(devs)

pos = 100
freqs = precompute_freqs_cis(DIM // HEADS, CTX * 2).cast(dtypes.bfloat16).shard(devs)[:, pos:pos+1]
x = Tensor.empty(1, 1, DIM, dtype=dtypes.bfloat16).shard(devs)
Tensor.realize(x, freqs, *[l.weight for l in (a.wq, a.wk, a.wv, a.wo, f.w1, f.w3, f.w2, blk.attention_norm, blk.ffn_norm)])
blk(x, pos, freqs, None)  # first call creates and realizes the KV cache
out = blk(x, pos, freqs, None)

print(f"plan={plan}: graph ops", {k.name: v for k, v in Counter(u.op for u in out.uop.toposort()).items()
                                  if k in (Ops.ALLREDUCE, Ops.COPY, Ops.MSELECT, Ops.MSTACK)})
for u in out.uop.toposort():
  if u.op is Ops.ALLREDUCE: print("  ALLREDUCE", u.arg, u.shape)
  if u.op is Ops.COPY: print("  COPY", u.shape, u.src[0].device if hasattr(u.src[0], "device") else "")

# The multi rewrite (sharded ops -> per-shard ops + ALLREDUCE / copies) runs while scheduling.
lin = out.schedule_linear()
print(f"schedule: {len(lin.src)} items")
def shape(u):
  try: return "x".join(map(str, u.shape)) or "1"
  except Exception: return "?"
def kernel(call):
  ast, args = call.src[0], call.src[1:]
  red = sum(u.op is Ops.REDUCE for u in ast.toposort())
  return f"kernel ({red} reduce): " + ", ".join(shape(a) for a in args)
runs = []
for item in lin.src:
  call = item.src[0] if item.src else item
  key = "copy" if call.op is Ops.STORE else kernel(item)
  if runs and runs[-1][0] == key == "copy": runs[-1][1] += 1
  else: runs.append([key, 1])
for k, n in runs: print(f"  {n:3d} x {k}")
