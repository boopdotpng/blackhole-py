# Unified kernel builder and linearized tinygrad lowering

Status: proposed design.

This document records the current direction for authoring Blackhole kernels and
connecting them to tinygrad. It supersedes the idea that the TT backend should
recognize complete kernels by matching arbitrary shaped-UOp DAGs. The TT
backend should intercept tinygrad before generic GPU rangeification and scalar
code generation, apply TT-owned rewrite/selection rules, linearize the result
into an ordered TT-facing stream, and render that stream into TTK calls.

The implementation remains entirely Python. There is no MLIR dependency, no
textual intermediate language, and no second general-purpose tensor compiler.

## Goals

- Author one Python function for one logical kernel bundle.
- Give that function access to all five RISC instruction streams on a Tensix
  worker core.
- Declare a multi-RISC synchronization point once and lower both/all sides
  together.
- Keep TTK as the programmable hardware interface.
- Let TTK helpers such as `math.add()` own the configuration and hardware
  sequencing required by an operation.
- Feed an ordered tinygrad representation into a TT renderer instead of
  recovering whole operations from an unordered DAG.
- Preserve raw RISC-V and Tensix emission as an escape hatch.

## Non-goals

- A general graph optimizer in `blackhole-py-rewrite`.
- An MLIR dialect or a textual TT IR.
- Reimplementing tinygrad's Tensor API, autograd, mutation tracking, or
  program scheduling.
- Hiding distinct synchronization domains behind an untyped generic wait.
- Initially inferring arbitrary cross-role synchronization from low-level
  instruction dependencies.

## Overall lowering shape

```text
tinygrad Tensor/UOp construction
  -> tinygrad realization and buffer semantics
  -> callified shaped UOp graph
  -> TT-owned normalization, selection, and tile planning
  -> TT-owned linearization
  -> ordered TT-facing operation stream
  -> TT renderer
       maintains renderer state
       calls unified KernelBuilder and TTK helpers
  -> KernelBundle
       BRISC image
       NCRISC image
       TRISC0 image
       TRISC1 image
       TRISC2 image
  -> Program and ordinary tinygrad runtime call
```

The interception point should be after tinygrad has established buffer,
`STORE`/`AFTER`, assignment, and parameter semantics, but before
`get_kernel_graph`, generic rangeification, GPU scheduling, scalar load/store
insertion, devectorization, and final GPU linearization. Most GPU-specific
optimization and code-generation passes are deliberately bypassed.

The TT backend owns the transformation from the callified shaped graph to the
ordered TT-facing stream. It may use tinygrad's Python pattern matcher for
local canonicalization and instruction selection, but it should not depend on
recognizing an entire fused kernel as one fragile graph pattern. Its
linearizer walks dependencies in a deterministic order, makes TT-specific
fusion/materialization decisions, and emits explicit tile, buffer, movement,
reduction, and control operations for the renderer.

The exact ordered stream schema remains to be selected by a prototype. The
important requirement is that it retain the information needed for TT
lowering:

- buffer identity and read/write intent;
- dtype and logical shape;
- address and movement semantics;
- reduction boundaries and identities;
- control flow and runtime parameters;
- enough tile structure to avoid reconstructing 32x32 operations from fully
  scalarized loads and stores.

Tinygrad's final GPU-oriented scalar stream is not the input to the TT renderer:
it has already committed to policies and representations that do not describe
Blackhole tile distribution, CB allocation, or five-RISC execution. The
TT-facing linearization step therefore occurs earlier and produces a plain
ordered collection of Python UOp-like objects. It does not require a new text
format or compiler framework.

## One builder for the five RISC kernels

A Tensix worker core runs five RISC-V kernels concurrently. The public builder
should represent the complete set, while the current role-specific builder
continues to own one instruction stream.

Conceptually:

```python
class RoleBuilder:
  """The current per-role KernelBuilder: registers, labels, and instructions."""

class KernelBuilder:
  core: Core
  brisc: RoleBuilder
  ncrisc: RoleBuilder
  trisc0: RoleBuilder
  trisc1: RoleBuilder
  trisc2: RoleBuilder
  sync: Sync
```

The current `KernelBuilder` can be renamed internally or wrapped; preserving
the old name during migration is not an architectural requirement. What
matters is that the object passed to a kernel-authoring function owns all five
role builders.

`KernelBundle` should construct the five role builders for one physical worker
core, invoke the logical build function once, then finalize each role into its
own binary. It repeats this process for each physical worker core so ordinary
Python control flow can still specialize on `k.core`.

```python
def lower(self, build):
  kernels = {}
  for core in self.cores:
    k = KernelBuilder(core, self.params, self.resources)
    build(k)
    kernels[core] = k.lower_roles()
  return Program(kernels, ...)
```

The five instruction streams remain independent and concurrent. The order in
which Python appends operations to different role builders does not impose a
runtime ordering between those roles. Only CB protocols, events, semaphores,
barriers, and hardware waits create such ordering.

## Kernel authoring example

The initial API can remain close to the existing `examples/add1.py`, but place
all role construction in one function:

```python
def build_add(k):
  reader = k.brisc
  writer = k.ncrisc
  unpack = Unpack(k.trisc0)
  math = Math(k.trisc1)
  pack = Pack(k.trisc2)

  input_reader_cb = CB(reader, input_cb_config)
  input_unpack_cb = CB(k.trisc0, input_cb_config)
  output_pack_cb = CB(k.trisc2, output_cb_config)
  output_writer_cb = CB(writer, output_cb_config)

  unpack.init(input_unpack_cb)
  math.initialize()
  pack.init(output_pack_cb)

  k.sync.rendezvous(
    "compute_init",
    k.trisc0,
    k.trisc1,
    k.trisc2,
  )

  # BRISC reader stream.
  input_reader_cb.reserve_back()
  read_noc = reader.noc(0).initialize_from_firmware()
  write_ptr = reader.reg()
  input_reader_cb.write_ptr(write_ptr)
  with read_noc.read_batch() as reads:
    reads.issue(reader.param(src_param), read_coord, write_ptr, TILE_BYTES)
  input_reader_cb.push_back()

  # TRISC0 unpack stream.
  input_unpack_cb.wait_front()
  unpack.to_src_a()
  unpack.wait()
  input_unpack_cb.pop_front()

  # TRISC1 math stream. A higher-level math.add() helper can replace this
  # explicit copy/SFPU sequence while preserving the same builder structure.
  math.copy_src_a_to_dst()
  math.sfpu.run_tile(add_one)
  math.publish_dst()

  # TRISC2 pack stream.
  pack.acquire_dst()
  output_pack_cb.reserve_back()
  pack.to_cb()
  output_pack_cb.push_back()

  # NCRISC writer stream.
  output_writer_cb.wait_front()
  write_noc = writer.noc(1).initialize_from_firmware()
  read_ptr = writer.reg()
  output_writer_cb.read_ptr(read_ptr)
  with write_noc.write_ack_batch() as writes:
    writes.issue(read_ptr, writer.param(dst_param), write_coord, TILE_BYTES)
  output_writer_cb.pop_front()
```

This example is intentionally close to today's TTK. It demonstrates the
structural change without requiring a new expression language.

The corresponding program construction can be:

```python
bundle = KernelBundle((core,), params=(src_param, dst_param))
input_cb_config = bundle.cb(DType.BF16, 1, INPUT_CB_ADDR)
output_cb_config = bundle.cb(DType.BF16, 1, OUTPUT_CB_ADDR)
program = bundle.lower(build_add)
```

Resource declarations occur before lowering so all physical cores use the
same CB indices, barrier layout, parameter slots, and synchronization storage.

## Centralized synchronization

The main purpose of the unified builder is to make synchronization structural.
The author should not write the same barrier separately in three role
functions and manually keep party indices, addresses, and phases consistent.

```python
k.sync.rendezvous("compute_init", k.trisc0, k.trisc1, k.trisc2)
```

One call performs all of the following:

1. Looks up or creates the named rendezvous specification.
2. Verifies that a repeated declaration has the same participants and mode.
3. Assigns storage and party indices in a stable canonical order.
4. Appends an arrival and wait sequence to every participant's current
   instruction cursor.
5. Records enough metadata to diagnose the synchronization in a dump.

The existing per-role `Barrier(kernel, config, party)` remains useful as the
low-level lowering mechanism, but it should not be the primary authoring API.

The first implementation should support a one-shot same-worker L1 rendezvous.
It should reject accidental reuse. A barrier that executes repeatedly inside a
runtime loop needs a generation-safe protocol and should be added explicitly
rather than silently reusing a value of one.

A small directed event is the natural second primitive:

```python
k.sync.event(
  "weights_ready",
  producer=k.brisc,
  consumers=(k.trisc0,),
)
```

That call appends the release publication to the producer and the matching
acquire wait to every consumer. Width, comparison mode, address, and generation
belong to the event specification rather than to individual call sites.

### Keep subsystem synchronization in its subsystem

The unified `Sync` object should not reimplement all hardware waits. Existing
owners should continue to lower their own protocols:

- `CB` owns space/data counters and reserve/wait/push/pop.
- `NoC` owns command-buffer readiness and completion tickets.
- `Tensix` owns FIFO drains, hazards, and hardware semaphores.
- `Unpack`, `Math`, and `Pack` own their engine ordering.

The public synchronization surface can remain small while these objects expose
typed operations. In particular, NoC command-buffer availability, posted-write
departure, write acknowledgement, and read completion must not collapse into
one generic barrier.

## Higher-level TTK methods

The unified builder does not replace higher-level TTK helpers. It makes those
helpers easier to compose safely.

For example:

```python
result = math.add(src_a, src_b, destination=dst)
```

`Math.add()` can own the complete TRISC1-local sequence:

- operand and destination formats;
- fidelity and accumulation mode;
- address modifiers;
- MOP or replay selection;
- required `TTSTALLWAIT` operations;
- destination acquisition and publication;
- tracked changes to TTK engine state.

Likewise, named unpack, pack, and NoC helpers should own their complete local
protocols. Cross-role hand-offs either remain explicit through `k.sync` or are
performed by a small composite helper that has access to the unified builder.

This distinction prevents a role-local `Math` object from silently editing an
unrelated instruction stream while still allowing an explicitly composite API
later:

```python
k.compute.add(input_a, input_b, output)
```

Such syntactic sugar should lower to the same TTK calls and synchronization
primitives. It should not introduce another representation.

## Optional construction sugar

The explicit role setup should be implemented first. Repetition can then be
reduced without changing semantics. Possible forms include:

```python
reader, unpack, math, pack, writer = k.standard_pipeline()
```

or:

```python
pipe = k.pipeline(
  input_cb=input_cb_config,
  output_cb=output_cb_config,
  input_noc=0,
  output_noc=1,
)
```

Automatic initialization must remain inspectable. It should produce the same
five role streams that explicit construction would produce, and dumps should
show every inserted initialization and synchronization operation.

## Tinygrad renderer contract

The tinygrad integration has two TT-owned stages:

1. A TT linearizer consumes the callified shaped graph. TT-specific pattern
   rules normalize supported operations, preserve or create intentional fusion,
   select tile/layout strategies, and produce an ordered stream.
2. A TT renderer consumes that ordered stream and calls TTK lowering functions.

The TT linearizer is allowed to inspect dependencies and use pattern matchers;
that is necessary to turn a shaped expression graph into an ordered program.
The restriction is that it should not require one monolithic pattern for an
entire add, matmul, attention block, or other kernel. Patterns should describe
local semantic lowering and legal fusion boundaries, while the linearizer owns
ordering and materialization.

The renderer treats TTK lowering functions as its backend, not as a second
graph language.

The renderer consumes one ordered stream and maintains ordinary Python state:

```python
@dataclass
class TTRenderState:
  kernel: KernelBuilder
  values: dict[object, object]
  buffers: dict[object, BufferBinding]
  layouts: dict[object, TTLayout]
  current_core_plan: CorePlan
```

For each ordered operation, it calls an appropriate TTK helper:

```python
def render_op(state, op):
  match op.kind:
    case LOAD:
      state.values[op.out] = lower_load(state, op)
    case ADD:
      state.values[op.out] = state.kernel.math.add(
        state.values[op.lhs], state.values[op.rhs],
      )
    case STORE:
      lower_store(state, op, state.values[op.value])
```

This is sequential dispatch over the stream produced by the TT linearizer, not
whole-DAG pattern matching inside the renderer. Small local peepholes or
operation-specific lowering helpers remain possible, but renderer correctness
must not depend on rediscovering a large fused motif from arbitrary graph
shape.

The renderer should return a complete `KernelBundle`/`Program`. Tinygrad can
then retain responsibility for ordering separate program calls, parameter
rebinding, JIT capture, caching, and runtime execution.

### Linearization boundary requirements

Before selecting the boundary, capture representative ordered streams for:

- aligned and partial-tile elementwise operations;
- broadcasting;
- sum and max reductions;
- matmul;
- assignment and in-place updates;
- layout-changing movement operations.

Reject a boundary that has already erased information required to distinguish
these operations efficiently. In particular, tinygrad's finalized GPU scalar
form is not suitable. A stream consisting only of scalar `LOAD`, `ALU`, and
`STORE` operations would force the TT renderer to reconstruct tile grouping
and reductions, recreating the same fragile pattern-matching problem at a later
stage.

The selected stream should be ordered but not prematurely scalarized.

### Tinygrad passes intentionally bypassed

The TT path should reuse tinygrad's Tensor semantics, callification, buffer
identity, assignment ordering, parameter normalization, and scheduling of
separate program calls. It should bypass the generic GPU policy that follows
the TT interception point, including:

- generic rangeification and its fusion/materialization decisions;
- GPU reduction splitting and workgroup scheduling;
- BEAM and hand-coded GPU optimization heuristics;
- GPU global/local/upcast/unroll mapping;
- scalar load/store insertion and scalar reduction lowering;
- GPU devectorization, coalescing, and renderer-specific source generation.

Useful symbolic simplification or local canonicalization rules can be reused
selectively inside the TT linearizer without adopting their GPU orchestration.

## Raw programmability

Every role builder should continue to expose the current low-level APIs:

```python
k.brisc.write32(...)
k.ncrisc.noc(1).write(...)
k.trisc0.push_tensix_word(...)
k.trisc1.tensix_word(...)
k.trisc2.j(...)
```

Kernel authors can therefore mix:

1. composite pipeline helpers;
2. stateful TTK engine methods;
3. raw RISC-V and Tensix instruction emission.

Only operations expressed through tracked resource objects receive automatic
validation. Raw emission remains available when bringing up new hardware
features or writing specialized kernels.

## Development order

Tinygrad integration follows completion and validation of the standalone
Python kernel stack. The intended order is:

1. Finish the TTK engine and synchronization surface.
2. Implement the unified five-role builder and centralized synchronization
   API.
3. Port the existing Llama 3 kernels from `blackhole-py` onto the new API.
4. Use those ports to remove repeated setup, introduce named TTK operations,
   and improve generated code and performance.
5. Only then finalize the tinygrad TT linearizer and renderer contract.

The Llama 3 ports are not intended to be line-for-line translations. They are
the conformance and design workload for TTK. A successful port should generally
have fewer lines because repeated initialization, configuration, CB protocols,
and engine hazards move into typed reusable helpers. It should produce code at
least as good as the old kernel, with performance improvements pursued once
correctness and synchronization are stable.

Finishing TTK includes, at minimum, the pieces exercised by those kernels:

- correct RISC- and Tensix-ordered CB publication and release;
- reusable same-core rendezvous and directed events;
- complete NoC transfer/completion forms and cross-core semaphores;
- named unpack paths and configuration-context handling;
- named math/FPU/SFPU operations with complete setup and hazard handling;
- correct pack tile selection, formats, and publication ordering;
- reusable Tensix semaphore, drain, and reconfiguration protocols;
- role-local state tracking and explicit handling of shared configuration.

Porting add1 first proves the five-stage pipeline. Elementwise, RMSNorm,
softmax, attention, matmul, and the remaining Llama kernels then expand the API
only when a real kernel requires a new abstraction. This avoids designing a
large speculative DSL before the hardware protocols are understood.

## Incremental implementation

1. Add a unified builder that owns five existing role builders.
2. Change `KernelBundle` to accept one build function, while retaining the old
   five-callback form temporarily for comparison.
3. Implement one-shot `Sync.rendezvous()` that emits all party operations from
   one call.
4. Port `examples/add1.py` without adding higher-level syntax.
5. Verify per-role images and run the existing hardware add1 test.
6. Add negative tests for participant mismatch, duplicate names, accidental
   reuse, and unsupported placement in divergent control flow.
7. Add `Sync.event()` when the first directed role hand-off needs it.
8. Add named TTK methods such as `math.add()` one complete local protocol at a
   time while porting the Llama 3 kernels.
9. Complete the standalone kernel ports and use them to validate TTK coverage,
   generated image size, synchronization, and performance.
10. Intercept tinygrad after callify and prototype a TT-owned linearizer over
    shaped UOps, before generic rangeify and GPU code generation.
11. Define the ordered TT-facing stream and renderer state from those probes.
12. Implement the linearizer and renderer for one aligned add, then broaden
    operation and layout coverage.

## Correctness rules

- A synchronization declaration is written once and emits every participant.
- A barrier name has one participant set and one protocol.
- One-shot barriers cannot appear in a repeated runtime region.
- Cross-role Python emission order is not treated as runtime synchronization.
- TTK state remains role-local unless a shared-state transition has an explicit
  ordering protocol.
- CB publication after pack and release after unpack use Tensix-ordered forms
  when engine retirement is the true dependency.
- NoC completion types remain distinct.
- A higher-level TTK operation owns all local initialization, hazard waits, and
  state transitions required by its documented contract.
- The tinygrad renderer consumes an ordered representation that retains enough
  semantic and layout information for tile-native lowering.
