# Llama 3.2 1B on Blackhole (p100a) — Port Plan

> **2026-06-09 — POCs deleted, knowledge harvested to `ttk/`.** The round of
> `examples/llama/` kernel POCs (all device-validated at toy sizes, bf16) was
> deleted ahead of a from-scratch restart. Their device-knowledge landed as
> permanent helpers:
> - unpack out-format nibble now derives from operand dtype (the fp16-decoded-
>   as-bf16 root-cause fix) — `ttk/unpack.py::Unpack._out_format`
> - fp32 DST accumulate (Dst32) opt-in — `Unpack.init(fp32_dest=True)` +
>   `Pack.init(fp32_dest=True)` (`ALU_FP32_DEST_BITS`, `pck_dest_rd_ctrl`)
> - runtime format reconfig for mixed-dtype pipelines (fp16 L1-acc bug dodge) —
>   `Unpack.set_format` / `Pack.set_format` / `Math.set_reload_format`
> - SFPU: exp/recip/rsqrt/sigmoid/silu were already in `ttk/sfpu.py`; added
>   `emit_sum_reduce_32`, `emit_horizontal_reduce_max`,
>   `emit_reduce_row_max_tile`, `rope_rotate_row_seq`
> - DRISC gather mechanics live on in the kept `examples/drisc_*` POCs
>
> **Dtype decision: bf16 everywhere** (the HF checkpoint is bf16; fp16 buys no
> decode speed and trips the fp16 packer-L1-acc HW bug). fp32 DST-acc reserved
> for reductions (rmsnorm/softmax/logits).

Goal: port `~/ml/llama3-cuda` (a correctness-first batch-1 CUDA decode path) onto
the from-scratch blackhole-py framework, end to end.

This document is the contract for whoever (human or agent) writes the kernels:
- the **kernels** we need (1:1 with the CUDA),
- the **low-level Tensix/SFPU ops** each kernel requires and which we still need
  worked examples / microbenches for,
- a **PyTorch-syntax reference** for every kernel so you can write and validate
  the math before fighting the hardware.

---

## 0. The single most important fact: batch-1 decode is memory-bound

Every weight multiply in decode is a matrix × **vector** (GEMV), because the
activation `x` is one token wide. M (the batch dimension) = 1.

- Arithmetic intensity ≈ `2 / bytes_per_weight` FLOP/byte → **~1 FLOP/byte for bf16**.
  Each weight is read from DRAM, used for one multiply-add, discarded. No reuse.
- Therefore **time/token ≈ (total weight bytes) / (DRAM bandwidth)**. The FPU
  compute ceiling is irrelevant; you read the whole model from DRAM once per token.

| Weight dtype | Model size (~1.24B params) | ~tok/s @ ~500 GB/s |
|---|---|---|
| bf16 | ~2.5 GB | ~200 |
| bfp8 | ~1.25 GB | ~400 |
| bfp4 | ~0.6 GB | ~800 |

Implications:
- `matmul_peak.py` measures the **compute-bound square GEMM** ceiling — decode
  never reaches it. We need a **skinny-GEMV / memory-bound** microbench whose
  metric is "% of peak DRAM bandwidth," swept over fp16/bf16/bfp8/bfp4.
- Weight dtype ≈ decode speed. fp16 and bf16 are both 2 bytes → identical decode
  speed; for more speed later, drop to **bfp8/bfp4**.
- Prefill (processing the prompt) *is* GEMM-shaped and compute-bound, so
  `matmul_peak.py` applies there. Only the per-token decode loop is GEMV.

---

## 0b. Dtype strategy: fp16 storage, fp32 accumulate

**Decision: port in fp16** to mirror the CUDA 1:1 (easiest correctness diff
against the reference). Storage = `Float16` for weights and activation tiles;
**accumulation = fp32**, exactly like the CUDA.

Why the split is mandatory, not optional:
- fp16 has a **5-bit exponent (max ~65504)** — a narrow range. bf16 has the full
  fp32-range exponent. The reductions in this model overflow/underflow fp16:
  RMSNorm sum-of-squares (2048 terms), softmax sum, and logits over the 128k
  vocab. The CUDA keeps `x` (residual stream) and every dot accumulator in
  **fp32** precisely to avoid this. Do the same — never store the residual stream
  or a reduction accumulator in fp16.
- fp16 buys **no decode speedup** over bf16 (both 2 bytes). It is a portability /
  correctness choice only.

Two consequences that change the prerequisite list:
1. **fp32 accumulation becomes blocking.** The Tensix DST holds fp32 and the
   **hardware supports fp32 GEMM accumulation natively** (Dst32 mode + the
   matching unpack/pack-dest config) — it just **hasn't been recreated in this
   framework yet**. This is a framework implementation gap, not a hardware limit.
   bf16's wide exponent would tolerate bf16 accumulation; fp16 does not, so this
   must land before the GEMVs. See "f32-acc GEMM" note below.
2. **The `Float16` hardware path is untested.** Only `Float16_b` (bf16) has ever
   run. fp16 needs different data-format config in unpack/math/pack regs, DST,
   and tilize — it is *not* just swapping the `Dtype` enum. **Smoke-test it
   first** (a `Float16` variant of `add1.py`, then a 1-tile `Float16` matmul with
   fp32 accumulate) before building the stack on it.

### Note: f32-acc GEMM

The hardware already supports fp32 accumulation in the matrix engine — this is a
**framework recreation task, not a hardware feature request**. The path:

- The Tensix **DST register file holds fp32**; `TTMVMUL` can accumulate into it
  in full fp32 (Dst32 mode) rather than the bf16/fp16 dest used by the current
  `matmul_peak.py`.
- What needs (re)building in the framework: enable Dst32 in the math-thread DST
  config, set the pack-dest read config (`PCK_DEST_RD_CTRL` / pack-dest format)
  so PACK reads fp32 out of DST, and keep `TTZEROACC` clearing the fp32 dest
  between output tiles. The unpack side stays fp16 (operands are fp16); only the
  accumulator/dest widens.
- Where it's needed: **every GEMV/GEMM accumulator**, plus the reduction
  accumulators in rmsnorm (sum-of-squares), softmax (sum), and logits — these are
  the spots fp16's range can't hold.

Reference: `matmul_peak.py` is the bf16-dest baseline to fork; the deleted
"FP32 accumulator side quest" notes in `docs/matmul-drisc-5000-progress.md`
describe the same rework.

### Findings (device-validated, `examples/llama/f16_f32acc_matmul.py`)

Forked `matmul_peak.py` (opt-in monkeypatch; peak path untouched). Results on p100a:

- **fp16 operands finally run.** Root cause of the old fp16 NaN/garbage: the
  shared unpacker init (`ttk/unpack.py::_tile_descriptor`) hardcodes the
  `THCON_SEC0_REG2` **out-data-format nibble to bf16 (`0x25` → format 5)**. The
  FPU infers SrcA/SrcB format from it, so fp16 inputs were decoded as bf16. Fix:
  derive that nibble from `dtype.value` (bf16 stays `0x25`; fp16 → `0x21`). This
  same bug almost certainly explains the fp16 NaN seen in `rmsnorm.py`/
  `rope_cache.py` — landing it in `ttk/unpack.py` should unblock fp16 for **all**
  the SFPU/eltwise kernels, not just matmul.
- **fp32 dest-acc is just two boolean bits, not a Float32 format.** Enable via
  `ALU_ACC_CTRL_Fp32_enabled|SFPU_Fp32_enabled` (cfg word 1 bits 29/30 — the
  framework already emits `TTRMWCIB3(Mask=0x60)` here, just with Data=0) plus
  `PCK_DEST_RD_CTRL.Read_32b_data` (+`Round_10b_mant` when packing back to fp16).
  All data-format fields stay Float16. Validated: pcc 0.99996+ for a single
  output tile at every K (64…8192).
- **Multi-K-block fp16 + fp32-acc hits a Blackhole HW bug.** The packer L1
  accumulation path (`llk_pack_reconfig_l1_acc`) is broken for IEEE Float16
  (A-format) — see the git-history `examples/l1_acc_bug.py` reproducer. Workaround
  (from git-history `examples/matmul_peak_f16f16_f32acc.py`): make the cb24 L1-acc
  intermediate a **non-fp16** CB (bf16 or fp32) with per-target packer format
  reconfig. The bf16-intermediate version works for single-output-tile GEMVs at
  all K, but the per-target reconfig still corrupts the 2nd+ **output** tile-row
  (an imperfect stand-in for LLK `pack_reconfig_data_format`/`copy_tile_with_dt`).

**DECISION (for now): GEMVs use fp16 operands + fp16 *dest* accumulate** — this
works at every shape/K (rel_l2 ≈ 0.006, no L1-acc bug, no reconfig) and is enough
for the projection magnitudes (~O(10), no fp16 overflow). True fp32 *dest*-acc is
kept only for the single-tile reductions (rmsnorm/softmax/logits), where single
output tile already passes. **Missing precision to revisit:** multi-output-tile
fp32 dest-acc for the GEMVs (needs the proper non-fp16-cb24 reconfig or full
Float32-cb24 port). Not blocking a first correct fp16 decode.

---

## 1. Model config (Llama 3.2 1B)

```
dim          = 2048      # hidden / model dim
n_layers     = 16
n_heads      = 32        # query heads
n_kv_heads   = 8         # GQA: 4 query heads share 1 kv head
head_dim     = 64        # dim / n_heads
kv_dim       = 512       # n_kv_heads * head_dim
hidden_dim   = 8192      # FFN intermediate (SwiGLU)
vocab_size   = 128256
rms_eps      = 1e-5
rope_theta   = 500000.0  # + Llama-3 frequency scaling (see HF config)
tie_embeddings = True    # output head reuses the embedding matrix
activations  = fp32      # CUDA keeps x in fp32; weights fp16, dot-accumulate fp32
```

The decode loop (per token):

```text
x = embedding[token]                       # fp32 vector, dim
for layer in range(n_layers):
    x = x + attention(rmsnorm(x))
    x = x + mlp(rmsnorm(x))
logits = embedding @ rmsnorm(x)            # tied head
next   = argmax(logits)
```

---

## 2. Kernels we need (1:1 with the CUDA)

Status legend: ✅ have a usable example · ⚠️ partial / wrong regime · ❌ missing.

| # | Kernel | Primitive(s) | Status |
|---|---|---|---|
| 0 | embed | indexed DRAM gather (token → row) | ❌ |
| 1/6/9 | rmsnorm_inv | sum-of-squares **reduction** + **rsqrt** | ❌ reduce, ❌ rsqrt |
| 2 | qkv_gemv_norm | **GEMV** (M=1) + **broadcast mul** (norm_w·inv_rms) | ⚠️ square matmul only; ❌ bcast |
| 3 | rope_cache | **eltwise** mul/add on pairs (cos/sin) + indexed **KV-cache scatter** | ❌ eltwise, ❌ scatter |
| 4 | attention | dot/matmul + **softmax** (max-reduce, **exp**, sum-reduce, recip) + weighted-sum | ❌ softmax, ❌ exp, ❌ reductions |
| 5/8 | proj_residual | GEMV + **eltwise add** (residual) | ❌ eltwise add |
| 7 | gate_up_swiglu | 2× GEMV + **silu** (sigmoid = exp/recip) + **eltwise mul** | ❌ silu, ❌ eltwise mul |
| 10 | logits_norm | large GEMV (vocab=128k) + broadcast | ⚠️ matmul only |
| 11 | argmax | **max reduction with index** (int) | ❌ |

---

## 3. Low-level Tenstorrent ops we need examples for

All opcodes already exist in `dsl.py`; almost none are exercised by a kernel.
`ttk/sfpu.py` (`SfpuScalarOp`, `SfpuTileWalk`, `sfpu_scalar_add`) was **deleted** —
only the `.pyc` remains; recover it as the SFPU scaffold.

| Need | Opcodes / mechanism | Have example? | Used by kernels |
|---|---|---|---|
| SFPU exp | `TTSFPEXEXP` 0x77 / `TTSFPEXMAN` 0x78, or `TTSFPLUT(FP32)` 0x73/0x95 | ❌ (add1 only does `+1.0`) | softmax, silu |
| SFPU reciprocal | `TTSFPARECIP` 0x99 (or Newton via `TTSFPMAD` 0x84) | ❌ | softmax denom, silu, rsqrt |
| SFPU rsqrt | `TTSFPEXMAN`/`TTSFPSETEXP` + Newton, or LUT | ❌ | rmsnorm |
| SFPU sigmoid/silu | compose exp + recip + `TTSFPMUL` 0x86 | ❌ | swiglu |
| SFPU load/op/store path | `TTSFPLOAD` 0x70 / `TTSFPSTORE` 0x72 / `TTSFPADDI` 0x75 | ✅ `examples/add1.py` | scaffold for all SFPU |
| Reduce (sum/max, row/col/scalar) | `TTGMPOOL`/`TTGAPOOL`, `TTDOTPV`, or SFPU-side reduce | ❌ (encoded, unused) | rmsnorm, softmax, argmax |
| Eltwise binary add/mul/sub | `TTELWADD`/`TTELWSUB`/`TTELWMUL` | ❌ (encoded, unused) | residual, swiglu, rope |
| Broadcast eltwise (row/col) | `srcb_bcast` on `TTUNPACR` | ❌ (flag exists, no helper) | rmsnorm scale, attn 1/√d |
| Transpose | `TTTRNSPSRCA/B`, `TTSFPTRANSP` 0x8C | ❌ (host numpy only) | attention Kᵀ |
| Tilize / untilize on device | host `dram.py` helpers today | ⚠️ host only | activation reshaping |
| GEMV / skinny matmul (M=1) | `TTMVMUL` but DRAM-feed-bound dataflow | ⚠️ wrong regime (peak = GEMM) | every projection |
| Indexed gather/scatter | NoC read/write w/ computed address; DRISC DMA | ❌ as a primitive | embed, KV cache |
| bfp8_b weights | not in `Dtype` enum (only bf16, bfp4) | ❌ | all GEMVs (decode speed) |

---

## 4. Microbenches to write (priority order)

These double as the reference implementations the kernel author copies from.

1. **SFPU transcendentals** — throughput/tile for `exp`, `rsqrt`, `recip`,
   `sigmoid`/`silu` (then `gelu`/`tanh`). Recover `ttk/sfpu.py` first. *Unblocks
   rmsnorm + softmax + swiglu in one shot — the highest-leverage item.*
2. **Reduction** — row/col/scalar `sum` and `max`.
3. **Eltwise binary** — `add`/`mul`/`sub` tile-tile.
4. **Broadcast eltwise** — row/col broadcast multiply.
5. **Softmax** — composite (max-reduce → exp → sum-reduce → recip-mul).
6. **Skinny GEMV / memory-bound matmul** — metric is % of peak DRAM bandwidth,
   swept over bf16/bfp8/bfp4. *This predicts real tok/s.*
7. **Embedding gather + KV-cache indexed write** — data movement, not compute.
8. **On-device tilize/untilize.**
9. **Transpose** (`TTTRNSPSRCA/B` / `TTSFPTRANSP`).

---

## 5. Device / functionality gaps for full p100a coverage

| Area | Status | Matters for 1B? |
|---|---|---|
| SFPU op helper library | ❌ deleted (only `.pyc`) | **blocking** |
| reduce/bcast/transpose/eltwise wrappers | ❌ encoded, never emitted | **blocking** |
| **fp16 (`Float16`) path** | ⚠️ enum exists, **never run** (only bf16 exercised) | **blocking — chosen storage dtype; smoke-test first** |
| **fp32-acc GEMM** | ⚠️ **HW-supported, not yet recreated** in framework (Dst32 + pack-dest config) | **blocking — required by fp16 (range), rmsnorm/logits accuracy** |
| `bfp8_b` dtype | ❌ not in `Dtype` enum | later (decode speed; not needed for first correct port) |
| on-device tilize/untilize | ⚠️ host only | medium |
| Tensix column harvesting applied | ⚠️ telemetry read but ignored | only if your part is harvested |
| int compute (argmax index) | ⚠️ enum only | low (index can be host-side) |
| Ethernet / chip-to-chip | ❌ field only | no (single card) |

Already fine — don't spend time here: NoC0/NoC1 unicast+mcast+atomics,
semaphores, CBs, DRAM/GDDR, DRISC DMA feed, fast-dispatch CQ, p100a topology,
emulator backend.

---

## 6. PyTorch-syntax reference for every kernel

Write/validate these in PyTorch first (fp32, batch 1), then port. Variable names
match the CUDA. `x` is the residual stream, shape `[dim]`.

```python
import torch, torch.nn.functional as F

# ---- 0. embedding lookup -------------------------------------------------
# CUDA: embed_kernel
x = embedding[token].float()                 # [dim], embedding: [vocab, dim] fp16

# ---- 1/6/9. RMSNorm inverse scalar --------------------------------------
# CUDA: rmsnorm_inv_kernel  (returns only the scalar inv_rms; scale folded into the GEMV)
def rmsnorm_inv(x, eps=1e-5):
    return torch.rsqrt(x.pow(2).mean() + eps)     # scalar
# normalized vector (what the GEMVs multiply against, folded in):
def normed(x, norm_w, inv_rms):
    return x * norm_w.float() * inv_rms           # [dim]

# ---- 2. fused Q/K/V projection from normalized x ------------------------
# CUDA: qkv_gemv_norm_kernel  (one block per output row; broadcast norm scale)
inv = rmsnorm_inv(x)
xn  = normed(x, attn_norm_w, inv)                 # [dim]
q = (Wq @ xn)                                     # [dim]      = [2048]
k = (Wk @ xn)                                     # [kv_dim]   = [512]
v = (Wv @ xn)                                     # [kv_dim]   = [512]

# ---- 3. RoPE + KV cache append ------------------------------------------
# CUDA: rope_cache_kernel  (rotate pairs (i, i+head_dim/2); scatter into cache)
def rope(t, cos, sin, n_h, head_dim):             # t: [n_h*head_dim]
    t = t.view(n_h, head_dim)
    h = head_dim // 2
    x1, x2 = t[:, :h], t[:, h:]
    out = torch.empty_like(t)
    out[:, :h] = x1 * cos - x2 * sin              # cos/sin: [h] for this pos
    out[:, h:] = x2 * cos + x1 * sin
    return out.reshape(-1)
q = rope(q, cos[pos], sin[pos], n_heads, head_dim)
k = rope(k, cos[pos], sin[pos], n_kv_heads, head_dim)
k_cache[:, pos, :] = k.view(n_kv_heads, head_dim) # scatter at pos
v_cache[:, pos, :] = v.view(n_kv_heads, head_dim)

# ---- 4. fused GQA causal attention --------------------------------------
# CUDA: attention_kernel  (per query head: scores -> softmax -> weighted V)
def attention(q, k_cache, v_cache, pos, n_heads, n_kv_heads, head_dim):
    group = n_heads // n_kv_heads                 # 4
    scale = head_dim ** -0.5
    out = torch.empty(n_heads * head_dim)
    q = q.view(n_heads, head_dim)
    for qh in range(n_heads):
        kvh = qh // group
        K = k_cache[kvh, :pos+1]                  # [pos+1, head_dim]
        V = v_cache[kvh, :pos+1]
        s = (K @ q[qh]) * scale                   # [pos+1]
        p = torch.softmax(s, dim=0)               # max-reduce, exp, sum-reduce, div
        out[qh*head_dim:(qh+1)*head_dim] = p @ V  # [head_dim]
    return out
attn = attention(q, k_cache, v_cache, pos, n_heads, n_kv_heads, head_dim)

# ---- 5/8. output projection + residual ----------------------------------
# CUDA: proj_residual_kernel  (reused for attn-out proj and MLP down proj)
x = x + (Wo @ attn)                               # [dim]

# ---- 7. gate/up projection + SwiGLU -------------------------------------
# CUDA: gate_up_swiglu_kernel  (silu(gate) * up, only tmp materialized)
inv = rmsnorm_inv(x)
xn  = normed(x, mlp_norm_w, inv)
gate = Wgate @ xn                                 # [hidden_dim] = [8192]
up   = Wup   @ xn                                 # [hidden_dim]
tmp  = F.silu(gate) * up                          # silu = g * sigmoid(g)
x = x + (Wdown @ tmp)                             # [dim]   (proj_residual again)

# ---- 10. tied-embedding logits ------------------------------------------
# CUDA: logits_norm_kernel
inv = rmsnorm_inv(x)
xn  = normed(x, final_norm_w, inv)
logits = embedding @ xn                           # [vocab] = [128256]

# ---- 11. argmax ----------------------------------------------------------
# CUDA: argmax_stage1/2_kernel  (two-stage max-with-index reduction)
next_token = int(torch.argmax(logits))
```

---

## 7. Suggested sequencing before launching a kernel-writing agent

0. **Smoke-test the `Float16` path** — a `Float16` `add1.py`, then a 1-tile
   `Float16` matmul with **fp32 accumulate**. This de-risks the chosen dtype and
   the fp32-accumulator rework before anything depends on them. (blocking)
1. Recover `ttk/sfpu.py` from the `.pyc` (SFPU load-op-store walker).
2. Land microbenches #1–#5 (SFPU transcendentals, reduce, eltwise, broadcast,
   softmax) — these become the reference impls the agent copies. All in fp16
   storage / fp32 accumulate.
3. Add the **skinny-GEMV** path (#6) — the real llama compute shape (fp16).
4. Add gather / KV-cache scatter (#7).
5. Now an agent can map `kernels.cu` 1:1 onto these primitives, validating each
   kernel against the PyTorch reference in §6.
6. (later, for speed) add **bfp8_b/bfp4** weights — fp16→block-float is the only
   real decode-speedup lever, since fp16 and bf16 are both 2 bytes.

Reusable assets: `matmul_peak.py` (unpack/math/pack/CB/semaphore/NoC scaffold,
+ prefill GEMM), `add1.py` (SFPU load-op-store skeleton), the DRISC POCs (weight
streaming from GDDR), `microbenching/program_timing_model.py` (perf estimation).
