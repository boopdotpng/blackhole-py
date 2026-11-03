# Row-major matmul peak

Both inputs are uploaded row-major. Padding preserves encoded input values;
there is no host tilization. FP8's physical row stride is padded to 1024 bytes.
The benchmark generates and quantizes synthetic inputs and computes a CPU
reference outside device timing.

Both readers fetch row spans directly into circular buffers. FP8's native
tileize mode gathers two 32×16 panels into each source bank, expanding FP8
into FP16 sources. BF16 uses replayed 16-element UNPACR reads with descriptor
row strides to gather the same panels, preserving BF16. Blackhole's tileize
mode reads 32 elements per row for BF16, so it cannot use FP8's two-instruction
sequence. Neither path copies elements with scalar RISC loads/stores. MVMUL addressing follows that panel order. L1 row strides
include a cache-line gap where needed to avoid bank conflicts. The fast preset
uses both dataflow controllers for output writes; timing waits for both.

Default: BF16 × BF16, HiFi4 products, FP32 accumulation and output. FP32 partials
stay FP32 across K blocks. Explicit BF16 accumulation
remains available. `--fp8-fast` uses FP16 accumulation and output; FP8 with
`--accumulation fp32` is also supported.

## P150 measurements

5000×5000×5000, device 0, September 16, 2026:

| Path | Mean TFLOP/s | Runs |
| --- | ---: | ---: |
| Host-tilized FP8 baseline (`2b5d51a`) | 392.30 | 10 |
| Row-major FP8, native unpack | 370.75 | 10 |
| Host-tilized BF16, HiFi2/BF16 accumulation (`2b5d51a`) | 182.53 | 5 |
| Row-major BF16, native unpack, HiFi2/BF16 accumulation | 50.93 | 5 |
| Row-major BF16, scalar panel-copy baseline (`0ebd556`) | 12.73 | 2 |
| Row-major BF16, native unpack, FP32 accumulation | 47.52 | 10 |

### October 2, 2026: FP32 accumulation only, row-major BF16 output

The kernel now has exactly two modes, both accumulating in FP32 and both
writing a **row-major BF16** result straight to DRAM (no host untilize):

* BF16 × BF16, fidelity a parameter (`--fidelity`, default HiFi2; HiFi4 is exact
  products).
* FP8 E4M3 × E4M3, one fidelity phase (exact products).

BF16 accumulation and FP8/FP16 accumulation were removed, along with the
switches that only selected slower variants (PIPELINED_PACK, NO_COMMIT_SYNC,
FAST_ADDR, BATCHED_UNPACK, FINAL_L1_ACC, OUTPUT_RING, DUAL_WRITER), the reload
schedule, and FP16/FP32 outputs.

The epilogue (`examples/matmul_peak_kernel/epilogue.py`) runs after the last K
block: TRISC0 unpacks each 1x4 subblock's FP32 accumulator tiles straight into
Dst, TRISC2 packs them untilized (strided Dst reads under Dst remap), rounding
to BF16 with ties away from zero (the packer's only deterministic mode; it
differs from round-to-nearest-even only on exact ties), into the tiles' own
CB16 storage, and NCRISC writes 32 row segments per subblock. Output rows are
padded to whole 2048-byte pages. Limits: 1xW subblocks, N_PASSES = 1.

5000³ and 4096³ on all 117 cores, full validation (PCC ≥ 0.999995):

| Mode | 5000³ TFLOP/s | 4096³ TFLOP/s | rel L2 |
| --- | ---: | ---: | ---: |
| FP8, FP32 accumulation | **289.7** | 286.6 | 1.7e-3 (BF16 output rounding) |
| BF16 HiFi2, FP32 accumulation | **132.5** | 137.8 | 3.9e-3 |
| BF16 HiFi4, FP32 accumulation | 97.0 | | 1.7e-3 |

Before this change the same FP32-accumulation modes measured 250.7 (FP8) and
53.1 (BF16) with FP32 tiled output. The BF16 jump comes from single-buffering B
by default: BF16 prepares each K block in a serialized phase, so the planner's
longer K block (2 instead of 1) beats double-buffered B staging.

### Earlier October 2 numbers (modes since removed)

| Path (row-major inputs, 117 cores) | Mean TFLOP/s |
| --- | ---: |
| BF16 accumulation, prepare + old readers | 98.6 |
| BF16 accumulation, prepare + fast readers | 188.2 |
| BF16 accumulation, tt-metal tilize prepare | 179.7 |
| FP8 FP16 accumulation | 380.4 |

tt-metal's Blackhole BF16 tilize (one tileize UNPACR per tile) leaves row halves
interleaved in Src; de-interleaving costs 32 PACRs per tile, so the gather
prepare (eight row UNPACRs plus a Dst-remapped pack) stayed
(`tests/probes/test_bf16_tilize.py`).

(September 16 notes.) BF16 was 3.7× faster than the scalar-copy implementation, but still 72.1% below
the host-tilized BF16 baseline in the same HiFi2/BF16 accumulation mode. Its
64 row gathers per tile were repeated on reuse; see the October section above for
the fix. The 47.52 result uses HiFi4/FP32, so it is not a matched-mode comparison
with 182.53. The FP8 gap is 5.5%. Device timing includes reads, unpacking, compute and final
DRAM writes, excluding host generation/upload/reference. For FP8, compared with the
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

54 hardware tests cover both source banks, row strides, FP8/BF16 FP32 arithmetic, BF16 accumulation, both reader paths,
partial tiles, K-block cancellation, alternate schedules and repeated launches.
Output is poisoned before launch to expose missing writes.
