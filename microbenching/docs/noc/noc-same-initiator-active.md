
## Run 2026-06-13T16:59:33-04:00 NoC same-initiator active commands

- Traffic: one BRISC issues read and/or write commands on one NoC, using write slot 0 and read slot 1.
- The mixed modes issue both commands back-to-back inside the loop and wait for read responses/write acks only after the loop.
- Purpose: distinguish multiple active NoC transactions from the earlier BRISC+NCRISC same-core timeout.

| noc | mode | source | read target | write target | bytes | iters | cycles | agg B/cyc | wr delta | rd delta | read sink | write seen |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | read | `1,2` | `2,2` | `1,3` | 16384 | 64 | 16882 | 62.112 | 0 | 64 | 0xa5000000 | 0x00000000 |
| 0 | write | `1,2` | `2,2` | `1,3` | 16384 | 64 | 16917 | 61.984 | 64 | 0 | 0x00000000 | 0xa5000000 |
| 0 | wr-read | `1,2` | `2,2` | `1,3` | 16384 | 64 | 17485 | 119.940 | 64 | 64 | 0xa5000000 | 0xa5000000 |
| 0 | read-wr | `1,2` | `2,2` | `1,3` | 16384 | 64 | 17220 | 121.786 | 64 | 64 | 0xa5000000 | 0xa5000000 |
| 1 | read | `1,2` | `2,2` | `1,3` | 16384 | 64 | 16904 | 62.031 | 0 | 64 | 0xa5000000 | 0x00000000 |
| 1 | write | `1,2` | `2,2` | `1,3` | 16384 | 64 | 16742 | 62.631 | 64 | 0 | 0x00000000 | 0xa5000000 |
| 1 | wr-read | `1,2` | `2,2` | `1,3` | 16384 | 64 | 17397 | 120.547 | 64 | 64 | 0xa5000000 | 0xa5000000 |
| 1 | read-wr | `1,2` | `2,2` | `1,3` | 16384 | 64 | 17149 | 122.290 | 64 | 64 | 0xa5000000 | 0xa5000000 |

## Run 2026-06-13T17:00:00-04:00 Same Remote Target Smoke

- Command: `riscv_noc_same_initiator_active.py --nocs 0,1 --modes wr-read,read-wr --read-target 2,2 --write-target 2,2 --bytes 4096 --iters 16 --no-report`
- Job: `bbc60434`
- Traffic: same BRISC, same NoC, same remote L1 target for both read and write.

| noc | mode | source | read target | write target | bytes | iters | cycles | agg B/cyc | wr delta | rd delta | read sink | write seen |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | wr-read | `1,2` | `2,2` | `2,2` | 4096 | 16 | 1566 | 83.699 | 16 | 16 | 0xa5000000 | 0xa5000000 |
| 0 | read-wr | `1,2` | `2,2` | `2,2` | 4096 | 16 | 1533 | 85.500 | 16 | 16 | 0xa5000000 | 0xa5000000 |
| 1 | wr-read | `1,2` | `2,2` | `2,2` | 4096 | 16 | 1568 | 83.592 | 16 | 16 | 0xa5000000 | 0xa5000000 |
| 1 | read-wr | `1,2` | `2,2` | `2,2` | 4096 | 16 | 1533 | 85.500 | 16 | 16 | 0xa5000000 | 0xa5000000 |

Scheduler implication: one BRISC can keep the write-owned and read-owned
command slots active on the same NoC. The earlier same-core hang is specific to
the BRISC+NCRISC concurrent probe shape, not a proof that the NIU is limited to
one active transaction total.
