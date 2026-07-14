# Host/device tensor transfers through the command queue

This document traces tt-metal's fast-dispatch buffer transfers and compares
them with the transfer path in this repository. It is based on tt-metal commit
`da4b5148e26b` and blackhole-py-rewrite commit `04a6aec`.

## Decision

The current fill/drain programs are a valid transfer mechanism. The problem is
not that a RISC kernel moves the bytes: tt-metal also moves them with long-running
prefetch and dispatch firmware. The important difference is that tt-metal's
transfer engine is always active and its bounded sysmem regions are recycling
streams, while this repository launches ordinary worker programs and treats a
large host allocation as if it must hold the whole tensor.

For the smallest safe next step, keep the current worker transfer programs and
make `cq.dram` a reusable, page-aligned chunk window. This fixes tensors larger
than the window without changing the CQ firmware. It also preserves the
current parallelism across worker cores.

If eliminating per-transfer worker launches is a hard requirement, the
smallest CQ-native step is one synchronous, staged `DRAM_COPY` command handled
by the dispatch firmware. It can reuse the same chunk loop and the
existing completion ring. It does **not** need tt-metal's completion-stream
protocol, but a naive implementation uses one dispatch core and must be
benchmarked before the worker programs are removed.

Do not initially port all of tt-metal's transfer machinery. In particular,
omit pinned-memory direct transfers, background reader threads, sharded
layouts, sub-buffers, multiple devices, and nonblocking reads. A faithful
completion-ring stream is useful later if nonblocking D2H or elimination of
the host staging window becomes important.

## Three designs at a glance

| Property | Current worker programs | Minimal firmware `DRAM_COPY` | tt-metal-style streaming |
|---|---|---|---|
| Transfer code runs on | Up to all worker NCRISCs | Dispatch firmware | Prefetch/dispatch firmware |
| H2D bytes travel through | `cq.dram` host window | `cq.dram` host window | Inline issue-ring records, or pinned source |
| D2H bytes travel through | `cq.dram` host window | `cq.dram` host window | Completion ring, or pinned destination |
| Tensor must fit a host window | Currently yes; not fundamentally | No, when chunked | No |
| Keeps current ring transport and completion format | Yes | Yes, but adds one command ABI | No: D2H needs completion read credits |
| Uses worker cores / replaces worker text | Yes | No | No |
| Expected implementation size | Smallest change | Small and potentially net-neutral after deletion | Materially larger |
| Performance expectation | Parallel but launch-heavy | Unknown; likely less parallel | Designed as a streaming DMA service |

`cq.dram` is a misleading name. It is a region of pinned host system memory,
not device DRAM.

## The current blackhole-py-rewrite path

### Host-memory layout

`CommandQueue` divides the default 1 GiB pinned mapping as follows:

```text
0                                                             1 GiB
+------------------+----------------+------------------------------+
| 64 MiB issue ring| 1 MiB completion| 959 MiB cq.dram host stage |
+------------------+----------------+------------------------------+
```

The first 4 KiB of the completion allocation holds its published write
pointer, so completion payload starts at the next page. The remaining 959 MiB
is allocated as one monotonic `cq.dram` region. See
[`cq.py`](../cq.py), `CommandQueue.__init__`, lines 226-263, and
[`pcie.py`](../pcie.py), `Sysmem`, lines 126-159.

The ordinary CQ transport is already circular:

- Records are at most 64 KiB and 64-byte aligned.
- The host pads to the issue-ring end, waits until every prefetch slot proving
  an earlier PCIe read is free, then wraps.
- Prefetch copies a record through its 64 KiB staging area, waits for dispatch
  ring credits, and publishes whole 4 KiB pages.
- Dispatch returns credits only after it has consumed a record.

Those rules are in [`cq.py`](../cq.py), lines 276-301,
[`fw/cq_prefetch.py`](../fw/cq_prefetch.py), lines 29-80, and
[`fw/cq_dispatch.py`](../fw/cq_dispatch.py), lines 128-139. They are enough to
stream arbitrary amounts of **inline issue data**; they are separate from the
large `cq.dram` allocation.

### Fill and drain programs

`Device.write()` copies each input into a distinct pending slice of `cq.dram`
and queues an ordinary worker `Program`. `Device.run()` submits these programs
in queue order before any compute program passed to that call. `Device.read()`
constructs the reverse program, calls the same `run()` path once, and copies the
output from the beginning of the staging region.

Transfer programs declare only an NCRISC image. `Program` fills each of their
four missing roles with an empty return kernel at launch, preventing a previous
compute image from running alongside the transfer. Per-core transfer arguments
are ordinary launch writes owned by the program.

The host partitions all logical pages into contiguous ranges, assigns one
range per worker, writes six arguments to each worker, uploads the program,
and runs it through the regular queue path. Each NCRISC then performs:

```text
global_page -> bank = global_page % 7
global_page -> bank_row = global_page // 7
DRAM address = buffer_base + bank_row * page_size
```

H2D reads one page from sysmem into worker L1 scratch and writes it to the
selected DRAM endpoint. D2H performs the reverse. Every source read and
destination write is completed before that worker reuses its scratch. The
implementation is in [`fw/dram.py`](../fw/dram.py), lines 14-63.

Each individual program submission is synchronous. Its Run completion is
observed only after all workers have reported done, and each worker reports
done only after its final acknowledged transfer. Consequently a following
compute program cannot observe a partially uploaded buffer.

### Current constraints and hazards

- A page must be 16-byte aligned and no larger than 16 KiB. The allocator is
  stricter for normal buffers and requires 64-byte-aligned DRAM pages.
- All writes pending in one queue must collectively fit in `cq.dram`; the
  staging cursor is reclaimed when `run()` drains the queue.
- The referenced portion of sysmem must not cross the current 4 GiB NoC
  low-address window.
- CQ discards the pinned mapping's upper address bits and uses a fixed
  `CQ.PCIE_MID`; correctness also assumes that fixed MID matches the mapping.
- A transfer consumes worker cores and uploads its worker images on every
  execution. It is an ordinary program boundary in the queue.
- The transfer replaces worker text and arguments. Missing roles are replaced
  by return kernels, and later programs upload their own state.
- Every CQ record and H2D staging copy calls `Sysmem.flush()`, which currently
  `msync`s the entire pinned mapping rather than the written range. This cost
  should be measured separately from transfer-kernel launch overhead.
- The public methods still accept or return one full-tensor `bytes` object.
  Chunking the pinned window removes the device-visible capacity limit, not
  that separate host-object memory requirement.

The queue-capacity and 4 GiB-window checks happen before `Sysmem.write()`, so an
oversized pending upload raises without writing past the staging mapping.

## How tt-metal fast-dispatch transfers work

tt-metal does not put an entire tensor in a CQ-sized host allocation. Its issue
and completion regions are producer/consumer rings, and bounded L1 buffers
relay the stream.

### CQ sysmem and publication

`SystemMemoryCQInterface` gives approximately 75% of each CQ's host-memory
slice to issue traffic and 25% to completion traffic, rounded in 4 KiB pages.
The host owns the issue write pointer and completion read pointer; the device
owns the converse pointers. See
[`system_memory_cq_interface.hpp`](../../tt-metal/tt_metal/impl/dispatch/system_memory_cq_interface.hpp),
lines 11-38, and
[`system_memory_cq_interface.cpp`](../../tt-metal/tt_metal/impl/dispatch/system_memory_cq_interface.cpp),
lines 13-39.

An issue transaction is published in this order:

1. Reserve a contiguous range in the host issue ring, wrapping if needed.
2. Encode the prefetch/dispatch commands and copy any inline payload.
3. Advance the host issue pointer.
4. Execute a host store fence.
5. Write the transaction size into a small FetchQ entry in prefetch L1.

When FetchQ is full, the host polls prefetch's read pointer before reusing an
entry. The issue FIFO is sized to cover every FetchQ entry, one extra wrapping
command, and outstanding tagged PCIe reads. This prevents the host from
overwriting issue bytes that prefetch has not consumed. See
[`system_memory_manager.cpp`](../../tt-metal/tt_metal/impl/dispatch/system_memory_manager.cpp),
lines 263-274, 491-535, 566-628, 665-723, and 817-858.

Blackhole's default worker-dispatch configuration permits a 128 KiB prefetch
transaction, uses a 256 KiB prefetch command/data ring, a 128 KiB double
scratch buffer, and a 512 KiB dispatch ring. See
[`dispatch_settings.cpp`](../../tt-metal/tt_metal/impl/dispatch/util/dispatch_settings.cpp),
lines 59-84. These are transport-window sizes, not tensor-size limits.

### Host to device

The ordinary, non-pinned H2D path is:

```text
host tensor
  -> bounded inline issue records
  -> CQ_PREFETCH_CMD_RELAY_INLINE
  -> prefetch command/data L1 ring
  -> dispatch 4 KiB page ring
  -> CQ_DISPATCH_CMD_WRITE_PAGED
  -> interleaved device DRAM
```

For an interleaved buffer, the host emits a `WRITE_PAGED` descriptor containing
`is_dram`, `start_page`, `base_addr`, `page_size`, and `pages`, followed by the
corresponding host bytes. See
[`cq_commands.hpp`](../../tt-metal/tt_metal/impl/dispatch/kernels/cq_commands.hpp),
lines 17-64 and 235-264, and
[`buffers/dispatch.cpp`](../../tt-metal/tt_metal/impl/buffers/dispatch.cpp),
lines 526-609 and 927-1032.

The host loop chooses only as many pages as fit both the remaining contiguous
issue-ring tail and one maximum prefetch transaction. When no page fits at the
tail, it wraps and continues. If a device page itself is larger than the
transaction limit, tt-metal subdivides it into aligned partial pages based on
a 4 KiB starting size. A 16-bit page-index overflow is handled by advancing
the bank base address and making the page index relative again. See
`buffers/dispatch.cpp`, lines 423-455, 480-523, and 1035-1080.

Prefetch reads the issue record, relays its inline bytes into dispatch's
credit-controlled circular buffer, and releases pages as the consumer makes
progress. Dispatch's `process_write_paged()` uses `TensorAccessor` to turn each
logical page into an interleaved bank NoC address, then writes directly from
the dispatch ring. No user worker is launched. See
[`cq_prefetch.cpp`](../../tt-metal/tt_metal/impl/dispatch/kernels/cq_prefetch.cpp),
lines 358-510 and 811-847, and
[`cq_dispatch.cpp`](../../tt-metal/tt_metal/impl/dispatch/kernels/cq_dispatch.cpp),
lines 589-631.

The first H2D transaction also waits for preceding worker activity. Later
transactions for the same logical write do not repeat that wait. Normal inline
H2D owns a copy of the data before the enqueue call returns, so the caller's
source may be reused even when the device transfer remains in flight.

### Device to host

The ordinary, non-pinned D2H path reverses the data flow but is not encoded as
a large issue payload:

```text
small [WAIT + WRITE_HOST + RELAY_PAGED] issue record
  -> prefetch reads interleaved DRAM into double-buffered scratch
  -> dispatch page ring
  -> dispatch waits for free completion pages
  -> completion sysmem ring
  -> host copies/unpads data and returns page credits
```

The host first emits worker-completion waits and a barrier. A no-flush host
write command reserves the front of the dispatch stream, and a
`CQ_PREFETCH_CMD_RELAY_PAGED` descriptor supplies `start_page`, `base_addr`,
`page_size`, and `pages`. For an interleaved read, one logical transaction can
describe every remaining page even when its payload is much larger than the
completion ring. The dispatcher copies the 16-byte `WRITE_HOST` command itself
at the front of the completion record; the host descriptor knows to skip that
framing before copying tensor bytes. See `buffers/dispatch.cpp`, lines
1363-1401, 1403-1527, 1558-1579, and 1641-1651.

Prefetch uses the interleaved address generator, fills alternating halves of
its scratch buffer with device reads, and streams completed halves to
dispatch. See `cq_prefetch.cpp`, lines 938-1157.

Dispatch treats the completion area as a real producer/consumer FIFO:

1. Poll the device-visible host read pointer and toggle.
2. Wait until enough completion pages are free.
3. Write data, splitting at the physical end of the ring when necessary.
4. Publish the new device write pointer and toggle only after the payload.
5. Stop when the host falls behind and resume as it returns pages.

See `cq_dispatch.cpp`, lines 252-405. A host completion-reader thread knows the
destination layout from a queued descriptor. It waits for the published write
pointer, copies only the currently contiguous bytes, removes per-page padding
or restores sharded order, advances its local read pointer, and writes that
pointer back to dispatch through a TLB. See `buffers/dispatch.cpp`, lines
1634-1833,
[`fd_mesh_command_queue.cpp`](../../tt-metal/tt_metal/distributed/fd_mesh_command_queue.cpp),
lines 900-1000, and `system_memory_manager.cpp`, lines 630-663 and 798-815.

This concurrent drain is essential. A tensor can be many times larger than the
completion ring because the ring is reused; the device blocks only when the
producer catches the consumer.

### Optional pinned path

Current tt-metal can also map caller-owned host memory into a device-visible
NoC address. H2D then uses an out-of-band linear relay rather than copying
tensor bytes into the issue ring. D2H can write directly to an aligned pinned
destination and skip the completion-ring copy. Alignment, range, lifetime, and
event ownership make this an optimization, not a good first feature for this
repository. The selection logic is in `buffers/dispatch.cpp`, lines 995-1032,
1154-1197, 1426-1452, and 1496-1523.

## Why tensor size is not bounded by sysmem capacity

The capacity question has different answers in the three designs:

- **tt-metal inline H2D:** split the tensor into transactions no larger than
  the maximum command and current issue-ring tail. FetchQ consumption makes
  wrapped issue bytes reusable.
- **tt-metal completion D2H:** describe the device pages with a small command,
  then concurrently stream them through the completion FIFO. Host read credits
  make wrapped completion pages reusable.
- **Current repository:** reuse `cq.dram` as a finite window. A chunk must fit;
  the tensor does not.

tt-metal has a regression that creates a buffer as large as the entire CQ,
which is necessarily larger than either its 75% issue or 25% completion
subregion, and transfers it successfully. See
[`test_EnqueueWriteBuffer_and_EnqueueReadBuffer.cpp`](../../tt-metal/tests/tt_metal/tt_metal/dispatch/dispatch_buffer/test_EnqueueWriteBuffer_and_EnqueueReadBuffer.cpp),
lines 1061-1073. Completion wrap is exercised at lines 1076-1100 and
1325-1366.

## Minimal safe implementation choices

No implementation is made by this document. The following sections define the
smallest sensible choices for later work.

### Choice A: retain worker programs and chunk the stage

This is the recommendation when minimizing complexity and preserving transfer
parallelism matter most.

Compute the number of whole pages that can be addressed in one use of the host
window:

```py
stage_noc_full = cq.pcie.sysmem.noc_addr + cq.dram
stage_mid = stage_noc_full >> 32
stage_lo = stage_noc_full & 0xFFFFFFFF
if stage_mid != CQ.PCIE_MID:
    raise ValueError("pinned sysmem is outside the configured PCIe MID")
window_bytes = min(cq.dram_size, (1 << 32) - stage_lo)
chunk_pages = window_bytes // buffer.page_size
```

Alternatively, a future command can carry the MID derived from the actual
pinned address instead of requiring the fixed constant. Reject the transfer
if `chunk_pages == 0`. The boundary term prevents a chunk from carrying into a
different MID while the low address wraps.

For every chunk:

1. Let `first_page` be its page index in the complete device buffer.
2. H2D: copy only the chunk to the beginning of `cq.dram` and flush it.
3. Launch workers with a global starting page and a chunk-local sysmem offset.
4. Wait for the existing Run completion before overwriting the host window.
5. D2H: after that completion, copy only the completed bytes out of
   `cq.dram`.

Partition each chunk into nonoverlapping worker ranges. For a worker whose
range begins at chunk-relative page `core_start`, initialize its arguments as:

```text
tile   = first_page + core_start
sysmem = stage_base + core_start * page_size
count  = pages assigned to this worker
```

The worker increments `tile` and `sysmem` together. Thus its `i`th page maps as
`global_page = first_page + core_start + i`, `bank = global_page % 7`, and
`bank_row = global_page // 7`. Do not restart device page numbering at zero
for each chunk, and do not restart the staging offset at zero for every worker.
A chunk boundary that is not a multiple of seven must continue on the correct
bank and bank row. The current worker already accepts a starting `tile`, so
this mainly changes host partitioning.

This supports a tensor larger than the host window and even a total logical
transfer larger than one 4 GiB host-address window, because every chunk reuses
the same addressable host range. Device-buffer address limits still apply.

### Choice B: one synchronous firmware `DRAM_COPY` command

This is the lowest-complexity way to stop launching transfer programs without
changing issue-ring transport or completion mechanics. It does add a CQ
command opcode and record ABI. It moves the existing page loop into dispatch
dispatch; it is not the full tt-metal streaming design.

One possible 64-byte record keeps the existing 16-byte `Packet.HEADER` and
adds five 32-bit words:

```text
Packet.HEADER:
  op          = DRAM_COPY
  total_size  = 64
  address     = bank-local device DRAM base
  data_size   = page size

extension <IIIII>:
  direction   = 0 for H2D, 1 for D2H
  sysmem_lo
  sysmem_mid
  first_page  = global logical page
  page_count
```

Compile the seven harvested-device NoC 1 DRAM endpoints into dispatch when
`init_device()` builds it. They then do not need to appear in every record.

The current dispatch ring ends at `0x160000` and Blackhole Tensix L1 ends at
`0x180000`, leaving 128 KiB after the ring. Existing completion scratch/control
uses only the first small portion. A fixed 16 KiB page scratch can be reserved
at `0x160100` without changing the dispatch ring. The handler performs the same
mapping and copy sequence as `fw/dram.py`, waits for each read response and
destination acknowledgement before scratch reuse, then returns the record's
dispatch credits normally.

`DRAM_COPY` must publish a completion after finishing all acknowledged writes.
Because submission is currently synchronous, that completion is also the
staging ownership boundary:

- H2D may overwrite the stage only after `submit()` returns.
- D2H may read the stage only after `submit()` returns.
- Large tensors use the exact chunk loop from Choice A.

This wait inside `DRAM_COPY` is a hard correctness requirement. The completion
is safe only after every source read and destination acknowledgement finishes.

No completion data or new completion pointer is required. Deleting
`fw/dram.py` and the transfer-program construction may offset much of the new
handler's line count. The command can record its own start/end timestamps using
the same completion format as Run.

The tradeoff is performance. The current path distributes ranges across many
workers; the simple firmware command serializes them on one dispatch RISC. It
may remove launch overhead yet lose bandwidth. Keep both paths until a
benchmark measures H2D and D2H bandwidth across small and large tensors.

### Choice C: the small faithful tt-metal subset

If the goal becomes tensor streaming with no `cq.dram` stage, implement two
paged operations:

- `DRAM_WRITE_PAGED`: inline page bytes in bounded issue records. The current
  issue-slot and dispatch-credit logic already provides the required wrap and
  reuse safety.
- `DRAM_READ_PAGED`: prefetch device pages and stream them through the
  completion ring while the host actively drains it.

H2D can be added independently. The existing `UnicastWrite` can technically
target DRAM endpoints now, grouping only pages that share one bank-row address.
That is useful for small writes but unattractive for tensors: it creates many
records and doorbells, runs a whole-mapping `msync()` for every record, and has
no D2H counterpart. A dedicated paged record is the better general H2D form.

D2H is the part that materially increases complexity. The current completion
ring is **not** a producer/consumer FIFO:

- Dispatch publishes only its write pointer.
- Host `wait()` advances only Python-local read state.
- Host never returns a read pointer or credits to dispatch.
- Dispatch writes one 4 KiB result slot and wraps without checking space.

See [`fw/cq_dispatch.py`](../fw/cq_dispatch.py), lines 144-169, and
[`cq.py`](../cq.py), lines 315-328. This is safe for today's synchronous,
24-byte result per submission, but it cannot safely carry an arbitrary tensor.

A faithful D2H implementation must add all of the following:

1. A device-visible host completion read pointer and wrap toggle.
2. Dispatch reservation that blocks before overwriting unread pages.
3. Completion writes split at the ring end.
4. Payload-before-write-pointer publication ordering.
5. A host drain loop that copies available bytes and returns read credits while
   the device command is still running.
6. Framing sufficient to distinguish tensor data from the final completion.

A background thread is optional while reads remain blocking, but concurrent
progress is not. Enqueueing a read and waiting for its final completion before
draining will deadlock whenever the payload is larger than the completion
ring: dispatch waits for space, while the host waits for dispatch.

## Recommended rollout

1. Fix validation order and add page-correct chunking to the current transfer
   programs.
2. Benchmark launch cost and sustained H2D/D2H bandwidth by tensor size.
3. If worker occupancy or launch overhead is a demonstrated problem, add the
   staged synchronous `DRAM_COPY` command and compare it with the worker path.
4. Add inline paged H2D if removing the H2D stage is valuable.
5. Add completion-stream D2H only together with read credits and an active host
   drain; do not implement it as an unchecked completion write.
6. Consider pinned direct transfers and nonblocking host reads only after the
   basic ring path is measured and stable.

The tests for the first implementation should include page sizes at the
smallest supported alignment and at 16 KiB; tensors just below, equal to, and
above the stage capacity; chunk starts on every `first_page % 7`; multiple
stage reuses; H2D-transfer-to-program ordering; program-to-D2H ordering; and a
forced 4 GiB low-address boundary. A streaming completion implementation also
needs payloads larger than the completion ring, wrap with a partial tail, and
a deliberately slow host consumer.

## Source map

| Topic | Primary source |
|---|---|
| Rewrite host CQ and rings | [`cq.py`](../cq.py) |
| Rewrite prefetch firmware | [`fw/cq_prefetch.py`](../fw/cq_prefetch.py) |
| Rewrite dispatch firmware | [`fw/cq_dispatch.py`](../fw/cq_dispatch.py) |
| Rewrite transfer API | [`device.py`](../device.py) |
| Rewrite worker transfer loop | [`fw/dram.py`](../fw/dram.py) |
| Rewrite DRAM endpoint mapping | [`ttk/dram.py`](../ttk/dram.py) |
| tt-metal buffer command generation | [`buffers/dispatch.cpp`](../../tt-metal/tt_metal/impl/buffers/dispatch.cpp) |
| tt-metal host CQ ring management | [`system_memory_manager.cpp`](../../tt-metal/tt_metal/impl/dispatch/system_memory_manager.cpp) |
| tt-metal CQ command ABI | [`cq_commands.hpp`](../../tt-metal/tt_metal/impl/dispatch/kernels/cq_commands.hpp) |
| tt-metal prefetch firmware | [`cq_prefetch.cpp`](../../tt-metal/tt_metal/impl/dispatch/kernels/cq_prefetch.cpp) |
| tt-metal dispatch firmware | [`cq_dispatch.cpp`](../../tt-metal/tt_metal/impl/dispatch/kernels/cq_dispatch.cpp) |
| tt-metal host completion reader | [`fd_mesh_command_queue.cpp`](../../tt-metal/tt_metal/distributed/fd_mesh_command_queue.cpp) |
