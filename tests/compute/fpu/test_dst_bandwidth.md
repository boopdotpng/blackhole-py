# Dst throughput and cross-thread contention — 2026-09-11

Card 1, core index 2. Firmware fusion and instruction prefetch enabled.
Run `PYTHONPATH=. python3 -m pytest -q -s tests/compute/fpu/test_dst_bandwidth.py
--bh-hardware --bh-device=1 --bh-core=2` on one line.

## Single-engine payload rates

32-instruction Replay bodies inside MOP, 32/128/256 repetitions, seven measured
launches after warmup at each length. Reported rates use adjacent timing slopes;
initial unpack/configuration and final correctness packing are outside the
interval. Engine drain is inside it. No empty-loop subtraction.

| Operation | Cycles/instruction | Logical payload/cycle |
| --- | ---: | ---: |
| MOVA2D, eight rows | 1.5 | 341.3 bytes written as FP32 Dst |
| SFPLOAD, 32 lanes | 1 | 128 bytes from FP32 Dst |
| SFPSTORE, 32 lanes | 1 | 128 bytes to FP32 Dst |

Results match across TRISC0/1/2 and addresses distributed over 1/2/4 Dst tiles.
For MOVA2D, BF16 source payload is half the FP32 destination payload above.
These are instruction/payload throughput measurements, NOT physical bus widths.
The tile sweep fixes operation count: SFPU accesses total 1024 elements per
body, split across the selected tiles. It is not four full simultaneous tile
reads, nor multiple independent SFPU engines. Load/store lane addressing spans
even/odd columns of four rows; it is not simply 32 contiguous elements.

Loads preserve the final L0 vector for checking against patterned BF16 input;
stores and moves check the packed tile and output bounds.

## Contention control matrix

Here bodies use RISC loops with 16 operations per engine. Lengths are again
32/128/256 iterations, with five measured launches after warmup. Each slope
below is cycles per pair: one FPU operation and one SFPU operation.
The FPU writes Dst tile 1; SFPU loads/stores tile 0. No overlapping addresses.
ELWMUL is LoFi with exact ones operands, exercising FP32 Dst read-modify-write.
MAD is a dependent local-register accumulator with no Dst access in the body.

| FPU + SFPU | Batched, one thread | Interleaved, one thread | Concurrent, T1 + T2 |
| --- | ---: | ---: | ---: |
| MOVA2D + SFPLOAD | 2.5 | 7.25 | ~5.5 |
| MOVA2D + SFPSTORE | 2.5 | 7.25 | ~5.5 |
| ELWMUL + SFPLOAD | 2 | 8 | ~2 |
| ELWMUL + SFPSTORE | 2 | 8 | ~2 |
| MOVA2D + local MAD | 3.5 | 2 | ~2 |
| ELWMUL + local MAD | 3 | 2 | ~2 |

Single-engine controls: MOVA2D 1.5, ELWMUL/load/store 1, dependent MAD 2
cycles/instruction. All arithmetic/movement result checks pass.
The concurrent variant uses readiness/start/done mailboxes outside the repeated
body. Joint completion, including the end handshake, is timed. Slopes amortize
fixed startup cost; this is not a measurement of each physical memory port.

Repeating with SrcA counter increments enabled versus stationary modifiers
gives the same slopes. Dst counters are stationary in both cases, with immediate
addresses selecting distinct blocks. Each thread has its own RWCs.

Interpretation: numerical counter increments are not required for the penalty.
Per-thread scheduling/addressing effects matter (ELWMUL improves from 8 to 2
when split), but do not explain everything (MOVA2D still suffers across threads).
Register-only MAD overlaps well, implicating Dst-access interactions rather
than a blanket FPU/SFPU execution exclusion. Physical port arbitration versus
other shared hardware interlocks remains unresolved.

## Full RMSNorm experiment

`test_rmsnorm_hybrid.py -k fair` now also compares `split0` and `split2`:
FPU stays on TRISC1, while SFPU square accumulation runs on TRISC0 or TRISC2.
Math publishes scratch readiness, waits for the SFPU accumulator to finish,
then performs the unchanged finalizer/epilogue. Both paths retain correct output.

Representative median L1-to-L1 cycles (100 samples):

| N | Current queued | SFPU on T0 | SFPU on T2 |
| --- | ---: | ---: | ---: |
| 1024 | 830 | 864.5 | 870.5 |
| 2048 | 1118 | 1228 | 1184 |

This split implementation loses overall: handshake cost and, for T0, sharing
the loader thread outweigh any overlap. It is not proof that all cross-thread
or persistent multi-row schedules lose. Default remains the queued kernel.

## Fixed-work engine-switch frequency sweep

Run the same file with `-k switch_frequency`. One TRISC issues 32 ELWMUL and
32 SFPLOAD instructions per RISC loop iteration, preserving each engine's
address order. Only grouping changes; all grouped bodies have identical size
and loop control. Stationary counters, disjoint Dst0 reads / Dst1 accumulation.
The all-batched control runs all FPU iterations before all SFPU iterations.
Lengths: 32/128/256 iterations, 20 measured samples after two warmups, reversing
variant order on alternate launches. Correctness and output sentinels checked.

| Instructions per engine per group | Cycles per FPU/load pair |
| --- | ---: |
| 1 | 8 |
| 2 | 8 |
| 4 | 5 |
| 8 | 3.5 |
| 16 | 2.75 |
| 32 | 2.375 |
| All FPU, then all loads | 2 |

Both adjacent length slopes give exactly the same values. For group size
`g >= 2`, the measured rule is `cycles/pair = 2 + 12/g`: 12 excess cycles per
FPU-group/SFPU-group round trip, independent of group length. Counting both
switch directions, this averages six extra cycles per switch; it does NOT
establish that each direction individually costs six. Group size 1 is an
exception: it ties size 2 at eight cycles/pair rather than following the formula.

This supports a fixed cross-engine transition/interlock cost, not merely a
penalty proportional to traffic volume. It does not yet identify the internal
resource (RWCs versus another shared pipeline), and the size-1 exception argues
against treating the fitted formula as a complete RTL model.
