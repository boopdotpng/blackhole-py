# Hybrid RMSNorm decode experiment (card 1)

The hybrid arithmetic remains faster in isolation, but the first production
port does **not** improve model throughput. Original RMSNorm remains the default.
Set `LLAMA_RMSNORM=hybrid` to test the port in standalone RMSNorm and the
RMSNorm portions of fused QKV, gate/up, and LM-head decode kernels.
Multi-token prefill is not changed.

## Method and results

Same device (1), weights, prompt, attention-core count, and 128 decode positions
within each model. Startup, prompt ingestion, and diagnostic logit reads are
excluded. A/B/B/A uses the baseline-generated token history for both paths;
it reports outer host wall time around decode (including token readback).
The reference is an exact source snapshot taken before this experiment,
including the user's pre-existing changes. No firmware setting was changed.

| Model | Original tok/s | Initial hybrid tok/s | Change |
| --- | ---: | ---: | ---: |
| Llama 3.2 1B, 2048 hidden, 16 attention cores | 152.697 | 152.556 | -0.092% |
| Llama 3 8B, 4096 hidden, 32 attention cores | 29.527 | 29.368 | -0.540% |

Values are means of the two runs per implementation in `rmsnorm_abba.json`.
The initial port used separate x and gamma CBs; `rmsnorm_initial_port.py`
preserves it. The current port uses the original single operands CB, removing
that transport difference. See `rmsnorm_one_cb.json` for its separate check.
The one-CB runs were 152.41 tok/s (1B) and about 29.38 tok/s (8B);
restoring old macro configuration,
restoring the old replay allocation offset, and adding 105 padding instructions
also remained about 29.37–29.38 tok/s. These are limited negative ablations,
not proof that every hardware-state or code-layout explanation is excluded.

Both variants predicted all 128 baseline tokens on the tested history.
Sampled hybrid-vs-original logit cosine minima were 0.999415 (1B) and
0.999829 (8B); this is not bit-identical or broad model-quality validation.
The new standalone outputs pass 0.4% relative tolerance against FP64 across
normal, small, large, zero, and repeated inputs with signed gamma. The port
must use the BF16 gasket rounding path from FP32 Dst: the original direct
FP32-to-packer configuration truncates and failed this tighter tolerance.

## Where the slowdown appears

The instrumented 8B one-CB run (`rmsnorm_stages_projection.json` in the 8B tree) measured:

| Fused kernel | Original RMSNorm cycles | Hybrid RMSNorm cycles | Original following projection cycles | Hybrid following projection cycles |
| --- | ---: | ---: | ---: | ---: |
| QKV | 9166 | 8505 | 140327 | 141941.5 |
| Gate/up | 8986.5 | 8467.5 | 641926 | 651506.5 |
| LM head | 8941.5 | 8463 | 2924301 | 2944727.5 |

RMSNorm runs from TRISC1's pre-RMSNorm timestamp to the packer's post-RMSNorm
timestamp; projection runs from TRISC1's pre-projection timestamp to its
post-projection drain. Intervals include waiting on transport and other engines,
not just arithmetic. Each number is the median of six per-launch slowest-core
samples after two warmups. Timed full decode is uninstrumented. Instrumentation
perturbs scheduling, so these locate a regression but are not additive exact
attribution of the uninstrumented tok/s change.

The following projection is slower even though the integrated RMSNorm section
is faster. The exact cause remains unresolved; do not attribute it confidently
to address counters, macro state, instruction cache layout, or numerical changes.
Restoring macro 0/misc configuration and replay start 16 did not recover speed.

## Reproduce

From either model tree, using its correct checkpoint path:

```sh
PYTHONPATH=. ../.venv/bin/python examples/benchmark_rmsnorm.py --device 1 --weights weights
LLAMA_TEST_DEVICE=1 PYTHONPATH=. ../.venv/bin/python -m pytest -q tests/test_rmsnorm_hybrid.py
LLAMA_RMSNORM=hybrid PYTHONPATH=. ../.venv/bin/python -m pytest -q tests/test_llama3_lowering.py
```

For 1B use `--weights weights/model.safetensors`. The A/B/B/A script explicitly
selects hybrid only for the current module; the saved reference does not consult
that selection. `profile_rmsnorm.py` takes the same device/weights arguments plus
`--attention-cores 16` (1B) or `32` (8B), and instruments temporary in-memory
module copies. It does not edit the model source.
