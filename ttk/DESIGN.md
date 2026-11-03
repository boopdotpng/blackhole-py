# ttk v2 — a complete Blackhole kernel frontend

Status: design draft, 2026-10-02. Nothing here is implemented yet. It keeps the
`UOp(op, src, arg, dtype, thread)` shape from `ttk/uop.py` and the
INDEX/AFTER/RANGE/END/SINK conventions. The frontend is the product; lowering
comes later, and §9 says what it is allowed to do.

The goal: any kernel a Blackhole Tensix grid can run can be written here. The
author chooses the engines, data flow, formats, fidelity, tiling, buffer depths,
core mapping and NoC topology. The backend does only five optimizations:
**RISC-V codegen, MOP expansion, replay, SFPLOADMACRO substitution and NoC
transaction batching**. Everything else in the backend is mechanical lowering,
not a choice.

---

## 1. Stop enumerating kernels. Enumerate edges.

There is no finite list of kernels to cover. There is a finite list of
**places data can live** and **engines that move it between them**:

```
            NOC_READ / NOC_WRITE / NOC_ATOMIC
 GLOBAL ───────────────────────────────────▶ L1 ◀────────▶ L1 of other cores
 (DRAM, host)                                │ ▲           (unicast / multicast)
                                     UNPACK  │ │ PACK
                              ┌──────────────┘ └────────────┐
                              ▼                             │
                    SRCA ─┐   SRCB ─┐                       │
                          ├── FPU ──┴──▶ DST ───────────────┘
                          ▲             │ ▲  ▲ (unpack-to-dest, Unp0 only)
                          └── FPU mov ──┘ │
                          (D2A/D2B/B2A)   │ LOAD / STORE
                                          ▼
                                   SFPU vector values (LRegs, 32 lanes)
 RISC-V scalar values (GPRs) ◀── LOAD/STORE of L1 words, PARAM, SPECIAL
```

One kernel is a composition of these edges. If the frontend has **one
primitive per edge**, and each primitive exposes **every mode its hardware unit
supports** as arguments, the frontend is complete by construction. That
replaces "did we think of every kernel?" with "did we cover every mode of
these units?", which is a finite checklist (§8).

Every kernel in the repo inventory is one of six compositions of these edges.
Use this taxonomy when planning a model; you don't need a list of kernels:

| Pattern | Edges used | Repo instances | Qwen-style additions |
|---|---|---|---|
| **Map** | read → unpack → (FPU elw \| mov) → SFPU → pack → write | SwiGLU, residual add, FP8 round, RoPE | sigmoid gates, softplus, conv1d (decode) |
| **Reduce** | Map plus a carry: Dst accumulate, SFPU vreg carry, L1 pack-accumulate, or a cross-core inbox | RMSNorm, row max/sum, argmax, attention merge | L2 norm, QK-norm, gated RMSNorm |
| **Contract** | read/multicast → unpack both operands → MVMUL/ELWMUL loop → pack(+acc) | matmul_peak, GEMV projections, QKᵀ, PV | — |
| **Scan** | Contract or Map inside a runtime RANGE, with state in Dst/vreg/L1 | online softmax, argmax running max | Gated DeltaNet state recurrence |
| **Move** | NoC only, addresses computed from scalars | embedding, KV append, compact→dense (no standalone tilize/untilize: §3.5) | conv state shift |
| **Collective** | NOC_WRITE to another core's inbox, NOC_ATOMIC, multicast | argmax final, token broadcast, split-KV merge, writer waves | — |

---

## 2. Program model

1. **SPMD over a grid.** `@kernel(grid=(gx, gy))`. Core coordinates are
   `SPECIAL` UOps (tinygrad's name). A predicate on them (`when(core.x == 0)`)
   is an `IF`. Since SPECIAL values are known per core, the backend may
   specialize one binary per role. That is a RISC-V optimization, not author
   work, so no role templates or `verify_roles` connection lists are needed: the
   grid trace *is* the composition.
2. **Sequential semantics per core.** The author writes one ordinary program.
   Its meaning is "run each op to completion, in program order." The backend
   splits it across BRISC/NCRISC/TRISC0/1/2 and must produce an execution
   indistinguishable from that order. Every RAW/WAR/WAW hazard, CB counter,
   semaphore, dvalid flip, STALLWAIT and Dst section handoff is **derived**,
   never authored. This keeps the good idea of current ttk and drops its
   handle-lifetime API.
3. **Concurrency comes from storage depth, and depth is the author's choice.**
   Storage with `depth=d` has `d` physical slots. Occupancy `i` lives in slot
   `i % d`. Threads can run up to `d` occupancies apart. `depth=1` serializes
   producer and consumer, and `depth=2` double-buffers. So pipelining is a
   visible data-flow decision, as you wanted, and the backend only implements
   it. Dst has no fixed "halves": each Dst DEFINE is its own row region with
   its own slots and its own handoff, so two Dst DEFINEs are two independent
   registers (one resident, one streaming; one fed by FPU, one by SFPU).
   tt-metal's SyncHalf is just the special case of one Dst DEFINE with
   `depth=2` and a slot of half of Dst (§9).
4. **Two kinds of data.** Tiles in L1, Src and Dst are **storage**: DEFINE +
   INDEX, written and read by engine effects. SFPU vectors and RISC-V scalars
   are **SSA values** (LOAD → ALU → STORE), exactly as in tinygrad. Carries across
   loop iterations use a REG DEFINE (current ttk lowering of `carry=`).
5. **Every effect returns the new version of its destination.** Reading a view
   pins the version produced by the latest earlier writer, which is the AFTER edge.
   In-place updates (pack-accumulate, SFPU store into Dst, resident state)
   create new versions of the same occupancy. Reads of stale versions are
   verifier errors, which catches the class of bug that hangs in raw RISC-V.

---

## 3. Storage (DEFINE)

`DEFINE` has `arg=(Storage,)` and, new, optional `src` for producer
coordinates (§3.4).

```python
@dataclass(frozen=True)
class Tile:              # the item geometry; element units, not bytes
  dtype: DType           # bf16 fp16 fp32 tf32 fp8e4m3 fp8e5m2 bfp8 bfp8a bfp4 bfp4a bfp2 int8 uint8 int16 int32 uint32
  rows: int = 32         # 1..32 ("tiny tiles": 1x32, 8x32, 16x32 for decode)
  cols: int = 32
  layout: str = 'faces'  # 'faces' (16x16 face-major), 'rows' (row-major), 'col0' (vector in column 0)

@dataclass(frozen=True)
class Storage:
  space: str             # GLOBAL L1 SRCA SRCB DST REG
  tile: Tile
  count: int = 1         # tiles per occupancy (one "item")
  depth: int = 1         # physical slots; SRCA/SRCB are always 2 (hardware banks)
  at: int | None = None  # optional pinned address/row (L1 byte addr, Dst row); else allocator
  alias: int | None = None  # identity of another DEFINE sharing memory (CB16/CB24 style)
  identity: int = 0
```

### 3.1 Spaces and what precision means in each

| Space | Unit of INDEX | Formats | Precision rule |
|---|---|---|---|
| GLOBAL | elements, row-major | any non-block L1 format | **one layout, never authored:** a row-major tensor, interleaved across banks with a page size of one tile (`32·32·itemsize` bytes, e.g. 2048 B bf16, 1024 B fp8, 4096 B fp32). No transposed, tiled, face-major or sharded GLOBAL layouts, ever: every tensor in DRAM or host memory is row-major, between kernels too. Tiled layouts exist only in L1/Src/Dst inside a kernel (§3.5). location = `dram` or `host` (PCIe) |
| L1 | bytes (tile helpers) | any | symmetric across cores: one DEFINE has the same address on every core, which makes remote INDEX and multicast well-defined |
| SRCA / SRCB | rows of 16 (64 rows/bank) | tf32 bf16 fp16 int8 int16 (19-bit cells) | conversion happens **at UNPACK**; only fp32 L1 may differ in→out |
| DST | rows of 16 | 16-bit (1024 rows) or 32-bit (512 rows) | DEFINE dtype selects the Dst mode; mixing modes with overlapping lifetimes is a verifier error. Live Dst DEFINEs must fit: Σ `count·depth·tile.rows` ≤ capacity (verifier), so there is no hard-coded half |
| REG | vector (32 lanes × 32b) or scalar | f32/i32/u32 | loop carries only |

Formats change **only on edges**: UNPACK (L1 → Src/Dst), PACK (Dst → L1,
with rounding mode), FPU moves (D2A/D2B truncate to tf32/bf16), SFPU
LOAD/STORE (Dst format ↔ fp32), explicit SFPU `CAST`/`STOCHRND`. Fidelity is
an FPU op argument. The precision path of a kernel is therefore readable
directly off its graph.

### 3.2 Views (INDEX)

Same as ttk: `INDEX(storage, occupancy)` names an occupancy, and
`INDEX(occupancy, offset)` with `arg=(extent,)` is a subview. One addition:

* `INDEX(view, offset, x, y)` is **the same view on core (x, y)** (remote L1).
* `INDEX(view, offset, x0, y0, x1, y1)` is **the rectangle** (multicast
  destination). Arity distinguishes them. Coordinates are scalar UOps, usually
  SPECIAL arithmetic.

Frontend sugar: `S[i]` (explicit occupancy) or `S.next()` (auto-numbered;
the current ttk mixed-radix numbering, emitted as explicit index
arithmetic), `.tile(j)`, `.tiles(j, n)`, `.face(j, f)`, `.rows(r, n)`,
`.cols(c, n)`, `.word(k)` (u32 scalar view), `.on(x, y)`, `.on(rect(...))`.
Global views are `g.tile(i)`, `g.tiles(rows=(r,n), cols=(c,m))`, `g.row(i)`,
`g.bytes(off, n)`. There is one fixed layout map (row-major, tile-sized pages
interleaved across banks), and lowering turns these views into page/bank
addresses with it. `g.tile(i)` on a 2D tensor is the 32×32 block, which is 32
strided row segments in DRAM (NoC batching merges them). It lands in L1
row-major; tilizing it is the kernel's job (§3.5).
`g.chunk(i)` is the i-th 1024 contiguous elements, i.e. exactly one page,
which is what elementwise kernels want.

**Strided row views** (`.rows(start, n, stride)`) map to UNPACK/PACK address-
counter Y strides and to NoC batching on GLOBAL. They are needed for strided and
dilated conv (implicit GEMM: tap `(ky,kx)` reads rows `q·s + ky·Wp + kx` of a
padded NHWC buffer). The verifier checks that unpacked row starts are 16-byte
aligned. Conv itself is a library function (`lib.conv2d`), not an op:
CONV3S*/MPOOL3* are neutered on BH, so it is a sum of per-tap MVMULs over
shifted views.

Occupancy indices must be **dense and monotone in program order** per storage
(checked). That is exactly the property that lets them lower to CB counters.

### 3.3 Resident (pinned) data within a kernel

A `depth=1` L1 DEFINE that is written once and read many times is resident for
the whole kernel. Its single slot is never reused, and no new concept is needed.
To pin part of a tensor, use two storages over the same GLOBAL: a resident one
for the pinned tiles and a `depth=2` ring that streams the rest. Sugar:

```python
Wp = l1.resident(w.tiles(rows=(0, 8), cols=(0, NT)))   # DEFINE depth=1 + one NOC_READ, emitted before any loop
Ws = l1(Tile(bf16), count=NT, depth=2)                  # streamed remainder
```

Add `at=` when the address matters (for example, matching a layout another
core multicasts into). State that must outlive the kernel is a separate,
unsolved problem (§13).

### 3.4 Remote producers

Storage that another core fills declares who fills it:
`DEFINE(src=(px, py), arg=(Storage(...),))`. The coordinates are expressions in
SPECIAL. On the core where `(px, py)` evaluates to itself, the storage is local.
This one declaration replaces ttk's `producer='remote'`, `peer`, `receive`,
`PeerGroup` and `Connection`. The verifier evaluates the grid, pairs every
remote write with the target core's reads of that occupancy, and checks that
each occupancy is written exactly once by the declared producer. Credit return
(the consumer freed slot `i-d`) is derived. Multiple producers use one
DEFINE each, made in a Python loop.

### 3.5 Layout inside a kernel: tilize and untilize are internal

GLOBAL is always row-major (§3.1). The FPU, however, wants face-ordered
operands: Src rows are 16 datums wide, so a 32×32 operand is consumed as 16-wide
column panels (any face permutation is absorbed by MVMUL addressing). So every
kernel that feeds the FPU from GLOBAL tilizes, and every kernel that packs a
result for GLOBAL untilizes. Both happen **inside the kernel** and are visible
in the graph through `Tile.layout` on L1 storages:

* `NOC_READ` from GLOBAL fills `layout='rows'` L1, and `NOC_WRITE` to GLOBAL
  reads `layout='rows'` L1. The one exception is a contiguous one-page view
  (`g.chunk(i)`, or `g.tile(t)` of a `(T, 32, 32)` tensor). It may land directly
  in `faces` L1, meaning "treat these 1024 elements as a tile." That is exact
  for Map kernels, whose ops don't care about element position (SwiGLU §6.1,
  conv §6.9), and the reference interpreter catches any misuse. Anything
  else is a verifier error.
* **Untilize** is a PACK mode (`PackArgs.layout='rows'`): Dst → row-major L1 →
  NOC_WRITE (tt-llk `pack_untilize`). It is paid once per output tile, with no
  reuse multiplier, though its throughput isn't measured here yet.
* **Tilize** has two placements, and the author picks one:
  1. **At each use:** UNPACK from `rows` L1 with the tilize/strided-gather mode
     straight into Src. There is no extra storage, but the gather is repeated every
     time the operand is unpacked. This is right for single-use operands and for
     FP8, whose native unpack tilize gathers both panels in two instructions.
  2. **Once, into tiled L1:** `lib.tilize(T, R)` = UNPACK(tilize) → FPU mov →
     PACK(`faces`) from a `rows` storage `R` into a `faces` storage `T`, then the
     hot loop unpacks `T`. This is right for **reused 16-bit operands**:
     Blackhole's tilize mode reads 32 datums per row at 16 bits, so BF16 can't use
     FP8's two-instruction path and needs 64 16-datum UNPACRs per tile instead.
     Measured on P150 at 5000³ (`tests/movement/matmul_row_major.md`):
     BF16 that is row-major and tilized at each use reaches 50.9 TFLOP/s, against
     182.5 when the operand is already tilized (same HiFi2/BF16 mode). FP8 at
     each use loses only 5.5% (370.8 vs 392.3). Tilizing once per K block,
     on every core, measured 188.2 TFLOP/s from row-major DRAM with BF16
     accumulation (above the 182.5 host-tilized baseline), and 132.5 with the
     FP32 accumulation the kernel now uses. That required fast DRAM readers;
     without them the kernel was reader-bound at 98.6. The untilize is a PACK
     epilogue (FP32 Dst -> row-major BF16) costing one pass per output tile. Cheapest BF16 tilize measured:
     eight row UNPACRs plus a Dst-remapped pack. tt-metal's one-UNPACR
     tileize leaves row halves interleaved in Src, and its de-interleaving
     pack costs 32 PACRs per tile, so it measured 179.7.

  A multicast matmul could instead have the leader core tilize once and
  multicast the tiled block (§6.3), paying the tilize once per row or column
  of cores. matmul_peak currently tilizes on every core.

---

## 4. Ops

This is a revision of `ttk/uop.py:Ops`. tinygrad names are reused wherever the
meaning matches.

### 4.1 Structure (unchanged unless marked)

| Op | src | arg | notes |
|---|---|---|---|
| SINK | effects | | |
| CONST | | (value,) | |
| PARAM | | (ParamArg,) | buffers gain `location`; GLOBAL layout is fixed (§3.1) |
| **SPECIAL** *(new)* | | ('core_x'\|'core_y', extent) | tinygrad name |
| DEFINE | producer coords *(new, optional)* | (Storage,) | |
| INDEX | view, offset[, x, y \| x0,y0,x1,y1] | (extent,) | remote/multicast operands are new |
| AFTER | value, deps… | | |
| RANGE | bound[, outer] | (name,) | **runtime bounds allowed** (any bounded scalar expr) |
| END | body, range | | |
| **IF / ENDIF** *(new)* | cond / if | | SPECIAL-only conditions are specialized away |

### 4.2 Values: RISC-V scalars and SFPU vectors

The dtype decides the engine: `i32/u32` means RISC-V, `f32.vec32/i32.vec32`
means SFPU.

| Op | Use |
|---|---|
| ADD SUB MUL MULACC NEG MAX | both (MULACC = SFPMAD) |
| CMPLT CMPNE CMPEQ WHERE | both. On SFPU, **WHERE is the only predication primitive**. The backend clusters WHEREs with a shared condition into SETCC/ENCC/PUSHC/POPC/COMPC regions. Any CC-stack program is SSA + WHERE. |
| AND OR XOR SHL SHR | both |
| IDIV MOD | scalar only |
| CAST BITCAST | both (SFPCAST modes, int sign-magnitude ↔ 2's complement) |
| **VOP** *(new)* arg=(mnemonic, mod, imm) | SFPU-only data instructions without a tinygrad equivalent: `exexp exman setexp setman setsgn abs lz arecip divp2 mul24 lut lutfp32 stochrnd shft2 transp swap` |
| GEP | picks an output of multi-result VOPs (`transp` → 4, `swap` → 2) |
| LOAD | `src=(view,)`. For SFPU, view = 4 Dst rows and `arg=(LaneMap(parity, col_exchange, capture_index),)`. For scalars, an L1 `.word()` view or REG. |
| STORE | `src=(view, value)`, **destination first** (tinygrad order; ttk currently has value first) |

Transcendentals (`exp`, `recip`, `rsqrt`, `sigmoid`, `silu`) are **not ops**.
They are frontend library functions that emit primitive ALU/VOP sequences, the
same approach as tinygrad's `transcendental.py`. The exp/recip/rsqrt variants in
`ttko/sfpu.py` and `tests/operation_pocs/sfpu_math` become library entries, so
picking an accuracy/speed variant stays an author decision.

Runtime constants (FP8 scales, `1/N`, a token-dependent value) are
`CAST(scalar) → vec` broadcasts. Today's instruction-buffer patching of
SFPLOADI words is then a *lowering technique* the backend may use, not
something the author writes.

### 4.3 Effects: the engine edges

All effects follow the convention `src[0]` = destination view, then sources.

| Op | Edge | arg | covers |
|---|---|---|---|
| **NOC_READ** | GLOBAL / remote L1 / local L1 → local L1 | `NocArgs(noc, vc, …)` | DRAM reads (interleaved/sharded/strided/gather by scalar offset), remote L1 pull, local L1→L1 (backend may pick XMOV) |
| **NOC_WRITE** | local L1 → GLOBAL / remote L1 / multicast rect / host | `NocArgs(noc, vc, posted, include_self)` | DRAM writes, unicast push, multicast, PCIe to host |
| **NOC_ATOMIC** *(new)* | scalar → remote L1 word | `(kind, width)`, kind ∈ inc, cas, swap, simd_add(fp32x4/bf16x8/…) | returns old value (u32) or void |
| **UNPACK** | L1 → SRCA \| SRCB \| DST | `UnpackArgs(transpose, tilize_row_stride, faces, upsample, rows, exp_section, …)` | every UNPACR mode; to-DST = Unp0 direct (fp32/int32) |
| **FPU** *(merges FPU_ELW/MATMUL/POOL/DOTPV/MOVE)* | SRCA, SRCB → DST; or moves | `FpuArgs(kind, broadcast, fidelity, accumulate, index)` | kind ∈ mvmul dotpv elwadd elwsub elwmul gapool gmpool mova2d movb2d movb2a movd2a movd2b trnspa trnspb shiftxa shiftxb zero fill |
| **PACK** | DST → L1 | `PackArgs(accumulate, relu, threshold, edge_mask, rounding, exp_threshold, layout, downsample)` | every PACR mode; `accumulate` may be a src predicate (`k > 0`) |

**Granularity.** Engine ops have *native-instruction semantics extended to
view extents*. An MVMUL with views of 8×16 (SrcB) · 16×16 (SrcA) → 8×16 (Dst)
is one instruction. Larger extents mean "the obvious tiling", and fringes are
simply smaller views. `lib.matmul_tile` is a frontend helper, not an op. The
graph therefore contains real loops over real instructions, which is what
MOP/replay recognition needs (§9).

**Fidelity** is a phase count (1 to 4) on `mvmul/dotpv/elwmul/gapool`. The
verifier rejects >1 on `elwadd/elwsub` (hardware is LoFi-only).

### 4.4 Explicit tier (escape, rarely used)

| Op | Why it must exist |
|---|---|
| **WAIT** `src=(word_view, value)` arg=(cond,) | Sync the dependency graph cannot show: host handshakes, wave gating on an atomic counter, epoch flags from a previous launch. Its result is an effect usable in AFTER. |
| **CUSTOM** `src=(views read..., views written...)` arg=(thread, words, n_writes) | Raw instructions. Declared reads and writes keep derived sync correct around them. This is the completeness guarantee for anything §8 missed. |

### 4.5 Backend-only (rejected in frontend graphs)

`MOP_*`, `REPLAY_*`, `MACRO_*`, `CFG_*` (already in ttk), lowered sync
(`SEM_POST/SEM_WAIT/STALL/CB_PUSH/CB_WAIT`), and `INS` (tinygrad's machine
instruction). The lowered program is a per-thread `LINEAR` of INS.

---

## 5. Frontend API (Python, tracing)

```python
from ttk import kernel, Global, Scalar, Tile, core, when, loop, l1, srca, srcb, dst, vreg, sreg
from ttk import noc, unpack, fpu, pack, sfpu, load, store, wait, custom, lib
from ttk.dtypes import bf16, fp16, fp32, tf32, fp8e4m3, bfp8, bfp4, u32

for i in loop(n): ...    # RANGE/END (n may be a runtime scalar). Python range() unrolls.
with when(cond): ...     # IF/ENDIF
acc = vreg(0.0)          # REG carry; acc.get(), acc.set(v) or acc += v
```

`for i in loop(n)` is a generator that yields the RANGE symbol once and closes
END when the body finishes. It is ordinary Python syntax and needs no closures
(current ttk takes `loop(n, body)`).

---

## 6. Worked kernels

These are sketches written against the API above, with `...` marking elided
indexing. Each one exercises a different part of the surface. Together they
cover every kernel in the current repo plus the likely Qwen additions.

### 6.1 Map: SwiGLU (SFPU, double-buffered, multi-core)

```python
@kernel(grid=(GX, 1))
def swiglu(gate: Global(bf16, (T, 32, 32)), up: Global(bf16, (T, 32, 32)), out: Global(bf16, (T, 32, 32))):
  per = T // GX
  g, u, o = (l1(Tile(bf16), depth=2) for _ in range(3))
  A, B = srca(bf16), srcb(bf16)
  D = dst(fp32, Tile(fp32), count=2, depth=2)           # 32-bit Dst, half-sync
  for i in loop(per):
    t = core.x * per + i
    noc.read(g[i], gate.tile(t)); noc.read(u[i], up.tile(t))
    unpack(A[i], g[i]); unpack(B[i], u[i])
    fpu.mova2d(D[i].tile(0), A[i]); fpu.movb2d(D[i].tile(1), B[i])
    for xl, ul in sfpu.lanes(D[i].tile(0), D[i].tile(1)):   # traced RANGE over 32 lane groups
      x, y = load(xl), load(ul)
      store(xl, x * lib.sigmoid(x) * y)
    pack(o[i], D[i].tile(0), rounding='rne')
    noc.write(out.tile(t), o[i])
```

The trace looks like this (abridged; this is the UOp shape you already have):

```
r   = RANGE(CONST(per))
t   = ADD(MUL(SPECIAL(core_x), CONST(per)), r)
rg  = NOC_READ(INDEX(g, r), INDEX(gate, MUL(t, 2048)))
ua  = UNPACK(INDEX(A, r), INDEX(AFTER(g, rg), r))
mv  = FPU(INDEX(INDEX(D, r), 0), INDEX(AFTER(A, ua), r)) arg=FpuArgs('mova2d')
lr  = RANGE(CONST(32), r)
x   = LOAD(INDEX(AFTER(INDEX(D, r), mv), MUL(lr, 4))) arg=(LaneMap(...),)
st  = STORE(INDEX(..), MUL(MUL(x, <sigmoid(x) subgraph>), y))
...
```

The backend sees: reader on BRISC/NCRISC, two UNPACKs on T0, moves and SFPU on
T1, PACK on T2, the write on a NoC RISC. All CB/sem/dvalid/Dst-section sync
follows from `depth=2` and the INDEX/AFTER edges. The SFPU loop body is a
LOADMACRO candidate, and the move loop is a MOP candidate.

### 6.2 Reduce: RMSNorm (SFPU carry, library rsqrt)

```python
@kernel(grid=(1, 1))
def rmsnorm(x: Global(bf16, (N,)), w: Global(bf16, (N,)), out: Global(bf16, (N,)), eps=1e-5):
  T = N // 1024
  xs, ws = l1(Tile(bf16), count=T), l1(Tile(bf16), count=T)        # resident
  A, B = srca(bf16), srcb(bf16)
  X, W = dst(fp32, Tile(fp32), count=T), dst(fp32, Tile(fp32), count=T)  # two independent Dst registers; verifier checks 2T <= 8
  noc.read(xs, x.tiles(0, T)); noc.read(ws, w.tiles(0, T))
  for t in loop(T):
    unpack(A.next(), xs.tile(t)); fpu.mova2d(X.tile(t), A.cur)
    unpack(B.next(), ws.tile(t)); fpu.movb2d(W.tile(t), B.cur)
  ss = vreg(0.0)
  for ln in sfpu.lanes(X):
    v = load(ln); ss += v * v
  scale = lib.rsqrt(lib.lane_sum(ss.get()) * (1.0 / N) + eps)
  for xl, wl in sfpu.lanes(X, W):
    store(xl, load(xl) * load(wl) * scale)
  o = l1(Tile(bf16), count=T)
  pack(o, X); noc.write(out.tiles(0, T), o)
```

The hybrid variant (FPU `elwmul` x·γ at fidelity 4 into `W` while the SFPU
squares `X`) is the same program with `fpu.elwmul(...)` replacing the
γ multiply. The engine choice stays in the source.

### 6.3 Contract: multicast blocked matmul (matmul_peak shape)

```python
@kernel(grid=(C, R))
def matmul(a: Global(bf16, (M, K)),            # row-major, 2048 B pages
           b: Global(fp8e4m3, (K, N)),         # row-major, 1024 B pages
           c: Global(bf16, (M, N))):
  x, y = core.x, core.y
  MT, NT, KT = M // 32 // R, N // 32 // C, 2
  KB, SB = K // 32 // KT, MT * NT // 4                      # K blocks, 2x2 subblocks
  Ar = l1(Tile(bf16, layout='rows'), count=MT * KT, depth=2)       # row leader only: row-major landing buffer
  As = l1(Tile(bf16),    count=MT * KT, depth=2, producer=(0, y))   # row leader tilizes + multicasts (§3.5)
  Bs = l1(Tile(fp8e4m3, layout='rows'), count=KT * NT, depth=2, producer=(x, 0))  # fp8: stays row-major, tilized at unpack
  P  = l1(Tile(fp32), count=MT * NT)                                # fp32 partial, L1-accumulated
  O  = l1(Tile(bf16, layout='rows'), count=MT * NT)               # untilized by PACK for the row-major write
  LHS, RHS = srcb(bf16), srca(fp16)       # MVMUL: in0 rows -> SrcB (8x16), in1 -> SrcA (16x16); fp8 expands to fp16
  D = dst(fp32, Tile(fp32), count=4, depth=2)

  for k in loop(KB):
    with when(x == 0):
      noc.read(Ar[k], a.tiles(rows=(y * MT, MT), cols=(k * KT, KT)), noc=0)
      lib.tilize(As[k], Ar[k])                                # bf16 is reused NT times per core: tilize once
      noc.write(As[k].on(rect((1, y), (C - 1, y))), As[k], noc=0)
    with when(y == 0):
      noc.read(Bs[k], b.tiles(rows=(k * KT, KT), cols=(x * NT, NT)), noc=1)
      noc.write(Bs[k].on(rect((x, 1), (x, R - 1))), Bs[k], noc=1)
    for s in loop(SB):
      d = D.next()
      for kt in range(KT):
        for mi in range(2):
          lhs = LHS.next(); unpack(lhs, As[k].tile(...))
          for ni in range(2):
            rhs = RHS.next(); unpack(rhs, Bs[k].tile(...))
            lib.matmul_tile(d.tile(2 * mi + ni), lhs, rhs, fidelity=2, accumulate=kt > 0)
      pack(P.tiles(4 * s, 4), d, accumulate=(k > 0))          # L1 += Dst after the first K block

  for s in loop(SB):                                          # epilogue: fp32 partial -> bf16
    d = D.next()
    unpack(d, P.tiles(4 * s, 4))                              # unpack-to-dest, fp32 exact
    pack(O.tiles(4 * s, 4), d, rounding='rne', layout='rows')   # untilize
  noc.write(c.tiles(rows=(y * MT, MT), cols=(x * NT, NT)), O, noc=x % 2)
```

Everything matmul_peak decides is in the source: which RISC/NoC reads which
operand, multicast topology, block sizes, fidelity, FP8→fp16 at unpack, fp32
accumulation in Dst and in L1, and the dual-writer NoC choice. Edge tiles are
smaller views; `lib.matmul_tile` emits 8×16 MVMULs, which replaces the
generated `edges.py` subroutines. The backend chooses none of this. It turns
`lib.matmul_tile` loops into MOP+replay, batches the reads, and inserts
multicast credits.

### 6.4 Scan + collective: flash-decode GQA with split-KV merge

```python
@kernel(grid=(SPLIT, KVH))                           # x = KV split, y = KV head
def attn_decode(q: Global(bf16, (QH, 128)), kc: Global(bf16, (KVH, MAXT, 128)),
                vc: Global(bf16, (KVH, MAXT, 128)), out: Global(bf16, (QH, 128)),
                pos: Scalar(u32, 0, MAXT - 1)):
  s, h = core.x, core.y
  nblk = pos // 32 + 1                                   # runtime scalar
  per = (nblk + SPLIT - 1) // SPLIT
  lo = s * per
  n = max(0, min(per, nblk - lo))                        # runtime trip count
  Qs = l1(Tile(bf16, rows=8, cols=128))                  # 4 heads valid; 8-row tiny tile
  Ks, Vs = l1(Tile(bf16, 32, 128), depth=2), l1(Tile(bf16, 32, 128), depth=2)
  LHS, RHS = srcb(bf16), srca(bf16)
  S = dst(fp32, Tile(fp32, 8, 32), depth=2)              # scores
  O = dst(fp32, Tile(fp32, 8, 128))                      # resident context accumulator
  m, l = vreg(-inf), vreg(0.0)
  noc.read(Qs, q.rows(h * 4, 4))
  fpu.zero(O)
  for i in loop(n):
    blk = lo + i
    noc.read(Ks[i], kc.rows(h, blk * 32, 32)); noc.read(Vs[i], vc.rows(h, blk * 32, 32))
    for f in range(4):                                   # QK^T over 4 feature chunks
      lhs = LHS.next(); unpack(lhs, Qs.cols(32 * f, 32))
      rhs = RHS.next(); unpack(rhs, Ks[i].cols(32 * f, 32), transpose=True)
      lib.matmul(S[i], lhs, rhs, fidelity=2, accumulate=f > 0)
    # SFPU: scale, causal mask (cols past pos -> -inf via lane ids), online update, rescale O
    lib.online_softmax_step(S[i], O, m, l, scale=128 ** -0.5, valid=pos - blk * 32 + 1)
    p = LHS.next(); fpu.movd2b(p, S[i])                  # P: Dst -> SrcB, no L1 round trip
    for f in range(4):
      rhs = RHS.next(); unpack(rhs, Vs[i].cols(32 * f, 32))
      lib.matmul(O.cols(32 * f, 32), p, rhs, fidelity=2, accumulate=True)
  # collective: partial (O, m, l) -> merge core (0, h). One inbox per producer.
  inbox = [l1(Tile(fp32, 8, 128 + 32), producer=(j, h)) for j in range(SPLIT)]
  stage = inbox[s]
  lib.pack_partial(stage, O, m, l)                       # pack O, store m, l as words
  noc.write(stage.on(0, h), stage)
  with when(s == 0):
    lib.merge_partials(out.rows(h * 4, 4), inbox)        # unpack-to-dest fp32, exp-rescale, normalize
```

This shows a runtime RANGE, an SFPU mask from lane ids instead of a −∞ tile,
MOVD2B, a resident Dst accumulator, vreg carries, and a cross-core merge where
the producer declarations derive all the flags that `_gqa_attention_program`
and `gqa_attention_merge` hand-code today.

### 6.5 Collective with data-dependent control: argmax → host + broadcast

```python
@kernel(grid=(GX, GY))
def argmax(logits: Global(bf16, (V,)), token: Global(u32, (1,), location='host'),
           params: Global(u32, (16,))):
  me, NC = core.y * GX + core.x, GX * GY
  T = V // NC // 1024
  L = l1(Tile(bf16), depth=2); A = srca(bf16); D = dst(fp32, Tile(fp32), depth=2)
  best = vreg((-inf, 0))                                  # (key, index) pair
  for t in loop(T):
    noc.read(L[t], logits.tile(me * T + t)); unpack(A[t], L[t]); fpu.mova2d(D[t], A[t])
    for ln in sfpu.lanes(D[t]):
      kv = load(ln, capture_index=True)                   # SFPCONFIG index mode is lowering
      best.set(sfpu.maxpair(best.get(), kv))              # VOP('swap', minmax) on tagged pairs
  cand = [l1(Tile(u32, 1, 64), producer=(j % GX, j // GX)) for j in range(NC)]
  lib.store_pairs(cand[me], best.get(), base=me * T * 1024)   # 32 (key, idx) words
  noc.write(cand[me].on(0, 0), cand[me])
  with when(me == 0):
    bk, bi = sreg(0), sreg(0)
    for j in range(NC):                                   # RISC-V scalar reduce
      for w in loop(32):
        k, ix = load(cand[j].word(2 * w)), load(cand[j].word(2 * w + 1))
        take = CMPLT(bk.get(), k)
        bk.set(WHERE(take, k, bk.get())); bi.set(WHERE(take, ix, bi.get()))
    store(prm.word(0), bi.get())                          # prm = l1(Tile(u32, 1, 16), producer=(0, 0)), declared above
    noc.write(token, prm.word(0))                         # PCIe write to host
    noc.write(prm.on(rect((0, 0), (GX - 1, GY - 1))), prm)   # next-token params to every core's prm
```

### 6.6 Move: embedding and KV append (scalar addressing)

```python
@kernel(grid=(1, 1))
def embed(params: Global(u32, (16,)), table: Global(bf16, (VOCAB, E)), out: Global(bf16, (E,))):
  p = l1(Tile(u32, 1, 16)); noc.read(p, params)
  tok = load(p.word(0))                                   # data-dependent address
  row = l1(Tile(bf16, 1, E, layout='rows'))
  noc.read(row, table.row(tok)); noc.write(out, row)

@kernel(grid=(KVH, 1))
def kv_append(k: Global(bf16, (KVH, 128)), kc: Global(bf16, (KVH, MAXT, 128)),
              pos: Scalar(u32, 0, MAXT - 1)):
  r = l1(Tile(bf16, 1, 128, layout='rows')); noc.read(r, k.row(core.x))
  noc.write(kc.row(core.x, pos), r)     # row-major cache: one contiguous 256 B row write
```

### 6.7 Scan with explicit precision: Gated-DeltaNet decode step

This assumes Qwen-style linear attention: S ← g·S + k·(β(v − Sᵀk))ᵀ, o = Sᵀq,
with a 128×128 fp32 state per head. Columns of S update independently, so the
kernel processes 128×32 column blocks, 4 fp32 tiles each, which is half of a
32-bit Dst:

```python
  St = l1(Tile(fp32, 128, 32), count=4)              # resident fp32 state, one head
  for cb in range(4):
    d = D.next()                                     # dst(fp32, Tile(fp32,128,32), depth=2)
    unpack(d, St.tile(cb))                           # unpack-to-dest: state stays fp32 exact
    ks = lib.matvec(KS.next(), kvec, St.tile(cb), src_fmt=tf32)   # Sᵀk via MVMUL; TF32 here is a CHOICE
    u  = lib.scale_sub(beta, v.cols(32 * cb, 32), ks)            # SFPU, fp32
    for ln in sfpu.lanes(d): store(ln, load(ln) * g)              # decay in Dst, fp32
    kcol = LHS.next(); unpack(kcol, kvec_tile, transpose=True)    # k as a column -> SrcB
    urow = RHS.next(); lib.vec_to_srca(urow, u)                   # u as row 0 of SrcA (pack+unpack, or movd2a)
    lib.matmul(d, kcol, urow, fidelity=4, accumulate=True)        # rank-1 update, HiFi4 into fp32 Dst
    pack(St.tile(cb), d, rounding='none')                         # fp32 back to L1 (new version)
    lib.matvec(Ob.cols(32 * cb, 32), qvec, St.tile(cb), src_fmt=tf32)   # o = Sᵀq reads the new version
```

The state keeps fp32 end to end, and the only lossy steps (TF32 inputs to the
two matvecs) are visible in the source. If those turn out too lossy, the
alternative (SFPU dot products from an unpack-to-dest copy) is a source change,
not a backend change.

### 6.8 Explicit tier: DRAM writer waves (matmul_peak `writers.py`)

```python
  done = l1(Tile(u32, 1, 4), producer='any')         # counter word on core (0,0)
  wait(gate.word(0), my_wave, cond='>=')             # spin on an L1 word
  noc.write(c.tiles(...), O)
  noc.atomic(done.word(0).on(0, 0), 1, kind='inc')
```

This is the only kind of code where the author writes sync by hand, and it is
always visible as WAIT/NOC_ATOMIC in the graph.

### 6.9 Map with a ring-buffer state: Gated-DeltaNet short conv (4 taps, 10240 ch)

The conv is depthwise, so per token it is an elementwise map:
`out[c] = silu(Σ_j w[j,c]·x[t-3+j,c])`. The weight is transposed once at load
from `(C,1,4)` to `(4,C)`. The conv state is a 4-slot ring (slot `t%4` holds
token `t`), so the "shift" is just a write of the new token. Elementwise ops
don't care about tile layout, so 1024-channel chunks are unpacked as tiles
without tilize.

```python
@kernel(grid=(10, 1))
def conv_silu(qkv: Global(bf16, (C,)), state: Global(bf16, (4, C)),
              w: Global(bf16, (4, C)), out: Global(bf16, (C,)),
              pos: Scalar(u32, 0, MAXT - 1)):
  c = core.x * 1024
  X, W = l1(Tile(bf16), count=4), l1(Tile(bf16), count=4)
  A, B = srca(bf16), srcb(bf16)
  D = dst(fp32, Tile(fp32))
  for j in range(3):
    noc.read(X.tile(j), state.row((pos + 1 + j) % 4).cols(c, 1024))
  noc.read(X.tile(3), qkv.cols(c, 1024))
  for j in range(4):
    noc.read(W.tile(j), w.row(j).cols(c, 1024))
  noc.write(state.row(pos % 4).cols(c, 1024), X.tile(3))      # whole state update
  fpu.zero(D)
  for j in range(4):
    a = A.next(); unpack(a, X.tile(j))
    b = B.next(); unpack(b, W.tile(j))
    fpu.elwmul(D, a, b, fidelity=4, accumulate=True)
  for ln in sfpu.lanes(D):
    v = load(ln); store(ln, v * lib.sigmoid(v))
  O = l1(Tile(bf16)); pack(O, D, rounding='rne')
  noc.write(out.cols(c, 1024), O)
```

Preferred placement is as an epilogue of the `in_proj_qkv` projection. The
conv is channel-local, so the core that produced channels `[c0,c1)` convolves
them with no extra launch or cross-core traffic. Round the projection to bf16
first to match the reference. Align each core's range to 128 inside q|k|v so
the q/k L2 norm fuses too. For prefill, each tap is an `elwmul` of the input
shifted by `j` rows against the weight row with `broadcast='row'`.

---

## 7. Why STALLWAIT, semaphores, RWCs and config are *not* author-visible

The hardware survey (tt-isa-documentation, tt-llk) suggests a "complete" DSL
must expose the full STALLWAIT block×condition cross-product, dvalid flips,
RWC/ADC counters and config writes. I disagree:

* **They are functions of the data flow.** A STALLWAIT before a MOVD2B exists
  because a math thread reads Src that it must own. That fact is already the
  edge `FPU(movd2b) after UNPACK/FPU writer`. Exposing the instruction adds a
  way to be wrong without adding a kernel you can express.
* **Exposing them would freeze the schedule.** MOP and replay rewriting must
  move these instructions. If the author placed them, every optimization would
  first have to prove the placement did not matter.
* **The constraints are real, but they bind the backend, not the language.**
  The 4-cycle Dst read-after-write window, the ≥5-block accumulate rule, MOVD2A/B
  needing explicit Src-owned waits, SEMPOST saturating at 15, forced non-posted
  atomics, fp16 L1-accumulate producing NaN, ELWADD LoFi-only, and int8 requiring
  32-bit Dst are each either a verifier rule (rejected at trace time) or a
  lowering obligation. §9 lists them.
* **The escape still exists.** `CUSTOM` with declared reads and writes, plus
  `WAIT`/`NOC_ATOMIC`, means a schedule the data-flow model cannot show is
  still expressible. It just isn't the default.

---

## 8. Completeness checklist (hardware → frontend)

| Hardware | Frontend | Notes |
|---|---|---|
| UNPACR: formats, tilize, haloize transpose, faces/z, upsample, to-dest, exp section, RLE | UNPACK args | "Broadcast" is not an unpacker feature; it lives on FPU `broadcast` |
| UNPACR_NOP, CLEARDVALID, SETDVALID (dead on BH), GATESRCRST | derived | |
| MVMUL DOTPV ELWADD/SUB/MUL GAPOOL GMPOOL(+index) | FPU kind + fidelity/broadcast/accumulate | CONV3*/MPOOL3*/APOOL3* are neutered on BH and excluded |
| MOVA2D MOVB2D MOVB2A MOVD2A MOVD2B MOVDBG* TRNSPSRCA/B SHIFTXA/B | FPU move kinds | |
| ZEROACC ZEROSRC | FPU `zero` / `fill(0 \| -inf)` | ZEROACC used as an "accumulate start" marker is derived from `accumulate=False` |
| SFP data instrs (all ~45) | ALU ops + VOP + LOAD/STORE | |
| SFPSETCC ENCC PUSHC POPC COMPC GT LE | WHERE / CMP* | lowered to CC regions |
| SFPCONFIG | derived: constant LRegs 11–14 from CONST, lane/index mode from LOAD args | |
| SFPLOADMACRO | **backend optimization** | |
| PACR (all modes), SETPKEDGOF | PACK args | fp16 L1-accumulate rejected (HW bug) |
| WRCFG SETC16 RMWCIB CFGSHIFTMASK RDCFG REG2FLOP STREAMWRCFG | derived from op args | redundant-config elimination is lowering |
| SETRWC INCRWC ADDRMOD SETADC* INCADC* ADDRCR* | derived from view offsets | |
| DMAREG ALU, LOADIND, STOREIND, LOADREG, STOREREG | RISC-V scalar values | the backend may place scalar math on Tensix GPRs (RISC-V optimization) |
| ATCAS ATINCGET ATSWAP (local) / NoC atomics incl. SIMD add | NOC_ATOMIC | NOC_CMD_L1_ACC_AT_EN is bugged and never emitted |
| SEM* STALLWAIT STREAMWAIT ATGETM/ATRELM | derived; WAIT for explicit cases | |
| MOP, MOP_CFG, REPLAY | **backend optimization** | |
| XMOV | NOC_READ local→local (backend may choose the mover) | |
| NoC read/write/inline/multicast, VCs, posted | NOC_READ/NOC_WRITE + NocArgs | WR_INLINE to L1 is unsafe on BH and never emitted |
| PCIe host writes | NOC_WRITE to GLOBAL(location='host') | |
| Ethernet / multi-chip | **not yet**: future GLOBAL space `remote_chip` | the llama `eth_output` all-gather has no home until then |
| GDDR-controller DRISC programs | **out of scope** (a different processor and program kind) | |
| Resident launch patching, trace replay | **out of scope** (launch layer, not kernel) | |

Anything not in this table is reachable only through CUSTOM. Each CUSTOM in
the kernel corpus is a ticket to either add a mode or move it to this table.

---

## 9. Contract for the (future) backend

**Lowering (mechanical; no choices):** thread placement by engine (respecting
`UOp.thread` hints), sync derivation from INDEX/AFTER and depth, L1/Dst/LReg
allocation (respecting `at=`/`alias=`), config derivation, DRAM layout address
math, 1:1 instruction selection, WHERE → CC regions, SPECIAL specialization.

**Optimizations (the only five):**

| Optimization | Matches | Preconditions the frontend guarantees |
|---|---|---|
| RISC-V | scalar SSA, per-core specialization, hoisting, Tensix-GPR placement | scalars are SSA; SPECIAL is known per core |
| MOP | RANGE nests of FPU/UNPACK/PACK whose view offsets are affine in the RANGE | views are affine INDEX arithmetic; addresses inside FPU loops are never data-dependent |
| Replay | repeated straight-line instruction sequences (unrolled `range()` bodies, fidelity phases, SFPU blocks) | 32 slots per thread; the backend partitions them (today 0–15 SFPU, 16–31 FPU) |
| SFPLOADMACRO | `LOAD → ≤4 ops on distinct sub-units → STORE` chains in SFPU RANGE bodies | ops are SSA, so the sub-unit/delay schedule can be solved; ≤4 macros |
| NoC batching | adjacent NOC_READ/WRITE with contiguous or strided addresses, same destination; posted-write + one barrier; stateful command-buffer reuse | views carry exact byte extents and layout maps |

**Invariants the backend must respect** (from the hardware survey): no Dst read
within 4 cycles of a write to the same 8×16 block; MOVD2A/B wait for Src
ownership; SEMPOST saturates at 15; Src ownership ordering; config drains
before writes (C12 is cross-thread); MOP config is live-sampled; REPLAY may
not contain MOP; push-then-load needs a fence; inline writes and atomics are
forced non-posted on BH.

**Dst sync lowering.** In the hardware, "halves" are only a convention. The
math base (`DEST_TARGET_REG_CFG_MATH_Offset`, set by SETC16) and the pack base
(`PACK_SEC0_Offset`, set by WRCFG) are plain row offsets, and tt-metal's
SyncHalf is one Tensix semaphore (`MATH_PACK`, SEMINIT max 2) plus a strict
0/HALF base flip on each side and `ZEROACC CLR_HALF` on release
(`tt-llk/.../llk_math_common.h`, `llk_pack_common.h`). It can only express one
FIFO of two equal regions handed off in lockstep. The lowering is therefore
per Dst DEFINE:

* every cross-thread Dst edge (FPU→PACK, FPU↔SFPU when SFPU runs on another
  TRISC, SFPU→PACK) on a DEFINE gets its own semaphore with max = `depth`;
* slot bases are absolute (`base(DEFINE) + slot·count·rows`), written per
  access with SETC16/WRCFG instead of flipped;
* a freed slot is cleared with `ZEROACC CLR_SPECIFIC`/`CLR_16` over its rows,
  or not at all when the next writer has `accumulate=False`;
* DEFINEs whose handoffs are provably in lockstep (same producer and consumer
  threads, alternating occupancies) **share** one semaphore. That is how the
  common case collapses back to exactly tt-metal's SyncHalf.

Budget: there are 8 Tensix semaphores, and CB/unpack sync already uses some
(`ckernel_structs.h`). Running out after sharing is a verifier error, not a
silent serialization. The finer-than-half handoff used by tt-metal's
experimental SDPA (`FPU_SFPU`/`SFPU_FPU` semaphores with `output_granularity`)
is the same rule with a smaller `count` and a larger `depth`, capped by the
SEMPOST max of 15.

---

## 10. How to know the frontend is "solid" before any lowering exists

Build a **reference interpreter** for the UOp graph: numpy, sequential
semantics, but with bit-faithful edges. That means unpack format conversion
(FP8 truncation, subnormal flush, TF32 on MOVA2D with fp32 accumulate),
fidelity phases as mantissa slices, 16-bit vs 32-bit Dst, pack rounding,
SFPU fp32, and lane maps. Plus a grid executor that runs every core's program
and delivers NOC_WRITEs.

This gives you three things:
1. Every kernel can be written and validated against torch **now**, with no
   hardware, sync or lowering.
2. When lowering exists, each lowered kernel is checked against the
   interpreter on the same inputs. The interpreter is the oracle, not ttko.
3. The interpreter is the readable, executable spec of the frontend.
   `tests/compute` already holds most of the bit-level facts it needs
   (`test_sfpu_bits`, fidelity tests, fp8.md, the packer tests).

---

## 11. Changes from current ttk

Kept: `UOp` class, hash-consing, DEFINE/INDEX/AFTER/RANGE/END/SINK,
occupancy = `INDEX(storage, seq)` with `slot = seq % depth`, memory hazard
inference (`memory.py`), loop expansion for verification, linearize.

Changed:
* **Destination-first** src order for all effects and STORE (tinygrad order).
* `FPU_ELW/FPU_MATMUL/FPU_POOL/FPU_DOTPV/MOVE` → one `FPU` op with `FpuArgs.kind`.
* `NOC_WRITE` peer groups → remote/multicast operands on INDEX.
* `RingSpec/StorageSpec` → one `Storage` with `Tile`.
* Runtime RANGE bounds are legal. The verifier expands with the PARAM's
  `hi` bound, plus spot values.
* Frontend drops `acquire/consume/release/handoff/peer/receive/Connection/
  verify_roles`. Their information is now in `depth`, `producer=`, `alias=`
  and the grid trace.

Added: SPECIAL, IF/ENDIF, WHERE/CMP*/bitwise ALU, CAST/BITCAST, VOP, NOC_ATOMIC,
WAIT, CUSTOM; PARAM host location; DEFINE producer srcs. GLOBAL layout is
fixed (row-major, tile-sized interleaved pages), not a parameter.

---

## 12. Order of work

1. Freeze `Ops`, `Storage/Tile`, `*Args` dataclasses (this doc → `uop.py`).
2. Frontend tracer (rewrite of `model.py`) and verifier (keep `memory.py`;
   add grid pairing, format/fidelity legality, Dst-mode lifetimes).
3. Reference interpreter (§10). Port the bit-exactness tests to it.
4. Port every kernel in the inventory and check each against torch on the
   interpreter: SwiGLU, RMSNorm (4 variants), GEMV projections with fused
   epilogues, matmul_peak, RoPE, KV append, GQA attention + merge, argmax,
   embedding, compact→dense. Count CUSTOMs; drive them to zero.
5. Write the Qwen kernels in the frontend against the interpreter.
6. Only then: naive lowering (1:1, no MOP/replay/macro, conservative sync),
   then the five optimizations as graph rewrites, each verified against the
   interpreter.

## 13. Open questions

* **Qwen architecture.** No notes on it exist in the repos. §6.7 assumes the
  Qwen3-Next/3.5-style hybrid (Gated DeltaNet + gated attention). If the model
  is a plain dense transformer, the DSL does not change and the work shrinks to
  QK-norm and partial RoPE on top of the Llama kernels.
* **Memory budget.** 27B parameters at FP8 is about 27 GB before KV/state. A
  p150 has 32 GB and a p100 28 GB. Expect bfp8/bfp4 for some weights, or two
  cards. The frontend supports those formats on UNPACK, but this is the first
  model where the precision choice is forced.
* **L1 state that persists across launches** (within a kernel, see §3.3). Not
  expressible today; all cross-launch state goes through GLOBAL. Most of the
  work is outside the kernel language: a runtime allocator that owns the region
  across launches, command-queue ordering between writer and reader, checks
  that launches in between don't touch it, and the loss of grid-mapping freedom.
  Defer until profiling shows state reads dominate. That is fine for the conv ring
  (60 KB/layer). For the DeltaNet recurrent state (128×128 fp32 per head per
  layer), DRAM vs L1-resident is a large decision. A candidate is
  `GLOBAL(location='l1', cores=...)`: a launch-persistent symmetric L1 region
  that the verifier treats like DRAM.
* **Ethernet** as a GLOBAL space: needed for TP across cards, not designed yet.
* **SFPU on TRISC2** (pack-thread SFPU, used by some LLK kernels): expressible
  with `thread=` hints, but derived sync for it is untested territory.
* **Mixed Dst modes in one kernel**: allowed with disjoint lifetimes; check the
  cost of the mode switch.
