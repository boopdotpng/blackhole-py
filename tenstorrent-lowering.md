# Direct Tenstorrent lowering from tinygrad UOps

Status: design and migration plan, not an implemented backend.

Code-reading snapshot:

- tinygrad: `149fd91e2` (2026-07-02)
- `blackhole-py-rewrite`: tracked commit `04a6aec2` plus active local work
- historical tinygrad TT branch: `c3e7c0bf7`; its uncommitted renderer prototype is in `stash@{0}`

## Recommendation

Keep tinygrad through **callify**, then route TT graphs to a direct TT lowerer
before generic `get_kernel_graph` / `run_rangeify`:

```text
Tensor methods
  -> shaped tinygrad UOp DAG
  -> transform_to_call                         reuse
       buffers, STORE/AFTER, assignment semantics, PARAM slots
  -> TT pattern matching and partitioning      backend-specific boundary
  -> KernelBuilder / KernelBundle              direct emission through TTK
  -> existing PROGRAM + CALL + AFTER UOps      no new Ops
  -> create_schedule / LINEAR / JIT / runtime  reuse
```

The exact current seam is
[`lower_sink_to_linear`](../tinygrad/tinygrad/schedule/__init__.py#L113). It currently
calls `create_schedule(get_kernel_graph(function))` unconditionally at line 120.
The smallest clean architecture change is a generic, optional backend graph
lowerer there. The default remains `get_kernel_graph`; TT supplies a pure
`lower_tt_graph` callable.

That dispatch must not select a backend from `function.device` alone. A callified
`SINK` can contain several jointly realized outputs and cross-device copies, and
`UOp.device` returns the first device it finds. The hook must inspect top-level
materialization roots. The first TT version can support TT compute plus ordinary
ingress/egress `COPY` roots and reject unrelated mixed-device compute with a
diagnostic. A later generic dispatcher can partition roots by backend, lower each
partition, then merge their ordinary call graphs before `create_schedule`.

The TT lowerer should pattern-match shaped UOps and immediately call existing
TTK/`KernelBuilder` helpers. It may keep short-lived Python records or maps for
logical shape, padded shape, tile access, core spans, and live CB slots. Those
are compiler analysis state, not a second graph IR.

Explicit non-goals:

- no TTIR;
- no new TT-specific tinygrad Ops;
- no `Tensor` subclass or overrides of `Tensor.sum`, `Tensor.matmul`, etc.;
- no BEAM;
- no attempt to force a five-RISC Blackhole bundle through GPU scalar codegen;
- no scattered `if device == "TT"` branches throughout generic matchers.

## Why this boundary

### Do not fork before callify

Tensor methods do mostly append shaped UOps. `Tensor._apply_uop` constructs one
new UOp and wraps it in a Tensor
([`tensor.py:108-117`](../tinygrad/tinygrad/tensor.py#L108)); reductions are still
`REDUCE(op, axes)` ([`uop/ops.py:561-563`](../tinygrad/tinygrad/uop/ops.py#L561)), and
movement remains `RESHAPE`, `PERMUTE`, `EXPAND`, `PAD`, `SHRINK`, or `FLIP`
([`uop/ops.py:704-716`](../tinygrad/tinygrad/uop/ops.py#L704)).

It is not literally an untouched append-only graph:

- UOps are hash-consed;
- ALU construction performs broadcasting;
- no-op reductions and movements can be elided;
- movement shape arguments receive symbolic simplification.

There is still no graph-wide performance optimization before realization.

Forking on this raw graph would preserve maximum intent, but it would also make
the TT backend reimplement tinygrad's realization and mutation contract.
[`transform_to_call`](../tinygrad/tinygrad/callify.py#L205) already does useful,
backend-independent work:

- identifies materialization points;
- converts `CONTIGUOUS` to explicit output buffers and `STORE`/`AFTER` effects;
- preserves assign and write-after-read ordering information;
- turns concrete buffers into cache-normalized `PARAM`s;
- returns the map used to update every affected live Tensor to its realized
  buffer identity.

That is worth keeping. The TT lowerer should consume the callified function's
inner shaped `SINK`, not each user's raw `Tensor.uop`.

### Do not wait for a Renderer hook

`Renderer.pre_matcher` sounds early, but it runs only at
[`codegen/__init__.py:126`](../tinygrad/tinygrad/codegen/__init__.py#L126). By then
tinygrad has already:

- made generic fusion/materialization decisions;
- replaced movement ops with scalar ranges and index expressions;
- run GPU loop scheduling (unless specially disabled);
- expanded vector/unroll ranges;
- lowered reductions toward scalar register loops;
- introduced GPU launch dimensions, loads, and backend vector legalization.

`Renderer.extra_matcher` is even later. These hooks are suitable for final
instruction legalization, not tile layout, core distribution, CB allocation,
or Blackhole fusion.

The historical stashed TT renderer demonstrates the failure mode: it discovers
which `PARAM` a `LOAD` uses, drops the actual index expression, and gives every
input the same `offset + tile` reader. That can only implement dense,
identically laid-out elementwise inputs. It cannot implement broadcast,
permute, reshape across tile boundaries, pad, shrink, gather, or batch indexing.

### Why not use generic rangeify and intercept before `to_program`?

This is a reasonable narrow bring-up experiment. Current rangeified kernel ASTs
still contain `REDUCE`, and tinygrad's own tensor-core matcher recognizes matmul
there. A one-tile elementwise prototype can therefore intercept `CALL(SINK)` in
`pm_compile` before `to_program`.

It is not the recommended permanent boundary because the requirements in this
project are scheduling requirements:

- physical 32x32 tile layout and partial-tile validity;
- logical versus padded shapes;
- tile-aware movement/indexing;
- different materialization and fusion decisions;
- aggregate input/output and CB budgets;
- distributing tile spans over cores rather than GPU work-items.

Generic rangeify has already made policy choices for those areas. Starting just
after callify gives TT control without discarding callify's semantic work.

## The complete current lowering pipeline

This section inventories the transforming matchers and non-matcher optimization
algorithms on the normal realization path. "Reuse" below means reuse on the TT
path, not merely that the pass continues to exist for other devices.

Legend:

- **yes**: use essentially unchanged;
- **part**: reuse rules or algorithms selectively under TT policy;
- **no**: bypass on TT.

### 1. Tensor construction and callify

| Order | Matcher / algorithm | What it does | TT |
|---:|---|---|:---:|
| 0 | UOp construction helpers | Hash-consing, broadcasting, trivial no-op removal, shape-argument simplification. No graph-wide optimizer. | yes |
| 1 | `add_tags` | Numbers materialization/assignment points and builds the original-to-buffer map. | yes |
| 2 | `pm_early_transform_tensor_graph` | Handles precompiled functions, tuple folding, allocatable contiguous views, tags to `CONTIGUOUS`, `CONTIGUOUS` to buffer + store + after, and detach cleanup. | yes* |
| 3 | `pm_finalize_call` | Collects output `AFTER`/copy effects and finalizes the live-Tensor buffer map. | yes |
| 4 | `pm_replace_buf` | Replaces `BUFFER`, `SLICE`, and `BIND` leaves with cache-normalized `PARAM`s and wraps the body in a call. | yes |

The call order is in
[`callify.py:204-223`](../tinygrad/tinygrad/callify.py#L204). Nested/conditional
matchers used here are `multi_pm` for multi-device contiguous views and
`pm_mops + symbolic` inside `contiguous_view_offset`.

`*` The structure is reusable, but its allocation operation needs a narrow
layout hook if TT buffers are physically tiled; see [Layout and allocation](#layout-and-allocation).

### 2. Generic scheduling and rangeify

The default scheduler starts at
[`get_kernel_graph`](../tinygrad/tinygrad/schedule/rangeify.py#L598). TT should replace
this orchestration, while selectively importing safe components.

| Order | Matcher / algorithm | What it does | TT |
|---:|---|---|:---:|
| 1 | `multi_pm` + `replace_allreduce` | Resolves `MULTI`, shard-local ops, copies, movement, and all-reduce. | part |
| 2 | `pm_fold_moved_after` | Optional OpenPilot-only movement/assignment rewrite. | no |
| 3a | `pm_syntactic_sugar` | Flattens nested pointer indexes and pushes index through elementwise nodes. | part |
| 3b | `pm_mops` | Pushes movement through indexes/afters and lowers `SHAPED_WMMA`. | part; exclude WMMA policy |
| 3c | `earliest_rewrites` | Function inlining, tuple folding, all-reduce expansion, large-reduction splitting, detach/copy/store/empty cleanup. | part |
| 3d | `mop_cleanup` | Merges adjacent reshapes; composed into `earliest_rewrites`. | yes |
| 3e | `pm_gather_params` | Helper used while resolving a function call. | yes |
| 4a | `pm_generate_realize_map` | Marks explicit realization points before range propagation. | part |
| 4b | `run_rangeify` reverse DAG algorithm | Builds consumer/range maps and chooses partial materializations. | no as policy |
| 4c | `pm_apply_rangeify` | Converts reductions to explicit ranges, PAD to validity `WHERE`, inserts `STAGE`/`INDEX`, removes shaped movement. | no |
| 4d | `pm_fix_deviceless` | Gives a materialized deviceless value the sink's device. | part |
| 5a | `symbolic` | General algebraic and index simplification. | yes |
| 5b | `pm_reduce_simplify` | Collapses/simplifies reductions (`pm_reduce_unparented` and reduction-collapse rules). | part |
| 5c | `pm_const_buffer_folding` | Removes constant/no-op stages and dead axes; includes `pm_mops`. | part |
| 5d | `pm_remove_bufferize` | Uses generic/GPU cost rules to remove stages and fuse computation. | no |
| 6 | `pm_limit_bufs` | Inserts stages if an elementwise root has too many input-like buffers, reserving one output. | no; replace |
| 7a | `pm_add_buffers` | Converts global `STAGE`s to output buffers/stores/afters; includes `pm_flatten_bufferize` and `to_bufferview`. | no orchestration |
| 7b | `pm_add_range_tags` | Tags ranges before kernel splitting. | no |
| 8a | `split_kernels` | Splits each store/end into a scheduled call. | no; TT emits calls |
| 8b | `to_define_global` | Converts buffer leaves to kernel `PARAM`s, resolves binds/afters, and renumbers ranges. | part |
| 8c | `pm_flatten_range` | Merges compatible nested ranges. | part |
| 8d | `rangeify_codegen` | Removes contiguity/no-ops and performs local-buffer index/load cleanup. | no |

Important non-matcher decisions:

- `run_rangeify` is also the current fusion/materialization algorithm. In
  [`rangeify.py:244-311`](../tinygrad/tinygrad/schedule/rangeify.py#L244), its cost
  model has assumptions such as refusing a removable stage after more than
  three accessed buffers and special scalar-range handling for reductions.
  These are not TT fusion rules.
- `split_reduceop` can turn a large reduction into two kernels based on GPU
  occupancy heuristics. Do not run it before TT gets to choose a tile reduction.
- `pm_limit_bufs` counts input-like buffers and subtracts one presumed output
  ([`rangeify.py:377-399`](../tinygrad/tinygrad/schedule/rangeify.py#L377)). It does
  not enforce `unique inputs + unique outputs <= N` for a multi-output bundle.

Some names are hidden inside the composed entries above rather than being
separate pipeline stages. `pm_remove_bufferize` uses `pm_gate_substitute` during
safe index substitution. Movement analysis uses `symbolic`,
`pm_simplify_valid`, and `pm_drop_and_clauses`; `symbolic` itself composes
`propagate_invalid`, `symbolic_simple`, `commutative`, and its algebraic rules.
Later, `pm_load_collapse` delegates to `pm_reduce_load_collapse`, which includes
`pm_reduce_collapse` and `pm_reduce_unparented`. These helpers are useful rule
sources, but running their parent orchestration would still commit TT to scalar
range/index policy.

After a backend produces calls, the following pieces are valuable and should be
kept:

| Matcher / algorithm | What it does | TT |
|---|---|:---:|
| `create_schedule` | Builds RAW/WAR dependencies and topologically orders calls into `LINEAR`. | yes |
| `pm_schedule` | Replaces a callified shaped `SINK` with its scheduled `LINEAR`. This is where backend dispatch belongs. | yes, with hook |
| `pm_post_sched_cache` | Maps cached `PARAM`s back to actual buffers and creates internal buffers. | yes |
| `pm_resolve_linear_call` | Resolves a cached `CALL(LINEAR, ...)`; composed with `pm_flatten_linear`. | yes |
| `memory_plan_rewrite` | Lifetime analysis and TLSF arena suballocation through buffer `SLICE`s. | later |

`memory_plan_rewrite` requires allocator `_offset` support
([`schedule/memory.py:13-16`](../tinygrad/tinygrad/schedule/memory.py#L13)). Do not use
it for TT until physical sizes and tile-aligned subviews are correct.

### 3. Engine compile and execution rewrites

These operate on the scheduled `LINEAR` in
[`engine/realize.py:225-281`](../tinygrad/tinygrad/engine/realize.py#L225).

| Order | Matcher | What it does | TT |
|---:|---|---|:---:|
| 1 | `pm_validate` + `pm_flatten_linear` | Optional CPU shadow validation; its pattern matches `CALL(SINK)`, not a completed `CALL(PROGRAM)`. | no for direct PROGRAM |
| 2 | `pm_beam` | Writes the global BEAM value into each kernel's `KernelInfo`. | no |
| 3 | `pm_compile` | Converts `CALL(SINK/PROGRAM)` to `CALL(PROGRAM)` through `to_program`. | yes for already-complete PROGRAM |
| 4 | optional HCQ2 compiler/linker | GPU command-queue path. | no |
| 5 | `pm_optimize_local_size` | Benchmarks GPU workgroup sizes up to 1024 threads. | no |
| 6 | `pm_exec` | Dispatches copy, slice, compiled program, graph, and other runtime calls. | yes |

The TT graph lowerer should return an already-complete `PROGRAM`, so
`pm_compile`/`to_program` leaves it alone. The normal program cache, runtime
cache, stats, JIT capture, and `pm_exec` path remain usable.

`VALIDATE_WITH_CPU` does not validate this shortcut because `pm_validate` only
matches an uncompiled `SINK`. Initially, CPU comparison belongs in the TT test
harness. Extending validation to opaque completed programs would require a
separate semantic reference or validator hook; it should not be implied by
reusing `pm_exec`.

### 4. Per-kernel GPU codegen

For completeness, this is the exact main pass order in
[`full_rewrite_to_sink`](../tinygrad/tinygrad/codegen/__init__.py#L54). A directly
constructed TT `PROGRAM` bypasses all of it.

| Order | Matcher / algorithm | Purpose | TT |
|---:|---|---|:---:|
| 1 | `pm_mops + pm_syntactic_sugar + pm_store_ranges` | Early movement/index/store normalization. | part, imported selectively before direct emission |
| 2 | `pm_load_collapse` | Collapse tensor-indexed loads/reductions. | no |
| 3 | `pm_split_ranges + pm_flatten_range` | Split/merge loop ranges. | no |
| 4 | `sym + pm_flatten_range` | Initial symbolic simplification. | symbolic only |
| 5 | `pm_flatten_range + pm_simplify_ranges` | GPU loop-schedule simplification. | no |
| 6 | `apply_opts` | Explicit opts, BEAM, or hand-coded GPU heuristics. | no |
| 7 | `sym + pm_move_where_on_load + pm_flatten_range` | Post-opt index cleanup. | symbolic only |
| 8 | `sym + pm_pre_expander + pm_group_for_reduce + expander` | Turn upcast/unroll/group ranges into vector/local work. | no |
| 9 | `pm_add_buffers_local + rangeify_codegen` | Materialize local/shared staging. | no |
| 10 | `pm_reduce + gep_pushing` | Lower `REDUCE` to scalar/vector accumulator loops. | no |
| 11 | `pm_add_gpudims` | Convert ranges to GPU global/local launch IDs. | no |
| 12 | `pm_add_loads + pm_remove_invalid` | Insert scalar pointer loads and remove invalid paths. | no |
| 13 | `sym + devectorize_alu + devectorize_buf_and_index + load_store_folding` | Legalize backend vector widths and fold memory ops. | no |
| 14 | `pm_render` | Convert old vector `GEP`/`STACK` representation. | no |
| 15 | `pm_remove_vec_dtypes + pm_clean_up_group_sink` | Remove vector dtypes / rewrite GEP to index. | no |
| 16 | `indexing_simplify` | Simplify scalar load/store indices. | part, only for scalar data-mover code if useful |
| 17 | `memory_coalesing` | GPU vector/coalesced memory policy. | no |
| 18 | `pm_simplify_add_image` | Image-load/store optimization. | no |
| 19 | `sym` | Extra symbolic cleanup. | yes, in TT analysis where applicable |
| 20 | `pm_lower_index_dtype + indexing_simplify` | Choose supported integer widths for indices. | part, after TT addressing is chosen |
| 21 | `symbolic` | Final algebraic simplification. | yes |
| 22 | renderer `pre_matcher` | Target-specific late legalization. | no as TT boundary |
| 23 | `symbolic_simple + get_simplifying_rewrite_patterns` | Early capability-driven op decomposition. | part |
| 24 | `pm_dtype_decomps` (`pm_long_decomp`, `pm_float_decomp`) | Emulate unsupported dtypes. | part |
| 25 | late op + transcendental decomposition | Shift/div/mod, compare, MULACC, reciprocal, transcendental lowering based on supported ops. | part |
| 26 | `pm_move_gates_from_index` | Move scalar validity gates to loads/stores. | no; TT uses tile/lane validity |
| 27 | decomposition + renderer `extra_matcher` + `pm_split_ends + pm_no_weakints` | Final target rewrite. | no orchestration |
| 28 | `pm_add_control_flow` | Build imperative scalar CFG. | no |
| 29 | `pm_number_params` | Assign slots to unnumbered scalar params. | part |

`apply_opts` deserves special emphasis. `beam=0` does **not** mean no GPU
optimization: absent `NOOPT`, it invokes `hand_coded_optimizations`
([`postrange.py:334-351`](../tinygrad/tinygrad/codegen/opt/postrange.py#L334)). Those
heuristics choose tensor cores, group reductions, locals/shared memory,
upcasts, unroll, and threads. TT must bypass the entire policy, not merely set
`BEAM=0`.

### 5. Linearization and renderer-specific matchers

The remaining normal stages are:

1. optional ISA `pre_isel_matcher` and `isel_matcher`;
2. `linearize` plus `pm_linearize_cleanups` (including gated store to
   `IF/STORE/ENDIF`);
3. for ISA renderers, `pre_regalloc_matcher`, `pm_regalloc_rewrite`, and
   `post_regalloc_matcher`;
4. `pm_to_program`, which advances `PROGRAM` through linearize, estimate,
   render/assemble, and compile;
5. one selected renderer's own rules (`base_rewrite`, PTX, WGSL, LLVM IR, NIR,
   x86 instruction selection, etc.). These renderer families are alternatives,
   not sequential passes.

TT bypasses this scalar pipeline because `KernelBuilder` has already produced
the five role images.

Type/specification matchers such as `spec_tensor`, `spec_program`, and
`spec_full` verify graphs when `SPEC` is enabled; they do not optimize them.
They should remain enabled where the direct `PROGRAM` form satisfies the normal
program spec.

## What tinygrad the TT path should reuse

### Reuse unchanged

- Tensor API and autograd;
- shaped UOps, dtype promotion, logical shape inference, and metadata;
- `UPat`, `PatternMatcher`, `graph_rewrite`, and rewrite tracing/visualization;
- callify's buffer, `STORE`, `AFTER`, assignment, and `PARAM` normalization;
- `create_schedule` RAW/WAR dependency ordering;
- cached-call parameter rebinding and `LINEAR` flattening;
- existing `PROGRAM`, `CALL`, `LINEAR`, `SOURCE`, `BINARY`, and `ProgramInfo`;
- runtime/program caching, stats, JIT capture, copies, and execution dispatch.

Tinygrad already tests direct construction of a complete `PROGRAM` in
[`test_custom_kernel.py:423-437`](../tinygrad/test/backend/test_custom_kernel.py#L423)
and [`test_function.py:571-585`](../tinygrad/test/unit/test_function.py#L571). The
valid progressive four-source form (`SINK`, `LINEAR`, `SOURCE`, `BINARY`) is in
[`uop/spec.py:176-183`](../tinygrad/tinygrad/uop/spec.py#L176). This is the key reason
no new TT program Op is needed.

### Reuse selectively

- `symbolic`, `symbolic_simple`, validity simplification, and constant folding;
- safe function/tuple/detach/copy/store normalization from
  `earliest_rewrites`, excluding GPU reduction splitting and shaped-WMMA policy;
- movement semantics in
  [`apply_movement_op`](../tinygrad/tinygrad/schedule/indexing.py#L132): shrink offsets,
  permute reorder, flip, expand-to-zero coordinate, pad validity, and reshape
  flatten/unflatten math;
- reduction identity semantics;
- multi-device semantics if/when a TT device is exposed as tinygrad multi-device
  rather than as cores within one device;
- generic memory planning only after TT has tile-aligned subviews.

### Replace or bypass

- generic rangeify's fusion/materialization policy;
- `split_reduceop`;
- `pm_limit_bufs` as the TT resource checker;
- all `OptOps` scheduling, hand heuristics, and BEAM;
- GPU global/local/upcast/unroll/thread concepts;
- scalar reduction lowering, load insertion, devectorization, coalescing, and
  renderer source generation;
- GPU local-size search.

## Direct TTK lowering design

### Output shape

The backend should construct the existing complete program form directly:

```text
PROGRAM(
  SINK(original shaped UOps used for identity/debug, arg=KernelInfo(...)),
  LINEAR(debug/topological summary),
  SOURCE(human-readable TTK lowering summary),
  BINARY(serialized compiled KernelBundle),
  arg=ProgramInfo(...),
)
```

Build one explicit ABI table and derive the call's non-`BIND` argument order,
`ProgramInfo.globals`, `ins`, `outs`, and the bundle's `Param` slots from it.
`globals` selects and orders call arguments for the runtime. `ins` and `outs`
describe read/write call-argument slots for JIT mutation tracking, profiling,
and graph dependencies; an in-place tensor belongs to both sets. Keep buffer
slots dense and in call order initially (`globals == range(N)`), because current
paths assume that common case when combining selected runtime buffers with
input/output metadata. Support sparse or reordered globals only with explicit
eager, JIT, profiling, and graph-runner tests.

`global_size`/`local_size` can remain inert `(1,1,1)` values; the serialized TT
program owns the core set and per-core work. `aux` may hold a small hashable ABI
descriptor (layouts, parameter contracts, core geometry), but not another
executable graph.

The inner `SINK` must retain a `KernelInfo`, including `estimates` when they are
known. Runtime accounting reads `PROGRAM.src[0].arg.estimates`; an unannotated
debug sink is therefore not a valid completed-program shortcut.

The TT runtime unpickles/loads the bundle, binds actual tinygrad buffers to the
bundle's fixed `Param` slots, submits its CQ commands, and reports completion
through the ordinary runtime callable.

### Matcher and emitter organization

A suggested backend-only layout is:

```text
tinygrad/codegen/tt/
  lower.py       shaped-SINK partitioning and direct PROGRAM construction
  patterns.py    ordered UPat recognizers
  layout.py      ephemeral shape/access analysis
  emit.py        UOp pattern -> TTK/KernelBuilder calls

tinygrad/runtime/ops_tt.py
tinygrad/runtime/support/tt/
  ...ported blackhole-py-rewrite runtime, TTK, assembler, firmware...
```

Pattern priority should go from most specific to most general:

1. explicit copy/layout conversion;
2. matmul plus supported epilogue;
3. specialized reductions;
4. fused motifs proven useful (RMSNorm, softmax, attention pieces);
5. generic same-tile-domain elementwise DAG;
6. a hard, diagnostic unsupported-pattern failure.

Callbacks should produce a complete program/call, not replace matched math with
a TT-specific semantic UOp. A conceptual callback is:

```python
def lower_store(ctx, store, output, value):
  layout = analyze_layout_and_access(value, output)
  fusion = choose_fused_subgraph(value, layout, ctx.uses)
  bundle = emit_with_kernelbuilder(fusion, layout, ctx.params)
  program = make_tinygrad_program(bundle, fusion, ctx.params)
  return output.after(program.call(*ctx.params))
```

In practice the partitioner must operate with the consumer map, so shared nodes
are emitted once or materialized deliberately. The important property is that
the only persistent graphs are the input tinygrad graph and the output ordinary
tinygrad call graph.

### Synchronization without TTIR

No intermediate IR is required, but synchronization cannot be ad hoc. Reusable
emitter functions should own complete role protocols:

- reader: reserve/fill/push CB pages;
- unpack: wait/acquire/unpack/release;
- math/SFPU: configure, compute, and publish Dst readiness;
- pack: acquire/pack/publish;
- writer: wait/drain/pop;
- phase and NoC completion rules.

TTK's stateful engine objects and scoped register allocator are the right place
to make these sequences composable. A lowering context still must track live
CBs, Dst ownership, and role progress so it does not concatenate two individually
valid sequences into a deadlock. That state is normal code-generation state,
not a new programming model.

## Layout and allocation

### Required metadata

For each external or materialized value, keep backend-local metadata keyed by
the shaped UOp or parameter slot:

```python
@dataclass(frozen=True)
class TTLayout:
  logical_shape: tuple[int, ...]
  padded_shape: tuple[int, ...]
  tile_grid: tuple[int, ...]
  layout: Literal["row_major", "tile"]
  dtype: DType
  valid_rows: int
  valid_cols: int
```

The first backend should require every layout-affecting extent to be concrete at
lowering time and report the first symbolic dimension it cannot place. Runtime
scalar variables whose bounds do not change allocation or tile partitioning are
a separate, smaller feature. Full symbolic shapes require `sint` extents,
max/padded allocation bounds, runtime valid extents, and all bound variables in
the bundle ABI and cache key; do not silently specialize them without keying the
specialization. This staged policy keeps the initial `TTLayout` intentionally
integer-valued while leaving a correct path for TinyJit dynamic shapes.

This maps directly to the existing `blackhole-py-rewrite.program.Buffer`, which
already distinguishes `shape`, `padded_shape`, and `layout`. It does not need to
be embedded in a new tinygrad Op.

Only the two selected tile axes are rounded. Outer/batch dimensions are tile
groups, not dimensions independently padded to 32. For rank zero/one, treat the
logical matrix extent as `(1,1)` / `(1,N)` for tile planning.

Examples:

| Logical shape | Padded matrix shape | Tile grid |
|---|---|---|
| `(32, 32)` | `(32, 32)` | `(1, 1)` |
| `(64, 64)` | `(64, 64)` | `(2, 2)` |
| `(33, 65)` | `(64, 96)` | `(2, 3)` |
| `(1, 2048)` | `(32, 2048)` | `(1, 64)` |

Do not round total flattened bytes to the next 1024 elements. For example,
`33*65 = 2145` rounded to three flat tiles is 3072 elements, but the correct
2-D tiled storage is `64*96 = 6144` elements. Likewise, independently
face-transforming 1024-element chunks of a 64x64 row-major buffer does not
extract the correct four logical tiles; grid extraction must precede face
swizzling.

### Allocation hook

Callify currently uses `u.empty_like()` when turning a realization into an
output buffer ([`callify.py:44-52`](../tinygrad/tinygrad/callify.py#L44)), and the
generic `Buffer` allocator receives only a flat element count. By then an
allocator cannot infer the required 2-D padded shape.

There are two clean stages:

1. **Initial correctness path:** keep global tinygrad buffers row-major and
   logical-sized. Generated readers tilize and pad into L1 CBs; writers crop and
   untilize. This avoids a tinygrad allocation change while the direct emitter
   is being proven.
2. **Persistent tiled-storage path:** add one generic optional
   layout-aware-buffer factory used by `Tensor.empty`/`UOp.empty_like` and
   callify allocation. TT returns an existing padded `BUFFER` reshaped to the
   physical shape and `SHRINK`ed to the logical view. Other devices retain the
   current flat allocation.

The second item should be a generic backend capability, not a TT conditional in
callify. It is the only likely core hook besides the scheduler dispatch. No new
Op is required.

Padding contents are not globally zero by definition. Invalid lanes use the
consumer's identity:

- sum: `0`;
- product: `1`;
- max: dtype minimum / `-inf`;
- min (currently expressed through inverse + max): the corresponding transformed
  identity;
- mean: sum with the logical, not padded, denominator.

Output stores crop to logical shape. Elementwise invalid output lanes can be
don't-care if they are never exposed, but reduction inputs must be masked with
the correct identity.

## Indexing and movement

Do not lower tinygrad scalar `INDEX` arithmetic and then translate each scalar
instruction. Instead, compose movement semantics over logical coordinates and
classify each buffer access:

1. **tile-affine:** contiguous tiled, tile-aligned shrink, supported transpose,
   or broadcast with zero tile stride; generate direct tile addressing;
2. **lane-masked:** partial edge pad/shrink; generate a tile plus a row/column
   validity mask;
3. **requires materialization:** reshape/permute that crosses the physical tile
   contract, non-affine gather, or unsupported overlap; emit a layout kernel or
   split the program;
4. **specialized gather/scatter:** embedding and KV-cache accesses, handled by a
   dedicated data-movement lowerer.

Reuse the formulas from `apply_movement_op`, but run them as analysis while the
shaped movement nodes still exist. Simplify the resulting coordinates with
tinygrad's symbolic matcher. The final hot loop should use TT tile/page cursors,
not repeated general integer div/mod. Initialize a bank/tile cursor once and
increment it across sequential pages.

`EXPAND` on a size-one dimension becomes coordinate/stride zero. This is the
critical batch-one behavior that the stashed renderer loses when it blindly uses
`input_offset + tile` for every operand.

## Core distribution

For ordinary elementwise and tile-local kernels:

```text
total_tiles = product(outer groups) * tile_rows * tile_cols
core c owns [floor(c*T/C), floor((c+1)*T/C))
```

Every active core can use byte-identical role kernels if its start/count comes
from a per-core scalar table or hardware logical coordinate. Tail cores simply
receive a smaller count.

A logical singleton does not create 32 independent pieces of work. For
`(1,2048)`, there is one padded tile row and 64 tile columns. Distribute those
64 tiles (or output column blocks) across useful cores and mask/crop the 31
invalid rows. Higher-rank singleton batch dimensions select or broadcast tile
groups; they do not get padded independently.

Matmul uses a separate planner. For decode `[1,K] @ [K,N]`, `Mt=1`; distribute
`N` tile blocks and K work according to the dedicated Tensix/multicast strategy.
Do not map tinygrad `global_size`/`local_size` directly onto cores.

`blackhole-py-rewrite` currently compiles per-core/per-role and can multicast
byte-identical images, but its fixed runtime parameter table contains shared
DRAM addresses, not general per-core scalar arguments. Add a small fixed
per-core argument table in the rewrite, or derive spans from logical coordinates.
Compiling offsets into every image is correct but defeats image sharing. The
fixed per-core table is the clean general solution and is a low-level runtime
change, not a tinygrad hack.

## Fusion and resource rules

Use deterministic greedy fusion; do not search.

A candidate fused bundle is legal only when all of these hold:

- all accesses have compatible tile mappings or an explicitly emitted
  conversion;
- partial-tile validity and reduction identities are compatible;
- external `unique input buffers + unique output targets` is within the chosen
  ABI limit;
- all simultaneously live input, output, spill, constant, and scratch CBs fit;
- CB backing pages fit L1;
- Dst slots and accumulation format fit;
- role kernel images fit their fixed text partitions;
- the same core topology/work partition can execute the fused region;
- TTK can establish a valid engine/synchronization transition.

Elementwise producer/consumer chains with the same tile domain should fuse by
default. Reduction or matmul epilogues should fuse while their output is still
available to the relevant math/SFPU/pack sequence. A reshape that is only a
logical view is free; a physical retilize is a boundary unless emitted inside
the same bundle.

Treat "32 inputs + outputs" as one centralized initial ABI constant and verify
it after building a candidate. Do not reuse `pm_limit_bufs`: it assumes one
output and ignores compiler-created CBs. Also track the CB namespace separately.
The legacy Python stack uses 32 CB identifiers, while current Blackhole tt-metal
headers expose 64; this checkout's rewrite has not yet made that distinction a
stable ABI. The compiler should therefore have separately named limits such as:

```text
MAX_EXTERNAL_TENSOR_PORTS = 32   # requested first compiler contract
MAX_LIVE_CBS = <rewrite ABI, verified independently>
```

Practical compute fan-in can be smaller than either limit because unpack/math
operate through SrcA/SrcB and Dst. A resource verifier should report which
limit forced a split.

## Minimal tinygrad change budget

### Required

1. Add TT to normal device registration/discovery.
2. Add one generic optional graph-lowering/partition hook at
   `lower_sink_to_linear`; default to `get_kernel_graph`.
3. Provide a tiny inert `TTRenderer` (or equivalent base-renderer configuration)
   because current `Compiled`/`pm_compile` plumbing still asks every device for a
   renderer even when a four-source `PROGRAM` is already complete. It must not
   lower scalar UOps or emit TT kernels.
4. Implement `runtime/ops_tt.py` and the TT runtime callable for serialized
   bundles.

### Required only for persistent tiled global buffers

5. Add one generic layout-aware buffer factory/allocation hook. It must receive
   logical shape and dtype before they are flattened and return a logical view of
   the physical allocation.
6. Later, add tile-aligned allocator `_offset` support before enabling the
   generic memory planner.

### Not required

- changes to Tensor math methods;
- new Ops or dtype kinds;
- modifications to generic rangeify/codegen rules;
- TT cases in BEAM, hand-coded GPU heuristics, gpudims, devectorizer, or a scalar
  code-emitting renderer (the inert device-plumbing shim above is not a lowering
  boundary);
- a custom execution Op.

If a local spike uses a single `if TT` at the dispatch seam, keep it confined
there and replace it with the generic hook before broadening operation coverage.

## What to salvage from the historical backend

The `blackhole-backend` branch is 1,295 current-master commits behind and also
has one divergent TT commit. It is not a branch to merge wholesale. Current
incompatibilities include removed `CompilerSet`, `ParamArg` replacing integer
PARAM args, removed `VCONST`, and Target-based renderer construction.

Salvage concepts/code selectively:

- device/DRAM/firmware/CQ work that is not duplicated by
  `blackhole-py-rewrite`;
- compiler/cache packaging patterns after fixing cache keys to include all
  ckernel/layout configuration;
- runtime binding of tinygrad buffers to TT program parameters;
- elementwise SFPU emission cases as references for direct TTK emitters.

Do not salvage as architecture:

- the late `TTRenderer` boundary;
- flat byte rounding as tile padding;
- `_face_transform` without a grid transform;
- index-blind `offset + tile` readers;
- hardcoded 118-core launch selection;
- the prototype's one-output/at-most-eight-input restrictions as hardware
  contracts.

The active `blackhole-py-rewrite` worktree should be the low-level source of
truth. Its tracked `todo.md` still lists CB synchronization, tensor address
generation, reusable math templates, and several layout paths, while the local
worktree already contains newer SFPU/tests work. Re-audit those low-level gaps
when integration starts rather than freezing this document's snapshot as truth.

The abandoned `blackhole-py/TTIR.md` should not drive the compiler architecture.
Some hardware observations in it remain useful, but this plan deliberately
replaces its intermediate programming model with direct UOp-to-TTK emission.

## Implementation plan

### Phase 0: lock contracts and probes

- Decide the first global-buffer policy: row-major with on-device tilize, or
  persistent tiled allocations.
- Confirm tile axes for rank 0/1/N and the physical ordering of outer groups.
- Confirm the initial external-port and live-CB limits independently.
- Add a per-core scalar argument mechanism or choose coordinate-derived spans.
- Check in shaped UOp dumps for elementwise, broadcast, reduction, matmul,
  assignment/KV-cache update, and one Llama decode block.

### Phase 1: runtime and direct PROGRAM proof

- Port the low-level TT runtime to current tinygrad APIs. Do not port the
  historical scalar renderer; add only the inert renderer shim current device
  plumbing requires.
- Construct a complete `PROGRAM` manually in a test, serialize one
  `KernelBundle`, bind buffers, and execute a single aligned tile.
- Test cache identity, JIT capture, copyin/copyout, repeated binding, and errors.
- Test dense ABI slot derivation, reordered/sparse-slot rejection, and an in-place
  tensor marked as both input and output.

### Phase 2: callified graph hook and aligned elementwise

- Add the generic schedule graph-lowerer hook.
- Reject mixed-device compute roots explicitly at first while preserving normal
  TT ingress/egress copies; add a jointly realized CPU/TT diagnostic test.
- Reuse callify, match a one-output aligned elementwise DAG, and emit TTK calls
  directly.
- Return ordinary `CALL`/`AFTER` graph nodes and let `create_schedule` order them.
- Support scalar constants and same-shape unary/binary chains before broadcast.

### Phase 3: shape, padding, and addressing correctness

- Implement logical/padded metadata and correct grid tilize/untilize.
- Add edge masks and logical output cropping.
- Add stride-zero broadcast, then tile-aligned shrink/permute.
- Classify unsupported reshape/gather as an explicit materialization or error.
- Only then add faster DRAM cursor/address generation.

### Phase 4: reductions

- Implement sum and max with operation-specific invalid-lane identities.
- Add multi-tile reductions, partial final tiles, and logical mean denominator.
- Add RMSNorm only after the primitive reduction path is correct and measured.

### Phase 5: fusion and resource splitting

- Add consumer/liveness analysis and deterministic elementwise fusion.
- Verify external endpoints, live CBs, L1, Dst, role text, and topology after
  every fusion.
- Materialize deterministic cuts and ensure `create_schedule` preserves hazards.
- Add multi-output only after endpoint and pack/write lifetimes are explicit.

### Phase 6: matmul and LLM motifs

- Match matmul structurally on the shaped `REDUCE(ADD, MUL(...))` graph.
- Use a dedicated KernelBuilder matmul path; do not route it through the generic
  elementwise walker or tinygrad WMMA.
- Add `[1,K] @ [K,N]` decode distribution first, then general prefill GEMM.
- Fuse supported epilogues, then add softmax, attention pieces, KV-cache
  gather/scatter, RoPE, and whole-block motifs only where they provide a clear
  program-level win.

## Verification matrix

At minimum, test these shapes through copy/layout round-trip and each applicable
operation:

```text
(32,32), (32,64), (64,32), (64,64)
(33,33), (1,33), (33,1), (33,65), (1,2048)
(2,1,33), (1,8,1,64)
```

Required test groups:

- logical and padded shape are both preserved;
- grid tile ordering, face ordering, and copy round-trip;
- broadcast of every size-one axis and mixed scalar/tensor operands;
- aligned and non-aligned shrink, pad, permute, and reshape classification;
- sum/max/mean padding identities;
- 31/32/33 external endpoints, multiple outputs, and compiler-created CBs;
- per-core spans with fewer tiles than cores and non-even division;
- assign/WAR hazards and persistent KV-cache updates;
- direct PROGRAM cache keys across dtype, layout, core geometry, and TTK config;
- dense/reordered ABI slots and in-place buffers in eager and JIT execution;
- concrete-shape rejection diagnostics and, once supported, symbolic-bound cache
  identity and runtime valid extents;
- mixed CPU/TT realization and TT ingress/egress copy ordering;
- CPU reference comparison in the test harness for every supported matcher;
- unsupported graphs fail with the first unsupported UOp, shape, access map, and
  proposed materialization boundary in the diagnostic.

The first success criterion is not model speed. It is that a non-aligned,
broadcasted, multi-core elementwise/reduction graph executes correctly without
entering generic GPU codegen. Once that is solid, matmul and aggressive fusion
have a trustworthy base.
