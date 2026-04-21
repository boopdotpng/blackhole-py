# semaphores

**Source:** [`semaphores.md`](../specs/semaphores.md)

## Hardware semaphore state

### `SEM.STATE.COUNT_8`
§Tensix Hardware Semaphores / Intro

> 8 hardware semaphores per tile, each with a 4-bit Value (0-15) and 4-bit Max (0-15).

### `SEM.STATE.VALUE_RANGE`
§Tensix Hardware Semaphores / Intro

> Value is a 4-bit counter: valid range 0-15.

### `SEM.STATE.MAX_RANGE`
§Tensix Hardware Semaphores / Intro

> Max is a 4-bit saturation limit: valid range 0-15.

### `SEM.SEMINIT.SETS_VALUE_AND_MAX`
§Manipulation via Coprocessor Instructions / ttseminit

> SEMINIT sets both Value (init_value) and Max (max_value) for all semaphores selected by sem_sel bitmask.

### `SEM.SEMINIT.SEM_SEL_BITMASK`
§Manipulation via Coprocessor Instructions / ttseminit

> sem_sel is an 8-bit bitmask; bit i = 1 selects semaphore i for initialization.

### `SEM.SEMPOST.INCREMENT`
§Manipulation via Coprocessor Instructions / ttsempost

> SEMPOST: increment Value by 1, saturating at Max.

### `SEM.SEMPOST.SATURATES_AT_MAX`
§Manipulation via Coprocessor Instructions / ttsempost

> Value is capped at Max; posting when Value==Max is a no-op.

### `SEM.SEMPOST.MULTI_SEM`
§Manipulation via Coprocessor Instructions / ttsempost

> sem_sel bitmask allows posting to multiple semaphores in one instruction.

### `SEM.SEMGET.DECREMENT`
§Manipulation via Coprocessor Instructions / ttsemget

> SEMGET: decrement Value by 1, flooring at 0.

### `SEM.SEMGET.FLOORS_AT_ZERO`
§Manipulation via Coprocessor Instructions / ttsemget

> Value is floored at 0; getting when Value==0 is a no-op.

### `SEM.SEMGET.MULTI_SEM`
§Manipulation via Coprocessor Instructions / ttsemget

> sem_sel bitmask allows getting from multiple semaphores in one instruction.

### `SEM.SEMWAIT.STALL_ON_ZERO`
§Manipulation via Coprocessor Instructions / ttsemwait

> SEMWAIT condition C0: block instruction types while selected semaphore Value == 0.

### `SEM.SEMWAIT.STALL_ON_MAX`
§Manipulation via Coprocessor Instructions / ttsemwait

> SEMWAIT condition C1: block instruction types while selected semaphore Value >= Max.

### `SEM.SEMWAIT.BLOCK_MASK`
§Manipulation via Coprocessor Instructions / ttsemwait

> stall_res bitmask (B0-B8) controls which instruction types are held; same semantics as STALLWAIT.

### `SEM.PCBUF.READ_RETURNS_VALUE`
§Manipulation via PCBuf Semaphore Window

> Read from PCBuf+0x20+i*4 returns Semaphores[i].Value.

### `SEM.PCBUF.WRITE_POST`
§Manipulation via PCBuf Semaphore Window

> Write to PCBuf+0x20+i*4 with bit 0 == 0 performs SEMPOST (increment).

### `SEM.PCBUF.WRITE_GET`
§Manipulation via PCBuf Semaphore Window

> Write to PCBuf+0x20+i*4 with bit 0 == 1 performs SEMGET (decrement).

### `SEM.PCBUF.ADDRESS_RANGE`
§Manipulation via PCBuf Semaphore Window

> Semaphore window is at 0xFFE80020..0xFFE8003C (8 semaphores × 4 bytes each).

### `SEM.SW.L1_PLAIN_WORD`
§Software Semaphores (L1 Memory Words)

> Software semaphores are plain uint32_t values in L1; no special hardware — emulator handles them automatically through existing L1 read/write support.
