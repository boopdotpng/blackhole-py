# Decode bottlenecks and query reuse

Measured on the same eight-bank P150A as [the initial optimization](decode-performance.md).
The remaining gap to the bandwidth roof is substantially a kernel-organization
problem. The largest projections already approach peak DRAM bandwidth; repeated
scalar copies, small launches, padded tensors, and intermediate DRAM transfers
consume time with little useful arithmetic.

## Attribution

Times below are milliseconds per generated token, summing all 16 layers, before
the query-reuse change. Kernel estimates come from the difference between
24-copy and 8-copy resident traces, divided by 16. This removes fixed trace
overhead while retaining per-launch firmware costs. Full decode is measured
separately. The estimated sums agree with full decode to within about 1%.

| Work | Context 64 | Context 512 |
|---|---:|---:|
| Gate/up projections | 2.29 | 2.29 |
| Down projections | 1.25 | 1.25 |
| LM head | 1.05 | 1.05 |
| QKV and output projections | 1.06 | 1.06 |
| Attention | 0.71 | 3.42 |
| Norms, residuals, RoPE, cache append, SwiGLU, reassembly, argmax | 0.97 | 0.97 |
| Separately measured full decode | 7.39 | 10.10 |

The complete before/after measurements, including empty-launch controls, are in
[the diagnostic results](benchmarks/llama3_kernel_diagnosis.json).

## Disproportionate costs

**Attention was the largest avoidable cost, particularly as context grew.** At
context 64, QK and PV require about 8.39 million useful FLOPs across all layers,
versus 2.47 billion for the projections. Attention nevertheless consumed 0.71 ms.
It used only eight cores, computed full 32-row matmuls for four live query rows,
and copied two 2-KiB padded query tiles through scalar RISC-V loops on every
32-token KV block. Across the model, those query copies alone moved 512 KiB
at context 64 and 4 MiB at context 512 through scalar L1 load/store loops.

**Small stages pay repeated launch and layout costs.** There are 212 launches
per token. Resident empty launches cost about 2.4–3.6 µs, depending on core count,
suggesting roughly 0.6 ms of launch/reset work spread throughout the table.
This is already included in kernel times, not an extra additive category.
Firmware resets Tensix configuration and CB counters for every launch and clears
each TRISC register file. Python/trace/readback overhead is only tens of µs.

The MLP's 8,192 values occupy 117 full 1,024-element tiles in its compact
intermediate representation: about 14.6 times the logical element count.
SwiGLU processes these padded tiles and a separate kernel gathers the result
back into a dense vector. Residual adds and RoPE also gather/scatter small pieces
between oversized intermediate tiles. These stages are dominated by layout,
movement, synchronization, and setup rather than their arithmetic counts.

**Smaller projections have more headroom than the LM head.** QKV plus output
projections achieve approximately 315 GB/s of useful weight traffic. The
gate/up, down, and LM-head kernels reach roughly 467, 430, and 499 GB/s,
respectively. Optimizing the LM-head arithmetic further has little bandwidth
headroom at the same precision.

## Implemented follow-up: reuse Q across KV blocks

The query does not change while processing a token's KV history. The kernel now
initializes one two-tile query CB once, then republishes those immutable tiles
after the consumer releases them. Initial copies use an eight-word unrolled loop.
The attention arithmetic, BF16 values, and online-softmax order are unchanged.

| Fixed context | Attention per layer, before → after | Full decode, before → after |
|---|---:|---:|
| 32 | 32.28 → 29.09 µs | 7.201 → 7.146 ms |
| 64 | 44.38 → 30.94 µs | 7.386 → 7.174 ms |
| 128 | 68.64 → 34.13 µs | 7.777 → 7.226 ms |
| 512 | 213.56 → 53.58 µs | 10.096 → 7.537 ms |

The original attention slope was about 12 µs per additional 32-token block per
layer. Query reuse reduces it to about 1.6 µs. This controlled change establishes
that redundant data preparation, rather than necessary attention FLOPs, was the
dominant source of the old context-dependent slowdown.

End-to-end fixed-length generation over three prompts:

| Generated tokens per prompt | Before | After |
|---|---:|---:|
| 64, contexts 42–108 | 132.20 tok/s | 138.72 tok/s |
| 512, contexts 42–556 | 112.15 tok/s | 135.30 tok/s |

All 1,728 generated token IDs and sampled full BF16 logit buffers matched exactly
against the preceding optimized runtime. Samples include both sides of 32-token
block boundaries. Full-model CPU lowering/residency checks pass for seven-bank,
eight-bank 120-core, and eight-bank 140-core firmware topologies.
Raw generation results: [64 tokens](benchmarks/llama3_query_reuse_64.json),
[512 tokens](benchmarks/llama3_query_reuse_512.json).

## Does assigning more cores help?

The projections, SwiGLU, dense reassembly, and local argmax already use all 117
available workers. Their output shards need not be equal: for example, a
2,048-row projection assigns 18 rows to 59 workers and 17 rows to the other 58.
Those output rows are independent and require no cross-core dot-product sum.

Attention exposes additional independent query heads. An experiment assigned
the 32 query heads to 8, 16, or 32 workers, preserving a complete KV history
and complete softmax on each worker. No cross-core softmax merge was needed.

| Attention workers | Heads per worker | Context 64, µs/layer | Context 512, µs/layer |
|---|---:|---:|---:|
| 8 | 4 | 30.94 | 53.58 |
| 16 | 2 | 29.68 | 52.61 |
| 32 | 1 | 32.06 | 55.51 |

The 16-worker mapping barely changed whole-token latency; the 32-worker mapping
was slightly slower. The 32-worker variant passed a 64-token generation and
sampled-logit exact comparison, but short-context generation decreased from
138.75 to 138.20 tok/s. The runtime therefore retains eight attention workers.
[Raw core-scaling experiment results](benchmarks/llama3_attention_core_scaling.json).

The explanation is granularity: these mappings still execute complete 32-row
matmul tiles on each worker. Reducing the live rows from four to one does not
reduce that instruction stream, and independently processing the heads reads
their shared K/V data four times. More workers help when each worker actually
executes less work, not merely when its tile contains fewer live values.

Splitting the KV sequence is a different strategy: workers process disjoint
blocks, then merge their softmax states. This does shorten each worker's block
loop. Given local maximum `m_i`, exponential sum `l_i`, and unnormalized weighted
value sum `u_i`, the merge is:

```
m = max(m_i)
l = sum(exp(m_i - m) * l_i)
output = sum(exp(m_i - m) * u_i) / l
```

That requires a reduction and synchronization, but not equal shard lengths.
The merge needs numerical validation because it changes floating-point
association. It is more attractive at long contexts, where savings in the
block loop can amortize the merge and launch costs. For RMSNorm's 2,048-element
vector, an analogous sum-of-squares reduction is possible, but communication
can cost more than the existing roughly 5.5-µs single-core kernel.

## Next targets

1. Fuse gate/up's epilogue with SwiGLU and emit the downstream activation layout
   directly, removing padded intermediate transfers and dense reassembly.
2. Fuse residual/RMSNorm and QKV/RoPE/cache stages where ownership permits;
   preserve activations in L1 across stages to remove DRAM round trips and resets.
3. Specialize attention's four-row matrix work and retained unpack/pack state.
   At longer contexts, consider distributing KV blocks across more cores with a
   numerically validated partial-softmax merge.
4. Improve small-projection occupancy and overlap, rather than prioritizing the
   already bandwidth-saturated LM head.

Current projection time alone is about 5.65 ms/token, so even eliminating every
other stage would cap the current projections at about 177 tok/s. The BF16
weight-only 512-GB/s ceiling is about 207 tok/s. Reaching 150–160 tok/s requires
removing another roughly 0.5–1.0 ms from short-context decode; these are useful
optimization targets, not measured promises. Approaching 200 tok/s requires
both near-ideal projections and very little time outside them.

```sh
PYTHONPATH=. python3 examples/profile_llama3.py --contexts 32 64 128 512 --output profile.json
PYTHONPATH=. python3 examples/benchmark_llama3.py --steps 512 --output generation.json
```
