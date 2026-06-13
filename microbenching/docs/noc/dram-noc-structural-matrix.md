# DRAM NoC Structural Matrix

This report covers simultaneous NoC0 and NoC1 DRAM traffic with named bank-set
and route-placement patterns. The benchmark runs each NoC group alone, then
runs both groups through a device-side start gate.

Implemented bank patterns:

- `same-dram-bank`: both NoCs address the same logical DRAM bank.
- `different-banks-same-dram-column`: both NoCs use different banks in the same
  low-half DRAM column.
- `banks-0-3`: low-half logical bank set.
- `banks-4-7`: high-half logical bank set, trimmed for harvested boards.
- `alternating-halves`: alternates low-half and high-half banks.
- `same-route-links`: nearby source-core placement into one bank.
- `disjoint-route-links`: separated source-core placement into low/high banks.

Full matrix command:

```bash
python3 microbenching/noc/riscv_dram_noc_structural_matrix.py \
  --cases same-dram-bank,different-banks-same-dram-column,banks-0-3,banks-4-7,alternating-halves,same-route-links,disjoint-route-links \
  --op-pairs read/read,write/write,read/write \
  --streams-per-noc 2 --bytes-per-stream 524288 --packet-bytes 2048
```

Scheduler implication from the representative hardware run: DRAM bank/controller
pressure is shared across NoC0 and NoC1. Same-bank read/read dropped from about
40 B/cyc per stream alone to about 22 B/cyc mixed, while different banks in the
same column and disjoint low/high bank placements overlapped at about 80 B/cyc
aggregate with no bad counters. Model DRAM structural resources as shared by
bank/controller across NoCs; keep route-link resources per NoC/direction.

## Run 2026-06-13T17:36:41-04:00 DRAM structural matrix

- Streams per NoC: `1`
- Bytes per stream: `131072`
- Packet size: `2048` bytes
- Endpoint mode: `preferred`
- Posting mode: `standard`
- Start gate lead: `200000000` cycles
- Traffic: NoC0 group alone, NoC1 group alone, then both groups simultaneously
- Read/write pairs use disjoint DRAM page ranges within the selected bank pattern.

| case | op pair | NoC0 streams | NoC1 streams | NoC0 alone B/cyc | NoC1 alone B/cyc | mixed NoC0 B/cyc | mixed NoC1 B/cyc | mixed aggregate B/cyc | bad counters |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| same-dram-bank | read/read | NoC0/read `1,4`->b0.e2 | NoC1/read `2,4`->b0.e1 | 40.181 | 40.293 | 22.141 | 22.383 | 44.281 | 0 |
| same-dram-bank | read/write | NoC0/read `1,4`->b0.e2 | NoC1/write `2,4`->b0.e1 | 38.460 | 44.371 | 20.739 | 21.996 | 41.478 | 0 |
| different-banks-same-dram-column | read/read | NoC0/read `1,4`->b0.e2 | NoC1/read `2,4`->b1.e1 | 40.157 | 40.022 | 40.157 | 40.095 | 80.093 | 0 |
| different-banks-same-dram-column | read/write | NoC0/read `1,4`->b0.e2 | NoC1/write `2,4`->b1.e1 | 40.145 | 44.401 | 40.157 | 44.416 | 80.020 | 0 |
| disjoint-route-links | read/read | NoC0/read `1,4`->b0.e2 | NoC1/read `13,7`->b4.e1 | 40.157 | 38.348 | 40.157 | 40.157 | 80.215 | 0 |
| disjoint-route-links | read/write | NoC0/read `1,4`->b0.e2 | NoC1/write `13,7`->b4.e1 | 40.157 | 44.371 | 40.157 | 44.326 | 80.314 | 0 |
