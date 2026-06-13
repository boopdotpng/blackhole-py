# microbenching/status.md

Single source of truth for what runs in `microbenching/`. All other markdown
under this directory was removed (`README.md`, `todo.md`, `docs/`, `logs/`)
and this file replaces it.

Hardware runs use the shared `tt-device-queue` MCP. Raw per-command output is in
`/home/boop/tenstorrent/tt-device-queue/logs/<job-id>/output`. Job IDs below are
real results from the refresh sweep that produced this file.

## How to run

```bash
# From repo root
PYTHONPATH=. python3 microbenching/tensix/microbench_sfpu_transcendental.py --iters 4096

# Through the shared device queue (recommended)
PYTHONPATH=. python3 microbenching/tensix/microbench_sfpu_transcendental.py --iters 4096
```

Most scripts import `microbenching/harness.py`, which sets `TT_USB=1` (slow
dispatch) and bootstraps paths. Some older scripts set `TT_USB=0` themselves;
when in doubt run the exact command from the job history below.

## Verification criteria

A bench is marked **compute-proof** only when the kernel emits TRISC math/SFPU
instructions and the host validates the returned tile against a numpy reference.
Benches that only move data, only read status words, or require host assistance
for scaling/constants are labeled separately. Timing is issue-side wall-clock on
the executing RISC (usually TRISC1) with a trailing `STALLWAIT`/`SYNC` drain,
except for end-to-end kernel benches (GEMV, matmul) where the number is the full
launch-to-completion time.

## Primitive inventory

### LOAD / STORE / INDEX / RANGE / CONST

| primitive | status | evidence | notes |
|---|---|---|---|
| SFPU tile LOAD/STORE | **RUNS** | used by every SFPU bench; absolute addr-mod offsets | `SFPLOAD`/`SFPSTORE` with fmt=2 bf16 |
| CONST tile fill | **RUNS** | `ttk.sfpu.emit_constant_tile` | writes a fp32 constant to every element |
| INDEX / RANGE / generic gather-scatter | **MISSING** | — | no reusable primitive; embedding gather and KV scatter are custom NCRISC kernels |

### Movement-as-indexing

| primitive | status | evidence | notes |
|---|---|---|---|
| TILIZE / UNTILIZE | **BROKEN** | `microbench_tilize.py` | fresh run `34440c2b` timed out waiting for core `(1,2)`; older notes mentioned wrong output permutation. Untilize remains host-only |
| COPY (tile) | **RUNS** | `add1.py`, `matmul_peak` GEMV | implicit in unpack/math/pack pipeline |
| FILL | **RUNS** | `emit_constant_tile` | const-fill primitive |
| RESHAPE / PERMUTE / EXPAND / PAD / SHRINK / FLIP | **MISSING** | — | no generic primitives; broadcast is the closest working layout transform |

### Elementwise unary

| op | status | bench | timing | notes |
|---|---|---|---|---|
| NEG | **MISSING** | — | — | not implemented |
| RECIPROCAL | **RUNS** | `microbench_sfpu_transcendental.py` | 16 cyc/op (32 lanes) | 2 Newton iterations, max_rel ~0.64% |
| SQRT | **MISSING** | — | — | only `rsqrt` Newton exists, and it is near-unit only |
| RSQRT (near-unit) | **RUNS** | `microbench_sfpu_transcendental.py` | 58 cyc/op | 5 Newton iterations, valid ~[0.5,2]; **not** a wide-range rsqrt |
| EXP2 / EXP | **RUNS** | `microbench_sfpu_transcendental.py` | 40 cyc/op | natural exp (`exp2` base transform inside) |
| LOG2 / LOG | **MISSING** | — | — | not implemented |
| SIN | **MISSING** | — | — | not implemented |
| TRUNC / CAST / BITCAST | **MISSING** | — | — | not implemented |
| ABS | **MISSING** | — | — | not implemented |
| GELU | **MISSING** | — | — | not implemented |
| SIGMOID | **RUNS** | `microbench_sfpu_transcendental.py` | 59 cyc/op | composite exp+recip+1 |
| SiLU | **RUNS** | `microbench_sfpu_transcendental.py` | 62 cyc/op | x * sigmoid(x) |

### Elementwise binary

| op | status | bench | timing | notes |
|---|---|---|---|---|
| ADD | **RUNS** | `microbench_eltwise_binary.py` | 676 cyc/tile | tile+tile, bf16 |
| MUL | **RUNS** | `microbench_eltwise_binary.py` | 680 cyc/tile | LoFi mul, ~3% low bias expected |
| SUB | **RUNS** | `microbench_eltwise_binary.py` | 682 cyc/tile | tile+tile, bf16 |
| MAX | **MISSING** | — | — | SFPU has max-reduce helpers but no elementwise MAX tile-map |
| Compares (cmplt/cmpne/cmpeq) | **MISSING** | — | — | needed for masks / WHERE |
| Shifts / bitwise | **MISSING** | — | — | `dsl.py` has RISC DMA-reg shift/cmp/bitw opcodes but no Tensix tile primitive |
| DIV / MOD | **MISSING** | — | — | no tile-level integer or fp div/mod |

### Broadcast binary

| variant | status | bench | timing | notes |
|---|---|---|---|---|
| row broadcast ADD/MUL | **RUNS** | `microbench_eltwise_bcast.py` | ~678 cyc/tile | `B[0,c]` applied to `A[r,c]` |
| col broadcast ADD/MUL | **RUNS** | `microbench_eltwise_bcast.py` | ~835 cyc/tile | `B[r,0]` applied to `A[r,c]` |
| scalar broadcast ADD/MUL | **RUNS** | `microbench_eltwise_bcast.py` | ~720 cyc/tile | `B[0,0]` applied to whole tile |

### Ternary

| op | status | evidence | notes |
|---|---|---|---|
| WHERE | **MISSING** | — | no compare/select primitive |
| MULACC (FMA) | **MISSING** | — | matmul uses `MVMUL`, not a generic tile FMA primitive |

### Reductions

| op | status | bench | timing | notes |
|---|---|---|---|---|
| REDUCE ADD (32-lane sum) | **RUNS** | `microbench_sfpu_reduce.py` | 51 cyc/op | `emit_sum_reduce_32` |
| REDUCE MAX (32-lane max) | **RUNS** | `microbench_sfpu_reduce.py` | 51 cyc/op | `emit_horizontal_reduce_max` |
| REDUCE MAX (per-row over 32x32) | **RUNS** | `microbench_sfpu_reduce.py` | 293 cyc/tile | `emit_reduce_row_max_tile` |
| REDUCE MUL | **MISSING** | — | not implemented |
| Argmax (value) | **RUNS** | `microbench_sfpu_argmax.py` | — | 32-lane + N-staged value max works |
| Argmax (index) | **PARTIAL** | `microbench_sfpu_argmax.py` | — | N-staged captured-lane index PASS; single 32-lane index XFAIL |

### Matmul / GEMV

| primitive | status | bench | timing | notes |
|---|---|---|---|---|
| GEMV M=1 | **RUNS** | `microbench_skinny_gemv.py` | 92.7 GB/s blended | real unpack/math/pack pipeline, PCC ~0.9999 |
| Full matmul [M,K]@[K,N] | **UNSTABLE** | `examples/matmul_peak.py 64 64 64` | — | timed out in current tree; GEMV is the stable matmul-like primitive |
| Tile-K MVMUL | **RUNS** (isolated) | `microbench_math_backend.py` | 102 cyc/program_mop | math backend proof only, not a usable public primitive |
| Composite: softmax row | **RUNS** | `microbench_softmax.py` | 2746 cyc/tile | exp + reduce + recip on SFPU |
| Composite: RMSNorm inv | **RUNS** | `microbench_rmsnorm_inv.py` | 3 launches, ~22 us | staged reductions on device |
| Composite: RoPE | **RUNS** | `microbench_rope_k_scatter.py` | ~14.8 us | SFPU rotate + NCRISC scatter |

## Recent hardware job history

| area | command | job | result |
|---|---|---|---|
| smoke | `PYTHONPATH=. python3 examples/add1.py --tiles-per-core 1 --cores one` | `4a44dcb0` | PASS |
| SFPU unary | `microbench_sfpu_transcendental.py --iters 4096` | `e7a9b047` | PASS exp/recip/rsqrt/sigmoid/silu |
| SFPU reduce | `microbench_sfpu_reduce.py --iters 4096` | `4d7ab968` | PASS sum/max/rowmax |
| binary bcast | `microbench_eltwise_bcast.py --iters 8` | `e755b8b5` | PASS row/col/scalar add/mul |
| binary | `microbench_eltwise_binary.py --iters 8` | `edf34159` | PASS add/sub/mul |
| softmax | `microbench_softmax.py --iters 8` | `3d11d4d7` | PASS 2746 cyc/tile |
| RMSNorm | `microbench_rmsnorm_inv.py` | `49e259bf` | PASS rel=0.000303 |
| RoPE | `microbench_rope_k_scatter.py` | `1fcd42f4` | PASS |
| math backend | `microbench_math_backend.py --iters 100 --no-report` | `6859cc30` | PASS |
| unpack backend | `microbench_unpack_backend.py --no-report` | `d06e74ff` | PASS |
| pack backend | `microbench_pack_backend.py --no-report` | `763d7409` | PASS empty-only smoke |
| sem/CB | `microbench_sem_cb.py --no-report` | `58cfdba0` | PASS |
| instr issue | `tensix_instr_bench.py --no-report` | `72386724` | PASS |
| argmax | `microbench_sfpu_argmax.py --n 1024 --cores 4` | `434f6c99` | VALUE PASS; index XFAIL (single), PASS (N-stage) |
| GEMV | `microbench_skinny_gemv.py` | `d7b20adf` | PASS 92.7 GB/s |

Failed / gated runs during this refresh:

| command | job | reason |
|---|---|---|
| `microbench_math_backend.py --iters 100` | `dbe57150` | FAIL: default report path `docs/tensix/math-backend-microbench.md` no longer exists; use `--no-report` |
| `tensix_instr_bench.py` | `3d2cc804` | FAIL: same report-path issue; use `--no-report` |
| `microbench_sem_cb.py` | `8b3bbdf8` | FAIL: same report-path issue; use `--no-report` |
| `microbench_xmov.py --no-report` | `406ff105` | FAIL: timeout on mover paths (quarantined) |
| `microbench_xmov.py --no-report --no-readback-probe --tests <dma_reg_only>` | `c1f8eb64` | FAIL: timeout even on DMA-reg subset in current tree |
| `microbench_tilize.py` | `34440c2b` | FAIL: timeout waiting for core `(1,2)`; device reset `e6ae0981` completed and follow-up add1 smoke `ace70ce3` passed |
| `examples/matmul_peak.py 64 64 64` | `5863905f` | FAIL: timeout waiting for core (1,2) |
| `microbenching/matmul/microbench_attention_scores_softmax.py` | `c733292f` | FAIL: CQ timeout |

## What's verified as real Tensix compute

- **Add1/copy scaffold**: one-core add1 still passes after the tilize timeout
  and reset (`ace70ce3`, 14.8 us for one tile).
- **SFPU transcendentals**: TRISC1 SFPU instructions, varied inputs, full tile
  readback vs numpy. Timings are TRISC1 wall-clock around the SFPU body.
- **SFPU reductions**: same scaffold; sum/max/rowmax validated against numpy.
- **Eltwise binary/bcast**: TRISC0 unpack, TRISC1 `ELWADD/ELWMUL/ELWSUB`, TRISC2
  pack, full tile readback vs numpy.
- **Softmax**: TRISC1 SFPU composite (rowmax, exp, sum, recip) with full tile
  readback.
- **RMSNorm inverse**: staged device reductions, scalar readback vs host ref.
- **GEMV**: full unpack/math/pack pipeline, output readback vs numpy, PCC
  ~0.9999.

## Broken / not working now

These are not just missing abstractions; they have recent failures or are known
unsafe to run casually.

- `microbench_tilize.py`: current run `34440c2b` timed out waiting for core
  `(1,2)`. This supersedes the older "wrong permutation" note until a new
  permutation-producing run is captured.
- `microbench_xmov.py`: times out on both the full mover suite and the reduced
  DMA-reg subset (`406ff105`, `c1f8eb64`).
- `examples/matmul_peak.py 64 64 64`: current full-matmul path times out under
  slow dispatch (`5863905f`); `microbench_skinny_gemv.py` is the stable
  matmul-like path.
- `microbenching/matmul/microbench_attention_scores_softmax.py`: current
  attention bridge run hit a CQ completion timeout (`c733292f`).
- Report-writing defaults are broken for old report benches after `docs/`
  removal. Use `--no-report` for `microbench_math_backend.py`,
  `tensix_instr_bench.py`, `microbench_sem_cb.py`, and similar report appenders.
- `microbench_dest_readback.py`, `microbench_sfpu.py` debug-readback validation,
  and `microbench_pack_backend.py --validate` remain quarantined.

## Missing kernel support now

The user target list and current support:

1. Generic unary tile-map: **exp/recip/rsqrt(near-unit)/sigmoid/silu run**;
   neg, wide-range sqrt/rsqrt, log2/log, sin, abs, cast/trunc/bitcast, and GELU
   are missing as reusable tile kernels.
2. Generic binary tile-map: **add/sub/mul and row/col/scalar broadcast run**;
   elementwise max, scalar-immediate arithmetic as a public primitive, and
   div/mod are missing.
3. Compare/select: **cmplt/cmpne/cmpeq/where missing**. This blocks generic
   masks, gated padding, causal masking, and tinygrad `WHERE` lowering.
4. Reductions: **sum/max/rowmax run**; product, reusable shape-aware multi-tile
   reductions, hidden-dim reductions, and cross-core reductions are missing.
   Argmax value works; captured-lane index works in the N-stage path but the
   single 32-lane index path is still XFAIL.
5. Movement/layout: **copy/fill run**; tilize is broken, untilize is host-only,
   and generic reshape/permute/expand/pad/shrink/flip lowering is missing.
   Broadcast works only through the eltwise broadcast kernels.
6. Matmul/GEMV: **GEMV runs**; full [M,K]@[K,N] matmul unstable, decode GEMV,
   K-blocking, batching, epilogues missing as public primitives.
7. Composites: **softmax row, RMSNorm inv, RoPE run**; KV read/write scatter
   exists as custom NCRISC, argmax partial.

In other words, the current runnable compute set is strong enough for add/mul
style elementwise, softmax/RMSNorm/RoPE pieces, and M=1 GEMV experiments. The
missing support for a tinygrad lowering target is mostly a reusable kernel
library around movement/indexing, compare/select, wider unary math, multi-tile
reductions, and full matmul/attention programs.

## Quarantined / do not run blindly

- `microbench_dest_readback.py` hardware path.
- `microbench_sfpu.py` debug-readback validation path.
- `microbench_xmov.py` mover/debug/readback rows.
- `microbench_tilize.py`.
- `microbench_pack_backend.py --validate`.
- Full `examples/matmul_peak.py` and attention bridge paths until they are
  re-audited; `microbench_skinny_gemv.py` is the current stable matmul-like
  primitive.

## Suggested PoC order (from target list)

1. copy, fill_const, cast, add1 — copy/fill/add1 run; cast missing.
2. generic unary tile-map — exp/recip run; extend to neg/sqrt/log2/sin/abs.
3. generic binary tile-map with scalar/row/col broadcast — runs.
4. where/compare — missing.
5. row sum/max reductions — runs.
6. multi-tile reductions — partial (argmax N-stage works).
7. softmax row — runs.
8. RMSNorm — inv_rms runs.
9. GEMV/matmul with epilogue — GEMV runs; matmul/epilogue unstable.
10. embedding gather and KV scatter/slice-store — custom NCRISC proofs exist.
