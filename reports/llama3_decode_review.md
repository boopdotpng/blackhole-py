# Llama 3.2 1B bs=1 decode: launch count, fusion, and implementation review

> July 25, 2026 update: Q/K/V projection is now fused per layer while
> preserving the three existing compact layouts. The trace has 228 launches,
> produces bit-exact Q/K/V versus separate projections, and measures 108.15
> tok/s. Embedding and LM-head storage is also tied, removing a duplicate
> 0.489 GiB upload. See [`llama3_e2e_profile.md`](llama3_e2e_profile.md).

Hardware: p100a, 118 worker cores, 1350 MHz ref clock. Measured at position 64
with `weights/model.safetensors` (unsloth 1B Instruct).

- Raw measurements: [`llama3_decode_profile.txt`](llama3_decode_profile.txt)
- Benchmark harness: [`../examples/llama_launch_bench.py`](../examples/llama_launch_bench.py)
- Baseline: **9744 us/token = 102.6 tok/s**, **260 launches/token**

## 1. Launches per token

`Llama3Decode._build_programs` queues one trace containing the whole token.
Per layer, `_queue_layer` issues 16 launches:

```text
                                            launches
  rms         input RMSNorm                     1
  q           Q projection                      1
  k           K projection                      1
  k           V projection (same kernel)        1
  rope        RoPE Q+K, reassemble V            1
  cache       KV-cache append                   1
  attention   fused QK/softmax/PV               1
  q           O projection (same kernel)        1
  residual    attn residual add + scatter       1
  rms         post-attention RMSNorm            1
  gate        gate projection                   1
  gate        up projection (same kernel)       1
  swiglu      silu(gate)*up                     1
  dense       compact -> dense [1,8192]         1
  down        down projection                   1
  residual    MLP residual add                  1
                                            ------
                                               16  x 16 layers = 256
  embedding   1  +  final rms 1  +  lm 1  +  argmax 1  =   4
                                            ------
                                        total  260
```

Only 14 distinct programs exist; the 260 launches are replays with different
weight-buffer parameters, and the whole token is one captured CQ trace with
resident kernels. That part of the design is already good — there is no
per-launch kernel upload and no host round-trip inside a token.

## 2. Where the 9744 us goes

Two independent measurements, because neither alone is trustworthy:

| stage | cores | isolated us | n/token | us/token | % | roofline |
|---|---:|---:|---:|---:|---:|---|
| gate (gate+up) | 118 | 99.5 | 32 | 3185 | 32.7% | 337 GB/s |
| down | 118 | 105.5 | 16 | 1687 | 17.3% | 318 GB/s |
| lm head | 118 | 1405.9 | 1 | 1406 | 14.4% | 374 GB/s |
| q (Q+O) | 118 | 30.2 | 32 | 968 | 9.9% | 277 GB/s |
| attention | 8 | 31.9 | 16 | 510 | 5.2% | latency |
| k (K+V) | 118 | 14.6 | 32 | 466 | 4.8% | 144 GB/s |
| rope | 40 | 12.2 | 16 | 195 | 2.0% | latency |
| residual | 32 | 6.0 | 32 | 191 | 2.0% | dispatch |
| rms | 1 | 4.8 | 33 | 159 | 1.6% | dispatch |
| dense | 118 | 9.9 | 16 | 158 | 1.6% | dispatch |
| swiglu | 118 | 5.7 | 16 | 91 | 0.9% | dispatch |
| cache | 8 | 3.6 | 16 | 58 | 0.6% | dispatch |
| argmax | 118 | 38.8 | 1 | 39 | 0.4% | latency |
| embedding | 1 | 3.9 | 1 | 4 | 0.0% | dispatch |
| **sum** | | | **260** | **9115** | 94% | |

Isolated kernel time sums to 9115 us of the 9744 us token, so **~94% of the
token is real kernel occupancy and only ~6% (≈630 us) is unhidden dispatch**.

### The dispatch floor is real but mostly hidden

```text
empty 118-core launch, GO->done          :   2.99 us
empty x260 as one trace                  : 2999 us  ->  11.5 us/launch
```

The dispatch pipeline sustains only ~11.5 us/launch, i.e. **260 launches cost
~3000 us of dispatch work** — 31% of the token if it were serial. It is not
serial: prefetch/dispatch run ahead of the workers, so dispatch hides behind
any kernel longer than ~11.5 us. This is why the picture is bimodal:

```text
  kernel time per launch
  ^
  |  gate 99us  down 105us  lm 1406us      <- memory bound, dispatch fully hidden
  |  ---------------------------------
  |  q 30us  attention 32us               <- comfortably above floor
  |  ==== 11.5us dispatch floor ====
  |  dense 9.9us  residual 6.0us  rms 4.8us  cache 3.6us  <- dispatch bound
  v
```

### In-situ ablation: what fusion actually buys

Removing launches from the trace and re-timing gives the true marginal cost,
including hidden overhead. This is the number that predicts fusion wins:

| removed | launches saved | us saved | us/launch |
|---|---:|---:|---:|
| lm + argmax | 2 | 1353 | 676 |
| attention | 16 | 877 | 54.8 |
| k/v projections | 32 | 508 | 15.9 |
| all small stages (rms,cache,residual,swiglu,dense) | 113 | 706 | **6.3** |
| rope | 16 | 237 | 14.8 |
| swiglu + dense | 32 | 254 | 7.9 |
| rms | 33 | 196 | 5.9 |
| dense | 16 | 150 | 9.4 |
| residual | 32 | 89 | 2.8 |
| swiglu | 16 | 0.2 | 0.0 |
| cache | 16 | 0.1 | 0.0 |

The key result: **eliminating 113 of 260 launches (43%) saves only 706 us
(7.3%)**. `swiglu` and `cache` are *completely free* — their 91 us and 58 us of
isolated kernel time is entirely hidden behind neighboring DRAM traffic.

## 3. DRAM roofline: the real ceiling

```text
weight bytes streamed per token = 16 layers x (2 x Q/O + 2 x K/V + 3 x MLP) + LM head
                                = 2471 MB   (the entire 1.24B params, BF16, every token)
achieved                        = 2471 MB / 9744 us = 254 GB/s
```

Decode at bs=1 is pure GEMV: every weight is read once and used for a single
MAC per element. p100a's practical DRAM ceiling is ~400-450 GB/s, and the
best-performing kernel here (`gate`) already hits **337 GB/s**, `lm` **374
GB/s**. So:

```text
   254 GB/s achieved  ──────────────────────────────▶  400 GB/s practical peak
   9744 us/token                                        ~6180 us/token
   102.6 tok/s                                          ~162 tok/s
```

**Ceiling is ~160 tok/s, and it is set by DRAM bandwidth, not by launch count.**
Fusing every fusable launch gets maybe 105-112 tok/s. The remaining gap is
bandwidth efficiency inside the projection kernel.

## 4. Fusion opportunities, ranked by value

### Worth doing

**(a) Fuse Q+K+V into one launch (and gate+up into one).** These read *different*
weights but the *same* input vector, and each currently re-reads `normalized`
and pays the projection kernel's fixed cost. The cost model from measurement:

```text
decode_projection(rows) ≈ 9.34 us + 10.20 ns/row
```

That 9.34 us fixed cost is paid 113 times per token = **1055 us (10.8%)**. It is
setup: the token broadcast read, CB priming, and the per-core compact-output
zero/scatter. Merging Q,K,V into one launch over 118 cores (each core owning a
slice of the 3072 concatenated output rows) removes 2 fixed costs x 16 layers,
and gate+up removes 1 x 16:

```text
  q+k+v  ->  1 launch : ~299 us   (saves 32 launches)
  gate+up ->  1 launch : ~149 us   (saves 16 launches)
                        ------
                         ~448 us  ->  ~4.8% faster, 107.7 tok/s
```

This is also the *cleanest* change: `decode_projection` already shards by output
row, so a fused version is a concatenated weight buffer plus one output buffer.
Note gate/up measure 99.5 us vs 92.9 us predicted — the 8192-row shape is 6.6 us
worse than the linear model, suggesting per-core row-loop overhead grows; fusing
gate+up into 16384 rows may not be purely additive.

**(b) Fold `dense` into `swiglu`'s writeback, and `residual` into the projection.**
`dense` (compact→dense [1,8192]) costs 150 us purely to reshape data that
`swiglu` just produced. `swiglu` already runs on all 118 cores holding the
compact hidden state; it could scatter directly to the dense layout in its
NCRISC writeback, exactly as `_decode_projection_residual_program` already does.
Ablation says swiglu+dense together are worth 254 us; fusing them should recover
most of the 150 us `dense` costs. Similarly `residual` (89 us marginal) is a
64-element add + scatter that the O/down projection could do in its own
writeback path — the code already proves this pattern works.

**(c) Fuse `cache` into `rope`.** `rope` already computes the rotated K and
reassembles V; `kv_cache_write` then re-reads both from DRAM just to write them
to cache tiles. `cache` is 0 us marginal (fully hidden) so this wins nothing
today, but it removes 16 launches and a DRAM round-trip, which matters once the
big projections get faster and the floor starts to bite.

### Not worth doing

- **`rms` (196 us, 33 launches).** It runs on **1 core** for a 2048-element
  vector. Fusing it into the following projection is awkward (all 118 cores need
  the normalized vector, so you need a broadcast anyway). Better fix: it is
  dispatch-bound at 4.8 us, so just accept it, or fuse the *residual add* into it
  (rms already reads `x`; making it read `x_b` + `context` and write both the new
  residual and the normalized output kills a launch for free).
- **`attention` (877 us marginal, 54.8 us/launch!).** Do not fuse — *optimize*.
  It runs on only **8 cores** (one per KV head) while 110 cores idle. Its 31.9 us
  isolated time is latency, not bandwidth: at position 64 it reads only
  8 heads x 3 blocks x 2 tiles x 2 KV = tiny. The 54.8 us/launch marginal cost
  (higher than isolated!) means it *stalls the pipeline* — the 110 idle cores
  can't help and dispatch can't run ahead through it. **This is the highest-value
  target after bandwidth**: split each KV head's time blocks across multiple
  cores and do a final cross-core softmax merge. Also note this cost grows with
  sequence length while everything else is constant, so at position 4000 it will
  dominate.

## 5. Implementation review

**What is genuinely well done:**

1. **Resident everything.** Kernels live in a per-core L1 arena
   (`cache_kernels`), immutable CQ records live in DRAM (`cache_programs`), and
   the entire token is one replayable trace. Per-token host work is a 24-byte
   runtime-param multicast plus one event patch. The `_TraceRuntime` /
   `PARAM_TEMPLATE` design — where BRISC resolves dynamic params from
   `RUNTIME_PARAM_BASE` via ID indirection before releasing the other RISCs — is
   a genuinely elegant way to get parameterized trace replay.
2. **Program reuse by buffer substitution.** 14 programs cover 260 launches
   because weights are just parameters. `_specialize_token_counts` combining
   compile-time loop-count variants into one heterogeneous launch (different
   kernel image per core, same launch) is a nice trick for the 42x18 + 76x17
   row-sharding split.
3. **Real fusion where it counts.** `gqa_attention_fused` does QK, online
   softmax (streaming m/l/O update in SFPU lane registers), and PV in a single
   launch with the mask synthesized on the fly — no materialized `[32,T]` score
   tensor, no separate scale/softmax launches. That is 4 launches from the
   original plan collapsed into 1.
4. **No unnecessary data movement in principle.** GQA doesn't repeat K/V, K is
   transposed during unpack (`right_transpose=True`), RoPE tables are host-built
   and resident, and the KV cache layout `[8,256,2,32,32]` is chosen so QK and PV
   both consume it natively.
5. **The device closes the loop itself.** `decode_argmax` publishes the token to
   pinned host memory *and* appends it to device-side token history *and* writes
   the next token's runtime params. Host reads 4 bytes; no readback program.

**What I'd push back on:**

1. **The compact→dense→compact shuffling is the main structural wart.**
   Projections write a "compact" `[118, rows_per_core]` layout (one scalar per
   packed tile, then hand-tilized on NCRISC), and then `rope`, `residual`, and
   `dense` all exist largely to un-shuffle it. Look at the cost: `dense` 158 us,
   `residual` 191 us, `rope` 195 us — ~540 us/token, 5.5%, is pure layout
   repair. The root cause is that a GEMV's output is one scalar per core per row,
   which packs terribly. Worth considering: have the projection's NCRISC scatter
   directly into the final dense layout (it already computes a full tilized
   byte offset — `_decode_projection_program`'s offset arithmetic is ~30
   instructions of shifts per row), or keep activations compact end-to-end and
   teach the consumers to read compact.
2. **`decode_projection`'s per-row scalar path is expensive.** For every output
   row: full 2-tile weight read, a 2-tile x 2-tile "matmul" that computes one dot
   product, SFPU accumulate, an SFPU lane-rotation reduction tree
   (`_dot_finalize`, ~20 instructions), a scalar pack into a whole tile, then
   ~30 instructions of address math to place 2 bytes. That is a lot of machinery
   per scalar, and it shows: only 277-337 GB/s of a ~400+ GB/s ceiling, and
   9.3 us fixed cost. A proper GEMV that keeps 32 output rows in one Dst tile and
   packs them together would amortize the reduction and the pack across 32 rows.
   **This, not launch count, is the real performance work.**
3. **8-core attention is a scaling landmine.** Already 5.2% at position 64 and
   the only stage whose cost grows with context. 110 idle cores.
4. **`rms` on a single core.** 4.8 us x 33 = 159 us for what is a 2048-element
   reduction. It's dispatch-bound so it's cheap in absolute terms, but combined
   with the fact that all 118 cores then need the result, a broadcast-fused
   norm+projection would be strictly better.
5. **Prompt ingestion still uses decode.** `run_decode_e2e` runs the full
   228-launch decode trace for every prompt token, so a 100-token prompt costs
   about 0.92 s of TTFT. Prefill is intentionally outside this decode-only
   module.
6. **Minor bugs/rough edges found while benchmarking:**
   - `run_decode_e2e` crashed on current `transformers`: `apply_chat_template`
     returns a `BatchEncoding`, not a list. Fixed in `examples/llama3.py`.
   - `_install_param_templates` leaks the L1 template arena — capturing a second
     228-launch trace in one session raises "arena is full". Traces never free
     their templates. The benchmark works around it by rewinding
     `_param_template_next`; a real fix needs refcounting or a `DeviceTrace.free()`.
   - Calling `cache_kernels` after traces are live corrupts subsequent
     `device.run` (CQ timeout, then `close()` fails in `SetPowerState` with
     EINVAL, requiring a device reset). Worth an explicit guard.
   - `_queue_layer(index, position)` takes `position` and computes
     `blocks`/`tail` from it, but the trace is captured with `position=0` and
     those values are overridden by runtime params at replay. The dead argument
     is confusing.

## 6. Recommended order of work

```text
  1. GEMV rewrite: 32 output rows per Dst tile, amortized reduction + pack
     -> targets the 277->400 GB/s gap on 74% of the token   ~+30-40 tok/s
  2. Parallelize attention across >8 cores                   fixes context scaling
  3. Fuse gate+up (Q+K+V is complete)                        next launch fusion
  4. Fold dense into swiglu, residual into projection wb     ~+2 tok/s, 48 fewer launches
  5. Fix the trace/template arena leak                        correctness
```

Fusion is worth roughly +7-8 tok/s total (102 -> ~110). Bandwidth efficiency in
`decode_projection` is worth +30-40. **The launch count is not the bottleneck —
94% of the token is genuine kernel occupancy, and the kernels are leaving
~35% of DRAM bandwidth on the table.**
