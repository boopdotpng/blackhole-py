# Test overlap review

Reviewed the five operation PoC subtrees on 2026-09-06. There are **28 test
functions in 9 files, collecting 622 independently named pytest cases** after
removing four duplicates from the previous 626. Counts exclude historical
evidence records and repeated launches inside tests. Transport cases still
contain their existing runtime length sweeps; no tests were combined.

| Area | Test files | Test functions | Collected cases |
|---|---:|---:|---:|
| transport | 4 | 4 | 32 |
| fpu | 2 | 2 | 224 |
| sfpu_math | 1 | 9 | 74 |
| sfpu_movement | 1 | 6 | 238 |
| runtime | 1 | 7 | 54 |
| Total | 9 | 28 | 622 |

## Removed duplicates

All paths below are relative to `sfpu_math/test_math.py`.

| Removed case | Retained equivalent | Reason |
|---|---|---|
| `test_aliases[all-add]` | `test_aliases[other-add]` | Add ignores the addend register. |
| `test_aliases[all-sub]` | `test_aliases[other-sub]` | Subtract ignores the addend register. |
| `test_aliases[all-mul]` | `test_aliases[other-mul]` | Multiply ignores the addend register. |
| `test_exp_same_domain_comparison[native]` | `test_native[exp]` | Same native mode, inputs, slots, mask, repetitions and oracle. |

For each pair, a device-free capture of the first `run()` launch verified
byte-identical assembled kernels and L1 inputs. The common host oracle uses
identical effective operands. MAD keeps all three alias cases because its
addend is an actual operand. Binary `addend` cases remain: they exercise
non-aliased operations at a different placement from `test_operations`.

## Kept intentionally

- BF16/FP32, source A/B, transfer directions, broadcasts, fidelities, allocation
  edges and masks test different behavior or addressing. Similar fixture code
  alone is not a duplicate.
- SFPU movement's predicate construction/reset and math's arithmetic under an
  existing predicate exercise separate emitters and contracts.
- Movement register/alias tests differ from repeated operation timing and
  four-position store tests. Raw versus converted stores use different modes,
  including where normal inputs happen to produce equal values.
- Numerical boundaries, exceptional-value characterization and repeated
  arithmetic chains differ from the ordinary numerical input families.
- Runtime blocking waits differ from uncontended actions. Serial/batched
  transfer modes retain their existing baseline comparison. NoC tests here
  validate the owned operation adapters and their completion/guard contracts;
  older NoC helper tests were not deleted.
- Transport signed/rounding cases differ from the positive prefix sweeps.

## Verification and evidence

CPU collection passed with 622 cases. Comparing complete before/after node-ID
sets confirmed exactly the four removals above, no additions and no renamed
survivors. An AST comparison confirmed that only the two parameter decorators
changed: test bodies, assertions and emitted operation code remain unchanged.
No new hardware run was performed for this selection-only change.

Historical result JSON, logs and pass counts remain unchanged, including the
78-case SFPU math run; it contains evidence for all 74 retained cases. Runtime's
combined-run timeouts and the documented numerical limitations remain open.

## Subsequent combined hardware run

After the selection-only checks above, the user requested one combined queued
session. Job `1ada983fbffe4279a35db72be7edda6c` passed **622 tests in 111.42 s**
(queue wall time 111.78 s), card 0/core index 12, with no skips or failures.
Both queues were healthy, live and empty before submission. No reset was issued.
The existing session-scoped `bh` fixture opens/boots one `Device` and closes it
after all tests; individual launches and L1/DRAM checks reuse it. No harness or
runtime change was necessary. This is sequential execution through one persistent
command queue, with host assertions between launches, not pre-enqueuing every
kernel without observation.

| Area | Cases | Summed pytest case seconds |
|---|---:|---:|
| FPU | 224 | 47.807 |
| SFPU math | 74 | 2.023 |
| SFPU movement | 238 | 5.907 |
| Transport | 32 | 54.146 |
| Runtime | 54 | 1.324 |

Case timings include pytest-attributed setup/teardown and exclude some session
overhead. The full transport runtime-length sweeps and seven measured samples
were enabled. Timings from older separate jobs are not same-core speedup controls.

Exact successful submission (inspect queue status and choose the less-full
healthy queue before repeating; keep both device arguments and TRANSPORT_DEVICE
matched):

```sh
tt-device-queue --client-id poc-review --json queue --device 0 \
  --cwd /home/boop/tenstorrent/blackhole-py --timeout 600 \
  --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 --env TRANSPORT_DEVICE=0 -- \
  '/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider --durations=15 --junitxml=/tmp/poc-review-combined.xml tests/operation_pocs/fpu tests/operation_pocs/sfpu_math tests/operation_pocs/sfpu_movement tests/operation_pocs/transport tests/operation_pocs/runtime --bh-hardware --bh-device=0 --bh-core=12 --bh-timeout=10'
```

`-x` stops at the first failing named pytest case; no tests were merged. Runtime
runs last so a synchronization failure cannot prevent the other areas' evidence.
The physical core index was validated against discovered topology by the fixture.
One successful combined run establishes compatibility in this session, not the
cause or elimination of previous intermittent timeouts. The removed exploratory
blocking source-free fixture is still an unresolved gap and is not among the 622.

Full raw cycle output, queue metadata, per-case JUnit results and timing totals
are retained in `evidence/combined.log`, `evidence/combined-job.json`,
`evidence/combined.xml` and `evidence/timings.json`.
