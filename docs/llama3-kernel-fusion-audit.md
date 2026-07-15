# Llama 3 Kernel and Fusion Audit

Date: 2026-07-14

## Scope

This audit covers the current working tree in
`/home/boop/tenstorrent/blackhole-py`, including its uncommitted and untracked
Llama 3 files. The target is the hardcoded Llama 3.2 1B configuration:

| Property | Value |
|---|---:|
| Batch | 1 |
| Hidden size | 2048 |
| Layers | 16 |
| Query heads | 32 |
| KV heads | 8 |
| Head dimension | 64 |
| MLP dimension | 8192 |
| Vocabulary | 128256 |
| Maximum cache length | 8192 |
| Weight/cache storage | BF16 |

The live implementation is in `examples/llama3`. It does not dispatch TTNN or
TT-Metal model operators. Its matmuls and Llama-specific operators are programs
built by this repository's Python assembler.

Hardware measurements in this document were submitted through
`tt-device-queue`. They are one-shot command-queue timestamps, not statistical
benchmark distributions, so they should be used for prioritization rather than
as final performance claims.

## Executive Summary

The current decode layer has 17 logical operators and 19 physical Program
invocations. Gate and up projections each split into two Programs. A complete
device-controlled decode step has about 310 physical Program invocations:

```text
embedding
+ 16 * 19 layer Programs
+ final RMSNorm
+ 2 LM-head chunks
+ argmax
+ position increment
= 310 Programs
```

The most important conclusions are:

1. **True prefill is the largest overall opportunity.** Current prefill runs the
   `S=1` decode block once per prompt token. It gives up matrix-matrix
   utilization and performs quadratic attention as many tiny launches. No
   amount of local decode fusion will recover that loss.
2. **MLP matmuls dominate short-context decode.** At `T=1`, projection matmuls
   in the MLP consume 4.018 ms of a 4.836 ms layer, or 83%. Planner and kernel
   improvements matter more than merely combining gate/up launch submission.
3. **Attention dominates long-context decode.** Score, softmax, and value stages
   grow from 85.6 us at `T=1` to 11.352 ms at `T=8192`. A score + online softmax
   + weighted-V kernel is the right long-term fusion, but optimizing the
   K-cache transpose in the score reader remains necessary.
4. **LM head + argmax is the best isolated fusion.** The current path writes a
   physically tiled full-vocabulary BF16 logits tensor, then spends 596 us
   scanning it. Emit an FP32 local `(max, index)` from each LM-head shard and
   reduce only those pairs.
5. **Projection + residual epilogues are low risk and measurable, but small.**
   The two standalone residual Programs total about 31 us per layer, or about
   0.50 ms across 16 layers at short context.
6. **Several intended fusions already exist.** K RoPE is fused with K/V cache
   append; score scale and tail masking are fused; GQA repetition is only an
   address mapping; SwiGLU is fused; RMSNorm and softmax each perform their
   internal passes within one Program.
7. **Trace replay is not kernel fusion.** It removes host dispatch work while
   preserving every Program boundary and all intermediate DRAM traffic.

## Current Execution Path

### One Transformer Layer

`examples/llama3/block.py:39-149` composes the layer in this order:

| # | Program name | Operation | Physical output |
|---:|---|---|---|
| 1 | `llama3_rmsnorm` | Input RMSNorm | BF16 `(32, 2048)` |
| 2 | `attn_q_proj` | Q projection | BF16 `(32, 2048)` |
| 3 | `attn_k_proj` | K projection | BF16 `(32, 512)` |
| 4 | `attn_v_proj` | V projection | BF16 `(32, 512)` |
| 5 | `llama3_rope` | Q RoPE | BF16 `(32, 2048)` |
| 6 | `llama3_rope_kv_store` | K RoPE and K/V append | raw K/V cache plus K mirror |
| 7 | `llama3_attention_scores_stream` | GQA QK, scale, tail mask | FP32 `(32, padded_T)` |
| 8 | `llama3_softmax_stream` | Three-pass softmax | BF16 `(32, padded_T)` |
| 9 | `llama3_attention_values_stream` | GQA probabilities times V | BF16 `(32, 2048)` |
| 10 | `attn_o_proj` | Attention output projection | BF16 `(32, 2048)` |
| 11 | `llama3_residual_add` | Attention residual | BF16 `(32, 2048)` |
| 12 | `llama3_rmsnorm` | Post-attention RMSNorm | BF16 `(32, 2048)` |
| 13 | `mlp_gate_chunk0/1` | Gate projection | BF16 `(32, 8192)` |
| 14 | `mlp_up_chunk0/1` | Up projection | BF16 `(32, 8192)` |
| 15 | `llama3_swiglu_fused` | `silu(gate) * up` | BF16 `(32, 8192)` |
| 16 | `mlp_down` | Down projection | BF16 `(32, 2048)` |
| 17 | `llama3_residual_add` | MLP residual | BF16 `(32, 2048)` |

The logical token count is one, but a token activation occupies at least one
full 32-row tile band. This makes intermediates larger than their logical
vectors. Examples include 128 KiB for `(32, 2048)` BF16 and 512 KiB for
`(32, 8192)` BF16.

### Decode

The default path captured by `SequentialModel.capture_decode_trace` at
`examples/llama3/model.py:731-757` is:

```text
device token id
  -> embedding gather
  -> 19 physical Programs per layer * 16 layers
  -> final RMSNorm
  -> LM-head chunk 0
  -> LM-head chunk 1
  -> BF16 argmax
  -> position increment
  -> host reads one uint32 token id
```

Weights and KV caches for all layers are resident. Activations and most scratch
buffers are shared between layers. Each layer has a separate K/V cache.

### Prefill

There is no multi-token prefill attention kernel. The module-level comment in
`examples/llama3/model.py:2-12` states that prefill is sequential `S=1` decode.

The default layer-major traced path executes, per layer and prompt token:

```text
dynamic sequence-row load
  -> 19 physical layer Programs
  -> dynamic sequence-row store
  -> decode-position increment
```

That is 22 physical Programs per layer-token, or 352 Program executions per
prompt token across 16 layers, excluding the initial embedding and final row
copy. Trace replay reduces host submission cost but does not reduce this device
work.

## Existing Fusions

### K RoPE + K/V Cache Append

`llama3_rope_kv_store` rotates K and appends rotated K and raw V into the
persistent caches in one Program. There is no standalone cache-store Program.
See `examples/llama3/attn.py:773-835` and `:980-1135`.

The Program still writes a contiguous rotated-K mirror for bring-up validation.
The score kernel reads the cache, not this mirror.

### Score Scale + Tail Mask

`llama3_attention_scores_stream` applies the fixed `1/sqrt(64) = 0.125` scale
and writes FP32 `-inf` into columns beyond logical `T`. Decode therefore has no
separate scale or mask Program. See `examples/llama3/attn.py:1339-1455`.

### Logical GQA

K and V heads are not physically repeated. The score and value readers map
query head `h` to KV head `h // 4`. This is preferable to a GQA-repeat fusion
because there is no repeated tensor to eliminate.

### Fused SwiGLU

`llama3_swiglu_fused` computes `silu(gate) * up` without storing a SiLU
intermediate. Gate and up projection outputs and the final hidden output are
still materialized in DRAM. See `examples/llama3/swiglu.py:1-11`.

### Internal Multi-Pass Programs

RMSNorm's reduction, rsqrt, normalization, and gamma multiplication are one
Program. Softmax's max, exp/sum, and normalize passes are also one Program.
They are internally staged but do not incur separate command-queue launches.

### Device Argmax Reduction

Argmax already performs local scans and a NOC reduction of local winners. The
remaining problem is its boundary with LM-head output materialization, not its
global reduction structure. See `examples/llama3/argmax.py:103-271`.

## Hardware Results

Commands were queued from `/home/boop/tenstorrent/blackhole-py`:

```sh
python3 examples/llama3/block.py --run --pos 0
python3 examples/llama3/block.py --run --pos 1023
python3 examples/llama3/block.py --run --pos 8191
python3 examples/llama3/model.py --run --prompt-token-limit 1 \
  --max-new-tokens 2 --num-layers 16
```

Queue job IDs were `b4d4ac43`, `e9c8af36`, `703d3b2d`, and `154cb14d`.
The final-token-selection probe was job `65580fd9`.

### Per-Layer Timings

All values are microseconds. `T` includes the current token.

| Program | T=1 | T=1024 | T=8192 |
|---|---:|---:|---:|
| Input RMSNorm | 96.675 | 96.739 | 96.547 |
| Q projection | 149.799 | 149.853 | 150.192 |
| K projection | 47.427 | 47.499 | 47.383 |
| V projection | 47.335 | 47.313 | 47.405 |
| Q RoPE | 16.341 | 16.396 | 16.673 |
| K RoPE + KV store | 19.259 | 13.379 | 13.527 |
| Attention scores | 44.348 | 958.535 | 7553.156 |
| Softmax | 13.531 | 57.808 | 409.882 |
| Attention values | 27.681 | 436.476 | 3388.828 |
| Output projection | 149.111 | 150.277 | 149.650 |
| Attention residual | 15.836 | 15.572 | 15.594 |
| Post-attention RMSNorm | 96.265 | 96.299 | 96.790 |
| Gate chunk 0 | 869.347 | 869.289 | 868.788 |
| Gate chunk 1 | 869.264 | 868.279 | 868.286 |
| Up chunk 0 | 867.793 | 868.356 | 868.379 |
| Up chunk 1 | 869.058 | 868.096 | 868.406 |
| SwiGLU | 79.041 | 76.373 | 76.215 |
| Down projection | 542.110 | 538.755 | 540.923 |
| MLP residual | 15.377 | 15.519 | 15.731 |
| **Layer total** | **4835.598** | **6190.813** | **16092.355** |

The layer-0 checkpoint correctness check at `T=1` passed with PCC `0.999960`
and relative L2 `0.071329`.

### Timing Breakdown

At `T=1`:

| Group | Time | Layer share |
|---|---:|---:|
| Gate, up, and down projections | 4.018 ms | 83.1% |
| Full MLP including SwiGLU and residual | 4.112 ms | 85.0% |
| Two RMSNorms | 0.193 ms | 4.0% |
| Attention path including projections and RoPE | about 0.515 ms | 10.6% |
| Two residual Programs | 0.031 ms | 0.6% |

At `T=8192`, score + softmax + value alone consume 11.352 ms, or 70.5% of
the entire layer. The score Program is the largest component at 7.553 ms.

### Final Token Selection

A separate queued one-layer model probe measured:

| Program | Time |
|---|---:|
| Embedding gather | 18.879 us |
| Final RMSNorm | 96.237 us |
| LM-head chunk 0 | 2776.935 us |
| LM-head chunk 1 | 2764.604 us |
| BF16 argmax | 596.265 us |
| **Final RMSNorm + LM head + argmax** | **6234.041 us** |

Static DRAM row copies measured between 13.939 and 18.391 us.

The full 16-layer two-token smoke test reported 23.30 tok/s. That number is not
steady-state decode throughput: `model.py` computes the first generated token
before `generation_start`, then divides two output tokens by a timer containing
only one decode replay (`examples/llama3/model.py:895-949`). The replay took
about 90 ms, which is consistent with the sum of 16 short-context layers plus
the final token-selection path. Fix the metric by either starting the timer
before the first greedy-token call or dividing by the number of timed decode
steps.

### Kernel-Time Decode Model

Using layer 0 as representative and excluding host overhead gives these rough
steady-state lower-bound estimates:

| Context | 16 layers + final token selection | Approximate rate |
|---|---:|---:|
| T=1 | 83.6 ms | 12.0 tok/s |
| T=1024 | 105.3 ms | 9.5 tok/s |
| T=8192 | 263.7 ms | 3.8 tok/s |

These are projections from one-shot kernel timestamps, not end-to-end benchmark
results.

## Prioritized Fusion Work

### P0: Implement True Multi-Token Prefill

This is larger than a local fusion but has the highest payoff. Replace repeated
decode with a tiled prefill path:

1. Run RMSNorm and projections over prompt tiles instead of one token at a time.
2. Use matrix-matrix QKV, output, gate/up, and down projections.
3. Implement causal tiled SDPA or flash attention over prompt blocks.
4. Write K/V cache blocks in the final decode cache layout.
5. Run the LM head only for the final prompt row.

Current prefill pays 352 physical layer Program executions per prompt token and
uses GEMV-like `M=1` matmuls. This architectural issue dominates all smaller
fusion opportunities. The embedding path's current 1024-token limit also needs
to be reconciled with the 8192-token cache target.

### P1: Improve MLP Matmuls Before Packing More Work Into One Program

Short-context decode is an MLP matmul problem. Gate and up consume 3.475 ms per
layer and down consumes another 0.542 ms. The normalized activation is only
4 KiB logically, while gate/up weights total about 64 MiB per layer. Sharing the
activation read alone cannot yield a large speedup.

First profile and tune `matmul_peak.py` for exact Llama shapes:

| Projection | Logical shape | Current Programs |
|---|---|---:|
| Gate | `1x2048 @ 2048x8192` | 2 |
| Up | `1x2048 @ 2048x8192` | 2 |
| Down | `1x8192 @ 8192x2048` | 1 |

Investigate output chunk planning, core partitioning, DRAM bank utilization,
reader stalls, and pack/write overlap. A 10% MLP projection improvement is worth
about 6.4 ms per 16-layer token, much more than all standalone residual launches.

After that, consider a gate/up + SwiGLU producer-consumer Program. A useful
fusion must do more than concatenate gate and up weights. It should avoid the
two 512 KiB projection-output round trips and the 512 KiB hidden write where
possible. Removing only the standalone SwiGLU Program has a measured ceiling of
about 76-79 us per layer, or 1.2 ms per token.

### P2: Fuse LM Head + FP32 Partial Argmax

Current boundary:

```text
LM-head chunk 0 -> BF16 tiled logits
LM-head chunk 1 -> BF16 tiled logits
BF16 argmax scans full logical vocabulary
```

Target:

```text
each LM-head output shard keeps FP32 local max and vocabulary index
  -> one global reduction of shard winners
  -> one uint32 token id
```

Benefits:

- Eliminate the measured 596 us standalone argmax Program.
- Avoid writing and rereading the physically tiled full-vocabulary logits
  buffer, roughly 8 MiB at 32 padded rows.
- Compare FP32 accumulator values rather than rounded BF16 logits.
- Resolve the mismatch with `kernel_list.md:68-69`, which specifies FP32 logit
  comparison.

The current generic matmul has an `output_tile_hook`, but it runs after the NOC
write at `examples/matmul_peak.py:2046-2048`. The useful implementation needs a
TRISC/packer epilogue or a writer path that extracts local maxima before the
full-logit write.

### P3: Add Projection + Residual Epilogues

Targets:

```text
attention output projection + x residual
MLP down projection + post-attention residual
```

The direct measured ceiling from deleting both residual Programs is about
31 us per layer, or 0.50 ms per 16-layer token. Additional benefit comes from
avoiding two 128 KiB projection-output writes and rereads per layer.

The add should happen in FP32 destination/epilogue state before BF16 packing if
the matmul path supports it. The existing NCRISC `output_tile_hook` cannot
perform a BF16 vector add and currently runs after output is already written, so
this requires a real compute epilogue rather than a callback-only change.

### P4: Fuse Score + Online Softmax, Then Weighted V

The current attention boundary materializes:

- FP32 scores: `(32, padded_T)`.
- FP32 softmax numerators: `(32, padded_T)`.
- BF16 probabilities: `(32, padded_T)`.

A staged implementation path is:

1. Fuse score production with online max/sum and emit only BF16 probabilities.
2. Once correct, accumulate weighted V in the same page loop and emit only the
   final 32 head vectors.

The eight score cores and eight softmax/value cores already use compatible
one-KV-head-per-core ownership. The fused decode loop can read one K page and
one V page, compute four query-head score rows, update online softmax state, and
update four 64-element output accumulators.

The measured standalone softmax ceiling is 13.5 us per layer at `T=1`, 57.8 us
at `T=1024`, and 409.9 us at `T=8192`. Avoided score, numerator, and probability
DRAM traffic adds to that benefit. The score and weighted-V dot products remain,
so fusion alone does not remove the 7.553 ms score or 3.389 ms value compute at
`T=8192`.

In parallel, optimize the score reader's row-major K-cache transpose. It is the
largest single long-context kernel and remains on the critical path after
attention fusion.

### P5: Fuse Q RoPE Into the Score Reader

Q RoPE is immediately consumed by the score Program. Apply the half-split
rotation while the score reader gathers Q, and remove `q_rope` materialization.

The direct launch saving is about 16 us per layer, or 0.26 ms across 16 layers.
It also removes one 128 KiB output and reread per layer. This is structurally
simpler than RMSNorm/projection fusion because Q is invariant across all cache
pages in a decode step.

### P6: Remove the Rotated-K Bring-Up Mirror

`llama3_rope_kv_store` writes rotated K to both the actual K cache and
`k_rope_buf`. The latter has no live model consumer. Remove its allocation,
writer arguments, full-tile NOC writes, and barriers from the model path while
retaining an optional validation mode for the standalone attention test.

This is a low-risk bandwidth cleanup rather than a Program-count reduction.

### P7: Fold Small Control and Staging Programs Into Their Neighbors

Useful cleanups after larger work:

| Current boundary | Fusion target |
|---|---|
| Dynamic prefill row load -> RMSNorm | RMSNorm reads the selected sequence row |
| Final residual -> dynamic row store | Residual writes the selected sequence row |
| Dynamic row store -> position increment | Store Program increments control word |
| Argmax -> decode position increment | Token writer increments control word |
| Prompt select -> embedding | Embedding indexes prompt IDs using device position |

Static row copies cost about 14-18 us each. These changes reduce launch count but
do not address sequential prefill's fundamental utilization problem. Prompt
select is only used by a debug token-major prefill path, not the default traced
path.

## Fusions to Defer

### Q/K/V as One Launch

Q, K, and V reread the same 4 KiB logical activation, but consume about 12 MiB of
weights per layer. Packing them as one `2048x3072` projection can reduce Program
count from three to one, but shared activation traffic is too small to promise a
large kernel-time improvement. Do this only if the packed shape produces a
better matmul plan or enables direct Q RoPE/KV-store consumers.

### Gate/Up as One Launch Without SwiGLU Streaming

A packed `2048x16384` projection reads the same amount of weight data and likely
retains four output chunks. If it still writes both complete outputs before a
separate SwiGLU Program, it is mostly launch consolidation rather than useful
fusion.

### RMSNorm + Projection

The current RMSNorm is a one-core, multi-pass row reduction; projections are
multicore matmuls. Fusing them requires broadcasting the computed scale/gamma
state into a differently partitioned reader. First optimize or parallelize
RMSNorm and establish a reliable collective. The measured 96 us norm is real,
but this boundary is much harder than a projection epilogue.

### Whole Transformer Block

Do not fuse the whole layer. Weight streaming, distinct core ownership, cache
updates, reductions, and L1 capacity make that a brittle mega-Program. Preserve
clear fusion boundaries around matmul epilogues and attention page loops.

## Correctness and Performance Gaps

### BF16 Logits Instead of FP32 Shard Maxima

The live LM head writes BF16 logits and argmax scans BF16 values. This can select
a different token when close FP32 logits round to the same BF16 value. LM-head
partial argmax should compare FP32 accumulator results and preserve the lowest
vocabulary index on ties.

### No True Prefill Mask Path

There is no live causal-mask Program because prompt tokens are processed one at
a time and only past/current cache entries exist. A real tiled prefill path must
introduce causal predicates inside score/softmax or flash attention.

### Embedding Length Mismatch

The cache and RoPE support 8192 positions, while embedding gather accepts at
most 1024 token IDs (`examples/llama3/embedding.py:21-33` and
`examples/llama3/model.py:320-327`).

### Decode Throughput Accounting

The first next-token calculation occurs before the decode timer. Report timed
decode steps, not emitted token count, or include the initial greedy-token stage
inside the timer.

### Prefill Timing Includes Setup

The current top-level prefill timer includes first-time layer weight uploads,
Program construction/capture, and replay. Report these separately from steady
device execution. The one-token smoke test took 20.86 seconds of prefill wall
time even though one layer's measured device kernels total only about 4.8 ms.

## Recommended Implementation Order

1. Correct decode and prefill performance accounting and add repeated hardware
   measurements with median and percentile output.
2. Profile and tune the exact MLP and LM-head matmul shapes using existing phase
   counters in `matmul_peak.py`.
3. Fuse LM-head shard maxima with FP32 argmax reduction.
4. Add output-projection and down-projection residual epilogues.
5. Remove the K mirror and fold Q RoPE into the score reader.
6. Implement score + online softmax, then extend it to weighted V.
7. Optimize the long-context K-cache transpose and attention page pipeline.
8. Build a real tiled prefill path; do not optimize sequential prefill beyond
   inexpensive staging cleanup.
9. Revisit gate/up + SwiGLU streaming only after matmul phase data shows the
   remaining output traffic is material.
10. Defer RMSNorm/projection and larger layer fusions until the smaller
    boundaries are measured and stable.

## Validation Requirements

Every fusion should retain or add these checks:

| Fusion | Required validation |
|---|---|
| LM head + argmax | Compare token ID to host FP32 argmax; test exact ties across shards |
| Projection + residual | PCC/relative-L2 against current block at multiple layers |
| Q RoPE + score | Score PCC at positions 0, 31, 32, 1023, and 8191 |
| Score + online softmax | Row sums, masked-tail zero, max-abs and relative-L2 across all page boundaries |
| Softmax + weighted V | Attention-output PCC with dense and sparse/random cache histories |
| Gate/up + SwiGLU | PCC around large positive/negative gate values and BF16 rounding boundaries |
| True prefill | Token logits/cache equality against sequential prefill for short prompts, then long-prompt quality tests |

Use `tt-device-queue` for all Blackhole runs. At minimum, benchmark `T=1`,
`T=32`, `T=33`, `T=1024`, and `T=8192`, because attention behavior changes at
32-token page boundaries.
