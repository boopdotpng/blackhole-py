# blackhole-py

Llama 3 on a Tenstorrent Blackhole card, from Python. The default runner uses the prebuilt RISC-V images in `kernels/`. Pass `--ttrv` to compile all eight decode stages from source.

## Requirements

- `tt-kmd` >= 2.12.0 (`smi.py` reads telemetry with the `NOC_READ` ioctl, added in 2.12.0)
- Python with `numpy` and `tiktoken`
- `clang` and `llvm-objcopy`
- Weights in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`

## Compile and run a TTRV kernel

The compiler builds the Llama 3 decode kernels for the 1B, 8B BF16 and 8B FP8 checkpoints. The [kernel sources](docs/examples) use the same O projection for the attention output and MLP down stages.

```sh
python -m ttrv build docs/examples/llama3_o.ttrv -D EMBED_TILES=4 -o /tmp/llama3-o
python test_ttrv.py
python test_ttrv_hardware.py --device 1
python llama3.py --model 1b --device 0 --tokens 64 --ttrv
```

The build directory contains a binary and a source-mapped instruction listing for each active RISC, plus a JSON manifest with parameter slots, grid size, and L1 placement. Building and inspecting the images requires only Python. The hardware regression runs the O projection on 88 workers, compares every output row with a CPU reference, and checks persistent storage, remote atomics, multicast, SFPU macros and pack formats.

From Python, compile source text with `ttrv.build` and install the result on an open `BlackholeDevice`. Installations with persistent storage report their device-specific addresses in `program.manifest`. Bind DRAM buffer parameters to allocator addresses with the page size declared in the manifest, host buffers to device-visible pinned addresses, and integer parameters to values in their declared range. `kernel.bind` rewrites some of them in place between runs.

```python
kernel = ttrv.build(source)
program = kernel.install(dev)
args = dev.allocator.upload(kernel.arguments(bindings)) if kernel.args_size else 0
BlackholeComputeQueue().exec(program, args).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
dev.synchronize()
```

Workers read their column, row and index from firmware and their arguments from one parameter block per launch. `llama3.py` binds the integer arguments (the token position and values derived from it) before each run, as tinygrad binds a graph's Variables. The [language specification](docs/ttrv_spec.md) describes device operations and the remaining hardware audits.

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
