# llama3 8b-bf16 decode: attention, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
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
     b4: 625270e3  bgeu         x4, x5, 0x00000ed4  # target 0x00000ed4
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
    288: 451000ef  jal          x1, 0x00000ed8  # target 0x00000ed8; x1 = 0x0000028c
    28c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    290: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    294: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    298: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    29c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2a0: 439000ef  jal          x1, 0x00000ed8  # target 0x00000ed8; x1 = 0x000002a4
    2a4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2a8: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    2ac: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2b0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2b4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2b8: 421000ef  jal          x1, 0x00000ed8  # target 0x00000ed8; x1 = 0x000002bc
    2bc: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2c0: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    2c4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2c8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2cc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2d0: 409000ef  jal          x1, 0x00000ed8  # target 0x00000ed8; x1 = 0x000002d4
    2d4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2d8: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    2dc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2e0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2e4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2e8: 3f1000ef  jal          x1, 0x00000ed8  # target 0x00000ed8; x1 = 0x000002ec
    2ec: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2f0: c8040702  SETC16       setc16_reg=1, setc16_value=448  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 448
    2f4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2f8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    300: 3d9000ef  jal          x1, 0x00000ed8  # target 0x00000ed8; x1 = 0x00000304
    304: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    308: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    30c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    310: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    314: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    318: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    31c: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_320:
    320: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_324:
    324: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    328: c420fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16256  # lreg_ind: L0
    32c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    330: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    334: fffa8a93  addi         x21, x21, -1
    338: fe0a96e3  bne          x21, x0, 0x00000324  # target 0x00000324
    33c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    340: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    344: fffa0a13  addi         x20, x20, -1
    348: fc0a1ce3  bne          x20, x0, 0x00000320  # target 0x00000320
    34c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    350: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    354: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    358: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    35c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    360: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    364: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    368: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    36c: c423fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=65408  # lreg_ind: L0
    370: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    374: c80f8509  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L0
    378: c80f8541  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L0
    37c: c80f8549  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L0
    380: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    384: c4200001  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=0  # lreg_ind: L0
    388: c80f8601  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L0
    38c: c80f8609  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=386  # lreg_ind: L0
    390: c80f8641  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=400  # lreg_ind: L0
    394: c80f8649  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=402  # lreg_ind: L0
    398: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    39c: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    3a0: 00020393  addi         x7, x4, 0
loc_3a4:
    3a4: 5a737e63  bgeu         x6, x7, 0x00000960  # target 0x00000960
    3a8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    3ac: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    3b0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    3b4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    3b8: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    3bc: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    3c0: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    3c4: c8350082  SETC16       setc16_reg=13, setc16_value=16416  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 32; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    3c8: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    3cc: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    3d0: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    3d4: c841c142  SETC16       setc16_reg=16, setc16_value=28752  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 16; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    3d8: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    3dc: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    3e0: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    3e4: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    3e8: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    3ec: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    3f0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3f4: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    3f8: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    3fc: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    400: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    404: 00907033  and          x0, x0, x9
    408: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    40c: 00440413  addi         x8, x8, 4  # x8 = 0xffb80004 · MopCfg[1] · InnerCount / Flags
    410: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    414: 00942023  sw           x9, 0(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    418: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    41c: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    420: 00942423  sw           x9, 8(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    424: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    428: 00942623  sw           x9, 12(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    42c: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    430: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    434: 00942823  sw           x9, 16(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    438: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    43c: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    440: 00942a23  sw           x9, 20(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    444: 00942c23  sw           x9, 24(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    448: 00942e23  sw           x9, 28(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    44c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    450: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    454: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    458: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    45c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    460: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    464: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    468: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    46c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    470: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    474: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    478: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    47c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    480: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    484: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    488: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    48c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    490: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    494: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    498: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    49c: 0c531263  bne          x6, x5, 0x00000560  # target 0x00000560
    4a0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    4a4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4a8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    4ac: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4b0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4b4: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    4b8: 79400513  addi         x10, x0, 1940  # x10 = 0x00000794
    4bc: 00052403  lw           x8, 0(x10)  # param valid_columns; 0x00000794
    4c0: 712204b7  lui          x9, 0x71220  # x9 = 0x71220000
    4c4: 0084e4b3  or           x9, x9, x8
    4c8: ffe40537  lui          x10, 0xffe40  # x10 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    4cc: 00952023  sw           x9, 0(x10)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    4d0: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    4d4: c523fe01  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=65408  # lreg_ind: L4
    4d8: c548003d  SFPLOADI     lreg_ind=5, instr_mod0=2, imm16=15  # lreg_ind: L5
    4dc: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    4e0: e4000455  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    4e4: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    4e8: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4ec: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    4f0: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    4f4: c90f8001  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L4
    4f8: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4fc: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    500: e4004455  SFPIADD      imm12_math=1, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    504: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    508: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    50c: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    510: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    514: c90f8009  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L4
    518: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    51c: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    520: e4040455  SFPIADD      imm12_math=16, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    524: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    528: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    52c: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    530: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    534: c90f8041  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L4
    538: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    53c: f8017c45  SFPAND       imm12_math=5, lreg_c=15, lreg_dest=1, instr_mod1=1  # lreg_c: L15 · lane ID (ttsim reset lane << 1); lreg_dest: L1
    540: e4044455  SFPIADD      imm12_math=17, lreg_c=1, lreg_dest=1, instr_mod1=5  # lreg_c: L1; lreg_dest: L1
    544: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    548: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    54c: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    550: e40004e9  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=10  # lreg_c: L1; lreg_dest: L3
    554: c90f8049  SFPSTORE     lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L4
    558: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    55c: 88042002  STALLWAIT    stall_res=2, wait_res=2048  # stall_res: Stall.SYNC; wait_res: Wait.SFPU
loc_560:
    560: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    564: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    568: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    56c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    570: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    574: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    578: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    57c: c52813cd  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=1267  # lreg_ind: L4
    580: c520f6d5  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=15797  # lreg_ind: L4
    584: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    588: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    58c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    590: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    594: 18052442  SFPMUL       lreg_src_a=1, lreg_src_b=4, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    598: c84f8009  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    59c: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    5a0: 18092482  SFPMUL       lreg_src_a=2, lreg_src_b=4, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    5a4: c88f8041  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    5a8: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    5ac: 180d24c2  SFPMUL       lreg_src_a=3, lreg_src_b=4, lreg_src_c=9, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L3
    5b0: c8cf8049  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    5b4: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    5b8: 480004c6  SFPSWAP      imm12_math=0, lreg_src_c=1, lreg_dest=3, instr_mod1=1  # lreg_src_c: L1; lreg_dest: L3
    5bc: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5c0: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    5c4: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5c8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5cc: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5d0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5d4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5d8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    5dc: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5e0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5e4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5e8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    5ec: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5f0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5f4: c08f8501  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L2
    5f8: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    5fc: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    600: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    604: c80f8509  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L0
    608: c80f8541  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L0
    60c: c80f8549  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L0
    610: 1002cd42  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=5, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L5
    614: c94f8701  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L5
    618: c94f8709  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L5
    61c: c94f8741  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L5
    620: c94f8749  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L5
    624: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    628: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    62c: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    630: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    634: c00f8009  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    638: c04f8509  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L1
    63c: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    640: c80f8009  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    644: c00f8041  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    648: c04f8541  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L1
    64c: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    650: c80f8041  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    654: c00f8049  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    658: c04f8549  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L1
    65c: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    660: c80f8049  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    664: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    668: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    66c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    670: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    674: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    678: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    67c: 0ad000ef  jal          x1, 0x00000f28  # target 0x00000f28; x1 = 0x00000680
    680: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    684: 0a5000ef  jal          x1, 0x00000f28  # target 0x00000f28; x1 = 0x00000688
    688: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    68c: 09d000ef  jal          x1, 0x00000f28  # target 0x00000f28; x1 = 0x00000690
    690: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    694: 095000ef  jal          x1, 0x00000f28  # target 0x00000f28; x1 = 0x00000698
    698: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    69c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    6a0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    6a4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    6a8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    6ac: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    6b0: 109000ef  jal          x1, 0x00000fb8  # target 0x00000fb8; x1 = 0x000006b4
    6b4: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    6b8: 101000ef  jal          x1, 0x00000fb8  # target 0x00000fb8; x1 = 0x000006bc
    6bc: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    6c0: 0f9000ef  jal          x1, 0x00000fb8  # target 0x00000fb8; x1 = 0x000006c4
    6c4: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    6c8: 0f1000ef  jal          x1, 0x00000fb8  # target 0x00000fb8; x1 = 0x000006cc
    6cc: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    6d0: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    6d4: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    6d8: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    6dc: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    6e0: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    6e4: 14284c42  SFPADD       lreg_src_a=10, lreg_src_b=1, lreg_src_c=3, lreg_dest=1, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L1; lreg_src_c: L3; lreg_dest: L1
    6e8: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    6ec: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    6f0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6f4: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6f8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    6fc: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    700: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    704: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    708: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    70c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    710: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    714: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    718: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    71c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    720: c08f8601  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L2
    724: c0cf8701  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L3
    728: 1008c002  SFPMAD       lreg_src_a=2, lreg_src_b=3, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L3; lreg_src_c: L0; lreg_dest: L0
    72c: c80f8601  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L0
    730: c80f8609  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=386  # lreg_ind: L0
    734: c80f8641  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=400  # lreg_ind: L0
    738: c80f8649  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=402  # lreg_ind: L0
    73c: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    740: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    744: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    748: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    74c: c00f8109  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    750: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    754: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    758: c80f8109  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    75c: c00f8141  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    760: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    764: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    768: c80f8141  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    76c: c00f8149  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    770: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    774: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    778: c80f8149  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    77c: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    780: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    784: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    788: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    78c: c00f8209  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    790: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    794: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    798: c80f8209  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    79c: c00f8241  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    7a0: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    7a4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7a8: c80f8241  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    7ac: c00f8249  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    7b0: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    7b4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7b8: c80f8249  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    7bc: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    7c0: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    7c4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7c8: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    7cc: c00f8309  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    7d0: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    7d4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7d8: c80f8309  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    7dc: c00f8341  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    7e0: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    7e4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7e8: c80f8341  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    7ec: c00f8349  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    7f0: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    7f4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7f8: c80f8349  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    7fc: c00f8401  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    800: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    804: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    808: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    80c: c00f8409  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    810: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    814: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    818: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    81c: c00f8441  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    820: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    824: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    828: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    82c: c00f8449  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    830: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    834: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    838: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    83c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    840: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    844: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    848: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    84c: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    850: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    854: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    858: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    85c: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    860: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    864: c8350042  SETC16       setc16_reg=13, setc16_value=16400  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 16; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    868: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    86c: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    870: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    874: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    878: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    87c: c841c182  SETC16       setc16_reg=16, setc16_value=28768  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 32; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    880: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    884: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    888: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    88c: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    890: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    894: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    898: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    89c: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    8a0: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    8a4: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    8a8: 00907033  and          x0, x0, x9
    8ac: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    8b0: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    8b4: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000001
    8b8: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    8bc: 00942223  sw           x9, 4(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    8c0: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    8c4: 00942423  sw           x9, 8(x8)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    8c8: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    8cc: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    8d0: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    8d4: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    8d8: 00942823  sw           x9, 16(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    8dc: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    8e0: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    8e4: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    8e8: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    8ec: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    8f0: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    8f4: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    8f8: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    8fc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    900: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    904: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    908: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    90c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    910: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    914: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    918: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    91c: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    920: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    924: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    928: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    92c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    930: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    934: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    938: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    93c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    940: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    944: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    948: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    94c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    950: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    954: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    958: 00130313  addi         x6, x6, 1
    95c: a49ff06f  jal          x0, 0x000003a4  # target 0x000003a4
loc_960:
    960: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    964: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    968: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    96c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    970: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    974: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    978: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    97c: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    980: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    984: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    988: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    98c: 54021463  bne          x4, x0, 0x00000ed4  # target 0x00000ed4
    990: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    994: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    998: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    99c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    9a0: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    9a4: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    9a8: 00507033  and          x0, x0, x5
    9ac: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    9b0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    9b4: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
    9b8: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    9bc: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    9c0: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
    9c4: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
    9c8: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    9cc: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    9d0: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    9d4: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    9d8: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    9dc: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    9e0: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    9e4: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    9e8: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    9ec: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    9f0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    9f4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    9f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9fc: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    a00: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a04: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a08: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    a0c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    a10: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    a14: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a18: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    a1c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a20: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a24: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    a28: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    a2c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    a30: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a34: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    a38: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a3c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a40: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    a44: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    a48: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    a4c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a50: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    a54: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a58: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a5c: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    a60: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    a64: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    a68: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a6c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    a70: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a74: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a78: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    a7c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    a80: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    a84: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a88: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    a8c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a90: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a94: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    a98: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    a9c: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    aa0: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    aa4: 00537a63  bgeu         x6, x5, 0x00000ab8  # target 0x00000ab8
    aa8: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    aac: 05000313  addi         x6, x0, 80  # x6 = 0x00000050
    ab0: 00537463  bgeu         x6, x5, 0x00000ab8  # target 0x00000ab8
    ab4: 00800213  addi         x4, x0, 8  # x4 = 0x00000008
loc_ab8:
    ab8: fff20213  addi         x4, x4, -1
    abc: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    ac0: 00020313  addi         x6, x4, 0
loc_ac4:
    ac4: 3062f063  bgeu         x5, x6, 0x00000dc4  # target 0x00000dc4
    ac8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    acc: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    ad0: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    ad4: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    ad8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    adc: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    ae0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    ae4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ae8: c8040702  SETC16       setc16_reg=1, setc16_value=448  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 448
    aec: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    af0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    af4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    af8: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    afc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    b00: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b04: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    b08: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    b0c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    b10: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    b14: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    b18: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    b1c: c00f8401  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    b20: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    b24: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    b28: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    b2c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    b30: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    b34: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    b38: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    b3c: c88f8421  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L2
    b40: c8cf8481  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L3
    b44: c00f8409  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    b48: c04f8609  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=386  # lreg_ind: L1
    b4c: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    b50: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    b54: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    b58: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    b5c: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    b60: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    b64: c88f8429  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=266  # lreg_ind: L2
    b68: c8cf8489  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=290  # lreg_ind: L3
    b6c: c00f8441  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    b70: c04f8641  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=400  # lreg_ind: L1
    b74: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    b78: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    b7c: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    b80: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    b84: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    b88: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    b8c: c88f8461  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=280  # lreg_ind: L2
    b90: c8cf84c1  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=304  # lreg_ind: L3
    b94: c00f8449  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    b98: c04f8649  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=402  # lreg_ind: L1
    b9c: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    ba0: f00004c1  SFPMOV       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=0  # lreg_c: L1; lreg_dest: L3
    ba4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    ba8: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    bac: 1002c882  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L2; lreg_dest: L2
    bb0: 1002ccc2  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=3, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L3
    bb4: c88f8469  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=282  # lreg_ind: L2
    bb8: c8cf84c9  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=306  # lreg_ind: L3
    bbc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    bc0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    bc4: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    bc8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    bcc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    bd0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    bd4: 458000ef  jal          x1, 0x0000102c  # target 0x0000102c; x1 = 0x00000bd8
    bd8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    bdc: 450000ef  jal          x1, 0x0000102c  # target 0x0000102c; x1 = 0x00000be0
    be0: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    be4: 448000ef  jal          x1, 0x0000102c  # target 0x0000102c; x1 = 0x00000be8
    be8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    bec: 440000ef  jal          x1, 0x0000102c  # target 0x0000102c; x1 = 0x00000bf0
    bf0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    bf4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    bf8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    bfc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    c00: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    c04: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    c08: 4b4000ef  jal          x1, 0x000010bc  # target 0x000010bc; x1 = 0x00000c0c
    c0c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c10: 4ac000ef  jal          x1, 0x000010bc  # target 0x000010bc; x1 = 0x00000c14
    c14: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    c18: 4a4000ef  jal          x1, 0x000010bc  # target 0x000010bc; x1 = 0x00000c1c
    c1c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c20: 49c000ef  jal          x1, 0x000010bc  # target 0x000010bc; x1 = 0x00000c24
    c24: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    c28: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    c2c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    c30: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    c34: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    c38: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    c3c: 510000ef  jal          x1, 0x0000114c  # target 0x0000114c; x1 = 0x00000c40
    c40: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c44: 508000ef  jal          x1, 0x0000114c  # target 0x0000114c; x1 = 0x00000c48
    c48: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    c4c: 500000ef  jal          x1, 0x0000114c  # target 0x0000114c; x1 = 0x00000c50
    c50: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c54: 4f8000ef  jal          x1, 0x0000114c  # target 0x0000114c; x1 = 0x00000c58
    c58: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    c5c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    c60: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    c64: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    c68: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    c6c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    c70: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    c74: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    c78: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    c7c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    c80: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    c84: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    c88: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    c8c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    c90: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    c94: 4dc000ef  jal          x1, 0x00001170  # target 0x00001170; x1 = 0x00000c98
    c98: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    c9c: 4d4000ef  jal          x1, 0x00001170  # target 0x00001170; x1 = 0x00000ca0
    ca0: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    ca4: 4cc000ef  jal          x1, 0x00001170  # target 0x00001170; x1 = 0x00000ca8
    ca8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    cac: 4c4000ef  jal          x1, 0x00001170  # target 0x00001170; x1 = 0x00000cb0
    cb0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    cb4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    cb8: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    cbc: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    cc0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    cc4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    cc8: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    ccc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    cd0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    cd4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    cd8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    cdc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    ce0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    ce4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ce8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    cec: 4a8000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x00000cf0
    cf0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    cf4: 4a0000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x00000cf8
    cf8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    cfc: 498000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x00000d00
    d00: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    d04: 490000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x00000d08
    d08: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    d0c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    d10: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    d14: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    d18: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    d1c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    d20: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    d24: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    d28: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    d2c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    d30: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    d34: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    d38: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    d3c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    d40: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    d44: 474000ef  jal          x1, 0x000011b8  # target 0x000011b8; x1 = 0x00000d48
    d48: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    d4c: 46c000ef  jal          x1, 0x000011b8  # target 0x000011b8; x1 = 0x00000d50
    d50: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    d54: 464000ef  jal          x1, 0x000011b8  # target 0x000011b8; x1 = 0x00000d58
    d58: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    d5c: 45c000ef  jal          x1, 0x000011b8  # target 0x000011b8; x1 = 0x00000d60
    d60: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    d64: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    d68: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    d6c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    d70: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    d74: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    d78: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    d7c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    d80: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    d84: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    d88: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    d8c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    d90: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    d94: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    d98: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    d9c: 440000ef  jal          x1, 0x000011dc  # target 0x000011dc; x1 = 0x00000da0
    da0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    da4: 438000ef  jal          x1, 0x000011dc  # target 0x000011dc; x1 = 0x00000da8
    da8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    dac: 430000ef  jal          x1, 0x000011dc  # target 0x000011dc; x1 = 0x00000db0
    db0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    db4: 428000ef  jal          x1, 0x000011dc  # target 0x000011dc; x1 = 0x00000db8
    db8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    dbc: 00128293  addi         x5, x5, 1
    dc0: d05ff06f  jal          x0, 0x00000ac4  # target 0x00000ac4
loc_dc4:
    dc4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    dc8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    dcc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    dd0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    dd4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    dd8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    ddc: 424000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000de0
    de0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    de4: 41c000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000de8
    de8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    dec: 414000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000df0
    df0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    df4: 40c000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000df8
    df8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    dfc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    e00: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    e04: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    e08: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    e0c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    e10: 41c000ef  jal          x1, 0x0000122c  # target 0x0000122c; x1 = 0x00000e14
    e14: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    e18: 414000ef  jal          x1, 0x0000122c  # target 0x0000122c; x1 = 0x00000e1c
    e1c: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    e20: 40c000ef  jal          x1, 0x0000122c  # target 0x0000122c; x1 = 0x00000e24
    e24: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    e28: 404000ef  jal          x1, 0x0000122c  # target 0x0000122c; x1 = 0x00000e2c
    e2c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    e30: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    e34: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    e38: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    e3c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    e40: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    e44: 400000ef  jal          x1, 0x00001244  # target 0x00001244; x1 = 0x00000e48
    e48: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    e4c: 3f8000ef  jal          x1, 0x00001244  # target 0x00001244; x1 = 0x00000e50
    e50: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    e54: 3f0000ef  jal          x1, 0x00001244  # target 0x00001244; x1 = 0x00000e58
    e58: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    e5c: 3e8000ef  jal          x1, 0x00001244  # target 0x00001244; x1 = 0x00000e60
    e60: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    e64: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    e68: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    e6c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    e70: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    e74: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    e78: 3e4000ef  jal          x1, 0x0000125c  # target 0x0000125c; x1 = 0x00000e7c
    e7c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    e80: 3dc000ef  jal          x1, 0x0000125c  # target 0x0000125c; x1 = 0x00000e84
    e84: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    e88: 3d4000ef  jal          x1, 0x0000125c  # target 0x0000125c; x1 = 0x00000e8c
    e8c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    e90: 3cc000ef  jal          x1, 0x0000125c  # target 0x0000125c; x1 = 0x00000e94
    e94: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    e98: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    e9c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    ea0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    ea4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ea8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    eac: 3c8000ef  jal          x1, 0x00001274  # target 0x00001274; x1 = 0x00000eb0
    eb0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    eb4: 3c0000ef  jal          x1, 0x00001274  # target 0x00001274; x1 = 0x00000eb8
    eb8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    ebc: 3b8000ef  jal          x1, 0x00001274  # target 0x00001274; x1 = 0x00000ec0
    ec0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    ec4: 3b0000ef  jal          x1, 0x00001274  # target 0x00001274; x1 = 0x00000ec8
    ec8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    ecc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    ed0: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
loc_ed4:
    ed4: 3b80006f  jal          x0, 0x0000128c  # target 0x0000128c
loc_ed8:
    ed8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    edc: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    ee0: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    ee4: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    ee8: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    eec: 01507033  and          x0, x0, x21
    ef0: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    ef4: 014a0a13  addi         x20, x20, 20  # x20 = 0xffb80014 · MopCfg[5] · LoopOp / InsnA2
    ef8: 04024ab7  lui          x21, 0x04024  # x21 = 0x04024000
    efc: 040a8a93  addi         x21, x21, 64  # x21 = 0x04024040
    f00: 015a2023  sw           x21, 0(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04024040; MOP template instruction · REPLAY start_idx=9, len=4, execute_while_loading=0, load_mode=0
    f04: 015a2423  sw           x21, 8(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04024040; MOP template instruction · REPLAY start_idx=9, len=4, execute_while_loading=0, load_mode=0
    f08: 015a2623  sw           x21, 12(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04024040; MOP template instruction · REPLAY start_idx=9, len=4, execute_while_loading=0, load_mode=0
    f0c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    f10: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    f14: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    f18: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    f1c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    f20: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    f24: 00008067  jalr         x0, 0(x1)
loc_f28:
    f28: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    f2c: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    f30: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    f34: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    f38: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    f3c: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    f40: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    f44: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    f48: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    f4c: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    f50: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    f54: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    f58: c00f8701  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L0
    f5c: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    f60: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    f64: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    f68: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    f6c: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    f70: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    f74: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    f78: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    f7c: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    f80: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    f84: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    f88: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    f8c: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    f90: c10f8701  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L4
    f94: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
    f98: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    f9c: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
    fa0: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
    fa4: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
    fa8: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    fac: c80f8701  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L0
    fb0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    fb4: 00008067  jalr         x0, 0(x1)
loc_fb8:
    fb8: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    fbc: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    fc0: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    fc4: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    fc8: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    fcc: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    fd0: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    fd4: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    fd8: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    fdc: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    fe0: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    fe4: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    fe8: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    fec: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    ff0: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    ff4: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    ff8: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    ffc: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
   1000: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
   1004: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
   1008: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
   100c: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
   1010: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
   1014: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
   1018: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
   101c: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
   1020: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
   1024: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   1028: 00008067  jalr         x0, 0(x1)
loc_102c:
   102c: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
   1030: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
   1034: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
   1038: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
   103c: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
   1040: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
   1044: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
   1048: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
   104c: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
   1050: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
   1054: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
   1058: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
   105c: c00f8421  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L0
   1060: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
   1064: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
   1068: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
   106c: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
   1070: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
   1074: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
   1078: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
   107c: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
   1080: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
   1084: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
   1088: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
   108c: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
   1090: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
   1094: c10f8421  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L4
   1098: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
   109c: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
   10a0: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
   10a4: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
   10a8: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
   10ac: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
   10b0: c80f8421  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L0
   10b4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   10b8: 00008067  jalr         x0, 0(x1)
loc_10bc:
   10bc: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
   10c0: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
   10c4: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
   10c8: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
   10cc: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
   10d0: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
   10d4: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
   10d8: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
   10dc: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
   10e0: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
   10e4: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
   10e8: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
   10ec: c00f8481  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L0
   10f0: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
   10f4: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
   10f8: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
   10fc: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
   1100: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
   1104: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
   1108: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
   110c: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
   1110: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
   1114: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
   1118: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
   111c: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
   1120: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
   1124: c10f8481  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L4
   1128: 24001106  SFPSETSGN    imm12_math=0, lreg_c=4, lreg_dest=4, instr_mod1=1  # lreg_c: L4; lreg_dest: L4
   112c: 1c000002  SFPPUSHC     imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
   1130: 2800c02a  SFPENCC      imm12_math=3, lreg_c=0, lreg_dest=0, instr_mod1=10  # lreg_c: L0; lreg_dest: L0
   1134: ec001019  SFPSETCC     imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=6  # lreg_c: L4; lreg_dest: L0
   1138: f0002801  SFPMOV       imm12_math=0, lreg_c=10, lreg_dest=0, instr_mod1=0  # lreg_c: L10 · constant 1 (0x3f800000); lreg_dest: L0
   113c: 20000002  SFPPOPC      imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
   1140: c80f8481  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L0
   1144: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   1148: 00008067  jalr         x0, 0(x1)
loc_114c:
   114c: c00f8501  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
   1150: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
   1154: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   1158: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
   115c: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
   1160: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
   1164: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
   1168: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   116c: 00008067  jalr         x0, 0(x1)
loc_1170:
   1170: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
   1174: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
   1178: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   117c: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
   1180: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
   1184: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
   1188: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
   118c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   1190: 00008067  jalr         x0, 0(x1)
loc_1194:
   1194: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
   1198: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
   119c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   11a0: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
   11a4: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
   11a8: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
   11ac: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
   11b0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   11b4: 00008067  jalr         x0, 0(x1)
loc_11b8:
   11b8: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
   11bc: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
   11c0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   11c4: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
   11c8: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
   11cc: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
   11d0: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
   11d4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   11d8: 00008067  jalr         x0, 0(x1)
loc_11dc:
   11dc: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
   11e0: c04f8421  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=264  # lreg_ind: L1
   11e4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   11e8: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
   11ec: c08f8481  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=288  # lreg_ind: L2
   11f0: 10048002  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L0; lreg_dest: L0
   11f4: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
   11f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   11fc: 00008067  jalr         x0, 0(x1)
loc_1200:
   1200: c00f8501  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
   1204: 64000042  SFPARECIP    imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
   1208: 10006886  SFPMAD       lreg_src_a=0, lreg_src_b=1, lreg_src_c=10, lreg_dest=2, instr_mod1=1  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L2
   120c: 100888c2  SFPMAD       lreg_src_a=2, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
   1210: 100c88c2  SFPMAD       lreg_src_a=3, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
   1214: 3c000002  SFPNOP
   1218: 480028c6  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
   121c: 100c4402  SFPMAD       lreg_src_a=3, lreg_src_b=1, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L1; lreg_src_c: L1; lreg_dest: L0
   1220: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
   1224: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   1228: 00008067  jalr         x0, 0(x1)
loc_122c:
   122c: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
   1230: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
   1234: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   1238: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
   123c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   1240: 00008067  jalr         x0, 0(x1)
loc_1244:
   1244: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
   1248: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
   124c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   1250: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
   1254: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   1258: 00008067  jalr         x0, 0(x1)
loc_125c:
   125c: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
   1260: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
   1264: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   1268: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
   126c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   1270: 00008067  jalr         x0, 0(x1)
loc_1274:
   1274: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
   1278: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
   127c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
   1280: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
   1284: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
   1288: 00008067  jalr         x0, 0(x1)
   128c:           j FW_TRISC1+4   # return to firmware, linked at install
