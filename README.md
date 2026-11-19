# blackhole-py

Llama 3 on a Tenstorrent Blackhole card, from Python. Every decode kernel is written in TTRV (`kernels/*.ttrv`) and compiled at startup against the current firmware.

## Requirements

- `tt-kmd` >= 2.12.0 (`smi.py` reads telemetry with the `NOC_READ` ioctl, added in 2.12.0)
- Python with `numpy` and `tiktoken`
- `clang` and `llvm-objcopy`
- Weights in `weights/llama3-1b/`, `weights/llama3-8b-bf16/` or `weights/llama3-8b-fp8/`

## Run

```sh
python llama3.py --model 1b --device 0 --tokens 64
python test_ttrv.py
python test_ttrv_hardware.py --device 0
python -m ttrv build kernels/o.ttrv -D EMBED_TILES=4 -o /tmp/llama3-o
```

`models/llama3-<model>/model.json` holds the DRAM buffer layout, the uploads, and the launch list: one entry per launch, naming a kernel and binding its parameters by name. `pos` and `write_token` are bound per run by STOREs queued ahead of the graph's CALL. The O kernel serves both the attention output and the MLP down projection.

A build directory holds a binary and a source-mapped instruction listing for each active RISC, plus a JSON manifest with parameter slots, grid size and L1 placement.

## Use from Python

```python
kernel = ttrv.build(source)
program = kernel.install(dev)
args = dev.allocator.upload(kernel.arguments(bindings)) if kernel.args_size else 0
BlackholeComputeQueue().exec(program, args).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
dev.synchronize()
```

DRAM buffer parameters bind to allocator addresses with the page size declared in the manifest, host buffers to device-visible pinned addresses, and integer parameters to 32-bit values.

## Performance

Decode on a p150a, 64 tokens after the default prompt (device clock).

| Model | ms/token | tok/s |
| --- | ---: | ---: |
| 1B BF16 | 6.35 | 157.6 |
| 8B FP8 | 26.15 | 38.2 |
| 8B BF16 | 34.11 | 29.3 |
