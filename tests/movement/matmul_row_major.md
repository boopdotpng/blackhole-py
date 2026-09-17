# Row-major matmul peak

Both inputs are uploaded row-major. Padding preserves encoded input values;
there is no host tilization. FP8's physical row stride is padded to 1024 bytes.
The benchmark generates and quantizes synthetic inputs and computes a CPU
reference outside device timing.

FP8 readers fetch row spans directly into circular buffers. The unpacker's
native tileize mode gathers two 32×16 panels into each source bank, expanding
FP8 into FP16 sources. MVMUL addressing follows that panel order. L1 row strides
include a cache-line gap where needed to avoid bank conflicts. The fast preset
uses both dataflow controllers for output writes; timing waits for both.

Default: BF16 × BF16, HiFi4 products, FP32 accumulation and output. FP32 partials
stay FP32 across K blocks. BF16 currently uses device-side scalar panel copies,
so it does not yet share the fast FP8 reader/unpacker. Explicit BF16 accumulation
remains available. `--fp8-fast` uses FP16 accumulation and output; FP8 with
`--accumulation fp32` is also supported.

## P150 measurements

5000×5000×5000, device 0, September 16, 2026:

| Path | Mean TFLOP/s | Runs |
| --- | ---: | ---: |
| Host-tilized FP8 baseline (`2b5d51a`) | 392.30 | 10 |
| Row-major FP8, native unpack | 370.74 | 10 |
| Row-major BF16, FP32 accumulation | 12.73 | 2 |

The FP8 gap is 5.5%. Device timing includes reads, unpacking, compute and final
DRAM writes, excluding host generation/upload/reference. Compared with the
baseline, math/unpack finishes sooner (~564 vs ~586 µs), but dataflow completes
later (~677 vs ~635 µs). The remaining gap is in data movement/output completion,
not a slower MVMUL loop. Full-output FP8 relative L2 error is 0.004849; BF16/FP32
is 0.000165. Inputs are compared after quantization.

Reproduce through the device queue:

```sh
../.venv/bin/python examples/matmul_peak.py 5000 5000 5000 --fp8-fast --run --device 0 --runs 10 --profile --full-validation
../.venv/bin/python examples/matmul_peak.py 5000 5000 5000 --run --device 0 --runs 2 --profile --full-validation
../.venv/bin/python -m pytest -q tests/movement/unpacker/test_unpack_row_major.py tests/compute/fpu/test_matmul_peak_fp32.py tests/compute/fpu/test_matmul_peak_schedule.py --bh-hardware
```

36 hardware tests cover both source banks, row strides, FP8/BF16 FP32 arithmetic,
partial tiles, K-block cancellation, alternate schedules and repeated launches.
Output is poisoned before launch to expose missing writes.
