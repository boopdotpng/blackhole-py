# SFPU individual arithmetic recipes

Current selection: **74 cases** after removing four duplicates; all retained
cases are included in the historical 78-case run below. See the
[overlap review](../review.md). No operation or assertion changed.

Validation status: final suite **78 passed**, physical card 0/core index 1
`(1,3)`, queue job `5a833c0cd88440328d4af1a1bebd849b`. All cases retain seven
samples, matched controls and firmware context in `final-results.json`.
Exception tests characterize unsupported inputs; they do not establish complete
IEEE numerical semantics. Historical baseline and recovery are in `results.md`.

`emit.arithmetic(k, op, dst, other=1, addend=2, mode='refined', scratch=(3,4,5,6))`
emits an **in-place LReg operation**, matching `SFPURegister` receiver semantics.
It does not modify `ttk/model.py` or provide a compiler. Inputs are FP32 in explicit
LRegs; dst must be L0–L7. Basic other/addend sources may be L0–L15 and may alias dst.
Numerical scratch is explicitly caller-owned and must not overlap live values.
`emit.drain(k)` orders SFPU completion before a RISC consumer or cycle marker.

| Public operation | Raw implementation / vector instruction count | Scratch | Precision and contract | Proof |
|---|---|---|---|---|
| add | SFPADD / 1 | none | FP32 nearest-even, input/output denormals flushed | operations, masks, aliases, repeated |
| sub | SFPADD NEGATE_VC / 1 | none | As add, receiver minus other | same |
| mul | SFPMUL with L9=0 / 1 | none | FP32 nearest-even, denormals flushed | same |
| mad | SFPMAD / 1 | none | Receiver*multiplier+addend; hardware partially fused FP32, not IEEE exact FMA | same |
| neg | SFPMOV NEGATE / 1 | none | Toggle sign bit, including signed zero and NaN | operations, masks, repeated |
| abs | SFPABS FLOAT / 1 | none | Clear sign except negative NaNs remain negative NaNs | same |
| reciprocal native | SFPARECIP / 1 | none | 0.6% relative bound for normal 2^-126 ≤ abs(x) < 2^126 | native, boundaries |
| reciprocal refined | seed then two Newton steps y*(2-x*y) / 8 | first 3 scratch LRegs | 3e-7 relative bound on same domain, independent FP64 reference | operations, masks, boundaries |
| exp native | Preserve input, SFPARECIP EXP then conditional reciprocal / 3 | first scratch LReg | Computes approximation to **e^x**, including negative x; 2.5% relative bound for abs(x)<2 | native, shared-domain comparison, boundaries |
| exp refined | Degree-8 Taylor of x/256, eight squarings / 36 | first/third scratch LRegs | 8e-5 relative bound on tested [-87,87]; no exact-rounding guarantee | operations, masks, shared-domain comparison, boundaries |

Counts include numerical constant loads, but exclude caller load/store/predicate and
completion. Native exp is not the sign-preserving exponential instruction alone.
Reciprocal's two Newton steps improve the native LUT seed; exp refined uses a
separate polynomial method to extend the useful domain. No host replaces a
per-element computation. Constants only are assembled on the host.

The accuracy bounds are declared contracts tested on structured samples, **not an
exhaustive proof across every FP32 bit pattern**. FP64 Python `math.exp` and `1/x`
are independent references. Reports include the input/output/reference at the
worst relative error and its absolute/ULP error. ULP distance compares with the
nearest FP32 reference. MAD's exact dyadic cases do not imply general exact-FMA
conformance; the architecture's partially fused semantics remain applicable.
The 16-call MAD chain compares against an independently rounded FP64 oracle with
an explicit final bound of 16 ULP for these noncanceling inputs; observed worst
relative error was 1.71e-7 (2 ULP). It originally failed an exact-FMA assertion.
Single-call dyadic MAD tests still require exact results. The chain bound is a
test-specific accumulated-rounding allowance, not a general MAD accuracy claim.

## Ownership and state

No operation reads or writes Dst, SrcA or SrcB. Callers separately load/store their
owned FP32 allocation. Tests operate on all four 32-lane positions in 128-element
slots, with receiver placements 0, 7 and 63 and independent input slots 0, 4, 17,
57 and 63. FP32 slot s means physical allocator units (2s,2s+1); raw SFPU row is
8*s+2*position. All 8192 FP32 Dst elements are initialized with distinctive poison
in the fixture, and **all non-output Dst elements** are compared after execution.
The operation itself does no whole-bank initialization. L1 input at 0x50000 owns
32768 bytes; observation output at 0x60000 owns 32768+64 bytes. The 64-byte output
sentinel is checked. Profiler storage is its default reserved last 32 bytes of L1.

Emitters preserve incoming predicate state, touch active lanes only, and do not
use the predicate stack. The fixture constructs all-on, all-off, alternating,
and lane-17 masks from an owned slot31 vector of ±1. Predicate creation is outside
the operation timer and is not claimed as a movement/control implementation.
Inactive receiver lanes must remain unchanged. L9=0/L10=1 architectural constants
and SFPU FP32 config are assumed. The harness configures address mode0 and zero
RWC; those reusable settings precede timing.

## Timing

Every case schedules one warmup and seven correctness-checked measured launches. Main
intervals cover the LReg operation and `Wait.SFPU`/`pc_sync` completion. Four vector
intervals are accumulated per allocation. `test_repeated_short_operations` emits
16 dependent calls per vector (K=64 total), with no device loop overhead; it tests
the resulting repeated computation. Raw counts remain authoritative; no marker
cost is subtracted. Single-operation intervals are substantially marker/drain
overhead. Numerical constant setup is included on each call. Dst transfers and
fixture mask setup are outside this register-operation contract.
The `empty` record pair measures timestamp/store overhead; `control` accumulates
four empty operation intervals containing the same SFPU drain as the measured
operation. Both controls are retained separately without subtraction.

## Explicit gaps

These are bounded numerical implementations, not complete IEEE exp/reciprocal.
`test_exception_characterization` reports zeros, denormals, smallest normals,
2^126, largest finite, infinities and signed NaNs for both modes. It validates
preservation and collects measurements; its passing status **does not establish
correct mathematical results on unsupported inputs**. In particular, Newton
refinement can produce NaNs for zero/infinite inputs; native reciprocal maps NaN
to signed zero and flushes large arguments; exp's native LUT saturates outside
its useful range and the polynomial has no infinity/overflow/underflow repair.
The recorded exception ledger makes these gaps visible for future lowering.
General arithmetic special-value behavior follows the cited ISA but is not yet
exhaustively tested here; full normal-domain random rounding stress is deferred.

Sources: local `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/`
VectorUnit, SFPMAD, SFPARECIP, SFPLOAD and linked Wormhole SFPMOV/SFPABS pages.
See `results.md` for exact queue evidence and measurements.
