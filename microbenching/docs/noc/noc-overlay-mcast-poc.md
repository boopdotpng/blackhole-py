## Current Finding

- Blackhole stream-overlay mcast works from a source-endpoint stream when using one of streams 0..3.
- Program `STREAM_MCAST_DEST_NUM` to 1 for this PoC; the NoC mcast rectangle controls the actual worker fanout.
- Setting `STREAM_MCAST_DEST_NUM` to the literal receiver count can wedge the stream phase before any posted request is issued.
- NoC1 rectangles still need the usual flipped/transformed coordinate handling.

## Run 2026-06-21T19:45:10-04:00

- Scope: arm one Blackhole NoC overlay source-endpoint stream as a multicast write.
- The stream reads one source L1 buffer and writes the same payload into a receiver rectangle.
- Current status: diagnostic only; this run used stream 8, but Blackhole stream-overlay multicast requires one of streams 0..3.
- Timing starts before `STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO` and ends after the stream phase completes.

| source | noc | stream | rect | dests | status | bytes | cycles | src B/cyc | delivered B/cyc | bad payloads | wr ack d | posted d | nonposted d | rd resp d | wait | debug8 | debug9 |
|---|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1,2` | 0 | 8 | `2,2->3,2` | 2 | done | 16384 | 315 | 52.013 | 104.025 | 1 | 0 | 1 | 0 | 0 | 0x00000001 | 0x00000c00 | 0x00000000 |

| receiver | payload ok | first | last |
|---|---|---:|---:|
| `2,2` | True | 0xe77a0000 | 0xe77a0fff |
| `3,2` | False | 0x00000000 | 0x00000000 |

## Run 2026-06-21T19:49:41-04:00

- Scope: arm one Blackhole NoC overlay source-endpoint stream as a multicast write.
- The stream reads one source L1 buffer and writes the same payload into a receiver rectangle.
- Blackhole stream-overlay multicast requires one of the multicast-capable streams 0..3.
- Current status: the stream-0..3 phase sequence reaches ready but times out before issuing a posted mcast request.
- Timing starts before `STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO` and ends after the stream phase completes.

| source | noc | stream | rect | dests | status | bytes | cycles | src B/cyc | delivered B/cyc | bad payloads | wr ack d | posted d | nonposted d | rd resp d | wait | debug8 | debug9 |
|---|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1,2` | 0 | 0 | `2,2->3,2` | 2 | done-timeout | 16384 | 130000051 | 0.000 | 0.000 | 2 | 0 | 0 | 0 | 0 | 0x0000002c | 0x00130345 | 0x00000000 |

| receiver | payload ok | first | last |
|---|---|---:|---:|
| `2,2` | False | 0x00000000 | 0x00000000 |
| `3,2` | False | 0x00000000 | 0x00000000 |

## Run 2026-06-21T19:56:42-04:00

- Scope: arm one Blackhole NoC overlay source-endpoint stream as a multicast write.
- The stream reads one source L1 buffer and writes the same payload into a receiver rectangle.
- Blackhole stream-overlay multicast requires one of the multicast-capable streams 0..3.
- `STREAM_MCAST_DEST_NUM` is programmed to 1 for this PoC; the NoC mcast rectangle controls the actual fanout.
- tt-metal exposes the register map, but its `stream_dram_write` helper clears mcast state and uses the overlay as unicast.
- Timing starts before `STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO` and ends after the stream phase completes.

| source | noc | stream | rect | dests | status | bytes | cycles | src B/cyc | delivered B/cyc | bad payloads | wr ack d | posted d | nonposted d | rd resp d | wait | debug8 | debug9 |
|---|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1,2` | 0 | 0 | `2,2->5,2` | 4 | done | 16384 | 649 | 25.245 | 100.980 | 0 | 0 | 1 | 0 | 0 | 0x00000001 | 0x00000c00 | 0x00000000 |

| receiver | payload ok | first | last |
|---|---|---:|---:|
| `2,2` | True | 0xe77a0000 | 0xe77a0fff |
| `3,2` | True | 0xe77a0000 | 0xe77a0fff |
| `4,2` | True | 0xe77a0000 | 0xe77a0fff |
| `5,2` | True | 0xe77a0000 | 0xe77a0fff |

| curr phase | phase header | remote dest | mcast dest | mcast num | msgs recv | msg ptr | msg wr | all pushed | can push | ready push | remote space 0 | remote space 1 | remote space 2 | remote space 3 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0x00000000 | 0x00000000 | 0x00000082 | 0x00005085 | 1 | 0 | 0x00013001 | 0x00013001 | 1 | 1 | 0 | 0x01340400 | 0x02860400 | 0x00800400 | 0x00000400 |
