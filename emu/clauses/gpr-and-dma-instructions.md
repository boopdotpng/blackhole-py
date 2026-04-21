# gpr-and-dma-instructions

**Source:** [`gpr-and-dma-instructions.md`](../specs/gpr-and-dma-instructions.md)

## GPR file layout

### `GPR.LAYOUT.64_PER_THREAD`
§GPR File Layout

> 192 GPRs total: 64 per thread (T0/T1/T2), each 32-bit.

### `GPR.LAYOUT.HALF_REG_ADDRESSING`
§GPR File Layout / Sub-Word Addressing

> SETDMAREG addresses GPRs in 16-bit half-register units: index 2*n = low half, 2*n+1 = high half.

### `GPR.LAYOUT.THREAD_ISOLATION`
§GPR File Layout / Access Rules

> Each coprocessor thread (T0/T1/T2) can only access its own 64 GPRs.

### `GPR.SETDMAREG.IMMEDIATE_WRITE_16B`
§SETDMAREG Functional model (immediate mode)

> SetSignalsMode=0: writes 16-bit immediate to HalfReg[RegIndex16b], leaving the other half unchanged.

### `GPR.SETDMAREG.IMM16_SPANS_BOTH_FIELDS`
§SETDMAREG Encoding

> The 16-bit immediate spans [Payload_SigSelSize:2][Payload_SigSel:14]; imm16 = (SigSelSize << 14) | SigSel.

### `GPR.ADDDMAREG.REG_REG`
§ADDDMAREG Functional model

> OpBisConst=0: GPRs[ResultReg] = GPRs[LeftReg] + GPRs[RightReg], 32-bit wrapping.

### `GPR.ADDDMAREG.REG_CONST`
§ADDDMAREG Functional model

> OpBisConst=1: GPRs[ResultReg] = GPRs[LeftReg] + RightImm6 (6-bit unsigned immediate).

### `GPR.ADDDMAREG.OVERFLOW_WRAPS`
§ADDDMAREG Functional model

> Result is 32-bit unsigned wrapping on overflow.

### `GPR.MULDMAREG.16BIT_TRUNCATION`
§MULDMAREG

> Inputs are truncated to 16 bits: GPRs[ResultReg] = (LeftVal & 0xFFFF) * (RightVal & 0xFFFF).

### `GPR.MULDMAREG.REG_CONST`
§MULDMAREG

> OpBisConst=1: RightVal is a 6-bit unsigned immediate (not truncated).

### `GPR.WRCFG.32BIT`
§WRCFG Functional model

> wr128b=0: Config[StateID][CfgIndex] = GPRs[CurrentThread][InputReg].

### `GPR.WRCFG.128BIT`
§WRCFG Functional model

> wr128b=1: copies 4 consecutive GPRs (InputReg & ~3) into 4 consecutive config words (CfgIndex & ~3).

### `GPR.WRCFG.STATE_BANK`
§WRCFG Functional model

> StateID is taken from ThreadConfig[CurrentThread].CFG_STATE_ID_StateID (bit 0 of word 42).

### `GPR.RDCFG.32BIT_READ`
§RDCFG Functional model

> GPRs[CurrentThread][ResultReg] = Config[StateID][CfgIndex].

### `GPR.RDCFG.CANNOT_READ_THREADCFG`
§RDCFG

> RDCFG cannot read ThreadConfig; only Config (thread-agnostic) is readable.

### `GPR.SETC16.WRITE_THREADCFG`
§SETC16 Functional model

> ThreadConfig[CurrentThread][CfgIndex].Value = NewValue (16-bit immediate).

### `GPR.SETC16.ONLY_WRITER`
§SETC16 Overview

> SETC16 is the only Tensix instruction that can write ThreadConfig.

### `GPR.RMWCIB.BYTE0_RMW`
§RMWCIB0/1/2/3 Functional model

> RMWCIB0: *ByteAddr = (NewValue & Mask) | (OldValue & ~Mask) on byte 0 of Config[0][CfgRegAddr].

### `GPR.RMWCIB.BYTE1_RMW`
§RMWCIB0/1/2/3 Functional model

> RMWCIB1: modifies byte 1 of the 32-bit config word.

### `GPR.RMWCIB.BYTE2_RMW`
§RMWCIB0/1/2/3 Functional model

> RMWCIB2: modifies byte 2 of the 32-bit config word.

### `GPR.RMWCIB.BYTE3_RMW`
§RMWCIB0/1/2/3 Functional model

> RMWCIB3: modifies byte 3 of the 32-bit config word.

### `GPR.RMWCIB.USES_STATE0`
§RMWCIB0/1/2/3 Functional model

> RMWCIB always targets Config bank 0, regardless of ThreadConfig.CFG_STATE_ID.
