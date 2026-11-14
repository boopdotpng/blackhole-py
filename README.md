# blackhole-py

Llama 3 on a Tenstorrent Blackhole card, from Python. The kernels in `kernels/` are prebuilt RISC-V images.

## Requirements

- `tt-kmd` > 2.9.0
- Python with `numpy` and `tiktoken`
- `clang` and `llvm-objcopy`
- Weights in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`

## Performance

Decode on a p150a, 64 tokens after a short prompt and after a 4096-token context (`python bench.py`).

| Model | Context | ms/token | tok/s | % DRAM |
| --- | --- | ---: | ---: | ---: |
| 1B BF16 | short | 5.96 | 167.9 | 81% |
| 1B BF16 | 4K | 6.50 | 153.9 | 78% |
| 8B FP8 | short | 18.81 | 53.2 | 83% |
| 8B FP8 | 4K | 20.48 | 48.8 | 82% |
| 8B BF16 | short | 32.43 | 30.8 | 90% |
| 8B BF16 | 4K | 33.99 | 29.4 | 89% |
