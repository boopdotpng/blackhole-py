# PCBufs (PC Buffers)

## Overview

3 PCBufs per Tensix tile. Each is a 16-entry FIFO of 32-bit values from BRISC to one TRISC. They serve as the control/dispatch channel: BRISC tells TRISCs what kernel to run, and uses PCBuf reads as a synchronization barrier.

PCBufs are completely separate from instruction buffers (see `instruction-push.md`). Instruction buffers push Tensix coprocessor opcodes. PCBufs pass control tokens between RISC-V cores and provide a semaphore access window.

## Addresses

| PCBuf | Address | Direction |
|-------|---------|-----------|
| PCBuf[0] | `0xFFE80000` (`PC_BUF_BASE`) | BRISC -> TRISC0 |
| PCBuf[1] | `0xFFE90000` (`PC1_BUF_BASE`) | BRISC -> TRISC1 |
| PCBuf[2] | `0xFFEA0000` (`PC2_BUF_BASE`) | BRISC -> TRISC2 |

## Access Rules

| Core | Write (push) | Read (pop/sync) |
|------|-------------|-----------------|
| BRISC | Yes (all 3 PCBufs) | Yes (sync barrier) |
| NCRISC | No | No |
| TRISC0 | No | Yes (own PCBuf[0] only) |
| TRISC1 | No | Yes (own PCBuf[1] only) |
| TRISC2 | No | Yes (own PCBuf[2] only) |
| NOC | No | No |
| Tensix coprocessor | No | No |

## Memory Map Within Each PCBuf

From the TRISC's perspective, the PCBuf region starting at `0xFFE80000` contains:

| Offset | Word | Name | Behavior |
|--------|------|------|----------|
| `0x00` | 0 | FIFO pop | TRISC read: blocks until a value is available, returns the next queued word. BRISC write: pushes a value into the FIFO. |
| `0x04` | 1 | `CoprocessorDoneCheck` | TRISC read: blocks until this TRISC's coprocessor thread is idle (no in-flight instructions). Used by `tensix_sync()`. |
| `0x08` | 2 | `MOPExpanderDoneCheck` | TRISC read: blocks until the MOP expander has finished expanding. Used by `mop_sync()`. |
| `0x0C-0x1C` | 3-7 | Reserved/padding | |
| `0x20` | 8 | `SemaphoreAccess[0]` | Read/write to hardware semaphore 0 (see semaphores.md) |
| `0x24` | 9 | `SemaphoreAccess[1]` | sem 1 |
| `0x28` | 10 | `SemaphoreAccess[2]` | sem 2 |
| `0x2C` | 11 | `SemaphoreAccess[3]` | sem 3 |
| `0x30` | 12 | `SemaphoreAccess[4]` | sem 4 |
| `0x34` | 13 | `SemaphoreAccess[5]` | sem 5 |
| `0x38` | 14 | `SemaphoreAccess[6]` | sem 6 |
| `0x3C` | 15 | `SemaphoreAccess[7]` | sem 7 |

Note: all three TRISCs read the semaphore window at the same base address (`0xFFE80020-0xFFE8003C`) because there is only one set of 8 hardware semaphores per tile.

## BRISC Write Semantics

BRISC pushes control tokens into a TRISC's PCBuf FIFO. Known token formats:

| Token | Value | Meaning |
|-------|-------|---------|
| `TENSIX_NEWPC_VAL(addr)` | `0x80000000 \| addr` | Unhalt the TRISC and jump to `addr` |
| `TENSIX_LOOP_PC_VAL(arg)` | `0x00000000 \| arg` | Start a PC buffer loop |
| `TENSIX_UNHALT_VAL` | `0x40000000` | Unhalt and resume at previous PC |
| `TENSIX_PC_SYNC(arg)` | `0xC0000000 \| arg` | Sync block until kernels done |

If the FIFO is full (16 entries), BRISC's write stalls until space is available.

## BRISC Read Semantics (Sync Barrier)

A BRISC read from `PC_BUF_BASE` / `PC1_BUF_BASE` / `PC2_BUF_BASE` is a **three-condition hardware barrier**. It blocks until ALL of:
1. The FIFO is fully drained (TRISC has consumed all queued values)
2. The TRISC itself is blocking on a PCBuf read (waiting for more work)
3. The Tensix coprocessor thread for that TRISC is idle (no in-flight instructions)

This is how BRISC knows a TRISC has completely finished its kernel.

## TRISC Read Semantics

### FIFO Pop (offset 0x00)
Blocking read. Returns the next 32-bit value BRISC pushed. If the FIFO is empty, the TRISC stalls until BRISC pushes something.

### CoprocessorDoneCheck (offset 0x04)
Blocking read. Returns only when this TRISC's coprocessor thread has finished executing all previously-pushed instructions. Used by `tensix_sync()`:
```c
inline void tensix_sync() {
    store_blocking(&pc_buf_base[1], 0);  // write 0 then read, blocks until idle
}
```

### MOPExpanderDoneCheck (offset 0x08)
Blocking read. Returns only when the MOP expander has finished expanding all queued MOPs.

### Semaphore Window (offsets 0x20-0x3C)
See `semaphores.md`. Read returns the semaphore value. Write does SEMPOST (bit 0 == 0) or SEMGET (bit 0 == 1).

## Observed Usage in Disassembly

### TRISCs polling PCBuf status
TRISCs poll `0xFFE80034` (offset 0x34 = `SemaphoreAccess[5]`) to check semaphore state before proceeding:
```
ffe806b7  lui   a3, 0xffe80
0346a703  lw    a4, 52(a3)     # read 0xFFE80034
0ff77713  zext.b a4, a4
fe071ce3  bnez  a4, <spin>     # spin until zero
```

### BRISC pushing instructions at init
BRISC writes SEMINIT opcodes through `instrn_buf_base(0)` at `0xFFE40000` (not through PCBuf). PCBuf is for control tokens, not coprocessor instructions.

## Current tt-metal Firmware

In current tt-metal Blackhole firmware, TRISCs don't actually pop from PCBuf for kernel dispatch. Instead, BRISC writes `RUN_SYNC_MSG_GO` to an L1 mailbox and TRISCs poll that. The PCBuf mechanism is still available and used for `tensix_sync()` and hardware semaphore access, but primary dispatch uses L1 polling.

## Emulator Implementation

Model each PCBuf as:
1. A 16-entry FIFO of uint32_t (BRISC pushes, TRISC pops)
2. BRISC write stalls if full, TRISC read stalls if empty
3. BRISC read from PCBuf base = three-condition barrier (FIFO drained + TRISC waiting + coprocessor idle)
4. Offset 0x04: read blocks until coprocessor thread idle
5. Offset 0x08: read blocks until MOP expander done
6. Offsets 0x20-0x3C: semaphore access window (shared across all TRISCs)
