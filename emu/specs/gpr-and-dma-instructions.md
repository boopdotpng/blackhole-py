# Tensix GPRs, Scalar Unit, and Configuration Unit Instructions

The Tensix coprocessor has a 192-register GPR (General Purpose Register) file that serves as a staging area for values destined for backend configuration registers. The RISC-V cores load constants into GPRs, then Tensix instructions copy those values into the config registers that control hardware units (unpackers, packers, matrix unit, etc.).

```
SETDMAREG → GPR → (sync) → WRCFG/RDCFG/RMWCIB/SETC16 → Config/ThreadConfig → controls hardware
```

Two execution units are involved:
- **Scalar Unit (ThCon):** Operates on GPRs. Runs SETDMAREG, ADDDMAREG, MULDMAREG, DMANOP, etc.
- **Configuration Unit:** Reads/writes config registers. Runs WRCFG, RDCFG, SETC16, RMWCIB, etc.


## GPR File Layout

The GPR file is mapped at `0xFFE00000` in the RISC-V address space:

```
0xFFE00000 .. 0xFFE000FF   Thread 0 (T0) — 64 x 32-bit registers (256 bytes)
0xFFE00100 .. 0xFFE001FF   Thread 1 (T1) — 64 x 32-bit registers
0xFFE00200 .. 0xFFE002FF   Thread 2 (T2) — 64 x 32-bit registers
```

The ISA models them as:
```c
uint32_t GPRs[3][64];   // 192 total, 64 per thread
```

The address space reservation extends to `0xFFE3FFFF` (256 KiB), but only 768 bytes are populated.

### Access Rules

- Each coprocessor thread (T0/T1/T2) can only access its own 64 GPRs via Tensix instructions.
- BRISC has full MMIO read/write access to all three threads' GPRs.
- NCRISC has no access.
- Each RISC-V T*i* also has its own GPRs mapped at `REGFILE_BASE` (`0xFFE00000`), but can only see `GPRs[i]`.

### Sub-Word Addressing

SETDMAREG addresses GPRs in **16-bit half-register** units. The index space is 0–127 (7 bits):
- Index `2*n` = low 16 bits of GPR `n`
- Index `2*n+1` = high 16 bits of GPR `n`

```c
#define LO_16(REG) (2 * (REG))       // low half of GPR
#define HI_16(REG) (2 * (REG) + 1)   // high half of GPR
```

### Named GPR Conventions

From `tt-llk/.../ckernel_gpr_map.h`:

**Common (all threads):**
| GPR | Name | Purpose |
|-----|------|---------|
| 0 | `ZERO` | Always 0 |
| 1 | `DBG_RESERVED` | Reserved |
| 2 | `DBG_MSG` | Firmware debug message |
| 3 | `DBG_CKID` | Ckernel ID |

**T0 (unpack thread):** GPRs 4–59 hold operand base/offset addresses, tile sizes, face dimensions, stride save/restore values.

**T1 (math thread):** GPRs 4–61 hold dest register offsets for SFPU, perf counters.

**T2 (pack thread):** GPRs 4–63 hold output L1 address, tile headers, stride configs, edge offsets.


## Instructions

All four instructions execute on the **Scalar Unit (ThCon)**. The Scalar Unit is fully serialized: at most one instruction at a time, no internal pipelining, and it blocks all threads' Wait Gates while executing.

### SETDMAREG — Set 16 bits of one GPR (opcode 0x45)

The workhorse instruction. Writes a 16-bit immediate to one half of a GPR, leaving the other half unchanged. Loading a full 32-bit constant requires two SETDMAREG instructions.

**Encoding:**
```
[31:24] = 0x45  (opcode)
[23:22] = Payload_SigSelSize  (2 bits — used in signal mode only)
[21:8]  = Payload_SigSel      (14 bits — immediate value in load mode)
[7]     = SetSignalsMode       (0 = immediate load, 1 = signal/packer read)
[6:0]   = RegIndex16b          (7 bits — half-register index 0–127)
```

```c
#define TT_OP_SETDMAREG(Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b) \
    TT_OP(0x45, (((Payload_SigSelSize) << 22) + ((Payload_SigSel) << 8) \
               + ((SetSignalsMode) << 7) + ((RegIndex16b) << 0)))
```

**Functional model (immediate mode, SetSignalsMode=0):**
```c
uint16_t *HalfReg = (char*)&GPRs[CurrentThread][0] + ResultHalfReg * 2;
*HalfReg = NewValue;
```

**Signal mode (SetSignalsMode=1):** Reads 128 bits of packer configuration or state, then writes 16–128 bits to GPRs. The field layout changes meaning:

```c
TT_SETDMAREG(/* u2 */ ResultSize,
           ((/* u4 */ WhichPackers) << 7) +
           ((/* u4 */ InputSource ) << 3) +
             /* u3 */ InputHalfReg,
             1,  // SetSignalsMode = 1
             /* u7 */ ResultHalfReg)
```

`InputSource` selects what 128-bit value to read:

| InputSource | Value read (128 bits across Values[0..3]) |
|---|---|
| 0 | Per-packer `{AccTileSize[hi16], LastTileSize[lo16]}` for packers 0–3 |
| 1 | Per-packer `AllZeroFlags` for packers 0–3 |
| 2–5 | Full tile header for packer `InputSource-2`: TileSize, DataFormat, DisableZeroCompression, AllZeroFlags |
| 6–7 | 16-byte slice of exponent histogram for packer `WhichPackers` (bytes `[0..15]` or `[16..31]`) |
| 8 | Bit 0 of each packer's AllZeroFlags packed into Values[0] bits [3:0]; optionally resets AccTileSize (masked by WhichPackers) |
| 9 | `Packers[0].ExponentHistogramMaxExponent` |

`ResultSize` selects how many bits to write to GPRs:

| ResultSize | Effect |
|---|---|
| 0 | 16-bit: `HalfRegs[ResultHalfReg] = InputHalves[InputHalfReg]` |
| 1 | 32-bit: `GPRs[ResultHalfReg >> 1] = Values[InputHalfReg >> 1]` |
| 2 | 128-bit: writes all 4 Values to 4 consecutive aligned GPRs |
| 3 | 128-bit tile header: writes only tile header fields, preserving reserved bits |

**Performance:** 1 cycle (both modes).

### ADDDMAREG — 32-bit GPR addition (opcode 0x58)

```c
TT_ADDDMAREG(0, ResultReg, RightReg, LeftReg)   // reg + reg
TT_ADDDMAREG(1, ResultReg, RightImm6, LeftReg)  // reg + 6-bit unsigned immediate
```

**Encoding:**
```
[31:24] = 0x58
[23]    = OpBisConst  (0 = reg-reg, 1 = reg-immediate)
[17:12] = ResultRegIndex  (6 bits)
[11:6]  = OpBRegIndex     (6 bits — GPR index or 6-bit constant)
[5:0]   = OpARegIndex     (6 bits — GPR index)
```

**Functional model:**
```c
uint32_t LeftVal  = GPRs[CurrentThread][LeftReg];
uint32_t RightVal = OpBisConst ? RightImm6 : GPRs[CurrentThread][RightReg];
GPRs[CurrentThread][ResultReg] = LeftVal + RightVal;  // 32-bit, wraps on overflow
```

**Performance:** 3 cycles (immediate, or same aligned group of 4), 4 cycles otherwise.

### MULDMAREG — 16-bit unsigned multiply → 32-bit result (opcode 0x5A)

Same encoding layout as ADDDMAREG. Key distinction: **inputs are truncated to 16 bits**, but the product is a full 32-bit result.

```c
GPRs[CurrentThread][ResultReg] = (LeftVal & 0xFFFF) * (RightVal & 0xFFFF);
```

**Performance:** Same as ADDDMAREG.

### DMANOP — Scalar Unit NOP (opcode 0x60)

```c
#define TT_OP_DMANOP TT_OP(0x60, 0)
```

Does nothing, occupies the Scalar Unit for 1 cycle. Used as a pipeline bubble between SETDMAREG and WRCFG when the Scalar Unit is provably already idle (replacing STALLWAIT in carefully scheduled code paths).


### LOADIND — Indirect GPR Load from L1 (opcode 0x49)

Reads 8, 16, 32, or 128 bits from tile-local L1 memory into one or more GPRs, using an indirect address computed from two GPR values. The address register holds a 16-byte-aligned base, and a separate offset half-register provides the byte offset.

**Encoding:**
```
[31:24] = 0x49  (opcode)
[23:22] = SizeSel        (2 bits — 0=16B/4 GPRs, 1=32-bit, 2=16-bit, 3=8-bit)
[21:14] = OffsetIndex    (8 bits — half-register index for byte offset)
[13:12] = AutoIncSpec    (2 bits — 0=none, 1=+2B, 2=+4B, 3=+16B)
[11:6]  = DataRegIndex   (6 bits — destination GPR index)
[5:0]   = AddrRegIndex   (6 bits — base address GPR index)
```

```c
#define TT_OP_LOADIND(SizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex) \
    TT_OP(0x49, (((SizeSel) << 22) + ((OffsetIndex) << 14) + ((AutoIncSpec) << 12) \
               + ((DataRegIndex) << 6) + ((AddrRegIndex) << 0)))
```

**Address computation:**
```c
uint32_t L1Address = GPRs[CurrentThread][AddrRegIndex] * 16 + *OffsetHalfReg;
```

The `AddrRegIndex` GPR holds a **16-byte word address** (multiply by 16 to get byte address). The `OffsetIndex` selects a 16-bit half-register (using the same `HalfReg[index]` scheme as SETDMAREG) that provides a byte offset added to the base.

**Functional model:**
```c
uint32_t* GPR = &GPRs[CurrentThread][DataRegIndex & (SizeSel ? 0x3F : 0x3C)];
uint16_t* Offset = (uint16_t*)((char*)&GPRs[CurrentThread][0] + OffsetIndex * 2);
uint32_t L1Addr = GPRs[CurrentThread][AddrRegIndex] * 16 + *Offset;

// Auto-increment offset register
switch (AutoIncSpec) {
    case 0: break;              // no increment
    case 1: *Offset += 2;  break;  // +2 bytes
    case 2: *Offset += 4;  break;  // +4 bytes
    case 3: *Offset += 16; break;  // +16 bytes
}

// Deferred: data arrives asynchronously after the Scalar Unit releases
switch (SizeSel) {
    case 0: memcpy(GPR, (void*)(L1Addr & ~15), 16); break;  // 16B → 4 aligned GPRs
    case 1: *GPR = *(uint32_t*)(L1Addr & ~3);       break;  // 32-bit word
    case 2: *(uint16_t*)GPR = *(uint16_t*)(L1Addr & ~1); break;  // 16-bit, low half only
    case 3: *(uint8_t*)GPR  = *(uint8_t*)L1Addr;    break;  // 8-bit, low byte only
}
```

For `SizeSel=0` (16B), the destination register index is masked to a 4-aligned boundary (`& 0x3C`), and four consecutive GPRs are written.

**Synchronization:** The Scalar Unit dispatches the read request and releases after >= 3 cycles, but the GPR data arrives asynchronously. Software must issue `STALLWAIT(STALL_CFG, THCON)` (block=B7, wait=C0) before any instruction that consumes the loaded GPR value.

**Performance:** >= 3 cycles occupying the Scalar Unit.

**Parameter constants** (from `ckernel_instr_params.h`):
```c
struct p_ind {
    static constexpr uint32_t HIER_L1   = 0x1;  // MemHierSel for STOREIND
    static constexpr uint32_t INC_NONE  = 0x0;
    static constexpr uint32_t INC_2B    = 0x1;
    static constexpr uint32_t INC_4B    = 0x2;
    static constexpr uint32_t INC_16B   = 0x3;
    static constexpr uint32_t LD_16B    = 0;
    static constexpr uint32_t LD_32bit  = 1;
    static constexpr uint32_t LD_16bit  = 2;
    static constexpr uint32_t LD_8bit   = 3;
};
```

### STOREIND — Indirect Store from GPR (opcode 0x66)

The counterpart to LOADIND. A polymorphic instruction with three modes selected by bit [23] (`MemHierSel`) and bit [22] (`SizeSel`):

| MemHierSel | SizeSel | Mode |
|---|---|---|
| 1 | x | **L1 mode**: write GPR data to L1 memory |
| 0 | 1 | **MMIO mode**: write 32-bit GPR to MMIO register |
| 0 | 0 | **Src mode**: write 2 GPRs (4×BF16) to SrcA or SrcB register file |

**Encoding:**
```
[31:24] = 0x66  (opcode)
[23]    = MemHierSel     (1 = L1 write, 0 = regfile/MMIO write)
[22]    = SizeSel        (mode-dependent — see above)
[21]    = RegSizeSel     (mode-dependent — data width or Src select)
[20:14] = OffsetIndex    (7 bits — half-register index for byte offset)
[13:12] = AutoIncSpec    (2 bits — auto-increment: 0=none, 1=+2B, 2=+4B, 3=+16B)
[11:6]  = DataRegIndex   (6 bits — source GPR index)
[5:0]   = AddrRegIndex   (6 bits — base address GPR index)
```

```c
#define TT_OP_STOREIND(MemHierSel, SizeSel, RegSizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex) \
    TT_OP(0x66, (((MemHierSel) << 23) + ((SizeSel) << 22) + ((RegSizeSel) << 21) \
               + ((OffsetIndex) << 14) + ((AutoIncSpec) << 12) \
               + ((DataRegIndex) << 6) + ((AddrRegIndex) << 0)))
```

#### L1 Mode (`MemHierSel=1`): GPR → L1

Address computation identical to LOADIND. `SizeSel` and `RegSizeSel` together encode the transfer size (same 0/1/2/3 scheme: 16B, 32-bit, 16-bit, 8-bit).

```c
// Functional model (L1 mode):
uint32_t* GPR = &GPRs[CurrentThread][DataRegIndex & (Size ? 0x3F : 0x3C)];
uint16_t* Offset = (uint16_t*)((char*)&GPRs[CurrentThread][0] + OffsetIndex * 2);
uint32_t L1Addr = GPRs[CurrentThread][AddrRegIndex] * 16 + *Offset;

// Auto-increment
switch (AutoIncSpec) { /* same as LOADIND */ }

// Write to L1
switch (Size) {
    case 0: memcpy((void*)(L1Addr & ~15), GPR, 16); break;  // 16B from 4 GPRs
    case 1: *(uint32_t*)(L1Addr & ~3)  = *GPR;      break;  // 32-bit
    case 2: *(uint16_t*)(L1Addr & ~1)  = (uint16_t)*GPR; break;  // 16-bit
    case 3: *(uint8_t*)L1Addr          = (uint8_t)*GPR;  break;  // 8-bit
}
```

#### MMIO Mode (`MemHierSel=0, SizeSel=1`): GPR → MMIO Register

Always a 32-bit write to the `0xFFB_____` address range (Tensix MMIO window, lower bound `0xFFB11000`).

```c
uint16_t* Offset = (uint16_t*)((char*)&GPRs[CurrentThread][0] + OffsetIndex * 2);
uint32_t Addr = GPRs[CurrentThread][AddrRegIndex] + (*Offset >> 4);
Addr = 0xFFB00000 + (Addr & 0x000FFFFC);
*(uint32_t*)Addr = GPRs[CurrentThread][DataRegIndex];
// then apply AutoIncSpec to Offset
```

#### Src Mode (`MemHierSel=0, SizeSel=0`): 2×GPR → SrcA/SrcB

Bit [21] (`RegSizeSel`) selects SrcA (0) or SrcB (1). Writes 4×BF16 values extracted from two consecutive GPRs into the FPU source register file. Waits on bank ownership semaphore. Rarely used — for software-feeding matrix input data.

**Performance:** >= 3 cycles (all modes).

**Common usage (L1 mode — writing tile header from packer):**
```c
// Write 16B tile header from GPRs to output L1 address
TTI_STOREIND(1, 0, p_ind::LD_16B, LO_16(0), p_ind::INC_NONE,
             p_gpr_pack::TILE_HEADER, p_gpr_pack::OUTPUT_ADDR);
```


## Backend Configuration Model

Before describing the Config Unit instructions, here's the data they operate on. Two distinct configuration spaces exist:

```c
uint32_t Config[2][CFG_STATE_SIZE * 4];                          // thread-agnostic, two banks
struct {uint16_t Value, Padding[7];} ThreadConfig[3][THD_STATE_SIZE]; // per-thread, one bank each
```

Both are mapped contiguously at `TENSIX_CFG_BASE` (`0xFFEF0000`, 64 KiB).

**Config** — Thread-agnostic, double-buffered. The active bank is selected by `ThreadConfig[CurrentThread].CFG_STATE_ID_StateID`. Holds unpack tile descriptors, pack config, ALU formats, ADDR_MOD slots, packer output addresses, stride configs, etc. Writes to indices `>= GLOBAL_CFGREG_BASE_ADDR32` write to *both* banks simultaneously.

**ThreadConfig** — Per-thread, single-banked. Holds thread-specific fields like `CFG_STATE_ID` (bank selector), dest register offsets, unpack context config, clock gater control. Only writable by `SETC16`; RISC-V `sw` cannot write ThreadConfig.

The `cfg_defines.h` file defines `Name_ADDR32`, `Name_MASK`, `Name_SHAMT` constants for both spaces. The `// Registers for THREAD` section indexes ThreadConfig; all other sections index Config.

| | Config (thread-agnostic) | ThreadConfig (per-thread) |
|---|---|---|
| **Tensix write** | WRCFG, RMWCIB, REG2FLOP | SETC16 only |
| **Tensix read** | RDCFG, various implicit | Various implicit only |
| **RISC-V write** | `sw` only (with ordering hazards) | Cannot write directly |
| **RISC-V read** | `lw`/`lh`/`lb` | `lw`/`lh`/`lb` |

**Special side effects on write:**
- Writing anything to `Config[i][STATE_RESET_EN_ADDR32]` (except via RMWCIB) zeros all non-global config in that bank.
- Writing to `Config.PRNG_SEED_Seed_Val_ADDR32` reseeds all PRNGs.
- Writing to `ThreadConfig[i][CG_CTRL_EN_*]` or `[CG_CTRL_KICK_*]` immediately affects clock gaters.


## Configuration Unit Instructions

The Configuration Unit handles all config register reads and writes. It accesses the same GPRs as the Scalar Unit. Key throughput rules:

- **SETC16** has its own IPC group: up to 3 per cycle (one per thread), independent of everything else.
- **All other instructions** (WRCFG, RDCFG, RMWCIB, RISCV requests, Mover requests) share a single `Config` IPC group with sustained throughput of at most 1 per cycle. Excessive WRCFG from one thread can starve RDCFG/RMWCIB from other threads and delay RISC-V config accesses.

### WRCFG — Write GPR to Config (opcode 0xB0)

Copies 32 or 128 bits from a GPR to `Config`.

**Encoding:**
```
[31:24] = 0xB0
[21:16] = GprAddress  (6 bits — which GPR provides the data)
[15]    = wr128b      (0 = 32-bit write, 1 = 128-bit write)
[10:0]  = CfgReg      (11 bits — config register index, matches Name_ADDR32)
```

```c
#define TT_OP_WRCFG(GprAddress, wr128b, CfgReg) \
    TT_OP(0xb0, (((GprAddress) << 16) + ((wr128b) << 15) + ((CfgReg) << 0)))
```

**Functional model:**
```c
uint1_t StateID = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID;

if (Is128Bit) {
    // InputReg aligned to 4-GPR boundary; writes 4 consecutive config words
    memcpy(&Config[StateID][CfgIndex & ~3], &GPRs[CurrentThread][InputReg & ~3], 16);
} else {
    Config[StateID][CfgIndex] = GPRs[CurrentThread][InputReg];
}
```

**Performance:** 2 cycles, fully pipelined (one per cycle). The issuing thread is not blocked during the 2nd cycle. **The instruction immediately after WRCFG must not consume the config just written** — insert a NOP.

### RDCFG — Read Config to GPR (opcode 0xB1)

Reads 32 bits from `Config` into a GPR. Cannot read ThreadConfig.

**Encoding:**
```
[31:24] = 0xB1
[23:16] = GprAddress  (8 bits — but only low 6 used for GPR index)
[15:0]  = CfgReg      (16 bits — but only low 11 used for config index)
```

```c
#define TT_OP_RDCFG(GprAddress, CfgReg) \
    TT_OP(0xb1, (((GprAddress) << 16) + ((CfgReg) << 0)))
```

**Functional model:**
```c
uint1_t StateID = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID;
GPRs[CurrentThread][ResultReg] = Config[StateID][CfgIndex];
```

**Performance:** At least 2 cycles. The GPR result is not available immediately — the instruction(s) after RDCFG must not read the destination GPR. Use `STALLWAIT(STALL_CFG, CFGEXU)` after issuing RDCFG(s) to ensure the result has landed before consuming it.

**Wormhole B0 hardware bug:** If multiple threads issue RDCFG on the same cycle, all but one are silently dropped. Software must ensure single-thread RDCFG. Blackhole does not have this bug — RDCFG is fully pipelined there (one per cycle, non-blocking, but still needs a stall before consuming the GPR result).

### SETC16 — Write 16-bit immediate to ThreadConfig (opcode 0xB2)

The **only instruction that can write ThreadConfig**. Writes a 16-bit immediate to one entry in the current thread's ThreadConfig bank.

**Encoding:**
```
[31:24] = 0xB2
[23:16] = CfgIndex    (8 bits — indexes ThreadConfig, matches "Registers for THREAD" Name_ADDR32)
[15:0]  = NewValue    (16 bits — immediate value)
```

```c
#define TT_OP_SETC16(setc16_reg, setc16_value) \
    TT_OP(0xb2, (((setc16_reg) << 16) + ((setc16_value) << 0)))
```

**Functional model:**
```c
ThreadConfig[CurrentThread][CfgIndex].Value = NewValue;
```

It always writes to the **current thread's** bank — there is no cross-thread ThreadConfig access. The 16-bit value replaces the entire `Value` field of the ThreadConfig entry (each entry is 16 bits of value + padding).

**Performance:** 1 cycle. Up to 3 SETC16 instructions can execute per cycle (one from each thread) because it has its own IPC group, independent of the Config pipeline.

**Common uses:**
```c
// Switch active config bank (double-buffering)
TT_SETC16(CFG_STATE_ID_StateID_ADDR32, new_state_id);

// Set math dest offset
TT_SETC16(DEST_TARGET_REG_CFG_MATH_Offset_ADDR32, dst_index);

// Set unpack config context
TT_SETC16(UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32, 0x0104);
```

**Blackhole scheduling restriction:** After reset, `SETC16(CFG_STATE_ID_StateID_ADDR32, x)` must be executed once before any other config-bank-dependent instruction. Also, within a fused instruction bundle, instructions after a `CFG_STATE_ID` write must not depend on the new value.

### RMWCIB0/1/2/3 — Read-Modify-Write Config Byte (opcodes 0xB3–0xB6)

Atomic read-modify-write on a single byte of `Config`. The digit suffix (0/1/2/3) selects which byte within the 32-bit config word to modify.

**Encoding (same for all four, opcode differs):**
```
[31:24] = 0xB3 (RMWCIB0), 0xB4 (RMWCIB1), 0xB5 (RMWCIB2), 0xB6 (RMWCIB3)
[23:16] = Mask          (8 bits — which bits to modify)
[15:8]  = NewValue      (8 bits — new bit values)
[7:0]   = CfgRegAddr    (8 bits — config register index, matches Name_ADDR32)
```

```c
#define TT_OP_RMWCIB0(Mask, Data, CfgRegAddr) TT_OP(0xb3, (((Mask)<<16)+((Data)<<8)+((CfgRegAddr)<<0)))
#define TT_OP_RMWCIB1(Mask, Data, CfgRegAddr) TT_OP(0xb4, (((Mask)<<16)+((Data)<<8)+((CfgRegAddr)<<0)))
#define TT_OP_RMWCIB2(Mask, Data, CfgRegAddr) TT_OP(0xb5, (((Mask)<<16)+((Data)<<8)+((CfgRegAddr)<<0)))
#define TT_OP_RMWCIB3(Mask, Data, CfgRegAddr) TT_OP(0xb6, (((Mask)<<16)+((Data)<<8)+((CfgRegAddr)<<0)))
```

**Functional model:**
```c
uint1_t StateID = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID;
uint8_t* ByteAddr = (uint8_t*)&Config[StateID][CfgRegAddr] + Index1;  // Index1 = opcode digit (0-3)
atomic {
    uint8_t OldValue = *ByteAddr;
    *ByteAddr = (NewValue & Mask) | (OldValue & ~Mask);
}
```

The formula is: **bits where Mask=1 get NewValue; bits where Mask=0 keep OldValue**. This is the standard RMW pattern `(new & mask) | (old & ~mask)`.

**Performance:** 1 cycle (but may wait at Wait Gate if Config pipeline is busy).

**LLK wrapper** — `cfg_reg_rmw_tensix<CfgAddr32, Shamt, Mask>(val)` in `ckernel.h` decomposes a 32-bit mask+value write into up to 4 RMWCIB calls (one per non-zero byte lane):
```c
// Only emits RMWCIB for byte lanes where the mask is non-zero
if (mask_b0) TT_RMWCIB0(mask_b0, data_b0, CfgAddr32);
if (mask_b1) TT_RMWCIB1(mask_b1, data_b1, CfgAddr32);
if (mask_b2) TT_RMWCIB2(mask_b2, data_b2, CfgAddr32);
if (mask_b3) TT_RMWCIB3(mask_b3, data_b3, CfgAddr32);
```


## Synchronization: SETDMAREG → WRCFG

The Scalar Unit and Configuration Unit are independent asynchronous backend units. Software must synchronize between them. The standard pattern:

```c
// 1. Load 32-bit constant into GPR via two 16-bit halves
TT_SETDMAREG(0, LOWER_HALFWORD(value), 0, LO_16(p_gpr_pack::TMP0));
TT_SETDMAREG(0, UPPER_HALFWORD(value), 0, HI_16(p_gpr_pack::TMP0));

// 2. Stall Config Unit until Scalar Unit finishes
TTI_STALLWAIT(p_stall::STALL_CFG, p_stall::THCON);
//             B7=0x80: block CFG   C0=0x001: wait while ThCon busy

// 3. Copy GPR to config register
TTI_WRCFG(p_gpr_pack::TMP0, p_cfg::WRCFG_32b, TARGET_ADDR32);

// 4. NOPs — WRCFG takes 2 cycles, next insn must not read this config
TTI_NOP;
TTI_NOP;
```

### RISC-V Direct Write Alternative

BRISC can write GPRs directly via stores to `0xFFE00000`, but must ensure the write completes before pushing a Tensix instruction that reads the GPR. Three approaches:
1. Use SETDMAREG instead (preferred).
2. Push a STALLWAIT with condition C13 before the consuming instruction.
3. Use a load-back fence: `sw` to GPR, `lw` from same address, consume result, then `sw` to push the Tensix instruction.


## Examples from Real Disassemblies

### Firmware GPR Init (fw_trisc2.S)

TRISC2 firmware zeroes the T0 GPR file at boot:

```asm
# from disasms/rvir/fw_trisc2.S — zero_gprs
    lui  a5, 0xffe00          # a5 = 0xFFE00000 (GPR base)
    addi a4, a5, 256          # a4 = 0xFFE00100 (end of 64 GPRs)
zero_gprs:
    sw   zero, 0(a5)          # *a5 = 0
    addi a5, a5, 4            # next GPR
    bne  a5, a4, zero_gprs    # loop until all 64 zeroed
```

### SETDMAREG → WRCFG Sequence (add1_trisc2.S)

Pack thread loading constants into GPRs 28–29, then writing to config:

```asm
# Build SETDMAREG instructions and push them to the T2 instruction FIFO (s0 = 0xFFE60000)
    lui  a4, 0x45000          # opcode 0x45, payload=0x0000
    addi a4, a4, 56           # RegIndex16b = 56 = LO_16(28)
    sw   a4, 0(s0)            # push: SETDMAREG(0, 0x0000, 0, LO_16(28))

    lui  a4, 0x45002          # opcode 0x45, payload=0x0002
    addi a4, a4, 57           # RegIndex16b = 57 = HI_16(28)
    sw   a4, 0(s0)            # push: SETDMAREG(0, 0x0002, 0, HI_16(28))

    lui  a4, 0x45020          # opcode 0x45, payload=0x0020
    addi a4, a4, 58           # RegIndex16b = 58 = LO_16(29)
    sw   a4, 0(s0)            # push: SETDMAREG(0, 0x0020, 0, LO_16(29))

    lui  a4, 0x45080          # opcode 0x45, payload=0x0080
    addi a4, a4, 59           # RegIndex16b = 59 = HI_16(29)
    sw   a4, 0(s0)            # push: SETDMAREG(0, 0x0080, 0, HI_16(29))

    # Inline Tensix: wait for Scalar Unit to finish
    TT_STALLWAIT 0x400001     # STALL_CFG, THCON

    # Inline Tensix: copy GPRs 28-29 to config
    TT_WRCFG 0x1c000c        # GPR 28 → Config[12], 32-bit
    TT_WRCFG 0x1d000d        # GPR 29 → Config[13], 32-bit
    TT_NOP
    TT_NOP
```

Note: The SETDMAREG instructions are built manually with `lui`+`addi` and pushed to the instruction FIFO via `sw` to `0xFFE60000`, while STALLWAIT/WRCFG/NOP appear as inline Tensix instructions in the rvir disassembly.

### RISC-V Direct GPR Write (add1_trisc2.S)

TRISC2 also writes GPRs directly via MMIO stores, bypassing SETDMAREG entirely:

```asm
    lui  s2, 0xffe00          # s2 = GPR base for this thread
    lui  a4, 0x1
    addi a4, a4, -2048        # a4 = 0x800
    sw   a4, 64(s2)           # GPR[16] = 0x800     (offset 64 = GPR index 16)
    sw   zero, 68(s2)         # GPR[17] = 0
    sw   zero, 72(s2)         # GPR[18] = 0
    sw   zero, 76(s2)         # GPR[19] = 0
    lw   a4, 76(s2)           # load-back fence: read GPR[19]
    sw   a4, 76(s2)           # consume result before pushing Tensix insn
```


## Encoding Quick Reference

### Scalar Unit (ThCon) — GPR operations

| Instruction | Opcode | Key Fields |
|---|---|---|
| SETDMAREG | 0x45 | `[23:22]` SigSelSize, `[21:8]` Payload, `[7]` SignalMode, `[6:0]` RegIndex16b |
| LOADIND | 0x49 | `[23:22]` SizeSel, `[21:14]` OffsetIndex, `[13:12]` AutoIncSpec, `[11:6]` DataReg, `[5:0]` AddrReg |
| ADDDMAREG | 0x58 | `[23]` OpBisConst, `[17:12]` Result, `[11:6]` OpB, `[5:0]` OpA |
| SUBDMAREG | 0x59 | (same as ADDDMAREG) |
| MULDMAREG | 0x5A | (same as ADDDMAREG) |
| DMANOP | 0x60 | (no fields) |
| STOREIND | 0x66 | `[23]` MemHierSel, `[22]` SizeSel, `[21]` RegSizeSel, `[20:14]` OffsetIdx, `[13:12]` AutoInc, `[11:6]` DataReg, `[5:0]` AddrReg |

### Configuration Unit — Config register operations

| Instruction | Opcode | Key Fields |
|---|---|---|
| WRCFG | 0xB0 | `[21:16]` GprAddr, `[15]` wr128b, `[10:0]` CfgReg |
| RDCFG | 0xB1 | `[23:16]` GprAddr, `[15:0]` CfgReg |
| SETC16 | 0xB2 | `[23:16]` CfgIndex (ThreadConfig), `[15:0]` NewValue |
| RMWCIB0 | 0xB3 | `[23:16]` Mask, `[15:8]` Data, `[7:0]` CfgRegAddr |
| RMWCIB1 | 0xB4 | (same as RMWCIB0, targets byte 1) |
| RMWCIB2 | 0xB5 | (same as RMWCIB0, targets byte 2) |
| RMWCIB3 | 0xB6 | (same as RMWCIB0, targets byte 3) |


## ISA Documentation Pointers

| File | Content |
|---|---|
| **Scalar Unit** | |
| `tt-isa-documentation/.../ScalarUnit.md` | GPR model, access rules, instruction latency table |
| `tt-isa-documentation/.../SETDMAREG_Immediate.md` | SETDMAREG load mode functional model |
| `tt-isa-documentation/.../SETDMAREG_Special.md` | SETDMAREG signal/packer-state mode (all InputSource/ResultSize combos) |
| `tt-isa-documentation/.../ADDDMAREG.md` | Addition functional model |
| `tt-isa-documentation/.../MULDMAREG.md` | Multiply functional model, 16-bit truncation |
| `tt-isa-documentation/.../DMANOP.md` | NOP functional model |
| **Configuration Unit** | |
| `tt-isa-documentation/.../ConfigurationUnit.md` | IPC groups, pipeline stages, throughput rules, starvation bugs |
| `tt-isa-documentation/.../BackendConfiguration.md` | Config vs ThreadConfig model, address space, special side effects |
| `tt-isa-documentation/.../WRCFG.md` | Config write from GPR, 32b vs 128b, scheduling |
| `tt-isa-documentation/.../RDCFG.md` | Config read to GPR, WH multi-thread bug, BH pipelining |
| `tt-isa-documentation/.../SETC16.md` | ThreadConfig write, BH scheduling restrictions |
| `tt-isa-documentation/.../RMWCIB.md` | Read-modify-write byte, mask formula, all 4 variants |
| **LLK headers** | |
| `tt-llk/.../ckernel_gpr_map.h` | Named GPR constants |
| `tt-llk/.../ckernel_ops.h` | Instruction encoding macros |
| `tt-llk/.../ckernel_defs.h` | `LO_16`/`HI_16`/`LOWER_HALFWORD`/`UPPER_HALFWORD` macros |
| `tt-llk/.../ckernel.h` | `cfg_reg_rmw_tensix` wrapper, `flip_cfg_state_id` |
| **Indirect Memory Ops** | |
| `tt-isa-documentation/.../LOADIND.md` | LOADIND functional model (WormholeB0 dir, applies to Blackhole) |
| `tt-isa-documentation/.../STOREIND.md` | STOREIND dispatcher (WormholeB0 dir) |
| `tt-isa-documentation/.../STOREIND_L1.md` | STOREIND L1 mode |
| `tt-isa-documentation/.../STOREIND_MMIO.md` | STOREIND MMIO mode |
| `tt-isa-documentation/.../STOREIND_Src.md` | STOREIND SrcA/SrcB mode |
| `tt-llk/.../ckernel_instr_params.h` | `struct p_ind` (HIER_L1, INC_*, LD_* constants) |
