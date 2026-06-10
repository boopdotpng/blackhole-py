
# Blackhole NoC Aggregate Writes

Goal: measure aggregate peer L1 write bandwidth with multiple independent
source cores active at the same time.

The harness lives in `microbenching/noc/riscv_noc_aggregate.py`. It forms disjoint
same-row adjacent sender/receiver pairs. Each sender writes a payload to its
receiver in 16 KiB NoC chunks; each receiver polls the final sentinel word. The
table reports both source-side `noc_write_barrier()` completion and
receiver-observed sentinel completion.

`sender agg B/cyc` uses `min(sender start)` to `max(sender write barrier)`.
`receiver agg B/cyc` uses `min(sender start)` to `max(receiver observed
sentinel)`. The wall-clock skew probes show cross-core clock deltas are stable,
but fixed core-to-core offsets can still add small noise to the aggregate
window.

## Headline Result

The trusted peak observed so far is the 60-pair single-NoC run. It uses the
correct adjacent direction for each NoC and one receiver tile per sender tile.
At `1350 MHz`, the receiver-observed aggregate rates convert to:

- NoC0: `3452.670 B/cyc` = about `4.66 TB/s`
- NoC1: `3464.267 B/cyc` = about `4.68 TB/s`

This is the current headline number for aggregate peer-L1 write bandwidth across
all program cores on one NoC. The source-side write barrier agrees with receiver
sentinel visibility in the separate observed-completion probe, so these numbers
are not caused by early acknowledgement.

## Run

- NoC: `0`
- Bytes per sender: `1048576`
- Pairing: disjoint adjacent same-row sender/receiver pairs

| noc | pairs | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | bad ack rows | bad sentinel rows |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 1.0 | 17138 | 61.184 | 16998 | 61.688 | 0 | 0 |
| 0 | 2 | 2.0 | 17195 | 121.963 | 17042 | 123.058 | 0 | 0 |
| 0 | 4 | 4.0 | 17316 | 242.221 | 17181 | 244.125 | 0 | 0 |
| 0 | 8 | 8.0 | 21151 | 396.606 | 21005 | 399.362 | 0 | 0 |
| 0 | 16 | 16.0 | 18101 | 926.867 | 17975 | 933.364 | 0 | 0 |
| 0 | 32 | 32.0 | 18807 | 1784.146 | 18664 | 1797.816 | 0 | 0 |
| 0 | 60 | 60.0 | 18344 | 3429.708 | 18222 | 3452.670 | 0 | 0 |

## Run

- NoC: `1`
- Bytes per sender: `1048576`
- Pairing: disjoint adjacent same-row sender/receiver pairs

| noc | pairs | total MiB | sender window cyc | sender agg B/cyc | receiver window cyc | receiver agg B/cyc | bad ack rows | bad sentinel rows |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1.0 | 17130 | 61.213 | 16994 | 61.703 | 0 | 0 |
| 1 | 2 | 2.0 | 17161 | 122.205 | 17022 | 123.202 | 0 | 0 |
| 1 | 4 | 4.0 | 17872 | 234.686 | 17727 | 236.605 | 0 | 0 |
| 1 | 8 | 8.0 | 18656 | 449.647 | 18526 | 452.802 | 0 | 0 |
| 1 | 16 | 16.0 | 18639 | 900.114 | 18513 | 906.240 | 0 | 0 |
| 1 | 32 | 32.0 | 18795 | 1785.285 | 18655 | 1798.683 | 0 | 0 |
| 1 | 60 | 60.0 | 18289 | 3440.022 | 18161 | 3464.267 | 0 | 0 |
