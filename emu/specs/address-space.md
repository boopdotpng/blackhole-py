# Blackhole Tensix Tile Address Space

Complete address map for a single Tensix tile, from the perspective of the 5 on-tile RISC-V cores (BRISC, NCRISC, TRISC0/1/2). All addresses are 32-bit. The RISC-V cores use a flat memory-mapped address space with no MMU.

> **Version note:** The L1 mailbox layout (section 6) matches the `blackhole-py` dependency snapshot where `sizeof(launch_msg_t) = 96`. Current tt-metal main has widened `local_cb_mask` to `uint64_t`, shifting `go_messages` from `0x370` to `0x3F0` and `go_message_index` from `0x3A0` to `0x420`. The rest of the address space is unaffected.


## 1. Full Address Map Overview

```
 Address Range                    Size     Region
 ─────────────────────────────    ──────   ──────────────────────────────────────
 0x00000000 .. 0x0017FFFF         1.5 MiB  L1 shared tile memory (scratchpad)
           (gap)
 0xFFB00000 .. 0xFFB01FFF         8 KiB    LDM — core-private SRAM (fast path)
           (gap)
 0xFFB10000 .. 0xFFB10FFF         4 KiB    (reserved / unmapped)
 0xFFB11000 .. 0xFFB11FFF         4 KiB    TDMA mover registers
 0xFFB12000 .. 0xFFB12FFF         4 KiB    Debug / control registers
 0xFFB13000 .. 0xFFB13FFF         4 KiB    PIC regs + RISC-V PC readback
 0xFFB14000 .. 0xFFB15FFF         8 KiB    BRISC LDM (slow / cross-core path)
 0xFFB16000 .. 0xFFB17FFF         8 KiB    NCRISC LDM (slow / cross-core path)
 0xFFB18000 .. 0xFFB18FFF         4 KiB    TRISC0 LDM (slow / cross-core path)
 0xFFB19000 .. 0xFFB19FFF         4 KiB    (unused — alignment padding)
 0xFFB1A000 .. 0xFFB1AFFF         4 KiB    TRISC1 LDM (slow / cross-core path)
 0xFFB1B000 .. 0xFFB1BFFF         4 KiB    (unused — alignment padding)
 0xFFB1C000 .. 0xFFB1CFFF         4 KiB    TRISC2 LDM (slow / cross-core path)
 0xFFB1D000 .. 0xFFB1FFFF         12 KiB   (unused)
 0xFFB20000 .. 0xFFB2FFFF         64 KiB   NOC0 NIU registers
 0xFFB30000 .. 0xFFB3FFFF         64 KiB   NOC1 NIU registers
 0xFFB40000 .. 0xFFB7FFFF         256 KiB  Stream / NOC overlay registers (64 streams)
 0xFFB80000 .. 0xFFB800FF         256 B    MOP expander config
           (gap)
 0xFFBD8000 .. 0xFFBDFFFF         32 KiB   Dest register debug window
           (gap)
 0xFFE00000 .. 0xFFE002FF         768 B    Tensix GPR regfile (3 threads x 64 regs)
           (gap to 0xFFE3FFFF — regfile address space reservation)
 0xFFE40000 .. 0xFFE4FFFF         64 KiB   T0 instruction buffer FIFO
 0xFFE50000 .. 0xFFE5FFFF         64 KiB   T1 instruction buffer FIFO
 0xFFE60000 .. 0xFFE6FFFF         64 KiB   T2 instruction buffer FIFO
           (gap)
 0xFFE80000 .. 0xFFE8FFFF         64 KiB   T0 PCBuf / semaphore window
 0xFFE90000 .. 0xFFE9FFFF         64 KiB   T1 PCBuf / semaphore window
 0xFFEA0000 .. 0xFFEAFFFF         64 KiB   T2 PCBuf / semaphore window
           (gap)
 0xFFEC0000 .. 0xFFEC0FFF         4 KiB    Hardware mailbox 0 (BRISC)
 0xFFEC1000 .. 0xFFEC1FFF         4 KiB    Hardware mailbox 1 (TRISC0)
 0xFFEC2000 .. 0xFFEC2FFF         4 KiB    Hardware mailbox 2 (TRISC1)
 0xFFEC3000 .. 0xFFEC3FFF         4 KiB    Hardware mailbox 3 (TRISC2)
           (gap)
 0xFFEF0000 .. 0xFFEFFFFF         64 KiB   Tensix backend config registers
```


## 2. L1 Shared Tile Memory

```
Base:  0x00000000
End:   0x0017FFFF  (inclusive)
Size:  0x180000 = 1,572,864 bytes = 1.5 MiB
```

All 5 cores on the tile share a single L1 SRAM. Reads and writes from any core go to the same physical memory. External access (from other tiles via NoC, or from the host) also targets this space.

L1 is byte-addressable. There is no hardware coherence protocol — software must use `FENCE` (invalidate L1 cache) when one core writes a location that another core polls.

### L1 layout (low addresses)

The bottom of L1 is reserved for firmware mailboxes, firmware code, kernel config, and coordination structures. See **section 6** for the full mailbox layout.

```
Offset       Name                        Size      Description
──────       ────                        ────      ───────────
0x000000     Boot JAL                    4 B       RISC-V JAL to BRISC firmware base
0x000004     NOC_ATOMIC_RET_VAL          8 B       NoC atomic return value scratch
0x00000C     L1_BARRIER                  4 B       L1 memory barrier word
0x000010     L1_ARC_FW_SCRATCH           16 B      ARC firmware scratch / power throttle
0x000020     L1_INLINE_BASE              64 B      Emulated inline write staging
0x000060     MAILBOX_BASE                ~12 KiB   mailboxes_t (see section 6)
0x003240     ZEROS_BASE                  512 B     Pre-zeroed region for DMA fills
0x003440     LLK_DEBUG_BASE              1024 B    LLK debug storage
0x003840     BRISC_FIRMWARE              7168 B    BRISC firmware code (XIP from L1)
0x005440     NCRISC_FIRMWARE             1536 B    NCRISC firmware code
0x005A40     TRISC0_FIRMWARE             1536 B    TRISC0 firmware code
0x006040     TRISC1_FIRMWARE             2560 B    TRISC1 firmware code
0x006A40     TRISC2_FIRMWARE             1536 B    TRISC2 firmware code
0x0086B0     KERNEL_CONFIG_BASE          variable  Kernel text + CB config + RTAs + sems
0x0116B0     BANK_TO_NOC_SCRATCH         ~2 KiB    Bank-to-NOC coordinate lookup tables
0x037000     DATA_BUFFER_SPACE_BASE      —         Start of user data buffer space
0x180000     (end of L1)
```


## 3. Core-Private SRAM (LDM) — Fast Path

```
Base:  0xFFB00000
End:   0xFFB01FFF  (BRISC/NCRISC: 8 KiB)
       0xFFB00FFF  (TRISC0/1/2: 4 KiB)
```

Each of the 5 RISC-V cores has its own private local data memory (LDM). All cores see the **same address range** (`0xFFB00000`), but hardware routes each core's accesses to its own physical SRAM bank. This is a hardware-level alias — BRISC writing to `0xFFB00100` and TRISC0 writing to `0xFFB00100` write to completely different physical memory.

| Core   | LDM Size | Fast-Path Range                    |
|--------|----------|-------------------------------------|
| BRISC  | 8 KiB    | `0xFFB00000` .. `0xFFB01FFF`        |
| NCRISC | 8 KiB    | `0xFFB00000` .. `0xFFB01FFF`        |
| TRISC0 | 4 KiB    | `0xFFB00000` .. `0xFFB00FFF`        |
| TRISC1 | 4 KiB    | `0xFFB00000` .. `0xFFB00FFF`        |
| TRISC2 | 4 KiB    | `0xFFB00000` .. `0xFFB00FFF`        |

LDM holds each core's `.data`/`.bss` sections and stack. The firmware `do_crt1()` copies initialized data from an L1 scratch area into LDM at boot, then zeroes BSS.

### LDM contents

```
+0x000 .. +0x???   .data (initialized globals, copied from L1 by do_crt1)
+0x??? .. +0x???   .bss  (zeroed by do_crt1)
  ...
+0x??? .. +0xFFF   stack (grows downward from top of LDM)
  or  .. +0x1FFF   (for 8K cores)
```

### Emulator note

The emulator must maintain 5 separate LDM banks, all mapped at the same address range. The active bank is selected by which core is currently executing. A store from BRISC to `0xFFB00000` must not be visible to TRISC0 reading `0xFFB00000`.


## 4. Core-Private SRAM (LDM) — Slow / Cross-Core Path

When one core (or an external agent like the host or another tile) needs to access a specific core's LDM, it uses the core's unique NOC-visible address:

| Core   | Slow-Path Range                     | Size   |
|--------|--------------------------------------|--------|
| BRISC  | `0xFFB14000` .. `0xFFB15FFF`         | 8 KiB  |
| NCRISC | `0xFFB16000` .. `0xFFB17FFF`         | 8 KiB  |
| TRISC0 | `0xFFB18000` .. `0xFFB18FFF`         | 4 KiB  |
| TRISC1 | `0xFFB1A000` .. `0xFFB1AFFF`         | 4 KiB  |
| TRISC2 | `0xFFB1C000` .. `0xFFB1CFFF`         | 4 KiB  |

Stride between slots is `0x2000` (8 KiB) for uniform address decoding. TRISC cores only use the first 4 KiB of each 8 KiB slot; the upper 4 KiB is unmapped padding.

These addresses are used for:
1. Cross-core access on the same tile (e.g., BRISC reading TRISC0's LDM)
2. Remote access from another tile via NoC
3. Host / debug tooling (e.g., tt-exalens reading core state)

### Emulator note

A read from `0xFFB16000+offset` (by any core) returns NCRISC's LDM at `offset`. A write to `0xFFB14000+offset` goes to BRISC's LDM at `offset`. These are the same physical memories as the fast-path aliases in section 3, just accessible via non-aliased addresses.


## 5. Tensix Control Registers (`0xFFB10000 .. 0xFFB13FFF`)

### 5a. TDMA Mover Registers (`0xFFB11000`)

The TDMA engine handles bulk data movement between L1 and the Tensix datapath (unpack/pack). Register layout:

```
0xFFB11000   XMOV_SRC_ADDR       Source address
0xFFB11004   XMOV_DST_ADDR       Destination address
0xFFB11008   XMOV_SIZE            Transfer size
0xFFB1100C   XMOV_DIRECTION       Transfer direction
0xFFB11010   COMMAND_ADDR         Command register
0xFFB11014   STATUS               Busy/idle flags
0xFFB11018   PACKED_SIZE          Packed tile size (W)
0xFFB1101C   ACC_PACKED_SIZE (R)  Accumulated packed size (read)
             INITIAL_PACK_ACC (W) Initial accumulation value (write)
0xFFB11024   CLK_GATE_EN          Clock gating enable (firmware writes 0x3F at init)
0xFFB11028   CLK_GATE_HYST        Clock gating hysteresis
0xFFB1102C   XMOV_L1_BASE_ADDR   L1 base address for transfers
0xFFB11x30   FIFO_PACKED_TILE_SIZE(packer)    Per-packer (x = packer << 8)
0xFFB11x34   FIFO_PACKED_TILE_ZEROMASK(packer)
0xFFB11038   FIFO_PACKED_TILE_STATUS
```

### 5b. Debug / Control Registers (`0xFFB12000`)

Main control plane for the tile. Contains performance counters, soft reset control, PC override registers, wall clock, watchdog, ECC, and debug bus.

Key registers used by firmware:

```
0xFFB12054   DBG_BUS_CTRL         Debug bus config (PC readback selector)
0xFFB1205C   DBG_RD_DATA          Debug bus read data
0xFFB121B0   SOFT_RESET_0         Core reset control
                                    0x47800 = all held in reset
                                    0x47000 = BRISC released only
0xFFB121D0   ECC_CTRL             ECC scrubber control
0xFFB121E0   WATCHDOG_TIMER       Watchdog timer value
0xFFB121F0   WALL_CLOCK_L         Wall clock low 32 bits
0xFFB121F8   WALL_CLOCK_H         Wall clock high 32 bits
0xFFB12228   TRISC0_RESET_PC      TRISC0 reset vector override
0xFFB1222C   TRISC1_RESET_PC      TRISC1 reset vector override
0xFFB12230   TRISC2_RESET_PC      TRISC2 reset vector override
0xFFB12234   TRISC_RESET_PC_OVERRIDE    Enable bits (0b111 = all TRISCs)
0xFFB12238   NCRISC_RESET_PC      NCRISC reset vector override
0xFFB1223C   NCRISC_RESET_PC_OVERRIDE   Enable bit (0x1)
0xFFB12240   DEST_CG_CTRL         Dest clock gate control (written to 0 at init)
```

### 5c. PIC Registers (`0xFFB13000`)

Programmable interrupt controller, 56 bytes. Used for inter-core interrupts. Not needed for basic emulation.

### 5d. RISC-V PC Readback (`0xFFB13138`)

20 bytes (5 cores x 4 bytes). Debug-only readback of current PC for each core.


## 6. NIU Registers (`0xFFB20000` / `0xFFB30000`)

Each tile has two independent Network-on-Chip Interface Units:

| NIU  | Base Address  | Size    |
|------|---------------|---------|
| NoC0 | `0xFFB20000`  | 64 KiB  |
| NoC1 | `0xFFB30000`  | 64 KiB  |

See `niu.md` for full register-level documentation. Summary of sub-regions within each NIU:

```
Base+0x0000 .. +0x1FFF   4 command buffers (stride 0x800)
Base+0x0040 .. +0x0068   Misc control (CMD_CTRL, NODE_ID, CMD_BUF_AVAIL)
Base+0x0100 .. +0x017F   Configuration (NIU_CFG_0, NOC_ID_LOGICAL, translate tables)
Base+0x0200 .. +0x02FF   Status counters (128 x 4 bytes, for barrier polling)
```

Critical register: `NOC_ID_LOGICAL` at `NIU_base + 0x148` — firmware reads this during `noc_init()` to discover the tile's logical coordinates. Must be pre-populated by the emulator.


## 7. Stream / NOC Overlay Registers (`0xFFB40000 .. 0xFFB7FFFF`)

```
Base:    0xFFB40000
Streams: 64
Stride:  0x1000 (4 KiB per stream)
End:     0xFFB7FFFF
Size:    256 KiB
```

`STREAM_REG_ADDR(stream_id, reg_id) = 0xFFB40000 + stream_id * 0x1000 + reg_id * 4`

The stream engine can issue NoC transactions for pipelined data movement. Includes circular buffer tile counter registers used for CB synchronization:

```
Stream base + 0x028 = tiles_received counter
Stream base + 0x02C = tiles_acked counter
```

TRISC0 zeroes these during `RUN_SYNC_MSG_INIT_SYNC_REGISTERS` (signal `0x03` from BRISC), stepping through each CB's stream at stride `0x20000`:
```
0xFFB48028, 0xFFB68028, 0xFFB88028, ...  (tiles_received per CB)
0xFFB4802C, 0xFFB6802C, 0xFFB8802C, ...  (tiles_acked per CB)
```

Not needed for basic compute kernel emulation (add1, matmul_peak use the raw NIU path).


## 8. MOP Expander Config (`0xFFB80000`)

```
Base:  0xFFB80000
Size:  0x100 (reserved), 0x24 = 36 bytes actual per-thread content
```

9 write-only 32-bit registers that configure the MOP (Macro-OP) expander. The MOP expander takes a single `TT_MOP` instruction and expands it into a loop of up to 32,639 individual Tensix instructions according to these templates.

Each thread has its own MOP configuration set. Written by TRISC firmware before issuing `TT_MOP` instructions.


## 9. Dest Register Debug Window (`0xFFBD8000`)

```
Base:  0xFFBD8000
End:   0xFFBDFFFF
Size:  0x8000 = 32 KiB  (8 tiles x 1024 entries x 4 bytes)
```

Memory-mapped read-only view of the Dest accumulator register file. Used by debug tooling (tt-exalens) to inspect Dest contents. Not used by normal kernel execution — kernels access Dest through Tensix instructions (`SFPLOAD`, `SFPSTORE`, `PACR`, `UNPACR`, etc.).


## 10. Tensix GPR Regfile (`0xFFE00000`)

```
Base:    0xFFE00000  (address space reservation extends to 0xFFE3FFFF)
Actual:  3 threads x 64 registers x 4 bytes = 768 bytes
```

| Thread | Address Range                  | Registers |
|--------|--------------------------------|-----------|
| T0     | `0xFFE00000` .. `0xFFE000FF`   | 64 x 32-bit |
| T1     | `0xFFE00100` .. `0xFFE001FF`   | 64 x 32-bit |
| T2     | `0xFFE00200` .. `0xFFE002FF`   | 64 x 32-bit |

These are the ThCon (Thread Context) general-purpose registers used by the Tensix scalar unit. Accessed by `SETDMAREG`, `ADDDMAREG`, `WRCFG` and related instructions. TRISC firmware zeroes the T0 regfile (at `0xFFE00000`, 256 bytes) during init.

BRISC has direct MMIO access to all three threads' regfiles. Each TRISC only accesses its own thread's regfile through Tensix instructions.


## 11. Tensix Instruction Buffer FIFOs (`0xFFE40000`)

```
T0:  0xFFE40000  (INSTRN_BUF_BASE)
T1:  0xFFE50000  (INSTRN1_BUF_BASE)
T2:  0xFFE60000  (INSTRN2_BUF_BASE)
Stride: 0x10000  (64 KiB per thread)
```

Write-only FIFOs. A 32-bit store to any of these addresses pushes a Tensix instruction word into the corresponding thread's instruction FIFO (32 slots deep). If the FIFO is full, the RISC-V core stalls until a slot frees up.

### Context-sensitive routing

The hardware routes writes based on which core issues the store:

| Store Target   | From BRISC | From TRISC0 | From TRISC1 | From TRISC2 |
|----------------|------------|-------------|-------------|-------------|
| `0xFFE40000`   | T0 FIFO    | T0 FIFO     | T1 FIFO     | T2 FIFO     |
| `0xFFE50000`   | T1 FIFO    | **HANG**    | **HANG**    | **HANG**    |
| `0xFFE60000`   | T2 FIFO    | **HANG**    | **HANG**    | **HANG**    |

Each TRISC can only push to its own thread via `0xFFE40000`. Hardware remaps the address per-core. BRISC can target any thread directly.

### Emulator note

NCRISC has **no** Tensix instruction push capability. Any store from NCRISC to the instruction buffer address range should be flagged as an error.


## 12. PCBuf / Semaphore Window (`0xFFE80000`)

```
T0:  0xFFE80000  (PC_BUF_BASE)
T1:  0xFFE90000  (PC1_BUF_BASE)
T2:  0xFFEA0000  (PC2_BUF_BASE)
Stride: 0x10000  (64 KiB per thread)
Total: 192 KiB
```

Each thread's window is subdivided:

```
Offset   Size     Name         Description
──────   ────     ────         ───────────
+0x000   4 B      PCBuf        PC buffer control word
+0x004   0x1C     TTSync       TTSync registers (pipeline drain/sync)
+0x020   0xFFD0   Semaphores   Hardware semaphore access window
```

### PCBuf control

A read from `PC_BUF_BASE + 4` (the TTSync word) blocks until the thread's Tensix pipeline is fully drained. This is how `tensix_sync()` works — TRISCs issue a blocking load from `pc_buf_base[1]` to ensure all coprocessor instructions have completed before signaling done.

### Semaphore window

The semaphore region at `+0x020` provides RISC-V load/store access to the 8 hardware Tensix semaphores, bypassing the instruction pipeline. This lets cores read semaphore values directly (e.g., for debug or polling) without issuing Tensix `SEMGET`/`SEMPOST` instructions.


## 13. Hardware Mailboxes (`0xFFEC0000`)

```
0xFFEC0000   Mailbox 0 (BRISC)    4 KiB
0xFFEC1000   Mailbox 1 (TRISC0)   4 KiB
0xFFEC2000   Mailbox 2 (TRISC1)   4 KiB
0xFFEC3000   Mailbox 3 (TRISC2)   4 KiB
```

Hardware FIFO-based mailboxes. A read retrieves a value written by Tensix coprocessor code, or returns 0 if empty. Not widely used by current firmware — inter-core coordination goes through L1 `subordinate_sync` instead.


## 14. Tensix Backend Config Registers (`0xFFEF0000`)

```
Base:  0xFFEF0000  (TENSIX_CFG_BASE)
End:   0xFFEFFFFF
Size:  0x10000 = 64 KiB
```

Shared configuration registers for the Tensix backend execution units. These control:
- Unpacker configuration (data format, tile dimensions, address counters)
- Packer configuration (output format, L1 write address, zero-write masks)
- FPU mode (accumulation, rounding)
- SFPU constants
- Instruction cache invalidation control
- PRNG seed
- ECC scrubber

Accessed through Tensix instructions (`WRCFG`, `RDCFG`, `SETC16`, `RMWCIB`) or direct MMIO reads. Firmware reads config registers via `cfg_regs[index]` where `cfg_regs` is a volatile pointer to `0xFFEF0000`:

```c
volatile uint32_t* cfg_regs = (volatile uint32_t*)TENSIX_CFG_BASE;
cfg_regs[RISCV_IC_INVALIDATE_InvalidateAll_ADDR32] = 0x1F;  // invalidate all icaches
```


## 15. L1 Mailbox Layout (`mailboxes_t` at `0x000060`)

The `mailboxes_t` structure begins at L1 offset `0x60` and contains all coordination state between the host, BRISC, and subordinate cores.

```
L1 Offset        Field                    Size     Description
─────────        ─────                    ────     ───────────
0x000060         ncrisc_halt.resume_addr  4 B      NCRISC halt/resume address
0x000064         ncrisc_halt.stack_save   4 B      NCRISC stack pointer save
0x000068         subordinate_sync         4 B      Per-core sync bytes (see below)
0x00006C         launch_msg_rd_ptr        4 B      Ring buffer read pointer (0..7)
0x000070         launch[8]                768 B    Launch message ring (8 x 96 bytes)
0x000370         go_messages[9]           36 B     Go message ring (9 x 4 bytes)
0x000398         link_status_check_ts     8 B      Link status timestamp (erisc only)
0x0003A0         go_message_index         4 B      Active go_message entry index
```

### `subordinate_sync` (`0x68`, 4 bytes)

```
Byte 0 (+0x68): NCRISC (dm1)  sync byte
Byte 1 (+0x69): TRISC0        sync byte
Byte 2 (+0x6A): TRISC1        sync byte
Byte 3 (+0x6B): TRISC2        sync byte
```

BRISC reads the full 32-bit word for fast "all done" checks (`sync.all == 0x00000000`). Subordinates write their individual byte.

| Value  | Name                            | Meaning                              |
|--------|---------------------------------|--------------------------------------|
| `0x00` | `RUN_SYNC_MSG_DONE`             | Subordinate finished (init or kernel)|
| `0x01` | `RUN_SYNC_MSG_LOAD`             | BRISC->NCRISC: pre-load CBs          |
| `0x03` | `RUN_SYNC_MSG_INIT_SYNC_REGISTERS` | BRISC->TRISC0: zero CB tile counters |
| `0x40` | `RUN_SYNC_MSG_INIT`             | Initial value at reset               |
| `0x80` | `RUN_SYNC_MSG_GO`               | BRISC->subordinate: execute kernel   |

Aggregate constants:
- `0x40404040` = `RUN_SYNC_MSG_ALL_INIT` (set by BRISC before releasing subordinates)
- `0x00000000` = all subordinates done

### `go_msg_t` (`0x370` + index*4, 4 bytes each)

```c
struct go_msg_t {
    uint8_t dispatch_message_offset;  // byte 0
    uint8_t master_x;                 // byte 1 — dispatch core NOC X
    uint8_t master_y;                 // byte 2 — dispatch core NOC Y
    uint8_t signal;                   // byte 3 — RUN_MSG_* value
};
```

`go_messages[0]` at L1 `0x370..0x373` is the primary entry. 9 entries exist in the ring, but only one is needed for workloads where the entire core grid runs the same program.

The `signal` byte (at `0x373` for entry 0) is the main handshake between host/dispatch and BRISC:

| Value  | Name                          | Meaning                                 |
|--------|-------------------------------|-----------------------------------------|
| `0x00` | `RUN_MSG_DONE`                | BRISC finished kernel, tile is idle     |
| `0x40` | `RUN_MSG_INIT`                | Initial value (host writes at upload)   |
| `0x80` | `RUN_MSG_GO`                  | Launch kernel (host or dispatch writes) |
| `0xC0` | `RUN_MSG_RESET_READ_PTR`      | Reset launch ring read pointer          |
| `0xF0` | `RUN_MSG_REPLAY_TRACE`        | Reset pointer + replay trace            |

**Slow dispatch:** `master_x` and `master_y` are unused (host polls `signal` directly). Only the `signal` byte matters.

**Fast dispatch:** `master_x` and `master_y` are set to the NoC coordinates of the fast dispatch core. BRISC sends a NoC atomic increment to that core's address as the completion notification.

### `launch_msg_t` (96 bytes each, 8 in ring starting at `0x70`)

Contains the full kernel configuration for one dispatch: which cores to enable, where kernel code lives, CB configuration offsets, NOC assignment, etc.

```
+0x00  kernel_config_base[3]         12 B   Per core-type config base address
+0x0C  sem_offset[3]                  6 B   Semaphore region offsets
+0x12  local_cb_offset                2 B   Local CB config blob offset
+0x14  remote_cb_offset               2 B   Remote CB config blob offset
+0x16  rta_offset[5]                 20 B   Per-processor {rta_offset, crta_offset}
+0x2A  mode                           1 B   DISPATCH_MODE_DEV(0) / HOST(1)
+0x2B  pad                            1 B
+0x2C  kernel_text_offset[5]         20 B   Per-processor kernel binary offset
+0x40  local_cb_mask                  4 B   Bitmask of local CBs (uint32_t)
+0x44  brisc_noc_id                   1 B   Which NOC BRISC uses (0 or 1)
+0x45  brisc_noc_mode                 1 B   DM_DEDICATED_NOC(0) / DM_DYNAMIC_NOC(1)
+0x46  min_remote_cb_start_index      1 B   First remote CB index
+0x47  exit_erisc_kernel              1 B
+0x48  host_assigned_id               4 B   Profiler program/launch ID
+0x4C  enables                        4 B   Core enable bitmask (see below)
+0x50  watcher_kernel_ids[5]         10 B
+0x5A  ncrisc_kernel_size16           2 B   NCRISC kernel size in 16B units
+0x5C  sub_device_origin_x            1 B
+0x5D  sub_device_origin_y            1 B
+0x5E  pad3                           1 B
+0x5F  preload                        1 B   DISPATCH_ENABLE_FLAG_PRELOAD = 0x80
       Total:                        96 B   (= 0x60)
```

**Enables bitmask:**
- Bit 0 -> BRISC
- Bit 1 -> NCRISC
- Bit 2 -> TRISC0
- Bit 3 -> TRISC1
- Bit 4 -> TRISC2

Kernel entry: `kernel_config_base[TENSIX] + kernel_text_offset[processor_index]` is a raw function pointer. The kernel returns a `uint32_t` (stack high-water mark).


## 16. Access Permissions by Core

Not all cores can access all regions. This table shows which cores have meaningful access:

| Region                     | BRISC | NCRISC | TRISC0 | TRISC1 | TRISC2 |
|----------------------------|-------|--------|--------|--------|--------|
| L1 (`0x000000..0x17FFFF`)  | R/W   | R/W    | R/W    | R/W    | R/W    |
| Own LDM (fast, `0xFFB0`)   | R/W   | R/W    | R/W    | R/W    | R/W    |
| Other core LDM (slow)      | R/W   | R/W    | R/W    | R/W    | R/W    |
| TDMA regs (`0xFFB11`)      | R/W   | R/W    | R/W    | R/W    | R/W    |
| Debug regs (`0xFFB12`)     | R/W   | R/W    | R/W    | R/W    | R/W    |
| NIU regs (`0xFFB2/3`)      | R/W   | R/W    | R/W    | R/W    | R/W    |
| Stream/overlay (`0xFFB4`)  | R/W   | R/W    | R/W    | R/W    | R/W    |
| MOP config (`0xFFB8`)      | W     | —      | W      | W      | W      |
| GPR regfile (`0xFFE0`)     | R/W*  | —      | own    | own    | own    |
| Instrn FIFO (`0xFFE4-6`)   | all 3 | **NO** | own    | own    | own    |
| PCBuf/Sem (`0xFFE8-A`)     | R/W*  | —      | own    | own    | own    |
| HW Mailbox (`0xFFEC`)      | own   | —      | own    | own    | own    |
| Config regs (`0xFFEF`)     | R/W   | R      | R/W    | R/W    | R/W    |

\* BRISC can access all 3 threads' regfile and PCBuf regions. TRISCs are restricted to their own thread. NCRISC has no Tensix access.


## Source References

| Purpose                     | File                                                                     |
|-----------------------------|--------------------------------------------------------------------------|
| Address map defines         | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix.h`            |
| Memory sizes and L1 layout  | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/dev_mem_map.h`       |
| Mailbox/launch structs      | `tt-metal/tt_metal/hw/inc/hostdev/dev_msgs.h`                           |
| NIU register defines        | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_parameters.h`|
| Stream/overlay defines      | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_overlay_parameters.h` |
| L1 address map (UMD)        | `tt-umd/src/firmware/riscv/blackhole/l1_address_map.h`                   |
| Hardware memory map model   | `tt-exalens/ttexalens/hardware/blackhole/functional_worker_block.py`     |
