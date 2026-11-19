# blackhole-py

Write kernels in TTRV, run them on a Tenstorrent Blackhole card from Python, CUDA style.

```python
import numpy as np
from ttrv import Device, Var

d = Device(0)                                      # open card 0; it closes at exit
x = d.array(np.ones(1024, np.float32))             # DRAM buffer, filled from the host
y = d.empty(1024, "fp32")
scale = d.kernel("scale.ttrv", N=1024)             # compile with N defined, install
scale(x=x, y=y, k=2)                               # queued; returns at once
print(y.numpy())                                   # waits for the device, copies back

k = Var("k")
with d.graph() as g:                               # launches are recorded, not run
  scale(x=x, y=y, k=k)
g(k=3).wait()                                      # replay with k bound to 3
```

`d.array` also takes safetensors tensors (`helpers.safe_load`), so a checkpoint goes to the card as stored.

## Requirements

- `tt-kmd` >= 2.12.0 (`smi.py` reads telemetry with the `NOC_READ` ioctl, added in 2.12.0)
- Python with `numpy` and `tiktoken`
- `clang` and `llvm-objcopy`

## Inference throughput

Batch-one greedy inference on one Blackhole p150a (card 0, 138 workers). Higher is faster.

| Model | Weights | Prefill (tok/s) | Decode (tok/s) |
| --- | --- | ---: | ---: |
| Llama 3.2 1B | BF16 | 7,368 | 161.6 |
| Llama 3 8B | BF16 | 2,020 | 29.9 |
| Llama 3 8B | FP8 | 1,882 | 45.8 |
| Qwen3.8-27B | Mixed BFP | 130 | 11.4 |
| Nanbeige4.3-33B | Mixed BFP | 1,004 | 18.2 |

Each rate is the median of three warm runs on the same fixed token IDs. Prefill measures KV-cache construction for 320 prefix tokens, in one chunk for Llama and Nanbeige and ten 32-token chunks for Qwen. Decode measures the next 32 streamed tokens after the first output. Timings exclude checkpoint loading, compilation, and graph capture. Mixed BFP uses BFP8_B attention and BFP4_B MLP projections.

Reproduce a row with `python sims/probes/model_rates.py 8b-fp8 --device 0`. The other checkpoint options are `1b`, `8b-bf16`, `nanbeige`, and `qwen38`.

## Examples

[examples/llama3.py](examples/llama3.py) runs chunked prefill and greedy decode with the kernels in [examples/llama3](examples/llama3). Weights go in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`.

```sh
python examples/llama3.py --model 1b --tokens 64
```

[Nanbeige4.3-33B](examples/nanbeige.py) runs greedy decode on one Blackhole card with BFP8_B attention projections,
BFP4_B MLP projections, and BF16 embeddings, normalization weights, and LM head. Pass the packed safetensors file
from a directory containing its config.json and tokenizer.json. The example requires the Python tokenizers package.

```sh
python examples/nanbeige.py --checkpoint ../weights/nanbeige4.3-33b/mixed_bfp4mlp_bfp8attn/model.safetensors --device 0 --prompt "The capital of France is" --tokens 64 --timing
```

The CLI allocates its BF16 KV cache for the prompt and requested output. The transformer graph handles RoPE, attention, residuals, RMSNorm, and SwiGLU on the card. Generated tokens
also run the LM head and argmax on the card. The timing option reports cached prompt tokens per second and generated tokens per second separately.

Both runners build the KV cache in chunks. Each chunk runs through all layers, with absolute positions and a causal mask for every query. The final prompt token runs the decode graph and produces the first output token. The Llama runners lazily create a second, tiled copy of the projection weights on the first chunked prompt. Nanbeige reuses the packed decode weights directly.

To compare chunk sizes at a fixed sequence length on card 0, run:

```sh
python sims/probes/prefill.py nanbeige --length 320 --chunks 32 64 160 320
```

The probe warms each graph and reports the median of three complete prefix runs. Checkpoint loading, one-time layout conversion, graph capture and first-token readout are excluded. Both example CLIs accept `--prefill-chunk` to set the maximum chunk size.

For a 320-row projection, a sender reads each packed weight block once and multicasts it to the other nine workers computing that output column. Workers computing the same prompt panel share activations across columns. The data movers stage blocks in L1 while the matrix unit consumes the previous block. Short tails of up to eight tokens use an eight-row matrix schedule.

## Qwen3.8-27B prefill and decode

Run batch-one greedy text generation from the mixed BFP4 MLP / BFP8 attention checkpoint.
Prefill batches up to 32 prompt tokens per graph and reuses the decode projection weights.
During prefill, two workers per GDN head update independent halves of its FP32 recurrent matrix in L1. An output kernel normalizes the combined head and applies its gate.
Full attention appends the chunk’s normalized, rotated keys and its values. BRISC gathers blocks from the KV cache and TRISC2 evaluates the causal queries using FP32 vector arithmetic.
The last prompt token enters the single-token decoder. Use `--serial` for token-at-a-time prompt processing.
Use `--checkpoint` for the packed safetensors file and `--metadata` for its original config and tokenizer directory.

```sh
python examples/qwen38.py --device 0 --prompt 'The capital of France is' --tokens 8 --profile
```

Prompt throughput measures execution of the captured prefix graphs. Decode throughput excludes loading, prompt processing and the first generated token.
`--profile` reports dispatcher timings grouped by kernel for the prefix and the last decode position.

On card 0 the single-token path fits 176,640 context positions with this checkpoint.
Sixteen full-attention layers consume a total of 64 KiB of BF16 KV storage per position.
The 48 GDN layers use fixed-size state. Chunked prefill also reserves activation buffers and captured graphs.

Generated-token throughput depends on context length. With 1, 96, and 320 cached prefix tokens, Qwen decoded the next 32 timed tokens at 17.3, 15.0, and 11.4 tok/s respectively. Across the 16 full-attention layers, grouped-query attention took 3.84 ms at position 33 and 33.89 ms at position 352. The 48 recurrent GDN layers took 6.47 and 6.46 ms at those positions.

Card 0 processed a 98-token prefix at 99.4 prompt tokens/s, versus 17.8 with serial decode.
At 512 prefix tokens it reached 67.7 prompt tokens/s. These timings exclude graph capture.

On card 0, a warm 320-token Qwen prefix takes 2.46 s (130 prompt tok/s).
Dispatcher timings attribute 1.24 s to GDN including its output kernel, 0.61 s to grouped-query attention,
and 0.48 s to matrix projections. Reproduce the throughput measurement with
`python sims/probes/prefill.py qwen38 --length 320`.
