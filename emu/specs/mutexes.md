# Mutexes

Hardware mutexes in the Tensix Sync Unit provide exclusive mutual exclusion among the three coprocessor threads (T0, T1, T2) within a single tile. They are manipulated by two instructions: `ATGETM` (acquire) and `ATRELM` (release).

Mutexes are unrelated to semaphores. Semaphores are counting primitives for producer/consumer synchronization (see `semaphores.md`). Mutexes are exclusive locks for protecting shared register read-modify-write sequences.

---

## Hardware State

There are 4 mutexes per tile. Each mutex holds a 2-bit owner field:

```
Mutex[i].HeldBy : enum { Nobody, T0, T1, T2 }
```

Valid indices: **0, 2, 3, 4**. Index 1 is invalid. Indices > 4 are invalid. Using an invalid index causes the issuing thread to wait forever.

| Index | Name     | Typical use |
|------:|----------|-------------|
|     0 | `math`   | Atomic config register read-modify-write (`REG_RMW`) between threads |
|     2 | `unpack0`| Unpacker 0 |
|     3 | `unpack1`| Unpacker 1 |
|     4 | `pack0`  | Packer 0 / SFPU (SFPU instructions can be issued by both T1 and T2) |

Initial state at reset: all mutexes are `Nobody` (not held).

### Comparison with Wormhole B0

Wormhole B0 has 7 mutexes (indices 0, 2, 3, 4, 5, 6, 7) — the extra three are `pack1` (5), `pack2` (6), `pack3` (7). Index 1 is still invalid. Blackhole reduced the count to 4.

---

## Instruction Encodings

Both instructions are 32 bits wide. The top 8 bits are the opcode, the bottom 24 bits are the `mutex_index` field (only the low 3 bits matter in practice).

### ATGETM — Acquire Mutex (opcode `0xA0`)

```
 31      24 23                              0
┌─────────┬──────────────────────────────────┐
│ 0xA0    │         mutex_index              │
│ [31:24] │            [23:0]                │
└─────────┴──────────────────────────────────┘
```

```c
#define TT_OP_ATGETM(mutex_index) TT_OP(0xa0, ((mutex_index) << 0))
// word = (0xA0 << 24) | (mutex_index & 0xFFFFFF)
```

### ATRELM — Release Mutex (opcode `0xA1`)

```
 31      24 23                              0
┌─────────┬──────────────────────────────────┐
│ 0xA1    │         mutex_index              │
│ [31:24] │            [23:0]                │
└─────────┴──────────────────────────────────┘
```

```c
#define TT_OP_ATRELM(mutex_index) TT_OP(0xa1, ((mutex_index) << 0))
// word = (0xA1 << 24) | (mutex_index & 0xFFFFFF)
```

Both instructions use execution resource `SYNC` and are routed to the Sync Unit backend.

---

## Functional Model

### ATGETM (Acquire)

The instruction blocks at the Wait Gate until it can acquire the mutex, then proceeds through the Sync Unit in 1 cycle.

```c
void ATGETM(uint thread_id, uint index) {
    // 1. Validate index
    if (index == 1 || index > 4) {
        while (true) { wait; }  // infinite stall
    }

    // 2. Wait for availability
    if (Mutex[index].HeldBy == thread_id) {
        // Already held by this thread — reentrant acquire.
        // May wait 1-2 cycles due to contention with other threads'
        // concurrent ATGETM/ATRELM on the same mutex.
    } else {
        // Spin at the Wait Gate until the mutex is free.
        while (Mutex[index].HeldBy != Nobody) {
            wait;
        }
    }

    // 3. Acquire
    Mutex[index].HeldBy = thread_id;
}
```

If multiple threads are waiting for the same free mutex simultaneously, one is chosen to acquire it. The fairness guarantee comes from `ATRELM` (see below).

### ATRELM (Release)

```c
void ATRELM(uint thread_id, uint index) {
    // 1. Validate index
    if (index == 1 || index > 4) {
        while (true) { wait; }  // infinite stall
    }

    // 2. May wait 1-2 cycles due to contention with concurrent
    //    ATGETM/ATRELM from other threads on the same mutex.

    // 3. Release (only if held by this thread)
    if (Mutex[index].HeldBy == thread_id) {
        Mutex[index].HeldBy = Nobody;
    }
    // If not held by this thread, instruction completes with no effect.
}
```

**Round-robin fairness:** When thread `i` releases a mutex and *both* other threads are waiting on it via `ATGETM`, thread `(i + 1) % 3` is chosen as the next acquirer.

---

## Timing and Throughput

| Property | Value |
|----------|-------|
| Latency | 1 cycle (once through the Wait Gate) |
| Throughput | Up to 3 ATGETM/ATRELM per cycle, if they reference **different** mutexes |
| Contention delay | 1-2 extra cycles if multiple threads touch the same mutex simultaneously |
| Blocked-thread behavior | Thread stalls at the Wait Gate; no instructions from that thread proceed past the gate |

Semaphore instructions (SEMINIT, SEMPOST, SEMGET, SEMWAIT) share the Sync Unit but have independent throughput — at most 1 semaphore instruction per cycle. Mutex and semaphore instructions can execute concurrently.

---

## Interaction with STALLWAIT

ATGETM and ATRELM are classified as Sync Unit instructions. They are blocked by the `STALL_SYNC` (B1, value `0x02`) bit in a `STALLWAIT`/`SEMWAIT` block mask.

If a thread has a latched `STALLWAIT` with B1 set and the wait condition has not yet been met, any ATGETM or ATRELM from that thread is held at the Wait Gate until the STALLWAIT condition clears.

See `stallwait-conditions.md` for the full block mask reference.

---

## Per-Core Access

Mutexes are only accessible from the three Tensix coprocessor threads (T0, T1, T2) via pushed Tensix instructions.

| Core   | Can use ATGETM/ATRELM? | Notes |
|--------|------------------------|-------|
| TRISC0 (T0) | Yes | Pushes instructions to T0's FIFO |
| TRISC1 (T1) | Yes | Pushes instructions to T1's FIFO |
| TRISC2 (T2) | Yes | Pushes instructions to T2's FIFO |
| BRISC        | No  | Cannot push ATGETM/ATRELM |
| NCRISC       | No  | Cannot push ATGETM/ATRELM |

There is no memory-mapped interface for mutexes (unlike semaphores, which have the PCBuf semaphore window). The only way to manipulate mutexes is through the Tensix instruction FIFO.

---

## Emulator Implementation

### State

```python
# 4 mutexes. HeldBy is None (nobody) or 0/1/2 (thread id).
mutex_held_by = [None] * 5  # indexed 0-4; index 1 is unused/invalid

VALID_MUTEX_INDICES = {0, 2, 3, 4}
```

### Decoding

```python
def decode(word):
    opcode = (word >> 24) & 0xFF
    mutex_index = word & 0xFFFFFF  # only low bits matter
    return opcode, mutex_index
```

### Execution

```python
def exec_atgetm(thread_id, index):
    """Returns True if acquired, False if must stall."""
    if index not in VALID_MUTEX_INDICES:
        return False  # stall forever (or raise in emulator)

    held = mutex_held_by[index]
    if held is None or held == thread_id:
        mutex_held_by[index] = thread_id
        return True   # acquired
    else:
        return False  # stall — re-evaluate next cycle

def exec_atrelm(thread_id, index):
    """Always completes (never stalls, beyond 1-2 cycle contention)."""
    if index not in VALID_MUTEX_INDICES:
        return False  # stall forever (or raise in emulator)

    if mutex_held_by[index] == thread_id:
        mutex_held_by[index] = None
    # else: no effect
    return True
```

For a cycle-accurate emulator, `exec_atgetm` should be called each cycle while the thread's instruction pointer is parked on the ATGETM. The thread's pipeline stalls (no further instructions issue) until the function returns `True`.

For a functional emulator that doesn't model cycle-level timing, you can treat ATGETM as an immediate acquire if the mutex is free, and use a simple scheduling policy (round-robin or arbitrary) to resolve contention when multiple threads attempt to acquire the same mutex in the same "step."

### Fairness (optional for functional emulation)

If modeling round-robin fairness: when `exec_atrelm` releases mutex `i` from thread `t`, and both other threads are stalled on ATGETM for mutex `i`, the next acquirer should be thread `(t + 1) % 3`.

---

## Real-World Usage Pattern

The primary use of mutexes in existing kernels is protecting shared config register read-modify-write (RMW) sequences between T0 (unpack) and T2 (pack), since both threads need to modify `ALU_FORMAT_SPEC_REG` registers:

```c
// T0 (cunpack_common.h) — unpack config
t6_mutex_acquire(mutex::REG_RMW);    // ATGETM(0)
cfg_reg_rmw_tensix<ALU_FORMAT_SPEC_REG_SrcA_val_ADDR32, ...>(alu_src_format);
// ... more RMW operations ...
t6_mutex_release(mutex::REG_RMW);    // ATRELM(0)

// T2 (cpack_common.h) — pack config
t6_mutex_acquire(mutex::REG_RMW);    // ATGETM(0)
cfg_reg_rmw_tensix<ALU_FORMAT_SPEC_REG2_Dstacc_RMW>(pack_output_src_format);
cfg_reg_rmw_tensix<STACC_RELU_ApplyRelu_ADDR32, ...>(relu_config);
t6_mutex_release(mutex::REG_RMW);    // ATRELM(0)
```

The C++ layer provides an RAII guard for convenience:

```c++
// ckernel_mutex_guard.h
{
    T6MutexLockGuard guard(mutex::REG_RMW);
    // critical section — automatically released on scope exit
}
```
