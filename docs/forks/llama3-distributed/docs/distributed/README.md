# Independent Blackhole distributed bring-up

Status, September 7, 2026: **design and CPU-tested building blocks, not working
multi-card inference**. This implements our own BHP1 packet format and static
mesh plan, with no tt-metal imports, copied kernels, launch messages, or fabric
headers. Hardware register definitions and the installed system firmware's
status ABI are necessarily hardware-specific. Stock firmware still trains the
SerDes; avoiding tt-metal does not require rewriting PHY training firmware.

Per the request to document until card 0 returns, no peer packets were sent and
no firmware was uploaded. Card 0 was never opened. Existing inference code and
its uncommitted optimization work were left intact.

## What is implemented

- `distributed/probe.py`: card-1-only local ERISC status inspection, avoiding
  `Device`/`PCIDevice` constructors and their reset/power/runtime side effects.
- `distributed/protocol.py`: original BHP1 codec and bounded stop-and-wait
  sender/receiver reference, with stale-session and duplicate rejection.
- `fw/erisc/bhp.c`: matching freestanding C codec, cross-compiled for RV32IM.
- `fw/erisc/raw_tx.c`: register-level raw TX primitive. This is an object file,
  **not a loadable application**. It requires queue ownership and configuration.
- `distributed/mesh.py`: independent, deterministic static route compiler.
- `distributed/tp.py`: TP=2 partition plan, CPU projection reference, and a
  reproducible estimate. It is not wired into `Llama3Decode`.

The C codec is deliberately straightforward, including a slow bitwise CRC for
bring-up. Neither this codec nor stop-and-wait is claimed to saturate 400 Gb/s.

## Actual card 1 observations

[Raw two-sample record](card1-status.json): P150A, system firmware 19.13.1.0.
All 12 logical endpoints responded and all firmware heartbeat values changed
between samples approximately 100 ms apart.

| Logical ERISC | Translated NoC0 | Reported status | Training |
|---|---|---|---|
| 0–3 | (20..23,25) | unused | skipped |
| 4–8 | (24..28,25) | down | manual EQ timeout; speed field 400 |
| 9 | (29,25) | up | pass; speed field 400 |
| 10 | (30,25) | down | manual EQ timeout; speed field 400 |
| 11 | (31,25) | up | pass; speed field 400 |

This establishes local firmware liveness and reported trained links. It does
not establish remote card identity, cable/cage mapping, payload correctness,
RTT, sustained bandwidth, or error rate. Do not assume the two up endpoints
are the two halves of one cable. The speed field on a down link is not proof
of usable bandwidth. No attempt was made to repair down links.

The probe reads `eth_status_t` at L1 `0x7cc00`: postcode, port state, training
state, speed at offsets 0/4/8/12 and four heartbeat words at offset 112. It
allocates/configures only its own KMD TLB. Its ABI is version-sensitive; keep
raw words with every result. Translated ETH coordinates enumerate the twelve
**unharvested logical** endpoints, not the fourteen physical channel IDs.

```sh
PYTHONPATH=. python3 -m distributed.probe --device 1 --output /tmp/card1.json
make -C fw/erisc
PYTHONPATH=. python3 -m unittest discover -s tests -p test_distributed.py -v
PYTHONPATH=. python3 -m distributed.tp --latency-us 5
```

The card-0 restriction is intentional. When card 0 becomes available, explicitly
extend the probe's device policy before using it there.

## Our packet: BHP1 v1

Use raw TX (`ETH_TXQ_CMD=1`) and raw RX. Do not use TT-link remote L1 writes,
TT-link sequence headers, tt-metal fabric headers, or a TCP stack. The MAC
still emits ordinary Ethernet framing; raw means we own its payload.

Wire: `DA[6] | SA[6] | EtherType[2] | BHP1[32] | payload[N] | pad | FCS`.
Ethernet outer fields use network order. Proposed laboratory EtherType is
`0x88b5` (local experimental use, not a globally assigned BHP protocol).
Use locally administered unicast MACs provisioned per endpoint. Hardware TX
header table supplies MACs/EtherType and MAC supplies FCS. No VLAN/IP/UDP in v1.

All multibyte BHP1 fields are **little endian**, intentionally matching ERISC
and the tensor storage. There are no packed-struct casts in the C codec.

| Byte offset | Bytes | Field |
|---|---:|---|
| 0 | 4 | literal ASCII `BHP1` |
| 4 | 1 | version = 1 |
| 5 | 1 | kind: DATA=1, ACK=2, PING=3 |
| 6 | 2 | flags = 0, reject unknown bits |
| 8 | 4 | nonzero host-installed session epoch |
| 12 | 4 | nonzero sequence, starting at 1 per directed peer stream |
| 16 | 2 | source rank |
| 18 | 2 | destination rank |
| 20 | 2 | registered destination slot ID |
| 22 | 1 | remaining hop budget, at least 1 |
| 23 | 1 | reserved = 0 |
| 24 | 4 | payload bytes, 0..8192 |
| 28 | 4 | standard reflected CRC-32, as Python `zlib.crc32` |
| 32 | N | payload; FP32 little endian for reduction partials |

CRC covers header bytes 0..27 followed by the exact payload; it excludes the
CRC field itself, Ethernet padding, and FCS. CRC is diagnostic integrity, not
authentication. An ACK has zero payload and echoes epoch/sequence/slot, swaps
ranks, and uses hop budget 1 for the implemented direct-peer reference.
PING uses the same ordering/retry rules as DATA and may carry test patterns.

The codec consumes exactly `32+N` bytes, not a complete Ethernet frame. The
future RX adapter must use hardware frame-length metadata, strip the outer
header and padding, validate truncation before parsing, and then pass that
exact slice. A zero-payload ACK needs Ethernet minimum-frame padding.
An 8192-byte partial needs an **8224-byte Ethernet payload MTU**, or 8242 bytes
from destination MAC through FCS. Switch configurations would need to allow
that size. Ethernet preamble/SFD and IFG add another 20 byte-times per frame.
Smaller-MTU fragmentation is not implemented; reject unsupported MTUs.

### Transfer and ownership

The host installs an epoch, peer MAC/rank, and slot table at both ends before
traffic. A slot resolves to a bounded owned L1 buffer and its operation; the
wire never supplies an arbitrary L1/NoC address. Slot ownership is also the
first credit scheme: one outstanding packet per directed peer stream.

1. Producer finishes its NoC write into TX staging, then publishes ready with
   proper ordering. ERISC encodes the header, retains a retry copy, and sends.
2. Receiver waits for RX writes to finish, validates frame/CRC/peer/epoch/slot/
   length/sequence, copies into owned staging and publishes local readiness.
3. Receiver sends ACK only once ownership is safely transferred. Duplicate
   sequence re-ACKs without copying or reducing a second time. A conflicting
   duplicate, skipped sequence, unknown slot, or stale epoch is rejected.
4. Sender frees retained data after the matching application ACK, not just
   TX-command acceptance. On timeout it retransmits identical bytes, bounded
   by a retry budget. Exhaustion aborts the session and preserves live buffers.
5. Consumer sums each partial exactly once on Tensix, adds residual once, then
   returns slot credit. The next receive may not overwrite an unconsumed slot.

`Receiver.receive()` is a synchronous CPU model: its caller must consume the
returned payload before the next call. The C device slot state machine and
credit publication are still to implement. ACK proves staging, not completion
of the tensor operation. Successful collective completion also requires the
local sum and its NoC writes to complete.

Reset installs a fresh epoch on all ranks, drains old RX/TX state, and resets
sequence numbers; do not reuse an epoch or wrap sequences within a session.
For now this is host-coordinated, with no discovery broadcasts or HELLO parser.

### ERISC hardware adapter still needed

An Ethernet tile has 512 KiB L1, two RISC-V cores, and three TX/RX queues. Reserve
system firmware's upper 64 KiB; negotiate ownership of lower memory and the
chosen queue/header entry. Do not assume an unused queue is unowned. Do not
reset E0 or replace its firmware on a trained link. E1 is a candidate for our
persistent service, subject to confirming it is unowned and providing our own
CRT/linker/cache/NoC initialization and lifecycle handshake.

The raw TX primitive uses `0xffb90000 + queue*0x1000`: source at +0x14, size at
+0x18, header selector at +0x80, command at +0x04. Read CMD before STATUS +0x08
bit 16 to enforce command ordering. Provision MAX_PKT_SIZE_BYTES at +0x0c
for the complete BHP packet; the primitive rejects implicit fragmentation. For raw TX, clearing this bit means
hardware finished reading payload; it does not mean remote delivery. This is
different from TT-link mode, where hardware may reread L1 for retries.

For RX, configure one exact-match classifier flow for our destination MAC and
EtherType, preserving firmware management flows; route it to an owned raw RX
queue and enable frame-length metadata. Queue base is
`0xffb94000 + queue*0x1000`. RX BUF_PTR alone is insufficient: writes may still
be outstanding. The documented conservative committed boundary is
`BUF_PTR - OUTSTANDING_WR_CNT*96`, with a monotonic high watermark and careful
wrap handling. Avoid enabling an unchecked wrapping ring. Start with a bounded
nonwrapping capture and fail before capacity; then implement a credited ring.
Do not equate packet-end counter changes with completion of L1 writes.

Still missing: exact classifier rule installation/restoration, RX frame
metadata parsing, cache invalidation, ring ownership, E1 boot/stop loader,
firmware-management coexistence, NoC staging/doorbells, and device-side retry/
credit state. These are the prerequisites for a real ERISC ping test. There is
intentionally no command here that uploads an incomplete image.

## Our mesh format

The host owns topology and validates reciprocal peer identity before installing
routes. Rank IDs are job-local uint16s, not PCIe device indices or physical
coordinates. The following is an **illustrative fixture, not discovered cabling**:

```json
{"version":1,"epoch":42,"ranks":[0,1,2],"links":[
  {"a":[0,4],"b":[1,5]},
  {"a":[1,6],"b":[2,7]}
]}
```

Each endpoint is `[rank, logical_erisc]`. `distributed.mesh.routes()` rejects
port reuse/disconnection and compiles `destination -> next_rank, output_port`
using deterministic shortest paths. Actual device/BDF/MAC identities live in
a separate host inventory, validated before launch. TP=2 needs one direct edge
and no on-chip router. Start there, with a pinned link per stream.

Future multi-hop forwarding preserves end-to-end rank/session/sequence/slot,
rewrites outer MACs, decrements hop budget and recomputes CRC. Reject forwarding
when budget is 1. Return ACKs follow an independently compiled reverse route,
with an adequate initial hop budget (the current reference ACK is direct-only).
Forwarding and hop-by-hop credits are **design only**, not implemented by the
route compiler. Start with a tree to avoid cyclic buffer dependencies; arbitrary
cyclic meshes require deadlock-free virtual channels or another proven credit
scheme. Do not stripe individual packets across links until reorder/reassembly
and per-link credits exist. Static routes avoid an initial distributed control
plane, not the need for flow control.

## QSFP-DD switches

QSFP-DD is a connector/module form factor, not a promise of switch compatibility.
The P150 has four passive 800-Gb/s ports, each served by two 400-Gb/s Ethernet
tiles. Tenstorrent currently documents those ports as connecting exclusively to
Blackhole add-in cards. **A conventional Ethernet switch is not a supported
plug-in substitute for direct cables.**

At controller level, standard MAC frames and optional VLAN/IP headers are
supported, so a custom switched L2 design is technically plausible. Our raw
protocol preserves that option. It would still require proving all of:
compatible passive cable pinout and reach, two-400G lane mapping/breakout,
SerDes training/FEC, independent switch-facing link bring-up without the stock
Blackhole peer handshake, MAC learning/static forwarding, MTU, and loss/credit
behavior under congestion. An 800G label does not prove a matching PHY mode.
The current host-routed mesh and Ethernet-switch topology are separate designs.

Do not buy a switch based on this proposal. Ask Tenstorrent for a supported
PHY/cable/switch combination first; absent that, treat switch attachment as a
separate PHY and firmware experiment. A custom protocol cannot fix incompatible
lane wiring or firmware training assumptions.

## Two-card validation when card 0 is free

1. Inventory both cards, firmware versions, logical/physical port mapping and
   reciprocal remote IDs. Confirm that the chosen queues/E1 cores are unowned.
2. Implement and first validate our E1 launch/stop and bounded raw RX capture on
   card 1. A locally configured loopback can prove local TX/RX only; it needs
   its own explicit setup/restore and cannot establish card-to-card operation.
3. Reserve one direct trained pair and memory on both ends, install identical
   session/slot tables and our classifier entries, then run patterned PING
   traffic in both directions: 0, 1, 16, 64, 4096, 8192 payload bytes.
4. Verify every byte and sequence, inject software DATA/ACK loss and duplicates,
   test full slots, corrupted CRC, stale epochs, timeout, and link loss. Verify
   no repeated reductions. Measure RTT distribution and counters, not merely
   whether a TX command cleared.
5. Measure streaming payload GB/s separately from ping latency and host polling.
   Add credits/windowing/ACK batching only with tests. Test one 400G endpoint
   before considering both halves of a QSFP-DD port.
6. Integrate a two-card FP32 SUM of 2048 values, then a TP transformer layer,
   then all 16 layers and distributed argmax. Validate logits against a CPU
   TP reference and assess token changes caused by the new reduction order.
7. Benchmark batch-one fixed-context decode, matching the existing baseline's
   exclusion of startup and prompt ingestion. Log host, NoC, ERISC, reduction,
   and compute time separately, plus link errors/retries.

## Evidence and provenance

Our code is original; these are specifications/ABI evidence, not build inputs:

- [Blackhole Ethernet tile specification](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/EthernetTile/README.md)
- [TX/RX registers, ordering and framing](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/EthernetTile/EthernetTxRx.md)
- [RX classifier and metadata](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/EthernetTile/EthernetRxClassifier.md)
- [Baby RISC-V and system-firmware ownership](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/EthernetTile/BabyRISCV/README.md)
- [P150 ports, cable support and DRAM specifications](https://docs.tenstorrent.com/aibs/blackhole/index.html)
- Installed firmware ABI cross-check: local `tt-metal/.../blackhole/eth_fw_api.h`
  defines `eth_status_t`; UMD `device/coordinates/blackhole_coordinate_manager.cpp`
  documents the logical-to-translated mapping. Neither implementation is copied.

See [TP partitioning and performance model](tensor-parallel.md).
