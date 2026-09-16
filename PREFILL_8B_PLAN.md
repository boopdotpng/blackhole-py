# Llama 3 8B BF16 / FP8 prefill

Design and optimization backlog, based on the current code as inspected on
2026-09-15. This is a proposed implementation, not a measured speedup or a
claim that the existing prefill path passes end-to-end correctness.

## Current path

- `examples/llama3.py:Prefill` accepts chunks of 1–8 tokens, BF16 only.
- `prefill_projections` shares streamed weights across tokens for QKV and
  gate/up. `_projection_dot_math` still uses elementwise multiplication and
  reductions for independent dot products, not sequence-by-weight GEMM.
- RMSNorm is repeated per token on each projection worker.
- Attention, O, SwiGLU, and down still launch separately for every token.
- `Prefill.run` submits and waits once per layer per chunk. Decode already
  has a replayable trace; prefill has a host-driven queue loop.
- `SequenceBuffer` preserves decode's padded token slabs and compact outputs.
  This is convenient for compatibility but is not the desired GEMM layout.
- The chat README says prompts currently use decode, not this prefill path.

Keep the current path as a comparison baseline. Build a separate tiled prefill
pipeline and hand its KV cache and final token to the existing decode runtime.

## Model and layout contract

Batch one initially. 32 layers, hidden size 4096, MLP size 14336, 32 query heads,
8 KV heads, head dimension 128, vocabulary 128256. Let M be the live query
tokens in a chunk and P the already-cached prefix length.

- Residual stream: BF16 `[M,4096]`, stored in 32x32 tiles with documented
  sharding and face order. Keep a separate residual from normalized operands.
- GEMM convention: `[M,K] @ [K,N]`. Checkpoints store projections `[N,K]`;
  transpose/tilize once during preparation or implement a measured tiled
  transpose reader. Do not transform full weights each prompt.
- Attention Q: logically `[32,M,128]`; K/V: `[8,P+M,128]`. Preserve the current
  decode cache's head, 32-token block, feature-tile, and face ordering.
- Full cache blocks use tile writes; partial blocks use masked row writes that
  preserve old prefix rows. Do not physically repeat K/V four times for GQA.
- Every kernel accepts valid rows and an absolute position. Padded rows must
  not enter attention, update cache, or determine the final output token.
- Initial prompt starts at P=0. An extension API must preserve prior cache and
  token history; current `load_tokens` resets history and is not that API.
- Account for resident decode weights, prepacked prefill weights, scratch,
  command records, and KV together before selecting a weight-storage scheme.
  BF16 KV at the current 8192-token capacity costs 1 GiB across 32 layers.
  Do not assume a second complete BF16 weight copy fits. Alternatives include
  a bounded tiled-weight cache or a reader that tilizes streamed weight blocks;
  include their conversion traffic in timing. Avoid changing decode's hot path.

## Kernel inventory

These are logical stages; fusion is conditional on measured latency and L1/Dst
capacity. A single parameterized GEMM family should serve all projection shapes.

| Stage | Logical operation | Implementation / optimization target |
|---|---|---|
| Embedding + tilize | IDs -> `[M,4096]` | Gather multiple tokens per launch and directly produce sequence tiles. |
| RMSNorm + optional quantize | `[M,4096]` | FP32 sum of squares; BF16 residual preserved. Normalize once per row; FP8 mode applies calibrated input scale and E4M3 conversion. |
| Grouped QKV GEMM | `[M,4096] @ [4096,6144]` | Share A across Q/K/V; independent output scales; emit head-friendly tiles. Logical concatenation need not require a contiguous combined weight allocation. |
| RoPE + KV write | Q `[M,4096]`, K/V `[M,1024]` each | Rotate Q/K with absolute positions; write K/V in decode-compatible layout; batch full-tile writes. V is not rotated. |
| Score mask (standalone validation, fused production) | Score tile `[Bq,Bk]` + absolute offsets/live lengths | Preserve valid causal scores, replace excluded scores with negative infinity before max/exp; skip wholly future blocks and bypass masking for wholly valid past blocks. |
| Causal GQA attention | 32 Q heads, 8 KV heads, D=128 | Tiled QK and PV with online softmax; no global score/probability matrix; reuse KV across grouped query heads where L1 permits. |
| O GEMM + residual | `[M,4096] @ [4096,4096]` | Descale if needed, add input residual, produce BF16. FP8 mode needs scaled context operands before GEMM. |
| Post-attention RMSNorm + optional quantize | `[M,4096]` | Same rowwise family as input RMSNorm, different weights and scales. |
| Gate/up GEMM + SwiGLU | Two `[M,4096] @ [4096,14336]` | Share A, pair gate/up output blocks, apply separate descales then SiLU(gate)*up. Emit only `[M,14336]` where fusion is feasible. |
| Down GEMM + residual | `[M,14336] @ [14336,4096]` | FP8 input conversion can fuse with SwiGLU; descale down output and add residual. |
| Final norm + LM head + selection | Last live row only; `[1,4096] @ [4096,128256]` | Reuse existing decode final-token path through one layout bridge. No vocabulary projection for earlier prompt rows in generation mode. |

Input and post-attention normalization may later fuse with their preceding
residual/embedding stage. A sharded GEMM epilogue does not automatically own a
complete 4096-wide row: include the necessary cross-core reduction and traffic
before deciding that residual+RMSNorm fusion is a win.

## GEMM first

`examples/matmul_peak.py` and `examples/matmul_peak_kernel/` already provide
blocked multicast BF16/FP8 matmul. Reuse that implementation's scheduling and
instruction work, adapting it to `ttko` buffers, command caching, and epilogues.
It currently uses `GridProgram` and another Device interface; it is not a
drop-in replacement. FP8 mode currently writes F16 and stores intermediate
partials in its output format: validate accumulation range/precision and add
the required BF16 output/scaling path before model integration.

- Partition M and N over a tunable core grid. Multicast A across N workers and
  B across M workers. Double-buffer K blocks; overlap DRAM, unpack, math, pack,
  and writes. Tune bank rotation and both NoCs for the actual grid.
- Keep output subblocks accumulating for as much K as Dst/L1 allow. Measure
  partial spill/reload cost and accuracy. Start with validated accumulation;
  reduce precision/fidelity only after full-model checks.
- Tune exact model shapes, not square synthetic matrices. Candidate M values:
  32, 64, 128, 256, 512. Candidate K blocks: 32, 64, 128, 256 elements, subject
  to buffer capacity; compare 1x4, 2x2, 2x4 output tile subblocks where supported.
- Select grids by measured useful latency, not worker count. The current
  peak planner prioritizes core count; extra cores and padded arithmetic can
  be especially expensive at small M. Report useful and padded FLOPs separately.
- Fuse paired gate/up only if holding both results does not cause excessive
  spills or reduce utilization. Compare separate GEMMs plus standalone tiled
  SwiGLU against the fused version.
- For very short prompts retain a measured decode/small-M crossover. Do not
  force a 256-row GEMM onto a few live tokens.

The four projection groups contain 218,103,808 weights per layer. Across 32
layers that is about 13.96 GFLOP per prompt token, excluding attention and the
final LM head. MLP accounts for about 80.8% of projection FLOPs; O+down account
for about 34.6%. Accelerating only QKV and gate/up leaves substantial work in
tokenwise projections. These are arithmetic shares, not measured time shares.

Ignoring activation traffic, reuse over M tokens gives roughly M FLOP/byte for
BF16 weights and 2M for FP8 weights. Actual intensity is lower with repeated
loads, spills, padding, or conversion. Use the measured compute/bandwidth
balance to choose chunk size; there is no justified universal optimum yet.

## Attention

### Mask kernel

Build `prefill_score_mask` as an independently testable SFPU tile operation,
then inline the same operation into attention before the online-softmax update.
Do not allocate or stream a full sequence-squared mask. First support the
contiguous causal prompt/prefix case; arbitrary user masks are separate scope.

For query-block offset q0 within the new chunk, absolute key-block offset k0,
prefix length P, and tile-local row/column r/c:

```
q = P + q0 + r
k = k0 + c
valid = (q0 + r < M) and (k < P + M) and (k <= q)
masked_score = score if valid else -infinity
```

Use the runtime's actual accessible key length if it differs from P+M. For
full tiles, `k_max <= q_min` permits the past-block fast path, while
`k_min > q_max` permits skipping the block. Check live row/column bounds before
using either shortcut. Diagonal and tail tiles use lane predicates derived
from logical row/column indices; account explicitly for the physical four-face
tile layout. Evaluate procedural lane predicates versus small reusable local
diagonal templates; measure SFPU instructions and L1 traffic.

Apply masking before row max and exponentiation. Negative infinity must be
preserved through the chosen score representation; do not quantize masked
scores to FP8. A finite negative constant is not a general substitute.
Padded query rows should be skipped or explicitly forced to zero output without
evaluating an all-masked `-infinity - -infinity` softmax recurrence.

Test exact masks independently of attention math: diagonal, fully past/future,
rows/columns 15/16 and 31/32 (face/tile boundaries), lengths 1/31/32/33,
nonaligned prefixes 1/17/31/33, and chunk boundaries. Check valid scores stay
unchanged and invalid probabilities become zero. Then test causal isolation:
alter future K/V and verify earlier valid outputs remain unchanged.

### Online softmax and scheduling

Use a FlashAttention-style online recurrence. For each query block, maintain
FP32 row maximum m, row sum l, and output accumulator O. For each valid KV
block, compute scores with `1/sqrt(128)` scaling and an absolute causal mask;
update m, rescale old l/O, and accumulate the new exp(scores) and P@V. Divide
O by l once after the final block. Never write an M-by-context score matrix
to DRAM. Skip blocks wholly above the causal diagonal, and mask diagonal/tail
blocks before max/exp. Padded/all-masked rows need explicit safe handling.

Start with 32- or 64-row query blocks and 32/64/128-token KV blocks, within
L1/Dst budgets. Parallelize over query blocks and heads; schedule differing
causal lengths to avoid late-query stragglers. Share K/V within each four-head
GQA group when beneficial. Split-KV plus stable partial-softmax merging is a
later option for few queries over a long cached prefix, not the default for
long initial prompts.

Keep attention and KV BF16 in the first FP8 projection pipeline; this matches
the current FP8 runtime's default attention dtype. FP8 attention is a separate
accuracy/performance experiment. The online-softmax and query-block scheduling
approach follows [FlashAttention-2](https://arxiv.org/abs/2307.08691); its GPU
performance results are not Blackhole performance predictions.

## FP8 contract

Use this repository's E4M3FN checkpoint bytes, not BFP8. Initially preserve
published per-projection input/weight scales:

`A8 = quantize(A / input_scale)`

`Y = matmul(A8, W8) * input_scale * weight_scale`

Q/K/V and gate/up share quantized A only when their input scales match, as
`_projection_scales` currently requires. Output scales remain separate even
inside a grouped GEMM. Apply scales before nonlinearities or residual adds.
Retain BF16 residuals and FP32 normalization/softmax statistics. Inspect the
FP8 helper paths and `tests/fp8.md`: packing truncation, subnormal behavior,
source-format conversion, and accumulator interpretation are real constraints.
Changing dtype and byte counts alone is insufficient. Validate checkpoint-scale
saturation on representative prompts before exploring dynamic activation scales.

## Runtime and implementation order

1. Establish BF16/FP8 decode and current BF16-prefill correctness/timing baselines.
   Add exact-shape GEMM measurements and a byte/FLOP/launch accounting report.
2. Implement tiled buffers, bounded weight preparation, and the GEMM adapter.
   Prove all four projection shapes in BF16 and scaled FP8 independently.
3. Implement multirow normalization, RoPE/cache writes, and block attention.
   Validate one BF16 layer, then all 32 layers and prefill-to-decode handoff.
4. Enable scaled FP8 projections with BF16 attention/cache; validate complete
   model quality. Integrate chat only after prefix extension semantics work.
5. Tune fusion, grids, block sizes, NoCs, buffering, and chunk size. Cache
   compiled variants by shape/dtype/layout; parameterize addresses and positions.
   Replay a chunk or bounded layer group without host waits after each layer,
   using explicit device dependency/barrier handling and bounded CQ storage.

A 128-token chunk is a reasonable first integration point, not a promised
optimum. Benchmark larger chunks to amortize weight reads, and sequence tails
without generating a separate large program for every possible live length.

## Acceptance and benchmark matrix

- Exact projection shapes: QKV N=6144, O N=4096, gate/up N=28672 (also paired
  separate outputs), down K=14336/N=4096. Sweep M above in both dtypes.
- Correctness cases: lengths 1, 7, 31, 32, 33, 127, 128, 129 and nonzero
  prefixes crossing 32-token cache boundaries. Check RoPE positions, causal
  masks, untouched cache rows, all layer outputs, final logits, and several
  subsequent decode tokens. Compare against an independent model reference
  as well as existing decode; changed reduction order need not be bit-identical.
- FP8: compare to a reference using the same checkpoint/scales, track absolute
  and relative errors, saturation/nonfinite counts, logit differences and
  corpus loss/perplexity. Token agreement alone is insufficient. Establish
  numerical acceptance thresholds from the validated decode/reference baseline
  before selecting lower-fidelity variants.
- End-to-end prompt lengths: 32, 128, 512, 2048, 4096, 8191 with capacity for
  the first generated token; shorter prompts exercise the dispatch crossover.
  The existing runtime rejects initial prompts of length 8192.
- Measure cold setup/weight preparation separately from warm prefill. Report
  wall time, device stage times, prompt tokens/s, TTFT through final selection,
  launch count, padding, and peak DRAM/L1 use. Include layout bridges and
  quantization in stage costs, not just GEMM math.
- Warm up, repeat, report median and spread, use identical prompt IDs and
  device conditions. Recheck decode performance after prefill handoff.

The success criterion is lower measured full-model TTFT with accepted numerical
quality and unchanged decode performance. Kernel TFLOP/s is diagnostic, not the
final optimization objective.
