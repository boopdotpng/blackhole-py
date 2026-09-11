# Transport continuation evidence

Final result: **24 full-sweep tests passed in 87.66 seconds**, covering 2,564
operation/format/placement/length cases with seven measured samples each, plus
**8 signed/rounding-edge tests passed in 1.03 seconds**. Existing code was
preserved and continued. No shared code was modified.

Final full-sweep job `382d3483697443dcb631d13902993dd1`: queue/card1, worker9,
physical `(1, 11)`, 2026-09-06 11:01:19, timeout240, exit0, no skips. Command:
```
/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/operation_pocs/transport --bh-hardware --bh-device=1 --bh-core=9 --bh-timeout=10
```
Environment: `PYTHONPATH=.`, `PYTHONDONTWRITEBYTECODE=1`, `TRANSPORT_DEVICE=1`.
`TRANSPORT_LENGTHS` was unset: every N=1..128 ran for all partial cases; aligned
A-pair controls use N=256. Both queues were healthy/live/empty; alternated to1.
`final-sweep.json` retains 6,924 raw timing/control/staging records. K=1, one warmup
per case, seven measured samples, no subtraction. Code was frozen throughout.

Final edge job `98175c3efcce4918b2dd7c4cd6c06006`: queue/card1, worker11,
physical `(2, 3)`, exit0, 8 passed/no skips; same environment, timeout120. Command:
```
/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/operation_pocs/transport/test_edges.py --bh-hardware --bh-device=1 --bh-core=11 --bh-timeout=10
```
`final-edges.json` retains seven samples plus controls per case. These tests were
added after the full sweep; emitters were unchanged. They cover signed normals,
signed zero, smallest normal magnitude and both signs/parities of BF16 ties.
FP32 pack/Dst preserve signed zero; BF16 pack canonicalizes it and rounds halfway
magnitude away from zero. Source observation canonicalizes signed zero; NaN/inf/
subnormal behavior is outside this measured contract.

Every operation includes required configuration/drain. Source additionally includes
exact input staging and zero fill; pack includes exact final copy from its padded
scratch page. Nested staging/copy markers contribute overhead to complete timings.
Empty controls are retained; no corrected timing or throughput claim is made.

`queue-evidence.json` retains exact commands/statuses for every continuation job,
including diagnostics and failed candidates. No timeout is counted as a pass.

## Recovered historical baseline

Job `75dbe5c15968431d9574215ef337e269`, card/queue 1, worker index 0, physical
core `(1, 2)`, 2026-09-06 10:41:50: **6 passed in 1.17s**, queue exit 0.
The log contains N=1,17,128 for BF16 and FP32 output at Dst slots 0,31,63.
`baseline-pack.json` retains all 36 operation/control records and seven raw
samples per case. Null device and placeholder job fields in the original output
were resolved from queue metadata, not inferred from hardware behavior.

Command:
```
/home/boop/tenstorrent/.venv/bin/python -m pytest -x -q -s -p no:cacheprovider tests/operation_pocs/transport/test_transport.py --bh-hardware --bh-device=1 --bh-core=0 --bh-timeout=10
```
This is inherited baseline evidence, not proof of the final instrumented version.
The exact-pack implementation, all-Dst preservation, and immediate output guards
passed those selected lengths. It does not establish the full N sweep.

## Inherited failures

- `0c90d7b39e7d4ec1a89b4ccfef05577c`: source, card0/core0, first BF16 A slot0 case,
  CQ completion 1 timeout; 1 failed, no cycle samples.
- `64a954a390994bf29fe24c1b0c9ed1d5`: Dst, card1/core0, first BF16 slot0 case,
  CQ completion 1 timeout; 1 failed, no cycle samples.

## Fresh continuation

Job `fff325e81fcb480c8d67f03ed39b9733`, queue/card1, worker0, timeout 90 seconds,
`TRANSPORT_LENGTHS=1,128`, `PYTHONPATH=.`, `PYTHONDONTWRITEBYTECODE=1`. Exact command
matches the baseline above. Both queues were healthy/live and empty before
submission; chose card1 on tie. **1 failed in 10.66s**, queue exit1, first launch
CQ completion1 timeout. This unchanged baseline emitted no measured samples.
Coordinator notified; no direct reset or bypass of the service was performed.

CPU verification: final 32 tests collected without hardware; all 24 full-sweep image configurations
assembled, and profiler labels validated. Collection/assembly is not a hardware
pass. Added separate staging/zero-fill and exact final-copy sections while retaining
complete-operation intervals. These changes were subsequently verified by the final full-sweep job above.

Firmware/runtime context is the existing dirty checkout. Hardware firmware
identification was not obtained before timeout. Queue metadata reported both
workers live, device0 reset epoch152 and device1 reset epoch19. That metadata does
not establish functional firmware health. Later successful evidence is recorded
above; no speedup claim is made from the baseline/candidate instrumentation change.


## Debugging and continuation conclusions

Fresh-core pack smoke `7a4698097ffe43f4839c27f190617cd3` passed6 on card0/core1;
`candidate-pack-smoke.json` retains the seven samples. Reusing core1 on card0 in
`8385258dd6414023a2529fa711bcf3fc` timed out CQ1 after another agent's process.
Full pack `e0fa95b4cc634ec8ba5341fde96c3613` passed6 on card1/core2 for all128
lengths, retained in `final-pack-sweep.json`. Other agents reproduced the
cross-process core reuse issue and coordinated a card0 service reset. Transport
performed no reset. Final full sweep used card1/core9 and required no recovery.

Source/Dst smoke `6f7c2f87e5364d888c513457af9d87e9` stalled. Diagnostic jobs
`5a1554ecc8e04f2a8408b5a2e3babb7a`, `30ba14b424ad47e7bf807808703e7aed`,
`e357e578b8ed43efa7c551d27eadeae8`, `e02b7b6ad3024e578115a73011bdd0ab`
localized missing unpack-sync acknowledgement and observation releases; corrected
diagnostic `b60aae1fdc6a4878b533a13708fa70e9` completed. Diagnostic markers and
script were removed before final testing. Subsequent correctness failures
`014e067c60774866b1ca4a1359cebfd2`, `65f61544fff34a5494503c240bb33f6b`,
`2b26356c6b2c459cb35ded8e57098540` exposed whole-bank observation addressing and
UNPACR_NOP clearing the supposedly preserved other bank. Explicit observation
addresses and publication in the initial seeded UNPACR fixed these. Source/Dst
smoke `cd22ce711abd45669b34988da1c3efe0` then passed18 on card0/core8.

Edge candidate jobs `1cd2e325648f4f13be3179026125ab9d`,
`71f4b06df2bc46d7a798ea1e9260828b`, `fe3399cf43c848229a5ebba57e5f4c3e`
identified signed-zero and tie semantics; final oracles now describe that hardware
behavior explicitly, without changing the emitters or the requested format paths.

No optimized copy candidate was selected. Scalar exact staging/copy is the
correctness baseline; costs below expose its long-prefix overhead. Historical
baseline and newly instrumented pack differ in nested marker overhead and were
measured on different cores, so they are retained separately without a speedup
claim. Kernel firmware is the existing frozen `fw/llama3` implementation built by
`fw/build.py`; `code-costs.json` records primitive assembled sizes. Device/core
coordinates were printed inside queued execution. Firmware source hashes are
retained in `firmware-context.json` (host source identity, not device telemetry).

## Representative final raw cycles

Card1/core9 physical `(1, 11)`, slot0, K=1; min/median/max from seven samples.
Full placement/length distributions and nested costs remain in `final-sweep.json`.

| Operation | Input/output format | N | min | median | max |
|---|---|---:|---:|---:|---:|
| unpack Dst SFPU | BF16 | 1 | 2300 | 2300 | 2301 |
| unpack Dst SFPU | BF16 | 128 | 4067 | 4067 | 4068 |
| unpack Dst SFPU | FP32 | 1 | 2301 | 2301 | 2302 |
| unpack Dst SFPU | FP32 | 128 | 5089 | 5089 | 5090 |
| SRCA | BF16 | 1 | 690 | 690 | 691 |
| SRCA | BF16 | 128 | 4247 | 4247 | 4248 |
| SRCB | BF16 | 1 | 687 | 687 | 689 |
| SRCB | BF16 | 128 | 4244 | 4244 | 4245 |
| SRCA | BF16 | 256 | 8153 | 8153 | 8154 |
| SRCA | FP32 | 1 | 1041 | 1041 | 1042 |
| SRCA | FP32 | 128 | 8154 | 8154 | 8155 |
| SRCB | FP32 | 1 | 1038 | 1038 | 1040 |
| SRCB | FP32 | 128 | 8151 | 8151 | 8152 |
| SRCA | FP32 | 256 | 15964 | 15967 | 15967 |
| pack exact | BF16 | 1 | 2588 | 2600 | 2630 |
| pack exact | BF16 | 128 | 6142 | 6144 | 6163 |
| pack exact | FP32 | 1 | 2617 | 2627 | 2638 |
| pack exact | FP32 | 128 | 9737 | 9746 | 9759 |
