
# Blackhole Dual-NoC Aggregate Writes

Goal: test whether using NoC0 and NoC1 together doubles aggregate write
bandwidth.

The harness lives in `microbenching/noc/riscv_noc_dual_aggregate.py`. This is a
negative control: one BRISC issues both NoC0 and NoC1 command streams serially.
It is not the expected fast path and should not be used as the headline fabric
bandwidth number. TT-Metal's convention for dual-NoC data movement is
BRISC/RISCV_0 on NoC0 and NCRISC/RISCV_1 on NoC1.

## Observation

One BRISC driving both NoCs does not double aggregate bandwidth. With 60 pairs
and 512 KiB per NoC per sender, it reaches only about `963 B/cyc`. That is far
below the one-NoC 60-pair result of about `3.45 KB/cyc`, so the bottleneck is
the single issuing RISC command stream, not shared NoC fabric. Keep this run as
a sanity check for command-submission serialization.

## Run

- Bytes per sender per NoC: `524288`
- Pairing: disjoint adjacent same-row sender/receiver pairs

| noc | pairs | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | bad ack rows | bad sentinel rows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dual | 1 | 1.0 | 8636 | 121.419 | 8629 | 121.518 | 0 | 0 |
| dual | 2 | 2.0 | 21168 | 99.072 | 21148 | 99.166 | 0 | 0 |
| dual | 4 | 4.0 | 42840 | 97.906 | 42833 | 97.922 | 0 | 0 |
| dual | 8 | 8.0 | 65230 | 128.600 | 65217 | 128.626 | 0 | 0 |
| dual | 16 | 16.0 | 65245 | 257.142 | 65234 | 257.185 | 0 | 0 |
| dual | 32 | 32.0 | 65340 | 513.536 | 65333 | 513.591 | 0 | 0 |
| dual | 60 | 60.0 | 65370 | 962.438 | 65359 | 962.600 | 0 | 0 |
