Good questions — and your own decode report actually contains most of the evidence needed to design this well. Let me lay out how I'd structure it, because I think the naive version ("enumerate configs, run kernels, pick fastest") fails for a specific reason your report already proved.

## The framing: three decisions, very different search characters

```text
  ┌──────────────────────────────────────────────────────────────────────┐
  │ L0  LAYOUT  (global, combinatorial, must be solved across ops)       │
  │     compact vs dense, shard axis, bank interleave, DRAM vs L1-resident│
  │     → cannot be tuned per-op: conversion cost is an EDGE property     │
  ├──────────────────────────────────────────────────────────────────────┤
  │ L1  PARALLELISM  (per-op, 1-D, smooth, ~unimodal)                    │
  │     core count P, work split, transaction size                       │
  │     → closed-form model + 3-4 probes. Never brute force.             │
  ├──────────────────────────────────────────────────────────────────────┤
  │ L2  ENGINE  (per-op, tiny discrete set, |S| < 20)                    │
  │     RV / FPU / SFPU / pack-path, dst tiling, HiFi mode               │
  │     → exhaustive measure is FINE here, cache by signature            │
  └──────────────────────────────────────────────────────────────────────┘
```

Brute force is only appropriate at L2. Applying it at L1 wastes device time on a knob you can predict, and applying it at L0 gives you *wrong answers* (below).

## L1: core count is analytic, don't search it blindly

Your data already gives you the shape of the curve. Model each op as a max of three regimes:

```text
  t(P) = max( dispatch_floor(P),           ~11.5 us  (measured, ~flat in P)
              bytes / BW_eff(P, chunk),    DRAM/NoC roofline
              work_total / (P * rate_engine) )   compute/issue
       + setup(P)                          9.34 us for decode_projection
```

The non-obvious term is `BW_eff(P, chunk)`. Aggregate bandwidth is *not* monotone in P, and the reason is transaction size, not "NoC traffic" in the abstract:

```text
  bytes per core per contiguous read = total_bytes / P

  BW_eff
   400 ┤            ╭───────╮
       │        ╭───╯        ╰──────╮        ← bank-side request-rate limit:
   300 ┤    ╭───╯                    ╰────   many small reads = row-thrash +
       │  ╭─╯                                header overhead per 64B beat
   200 ┤ ╭╯
       │╭╯   ← too few cores: can't keep 7 banks × N outstanding reqs busy
   100 ┤╯
       └┬────┬────┬────┬────┬────┬────┬───▶ P
        4    8    16   32   64   96  118

        sweet spot ≈ where chunk_per_core first drops below ~2-4 KB
```

So the practical rule that replaces a search: **pick the largest P such that each core's contiguous DRAM chunk is still ≥ a calibrated threshold (one or two tiles' worth), and such that per-core work ≥ dispatch floor × margin.**

```text
  P* = clamp( 1,
              min( total_bytes / MIN_CHUNK,        # keep transactions fat
                   work_total / (rate * FLOOR) ),  # beat the 11.5us floor
              len(worker_cores) )
```

Then probe only `{P*/2, P*, min(P*·2, 118)}` on hardware and keep the winner. Three measurements, not a sweep. This immediately fixes two things your report flags: `attention` on 8 cores (P* would say ~32-64, work-limited) and `rms` on 1 core.

There's also a placement sub-knob worth being explicit about: **which** cores, not just how many. Since DRAM is 7-bank interleaved, the assignment should make core→bank affinity uniform and short-hop. Your `shard_addr` already smuggles the starting bank into the low address bits, so the scheduler has a natural hook: choose the shard→core permutation so that `bank(shard) ≡ f(core_column)`, minimizing NoC hop distance and avoiding N cores hammering bank 0 simultaneously.

```text
      DRAM banks along the die edge          workers
      ┌───┬───┬───┬───┬───┬───┬───┐
      │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │
      └─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┘
    bad:  all cores start at bank 0  →  1/7 of BW, serialized queue
    good: core (x,y) starts at bank (x + 3y) mod 7  →  uniform, short hops
```

## L0: layout is the part that must NOT be per-op

This is the thing I'd push hardest. Your report measured it: `dense` 158 µs + `residual` 191 µs + `rope` 195 µs ≈ **540 µs/token of pure layout repair**, because `decode_projection`'s locally-optimal output layout (compact `[118, rows_per_core]`) is a bad input layout for everyone downstream.

A per-op autotuner will reproduce that bug forever, because it optimizes `t(op | layout)` while the real objective is:

```text
  minimize  Σ_v  t(v, layout[v], P[v])  +  Σ_(u→v)  convert(layout[u] → layout[v])
```

Llama decode is essentially a chain (with residual skip edges), so this is not a hard problem — it's a shortest-path/DP over layout candidates per node:

```text
    rms          qkv          rope         attn         o-proj
  ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐
  │dense  │──▶ │dense  │──▶ │dense  │──▶ │dense  │──▶ │dense  │
  │compact│──▶ │compact│──▶ │compact│──▶ │compact│──▶ │compact│
  │L1-res │──▶ │L1-res │──▶ │ ...   │    │       │    │       │
  └───────┘    └───────┘    └───────┘    └───────┘    └───────┘
     node cost = kernel time in that layout
     edge cost = 0 if same, else measured/modelled reshuffle cost
                 (∞ if the kernel has no variant for that input layout)

  DP: best[v][L] = t(v,L) + min_over_L'( best[u][L'] + convert(L'→L) )
```

Viterbi over a chain, exact, milliseconds to solve. Residual skips make it a series-parallel graph — still tractable with a small amount of care (treat the residual as a second incoming edge and include the residual's layout in the state, or just tree-decompose).

The payoff is that the DP will *discover* the fusions in your section 4 on its own: if `swiglu` has a variant that writes dense directly, the DP picks it because `convert=0` beats `dense`'s 158 µs. Fusion becomes a consequence of layout assignment rather than a separate manual pass.

## L2: engine selection — this is where brute force earns its keep

The space is genuinely small and genuinely hard to model (SFPU lane rotations, MOP replay, pack throughput, HiFi2 vs HiFi4). So: don't model it, **measure primitives once and build a calibrated LUT**, then compose.

```text
  microbench suite (run once per silicon rev, ~seconds):
    ├─ unpack: L1→srcA/B, tiles/us, per dtype, per transpose mode
    ├─ FPU:    matmul 32x32, HiFi2/HiFi4, reduce, transpose
    ├─ SFPU:   per-instruction cost, exp/recip/sqrt, lane rotate, mask
    ├─ pack:   dst→L1, full tile vs scalar vs strided
    ├─ RV:     ALU ops/cycle, L1 load latency, loop overhead   ← argmax lives here
    └─ NoC:    read/write BW vs chunk size vs #outstanding vs hop count
                                    ↓
    cost(candidate impl) = Σ primitive_cost × count   (a static analysis of
                            the emitted instruction stream — you already have
                            the full IR in asm.py/ttk, so counting is free)
                                    ↓
    rank candidates, measure only top-k (k≈3) on hardware
```

Because you generate code in Python and own the whole IR, you can get counts *without* running anything. That turns "run a bunch of kernels and see" into "run 3 kernels and see", which matters a lot when the search runs inside a compile.

Two concrete traps for the measure-with-fake-data approach:

1. **Fake data can change timing.** Anything with SFPU predication/early-out, and especially anything data-dependent like your argmax, will time differently on zeros vs realistic values. Use a fixed pseudo-random fill from the same distribution class as real activations, and record the seed in the cache key.
2. **Isolated measurement optimizes the wrong objective.** This is the big one, and again your own report is the proof: `swiglu` measures 91 µs/token in isolation and **0 µs marginal** in the trace. `attention` measures 31.9 µs isolated but costs **54.8 µs marginal** because it stalls the pipeline. Isolated timing is off by ∞% in one direction and −70% in the other.

```text
   isolated timing                     in-situ marginal timing
   ┌────────┐                          ┌────┬────┬────┬────┐  T_with
   │ op     │  → 91us  "expensive!"    │ .. │ op │ .. │ .. │
   └────────┘                          └────┴────┴────┴────┘
                                       ┌────┬────┬────┐      T_without
                                       │ .. │ .. │ .. │
                                       └────┴────┴────┘
                                       cost = T_with − T_without  = 0us
```

So the autotuner's fitness function should be **marginal cost measured inside a representative trace**, exactly like your ablation harness in `llama_launch_bench.py`. That harness is already 80% of an autotuner's measurement backend; I'd promote it to a first-class API rather than a benchmark script.

## How I'd actually build it here

```text
  Stage 1  ── declare, don't hardcode
     Ops describe a candidate space instead of a fixed shard.
       @schedulable
       def projection(x, w, out):
         cores  = Knob.cores(min_chunk=2*TILE, floor_us=11.5)
         layout = Knob.enum("compact", "dense", "dense_scatter")
         engine = Knob.enum("gemv_scalar", "gemv_32row_dst")
     Nothing else changes; Program already takes `cores` as an argument.

  Stage 2  ── analytic model + primitive LUT
     Calibration suite writes primitives.json. Static instruction counting
     over the emitted asm gives cost() for free. Now you can rank 1000
     candidates offline in ms.

  Stage 3  ── hardware-in-loop, top-k only, cached
     key = (op class, shapes, dtypes, input layouts, silicon rev, primitives hash)
     value = winning config + measured marginal us
     ~/.cache/blackhole-py/schedules.json, committed for known models.
     Measure via trace ablation, median of N, discard first (cold CB) run.

  Stage 4  ── global layout DP over the op graph
     Node costs from Stage 2/3, edge costs from a convert-cost table.
     Viterbi the chain. This is where the 540us of layout repair dies.

  Stage 5  ── feedback
     After a real run, compare predicted vs measured; refit the model
     (per-op residual correction). Your report already found a systematic
     one: 8192-row gate/up is 6.6us worse than linear → per-core row-loop
     overhead is superlinear. That's a model term waiting to be fit.
```

## Things I'd watch out for

- **Search must be cheap enough to run at import time.** With the LUT + DP, a whole llama schedule is a few ms of Python plus maybe 40 hardware probes on a cold cache. That's acceptable. A blind grid over (P × layout × engine) per op is thousands of device launches and minutes — nobody will leave it on.
- **Autotune fused regions, not ops.** Once fusion is on the table, the unit of scheduling is a region (qkv+rope+cache), because that's the unit whose layout boundaries you control. Otherwise the tuner keeps picking layouts that are locally free and globally expensive.
- **Constraints before objectives.** L1 arena capacity, CB depth, param slots (`PARAM_SLOTS`), the 118-core limit, and `MAX_WRITE_SIZE` are hard feasibility filters. Prune with those first — most of the space is invalid, and validity is cheap to check statically.
- **Keep an escape hatch.** `@schedulable(pin=...)` so a hand-tuned kernel (your `gqa_attention_fused`) can override the scheduler, and so you can A/B the scheduler against hand-written code. If the scheduler can't beat hand-tuning on your existing 14 programs, it isn't ready.

If you want, I can prototype Stage 1+2 concretely: a `Knob`/candidate-space wrapper around `Program`, the microbench calibration suite, and the static instruction-count coster over your existing `asm.py` IR — then validate it by checking whether the model reproduces the measured table in `reports/llama3_decode_review.md` (which is a genuinely good ground truth to fit against). That's the highest-confidence starting point, since it's testable against numbers you already have.