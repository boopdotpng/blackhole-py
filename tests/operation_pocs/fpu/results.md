# FPU hardware results

**Final selected version: 224 passed, no failures or skips**, queued job `e9be39840c454903902c7d605bb33c31`, card 0, worker index 1, physical core `(1,3)`, 2026-09-06 10:58:42–10:59:31. Pytest 47.98 s; queue job 48.34 s. All 141 FP32-Dst and 83 BF16-Dst cases retain seven measured samples after one warmup, with correctness and guards on measured kernels.

```sh
tt-device-queue --client-id poc-B --json queue --device 0 --cwd /home/boop/tenstorrent/blackhole-py --timeout 180 --env PYTHONPATH=. --env PYTHONDONTWRITEBYTECODE=1 -- '/home/boop/tenstorrent/.venv/bin/python -m pytest -q -s -x -p no:cacheprovider tests/operation_pocs/fpu --bh-hardware --bh-device=0 --bh-core=1 --bh-timeout=10'
```

`measurements.json` contains the exact queue metadata, physical coordinates, firmware/source SHA256 context, all raw samples and per-case min/median/max. Source fingerprints were checked against the final files after completion. Vendored llama3 firmware reference: `cce3e77f3a245dadfaa4a29ae3a0dda499b53708`; firmware manifest SHA256 `8d7e24525e5a0cbcabf97e70d0415c8871c9f3c899c031ddc23a03cff61a02d6`.

## Measurements

Each range below spans **case medians** for that dtype and operation, not pooled samples. `operation` includes repeated execution and completion drain; `complete` includes setup once per batch and nested profiling markers. K=16 for FP32 and K=1 for BF16. `complete/K` is amortized setup cost, not standalone per-call latency. Empty marker control is preserved without subtraction.

| Dst | Operation | Cases | Operation raw cycles | Raw/K cycles | Complete raw cycles |
|---|---|---:|---:|---:|---:|
| FP32 | elwadd | 40 | 119–120 | 7.4375–7.5 | 441–452 |
| FP32 | elwsub | 40 | 119–120 | 7.4375–7.5 | 441–452 |
| FP32 | elwmul | 20 | 215–216 | 13.4375–13.5 | 538–549 |
| FP32 | mvmul | 8 | 119–216 | 7.4375–13.5 | 441–542 |
| FP32 | gapool | 4 | 215–216 | 13.4375–13.5 | 538–542 |
| FP32 | gmpool | 4 | 119–120 | 7.4375–7.5 | 441–447 |
| FP32 | zero | 5 | 156 | 9.75 | 476 |
| FP32 | a2d | 5 | 43–58 | 2.6875–3.625 | 363–379 |
| FP32 | b2d | 5 | 59 | 3.6875 | 379 |
| FP32 | d2a | 5 | 59 | 3.6875 | 379 |
| FP32 | d2b | 5 | 59 | 3.6875 | 379 |
| BF16 | elwadd | 24 | 29 | 29 | 135 |
| BF16 | elwsub | 24 | 29 | 29 | 135 |
| BF16 | elwmul | 12 | 36 | 36 | 144 |
| BF16 | mvmul | 4 | 29–36 | 29–36 | 135–144 |
| BF16 | gapool | 2 | 36 | 36 | 144 |
| BF16 | gmpool | 2 | 29 | 29 | 135 |
| BF16 | zero | 3 | 35 | 35 | 141 |
| BF16 | a2d | 3 | 29 | 29 | 128 |
| BF16 | b2d | 3 | 29 | 29 | 129 |
| BF16 | d2a | 3 | 29 | 29 | 129 |
| BF16 | d2b | 3 | 29 | 29 | 129 |

All final control samples are 12 cycles. No timing threshold is asserted. Repeated accumulation/overwrite has dependencies and loop/Replay overhead; these numbers are not peak FPU throughput.

## Changes and retained baseline

- Preserved existing raw arithmetic/movement emitter. Recovered prior 116-case FP32 job `5666ef642d2845929f066423bb00a36a` in `baseline.json` (card0/core0). `fp32_card1.json` retains 116 passing resumed FP32 records from `c8d11effebd54507a4c62755dbe8a905` (card1/core1). Do not compare these different card/core configurations as an optimization result.
- Fixed the owned BF16 observation adapter: native BF16 Dst requires `PackCfg.DESTINATION_READ=0`; the shared helper deliberately assumed FP32 Dst even for BF16 output. Incorrect reads had made all 56 initial BF16 cases fail. No arithmetic oracle was relaxed.
- Corrected d2a/d2b FP32 input fractions so they actually exercise BF16 truncation. Added last legal A slot 7 for elementwise/moves, all four aligned A matrix pairs, and BF16 LoFi MVMUL alongside HiFi2. Dst guards cover all 64 FP32 or 128 BF16 slots through repeated observation launches.
- Intermediate fixed-observer job `05907e0b29fd42fba6d371c1f8f99e9e`, card0/core1, passed 172 cases before final coverage expansion.
- No schedule optimization was selected: the inherited minimal stationary Replay emitter remains the simple baseline. The BF16 adapter change fixes correctness, not an operation-performance claim.

## Queue recovery and limits

First-CQ timeouts occurred on stale source-bank state: resumed core0 smoke `ef1e83529ca640cc8e2ad840b1c00c7f`, card0/core1 attempt `a3325734a5044aedaa131a253ffde582`, and card1/core2 expanded attempt `0221de51f4fb433190c4022ed3b1affb`. None yielded operation evidence. The SFPU math agent coordinated card0 reset through the service (epoch 153, 10:55:37); FPU issued no resets. Final tests pass on that recovered card and a second same-card FPU run also succeeded. Queue health metadata alone does not prove clean hardware bank-credit state.

Contracts are finite exactly representable arithmetic controls and BF16 move conversion. General GMPOOL B exponent scaling, NaN/inf/subnormal/overflow and signed-zero bit policies are uncharacterized. ZEROACC invalidates rows: pack sees zero and FPU sees its identity; SFPU reads of invalid rows are unsupported. These limits are explicit in README. All assigned operations and exposed broadcasts/fidelities have passing FP32 and BF16 measurements for the stated contracts.

`history.md` preserves the earlier diagnostic record, whose pending statements refer to that earlier stage. No hardware jobs remain outstanding.
