
## Run 2026-06-13T16:45:47-04:00

- Start gate lead: `100000000` cycles
- Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender
- Placement: one row; NoC0 sends right into the row's right edge, NoC1 sends left into the row's left edge
- Sender order: farthest from target to nearest target; favored nearest implies through-traffic priority, favored farthest implies injection priority

| noc | K | packet B | packets | target | sender order | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | spread | interpretation | bad counters | target missing | target polls |
|---:|---:|---:|---:|---|---|---:|---:|---|---:|---|---:|---:|---:|
| 0 | 2 | 4096 | 128 | `14,4` | `12,4` `13,4` | 61.134 | 0.01493 | 30.567 30.669 | 0.003 | roughly equal | 0 | 0 | 6 |
| 0 | 2 | 16384 | 128 | `14,4` | `12,4` `13,4` | 62.783 | 0.00383 | 31.392 31.508 | 0.004 | roughly equal | 0 | 0 | 18 |
| 0 | 3 | 4096 | 128 | `14,4` | `11,4` `12,4` `13,4` | 61.454 | 0.01500 | 20.545 20.488 30.685 | 0.427 | near target favored | 0 | 0 | 7 |
| 0 | 3 | 16384 | 128 | `14,4` | `11,4` `12,4` `13,4` | 62.860 | 0.00384 | 20.955 21.006 31.505 | 0.431 | near target favored | 0 | 0 | 24 |
| 0 | 4 | 4096 | 128 | `14,4` | `10,4` `11,4` `12,4` `13,4` | 61.652 | 0.01505 | 15.413 15.436 20.539 30.685 | 0.744 | near target favored | 0 | 0 | 10 |
| 0 | 4 | 16384 | 128 | `14,4` | `10,4` `11,4` `12,4` `13,4` | 63.062 | 0.00385 | 15.766 15.795 21.020 31.611 | 0.753 | near target favored | 0 | 0 | 27 |
| 0 | 6 | 4096 | 128 | `14,4` | `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 61.828 | 0.01509 | 10.306 10.314 12.347 15.447 20.545 30.685 | 1.227 | near target favored | 0 | 0 | 19 |
| 0 | 6 | 16384 | 128 | `14,4` | `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 63.170 | 0.00386 | 10.529 10.541 12.655 15.817 21.093 31.611 | 1.237 | near target favored | 0 | 0 | 97 |
| 0 | 8 | 4096 | 128 | `14,4` | `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 61.909 | 0.01511 | 7.739 7.747 8.848 10.315 12.368 15.439 20.546 30.683 | 1.615 | near target favored | 0 | 0 | 75 |
| 0 | 8 | 16384 | 128 | `14,4` | `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 63.098 | 0.00385 | 7.887 7.895 9.024 10.521 12.623 15.766 21.006 31.505 | 1.626 | near target favored | 0 | 0 | 295 |
| 1 | 2 | 4096 | 128 | `1,4` | `2,4` `3,4` | 61.045 | 0.01490 | 30.612 30.526 | 0.003 | roughly equal | 0 | 0 | 5 |
| 1 | 2 | 16384 | 128 | `1,4` | `2,4` `3,4` | 62.811 | 0.00383 | 31.520 31.407 | 0.004 | roughly equal | 0 | 0 | 17 |
| 1 | 3 | 4096 | 128 | `1,4` | `2,4` `3,4` `4,4` | 61.385 | 0.01499 | 30.628 20.514 20.462 | 0.426 | far source favored | 0 | 0 | 6 |
| 1 | 3 | 16384 | 128 | `1,4` | `2,4` `3,4` `4,4` | 62.901 | 0.00384 | 31.516 21.021 20.967 | 0.431 | far source favored | 0 | 0 | 23 |
| 1 | 4 | 4096 | 128 | `1,4` | `2,4` `3,4` `4,4` `5,4` | 61.639 | 0.01505 | 30.657 20.545 15.436 15.414 | 0.743 | far source favored | 0 | 0 | 9 |
| 1 | 4 | 16384 | 128 | `1,4` | `2,4` `3,4` `4,4` `5,4` | 63.013 | 0.00385 | 31.520 21.051 15.784 15.754 | 0.750 | far source favored | 0 | 0 | 35 |
| 1 | 6 | 4096 | 128 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` | 61.840 | 0.01510 | 30.642 20.539 15.432 12.363 10.315 10.308 | 1.225 | far source favored | 0 | 0 | 24 |
| 1 | 6 | 16384 | 128 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` | 63.169 | 0.00386 | 31.611 21.088 15.806 12.654 10.541 10.528 | 1.237 | far source favored | 0 | 0 | 96 |
| 1 | 8 | 4096 | 128 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` | 61.884 | 0.01511 | 30.628 20.526 15.425 12.359 10.311 8.839 7.744 7.736 | 1.613 | far source favored | 0 | 0 | 56 |
| 1 | 8 | 16384 | 128 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` | 63.182 | 0.00386 | 31.558 21.080 15.799 12.643 10.536 9.035 7.906 7.898 | 1.625 | far source favored | 0 | 0 | 295 |

## Run 2026-06-13T16:55:15-04:00

- Start gate lead: `100000000` cycles
- Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender
- Placement: one row; NoC0 sends right into the row's right edge, NoC1 sends left into the row's left edge
- Sender order: farthest from target to nearest target; favored nearest implies through-traffic priority, favored farthest implies injection priority

| noc | K | packet B | packets | target | sender order | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | spread | interpretation | bad counters | target missing | target polls |
|---:|---:|---:|---:|---|---|---:|---:|---|---:|---|---:|---:|---:|
| 0 | 2 | 16384 | 256 | `14,4` | `12,4` `13,4` | 62.921 | 0.00384 | 31.461 31.519 | 0.002 | roughly equal | 0 | 0 | 18 |
| 0 | 3 | 16384 | 256 | `14,4` | `11,4` `12,4` `13,4` | 63.064 | 0.00385 | 21.022 21.047 31.599 | 0.431 | near target favored | 0 | 0 | 24 |
| 0 | 4 | 16384 | 256 | `14,4` | `10,4` `11,4` `12,4` `13,4` | 63.070 | 0.00385 | 15.768 15.782 21.053 31.550 | 0.750 | near target favored | 0 | 0 | 36 |
| 0 | 5 | 16384 | 256 | `14,4` | `7,4` `10,4` `11,4` `12,4` `13,4` | 63.059 | 0.00385 | 12.622 12.612 15.781 21.040 31.510 | 1.010 | near target favored | 0 | 0 | 58 |
| 0 | 6 | 16384 | 256 | `14,4` | `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 63.208 | 0.00386 | 10.542 10.535 12.659 15.810 21.098 31.645 | 1.238 | near target favored | 0 | 0 | 97 |
| 0 | 7 | 16384 | 256 | `14,4` | `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 63.172 | 0.00386 | 9.025 9.030 10.538 12.644 15.796 21.080 31.634 | 1.442 | near target favored | 0 | 0 | 168 |
| 0 | 8 | 16384 | 256 | `14,4` | `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 63.220 | 0.00386 | 7.907 7.903 9.040 10.544 12.653 15.803 21.044 31.611 | 1.628 | near target favored | 0 | 0 | 291 |
| 1 | 2 | 16384 | 256 | `1,4` | `2,4` `3,4` | 62.913 | 0.00384 | 31.517 31.457 | 0.002 | roughly equal | 0 | 0 | 17 |
| 1 | 3 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` | 62.957 | 0.00384 | 31.518 21.011 20.986 | 0.430 | far source favored | 0 | 0 | 23 |
| 1 | 4 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` | 63.132 | 0.00385 | 31.616 21.079 15.798 15.783 | 0.752 | far source favored | 0 | 0 | 35 |
| 1 | 5 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` | 63.141 | 0.00385 | 31.605 21.074 15.806 12.637 12.628 | 1.012 | far source favored | 0 | 0 | 57 |
| 1 | 6 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` | 63.235 | 0.00386 | 31.620 21.095 15.816 12.662 10.545 10.539 | 1.237 | far source favored | 0 | 0 | 96 |
| 1 | 7 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` | 63.115 | 0.00385 | 31.521 21.044 15.781 12.637 10.527 9.021 9.016 | 1.438 | far source favored | 0 | 0 | 168 |
| 1 | 8 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` | 63.156 | 0.00385 | 31.582 21.061 15.801 12.644 10.535 9.027 7.898 7.895 | 1.627 | far source favored | 0 | 0 | 295 |

## Run 2026-06-13T17:39:26-04:00

- Start gate lead: `100000000` cycles
- Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender
- Placement: one row; NoC0 sends right into the row's right edge, NoC1 sends left into the row's left edge
- Sender order: farthest from target to nearest target; favored nearest implies through-traffic priority, favored farthest implies injection priority

| noc | K | packet B | packets | target | sender order | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | spread | interpretation | bad counters | target missing | target polls |
|---:|---:|---:|---:|---|---|---:|---:|---|---:|---|---:|---:|---:|
| 0 | 8 | 16384 | 256 | `14,4` | `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | 62.888 | 0.00384 | 7.861 7.865 8.986 10.479 12.565 15.681 20.874 31.193 | 1.616 | near target favored | 0 | 0 | 303 |

## Run 2026-06-13T17:39:32-04:00

- Start gate lead: `100000000` cycles
- Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender
- Placement: one row; NoC0 sends right into the row's right edge, NoC1 sends left into the row's left edge
- Sender order: farthest from target to nearest target; favored nearest implies through-traffic priority, favored farthest implies injection priority

| noc | K | packet B | packets | target | sender order | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | spread | interpretation | bad counters | target missing | target polls |
|---:|---:|---:|---:|---|---|---:|---:|---|---:|---|---:|---:|---:|
| 1 | 8 | 16384 | 256 | `1,4` | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` | 63.141 | 0.00385 | 31.595 21.080 15.798 12.631 10.531 9.019 7.893 7.897 | 1.628 | far source favored | 0 | 0 | 221 |

## Run 2026-06-13T17:35:34-04:00

- Start gate lead: `100000000` cycles
- Command: `microbenching/noc/riscv_noc_arbitration_bench.py --layouts all --counts 4 --packet-bytes 4096,16384 --packets 64 --nocs 0,1`
- Full matrix recipe: run through `tt-device-queue` with `PYTHONPATH=.:examples python3 microbenching/noc/riscv_noc_arbitration_bench.py --layouts all --counts 2,3,4,6,8 --packet-bytes 4096,16384 --packets 256 --nocs 0,1`
- Traffic: BRISC nonposted peer-L1 writes, one far-end receiver tile, one destination slice per sender
- Placement: target-ingress layouts include one-sided row, two-sided row/wrap, holey row, diagonal, multi-row, and start-skew variants
- Receiver visibility cycles are target-side first-observed sentinel timestamps relative to the receiver's gated start

| layout | noc | K | packet B | packets | target | sender order (+skew cyc) | aggregate B/cyc | aggregate req/cyc | per-stream B/cyc | spread | interpretation | receiver visibility cycles | bad counters | target missing | target polls |
|---|---:|---:|---:|---:|---|---|---:|---:|---|---:|---|---|---:|---:|---:|
| one-sided | 0 | 4 | 4096 | 64 | `14,4` | `10,4` `11,4` `12,4` `13,4` | 61.252 | 0.01495 | 15.313 15.371 20.405 30.372 | 0.739 | near target favored | 669 414 290 210 | 0 | 0 | 11 |
| one-sided | 0 | 4 | 16384 | 64 | `14,4` | `10,4` `11,4` `12,4` `13,4` | 62.987 | 0.00384 | 15.747 15.808 21.090 31.608 | 0.753 | near target favored | 2216 1167 660 383 | 0 | 0 | 48 |
| two-sided | 0 | 4 | 4096 | 64 | `7,6` | `6,6` `10,6` `5,6` `11,6` | 61.991 | 0.01513 | 15.657 15.538 15.501 15.590 | 0.010 | roughly equal | 237 507 382 312 | 0 | 0 | 6 |
| two-sided | 0 | 4 | 16384 | 64 | `7,6` | `6,6` `10,6` `5,6` `11,6` | 63.153 | 0.00385 | 15.850 15.876 15.788 16.042 | 0.016 | roughly equal | 785 1116 1260 543 | 0 | 0 | 18 |
| holes | 0 | 4 | 4096 | 64 | `14,4` | `4,4` `6,4` `10,4` `12,4` | 61.464 | 0.01501 | 15.378 15.407 20.445 30.376 | 0.735 | near target favored | 687 432 309 226 | 0 | 0 | 11 |
| holes | 0 | 4 | 16384 | 64 | `14,4` | `4,4` `6,4` `10,4` `12,4` | 63.155 | 0.00385 | 15.790 15.846 21.148 31.677 | 0.752 | near target favored | 2227 1179 675 462 | 0 | 0 | 48 |
| diagonal | 0 | 4 | 4096 | 64 | `7,7` | `6,6` `5,6` `6,5` `4,6` | 61.353 | 0.01498 | 20.419 15.343 30.344 15.407 | 0.736 | middle source favored | 327 661 265 444 | 0 | 0 | 10 |
| diagonal | 0 | 4 | 16384 | 64 | `7,7` | `6,6` `5,6` `6,5` `4,6` | 63.196 | 0.00386 | 21.131 15.857 31.418 15.802 | 0.742 | middle source favored | 411 925 661 1962 | 0 | 0 | 42 |
| multi-row | 0 | 4 | 4096 | 64 | `7,7` | `7,6` `6,6` `5,6` `4,6` | 61.439 | 0.01500 | 30.764 20.445 15.407 15.364 | 0.751 | far source favored | 251 289 432 673 | 0 | 0 | 10 |
| multi-row | 0 | 4 | 16384 | 64 | `7,7` | `7,6` `6,6` `5,6` `4,6` | 63.304 | 0.00386 | 31.853 21.179 15.886 15.827 | 0.756 | far source favored | 407 639 1162 2228 | 0 | 0 | 48 |
| start-skew | 0 | 4 | 4096 | 64 | `14,4` | `10,4` `11,4+10000` `12,4+20000` `13,4+30000` | 30.455 | 0.00744 | 59.389 59.538 58.896 59.215 | 0.011 | roughly equal | 252 10266 20251 30195 | 0 | 0 | 663 |
| start-skew | 0 | 4 | 16384 | 64 | `14,4` | `10,4` `11,4+10000` `12,4+20000` `13,4+30000` | 62.756 | 0.00383 | 39.435 19.613 22.394 31.554 | 0.702 | far source favored | 490 10617 20468 30478 | 0 | 0 | 668 |
| one-sided | 1 | 4 | 4096 | 64 | `1,4` | `2,4` `3,4` `4,4` `5,4` | 61.299 | 0.01497 | 30.401 20.431 15.335 15.392 | 0.739 | far source favored | 230 268 636 381 | 0 | 0 | 10 |
| one-sided | 1 | 4 | 16384 | 64 | `1,4` | `2,4` `3,4` `4,4` `5,4` | 62.889 | 0.00384 | 31.502 21.036 15.783 15.722 | 0.751 | far source favored | 412 644 1168 2235 | 0 | 0 | 48 |
| two-sided | 1 | 4 | 4096 | 64 | `7,6` | `6,6` `10,6` `5,6` `11,6` | 61.630 | 0.01505 | 15.628 15.473 15.740 15.415 | 0.021 | roughly equal | 420 180 289 335 | 0 | 0 | 4 |
| two-sided | 1 | 4 | 16384 | 64 | `7,6` | `6,6` `10,6` `5,6` `11,6` | 63.258 | 0.00386 | 16.352 15.873 16.529 15.817 | 0.044 | roughly equal | 1174 661 699 1130 | 0 | 0 | 16 |
| holes | 1 | 4 | 4096 | 64 | `1,4` | `2,4` `4,4` `6,4` `10,4` | 61.500 | 0.01501 | 30.348 20.443 15.408 15.379 | 0.734 | far source favored | 172 277 368 642 | 0 | 0 | 10 |
| holes | 1 | 4 | 16384 | 64 | `1,4` | `2,4` `4,4` `6,4` `10,4` | 63.010 | 0.00385 | 31.662 21.087 15.806 15.754 | 0.755 | far source favored | 409 641 1164 2230 | 0 | 0 | 48 |
| diagonal | 1 | 4 | 4096 | 64 | `7,7` | `10,8` `11,8` `10,9` `12,8` | 61.468 | 0.01501 | 15.538 15.378 15.428 15.487 | 0.010 | roughly equal | 174 373 320 249 | 0 | 0 | 3 |
| diagonal | 1 | 4 | 16384 | 64 | `7,7` | `10,8` `11,8` `10,9` `12,8` | 63.265 | 0.00386 | 16.002 15.940 15.878 15.817 | 0.012 | roughly equal | 409 642 926 1168 | 0 | 0 | 18 |
| multi-row | 1 | 4 | 4096 | 64 | `7,7` | `7,8` `6,8` `5,8` `4,8` | 61.899 | 0.01511 | 26.450 15.479 15.516 20.597 | 0.562 | far source favored | 177 661 438 320 | 0 | 0 | 10 |
| multi-row | 1 | 4 | 16384 | 64 | `7,7` | `7,8` `6,8` `5,8` `4,8` | 63.410 | 0.00387 | 29.568 15.855 15.909 21.118 | 0.665 | far source favored | 922 1163 528 826 | 0 | 0 | 17 |
| start-skew | 1 | 4 | 4096 | 64 | `1,4` | `2,4` `3,4+10000` `4,4+20000` `5,4+30000` | 30.448 | 0.00743 | 59.376 59.538 58.685 59.215 | 0.014 | roughly equal | 179 10192 20226 30236 | 0 | 0 | 665 |
| start-skew | 1 | 4 | 16384 | 64 | `1,4` | `2,4` `3,4+10000` `4,4+20000` `5,4+30000` | 62.844 | 0.00384 | 44.969 30.029 24.778 28.544 | 0.629 | far source favored | 406 10458 20840 31114 | 0 | 0 | 683 |
