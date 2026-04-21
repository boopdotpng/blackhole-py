# Additional Scalar Unit Instructions

Four additional Scalar Unit (ThCon) instructions operate on the GPR file. They are used infrequently in LLK kernels (~400–450 occurrences across 747 Blackhole ELFs) and are not needed for matmul or add1, but they appear in STALLWAIT block masks and must be modeled for completeness.

All four share the same execution characteristics as ADDDMAREG/MULDMAREG: they execute on the Scalar Unit (ThCon), which is fully serialized. They stall under STALLWAIT block bit B5 (`STALL_THCON`).


## SHIFTDMAREG — Bitwise Shift GPR (opcode 0x5C)

Performs an unsigned bitwise shift (left or right) of one GPR by another GPR, or by a 5-bit immediate.

**Encoding:**
```
[31:24] = 0x5C
[23]    = OpBisConst  (0 = reg-reg, 1 = reg-immediate)
[20:18] = Mode        (3 bits — shift direction)
[17:12] = ResultRegIndex  (6 bits)
[11:6]  = OpBRegIndex     (6 bits — GPR index or 5-bit shift amount if OpBisConst=1)
[5:0]   = OpARegIndex     (6 bits — source GPR)
```

```c
#define TT_OP_SHIFTDMAREG(OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex) \
    TT_OP(0x5c, (((OpBisConst) << 23) + ((OpSel) << 18) + ((ResultRegIndex) << 12) \
               + ((OpBRegIndex) << 6) + ((OpARegIndex) << 0)))
```

**Modes:**
| Mode | Name | Operation |
|------|------|-----------|
| 0 | `SHIFTDMAREG_MODE_LEFT` | `Result = Left << Right` |
| 1 | `SHIFTDMAREG_MODE_RIGHT` | `Result = Left >> Right` (unsigned) |

**Functional model:**
```python
def SHIFTDMAREG(OpBisConst, mode, result_reg, right_reg_or_imm, left_reg):
    left_val = GPRs[CurrentThread][left_reg]
    if OpBisConst:
        right_val = right_reg_or_imm & 0x1F    # 5-bit immediate
    else:
        right_val = GPRs[CurrentThread][right_reg_or_imm] & 0x1F

    if mode == 0:    # LEFT
        result = (left_val << right_val) & 0xFFFFFFFF
    elif mode == 1:  # RIGHT
        result = left_val >> right_val
    else:
        raise UndefinedBehaviour()

    GPRs[CurrentThread][result_reg] = result
```

**Performance:** 3 cycles (immediate variant, or both regs in same aligned group of 4 GPRs), 4 cycles otherwise.


## BITWOPDMAREG — Bitwise AND/OR/XOR on GPR (opcode 0x5B)

Performs a bitwise AND, OR, or XOR between two GPRs, or between a GPR and a 6-bit immediate.

**Encoding:**
```
[31:24] = 0x5B
[23]    = OpBisConst  (0 = reg-reg, 1 = reg-immediate)
[20:18] = OpSel       (3 bits — operation select)
[17:12] = ResultRegIndex  (6 bits)
[11:6]  = OpBRegIndex     (6 bits — GPR index or 6-bit constant)
[5:0]   = OpARegIndex     (6 bits — source GPR)
```

```c
#define TT_OP_BITWOPDMAREG(OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex) \
    TT_OP(0x5b, (((OpBisConst) << 23) + ((OpSel) << 18) + ((ResultRegIndex) << 12) \
               + ((OpBRegIndex) << 6) + ((OpARegIndex) << 0)))
```

**Modes:**
| OpSel | Name | Operation |
|-------|------|-----------|
| 0 | `BITWOPDMAREG_MODE_AND` | `Result = A & B` |
| 1 | `BITWOPDMAREG_MODE_OR` | `Result = A \| B` |
| 2 | `BITWOPDMAREG_MODE_XOR` | `Result = A ^ B` |

**Functional model:**
```python
def BITWOPDMAREG(OpBisConst, mode, result_reg, right_reg_or_imm, left_reg):
    left_val = GPRs[CurrentThread][left_reg]
    if OpBisConst:
        right_val = right_reg_or_imm & 0x3F    # 6-bit immediate
    else:
        right_val = GPRs[CurrentThread][right_reg_or_imm]

    if mode == 0:    result = left_val & right_val
    elif mode == 1:  result = left_val | right_val
    elif mode == 2:  result = left_val ^ right_val
    else:            raise UndefinedBehaviour()

    GPRs[CurrentThread][result_reg] = result
```

**Performance:** 3 cycles (immediate variant, or both regs in same aligned group of 4 GPRs), 4 cycles otherwise.


## CMPDMAREG — Compare GPRs (opcode 0x5D)

Unsigned comparison (GT, LT, EQ) between two GPRs, or between a GPR and a 6-bit immediate. Result is 0 or 1.

**Encoding:**
```
[31:24] = 0x5D
[23]    = OpBisConst  (0 = reg-reg, 1 = reg-immediate)
[20:18] = OpSel       (3 bits — comparison mode)
[17:12] = ResultRegIndex  (6 bits)
[11:6]  = OpBRegIndex     (6 bits — GPR index or 6-bit constant)
[5:0]   = OpARegIndex     (6 bits — source GPR)
```

```c
#define TT_OP_CMPDMAREG(OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex) \
    TT_OP(0x5d, (((OpBisConst) << 23) + ((OpSel) << 18) + ((ResultRegIndex) << 12) \
               + ((OpBRegIndex) << 6) + ((OpARegIndex) << 0)))
```

**Modes:**
| OpSel | Name | Operation |
|-------|------|-----------|
| 0 | `CMPDMAREG_MODE_GT` | `Result = (A > B) ? 1 : 0` |
| 1 | `CMPDMAREG_MODE_LT` | `Result = (A < B) ? 1 : 0` |
| 2 | `CMPDMAREG_MODE_EQ` | `Result = (A == B) ? 1 : 0` |

**Functional model:**
```python
def CMPDMAREG(OpBisConst, mode, result_reg, right_reg_or_imm, left_reg):
    left_val = GPRs[CurrentThread][left_reg]
    if OpBisConst:
        right_val = right_reg_or_imm & 0x3F    # 6-bit unsigned immediate
    else:
        right_val = GPRs[CurrentThread][right_reg_or_imm]

    if mode == 0:    result = 1 if left_val > right_val else 0
    elif mode == 1:  result = 1 if left_val < right_val else 0
    elif mode == 2:  result = 1 if left_val == right_val else 0
    else:            raise UndefinedBehaviour()

    GPRs[CurrentThread][result_reg] = result
```

All comparisons are **unsigned**. Performance: same as SHIFTDMAREG/BITWOPDMAREG.


## FLUSHDMA — Occupy Scalar Unit Until Conditions Met (opcode 0x46)

Stalls the issuing thread **and all other threads** trying to use the Scalar Unit until selected conditions are met. In almost every case, STALLWAIT should be preferred — it waits without blocking other threads' Scalar Unit access.

**Encoding:**
```
[31:24] = 0x46
[3:0]   = ConditionMask  (4 bits — conditions C0–C3)
```

```c
#define TT_OP_FLUSHDMA(FlushSpec) TT_OP(0x46, (((FlushSpec) << 0)))
```

**Condition mask:**

| Bit | Condition | Keep waiting if... |
|-----|-----------|-------------------|
| C0 | Scalar Unit memory | The Scalar Unit has outstanding memory requests for the current thread |
| C1 | Unpacker 0 | The current thread has an instruction in any stage of Unpacker 0's pipeline |
| C2 | Unpacker 1 | The current thread has an instruction in any stage of Unpacker 1's pipeline |
| C3 | Packer 0 | The current thread has an instruction in any stage of Packer 0's pipeline |

If `ConditionMask == 0`, it defaults to `0xF` (all conditions). The instruction waits until **all** selected conditions are simultaneously met (i.e., none of the "keep waiting" conditions are true). These condition bits coincide exactly with the low four bits of STALLWAIT's condition mask.

**Functional model:**
```python
def FLUSHDMA(condition_mask):
    if condition_mask == 0:
        condition_mask = 0xF

    # Block the Scalar Unit for all threads until conditions are met
    while any_selected_condition_indicates_busy(condition_mask, CurrentThread):
        wait()  # stalls this thread AND any other thread trying to use ThCon
```

**Performance:** At least 2 cycles, plus however long the wait takes.

**Emulator note:** For a synchronous emulator, FLUSHDMA is functionally equivalent to STALLWAIT with block mask `0x20` (STALL_THCON) and the same condition bits. The distinction (blocking other threads' ThCon access) only matters for cycle-accurate timing.


## AutoTTSync Classification

All four instructions share the same STALLWAIT behavior:

| Class | Instructions | Behavior |
|-------|-------------|----------|
| 0 | ADDDMAREG, SUBDMAREG, MULDMAREG, **BITWOPDMAREG**, **SHIFTDMAREG**, **CMPDMAREG**, SETDMAREG | Read and write Tensix GPRs |
| 7 | **FLUSHDMA** | Write TDMA-RISC state (synchronization barrier) |


## Encoding Quick Reference

| Instruction | Opcode | Field Layout |
|---|---|---|
| BITWOPDMAREG | 0x5B | `[23]` OpBisConst, `[20:18]` OpSel, `[17:12]` Result, `[11:6]` OpB, `[5:0]` OpA |
| SHIFTDMAREG | 0x5C | (same — but immediate is 5-bit, not 6-bit) |
| CMPDMAREG | 0x5D | (same as BITWOPDMAREG) |
| FLUSHDMA | 0x46 | `[3:0]` ConditionMask |


## Source References

| Source | Path |
|--------|------|
| ISA functional models | `tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/{SHIFTDMAREG,BITWOPDMAREG,CMPDMAREG,FLUSHDMA}.md` |
| Blackhole C macros | `tt-llk/tt_llk_blackhole/common/inc/ckernel_ops.h` |
| Blackhole assembly YAML | `tt-llk/tt_llk_blackhole/instructions/assembly.yaml` |
| Python instruction encoders | `tt-exalens/ttexalens/hardware/blackhole/tensix_ops.py` |
| Instruction frequency data | `boop-docs/llk-sfpi/instruction-frequency-report.md` |
| AutoTTSync classes | `tt-isa-documentation/BlackholeA0/TensixTile/BabyRISCV/AutoTTSync.md` |
