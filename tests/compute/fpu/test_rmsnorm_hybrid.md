# RMSNorm transport cleanup, 2026-09-11

Measured on card 1, core index 2, after a card-1-only `tt-smi` reset.
Run `PYTHONPATH=. python3 -m pytest -q -s tests/timing/test_firmware_cache.py
tests/compute/fpu/test_rmsnorm_hybrid.py --bh-hardware --bh-device=1 --bh-core=2`
(join the command onto one line). Seven tests passed.

Firmware previously set CSR `cfg0.DisTriscCache` and zeroed backend
`RISC_PREFETCH_CTRL` on every launch. The build wrapper now enables fusion
and restores prefetch after each backend reset, leaving the reference source
snapshot intact. Live reads on all 117 compute workers confirmed TRISC
`cfg0=0x20008` and prefetch control `0x11f` (all five RISCs, eight requests).
BRISC/NCRISC `cfg0=0x60008`; bit 18's TRISC fusion function is irrelevant there.

Median L1-to-L1 cycles, 20 normal-input samples after warmup:

| Variant | N=1024 | N=2048 |
| --- | ---: | ---: |
| llama3 arithmetic port, diagnostic export retained | 1369 | 2141.5 |
| Original hybrid, diagnostic export retained | 1126.5 | 1600 |
| Hybrid, no scale export | 834 | 1301.5 |
| Default hybrid, no export + unpack config reuse | 840.5 | 1122 |
| Same, explicitly serialized FPU/SFPU | 837 | 1120 |
| Same, instruction-interleaved FPU/SFPU | 1174.5 | 1796 |

Default compute/pack intervals: 245/199.5 cycles at 1024, 410/310 at 2048.
The 2048 compute interval includes second-tile staging. Total timing includes
the same unpack/pack setup as before; setup was not moved outside the timer.
Launch, firmware initialization, host transfer, and NoC are excluded.

The no-export path skips the FP32 scale store, diagnostic packing, runtime
partial-row branching, and F32-to-BF16 packer reconfiguration. Reusing unpack
descriptors/MOP saves second-tile setup; only bases and Z/W counters change.
For 1024 there is no second tile, so reuse is not an expected speedup; small
differences between these variants reflect scheduling/layout/timing variation.

Arithmetic is unchanged. Arange, normal, tiny, zero, and outlier inputs with
signed gamma passed FP64-reference checks on BF16-quantized operands. Worst
relative output errors were 0.38433% / 0.38814%, unchanged across variants.
The reference scale is checked only in diagnostic variants; optimized variants
instead assert the entire diagnostic buffer remains untouched. Output bounds
are checked with sentinels.

The llama3 total still includes its diagnostic export: do not attribute the
entire total-time advantage to arithmetic. Queued versus serialized remains
essentially tied, and fine-grained interleaving remains substantially slower.

## Fair output-only comparison

Both kernels now call the same `_unpack_reused` and `_pack_output` helpers.
The llama3 arithmetic, replay/MOP schedule, rsqrt, and apply macro are unchanged.
Neither exports scale. Dst layouts remain algorithm-specific; copying gamma
into Dst is necessary for the SFPU baseline, not added artificial overhead.
Both timers begin before first unpack setup and end after final pack drain.
Math initialization before that interval, firmware, host, and NoC are excluded.

Reproduce with `PYTHONPATH=. python3 -m pytest -q -s
tests/compute/fpu/test_rmsnorm_hybrid.py -k fair
--bh-hardware --bh-device=1 --bh-core=2` (one line).
Each run takes 100 measured normal-input samples per kernel after warmup,
alternates execution order, and checks arange/normal/tiny/zero/outlier inputs
with signed gamma against the same FP64 reference and output tolerance.
Both scale buffers must remain untouched and output sentinels must survive.

First run, median cycles:

| N | llama3 output-only | Hybrid | Speedup | Fewer cycles |
| --- | ---: | ---: | ---: | ---: |
| 1024 | 1073 | 825 | 1.301x | 23.11% |
| 2048 | 1563 | 1105 | 1.414x | 29.30% |

A second run gave 1073/827 and 1564.5/1112 respectively (22.93%/28.92%
fewer cycles). Both pack medians match: 193 cycles at 1024, 305 at 2048.
Worst relative output errors still match: 0.38433% and 0.38814% respectively.
The ablation and original llama3 correctness tests also pass (six tests).
This is a fair comparison of the raw L1-to-L1 implementations, not a timed
production llama3 model run. The 2048 compute subintervals have different
staging boundaries, so compare total intervals, not compute alone.

## Macro square accumulation (now the default)

All math remains on TRISC1. Each scratch tile now needs 32 SFPLOADMACRO
instructions instead of 32 explicit SFPLOAD/SFPMAD pairs. Four templates use
two independent, ping-pong accumulator chains: L0/L2 and L1/L3. A macro loads
x into register r, then schedules `Lr = x*x + L(r xor 2)` one cycle later.
This accommodates forced macro destination remapping and gives dependent MADs
two cycles of spacing. Macro MADs do not provide automatic dependency stalls.
After a complete tile, the current sums reside in L2/L3; these survive across
tiles. Three NOPs drain scheduled work; the final L2+L3 sum goes into L7 for
the unchanged llama3 finalizer. Macro 0 is then reused for output scaling.

Changing summation order is not bitwise-equivalent in general. The existing
five input families pass, and a separate test covers 12 random seeds, signed
gamma, scales from 1e-8 to 1e8, and lognormal dynamic ranges at each size.
Worst macro scale errors: 0.0000100% / 0.0000055%; worst output relative errors:
0.38669% / 0.38868% (N=1024/2048). Six tests passed on card 1, core index 2.

Second run, same fair output-only comparison, 100 measured samples:

| N | Explicit load/MAD hybrid | Macro hybrid | llama3 output-only |
| --- | ---: | ---: | ---: |
| 1024 | 834 | 793.5 | 1072 |
| 2048 | 1104 | 1041 | 1563 |

Macro compute medians: 225 / 360.5 cycles. Pack medians remain 193 / 305.
Initial math/macro configuration is before the timer, as in the original
benchmark; switching from square macros to the output macro IS timed.
Unpack/pack setup remains timed. No double-buffered next-tile prefetch was
added. Explicit load/MAD and split-thread variants remain benchmark controls;
the default `_images(n)` selects the macro version with queued math on TRISC1.

## Explicit source-bank double buffering (default)

The default now prefetches x/gamma into the alternate SrcA/SrcB banks while
TRISC1 processes the current tile. It reuses descriptors and the unpack MOP,
updates only tile bases/counters, and uses one pending completion credit plus
hardware bank-valid bits. All math remains on TRISC1. The same prefetch option
is enabled for the fair output-only llama3 baseline.

Card 1, core index 2, 100 measured samples after two warmups, median L1-to-L1
cycles (same macro arithmetic and packing):

| Elements | Sequential | Double-buffered |
| --- | ---: | ---: |
| 1024 | 787 | 786 |
| 2048 | 1085 | 1032 |
| 3072 | 1379 | 1278 |
| 4096 | 1686 | 1525 |

4096 is the hidden dimension in the sibling blackhole-py-llama3-8b model.
All five input families produce bit-identical output between the two schedules;
outputs meet 0.4% relative tolerance against FP64. Pack medians are unchanged:
193/305/417/529 cycles. Instrumented wall-clock traces separately confirm that
unpacking the next tile overlaps current-tile math; these trace writes are not
included in the above timings.

Important historical correction: the former nominally sequential reused-unpack
helper waited with only Stall.UNPACK. A subsequent semaphore wait could replace
that wait, so it already allowed accidental prefetch. The explicit sequential
control now also blocks Stall.SYNC. Thus the 9.5% improvement at 4096 is versus
the corrected truly sequential control, not a 9.5% improvement over the previous
accidentally overlapping implementation. The single-tile difference is noise,
not evidence that double buffering is universally free.

Regression checks: 41 tests passed (hybrid, standalone llama3, and Dst payload
tests). Split-thread controls now drain math before signaling scratch readiness;
the Dst load diagnostic explicitly initializes untouched lanes rather than
assuming ZEROACC invalidation physically clears them.
