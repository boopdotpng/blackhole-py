# blackhole-py

Llama 3 on a Tenstorrent Blackhole card, from Python.

## Requirements

- `tt-kmd` > 2.9.0
- Python with `numpy`, `tokenizers`, `jinja2`
- `clang` and `llvm-objcopy` (the firmware builds at startup)
- Weights in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`

## Run

```sh
python llama3.py --chat --port 8000                  # web chat on http://<host>:8000
python llama3.py --model 1b --prompt "Hello"         # one prompt in the terminal
```

Models: `1b`, `8b-fp8`, `8b-bf16`. The chat page has a model selector: nothing is loaded until you pick one, picking
another on a new chat unloads the current one and loads it, and a chat stays on the model it started with.

## Runtime

`ops_blackhole.py` follows tinygrad's HCQ naming: `BlackholeDevice` owns the `PCIIface`, the `BlackholeAllocator`
(`_alloc`, `_copyin`, `_copyout`), a `compute_queue` and a `dma_queue` (`BlackholeQueueDesc`s), and one
`timeline_signal` (`next_timeline`, `synchronize`). `BlackholeComputeQueue` (`exec`, `call`) and `BlackholeDMAQueue`
(`copy`) encode packets on top of `HWQueue` (`wait`, `signal`, `timestamp`), and `.submit(dev)` them.
`blackhole_build_program` returns immutable `BlackholeProgramData`. A `BlackholeGraph` is a compute queue stored in
DRAM, `count` times with patched args, run with CALL.

`system.py` contains the tt-kmd ioctl layouts, pinned host memory and NoC windows. Weights stream from
file mappings through two pinned staging slots. Allocations live until device close. The CQ firmware
and packet ABI are in `fw/`.

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
