# llama3 8b-bf16 decode: attention, trisc0. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
      4: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
      8: 00023b37  lui          x22, 0x00023  # x22 = 0x00023000
      c: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00022800
     10: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820; write 0x00022800
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
     44: 00014b37  lui          x22, 0x00014  # x22 = 0x00014000
     48: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830; write 0x00014000
     4c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     50: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
     54: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write 0x00000000
     58: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     5c: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
     60: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
     64: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838; write 0x00018000
     68: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     6c: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
     70: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write 0x00000000
     74: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     78: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
     7c: 0001cb37  lui          x22, 0x0001c  # x22 = 0x0001c000
     80: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840; write 0x0001c000
     84: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     88: 844a8a93  addi         x21, x21, -1980  # x21 = 0xffb00844 · riscv_local_mem + 0x844
     8c: 000aa023  sw           x0, 0(x21)  # riscv_local_mem + 0x844 · 0xffb00844; write 0x00000000
     90: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
     94: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
     98: 00026b37  lui          x22, 0x00026  # x22 = 0x00026000
     9c: 900b0b13  addi         x22, x22, -1792  # x22 = 0x00025900
     a0: 016aa023  sw           x22, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848; write 0x00025900
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
     dc: 2e527ce3  bgeu         x4, x5, 0x00000bd4  # target 0x00000bd4
     e0: 2f9000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000000e4
     e4: 2f5000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000000e8
     e8: 2f1000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000000ec
     ec: 2ed000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000000f0
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
    144: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
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
    178: 7662f263  bgeu         x5, x6, 0x000008dc  # target 0x000008dc
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
    380: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    384: 016a6663  bltu         x20, x22, 0x00000390  # target 0x00000390
    388: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
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
    410: 00014b37  lui          x22, 0x00014  # x22 = 0x00014000
    414: 016a6663  bltu         x20, x22, 0x00000420  # target 0x00000420
    418: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
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
    508: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    50c: 016a6663  bltu         x20, x22, 0x00000518  # target 0x00000518
    510: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    514: 417a0a33  sub          x20, x20, x23
loc_518:
    518: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    51c: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    520: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    524: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    528: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_52c:
    52c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    530: 0feafa93  andi         x21, x21, 254
    534: 000a8663  beq          x21, x0, 0x00000540  # target 0x00000540
    538: 0ff0000f  fence        0xf, 0xf
    53c: ff1ff06f  jal          x0, 0x0000052c  # target 0x0000052c
loc_540:
    540: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    544: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    548: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    54c: 004a5a13  srli         x20, x20, 4
    550: fffa0a13  addi         x20, x20, -1
    554: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    558: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    55c: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    560: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    564: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    568: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_56c:
    56c: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    570: 0feafa93  andi         x21, x21, 254
    574: 000a8663  beq          x21, x0, 0x00000580  # target 0x00000580
    578: 0ff0000f  fence        0xf, 0xf
    57c: ff1ff06f  jal          x0, 0x0000056c  # target 0x0000056c
loc_580:
    580: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    584: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    588: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    58c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    590: 015a0a33  add          x20, x20, x21
    594: 00014b37  lui          x22, 0x00014  # x22 = 0x00014000
    598: 016a6663  bltu         x20, x22, 0x000005a4  # target 0x000005a4
    59c: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    5a0: 415a0a33  sub          x20, x20, x21
loc_5a4:
    5a4: 004a5a13  srli         x20, x20, 4
    5a8: fffa0a13  addi         x20, x20, -1
    5ac: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    5b0: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    5b4: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    5b8: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    5bc: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    5c0: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    5c4: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    5c8: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    5cc: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    5d0: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    5d4: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    5d8: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    5dc: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    5e0: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    5e4: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_5e8:
    5e8: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    5ec: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    5f0: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    5f4: 414a8b33  sub          x22, x21, x20
    5f8: 010b1b13  slli         x22, x22, 16
    5fc: 010b5b13  srli         x22, x22, 16
    600: 017b7663  bgeu         x22, x23, 0x0000060c  # target 0x0000060c
    604: 0ff0000f  fence        0xf, 0xf
    608: fe1ff06f  jal          x0, 0x000005e8  # target 0x000005e8
loc_60c:
    60c: 0ff0000f  fence        0xf, 0xf
    610: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    614: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    618: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    61c: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    620: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    624: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    628: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    62c: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    630: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    634: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    638: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    63c: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    640: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    644: 01507033  and          x0, x0, x21
    648: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    64c: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    650: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    654: 001a0a13  addi         x20, x20, 1
    658: 010a1a13  slli         x20, x20, 16
    65c: 010a5a13  srli         x20, x20, 16
    660: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    664: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    668: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    66c: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    670: 0ff0000f  fence        0xf, 0xf
    674: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    678: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    67c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    680: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    684: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    688: 015a0a33  add          x20, x20, x21
    68c: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    690: 016a6663  bltu         x20, x22, 0x0000069c  # target 0x0000069c
    694: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    698: 417a0a33  sub          x20, x20, x23
loc_69c:
    69c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    6a0: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    6a4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    6a8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    6ac: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_6b0:
    6b0: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    6b4: 0feafa93  andi         x21, x21, 254
    6b8: 000a8663  beq          x21, x0, 0x000006c4  # target 0x000006c4
    6bc: 0ff0000f  fence        0xf, 0xf
    6c0: ff1ff06f  jal          x0, 0x000006b0  # target 0x000006b0
loc_6c4:
    6c4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    6c8: 830a8a93  addi         x21, x21, -2000  # x21 = 0xffb00830 · riscv_local_mem + 0x830
    6cc: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x830 · 0xffb00830
    6d0: 004a5a13  srli         x20, x20, 4
    6d4: fffa0a13  addi         x20, x20, -1
    6d8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    6dc: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    6e0: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    6e4: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    6e8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    6ec: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_6f0:
    6f0: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    6f4: 0feafa93  andi         x21, x21, 254
    6f8: 000a8663  beq          x21, x0, 0x00000704  # target 0x00000704
    6fc: 0ff0000f  fence        0xf, 0xf
    700: ff1ff06f  jal          x0, 0x000006f0  # target 0x000006f0
loc_704:
    704: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    708: 828a8a93  addi         x21, x21, -2008  # x21 = 0xffb00828 · riscv_local_mem + 0x828
    70c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x828 · 0xffb00828
    710: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    714: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00001800
    718: 015a0a33  add          x20, x20, x21
    71c: 00014b37  lui          x22, 0x00014  # x22 = 0x00014000
    720: 016a6663  bltu         x20, x22, 0x0000072c  # target 0x0000072c
    724: 00002ab7  lui          x21, 0x00002  # x21 = 0x00002000
    728: 415a0a33  sub          x20, x20, x21
loc_72c:
    72c: 004a5a13  srli         x20, x20, 4
    730: fffa0a13  addi         x20, x20, -1
    734: ffef0bb7  lui          x23, 0xffef0  # x23 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    738: 1f0b8b93  addi         x23, x23, 496  # x23 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    73c: 014ba023  sw           x20, 0(x23)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    740: 014ba223  sw           x20, 4(x23)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    744: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    748: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    74c: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    750: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    754: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    758: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    75c: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    760: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    764: 834c0c13  addi         x24, x24, -1996  # x24 = 0xffb00834 · riscv_local_mem + 0x834
    768: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x834 · 0xffb00834
    76c: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_770:
    770: ffb49c37  lui          x24, 0xffb49  # x24 = 0xffb49000
    774: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb49028
    778: 000c5a83  lhu          x21, 0(x24)  # 0xffb49028
    77c: 414a8b33  sub          x22, x21, x20
    780: 010b1b13  slli         x22, x22, 16
    784: 010b5b13  srli         x22, x22, 16
    788: 017b7663  bgeu         x22, x23, 0x00000794  # target 0x00000794
    78c: 0ff0000f  fence        0xf, 0xf
    790: fe1ff06f  jal          x0, 0x00000770  # target 0x00000770
loc_794:
    794: 0ff0000f  fence        0xf, 0xf
    798: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    79c: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    7a0: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    7a4: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    7a8: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    7ac: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    7b0: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    7b4: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    7b8: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    7bc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    7c0: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    7c4: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    7c8: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    7cc: 01507033  and          x0, x0, x21
    7d0: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    7d4: 834a8a93  addi         x21, x21, -1996  # x21 = 0xffb00834 · riscv_local_mem + 0x834
    7d8: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834
    7dc: 001a0a13  addi         x20, x20, 1
    7e0: 010a1a13  slli         x20, x20, 16
    7e4: 010a5a13  srli         x20, x20, 16
    7e8: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x834 · 0xffb00834; write runtime value
    7ec: ffb49ab7  lui          x21, 0xffb49  # x21 = 0xffb49000
    7f0: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb49020
    7f4: 014aa023  sw           x20, 0(x21)  # 0xffb49020; write runtime value
    7f8: 0ff0000f  fence        0xf, 0xf
    7fc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    800: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    804: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830
    808: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    80c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    810: 015a0a33  add          x20, x20, x21
    814: 00018b37  lui          x22, 0x00018  # x22 = 0x00018000
    818: 016a6663  bltu         x20, x22, 0x00000824  # target 0x00000824
    81c: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    820: 417a0a33  sub          x20, x20, x23
loc_824:
    824: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    828: 830c0c13  addi         x24, x24, -2000  # x24 = 0xffb00830 · riscv_local_mem + 0x830
    82c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x830 · 0xffb00830; write runtime value
    830: ffe803b7  lui          x7, 0xffe80  # x7 = 0xffe80000 · tensix_pc_buf + 0x0
    834: 03438393  addi         x7, x7, 52  # x7 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_838:
    838: 0003a403  lw           x8, 0(x7)  # UNPACK_CONFIG_SYNC · 0xffe80034
    83c: 0fe47413  andi         x8, x8, 254
    840: 00040663  beq          x8, x0, 0x0000084c  # target 0x0000084c
    844: 0ff0000f  fence        0xf, 0xf
    848: ff1ff06f  jal          x0, 0x00000838  # target 0x00000838
loc_84c:
    84c: ffef03b7  lui          x7, 0xffef0  # x7 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    850: 12038393  addi         x7, x7, 288  # x7 = 0xffef0120 · cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3
    854: 02500413  addi         x8, x0, 37  # x8 = 0x00000025
    858: 0083a023  sw           x8, 0(x7)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    85c: 5a0000ef  jal          x1, 0x00000dfc  # target 0x00000dfc; x1 = 0x00000860
    860: 59c000ef  jal          x1, 0x00000dfc  # target 0x00000dfc; x1 = 0x00000864
    864: 598000ef  jal          x1, 0x00000dfc  # target 0x00000dfc; x1 = 0x00000868
    868: 594000ef  jal          x1, 0x00000dfc  # target 0x00000dfc; x1 = 0x0000086c
    86c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    870: 84440413  addi         x8, x8, -1980  # x8 = 0xffb00844 · riscv_local_mem + 0x844
    874: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844
    878: 00138393  addi         x7, x7, 1
    87c: 01039393  slli         x7, x7, 16
    880: 0103d393  srli         x7, x7, 16
    884: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x844 · 0xffb00844; write runtime value
    888: ffb4b437  lui          x8, 0xffb4b  # x8 = 0xffb4b000
    88c: 02040413  addi         x8, x8, 32  # x8 = 0xffb4b020
    890: 00742023  sw           x7, 0(x8)  # 0xffb4b020; write runtime value
    894: 0ff0000f  fence        0xf, 0xf
    898: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    89c: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    8a0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840
    8a4: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8a8: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    8ac: 008383b3  add          x7, x7, x8
    8b0: 0001d4b7  lui          x9, 0x0001d  # x9 = 0x0001d000
    8b4: 80048493  addi         x9, x9, -2048  # x9 = 0x0001c800
    8b8: 0093e863  bltu         x7, x9, 0x000008c8  # target 0x000008c8
    8bc: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8c0: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    8c4: 40a383b3  sub          x7, x7, x10
loc_8c8:
    8c8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    8cc: 84058593  addi         x11, x11, -1984  # x11 = 0xffb00840 · riscv_local_mem + 0x840
    8d0: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x840 · 0xffb00840; write runtime value
    8d4: 00128293  addi         x5, x5, 1
    8d8: 8a1ff06f  jal          x0, 0x00000178  # target 0x00000178
loc_8dc:
    8dc: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    8e0: 82c30313  addi         x6, x6, -2004  # x6 = 0xffb0082c · riscv_local_mem + 0x82c
    8e4: 00032283  lw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c
    8e8: 00428293  addi         x5, x5, 4
    8ec: 01029293  slli         x5, x5, 16
    8f0: 0102d293  srli         x5, x5, 16
    8f4: 00532023  sw           x5, 0(x6)  # riscv_local_mem + 0x82c · 0xffb0082c; write runtime value
    8f8: ffb48337  lui          x6, 0xffb48  # x6 = 0xffb48000
    8fc: 02030313  addi         x6, x6, 32  # x6 = 0xffb48020
    900: 00532023  sw           x5, 0(x6)  # 0xffb48020; write runtime value
    904: 0ff0000f  fence        0xf, 0xf
    908: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    90c: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    910: 0004a283  lw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828
    914: 00002337  lui          x6, 0x00002  # x6 = 0x00002000
    918: 006282b3  add          x5, x5, x6
    91c: 000143b7  lui          x7, 0x00014  # x7 = 0x00014000
    920: 0072e663  bltu         x5, x7, 0x0000092c  # target 0x0000092c
    924: 00002437  lui          x8, 0x00002  # x8 = 0x00002000
    928: 408282b3  sub          x5, x5, x8
loc_92c:
    92c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    930: 82848493  addi         x9, x9, -2008  # x9 = 0xffb00828 · riscv_local_mem + 0x828
    934: 0054a023  sw           x5, 0(x9)  # riscv_local_mem + 0x828 · 0xffb00828; write runtime value
    938: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    93c: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    940: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    944: 28021863  bne          x4, x0, 0x00000bd4  # target 0x00000bd4
    948: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
    94c: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
    950: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    954: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    958: 0063fa63  bgeu         x7, x6, 0x0000096c  # target 0x0000096c
    95c: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    960: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
    964: 0063f463  bgeu         x7, x6, 0x0000096c  # target 0x0000096c
    968: 00800213  addi         x4, x0, 8  # x4 = 0x00000008
loc_96c:
    96c: 00600293  addi         x5, x0, 6  # x5 = 0x00000006
    970: 02520233  mul          x4, x4, x5
    974: fff20213  addi         x4, x4, -1
    978: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    97c: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_980:
    980: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    984: 0feafa93  andi         x21, x21, 254
    988: 000a8663  beq          x21, x0, 0x00000994  # target 0x00000994
    98c: 0ff0000f  fence        0xf, 0xf
    990: ff1ff06f  jal          x0, 0x00000980  # target 0x00000980
loc_994:
    994: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    998: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    99c: 01000a93  addi         x21, x0, 16  # x21 = 0x00000010
    9a0: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000010; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 16
    9a4: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    9a8: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
    9ac: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848
    9b0: 004a5a13  srli         x20, x20, 4
    9b4: fffa0a13  addi         x20, x20, -1
    9b8: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    9bc: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    9c0: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    9c4: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    9c8: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    9cc: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    9d0: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    9d4: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    9d8: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    9dc: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    9e0: 84cc0c13  addi         x24, x24, -1972  # x24 = 0xffb0084c · riscv_local_mem + 0x84c
    9e4: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x84c · 0xffb0084c
    9e8: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_9ec:
    9ec: ffb50c37  lui          x24, 0xffb50  # x24 = 0xffb50000
    9f0: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb50028
    9f4: 000c5a83  lhu          x21, 0(x24)  # 0xffb50028
    9f8: 414a8b33  sub          x22, x21, x20
    9fc: 010b1b13  slli         x22, x22, 16
    a00: 010b5b13  srli         x22, x22, 16
    a04: 017b7663  bgeu         x22, x23, 0x00000a10  # target 0x00000a10
    a08: 0ff0000f  fence        0xf, 0xf
    a0c: fe1ff06f  jal          x0, 0x000009ec  # target 0x000009ec
loc_a10:
    a10: 0ff0000f  fence        0xf, 0xf
    a14: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    a18: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    a1c: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    a20: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    a24: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a28: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    a2c: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    a30: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    a34: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    a38: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    a3c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    a40: 01507033  and          x0, x0, x21
    a44: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    a48: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
    a4c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c
    a50: 001a0a13  addi         x20, x20, 1
    a54: 010a1a13  slli         x20, x20, 16
    a58: 010a5a13  srli         x20, x20, 16
    a5c: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write runtime value
    a60: ffb50ab7  lui          x21, 0xffb50  # x21 = 0xffb50000
    a64: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb50020
    a68: 014aa023  sw           x20, 0(x21)  # 0xffb50020; write runtime value
    a6c: 0ff0000f  fence        0xf, 0xf
    a70: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    a74: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    a78: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848
    a7c: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a80: 015a0a33  add          x20, x20, x21
    a84: 00056b37  lui          x22, 0x00056  # x22 = 0x00056000
    a88: 900b0b13  addi         x22, x22, -1792  # x22 = 0x00055900
    a8c: 016a6663  bltu         x20, x22, 0x00000a98  # target 0x00000a98
    a90: 00030bb7  lui          x23, 0x00030  # x23 = 0x00030000 · arc_apb_reset_unit + 0x0
    a94: 417a0a33  sub          x20, x20, x23
loc_a98:
    a98: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    a9c: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    aa0: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848; write runtime value
    aa4: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    aa8: 00020393  addi         x7, x4, 0
loc_aac:
    aac: 12737463  bgeu         x6, x7, 0x00000bd4  # target 0x00000bd4
    ab0: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    ab4: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_ab8:
    ab8: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    abc: 0feafa93  andi         x21, x21, 254
    ac0: 000a8663  beq          x21, x0, 0x00000acc  # target 0x00000acc
    ac4: 0ff0000f  fence        0xf, 0xf
    ac8: ff1ff06f  jal          x0, 0x00000ab8  # target 0x00000ab8
loc_acc:
    acc: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    ad0: 848a8a93  addi         x21, x21, -1976  # x21 = 0xffb00848 · riscv_local_mem + 0x848
    ad4: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x848 · 0xffb00848
    ad8: 004a5a13  srli         x20, x20, 4
    adc: fffa0a13  addi         x20, x20, -1
    ae0: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    ae4: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    ae8: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    aec: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    af0: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    af4: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    af8: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    afc: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    b00: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    b04: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    b08: 84cc0c13  addi         x24, x24, -1972  # x24 = 0xffb0084c · riscv_local_mem + 0x84c
    b0c: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x84c · 0xffb0084c
    b10: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_b14:
    b14: ffb50c37  lui          x24, 0xffb50  # x24 = 0xffb50000
    b18: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb50028
    b1c: 000c5a83  lhu          x21, 0(x24)  # 0xffb50028
    b20: 414a8b33  sub          x22, x21, x20
    b24: 010b1b13  slli         x22, x22, 16
    b28: 010b5b13  srli         x22, x22, 16
    b2c: 017b7663  bgeu         x22, x23, 0x00000b38  # target 0x00000b38
    b30: 0ff0000f  fence        0xf, 0xf
    b34: fe1ff06f  jal          x0, 0x00000b14  # target 0x00000b14
loc_b38:
    b38: 0ff0000f  fence        0xf, 0xf
    b3c: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    b40: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    b44: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    b48: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    b4c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b50: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    b54: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    b58: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    b5c: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    b60: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    b64: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    b68: 01507033  and          x0, x0, x21
    b6c: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    b70: 84ca8a93  addi         x21, x21, -1972  # x21 = 0xffb0084c · riscv_local_mem + 0x84c
    b74: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c
    b78: 001a0a13  addi         x20, x20, 1
    b7c: 010a1a13  slli         x20, x20, 16
    b80: 010a5a13  srli         x20, x20, 16
    b84: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x84c · 0xffb0084c; write runtime value
    b88: ffb50ab7  lui          x21, 0xffb50  # x21 = 0xffb50000
    b8c: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb50020
    b90: 014aa023  sw           x20, 0(x21)  # 0xffb50020; write runtime value
    b94: 0ff0000f  fence        0xf, 0xf
    b98: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    b9c: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    ba0: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848
    ba4: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    ba8: 015a0a33  add          x20, x20, x21
    bac: 00056b37  lui          x22, 0x00056  # x22 = 0x00056000
    bb0: 900b0b13  addi         x22, x22, -1792  # x22 = 0x00055900
    bb4: 016a6663  bltu         x20, x22, 0x00000bc0  # target 0x00000bc0
    bb8: 00030bb7  lui          x23, 0x00030  # x23 = 0x00030000 · arc_apb_reset_unit + 0x0
    bbc: 417a0a33  sub          x20, x20, x23
loc_bc0:
    bc0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    bc4: 848c0c13  addi         x24, x24, -1976  # x24 = 0xffb00848 · riscv_local_mem + 0x848
    bc8: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x848 · 0xffb00848; write runtime value
    bcc: 00130313  addi         x6, x6, 1
    bd0: eddff06f  jal          x0, 0x00000aac  # target 0x00000aac
loc_bd4:
    bd4: 3d00006f  jal          x0, 0x00000fa4  # target 0x00000fa4
loc_bd8:
    bd8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    bdc: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_be0:
    be0: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    be4: 0feafa93  andi         x21, x21, 254
    be8: 000a8663  beq          x21, x0, 0x00000bf4  # target 0x00000bf4
    bec: 0ff0000f  fence        0xf, 0xf
    bf0: ff1ff06f  jal          x0, 0x00000be0  # target 0x00000be0
loc_bf4:
    bf4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    bf8: d500011e  RMWCIB2      Mask=64, Data=0, CfgRegAddr=71  # cfg[71] (current thread StateID); THCON_SEC0_REG1_Unp_LF8_4b_exp = 0
    bfc: ffef0a37  lui          x20, 0xffef0  # x20 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    c00: 100a0a13  addi         x20, x20, 256  # x20 = 0xffef0100 · cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor
    c04: 01500a93  addi         x21, x0, 21  # x21 = 0x00000015
    c08: 015a2023  sw           x21, 0(x20)  # cfg[64] (bank 0) · THCON_SEC0_REG0_TileDescriptor · 0xffef0100; write 0x00000015; cfg[64] (bank 0); THCON_SEC0_REG0_TileDescriptor = 21
    c0c: 00040ab7  lui          x21, 0x00040  # x21 = 0x00040000
    c10: 001a8a93  addi         x21, x21, 1  # x21 = 0x00040001
    c14: 015a2223  sw           x21, 4(x20)  # cfg[65] (bank 0) (undocumented index) · 0xffef0104; write 0x00040001; cfg[65] (bank 0) · fields not in ttsim
    c18: 000a2423  sw           x0, 8(x20)  # cfg[66] (bank 0) (undocumented index) · 0xffef0108; write 0x00000000; cfg[66] (bank 0) · fields not in ttsim
    c1c: 000a2623  sw           x0, 12(x20)  # cfg[67] (bank 0) (undocumented index) · 0xffef010c; write 0x00000000; cfg[67] (bank 0) · fields not in ttsim
    c20: 02500a93  addi         x21, x0, 37  # x21 = 0x00000025
    c24: 035a2023  sw           x21, 32(x20)  # cfg[72] (bank 0) · THCON_SEC0_REG2_Out_data_format, THCON_SEC0_REG2_Throttle_mode, THCON_SEC0_REG2_Context_count, THCON_SEC0_REG2_Haloize_mode, THCON_SEC0_REG2_Tileize_mode, THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd, THCON_SEC0_REG2_Unpack_If_Sel, THCON_SEC0_REG2_Upsample_rate, THCON_SEC0_REG2_Ovrd_data_format, THCON_SEC0_REG2_Upsample_and_interleave, THCON_SEC0_REG2_Shift_amount_cntx0, THCON_SEC0_REG2_Shift_amount_cntx1, THCON_SEC0_REG2_Shift_amount_cntx2, THCON_SEC0_REG2_Shift_amount_cntx3 · 0xffef0120; write 0x00000025; cfg[72] (bank 0); THCON_SEC0_REG2_Out_data_format = 5; THCON_SEC0_REG2_Throttle_mode = 2; THCON_SEC0_REG2_Context_count = 0; THCON_SEC0_REG2_Haloize_mode = 0; THCON_SEC0_REG2_Tileize_mode = 0; THCON_SEC0_REG2_Unpack_Src_Reg_Set_Upd = 0; THCON_SEC0_REG2_Unpack_If_Sel = 0; THCON_SEC0_REG2_Upsample_rate = 0; THCON_SEC0_REG2_Ovrd_data_format = 0; THCON_SEC0_REG2_Upsample_and_interleave = 0; THCON_SEC0_REG2_Shift_amount_cntx0 = 0; THCON_SEC0_REG2_Shift_amount_cntx1 = 0; THCON_SEC0_REG2_Shift_amount_cntx2 = 0; THCON_SEC0_REG2_Shift_amount_cntx3 = 0
    c28: 00300a93  addi         x21, x0, 3  # x21 = 0x00000003
    c2c: 035a2223  sw           x21, 36(x20)  # cfg[73] (bank 0) · THCON_SEC0_REG2_Disable_zero_compress_cntx0, THCON_SEC0_REG2_Disable_zero_compress_cntx1, THCON_SEC0_REG2_Disable_zero_compress_cntx2, THCON_SEC0_REG2_Disable_zero_compress_cntx3, THCON_SEC0_REG2_Unpack_if_sel_cntx0, THCON_SEC0_REG2_Unpack_if_sel_cntx1, THCON_SEC0_REG2_Unpack_if_sel_cntx2, THCON_SEC0_REG2_Unpack_if_sel_cntx3, THCON_SEC0_REG2_Force_shared_exp, THCON_SEC0_REG2_Context_count_non_log2, THCON_SEC0_REG2_Context_count_non_log2_en, THCON_SEC0_REG2_Disable_zero_compress_cntx4, THCON_SEC0_REG2_Disable_zero_compress_cntx5, THCON_SEC0_REG2_Disable_zero_compress_cntx6, THCON_SEC0_REG2_Disable_zero_compress_cntx7, THCON_SEC0_REG2_Unpack_if_sel_cntx4, THCON_SEC0_REG2_Unpack_if_sel_cntx5, THCON_SEC0_REG2_Unpack_if_sel_cntx6, THCON_SEC0_REG2_Unpack_if_sel_cntx7, THCON_SEC0_REG2_Metadata_x_end · 0xffef0124; write 0x00000003; cfg[73] (bank 0); THCON_SEC0_REG2_Disable_zero_compress_cntx0 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx1 = 1; THCON_SEC0_REG2_Disable_zero_compress_cntx2 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx3 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx0 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx1 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx2 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx3 = 0; THCON_SEC0_REG2_Force_shared_exp = 0; THCON_SEC0_REG2_Context_count_non_log2 = 0; THCON_SEC0_REG2_Context_count_non_log2_en = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx4 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx5 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx6 = 0; THCON_SEC0_REG2_Disable_zero_compress_cntx7 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx4 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx5 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx6 = 0; THCON_SEC0_REG2_Unpack_if_sel_cntx7 = 0; THCON_SEC0_REG2_Metadata_x_end = 0
    c30: 020a2423  sw           x0, 40(x20)  # cfg[74] (bank 0) · THCON_SEC0_REG2_Unpack_limit_address · 0xffef0128; write 0x00000000; cfg[74] (bank 0); THCON_SEC0_REG2_Unpack_limit_address = 0
    c34: 020a2623  sw           x0, 44(x20)  # cfg[75] (bank 0) · THCON_SEC0_REG2_Unpack_fifo_size · 0xffef012c; write 0x00000000; cfg[75] (bank 0); THCON_SEC0_REG2_Unpack_fifo_size = 0
    c38: fa0a2823  sw           x0, -80(x20)  # cfg[44] (bank 0) · UNP0_ADDR_CTRL_XY_REG_0_Xstride, UNP0_ADDR_CTRL_XY_REG_0_Ystride · 0xffef00b0; write 0x00000000; cfg[44] (bank 0); UNP0_ADDR_CTRL_XY_REG_0_Xstride = 0; UNP0_ADDR_CTRL_XY_REG_0_Ystride = 0
    c3c: fa0a2a23  sw           x0, -76(x20)  # cfg[45] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_0_Zstride, UNP0_ADDR_CTRL_ZW_REG_0_Wstride · 0xffef00b4; write 0x00000000; cfg[45] (bank 0); UNP0_ADDR_CTRL_ZW_REG_0_Zstride = 0; UNP0_ADDR_CTRL_ZW_REG_0_Wstride = 0
    c40: 00200ab7  lui          x21, 0x00200  # x21 = 0x00200000
    c44: 002a8a93  addi         x21, x21, 2  # x21 = 0x00200002
    c48: ff5a2023  sw           x21, -32(x20)  # cfg[56] (bank 0) · UNP0_ADDR_CTRL_XY_REG_1_Xstride, UNP0_ADDR_CTRL_XY_REG_1_Ystride · 0xffef00e0; write 0x00200002; cfg[56] (bank 0); UNP0_ADDR_CTRL_XY_REG_1_Xstride = 2; UNP0_ADDR_CTRL_XY_REG_1_Ystride = 32
    c4c: 20000a93  addi         x21, x0, 512  # x21 = 0x00000200
    c50: ff5a2223  sw           x21, -28(x20)  # cfg[57] (bank 0) · UNP0_ADDR_CTRL_ZW_REG_1_Zstride, UNP0_ADDR_CTRL_ZW_REG_1_Wstride · 0xffef00e4; write 0x00000200; cfg[57] (bank 0); UNP0_ADDR_CTRL_ZW_REG_1_Zstride = 512; UNP0_ADDR_CTRL_ZW_REG_1_Wstride = 0
    c54: fc0a2023  sw           x0, -64(x20)  # cfg[48] (bank 0) · UNP0_ADDR_BASE_REG_0_Base · 0xffef00c0; write 0x00000000; cfg[48] (bank 0); UNP0_ADDR_BASE_REG_0_Base = 0
    c58: fc0a2223  sw           x0, -60(x20)  # cfg[49] (bank 0) · UNP0_ADDR_BASE_REG_1_Base · 0xffef00c4; write 0x00000000; cfg[49] (bank 0); UNP0_ADDR_BASE_REG_1_Base = 0
    c5c: 10000a93  addi         x21, x0, 256  # x21 = 0x00000100
    c60: fd5a2423  sw           x21, -56(x20)  # cfg[50] (bank 0) · UNP0_FORCED_SHARED_EXP_shared_exp, UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr · 0xffef00c8; write 0x00000100; cfg[50] (bank 0); UNP0_FORCED_SHARED_EXP_shared_exp = 0; UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr = 1
    c64: fc0a2a23  sw           x0, -44(x20)  # cfg[53] (bank 0) · UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val · 0xffef00d4; write 0x00000000; cfg[53] (bank 0); UNP0_NOP_REG_CLR_VAL_nop_reg_clr_val = 0
    c68: 00400ab7  lui          x21, 0x00400  # x21 = 0x00400000
    c6c: 040a8a93  addi         x21, x21, 64  # x21 = 0x00400040
    c70: 055a2823  sw           x21, 80(x20)  # cfg[84] (bank 0) · THCON_SEC0_REG5_Dest_cntx0_address, THCON_SEC0_REG5_Dest_cntx1_address · 0xffef0150; write 0x00400040; cfg[84] (bank 0); THCON_SEC0_REG5_Dest_cntx0_address = 64; THCON_SEC0_REG5_Dest_cntx1_address = 64
    c74: 01000ab7  lui          x21, 0x01000  # x21 = 0x01000000
    c78: 100a8a93  addi         x21, x21, 256  # x21 = 0x01000100
    c7c: 055a2c23  sw           x21, 88(x20)  # cfg[86] (bank 0) · THCON_SEC0_REG5_Tile_x_dim_cntx0, THCON_SEC0_REG5_Tile_x_dim_cntx1 · 0xffef0158; write 0x01000100; cfg[86] (bank 0); THCON_SEC0_REG5_Tile_x_dim_cntx0 = 256; THCON_SEC0_REG5_Tile_x_dim_cntx1 = 256
    c80: 060a2823  sw           x0, 112(x20)  # cfg[92] (bank 0) · THCON_SEC0_REG7_Offset_address, THCON_SEC0_REG7_Unpack_data_format_cntx0, THCON_SEC0_REG7_Unpack_out_data_format_cntx0, THCON_SEC0_REG7_Unpack_data_format_cntx4, THCON_SEC0_REG7_Unpack_out_data_format_cntx4 · 0xffef0170; write 0x00000000; cfg[92] (bank 0); THCON_SEC0_REG7_Offset_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx0 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx4 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx4 = 0
    c84: 060a2a23  sw           x0, 116(x20)  # cfg[93] (bank 0) · THCON_SEC0_REG7_Offset_cntx1_address, THCON_SEC0_REG7_Unpack_data_format_cntx1, THCON_SEC0_REG7_Unpack_out_data_format_cntx1, THCON_SEC0_REG7_Unpack_data_format_cntx5, THCON_SEC0_REG7_Unpack_out_data_format_cntx5 · 0xffef0174; write 0x00000000; cfg[93] (bank 0); THCON_SEC0_REG7_Offset_cntx1_address = 0; THCON_SEC0_REG7_Unpack_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx1 = 0; THCON_SEC0_REG7_Unpack_data_format_cntx5 = 0; THCON_SEC0_REG7_Unpack_out_data_format_cntx5 = 0
    c88: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    c8c: 820a8a93  addi         x21, x21, -2016  # x21 = 0xffb00820 · riscv_local_mem + 0x820
    c90: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x820 · 0xffb00820
    c94: 004a5a13  srli         x20, x20, 4
    c98: fffa0a13  addi         x20, x20, -1
    c9c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    ca0: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    ca4: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    ca8: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    cac: c8a40002  SETC16       setc16_reg=41, setc16_value=0  # thread_cfg[41] (current thread); UNPACK_MISC_CFG_CfgContextOffset_0 = 0; UNPACK_MISC_CFG_CfgContextCntReset_0 = 0; UNPACK_MISC_CFG_CfgContextCntInc_0 = 0; UNPACK_MISC_CFG_CfgContextOffset_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_1 = 0; UNPACK_MISC_CFG_CfgContextCntInc_1 = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata = 0; UNPACK_MISC_CFG_CfgContextCntReset_metadata_zstart = 0
    cb0: c8140012  SETC16       setc16_reg=5, setc16_value=4  # thread_cfg[5] (current thread); SRCA_SET_Base = 0; SRCA_SET_SetOvrdWithAddr = 1
    cb4: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    cb8: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    cbc: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    cc0: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    cc4: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    cc8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    ccc: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    cd0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    cd4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    cd8: 01507033  and          x0, x0, x21
    cdc: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    ce0: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
    ce4: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000004
    ce8: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    cec: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000001
    cf0: 42008ab7  lui          x21, 0x42008  # x21 = 0x42008000
    cf4: 0c1a8a93  addi         x21, x21, 193  # x21 = 0x420080c1
    cf8: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x420080c1; MOP template instruction · UNPACR Unpack_block_selection=0, AddrMode=1, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    cfc: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    d00: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    d04: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    d08: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    d0c: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    d10: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    d14: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    d18: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    d1c: 43800ab7  lui          x21, 0x43800  # x21 = 0x43800000
    d20: 101a8a93  addi         x21, x21, 257  # x21 = 0x43800101
    d24: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    d28: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x43800101; MOP template instruction · UNPACR_NOP Unpacker_Select=1, Stream_Id=0, Msg_Clr_Cnt=0, Set_Dvalid=1, Clr_to1_fmt_Ctrl=0, Stall_Clr_Cntrl=0, Bank_Clr_Ctrl=0, Src_ClrVal_Ctrl=0, Unpack_Pop=1
    d2c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    d30: 824c0c13  addi         x24, x24, -2012  # x24 = 0xffb00824 · riscv_local_mem + 0x824
    d34: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x824 · 0xffb00824
    d38: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_d3c:
    d3c: ffb4dc37  lui          x24, 0xffb4d  # x24 = 0xffb4d000
    d40: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4d028
    d44: 000c5a83  lhu          x21, 0(x24)  # 0xffb4d028
    d48: 414a8b33  sub          x22, x21, x20
    d4c: 010b1b13  slli         x22, x22, 16
    d50: 010b5b13  srli         x22, x22, 16
    d54: 017b7663  bgeu         x22, x23, 0x00000d60  # target 0x00000d60
    d58: 0ff0000f  fence        0xf, 0xf
    d5c: fe1ff06f  jal          x0, 0x00000d3c  # target 0x00000d3c
loc_d60:
    d60: 0ff0000f  fence        0xf, 0xf
    d64: 88100082  STALLWAIT    stall_res=8, wait_res=32  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR
    d68: 788ff001  SETADCXX     CntSetMask=1, x_end2=255, x_start=0
    d6c: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    d70: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    d74: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    d78: 8810000a  STALLWAIT    stall_res=8, wait_res=2  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0
    d7c: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    d80: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    d84: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    d88: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    d8c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    d90: 01507033  and          x0, x0, x21
    d94: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    d98: 824a8a93  addi         x21, x21, -2012  # x21 = 0xffb00824 · riscv_local_mem + 0x824
    d9c: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824
    da0: 001a0a13  addi         x20, x20, 1
    da4: 010a1a13  slli         x20, x20, 16
    da8: 010a5a13  srli         x20, x20, 16
    dac: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x824 · 0xffb00824; write runtime value
    db0: ffb4dab7  lui          x21, 0xffb4d  # x21 = 0xffb4d000
    db4: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4d020
    db8: 014aa023  sw           x20, 0(x21)  # 0xffb4d020; write runtime value
    dbc: 0ff0000f  fence        0xf, 0xf
    dc0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    dc4: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    dc8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820
    dcc: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    dd0: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    dd4: 015a0a33  add          x20, x20, x21
    dd8: 00025b37  lui          x22, 0x00025  # x22 = 0x00025000
    ddc: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00024800
    de0: 016a6663  bltu         x20, x22, 0x00000dec  # target 0x00000dec
    de4: 00002bb7  lui          x23, 0x00002  # x23 = 0x00002000
    de8: 417a0a33  sub          x20, x20, x23
loc_dec:
    dec: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    df0: 820c0c13  addi         x24, x24, -2016  # x24 = 0xffb00820 · riscv_local_mem + 0x820
    df4: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x820 · 0xffb00820; write runtime value
    df8: 00008067  jalr         x0, 0(x1)
loc_dfc:
    dfc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    e00: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_e04:
    e04: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    e08: 0feafa93  andi         x21, x21, 254
    e0c: 000a8663  beq          x21, x0, 0x00000e18  # target 0x00000e18
    e10: 0ff0000f  fence        0xf, 0xf
    e14: ff1ff06f  jal          x0, 0x00000e04  # target 0x00000e04
loc_e18:
    e18: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    e1c: 838a8a93  addi         x21, x21, -1992  # x21 = 0xffb00838 · riscv_local_mem + 0x838
    e20: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x838 · 0xffb00838
    e24: 004a5a13  srli         x20, x20, 4
    e28: fffa0a13  addi         x20, x20, -1
    e2c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    e30: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    e34: 014aa023  sw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130; write runtime value; cfg[76] (bank 0); THCON_SEC0_REG3_Base_address = runtime
    e38: 014aa223  sw           x20, 4(x21)  # cfg[77] (bank 0) · THCON_SEC0_REG3_Base_cntx1_address · 0xffef0134; write runtime value; cfg[77] (bank 0); THCON_SEC0_REG3_Base_cntx1_address = runtime
    e3c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    e40: 034a0a13  addi         x20, x20, 52  # x20 = 0xffe80034 · UNPACK_CONFIG_SYNC
loc_e44:
    e44: 000a2a83  lw           x21, 0(x20)  # UNPACK_CONFIG_SYNC · 0xffe80034
    e48: 0feafa93  andi         x21, x21, 254
    e4c: 000a8663  beq          x21, x0, 0x00000e58  # target 0x00000e58
    e50: 0ff0000f  fence        0xf, 0xf
    e54: ff1ff06f  jal          x0, 0x00000e44  # target 0x00000e44
loc_e58:
    e58: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    e5c: 840a8a93  addi         x21, x21, -1984  # x21 = 0xffb00840 · riscv_local_mem + 0x840
    e60: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x840 · 0xffb00840
    e64: 004a5a13  srli         x20, x20, 4
    e68: fffa0a13  addi         x20, x20, -1
    e6c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    e70: 1f0a8a93  addi         x21, x21, 496  # x21 = 0xffef01f0 · cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address
    e74: 014aa023  sw           x20, 0(x21)  # cfg[124] (bank 0) · THCON_SEC1_REG3_Base_address · 0xffef01f0; write runtime value; cfg[124] (bank 0); THCON_SEC1_REG3_Base_address = runtime
    e78: 014aa223  sw           x20, 4(x21)  # cfg[125] (bank 0) · THCON_SEC1_REG3_Base_cntx1_address · 0xffef01f4; write runtime value; cfg[125] (bank 0); THCON_SEC1_REG3_Base_cntx1_address = runtime
    e7c: ffef0ab7  lui          x21, 0xffef0  # x21 = 0xffef0000 · cfg[0] (bank 0) · ALU_FORMAT_SPEC_REG_SrcA_val, ALU_FORMAT_SPEC_REG_SrcA_override, ALU_FORMAT_SPEC_REG_SrcB_val, ALU_FORMAT_SPEC_REG_SrcB_override, ALU_FORMAT_SPEC_REG_Dstacc_val, ALU_FORMAT_SPEC_REG_Dstacc_override
    e80: 130a8a93  addi         x21, x21, 304  # x21 = 0xffef0130 · cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address
    e84: 000aaa03  lw           x20, 0(x21)  # cfg[76] (bank 0) · THCON_SEC0_REG3_Base_address · 0xffef0130
    e88: ffe80ab7  lui          x21, 0xffe80  # x21 = 0xffe80000 · tensix_pc_buf + 0x0
    e8c: 034a8a93  addi         x21, x21, 52  # x21 = 0xffe80034 · UNPACK_CONFIG_SYNC
    e90: 00000b13  addi         x22, x0, 0  # x22 = 0x00000000
    e94: 016aa023  sw           x22, 0(x21)  # UNPACK_CONFIG_SYNC · 0xffe80034; write 0x00000000
    e98: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    e9c: 844c0c13  addi         x24, x24, -1980  # x24 = 0xffb00844 · riscv_local_mem + 0x844
    ea0: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x844 · 0xffb00844
    ea4: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_ea8:
    ea8: ffb4bc37  lui          x24, 0xffb4b  # x24 = 0xffb4b000
    eac: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4b028
    eb0: 000c5a83  lhu          x21, 0(x24)  # 0xffb4b028
    eb4: 414a8b33  sub          x22, x21, x20
    eb8: 010b1b13  slli         x22, x22, 16
    ebc: 010b5b13  srli         x22, x22, 16
    ec0: 017b7663  bgeu         x22, x23, 0x00000ecc  # target 0x00000ecc
    ec4: 0ff0000f  fence        0xf, 0xf
    ec8: fe1ff06f  jal          x0, 0x00000ea8  # target 0x00000ea8
loc_ecc:
    ecc: 0ff0000f  fence        0xf, 0xf
    ed0: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    ed4: 83cc0c13  addi         x24, x24, -1988  # x24 = 0xffb0083c · riscv_local_mem + 0x83c
    ed8: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x83c · 0xffb0083c
    edc: 00100b93  addi         x23, x0, 1  # x23 = 0x00000001
loc_ee0:
    ee0: ffb4ac37  lui          x24, 0xffb4a  # x24 = 0xffb4a000
    ee4: 028c0c13  addi         x24, x24, 40  # x24 = 0xffb4a028
    ee8: 000c5a83  lhu          x21, 0(x24)  # 0xffb4a028
    eec: 414a8b33  sub          x22, x21, x20
    ef0: 010b1b13  slli         x22, x22, 16
    ef4: 010b5b13  srli         x22, x22, 16
    ef8: 017b7663  bgeu         x22, x23, 0x00000f04  # target 0x00000f04
    efc: 0ff0000f  fence        0xf, 0xf
    f00: fe1ff06f  jal          x0, 0x00000ee0  # target 0x00000ee0
loc_f04:
    f04: 0ff0000f  fence        0xf, 0xf
    f08: 88100182  STALLWAIT    stall_res=8, wait_res=96  # stall_res: Stall.UNPACK; wait_res: Wait.SRCA_CLR | Wait.SRCB_CLR
    f0c: 78bff001  SETADCXX     CntSetMask=1, x_end2=1023, x_start=0
    f10: 793ff001  SETADCXX     CntSetMask=2, x_end2=1023, x_start=0
    f14: 5180003d  SETADCZW     CntSetMask=3, Ch1_W=0, Ch1_Z=0, Ch0_W=0, Ch0_Z=0, BitMask=15
    f18: 88101002  STALLWAIT    stall_res=8, wait_res=1024  # stall_res: Stall.UNPACK; wait_res: Wait.TRISC_CFG
    f1c: 0a000305  UNPACR       Unpack_block_selection=1, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    f20: 08000305  UNPACR       Unpack_block_selection=0, AddrMode=0, CfgContextCntInc=0, CfgContextId=0, AddrCntContextId=0, OvrdThreadId=1, SetDatValid=1, srcb_bcast=0, ZeroWrite2=0, AutoIncContextID=0, RowSearch=0, SearchCacheFlush=0, Last=1
    f24: 8810001a  STALLWAIT    stall_res=8, wait_res=6  # stall_res: Stall.UNPACK; wait_res: Wait.UNPACK0 | Wait.UNPACK1
    f28: 94000202  SEMGET       sem_sel=32  # sem_sel: Sem.UNPACK_SYNC
    f2c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    f30: 004a0a13  addi         x20, x20, 4  # x20 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    f34: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    f38: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    f3c: 01507033  and          x0, x0, x21
    f40: ffb01ab7  lui          x21, 0xffb01  # x21 = 0xffb01000
    f44: 83ca8a93  addi         x21, x21, -1988  # x21 = 0xffb0083c · riscv_local_mem + 0x83c
    f48: 000aaa03  lw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c
    f4c: 001a0a13  addi         x20, x20, 1
    f50: 010a1a13  slli         x20, x20, 16
    f54: 010a5a13  srli         x20, x20, 16
    f58: 014aa023  sw           x20, 0(x21)  # riscv_local_mem + 0x83c · 0xffb0083c; write runtime value
    f5c: ffb4aab7  lui          x21, 0xffb4a  # x21 = 0xffb4a000
    f60: 020a8a93  addi         x21, x21, 32  # x21 = 0xffb4a020
    f64: 014aa023  sw           x20, 0(x21)  # 0xffb4a020; write runtime value
    f68: 0ff0000f  fence        0xf, 0xf
    f6c: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    f70: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    f74: 000c2a03  lw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838
    f78: 00001ab7  lui          x21, 0x00001  # x21 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    f7c: 800a8a93  addi         x21, x21, -2048  # x21 = 0x00000800
    f80: 015a0a33  add          x20, x20, x21
    f84: 0001cb37  lui          x22, 0x0001c  # x22 = 0x0001c000
    f88: 016a6663  bltu         x20, x22, 0x00000f94  # target 0x00000f94
    f8c: 00004bb7  lui          x23, 0x00004  # x23 = 0x00004000
    f90: 417a0a33  sub          x20, x20, x23
loc_f94:
    f94: ffb01c37  lui          x24, 0xffb01  # x24 = 0xffb01000
    f98: 838c0c13  addi         x24, x24, -1992  # x24 = 0xffb00838 · riscv_local_mem + 0x838
    f9c: 014c2023  sw           x20, 0(x24)  # riscv_local_mem + 0x838 · 0xffb00838; write runtime value
    fa0: 00008067  jalr         x0, 0(x1)
    fa4:           j FW_TRISC0+4   # return to firmware, linked at install
