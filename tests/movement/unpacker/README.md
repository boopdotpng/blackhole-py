# Unpacker movement kernels

Handwritten, row-major L1 proofs for every unpacker bullet in
`docs/components.md`:

- runtime-sized F32 copies directly into FP32 Dst tiles 0 through 7;
- BF16 tile copies to SrcA and SrcB, copied through FP32 Dst only for readback;
- paired SrcA/SrcB programming and a cycle comparison with two individual
  unpack MOPs; and
- partial direct-to-Dst copies, including a half tile and a non-face-aligned
  tail. Blackhole's minimum direct-Dst footprint is one 16-element register
  row, so byte counts and offsets are exact in 64-byte F32 row units.

No path enables tileize mode or changes the ordering of the input stream.  The
direct-to-Dst MOP plays a two-word Replay for every fragment: `UNPACR` followed
by the hardware-required `STALLWAIT(UNPACK, UNPACK0)`.  Runtime byte counts use
one MOP for all complete 256-element fragments and at most one more MOP for the
tail, so generated code contains exactly one literal unpack instruction rather
than growing with the requested copy size.

## Cycle samples

One Blackhole run on device 1, worker 4 produced the following raw wall-clock
cycle counts.  The profiler markers surround the unpack primitive, including
its configuration and synchronization; no baseline is subtracted.

| operation | cycles |
| --- | ---: |
| direct F32 to Dst tile 0 | 326 |
| direct F32 to Dst tile 1 | 316 |
| direct F32 to Dst tile 2 | 314 |
| direct F32 to Dst tile 3 | 320 |
| direct F32 to Dst tile 4 | 316 |
| direct F32 to Dst tile 5 | 310 |
| direct F32 to Dst tile 6 | 312 |
| direct F32 to Dst tile 7 | 310 |
| partial: 16 elements at offset 0 | 247 |
| partial: 128 elements at offset 16 | 255 |
| partial: 256 elements at offset 256 | 247 |
| partial: 512 elements at offset 128 | 263 |
| partial: 768 elements at offset 32 | 283 |
| BF16 tile to SrcA | 261 |
| BF16 tile to SrcB | 234 |
| paired SrcA + SrcB | 449 |

The like-for-like comparison test measured 249 cycles for an individual SrcA
unpack plus 235 for an individual SrcB unpack (484 total), versus 436 cycles
for the parallel dual-unpacker MOP: 48 cycles faster in that sample.  Tests
print fresh measurements through `tests.profiler.Profiler` on every hardware
run; these numbers are a recorded sample, not fixed performance assertions.

## Direct Dst vs source-register staging

Run `PYTHONPATH=. pytest -q -s tests/movement/unpacker/test_dst_paths.py
--bh-hardware --bh-device=0 --bh-core=28` (on one shell line).

Nine cases pass on Blackhole device 0, worker 28. Each latency case measures
15 launches. Input is FP32 in L1 and output is FP32 in Dst for every path.
The staged paths explicitly convert FP32 to BF16 while unpacking to SrcA or
SrcB, then widen with MOVA2D/MOVB2D. Timing inputs are distinct values exactly
representable in BF16, so the three paths must produce identical bits.

| Path | 128 elements | 1024 elements |
| --- | ---: | ---: |
| Direct to Dst | 48 | 127 |
| SrcA then MOVA2D | 45 | 74 |
| SrcB then MOVB2D | 46 | 74 |

Numbers are median cycles from prepared unpack launch to math acknowledging
Dst ready. Configuration and zero initialization are outside the interval.
All paths include the same producer/consumer handshake and acknowledgement;
these numbers are not bare instruction latencies or steady-state throughput.
Packing the entire Dst tile to FP32 L1 happens after the timer; tests check
all values, untouched zeros for the partial case, and a trailing sentinel.
No DRAM data transfer is included.

The direct sequence uses one 128-element fragment or four 256-element
fragments, each followed by an unpack drain. The source paths unpack the
entire operand with one UNPACR, then use one/eight MOVA2Ds or two/sixteen
MOVB2Ds. Thus the full-tile result includes the existing direct path's
fragment/drain overhead. It does not establish an architectural lower bound
for direct unpack, and it is not a BF16-input bandwidth comparison.

Three additional tests use FP32 values with nonzero low mantissa bits:
direct unpack preserves every bit; the explicitly BF16-configured source
paths truncate those bits as expected. Source registers also support TF32
and FP16; BF16 is the chosen staging format here, not their only format.
Retain direct-to-Dst when arbitrary FP32 precision must survive the load.
