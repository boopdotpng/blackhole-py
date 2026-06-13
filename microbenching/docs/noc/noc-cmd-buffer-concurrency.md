
## Run 2026-06-13T17:37:41-04:00 NoC command-buffer concurrency truth table

- Command-buffer matrix: pairs `write+read`, NoC modes `same0,diff01`, slot modes `diff`
- Iters: `4`, bytes per copy command: `1024`, command-ready timeout loops: `1000000`, response timeout loops: `10000000`
- Traffic uses one BRISC and one NCRISC on the same Tensix core, with disjoint remote L1 targets by default.
- Rates are bytes/cycle for read/write copies and cycles/op for atomic/inline operations.
- Same-slot rows are intentionally opt-in because both RISCs program the same NIU command buffer concurrently.

| pair | nocs | slots | source | brisc target | ncrisc target | BRISC result | NCRISC result | verdict |
|---|---|---|---|---|---|---|---|---|
| write+read | `0/0` | `0/1` (diff) | `7,4` | `14,4` | `1,4` | pass 11.441 B/cyc ctr=4 | timeout-flush 0.000 B/cyc ctr=0 | timeout/error |
| write+read | `0/1` | `0/1` (diff) | `7,4` | `14,4` | `1,4` | pass 11.011 B/cyc ctr=4 | timeout-flush 0.000 B/cyc ctr=0 | timeout/error |

## Run 2026-06-13T17:38:16-04:00 NoC command-buffer concurrency truth table

- Command-buffer matrix: pairs `write+atomic,write+inline`, NoC modes `same0,diff01`, slot modes `diff`
- Iters: `4`, bytes per copy command: `1024`, command-ready timeout loops: `1000000`, response timeout loops: `10000000`
- Traffic uses one BRISC and one NCRISC on the same Tensix core, with disjoint remote L1 targets by default.
- Rates are bytes/cycle for read/write copies and cycles/op for atomic/inline operations.
- Same-slot rows are intentionally opt-in because both RISCs program the same NIU command buffer concurrently.

| pair | nocs | slots | source | brisc target | ncrisc target | BRISC result | NCRISC result | verdict |
|---|---|---|---|---|---|---|---|---|
| write+atomic | `0/0` | `0/3` (diff) | `7,4` | `14,4` | `1,4` | pass 11.736 B/cyc ctr=4 | timeout-flush 25000053.500 cyc/op ctr=0 | timeout/error |
| write+atomic | `0/1` | `0/3` (diff) | `7,4` | `14,4` | `1,4` | pass 11.011 B/cyc ctr=4 | timeout-flush 25000048.000 cyc/op ctr=0 | timeout/error |
| write+inline | `0/0` | `0/2` (diff) | `7,4` | `14,4` | `1,4` | pass 11.378 B/cyc ctr=4 | pass 94.000 cyc/op ctr=4 | pass |
| write+inline | `0/1` | `0/2` (diff) | `7,4` | `14,4` | `1,4` | pass 11.409 B/cyc ctr=4 | timeout-flush 25000045.500 cyc/op ctr=0 | timeout/error |

## Run 2026-06-13T17:38:31-04:00 NoC command-buffer concurrency truth table

- Command-buffer matrix: pairs `write+read,write+atomic,write+inline`, NoC modes `same0,same1,diff01,diff10`, slot modes `diff`
- Iters: `4`, bytes per copy command: `1024`, command-ready timeout loops: `1000000`, response timeout loops: `10000000`
- Traffic uses one BRISC and one NCRISC on the same Tensix core, with disjoint remote L1 targets by default.
- Rates are bytes/cycle for read/write copies and cycles/op for atomic/inline operations.
- Same-slot rows are intentionally opt-in because both RISCs program the same NIU command buffer concurrently.

| pair | nocs | slots | source | brisc target | ncrisc target | BRISC result | NCRISC result | verdict |
|---|---|---|---|---|---|---|---|---|
| write+read | `0/0` | `0/1` (diff) | `7,4` | `14,4` | `1,4` | pass 11.670 B/cyc ctr=4 | timeout-flush 0.000 B/cyc ctr=0 | timeout/error |
| write+read | `1/1` | `0/1` (diff) | `7,4` | `14,4` | `1,4` | pass 10.695 B/cyc ctr=4 | timeout-flush 0.000 B/cyc ctr=0 | timeout/error |
| write+read | `0/1` | `0/1` (diff) | `7,4` | `14,4` | `1,4` | pass 10.667 B/cyc ctr=4 | timeout-flush 0.000 B/cyc ctr=0 | timeout/error |
| write+read | `1/0` | `0/1` (diff) | `7,4` | `14,4` | `1,4` | pass 12.012 B/cyc ctr=4 | timeout-flush 0.000 B/cyc ctr=0 | timeout/error |
| write+atomic | `0/0` | `0/3` (diff) | `7,4` | `14,4` | `1,4` | pass 11.804 B/cyc ctr=4 | timeout-flush 25000051.250 cyc/op ctr=0 | timeout/error |
| write+atomic | `1/1` | `0/3` (diff) | `7,4` | `14,4` | `1,4` | pass 11.378 B/cyc ctr=4 | timeout-flush 25000052.250 cyc/op ctr=0 | timeout/error |
| write+atomic | `0/1` | `0/3` (diff) | `7,4` | `14,4` | `1,4` | pass 11.378 B/cyc ctr=4 | timeout-flush 25000047.250 cyc/op ctr=0 | timeout/error |
| write+atomic | `1/0` | `0/3` (diff) | `7,4` | `14,4` | `1,4` | pass 10.981 B/cyc ctr=4 | timeout-flush 25000047.000 cyc/op ctr=0 | timeout/error |
| write+inline | `0/0` | `0/2` (diff) | `7,4` | `14,4` | `1,4` | pass 11.409 B/cyc ctr=4 | pass 93.250 cyc/op ctr=4 | pass |
| write+inline | `1/1` | `0/2` (diff) | `7,4` | `14,4` | `1,4` | pass 11.703 B/cyc ctr=4 | pass 93.250 cyc/op ctr=4 | pass |
| write+inline | `0/1` | `0/2` (diff) | `7,4` | `14,4` | `1,4` | pass 11.378 B/cyc ctr=4 | timeout-flush 25000046.250 cyc/op ctr=0 | timeout/error |
| write+inline | `1/0` | `0/2` (diff) | `7,4` | `14,4` | `1,4` | pass 11.942 B/cyc ctr=4 | timeout-flush 25000044.250 cyc/op ctr=0 | timeout/error |

## Run 2026-06-13T17:38:38-04:00 NoC command-buffer concurrency truth table

- Command-buffer matrix: pairs `write+read,write+atomic,write+inline`, NoC modes `diff01,diff10`, slot modes `same`
- Iters: `4`, bytes per copy command: `1024`, command-ready timeout loops: `1000000`, response timeout loops: `10000000`
- Traffic uses one BRISC and one NCRISC on the same Tensix core, with disjoint remote L1 targets by default.
- Rates are bytes/cycle for read/write copies and cycles/op for atomic/inline operations.
- Same-slot rows are intentionally opt-in because both RISCs program the same NIU command buffer concurrently.

| pair | nocs | slots | source | brisc target | ncrisc target | BRISC result | NCRISC result | verdict |
|---|---|---|---|---|---|---|---|---|
| write+read | `0/1` | `0/0` (same) | `7,4` | `14,4` | `1,4` | pass 11.409 B/cyc ctr=4 | timeout-flush 0.000 B/cyc ctr=0 | timeout/error |
| write+read | `1/0` | `0/0` (same) | `7,4` | `14,4` | `1,4` | pass 10.557 B/cyc ctr=4 | timeout-flush 0.000 B/cyc ctr=0 | timeout/error |
| write+atomic | `0/1` | `0/0` (same) | `7,4` | `14,4` | `1,4` | pass 10.584 B/cyc ctr=4 | timeout-flush 25000051.000 cyc/op ctr=0 | timeout/error |
| write+atomic | `1/0` | `0/0` (same) | `7,4` | `14,4` | `1,4` | pass 11.070 B/cyc ctr=4 | timeout-flush 25000047.250 cyc/op ctr=0 | timeout/error |
| write+inline | `0/1` | `0/0` (same) | `7,4` | `14,4` | `1,4` | pass 12.012 B/cyc ctr=4 | timeout-flush 25000047.750 cyc/op ctr=0 | timeout/error |
| write+inline | `1/0` | `0/0` (same) | `7,4` | `14,4` | `1,4` | pass 11.378 B/cyc ctr=4 | timeout-flush 25000044.500 cyc/op ctr=0 | timeout/error |

## Notes 2026-06-13

- Queue jobs: `2a01b621` smoke `write+read` on `same0,diff01`; `0a1b21d3` smoke `write+atomic,write+inline` on `same0,diff01`; `a216dc20` full different-slot matrix; `e2c17208` same slot-index on different NoC instances.
- The bench issues one BRISC command stream and one NCRISC command stream from the same Tensix core, with disjoint remote L1 endpoints: source `7,4`, BRISC target `14,4`, NCRISC target `1,4`.
- Different-slot truth table: BRISC nonposted writes completed in every case. NCRISC read and atomic commands never advanced the relevant response counter (`ctr=0`) before the bounded flush timeout. NCRISC inline writes completed only when BRISC and NCRISC used the same NoC instance (`0/0` or `1/1`), and timed out on split NoC assignment (`0/1` or `1/0`).
- Same slot-index coverage was run only for different NoC instances (`diff01,diff10`) because BRISC and NCRISC then program slot `0` on separate NIU instances. Same-NoC same-slot rows are implemented and dry-run checked, but were not run on shared hardware because both RISCs concurrently program the same command-buffer MMIO window.
- To run the omitted hazardous rows explicitly: `PYTHONPATH=. python3 microbenching/noc/riscv_noc_cmd_buf_concurrency.py --pairs write+read,write+atomic,write+inline --noc-modes same0,same1 --slot-modes same --include-same-slot --iters 4 --bytes 1024`
- Scheduler implication: treat BRISC+NCRISC same-core NoC command concurrency as operation- and NoC-instance-dependent. A safe scheduler model should not assume NCRISC can independently issue read/atomic command-buffer traffic concurrently with BRISC writes from the same core without additional firmware ownership/proxying. Inline/reg-write is the only passing NCRISC peer operation observed here, and only when sharing the same NoC instance in this harness.
