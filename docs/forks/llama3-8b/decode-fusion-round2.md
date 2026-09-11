# Decode fusion, round two

Measured September 7, 2026 on **card 0**, an eight-bank P150A with 117 worker
cores. Llama 3.2 1B Instruct, batch one, original BF16 weights and HiFi2
projection arithmetic. The starting point is the uncommitted query-reuse
runtime described in [the previous bottleneck report](decode-bottlenecks.md).

The default now uses **83 launches per token**, down from 212, and **16 attention
workers**, up from eight. Short-context generation reaches approximately
**152.3 tok/s**, compared with 139 tok/s before this round. The 200-tok/s target
has not been reached.

## Results and validation

The benchmark times complete `decode()` calls, including trace submission and
token readback. Weight loading, prompt ingestion, text streaming, and diagnostic
logit reads are excluded. Generation continues through EOS for a fixed number
of steps. Reference and candidate run sequentially on card 0.

| Workload | Before | After |
|---|---:|---:|
| Three prompts, 64 generated tokens each, contexts 42–108 | 139.1 tok/s | 152.3 tok/s |
| Three prompts, 512 generated tokens each, contexts 42–556 | 135.6 tok/s | 148.2 tok/s |
| Resident launches per token | 212 | 83 |

The final 64- and 512-token-per-prompt comparisons matched all **1,728 generated
token IDs** and sampled complete BF16 logit buffers exactly. Samples cover the first and last
steps and both sides of every 32-token attention-block boundary. Short-context
comparisons also passed at eight, 16, and 32 attention workers.

CPU checks lower and install the full model for all nine combinations of
seven-bank/117-worker, eight-bank/117-worker, and eight-bank/137-worker storage
topologies with eight, 16, or 32 attention workers. They check the 83-launch
budget, worker mapping, resident kernel/template capacity, and transient L1
capacity. Only card 0's eight-bank/117-worker topology was measured on hardware.

Final raw results:

- [Short-context generation](benchmarks/llama3_round2_final_64.json)
- [512-token generation](benchmarks/llama3_round2_final_512.json)
- [Fixed-context kernel attribution](benchmarks/llama3_round2_final_profile.json)

## Five launches per layer

| Launch | Work |
|---|---|
| QKV | Each projection core computes RMSNorm, keeps its rounded BF16 token in L1, then computes Q/K/V. |
| Attention | Each worker gathers and rotates its query heads and key together, appends K/V, and performs streaming attention. |
| Output | Output projection, BF16 residual add, and direct dense scatter. |
| Gate/up | Local RMSNorm, gate/up projections, SwiGLU, and direct dense scatter into the down-projection layout. |
| Down | Down projection, BF16 residual add, and direct dense scatter. |

Sixteen layers account for 80 launches. Embedding, fused final RMSNorm/LM head,
and argmax/token publication account for the remaining three.

The MLP no longer writes gate/up/hidden padded intermediates to DRAM or launches
a separate gather to reconstruct the dense activation. Residual adds retain the
original BF16 destination arithmetic: switching them to FP32 changed the
reference rounding. Dense scatter preserves the source/destination NoC byte
alignment and writes only each core's owned feature range, including uneven
shard boundaries.

The fused attention kernel rotates multiple heads in different rows of the
same tile. It retains queries in local L1 and waits for acknowledged cache writes
before reading K/V. At 16/32 workers, workers sharing a KV head write identical
cache bytes; each waits for its own writes. There is no cross-worker softmax
reduction and no change in each query's KV-block reduction order. The complete
SFPU softmax footprint is retained because its chunks span column faces as
well as row pairs.

Scalar packing keeps invariant configuration outside the projection row loop.
Scratch clearing uses eight stores per iteration, and fused attention omits
query scratch that its local path does not use. The resident program arena is
expanded from `0x12000..0x42000` to `0x12000..0x62000` to accommodate fused variants;
transient buffers begin after it and are checked against the remaining L1.

## Experiments

| Cumulative change | Launches/token | Short-context tok/s |
|---|---:|---:|
| Starting runtime | 212 | 139.1 |
| Fused gate/up, SwiGLU, dense scatter | 180 | 143.0 |
| Fused output/down residual epilogues | 148 | 144.2 |
| Fused norms and RoPE/cache append | 99 | 147.1 |
| Grouped RoPE/cache/attention, eight workers | 83 | 145.7 |
| Remove unused scratch clears and unroll remaining clears | 83 | 149.9 |
| Two query heads per worker, 16 attention workers | 83 | 152.3 |
| One query head per worker, 32 attention workers | 83 | 152.3 |

Reducing launches alone initially made the 83-launch version slower than the
99-launch version. Eliminating redundant clears and spreading local gathering
across more workers made the fused path faster. Thirty-two attention workers
provided no further improvement, so the default is 16. The projections still
use all 117 workers; this experiment divides query heads, not the KV sequence.

A four-row batched weight-reader experiment failed exact comparison and did not
improve measured throughput; it was reverted. It is not part of the runtime.

## Remaining gap

The model reads approximately 2.471 GB of projection weights per token. At the
supplied 512-GB/s peak, the weight-only ceiling is approximately 207 tok/s.
152.3 tok/s corresponds to about 376 GB/s of useful weight traffic, before
activation, KV-cache, padding, and command traffic.

At context 64, fused projection kernels occupy approximately **5.98 ms** of the
**6.53-ms** device/CQ decode interval. These estimates include their fused norms
and epilogues. The isolated-kernel sum is within 0.5% of complete decode.

| Fused stage, summed across layers | ms/token at context 64 |
|---|---:|
| Gate/up, RMSNorm, SwiGLU, dense scatter | 2.419 |
| Down and residual | 1.310 |
| Final RMSNorm and LM head | 1.057 |
| RMSNorm and QKV | 0.670 |
| Output projection and residual | 0.523 |
| RoPE, cache append, and attention | 0.482 |
| Embedding and argmax | 0.041 |

Most remaining time is inside the fused projections. Removing more small
launches is insufficient to reach 200 tok/s. The next substantial target is the
projection microkernel and weight layout, especially the smaller QKV/output
matrices. A matrix-oriented GEMV layout could compute several output rows
without repeatedly performing a full-tile scalar reduction, but would require
new weight packing and numerical validation. Splitting KV blocks across cores
is a separate longer-context optimization and would require a softmax merge.

## Reproduce

```sh
PYTHONPATH=. python3 examples/benchmark_llama3.py \
  --device 0 --attention-cores 16 --steps 64 --output short.json
PYTHONPATH=. python3 examples/benchmark_llama3.py \
  --device 0 --attention-cores 16 --steps 512 --output long.json
PYTHONPATH=. python3 examples/profile_llama3.py \
  --device 0 --attention-cores 16 --contexts 32 64 128 512 --output profile.json
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

The baseline was already uncommitted when this round started. Reconstruct its
inference source from the original commit and saved patch, then compare using
the current shared runtime modules:

```sh
git show cce3e77f3a245dadfaa4a29ae3a0dda499b53708:examples/llama3.py > /tmp/llama3-round2-reference.py
patch /tmp/llama3-round2-reference.py < benchmarks/llama3_round2_reference.patch
PYTHONPATH=. python3 examples/benchmark_llama3.py \
  --device 0 --attention-cores 16 --steps 64 \
  --reference /tmp/llama3-round2-reference.py --output comparison.json
```

Use `--attention-cores 8` or `32` to reproduce the core-scaling alternatives.
The same option is available in `examples/llama3.py` and on `Llama3Decode`.
