# ttk data/effect graph

`ttk` is a trace-only frontend. `ttko` remains the executable reference.
Device lowering, instruction scheduling, synchronization insertion and launching
are future work. The authored graph contains no `RING_*` or `WAIT` operations.

## Storage and items

`DEFINE(spec)` is a source-free logical storage declaration. `RingSpec` describes
L1/SrcA/SrcB storage with item size, depth, dtype and optional CB slot/alias;
`StorageSpec` describes Dst or register storage. Trace-local allocation identities
keep equally sized allocations distinct. These identities are not L1 addresses.

An occupancy is `INDEX(storage, seq)`. Its physical slot will be `seq % depth`.
The sequence is a bounded integer expression: a constant outside loops, or
mixed-radix arithmetic over RANGE indices. Multiple items per iteration, nested
loops, and work before/after loops are numbered continuously from zero. Sequence
construction placeholders are resolved before the graph is returned.

A subview is `INDEX(INDEX(storage, seq), offset)`. L1 item extents/offsets use
bytes; source and Dst subviews use 128-element blocks. Full items need only the
occupancy INDEX. L1 defaults to 2048 BF16 bytes and depth 3. Source storage uses
at most eight blocks per item and depth 2.

```python
inputs = cb.read(activations, capacity=2)
a_storage = cb.alloc(kind='SRCA')
scratch = dst.alloc(8)
def tile(i):
    item = inputs.next()
    a = a_storage.acquire()
    unpack(item, into=a)
    fpu.move(a, into=scratch)
loop(tiles, tile)
```

The graph describes `NOC_READ → UNPACK → MOVE` using INDEX/AFTER dependencies.
`acquire()` creates a frontend item handle; it emits no reservation operation.
`consume()` is a compatibility readiness check. `release()` closes a frontend
handle but emits no node and is optional. Local handles close automatically at
their loop boundary, and cannot escape the region. Unused item handles do not
consume sequence numbers. Dst allocation remains outside loops.

`cb.read(weights, resident=True)` uses depth equal to item count, so no occupancy
reuses a physical slot. Streams derive DRAM offsets from the same sequence as
the storage item. Bounds and stream exhaustion are checked across the expanded
finite execution, including nested loops and multiple `next()` calls.

## Dependencies and verification

`AFTER(storage, operation)` forwards storage while requiring the operation's
result. For example, the reader is:

```text
r = RANGE(CONST(tiles))
a = INDEX(cb0, r)
read = NOC_READ(input, r*2048, a)
UNPACK(INDEX(AFTER(cb0, read), r), INDEX(dst, r*8))
```

The operation itself expresses the completion requirement. There is no WAIT
wrapper, and no synthetic previous-operation edge for a logical queue. Later
lowering can choose engine waits, source-bank handoffs, CB counters, barriers
and NoC semaphores from these dependencies and placement. None is inserted yet.

`ttk.memory` classifies each issue's storage reads and writes and infers:

- RAW dependencies between writers and readers of the same occupancy/version.
- Ordering of occupancy sequences on each producer/consumer side.
- WAR/capacity dependencies from every reader of `seq-depth` to the next write
  reusing its slot. A write cannot overwrite an unread occupancy.
- Read-modify-write and alias hazards for depth-one partial outputs.

The verifier privately expands static loops, checks sequence coverage from zero,
DRAM/subview bounds, initialization and layout agreement, and rejects cycles
through inferred hazards and authored dependencies. Sequence order supplies FIFO
constraints even when independent graph branches are discovered out of order.
Repeated reads of one item share the same producer-version INDEX but remain
separate operations; capacity reuse waits for all of them. Explicit Python `release()` placement does not affect these facts.

This checks the modeled finite execution, not general device safety. Partial item
writes, runtime loop trip counts, physical placement and cross-launch state are
not modeled. Expansion is limited to 200000 execution nodes.

## Structured loops and pure nodes

`loop(n, body)` traces one body. Each terminal has `END(terminal, range)`; only
the graph root is a SINK. A resource exposes its own final effect through END,
for example `AFTER(dst, END(UNPACK(...), r))`, without depending on sibling work.
`linearize` groups sibling ENDs at one closing boundary; expansion closes a
range after all of them. Nested loops remain contiguous and close directly as
`END(inner_end, outer_range)`, without forwarding the outer index through AFTER.

`RANGE.src[0]` is always the integer bound (a CONST for the current frontend).
An inner RANGE has its outer range in `src[1]`: `RANGE(bound, outer_range)`.
The optional loop name is the only entry in `arg`. Bounds analysis reads the
bound operand; finite expansion still requires a statically known positive
count. This reserves the bound slot for runtime counts without implementing
runtime loop lowering.

`carry=` uses a source-free register DEFINE, an initial STORE, and
`LOAD(AFTER(reg, initial_store))` inside the loop. Its final read is
`LOAD(AFTER(reg, END(final_store, range)))`. ENDs feed AFTER, the root SINK,
or another END when closing nested loops. Zero-trip loops preserve the initial
carry and omit the body.

Nodes inherit region membership from their operands. Independent work gets
`AFTER(first_operand, range)` only when needed, preserving operation arity.
CONST, PARAM, DEFINE, arithmetic, INDEX and AFTER are hash-consed within a trace.
Integer `x+0`, `0+x`, and `x-0` fold during construction; floating-point signed
zero remains distinct. `after()` flattens existing AFTER wrappers and deduplicates
dependencies: `AFTER(AFTER(reg, store), range)` becomes `AFTER(reg, store, range)`. LOAD, STORE, other issues and RANGE retain occurrence
identity. These construction rules are not device optimization passes.

## Launch arguments and remote roles

`Buffer(name, dtype, nbytes)` describes a runtime u32 DRAM address.
`Param(name, Dtype.i32/u32, lo, hi)` describes a bounded runtime scalar (inclusive
bounds). Parameters support symbolic offsets and `Kernel.bind()` validates the
supplied values without specializing or launching the graph.

`cb.alloc(slot=0, producer='remote', ...)` describes local storage filled by a
peer. `storage.receive(sender=(sx, sy), after=optional_operation)` creates the
next item handle. The sender coordinates are constants or bounded scalar
parameter descriptors in the storage spec; the corresponding PARAMs remain in
the launch ABI. An explicit receive thread is retained as endpoint metadata for
future placement. No local receive/acquire/wait issue is fabricated.

`cb.peer('a', receivers=n, coordinates=(x0,y0,x1,y1,sx,sy), slot=0, ...)` describes
a peer destination. `noc.multicast(item, peer)` is a NOC_WRITE from the local
item to `INDEX(peer_storage, same_seq)`. Multicast coordinates remain ordinary
graph operands. Local and peer slot/depth/layout must match.

`verify_roles({participant: kernel}, connections)` composes concrete participants.
`Connection(sender, group, receivers)` wires one producer group to its peers;
the same Kernel may be reused under multiple participant names without retracing.
The checker requires unique complete wiring, matching layouts/receiver counts,
matching occupancy sequences and loop shapes, then checks remote credit and data
availability hazards together with local capacity. Credit markers exist only in
this private model. Rectangle membership, actual sender coordinates and L1
addresses still require future launch validation.

`noc.write(..., noc=0, after=operation)` and `receive(after=operation)` express
real ordering requirements through AFTER. Thread placement alone implies none.
The `ttk.sketches.matmul_peak` example builds eight role templates for A row
multicast, B column multicast and output NoC selection. It remains a one-output-
tile-per-core example with explicitly unrolled K blocks. Full reference DRAM
addressing, the performance schedule, FP8 and writer-wave barriers are not ported.

## Accumulation, aliases and fringes

`pack(dst, into=item, accumulate=True)` reads/modifies the same initialized
local depth-one occupancy and returns its replacement handle. The old handle is
closed; the graph has another PACK on the same sequence, dependent on the prior
version through AFTER. Uninitialized accumulation is rejected.

`storage='output'` declares a storage alias, such as CB24/CB16.
`partial.handoff(output_storage)` exposes the original data under the output
identity through AFTER, without a copy or protocol operations. Alias layouts
must match and have depth one; conflicting initializing writes are rejected.

`fpu.op('mvmul', ..., shape=(m,n,k))` preserves extents in [1,32] for future
8×16 fringe/RWC lowering. No fringe instructions are emitted by the text renderer.

## Reviewing graphs

```sh
PYTHONPATH=. ../.venv/bin/python -m ttk.sketches.rmsnorm --stage graph
PYTHONPATH=. ../.venv/bin/python -m ttk.sketches.rmsnorm_hybrid --stage linear
PYTHONPATH=. ../.venv/bin/python -m ttk.sketches.matmul_peak
```

`repr(uop)`/`pretty()` show nested UOps with shared bindings; `dump()` shows a
numbered list. `--stage render --per-thread` projects the global order by thread.
The renderer displays authored dependencies, not executable synchronization.
