> Archived design history; superseded by [the consolidated spec](../../ttrv_spec.md).

# ttrv: proposed language contract

Status: design proposal, 2026-11-15. This formalizes the missing contracts in
[ttrv_spec_new.md](ttrv_spec_new.md); it does not replace that draft or claim an
implemented compiler. See [the review](ttrv_review.md) for findings and evidence.
Syntax below is proposed. Examples are uncompiled. The runtime is to implement
the language contract, rather than constrain it to today's ABI.
The [v1 follow-up](ttrv_v1_followup.md) records subsequent decisions and the macro
proposal; it supersedes earlier suggestions about per-core bindings and DRAM lookup.

V1 scope: thin instruction wrappers for compute; thin wrappers over existing
RISC-V sequences for NoC requests and waits; author-written CB and remote
publication protocols. No algorithm-level compute operations or automatic
transaction/ownership system is required. Proposed conveniences below are not
prerequisites when ordinary scalar instructions and named hardware fields already
express the same behavior.

## 1. Execution model

A program contains up to five entry functions: `brisc`, `ncrisc`, `trisc0`,
`trisc1`, and `trisc2`. BRISC and NCRISC are general scalar workers, not mandatory
reader/writer roles. Tensix operations have explicit engine restrictions.

Scalar instructions execute in their RISC stream. Tensix instructions enqueue work
on an engine; issuing one does not mean it has completed. NoC requests are also
asynchronous. There is no implicit ordering between different worker streams.

The author chooses loops, unrolling, transfers, layout conversion, configuration
changes, and synchronization. The compiler may select instruction encodings,
allocate registers/resources, and emit the operation's specified recipe. It may
not reorder operations, insert a pipeline, fuse arithmetic, spill scalar registers,
or silently wait for unrelated work.

Some operations necessarily poll for an issue slot or resource credit. Their
reference entries must say so. Such polls implement the operation's semantics;
they are not a promise of constant latency.

Entry and exit have a documented cost. Before workers start, runtime initialization
establishes declared resources and initial configuration. Exit requires all owned
asynchronous work to have reached its required completion state. Returns must not
silently drop outstanding work. Whether a fixed exit drain is part of the ABI must
be stated and counted; it cannot repair an earlier premature buffer publication.

## 2. Values and spelling

Scalar registers hold 32-bit words. Arithmetic has RV32 semantics, with signedness
in the operation. No tensor type inference or runtime register expressions are
needed. **Checked operand kinds are still required:** scalar register, SFPU
register, byte address, coordinate, format, channel, buffer, and template are not
interchangeable operands.

- Required operands are positional, or named from the first named operand onward.
  Allow destination plus three sources for `sfp.mad`; remove the three-operand cap.
- Optional arguments have defaults documented by each operation, not a global zero
  rule. Booleans use one canonical spelling. Enumerations use semantic names.
- Constants may use arithmetic and bitwise expressions; runtime arithmetic remains
  explicit instructions. Define precedence, integer range, and division by zero.
- Registers must be assigned on every path before use. Parameters are read-only.
- A loop samples its unsigned trip count once on entry; zero executes no iterations.
  Changing the source register in the body does not change the trip count.
- A compile-time `repeat i, N { ... }` duplicates its body; a runtime `loop` never
  unrolls implicitly. `N` is a nonnegative constant subject to compiler limits.
- Calls have checked argument/return counts, a static acyclic call graph, and
  preservation of caller-live values. Register allocation includes return-address
  lifetimes and compiler temporaries. Exhaustion is an error, not a hidden spill.

SFPU working registers may remain `l0`–`l7`: their physical grouping affects real
instructions and is useful scheduling information. Give fixed constants semantic
names (`zero`, `one`, `neg_one`, and a documented name/value for other fixed
coefficients). Allow named aliases for programmable constants while reporting
their physical slots. Accept numeric float literals and named rounding/comparison
modes; do not require IEEE bit patterns or integer modifier codes. An explicit
bitcast is appropriate when an algorithm intentionally manipulates bits, as argmax
does. It must not be the normal way to load a floating-point constant.

Keep preprocessing small: named constants and conditional compilation, with an
error for undefined condition names. Avoid defining behavior as “same as C” unless
the entire relevant preprocessing grammar and include policy are intended.

## 3. Storage and parameters

Proposed declarations:

```text
param input, kind=dram, page_bytes=2048, banks=8
param output, kind=dram, page_bytes=2048, banks=8
param total_rows

l1 scratch, bytes=4096, align=64
persistent arrived, bytes=4, align=4, init=0
cb tiles, page_bytes=2048, capacity=2, producer=brisc, consumer=trisc0
```

Names bind through a generated host manifest. Parameter slot numbers and firmware
addresses are ABI details. Launch parameters are shared; kernels derive their work
from `core.x` / `core.y`. Per-core parameter tables are deferred. The target profile
states parameter/resource limits.

`core.x` and `core.y` provide worker coordinates. Their exact mapping and any
additional rank/id facilities will be settled with the runtime, not prescribed by
this proposal.

L1 allocation is static. Size and alignment are constants. The host supplies an
allowed arena and bindings for persistent regions; deterministic placement within
that arena is reported in the manifest. `at=` may pin an address explicitly.
Overlaps, misalignment, and overflow are errors unless an explicit alias/view binds
the same backing allocation. No automatic lifetime-based storage reuse in v1.

Ordinary L1 contents are unspecified on entry. Allocation does not imply zeroing.
Persistent storage is initialized once at installation and survives launches;
the program owns subsequent reset/rearm synchronization. Reinstallation and
concurrent-launch access have explicit host-side lifetime rules.

CB payloads, metadata, atomic return slots, constant tables, code, and any fixed
call bookkeeping all appear in the memory report. An allocation's name denotes
its byte address; no hidden element-size multiplier.

Provide read-only data tables and named views for host/runtime bindings. Host
endpoints need a full address representation; a scalar `u32` plus worker XY is
not enough for every endpoint used by argmax.

## 4. Layout and numerical interpretation

A buffer is bytes; its interpretation is explicit at an operation or view.
Define `linear` and `tile32` layouts first. For 16/32-bit tile data, `tile32`
means four 16×16 faces in top-left, top-right, bottom-left, bottom-right order.
Document the map for partial tiles separately; a short count must not implicitly
mean a crop of a different shape.

Provide `tile.bytes(format, shape)` as a constant query, including BFP exponent
storage and alignment. BFP byte size must not be calculated as `1024 * itemsize`.
Define format exponent family, special values, group size, and mantissa rounding.

Use separate semantic fields for Dst representation, output representation, and
rounding. A field called `in=bf16` must not secretly be the only way to request
seven-bit prerounding of FP32 accumulators. Named rounding modes can still lower
to that hardware input-format encoding.

Conversions state saturation, NaN/Inf/signed-zero behavior, and whether they are
exact or approximate. No automatic conversion or retile is inserted because a
consumer expects a different layout. Known incompatible uses are errors.

## 5. Circular buffers

A CB is a bounded queue of fixed-size pages in L1 with one producer and one
consumer. It owns storage, publication counters, and each end's cursor. These are
named resources; users never encode a CB index or synchronization MMIO address.

| Operation | Contract |
| --- | --- |
| `cb.reserve q, n` | Block until the producer may write `n` free pages; reserve them without publication |
| `cb.write_ptr p, q` | Address of the current reservation |
| `cb.push q, n` | Publish the reserved pages after their writes have completed |
| `cb.wait q, n` | Block until the next `n` pages are published; retain read ownership |
| `cb.read_ptr p, q` | Address of the retained front pages |
| `cb.pop q, n` | Release retained pages after all accesses using them have completed |

For the minimal version, `n` is a positive compile-time constant no greater than
capacity. Permit only one outstanding producer reservation per CB and one consumer
front window. Repeated `wait` on the same front window does not consume pages or
create another reader. Repeated reads before `pop` are legal and necessary.

Reservations/windows may wrap, but a returned pointer must not imply contiguous
storage across the ring boundary. V1 can use the current cursor-advance recipe and
author-written page-address arithmetic. Document the contiguous-span precondition
and explicit wrap calculation; do not insert padding or copies. A `cb.page` helper
and nonblocking `cb.test` are optional later conveniences. Named counter reads plus
scalar comparisons suffice for manual nonblocking protocols in v1.

Formal abstract state uses unbounded logical counters `P` (published) and `C`
(consumed), with `0 <= P-C <= capacity`. Reserve requires
`n <= capacity-(P-C)`; wait requires `n <= P-C`; push advances `P`; pop advances `C`.
Hardware counters may wrap only under a documented capacity/outstanding bound
that makes their modular differences unambiguous. That bound is a target limit.

Publication/release orders preceding scalar L1 accesses. It **does not complete
NoC, unpack, or pack work**. The producer must complete incoming reads or packing
before push; the consumer must complete unpack reads or outgoing sends before pop.
The implementation supplies the local fences required by these contracts.

For concurrent local unpack and multicast of one allocation, retain storage until
both complete. Use explicit shared L1 plus one completion per reader in v1.
Do not let a second consumer masquerade as SPSC.

## 6. Completion and synchronization

Keep these distinct in names and documentation:

| Event | What it proves |
| --- | --- |
| Instruction issued | Work was accepted into a stream |
| Engine dependency satisfied | Later work in the blocked engine may proceed |
| RISC-visible engine completion | Earlier specified engine accesses finished; scalar code may act on that fact |
| NoC source released (`sent`) | All prior writes in the channel have finished reading local source bytes |
| NoC response received (`complete`) | Prior requests completed according to their request kind |
| CB publication observed | The producer published pages after satisfying their required completion |

Retain `stallwait` as the explicit engine-scheduling primitive, with a truth table
for each condition. Do not describe `srca_vld` as “clear” without explaining whether
it names valid state or the reason for stalling. Add a distinct RISC-visible
`tensix.wait unpack|pack|math|sfpu` operation for safe scalar handoff; its backend
must implement the exact engine-to-RISC completion guarantee.

Tensix semaphores and L1 counters are different resource classes. Name and declare
application semaphores; compiler-reserved unpack credits cannot also be allocated
to user code. Define initial/max values and ownership. Hardware semaphore updates
do not themselves wait for prior math/packing to finish.

Dst ownership transfer and Dst clearing are separate. The author writes the
semaphore/stall protocol and invokes the native ZEROACC wrapper separately.
Packing never implies clearing Dst. Declare valid row bounds for each
Dst representation and make offset units explicit.

## 7. NoC channels and endpoints

```text
noc rd, kind=read, network=0, owner=brisc
noc wr, kind=write, network=1, owner=ncrisc, delivery=acknowledged
noc increment, kind=atomic_add, network=0, owner=ncrisc
```

A channel here is just a name for a fixed NoC instance, command buffer, transaction
ID, and request options. It is not a transaction object with automatic begin/end,
waits, or scope-exit cleanup. Explicit `buffer=` and `tid=` bindings are sufficient
for v1; report bindings and reject conflicting owners where statically known.
Requests may rewrite all required command words every time, using the existing
RISC-V recipes. Static-word caching, automatic TID reuse, and command-buffer
virtualization are not v1 requirements.

Endpoints distinguish local L1, remote worker L1, banked DRAM, and host memory.
Provide named constructors/address operations, never packed coordinate bitfields.
DRAM page lookup is handled inside the NoC helpers. Authors need not reconstruct
the standard bank/address mapping. Expose tuning options where useful; coordinate
mapping and address-width checks belong to the compiler/runtime target.

Proposed operations (the reference must enumerate allowed operand kinds):

```text
noc.read  rd, dst=local_bytes, src=remote_endpoint, bytes=count
noc.write wr, dst=remote_endpoint, src=local_bytes, bytes=count
noc.wait  rd, complete
noc.wait  wr, sent
noc.wait  wr, complete
```

Requests may block for command-buffer availability and issue credits. They do not
wait for remote completion. The target reference defines packet splitting,
transfer bounds, alignment, counter limits, and the static/dynamic operand cost.
Do not silently repair an alignment mismatch with a bounce buffer.

A wait covers all requests issued on that channel before the wait, including
requests in earlier loop iterations. A channel has one issuer, so no other worker
can add requests during its wait. `complete` on read means destination bytes are
ready for local use; on acknowledged write it means destination acceptance at the
documented memory-visibility point and implies `sent`. Posted writes support only
`sent`; that is insufficient to publish data to a remote consumer.

Expose named status reads for command-buffer busy, requests outstanding, and writes
outgoing. Authors can write scalar polling/pumping loops with them, as in the
current kernels. No `noc.try_*` or transaction scheduler is required for v1.
Document what each counter counts and when it is safe to reuse the command buffer.
Wrap issue-safe polls and fences at the same boundary as the selected existing
recipe; list them explicitly in that operation's lowering contract.

## 8. Atomics and remote publication

Start with the operation the kernels actually require:

```text
noc.atomic_add increment, dst=remote_counter, value=1, result=old_value_slot
noc.wait increment, complete
```

Define width, alignment, wrap behavior, supported increment range, and the atomic
linearization/visibility point in the target operation reference. Requesting an
unsupported runtime increment must be an error, not truncation into an ISA field.
`result` is an aligned L1 response allocation, not an immediately available scalar
register. It remains live until completion; simultaneous atomics need distinct
return slots unless their protocol proves safe reuse. Default to acknowledged
atomics. An omitted result may use compiler-owned scratch shown in the manifest.

Atomics apply to the named word. They are not an implicit release fence for other
channels. A complete publication protocol is:

1. Sender writes payload to a receiver-owned slot using acknowledged writes.
2. Sender waits for those writes to complete.
3. Sender issues the counter increment and waits for its completion.
4. Receiver observes the expected count with an acquire-capable local wait, then
   reads the payload.

V1 can use explicit scalar loads, comparisons, loops, and fences for the receiver
wait. Document the ordering sequence in a complete example. `l1.wait` and
`l1.test` are optional later conveniences. The receiver clears/rearms only after every sender for this
generation is accounted for and before any sender can publish the next one.
Persistent counters must not be reset by unsynchronized launch setup.

Other atomics belong in the operation schema when a kernel or measured hardware
capability justifies them. Do not imply a generic arbitrary atomic expression API.

## 9. Multicast

```text
noc broadcast, kind=multicast, network=0, owner=brisc, delivery=posted
noc.multicast broadcast, dst=receiver_buffer, src=local_buffer,
              group=rectangle, bytes=block_bytes
noc.wait broadcast, sent
```

This is only the data-transfer fragment, not a complete publication protocol.
A group has logical inclusive rectangle bounds and explicit `include_sender`.
The target maps logical coordinates to the chosen network. Holes, excluded cores,
empty groups, and incompatible destination placements are validated. Do not silently
multicast to a bounding rectangle containing workers outside the declared group.
All recipients use the specified destination byte address; source and destination
layout compatibility is the program's responsibility.

Receiver readiness, arrival, and storage release are separate:

1. Each recipient reserves destination storage and announces readiness for a
   generation. The sender waits for all required recipients.
2. The sender multicasts payload. It may reuse its source after `sent` only if
   no local compute operation is still reading that source.
3. Each recipient establishes payload arrival before publishing to its local CB.
4. Consumption returns credit for the next generation; stale readiness or arrival
   notifications cannot satisfy the next transfer.

For v1, lift the current multicast request, route options, status reads, and waits,
and document the existing author-written payload/notification protocol. The
ordering guarantee that protocol relies on must be stated and validated; a new
acknowledged-multicast abstraction is not required. Posted multicast followed by
`sent` followed by an unrelated flag/atomic is not sufficient by this contract.
If hardware cannot implement the chosen arrival guarantee, reject that mode;
do not quietly lower it to many unicasts. Keep the protocol visible in source.

Route/VC/link options, when needed for performance, use named enums and document
their ordering and contention effects. Users must never calculate a packet control
word. Full multicast conformance remains blocked until the arrival protocol is
specified and validated; this proposal does not claim to have proved it.

## 10. Configuration and compute

Initial config is a declarative startup block applied before workers are released.
Its cost is reported separately. Executable config writes remain at their source
location and are always emitted; do not infer hoisting or deduplication.

For each physical config word, define one writer in an execution phase. Independent
field names in the same word do not authorize independent concurrent writers.
Phase changes use explicit handoffs: quiesce readers, transfer ownership, write
the complete known word, publish completion, resume readers. Define engine barriers
needed for each public operation; reject known misuse instead of adding unrelated
waits. The compiler emits mandatory local encoding/workaround recipes only.

Track values as known or unknown through branch joins and loop fixed points.
A use requiring unknown config is an error. Complete assignments can restore
known state. Function summaries and replay/MOP effects participate in this analysis.
Named native instruction wrappers participate in this analysis and are the normal
compute API. Opaque encoded words, if allowed for backend development, invalidate
affected knowledge; only those opaque escapes are excluded from the coverage gate.

Cover these capabilities through native instructions and configuration fields:

- Plain and partial unpack with a specified layout and source-bank publication.
- Matmul-compatible transpose/tilize and explicit counter/address modifiers.
- Scalar pack, tile pack, numerical rounding, and format changes.
- Dst clear/preserve, math fidelity, SFPU load/store formats, constants, predicates,
  casts, shifts, comparisons, transpose, and approximation sequences.
- Replay/MOP installation and calls with checked capacity and side effects.
- SFPMACRO register clobbers, cross-macro hazards, and delayed instructions at exits.

The compute API is `fpu.elwmul`, `fpu.mvmul`, the other native FPU operations,
SFPU operations, counter changes, configuration, and syncs. The current draft calls
the FPU namespace `math`; choosing `math` versus `fpu` is just a naming decision.
Users construct matmul, reduction, softmax, masking, and conversion sequences from
these operations. No extra compute abstraction is needed. The remaining work is
to enumerate operands, readable enum values, state effects, and legal combinations.

## 11. A complete data-movement example

This proposed embedding-like page copy demonstrates the lifetime rules without
depending on unspecified math op signatures. The proposed `dram.page` constructor
means one logical page of the declared banked buffer. It expands address mapping;
it is not arbitrary runtime expression syntax. A performance-oriented loop may use
the separate locate/advance operations described above.

```text
param input, kind=dram, page_bytes=2048, banks=8
param output, kind=dram, page_bytes=2048, banks=8
param pages

cb staging, page_bytes=2048, capacity=2, producer=brisc, consumer=ncrisc
noc rd, kind=read, network=0, owner=brisc
noc wr, kind=write, network=1, owner=ncrisc, delivery=acknowledged

fn brisc {
    loop page, pages {
        cb.reserve staging, 1
        cb.write_ptr p, staging
        noc.read rd, dst=p, src=dram.page(input, page), bytes=2048
        noc.wait rd, complete
        cb.push staging, 1
    }
}

fn ncrisc {
    loop page, pages {
        cb.wait staging, 1
        cb.read_ptr p, staging
        noc.write wr, dst=dram.page(output, page), src=p, bytes=2048
        noc.wait wr, sent
        cb.pop staging, 1
    }
    noc.wait wr, complete
}
```

Reader and writer overlap across pages. The reader permits one read in flight;
that throughput limitation is visible at the wait. The writer releases each source
after `sent` but allows remote acknowledgements to overlap until the final wait.
Zero pages issues no requests; waiting on an empty channel completes immediately.

A compute pipeline adds two handoffs with the same rules: `tensix.wait unpack`
before releasing its input CB, and `tensix.wait pack` before publishing its output
CB. Engine-local stalls still express math/source-bank/Dst dependencies.

## 12. Completion criteria for this design

Before calling this a final specification, resolve the multicast arrival protocol,
the unpack base/context credit protocol, runtime shared-config handoff, and the
complete math/SFPU signature/default table. Select and document the remaining
target-specific numeric, alignment, and resource bounds.

Then require:

- Parseable complete embedding, O, attention-merge, and multicast examples in the
  chosen syntax; no placeholders presented as compilable code.
- A schema entry for every public operation: signature, operand kinds, defaults,
  units, effects, completion, owner, resource use, lowering, and diagnostics.
- Protocol tests for CB wrap/retention, delayed pack/unpack, multiple NoC requests,
  atomics with reused response storage, delayed multicast receivers, repeated
  generations, zero work, and return with outstanding work.
- Numerical tests and ports for every shipped family/variant, including partial
  attention blocks and scalar outputs, followed by matched performance comparison.
- A readable listing and memory/resource report that account for all generated
  setup, polling, fences, and bookkeeping. No hidden data movement or spilling.

These are compiler/runtime implementation obligations derived from the language.
Current firmware addresses, reset habits, and code-slot sizes do not decide them.
