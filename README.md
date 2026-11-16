# blackhole-py

Llama 3 on a Tenstorrent Blackhole card, from Python.

## Requirements

- Linux: `tt-kmd` > 2.9.0. macOS: the TTGPU driver extension, see [ttgpu-dext](ttgpu-dext/README.md)
- A p150a/p150b, or a p100a (7 DRAM banks, its own kernels in `kernels/llama3-1b-p100a`)
- Python with `numpy`, `tokenizers`, `jinja2`
- `clang` and `llvm-objcopy` (the firmware builds at startup)
- Weights in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`

## Run

```sh
python llama3.py --model 8b-fp8 --chat --port 8000   # web chat on http://<host>:8000
python llama3.py --model 1b --prompt "Hello"         # one prompt in the terminal
```

Models: `1b`, `8b-fp8`, `8b-bf16`. On a p100a only `1b` is exported for now.

`smi.py` is a small tt-smi that reads telemetry without waking the card (`./smi.py`, `./smi.py --csv`, `./smi.py -r`).

## macOS

Blackhole over Thunderbolt on Apple Silicon. Install the driver extension per [ttgpu-dext/README.md](ttgpu-dext/README.md);
`system.py` then uses `system_darwin.py`, which does tt-kmd's work (TLBs, iATU, ARC messages) from Python. Everything
else, including `llama3.py`, runs unchanged.

## Performance

Decode on a p150a, 64 tokens. Short is the default story prompt (20 tokens on 8B, 45 on 1B); 4K is after a
4096-token context. % DRAM is the share of 512 GB/s needed to read the weights, LM head and KV cache once per token.

| Model | Context | ms/token | tok/s | % DRAM |
| --- | --- | ---: | ---: | ---: |
| 1B BF16 | short | 6.21 | 161.0 | 78% |
| 1B BF16 | 4K | 8.54 | 117.1 | 60% |
| 8B FP8 | short | 19.39 | 51.6 | 81% |
| 8B FP8 | 4K | 28.03 | 35.7 | 60% |
| 8B BF16 | short | 32.99 | 30.3 | 89% |
| 8B BF16 | 4K | 41.61 | 24.0 | 73% |
