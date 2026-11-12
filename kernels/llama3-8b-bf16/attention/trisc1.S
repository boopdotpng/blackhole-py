# llama3 8b-bf16 decode: attention, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: 100002c4  REPLAY       start_idx=0, len=11, execute_while_loading=0, load_mode=1
      4: c0038001  SFPLOAD      lreg_ind=0, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[0]; not executed here
      8: c0438101  SFPLOAD      lreg_ind=1, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L1; Record replay[1]; not executed here
      c: c0838201  SFPLOAD      lreg_ind=2, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L2; Record replay[2]; not executed here
     10: c0c38301  SFPLOAD      lreg_ind=3, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L3; Record replay[3]; not executed here
     14: 1800a502  SFPMUL       lreg_src_a=0, lreg_src_b=2, lreg_src_c=9, lreg_dest=4, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L4; Record replay[4]; not executed here
     18: 3c000002  SFPNOP         # Record replay[5]; not executed here
     1c: 1004d142  SFPMAD       lreg_src_a=1, lreg_src_b=3, lreg_src_c=4, lreg_dest=5, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L3; lreg_src_c: L4; lreg_dest: L5; Record replay[6]; not executed here
     20: 3c000002  SFPNOP         # Record replay[7]; not executed here
     24: 38001546  SFPSTOCHRND  rnd_mode=0, imm8_math=0, lreg_src_b=0, lreg_src_c=5, lreg_dest=5, instr_mod1=1  # lreg_src_b: L0; lreg_src_c: L5; lreg_dest: L5; Record replay[8]; not executed here
     28: c9438001  SFPSTORE     lreg_ind=5, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L5; Record replay[9]; not executed here
     2c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[10]; not executed here
     30: 100b0104  REPLAY       start_idx=11, len=4, execute_while_loading=0, load_mode=1
     34: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0; Record replay[11]; not executed here
     38: c4200001  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=0  # lreg_ind: L0; Record replay[12]; not executed here
     3c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[13]; not executed here
     40: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[14]; not executed here
     44: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     48: 90830313  addi         x6, x6, -1784  # x6 = 0x0000e908
     4c: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x0000e908
     50: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     54: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     58: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     5c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     60: 0063fa63  bgeu         x7, x6, 0x00000074  # target 0x00000074
     64: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     68: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     6c: 0063f463  bgeu         x7, x6, 0x00000074  # target 0x00000074
     70: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_74:
     74: 2a5278e3  bgeu         x4, x5, 0x00000b24  # target 0x00000b24
     78: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     7c: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     80: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     84: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     88: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     8c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     90: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     94: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     98: 00507033  and          x0, x0, x5
     9c: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     a0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     a4: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     a8: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     ac: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     b0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     b4: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     b8: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     bc: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
     c0: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     c4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     c8: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
     cc: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     d0: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     d4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     d8: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
     dc: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     e0: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     e4: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     e8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     ec: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
     f0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     f4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     fc: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    100: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    104: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    108: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    10c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    110: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    114: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    118: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    11c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    120: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    124: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    128: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    12c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    130: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    134: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    138: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    13c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    140: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    144: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    148: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    14c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    150: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    154: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    158: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    15c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    160: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    164: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    168: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    16c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    170: 3c000002  SFPNOP
    174: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    178: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    17c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    180: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    184: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    188: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    18c: 01507033  and          x0, x0, x21
    190: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    194: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    198: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    19c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    1a0: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    1a4: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    1a8: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    1ac: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    1b0: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    1b4: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1b8: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1bc: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    1c0: 0b0a8a93  addi         x21, x21, 176  # x21 = 0x040000b0
    1c4: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    1c8: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    1cc: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    1d0: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    1d4: 0b0a8a93  addi         x21, x21, 176  # x21 = 0x040000b0
    1d8: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    1dc: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    1e0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1e4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1e8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1ec: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1f0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    1f4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1fc: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    200: 79000313  addi         x6, x0, 1936  # x6 = 0x00000790
    204: 00032203  lw           x4, 0(x6)  # param kv_blocks; 0x00000790
    208: fff20293  addi         x5, x4, -1
    20c: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    210: 90840413  addi         x8, x8, -1784  # x8 = 0x0000e908
    214: 00042303  lw           x6, 0(x8)  # param attention_phase; 0x0000e908
    218: 79000513  addi         x10, x0, 1936  # x10 = 0x00000790
    21c: 00052403  lw           x8, 0(x10)  # param kv_blocks; 0x00000790
    220: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
    224: 00400493  addi         x9, x0, 4  # x9 = 0x00000004
    228: 0084fa63  bgeu         x9, x8, 0x0000023c  # target 0x0000023c
    22c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    230: 08000493  addi         x9, x0, 128  # x9 = 0x00000080
    234: 0084f463  bgeu         x9, x8, 0x0000023c  # target 0x0000023c
    238: 00c00393  addi         x7, x0, 12  # x7 = 0x0000000c
loc_23c:
    23c: 0272f433  remu         x8, x5, x7
    240: 0272d2b3  divu         x5, x5, x7
    244: 00640463  beq          x8, x6, 0x0000024c  # target 0x0000024c
    248: fff00293  addi         x5, x0, -1  # x5 = 0xffffffff
loc_24c:
    24c: 00720233  add          x4, x4, x7
    250: fff20213  addi         x4, x4, -1
    254: 40620233  sub          x4, x4, x6
    258: 02725233  divu         x4, x4, x7
    25c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    260: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    264: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    268: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    26c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    270: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    274: 3c000002  SFPNOP
    278: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    27c: 0ad000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x00000280
    280: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    284: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    288: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    28c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    290: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    294: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    298: 3c000002  SFPNOP
    29c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2a0: 089000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x000002a4
    2a4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2a8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2ac: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    2b0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2b4: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2b8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2bc: 3c000002  SFPNOP
    2c0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2c4: 065000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x000002c8
    2c8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2cc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2d0: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    2d4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2d8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2dc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2e0: 3c000002  SFPNOP
    2e4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2e8: 041000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x000002ec
    2ec: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2f0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2f4: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    2f8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2fc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    300: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    304: 3c000002  SFPNOP
    308: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    30c: 01d000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x00000310
    310: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    314: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    318: c8040702  SETC16       setc16_reg=1, setc16_value=448  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 448
    31c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    320: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    324: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    328: 3c000002  SFPNOP
    32c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    330: 7f8000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x00000334
    334: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    338: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    33c: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    340: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    344: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    348: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    34c: 3c000002  SFPNOP
    350: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    354: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    358: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_35c:
    35c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_360:
    360: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    364: c420fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16256  # lreg_ind: L0
    368: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    36c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    370: fffa8a93  addi         x21, x21, -1
    374: fe0a96e3  bne          x21, x0, 0x00000360  # target 0x00000360
    378: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    37c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    380: fffa0a13  addi         x20, x20, -1
    384: fc0a1ce3  bne          x20, x0, 0x0000035c  # target 0x0000035c
    388: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    38c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    390: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    394: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    398: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    39c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    3a0: 3c000002  SFPNOP
    3a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3a8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    3ac: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    3b0: c423fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=65408  # lreg_ind: L0
    3b4: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    3b8: c80f8509  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L0
    3bc: c80f8541  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L0
    3c0: c80f8549  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L0
    3c4: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    3c8: c4200001  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=0  # lreg_ind: L0
    3cc: c80f8601  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L0
    3d0: c80f8609  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=386  # lreg_ind: L0
    3d4: c80f8641  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=400  # lreg_ind: L0
    3d8: c80f8649  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=402  # lreg_ind: L0
    3dc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    3e0: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    3e4: 00020393  addi         x7, x4, 0
loc_3e8:
    3e8: 70737a63  bgeu         x6, x7, 0x00000afc  # target 0x00000afc
    3ec: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    3f0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    3f4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    3f8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    3fc: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    400: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    404: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    408: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    40c: c8350082  SETC16       setc16_reg=13, setc16_value=16416  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 32; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    410: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    414: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    418: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    41c: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    420: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    424: c841c142  SETC16       setc16_reg=16, setc16_value=28752  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 16; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    428: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    42c: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    430: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    434: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    438: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    43c: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    440: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    444: 10100204  REPLAY       start_idx=16, len=8, execute_while_loading=0, load_mode=1
    448: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[16]; not executed here
    44c: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[17]; not executed here
    450: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[18]; not executed here
    454: 98020000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=2, dst=0  # Record replay[19]; not executed here
    458: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[20]; not executed here
    45c: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[21]; not executed here
    460: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[22]; not executed here
    464: 98040000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=4, dst=0  # Record replay[23]; not executed here
    468: 10180204  REPLAY       start_idx=24, len=8, execute_while_loading=0, load_mode=1
    46c: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[24]; not executed here
    470: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[25]; not executed here
    474: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[26]; not executed here
    478: 98020000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=2, dst=0  # Record replay[27]; not executed here
    47c: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[28]; not executed here
    480: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[29]; not executed here
    484: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[30]; not executed here
    488: 98050000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=5, dst=0  # Record replay[31]; not executed here
    48c: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    490: 00440413  addi         x8, x8, 4  # x8 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    494: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    498: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    49c: 00907033  and          x0, x0, x9
    4a0: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    4a4: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    4a8: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    4ac: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    4b0: 00907033  and          x0, x0, x9
    4b4: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    4b8: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    4bc: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000001
    4c0: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    4c4: 00942223  sw           x9, 4(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    4c8: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    4cc: 00942423  sw           x9, 8(x8)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    4d0: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    4d4: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    4d8: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4dc: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    4e0: 00942823  sw           x9, 16(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    4e4: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    4e8: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    4ec: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    4f0: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    4f4: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    4f8: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    4fc: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    500: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    504: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    508: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    50c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    510: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    514: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    518: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    51c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    520: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    524: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    528: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    52c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    530: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    534: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    538: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    53c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    540: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    544: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    548: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    54c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    550: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    554: 0c531463  bne          x6, x5, 0x0000061c  # target 0x0000061c
    558: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    55c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    560: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    564: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    568: 3c000002  SFPNOP
    56c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    570: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    574: 79400513  addi         x10, x0, 1940  # x10 = 0x00000794
    578: 00052403  lw           x8, 0(x10)  # param valid_columns; 0x00000794
    57c: 712204b7  lui          x9, 0x71220  # x9 = 0x71220000
    580: 0084e4b3  or           x9, x9, x8
    584: ffe40537  lui          x10, 0xffe40  # x10 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    588: 00952023  sw           x9, 0(x10)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    58c: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    590: c523fe01  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=65408  # lreg_ind: L4
    594: c548003d  SFPLOADI     lreg_ind=5, instr_mod0=2, imm16=15  # lreg_ind: L5
    598: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    59c: e4000455  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    5a0: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    5a4: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5a8: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    5ac: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    5b0: c90f8001  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L4
    5b4: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5b8: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    5bc: e4004455  SFPIADD      imm12_math=1, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    5c0: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    5c4: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5c8: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    5cc: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    5d0: c90f8009  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L4
    5d4: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5d8: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    5dc: e4040455  SFPIADD      imm12_math=16, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    5e0: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    5e4: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5e8: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    5ec: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    5f0: c90f8041  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L4
    5f4: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    5f8: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    5fc: e4044455  SFPIADD      imm12_math=17, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    600: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    604: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    608: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    60c: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    610: c90f8049  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L4
    614: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    618: 88042002  STALLWAIT    stall_res=2, wait_res=2048  # stall_res: Stall.SYNC; wait_res: Wait.SFPU
loc_61c:
    61c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    620: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    624: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    628: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    62c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    630: 3c000002  SFPNOP
    634: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    638: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    63c: c52813cd  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=1267  # lreg_ind: L4
    640: c520f6d5  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=15797  # lreg_ind: L4
    644: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    648: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    64c: 3c000002  SFPNOP
    650: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    654: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    658: 18052442  SFPMUL       lreg_src_a=1, lreg_src_b=4, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    65c: 3c000002  SFPNOP
    660: c84f8009  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    664: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    668: 18092482  SFPMUL       lreg_src_a=2, lreg_src_b=4, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    66c: 3c000002  SFPNOP
    670: c88f8041  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    674: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    678: 180d24c2  SFPMUL       lreg_src_a=3, lreg_src_b=4, lreg_src_c=9, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L3
    67c: 3c000002  SFPNOP
    680: c8cf8049  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    684: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    688: 3c000002  SFPNOP
    68c: 480004c6  SFPSWAP      imm12_math=0, lreg_src_c=1, lreg_dest=3, instr_mod1=1  # lreg_src_c: L1; lreg_dest: L3
    690: 3c000002  SFPNOP
    694: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    698: 3c000002  SFPNOP
    69c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    6a0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6a4: 3c000002  SFPNOP
    6a8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6ac: 3c000002  SFPNOP
    6b0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6b4: 3c000002  SFPNOP
    6b8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6bc: 3c000002  SFPNOP
    6c0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6c4: 3c000002  SFPNOP
    6c8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    6cc: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6d0: 3c000002  SFPNOP
    6d4: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6d8: 3c000002  SFPNOP
    6dc: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6e0: 3c000002  SFPNOP
    6e4: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    6e8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6ec: 3c000002  SFPNOP
    6f0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    6f4: 3c000002  SFPNOP
    6f8: c08f8501  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L2
    6fc: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    700: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    704: 3c000002  SFPNOP
    708: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    70c: c80f8509  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L0
    710: c80f8541  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L0
    714: c80f8549  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L0
    718: 1002cd42  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=5, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L5
    71c: 3c000002  SFPNOP
    720: c94f8701  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L5
    724: c94f8709  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L5
    728: c94f8741  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L5
    72c: c94f8749  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L5
    730: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    734: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    738: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    73c: 3c000002  SFPNOP
    740: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    744: c00f8009  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    748: c04f8509  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L1
    74c: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    750: 3c000002  SFPNOP
    754: c80f8009  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    758: c00f8041  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    75c: c04f8541  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L1
    760: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    764: 3c000002  SFPNOP
    768: c80f8041  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    76c: c00f8049  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    770: c04f8549  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L1
    774: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    778: 3c000002  SFPNOP
    77c: c80f8049  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    780: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    784: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    788: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    78c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    790: 3c000002  SFPNOP
    794: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    798: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    79c: 410000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000007a0
    7a0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    7a4: 408000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000007a8
    7a8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    7ac: 400000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000007b0
    7b0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    7b4: 3f8000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000007b8
    7b8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    7bc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    7c0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    7c4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    7c8: 3c000002  SFPNOP
    7cc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    7d0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    7d4: 46c000ef  jal          x1, 0x00000c40  # target 0x00000c40; x1 = 0x000007d8
    7d8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    7dc: 464000ef  jal          x1, 0x00000c40  # target 0x00000c40; x1 = 0x000007e0
    7e0: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    7e4: 45c000ef  jal          x1, 0x00000c40  # target 0x00000c40; x1 = 0x000007e8
    7e8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    7ec: 454000ef  jal          x1, 0x00000c40  # target 0x00000c40; x1 = 0x000007f0
    7f0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    7f4: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    7f8: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    7fc: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    800: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    804: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    808: 3c000002  SFPNOP
    80c: 14284c42  SFPADD       lreg_src_a=10, lreg_src_b=1, lreg_src_c=3, lreg_dest=1, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L1; lreg_src_c: L3; lreg_dest: L1
    810: 3c000002  SFPNOP
    814: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    818: 3c000002  SFPNOP
    81c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    820: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    824: 3c000002  SFPNOP
    828: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    82c: 3c000002  SFPNOP
    830: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    834: 3c000002  SFPNOP
    838: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    83c: 3c000002  SFPNOP
    840: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    844: 3c000002  SFPNOP
    848: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    84c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    850: 3c000002  SFPNOP
    854: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    858: 3c000002  SFPNOP
    85c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    860: 3c000002  SFPNOP
    864: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    868: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    86c: 3c000002  SFPNOP
    870: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    874: 3c000002  SFPNOP
    878: c08f8601  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L2
    87c: c0cf8701  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L3
    880: 1008c002  SFPMAD       lreg_src_a=2, lreg_src_b=3, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L3; lreg_src_c: L0; lreg_dest: L0
    884: 3c000002  SFPNOP
    888: c80f8601  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L0
    88c: c80f8609  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=386  # lreg_ind: L0
    890: c80f8641  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=400  # lreg_ind: L0
    894: c80f8649  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=402  # lreg_ind: L0
    898: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    89c: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    8a0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8a4: 3c000002  SFPNOP
    8a8: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    8ac: c00f8109  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    8b0: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    8b4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8b8: 3c000002  SFPNOP
    8bc: c80f8109  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    8c0: c00f8141  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    8c4: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    8c8: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8cc: 3c000002  SFPNOP
    8d0: c80f8141  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    8d4: c00f8149  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    8d8: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    8dc: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8e0: 3c000002  SFPNOP
    8e4: c80f8149  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    8e8: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    8ec: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    8f0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8f4: 3c000002  SFPNOP
    8f8: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    8fc: c00f8209  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    900: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    904: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    908: 3c000002  SFPNOP
    90c: c80f8209  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    910: c00f8241  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    914: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    918: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    91c: 3c000002  SFPNOP
    920: c80f8241  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    924: c00f8249  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    928: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    92c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    930: 3c000002  SFPNOP
    934: c80f8249  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    938: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    93c: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    940: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    944: 3c000002  SFPNOP
    948: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    94c: c00f8309  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    950: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    954: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    958: 3c000002  SFPNOP
    95c: c80f8309  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    960: c00f8341  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    964: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    968: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    96c: 3c000002  SFPNOP
    970: c80f8341  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    974: c00f8349  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    978: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    97c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    980: 3c000002  SFPNOP
    984: c80f8349  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    988: c00f8401  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    98c: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    990: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    994: 3c000002  SFPNOP
    998: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    99c: c00f8409  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    9a0: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    9a4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    9a8: 3c000002  SFPNOP
    9ac: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    9b0: c00f8441  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    9b4: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    9b8: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    9bc: 3c000002  SFPNOP
    9c0: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    9c4: c00f8449  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    9c8: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    9cc: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    9d0: 3c000002  SFPNOP
    9d4: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    9d8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    9dc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    9e0: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    9e4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    9e8: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    9ec: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    9f0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    9f4: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    9f8: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    9fc: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    a00: c8350042  SETC16       setc16_reg=13, setc16_value=16400  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 16; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    a04: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    a08: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    a0c: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    a10: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    a14: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    a18: c841c182  SETC16       setc16_reg=16, setc16_value=28768  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 32; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    a1c: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    a20: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    a24: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    a28: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    a2c: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    a30: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a34: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    a38: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    a3c: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    a40: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    a44: 00907033  and          x0, x0, x9
    a48: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    a4c: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    a50: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000001
    a54: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    a58: 00942223  sw           x9, 4(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    a5c: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    a60: 00942423  sw           x9, 8(x8)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    a64: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    a68: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    a6c: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a70: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    a74: 00942823  sw           x9, 16(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    a78: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    a7c: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    a80: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    a84: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    a88: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    a8c: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    a90: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    a94: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    a98: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a9c: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    aa0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    aa4: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    aa8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    aac: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    ab0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ab4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    ab8: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    abc: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    ac0: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    ac4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    ac8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    acc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ad0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    ad4: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ad8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    adc: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    ae0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    ae4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    ae8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    aec: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    af0: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    af4: 00130313  addi         x6, x6, 1
    af8: 8f1ff06f  jal          x0, 0x000003e8  # target 0x000003e8
loc_afc:
    afc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    b00: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    b04: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    b08: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    b0c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    b10: 3c000002  SFPNOP
    b14: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b18: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    b1c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    b20: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
loc_b24:
    b24: 1940006f  jal          x0, 0x00000cb8  # target 0x00000cb8
loc_b28:
    b28: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    b2c: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    b30: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    b34: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    b38: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    b3c: 01507033  and          x0, x0, x21
    b40: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    b44: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    b48: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    b4c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    b50: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    b54: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    b58: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    b5c: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    b60: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    b64: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    b68: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    b6c: 0402cab7  lui          x21, 0x0402c  # x21 = 0x0402c000
    b70: 040a8a93  addi         x21, x21, 64  # x21 = 0x0402c040
    b74: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x0402c040; MOP template instruction · REPLAY start_idx=11, len=4, execute_while_loading=0, load_mode=0
    b78: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    b7c: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    b80: 0402cab7  lui          x21, 0x0402c  # x21 = 0x0402c000
    b84: 040a8a93  addi         x21, x21, 64  # x21 = 0x0402c040
    b88: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x0402c040; MOP template instruction · REPLAY start_idx=11, len=4, execute_while_loading=0, load_mode=0
    b8c: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x0402c040; MOP template instruction · REPLAY start_idx=11, len=4, execute_while_loading=0, load_mode=0
    b90: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b94: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b98: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b9c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    ba0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    ba4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    ba8: 00008067  jalr         x0, 0(x1)
loc_bac:
    bac: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    bb0: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    bb4: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    bb8: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    bbc: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    bc0: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    bc4: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    bc8: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    bcc: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    bd0: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    bd4: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    bd8: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    bdc: c00f8701  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L0
    be0: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    be4: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    be8: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    bec: 3c000002  SFPNOP
    bf0: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    bf4: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    bf8: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    bfc: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    c00: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    c04: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    c08: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    c0c: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    c10: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    c14: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    c18: c10f8701  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L4
    c1c: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    c20: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    c24: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    c28: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    c2c: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    c30: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    c34: c80f8701  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L0
    c38: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    c3c: 00008067  jalr         x0, 0(x1)
loc_c40:
    c40: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    c44: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    c48: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    c4c: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    c50: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    c54: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    c58: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    c5c: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    c60: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    c64: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    c68: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    c6c: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    c70: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    c74: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    c78: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    c7c: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    c80: 3c000002  SFPNOP
    c84: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    c88: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    c8c: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    c90: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    c94: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    c98: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    c9c: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    ca0: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    ca4: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    ca8: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    cac: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    cb0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    cb4: 00008067  jalr         x0, 0(x1)
    cb8:           j FW_TRISC1+4   # return to firmware, linked at install
