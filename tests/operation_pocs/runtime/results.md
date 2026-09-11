# Runtime operation hardware evidence — resumed 2026-09-06

**Later combined-session verification:** all 54 current runtime cases passed
after the other four operation suites in job `1ada983fbffe4279a35db72be7edda6c`,
card 0/core index 12. The entire session passed 622 tests in 111.42 s with one
device open. See [the combined review](../review.md) for logs and timings.
This supersedes the absence of a final 54-case combined pass below, but does not
establish the cause or elimination of intermittent timeouts. Delayed source-free
coverage remains unresolved and is absent from the current selection.

The prior emitters were retained. The 52-test suite passed together in job `107d2bcc9eda4c7d9d41431951639c92` on card 1, core index 2 (physical 1,4), with **68 complete measured cases**. Two added delayed source-valid tests passed separately on final code in job `874cef64fac24e98a158c111b93a7b3c`, card 0, core index 3 (physical 1,5). Every callable operation has seven-sample cycle evidence and correctness evidence.

**Completion limitation:** later 54-test full-suite revalidations on cards 0 and 1 passed the 24 external/CB cases then timed out at the first TRISC semaphore post. Thus final code has passing operation-level evidence but a reliably passing final combined suite is not claimed. Delayed source-free behavior also remains unresolved: its exploratory two-full-bank fixture timed out; uncontended source-free cycles pass and are measured. No skip/xfail was added to conceal either limitation.

## Resumed changes and failure investigation

`test_runtime.py` source-flag setup now uses `configure_unpacker(..., commit=False)`. Its flag-only NOP sequence does not execute a data unpack, so committing unpack configuration consumes credits that the fixture never returns. The old fixture completed two launches then timed out before the third operation; the corrected fixture completed all eight A/B primitive cases and the 52-test combined run. This is a local fixture change; no shared firmware/runtime/model or emitter modification.

A separate repeated-boot/TRISC-state problem remains: an available worker can pass a standalone TRISC suite then later hang on a no-wait semaphore post. Selecting a different runtime-discovered valid core enabled additional proof but did not reliably eliminate this. Other agents reproduced first-TRISC CQ timeouts. The coordinator and peers were notified; C coordinated a service reset of card 0 (epoch 153), while E used card 1. E performed no reset and made no shared edits. Queue health metadata by itself did not detect the stalled core state.

Added owned `conftest.py` prints hardware-discovered worker/core/DRAM topology and source hashes after the explicitly selected card boots. All jobs use one physical card matching their queue, client `poc-E`, one outstanding job, no background hardware. Before every submission queue health, workers, running and pending were inspected; card 0 was excluded during C's coordinated recovery.

## Measured context and interpretation

One warmup precedes seven measured samples per case. All raw arrays, controls, K and min/median/max are retained in [`evidence/measurements.json`](evidence/measurements.json). Per-job full logs and queue metadata/commands are adjacent. Data from different cards/cores is never pooled. Timed external calls include command setup/address arithmetic and response drain. Write timing drains source lifetime separately before remote visibility. CB/semaphore unrolled repetitions include per-call setup/fences. Source flags accumulate eight individually marked intervals, with an eight-interval empty control. No overhead subtraction or fixed timing threshold is used. K=1 delayed waits include intentional peer delay plus notification, not bare primitive latency.

Measured resident firmware is the unchanged llama3 snapshot documented by `fw/README.md` (reference commit `cce3e77f3a245dadfaa4a29ae3a0dda499b53708`). Context hashes from the queued 52-test pass:

```json
{
  "card": 1,
  "core": [
    1,
    4
  ],
  "core_index": 2,
  "dram_endpoints": [
    [
      [
        17,
        14
      ],
      [
        17,
        13
      ]
    ],
    [
      [
        17,
        15
      ],
      [
        17,
        16
      ]
    ],
    [
      [
        17,
        18
      ],
      [
        17,
        19
      ]
    ],
    [
      [
        17,
        21
      ],
      [
        17,
        22
      ]
    ],
    [
      [
        18,
        14
      ],
      [
        18,
        13
      ]
    ],
    [
      [
        18,
        17
      ],
      [
        18,
        16
      ]
    ],
    [
      [
        18,
        20
      ],
      [
        18,
        19
      ]
    ],
    [
      [
        18,
        23
      ],
      [
        18,
        22
      ]
    ]
  ],
  "firmware_manifest_sha256": "8d7e24525e5a0cbcabf97e70d0415c8871c9f3c899c031ddc23a03cff61a02d6",
  "ops_sha256": "ae96742ac2dabcd191db4b2ac0178b4150709d00731595cc2c5e61f3abac5ef4",
  "runtime_sha256": "094ac79248655ba75aa70810e43636858ba83e3a31b1d11e20f23efc40d80687",
  "worker_count": 117
}
```

## Complete-operation cycle table

The following table is solely card 1/core (1,4), job `107d2bcc9eda4c7d9d41431951639c92`. Normalized values include marker overhead. Full identity and samples remain in JSON.

| Operation | Mode / case | K | Raw min / median / max | Median cycles/call |
|---|---|---:|---:|---:|
| read | serial-baseline; N=128, element_bytes=2, noc=0 | 1 | 542 / 542 / 622 | 542.000 |
| read | batched; N=128, element_bytes=2, noc=0 | 1 | 522 / 522 / 522 | 522.000 |
| write | serial-baseline; N=128, element_bytes=2, noc=0 | 1 | 451 / 451 / 451 | 451.000 |
| write | batched; N=128, element_bytes=2, noc=0 | 1 | 419 / 419 / 419 | 419.000 |
| read | serial-baseline; N=128, element_bytes=2, noc=1 | 1 | 534 / 542 / 542 | 542.000 |
| read | batched; N=128, element_bytes=2, noc=1 | 1 | 514 / 522 / 642 | 522.000 |
| write | serial-baseline; N=128, element_bytes=2, noc=1 | 1 | 451 / 451 / 451 | 451.000 |
| write | batched; N=128, element_bytes=2, noc=1 | 1 | 419 / 419 / 419 | 419.000 |
| read | serial-baseline; N=128, element_bytes=4, noc=0 | 1 | 550 / 550 / 654 | 550.000 |
| read | batched; N=128, element_bytes=4, noc=0 | 1 | 530 / 530 / 562 | 530.000 |
| write | serial-baseline; N=128, element_bytes=4, noc=0 | 1 | 459 / 459 / 459 | 459.000 |
| write | batched; N=128, element_bytes=4, noc=0 | 1 | 427 / 427 / 427 | 427.000 |
| read | serial-baseline; N=128, element_bytes=4, noc=1 | 1 | 550 / 550 / 638 | 550.000 |
| read | batched; N=128, element_bytes=4, noc=1 | 1 | 530 / 530 / 610 | 530.000 |
| write | serial-baseline; N=128, element_bytes=4, noc=1 | 1 | 459 / 459 / 459 | 459.000 |
| write | batched; N=128, element_bytes=4, noc=1 | 1 | 427 / 427 / 427 | 427.000 |
| read | serial-baseline; N=256, element_bytes=2, noc=0 | 1 | 986 / 997 / 1149 | 997.000 |
| read | batched; N=256, element_bytes=2, noc=0 | 1 | 525 / 525 / 677 | 525.000 |
| write | serial-baseline; N=256, element_bytes=2, noc=0 | 1 | 793 / 793 / 793 | 793.000 |
| write | batched; N=256, element_bytes=2, noc=0 | 1 | 438 / 438 / 438 | 438.000 |
| read | serial-baseline; N=256, element_bytes=2, noc=1 | 1 | 986 / 994 / 1114 | 994.000 |
| read | batched; N=256, element_bytes=2, noc=1 | 1 | 525 / 525 / 529 | 525.000 |
| write | serial-baseline; N=256, element_bytes=2, noc=1 | 1 | 793 / 793 / 793 | 793.000 |
| write | batched; N=256, element_bytes=2, noc=1 | 1 | 438 / 438 / 438 | 438.000 |
| read | serial-baseline; N=256, element_bytes=4, noc=0 | 1 | 1002 / 1018 / 1133 | 1018.000 |
| read | batched; N=256, element_bytes=4, noc=0 | 1 | 541 / 541 / 545 | 541.000 |
| write | serial-baseline; N=256, element_bytes=4, noc=0 | 1 | 809 / 809 / 809 | 809.000 |
| write | batched; N=256, element_bytes=4, noc=0 | 1 | 446 / 446 / 446 | 446.000 |
| read | serial-baseline; N=256, element_bytes=4, noc=1 | 1 | 1010 / 1018 / 1170 | 1018.000 |
| read | batched; N=256, element_bytes=4, noc=1 | 1 | 541 / 541 / 545 | 541.000 |
| write | serial-baseline; N=256, element_bytes=4, noc=1 | 1 | 809 / 809 / 809 | 809.000 |
| write | batched; N=256, element_bytes=4, noc=1 | 1 | 446 / 446 / 446 | 446.000 |
| cb_reserve | uncontended; slot=0, initial_counter=0 | 16 | 431 / 435 / 441 | 27.188 |
| cb_publish | uncontended; slot=0, initial_counter=0 | 16 | 400 / 400 / 400 | 25.000 |
| cb_wait | uncontended; slot=0, initial_counter=0 | 16 | 385 / 385 / 391 | 24.062 |
| cb_release | uncontended; slot=0, initial_counter=0 | 16 | 397 / 397 / 401 | 24.812 |
| cb_reserve | uncontended; slot=31, initial_counter=65535 | 16 | 419 / 424 / 429 | 26.500 |
| cb_publish | uncontended; slot=31, initial_counter=65535 | 16 | 399 / 399 / 399 | 24.938 |
| cb_wait | uncontended; slot=31, initial_counter=65535 | 16 | 387 / 387 / 387 | 24.188 |
| cb_release | uncontended; slot=31, initial_counter=65535 | 16 | 397 / 397 / 401 | 24.812 |
| semaphore_post | uncontended; semaphore=1 | 7 | 76 / 76 / 77 | 10.857 |
| semaphore_get | uncontended; semaphore=1 | 7 | 76 / 76 / 76 | 10.857 |
| semaphore_wait_ready | uncontended; semaphore=1 | 7 | 90 / 90 / 90 | 12.857 |
| semaphore_wait_space | uncontended; semaphore=1 | 7 | 90 / 90 / 91 | 12.857 |
| semaphore_post | uncontended; semaphore=2 | 7 | 76 / 76 / 77 | 10.857 |
| semaphore_get | uncontended; semaphore=2 | 7 | 76 / 76 / 76 | 10.857 |
| semaphore_wait_ready | uncontended; semaphore=2 | 7 | 90 / 90 / 91 | 12.857 |
| semaphore_wait_space | uncontended; semaphore=2 | 7 | 90 / 90 / 90 | 12.857 |
| semaphore_post | uncontended; semaphore=5 | 7 | 76 / 76 / 77 | 10.857 |
| semaphore_get | uncontended; semaphore=5 | 7 | 76 / 76 / 77 | 10.857 |
| semaphore_wait_ready | uncontended; semaphore=5 | 7 | 90 / 90 / 90 | 12.857 |
| semaphore_wait_space | uncontended; semaphore=5 | 7 | 90 / 90 / 91 | 12.857 |
| semaphore_post | uncontended; semaphore=7 | 7 | 76 / 76 / 76 | 10.857 |
| semaphore_get | uncontended; semaphore=7 | 7 | 76 / 76 / 77 | 10.857 |
| semaphore_wait_ready | uncontended; semaphore=7 | 7 | 90 / 90 / 90 | 12.857 |
| semaphore_wait_space | uncontended; semaphore=7 | 7 | 90 / 90 / 90 | 12.857 |
| cb_reserve | intentional-peer-wait; slot=31 | 1 | 2163 / 2163 / 2163 | 2163.000 |
| cb_wait | intentional-peer-wait; slot=31 | 1 | 2151 / 2152 / 2152 | 2152.000 |
| semaphore_wait_ready | intentional-peer-wait; semaphore=2 | 1 | 2123 / 2124 / 2126 | 2124.000 |
| semaphore_wait_space | intentional-peer-wait; semaphore=2 | 1 | 2123 / 2125 / 2126 | 2125.000 |
| source_publish | uncontended-accumulated; source_bank=A | 8 | 162 / 162 / 165 | 20.250 |
| source_wait_valid | uncontended-accumulated; source_bank=A | 8 | 136 / 136 / 137 | 17.000 |
| source_release | uncontended-accumulated; source_bank=A | 8 | 154 / 157 / 157 | 19.625 |
| source_wait_free | uncontended-accumulated; source_bank=A | 8 | 136 / 136 / 137 | 17.000 |
| source_publish | uncontended-accumulated; source_bank=B | 8 | 162 / 164 / 165 | 20.500 |
| source_wait_valid | uncontended-accumulated; source_bank=B | 8 | 136 / 136 / 136 | 17.000 |
| source_release | uncontended-accumulated; source_bank=B | 8 | 154 / 154 / 157 | 19.250 |
| source_wait_free | uncontended-accumulated; source_bank=B | 8 | 136 / 136 / 138 | 17.000 |

Batched transfers retain the same oracle and complete-operation boundary as the serial baseline. At N=256, median BF16 read decreases from 997 to 525 cycles on NoC0 and FP32 read from 1018 to 541; writes decrease from 793 to 438 (BF16) and 809 to 446 (FP32). One-block cases primarily remove duplicate drains. Batched remains the simpler default; serial remains callable for same-card comparisons. No more complex optimization was added.

## Exact queue jobs

All jobs ran from `/home/boop/tenstorrent/blackhole-py`, with environment `PYTHONPATH=.` and `PYTHONDONTWRITEBYTECODE=1`; matching queue/physical-device numbers are recorded below. The common submission prefix was `tt-device-queue --client-id poc-E --json queue --device N --cwd /home/boop/tenstorrent/blackhole-py --timeout T --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- COMMAND`. Metadata files retain every exact command and timeout; each command below is the quoted COMMAND argument.

- `0d9a6b3c229f47ae8d95c941e704cbf8`: card 1, queue timeout 180s, exit 1, service timed_out=False; 1 failed, 24 passed in 4.47s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime --bh-hardware --bh-device=1 --bh-core=3 --bh-timeout=3`

- `107d2bcc9eda4c7d9d41431951639c92`: card 1, queue timeout 180s, exit 0, service timed_out=False; 52 passed in 1.84s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime --bh-hardware --bh-device=1 --bh-core=2 --bh-timeout=3`

- `300e6fa53bd84d91a28423186c64fc5b`: card 0, queue timeout 180s, exit 1, service timed_out=False; 1 failed, 24 passed in 4.42s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime --bh-hardware --bh-device=0 --bh-core=2 --bh-timeout=3`

- `502dd29ff3034554a157edfdf7574eb9`: card 0, queue timeout 120s, exit 0, service timed_out=False; 18 passed, 34 deselected in 0.86s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime -k semaphore --bh-hardware --bh-device=0 --bh-core=1 --bh-timeout=3`

- `5bc12ef61b9843ad9cab766a2451cc4e`: card 0, queue timeout 120s, exit 1, service timed_out=False; see log

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime -k source_flags --bh-hardware --bh-device=0 --bh-core=1 --bh-timeout=3`

- `616bd207e28a44868a7311749df4eedc`: card 1, queue timeout 180s, exit 0, service timed_out=False; 26 passed, 26 deselected in 1.46s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime -k "external or cb" --bh-hardware --bh-device=1 --bh-core=0 --bh-timeout=10`

- `7a5c720ac9bd432e895f24685761fa03`: card 1, queue timeout 120s, exit 1, service timed_out=False; 1 failed in 3.65s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime --bh-hardware --bh-device=1 --bh-core=1 --bh-timeout=3`

- `874cef64fac24e98a158c111b93a7b3c`: card 0, queue timeout 60s, exit 0, service timed_out=False; 2 passed, 52 deselected in 0.65s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime -k source_flag_blocking --bh-hardware --bh-device=0 --bh-core=3 --bh-timeout=3`

- `938f8d6baae84ca0b7003aac5b1d759c`: card 0, queue timeout 180s, exit 1, service timed_out=False; 1 failed, 24 passed, 8 deselected in 11.45s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime -k "not source_flags" --bh-hardware --bh-device=0 --bh-core=0 --bh-timeout=10`

- `ac41ff41efd948b28121a384ed77c008`: card 1, queue timeout 120s, exit 0, service timed_out=False; 8 passed, 44 deselected in 0.76s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime -k source_flags --bh-hardware --bh-device=1 --bh-core=2 --bh-timeout=3`

- `b339d5b04ce14f17ad290e58c6ad56c1`: card 1, queue timeout 120s, exit 1, service timed_out=False; 1 failed, 1 passed, 52 deselected in 3.65s

  `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/runtime -k source_flag_blocking --bh-hardware --bh-device=1 --bh-core=2 --bh-timeout=3`

Historical pre-resume failures `2568cf3f2c684d3c95ac3f6f45865d6d` and `9ffb5955a94549ce832b9067d5391e2a` were inspected through the queue to continue prior work. They showed source-fixture timeouts, not a completed source-flag implementation proof. Their earlier samples are not mixed into the retained resumed measurements.

## Remaining scope limits

- Delayed source-free experiment `b339d5b04ce14f17ad290e58c6ad56c1` passed A source-valid wait then timed out in a two-full-bank source-free fixture. That speculative fixture was removed, and its failure is retained explicitly. Existing balanced source-free operation tests remain active, measured and passing in the 52-test job.
- Full 54-test final revalidation failed on shared TRISC state despite previously passing the unchanged 52-test portion; operation-level passes must not be promoted to reliable multi-job integration.
- Semaphores are tested on slots 1/2/5/7 and interior values; saturation at 0/15 is the ISA contract, not separately measured edge coverage.
- External allocations are guarded, but these are single-bank 1/2-block recipes, not interleaved/partial/collective coverage. Source flag sentinels check L1 fixture preservation, not a complete Src/Dst memory snapshot.
- Physical register allocation is delegated to the assembler; per-image byte counts include fixture/profiler overhead. This catalog does not pretend those totals are emitter-only instruction counts.
