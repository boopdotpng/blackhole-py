# Blackhole Dual-DM NoC Aggregate Writes

Goal: test the TT-Metal-style split where BRISC/RISCV_0 drives NoC0 and
NCRISC/RISCV_1 drives NoC1 from the same sender tile.

The harness lives in `examples/riscv_noc_dual_dm_aggregate.py`. Each sender tile
runs BRISC and NCRISC. BRISC writes one target L1 region over NoC0; NCRISC
writes a second target L1 region over NoC1. The receiver BRISC polls both final
sentinel words. Sender-side rows use the max of BRISC/NCRISC write barriers;
receiver-side rows use the time at which both sentinels are visible.

## Observation

This did not double the one-NoC aggregate result. One pair reaches about
`121 B/cyc`, close to doubling a single source stream. At 60 pairs it reaches
only about `961 B/cyc`, much lower than the one-NoC 60-pair result of about
`3.45 KB/cyc`. The limiting factor is therefore not simply independent NoC0 and
NoC1 fabric bandwidth. This pattern likely adds pressure on shared sender-tile
L1/source reads, shared receiver-tile L1 writes, or BRISC/NCRISC data-movement
coordination.

There is also an important routing caveat: this run uses NoC0-style adjacent
same-row pairs. That is the correct short direction for NoC0, but the direction
is flipped for NoC1, so the NoC1 stream may take the wrapped path at scale. Treat
this as a target-L1 and dual-DM pressure experiment, not as a clean dual-NoC peak
bandwidth test.

## Run

- Bytes per sender per NoC: `524288`
- Sender tile: BRISC on NoC0 plus NCRISC on NoC1
- Pairing: disjoint adjacent same-row sender/receiver pairs

| noc | pairs | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | bad ack rows | bad sentinel rows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dual-dm | 1 | 1.0 | 8695 | 120.595 | 8647 | 121.265 | 0 | 0 |
| dual-dm | 2 | 2.0 | 21289 | 98.509 | 21265 | 98.620 | 0 | 0 |
| dual-dm | 4 | 4.0 | 42910 | 97.747 | 42906 | 97.756 | 0 | 0 |
| dual-dm | 8 | 8.0 | 65338 | 128.388 | 65328 | 128.408 | 0 | 0 |
| dual-dm | 16 | 16.0 | 65433 | 256.403 | 65427 | 256.426 | 0 | 0 |
| dual-dm | 32 | 32.0 | 65449 | 512.681 | 65435 | 512.790 | 0 | 0 |
| dual-dm | 60 | 60.0 | 65477 | 960.865 | 65467 | 961.012 | 0 | 0 |
