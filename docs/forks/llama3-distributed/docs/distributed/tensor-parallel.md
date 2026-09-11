# Llama 3.2 1B, tensor parallelism across two P150s

This is a design and theoretical model, not a measured distributed result.
Model dimensions come from this checkout's `weights/config.json` and
`examples/llama3.py`: 16 layers, hidden 2048, intermediate 8192, 32 query heads,
8 KV heads, head dimension 64, vocabulary 128256, BF16 weights, tied embeddings.
The existing measured batch-one short-context baseline is **152.3 tok/s**;
see [the local measurement report](../../decode-fusion-round2.md).

## Partitioning

Use replicated residual vectors and RMSNorm, column-parallel QKV and gate/up,
row-parallel O and down, and a vocabulary-parallel LM head. Weight shapes use
`[output, input]`, as stored by the model.

| Quantity | Rank 0 | Rank 1 |
|---|---|---|
| Q heads | 0..15 | 16..31 |
| KV heads and KV cache | 0..3 | 4..7 |
| Q projection rows | 0..1023 | 1024..2047 |
| K/V projection rows | 0..255 | 256..511 |
| O projection input columns | 0..1023 | 1024..2047 |
| Gate/up rows and intermediate features | 0..4095 | 4096..8191 |
| Down projection input columns | 0..4095 | 4096..8191 |
| LM-head rows | 0..64127 | 64128..128255 |
| Residual and norm weights | replicated | replicated |

The Q partition aligns with GQA's four query heads per KV head, so RoPE,
KV append, and attention stay local. Cache data is sharded by heads, not token
positions. There is no cross-card softmax for attention in this layout.

Each layer runs:

1. Replicated norm, local QKV, local RoPE/cache/attention.
2. Local O partial in FP32; exchange the full 2048-value partial with the other
   rank; each rank sums both partials, rounds at the chosen boundary, then adds
   the replicated residual **once**.
3. Replicated norm, local gate/up and SwiGLU.
4. Local down partial, same full-vector exchange/SUM/residual operation.

For two ranks, direct symmetric exchange of the full partial needs one phase
and each rank sends/receives one vector. Ring reduce-scatter + all-gather sends
the same total bytes but introduces two phases; start with the direct exchange.
ERISC transports bytes; Tensix performs the FP32 sum. Both sends must be able
to progress concurrently, with independent receive storage and credits.

After the final norm, each rank scores its half of the vocabulary. Exchange
one `(FP32 score, uint32 global token ID)` per rank and choose the same winner,
with a deterministic tie rule (lowest global token ID). Greedy decode avoids
a full-logit all-gather. Sampling would need another distributed algorithm.
Replicate the input embedding table, or broadcast only the selected embedding
row from its owner. Replication costs about 525.34 MB per card but avoids a
per-token embedding broadcast. The estimator assumes that replication and
excludes startup transfers; the sharded LM-head portion may share storage with
the matching half of the replicated embedding table.

## Required inference changes

The existing projection kernels partition **output rows across cores within
one chip**. Merely allocating half the weights does not implement TP. Introduce
rank-local dimensions and global head/feature offsets into weight packing,
attention/cache addressing, and launch generation. O/down must accept a
half-width input and publish an FP32 partial instead of immediately adding the
residual. Move their fused residual/scatter epilogues behind the collective.
Gate/up and attention retain their local fusion opportunities.

Add persistent ERISC staging and local NoC readiness/completion signals to the
resident execution graph, so the host does not mediate 32 collectives per token.
Treat collective failure as a failed token step: do not advance KV position or
silently continue on one rank. Define session-wide recovery before retrying
inference following partial cache updates.

TP changes the reduction order. A single-card BF16 result need not match bit
for bit, even if each shard is correct. FP32 exchange preserves partial precision
but still changes grouping. Validate layer outputs, logits and token sequences
against a TP numerical reference; report differences rather than assuming the
existing exact-BF16 test remains appropriate.

## Weight-bandwidth ceiling

Useful projection weight bytes read for one batch-one decode step:

```
W = 2 * [16 * (2048*(2048 + 2*512) + 2048*2048
                + 3*2048*8192) + 128256*2048]
  = 2,471,493,632 bytes
```

Each rank reads 1,235,746,816 projection bytes. Replicated norm weights, the
selected embedding row, KV, activation/padding/command traffic are extra.
P150 peak DRAM bandwidth is 512 GB/s per card, decimal units.

```
one-card weight-only ceiling = 512e9 / W       = 207.16 tok/s
two-card weight-only ceiling = 2 * 512e9 / W   = 414.32 tok/s
ideal two-card weight time                    = 2.414 ms/token
```

This upper bound assumes both cards simultaneously attain peak bandwidth on
half-size matrices, with no extra work. It is not a throughput forecast.

## Communication and latency

FP32 partial: `2048 * 4 = 8192` bytes. Two SUMs per layer yield **32 collectives
per token**, **262144 bytes sent and received per rank per token**, plus an
8-byte candidate exchange. Count neither both directions nor both ranks again
when calculating full-duplex serialization time.

One Ethernet tile supplies 400 Gb/s = 50 GB/s raw per direction. One passive
800G cage comprises two such tiles; our v1 stream uses one tile, so do not use
100 GB/s unless both paths are implemented and measured.

At an illustrative 80% payload efficiency, useful bandwidth is 40 GB/s and
all 32 vectors serialize in just **6.554 microseconds**. Effective collective
latency matters much more. Define `alpha` to include staging, protocol/ACK
scheduling, peer progress, reduction and synchronization overhead beyond
payload serialization; do not substitute a bare cable propagation time.

```
Tcomm = 32*(alpha + 8192 / 40e9) + (alpha + 8 / 40e9)
Ttp   = (1 / 152.3)*(1 - f + f/2) + Tcomm
```

`f` is the fraction of current time that halves with TP=2. This is an Amdahl
scenario, not a fitted measurement. If `alpha=5 us`, total modeled communication
is 171.55 us and the peak-weight-plus-communication ceiling is **386.83 tok/s**.

| Effective alpha | f=80% | f=90% | f=100%, optimistic |
|---:|---:|---:|---:|
| 1 us | 251.3 tok/s | 273.9 tok/s | 301.0 tok/s |
| 5 us | 243.2 tok/s | 264.4 tok/s | 289.5 tok/s |
| 10 us | 233.9 tok/s | 253.3 tok/s | 276.3 tok/s |
| 20 us | 217.1 tok/s | 233.8 tok/s | 253.2 tok/s |
| 50 us | 178.7 tok/s | 189.8 tok/s | 202.4 tok/s |

Thus **roughly 243–274 tok/s** is a useful *conditional target* for 80–90%
scalable work and 1–5 us collective latency. It is not established that our
firmware can meet either assumption. The baseline-derived no-overhead maximum
is 304.6 tok/s if every operation halves. Lower-utilization small GEMVs, host
round-trips, a software bitwise CRC, NoC staging, or long-context KV traffic can
erase much of the benefit. The CPU reference stop-and-wait implementation is
for correctness only and its timeout is not an estimate of device latency.

An extra link or a switch is unlikely to help this batch-one workload through
bandwidth alone: at 264 tok/s, each rank sends only about 69 MB/s of activation
partials. Optimize synchronization first. Larger batches and prefill have
different compute/communication balance; these token-rate estimates do not
apply to them. The script exposes a batch parameter at API level for byte-count
exploration only, and labels extrapolating the batch-one timing as illustrative.

Reproduce the default assumptions with `python3 -m distributed.tp`; saved output
is [tp-estimate.json](tp-estimate.json). Change `--latency-us`, `--efficiency`,
`--link-gbps`, or `--scalable-fraction` for sensitivity analysis.

Hardware bandwidth sources: [P150 specifications](https://docs.tenstorrent.com/aibs/blackhole/index.html)
and [per-tile link specification](https://github.com/tenstorrent/tt-isa-documentation/blob/main/BlackholeA0/EthernetTile/README.md).
