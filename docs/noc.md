# Blackhole NoC

This document describes the interface implemented by [`ttk/noc.py`](../ttk/noc.py).
It covers the generated RISC-V code and the Blackhole NIU registers that code
uses.

## Instances and command buffers

Every Tensix tile has two Network Interface Units (NIUs). NIU 0 connects to
NoC 0 and NIU 1 connects to NoC 1. They expose the same programming interface
through separate register banks and status counters.

| NoC index | NIU base | Available from |
|---:|---:|---|
| 0 | `0xFFB2_0000` | BRISC or NCRISC `KernelBuilder` |
| 1 | `0xFFB3_0000` | BRISC or NCRISC `KernelBuilder` |

BRISC and NCRISC explicitly select an instance with `k.noc(0)` or `k.noc(1)`.
TRISC kernels cannot access either NoC. NoC 0 normally routes X then Y and NoC
1 routes Y then X. A program may choose different instances to overlap traffic.

Each NIU has four request initiators, also called command buffers. The API
assigns each operation a fixed buffer:

| Buffer | Offset | API use |
|---:|---:|---|
| 0 | `0x0000` | posted writes and multicast writes |
| 1 | `0x0800` | reads |
| 2 | `0x1000` | unused |
| 3 | `0x1800` | atomic increments |

For NoC index `n` and command buffer `b`:

```text
base = 0xFFB2_0000 + (n << 16) + (b << 11)
```

The buffer choice is private. Callers select an operation with `read()`,
`write()`, `multicast()`, or `atomic_inc()`.

## Initialization and coordinates

Obtain the role-owned `NoC` from the builder passed to a kernel function, then
record the initiating tile's logical coordinate:

```py
def brisc(k):
  noc = k.noc(0)
  noc.initialize(NoC.static_coord(*k.core), atomic_return=4)
```

`initialize()` only records values in the Python object; it emits no
instructions. Because every core is lowered independently, `k.core` can be
packed into an immediate at compile time. The local coordinate is used as the
return coordinate for reads and atomics and as the source coordinate for
writes. `atomic_return` is the local L1 address where an atomic response stores
the old value. The defaults after construction are no local coordinate and
atomic return address `4`.

An explicit `return_coord=` lets a read or atomic override the recorded local
coordinate. A write always needs `initialize()`. Omitting both the recorded and
explicit coordinate raises `RuntimeError` while generating the kernel.

`logical_coord(out)` emits a load of the current NIU's `NOC_ID_LOGICAL`
configuration register at `NIU_BASE + 0x148`, stores it in `out`, and returns
`out`.

Unicast coordinates use six bits per axis:

```text
coord = x | (y << 6)
```

Multicast rectangles place the inclusive end coordinate in the low 12 bits and
the inclusive start coordinate in the next 12 bits:

```text
rectangle = end_x | (end_y << 6) | (start_x << 12) | (start_y << 18)
```

The coordinate helpers are:

| Method | Inputs | Result |
|---|---|---|
| `NoC.static_coord(x, y)` | Python `int` values | packed Python `int` |
| `NoC.static_multicast_coord(start, end)` | two `(x, y)` tuples of Python `int` values | packed Python `int` |
| `pack_coord(out, x, y)` | RISC-V registers | emits `out = x \| (y << 6)` and returns `out` |
| `pack_multicast_coord(out, start, end)` | packed coordinate registers | emits `out = end \| (start << 12)` and returns `out` |

The helpers do not range-check or mask axes. Callers must supply coordinates
valid for the NIU's current translation configuration.

## Command registers

All offsets are relative to a command-buffer base.

| Offset | Register | API use |
|---:|---|---|
| `0x00` | `NOC_TARG_ADDR_LO` | target address bits 0–31 |
| `0x04` | `NOC_TARG_ADDR_MID` | target upper address and routing bits; currently `0` |
| `0x08` | `NOC_TARG_ADDR_COORDINATE` | target/source coordinate |
| `0x0C` | `NOC_RET_ADDR_LO` | return address bits 0–31 |
| `0x10` | `NOC_RET_ADDR_MID` | return upper address and routing bits; currently `0` |
| `0x14` | `NOC_RET_ADDR_COORDINATE` | return/destination coordinate or multicast rectangle |
| `0x18` | `NOC_PACKET_TAG` | transaction tag; the API writes `0` |
| `0x1C` | `NOC_CTRL` | request, response, VC, and multicast flags |
| `0x20` | `NOC_AT_LEN_BE` | byte count or atomic instruction |
| `0x24` | `NOC_AT_LEN_BE_1` | upper length/byte-enable word; the API writes `0` |
| `0x28` | `NOC_AT_DATA` | atomic increment value |
| `0x2C` | `NOC_BRCST_EXCLUDE` | multicast exclusions |
| `0x40` | `NOC_CMD_CTRL` | write `1` to issue |

Before changing a buffer, generated code polls `NOC_CMD_CTRL` until it is
zero. It then writes the complete required register image and writes
`NOC_CMD_CTRL = 1` last. A zero means the NIU accepted the request, not that
the data transfer completed.

The target and return names follow packet flow:

| Operation | `TARG` fields | `RET` fields |
|---|---|---|
| Read | remote source | local response destination |
| Write/multicast | local source | remote destination(s) |
| Atomic increment | remote operand | local old-value destination |

Every ordinary issue returns the same `NoC` object, allowing chaining.

## Reads

```py
noc.read(src, src_coord, dst, size, return_coord=local_coord)
```

`read()` uses command buffer 1. `size` must be a Python `int` from 1 through
16 KiB. Its complete command image is:

| Register | Value |
|---|---|
| `NOC_CTRL` | `0x2090`: response-marked read on static VC 1 |
| `NOC_PACKET_TAG` | `0` |
| `NOC_TARG_ADDR_LO/MID/COORDINATE` | `src`, `0`, `src_coord` |
| `NOC_RET_ADDR_LO/MID/COORDINATE` | `dst`, `0`, local or explicit return coordinate |
| `NOC_AT_LEN_BE`, `NOC_AT_LEN_BE_1` | `size`, `0` |
| `NOC_CMD_CTRL` | `1`, written last |

The response carries the requested data. Use `read_batch()` to wait until a
group of reads is committed to its local destinations.

## Posted writes

```py
noc.write(src, dst, dst_coord, size)
```

`write()` uses command buffer 0. `size` must be a Python `int` from 1 through
16 KiB. Its complete command image is:

| Register | Value |
|---|---|
| `NOC_CTRL` | `0x2082`: posted write on static VC 1 |
| `NOC_PACKET_TAG` | `0` |
| `NOC_TARG_ADDR_LO/MID/COORDINATE` | `src`, `0`, initialized local coordinate |
| `NOC_RET_ADDR_LO/MID/COORDINATE` | `dst`, `0`, `dst_coord` |
| `NOC_AT_LEN_BE`, `NOC_AT_LEN_BE_1` | `size`, `0` |
| `NOC_CMD_CTRL` | `1`, written last |

Writes are posted and generate no destination acknowledgement. Exiting a
`write_batch()` proves that the NIU consumed and injected the source payloads.
It does not prove that the destinations stored them.

## Repeated read and write streams

Streams program invariant fields once and keep the command-buffer base,
scratch value, and send value in RISC-V registers. They are intended for hot
loops with at least two same-sized transfers:

```py
with noc.read_stream(tile_bytes, return_coord=local_coord) as reads:
  with reads.batch():
    reads.issue(src, src_coord, dst)
    reads.issue(next_src, next_coord, next_dst)

with noc.write_stream(tile_bytes) as writes:
  with writes.batch():
    writes.issue(src, dst, dst_coord)
    writes.issue(next_src, next_dst, next_coord)
```

`read_stream()` and `write_stream()` apply the same 1–16 KiB validation as
their ordinary operations. Entering a read stream writes the read control,
tag, both MID fields, return coordinate, and size fields. Each `issue()` waits
for readiness and updates `TARG_LO`, `TARG_COORDINATE`, and `RET_LO`.

Entering a write stream writes the write control, tag, both MID fields, local
source coordinate, and size fields. Each `issue()` updates `TARG_LO`,
`RET_LO`, and `RET_COORDINATE`.

A stream exclusively owns its operation's command buffer until context exit.
An ordinary operation using that buffer or a second stream of the same kind
raises `RuntimeError` during generation. Skipping an `issue()` in a runtime
branch is safe because the next issue updates every dynamic field.

Stream `issue()` methods return `None`. A nested `batch()` infers the number of
statically generated issues and waits when its context exits. Pass
`batch(count=runtime_count)` when a runtime loop or branch determines how many
issues execute.

## Multicast writes

```py
packets = noc.multicast(src, dst, rectangle, size,
                        exclude=0, along_y=False)
```

`multicast()` uses write buffer 0 and requires a positive Python integer size.
Unlike `write()`, it accepts more than 16 KiB and emits
`ceil(size / 16 KiB)` packets at generation time. It returns that packet count;
`WriteBatch.multicast()` includes all of those packets in its inferred count.

Each packet writes the ordinary posted-write image plus
`NOC_BRCST_EXCLUDE = exclude`. The base control value is `0xA1A2`: posted
broadcast, static VC 5, with path reservation. `along_y=True` adds
`NOC_CMD_BRCST_XY`.

For a multi-packet transfer:

1. The first packet reserves the path.
2. Every non-final packet sets `NOC_CMD_VC_LINKED`.
3. Packets after the first omit path reservation.
4. The final packet is unlinked, releasing the path.
5. Source and destination addresses advance by 16 KiB per packet.

If either address is a RISC-V register, `multicast()` copies it to a temporary
before advancing it, so the caller's register is not modified. The final
packet carries the remaining byte count.

## Atomic increment

```py
noc.atomic_inc(dst, dst_coord, value=1, return_coord=local_coord)
```

`atomic_inc()` uses command buffer 3 and emits:

| Register | Value |
|---|---|
| `NOC_CTRL` | `0x2091`: response-marked atomic on static VC 1 |
| `NOC_PACKET_TAG` | `0` |
| `NOC_TARG_ADDR_LO/MID/COORDINATE` | `dst`, `0`, `dst_coord` |
| `NOC_RET_ADDR_LO/MID/COORDINATE` | initialized atomic return address, `0`, local or explicit return coordinate |
| `NOC_AT_LEN_BE`, `NOC_AT_LEN_BE_1` | `0x107C` (increment/get with 32-bit wrap), `0` |
| `NOC_AT_DATA` | `value` |
| `NOC_CMD_CTRL` | `1`, written last |

NoC atomics operate on Tensix or Ethernet L1, not DRAM, MMIO, or PCIe memory.
The response writes the old value to `atomic_return`. Use `atomic_batch()` when
responses must be complete before proceeding.

## Completion batches

The public API groups asynchronous operations in context managers:

```py
with noc.read_batch() as reads:
  reads.issue(src, src_coord, dst, size)
  reads.issue(next_src, next_coord, next_dst, size)

with noc.write_batch() as writes:
  writes.issue(src, dst, dst_coord, size)
  writes.multicast(src, dst, rectangle, larger_size)

with noc.atomic_batch() as atomics:
  atomics.issue(semaphore, remote_coord)
```

The batch infers a count from its `issue()` calls and from the number of packets
generated by `multicast()`. Source-level counting is not sufficient when one
generated issue sits inside a runtime loop or conditional. Supply a Python
integer or RISC-V register in that case:

```py
with noc.read_batch(count=runtime_count) as reads:
  # Generated runtime loop issuing reads.
  reads.issue(src, src_coord, dst, size)
```

Internally, entering a batch snapshots and fences the corresponding global
status counter. Exiting successfully then:

1. Polls the matching buffer's `NOC_CMD_CTRL` until the final request is
   accepted.
2. Polls the status counter until `(current - start) >=u count`.
3. Emits a fence.

Status counters begin at `0xFFB2_0200 + (index << 16)`:

| Batch | Buffer | Counter offset | Completion represented |
|---|---:|---:|---|
| `read_batch()` | 1 | `0x08` | read responses received and committed |
| `write_batch()` | 0 | `0x2C` | posted write payloads consumed/injected |
| `atomic_batch()` | 3 | `0x00` | atomic responses received |

Python counts must be in `[0, 2^31)`. Unsigned subtraction makes the wait safe
across a 32-bit counter wrap as long as fewer than `2^31` completions are
expected. A batch wait is not emitted if Python exits its body with an
exception.

Batches use global per-NIU counters, so resident firmware and a kernel must not
share an NIU during the same batch. The API writes packet tag zero and does not
use hardware transaction IDs.

## Current limits

- Addresses are endpoint-local 32-bit values; every MID field is zero.
- Ordinary reads and writes do not split transfers larger than 16 KiB.
- Multicast size splitting is unrolled while generating the kernel, so its
  total size must be a Python integer.
- There is no inline-write API or public command-buffer API.
- NoC initialization and concurrent NIU ownership remain firmware/program
  responsibilities.

## Sources

- [`ttk/noc.py`](../ttk/noc.py), the implementation described here
- [Blackhole NoC memory map](../../tt-isa-documentation/BlackholeA0/NoC/MemoryMap.md)
- [Blackhole NoC counters](../../tt-isa-documentation/BlackholeA0/NoC/Counters.md)
- [Blackhole NoC atomics](../../tt-isa-documentation/BlackholeA0/NoC/Atomics.md)
- [TT-Metal Blackhole NoC parameters](../../tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_parameters.h)
