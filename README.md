# blackhole-py

Llama 3 8B chat on a single Tenstorrent Blackhole card.

## Requirements

- `tt-kmd` > 2.9.0
- Clang, `riscv64-linux-gnu-ld`, `riscv64-linux-gnu-objcopy`
- Checkpoints and tokenizers in `weights/llama3-8b-fp8/` and `weights/llama3-8b-bf16/` (not in Git)

## Chat

```sh
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python -m tools.chat --device 0
```

Open **http://127.0.0.1:8000** (or `http://<server-ip>:8000`). Use `--host` and `--port` to change the bind address.

| | Supported |
| --- | --- |
| Models | Llama 3 8B FP8, Llama 3 8B BF16 |
| Context | 8192 tokens (history + template + response) |
| Prompt ingestion | Decode only; no prefill |
| KV cache | Reused across turns when history matches |
| Streaming | Yes, until EOS or full context |
| Batch size | 1 |

## Performance

Decode on a p150a (card 0), 2026-11-05, `tools.bench_llama_decode`. Roofline: weights + LM head + KV cache read once per token at 512 GB/s.

| Model | Context | ms/token | tok/s | DRAM roofline |
| --- | ---: | ---: | ---: | ---: |
| 8B FP8 | short | 19.27 | 51.9 | 81% (of 63.7 tok/s) |
| 8B FP8 | 4096 | 28.07 | 35.6 | 60% (of 59.8 tok/s) |
| 8B BF16 | short | 33.11 | 30.2 | 89% (of 34.1 tok/s) |
| 8B BF16 | 4096 | 41.91 | 23.9 | 73% (of 32.9 tok/s) |

Opt-in FP8 modes (`--lm-head-dtype fp8`, `--split-attention`) are faster but change numerics; see [fp8-decode](../boop-docs/measurements/llama/fp8-decode.md).

## Docs

Prose docs live in [boop-docs](../boop-docs/blackhole-py/README.md). Do not add Markdown reports here.
