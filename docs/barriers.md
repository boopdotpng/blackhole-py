# Barrier and synchronization coverage

This is an implementation checklist for replacing the explicit synchronization
in `blackhole-py` with one injectable `Barrier` abstraction in
`blackhole-py-rewrite`.

The inventory was made from the current Python kernels under
`blackhole-py/examples/`, including the Llama 3 kernels and `matmul_peak.py`.
The helper implementations in `blackhole-py/ttk/` were also read to determine
what each call actually waits for. Generated tt-lang dumps, command-queue
firmware, host waits, and PCIe cache flushes are outside this inventory.

## Executive summary

The examples use seven synchronization families:

1. RISC memory ordering (`fence`).
2. Same-core RISC rendezvous and value events in shared L1.
3. Circular-buffer space/data flow control and publication.
4. NoC command-buffer backpressure and transfer-completion counters.
5. Cross-core NoC semaphores.
6. Tensix FIFO drains, resource hazards, and hardware semaphores.
7. Overlay stream state waits.

They can share one public `Barrier` class, but they are not interchangeable.
The barrier IR has to preserve at least:

- the **domain** being synchronized (RISC memory, L1, CB, NoC, Tensix, or
  overlay);
- the **condition** (equal, at least, zero, below a limit, semaphore not zero,
  resource idle, and so on);
- whether the wait is for **issue capacity**, **source-side departure**, or
  **end-to-end completion**;
- the **arrival/publication action**, if any;
- acquire/release ordering around the wait or publication;
- whether the barrier is one-shot or uses a phase/generation.

The existing [`Barrier`](../ttk/sync.py#L1) only implements a one-shot,
same-core L1 rendezvous. The other mechanisms already have partial lowerings in
`ttk/noc.py`, `ttk/cb.py`, and `ttk/tensix.py`; unification should reuse those
lowerings rather than duplicate them in `sync.py`.

## 1. RISC ordering, events, and rendezvous

### `fence`: ordering, not completion

The RISC-V `fence` orders RISC loads and stores. It appears before/after shared
state publication and inside polling loops. It does **not** by itself wait for
a NoC transfer, Tensix operation, CB producer, or another RISC.

This distinction should remain visible in the IR. A barrier lowering may emit a
release fence before publishing or an acquire fence after observing a value,
but a bare fence is not a replacement for a completion wait.

Representative source: polling helpers in
[`asm.py`](../../blackhole-py/asm.py#L605) and CB waits in
[`ttk/cb.py`](../../blackhole-py/ttk/cb.py#L112).

### One-shot all-party rendezvous

`init_barrier()` gives each of the three TRISCs one L1 word. A TRISC stores its
arrival flag, fences, and polls every party's word. This is the mechanism most
similar to a GPU thread/block barrier.

Representative sources:

- [`add1.py`](../../blackhole-py/examples/add1.py#L90)
- [`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L884)
- the rewrite's current [`Barrier.wait()`](../ttk/sync.py#L4)

Requirements for the unified barrier:

- known party count and local party index;
- release before publishing arrival and acquire after observing peers;
- an explicit one-shot contract, or phase/generation storage for reuse;
- initialization/reset ownership.

The value `1` implementation cannot be safely reused without a reset. The
RMSNorm kernels avoid a fast party overwriting state needed by a slow party by
allocating a distinct arrival array for every phase in
[`phase_barrier()`](../../blackhole-py/examples/llama3/rmsnorm.py#L212). A
reusable barrier needs a generation protocol or the same phase-separated
storage rule.

### One-way L1 value event

`signal_sync(addr, value)` publishes a value and `wait_sync_value(addr, value)`
polls until exact equality. The examples use this for pipeline hand-offs such
as:

- waiting until the softmax numerator has reached DRAM before reading it back
  in place ([`softmax.py`](../../blackhole-py/examples/llama3/softmax.py#L128));
- waiting for the second SwiGLU input publication
  ([`swiglu.py`](../../blackhole-py/examples/llama3/swiglu.py#L161));
- coordinating an attention RoPE copy
  ([`attn.py`](../../blackhole-py/examples/llama3/attn.py#L475)).

This is a producer/consumer event, not an all-party barrier. The unified form
needs configurable address, value/generation, comparison, and signal/wait
roles. Exact equality is intentional in the current helper, but an `at_least`
condition is safer for monotonic counters that may advance past the expected
value.

### Firmware/kernel lifecycle waits

TRISC prologues use byte-valued shared-L1 start flags (`wait8`) and BRISC uses
the matching release. Firmware also uses GO/DONE byte states. These are the
same general value-event lowering with an 8-bit load and a lifecycle-specific
address.

Representative source: [`Trisc.prologue()`](../../blackhole-py/examples/add1.py#L77).

Coverage needed: 8- and 32-bit values, configurable comparison, separate
signal and wait operations, and optional rendezvous arrival.

## 2. Circular-buffer synchronization

CB synchronization is a two-counter producer/consumer protocol. The counters
are 16-bit `received` and `acked` values, mirrored into per-CB MMIO sync
registers.

| Operation | Wait/publication | Meaning |
| --- | --- | --- |
| `cb_reserve_back(count)` | Wait until `capacity - (received - acked) >= count` | Producer backpressure: enough pages are free. |
| `cb_push_back(count)` | Publish the new `received` count | Producer makes filled pages visible. |
| `cb_wait_front(count)` | Wait until `received - acked >= count` | Consumer waits for enough pages. |
| `cb_pop_front(count)` | Publish the new `acked` count | Consumer releases pages to the producer. |

Implementation: [`blackhole-py/ttk/cb.py`](../../blackhole-py/ttk/cb.py#L112).
Representative use: [`add1.py`](../../blackhole-py/examples/add1.py#L181) and
[`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L2816).

### The critical deferred-publication variants

There are two ordering-sensitive variants that the current rewrite CB does not
cover:

- `cb_push_back(..., tensix_received=True)` publishes `received` with a
  Tensix-queued `TTSTOREREG`, ordered after packing. Publishing from the RISC
  immediately would let the consumer see a page before pack has completed.
- `cb_pop_front(..., tensix_ack=True)` publishes `acked` with a Tensix-queued
  `TTSTOREREG`, ordered after unpack. Publishing from the RISC immediately
  would let the producer overwrite a page still being consumed by unpack.

The implementation and rationale are in
[`ttk/cb.py`](../../blackhole-py/ttk/cb.py#L132) and
[`ttk/cb.py`](../../blackhole-py/ttk/cb.py#L199). The rewrite currently always
publishes immediately in [`ttk/cb.py`](../ttk/cb.py#L72) and
[`ttk/cb.py`](../ttk/cb.py#L98).

These must be first-class release modes in the barrier IR, for example
`publisher=RISC` versus `publisher=TENSIX_AFTER_PACK/UNPACK`. They cannot be
recovered later by adding a RISC fence.

## 3. NoC synchronization

NoC synchronization uses monotonic hardware counters and live gauges. A robust
abstraction should normally snapshot a counter **before** issuing a batch and
wait for `current - snapshot >= issued_count`. This is already the useful core
of [`_CounterTicket`](../ttk/noc.py#L37).

### NoC command-buffer ready

`noc_wait_cmd_ready(noc, buffer)` polls `CMD_CTRL == 0`. Every regular read,
write, and atomic issue path performs this wait.

It means only that the command buffer can accept/reuse command state. It does
not mean the prior transfer reached its destination. Treat it as issue
backpressure, not a transfer barrier.

Old implementation: [`ttk/noc.py`](../../blackhole-py/ttk/noc.py#L416).
Rewrite implementation: [`NoC._issue()`](../ttk/noc.py#L211).

### NoC completion points

| Completion condition | Old helper/example | What observation permits |
| --- | --- | --- |
| Read responses received reaches target | `noc_reads_flushed` | The requested read data has returned to local L1. |
| Non-posted write acknowledgements received reaches target | `noc_write_barrier` / `noc_wait_write_acks` | The destination-side write acknowledgement has returned. |
| Posted write requests sent reaches target | `_emit_posted_writes_flushed` | The request has left the source NIU; this is not a remote acknowledgement. |
| Non-posted write requests sent reaches target | `noc_nonposted_writes_flushed` helper | Source-side departure of non-posted writes, not acknowledgement. |
| Atomic responses received reaches target | `noc_wait_atomic_responses` | The requested atomic responses have returned. |
| Tagged read outstanding gauge becomes zero | `noc_async_read_barrier_with_trid` | All reads with that transaction ID are complete. |
| Tagged write outgoing gauge becomes zero | `_emit_trid_writes_sent` | All tagged write payloads have departed after the final command was accepted. |

Implementations and representative uses:

- counter helpers in [`ttk/noc.py`](../../blackhole-py/ttk/noc.py#L424);
- ordinary read and write barriers in
  [`row_copy.py`](../../blackhole-py/examples/llama3/row_copy.py#L55);
- atomic response wait in [`add1.py`](../../blackhole-py/examples/add1.py#L435);
- transaction-ID read barriers in
  [`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L1529);
- posted and tagged-write source-side waits in
  [`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L1113).

The rewrite already exposes most snapshot/delta forms as:

- `NoC.read_batch()`;
- `NoC.write_batch()` for posted requests sent;
- `NoC.write_ack_batch()` for non-posted acknowledgements;
- `NoC.atomic_batch()`.

The unified barrier should wrap the resulting ticket/batch completion, while
retaining the counter kind in its IR. Calling every one of these a generic
`noc_barrier` would hide unsafe substitutions.

### Transaction-ID setup and throttling

The matmul readers reset the per-TRID barrier counter before issuing tagged
reads, then wait for that TRID's outstanding count to become zero. The old NoC
layer also contains `noc_wait_trid_issue_safe`, which waits until a per-ID
outstanding gauge is below the safe issue limit, although no current example
calls it.

Coverage needed:

- reset/arm a TRID epoch;
- wait for a TRID gauge to reach zero;
- optionally wait for issue credit below a limit;
- do not represent counter reset itself as completion.

### Sentinel read after an overlay transfer

`_emit_overlay_remote_read_barrier()` issues a four-byte NoC read from the last
word of a remote overlay-transferred region and waits for its response. The
read is used as an ordering/completion sentinel before consuming the region.

Source: [`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L1354).

This can lower as a composite barrier: issue sentinel read, then use the normal
read-response ticket. The address and ordering assumption must remain explicit
in the spec.

## 4. Cross-core NoC semaphores

Physical worker cores do not share local L1, so cross-core rendezvous uses a
semaphore in one core's L1:

- `noc_semaphore_set` initializes/clears a local semaphore;
- `noc_semaphore_inc` performs a remote NoC atomic increment;
- `noc_semaphore_set_multicast` publishes a value to multiple cores;
- `noc_semaphore_wait` polls a local semaphore for an exact value.

The argmax reducer is the clearest example: each core writes its result to the
reducer, waits for the data write to be acknowledged, then atomically increments
the reducer semaphore. The reducer waits for `core_count` arrivals before
reading all results ([`argmax.py`](../../blackhole-py/examples/llama3/argmax.py#L139)).
Matmul uses the same mechanism for multicast data-ready handshakes
([`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L1341)).

The barrier representation therefore needs distinct `arrive`, `wait`, and
`arrive_and_wait` forms. It also needs a way to attach a prerequisite completion
edge: payload write completion/departure must occur before the semaphore signal
when the consumer will act on that payload.

## 5. Tensix synchronization

Tensix synchronization is instruction-pipeline synchronization. It is not a
RISC or core rendezvous even though the kernels sometimes use the word
"barrier" for it.

### Full instruction-buffer drain: `tensix_sync`

`tensix_sync()` writes and reads `PC_BUF_SYNC`, creating a synchronous drain of
the active TRISC's Tensix instruction stream. The examples use it before
reconfiguration, before publishing packed data, and at math/pack phase
boundaries.

Implementation: [`ttk/tensix.py`](../../blackhole-py/ttk/tensix.py#L316).
Representative uses: [`add1.py`](../../blackhole-py/examples/add1.py#L341) and
[`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L2689).

This needs `pipe/thread` identity in the barrier spec even though the Blackhole
MMIO address is shared.

### MOP configuration drain: `mop_sync`

`mop_sync()` uses `PC_BUF_MOP_SYNC` before changing the MOP configuration. It is
a narrower configuration hazard than a general software rendezvous and is
currently called automatically by `write_mop_cfg`.

Implementation: [`ttk/tensix.py`](../../blackhole-py/ttk/tensix.py#L302).
Rewrite implementation: [`Tensix.configure_mop()`](../ttk/tensix.py#L276).

### Unpack configuration handshake

Before changing an unpack context, kernels poll `PC_UNPACK_SYNC` until the busy
bits (`value & 0xfe`) are clear. They then update configuration and write zero
to `PC_UNPACK_SYNC` to commit/hand off the new state.

Representative source: [`add1.py`](../../blackhole-py/examples/add1.py#L187).
Rewrite helpers: [`wait_unpack_config_idle()`](../ttk/tensix.py#L313) and
`commit_unpack_config()` immediately below it.

Model this as a dedicated Tensix configuration barrier with wait and commit
operations, not as an arbitrary MMIO value wait at call sites.

### Tensix hardware resource hazards: `TTSTALLWAIT`

`TTSTALLWAIT(stall_resources, wait_for)` blocks selected issue resources until
the requested hardware resources/state are ready. The examples exercise these
stall resources:

- `TDMA`, `SYNC`, `UNPACK`, `THCON`, `MATH`, `CFG`, and `SFPU`;
- combined `SYNC | MATH | SFPU` for math-to-pack backpressure.

They wait on these resource/state bits:

- `THCON`, `UNPACK0`, `UNPACK1`, `PACK0`, `MATH`, `SFPU`, and `TRISC_CFG`;
- source-valid state `SRCA_VLD | SRCB_VLD`.

Observed dependency patterns include:

| Stalled issuer | Waited resource/state | Purpose in examples |
| --- | --- | --- |
| `UNPACK` | `TRISC_CFG` | Do not unpack until the RISC configuration write is visible. |
| `UNPACK` | `UNPACK0`, optionally `UNPACK1` and/or `THCON` | Serialize face unpack and wait for unpack/THCON retirement. |
| `MATH` | `SRCA_VLD | SRCB_VLD` | Do not start elementwise math until both operands are valid. |
| `SFPU` | `MATH` | Keep SFPU behind math production of DST data. |
| `SYNC` | `MATH | SFPU` | Wait for math/SFPU completion before publication or reuse. |
| `CFG` | `THCON`, `PACK0`, and/or `MATH | SFPU` | Protect configuration changes from active engines. |
| `THCON` or `SYNC` | `PACK0` | Wait for pack retirement before reuse/publication. |

Representative sources: [`add1.py`](../../blackhole-py/examples/add1.py#L261),
[`rmsnorm.py`](../../blackhole-py/examples/llama3/rmsnorm.py#L325), and
[`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L2666).

The unified barrier should accept typed stall and wait masks. These masks are
part of the dependency and should not be reduced to a generic "wait for math"
boolean.

### Tensix counting semaphores: `TTSEMWAIT/POST/GET`

The examples use two wait predicates:

- `STALL_ON_MAX`: wait for capacity before producing/posting;
- `STALL_ON_ZERO`: wait for data/permission before consuming/getting.

The semaphore protocols observed are:

| Semaphore | Producers/consumers | Protocol |
| --- | --- | --- |
| `MATH_PACK` | Math -> pack | Math waits for not-max and posts; pack waits for not-zero and gets. |
| `UNPACK_SYNC` | Unpack engine -> TRISC0 control | Wait/get or get after an unpack MOP completes. |
| `UNPACK_TO_DEST` | Unpack <-> math | Coordinates direct unpack into DST and subsequent math use. |
| `MATH_DONE` | Math <-> unpack | Coordinates DST reload/reuse phases. |

`TTSEMINIT` establishes the initial and maximum counts. Before reinitializing a
live semaphore, matmul drains the Tensix FIFO and polls the semaphore MMIO low
byte to zero ([`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L2563)).

Coverage needed: semaphore identity, initial/max values, wait predicate,
stalled resource mask, post/get operations, and a safe reinitialization
sequence.

### Tensix-ordered L1 publication

`TTSTOREREG` is used after pack/unpack stall points to publish CB counters from
inside the Tensix FIFO. This is the mechanism behind deferred CB publication,
but it is also a general ordering edge from a Tensix operation to an L1-visible
event. The barrier IR should be able to express `publish_after(resource)` and
lower it to this sequence.

## 6. Overlay stream waits

`matmul_peak.py` has two stream-state polling barriers:

- `_emit_overlay_wait_src_ready` waits for the stream source state to become
  `SRC_READY_WAIT_ALL_DESTS`;
- `_emit_overlay_wait_done` waits for the software phase-advance signal and for
  the outstanding word count to become zero.

Sources: [`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L1160) and
[`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L1174).

These are optional for a minimal non-overlay runtime, but they should be kept as
a distinct `STREAM_STATE` lowering if overlay matmul remains in scope. A generic
L1 wait is insufficient because the fields are packed MMIO state with multiple
conditions.

## Recommended unified representation

Use one `Barrier` façade over typed barrier specifications. One possible shape
is:

```python
Barrier(kernel, spec, party=None).wait()
Barrier(kernel, spec, party=None).arrive()
Barrier(kernel, spec, party=None).arrive_and_wait()
```

Where `spec` retains a kind such as:

```text
MEMORY_FENCE
L1_VALUE
L1_RENDEZVOUS
CB_SPACE / CB_DATA / CB_PUBLISH / CB_RELEASE
NOC_CMD_READY
NOC_COUNTER_DELTA
NOC_GAUGE
NOC_SEMAPHORE
TENSIX_DRAIN / TENSIX_MOP_DRAIN / TENSIX_UNPACK_CONFIG
TENSIX_HAZARD
TENSIX_SEMAPHORE
STREAM_STATE
```

This still gives kernels one injected `Barrier` concept while preventing the
IR from losing what is being synchronized. High-level named barriers can bind
the fixed details once, so kernel code remains GPU-like:

```python
barriers.init.arrive_and_wait()
barriers.input_pages.wait(count)
barriers.reads_complete.wait(ticket)
barriers.math_to_pack.wait()
```

`wait()` should lower through the owning subsystem (`CB`, `NoC`, or `Tensix`)
instead of making `sync.py` know every register address.

## Implementation priority

### P0: needed by ordinary add/elementwise/matmul kernels

- [ ] Preserve a standalone memory fence operation.
- [ ] Generalize L1 value waits/signals to 8/32-bit width and typed comparison.
- [ ] Make the all-party L1 barrier explicitly one-shot or generation-safe.
- [ ] Wrap CB reserve/wait/push/pop as barrier specs.
- [ ] Add Tensix-deferred CB `received` and `acked` publication.
- [ ] Wrap NoC read-response, write-ack, posted-write-sent, and atomic-response
      tickets without conflating their completion points.
- [ ] Wrap Tensix full sync, MOP sync, unpack-config wait/commit, resource
      stalls, and semaphore wait/post/get.

### P1: needed by distributed and optimized matmul kernels

- [ ] Add cross-core NoC semaphore arrive/wait and multicast publication.
- [ ] Support ordered payload-then-semaphore signaling.
- [ ] Add TRID counter reset, read completion, write departure, and issue-credit
      waits.
- [ ] Support safe Tensix semaphore reinitialization.
- [ ] Add reusable multi-phase barriers without stale-generation races.

### P2: needed if overlay transport remains in scope

- [ ] Add packed overlay stream-state predicates.
- [ ] Add the sentinel-read composite completion barrier.

## Correctness rules for lowering and tests

1. Never replace a NoC acknowledgement wait with command-buffer-ready or
   posted-write-sent.
2. Snapshot monotonic completion counters before issue and compare unsigned
   deltas; do not assume counters start at zero.
3. Drain/accept the final command before treating a zero live gauge as batch
   completion.
4. Emit release ordering before arrival/publication and acquire ordering after
   a successful shared-state wait.
5. Do not publish a CB page from the RISC when pack/unpack retirement is the
   true producer/consumer edge; use Tensix-ordered publication.
6. Do not reuse a value-based rendezvous without reset or generation handling.
7. Preserve Tensix stall-resource and waited-resource masks exactly.
8. Keep source-side NoC departure and remote completion as different barrier
   kinds in names, types, traces, and tests.
