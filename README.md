# blackhole-py

Llama 3 on a Tenstorrent Blackhole card, from Python. The kernels in `kernels/` are prebuilt RISC-V images.

## Requirements

- `tt-kmd` > 2.9.0
- Python with `numpy` and `tiktoken`
- `clang` and `llvm-objcopy`
- Weights in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`

## Performance

Decode on a p150a, 64 tokens after a short prompt and after a 4096-token context.

| Model | Context | ms/token | tok/s | % DRAM |
| --- | --- | ---: | ---: | ---: |
| 1B BF16 | short | 6.27 | 159.4 | 77% |
| 1B BF16 | 4K | 7.02 | 142.5 | 73% |
| 8B FP8 | short | 19.79 | 50.5 | 79% |
| 8B FP8 | 4K | 22.12 | 45.2 | 76% |
| 8B BF16 | short | 33.38 | 30.0 | 88% |
| 8B BF16 | 4K | 35.67 | 28.0 | 85% |
