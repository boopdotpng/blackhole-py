# sfploadmacro-and-sfptransp

**Source:** [`sfploadmacro-and-sfptransp.md`](../specs/sfploadmacro-and-sfptransp.md) · **Emulator:** `blackhole-py/emu/tensix/sfpu.py`

## ========================================================== SFPLOADMACRO

### `SFPLM.LOAD_PART`
§SFPLOADMACRO / Functional Model step 1

> SFPLOADMACRO first executes an SFPLOAD: Dst → LReg[vd].

### `SFPLM.LREG16_WRITABLE_VIA_MACRO`
§SFPLOADMACRO / LReg[16]

> LReg[16] is writable only by instructions scheduled via SFPLOADMACRO.

### `SFPLM.LOADMACROCONFIG_IGNORED`
§SFPLOADMACRO / LoadMacroConfig State

> LoadMacroConfig state (programmed via SFPCONFIG VD=0..8) controls per-lane instruction templates, sequence bytes, and Misc fields used for scheduling.

### `SFPLM.SCHEDULING_CONSTRAINT_3_INSN`
§SFPLOADMACRO / Scheduling Constraints §1

> At least 3 unrelated Tensix instructions must execute between FPU write to Dst and SFPLOADMACRO reading that Dst region.

### `SFPLM.SCHEDULED_NO_AUTOSTALL`
§SFPLOADMACRO / Scheduling Constraints §2

> None of the SFPU auto-stalling applies to instructions executed as part of an SFPLOADMACRO sequence; programmer must ensure correct ordering via delays.

## ========================================================== SFPTRANSP

### `SFPTR.TWO_GROUPS`
§SFPTRANSP / Overview

> SFPTRANSP operates on two independent groups: LReg[0..3] and LReg[4..7]. Within each group it performs a 4×4 transpose across the 8 columns.

### `SFPTR.SWAP_RULE`
§SFPTRANSP / Functional Model

> For column c (0–7): swaps LReg[base+i][j*8+c] with LReg[base+j][i*8+c] for all i > j (in-place 4×4 transpose within the column).

### `SFPTR.LANE_ENABLED_GUARD`
§SFPTRANSP / Functional Model

> Each swap is guarded: LReg[base+i][j*8+c] is overwritten only if LaneEnabled[j*8+c] is true; LReg[base+j][i*8+c] only if LaneEnabled[i*8+c].

### `SFPTR.DOUBLE_TRANSPOSE_IDENTITY`
§SFPTRANSP / Usage Pattern

> Applying SFPTRANSP twice (with no intervening modifications) restores the original LReg state (transpose is its own inverse).

