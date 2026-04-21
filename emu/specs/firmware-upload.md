# Firmware Upload and Core Boot Process

## Overview

Each Tensix tile has **5 RISC-V cores**:

| Index | Name | Type | Role |
|-------|------|------|------|
| 0 | BRISC | DM0 | Master dispatcher, writer/dataflow out |
| 1 | NCRISC | DM1 | Data mover, reader/dataflow in |
| 2 | TRISC0 | MATH0 | Unpack |
| 3 | TRISC1 | MATH1 | Math/compute |
| 4 | TRISC2 | MATH2 | Pack |

The host uploads firmware to all worker cores in parallel via NOC multicast, then bootstraps them through a coordinated reset sequence. BRISC is the master — it releases the other 4 cores from reset and coordinates all kernel launches.

## Upload Sequence

Source: `device.py:202-276`

### Step 1: Assert soft reset

Write `0x47800` (`SOFT_RESET_ALL`) to MMIO register `0xFFB121B0` (`SOFT_RESET_0`) on all cores via multicast. This holds all 5 RISCs in reset.

### Step 2: Upload ELF segments via WC multicast

Each firmware ELF's `PT_LOAD` segments are written to L1 via write-combining (WC) TLB windows. Segments whose physical address falls in `0xFFB00000–0xFFB01FFF` (LOCAL_RAM, core-private SRAM) are remapped to a scratch area in L1 so that `do_crt1()` can later copy them into actual local memory at runtime.

All other segments are written directly to their L1 address.

### Step 3: Write boot stub at L1[0]

A single RISC-V JAL instruction encoding a jump to `0x3840` (`BRISC_FIRMWARE_BASE`) is written to L1 address 0:

```python
brisc_base = 0x3840
jal = ((brisc_base & 0xFF000)
     | ((brisc_base & 0x800) << 9)
     | ((brisc_base & 0x7FE) << 20)
     | 0x6F).to_bytes(4, "little")
```

When BRISC exits reset, its PC starts at 0 and immediately jumps to its firmware.

### Step 4: Write initial go_message

`{0x00, 0x00, 0x00, 0x40}` is written to L1 offset `0x370`. The signal byte (byte 3, at offset `0x373`) is `RUN_MSG_INIT = 0x40`.

### Step 5: Write bank-to-NOC mapping table

The DRAM and L1 bank-to-NOC-coordinate lookup table is written at L1 offset `0x116B0`.

### Step 6: Drain WC buffer

A read from the WC mmap forces all pending write-combining writes to complete before any subsequent MMIO updates.

### Step 7: Program subordinate reset PCs

The `.text` base address of each subordinate firmware ELF is written to the corresponding MMIO debug register:

| Register | Address | Target |
|----------|---------|--------|
| `NCRISC_RESET_PC` | `0xFFB12238` | NCRISC text base (e.g. `0x5440`) |
| `TRISC0_RESET_PC` | `0xFFB12228` | TRISC0 text base (e.g. `0x5A40`) |
| `TRISC1_RESET_PC` | `0xFFB1222C` | TRISC1 text base (e.g. `0x6040`) |
| `TRISC2_RESET_PC` | `0xFFB12230` | TRISC2 text base (e.g. `0x6A40`) |

These are override registers — BRISC firmware also sets the override enable bits (`TRISC_RESET_PC_OVERRIDE = 0b111`, `NCRISC_RESET_PC_OVERRIDE = 0x1`) so the hardware uses these values instead of hardcoded defaults.

### Step 8: Release BRISC from reset

Write `0x47000` (`SOFT_RESET_BRISC_ONLY_RUN`) to `0xFFB121B0`. Only BRISC is released; NCRISC and TRISCs remain in reset.

### Step 9: Poll for firmware ready

Host polls `L1[0x373]` (the signal byte of `go_messages[0]`) until it reads `0x00` (`RUN_MSG_DONE`). This indicates BRISC has completed its init, released all subordinates, waited for them to finish their init, and is ready for dispatch.

Timeout: 2 seconds, with 1 ms sleep between polls.


## Per-Core Firmware Behavior

### BRISC (DM0) — `firmware/brisc.cc`

#### Init Phase

1. `configure_csr()` — configure RISC-V CSRs (instruction cache, etc.)
2. `do_crt1(MEM_BRISC_INIT_LOCAL_L1_BASE_SCRATCH)` — copy initialized data from L1 scratch area into LOCAL_RAM at `0xFFB00000`, zero BSS section
3. `noc_bank_table_init(MEM_BANK_TO_NOC_SCRATCH)` — load DRAM/L1 bank-to-NOC-XY lookup tables from the table the host wrote
4. `noc_worker_logical_to_virtual_map_init()` — load logical-to-virtual coordinate mapping
5. `risc_init()` — read NOC coordinates (`my_x[0]`, `my_y[0]`, `my_x[1]`, `my_y[1]`) from hardware
6. `device_setup()`:
   - Initialize instruction/PC buffers for 3 Tensix threads
   - Write `0` to `RISCV_DEBUG_REG_DEST_CG_CTRL` (`0xFFB12240`) — disable dest clock gating
   - Write `0x3F` to `RISCV_TDMA_REG_CLK_GATE_EN` (`0xFFB11024`) — enable TDMA clock gating
   - Configure NOC0 and NOC1: set bit 0 of `NIU_CFG_0` and `ROUTER_CFG_0` on each
   - Enable reset PC override for subordinates
   - Zero 512 bytes at `MEM_ZEROS_BASE` (`0x3240`)
   - Invalidate all 5 instruction caches: write `0x1F` to `cfg_regs[RISCV_IC_INVALIDATE_InvalidateAll]`
   - Execute `ex_zeroacc`, `ex_encc`, `ex_load_const` on Tensix instruction buffer (ECC/accumulator init)
   - Enable ECC scrubber with delay `0x100`
   - Initialize Tensix semaphores
7. Set `subordinate_sync.all = 0x40404040` (`RUN_SYNC_MSG_ALL_INIT`)
8. `deassert_all_reset()` — release NCRISC + TRISC0/1/2 from soft reset
9. `wait_ncrisc_trisc()` — spin on `subordinate_sync.all` until it equals `0x00000000` (all 4 subordinates have written `RUN_SYNC_MSG_DONE`)
10. Set `go_messages[0].signal = RUN_MSG_DONE` (0x00) — the host sees this and knows the tile is ready
11. Initialize NOC (`noc_init`, `noc_local_state_init`)
12. `trigger_sync_register_init()` — write `0x03` to `subordinate_sync->trisc0` to tell TRISC0 to zero all CB tile counters

#### Dispatch Loop

```
while (1) {
    // 1. POLL: spin on go_messages[go_message_index].signal
    //    - Each iteration: invalidate_l1_cache() (fence instruction)
    //    - Also check launch[launch_msg_rd_ptr].preload for DISPATCH_ENABLE_FLAG_PRELOAD
    //    - Handle special signals:
    //        0xC0 (RESET_READ_PTR): reset launch_msg_rd_ptr=0, write DONE, notify dispatch
    //        0xF0 (REPLAY_TRACE): same as above + re-init profiler
    //    - Break when signal == RUN_MSG_GO (0x80) or preload flag set

    // 2. READ LAUNCH MESSAGE
    //    launch_msg = &mailboxes->launch[launch_msg_rd_ptr]
    //    enables = launch_msg->kernel_config.enables  (bitmask: bit0=BRISC, bit1=NCRISC, bit2-4=TRISC0-2)

    // 3. SIGNAL NCRISC TO PRELOAD
    //    if NCRISC enabled: subordinate_sync->dm1 = RUN_SYNC_MSG_LOAD (0x01)

    // 4. INIT CONFIG
    //    kernel_config_base = firmware_config_init(mailboxes, TENSIX, PROCESSOR_INDEX)
    //    This reads kernel_config_base from the launch message and sets up RTA/CRTA/semaphore pointers

    // 5. INVALIDATE ALL ICACHES
    //    cfg_regs[RISCV_IC_INVALIDATE] = 0x1F

    // 6. LAUNCH TRISCs
    //    Wait for trisc0 == DONE (from previous sync register init)
    //    If TRISC enabled: set trisc0=trisc1=trisc2 = RUN_SYNC_MSG_GO (0x80)

    // 7. CONFIGURE NOC + CB INTERFACES
    //    Set noc_index, noc_mode from launch_msg
    //    setup_local_cb_read_write_interfaces()
    //    setup_remote_cb_interfaces()

    // 8. LAUNCH NCRISC
    //    subordinate_sync->dm1 = RUN_SYNC_MSG_GO (0x80)

    // 9. RUN KERNEL OR WAIT
    //    if BRISC kernel enabled:
    //        kernel_lma = kernel_config_base + kernel_text_offset[0]
    //        stack_free = ((uint32_t(*)())kernel_lma)()
    //    else:
    //        wait_for_go_message()  // re-enter poll loop

    // 10. WAIT FOR SUBORDINATES
    //     wait_ncrisc_trisc()  — spin until subordinate_sync.all == 0

    // 11. RESET CB SYNC REGISTERS
    //     trigger_sync_register_init()  — subordinate_sync->trisc0 = 0x03

    // 12. SIGNAL COMPLETION
    //     go_messages[go_message_index].signal = RUN_MSG_DONE (0x00)
    //     If DISPATCH_MODE_DEV:
    //       Clear enables and preload in launch_msg
    //       notify_dispatch_core_done()  — NOC atomic increment to dispatch core
    //       Advance launch_msg_rd_ptr = (ptr + 1) & 7
}
```

### NCRISC (DM1) — `firmware/ncrisc.cc`

#### Init Phase

1. `configure_csr()`
2. `do_crt1(MEM_NCRISC_INIT_LOCAL_L1_BASE_SCRATCH)`
3. `noc_bank_table_init()`, `noc_worker_logical_to_virtual_map_init()`
4. `risc_init()`
5. Write `*ncrisc_run = RUN_SYNC_MSG_DONE` (0x00) — signal BRISC that init is complete

The sync byte pointer: `ncrisc_run = &mailboxes->subordinate_sync.map[0]` (L1 offset `0x068`, the `dm1` byte).

#### Main Loop

```
while (1) {
    // 1. POLL: spin on *ncrisc_run until GO (0x80) or LOAD (0x01)
    //    invalidate_l1_cache() between reads

    // 2. READ LAUNCH MESSAGE + INIT CONFIG
    //    launch_msg = &mailboxes->launch[launch_msg_rd_ptr]
    //    kernel_config_base = firmware_config_init()
    //    kernel_lma = kernel_config_base + kernel_text_offset[1]

    // 3. SET UP CB INTERFACES
    //    setup_local_cb_read_write_interfaces()
    //    setup_remote_cb_interfaces()

    // 4. WAIT FOR ACTUAL GO
    //    spin on *ncrisc_run until == RUN_SYNC_MSG_GO (0x80)
    //    (handles the LOAD → GO transition: BRISC sends LOAD first for CB preloading,
    //     then sends GO when ready to execute)

    // 5. RUN KERNEL
    //    stack_free = ((uint32_t(*)())kernel_lma)()

    // 6. SIGNAL DONE
    //    *ncrisc_run = RUN_SYNC_MSG_DONE (0x00)
}
```

### TRISC0/1/2 (Unpack/Math/Pack) — `firmware/trisc.cc`

Compiled 3 times with `COMPILE_FOR_TRISC` = 0, 1, 2.

#### Init Phase

1. `configure_csr()`
2. `do_crt1()` — copy data from L1 scratch for the specific TRISC
3. Zero the 64-entry Tensix GPR register file at `REGFILE_BASE` (`0xFFE00000`)
4. `reset_cfg_state_id()`
5. Seed PRNG: write 0 to `cfg[PRNG_SEED_Seed_Val]`
6. `riscv_wait(600)` — wait 600 cycles for PRNG to settle
7. Write `*trisc_run = RUN_SYNC_MSG_DONE` (0x00) — signal BRISC

The sync byte pointer: `trisc_run = &mailboxes->subordinate_sync.map[COMPILE_FOR_TRISC + 1]`
- TRISC0 → `map[1]` → L1 offset `0x069`
- TRISC1 → `map[2]` → L1 offset `0x06A`
- TRISC2 → `map[3]` → L1 offset `0x06B`

#### Main Loop

```
while (1) {
    // 1. POLL: spin on *trisc_run until RUN_SYNC_MSG_GO (0x80)
    //    invalidate_l1_cache() between reads
    //
    //    TRISC0 ONLY: also handles RUN_SYNC_MSG_INIT_SYNC_REGISTERS (0x03)
    //      → zeroes all NUM_CIRCULAR_BUFFERS tiles_received and tiles_acked counters
    //        (hardware sync registers at 0xFFB48028 stepping by 0x20000 per CB)
    //      → writes *trisc_run = RUN_SYNC_MSG_DONE (0x00)
    //      → continues polling

    // 2. READ LAUNCH MESSAGE
    //    launch_msg = &mailboxes->launch[launch_msg_rd_ptr]
    //    kernel_config_base = launch_msg->kernel_config.kernel_config_base[TENSIX]

    // 3. SET UP CB INTERFACES (TRISC0 and TRISC2 only, not TRISC1/Math)
    //    TRISC0 (Unpack): setup_local_cb_read_write_interfaces<read=true, write=false>
    //    TRISC2 (Pack):   setup_local_cb_read_write_interfaces<read=false, write=true>

    // 4. SET UP RTA POINTERS
    //    rta_l1_base  = kernel_config_base + rta_offset[PROCESSOR_INDEX].rta_offset
    //    crta_l1_base = kernel_config_base + rta_offset[PROCESSOR_INDEX].crta_offset

    // 5. RUN KERNEL
    //    index = MATH0 + thread_id  (i.e., 2, 3, or 4)
    //    kernel_lma = kernel_config_base + kernel_text_offset[index]
    //    stack_free = ((uint32_t(*)())kernel_lma)()

    // 6. SYNC TENSIX PIPELINE
    //    tensix_sync()  — wait for Tensix hardware pipeline to drain

    // 7. SIGNAL DONE
    //    *trisc_run = RUN_SYNC_MSG_DONE (0x00)
}
```


## Protocol Constants

### go_msg_t signal values (host ↔ BRISC)

| Value | Name | Meaning |
|-------|------|---------|
| `0x00` | `RUN_MSG_DONE` | BRISC finished kernel, ready for next |
| `0x40` | `RUN_MSG_INIT` | Initial value written by host at upload time |
| `0x80` | `RUN_MSG_GO` | Launch kernel (written by host or dispatch core) |
| `0xC0` | `RUN_MSG_RESET_READ_PTR` | Reset launch_msg_rd_ptr to 0 (from dispatch) |
| `0xE0` | `RUN_MSG_RESET_READ_PTR_FROM_HOST` | Reset launch_msg_rd_ptr to 0 (from host) |
| `0xF0` | `RUN_MSG_REPLAY_TRACE` | Reset read pointer and replay trace |

### subordinate_sync byte values (BRISC ↔ subordinates)

| Value | Name | Meaning |
|-------|------|---------|
| `0x00` | `RUN_SYNC_MSG_DONE` | Subordinate finished (init or kernel) |
| `0x01` | `RUN_SYNC_MSG_LOAD` | BRISC→NCRISC: pre-load circular buffers |
| `0x02` | `RUN_SYNC_MSG_WAITING_FOR_RESET` | Subordinate waiting for reset |
| `0x03` | `RUN_SYNC_MSG_INIT_SYNC_REGISTERS` | BRISC→TRISC0: zero CB tile counters |
| `0x40` | `RUN_SYNC_MSG_INIT` | Initial value at reset |
| `0x80` | `RUN_SYNC_MSG_GO` | BRISC→subordinate: execute kernel now |

Aggregate constants:
- `0x40404040` = `RUN_SYNC_MSG_ALL_INIT`
- `0x80808080` = `RUN_SYNC_MSG_ALL_GO`
- `0x00000000` = `RUN_SYNC_MSG_ALL_SUBORDINATES_DONE`


## Data Structures

### `go_msg_t` (4 bytes, at L1 offset `0x370` + index*4)

```
struct go_msg_t {
    union {
        uint32_t all;
        struct {
            uint8_t dispatch_message_offset;  // byte 0
            uint8_t master_x;                 // byte 1 — dispatch core NOC X
            uint8_t master_y;                 // byte 2 — dispatch core NOC Y
            uint8_t signal;                   // byte 3 — RUN_MSG_* value
        };
    };
};
```

9 entries in the ring buffer. `go_message_index` at L1 `0x3A0` selects which entry is active.

### `subordinate_sync` (4 bytes, at L1 offset `0x068`)

```
union subordinate_map_t {
    volatile uint32_t all;
    struct {
        volatile uint8_t dm1;     // byte 0 — NCRISC sync
        volatile uint8_t trisc0;  // byte 1 — TRISC0 sync
        volatile uint8_t trisc1;  // byte 2 — TRISC1 sync
        volatile uint8_t trisc2;  // byte 3 — TRISC2 sync
    };
};
```

BRISC polls `all` as a single 32-bit read for fast "all done" checks.

### `kernel_config_msg_t` (embedded in `launch_msg_t`)

```
struct kernel_config_msg_t {
    uint32_t kernel_config_base[3];       // per ProgrammableCoreType (TENSIX, ACTIVE_ETH, IDLE_ETH)
    uint16_t sem_offset[3];               // semaphore region offset within config
    uint16_t local_cb_offset;             // offset to local CB config blob
    uint16_t remote_cb_offset;            // offset to remote CB config blob
    rta_offset_t rta_offset[5];           // per-processor {rta_offset, crta_offset}
    uint8_t  mode;                        // DISPATCH_MODE_DEV(0) or DISPATCH_MODE_HOST(1)
    uint8_t  pad;
    uint32_t kernel_text_offset[5];       // per-processor kernel binary offset from kernel_config_base
    uint32_t local_cb_mask;               // bitmask of which CBs are local
    uint8_t  brisc_noc_id;                // which NOC BRISC uses (0 or 1)
    uint8_t  brisc_noc_mode;              // DM_DEDICATED_NOC(0) or DM_DYNAMIC_NOC(1)
    uint8_t  min_remote_cb_start_index;   // first remote CB index
    uint8_t  exit_erisc_kernel;
    uint32_t host_assigned_id;            // profiler program/launch ID
    uint32_t enables;                     // bitmask: bit0=BRISC, bit1=NCRISC, bit2=TRISC0, bit3=TRISC1, bit4=TRISC2
    uint16_t watcher_kernel_ids[5];
    uint16_t ncrisc_kernel_size16;        // NCRISC kernel size in 16-byte units
    uint8_t  sub_device_origin_x;
    uint8_t  sub_device_origin_y;
    uint8_t  pad3;
    uint8_t  preload;                     // DISPATCH_ENABLE_FLAG_PRELOAD = 0x80
} __attribute__((packed));
```

`launch_msg_t` is just a wrapper around `kernel_config_msg_t`. 8 entries in a ring buffer starting at L1 `0x070`, each 96 bytes.

### `mailboxes_t` (L1 offset `0x060`)

```
struct mailboxes_t {
    ncrisc_halt_msg_t ncrisc_halt;              // +0x00 (abs 0x060): {resume_addr, stack_save}
    subordinate_sync_msg_t subordinate_sync;    // +0x08 (abs 0x068): 4 sync bytes
    volatile uint32_t launch_msg_rd_ptr;        // +0x0C (abs 0x06C): ring buffer read index
    launch_msg_t launch[8];                     // +0x10 (abs 0x070): 8 x 96 bytes = 768 bytes
    volatile go_msg_t go_messages[9];           // +0x310 (abs 0x370): 9 x 4 bytes = 36 bytes
    uint64_t link_status_check_timestamp;       // (active erisc only)
    volatile uint32_t go_message_index;         // +0x340 (abs 0x3A0): which go_msg entry is active
    watcher_msg_t watcher;                      // debug watcher state
    dprint_buf_msg_t dprint_buf;                // debug print buffers
    core_info_msg_t core_info;                  // abs ~0x9A0: {noc addresses, logical coords, ...}
    uint32_t aerisc_run_flag;
    profiler_msg_t profiler;
};
```


## MMIO Register Map

### Reset Control

| Address | Name | Description |
|---------|------|-------------|
| `0xFFB121B0` | `SOFT_RESET_0` | Soft reset for all 5 cores. Values: `0x47800`=all held, `0x47000`=BRISC released only |
| `0xFFB12228` | `TRISC0_RESET_PC` | TRISC0 reset vector (set by host before release) |
| `0xFFB1222C` | `TRISC1_RESET_PC` | TRISC1 reset vector |
| `0xFFB12230` | `TRISC2_RESET_PC` | TRISC2 reset vector |
| `0xFFB12238` | `NCRISC_RESET_PC` | NCRISC reset vector |

BRISC always resets to PC=0 (the JAL stub in L1). Subordinate PCs are programmed via these override registers.

### Clock Gating

| Address | Name | Description |
|---------|------|-------------|
| `0xFFB12240` | `DEST_CG_CTRL` | Destination clock gate control (written to 0 during init) |
| `0xFFB11024` | `TDMA_CLK_GATE_EN` | TDMA clock gate enable (written to 0x3F during init) |

### Debug Bus (PC Readback)

| Address | Name | Description |
|---------|------|-------------|
| `0xFFB12054` | `DBG_BUS_CNTL` | Config register: `(1<<29) \| (rd_sel<<25) \| (daisy_sel<<16) \| sig_sel` |
| `0xFFB1205C` | `DBG_BUS_RD_DATA` | Read data, masked with `0x3FFFFFFF` for PC value |

Per-core signal configuration (all use rd_sel=1, daisy_sel=7):

| Core | sig_sel |
|------|---------|
| BRISC | 11 |
| TRISC0 | 13 |
| TRISC1 | 15 |
| TRISC2 | 17 |
| NCRISC | 25 |

### Wall Clock

| Address | Name |
|---------|------|
| `0xFFB121F0` | `WALL_CLOCK_L` — low 32 bits |
| `0xFFB121F8` | `WALL_CLOCK_H` — high 32 bits |

### Instruction Cache

Written via Tensix config register space:

```
cfg_regs[RISCV_IC_INVALIDATE_InvalidateAll_ADDR32] = mask
```

Mask bits:
- `0x01` = BRISC
- `0x02` = TRISC0
- `0x04` = TRISC1
- `0x08` = TRISC2
- `0x10` = NCRISC
- `0x1F` = all


## Core-Private Memory Regions

| Address Range | Name | Size | Notes |
|---------------|------|------|-------|
| `0xFFB00000–0xFFB01FFF` | LOCAL_RAM (LDM) | 8 KB (BRISC/NCRISC), 4 KB (TRISC) | Globals + stack, per-processor private |
| `0xFFE00000` | `REGFILE_BASE` | 256 bytes | 64 x 32-bit Tensix GPR register file |
| `0xFFE40000` | `INSTRN_BUF_BASE` | — | Tensix instruction buffer |
| `0xFFE80000` | `PC_BUF_BASE[0]` | — | Thread 0 PC buffer |
| `0xFFE90000` | `PC_BUF_BASE[1]` | — | Thread 1 PC buffer |
| `0xFFEA0000` | `PC_BUF_BASE[2]` | — | Thread 2 PC buffer |
| `0xFFEF0000` | `TENSIX_CFG_BASE` | — | Tensix configuration register space |


## L1 Memory Map

| Offset | Name | Size | Description |
|--------|------|------|-------------|
| `0x0000` | Boot JAL | 4 B | Jump instruction to BRISC firmware |
| `0x0004` | `NOC_ATOMIC_RET_VAL` | 8 B | NOC atomic operation return value |
| `0x000C` | `L1_BARRIER` | 4 B | L1 memory barrier |
| `0x0010` | `L1_ARC_FW_SCRATCH` | 16 B | ARC firmware scratch / power throttling |
| `0x0020` | `L1_INLINE_BASE` | 64 B | Emulated inline write staging (2 NOCs x 2 DMs x 16 B) |
| `0x0060` | `MAILBOX_BASE` | ~12768 B | `mailboxes_t` (see struct above) |
| `0x3240` | `ZEROS_BASE` | 512 B | Zeroed region for DMA zero-fills |
| `0x3440` | `LLK_DEBUG_BASE` | 1024 B | LLK debug storage |
| `0x3840` | `BRISC_FIRMWARE` | 7168 B | BRISC firmware code (XIP) |
| `0x5440` | `NCRISC_FIRMWARE` | 1536 B | NCRISC firmware code (XIP) |
| `0x5A40` | `TRISC0_FIRMWARE` | 1536 B | TRISC0 firmware code (XIP) |
| `0x6040` | `TRISC1_FIRMWARE` | 2560 B | TRISC1 firmware code (XIP) |
| `0x6A40` | `TRISC2_FIRMWARE` | 1536 B | TRISC2 firmware code (XIP) |
| `0x86B0` | `KERNEL_CONFIG_BASE` | variable | Kernel text + CB config + RTAs + semaphores |
| `0x116B0` | `BANK_TO_NOC_SCRATCH` | ~2 KB | Bank-to-NOC coordinate lookup tables |
| `0x37000` | `DATA_BUFFER_SPACE_BASE` | — | Start of user data buffer space |
| `0x180000` | End of L1 | — | Total L1 = 1.5 MB |


## Kernel Launch Flow Summary

The kernel entry point is not a named symbol. It is a raw function pointer call to whatever code sits at `kernel_config_base + kernel_text_offset[processor_index]` in L1:

```c
uint32_t kernel_lma = kernel_config_base + launch_msg->kernel_config.kernel_text_offset[index];
uint32_t stack_free = ((uint32_t(*)())kernel_lma)();
```

The kernel returns a `uint32_t` representing the stack high-water mark (used for profiling/watcher stack usage tracking).

### Processor Index Mapping

| Index | Enum | Core | Kernel Role |
|-------|------|------|-------------|
| 0 | `DM0` | BRISC | Writer / dataflow out |
| 1 | `DM1` | NCRISC | Reader / dataflow in |
| 2 | `MATH0` | TRISC0 | Unpack |
| 3 | `MATH1` | TRISC1 | Math / compute |
| 4 | `MATH2` | TRISC2 | Pack |

### Enables Bitmask

The `enables` field in `kernel_config_msg_t` controls which cores actually run a kernel:
- Bit 0 → BRISC
- Bit 1 → NCRISC
- Bit 2 → TRISC0
- Bit 3 → TRISC1
- Bit 4 → TRISC2

If a core's bit is not set, it skips the kernel call but still participates in the sync protocol.


## Coordination Timeline

```
HOST                    BRISC                  NCRISC              TRISC0/1/2
─────                   ─────                  ──────              ──────────
assert reset (all)
upload FW segments
write JAL at L1[0]
write go_msg = INIT
set subordinate PCs
release BRISC          ┌─ boot from L1[0]
                       │  do_crt1, init HW
                       │  sub_sync = ALL_INIT
                       │  deassert_all_reset() ┌─ boot from PC reg  ┌─ boot from PC reg
                       │                       │  do_crt1, init     │  do_crt1, init
                       │                       │  *ncrisc_run=DONE  │  *trisc_run=DONE
                       │  wait sub_sync==0  ◄──┘                 ◄──┘
                       │  go_msg.signal=DONE
poll go_msg==DONE  ◄───┘
                       │  [ready — polling go_msg for GO]

... kernel dispatch ...

write GO to go_msg ──► │  read launch_msg
                       │  sub->dm1 = LOAD ────► wake, load CBs
                       │  invalidate icaches
                       │  sub->trisc* = GO ──────────────────────► wake, read launch_msg
                       │  sub->dm1 = GO ──────► wake (LOAD→GO)
                       │  run BRISC kernel      run NCRISC kernel   run TRISC kernel
                       │  ...                   ...                 ...
                       │                        *ncrisc_run=DONE    tensix_sync()
                       │                                            *trisc_run=DONE
                       │  wait sub_sync==0  ◄── (all done)
                       │  go_msg.signal=DONE
                       │  notify_dispatch_core_done() (NOC atomic)
                       │  advance rd_ptr
                       └─ [loop: poll for next GO]
```
