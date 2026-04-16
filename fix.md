# Emulator Audit Notes

This is a summary of the current `extra/emu` audit against `../emu-specs`, with a focus on:

- whether the current tests are actually correct and useful
- what fidelity gaps still matter outside the Tensix coprocessor
- whether we should model exact boot/reset behavior

## Decision

Assume firmware works.

We should treat firmware as trusted input and keep the current model where we:

1. upload firmware into the emulated memories
2. set the relevant PCs
3. start stepping cores

Exact reset / boot-state emulation is not worth the complexity unless we explicitly decide to debug firmware bring-up behavior.

## Boot / Reset Recommendation

Do not model exact boot semantics for now.

Reasons:

- The current emulator is clearly optimized for functional execution, not hardware bring-up fidelity.
- The current tests already lean on the simplified model.
- Modeling reset gates, boot JAL flow, subordinate release, reset-PC overrides, and related MMIO side effects would add noticeable complexity for limited value.
- We do not expect frequent firmware changes, so validating every detail of firmware boot choreography is not the best use of effort.

Rough effort estimate if we changed our mind later:

- Minimal "realistic enough" boot/reset model: about 1 to 3 focused days plus test rewrites.
- More hardware-faithful boot/reset/register behavior: roughly a week or more.

## Test Suite Review

Overall: the tests are useful, but mixed in quality.

The strongest parts are:

- RV32 core behavior tests
- LDM fast/slow-path routing tests
- NIU read/write/atomic behavior tests
- semaphore and CB config tests

The weaker parts are mostly "smoke tests" that assert very little, or tests that encode the simplified emulator model rather than true hardware semantics.

### Tests that are weaker than they look

#### `extra/emu/tests/test_device.py`

- `test_device_wall_clock`
  - This does not test the device stepping logic.
  - It manually writes `WALL_CLOCK_L` through shared MMIO instead of verifying `_step_loop()` updates the clock.

- `test_ldm_segment_redirected_to_scratch`
  - This does not call the actual upload path.
  - It manually writes the scratch region, so it validates layout assumptions rather than `_upload_firmware()`.

- `test_ldm_segment_per_core_isolation`
  - Same issue: validates scratch layout, not the real upload implementation.

- `test_bank_xy_p100a`, `test_bank_xy_p150`
  - These only check counts, not actual coordinates.

- `test_bank_noc_table_size`
  - This is only a non-empty-output smoke test.
  - It does not validate the real table layout or packed XY entries.

#### `extra/emu/tests/test_noc.py`

- The NIU suite is generally strong, but `program_write()` writes the same XY value into both `TARG_ADDR_HI` and `RET_ADDR_HI`.
- Because of that, the tests would not catch an implementation that accidentally sourced write destination coordinates from the wrong field.
- The tests are still useful, just slightly less discriminating than they appear.

#### `extra/emu/tests/test_rv32i.py`

- `test_mmio_catch_all`
  - This explicitly treats `SOFT_RESET_0` like generic stored MMIO.
  - That is fine for the current simplified model, but it bakes in the decision not to emulate reset semantics.

## Missing or Weak Coverage

These are the main areas where the tests do not currently protect us well:

- NIU `WR_BE` behavior
  - The register bits/constants exist, but there is no test for byte-enable writes.

- NIU multicast exclusion
  - `NOC_BRCST_EXCLUDE` is defined, but there is no coverage for exclusion behavior.

- PCIe bit-60 addressing path
  - No meaningful tests for PCIe-specific NIU addressing semantics.

- Actual firmware upload integration
  - The current suite does not really validate the real `_upload_firmware()` path end to end.

- Bank-to-NOC table contents
  - There should be direct assertions for expected packed XY entries, not just count/size checks.

- Wall clock stepping
  - The tests should verify device stepping mutates wall-clock registers.

## Non-Coprocessor Fidelity Gaps Still Worth Tracking

Ignoring Tensix coprocessor functionality, these were the most relevant remaining mismatches:

- NIU `WR_BE` is specified but not implemented.
- NIU multicast exclusion is specified but not implemented.
- `TRISC1_RESET_PC` constant appears inconsistent with the spec and currently collides with `TRISC2_RESET_PC`.
- `RISC_PC_READBACK` is declared but not populated.

Given the decision above, only the first two are clearly important emulator-behavior gaps for ordinary functional correctness.

## Suggested Next Steps

If we want to improve the suite without taking on boot/reset complexity:

1. Add direct tests for `WR_BE`.
2. Add direct tests for multicast exclusion.
3. Strengthen bank-table tests to assert concrete XY values.
4. Replace the wall-clock smoke test with a real stepping-based test.
5. Add one integration-style firmware upload test that actually exercises `_upload_firmware()`.

## Bottom Line

The current emulator direction is reasonable:

- trust firmware
- start from uploaded code/data
- step cores directly

The better investment is improving NIU and memory-model coverage, not implementing exact boot/reset semantics.
