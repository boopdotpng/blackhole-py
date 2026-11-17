# llama3 1b decode: attention, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: 10000244  REPLAY       start_idx=0, len=9, execute_while_loading=0, load_mode=1
      4: c0038001  SFPLOAD      lreg_ind=0, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[0]; not executed here
      8: c0438101  SFPLOAD      lreg_ind=1, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L1; Record replay[1]; not executed here
      c: c0838201  SFPLOAD      lreg_ind=2, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L2; Record replay[2]; not executed here
     10: c0c38301  SFPLOAD      lreg_ind=3, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L3; Record replay[3]; not executed here
     14: 1800a502  SFPMUL       lreg_src_a=0, lreg_src_b=2, lreg_src_c=9, lreg_dest=4, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L4; Record replay[4]; not executed here
     18: 1004d142  SFPMAD       lreg_src_a=1, lreg_src_b=3, lreg_src_c=4, lreg_dest=5, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L3; lreg_src_c: L4; lreg_dest: L5; Record replay[5]; not executed here
     1c: 38001546  SFPSTOCHRND  rnd_mode=0, imm8_math=0, lreg_src_b=0, lreg_src_c=5, lreg_dest=5, instr_mod1=1  # lreg_src_b: L0; lreg_src_c: L5; lreg_dest: L5; Record replay[6]; not executed here
     20: c9438001  SFPSTORE     lreg_ind=5, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L5; Record replay[7]; not executed here
     24: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[8]; not executed here
     28: 10090104  REPLAY       start_idx=9, len=4, execute_while_loading=0, load_mode=1
     2c: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0; Record replay[9]; not executed here
     30: c4200001  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=0  # lreg_ind: L0; Record replay[10]; not executed here
     34: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[11]; not executed here
     38: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[12]; not executed here
     3c: 10100204  REPLAY       start_idx=16, len=8, execute_while_loading=0, load_mode=1
     40: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[16]; not executed here
     44: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[17]; not executed here
     48: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[18]; not executed here
     4c: 98020000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=2, dst=0  # Record replay[19]; not executed here
     50: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[20]; not executed here
     54: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[21]; not executed here
     58: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[22]; not executed here
     5c: 98040000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=4, dst=0  # Record replay[23]; not executed here
     60: 10180204  REPLAY       start_idx=24, len=8, execute_while_loading=0, load_mode=1
     64: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[24]; not executed here
     68: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[25]; not executed here
     6c: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[26]; not executed here
     70: 98020000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=2, dst=0  # Record replay[27]; not executed here
     74: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[28]; not executed here
     78: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[29]; not executed here
     7c: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[30]; not executed here
     80: 98050000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=5, dst=0  # Record replay[31]; not executed here
     84: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     88: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
     8c: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
     90: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     94: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     98: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     9c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     a0: 0063fa63  bgeu         x7, x6, 0x000000b4  # target 0x000000b4
     a4: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     a8: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
     ac: 0063f463  bgeu         x7, x6, 0x000000b4  # target 0x000000b4
     b0: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_b4:
     b4: 3a527ce3  bgeu         x4, x5, 0x00000c6c  # target 0x00000c6c
     b8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     bc: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     c0: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     c4: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     c8: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     cc: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     d0: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     d4: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     d8: 00507033  and          x0, x0, x5
     dc: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     e0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     e4: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     e8: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     ec: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     f0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     f4: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     f8: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     fc: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
    100: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    104: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    108: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    10c: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    110: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    114: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    118: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    11c: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    120: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    124: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    128: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    12c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    130: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    134: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    138: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    13c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    140: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    144: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    148: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    14c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    150: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    154: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    158: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    15c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    160: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    164: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    168: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    16c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    170: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    174: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    178: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    17c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    180: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    184: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    188: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    18c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    190: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    194: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    198: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    19c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    1a0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    1a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1a8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    1ac: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    1b0: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    1b4: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    1b8: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    1bc: 01507033  and          x0, x0, x21
    1c0: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    1c4: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    1c8: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    1cc: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    1d0: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    1d4: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    1d8: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    1dc: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1e0: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1e4: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    1e8: 090a8a93  addi         x21, x21, 144  # x21 = 0x04000090
    1ec: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04000090; MOP template instruction · REPLAY start_idx=0, len=9, execute_while_loading=0, load_mode=0
    1f0: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04000090; MOP template instruction · REPLAY start_idx=0, len=9, execute_while_loading=0, load_mode=0
    1f4: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04000090; MOP template instruction · REPLAY start_idx=0, len=9, execute_while_loading=0, load_mode=0
    1f8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1fc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    200: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    204: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    208: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    20c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    210: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    214: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    218: 79000313  addi         x6, x0, 1936  # x6 = 0x00000790
    21c: 00032203  lw           x4, 0(x6)  # param kv_blocks; 0x00000790
    220: fff20293  addi         x5, x4, -1
    224: 00012437  lui          x8, 0x00012  # x8 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    228: 90440413  addi         x8, x8, -1788  # x8 = 0x00011904
    22c: 00042303  lw           x6, 0(x8)  # param attention_phase; 0x00011904
    230: 79000513  addi         x10, x0, 1936  # x10 = 0x00000790
    234: 00052403  lw           x8, 0(x10)  # param kv_blocks; 0x00000790
    238: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
    23c: 00400493  addi         x9, x0, 4  # x9 = 0x00000004
    240: 0084fa63  bgeu         x9, x8, 0x00000254  # target 0x00000254
    244: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    248: 05000493  addi         x9, x0, 80  # x9 = 0x00000050
    24c: 0084f463  bgeu         x9, x8, 0x00000254  # target 0x00000254
    250: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
loc_254:
    254: 0272f433  remu         x8, x5, x7
    258: 0272d2b3  divu         x5, x5, x7
    25c: 00640463  beq          x8, x6, 0x00000264  # target 0x00000264
    260: fff00293  addi         x5, x0, -1  # x5 = 0xffffffff
loc_264:
    264: 00720233  add          x4, x4, x7
    268: fff20213  addi         x4, x4, -1
    26c: 40620233  sub          x4, x4, x6
    270: 02725233  divu         x4, x4, x7
    274: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    278: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    27c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    280: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    284: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    288: 1e9000ef  jal          x1, 0x00000c70  # target 0x00000c70; x1 = 0x0000028c
    28c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    290: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    294: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    298: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    29c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2a0: 1d1000ef  jal          x1, 0x00000c70  # target 0x00000c70; x1 = 0x000002a4
    2a4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2a8: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    2ac: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2b0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2b4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2b8: 1b9000ef  jal          x1, 0x00000c70  # target 0x00000c70; x1 = 0x000002bc
    2bc: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2c0: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    2c4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2c8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2cc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2d0: 1a1000ef  jal          x1, 0x00000c70  # target 0x00000c70; x1 = 0x000002d4
    2d4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2d8: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    2dc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2e0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2e4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2e8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    2ec: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_2f0:
    2f0: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_2f4:
    2f4: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    2f8: c420fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16256  # lreg_ind: L0
    2fc: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    300: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    304: fffa8a93  addi         x21, x21, -1
    308: fe0a96e3  bne          x21, x0, 0x000002f4  # target 0x000002f4
    30c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    310: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    314: fffa0a13  addi         x20, x20, -1
    318: fc0a1ce3  bne          x20, x0, 0x000002f0  # target 0x000002f0
    31c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    320: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    324: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    328: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    32c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    330: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    334: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    338: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    33c: c423fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=65408  # lreg_ind: L0
    340: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    344: c80f8309  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    348: c80f8341  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    34c: c80f8349  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    350: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    354: c4200001  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=0  # lreg_ind: L0
    358: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    35c: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    360: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    364: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    368: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    36c: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    370: 00020393  addi         x7, x4, 0
loc_374:
    374: 4c737a63  bgeu         x6, x7, 0x00000848  # target 0x00000848
    378: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    37c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    380: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    384: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    388: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    38c: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    390: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    394: c8350082  SETC16       setc16_reg=13, setc16_value=16416  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 32; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    398: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    39c: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    3a0: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    3a4: c841c142  SETC16       setc16_reg=16, setc16_value=28752  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 16; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    3a8: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    3ac: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    3b0: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    3b4: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    3b8: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    3bc: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    3c0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3c4: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    3c8: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    3cc: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    3d0: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    3d4: 00907033  and          x0, x0, x9
    3d8: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    3dc: 00440413  addi         x8, x8, 4  # x8 = 0xffb80004 · MopCfg[1] · InnerCount / Flags
    3e0: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    3e4: 00942023  sw           x9, 0(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    3e8: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    3ec: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    3f0: 00942423  sw           x9, 8(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3f4: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    3f8: 00942623  sw           x9, 12(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    3fc: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    400: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    404: 00942823  sw           x9, 16(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    408: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    40c: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    410: 00942a23  sw           x9, 20(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    414: 00942c23  sw           x9, 24(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    418: 00942e23  sw           x9, 28(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    41c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    420: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    424: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    428: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    42c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    430: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    434: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    438: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    43c: 0c531263  bne          x6, x5, 0x00000500  # target 0x00000500
    440: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    444: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    448: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    44c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    450: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    454: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    458: 79400513  addi         x10, x0, 1940  # x10 = 0x00000794
    45c: 00052403  lw           x8, 0(x10)  # param valid_columns; 0x00000794
    460: 712204b7  lui          x9, 0x71220  # x9 = 0x71220000
    464: 0084e4b3  or           x9, x9, x8
    468: ffe40537  lui          x10, 0xffe40  # x10 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    46c: 00952023  sw           x9, 0(x10)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    470: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    474: c523fe01  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=65408  # lreg_ind: L4
    478: c548003d  SFPLOADI     lreg_ind=5, instr_mod0=2, imm16=15  # lreg_ind: L5
    47c: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    480: e4000455  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    484: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    488: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    48c: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    490: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    494: c90f8001  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L4
    498: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    49c: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    4a0: e4004455  SFPIADD      imm12_math=1, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    4a4: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    4a8: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4ac: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    4b0: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    4b4: c90f8009  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L4
    4b8: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4bc: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    4c0: e4040455  SFPIADD      imm12_math=16, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    4c4: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    4c8: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4cc: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    4d0: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    4d4: c90f8041  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L4
    4d8: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4dc: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    4e0: e4044455  SFPIADD      imm12_math=17, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    4e4: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    4e8: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4ec: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    4f0: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    4f4: c90f8049  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L4
    4f8: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4fc: 88042002  STALLWAIT    stall_res=2, wait_res=2048  # stall_res: Stall.SYNC; wait_res: Wait.SFPU
loc_500:
    500: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    504: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    508: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    50c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    510: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    514: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    518: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    51c: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    520: c520f801  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=15872  # lreg_ind: L4
    524: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    528: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    52c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    530: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    534: 18052442  SFPMUL       lreg_src_a=1, lreg_src_b=4, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    538: c84f8009  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    53c: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    540: 18092482  SFPMUL       lreg_src_a=2, lreg_src_b=4, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    544: c88f8041  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    548: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    54c: 180d24c2  SFPMUL       lreg_src_a=3, lreg_src_b=4, lreg_src_c=9, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L3
    550: c8cf8049  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    554: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    558: 480004c6  SFPSWAP      imm12_math=0, lreg_src_c=1, lreg_dest=3, instr_mod1=1  # lreg_src_c: L1; lreg_dest: L3
    55c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    560: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    564: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    568: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    56c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    570: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    574: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    578: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    57c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    580: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    584: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    588: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    58c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    590: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    594: c08f8301  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L2
    598: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    59c: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    5a0: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    5a4: c80f8309  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    5a8: c80f8341  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    5ac: c80f8349  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    5b0: 1002cd42  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=5, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L5
    5b4: c94f8501  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L5
    5b8: c94f8509  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L5
    5bc: c94f8541  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L5
    5c0: c94f8549  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L5
    5c4: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    5c8: c04f8301  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L1
    5cc: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    5d0: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    5d4: c00f8009  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    5d8: c04f8309  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L1
    5dc: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    5e0: c80f8009  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    5e4: c00f8041  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    5e8: c04f8341  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L1
    5ec: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    5f0: c80f8041  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    5f4: c00f8049  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    5f8: c04f8349  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L1
    5fc: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    600: c80f8049  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    604: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    608: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    60c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    610: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    614: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    618: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    61c: 6a4000ef  jal          x1, 0x00000cc0  # target 0x00000cc0; x1 = 0x00000620
    620: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    624: 69c000ef  jal          x1, 0x00000cc0  # target 0x00000cc0; x1 = 0x00000628
    628: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    62c: 694000ef  jal          x1, 0x00000cc0  # target 0x00000cc0; x1 = 0x00000630
    630: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    634: 68c000ef  jal          x1, 0x00000cc0  # target 0x00000cc0; x1 = 0x00000638
    638: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    63c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    640: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    644: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    648: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    64c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    650: 700000ef  jal          x1, 0x00000d50  # target 0x00000d50; x1 = 0x00000654
    654: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    658: 6f8000ef  jal          x1, 0x00000d50  # target 0x00000d50; x1 = 0x0000065c
    65c: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    660: 6f0000ef  jal          x1, 0x00000d50  # target 0x00000d50; x1 = 0x00000664
    664: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    668: 6e8000ef  jal          x1, 0x00000d50  # target 0x00000d50; x1 = 0x0000066c
    66c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    670: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    674: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    678: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    67c: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    680: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    684: 14284c42  SFPADD       lreg_src_a=10, lreg_src_b=1, lreg_src_c=3, lreg_dest=1, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L1; lreg_src_c: L3; lreg_dest: L1
    688: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    68c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    690: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    694: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    698: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    69c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6a0: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    6a4: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    6a8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6ac: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6b0: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    6b4: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    6b8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6bc: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    6c0: c08f8401  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L2
    6c4: c0cf8501  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L3
    6c8: 1008c002  SFPMAD       lreg_src_a=2, lreg_src_b=3, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L3; lreg_src_c: L0; lreg_dest: L0
    6cc: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    6d0: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    6d4: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    6d8: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    6dc: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    6e0: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    6e4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    6e8: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    6ec: c00f8109  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    6f0: c04f8509  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L1
    6f4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    6f8: c80f8109  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    6fc: c00f8141  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    700: c04f8541  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L1
    704: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    708: c80f8141  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    70c: c00f8149  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    710: c04f8549  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L1
    714: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    718: c80f8149  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    71c: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    720: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    724: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    728: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    72c: c00f8209  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    730: c04f8509  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L1
    734: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    738: c80f8209  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    73c: c00f8241  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    740: c04f8541  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L1
    744: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    748: c80f8241  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    74c: c00f8249  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    750: c04f8549  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L1
    754: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    758: c80f8249  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    75c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    760: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    764: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    768: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    76c: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    770: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    774: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    778: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    77c: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    780: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    784: c8350042  SETC16       setc16_reg=13, setc16_value=16400  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 16; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    788: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    78c: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    790: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    794: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    798: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    79c: c841c182  SETC16       setc16_reg=16, setc16_value=28768  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 32; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    7a0: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    7a4: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    7a8: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    7ac: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    7b0: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    7b4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    7b8: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    7bc: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    7c0: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    7c4: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    7c8: 00907033  and          x0, x0, x9
    7cc: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    7d0: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    7d4: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000001
    7d8: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    7dc: 00942223  sw           x9, 4(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    7e0: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    7e4: 00942423  sw           x9, 8(x8)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    7e8: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    7ec: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    7f0: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    7f4: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    7f8: 00942823  sw           x9, 16(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    7fc: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    800: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    804: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    808: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    80c: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    810: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    814: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    818: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    81c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    820: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    824: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    828: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    82c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    830: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    834: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    838: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    83c: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    840: 00130313  addi         x6, x6, 1
    844: b31ff06f  jal          x0, 0x00000374  # target 0x00000374
loc_848:
    848: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    84c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    850: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    854: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    858: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    85c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    860: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    864: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    868: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    86c: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    870: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    874: 3e021c63  bne          x4, x0, 0x00000c6c  # target 0x00000c6c
    878: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    87c: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    880: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    884: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    888: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    88c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    890: 00507033  and          x0, x0, x5
    894: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    898: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    89c: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
    8a0: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    8a4: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    8a8: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
    8ac: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
    8b0: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    8b4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    8b8: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    8bc: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    8c0: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    8c4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    8c8: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    8cc: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    8d0: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    8d4: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    8d8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    8dc: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    8e0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    8e4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    8e8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    8ec: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    8f0: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    8f4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    8f8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    8fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    900: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    904: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    908: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    90c: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    910: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    914: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    918: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    91c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    920: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    924: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    928: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    92c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    930: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    934: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    938: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    93c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    940: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    944: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    948: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    94c: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    950: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    954: 00537a63  bgeu         x6, x5, 0x00000968  # target 0x00000968
    958: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    95c: 05000313  addi         x6, x0, 80  # x6 = 0x00000050
    960: 00537463  bgeu         x6, x5, 0x00000968  # target 0x00000968
    964: 00800213  addi         x4, x0, 8  # x4 = 0x00000008
loc_968:
    968: fff20213  addi         x4, x4, -1
    96c: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    970: 00020313  addi         x6, x4, 0
loc_974:
    974: 2462f863  bgeu         x5, x6, 0x00000bc4  # target 0x00000bc4
    978: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    97c: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    980: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    984: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    988: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    98c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    990: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    994: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    998: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    99c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    9a0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    9a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9a8: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    9ac: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    9b0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9b4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    9b8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    9bc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    9c0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    9c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9c8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    9cc: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    9d0: c04f8401  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L1
    9d4: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    9d8: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    9dc: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    9e0: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    9e4: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    9e8: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    9ec: c88f8221  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L2
    9f0: c8cf8281  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L3
    9f4: c00f8209  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    9f8: c04f8409  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L1
    9fc: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    a00: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    a04: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    a08: c80f8209  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    a0c: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    a10: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    a14: c88f8229  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=138  # lreg_ind: L2
    a18: c8cf8289  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=162  # lreg_ind: L3
    a1c: c00f8241  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    a20: c04f8441  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L1
    a24: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    a28: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    a2c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    a30: c80f8241  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    a34: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    a38: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    a3c: c88f8261  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=152  # lreg_ind: L2
    a40: c8cf82c1  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=176  # lreg_ind: L3
    a44: c00f8249  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    a48: c04f8449  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L1
    a4c: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    a50: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    a54: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    a58: c80f8249  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    a5c: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    a60: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    a64: c88f8269  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=154  # lreg_ind: L2
    a68: c8cf82c9  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=178  # lreg_ind: L3
    a6c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    a70: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    a74: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    a78: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    a7c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a80: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    a84: 340000ef  jal          x1, 0x00000dc4  # target 0x00000dc4; x1 = 0x00000a88
    a88: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    a8c: 338000ef  jal          x1, 0x00000dc4  # target 0x00000dc4; x1 = 0x00000a90
    a90: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    a94: 330000ef  jal          x1, 0x00000dc4  # target 0x00000dc4; x1 = 0x00000a98
    a98: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    a9c: 328000ef  jal          x1, 0x00000dc4  # target 0x00000dc4; x1 = 0x00000aa0
    aa0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    aa4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    aa8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    aac: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    ab0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ab4: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    ab8: 39c000ef  jal          x1, 0x00000e54  # target 0x00000e54; x1 = 0x00000abc
    abc: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    ac0: 394000ef  jal          x1, 0x00000e54  # target 0x00000e54; x1 = 0x00000ac4
    ac4: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    ac8: 38c000ef  jal          x1, 0x00000e54  # target 0x00000e54; x1 = 0x00000acc
    acc: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    ad0: 384000ef  jal          x1, 0x00000e54  # target 0x00000e54; x1 = 0x00000ad4
    ad4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    ad8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    adc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    ae0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    ae4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ae8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    aec: 3f8000ef  jal          x1, 0x00000ee4  # target 0x00000ee4; x1 = 0x00000af0
    af0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    af4: 3f0000ef  jal          x1, 0x00000ee4  # target 0x00000ee4; x1 = 0x00000af8
    af8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    afc: 3e8000ef  jal          x1, 0x00000ee4  # target 0x00000ee4; x1 = 0x00000b00
    b00: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    b04: 3e0000ef  jal          x1, 0x00000ee4  # target 0x00000ee4; x1 = 0x00000b08
    b08: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    b0c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    b10: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    b14: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    b18: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    b1c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b20: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    b24: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b28: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b2c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    b30: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    b34: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    b38: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    b3c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b40: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    b44: 3c4000ef  jal          x1, 0x00000f08  # target 0x00000f08; x1 = 0x00000b48
    b48: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    b4c: 3bc000ef  jal          x1, 0x00000f08  # target 0x00000f08; x1 = 0x00000b50
    b50: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    b54: 3b4000ef  jal          x1, 0x00000f08  # target 0x00000f08; x1 = 0x00000b58
    b58: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    b5c: 3ac000ef  jal          x1, 0x00000f08  # target 0x00000f08; x1 = 0x00000b60
    b60: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    b64: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    b68: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    b6c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    b70: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    b74: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b78: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    b7c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b80: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b84: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    b88: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    b8c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    b90: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    b94: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b98: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    b9c: 390000ef  jal          x1, 0x00000f2c  # target 0x00000f2c; x1 = 0x00000ba0
    ba0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    ba4: 388000ef  jal          x1, 0x00000f2c  # target 0x00000f2c; x1 = 0x00000ba8
    ba8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    bac: 380000ef  jal          x1, 0x00000f2c  # target 0x00000f2c; x1 = 0x00000bb0
    bb0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    bb4: 378000ef  jal          x1, 0x00000f2c  # target 0x00000f2c; x1 = 0x00000bb8
    bb8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    bbc: 00128293  addi         x5, x5, 1
    bc0: db5ff06f  jal          x0, 0x00000974  # target 0x00000974
loc_bc4:
    bc4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    bc8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    bcc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    bd0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    bd4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    bd8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    bdc: 374000ef  jal          x1, 0x00000f50  # target 0x00000f50; x1 = 0x00000be0
    be0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    be4: 36c000ef  jal          x1, 0x00000f50  # target 0x00000f50; x1 = 0x00000be8
    be8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    bec: 364000ef  jal          x1, 0x00000f50  # target 0x00000f50; x1 = 0x00000bf0
    bf0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    bf4: 35c000ef  jal          x1, 0x00000f50  # target 0x00000f50; x1 = 0x00000bf8
    bf8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    bfc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    c00: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    c04: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    c08: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    c0c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    c10: 36c000ef  jal          x1, 0x00000f7c  # target 0x00000f7c; x1 = 0x00000c14
    c14: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c18: 364000ef  jal          x1, 0x00000f7c  # target 0x00000f7c; x1 = 0x00000c1c
    c1c: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    c20: 35c000ef  jal          x1, 0x00000f7c  # target 0x00000f7c; x1 = 0x00000c24
    c24: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c28: 354000ef  jal          x1, 0x00000f7c  # target 0x00000f7c; x1 = 0x00000c2c
    c2c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    c30: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    c34: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    c38: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    c3c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    c40: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    c44: 350000ef  jal          x1, 0x00000f94  # target 0x00000f94; x1 = 0x00000c48
    c48: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c4c: 348000ef  jal          x1, 0x00000f94  # target 0x00000f94; x1 = 0x00000c50
    c50: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    c54: 340000ef  jal          x1, 0x00000f94  # target 0x00000f94; x1 = 0x00000c58
    c58: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c5c: 338000ef  jal          x1, 0x00000f94  # target 0x00000f94; x1 = 0x00000c60
    c60: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    c64: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    c68: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
loc_c6c:
    c6c: 3400006f  jal          x0, 0x00000fac  # target 0x00000fac
loc_c70:
    c70: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    c74: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    c78: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    c7c: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    c80: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    c84: 01507033  and          x0, x0, x21
    c88: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    c8c: 014a0a13  addi         x20, x20, 20  # x20 = 0xffb80014 · MopCfg[5] · LoopOp / InsnA2
    c90: 04024ab7  lui          x21, 0x04024  # x21 = 0x04024000
    c94: 040a8a93  addi         x21, x21, 64  # x21 = 0x04024040
    c98: 015a2023  sw           x21, 0(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04024040; MOP template instruction · REPLAY start_idx=9, len=4, execute_while_loading=0, load_mode=0
    c9c: 015a2423  sw           x21, 8(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04024040; MOP template instruction · REPLAY start_idx=9, len=4, execute_while_loading=0, load_mode=0
    ca0: 015a2623  sw           x21, 12(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04024040; MOP template instruction · REPLAY start_idx=9, len=4, execute_while_loading=0, load_mode=0
    ca4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    ca8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    cac: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    cb0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    cb4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    cb8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    cbc: 00008067  jalr         x0, 0(x1)
loc_cc0:
    cc0: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    cc4: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    cc8: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    ccc: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    cd0: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    cd4: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    cd8: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    cdc: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    ce0: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    ce4: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    ce8: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    cec: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    cf0: c00f8501  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    cf4: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    cf8: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    cfc: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    d00: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    d04: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    d08: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    d0c: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    d10: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    d14: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    d18: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    d1c: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    d20: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    d24: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    d28: c10f8501  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L4
    d2c: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    d30: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    d34: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    d38: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    d3c: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    d40: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    d44: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    d48: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    d4c: 00008067  jalr         x0, 0(x1)
loc_d50:
    d50: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    d54: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    d58: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    d5c: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    d60: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    d64: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    d68: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    d6c: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    d70: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    d74: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    d78: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    d7c: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    d80: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    d84: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    d88: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    d8c: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    d90: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    d94: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    d98: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    d9c: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    da0: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    da4: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    da8: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    dac: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    db0: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    db4: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    db8: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    dbc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    dc0: 00008067  jalr         x0, 0(x1)
loc_dc4:
    dc4: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    dc8: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    dcc: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    dd0: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    dd4: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    dd8: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    ddc: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    de0: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    de4: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    de8: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    dec: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    df0: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    df4: c00f8221  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L0
    df8: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    dfc: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    e00: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    e04: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    e08: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    e0c: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    e10: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    e14: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    e18: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    e1c: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    e20: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    e24: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    e28: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    e2c: c10f8221  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L4
    e30: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    e34: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    e38: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    e3c: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    e40: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    e44: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    e48: c80f8221  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L0
    e4c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    e50: 00008067  jalr         x0, 0(x1)
loc_e54:
    e54: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    e58: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    e5c: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    e60: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    e64: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    e68: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    e6c: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    e70: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    e74: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    e78: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    e7c: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    e80: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    e84: c00f8281  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L0
    e88: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    e8c: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    e90: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    e94: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    e98: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    e9c: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    ea0: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    ea4: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    ea8: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    eac: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    eb0: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    eb4: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    eb8: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    ebc: c10f8281  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L4
    ec0: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    ec4: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    ec8: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    ecc: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    ed0: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    ed4: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    ed8: c80f8281  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L0
    edc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    ee0: 00008067  jalr         x0, 0(x1)
loc_ee4:
    ee4: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    ee8: c04f8221  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L1
    eec: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    ef0: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    ef4: c08f8281  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L2
    ef8: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    efc: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    f00: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    f04: 00008067  jalr         x0, 0(x1)
loc_f08:
    f08: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    f0c: c04f8221  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L1
    f10: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    f14: c04f8401  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L1
    f18: c08f8281  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L2
    f1c: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    f20: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    f24: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    f28: 00008067  jalr         x0, 0(x1)
loc_f2c:
    f2c: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    f30: c04f8221  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=136  # lreg_ind: L1
    f34: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    f38: c04f8401  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L1
    f3c: c08f8281  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=160  # lreg_ind: L2
    f40: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
    f44: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    f48: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    f4c: 00008067  jalr         x0, 0(x1)
loc_f50:
    f50: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    f54: 64000042  SFPARECIP    imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    f58: 10006886  SFPMAD       lreg_src_a=0, lreg_src_b=1, lreg_src_c=10, lreg_dest=2, instr_mod1=1  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L2
    f5c: 100888c2  SFPMAD       lreg_src_a=2, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    f60: 100c88c2  SFPMAD       lreg_src_a=3, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    f64: 3c000002  SFPNOP
    f68: 480028c6  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    f6c: 100c4402  SFPMAD       lreg_src_a=3, lreg_src_b=1, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L1; lreg_src_c: L1; lreg_dest: L0
    f70: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    f74: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    f78: 00008067  jalr         x0, 0(x1)
loc_f7c:
    f7c: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    f80: c04f8301  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L1
    f84: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    f88: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    f8c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    f90: 00008067  jalr         x0, 0(x1)
loc_f94:
    f94: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    f98: c04f8301  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L1
    f9c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    fa0: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    fa4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    fa8: 00008067  jalr         x0, 0(x1)
    fac:           j FW_TRISC1+4   # return to firmware, linked at install
