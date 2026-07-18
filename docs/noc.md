# noc documentation, as blackhole-py uses it

There are 5 basic NoC operations: 
- unicast read 
- unicast write 
- multicast write
- inline write
- atomic increment,

an overlay stream (niu state machines in hardware) that you can use to transfer large amounts of data around the chip without holding up the risc-v processor on the chip, 

and completion / status counters so you can figure out if your request was fulfilled. 

## hardware per tile
Every tile has access to two NoCs (through two NIUs), going in opposite directions: 
- noc 0 starts at 0,0 (top left) and can only transfer packets down and right. 
- noc 1 starts at the bottom-most tile (this differs on p100a vs p150a) and can only transfer left and up

In addition to the two NIUs, each tile has 64 overlay streams (shared by both NIUs) that can be configured for long-running transfers. 

### NiU
I'm not sure how tenstorrent defines this (this is purely my speculation based on microbenches), but on every NIU there is a router with 5 ports: north, south, east, west, and a port connecting to the tile's L1. When a packet goes through a tile, it passes through the router, which decides what direction to forward the packet in or to write it into the tile's L1. 

This is where the concept of VCs, static VCs, path reserve, priority, etc come into play, but from my microbenches, this is completely unnecessary overhead that almost never makes a real difference to throughput or contention. 

## an average noc request 
For the five basic NoC operations, the flow is generally: 
- make sure there is no existing command (poll `noc_cmd_ctrl = 0`)
- snapshot completion counter
- write all your config to the mmio registers for the NoC you want to use 
- poke the niu_cmd_ctrl register, which triggers the transaction
- read back the control register (orders the risc-v store before the counter read)
- poll on a completion counter or wait for the returned ack (if nonposted, more info later)
- fence

### Configuration registers

Each NIU has four identical request initiators, which we call **command
buffers**. A command buffer is an MMIO register block containing one complete
NoC request. Because operations wait until submission has consumed the command
image, `noc.py` uses buffer 0 for every request type; the other three remain
available for a future concurrent submitter.

#### Command-buffer layout

The names below are the semantic names used by `noc.py`. The hardware calls the
source group `NOC_TARG_ADDR` and the target group `NOC_RET_ADDR`; those names
are awkward because their roles change with the request type.

| Offset | `noc.py` name | Contents |
|---:|---|---|
| `0x00` | `SOURCE_ENDPOINT + 0` | Low 32 bits of the source address |
| `0x04` | `SOURCE_ENDPOINT + 4` | High 32 bits of the source address |
| `0x08` | `SOURCE_ENDPOINT + 8` | Source coordinate |
| `0x0c` | `TARGET_ENDPOINT + 0` | Low 32 bits of the target address |
| `0x10` | `TARGET_ENDPOINT + 4` | High 32 bits of the target address |
| `0x14` | `TARGET_ENDPOINT + 8` | Target coordinate or multicast rectangle |
| `0x18` | `PACKET_TAG` | Four-bit transaction ID in bits `10..13` |
| `0x1c` | `PACKET_OPTIONS` | Operation, completion, multicast, routing, and VC flags |
| `0x20` | `PACKET_BYTES` | Byte count, byte enables, or atomic encoding |
| `0x24` | `PACKET_BYTES + 4` | Upper 32 bits; currently written as `0` |
| `0x28` | `IMMEDIATE_DATA` | Inline-write value or atomic operand |
| `0x2c` | `MULTICAST_EXCLUSIONS` | Optional multicast recipient filtering |
| `0x40` | `SEND_REQUEST` | Write `1` to submit the configured request |

There are two special cases:

- An inline write puts its remote destination in the source endpoint group;
  the target group is unused.
- An atomic puts the remote operand address in the source group and the
  optional response address in the target group.

#### `PACKET_BYTES`

For ordinary transfers this is the exact number of bytes moved:

| Request | Meaning of `PACKET_BYTES` |
|---|---|
| Read | Bytes read from the remote source into local L1 |
| Write | Bytes copied from local L1 to the remote target |
| Multicast write | Bytes copied to **each** recipient |
| Inline write | `0xF`, representing four enabled bytes |
| Atomic increment | Atomic-operation encoding, not a byte count |

The atomic increment encoding used here is
`(1 << 12) | (31 << 2) == 0x107c`, meaning increment-and-get on a 32-bit word.
An ordinary Blackhole NIU request can move at most 16 KiB. Larger logical
transfers must be split into multiple requests or use the overlay engine.

#### `PACKET_OPTIONS`

`NoC._packet_options()` builds this register from the requested operation and
the policy fields on `NoC`:

| Bits | Hardware field | Behavior in `noc.py` |
|---:|---|---|
| `0..1` | Request type | `0` read, `1` atomic, or `2` write |
| `3` | Inline write | Set only by `inline_write()` |
| `4` | Response marked | Set for reads and for non-posted writes/atomics |
| `5` | Multicast | Set only by `multicast_write()` |
| `6` | VC linked | Set when `linked=True` |
| `7` | Static VC | Always set |
| `8` | Multicast path reservation | Controlled by `reserve_multicast_path`; default `True` |
| `13..15` | Static VC number | `unicast_vc=1` or `multicast_vc=4` by default |
| `16` | Y-major multicast | Controlled by `multicast_along_y`; default `False` |
| `17` | Include sender | Controlled by `multicast_include_sender`; default `False` |
| `27..30` | Arbitration priority | Controlled by `arbitration_priority`; default `0` |

All omitted and reserved bits are written as zero.

For writes and atomics, `posted` controls bit 4 and what completion means:

```text
posted=True:   wait until the local NIU has sent the request
posted=False:  wait for an acknowledgement/response from the destination
```

A posted write completing does not, by itself, prove that the destination has
already committed the data.

`linked=True` says that another request will continue the same transaction and
retain its VC/path. The final request in the sequence must use `linked=False`,
and every request in the sequence must use a compatible destination and VC.
Incorrectly using this flag can stall the NoC.

#### `MULTICAST_EXCLUSIONS`

A multicast normally sends to every eligible tile in the target rectangle.
`MULTICAST_EXCLUSIONS` is an additional hardware-encoded filter that can turn
that rectangle into a non-rectangular recipient set:

```text
target rectangle − excluded region/filter = actual recipients
```

It is not a simple one-bit-per-core bitmap. The current `multicast_write()` API
does not expose the encoding and writes `0`, meaning no additional filtering.
The initiating tile may still be excluded independently because
`multicast_include_sender` defaults to `False`.

For a non-posted multicast, `destinations` must equal the actual number of
recipients. A value that is too high can wait forever for acknowledgements that
will never arrive; a value that is too low can return before every recipient
has acknowledged the write.

### a note about packets 
The max packet size on blackhole is 16kb; a packet generally looks like 
```text
64-byte packet header........up to 256 flits containing data 
```

Inline writes are very fast because they put the data inside the 64-byte packet header (not all of it is actually used). 

The packet header contains information about how to route the packet through the NoC, so that every router knows what to do with the packet. If you submit a transfer exceeding 16kb, the hardware will automatically split your transfer up into multiple packets. You don't need to loop in risc-v to submit large transfers. 

### completion counters 
There are two buckets of completion counters, one transaction-id based, and a general set of completion counters for all 4 command buffers and the overlay stream on the NIU. The NIU actually has 64 lifecycle counters (to track various noc related things, some of these are debug), but only a few are actually useful as completion conditions: 

 ```text
   Indices  0–15   master cumulative event counters (32-bit wrapping)
   Indices 16–31   REQS_OUTSTANDING_ID(0–15)
   Indices 32–47   WRITE_REQS_OUTGOING_ID(0–15)
   Indices 48–61   slave cumulative event counters
 ```

#### 1. Master-side cumulative counters

These counters describe traffic initiated by this NIU. They are cumulative
32-bit event totals rather than live outstanding counts, so software normally
snapshots them or compares them against its own number of issued requests.
They are shared by all four command buffers and all transaction IDs on the
NIU.

| Index | Counter | Meaning |
|---:|---|---|
| 0 | `NIU_MST_ATOMIC_RESP_RECEIVED` | Atomic response received and written to the return address |
| 1 | `NIU_MST_WR_ACK_RECEIVED` | Non-posted write acknowledgement received |
| 2 | `NIU_MST_RD_RESP_RECEIVED` | Read response received and written to the return address |
| 3 | `NIU_MST_RD_DATA_WORD_RECEIVED` | Read-response data flits received |
| 4 | `NIU_MST_CMD_ACCEPTED` | Request obtained its first-hop VC; this is acceptance, not completion |
| 5 | `NIU_MST_RD_REQ_SENT` | Read-request packets sent |
| 6 | `NIU_MST_NONPOSTED_ATOMIC_SENT` | Response-marked atomic packets sent |
| 7 | `NIU_MST_POSTED_ATOMIC_SENT` | Posted atomic packets sent |
| 8 | `NIU_MST_NONPOSTED_WR_DATA_WORD_SENT` | Non-posted write data flits sent |
| 9 | `NIU_MST_POSTED_WR_DATA_WORD_SENT` | Posted write data flits sent |
| 10 | `NIU_MST_NONPOSTED_WR_REQ_SENT` | Non-posted write packets sent |
| 11 | `NIU_MST_POSTED_WR_REQ_SENT` | Posted write packets sent |
| 12 | `NIU_MST_NONPOSTED_WR_REQ_STARTED` | Non-posted write packets started |
| 13 | `NIU_MST_POSTED_WR_REQ_STARTED` | Posted write packets started |
| 14 | `NIU_MST_RD_REQ_STARTED` | Read-request packets started |
| 15 | `NIU_MST_NONPOSTED_ATOMIC_STARTED` | Non-posted atomic requests started |

Here, a data "word" means one 512-bit / 64-byte NoC data flit. The most
useful cumulative completion events are:

```text
RD_RESP_RECEIVED      read response has landed at the return NIU
WR_ACK_RECEIVED       remote non-posted write has been acknowledged
ATOMIC_RESP_RECEIVED  non-posted atomic response has landed
```

These counters work well when one software owner knows exactly how many
operations the whole NIU has issued. The transaction-ID counters below are
usually easier when several independent groups are in flight.

#### 2. Transaction-ID-specific counters

`PACKET_TAG` contains a four-bit software-selected transaction ID (`0..15`).
The ID is an accounting tag, not a hardware-allocated handle: requests that
reuse an active ID are deliberately merged into the same counter bucket. The
buckets are per NIU, so NoC 0 / TID 5 and NoC 1 / TID 5 are independent.

##### `NIU_MST_REQS_OUTSTANDING_ID(tid)`

This is an eight-bit live count of response-bearing packets that have not yet
returned their expected response:

| Operation | Increment | Decrement |
|---|---:|---|
| Read | One per resulting packet | When each read response is stored at the return NIU |
| Non-posted write | One per resulting packet | When each write acknowledgement arrives |
| Non-posted atomic | One | When its response is stored at the return NIU |
| Posted write or atomic | None | None |
| Non-posted inline write | One | When its acknowledgement arrives |
| Posted inline write | None | None |

Consequently,

```text
REQS_OUTSTANDING_ID(tid) == 0
```

proves that all currently tracked response-bearing requests with that ID have
completed at the return NIU. For a read, the returned data has been written to
its local destination. For a non-posted write, the remote write has been
acknowledged. Posted operations never enter this counter, so zero says nothing
about their remote completion.

This is the only counter array that supports return-to-zero notification via
`NIU_TRANS_COUNT_RTZ_SOURCE` and the NIU interrupt machinery.

##### `NIU_MST_WRITE_REQS_OUTGOING_ID(tid)`

This is an eight-bit live count of non-inline write packets whose payload has
not yet been completely read from the initiating tile's source memory:

| Operation | Uses this counter? |
|---|---:|
| Posted non-inline write | Yes |
| Non-posted non-inline write | Yes |
| Byte-enable non-inline write | Yes, as one request |
| Inline write | No |
| Read or atomic | No |

Therefore,

```text
WRITE_REQS_OUTGOING_ID(tid) == 0
```

means the NIU no longer needs the source L1 data for those writes. The source
buffer can be reused, but this does not prove that a posted write has reached
its destination. This counter does not have a return-to-zero interrupt.

Automatic splitting contributes one count per generated packet. For example,
a 40 KiB transfer tagged with TID 5 contributes three counts: 16 KiB, 16 KiB,
and 8 KiB. Because both TID counter arrays are only eight bits wide, software
must avoid having enough same-ID packet counts in flight to overflow them.

#### 3. What zero proves

| Operation | `WRITE_REQS_OUTGOING_ID(tid) == 0` | `REQS_OUTSTANDING_ID(tid) == 0` |
|---|---|---|
| Read | Not applicable | Return data has landed at the return NIU |
| Posted write | Source L1 is reusable | Always zero; no remote-completion guarantee |
| Non-posted write | Source L1 is reusable | Remote write has been acknowledged |
| Posted atomic | Not applicable | Always zero; no remote-completion guarantee |
| Non-posted atomic | Not applicable | Atomic response has been received |
| Posted inline write | Not applicable | Always zero |
| Non-posted inline write | Not applicable | Remote write has been acknowledged |

For a non-posted write, the two useful completion points are:

```text
submit
   │
   ├── WRITE_REQS_OUTGOING_ID(tid) becomes zero
   │       source L1 can be reused
   │
   └── REQS_OUTSTANDING_ID(tid) becomes zero
           destination has acknowledged the write
```

For a posted write there is no acknowledgement, so the outgoing counter can
only prove source-side completion. If software needs proof of remote arrival,
it must follow the posted writes with an appropriately ordered non-posted
request and wait for that response.

## overlay streams 

A stream is a hardware configurable state machine containing: 
- source and destination configuration
- phase state
- l1 ring buffer pointers
- message counts
- destination space credits
- source-read completion tracking
- remote tile coordinates and stream id
- selected NoC

A tensix tile has 64 streams, a dram tile has 16. 

To transfer between two tiles, you configure one transmitting stream on the source tile and one receiving stream on the destination tile. Payloads remain in l1i see