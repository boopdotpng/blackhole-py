# Blackhole Tensix text IR proposal

Status: design proposal, not an implemented language. Syntax below is illustrative.

## Purpose

The text IR is the single contract between two producers and one consumer:

```text
handwritten Python kernels -> Python DSL -------------------+
                                                           +-> text IR -> C++ compiler
tinygrad UOps -> Tensix scheduling and emission -------------+
```

The compiler produces binaries for the five RISC-V cores on each participating
Tensix tile, plus a launch manifest. Compiler implementation is out of scope.

The IR is **scheduled Tensix assembly**: explicit, close to the hardware, and
cheap to compile. Producers choose the schedule; the compiler implements it
safely on the five cores.

Ergonomic constructs such as automatic pipelining, layout algebra, and scoped
allocation belong in the Python DSL. They expand into concrete IR. tinygrad may
emit the same IR directly without using that DSL.

## Goals

1. No configuration-register writes in user programs.
2. No long RISC-V setup sequences for transfers, coprocessor operations, or address math.
3. No manual NoC transaction IDs, acknowledgments, or completion-counter management.
4. Access to every kernel-visible hardware capability.
5. One program per kernel, never separately authored programs for each RISC-V core.
6. No raw RISC-V or inline escape hatch below this layer.
7. Humans can write high-performance kernels with little effort through the DSL.
8. tinygrad can emit the text directly with a small target-specific implementation.
9. Few concepts and readable text; no MLIR or dialect-lowering stack.

“Every capability” here means kernel-visible Tensix facilities and communication
endpoints. Programming ARC firmware, PCIe configuration, or Ethernet cores would
require extending the target beyond the five Tensix controllers.

## Boundary between producers and compiler

| Decision | Producer: DSL or tinygrad | C++ compiler |
|---|---|---|
| Tiling, fusion, traversal | Chooses | Implements |
| L1 placement and buffer depth | Specifies | Checks bounds and alignment |
| Dst placement and reuse | Specifies | Checks legality and dependencies |
| Pipeline stages and prefetch | Specifies | Implements |
| MOP/replay/load-macro strategy | Specifies | Encodes and manages configuration |
| Address calculations | Emits expressions or traversal descriptors | Lowers to RISC/address-counter operations |
| NoC transfers | Specifies endpoints, sizes, ordering | Tracks transactions and completion |
| Five-core execution | Specifies operations and dependency structure | Partitions and emits controller programs |

The compiler may perform local mechanical optimizations: constant folding,
configuration deduplication, and instruction selection. It should not discover
the kernel's pipeline, choose tiling, or perform general layout legalization.

The earlier, more automatic design placed too much policy in the backend.
In particular, these constructs do **not** belong in the assembly-level IR:

```text
pipeline(window=2)
alloc scoped ...
layout compose(...)
prefer placement ...
```

Producers expand them into explicit buffers, loops, stages, and access patterns.

## Core model

Expose resources and operations; hide the protocols used to operate them.

The core concepts are:

- Typed scalar/vector values, including native SFPU vectors and masks.
- Explicit storage and views into that storage.
- Hardware operations with concrete operands and semantic attributes.
- Control flow, concurrent regions, and data handoffs.

Storage spaces include L1, SrcA, SrcB, Dst, and LRegs. DRAM, remote L1, and host
memory are transfer endpoints. Resource placement and reuse are explicit where
they affect the schedule. SrcA, SrcB, and Dst are not generic randomly accessible
arrays: legal operations and access shapes follow the hardware.

Useful operation families remain:

```text
copy ...
unpack ...
fpu.mul ...
sfpu.load ...
pack ...
```

Operands identify concrete L1 ranges, source banks, Dst ranges, formats, and
traversals. Address expressions can remain compact; the compiler generates the
corresponding address-math instructions.

Storage format, register format, logical indexing, and physical layout must not
be conflated. The DSL may use composable layout objects, but the text contains
their expanded maps or concrete access descriptors. Block floating point needs
explicit encoding metadata and exponent grouping, not merely an element size.

## Explicit scheduling without separate per-core programs

One kernel describes the participating tiles and the entire operation graph.
Tile-dependent branches express different tile roles.

Concurrent regions express the producer's chosen instruction streams. Operations
such as unpack, math, and pack identify their engines intrinsically. Ambiguous
scalar work or NoC issue placement can have an explicit placement attribute;
the backend should not need an optimizer to guess.

A producer could expand double buffering into:

```text
# Illustrative syntax; sizes and placement are producer decisions.
buffer weights l1 offset=0x10000 bytes=8192
stream w storage=weights slots=2 item_bytes=4096

concurrent {
    region fetch {
        for i = 0 .. rows {
            produce w as slot {
                copy dram(W + i*4096) -> slot bytes=4096 noc=0
            }
        }
    }

    region compute {
        for i = 0 .. rows {
            consume w as slot {
                unpack slot -> srca.bank0 ...
                ...
            }
        }
    }
}
```

`produce` and `consume` have fixed mechanical semantics: reserve storage, publish
completed contents, borrow them, and release after the last asynchronous use.
They do not ask the compiler to invent a pipeline. The producer explicitly chose
two slots and two concurrent regions.

These regions are parts of one kernel, not five separately authored programs.
The exact spelling of the handoffs remains an open design choice.

## Dependencies and completion

General alias analysis across mutable buffers and concurrent regions is too much
machinery for this compiler. Prefer named buffer handoffs and explicit operation
dependencies over broad automatic dependency inference.

For example:

```text
copy input -> staging complete=input_ready
unpack staging -> srca after=input_ready
```

A completion name is an abstract dependency, not a NoC transaction ID or counter.
The compiler owns transaction allocation, fragmentation, acknowledgment counts,
and the instructions needed to observe completion.

Alternatively, buffer handoffs can carry these dependencies implicitly, avoiding
completion names in common cases. Whether to expose both forms needs resolution.

The contract must distinguish:

- Data becoming ready for reading.
- Storage becoming safe to overwrite.
- A remote publication becoming visible to its consumer.
- Controller instruction execution versus queued coprocessor completion.

An asynchronous reader extends a buffer's lifetime until it no longer needs the
buffer. Kernel completion must include externally observable writes.

Remote communication needs a semantic publication/handoff, not just a write to
an address. A typed mailbox or bounded stream can express payload publication,
generation handling, and backpressure without exposing NoC bookkeeping. Ordinary
remote copies remain useful when another established dependency or kernel
completion orders the consumer.

Atomics need explicit supported operations, widths, and ordering semantics. Do
not imply a stronger general-purpose memory model than the lowering provides.

Check structured pipelines and static communication schedules where possible.
Do not promise a general proof that arbitrary distributed programs cannot deadlock.

## MOP, replay, load-macros, and address traversal

These are first-class assembly structures, not optimizations the compiler must
discover. For example:

```text
replay accumulate {
    sfpu.load ...
    sfpu.fma ...
}

...
replay.call accumulate
```

A MOP declaration describes its supported loop/template structure, including
distinct final iterations and traversal increments. A load-macro describes its
supported load-associated computation. Neither accepts arbitrary instruction
words or unrestricted expressions that cannot fit the hardware facility.

The compiler installs and encodes these structures and inserts necessary
configuration transitions. The producer controls invocation, reuse, and the
residency decisions relevant to performance. Resource conflicts should be
diagnosed rather than silently replaced by a different execution strategy.

Direct SFPU replay and SFPU replay driven through MOP are distinct choices:
they interact differently with a resident FPU MOP.

## Numerical semantics

The text must specify relevant numerical choices:

- Storage and register formats independently.
- Fidelity phases and accumulator behavior.
- Rounding, saturation, denormal behavior, and stochastic-rounding state.
- Fused versus separate arithmetic.
- Reduction order and lane traversal.
- Approximation recipes or explicitly supported approximation operations.
- NaNs, signed zeros, ties, and inactive-lane preservation.

Convenient reductions and approximation helpers can live in the DSL and expand
into explicit SFPU operations. Their semantics must not depend on hidden Python
objects or unspecified backend choices.

## Existing kernels as design tests

The references below are in the sibling `blackhole-py-old` checkout. They are
requirements for the design, not completed IR translations.

### Embedding

Reference: `../blackhole-py-old/examples/llama3/kernels.py`, `embedding`.

The schedule reads a token-ID page, extracts one scalar ID, and streams the
selected embedding row through L1 to its output. It needs dynamic addressing,
page-granularity transfers, and overlapping data movers, but no compute engines.
The producer explicitly chooses staging buffers and transfer granularity.

### QKV projection

Reference: the same file, `_projection_dot_math`, `_dot_row`, `_dot_accumulate`,
and `_dot_finalize`.

The existing BF16 path uses FPU elementwise products, persistent SFPU lane sums,
and a final lane reduction. The multiply MOP remains resident while the SFPU uses
direct replay. This is not simply a generic matmul lowering.

The IR must express explicit product scratch placement, source-bank lifetimes,
persistent LRegs, fidelity phases, replay bodies, and a concrete reduction tree.
FP8 activation quantization and output rescaling remain explicit operations.

### RMSNorm

Reference: the same file, `_rmsnorm`, `_rms_finalize_scale`,
`_rms_apply_weight_pair`, and `_rms_setup_apply_macro`.

The schedule retains input and gamma in Dst, accumulates squares, executes a
specific reciprocal-square-root recipe, and uses load-macros to apply the scale.
Typed bit operations, constants, shuffles, and arithmetic must express that recipe
without embedded instruction words.

`../blackhole-py-old/tests/timing/test_rmsnorm_half_pipeline.py` supplies useful
alternative scratch placements and overlap patterns. The DSL may choose among
them; the IR must spell out the chosen schedule. Capacity failures should be
diagnosed, not repaired by silent spills or a new algorithm.

### Attention

Reference: the same file, `_attention_program` and `_softmax_online_update`.

Context and online-softmax state remain in Dst while probabilities flow through
pack -> L1 -> unpack for the PV multiplication. Packing probabilities borrows
only the relevant Dst region; it does not release all Dst. Probability storage
remains live across all feature-tile consumers.

This feedback path is the decisive scheduling test. A simple acyclic
reader -> compute -> writer model is insufficient. Next-block transfers may
overlap computation, while loop-carried context updates remain ordered.

Split attention requires tile-dependent control and explicit block traversal.
RoPE/cache append additionally requires gathers and publication dependencies
before consumers read newly appended data.

### Argmax

References: the same file, `argmax`, and `../blackhole-py-old/ttko/argmax.py`.

The existing kernel combines SFPU scanning, index capture, scalar reduction,
remote L1 communication, host writes, history updates, and runtime publication.
The helper excludes NaNs and depends on logical traversal order for ties.

The IR must preserve those contracts or deliberately replace them with explicit
alternatives. SFPU-to-scalar data crosses Dst -> pack -> L1; there is no free
general extraction into RISC registers.

Runtime-state publication must use the current driver's declared ABI rather than
copying the old fixed-address parameter writes.

## Completeness without an escape hatch

Every supported computational hardware behavior needs a typed representation:

- FPU matrix/vector/elementwise/pooling operations and broadcasts.
- SFPU arithmetic, bit manipulation, exponent/mantissa operations, lookup tables,
  shuffles, transposes, index capture, paired compare/exchange, and rounding.
- Lane predication and inactive-lane preservation.
- Unpack/pack traversal, transpose, conversion, activation, and supported
  scatter/compression modes.
- NoC transfers, multicast, atomics, and publication.
- Relevant counters and runtime interactions through named operations.

Configuration-backed behavior appears as semantic attributes or declarative
hardware structures. Configuration register numbers and arbitrary MMIO pointers
do not enter the language.

Few concepts are achievable; a tiny opcode list with complete hardware coverage
is not. Use `../blackhole-py-old/tests/isa/requirements.py` as a starting point
for a capability-to-IR coverage matrix, preserving its distinction between tested
behavior and untested combinations.

## tinygrad integration

tinygrad can own scheduling, but its renderer alone cannot supply all of it.
Printing arithmetic, loops, conditions, loads, and stores is straightforward.
Before or during emission, target-specific logic must decide:

- Tile assignment and vectorization.
- Which values remain in Dst.
- Buffering and prefetch strategy.
- Where pack -> L1 -> unpack transitions occur.
- FPU versus SFPU implementation.
- MOP/replay/load-macro use.
- Reduction structure and matrix-fragment mapping.

Start with fixed lowering recipes for supported patterns: elementwise kernels,
reductions, and matrix operations. Each recipe emits a known schedule with a few
parameters. Later add selection, tuning, or schedule construction without
changing the text contract.

A generic arithmetic UOp stream does not by itself specify the optimized QKV or
attention schedules. That hardware knowledge must exist in a producer. Moving it
out of C++ does not eliminate it.

The DSL and tinygrad may share Python utilities for buffer planning, traversal
generation, and standard schedules. Neither producer is required to route through
the other's frontend. All compilation-relevant decisions must be serialized.

## Driver and launch manifest

The current `device.py` binding interface consumes per-worker role images and
expects position-independent execution in alternating code slots. The manifest
should describe:

- Worker selection and image variants.
- Role images, including inactive/trivial roles as required by the ABI.
- Argument layout and relocations.
- L1 allocations and initialization requirements.
- Runtime ABI and target version.
- Completion guarantees and resource limits.

A compilation report should expose storage usage, replay/MOP occupancy,
configuration transitions, and rejected resource constraints. This makes explicit
performance programming reviewable without an escape hatch.

## Suggested next steps

1. Define storage ownership, readiness, reuse, and remote-publication semantics.
2. Choose the minimal explicit handoff and concurrent-region syntax.
3. Manually translate the existing QKV, RMSNorm, and attention schedules.
4. Audit hardware capability coverage against ISA documentation and tests.
5. Add a small DSL that reproduces those explicit translations.
6. Give tinygrad fixed schedule recipes, then expand scheduling sophistication.

The tradeoff is deliberate: a smaller, cheaper compiler puts more scheduling
responsibility in both producers.

## Reading list

- [Exo](https://exo-lang.dev/) and [Exo 2](https://arxiv.org/abs/2411.07211):
  programmer-controlled scheduling and reusable transformations. Useful for the
  producer layer rather than requiring an elaborate IR compiler.
- [Halide: Decoupling Algorithms from Schedules](https://people.csail.mit.edu/jrk/halide12/):
  separates numerical meaning from execution strategy; useful when designing DSL
  conveniences that expand into explicit scheduled text.
- [Pallas software pipelining](https://docs.jax.dev/en/latest/pallas/pipelining.html)
  and [Mosaic GPU pipelining](https://docs.jax.dev/en/latest/pallas/gpu/pipelining.html):
  buffer retention and communication/compute overlap; useful models for DSL expansion.
- [Gluon layouts](https://triton-lang.org/main/getting-started/tutorials/gluon/layouts.html)
  and [async copies](https://triton-lang.org/main/getting-started/tutorials/gluon/async-copy.html):
  explicit placement and hardware execution beneath a compact kernel language.
- [CuTe layout algebra](https://github.com/NVIDIA/cutlass/blob/main/media/docs/cpp/cute/02_layout_algebra.md):
  coordinate maps and tiling; useful machinery for producers that emit concrete accesses.
- [Calyx](https://arxiv.org/abs/2102.09713): explicit control over asynchronous
  components and the distinction between starting work and observing completion.
- [StreamIt](https://people.csail.mit.edu/thies/papers/streamit-620.pdf) and
  [Phased Scheduling](https://commit.csail.mit.edu/papers/2003/lctes-phased.pdf):
  bounded buffering, producer/consumer rates, feedback, and static scheduling.
- [PTX ISA](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html):
  asynchronous completion, memory visibility, and storage reuse. Preserve the
  distinctions while hiding protocol mechanics.
- [FlashAttention](https://arxiv.org/abs/2205.14135): retained state and data
  movement as algorithmic choices; a useful expressiveness test.
- [The Real Tenstorrent Tensix Programming Model](https://clehaxze.tw/gemlog/2026/01-22-the-real-tenstorrent-tensix-programming-model.gmi):
  hardware-focused discussion of controller/coprocessor execution and performance.
- [Metalium guide](https://github.com/tenstorrent/tt-metal/blob/main/METALIUM_GUIDE.md):
  a baseline for separating essential schedule decisions from removable protocols.
- Local `../tt-isa-documentation/BlackholeA0` and behavioral tests in
  `../blackhole-py-old/tests/isa`: the completeness audit for operations, attributes,
  schedule structures, and compiler-owned mechanics.
