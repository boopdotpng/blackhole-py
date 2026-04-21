# Configuration Unit and Sync Unit: Additional Instructions

Four instructions that interact with the backend configuration registers and the NoC overlay stream system. CFGSHIFTMASK and STREAMWRCFG execute on the Configuration Unit; STREAMWAIT executes on the Sync Unit; REG2FLOP executes on the Scalar Unit (ThCon).


## CFGSHIFTMASK — Read-Modify-Write Config via Scratch Register (opcode 0xB8)

### Overview

Performs a masked, rotated, ALU read-modify-write on a thread-agnostic `Config` register, using a value from one of the `SCRATCH_SEC[].val` configuration registers as the operand. This is more powerful than RMWCIB (which only does byte-granularity mask-and-set) — CFGSHIFTMASK can rotate, mask to arbitrary width, and apply one of 8 ALU operations.

Used 263 times across LLK ELFs, primarily in unpack tilize routines to update tile descriptor base addresses.

### Encoding

```
[31:24] = 0xB8
[23]    = MaskMode        (1 bit — 0=clear mask region first, 1=don't clear)
[22:20] = AluMode         (3 bits — ALU operation)
[19:15] = MaskWidth       (5 bits — mask is (2 << MaskWidth) - 1, i.e., MaskWidth+1 bits wide)
[14:10] = RotateAmt       (5 bits — circular right shift amount)
[9:8]   = ScratchIndex    (2 bits — which SCRATCH_SEC, or 3=use thread ID)
[7:0]   = CfgIndex        (8 bits — Config register ADDR32 index)
```

```c
#define TT_OP_CFGSHIFTMASK(disable_mask_on_old_val, operation, mask_width, \
                            right_cshift_amt, scratch_sel, CfgReg) \
    TT_OP(0xb8, (((disable_mask_on_old_val) << 23) + ((operation) << 20) \
               + ((mask_width) << 15) + ((right_cshift_amt) << 10) \
               + ((scratch_sel) << 8) + ((CfgReg) << 0)))
```

### ALU Modes

| AluMode | Operation |
|---------|-----------|
| 0 | `CfgValue \|= ScratchValue` (OR) |
| 1 | `CfgValue &= ScratchValue` (AND) |
| 2 | `CfgValue ^= ScratchValue` (XOR) |
| 3 | `CfgValue += ScratchValue` (ADD) |
| 4 | `CfgValue \|= ~ScratchValue` (OR-NOT) |
| 5 | `CfgValue &= ~ScratchValue` (AND-NOT) |
| 6 | `CfgValue ^= ~ScratchValue` (XOR-NOT) |
| 7 | `CfgValue -= ScratchValue` (SUB) |

### Functional Model

```python
def CFGSHIFTMASK(mask_mode, alu_mode, mask_width, rotate_amt, scratch_index, cfg_index):
    # Select scratch register value
    if scratch_index < 3:
        scratch_val = Config.SCRATCH_SEC[scratch_index].val
    else:
        scratch_val = Config.SCRATCH_SEC[CurrentThread].val

    # Build mask and apply rotation
    mask_val = (2 << mask_width) - 1                     # MaskWidth+1 bits of 1s
    scratch_val = rotr32(scratch_val & mask_val, rotate_amt)

    # Read current config value
    state_id = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID
    cfg_val = Config[state_id][cfg_index]

    # Optionally clear the mask region in the old value
    if mask_mode == 0:
        cfg_val &= ~rotr32(mask_val, rotate_amt)

    # Apply ALU operation
    if   alu_mode == 0: cfg_val |=   scratch_val
    elif alu_mode == 1: cfg_val &=   scratch_val
    elif alu_mode == 2: cfg_val ^=   scratch_val
    elif alu_mode == 3: cfg_val  +=  scratch_val
    elif alu_mode == 4: cfg_val |=  ~scratch_val & 0xFFFFFFFF
    elif alu_mode == 5: cfg_val &=  ~scratch_val & 0xFFFFFFFF
    elif alu_mode == 6: cfg_val ^=  ~scratch_val & 0xFFFFFFFF
    elif alu_mode == 7: cfg_val  -=  scratch_val

    Config[state_id][cfg_index] = cfg_val & 0xFFFFFFFF

def rotr32(val, amount):
    amount &= 31
    return ((val >> amount) | (val << (32 - amount))) & 0xFFFFFFFF
```

### Performance and Scheduling

- 2 cycles, not pipelined (can start one every other cycle)
- The issuing thread is **not** blocked — it can start its next instruction during the 2nd cycle
- The instruction immediately after CFGSHIFTMASK must **not** consume the config value just written. Insert a NOP if needed. This restriction does not apply if the next instruction is itself a Configuration Unit instruction (the pipeline rules handle it).

### LLK Usage Example

```c
// From llk_unpack_tilize.h — update tile descriptor base address
TTI_CFGSHIFTMASK(1, 0b011, 32-1, 0, 0b11, THCON_SEC0_REG3_Base_address_ADDR32);
// MaskMode=1 (don't clear), AluMode=3 (ADD), MaskWidth=31 (full 32 bits),
// RotateAmt=0, ScratchIndex=3 (use thread ID), CfgReg=THCON_SEC0_REG3 base address
```


## REG2FLOP — Move from GPRs to THCON Configuration (opcode 0x48)

### Overview

Uses the Scalar Unit (ThCon) to write from the current thread's GPRs into `THCON_*` backend configuration fields. The target is always the `THCON_*` portion of the configuration register space — this instruction **cannot** address other configuration targets. For a more general configuration write (not limited to `THCON_*` fields), use `WRCFG` instead.

Used 414 times across LLK ELFs, heavily in unpack/pack routines (tilize, untilize, matmul).

> **ISA source:** `REG2FLOP_Configuration.md` in the WormholeB0 TensixCoprocessor ISA documentation.

### Encoding

```
TT_REG2FLOP(/* u2 */ SizeSel, 0, 0, 0, /* u7 */ ThConCfgIndex, /* u6 */ InputReg)
```

Fields other than `SizeSel`, `ThConCfgIndex`, and `InputReg` are reserved (must be zero) in the configuration variant documented by the ISA.

### SizeSel Values

| SizeSel | Transfer width |
|---------|----------------|
| 0       | 128-bit (16 bytes): copies 4 consecutive GPRs starting at `InputReg & ~3` into the 4 consecutive THCON config words starting at `ThConCfgIndex & ~3` |
| 1–3     | 32-bit: copies `GPRs[CurrentThread][InputReg]` into `ThConCfgBase[ThConCfgIndex]` |

No 8-bit or 16-bit write modes are defined for this instruction variant in the ISA.

### Functional Model

> Source: `REG2FLOP_Configuration.md` (WormholeB0 ISA)

```c
if (ThConCfgIndex >= (GLOBAL_CFGREG_BASE_ADDR32 - THCON_CFGREG_BASE_ADDR32)) {
  // Can only write to backend configuration whose field name starts with THCON_.
  // See WRCFG for a similar instruction without this limitation.
  UndefinedBehaviour();
}

uint1_t StateID = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID;
uint32_t* ThConCfgBase = &Config[StateID][THCON_CFGREG_BASE_ADDR32];

if (SizeSel == 0) {
  // 128-bit configuration write
  memcpy(&ThConCfgBase[ThConCfgIndex & ~3], &GPRs[CurrentThread][InputReg & ~3], 16);
} else {
  // 32-bit configuration write
  ThConCfgBase[ThConCfgIndex] = GPRs[CurrentThread][InputReg];
}
```

### Emulator Note

REG2FLOP (configuration variant) writes only to `THCON_*` configuration fields, routed through `Config[StateID]` offset by `THCON_CFGREG_BASE_ADDR32`. Indices at or above `GLOBAL_CFGREG_BASE_ADDR32 - THCON_CFGREG_BASE_ADDR32` are undefined behaviour per ISA. If the emulator models unpack/pack config through `Config`/`ThreadConfig` registers, map `ThConCfgIndex` to the corresponding `THCON_*` field offset; there is no separate "flop" target space for this variant.

### Performance

Typically two cycles; longer if Configuration Unit instructions from any Tensix thread or baby RISCV are contending for write bandwidth to THCON configuration. The Scalar Unit (ThCon) is occupied for the entire duration and the issuing thread is blocked until completion.

Stall bits: STALL_THCON (B5).


## STREAMWAIT — Wait on NoC Overlay Stream Condition (opcode 0xA7)

### Overview

A Blackhole-new instruction. Sets a persistent "wait condition" on the current thread keyed to a NoC overlay stream register. The thread can continue executing until it reaches an instruction type that is blocked by the block mask; at that point, execution pauses until the selected stream condition is met.

Unlike STALLWAIT (which stalls immediately), STREAMWAIT sets a latched condition that only triggers when a blocked instruction is encountered. This allows non-blocked work to continue in the meantime.

Used 235 times across LLK ELFs. Only exists on Blackhole (not Wormhole B0).

### Encoding

```
[31:24] = 0xA7
[23:15] = stall_res       (9 bits — block mask, same bits as STALLWAIT block mask B0–B8)
[14:4]  = target_value    (11 bits — low 10/11 bits of the target comparison value)
[3]     = target_sel      (1 bit — 0=compare phase, 1=compare num_msgs)
[1:0]   = wait_stream_sel (2 bits — selects one of 4 thread-private STREAM_ID_SYNC registers)
```

```c
#define TT_OP_STREAMWAIT(stall_res, target_value, target_sel, wait_stream_sel) \
    TT_OP(0xa7, (((stall_res) << 15) + ((target_value) << 4) + \
                  ((target_sel) << 3) + ((wait_stream_sel) << 0)))
```

### Condition Index

| ConditionIndex | Condition | Keep blocking if... |
|---|---|---|
| 0 (C0) | Phase | `NOC_STREAM_READ_REG(StreamIndex, STREAM_CURR_PHASE_REG_INDEX) < TargetValue` |
| 1 (C1) | Num msgs | `NOC_STREAM_READ_REG(StreamIndex, STREAM_NUM_MSGS_RECEIVED_REG_INDEX) < TargetValue` |

Where `StreamIndex = ThreadConfig[CurrentThread].STREAM_ID_SYNC_SEC[StreamSelect].BankSel`.

The full target value is formed by combining the low bits from the instruction with high bits from ThreadConfig:
- C0: `TargetValue = (ThreadConfig[t].STREAMWAIT_PHASE_HI_Val << 10) | TargetValueLo`
- C1: `TargetValue = (ThreadConfig[t].STREAMWAIT_NUM_MSGS_HI_Val << 10) | TargetValueLo`

### Block Mask

Same 9-bit block mask as STALLWAIT (B0–B8). If `BlockMask == 0`, it defaults to `1 << 6` (STALL_MATH). The block mask determines which instruction types are held until the condition is met.

### Functional Model

```python
def STREAMWAIT(block_mask, target_value_lo, condition_index, stream_select):
    # Compute full target value
    if condition_index == 0:
        target = (ThreadConfig[CurrentThread].STREAMWAIT_PHASE_HI_Val << 10) | target_value_lo
    else:
        target = (ThreadConfig[CurrentThread].STREAMWAIT_NUM_MSGS_HI_Val << 10) | target_value_lo

    # Latch the wait condition into the Wait Gate
    if block_mask == 0:
        block_mask = 1 << 6   # default: block Math instructions

    WaitGate[CurrentThread].latch(
        opcode=STREAMWAIT,
        condition_mask=(1 << condition_index),
        target_value=target,
        stream_select=stream_select,
        block_mask=block_mask
    )
    # The wait condition takes effect immediately — subsequent instructions
    # of blocked types will stall until the stream register >= target_value.
    # There is a 1-cycle lag: even if the condition is already met,
    # the instruction immediately after STREAMWAIT is subject to the block
    # for at least 1 cycle.
```

### Emulator Note

For a synchronous emulator that does not model stream/overlay data movement, STREAMWAIT conditions will typically be immediately satisfied (stream registers are at their final values). The emulator should still decode the instruction and apply the block mask logic for correctness. If the emulator does model stream progress, the Wait Gate must evaluate the condition each time a blocked instruction type is encountered.

### Performance

Executes on the Sync Unit. Stall bit: STALL_SYNC (B1).


## STREAMWRCFG — Copy Stream Register to Config (opcode 0xB7)

### Overview

Reads one 32-bit register from a NoC overlay stream and writes it to a thread-agnostic `Config` register. The stream is selected via one of the thread-private `STREAM_ID_SYNC_SEC` registers.

Used 260 times across LLK ELFs. Provides a direct path from overlay stream state to backend configuration, avoiding the roundabout path of LOADREG + WRCFG.

### Encoding

```
[31:24] = 0xB7
[22:21] = stream_id_sel   (2 bits — selects which STREAM_ID_SYNC register to use)
[20:11] = StreamRegAddr   (10 bits — stream register index to read)
[10:0]  = CfgReg          (11 bits — config register ADDR32 index)
```

```c
#define TT_OP_STREAMWRCFG(stream_id_sel, StreamRegAddr, CfgReg) \
    TT_OP(0xb7, (((stream_id_sel) << 21) + ((StreamRegAddr) << 11) + ((CfgReg) << 0)))
```

### Functional Model

```python
def STREAMWRCFG(stream_select, reg_index, cfg_index):
    stream_index = ThreadConfig[CurrentThread].STREAM_ID_SYNC_SEC[stream_select].BankSel
    state_id = ThreadConfig[CurrentThread].CFG_STATE_ID_StateID
    Config[state_id][cfg_index] = NOC_STREAM_READ_REG(stream_index, reg_index)
```

### Performance and Scheduling

- At least 5 cycles, fully pipelined (one per cycle assuming no contention)
- The issuing thread is **not** blocked
- **Hardware bug:** During the initial "prepare" phase (1+ cycles), if the same thread issues another Configuration Unit instruction (that is not STREAMWRCFG), that instruction will re-order and jump ahead of the pending STREAMWRCFG. After the prepare phase completes, subsequent Config instructions correctly wait.
- **Recommended:** Follow STREAMWRCFG with `STALLWAIT` before consuming the written config value. Alternatively, use `LOADREG` + `WRCFG` instead of STREAMWRCFG.

### Emulator Note

For a synchronous emulator, STREAMWRCFG reduces to a simple read from the stream register array and write to the config register. The hardware bug (instruction reordering during the prepare phase) is not relevant unless the emulator models cycle-accurate Configuration Unit pipeline stages. The emulator should still honor the STALLWAIT synchronization that software inserts.


## Encoding Quick Reference

| Instruction | Opcode | Backend | Stall Block | Key Fields |
|---|---|---|---|---|
| CFGSHIFTMASK | 0xB8 | Config Unit | B7 (STALL_CFG) | MaskMode, AluMode, MaskWidth, RotateAmt, ScratchIndex, CfgIndex |
| REG2FLOP | 0x48 | Scalar Unit (ThCon) | B0 (STALL_TDMA), B5 (STALL_THCON) | SizeSel, TargetSel, ByteOffset, ContextId, FlopIndex, RegIndex |
| STREAMWAIT | 0xA7 | Sync Unit | B1 (STALL_SYNC) | BlockMask, TargetValue, ConditionIndex, StreamSelect |
| STREAMWRCFG | 0xB7 | Config Unit | B7 (STALL_CFG) | StreamSelect, StreamRegAddr, CfgReg |


## Source References

| Source | Path |
|--------|------|
| CFGSHIFTMASK ISA (BH) | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/CFGSHIFTMASK.md` |
| STREAMWAIT ISA (BH) | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/STREAMWAIT.md` |
| STREAMWRCFG ISA (BH) | `tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/STREAMWRCFG.md` |
| STALLWAIT block mask | `emu-specs/stallwait-conditions.md` |
| Blackhole C macros | `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` |
| Blackhole assembly YAML | `tt-llk/tt_llk_blackhole/instructions/assembly.yaml` |
| Config register defines | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` |
| STREAMWAIT hi-value defs | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h` (lines 1299–1308) |
| REG2FLOP target constants | `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/tensix.h` (lines 388–390) |
| Python instruction encoders | `tt-exalens/ttexalens/hardware/blackhole/tensix_ops.py` |
