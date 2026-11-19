# Card 1 core scaling and multicast

Card 1 is a p150a. The 140 Tensix cores include one command processor and one DMA core, leaving 138 workers. Measurements below use dispatch timestamps at 1.35 GHz and exclude checkpoint loading and compilation.

## Decode

The position-zero sweep changes only projection grids. For Llama these are QKV, attention output, gate/up, MLP down, and LM head. For the packed models the count is capped at the available 32-column output tiles. Each pair below is a median of warm complete graphs. Qwen and Nanbeige include their readout in the timed graph.

| Model | Original grids, million cycles | 138-worker projection cap, million cycles |
| --- | ---: | ---: |
| Llama 1B BF16 | 8.53 | 8.83 |
| Llama 8B BF16 | 45.96 | 46.70 |
| Llama 8B FP8 | 35.44 | 30.60 |
| Qwen3.8-27B mixed BFP | 72.39 | 75.29 |
| Nanbeige4.3-33B mixed BFP | 73.69 | 76.74 |

Llama 8B FP8 benefits most from widening QKV, O and down. At 138 workers their median spans fell from 148k, 104k and 345k to 121k, 75k and 236k cycles. Gate rose from 339k to 342k and the LM head from 2.80M to 3.06M. The worktree selects the available workers for FP8 QKV, O and down. At position 7 the mixed grid took 29.16M cycles against 34.36M for the original, over nine warm graph replays. All 128,256 BF16 logits matched at each of eight successive positions.

The existing [NoC and DRAM measurements](noc_findings.md) show 335 B/cycle with 44 readers and 350 B/cycle with 88 for Llama's NoC0 access pattern. The 1B LM head streams 525 MB of distinct weights in 1.48M cycles, about 355 B/cycle. In batch-one decode, workers own disjoint output rows. Sharing a token activation saves activation traffic, but each of those weight rows still has to arrive once. Different input shapes, bank accesses and routes produce different grid optima.

## Prefill

In the Llama and Nanbeige prompt projection a worker owns an output tile and a panel of up to 32 tokens. Workers on different token panels need the same weights. One worker per group reads the weight block and sends it down the column. Workers covering the same tokens and different output columns also share activation stripes. The weight buffer is double-buffered. Receivers reserve the next local slot and notify the sender before the sender publishes data and its completion flag.

The controlled BF16 projection uses K=N=4096, 130 workers and 32 tokens per panel. Weight multicast reads the 32 MiB matrix once per launch. Independent readers request it once per panel. The two columns keep activation multicast enabled, with identical inputs, tile math, panel layout and output placement. Each measurement is a median of seven warm launches. All output elements matched bit-for-bit.

| Prompt tokens | Independent weight reads, cycles | Multicast weights, cycles | Speedup |
| ---: | ---: | ---: | ---: |
| 64 | 248,634 | 144,088 | 1.73× |
| 160 | 920,834 | 181,968 | 5.06× |
| 320 | 1,204,167 | 264,641 | 4.55× |

Run the four combinations of activation and weight sharing with `python sims/probes/prefill_multicast.py --device 1`.

For a **complete Llama 1B prefill** with actual checkpoint weights, the same comparison took 22.38M versus 17.21M cycles for 64 tokens (1.30×), and 111.66M versus 58.66M cycles for 320 tokens (1.90×). These are seven warm replays of one chunk. The next decode step produced identical logits after both prefixes. Weight multicast was already enabled in the source checkout. These figures quantify its existing contribution.

The FP8 activation packer also requested the same 64 KiB quantization table on every worker. The worktree has one reader per worker column multicast the table into local L1. With 138 workers this reduces requested table bytes from 8.625 MiB to 0.875 MiB per launch. For 320 tokens at width 4096 the packer dropped from 456k to 435k cycles, and at width 14336 from 1.305M to 1.281M. In the complete 8B FP8 prompt graph, holding weight and activation sharing fixed, the table change reduced 64-token time from 64.49M to 62.56M cycles and 320-token time from 231.62M to 229.04M. The next-token logits matched in each comparison.

The shared projection is already used by Qwen prefill, where the host currently schedules at most one 32-token panel per chunk. Extending cross-panel weight reuse there requires a larger prompt graph that preserves the order of recurrent GDN updates and causal KV operations. Independent decode sequences are another source of weight reuse if the runner batches them.
