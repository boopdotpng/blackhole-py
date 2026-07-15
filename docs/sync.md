# Explicit synchronization required by `matmul_peak`

This document inventories the synchronization needed to launch and execute
[`blackhole-py/examples/matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py).
It covers the default path and the grouped-K, transaction-ID, and overlay
variants present in that file.

The design rule for the rewrite is simple:

> Every synchronization point must remain a typed, explicit operation at the
> call site. Do not infer synchronization from Python order, buffer use, an
> AST, or a generic `Barrier` lowering pass.

There is a second, equally important visibility rule:

> If an operation can wait, release another worker, publish data, or permit
> storage/configuration reuse, it must be a standalone statement in the
> logical kernel function. Do not bury it inside `init()`, `read()`, `pack()`,
> `issue()`, or another innocent-looking helper.

There is no single hardware operation called "synchronize." The kernel waits
for different facts in different domains: RISC stores becoming ordered, CB
pages becoming available, NoC payloads leaving the source, NoC reads reaching
L1, remote cores publishing a semaphore, Tensix engines retiring work, and so
on. Those facts are not interchangeable.

This supersedes the generic-barrier recommendation in
[`docs/barriers.md`](barriers.md). That document remains useful as a broader
repository inventory, but the owning subsystem should expose each operation
directly rather than route it through a universal barrier facade.

## Kernel dataflow

One physical worker core runs five RISC kernels:

| Role | Matmul responsibility |
| --- | --- |
| BRISC | Read an A block from DRAM, distribute it across a worker row, then publish CB0. |
| NCRISC | Read a B block from DRAM, distribute it down a worker column, publish CB1, then drain CB16 to DRAM. |
| TRISC0 | Wait for CB0/CB1, unpack A and B, and optionally reload partial accumulations from CB24. |
| TRISC1 | Run math and publish destination-register tiles to TRISC2. |
| TRISC2 | Pack partial results to CB24 or final results to CB16. |

The physical cores do not share L1. Same-core RISC coordination can use shared
worker L1 or Tensix hardware state. Cross-core coordination must travel over
the NoC.

The default dataflow is:

```text
host/CQ
  -> worker firmware launch handshake
  -> BRISC releases TRISC0/1/2
  -> TRISC initialization rendezvous

DRAM A -> BRISC -> row multicast    -> CB0 -> TRISC0 unpack --+
DRAM B -> NCRISC -> column multicast -> CB1 -> TRISC0 unpack --+-> TRISC1 math
                                                               -> TRISC2 pack
                                         partial: CB24 ----------^    |
                                         final:   CB16 -> NCRISC -> DRAM C

all five worker RISCs return
  -> firmware completion handshake
  -> dispatch completion
  -> host observes completion
```

## Summary of explicit synchronization points

| ID | Domain | Explicit condition or action |
| --- | --- | --- |
| L1 | CQ/launch | Program and launch writes complete before GO is sent. |
| L2 | Firmware | BRISC, NCRISC, and TRISCs exchange LOAD/GO/DONE states. |
| L3 | Firmware/CB | TRISC0 clears all CB received/acked hardware counters before and after a launch. |
| L4 | RISC instruction coherence | Invalidate RISC instruction caches after replacing worker images and before entering them. |
| R1 | Same-core RISC event | BRISC clears init state and releases each TRISC through its own consumable start byte. |
| R2 | Same-core RISC rendezvous | TRISC0/1/2 publish one init flag each and wait for all three flags. |
| R3 | RISC memory ordering | `fence` orders publication and observation; it does not complete NoC or Tensix work. |
| C1 | CB producer backpressure | `reserve_back`: enough free pages exist. |
| C2 | CB data publication | `push_back`: received count advances after data is ready. |
| C3 | CB consumer availability | `wait_front`: enough received, unacked pages exist. |
| C4 | CB space release | `pop_front`: acked count advances after consumption. |
| C5 | Tensix-ordered CB publication | Pack/unpack enqueue `TTSTOREREG` so CB visibility is ordered after engine retirement. |
| N1 | NoC issue backpressure | Command buffer `CMD_CTRL == 0` before command state is reused. |
| N2 | NoC read completion | Global read-response target reached, or tagged-read outstanding gauge reaches zero. |
| N3 | Posted payload departure | Posted-write sent counter reaches the batch target. |
| N4 | Tagged payload departure | Final command is accepted, then the tagged outgoing-write gauge reaches zero. |
| N5 | Remote write acknowledgement | Non-posted write acknowledgement counter reaches the batch target. |
| N6 | NoC atomic response | Available as a distinct wait, although the matmul receiver-notify path does not wait for it. |
| X1 | Cross-core arrival | Receiver atomically increments a semaphore in the sender core's L1. |
| X2 | Cross-core data-ready event | Sender publishes a semaphore to receiver cores after multicast payload departure. |
| T1 | Tensix instruction drain | `PC_BUF_SYNC` drains one TRISC's Tensix instruction stream. |
| T2 | MOP configuration drain | `PC_BUF_MOP_SYNC` protects MOP reprogramming. |
| T3 | Unpack configuration handshake | Wait for `PC_UNPACK_SYNC` idle, write config, then commit the new context. |
| T4 | Tensix resource hazard | `TTSTALLWAIT` stalls named issue resources on named engine/resource conditions. |
| T5 | Tensix counting semaphore | `TTSEMWAIT`, `TTSEMPOST`, and `TTSEMGET` coordinate unpack, math, and pack. |
| T6 | Safe semaphore reinitialization | Drain Tensix, wait for the old semaphore value to become zero, then `TTSEMINIT`. |
| O1 | Overlay source readiness | Stream source state reaches `SRC_READY_WAIT_ALL_DESTS`. |
| O2 | Overlay transfer completion | Phase-advance signal is set and outstanding stream words reach zero. |
| O3 | Overlay sentinel read | A read of the last remote word returns before the destination consumes the region. |
| F1 | Worker completion | Firmware waits for every enabled subordinate RISC before notifying dispatch. |

Each row above should remain a distinct method or instruction sequence. In
particular, `N1`, `N3`, `N4`, and `N5` all mean
different things.

They must also remain visible where the kernel uses them. It is insufficient
for `noc.issue_read()` to call N1 internally or for `pack.to_cb()` to perform
T4, T5, and C5 internally. The build function should show those waits and
publications in their actual order.

## 1. Command queue and firmware lifecycle

These operations are outside the matmul worker-kernel bodies, but a kernel
cannot be launched or reused correctly without them.

### L1. Program writes before GO

Fast dispatch inserts a command-queue wait after multicast program writes and
again before the run command. Only after those writes have drained does it send
the GO word and begin waiting on the worker-done stream.

Source: [`blackhole-py/cq.py`](../../blackhole-py/cq.py#L392).

This is command-queue ordering. It is not a worker RISC rendezvous and should
not share an API with one.

### L2. Firmware LOAD/GO/DONE protocol

BRISC firmware receives the launch GO, resets launch-scoped Tensix state,
loads launch metadata, and signals subordinate RISCs. NCRISC and the TRISCs
wait on their byte-valued subordinate states before entering their worker
kernels. On return they publish DONE. BRISC waits for all enabled subordinate
RISCs before reporting worker completion.

Sources:

- [`fw/brisc.py`](../../blackhole-py/fw/brisc.py#L199)
- [`fw/ncrisc.py`](../../blackhole-py/fw/ncrisc.py#L35)
- [`fw/trisc.py`](../../blackhole-py/fw/trisc.py#L65)

These lifecycle states must be explicit firmware operations. A Python kernel
builder should not silently synthesize or reinterpret them.

### L3. Per-launch CB-counter reset handshake

Before releasing a worker launch, BRISC asks TRISC0 firmware to clear every
hardware CB `received` and `acked` counter. BRISC waits for TRISC0 to report
that reset complete. The same handshake runs again after the worker kernels
finish, before the next launch is accepted.

Sources:

- BRISC request/wait: [`fw/brisc.py`](../../blackhole-py/fw/brisc.py#L295)
- TRISC0 reset loop: [`fw/trisc.py`](../../blackhole-py/fw/trisc.py#L74)

This reset is different from initializing each RISC's local CB cursor state.
Both are needed.

### L4. Worker instruction-cache invalidation

Program text is replaced in worker L1 between launches. BRISC firmware
invalidates the RISC instruction caches after launch setup and before calling
the worker kernels, so no role executes stale instructions from a previous
program.

Source: [`fw/brisc.py`](../../blackhole-py/fw/brisc.py#L291).

This is an instruction-coherence operation, not a RISC data fence and not a
Tensix pipeline drain. It must remain visible in firmware lifecycle code.

## 2. Same-core RISC synchronization

### R1. BRISC-to-TRISC start event

Every BRISC matmul variant calls `release_triscs()` before beginning its data
loop. It clears the three TRISC arrival words and the packed start word, then
writes one `0x01` byte per TRISC. Each TRISC waits on its own byte and clears
that byte after consuming the event.

Sources:

- release: [`matmul_peak.py`](../../blackhole-py/examples/matmul_peak.py#L851)
- consume: [`MatmulTrisc.prologue()`](../../blackhole-py/examples/matmul_peak.py#L873)

This is a one-to-many, consumable same-core event. BRISC is the producer, not a
participant in the following rendezvous.

### R2. TRISC initialization rendezvous

After role-local unpack, math, and pack initialization, each TRISC writes `1`
to its own L1 word, executes a release fence, and polls all three arrival
words. The rendezvous is used by both ordinary and grouped-K variants.

Source: [`MatmulTrisc.init_barrier()`](../../blackhole-py/examples/matmul_peak.py#L884).

The explicit facts are:

- participants: TRISC0, TRISC1, TRISC2;
- initializer/reset owner: BRISC through R1;
- storage: three same-core L1 words;
- comparison: exact equality with `1`;
- reuse rule: BRISC resets the words before each release.

No generic barrier is required. A narrow `risc_rendezvous` operation may
represent this exact protocol.

### R3. RISC `fence`

`fence` supplies release/acquire ordering around shared L1 values and polling
loops. It also appears after several hardware counter waits.

It does not prove any of these facts:

- a NoC command was accepted;
- a NoC payload left the source;
- a remote write was acknowledged;
- a Tensix instruction retired;
- another RISC reached a rendezvous.

Those require their own waits below.

## 3. Circular-buffer synchronization

Matmul declares four CBs:

| CB | Producer | Consumer | Contents |
| --- | --- | --- | --- |
| CB0 | BRISC A reader/distributor | TRISC0 | Input A blocks. |
| CB1 | NCRISC B reader/distributor | TRISC0 | Input B blocks. |
| CB24 | TRISC2 | TRISC0 and/or accumulation flow | Partial accumulations. |
| CB16 | TRISC2 | NCRISC | Final output tiles. |

CB synchronization uses monotonically wrapping 16-bit `received` and `acked`
counters plus per-RISC local read/write pointers.

### C1. `reserve_back(cb, count)`

The producer waits until:

```text
capacity - (received - acked) >= count
```

Matmul uses this before DRAM reads into CB0/CB1, before receiving multicasts,
and before TRISC2 packs into CB24/CB16. This is producer backpressure; it says
nothing about whether new data has arrived.

### C2. `push_back(cb, count)`

The producer advances its write pointer and publishes a new `received` count.
BRISC and NCRISC do this only after their DRAM read and cross-core distribution
protocols are complete. Receiver cores publish only after observing their
data-ready semaphore.

For CB0/CB1, the publication edge is:

```text
DRAM read complete
  -> multicast payload departed
  -> remote data-ready semaphore observed where applicable
  -> CB received count published
```

### C3. `wait_front(cb, count)`

The consumer waits until:

```text
received - acked >= count
```

TRISC0 waits on CB0/CB1 before unpacking and on CB24 before a partial reload.
NCRISC waits on CB16 before writing final output tiles.

### C4. `pop_front(cb, count)`

The consumer advances its read pointer and publishes `acked`, returning pages
to the producer. An ordinary RISC publication is correct only when all actual
consumption is already complete.

### C5. Tensix-ordered `push_back` and `pop_front`

Matmul needs two deferred variants:

- `push_back(..., tensix_received=True)` queues a `TTSTOREREG` behind pack, so
  CB24/CB16 does not become visible before the pack engine has produced it.
- `pop_front(..., tensix_ack=True)` queues a `TTSTOREREG` behind unpack, so
  CB0/CB1/CB24 pages are not returned while unpack still consumes them.

Source: [`blackhole-py/ttk/cb.py`](../../blackhole-py/ttk/cb.py#L132).

These modes must stay explicit at the call site. An eager RISC store followed
by a fence is not equivalent.

### Output CB release requires NoC source departure

NCRISC uses posted writes for CB16 output. Before `pop_front(CB16)`, it waits
until the output payload has left the source NIU. Otherwise TRISC2 could reuse
and overwrite the L1 pages while the NoC still reads them.

This dependency intentionally uses source-side departure, not a remote DRAM
acknowledgement.

## 4. NoC issue and local completion

### N1. Command-buffer ready

Before reusing a NoC command buffer, matmul polls `CMD_CTRL == 0`. This is
required before changing command registers or issuing the next command.

Source: [`noc_wait_cmd_ready()`](../../blackhole-py/ttk/noc.py#L416).

It proves only that command state can be reused. It does not prove that data
has departed or arrived.

### N2. DRAM read completion

BRISC reads A into CB0 and NCRISC reads B into CB1. Both support two explicit
completion modes:

1. **Global counter:** snapshot `NIU_MST_RD_RESP_RECEIVED`, issue the known
   number of reads, then wait for the snapshot plus issued count.
2. **Transaction ID:** reset/arm TRID 2, tag the reads, then wait until that
   TRID's outstanding-read gauge becomes zero.

Sources:

- A path: [`matmul_reader_sender()`](../../blackhole-py/examples/matmul_peak.py#L1510)
- B path: [`matmul_writer_sender()`](../../blackhole-py/examples/matmul_peak.py#L1770)

Only after this wait may the local L1 input block be multicast or published to
CB0/CB1.

Resetting a TRID counter is setup, not completion. Likewise, a zero tagged
gauge is safe only after the final command has been accepted.

### N3. Posted-write source departure

Input multicast and ordinary output writes are posted. Matmul snapshots
`NIU_MST_POSTED_WR_REQ_SENT`, adds the expected command count, issues the
writes, and waits until the sent counter reaches that target.

Source: [`_emit_posted_writes_flushed()`](../../blackhole-py/examples/matmul_peak.py#L1113).

For input multicast, this orders payload departure before the data-ready
semaphore publication. For output, it permits CB16 source pages to be reused.
It is not a destination acknowledgement.

### N4. Tagged outgoing-write drain

The optional output TRID mode tags writes with TRID 3. Before releasing CB16,
it first waits for the final command buffer to become ready, then polls that
TRID's outgoing-write gauge until zero.

Source: [`_emit_trid_writes_sent()`](../../blackhole-py/examples/matmul_peak.py#L1125).

The initial command-ready wait is essential: observing a zero gauge before the
last command is accepted would be a false completion.

### N5. Remote acknowledgement is a separate operation

The default matmul worker path does not require non-posted acknowledgements for
input multicast or output writes. Other kernels and command-queue firmware do.
The rewrite must retain a separate `wait_write_acks(ticket)` operation and
must never substitute N1, N3, or N4 for it.

## 5. Cross-core NoC synchronization

Matmul uses four L1 semaphore IDs: two for the A row-distribution protocol and
two for the B column-distribution protocol.

| Semaphore | Owner/location | Purpose |
| --- | --- | --- |
| 0 | A sender core | Count row receivers that reserved CB0 and are ready. |
| 1 | Each A receiver core | Signal that the A multicast payload is ready. |
| 2 | B sender core | Count column receivers that reserved CB1 and are ready. |
| 3 | Each B receiver core | Signal that the B multicast payload is ready. |

### X1. Receiver-ready atomic arrival

For each block, a receiver:

1. reserves space in its local CB0 or CB1;
2. clears its local data-ready semaphore;
3. issues a NoC atomic increment to the sender's receiver-count semaphore;
4. waits for its own data-ready semaphore to become `1`.

The sender waits until its receiver-count semaphore equals the number of
receivers, then clears it for the next block. This prevents the sender from
multicasting into a receiver CB before that receiver has space.

Sources:

- A receiver: [`matmul_reader_recv()`](../../blackhole-py/examples/matmul_peak.py#L1720)
- B receiver: [`matmul_writer_recv()`](../../blackhole-py/examples/matmul_peak.py#L1900)

The receiver-notify path does not explicitly wait for the atomic response.
Functional progress is established when the sender observes the increment and
later publishes data-ready. If a source-side atomic completion is required for
resource reuse in a future path, it must be added as an explicit N6 wait.

### X2. Payload-before-data-ready publication

After every receiver has arrived, the sender multicasts the payload. It waits
for the posted payload commands to depart, then multicasts a data-ready
semaphore value of `1` to the receivers. Each receiver waits on its local
semaphore before publishing its CB received count.

The required order is:

```text
receiver reserve
  -> receiver atomic arrival
  -> sender sees all arrivals
  -> sender issues payload multicast
  -> sender waits for payload source departure
  -> sender publishes data-ready semaphore
  -> receiver observes data-ready
  -> receiver push_back(CB0 or CB1)
```

The data-ready write and the payload use the same NoC ordering assumptions in
the non-overlay path. Overlay mode optionally waits for its own posted
semaphore write to depart as well.

### N6. Atomic-response completion

`noc_wait_atomic_responses` polls the atomic-response counter. It is a distinct
completion point even though default matmul does not call it. Do not make every
NoC atomic implicitly wait: the receiver-arrival protocol deliberately allows
the sender's observation to provide the synchronization edge.

## 6. Tensix synchronization

Tensix instructions from TRISC0/1/2 are queued into hardware pipelines. RISC
program order alone does not mean an unpack, math, or pack operation has
retired.

### T1. Full per-TRISC instruction drain

`tensix_sync(trisc_id)` writes and reads `PC_BUF_SYNC`. Matmul uses it:

- before safely reinitializing `MATH_PACK`;
- after unpack/reload work before deferred CB release;
- after math/SFPU completion before reconfiguration or phase reuse;
- during pack sequences before publishing or reusing state.

Source: [`Tensix.tensix_sync()`](../../blackhole-py/ttk/tensix.py#L316).

The TRISC/pipe identity is part of the operation.

### T2. MOP configuration drain

`write_mop_cfg()` first performs `mop_sync()` through `PC_BUF_MOP_SYNC`, then
writes the new MOP template. This prevents a live MOP from observing a partial
or replacement configuration.

Source: [`Tensix.write_mop_cfg()`](../../blackhole-py/ttk/tensix.py#L304).

The rewrite should expose MOP reconfiguration as an explicit synchronized
operation rather than silently writing configuration words.

### T3. Unpack configuration context handshake

Before changing unpack base addresses or context, TRISC0 polls
`PC_UNPACK_SYNC` until busy bits `value & 0xfe` are zero. It writes the selected
configuration context, writes zero to `PC_UNPACK_SYNC` to commit, and issues
`TTSTALLWAIT(UNPACK, TRISC_CFG)` before unpack begins.

Representative source:
[`emit_trisc0_unpack_row()`](../../blackhole-py/examples/matmul_peak.py#L2095).

The wait, configuration writes, commit, and hazard wait are all distinct and
should remain visible in the unpack API.

### T4. Typed engine/resource hazards

Matmul uses the following `TTSTALLWAIT` relationships:

| Stalled issue resource | Waited condition | Purpose |
| --- | --- | --- |
| `UNPACK` | `TRISC_CFG` | Do not unpack before RISC configuration is committed. |
| `UNPACK` | `UNPACK0` | Serialize direct-to-destination unpack faces. |
| `UNPACK` | `THCON | UNPACK0` | Ensure unpack and thread-controller retirement before restoring context. |
| `SYNC` | `MATH | SFPU` | Finish math/SFPU before publication, drain, reload, or reconfiguration. |
| `CFG` | `MATH | SFPU` | Protect math configuration changes. |
| `CFG` | `THCON | PACK0` | Protect pack destination/configuration changes. |
| `CFG` | `THCON` | Wait for thread-controller use of pack configuration. |
| `CFG` | `PACK0` | Protect pack L1-accumulation reconfiguration. |
| `THCON` | `PACK0` | Wait for pack retirement before destination reuse. |

The exact stall and wait masks are part of correctness. A method named only
`wait_for_tensix()` would discard necessary information.

### T5. Tensix hardware semaphores

Matmul uses four hardware semaphore protocols:

#### `UNPACK_SYNC`

TRISC0 consumes completion credits generated by unpack MOPs. It uses
`TTSEMGET`, and in the direct-to-destination path explicitly waits for a
non-zero credit before the final get/drain.

#### `MATH_PACK`

This is the main TRISC1-to-TRISC2 flow-control semaphore:

```text
TRISC1: wait STALL_ON_MAX -> produce destination tile -> post
TRISC2: wait STALL_ON_ZERO -> pack destination tile -> get
```

Matmul configures it with initial value `0` and maximum value `2`, allowing
bounded producer/consumer overlap.

#### `UNPACK_TO_DEST`

TRISC0 and TRISC1 coordinate partial-accumulation reload directly into
destination registers. The semaphore prevents unpack from overwriting a
destination region before math grants permission and lets math wait until the
reload is available.

#### `MATH_DONE`

TRISC1 uses a post/wait/get handshake around the shared
`UNPACK_TO_DEST_ADDR_MAILBOX`. The release fence before posting ensures TRISC0
sees the destination address before acting on the semaphore.

Representative source:
[`emit_math_fp32_reload_subblock()`](../../blackhole-py/examples/matmul_peak.py#L2655).

### T6. Safe hardware-semaphore reinitialization

`matmul_math_init()` cannot overwrite a live `MATH_PACK` semaphore. It first
drains the math Tensix stream, polls the semaphore MMIO low byte until zero,
and only then emits `TTSEMINIT(initial=0, max=2)`.

Source: [`matmul_math_init()`](../../blackhole-py/examples/matmul_peak.py#L2551).

This three-step sequence must remain explicit. `TTSEMINIT` alone is not a
safe reset of a live semaphore.

### T7. Tensix-ordered L1 stores

Deferred CB publication uses `TTSTOREREG` inside the Tensix instruction FIFO.
This creates an ordering edge from pack/unpack retirement to an L1-visible CB
counter. It is not equivalent to a later RISC `fence`.

## 7. Optional overlay synchronization

Overlay transport is disabled by default, but `matmul_peak.py` contains three
additional synchronization points when enabled.

### O1. Stream source ready

After configuring a stream, the kernel polls packed stream debug state until
the source state equals `SRC_READY_WAIT_ALL_DESTS`.

Source: [`_emit_overlay_wait_src_ready()`](../../blackhole-py/examples/matmul_peak.py#L1160).

### O2. Stream transfer done

After publishing the source message, the kernel waits until both:

- the software phase-advance signal is asserted; and
- the stream's outstanding word count is zero.

Source: [`_emit_overlay_wait_done()`](../../blackhole-py/examples/matmul_peak.py#L1174).

Both predicates are required.

### O3. Remote sentinel read

The optional overlay read barrier issues a four-byte NoC read of the last word
in the remote destination region and waits for that read response. It is used
as a payload-ordering sentinel before remote consumption.

Source:
[`_emit_overlay_remote_read_barrier()`](../../blackhole-py/examples/matmul_peak.py#L1354).

This must remain an explicit composite operation because its correctness
depends on the chosen sentinel address and the overlay/NoC ordering contract.

## 8. Completion and resource reuse

### F1. Worker-kernel completion

Returning from one role does not complete the worker launch. BRISC firmware
waits for DONE from every enabled NCRISC/TRISC role. Only then does it notify
dispatch and advance the launch pointer.

Dispatch waits for one completion signal from every target physical core. The
host observes completion only after that count is satisfied.

### Output visibility

Worker completion follows the output writer's source-departure wait. The
default worker matmul path uses posted writes, so it establishes that DRAM has
accepted the source-side transaction stream according to the NoC contract; it
does not perform a per-tile non-posted acknowledgement.

Host readback is a later ordered program/transfer and must not be conflated
with the worker's CB16 release condition.

## 9. Things that are not synchronization

The following may affect timing or scheduling but do not establish a
correctness dependency by themselves:

- `emit_output_launch_stagger()` and overlay row-stagger delay loops;
- Python statement order between different role builders;
- allocating two objects that refer to the same CB;
- resetting a TRID counter without a following completion wait;
- reading a NoC counter without recording the corresponding target;
- command-buffer ready when the needed fact is payload departure or arrival;
- a RISC `fence` when the needed fact is NoC or Tensix completion.

## 10. Required rewrite API shape

The rewrite should expose these operations through their owning subsystem. The
names below are illustrative; preserving the semantics is mandatory.

```python
# Same-core RISC synchronization.
start = k.risc_event("trisc_start", producer=k.brisc,
                     consumers=(k.trisc0, k.trisc1, k.trisc2), consumable=True)
ready = k.risc_rendezvous("trisc_ready", participants=(k.trisc0, k.trisc1, k.trisc2))
k.brisc.clear(ready)
k.brisc.signal(start)
k.trisc0.wait(start); k.trisc0.arrive_and_wait(ready)
k.trisc1.wait(start); k.trisc1.arrive_and_wait(ready)
k.trisc2.wait(start); k.trisc2.arrive_and_wait(ready)

# CB synchronization.
k.brisc.reserve_back(cb0, count)
k.brisc.push_back(cb0, count, after="noc_read_and_distribution")
k.trisc0.wait_front(cb0, count)
k.trisc0.pop_front(cb0, count, publish="tensix_after_unpack")

# NoC synchronization.
noc.wait_cmd_ready(buffer)
reads = noc.snapshot_read_responses()
noc.issue_reads(...)
noc.wait_read_responses(reads, count)
noc.wait_posted_writes_sent(write_ticket)
noc.wait_tagged_writes_sent(trid)
noc.atomic_increment(remote_semaphore, 1)
noc.wait_atomic_responses(atomic_ticket)  # only where source completion is required

# Tensix synchronization.
tensix.drain()
tensix.mop_drain()
unpack.wait_config_idle()
unpack.commit_config()
tensix.stall(stall=UNPACK, wait_for=TRISC_CFG)
tensix.sem_wait(MATH_PACK, STALL_ON_MAX, stall=MATH | SYNC | SFPU)
tensix.sem_post(MATH_PACK)
tensix.sem_get(MATH_PACK)
```

No call above should be inserted because a lowering pass guessed that two
operations might conflict. The kernel author or a named TTK operation with a
fully documented hardware contract must call it explicitly.

### Call-site visibility

This is too implicit:

```python
noc.issue_read(...)       # secretly waits for command-buffer space
unpack.tile(src_cb)       # secretly waits for config and completion
pack.tile_to_cb(dst_cb)   # secretly waits for math, reserves, packs, and publishes
```

The logical kernel should instead show the synchronization sequence:

```python
noc.wait_cmd_ready(read_buffer)
read_ticket = noc.issue_read(...)
noc.wait_read_responses(read_ticket)

unpack.wait_config_idle()
unpack.configure_source(src_cb)
unpack.commit_config()
unpack.wait_config_visible()
unpack.run_tile()
unpack.wait_complete()

k.trisc2.wait_semaphore(MATH_PACK, condition=NONZERO)
k.trisc2.reserve_back(dst_cb, count)
pack.configure_destination(dst_cb)
pack.wait_config_safe()
pack.run_tiles(count)
pack.wait_complete()
k.trisc2.publish_back(dst_cb, count, ordering=TENSIX_FIFO)
k.trisc2.consume_semaphore(MATH_PACK)
```

Configuration and instruction-encoding helpers may remain reusable. They may
not silently introduce a wait, signal, counter publication, semaphore action,
or completion edge. If a hardware instruction combines an action with a wait,
the method name and arguments must say so directly, such as
`stall_until(stall=UNPACK, wait_for=TRISC_CFG)`.

The same rule applies to composite cross-role helpers. Do not make
`k.compute.matmul()` silently edit five streams and insert synchronization.
The one-function kernel can call shared configuration helpers, but every
cross-role handoff remains visible in that function.

## 11. Migration checklist for `matmul_peak`

- [ ] Keep CQ write-before-GO ordering explicit in dispatch.
- [ ] Keep firmware LOAD/GO/DONE and CB-reset handshakes explicit.
- [ ] Keep worker instruction-cache invalidation explicit after program text replacement.
- [ ] Model BRISC-to-TRISC start as a consumable RISC event.
- [ ] Model TRISC initialization as a same-core three-party rendezvous.
- [ ] Port CB0/CB1/CB24/CB16 reserve, publish, wait, and release calls.
- [ ] Preserve Tensix-deferred CB24/CB16 publication and CB0/CB1/CB24 release.
- [ ] Preserve global and TRID read-completion modes as different calls.
- [ ] Preserve command-ready, posted-sent, tagged-sent, write-ack, and
      atomic-response waits as different types.
- [ ] Port the receiver-ready atomic protocol and payload-before-data-ready
      semaphore ordering for A and B distribution.
- [ ] Port unpack-config wait/commit and all exact `TTSTALLWAIT` masks.
- [ ] Port `UNPACK_SYNC`, `MATH_PACK`, `UNPACK_TO_DEST`, and `MATH_DONE`
      semaphore protocols.
- [ ] Preserve the drain/wait-zero/init sequence for `MATH_PACK`.
- [ ] Port optional overlay source-ready, done, and sentinel-read waits only
      when overlay transport is enabled.
- [ ] Keep worker-role completion and dispatch completion explicit.
- [ ] Audit every helper used by the port and split out hidden waits, signals,
      publications, semaphore operations, and completion edges.
- [ ] Add tests that intentionally distinguish source departure, remote
      acknowledgement, read arrival, and command-buffer availability.
