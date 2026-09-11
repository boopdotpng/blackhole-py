# SFPU math execution evidence

Test selection update: the overlap review removed four equivalent parameter
cases, leaving **74 collected cases**. Test bodies and emitters are unchanged;
the 78-case hardware evidence below remains historical and includes every
retained case. See [the overlap review](../review.md) for exact removals and CPU
verification. No new hardware run is claimed for this selection change.

Continuation on 2026-09-06 preserved the existing arithmetic emitters and 78-case
suite. The earlier worker left no results file; the queue service supplied the
historical baseline below. Final hardware validation completed: **78 passed**,
zero skips, job `5a833c0cd88440328d4af1a1bebd849b`, card 0/core index 1 `(1,3)`.
All 78 cases retain seven measurements in `final-results.json`.

## Historical successful baseline

Job `7e7ec43b14ba496f928a1a9f2f207286`, physical device 1, worker index 0,
core `(1,2)`, finished 2026-09-06 10:42:03: **8 passed**, no skips. Exact command:

```sh
tt-device-queue --client-id poc-C --json queue --device 1 --cwd /home/boop/tenstorrent/blackhole-py --timeout 120 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/operation_pocs/sfpu_math/test_math.py::test_operations --bh-hardware --bh-device=1 --bh-core=0 --bh-timeout=10'
```

All cases FP32, N=128, input/output slots `(0,17,63)`, mask all, no operand
aliases, refined numerical mode, K=4 vector calls. One warmup, seven samples.
All seven samples were identical within each case, so min=median=max as shown.
Raw per-case counts and worst-error inputs are in `baseline-results.json`.

| Operation | Raw min/median/max cycles | Median cycles/vector |
|---|---:|---:|
| add | 78 / 78 / 78 | 19.5 |
| sub | 78 / 78 / 78 | 19.5 |
| mul | 78 / 78 / 78 | 19.5 |
| mad | 78 / 78 / 78 | 19.5 |
| neg | 74 / 74 / 74 | 18.5 |
| abs | 74 / 74 / 74 | 18.5 |
| exp refined | 250 / 250 / 250 | 62.5 |
| reciprocal refined | 118 / 118 / 118 | 29.5 |

Empty-marker interval was 12 cycles in all samples. This old control is one
`record` pair whereas operations accumulate four drained intervals; it cannot
be subtracted directly. Resumed instrumentation adds a matched accumulated
four-interval drain control. No overhead correction is applied.

Basic arithmetic was exact on these dyadic inputs. Maximum relative errors:
exp 2.089872557963821e-5; reciprocal 1.0803341905785135e-7. This baseline
does not establish mask, alias, native-mode, boundary or exception coverage.
The firmware/configuration was not printed by this historical job, so its
exact image hashes cannot be established from that output.

## Failed jobs and current status

| Job | Card | Result |
|---|---:|---|
| `869888833f9246b7ab1dbbd572d9721d` | 0 | Historical full suite: first add launch CQ completion 1 timeout |
| `712fdcc8c17e4c079ddf5338959353b7` | 1 | Historical full suite: first add launch CQ completion 1 timeout |
| `a4866a73881a41b78ab3e74637b228be` | 1 | Resumed unchanged suite: 1 failed, first add launch CQ completion 1 timeout, no cycle samples |

The resumed queue was healthy/enabled with live worker and equal queue depth
when card 1 was selected. It finished 2026-09-06 10:49:06. Exact submission:

```sh
tt-device-queue --client-id poc-C --json queue --device 1 --cwd /home/boop/tenstorrent/blackhole-py --timeout 900 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/operation_pocs/sfpu_math --bh-hardware --bh-device=1 --bh-core=0 --bh-timeout=10'
```

This is a kernel/CQ timeout, not queue timeout or correctness pass. Recovery
was reported to the coordinator; no direct hardware reset was performed.
Device-free collection after matched-control instrumentation: 78 tests
collected. Collection is not hardware validation. Exp/reciprocal exception
semantics outside the documented bounded domain remain explicit API gaps.

## Final selected version

The final emitter is unchanged from the resumed implementation. Changes add a
matched accumulated drain control, complete exception measurement metadata,
firmware worker hashes, and a correct repeated-MAD rounding contract.

Card 0/core index 1 job `8e8783608c87452bb5a66df50843047d` reached 49 passes,
then the 16-call MAD chain failed its exact-FMA oracle. Blackhole MAD is only
partially fused. The chain now requires at most 16 ULP against the independently
rounded FP64 oracle for its noncanceling inputs, while single-call dyadic tests
remain exact. Actual worst relative error was 1.7061e-7 (2 ULP). This is not a
claim of exact IEEE FMA or a bound for arbitrary chains. The failed exact
assertion is retained here rather than hidden by a skip.

Follow-up job `8372c4a6ebdd42be90a84c2449d7579b` on card 0/core index 1 timed
out at its first CQ completion. Peers also observed stale core failures; runtime
found and fixed an owned fixture that consumed unpack configuration credits
without releasing them. That is a plausible cause, not a proven complete boot
diagnosis. With A/B/E confirming no card-0 jobs and D notified, all queue jobs
drained and `tt-device-queue --client-id poc-C --json reset --device 0` recovered
card 0 at 10:55:37, reset epoch 152→153. This was one coordinated recovery,
not routine benchmark setup. No shared runtime files were changed.

Final successful command (both queues healthy/live/empty before selection):

```sh
tt-device-queue --client-id poc-C --json queue --device 0 --cwd /home/boop/tenstorrent/blackhole-py --timeout 900 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/operation_pocs/sfpu_math --bh-hardware --bh-device=0 --bh-core=1 --bh-timeout=10'
```

Job `5a833c0cd88440328d4af1a1bebd849b`, 10:55:55–10:55:58, **78 passed in
2.87 s** pytest time (3.22 s queue elapsed). Physical core `(1,3)`, FP32 Dst,
cfg12/28/47=0, RWC=0, L9=0/L10=1. `final-results.json` includes actual worker
firmware SHA256 hashes obtained inside this queued session, case names, exact
placement/mask/alias/mode, all raw samples and exception bit-pattern ledgers.

All seven raw samples were identical within each final case. Representative
min/median/max are therefore equal; the JSON preserves all counts explicitly.
Each case has one warmup. Main K=4 means one operation on each of four vectors;
K=64 means 16 dependent unrolled operations on each vector. Completion drain
is included, with no device-loop overhead and no control subtraction.

| Operation/mode | K | Raw min=median=max | Cycles/vector call |
|---|---:|---:|---:|
| add/sub/mul/mad single | 4 | 77 | 19.25 |
| neg/abs single | 4 | 73 | 18.25 |
| reciprocal native | 4 | 73 | 18.25 |
| reciprocal refined | 4 | 117 | 29.25 |
| exp native | 4 | 81 | 20.25 |
| exp refined | 4 | 249 | 62.25 |
| add/sub/mul/mad dependent chain | 64 | 197 | 3.078125 |
| neg/abs dependent chain | 64 | 133 | 2.078125 |

Empty record-pair overhead: 12 cycles. Matched four-interval control including
drains: 64 cycles. These large controls mean the single-call counts mainly
measure markers/completion. Repeated chains better expose instruction latency.
The historical card-1 baseline is not pooled or presented as a performance
comparison with final card-0 results.

On the same card/config/input grid x∈[-1.99,1.99], native exp costs 81 cycles
with worst relative error 0.0079692; refined exp costs 249 with worst error
2.32743e-5. Across structured boundary cases, native exp's worst was 0.01171875
at -2^-126 (output 0.98828125 versus reference 1); refined remained within its
8e-5 contract over sampled [-87,87]. Reciprocal native worst relative error
0.00537109375; refined worst 1.1175871e-7. See the JSON worst tuple for each
case: relative, absolute, ULP, input, actual, reference. These are sampled-domain
measurements, not exhaustive error proofs. Approximate and refined variants
remain separately callable: greater accuracy costs more instructions/scratch.

All default operations, fixed masks, first/last/interior independent placements,
operand aliases, short-operation repetitions, reciprocal exponent/mantissa
boundaries and exponential boundaries passed. Four exception cases preserve
guards and collect seven samples but explicitly do not count unsupported
IEEE behaviors as numerically correct. Exp/reciprocal full IEEE exceptions and
general MAD rounding stress remain gaps described in README.md.
