## Reduction summary

Bench source: `microbenching/noc/riscv_noc_mcast_scheduler_calibration.py`

Validation:

- `python3 -m py_compile microbenching/noc/riscv_noc_mcast_scheduler_calibration.py`
- Hardware jobs: `091ae992` smoke, `9d75e00c` full sweep, `e7bf642b` corrected NoC1-local path-reserve sweep.
- All rows in the calibration tables reported `bad counter = 0` and `stale data = 0` where those checks apply.

Model-facing constants/verdicts:

- `mcast_path_reserve_cycles ~= 18 cycles` for a one-receiver local-direction multicast. NoC0 `(1,4)->(2,4)` gives `17-20 cycles`; corrected NoC1 `(2,4)->(1,4)` gives `16.5-20 cycles`. The first full sweep's NoC1 `(1,4)->(2,4)` rows show `~226-229 cycles` because that pair is the wrong NoC1 direction and should not be used as the fixed setup constant.
- Trunk charging is once per multicast tree, not once per receiver. Delivered bandwidth scales roughly as `source_bpc * receiver_count`: for NoC0, N=1/2/4 gives `44.5/85.4/160 B/cyc` delivered; for NoC1, N=1/2/4/8/11 gives `28.4/56.8/113.6/227.1/312 B/cyc`.
- There is a NoC0 fanout/source-window tax beyond about four row receivers: source bandwidth drops from `~40 B/cyc` at N=4 to `~32 B/cyc` at N=8 and `~28.9 B/cyc` at N=11. For 16 KiB packets this is about `20-25 cycles` per extra receiver beyond N=4 in this row layout. NoC1 is already at its lower row rate and stays nearly flat through N=11.
- `VC_LINKED` changes source/trunk bandwidth, not only ordering. At K=8, 16 KiB, depth 4 improves source bandwidth from `32.1 -> 49.1 B/cyc` on NoC0 and `28.5 -> 46.8 B/cyc` on NoC1, about `1.5-1.6x` versus depth 1.
- Without `CMD_PATH_RESERVE`, overlapping multicast trees behave like shared directed-link serialization; no extra non-reserve overlap constant is needed. With `CMD_PATH_RESERVE`, multi-tree cases slow far beyond the single-tree `+18 cyc` setup cost, so reserve-mode overlap needs a reservation/locked-path contention term if the scheduler models reserve-enabled traffic.

## Run 2026-06-24T18:09:32-04:00

- Command: `microbenching/noc/riscv_noc_mcast_scheduler_calibration.py --sections path,trunk,vc,overlap --nocs 0,1 --majors x,y --path-sizes 16,64,1024,16384 --path-iters 32 --trunk-counts 1,2,4,8,11 --trunk-iters 128 --vc-depths 1,2,4 --vc-count 8 --overlap-cases disjoint,overlap,same_rect --overlap-path-modes both,none --overlap-iters 16 --overlap-chunks 1 --report microbenching/docs/noc/noc-mcast-scheduler-calibration.md`

### Verdicts

- Path reserve: one-receiver reserve/no-reserve median delta at smallest size is `123.4 cycles`.
- Trunk charged once: source bandwidth stays within 10% of the N=1 rate through `N=4` in this sweep; delivered bandwidth scales with receiver count.
- VC_LINKED: best source bandwidth multiplier vs depth-1 is `1.58x` at depth `4`.
- Overlap: shared-tree cases serialize on shared directed links; no separate path-reserve-only contention term is indicated unless reserve and no-reserve rows diverge beyond link serialization.

### Path Reserve

| noc | major | bytes | unicast seen-issue | mcast nores seen-issue | mcast reserve seen-issue | reserve delta seen | reserve delta seen-sent | reserve mcast - unicast |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | x | 16 | 43.0 | 44.5 | 63.0 | 18.5 | 18.5 | 20.0 |
| 0 | y | 16 | 43.0 | 44.5 | 63.0 | 18.5 | 18.5 | 20.0 |
| 0 | x | 64 | 43.0 | 45.0 | 62.5 | 17.5 | 17.5 | 19.5 |
| 0 | y | 64 | 43.0 | 45.0 | 62.0 | 17.0 | 17.0 | 19.0 |
| 0 | x | 1024 | 60.0 | 60.0 | 78.0 | 18.0 | 10.0 | 18.0 |
| 0 | y | 1024 | 60.0 | 60.5 | 76.0 | 15.5 | 7.5 | 16.0 |
| 0 | x | 16384 | 307.5 | 306.0 | 325.0 | 19.0 | 3.5 | 17.5 |
| 0 | y | 16384 | 307.5 | 305.0 | 324.5 | 19.5 | 3.5 | 17.0 |
| 1 | x | 16 | 180.0 | 178.0 | 407.0 | 229.0 | 229.0 | 227.0 |
| 1 | y | 16 | 180.0 | 178.0 | 405.5 | 227.5 | 227.5 | 225.5 |
| 1 | x | 64 | 179.0 | 180.0 | 407.5 | 227.5 | 227.5 | 228.5 |
| 1 | y | 64 | 179.0 | 180.5 | 407.0 | 226.5 | 226.5 | 228.0 |
| 1 | x | 1024 | 194.0 | 194.0 | 422.0 | 228.0 | 4.0 | 228.0 |
| 1 | y | 1024 | 194.0 | 194.5 | 423.5 | 229.0 | 5.0 | 229.5 |
| 1 | x | 16384 | 443.0 | 442.0 | 668.0 | 226.0 | -2.0 | 225.0 |
| 1 | y | 16384 | 443.0 | 442.0 | 668.0 | 226.0 | -2.0 | 225.0 |

### Trunk Fanout

| noc | major | dests | depth | bytes | source B/cyc | delivered B/cyc | req/cyc | bad counter |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | x | 1 | 1 | 16384 | 44.543 | 44.519 | 0.00272 | 0 |
| 0 | y | 1 | 1 | 16384 | 44.528 | 44.500 | 0.00272 | 0 |
| 1 | x | 1 | 1 | 16384 | 28.456 | 28.394 | 0.00174 | 0 |
| 1 | y | 1 | 1 | 16384 | 28.456 | 28.394 | 0.00174 | 0 |
| 0 | x | 2 | 1 | 16384 | 42.742 | 85.436 | 0.00261 | 0 |
| 0 | y | 2 | 1 | 16384 | 42.749 | 85.450 | 0.00261 | 0 |
| 1 | x | 2 | 1 | 16384 | 28.456 | 56.788 | 0.00174 | 0 |
| 1 | y | 2 | 1 | 16384 | 28.456 | 56.788 | 0.00174 | 0 |
| 0 | x | 4 | 1 | 16384 | 40.021 | 159.948 | 0.00244 | 0 |
| 0 | y | 4 | 1 | 16384 | 40.132 | 160.397 | 0.00245 | 0 |
| 1 | x | 4 | 1 | 16384 | 28.456 | 113.578 | 0.00174 | 0 |
| 1 | y | 4 | 1 | 16384 | 28.456 | 113.584 | 0.00174 | 0 |
| 0 | x | 8 | 1 | 16384 | 32.141 | 256.697 | 0.00196 | 0 |
| 0 | y | 8 | 1 | 16384 | 32.212 | 257.252 | 0.00197 | 0 |
| 1 | x | 8 | 1 | 16384 | 28.456 | 227.152 | 0.00174 | 0 |
| 1 | y | 8 | 1 | 16384 | 28.456 | 227.134 | 0.00174 | 0 |
| 0 | x | 11 | 1 | 16384 | 28.930 | 317.597 | 0.00177 | 0 |
| 0 | y | 11 | 1 | 16384 | 28.899 | 317.239 | 0.00176 | 0 |
| 1 | x | 11 | 1 | 16384 | 28.419 | 311.941 | 0.00173 | 0 |
| 1 | y | 11 | 1 | 16384 | 28.429 | 312.042 | 0.00174 | 0 |

### VC Linked

| noc | major | dests | depth | bytes | source B/cyc | delivered B/cyc | req/cyc | bad counter |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | x | 8 | 1 | 16384 | 32.137 | 256.638 | 0.00196 | 0 |
| 0 | y | 8 | 1 | 16384 | 32.125 | 256.572 | 0.00196 | 0 |
| 1 | x | 8 | 1 | 16384 | 28.453 | 227.127 | 0.00174 | 0 |
| 1 | y | 8 | 1 | 16384 | 28.456 | 227.161 | 0.00174 | 0 |
| 0 | x | 8 | 2 | 16384 | 41.981 | 335.474 | 0.00256 | 0 |
| 0 | y | 8 | 2 | 16384 | 41.927 | 335.058 | 0.00256 | 0 |
| 1 | x | 8 | 2 | 16384 | 38.638 | 308.649 | 0.00236 | 0 |
| 1 | y | 8 | 2 | 16384 | 38.633 | 308.586 | 0.00236 | 0 |
| 0 | x | 8 | 4 | 16384 | 49.076 | 392.365 | 0.00300 | 0 |
| 0 | y | 8 | 4 | 16384 | 49.088 | 392.452 | 0.00300 | 0 |
| 1 | x | 8 | 4 | 16384 | 46.804 | 374.068 | 0.00286 | 0 |
| 1 | y | 8 | 4 | 16384 | 46.790 | 373.961 | 0.00286 | 0 |

### Overlap

| case | noc | major | path reserve | chunks | aggregate delivered B/cyc | A source B/cyc | B source B/cyc | A delivered B/cyc | B delivered B/cyc | bad counter | stale data |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| disjoint | 0 | x | both | 1 | 820.001 | 29.153 | 27.817 | 457.195 | 434.328 | 0 | 0 |
| disjoint | 0 | x | none | 1 | 1154.025 | 39.196 | 39.767 | 621.378 | 626.670 | 0 | 0 |
| disjoint | 0 | y | both | 1 | 820.723 | 29.208 | 27.864 | 457.793 | 435.049 | 0 | 0 |
| disjoint | 0 | y | none | 1 | 1137.438 | 39.243 | 39.196 | 622.116 | 617.809 | 0 | 0 |
| disjoint | 1 | x | both | 1 | 195.425 | 6.200 | 14.353 | 97.712 | 221.663 | 0 | 0 |
| disjoint | 1 | x | none | 1 | 680.728 | 23.797 | 22.819 | 359.964 | 357.266 | 0 | 0 |
| disjoint | 1 | y | both | 1 | 178.432 | 9.207 | 5.727 | 144.040 | 90.334 | 0 | 0 |
| disjoint | 1 | y | none | 1 | 756.276 | 25.500 | 25.563 | 381.266 | 398.964 | 0 | 0 |
| overlap | 0 | x | both | 1 | 291.697 | 29.231 | 9.474 | 150.950 | 148.829 | 0 | 0 |
| overlap | 0 | x | none | 1 | 760.458 | 25.600 | 25.580 | 394.609 | 401.638 | 0 | 0 |
| overlap | 0 | y | both | 1 | 311.833 | 27.418 | 10.151 | 161.799 | 159.237 | 0 | 0 |
| overlap | 0 | y | none | 1 | 907.563 | 31.060 | 30.942 | 474.469 | 483.884 | 0 | 0 |
| overlap | 1 | x | both | 1 | 228.398 | 14.681 | 7.326 | 116.515 | 115.980 | 0 | 0 |
| overlap | 1 | x | none | 1 | 779.538 | 27.652 | 26.152 | 402.756 | 412.136 | 0 | 0 |
| overlap | 1 | y | both | 1 | 242.775 | 7.730 | 18.629 | 121.388 | 127.630 | 0 | 0 |
| overlap | 1 | y | none | 1 | 898.619 | 32.098 | 30.482 | 466.656 | 478.966 | 0 | 0 |
| same_rect | 0 | x | both | 1 | 267.844 | 8.422 | 17.955 | 133.922 | 138.696 | 0 | 0 |
| same_rect | 0 | x | none | 1 | 880.509 | 29.843 | 29.816 | 456.796 | 469.057 | 0 | 0 |
| same_rect | 0 | y | both | 1 | 320.457 | 29.101 | 10.386 | 164.728 | 163.827 | 0 | 0 |
| same_rect | 0 | y | none | 1 | 874.907 | 29.681 | 29.521 | 454.618 | 464.537 | 0 | 0 |
| same_rect | 1 | x | both | 1 | 215.142 | 14.780 | 6.912 | 109.994 | 109.161 | 0 | 0 |
| same_rect | 1 | x | none | 1 | 765.244 | 26.154 | 25.721 | 395.130 | 403.725 | 0 | 0 |
| same_rect | 1 | y | both | 1 | 209.119 | 14.774 | 6.712 | 106.848 | 106.069 | 0 | 0 |
| same_rect | 1 | y | none | 1 | 777.659 | 27.652 | 26.214 | 401.792 | 411.085 | 0 | 0 |

## Run 2026-06-24T18:09:44-04:00

- Command: `microbenching/noc/riscv_noc_mcast_scheduler_calibration.py --sections path --nocs 1 --majors x,y --source 2,4 --target 1,4 --path-sizes 16,64,1024,16384 --path-iters 32 --report microbenching/docs/noc/noc-mcast-scheduler-calibration.md`

### Verdicts

- Path reserve: one-receiver reserve/no-reserve median delta at smallest size is `18.2 cycles`.

### Path Reserve

| noc | major | bytes | unicast seen-issue | mcast nores seen-issue | mcast reserve seen-issue | reserve delta seen | reserve delta seen-sent | reserve mcast - unicast |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | x | 16 | 44.0 | 42.0 | 61.0 | 19.0 | 19.0 | 17.0 |
| 1 | y | 16 | 44.0 | 43.5 | 61.0 | 17.5 | 17.5 | 17.0 |
| 1 | x | 64 | 44.0 | 44.0 | 63.0 | 19.0 | 19.0 | 19.0 |
| 1 | y | 64 | 44.0 | 43.0 | 60.0 | 17.0 | 17.0 | 16.0 |
| 1 | x | 1024 | 60.5 | 60.5 | 77.0 | 16.5 | 8.5 | 16.5 |
| 1 | y | 1024 | 60.5 | 61.0 | 77.5 | 16.5 | 8.5 | 17.0 |
| 1 | x | 16384 | 307.5 | 305.0 | 325.0 | 20.0 | 4.0 | 17.5 |
| 1 | y | 16384 | 307.5 | 305.0 | 325.0 | 20.0 | 4.0 | 17.5 |
