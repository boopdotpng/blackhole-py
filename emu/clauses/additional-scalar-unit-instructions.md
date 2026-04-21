# additional-scalar-unit-instructions

**Source:** [`additional-scalar-unit-instructions.md`](../specs/additional-scalar-unit-instructions.md)

## SHIFTDMAREG

### `ASUI.SHIFTDMAREG.LEFT`
§SHIFTDMAREG / Mode=0

> Mode=0 (LEFT): Result = (Left << Right) & 0xFFFFFFFF.

### `ASUI.SHIFTDMAREG.RIGHT`
§SHIFTDMAREG / Mode=1

> Mode=1 (RIGHT): Result = Left >> Right (unsigned logical right shift).

### `ASUI.SHIFTDMAREG.IMMEDIATE_5BIT`
§SHIFTDMAREG Functional model

> OpBisConst=1: shift amount is a 5-bit immediate (right_reg_or_imm & 0x1F).

### `ASUI.SHIFTDMAREG.REG_5BIT_MASK`
§SHIFTDMAREG Functional model

> OpBisConst=0: shift amount is GPR value masked to 5 bits (& 0x1F).

### `ASUI.BITWOPDMAREG.AND`
§BITWOPDMAREG / OpSel=0

> OpSel=0 (AND): Result = A & B.

### `ASUI.BITWOPDMAREG.OR`
§BITWOPDMAREG / OpSel=1

> OpSel=1 (OR): Result = A | B.

### `ASUI.BITWOPDMAREG.XOR`
§BITWOPDMAREG / OpSel=2

> OpSel=2 (XOR): Result = A ^ B.

### `ASUI.BITWOPDMAREG.IMMEDIATE_6BIT`
§BITWOPDMAREG Functional model

> OpBisConst=1: B is a 6-bit unsigned immediate (right_reg_or_imm & 0x3F).

### `ASUI.CMPDMAREG.GT`
§CMPDMAREG / OpSel=0

> OpSel=0 (GT): Result = 1 if A > B else 0 (unsigned comparison).

### `ASUI.CMPDMAREG.LT`
§CMPDMAREG / OpSel=1

> OpSel=1 (LT): Result = 1 if A < B else 0 (unsigned comparison).

### `ASUI.CMPDMAREG.EQ`
§CMPDMAREG / OpSel=2

> OpSel=2 (EQ): Result = 1 if A == B else 0.

### `ASUI.CMPDMAREG.UNSIGNED`
§CMPDMAREG

> All comparisons are unsigned (32-bit unsigned integer comparison).

### `ASUI.CMPDMAREG.IMMEDIATE_6BIT`
§CMPDMAREG Functional model

> OpBisConst=1: B is a 6-bit unsigned immediate.

### `ASUI.FLUSHDMA.CONDITION_MASK`
§FLUSHDMA Functional model

> Blocks until all selected conditions are simultaneously met. ConditionMask=0 defaults to 0xF (all conditions).

### `ASUI.FLUSHDMA.BLOCKS_ALL_THREADS`
§FLUSHDMA Functional model

> FLUSHDMA blocks the Scalar Unit for ALL threads while waiting (not just the issuing thread).

