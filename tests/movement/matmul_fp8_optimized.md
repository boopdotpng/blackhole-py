# FP8 matmul scheduling experiments — card 1, 2026-09-16

Measured in `blackhole-py-matmul-speedup` on card 1 (P150a), through
`tt-device-queue`. Timings include completion of all output writes. Throughput
uses the logical 5000³ operation count, not padding. No changes were committed.

## Result and reproduction

The selected preset averages **638.13 us / 391.77 logical TFLOP/s** over 25
runs (632.09–642.59 us). Full-output CPU comparison passed for all 25 million
logical outputs: PCC 0.999999, relative L2 0.004849. Validation runs after the
timed launches; it is not included in kernel timing. Padded throughput is
403.76 TFLOP/s and should not be confused with logical throughput.

From this worktree:

```sh
~/.local/bin/tt-device-queue run --device 1 --cwd "$PWD" -- \
  'OPENBLAS_NUM_THREADS=8 ../.venv/bin/python examples/matmul_peak.py 5000 5000 5000 --fp8-fast --run --device 1 --runs 25 --profile --full-validation'
```

`--fp8-fast` selects FP8 inputs, FP16 accumulation/output, 1x8 subblocks, K
block 10, two N passes, two A buffers, four B buffers, NoC 1 output, row MOPs,
no blocking commit sync, faster readers, and final-block L1 accumulation.
Ordinary invocations retain the previous schedule. The preset targets large
matrices; a requested multi-pass plan must give every pass useful output.

| Configuration | Runs | Mean us | Logical TFLOP/s | Validation |
|---|---:|---:|---:|---|
| Original defaults, 2x4 | 10 | 737.42 | 339.02 | sampled + all finite |
| 1x8, no commit sync | 5 | 711.10 | 351.57 | sampled + all finite |
| Row MOP including partial-width rows | 5 | 667.20 | 374.70 | sampled + all finite |
| Two passes, compact output ring, K16, faster readers, NoC1 | 3 | 643.57 | 388.46 | sampled + all finite |
| Selected preset, final L1 accumulation | 25 | **638.13** | **391.77** | **full output** |

The selected preset takes 13.5% less time than the original defaults and
10.3% less time than the reproduced 1x8/no-sync baseline. This is about 392
TFLOP/s, not the projected 480–500 TFLOP/s.

## Implementation

- Math replays the first 15 MVMULs, then folds source release and destination
  tile progression into the last MVMUL. The destination carry tracks tile
  bases. One MOP covers a row; full 1xW subblocks also batch their K iterations
  using Blackhole's outer-count override. Partial-width rows use the inner-count
  override for their full tiles, retaining the existing 8x16 fringe arithmetic.
- The input/compute/pack controllers iterate over N passes. A is streamed again;
  B and output tile offsets advance by one pass. Global N subblock indices are
  used for edge decisions, while local indices address input buffers.
- NCRISC interleaves rows of the previous pass's output with the next pass's
  input blocks. Output uses command buffer 2 and transaction ID 2, so its
  configuration does not overwrite the reader's multicast command buffer.
  Full output storage allows outstanding writes until the final drain.
- The reload-based schedule has independent CB16/CB24 storage. The selected
  final-L1-accumulation schedule instead gives **each pass a distinct output
  slice**, points CB24 at that slice for partials, and packs the final block
  directly into it. No pass overwrites an earlier pass's output. This removes
  the final partial reload and frees L1 for deeper B buffering.
- Input readers retain invariant NoC command settings. Eight-bank address
  calculation uses shifts/masks; other bank counts retain the generic mapping.
- The optional unpack Z schedule changes the source descriptor to four rows
  per Z step and uses a single UNPACR per tile, resetting Z at each row. It
  passes hardware tests but did not improve the selected workload, so the
  preset leaves it disabled.

The FP16 issue mentioned in the earlier notes was a tt-metal compiler issue,
not a hardware restriction. Direct final FP16 L1 accumulation passed full-output
validation here. FP16 accumulation remains approximate and can lose small
partial sums; the existing FP32 cancellation/range tests still pass.

## What limited the gains

The single-pass row MOP reduced compute from about 592 to 547 us, but retained
about 120 us of exposed output tail. In the selected 25-run measurement,
compute/pack finished at about 584 us and the completed kernel at 639 us in the
last run: approximately 55 us of exposed tail.

Splitting the original readers into N passes introduced a new input-feed
bottleneck. An early two-pass version accumulated roughly 150 us of input waits,
versus 21 us for the original schedule. Faster readers, deeper buffering, and
NoC1 output recovered much of this cost. Splitting output did not provide the
predicted tail saving for free. Four passes, one A buffer, and concentrating
writes into the first few input blocks all performed worse. Split-NoC output
was also worse than NoC1 for the selected overlap workload.

The selected preset's level-1 profile measured 54 us maximum / 36 us mean
input waits, about 6 us of math waiting for pack room, and 468 us in the unpack
body. Profiling perturbed its total to 643 us. The commit counter includes
waiting for previously queued math: batching K moves more work into this wait,
so its 181 us maximum is not 181 us of removable synchronization overhead.

Template NOPs are omitted by the MOP expander, and replay can hide some expander
transition costs (see the local ISA `MOPExpander.md`). The original per-tile
slot estimate should therefore not be treated as an exact speedup prediction.

## Validation

```sh
~/.local/bin/tt-device-queue run --device 1 --cwd "$PWD" -- \
  'MATMUL_ROW_MOP=1 MATMUL_NO_COMMIT_SYNC=1 MATMUL_FAST_READS=1 MATMUL_FAST_ADDR=1 MATMUL_FINAL_L1_ACC=1 ../.venv/bin/python -m pytest -q tests/compute/fpu/test_matmul_peak_schedule.py tests/compute/fpu/test_matmul_peak_fp32.py --bh-hardware --bh-device 1'
```

**18 hardware tests passed.** Coverage includes full CPU comparisons on odd M/N/K dimensions, multiple
subblocks per pass, repeated launches on the same buffers, separate/ring/aliased
output storage, Z addressing, FP32 accumulation, cancellation, and values beyond
FP16 range. A multicore 513x257x777 preset run and a BF16 regression run also
passed full-output validation. Compile checks and `git diff --check` passed.

## Experimental controls

These remain independently selectable without `--fp8-fast`:

| Environment variable | Meaning |
|---|---|
| `MATMUL_ROW_MOP=1` | FP8 row MOP and K batching |
| `MATMUL_N_PASSES=1\|2\|4` | Per-core N passes |
| `MATMUL_A_BUFFERS`, `MATMUL_B_BUFFERS` | Input block-buffer counts |
| `MATMUL_FAST_READS=1` | Persistent input command configuration |
| `MATMUL_FAST_ADDR=1` | Eight-bank shift/mask address calculation |
| `MATMUL_FINAL_L1_ACC=1` | Final block accumulated directly in L1 |
| `MATMUL_OUTPUT_RING=1` | Compact CB16; drain before page reuse; incompatible with multi-pass final L1 accumulation |
| `MATMUL_OVERLAP_BLOCKS=n` | Spread previous output over the first n input blocks; 0 means all blocks |
| `MATMUL_UNPACK_Z=1` | Experimental Z addressing |
| `MATMUL_VALIDATE_FULL=1` | Same full reference comparison as `--full-validation` |

The earlier commit-sync and stall-counter controls remain available.
