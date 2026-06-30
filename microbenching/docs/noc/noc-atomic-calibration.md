
## Analysis summary

Bench source: `microbenching/noc/riscv_noc_atomic_visibility_bench.py`

Commands run:

```bash
PYTHONPATH=.:examples PYTHONDONTWRITEBYTECODE=1 python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --nocs 0 --counts 1 --cases same-row-sem-noret --iters 32 --max-polls 10000000 --no-report
PYTHONPATH=.:examples PYTHONDONTWRITEBYTECODE=1 python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --nocs 0,1 --counts 8 --cases hop-row-atomic-blocking,hop-col-atomic-blocking --iters 64 --max-polls 10000000 --report microbenching/docs/noc/noc-atomic-calibration.md
PYTHONPATH=.:examples PYTHONDONTWRITEBYTECODE=1 python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --nocs 0,1 --counts 1 --cases same-row-atomic,same-row-sem,same-row-sem-noret --iters 512 --max-polls 100000000 --report microbenching/docs/noc/noc-atomic-calibration.md
PYTHONPATH=.:examples PYTHONDONTWRITEBYTECODE=1 python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --nocs 0,1 --counts 1,2,4,8 --cases same-row-atomic,same-row-sem,same-row-sem-noret --iters 256 --max-polls 100000000 --report microbenching/docs/noc/noc-atomic-calibration.md
PYTHONPATH=.:examples PYTHONDONTWRITEBYTECODE=1 python3 microbenching/noc/riscv_noc_atomic_visibility_bench.py --nocs 0,1 --counts 8 --cases hop-row-atomic-blocking,hop-col-atomic-blocking --iters 1 --max-polls 10000000 --report microbenching/docs/noc/noc-atomic-calibration.md
```

Validation:

- `python3 -m py_compile microbenching/noc/riscv_noc_atomic_visibility_bench.py`
- All hardware rows below reported `bad = 0`.
- The no-return semaphore form increments the target value while producing zero source atomic responses.

Single-initiator issue cost:

| op | noc | K | issue cyc/op | sender cyc/op | target-observed cyc/op |
|---|---:|---:|---:|---:|---:|
| atomic | 0 | 1 | 36.05 | 36.43 | 36.15 |
| sem | 0 | 1 | 36.06 | 36.45 | 36.15 |
| sem-noret | 0 | 1 | 36.07 | 36.10 | 36.16 |
| atomic | 1 | 1 | 36.05 | 36.43 | 36.13 |
| sem | 1 | 1 | 36.06 | 36.45 | 36.13 |
| sem-noret | 1 | 1 | 36.08 | 36.10 | 36.14 |

Target visibility hop fits from the single-op blocking sweep:

| window | noc | direction | slope cyc/hop | intercept cyc |
|---|---:|---|---:|---:|
| sender completion | 0 | row | 0.39 | 278.18 |
| sender completion | 0 | col | 0.60 | 237.57 |
| sender completion | 1 | row | 0.42 | 278.06 |
| sender completion | 1 | col | 0.58 | 237.50 |
| target observed | 0 | row | 9.75 | 84.88 |
| target observed | 0 | col | 9.60 | 89.32 |
| target observed | 1 | row | 9.70 | 87.43 |
| target observed | 1 | col | 9.76 | 90.07 |

The source-side atomic response completion is effectively distance-flat in this microbench. Target-side first visibility sees about `9.6-9.8 cyc/hop`, which is approximately the expected round trip from the `~5 cyc/hop` packet calibration. Subtracting the single-initiator issue cost leaves about `50-54 cycles` of target update plus target-side polling/visibility intercept; this should not be treated as a clean isolated RMW cost.

Same-target saturation:

| op | noc | K | target observed op/cyc | target observed cyc/op |
|---|---:|---:|---:|---:|
| atomic | 0 | 1 | 0.02754 | 36.31 |
| atomic | 0 | 2 | 0.05492 | 18.21 |
| atomic | 0 | 4 | 0.07880 | 12.69 |
| atomic | 0 | 8 | 0.07928 | 12.61 |
| sem | 0 | 8 | 0.08294 | 12.06 |
| sem-noret | 0 | 8 | 0.07929 | 12.61 |
| atomic | 1 | 1 | 0.02759 | 36.25 |
| atomic | 1 | 2 | 0.05504 | 18.17 |
| atomic | 1 | 4 | 0.07640 | 13.09 |
| atomic | 1 | 8 | 0.08068 | 12.39 |
| sem | 1 | 8 | 0.08297 | 12.05 |
| sem-noret | 1 | 8 | 0.08298 | 12.05 |

Model-facing takeaways:

- Use a separate `atomic_target:<endpoint>` serialization resource. The saturated same-target rate is about `0.08-0.083 ops/cyc`, so `atomic_target_cycles ~= 12.0-12.5 cyc/op`, not the previous 24-cycle placeholder.
- A single initiator is issue-limited at about `36.1 cyc/op`, so the one-initiator stream is not sufficient to saturate the target update pipe.
- Response-bearing `atomic`/`sem` do produce source responses. `sem-noret` with `ret_coord=0` is a real fire-and-forget form for the model and should use zero response bytes.
- For latency modeling, do not expect source completion to expose `issue + 2*d*hop + target_update` directly on this bench; the visible hop term appears in the target-observed window, while source completion is dominated by local response/poll mechanics.

## Run 2026-06-24T18:02:25-04:00

- Suite: `representative`
- Iterations per sender-target edge: `64`
- Start gate lead: `100000000` cycles
- Traffic: BRISC NoC atomic/semaphore increments, optional nonposted unicast writes to the same target L1
- Completion columns compare sender atomic-response/write-ack completion with target BRISC polling of the final L1 value
- Scheduler calibration hint: `n/a`; use same-target atomic rows to refine `atomic_target_cycles` only after subtracting hop/response overhead

| case | mode | noc | K | op | initiators | targets | hops | atomic ops | issue cyc | issue op/cyc | sender cyc | sender op/cyc | target observed cyc | observed op/cyc | observed-minus-sender cyc | sender spreads | bad | target polls |
|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hop-row-h1-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `2,4` | 1 | 64 | 15382 | 0.00416 | 15394 | 0.00416 | 15214 | 0.00421 | -180 | 0.000 | 0 | 1140 |
| hop-row-h2-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `3,4` | 2 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15225 | 0.00420 | -176 | 0.000 | 0 | 1142 |
| hop-row-h3-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `4,4` | 3 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15229 | 0.00420 | -172 | 0.000 | 0 | 1140 |
| hop-row-h4-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `5,4` | 4 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15238 | 0.00420 | -163 | 0.000 | 0 | 1142 |
| hop-row-h5-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `6,4` | 5 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15251 | 0.00420 | -150 | 0.000 | 0 | 1142 |
| hop-row-h6-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `7,4` | 6 | 64 | 15390 | 0.00416 | 15402 | 0.00416 | 15274 | 0.00419 | -128 | 0.000 | 0 | 1143 |
| hop-row-h9-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `10,4` | 9 | 64 | 15390 | 0.00416 | 15402 | 0.00416 | 15288 | 0.00419 | -114 | 0.000 | 0 | 1145 |
| hop-row-h10-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `11,4` | 10 | 64 | 15390 | 0.00416 | 15402 | 0.00416 | 15302 | 0.00418 | -100 | 0.000 | 0 | 1147 |
| hop-col-h1-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,3` | 1 | 64 | 12822 | 0.00499 | 12834 | 0.00499 | 12694 | 0.00504 | -140 | 0.000 | 0 | 950 |
| hop-col-h2-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,4` | 2 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12710 | 0.00504 | -131 | 0.000 | 0 | 951 |
| hop-col-h3-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,5` | 3 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12719 | 0.00503 | -122 | 0.000 | 0 | 952 |
| hop-col-h4-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,6` | 4 | 64 | 12830 | 0.00499 | 12842 | 0.00498 | 12729 | 0.00503 | -113 | 0.000 | 0 | 953 |
| hop-col-h5-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,7` | 5 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12737 | 0.00502 | -104 | 0.000 | 0 | 954 |
| hop-col-h6-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,8` | 6 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12746 | 0.00502 | -95 | 0.000 | 0 | 954 |
| hop-col-h7-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,9` | 7 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12756 | 0.00502 | -85 | 0.000 | 0 | 955 |
| hop-col-h8-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,10` | 8 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12764 | 0.00501 | -77 | 0.000 | 0 | 954 |
| hop-row-h1-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `13,4` | 1 | 64 | 15382 | 0.00416 | 15394 | 0.00416 | 15218 | 0.00421 | -176 | 0.000 | 0 | 1140 |
| hop-row-h2-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `12,4` | 2 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15229 | 0.00420 | -172 | 0.000 | 0 | 1141 |
| hop-row-h3-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `11,4` | 3 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15238 | 0.00420 | -163 | 0.000 | 0 | 1141 |
| hop-row-h4-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `10,4` | 4 | 64 | 15390 | 0.00416 | 15402 | 0.00416 | 15243 | 0.00420 | -159 | 0.000 | 0 | 1142 |
| hop-row-h7-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `7,4` | 7 | 64 | 15390 | 0.00416 | 15402 | 0.00416 | 15247 | 0.00420 | -155 | 0.000 | 0 | 1142 |
| hop-row-h8-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `6,4` | 8 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15278 | 0.00419 | -123 | 0.000 | 0 | 1144 |
| hop-row-h9-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `5,4` | 9 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15301 | 0.00418 | -100 | 0.000 | 0 | 1147 |
| hop-row-h10-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `4,4` | 10 | 64 | 15389 | 0.00416 | 15401 | 0.00416 | 15310 | 0.00418 | -91 | 0.000 | 0 | 1147 |
| hop-col-h1-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,10` | 1 | 64 | 12822 | 0.00499 | 12834 | 0.00499 | 12694 | 0.00504 | -140 | 0.000 | 0 | 951 |
| hop-col-h2-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,9` | 2 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12710 | 0.00504 | -131 | 0.000 | 0 | 952 |
| hop-col-h3-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,8` | 3 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12720 | 0.00503 | -121 | 0.000 | 0 | 952 |
| hop-col-h4-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,7` | 4 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12728 | 0.00503 | -113 | 0.000 | 0 | 953 |
| hop-col-h5-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,6` | 5 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12737 | 0.00502 | -104 | 0.000 | 0 | 954 |
| hop-col-h6-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,5` | 6 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12746 | 0.00502 | -95 | 0.000 | 0 | 954 |
| hop-col-h7-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,4` | 7 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12755 | 0.00502 | -86 | 0.000 | 0 | 955 |
| hop-col-h8-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,3` | 8 | 64 | 12829 | 0.00499 | 12841 | 0.00498 | 12764 | 0.00501 | -77 | 0.000 | 0 | 955 |

## Run 2026-06-24T18:02:32-04:00

- Suite: `representative`
- Iterations per sender-target edge: `512`
- Start gate lead: `100000000` cycles
- Traffic: BRISC NoC atomic/semaphore increments, optional nonposted unicast writes to the same target L1
- Completion columns compare sender atomic-response/write-ack completion with target BRISC polling of the final L1 value
- Scheduler calibration hint: `36.1 cycles/op observed-window mean across same-target rows`; use same-target atomic rows to refine `atomic_target_cycles` only after subtracting hop/response overhead

| case | mode | noc | K | op | initiators | targets | hops | atomic ops | issue cyc | issue op/cyc | sender cyc | sender op/cyc | target observed cyc | observed op/cyc | observed-minus-sender cyc | sender spreads | bad | target polls |
|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| same-row-atomic | pipelined | 0 | 1 | atomic | `13,4` | `14,4` | 1 | 512 | 18455 | 0.02774 | 18653 | 0.02745 | 18511 | 0.02766 | -142 | 0.000 | 0 | 1369 |
| same-row-sem | pipelined | 0 | 1 | sem | `13,4` | `14,4` | 1 | 512 | 18462 | 0.02773 | 18660 | 0.02744 | 18511 | 0.02766 | -149 | 0.000 | 0 | 1368 |
| same-row-sem-noret | pipelined | 0 | 1 | sem-noret | `13,4` | `14,4` | 1 | 512 | 18470 | 0.02772 | 18482 | 0.02770 | 18515 | 0.02765 | 33 | 0.000 | 0 | 1369 |
| same-row-atomic | pipelined | 1 | 1 | atomic | `2,4` | `1,4` | 1 | 512 | 18455 | 0.02774 | 18653 | 0.02745 | 18497 | 0.02768 | -156 | 0.000 | 0 | 1335 |
| same-row-sem | pipelined | 1 | 1 | sem | `2,4` | `1,4` | 1 | 512 | 18462 | 0.02773 | 18660 | 0.02744 | 18499 | 0.02768 | -161 | 0.000 | 0 | 1368 |
| same-row-sem-noret | pipelined | 1 | 1 | sem-noret | `2,4` | `1,4` | 1 | 512 | 18471 | 0.02772 | 18483 | 0.02770 | 18504 | 0.02767 | 21 | 0.000 | 0 | 1368 |

## Run 2026-06-24T18:02:47-04:00

- Suite: `representative`
- Iterations per sender-target edge: `256`
- Start gate lead: `100000000` cycles
- Traffic: BRISC NoC atomic/semaphore increments, optional nonposted unicast writes to the same target L1
- Completion columns compare sender atomic-response/write-ack completion with target BRISC polling of the final L1 value
- Scheduler calibration hint: `19.9 cycles/op observed-window mean across same-target rows`; use same-target atomic rows to refine `atomic_target_cycles` only after subtracting hop/response overhead

| case | mode | noc | K | op | initiators | targets | hops | atomic ops | issue cyc | issue op/cyc | sender cyc | sender op/cyc | target observed cyc | observed op/cyc | observed-minus-sender cyc | sender spreads | bad | target polls |
|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| same-row-atomic | pipelined | 0 | 1 | atomic | `13,4` | `14,4` | 1 | 256 | 9239 | 0.02771 | 9437 | 0.02713 | 9294 | 0.02754 | -143 | 0.000 | 0 | 686 |
| same-row-sem | pipelined | 0 | 1 | sem | `13,4` | `14,4` | 1 | 256 | 9247 | 0.02768 | 9445 | 0.02710 | 9302 | 0.02752 | -143 | 0.000 | 0 | 687 |
| same-row-sem-noret | pipelined | 0 | 1 | sem-noret | `13,4` | `14,4` | 1 | 256 | 9255 | 0.02766 | 9267 | 0.02762 | 9300 | 0.02753 | 33 | 0.000 | 0 | 686 |
| same-row-atomic | pipelined | 0 | 2 | atomic | `12,4` `13,4` | `14,4` | 1..2 | 512 | 9254 | 0.05533 | 9452 | 0.05417 | 9322 | 0.05492 | -130 | 0.001 | 0 | 689 |
| same-row-sem | pipelined | 0 | 2 | sem | `12,4` `13,4` | `14,4` | 1..2 | 512 | 9255 | 0.05532 | 9453 | 0.05416 | 9320 | 0.05494 | -133 | 0.000 | 0 | 689 |
| same-row-sem-noret | pipelined | 0 | 2 | sem-noret | `12,4` `13,4` | `14,4` | 1..2 | 512 | 9259 | 0.05530 | 9271 | 0.05523 | 9322 | 0.05492 | 51 | 0.000 | 0 | 688 |
| same-row-atomic | pipelined | 0 | 4 | atomic | `10,4` `11,4` `12,4` `13,4` | `14,4` | 1..4 | 1024 | 12921 | 0.07925 | 13119 | 0.07805 | 12995 | 0.07880 | -124 | 0.286 | 0 | 964 |
| same-row-sem | pipelined | 0 | 4 | sem | `10,4` `11,4` `12,4` `13,4` | `14,4` | 1..4 | 1024 | 12904 | 0.07936 | 13102 | 0.07816 | 12975 | 0.07892 | -127 | 0.287 | 0 | 962 |
| same-row-sem-noret | pipelined | 0 | 4 | sem-noret | `10,4` `11,4` `12,4` `13,4` | `14,4` | 1..4 | 1024 | 13060 | 0.07841 | 13072 | 0.07834 | 13134 | 0.07797 | 62 | 0.343 | 0 | 985 |
| same-row-atomic | pipelined | 0 | 8 | atomic | `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | `14,4` | 1..10 | 2048 | 24319 | 0.08421 | 25893 | 0.07909 | 25834 | 0.07928 | -59 | 1.032 | 0 | 1940 |
| same-row-sem | pipelined | 0 | 8 | sem | `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | `14,4` | 1..10 | 2048 | 23327 | 0.08780 | 24757 | 0.08272 | 24694 | 0.08294 | -63 | 0.973 | 0 | 1799 |
| same-row-sem-noret | pipelined | 0 | 8 | sem-noret | `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` `12,4` `13,4` | `14,4` | 1..10 | 2048 | 24299 | 0.08428 | 24311 | 0.08424 | 25828 | 0.07929 | 1517 | 1.025 | 0 | 1940 |
| same-row-atomic | pipelined | 1 | 1 | atomic | `2,4` | `1,4` | 1 | 256 | 9239 | 0.02771 | 9437 | 0.02713 | 9280 | 0.02759 | -157 | 0.000 | 0 | 685 |
| same-row-sem | pipelined | 1 | 1 | sem | `2,4` | `1,4` | 1 | 256 | 9246 | 0.02769 | 9444 | 0.02711 | 9280 | 0.02759 | -164 | 0.000 | 0 | 670 |
| same-row-sem-noret | pipelined | 1 | 1 | sem-noret | `2,4` | `1,4` | 1 | 256 | 9254 | 0.02766 | 9266 | 0.02763 | 9291 | 0.02755 | 25 | 0.000 | 0 | 686 |
| same-row-atomic | pipelined | 1 | 2 | atomic | `2,4` `3,4` | `1,4` | 1..2 | 512 | 9256 | 0.05532 | 9462 | 0.05411 | 9303 | 0.05504 | -159 | 0.002 | 0 | 687 |
| same-row-sem | pipelined | 1 | 2 | sem | `2,4` `3,4` | `1,4` | 1..2 | 512 | 9249 | 0.05536 | 9447 | 0.05420 | 9296 | 0.05508 | -151 | 0.000 | 0 | 686 |
| same-row-sem-noret | pipelined | 1 | 2 | sem-noret | `2,4` `3,4` | `1,4` | 1..2 | 512 | 9261 | 0.05529 | 9273 | 0.05521 | 9311 | 0.05499 | 38 | 0.000 | 0 | 688 |
| same-row-atomic | pipelined | 1 | 4 | atomic | `2,4` `3,4` `4,4` `5,4` | `1,4` | 1..4 | 1024 | 13335 | 0.07679 | 13533 | 0.07567 | 13403 | 0.07640 | -130 | 0.336 | 0 | 1005 |
| same-row-sem | pipelined | 1 | 4 | sem | `2,4` `3,4` `4,4` `5,4` | `1,4` | 1..4 | 1024 | 13328 | 0.07683 | 13526 | 0.07571 | 13394 | 0.07645 | -132 | 0.336 | 0 | 1004 |
| same-row-sem-noret | pipelined | 1 | 4 | sem-noret | `2,4` `3,4` `4,4` `5,4` | `1,4` | 1..4 | 1024 | 13361 | 0.07664 | 13373 | 0.07657 | 13419 | 0.07631 | 46 | 0.365 | 0 | 1006 |
| same-row-atomic | pipelined | 1 | 8 | atomic | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` | `1,4` | 1..10 | 2048 | 24209 | 0.08460 | 25447 | 0.08048 | 25383 | 0.08068 | -64 | 1.034 | 0 | 1886 |
| same-row-sem | pipelined | 1 | 8 | sem | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` | `1,4` | 1..10 | 2048 | 23583 | 0.08684 | 24749 | 0.08275 | 24684 | 0.08297 | -65 | 0.992 | 0 | 1797 |
| same-row-sem-noret | pipelined | 1 | 8 | sem-noret | `2,4` `3,4` `4,4` `5,4` `6,4` `7,4` `10,4` `11,4` | `1,4` | 1..10 | 2048 | 23567 | 0.08690 | 23579 | 0.08686 | 24682 | 0.08298 | 1103 | 0.973 | 0 | 1797 |

## Run 2026-06-24T18:03:10-04:00

- Suite: `representative`
- Iterations per sender-target edge: `1`
- Start gate lead: `100000000` cycles
- Traffic: BRISC NoC atomic/semaphore increments, optional nonposted unicast writes to the same target L1
- Completion columns compare sender atomic-response/write-ack completion with target BRISC polling of the final L1 value
- Scheduler calibration hint: `n/a`; use same-target atomic rows to refine `atomic_target_cycles` only after subtracting hop/response overhead

| case | mode | noc | K | op | initiators | targets | hops | atomic ops | issue cyc | issue op/cyc | sender cyc | sender op/cyc | target observed cyc | observed op/cyc | observed-minus-sender cyc | sender spreads | bad | target polls |
|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hop-row-h1-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `2,4` | 1 | 1 | 262 | 0.00382 | 274 | 0.00365 | 90 | 0.01111 | -184 | 0.000 | 0 | 4 |
| hop-row-h2-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `3,4` | 2 | 1 | 269 | 0.00372 | 281 | 0.00356 | 109 | 0.00917 | -172 | 0.000 | 0 | 6 |
| hop-row-h3-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `4,4` | 3 | 1 | 269 | 0.00372 | 281 | 0.00356 | 112 | 0.00893 | -169 | 0.000 | 0 | 7 |
| hop-row-h4-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `5,4` | 4 | 1 | 269 | 0.00372 | 281 | 0.00356 | 118 | 0.00847 | -163 | 0.000 | 0 | 7 |
| hop-row-h5-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `6,4` | 5 | 1 | 269 | 0.00372 | 281 | 0.00356 | 138 | 0.00725 | -143 | 0.000 | 0 | 9 |
| hop-row-h6-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `7,4` | 6 | 1 | 269 | 0.00372 | 281 | 0.00356 | 153 | 0.00654 | -128 | 0.000 | 0 | 9 |
| hop-row-h9-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `10,4` | 9 | 1 | 269 | 0.00372 | 281 | 0.00356 | 167 | 0.00599 | -114 | 0.000 | 0 | 10 |
| hop-row-h10-atomic-blocking | blocking | 0 | 1 | atomic | `1,4` | `11,4` | 10 | 1 | 269 | 0.00372 | 281 | 0.00356 | 182 | 0.00549 | -99 | 0.000 | 0 | 12 |
| hop-col-h1-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,3` | 1 | 1 | 222 | 0.00450 | 234 | 0.00427 | 94 | 0.01064 | -140 | 0.000 | 0 | 5 |
| hop-col-h2-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,4` | 2 | 1 | 229 | 0.00437 | 241 | 0.00415 | 111 | 0.00901 | -130 | 0.000 | 0 | 6 |
| hop-col-h3-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,5` | 3 | 1 | 229 | 0.00437 | 241 | 0.00415 | 120 | 0.00833 | -121 | 0.000 | 0 | 6 |
| hop-col-h4-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,6` | 4 | 1 | 229 | 0.00437 | 241 | 0.00415 | 129 | 0.00775 | -112 | 0.000 | 0 | 7 |
| hop-col-h5-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,7` | 5 | 1 | 230 | 0.00435 | 242 | 0.00413 | 139 | 0.00719 | -103 | 0.000 | 0 | 8 |
| hop-col-h6-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,8` | 6 | 1 | 229 | 0.00437 | 241 | 0.00415 | 147 | 0.00680 | -94 | 0.000 | 0 | 9 |
| hop-col-h7-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,9` | 7 | 1 | 229 | 0.00437 | 241 | 0.00415 | 156 | 0.00641 | -85 | 0.000 | 0 | 10 |
| hop-col-h8-atomic-blocking | blocking | 0 | 1 | atomic | `1,2` | `1,10` | 8 | 1 | 229 | 0.00437 | 241 | 0.00415 | 164 | 0.00610 | -77 | 0.000 | 0 | 9 |
| hop-row-h1-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `13,4` | 1 | 1 | 262 | 0.00382 | 274 | 0.00365 | 101 | 0.00990 | -173 | 0.000 | 0 | 6 |
| hop-row-h2-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `12,4` | 2 | 1 | 269 | 0.00372 | 281 | 0.00356 | 109 | 0.00917 | -172 | 0.000 | 0 | 6 |
| hop-row-h3-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `11,4` | 3 | 1 | 269 | 0.00372 | 281 | 0.00356 | 119 | 0.00840 | -162 | 0.000 | 0 | 7 |
| hop-row-h4-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `10,4` | 4 | 1 | 270 | 0.00370 | 282 | 0.00355 | 130 | 0.00769 | -152 | 0.000 | 0 | 8 |
| hop-row-h7-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `7,4` | 7 | 1 | 269 | 0.00372 | 281 | 0.00356 | 126 | 0.00794 | -155 | 0.000 | 0 | 7 |
| hop-row-h8-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `6,4` | 8 | 1 | 269 | 0.00372 | 281 | 0.00356 | 159 | 0.00629 | -122 | 0.000 | 0 | 10 |
| hop-row-h9-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `5,4` | 9 | 1 | 269 | 0.00372 | 281 | 0.00356 | 182 | 0.00549 | -99 | 0.000 | 0 | 12 |
| hop-row-h10-atomic-blocking | blocking | 1 | 1 | atomic | `14,4` | `4,4` | 10 | 1 | 270 | 0.00370 | 282 | 0.00355 | 200 | 0.00500 | -82 | 0.000 | 0 | 13 |
| hop-col-h1-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,10` | 1 | 1 | 222 | 0.00450 | 234 | 0.00427 | 95 | 0.01053 | -139 | 0.000 | 0 | 6 |
| hop-col-h2-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,9` | 2 | 1 | 229 | 0.00437 | 241 | 0.00415 | 111 | 0.00901 | -130 | 0.000 | 0 | 6 |
| hop-col-h3-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,8` | 3 | 1 | 229 | 0.00437 | 241 | 0.00415 | 124 | 0.00806 | -117 | 0.000 | 0 | 8 |
| hop-col-h4-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,7` | 4 | 1 | 229 | 0.00437 | 241 | 0.00415 | 130 | 0.00769 | -111 | 0.000 | 0 | 8 |
| hop-col-h5-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,6` | 5 | 1 | 229 | 0.00437 | 241 | 0.00415 | 139 | 0.00719 | -102 | 0.000 | 0 | 9 |
| hop-col-h6-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,5` | 6 | 1 | 229 | 0.00437 | 241 | 0.00415 | 149 | 0.00671 | -92 | 0.000 | 0 | 10 |
| hop-col-h7-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,4` | 7 | 1 | 229 | 0.00437 | 241 | 0.00415 | 156 | 0.00641 | -85 | 0.000 | 0 | 10 |
| hop-col-h8-atomic-blocking | blocking | 1 | 1 | atomic | `1,11` | `1,3` | 8 | 1 | 229 | 0.00437 | 241 | 0.00415 | 168 | 0.00595 | -73 | 0.000 | 0 | 10 |
