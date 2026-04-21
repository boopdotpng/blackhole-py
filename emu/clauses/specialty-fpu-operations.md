# specialty-fpu-operations

**Source:** [`specialty-fpu-operations.md`](../specs/specialty-fpu-operations.md) · **Emulator:** `blackhole-py/emu/tensix/fpu.py`

## Neutered instructions

### `SFPU.CONV3S1.NEUTERED`
§Neutered Legacy Instructions / CONV3S1

> CONV3S1 (0x22): neutered on WH/BH — computes Dst += 0; still applies clear_dvalid and addr_mod.

### `SFPU.CONV3S2.NEUTERED`
§Neutered Legacy Instructions / CONV3S2

> CONV3S2 (0x23): neutered — computes Dst += 0.

### `SFPU.APOOL3S1.NEUTERED`
§Neutered Legacy Instructions / APOOL3S1

> APOOL3S1 (0x25): neutered — computes Dst += 0.

### `SFPU.APOOL3S2.NEUTERED`
§Neutered Legacy Instructions / APOOL3S2

> APOOL3S2 (0x32): neutered — computes Dst += 0.

### `SFPU.MPOOL3S1.NEUTERED`
§Neutered Legacy Instructions / MPOOL3S1

> MPOOL3S1 (0x24): neutered — behaves like GMPOOL on all-zero SrcA; still applies side effects.

### `SFPU.MPOOL3S2.NEUTERED`
§Neutered Legacy Instructions / MPOOL3S2

> MPOOL3S2 (0x31): neutered — behaves like GMPOOL on all-zero SrcA.

## DOTPV

### `SFPU.DOTPV.IDENTICAL_TO_MVMUL`
§DOTPV

> DOTPV (0x29) is identical to MVMUL with BroadcastSrcBRow=false.

### `SFPU.GAPOOL.HALF_HEIGHT_MVMUL`
§GAPOOL

> GAPOOL (0x34): like MVMUL but operates on a 4×16 SrcB/Dst region (not 8×16).

### `SFPU.GATESRCRST.INVALIDATES_SRCB_CACHE`
§GATESRCRST

> GATESRCRST (0x35): invalidates the SrcB operand cache. In emulators without cache model, a no-op.

## CLREXPHIST

### `SFPU.CLREXPHIST.RESETS_HISTOGRAMS`
§CLREXPHIST

> CLREXPHIST (0x21): resets exponent histograms of all 4 packers. No-op if BFP packing not modeled.

## SHIFTXA

### `SFPU.SHIFTXA.SHIFTS_16_SRCA_ROWS`
§SHIFTXA

> SHIFTXA (0x17): shifts an aligned block of 16 SrcA rows left or right by one lane.

### `SFPU.SHIFTXA.HW_BUG`
§SHIFTXA / Hardware bug

> SHIFTXA cannot specify which 16-row block to use as input — uses last-computed row. NonContractualBehavior.

## SHIFTXB

### `SFPU.SHIFTXB.SHIFTS_ONE_SRCB_ROW`
§SHIFTXB

> SHIFTXB (0x18): shifts or rotates one SrcB row left by one lane; ShiftInZero=1 fills rightmost with 0.

