# FP8 single-card cache and fusion validation

2026-09-09. **L0 data cache and Tensix instruction fusion are now enabled by default** in [`Asm.configure_csr()`](../asm.py). The firmware clears CSR `0x7C0` bit 3 (`DisLowCash`) and bit 18 (`DisTriscCache`) on all five worker RISCs. Existing fences, branch-predictor configuration and firmware image sizes are preserved.

The normal default firmware images were checked byte-for-byte by SHA-256 against the hardware-tested `both` configuration for BRISC, NCRISC and all three TRISCs. The original assembler is preserved in [risc-config-original-asm.py](risc-config-original-asm.py); measured image hashes and input/source hashes are in the raw JSON reports.

## Performance

Each comparison uses one physical card, the published FP8 checkpoint (`weights-published-fp8`), and 32 attention cores. Rates measure host-observed sequential decode, excluding model loading, prompt prefill and sampled logit readbacks. Generation continues for the fixed number of steps even through EOS. These are end-to-end throughput measurements, not device-cycle measurements.

Card 1, three prompts, **256 generated tokens per prompt per configuration**, with an original-firmware repeat to check drift:

| Prompt | Original, tok/s | Both enabled, tok/s | Original repeat, tok/s | Gain vs mean of originals |
|---|---:|---:|---:|---:|
| Sky | 46.9400 | 47.2978 | 46.9394 | 0.763% |
| Fibonacci | 46.9113 | 47.2741 | 46.9109 | 0.774% |
| Ocean | 46.9231 | 47.2823 | 46.9179 | 0.771% |

Original repeats differ by at most 0.012%. Both-enabled throughput improves about **0.76–0.77%**. These are single sequential trials per configuration, not a statistical confidence interval.

The preceding 64-token sky-prompt checks isolated the flags:

| Card | Original, tok/s | Configuration | tok/s | Gain |
|---|---:|---|---:|---:|
| 0 | 47.9378 | Fusion only | 47.9605 | 0.047% |
| 1 | 47.9291 | L0 only | 48.2991 | 0.772% |
| 1 | 47.9291 | Both | 48.3011 | 0.776% |

The observed gain comes predominantly from enabling L0; fusion alone is within the scale of benchmark noise. Compare modes within the same card and workload, rather than comparing these figures against earlier published runs.

## Correctness and evidence

All generated token IDs match the original firmware exactly. SHA-256 hashes of complete BF16 vocabulary logits also match at the first and last generated token and on both sides of every 32-token attention boundary. This validates the tested FP8 decode paths and lengths; it does not exhaustively test every possible kernel or workload.

The CPU suite completed 15 tests: 14 passed and the explicitly opt-in device readback test was skipped. The [CPU log](risc-config-evidence/cpu-tests.log) is retained. Hardware inference validation above ran separately and passed.

- [Card 0 fusion isolation](risc-config-card0-smoke.json): `b1775fb0f64d4f8f9da2aa1d7286e6ac`.
- [Card 1 cache/both isolation](risc-config-card1-smoke.json): `1a2e8a09215b4e02b05b851653221c20`.
- [Card 1 256-token validation and drift repeat](risc-config-card1-validation.json): `dd8d8c50e124456ead45fd0a3d778169`.
- [Queue metadata](risc-config-evidence/runs.json), compressed logs and final source snapshots are in `risc-config-evidence/`. Snapshot `source/asm.py` contains the enabled default; raw experiment source hashes refer to the preserved original assembler.

## Reproduction

From this repository, submit through `tt-device-queue` on the queue matching `--device`. The comparison script reconstructs the original firmware for `baseline`, independently of the new defaults, and changes modes only inside its process. Each mode boots a fresh runtime.

```bash
PYTHONPATH=. OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/benchmark_risc_config.py \
  --device 1 --steps 256 --modes baseline both baseline \
  --output validation/risc-config-card1-validation.json
```

For isolation, use `--modes baseline fusion cache both`. Raw files contain every per-token duration, generated token, sampled logit hash and firmware image hash.

The [Blackhole cycle reference](../../boop-docs/microbenching/timing-reference/README.md) explains why enabling L0 changes loads and enabling fusion changes Tensix delivery. Its original `blackhole-py` baseline measurements retain their original disabled-cache/fusion configuration; the default change here applies to this FP8 runtime.
