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
| Llama 3.2 1B | BF16 | 7,359 | 159.0 |
| Llama 3 8B | BF16 | 2,019 | 30.1 |
| Llama 3 8B | BFP8_B | 2,493 | 47.4 |
| Qwen3.8-27B | Mixed BFP, BFP8_B down | 181 | 17.3 |
| Nanbeige4.3-33B | Mixed BFP | 1,003 | 19.0 |

Each rate is the median of three warm runs on the same fixed token IDs. Prefill measures KV-cache construction for 320 prefix tokens, in one chunk for Llama and Nanbeige and ten 32-token chunks for Qwen. Decode measures the next 32 streamed tokens after the first output. Timings exclude checkpoint loading, compilation, and graph capture. Both mixed checkpoints use BFP8_B attention and BFP4_B MLP gate and up projections. Qwen uses BFP8_B down projections and a BF16 LM head. Nanbeige uses BFP4_B down projections and a BFP8_B LM head. Llama 3 8B BFP8_B packs every attention and MLP projection and the LM head as BFP8_B and keeps embeddings and norms in BF16.

Reproduce a row with `python sims/probes/model_rates.py 8b-bfp8 --device 0`. The other checkpoint options are `1b`, `8b-bf16`, `nanbeige`, and `qwen38`.

## Two cards

Two p150a cards joined by a QSFP-DD cable run decode tensor parallel. Each card holds half the attention heads, half
the MLP and half the vocabulary. Same measurement as above (320-token prefix, the 32 streamed tokens after the first
output, median of three warm runs); the one-card column is the table above.

| Model | Weights | 1× p150a decode (tok/s) | 2× p150a decode (tok/s) | Speedup |
| --- | --- | ---: | ---: | ---: |
| Llama 3.2 1B | BF16 | 159.0 | 258.1 | 1.62× |
| Llama 3 8B | BF16 | 30.1 | 52.4 | 1.74× |
| Llama 3 8B | BFP8_B | 47.4 | 74.3 | 1.57× |
| Nanbeige4.3-33B | Mixed BFP | 19.0 | 31.3 | 1.65× |
| Qwen3.8-27B | Mixed BFP, BFP8_B down | 17.3 | 28.8 | 1.66× |

Reproduce a row with `python eth/tp_rates.py 8b-bfp8`; the other options are `1b`, `8b-bf16`, `nanbeige` and `qwen38`. To generate
text, run `python eth/llama3_tp.py --model 8b-bf16` (BF16 Llama) or `python eth/nanbeige_tp.py --checkpoint ...` (packed
checkpoints, including Llama 3 8B BFP8_B).

The cards talk over Ethernet channel 11, which must be cabled straight across (card 0 ch 11 to card 1 ch 11). Each
card's second Ethernet RISC (ERISC1) runs a small forwarder ([eth/e1_fwd.c](eth/e1_fwd.c)) while the vendor base
firmware keeps running on ERISC0. It sends over TT-link TX queue 2, which the base firmware configures and leaves idle,
so no link, MAC or queue configuration changes. Before ERISC1 leaves reset the KMD is told to put it back in reset when
the device fd closes, so a crash or kill leaves nothing running.

After o_proj and down_proj each card writes a BF16 partial sum. A 16-worker kernel ([eth/allreduce.c](eth/allreduce.c))
stages it in the Ethernet tile, waits for the peer's half and writes `(p0 + p1) + residual`, summed in FP32 in card order
so both cards hold the same bits. Each all-reduce takes 10 to 15 µs including its launch. After the vocabulary-split LM
head, [eth/pick.c](eth/pick.c) exchanges the two argmax winners. Llama and Nanbeige process two-card prompts one token at a time. Qwen supports chunked prefill on both one and two cards.

Both cards pick the same token at every step. Llama matches single-card output token for token. Nanbeige matches for the
first dozen tokens of a sample prompt and then picks the runner-up at a one-logit margin: splitting o_proj and down_proj
adds two rounded partials instead of rounding once, and on layer 0 both are equally close to a float64 reference.

## Examples

[examples/llama3.py](examples/llama3.py) runs chunked prefill and greedy decode with the kernels in [examples/llama3](examples/llama3). Weights go in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-bfp8/`. BF16 checkpoints use the row-major kernels in `examples/llama3`; the BFP8_B checkpoint is a single packed safetensors file and runs on the Nanbeige projection graph.

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

The default checkpoint stores attention and MLP down projections in BFP8_B, gate and up projections in BFP4_B, and the vocabulary head in BF16. The loader also accepts the earlier BFP4_B-down checkpoint with `--checkpoint`. To build the new checkpoint from the original packed and BF16 snapshots, run `python -I examples/qwen38_repack.py`.

All Qwen compute kernels are TTRV. The SFPU performs the depthwise convolution, SiLU, FP32 gated delta recurrence and gated RMSNorm. Each worker retains 64 value channels of a head. The unpacker moves the FP32 state directly into Dst. The SFPU computes the correction against the previous state, updates each row, and accumulates the context from the updated rows in key order.

Prefill batches up to 32 prompt rows for projections. The recurrent and causal attention kernels consume those rows in sequence and share their state with decode. Use `--serial` for token-at-a-time prompt processing.

| Qwen3.8-27B throughput | 1× P150a | 2× P150a | Speedup |
| --- | ---: | ---: | ---: |
| Prefill (tok/s) | 180.7 | 186.2 | 1.03× |
| Decode (tok/s) | 17.3 | 28.8 | 1.66× |

These are medians of three warm runs with the BFP8_B-down checkpoint, a 320-token prefix in ten chunks, and 32 timed decode steps after the first output.

In a 64-step GDN comparison, 99.991% of 393,216 BF16 outputs matched the original C worker bit for bit. The FP32 state check also passed over 1,024 recurrent steps. On 5-token and 41-token prompts, serial and chunked prefill on both card configurations produced the same 12 greedy tokens as the C decoder.

```sh
python examples/qwen38.py --prompt 'The capital of France is' --tokens 12
python examples/qwen38.py --tp 2 --prompt 'The capital of France is' --tokens 12
python examples/qwen38_check.py --device 0 --tokens 256
```

Two-card TP splits each Q, K and V projection by head, the MLP by intermediate channel, and the LM head by vocabulary row. The TTRV residual kernel exchanges the attention and MLP partial sums on TT-link channel 11, then adds them on the SFPU. The argmax workers exchange their candidates and publish the winning token on both cards. `--profile` reports rank 0 dispatcher timings in TP mode.
