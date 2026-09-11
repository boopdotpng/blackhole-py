# Two-card implementation and measurements

## Layout

Each of 32 layers is split across both cards. Q/K/V and gate/up are split by
output rows: each rank has 16 query heads, 4 KV heads, and 7,168 MLP channels.
O/down are split by input columns. Their FP32 partial output vectors are summed
across ranks, packed to BF16, and added to the BF16 residual once per rank.
The embedding, normalization scales and final vocabulary projection are
replicated; only rank 0 executes the final projection and argmax.

The published calibrated FP8 bytes and scales are retained. All 224 split
matrices reconstruct byte-for-byte; 515 other tensors/scales are replicated.
Each rank uploads about 5.59 GB of checkpoint tensor payload, including the
replicated embedding/head. See `validation/tp2-checkpoint-verification.json`.

Both devices launch from the host. They replay resident traces, synchronize at
each O/down output, and perform reduction on Tensix cores. There are 226 launches
on rank 0 and 224 on rank 1 per token. The host handles embedding upload, trace
submission, and the selected token; it does not relay collective payloads.

## Inter-card path

```
Tensix FP32 partials -> local ERISC L1 -> cable -> peer ERISC L1
                                      -> Tensix FP32 SUM -> BF16 residual
```

The path uses endpoint 9 on each card, with reciprocal firmware board identities
verified before starting E1. Endpoint 11 is also trained but isn't used for the
model. Each Ethernet tile's E0 keeps the stock trained link alive; E1 runs the
freestanding C in `fw/erisc/collective.c`. The existing hardware TT-link queue 1
provides packet sequence checking and retransmission.

One vector is 4,096 FP32 values = **16 KiB**. Send and receive slots occupy
32 KiB total, at L1 addresses `0x50000` and `0x54000`. Each exchange sends four
4 KiB payload packets and generation-tagged ready/credit markers. Producer and
consumer flags prevent stale reads and overwriting live slots. The current
service waits for each packet's acknowledgment before sending the next packet.
There are 64 exchanges/token: 1 MiB of activation payload per direction/token.

**No inter-card activation staging uses DRAM.** The inherited single-card
kernels still keep their *local* activations and KV cache in DRAM. Removing that
local storage would require a separate kernel-fusion change.

Ethernet L1 is **512 KiB**, whereas the 1.5 MiB number applies to Tensix L1.
Stock Ethernet firmware also reserves the upper 64 KiB. Even so, batch-one 8B
partials fit comfortably. In general, vector bytes are
`batch * token_chunk * hidden_width * bytes_per_element`; prefill chunks or
batches can exceed a slot without requiring a giant parameter count. Larger
payloads can be streamed through bounded L1 slots with credits. This prototype
is explicitly fixed to batch-one, hidden-width 4,096 and TP=2.

`distributed/runtime.py` retains the slower host-mediated transport as a debug
reference (`--transport host`). Its CPU rounding is idealized; it is not a
bit-exact emulator of Tensix pack/residual arithmetic.

## Why scaling is 1.38×

Measured launch attribution at context 64 (milliseconds/token). Device markers
add a little overhead and include dispatch costs; these are full-trace stage
measurements, not standalone wire latency.

| Stage | One card | Two-card critical rank |
|---|---:|---:|
| QKV projection + norm | 2.30 | 1.47 |
| Attention + RoPE/KV handling | 1.54 | 1.56 |
| O projection | 1.67 | 1.16 |
| Gate/up + norm + SwiGLU | 8.31 | 4.47 |
| Down projection | 5.03 | 2.52 |
| New reductions, including peer wait | — | 1.81 |
| Vocabulary head + argmax | 2.27 | 2.27 |

MLP time nearly halves. Attention does not speed up with half as many heads and
half as many workers; its per-head and launch costs remain. The unsharded output
head leaves card 1 idle for roughly 2.2 ms/token. Smaller projections retain
fixed costs, and collectives add synchronization latency.

Projection kernels use 96 workers/card, attention uses 16, and reduction uses
32. Attention needs a different work decomposition to use the remaining cores
to shorten each head's execution; simply assigning half the heads to each card
leaves approximately the same work per participating attention worker.

E1 timestamps measure about 1.43 ms/token for rank 0's exchange intervals
(including waiting for peer readiness), plus 0.77 ms for consumer/credit waits.
These overlap Tensix intervals and must **not** be added to the table as another
independent cost. Raw timings are in `validation/tp2-profile.json`.

This is not a measured hardware compute-utilization percentage. We have stage
wall times and board power, not arithmetic occupancy or DRAM-controller counters.
The data supports optimizing fixed/serial work before concluding the model must
be larger. A larger width would increase sharded matrix work faster than vector
bytes, but model depth alone also increases the number of collectives. Batching
would change the compute/memory balance and requires additional implementation.

Next performance work: shard the vocabulary head with a global argmax; profile
attention's fixed work; pipeline packet submission safely; overlap/merge
projection and reduction launches. Correctness takes priority over those changes.

## Validation and limits

The three-prompt, 64-generated-token matched-history test compares the same
input token at every position, including the context-32 and context-64 cache
boundaries. Result: 250/250 greedy choices match, minimum sampled PCC 0.99296,
maximum relative RMS 0.12350. This **fails** the strict 0.05 RMS target. FP32
partials remain FP32 through the SUM; ordinary SrcA/SrcB unpack would silently
reduce precision, so the reduction loads Dst directly. Remaining numerical
agreement requires further investigation. Do not infer broad task accuracy
from greedy matches on three short histories.

CPU suite: 20 tests run, one hardware-gated inherited test skipped. Checkpoint
reconstruction, rank shapes, FP8 byte preservation, kernel lowering and local L1
bounds are covered. Real hardware checks include reciprocal link identity, E1
start/restore, exact bidirectional transfers from 16 B through 16 KiB, direct
Tensix-to-ERISC producer flags/payloads, and complete two-card model runs.

Earlier failed/debug runs are retained under `validation/tp2-debug/`; they are
not current validation claims. Source-repository validation predates this fork.

After a kernel timeout, outstanding NoC/dispatch work may survive ordinary
core reset. Stop the failing process and recover both devices before running
another model; a normal successful exit restores the temporary E1 state.

## Power

Final sustained run: 1,024 generated tokens after 66 warmup tokens, both runs
starting from the same two tokens. Single-card decode averages **42.99 tok/s**;
TP=2 averages **57.43 tok/s (1.34×)** as context grows. These are separate from
the short-context matched-history 47.9→66.0 tok/s measurements.

| Run | Card 0 mean / sampled peak | Card 1 mean / sampled peak | Combined mean |
|---|---:|---:|---:|
| Single-card, card 1 active | 93.6 / 102 W (idle) | 255.3 / 288 W | 348.8 W |
| TP=2 | 240.1 / 293 W | 229.0 / 286 W | 469.1 W |

TP=2 uses **8.17 J/token** across both boards (4.18 on card 0, 3.99 on card 1),
or about 8.36 kJ over the measured 17.83 seconds. The active single card uses
**5.94 J/token**; including its unused second board gives 8.11 J/token. Thus
the two-card run improves latency/throughput but does not improve energy per
token compared with operating only one active board.

`scripts/benchmark_power_tp2.py` samples both cards through the local tt-smi
backend in a separate process. `INPUT_POWER` is total board input watts; `TDP`
is ASIC watts. The installed CLI predates board-input display support, so the
sampler imports `../tt-smi` with the parent's Python environment.

UMD initially opens devices with a power request even for telemetry. The sampler
clears **only its own file descriptors'** KMD power votes after discovery. KMD
ORs votes across clients, so inference keeps its requested state while the idle
second board remains at its natural idle draw. The initial measurements made
without this correction are archived, not used as the final power comparison.

The report separates loading, 66 warmup tokens, and continuous generation.
Per-card mean watts are time-weighted, peaks are sampled maxima at 10 Hz, and
joules are integrated with interpolation at phase boundaries. The two cards are
read sequentially within each sample. Total-board readings include board idle
draw but exclude the host CPU and other system components. In the one-card run,
the combined figure includes the idle second board; compare the active card
alone when evaluating one-board energy efficiency. Fixed-count generation
continues after EOS to provide a sustained load, not a conversational output.

See `validation/tp2-power.json`, its `.jsonl` raw samples, and `.phases.json`.
