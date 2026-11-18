# Llama3 O port and implementation assessment

The single language reference is [ttrv_spec.md](ttrv_spec.md).
The [complete BF16 O projection source](examples/llama3_o.ttrv) computes
`output = residual + matrix @ context` on all five RISCs. The original design assessment below predates the backend. Hardware results are recorded under Validation.

## What the source exercises

| Worker | Work |
| --- | --- |
| BRISC | Fetch context and this worker's residual slice; stream its weight rows through a CB |
| TRISC0 | Unpack pairs of BF16 faces; release input pages only after `tensix.wait` |
| TRISC1 | Two-phase FPU multiply MOP; SFPU lane accumulation/reduction; BF16 residual-add MOP |
| TRISC2 | Pack each dot result; then pack the residual sum |
| NCRISC | Copy each dot result to its datum in the result page; write the output range |

The port starts from [the current projection](../../blackhole-py-old/examples/llama3/kernels.py#L181),
[dot schedule](../../blackhole-py-old/examples/llama3/kernels.py#L474),
[SFPU reduction](../../blackhole-py-old/examples/llama3/kernels.py#L553), and
[scatter](../../blackhole-py-old/examples/llama3/kernels.py#L748). Unlike the old
kernel, it never tilizes the 1-D vectors (see below).
The calls/macros are fully written; there is no hidden projection, reduction,
matmul, or residual-add helper supplied by the compiler.

Scalar code (partitioning,
addresses, the BRISC/NCRISC loops) is ordinary expressions and control flow; the
device operations are explicit statements. The native 32-lane reduction macro
expands to 34 instructions. Most of the kernel is explicit movement and handoff,
not arithmetic. This is reasonably writable for someone familiar with the device;
the Tensix side still requires knowledge of Src banks, Dst layouts, SFPU lane
groups, and asynchronous engines.

## Deliberate choices

- Work is assigned by `split(DIM)` over the `grid 88` launch (the first 88 workers,
  column-major); no per-core table. Firmware publishes each core's `core.*` at boot;
  `grid.size` is a compile-time constant (spec §4). Balanced row partitioning
  differs from the old table's placement policy, but assigns each output row
  exactly once.
- EMBED_TILES=2 covers 1B BF16; 4 covers 8B BF16. FP8 scaling/conversion is not ported.
- Unpack publishes one 256-element face at a time. The multiply MOP releases a
  Src bank after each face, matching that granularity. Publishing an entire tile
  while retaining the face-release schedule would be incorrect.
- Vectors stay in element order. The old kernel placed each result and residual
  value at its 32×32 tile position, added, then reordered back for the output. The
  add is elementwise, so that round trip did nothing. Here, with `lead = first & 31`,
  row `first + i` is datum `lead + i` in the result, residual and summed pages. BRISC
  reads the residual slice as one byte range; NCRISC writes the output as one. Both
  keep L1 and DRAM offsets equal modulo 64. Datums outside the range are never
  initialized or written out. This removed `tile_offset`, `zero_tile`, the residual
  gather, the 16-element output runs, three L1 buffers and the `inputs_ready` flag.
- Each dot result is packed as a full tile, then NCRISC reads its first BF16 value.
  This avoids inventing scalar-mask configuration while that audit is deferred.
  It writes extra bytes and is not expected to match the existing scalar pack's
  performance. The original reduction also rounds to BF16 before the residual add;
  this port preserves that arithmetic boundary.
- Dst-format switching uses an explicit completion/semaphore handshake (`dst_bf16`). It makes the
  ordering intended by the source visible. Math's and unpack's format fields share
  Config word 1; masked writes (spec §8) keep either from clobbering the other, and
  the handshake orders the switch against pack. The compiler does not check it.
- Conservative per-tile drains and per-row weight waits remain visible. No claim
  that this is the best schedule. Existing reduction NOPs are retained.

Resources: six CBs, BRISC reads on NoC0 (three transaction IDs), one acknowledged
NCRISC write on NoC1, two application Tensix semaphores, four math address-modifier slots, one
three-word replay, and one MOP configuration replaced between phases. Declared L1
payload is 22 KiB for 1B, 34 KiB for 8B, before alignment and
metadata. Actual register pressure and binary/code-slot size require a compiler.

## What writing the kernel exposed

1. **Unpack publication granularity must agree with math release granularity.**
   A high-level tile count alone does not encode this scheduling choice.
2. **Scalar packing matters for performance, not expressibility.** Full-tile pack
   makes the algorithm writable today; named scalar-mask fields remove that cost.
3. **Format changes cross worker boundaries.** Math and pack must agree on the
   phase. Preserving the other engines' fields in a shared word turned out to need
   no analysis: every Config write is a masked `RMWCIB`, and two TRISCs writing the
   same byte never lost a write on hardware (spec §8). Agreeing on the phase stays
   the author's protocol.
4. **ZEROACC cannot be documented as ordinary zero fill.** The encoder's field names
   disagree with the shared manual; preserve the working recipe pending a probe.
   SFPU loads require valid data. This source fully computes products before reading
   them. The epilogue's padding datums hold arbitrary L1 bytes, but they reach Dst
   only through unpack and the FPU add, never as invalid Dst read by the SFPU.
5. **The old blanket NoC source-alignment rule was too strong.** The output is one
   `output[first]` write with matching L1/DRAM offsets modulo 64 that may start at a
   non-16-byte boundary. The old scatter split it into 16-element runs; whether
   hardware needs that is spec audit item 4. If it does, the helper splits, not kernels.
6. **A declaration/operand reference is needed before a compiler.** The example
   forced explicit spellings for endpoint indexing, transfer counts, transpose,
   rotating lanes, address modifiers, and full-value SFPU constants.

This port does not exercise SFPU predicates/index capture, host writes, remote
atomics, or multicast. Attention and argmax still need those audits. Neither this
example nor consolidation proves that all Llama3 variants are now implementable.

## Validation

The hardware regression compiles this source and runs it on 88 workers of a p150.
It checks every BF16 output at dimensions 2048 and 4096 against an independent CPU
reference, using sparse weights, sign changes between launches, dense signed integer
weights, and dense fractional inputs. The fractional reference models the FP32-to-BF16
pack and ELWADD's shared-exponent significand alignment. The mixed decode graph also runs compiled embedding and BF16 down. With the reference prompt on p150a, 1B and 8B BF16 each matched all 64 reference tokens. The FP8 checkpoint matched 64 tokens with compiled embedding and prebuilt compute kernels.

## Original implementation estimate

The front end is modest. Structured statements, constant folding, hygienic expansion,
name resolution and table-driven instruction operands do not require a general
optimizing compiler. No tensor IR, auto-vectorizer, scheduler or graph partitioner.
The existing `ttrv/isa.py` supplies encoding/decoding machinery; most higher passes
are still placeholders.

| Part | Assessment |
| --- | --- |
| Parser, constants, macros, formatter | Small, conventional; keep expansion/source locations disciplined |
| Scalar expressions and control flow | Small; recursive descent and tree-walking codegen, constant folding only, no optimizer |
| Native instruction wrappers | Mostly schema work, plus float-immediate and runtime-field recipes |
| L1/CB/NoC lowering | Moderate; reuse existing recipes, document fences/credits and reserve hardware resources |
| Register allocation and calls | Small; lexical lifetimes, per-function static registers chosen against all call sites, no liveness, stack or spills |
| State checking | Small: template installation and semaphore initialization through branches, loops and calls. Config values are not tracked (masked writes, spec §8). SFPU scheduling hazards remain an audit |
| Hardware validation | Substantial; accepting a field width is easier than proving that the mode combination works |

Scalar code needs no dataflow analysis: lexical lifetimes replace register
liveness, and callers are compiled before callees so each callee's registers avoid
everything held at its call sites. Calls still move arguments and results. Config
needs no dataflow analysis either: each write changes only its own bits, so no
value is tracked. The work is in hardware recipes and validation, not analysis.

Keep v1 checking practical: reject known invalid uses and resource conflicts,
validate the local rules actually implemented, and document remaining runtime
preconditions. Do not turn a compiler for explicit instruction streams into a
proof system for arbitrary distributed protocols. Start with the O fixture's subset,
then extend the schema for attention and argmax. The design is manageable; the
hardware-specific semantics and verification are the work, not parsing the syntax.

### DRAM ports (2026-11-18)

The compiled O and down first ran slower than the exported kernels (1B: down 126.6 vs
77.6 µs per launch, 148 vs 168 tok/s). Every worker read its weights through the same
port of each DRAM bank. Rotating the port by worker, `port=core.id % 3` on the weight
read (a runtime `port=`, spec §7), as the exported O does, brings them to parity:

| p150a, per launch | exported | TTRV |
| --- | --- | --- |
| 1B O | 29.0 µs | 26.2 µs |
| 1B down | 77.6 µs | 83.1 µs |
| 8B O | 80.4 µs | 80.1 µs |
| 8B down | 253.3 µs | 256.9 µs |

Decode: 1B 167.2 vs 168.3 tok/s, 8B BF16 30.8 vs 30.9 tok/s, all 64 reference tokens
matching. The remaining down difference is the exported down's spatial NoC split (half
the workers read on NoC1); TTRV fixes BRISC to NoC0 (§7).

