
## Run 2026-06-24T17:52:47-04:00

- Start gate lead: `100000000` cycles
- Command: `microbenching/noc/riscv_noc_arbitration_bench.py --layouts rank-line --counts 2,3,4,5,6,7,8,9,10,11 --packet-bytes 16384 --packets 256 --nocs 0,1 --report microbenching/docs/noc/noc-arbitration-priority.md`
- Rank-priority recipe: run through `tt-device-queue` with `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts rank-line --counts 2,3,4,5,6,7,8,9,10,11 --packet-bytes 16384 --packets 256 --nocs 0,1`; add K=12 on devices with at least 13 live workers in one row
- Asymmetry recipe: `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts two-sided-asym --counts 4 --asym-left 3 --asym-right 1 --packet-bytes 16384 --packets 256 --nocs 0,1`
- Diagonal recipe: `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts diagonal-xleg,diagonal-yleg --counts 4 --packet-bytes 16384 --packets 256 --nocs 0,1`
- Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender
- Placement: target-ingress layouts include one-sided row, near-to-far rank-line, two-sided row/wrap, asymmetric two-sided, holey row, diagonal, diagonal X-leg/Y-leg, multi-row, and start-skew variants
- Ladder columns sort senders near-to-far by modeled routed path and compare against aggregate/min(rank+2,K), which gives the farthest two senders the same tail share
- Receiver visibility cycles are target-side first-observed sentinel timestamps relative to the receiver's gated start

| layout | noc | K | packet B | packets | target | sender order (+skew cyc) | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | near-rank B/cyc | ladder B/cyc | max ladder err | spread | interpretation | receiver visibility cycles | bad counters | target missing | target polls |
|---|---:|---:|---:|---:|---|---|---:|---:|---|---|---|---:|---:|---|---|---:|---:|---:|
| rank-line | 0 | 2 | 16384 | 256 | `14,4` | `13,4` `12,4` | 62.895 | 0.00384 | 31.506 31.449 | 31.506 31.449 | 31.447 31.447 | 0.002 | 0.002 | roughly equal | 393 652 | 0 | 0 | 16 |
| rank-line | 0 | 3 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` | 63.040 | 0.00385 | 31.588 21.015 21.042 | 31.588 21.015 21.042 | 31.520 21.013 21.013 | 0.002 | 0.431 | near target favored | 384 1180 671 | 0 | 0 | 26 |
| rank-line | 0 | 4 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` `10,4` | 63.128 | 0.00385 | 31.605 21.079 15.797 15.782 | 31.605 21.079 15.797 15.782 | 31.564 21.043 15.782 15.782 | 0.002 | 0.751 | near target favored | 413 647 1170 2237 | 0 | 0 | 48 |
| rank-line | 0 | 5 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` `10,4` `7,4` | 63.170 | 0.00386 | 31.636 21.088 15.812 12.644 12.634 | 31.636 21.088 15.812 12.644 12.634 | 31.585 21.057 15.792 12.634 12.634 | 0.002 | 1.013 | near target favored | 408 694 1201 2216 4282 | 0 | 0 | 88 |
| rank-line | 0 | 6 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` `10,4` `7,4` `6,4` | 63.227 | 0.00386 | 31.618 21.086 15.812 12.660 10.544 10.538 | 31.618 21.086 15.812 12.660 10.544 10.538 | 31.614 21.076 15.807 12.645 10.538 10.538 | 0.001 | 1.237 | near target favored | 479 721 1186 2268 4324 8509 | 0 | 0 | 168 |
| rank-line | 0 | 7 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` `10,4` `7,4` `6,4` `5,4` | 63.169 | 0.00386 | 31.641 21.078 15.797 12.643 10.539 9.029 9.024 | 31.641 21.078 15.797 12.643 10.539 9.029 9.024 | 31.585 21.056 15.792 12.634 10.528 9.024 9.024 | 0.002 | 1.443 | near target favored | 417 695 1249 2253 4319 8472 16728 | 0 | 0 | 315 |
| rank-line | 0 | 8 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` `10,4` `7,4` `6,4` `5,4` `4,4` | 63.224 | 0.00386 | 31.639 21.104 15.821 12.656 10.547 9.041 7.903 7.907 | 31.639 21.104 15.821 12.656 10.547 9.041 7.903 7.907 | 31.612 21.075 15.806 12.645 10.537 9.032 7.903 7.903 | 0.001 | 1.628 | near target favored | 467 781 1184 2283 4312 8496 33309 16740 | 0 | 0 | 597 |
| rank-line | 0 | 9 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` `10,4` `7,4` `6,4` `5,4` `4,4` `3,4` | 63.060 | 0.00385 | 31.637 21.068 15.790 12.626 10.519 9.015 7.887 7.007 7.010 | 31.637 21.068 15.790 12.626 10.519 9.015 7.887 7.007 7.010 | 31.530 21.020 15.765 12.612 10.510 9.009 7.882 7.007 7.007 | 0.003 | 1.809 | near target favored | 520 716 1174 2328 4318 8472 16736 66473 33370 | 0 | 0 | 1130 |
| rank-line | 0 | 10 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` `10,4` `7,4` `6,4` `5,4` `4,4` `3,4` `2,4` | 63.222 | 0.00386 | 31.632 21.081 15.803 12.647 10.541 9.032 7.903 7.024 6.322 6.325 | 31.632 21.081 15.803 12.647 10.541 9.032 7.903 7.024 6.322 6.325 | 31.611 21.074 15.805 12.644 10.537 9.032 7.903 7.025 6.322 6.322 | 0.001 | 1.973 | near target favored | 383 769 1283 2318 4383 8451 16789 66453 99544 33396 | 0 | 0 | 1502 |
| rank-line | 0 | 11 | 16384 | 256 | `14,4` | `13,4` `12,4` `11,4` `10,4` `7,4` `6,4` `5,4` `4,4` `3,4` `2,4` `1,4` | 63.220 | 0.00386 | 31.553 21.041 15.781 12.631 10.530 9.028 7.902 7.023 6.321 5.747 5.749 | 31.553 21.041 15.781 12.631 10.530 9.028 7.902 7.023 6.321 5.747 5.749 | 31.610 21.073 15.805 12.644 10.537 9.031 7.903 7.024 6.322 5.747 5.747 | 0.002 | 2.129 | near target favored | 419 651 1216 2217 4285 8474 16855 66612 99803 149728 33440 | 0 | 0 | 2090 |
| rank-line | 1 | 2 | 16384 | 256 | `1,4` | `2,4` `3,4` | 62.902 | 0.00384 | 31.510 31.453 | 31.510 31.453 | 31.451 31.451 | 0.002 | 0.002 | roughly equal | 395 632 | 0 | 0 | 15 |
| rank-line | 1 | 3 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` | 63.193 | 0.00386 | 31.693 21.091 21.064 | 31.693 21.091 21.064 | 31.597 21.064 21.064 | 0.003 | 0.432 | near target favored | 385 654 1147 | 0 | 0 | 25 |
| rank-line | 1 | 4 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` | 62.975 | 0.00384 | 31.519 21.013 15.759 15.744 | 31.519 21.013 15.759 15.744 | 31.488 20.992 15.744 15.744 | 0.001 | 0.751 | near target favored | 416 648 1177 2211 | 0 | 0 | 47 |
| rank-line | 1 | 5 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` | 63.201 | 0.00386 | 31.641 21.104 15.826 12.650 12.640 | 31.641 21.104 15.826 12.650 12.640 | 31.600 21.067 15.800 12.640 12.640 | 0.002 | 1.012 | near target favored | 407 694 1202 2215 4279 | 0 | 0 | 88 |
| rank-line | 1 | 6 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` | 63.094 | 0.00385 | 31.622 21.071 15.792 12.627 10.522 10.516 | 31.622 21.071 15.792 12.627 10.522 10.516 | 31.547 21.031 15.774 12.619 10.516 10.516 | 0.002 | 1.240 | near target favored | 362 702 1170 2252 4295 8438 | 0 | 0 | 167 |
| rank-line | 1 | 7 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` | 63.166 | 0.00386 | 31.618 21.081 15.807 12.651 10.537 9.029 9.024 | 31.618 21.081 15.807 12.651 10.537 9.029 9.024 | 31.583 21.055 15.791 12.633 10.528 9.024 9.024 | 0.001 | 1.441 | near target favored | 411 690 1246 2251 4320 8472 16728 | 0 | 0 | 315 |
| rank-line | 1 | 8 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` | 63.187 | 0.00386 | 31.605 21.075 15.800 12.647 10.540 9.030 7.902 7.899 | 31.605 21.075 15.800 12.647 10.540 9.030 7.902 7.899 | 31.594 21.062 15.797 12.637 10.531 9.027 7.898 7.898 | 0.001 | 1.628 | near target favored | 466 644 1175 2270 4299 8478 16761 33351 | 0 | 0 | 598 |
| rank-line | 1 | 9 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` | 63.195 | 0.00386 | 31.624 21.081 15.798 12.632 10.529 9.032 7.902 7.025 7.022 | 31.624 21.081 15.798 12.632 10.529 9.032 7.902 7.025 7.022 | 31.598 21.065 15.799 12.639 10.533 9.028 7.899 7.022 7.022 | 0.001 | 1.805 | near target favored | 517 713 1172 2205 4309 8459 33300 16730 49888 | 0 | 0 | 786 |
| rank-line | 1 | 10 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 63.196 | 0.00386 | 31.588 21.069 15.795 12.631 10.528 9.027 7.903 7.027 6.320 6.322 | 31.588 21.069 15.795 12.631 10.528 9.027 7.903 7.027 6.320 6.322 | 31.598 21.065 15.799 12.639 10.533 9.028 7.899 7.022 6.320 6.320 | 0.001 | 1.971 | near target favored | 384 772 1284 2318 4386 8458 16800 33453 132947 66560 | 0 | 0 | 2155 |
| rank-line | 1 | 11 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` `14,4` | 63.199 | 0.00386 | 21.083 15.817 12.645 10.532 9.029 7.903 7.023 6.324 5.747 5.745 32.462 | 21.083 15.817 12.645 10.532 9.029 7.903 7.023 6.324 5.747 5.745 32.462 | 31.599 21.066 15.800 12.640 10.533 9.028 7.900 7.022 6.320 5.745 5.745 | 4.650 | 2.188 | far source favored | 626 1239 2242 4592 9419 17223 69924 34866 102916 182516 828 | 0 | 0 | 2671 |

## Run 2026-06-24T17:52:48-04:00

- Start gate lead: `100000000` cycles
- Command: `microbenching/noc/riscv_noc_arbitration_bench.py --layouts two-sided-asym --counts 4 --asym-left 3 --asym-right 1 --packet-bytes 16384 --packets 256 --nocs 0,1 --report microbenching/docs/noc/noc-arbitration-priority.md`
- Rank-priority recipe: run through `tt-device-queue` with `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts rank-line --counts 2,3,4,5,6,7,8,9,10,11 --packet-bytes 16384 --packets 256 --nocs 0,1`; add K=12 on devices with at least 13 live workers in one row
- Asymmetry recipe: `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts two-sided-asym --counts 4 --asym-left 3 --asym-right 1 --packet-bytes 16384 --packets 256 --nocs 0,1`
- Diagonal recipe: `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts diagonal-xleg,diagonal-yleg --counts 4 --packet-bytes 16384 --packets 256 --nocs 0,1`
- Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender
- Placement: target-ingress layouts include one-sided row, near-to-far rank-line, two-sided row/wrap, asymmetric two-sided, holey row, diagonal, diagonal X-leg/Y-leg, multi-row, and start-skew variants
- Ladder columns sort senders near-to-far by modeled routed path and compare against aggregate/min(rank+2,K), which gives the farthest two senders the same tail share
- Receiver visibility cycles are target-side first-observed sentinel timestamps relative to the receiver's gated start

| layout | noc | K | packet B | packets | target | sender order (+skew cyc) | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | near-rank B/cyc | ladder B/cyc | max ladder err | spread | interpretation | receiver visibility cycles | bad counters | target missing | target polls |
|---|---:|---:|---:|---:|---|---|---:|---:|---|---|---|---:|---:|---|---|---:|---:|---:|
| two-sided-asym-3l1r | 0 | 4 | 16384 | 256 | `7,6` | `6,6` `5,6` `4,6` `10,6` | 63.213 | 0.00386 | 21.120 15.819 15.803 31.741 | - | - | - | 0.755 | far source favored | 393 1036 2136 792 | 0 | 0 | 46 |
| two-sided-asym-3l1r | 1 | 4 | 16384 | 256 | `7,6` | `6,6` `5,6` `4,6` `10,6` | 63.287 | 0.00386 | 15.822 15.835 21.150 30.148 | - | - | - | 0.691 | near target favored | 2290 1374 871 469 | 0 | 0 | 47 |

## Run 2026-06-24T17:52:48-04:00

- Start gate lead: `100000000` cycles
- Command: `microbenching/noc/riscv_noc_arbitration_bench.py --layouts diagonal-xleg,diagonal-yleg --counts 4 --packet-bytes 16384 --packets 256 --nocs 0,1 --report microbenching/docs/noc/noc-arbitration-priority.md`
- Rank-priority recipe: run through `tt-device-queue` with `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts rank-line --counts 2,3,4,5,6,7,8,9,10,11 --packet-bytes 16384 --packets 256 --nocs 0,1`; add K=12 on devices with at least 13 live workers in one row
- Asymmetry recipe: `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts two-sided-asym --counts 4 --asym-left 3 --asym-right 1 --packet-bytes 16384 --packets 256 --nocs 0,1`
- Diagonal recipe: `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts diagonal-xleg,diagonal-yleg --counts 4 --packet-bytes 16384 --packets 256 --nocs 0,1`
- Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender
- Placement: target-ingress layouts include one-sided row, near-to-far rank-line, two-sided row/wrap, asymmetric two-sided, holey row, diagonal, diagonal X-leg/Y-leg, multi-row, and start-skew variants
- Ladder columns sort senders near-to-far by modeled routed path and compare against aggregate/min(rank+2,K), which gives the farthest two senders the same tail share
- Receiver visibility cycles are target-side first-observed sentinel timestamps relative to the receiver's gated start

| layout | noc | K | packet B | packets | target | sender order (+skew cyc) | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | near-rank B/cyc | ladder B/cyc | max ladder err | spread | interpretation | receiver visibility cycles | bad counters | target missing | target polls |
|---|---:|---:|---:|---:|---|---|---:|---:|---|---|---|---:|---:|---|---|---:|---:|---:|
| diagonal-xleg | 0 | 4 | 16384 | 256 | `7,7` | `6,6` `5,6` `4,6` `3,6` | 63.470 | 0.00387 | 31.743 21.176 15.868 15.883 | 31.743 21.176 15.868 15.883 | 31.735 21.157 15.867 15.867 | 0.001 | 0.750 | near target favored | 393 688 2230 1181 | 0 | 0 | 48 |
| diagonal-yleg | 0 | 4 | 16384 | 256 | `7,7` | `6,6` `6,5` `6,4` `6,3` | 63.594 | 0.00388 | 31.779 21.181 15.914 15.899 | 31.779 21.181 15.914 15.899 | 31.797 21.198 15.899 15.899 | 0.001 | 0.749 | near target favored | 642 925 448 1434 | 0 | 0 | 26 |
| diagonal-xleg | 1 | 4 | 16384 | 256 | `7,7` | `10,8` `11,8` `12,8` `13,8` | 63.622 | 0.00388 | 31.816 21.222 15.921 15.906 | 31.816 21.222 15.921 15.906 | 31.811 21.207 15.905 15.905 | 0.001 | 0.750 | near target favored | 413 645 1168 2201 | 0 | 0 | 47 |
| diagonal-yleg | 1 | 4 | 16384 | 256 | `7,7` | `10,8` `10,9` `10,10` `10,11` | 63.251 | 0.00386 | 21.076 15.829 15.813 31.491 | 21.076 15.829 15.813 31.491 | 31.626 21.084 15.813 15.813 | 0.991 | 0.745 | far source favored | 409 922 1956 678 | 0 | 0 | 42 |
