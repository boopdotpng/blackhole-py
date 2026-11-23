# blackhole-py

A single-card runtime for Tenstorrent Blackhole (p100a/p150a) in Python, plus LLM inference on it. Kernels are
written in TTRV (`ttrv/`), a small language that compiles to the five RISC-V cores and Tensix engines of each
worker. The host installs kernel images and a table of kernel calls in worker L1; one graph replay runs a whole
decode step. It runs on Linux (`/dev/tenstorrent`) and macOS (the TTGPU driver extension in `ttgpu-dext/`).

Models (weights under `../weights`): Nanbeige4.3-33B, Qwen3.8-27B, Inkling 2 Mini.

## Requirements

Python 3, NumPy, tokenizers, Jinja2, Clang, LLD and LLVM objcopy. Linux needs the IOMMU enabled. macOS needs
the driver extension: `./dext.sh`.

## Run

```sh
python3 examples/nanbeige.py --prompt "The capital of France is" --tokens 16 --timing
python3 examples/qwen38.py --tokens 16 --profile
python3 examples/inkling.py --chat --prompt "Name three primary colors." --tokens 32
```

## Serve (OpenAI-compatible)

```sh
python3 examples/serve.py --model nanbeige --context 8192 --port 8000
curl localhost:8000/v1/chat/completions -H 'content-type: application/json' \
  -d '{"messages": [{"role": "user", "content": "Hi"}], "stream": true}'
```

Concurrent requests decode together (up to 64 sequences per step). Prompts prefill in chunks between decode
steps. Slot states that get evicted go to host RAM, then SSD (`--offload-ram`, `--offload-ssd`,
`--offload-dir`). The SSD entries persist across restarts, so a new session that shares a long system prompt
skips its prefill. Batched Qwen and Inkling backends are in progress.

## Test

```sh
python3 -m pytest -q                                  # card 0
python3 examples/batch_check.py --model nanbeige      # batched decode against single-sequence decode
python3 examples/offload_check.py --model nanbeige    # RAM, SSD and restart restores
python3 smi.py                                        # card telemetry
```

Each process owns one card (`--device N`).
