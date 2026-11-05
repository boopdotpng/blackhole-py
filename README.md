# blackhole-py

Llama 3 chat (1B and 8B) on a single Tenstorrent Blackhole card.

## Requirements

- `tt-kmd` > 2.9.0
- Clang, `riscv64-linux-gnu-ld`, `riscv64-linux-gnu-objcopy`
- Checkpoints and tokenizers in `weights/llama3-1b/`, `weights/llama3-8b-fp8/`, and `weights/llama3-8b-bf16/` (not in Git)

## Chat

```sh
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python -m tools.chat --device 0
```

Open **http://127.0.0.1:8000** (or `http://<server-ip>:8000`). Use `--host` and `--port` to change the bind address.

| | Supported |
| --- | --- |
| Models | Llama 3.2 1B BF16, Llama 3 8B FP8, Llama 3 8B BF16 |
| Context | 8192 tokens (history + template + response) |
| Prompt ingestion | Decode only; no prefill |
| KV cache | Reused across turns when history matches |
| Sampling | Greedy (argmax), no temperature or top-p |
| Streaming | Yes, until EOS or full context |
| Batch size | 1 |

## Performance

Decode on a p150a (card 0), 2026-11-05, `tools.bench_llama_decode`, mean of 64 tokens. "Short" is the default
story prompt (20 tokens on 8B, 45 on 1B's chat template); "4K" decodes after a 4096-token prefix. Each cell is ms/token · tok/s · share of the DRAM roofline
(weights + LM head + KV cache read once per token at 512 GB/s).

| Model | Short | 4K context |
| --- | ---: | ---: |
| 1B BF16 | 6.23 ms · 160.4 tok/s · 78% | 8.65 ms · 115.6 tok/s · 59% |
| 8B FP8 | 19.27 ms · 51.9 tok/s · 81% | 22.20 ms · 45.1 tok/s · 75% |
| 8B BF16 | 33.11 ms · 30.2 tok/s · 89% | 36.06 ms · 27.7 tok/s · 84% |

From position 511, 8B splits each KV head's cache across four workers and merges the partial softmax states
(split-KV / Flash-Decoding). Shorter positions use one worker per query head.

## Docs

Prose docs live in [boop-docs](../boop-docs/blackhole-py/README.md). Do not add Markdown reports here.
