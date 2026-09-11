# SFPU movement evidence

Resumed 2026-09-06. Preserved existing emitter, expanded tests and `baseline.log`; added a machine-readable extraction of all 125 historical hardware records in `baseline-results.json`. The historical log has 126 passes (125 hardware cases and one CPU validation), but does not cover all 238 currently collected tests.

## Exact queued runs

All commands use client `poc-D`, cwd `/home/boop/tenstorrent/blackhole-py`, environment `PYTHONPATH=.` and `PYTHONDONTWRITEBYTECODE=1`, queue timeout 900, one process, no xdist. Queue choice is inspected before each submission.

```sh
tt-device-queue --client-id poc-D --json queue --device N --cwd /home/boop/tenstorrent/blackhole-py --timeout 900 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/operation_pocs/sfpu_movement --bh-hardware --bh-device=N --bh-core=0 --bh-timeout=10'
```

Substitute N=1 for the historical pass and N=0/1 for the listed resumed runs. Job metadata provides the exact concrete command.

| Job | Card / core | Outcome |
|---|---|---|
| `e3e2975a1e7d493bbeed2add4209c142` | 1 / index 0, coordinate (1,2) | Historical baseline: 126 passed in 5.15s, exit 0, no skip. `baseline.log` matches queue log. 125 seven-sample records |
| `f04b5cd672a845e1921e3e93270dda05` | 0 / index 0 | Historical follow-up: exit 1 after 11.06s, no validated final suite |
| `1f4a0f9f359d47268b286806763e0bab` | 0 / index 0 | Resumed suite: first lane-mapping case failed after 10.65s; CQ completion 1 timed out (`cq.py:301`). Queue job completed exit 1 in 10.99s, not a service timeout. No hardware correctness or cycles obtained; `final-card0.log` |
| `7f87bb178ac34af6818245969da6d023` | 1 / index 0 | First lane-mapping case CQ completion 1 timeout; exit 1 in 11.00s. No measurements; `final-card1-core0.log` |

At resumed card0 submission queue0 was empty and queue1 had one running/two pending jobs; a submission race placed this job behind another card0 job. At card1 submission both queues were empty and healthy with live workers; alternated to card1. Queue metadata showed reset epochs card0=152/card1=19, last resets 10:12:07/10:13:12 and no pending reset. The harness uses current `device.py`/`cq.py` and `fw/build.py` llama3 firmware; exact on-device firmware revision was not captured by the old log and is not invented here. No reset was performed by Agent D.

## Historical measurements and limits

All rows retain raw seven-sample counts and min/median/max in `baseline-results.json`, with job ID, card, core, dtype, placement, N, K and one-warmup policy. No cards are pooled and no marker subtraction is performed. Representative median ranges over placements, in measured sequence cycles per vector operation:

| Operation | K | Historical median cycles/op |
|---|---:|---:|
| load | 64 | 15.796875 |
| store | 64 | 15.796875 |
| loadi (two instructions) | 16 | 61.25–61.3125 |
| copy | 16 | 59.9375–60 |
| zero constant | 16 | 60–60.0625 |
| one constant | 16 | 59.875–60 |
| l8 constant | 16 | 59.8125 |
| l15 lane tags | 16 | 59.875–59.9375 |

Empty record-marker control median was 13 cycles. These issue-plus-drain measurements include marker overhead and are not advertised as SFPU peak throughput/latency. The baseline predicate/reset log has suspiciously small per-call values after dividing by four and does not establish correct accumulated interval boundaries. Keep its raw data for provenance, but **do not use its normalized predicate/reset values**. Current tests use four accumulated complete predicate+masked-operation intervals, four reset intervals, and (corrected on resumption) four matching accumulated empty control intervals. This corrected version passed the final core1 run below.

No optimized emitter replaced the baseline. The change on resumption is a profiling-control correction and documentation, not a speed claim. The pre-existing expanded suite adds masked loadi/copy, all register sources/destinations/self aliases, configurable l11–l14 and special FP32/raw store patterns. These cases received their own final hardware evidence below.

## CPU checks and remaining work

`PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 /home/boop/tenstorrent/.venv/bin/python -m pytest -q -p no:cacheprovider tests/operation_pocs/sfpu_movement -k cpu`: 1 passed, 237 deselected. Device-free collection: 238 tests collected. These do not replace hardware proof.

Core0 TRISC/CQ execution remains unavailable, but Agent E demonstrated valid core index 1. The unchanged SFPU implementation and corrected timing controls pass there; no reset was needed.

## Final selected version: all 238 tests pass

Queue job **`1e6cf52ff6e347c08d6bbf5eec17f738`**, card **0**, core index **1**, physical coordinate **(2,2)**: **238 passed in 7.10s**, exit 0, no skip/xfail, queue elapsed 7.43s. Both healthy live queues were empty at status inspection; alternated from preceding card1 run to card0.

```sh
tt-device-queue --client-id poc-D --json queue --device 0 --cwd /home/boop/tenstorrent/blackhole-py --timeout 900 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/operation_pocs/sfpu_movement --bh-hardware --bh-device=0 --bh-core=1 --bh-timeout=10'
```

`final-card0-core1.log` retains the complete 403910-byte queue output. `final-results.json` contains **237 hardware cases**, each with one warmup, seven measured samples, raw intervals, K, minimum/median/maximum, median cycles/op, FP32 dtype, N=128, concrete placement/mask/bits/mode, core and job ID. The remaining case validates CPU model operands. This is final implementation evidence, not inherited baseline evidence.

Final median ranges across cases (see JSON for individual raw distributions):

| Interval | K | Median cycles/op range |
|---|---:|---:|
| load, all positions | 64 | 15.734375–15.8125 |
| store, all positions and special bits | 64 | 1.28125–15.796875 |
| loadi, general/special bits | 16 | 1.8125–61.5 |
| copy | 16 | 59.875–59.9375 |
| exposed register copy, eight destinations | 8 | 2.625 |
| exposed register store | 1 | 14–15 |
| complete predicate + masked load | 4 | 5.5–219.25 |
| complete predicate + masked store | 4 | 7–217.75 |
| complete predicate + masked add (observation support) | 4 | 5.5–217.5 |
| complete predicate + masked loadi | 4 | 8–218.5 |
| complete predicate + masked copy | 4 | 7–217.75 |
| predicate reset | 4 | 5–197.75 |

These broad ranges are retained transparently: instruction issue scheduling, mask construction and marker placement differ by case, so ranges are not universal per-instruction latency claims. The empty controls and exact raw values remain attached to each case; no unsupported subtraction or fixed timing assertion is made. Baseline and final runs use different cards/cores, so their numbers are not an optimization comparison. Final correctness checks independently pass on every measured launch, including all-Dst guards, masked inactive lanes, special registers and signed-zero/subnormal/NaN/Inf behavior.
