# FPU queued hardware evidence

Work resumed from existing emitters and tests on 2026-09-06. No prior README/results existed. The queue retained a successful FP32 baseline, recovered verbatim into `baseline.json` with job/card/core annotations. This is historical evidence, not a claim that the final edited tests have passed.

## Recovered baseline

Job `5666ef642d2845929f066423bb00a36a`, physical card 0, worker index 0, 2026-09-06 10:41:54 to 10:42:00 (queue timestamp). Exit 0, **116 passed**, no skips, pytest time 4.77 seconds. Command:

```sh
/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/fpu --bh-hardware --bh-device=0 --bh-core=0 --bh-timeout=10
```

Submitted under client poc-B, cwd `/home/boop/tenstorrent/blackhole-py`, timeout 900. The log identifies these as BF16-source/FP32-Dst cases. Firmware revision/core coordinate were not printed by the prior job and cannot be reconstructed as measured facts. Public model modes LoFi/HiFi2, normal/column/row/scalar broadcasts are covered.

The table gives ranges across **case medians**, not pooled samples. Every raw sample and per-case min/median/max is in `baseline.json`. K=16, one warmup, seven retained samples. No control subtraction.

| Operation | Cases | Operation median raw cycles | Raw/K cycles | Complete median raw cycles |
|---|---:|---:|---:|---:|
| elwadd | 32 | 119–120 | 7.4375–7.5 | 439–446 |
| elwsub | 32 | 119–120 | 7.4375–7.5 | 440–447 |
| elwmul | 16 | 215–216 | 13.4375–13.5 | 537–541 |
| mvmul | 8 | 119–216 | 7.4375–13.5 | 440–541 |
| gapool | 4 | 215–216 | 13.4375–13.5 | 536–541 |
| gmpool | 4 | 119–120 | 7.4375–7.5 | 439–446 |
| zero | 4 | 156 | 9.75 | 475 |
| a2d | 4 | 43–58 | 2.6875–3.625 | 361–377 |
| b2d | 4 | 59 | 3.6875 | 378 |
| d2a | 4 | 59 | 3.6875 | 377–378 |
| d2b | 4 | 59 | 3.6875 | 377–378 |

Control is 12 raw cycles in every baseline sample. Complete includes configuration once per batch plus nested profiling overhead; dividing by K amortizes that setup. The dependent-loop numbers are not peak throughput. No alternative schedule is selected: preserve the simple prior emitter until a same-card candidate has correctness and repeated measurements.

## Resumed verification and outstanding work

Job `ef1e83529ca640cc8e2ad840b1c00c7f`, card 1/core 0, 2026-09-06 10:49:06–10:49:17: exit 1, **1 failed, 112 deselected**, no skips. First warmup launch hit `TimeoutError: CQ completion 1 timed out`; no cycle sample or numerical comparison was reached. Both queues reported healthy live workers before submission.

```sh
tt-device-queue --client-id poc-B --json queue --device 1 --cwd /home/boop/tenstorrent/blackhole-py --timeout 90 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/fpu/test_fpu.py -k a2d --bh-hardware --bh-device=1 --bh-core=0 --bh-timeout=10'
```

The prior BF16 a2d job `b3e725befbcb4428944f57d7473346d2` likewise failed its first CQ launch on card 1/core 0. This does not establish a BF16 hardware limitation; the common launch issue must be resolved before diagnosing BF16 arithmetic or transport. No device resets were issued by this agent.

Since the baseline, d2a/d2b input fractions were changed to genuinely require FP32-to-BF16 truncation. Per-result physical card, core index and coordinate metadata were added. These final changes require queued hardware revalidation. BF16 tests have no passing retained evidence yet; neither collection nor a timeout is counted as completion.

## Additional resumed jobs

- `bbe676b13bf747e185f25f884235ad60`, card0/core1: one BF16 numerical failure, confirming launch works on core1.
- `c8d11effebd54507a4c62755dbe8a905`, card1/core1: **116 FP32 passed, 56 BF16 failed**, no skips; 21.66 seconds pytest, 22.0 seconds job. All final FP32 narrowing checks passed; raw records retained in `fp32_card1.json`. Command was `/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -p no:cacheprovider tests/operation_pocs/fpu/test_fpu.py tests/operation_pocs/fpu/test_bf16.py --bh-hardware --bh-device=1 --bh-core=1 --bh-timeout=10`, queue timeout180, normal poc-B cwd/env.
- BF16 failure diagnosis: the copied shared pack fixture reads **FP32 Dst** even when its output format is BF16. The owned adapter now writes `PackCfg.DESTINATION_READ=0` for native BF16 observation (1 for FP32); this corrects the physical read width instead of weakening the oracle.
- `a3325734a5044aedaa131a253ffde582`, card0/core1, same full-suite command as bbe with -x: first launch CQ timeout, 1 failed. Peers traced stale source-unpack credit to a separate runtime fixture; the math agent subsequently coordinated card0 reset through the service. No successful evidence is inferred from this attempt.

Final queued validation of native BF16 observer fix is pending. `conftest.py` now prints physical topology and SHA256 context for actual measured source versions, including the vendored firmware manifest.
