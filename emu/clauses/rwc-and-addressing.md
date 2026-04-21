# rwc-and-addressing

**Source:** [`rwc-and-addressing.md`](../specs/rwc-and-addressing.md) · **Emulator:** `blackhole-py/emu/tensix/rwc.py`

## RWCState initial values

### `RWC.INIT.ALL_ZERO`
§2.1 State

> RWCState initializes all counters (a, b, d, cr) to 0.

### `RWC.INIT.PER_THREAD`
§2.1 State

> Each of the three Tensix threads has its own independent RWC state. No cross-thread access.

## SETRWC

### `RWC.SETRWC.BITMASK_SELECTS_COUNTERS`
§2.3 SETRWC / BitMask

> BitMask in SETRWC selects which counters to set: bit0=SET_A, bit1=SET_B, bit2=SET_D, bit3=SET_F.

### `RWC.SETRWC.SET_A`
§2.3 SETRWC / BitMask

> BitMask&0x01: sets rwc.a to the provided rwc_a value.

### `RWC.SETRWC.SET_B`
§2.3 SETRWC / BitMask

> BitMask&0x02: sets rwc.b to the provided rwc_b value.

### `RWC.SETRWC.SET_D`
§2.3 SETRWC / BitMask

> BitMask&0x04: sets rwc.d to the provided rwc_d value.

### `RWC.SETRWC.SELECTIVE_UPDATE`
§2.3 SETRWC / selective

> Counters not selected by BitMask are unchanged.

### `RWC.SETRWC.RETURNS_CLEAR_AB`
_§2.3 SETRWC / clear_ab_

> SETRWC returns d.clear_ab_vld; the caller uses it to release SrcA/SrcB banks.

### `RWC.INCRWC.ADDS_DELTA`
§2.4 INCRWC

> INCRWC adds immediate deltas to each enabled counter: a, b, d, cr.

### `RWC.INCRWC.WRAP_4BIT`
§2.4 INCRWC / wrapping

> INCRWC counters a, b, d wrap modulo 0x10 (4-bit); cr wraps modulo 0x8 (3-bit).

### `RWC.ADDRMOD.8_DESCRIPTORS`
§3.1 Purpose

> AddrModState holds 8 descriptors (indices 0–7).

### `RWC.ADDRMOD.APPLY_INCREMENT`
§3.4 ApplyAddrMod

> apply() with no clear flags: adds incr to the selected counter.

### `RWC.ADDRMOD.APPLY_CLEAR`
§3.4 ApplyAddrMod

> apply() with srca_clr=True: resets rwc.a to 0 (clear takes priority over increment).

### `RWC.ADDRMOD.WRAP_4BIT`
§3.4 ApplyAddrMod

> AddrMod increments wrap modulo 0x10 for a/b/d counters; cr wraps 0x8.

### `RWC.ADDRMOD.OOB_INDEX_NOP`
§3.1 Purpose

> apply() with index outside [0,7] is a no-op.

### `RWC.ADC.SETADC_SETS_ONE_DIM`
§5.3 ADC Instructions / SETADC

> SETADC sets one dimension (X/Y/Z/W) of one channel for selected units.

### `RWC.ADC.SETADCXY_SETS_XY`
§5.3 ADC Instructions / SETADCXY

> SETADCXY sets X and Y of both channels simultaneously for selected units, controlled by BitMask.

### `RWC.ADC.SETADCZW_SETS_ZW`
§5.3 ADC Instructions / SETADCZW

> SETADCZW sets Z and W of both channels simultaneously for selected units.

### `RWC.ADC.INCADCZW_INCREMENTS_ZW`
§5.3 ADC Instructions / INCADCZW

> INCADCZW increments Z and W of both channels for selected units.

### `RWC.ADC.CNTSETMASK_SELECTS_UNITS`
§5.3 ADC Instructions / CntSetMask

> CntSetMask bit0=UNP0, bit1=UNP1, bit2=PAC. Multiple bits = multiple units updated.

### `RWC.ADC.MULTI_UNIT_UPDATE`
§5.3 ADC Instructions / CntSetMask=7

> CntSetMask=7 (all units) updates UNP0, UNP1, and Packers simultaneously.

### `RWC.ADC.SETADCXX_BOTH_CHANNELS`
§5.3 ADC Instructions / SETADCXX

> SETADCXX sets X of both channels from 10-bit start/end values.
