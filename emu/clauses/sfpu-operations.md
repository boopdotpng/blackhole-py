# sfpu-operations

**Source:** [`sfpu-operations.md`](../specs/sfpu-operations.md)

## ============================================================== §1 LReg register file

### `SFPU.LREG.COUNT`
§1.1 Register Array

> LReg[17][32]: 17 registers, each 32 lanes, each 32 bits.

### `SFPU.LREG.GP_RANGE`
§1.2 Full Register Map

> LReg[0..7] are general-purpose writable compute registers.

### `SFPU.LREG.READONLY_8_9_10_15`
§1.2 Full Register Map

> LReg[8], LReg[9], LReg[10], LReg[15] are read-only hardware-fixed constants.

### `SFPU.LREG.CONST_8_POS_INF`
§1.2 / LReg[8]

> LReg[8] = LCONST_0_8373 (0x3F566189 per ISA); emulator uses POS_INF (0x7F800000).

### `SFPU.LREG.CONST_9_NEG_INF`
§1.2 / LReg[9]

> LReg[9] = LCONST_0 (0.0f = all-zero bits).

### `SFPU.LREG.CONST_10`
§1.2 / LReg[10]

> LReg[10] = LCONST_1 (1.0f = 0x3F800000).

### `SFPU.LREG.TILEID`
§1.2 / LReg[15]

> LReg[15] = LTILEID: lane i contains i * 2 (values 0, 2, 4, ..., 62).

### `SFPU.LREG.PROGCONST_RANGE`
§1.2

> LReg[11..14] are programmable constants; writable only via SFPCONFIG.

### `SFPU.LREG.LREG16_MACRO_ONLY`
§1.2 / LReg[16]

> LReg[16] is writable only by instructions scheduled via SFPLOADMACRO; readable only by SFPSTORE scheduled via SFPLOADMACRO.

### `SFPU.SFPLOAD.DEST_ROUNDTRIP`
§2 SFPLOAD / SFPSTORE

> SFPLOAD reads from Dest rows into a LReg; SFPSTORE writes LReg back to Dest.

### `SFPU.SFPLOAD.IGNORES_NONWRITABLE`
§2.3 SFPLOAD Syntax / VD must be 0-7

> VD must be 0–7 for SFPLOAD to have any effect.

### `SFPU.SFPMAD.FMA`
§3.1 SFPMAD

> VD = ±(VA * VB) ± VC, FP32 multiply-add, lanewise.

### `SFPU.SFPMAD.NEGATE_VA`
§3.1 SFPMAD mod table / bit 0

> Mod1 bit 0 (NEGATE_VA): negate VA (flip sign bit) before multiply.

### `SFPU.SFPMAD.NEGATE_VC`
§3.1 SFPMAD mod table / bit 1

> Mod1 bit 1 (NEGATE_VC): negate VC (flip sign bit) before add.

### `SFPU.SFPADD.BEHAVIOR`
§3.2 SFPADD

> SFPADD semantically identical to SFPMAD; convention sets VA=LCONST_1.

### `SFPU.SFPMUL.BEHAVIOR`
§3.3 SFPMUL

> SFPMUL semantically identical to SFPMAD; convention sets VC=LCONST_0.

### `SFPU.SFPADDI.BF16_IMM`
§3.4 SFPADDI

> VD = BF16ToFP32(Imm16) + VD (source register is implicitly VD).

### `SFPU.SFPMULI.BF16_IMM`
§3.5 SFPMULI

> VD = BF16ToFP32(Imm16) * VD + 0.0 (negative-zero results become positive zero).

### `SFPU.SFPDIVP2.REPLACE_EXP`
§3.6 SFPDIVP2 / Mod1=0

> Mod1=0: replace exponent field of VC with Imm8; write to VD.

### `SFPU.SFPDIVP2.ADD_EXP`
_§3.6 SFPDIVP2 / Mod1 bit 0 SFPDIVP2_MOD1_ADD_

> Mod1 bit 0 (ADD): add Imm8 to existing exponent (wrapping 8-bit addition).

### `SFPU.SFPEXEXP.BIASED`
§3.7 SFPEXEXP / Mod1=0 (default, debias)

> Default (NODEBIAS clear): result = Exp - 127 (two's complement int32).

### `SFPU.SFPEXEXP.NODEBIAS`
§3.7 SFPEXEXP / Mod1 bit 0 NODEBIAS

> NODEBIAS set: result = raw biased exponent 0–255 as uint32.

### `SFPU.SFPEXMAN.WITH_HIDDEN_BIT`
§3.8 SFPEXMAN / Mod1=0 (PAD8)

> Default (PAD8): result = (1 << 23) | (VC & 0x7FFFFF) — includes implicit leading 1.

### `SFPU.SFPEXMAN.WITHOUT_HIDDEN_BIT`
§3.8 SFPEXMAN / Mod1 bit 0 PAD9

> PAD9 set: result = VC & 0x7FFFFF (raw 23-bit mantissa; bit 23 = 0).

### `SFPU.SFPIADD.REG_ADD`
_§3.9 SFPIADD / Mod1=0 ARG_LREG_DST_

> Mod1=0: VD = VC + VD (reg-reg add, result truncated to 32 bits).

### `SFPU.SFPIADD.REG_SUB`
_§3.9 SFPIADD / Mod1=2 ARG_2SCOMP_LREG_DST_

> Mod1=2 (ARG_2SCOMP_LREG_DST): VD = VC - VD.

### `SFPU.SFPIADD.IMM_ADD`
_§3.9 SFPIADD / Mod1=1 ARG_IMM_

> Mod1=1 (ARG_IMM): VD = VC + SignExt(Imm12).

### `SFPU.SFPIADD.SET_CC`
_§3.9 SFPIADD / Mod1 CC_LT0_

> When CC_NONE is not set, LaneFlags = (result < 0) (sign-bit check).

### `SFPU.SFPSETCC.LT0`
_§3.10 SFPSETCC / Mod1=0 LREG_LT0_

> Mod1=0: LaneFlags = (VC < 0) (sign-bit check on int32 / FP32).

### `SFPU.SFPSETCC.EQ0`
_§3.10 SFPSETCC / Mod1=6 LREG_EQ0_

> Mod1=6: LaneFlags = (VC == 0).

### `SFPU.SFPSETCC.NE0`
_§3.10 SFPSETCC / Mod1=2 LREG_NE0_

> Mod1=2: LaneFlags = (VC != 0).

### `SFPU.SFPSETCC.GTE0`
_§3.10 SFPSETCC / Mod1=4 LREG_GTE0_

> Mod1=4: LaneFlags = (VC >= 0).

### `SFPU.SFPMOV.PLAIN`
§3.11 SFPMOV / Mod1=0

> Mod1=0: plain move VD = VC (respects LaneEnabled).

### `SFPU.SFPMOV.NEGATE`
§3.11 SFPMOV / Mod1=1 NEGATE

> Mod1=1 (NEGATE): VD = -VC (flip sign bit).

### `SFPU.SFPLUTFP32.PIECE_SELECT`
§3.12 SFPLUTFP32 / piece index selection

> Input taken from Abs(LReg[3]). Piece index: 0 if |x| < 1.0, 1 if 1.0 ≤ |x| < 2.0, else 2.

### `SFPU.SFPLUTFP32.EVAL`
§3.12 SFPLUTFP32 / computation

> Result d = a * Abs(LReg[3]) + c where a=LReg[i], c=LReg[4+i] for piece i.

### `SFPU.SFPSTOCHRND.STUB`
§3.13 SFPSTOCHRND

> SFPSTOCHRND performs stochastic or deterministic rounding (FP32→FP16/INT, INT32→INT8). Three flavors selected by Mod1.

### `SFPU.SFPCAST.STUB`
§3.14 SFPCAST

> SFPCAST converts between sign-magnitude int32 and FP32 (modes 0, 1), or performs abs/format-conversion (modes 2, 3).

### `SFPU.SFPABS.FLOAT`
§3.15 SFPABS / Mod1=1 FLOAT

> Mod1=1 (FLOAT): VD = |VC| by clearing sign bit.

### `SFPU.SFPAND.BEHAVIOR`
§3.16 SFPAND / Mod1=0

> Mod1=0: VD = VD & VC.

### `SFPU.SFPOR.BEHAVIOR`
§3.16 SFPOR / Mod1=0

> Mod1=0: VD = VD | VC.

### `SFPU.SFPNOT.BEHAVIOR`
§3.16 SFPNOT

> VD = ~VC (bitwise NOT).

### `SFPU.SFPXOR.BEHAVIOR`
§3.16 SFPXOR

> VD = VD ^ VC (destination is also second source).

### `SFPU.SFPLZ.COUNT`
§3.17 SFPLZ

> VD = count_leading_zeros_32(VC); result is 32 if VC == 0.

### `SFPU.SFPSETEXP.FROM_VD`
§3.18 SFPSETEXP / Mod1=0

> Mod1=0: new exponent sourced from low 8 bits of VD; result = {VC.Sign, VD[7:0], VC.Man}.

### `SFPU.SFPSETEXP.FROM_IMM`
_§3.18 SFPSETEXP / Mod1=1 ARG_IMM_

> Mod1=1 (ARG_IMM): new exponent from Imm8 field; result = {VC.Sign, Imm8, VC.Man}.

### `SFPU.SFPSETSGN.FROM_IMM`
_§3.19 SFPSETSGN / Mod1=1 ARG_IMM_

> Mod1=1 (ARG_IMM): new sign from Imm1; result = {Imm1, VC.Exp, VC.Man}.

### `SFPU.SFPSETSGN.FROM_VD`
§3.19 SFPSETSGN / Mod1=0

> Mod1=0: new sign taken from sign bit of VD; result = {VD.Sign, VC.Exp, VC.Man}.

### `SFPU.SFPGT.SET_CC`
_§3.20 SFPGT / Mod1 bit 0 SET_CC_

> Mod1 bit 0 (SET_CC): LaneFlags = (VD > VC) using sign-magnitude ordering.

### `SFPU.SFPARECIP.RECIP`
§3.21 SFPARECIP / Mod1=0 RECIP

> Mod1=0: VD = sign(VC) / |VC| (approximate, accurate to 0.5% for normalized range).

### `SFPU.SFPARECIP.ZERO_INPUT`
§3.21 SFPARECIP / zero input

> VC = 0: result is +Inf or -Inf (sign from VC).

### `SFPU.SFPSWAP.MINMAX`
_§3.22 SFPSWAP / Mod1=1 VEC_MIN_MAX_

> Mod1=1 (VEC_MIN_MAX): all lanes: VD = min(VC, VD), VC = max(VC, VD).

### `SFPU.SFPSHFT.LEFT_IMM`
§3.23 SFPSHFT / logical left

> Mod1=0 + ARG_IMM: logical left shift by sign-extended Imm12 (& 31).

### `SFPU.SFPSHFT.RIGHT_IMM`
§3.23 SFPSHFT / logical right

> Negative shift with ARITHMETIC clear: logical right shift by (-shift) & 31.

### `SFPU.SFPSHFT.ARITH_RIGHT`
§3.23 SFPSHFT / arithmetic right

> Negative shift with ARITHMETIC set: arithmetic (sign-extending) right shift.

### `SFPU.SFPSHFT2.SHIFT_LREG`
_§3.24 SFPSHFT2 / Mod1=5 SHFT_LREG_

> Mod1=5 (SHFT_LREG): VD = VB << (VC & 31) if VC >= 0, else right shift.

### `SFPU.SFPMUL24.LOWER`
§3.25 SFPMUL24 / Mod1=0 LOWER

> Mod1=0: VD = (VA & 0x7FFFFF) * (VB & 0x7FFFFF) — low 23 bits of 46-bit product.

### `SFPU.SFPMUL24.UPPER`
§3.25 SFPMUL24 / Mod1 bit 0 UPPER

> Mod1 bit 0 set: VD = product >> 23 — high 23 bits.

### `SFPU.SFPLOADI.BF16`
§3.27 SFPLOADI / Mod0=0 FLOATB

> Mod0=0 (FLOATB): VD = BF16ToFP32(Imm16) — BF16 immediate expanded to FP32.

### `SFPU.SFPLOADI.U16`
§3.27 SFPLOADI / Mod0=2 USHORT

> Mod0=2 (USHORT): VD = ZeroExtend(Imm16).

### `SFPU.SFPLOADI.UPPER16`
§3.27 SFPLOADI / Mod0=8 UPPER

> Mod0=8 (UPPER): VD.High16 = Imm16, low 16 bits preserved.

### `SFPU.SFPLOADI.LOWER16`
§3.27 SFPLOADI / Mod0=10 LOWER

> Mod0=10 (LOWER): VD.Low16 = Imm16, high 16 bits preserved.

### `SFPU.SFPCONFIG.PROGCONST`
§3.28 SFPCONFIG / VD=11..14

> VD in 11..14: writes BF16ToFP32(Imm16) to all 32 lanes of that LReg.

### `SFPU.PRED.LANE_FLAGS_INIT_FALSE`
§4.1 Predication State

> LaneFlags initializes to false for all 32 lanes.

### `SFPU.PRED.DISABLED_LANE_NO_WRITE`
§4.3 Effect of Predication

> When a lane is disabled, LReg entries are not written (preserve previous values).

### `SFPU.PRED.CC_UPDATED_REGARDLESS`
§4.3 Effect of Predication

> LaneFlags state IS still updated by comparison instructions (SFPSETCC, SFPGT, SFPIADD) even when a lane is disabled.

### `SFPU.PRED.SFPENCC_ENABLE`
§4.4 SFPENCC

> Mod1=0: use_lane_flags unchanged; LaneFlags = true for all lanes.

### `SFPU.PRED.SFPENCC_DISABLE`
§4.4 SFPENCC / Mod1=0 with Imm2=0

> Mod1=0 disables predication (use_lane_flags = False).

### `SFPU.PRED.PUSHC`
§4.5 SFPPUSHC

> Mod1=0: push current LaneFlags copy onto flag_stack.

### `SFPU.PRED.POPC`
§4.6 SFPPOPC

> Mod1=0: pop from flag_stack, restoring LaneFlags.

### `SFPU.PRED.COMPC`
§4.7 SFPCOMPC

> SFPCOMPC inverts LaneFlags (implements else branch).

### `SFPU.PRED.FLAG_STACK_DEPTH`
§4.5 SFPPUSHC / stack depth limit 8

> Flag stack depth limit is 8 entries.

### `SFPU.PRED.SIMT_IF_ELSE`
§4.9 SIMT if/else/endif Pattern

> Canonical SIMT branching: SFPENCC → SFPPUSHC → (condition) → SFPSETCC → (if body) → SFPCOMPC → (else body) → SFPPOPC restores state.
