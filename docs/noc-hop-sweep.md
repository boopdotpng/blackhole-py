
# Blackhole NoC Hop Sweep

Goal: estimate whether same-row peer-tile L1 unicast latency changes with
logical x distance on NoC0 and NoC1, without using DRAM writes or multicast.

The harness lives in `examples/riscv_noc_hop_sweep.py` and reuses the peer
unicast kernels from `examples/riscv_noc_bench.py`.

## Method

- NoC0: choose the left edge of a logical row as source, then sweep peers to the
  right.
- NoC1: choose the right edge of a logical row as source, then sweep peers to
  the left.
- Traffic is one active BRISC issuing peer L1 reads/writes to one passive peer
  tile at a time.
- `logical dx` is the difference in logical X coordinate. Harvested/missing
  columns mean this is not guaranteed to equal physical router count.
- Rows time command issue, read-response flush, or write-ack barrier in cycles.

## First Observation

The 2026-06-06 row-2 sweep was flat from logical dx 1 through 13. That suggests
this benchmark is dominated by fixed command/NIU/ack latency or that logical
same-row distance is not exposing physical router delay. A more router-focused
follow-up should inspect physical NoC coordinate mapping and possibly use
lower-level status/config registers or traffic patterns with enough in-flight
data to expose per-hop effects.

## Run 2026-06-06T23:20:54-04:00

- Iterations per test: `1000`
- Traffic: same-row peer-tile L1 unicast only; no DRAM writes and no multicast
- Direction policy: NoC0 sweeps peers to the right of the source; NoC1 sweeps peers to the left

| noc | source | peer | logical dx | read4 cmd | read4 flush | read64 flush | read256 flush | write4 cmd | write4 barrier | write64 barrier | write256 barrier |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `1,2` | `2,2` | 1 | 24.998 | 230.996 | 222.996 | 230.996 | 22.998 | 228.996 | 220.996 | 221.004 |
| 0 | `1,2` | `3,2` | 2 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.003 |
| 0 | `1,2` | `4,2` | 3 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.011 |
| 0 | `1,2` | `5,2` | 4 | 25.004 | 231.008 | 223.008 | 231.008 | 23.009 | 228.997 | 221.008 | 221.004 |
| 0 | `1,2` | `6,2` | 5 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.019 |
| 0 | `1,2` | `7,2` | 6 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.011 |
| 0 | `1,2` | `10,2` | 9 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.003 |
| 0 | `1,2` | `11,2` | 10 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.011 |
| 0 | `1,2` | `12,2` | 11 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.003 |
| 0 | `1,2` | `13,2` | 12 | 25.004 | 231.008 | 223.008 | 231.008 | 23.009 | 228.997 | 221.008 | 221.012 |
| 0 | `1,2` | `14,2` | 13 | 25.004 | 231.008 | 223.008 | 231.008 | 23.009 | 228.997 | 221.008 | 221.004 |
| 1 | `14,2` | `13,2` | 1 | 24.998 | 230.996 | 222.996 | 230.996 | 22.998 | 228.996 | 220.996 | 220.996 |
| 1 | `14,2` | `12,2` | 2 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.027 |
| 1 | `14,2` | `11,2` | 3 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.003 |
| 1 | `14,2` | `10,2` | 4 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.003 |
| 1 | `14,2` | `7,2` | 7 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.003 |
| 1 | `14,2` | `6,2` | 8 | 25.004 | 231.008 | 223.008 | 231.008 | 23.009 | 228.997 | 221.008 | 221.012 |
| 1 | `14,2` | `5,2` | 9 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.011 |
| 1 | `14,2` | `4,2` | 10 | 25.006 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.011 |
| 1 | `14,2` | `3,2` | 11 | 25.004 | 231.008 | 223.008 | 231.008 | 23.009 | 228.997 | 221.008 | 221.004 |
| 1 | `14,2` | `2,2` | 12 | 25.004 | 231.008 | 223.008 | 231.008 | 23.009 | 228.997 | 221.008 | 221.012 |
| 1 | `14,2` | `1,2` | 13 | 25.004 | 231.007 | 223.007 | 231.007 | 23.008 | 228.996 | 221.007 | 221.011 |
