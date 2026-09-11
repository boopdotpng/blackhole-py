# blackhole-py-llama3-8b-fp8

Llama 3 8B Instruct inference on Tenstorrent Blackhole, using Neural Magic's
calibrated FP8 checkpoint, published by Red Hat AI. Built with Meta Llama 3.

This is a separate copy of `../blackhole-py-llama3-8b`. The original repository
and its BF16 weights are unchanged. All hardware validation uses **card 1**.
Measured throughput is **47.72 tok/s** for 64-token runs and **45.51 tok/s**
for 512-token runs. See [PERFORMANCE.md](PERFORMANCE.md) for accuracy limits.

## Run

The local `.venv` and downloaded `weights-published-fp8/` are ready:

```sh
PYTHONPATH=. .venv/bin/python examples/llama3.py \
  --device 1 --prompt 'What is the capital of France? Answer in one short sentence.' \
  --steps 16 --profile
```

The default checkpoint is `weights-published-fp8/`. To reproduce the download:

```sh
.venv/bin/python scripts/download_fp8_weights.py
```

This downloads about 9.1 GB directly from
[RedHatAI/Meta-Llama-3-8B-Instruct-FP8](https://huggingface.co/RedHatAI/Meta-Llama-3-8B-Instruct-FP8),
pinned to `c5c6b5700a4178ef1fdae2ae37827382b90eb400`. It is Neural Magic's
quantization of Meta's model, not a Meta-published FP8 checkpoint. The publisher
calibrated static activation scales on 512 UltraChat sequences. We use the
supplied FP8 weights and per-projection scales; no BF16-to-FP8 weight conversion
or second weight download occurs at startup. Host preparation still tiles and
stages the weights for device upload.

## Precision

| Operation / storage | Precision |
| --- | --- |
| Q, K, V and output projections | FP8 E4M3 weights and scaled FP8 inputs |
| MLP gate, up and down projections | FP8 E4M3 weights and scaled FP8 inputs |
| Projection accumulation and scale application | FP32, packed to BF16 |
| Embeddings, normalization weights, output head | BF16, as supplied |
| Residual stream, Q/K/V, attention context, MLP intermediates | BF16 |
| Attention QK/PV operands and KV cache | BF16 |
| RMSNorm and softmax calculations | FP32 |

FP8 inference is mixed precision. The existing BF16 attention, residual, embedding
and output-head kernels remain in use. Input quantization happens on-device,
fused into the projection launch, using `quantize(x / input_scale)`; projection
results are multiplied by `input_scale * weight_scale`.

Blackhole's native FP8 subnormal behavior differs from IEEE E4M3. Native operands
explicitly flush subnormals, and an SFPU rounding step precedes the truncating
hardware FP8 packer. The CPU reference emulates that contract. FP32 fused RMSNorm
and device arithmetic can still differ slightly from the CPU implementation.

## Launches and tuning

There are **163 launches per generated token**: five fused launches per layer
across 32 layers, plus embedding, final normalization/output head, and argmax.
The sibling `blackhole-py-llama3` 1B runtime uses the same structure with 16 layers,
which gives 83 launches. This copy already includes those fusions and resident
command traces; FP8 conversion adds no launches.

The card 1 defaults use 96 projection workers, 32 attention workers, NoC split
at x=10, and one FP8 math fidelity phase. Environment overrides are
`LLAMA_PROJECTION_CORES`, `LLAMA_NOC_SPLIT_X`, and `LLAMA_FP8_FIDELITY`.
This is batch-one decode; prompt ingestion also processes one token at a time.
The model has an 8,192-token cache. No external kernel compiler is needed.

## Reproduce validation

```sh
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=. .venv/bin/python scripts/projection_probe.py
PYTHONPATH=. .venv/bin/python scripts/cpu_fp8_reference.py
PYTHONPATH=. .venv/bin/python scripts/evaluate_fp8.py --mode fp8 \
  --steps 64 256 512 --output validation/published-fp8-final.json \
  --reference validation/published-fp8-cpu-logits.npz \
  --logits-output validation/published-fp8-device-logits.npz
```

For the BF16 comparison, select `--mode bf16` and set
`LLAMA_PROJECTION_CORES=88 LLAMA_NOC_SPLIT_X=7`, matching the original 8B tuning.
Fresh environments need `requirements-cpu.txt` for tests and CPU references;
`requirements.txt` covers the runtime. NumPy 2.4.6 is pinned because the machine's
older NumPy build produced incorrect conversion results under Python 3.14.

## Earlier experiments

`weights-fp8/` and `scripts/convert_fp8.py` retain the initial local conversion
experiment. `LLAMA_ATTENTION_DTYPE=fp8` enables experimental native FP8 attention;
it is **not** the validated default. The initial approximately 50 tok/s results
used more aggressive quantization and had substantially worse logit agreement.
Do not confuse those artifacts with `validation/published-fp8-final.json`.

Model weights now upload in row-major order without host tilization. See
[layout contract and validation](ROW_MAJOR_WEIGHTS.md).

L0 data cache and Tensix instruction fusion are enabled in worker firmware.
[Same-card FP8 validation](validation/risc-config-results.md) measured about
0.76–0.77% higher decode throughput with exact generated-token and sampled-logit
matches across three 256-token prompts.
