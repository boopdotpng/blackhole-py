# NoC output writes and DRISC DMA — Card 1, 2026-09-16

All hardware work used physical `/dev/tenstorrent/1`, serialized through queue 1.
Checkout baseline: `68d6dd7` plus existing unrelated working-tree changes.
Card 1 exposes eight DRAM banks and 117 available worker cores; `matmul_peak`
chooses a rectangular 10×11 grid for the shapes below. The remaining three of
120 hardware workers run runtime services. No Card 0 tests or resets were run.

## Retained matmul change

The output writer selected a NoC but always indexed the NoC 0 preferred DRAM
port table. It now preserves the selected NoC in S8 and indexes that NoC's table.
Both endpoint choices reach the correct DRAM bank, so this was a routing
performance problem, not a tensor-layout correctness problem. Interleaving,
write acknowledgments, TID throttling and output CB lifetime remain intact.

A/B/A/B, each with an upload/warmup and nine timed runs, default 5000×5000×5000,
split NoCs, 2×4 subblocks:

| Dtype | Original total µs | Preferred-port total µs | Original output phase µs | Preferred output phase µs |
|---|---:|---:|---:|---:|
| BF16 | 1388.18 | 1369.56 | 199.47 | 180.88 |
| FP8 | 755.36 | 737.35 | 194.48 | 176.49 |

These are means over 18 samples per variant/dtype. Total latency drops 1.34%
(BF16) / 2.38% (FP8); output phase drops 9.32% / 9.25%. All numerical validations
pass. Compute duration is essentially unchanged. FP8's original output phase
is indeed about one quarter of total time.

The output interval starts before waiting for packed output, so it includes
producer wait and cannot be interpreted as pure DRAM service time. Its final
stamp follows the nonposted TID drain. Total time includes the output tail.

Also passed: M=1025, N=769, K=513, BF16 and FP8, fixed NoC 0 / fixed NoC 1 /
split, three repeats each. These exercise partial tiles and padding.

[Raw A/B samples](matmul_writer_results.json).

## Other writer experiments

Exploratory FP8 5000³ runs, nine repeats, all successful variants numerically
validated. These are individual sweeps rather than repeated A/B confirmations:

| Variant | Mean total µs | Outcome |
|---|---:|---|
| Preferred port | 736.7 | Retained |
| Preferred port + shift/mask for 8-bank addressing | 736.3 | Within noise; not retained |
| Force port 0 / 1 / 2 on both NoCs | 766.6 / 764.2 / 757.1 | No improvement |
| Spread rows over three ports | 765.0 | No improvement |
| Spread rows over static VCs 0–3 | 835.5 | Worse |
| Dynamic request VC | 883.9 | Worse |
| One-row writer waves | 905.1 | Worse |
| Two-row writer waves | 786.8 | Worse |

Waves lower the per-core reported output phase to roughly 58 µs but move time
into the gate wait outside that interval. Total kernel latency gets worse;
judging only the output-phase number would select the wrong optimization.

The wave path initially could not compile because `NocOps.noc_coord` and
`noc_mcast_coord` referenced an undefined `noc_xy`. Replaced those two calls
with the existing packed-coordinate expression. Both wave variants then ran
and validated. This small helper repair is retained; waves remain disabled.

## All-worker write-only check

A separate test launches 16 or 117 writers, split across the two NoCs, with
16-page rings, batches of eight, one warmup and three timed iterations. It
checks every output byte after completion, starting with poisoned DRAM.
Traffic is synthetic contiguous worker shards; this is not matmul timing.
The reported rate uses the existing suite's 1.35 GHz wall-clock conversion.

| Workers | Interleaving page | Original endpoint GB/s | Preferred endpoint GB/s |
|---|---:|---:|---:|
| 16 | 2 KiB | 280.5 | 280.8 |
| 117 | 2 KiB | 316.9 | 347.8 |
| 16 | 16 KiB | 252.4 | 255.5 |
| 117 | 16 KiB | 275.1 | 284.8 |

Medians of three completion-inclusive samples. Eight cases passed. The 2 KiB
all-worker case improves about 9.8%, consistent with reducing a routing
hotspot. This does not establish an optimal topology or justify changing
matmul's tile layout. Larger packets alone did not improve this experiment.

## DRISC GDDR DMA

Added a standalone scalar DRISC launch harness and 128 passing cases:

- Eight banks, DMA streams 0 and 1 tested independently.
- AXI burst setting 16 and 255.
- 16-byte and 2 KiB transfers at queue depth one; 2 KiB and 16 KiB at depth four.
- 32 repeated read batches, then 32 write batches; full completion inside each
  timed direction, before stage reuse.
- Full staged payload, source, destination and adjacent guard checks.
- Exact global DMA attribute restoration checked; both NIU modes unchanged.
- DRISC L1, reset PC and reset state restored by the host harness.

Uses each bank's NoC 1 preferred DRISC; the NoC 0 preferred endpoint is reserved
for system telemetry firmware. The harness refuses to take over a running
DRISC. No stream-mode NIU switch is required for these bank-local transfers.
The code reuses scalar assembler encoding, not the worker firmware launch ABI.
Polling has a device-side bound and an explicit error result.

Median direction timings across banks, streams and burst settings:

| Transfer / depth | Bytes per direction | Read cycles | Write cycles |
|---|---:|---:|---:|
| 2 KiB / 1 | 65,536 | 7,309 | 3,998 |
| 2 KiB / 4 | 262,144 | 11,628.5 | 7,937 |
| 16 KiB / 4 | 2,097,152 | 50,187.5 | 46,400 |

This establishes working GDDR ↔ DRISC L1 DMA and shows the value of amortizing
issue/completion overhead. Burst 255 provides no clear benefit for the large
case. These timings include scalar issue loops and polling; they do not measure
CPU utilization, concurrent streams, simultaneous banks, or an end-to-end
Tensix → DRISC → GDDR pipeline. The same addresses are reused between completed
batches. [Raw DMA results](drisc_dma_results.json).

During bring-up, a scratch-register alias in the first emitter incorrectly
programmed DMA attributes. Fixed before the passing measurements and reset
only Card 1 through the queue. The final tests use explicit safe scratch
registers, bounded polls and attribute readback.

## Overlay engine: where it fits

Source review, **not an overlay hardware transport test**. The Blackhole
[register map](../../../tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_overlay_parameters.h)
provides local-source messages, remote stream destinations, credit/buffer
tracking and automatic phase configuration/advance. This can remove repeated
RISC issue and buffer bookkeeping in a persistent producer/consumer pipeline.

Useful candidates:

1. L1-to-L1 pipelines between operations, avoiding a DRAM round trip entirely.
2. Multicast of a reused block, with hardware receiver credits, so a RISC does
   not manage every message/receiver handoff.
3. Long bank-local or explicitly sharded streams whose destination and physical
   page order remain stable across many messages.

The existing mapping is `bank = tile % banks`, bank offset
`(tile // banks) * 2048`. Output CB order also follows compute subblocks rather
than one contiguous bank-local range. A single fixed-endpoint FIFO stream
cannot implement that mapping unchanged. Per-bank streams, descriptor/phase
programming, or staging/reordering could implement it, but their cost and
stream resources must be measured. Interleaving is not a fundamental ban on
using overlays; it prevents treating this writer as a simple stream replacement.
Do not infer autonomous DRAM interleaving from DRAM-named overlay scratch fields.

Similarly, replacing direct writes with Tensix → DRISC L1 → DMA does not remove
the NoC payload. It adds staging and ownership/credit handoffs. It might help
if bank-side aggregation turns many small writes into long local DMA bursts,
or if it enables overlap with useful compute. The measurements here do not
establish such a win. Switching a DRISC NIU to stream mode also changes its
incoming address semantics; other direct DRAM traffic must use an endpoint
still in NOC2AXI mode. See the local
[mode contract](../../../tt-metal/tt_metal/hw/inc/experimental/drisc_mode.h) and
[DMA API](../../../tt-metal/tt_metal/hw/inc/experimental/gddr_dma.h).

The next useful architectural experiment would be an explicit bank-owned output
layout with matched downstream consumers, followed by a bounded DRISC staging
ring comparison. Keep direct preferred-port writes as the baseline and measure
receiver/DRAM completion, total kernel latency, staging space, and RISC work.

## Reproduction

From `blackhole-py` (the queue tool is installed in `~/.local/bin`):

```sh
~/.local/bin/tt-device-queue run --device 1 --cwd "$PWD" -- '../.venv/bin/python tests/movement/bench_matmul_writer.py --device 1 --dtype bf16 fp8 --json /tmp/matmul_writer_ab.json'
~/.local/bin/tt-device-queue run --device 1 --cwd "$PWD" -- '../.venv/bin/python -m pytest tests/movement/test_drisc_dma.py tests/movement/test_noc_output.py --bh-hardware --bh-device=1 -q -s'
```

`bench_matmul_writer.py --variants` exposes the exploratory variants above.
Every matmul variant runs normal numerical validation. No performance threshold
is asserted in tests. Raw queue jobs: A/B `e0aa0b5189f54bc78cb9c3c51e1a9878`,
DMA `86bc826c97e643bab7712aa662c601eb`, all-worker
`d6365bb3abd44f52bd46eec158f810d6`, irregular-shape regression
`4b0a03fef67e482b84918a23c83d5f34`.
