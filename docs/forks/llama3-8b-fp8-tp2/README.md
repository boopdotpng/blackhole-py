# Llama 3 8B FP8/BF16 on two P150s

Experimental tensor parallelism across this machine's cabled cards 0 and 1.
Copied from `../blackhole-py-llama3-8b-fp8`, including its row-major weight work;
the source repository is unchanged. Checkpoint and environment symlinks reuse
its existing assets. See `FORK.json` for provenance.

The first matched-history benchmark reaches **66.0 tokens/s versus 47.9 on one
card (1.38×)**. All **250/250 greedy choices** match across three tested histories,
but the maximum sampled logit relative RMS error is **12.35%**, above the 5%
validation target. This is a working distributed experiment, not a claim of
numerical equivalence or completed accuracy validation.

During sustained 1,024-token generation, the cards average **240 W + 229 W =
469 W**, at **57.4 tok/s versus 43.0 on one card** as context grows. Power is
total board input, sampled independently at 10 Hz; see [details](TP2.md#power).

```sh
make -C fw/erisc
PYTHONPATH=. .venv/bin/python examples/llama3_tp2.py \
  --prompt 'The capital of France is' --steps 16
```

This runs both cards and a temporary C service on each link's E1 core. Run only
one inference/probe process at a time; the power sampler can run alongside it.
The existing E0 link firmware stays running. E1's previous code and control
state are restored on normal exit. No firmware is flashed.

- [Architecture, measurements, and remaining work](TP2.md)
- [Original single-card runtime and precision notes](SINGLE_CARD.md)
- [Matched-history results](validation/tp2-comparison-pack.json)
- [Per-stage timing](validation/tp2-profile.json)
- [Power results](validation/tp2-power.json)

Reproduce the measurements:

```sh
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=. .venv/bin/python scripts/benchmark_tp2.py \
  --output validation/tp2-comparison-pack.json
PYTHONPATH=. .venv/bin/python scripts/profile_tp2.py
PYTHONPATH=. .venv/bin/python scripts/benchmark_power_tp2.py
```

The accuracy benchmark writes its results and then exits nonzero if its strict
logit threshold fails. The profiler inserts device timestamps and therefore has
some overhead. The power benchmark runs an independent 10 Hz tt-smi backend
process, records raw samples and phase boundaries, and excludes loading/warmup
from generation power. It uses the parent workspace's `.venv` for tt-smi's
dependencies and the local `../tt-smi` source for total-board telemetry support.
