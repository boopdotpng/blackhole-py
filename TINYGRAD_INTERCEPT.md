# tinygrad interception plan

How we get from tinygrad's lazy Tensor graph to TTIR. This is the integration
boundary — the rest of the stack (TTIR lowering, codegen, device launch) is
described in TTIR.md and ARCHITECTURE.md.

## Intercept point: pre-schedule UOp DAG (altitude A)

tinygrad's Tensor methods (`x.matmul()`, `.reshape()`, `.cast()`, etc.) build a
lazy UOp DAG directly — there is no separate IR construction pass. Each method
appends UOp nodes. The DAG is closed when `.realize()` or `.schedule_linear()`
is called. **We intercept the finished DAG before any lowering pass runs.**

At this altitude, op intent is fully recoverable:
- `REDUCE(ADD, axis=(3,), dtype=float) ← MUL(EXPAND, EXPAND)` is a matmul with
  fp32 accumulation.
- `REDUCE(MAX, axis) → SUB → EXP2 → REDUCE(ADD, axis) → RECIP → MUL` is softmax.
- `CAST(f32) → MUL(x,x) → REDUCE(mean) → ADD(eps) → SQRT → RECIP → MUL(x) →
  CAST(bf16) → MUL(weight)` is RMSNorm.

After tinygrad's `run_rangeify` (schedule/indexing.py:151), these collapse into
flat `RANGE → INDEX → MUL → STORE` kernels — no matmul, no reduce-over-axis, no
softmax. Too late. We must intercept before `transform_to_call` (callify.py:198).

## tinygrad's lowering pipeline (for reference)

```
Tensor API (lazy UOp DAG)
   │  x.matmul(W) → MUL(EXPAND,EXPAND) → REDUCE(ADD); .reshape() → RESHAPE; etc.
   │  *** THIS IS WHERE WE INTERCEPT — the finished DAG, x.uop ***
   ▼
1. transform_to_call        (callify.py:198)
   │  Splits SINK into CALL kernels (fusion boundaries).
   ▼
2. create_schedule          (schedule/__init__.py:29)
   │  Toposort CALLs by RAW/WAR deps.
   ▼
3. run_rangeify             (schedule/indexing.py:151)
   │  Fuses elementwise into RANGE loops, collapses movement ops into
   │  address arithmetic. REDUCE(axis) → flat RANGE+INDEX+STORE.
   │  *** After this, tile intent is gone. ***
   ▼
4. full_rewrite_to_sink      (codegen/__init__.py:278)
   │  Per-kernel: load collapse, range splitting, symbolic, BEAM,
   │  expansion, linearization.
   ▼
5. to_program                (codegen/__init__.py:482)
   │  → renderer-specific code (Metal/LLVM/etc).
   ▼
6. run_linear               (engine/realize.py:279)
   │  Execute.
```

## tinygrad's optimization mechanisms (exactly two)

### 1. Pattern matchers — the main route

Every graph-level pass in tinygrad is a `graph_rewrite(sink, PatternMatcher,
...)` call. A `PatternMatcher` is a list of `(UPat(pattern), rewrite_fn)` rules;
`graph_rewrite` walks the DAG bottom-up and applies them to fixed point. This is
the **only** graph-level optimization mechanism. The key passes:

```
schedule/rangeify.py  pm_mops              movement ops through INDEX
                      pm_syntactic_sugar   INDEX-on-INDEX fusion
                      pm_store_ranges       assign RANGE loops
                      mop_cleanup           merge RESHAPES, drop no-op PERMUTEs
codegen/simplify.py   pm_load_collapse      collapse tensor-indexed loads
                      pm_split_ranges       split reduce ranges
                      pm_simplify_ranges    range arithmetic
codegen/__init__.py   pm_wmma_add           matmul → WMMA hardware op
                      expander2             vector → scalar expansion
                      pm_remove_vec_dtypes  devectorize
```

### 2. BEAM search — per-kernel, post-fusion, not relevant to us

`codegen/opt/search.py` runs on a single `Scheduler` AST after rangeify has
fused everything. It searches over loop order, upcast amounts, local sizes.
This is local optimization within one GPU kernel. **Not applicable to
Tenstorrent** (the whole TTIR thesis is one deterministic lowering per op, no
search). We ignore this entirely.

There is no graph-level cost model, no autotuning, no ML-based fusion search.

## Our approach: TT PatternMatcher

We implement a `PatternMatcher` that runs on the pre-schedule UOp DAG and
rewrites tinygrad's verbose op subgraphs into TTIR ops. This is registered as
a `graph_rewrite` pass before `transform_to_call` — same mechanism tinygrad's
own passes use. **It must upstream cleanly**, so we use tinygrad's own
`PatternMatcher`/`UPat`/`graph_rewrite` APIs, no fork.

### Op count reality (decode, 2 layers)

The pre-schedule DAG has 1983 nodes, but most are movement plumbing:

| category | count | notes |
|---|---|---|
| movement (RESHAPE+EXPAND+SHRINK+PAD+PERMUTE) | 784 | 40% of nodes; collapse to address math |
| index/buffer (CONST+STORE+BUFFER+COPY+AFTER) | 156 | plumbing |
| bit/integer (AND+OR+SHR+SHL+CMPLT) | 232 | KV-cache + index math |
| RNG (THREEFRY) | 30 | random-init weights in dump, not real inference |
| **compute (ADD+MUL+REDUCE+RECIP+EXP2+SQRT+SIN+CAST+WHERE)** | **445** | the real IR |
| STACK | 96 | KV-cache plumbing |
| BITCAST | 19 | dtype reinterpret |
| CONTIGUOUS | 15 | |
| DETACH | 2 | |
| POW | 1 | |

Of the 445 compute nodes, only **39 are REDUCE** (the matmul/mean/softmax
intent). The rest are elementwise that fuses onto the nearest matmul or
attention kernel.

### Patterns to match (reduces ~1983 → ~80-100 TTIR nodes for 2 layers)

```python
# 1. MATMUL: REDUCE(ADD, axis) ← MUL(EXPAND, EXPAND)
#    ~15-20 surrounding nodes → 1 TTIR matmul(a, b, out_dtype=reduce.dtype)
#    24 instances in 2-layer decode.
UPat(Ops.REDUCE, arg=(Ops.ADD, ...), src=(
    UPat(Ops.MUL, src=(UPat(Ops.EXPAND, name="a"), UPat(Ops.EXPAND, name="b")))
)) → matmul(a.src, b.src, out_dtype=reduce.dtype)

# 2. RMSNORM: the full chain (square → mean → eps → rsqrt → scale → weight)
#    ~10 nodes → 1 TTIR rmsnorm op. 3 instances (2 per-layer + 1 final).

# 3. SOFTMAX: REDUCE(MAX) → SUB → EXP2 → REDUCE(ADD) → RECIP → MUL
#    ~15 nodes → 1 TTIR softmax op. 2 instances.

# 4. SiLU: MUL(x, SIGMOID(x)) or equivalent EXP/RECIP form
#    ~5 nodes → 1 TTIR silu op. 2 instances.

# 5. Movement collapse: RESHAPE←RESHAPE←RESHAPE → one RESHAPE or nothing.
#    (tinygrad already has this in mop_cleanup, but we run it before our lowering
#     so patterns 1-4 see clean subgraphs.)

# 6. RoPE: slice(cos) → MUL + slice(sin) → concat(-x2, x1) → MUL → ADD
#    ~12 nodes → 1 TTIR rope op. 2 instances.
```

After these patterns, the remaining elementwise ADD/MUL/CAST fuse onto the
nearest matmul as epilogues/prologues (the TTIR scheduling pass, §8 of
TTIR.md). That's where the 5-programs-per-layer target is achieved — it's a
scheduling decision, not a pattern-match decision.

### Stability

The fragile part is that tinygrad's UOp representation churns across versions.
Mitigation: match on **structurally stable** subgraphs — `REDUCE(ADD) ←
MUL(EXPAND, EXPAND)` is how matmul is *defined* at the uop level; it won't
change without tinygrad fundamentally reworking its matmul. The surrounding
movement ops (RESHAPE/PERMUTE/EXPAND) are noisier, but we absorb them into the
pattern rather than matching each one individually, so a new movement op in the
chain doesn't break the match.

### What we do NOT do

- **No Tensor API interception.** We don't subclass `Tensor` or override
  `.matmul()` etc. That would require reimplementing every Tensor method and
  would never upstream.
- **No BEAM search.** Tenstorrent is non-tunable (TTIR §9). One deterministic
  lowering per op.
- **No fork.** The PatternMatcher runs through tinygrad's own `graph_rewrite`
  infrastructure. Upstreaming is adding a new `PatternMatcher` + a hook to run
  it before `transform_to_call`.

## Reference dumps

Decoding forward pass (S=1, 2 layers, random weights) captured in
`tools/tg_dumps/`:

```
DECODE_A_preschedule.txt    the UOp DAG at intercept point (529 KB, 1983 nodes)
DECODE_B_prerangeify.txt    the DAG right before rangeify (260 KB)
DECODE_C_kernel_*.txt        83 GPU kernels tinygrad fuses into (post-rangeify)
DECODE_annotated.txt        annotated topo dump + op histogram + REDUCE listing
```

Generated by `tools/tg_decode_dump.py`. The prefill dump (S=4) is in the same
directory from `tools/tg_dump.py`.

tinygrad's own kernel-list analysis for the full 16-layer model is in
`~/ml/llama3-tinygrad/kernel_list.md`.
