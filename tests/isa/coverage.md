# ISA coverage inventory

Generated from local manuals with `python -m tests.isa.inventory`.
Encoding checks do not establish hardware behavior. “Not audited” is an open gap,
not a skip or a passing behavioral test. See [audit.md](audit.md) for reviewed
existing-test assertions, limitations and recorded outcomes. Blackhole pages forwarding to Wormhole
are resolved; no other Wormhole behavior is assumed to apply.

Manual commit: `82f600dca3ec664b721bcb0effc087f0c3fd7c11`.

Encoding field counts below come from the Blackhole LLK header. Manual diagrams
provide additional checks only where a Blackhole contract is explicit. The full
JSON also inventories modifiers in specialized subpages (casts, rounding, etc.).

| Instruction | Source | Documented constants | Encoding fields checked | Behavior |
|---|---|---|---|---|
| ADDDMAREG | missing | — | 4 | [partial](test_scalar.py) |
| ADDRCRXY | missing | — | 6 | not audited |
| ADDRCRZW | missing | — | 6 | not audited |
| APOOL3S1 | missing | — | 4 | not audited |
| APOOL3S2 | missing | — | 4 | not audited |
| ATCAS | missing | — | 6 | not audited |
| ATGETM | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/ATGETM.md) | — | 1 | [partial](test_sync.py) / [reviewed claims](audit.md) |
| ATINCGET | missing | — | 5 | not audited |
| ATINCGETPTR | missing | — | 7 | not audited |
| ATRELM | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/ATRELM.md) | — | 1 | [partial](test_sync.py) / [reviewed claims](audit.md) |
| ATSWAP | missing | — | 4 | not audited |
| BITWOPDMAREG | missing | — | 5 | [partial](test_scalar.py) |
| CFGSHIFTMASK | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/CFGSHIFTMASK.md) | — | 6 | not audited |
| CLEARDVALID | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/CLEARDVALID.md) | — | 2 | partial / [reviewed claims](audit.md) |
| CLREXPHIST | missing | — | 0 | not audited |
| CMPDMAREG | missing | — | 5 | [partial](test_scalar.py) |
| CONV3S1 | missing | — | 4 | not audited |
| CONV3S2 | missing | — | 4 | not audited |
| DMANOP | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/DMANOP.md) | — | 0 | not audited |
| DOTPV | missing | — | 5 | not audited |
| ELWADD | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ELWADD.md) | — | 5 | partial / [reviewed claims](audit.md) |
| ELWMUL | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ELWMUL.md) | — | 5 | partial / [reviewed claims](audit.md) |
| ELWSUB | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ELWSUB.md) | — | 5 | partial / [reviewed claims](audit.md) |
| FLUSHDMA | missing | — | 1 | not audited |
| GAPOOL | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/GAPOOL.md) | — | 5 | partial / [reviewed claims](audit.md) |
| GATESRCRST | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/GATESRCRST.md) | — | 2 | not audited |
| GMPOOL | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/GMPOOL.md) | — | 5 | partial / [reviewed claims](audit.md) |
| INCADCXY | missing | — | 5 | not audited |
| INCADCZW | missing | — | 5 | not audited |
| INCRWC | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/INCRWC.md) | — | 4 | partial / [reviewed claims](audit.md) |
| LOADIND | missing | — | 5 | not audited |
| LOADREG | missing | — | 2 | not audited |
| MFCONV3S1 | missing | — | 4 | not audited |
| MOP | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOP.md) | — | 3 | partial / [reviewed claims](audit.md) |
| MOP_CFG | missing | — | 1 | not audited |
| MOVA2D | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVA2D.md) | — | 5 | partial / [reviewed claims](audit.md) |
| MOVB2A | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVB2A.md) | — | 4 | not audited |
| MOVB2D | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVB2D.md) | — | 5 | partial / [reviewed claims](audit.md) |
| MOVD2A | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVD2A.md) | — | 5 | partial / [reviewed claims](audit.md) |
| MOVD2B | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MOVD2B.md) | — | 5 | partial / [reviewed claims](audit.md) |
| MOVDBGA2D | missing | — | 5 | not audited |
| MOVDBGB2D | missing | — | 5 | not audited |
| MPOOL3S1 | missing | — | 4 | not audited |
| MPOOL3S2 | missing | — | 4 | not audited |
| MULDMAREG | missing | — | 4 | [partial](test_scalar.py) |
| MVMUL | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/MVMUL.md) | — | 4 | partial / [reviewed claims](audit.md) |
| NOP | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/NOP.md) | — | 0 | not audited |
| PACR | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/PACR.md) | — | 12 | partial / [reviewed claims](audit.md) |
| PACR_SETREG | missing | — | 8 | not audited |
| RAREB | missing | — | 0 | not audited |
| RDCFG | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/RDCFG.md) | — | 2 | not audited |
| REG2FLOP | missing | — | 6 | not audited |
| REPLAY | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/REPLAY.md) | — | 4 | partial / [reviewed claims](audit.md) |
| RESOURCEDECL | missing | — | 3 | not audited |
| RMWCIB0 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/RMWCIB.md) | — | 3 | not audited |
| RMWCIB1 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/RMWCIB.md) | — | 3 | not audited |
| RMWCIB2 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/RMWCIB.md) | — | 3 | not audited |
| RMWCIB3 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/RMWCIB.md) | — | 3 | not audited |
| RSTDMA | missing | — | 0 | not audited |
| SEMGET | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SEMGET.md) | — | 1 | [partial](test_sync.py) / [reviewed claims](audit.md) |
| SEMINIT | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SEMINIT.md) | — | 3 | [partial](test_sync.py) / [reviewed claims](audit.md) |
| SEMPOST | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SEMPOST.md) | — | 1 | [partial](test_sync.py) / [reviewed claims](audit.md) |
| SEMWAIT | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SEMWAIT.md) | — | 3 | [partial](test_sync.py) / [reviewed claims](audit.md) |
| SETADC | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADC.md) | — | 4 | not audited |
| SETADCXX | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCXX.md) | — | 3 | not audited |
| SETADCXY | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCXY.md) | — | 6 | not audited |
| SETADCZW | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETADCZW.md) | — | 6 | not audited |
| SETASHRMH | missing | — | 2 | not audited |
| SETASHRMH0 | missing | — | 2 | not audited |
| SETASHRMH1 | missing | — | 2 | not audited |
| SETASHRMV | missing | — | 1 | not audited |
| SETC16 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SETC16.md) | — | 2 | not audited |
| SETDMAREG | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETDMAREG_Immediate.md) | — | 4 | not audited |
| SETDVALID | missing | — | 1 | not audited |
| SETIBRWC | missing | — | 3 | not audited |
| SETPKEDGOF | missing | — | 4 | not audited |
| SETRWC | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/SETRWC.md) | — | 6 | not audited |
| SFPABS | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPABS.md) | `SFPABS_MOD1_INT=0`, `SFPABS_MOD1_FLOAT=1` | 4 | [partial](test_sfpu_bits.py) / [reviewed claims](audit.md) |
| SFPADD | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPADD.md) | — | 5 | partial / [reviewed claims](audit.md) |
| SFPADDI | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPADDI.md) | `SFPMAD_MOD1_NEGATE_VC=2`, `SFPMAD_MOD1_INDIRECT_VD=8` | 3 | partial / [reviewed claims](audit.md) |
| SFPAND | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPAND.md) | `SFPAND_MOD1_USE_VB=1` | 4 | [partial](test_sfpu_bits.py) |
| SFPARECIP | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPARECIP.md) | `SFPARECIP_MOD1_RECIP=0`, `SFPARECIP_MOD1_COND_RECIP=1`, `SFPARECIP_MOD1_EXP=2` | 4 | partial / [reviewed claims](audit.md) |
| SFPCAST | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPCAST.md) | — | 3 | [partial](test_sfpu_bits.py) / [reviewed claims](audit.md) |
| SFPCOMPC | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPCOMPC.md) | — | 4 | [partial](test_predicate_stack.py) |
| SFPCONFIG | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPCONFIG.md) | `MOD1_IMM16_IS_VALUE=1`, `MOD1_IMM16_IS_LANE_MASK=8` | 3 | partial / [reviewed claims](audit.md) |
| SFPDIVP2 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPDIVP2.md) | `SFPDIVP2_MOD1_ADD=1` | 4 | [partial](test_sfpu_bits.py) |
| SFPENCC | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPENCC.md) | `SFPENCC_MOD1_EC=1 // Invert UseLaneFlagsForLaneEnable`, `SFPENCC_MOD1_EI=2 // Set UseLaneFlagsForLaneEnable from SFPENCC_IMM2_E`, `SFPENCC_MOD1_RI=8 // Set LaneFlags from SFPENCC_IMM2_R`, `SFPENCC_IMM2_E=1 // Immediate bit for UseLaneFlagsForLaneEnable`, `SFPENCC_IMM2_R=2 // Immediate bit for LaneFlags` | 4 | [partial](test_predicate_stack.py) / [reviewed claims](audit.md) |
| SFPEXEXP | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPEXEXP.md) | `SFPEXEXP_MOD1_NODEBIAS=1`, `SFPEXEXP_MOD1_SET_CC_SGN_EXP=2`, `SFPEXEXP_MOD1_SET_CC_COMP_EXP=8` | 4 | [partial](test_sfpu_bits.py) |
| SFPEXMAN | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPEXMAN.md) | `SFPEXMAN_MOD1_PAD9=1` | 4 | [partial](test_sfpu_bits.py) |
| SFPGT | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPGT.md) | `SFPGT_MOD1_SET_CC=1`, `SFPGT_MOD1_MUTATE_STACK=2`, `SFPGT_MOD1_MUTATE_OR=4`, `SFPGT_MOD1_SET_VD=8` | 4 | [partial](test_sfpu_bits.py), [partial](test_predicate_stack.py) |
| SFPIADD | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPIADD.md) | `SFPIADD_MOD1_ARG_LREG_DST=0`, `SFPIADD_MOD1_ARG_IMM=1`, `SFPIADD_MOD1_ARG_2SCOMP_LREG_DST=2`, `SFPIADD_MOD1_CC_LT0=0`, `SFPIADD_MOD1_CC_NONE=4`, `SFPIADD_MOD1_CC_GTE0=8` | 4 | [partial](test_sfpu_bits.py) |
| SFPLE | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLE.md) | `SFPLE_MOD1_SET_CC=1`, `SFPLE_MOD1_MUTATE_STACK=2`, `SFPLE_MOD1_MUTATE_OR=4`, `SFPLE_MOD1_SET_VD=8` | 4 | [partial](test_sfpu_bits.py), [partial](test_predicate_stack.py) |
| SFPLOAD | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLOAD.md) | — | 4 | partial / [reviewed claims](audit.md) |
| SFPLOADI | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLOADI.md) | `SFPLOADI_MOD0_FLOATB=0 // Immediate is BF16`, `SFPLOADI_MOD0_FLOATA=1 // Immediate is FP16 (ish)`, `SFPLOADI_MOD0_USHORT=2 // Immediate is UINT16`, `SFPLOADI_MOD0_SHORT=4 // Immediate is INT16`, `SFPLOADI_MOD0_UPPER=8 // Immediate overwrites upper 16 bits`, `SFPLOADI_MOD0_LOWER=10 // Immediate overwrites lower 16 bits` | 3 | [partial](test_sfpu_bits.py) / [reviewed claims](audit.md) |
| SFPLOADMACRO | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLOADMACRO.md) | — | 4 | partial / [reviewed claims](audit.md) |
| SFPLUT | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLUT.md) | `SFPLUT_MOD0_SGN_RETAIN=4`, `SFPLUT_MOD0_INDIRECT_VD=8` | 3 | not audited |
| SFPLUTFP32 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLUTFP32.md) | `SFPLUTFP32_MOD1_FP32_3ENTRY_TABLE=0`, `SFPLUTFP32_MOD1_FP16_3ENTRY_TABLE=10 // Overlaps with SFPLUTFP32_MOD1_INDIRECT_VD!`, `SFPLUTFP32_MOD1_FP16_6ENTRY_TABLE1=2`, `SFPLUTFP32_MOD1_FP16_6ENTRY_TABLE2=3`, `SFPLUTFP32_MOD1_SGN_RETAIN=4`, `SFPLUTFP32_MOD1_INDIRECT_VD=8 // Overlaps with SFPLUTFP32_MOD1_FP16_3ENTRY_TABLE!` | 2 | not audited |
| SFPLZ | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPLZ.md) | `SFPLZ_MOD1_CC_NE0=2`, `SFPLZ_MOD1_NOSGN_MASK=4`, `SFPLZ_MOD1_CC_COMP=8` | 4 | [partial](test_sfpu_bits.py) |
| SFPMAD | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPMAD.md) | `SFPMAD_MOD1_NEGATE_VA=1`, `SFPMAD_MOD1_NEGATE_VC=2`, `SFPMAD_MOD1_INDIRECT_VA=4`, `SFPMAD_MOD1_INDIRECT_VD=8` | 5 | partial / [reviewed claims](audit.md) |
| SFPMOV | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPMOV.md) | `SFPMOV_MOD1_NEGATE=1`, `SFPMOV_MOD1_ALL_LANES_ENABLED=2`, `SFPMOV_MOD1_FROM_SPECIAL=8` | 4 | [partial](test_sfpu_bits.py) / [reviewed claims](audit.md) |
| SFPMUL | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPMUL.md) | — | 5 | partial / [reviewed claims](audit.md) |
| SFPMUL24 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPMUL24.md) | `SFPMUL24_MOD1_UPPER=1`, `SFPMUL24_MOD1_INDIRECT_VA=4`, `SFPMUL24_MOD1_INDIRECT_VD=8` | 5 | [partial](test_sfpu_bits.py) |
| SFPMULI | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPMULI.md) | `SFPMAD_MOD1_NEGATE_VC=2`, `SFPMAD_MOD1_INDIRECT_VD=8` | 3 | not audited |
| SFPNOP | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPNOP.md) | — | 0 | not audited |
| SFPNOT | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPNOT.md) | — | 4 | [partial](test_sfpu_bits.py) |
| SFPOR | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPOR.md) | `SFPOR_MOD1_USE_VB=1` | 4 | [partial](test_sfpu_bits.py) |
| SFPPOPC | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPPOPC.md) | — | 4 | [partial](test_predicate_stack.py) |
| SFPPUSHC | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPPUSHC.md) | — | 4 | [partial](test_predicate_stack.py) |
| SFPSETCC | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSETCC.md) | `SFPSETCC_MOD1_IMM_BIT0=1`, `SFPSETCC_MOD1_CLEAR=8`, `SFPSETCC_MOD1_LREG_LT0=0`, `SFPSETCC_MOD1_LREG_NE0=2`, `SFPSETCC_MOD1_LREG_GTE0=4`, `SFPSETCC_MOD1_LREG_EQ0=6` | 4 | [partial](test_sfpu_bits.py) / [reviewed claims](audit.md) |
| SFPSETEXP | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSETEXP.md) | `SFPSETEXP_MOD1_ARG_IMM=1`, `SFPSETEXP_MOD1_ARG_EXPONENT=2` | 4 | [partial](test_sfpu_bits.py) |
| SFPSETMAN | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSETMAN.md) | `SFPSETMAN_MOD1_ARG_IMM=1` | 4 | [partial](test_sfpu_bits.py) |
| SFPSETSGN | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSETSGN.md) | `SFPSETSGN_MOD1_ARG_IMM=1` | 4 | [partial](test_sfpu_bits.py) |
| SFPSHFT | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSHFT.md) | `SFPSHFT_MOD1_ARG_IMM=1`, `SFPSHFT_MOD1_ARITHMETIC=2`, `SFPSHFT_MOD1_ARG_IMM_USE_VC=4` | 4 | [partial](test_sfpu_bits.py) |
| SFPSHFT2 | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSHFT2.md) | `SFPSHFT2_MOD1_COPY4=0`, `SFPSHFT2_MOD1_SUBVEC_CHAINED_COPY4=1`, `SFPSHFT2_MOD1_SUBVEC_SHFLROR1_AND_COPY4=2`, `SFPSHFT2_MOD1_SUBVEC_SHFLROR1=3`, `SFPSHFT2_MOD1_SUBVEC_SHFLSHR1=4`, `SFPSHFT2_MOD1_SHFT_LREG=5`, `SFPSHFT2_MOD1_SHFT_IMM=6` | 4 | not audited |
| SFPSTOCHRND | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSTOCHRND.md) | — | 6 | not audited |
| SFPSTORE | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSTORE.md) | — | 4 | partial / [reviewed claims](audit.md) |
| SFPSWAP | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPSWAP.md) | `SFPSWAP_MOD1_SWAP=0`, `SFPSWAP_MOD1_VEC_MIN_MAX=1`, `SFPSWAP_MOD1_SUBVEC_MIN01_MAX23=2`, `SFPSWAP_MOD1_SUBVEC_MIN02_MAX13=3`, `SFPSWAP_MOD1_SUBVEC_MIN03_MAX12=4`, `SFPSWAP_MOD1_SUBVEC_MIN0_MAX123=5`, `SFPSWAP_MOD1_SUBVEC_MIN1_MAX023=6`, `SFPSWAP_MOD1_SUBVEC_MIN2_MAX013=7`, `SFPSWAP_MOD1_SUBVEC_MIN3_MAX012=8` | 4 | partial / [reviewed claims](audit.md) |
| SFPTRANSP | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPTRANSP.md) | — | 4 | not audited |
| SFPXOR | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/SFPXOR.md) | — | 4 | [partial](test_sfpu_bits.py) |
| SHIFTDMAREG | missing | — | 5 | [partial](test_scalar.py) |
| SHIFTXA | missing | — | 2 | not audited |
| SHIFTXB | missing | — | 3 | not audited |
| STALLWAIT | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/STALLWAIT.md) | — | 2 | partial / [reviewed claims](audit.md) |
| STOREIND | missing | — | 7 | not audited |
| STOREREG | missing | — | 2 | not audited |
| STREAMWAIT | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/STREAMWAIT.md) | — | 4 | not audited |
| STREAMWRCFG | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/STREAMWRCFG.md) | — | 3 | not audited |
| SUBDMAREG | missing | — | 4 | [partial](test_scalar.py) |
| TBUFCMD | missing | — | 0 | not audited |
| TRNSPSRCA | missing | — | 0 | not audited |
| TRNSPSRCB | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/TRNSPSRCB.md) | — | 0 | not audited |
| UNPACR | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_Regular.md) | — | 13 | partial / [reviewed claims](audit.md) |
| UNPACR_NOP | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/UNPACR_NOP_SETDVALID.md) | — | 9 | partial / [reviewed claims](audit.md) |
| WRCFG | [manual](../../../../tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/WRCFG.md) | — | 3 | not audited |
| XMOV | missing | — | 2 | not audited |
| ZEROACC | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ZEROACC.md) | `ZEROACC_MODE_ONE_ROW=0`, `ZEROACC_MODE_16_ROWS=1`, `ZEROACC_MODE_HALF_OF_DST=2`, `ZEROACC_MODE_ALL_OF_DST=3` | 5 | partial / [reviewed claims](audit.md) |
| ZEROSRC | [manual](../../../../tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ZEROSRC.md) | — | 4 | not audited |

## Architecture pages

These pages include non-opcode functionality (configuration, memory, NoC,
PCIe, Ethernet, and L2CPU). All require separate behavioral coverage review.

- `BlackholeA0/EthernetTile/BabyRISCV/README.md`: not audited
- `BlackholeA0/EthernetTile/EthernetRxClassifier.md`: not audited
- `BlackholeA0/EthernetTile/EthernetTxRx.md`: not audited
- `BlackholeA0/EthernetTile/README.md`: not audited
- `BlackholeA0/EthernetTile/Samples/ethdump/README.md`: not audited
- `BlackholeA0/L2CPUTile/Caches.md`: not audited
- `BlackholeA0/L2CPUTile/MSICatcher.md`: not audited
- `BlackholeA0/L2CPUTile/MemoryMap.md`: not audited
- `BlackholeA0/L2CPUTile/README.md`: not audited
- `BlackholeA0/L2CPUTile/RNMIs.md`: not audited
- `BlackholeA0/L2CPUTile/TLBWindows.md`: not audited
- `BlackholeA0/NoC/Atomics.md`: not audited
- `BlackholeA0/NoC/Coordinates.md`: not audited
- `BlackholeA0/NoC/Counters.md`: not audited
- `BlackholeA0/NoC/Interrupts.md`: not audited
- `BlackholeA0/NoC/MemoryMap.md`: not audited
- `BlackholeA0/NoC/README.md`: not audited
- `BlackholeA0/NoC/RoutingPaths.md`: not audited
- `BlackholeA0/PCIExpressTile/HostToDeviceTLBs.md`: not audited
- `BlackholeA0/PCIExpressTile/README.md`: not audited
- `BlackholeA0/README.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/AutoTTSync.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/CSRs.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/InstructionSet.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/L1CacheTagSearchAccel.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/Mailboxes.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/ManualTTSync.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/MemoryOrdering.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/PCBufs.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/PushTensixInstruction.md`: not audited
- `BlackholeA0/TensixTile/BabyRISCV/README.md`: not audited
- `BlackholeA0/TensixTile/DebugTimestamper.md`: not audited
- `BlackholeA0/TensixTile/L1.md`: not audited
- `BlackholeA0/TensixTile/PIC.md`: not audited
- `BlackholeA0/TensixTile/README.md`: not audited
- `BlackholeA0/TensixTile/SoftReset.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/ATGETM.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/ATRELM.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/BackendConfiguration.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/CFGSHIFTMASK.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/ConfigurationUnit.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/Dst.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/LReg.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/MOPExpander.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/MatrixUnit.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/RDCFG.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/RMWCIB.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SEMGET.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SEMINIT.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SEMPOST.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SEMWAIT.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SETC16.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPABS.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPADD.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPADDI.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPAND.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPARECIP.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPCAST.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPCAST_IntAbs.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPCAST_IntFloat.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPCAST_IntInt.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPCOMPC.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPCONFIG.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPDIVP2.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPENCC.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPEXEXP.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPEXMAN.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPGT.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPIADD.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPLE.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPLOAD.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPLOADI.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPLOADMACRO.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPLUT.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPLUTFP32.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPLZ.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPMAD.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPMOV.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPMUL.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPMUL24.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPMULI.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPNOP.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPNOT.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPOR.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPPOPC.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPPUSHC.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSETCC.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSETEXP.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSETMAN.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSETSGN.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSHFT.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSHFT2.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSTOCHRND.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSTOCHRND_FloatFloat.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSTOCHRND_FloatInt.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSTOCHRND_IntInt.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSTORE.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPSWAP.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPTRANSP.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SFPXOR.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/STALLWAIT.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/STREAMWAIT.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/STREAMWRCFG.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/SyncUnit.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/UNPACR_Regular.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/VectorUnit.md`: not audited
- `BlackholeA0/TensixTile/TensixCoprocessor/WRCFG.md`: not audited
- `BlackholeA0/TensixTile/TileControlDebugStatus.md`: not audited
