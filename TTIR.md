# TTIR — Tenstorrent tile IR for blackhole-py

**Status:** written spec / design prototype. Implementation lands later.
No tt-metal, no tt-lang, no C++. tinygrad frontend → TTIR → RISC-V on cores.
blackhole-py already launches/runs hand kernels with zero TT software.

Design axioms: **the atom is a 32×32 tile; every author op is tile→tile;
CBs are tile queues (`Stream`s); non-queue sync is `Wait`; codegen is a
state machine over composable op templates; maximize fusion into one Program
(where the chip shines); one deterministic lowering per op (no search).**

```
tinygrad Tensor graph
   │  intercept pre-schedule UOp DAG (intent intact: REDUCE, matmul, softmax)
   ▼
TTIR  — tile-native SSA over tiles + streams
   │  schedule → engine-assign → sync-insert → emit
   ▼
5 coordinated RISC-V programs (brisc/ncrisc/trisc0/1/2) → Tensix words → CQ → device
```

---

## 0. Scope

| in scope | out of scope (for now) |
|---|---|
| Single-device Blackhole, core-local SPMD | Multi-card / distributed (tinygrad later) |
| Tile SSA + Stream queues + deterministic lowering | BEAM / autotune / search |
| Max fusion into one Program (DST + L1 CBs) | Multi-tenant scheduling |
| PatternMatcher intercept into tinygrad | Tensor-API subclassing / fork |

Spec first. Runtime stack (`program`, `cq`, `device`, `ttk`, hand kernels under
`examples/`) already exists. This doc is the compiler IR they lower toward.

---

## 1. Values: three types, one atom

- **`Tile`** — one 32×32 tile; an **SSA value** with a `dtype`. Single-assignment,
  immutable. The author never says *where* it lives; whether a `Tile` is a CB
  slot, SrcA, SrcB, or a DST register is decided by lowering.
- **`Tensor`** — a named DRAM/L1 buffer = a **grid of tiles** with metadata (§2).
  Storage only; you stream it or index it into `Tile`s.
- **`Stream`** — an ordered **queue of tiles**. Maps onto a hardware circular
  buffer (CB). `stream(tensor)` dequeues tiles out; `out << tile` enqueues.
  Streams are **sugar** over indexed-tile loops (§5). **FIFO tile dataflow is
  expressed entirely as produce/consume on Streams — never as `Wait`.**

---

## 2. Tensor metadata

```python
@dataclass(frozen=True)
class DType:
    name: str          # "bf16" | "fp32" | "fp16" | "bfp8" ...
    tile_bytes: int    # bf16/fp16=2048, fp32=4096, bfp8~1088

@dataclass(frozen=True)
class Layout:
    kind: str          # "tiled" (32x32, face-swizzled) | "row_major"

@dataclass
class Tensor:
    name: str
    dtype: DType
    shape: tuple[int, ...]     # LOGICAL dims — kept for untilize + pad masks
    layout: Layout             # declarative TYPE; coercion at mismatched edges (§4)
    where: str = "dram"        # "dram" | "l1"
    addr: int | None = None    # base (allocator-filled)
    banks: int = 8             # dram bank interleave
    # later: shard  — core distribution; out of scope until multi-core collectives
    # derived: padded_shape, tile_grid, num_tiles, page_bytes = dtype.tile_bytes
```

| field | drives |
|---|---|
| `dtype.tile_bytes` | CB page size, DST capacity, unpack/pack format |
| `shape` (original) | untilize crop + padding masks |
| `layout.kind` | whether an edge needs `tilize`/`untilize` (§4) |
| `addr`/`banks` | brisc/ncrisc NOC addressing — generated plumbing |

CB depth = N tiles; page = 1 tile = `dtype.tile_bytes`.

---

## 3. Node taxonomy

### a) Compute (tile → tile) — authors write these

```
mul add sub max  exp2 log2 recip sqrt gelu silu ...   # SFPU/FPU
matmul(a, b, *, out_dtype) -> Tile                    # tile·tile MAC into DST
reduce_across(op, stream, *, out_dtype) -> Tile       # fold tiles (DST acc)
reduce_intile(op, tile, axis, *, out_dtype) -> Tile   # within-tile reduce-LLK
mask(tile, lane_pred) / masked reduce                 # sub-tile escape (§10)
```

`out_dtype` on reduce/matmul is the **accumulation dtype**. There is no separate
accumulator concept — same as tinygrad: matmul is
`REDUCE(ADD, dtype=float, MUL(EXPAND, EXPAND))`; the REDUCE node's dtype *is*
the accumulation dtype.

| `out_dtype` | effect (atomic ConfigEnv chain, §9) |
|---|---|
| `fp32` | fp32_dest_acc on; DST half ≤4 tiles; cb24 reload path; ZEROACC; packer 32b |
| `bf16` / narrower | all of that off; DST half ≤8 tiles |

Authors never flip knobs; the effect is derived from `out_dtype`.

### b) Movement (tiles change location)

```
load(tensor) -> Stream          # brisc / NOC0
store(stream, tensor)           # ncrisc / NOC1
# later: gather / broadcast / all_reduce  across cores
```

Bodies are **parameterized templates** keyed by `(layout, banks, out_dtype)`,
sourced from known-good hand kernels (`examples/matmul_peak.py`, `add1.py`,
`llama3/*`). Defaults for mcast rect, linked-VC, path-reserve, overlay vs
command-buffer are **baked into templates**, not IR knobs.

### c) Coercion (tiles change type) — inserted by type pass (§4)

```
cast(tile, dtype) -> Tile
tilize(tile) / untilize(tile)
```

### d) Non-queue sync — inserted by sync-insert, never authored as compute

See §6. `Wait` and `Cap` only — **not** CB tile flow.

---

## 4. Coercions are a type system

`Tensor` carries the declarative type (`dtype` + `layout`). A pass inserts
coercion nodes where edges mismatch: dtype → `cast`; layout → `tilize`/`untilize`.
Visible IR nodes (pretty-printer sees them), not hidden mutations.

Not free: SFPU cast, format-converting pack/unpack, or tilize-LLK. Lowering may
fold a coercion into the neighbor unpack/pack (format on the fly) → often zero
extra instructions. Represent first; fold as optimization.

---

## 5. Streams vs indexed tiles

`Stream` is sugar over an indexed-tile loop; the core is indexed tiles + loops.

- **Streams** — 1D pointwise: `out <<= stream(a) * stream(b)`. CB = FIFO; loop is
  “for each tile”; no addressing.
- **Indexed tiles** — matmul/attention: `C[i,j] = Σ_k A[i,k]·B[k,j]` needs 2D
  tile indices + k-accumulation. Subblock tiling is chosen to **fit DST**.

Rule: streams for pointwise; indices for reductions / 2D structure.
**DST allocation lives in the indexed layer** (subblock loop = DST-half tiling).

**Subblock size is derived, not chosen:**

```
subblock = min(output_tiles, dst_half_capacity)
dst_half_capacity(fp32) = 4
dst_half_capacity(bf16) = 8
```

Lowerer computes this from the reduce/matmul `out_dtype` and uses it as MOP loop
counts. Author never specifies it.

Streams, at the hardware level:

```
produce:  cb_reserve_back(cb, N) → fill → cb_push_back(cb, N)
consume:  cb_wait_front(cb, N)  → use  → cb_pop_front(cb, N)
```

N is always a tile count (1, subblock, or K-block) — never fractional.
Which engine owns which half, and whether pop uses deferred Tensix ack
(`TTSTOREREG`, trisc0) vs eager RISC store (brisc/ncrisc), is **role assignment
in emission**, not an author-visible node.

---

## 6. Sync model (CBs are queues; Wait is everything else)

### Two layers

**Layer A — dataflow / occupancy. TTIR inserts it; authors don’t write it.**

| mechanism | TTIR form | units | role |
|---|---|---|---|
| Circular buffer | **`Stream` produce/consume** (§1, §5) | tiles | ordered tile FIFO in L1 |
| Tensix semaphore | **`Cap` acquire/release** | events (usually 1 per subblock) | engine occupancy (double-buffer) |
| NOC readiness | **`Wait`** (and template-private arming) | free slots / receiver count / ready | multi-core handshakes inside a Program |

**Layer B — pipeline hazards. Templates only. Never TTIR nodes.**

`TTSTALLWAIT` on CFG/THCON/MATH/SFPU/PACK0, `tensix_sync`, `PC_UNPACK_SYNC`
spins, fences. Fixed per op body; fires within processing one tile/subblock.

### Why CBs are not `Wait`

A CB is an **ordered queue of tiles**. Produce/consume *is* the protocol.
Modeling it as generic `Wait(edge, n)` loses reserve/push · wait/pop pairing and
blithely mixes it with non-FIFO credits. **Stream ops are the CB IR.**

### Caps (Tensix semaphores)

Bounded engine credits, confirmed against `matmul_peak` / `add1` / `rmsnorm`:

```
UNPACK_SYNC     max=2
MATH_PACK       max=2   # room side → math; data side → pack
UNPACK_TO_DEST  (as needed)
```

```
Cap(name, max)
  Acquire(cap, n=1)   # SEMWAIT-style, room or data end
  Release(cap, n=1)   # SEMPOST / SEMGET as emission chooses
```

`MATH_PACK` is **DST-stage occupancy**, not a tile payload. Cap is the right
abstraction: bounded capacity shared across trisc1 and trisc2.

### `Wait` — non-queue synchronizers only

```
Wait(kind, count, ...)
  kind ∈ { noc_free, noc_data_ready, init_barrier, ... }
```

Examples from multi-core matmul (same Program):

- receivers reserve CB and notify sender → sender **`Wait(noc_free, n_receivers)`**
- sender mcasts tiles then signals → receivers **`Wait(noc_data_ready, 1)`**

`count` may be **receiver heads**, not tiles. Tile payload still moves through
Streams/CBs on each core; the NOC protocol only ships readiness.

Init/`RiscSync` barriers between BRISC and TRISCs may lower to a trivial
`Wait(init_barrier)` or stay as fixed template prologue — either is fine as long
as author compute never sees it.

### What sync-insert does

Given tile dataflow edges after schedule + engine-assign:

1. Every Stream producer/consumer edge → CB allocate (depth) + insert
   reserve/push on producer role, wait_front/pop on consumer role.
2. DST double-buffer between math and pack → Cap(`MATH_PACK`) acquire/release
   around those stages.
3. Multi-core movement templates *may* emit `Wait` nodes for NOC readiness
   (or fold them entirely into the load/store mcast template bodies — v0 can
   keep them template-private).

Layer-A deadlock classes (unbalanced CB or Cap) are **prevented by construction**:
sync-insert only emits balanced pairs. Optional post-lowering assertion later.

---

## 7. Cores and programs (single-device, SPMD)

A **Program** is one per-core tile program, replicated across a set of live
Tensix cores. Each core may run different RTAs (sender vs receiver roles,
inequality of local tile offsets) under the same template.

**Inter-core collectives** (all-gather / reduce-scatter / broadcast as first-class
TTIR ops) and **shard metadata as HARD fusion boundaries** are intentional later
work. Until then:

- Multi-core *inside* one matmul Program (row/col mcast of A/B tiles) lives in
  the matmul/load/store **templates**, not as author-level collective ops.
- Max fusion is pursued core-locally: keep work on-core via DST + L1 Streams.

Multi-card stays entirely outside this stack (tinygrad).

---

## 8. Lowering → five straight lines

Four passes:

1. **Schedule** — tile-DAG → order of tile-ops, constrained by DST residency.
   Fusion decisions live here.
2. **Engine-assign** — fixed routing: load→brisc, store→ncrisc, unpack→trisc0,
   math/SFPU→trisc1, pack→trisc2.
3. **Sync-insert** — Stream/Cap (and Wait if not template-folded). Layer B stays
   inside templates.
4. **Emit** — each engine’s ordered ops → straight-line RISC-V (loops allowed).

Output: **five coordinated programs**, one Device launch.

Fixed pipeline:

```
brisc (reader) → trisc0 (unpack) → trisc1 (math/SFPU) → trisc2 (pack) → ncrisc (writer)
```

A Program can cycle this pipeline many times (on-device loops) = multiple DST
residency windows inside one launch.

### 8.1 Fusion tiers — maximize one Program

On a GPU, fusion ≈ one kernel, limited by register pressure. On Tensix, fusion =
**one Program**, data lives in **DST (~8 KiB) and/or L1 CB queues (~1.28 MiB)**.
Multiple matmuls *can* share a Program via L1 Streams; SFPU epilogues ride free
on DST between them. **That is the point of this IR.**

**Tier 1 — DST-resident (free, unlimited op count).**
SFPU on a value currently in DST. No L1 round-trip, no Stream, no Cap.
`silu(gate)*up`, `x*cos + rot*sin`, residual add, cast, recip, scale, … Chain
while the value stays in DST. Boundary only when DST must free for the next
matmul (pack → Stream).

**Tier 2 — L1-resident (cheap, L1-bounded).**
Matmul packs to Stream; next matmul consumes it. New DST window, data never
leaves L1:

```
sum(CB bytes for fused stages) ≤ ~1.28 MiB L1 data budget
```

Decode BS=1 intermediates are tiny (~4 KiB for a 2048 bf16 vector) → many
stages in one Program is normal.

**Tier 3 — DRAM (or future cross-core collective).**
Must leave the core’s L1. L1 budget blow-up, or (later) a real shard collective.
**Hard Program boundary.**

Elementwise chains from the intercept collapse before fusion reasoning:
`CAST→MUL→ADD→…` → one **epilogue list** on the nearest matmul/reduce. Fusion
thinks in “matmul + epilogue”, not individual elw ops. Codegen walks each
epilogue step as `(requires, body, effect)` (§9).

| rule | action |
|---|---|
| L1 budget exceeded | new Program |
| next op needs DST; live value has no residual epilogue | pack → Stream; stay in Program |
| `StaticEnv` incompatible (CB table, role topology, storage, NoC topology) | new Program |
| `ConfigEnv` transition only | `ConfigEnv.update()`; stay in Program |
| SFPU / elw on DST | fuse free |
| future: cross-core collective edge | HARD new Program |

| | GPU | Tensix |
|---|---|---|
| fusion unit | one kernel launch | one Program (5 RISC-V roles) |
| resides in | regs + smem | DST + L1 Streams |
| two matmuls same unit | no | yes (loop + Stream) |
| elw epilogue | register pressure | free if in DST |
| limit | continuous reg pressure | L1 capacity (+ later collectives) |

---

## 9. Codegen is a STATE MACHINE, not template concatenation

Tensix is a **stateful datapath**. Unpack format, math ADDR_MODs, dest format,
pack format, loaded MOPs, SFPU state must hold specific values before each op.
Concatenating frozen templates silently corrupts or hangs. Fusion must emit
**config transitions**.

Each op-template is a triple over `ConfigEnv`:

```
(requires, body, effect)
```

- `body` — parameterized instruction core (incl. Layer-B stalls).
- `requires` — ConfigEnv pretences that must hold before `body`.
- `effect` — ConfigEnv postconditions after `body`.

Before emit: diff `current` vs `requires`, emit reconfig (or full restore in v0),
run `body`, `current = effect(current)`.

Three tracked states:

1. **`ConfigEnv`** — persistent datapath interpretation (per role).
2. **Tile registers** — DST / SrcA / SrcB residency / liveness.
3. **Scalar GPRs** — virtual regs + liveness (no hardcoded `t0` collisions).

### 9.1 StaticEnv vs ConfigEnv vs resource state

**`StaticEnv`** — fixed for the whole Program; incompatible values = hard fusion
boundary:

- CB table (page size, depth, L1 base, interface offsets)
- Program layout (RTA, sem offsets, L1 scratch, enable mask)
- Tensor/storage layout (dtype, tile bytes, shape, banks)
- NoC defaults (coords_cb assignment, VC/path policy, bank tables)

**`ConfigEnv`** — survives across ops; per-role; `config.update(want)` emits the
instructions to establish `want`:

- Untpack: tile descriptor, input/output format, contexts, SRCA/B set, z-stride, …
- Math: ADDR_MODs, fidelity, ALU / fp32-dest, ZEROACC, MOP + replay payload, …
- Pack: in/out dtype, PCK_DEST_RD_CTRL, strides, L1-acc, out CB, pack MOP, …
- SFPU: PRGM consts, SFPU_CTRL, predicate mode, DEST_FMT, LReg convention, …
- Thread/RWC/ADC if a following template assumes them (v0: reset at op
  boundaries so they stay non-preconditions)
- TLM/mailbox format shadows templates consult

**Resource state** (scheduler/emitter, not ConfigEnv): DST liveness, SrcA/B
validity, GPR liveness, CB queue counters, Cap balances, NOC outstanding IDs,
loop IVs, temp mailboxes.

### Staging

- **v0** — every op restores canonical ConfigEnv + DST + GPRs on exit → any two
  ops concatenate safely; redundant reconfig; fuse-on-demand works.
- **v1** — diff and elide; expensive forced reconfigs feed soft fusion costs.

Emitter refuses to emit `body` until `requires` is established.

### Template ground truth

`examples/matmul_peak.py` is the primary specimen. Static inits map to
StaticEnv + startup ConfigEnv; mid-kernel reconfigs (cb24 fp32 reload, pack
L1-acc toggle, format switches) are explicit `ConfigEnv.update()` sites.

Op bodies are **hand-specified in the implementation from that kernel** (and
`add1`, `llama3/*`). Automated instruction mining is optional RE sugar, not a
spec dependency: tile/Stream author programs are correct by construction once
templates and sync-insert exist; templates themselves are the RE product.

Sketch of mid-kernel reconfig (conceptual):

```python
env.trisc0.update(UnpackMode(dtype=intermediate, mop=reload_to_dest, z_stride=fp32))
emit_reload_body()
env.trisc0.update(UnpackMode(dtype=input, mop=matmul_ab, z_stride=fp16))

env.trisc1.update(MathMode(kind="reload")); emit_reload_math()
env.trisc1.update(MathMode(kind="matmul", addrmods=matmul_hifi2, mop=matmul_mop))

env.trisc2.update(PackMode(dtype=intermediate, out_cb=24, l1_acc=True)); emit_partial_pack()
env.trisc2.update(PackMode(dtype=output, out_cb=16, l1_acc=False)); emit_final_pack()
```

---

## 10. Sub-tiles — the one place below a tile

- **`reduce_intile`** — tile-aligned axis reduce (e.g. row-sum 32×32 → 1×32).
  Reduce-LLK; no predicate. RMSNorm mean over width-aligned tiles is pure this.
- **`SubTileMask`** — true partial-tile slice when SHRINK bounds are **not**
  multiples of 32. Lowering: SFPU `SETCC` over lane index + selective accumulate.
  Trigger: non-aligned slice from tinygrad. Isolate the leak here; nothing else
  goes sub-tile.

---

## 11. tinygrad intercept

### Why not the renderer / post-rangeify path

Post-`run_rangeify`, kernels are flat `STORE(INDEX(PARAM, RANGE))` — GPU address
math, no matmul, no axis-reduce, no softmax. A renderer→TT lowerer cannot recover
tile intent. Intercept **before** `transform_to_call` / rangeify, on the finished
lazy UOp DAG (`x.uop` at realize/schedule time).

Recoverable at that altitude:

- matmul: `REDUCE(ADD, axis) ← MUL(EXPAND, EXPAND)` + `out_dtype = reduce.dtype`
- softmax: `REDUCE(MAX) → SUB → EXP2 → REDUCE(ADD) → RECIP → MUL`
- RMSNorm: square → mean → eps → rsqrt → scale → weight

tinygrad’s UOp path churns across versions — accepted; match **structurally
stable** subgraphs (`REDUCE(ADD)←MUL(EXPAND,EXPAND)` is how matmul is defined).

### tinygrad pipeline (reference)

```
Tensor API (lazy UOp DAG)
   │  *** INTERCEPT HERE: finished DAG ***
   ▼
1. transform_to_call
2. create_schedule
3. run_rangeify          ← tile intent dies after this
4. full_rewrite_to_sink  (incl. BEAM — unused by us)
5. to_program
6. run_linear
```

tinygrad has two optimization mechanisms: **`PatternMatcher` graph rewrites**
(we use this) and **BEAM** (per-kernel loop search — irrelevant; TT is
non-tunable).

### TT PatternMatcher

A `PatternMatcher` on the pre-schedule DAG, registered as a `graph_rewrite`
before `transform_to_call`. Uses tinygrad’s own `UPat`/`graph_rewrite` APIs —
upstream-clean, no fork.

Decode 2-layer UOp scale (historical dump): ~1983 nodes, only ~39 REDUCEs; rest
movement + elw. Target after match: ~80–100 TTIR nodes.

```python
# 1. MATMUL — ~15-20 nodes → 1 TTIR matmul(out_dtype=reduce.dtype)
# 2. RMSNORM — full chain → 1 rmsnorm (or reduce_intile + epilogue list)
# 3. SOFTMAX — max/exp2/sum chain → 1 softmax
# 4. SiLU — mul(x, sigmoid(x)) → 1 silu (or pure elw epilogue)
# 5. Movement collapse — reshape chains cleaned before patterns 1-4
# 6. RoPE — cos/sin/rotate → 1 rope
```

Remaining elw fuses as prologues/epilogues in the **schedule** pass (§8), not the
matcher. How many Programs/layer is a **fusion** decision, not a pattern count.

**Do not:**

- Subclass `Tensor` / override methods (would never upstream).
- Run BEAM on TT kernels.
- Fork tinygrad.

Upstreaming = one PatternMatcher + hook before `transform_to_call`, plus a Device
that consumes TTIR Programs.

### Reference dumps (restore when implementing)

```
tools/tg_dumps/DECODE_A_preschedule.txt   # UOp DAG at intercept
tools/tg_dumps/DECODE_annotated.txt       # histogram + REDUCE listing
tools/tg_decode_dump.py                   # harness
```

---

## 12. Relation to existing codebase

What already runs:

| layer | files |
|---|---|
| Launch / CQ / Program | `program.py`, `cq.py`, `device.py`, `pcie.py` |
| Assembler / Tensix ISA | `asm.py`, `dsl.py` |
| Role helpers | `ttk/` (cb, noc, pack, unpack, math, sfpu, tensix, …) |
| Firmware stubs | `fw/` |
| Working hand kernels | `examples/matmul_peak.py`, `add1.py`, `llama3/*` |
| Sim | `ttsim/` |

What this graph / this IR replaces at the *semantic* level (not necessarily as
packages today): hand-built kernels as the sole programming model; ad-hoc
knob-consistency reasoning; fixed-GPR composition that collides under fusion.

Checkers (sem balance, reg clobber) become mostly **prevention-by-construction**
once Stream/Cap sync-insert and virtual GPRs exist; keep post-hoc checks only for
hand-ingested asm if needed.

---

## 13. Worked examples

### Elementwise multiply (streams)

```python
def elwmul(a, b, out):           # Tensor tiled bf16
    out <<= stream(a) * stream(b)
    # Streams → CBs. Cap(MATH_PACK) between math and pack.
    # brisc load a,b → CB0,CB1; trisc0 unpack; trisc1 FPU mul → DST;
    # trisc2 pack → CB16; ncrisc store. Layer-B stalls inside templates.
```

### Matmul block (indexed, DST acc, subblock = DST tiling)

```python
def matmul_block(A, B, C, Kt):   # A,B bf16; C fp32
    for i in range(A.tile_grid_M):
        for j in range(B.tile_grid_N):
            acc = matmul(A[i, 0], B[0, j], out_dtype=fp32)
            for k in range(1, Kt):
                acc = matmul(A[i, k], B[k, j], acc=acc)  # stays in DST
            C[i, j] = acc                                  # pack = leave DST
```

Subblock (4 tiles/half for fp32) is derived. Epilogue on `acc` before pack fuses
free (Tier 1). Pack is DST boundary, not necessarily a Program boundary (Tier 2
can unpack again from L1 Stream).

### Author surface vs inserted sync

Authors write Tiles, Streams, compute, load/store.
Lowerer inserts Stream enqueue/dequeue on edges, Caps for stage occupancy,
and (if not folded) Waits for NOC readiness. Authors never write `Wait` or Cap.

---

## 14. Design decisions locked

1. **Atom = 32×32 tile.** No scalar programming model.
2. **CBs = Streams = queues of tiles.** Produce/consume, not Wait.
3. **`Wait` = non-queue sync** (NOC ready, tensix Caps publicly, init). Caps may
   be written as Cap ops distinct from Wait — either spelling benefits from the
   “not a tile queue” rule.
4. **Layer B never in TTIR** — templates only.
5. **One deterministic lowering** per author op; no BEAM.
6. **Codegen = ConfigEnv state machine** with `(requires, body, effect)`.
7. **Subblock from `out_dtype`.** No author subblock knobs.
8. **Maximize fusion** (Tier 1+2 default). Program split on L1 overflow /
   StaticEnv clash / (later) collective edges only.
9. **Intercept pre-schedule UOps**; PatternMatcher; no Tensor fork.
10. **Single device** for this revision; multi-card is tinygrad’s problem later.
11. **Spec-first** — this document is the contract; code follows.

---

## 15. Implementation order (when coding starts)

Not part of the semantic contract; planning only:

1. Stream + Cap types; trivial elw Program (load → compute → store) with v0
   canonical ConfigEnv reset between roles — prove CB = queue model.
2. Matmul template factored from `matmul_peak` as `(requires, body, effect)`.
3. Intercept: one matmul PatternMatcher rule on a checked-in UOp dump.
4. Fusion: attach elw epilogue list to matmul; Tier-1 SFPU while in DST.
5. Multi-matmul via L1 Streams in one Program (Tier 2).
6. Collectives / shard HARD boundaries when multi-core author ops are needed.
