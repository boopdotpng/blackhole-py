# todo

Design detail lives in `tinygrad-integration.md`. This file is order of work and
the one open conceptual question: what happens to `ttk/`.

Standing items not tied to the port:

- understand llama3 end to end
- remove kv cache zero hack

---

## What `ttk/` becomes

The confusion is real and worth naming: `ttk/` today is an **imperative builder
API** — you call `unpack.move_matmul(...)` and it appends instructions. In a
tinygrad port nobody calls that by hand, because the lowerer emits UOps. So who
is `ttk/` for?

The reframe that resolves it:

> **ttk's methods are not ops. They are rewrite rules that happen to be written
> imperatively.**

`unpack.move_matmul` encodes the answer to "how do I get a tile from L1 into
SrcB in matmul layout" — a specific unpack config, specific strides, specific
bank handling. That is not a primitive. It is the *result* of a selection
decision that we currently make by choosing which method to call.

So each `ttk` method splits in two:

- the config computation → the right-hand side of a PatternMatcher rule
- the word emission → an entry in the encoder table

### Where each piece lands

| `ttk/` today | becomes | lives in |
|---|---|---|
| `unpack.py`, `pack.py` `move_*` | isel rules, keyed on (src space → dst space) | `codegen/tensix.py` + `isa/tensix.py` |
| `fpu.py` matmul/binary/reduce | isel rules on `REDUCE(MUL())`, `GroupOp.Binary` | `codegen/tensix.py` |
| `sfpu.py` transcendentals, composites | `extra_matcher` decomposition, or direct isel if single-instruction | `renderer/isa/tensix.py` |
| `cb.py`, `l1.py`, `sync.py`, `shard.py` | allocation + scheduling passes | `codegen/tensix.py` |
| `ops.py` scaler addresses, face offsets | index expressions for `symbolic.py` | `codegen/tensix.py` |
| `mop.py` | macro-op config | `isa/tensix.py` |
| `check.py` | tests | `test/` |

This maps onto `ISARenderer`'s existing slots, which is a decent sign the
decomposition is the natural one:

- **data movement** (unpack/pack) → `isel_matcher` + register classes
- **composite math** (sfpu butterfly, transcendentals) → `extra_matcher`,
  exactly what `x86.py:123-160` does for ops x86 lacks natively
- **resource management** (CBs, L1, sync) → not isel at all; passes in
  `codegen/tensix.py`, partly absorbed by regalloc via `Register._cons`
- **encoding** → the encoder table in `isa/tensix.py`

### The durable artifact is a table, not an API

The taxonomy in `unpack.move() / pack.move() / sfpu.butterfly()` is right — the
axis that matters is **(source register file → destination register file), and
which engine performs the transition.** But the durable form of that knowledge
is a lookup table, not a set of methods:

```
(src space, dst space, dtype, layout) -> (engine, instruction, config)
```

Engine assignment is a lookup on that pair, not a search. That table is what
`codegen/tensix.py` consults, and building it *is* the "clean up ttk" task.
Everything currently in `unpack.py` / `fpu.py` / `pack.py` / `sfpu.py` is that
table, spread across function bodies and fused with encoding.

### Does the directory survive?

Architecturally, no — the contents move to `codegen/tensix.py` and
`isa/tensix.py`.

Practically, keep it through the port **as a test oracle**. If `ttk/` dies and
the lowerer emits wrong instructions, there is nothing to diff against. A thin
hand-written kernel path means every ported kernel has a golden pair. That is a
testing artifact, not architecture — plan to delete it once decode passes
through the new pipeline.

### The only cleanup worth doing now

**Separate selection from encoding.** `fpu.py:matmul` and `unpack.move_matmul`
each do encoding, selection, and resource management in one function body.

Any other tidying — better names, shorter functions, fewer lines — is polish on
code about to be split in half and moved to two different files. The select/
encode split is the one piece of work that survives the port.

It doubles as requirements gathering: it forces every selection decision that is
currently implicit in "which method did I call" to be named explicitly. That
list is the isel matcher's spec.

---

## Order

### Phase 0 — unblock and learn

**1. Move DRAM transfers to the CQ. — done.** Uploads and readbacks are
`Op.DRAM_COPY` records consumed by the resident BRISC/NCRISC engines on `(14,4)`;
`fw/dram.py` and per-transfer kernel launches are gone. The post-tilize path
sustains more than 20 GB/s.

**2. Split ttk's select/encode seam.** Produces the table above.

### Phase 1 — tinygrad plumbing, no codegen

**3. `TTAllocator` + registration.** `_alloc`/`_copyin`/`_copyout` over existing
`pcie.py`, `TTDevice` with no renderer at all. Target:
`Tensor([1,2,3]).to("TT").numpy()` round-trips. Validates registration, the
allocator contract, and the tilize hook before any codegen exists.

Host tilize lives here, in `_copyin`. Keep numpy — it's a strided memcpy on
opaque bytes and tinygrad's CPU backend will not beat it. See
`tinygrad-integration.md` §3.

**4. `HWQueue` subclass** over `cq.py` + `fw/`. Target: launch an existing
hand-written kernel through tinygrad's queue. The CQ protocol now already has
the required `HCQSignal` layout and monotonic put/read issue-ring pointers.

### Phase 2 — codegen bring-up

**5. `TensixRenderer`, RV32 only.** No Tensix words yet. Target: the mask/zero
fill loop (`examples/llama3.py:1438-1494`, ~57 lines of hand-written brisc)
regenerated from UOps and byte-identical.

**6. Tensix words + isel for one kernel.** `decode_projection` is the right
first target: single bias-free `weight @ x`, already sharded over 117 cores, no
softmax.

**7. `codegen/tensix.py`** — CB assignment, stream split, driven by whatever
step 6 needs rather than designed up front.

### Phase 3 — port and extend

**8. Port decode.** Golden reference already exists, which is what makes this
the port rather than the experiment.

### Phase 4 — consolidate

**9. Firmware in UOps.** `fw/cq.py` is already an embedded RV32 DSL with
hand-rolled register allocation (`fw.reg(12)`, twelve registers threaded through
as a tuple). Porting deletes `fw.reg`, `fw.scope`, and all manual liveness
reasoning, because `codegen/late/regalloc.py` does linear-scan with spill/fill.

Last, deliberately. Debugging a miscompiled register allocation on a hung Tensix
core with no printf is a bad time, and the firmware is the thing that would say
what went wrong. Also the firmware is a *fixed* artifact — it doesn't change per
graph, so it earns the least per unit of risk. That flips once we want to
specialize the dispatch loop per graph, which is the actual long-term prize.

**10. Delete `ttk/` and shrink the repo.** (was: "move llama3 into ttk/ and make
it much smaller", "shrink repo lines <6500 ish") — the port is the mechanism.
Don't restructure code that's about to be split across two tinygrad files.

## Deferred

Prefill stays out of the hand-written path. Revisit it only after decode runs
through the new tinygrad pipeline.

---

## Probe, worth doing at any point

Write `decode_projection` as a `Tensor.custom_kernel` (`tensor.py:160`, marked
"alpha and may change") and run it on CPU/CLANG. Tests whether the opt pipeline
can be constrained to 32×32 tiles without forking `codegen/opt/` — which is the
largest open risk in the whole plan, and it's answerable in an afternoon without
touching hardware.

See `test/backend/test_custom_kernel.py` (`custom_gemm`, `simple_qkv_kernel`,
`slice_sum_kernel`) — the single highest-value file to read.
