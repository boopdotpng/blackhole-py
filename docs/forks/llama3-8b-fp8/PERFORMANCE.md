# Llama 3 8B FP8 on card 1

Measured September 7, 2026, on the P150A with eight DRAM banks and 117 available
application workers. This separate repository uses the calibrated Neural Magic /
Red Hat AI FP8 checkpoint and mixed precision described in [README.md](README.md).

## Throughput

Final measurements are in `validation/published-fp8-final.json`; the fresh BF16
control is `validation/bf16-benchmark.json`. Aggregates and source hashes are in
`validation/fp8-summary.json`.

| Generated tokens per prompt | BF16 | Published FP8 | Speedup |
| --- | ---: | ---: | ---: |
| 64 | 29.38 tok/s | **47.72 tok/s** | 1.62× |
| 256 | 29.01 tok/s | **46.74 tok/s** | 1.61× |
| 512 | Not remeasured | **45.51 tok/s** | — |

Reserved device DRAM falls from **17.14 GB to 10.16 GB** (41% less).
The final FP8 startup took 30.27 seconds, including 28.11 seconds preparing,
staging and uploading weights. These figures exclude the one-time download.

All rates use batch-one greedy decode, four fixed prompts, and wall-clock token
timing. Startup, prompt ingestion and diagnostic logit readbacks are excluded.
Generation deliberately continues through EOS to hold work constant; assistant
markers and repeated conversation after EOS in benchmark transcripts are not the
normal stopping behavior of `examples/llama3.py`. The 512-token run ends at roughly
540 cached tokens depending on the prompt; it does not validate the full 8K cache.

BF16 uses the original 88 projection workers and NoC split x=7. FP8 uses 96
projection workers, 32 attention workers, NoC split x=10, and one math fidelity
phase. Worker and NoC sweeps preserved exact sampled logits across candidates;
see `published-fp8-worker-tuning.json` and `published-fp8-noc-tuning.json`.

Both runtimes use **163 launches per token**, five per layer plus three outside
the layers. The sibling 1B runtime uses the same fusion structure with 16 layers
and 83 launches. The speedup here comes primarily from FP8 projection operands,
not a reduction in launch count.

## Correctness and limits

- Nine CPU tests pass, including E4M3 rounding against PyTorch, tiling,
  checkpoint scale rejection, and kernel/parameter-template residency across
  18 combinations of topology, attention worker count and checkpoint mode.
- A card 1 projection probe compares native FP8 arithmetic with CPU-quantized
  operands using non-power-of-two scales from the published checkpoint.
- A 256-token teacher-forced sequence samples 11 complete vocabulary logit
  vectors, including both sides of 32-token attention block boundaries.
- Against CPU emulation of the same published FP8 checkpoint, all **11/11**
  greedy choices match. Logit Pearson correlation ranges **0.99294–0.99976**.
  The CPU emulation uses FP32 GEMM for decoded FP8 operands, BF16 surrounding
  operations, and the same native-subnormal flush contract; it is not a vLLM run.
- Against the unquantized BF16 device reference, **10/11** greedy choices match.
  Correlation ranges **0.84577–0.99974**. The largest deviation also appears in
  the CPU quantized model (0.815 at position 64), so the published static
  quantization is not numerically equivalent to BF16.

These checks validate the tested implementation and workloads. They are not
perplexity, MMLU, long-context or broad model-quality evaluations, and do not
establish bit-for-bit equality with the publisher's inference backend.
`validation/published-fp8-accuracy.json` records both comparisons.

The embeddings and LM head, plus two sampled normalization weights, are
byte-identical between the local BF16 model and published checkpoint;
`validation/checkpoint-comparison.json` records their SHA-256 checksums.

## Earlier experiments

`validation/fp8-benchmark.json` used locally converted weights, FP8 attention and
FP8 intermediates. It reached about 49–50 tok/s but had worse logit agreement.
`fp8-v2-benchmark.json` retained BF16 embeddings and normalization weights and
still had substantial drift. Neither is the final default. The calibrated mixed
checkpoint is used for the results above.

Other inherited validation files describe the earlier BF16 8B repository or its
1B ancestor. Use the explicitly named files above for this FP8 implementation.
