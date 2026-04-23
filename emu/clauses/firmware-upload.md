# firmware-upload

**Source:** [`firmware-upload.md`](../specs/firmware-upload.md)

## Reset state

### `FW.RESET.POWER_ON_STATE`
§Upload Sequence / Step 1

> On power-on, all 5 RISCs are held in reset (SOFT_RESET_0 = 0x47800).

### `FW.RESET.BRISC_ONLY_RELEASE`
§Upload Sequence / Step 8

> Writing SOFT_RESET_BRISC_ONLY (0x47000) releases BRISC from reset (PC=0); NCRISC and TRISCs remain held.

### `FW.RESET.ALL_RELEASE`
§Upload Sequence

> Writing 0 to SOFT_RESET_0 releases all 5 cores from reset.

### `FW.RESET.REASSERT`
§Reset Control

> Writing SOFT_RESET_ALL back to SOFT_RESET_0 re-asserts reset on all cores.

### `FW.BOOT.BRISC_PC_ZERO`
§Upload Sequence / Step 8

> BRISC always resets to PC=0 (the JAL stub in L1); no PC override register exists for BRISC.

### `FW.RESET_PC.OVERRIDE_MECHANISM`
§Upload Sequence / Step 7

> Subordinate reset PCs are programmed via NCRISC_RESET_PC, TRISC0/1/2_RESET_PC registers. The core uses the override value only when the corresponding enable bit (TRISC_RESET_PC_OVR, NCRISC_RESET_PC_OVR) is set.

### `FW.RESET_PC.WITHOUT_OVR`
§Upload Sequence

> If override is not enabled, core starts from PC=0 regardless of RESET_PC register value.

### `FW.RESET_PC.TRISC_INDIVIDUAL_BITS`
_§Upload Sequence / TRISC_RESET_PC_OVR_

> TRISC_RESET_PC_OVR has 3 independent bits: bit 0=TRISC0, bit 1=TRISC1, bit 2=TRISC2. Each can be independently enabled.

### `FW.JAL.ENCODING`
§Upload Sequence / Step 3

> Boot stub at L1[0] is a RISC-V JAL x0, BRISC_FIRMWARE_BASE (0x3840). _make_jal(0x3840) produces the correct 4-byte little-endian encoding.

### `FW.JAL.PC_JUMP`
§Upload Sequence / Step 3

> After executing the JAL at L1[0], BRISC's PC is BRISC_FIRMWARE_BASE (0x3840).

### `FW.JAL.ROUNDTRIP`
§Upload Sequence / Step 3

> _make_jal produces correct encodings for targets 0x100, 0x3840, 0x5440, 0x6A40.

### `FW.GO_MSG.INIT_VALUE`
§Upload Sequence / Step 4

> Boot writes RUN_MSG_INIT (0x40) to L1[GO_MESSAGES + 3] (the signal byte).

### `FW.GO_MSG.DONE_SIGNAL`
§Upload Sequence / Step 9

> Host polls L1[GO_MESSAGES + 3] until it reads RUN_MSG_DONE (0x00), which indicates BRISC has completed init and released all subordinates.

### `FW.STEP.SKIPS_RESET`
_§Per-Core Firmware Behavior / _step_loop_

> step_loop does not call step() on cores that have in_reset=True.

### `FW.STEP.WALL_CLOCK`
§MMIO Register Map / Wall Clock

> WALL_CLOCK_L increments every call to _step_loop, even when all cores are in reset.

### `FW.STEP.TIMEOUT`
§Upload Sequence / Step 9

> _step_loop raises TimeoutError after max_steps iterations without done condition.

### `FW.BRISC.RELEASES_SUBORDINATES`
_§Per-Core Firmware Behavior / BRISC deassert_all_reset_

> BRISC firmware writes 0 to SOFT_RESET_0 to release NCRISC + TRISCs. The reset hook fires on that write and transitions the subordinate cores from held→running.

### `FW.SOFT_RESET.HOOK`
_§Reset Control / SOFT_RESET_0_

> A write32 callback on SOFT_RESET_0 (0xFFB121B0) fires for every bus write. The hook reads old and new values and transitions cores accordingly.
