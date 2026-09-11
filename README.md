# blackhole-py

Blackhole assembly, a raw byte-buffer runtime, and Llama inference on one or two
cards. This is the central repository for the former Llama forks. Qwen remains
separate.

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

For two-card mixed FP8, build the Ethernet service and reserve both cards in
ascending order. The default transport transfers partials through ERISC L1 and
the cable, then reduces them on Tensix:

```sh
make -C fw/erisc/tp2
tt-device-queue run --device 0 --cwd "$PWD" -- \
  "tt-device-queue run --device 1 --cwd '$PWD' -- '.venv/bin/python -m examples.llama3_tp2 --devices 0 1 --steps 32 --output validation/tp2-run.json'"
```

This path requires two cabled P150 cards with the trained link used by the
ported service. `--transport host` retains the diagnostic host collective.
The two-card runner uses a raw completion prompt; the single-card 8B runners
apply the checkpoint's chat template.

## Prefill and speculation

Chunked prefill is available for **8B BF16**, behind `--prefill`. The default
still ingests the prompt one token at a time. `--prefill-chunk-size` accepts
1–8, with 4 as the default:

```sh
tt-device-queue run --device 1 --cwd "$PWD" -- \
  '.venv/bin/python -m examples.llama3_8b --device 1 --prefill --prefill-chunk-size 4 --prompt "Explain why the sky is blue." --steps 32'

tt-device-queue run --device 0 --cwd "$PWD" -- \
  '.venv/bin/python -m examples.llama3_speculative --device 0 --steps 32 --benchmark --output validation/speculative.json'
```

Prefill is a preserved experimental optimization: it matched sequential
BF16 logits exactly in port validation, but was slower for the short prompts
measured. Speculation uses prompt lookup and the same model as verifier.
Neither path changes the default FP8 or two-card runner.

## Checkpoints

| Directory | Contents |
| --- | --- |
| `weights/llama3-1b/` | Existing Llama 3.2 1B BF16 checkpoint |
| `weights/llama3-8b-bf16/` | Existing Llama 3 8B Instruct BF16 checkpoint |
| `weights/llama3-8b-fp8/` | Published RedHatAI / Neural Magic calibrated FP8 checkpoint |
| `weights/archive/` | Existing duplicate BF16 snapshots retained from the forks |

The experimental local BF16-to-FP8 checkpoint and its conversion tools have
been removed. The retained FP8 checkpoint is
`RedHatAI/Meta-Llama-3-8B-Instruct-FP8`, revision
`c5c6b5700a4178ef1fdae2ae37827382b90eb400`; it is a published quantization of
Meta's model. Its embeddings, normalization weights, and output head remain
BF16. Projection weights and scaled projection inputs use FP8; accumulation,
attention, and residual handling retain the original mixed-precision contract.
The download utility is `scripts/llama3_8b_fp8/download_fp8_weights.py`.
Checkpoint licenses remain alongside the weights.

## Code layout

- `device.py`, `program.py`, `cq.py`, `pcie.py`: central raw-byte runtime.
- `asm.py`, `isa.py`, `regalloc.py`: central raw kernel assembler.
- `ttk/model.py` and `ttk/sketches/rmsnorm_embedding.py`: preserved experimental
  TTK and RMSNorm sketch; independent of the working model stack.
- `ttko/`: legacy TTK, its namespaced assembler/ISA, and model adapters.
  The adapters inherit central device boot and command-queue transport, adding
  resident kernel caching, parameter templates, and asynchronous trace replay.
- `examples/`: main runners, prefill, speculative verifier, and RMSNorm helper.
  `llama3_reference.py` preserves the original unhooked central example.
- `examples/diagnostics/` and `scripts/`: per-model probes, benchmarks,
  checkpoint tools, and validation utilities.
- `distributed/llama3/`: mesh/protocol experiments;
  `distributed/tp2/` and `fw/erisc/tp2/`: working two-card implementation.
- `tools/viewer/`: preserved instruction viewer and reference data.
- `docs/forks/`: historical notes and measurements, attributed to each fork.
  Their old commands and paths are historical, not current instructions.

Model weights upload as row-major bytes. There is no host tilization or
untilization. Legacy buffers requiring face layout use `ttko/layout.py` to
convert on the device; host work only pads shards and converts scalar dtypes.
The raw runtime continues to transfer bytes without tensor conversion.

All model variants boot through `fw/build.py`. Instruction prefetch remains
`0x11f`, instruction caches remain enabled, and TRISC instruction fusion stays
enabled. The consolidated ABI has 24 parameter words and a larger resident
kernel arena. CQ firmware sources and service image hashes are unchanged.
See [firmware details](fw/README.md).

## Validation

The four requested model configurations generated coherent text from this
repository. Results, commands, and limits are recorded in
[the port validation report](validation/current/README.md).

```sh
PYTHONPATH=. .venv/bin/python -m pytest -q
tt-device-queue run --device 0 --cwd "$PWD" -- \
  'PYTHONPATH=. .venv/bin/python -m pytest -q tests/timing/test_firmware_cache.py tests/models/test_runtime.py --bh-hardware --bh-device=0'
```

CPU reference tools also need `requirements-cpu.txt`; CPU test collection needs
pytest. Hardware tests are opt-in. Some inherited model tests additionally use
`LLAMA_TEST_DEVICE`; always match it to the reserved card.

Supported runtime topology: P100A with seven DRAM banks or P150A/B/C with eight,
using the existing 120-tile firmware layout and three CQ service tiles. Requires
`tt-kmd` > 2.9.0. Ethernet C builds require `riscv64-linux-gnu-gcc` and binutils;
worker firmware assembly requires only Python.
