# blackhole-py

Blackhole assembly, a raw byte-buffer runtime, single-card Llama inference,
and hardware operation tests.

## Run the models

Run commands from this directory. Local checkpoints are under `weights/` and
are ignored by Git. The main runners require NumPy and Transformers:

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt
```

Use `tt-device-queue` to reserve the physical card selected by `--device`:

```sh
# Llama 3.2 1B, BF16
tt-device-queue run --device 0 --cwd "$PWD" -- \
  '.venv/bin/python -m examples.llama3_1b --device 0 --prompt "What is the capital of France?" --steps 32 --profile'

# Llama 3 8B Instruct, BF16
tt-device-queue run --device 1 --cwd "$PWD" -- \
  '.venv/bin/python -m examples.llama3_8b --device 1 --prompt "What is the capital of France?" --steps 32 --profile'

# Llama 3 8B Instruct, published calibrated mixed FP8/BF16
tt-device-queue run --device 0 --cwd "$PWD" -- \
  '.venv/bin/python -m examples.llama3_8b_fp8 --device 0 --prompt "What is the capital of France?" --steps 32 --profile'
```

`examples/llama3.py` is a compatibility entry point for 1B. Each single-card
runner accepts `--safetensor` and `--tokenizer` to override its local defaults.
There are no runtime source dependencies on the sibling forks.

## Prefill

The 8B BF16 runner accepts `--prefill --prefill-chunk-size 4` (chunk size 1–8).
Sequential prompt ingestion remains the default.

## Checkpoints

| Directory | Contents |
| --- | --- |
| `weights/llama3-1b/` | Existing Llama 3.2 1B BF16 checkpoint |
| `weights/llama3-8b-bf16/` | Existing Llama 3 8B Instruct BF16 checkpoint |
| `weights/llama3-8b-fp8/` | Published RedHatAI / Neural Magic calibrated FP8 checkpoint |
| `weights/archive/` | Existing duplicate BF16 snapshots retained from the forks |

FP8 uses `RedHatAI/Meta-Llama-3-8B-Instruct-FP8`, revision
`c5c6b5700a4178ef1fdae2ae37827382b90eb400`, with BF16 embeddings, norms, and
output head.
Checkpoint licenses remain alongside the weights.

## Code layout

- `device.py`, `program.py`, `cq.py`, `pcie.py`: central raw-byte runtime.
- `asm.py`, `isa.py`, `regalloc.py`: central raw kernel assembler.
- `ttko/`: legacy TTK, its namespaced assembler/ISA, and model adapters.
  The adapters inherit central device boot and command-queue transport, adding
  resident kernel caching, parameter templates, and asynchronous trace replay.
- `examples/`: model runners, prefill, and RMSNorm helper.
- `tests/`: hardware operation examples.
- `tools/viewer/`: preserved instruction viewer and reference data.

Model weights upload as row-major bytes. There is no host tilization or
untilization. Legacy buffers requiring face layout use `ttko/layout.py` to
convert on the device; host work only pads shards and converts scalar dtypes.
The raw runtime continues to transfer bytes without tensor conversion.

All model variants boot through `fw/build.py`. Instruction prefetch remains
`0x11f`, instruction caches remain enabled, and TRISC instruction fusion stays
enabled. The consolidated ABI has 24 parameter words and a larger resident
kernel arena. CQ firmware sources and service image hashes are unchanged.
See [firmware details](fw/README.md).

## Tests

```sh
tt-device-queue run --device 0 --cwd "$PWD" -- \
  'PYTHONPATH=. .venv/bin/python -m pytest -q tests/timing/test_firmware_cache.py tests/models/test_runtime.py --bh-hardware --bh-device=0'
```

Tests require pytest and run only with hardware enabled. Model tests may use
`LLAMA_TEST_DEVICE` or `LLAMA_PREFILL_DEVICE`; match these to the reserved card.

Supported runtime topology: P100A with seven DRAM banks or P150A/B/C with eight,
using the existing 120-tile firmware layout and three CQ service tiles. Requires
`tt-kmd` > 2.9.0. Worker firmware assembly requires only Python.
