# Allocation-scoped FPU recipes

`emit.prepare(k, op, a, b, dst, broadcast=0, accumulate=True, fidelity=2,
repeats=16, fp32=True)` configures a stationary operation batch;
`emit.execute(k)` runs it and drains math using `STALLWAIT(SYNC, MATH)` and
`pc_sync`. These are raw assembly emitters, with no host-computed device result.
Final hardware evidence covers all eleven operations: 224 cases pass with
seven cycle samples each, including FP32 and BF16 Dst; see [results.md](results.md).

A/B slot indices are 0..7 and each means eight rows of sixteen elements.
FP32 Dst indices are 0..63, each owning two adjacent aligned 16-bit allocation
units (128 FP32 values). BF16 Dst indices are 0..127, one 16-bit unit each.
Dst instruction row address is `dst * 8` in its configured format. Matrix
operations require even A starts 0, 2, 4, 6 and an independently selected B slot.
`broadcast`: 0 normal, 1 column-zero, 2 row-zero, 3 scalar B[0,0].

| Operation | Reads and exact writes | Numerical/accumulator contract | Replay words per call | Correctness test |
|---|---|---|---:|---|
| elwadd | A128, B128 allocation; Dst128 | `D=A+B` or `D+=A+B`; all four broadcasts | 1 | `test_operation[elwadd-*]`, `test_bf16_dst[elwadd-*]` |
| elwsub | A128, B128 allocation; Dst128 | `D=A-B` or `D+=A-B`; all four broadcasts | 1 | corresponding `elwsub` cases |
| elwmul | A128, B128 allocation; Dst128 | `D+=A*B`, HiFi2 phases 0,1; all broadcasts | 2 | corresponding `elwmul` cases |
| mvmul | A256, B128; Dst128 | `D+=B@A`; public LoFi phase 0 or HiFi2 phases 0,1 | 1 / 2 | corresponding `mvmul` cases |
| gapool | A256, first B64 of owned B128; first Dst64 | `D[0:4,:]+=B[0:4,:]@A`; last Dst64 preserved | 2 | corresponding `gapool` cases |
| gmpool | A256, first B16 of owned B128; first Dst64 | B=1 contract: first row `max(D,rowmax(A))`; next three rows cleared; last Dst64 preserved | 1 | corresponding `gmpool` cases |
| zero | No source data; eight selected Dst rows invalidated | Packer reads zero; FPU sees operation identity. **Not initialized zero storage for SFPU reads.** | 8 | corresponding `zero` cases |
| a2d | A128 to Dst128 | overwrite, BF16 to FP32 widening / BF16 pass-through | 1 | corresponding `a2d` cases |
| b2d | B128 to Dst128 | same conversion; two four-row halves at offsets 0,4 | 2 | corresponding `b2d` cases |
| d2a | Dst128 to A128 | overwrite, FP32 to BF16 truncation / BF16 pass-through; offsets 0,4 | 2 | corresponding `d2a` cases |
| d2b | Dst128 to B128 | same conversion and halves as d2a | 2 | corresponding `d2b` cases |

Source formats are BF16, with valid banks already owned by math. The caller
must finish source unpack, configure matching math/Dst formats, clear or own
lane write masks, and hold source ownership through execution. `prepare`
clobbers thread configuration indices 1,11,12..14,28..30,47..49; math RWCs and
fidelity; Replay beginning at 0 (up to eight words); and MOP configuration.
Static format setup and ownership handoff belong to the caller. `execute`
does not release banks or publish Dst. A subsequent consumer may use the
drained result; ZEROACC needs its special identity/undefined-row contract.
No whole-bank loads or clears occur inside these emitters. No L1 operand
scratch is required by the operation; assembly helpers allocate RISC registers.
No low-half (`UseDst32bLo`) or FP16/integer conversions are claimed.

`fixture.py` deliberately initializes all source and Dst allocations outside
timing, then observes complete Dst tiles and A/B guards in separate launches.
Observation consumes one explicitly owned 1024-element Dst scratch tile after
measurement. Each observed tile is checked against a pristine reference;
all other physical Dst tiles are separately checked, and the output sentinel
is checked. This catches writes but does not alone prove absence of reads:
the emitter's explicit row addresses and documented masks define reads.
`observation.py` is a local copy of the existing pack fixture with its tile
validation extended to all sixteen physical BF16 tiles and its Dst read width
set explicitly for native BF16 storage, not a production pack
primitive. No mutable transport-agent helper is imported.

Fixtures use L1 INPUT at DATA_BUFFER_SPACE_BASE (4096 bytes), A at +4096
(2048), B at +6144 (2048), output at +8192 (4160 including guards), and the
Profiler's reserved final 32 bytes of DATA_BUFFER_SPACE. Profiler validates
that its storage does not overlap initialization. Fixture setup uses broad
source/Dst transport solely for poisoning and observation.

Timing retains one warmup and seven measured launches. `operation` encloses
MOP execution and required math drain. `complete` additionally includes
per-batch configuration, Replay recording, MOP setup, synchronization and the
nested operation markers. Neither includes fixture staging/unpack/pack or
host launch. FP32 K=16 is repeated dependent accumulation/overwrite with
Replay/MOP and marker overhead; BF16 K=1 avoids precision loss from repeated
16-bit accumulation. `complete/K` is **amortized batch cost**, not independent
per-call configuration latency. `control` is an empty marker pair, reported
raw without subtraction. No fixed timing assertions are used.

FP32 references use signed binary fractions with exactly representable
intermediates; HiFi2 tests exercise low A mantissa bits with B restricted to
its high phase. LoFi controls use powers of two to isolate placement from
precision truncation. BF16 tests use small exactly representable signed
integers. The final FP32 d2a/d2b fixture adds non-BF16 Dst fractions to verify
truncation, correcting the prior fixture's already-BF16 inputs. Arithmetic
NaN, infinity, subnormal, overflow and signed-zero bit policies remain
uncharacterized; these recipes claim the finite domains above only. General
GMPOOL B exponent scaling is not covered by the B=1 baseline.

Device-free assembly of `prepare`+`execute` at A6/B7/Dst63, FP32 K16,
HiFi2 (default add accumulation), uses 22 virtual temporaries allocated to
2 physical RISC registers. Assembled sizes including the Asm return sequence:
add/sub/gmpool 308 bytes; mul/mvmul/gapool 312; zero 284; a2d 256;
b2d/d2a/d2b 260. Counter positioning makes sizes placement-dependent. These
are complete emission-unit sizes, not the Replay instruction counts in the
table and not the broad fixture/profiler register footprint.
