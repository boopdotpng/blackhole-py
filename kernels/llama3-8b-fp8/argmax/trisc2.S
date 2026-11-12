# llama3 8b-fp8 decode: argmax, trisc2. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_token_history, 0x784=argmax_host_address, 0x788=argmax_count, 0x78c=write_pos, 0x790=write_token, 0xea00=e2e_logits, 0xea04=argmax_start, 0xea08=argmax_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
      4: 8c0a0a13  addi         x20, x20, -1856  # x20 = 0xffb008c0 · riscv_local_mem + 0x8c0
      8: 00010ab7  lui          x21, 0x00010  # x21 = 0x00010000
      c: 080a8a93  addi         x21, x21, 128  # x21 = 0x00010080
     10: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8c0 · 0xffb008c0; write 0x00010080
     14: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     18: 8c4a0a13  addi         x20, x20, -1852  # x20 = 0xffb008c4 · riscv_local_mem + 0x8c4
     1c: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8c4 · 0xffb008c4; write 0x00000000
     20: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
     2c: 8c4c8c93  addi         x25, x25, -1852  # x25 = 0xffb008c4 · riscv_local_mem + 0x8c4
     30: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8c4 · 0xffb008c4
loc_34:
     34: ffb49cb7  lui          x25, 0xffb49  # x25 = 0xffb49000
     38: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb49020
     3c: 000cda83  lhu          x21, 0(x25)  # 0xffb49020
     40: 415a0b33  sub          x22, x20, x21
     44: 010b1b13  slli         x22, x22, 16
     48: 010b5b13  srli         x22, x22, 16
     4c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
     50: 416b8bb3  sub          x23, x23, x22
     54: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
     58: 018bf663  bgeu         x23, x24, 0x00000064  # target 0x00000064
     5c: 0ff0000f  fence        0xf, 0xf
     60: fd5ff06f  jal          x0, 0x00000034  # target 0x00000034
loc_64:
     64: 0ff0000f  fence        0xf, 0xf
     68: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     6c: d600011e  RMWCIB2      Mask=128, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Pac_LF8_4b_exp = 0
     70: d8780006  RMWCIB3      Mask=30, Data=0, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_FORMAT_SPEC_REG2_Dstacc = 0
     74: cff0000a  RMWCIB0      Mask=252, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ApplyRelu = 0; STACC_RELU_ReluThreshold = 0 (masked bits only)
     78: d3fc000a  RMWCIB1      Mask=255, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
     7c: d4fc000a  RMWCIB2      Mask=63, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
     80: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
     84: 110a0a13  addi         x20, x20, 272  # x20 = 0xffef0110 · cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size
     88: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
     8c: 015a2023  sw           x21, 0(x20)  # cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size · 0xffef0110; write 0x00040000; cfg[68] (bank 0); THCON_SEC0_REG1_Row_start_section_size = 0; THCON_SEC0_REG1_Exp_section_size = 4
     90: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
     94: 015a2423  sw           x21, 8(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x00000001; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 0; THCON_SEC0_REG1_In_data_format = 0; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
     98: f35a2c23  sw           x21, -200(x20)  # cfg[18] (bank 0) · PCK_DEST_RD_CTRL_Read_32b_data, PCK_DEST_RD_CTRL_Read_unsigned, PCK_DEST_RD_CTRL_Read_int8, PCK_DEST_RD_CTRL_Round_10b_mant · 0xffef0048; write 0x00000001; cfg[18] (bank 0); PCK_DEST_RD_CTRL_Read_32b_data = 1; PCK_DEST_RD_CTRL_Read_unsigned = 0; PCK_DEST_RD_CTRL_Read_int8 = 0; PCK_DEST_RD_CTRL_Round_10b_mant = 0
     9c: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
     a0: f35a2023  sw           x21, -224(x20)  # cfg[12] (bank 0) · PCK0_ADDR_CTRL_XY_REG_0_Xstride, PCK0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef0030; write 0x00400000; cfg[12] (bank 0); PCK0_ADDR_CTRL_XY_REG_0_Xstride = 0; PCK0_ADDR_CTRL_XY_REG_0_Ystride = 64
     a4: 10000ab7  lui          x21, 0x10000  # x21 = 0x10000000 · CQConfig.PCIE_MID
     a8: 400a8a93  addi         x21, x21, 1024  # x21 = 0x10000400 · arc_csm + 0x400
     ac: f35a2223  sw           x21, -220(x20)  # cfg[13] (bank 0) · PCK0_ADDR_CTRL_ZW_REG_0_Zstride, PCK0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef0034; write 0x10000400; cfg[13] (bank 0); PCK0_ADDR_CTRL_ZW_REG_0_Zstride = 1024; PCK0_ADDR_CTRL_ZW_REG_0_Wstride = 4096
     b0: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     b4: f75a2023  sw           x21, -160(x20)  # cfg[28] (bank 0) · PACK_COUNTERS_SEC0_pack_per_xy_plane, PACK_COUNTERS_SEC0_pack_reads_per_xy_plane, PACK_COUNTERS_SEC0_pack_xys_per_tile, PACK_COUNTERS_SEC0_pack_yz_transposed, PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt · 0xffef0070; write 0x00001000; cfg[28] (bank 0); PACK_COUNTERS_SEC0_pack_per_xy_plane = 0; PACK_COUNTERS_SEC0_pack_reads_per_xy_plane = 16; PACK_COUNTERS_SEC0_pack_xys_per_tile = 0; PACK_COUNTERS_SEC0_pack_yz_transposed = 0; PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt = 0
     b8: 00010ab7  lui          x21, 0x00010  # x21 = 0x00010000
     bc: fffa8a93  addi         x21, x21, -1  # x21 = 0x0000ffff
     c0: f55a2823  sw           x21, -176(x20)  # cfg[24] (bank 0) · PCK_EDGE_OFFSET_SEC0_mask, PCK_EDGE_MODE_mode, PCK_EDGE_TILE_ROW_SET_SELECT_select · 0xffef0060; write 0x0000ffff; cfg[24] (bank 0); PCK_EDGE_OFFSET_SEC0_mask = 65535; PCK_EDGE_MODE_mode = 0; PCK_EDGE_TILE_ROW_SET_SELECT_select = 0
     c4: f40a2a23  sw           x0, -172(x20)  # cfg[25] (bank 0) · PCK_EDGE_OFFSET_SEC1_mask · 0xffef0064; write 0x00000000; cfg[25] (bank 0); PCK_EDGE_OFFSET_SEC1_mask = 0
     c8: f40a2023  sw           x0, -192(x20)  # cfg[20] (bank 0) · TILE_ROW_SET_MAPPING_0_row_set_mapping_0, TILE_ROW_SET_MAPPING_0_row_set_mapping_1, TILE_ROW_SET_MAPPING_0_row_set_mapping_2, TILE_ROW_SET_MAPPING_0_row_set_mapping_3, TILE_ROW_SET_MAPPING_0_row_set_mapping_4, TILE_ROW_SET_MAPPING_0_row_set_mapping_5, TILE_ROW_SET_MAPPING_0_row_set_mapping_6, TILE_ROW_SET_MAPPING_0_row_set_mapping_7, TILE_ROW_SET_MAPPING_0_row_set_mapping_8, TILE_ROW_SET_MAPPING_0_row_set_mapping_9, TILE_ROW_SET_MAPPING_0_row_set_mapping_10, TILE_ROW_SET_MAPPING_0_row_set_mapping_11, TILE_ROW_SET_MAPPING_0_row_set_mapping_12, TILE_ROW_SET_MAPPING_0_row_set_mapping_13, TILE_ROW_SET_MAPPING_0_row_set_mapping_14, TILE_ROW_SET_MAPPING_0_row_set_mapping_15 · 0xffef0050; write 0x00000000; cfg[20] (bank 0); TILE_ROW_SET_MAPPING_0_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_15 = 0
     cc: f40a2223  sw           x0, -188(x20)  # cfg[21] (bank 0) · TILE_ROW_SET_MAPPING_1_row_set_mapping_0, TILE_ROW_SET_MAPPING_1_row_set_mapping_1, TILE_ROW_SET_MAPPING_1_row_set_mapping_2, TILE_ROW_SET_MAPPING_1_row_set_mapping_3, TILE_ROW_SET_MAPPING_1_row_set_mapping_4, TILE_ROW_SET_MAPPING_1_row_set_mapping_5, TILE_ROW_SET_MAPPING_1_row_set_mapping_6, TILE_ROW_SET_MAPPING_1_row_set_mapping_7, TILE_ROW_SET_MAPPING_1_row_set_mapping_8, TILE_ROW_SET_MAPPING_1_row_set_mapping_9, TILE_ROW_SET_MAPPING_1_row_set_mapping_10, TILE_ROW_SET_MAPPING_1_row_set_mapping_11, TILE_ROW_SET_MAPPING_1_row_set_mapping_12, TILE_ROW_SET_MAPPING_1_row_set_mapping_13, TILE_ROW_SET_MAPPING_1_row_set_mapping_14, TILE_ROW_SET_MAPPING_1_row_set_mapping_15 · 0xffef0054; write 0x00000000; cfg[21] (bank 0); TILE_ROW_SET_MAPPING_1_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_15 = 0
     d0: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
     d4: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
     d8: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
     dc: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000100
     e0: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
     e4: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
     e8: c8940412  SETC16       setc16_reg=37, setc16_value=260  # thread_cfg[37] (current thread); ADDR_MOD_PACK_SEC0_YsrcIncr = 4; ADDR_MOD_PACK_SEC0_YsrcCR = 0; ADDR_MOD_PACK_SEC0_YsrcClear = 0; ADDR_MOD_PACK_SEC0_YdstIncr = 4; ADDR_MOD_PACK_SEC0_YdstCR = 0; ADDR_MOD_PACK_SEC0_YdstClear = 0; ADDR_MOD_PACK_SEC0_ZsrcIncr = 0; ADDR_MOD_PACK_SEC0_ZsrcClear = 0; ADDR_MOD_PACK_SEC0_ZdstIncr = 0; ADDR_MOD_PACK_SEC0_ZdstClear = 0
     ec: c898a082  SETC16       setc16_reg=38, setc16_value=10272  # thread_cfg[38] (current thread); ADDR_MOD_PACK_SEC1_YsrcIncr = 0; ADDR_MOD_PACK_SEC1_YsrcCR = 0; ADDR_MOD_PACK_SEC1_YsrcClear = 1; ADDR_MOD_PACK_SEC1_YdstIncr = 0; ADDR_MOD_PACK_SEC1_YdstCR = 0; ADDR_MOD_PACK_SEC1_YdstClear = 1; ADDR_MOD_PACK_SEC1_ZsrcIncr = 0; ADDR_MOD_PACK_SEC1_ZsrcClear = 1; ADDR_MOD_PACK_SEC1_ZdstIncr = 0; ADDR_MOD_PACK_SEC1_ZdstClear = 0
     f0: c89c4482  SETC16       setc16_reg=39, setc16_value=4384  # thread_cfg[39] (current thread); ADDR_MOD_PACK_SEC2_YsrcIncr = 0; ADDR_MOD_PACK_SEC2_YsrcCR = 0; ADDR_MOD_PACK_SEC2_YsrcClear = 1; ADDR_MOD_PACK_SEC2_YdstIncr = 4; ADDR_MOD_PACK_SEC2_YdstCR = 0; ADDR_MOD_PACK_SEC2_YdstClear = 0; ADDR_MOD_PACK_SEC2_ZsrcIncr = 1; ADDR_MOD_PACK_SEC2_ZsrcClear = 0; ADDR_MOD_PACK_SEC2_ZdstIncr = 0; ADDR_MOD_PACK_SEC2_ZdstClear = 0
     f4: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
     f8: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
     fc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    100: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    104: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    108: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    10c: 01507033  and          x0, x0, x21
    110: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    114: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    118: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    11c: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    120: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    124: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    128: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    12c: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    130: 41000ab7  lui          x21, 0x41000  # x21 = 0x41000000
    134: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x41000000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    138: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    13c: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    140: 41008ab7  lui          x21, 0x41008  # x21 = 0x41008000
    144: 001a8a93  addi         x21, x21, 1  # x21 = 0x41008001
    148: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x41008001; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=1, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1
    14c: 41010ab7  lui          x21, 0x41010  # x21 = 0x41010000
    150: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x41010000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=2, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    154: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    158: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    15c: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    160: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    164: 01507033  and          x0, x0, x21
    168: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    16c: 8c0b8b93  addi         x23, x23, -1856  # x23 = 0xffb008c0 · riscv_local_mem + 0x8c0
    170: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8c0 · 0xffb008c0
    174: 004a5a13  srli         x20, x20, 4
    178: fffa0a13  addi         x20, x20, -1
    17c: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    180: 01fbebb3  or           x23, x23, x31  # x23 = 0x508c0000
    184: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    188: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write 0x508c0000; MMIO instruction · SETADC CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=0
    18c: 008a1c13  slli         x24, x20, 8
    190: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    194: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    198: 019c7c33  and          x24, x24, x25
    19c: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    1a0: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    1a4: 01ac6c33  or           x24, x24, x26
    1a8: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    1ac: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    1b0: 010a5a93  srli         x21, x20, 16
    1b4: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    1b8: 015b6b33  or           x22, x22, x21
    1bc: 008b1c13  slli         x24, x22, 8
    1c0: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    1c4: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    1c8: 019c7c33  and          x24, x24, x25
    1cc: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    1d0: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    1d4: 01ac6c33  or           x24, x24, x26
    1d8: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    1dc: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    1e0: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    1e4: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    1e8: 008a9c13  slli         x24, x21, 8
    1ec: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    1f0: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    1f4: 019c7c33  and          x24, x24, x25
    1f8: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    1fc: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    200: 01ac6c33  or           x24, x24, x26
    204: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    208: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    20c: 80000001  DMANOP
    210: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    214: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    218: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    21c: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    220: 00000a93  addi         x21, x0, 0  # x21 = 0x00000000
    224: 015a2023  sw           x21, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    228: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    22c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    230: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    234: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    238: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    23c: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    240: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    244: 01507033  and          x0, x0, x21
    248: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    24c: 8c0c0c13  addi         x24, x24, -1856  # x24 = 0xffb008c0 · riscv_local_mem + 0x8c0
    250: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8c0 · 0xffb008c0
    254: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    258: 015a0a33  add          x20, x20, x21
    25c: 00011b37  lui          x22, 0x00011  # x22 = 0x00011000
    260: 080b0b13  addi         x22, x22, 128  # x22 = 0x00011080
    264: 016a6663  bltu         x20, x22, 0x00000270  # target 0x00000270
    268: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    26c: 417a0a33  sub          x20, x20, x23
loc_270:
    270: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    274: 8c0c0c13  addi         x24, x24, -1856  # x24 = 0xffb008c0 · riscv_local_mem + 0x8c0
    278: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8c0 · 0xffb008c0; write runtime value
    27c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    280: 8c4a8a93  addi         x21, x21, -1852  # x21 = 0xffb008c4 · riscv_local_mem + 0x8c4
    284: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8c4 · 0xffb008c4
    288: 001a0a13  addi         x20, x20, 1
    28c: 010a1a13  slli         x20, x20, 16
    290: 010a5a13  srli         x20, x20, 16
    294: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    298: 8c4a8a93  addi         x21, x21, -1852  # x21 = 0xffb008c4 · riscv_local_mem + 0x8c4
    29c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8c4 · 0xffb008c4; write runtime value
    2a0: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    2a4: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb49028
    2a8: 014aa023  sw           x20, 0(x21)  # 0xffb49028; write runtime value
    2ac: 0ff0000f  fence        0xf, 0xf
    2b0: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    2b4: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    2b8:           j FW_TRISC2+4   # return to firmware, linked at install
