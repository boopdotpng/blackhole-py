# SFPU API sketch

`ttk/model.py` records intent; these additions have no instruction lowering or
hardware validation yet. The scope comes from `components.md`. Register methods
mutate their receiver and return it. Every operation respects the active predicate,
except predicate replacement itself. Cross-lane operations need their native
predicate semantics accounted for by lowering.

```python
s = SFPU().predicate()  # all lanes enabled
s.l0.load(d, block=0, position=0)
s.l1.load(d, block=0, position=1)
s.l2.copy(s.l0)
s.l2.add(s.l1)
s.l2.sub(s.one)
s.l2.mul(s.l1)
s.l2.mad(s.l1, s.l0)  # l2 = old_l2 * l1 + l0
s.l2.add_scalar(5)
s.l2.mul_scalar(0.5)
s.l2.neg().abs()
s.l2.store(d, block=0, position=0)
```

Numeric constants retain FP32 precision; `loadi` may need two instructions.
`load_bits` instead records an exact 32-bit integer/opaque bit pattern:

```python
s.l4.loadi(math.pi)       # FP32 bits 0x40490FDB, not a BF16 approximation
s.l5.load_bits(0x12345678)
```

The existing `examples/llama3.py::_sfpu_float_words` uses SFPLOADI LOWER (mode
10) and UPPER (mode 8) to install the two halves of a float. For pi those halves
are 0x0FDB and 0x4049. Constants such as 5 can use a single BF16 immediate.

Comparisons write integer 0/1 masks, separate from execution predication:

```python
s.l2.copy(s.l0).compare(s.l1, "lt")
s.l3.copy(s.l0).select(s.l2, s.l1)  # l3 = mask ? l3 : l1
s.predicate(s.l2)                 # replace predicate with register != 0
s.l0.add_scalar(5)
s.predicate()                    # restore all lanes
s.minmax(s.l0, s.l1)              # l0=min, l1=max
s.compare_exchange(s.l0, s.l1, s.l2, s.l3)
# Descending values, ascending original indices for ties; updates all four.
```

Comparison names: eq/ne/lt/le/gt/ge. Native floating-point total ordering and
special values need explicit treatment by lowering; do not assume host IEEE
min/max semantics. Compare/select and indexed compare-exchange may be multi-op.

```python
s.l0.integer(s.l1, op="add", signed=False)  # add/sub
s.l2.integer_compare(s.l3, "ge", signed=True)
s.l0.mul23(s.l1, part="low")               # low/high; NOT a full 32-bit multiply
s.l0.bitwise("xor", s.l1)                  # and/or/xor/not
s.l0.bitshift("right", 3)                  # logical bit shift inside each lane
s.l0.exponent()
s.l1.mantissa()
s.l2.set_exponent(s.l0)
s.l2.set_mantissa(s.l1)
s.l2.set_sign(s.l3)
s.l2.scale_pow2(-2)
s.l2.cast("f32_to_i32", rounding="toward_zero")
```

Cast records retain explicit conversion and rounding strings for later lowering.
The kernel suite will determine supported conversion/rounding combinations.

Lane movement uses the hardware 4x8 lane layout, not row-major tensor indexing:

```python
s.l0.rotate(1, group_width=8)
s.l1.shift_lanes_right(1, group_width=8)  # zero fill, no wrap
s.l2.broadcast(s.l0, lane=0)
s.l0.butterfly(distance=2, group_width=8) # old x + rotated old x
s.transpose()                          # affects BOTH l0-l3 and l4-l7
```

Broadcast and some shift distances/group widths require composed sequences.
A scan or reduction must explicitly propagate values between eight-lane groups
and between vectors. `transpose` is the native cross-register transpose within
each lane column, not a tensor transpose.

```python
s.lut(s.l0, (s.l1, s.l2, s.l3), table_format="fp32_3", retain_sign=True)
s.l0.reciprocal_estimate()
s.seed(123)
s.l0.rng_bits()
```

LUT coefficients are register references; lowering arranges the instruction's
fixed operand registers. Table formats correspond to the components checklist,
including packed coefficient tables and FP32 tables. RNG here is the hardware
PRNG; reproducibility and seed programming still need hardware validation.

Higher-level routines should compose these primitives rather than claim one
native instruction per function:

- reciprocal: estimate plus Newton refinement;
- rsqrt: bit estimate, shifts/subtraction, MAD refinement;
- exp2/log2: casts, exponent/mantissa manipulation, MAD or LUT approximation;
- Threefry: integer add, xor, bit shifts and rotates;
- inclusive scan/reductions: copy, lane shift/rotate, add, broadcast and carries.

## Library composition sketch

`SFPURegister` now records common compositions using the same in-place convention:

```python
s.l0.rsqrt()                  # l0 = 1 / sqrt(old_l0)
s.l1.div(s.l0)                # l1 = old_l1 / l0; preserve l0
s.l2.exp().silu()
s.l3.gelu(approximation="tanh")  # alternatively "erf"
s.l4.clamp(0.0, 6.0)
s.l5.reduce("sum", group_width=32)
s.l6.scan("sum", group_width=8, inclusive=True)
```

These methods only record intent today. The library lowerer will expand each
composition, allocate/spill temporaries, preserve other live registers and
inactive destination lanes, and schedule instruction dependencies. It must not
silently borrow live LRegs. Neither numerical accuracy nor special-value support
is established by adding a record name.

The scalar vocabulary includes reciprocal/division, rsqrt/sqrt, exp2/exp,
log2/log, expm1/log1p, pow, sin/cos, tanh/sigmoid/SiLU, erf/GELU, ReLU/clamp,
floor/ceil/trunc/round, and isnan/isinf/isfinite. `round` means nearest with ties
to even and produces a float; classification operations produce integer masks.
`expm1` and `log1p` deserve separate compositions to avoid cancellation near zero.

Register collectives support sum/max/min/product in consecutive hardware lane
groups of width 1, 2, 4, 8, 16 or 32. Inactive inputs contribute identities
(0, -infinity, +infinity, 1 respectively). Reduction broadcasts the result to
active lanes in the group; scans follow increasing lane number and can be
inclusive or exclusive. Cross-group movement for widths above eight must be
composed. These are not tensor-axis reductions.

The API boundary is register computation: scalar math compositions such as
rsqrt/exp and explicit hardware-lane reductions/scans belong here. Tensor
softmax, RMSNorm and LayerNorm belong in compiler decompositions or a higher
kernel library. They combine these operations with tensor axes, valid element
counts, affine parameters and scheduling across registers, tiles or cores.
Mean likewise decomposes into sum and scaling by the reciprocal of the valid
count; the compiler owns that count, including masking and padding.

Argmax/top-k, quantization and random distributions still need their own
index, scale or counter contracts.

### First composition: rsqrt on Blackhole

The existing `examples/llama3_row_major.py::_append_rms_rsqrt` contains a candidate
core. After the RMS-specific mean and epsilon steps, its arithmetic is:

```python
# x is positive normal FP32; these are bit reinterpretations, not conversions.
y = as_float(0x5f1110a0 - (as_uint(x) >> 1))
c = (x * y) * y
y = y * (2.2825186 - c * (2.2533049 - c))
y = y + (0.5 * y) * (1.0 - (x * y) * y)
```

The exponent bits provide a cheap initial estimate. The polynomial improves
that estimate; the last line is Newton's inverse-square-root update, equivalent
in real arithmetic to `y * (1.5 - 0.5 * x * y * y)`. The parenthesization shown
keeps `x*y` together before multiplying by `y`, avoiding an unnecessarily extreme
`y*y` intermediate. Rounding and MAD behavior still matter on the device.

The core uses integer shifts/subtraction and floating multiply/add/MAD, rather
than a native rsqrt opcode. The existing example manually assigns LRegs and
inserts an instruction delay. The future composition lowerer owns those details.
Mean and epsilon belong to RMSNorm, not to `rsqrt()` itself.

Before implementing the public operation, define and test handling for signed
zero, negative values, subnormals, infinities and NaNs, plus error across the
normal exponent range. The fast core alone does not establish those semantics.

Load macros remain a lowering/scheduling API to design after these instruction
sequences work. They need instruction templates, operand substitutions, subunit
delays and register effects; an opaque `macro()` call would hide precisely the
information the scheduler needs. `llama3` demonstrates template recording via
CONFIG0 and separate SFPCONFIG sequence/misc configuration.
