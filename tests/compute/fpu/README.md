# FPU compute kernels

Split handwritten FPU PoCs into matmul, elementwise/broadcast, and reduction
test files.

## Mean of materialized FP32 arange(1024)

```sh
PYTHONPATH=. /home/boop/tenstorrent/.venv/bin/python -m pytest -q -s \
  tests/compute/fpu/test_mean.py --bh-hardware --bh-device=0 --bh-core=27
```

Eight tests pass on Blackhole device 0, worker 27 (2026-09-05). This is the
reduction in `Tensor.arange(1024).mean()`, with the input materialized as FP32
in L1. It does not invoke tinygrad, generate arange on device, or substitute
the closed-form answer. The exact sum is 523776 and the mean is **511.5**.
The existing worker 27 initially stalled even on an old GAPOOL test; resetting
device 0 with `.venv/bin/tt-smi -r /dev/tenstorrent/0` restored it.

Median wall-clock cycles over seven launches, with no overhead subtraction:

| Input / reduction | Reduction to Dst | Prepared L1 to L1 |
| --- | ---: | ---: |
| SrcA GAPOOL, final SFPU scaling | 106 | 221 |
| SrcA MVMUL, final SFPU scaling | 106 | 221 |
| SrcB MVMUL, final SFPU scaling | 141 | 256 |
| SrcA GAPOOL, scale folded into weights | **104** | **219** |
| SrcA MVMUL, scale folded into weights | **104** | **219** |
| SrcB MVMUL, scale folded into weights | 139 | 254 |
| Direct FP32 Dst, SFPU-only reduction/scaling | 128 | 288 |

The reduction interval includes matrix Replay where used, the FPU-to-SFPU
dependency wait, SFPU final reduction/scaling/store and completion drain.
Unpack and math configuration, Replay recording and initial Dst zeroing happen
before the intervals. The wider interval includes the source unpack (data and
weight banks for FPU), handshakes, both reduction markers, and the existing
pack helper's configuration and completion to a 16-float L1 row. Only the first
float is the scalar output; the remaining row is scratch. Host staging, launch,
DRAM/NoC transfers, and profiler export are excluded. An empty marker pair
measures 12 cycles. These are latency comparisons of these concrete schedules,
not peak throughput or a claim of globally optimal lowering.

### How the reduction works

With data in SrcA, four 16x16 chunks accumulate into the same Dst row. SrcB's
first row contains ones and its remaining rows contain zeros. Each GAPOOL
computes `D[0,j] += sum_k A[k,j]`; MVMUL computes the same useful row and four
additional zero rows. Fidelity phases 0 and 1 give eight matrix instructions
total. The final sixteen FP32 column sums are loaded into two SFPU vectors,
added together, and reduced within one eight-lane SFPU row. There is no
unnecessary reduction across the three zero SFPU rows.

With data in SrcB, eight 8x16 chunks multiply a SrcA matrix whose first column
is ones and remaining columns are zeros. MVMUL accumulates eight row sums in
Dst column zero. Fidelity phases 0 and 2 recover the two B mantissa portions;
the constant A has no low contribution, so phases 1 and 3 are unnecessary.
This takes sixteen matrix instructions. Two SFPU loads at addresses 0 and 4
cover the eight nonzero partials; an add, register transpose and three adds
finish the scalar. No horizontal lane reduction is needed on this path.

Thus **MVMUL's doubled output-row capacity does not halve the work for input
in SrcA**: both instructions consume a 16x16 A matrix per phase. With input in
SrcB, MVMUL consumes 8x16 values per phase, whereas GAPOOL exposes only 4x16.
The latter also aligns its B footprint to eight rows, so merely stepping by
four would reread the same half-block. This PoC uses MVMUL for B input.

The final division by 1024 is an exact power-of-two multiply. Putting 1/1024
in the matrix weights eliminates that final SFPU multiply and saves two cycles
here. This is a compiler fusion opportunity; it does not require a `mean`
hardware primitive. The unscaled paths demonstrate sum followed by scaling.

### Where precision is lost

All paths accumulate in **FP32 Dst**. FPU paths unpack FP32 input to TF32
source registers, which preserve the tested integers; the final reduction
stays in FP32 SFPU and never narrows the partial sums through SrcA/SrcB.
This does **not** establish arbitrary FP32-input accuracy: TF32 has fewer
mantissa bits, and A/B multiplication fidelity is asymmetric. The direct
FP32-to-Dst SFPU path preserves input bits and provides a separate baseline.

The retained BF16 control changes only source unpack format/strides and
returns **510.625**. This exactly matches reducing the BF16-truncated input:
bits were discarded before FP32 accumulation. BF16 round-to-nearest happens
to give mean 511.5 for this particular arange, so checking that answer alone
would not prove the original inputs were preserved.

Every main path additionally checks a signed shuffled input (mean -0.5) and
32 sparse inputs covering all eight source blocks, both SFPU lane parities,
and block boundaries. Every run checks the untouched 64-byte output sentinel.

## HiFi2 ELWMUL source slot placement

```sh
PYTHONPATH=. pytest -q -s tests/compute/fpu/test_elwmul_slots.py \
  --bh-hardware --bh-device=0 --bh-core=27
```

Four cases multiply two 256-element BF16 vectors, each split into two
128-element source slots. They accumulate into the same two FP32 Dst slots:

- contiguous: A `(0, 1)`, B `(0, 1)`;
- opposite ends: A `(0, 7)`, B `(0, 7)`;
- opposite ends with mismatched slot numbers: A `(0, 7)`, B `(7, 0)`;
- contiguous with mismatched slot numbers: A `(0, 1)`, B `(6, 7)`.

Each logical operation issues four ELWMULs: two output blocks at fidelity
phase 0, then the same blocks at phase 1 (HiFi2). Preconfigured address
modifiers advance A and B independently; scattering adds no instructions to
the timed loop. Source banks stay owned by math throughout the loop.

Dst starts with nonzero values, and the loop performs 64 accumulations without
clearing it. Exact FP32 output is checked against `initial + 64 * A * B`, then
the sentinel after the packed L1 output is checked. A uses mantissa bits that
require the second fidelity phase; B is chosen to fit the high B phase used
by HiFi2. All intermediate sums are exactly representable. This avoids
confusing HiFi2 truncation with source-addressing failures.

The unpacker initializes Dst directly and loads complete A/B banks containing
the selected operands plus nonzero distractors. Loading, address-modifier
configuration, and packing are outside timing. Timing includes the math MOP,
Replay overhead, and final completion synchronization, divided by 64. Seven
launches are measured per case. Only two Dst blocks are reused, so ordinary
accumulator dependencies are included; this is not a peak-FPU-throughput test.

Device 0, worker 27 sample (median cycles per 256-element HiFi2 accumulation):

| Placement | Cycles |
| --- | ---: |
| Contiguous | 16.891 |
| Opposite ends | 16.875 |
| Opposite ends, mismatched A/B slots | 16.766 |
| Contiguous, mismatched A/B slots | 16.797 |

All four cases passed. These small differences do not show a meaningful
source-scattering penalty; timings are reported rather than asserted.

## Arithmetic source placement and operand footprints

```sh
PYTHONPATH=. pytest -q -s tests/compute/fpu/test_arithmetic_slots.py \
  tests/compute/fpu/test_elwmul_slots.py --bh-hardware --bh-device=0 --bh-core=27
```

22 cases pass on Blackhole device 0, worker 27. ELWADD represents add/sub;
DOTPV is deliberately omitted. This covers normal arithmetic modes, not all
broadcast, integer, argmax, move, or legacy opcodes.

The tests compare two operations with adjacent operands, distant operands,
and independently placed A/B operands. Multiplications use HiFi2 and nonzero
FP32 accumulators. Add uses destination accumulation. Max uses existing Dst
values and verifies the three cleared rows. Unused output rows and the output
sentinel are checked. Each case has seven launches of 64 repetitions; unpack,
configuration, and FP32 packing to L1 are outside the timer. No DRAM transfer
is measured. Source address changes are folded into instruction modifiers.

Sample median cycles per pair of operations (including loop and drain overhead):

| Instruction | Adjacent | Distant | Distant, mismatched A/B |
| --- | ---: | ---: | ---: |
| ELWMUL, HiFi2 | 16.875 | 16.875 | 16.766 |
| ELWADD, accumulate | 10.891 | 10.891 | 10.766 |
| MVMUL, HiFi2 | 16.875 | 16.891 | 16.781 |
| GAPOOL, HiFi2 | 16.875 | 16.875 | 16.766 |
| GMPOOL | 10.891 | 10.875 | 10.781 |

There is no measurable source-distance penalty in this schedule. This does
not measure peak throughput or the cost of arbitrary address reconfiguration.

| Instruction | A read | B read | Dst written |
| --- | --- | --- | --- |
| ELWADD / ELWMUL | 8x16 | 8x16 | 8x16 |
| MVMUL | 16x16 | 8x16 | 8x16 |
| GAPOOL | 16x16 | 4x16, at an 8-row boundary | 4x16 |
| GMPOOL, no argmax | 16x16 | 1x16, at an 8-row boundary | 1x16 maxima, then 3x16 zeros |

GAPOOL computes `Dst += B @ A`, like MVMUL with four output rows instead of
eight. It can implement sum/average pooling through the B weights; it does
not automatically divide by the reduction size. GMPOOL takes a maximum over
the 16 A rows for each column, then maxes that against the first Dst row.
B supplies per-input-row exponent scaling; these tests use B=1 to disable it.

In units of 128 elements, MVMUL/GAPOOL/GMPOOL require one aligned pair in A,
one slot in B, and one slot in Dst under the proposed allocator. Only the
instruction footprint must be contiguous; separate operations may be distant.
A/B slot numbers need not match.

An additional hardware probe placed MVMUL/GAPOOL operands at odd slot starts
and failed correctness. The retained regression cases instead put operands at
A slots `(0,1)` and `(4,5)` while setting A counters to slot starts 1 and 5:
both pass, demonstrating rounding down to an even slot. Thus Blackhole A
pairs are `(0,1)`, `(2,3)`, `(4,5)`, `(6,7)`, not arbitrary adjacent slots.
This is stricter than the `& 0x38` A-row expression currently in the local
shared MVMUL documentation. One MVMUL cannot gather its two A halves from
separate source slots.
