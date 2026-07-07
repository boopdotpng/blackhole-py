# TTIR — the tile-native kernel IR

TTIR is the IR you write kernels in and lower to RISC-V that runs on Tensix
cores. tinygrad lowers to it; humans can author it directly. It replaces the
"semantic layer" kir was reaching for (see §11 for the kir migration map).

Design axioms, in one breath: **the atom is a 32×32 tile; every op is
tile→tile; all dataflow sync is tile-counting; there is exactly one lowering per
op, so the "compiler" is a table, not a search.**

```
tinygrad Tensor graph
   │  intercept PRE-RANGEIFY uops (intent intact: REDUCE(axis), matmul, softmax)
   ▼
TTIR  (this doc)  — tile-native, SSA over tiles
   │  linearize: schedule → engine-assign → sync-insert → emit  (§8)
   ▼
5 straight-line RISC-V programs (brisc/ncrisc/trisc0/1/2) → Tensix words → device
```

---

## 1. Values: three types, one atom

- **`Tile`** — one 32×32 tile; an **SSA value** with a `dtype`. Single-assignment,
  immutable. The author never says *where* it lives; whether a `Tile` is a CB
  slot, SrcA, SrcB, or a DST register is decided by lowering. This is the whole
  "write only the ops" payoff.
- **`Tensor`** — a named DRAM/L1 buffer = a **grid of tiles** with metadata
  (§2). This is *storage*; you stream it or index it into `Tile`s.
- **`Stream`** — an ordered sequence of tiles, the loop-carried form; what maps
  onto a CB. `stream(tensor)` reads tiles out; `out << tile` pushes tiles in.
  Streams are **sugar** over indexed-tile loops (§5).

## 2. Tensor metadata

```python
@dataclass(frozen=True)
class DType:
    name: str          # "bf16" | "fp32" | "fp16" | "bfp8" ...
    tile_bytes: int    # per 32x32 tile: bf16/fp16=2048, fp32=4096, bfp8~1088

@dataclass(frozen=True)
class Layout:
    kind: str          # "tiled" (32x32, face-swizzled) | "row_major"

@dataclass
class Tensor:
    name: str
    dtype: DType
    shape: tuple[int, ...]     # LOGICAL/original dims — kept for untilize + pad masks
    layout: Layout             # declarative TYPE; coercion nodes inserted at mismatched edges (§4)
    where: str = "dram"        # "dram" | "l1"
    addr: int | None = None    # base address (allocator-filled) -> reader/writer addressing
    banks: int = 8             # dram bank interleave
    shard: "Shard | None" = None   # tile distribution across the core grid (§7)
    # derived: padded_shape (last two dims up to 32), tile_grid, num_tiles,
    #          page_bytes = dtype.tile_bytes (one tile per CB page)
```

| field | drives |
|---|---|
| `dtype.tile_bytes` | CB page size, DST capacity, unpack/pack format |
| `shape` (original) | untilize crop + padding masks — unrecoverable from padded storage |
| `layout.kind` | whether an edge needs `tilize`/`untilize` (§4) |
| `addr`/`banks` | brisc/ncrisc NOC addressing — static plumbing, generated not written |
| `shard` | HARD fusion boundary: a reduce/gather across the shard axis crosses cores |

## 3. Node taxonomy — three categories

**a) Compute (tile → tile) — you author these:**
```
mul add sub max  exp2 log2 recip sqrt gelu ...      # SFPU/FPU, Tile... -> Tile
matmul(a, b, *, out_dtype) -> Tile                   # tile·tile MAC, K-reduction into DST
reduce_across(op, stream, *, out_dtype) -> Tile      # fold tiles (DST accumulate)
reduce_intile(op, tile, axis, *, out_dtype) -> Tile  # 32x32 within-tile reduce (reduce-LLK)
mask(tile, lane_pred) / masked reduce                # the sub-tile escape hatch (§10)
```

`out_dtype` on a reduce/matmul is the **accumulation dtype** — there is no
separate accumulator concept. tinygrad expresses this identically: a matmul is
`REDUCE(ADD, dtype=float, MUL(EXPAND, EXPAND))` — the REDUCE node's output dtype
*is* the accumulation dtype; `MUL(bf16,bf16)→bf16`, then `REDUCE(...,float)→float`.
`out_dtype=fp32` ⇒ fp32_dest_acc (halves DST, subblock ≤4/half, cb24 reload
ping, ZEROACC flag, packer 32b read); `out_dtype=bf16` ⇒ all of that off. The
full chain is an op `effect` in the codegen state machine (§9), not a knob the
author manages — making the knob-consistency checker redundant by construction.

**b) Movement (tiles change location) — mined templates, not hand-derived:**
```
load(tensor) -> Stream        # brisc / NOC0  — template keyed by (layout, banks, out_dtype)
store(stream, tensor)          # ncrisc / NOC1 — same
gather / broadcast / all_reduce  across cores  # NOC, tier-2 sync (§7)
```
Reader/writer bodies are **mined from working kernels** (§9), parameterized by
`Tensor` metadata (`layout`, `banks`, `addr`) and `out_dtype`. The mcast
rectangle, sender/receiver role, linked-VC, path-reservation, and overlay-vs-
command-buffer choices are **production defaults baked into the template**, not
IR-level knobs — they were env-gated during iteration (matmul_peak) but the
default path is what ships.

**c) Coercion (tiles change type) — inserted at type-mismatch edges (§4):**
```
cast(tile, dtype) -> Tile      # dtype conversion (SFPU cast or format-converting un/pack)
tilize(tile) / untilize(tile)  # layout conversion (tilize-LLK or format-converting un/pack)
```

## 4. Coercions are a type system

`Tensor` carries the **declarative type** (`dtype` + `layout`). Coercion nodes
are **inserted by a pass** wherever an edge connects mismatched types — dtype
differs → `cast`; layout differs → `tilize`/`untilize` — exactly like sync is
inserted at dataflow edges. The author never hand-writes them, but they are
**visible IR nodes** (the pretty-printer and checkers see them; they are not
hidden `Tensor` mutations).

They are not free (unlike a GPU register cast): `cast` lowers to an SFPU cast or
a format-converting pack/unpack; `tilize`/`untilize` to the tilize-LLK or a
format-converting unpack. **Lowering may fold a coercion into the adjacent
unpack/pack** (the datapath converts format on the fly), so a coercion node
often emits zero extra instructions — it just sets the neighbor's format config.
Represent them explicitly first (correct + legible); fold as an optimization.

## 5. Streams vs indexed tiles

Not an either/or — `Stream` is sugar over an indexed-tile loop, and the core is
indexed tiles + explicit loops:

- **Streams** fit the 1D pointwise march: `out <<= stream(a) * stream(b)`. CB is
  a FIFO, the loop is "for each tile," no addressing. Elementwise / activations.
- **Indexed tiles** are unavoidable for matmul/attention:
  `C[i,j] = Σ_k A[i,k]·B[k,j]` is 2D tile addressing with a k-accumulation loop.
  matmul_peak makes this explicit as `in0_block` / `out_subblock` tiling — and
  **that tiling is chosen to fit DST** (§6). You cannot express it as one `zip`.

Rule: streams for pointwise; indices for anything with a reduction or 2D
structure. **DST allocation lives in the indexed layer** (the subblock loop =
the DST-half tiling); streams hide it for the single-pass case.

**Subblock size is derived, not chosen.** The subblock (group of tiles filled
into one DST half before a pack) is `min(output_tiles, dst_half_capacity)` where
`dst_half_capacity(out_dtype=fp32) = 4` and `dst_half_capacity(out_dtype=bf16) =
8`. The author never specifies it; the lowerer computes it from the
reduce/matmul node's `out_dtype` and uses it as a loop count in the MOP template.

## 6. Two sync layers (confirmed against matmul_peak)

**Layer A — dataflow sync, fully tile-counted. This lives in TTIR.**
- CB handshakes count **tiles**, in **blocks/subblocks**: `cb_wait_front(cb, N_tiles)`,
  `cb_pop_front(cb, N_tiles)`. Never fractional.
- Semaphores are **bounded counters** (`max_value=2` → double-buffer): UNPACK_SYNC,
  MATH_PACK, MATH_DONE, UNPACK_TO_DEST. Each tick = one tile/subblock event.
- TTIR models this as ONE node: `Wait(edge, count, scope)`. Every concrete
  handshake (cb credit, MATH_PACK sem, NOC credit) is this primitive at a
  different scope; lowering picks the mechanism.
- **Counting unit is a subblock** (a group of tiles sized to fit DST-half), not a
  single tile. `Wait` counts allow N tiles; the subblock size *is* the
  DST-capacity tiling, derived from `out_dtype` (§5).
- **CB ack ordering is per-engine, not an IR contract.** Deferred
  `TTSTOREREG` ack (mandatory when the consumer is trisc0 — the unpacker hasn't
  consumed the tile yet) vs eager RISC store (brisc/ncrisc) is fixed by which
  engine owns the pop. It rides inside the movement template (§3b, §9), not in
  the `Wait` node.

**Layer B — pipeline-hazard stalls, NOT tile-counted. This lives in TEMPLATES, not TTIR.**
- `TTSTALLWAIT` on engine-busy flags (THCON config-before-use, MATH|SFPU pipe
  drain before pack reads DST, PACK0 done) and `tensix_sync` pipe flushes. No
  count; pure intra-op ordering, firing *within* processing a tile/subblock.
- Mechanical and fixed per op-type (every MOP-config write → `STALLWAIT(THCON)`;
  every math group → `STALLWAIT(MATH|SFPU)`). The author never reasons about
  them — they ride inside each op's lowering template (§9). This is why the tile
  model stays clean: Layer B never surfaces above codegen.

## 7. 118 cores = SPMD + collectives

A program is **one per-core tile-program, replicated**, each core owning a shard
of the TileGrids (`Tensor.shard`). An edge whose producer and consumer are on
different cores becomes a NOC collective (`all_reduce`, `gather`, `broadcast`)
with tier-2 sync, and marks a **HARD** fusion boundary. "Core-local or not" is
read straight off the shard — no analysis pass. This is what makes rmsnorm 5
launches (cross-core mean) vs 1 (redundant-local): the `all_reduce` is a hard
edge; nothing is special-cased.

## 8. Lowering = our own linearizer → five straight lines

tinygrad's linearizer flattens the DAG into one scalar-indexed stream (GPU
math). Ours produces the tile-native shape via four passes:

1. **Schedule** — tile-DAG → topological order of tile-ops, constrained by DST
   residency. *This is where the fusion / DST-capacity decision happens.*
2. **Engine-assign** — each op's substeps route to fixed engines: loads→brisc,
   stores→ncrisc, unpack→trisc0, math→trisc1, pack→trisc2.
3. **Sync-insert** — Layer-A tile-count handshakes on every edge (Layer B rides
   in templates).
4. **Emit** — each engine's ordered ops → straight-line RISC-V (loops allowed).

Output: **5 coordinated straight-line programs**, not one.

### 8.1 Fusion tiers — what fuses, how much, when it stops

On a GPU, fusion = "one kernel launch, data stays in registers/shared memory."
The limit is register pressure (255 regs) and shared memory (48–96 KiB/SM).
Two matmuls cannot fuse (different grid configs, different launch dimensions).

On Tenstorrent, fusion = "one Program launch, data stays in DST and/or L1 CBs."
The pipeline is fixed per core:

```
brisc (reader) → trisc0 (unpack) → trisc1 (math/SFPU) → trisc2 (pack) → ncrisc (writer)
```

A Program can cycle through this pipeline **multiple times** via on-device
loops — each cycle is one "DST residency window." So multiple matmuls CAN be in
one Program, connected by CBs in L1, with SFPU epilogues/prologues riding free
on the DST values between matmuls. This is structurally different from a GPU.

**Three fusion tiers, in increasing cost order:**

**Tier 1 — DST-resident (free, unlimited op count).**
SFPU epilogue/prologue on a value currently in DST. The SFPU reads/writes the
**same DST tiles** — no L1 round-trip, no CB, no sync node. This is where
`acc * inv_rms`, `silu(gate) * up`, `x * cos + rotated * sin`, residual add,
scale-by-scalar, cast, recip, exp2 all live. **No limit on op count** — chain
as many SFPU ops as you want while the value stays in DST. The only boundary is
"the value must leave DST" (pack to CB) to make room for the next matmul's
accumulator. This is the fusion the codegen state machine (§9) enables
trivially: each SFPU op is a `(requires, body, effect)` that reads/writes DST
with no config transition beyond SFPU mode.

**Tier 2 — L1-resident (cheap, bounded by L1 capacity).**
Multiple matmuls chained through CBs in L1. The first matmul packs its result
to a CB; the second matmul unpacks from that CB. Each matmul is a new DST
residency window, but the data never leaves L1. Bounded by:
```
sum(all CB sizes for fused stages) ≤ ~1.28 MiB L1 budget
```
For decode BS=1, intermediates are tiny (a 2048-wide bf16 vector = 4 KiB per
CB). You can chain many matmuls + SFPU stages in one Program. This is what
enables "5 programs/layer" — each Program is a matmul + SFPU epilogue, connected
by L1 CBs, and only the weight stream hits DRAM.

**Tier 3 — DRAM / cross-core boundary (expensive, always a Program boundary).**
The value must go to DRAM. Happens when:
- L1 is full (large intermediates — prefill with S>1, or a fused stage's CB
  set exceeds 1.28 MiB).
- The value crosses cores (shard boundary — the producer's output is sharded
  across N cores, the consumer needs the full vector). This is the **hard**
  boundary (§7): it requires a NOC collective (all-gather, broadcast,
  reduce-scatter) with tier-2 sync, and marks a `HARD` fusion boundary.

**The simplification before fusion:** the pattern-matched TTIR graph has long
elementwise chains (`CAST → MUL → ADD → CAST → MUL`). These are not separate
ops to fuse individually — they collapse into a single "SFPU epilogue with N
steps" description attached to the nearest matmul or reduce. The fusion pass
does not reason about individual elementwise ops; it reasons about "matmul +
epilogue(node list)." The codegen state machine (§9) handles each elementwise
step as a `(requires, body, effect)` within the matmul op's body, not as a
separate IR node.

**The fusion boundary ruleset** (elaborates §9.1):

| rule | tier | action |
|---|---|---|
| cross-core shard boundary (all-gather / reduce-scatter needed) | 3 | **HARD stop** — new Program |
| `StaticEnv` incompatible (CB layout, role topology, storage layout, NoC topology) | 3 | **HARD stop** — new Program |
| L1 budget exceeded (sum of fused CBs > 1.28 MiB) | 2→3 | **stop** — new Program |
| DST residency conflict (next op needs DST, current value must pack out, no epilogue left) | 1→2 | pack to CB, continue in same Program |
| `ConfigEnv` transition needed (e.g. fp32→bf16 dest, format switch) | — | `ConfigEnv.update()`, continue in same Program |
| SFPU epilogue on DST-resident value | 1 | **fuse** — free, no boundary |
| elementwise chain on DST-resident value | 1 | **fuse** — collapse to epilogue |

The first two rules are hard boundaries (always a new Program). The third is a
capacity limit. Everything else fuses within a Program via the codegen state
machine.

**What's genuinely different from a GPU:**

| | GPU | Tenstorrent |
|---|---|---|
| fusion unit | one kernel launch | one Program (5 coordinated RISC-V kernels) |
| data stays in | registers + shared memory | DST (8 KiB) + L1 CBs (1.28 MiB) |
| two matmuls in one unit | no (different grid/launch) | yes (on-device loop, CB in L1) |
| elementwise epilogue | fuses if register pressure allows | fuses free if value in DST |
| fusion limit | register pressure (small, scalar) | cross-core shard boundary (binary) + L1 capacity |
| cross-SM boundary | global memory (cheap) | NOC + L1 mailbox (expensive, needs sync) |

The key insight: **on a GPU, the fusion limit is register pressure (small and
continuous). On Tenstorrent, the fusion limit is cross-core communication
(binary — either you're on the same core or you're not) plus L1 capacity
(generous for BS=1).** For decode BS=1 where the input vector is broadcast to
all cores, every core can do its own RMSNorm/rope/SiLU locally (per-core-
redundant, no cross-core traffic), so fusion is maximized. For prefill S>1 or
any cross-core reduction, fusion breaks at the shard boundary.

**Llama decode — the 5-programs-per-layer boundary:**

The 5-programs-per-layer target (LLAMA_PORT_PLAN.md §4) is driven by exactly
one rule: each GEMV shards its N output across cores; the next stage needs the
full vector as a broadcast in0 → shard→broadcast (all-gather) = Program
boundary. The intermediates are 4 KiB (fit in L1 trivially), DST residency is
fine (M=1, tiny output), SFPU epilogues are free (Tier 1). The ONLY thing
breaking fusion is the cross-core shard boundary (Tier 3).

## 9. Codegen is a STATE MACHINE, not template concatenation

Tensix is a **stateful datapath**: config registers (unpack format + tile
descriptor, math ADDR_MODs + dest format, pack format + dest offset, loaded MOP
templates, SFPU state) must hold specific values before each op. A GPU ISA hides
this — arbitrary ops concatenate and it just works. Tensix does not: chaining op
A → op B without re-establishing B's required config silently corrupts data or
hangs. **So fusion cannot be template concatenation — you must emit the config
transition between ops** (this is what "reconfigure the pipeline after mean"
is: mean leaves one config, the next op needs another, and something must emit
the delta). A frozen template bakes in the state its neighbors happened to leave,
so templates alone do not compose.

Codegen tracks **three resource-states** and emits a transition whenever
composition changes one:

1. **Datapath config** — a `ConfigEnv` of the slots that matter. Each op declares
   `requires` (preconditions) and `effect` (postconditions). Before an op, diff
   `current_env` vs `op.requires`, emit the minimal reconfig, then
   `current_env = op.effect(current_env)`. This auto-inserts the reconfig after
   mean/reduce. An op's `out_dtype` drives its `effect`: `out_dtype=fp32` on a
   reduce/matmul flips `fp32_dest_acc` (ALU enable bits + dstacc nibble + ZEROACC
   flag + packer 32b read + subblock clamp to 4 + cb24 reload ping) as a single
   atomic effect — so the knob-consistency checker (KERNEL_GUIDE §8.3) is
   redundant: the chain is established by construction, not checked after.
2. **Tile registers** (DST / SrcA / SrcB) — the DST-residency allocator (§5/§6).
3. **Scalar GPRs** — virtual registers + liveness allocation, replacing ttk's
   hardcoded `t0`/`t1`. Clobbering becomes impossible by construction (ttk is
   fickle precisely because composed snippets collide on fixed registers).

### 9.1 StaticEnv vs ConfigEnv vs resource state

Do not put every piece of kernel state into `ConfigEnv`; split it by lifetime.

**`StaticEnv`** is fixed for the whole emitted Program. It is configured before
the fused kernel's main loop starts and is a hard fusion boundary if two TTIR
regions need incompatible values:

- CB table: page size, depth, L1 base, local/remote interface offsets.
- Program layout: RTA locations, semaphore offsets, L1 scratch allocations,
  kernel-config base, role enable mask.
- Tensor/storage layout: dtype, tile bytes, logical shape, tile grid, shard,
  DRAM bank/interleave policy.
- NoC defaults that are not intended to change in the kernel: local coordinates,
  command-buffer assignment, default VC/path policy, bank-coordinate tables.

**`ConfigEnv`** is persistent hardware interpretation state. It survives past one
TTIR op and affects how the next op is decoded/executed. Each role has its own
`ConfigEnv`; `config.update(want)` mutates the compiler's known environment and
emits the RISC-V/Tensix instructions needed at that point in that role program.
In v0 it may conservatively restore a canonical state and then establish `want`;
in v1 it diffs `current` against `want` and emits only the delta.

The fields we currently know belong in `ConfigEnv`:

- **Unpack state:** tile descriptor/input dtype, unpack output format,
  compressed/uncompressed bit, tile dims, base/dest contexts, unpack address
  controls, `UNPACK_MISC_CFG_CfgContext`, `SRCA_SET`/`SRCB_SET`, z-stride.
- **Math/FPU state:** `ADDR_MOD_AB*`, `ADDR_MOD_DST*`, bias addrmods, fidelity,
  ALU format/accumulation bits, fp32-dest enable, zero-flag behavior,
  `DEST_ACCESS_CFG`, current matmul/copy/reduce MOP and replay payload.
- **Pack state:** pack input/output dtype, `PCK_DEST_RD_CTRL` read width,
  pack strides, pack counters/edge/mapping/concat config, zero-compress bits,
  L1-acc bits, current output CB/tile header, pack MOP.
- **SFPU state:** program constants (`PRGM0..2`), `SFPU_CTRL`, condition-code /
  predicate mode, `SFPU_DEST_FMT`, and any assumed LReg convention for a composed
  SFPU snippet.
- **Thread-cfg / counter state used across templates:** `CFG_STATE_ID`,
  RWC/ADC state if a following template assumes it. v0 should reset RWC/ADC at
  op boundaries so they do not become semantic preconditions; if a mined
  template relies on inherited RWC/ADC position, promote that field into
  `ConfigEnv`.
- **TLM/mailbox shadow state that templates consult:** unpack/pack src/dst
  format bytes, face dims, num faces, `dest_offset_id`, local cfg-context state.

**Resource state** is tracked by the scheduler/emitter, not by `ConfigEnv`:
DST allocation/liveness, SrcA/SrcB validity, GPR allocation/liveness, CB runtime
counters, semaphore balances, NoC outstanding transaction IDs/barriers, loop
induction variables, and temporary mailbox values. These are still critical
correctness state, but they are part of sync/resource allocation rather than
persistent datapath configuration.

Fusion rules at the tinygrad/TTIR boundary:

- Stop at hard shard/core collective boundaries.
- Stop when `StaticEnv` requirements differ (CB layout, role topology, storage
  layout, or NoC topology).
- Stop when DST residency cannot hold the live tile set or fp32-dest halves make
  the required subblock illegal.
- Stop when the value must be packed/unpacked anyway and no useful epilogue or
  prologue remains on-chip.
- Otherwise fuse, and let `ConfigEnv.update()` insert the mid-kernel reconfig
  transitions.

`examples/matmul_peak.py` is the first rewrite target and the best specimen for
mining this model. Its static role init maps to `StaticEnv` plus canonical
startup config:

- `trisc0`: `unpack.init(dtype=INPUT_DTYPE, ..., mop_cfg=MATMUL_UNPACK_AB_MOP_CFG)`.
- `trisc1`: `matmul_math_init()` and the matmul addrmods/replay payload.
- `trisc2`: `pack.init(dtype=OUTPUT_DTYPE, out_cb=16, mop_cfg=MATMUL_PACK_MOP_CFG)`.

The mid-kernel reconfig sites become explicit `ConfigEnv.update()` calls:

```python
env.trisc0.update(UnpackMode(dtype=intermediate, mop=reload_to_dest, z_stride=fp32))
emit_reload_body()
env.trisc0.update(UnpackMode(dtype=input, mop=matmul_ab, z_stride=fp16))

env.trisc1.update(MathMode(kind="reload"))
emit_reload_math()
env.trisc1.update(MathMode(kind="matmul", addrmods=matmul_hifi2, mop=matmul_mop))

env.trisc2.update(PackMode(dtype=intermediate, out_cb=24, l1_acc=True))
emit_partial_pack()
env.trisc2.update(PackMode(dtype=output, out_cb=16, l1_acc=False))
emit_final_pack()
```

Those correspond to the existing hand-coded switch points: unpack format/MOP
switch for cb24 reload, math copy-to-DST reload then matmul restore, pack format
switch from intermediate cb24 partials to final cb16 output, and pack L1-acc /
zero-flag toggling for partial blocks. Mining should factor each of these into
`(requires, body, effect)` rather than stamping the whole `matmul_peak` kernel.

**Mining, revised.** Don't stamp whole templates. `kir.lift()` a working kernel
and factor each op into a signature `(requires, body, effect)` over `ConfigEnv`,
with its GPRs renamed to virtual. `body` is the parameterized instruction core;
`requires`/`effect` are the config deltas around it. Ground truth still comes
from real kernels (incl. the Layer-B stall dance, §6), but it now composes.

**Staging — correct first, fast later:**
- **v0, canonical resting state.** Every op restores config + DST + GPRs to a
  canonical state on exit; any two ops then concatenate safely. Always correct;
  redundant reconfig overhead. This alone delivers fuse-on-demand.
- **v1, state diffing.** Track `ConfigEnv`, elide already-satisfied reconfig; the
  cost of a mandatory transition feeds the fusion cost model (expensive forced
  reconfig ⇒ argument for a kernel boundary — a soft boundary, §6/§7).

The guarantee: the emitter refuses to emit an op whose preconditions aren't met
— it establishes them first — so you cannot chain two ops into a corrupt state.
That is the "you can't crash a GPU" property, rebuilt by construction.

## 10. Sub-tiles — the one place below a tile

Two distinct cases, often conflated:

- **`reduce_intile` (§3) — tile-aligned intra-tile reduction.** Reducing a
  32×32 tile along one axis (e.g. sum each row → 1×32, or column-max → 32×1).
  This is the normal reduce-LLK path: no predicate, no sub-tile mask. A
  width-2048 RMSNorm mean (64 tiles, each reduced along its 32-wide axis) is
  pure `reduce_intile` — no `SubTileMask` involved.
- **`SubTileMask` — true partial-tile slice.** Needed only when a
  `SHRINK`/slice has bounds **NOT multiples of 32**, e.g. `x[45:55].sum()`
  over a 1024-lane tile. Lowering: SFPU predicate (`SETCC` over lane index) + a
  loop summing only selected lanes into DST. **Trigger from tinygrad:** a slice
  whose bounds are not tile-aligned → emit a `SubTileMask` op carrying the lane
  predicate. Tile-aligned slices stay pure tile ops.

Isolate the partial-slice leak in `SubTileMask` alone; `reduce_intile` is a
first-class tile op with no sub-tile machinery.

## 11. Migration from kir

| kir today | fate under TTIR |
|---|---|
| `kir/ir.py` `Node`/`KernelIR`/`lift()` (instruction nodes, CFG) | **KEEP** — it's the template-mining tool (§9) and the substrate for the clobber checker. |
| `kir/sem.py`, `kir/synccheck.py` (semaphore-balance checker) | **SUBSUME** — TTIR *constructs* balanced Layer-A sync, so the deadlock class is prevented by construction, not checked after. Keep as an optional post-lowering assertion. |
| `kir/regcheck.py` (register-clobber checker) | **PREVENT, don't check** — the GPR virtual-register allocator (§9) makes clobbering impossible in generated code. Keep the checker only for ingested / hand-written code. |
| deleted `kir/IR_DESIGN.md` (imperative `prog.unpack/pack` sketch) | **SUPERSEDED** by this doc; keep only as historical context in git history. |
| Task #4 knob-consistency checker | **REDUNDANT** — `out_dtype` on reduce/matmul drives the fp32_dest effect chain in the codegen state machine (§9); subblock is derived from `out_dtype` (§5). The checker has nothing to verify that isn't already enforced by `ConfigEnv` effect declarations. |

Net: TTIR replaces what kir's *checkers* were guarding against by making those
states unrepresentable. **Register clobbering** and the **ttk hand-built-RISC-V
fragility** are both resolved by the codegen state machine (§9): the GPR
allocator prevents clobbers, and the `ConfigEnv` `(requires, body, effect)` model
lets ops compose without hardcoded state — so fusion is safe by construction.

## 12. Worked examples

Elementwise multiply (streams, the whole kernel):
```python
def elwmul(a, b, out):           # a, b, out: Tensor (tiled, bf16)
    out <<= stream(a) * stream(b)
    # lowering: brisc loads a,b -> CB0,CB1; trisc0 unpack -> SrcA,SrcB;
    #           trisc1 FPU mul -> DST; trisc2 pack -> CB16; ncrisc store -> out.
    #           Layer-A tile-count sync on every edge; Layer-B in templates.
```

Matmul block (indexed tiles, DST accumulation, subblock = DST tiling):
```python
def matmul_block(A, B, C, Kt):           # A[Mt,Kt] bf16, B[Kt,Nt] bf16, C[Mt,Nt] fp32
    for i in range(A.tile_grid_M):        # subblock sized to DST-half (4 tiles, fp32 acc)
        for j in range(B.tile_grid_N):
            acc = matmul(A[i, 0], B[0, j], out_dtype=fp32)  # zero-init + first MAC
            for k in range(1, Kt):        # K-accumulation, stays in DST
                acc = matmul(A[i, k], B[k, j], acc=acc)
            C[i, j] = acc                 # pack once, when the chain leaves DST
```
The subblock (4 tiles/half here) is derived from `out_dtype=fp32`, not chosen.
The fusion rule is visible: `acc` lives in DST across the whole k-loop; a
pointwise epilogue on `acc` fuses (still in DST); the pack is the boundary
where the value must leave DST.
