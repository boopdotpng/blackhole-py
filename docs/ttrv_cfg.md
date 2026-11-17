# ttrv config fields (generated)

every writable field in Blackhole `Config` / `ThreadConfig`: 820 fields, generated from tt-metal `cfg_defines.h`.
names are the native `cfg_defines.h` names. `word` is the 32-bit word index, `bits` is shift:width.

not in this file (configured elsewhere): MOP templates (MMIO), replay buffer (`REPLAY`), SFPU `LaneConfig` / `LoadMacroConfig` (`SFPCONFIG`), TDMA-RISC registers, ADCs (`SETADC*`), RWCs (`SETRWC` / `INCRWC`).

contexts: unpack a has contexts 0-7, unpack b 0-1, some unpack fields only have 4 copies (ctx & 3). pack has contexts 0-3 spread over THCON_SEC0_REG1, SEC0_REG8, SEC1_REG1, SEC1_REG8 and the `_SEC0..3` PACK fields. `Shift_amount_cntx0..3` has two uses: together they form the row stride, and in one mode each is the column shift for ctx & 3.

the unpack context counts, `base`, `offset` and `x_dim` aliasing, and context selection were measured on Blackhole (see [unpack contexts](ttrv_pack_unpack.md#unpack-contexts)). b's fields for contexts 2-7 are writable but unused: b on context 2-7 hangs the card. the public advanced-configuration grammar is still under audit in [the spec](ttrv_spec.md); these native names document encodings, not accepted application syntax.

## thread (ThreadConfig, SETC16): 47 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `CFG_STATE_ID_StateID` | 0 | 0:1 |  |
| `DEST_TARGET_REG_CFG_MATH_Offset` | 1 | 0:12 |  |
| `DISABLE_IMPLIED_SRCA_FMT_Base` | 2 | 0:1 |  |
| `DISABLE_IMPLIED_SRCB_FMT_Base` | 3 | 0:1 |  |
| `SFPU_DEST_FMT_Enable` | 4 | 0:1 |  |
| `SFPU_DEST_FMT_Base` | 4 | 1:4 |  |
| `SRCA_SET_Base` | 5 | 0:2 |  |
| `SRCA_SET_SetOvrdWithAddr` | 5 | 2:1 |  |
| `SRCB_SET_Base` | 6 | 0:2 |  |
| `CLR_DVALID_SrcA_Disable` | 7 | 0:1 |  |
| `CLR_DVALID_SrcB_Disable` | 7 | 1:1 |  |
| `SCBD_BANK_MASK_32b_Enable` | 8 | 0:1 |  |
| `PACK_SCBD_BANK_MASK_32b_Enable` | 9 | 0:1 |  |
| `UNPACK_SCBD_BANK_MASK_32b_Enable` | 10 | 0:1 |  |
| `FIDELITY_BASE_Phase` | 11 | 0:2 |  |
| `SFPU_STACK_Incr` | 36 | 0:10 |  |
| `NOC_OVERLAY_MSG_CLEAR_StreamId_0` | 42 | 0:6 |  |
| `NOC_OVERLAY_MSG_CLEAR_MsgNum_0` | 42 | 8:3 |  |
| `NOC_OVERLAY_MSG_CLEAR_StreamId_1` | 43 | 0:6 |  |
| `NOC_OVERLAY_MSG_CLEAR_MsgNum_1` | 43 | 8:3 |  |
| `PERF_CNT_CMD_Cmd0Start` | 44 | 0:1 |  |
| `PERF_CNT_CMD_Cmd0Stop` | 44 | 1:1 |  |
| `PERF_CNT_CMD_Cmd1Start` | 44 | 2:1 |  |
| `PERF_CNT_CMD_Cmd1Stop` | 44 | 3:1 |  |
| `PERF_CNT_CMD_Cmd2Start` | 44 | 4:1 |  |
| `PERF_CNT_CMD_Cmd2Stop` | 44 | 5:1 |  |
| `PERF_CNT_CMD_Cmd3Start` | 44 | 6:1 |  |
| `PERF_CNT_CMD_Cmd3Stop` | 44 | 7:1 |  |
| `ENABLE_ACC_STATS_Enable` | 45 | 0:1 |  |
| `FPU_BIAS_SEL_Pointer` | 46 | 0:1 |  |
| `FP16A_FORCE_Enable` | 55 | 0:1 |  |
| `TENSIX_TRISC_SYNC_TrackGlobalCfg` | 56 | 0:1 |  |
| `TENSIX_TRISC_SYNC_EnSubdividedCfgForUnpacr` | 56 | 1:1 |  |
| `TENSIX_TRISC_SYNC_TrackGPR` | 56 | 2:1 |  |
| `TENSIX_TRISC_SYNC_TrackTDMARegs` | 56 | 3:1 |  |
| `TENSIX_TRISC_SYNC_TrackTensixInstructions` | 56 | 4:1 |  |
| `STREAMWAIT_PHASE_HI_Val` | 57 | 0:10 |  |
| `STREAMWAIT_NUM_MSGS_HI_Val` | 58 | 0:7 |  |
| `STREAM_ID_SYNC_SEC0_BankSel` | 59 | 0:6 |  |
| `STREAM_ID_SYNC_SEC1_BankSel` | 60 | 0:6 |  |
| `STREAM_ID_SYNC_SEC2_BankSel` | 61 | 0:6 |  |
| `STREAM_ID_SYNC_SEC3_BankSel` | 62 | 0:6 |  |
| `STREAM_ID_TRISC_SEC0_BankSel` | 63 | 0:6 |  |
| `STREAM_ID_TRISC_SEC1_BankSel` | 64 | 0:6 |  |
| `STREAM_ID_TRISC_SEC2_BankSel` | 65 | 0:6 |  |
| `STREAM_ID_TRISC_SEC3_BankSel` | 66 | 0:6 |  |
| `TENSIX_CSR_CONFIG_RawBusyStatus` | 67 | 0:1 |  |

## addrmod (ThreadConfig, SETC16): 168 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `ADDR_MOD_AB_SEC0_SrcAIncr` | 12 | 0:6 |  |
| `ADDR_MOD_AB_SEC0_SrcACR` | 12 | 6:1 |  |
| `ADDR_MOD_AB_SEC0_SrcAClear` | 12 | 7:1 |  |
| `ADDR_MOD_AB_SEC0_SrcBIncr` | 12 | 8:6 |  |
| `ADDR_MOD_AB_SEC0_SrcBCR` | 12 | 14:1 |  |
| `ADDR_MOD_AB_SEC0_SrcBClear` | 12 | 15:1 |  |
| `ADDR_MOD_AB_SEC1_SrcAIncr` | 13 | 0:6 |  |
| `ADDR_MOD_AB_SEC1_SrcACR` | 13 | 6:1 |  |
| `ADDR_MOD_AB_SEC1_SrcAClear` | 13 | 7:1 |  |
| `ADDR_MOD_AB_SEC1_SrcBIncr` | 13 | 8:6 |  |
| `ADDR_MOD_AB_SEC1_SrcBCR` | 13 | 14:1 |  |
| `ADDR_MOD_AB_SEC1_SrcBClear` | 13 | 15:1 |  |
| `ADDR_MOD_AB_SEC2_SrcAIncr` | 14 | 0:6 |  |
| `ADDR_MOD_AB_SEC2_SrcACR` | 14 | 6:1 |  |
| `ADDR_MOD_AB_SEC2_SrcAClear` | 14 | 7:1 |  |
| `ADDR_MOD_AB_SEC2_SrcBIncr` | 14 | 8:6 |  |
| `ADDR_MOD_AB_SEC2_SrcBCR` | 14 | 14:1 |  |
| `ADDR_MOD_AB_SEC2_SrcBClear` | 14 | 15:1 |  |
| `ADDR_MOD_AB_SEC3_SrcAIncr` | 15 | 0:6 |  |
| `ADDR_MOD_AB_SEC3_SrcACR` | 15 | 6:1 |  |
| `ADDR_MOD_AB_SEC3_SrcAClear` | 15 | 7:1 |  |
| `ADDR_MOD_AB_SEC3_SrcBIncr` | 15 | 8:6 |  |
| `ADDR_MOD_AB_SEC3_SrcBCR` | 15 | 14:1 |  |
| `ADDR_MOD_AB_SEC3_SrcBClear` | 15 | 15:1 |  |
| `ADDR_MOD_AB_SEC4_SrcAIncr` | 16 | 0:6 |  |
| `ADDR_MOD_AB_SEC4_SrcACR` | 16 | 6:1 |  |
| `ADDR_MOD_AB_SEC4_SrcAClear` | 16 | 7:1 |  |
| `ADDR_MOD_AB_SEC4_SrcBIncr` | 16 | 8:6 |  |
| `ADDR_MOD_AB_SEC4_SrcBCR` | 16 | 14:1 |  |
| `ADDR_MOD_AB_SEC4_SrcBClear` | 16 | 15:1 |  |
| `ADDR_MOD_AB_SEC5_SrcAIncr` | 17 | 0:6 |  |
| `ADDR_MOD_AB_SEC5_SrcACR` | 17 | 6:1 |  |
| `ADDR_MOD_AB_SEC5_SrcAClear` | 17 | 7:1 |  |
| `ADDR_MOD_AB_SEC5_SrcBIncr` | 17 | 8:6 |  |
| `ADDR_MOD_AB_SEC5_SrcBCR` | 17 | 14:1 |  |
| `ADDR_MOD_AB_SEC5_SrcBClear` | 17 | 15:1 |  |
| `ADDR_MOD_AB_SEC6_SrcAIncr` | 18 | 0:6 |  |
| `ADDR_MOD_AB_SEC6_SrcACR` | 18 | 6:1 |  |
| `ADDR_MOD_AB_SEC6_SrcAClear` | 18 | 7:1 |  |
| `ADDR_MOD_AB_SEC6_SrcBIncr` | 18 | 8:6 |  |
| `ADDR_MOD_AB_SEC6_SrcBCR` | 18 | 14:1 |  |
| `ADDR_MOD_AB_SEC6_SrcBClear` | 18 | 15:1 |  |
| `ADDR_MOD_AB_SEC7_SrcAIncr` | 19 | 0:6 |  |
| `ADDR_MOD_AB_SEC7_SrcACR` | 19 | 6:1 |  |
| `ADDR_MOD_AB_SEC7_SrcAClear` | 19 | 7:1 |  |
| `ADDR_MOD_AB_SEC7_SrcBIncr` | 19 | 8:6 |  |
| `ADDR_MOD_AB_SEC7_SrcBCR` | 19 | 14:1 |  |
| `ADDR_MOD_AB_SEC7_SrcBClear` | 19 | 15:1 |  |
| `ADDR_MOD_AB2_SEC0_SrcAIncr` | 20 | 0:1 |  |
| `ADDR_MOD_AB2_SEC0_SrcBIncr` | 20 | 1:1 |  |
| `ADDR_MOD_AB2_SEC1_SrcAIncr` | 21 | 0:1 |  |
| `ADDR_MOD_AB2_SEC1_SrcBIncr` | 21 | 1:1 |  |
| `ADDR_MOD_AB2_SEC2_SrcAIncr` | 22 | 0:1 |  |
| `ADDR_MOD_AB2_SEC2_SrcBIncr` | 22 | 1:1 |  |
| `ADDR_MOD_AB2_SEC3_SrcAIncr` | 23 | 0:1 |  |
| `ADDR_MOD_AB2_SEC3_SrcBIncr` | 23 | 1:1 |  |
| `ADDR_MOD_AB2_SEC4_SrcAIncr` | 24 | 0:1 |  |
| `ADDR_MOD_AB2_SEC4_SrcBIncr` | 24 | 1:1 |  |
| `ADDR_MOD_AB2_SEC5_SrcAIncr` | 25 | 0:1 |  |
| `ADDR_MOD_AB2_SEC5_SrcBIncr` | 25 | 1:1 |  |
| `ADDR_MOD_AB2_SEC6_SrcAIncr` | 26 | 0:1 |  |
| `ADDR_MOD_AB2_SEC6_SrcBIncr` | 26 | 1:1 |  |
| `ADDR_MOD_AB2_SEC7_SrcAIncr` | 27 | 0:1 |  |
| `ADDR_MOD_AB2_SEC7_SrcBIncr` | 27 | 1:1 |  |
| `ADDR_MOD_DST_SEC0_DestIncr` | 28 | 0:10 |  |
| `ADDR_MOD_DST_SEC0_DestCR` | 28 | 10:1 |  |
| `ADDR_MOD_DST_SEC0_DestClear` | 28 | 11:1 |  |
| `ADDR_MOD_DST_SEC0_DestCToCR` | 28 | 12:1 |  |
| `ADDR_MOD_DST_SEC0_FidelityIncr` | 28 | 13:2 |  |
| `ADDR_MOD_DST_SEC0_FidelityClear` | 28 | 15:1 |  |
| `ADDR_MOD_DST_SEC1_DestIncr` | 29 | 0:10 |  |
| `ADDR_MOD_DST_SEC1_DestCR` | 29 | 10:1 |  |
| `ADDR_MOD_DST_SEC1_DestClear` | 29 | 11:1 |  |
| `ADDR_MOD_DST_SEC1_DestCToCR` | 29 | 12:1 |  |
| `ADDR_MOD_DST_SEC1_FidelityIncr` | 29 | 13:2 |  |
| `ADDR_MOD_DST_SEC1_FidelityClear` | 29 | 15:1 |  |
| `ADDR_MOD_DST_SEC2_DestIncr` | 30 | 0:10 |  |
| `ADDR_MOD_DST_SEC2_DestCR` | 30 | 10:1 |  |
| `ADDR_MOD_DST_SEC2_DestClear` | 30 | 11:1 |  |
| `ADDR_MOD_DST_SEC2_DestCToCR` | 30 | 12:1 |  |
| `ADDR_MOD_DST_SEC2_FidelityIncr` | 30 | 13:2 |  |
| `ADDR_MOD_DST_SEC2_FidelityClear` | 30 | 15:1 |  |
| `ADDR_MOD_DST_SEC3_DestIncr` | 31 | 0:10 |  |
| `ADDR_MOD_DST_SEC3_DestCR` | 31 | 10:1 |  |
| `ADDR_MOD_DST_SEC3_DestClear` | 31 | 11:1 |  |
| `ADDR_MOD_DST_SEC3_DestCToCR` | 31 | 12:1 |  |
| `ADDR_MOD_DST_SEC3_FidelityIncr` | 31 | 13:2 |  |
| `ADDR_MOD_DST_SEC3_FidelityClear` | 31 | 15:1 |  |
| `ADDR_MOD_DST_SEC4_DestIncr` | 32 | 0:10 |  |
| `ADDR_MOD_DST_SEC4_DestCR` | 32 | 10:1 |  |
| `ADDR_MOD_DST_SEC4_DestClear` | 32 | 11:1 |  |
| `ADDR_MOD_DST_SEC4_DestCToCR` | 32 | 12:1 |  |
| `ADDR_MOD_DST_SEC4_FidelityIncr` | 32 | 13:2 |  |
| `ADDR_MOD_DST_SEC4_FidelityClear` | 32 | 15:1 |  |
| `ADDR_MOD_DST_SEC5_DestIncr` | 33 | 0:10 |  |
| `ADDR_MOD_DST_SEC5_DestCR` | 33 | 10:1 |  |
| `ADDR_MOD_DST_SEC5_DestClear` | 33 | 11:1 |  |
| `ADDR_MOD_DST_SEC5_DestCToCR` | 33 | 12:1 |  |
| `ADDR_MOD_DST_SEC5_FidelityIncr` | 33 | 13:2 |  |
| `ADDR_MOD_DST_SEC5_FidelityClear` | 33 | 15:1 |  |
| `ADDR_MOD_DST_SEC6_DestIncr` | 34 | 0:10 |  |
| `ADDR_MOD_DST_SEC6_DestCR` | 34 | 10:1 |  |
| `ADDR_MOD_DST_SEC6_DestClear` | 34 | 11:1 |  |
| `ADDR_MOD_DST_SEC6_DestCToCR` | 34 | 12:1 |  |
| `ADDR_MOD_DST_SEC6_FidelityIncr` | 34 | 13:2 |  |
| `ADDR_MOD_DST_SEC6_FidelityClear` | 34 | 15:1 |  |
| `ADDR_MOD_DST_SEC7_DestIncr` | 35 | 0:10 |  |
| `ADDR_MOD_DST_SEC7_DestCR` | 35 | 10:1 |  |
| `ADDR_MOD_DST_SEC7_DestClear` | 35 | 11:1 |  |
| `ADDR_MOD_DST_SEC7_DestCToCR` | 35 | 12:1 |  |
| `ADDR_MOD_DST_SEC7_FidelityIncr` | 35 | 13:2 |  |
| `ADDR_MOD_DST_SEC7_FidelityClear` | 35 | 15:1 |  |
| `ADDR_MOD_PACK_SEC0_YsrcIncr` | 37 | 0:4 |  |
| `ADDR_MOD_PACK_SEC0_YsrcCR` | 37 | 4:1 |  |
| `ADDR_MOD_PACK_SEC0_YsrcClear` | 37 | 5:1 |  |
| `ADDR_MOD_PACK_SEC0_YdstIncr` | 37 | 6:4 |  |
| `ADDR_MOD_PACK_SEC0_YdstCR` | 37 | 10:1 |  |
| `ADDR_MOD_PACK_SEC0_YdstClear` | 37 | 11:1 |  |
| `ADDR_MOD_PACK_SEC0_ZsrcIncr` | 37 | 12:1 |  |
| `ADDR_MOD_PACK_SEC0_ZsrcClear` | 37 | 13:1 |  |
| `ADDR_MOD_PACK_SEC0_ZdstIncr` | 37 | 14:1 |  |
| `ADDR_MOD_PACK_SEC0_ZdstClear` | 37 | 15:1 |  |
| `ADDR_MOD_PACK_SEC1_YsrcIncr` | 38 | 0:4 |  |
| `ADDR_MOD_PACK_SEC1_YsrcCR` | 38 | 4:1 |  |
| `ADDR_MOD_PACK_SEC1_YsrcClear` | 38 | 5:1 |  |
| `ADDR_MOD_PACK_SEC1_YdstIncr` | 38 | 6:4 |  |
| `ADDR_MOD_PACK_SEC1_YdstCR` | 38 | 10:1 |  |
| `ADDR_MOD_PACK_SEC1_YdstClear` | 38 | 11:1 |  |
| `ADDR_MOD_PACK_SEC1_ZsrcIncr` | 38 | 12:1 |  |
| `ADDR_MOD_PACK_SEC1_ZsrcClear` | 38 | 13:1 |  |
| `ADDR_MOD_PACK_SEC1_ZdstIncr` | 38 | 14:1 |  |
| `ADDR_MOD_PACK_SEC1_ZdstClear` | 38 | 15:1 |  |
| `ADDR_MOD_PACK_SEC2_YsrcIncr` | 39 | 0:4 |  |
| `ADDR_MOD_PACK_SEC2_YsrcCR` | 39 | 4:1 |  |
| `ADDR_MOD_PACK_SEC2_YsrcClear` | 39 | 5:1 |  |
| `ADDR_MOD_PACK_SEC2_YdstIncr` | 39 | 6:4 |  |
| `ADDR_MOD_PACK_SEC2_YdstCR` | 39 | 10:1 |  |
| `ADDR_MOD_PACK_SEC2_YdstClear` | 39 | 11:1 |  |
| `ADDR_MOD_PACK_SEC2_ZsrcIncr` | 39 | 12:1 |  |
| `ADDR_MOD_PACK_SEC2_ZsrcClear` | 39 | 13:1 |  |
| `ADDR_MOD_PACK_SEC2_ZdstIncr` | 39 | 14:1 |  |
| `ADDR_MOD_PACK_SEC2_ZdstClear` | 39 | 15:1 |  |
| `ADDR_MOD_PACK_SEC3_YsrcIncr` | 40 | 0:4 |  |
| `ADDR_MOD_PACK_SEC3_YsrcCR` | 40 | 4:1 |  |
| `ADDR_MOD_PACK_SEC3_YsrcClear` | 40 | 5:1 |  |
| `ADDR_MOD_PACK_SEC3_YdstIncr` | 40 | 6:4 |  |
| `ADDR_MOD_PACK_SEC3_YdstCR` | 40 | 10:1 |  |
| `ADDR_MOD_PACK_SEC3_YdstClear` | 40 | 11:1 |  |
| `ADDR_MOD_PACK_SEC3_ZsrcIncr` | 40 | 12:1 |  |
| `ADDR_MOD_PACK_SEC3_ZsrcClear` | 40 | 13:1 |  |
| `ADDR_MOD_PACK_SEC3_ZdstIncr` | 40 | 14:1 |  |
| `ADDR_MOD_PACK_SEC3_ZdstClear` | 40 | 15:1 |  |
| `ADDR_MOD_BIAS_SEC0_BiasIncr` | 47 | 0:4 |  |
| `ADDR_MOD_BIAS_SEC0_BiasClear` | 47 | 4:1 |  |
| `ADDR_MOD_BIAS_SEC1_BiasIncr` | 48 | 0:4 |  |
| `ADDR_MOD_BIAS_SEC1_BiasClear` | 48 | 4:1 |  |
| `ADDR_MOD_BIAS_SEC2_BiasIncr` | 49 | 0:4 |  |
| `ADDR_MOD_BIAS_SEC2_BiasClear` | 49 | 4:1 |  |
| `ADDR_MOD_BIAS_SEC3_BiasIncr` | 50 | 0:4 |  |
| `ADDR_MOD_BIAS_SEC3_BiasClear` | 50 | 4:1 |  |
| `ADDR_MOD_BIAS_SEC4_BiasIncr` | 51 | 0:4 |  |
| `ADDR_MOD_BIAS_SEC4_BiasClear` | 51 | 4:1 |  |
| `ADDR_MOD_BIAS_SEC5_BiasIncr` | 52 | 0:4 |  |
| `ADDR_MOD_BIAS_SEC5_BiasClear` | 52 | 4:1 |  |
| `ADDR_MOD_BIAS_SEC6_BiasIncr` | 53 | 0:4 |  |
| `ADDR_MOD_BIAS_SEC6_BiasClear` | 53 | 4:1 |  |
| `ADDR_MOD_BIAS_SEC7_BiasIncr` | 54 | 0:4 |  |
| `ADDR_MOD_BIAS_SEC7_BiasClear` | 54 | 4:1 |  |

## unpack a (Config): 15 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `UNP0_ADDR_CTRL_XY_REG_0_Xstride` | 44 | 0:16 |  |
| `UNP0_ADDR_CTRL_XY_REG_0_Ystride` | 44 | 16:16 |  |
| `UNP0_ADDR_CTRL_ZW_REG_0_Zstride` | 45 | 0:16 |  |
| `UNP0_ADDR_CTRL_ZW_REG_0_Wstride` | 45 | 16:16 |  |
| `UNP0_ADDR_BASE_REG_0_Base` | 48 | 0:18 |  |
| `UNP0_ADDR_BASE_REG_1_Base` | 49 | 0:18 |  |
| `UNP0_FORCED_SHARED_EXP_shared_exp` | 50 | 0:8 |  |
| `UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr` | 50 | 8:1 |  |
| `UNP0_BLOBS_Y_START_CNTX_01_blobs_y_start` | 51 | 0:32 |  |
| `UNP0_BLOBS_Y_START_CNTX_23_blobs_y_start` | 52 | 0:32 |  |
| `UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val` | 53 | 0:32 |  |
| `UNP0_ADDR_CTRL_XY_REG_1_Xstride` | 56 | 0:16 |  |
| `UNP0_ADDR_CTRL_XY_REG_1_Ystride` | 56 | 16:16 |  |
| `UNP0_ADDR_CTRL_ZW_REG_1_Zstride` | 57 | 0:16 |  |
| `UNP0_ADDR_CTRL_ZW_REG_1_Wstride` | 57 | 16:16 |  |

## unpack a (Config, THCON): 88 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `THCON_SEC0_REG0_TileDescriptor` | 64 | 0:128 |  |
| `THCON_SEC0_REG2_Out_data_format` | 72 | 0:4 |  |
| `THCON_SEC0_REG2_Throttle_mode` | 72 | 4:2 |  |
| `THCON_SEC0_REG2_Context_count` | 72 | 6:2 |  |
| `THCON_SEC0_REG2_Haloize_mode` | 72 | 8:1 |  |
| `THCON_SEC0_REG2_Tileize_mode` | 72 | 9:1 |  |
| `THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd` | 72 | 10:1 |  |
| `THCON_SEC0_REG2_Unpack_If_Sel` | 72 | 11:1 |  |
| `THCON_SEC0_REG2_Upsample_rate` | 72 | 12:2 |  |
| `THCON_SEC0_REG2_Ovrd_data_format` | 72 | 14:1 |  |
| `THCON_SEC0_REG2_Upsample_and_interleave` | 72 | 15:1 |  |
| `THCON_SEC0_REG2_Shift_amount_cntx0` | 72 | 16:4 | two uses: row stride bits, or column shift for ctx & 3 |
| `THCON_SEC0_REG2_Shift_amount_cntx1` | 72 | 20:4 | two uses: row stride bits, or column shift for ctx & 3 |
| `THCON_SEC0_REG2_Shift_amount_cntx2` | 72 | 24:4 | two uses: row stride bits, or column shift for ctx & 3 |
| `THCON_SEC0_REG2_Shift_amount_cntx3` | 72 | 28:4 | two uses: row stride bits, or column shift for ctx & 3 |
| `THCON_SEC0_REG2_Disable_zero_compress_cntx0` | 73 | 0:1 | unpack ctx 0 |
| `THCON_SEC0_REG2_Disable_zero_compress_cntx1` | 73 | 1:1 | unpack ctx 1 |
| `THCON_SEC0_REG2_Disable_zero_compress_cntx2` | 73 | 2:1 | unpack ctx 2 |
| `THCON_SEC0_REG2_Disable_zero_compress_cntx3` | 73 | 3:1 | unpack ctx 3 |
| `THCON_SEC0_REG2_Unpack_if_sel_cntx0` | 73 | 4:1 | unpack ctx 0 |
| `THCON_SEC0_REG2_Unpack_if_sel_cntx1` | 73 | 5:1 | unpack ctx 1 |
| `THCON_SEC0_REG2_Unpack_if_sel_cntx2` | 73 | 6:1 | unpack ctx 2 |
| `THCON_SEC0_REG2_Unpack_if_sel_cntx3` | 73 | 7:1 | unpack ctx 3 |
| `THCON_SEC0_REG2_Force_shared_exp` | 73 | 8:1 |  |
| `THCON_SEC0_REG2_Context_count_non_log2` | 73 | 9:3 |  |
| `THCON_SEC0_REG2_Context_count_non_log2_en` | 73 | 12:1 |  |
| `THCON_SEC0_REG2_Disable_zero_compress_cntx4` | 73 | 16:1 | unpack ctx 4 |
| `THCON_SEC0_REG2_Disable_zero_compress_cntx5` | 73 | 17:1 | unpack ctx 5 |
| `THCON_SEC0_REG2_Disable_zero_compress_cntx6` | 73 | 18:1 | unpack ctx 6 |
| `THCON_SEC0_REG2_Disable_zero_compress_cntx7` | 73 | 19:1 | unpack ctx 7 |
| `THCON_SEC0_REG2_Unpack_if_sel_cntx4` | 73 | 20:1 | unpack ctx 4 |
| `THCON_SEC0_REG2_Unpack_if_sel_cntx5` | 73 | 21:1 | unpack ctx 5 |
| `THCON_SEC0_REG2_Unpack_if_sel_cntx6` | 73 | 22:1 | unpack ctx 6 |
| `THCON_SEC0_REG2_Unpack_if_sel_cntx7` | 73 | 23:1 | unpack ctx 7 |
| `THCON_SEC0_REG2_Metadata_x_end` | 73 | 24:8 |  |
| `THCON_SEC0_REG2_Unpack_limit_address` | 74 | 0:17 |  |
| `THCON_SEC0_REG2_Unpack_fifo_size` | 75 | 0:17 |  |
| `THCON_SEC0_REG3_Base_address` | 76 | 0:32 | unpack ctx 0 |
| `THCON_SEC0_REG3_Base_cntx1_address` | 77 | 0:32 | unpack ctx 1 |
| `THCON_SEC0_REG3_Base_cntx2_address` | 78 | 0:32 | unpack ctx 2 |
| `THCON_SEC0_REG3_Base_cntx3_address` | 79 | 0:32 | unpack ctx 3 |
| `THCON_SEC0_REG4_Base_cntx4_address` | 80 | 0:32 | unpack ctx 4 |
| `THCON_SEC0_REG4_Base_cntx5_address` | 81 | 0:32 | unpack ctx 5 |
| `THCON_SEC0_REG4_Base_cntx6_address` | 82 | 0:32 | unpack ctx 6 |
| `THCON_SEC0_REG4_Base_cntx7_address` | 83 | 0:32 | unpack ctx 7 |
| `THCON_SEC0_REG5_Dest_cntx0_address` | 84 | 0:16 | unpack ctx 0 |
| `THCON_SEC0_REG5_Dest_cntx1_address` | 84 | 16:16 | unpack ctx 1 |
| `THCON_SEC0_REG5_Dest_cntx2_address` | 85 | 0:16 | unpack ctx 2 |
| `THCON_SEC0_REG5_Dest_cntx3_address` | 85 | 16:16 | unpack ctx 3 |
| `THCON_SEC0_REG5_Tile_x_dim_cntx0` | 86 | 0:16 | unpack ctx 0 |
| `THCON_SEC0_REG5_Tile_x_dim_cntx1` | 86 | 16:16 | unpack ctx 1 |
| `THCON_SEC0_REG5_Tile_x_dim_cntx2` | 87 | 0:16 | unpack ctx 2 |
| `THCON_SEC0_REG5_Tile_x_dim_cntx3` | 87 | 16:16 | unpack ctx 3 |
| `THCON_SEC0_REG6_Source_address` | 88 | 0:32 |  |
| `THCON_SEC0_REG6_Destination_address` | 89 | 0:32 |  |
| `THCON_SEC0_REG6_Buffer_size` | 90 | 0:30 |  |
| `THCON_SEC0_REG6_Transfer_direction` | 90 | 30:2 |  |
| `THCON_SEC0_REG6_Metadata_misc` | 91 | 0:32 |  |
| `THCON_SEC0_REG7_Offset_address` | 92 | 0:16 |  |
| `THCON_SEC0_REG7_Unpack_data_format_cntx0` | 92 | 16:4 | unpack ctx 0 |
| `THCON_SEC0_REG7_Unpack_out_data_format_cntx0` | 92 | 20:4 | unpack ctx 0 |
| `THCON_SEC0_REG7_Unpack_data_format_cntx4` | 92 | 24:4 | unpack ctx 4 |
| `THCON_SEC0_REG7_Unpack_out_data_format_cntx4` | 92 | 28:4 | unpack ctx 4 |
| `THCON_SEC0_REG7_Offset_cntx1_address` | 93 | 0:16 | unpack ctx 1 |
| `THCON_SEC0_REG7_Unpack_data_format_cntx1` | 93 | 16:4 | unpack ctx 1 |
| `THCON_SEC0_REG7_Unpack_out_data_format_cntx1` | 93 | 20:4 | unpack ctx 1 |
| `THCON_SEC0_REG7_Unpack_data_format_cntx5` | 93 | 24:4 | unpack ctx 5 |
| `THCON_SEC0_REG7_Unpack_out_data_format_cntx5` | 93 | 28:4 | unpack ctx 5 |
| `THCON_SEC0_REG7_Offset_cntx2_address` | 94 | 0:16 | unpack ctx 2 |
| `THCON_SEC0_REG7_Unpack_data_format_cntx2` | 94 | 16:4 | unpack ctx 2 |
| `THCON_SEC0_REG7_Unpack_out_data_format_cntx2` | 94 | 20:4 | unpack ctx 2 |
| `THCON_SEC0_REG7_Unpack_data_format_cntx6` | 94 | 24:4 | unpack ctx 6 |
| `THCON_SEC0_REG7_Unpack_out_data_format_cntx6` | 94 | 28:4 | unpack ctx 6 |
| `THCON_SEC0_REG7_Offset_cntx3_address` | 95 | 0:16 | unpack ctx 3 |
| `THCON_SEC0_REG7_Unpack_data_format_cntx3` | 95 | 16:4 | unpack ctx 3 |
| `THCON_SEC0_REG7_Unpack_out_data_format_cntx3` | 95 | 20:4 | unpack ctx 3 |
| `THCON_SEC0_REG7_Unpack_data_format_cntx7` | 95 | 24:4 | unpack ctx 7 |
| `THCON_SEC0_REG7_Unpack_out_data_format_cntx7` | 95 | 28:4 | unpack ctx 7 |
| `THCON_SEC0_REG10_Unpack_limit_address` | 104 | 0:17 |  |
| `THCON_SEC0_REG10_Unpack_fifo_size` | 105 | 0:17 |  |
| `THCON_SEC0_REG10_Unpack_limit_address_en` | 105 | 17:1 |  |
| `THCON_SEC0_REG10_Unpacker_Reg_Wr_Addr` | 106 | 0:24 |  |
| `THCON_SEC0_REG10_Packer_Reg_Wr_Addr` | 107 | 0:24 |  |
| `THCON_SEC0_REG11_Metadata_l1_addr` | 108 | 0:32 |  |
| `THCON_SEC0_REG11_Metadata_limit_addr` | 109 | 0:32 |  |
| `THCON_SEC0_REG11_Metadata_fifo_size` | 110 | 0:32 |  |
| `THCON_SEC0_REG11_Metadata_z_cntr_rst_unpacr_count` | 111 | 0:8 |  |
| `THCON_SEC0_REG11_Metadata_cntxt_switch_unpacr_count` | 111 | 8:8 |  |

## unpack b (Config): 13 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `UNP1_ADDR_CTRL_XY_REG_0_Xstride` | 46 | 0:16 |  |
| `UNP1_ADDR_CTRL_XY_REG_0_Ystride` | 46 | 16:16 |  |
| `UNP1_ADDR_CTRL_ZW_REG_0_Zstride` | 47 | 0:16 |  |
| `UNP1_ADDR_CTRL_ZW_REG_0_Wstride` | 47 | 16:16 |  |
| `UNP1_ADDR_CTRL_XY_REG_1_Xstride` | 58 | 0:16 |  |
| `UNP1_ADDR_CTRL_XY_REG_1_Ystride` | 58 | 16:16 |  |
| `UNP1_ADDR_CTRL_ZW_REG_1_Zstride` | 59 | 0:16 |  |
| `UNP1_ADDR_CTRL_ZW_REG_1_Wstride` | 59 | 16:16 |  |
| `UNP1_ADDR_BASE_REG_0_Base` | 60 | 0:18 |  |
| `UNP1_ADDR_BASE_REG_1_Base` | 61 | 0:18 |  |
| `UNP1_FORCED_SHARED_EXP_shared_exp` | 62 | 0:8 |  |
| `UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr` | 62 | 8:1 |  |
| `UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val` | 63 | 0:32 |  |

## unpack b (Config, THCON): 88 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `THCON_SEC1_REG0_TileDescriptor` | 112 | 0:128 |  |
| `THCON_SEC1_REG2_Out_data_format` | 120 | 0:4 |  |
| `THCON_SEC1_REG2_Throttle_mode` | 120 | 4:2 |  |
| `THCON_SEC1_REG2_Context_count` | 120 | 6:2 |  |
| `THCON_SEC1_REG2_Haloize_mode` | 120 | 8:1 |  |
| `THCON_SEC1_REG2_Tileize_mode` | 120 | 9:1 |  |
| `THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd` | 120 | 10:1 |  |
| `THCON_SEC1_REG2_Unpack_If_Sel` | 120 | 11:1 |  |
| `THCON_SEC1_REG2_Upsample_rate` | 120 | 12:2 |  |
| `THCON_SEC1_REG2_Ovrd_data_format` | 120 | 14:1 |  |
| `THCON_SEC1_REG2_Upsample_and_interleave` | 120 | 15:1 |  |
| `THCON_SEC1_REG2_Shift_amount_cntx0` | 120 | 16:4 | two uses: row stride bits, or column shift for ctx & 3 |
| `THCON_SEC1_REG2_Shift_amount_cntx1` | 120 | 20:4 | two uses: row stride bits, or column shift for ctx & 3 |
| `THCON_SEC1_REG2_Shift_amount_cntx2` | 120 | 24:4 | two uses: row stride bits, or column shift for ctx & 3 |
| `THCON_SEC1_REG2_Shift_amount_cntx3` | 120 | 28:4 | two uses: row stride bits, or column shift for ctx & 3 |
| `THCON_SEC1_REG2_Disable_zero_compress_cntx0` | 121 | 0:1 | unpack ctx 0 |
| `THCON_SEC1_REG2_Disable_zero_compress_cntx1` | 121 | 1:1 | unpack ctx 1 |
| `THCON_SEC1_REG2_Disable_zero_compress_cntx2` | 121 | 2:1 | unpack ctx 2 |
| `THCON_SEC1_REG2_Disable_zero_compress_cntx3` | 121 | 3:1 | unpack ctx 3 |
| `THCON_SEC1_REG2_Unpack_if_sel_cntx0` | 121 | 4:1 | unpack ctx 0 |
| `THCON_SEC1_REG2_Unpack_if_sel_cntx1` | 121 | 5:1 | unpack ctx 1 |
| `THCON_SEC1_REG2_Unpack_if_sel_cntx2` | 121 | 6:1 | unpack ctx 2 |
| `THCON_SEC1_REG2_Unpack_if_sel_cntx3` | 121 | 7:1 | unpack ctx 3 |
| `THCON_SEC1_REG2_Force_shared_exp` | 121 | 8:1 |  |
| `THCON_SEC1_REG2_Context_count_non_log2` | 121 | 9:3 |  |
| `THCON_SEC1_REG2_Context_count_non_log2_en` | 121 | 12:1 |  |
| `THCON_SEC1_REG2_Disable_zero_compress_cntx4` | 121 | 16:1 | unpack ctx 4 |
| `THCON_SEC1_REG2_Disable_zero_compress_cntx5` | 121 | 17:1 | unpack ctx 5 |
| `THCON_SEC1_REG2_Disable_zero_compress_cntx6` | 121 | 18:1 | unpack ctx 6 |
| `THCON_SEC1_REG2_Disable_zero_compress_cntx7` | 121 | 19:1 | unpack ctx 7 |
| `THCON_SEC1_REG2_Unpack_if_sel_cntx4` | 121 | 20:1 | unpack ctx 4 |
| `THCON_SEC1_REG2_Unpack_if_sel_cntx5` | 121 | 21:1 | unpack ctx 5 |
| `THCON_SEC1_REG2_Unpack_if_sel_cntx6` | 121 | 22:1 | unpack ctx 6 |
| `THCON_SEC1_REG2_Unpack_if_sel_cntx7` | 121 | 23:1 | unpack ctx 7 |
| `THCON_SEC1_REG2_Metadata_x_end` | 121 | 24:8 |  |
| `THCON_SEC1_REG2_Unpack_limit_address` | 122 | 0:17 |  |
| `THCON_SEC1_REG2_Unpack_fifo_size` | 123 | 0:17 |  |
| `THCON_SEC1_REG3_Base_address` | 124 | 0:32 | unpack ctx 0 |
| `THCON_SEC1_REG3_Base_cntx1_address` | 125 | 0:32 | unpack ctx 1 |
| `THCON_SEC1_REG3_Base_cntx2_address` | 126 | 0:32 | unpack ctx 2 |
| `THCON_SEC1_REG3_Base_cntx3_address` | 127 | 0:32 | unpack ctx 3 |
| `THCON_SEC1_REG4_Base_cntx4_address` | 128 | 0:32 | unpack ctx 4 |
| `THCON_SEC1_REG4_Base_cntx5_address` | 129 | 0:32 | unpack ctx 5 |
| `THCON_SEC1_REG4_Base_cntx6_address` | 130 | 0:32 | unpack ctx 6 |
| `THCON_SEC1_REG4_Base_cntx7_address` | 131 | 0:32 | unpack ctx 7 |
| `THCON_SEC1_REG5_Dest_cntx0_address` | 132 | 0:16 | unpack ctx 0 |
| `THCON_SEC1_REG5_Dest_cntx1_address` | 132 | 16:16 | unpack ctx 1 |
| `THCON_SEC1_REG5_Dest_cntx2_address` | 133 | 0:16 | unpack ctx 2 |
| `THCON_SEC1_REG5_Dest_cntx3_address` | 133 | 16:16 | unpack ctx 3 |
| `THCON_SEC1_REG5_Tile_x_dim_cntx0` | 134 | 0:16 | unpack ctx 0 |
| `THCON_SEC1_REG5_Tile_x_dim_cntx1` | 134 | 16:16 | unpack ctx 1 |
| `THCON_SEC1_REG5_Tile_x_dim_cntx2` | 135 | 0:16 | unpack ctx 2 |
| `THCON_SEC1_REG5_Tile_x_dim_cntx3` | 135 | 16:16 | unpack ctx 3 |
| `THCON_SEC1_REG6_Source_address` | 136 | 0:32 |  |
| `THCON_SEC1_REG6_Destination_address` | 137 | 0:32 |  |
| `THCON_SEC1_REG6_Buffer_size` | 138 | 0:30 |  |
| `THCON_SEC1_REG6_Transfer_direction` | 138 | 30:2 |  |
| `THCON_SEC1_REG6_Metadata_misc` | 139 | 0:32 |  |
| `THCON_SEC1_REG7_Offset_address` | 140 | 0:16 |  |
| `THCON_SEC1_REG7_Unpack_data_format_cntx0` | 140 | 16:4 | unpack ctx 0 |
| `THCON_SEC1_REG7_Unpack_out_data_format_cntx0` | 140 | 20:4 | unpack ctx 0 |
| `THCON_SEC1_REG7_Unpack_data_format_cntx4` | 140 | 24:4 | unpack ctx 4 |
| `THCON_SEC1_REG7_Unpack_out_data_format_cntx4` | 140 | 28:4 | unpack ctx 4 |
| `THCON_SEC1_REG7_Offset_cntx1_address` | 141 | 0:16 | unpack ctx 1 |
| `THCON_SEC1_REG7_Unpack_data_format_cntx1` | 141 | 16:4 | unpack ctx 1 |
| `THCON_SEC1_REG7_Unpack_out_data_format_cntx1` | 141 | 20:4 | unpack ctx 1 |
| `THCON_SEC1_REG7_Unpack_data_format_cntx5` | 141 | 24:4 | unpack ctx 5 |
| `THCON_SEC1_REG7_Unpack_out_data_format_cntx5` | 141 | 28:4 | unpack ctx 5 |
| `THCON_SEC1_REG7_Offset_cntx2_address` | 142 | 0:16 | unpack ctx 2 |
| `THCON_SEC1_REG7_Unpack_data_format_cntx2` | 142 | 16:4 | unpack ctx 2 |
| `THCON_SEC1_REG7_Unpack_out_data_format_cntx2` | 142 | 20:4 | unpack ctx 2 |
| `THCON_SEC1_REG7_Unpack_data_format_cntx6` | 142 | 24:4 | unpack ctx 6 |
| `THCON_SEC1_REG7_Unpack_out_data_format_cntx6` | 142 | 28:4 | unpack ctx 6 |
| `THCON_SEC1_REG7_Offset_cntx3_address` | 143 | 0:16 | unpack ctx 3 |
| `THCON_SEC1_REG7_Unpack_data_format_cntx3` | 143 | 16:4 | unpack ctx 3 |
| `THCON_SEC1_REG7_Unpack_out_data_format_cntx3` | 143 | 20:4 | unpack ctx 3 |
| `THCON_SEC1_REG7_Unpack_data_format_cntx7` | 143 | 24:4 | unpack ctx 7 |
| `THCON_SEC1_REG7_Unpack_out_data_format_cntx7` | 143 | 28:4 | unpack ctx 7 |
| `THCON_SEC1_REG10_Unpack_limit_address` | 152 | 0:17 |  |
| `THCON_SEC1_REG10_Unpack_fifo_size` | 153 | 0:17 |  |
| `THCON_SEC1_REG10_Unpack_limit_address_en` | 153 | 17:1 |  |
| `THCON_SEC1_REG10_Unpacker_Reg_Wr_Addr` | 154 | 0:24 |  |
| `THCON_SEC1_REG10_Packer_Reg_Wr_Addr` | 155 | 0:24 |  |
| `THCON_SEC1_REG11_Metadata_l1_addr` | 156 | 0:32 |  |
| `THCON_SEC1_REG11_Metadata_limit_addr` | 157 | 0:32 |  |
| `THCON_SEC1_REG11_Metadata_fifo_size` | 158 | 0:32 |  |
| `THCON_SEC1_REG11_Metadata_z_cntr_rst_unpacr_count` | 159 | 0:8 |  |
| `THCON_SEC1_REG11_Metadata_cntxt_switch_unpacr_count` | 159 | 8:8 |  |

## unpack, per thread (ThreadConfig, SETC16): 8 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `UNPACK_MISC_CFG_CfgContextOffset_0` | 41 | 0:4 |  |
| `UNPACK_MISC_CFG_CfgContextCntReset_0` | 41 | 4:1 |  |
| `UNPACK_MISC_CFG_CfgContextCntInc_0` | 41 | 5:1 |  |
| `UNPACK_MISC_CFG_CfgContextOffset_1` | 41 | 8:4 |  |
| `UNPACK_MISC_CFG_CfgContextCntReset_1` | 41 | 12:1 |  |
| `UNPACK_MISC_CFG_CfgContextCntInc_1` | 41 | 13:1 |  |
| `UNPACK_MISC_CFG_CfgContextCntReset_metadata` | 41 | 14:1 |  |
| `UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart` | 41 | 15:1 |  |

## math (Config): 49 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `ALU_FORMAT_SPEC_REG_SrcA_val` | 0 | 0:4 |  |
| `ALU_FORMAT_SPEC_REG_SrcA_override` | 0 | 4:1 |  |
| `ALU_FORMAT_SPEC_REG_SrcB_val` | 0 | 5:4 |  |
| `ALU_FORMAT_SPEC_REG_SrcB_override` | 0 | 9:1 |  |
| `ALU_FORMAT_SPEC_REG_Dstacc_val` | 0 | 10:4 |  |
| `ALU_FORMAT_SPEC_REG_Dstacc_override` | 0 | 14:1 |  |
| `ALU_ROUNDING_MODE_Fpu_srnd_en` | 1 | 0:1 |  |
| `ALU_ROUNDING_MODE_Gasket_srnd_en` | 1 | 1:1 |  |
| `ALU_ROUNDING_MODE_Packer_srnd_en` | 1 | 2:1 |  |
| `ALU_ROUNDING_MODE_Padding` | 1 | 3:10 |  |
| `ALU_ROUNDING_MODE_GS_LF` | 1 | 13:1 |  |
| `ALU_ROUNDING_MODE_Bfp8_HF` | 1 | 14:1 |  |
| `ALU_FORMAT_SPEC_REG0_SrcAUnsigned` | 1 | 15:1 |  |
| `ALU_FORMAT_SPEC_REG0_SrcBUnsigned` | 1 | 16:1 |  |
| `ALU_FORMAT_SPEC_REG0_SrcA` | 1 | 17:4 |  |
| `ALU_FORMAT_SPEC_REG1_SrcB` | 1 | 21:4 |  |
| `ALU_FORMAT_SPEC_REG2_Dstacc` | 1 | 25:4 |  |
| `ALU_ACC_CTRL_Fp32_enabled` | 1 | 29:1 |  |
| `ALU_ACC_CTRL_SFPU_Fp32_enabled` | 1 | 30:1 |  |
| `ALU_ACC_CTRL_INT8_math_enabled` | 1 | 31:1 |  |
| `ALU_ACC_CTRL_Zero_Flag_disabled_src` | 2 | 0:1 |  |
| `ALU_ACC_CTRL_Zero_Flag_disabled_dst` | 2 | 1:1 |  |
| `STACC_RELU_ApplyRelu` | 2 | 2:4 |  |
| `STACC_RELU_ReluThreshold` | 2 | 6:16 |  |
| `DISABLE_RISC_BP_Disable_main` | 2 | 22:1 |  |
| `DISABLE_RISC_BP_Disable_trisc` | 2 | 23:3 |  |
| `DISABLE_RISC_BP_Disable_ncrisc` | 2 | 26:1 |  |
| `DISABLE_RISC_BP_Disable_bmp_clear_main` | 2 | 27:1 |  |
| `DISABLE_RISC_BP_Disable_bmp_clear_trisc` | 2 | 28:3 |  |
| `DISABLE_RISC_BP_Disable_bmp_clear_ncrisc` | 2 | 31:1 |  |
| `ECC_SCRUBBER_Enable` | 3 | 0:1 |  |
| `ECC_SCRUBBER_Scrub_On_Error` | 3 | 1:1 |  |
| `ECC_SCRUBBER_Scrub_On_Error_Immediately` | 3 | 2:1 |  |
| `ECC_SCRUBBER_Delay` | 3 | 3:11 |  |
| `RISC_DEST_ACCESS_CTRL_SEC0_no_swizzle` | 3 | 14:1 |  |
| `RISC_DEST_ACCESS_CTRL_SEC0_unsigned_int` | 3 | 15:1 |  |
| `RISC_DEST_ACCESS_CTRL_SEC0_fmt` | 3 | 16:3 |  |
| `RISC_DEST_ACCESS_CTRL_SEC1_no_swizzle` | 3 | 19:1 |  |
| `RISC_DEST_ACCESS_CTRL_SEC1_unsigned_int` | 3 | 20:1 |  |
| `RISC_DEST_ACCESS_CTRL_SEC1_fmt` | 3 | 21:3 |  |
| `RISC_DEST_ACCESS_CTRL_SEC2_no_swizzle` | 3 | 24:1 |  |
| `RISC_DEST_ACCESS_CTRL_SEC2_unsigned_int` | 3 | 25:1 |  |
| `RISC_DEST_ACCESS_CTRL_SEC2_fmt` | 3 | 26:3 |  |
| `STATE_RESET_EN` | 4 | 0:1 |  |
| `DEST_OFFSET_Enable` | 5 | 0:1 |  |
| `DEST_REGW_BASE_Base` | 6 | 0:16 |  |
| `DEST_SP_BASE_Base` | 7 | 0:16 |  |
| `INT_DESCALE_Enable` | 8 | 0:1 |  |
| `INT_DESCALE_Mode` | 8 | 1:1 |  |

## pack (Config): 175 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `PCK0_ADDR_CTRL_XY_REG_0_Xstride` | 12 | 0:16 |  |
| `PCK0_ADDR_CTRL_XY_REG_0_Ystride` | 12 | 16:16 |  |
| `PCK0_ADDR_CTRL_ZW_REG_0_Zstride` | 13 | 0:16 |  |
| `PCK0_ADDR_CTRL_ZW_REG_0_Wstride` | 13 | 16:16 |  |
| `PCK0_ADDR_CTRL_XY_REG_1_Xstride` | 14 | 0:16 |  |
| `PCK0_ADDR_CTRL_XY_REG_1_Ystride` | 14 | 16:16 |  |
| `PCK0_ADDR_CTRL_ZW_REG_1_Zstride` | 15 | 0:16 |  |
| `PCK0_ADDR_CTRL_ZW_REG_1_Wstride` | 15 | 16:16 |  |
| `PCK0_ADDR_BASE_REG_0_Base` | 16 | 0:18 |  |
| `PCK0_ADDR_BASE_REG_1_Base` | 17 | 0:18 |  |
| `PCK_DEST_RD_CTRL_Read_32b_data` | 18 | 0:1 |  |
| `PCK_DEST_RD_CTRL_Read_unsigned` | 18 | 1:1 |  |
| `PCK_DEST_RD_CTRL_Read_int8` | 18 | 2:1 |  |
| `PCK_DEST_RD_CTRL_Round_10b_mant` | 18 | 3:1 |  |
| `PCK_EDGE_TILE_FACE_SET_SELECT_select` | 19 | 0:8 |  |
| `PCK_EDGE_TILE_FACE_SET_SELECT_enable` | 19 | 8:1 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_0` | 20 | 0:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_1` | 20 | 2:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_2` | 20 | 4:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_3` | 20 | 6:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_4` | 20 | 8:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_5` | 20 | 10:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_6` | 20 | 12:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_7` | 20 | 14:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_8` | 20 | 16:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_9` | 20 | 18:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_10` | 20 | 20:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_11` | 20 | 22:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_12` | 20 | 24:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_13` | 20 | 26:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_14` | 20 | 28:2 |  |
| `TILE_ROW_SET_MAPPING_0_row_set_mapping_15` | 20 | 30:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_0` | 21 | 0:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_1` | 21 | 2:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_2` | 21 | 4:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_3` | 21 | 6:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_4` | 21 | 8:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_5` | 21 | 10:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_6` | 21 | 12:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_7` | 21 | 14:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_8` | 21 | 16:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_9` | 21 | 18:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_10` | 21 | 20:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_11` | 21 | 22:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_12` | 21 | 24:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_13` | 21 | 26:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_14` | 21 | 28:2 |  |
| `TILE_ROW_SET_MAPPING_1_row_set_mapping_15` | 21 | 30:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_0` | 22 | 0:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_1` | 22 | 2:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_2` | 22 | 4:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_3` | 22 | 6:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_4` | 22 | 8:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_5` | 22 | 10:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_6` | 22 | 12:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_7` | 22 | 14:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_8` | 22 | 16:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_9` | 22 | 18:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_10` | 22 | 20:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_11` | 22 | 22:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_12` | 22 | 24:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_13` | 22 | 26:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_14` | 22 | 28:2 |  |
| `TILE_ROW_SET_MAPPING_2_row_set_mapping_15` | 22 | 30:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_0` | 23 | 0:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_1` | 23 | 2:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_2` | 23 | 4:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_3` | 23 | 6:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_4` | 23 | 8:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_5` | 23 | 10:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_6` | 23 | 12:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_7` | 23 | 14:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_8` | 23 | 16:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_9` | 23 | 18:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_10` | 23 | 20:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_11` | 23 | 22:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_12` | 23 | 24:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_13` | 23 | 26:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_14` | 23 | 28:2 |  |
| `TILE_ROW_SET_MAPPING_3_row_set_mapping_15` | 23 | 30:2 |  |
| `PCK_EDGE_OFFSET_SEC0_mask` | 24 | 0:16 |  |
| `PCK_EDGE_MODE_mode` | 24 | 16:1 |  |
| `PCK_EDGE_TILE_ROW_SET_SELECT_select` | 24 | 17:8 |  |
| `PCK_EDGE_OFFSET_SEC1_mask` | 25 | 0:16 |  |
| `PCK_EDGE_OFFSET_SEC2_mask` | 26 | 0:16 |  |
| `PCK_EDGE_OFFSET_SEC3_mask` | 27 | 0:16 |  |
| `PACK_COUNTERS_SEC0_pack_per_xy_plane` | 28 | 0:8 | pack ctx 0 |
| `PACK_COUNTERS_SEC0_pack_reads_per_xy_plane` | 28 | 8:8 | pack ctx 0 |
| `PACK_COUNTERS_SEC0_pack_xys_per_tile` | 28 | 16:7 | pack ctx 0 |
| `PACK_COUNTERS_SEC0_pack_yz_transposed` | 28 | 23:1 | pack ctx 0 |
| `PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt` | 28 | 24:8 | pack ctx 0 |
| `PACK_COUNTERS_SEC1_pack_per_xy_plane` | 29 | 0:8 | pack ctx 1 |
| `PACK_COUNTERS_SEC1_pack_reads_per_xy_plane` | 29 | 8:8 | pack ctx 1 |
| `PACK_COUNTERS_SEC1_pack_xys_per_tile` | 29 | 16:7 | pack ctx 1 |
| `PACK_COUNTERS_SEC1_pack_yz_transposed` | 29 | 23:1 | pack ctx 1 |
| `PACK_COUNTERS_SEC1_auto_ctxt_inc_xys_cnt` | 29 | 24:8 | pack ctx 1 |
| `PACK_COUNTERS_SEC2_pack_per_xy_plane` | 30 | 0:8 | pack ctx 2 |
| `PACK_COUNTERS_SEC2_pack_reads_per_xy_plane` | 30 | 8:8 | pack ctx 2 |
| `PACK_COUNTERS_SEC2_pack_xys_per_tile` | 30 | 16:7 | pack ctx 2 |
| `PACK_COUNTERS_SEC2_pack_yz_transposed` | 30 | 23:1 | pack ctx 2 |
| `PACK_COUNTERS_SEC2_auto_ctxt_inc_xys_cnt` | 30 | 24:8 | pack ctx 2 |
| `PACK_COUNTERS_SEC3_pack_per_xy_plane` | 31 | 0:8 | pack ctx 3 |
| `PACK_COUNTERS_SEC3_pack_reads_per_xy_plane` | 31 | 8:8 | pack ctx 3 |
| `PACK_COUNTERS_SEC3_pack_xys_per_tile` | 31 | 16:7 | pack ctx 3 |
| `PACK_COUNTERS_SEC3_pack_yz_transposed` | 31 | 23:1 | pack ctx 3 |
| `PACK_COUNTERS_SEC3_auto_ctxt_inc_xys_cnt` | 31 | 24:8 | pack ctx 3 |
| `PACK_CONCAT_MASK_SEC0_pack_concat_mask` | 32 | 0:16 | pack ctx 0 |
| `PACK_CONCAT_MASK_SEC1_pack_concat_mask` | 33 | 0:16 | pack ctx 1 |
| `PACK_CONCAT_MASK_SEC2_pack_concat_mask` | 34 | 0:16 | pack ctx 2 |
| `PACK_CONCAT_MASK_SEC3_pack_concat_mask` | 35 | 0:16 | pack ctx 3 |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_0` | 36 | 0:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_1` | 36 | 2:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_2` | 36 | 4:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_3` | 36 | 6:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_4` | 36 | 8:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_5` | 36 | 10:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_6` | 36 | 12:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_7` | 36 | 14:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_8` | 36 | 16:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_9` | 36 | 18:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_10` | 36 | 20:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_11` | 36 | 22:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_12` | 36 | 24:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_13` | 36 | 26:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_14` | 36 | 28:2 |  |
| `TILE_FACE_SET_MAPPING_0_face_set_mapping_15` | 36 | 30:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_0` | 37 | 0:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_1` | 37 | 2:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_2` | 37 | 4:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_3` | 37 | 6:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_4` | 37 | 8:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_5` | 37 | 10:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_6` | 37 | 12:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_7` | 37 | 14:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_8` | 37 | 16:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_9` | 37 | 18:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_10` | 37 | 20:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_11` | 37 | 22:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_12` | 37 | 24:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_13` | 37 | 26:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_14` | 37 | 28:2 |  |
| `TILE_FACE_SET_MAPPING_1_face_set_mapping_15` | 37 | 30:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_0` | 38 | 0:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_1` | 38 | 2:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_2` | 38 | 4:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_3` | 38 | 6:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_4` | 38 | 8:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_5` | 38 | 10:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_6` | 38 | 12:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_7` | 38 | 14:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_8` | 38 | 16:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_9` | 38 | 18:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_10` | 38 | 20:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_11` | 38 | 22:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_12` | 38 | 24:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_13` | 38 | 26:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_14` | 38 | 28:2 |  |
| `TILE_FACE_SET_MAPPING_2_face_set_mapping_15` | 38 | 30:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_0` | 39 | 0:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_1` | 39 | 2:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_2` | 39 | 4:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_3` | 39 | 6:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_4` | 39 | 8:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_5` | 39 | 10:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_6` | 39 | 12:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_7` | 39 | 14:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_8` | 39 | 16:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_9` | 39 | 18:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_10` | 39 | 20:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_11` | 39 | 22:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_12` | 39 | 24:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_13` | 39 | 26:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_14` | 39 | 28:2 |  |
| `TILE_FACE_SET_MAPPING_3_face_set_mapping_15` | 39 | 30:2 |  |
| `PACK_GLOBAL_CFG_CTL_pack_disable_fast_tile_end_drain` | 40 | 0:1 |  |

## pack (Config, THCON): 106 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `THCON_SEC0_REG1_Row_start_section_size` | 68 | 0:16 | pack ctx 0 |
| `THCON_SEC0_REG1_Exp_section_size` | 68 | 16:16 | pack ctx 0 |
| `THCON_SEC0_REG1_L1_Dest_addr` | 69 | 0:32 | pack ctx 0 |
| `THCON_SEC0_REG1_Disable_zero_compress` | 70 | 0:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Add_l1_dest_addr_offset` | 70 | 1:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Disable_pack_zero_flags` | 70 | 2:1 | pack ctx 0 |
| `THCON_SEC0_REG1_ovrd_default_throttle_mode` | 70 | 3:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Out_data_format` | 70 | 4:4 | pack ctx 0 |
| `THCON_SEC0_REG1_In_data_format` | 70 | 8:4 | pack ctx 0 |
| `THCON_SEC0_REG1_Dis_shared_exp_assembler` | 70 | 12:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel` | 70 | 13:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Enable_out_fifo` | 70 | 14:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Sub_l1_tile_header_size` | 70 | 15:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Source_interface_selection` | 70 | 16:1 | pack ctx 0 |
| `THCON_SEC0_REG1_pack_start_intf_pos` | 70 | 17:4 | pack ctx 0 |
| `THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd` | 70 | 21:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Add_tile_header_size` | 70 | 22:1 | pack ctx 0 |
| `THCON_SEC0_REG1_pack_dis_y_pos_start_offset` | 70 | 23:1 | pack ctx 0 |
| `THCON_SEC0_REG1_L1_source_addr` | 70 | 24:8 | pack ctx 0 |
| `THCON_SEC0_REG1_Downsample_mask` | 71 | 0:16 | pack ctx 0 |
| `THCON_SEC0_REG1_Downsample_rate` | 71 | 16:3 | pack ctx 0 |
| `THCON_SEC0_REG1_Pack_L1_Acc` | 71 | 19:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Exp_threshold_en` | 71 | 20:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Unp_LF8_4b_exp` | 71 | 22:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Pac_LF8_4b_exp` | 71 | 23:1 | pack ctx 0 |
| `THCON_SEC0_REG1_Exp_threshold` | 71 | 24:8 | pack ctx 0 |
| `THCON_SEC0_REG8_Row_start_section_size` | 96 | 0:16 | pack ctx 1 |
| `THCON_SEC0_REG8_Exp_section_size` | 96 | 16:16 | pack ctx 1 |
| `THCON_SEC0_REG8_L1_Dest_addr` | 97 | 0:32 | pack ctx 1 |
| `THCON_SEC0_REG8_Disable_zero_compress` | 98 | 0:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Add_l1_dest_addr_offset` | 98 | 1:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Disable_pack_zero_flags` | 98 | 2:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Unused1` | 98 | 3:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Out_data_format` | 98 | 4:4 | pack ctx 1 |
| `THCON_SEC0_REG8_In_data_format` | 98 | 8:4 | pack ctx 1 |
| `THCON_SEC0_REG8_Dis_shared_exp_assembler` | 98 | 12:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Auto_set_last_pacr_intf_sel` | 98 | 13:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Enable_out_fifo` | 98 | 14:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Sub_l1_tile_header_size` | 98 | 15:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Source_interface_selection` | 98 | 16:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Add_tile_header_size` | 98 | 17:1 | pack ctx 1 |
| `THCON_SEC0_REG8_pack_dis_y_pos_start_offset` | 98 | 18:1 | pack ctx 1 |
| `THCON_SEC0_REG8_unpack_tile_offset` | 98 | 19:5 | pack ctx 1 |
| `THCON_SEC0_REG8_L1_source_addr` | 98 | 24:8 | pack ctx 1 |
| `THCON_SEC0_REG8_Downsample_mask` | 99 | 0:16 | pack ctx 1 |
| `THCON_SEC0_REG8_Downsample_rate` | 99 | 16:3 | pack ctx 1 |
| `THCON_SEC0_REG8_Pack_L1_Acc` | 99 | 19:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Exp_threshold_en` | 99 | 20:1 | pack ctx 1 |
| `THCON_SEC0_REG8_Exp_threshold` | 99 | 24:8 | pack ctx 1 |
| `THCON_SEC0_REG9_Pack_0_2_limit_address` | 100 | 0:17 | pack ctx 0/2 |
| `THCON_SEC0_REG9_Pack_0_2_fifo_size` | 101 | 0:17 | pack ctx 0/2 |
| `THCON_SEC0_REG9_Pack_1_3_limit_address` | 102 | 0:17 | pack ctx 1/3 |
| `THCON_SEC0_REG9_Pack_1_3_fifo_size` | 103 | 0:17 | pack ctx 1/3 |
| `THCON_SEC1_REG1_Row_start_section_size` | 116 | 0:16 | pack ctx 2 |
| `THCON_SEC1_REG1_Exp_section_size` | 116 | 16:16 | pack ctx 2 |
| `THCON_SEC1_REG1_L1_Dest_addr` | 117 | 0:32 | pack ctx 2 |
| `THCON_SEC1_REG1_Disable_zero_compress` | 118 | 0:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Add_l1_dest_addr_offset` | 118 | 1:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Disable_pack_zero_flags` | 118 | 2:1 | pack ctx 2 |
| `THCON_SEC1_REG1_ovrd_default_throttle_mode` | 118 | 3:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Out_data_format` | 118 | 4:4 | pack ctx 2 |
| `THCON_SEC1_REG1_In_data_format` | 118 | 8:4 | pack ctx 2 |
| `THCON_SEC1_REG1_Dis_shared_exp_assembler` | 118 | 12:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Auto_set_last_pacr_intf_sel` | 118 | 13:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Enable_out_fifo` | 118 | 14:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Sub_l1_tile_header_size` | 118 | 15:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Source_interface_selection` | 118 | 16:1 | pack ctx 2 |
| `THCON_SEC1_REG1_pack_start_intf_pos` | 118 | 17:4 | pack ctx 2 |
| `THCON_SEC1_REG1_All_pack_disable_zero_compress_ovrd` | 118 | 21:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Add_tile_header_size` | 118 | 22:1 | pack ctx 2 |
| `THCON_SEC1_REG1_pack_dis_y_pos_start_offset` | 118 | 23:1 | pack ctx 2 |
| `THCON_SEC1_REG1_L1_source_addr` | 118 | 24:8 | pack ctx 2 |
| `THCON_SEC1_REG1_Downsample_mask` | 119 | 0:16 | pack ctx 2 |
| `THCON_SEC1_REG1_Downsample_rate` | 119 | 16:3 | pack ctx 2 |
| `THCON_SEC1_REG1_Pack_L1_Acc` | 119 | 19:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Exp_threshold_en` | 119 | 20:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Unp_LF8_4b_exp` | 119 | 22:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Pac_LF8_4b_exp` | 119 | 23:1 | pack ctx 2 |
| `THCON_SEC1_REG1_Exp_threshold` | 119 | 24:8 | pack ctx 2 |
| `THCON_SEC1_REG8_Row_start_section_size` | 144 | 0:16 | pack ctx 3 |
| `THCON_SEC1_REG8_Exp_section_size` | 144 | 16:16 | pack ctx 3 |
| `THCON_SEC1_REG8_L1_Dest_addr` | 145 | 0:32 | pack ctx 3 |
| `THCON_SEC1_REG8_Disable_zero_compress` | 146 | 0:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Add_l1_dest_addr_offset` | 146 | 1:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Disable_pack_zero_flags` | 146 | 2:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Unused1` | 146 | 3:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Out_data_format` | 146 | 4:4 | pack ctx 3 |
| `THCON_SEC1_REG8_In_data_format` | 146 | 8:4 | pack ctx 3 |
| `THCON_SEC1_REG8_Dis_shared_exp_assembler` | 146 | 12:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Auto_set_last_pacr_intf_sel` | 146 | 13:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Enable_out_fifo` | 146 | 14:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Sub_l1_tile_header_size` | 146 | 15:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Source_interface_selection` | 146 | 16:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Add_tile_header_size` | 146 | 17:1 | pack ctx 3 |
| `THCON_SEC1_REG8_pack_dis_y_pos_start_offset` | 146 | 18:1 | pack ctx 3 |
| `THCON_SEC1_REG8_unpack_tile_offset` | 146 | 19:5 | pack ctx 3 |
| `THCON_SEC1_REG8_L1_source_addr` | 146 | 24:8 | pack ctx 3 |
| `THCON_SEC1_REG8_Downsample_mask` | 147 | 0:16 | pack ctx 3 |
| `THCON_SEC1_REG8_Downsample_rate` | 147 | 16:3 | pack ctx 3 |
| `THCON_SEC1_REG8_Pack_L1_Acc` | 147 | 19:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Exp_threshold_en` | 147 | 20:1 | pack ctx 3 |
| `THCON_SEC1_REG8_Exp_threshold` | 147 | 24:8 | pack ctx 3 |
| `THCON_SEC1_REG9_Pack_0_2_limit_address` | 148 | 0:17 | pack ctx 0/2 |
| `THCON_SEC1_REG9_Pack_0_2_fifo_size` | 149 | 0:17 | pack ctx 0/2 |
| `THCON_SEC1_REG9_Pack_1_3_limit_address` | 150 | 0:17 | pack ctx 1/3 |
| `THCON_SEC1_REG9_Pack_1_3_fifo_size` | 151 | 0:17 | pack ctx 1/3 |

## global (Config, both banks): 63 fields

| field | word | bits | context |
| --- | --- | --- | --- |
| `DEST_TARGET_REG_CFG_PACK_SEC0_Offset` | 180 | 0:12 |  |
| `DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset` | 180 | 12:6 |  |
| `DEST_TARGET_REG_CFG_PACK_SEC1_Offset` | 181 | 0:12 |  |
| `DEST_TARGET_REG_CFG_PACK_SEC1_ZOffset` | 181 | 12:6 |  |
| `DEST_TARGET_REG_CFG_PACK_SEC2_Offset` | 182 | 0:12 |  |
| `DEST_TARGET_REG_CFG_PACK_SEC2_ZOffset` | 182 | 12:6 |  |
| `DEST_TARGET_REG_CFG_PACK_SEC3_Offset` | 183 | 0:12 |  |
| `DEST_TARGET_REG_CFG_PACK_SEC3_ZOffset` | 183 | 12:6 |  |
| `CG_SRC_PIPELINE_GateSrcAPipeEn` | 184 | 0:1 |  |
| `CG_SRC_PIPELINE_GateSrcBPipeEn` | 184 | 1:1 |  |
| `RISCV_IC_INVALIDATE_InvalidateAll` | 185 | 0:5 |  |
| `PRNG_SEED_Seed_Val` | 186 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC0_Value` | 187 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC1_Value` | 188 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC2_Value` | 189 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC3_Value` | 190 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC4_Value` | 191 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC5_Value` | 192 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC6_Value` | 193 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC7_Value` | 194 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC8_Value` | 195 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC9_Value` | 196 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC10_Value` | 197 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC11_Value` | 198 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC12_Value` | 199 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC13_Value` | 200 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC14_Value` | 201 | 0:32 |  |
| `INT_DESCALE_VALUES_SEC15_Value` | 202 | 0:32 |  |
| `TRISC_END_PC_SEC0_PC` | 203 | 0:32 |  |
| `TRISC_END_PC_SEC1_PC` | 204 | 0:32 |  |
| `TRISC_END_PC_SEC2_PC` | 205 | 0:32 |  |
| `BRISC_END_PC_PC` | 206 | 0:32 |  |
| `NOC_RISC_END_PC_PC` | 207 | 0:32 |  |
| `RISC_PREFETCH_CTRL_Enable_Trisc` | 208 | 0:3 |  |
| `RISC_PREFETCH_CTRL_Enable_Brisc` | 208 | 3:1 |  |
| `RISC_PREFETCH_CTRL_Enable_NocRisc` | 208 | 4:1 |  |
| `RISC_PREFETCH_CTRL_Max_Req_Count` | 208 | 5:8 |  |
| `SCRATCH_SEC0_val` | 209 | 0:32 |  |
| `SCRATCH_SEC1_val` | 210 | 0:32 |  |
| `SCRATCH_SEC2_val` | 211 | 0:32 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Search_Enable` | 212 | 0:1 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Start_Addr` | 212 | 1:17 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_End_Addr` | 213 | 0:17 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Tag_Value_low` | 214 | 0:32 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Tag_Value_high` | 215 | 0:32 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Tag_Width` | 216 | 0:2 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Valid_bit_section_start_addr` | 216 | 2:17 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Valid_bit_section_end_addr` | 217 | 0:17 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Data_Valid_bit_section_start_addr` | 218 | 0:17 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Data_Valid_chk` | 218 | 17:1 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Data_Valid_offset` | 219 | 0:24 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Tag_inv` | 219 | 24:1 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Tag_inv_all` | 219 | 25:1 |  |
| `L1_CACHE_TAG_SEARCH_ACCEL_Tag_alloc` | 219 | 26:1 |  |
| `DEST_ACCESS_CFG_swizzle_32b` | 220 | 0:1 |  |
| `DEST_ACCESS_CFG_remap_addrs` | 220 | 1:1 |  |
| `DEST_ACCESS_CFG_disable_full_write_dest_q_bypass` | 220 | 2:1 |  |
| `DEST_ACCESS_CFG_zeroacc_absolute_tile_mode` | 220 | 3:1 |  |
| `SRC_ACCESS_CFG_math_view_srca_as_one_bank` | 221 | 0:1 |  |
| `SRC_ACCESS_CFG_math_view_srcb_as_one_bank` | 221 | 1:1 |  |
| `SRC_ACCESS_CFG_disable_contig_srca_dvalid_phase` | 221 | 2:1 |  |
| `SRC_ACCESS_CFG_disable_contig_srcb_dvalid_phase` | 221 | 3:1 |  |
| `CHICKEN_BITS_sfpu_scbd_disable` | 222 | 0:1 |  |

