# Tensix ISA conformance tests

For cycle costs, see the [Tensix timing reference and kernel estimation guide](../timing/README.md).
It covers all 137 encoders, distinguishes latency from issue spacing, and includes
hardware timing samples. Functional conformance does not establish timing.

This suite is **not exhaustive functional ISA coverage**. It provides encoding
coverage for every one of the 137 public Tensix encoders and direct hardware
oracles for selected behavior of 37 instructions. See [coverage.md](coverage.md)
for the instruction inventory and [inventory.json](inventory.json) for exact
fields, source revisions, constants, subpage sections, and hardware scenarios.

All new tests are Python, using `Asm` and `ttko.isa.Tensix`. C headers are
read-only encoding references; the existing runtime retains its normal firmware
build. Start with [review.md](review.md) for results and remaining work.

## Run

From `blackhole-py`, using the shared virtualenv:

```sh
# No device access; the default run also reports hardware cases as skipped.
../.venv/bin/python -m pytest tests/isa/test_encoding.py -q

# Reserve card 0 and run sequentially.
tt-device-queue run --device 0 --cwd "$PWD" -- \
  '../.venv/bin/python -m pytest tests/isa --bh-hardware --bh-device=0 -q'

# Regenerate the independent source snapshot and coverage inventory.
../.venv/bin/python -m tests.isa.inventory
```

Regeneration requires the sibling `tt-isa-documentation`, `tt-ins-docs`, and
`tt-llk` checkouts. Test execution uses the committed snapshot and does not need
those repositories. The website catalog supplies manual links, never expected
encoding words. Blackhole LLK supplies all 517 encoded operand fields; applicable
manual SVG diagrams independently check additional field layouts. The two LLK
X/Y versus Python Z/W parameter-name differences are explicit aliases.

## What is checked

| Test | Assertions |
|---|---|
| `test_encoding.py` | All 137 opcodes and 517 fields; walking bits, boundaries and alternating patterns for every field; combined operands; negative and overflowing operands rejected. Reserved bit patterns are checked only as encodings, never executed as behavioral contracts. |
| `test_sfpu_bits.py` | Bitwise operations, integer add/subtract, integer multiply, shifts, absolute value, sign/exponent/mantissa manipulation, immediate conversion, comparisons and condition flags. Crosses selected modes with distinct/aliased registers and all/none/half-lane masks. |
| `test_predicate_stack.py` | All 16 push/pop modifiers, enable/disable modifiers, complement, all comparison stack-mutation modifiers; truth tables for current and saved state; depths zero, one, seven and eight where defined; subsequent pops check deeper stack preservation. |
| `test_sync.py` | Walking-bit and multi-bit semaphore masks, saturation, multi-condition waits, and mutex exclusion with two/three contenders. |
| `test_sfpu_cast.py` | Sign-magnitude integer-to-FP32 nearest-even results and stochastic adjacent-value bounds, with masks and aliases. |
| `test_audit.py` | Coverage evidence bookkeeping and opt-in native-memory diagnostic guards. |
| `test_scalar.py` | Add/subtract, low-16-bit multiply, all documented bitwise/shift/comparison modes, register/immediate operands, output aliases, GPR bank boundaries, all three Tensix threads. Checks intermediate results and the final contents of all 64 GPRs. |

SFPU bit tests construct raw values with immediates and transport results as two
normal FP32 mantissas. This preserves all 32 result bits without depending on
whether the unpacker or packer normalizes NaNs, denormals, or signed zero.
Hardware tests also check an adjacent untouched Dst slot where applicable and
an L1 output guard. Predicate-stack tests observe both the enabled lanes and
their complement to distinguish enabled predication from globally disabled
predication. Latent flags while predication is disabled are not fully observed.

## Remaining work

An encoding pass is not a hardware behavior pass. “Partial” in the inventory
means precisely that; “not audited” does not mean the existing test suite lacks
coverage. Reviewed existing tests are mapped in [audit.md](audit.md): 66 instructions
have partial claims and 71 have no reviewed claim. Every claim names its actual
assertions and remaining gaps. [modifiers.md](modifiers.md) tracks named manual
modifier definitions; candidate links do not establish exhaustive coverage.

The next conformance work must include:

- Matrix instructions, all address/broadcast/accumulation/fidelity modifiers,
  source-valid and zero-flag side effects, layouts and numeric formats.
- Unpack/pack modes, contexts, address counters, stream integration, rounding,
  saturation, scatter, compression, and format-specific edge cases.
- SFPU floating-point arithmetic against the documented partially fused model;
  conversions and stochastic rounding; lookup tables; shuffle/transpose/swap;
  load/store modes, addressing, macros, indirect operands varying by lane,
  configuration registers, PRNG, and constant/backdoor register behavior.
- Configuration and synchronization instructions, mutexes, semaphores,
  replay/MOP, resource waits, scalar memory/atomic operations, and stream access.
- Scheduling dependencies, documented silicon bugs, cross-thread interference,
  modifier interactions and sequence-dependent state transitions.

The new integer multiply tests exercise uniform indirect indices, but do not
prove lane-varying indirection or nominal-destination preservation. The cast
tests cover integer absolute value, integer/sign-magnitude conversion, and
integer-to-float rounding boundaries; stochastic distributions and seeds remain
unverified. Reserved and undefined behavior must
remain distinct from supported behavior. NoC, PCIe, Ethernet and L2CPU behavior
are outside the current user-selected Tensix-first scope.
