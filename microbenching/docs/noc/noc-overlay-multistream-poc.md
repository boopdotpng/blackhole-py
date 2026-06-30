
## Run 2026-06-21T19:45:10-04:00

- Scope: arm multiple Blackhole NoC overlay source-endpoint streams on one source core.
- Each stream writes a distinct source L1 buffer to one peer L1 destination buffer.
- Timing starts before the first `STREAM_SOURCE_ENDPOINT_NEW_MSG_INFO` and ends after all stream phases complete.

| source | noc | streams | status | bytes/stream | total bytes | cycles | B/cyc | bad payloads | wr ack d | posted d | nonposted d | rd resp d | wait xor | debug8 xor | debug9 xor |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1,2` | 0 | 4 | done | 16384 | 65536 | 1159 | 56.545 | 0 | 0 | 4 | 0 | 0 | 0x00000000 | 0x00000000 | 0x00000000 |

| peer | payload ok | first | last |
|---|---|---:|---:|
| `2,2` | True | 0xd10d0000 | 0xd10d00ff |
| `3,2` | True | 0xd10d0100 | 0xd10d01ff |
| `4,2` | True | 0xd10d0200 | 0xd10d02ff |
| `5,2` | True | 0xd10d0300 | 0xd10d03ff |
