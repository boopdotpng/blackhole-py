# Blackhole-py Research Direction: Batched Serving, 138-Core Kernel Templates & Cost-Guided Scheduling

This document consolidates the hardware roofline and DRAM/NoC findings on Blackhole p150a, the architecture for batched Orca-style inference serving (targeting Inkling 2 Mini and Llama 3 for OpenCode / coding-agent workloads on 1× and 2× cards), the 138-core P1/P2 kernel template model replacing hand-written 5-core `.ttrv` synchronization, the lightweight analytical planner (`plan()`), and the resident-L1 megakernel / static graph L1 reuse architecture. Llama 3 training and the Tinygrad port contract are retained in Appendices A and B as later milestones.

---

## 1. Hardware Roofline, DRAM Rules & Current Kernel Audit

### Hardware Ceilings (Measured on p150a, `boop-docs/data/`)

| Parameter | Value | Notes |
| --- | --- | --- |
| Worker cores | **138** (14 cols × 10 rows − CQ − DMA) | Cols 0–12 have 10 rows; **col 13 (`x = 16`) has 8 rows** (CQ at `(16,10)`, DMA at `(16,11)`). `cover()` reaches all 138 cores in **1 multicast** via `BRCST_EXCLUDE`. |
| AICLK | **1.35 GHz** | Nominal & wall-clock verified |
| L1 SRAM / core | **1.5 MiB** (`0x180000`) | Shared by activations, CBs, staging rings, `keep` flags |
| `Dst` register file / core | **8 tiles FP32** / **16 tiles BF16** | 32×32 tiles |
| Usable DRAM / card | **34.23 GB** (`8 × 0xFF000000`) | Allocator limit across 8 GDDR6 banks |
| GDDR6 pin bandwidth | **514.6 GB/s** (8 × 64.3 GB/s) | 47.6 B/cyc per controller |
| GDDR6 practical ceiling | **~506 GB/s** (98.5% of pin) | `chip-dram`: ~63.3 GB/s per controller |
| GDDR6 sustained read BW | **506.0 GB/s** (374.8 B/cyc; **508.4 GB/s** core makespan, **98.8% of pin**) | Measured on p150a Card 0 (`stage0_bench.py`, **138 workers**, NoC0, 3-port rotation, staggered, 2 KiB pages, **`cap = 2` in-flight reads/core**; **1.01×** max/median, **1.07×** max/min). At 4 KiB pages: **503.6 GB/s** (`cap = 8`) / **501.9 GB/s** (`cap = 4`) / **498.4 GB/s** (`cap = 2`, 1.03× max/med). Earlier `chip-dram` (117c) was 496 GB/s; `dram-many` (88c, fixed port) was 474.5 GB/s. |
| FPU peak — HiFi2 (BF16/BFP8) | **381.5 TFLOPS** (138c) / **359.4 TF** (130c) | 2,048 FLOP/cyc/core (32 cyc per 32×32×32 tile) |
| FPU peak — LoFi (BFP4) | **763.1 TFLOPS** (138c) / **718.8 TF** (130c) | 4,096 FLOP/cyc/core (16 cyc per 32×32×32 tile) |
| HiFi2 Roofline Ridge Point | **741 FLOP/B** (pin) / **~754 FLOP/B** (506 GB/s) | Arithmetic intensity needed to become compute-bound |
| TT-link (2× 400G, ch 11 + 13) | **49.15 GB/s** per link/dir (**98.3 GB/s** 1-way, **196.6** duplex) | **0.64 µs RTT** (0.32 µs one-way) measured on ERISC1 (`boop-docs/notes/tt_link.md`) |

### Five Mandatory DRAM Rules & NoC Arbitration Reality

1. **All DRAM reads on NoC0, never NoC1.** NoC1 routes y-first, so read responses climb north inside the DRAM columns (`x = 0, 9`) and serialize on shared vertical links (**232 GB/s** vs. **491 GB/s** on NoC0). Writes on NoC1 spread out fine (338 B/c).
2. **Cap per-core in-flight reads (`cap = 2..8`, critical!).** Routers arbitrate per input port round-robin by whole packet. Leaving 138 readers uncapped (`cap = 0`) drops kernel throughput to **489.7 GB/s** with a **7.91×** max/min (**1.65×** max/med) spread. Capping each core to **`cap = 2` in-flight reads** lifts 138-core 2 KiB reads to **506.0 GB/s (98.8% of pin)** and collapses the tail to **1.01× max/median, 1.07× max/min**! (At `R = 42..64` readers, `cap = 8` hits **493–503 GB/s** at **1.03–1.12×** max/med; at `R = 88..138`, `cap = 2..4` hits **501–506 GB/s** at **1.01–1.17×** max/med.)
3. **Spread readers across all 14 columns (row-major), never bunch column-major.** Measured at `R = 28` (2 readers/col): spread = **429.6 GB/s** vs. bunched = **208.8 GB/s** (**2.06× faster!**). At `R = 96`: spread = **481.1 GB/s** uncapped (**501.1 GB/s** with `cap = 4`) vs. bunched = **440.6 GB/s**.
4. **Rotate across all 3 ports of every DRAM bank** (fixed port caps low-`R` throughput; at 138 readers with `cap = 0` all ports saturate, while rotation keeps low-`R` P2 readers balanced).
5. **Never start concurrent streams a multiple of 128 KiB apart, and stagger start banks (`rank & 7`).** Streams matching in bits `0..16` collide on internal GDDR6 banks/rows (−17% at 2 KiB pages, −39% at 1 KiB); offset starts by odd multiples of 256 B (`(2 * core.id + 1) * 256`) and use odd `NT_PITCH`.

**Measured Stage 0 reader scaling & ablations (p150a Card 0, NoC0, rotated + staggered + spread across 14 cols unless noted):**

| Config | `R` | Page | In-flight `cap` | Kernel GB/s | Core-max GB/s | `max/med` | `max/min` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1/col (old prefill) | 14 | 4 KiB | 0 / 8 | 426.7 / 380.5 | 429.4 / 382.6 | 1.09 / 1.00 | 2.45 / 1.00 |
| 2/col **bunched (col-maj)** | 28 | 4 KiB | 0 | **208.8** | 207.8 | 1.46 | 6.02 |
| 2/col **spread (row-maj)** | 28 | 4 KiB | 0 / 8 | **429.6 / 448.1** | 405.0 / 469.5 | 1.46 / 1.04 | 2.18 / 1.09 |
| 3/col spread (P2 sweet spot) | 42 | 4 KiB | 8 | **493.2** | 495.4 | **1.03** | 1.28 |
| 4/col spread (P2 sweet spot) | 56 | 4 KiB | 8 | **496.5** | 498.8 | **1.09** | 1.63 |
| 64 spread | 64 | 4 KiB | 8 | **503.1** | 505.3 | 1.12 | 2.18 |
| 96 **bunched** vs. **spread** | 96 | 4 KiB | 0 / 4 (spread) | 440.6 vs. **501.1** | 447.3 vs. 501.6 | 1.59 vs. **1.04** | 8.72 vs. 1.40 |
| **138 uncapped** | 138 | 4 KiB | 0 | 489.7 | 491.7 | 1.65 | **7.91** |
| **138 paced** | 138 | 4 KiB | 4 / 2 | 501.9 / 498.4 | 504.1 / 503.9 | 1.17 / **1.03** | 1.78 / 1.10 |
| **138 paced (peak)** | 138 | **2 KiB** | **2** | **506.0** | **508.4 (98.8% pin)** | **1.01** | **1.07** |

**What "pacing" means in hardware:** Every NIU tracks live uncompleted reads per transaction ID in hardware register `OUTSTANDING(noc, tid)` (`0xFFB20240 + 4 * tid`). Pacing simply polls `while (OUTSTANDING(tid) >= cap) {}` before firing the next read so each core keeps at most `cap` (2–8) requests in flight at once. Without pacing, fast cores near the DRAM columns keep their router input ports continuously full and starve upstream cores via round-robin packet arbitration (7.91× spread); with `cap = 2..4`, each core pauses briefly once its 2–4 slots are full, letting upstream cores take turns while all 138 cores collectively still keep `138 × 2 = 276` requests in flight—more than enough to saturate all 8 GDDR6 banks at 98.8% of pin rate!
- **Two-sided pacing rule (verified via end-to-end `model_rates.py` A/B sweep on Card 0):**
  - **Low-`R` readers (`R = 13..28`) must NOT use `cap = 2`:** globally forcing `cap = 2` cut 13-reader prefill by **17–23%** (1B `34,382 → 28,509`, 8B-BFP8 `9,370 → 7,827`, 8B-BF16 `6,763 → 5,197` tok/s) because `13 × 2 = 26` total requests cannot hide DRAM RTT (Little's law).
  - **Existing decode kernels are already accidentally capped or *under*-pipelined:** Llama BF16 decode issues 1 row (2–4 pages) + `noc.wait` per `noc.read` (`1b` edged up `163.6 → 165.4 tok/s` at `cap = 2` from `down.ttrv`'s 8-page rows; `8b-bf16` flat at `30.4 → 30.5`); `8b-bfp8` (`BATCH=16, GROUP=8`) already waits every 2 pages (`46.8 → 46.7`); and `examples/inkling/experts.ttrv` (`BATCH=GROUP=8`) waits after **every single page (`cap = 1`)**. Pacing pays off when paired with **continuous multi-block streaming** (no stop-and-go `noc.wait` per block) at high `R` (`88..138` → `cap = 2..4`; `42..64` → `cap = 8`).

**Measured Stage 0 dispatch multicast overhead (p150a Card 0, 138 workers, 5 roles × 1 KiB):**

| Install rects (`d[6]` transfers) | `spin = 0` period (unhidden) | `spin = 15k` (~11 µs) | `spin = 60k` (~44 µs) |
| ---: | ---: | ---: | ---: |
| 1 (6) | 2,848 cyc | 16,710 cyc | 61,710 cyc |
| 2 (12) | 3,507 cyc (+659) | 16,722 cyc | 61,722 cyc |
| 4 (24) | 4,825 cyc | 16,710 cyc | 61,710 cyc |
| 8 (48) | 7,460 cyc | 16,710 cyc | 61,710 cyc |
| 14 (84) | 11,409 cyc | **16,709 cyc (0 overhead)** | 61,709 cyc |
| 28 (168) | 20,633 cyc | 20,633 cyc | **61,711 cyc (+1 cyc)** |

- Synchronous `mcast_launch` (params + GO on the critical path): **1 rect = 2,848 cyc**, **2 rects = 3,040 cyc** (**+192 cycles / ~0.14 µs** per extra launch rect).

**Measured Stage 0 data multicast across `x = 8, 9` gap:** Both **NoC0** `(1,2) → (16,2)` and **NoC1** `(16,2) → (1,2)` single-rectangle 4 KiB data multicasts delivered bit-exact data to **14/14 workers** across columns 8 and 9. Splitting `row_mcast` at `x = 7` is **not required**.

### Measured vs. Theoretical Throughput (1× p150a)

#### Batch-1 Decode (`seq ≈ 336`, memory-bandwidth bound)

| Model | Bytes / tok (Weights + LM + KV) | Measured (tok/s) | Effective BW | Measured BW Roof (496 GB/s) | Pin Roof (514.6 GB/s) | % of 496 GB/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Llama 3.2 1B (BF16) | 2.48 GB | **163.7** | 406 GB/s | 200.0 | 207.5 | 81.9% |
| Llama 3 8B (BF16) | 15.05 GB | **30.5** | 459 GB/s | 33.0 | 34.2 | **92.5%** |
| Llama 3 8B (BFP8_B) | 8.02 GB | **46.8** | 375 GB/s | 61.8 | 64.2 | 75.7% |
| Inkling 2 Mini (BFP8_B, 1×) | 5.26 GB | **57.0** | 300 GB/s | 94.3 | 97.8 | 60.4% |
| Inkling 2 Mini (BFP8_B, 2× TP) | 2.63 GB/card | **82.1** | 216 GB/s/card | ~188 | ~196 | 43.6% |

#### Prefill (`S = 320` tokens for Llama; Inkling currently token-by-token)

| Model | Weight Bytes | AI at `S=320` | Measured (tok/s) | Achieved TF / BW | `S=320` BW Roof (496 GB/s) | HiFi2 Compute Peak (138c) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Llama 3.2 1B (BF16) | 1.95 GB | 320 FLOP/B | **34,392** | 67.7 TF · 209 GB/s | 81,560 | 193,959 |
| Llama 3 8B (BF16) | 13.96 GB | 320 FLOP/B | **6,748** | 94.8 TF · 294 GB/s | 11,371 | 27,170 |
| Llama 3 8B (BFP8_B) | 7.42 GB | 602 FLOP/B | **9,370** | 131.6 TF · 217 GB/s | 21,405 | 27,170 |
| Inkling 2 Mini (BFP8_B, 1×) | 53.4 GB (all 128 exp × 48 passes) | ~104 FLOP/B at `S=320` | **61** (serial) | — | 2,970 (`S=320`) / 19k (`S=2048`) | 43,644 (ridge `S ≈ 4.6k`) |

### Inkling 2 Mini VRAM & MoE Batching Analysis (BFP8_B)

Inkling 2 Mini runs 24 layers with the middle 12 layers looped 3× (**48 layer passes**: 8 full-attention passes on layers 5/11/17/23 + 40 sliding-window passes with window 1024), routing 8 of 128 experts per token (`8.58 MB`/expert in BFP8).

- **Weights:** **28.54 GB** on 1× card (leaving **5.29 GB** free after ~0.4 GB activations/metadata) vs. **14.77 GB/card** on 2× TP (**38.1 GB** free across both cards).
- **Per-sequence state:** KV is 4 KiB/tok/pass in BF16 (2.1 KiB in BFP8); conv rings (`kvconv`, `attn_sconv`, `mlp_sconv`) add 2.6 MB/seq; `attn_res` block states are ephemeral (~147 KB/in-flight token). Currently `examples/inkling.py` wastes memory by allocating full-length KV on all 40 sliding passes and caps context at 8,192 (missing per-row log-scaling `tau`):

| Context | Current (48 full) | Sliding rings + paged full (BF16 KV) | Sliding rings + paged full (BFP8 KV) | Max `B` 1× (BF16 / BFP8) | Max `B` 2× TP (BF16 / BFP8) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2k | 405 MB | 243 MB | 130 MB | 21 / 40 | 157 / 292 |
| 8k | 1,613 MB | 444 MB | 237 MB | **11** / 22 | **85** / 160 |
| 16k | 3.2 GB | 712 MB | 380 MB | 7 / 13 | 53 / 100 |
| 32k | 6.4 GB | 1,249 MB | 665 MB | **4** / 7 | **30** / 57 |

- **The MoE batching valley (`ctx = 8k`, uniform routing $E(B) = 128(1 - (15/16)^B)$, fitted with 85% of 474.5 GB/s + 4.1 ms / 5.4 ms fixed overhead; real routing skew makes the valley slightly shallower):**

| `B` | Distinct Experts $E(B)$ | GB/step (1× / per card 2×) | 1× per-user / total (tok/s) | 2× TP per-user / total (tok/s) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 8 | 5.8 / 3.0 | **54** / 54 | **78** / 78 |
| 4 | 29 | 15.8 / 8.0 | 23 / 92 | 40 / 159 |
| 8 | 52 | 26.8 / 13.5 | 14 / 113 | 26 / 206 |
| 16 | 82 | 43 / 21.6 | 9 / 144 *(OOM 1×)* | 17 / 271 |
| 32 | 112 | 62 / 31 | 6.3 / 202 *(OOM 1×)* | 12 / 387 |
| 64 | 126 | 82 / 41 | 4.8 / 308 *(OOM 1×)* | 9.3 / 596 |
| 128 | 128 | 111 / 56 | 3.6 / 457 *(OOM 1×)* | 7.0 / 892 *(needs BFP8 KV)* |

**Takeaway:** Going from `B = 1` to `B = 8` multiplies active experts 6.5×, cutting per-user speed ~3.8× for only 2.1× aggregate gain. Total throughput only scales linearly past `B ≳ 64` (impossible on 1× at 8k). On 1× card, the ~11-sequence cap sits right inside the worst part of the MoE valley.

### The P1 vs. P2 Crossover: When "DRAM Sender + Compute-Only" Pays Off

At 496 GB/s across 138 cores (**2.66 B/cycle/core**), fetching one weight tile takes **409 cycles (BFP8)**, **769 cycles (BF16)**, or **216 cycles (BFP4)**, while one HiFi2 tile-matmul per 32-row activation panel takes **32 cycles** (16 cycles LoFi on BFP4). Therefore:

> **Regime P1 (Direct Weight Streaming, zero compute-only cores)** wins whenever activation panels per weight tile $P \le P^*$, where **$P^* \approx 6\text{–}13$ panels (~200–400 tokens)** for BFP8/BFP4 and **$12\text{–}24$ panels** for BF16 (lower bound assumes 50% FPU efficiency).
>
> **Regime P2 (DRAM Sender + Compute-Only Multicast Receivers)** pays off **only above $P^*$** — i.e. prefill and large dense batches (`B > ~400`).

**Crucial consequence for Inkling:** Even at `B = 512`, each of the 128 experts averages only ~32 tokens ($P = 1$ panel). Every Inkling MoE decode matmul stays deep inside **P1**; splitting cores into "DRAM sender + compute-only receivers" for Inkling decode experts slows it down by adding NoC1 traffic without reducing DRAM bytes.

### Key Bottlenecks in Current Kernels

1. **Inkling prefill runs serially at 61 tok/s** (~8 min for a 30k coding prompt) because `inkling.py` feeds prompts through the decode graph one token at a time. Tiled `T = 2048` chunked prefill brings 1× to **~6.5–13k tok/s** and 2× TP to **~24k tok/s** (2–4 s for 20k tokens).
2. **Inkling decode pays ~4.1 ms (1×) / ~5.4 ms (2×) fixed launch overhead** across ~770–800 launches/token (~5–6% at B=1, larger on 2× TP due to ~96 separate TT-link sync launches).
3. **Llama BF16 decode/prefill duplicates weights (~29 GB)** because `examples/llama3/*.ttrv` uses row-major `elwmul` + SFPU dot-product instead of face-tiled weights. Unifying on `kn_tiles_32x32_v1` eliminates the duplicate copy.
4. **Hand-written 5-core `.ttrv` has hit its complexity wall:** `examples/prefill/projection.ttrv` (411 lines) still has the `STAGES = 2` overwrite race and `RESIDUAL` BF16/BFP8 unpacker-config race, and only accumulates 1×1 `Dst` tiles on 130 cores (leaving col 13 and 6–7 FP32 `Dst` tiles idle).

---

## 2. Batched Serving, Orca Continuous Batching & OpenCode

### Multi-Card Topology: 2× TP vs. 2× EP vs. 1P+1D

- **Inkling 2 Mini (~28.5 GB) / Qwen3.8-27B / Nanbeige-33B → 2× Tensor Parallel (TP):**
  - Halves weights per card (**14.8 GB**), expanding KV capacity ~7–9× (**38.1 GB** vs. 5.3 GB) and doubling both single-user decode (~94 → ~188 tok/s ceiling) and prefill (~24k tok/s at `T = 2048`).
  - **Why not 2× Expert Parallel (EP)?** Same memory and AllReduce size, but at `B = 1` the 8 active experts split unevenly (~5.1 vs. 2.9 on the busier card), slowing decode ~15%. EP only pays off at ≥ 4 cards.
  - **Why not 1P+1D disaggregated?** Even though dual-400G TT-link (98.3 GB/s) transfers KV in ~1–2 ms, duplicating 28.5 GB weights leaves only ~5.3 GB on the decode card and leaves half the hardware idle during single-user OpenCode turns.
- **Llama 3 8B BFP8 (~8.5 GB) under multi-user load → 1P+1D over TT-link is viable:** ~23 GB KV headroom on the decode card, zero decode jitter during prefills, and zero TP syncs.
- **Card 1 PCIe note:** Card 1 runs at PCIe Gen3 x1 (~1 GB/s) vs. Card 0 Gen5 x16; keep all inter-card transfers on TT-link, and consider streaming Card 1's initial weight load from Card 0 over TT-link (~0.3 s vs. ~30 s).

### Two Kernel Regimes Over One DRAM Weight Layout

Both regimes read the **same `32×32` face-tiled BFP8 weights** in DRAM:

1. **Low-Latency Decode Graph (`T ≤ 32–64`, P1 streaming):**
   - **Dense projections (`qkv`, `o`, `router`, `message_gates`, `lm_head`):** Tiled `StreamK` over 1–2 panels (`experts.ttrv` already performs full 32×32 MVMUL, so `T = 1..32` costs identical FPU time). `lm_head` gathers only rows needing logits.
   - **MoE ("expert panel"):** Generalize `SELECT = 1/2` to the union of active experts ($E(B) \le 128$). Each active expert multiplies the 32-row panel; the SwiGLU epilogue applies per-row routing weights (0 for unrouted rows). Zero gather/scatter, skips inactive experts, and matches today's byte count at `B = 1`.
   - **Attention:** Paged Flash-Decoding sharded over `(seq, kv_head, kv_split)` + merge.
2. **Prefill / Mixed Throughput Graph (`T ∈ {512, 2048}`, P2 dense + grouped MoE):**
   - **Dense projections:** `ColumnRing` P2 over all 138 workers (2×4 `Dst` blocking, multi-reader columns).
   - **MoE (token-bucketed grouped GEMM):** Per-expert histogram → prefix sum → gather into expert-major 32-row panels; each core pins an expert's weight column in L1 and streams its panels (~4 panels × 147 KB at `T = 2048` fits in 1.5 MiB). Down projection writes per-`(token, expert)` rows combined in a fused `resconv` + residual epilogue.
   - **Attention:** Disjoint-core `_async` + `CORE_BASE` split within the same step: paged decode cores + chunked prefill cores (`(seq, kv_head, 32-tok Q panel)` = 96 Q rows per KV head → 3× KV reuse). Relative bias gathers contiguous 32-key slices from reversed `rel` rows within 1024 distance; sinks keep `m = sink, l = 1`; `tau` and output gates apply per-row.
   - **Causal convolutions (`kvconv`, `resconv`, `attn_sconv`, `mlp_sconv`):** Unified across `P = 1` decode and multi-token prefill chunks via a per-token 4-lag source table (pointing either to `row - l` in-chunk or entry `(pos - l) % 4` of the sequence's conv ring), fused into `qkv` / `o` / `down` epilogues.

**Sarathi-style piggybacking rule for Inkling:** Because adding a `T = 2048` prefill chunk to a `B = 4` decode step jumps step latency from ~43 ms to ~160–300 ms, flip the mental model: **decode tokens ride nearly free inside prefill steps**, and the scheduler bounds decode inter-token latency by limiting the ratio of prefill-chunk steps to decode-only steps.

### Orca Continuous Batching on `BlackholeGraph`

- **Two captured graphs** (decode `T ≤ 32–64`, mixed/prefill `T ∈ {512, 2048}`); kernels read active token/panel counts at runtime and idle cores exit early—no per-batch recompilation.
- **3-slot pinned host metadata ring:** Per-step token table `(slot, pos, lag_sources)`, full-attention page tables (128 KiB pages = 32 tok × 8 heads × K/V, shared across all 8 full passes), sliding-window 33-block ring pointers, and sampling params live in host sysmem; the graph's first kernel DMA-copies `step % 3` into fixed DRAM addresses. **Never call `Buffer.copy_from()` inside the step loop** (it synchronizes the device).
- **1-step-ahead host overlap:** On-device sampler writes next tokens directly into `history[slot][pos+1]` and a host ring; host schedules step `n + 1` before reading step `n`'s token (1 wasted token on EOS, zero pipeline bubble).

### OpenCode Workload Priorities

OpenCode runs 1–8 agents with 10–20k system/tool prefixes growing to 30–64k, prefilling 10–50× more tokens than it decodes:
1. **`T = 2048` chunked prefill** (61 → 6.5–13k tok/s 1×, ~24k 2×).
2. **Prefix caching with Inkling snapshots:** Because sliding-window rings and conv states cannot be rolled back and OpenCode re-renders past assistant turns (stripping thinking / re-serializing tool JSON), **snapshot the sliding rings + conv state at each prompt boundary** (~176 MB BF16 / ~94 MB BFP8; <1 ms DRAM copy for COW branching across subagents), while full-attention KV pages are simply shared and truncated via a radix tree.
3. **32k+ context:** Lift the 8,192 `tau` cap and convert the 40 sliding passes to 1024-token ring buffers.
4. **OpenAI API completeness:** On-device temperature/top-p sampling (currently greedy argmax only), stop sequences, and `<|content_invoke_tool_json|>` → OpenAI `tool_calls` mapping.
5. **`B = 1` speed lever:** The **MTP head** (`mtp.safetensors`, verifying `k = 2–3` drafts as a `T = k` step; break-even 1.25–1.8 accepted tokens, ~1.5–1.8× estimated on code) + launch fusion.

---

## 3. Architectural Shift: Dropping "Perf-from-Source"

Reading hardware scheduling and cycle stalls directly from `.ttrv` source has become the primary bottleneck to scaling kernels. Replace it with **post-compile introspection + hardware telemetry**:
- `kernel.inspect()` / `TTRV_DEBUG=1`: dumps lowered 5-core IR, synthesized CB sizes, L1 map, `Dst` tiles used, `STAGES`/`DEPTH`, MOP/replay breakdown, and **predicted per-core makespan + slowest-to-median tail spread**.
- `PROFILE=1` per-core hardware counters (stalls, operand/semaphore waits, FPU/SFPU/NoC busy cycles, per-core finish spread).
- Microbenchmarks (`boop-docs/data/*.json`) + static cycle simulator (`static-cycles`, commit `0b33893`) + lightweight analytical `plan()`.

---

## 4. Kernel Authoring Going Forward: Verified Templates Before Full UOp Compiler

### Immediate `ttrv` Changes vs. Longer-Term Restructuring

Right now, `ttrv` already implements half the machinery needed, and **four concrete limitations in the current `ttrv` frontend/lowering** explain why existing kernels miss 506 GB/s and hit complexity walls:

| Current `ttrv` gap | Where it lives | Quick surgical fix (works immediately in existing `.ttrv`) | Restructuring target (Python template / IR layer) |
| --- | --- | --- | --- |
| **Hardcoded in-flight cap = `128`** (effectively uncapped → 7.91× spread!) | `ttrv/noc.py:318` (`poll(hw.outstanding(tid), 128)`) | Expose optional `cap=N` on `noc.read` (and default `cap` from grid size: `2..4` for `R ≥ 88`, `8` for `R = 42..64`). | Automatic `DramPlan(cap=...)` chosen by `plan()` from active reader count `R`. |
| **Column-major grid slicing bunches readers** when `grid < 138` (208.8 vs. 429.6 GB/s at `R = 28`) | `ttrv/layout.py:75` + `ttrv/__init__.py` (`workers[base : base + grid]`) | Support a `spread` / row-major worker placement option (or keep `grid 138` and branch on row-major `rank = y*14 + x - (y==9)`). | Decouple logical work space from physical grid via `P150()` placement (`G.readers(R)`, `G.cols()`). |
| **Static per-statement port & no auto 128 KiB stagger** on single-page (`tiles_per_page=8`) reads | `ttrv/noc.py:224-235, 285-312` | Optional `port=rotate` inside `noc.read` page loop; enforce odd `NT_PITCH` / staggered stream offsets. | Handled centrally inside `DramPlan`, never hand-coded per kernel. |
| **Single image set per launch & separate `LAUNCH`/`CODE_BRISC` transfer** | `ops_blackhole.py:121-142` | Merge `LAUNCH` (`0xCF0`) + `CODE_BRISC` (`0xD00`); allow `[(core_set, roles), ...]` if a role ever overflows 8–10 KiB. | Default to 1 homogeneous binary over 138 cores (`cover()` = 1 rect); multi-set only on code overflow. |

**Should we restructure all of `ttrv` right now?**
- **Keep the bottom half untouched:** `isa.py`, `cfg.py`, `hw.py`, `field.py`, `emit.py`, `sfpmacro.py`, `regalloc.py`, `state.py`, `runtime.py`, `fw/`, and `ops_blackhole.py` are clean, fast, and battle-tested. You do **not** need to rewrite the backend or assembler.
- **Restructure only the top half (`parse.py` / `expand.py` / `codegen.py` / `noc.py`) incrementally:**
  1. **First (today, ~30 LOC):** Patch `ttrv/noc.py:318` to support `cap=` pacing (and test it immediately on existing 138-core Llama/Inkling decode kernels!).
  2. **Next (alongside Stage 1–3 serving):** Build the 3 Python kernel templates (`StreamK`, `ColumnRing`, `PagedAttn`) directly targeting `codegen`/`regalloc`/`state.py`/`isa.py` so new serving kernels (Inkling chunked prefill, batched MoE, paged attention) stop fighting 400-line `.ttrv` text files.
  3. **Last (Stage 5):** Once those templates stabilize, replace `.ttrv` text parsing entirely with the thin Python UOp IR.

### Keep vs. Build vs. Defer

- **Keep untouched (rock-solid bottom half):** `ttrv/isa.py`, `cfg.py`, `hw.py`, `field.py`, `emit.py`, `sfpmacro.py`, `state.py` (compile-time CFG/CB/semaphore/stall firewall), `runtime.py`, `fw/`, `ops_blackhole.py`.
- **Build first — Verified Template Library (~600 LOC) + `plan()` (~200 LOC):** Only **3 kernel patterns** cover nearly every matmul/attention workload (`StreamK` P1, `ColumnRing` P2, `PagedAttn`). Write the 5-core synchronization **once per template** (verified by `state.py`), instead of building a 1,850-LOC generic auto-splitter before serving works.
- **Dispatch & heterogeneous roles:**
  - `fw/dispatch.c:install()` already supports arbitrary transfer rects overlapped behind the previous kernel; `mcast_launch()` sends params and GO in at most 2 rects (`cover()` reaches all 138 workers in **1 rect**).
  - **Default to one homogeneous binary** across all 138 cores where BRISC/NCRISC branches on `is_reader` (**zero extra launch multicasts**). Use per-group binaries (extend `blackhole_build_program` to accept `[(core_set, roles), ...]`, bounded by 64 KiB `STAGE_SIZE`) only when fusing distinct ops or hitting the 8–10 KiB per-RISC code limit.
  - Free dispatch win: `LAUNCH` (`0xCF0`) is adjacent to `CODE_BRISC` (`0xD00`); merging them saves 1 multicast per rect (6 → 5).
- **Defer until ≥ 3 templates stabilize:** Full Tinygrad-isomorphic UOp IR (`ttrv/uop.py`, `opt.py`, `split.py`) and deletion of `.ttrv` (keep `.ttrv` + role escape hatch for quirky kernels like `gdn_state.ttrv`, `argmax.ttrv` while serving ships).

### Decoupling Logical Work from Physical Grid (All 138 Cores + MoE)

Stop binding kernels to hardcoded `grid_axis(13) × grid_axis(10)` (130 cores). Express work over a **logical index space** mapped onto the column-major 138-worker grid (`P150()`, where column 13 has height 8):

```python
from ttrv.sched import P150, StreamK, Broadcast, ColumnRing, DramPlan, Ragged, ticket

G = P150()  # 138 workers, column-major; col 13 height 8; .rows(), .cols(), .range(a, b)
DRAM = DramPlan(
  noc=0, ports="rotate",
  stagger=lambda core: (2 * core.id + 1) * 256,  # avoids 128 KiB internal-bank collisions
  start_page=lambda core, n: core.id % n,
)

@bh.kernel
def proj_stream(x, w, out, *, epilogue=None, plan):               # P1: decode & B <= ~200-400
  P = bh.cdiv(x.M, 32)
  space = bh.space(n=w.N // 32, k=w.K // 32)
  part = StreamK(space, workers=G.readers(plan.readers),          # spread across all 14 cols
                 order=("n", "k"), chunk=plan.chunk,
                 balance=ticket() if plan.dynamic else "static",  # atomic ticket + fixed-order slot fixup
                 reduce="slots")
  xa = Broadcast(x, to=G.all, gather="striped", kblock=plan.kb)   # 1 DRAM read; cover() reaches all 138
  for c in part.chunks():
    acc = bh.zeros(TM=P, TN=max(1, 8 // P), dtype="fp32")
    for k in c.k_range():
      acc = bh.mma(xa.tile(panels=P, k=k), w.tile(k, c.n).read(DRAM), acc, fidelity=2)
    c.emit(acc, epilogue)

@bh.kernel
def moe_w13(x, w13, act, route: ExpertPlan, *, plan):             # router emits A, ids[A], off[A+1], tok[], cost_prefix[]
  space = Ragged(slot=route.A, n=144, k=72, cost=route.cost_prefix)  # runtime-uniform bounds
  part = StreamK(space, workers=G.all, balance="prefix")          # device-side prefix-sum partition
  for c in part.chunks():
    e = route.ids[c.slot]                                         # indirect expert base, uniform within slot
    xs = x.gather(route.tokens(c.slot)).stage(share=part.cores_of(c.slot))  # covers() <= 2 rects
    ...                                                           # same P1 body + SwiGLU epilogue

@bh.kernel
def proj_reuse(x, w, out, *, plan):                               # P2: prefill & dense B > ~400
  groups = G.cols()                                               # 14 column groups, heights [10]*13 + [8]
  shares = bh.split_proportional(w.N // 32, groups.heights)       # col 13 gets 8/10 of N share
  ring = ColumnRing(readers=plan.R, stages=plan.S, noc=1, dram=DRAM)  # canonical ring (fixes STAGES=2 race)
  for g in groups:
    for (p, n) in g.units(panels=bh.cdiv(x.M, 32), cols=shares[g], TM=plan.TM, TN=plan.TN):
      ...                                                         # wb = ring.recv(k, n); acc = mma(...)
```

---

## 5. Multicast Sharing Analysis & Hardware Safety Invariants

1. **Sharing vs. reader selection:** Compute sharing from the **preimage of the placement** (`cores_needing(tile)`) and enable multicast only when `covers(cores)` reaches the set in **≤ 2 rectangles** (otherwise fall back to unicast). Choosing **which cores read** (`readers = R`, placement, ring depth) is a **schedule decision** from `plan()`, not an output of null-space analysis.
2. **Three uniformity classes (replacing binary static/divergent):**
   - **Compile-time constant** (static tensor shapes).
   - **Runtime-uniform** (MoE active count `A`, per-expert `count[s]`, step `seq_len` — loaded once by every group member and immutable during the launch). Multicast and indirect slot-uniform bases (`ids[slot]`) stay legal here.
   - **Divergent** (per-core variable loops/masks) → safely falls back to unicast.
3. **Physical `x = 8, 9` gap — single-rectangle multicast verified on silicon:** Stage 0 verified that both **NoC0** `(1,2) → (16,2)` and **NoC1** `(16,2) → (1,2)` 4 KiB data multicasts deliver bit-exact payloads to all 14 workers across `x = 8, 9`. Do **not** split `row_mcast` at `x = 7`.
4. **NoC0 / NoC1 contention:** Row multicasts on NoC0 share eastbound links with every DRAM read response, and BRISC command issue is RISC-loop bound (41–59 cyc/cmd), so a DRAM reader's BRISC cannot simultaneously gather and multicast activations for free. Keep streaming column multicasts on NoC1 (`ncrisc`) and stagger activation gathers out of DRAM read waves.
5. **Grid-level K-reductions:** When `N / TN < 14` (e.g. Inkling router `N = 4` tiles, or `o`/`down` at 72 tiles), map `K` onto the grid via `StreamK` deterministic slot partials + fixed-order reduction (generalizing `experts.ttrv`'s `SPLIT` / `SUMS`).

---

## 6. Multi-Device Collectives (`Ops.ALLREDUCE` & Resident ERISC)

Keep `eth/e1_fwd.c` as a ~50-line **resident fabric-DMA daemon** (never compile ERISC with UOps or add a 6th core role):
1. **Firmware upgrade:** Replace the 64-worker polling loop with a single `noc.inc` arrival counter (supporting all 138 workers) + optional arrival-flag multicast back to workers, with a persistent L1 `link_epoch` word.
2. **Fused epilogue AllReduce:** Lower `allreduce(ADD)` directly into projection epilogues (`trisc2` packs to `link_tx` → `ncrisc` streams to E1 `LINK_STAGE(epoch & 1)` → `trisc0/1` FP32 `y_local + y_peer` + fused residual/conv).
   - **Measured TT-link reality:** Wire time for decode (8–14 KiB) is only **0.2–0.3 µs** against **10–15 µs** per separate launch; fusing eliminates ~96 sync launches/token on 2× TP Inkling and ~65 on Llama 3 8B TP.
   - **Prefill streaming:** Large payloads (e.g. 2.6 MB = 53 µs on 1 link, 27 µs across ch 11 + ch 13) exceed Ethernet L1 (~448 KiB), so stream through a credit ring of **4–8 × 16 KiB slots** (matching the ~31 KB bandwidth-delay product at 0.64 µs RTT × 49 GB/s).

---

## 7. Lightweight Analytical Planner (`plan()`) Replacing Heavy Search

Because only **P2** has a non-trivial parameter space (`TM`, `TN`, `R`, `STAGES`) and the cycle simulator itself has ~8.8% median error on 1B `o` (meaning any analytical model reliably ranks gaps > ~15% and needs hardware tie-breaking below that), **defer** Layers 1/3/4 (Pareto DAG covering, Hong–Kung pebbling, full branch-and-bound) in favor of a ~40-line classifier + ~150-line P2 enumerator:

```python
def plan(M, K, N, fmt, free=138):
  P = cdiv(M, 32)
  t_w = TILE[fmt] * free / DRAM_BPC(free)  # measured makespan curve from boop-docs/data/noc.json
  if P * MMA[fmt] / EFF <= t_w:            # P1: weight-streaming
    return Stream(readers=best_readers(fmt), chunk=8, dynamic=coupled_tail_risk(K, N))
  cands = [(TM, TN, R, S)
           for TM in (1, 2, 4) for TN in (1, 2, 4) if TM * TN <= 8
           for R in (1, 2, 3, 4) for S in (3, 4, 6)]
  return sorted(cands, key=lambda c: cost_p2(c, M, K, N, fmt))[:3]  # benchmark top 3 on hardware
```

**Required terms in `cost_p2` / `cost_p1` (grounded in `boop-docs/data/*.json`):**
1. **Measured makespan DRAM term:** `total_bytes / B_dram(readers, placement, page)` (already captures steady-state arbitration tail).
2. **Coupled-group tail term:** `max_g remaining_g / rate_max(g)` (`rate_max ≈ R · (25..54)` B/c) for credit rings/barriers; collapsed by atomic tickets in P1.
3. **Short-stream startup:** `~1,000` cycles overhead for short streams (4–8 rows).
4. **Little's law (`RecMII`):** Exact minimum `STAGES` and `DEPTH` to hide DRAM + NoC RTT (`throughput ≤ B · block_size / L`).
5. **MoE terms:** `A(B) × expert_bytes` in P1 (token skew barely matters while DRAM-bound); runtime `Σ_e ceil(n_e / 32)` prefix sum on device in P2.
6. **Dispatch cost:** `~1,550 + ~4 × cores + payload_bytes / ~16` cyc when unhidden; `~100–150` cyc per extra synchronous `mcast_launch` rect (Stage 0 will pin exact measured numbers).

---

## 8. Resident Megakernel, L1 Reuse & Fine-Grained Core-to-Core Sync

### DRAM Bubbles vs. DRAM Bytes

At batch-1 decode, keep the two throughput levers distinct:
- **Reducing DRAM bytes/token** sets the theoretical ceiling (weight quantization `BFP8 → BFP4`, batching/MTP amortization, and pinning hot KV/small weights in L1). Because total chip L1 is **207 MiB** (`138 × 1.5 MiB`) against 2.5–28.5 GB of model weights, a megakernel cannot eliminate streaming active projection weights from GDDR6.
- **Eliminating DRAM idle bubbles** closes the gap between achieved bandwidth and the **506 GB/s** GDDR6 ceiling. Llama 3 8B BF16 is already at **92.5%** (459 GB/s, tiny megakernel upside), whereas **Llama 3 8B BFP8 (75.7%)**, **Inkling 2 Mini 1× (60.4%)**, and **Inkling 2 Mini 2× TP (43.6%)** lose 25–56% of GDDR6 bandwidth to ~770–800 CQ launches/token, chip-wide barriers, straggler tails, small standalone ops, and separate TT-link sync launches.
- At `B = 1`, activation DRAM round-trips are negligible by volume (<0.1% of weight bytes: ~6 MB/tok on Llama 8B, ~590 KiB live + 2.6 MiB conv rings on Inkling). Keeping activations in L1 saves **latency and NoC0 contention**, while spending the remaining spare L1 on **sliding/short-context KV and looped small weights** directly cuts **DRAM bytes/token**.

### Measured L1 Budget Across Compiled Kernels (`1,536 KiB / core`)

Firmware + double-buffered code slots (`fw.DATA_BASE`) take **94.8 KiB (6.2%)**, leaving **1,441.2 KiB (93.8%)** usable per core. Compiling the existing `blackhole-py` kernels shows massive unused L1 headroom:

| Workload | Kernel Scope | Total Code (all 5 RISCs) | Peak L1 Data (CBs + `l1`) | % of 1.5 MiB |
| --- | --- | ---: | ---: | ---: |
| **Llama 3 8B BFP8** | All 11 decode kernels (`proj` 48–68 KiB, `vec` 4.5–8 KiB, `attention` 277.6 KiB) | **62.4 KiB** *(4.1%)* | **277.6 KiB** | **18.1%** |
| **Inkling 2 Mini decode** | All 9 kernel families (`experts` 28 KiB, `mix/prep/conv/router` 20–52 KiB, `attention` 290.1 KiB) | **71.8 KiB** *(4.7%)* | **290.2 KiB** | **18.9%** |
| **Prefill (`S = 320`)** | All 5 prefill kernels (`proj_prefill` 464.2 KiB peak) | **35.6 KiB** *(2.3%)* | **464.5 KiB** | **30.2%** |

- **No I-cache cliff:** Measured on Blackhole with `RISC_PREFETCH_CTRL = 0x11F` (`boop-docs/data/riscv.json`), straight-line loops execute at **1.00 cyc/instr** up to 512 instructions and **1.006–1.008 cyc/instr** at 1,024 instructions even under heavy NoC/unpacker L1 traffic. Expanding code space to keep every decode kernel resident permanently in L1 avoids DRAM code fetches and `install()` multicasts without I-cache thrashing.
- **~130–150 MiB of free chip-wide SRAM during decode:** All Inkling decode code (~75–150 KiB) + peak attention CBs (~290 KiB) + all live decode activations (~590 KiB chip-wide = **4.3 KiB/core** sharded, plus 2.6 MiB conv rings = **19 KiB/core** sharded) totals only **~400–600 KiB/core (26–39%)**, leaving **~950–1,100 KiB/core (~130–150 MiB chip-wide)** unused.
- **High-ROI DRAM-byte savers for the spare ~140 MiB (decode graph only; prefill/batched graphs retain full scratch headroom for `T = 2048` `ColumnRing` / grouped MoE):**
  1. **Inkling sliding-window KV (100% on-chip):** 40 sliding passes × 1,024 window × 2.1 KiB/tok (BFP8) = **~84 MiB** (or 160 MiB BF16 → **80 MiB/card** on 2× TP), eliminating 84–160 MB/tok of KV DRAM reads once context ≥ 1k.
  2. **Llama 3 8B KV:** `131 KiB/tok` (BF16) / `~70 KiB/tok` (BFP8) → **~1,100 tokens (BF16)** or **~2,050 tokens (BFP8)** completely in L1 (**2× on 2× TP**).
  3. **Hot / looped small weights:** Inkling routers (`~14 MiB`) + message gates (`~50–70 MiB` BF16) + norms/convs/sinks (`~70–90 MiB` total). Pinning these eliminates short-stream BF16 DRAM startup stalls (`~1,000` cyc) and saves **3× reads/token** across the looped middle 12 layers.

### True Global Sync Points vs. Local / Streaming Dependencies

Cores do not need a chip-wide barrier after every op. Tracing true data dependencies per layer:
- **Only 2 true mathematical global barriers per Llama layer:** post-`o_proj` `RMSNorm` and post-`down_proj` `RMSNorm` (global sum-of-squares over `D`; identical to the two 2× TP `AllReduce` points).
- **Inkling adds 1 more per layer:** MoE `router` → top-8 selection (active expert addresses cannot be fetched until top-8 is resolved).
- **Everything else runs without pausing the chip:**
  - `QKV → RoPE + Attention`: **per-KV-head local** — head `h` starts attention as soon as head `h`'s QKV slices finish, overlapping with other heads' QKV.
  - `Attention → O_proj` and `SwiGLU → Down_proj`: **additive over `K`** — consumers can accumulate partial tiles as producers finish (or K-split `Down_proj` locally and reduce only at the end).
  - `Gate/Up → SwiGLU` and causal convolutions (`kvconv`, `resconv`): **100% local / per-channel** — zero cross-core sync.
- **BRISC / TRISC decoupling across dense barriers:** Even at a true global barrier (`RMSNorm`), only TRISC math waits on `x_norm`. For every dense projection, the weight pointers are static, so **BRISC can immediately advance to prefetch the next projection's weights from GDDR6 into L1 CBs** while TRISC finishes the current op and waits on the barrier — keeping GDDR6 saturated continuously.

### Core-to-Core Sync & Resident Interpreter Mechanics

Replace ~800 CQ `DONE_COUNT` → `GO` round-trips (~2.1 µs / ~2,850 cyc each) with **one persistent launch** per decode step:
1. **Resident code + L1 op table:** All decode op routines stay permanently in L1 (single slot, no double-buffering). Each core walks a flat array of ~32-byte op descriptors in L1 (`{fn_pc, weight_ptr, act_in_l1, act_out_l1, wait_sem, signal_sem, dims...}` — 800 ops = **25 KiB**), invoking ops by local function pointer.
2. **Fine-grained producer → consumer (~20–60 cyc / 0.02–0.05 µs):** Producer writes output slice directly to consumer L1 on **NoC1** (keeping NoC0 pure for DRAM reads) and fires `noc_atomic_inc` on a consumer L1 semaphore; consumer spins locally in L1 with zero NoC traffic.
3. **Fast coordinator barrier (~0.2–0.4 µs, for `RMSNorm` / `Router`):** Workers write their 1-word partial (e.g., partial `Σ x²`) + `noc_atomic_inc` to one central worker core; the coordinator finishes the scalar reduction (or top-8 selection) and sends **one `cover()` multicast** writing `(inv_rms, ++epoch)` to all 138 workers — 5–10× faster than a CQ barrier and fusing the reduction simultaneously.

### How the Compiler Discovers L1 Reuse (~150 LOC Static Graph Pass)

No global UOp pebbling or branch-and-bound search is needed. Because decode is traced as a static tensor graph (`with dev.graph()`) with known tensor sizes, lifetimes, and template sharding tags, three deterministic passes (~50 LOC each) handle all L1 reuse and sync insertion:
1. **Activation liveness allocator (~50 LOC):** Standard linear-scan interval allocation over `[producer_op, last_consumer_op]`. Assign intermediate tensors to L1 offsets (reusing dead intervals) whenever `peak_live ≤ act_budget` (always true at `B = 1`), spilling to DRAM only when large `B` or prefill `T` overflows.
2. **Greedy L1 pinning knapsack (~50 LOC):** Compute `spare_L1 = 138 × (1536 KiB - code - peak_CB - peak_act)` (~130–150 MiB). Sort persistent read-only/state tensors by `reads_per_token × (1 + short_stream_penalty)` per byte (looped small weights `3×` first → non-looped small weights & conv rings → sliding/short-context KV pages) and greedily pack across the 138 cores' L1.
3. **Edge-driven sync lowering (~50 LOC):** Inspect producer/consumer sharding tags on each graph edge:
   - Same sharding (`core i → core i`) → local L1 read / fused epilogue, **0 sync**.
   - Group-local (`head h cores → head h core`) → NoC1 write + per-group `noc_atomic_inc`.
   - Global reduction (`RMSNorm`, `Router`, `AllReduce`) → coordinator barrier + `cover()` multicast.
   - Static next-op weights → allow BRISC to cross the TRISC activation barrier and prefetch early.

---

## 9. Staged Implementation Roadmap (Serving-First, Compiler-Parallel)

Build serving value immediately without blocking on a full compiler rewrite:

- **Stage 0 — Hardware Measurements *(mostly complete on p150a Card 0)*:**
  1. ~~Dispatch multicast sweep (`d[6]` = 6..168; 1 vs. 2 `mcast_launch` rects).~~ **Done:** +659 cyc/rect unhidden, 0 overhead behind ≥ 15k-cyc kernels up to 14 rects (and up to 28 rects behind 60k-cyc kernels); +192 cyc per extra synchronous `mcast_launch` rect.
  2. ~~138-core DRAM sweep (`R ∈ {14..138}`, NoC0, rotation, stagger, `cap = 0/2/4/8/16`).~~ **Done:** 138c + `cap = 2` (2 KiB) hits **506.0 GB/s (98.8% of pin)** at **1.01× max/med**; 42–64 spread readers (`cap = 8`) hit **493–503 GB/s** for P2.
  3. ~~Verify data multicast across `x = 8, 9`.~~ **Done:** 14/14 bit-exact on both NoC0 and NoC1.
  4. **Remaining:** Collect real Inkling routing histograms for empirical $A(B)$.
- **Stage 1 — OpenCode Unblock: OpenAI Server + Inkling Chunked Prefill:**
  1. Ship OpenAI `/v1/chat/completions` (SSE streaming, stop sequences, `<|content_invoke_tool_json|>` → `tool_calls`, `/v1/models`) on the existing B=1 graph with live session KV retention.
  2. Lift the 8,192 `tau` cap.
  3. Build Inkling tiled prefill (`T = 2048` chunks: grouped-GEMM MoE + chunked prefill attention + lag-table convs), taking a 20k prompt from ~5.5 min down to **~2–4 s**.
- **Stage 2 — Memory Capacity, Prefix Caching & 2× TP Serving:**
  1. Convert the 40 sliding-window passes to 1024-token ring buffers + paged 128 KiB full-attention KV pool (unlocks 32k+ context).
  2. Add radix-tree prefix cache with prompt-boundary sliding-ring/conv snapshots.
  3. Add on-device temperature/top-p sampling and move the server to **2× TP** (38.1 GB KV headroom, ~2× speed).
- **Stage 3 — Orca Continuous Batching & Verified P1/P2 Templates:**
  1. Add expert-panel batched decode (`T ≤ 32–64`) + two-graph Orca scheduler with 3-slot host metadata ring and 1-step-ahead host overlap (decode tokens riding prefill chunks).
  2. Implement canonical P1 `StreamK` (with atomic tickets) and P2 `ColumnRing` (138 cores with col-13 scaling, fixing `STAGES = 2` and `RESIDUAL` races; unifying Llama BF16 onto one tiled weight copy).
- **Stage 4 — Latency, Resident Megakernel & Efficiency Polish:**
  1. Fused ERISC epilogue AllReduce (cutting ~96 syncs/tok on 2× TP Inkling), BFP8 KV cache (2× batch capacity), and MTP speculative decoding (`mtp.safetensors`).
  2. Resident-L1 decode megakernel (all decode kernels + 25 KiB op table resident in L1, fine-grained NoC1 semaphores + fast coordinator barrier for `RMSNorm`/`Router`, BRISC early weight prefetch across barriers) + ~150-LOC static graph L1 pass (linear-scan L1 activations + greedy pinning of looped routers/message gates/convs and sliding-window BFP8 KV into the ~140 MiB spare L1 pool).
- **Stage 5 — Compiler Generalization (Once Templates Converge):**
  1. Implement `plan()` + P2 enumerator calibrated against `PROFILE=1` and `static-cycles`.
  2. Promote stabilized templates into a Python UOp IR (`ttrv/uop.py`) and eventually wire up the Tinygrad adapter (Appendix B).

---

## Appendix A: Llama 3 Training Requirements (Deferred)

Training (~3× kernel complexity of inference) requires 6 additional kernel families once the UOp/template stack matures:
1. **`dX = dY @ W`** — transposed weight projection (`haloize` transpose for BF16 or transposed tile storage for BFP8/BFP4).
2. **`dW = X^T @ dY`** — 2D SUMMA multicast or split-K partial `dW` reductions with FP32 accumulation (`HiFi2`/`HiFi4` + FP32 master weights or stochastic rounding).
3. **FlashAttention Backward (`dQ`, `dK`, `dV`)** — recomputes `S = QK^T`, `P = exp(S - L)`, `D = rowsum(dO * O)`, `dP = dO @ V^T`, `dS = P * (dP - D)` inside 8 FP32 `Dst` tiles and 1.5 MiB L1.
4. **RMSNorm, RoPE & SwiGLU Backward** — cross-peer `dX`/`dGamma`, negated-`sin` RoPE, fused SFPU `dGate`/`dUp`.
5. **Fused Chunked Cross-Entropy + Backward** — online tiled softmax/CE fused with `lm_head` backward over `V = 128,256`.
6. **AdamW Optimizer** — streaming FP32 master weights, `m`, `v`.

**VRAM reality:** Llama 3.2 1B full FP32 AdamW (~19.8 GB + checkpointed activations) fits on 1× p150a; Llama 3 8B (~128 GB) requires LoRA/QLoRA (~1–2 GB optimizer state) or multi-card sharding.

---

## Appendix B: Tinygrad Port Contract (Deferred)

Tinygrad's pipeline (`rangeify → apply_opts → expander → lower_reduce → devectorizer2 → linearize → ISARenderer`) emits per-kernel single-source UOp graphs (`PARAM`, `RANGE`, `STAGE`, `AFTER`, `WMMA`, `REDUCE`, `ALLREDUCE`, `STORE`). Once `blackhole-py`'s templates stabilize into a Python UOp lowering backend (`opt.py → split.py → lower.py → isel.py → regalloc.py → state.py → isa.py`), porting into Tinygrad requires only two thin adapters (~250 LOC):
1. **Blackhole `32×32×32` `TensorCore` & tile-layout bufferizer** (`BF16`/`BFP8`/`BFP4` → `FP32` + face-tiled DRAM pages).
2. **Placement + `STAGE` multicast-scope tagging + `ALLREDUCE` epilogue absorption**, plugging `plan()` in place of brute-force `BEAM`.
