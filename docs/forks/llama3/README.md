# blackhole-py

Run Llama 3.2 1B Instruct end-to-end decode:

```sh
PYTHONPATH=. python3 examples/llama3.py \
  --safetensor weights/model.safetensors \
  --tokenizer weights \
  --device 0 \
  --prompt "hello"
```

Add `--profile` to print startup preparation/staging/DRAM-upload time and the
generated-token device/CQ versus host-loop breakdown.

Decode optimizations now reach **153 tok/s with 83 launches per token** on the
tested P150A, up from 139 tok/s and 212 launches before the fusion work. The
default uses 16 attention workers and preserves the reference BF16 results.
See [RISC-V optimizations and the 200 tok/s budget](decode-riscv-round3.md),
[fusion measurements and validation](decode-fusion-round2.md),
[earlier measurements](decode-performance.md), and the
[previous bottleneck analysis](decode-bottlenecks.md).

Run the fixed-length decode benchmark (startup and prompt ingestion excluded):

```sh
PYTHONPATH=. python3 examples/benchmark_llama3.py --device 0 --steps 64
```

Pass `--reference /path/to/original/llama3.py` to compare token IDs and sampled
BF16 logits on the same card, and `--output result.json` to retain the measurements.

## Requirements

- `tt-kmd` > 2.9.0
- P100A with 120 Tensix cores, or P150A/P150B/P150C with either the stock
  120-core firmware topology or a restored 140-core topology

P150 uses all eight DRAM banks; P100A uses its seven enabled banks.

Model weights now upload in row-major order without host tilization. See
[layout contract and validation](ROW_MAJOR_WEIGHTS.md).
