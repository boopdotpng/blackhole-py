# Llama 3.2 1B on Blackhole (p100a) — Port Plan

> **2026-06-10 — `--fast` host-math path: 11.6 tok/s, 260-token soaks stable.**
> New `examples/llama3.py --fast` keeps only the projection GEMVs on device
> (QKV fused, Wo, fused Gate+Up, Wdown per layer + tied logits; 65 GEMV
> bundles, 198 launches/token); host does RMSNorm/RoPE/KV/attention/SwiGLU/
> residual/argmax. Each projection is one pre-encoded CQ submission
> (sysmem fill -> GEMV -> drain), lowered once and replayed per token.
> Checked PCC 0.9996/argmax ok; 260-token runs at 10.9–11.6 tok/s
> (`7cb9bcfa`, `68ef36c5`). CQ fixes that this surfaced:
> - completion-event payload could publish after the wr-ptr → host now
>   consumes only on event-id match (`cq.py::wait_completion`), and dispatch
>   drains NOC1 before the payload write (`fw/cq.py::cmd_host`).
> - FW `HOST_ISSUE_SIZE`/`COMPLETION_BASE` were hardcoded; now derived from
>   `cq.py` so host/FW layouts can't drift (`CQ_ISSUE_MB` env shrinks the ring
>   to stress wraps; 4 MB ring soaks pass).
> - rare relaunch wedge (a GEMV's core row never reaches DONE, ~1/5k
>   launches) auto-recovers: `Device.recover_dispatch()` resets workers + CQ
>   cores, reuses pinned sysmem, replays the idempotent bundle (~0.7 s).
> - `FAST_SUBMIT_DELAY_US` (default 150) throttles submits; reduces wedge
>   frequency. Wedge root cause is still open; recovery makes it survivable.

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
- Prefill should eventually move back to device as a **batched/chunked path**,
  not as the current per-token decode loop repeated over the prompt. A naive
  device prefill creates one CQ submission storm per prompt token; the future
  path should amortize launch overhead over many prompt positions and write the
  KV cache in chunks.

---

## 0b. Dtype strategy: fp16 storage, fp32 accumulate

> **SUPERSEDED 2026-06-09: port in bf16 everywhere** (HF checkpoint is bf16,
> identical decode speed, dodges the fp16 packer-L1-acc bug, exponent range
> tolerates bf16 accumulation; fp32 DST-acc reserved for reductions). The fp16
> path/notes below kept for the later dtype work only. All 2026-06 microbenches
> are bf16.

~~**Decision: port in fp16**~~ to mirror the CUDA 1:1 (easiest correctness diff
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

Current integration target: keep all per-layer math, activation handoffs,
token-to-embedding flow, and KV-cache mutation device-resident. As a temporary
exception, logits may be read back for host-side greedy argmax/token selection
until an on-device max-with-index reduction exists.

Program-boundary rule for the integrated driver: do not chase a single
everything-kernel. Stable separate programs are acceptable when they line up
with real dataflow boundaries or isolate fragile TRISC/SFPU state. The thing to
eliminate is host arithmetic/host activation traffic in the decode loop; launch
reduction should come from obvious local fusions, BRISC/NOC preambles, and CQ
batching after each candidate has its own microbench soak. For full-history
attention, expect a short program chain: grouped Q/RoPE, one score+KV-stage
program per live history tile, current-tile masking, global softmax stats, and
weighted-V accumulation. Only fuse adjacent pieces when the producer/consumer
contract is simple enough to soak independently.

---

## 2. Kernels we need (1:1 with the CUDA)

Status legend: ✅ have a usable example · ⚠️ partial / wrong regime · ❌ missing.

| # | Kernel | Primitive(s) | Status |
|---|---|---|---|
| 0 | embed | indexed DRAM gather (token → row) | ✅ gather microbench (2026-06-10), byte-exact at full vocab |
| 1/6/9 | rmsnorm_inv | sum-of-squares **reduction** + **rsqrt** | ✅ K=2048 staged device inv_rms proof |
| 2 | qkv_gemv_norm | **GEMV** (M=1) + **broadcast mul** (x·norm_w·inv_rms) | ✅ staged device RMSNorm→GEMV integrated; ⚠️ numerical fidelity gap |
| 3 | rope_cache | **eltwise** mul/add on pairs (cos/sin) + indexed **KV-cache scatter** | ⚠️ V scatter integrated; K QKV-output stage + RoPE scatter proved |
| 4 | attention | dot/matmul + **softmax** (max-reduce, **exp**, sum-reduce, recip) + weighted-sum | ⚠️ opt-in staged device decode integrated; compact GQA path handles the first tile, and full-history attention is integrated for `pos >= 32`; one-layer cross-tile check passes with local copy-fusion, while full-model long-run stability is still open |
| 5/8 | proj_residual | GEMV + **eltwise add** (residual) | ✅ separate device ADD integrated; ✅ device-attention path can feed resident post-add activations forward |
| 7 | gate_up_swiglu | 2× GEMV + **silu** (sigmoid = exp/recip) + **eltwise mul** | ✅ staged device bridge integrated; ⚠️ four extra launches/layer |
| 10 | logits_norm | large GEMV (vocab=128k) + broadcast | ✅ staged device RMSNorm→GEMV integrated; ⚠️ numerical fidelity gap |
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
| SFPU sigmoid/silu | compose exp + recip + `TTSFPMUL` 0x86 | ✅ `microbench_sfpu_transcendental.py`; staged SwiGLU bridge integrated | swiglu |
| SFPU load/op/store path | `TTSFPLOAD` 0x70 / `TTSFPSTORE` 0x72 / `TTSFPADDI` 0x75 | ✅ `examples/add1.py` | scaffold for all SFPU |
| Reduce (sum/max, row/col/scalar) | `TTGMPOOL`/`TTGAPOOL`, `TTDOTPV`, or SFPU-side reduce | ❌ (encoded, unused) | rmsnorm, softmax, argmax |
| Eltwise binary add/mul/sub | `TTELWADD`/`TTELWSUB`/`TTELWMUL` | ✅ residual ADD integrated; mul/sub microbenched | residual, swiglu, rope |
| Broadcast eltwise (row/col) | `srcb_bcast` on `TTUNPACR` | ❌ (flag exists, no helper) | rmsnorm scale, attn 1/√d |
| Transpose | `TTTRNSPSRCA/B`, `TTSFPTRANSP` 0x8C | ❌ (host numpy only) | attention Kᵀ |
| Tilize / untilize on device | host `dram.py` helpers today | ⚠️ host only | activation reshaping |
| GEMV / skinny matmul (M=1) | `TTMVMUL` but DRAM-feed-bound dataflow | ⚠️ wrong regime (peak = GEMM) | every projection |
| Indexed gather/scatter | NoC read/write w/ computed address; DRISC DMA | ✅ 2026-06-10 (gather + scatter microbenches) | embed, KV cache |
| bfp8_b weights | not in `Dtype` enum (only bf16, bfp4) | ❌ | all GEMVs (decode speed) |

---

## 4. Microbenches to write (priority order)

These double as the reference implementations the kernel author copies from.

1. ~~**SFPU transcendentals**~~ DONE 2026-06-09 (`microbench_sfpu_transcendental.py`,
   exp 40 / recip 16 / rsqrt 58 / sigmoid 59 / silu 62 cyc per 32-lane group).
2. ~~**Reduction**~~ DONE 2026-06-09 (`microbench_sfpu_reduce.py`: sum32 51 cyc,
   max8x4 51 cyc, rowmax 293 cyc/tile; helper contracts pinned).
3. ~~**Eltwise binary**~~ DONE 2026-06-09 (`microbench_eltwise_binary.py`,
   add/sub/mul bf16, ~1234 cyc/tile single-core DRAM-bound; mul LoFi ~3% low).
4. ~~**Broadcast eltwise**~~ DONE 2026-06-09 (`microbench_eltwise_bcast.py`,
   row/col/scalar × add/mul all PASS; bcast cost ≈ free vs stream).
5. ~~**Softmax**~~ DONE 2026-06-09 (`microbench_softmax.py`: per-row softmax of
   a 32×32 tile, all-SFPU composite, 2738 cyc/tile = 85.6 cyc/row, math-bound,
   ≈ sum of parts; exposed cb_pop_front eager-ack bug, FIXED same day in
   ttk/cb.py — flow control now blocks correctly at no cost, details in
   microbenching/todo.md).
6. ~~**Skinny GEMV / memory-bound matmul**~~ DONE 2026-06-09 bf16
   (`microbenching/matmul/microbench_skinny_gemv.py`, matmul_peak at M=1 on one
   core row). All 5 llama shapes PASS (pcc ≥0.9999): wqkv_q 86.6 / wqkv_kv 76 /
   ffn_gate 90 / ffn_down 96 / logits 94 GB/s ≈ **30% of 305 GB/s roof →
   ~36 tok/s today**. Bottleneck = 11 column NCRISC readers (1 block in flight);
   10-row grid is slower (82.6, padded-out writes). bfp8/bfp4 sweep still open
   (no dtype). Gotcha: >6 differing programs per session wedges CQ — one
   shape/job.
7. ~~**Embedding gather + KV-cache indexed write**~~ DONE 2026-06-10
   (`microbenching/noc/microbench_embedding_gather.py` — NCRISC, id `lw`'d from
   L1 → `dram_tile_addr_from`, byte-exact at full 128k vocab;
   `microbenching/noc/microbench_embedding_gather_tilized.py` — same
   data-dependent gather but writes row 0 directly into the padded 32×dim
   tilized M=1 GEMV input layout, with padded rows pre-zeroed; PASS at full
   128256×2048 table;
   `microbenching/noc/microbench_kv_scatter.py` — BRISC, pos-indexed 128 B
   writes, byte-exact shuffled sweep, ~14 µs/launch = launch-bound, fold into
   the layer program). Both keep DRAM row-major in the standard 2 KiB-page
   interleave for source tables; tied logits GEMV needs a second tilized table
   copy.
7b. ~~**Fused embedding gather + skinny GEMV**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_embed_gather_gemv.py`): BRISC preamble
   loads token id from device DRAM, gathers the embedding row into the M=1
   tilized A buffer, then releases the normal GEMV TRISCs in the same launch.
   PASS at 2048×256, 2048×512, QKV-sized 2048×3072, and FFN-sized 2048×8192;
   QKV-sized fused launch also passed a 100-run relaunch soak.
   This removes the host `embed_row()` + host-side A-buffer upload boundary for
   the first projection once RMSNorm can produce the GEMV input on device.
   Gotchas: receiver BRISC text and RTA blobs need padding for CQ uniform
   per-core writes; NoC helper temp regs must not alias L1 source/dest regs;
   only write logical K tiles so padded K columns remain zero; gather scratch
   must be placed after the matmul plan's CB footprint because wider GEMVs grow
   CB1/CB16/CB24.
7b2. ~~**Embedding gather into staged RMSNorm inputs**~~ DONE 2026-06-10
   (`microbenching/noc/microbench_embedding_gather_norm_inputs.py`): staged
   bridge for the integrated `DeviceNormGemv` path. Launch 1 gathers the token
   id from device memory into the row-tiled M=1 input layout; launch 2 converts
   those row tiles into the 32-lane SFPU footprint layout used by the staged
   RMS reduction. Llama-width one-token smoke PASS (`68083aaf`), 8-token
   small-table PASS (`a2d9c184`), full-vocab 128256x2048 PASS (`9740fb94`),
   and 100-run one-token soak PASS (`005adf85`, rerun after cleanup
   `b17c69ee`, current byte-exact rerun `a1e59548`). This proves token->embedding can feed both `x_row_buf` and
   `x_rms_buf` without host materialization. One-launch experiment was dropped:
   row-major NoC buffers validated for NoC copies, but RISC halfword lane
   extraction from that raw row was not reliable enough; the staged row-to-
   footprint converter reuses the already-validated tile-layout path. Integrated
   into `examples/llama3.py` for layer-0 QKV's staged RMSNorm inputs as
   `DeviceTokenEmbeddingNormInputs`: one-layer checked decode PASS (`73ce67e1`,
   logits PCC 0.41452, argmax ok, 32 launches/token), full 16-layer
   one-token decode PASS (`c292d5e3`, 347 launches/token, 0.97 tok/s), and full
   16-layer four-token decode survived (`359fdc3b`, 0.96 tok/s). Host still keeps
   an embedding copy for the residual/attention fallback; this specifically
   removes the host materialization for device QKV norm inputs.
7c. ~~**Norm-scale producer into skinny GEMV input**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_normscale_gemv.py`): device row-broadcast
   mul writes `x * norm_scale` into the exact padded, tilized M=1 A buffer that
   skinny GEMV consumes. QKV-sized 2048x3072 PASS (`ad946ad0`) and 100-run
   relaunch soak PASS (`24d91d13`), with A-buffer validation plus GEMV PCC.
   This removes the host `normed()` materialization/upload shape from the path,
   but is still a two-launch bridge and still uses a host-supplied
   `norm_scale = norm_w * inv_rms` vector. Next fuse target: compute the scale
   phase inside the GEMV launch, then replace host `inv_rms` with the device
   sumsq+rsqrt producer.
7c2. ~~**Device RMSNorm inverse scalar**~~ DONE 2026-06-10
   (`microbenching/tensix/microbench_rmsnorm_inv.py`): three staged device
   reductions compute `inv_rms = rsqrt(mean(x*x)+eps)` for K=2048 without host
   arithmetic: 64 sumsq partials, 2 partial sums, final scale+eps+rsqrt.
   Llama-sized smoke PASS (`67eb57de`) and 100-run soak PASS (`2164b729`),
   `inv_rms` rel error 0.000303 vs bf16 host reference. This removes the
   host scalar calculation from the RMSNorm story; the staged bridge below
   wires this scalar into norm-weight/activation scaling without host
   `norm_scale` construction.
7c3. ~~**Staged device RMSNorm into GEMV**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_rmsnorm_scale_gemv.py`): connects the
   staged device `inv_rms` reduction to device row-bcast `x * norm_w`, device
   scalar-bcast `* inv_rms` into the padded tilized M=1 A buffer, then normal
   skinny GEMV. QKV-sized 2048x3072 smoke PASS (`bd36739a`) and 100-run soak
   PASS (`ed6e6de5`), covering 600 launches: A buffer validates, GEMV PCC
   0.999951 / rel_l2 0.011411. This removes the host `norm_scale` calculation
   from the proof path; remaining work is selective launch fusion and
   integration into `examples/llama3.py`. Current bench still stages `x` in
   both RMS-footprint and GEMV-row layouts, so final integration needs a device
   layout handoff. It supersedes the earlier scalar-first
   `microbenching/matmul/microbench_rmsnorm_gemv.py` proof.
7d. ~~**QKV GEMV + V-cache scatter tail**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_qkv_vscatter_gemv.py`): optional
   `matmul_peak` NCRISC output-tile hook lets NCRISC copy selected row-0 output
   tiles from CB16 into the row-major V cache while the normal QKV output write
   is happening. QKV-sized 2048x3072 PASS (`6567db6b`) and 100-run relaunch soak
   PASS (`82d78c68`): GEMV still validates, the V cache row is byte-exact, and
   untouched positions remain zero. `examples/llama3.py` now uses this hook in
   the device QKV wrapper and maintains a per-layer device V cache in parallel
   with the host fallback cache. This is a cheap tail fusion: V needs no RoPE,
   while K still belongs with the future RoPE+K-scatter composite.
   Gotcha: the hook must reload the RTA pointer explicitly because the output
   writer has repurposed `s11` for bank count; `rta_ptr` also clobbers `t0`, so
   keep data-derived tile indices out of `t0..t2` across that call; restore the
   normal 2 KiB output-write NoC state after the two 32 B V-cache writes.
7e. ~~**RoPE + K-cache scatter composite**~~ DONE 2026-06-10
   (`microbenching/tensix/microbench_rope_k_scatter.py`): single-core add1-style
   Tensix pipeline stages one K head plus cos/sin as four SFPU footprints in
   one tile, runs `ttk.sfpu.rope_rotate_row_seq`, then NCRISC compacts the
   rotated x1/x2 footprint lanes into the row-major `k_cache[head,pos]` row.
   Llama-1B K shape (8 heads, head_dim=64, max_seq=64) PASS (`5e5a2630`) and
   100-run relaunch soak PASS (`83b14856`): K cache row validates and untouched
   positions remain zero. This is intentionally the K-side composite boundary,
   not yet a QKV GEMV tail, because K must be rotated before cache mutation.
7e2. ~~**QKV K-output stage into RoPE+K scatter**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_qkv_kstage_rope_scatter.py`): BRISC/NOC
   staging reads the normal QKV GEMV C-buffer K tiles, reads device cos/sin row
   tiles for `pos`, writes the sparse x1/x2/cos/sin SFPU footprint expected by
   the RoPE program, then runs the existing RoPE+K-cache scatter composite.
   Llama-1B K shape PASS (`98f63391`) and 100-run staged-composite soak PASS
   (`bccdc78d`), covering 200 launches: RoPE source footprint validates, K
   cache row validates, and untouched cache positions remain zero. This proves
   the missing K-side device bridge from QKV output layout to cache mutation.
   Integrated into `examples/llama3.py` as a separate two-program path after
   QKV while host attention remains a fallback. One-layer driver `--check` PASS
   (`1495ba74`, 33 launches/token, logits PCC 0.96351, argmax ok) and 4-token
   one-layer `--check` PASS (`cdb835e2`, logits PCC 0.91959..0.96351, argmax
   ok), proving the mutable `pos` RTA relaunch path. Full 16-layer 4-token
   decode survived (`ba896722`) at 0.80 tok/s, 393 launches/token, ~41 ms/token
   device time, but emitted host fallback overflow/NaN warnings; numerical
   fidelity remains unsolved.
7h. ~~**Per-token launch accounting in `examples/llama3.py`**~~ DONE 2026-06-10
   (`--launch-breakdown`): grouped launch counters show the current full
   16-layer decode is dominated by staged RMSNorm, not matmul. Before integrated
   SwiGLU, one-token full-model run PASS (`7c42e7a8`) at 0.79 tok/s,
   393 launches/token: RMS reductions 147, norm-scale bcasts 98, GEMV 84,
   residual adds 32, K-stage 16, K RoPE-scatter 16. After staged device SwiGLU
   integration, full-model one-token run PASS (`f691bde1`) at 0.83 tok/s,
   457 launches/token: RMS reductions 147, norm-scale bcasts 98, GEMV 84,
   SwiGLU 64, residual adds 32, K-stage 16, K RoPE-scatter 16. After sharing
   FFN RMSNorm and fusing K staging as the RoPE-program preamble, current
   full-model one-token run PASS (`7d6f0a4d`) at 0.97 tok/s, 361 launches/token:
   RMS reductions 99, norm-scale bcasts 66, GEMV 84, SwiGLU 64, residual adds
   32, K-stage+RoPE-scatter 16. After fusing row->footprint into the SiLU
   program, full-model one-token run PASS (`986d7f3e`) at 0.96 tok/s,
   345 launches/token: RMS reductions 99, norm-scale bcasts 66, GEMV 84,
   SwiGLU 48, residual adds 32, K-stage+RoPE-scatter 16. After enabling
   token->layer-0-QKV norm-input gather, current full-model one-token run PASS
   (`c292d5e3`) at 0.97 tok/s, 347 launches/token: the same groups plus
   embedding 2. Device time is ~78.0 ms/token while wall time is ~1.04 s/token, so launch/readback/host
   fallback overhead still dominates.
7j. ~~**Attention score + softmax + weighted-V proof**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_attention_scores_softmax.py`): first
   attention bridge for `q[1, head_dim] @ K^T[head_dim, seq] -> scores ->
   softmax(scores) -> probs @ V` using skinny GEMV, the validated softmax
   composite, then a second skinny GEMV for the weighted V sum. Current proof
   keeps `seq=32`, supplies K/V in matmul-friendly layouts, and folds
   `1/sqrt(head_dim)` into the staged K input, so it is not the real live-cache
   attention kernel yet. Score+softmax smoke PASS (`31442e82`, 2 launches,
   15.8 us avg) and 100-run soak PASS (`0199ea72`, 200 launches, 15.4 us avg).
   Full score+softmax+weighted-V smoke PASS (`2c9f74f7`, 3 launches, 15.2 us
   avg) and 100-run soak PASS (`ea6e977d`, 300 launches, 15.3 us avg). A
   separate device scalar-bcast scale stage before softmax repeatedly made the
   following softmax launch time out (`b2be9f81`, `ae264beb`, `1f5ce859`,
   verbose `854b7609`), so the next attention step should either fold scale
   into the score writer or isolate the scaled-score layout/state before wiring
   live row-major K/V caches.
7m. ~~**Attention live KV-cache staging proof**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_attention_k_stage.py`): separate BRISC/NOC
   staging programs read one live tilized KV-cache head (`seq=32`,
   `head_dim=64`). K is transposed into the score GEMV B buffer
   `K^T[dim, seq]`; V is copied into the weighted-V GEMV B buffer
   `V[seq, dim]`. The score GEMV, masked-softmax, and weighted-V GEMV programs
   consume those staged buffers as separate launches. K-only smoke and soak
   PASS (`288d4c6c`/`258eebe4`, earlier `fa731174`/`03ad4cb9`); full KV smoke
   PASS (`aae7ca09`, earlier `68180652`; 5 launches, 17.3/17.4 us avg) and
   100-run soak PASS (`db26fc4e`, earlier `4f0a486d`; 500 launches,
   17.3/17.4 us avg). Current causal path fuses the causal mask into the
   softmax BRISC feeder, keeping the chain at 5 launches:
   K^T stage -> score GEMV -> masked softmax -> V stage -> weighted V.
   Causal smoke PASS (`0476309d`, pos=17, 5 launches, 17.5 us avg), 100-run
   causal soak PASS (`f17a4bc0`, 500 launches, 17.4 us avg), and edge smokes
   PASS at pos=0 (`61f7e34c`) and pos=31 (`37b6d50b`). Staged K^T bytes,
   staged V bytes, scores, causal mask, softmax, and weighted V all PASS.
   Caveats: this live-cache proof is unscaled, one sequence tile only, and does
   not integrate the multi-head/GQA loop yet. Gotcha: a separate eltwise ADD
   mask before softmax reproduced the old post-ADD softmax CQ timeout
   (`dcad483b`), so keep masking in the softmax BRISC feeder.
   Follow-up correction: the Llama driver KV caches are raw row-major pages,
   not the tilized fixture used by the first proof. `microbench_attention_k_stage.py`
   now also has row-major K/V stagers. Row-major causal KV smoke PASS
   (`1527f804`, 5 launches, 19.5 us avg), and the full one-head row-major chain
   PASS/soak below validates the real driver cache layout.
7n. ~~**Attention Q-head staging from QKV C buffer**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_attention_q_stage.py`): BRISC/NOC stages
   one selected Q head from the QKV GEMV output C-buffer into the score GEMV
   A-buffer, then runs score GEMV. This proves the Q operand can come from
   device QKV output without host splitting/readback. Smoke PASS (`97927541`,
   2 launches, 14.5 us avg), 20-run PASS (`58e3e3a5`, 40 launches), 60-run
   PASS (`1e8e1895`, 120 launches), and 100-run retry PASS (`996a5610`, 200
   launches, 14.7 us avg). One prior 100-run attempt timed out late
   (`1f672549`, CQ event 104) but did not reproduce after reset. Caveat:
   this is unrotated Q; the next bridge is Q RoPE into the same attention
   A-buffer, then composing Q-stage/Q-RoPE with the live K/V staged attention
   proof.
7o. ~~**Attention Q-head staging + RoPE into score GEMV A**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_attention_q_rope_stage.py`): staged one Q
   head plus cos/sin into the existing RoPE SFPU footprint, ran RoPE, then used
   a custom NCRISC writer to compact rotated x1/x2 lanes into the score GEMV
   A-buffer. The following score GEMV consumes that A-buffer directly. Smoke
   PASS (`9ebd448e`, 3 launches, 14.5 us avg) and 100-run soak PASS
   (`9904061b`, 300 launches, 14.7 us avg): RoPE source footprint PASS,
   rotated Q A-buffer PASS, scores PASS. Later fused the Q-stage BRISC
   preamble into the Q-RoPE program (`build_q_rope_stage_to_a_program`): smoke
   PASS (`14ffcc47`, 2 launches, 14.7 us avg) and 100-run soak PASS
   (`31716052`, 200 launches, 15.0 us avg). This closes the isolated Q-side
   attention handoff and removes one launch per query head in the integrated
   path.
7p. ~~**Full staged one-head attention proof**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_attention_live_head.py`; supersedes older
   `microbench_attention_full_stage.py` jobs): composes the Q-side and
   live-cache bridges into one device chain for a single query head:
   QKV C Q head -> Q RoPE -> score GEMV A; live K cache -> `K^T`; score GEMV;
   causal masked softmax; live V cache -> `V`; weighted-V GEMV -> context
   head. The weighted-V output writer also hooks row 0 directly into the
   correct full-width `Wo.x_buf` tile slice, so no separate context-copy launch
   is needed. Smoke PASS (`956acf9c`, 7 launches, 16.7 us avg; earlier
   `e413276c`) and 100-run soak PASS (`0b1c6bae`, 700 launches, 16.4 us avg;
   earlier `18740d68`): Q RoPE source PASS, rotated Q A PASS, staged `K^T`
   PASS, staged V PASS, scores PASS, causal mask PASS, softmax PASS,
   weighted V PASS, Wo input placement PASS. Edge smokes PASS for
   q_head=0/kv_head=0,pos=0 (`9a304318`) and q_head=31/kv_head=7,pos=31
   (`c0bb4f14`). This is the strongest attention boundary proof so far.
   Row-major driver-cache reruns also PASS: smoke (`2caf18eb`, 7 launches,
   18.1 us avg), 100-run soak (`fe9d8218`, 700 launches, 17.9 us avg), and
   edge smokes q_head=0,pos=0 (`cce4e98c`) / q_head=31,pos=31 (`d4e4f761`).
   Remaining work: scale placement and cross-tile sequence support.
7q. ~~**All-head staged attention -> Wo input proof**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_attention_all_heads_wo.py`): wraps the
   one-head live-cache chain over all 32 query heads with 8 KV heads, writes
   each weighted-V row directly into the corresponding full-width `Wo.x_buf`
   tile slice, verifies padded K columns/rows stay zero, then runs a real
   `Wo` GEMV from the assembled device buffer. Smoke PASS (`19fa278a`,
   `Wo.N=256`, 225 launches, 16.3 us avg), full-width `Wo.N=2048` smoke PASS
   (`41ef855b`, 225 launches, 18.7 us avg), and 10-run relaunch soak PASS
   (`6ca5bfb2`, 2250 launches, 16.1 us avg). Causal edge smokes PASS at
   pos=0 (`99b2698d`) and pos=31 (`734612a6`). All runs report Wo input row
   PASS, padded K columns zero PASS, padded rows zero PASS, and Wo GEMV
   consumes assembled input PASS (PCC ~0.99995 / rel_l2 ~0.011). This removes
   the need for a separate context-copy kernel. The first-cut integrated path
   started at 176 attention launches/layer after K/V staging reuse; fused
   Q-stage+Q-RoPE brings that to 144 attention launches/layer; fused row-major
   K/V staging brings it to 136 attention launches/layer.
7r. ~~**Opt-in device attention integration**~~ DONE 2026-06-10
   (`examples/llama3.py --device-attention`): replaces the host `attention()`
   call for the first 32-position decode tile with separate stable programs.
   The integrated wrapper stages K/V once per KV head, then reuses those buffers
   across the GQA group. After fusing Q-stage+Q-RoPE and row-major K/V staging,
   the all-head attention path is 136 launches/layer:
   8*(fused K/V stage) + 32*(fused Q-stage/RoPE + score GEMV + masked
   softmax + weighted-V-to-Wo). It writes the assembled context directly into
   `Wo.x_buf`, then calls `Wo.run_prefilled()`. Split-Q one-layer smoke PASS at
   pos=5 (`898148fc`, 208 launches/token, 3.04 tok/s) and 4-token relaunch PASS
   (`fb87f249`, 208 launches/token, ~3.00 tok/s). Fused-Q one-layer smoke PASS
   (`2af2abe6`, 176 launches/token, 3.14 tok/s), and fused-Q one-layer
   four-token relaunch PASS (`a3622288`, 176 launches/token, ~3.16 tok/s).
   Fused-Q+KV one-layer smoke PASS (`3eea8a58`, 168 launches/token,
   attention 136, 3.17 tok/s) and 4-token relaunch PASS (`62f53052`,
   168 launches/token, ~3.19 tok/s).
   Baseline without attention still PASS on the same default-prompt path
   (`07fbbc15`, 32 launches/token, 9.49 tok/s). Full 16-layer split-Q smoke PASS
   (`1630b4cc`, 3163 launches/token, attention 2816, 0.22 tok/s); full
   16-layer fused-Q smoke PASS (`f8bf8ab0`, 2651 launches/token, attention
   2304, 0.23 tok/s, 114 ms device time but 4.4 s wall time).
   Caveats: opt-in only, scores are still unscaled, only pos 0..31 is supported,
   and full 16-layer launch count is too high until the easy fusions below
   land. A one-token pos=0 driver smoke currently times out in the pre-existing
   K-stage/RoPE updater (`1327578a`, `9b778486` with `--device-attention`;
   baseline `2e353ed6`/`f34694d0`), even though the isolated K updater pos=0
   microbench PASSes (`1b9526f0`) and the normal default-prompt pos=5 driver
   path PASSes.
7s. **GQA-group attention sharing + grouped Q/RoPE** IN PROGRESS 2026-06-10
   (`microbenching/matmul/microbench_attention_gqa_group.py`,
   `examples/llama3.py --device-attention`): proves and integrates the next
   launch-count boundary without making attention one program. One KV group now
   runs as one grouped Q-stage/RoPE program that writes four Q rows into the
   score-GEMV A buffer, one fused row-major K/V stage, one grouped score GEMV,
   one four-row masked softmax, and one grouped weighted-V GEMV whose writer
   places the four context rows into `Wo.x_buf`: 5 launches/group, 40
   attention launches/layer. The older split path remains in the microbench via
   `--split-q`: four Q-stage/RoPE launches plus a Q-row assembler, 9
   launches/group.

   Standalone grouped-Q proof PASSes (`bab9024a`, 5 launches, 22.6 us avg;
   edge smokes `109bf359` pos=0 and `3be7312f` pos=31; 100-run/500-launch
   soak `99e85d62`, 22.8 us avg): grouped Q A rows, staged K^T/V, scores,
   causal mask, softmax, weighted V, and Wo placement all PASS. Driver
   one-layer smoke PASSes (`bc716a67`,
   72 launches/token, attention 40, 5.79 tok/s). Full 16-layer one-token smoke
   PASSes (`aed01ad8`, 987 launches/token, attention 640, 0.47 tok/s,
   92.5 ms device time). A later run removed the per-layer host zero-fill of
   `Wo.x_buf` before attention, because grouped attention writes all row-0 head
   slices consumed by the M=1 Wo GEMV. Checked one-layer four-token decode PASS
   (`739d9bb4`, logits argmax ok, 72 launches / 22 submits per token) and
   full 16-layer four-token decode PASS (`f257dee4`, 987 launches / 307 submits
   per token, 0.54 tok/s). Full 16-layer 16-token decode also PASSes after a
   reset (`b2415296`, pos 5..20, 0.54 tok/s, 29.5 s decode wall). A pre-reset
   16-token attempt timed out in `wdown_residual_add` (`800c0017`, event 2196),
   so longer soak is still required before calling this long-running stable.
   Follow-up resident-residual cleanup wires `Wo` residual adds to the row-tiled
   QKV norm input and `Wdown` residual adds to the row-tiled Wgate norm input,
   so those adds no longer upload residual vectors from host. It also drops the
   unnecessary per-run zero of fully-overwritten RMS `partial1` buffers and
   batches CQ submissions for GEMV chunks, RMSNorm+GEMV chains, attention
   groups, projection+residual-add chains, the 3-program SwiGLU bridge, and the
   2-program embedding bridge. Checked one-layer decode PASSes (`982ac893`,
   72 launches / 17 submits per token, argmax ok), and two full 16-layer
   16-token runs PASS back-to-back
   (`2bd62082`, `7c2f925a`, pos 5..20, 987 launches / 242 submits per token,
   0.57 tok/s). One max-first-tile run (`cf5786f8`, steps=27) reached pos 23
   and then timed out in a later QKV RMS/GEMV submission (`event 8121`);
   after reset, a current-tree max-first-tile run PASSed through pos 31
   (`fc6009b2`, 27 generated tokens, 987 launches / 242 submits per token,
   0.57 tok/s). This proves the current first-tile limit can survive a full
   tile once, but cross-tile attention and longer soak are still open.

   Follow-up resident-activation cleanup wires later QKV RMSNorm inputs to the
   previous layer's `Wdown.next_buf`, Wgate RMSNorm inputs to the current
   `Wo.next_buf`, and tied logits RMSNorm inputs to the final `Wdown.next_buf`.
   This removes the decode path's remaining host activation upload boundary for
   those norms, while keeping the kernels as separate staged programs. It adds
   row-tile-to-RMS-footprint converters, so the launch count rises to 1019, but
   avoids cheating by feeding later math from host-computed activation vectors.
   The device-attention decode path no longer computes an unused host embedding
   row or host RoPE table row while device gather/RoPE is active. Checked
   one-layer decode PASSes (`f5025d8d`, `19340d80`, current-tree `27c1f3df`,
   74 launches / 17 submits per token, argmax ok). Full 16-layer one-token
   decode PASSes (`db728ebe`, current-tree `6e15f26b`, 1019 launches /
   242 submits per token, 0.62 tok/s, ~96.8 ms device time). The current tree
   survives a 16-token full decode (`ccad6c63`, pos 5..20, 0.62 tok/s) and
   also survives the whole first decode tile (`9efa0f30`, 27 generated tokens
   through pos 31, 1019 launches / 242 submits per token, 0.62 tok/s).

   Follow-up fused-score cleanup moves the row-major K/V staging program into a
   synchronized preamble on the grouped score GEMV. The safe boundary is:
   grouped Q/RoPE -> score GEMV with NCRISC K/V-stage preamble + BRISC wait ->
   masked softmax -> weighted-V. Standalone fused GQA proof PASSes (`89d6450f`,
   4 launches/group, 25.5 us avg) and 100-run soak PASSes (`84b7c7e3`,
   400 launches, 25.9 us avg). Failed attempts were informative: BRISC-only
   staging raced the score GEMV's B-side reader and produced zero scores, while
   unsynchronized NCRISC staging raced BRISC's matmul CB use. Integrated driver
   checks PASS: one-layer checked decode (`968b0c9a`, 66 launches / 17 submits
   per token, argmax ok) and full 16-layer one-token decode (`8b4640e3`,
   repeated by `a6b232bd`, 891 launches / 242 submits per token, 0.62 tok/s,
   ~95.4 ms device time). Full 16-layer 16-token breakdown PASSes (`a944d11d`,
   pos 5..20, 891 launches / 242 submits per token, 0.63 tok/s). Full
   16-layer first-tile decode PASSes (`70304c02`,
   27 generated tokens through pos 31, 891 launches / 242 submits per token,
   0.63 tok/s, ~95.3 ms device time). One-layer fused-score decode also
   crosses the first sequence tile (`ace1d38a`, 40 generated tokens through
   pos 44, 66 launches / 17 submits per token, 7.29 tok/s), proving the baked
   `seq_start` preambles select later row-major cache tiles. This is still the
   temporary block-local attention fallback beyond pos 31, not full historical
   attention. A full 16-layer cross-tile attempt reached pos 32, then timed
   out on the following token in a later QKV RMS/GEMV submission (`cc7fab00`,
   CQ event 8307), but after reset the same full 16-layer 40-token run PASSes
   through pos 44 (`0b4ce8da`, 891 launches / 242 submits per token,
   0.61 tok/s), and a launch-breakdown run PASSes through pos 33
   (`df25030b`, 0.63 tok/s). A longer multi-block soak also PASSes through
   pos 84 (`c569b1ec`, 80 generated tokens, 891 launches / 242 submits per
   token, 0.62 tok/s). Current-tree restored fused-score checks also PASS:
   one-layer checked decode (`149a3f14`, 66 launches / 17 submits per token,
   argmax ok), full 16-layer one-token breakdown (`3084cf97`, 891 launches /
   242 submits per token, 0.63 tok/s), full 16-layer four-token breakdown
   (`ff8aafc5`, 891 launches / 242 submits per token), and full 16-layer
   16-token soak through pos 20 (`883d3f8d`, 0.60 tok/s). This is a better
   stability baseline, but still uses
   block-local attention past each 32-token tile.

   Follow-up score-scale cleanup folds Llama's `1/sqrt(64)=1/8` into
   row-major K staging, so the score GEMV sees `(K/8)^T` and the softmax feeder
   only handles causal masking. Focused fused row-major K/V proof PASSes
   (`05c16415`, 4 launches, 28.7 us avg) and 100-run soak PASSes (`74150b38`,
   400 launches, 28.8 us avg), with staged K^T bytes, staged V bytes, scores,
   causal mask, softmax, and weighted V all passing. Grouped GQA proof for the
   active driver shape PASSes (`04d22bf1`, fused KV-score preamble,
   `k_scale=2^-3`, 20 runs / 80 launches) with grouped scores, causal mask,
   softmax, weighted V, and Wo placement all passing. Integrated driver checks
   PASS: one-layer checked decode (`99b4588b`, repeated by `8551956e`,
   66 launches / 17 submits per token, argmax ok) and full 16-layer one-token
   decode (`3061047a`, repeated by `17c40912`, 891 launches / 242 submits per
   token, output token changes to `9822`/"France" as expected from scaled
   attention). Current full 16-layer four-token breakdown PASSes (`b03b31a4`,
   891 launches / 242 submits per token, ~99 ms device time/token, 0.22 tok/s
   wall). A 16-token full run (`40fa75e2`) emitted all 16 decode tokens
   through pos 20 at 891 launches / 242 submits and ~99 ms device time/token,
   then was SIGKILLed by the 300 s queue wall timeout before clean process exit
   because that run's model upload/wall time was unusually slow.

   Larger correctness/stability gaps remain: longer full-history attention
   soaks past pos 32, host prefill plus device-cache sync, and host logits
   readback/argmax. `examples/llama3.py --device-attention` now uses
   model-correct full-history attention at positions beyond the first
   32-token tile by default; `--allow-block-local-attention` keeps the older
   block-local debug/stability mode.
   The first cross-tile building block now PASSes in isolation:
   `microbench_attention_gqa_multitile_scores.py` runs grouped Q/RoPE once,
   then one synchronized KV-stage+score GEMV per live history tile, then a
   small current-tile score-mask program writes the `-100` softmax sentinel
   after `pos % 32`. Masked two-tile smoke/soak (`aad41a8d`, `f388379e`) and a
   masked three-tile edge (`9efe0968`) validate multi-tile causal grouped
   scores. The shared row-major K/V stager also now supports explicit
   destination sequence placement and partial-page writeback for prefix
   staging; lower-level two-tile score-only proof PASSes (`a77ab68b`) and
   100-run soak PASSes (`cbff2b33`, 300 launches, 51.3 us avg), with scaled
   K^T, V, and scores validating across a 64-token prefix. A BRISC-only global
   row-max pass over the per-tile score buffers now also PASSes two-tile smoke
   (`d72f6b24`), two-tile soak (`232cb811`, 100 launches), and a three-tile
   edge (`07e4a642`). A separate per-tile SFPU stats producer
   (`microbench_attention_global_softmax_stats.py`) computes tile-local row max
   and `sum(exp(score - row_max))`, with 2-tile smoke/soak (`6b040f67`,
   `af1e49d5`) and 3-tile edge (`317f6f13`) PASSing. A packed-stat SFPU
   combiner (`microbench_attention_global_softmax_combine.py`) now computes
   `global_max=max(tile_max)` and
   `global_sum=sum(tile_sum*exp(tile_max-global_max))`, with 2-tile smoke
   (`9c8fa934`, current rerun `b17216de`), 3-tile smoke (`9f7529f9`,
   current rerun `760ae08d`), and 2-tile 100-run soak (`ac87f411`,
   current rerun `4d735529`) PASSing. Probability scaling from those global
   stats is also proved in
   `microbench_attention_global_softmax_probs.py`: current 2-tile smoke
   (`086ccd25`), 2-tile 100-run soak (`b6025f1d`, 400 launches), and 3-tile
   edge (`e73a16aa`) all PASS with probability rows summing near 1 and padding
   rows cleared. Weighted-V accumulation across per-tile probability/V buffers
   is now proved conservatively in `microbench_attention_multitile_weighted_v.py`:
   current 2-tile smoke (`de85988f`), 2-tile 100-run soak (`26096a12`,
   300 launches), and 3-tile edge (`7c7c4280`) all PASS. A lower-launch
   one-GEMV-across-history tail remains a layout-writer optimization: host-written
   GEMV-A diagnostic PASSes (`28863b33`), but the device probability-tile-list
   to GEMV-A compactor is not correct yet (`580a60b8`). The conservative
   full-history chain is now integrated in `examples/llama3.py` for
   `--device-attention` at `pos >= 32` unless the explicit
   `--allow-block-local-attention` debug flag is passed; one-layer checked
   decode first crossed into the second tile with host argmax ok (`8b3a9cd2`,
   pos32, 162 launches / 17 submits, attention 128 launches). A later
   full-history launch-reduction pass kept the chain split but removed two
   pure copy launches per live tile/KV group: score GEMV mirrors into the
   history score tile list from its output writer, current-tile masking edits
   that history page in place, and weighted-V reads probability tiles directly
   from the full probability tile list via separate A/C layout offsets. The
   updated one-layer checked run PASSes at pos32 (`5ecefba0`): 130 launches /
   17 submits, attention 96 launches, host argmax ok. Full 16-layer decode
   also reached pos32 before that launch-reduction pass (`98514a05`): pos5..31
   stayed on the compact first-tile path at 891 launches / 242 submits and
   ~0.21-0.22 tok/s; pos32 used two live history tiles at 2427 launches /
   242 submits, attention 2048 launches, ~126.6 ms device time, and 0.12 tok/s
   wall. A longer full-model attempt (`01f38d7b`) timed out earlier at pos21 in
   `l5.wup_c0`, so that is compact-path/CQ stability evidence, not a
   full-history failure. Eager full-history program construction remains slow
   (128.9s in the `98514a05` run). Next gates are lazy/on-demand full-history
   program construction, then longer sequence stability runs.
   Keep the attention chain split at real synchronization boundaries; the next
   easy launch reductions should stay local rather than trying to make
   attention one program.

   Experimental row-to-RMS cleanup can fold resident row-buffer conversion into
   the first RMS sumsq reduction as a BRISC preamble (`--fuse-row-to-rms`). The
   default RMS reducer still PASSes (`95c1f7f1`), the fused path one-layer check
   PASSes (`9fa1c912`, 64 launches / 17 submits per token, argmax ok),
   full 16-layer one-token decode PASSes (`18f1eb33`, 859 launches /
   242 submits per token, 0.62 tok/s, ~94.8 ms device time), and a focused
   full-model retry crosses pos 16 (`349f8e9b`, 12 generated tokens,
   859 launches / 242 submits per token, 0.63 tok/s). But two 16-token attempts
   around this change timed out in layer-7 attention (`e6c841d0` at pos 16,
   `674189af` at pos 9), so the fused RMS preamble is gated off by default until
   it soaks cleanly. Current tree also routes the layer-0 embedding row through
   the same `DeviceNormGemv` row-source hook, so `--fuse-row-to-rms` can fold
   that embedding row-to-RMS conversion into the first QKV RMS reducer too;
   focused one-layer checked decode PASSes (`2aa78c0c`, 63 launches /
   17 submits per token, argmax ok). Stable default remains the separate
   row-to-RMS converter and 891 launches/token; one-layer default check PASSes
   (`e100d8f6`, 66 launches / 17 submits per token, argmax ok). A later
   default 16-token run
   also timed out in attention (`88b73829`), so long-soak attention/CQ stability
   remains a live issue even with the RMS preamble gated off.
7f. ~~**Projection GEMV + residual add**~~ DONE 2026-06-10
   (`microbenching/matmul/microbench_residual_gemv.py`): stages projection GEMV
   output in DRAM, then a separate two-source eltwise ADD program streams the
   first GEMV output row plus the residual row and writes the next activation
   buffer. `wo` shape 2048x2048 PASS (`6a2b9170`); `wdown` shape 8192x2048
   PASS (`bfd201ea`) and 100-run relaunch soak PASS (`ebde4d2e`), covering 200
   launches. This removes the host `x = x + projection(...)` arithmetic from
   the proof path while keeping a clean program boundary. Integrated into
   `examples/llama3.py` as `DeviceResidualGemv`; class smoke PASS (`5dc890b4`)
   and residual-only one-layer decode `--check` PASS (`b6972096`, logits PCC
   0.99982, argmax ok). Historical note: this initially read the post-add
   activation back while attention remained a host fallback; the later
   device-attention path can now keep these row-tiled activations resident.
   Wdown can also run from a device-prefilled input buffer produced by staged
   SwiGLU.
7g. **Integrated staged RMSNorm into GEMV.**
   `examples/llama3.py` now uses `DeviceNormGemv` for QKV, Wgate/Wup, and the
   tied logits head in device mode. It runs device inv_rms reduction, device
   norm-weight scaling, device activation scaling into the GEMV A buffer, then
   the existing skinny GEMV. Class smoke PASS (`7e5f873f`, PCC 0.999771,
   rel_l2 0.043849) and 100-run wrapper soak PASS (`e310a033`, 600 launches).
   One-layer driver check survived (`25addcbb`, 31 launches/token, argmax ok)
   but logits PCC dropped to 0.42827 versus the fp32 host golden; 4-token
   one-layer decode without check also survived (`29c3bb5b`, 8.40 tok/s).
   This removes host `rmsnorm_inv()`/`normed()` arithmetic from the integrated
   device path, but the bf16/LoFi staged norm path is not numerically faithful
   enough yet for quality. A scaled-square RMS experiment localized the first
   error: on the token-791 embedding row, unscaled device `inv_rms` was 7.53125
   vs host 59.53367 (`553a658f`); scale-16 improved that to 59.0 and recovered
   one-layer logits PCC to 0.99803 (`27545113`), with a 4-token checked run
   also passing (`c3323f24`). It is not safe enough to enable: scale 16/12/10/8
   produced non-finite output on random large-activation smokes/soaks
   (`e5717bd1`, `224b8b58`, `c8aa97c5`, `45819303`, `dbeeb9e1`). Current
   default remains unscaled for stability (`b6e2f354`, `9fb22998`, `4828bf59`).
   `DeviceNormGemv` exposes `rms_input_scale` as an explicit constructor knob
   for controlled experiments; scale-16 via the constructor reproduces the
   model-row fix (`ca9d9e8a`) but is not used by integrated decode. Next
   correctness target: bounded/adaptive device-side RMS scaling or fp32/higher
   fidelity norm scaling before chasing launch fusion.
7i. ~~**Staged device SwiGLU bridge + integration**~~ DONE 2026-06-10.
   `microbenching/matmul/microbench_swiglu_bridge.py` converts Wgate row-tiled
   GEMV output into the SFPU footprint layout, runs SiLU with the existing
   add1/SFPU pipeline, converts back to row tiles, then multiplies by Wup row
   tiles to produce Wdown's M=1 input layout. Full hidden=8192 smoke PASS
   (`51f26e33`, current rerun `43e1b4f5`) and 100-run soak PASS
   (`d8eba984`, current rerun `360d6696`), covering 400 launches:
   row->footprint PASS, SiLU footprint PASS, SwiGLU row PASS. Integrated into
   `examples/llama3.py` as `DeviceSwiGLU`: the device branch now runs Wgate/Wup
   without host readback, writes Wdown's input buffer on device, and calls
   `DeviceResidualGemv.run_prefilled()`. One-layer checked decode PASS
   (`74944c94`, logits PCC 0.41452, argmax ok, 37 launches/token) and 4-token
   one-layer checked decode PASS (`cd2951a7`, logits PCC 0.41452..0.45147,
   argmax ok, 8.51 tok/s). This removes the integrated host `swiglu(gate, up)`
   arithmetic/readback boundary, at the cost of 4 staged launches per layer.
   Current-tree validation with K-cache updater + device SwiGLU active: one-layer
   checked decode survived (`6943642f`, argmax ok, 37 launches/token),
   4-token one-layer checked decode survived (`43659733`, argmax ok), and full
   16-layer single-token decode survived (`4b5ff0aa`, 457 launches/token,
   0.83 tok/s). Later shared FFN RMSNorm, combined K-stage+RoPE updater, and
   row->SiLU fusion reduce the full 16-layer path to 345 launches/token
   (`986d7f3e`).
7j. ~~**Shared FFN RMSNorm for Wgate/Wup**~~ DONE 2026-06-10.
   Wgate and Wup consume the same `ffn_norm(x)`. `examples/llama3.py` now lets
   Wgate's `DeviceNormGemv` produce the shared normalized M=1 GEMV input buffer,
   then runs Wup's GEMV from that prefilled buffer via `DeviceGemv.run_prefilled`
   instead of recomputing the whole staged RMSNorm stack. One-layer checked
   decode first hit the expected 32 launches/token for three tokens but then CQ
   timed out during a later host DRAM fill (`56f56c89`); after queue reset, the
   same three-token checked run passed cleanly (`257cb9fd`, logits PCC
   0.41452..0.44233, argmax ok, 9.23 tok/s). Full 16-layer one-token launch
   breakdown PASS (`605c7231`): 377 launches/token at 0.97 tok/s, with RMS
   reductions 99, norm-scale bcasts 66, GEMV 84, SwiGLU 64, residual adds 32,
   K-stage 16, K RoPE-scatter 16. Full 16-layer four-token decode also survived
   (`f3b53bb8`) at 0.96 tok/s with 377 launches/token. This removes 80 launches
   per token versus the staged-SwiGLU path. Later row->SiLU fusion cuts the
   current path further; next launch-fusion target is collapse the staged
   RMSNorm producer launches.
7k. ~~**K-stage preamble fused into RoPE scatter**~~ DONE 2026-06-10.
   `microbenching/matmul/microbench_qkv_kstage_rope_scatter.py` now defaults to
   a one-launch combined path: BRISC stages K/cos/sin into the RoPE footprint,
   then releases the existing RoPE+K-cache scatter TRISCs in the same program.
   Standalone combined smoke PASS (`101a751a`, RoPE source footprint PASS, K
   cache row PASS, untouched rows PASS). Integrated `DeviceKCacheUpdater` now
   runs one `k_stage_rope_scatter` program after QKV; one-layer checked decode
   PASS (`05d258db`, 31 launches/token, argmax ok) and full 16-layer one-token
   decode PASS (`7d6f0a4d`, 361 launches/token, 0.97 tok/s). This keeps the
   sensible program boundary: QKV GEMV, K-stage+RoPE cache update, later
   attention. It just removes the pure staging launch.
7l. ~~**SwiGLU row-to-SiLU fusion**~~ DONE 2026-06-10.
   `microbenching/matmul/microbench_swiglu_bridge.py` now defaults to a
   three-launch SwiGLU bridge: BRISC converts Wgate row tiles to the SFPU
   footprint while feeding the SiLU program, then separate programs convert
   footprint->row and multiply by Wup. Standalone hidden=8192 PASS (`fcefdcbe`,
   3 launches; row->footprint PASS, SiLU PASS, SwiGLU row PASS). Integrated
   `DeviceSwiGLU` now uses `row_silu`, `fp_to_row`, `mul`: one-layer checked
   decode PASS (`6a81ce3e`, 30 launches/token, argmax ok), full 16-layer
   one-token decode PASS (`986d7f3e`, 345 launches/token, 0.96 tok/s), and full
   16-layer 4-token decode survived (`68b7ff64`, 0.96 tok/s). A more aggressive
   direct row->SiLU->row composite passed one tile but failed multi-tile
   validation when NCRISC read packed output directly from CB16; keep the raw
   NoC output path plus separate footprint->row conversion for stability.
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
