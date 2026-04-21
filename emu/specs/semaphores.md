# Semaphores

There are two completely separate semaphore systems. They share the name but have nothing in common architecturally.

## 1. Tensix Hardware Semaphores (Coprocessor Sync Unit)

8 semaphores inside the Tensix coprocessor, each with a 4-bit `Value` (0-15) and 4-bit `Max` (0-15).

| Index | Name                  | Purpose                                   |
|------:|-----------------------|-------------------------------------------|
|     0 | `FPU_SFPU`            | FPU <-> SFPU sync                         |
|     1 | `MATH_PACK`           | Math <-> Packer sync on dest register     |
|     2 | `UNPACK_TO_DEST`      | Unpack <-> Math sync                      |
|     3 | `UNPACK_OPERAND_SYNC` | Unpack <-> Pack/Math on operand get/release|
|     4 | `PACK_DONE`           | Pack iteration start/end                  |
|     5 | `UNPACK_SYNC`         | TRISC <-> Unpack sync                     |
|     6 | `UNPACK_MATH_DONE`    | Unpack or math iteration done             |
|     7 | `MATH_DONE`           | Wait for math when unpacking to dest      |

### Manipulation via Coprocessor Instructions

These are Tensix instructions pushed through the instruction FIFO (see `instruction-push.md`):

| Instruction     | Encoding example | Behavior |
|-----------------|------------------|----------|
| `ttseminit`     | `0x8c800022`     | Set Value=0 and Max for a semaphore |
| `ttsempost`     | `0x90000022`     | Increment Value (cap at Max) |
| `ttsemget`      | `0x94000022`     | Decrement Value (floor at 0) |
| `ttsemwait`     | `0x98020026`     | Stall coprocessor thread until Value meets condition |

These go through the coprocessor pipeline like any other Tensix instruction. They are ordered with respect to other Tensix instructions in the same thread.

### Manipulation via PCBuf Semaphore Window (RISC-V bypass)

TRISC0/1/2 can also read/write hardware semaphores directly from RISC-V code through a memory-mapped window in the PCBuf address space, bypassing the instruction FIFO entirely. See `pcbufs.md` for details.

| Operation | Address | Behavior |
|-----------|---------|----------|
| Read sem[i] | `PC_BUF_BASE + 0x20 + i*4` | Returns `Semaphores[i].Value` |
| SEMPOST sem[i] | Write with `val & 1 == 0` | Increment Value (cap at 15) |
| SEMGET sem[i] | Write with `val & 1 == 1` | Decrement Value (floor at 0) |

The semaphore window is at a fixed offset from `PC_BUF_BASE` (`0xFFE80000`), so:

| Semaphore | Address |
|-----------|---------|
| sem[0] | `0xFFE80020` |
| sem[1] | `0xFFE80024` |
| ... | ... |
| sem[7] | `0xFFE8003C` |

All three TRISCs access the same address range (`0xFFE80020-0xFFE8003C`) since there is only one set of 8 semaphores per tile. BRISC and NCRISC cannot access this window.

### BRISC Initialization

At boot, BRISC initializes semaphores 1 (`MATH_PACK`), 2 (`UNPACK_TO_DEST`), and 7 (`MATH_DONE`) by constructing SEMINIT instruction words and pushing them through `instrn_buf_base(0)`:

```
opcode = 0xa3100000 | (1 << (sem_id + 2))
store opcode to 0xFFE40000   // push SEMINIT to T0's instruction FIFO
```

### Per-Core Access

| Core   | Via coprocessor instructions | Via PCBuf window | Notes |
|--------|------------------------------|------------------|-------|
| BRISC  | Can push SEMINIT through instrn_buf | No | Only at init time |
| NCRISC | No | No | No access to hardware semaphores at all |
| TRISC0 | Yes | Yes | Both paths available |
| TRISC1 | Yes | Yes | Both paths available |
| TRISC2 | Yes | Yes | Both paths available |

### Emulator Implementation

Model the 8 semaphores as an array of `{value: u4, max: u4}`. Handle:
1. Coprocessor instructions (`ttseminit/post/get/wait`) when they reach the execution stage of the Tensix pipeline.
2. Loads from `0xFFE80020-0xFFE8003C` return `semaphores[offset].value`.
3. Stores to `0xFFE80020-0xFFE8003C` do SEMPOST or SEMGET based on bit 0 of the written value.

---

## 2. Software Semaphores (L1 Memory Words)

These are plain `uint32_t` values in L1. No special hardware. If the emulator already supports L1 memory and NOC operations, these work automatically.

### What They Are

A "software semaphore" is just a 32-bit word at a 16-byte-aligned L1 address. The API:

```c
// Set = plain store
void noc_semaphore_set(volatile uint32_t* sem_addr, uint32_t val) {
    *sem_addr = val;
}

// Wait = spin-loop on a plain load
void noc_semaphore_wait(volatile uint32_t* sem_addr, uint32_t val) {
    do { invalidate_l1_cache(); } while (*sem_addr != val);
}
```

`invalidate_l1_cache()` is for Blackhole's optional L1 data cache. In emulation there's no cache, so this is a no-op. The wait is just a spin on a load.

### Layout in L1

The base address is not fixed. It's computed at kernel launch:

```c
sem_l1_base[index] = kernel_config_base[index] + launch_msg->kernel_config.sem_offset[index];
```

Each semaphore slot is 16 bytes (only first 4 used), up to 16 semaphores per core type = 256 bytes total.

```
get_semaphore(id) = sem_l1_base + id * 16
```

### Remote Signaling (Cross-Tile)

Three mechanisms, all using the NOC:

| Function | Mechanism | Use case |
|----------|-----------|----------|
| `noc_semaphore_set_remote` | Plain 4-byte NOC write | Single sender overwrites remote sem |
| `noc_semaphore_inc` | NOC atomic increment (`NOC_AT_INS_INCR_GET`) | Multiple senders safely increment one receiver |
| `noc_semaphore_set_multicast` | NOC multicast write | Signal multiple tiles at once |

The NOC atomic increment (`noc_semaphore_inc`) is the only part that uses hardware assist. It programs the NIU AT command buffer with opcode `0x1` (INCR_GET), which performs a read-modify-write at the destination L1 address and returns the old value to `MEM_NOC_ATOMIC_RET_VAL_ADDR` (L1 offset 4).

Blackhole-specific: all atomics are forced non-posted (require ack) due to a hardware issue with memory port contention.

### Per-Core Access

All 5 RISC-V cores can read/write software semaphores (they're just L1 memory). BRISC and NCRISC are the primary users for cross-tile coordination. TRISCs can access them too but typically use hardware semaphores for intra-tile sync.

### Emulator Implementation

Nothing to do. These are plain L1 loads/stores and NOC writes/atomics, all of which the emulator already handles.
