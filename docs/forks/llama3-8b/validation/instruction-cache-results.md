# Llama 3 8B BF16: fusion and instruction prefetch

Measured 2026-09-11 on card 1. Mirrors the firmware policy from
`blackhole-py` session `01a08ea9-aa58-7923-87a4-a6f681ff3d61`.

Fusion was already enabled in this repo. The new firmware change restores
`RISC_PREFETCH_CTRL` (config word 208) to `0x11f` after backend reset at boot
and every kernel launch: all five RISCs, eight outstanding requests.
Existing CSR cache policy is preserved.

All 117 workers pass register readback on two successive launches:
all five cfg0 values are `0x20000`, and prefetch control is `0x11f`.
Firmware slot-size and full decode lowering tests pass.

Aggregate generation throughput: **29.52 tok/s**. Three prompts,
128 generated tokens each, 32 attention cores, single card. Timing includes
host decode calls and token readback, excludes startup, prompt ingestion,
and diagnostic logit reads. No before-change benchmark was run.

| Prompt | tok/s |
|---|---:|
| Explain why the sky is blue | 29.52 |
| Write a Python function that returns the Fibonacci sequence. | 29.52 |
| What are three interesting facts about the ocean? | 29.52 |

Command (from repo root):

```sh
PYTHONPATH=. /home/boop/tenstorrent/.venv/bin/python -m examples.benchmark_llama3 --device 1 --steps 128 --output validation/instruction-cache-benchmark.json
```

Evidence: [benchmark JSON](instruction-cache-benchmark.json),
[hardware tests](instruction-cache-tests.txt),
[lowering tests](instruction-cache-lowering-tests.txt).
No before/after numerical equivalence comparison was performed.

Source SHA-256 at measurement:

```json
{
  "asm.py": "fed3d619817b1cde00cae516780ec93fd53acabf6c67fa166349231ae7149965",
  "fw/core.py": "6e78a412c76f3028a9e384ed16e7408ffb73c448c1b89c5baf357f4faea7b72f",
  "examples/benchmark_llama3.py": "0623bf284ec7bc4ad42c62bd3dfc3ac46b52de2247a29051104c302e6f8be0e9"
}
```
