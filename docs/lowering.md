# Blackhole Unified Middle-End Lowering Architecture

This document is the implementation blueprint for replacing the seven whole-kernel lowering templates in `compiler/blackhole/` (`lower.py`, `map.py`, `matmul.py`, `mcast.py`, `reduction.py`, `argmax.py`, `staged.py`) with a single, composable middle-end pipeline.

---

## 1. Architectural Boundary & Core Framing

The frontend and backend of `blackhole-py` are already general:

```text
[Frontend — tinygrad design, unchanged]
Tensor ──► UOp graph ──► symbolic ──► rangeify.py ──► memory.py (DRAM lifetimes)
                                          │
                                  scalar loop AST per kernel
                                          ▼
[Middle-end — THIS REFACTOR (compiler/blackhole/)]
Normalize stages ──► Match FPU / Reductions ──► Choose Schedule ──► Lower to Tile DAG + Alloc
                                          │
                                  abstract Tile DAG (specs.py)
                                          ▼
[Backend — general 5-core Blackhole compiler, mostly unchanged]
compile_tile_graph (linearize once ──► insert_syncs ──► split_roles)
  ──► recipes.py + sfpu.py + scalar.py ──► RV32/Tensix regalloc + hazards ──► BH01 binary
```

### Core Principle
- **SFPU is the universal base path.** Every pointwise op, mask, cast, transcendental, horizontal reduction (`sum`/`max`), index expression (`IndexTile`), and arbitrary view (`NocGather`/`NocScatter`) lowers through one shared SFPU + NoC path. On Blackhole, this is the native unit for elementwise ops, norms, softmax, RoPE, and argmax.
- **FPU matching is a declarative subexpression rewrite on top (tinygrad TC style).** Just as tinygrad matches `REDUCE(ADD, MUL(a, b))` and swaps in `Ops.WMMA` via range-set analysis and whole-AST `PADTO`/`SPLIT`, Blackhole matches FPU patterns (`MVMUL` first; optionally `ELW*`/`GAPOOL`/`GMPOOL` later) directly on subexpressions inside the unified AST.
- **No SFPU fallback for contractions.** A dot product on the SFPU gets ~32 MACs/cycle versus ~2k on the FPU. Any `Ops.REDUCE` that matches neither an FPU op nor a supported horizontal SFPU reduction immediately raises `NotImplementedError` pointing at the offending `UOp` — no shape heuristics and no slow fallback codegen.
- **Composition comes for free.** Matmul + SiLU, SwiGLU (`gate_proj` + `up_proj`), matmul + broadcast residual, RMSNorm + projection, scores + causal mask + softmax, and argmax all flow through the same pipeline with different rules firing, rather than separate templates that each try to anticipate their epilogues.

---

## 2. Non-Negotiable Hardware & Runtime Invariants

Preserved from verified silicon behavior (`hw/isa.py`, `fw/`, `device.py`, `compiler/blackhole/runtime.py`):

1. **Global `Dst` precision & budget:** `fp32_dest_acc = 1` always. `Dst` has `512 × 16` fp32 rows = `64` slots of `8×16`:
   - Slots `0..55` (rows `0..447`) are available to the tile allocator (`0..31` when double-buffered in the future).
   - Slots `56..63` (rows `448..511`) are reserved for `SfpuRenderer`'s `LReg` spill area (`compiler/blackhole/sfpu.py:67`).
2. **Face geometry & the `runtime.py` layout contract:**
   - Default physical layout for all activations, intermediates, KV cache, and outputs is **`8×16` faces** (`face_rows = 8`).
   - Static read-only 2D weight `PARAM`s consumed exclusively as `MVMUL` RHS may use **`16×16` faces** (`face_rows = 16`).
   - `runtime.py` rejects mixed `face_rows` on the same buffer (`"transient buffer layout conversion"`). Therefore, **never** assign `face_rows = 16` to a runtime/transient `ALLOC` buffer or a `PARAM` also read as an `8×16` activation (e.g. attention `K`/`V` in `Q @ K^T` and `attn @ V`). Those stay `face_rows = 8` in DRAM and gather into `16×16` L1 faces via `NocGather(..., lanes=256)` (the mechanism already proven in `matmul.py` + `recipes.py:gather`).
3. **2D multicast NoC deadlock rules** (used whenever the schedule selects a 2D grid):
   - All DRAM reads stay on **NoC0 (`niu = 0`, BRISC)**.
   - Row multicasts (`axis == "x"`, invariant across `worker_x`) run on **NoC0 (`niu = 0`, BRISC)**.
   - Column multicasts (`axis == "y"`, invariant across `worker_y`) run on **NoC1 (`niu = 1`, NCRISC)** after BRISC reads from DRAM and signals local L1 `staged`.
   - Credit atomics (`FN_NOC_INC`) run on **NoC1 (`niu = 1`, NCRISC)** on `ATOMIC_BUF` (`STATIC_VC(1)`), separate from `MCAST_BUF` (`STATIC_VC(4)`).
   - Multicast rects are strictly 1D and include the sender (`CTRL_BRCST_SRC_INCLUDE`).
   - Monotonic sequence counters only; uniform `(batch, om, on, slabs)` trip counts across the grid (out-of-bounds reads clamp offset to `0`; out-of-bounds `NocWrite`s are predicated).
4. **No early machine instructions.** The middle end emits only abstract `specs.py` tile ops (`NocRead`, `NocGather`, `NocMcastRead`, `IndexTile`, `UnpackOp`, `MoveToDst`, `FpuOp`, `SfpLoadOp`, `SfpStoreOp`, `SfpReduceRows`, `SfpReduceLanes`, `SfpBroadcastRows`, `PackOp`, `NocWrite`, `NocScatter`) plus plain core ALU `UOp`s inside `RANGE("fp")`. All `hw_isa.*`, `SfpSpec`, and `RVOps` generation stays late in `recipes.py` / `sfpu.py` / `scalar.py`.

---

## 3. Middle-End Pipeline (Pass-by-Pass Specification)

### Ordering Invariant: Match → Schedule → Lower → Allocate
Matching **must** run before layout selection, tiling, and sharding:
- Layout (`face_rows = 16` vs `8`) depends on whether a `PARAM` is a static `MVMUL` weight.
- Tile size (`1×1` vs `BM×BN`) and grid topology (1D vs 2D mcast) depend on whether the kernel contains a compute-bound `MVMUL`, a decode `MVMUL`, a row reduction, or pure elementwise ops.

```text
Layer 1 Kernel SINK (from rangeify.py)
  │
  ├─ Pass 0: Index Structure Preservation (rangeify.py boundary cleanup)
  ├─ Pass 1: Normalize & Inline Cheap Vector L1 Stages
  ├─ Pass 2: Declarative FPU Matching + Reduction Classification (tinygrad-TC style)
  ├─ Pass 3: Schedule Selection (Schedule dataclass — pure policy, zero codegen)
  ├─ Pass 4: Unified Tile-DAG Lowering + Space Transition Table
  ├─ Pass 5: Liveness-Based CB / L1 / Dst Allocation
  └─ Pass 6: Sync Insertion Hardening (pipeline.py) ──► existing backend
```

---

### Pass 0: Index Structure Preservation (Boundary with `rangeify.py`)

**Current problem:** `compiler/rangeify.py:_split_store` (lines 823–827) runs `pm_mops` to flatten multi-axis `INDEX(RESHAPE(PARAM, shape), r0, r1, ...)` into a flat 1D polynomial `INDEX(PARAM, r0 * S0 + r1)`. Every lowerer in `compiler/blackhole/` then calls `affine()` to reverse-engineer `(batch, m, n)` and `(mr, nr, kr)` from integer stride coefficients — breaking on symbolic offsets (`start_pos`), slices, transposes, or degenerate dims (`m == 1` where strides collide).

**What to do:**
- Keep the flat 1D `INDEX` representation compatible during incremental bring-up, **or** stop flattening `PARAM`/`ALLOC` multi-axis `INDEX` in `_split_store` (leaving N-D coordinates intact until Pass 4 computes physical face byte offsets).
- Crucially, **FPU contraction matching (Pass 2) must NOT call `affine()` at all.** Like tinygrad's `_apply_tc_opt`, contraction matching inspects only **range membership** (`in0.ranges` vs `in1.ranges` vs `reduce.src[1:]`). Only Pass 4's address classifier checks whether a specific `LOAD`/`STORE` is face-aligned contiguous (`NocRead`/`NocWrite`), row-broadcast (`SfpBroadcastRows`), or general (`NocGather`/`NocScatter`).

---

### Pass 1: Normalize & Inline Cheap Vector Stages

Subsumes `compiler/blackhole/staged.py:22-42` so single-store and multi-store kernels enter the exact same pipeline:

1. Topologically order all `Ops.STORE` nodes in the kernel.
2. Identify intermediate `Ops.ALLOC` buffers:
   - **Elementwise vector temporaries** (`prod(alloc.shape) > 1`, stored by a non-reduction pointwise expression with 1-to-1 indexing): inline into their consumer `Ops.LOAD`s (recomputing at each column avoids full-row L1 allocations).
   - **True L1 stages** (scalar/row-reduced temporaries like RMSNorm's `(m, 1)` inverse-rms or softmax's `(m, 1)` max/sum, or any `ALLOC` fed by a `REDUCE`): keep as explicit `Stage(alloc, store)` nodes in topological order.
3. Require all DRAM `Ops.STORE`s in the kernel to share compatible output iteration domains (or fail cleanly with `NotImplementedError("incompatible multi-output domains")` — no silent miscompiles).

---

### Pass 2: Declarative FPU Matching & Reduction Classification

Modeled directly on `tinygrad/renderer/tc.py` and `tinygrad/codegen/opt/postrange.py:_apply_tc_opt`, simplified for Blackhole's core-atomic faces (no warp-lane bit-shuffling):

#### 2.1 Declarative FPU Op Table (`compiler/blackhole/fpu.py`)

```python
@dataclass(frozen=True)
class FpuRule:
  op: str                          # "MVMUL" (future: "ELWADD", "ELWSUB", "ELWMUL", "GAPOOL", "GMPOOL")
  tile: tuple[int, int, int]       # (N, M, K) face quantum, e.g. (16, 8, 16) for MVMUL
  dtypes_in: tuple[DType, ...]     # supported SrcA/SrcB dtypes
  dtype_out: DType                 # dtypes.fp32 (fp32_dest_acc = 1)
  fidelity: Callable[[DType], int] # bfp4->1, bfp8->2, bf16/fp32->3
```

**Initial rule set (v1):**
- **`MVMUL`:** `tile = (16, 8, 16)`, `dtypes_in = (dtypes.bf16, dtypes.bfp8, dtypes.bfp4, dtypes.fp32)` (with `fp32` unpacked as TF32 if enabled, else `bf16`/`bfp8`/`bfp4`), `dtype_out = dtypes.fp32`.

**Future FPU rules (opt-in once `recipes.py` supports them, same table):**
- `ELWADD` / `ELWSUB` / `ELWMUL`: `tile = (16, 8, 1)`, only when both operands are `<= bf16` and neither is already inside an fp32 SFPU chain. *(Defer for v1 — elementwise kernels on Blackhole are DRAM-bandwidth bound, and SFPU handles all dtypes + fused chains in `L0..L7`.)*
- `GAPOOL` / `GMPOOL`: `tile = (16, 8, K_pool)` for 2D pooling reductions.

#### 2.2 Range-Set Contraction Matcher (No `affine()`!)

Walk all `Ops.REDUCE` nodes in the kernel **bottom-up** (so nested reductions like argmax or inner contractions are classified before outer ones):

1. **Try `MVMUL` match** when `red.arg[0] is Ops.ADD`:
   - Unwrap optional `Ops.CAST` around `red.src[0]` to find `mul` (`Ops.MUL`), yielding `(in0, in1)` (unwrap casts on inputs to inspect their native storage dtypes, checking compatibility with `rule.dtypes_in`).
   - Compute range sets purely from `.ranges`:
     - `r_k = [r for r in red.src[1:] if r in in0.ranges and r in in1.ranges]`
     - `r_m = [r for r in in0.ranges if r not in in1.ranges and r not in red.src[1:]]`
     - `r_n = [r for r in in1.ranges if r not in in0.ranges and r not in red.src[1:]]`
     - `r_batch = [r for r in in0.ranges if r in in1.ranges and r not in red.src[1:]]` (plus any batch range in only one operand when broadcasting batch weights!)
   - A contraction matches `MVMUL` iff `r_k` is non-empty AND at least one of `(r_m, r_n)` is non-empty (covering both matrix-matrix `M > 1, N > 1` and decode GEMV `M == 1` where `r_m` is empty!).
   - Assign **activation (`SrcB`, `8×16`)** and **weight (`SrcA`, `16×16`)**:
     - The operand carrying `r_m` (or the non-weight operand when `M == 1`, i.e. the one without `r_n`) maps to `SrcB`; the operand carrying `r_n` maps to `SrcA`.
     - If `r_n` is empty and `r_m` is non-empty, swap roles so the output axis always maps to `N` (or `M` with `N=1`).
   - Record a `MatchedMvmul(reduce_uop, act, weight, m_axis, n_axis, k_axis, batch_axes, rule, weight_is_static_param)`.
   - **Multiple contractions per kernel:** Unlike tinygrad's `_apply_tc_opt` (which stops after `reduceops[0]`), match **every** eligible `REDUCE` in the kernel. Sibling contractions sharing the same `(m_axis, n_axis)` (e.g. SwiGLU `gate_proj` + `up_proj`) share the same output tile coordinates automatically.

2. **Try SFPU Horizontal Reduction match** if not matched as `MVMUL`:
   - Matches any `Ops.REDUCE` with `red.arg[0] in (Ops.ADD, Ops.MAX)` and `len(red.src) == 2` whose single reduction range `kr` is statically bounded (`int` or `Variable.vmax`) and whose body contains no unmatched `REDUCE` (nested matched `REDUCE`s are allowed — they lower first into a scalar `Dst` slot / L1 CB, which handles `argmax` with zero special cases!).
   - Record `MatchedRowReduce(reduce_uop, op, k_axis, body, nested_deps)`.

3. **Fail fast on anything else:**
   - Any remaining `Ops.REDUCE` raises:
     `NotImplementedError(f"unmatched reduction {red.arg[0].name} over {red.src[1:]}")`
   - Never guess by output shape. Never fall back to SFPU matmul.

#### 2.3 Whole-AST Face `PADTO` + Coarse `SPLIT`

Once all reductions are matched, perform **one** coarse face split per logical axis across the entire kernel AST (replacing tinygrad's 12 single-bit `WARP`/`UPCAST` splits):
- Output col axis `N` → `(f_n ∈ [0, ceil(N/16)), i_n ∈ [0, 16))`
- Output row axis `M` → `(f_m ∈ [0, ceil(M/8)), i_m ∈ [0, 8))` (for `M = 1`, `f_m = 0`, `i_m ∈ [0, 8)`)
- Each contraction / reduction axis `K` → `(f_k ∈ [0, ceil(K/16)), i_k ∈ [0, 16))`

When an axis extent is not divisible by `16` (or `8`), attach the validity predicate `f * Q + i < extent` using tinygrad's exact `PADTO` rule (`postrange.py:135-148`):
- Gate `LOAD`/`STORE` addresses with `valid`.
- Gate `REDUCE` inputs with `valid.where(val, identity_element(op, dtype))` (`0.0` for `ADD`, `-inf` for `MAX`).
- Run `sym` so all static-multiple gates (`7168 % 16 == 0`, `22016 % 16 == 0`, `128 % 16 == 0`) vanish immediately.

#### 2.4 Buffer Layout Role Assignment (`face_rows`)

Compute `face_rows: tuple[int, ...]` for kernel `args` **here**, before Pass 3:
- Start with `layouts = [8] * len(args)`.
- For each `MatchedMvmul`: if its `weight` expression is a direct `LOAD` (optionally cast) from a read-only `PARAM` `p` with 2D static shape `(N, K)`, contiguous `(n_axis, k_axis)` indexing (stride `K` on `n_axis`, stride `1` on `k_axis`, zero offset), and `p` is **not** read by any non-`MVMUL-weight` `LOAD` in this kernel:
  - Set `layouts[p] = 16` and mark this weight fetch as `weight_layout = 16`.
- Otherwise (batched runtime `K`/`V`, transposed tensor, slice with offset, or shared buffer):
  - Keep `layouts[p] = 8` and mark this weight fetch as `weight_layout = 8` (Pass 4 lowers it via `NocGather(..., lanes=256)` into a `16×16` L1 face, or `UnpackOp(transpose=True)` if simply transposed).

---

### Pass 3: Schedule Selection (`compiler/blackhole/schedule.py`)

Pure policy function: `select_schedule(matched_kernel, args, max_workers, grid_shape, allow_mcast) -> Schedule`. **Zero IR emission.**

```python
@dataclass(frozen=True)
class Schedule:
  grid: tuple[int, int] | None        # None -> 1D (workers,); (cols, rows) -> 2D mcast grid
  workers: int
  tile_m: int                         # bm: 1 for 1D/decode/map/reduction; 2 or 4 for 2D mcast
  tile_n: int                         # bn: 1 for 1D/map/reduction; 2 or 4 for 2D mcast (or N_BLK later)
  slab_k: int                         # sk: K faces per L1 slab (mcast) or 1 (streaming)
  prefetch_k: frozenset[int]          # param slots burst-prefetched for the full K strip in 1D
  mcast_axes: dict[UOp, str]          # operand -> "x" | "y" | "local" (derived from invariant_axis)
```

**Selection rules (unifying all 7 old templates into one decision table):**
1. **2D Multicast Matmul schedule** (replaces `mcast.py`):
   - Eligible when: `allow_mcast`, kernel has `1..2` `MatchedMvmul`s (no `MatchedRowReduce` spanning across workers), `mf >= 2` and `nf >= 2`, all `MVMUL` activations are `bf16` and both operands have face-aligned `NocRead`-compatible layouts (no per-element `NocGather` on the `MVMUL` operands).
   - Pick `bm = 4 if mf >= 4 else 2`, `bn = 4 if nf >= 4 else 2`, `cols = min(ceil(nf/bn), grid_shape[0], max_workers)`, `rows = min(ceil(mf/bm), grid_shape[1], max_workers // cols)`, `sk` = largest in `(16, 8, 4, 1)` dividing `kf` with slab `<= 64 KiB`.
   - `mcast_axes` is computed generically via `invariant_axis(offset, cols, rows)` (`mcast.py:12-16`): any operand independent of `worker_x` gets `"x"`, independent of `worker_y` gets `"y"`, else `"local"`.
2. **1D Sharded schedule** (replaces `lower.py`, `map.py`, `matmul.py`, `reduction.py`, `argmax.py`, `staged.py`):
   - `grid = None`, `tile_m = 1`, `tile_n = 1`.
   - Parallel work units `W`:
     - If final store is `(batch, m, n)`: `W = batch * mf * nf` (note: for row reductions where `n == 1`, `nf == 1` so `W = batch * mf` automatically!).
     - For pure scalar output (`prod(shape) == 1`, e.g. global argmax): `W = 1`, `workers = 1`.
   - `workers = min(W, max_workers)`, `wid = UOp.special(workers, "worker_id")`, `outer = UOp.range((W + workers - 1 - wid) // workers, 0, "out")`.
   - For each `MatchedMvmul` or `MatchedRowReduce` with face-aligned inputs: add to `prefetch_k` if the full K-strip fits in the L1 budget (`<= 0x160000`).

---

### Pass 4: Unified Tile-DAG Lowering & Space Transition Table

One lowering function `lower_tile_dag(matched_kernel, schedule, args, alloc)` walks the kernel's stages and stores inside the outer loop (`(batch, om, on)` for 2D or `outer` for 1D).

#### 4.1 Per-`LOAD` / Per-`STORE` Address Classification (Eliminating Broadcast & Gather Rejections)

For any `LOAD` from a DRAM `PARAM` (whether in a map, a matmul epilogue, a reduction body, or a runtime-layout `MVMUL` operand), classify its index expression against the active face coordinates `(batch_id, row_tile, col_tile, i_m, i_n)`:

| Pattern | Lowering | Replaces |
|---|---|---|
| Exact 1-to-1 match to `(batch_id, row_tile, col_tile)` with `face_rows == needed_rows` | `NocRead` (1 transfer per face, or burst `prefetch_k`, or `NocMcastRead` on 2D grid) | `lower.py`, `map.py:61`, `mcast.py` |
| Row-invariant (`col`-only, independent of `i_m` / `row_tile`, e.g. bias `(N,)` or RMSNorm weight `(N,)`) | `NocRead` of row `0` + `SfpBroadcastRows` on `trisc1` | `staged.py:87,122`; fixes `"broadcast matmul epilogue"` |
| Col-invariant (`row`-only, e.g. `(M, 1)` scalar stage from `ALLOC` or DRAM) | `NocRead` (or L1 CB) + lane-0 broadcast across `sub_row`s | `staged.py:78-81` |
| Arbitrary / transposed / sliced / indirect (`start_pos`, `Embedding`, `K^T`/`V` `rows=8 -> 16×16`) | `NocGather(..., lanes=rows*16)` | `map.py:63-80`, `matmul.py:49-70` |
| Pure int/bool expression of ranges/variables (no `LOAD`s, e.g. causal mask, `n - kr`, `valid_mask`) | `IndexTile(cb_id)` on BRISC | `map.py:82-96`, `reduction.py:25-28`, `argmax.py:61-65` |

Likewise for DRAM `STORE`s:
- Face-aligned full write → `NocWrite` (single face or `(bm, bn)` block write).
- Partial/indexed/scattered write (e.g. KV cache slice `kv[0, :B, :, start_pos:start_pos+S, :]`) → `NocScatter` (`map.py:103-109`).

#### 4.2 Single `to_space(val, target_space)` Helper

Implement the space-transition table in **one** place (deleting the 6 copies of `via_srca = dtype is not dtypes.fp32; UnpackOp(...); MoveToDst(...)`):

| Transition | Emitted Abstract Ops |
|---|---|
| `DRAM -> L1` | `NocRead` / `NocMcastRead` / `NocGather` |
| `L1 -> SRCA / SRCB` | `UnpackOp(SRCA/SRCB, cb, src_dtype, rows, faces, face_stride)` |
| `L1 -> DST` (`fp32` / `i32` / `u32`) | `UnpackOp(DST, cb, src_dtype, dst_slot=slot)` |
| `L1 -> DST` (`bf16`) | `UnpackOp(SRCA, cb, bf16)` → `MoveToDst(slot)` |
| `DST -> LREG` | `SfpLoadOp(slot, sub_row, fmt)` inside `RANGE("fp")` |
| `LREG -> LREG` | Nothing (stays in `L0..L7`) |
| `LREG -> DST` | `SfpStoreOp(slot, sub_row, fmt)` inside `RANGE("fp")` |
| `DST -> SRCA / SRCB` *(for fused FPU prologues)* | `PackOp(cb, bf16)` → `UnpackOp(SRCA/SRCB, cb)` *(or raise `NotImplementedError("fused MVMUL prologue")` in v1 until enabled)* |
| `DST -> L1` | `PackOp(cb, dst_dtype, blocks, dst_slot)` |
| `L1 -> DRAM` | `NocWrite` / `NocScatter` |

#### 4.3 Subexpression Lowering Rules

Inside the outer tile loop, lower each stage in topological order:
1. **`MatchedMvmul`:**
   - Allocate `bm * bn` contiguous `Dst` slots (`dst_base`).
   - Emit `DstZero` (once per output tile group before any `MVMUL` writes).
   - Emit `K` loop (1D: `rk in 0..kf`; 2D mcast: `slab in 0..slabs`, `kl in 0..sk`).
   - Lower `act -> Space.SRCB` (`rows=8`, `faces=bm`) and `weight -> Space.SRCA` (`rows=16`, `faces=bn`) using the schedule's fetch strategy (`NocMcastRead` / `prefetch_k` / `NocRead` / `NocGather`).
   - Emit `FpuOp("MVMUL", m_blocks=bm, n_blocks=bn, fidelity=..., dst_slot=dst_base, src_dtype=w_dtype, accumulate=True)` closed by `END(k)` (plus `McastConsumed`/`McastRelease` if mcast).
   - Bind `mvmul.reduce_uop -> DstValue(dst_base, bm, bn)`.
2. **`MatchedRowReduce`:**
   - First lower any nested `MatchedRowReduce`s in its body (their result is a scalar `Dst` slot or 1-face L1 CB, eliminating `argmax.py`'s fake `param(1000)` hack!).
   - Allocate 1 accumulator `Dst` slot (`acc_slot`), initialize to `identity`, run `rk in 0..ceil(K/16)` with `SfpReduceRows(op)` + `valid_mask` when `K % 16 != 0` (reusing the proven `reduce_expression` core from `reduction.py:31-70`, parameterized by `acc_slot` instead of hardcoded slot `0`!).
   - Bind `row_red.reduce_uop -> DstValue(acc_slot, 1, 1, is_row_scalar=True)`.
3. **Pointwise SFPU Expression (maps, matmul epilogues, reduction tails):**
   - Fast path: if the store value is directly a single `DstValue` (optionally cast to the `PackOp` output dtype) with no further ALU ops, skip `RANGE("fp")` entirely and pass the `DstValue` straight to `PackOp`.
   - General path: for each `(r, c)` block in `bm × bn`, emit `RANGE("fp", 4)` (or `1` with explicit `sub_row in (0, 2, 4, 6)` when row-broadcast/row-reduction alignment requires it), substitute every `DstValue` / `LOAD` / `IndexTile` with `SfpLoadOp(slot, ...)`, leave all core ALU `UOp`s untouched in `Space.LREG`, and write `SfpStoreOp(out_slot, ...)`.
4. **Stage Store:**
   - If target is an L1 `Ops.ALLOC`: emit `PackOp(stage_cb, dst_dtype=alloc.dtype)` and bind `alloc -> L1StageValue(stage_cb, packed)`.
   - If target is a DRAM `Ops.PARAM`: emit `PackOp(out_cb, dst_dtype, blocks=bm*bn)` → `NocWrite` (or `NocScatter`).

---

### Pass 5: Liveness-Based CB, L1 & `Dst` Resource Allocator (`compiler/blackhole/alloc.py`)

Replaces all six copy-pasted `cb()` closures and hardcoded slot numbers (`slot = 55`, `slot = len(reductions) + j`, `dst_slot = 0`):

- **CB & L1 allocator:**
  - Tracks live CB IDs (`0..31`) and 4 KiB-aligned L1 ranges inside `[0x20000, 0x180000)` (leaving `[0x1EC00, 0x20000)` for `MCAST_CTRL_BASE` and `NOC_READ_SCRATCH`).
  - Releases transient streaming CBs after their consuming loop/stage ends so multi-stage fused kernels don't exhaust the 32-CB limit.
  - Keeps static L1 stage CBs (`Ops.ALLOC`) live until their last consumer stage completes.
- **`Dst` slot allocator:**
  - Manages contiguous slot ranges inside `0..55` (never touching `56..63` reserved for `SfpuRenderer` spills).
  - Frees input `Dst` slots immediately after their consuming `RANGE("fp")` finishes, and frees output `Dst` slots after `PackOp`.
  - Enables in-place epilogues (`out_slot == acc_slot` when the accumulator dies in the epilogue).
  - Fails with a clear `MemoryError("kernel requires N Dst slots, limit 56")` rather than silently overlapping slots.

---

### Pass 6: Harden `pipeline.py:insert_syncs()` for Multi-Phase Composed DAGs

Before fusing multi-stage graphs (e.g. `MVMUL → epilogue with 2 loads → row reduction → broadcast tail → PackOp`), fix two fragile heuristics in `compiler/blackhole/pipeline.py:38-80`:

1. **Fragile `MoveToDst` lookahead (`pipeline.py:72-73`):**
   - Currently checks `if spec_at(i, MoveToDst) and wi + 1 < len(work) and footprint(work[wi + 1]): release = ends[work[wi + 1]]`.
   - When an epilogue has **multiple** `bf16` inputs (`Unpack(A) -> MoveToDst(s1)`, `Unpack(B) -> MoveToDst(s2)`, `RANGE(fp)`), or mixes `bf16` (`MoveToDst`) with `fp32` (`UnpackOp(DST)`), `s1`'s credit is released before `fp` runs, and consecutive unpacks into different `Dst` slots can race if a loop wraps around.
   - **Fix:** Determine `sem 0` (input/scratch `Dst` credit) release by scanning forward to the **last** `RANGE("fp")` / `FpuOp` in the same loop scope that reads `spec.dst_slot` (or hold `sem 0` until the end of the consuming `RANGE("fp")` for all `MoveToDst` / `UnpackOp(DST)` feeding that footprint).
2. **Implicit `PackOp` phase grouping (`pipeline.py:38-80`):**
   - Verify explicitly that every `UnpackOp` is matched by a consumer in the same `Dst` ownership window, and support multiple sequential `RANGE("fp")` phases (e.g. `MVMUL -> fp1 (epilogue) -> fp2 (reduction) -> PackOp`) cleanly without requiring an intermediate `PackOp` between them.
   - Add a lightweight `verify_tile_stream(stream)` assertion in `compile_tile_graph` checking balanced `SemOp` wait/get/post and `CbOp` reserve/push/wait/pop counts per loop level before codegen, so sync bugs fail fast on CPU instead of hanging hardware.

---

## 4. Target Module Layout

| File | Action | Responsibility |
|---|---|---|
| `compiler/blackhole/fpu.py` | **Create** | Declarative `FpuRule` table, range-set contraction matcher, horizontal reduction classifier, whole-AST face `PADTO`/`SPLIT`, `face_rows` assignment |
| `compiler/blackhole/schedule.py` | **Create** | `Schedule` dataclass and policy (`select_schedule`, `invariant_axis`) choosing 1D vs 2D mcast, `(bm, bn)`, `sk`, and `prefetch_k` |
| `compiler/blackhole/alloc.py` | **Create** | Liveness-based CB (`0..31`), L1 (`0x20000..0x180000`), and `Dst` (`0..55`) allocator |
| `compiler/blackhole/lower.py` | **Rewrite** | Thin entry point (`lower_kernel`) + Stage 1 inliner + Pass 4 unified tile-DAG lowerer (`to_space`, per-load classifier, `MVMUL` / `ROW_REDUCE` / SFPU / stage lowering) |
| `compiler/blackhole/pipeline.py` | **Harden** | Multi-phase `insert_syncs()` + `verify_tile_stream()` |
| `compiler/blackhole/map.py` | **Delete** | Subsumed by unified base path (`NocRead`/`NocGather`/`NocScatter`/`IndexTile`) |
| `compiler/blackhole/matmul.py` | **Delete** | Subsumed by `MatchedMvmul` with `weight_layout = 8` (`NocGather` 256 lanes) |
| `compiler/blackhole/mcast.py` | **Delete** | Subsumed by `Schedule(grid=(cols, rows))` + `invariant_axis` |
| `compiler/blackhole/reduction.py` | **Delete** | `reduce_expression` core folded into `lower.py` (generalized to any `acc_slot` and nested reductions) |
| `compiler/blackhole/argmax.py` | **Delete** | Subsumed automatically by nested `MatchedRowReduce` + `IndexTile` |
| `compiler/blackhole/staged.py` | **Delete** | Subsumed by Pass 1 stage normalization + L1 `ALLOC` stage lowering in `lower.py` |

*(Unchanged: `specs.py`, `recipes.py`, `sfpu.py`, `scalar.py`, `runtime.py`, `compiler/isa/`, `fw/`, `hw/`, `device.py`.)*

---

## 5. Incremental Migration Plan

Execute in small commits where `python3 -m pytest -q` (and `BH_HW=1` when on hardware) stays green at every step:

1. **Step 1 — Allocator & `pipeline.py` verifier:**
   - Add `compiler/blackhole/alloc.py` and `verify_tile_stream()` + multi-phase `insert_syncs()` fixes in `pipeline.py`.
   - Unit-test multi-input epilogues (`2× bf16` + `1× fp32` into one `RANGE("fp")`) and nested `RANGE("fp")` phases in `test/test_tile_pipeline.py`.
2. **Step 2 — Unified SFPU base path (delete `map.py`, `reduction.py`, `argmax.py`, `staged.py`):**
   - Implement Pass 1 (stage normalization), Pass 2 (horizontal `MatchedRowReduce` + nested reduction support), and Pass 4 (`to_space`, per-load `NocRead`/`SfpBroadcastRows`/`NocGather`/`IndexTile`).
   - Route all non-`MVMUL` kernels through the unified lowerer; delete `map.py`, `reduction.py`, `argmax.py`, `staged.py`.
   - Verify: `test_map_blackhole.py`, `test_reduction_blackhole.py`, `test_tensor_blackhole.py`, `test_sfpu.py`.
3. **Step 3 — Declarative `MVMUL` matcher + 1D schedule (delete `matmul.py` and old 1D matmul block in `lower.py`):**
   - Implement `fpu.py` (`FpuRule("MVMUL")` + range-set matching + `face_rows` rule separating static 2D weights from transient `8×16` RHS).
   - Route 1D decode matmuls, SwiGLU (`2× MVMUL`), batched matmuls (attention `Q @ K^T`, `attn @ V`), and matmul + broadcast residual epilogues through the unified lowerer; delete `matmul.py`.
   - Verify: `test_matmul_blocks.py`, `test_packed_checkpoint.py`, `test_nanbeige_e2e.py`.
4. **Step 4 — 2D multicast as a schedule choice (delete `mcast.py`):**
   - Implement `schedule.py` with `grid=(cols, rows)`, `(bm, bn)`, `sk`, and `invariant_axis`.
   - Route 2D multicast matmuls (including broadcast epilogues and SwiGLU) through the exact same `lower.py` loop; delete `mcast.py`.
   - Verify: `test_mcast_control.py`, `test_matmul_mcast.py`, `examples/benchmark_matmul_mcast.py` (confirm no TFLOP/s regression).
5. **Step 5 — Preserve N-D `INDEX` & remove `materialize=True` hacks in `examples/nanbeige.py`:**
   - Remove unnecessary `.contiguous()` boundaries in `examples/nanbeige.py` (`Linear.materialize`, `Attention.materialize`) one by one:
     1. `gate.silu() * up` (already fused in 1D/2D — verify both paths)
     2. `down_proj + residual` and `o_proj + residual` (including broadcast bias)
     3. `scores * scale + causal_mask + softmax` (matmul + `IndexTile` + row reductions in one kernel)
     4. Full `logits.flatten().argmax()` without `argmax.py`
   - Run `BH_NANBEIGE=1 python3 -m pytest -q test/test_nanbeige_e2e.py` and confirm exact token-for-token match.

---

## 6. Verification Commands

```sh
# Fast CPU compiler, ISA, sync-verifier, and control tests (run after every step)
python3 -m pytest -q

# Full hardware regression suite
BH_HW=1 python3 -m pytest -q

# Real 2D multicast Nanbeige projections (throughput + correctness)
BH_MCAST_REAL=1 python3 -m pytest -q test/test_matmul_mcast.py -k real_nanbeige

# Full 52-layer Nanbeige4.3-33B end-to-end token match
BH_NANBEIGE=1 python3 -m pytest -q test/test_nanbeige_e2e.py
```

---

## 7. Ideal End State (Lowering-Wise)

Once the middle-end refactor lands and the subsequent hardware/codegen optimizations are layered on top, the compiler reaches a clean 3-stage separation where **semantics, scheduling, and hardware execution are completely orthogonal**:

```text
Layer 0: Tensor / UOp graph (zero .contiguous() / materialize hacks, zero custom_kernel)
   │
   ▼  [1. Frontend — Semantics & Kernel Boundaries (rangeify.py, memory.py)]
      • Decides kernel fusion purely from L1/DRAM budgets, never to appease backend templates
      • Preserves N-D INDEX structure and explicit L1 Ops.ALLOC stages per kernel
   │
   ▼  [2. Middle End — Match -> Schedule -> Tile DAG (fpu.py, schedule.py, lower.py, alloc.py)]
      • Declarative subexpression matcher: tinygrad-TC-style range-set rules match every
        eligible FPU op (MVMUL, and optionally ELW*/POOL); everything else (pointwise,
        horizontal/nested reductions, masks, IndexTile, NocGather/Scatter) stays on SFPU;
        unmatched contractions fail loudly on the exact UOp
      • Schedule is pure data: 1D vs 2D grid, (bm, bn, sk, k_blk), invariant_axis multicast,
        K-prefetch, double-buffering (Dst halves + 2-page CBs) — tunable by heuristic or BEAM
        without touching lowering code
      • One mechanical lowerer: to_space() inserts all DRAM↔L1↔Src↔Dst↔LReg transfers;
        one liveness allocator assigns CBs, L1 rings, and Dst slots (0..31 double-buf / 0..55)
   │
   ▼  [3. Backend — 5-Core Concurrency & Hardware Codegen (pipeline.py, recipes.py, sfpu.py, isa/)]
      • Linearize once -> hazard-driven sync insertion (overlapped CB pipelining +
        double-buffered math/pack semaphores) -> 5-core projection
      • State-tracked config diffing hoists static UNPACR/MATH/PACK config out of K-loops
      • Late TRISC compression while RANGE/END loops are still intact:
          SFPLOADMACRO (parity-aware L0..L3 / L4..L7) -> REPLAY -> MOP Template 1
      • RV32 scalar isel, CFG-aware regalloc, SFPU hazard fixing, BH01 assembly
```

### What This Buys You (Litmus Tests)
1. **New fused patterns need zero new lowerers:** Fused SwiGLU, `down_proj + broadcast bias + residual`, `Q @ K^T * scale + causal mask + softmax`, `RMSNorm` + projection, MoE router + gather, and `argmax` all compile through the exact same pipeline.
2. **Performance work is global, not per-template:** Enabling double-buffered `Dst` (`sem math_pack max=2`), 2-page pipelined CBs (overlapping `brisc` DRAM read `k+1` with `trisc0/1` compute `k`), `N_BLK` decode strips, or `SFPLOADMACRO → REPLAY → MOP` compression happens once in `schedule.py` / `pipeline.py` / `recipes.py` and speeds up **every** kernel automatically.
3. **Scheduling becomes searchable:** Because `Schedule` is a small, verified dataclass decoupled from lowering, you can start with simple heuristics and later plug in a BEAM-style autotuner over `(grid, bm, bn, sk, prefetch, double_buf)` just like tinygrad — while keeping the exact same tile-DAG lowerer and 5-core backend underneath.

