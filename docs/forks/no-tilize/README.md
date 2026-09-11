# blackhole-py

Run Llama 3.2 1B Instruct end-to-end decode:

```sh
PYTHONPATH=. python3 examples/llama3.py \
  --safetensor weights/model.safetensors \
  --tokenizer weights \
  --device 1 \
  --prompt "hello"
```

Add `--profile` to print startup preparation/staging/DRAM-upload time and the
generated-token device/CQ versus host-loop breakdown.

The decoder consumes original row-major BF16 checkpoint weights without host
tilization, weight padding, or a prepacked device copy. It preserves the existing
kernel schedule and streams each projection weight once. Card 1 measurements
remain within about **0.5%** of the previous tilized version. See the
[row-major weight results and numerical limits](decode-no-tilize.md).

Earlier optimization measurements are in [decode performance](decode-performance.md)
and the [kernel bottleneck analysis](decode-bottlenecks.md).

Run the fixed-length decode benchmark (startup and prompt ingestion excluded):

```sh
PYTHONPATH=. python3 examples/benchmark_llama3.py --device 1 --steps 64
```

Pass `--reference /path/to/original/llama3.py` to compare token IDs and sampled
BF16 logits on the same card, and `--output result.json` to retain the measurements.
Raw-page reductions change floating-point summation order, so exact logit hashes
are not expected to match a tilized reference. The benchmark supports
`--logit-rms-tolerance` and `--teacher-force-reference` for numerical comparisons
with identical token histories; see [validation commands](decode-no-tilize.md#reproduce).

## Requirements

- `tt-kmd` > 2.9.0
- P100A with 120 Tensix cores, or P150A/P150B/P150C with either the stock
  120-core firmware topology or a restored 140-core topology

P150 uses all eight DRAM banks; P100A uses its seven enabled banks.
