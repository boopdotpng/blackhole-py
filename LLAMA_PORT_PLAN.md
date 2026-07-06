# Llama 3.2 1B → Blackhole port plan (blackhole-py)

Working plan for porting `~/ml/llama3-tinygrad/main.py` (Llama 3.2 1B, BS=1, greedy
decode) to hand-written blackhole-py kernels. Covers: the real execution model, the
minimal unique-kernel set, the maximal fusion / launches-per-token ceiling, the
abstractions to add, and a clean bottom-up build order.

Config: `dim=2048, layers=16, n_heads=32, n_kv_heads=8, head_dim=64, mlp=8192,
vocab=128256, eps=1e-5, rope_theta=5e5`. Weights + KV cache bf16, FP32 accumulation.

---

## 0. What a "launch" actually is here (execution model)

- A **Program** = exactly 5 role-kernels (`brisc` reader, `ncrisc` writer, `trisc0`
  unpack, `trisc1` math, `trisc2` pack) + a CB table + a core grid + per-core RTA.
- **One dispatch = one grid-wide GO + DONE.** Kernels contain *on-device loops*
  (see `add1` tile loop, `matmul_peak` K-block loop), so a full GEMV K-reduction is
  **one** launch, not one-per-tile.
- `device.run()` flushes **all queued programs in a single host↔device sync**
  (`cq.submit_ir([...])`). So **host round-trips per token = 1** if you queue the
  whole token then flush once. **Device dispatches per token = number of Programs.**
- **No persistent kernel across tokens.** But **DRAM persists** (weights, KV cache),
  and **RTA updates are recompile-free** (kernel text cached by `id(kernel)`; RTA is
  a tiny separate per-core unicast). So `start_pos` / KV-length change per token for free.
- L1 = **1.5 MiB/core**, ~1.28 MiB usable for CBs.

**Therefore "reduce launches/token" = reduce the number of Programs, and reuse the
same Program objects across tokens updating only RTA.** Target: fewer, fatter fused
programs, all queued and flushed once per token.

---

## 1. Decode is a bandwidth-bound GEMV problem (not matmul_peak)

BS=1, S=1 ⇒ every projection is **M=1 matrix–vector**. Consequences:

- `matmul_peak` (compute-bound square MM) is the **wrong** primitive for decode and
  is currently **unstable at runtime** (times out ≥ 64³ per `status.md`) — note this is
  a *dispatch/runtime* reliability issue, **not** a shape-support gap. Do **not** build
  decode on it. The stable, proven primitive is the **M=1 skinny GEMV** (92.7 GB/s, PCC 0.9999).
- **Shape/padding is already handled** by `plan_matmul`: it `_ceil32`-pads M/K/N to tile
  multiples, does ragged-core allocation + subblock search + L1 fitting, and exposes
  **bf16-in / fp32-DST-accumulate** via `configure_numeric_path(fp32_dest_acc=True)`
  (Float32 intermediate + packer L1 acc). Every Llama projection dim is already a clean
  multiple of 32 (2048, 3072, 512, 8192, 128256; head_dim 64 = 2 tiles) → **no projection
  padding needed; you plug in numbers.** The only real padding case is **attention along
  `T`** (KV length is not tile-aligned) — pad T to 32 and mask the tail in softmax.
- Dominant cost = **weights streamed from DRAM (~2.3 GB/token)** + **KV cache**
  (grows to ~256 MiB/token at T=8192). Decode tok/s ≈ DRAM_BW / (weight+KV bytes).
- Everything else — RMSNorm, RoPE, softmax, SiLU, residual — is cheap SFPU that must
  ride as a **fused prologue/epilogue on a GEMV**, never its own DRAM round-trip.
- **Prefill (S>1)** is the matmul-bound path (needs a stable square matmul + causal
  mask via compare/select). Defer it; it is a separate milestone.

---

## 1b. Precision policy (storage bf16, compute fp32 where it matters)

The SFPU is **internally fp32** (LRegs are 32-bit), and the FPU matmul can accumulate
in fp32 DST — so "storage bf16, math fp32" is free where we need it. Per-op policy:

| Op | Input/weight storage | Compute / accumulate | Output storage |
|---|---|---|---|
| GEMV / matmul (QKV, O, gate/up, down, lm_head) | bf16 | **fp32 DST acc** (`fp32_dest_acc=True`) | bf16 |
| RMSNorm mean-of-squares + rsqrt | bf16 x | **fp32** (sum-reduce-32 + rsqrt in LRegs) | scale applied in fp32, store bf16 |
| RoPE | bf16 q/k, **fp32 cos/sin** | **fp32** rotation | k→bf16 (cache), q→fp32 in scratch (no DRAM downcast needed) |
| Attention scores `q·kᵀ` | bf16 q/k | **fp32 acc, keep score tensor fp32** | fp32 (do not downcast before softmax) |
| Softmax (max/exp/sum/recip) | fp32 scores | **fp32** throughout | fp32 probs (never materialized to DRAM) |
| Attention `probs·V` | fp32 probs, bf16 V | **fp32 acc** | bf16 attn_out |
| SiLU·up | bf16 gate/up | fp32 SFPU | bf16 hidden |
| residual add | bf16 | fp32 add | bf16 (or keep fp32 on-chip while local) |

Note: `fp32_dest_acc=True` **halves DST capacity** (8 tiles instead of 16, 4 per half) —
fine for M=1 GEMV (tiny output) and per-head attention, but it constrains fused-subblock
size, so size epilogues to fit one DST half.

## 2. Honest current-state inventory (what's written vs what works)

Read from code + `boop-docs/microbenching/status.md` (job IDs are *historical* claims,
not re-verified here). Trust column is my recommendation.

| Component | Where | Claimed state | Trust / action |
|---|---|---|---|
| eltwise copy/add scaffold | `examples/add1.py` | RUNS | ✅ trusted base scaffold |
| square matmul | `examples/matmul_peak.py` | **UNSTABLE** (timeout ≥64³) | ⚠️ reference only; not the decode path |
| **skinny GEMV M=1** | `microbench_skinny_gemv.py` | RUNS 92.7 GB/s, PCC .9999 | ✅ **the decode workhorse** — promote into `blackhole-py/` |
| SFPU seqs: exp/recip/sigmoid/silu, sum-reduce-32, rowmax, argmax-rowmax, `rope_rotate_row_seq` | `ttk/sfpu.py` | device-validated per comments | ✅ trust the sequences (keep) |
| rsqrt (RMSNorm) | `ttk/sfpu.py:emit_rsqrt` | **near-unit only** | ⚠️ must extend to wide range (Newton + exponent seed) |
| argmax index | `microbench_sfpu_argmax.py` | value ✅, single-lane index **XFAIL** | ⚠️ finish index reduction |
| RMSNorm | `microbench_rmsnorm_inv.py` | RUNS, 3 launches, rel 3e-4 | ⚠️ correct but 3 launches → fold to a GEMV prologue |
| RoPE + K scatter | `microbench_rope_k_scatter.py` | RUNS 14.8 µs | 🔁 rebuild as QKV epilogue+writer |
| softmax row | `microbench_softmax.py` | RUNS 2746 cyc/tile | 🔁 rebuild inside flash attention |
| fusion sketches: `rmsnorm_gemv`, `rmsnorm_scale_gemv`, `qkv_kstage_rope_scatter`, `attention_q_rope_stage` | `boop-docs/microbenching/matmul/` | **"separate launches on purpose"**, staging proofs | ❌ do **not** trust for perf/precision; treat as design notes, rebuild |
| movement/layout (tilize/untilize/reshape/permute) | — | tilize **times out**, untilize host-only | ❌ missing; design layouts to avoid, add minimal tilize where forced |
| compare/select (masks) | — | MISSING | ❌ needed for **prefill** causal mask only (decode has no mask) |
| cross-core + multi-tile/hidden-dim reductions | — | PARTIAL | ⚠️ RMSNorm(2048)/softmax(T) need these; the per-core-redundant trick avoids cross-core (see §4) |

**Recommendation:** quarantine the `boop-docs/microbenching/` llama *fusion* scripts as
design sketches (they are explicitly staged, not fused/fast, and several are
unverified). Keep as trusted seeds: `ttk/sfpu.py` sequences, `examples/add1.py`,
`examples/matmul_peak.py` (as square-MM reference), and the skinny-GEMV. Rebuild the
llama kernels cleanly under `blackhole-py/` on top of the Tensor abstraction (§5).
Do **not** delete anything until we've re-run the key ones on device to confirm what
still passes (§6 step 0).

---

## 3. The minimal unique-kernel set

The whole model is a handful of **parameterized** programs; everything else is RTA:

- **K1 — GEMV** `y[N] = x[1,K] @ W[K,N]` with pluggable **prologue** (RMSNorm-scale)
  and **epilogue** (SiLU·mul, residual-add, scale). This single program covers
  **QKV, O, gate/up, down, lm_head** — they differ only by (K, N, weight addr,
  epilogue id) in RTA.
- **K2 — RoPE + KV-scatter**: rotate q,k by cos/sin[start_pos]; write k,v tiles to the
  KV-cache DRAM buffers at `start_pos`.
- **K3 — Flash decode attention**: per q-head, stream K/V cache `[0:T]`, `q·kᵀ·scale`,
  online (streaming) softmax, `·V` → attn_out. GQA via `kv_head = h // 4`. No mask.
- **K4 — Embedding gather**: copy one 2048-row from the embed table DRAM → activation
  scratch (pure NoC, no compute).
- **K5 — Argmax** over logits (128256) → token id (rowmax value + index; ideally folded
  into the lm_head epilogue as a streaming best-(val,idx)).
- **K6 — tilize/untilize** (only if a layout transition is unavoidable; aim to design
  DRAM/L1 layouts so it isn't needed in the hot loop).

That's **~5–6 unique kernel programs**. Prefill later adds a square-matmul (K1') and a
causal-mask compare/select.

---

## 4. Maximal fusion & launches-per-token

**Per-layer max-fusion (each bullet = one Program):**

1. **norm + QKV + RoPE + KVwrite** — RMSNorm-scale prologue on x; fused
   `W_qkv[2048, 3072]` (q2048‖k512‖v512); RoPE SFPU epilogue on q,k; writer scatters
   k,v into the cache and q into scratch.
2. **flash attention** → attn_out[2048].
3. **O-proj GEMV + residual-add** epilogue.
4. **norm + gate/up + SiLU·up** — RMSNorm-scale prologue; fused `W_gu[2048, 16384]`
   (gate8192‖up8192); `silu(gate)*up` SFPU epilogue → hidden[8192].
5. **down GEMV + residual-add** epilogue.

**Why the boundaries exist:** each GEMV **shards its N output across cores**; the next
stage needs the **full vector as a broadcast in0** → a shard→broadcast (all-gather)
transition is a natural program boundary. That gives **5 programs/layer**.

**Fusion rules that make this legal on TT** (from `boop-docs/kernel-dev/kernel-fusion.md`):

- FPU matmul result lands in **DST**; an SFPU epilogue reads/writes the **same DST** →
  no L1 round-trip. Do all math between `tile_regs_acquire/commit`, pack once.
- **RMSNorm reduction over K=2048 is per-core-redundant**: in a GEMV, in0 (the M=1 row)
  is broadcast to every core, so each core already holds the full x and can compute
  `inv_rms` locally — **no cross-core reduction, free prologue**.
- residual-add, RoPE, SiLU·mul, scale-by-inv_rms are all SFPU-on-DST epi/prologues.
- DST capacity: 16 tiles (`fp32_dest_acc=false`) / 8 (true); keep the fused subblock in one half.

**Launches per token (staged max-fusion):**

```
embedding            1   (or fold into layer-0 norm reader → 0)
16 layers × 5       80
final norm+lm_head   1   (fused)
argmax               1   (or fold into lm_head epilogue → 0)
--------------------------------
≈ 82 device dispatches, 1 host flush     (vs tinygrad's 216 Metal kernels)
```

**Aspirational ceilings (later, higher risk):**

- On-core **NoC all-gather between stages** (matmul_peak already multicasts) collapses
  the 5 per-layer boundaries → **1–2 programs/layer**.
- Full **decode megakernel**: one Program with an on-device loop over 16 layers, weights
  streamed from DRAM via an RTA address table, KV in DRAM → approaches **1 dispatch/token**.
  Highest complexity; do last, only after the staged path is correct and measured.

---

## 5. Abstractions to add to blackhole-py

Today every kernel hardcodes shapes/addresses. Add a thin metadata + op-builder layer
so shapes/addrs come from tensors and RTA is derived, not hand-written:

- **`TileTensor`** — dtype, logical shape, tile-grid `(Rt, Ct)`, DRAM buffer + base addr,
  bank/interleave layout; methods `tile_addr(rt,ct)`, `num_tiles`, row/col strides.
  Kernels/op-builders take `TileTensor`s; RTA is generated from metadata.
- **`DramArena`** — named persistent buffers over `device.dram.alloc`: per-layer weight
  `TileTensor`s (loaded/tilized once at init), activation scratch **ping-pong** (A/B for
  2048 and 8192 vectors), logits scratch.
- **`KVCache(layer)`** — holds k/v DRAM `TileTensor`s `(8, 8192, 64)` bf16, tracks
  `length`; `.append(k,v,pos)` → writer RTA (dest tile = f(pos)); `.view(T)` → attention
  reader RTA. Persists in DRAM across tokens; only `pos`/`T` change via RTA.
- **Weights registry** — HF name → `TileTensor`; loader tilizes bf16 weights to DRAM once.
- **Op builders** — `gemv(y, x, W, prologue=, epilogue=)`, `rope_kv(...)`,
  `flash_attn(...)` each return a `Program` with RTA derived from the tensors. A
  **`DecodeGraph`** builds the ~82 programs **once**, then each token updates only
  `(start_pos, T)` RTAs and flushes — exactly matching the recompile-free RTA path.

This is what turns "reduce launches" from per-kernel hand-tuning into a graph-level
decision (choose `gemv(epilogue=SILU_MUL)` vs a separate program).

---

## 6. Clean build order (forward-pass order, each with a device check)

Two things run first as a foundation, then we walk the model front-to-back. Every step
ends with a device readback validated against numpy / HF / tinygrad `main.py`.

**Step 0 — Foundation**
- Verify ground truth: re-run key existing benches on device via `tt-device-queue`
  (skinny GEMV, sfpu transcendental/reduce, rmsnorm_inv, rope_k_scatter, softmax, argmax);
  record actual PCC/latency. *Then* decide deletions.
- Add `TileTensor` + `DramArena` + host tilize/untilize with a device readback roundtrip.
- One-time init buffers: tilize+upload all bf16 weights to DRAM; **precompute cos/sin
  RoPE tables on host and upload** (8192×64, ~2 MiB). *(On-device table generation needs
  SFPU sin/cos, which is missing — build it later as an optional primitive, not on the
  bring-up critical path.)* Allocate per-layer `KVCache` DRAM buffers.

**Step 1 — Embedding gather (K4).** NoC/DRAM gather of one 2048-row token embedding →
activation scratch. Pure reader/writer, no compute. Validate the row bytes.

**Step 2 — GEMV core (K1).** M=1 skinny GEMV as a first-class op on `TileTensor` with
`fp32_dest_acc`. Reprove 92.7 GB/s + PCC. This is the reused workhorse.

**Step 3 — RMSNorm as a GEMV prologue.** Fold square/sum/rsqrt/scale into the GEMV reader
(per-core-redundant reduction, §4); delete the 3-launch version; extend rsqrt to wide
range. Validate.

**Step 4 — Fused QKV GEMV** (`W_qkv[2048,3072]`) → q,k,v in scratch. Validate.

**Step 5 — RoPE + KV-scatter (K2)** as the QKV epilogue + writer; wire `KVCache.append`
(dest tile = f(start_pos)). Validate rotated k,v landed in cache.

**Step 6 — Flash decode attention (K3).** Single head → 32-head GQA, T padded to 32 with
tail-masked softmax, growing T via RTA. fp32 scores/softmax. Validate vs numpy.

**Step 7 — Close the block.** O-proj+residual → post-attn norm+gate/up+SiLU → down+residual
= one full transformer block. Validate block output vs HF.

**Step 8 — Full model.** 16 blocks + final norm + lm_head GEMV + argmax (K5) → greedy
decode. Validate the token stream vs HF / tinygrad `main.py`. **← end-to-end parity.**

**Step 9 — Launch minimization.** Build all ~82 programs once in a `DecodeGraph`; per token
update only `(start_pos, T)` RTAs and flush once. Measure dispatches/token + tok/s, then
pursue the boundary-collapse fusions (§4 aspirational).

**Step 10 — (later) Prefill** on a stabilized square matmul + causal mask (needs
compare/select). Separate path from decode.

Steps 1–8 are all decode-only and sit entirely on the stable GEMV + SFPU primitives.
```
