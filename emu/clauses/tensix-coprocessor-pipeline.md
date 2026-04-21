# tensix-coprocessor-pipeline

**Source:** [`tensix-coprocessor-pipeline.md`](../specs/tensix-coprocessor-pipeline.md) · **Emulator:** `blackhole-py/emu/tensix/__init__.py`

## Thread model

### `TCP.THREADS.THREE_INDEPENDENT`
§Overview

> The Tensix coprocessor has 3 independent threads (T0, T1, T2), each with its own frontend pipeline.

### `TCP.THREADS.INDEPENDENT_STEP`
§Overview

> Instructions are dispatched in-order per thread. Across threads, each thread proceeds independently.

### `TCP.ROLES.BRISC_ALL_FIFOS`
§Overview / role table

> BRISC can push to all 3 thread FIFOs via 0xFFE40000/0xFFE50000/0xFFE60000.

### `TCP.ROLES.NCRISC_NO_PUSH`
§Overview / role table

> NCRISC cannot push instructions.

### `TCP.ROLES.TRISC_OWN_THREAD`
§Overview / role table

> Each TRISC pushes only to its own thread FIFO.

### `TCP.ENCODING.32BIT_WORD`
§Instruction Encoding

> All Tensix instructions are 32-bit words: bits[31:24] = opcode, bits[23:0] = parameters.

### `TCP.PIPELINE.FIFO_MOP_REPLAY_WAIT`
§Frontend Pipeline (per-thread)

> Per-thread frontend pipeline order: Instruction FIFO → MOP Expander → Replay Expander → Wait Gate → Backend Dispatch.

### `TCP.BRISC.NO_MOP`
§BRISC Coprocessor Access

> BRISC's pushes enter after the MOP Expander, bypassing MOP expansion. BRISC cannot issue MOP instructions.

## Instruction dispatch

### `TCP.DISPATCH.NOP_PASSTHROUGH`
§Key Opcodes / NOP dispatch

> NOP (opcode 0x02) and DMANOP are dispatched and consumed without side-effects.

### `TCP.DISPATCH.STALLWAIT_INSTALLS_GATE`
§Key Opcodes / STALLWAIT

> STALLWAIT (opcode 0xA2) dispatches to the Sync Unit which installs a latched wait in the thread's Wait Gate.

### `TCP.DISPATCH.SEMWAIT_INSTALLS_GATE`
§Key Opcodes / SEMWAIT

> SEMWAIT (opcode 0xA6) dispatches to the Sync Unit which installs a semaphore wait in the thread's Wait Gate.

### `TCP.DISPATCH.MUTEX_ACQUIRE`
§Full Coprocessor Integration

> ATGETM acquires a mutex for the issuing thread. If the mutex is already held by another thread, the instruction is re-queued (replayed).

### `TCP.DISPATCH.MUTEX_RELEASE`
§Full Coprocessor Integration

> ATRELM releases the mutex held by the issuing thread.

### `TCP.DISPATCH.MOP_CFG_WRITE`
_§Full Coprocessor Integration / mop_handler_for_

> MMIO write to 0xFFB80000 + i*4 sets MopCfg[i] for the calling TRISC's thread. BRISC and NCRISC have no MOP config handler.

### `TCP.SEMAPHORE.8_PER_TILE`
§Hardware Semaphores

> 8 hardware semaphores per tile, 4-bit value and 4-bit max each.

### `TCP.SEMAPHORE.BRISC_INIT`
§Hardware Semaphores

> BRISC initializes all semaphores at boot via SEMINIT through T0's FIFO.

### `TCP.ADDRMAP.INSTRN_BUF`
_§INSTRN_BUF Address Map_

> 0xFFE40000 = T0 FIFO; 0xFFE50000 = T1 FIFO; 0xFFE60000 = T2 FIFO. Stride = 0x10000.

### `TCP.ADDRMAP.MOP_CFG_BASE`
§Other Key Address Regions

> 0xFFB80000 = TENSIX_MOP_CFG_BASE (MOP Expander config, write-only, 9 words).
