> Archived design history; superseded by [the consolidated spec](../../ttrv_spec.md).

# ttrv design review

Reviewed 2026-11-15. Target: [ttrv_spec_new.md](ttrv_spec_new.md).
Companion: [proposed language contract](ttrv_language_contract.md).
Current scope decisions and review of Fable's additions: [v1 follow-up](ttrv_v1_followup.md).

This is a review of the intended language, not a request to preserve the current
runtime ABI. The runtime should implement the chosen contract. Existing kernels
are evidence of required behavior and useful schedules, not syntax to reproduce.
The companion is a proposal, not an implemented or hardware-validated specification.

Scope clarification: v1 compute is a readable wrapper over individual FPU/SFPU
instructions, such as `fpu.elwmul` and `fpu.mvmul`, plus explicit configuration and
syncs. There is no requirement for higher-level compute operations. NoC should
start by wrapping the existing RISC-V request and wait sequences. Authors still
write the CB and inter-core protocols; simplifying those protocols is later work.

## Verdict

Keep the core idea: structured scalar assembly, named hardware operations, explicit
movement and synchronization, and small documented lowering recipes. It is a good
fit for readable kernels and model training. The draft is not yet sufficient to
write the shipped applications with fully specified named instructions and fields.

The largest missing piece is **ownership and completion**, not instruction spelling.
A kernel author must know when L1 can be overwritten, when another RISC can read
it, who owns Dst, and what a remote notification proves. Adding `noc.read` and
`cb.push` without documenting those rules would make it unclear how to write the
existing protocols correctly. V1 may deliberately keep that protocol work manual.

Replace the central promise with:

> The author chooses the schedule, storage, communication, and numerical behavior.
> The compiler encodes those choices, allocates named resources, and implements
> documented local instruction recipes. It never invents a pipeline or moves work
> across a synchronization boundary.

“Every line is a short fixed sequence” is too strong: `li`, register operands,
format-dependent moves, calls, and polling already violate a literal reading.
“No optimization” should mean no schedule transformation; choosing an immediate
instruction or allocating registers efficiently is desirable lowering.

## Blocking findings

### 1. Memory and publication have no contract

The final “not designed yet” section defers L1 resources, CBs, NoC, and cross-RISC
synchronization. Even embedding requires them. Define allocation, address spaces,
initialization, lifetime, CB wrap, retained reads, and completion before reuse as
language semantics. Persistent storage also belongs here. Work assignment can be
derived from core coordinates; per-core bindings are not a v1 requirement.

Do not make `cb.pop` wait for everything implicitly. Unpack must finish reading
its L1 source before that source is freed. Similarly, issuing `pack` is not proof
that a RISC can publish the output. An engine stall and a RISC-visible completion
wait are different operations; spell both out.

### 2. Shared config-word merging is not a concurrency rule

The config section says words 70, 71, and 119 are merged. Merging two compile-time
values does not order stores from different RISCs. A late whole-word store can
restore stale fields owned by another engine.

Choose a single-writer rule for each physical word within a phase. Merge immutable
initial configuration before workers run. For runtime changes, require an explicit
phase handoff that quiesces all users of the word and gives one writer ownership.
Check this through calls, loops, and templates. Do not silently add a global barrier.

The “paths disagree at a merge = error, write the field again after the merge” rule
also needs repair: a merge must produce unknown state, then a subsequent complete
assignment may restore it. Error when an operation needs an unknown value, not
merely because control flow joined. Whole-word writes still need known values for
the other fields; restating one field is not always sufficient.

### 3. The unpack context protocol is incomplete

The unpack section describes a RISC semaphore increment and a queued decrement,
while the semaphore section initializes every semaphore with maximum one and makes
increment-at-maximum undefined. That does not specify a two-in-flight protocol.
An increment is also not the base-address write itself.

Specify credit acquisition, the reserved semaphore's initialization, the actual
base write, context selection, and the event that returns credit. A total limit of
two does not prevent overwriting context 0 twice while it is still in use. Reuse
must be tracked per context, or the operation must enforce a defined rotation.
“No semaphores” should refer only to the Src-bank handoff, not the whole unpack.
The notes themselves leave the fastest base-update mechanism open; keep that
implementation choice separate from the source-level lifetime guarantee.

### 4. Complete the instruction and configuration reference

`pack` requires a multiple of 64 datums, but projections use scalar packing.
Attention needs transposed matmul operands, repeated reads of retained buffers,
SFPU predicates/tail masking, and Dst preservation across pack→L1→unpack.
FP8 needs an explicit numerical conversion contract. Argmax needs comparison and
selection modes, tie behavior, and host-addressed output.

These can all be written using native instruction wrappers, named configuration
fields, and explicit syncs. They do not require scalar-pack, transpose, reduction,
or attention algorithm abstractions. For example, scalar packing may be the
author's config sequence followed by PACR wrappers. Coverage means those fields
and instructions are specified and available, not that a one-line convenience
operation exists. Native operation names are welcome; manually assembled words
and unexplained numeric mode bitmasks are the encoding work to remove.

### 5. Multicast needs a receiver protocol

A rectangle and a write are insufficient. Define membership, sender inclusion,
destination layout, receiver readiness, source lifetime, remote arrival, and reuse
across generations. A local `sent` wait permits source reuse; it does not prove
that receivers may consume the data. An atomic issued afterward does not establish
payload-before-notification ordering without an explicit ordering guarantee.

The existing blocked matmul also has two simultaneous readers of a tilized buffer:
local unpack and NoC transmission. One ordinary SPSC CB pop cannot release storage
on behalf of both. In v1, keep this as an explicitly written protocol over shared
storage and completion counters. A new multi-reader abstraction is unnecessary.

### 6. The language reference is not yet complete enough to implement independently

The remaining math/SFPU signature table is explicitly absent. Also missing:
constant-expression grammar, runtime-operand eligibility per field, def-before-use,
register lifetime across calls, loop-bound sampling, integer edge cases, complete
format/layout definitions, and the initial state on which config tracking relies.

The spec permits at most three positional operands but uses four for `sfp.mad`
in two examples. Prefer removing the artificial limit: destination plus three
sources is familiar. Define defaults per operation rather than “absent = zero.”
Zero is not a universal safe format, route, count, or completion policy.

## Kernel coverage

The three shipped manifests contain the same eight families: embedding, QKV, O,
gate, down, LM, attention, and argmax. There are 114 exported `.S` files across
their variants. This review inspected the manifests, representative assembly,
the existing uncompiled O port, and the originating Python kernel routines and
helpers. It is a requirements audit, not an exhaustive instruction equivalence
proof or an on-device port validation.

| Kernel family | Required readable features | Current draft assessment |
| --- | --- | --- |
| Zero / embedding | Byte L1, DRAM page addressing, variable indexing, read completion, CB handoff, acknowledged writes | Blocked on memory/NoC/CBs |
| QKV / LM | Coordinate-derived row counts and routes, retained activations, streamed weights, fidelity, reductions, scalar packing | Compute skeleton present; configuration/signatures and movement incomplete |
| O / down | Projection features, residual phase, compact/dense element placement, variable-length writes, NoC variants | Requires scalar pack, explicit mode transition and layouts |
| Gate | RMSNorm, two projections, SwiGLU SFPU code, explicit approximation/rounding | Missing full SFPU and numerical contracts |
| Attention | RoPE gather, partial tiles, transpose, Q/P retention, masks, persistent Dst, DRAM port selection, remote state merge, acknowledged increment | Largest semantic coverage test; not writable in current public layer |
| Argmax | Predication, integer/float bit conversions, tie policy, mailboxes, host endpoint, runtime-state multicast | Needs scalar/SFPU completeness and remote publication |
| Blocked matmul, outside the shipped decode manifests | Tilize, multicast pumping during waits, two-reader buffer lifetime, accumulation | Advanced acceptance target; requires nonblocking progress tests |

Representative source anchors:

- [Projection scalar output](../../../../blackhole-py-old/examples/llama3/kernels.py#L302)
  and [dense scatter](../../../../blackhole-py-old/examples/llama3/kernels.py#L748).
- [Attention retained operands](../../../../blackhole-py-old/examples/llama3/kernels.py#L1158),
  [merge and non-posted increment](../../../../blackhole-py-old/examples/llama3/kernels.py#L1711).
- [Argmax](../../../../blackhole-py-old/examples/llama3/kernels.py#L1873).
- [Multicast sender and concurrent local reader](../../../../blackhole-py-old/examples/matmul_peak_kernel/kernel.py#L1103).
- [CB implementation](../../../../blackhole-py-old/ttko/cb.py),
  [NoC implementation](../../../../blackhole-py-old/ttko/noc.py),
  [existing O port with GAP annotations](../../../tests/ttrv/cases/o.ttrv).

These sources establish needs and supply useful v1 lowering recipes. Repeated
NoC setup is acceptable initially if it preserves the current known sequence and
has a visible cost. Replace raw word patching with named fields. Make any helper
side effects, including Dst clearing or transaction-exit waits, explicit.

## What to trim

| Keep in the main language guide | Move to a reference or implementation appendix | Remove or replace |
| --- | --- | --- |
| Five worker streams and asynchronous engines | Firmware addresses, code slots, encoding rotation | “No types”: use scalar words plus checked operand/resource kinds |
| Named byte storage, CB ownership, explicit waits | Native config field tables and bit positions | Global zero defaults: publish per-operation defaults |
| Normal tile moves and scalar pack | BFP exponent derivation and workaround sequences | Raw words as the answer to missing normal operations |
| Named math/SFPU operations and numeric modes | Complete MOP mask and SFPMACRO timing rules | “Output is exactly what you wrote”: define allowed lowering |
| Calls, loops, constant specialization | Measured cycle tables and probe provenance | In-body addrmod declarations silently hoisted to function entry |
| One complete working example | Advanced multicast routes and physical resource pinning | Calling BRISC “read” and NCRISC “write” as if these were restrictions |

MOP, replay, and SFPMACRO are useful performance tools, not candidates for deletion.
They currently occupy roughly a quarter of the draft before a reader has a complete
data-movement example. Teach them after the basic pipeline. Keep their normative
contracts, but give the beginner a short path through the documentation.

Retain the explicit `mop.load` model. Apply the same distinction to address modifiers:
file-level definition plus explicit installation, or a clearly marked startup block.
Do not imply that text placed inside a loop runs there when it is actually hoisted.

The generated config catalog is useful backend evidence, not human-facing API
documentation. Every public field needs a semantic name, unit, allowed symbolic
values, default, owner, lifetime, and interaction rules. A shorter spelling of an
undocumented bitfield is still a leaky abstraction.

## Recommended documentation order

1. What runs where: scalar RISCs, queued engines, local and remote storage.
2. A complete reader→compute→writer kernel, then its cost annotations.
3. Values, constants, functions, and control flow.
4. L1 declarations, layouts, parameters, and CB ownership.
5. NoC transfers, waits, atomics, and multicast.
6. Unpack, math, SFPU, pack, and Dst ownership.
7. Named configuration and phase changes.
8. Replay, MOP, and SFPMACRO.
9. Generated operation reference, diagnostics, and target limits.
10. Backend recipes and experimental hardware evidence, separately versioned.

For each operation use the same small reference template: **signature; effects;
completion; resources; preconditions; lowering/cost; example**. Make all examples
parse-checkable once the parser exists. Mark fragments and proposed syntax now.

Do not maintain two conflicting normative drafts. The old
[kernel-language-v1.md](kernel-language-v1.md) contains useful memory/NoC design,
but its automatic stalls, config elision, template installation, syntax, and entry
state conflict with the new draft. Salvage the contracts, then archive it as history.
Fix stale cross-references too: `ttrv_cfg.md` points to an “unpack contexts” section
that moved, and the new draft's `SFPLOADMACRO.md` reference has no local link.

## What would make this a net improvement over TTK?

Less code is useful if it removes encoding and repetitive instruction boilerplate without
hiding decisions that determine speed. The winning abstraction boundary is:

- **Visible:** bytes transferred, layouts, retained storage, outstanding work,
  source-bank and Dst handoffs, configuration changes, waits, unrolling, routing,
  precision, and resource capacity.
- **Mechanical:** bit encodings, packet registers, address units, branch encoding,
  instruction packing, fixed hardware workarounds, and named resource assignment.

Source should reveal likely bottlenecks; it cannot guarantee exact cycle prediction
under contention, cold instruction cache, or variable backpressure. Document which
operations may block and why. Supply a listing mapping every expansion and injected
poll to its source line, plus resource and transfer summaries. Do not replace this
with a blanket “one line = one instruction” claim.

Prove improvement using matched algorithms and numerical contracts:

| Measure | Acceptance evidence |
| --- | --- |
| Expressibility | All eight shipped families in public syntax; no raw words or native config masks |
| Correctness | Existing references, repeated launches, tail cases, all three model variants |
| Performance | Per-kernel latency and throughput distributions versus TTK on the same device/workload; no unapproved regression |
| Readability | Side-by-side O and attention ports, count manual encoding/setup lines and explain each wait from source |
| Compiler quality | Code size, live scalar registers, L1 usage, setup cost, and source→listing correspondence |
| Model usability | Compile rate, correctness rate, timeout rate, and achieved speed for the same small model and rollout budget |

Nothing inspected establishes those outcomes yet. Most compiler passes are stubs;
the O fixture explicitly says it has not compiled and targets the older draft.

## Additional goals worth making explicit

**Numerical reproducibility.** Specify rounding, accumulation, saturation, NaNs,
infinities, signed zero, approximation error, and argmax ties where applicable.
Never change these to improve a benchmark silently.

**Composability.** A subroutine should state which engines, config, counters,
templates, and buffers it touches. Otherwise factoring code hides device state.
These effect summaries may be compiler-derived and shown in docs/listings.

**Stable training feedback.** One canonical formatter, stable diagnostic IDs,
small error spans, bounded compilation, and deterministic builds reduce wasted
rollouts. Permit fixed-budget resource exhaustion as an ordinary diagnostic.

**Useful verification, honest limits.** Check local misuse and statically known
hazards; do not promise to prove distributed liveness or all runtime address bounds.
Provide instrumented runs and timeouts for those. SFPMACRO checking must include
interactions across macros and explicit SFPU operations, not only each macro alone.

**A clean RL objective.** Gate reward on correctness and completion; penalize
timeouts/resource violations; then reward measured speed. Keep warmup policy,
timing boundaries, shapes, numeric tolerances, and device state fixed. Use held-out
shapes/seeds and distributions rather than one noisy timing. Deterministic source
and compiler do not make hardware timings deterministic.

**Versioned coverage.** Every operation/mode should say supported, experimental,
or rejected. The measured plain-pack result for BF16/FP32 must not be presented as
verification of BFP packing: the supporting notes explicitly leave BFP output
under the uniform addrmods unconfirmed.

## Suggested next steps

1. Settle the memory/completion/config ownership contracts in the companion.
2. Finish the native instruction/field schema and wrap the existing NoC request,
   status, and wait sequences. Keep CB and inter-core protocols explicit.
3. Write complete embedding, O, and partitioned-attention ports against that schema.
   Add a small multicast protocol and the blocked-matmul lifetime example.
4. Reorganize the main spec around those examples; generate the reference tables.
5. Implement and validate the runtime/compiler against the spec, then measure
   expressibility, correctness, speed, and small-model learning together.
