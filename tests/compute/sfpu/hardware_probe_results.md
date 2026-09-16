# SFPU argmax, packer L1 accumulation, and load macros

All hardware runs used **card 0**. Final combined run: **76 passed in 4.40 s**;
queue job `df99c6a6bba443cfa2d0f27f9fadc546`.
[Machine-readable measurements](hardware_probe_results.json) retain individual
argmax/macro samples and packer medians. Times below are device cycles, not host
launch latency. These are tested experimental implementations; the model's
`decode_argmax` has not been switched over.

## 250,000-value argmax

A distributed BF16 argmax works with SFPU doing the main scan. The full test
uses **62 cores**, up to 4,096 logits per core, and a final 144-logit shard.
Input is face-tiled, with the final tile padded to negative infinity.
Both variants read identical data from one DRAM bank, send their local result
over NoC, and reduce the 62 results on the first core. No host reduction.

| 250,000-value input | RISC-V scan | SFPU hybrid | Speedup |
|---|---:|---:|---:|
| Random logits | 174,228.5 | 16,417.5 | 10.61× |
| Maximum at index 249,999 | 174,208 | 16,248.5 | 10.72× |
| Negative maxima tied across cores | 172,403.5 | 16,386 | 10.52× |

Medians of four retained launches after one warmup; variant order alternates.
Timing runs from the reducer's kernel entry through the final result, including
its DRAM transfer and waiting for every remote partial. Launch skew and NoC
contention are included; host uploads, firmware launch overhead before entry,
and host result download are excluded. The single-bank source is deliberately
identical for both algorithms; this does not measure the model's exact
interleaved logits layout or token-history/host-publication tail.

Local L1-input tests include unpacking, copying to Dst, SFPU work, packing
32 candidates, and the final RISC-V scan. Eight retained alternating launches:

| Local tiled BF16 count | RISC-V scan | SFPU hybrid |
|---|---:|---:|
| 1,024 | 44,148 | 2,343.5 |
| 2,048 | 90,331.5 | 2,894.5 |
| 3,072 | 135,537.5 | 3,450.5 |
| 4,096 | 176,632 | 4,011 |

The scalar baseline follows decode's BF16 sortable-key logic and tiled address
mapping, with an explicit minimum-index tie comparison. It is a standalone
baseline, not a timed invocation of the complete model program.

### Implementation and correctness

[`ttko/argmax.py`](../../../ttko/argmax.py) scans 32 values per vector using
`SFPSWAP` and paired index registers. `SFPLOAD` automatically captures the
physical Dst index. Each lane produces one candidate; RISC-V converts its
physical index back to logical tile order and reduces just 32 candidates.

Native `SFPSWAP` swaps equal **negative** operands, which would lose decode's
first-index tie behavior. The implementation first transforms each BF16 value
into a monotonic nonnegative integer key. Equal keys then keep the old index.
Traversal order also accounts for the tile's four-face layout. Disabling source
zero flags preserves the distinction between -0 and +0 during `MOVA2D`.

Coverage:

- 35 min/max tests: all ten swap modes, paired indices, exchange configuration,
  predication, positive/negative ties, signed zeros, five Dst capture positions.
- Argmax on both sequential and tiled input: random values, positive/negative
  ties, signed zeros, infinities, all negative infinity, subnormals, partial
  final tiles, and a winner at the final index.
- A full eight-tile/8,192-element Dst scan and output guards.
- Actual 250k global random, final-index, and cross-core negative-tie cases.

NaN semantics are not specified by this prototype. It targets BF16 logits.
The transport currently uses the existing paired-unpack helper, redundantly
loading the logits into SrcB as well as SrcA; removing that extra work is a
remaining optimization. The main scan helper is reusable, while transport and
multi-core orchestration remain in the raw hardware tests.

## Packer L1 accumulation

[`test_l1_accumulation.py`](../../movement/packer/test_l1_accumulation.py) proves
`L1[out] += Dst` for BF16 and FP32, at 16, 256, and 1,024 elements, with one or
four passes. Tests initialize L1 to nonzero signed values, include cancellation
and a whole zero face, and check guards on both sides of the output.

The required configuration is `Pack_L1_Acc` (word 71, bit 19) **and**
`Disable_pack_zero_flags` (word 70, bit 2). Both are cleared after the test.
Zero flags must not claim an accumulated output is zero merely because the
new Dst contribution was zero.

| Packing 1,024 values | Overwrite | Accumulate |
|---|---:|---:|
| FP32, one pass | 180 | 180 |
| BF16, one pass | 116 | 116 |
| FP32, four passes | 684 | 684 |
| BF16, four passes | 428 | 428 |

Every tested size had identical median overwrite/accumulate timing. Intervals
include destination setup, PACR/MOP execution, and completion drains; initial
unpacking and pack configuration are excluded. This demonstrates no additional
measured pack cost, not an end-to-end model speedup.

Useful next integration: accumulate spilled partial tiles directly in L1
instead of unpacking old partials, adding them, and packing again. FP32 L1
partials preserve more precision; BF16 accumulation rounds at each spill and
is not equivalent to keeping the entire sum in FP32 Dst. Numerical tests here
use exactly representable sums; arbitrary rounding/overflow remains untested.

## SFPLOADMACRO scheduling

[`test_loadmacro_pipeline.py`](test_loadmacro_pipeline.py) scales 8,192 signed
FP32 values by two and checks every output plus trailing guards.
Seven retained launches after one warmup:

| Schedule | Cycles |
|---|---:|
| Explicit load/multiply/NOP/store | 1,054 |
| Macro with three NOPs after every load | 1,164 |
| Four-register pipelined macros | **306** |
| Explicit Replay/MOP loop | 1,377 |
| Macro Replay/MOP loop | 597 |

The winning schedule is **3.44× faster** than explicit instructions. Macro 0
schedules multiplication at t+1 and store at t+3. Rotating L0..L3 allows the
next vector to load while earlier vectors compute/store, without overwriting
an outstanding store's register. Replay saves code size but the explicit
address increments and loop setup make it slower for this operation.

Both timing boundaries synchronize the issuing thread; the final boundary
waits for Replay/MOP and all delayed SFPU work. Earlier exploratory timings
without that synchronization are superseded by these results. The numbers
measure the Dst-to-Dst compute pass, excluding initial unpack, final pack, and
macro-template configuration. No RMSNorm/model speedup is claimed from this
isolated scale test. LUT exploration is deferred as requested.

## Reproduce

```sh
tt-device-queue run --device 0 --cwd /home/boop/tenstorrent/blackhole-py --timeout 120 -- \
  ../.venv/bin/python -m pytest \
  tests/movement/sfpu/test_minmax.py \
  tests/compute/sfpu/test_argmax.py \
  tests/compute/sfpu/test_argmax_vocab.py \
  tests/movement/packer/test_l1_accumulation.py \
  tests/compute/sfpu/test_loadmacro_pipeline.py \
  --bh-hardware --bh-device=0 -xqs
```
