# ttptx v1: explicit pipelines, managed hardware configuration

Design proposal, not an implemented syntax or a claim that the existing samples compile.

ttptx v1 is a structured assembler for Blackhole. The author writes one program and chooses data flow,
buffer ownership, and synchronization. The assembler chooses registers and emits hardware configuration,
address setup, instruction encodings, local hazard stalls, and protocol boilerplate.

The first goal is to replace configuration writes and repetitive RISC-V sequences in the old kernels.
There are no per-RISC sections, duplicated loops, or user-assigned RISC roles. Operation classes have
fixed routing rules, and structured control flow is mechanically projected onto the participating RISCs.
The assembler emits the five images and launch manifest as implementation details. General scheduling
and software-pipeline synthesis are not prerequisites for compiling a kernel.

## 1. Author/compiler boundary

| Author specifies | Assembler supplies |
| --- | --- |
| One program of engine-specific operations | Fixed operation routing, image generation and launch ABI |
| Byte buffers and CB storage budgets | L1 addresses, CB counters, pointer arithmetic and wrap |
| Copies and explicit completion waits | NoC requests, page/bank splitting, transaction IDs, counter handling |
| Source-bank publication and release | Dvalid protocol and independent SrcA/SrcB bank advancement |
| Dst ownership handoff | Semaphores and completion ordering |
| Unpack/pack format and geometry | Descriptors, configuration writes and address counters |
| FPU/SFPU instructions and numeric policy | Physical register allocation, legal encodings and local hazards |
| Structured loops and optional templates | RISC-V branches, address expressions, MOP/replay programming |

No general alias analysis, pipeline synthesis, arbitrary cross-RISC scalar communication, or implicit
spilling is required. Replication is limited to pure scalar expressions over parameters and loop indices.
Unsupported schedules produce diagnostics rather than an attempted clever lowering.

## 2. One program, fixed operation routing

```ptx
.visible .entry example (.param .dram input, .param .dram output,
                        .param .u32 chunks) .cores 1
{
    // Buffers and register declarations.
    loop %i = 0, chunks {
        // Read, unpack, compute, pack and write in one loop.
        // Explicit waits and ownership operations connect those stages.
    }
    exit;
}
```

The author writes each loop once. V1 assigns operations by a fixed table:

| Operation | Internal issuer |
| --- | --- |
| DRAM/remote-to-L1 `cp.async` | Reader (initially BRISC) |
| L1-to-DRAM/remote `cp.async` | Writer (initially NCRISC) |
| `cp.wait` | Issuer of the named copy token |
| `unpack.*`, `src.acquire`, `src.publish` | Unpack (TRISC0) |
| `fpu.*`, `sfp.*`, `src.wait`, `src.release`, `dst.acquire`, `dst.publish` | Math (TRISC1) |
| `pack.*`, `dst.wait`, `dst.release` | Pack (TRISC2) |
| `cb.reserve`, `cb.push` | Producer endpoint determined by the operations filling that CB |
| `cb.wait`, `cb.pop` | Consumer endpoint determined by the operations reading that CB |

These names describe lowering, not source annotations. Each CB endpoint must have one unambiguous owner.
For example, a copy-filled/unpack-consumed CB routes its producer operations to reader and its consumer
operations to unpack. Ambiguous or multiple-owner endpoints are rejected in v1.

For every RISC, retain its operations in source order and retain the enclosing loops/conditions needed
to reach them; discard empty control-flow bodies. Recompute required pure scalar expressions from launch
parameters and induction variables locally. This is a restricted syntactic projection, not a search for
an optimal loop partition. The same logical loop may have different iteration progress on different
RISCs; explicit CB and register handoffs supply backpressure and match the iterations.

Source order preserves order within each routed stream. It is not a global barrier between engines.
Cross-engine ordering comes from the explicit protocols below, rather than an inferred memory dependency.
`cp.wait` followed by `cb.push`, and the matching `cb.wait` before unpack, establishes the input handoff.

Initially, shared loop bounds and conditions must depend only on parameters and pure scalar expressions
over enclosing induction variables. A loaded scalar can drive operations/control flow on its own routed
stream (embedding's token-ID load and subsequent DRAM read, for example). A data-dependent value needed
by another stream requires an explicit synchronized scalar transfer; reject it until that transfer is
supported. Do not replicate memory loads or side effects as if they were pure expressions. Scalar loads
through a CB lease belong to its consumer; other scalar memory operations require a unique owner derived
from their local uses, or are rejected. This keeps placement constrained and diagnosable.

FPU and SFPU prefixes name engines. V1 fixes their issuing stream instead of asking the author to choose
a RISC. The half-pipelined RMSNorm's SFPU-on-TRISC2 schedule can be a later scheduling extension; the eight
LRegs and SFPU configuration remain shared hardware state.

## 3. Memory and circular buffers

There are two common ways to use L1 storage:

- **Stream:** read a chunk of this core's assigned DRAM region, consume it, and reuse the L1 space for
  another chunk. Repeat until that assigned region is exhausted. Each chunk needs both a "ready to read"
  handoff and a "finished using it; safe to overwrite" handoff.
- **Load once and retain:** read a buffer into this core's L1, wait for it to arrive, and reuse it throughout
  the computation. Keep its storage occupied until the final use. This needs one initial readiness handoff,
  not a push/pop on every use. The retained buffer must fit in the available L1 budget.

The distinction is how long data is kept, not whether it contains weights or activations. V1 implements
both with the same CB operations: repeated publication/consumption for a stream; publish once, wait once,
and hold until done for a retained buffer. No separate stream, latch, batch, or feedback type is required.
A plain L1 allocation provides storage only; the CB adds the explicit ownership protocol.

Memory declarations allocate bytes, with no tile type:

```ptx
.l1 .b8 scratch[4096];
.cb input_q  .block_bytes 2048 .capacity_bytes 4096;
.cb output_q .block_bytes 2048 .capacity_bytes 4096;
```

V1 defaults L1/CB allocation bases to 64-byte alignment; ordinary declarations need no `.align` qualifier.
This is a conservative allocator policy for DMA staging, not the minimum addressable unit of L1. Scalar
byte accesses remain legal. Allocation alignment does not establish legality of every offset: the old
Blackhole DRAM-read probe records source/destination congruence modulo 64, including successful nonzero
offsets. Copy lowering must still check the actual addresses. The 2048-byte blocks above preserve the base
alignment at every slot; other block sizes require their own transfer checks.

A CB is a single-producer, single-consumer FIFO backed by allocated L1 bytes. Its block is a protocol unit,
not a compute tile or a storage format. `block_bytes` is fixed; `capacity_bytes` is a positive multiple of
it. A block can contain a vector segment, packed matrix data, or scalar records. The initial implementation
requires block sizes/alignment compatible with the chosen transfer path; more general padding is explicit.

There is no `.depth 2` loop annotation and no exposed source-bank number. Explicit CB storage does still
need a memory budget: the example above has room for two blocks because 4096 / 2048 = 2. That capacity is
chosen by the author in this explicit v1; automatic capacity selection can be added later. It is not a
promise that the compiler will discover two-iteration overlap.

| Operation | Contract |
| --- | --- |
| `cb.reserve %p, q` | Wait for one free block; return a producer-owned L1 pointer |
| `cb.push q` | Publish that block to the consumer and advance the producer |
| `cb.wait %p, q` | Wait for one published block; return a consumer-owned L1 pointer |
| `cb.pop q` | Return that block's storage to the producer and advance the consumer |

Only one outstanding reservation/claim per endpoint in v1. Pointers are scoped leases: `%p` from reserve
expires at push, and `%p` from wait expires at pop. Both endpoints may have different blocks leased at
once. Multi-block reservations/claims and wrap-spanning ranges can be added later.

`cb.push` does not wait for an outstanding copy or pack. `cb.pop` does not wait for an outstanding read of
the block. The author must explicitly complete those operations first. The assembler checks associated
tokens where their storage provenance is known and emits publication/acquisition memory ordering.

A plain `.l1` array has no readiness or ownership protocol. Sharing it across routed engines requires an explicit
handoff. V1 can use CBs even for one-time transfers: claim once, then retain the lease until the final use.
Broadcast/multiple-consumer CBs and remote CB credits are outside the initial local SPSC subset.

### Unpack with optional consumption

Unpack can name a CB directly instead of a pointer. An optional `consume` modifier says that this is the
last read of the current block and its storage can be released after unpack completes:

```ptx
unpack.bf16 %a, [weights] consume;           // read the front block, then release it
unpack.bf16 %b, [resident_x + %feature*2048]; // read a region and retain the block
```

Here `weights` and `resident_x` are declared CB names. Offsets are in bytes within the current block,
not indices into future FIFO slots. For a retained vector containing several tiles, declare one block
large enough for the vector and select its regions with byte offsets. Every unpack footprint must fit
within that block and satisfy the unpack operation's alignment and geometry requirements.

This is shorthand over the existing consumer protocol, not a special reusable CB:

- A direct CB operand with no current consumer claim waits for a published block and claims it, just
  like `cb.wait`. If this consumer already holds the block, the operand reuses that claim.
- Without `consume`, unpack leaves the claim and front pointer unchanged. Repeating the same address
  reads the same data. The author still writes `unpack.wait` before source publication as usual.
- With `consume`, the operation includes unpack completion followed by `cb.pop`. It releases the whole
  CB block, even if the unpack reads only a region. No outstanding read of that block may survive release.
  All pointers into the released block expire, including a pointer obtained by an earlier explicit wait.
- A retained block can be released by `consume` on its final unpack, or by an explicit `cb.pop` after all
  reads complete. It must be released before exit under the existing lease rules.

For example, with no existing claim, this:

```ptx
src.acquire a;
unpack.bf16 %a, [weights] consume;
src.publish a;
```

expands to the following consumer-side operations (the pointer is compiler-generated):

```ptx
src.acquire a;
cb.wait %temporary, weights;
unpack.bf16 %a, [%temporary];
unpack.wait a;
cb.pop weights;
src.publish a;
```

Source-bank acquisition/publication and math's source wait/release remain explicit. Releasing L1 after
unpack finishes is safe even while math has yet to consume the separate source-bank copy. `consume`
does not release that source bank or dst. Ordinary pointer-based unpack retains its existing semantics;
v1 accepts the modifier only on a named CB operand, so the released queue is unambiguous.

Keeping one operand while consuming another is expressed independently, for example retaining Q while
consuming K, or retaining X while consuming weights. V1 can spell these as separate unpacks into A and B;
any future combined unpack form must preserve the per-input choice. A held block needs only its original
publication, not a new push on each read. This replaces attention's existing repeated publication of
unchanged Q bytes, which accommodates an unpack helper that always pops both inputs.

Consumption grants the producer permission to reuse storage; it does not itself issue a NoC request.
The reader's explicit loop fetches the next chunk when space is available and stops at its specified
count. A pack-produced CB instead gets its next contents from pack. CBs drained by a writer still use
`cp.wait` followed by `cb.pop`; unpack shorthand does not change those lifetimes.

The assembler tracks whether a consumer claim is held at each operation, including across loop
iterations. It rejects ambiguous ownership at control-flow joins and checks that no asynchronous use
outlives consumption. The explicit `cb.wait` / pointer unpack / `unpack.wait` / `cb.pop` form remains
available whenever the author wants to spell out the same schedule.

### Load once, use repeatedly

This fragment loads 4096 bytes once and retains them across a computation loop. The consumer-side body
is illustrative; it must include the explicit source/dst protocols required by its compute operations.

```ptx
.cb resident .block_bytes 4096 .capacity_bytes 4096;
.reg .ptr.l1 %write_ptr, %read_ptr;
.reg .copy %load;
.reg .u32 %i;

// Reader: fill and publish once.
cb.reserve %write_ptr, resident;
cp.async %load, [%write_ptr], [weights], 4096;
cp.wait %load;
cb.push resident;

// Unpack: claim once, then repeatedly read the same L1 bytes.
cb.wait %read_ptr, resident;
loop %i = 0, uses {
    // Unpack the needed regions of [%read_ptr], with explicit source handoffs.
    // Complete each unpack before publishing the source bank to math.
    // Math consumes the source data under the usual src/dst protocols.
}
// All unpack reads from this buffer must have completed before this release.
cb.pop resident;
```

The reader does not refill this buffer on each iteration. Holding its L1 lease does not require holding
a source bank or dst for the same duration: those have separate handoffs. The final pop belongs to the
consumer engine and follows its final completed read; it is not a barrier for all five RISCs. It closes
the lease even when the storage will not be reused before kernel exit.

### Streaming and other uses of the same protocol

Section 7 shows a stream: reserve/copy/wait/push and wait/use/pop repeat inside an explicit loop. The
launch parameters and address expressions specify this core's assigned DRAM range. The loop count
specifies when it ends; a CB has no implicit end-of-stream marker. That example requires a whole number
of fixed-size chunks. A partial final chunk needs explicit handling and must not read past the buffer.
Declaring a CB does not implicitly wrap the rest of the kernel in a loop.

"Batch" simply means handing over several compute tiles together. A single CB block can contain them
all; block size is independent of compute tile size. It does not require a new buffer type.

"Feedback" means that compute results are packed into L1 and later unpacked for more computation, such
as attention probabilities used in the multiplication by V. The same CB protocol connects pack to unpack.
This is a data-flow pattern, not a new declaration or an implicit scheduling feature. Supporting a kernel
with this pattern still requires its compute operations and an explicitly workable ordering of handoffs.

Matching producer/consumer counts alone does not guarantee progress. For example, one reader producing
all X chunks before any gamma chunks can fill a small X queue and block while unpack waits for gamma.
Interleave production to match consumption, or explicitly provide enough storage for the chosen order.
Future stream shorthand must preserve a specified producer order and explicit completion/ownership
semantics. Inferring releases from the last pointer mention is insufficient when an operation is async.

## 4. Copies have completion tokens

```ptx
.reg .copy %read;
.reg .ptr.l1 %p;

cb.reserve %p, input_q;
cp.async %read, [%p], [input + %i*2048], 2048;
cp.wait %read;
cb.push input_q;
```

`cp.async` issues a byte copy and returns a token naming the entire logical transfer, including all NoC
requests needed to split it across pages/banks. It does not make the data ready merely by returning.
`cp.wait` waits for completion and consumes the token. For reads, completion means L1 data is available;
for writes, the conservative v1 wait includes destination acknowledgement. The assembler handles the
required local ordering around issuing and observing transfers.

Several distinct tokens can be outstanding and waited individually. An implementation can conservatively
serialize requests when transaction resources are scarce. No unbounded transaction allocation is required.
Control flow must not overwrite or abandon a live token. `exit` requires no outstanding tokens or leases;
it is not an implicit catch-all wait.

The source of an asynchronous copy must remain unchanged and allocated until its wait completes. The
destination must not be read or overwritten before completion. The usual output sequence is therefore:

```ptx
cb.wait %p, output_q;
cp.async %write, [output + %i*2048], [%p], 2048;
cp.wait %write;
cb.pop output_q;
```

A later extension may distinguish source-reusable/departed from destination-visible/landed completion.
V1 deliberately uses the stronger wait so the ownership rule is simple. Interleaved DRAM pointers carry
buffer metadata; the assembler lowers byte offsets and diagnoses unsupported address congruences. It must
not silently round a copy outwards and read/write beyond the specified extent.

## 5. Source allocations and whole-bank handoffs

```ptx
.reg .srca.bf16 %a[64];
.reg .srcb.bf16 %b[64];
```

Each physical source has two banks of 64 rows of 16 datums. Row regions can be smaller than a whole bank,
but ownership transfers for the entire bank. SrcA and SrcB have independent handoffs. Matmul requires an
aligned 16-row SrcA operand and an aligned 8-row SrcB operand; eight-row granules are not universal shapes.

V1 makes the bank lifetime explicit without naming bank 0/1:

```ptx
// All of this appears together in the one program:
src.acquire a;                     // next A bank is available to unpack
unpack.bf16 %a[0:+64], [%p];
unpack.wait a;                      // finish reading L1 and writing this bank
src.publish a;                     // hand the bank to math; advance unpack's A bank
cb.pop input_q;                    // the L1 bytes are no longer in use

src.wait a;                        // next A bank is available to math
fpu.mov %d[0:+64], %a[0:+64];
src.release a;                     // finish source reads; return bank; advance math's A bank
```

`a`/`b` are protocol endpoints for physical SrcA/SrcB, not virtual value names. Multiple declared regions
of the same source receive disjoint, statically assigned row ranges within a bank. They share each
acquire/publish/wait/release cycle. The author fills the required regions before publishing and completes
all uses before releasing. Allocations do not survive release into the next cycle.

Start with static source placement across a kernel: no lifetime-based packing of unrelated source regions
and no implicit reloading of values. Eight 8-row regions fit in one bank; a 16-row region consumes twice
that space and has the alignment required by its users. Unused rows are not implicitly initialized.

`unpack.wait a`/`b` are logical engine-completion operations, not promises of a single hardware instruction.
The lowering includes necessary drains and documented workarounds. `src.release` is a completion handoff,
so its lowering waits for queued FPU reads before giving the bank back.

## 6. Dst ownership and SFPU registers

```ptx
.reg .dst.f32 %d[64];
```

The initial subset uses one dst width per kernel and a single whole-dst math-to-pack handoff:

| Math operations | Pack operations |
| --- | --- |
| `dst.acquire` waits until math owns dst | `dst.wait` waits for a math publication |
| Compute into declared dst regions | Pack selected regions |
| `dst.publish` completes preceding writes and hands dst to pack | `pack.wait` completes L1 writes and dst reads |
| | `dst.release` returns ownership to math |

Initially dst is available to math. This protocol neither zeroes nor invalidates its contents. Explicit
initialization is required. Distinguish `fpu.zeroacc` (accumulator validity semantics) from an SFPU store
of numerical zeros. `pack` does not destroy its source. Math can reacquire persistent state after pack
releases it. Whole-dst exclusion sacrifices overlap to keep the first implementation straightforward;
half-dst ownership and direct-unpack-to-dst ownership are subsequent extensions.

SFPU values are virtual 32-lane registers:

```ptx
.reg .sfp %v, %sum, %scale;
sfp.ld.f32 %v, %d[0].even;
sfp.add.f32 %v, %v, %scale;
sfp.st.f32 %d[0].even, %v;
```

Ordinary `.even`/`.odd` accesses cover the respective columns of four rows. Require an aligned four-row
base and a footprint entirely within the allocation. Virtual names map to the eight writable LRegs,
respecting fixed/pair constraints. V1 errors on excess live registers and does not spill implicitly.
Small library functions inline before allocation. LRegs are shared hardware state, not per-RISC registers.

Within the math stream, dependent FPU/SFPU operations have sequential semantics. The assembler inserts
local stalls/NOPs, including FPU-write to SFPU-read ordering. This is bounded instruction scheduling,
not inference of missing cross-engine synchronization. Initially it may serialize engine transitions.

## 7. Complete streaming example

This copies `chunks` segments of 1024 BF16 values through src and FP32 dst back to BF16 L1/DRAM. It is a
pipeline demonstration, not a bitwise-copy primitive or an optimized identity kernel. The buffers are
nonaliasing and contain `chunks * 2048` accessible bytes. `pack.bf16` uses a specified native conversion
policy; it must not silently claim PTX nearest-even semantics.

```ptx
.visible .entry stream_example (.param .dram input, .param .dram output,
                               .param .u32 chunks) .cores 1
{
    .cb incoming .block_bytes 2048 .capacity_bytes 4096;
    .cb outgoing .block_bytes 2048 .capacity_bytes 4096;
    .reg .srca.bf16 %a[64];
    .reg .dst.f32 %d[64];
    .reg .u32 %i;
    .reg .ptr.l1 %in_write, %in_read, %out_write, %out_read;
    .reg .copy %read, %write;

    loop %i = 0, chunks {
        cb.reserve %in_write, incoming;
        cp.async %read, [%in_write], [input + %i*2048], 2048;
        cp.wait %read;
        cb.push incoming;

        cb.wait %in_read, incoming;
        src.acquire a;
        unpack.bf16 %a, [%in_read];
        unpack.wait a;
        src.publish a;
        cb.pop incoming;

        dst.acquire;
        src.wait a;
        fpu.mov %d, %a;
        src.release a;
        dst.publish;

        cb.reserve %out_write, outgoing;
        dst.wait;
        pack.bf16 [%out_write], %d;
        pack.wait;
        dst.release;
        cb.push outgoing;

        cb.wait %out_read, outgoing;
        cp.async %write, [output + %i*2048], [%out_read], 2048;
        cp.wait %write;
        cb.pop outgoing;
    }
    exit;
}
```

The reader waits for each segment before publishing it, but may then fetch the next while unpack/math/pack
work on earlier segments. CB capacity supplies backpressure. Copies need not all be simultaneously
outstanding to overlap transport and computation. Each token covers one iteration's transfer; there is no
inferred connection between a loop and a hidden FIFO.

RMSNorm uses the same structure: the reader pushes x and gamma chunks in a specified order; unpack sends
them through A; math copies them into persistent `%x[128]` and `%g[128]` under one dst acquisition, runs the
two SFPU passes, then publishes once. Pack produces two BF16 output chunks before releasing dst, and the
writer drains them. The source handoff count differs from the dst handoff count deliberately and visibly.

## 8. Configuration and repetition

Every operation declares required formats, geometry, read/write footprints, and affected engines. The
assembler emits a known lowering recipe. Start with safe configuration at each operation; eliminate
redundant writes within straight-line regions only when the state is known. At control-flow joins, use
the intersection of known states or reconfigure. Correctness must not depend on global optimization.

Shared configuration fields have an assigned owner. A write that changes another live engine's
interpretation requires an explicit ownership boundary; v1 rejects incompatible concurrent configurations.
Do not let independently cached per-thread configuration states assume shared registers are private.

Ranges have documented expansions: an aligned 64-row A-to-dst move uses eight eight-row MOVA2Ds, plus
necessary setup/ordering. Ordinary loops lower to device loops. The user never writes MOP configuration
registers. Initially ranges can use fixed recipes or direct instructions; optimal MOP synthesis is optional.
Explicit replay/MOP/SFPU-macro templates can retain a declarative form with checked resource allocation,
but need not be implemented before the basic kernel path works.

The listing should show source operations alongside expanded instructions, inserted waits/configuration,
register assignments, and allocated L1 bytes. This makes both cost and synchronization reviewable.

## 9. Validation and implementation order

First implement local SPSC CBs, explicit copy tokens, independent source handoffs, whole-dst ownership,
BF16 contiguous unpack/pack, FP32 dst, FPU moves/elementwise operations, and basic SFPU operations.
Use streaming copy, a load-once buffer reused across a loop, and naive RMSNorm as initial end-to-end
examples. Support scalar L1 loads/stores and integer address arithmetic for embedding. Scalar load width
does not change byte-based pointer arithmetic.

Check region bounds/alignment, register capacity, token completion, lease use after release, permitted
operation routing, and balanced local protocol operations. Protocol endpoints in the same structured
loop inherit its count without the author duplicating that loop. Check compatible counts across distinct
loops where possible, and reject shared control flow that cannot be projected under section 2's rules.
V1 does not promise to prove freedom from every deadlock, including cycles between multiple FIFOs.

Next add matmul geometry/fidelity, strided transfers, packer L1 accumulation, direct unpack-to-dst,
numerical conversions, and BFP block descriptors. BFP stored-block geometry is separate from the subset
of rows accessed. Then add remote credits/multicast and finer dst ownership. These are required for the
broader old-kernel inventory, but not for the first useful compiler.

Only after explicit pipelines work should a higher-level frontend introduce CBs, choose capacities,
choose alternative issuing RISCs, transform loops beyond the fixed projection, or pipeline multiple copy
tokens. tinygrad targets v1 by generating one structured program with explicit transfers and protocols.
It never has to generate separate RISC programs. The explicit form remains the lowering target and the
way to inspect or tune a schedule.
