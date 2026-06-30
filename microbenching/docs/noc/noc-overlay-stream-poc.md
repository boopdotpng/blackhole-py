
## Run 2026-06-21T19:35:02-04:00

- Scope: one-shot Blackhole NoC overlay source endpoint to remote L1 destination buffer
- Programming sequence mirrors tt-metal `blackhole/stream_interface.h::stream_dram_write`.
- Timing starts immediately before `STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO` and ends after stream phase completion.

| source | peer | noc | stream | status | bytes | cycles | B/cyc | payload ok | first | last | wr ack d | posted d | nonposted d | rd resp d | wait | debug8 | debug9 | buf space | remote space | can push | ready push |
|---|---|---:|---:|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1,2` | `2,2` | 0 | 8 | done | 16384 | 319 | 51.361 | True | 0xd00d0000 | 0xd00d0fff | 0 | 1 | 0 | 0 | 0x00000001 | 0x00000c00 | 0x00000000 | 225280 | 46923776 | 1 | 0 |
