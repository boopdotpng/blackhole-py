# llama3 1b decode: attention, trisc0. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
      4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
      8: 0001cb37  lui          x22, 0x0001c  # x22 = 0x0001c000
      c: 800b0b13  addi         x22, x22, -2048  # x22 = 0x0001b800
     10: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820; write 0x0001b800
     14: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     18: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
     1c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write 0x00000000
     20: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     24: 82828293  addi         x5, x5, -2008  # x5 = 0xffb00828 · riscv_local_mem + 0x828
     28: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     2c: 0062a023  sw           x6, 0(x5)  # riscv_local_mem + 0x828 · 0xffb00828; write 0x00012000
     30: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     34: 82c28293  addi         x5, x5, -2004  # x5 = 0xffb0082c · riscv_local_mem + 0x82c
     38: 0002a023  sw           x0, 0(x5)  # riscv_local_mem + 0x82c · 0xffb0082c; write 0x00000000
     3c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     40: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
     44: 00013b37  lui          x22, 0x00013  # x22 = 0x00013000
     48: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830; write 0x00013000
     4c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     50: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
     54: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write 0x00000000
     58: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     5c: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
     60: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
     64: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838; write 0x00015000
     68: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     6c: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
     70: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write 0x00000000
     74: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     78: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
     7c: 00017b37  lui          x22, 0x00017  # x22 = 0x00017000
     80: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840; write 0x00017000
     84: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     88: 844a8a93  addi         x21, x21, -1980  # x21 = 0xffb00844 · riscv_local_mem + 0x844
     8c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x844 · 0xffb00844; write 0x00000000
     90: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     94: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
     98: 0001fb37  lui          x22, 0x0001f  # x22 = 0x0001f000
     9c: 880b0b13  addi         x22, x22, -1920  # x22 = 0x0001e880
     a0: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848; write 0x0001e880
     a4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     a8: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
     ac: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write 0x00000000
     b0: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
     b4: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
     b8: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     bc: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     c0: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     c4: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     c8: 0063fa63  bgeu         x7, x6, 0x000000dc  # target 0x000000dc
     cc: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     d0: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
     d4: 0063f463  bgeu         x7, x6, 0x000000dc  # target 0x000000dc
     d8: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_dc:
     dc: 7e527263  bgeu         x4, x5, 0x000008c0  # target 0x000008c0
     e0: 7e4000ef  jal          x1, 0x000008c4  # target 0x000008c4; x1 = 0x000000e4
     e4: 7e0000ef  jal          x1, 0x000008c4  # target 0x000008c4; x1 = 0x000000e8
     e8: 7dc000ef  jal          x1, 0x000008c4  # target 0x000008c4; x1 = 0x000000ec
     ec: 7d8000ef  jal          x1, 0x000008c4  # target 0x000008c4; x1 = 0x000000f0
     f0: 79000293  addi         x5, x0, 1936  # x5 = 0x00000790
     f4: 0002a203  lw           x4, 0(x5)  # param kv_blocks; 0x00000790
     f8: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     fc: 90438393  addi         x7, x7, -1788  # x7 = 0x00011904
    100: 0003a283  lw           x5, 0(x7)  # param attention_phase; 0x00011904
    104: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    108: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    10c: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    110: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    114: 00747a63  bgeu         x8, x7, 0x00000128  # target 0x00000128
    118: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    11c: 05000413  addi         x8, x0, 80  # x8 = 0x00000050
    120: 00747463  bgeu         x8, x7, 0x00000128  # target 0x00000128
    124: 00800313  addi         x6, x0, 8  # x6 = 0x00000008
loc_128:
    128: 00620233  add          x4, x4, x6
    12c: fff20213  addi         x4, x4, -1
    130: 40520233  sub          x4, x4, x5
    134: 02625233  divu         x4, x4, x6
    138: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    13c: 82c48493  addi         x9, x9, -2004  # x9 = 0xffb0082c · riscv_local_mem + 0x82c
    140: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x82c · 0xffb0082c
    144: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
loc_148:
    148: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    14c: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    150: 0004d303  lhu          x6, 0(x9)  # 0xffb48028
    154: 405303b3  sub          x7, x6, x5
    158: 01039393  slli         x7, x7, 16
    15c: 0103d393  srli         x7, x7, 16
    160: 0083f663  bgeu         x7, x8, 0x0000016c  # target 0x0000016c
    164: 0ff0000f  fence        0xf, 0xf
    168: fe1ff06f  jal          x0, 0x00000148  # target 0x00000148
loc_16c:
    16c: 0ff0000f  fence        0xf, 0xf
    170: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    174: 00020313  addi         x6, x4, 0
loc_178:
    178: 4462f863  bgeu         x5, x6, 0x000005c8  # target 0x000005c8
    17c: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    180: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_184:
    184: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    188: 0fe47413  andi         x8, x8, 254
    18c: 00040663  beq          x8, x0, 0x00000198  # target 0x00000198
    190: 0ff0000f  fence        0xf, 0xf
    194: ff1ff06f  jal          x0, 0x00000184  # target 0x00000184
loc_198:
    198: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    19c: 12038393  addi         x7, x7, 288  # x7 = 0xffef0120 · cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3
    1a0: 12500413  addi         x8, x0, 293  # x8 = 0x00000125
    1a4: 0083a023  sw           x8, 0(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000125; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 1; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    1a8: d50001de  RMWCIB2      Mask=64, Data=0, CfgRegAddr=119  # cfg[119] (current thread StateID); THCON_SEC1_REG1_Unp_LF8_4b_exp = 0
    1ac: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    1b0: 1c038393  addi         x7, x7, 448  # x7 = 0xffef01c0 · cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor
    1b4: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    1b8: 01540413  addi         x8, x8, 21  # x8 = 0x01000015
    1bc: 0083a023  sw           x8, 0(x7)  # cfg[112] (bank 0) · THCON_SEC1_REG0_TileDescriptor · 0xffef01c0; write 0x01000015; cfg[112] (bank 0); THCON_SEC1_REG0_TileDescriptor = 16777237
    1c0: 00040437  lui          x8, 0x00040  # x8 = 0x00040000
    1c4: 00140413  addi         x8, x8, 1  # x8 = 0x00040001
    1c8: 0083a223  sw           x8, 4(x7)  # cfg[113] (bank 0) (undocumented index) · 0xffef01c4; write 0x00040001; cfg[113] (bank 0) · fields not in ttsim
    1cc: 0003a423  sw           x0, 8(x7)  # cfg[114] (bank 0) (undocumented index) · 0xffef01c8; write 0x00000000; cfg[114] (bank 0) · fields not in ttsim
    1d0: 0003a623  sw           x0, 12(x7)  # cfg[115] (bank 0) (undocumented index) · 0xffef01cc; write 0x00000000; cfg[115] (bank 0) · fields not in ttsim
    1d4: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    1d8: 0283a023  sw           x8, 32(x7)  # cfg[120] (bank 0) · THCON_SEC1_REG2_Out_data_format, THCON_SEC1_REG2_Throttle_mode, THCON_SEC1_REG2_Context_count, THCON_SEC1_REG2_Haloize_mode, THCON_SEC1_REG2_Tileize_mode, THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC1_REG2_Unpack_If_Sel, THCON_SEC1_REG2_Upsample_rate, THCON_SEC1_REG2_Ovrd_data_format, THCON_SEC1_REG2_Upsample_and_interleave, THCON_SEC1_REG2_Shift_amount_cntx0, THCON_SEC1_REG2_Shift_amount_cntx1, THCON_SEC1_REG2_Shift_amount_cntx2, THCON_SEC1_REG2_Shift_amount_cntx3 · 0xffef01e0; write 0x00000025; cfg[120] (bank 0); THCON_SEC1_REG2_Out_data_format = 5; THCON_SEC1_REG2_Throttle_mode = 2; THCON_SEC1_REG2_Context_count = 0; THCON_SEC1_REG2_Haloize_mode = 0; THCON_SEC1_REG2_Tileize_mode = 0; THCON_SEC1_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC1_REG2_Unpack_If_Sel = 0; THCON_SEC1_REG2_Upsample_rate = 0; THCON_SEC1_REG2_Ovrd_data_format = 0; THCON_SEC1_REG2_Upsample_and_interleave = 0; THCON_SEC1_REG2_Shift_amount_cntx0 = 0; THCON_SEC1_REG2_Shift_amount_cntx1 = 0; THCON_SEC1_REG2_Shift_amount_cntx2 = 0; THCON_SEC1_REG2_Shift_amount_cntx3 = 0
    1dc: 00300413  addi         x8, x0, 3  # x8 = 0x00000003
    1e0: 0283a223  sw           x8, 36(x7)  # cfg[121] (bank 0) · THCON_SEC1_REG2_Disable_zero_compress_cntx0, THCON_SEC1_REG2_Disable_zero_compress_cntx1, THCON_SEC1_REG2_Disable_zero_compress_cntx2, THCON_SEC1_REG2_Disable_zero_compress_cntx3, THCON_SEC1_REG2_Unpack_if_sel_cntx0, THCON_SEC1_REG2_Unpack_if_sel_cntx1, THCON_SEC1_REG2_Unpack_if_sel_cntx2, THCON_SEC1_REG2_Unpack_if_sel_cntx3, THCON_SEC1_REG2_Force_shared_exp, THCON_SEC1_REG2_Context_count_non_log2, THCON_SEC1_REG2_Context_count_non_log2_en, THCON_SEC1_REG2_Disable_zero_compress_cntx4, THCON_SEC1_REG2_Disable_zero_compress_cntx5, THCON_SEC1_REG2_Disable_zero_compress_cntx6, THCON_SEC1_REG2_Disable_zero_compress_cntx7, THCON_SEC1_REG2_Unpack_if_sel_cntx4, THCON_SEC1_REG2_Unpack_if_sel_cntx5, THCON_SEC1_REG2_Unpack_if_sel_cntx6, THCON_SEC1_REG2_Unpack_if_sel_cntx7, THCON_SEC1_REG2_Metadata_x_end · 0xffef01e4; write 0x00000003; cfg[121] (bank 0); THCON_SEC1_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC1_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC1_REG2_Force_shared_exp = 0; THCON_SEC1_REG2_Context_count_non_log2 = 0; THCON_SEC1_REG2_Context_count_non_log2_en = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC1_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC1_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC1_REG2_Metadata_x_end = 0
    1e4: 0203a423  sw           x0, 40(x7)  # cfg[122] (bank 0) · THCON_SEC1_REG2_Unpack_limit_address · 0xffef01e8; write 0x00000000; cfg[122] (bank 0); THCON_SEC1_REG2_Unpack_limit_address = 0
    1e8: 0203a623  sw           x0, 44(x7)  # cfg[123] (bank 0) · THCON_SEC1_REG2_Unpack_fifo_size · 0xffef01ec; write 0x00000000; cfg[123] (bank 0); THCON_SEC1_REG2_Unpack_fifo_size = 0
    1ec: ee03ac23  sw           x0, -264(x7)  # cfg[46] (bank 0) · UNP1_ADDR_CTRL_XY_REG_0_Xstride, UNP1_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b8; write 0x00000000; cfg[46] (bank 0); UNP1_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP1_ADDR_CTRL_XY_REG_0_Ystride = 0
    1f0: ee03ae23  sw           x0, -260(x7)  # cfg[47] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_0_Zstride, UNP1_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00bc; write 0x00000000; cfg[47] (bank 0); UNP1_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP1_ADDR_CTRL_ZW_REG_0_Wstride = 0
    1f4: 00200437  lui          x8, 0x00200  # x8 = 0x00200000
    1f8: 00240413  addi         x8, x8, 2  # x8 = 0x00200002
    1fc: f283a423  sw           x8, -216(x7)  # cfg[58] (bank 0) · UNP1_ADDR_CTRL_XY_REG_1_Xstride, UNP1_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e8; write 0x00200002; cfg[58] (bank 0); UNP1_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP1_ADDR_CTRL_XY_REG_1_Ystride = 32
    200: 20000413  addi         x8, x0, 512  # x8 = 0x00000200
    204: f283a623  sw           x8, -212(x7)  # cfg[59] (bank 0) · UNP1_ADDR_CTRL_ZW_REG_1_Zstride, UNP1_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00ec; write 0x00000200; cfg[59] (bank 0); UNP1_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP1_ADDR_CTRL_ZW_REG_1_Wstride = 0
    208: f203a823  sw           x0, -208(x7)  # cfg[60] (bank 0) · UNP1_ADDR_BASE_REG_0_Base · 0xffef00f0; write 0x00000000; cfg[60] (bank 0); UNP1_ADDR_BASE_REG_0_Base = 0
    20c: f203aa23  sw           x0, -204(x7)  # cfg[61] (bank 0) · UNP1_ADDR_BASE_REG_1_Base · 0xffef00f4; write 0x00000000; cfg[61] (bank 0); UNP1_ADDR_BASE_REG_1_Base = 0
    210: f203ac23  sw           x0, -200(x7)  # cfg[62] (bank 0) · UNP1_FORCED_SHARED_EXP_shared_exp, UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00f8; write 0x00000000; cfg[62] (bank 0); UNP1_FORCED_SHARED_EXP_shared_exp = 0; UNP1_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 0
    214: f203ae23  sw           x0, -196(x7)  # cfg[63] (bank 0) · UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00fc; write 0x00000000; cfg[63] (bank 0); UNP1_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    218: 0403a823  sw           x0, 80(x7)  # cfg[132] (bank 0) · THCON_SEC1_REG5_Dest_cntx0_address, THCON_SEC1_REG5_Dest_cntx1_address · 0xffef0210; write 0x00000000; cfg[132] (bank 0); THCON_SEC1_REG5_Dest_cntx0_address = 0; THCON_SEC1_REG5_Dest_cntx1_address = 0
    21c: 01000437  lui          x8, 0x01000  # x8 = 0x01000000
    220: 10040413  addi         x8, x8, 256  # x8 = 0x01000100
    224: 0483ac23  sw           x8, 88(x7)  # cfg[134] (bank 0) · THCON_SEC1_REG5_Tile_x_dim_cntx0, THCON_SEC1_REG5_Tile_x_dim_cntx1 · 0xffef0218; write 0x01000100; cfg[134] (bank 0); THCON_SEC1_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC1_REG5_Tile_x_dim_cntx1 = 256
    228: 0603a823  sw           x0, 112(x7)  # cfg[140] (bank 0) · THCON_SEC1_REG7_Offset_address, THCON_SEC1_REG7_Unpack_data_format_cntx0, THCON_SEC1_REG7_Unpack_out_data_format_cntx0, THCON_SEC1_REG7_Unpack_data_format_cntx4, THCON_SEC1_REG7_Unpack_out_data_format_cntx4 · 0xffef0230; write 0x00000000; cfg[140] (bank 0); THCON_SEC1_REG7_Offset_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx4 = 0
    22c: 0603aa23  sw           x0, 116(x7)  # cfg[141] (bank 0) · THCON_SEC1_REG7_Offset_cntx1_address, THCON_SEC1_REG7_Unpack_data_format_cntx1, THCON_SEC1_REG7_Unpack_out_data_format_cntx1, THCON_SEC1_REG7_Unpack_data_format_cntx5, THCON_SEC1_REG7_Unpack_out_data_format_cntx5 · 0xffef0234; write 0x00000000; cfg[141] (bank 0); THCON_SEC1_REG7_Offset_cntx1_address = 0; THCON_SEC1_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC1_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC1_REG7_Unpack_out_data_format_cntx5 = 0
    230: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    234: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_238:
    238: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    23c: 0feafa93  andi         x21, x21, 254
    240: 000a8663  beq          x21, x0, 0x0000024c  # target 0x0000024c
    244: 0ff0000f  fence        0xf, 0xf
    248: ff1ff06f  jal          x0, 0x00000238  # target 0x00000238
loc_24c:
    24c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    250: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    254: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    258: 004a5a13  srli         x20, x20, 4
    25c: fffa0a13  addi         x20, x20, -1
    260: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    264: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    268: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    26c: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    270: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    274: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_278:
    278: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    27c: 0feafa93  andi         x21, x21, 254
    280: 000a8663  beq          x21, x0, 0x0000028c  # target 0x0000028c
    284: 0ff0000f  fence        0xf, 0xf
    288: ff1ff06f  jal          x0, 0x00000278  # target 0x00000278
loc_28c:
    28c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    290: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    294: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    298: 004a5a13  srli         x20, x20, 4
    29c: fffa0a13  addi         x20, x20, -1
    2a0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    2a4: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    2a8: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    2ac: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    2b0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    2b4: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    2b8: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    2bc: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    2c0: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    2c4: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    2c8: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    2cc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    2d0: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    2d4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    2d8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_2dc:
    2dc: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    2e0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    2e4: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    2e8: 414a8b33  sub          x22, x21, x20
    2ec: 010b1b13  slli         x22, x22, 16
    2f0: 010b5b13  srli         x22, x22, 16
    2f4: 017b7663  bgeu         x22, x23, 0x00000300  # target 0x00000300
    2f8: 0ff0000f  fence        0xf, 0xf
    2fc: fe1ff06f  jal          x0, 0x000002dc  # target 0x000002dc
loc_300:
    300: 0ff0000f  fence        0xf, 0xf
    304: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    308: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    30c: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    310: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    314: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    318: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    31c: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    320: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    324: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    328: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    32c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    330: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    334: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    338: 01507033  and          x0, x0, x21
    33c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    340: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    344: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    348: 001a0a13  addi         x20, x20, 1
    34c: 010a1a13  slli         x20, x20, 16
    350: 010a5a13  srli         x20, x20, 16
    354: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    358: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    35c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    360: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    364: 0ff0000f  fence        0xf, 0xf
    368: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    36c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    370: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    374: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    378: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    37c: 015a0a33  add          x20, x20, x21
    380: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    384: 016a6663  bltu         x20, x22, 0x00000390  # target 0x00000390
    388: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    38c: 417a0a33  sub          x20, x20, x23
loc_390:
    390: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    394: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    398: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    39c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3a0: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_3a4:
    3a4: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    3a8: 0feafa93  andi         x21, x21, 254
    3ac: 000a8663  beq          x21, x0, 0x000003b8  # target 0x000003b8
    3b0: 0ff0000f  fence        0xf, 0xf
    3b4: ff1ff06f  jal          x0, 0x000003a4  # target 0x000003a4
loc_3b8:
    3b8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3bc: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    3c0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    3c4: 004a5a13  srli         x20, x20, 4
    3c8: fffa0a13  addi         x20, x20, -1
    3cc: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    3d0: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    3d4: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    3d8: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    3dc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    3e0: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_3e4:
    3e4: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    3e8: 0feafa93  andi         x21, x21, 254
    3ec: 000a8663  beq          x21, x0, 0x000003f8  # target 0x000003f8
    3f0: 0ff0000f  fence        0xf, 0xf
    3f4: ff1ff06f  jal          x0, 0x000003e4  # target 0x000003e4
loc_3f8:
    3f8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    3fc: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    400: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    404: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    408: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    40c: 015a0a33  add          x20, x20, x21
    410: 00013b37  lui          x22, 0x00013  # x22 = 0x00013000
    414: 016a6663  bltu         x20, x22, 0x00000420  # target 0x00000420
    418: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    41c: 415a0a33  sub          x20, x20, x21
loc_420:
    420: 004a5a13  srli         x20, x20, 4
    424: fffa0a13  addi         x20, x20, -1
    428: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    42c: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    430: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    434: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    438: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    43c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    440: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    444: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    448: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    44c: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    450: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    454: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    458: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    45c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    460: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_464:
    464: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    468: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    46c: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    470: 414a8b33  sub          x22, x21, x20
    474: 010b1b13  slli         x22, x22, 16
    478: 010b5b13  srli         x22, x22, 16
    47c: 017b7663  bgeu         x22, x23, 0x00000488  # target 0x00000488
    480: 0ff0000f  fence        0xf, 0xf
    484: fe1ff06f  jal          x0, 0x00000464  # target 0x00000464
loc_488:
    488: 0ff0000f  fence        0xf, 0xf
    48c: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    490: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    494: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    498: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    49c: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    4a0: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    4a4: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    4a8: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    4ac: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    4b0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    4b4: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    4b8: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    4bc: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    4c0: 01507033  and          x0, x0, x21
    4c4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    4c8: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    4cc: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    4d0: 001a0a13  addi         x20, x20, 1
    4d4: 010a1a13  slli         x20, x20, 16
    4d8: 010a5a13  srli         x20, x20, 16
    4dc: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    4e0: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    4e4: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    4e8: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    4ec: 0ff0000f  fence        0xf, 0xf
    4f0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    4f4: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    4f8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    4fc: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    500: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    504: 015a0a33  add          x20, x20, x21
    508: 00015b37  lui          x22, 0x00015  # x22 = 0x00015000
    50c: 016a6663  bltu         x20, x22, 0x00000518  # target 0x00000518
    510: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    514: 417a0a33  sub          x20, x20, x23
loc_518:
    518: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    51c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    520: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    524: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    528: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_52c:
    52c: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    530: 0fe47413  andi         x8, x8, 254
    534: 00040663  beq          x8, x0, 0x00000540  # target 0x00000540
    538: 0ff0000f  fence        0xf, 0xf
    53c: ff1ff06f  jal          x0, 0x0000052c  # target 0x0000052c
loc_540:
    540: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    544: 12038393  addi         x7, x7, 288  # x7 = 0xffef0120 · cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3
    548: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    54c: 0083a023  sw           x8, 0(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    550: 598000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x00000554
    554: 594000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x00000558
    558: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    55c: 84440413  addi         x8, x8, -1980  # x8 = 0xffb00844 · riscv_local_mem + 0x844
    560: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844
    564: 00138393  addi         x7, x7, 1
    568: 01039393  slli         x7, x7, 16
    56c: 0103d393  srli         x7, x7, 16
    570: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844; write runtime value
    574: ffb4b437  lui          x8, 0xffb4b  # x8 = 0xffb4b000
    578: 02040413  addi         x8, x8, 32  # x8 = 0xffb4b020
    57c: 00742023  sw           x7, 0(x8)  # 0xffb4b020; write runtime value
    580: 0ff0000f  fence        0xf, 0xf
    584: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    588: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    58c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840
    590: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    594: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    598: 008383b3  add          x7, x7, x8
    59c: 000184b7  lui          x9, 0x00018  # x9 = 0x00018000
    5a0: 80048493  addi         x9, x9, -2048  # x9 = 0x00017800
    5a4: 0093e863  bltu         x7, x9, 0x000005b4  # target 0x000005b4
    5a8: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5ac: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    5b0: 40a383b3  sub          x7, x7, x10
loc_5b4:
    5b4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    5b8: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    5bc: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840; write runtime value
    5c0: 00128293  addi         x5, x5, 1
    5c4: bb5ff06f  jal          x0, 0x00000178  # target 0x00000178
loc_5c8:
    5c8: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    5cc: 82c30313  addi         x6, x6, -2004  # x6 = 0xffb0082c · riscv_local_mem + 0x82c
    5d0: 00032283  lw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c
    5d4: 00228293  addi         x5, x5, 2
    5d8: 01029293  slli         x5, x5, 16
    5dc: 0102d293  srli         x5, x5, 16
    5e0: 00532023  sw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c; write runtime value
    5e4: ffb48337  lui          x6, 0xffb48  # x6 = 0xffb48000
    5e8: 02030313  addi         x6, x6, 32  # x6 = 0xffb48020
    5ec: 00532023  sw           x5, 0(x6)  # 0xffb48020; write runtime value
    5f0: 0ff0000f  fence        0xf, 0xf
    5f4: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    5f8: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    5fc: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828
    600: 00001337  lui          x6, 0x00001  # x6 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    604: 006282b3  add          x5, x5, x6
    608: 000133b7  lui          x7, 0x00013  # x7 = 0x00013000
    60c: 0072e663  bltu         x5, x7, 0x00000618  # target 0x00000618
    610: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    614: 408282b3  sub          x5, x5, x8
loc_618:
    618: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    61c: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    620: 0054a023  sw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828; write runtime value
    624: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    628: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    62c: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    630: 28021863  bne          x4, x0, 0x000008c0  # target 0x000008c0
    634: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
    638: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
    63c: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    640: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    644: 0063fa63  bgeu         x7, x6, 0x00000658  # target 0x00000658
    648: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    64c: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
    650: 0063f463  bgeu         x7, x6, 0x00000658  # target 0x00000658
    654: 00800213  addi         x4, x0, 8  # x4 = 0x00000008
loc_658:
    658: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    65c: 02520233  mul          x4, x4, x5
    660: fff20213  addi         x4, x4, -1
    664: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    668: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_66c:
    66c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    670: 0feafa93  andi         x21, x21, 254
    674: 000a8663  beq          x21, x0, 0x00000680  # target 0x00000680
    678: 0ff0000f  fence        0xf, 0xf
    67c: ff1ff06f  jal          x0, 0x0000066c  # target 0x0000066c
loc_680:
    680: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    684: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    688: 01000a93  addi         x21, x0, 16  # x21 = 0x00000010
    68c: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000010; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 16
    690: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    694: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
    698: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848
    69c: 004a5a13  srli         x20, x20, 4
    6a0: fffa0a13  addi         x20, x20, -1
    6a4: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    6a8: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    6ac: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    6b0: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    6b4: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    6b8: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    6bc: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    6c0: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    6c4: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    6c8: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    6cc: 84cc0c13  addi         x24, x24, -1972  # x24 = 0xffb0084c · riscv_local_mem + 0x84c
    6d0: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x84c · 0xffb0084c
    6d4: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_6d8:
    6d8: ffb50c37  lui          x24, 0xffb50  # x24 = 0xffb50000
    6dc: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb50028
    6e0: 000c5a83  lhu          x21, 0(x24)  # 0xffb50028
    6e4: 414a8b33  sub          x22, x21, x20
    6e8: 010b1b13  slli         x22, x22, 16
    6ec: 010b5b13  srli         x22, x22, 16
    6f0: 017b7663  bgeu         x22, x23, 0x000006fc  # target 0x000006fc
    6f4: 0ff0000f  fence        0xf, 0xf
    6f8: fe1ff06f  jal          x0, 0x000006d8  # target 0x000006d8
loc_6fc:
    6fc: 0ff0000f  fence        0xf, 0xf
    700: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    704: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    708: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    70c: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    710: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    714: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    718: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    71c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    720: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    724: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    728: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    72c: 01507033  and          x0, x0, x21
    730: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    734: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
    738: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c
    73c: 001a0a13  addi         x20, x20, 1
    740: 010a1a13  slli         x20, x20, 16
    744: 010a5a13  srli         x20, x20, 16
    748: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write runtime value
    74c: ffb50ab7  lui          x21, 0xffb50  # x21 = 0xffb50000
    750: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb50020
    754: 014aa023  sw           x20, 0(x21)  # 0xffb50020; write runtime value
    758: 0ff0000f  fence        0xf, 0xf
    75c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    760: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    764: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848
    768: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    76c: 015a0a33  add          x20, x20, x21
    770: 0003fb37  lui          x22, 0x0003f  # x22 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    774: 880b0b13  addi         x22, x22, -1920  # x22 = 0x0003e880 · arc_apb_reset_unit + 0xe880
    778: 016a6663  bltu         x20, x22, 0x00000784  # target 0x00000784
    77c: 00020bb7  lui          x23, 0x00020  # x23 = 0x00020000
    780: 417a0a33  sub          x20, x20, x23
loc_784:
    784: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    788: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    78c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848; write runtime value
    790: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    794: 00020393  addi         x7, x4, 0
loc_798:
    798: 12737463  bgeu         x6, x7, 0x000008c0  # target 0x000008c0
    79c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    7a0: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_7a4:
    7a4: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    7a8: 0feafa93  andi         x21, x21, 254
    7ac: 000a8663  beq          x21, x0, 0x000007b8  # target 0x000007b8
    7b0: 0ff0000f  fence        0xf, 0xf
    7b4: ff1ff06f  jal          x0, 0x000007a4  # target 0x000007a4
loc_7b8:
    7b8: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    7bc: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
    7c0: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848
    7c4: 004a5a13  srli         x20, x20, 4
    7c8: fffa0a13  addi         x20, x20, -1
    7cc: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    7d0: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    7d4: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    7d8: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    7dc: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    7e0: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    7e4: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    7e8: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    7ec: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    7f0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    7f4: 84cc0c13  addi         x24, x24, -1972  # x24 = 0xffb0084c · riscv_local_mem + 0x84c
    7f8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x84c · 0xffb0084c
    7fc: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_800:
    800: ffb50c37  lui          x24, 0xffb50  # x24 = 0xffb50000
    804: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb50028
    808: 000c5a83  lhu          x21, 0(x24)  # 0xffb50028
    80c: 414a8b33  sub          x22, x21, x20
    810: 010b1b13  slli         x22, x22, 16
    814: 010b5b13  srli         x22, x22, 16
    818: 017b7663  bgeu         x22, x23, 0x00000824  # target 0x00000824
    81c: 0ff0000f  fence        0xf, 0xf
    820: fe1ff06f  jal          x0, 0x00000800  # target 0x00000800
loc_824:
    824: 0ff0000f  fence        0xf, 0xf
    828: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    82c: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    830: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    834: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    838: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    83c: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    840: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    844: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    848: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    84c: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    850: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    854: 01507033  and          x0, x0, x21
    858: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    85c: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
    860: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c
    864: 001a0a13  addi         x20, x20, 1
    868: 010a1a13  slli         x20, x20, 16
    86c: 010a5a13  srli         x20, x20, 16
    870: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write runtime value
    874: ffb50ab7  lui          x21, 0xffb50  # x21 = 0xffb50000
    878: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb50020
    87c: 014aa023  sw           x20, 0(x21)  # 0xffb50020; write runtime value
    880: 0ff0000f  fence        0xf, 0xf
    884: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    888: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    88c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848
    890: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    894: 015a0a33  add          x20, x20, x21
    898: 0003fb37  lui          x22, 0x0003f  # x22 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    89c: 880b0b13  addi         x22, x22, -1920  # x22 = 0x0003e880 · arc_apb_reset_unit + 0xe880
    8a0: 016a6663  bltu         x20, x22, 0x000008ac  # target 0x000008ac
    8a4: 00020bb7  lui          x23, 0x00020  # x23 = 0x00020000
    8a8: 417a0a33  sub          x20, x20, x23
loc_8ac:
    8ac: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    8b0: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    8b4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848; write runtime value
    8b8: 00130313  addi         x6, x6, 1
    8bc: eddff06f  jal          x0, 0x00000798  # target 0x00000798
loc_8c0:
    8c0: 3d00006f  jal          x0, 0x00000c90  # target 0x00000c90
loc_8c4:
    8c4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    8c8: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_8cc:
    8cc: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    8d0: 0feafa93  andi         x21, x21, 254
    8d4: 000a8663  beq          x21, x0, 0x000008e0  # target 0x000008e0
    8d8: 0ff0000f  fence        0xf, 0xf
    8dc: ff1ff06f  jal          x0, 0x000008cc  # target 0x000008cc
loc_8e0:
    8e0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    8e4: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    8e8: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    8ec: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    8f0: 01500a93  addi         x21, x0, 21  # x21 = 0x00000015
    8f4: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    8f8: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    8fc: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
    900: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    904: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    908: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    90c: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
    910: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    914: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
    918: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    91c: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    920: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    924: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    928: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    92c: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    930: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
    934: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    938: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
    93c: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    940: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    944: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    948: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
    94c: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    950: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    954: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    958: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
    95c: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    960: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    964: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    968: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    96c: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    970: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    974: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    978: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    97c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    980: 004a5a13  srli         x20, x20, 4
    984: fffa0a13  addi         x20, x20, -1
    988: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    98c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    990: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    994: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    998: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    99c: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    9a0: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    9a4: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    9a8: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    9ac: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    9b0: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    9b4: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    9b8: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    9bc: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    9c0: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    9c4: 01507033  and          x0, x0, x21
    9c8: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    9cc: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    9d0: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    9d4: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    9d8: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    9dc: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    9e0: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    9e4: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    9e8: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    9ec: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    9f0: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    9f4: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    9f8: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    9fc: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    a00: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    a04: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    a08: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    a0c: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    a10: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    a14: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    a18: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    a1c: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    a20: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    a24: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_a28:
    a28: ffb4dc37  lui          x24, 0xffb4d  # x24 = 0xffb4d000
    a2c: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4d028
    a30: 000c5a83  lhu          x21, 0(x24)  # 0xffb4d028
    a34: 414a8b33  sub          x22, x21, x20
    a38: 010b1b13  slli         x22, x22, 16
    a3c: 010b5b13  srli         x22, x22, 16
    a40: 017b7663  bgeu         x22, x23, 0x00000a4c  # target 0x00000a4c
    a44: 0ff0000f  fence        0xf, 0xf
    a48: fe1ff06f  jal          x0, 0x00000a28  # target 0x00000a28
loc_a4c:
    a4c: 0ff0000f  fence        0xf, 0xf
    a50: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    a54: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    a58: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    a5c: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    a60: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a64: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    a68: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    a6c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    a70: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    a74: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    a78: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    a7c: 01507033  and          x0, x0, x21
    a80: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    a84: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    a88: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    a8c: 001a0a13  addi         x20, x20, 1
    a90: 010a1a13  slli         x20, x20, 16
    a94: 010a5a13  srli         x20, x20, 16
    a98: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    a9c: ffb4dab7  lui          x21, 0xffb4d  # x21 = 0xffb4d000
    aa0: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4d020
    aa4: 014aa023  sw           x20, 0(x21)  # 0xffb4d020; write runtime value
    aa8: 0ff0000f  fence        0xf, 0xf
    aac: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    ab0: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    ab4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    ab8: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    abc: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    ac0: 015a0a33  add          x20, x20, x21
    ac4: 0001eb37  lui          x22, 0x0001e  # x22 = 0x0001e000
    ac8: 800b0b13  addi         x22, x22, -2048  # x22 = 0x0001d800
    acc: 016a6663  bltu         x20, x22, 0x00000ad8  # target 0x00000ad8
    ad0: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    ad4: 417a0a33  sub          x20, x20, x23
loc_ad8:
    ad8: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    adc: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    ae0: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    ae4: 00008067  jalr         x0, 0(x1)
loc_ae8:
    ae8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    aec: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_af0:
    af0: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    af4: 0feafa93  andi         x21, x21, 254
    af8: 000a8663  beq          x21, x0, 0x00000b04  # target 0x00000b04
    afc: 0ff0000f  fence        0xf, 0xf
    b00: ff1ff06f  jal          x0, 0x00000af0  # target 0x00000af0
loc_b04:
    b04: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    b08: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
    b0c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838
    b10: 004a5a13  srli         x20, x20, 4
    b14: fffa0a13  addi         x20, x20, -1
    b18: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    b1c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    b20: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    b24: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    b28: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    b2c: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_b30:
    b30: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    b34: 0feafa93  andi         x21, x21, 254
    b38: 000a8663  beq          x21, x0, 0x00000b44  # target 0x00000b44
    b3c: 0ff0000f  fence        0xf, 0xf
    b40: ff1ff06f  jal          x0, 0x00000b30  # target 0x00000b30
loc_b44:
    b44: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    b48: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
    b4c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840
    b50: 004a5a13  srli         x20, x20, 4
    b54: fffa0a13  addi         x20, x20, -1
    b58: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    b5c: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    b60: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    b64: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    b68: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    b6c: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    b70: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    b74: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    b78: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    b7c: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    b80: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    b84: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    b88: 844c0c13  addi         x24, x24, -1980  # x24 = 0xffb00844 · riscv_local_mem + 0x844
    b8c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x844 · 0xffb00844
    b90: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_b94:
    b94: ffb4bc37  lui          x24, 0xffb4b  # x24 = 0xffb4b000
    b98: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4b028
    b9c: 000c5a83  lhu          x21, 0(x24)  # 0xffb4b028
    ba0: 414a8b33  sub          x22, x21, x20
    ba4: 010b1b13  slli         x22, x22, 16
    ba8: 010b5b13  srli         x22, x22, 16
    bac: 017b7663  bgeu         x22, x23, 0x00000bb8  # target 0x00000bb8
    bb0: 0ff0000f  fence        0xf, 0xf
    bb4: fe1ff06f  jal          x0, 0x00000b94  # target 0x00000b94
loc_bb8:
    bb8: 0ff0000f  fence        0xf, 0xf
    bbc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    bc0: 83cc0c13  addi         x24, x24, -1988  # x24 = 0xffb0083c · riscv_local_mem + 0x83c
    bc4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x83c · 0xffb0083c
    bc8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_bcc:
    bcc: ffb4ac37  lui          x24, 0xffb4a  # x24 = 0xffb4a000
    bd0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4a028
    bd4: 000c5a83  lhu          x21, 0(x24)  # 0xffb4a028
    bd8: 414a8b33  sub          x22, x21, x20
    bdc: 010b1b13  slli         x22, x22, 16
    be0: 010b5b13  srli         x22, x22, 16
    be4: 017b7663  bgeu         x22, x23, 0x00000bf0  # target 0x00000bf0
    be8: 0ff0000f  fence        0xf, 0xf
    bec: fe1ff06f  jal          x0, 0x00000bcc  # target 0x00000bcc
loc_bf0:
    bf0: 0ff0000f  fence        0xf, 0xf
    bf4: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    bf8: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    bfc: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    c00: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    c04: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    c08: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    c0c: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    c10: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    c14: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    c18: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    c1c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    c20: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    c24: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    c28: 01507033  and          x0, x0, x21
    c2c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    c30: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    c34: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c
    c38: 001a0a13  addi         x20, x20, 1
    c3c: 010a1a13  slli         x20, x20, 16
    c40: 010a5a13  srli         x20, x20, 16
    c44: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write runtime value
    c48: ffb4aab7  lui          x21, 0xffb4a  # x21 = 0xffb4a000
    c4c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4a020
    c50: 014aa023  sw           x20, 0(x21)  # 0xffb4a020; write runtime value
    c54: 0ff0000f  fence        0xf, 0xf
    c58: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    c5c: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    c60: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838
    c64: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    c68: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    c6c: 015a0a33  add          x20, x20, x21
    c70: 00017b37  lui          x22, 0x00017  # x22 = 0x00017000
    c74: 016a6663  bltu         x20, x22, 0x00000c80  # target 0x00000c80
    c78: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    c7c: 417a0a33  sub          x20, x20, x23
loc_c80:
    c80: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    c84: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    c88: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838; write runtime value
    c8c: 00008067  jalr         x0, 0(x1)
    c90:           j FW_TRISC0+4   # return to firmware, linked at install
