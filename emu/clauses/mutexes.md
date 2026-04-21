# mutexes

**Source:** [`mutexes.md`](../specs/mutexes.md)

## Valid indices

### `MTX.INDICES.VALID_SET`
§Hardware State

> Valid mutex indices: 0, 2, 3, 4. Index 1 is invalid. Indices > 4 are invalid.

### `MTX.INDICES.INITIAL_STATE`
§Hardware State

> Initial state at reset: all mutexes are Nobody (not held).

### `MTX.INDICES.COUNT_4`
§Hardware State

> 4 mutexes per tile (Blackhole). Wormhole B0 had 7.

### `MTX.ATGETM.ACQUIRE`
§ATGETM (Acquire)

> ATGETM: if mutex is free (Nobody), acquire it — set HeldBy = CurrentThread.

### `MTX.ATGETM.BLOCKS_WHEN_HELD`
§ATGETM (Acquire)

> If the mutex is held by a different thread, the issuing thread spins at the Wait Gate until it becomes free.

### `MTX.ATGETM.REENTRANT`
§ATGETM (Acquire)

> If the mutex is already held by the issuing thread (reentrant acquire), it proceeds.

### `MTX.ATRELM.RELEASE`
§ATRELM (Release)

> ATRELM: if HeldBy == CurrentThread, set HeldBy = Nobody.

### `MTX.ATRELM.NOOP_IF_NOT_HELD`
§ATRELM (Release)

> If the mutex is not held by the issuing thread, ATRELM completes with no effect.

### `MTX.FAIRNESS.ROUND_ROBIN`
§ATRELM Round-robin fairness

> When thread i releases and both other threads are waiting, thread (i+1) % 3 acquires next.

## Access restrictions

### `MTX.ACCESS.TRISC_ONLY`
§Per-Core Access

> Mutexes are only accessible from the three Tensix coprocessor threads (T0/T1/T2). BRISC and NCRISC cannot use ATGETM/ATRELM.

### `MTX.ACCESS.NO_MMIO`
§Per-Core Access

> There is no memory-mapped interface for mutexes (unlike semaphores).

### `MTX.STALLWAIT.STALL_SYNC`
§Interaction with STALLWAIT

> ATGETM and ATRELM are blocked by STALL_SYNC (B1) in a STALLWAIT block mask.
