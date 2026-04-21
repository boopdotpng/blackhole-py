# config-sync-instructions

**Source:** [`config-sync-instructions.md`](../specs/config-sync-instructions.md)

## CFGSHIFTMASK

### `CSI.CFGSHIFTMASK.MASK_WIDTH`
§CFGSHIFTMASK Functional Model

> mask_val = (2 << mask_width) - 1 (MaskWidth+1 bits of ones).

### `CSI.CFGSHIFTMASK.ROTATE`
§CFGSHIFTMASK Functional Model

> scratch_val = rotr32(scratch_val & mask_val, rotate_amt) before ALU.

### `CSI.CFGSHIFTMASK.ALU_OR`
§CFGSHIFTMASK ALU Modes / AluMode=0

> AluMode=0: CfgValue |= ScratchValue.

### `CSI.CFGSHIFTMASK.ALU_ADD`
§CFGSHIFTMASK ALU Modes / AluMode=3

> AluMode=3: CfgValue += ScratchValue (32-bit wrapping).

### `CSI.CFGSHIFTMASK.SCRATCH_INDEX_3_USES_THREAD`
§CFGSHIFTMASK Functional Model

> ScratchIndex=3 → use SCRATCH_SEC[CurrentThread].val rather than a fixed slot.

### `CSI.CFGSHIFTMASK.MASK_MODE_0_CLEARS`
§CFGSHIFTMASK Functional Model

> MaskMode=0: cfg_val &= ~rotr32(mask_val, rotate_amt) before applying ALU op.

### `CSI.REG2FLOP.32BIT_WRITE`
§REG2FLOP Functional Model

> SizeSel=1..3: ThConCfgBase[ThConCfgIndex] = GPRs[CurrentThread][InputReg].

### `CSI.REG2FLOP.128BIT_WRITE`
§REG2FLOP SizeSel Values / SizeSel=0

> SizeSel=0: copies 4 consecutive GPRs (InputReg & ~3) into 4 consecutive THCON config words (ThConCfgIndex & ~3).

### `CSI.REG2FLOP.THCON_ONLY`
§REG2FLOP Overview

> REG2FLOP can only address THCON_* configuration fields; indices >= GLOBAL_CFGREG_BASE_ADDR32 - THCON_CFGREG_BASE_ADDR32 are undefined behaviour.

### `CSI.STREAMWAIT.CONDITION_PHASE`
§STREAMWAIT Condition Index / C0

> C0: block while STREAM_CURR_PHASE_REG < TargetValue.

### `CSI.STREAMWAIT.CONDITION_NUM_MSGS`
§STREAMWAIT Condition Index / C1

> C1: block while STREAM_NUM_MSGS_RECEIVED_REG < TargetValue.

### `CSI.STREAMWAIT.BLOCK_MASK_ZERO_DEFAULT`
§STREAMWAIT Block Mask

> BlockMask=0 defaults to 1<<6 (STALL_MATH).

### `CSI.STREAMWAIT.TARGET_VALUE_HI_FROM_THREADCFG`
§STREAMWAIT Functional Model

> Full TargetValue = (ThreadConfig.STREAMWAIT_PHASE_HI_Val << 10) | TargetValueLo.

### `CSI.STREAMWRCFG.COPIES_STREAM_TO_CONFIG`
§STREAMWRCFG Functional Model

> Config[state_id][cfg_index] = NOC_STREAM_READ_REG(stream_index, reg_index).

### `CSI.STREAMWRCFG.STREAM_SEL_FROM_THREADCFG`
§STREAMWRCFG Functional Model

> stream_index = ThreadConfig[CurrentThread].STREAM_ID_SYNC_SEC[stream_select].BankSel.

### `CSI.STREAMWRCFG.HW_BUG_REORDER`
§STREAMWRCFG Performance and Scheduling

> Hardware bug: during initial prepare phase, another Config Unit instruction from the same thread can jump ahead of the pending STREAMWRCFG.
