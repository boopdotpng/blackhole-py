# Blackhole Compiler Lowering Pipeline & Tinygrad Architecture Guide

A reference and build plan for lowering Tinygrad kernels (and replacing hand-written 5-RISC `.ttrv` kernels) onto Tenstorrent Blackhole.

---

## 1. Where Things Stand Today

On branch `blackhole-compiler` in `tinygrad`, the prototype lives in `tinygrad/renderer/blackhole/`:

| File | Role | Current Status |
|---|---|---|
| `__init__.py` | `BlackholeRenderer` | Hooks `to_program(ast)` **before** `full_rewrite_to_sink`, keeping `RANGE` / `REDUCE` intact. Renders Engine IR + 5-RISC thread schedule into `Ops.SOURCE`. |
| `ops.py` | Engine Ops IR (`Ops.NATIVE` + `BHSpec`) | Defines `Space`, `Fmt`, `Fidelity`, `BHOps`, precision guards (`PrecisionError`, `precision_report`), `SFPU_LANES = 32`, `TILE_ELEMS = 1024`. |
| `lower.py` | AST -> Engine Ops | Runs `multi_pm`, `pm_mops`, `pm_load_collapse`, `sym + pm_flatten_range`, then lowers 1D/2D elementwise and 0D/1D reductions. |
| `sched.py` | `plan -> add_sync -> split` | Lifts Engine IR to a single sequential program over all 5 RISCs (`brisc`, `ncrisc`, `trisc0`, `trisc1`, `trisc2`), allocates `L0..L7` / `Dst` / CBs, lowers SFPU math (`recip`, `sqrt`, `rsqrt` with demand-driven `newton_terms()`), inserts `ownership()` + `completion()` syncs, and splits into 5 thread programs. |
| `tsim.py` | Adversarial 5-RISC tile simulator | Random interleaving + single-RISC starvation, tracks pending async engine ops for `RaceError` / `DeadlockError`, models 4x8 even/odd SFPU footprints, denormal flush, worst-case `SFPARECIP`. |
| `isa.py` | RV32IM + Tensix encoder/decoder | Complete encoder/decoder + inline Tensix encoding. |
| `test/blackhole/test_blackhole.py` | Unit + mutation tests | Validates RMSNorm, negative-tail `max`, FP32 `unpack_to_dest`, precision-demand refinement, and `test_every_sync_op_is_needed` (dropping any of >40 sync ops must fail). |

### Current Gaps & Hardware Mismatches to Fix
1. **Sharding is rigid and too coarse (`lower.py`)**:
   - 1D elementwise splits on `TILE_ELEMS = 1024` -> `(1, 4096)` uses only **4 of 119/139 cores**.
   - 2D elementwise only shards `outer_ranges[0]` -> `(4, 8192)` uses only **4 cores**. `>2` ranges raise `NotImplementedError`.
   - Reductions only shard 1 outer range -> `(1, 4096)` RMSNorm K0 uses **1 core** (no Split-K / `PEERS`), and `>1` outer ranges (e.g. prefill matmul `(32, 4096) @ (4096, 4096).T`) raise `NotImplementedError`.
2. **Hardcoded 1024-element tiles in `sched.py`**:
   - Always emits `Loop("foot", 32)` and `n=1024` for NoC/unpack/pack, even on `(64, 50)` or `(7, 100)`.
3. **`tsim.py` shortcuts that won't hold on silicon**:
   - `noc.read` auto-pads partial tails with `0.0` or `-inf`. Real NoC does not pad — BRISC must zero/fill the L1 tail or TRISC1 must mask tail lanes / use `UNPACR_NOP_ZEROSRC`.
   - Scalar reduction writes emit `noc.write n=1` (4 bytes to DRAM); real DRAM writes require aligned chunks or core-local gathering.
   - Row-invariant buffers (e.g. RMSNorm `gamma`) are re-read from DRAM on every row instead of hoisted into L1.
   - No `SrcB`, `math.zero`, `math.mvmul`, or mixed non-FP32 unpack formats yet.
4. **Backend not wired yet**:
   - No RV32IM + Tensix emitter (`emit.py`), no `REPLAY`/`MOP`/`SFPLOADMACRO` passes, and `BlackholeProgram.__call__` is still `NotImplementedError`.

---

## 2. Entry Point & What Tinygrad Actually Hands the Backend

**Do NOT start from `Ops.LINEAR` (`Renderer.render(uops)`).** By the time `linearize()` runs (`tinygrad/codegen/__init__.py`), tinygrad has already applied GPU `apply_opts`, SIMT `LOCAL`/`UPCAST`/`WARP` splitting, `devectorizer2`, `pm_reduce_local`, and software polynomial expansions.

**The right starting point is `BlackholeRenderer.to_program(ast)`** (pre-`full_rewrite_to_sink`), where you receive the clean Kernel AST (`Ops.SINK`).

### Example 1 — Llama 3 Prefill Q-Proj `(32, 4096) @ (4096, 4096).T` (BF16)
Tinygrad schedules **1 kernel** and already inserts FP32 accumulation (`sum_acc_dtype`) and an explicit BF16 cast on store:

```text
SINK
  END(r_m = RANGE(32, axis=1), r_n = RANGE(4096, axis=2))
    STORE(
      INDEX(PARAM[0: bf16, 131072], r_m * 4096 + r_n),             # out[m, n]
      CAST[bf16](
        REDUCE[ADD](
          CAST[f32](
            MUL(
              INDEX(PARAM[1: bf16, 131072],   r_m * 4096 + r_k),   # x[m, k]
              INDEX(PARAM[2: bf16, 16777216], r_n * 4096 + r_k),   # w[n, k] (transposed!)
            )
          ),
          r_k = RANGE(4096, axis=0)
        )
      )
    )
```

* Three axis roles: `M = 32` (`in0`-only), `N = 4096` (`in1`-only), `K = 4096` (reduced in both).
* Both `x[m, k]` and `w[n, k]` are row-major and contiguous along `K`; `out[m, n]` is contiguous along `N`.
* For **decode (`M = 1`)**, `r_m` collapses completely, leaving `r_n = RANGE(4096)` and `r_k = RANGE(4096)`.

### Example 2 — BF16 RMSNorm `(128, 4096)`
Tinygrad schedules **2 kernels**:
* **Kernel 0**: `out[row] = sqrt(REDUCE[ADD](cast[f32](x[row*4096 + col])^2, col) * (1/4096) + 1e-5)`
* **Kernel 1**: `y[row*4096 + col] = cast[bf16](cast[f32](x[row, col]) * recip(rms[row]) * cast[f32](w[col]))`

---

## 3. Hardware Engine Granularities, Lowering Rules & `blackhole-py` Patterns

### Exact Per-Engine Granularities (Separate DRAM Transfer from Compute!)
| Engine | Real Granularity | Lowering Rule |
|---|---|---|
| **NoC Read (BRISC)** | **1024-elem tiles (2–4 KiB bursts)** *(sub-tile only for tiny kernels/tails)* | For all real kernels, always stream whole tiles on **NoC0** (never NoC1), 3-port rotated, odd pitch/stagger, with **paced in-flight `cap = 2..4`** (88–138 readers) or `cap = 8` (42–64 readers) to sustain ~506 GB/s without router tail blowup (`research.md` §1). |
| **NoC Write (NCRISC)** | **1024-elem tiles (2–4 KiB bursts)** | Mirror the read rules on **NoC1**: buffer packed tiles in L1 and stream paced full-tile bursts back to DRAM. |
| **Unpacker (`UNPACR`)** | **BF16/FP32**: `1..1024` datums (16B-aligned; face mode = `256 x 1..4`)<br>**FP32 -> Dst**: `256 x 1..4` faces<br>**BFP8/BFP4**: `128, 256, 512, 1024` | Unpack whole tiles (`1024`) or faces (`256`) whenever data is tiled; use sub-tile `x_dim` only for genuine short-M / tail shapes. |
| **FPU (`MVMUL`, `ELW*`, `GMPOOL`)** | **`MVMUL`**: **`8x16x16`** atom (`16x16x16` face = 2 `MVMUL`s; `32x32x32` tile = 16 `MVMUL`s)<br>**`GAPOOL`**: `4x16x16` (half rate, 4-row edge cases only)<br>**`ELWADD/SUB/MUL`**: `8x16 = 128` datums/cyc (4x faster than SFPU)<br>**`GMPOOL`**: `16x16 -> 1x16` col-max | Lower **any matmul (`>= 8x16`)**, **BF16/BFP8 elementwise `add/sub/mul`**, **sum reductions** (`MVMUL` against a `1.0` tile/face, then SFPU finishes the last 16/32 elems), and **BF16 max reductions** (`GMPOOL` + SFPU finalize) on the FPU — not SFPU. |
| **SFPU** | **32 physical lanes**, **1 logical element** (via `SFPSETCC` / `SFPPUSHC` lane masks) | Owns FP32-input math (avoiding 19-bit TF32 truncation), transcendentals (`rsqrt`, `recip`, `exp2`, `log2`), final reduction tails, and **all conditionals / masks** (`WHERE`, `CMPLT`, causal mask, ReLU — unless materializing a 0/1 mask tile to feed FPU). |
| **Packer (`PACR`)** | **64 datums** (`4x16`, multiples of 64 up to `1024`; BFP8/BFP4: `128, 256, 512, 1024`; `pack.gather` down to `1` for scalars) | Prefer `64..1024` (`n=1024` for full tiles) so NCRISC writes full tile bursts back to DRAM. |

### FPU (`MVMUL`) Native Tile Shapes
* **Atom**: `(8, 16, 16)` — 1 `MVMUL`: `Dst[8, 16] += SrcB[8, 16] @ SrcA[16, 16]` (cleanly lowerable as a standalone small FPU matmul!)
* **Face**: `(16, 16, 16)` — 2 `MVMUL`s (same dims as AMD `16x16x16`)
* **Short-M**: `(16, 32, 32)` — 8 `MVMUL`s/phase (`nanbeige/projection.ttrv` `TILE_ROWS=16`)
* **Standard Tile**: `(32, 32, 32)` — 16 `MVMUL`s/phase x `PHASES` (`2` for exact BF16xBFP8 HiFi2, `4` for exact BF16xBF16 HiFi4)
* **Panel / SUMMA**: `(32*P, 32, 32)` (`P <= 8` Dst tiles) or `(64, 64, 16)` (32 `MVMUL`s -> 4 FP32 Dst tiles)

### The 4 Sharding Patterns Across Every `blackhole-py` Model
Across Llama 3 1B/8B, Qwen3.8-27B, Nanbeige4.3-33B, Inkling 2 Mini, and standalone matmul/SUMMA, every kernel uses one of 4 grid strategies:
1. **1D parallel / N-sharded** (`llama3/qkv.ttrv`, `nanbeige/projection.ttrv` decode, `qwen38/gdn_state.ttrv`): shard output columns/channels across workers (down to 32 cols for MVMUL, 64 channels for SFPU, or 1 row for dense dot products).
2. **2D `(M_panel x N_col)` grid + multicast** (`prefill/projection.ttrv`, `matmul.ttrv`, `summa.ttrv`): split grid into `R` row-groups x `C` col-groups. One reader per column multicasts `W` down the column (NoC1); workers in a row gather/multicast `X` along the row (NoC0).
3. **Split-K / Split-Reduce (`PEERS`)** (`inkling/experts.ttrv` `SPLIT`, `prefill/vector.ttrv` `PEERS`): when parallel work `< num_cores`, split the reduction axis across peer cores and exchange/reduce partials.
4. **Dynamic/snaked 2D tile queue** (`llama3/prompt_attention.ttrv`): flatten `(head, q_tile)` and snake largest-first across cores to balance causal-mask work.

---

## 4. The 3-Stage Compiler Architecture (and the UOp Boundary)

### Where UOps Work vs Where UOps Break
* **UOps ARE the right structure above resource allocation (Level A — functional tile dataflow)**:
  Symbolic index algebra, contraction detection, hoisting loop-invariant reads, epilogue fusion, and precision checking are pure SSA DAG operations where `graph_rewrite` and `UPat` shine.
* **UOps are the WRONG structure below resource allocation (Level B — replacing TTRV)**:
  Hardware state (`Dst` tiles, `SrcA`/`SrcB` 2-bank rings, `L0..L7`, `RWC`/`ADDR_MOD`/`CFG`, CB counters, semaphores, NoC groups) is mutable and side-effectful. Hash-consing collapses repeated instructions (e.g., 16 identical `MVMUL`s with the same `addr_mode`) unless every op threads dummy `AFTER` tokens — reinventing an imperative list badly.
* **Structured imperative `Schedule` (`Op` + `Loop` + `If`) IS the right structure to replace TTRV**:
  Start as **1 sequential stream** over all 5 RISCs (trivial functional semantics), let `add_sync()` insert CB/semaphore/`dvalid`/`STALLWAIT`/collective syncs mechanically, and let `split()` project onto the 5 RISC threads.

### The Minimal 3-Stage Pipeline

```text
  [Input]  Tinygrad Kernel AST  (Ops.SINK — pre-devectorize UOp graph)
              │
              │  Stage 1 — Classify, Shard & Tile  (lower.py, UOps)
              │    • Classify: Matmul(B,M,N,K) | Reduce(outer,red) | Elementwise(outer,vec)
              │    • Build GridPlan: physical grid (R x C), FPUTile or adaptive chunk (64..1024),
              │      Split-K / PEERS if under-subscribed, precision & fidelity check
              │    • Emit Level-A Tile Engine UOps (pure SSA, real tile/chunk granularity)
              ▼
  [IR 1]   Level-A Tile Engine UOps  (1 functional graph of bare engines:
                                      row_gather, col_mcast, noc_read, unpack, mvmul, sfpu, pack, noc_write)
              │
              │  Stage 2 — Bind, Sync & Split  (sched.py, imperative Schedule)
              │    • Lower Level-A UOps -> 1-stream imperative Schedule (Op / Loop / If)
              │      allocating CBs, CollectiveCBs, L1 scratch, Dst tiles, L0..L7, SFPU expansions
              │    • ownership() + completion() + merge_stalls()
              │    • split() -> 5 per-RISC streams (brisc, ncrisc, trisc0, trisc1, trisc2)
              ▼
  [IR 2]   5-RISC Synchronized Streams  (the TTRV replacement; verified by tsim.py)
              │
              │  Stage 3 — Compress & Emit  (opt.py + emit.py + isa.py)
              │    • Optional late passes per TRISC: SFPLOADMACRO -> REPLAY -> MOP
              │    • RV32IM linear-scan regalloc + inline Tensix emission via isa.py
              ▼
  [Output] 5 RISC binaries  (Ops.PROGRAM / BINARY -> BlackholeProgram)
```

---

## 5. Concrete Case Study: `examples/prefill/projection.ttrv` (411 Lines -> 2 Levels)

### Level A — High-Level Engine UOps (~15 lines, pure SSA)
```python
col_id    = core_id // PANELS
panel     = core_id % PANELS
first_col = col_id * per
r_j       = UOp.range(count, 0)                      # output column tiles owned by this core
r_b       = UOp.range(BLOCKS, 1)                     # K-blocks (BATCH=32 tiles each)
r_i       = UOp.range(BATCH, 2)                      # K-tile within block
col       = first_col + (r_j + rot) % count

# Invariant to r_j -> hoisted automatically outside the column loop
x_l1  = bh_op(BHOps.ROW_GATHER, (x_param, panel), space=L1, fmt=BF16, tiles=KT, rect="row")
w_off = ((r_b * (BATCH // GROUP)) * NT_PITCH + col) * GROUP
w_blk = bh_op(BHOps.COL_MCAST, (w_param, w_off), space=L1, fmt=W_FMT,
              tiles=BATCH, group=GROUP, depth=2, stages=4, sender=(panel == 0))

srca   = bh_op(BHOps.UNPACK_SRC, (w_blk, r_i),             space=SRCA, fmt=W_FMT, shape=(32, 32))
srcb   = bh_op(BHOps.UNPACK_SRC, (x_l1, r_b * BATCH + r_i), space=SRCB, fmt=BF16,  shape=(32, 32))
prod   = bh_op(BHOps.MATMUL_TILE, (srca, srcb), space=DST, fmt=FP32, fidelity=HIFI2, tile=(32, 32, 32))
acc    = UOp(Ops.REDUCE, dtypes.float32, (prod, r_b, r_i), arg=(Ops.ADD, 0))

res_l1 = bh_op(BHOps.PACK, (acc,), space=L1, fmt=BF16, n=1024, explicit_cast=True)
wr     = bh_op(BHOps.NOC_WRITE, (out_param, (panel * NT + col) * 1024, res_l1), space=DRAM, fmt=BF16, n=1024)
sink   = wr.end(r_j).sink()
```

### Level B — 1-Stream Imperative `Schedule` (Before `add_sync()` + `split()`)
```python
Schedule(
  cbs  = {"act": (KT, "bf16"), "stage": (STAGES * BATCH, W_FMT), "results": (2, "bf16")},
  mcbs = {"matrices": CollectiveCB(pages=DEPTH * BATCH, fmt=W_FMT, rect="col", sender="panel==0")},
  body = (
    Op("trisc0", "cfg", "unpack.fmt", "a", f"in={W_FMT}"),
    Op("trisc0", "cfg", "unpack.fmt", "b", "in=bf16"),
    Op("trisc1", "cfg", "math.fmt", "dst=fp32", "sfp=fp32"),
    Op("trisc2", "cfg", "pack.fmt", "in=fp32", "out=bf16"),

    Op("brisc", "noc", "noc.row_gather", "act", "x[panel]", n=KT*1024, wr=["cb:act"]),

    Loop("j", count, (
      Op("trisc1", "fpu", "math.zero", "dst[0]", wr=["dst:0"]),
      Loop("b", BLOCKS, (
        If("panel == 0", (
          Op("brisc",  "noc", "noc.read",  "stage",    "w[col, b]", n=BATCH*1024, wr=["cb:stage"]),
          Op("ncrisc", "noc", "noc.mcast", "matrices", "stage",     n=BATCH*1024, rd=["cb:stage"], wr=["mcb:matrices"]),
        )),
        Loop("i", BATCH, (
          Op("trisc0", "unpack", "unpack.tile", "a", "matrices[i]",      rd=["mcb:matrices"], wr=["srca"]),
          Op("trisc0", "unpack", "unpack.tile", "b", "act[b*BATCH + i]", rd=["cb:act"],       wr=["srcb"]),
          Op("trisc1", "fpu",    "math.mvmul",  "dst[0]", f"phases={PHASES}", rd=["srca", "srcb", "dst:0"], wr=["dst:0"]),
        )),
      )),
      Op("trisc2", "pack", "pack.move", "results", "dst[0]", n=1024, rd=["dst:0"], wr=["cb:results"]),
      Op("ncrisc", "noc",  "noc.write", "out[panel, col]", "results", n=1024, rd=["cb:results"]),
    )),
  )
)
```

### How Collective Sync & Edge Cases Work
* **`CollectiveCB` (`mcb:matrices`)**: `ownership()` lowers it to the exact credit/flag protocol: consumer reserve/release -> `noc.inc remote(sender, b_ready[slot])`; sender reserve -> poll `b_ready`; sender publish -> `noc.mcast` data + `b_sent[slot] = n + 1`; consumer wait -> poll `b_sent`.
* **Pipelining**: `pages = DEPTH * BATCH` lets `brisc` / `ncrisc` / `trisc0` / `trisc1` / `trisc2` overlap iterations automatically once `split()` runs.
* **Dual-role RISC edge case**: when one RISC (e.g. `ncrisc` on `panel == 0`) owns both `noc.mcast` inside `Loop("b")` and `noc.write` after `Loop("b")`, either move `noc.write` to the other NoC RISC or tag the `cb:results` consumer with `lag=1` so `store(j - 1)` doesn't stall multicasting column `j + 1`.

---

## 6. Core Sharding (`GridPlan`), `FPUTile`, and Row-Major Layout

### Why NOT Tinygrad's Built-In `tc.TensorCore` / `Ops.WMMA`
`tinygrad/renderer/tc.py` and `postrange.py:_apply_tc_opt` model **SIMT warp-lane bit-shuffling** (`AxisType.WARP` of 32/64 threads, splitting `m/n/k` into `LOCAL` and `UPCAST` bits). Blackhole has no SIMT warp (`has_local = False`): one scalar TRISC1 issues `MVMUL` directly on `SrcB[8,16] x SrcA[16,16] -> Dst[8,16]`.
* **Steal** the ~25-line contraction matcher from `postrange.py:165-186` (`REDUCE[ADD](CAST?(MUL(in0, in1)))` -> `(B, M, N, K)` axes).
* **Define** a Blackhole-native `FPUTile(m, n, k, dst_tiles, mvmuls_per_phase)` table (`(8,16,16)`, `(16,16,16)`, `(16,32,32)`, `(32,32,32)`, `(64,64,16)`).

### Adaptive Sharding Rules (`GridPlan`)
* **Core DRAM Rule**: On any kernel large enough to be bandwidth-bound, keep NoC reads/writes at **full 1024-element tile bursts** (paced `cap = 2..4` / `8` on NoC0/NoC1) and get core parallelism from **2D `(M_tile x N_tile)` + `StreamK` / `Split-K`** — do *not* chop big DRAM reads into 128B bursts. Only drop below 1024 elements for genuinely tiny tensors or partial tails.
* **Elementwise & Reductions**:
  1. Flatten all outer parallel ranges into `outer = prod(outer_axes)`.
  2. Keep `chunk_elems = 1024` (full tiles) whenever total tiles saturate DRAM/cores; only shrink `chunk_elems` into `{512, 256, 128, 64}` on genuinely tiny tensors (e.g. `(1, 4096)` = 8 KiB total) or short rows (e.g. `(64, 50)` -> 64 datums = 1 `PACR`, 2 SFPU footprints).
  3. On reductions where `outer < num_cores`, enable `peers` (`Split-K`) across cores per output row, and lower BF16/BFP8 sum/max reductions through FPU (`MVMUL`-with-ones / `GMPOOL`) before SFPU finishes the last 16/32 elements.
* **Matmul `(B, M, N, K)`**:
  1. Support clean FPU lowering all the way down to `(8, 16, 16)` and `(16, 16, 16)` for small shapes; default to `(32, 32, 32)` for large shapes (or `(16, 32, 32)` when `M <= 16`).
  2. If `B * MT * NT < num_cores`, shrink `(m_tile, n_tile)` toward `(16, 16)` / `(8, 16)` or enable `k_split` (`StreamK`) so DRAM readers still stream full 1024-element weight tiles across all 138 cores (e.g. GQA K/V-proj `(32, 4096) @ (4096, 1024)` gets 128 workers via `32x32 + k_split=4` or `(16, 16)`).
  3. For Llama 3 prefill Q-proj `(32, 4096) @ (4096, 4096)`: `MT = 1, NT = 128` -> `1 x 119/128` cores, 1–2 tiles/core, zero cross-core reduction.
  4. For longer prefill `(320, 4096) @ (4096, 4096)`: `MT = 10, NT = 128` -> `10 x 12/14` 2D grid. `GridPlan` marks `A` invariant along `grid_c` (NoC0 row multicast) and `B` invariant along `grid_r` (NoC1 column multicast).

### Row-Major DRAM <-> Face-Tiled FPU Bridge
1. **Immediate (any row-major Tinygrad tensor)**:
   - `x[m, k]`: strided `noc.read` per row in one `noc.group` + L1 face-pack (`examples/prefill/pack.ttrv`).
   - `w[n, k]` (transposed `[N, K]`): **Unpacker 0 (`SrcA`) has free hardware X/Y face transpose** (`haloize_mode=1`, `unpack.fmt a, transpose`) — only face-order swap `(f1 <-> f2)` is needed for 32x32!
   - `out[m, n]`: pack face tile to L1, untilize/scatter rows to DRAM.
2. **Follow-up (full `blackhole-py` speed)**: track per-buffer layout (`ROW_MAJOR` vs `TILED_32x32` vs `KN_PACKED`) across kernels so activations stay face-tiled across the transformer block.

---

## 7. Automatic `SFPLOADMACRO`, `REPLAY`, and `MOP` Generation

Keep them as **3 separate, orthogonal passes** on the per-RISC `Op`/`Loop` stream in **reverse hardware pipeline order** (`SFPLOADMACRO -> REPLAY -> MOP`), right before `isa.py` emission:

```text
  TRISC (RV32) -> [MOP Expander] -> [Replay Expander] -> Wait Gate -> [SFPLOADMACRO] -> SFPU
```

1. **Pass 1 — `SFPLOADMACRO` (`trisc1` peephole matcher, ~60 lines)**
   - Anchor on `sfp.load r, dst[off]` (`x = r`) and fuse at most 1 op per sub-unit (`simple`: `mov`; `mad`: `add/mul/mad`; `round`: `shft2`; `store`: `store dst[off]`).
   - Hardware legality (from `blackhole-py/ttrv/sfpmacro.py`): `x` must appear **once** in `vb` or `vc` (never `va`; commute `mul(x, c)` to `mul(c, x)`), dest is `x` or `l16`, delays in `0..7` with no write collision, `(dst_row & 1) == (r // 4)`.
   - Budget: 4 macro slots + 4 shared instruction templates (`SFPCONFIG` 12..15). Hoist `sfpmacro.load`, replace chain with `sfpmacro.run`.
   - Note: `scale_x` (`load l1; mul l1, l0, l1`) matches; `square` (`load l1; mad l0, l1, l1, l0`) does not and passes straight to `REPLAY`.
2. **Pass 2 — `REPLAY` (constant-block matcher per TRISC, ~40 lines)**
   - Match any contiguous sequence of `2 <= len <= 32` constant 32-bit Tensix words (including `sfpmacro.run`, no RV32 ops, no nested `REPLAY`) executed >= 2 times.
   - Budget: 32 words/thread. Deduplicate, rank by `(execs - 1) * len`, pack into `[0..32)`. Hoist `replay.load(idx, words)` and replace occurrences with `replay.run(idx, len)`.
3. **Pass 3 — `MOP` Template 1 (structural loop matcher per TRISC, ~50 lines)**
   - Match any 1- or 2-level static-count `Loop` nest (`1 <= outer, inner <= 1023`) of constant Tensix words (now including `replay.run`!) with `<= 1` prologue word (`StartOp`), `1` or `2` alternating inner words (`LoopOp`/`LoopOp1`, plus optional peeled `Loop1Last`/`Loop0Last`), and `<= 2` epilogue words (`EndOp0`/`EndOp1`).
   - Hoist `mop.load(cfg[0..8])` and replace the loop nest with `mop.run(1)`. Non-matching loops stay RV32 loops around `REPLAY`.

### Trace on RMSNorm `apply_pair` (`x = (x * scale) * gamma`)
* **Raw 2x-interleaved `trisc1` loop**: `4 faces x (4 pairs x 11 words + 2 rwc words)`
* **After Pass 1 (`SFPLOADMACRO`)**: `scale_x` fuses `load + mul` -> inner body shrinks **11 -> 9 words**
* **After Pass 2 (`REPLAY`)**: 9 words hoisted to Replay `[0..9)` -> inner body shrinks **9 -> 1 word** (`replay.run(0, 9)`)
* **After Pass 3 (`MOP`)**: `4 faces x 4 pairs + 2 rwc` hoisted to `MopCfg` -> entire 1024-element tile becomes **1 word (`mop.run(1)`)** — identical to `blackhole-py/examples/llama3/rms_norm.ttrv`.

---

## 8. Deferred Milestone: Adding `dtypes.bfp8` to Tinygrad

Blackhole `BFP8_B` stores **16 datums per shared 8-bit exponent** with all exponents first, then sign+7-bit magnitudes:
* `1024` datums (32x32 tile) = `64B exp + 1024B data = 1088B` (`8.5` bits/elem)
* `256` datums (1 face) = `16B exp + 256B data = 272B` (`8.5` bits/elem)
* `128` datums = `16B exp (padded) + 128B data = 144B`

Because Tinygrad assumes `nbytes = numel * dtype.itemsize` (integer `itemsize`) everywhere (~15 sites in `uop/ops.py`, `codegen/memory.py`, `engine/realize.py`, `tensor.py`, `nn/state.py`):
* **Clean solution**: add `block_elems` / `block_bytes` and `dtype.nbytes(numel)` / `dtype.numel(nbytes)` to `DType` in `tinygrad/dtype.py`, put `dtypes.bfp8` in `DTypes.floats` and `promo_lattice` (with `finfo = (8, 7)` so `can_lossless_cast(bfp8, bf16)` is `True`), add CPU pack/unpack matching `BFP8ToBF16`, and teach `nn/state.py:safe_load` to read `blackhole.formats` metadata.
* **Layout trade-off to decide when implementing**: 256-datum self-contained blocks (`[16B exp | 256B data]`) allow arbitrary sub-tile sharding, whereas 1024-datum tiles (`[64B exp | 1024B data]`) match `blackhole-py` checkpoints zero-copy (but cannot unpack a middle 256-element slice without splitting exponent and mantissa reads).

---

## 9. Tinygrad Reading Guide (The ~11 Files That Matter)

You do **not** need to read all of tinygrad. Everything above Blackhole lives in ~3,500 lines across 4 tiers:

### Tier 1 — Graph & Rewrite Engine
1. `tinygrad/uop/__init__.py` *(139 lines)* — all `Ops` and `GroupOp` sets.
2. `tinygrad/uop/ops.py` *(selective)* — `UOp`, `UPat`, `PatternMatcher`, `graph_rewrite`, `toposort`, `substitute`, `ranges`, `new_buffer`, `ProgramInfo` (skip the Tensor math mixins).
3. `tinygrad/dtype.py` *(327 lines)* — `DType`, `itemsize`, `promo_lattice`, `sum_acc_dtype`.

### Tier 2 — How `Tensor` Ops Become the Kernel AST You Receive *(most important)*
4. `tinygrad/codegen/rangeify.py` *(351 lines)* + `tinygrad/codegen/indexing.py` *(296 lines)* — tinygrad's scheduler: kernel boundary decisions and movement-op -> `RANGE`/`REDUCE`/`INDEX`/`STORE`/`END` lowering.
5. `tinygrad/codegen/prepare.py` *(275 lines)* + `tinygrad/codegen/simplify.py` *(161 lines)* + skim `tinygrad/uop/symbolic.py` *(492 lines)* — the cleanup passes run at the start of `lower.py`.

### Tier 3 — Backend Hook & Runtime Execution
6. `tinygrad/codegen/__init__.py` *(lines 486–540 + schedule linearizer)* — `do_to_program` hook and `Ops.PROGRAM` contract.
7. `tinygrad/renderer/__init__.py` *(131 lines)* — `Renderer` and `TinyELF`.
8. `tinygrad/device.py` *(496 lines)* + `tinygrad/engine/realize.py` *(274 lines)* — `Buffer`, `Allocator`, `Compiled`, `Program`, execution loop.

### Tier 4 — Skim Only for Ideas
* `tinygrad/codegen/opt/postrange.py` *(lines 162–228 only)* — `(M, N, K)` contraction matcher.
* `tinygrad/codegen/late/regalloc.py` *(116 lines)* — linear-scan regalloc reference.
* `tinygrad/llm/model.py` — skim `RMSNorm`, `Attention`, `TransformerBlock` to see exact real-model Tensor graphs.

### Skip
`tensor.py`, `codegen/opt/*` (except those 60 lines), `codegen/late/{coalesce,linearizer}.py`, `codegen/decomp/*`, `renderer/{cstyle,ptx,wgsl,llvmir,nir,amd,x86}.py`, `runtime/ops_*.py`, `runtime/autogen/`.

### Hands-On Exercise to Lock It All In
Dump scheduled `Ops.SINK` ASTs (or run with `VIZ=1`) for 5 ops while reading Tier 2:
1. Elementwise `(a + b) * c`
2. `RMSNorm` (`(1, 4096)` and `(32, 4096)`)
3. Decode matmul `(1, 4096) @ (4096, 4096).T`
4. Prefill matmul `(32, 4096) @ (4096, 4096).T`
5. Causal `scaled_dot_product_attention` (`(1, 32, 32, 128)`)

---

## 10. Suggested Build Order

0. **Reference Fast Batched (`BS > 1`) `.ttrv` Kernels First (Ground-Truth Target for Tinygrad)**:
   - Surgical `ttrv` fix (~30 LOC): expose `cap=N` pacing in `ttrv/noc.py` (replacing hardcoded `128`) and row-major `spread` placement in `ttrv/layout.py` so all 138 cores hit ~506 GB/s cleanly.
   - Write & profile (`PROFILE=1`) 4 parameterized batched reference kernels on silicon:
     1. **Batched Projection P1 (`BS = 1..64/128`)**: 138-core `StreamK` / N-sharded, `cap=2..4` paced full-tile DRAM reads, `M_TILE in {8, 16, 32}` (`MVMUL`), FP32 Dst accumulation.
     2. **Batched Projection P2 (`BS = 128..320+`)**: 14-column `ColumnRing` multicast (fixing the `STAGES=2` ring race) + `P <= 8` resident Dst panels.
     3. **Batched Vector + FPU Reduction (`RMSNorm` / `Softmax` / `SwiGLU`)**: tile-paced NoC + FPU `ELW*` / `MVMUL`-with-ones / `GMPOOL` + SFPU finalize/conditionals.
     4. **Batched Attention (`BS = 1..32`)**: GQA decode + chunked prefill.
   - These measured kernels define the exact `GridPlan` crossover points, L1 staging budgets, and cycle/BW ceilings that Tinygrad-generated code must match.
1. **Unified Sharding + Matmul (BF16)**: refactor `lower.py` to emit Level-A Tile Engine UOps with `GridPlan`, paced tile NoC bursts, `FPUTile` (`8x16x16`..`32x32x32`), FPU reductions, and `(B, M, N, K)` contraction matching.
2. **Extend `sched.py` + `tsim.py`**: `If`, `srcb`, `math.zero`, `math.mvmul` (HiFi4 BF16xBF16), FPU `elw*`/`gmpool`, explicit tail handling, and `CollectiveCB` multicast protocol; verify RMSNorm + batched Q-proj under sync-drop mutation tests.
3. **Naive `emit.py` (no MOP/Replay/SFPLOADMACRO yet)**: lower 5-RISC `Schedule` -> RV32IM + inline Tensix via `isa.py` and wire up `BlackholeProgram` to run real binaries on hardware.
4. **Compression & Speed Passes (`opt.py`)**: add 2x SFPU interleave -> `SFPLOADMACRO` -> `REPLAY` -> `MOP`, then persistent tiled buffer layouts and multicast — benchmarking head-to-head against Milestone 0's `.ttrv` references.
5. **Block Float (`dtypes.bfp8`)**: add block-sized `DType` + BFP8 unpack/pack (`BF16 x BFP8` HiFi2) + `safe_load` support.
