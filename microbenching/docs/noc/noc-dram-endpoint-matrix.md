## Run 2026-06-13T16:56:00-04:00 DRAM endpoint matrix

- Command: loop over `riscv_dram_noc_bench.py --mode single-bank --bank B --endpoint E --counts 1 --ops read,write --nocs 0,1 --bytes-per-core 1048576 --packet-bytes 16384 --no-report`
- Job: `3e59ab0d`
- Traffic: one worker core, one DRAM bank, one explicit endpoint, 1 MiB/core, 16 KiB NoC commands.
- Purpose: isolate single-source per-bank/per-endpoint asymmetry without aggregate DRAM fabric saturation.

Summary:

| op | NoC | min B/cyc | mean B/cyc | max B/cyc | worst bank/ep | best bank/ep |
|---|---:|---:|---:|---:|---|---|
| read | 0 | 45.781 | 46.375 | 46.612 | 5/2 | 1/0 |
| read | 1 | 46.085 | 46.363 | 46.579 | 0/0 | 1/0 |
| write | 0 | 47.068 | 47.110 | 47.306 | 6/2 | 1/0 |
| write | 1 | 47.061 | 47.093 | 47.299 | 3/1 | 1/0 |

Condensed endpoint table, B/cyc:

| bank | endpoint | read N0 | read N1 | write N0 | write N1 |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 46.360 | 46.085 | 47.085 | 47.078 |
| 0 | 1 | 46.397 | 46.364 | 47.102 | 47.080 |
| 0 | 2 | 46.397 | 46.381 | 47.102 | 47.078 |
| 1 | 0 | 46.612 | 46.579 | 47.306 | 47.299 |
| 1 | 1 | 46.397 | 46.381 | 47.102 | 47.080 |
| 1 | 2 | 46.397 | 46.346 | 47.102 | 47.080 |
| 2 | 0 | 46.381 | 46.346 | 47.085 | 47.064 |
| 2 | 1 | 46.397 | 46.381 | 47.102 | 47.080 |
| 2 | 2 | 46.377 | 46.381 | 47.102 | 47.080 |
| 3 | 0 | 46.381 | 46.364 | 47.083 | 47.064 |
| 3 | 1 | 46.381 | 46.364 | 47.085 | 47.061 |
| 3 | 2 | 46.381 | 46.348 | 47.085 | 47.078 |
| 4 | 0 | 46.612 | 46.576 | 47.306 | 47.282 |
| 4 | 1 | 46.381 | 46.364 | 47.085 | 47.064 |
| 4 | 2 | 46.381 | 46.362 | 47.085 | 47.080 |
| 5 | 0 | 46.381 | 46.364 | 47.085 | 47.064 |
| 5 | 1 | 46.360 | 46.364 | 47.085 | 47.064 |
| 5 | 2 | 45.781 | 46.364 | 47.085 | 47.078 |
| 6 | 0 | 46.381 | 46.201 | 47.085 | 47.064 |
| 6 | 1 | 46.364 | 46.364 | 47.085 | 47.064 |
| 6 | 2 | 46.381 | 46.346 | 47.068 | 47.080 |

Scheduler implication: single-source endpoint variation is small. For current
long-stream scheduling, a single endpoint constant is fine; the large aggregate
read/write differences come from fabric/placement saturation rather than
per-endpoint ceiling differences.
