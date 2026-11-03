# Tensix ISA test review

All added tests are **Python in `blackhole-py/tests/isa`**, using the existing
`Asm` harness and `ttko.isa.Tensix`. No C tests or new Clang test path were added.
C headers supply independent encoding expectations; device execution continues
to use the existing runtime and firmware build.

## What is ready to review

- [README.md](README.md): test design and run commands.
- [results.md](results.md): hardware/offline validation and retained evidence.
- [audit.md](audit.md): each reviewed behavioral assertion, exact test functions,
  recorded outcomes, and remaining gaps.
- [coverage.md](coverage.md): all 137 encoders and 517 operand fields.
- [modifiers.md](modifiers.md): 105 named MOD/IMM definitions extracted from
  applicable manual pages, with candidate tests and explicit review obligations.
- [crash_investigation.md](crash_investigation.md): native crash evidence,
  diagnostic runs, and reproduction tooling.

The new ISA suite has 9,534 encoding checks (trimmed from 23,211 exhaustive sweeps on 2026-10-07; results.md predates the trim), 10 audit/diagnostic checks and
9,572 hardware cases. Hardware cases cover SFPU bit operations and flags,
predicate stack state transitions, scalar ALU modes, semaphore masks and
saturation, multi-condition waits, mutex exclusion, and integer-to-float rounding.
Stochastic rounding tests check legal adjacent results, not distribution quality.

Reviewing existing FPU, SFPU, packer, unpacker, transport and synchronization
tests brings the map to **66 instructions with partial behavioral claims**.
The remaining **71 instructions have no reviewed behavioral claim**. No
instruction is declared exhaustively tested. Encoding coverage is not semantic
coverage, and this count is not a percentage of ISA functionality.

The existing transport tests had two stale imports of `isa`. They now import
`Tensix` from `ttko.isa`; all 88 transport cases passed, including the default
prefix sweep from 1 through 128. The initial failure remains in
[evidence/transport_before_fix.json](evidence/transport_before_fix.json).

## Remaining work, in priority order

1. Address-counter/configuration state and replay/MOP semantics, including
   updates, wraps, stalls, resource waits and sequence-dependent effects.
2. Remaining scalar memory/atomic operations and stream instructions; dedicated
   oracles for instructions currently used only as fixture setup.
3. FPU matrix/convolution/pooling semantics, all fidelity/address/broadcast modes,
   source-valid/zero flags, exceptional numeric values and accumulation edges.
4. Pack/unpack contexts, compression, addressing, formats, saturation and rounding
   combinations beyond the existing transport and format checks.
5. Remaining SFPU lookup, shuffle, transpose, swap, indirect addressing and
   load/store modes; PRNG, constant/backdoor registers, partially fused arithmetic
   and stochastic distributions.
6. Modifier interaction matrices, scheduling hazards and documented silicon bugs;
   broader core/card coverage and untested cross-thread interleavings.

The per-requirement gaps in the audit are more precise than this family-level
list. The modifier checklist includes named constants, not every prose-defined
mode or configuration field. Reserved/undefined encodings are tested offline
only. NoC, PCIe, Ethernet and L2CPU subsystem conformance remains outside the
current Tensix-first scope.

## Evidence and limitations

`inventory.py` regenerates the source snapshot. `requirements.py` records
reviewed claims; `audit.py` links claims to assertions and recorded test outcomes.
Static source sightings and dynamic-dispatch sites are navigation aids and never
automatically count as behavioral coverage. Evidence includes source hashes;
relevant source changes invalidate recorded results. Compact evidence retains
non-passing outcomes while grouping successful parameter cases by test function.

The intermittent native segfault has not reproduced under GDB, debug allocation
or opt-in mapping bounds checks. Its root cause remains unresolved; no fix is
claimed. Five existing FP8 subnormal cases remain expected failures. Validation
covers device 0 and worker-core index 0, not all hardware configurations.
