# llama3 8b-fp8 decode: attention, trisc2. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
      4: 8c0a0a13  addi         x20, x20, -1856  # x20 = 0xffb008c0 · riscv_local_mem + 0x8c0
      8: 00025ab7  lui          x21, 0x00025  # x21 = 0x00025000
      c: 880a8a93  addi         x21, x21, -1920  # x21 = 0x00024880
     10: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8c0 · 0xffb008c0; write 0x00024880
     14: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     18: 8c4a0a13  addi         x20, x20, -1852  # x20 = 0xffb008c4 · riscv_local_mem + 0x8c4
     1c: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8c4 · 0xffb008c4; write 0x00000000
     20: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     24: 8c8a0a13  addi         x20, x20, -1848  # x20 = 0xffb008c8 · riscv_local_mem + 0x8c8
     28: 0001cab7  lui          x21, 0x0001c  # x21 = 0x0001c000
     2c: 080a8a93  addi         x21, x21, 128  # x21 = 0x0001c080
     30: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8c8 · 0xffb008c8; write 0x0001c080
     34: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     38: 8cca0a13  addi         x20, x20, -1844  # x20 = 0xffb008cc · riscv_local_mem + 0x8cc
     3c: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8cc · 0xffb008cc; write 0x00000000
     40: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     44: 8d0a0a13  addi         x20, x20, -1840  # x20 = 0xffb008d0 · riscv_local_mem + 0x8d0
     48: 0001dab7  lui          x21, 0x0001d  # x21 = 0x0001d000
     4c: 880a8a93  addi         x21, x21, -1920  # x21 = 0x0001c880
     50: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8d0 · 0xffb008d0; write 0x0001c880
     54: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     58: 8d4a0a13  addi         x20, x20, -1836  # x20 = 0xffb008d4 · riscv_local_mem + 0x8d4
     5c: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8d4 · 0xffb008d4; write 0x00000000
     60: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     64: 8d8a0a13  addi         x20, x20, -1832  # x20 = 0xffb008d8 · riscv_local_mem + 0x8d8
     68: 00056ab7  lui          x21, 0x00056  # x21 = 0x00056000
     6c: 980a8a93  addi         x21, x21, -1664  # x21 = 0x00055980
     70: 015a2023  sw           x21, 0(x20)  # riscv_local_mem + 0x8d8 · 0xffb008d8; write 0x00055980
     74: ffb01a37  lui          x20, 0xffb01  # x20 = 0xffb01000
     78: 8dca0a13  addi         x20, x20, -1828  # x20 = 0xffb008dc · riscv_local_mem + 0x8dc
     7c: 000a2023  sw           x0, 0(x20)  # riscv_local_mem + 0x8dc · 0xffb008dc; write 0x00000000
     80: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     84: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
     88: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
     8c: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     90: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     94: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     98: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     9c: 0063fa63  bgeu         x7, x6, 0x000000b0  # target 0x000000b0
     a0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     a4: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
     a8: 0063f463  bgeu         x7, x6, 0x000000b0  # target 0x000000b0
     ac: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_b0:
     b0: 62527863  bgeu         x4, x5, 0x000006e0  # target 0x000006e0
     b4: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
     b8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     bc: d600011e  RMWCIB2      Mask=128, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Pac_LF8_4b_exp = 0
     c0: d8780006  RMWCIB3      Mask=30, Data=0, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_FORMAT_SPEC_REG2_Dstacc = 0
     c4: cff0000a  RMWCIB0      Mask=252, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ApplyRelu = 0; STACC_RELU_ReluThreshold = 0 (masked bits only)
     c8: d3fc000a  RMWCIB1      Mask=255, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
     cc: d4fc000a  RMWCIB2      Mask=63, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
     d0: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
     d4: 110a0a13  addi         x20, x20, 272  # x20 = 0xffef0110 · cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size
     d8: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
     dc: 015a2023  sw           x21, 0(x20)  # cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size · 0xffef0110; write 0x00040000; cfg[68] (bank 0); THCON_SEC0_REG1_Row_start_section_size = 0; THCON_SEC0_REG1_Exp_section_size = 4
     e0: 05100a93  addi         x21, x0, 81  # x21 = 0x00000051
     e4: 015a2423  sw           x21, 8(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x00000051; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 5; THCON_SEC0_REG1_In_data_format = 0; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
     e8: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
     ec: f35a2c23  sw           x21, -200(x20)  # cfg[18] (bank 0) · PCK_DEST_RD_CTRL_Read_32b_data, PCK_DEST_RD_CTRL_Read_unsigned, PCK_DEST_RD_CTRL_Read_int8, PCK_DEST_RD_CTRL_Round_10b_mant · 0xffef0048; write 0x00000001; cfg[18] (bank 0); PCK_DEST_RD_CTRL_Read_32b_data = 1; PCK_DEST_RD_CTRL_Read_unsigned = 0; PCK_DEST_RD_CTRL_Read_int8 = 0; PCK_DEST_RD_CTRL_Round_10b_mant = 0
     f0: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
     f4: f35a2023  sw           x21, -224(x20)  # cfg[12] (bank 0) · PCK0_ADDR_CTRL_XY_REG_0_Xstride, PCK0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef0030; write 0x00400000; cfg[12] (bank 0); PCK0_ADDR_CTRL_XY_REG_0_Xstride = 0; PCK0_ADDR_CTRL_XY_REG_0_Ystride = 64
     f8: 10000ab7  lui          x21, 0x10000  # x21 = 0x10000000 · CQConfig.PCIE_MID
     fc: 400a8a93  addi         x21, x21, 1024  # x21 = 0x10000400 · arc_csm + 0x400
    100: f35a2223  sw           x21, -220(x20)  # cfg[13] (bank 0) · PCK0_ADDR_CTRL_ZW_REG_0_Zstride, PCK0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef0034; write 0x10000400; cfg[13] (bank 0); PCK0_ADDR_CTRL_ZW_REG_0_Zstride = 1024; PCK0_ADDR_CTRL_ZW_REG_0_Wstride = 4096
    104: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    108: f75a2023  sw           x21, -160(x20)  # cfg[28] (bank 0) · PACK_COUNTERS_SEC0_pack_per_xy_plane, PACK_COUNTERS_SEC0_pack_reads_per_xy_plane, PACK_COUNTERS_SEC0_pack_xys_per_tile, PACK_COUNTERS_SEC0_pack_yz_transposed, PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt · 0xffef0070; write 0x00001000; cfg[28] (bank 0); PACK_COUNTERS_SEC0_pack_per_xy_plane = 0; PACK_COUNTERS_SEC0_pack_reads_per_xy_plane = 16; PACK_COUNTERS_SEC0_pack_xys_per_tile = 0; PACK_COUNTERS_SEC0_pack_yz_transposed = 0; PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt = 0
    10c: 00010ab7  lui          x21, 0x00010  # x21 = 0x00010000
    110: fffa8a93  addi         x21, x21, -1  # x21 = 0x0000ffff
    114: f55a2823  sw           x21, -176(x20)  # cfg[24] (bank 0) · PCK_EDGE_OFFSET_SEC0_mask, PCK_EDGE_MODE_mode, PCK_EDGE_TILE_ROW_SET_SELECT_select · 0xffef0060; write 0x0000ffff; cfg[24] (bank 0); PCK_EDGE_OFFSET_SEC0_mask = 65535; PCK_EDGE_MODE_mode = 0; PCK_EDGE_TILE_ROW_SET_SELECT_select = 0
    118: f40a2a23  sw           x0, -172(x20)  # cfg[25] (bank 0) · PCK_EDGE_OFFSET_SEC1_mask · 0xffef0064; write 0x00000000; cfg[25] (bank 0); PCK_EDGE_OFFSET_SEC1_mask = 0
    11c: f40a2023  sw           x0, -192(x20)  # cfg[20] (bank 0) · TILE_ROW_SET_MAPPING_0_row_set_mapping_0, TILE_ROW_SET_MAPPING_0_row_set_mapping_1, TILE_ROW_SET_MAPPING_0_row_set_mapping_2, TILE_ROW_SET_MAPPING_0_row_set_mapping_3, TILE_ROW_SET_MAPPING_0_row_set_mapping_4, TILE_ROW_SET_MAPPING_0_row_set_mapping_5, TILE_ROW_SET_MAPPING_0_row_set_mapping_6, TILE_ROW_SET_MAPPING_0_row_set_mapping_7, TILE_ROW_SET_MAPPING_0_row_set_mapping_8, TILE_ROW_SET_MAPPING_0_row_set_mapping_9, TILE_ROW_SET_MAPPING_0_row_set_mapping_10, TILE_ROW_SET_MAPPING_0_row_set_mapping_11, TILE_ROW_SET_MAPPING_0_row_set_mapping_12, TILE_ROW_SET_MAPPING_0_row_set_mapping_13, TILE_ROW_SET_MAPPING_0_row_set_mapping_14, TILE_ROW_SET_MAPPING_0_row_set_mapping_15 · 0xffef0050; write 0x00000000; cfg[20] (bank 0); TILE_ROW_SET_MAPPING_0_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_15 = 0
    120: f40a2223  sw           x0, -188(x20)  # cfg[21] (bank 0) · TILE_ROW_SET_MAPPING_1_row_set_mapping_0, TILE_ROW_SET_MAPPING_1_row_set_mapping_1, TILE_ROW_SET_MAPPING_1_row_set_mapping_2, TILE_ROW_SET_MAPPING_1_row_set_mapping_3, TILE_ROW_SET_MAPPING_1_row_set_mapping_4, TILE_ROW_SET_MAPPING_1_row_set_mapping_5, TILE_ROW_SET_MAPPING_1_row_set_mapping_6, TILE_ROW_SET_MAPPING_1_row_set_mapping_7, TILE_ROW_SET_MAPPING_1_row_set_mapping_8, TILE_ROW_SET_MAPPING_1_row_set_mapping_9, TILE_ROW_SET_MAPPING_1_row_set_mapping_10, TILE_ROW_SET_MAPPING_1_row_set_mapping_11, TILE_ROW_SET_MAPPING_1_row_set_mapping_12, TILE_ROW_SET_MAPPING_1_row_set_mapping_13, TILE_ROW_SET_MAPPING_1_row_set_mapping_14, TILE_ROW_SET_MAPPING_1_row_set_mapping_15 · 0xffef0054; write 0x00000000; cfg[21] (bank 0); TILE_ROW_SET_MAPPING_1_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_15 = 0
    124: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
    128: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
    12c: 08000a93  addi         x21, x0, 128  # x21 = 0x00000080
    130: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000080
    134: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    138: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
    13c: c8940412  SETC16       setc16_reg=37, setc16_value=260  # thread_cfg[37] (current thread); ADDR_MOD_PACK_SEC0_YsrcIncr = 4; ADDR_MOD_PACK_SEC0_YsrcCR = 0; ADDR_MOD_PACK_SEC0_YsrcClear = 0; ADDR_MOD_PACK_SEC0_YdstIncr = 4; ADDR_MOD_PACK_SEC0_YdstCR = 0; ADDR_MOD_PACK_SEC0_YdstClear = 0; ADDR_MOD_PACK_SEC0_ZsrcIncr = 0; ADDR_MOD_PACK_SEC0_ZsrcClear = 0; ADDR_MOD_PACK_SEC0_ZdstIncr = 0; ADDR_MOD_PACK_SEC0_ZdstClear = 0
    140: c898a082  SETC16       setc16_reg=38, setc16_value=10272  # thread_cfg[38] (current thread); ADDR_MOD_PACK_SEC1_YsrcIncr = 0; ADDR_MOD_PACK_SEC1_YsrcCR = 0; ADDR_MOD_PACK_SEC1_YsrcClear = 1; ADDR_MOD_PACK_SEC1_YdstIncr = 0; ADDR_MOD_PACK_SEC1_YdstCR = 0; ADDR_MOD_PACK_SEC1_YdstClear = 1; ADDR_MOD_PACK_SEC1_ZsrcIncr = 0; ADDR_MOD_PACK_SEC1_ZsrcClear = 1; ADDR_MOD_PACK_SEC1_ZdstIncr = 0; ADDR_MOD_PACK_SEC1_ZdstClear = 0
    144: c89c4482  SETC16       setc16_reg=39, setc16_value=4384  # thread_cfg[39] (current thread); ADDR_MOD_PACK_SEC2_YsrcIncr = 0; ADDR_MOD_PACK_SEC2_YsrcCR = 0; ADDR_MOD_PACK_SEC2_YsrcClear = 1; ADDR_MOD_PACK_SEC2_YdstIncr = 4; ADDR_MOD_PACK_SEC2_YdstCR = 0; ADDR_MOD_PACK_SEC2_YdstClear = 0; ADDR_MOD_PACK_SEC2_ZsrcIncr = 1; ADDR_MOD_PACK_SEC2_ZsrcClear = 0; ADDR_MOD_PACK_SEC2_ZdstIncr = 0; ADDR_MOD_PACK_SEC2_ZdstClear = 0
    148: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
    14c: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    150: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    154: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    158: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    15c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    160: 01507033  and          x0, x0, x21
    164: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    168: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    16c: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    170: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    174: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    178: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    17c: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    180: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    184: 41000ab7  lui          x21, 0x41000  # x21 = 0x41000000
    188: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x41000000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    18c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    190: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    194: 41008ab7  lui          x21, 0x41008  # x21 = 0x41008000
    198: 001a8a93  addi         x21, x21, 1  # x21 = 0x41008001
    19c: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x41008001; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=1, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1
    1a0: 41010ab7  lui          x21, 0x41010  # x21 = 0x41010000
    1a4: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x41010000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=2, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    1a8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    1ac: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    1b0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    1b4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    1b8: 01507033  and          x0, x0, x21
    1bc: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    1c0: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
    1c4: 8c4c8c93  addi         x25, x25, -1852  # x25 = 0xffb008c4 · riscv_local_mem + 0x8c4
    1c8: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8c4 · 0xffb008c4
loc_1cc:
    1cc: ffb4ecb7  lui          x25, 0xffb4e  # x25 = 0xffb4e000
    1d0: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb4e020
    1d4: 000cda83  lhu          x21, 0(x25)  # 0xffb4e020
    1d8: 415a0b33  sub          x22, x20, x21
    1dc: 010b1b13  slli         x22, x22, 16
    1e0: 010b5b13  srli         x22, x22, 16
    1e4: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
    1e8: 416b8bb3  sub          x23, x23, x22
    1ec: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    1f0: 018bf663  bgeu         x23, x24, 0x000001fc  # target 0x000001fc
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: fd5ff06f  jal          x0, 0x000001cc  # target 0x000001cc
loc_1fc:
    1fc: 0ff0000f  fence        0xf, 0xf
    200: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    204: 8c0b8b93  addi         x23, x23, -1856  # x23 = 0xffb008c0 · riscv_local_mem + 0x8c0
    208: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8c0 · 0xffb008c0
    20c: 004a5a13  srli         x20, x20, 4
    210: fffa0a13  addi         x20, x20, -1
    214: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    218: 01fbebb3  or           x23, x23, x31  # x23 = 0x508c0000
    21c: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    220: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write 0x508c0000; MMIO instruction · SETADC CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=0
    224: 008a1c13  slli         x24, x20, 8
    228: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    22c: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    230: 019c7c33  and          x24, x24, x25
    234: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    238: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    23c: 01ac6c33  or           x24, x24, x26
    240: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    244: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    248: 010a5a93  srli         x21, x20, 16
    24c: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    250: 015b6b33  or           x22, x22, x21
    254: 008b1c13  slli         x24, x22, 8
    258: 019c7c33  and          x24, x24, x25
    25c: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    260: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    264: 01ac6c33  or           x24, x24, x26
    268: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    26c: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    270: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    274: 008a9c13  slli         x24, x21, 8
    278: 019c7c33  and          x24, x24, x25
    27c: 01ac6c33  or           x24, x24, x26
    280: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    284: 80000001  DMANOP
    288: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    28c: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    290: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    294: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    298: 000a2023  sw           x0, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    29c: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    2a0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2a4: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    2a8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    2ac: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    2b0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    2b4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    2b8: 01507033  and          x0, x0, x21
    2bc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    2c0: 8c0c0c13  addi         x24, x24, -1856  # x24 = 0xffb008c0 · riscv_local_mem + 0x8c0
    2c4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8c0 · 0xffb008c0
    2c8: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2cc: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    2d0: 015a0a33  add          x20, x20, x21
    2d4: 00025b37  lui          x22, 0x00025  # x22 = 0x00025000
    2d8: 080b0b13  addi         x22, x22, 128  # x22 = 0x00025080
    2dc: 016a6863  bltu         x20, x22, 0x000002ec  # target 0x000002ec
    2e0: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2e4: 800b8b93  addi         x23, x23, -2048  # x23 = 0x00000800
    2e8: 417a0a33  sub          x20, x20, x23
loc_2ec:
    2ec: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    2f0: 8c0c0c13  addi         x24, x24, -1856  # x24 = 0xffb008c0 · riscv_local_mem + 0x8c0
    2f4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8c0 · 0xffb008c0; write runtime value
    2f8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    2fc: 8c4a8a93  addi         x21, x21, -1852  # x21 = 0xffb008c4 · riscv_local_mem + 0x8c4
    300: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8c4 · 0xffb008c4
    304: 001a0a13  addi         x20, x20, 1
    308: 010a1a13  slli         x20, x20, 16
    30c: 010a5a13  srli         x20, x20, 16
    310: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8c4 · 0xffb008c4; write runtime value
    314: ffb4eab7  lui          x21, 0xffb4e  # x21 = 0xffb4e000
    318: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb4e028
    31c: 014aa023  sw           x20, 0(x21)  # 0xffb4e028; write runtime value
    320: 0ff0000f  fence        0xf, 0xf
    324: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    328: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    32c: 79000293  addi         x5, x0, 1936  # x5 = 0x00000790
    330: 0002a203  lw           x4, 0(x5)  # param kv_blocks; 0x00000790
    334: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    338: 90438393  addi         x7, x7, -1788  # x7 = 0x00011904
    33c: 0003a283  lw           x5, 0(x7)  # param attention_phase; 0x00011904
    340: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    344: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    348: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    34c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    350: 00747a63  bgeu         x8, x7, 0x00000364  # target 0x00000364
    354: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    358: 05000413  addi         x8, x0, 80  # x8 = 0x00000050
    35c: 00747463  bgeu         x8, x7, 0x00000364  # target 0x00000364
    360: 00800313  addi         x6, x0, 8  # x6 = 0x00000008
loc_364:
    364: 00620233  add          x4, x4, x6
    368: fff20213  addi         x4, x4, -1
    36c: 40520233  sub          x4, x4, x5
    370: 02625233  divu         x4, x4, x6
    374: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    378: 00020313  addi         x6, x4, 0
loc_37c:
    37c: 1a62f263  bgeu         x5, x6, 0x00000520  # target 0x00000520
    380: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
    384: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    388: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
    38c: 8ccc8c93  addi         x25, x25, -1844  # x25 = 0xffb008cc · riscv_local_mem + 0x8cc
    390: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8cc · 0xffb008cc
loc_394:
    394: ffb4bcb7  lui          x25, 0xffb4b  # x25 = 0xffb4b000
    398: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb4b020
    39c: 000cda83  lhu          x21, 0(x25)  # 0xffb4b020
    3a0: 415a0b33  sub          x22, x20, x21
    3a4: 010b1b13  slli         x22, x22, 16
    3a8: 010b5b13  srli         x22, x22, 16
    3ac: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
    3b0: 416b8bb3  sub          x23, x23, x22
    3b4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3b8: 018bf663  bgeu         x23, x24, 0x000003c4  # target 0x000003c4
    3bc: 0ff0000f  fence        0xf, 0xf
    3c0: fd5ff06f  jal          x0, 0x00000394  # target 0x00000394
loc_3c4:
    3c4: 0ff0000f  fence        0xf, 0xf
    3c8: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
    3cc: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
    3d0: 08000a93  addi         x21, x0, 128  # x21 = 0x00000080
    3d4: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000080
    3d8: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    3dc: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
    3e0: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
    3e4: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    3e8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3ec: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    3f0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    3f4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    3f8: 01507033  and          x0, x0, x21
    3fc: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    400: 8c8b8b93  addi         x23, x23, -1848  # x23 = 0xffb008c8 · riscv_local_mem + 0x8c8
    404: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8c8 · 0xffb008c8
    408: 004a5a13  srli         x20, x20, 4
    40c: fffa0a13  addi         x20, x20, -1
    410: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    414: 01fbebb3  or           x23, x23, x31  # x23 = 0x508c0000
    418: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    41c: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write 0x508c0000; MMIO instruction · SETADC CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=0
    420: 008a1c13  slli         x24, x20, 8
    424: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    428: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    42c: 019c7c33  and          x24, x24, x25
    430: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    434: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    438: 01ac6c33  or           x24, x24, x26
    43c: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    440: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    444: 010a5a93  srli         x21, x20, 16
    448: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    44c: 015b6b33  or           x22, x22, x21
    450: 008b1c13  slli         x24, x22, 8
    454: 019c7c33  and          x24, x24, x25
    458: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    45c: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    460: 01ac6c33  or           x24, x24, x26
    464: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    468: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    46c: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    470: 008a9c13  slli         x24, x21, 8
    474: 019c7c33  and          x24, x24, x25
    478: 01ac6c33  or           x24, x24, x26
    47c: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    480: 80000001  DMANOP
    484: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    488: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    48c: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    490: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    494: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    498: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    49c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    4a0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    4a4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    4a8: 01507033  and          x0, x0, x21
    4ac: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    4b0: 8c8c0c13  addi         x24, x24, -1848  # x24 = 0xffb008c8 · riscv_local_mem + 0x8c8
    4b4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8c8 · 0xffb008c8
    4b8: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4bc: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    4c0: 015a0a33  add          x20, x20, x21
    4c4: 0001db37  lui          x22, 0x0001d  # x22 = 0x0001d000
    4c8: 880b0b13  addi         x22, x22, -1920  # x22 = 0x0001c880
    4cc: 016a6863  bltu         x20, x22, 0x000004dc  # target 0x000004dc
    4d0: 00001bb7  lui          x23, 0x00001  # x23 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4d4: 800b8b93  addi         x23, x23, -2048  # x23 = 0x00000800
    4d8: 417a0a33  sub          x20, x20, x23
loc_4dc:
    4dc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    4e0: 8c8c0c13  addi         x24, x24, -1848  # x24 = 0xffb008c8 · riscv_local_mem + 0x8c8
    4e4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8c8 · 0xffb008c8; write runtime value
    4e8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    4ec: 8cca8a93  addi         x21, x21, -1844  # x21 = 0xffb008cc · riscv_local_mem + 0x8cc
    4f0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8cc · 0xffb008cc
    4f4: 001a0a13  addi         x20, x20, 1
    4f8: 010a1a13  slli         x20, x20, 16
    4fc: 010a5a13  srli         x20, x20, 16
    500: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8cc · 0xffb008cc; write runtime value
    504: ffb4bab7  lui          x21, 0xffb4b  # x21 = 0xffb4b000
    508: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb4b028
    50c: 014aa023  sw           x20, 0(x21)  # 0xffb4b028; write runtime value
    510: 0ff0000f  fence        0xf, 0xf
    514: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    518: 00128293  addi         x5, x5, 1
    51c: e61ff06f  jal          x0, 0x0000037c  # target 0x0000037c
loc_520:
    520: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
    524: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    528: 118a0a13  addi         x20, x20, 280  # x20 = 0xffef0118 · cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr
    52c: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    530: 015a2023  sw           x21, 0(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x00000001; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 0; THCON_SEC0_REG1_In_data_format = 0; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
    534: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
    538: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
    53c: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
    540: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000100
    544: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    548: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
    54c: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
    550: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    554: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    558: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    55c: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    560: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    564: 01507033  and          x0, x0, x21
    568: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    56c: 178000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x00000570
    570: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    574: 170000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x00000578
    578: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    57c: 168000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x00000580
    580: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
    584: 160000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x00000588
    588: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
    58c: 158000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x00000590
    590: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
    594: 150000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x00000598
    598: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    59c: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
    5a0: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    5a4: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    5a8: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    5ac: 12021a63  bne          x4, x0, 0x000006e0  # target 0x000006e0
    5b0: 98020026  SEMWAIT      stall_res=1, sem_sel=2, wait_sem_cond=1  # stall_res: Stall.TDMA; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_ZERO
    5b4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    5b8: d600011e  RMWCIB2      Mask=128, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Pac_LF8_4b_exp = 0
    5bc: d8780006  RMWCIB3      Mask=30, Data=0, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_FORMAT_SPEC_REG2_Dstacc = 0
    5c0: cff0000a  RMWCIB0      Mask=252, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ApplyRelu = 0; STACC_RELU_ReluThreshold = 0 (masked bits only)
    5c4: d3fc000a  RMWCIB1      Mask=255, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
    5c8: d4fc000a  RMWCIB2      Mask=63, Data=0, CfgRegAddr=2  # cfg[2] (current thread StateID); STACC_RELU_ReluThreshold = 0 (masked bits only)
    5cc: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    5d0: 110a0a13  addi         x20, x20, 272  # x20 = 0xffef0110 · cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size
    5d4: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    5d8: 015a2023  sw           x21, 0(x20)  # cfg[68] (bank 0) · THCON_SEC0_REG1_Row_start_section_size, THCON_SEC0_REG1_Exp_section_size · 0xffef0110; write 0x00040000; cfg[68] (bank 0); THCON_SEC0_REG1_Row_start_section_size = 0; THCON_SEC0_REG1_Exp_section_size = 4
    5dc: 05100a93  addi         x21, x0, 81  # x21 = 0x00000051
    5e0: 015a2423  sw           x21, 8(x20)  # cfg[70] (bank 0) · THCON_SEC0_REG1_Disable_zero_compress, THCON_SEC0_REG1_Add_l1_dest_addr_offset, THCON_SEC0_REG1_Disable_pack_zero_flags, THCON_SEC0_REG1_ovrd_default_throttle_mode, THCON_SEC0_REG1_Out_data_format, THCON_SEC0_REG1_In_data_format, THCON_SEC0_REG1_Dis_shared_exp_assembler, THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel, THCON_SEC0_REG1_Enable_out_fifo, THCON_SEC0_REG1_Sub_l1_tile_header_size, THCON_SEC0_REG1_Source_interface_selection, THCON_SEC0_REG1_pack_start_intf_pos, THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd, THCON_SEC0_REG1_Add_tile_header_size, THCON_SEC0_REG1_pack_dis_y_pos_start_offset, THCON_SEC0_REG1_L1_source_addr · 0xffef0118; write 0x00000051; cfg[70] (bank 0); THCON_SEC0_REG1_Disable_zero_compress = 1; THCON_SEC0_REG1_Add_l1_dest_addr_offset = 0; THCON_SEC0_REG1_Disable_pack_zero_flags = 0; THCON_SEC0_REG1_ovrd_default_throttle_mode = 0; THCON_SEC0_REG1_Out_data_format = 5; THCON_SEC0_REG1_In_data_format = 0; THCON_SEC0_REG1_Dis_shared_exp_assembler = 0; THCON_SEC0_REG1_Auto_set_last_pacr_intf_sel = 0; THCON_SEC0_REG1_Enable_out_fifo = 0; THCON_SEC0_REG1_Sub_l1_tile_header_size = 0; THCON_SEC0_REG1_Source_interface_selection = 0; THCON_SEC0_REG1_pack_start_intf_pos = 0; THCON_SEC0_REG1_All_pack_disable_zero_compress_ovrd = 0; THCON_SEC0_REG1_Add_tile_header_size = 0; THCON_SEC0_REG1_pack_dis_y_pos_start_offset = 0; THCON_SEC0_REG1_L1_source_addr = 0
    5e4: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    5e8: f35a2c23  sw           x21, -200(x20)  # cfg[18] (bank 0) · PCK_DEST_RD_CTRL_Read_32b_data, PCK_DEST_RD_CTRL_Read_unsigned, PCK_DEST_RD_CTRL_Read_int8, PCK_DEST_RD_CTRL_Round_10b_mant · 0xffef0048; write 0x00000001; cfg[18] (bank 0); PCK_DEST_RD_CTRL_Read_32b_data = 1; PCK_DEST_RD_CTRL_Read_unsigned = 0; PCK_DEST_RD_CTRL_Read_int8 = 0; PCK_DEST_RD_CTRL_Round_10b_mant = 0
    5ec: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    5f0: f35a2023  sw           x21, -224(x20)  # cfg[12] (bank 0) · PCK0_ADDR_CTRL_XY_REG_0_Xstride, PCK0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef0030; write 0x00400000; cfg[12] (bank 0); PCK0_ADDR_CTRL_XY_REG_0_Xstride = 0; PCK0_ADDR_CTRL_XY_REG_0_Ystride = 64
    5f4: 10000ab7  lui          x21, 0x10000  # x21 = 0x10000000 · CQConfig.PCIE_MID
    5f8: 400a8a93  addi         x21, x21, 1024  # x21 = 0x10000400 · arc_csm + 0x400
    5fc: f35a2223  sw           x21, -220(x20)  # cfg[13] (bank 0) · PCK0_ADDR_CTRL_ZW_REG_0_Zstride, PCK0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef0034; write 0x10000400; cfg[13] (bank 0); PCK0_ADDR_CTRL_ZW_REG_0_Zstride = 1024; PCK0_ADDR_CTRL_ZW_REG_0_Wstride = 4096
    600: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    604: f75a2023  sw           x21, -160(x20)  # cfg[28] (bank 0) · PACK_COUNTERS_SEC0_pack_per_xy_plane, PACK_COUNTERS_SEC0_pack_reads_per_xy_plane, PACK_COUNTERS_SEC0_pack_xys_per_tile, PACK_COUNTERS_SEC0_pack_yz_transposed, PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt · 0xffef0070; write 0x00001000; cfg[28] (bank 0); PACK_COUNTERS_SEC0_pack_per_xy_plane = 0; PACK_COUNTERS_SEC0_pack_reads_per_xy_plane = 16; PACK_COUNTERS_SEC0_pack_xys_per_tile = 0; PACK_COUNTERS_SEC0_pack_yz_transposed = 0; PACK_COUNTERS_SEC0_auto_ctxt_inc_xys_cnt = 0
    608: 00010ab7  lui          x21, 0x00010  # x21 = 0x00010000
    60c: fffa8a93  addi         x21, x21, -1  # x21 = 0x0000ffff
    610: f55a2823  sw           x21, -176(x20)  # cfg[24] (bank 0) · PCK_EDGE_OFFSET_SEC0_mask, PCK_EDGE_MODE_mode, PCK_EDGE_TILE_ROW_SET_SELECT_select · 0xffef0060; write 0x0000ffff; cfg[24] (bank 0); PCK_EDGE_OFFSET_SEC0_mask = 65535; PCK_EDGE_MODE_mode = 0; PCK_EDGE_TILE_ROW_SET_SELECT_select = 0
    614: f40a2a23  sw           x0, -172(x20)  # cfg[25] (bank 0) · PCK_EDGE_OFFSET_SEC1_mask · 0xffef0064; write 0x00000000; cfg[25] (bank 0); PCK_EDGE_OFFSET_SEC1_mask = 0
    618: f40a2023  sw           x0, -192(x20)  # cfg[20] (bank 0) · TILE_ROW_SET_MAPPING_0_row_set_mapping_0, TILE_ROW_SET_MAPPING_0_row_set_mapping_1, TILE_ROW_SET_MAPPING_0_row_set_mapping_2, TILE_ROW_SET_MAPPING_0_row_set_mapping_3, TILE_ROW_SET_MAPPING_0_row_set_mapping_4, TILE_ROW_SET_MAPPING_0_row_set_mapping_5, TILE_ROW_SET_MAPPING_0_row_set_mapping_6, TILE_ROW_SET_MAPPING_0_row_set_mapping_7, TILE_ROW_SET_MAPPING_0_row_set_mapping_8, TILE_ROW_SET_MAPPING_0_row_set_mapping_9, TILE_ROW_SET_MAPPING_0_row_set_mapping_10, TILE_ROW_SET_MAPPING_0_row_set_mapping_11, TILE_ROW_SET_MAPPING_0_row_set_mapping_12, TILE_ROW_SET_MAPPING_0_row_set_mapping_13, TILE_ROW_SET_MAPPING_0_row_set_mapping_14, TILE_ROW_SET_MAPPING_0_row_set_mapping_15 · 0xffef0050; write 0x00000000; cfg[20] (bank 0); TILE_ROW_SET_MAPPING_0_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_0_row_set_mapping_15 = 0
    61c: f40a2223  sw           x0, -188(x20)  # cfg[21] (bank 0) · TILE_ROW_SET_MAPPING_1_row_set_mapping_0, TILE_ROW_SET_MAPPING_1_row_set_mapping_1, TILE_ROW_SET_MAPPING_1_row_set_mapping_2, TILE_ROW_SET_MAPPING_1_row_set_mapping_3, TILE_ROW_SET_MAPPING_1_row_set_mapping_4, TILE_ROW_SET_MAPPING_1_row_set_mapping_5, TILE_ROW_SET_MAPPING_1_row_set_mapping_6, TILE_ROW_SET_MAPPING_1_row_set_mapping_7, TILE_ROW_SET_MAPPING_1_row_set_mapping_8, TILE_ROW_SET_MAPPING_1_row_set_mapping_9, TILE_ROW_SET_MAPPING_1_row_set_mapping_10, TILE_ROW_SET_MAPPING_1_row_set_mapping_11, TILE_ROW_SET_MAPPING_1_row_set_mapping_12, TILE_ROW_SET_MAPPING_1_row_set_mapping_13, TILE_ROW_SET_MAPPING_1_row_set_mapping_14, TILE_ROW_SET_MAPPING_1_row_set_mapping_15 · 0xffef0054; write 0x00000000; cfg[21] (bank 0); TILE_ROW_SET_MAPPING_1_row_set_mapping_0 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_1 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_2 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_3 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_4 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_5 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_6 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_7 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_8 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_9 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_10 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_11 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_12 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_13 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_14 = 0; TILE_ROW_SET_MAPPING_1_row_set_mapping_15 = 0
    620: ffe00a37  lui          x20, 0xffe00  # x20 = 0xffe00000 · TensixMMIO.REGFILE_BASE
    624: 040a0a13  addi         x20, x20, 64  # x20 = 0xffe00040 · tensix_regfile + 0x40
    628: 08000a93  addi         x21, x0, 128  # x21 = 0x00000080
    62c: 015a2023  sw           x21, 0(x20)  # tensix_regfile + 0x40 · 0xffe00040; write 0x00000080
    630: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    634: 095a2823  sw           x21, 144(x20)  # tensix_regfile + 0xd0 · 0xffe000d0; write 0x00040000
    638: c8940412  SETC16       setc16_reg=37, setc16_value=260  # thread_cfg[37] (current thread); ADDR_MOD_PACK_SEC0_YsrcIncr = 4; ADDR_MOD_PACK_SEC0_YsrcCR = 0; ADDR_MOD_PACK_SEC0_YsrcClear = 0; ADDR_MOD_PACK_SEC0_YdstIncr = 4; ADDR_MOD_PACK_SEC0_YdstCR = 0; ADDR_MOD_PACK_SEC0_YdstClear = 0; ADDR_MOD_PACK_SEC0_ZsrcIncr = 0; ADDR_MOD_PACK_SEC0_ZsrcClear = 0; ADDR_MOD_PACK_SEC0_ZdstIncr = 0; ADDR_MOD_PACK_SEC0_ZdstClear = 0
    63c: c898a082  SETC16       setc16_reg=38, setc16_value=10272  # thread_cfg[38] (current thread); ADDR_MOD_PACK_SEC1_YsrcIncr = 0; ADDR_MOD_PACK_SEC1_YsrcCR = 0; ADDR_MOD_PACK_SEC1_YsrcClear = 1; ADDR_MOD_PACK_SEC1_YdstIncr = 0; ADDR_MOD_PACK_SEC1_YdstCR = 0; ADDR_MOD_PACK_SEC1_YdstClear = 1; ADDR_MOD_PACK_SEC1_ZsrcIncr = 0; ADDR_MOD_PACK_SEC1_ZsrcClear = 1; ADDR_MOD_PACK_SEC1_ZdstIncr = 0; ADDR_MOD_PACK_SEC1_ZdstClear = 0
    640: c89c4482  SETC16       setc16_reg=39, setc16_value=4384  # thread_cfg[39] (current thread); ADDR_MOD_PACK_SEC2_YsrcIncr = 0; ADDR_MOD_PACK_SEC2_YsrcCR = 0; ADDR_MOD_PACK_SEC2_YsrcClear = 1; ADDR_MOD_PACK_SEC2_YdstIncr = 4; ADDR_MOD_PACK_SEC2_YdstCR = 0; ADDR_MOD_PACK_SEC2_YdstClear = 0; ADDR_MOD_PACK_SEC2_ZsrcIncr = 1; ADDR_MOD_PACK_SEC2_ZsrcClear = 0; ADDR_MOD_PACK_SEC2_ZdstIncr = 0; ADDR_MOD_PACK_SEC2_ZdstClear = 0
    644: 4600002d  SETADCXY     CntSetMask=4, Ch1_Y=0, Ch1_X=0, Ch0_Y=0, Ch0_X=0, BitMask=11
    648: 5200003d  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    64c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    650: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    654: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    658: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    65c: 01507033  and          x0, x0, x21
    660: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    664: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    668: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    66c: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    670: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    674: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    678: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    67c: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    680: 41000ab7  lui          x21, 0x41000  # x21 = 0x41000000
    684: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x41000000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=0, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    688: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    68c: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    690: 41008ab7  lui          x21, 0x41008  # x21 = 0x41008000
    694: 001a8a93  addi         x21, x21, 1  # x21 = 0x41008001
    698: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x41008001; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=1, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=1
    69c: 41010ab7  lui          x21, 0x41010  # x21 = 0x41010000
    6a0: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x41010000; MOP template instruction · PACR CfgContext=0, RowPadZero=0, DstAccessMode=0, AddrMode=2, AddrCntContext=0, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=0, Concat=0, CtxtCtrl=0, Flush=0, Last=0
    6a4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    6a8: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    6ac: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    6b0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    6b4: 01507033  and          x0, x0, x21
    6b8: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    6bc: 188000ef  jal          x1, 0x00000844  # target 0x00000844; x1 = 0x000006c0
    6c0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    6c4: 180000ef  jal          x1, 0x00000844  # target 0x00000844; x1 = 0x000006c8
    6c8: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    6cc: 178000ef  jal          x1, 0x00000844  # target 0x00000844; x1 = 0x000006d0
    6d0: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    6d4: 170000ef  jal          x1, 0x00000844  # target 0x00000844; x1 = 0x000006d8
    6d8: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    6dc: 94000022  SEMGET       sem_sel=2  # sem_sel: Sem.MATH_PACK
loc_6e0:
    6e0: 2c80006f  jal          x0, 0x000009a8  # target 0x000009a8
loc_6e4:
    6e4: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
    6e8: 8d4c8c93  addi         x25, x25, -1836  # x25 = 0xffb008d4 · riscv_local_mem + 0x8d4
    6ec: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8d4 · 0xffb008d4
loc_6f0:
    6f0: ffb4ccb7  lui          x25, 0xffb4c  # x25 = 0xffb4c000
    6f4: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb4c020
    6f8: 000cda83  lhu          x21, 0(x25)  # 0xffb4c020
    6fc: 415a0b33  sub          x22, x20, x21
    700: 010b1b13  slli         x22, x22, 16
    704: 010b5b13  srli         x22, x22, 16
    708: 00600b93  addi         x23, x0, 6  # x23 = 0x00000006
    70c: 416b8bb3  sub          x23, x23, x22
    710: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    714: 018bf663  bgeu         x23, x24, 0x00000720  # target 0x00000720
    718: 0ff0000f  fence        0xf, 0xf
    71c: fd5ff06f  jal          x0, 0x000006f0  # target 0x000006f0
loc_720:
    720: 0ff0000f  fence        0xf, 0xf
    724: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    728: 8d0b8b93  addi         x23, x23, -1840  # x23 = 0xffb008d0 · riscv_local_mem + 0x8d0
    72c: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8d0 · 0xffb008d0
    730: 004a5a13  srli         x20, x20, 4
    734: fffa0a13  addi         x20, x20, -1
    738: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    73c: 01fbebb3  or           x23, x23, x31
    740: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    744: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    748: 008a1c13  slli         x24, x20, 8
    74c: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    750: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    754: 019c7c33  and          x24, x24, x25
    758: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    75c: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    760: 01ac6c33  or           x24, x24, x26
    764: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    768: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    76c: 010a5a93  srli         x21, x20, 16
    770: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    774: 015b6b33  or           x22, x22, x21
    778: 008b1c13  slli         x24, x22, 8
    77c: 019c7c33  and          x24, x24, x25
    780: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    784: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    788: 01ac6c33  or           x24, x24, x26
    78c: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    790: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    794: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    798: 008a9c13  slli         x24, x21, 8
    79c: 019c7c33  and          x24, x24, x25
    7a0: 01ac6c33  or           x24, x24, x26
    7a4: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    7a8: 80000001  DMANOP
    7ac: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    7b0: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    7b4: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    7b8: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    7bc: 000a2023  sw           x0, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    7c0: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    7c4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    7c8: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    7cc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    7d0: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    7d4: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    7d8: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    7dc: 01507033  and          x0, x0, x21
    7e0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    7e4: 8d0c0c13  addi         x24, x24, -1840  # x24 = 0xffb008d0 · riscv_local_mem + 0x8d0
    7e8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8d0 · 0xffb008d0
    7ec: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7f0: 015a0a33  add          x20, x20, x21
    7f4: 00023b37  lui          x22, 0x00023  # x22 = 0x00023000
    7f8: 880b0b13  addi         x22, x22, -1920  # x22 = 0x00022880
    7fc: 016a6663  bltu         x20, x22, 0x00000808  # target 0x00000808
    800: 00006bb7  lui          x23, 0x00006  # x23 = 0x00006000
    804: 417a0a33  sub          x20, x20, x23
loc_808:
    808: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    80c: 8d0c0c13  addi         x24, x24, -1840  # x24 = 0xffb008d0 · riscv_local_mem + 0x8d0
    810: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8d0 · 0xffb008d0; write runtime value
    814: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    818: 8d4a8a93  addi         x21, x21, -1836  # x21 = 0xffb008d4 · riscv_local_mem + 0x8d4
    81c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8d4 · 0xffb008d4
    820: 001a0a13  addi         x20, x20, 1
    824: 010a1a13  slli         x20, x20, 16
    828: 010a5a13  srli         x20, x20, 16
    82c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8d4 · 0xffb008d4; write runtime value
    830: ffb4cab7  lui          x21, 0xffb4c  # x21 = 0xffb4c000
    834: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb4c028
    838: 014aa023  sw           x20, 0(x21)  # 0xffb4c028; write runtime value
    83c: 0ff0000f  fence        0xf, 0xf
    840: 00008067  jalr         x0, 0(x1)
loc_844:
    844: ffb01cb7  lui          x25, 0xffb01  # x25 = 0xffb01000
    848: 8dcc8c93  addi         x25, x25, -1828  # x25 = 0xffb008dc · riscv_local_mem + 0x8dc
    84c: 000caa03  lw           x20, 0(x25)  # riscv_local_mem + 0x8dc · 0xffb008dc
loc_850:
    850: ffb51cb7  lui          x25, 0xffb51  # x25 = 0xffb51000
    854: 020c8c93  addi         x25, x25, 32  # x25 = 0xffb51020
    858: 000cda83  lhu          x21, 0(x25)  # 0xffb51020
    85c: 415a0b33  sub          x22, x20, x21
    860: 010b1b13  slli         x22, x22, 16
    864: 010b5b13  srli         x22, x22, 16
    868: 00400b93  addi         x23, x0, 4  # x23 = 0x00000004
    86c: 416b8bb3  sub          x23, x23, x22
    870: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    874: 018bf663  bgeu         x23, x24, 0x00000880  # target 0x00000880
    878: 0ff0000f  fence        0xf, 0xf
    87c: fd5ff06f  jal          x0, 0x00000850  # target 0x00000850
loc_880:
    880: 0ff0000f  fence        0xf, 0xf
    884: ffb01bb7  lui          x23, 0xffb01  # x23 = 0xffb01000
    888: 8d8b8b93  addi         x23, x23, -1832  # x23 = 0xffb008d8 · riscv_local_mem + 0x8d8
    88c: 000baa03  lw           x20, 0(x23)  # riscv_local_mem + 0x8d8 · 0xffb008d8
    890: 004a5a13  srli         x20, x20, 4
    894: fffa0a13  addi         x20, x20, -1
    898: 508c0bb7  lui          x23, 0x508c0  # x23 = 0x508c0000
    89c: 01fbebb3  or           x23, x23, x31
    8a0: ffe40c37  lui          x24, 0xffe40  # x24 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    8a4: 017c2023  sw           x23, 0(x24)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    8a8: 008a1c13  slli         x24, x20, 8
    8ac: 01000cb7  lui          x25, 0x01000  # x25 = 0x01000000
    8b0: f00c8c93  addi         x25, x25, -256  # x25 = 0x00ffff00
    8b4: 019c7c33  and          x24, x24, x25
    8b8: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    8bc: 018d0d13  addi         x26, x26, 24  # x26 = 0x45000018
    8c0: 01ac6c33  or           x24, x24, x26
    8c4: ffe40db7  lui          x27, 0xffe40  # x27 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    8c8: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    8cc: 010a5a93  srli         x21, x20, 16
    8d0: 00008b37  lui          x22, 0x00008  # x22 = 0x00008000
    8d4: 015b6b33  or           x22, x22, x21
    8d8: 008b1c13  slli         x24, x22, 8
    8dc: 019c7c33  and          x24, x24, x25
    8e0: 45000d37  lui          x26, 0x45000  # x26 = 0x45000000
    8e4: 019d0d13  addi         x26, x26, 25  # x26 = 0x45000019
    8e8: 01ac6c33  or           x24, x24, x26
    8ec: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    8f0: 89000026  STALLWAIT    stall_res=128, wait_res=9  # stall_res: Stall.CFG; wait_res: Wait.THCON | Wait.PACK0
    8f4: c0300116  WRCFG        GprAddress=12, wr128b=0, CfgReg=69  # cfg[69] (current thread StateID); THCON_SEC0_REG1_L1_Dest_addr = runtime
    8f8: 008a9c13  slli         x24, x21, 8
    8fc: 019c7c33  and          x24, x24, x25
    900: 01ac6c33  or           x24, x24, x26
    904: 018da023  sw           x24, 0(x27)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    908: 80000001  DMANOP
    90c: 7a00f001  SETADCXX     CntSetMask=4, x_end2=15, x_start=0
    910: 52000015  SETADCZW     CntSetMask=4, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=5
    914: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    918: 2d0a0a13  addi         x20, x20, 720  # x20 = 0xffef02d0 · cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset
    91c: 000a2023  sw           x0, 0(x20)  # cfg[180] (bank 0) · DEST_TARGET_REG_CFG_PACK_SEC0_Offset, DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset · 0xffef02d0; write 0x00000000; cfg[180] (bank 0); DEST_TARGET_REG_CFG_PACK_SEC0_Offset = 0; DEST_TARGET_REG_CFG_PACK_SEC0_ZOffset = 0
    920: 89000022  STALLWAIT    stall_res=128, wait_res=8  # stall_res: Stall.CFG; wait_res: Wait.PACK0
    924: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    928: 88040022  STALLWAIT    stall_res=2, wait_res=8  # stall_res: Stall.SYNC; wait_res: Wait.PACK0
    92c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    930: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    934: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    938: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    93c: 01507033  and          x0, x0, x21
    940: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    944: 8d8c0c13  addi         x24, x24, -1832  # x24 = 0xffb008d8 · riscv_local_mem + 0x8d8
    948: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x8d8 · 0xffb008d8
    94c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    950: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    954: 015a0a33  add          x20, x20, x21
    958: 00058b37  lui          x22, 0x00058  # x22 = 0x00058000 · arc_apb_niu1 + 0x0
    95c: 980b0b13  addi         x22, x22, -1664  # x22 = 0x00057980
    960: 016a6663  bltu         x20, x22, 0x0000096c  # target 0x0000096c
    964: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    968: 417a0a33  sub          x20, x20, x23
loc_96c:
    96c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    970: 8d8c0c13  addi         x24, x24, -1832  # x24 = 0xffb008d8 · riscv_local_mem + 0x8d8
    974: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x8d8 · 0xffb008d8; write runtime value
    978: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    97c: 8dca8a93  addi         x21, x21, -1828  # x21 = 0xffb008dc · riscv_local_mem + 0x8dc
    980: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x8dc · 0xffb008dc
    984: 001a0a13  addi         x20, x20, 1
    988: 010a1a13  slli         x20, x20, 16
    98c: 010a5a13  srli         x20, x20, 16
    990: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x8dc · 0xffb008dc; write runtime value
    994: ffb51ab7  lui          x21, 0xffb51  # x21 = 0xffb51000
    998: 028a8a93  addi         x21, x21, 40  # x21 = 0xffb51028
    99c: 014aa023  sw           x20, 0(x21)  # 0xffb51028; write runtime value
    9a0: 0ff0000f  fence        0xf, 0xf
    9a4: 00008067  jalr         x0, 0(x1)
    9a8:           j FW_TRISC2+4   # return to firmware, linked at install
