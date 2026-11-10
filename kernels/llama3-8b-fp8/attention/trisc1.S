# llama3 8b-fp8 decode: attention, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (32): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=attention_core
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
     44: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     48: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     4c: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     50: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     54: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     58: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     5c: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     60: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     64: 00507033  and          x0, x0, x5
     68: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     6c: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     70: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     74: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     78: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     7c: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     80: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
     84: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     88: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
     8c: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     90: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     94: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
     98: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     9c: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     a0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     a4: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
     a8: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     ac: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     b0: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     b4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     b8: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
     bc: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     c0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     c8: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     cc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     d0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     d4: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
     d8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     dc: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     e0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     e4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     e8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     ec: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     f0: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
     f4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     f8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    100: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    104: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    108: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    10c: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    110: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    114: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    118: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    11c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    120: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    124: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    128: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    12c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    130: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    134: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    138: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    13c: 3c000002  SFPNOP       
    140: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    144: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    148: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    14c: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    150: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    154: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    158: 01507033  and          x0, x0, x21
    15c: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    160: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    164: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    168: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    16c: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    170: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    174: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
    178: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    17c: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    180: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    184: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    188: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    18c: 0b0a8a93  addi         x21, x21, 176  # x21 = 0x040000b0
    190: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    194: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    198: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    19c: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    1a0: 0b0a8a93  addi         x21, x21, 176  # x21 = 0x040000b0
    1a4: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    1a8: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x040000b0; MOP template instruction · REPLAY start_idx=0, len=11, execute_while_loading=0, load_mode=0
    1ac: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1b0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1b4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1bc: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    1c0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1c4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1c8: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    1cc: 79000313  addi         x6, x0, 1936  # x6 = 0x00000790
    1d0: 00032203  lw           x4, 0(x6)  # param kv_blocks; 0x00000790
    1d4: fff20293  addi         x5, x4, -1
    1d8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    1dc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    1e0: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    1e4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    1e8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    1ec: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    1f0: 3c000002  SFPNOP       
    1f4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1f8: 131000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x000001fc
    1fc: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    200: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    204: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    208: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    20c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    210: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    214: 3c000002  SFPNOP       
    218: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    21c: 10d000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x00000220
    220: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    224: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    228: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    22c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    230: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    234: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    238: 3c000002  SFPNOP       
    23c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    240: 0e9000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x00000244
    244: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    248: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    24c: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    250: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    254: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    258: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    25c: 3c000002  SFPNOP       
    260: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    264: 0c5000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x00000268
    268: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    26c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    270: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    274: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    278: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    27c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    280: 3c000002  SFPNOP       
    284: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    288: 0a1000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x0000028c
    28c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    290: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    294: c8040702  SETC16       setc16_reg=1, setc16_value=448  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 448
    298: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    29c: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2a0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2a4: 3c000002  SFPNOP       
    2a8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2ac: 07d000ef  jal          x1, 0x00000b28  # target 0x00000b28; x1 = 0x000002b0
    2b0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    2b4: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2b8: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    2bc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2c0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2c4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2c8: 3c000002  SFPNOP       
    2cc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2d0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    2d4: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_2d8:
    2d8: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_2dc:
    2dc: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    2e0: c420fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16256  # lreg_ind: L0
    2e4: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    2e8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    2ec: fffa8a93  addi         x21, x21, -1
    2f0: fe0a96e3  bne          x21, x0, 0x000002dc  # target 0x000002dc
    2f4: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    2f8: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    2fc: fffa0a13  addi         x20, x20, -1
    300: fc0a1ce3  bne          x20, x0, 0x000002d8  # target 0x000002d8
    304: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    308: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    30c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    310: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    314: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    318: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    31c: 3c000002  SFPNOP       
    320: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    324: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    328: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    32c: c423fe01  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=65408  # lreg_ind: L0
    330: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    334: c80f8509  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L0
    338: c80f8541  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L0
    33c: c80f8549  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L0
    340: c4280001  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=0  # lreg_ind: L0
    344: c4200001  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=0  # lreg_ind: L0
    348: c80f8601  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L0
    34c: c80f8609  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=386  # lreg_ind: L0
    350: c80f8641  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=400  # lreg_ind: L0
    354: c80f8649  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=402  # lreg_ind: L0
    358: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    35c: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    360: 00020393  addi         x7, x4, 0
loc_364:
    364: 6a737c63  bgeu         x6, x7, 0x00000a1c  # target 0x00000a1c
    368: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    36c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    370: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    374: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    378: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    37c: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    380: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    384: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    388: c8350082  SETC16       setc16_reg=13, setc16_value=16416  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 32; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    38c: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    390: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    394: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    398: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    39c: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    3a0: c841c142  SETC16       setc16_reg=16, setc16_value=28752  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 16; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    3a4: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    3a8: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    3ac: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    3b0: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    3b4: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    3b8: 40710000  ZEROACC      clear_mode=3, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    3bc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3c0: 10100204  REPLAY       start_idx=16, len=8, execute_while_loading=0, load_mode=1
    3c4: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[16]; not executed here
    3c8: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[17]; not executed here
    3cc: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[18]; not executed here
    3d0: 98020000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=2, dst=0  # Record replay[19]; not executed here
    3d4: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[20]; not executed here
    3d8: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[21]; not executed here
    3dc: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[22]; not executed here
    3e0: 98040000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=4, dst=0  # Record replay[23]; not executed here
    3e4: 10180204  REPLAY       start_idx=24, len=8, execute_while_loading=0, load_mode=1
    3e8: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[24]; not executed here
    3ec: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[25]; not executed here
    3f0: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[26]; not executed here
    3f4: 98020000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=2, dst=0  # Record replay[27]; not executed here
    3f8: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[28]; not executed here
    3fc: 98010000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=1, dst=0  # Record replay[29]; not executed here
    400: 98000000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=0, dst=0  # Record replay[30]; not executed here
    404: 98050000  MVMUL        clear_dvalid=0, instr_mod19=0, addr_mode=5, dst=0  # Record replay[31]; not executed here
    408: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    40c: 00440413  addi         x8, x8, 4  # x8 = 0xffe80004 · TensixMMIO.PC_BUF_SYNC
    410: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004; write 0x00000000
    414: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_SYNC · 0xffe80004
    418: 00907033  and          x0, x0, x9
    41c: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    420: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    424: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    428: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    42c: 00907033  and          x0, x0, x9
    430: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    434: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    438: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000001
    43c: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    440: 00942223  sw           x9, 4(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    444: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    448: 00942423  sw           x9, 8(x8)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
    44c: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    450: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    454: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    458: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    45c: 00942823  sw           x9, 16(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    460: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    464: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    468: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    46c: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    470: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    474: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    478: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    47c: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    480: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    484: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    488: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    48c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    490: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    494: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    498: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    49c: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4a0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    4a4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    4a8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    4ac: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4b0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4b4: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4b8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    4bc: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    4c0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    4c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4c8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4cc: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4d0: 06531663  bne          x6, x5, 0x0000053c  # target 0x0000053c
    4d4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    4d8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    4dc: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    4e0: c8382022  SETC16       setc16_reg=14, setc16_value=2056  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 8; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    4e4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4e8: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    4ec: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    4f0: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    4f4: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    4f8: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    4fc: 00907033  and          x0, x0, x9
    500: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    504: 00400493  addi         x9, x0, 4  # x9 = 0x00000004
    508: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000004
    50c: 37c004b7  lui          x9, 0x37c00  # x9 = 0x37c00000
    510: 00348493  addi         x9, x9, 3  # x9 = 0x37c00003
    514: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    518: 282084b7  lui          x9, 0x28208  # x9 = 0x28208000
    51c: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x28208000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=1, instr_mod19=0, addr_mode=2, dst=0
    520: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    524: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    528: 282084b7  lui          x9, 0x28208  # x9 = 0x28208000
    52c: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x28208000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=1, instr_mod19=0, addr_mode=2, dst=0
    530: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x28208000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=1, instr_mod19=0, addr_mode=2, dst=0
    534: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    538: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
loc_53c:
    53c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    540: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    544: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    548: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    54c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    550: 3c000002  SFPNOP       
    554: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    558: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    55c: c52813cd  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=1267  # lreg_ind: L4
    560: c520f6d5  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=15797  # lreg_ind: L4
    564: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    568: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    56c: 3c000002  SFPNOP       
    570: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    574: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    578: 18052442  SFPMUL       lreg_src_a=1, lreg_src_b=4, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    57c: 3c000002  SFPNOP       
    580: c84f8009  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    584: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    588: 18092482  SFPMUL       lreg_src_a=2, lreg_src_b=4, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    58c: 3c000002  SFPNOP       
    590: c88f8041  SFPSTORE     lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    594: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    598: 180d24c2  SFPMUL       lreg_src_a=3, lreg_src_b=4, lreg_src_c=9, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L3
    59c: 3c000002  SFPNOP       
    5a0: c8cf8049  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    5a4: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    5a8: 3c000002  SFPNOP       
    5ac: 480004c6  SFPSWAP      imm12_math=0, lreg_src_c=1, lreg_dest=3, instr_mod1=1  # lreg_src_c: L1; lreg_dest: L3
    5b0: 3c000002  SFPNOP       
    5b4: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5b8: 3c000002  SFPNOP       
    5bc: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    5c0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5c4: 3c000002  SFPNOP       
    5c8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5cc: 3c000002  SFPNOP       
    5d0: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5d4: 3c000002  SFPNOP       
    5d8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5dc: 3c000002  SFPNOP       
    5e0: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    5e4: 3c000002  SFPNOP       
    5e8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    5ec: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5f0: 3c000002  SFPNOP       
    5f4: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    5f8: 3c000002  SFPNOP       
    5fc: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    600: 3c000002  SFPNOP       
    604: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    608: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    60c: 3c000002  SFPNOP       
    610: 48000046  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=1, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L1
    614: 3c000002  SFPNOP       
    618: c08f8501  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L2
    61c: f00008c1  SFPMOV       imm12_math=0, lreg_c=2, lreg_dest=3, instr_mod1=0  # lreg_c: L2; lreg_dest: L3
    620: 48000086  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=2, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L2
    624: 3c000002  SFPNOP       
    628: c80f8501  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L0
    62c: c80f8509  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L0
    630: c80f8541  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L0
    634: c80f8549  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L0
    638: 1002cd42  SFPMAD       lreg_src_a=0, lreg_src_b=11, lreg_src_c=3, lreg_dest=5, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L3; lreg_dest: L5
    63c: 3c000002  SFPNOP       
    640: c94f8701  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L5
    644: c94f8709  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L5
    648: c94f8741  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L5
    64c: c94f8749  SFPSTORE     lreg_ind=5, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L5
    650: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    654: c04f8501  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=320  # lreg_ind: L1
    658: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    65c: 3c000002  SFPNOP       
    660: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    664: c00f8009  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    668: c04f8509  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=322  # lreg_ind: L1
    66c: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    670: 3c000002  SFPNOP       
    674: c80f8009  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L0
    678: c00f8041  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    67c: c04f8541  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=336  # lreg_ind: L1
    680: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    684: 3c000002  SFPNOP       
    688: c80f8041  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L0
    68c: c00f8049  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    690: c04f8549  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=338  # lreg_ind: L1
    694: 1006c002  SFPMAD       lreg_src_a=1, lreg_src_b=11, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L0; lreg_dest: L0
    698: 3c000002  SFPNOP       
    69c: c80f8049  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L0
    6a0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    6a4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    6a8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    6ac: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    6b0: 3c000002  SFPNOP       
    6b4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    6b8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    6bc: 4f0000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000006c0
    6c0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    6c4: 4e8000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000006c8
    6c8: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    6cc: 4e0000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000006d0
    6d0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    6d4: 4d8000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000006d8
    6d8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    6dc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    6e0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    6e4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    6e8: 3c000002  SFPNOP       
    6ec: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    6f0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    6f4: 530000ef  jal          x1, 0x00000c24  # target 0x00000c24; x1 = 0x000006f8
    6f8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    6fc: 528000ef  jal          x1, 0x00000c24  # target 0x00000c24; x1 = 0x00000700
    700: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    704: 520000ef  jal          x1, 0x00000c24  # target 0x00000c24; x1 = 0x00000708
    708: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    70c: 518000ef  jal          x1, 0x00000c24  # target 0x00000c24; x1 = 0x00000710
    710: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    714: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    718: c04f8009  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L1
    71c: c08f8041  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=16  # lreg_ind: L2
    720: c0cf8049  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=18  # lreg_ind: L3
    724: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    728: 3c000002  SFPNOP       
    72c: 14284c42  SFPADD       lreg_src_a=10, lreg_src_b=1, lreg_src_c=3, lreg_dest=1, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L1; lreg_src_c: L3; lreg_dest: L1
    730: 3c000002  SFPNOP       
    734: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    738: 3c000002  SFPNOP       
    73c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    740: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    744: 3c000002  SFPNOP       
    748: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    74c: 3c000002  SFPNOP       
    750: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    754: 3c000002  SFPNOP       
    758: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    75c: 3c000002  SFPNOP       
    760: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    764: 3c000002  SFPNOP       
    768: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    76c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    770: 3c000002  SFPNOP       
    774: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    778: 3c000002  SFPNOP       
    77c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    780: 3c000002  SFPNOP       
    784: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    788: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    78c: 3c000002  SFPNOP       
    790: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    794: 3c000002  SFPNOP       
    798: c08f8601  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L2
    79c: c0cf8701  SFPLOAD      lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L3
    7a0: 1008c002  SFPMAD       lreg_src_a=2, lreg_src_b=3, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L3; lreg_src_c: L0; lreg_dest: L0
    7a4: 3c000002  SFPNOP       
    7a8: c80f8601  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L0
    7ac: c80f8609  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=386  # lreg_ind: L0
    7b0: c80f8641  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=400  # lreg_ind: L0
    7b4: c80f8649  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=402  # lreg_ind: L0
    7b8: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    7bc: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    7c0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7c4: 3c000002  SFPNOP       
    7c8: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    7cc: c00f8109  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    7d0: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    7d4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7d8: 3c000002  SFPNOP       
    7dc: c80f8109  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=66  # lreg_ind: L0
    7e0: c00f8141  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    7e4: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    7e8: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7ec: 3c000002  SFPNOP       
    7f0: c80f8141  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=80  # lreg_ind: L0
    7f4: c00f8149  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    7f8: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    7fc: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    800: 3c000002  SFPNOP       
    804: c80f8149  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=82  # lreg_ind: L0
    808: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    80c: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    810: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    814: 3c000002  SFPNOP       
    818: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    81c: c00f8209  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    820: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    824: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    828: 3c000002  SFPNOP       
    82c: c80f8209  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L0
    830: c00f8241  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    834: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    838: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    83c: 3c000002  SFPNOP       
    840: c80f8241  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=144  # lreg_ind: L0
    844: c00f8249  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    848: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    84c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    850: 3c000002  SFPNOP       
    854: c80f8249  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=146  # lreg_ind: L0
    858: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    85c: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    860: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    864: 3c000002  SFPNOP       
    868: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    86c: c00f8309  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    870: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    874: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    878: 3c000002  SFPNOP       
    87c: c80f8309  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=194  # lreg_ind: L0
    880: c00f8341  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    884: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    888: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    88c: 3c000002  SFPNOP       
    890: c80f8341  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=208  # lreg_ind: L0
    894: c00f8349  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    898: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    89c: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8a0: 3c000002  SFPNOP       
    8a4: c80f8349  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=210  # lreg_ind: L0
    8a8: c00f8401  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    8ac: c04f8701  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L1
    8b0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8b4: 3c000002  SFPNOP       
    8b8: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    8bc: c00f8409  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    8c0: c04f8709  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=450  # lreg_ind: L1
    8c4: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8c8: 3c000002  SFPNOP       
    8cc: c80f8409  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L0
    8d0: c00f8441  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    8d4: c04f8741  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=464  # lreg_ind: L1
    8d8: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8dc: 3c000002  SFPNOP       
    8e0: c80f8441  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=272  # lreg_ind: L0
    8e4: c00f8449  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    8e8: c04f8749  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=466  # lreg_ind: L1
    8ec: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    8f0: 3c000002  SFPNOP       
    8f4: c80f8449  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=274  # lreg_ind: L0
    8f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    8fc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    900: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    904: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    908: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    90c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    910: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    914: c8302002  SETC16       setc16_reg=12, setc16_value=2048  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 0; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    918: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    91c: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    920: c8350042  SETC16       setc16_reg=13, setc16_value=16400  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 16; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 1; ADDR_MOD_AB_SEC1_SrcBClear = 0
    924: c8740022  SETC16       setc16_reg=29, setc16_value=8  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 8; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    928: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    92c: c8398102  SETC16       setc16_reg=14, setc16_value=24640  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 1; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 32; ADDR_MOD_AB_SEC2_SrcBCR = 1; ADDR_MOD_AB_SEC2_SrcBClear = 0
    930: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    934: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    938: c841c182  SETC16       setc16_reg=16, setc16_value=28768  # thread_cfg[16] (current thread); ADDR_MOD_AB_SEC4_SrcAIncr = 32; ADDR_MOD_AB_SEC4_SrcACR = 1; ADDR_MOD_AB_SEC4_SrcAClear = 0; ADDR_MOD_AB_SEC4_SrcBIncr = 48; ADDR_MOD_AB_SEC4_SrcBCR = 1; ADDR_MOD_AB_SEC4_SrcBClear = 0
    93c: c8801002  SETC16       setc16_reg=32, setc16_value=1024  # thread_cfg[32] (current thread); ADDR_MOD_DST_SEC4_DestIncr = 0; ADDR_MOD_DST_SEC4_DestCR = 1; ADDR_MOD_DST_SEC4_DestClear = 0; ADDR_MOD_DST_SEC4_DestCToCR = 0; ADDR_MOD_DST_SEC4_FidelityIncr = 0; ADDR_MOD_DST_SEC4_FidelityClear = 0
    940: c8cc0002  SETC16       setc16_reg=51, setc16_value=0  # thread_cfg[51] (current thread); ADDR_MOD_BIAS_SEC4_BiasIncr = 0; ADDR_MOD_BIAS_SEC4_BiasClear = 0
    944: c8470302  SETC16       setc16_reg=17, setc16_value=49344  # thread_cfg[17] (current thread); ADDR_MOD_AB_SEC5_SrcAIncr = 0; ADDR_MOD_AB_SEC5_SrcACR = 1; ADDR_MOD_AB_SEC5_SrcAClear = 1; ADDR_MOD_AB_SEC5_SrcBIncr = 0; ADDR_MOD_AB_SEC5_SrcBCR = 1; ADDR_MOD_AB_SEC5_SrcBClear = 1
    948: c884b002  SETC16       setc16_reg=33, setc16_value=11264  # thread_cfg[33] (current thread); ADDR_MOD_DST_SEC5_DestIncr = 0; ADDR_MOD_DST_SEC5_DestCR = 1; ADDR_MOD_DST_SEC5_DestClear = 1; ADDR_MOD_DST_SEC5_DestCToCR = 0; ADDR_MOD_DST_SEC5_FidelityIncr = 1; ADDR_MOD_DST_SEC5_FidelityClear = 0
    94c: c8d00002  SETC16       setc16_reg=52, setc16_value=0  # thread_cfg[52] (current thread); ADDR_MOD_BIAS_SEC5_BiasIncr = 0; ADDR_MOD_BIAS_SEC5_BiasClear = 0
    950: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    954: ffe80437  lui          x8, 0xffe80  # x8 = 0xffe80000 · tensix_pc_buf + 0x0
    958: 00840413  addi         x8, x8, 8  # x8 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    95c: 00042023  sw           x0, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    960: 00042483  lw           x9, 0(x8)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    964: 00907033  and          x0, x0, x9
    968: ffb80437  lui          x8, 0xffb80  # x8 = 0xffb80000 · MOP_CFG
    96c: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
    970: 00942023  sw           x9, 0(x8)  # MOP_CFG · 0xffb80000; write 0x00000001
    974: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    978: 00942223  sw           x9, 4(x8)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    97c: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    980: 00942423  sw           x9, 8(x8)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
    984: 374004b7  lui          x9, 0x37400  # x9 = 0x37400000
    988: 00f48493  addi         x9, x9, 15  # x9 = 0x3740000f
    98c: 00942623  sw           x9, 12(x8)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x3740000f; MOP template instruction · SETRWC clear_ab_vld=1, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    990: 020004b7  lui          x9, 0x02000  # x9 = 0x02000000
    994: 00942823  sw           x9, 16(x8)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    998: 040404b7  lui          x9, 0x04040  # x9 = 0x04040000
    99c: 08048493  addi         x9, x9, 128  # x9 = 0x04040080
    9a0: 00942a23  sw           x9, 20(x8)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040080; MOP template instruction · REPLAY start_idx=16, len=8, execute_while_loading=0, load_mode=0
    9a4: 040604b7  lui          x9, 0x04060  # x9 = 0x04060000
    9a8: 08048493  addi         x9, x9, 128  # x9 = 0x04060080
    9ac: 00942c23  sw           x9, 24(x8)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    9b0: 00942e23  sw           x9, 28(x8)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    9b4: 02942023  sw           x9, 32(x8)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04060080; MOP template instruction · REPLAY start_idx=24, len=8, execute_while_loading=0, load_mode=0
    9b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    9bc: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9c0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    9c4: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    9c8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    9cc: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    9d0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9d4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    9d8: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9dc: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    9e0: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    9e4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    9e8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    9ec: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9f0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    9f4: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    9f8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    9fc: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    a00: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    a04: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    a08: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a0c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a10: de00003c  SETRWC       clear_ab_vld=2, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a14: 00130313  addi         x6, x6, 1
    a18: 94dff06f  jal          x0, 0x00000364  # target 0x00000364
loc_a1c:
    a1c: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    a20: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    a24: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    a28: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    a2c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    a30: 3c000002  SFPNOP       
    a34: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a38: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    a3c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    a40: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    a44: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    a48: 3c000002  SFPNOP       
    a4c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a50: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    a54: 248000ef  jal          x1, 0x00000c9c  # target 0x00000c9c; x1 = 0x00000a58
    a58: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    a5c: 240000ef  jal          x1, 0x00000c9c  # target 0x00000c9c; x1 = 0x00000a60
    a60: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    a64: 238000ef  jal          x1, 0x00000c9c  # target 0x00000c9c; x1 = 0x00000a68
    a68: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    a6c: 230000ef  jal          x1, 0x00000c9c  # target 0x00000c9c; x1 = 0x00000a70
    a70: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    a74: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    a78: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    a7c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    a80: 3c000002  SFPNOP       
    a84: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a88: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    a8c: 258000ef  jal          x1, 0x00000ce4  # target 0x00000ce4; x1 = 0x00000a90
    a90: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    a94: 250000ef  jal          x1, 0x00000ce4  # target 0x00000ce4; x1 = 0x00000a98
    a98: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    a9c: 248000ef  jal          x1, 0x00000ce4  # target 0x00000ce4; x1 = 0x00000aa0
    aa0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    aa4: 240000ef  jal          x1, 0x00000ce4  # target 0x00000ce4; x1 = 0x00000aa8
    aa8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    aac: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    ab0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    ab4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    ab8: 3c000002  SFPNOP       
    abc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    ac0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    ac4: 268000ef  jal          x1, 0x00000d2c  # target 0x00000d2c; x1 = 0x00000ac8
    ac8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    acc: 260000ef  jal          x1, 0x00000d2c  # target 0x00000d2c; x1 = 0x00000ad0
    ad0: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    ad4: 258000ef  jal          x1, 0x00000d2c  # target 0x00000d2c; x1 = 0x00000ad8
    ad8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    adc: 250000ef  jal          x1, 0x00000d2c  # target 0x00000d2c; x1 = 0x00000ae0
    ae0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    ae4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    ae8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    aec: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    af0: 3c000002  SFPNOP       
    af4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    af8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    afc: 278000ef  jal          x1, 0x00000d74  # target 0x00000d74; x1 = 0x00000b00
    b00: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    b04: 270000ef  jal          x1, 0x00000d74  # target 0x00000d74; x1 = 0x00000b08
    b08: e00e0000  INCRWC       rwc_cr=0, rwc_d=14, rwc_b=0, rwc_a=0
    b0c: 268000ef  jal          x1, 0x00000d74  # target 0x00000d74; x1 = 0x00000b10
    b10: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    b14: 260000ef  jal          x1, 0x00000d74  # target 0x00000d74; x1 = 0x00000b18
    b18: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    b1c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    b20: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    b24: 2980006f  jal          x0, 0x00000dbc  # target 0x00000dbc
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
    c18: c80f8701  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=448  # lreg_ind: L0
    c1c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    c20: 00008067  jalr         x0, 0(x1)
loc_c24:
    c24: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    c28: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    c2c: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    c30: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    c34: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    c38: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    c3c: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    c40: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    c44: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    c48: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    c4c: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    c50: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    c54: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    c58: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    c5c: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    c60: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    c64: 3c000002  SFPNOP       
    c68: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    c6c: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    c70: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    c74: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    c78: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    c7c: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    c80: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    c84: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    c88: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    c8c: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    c90: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    c94: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    c98: 00008067  jalr         x0, 0(x1)
loc_c9c:
    c9c: c00f8101  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    ca0: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    ca4: 64000482  SFPARECIP    imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=0  # lreg_c: L1; lreg_dest: L2
    ca8: 1004a8c6  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    cac: 3c000002  SFPNOP       
    cb0: 100ccd02  SFPMAD       lreg_src_a=3, lreg_src_b=3, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L3; lreg_src_c: L3; lreg_dest: L4
    cb4: 3c000002  SFPNOP       
    cb8: 1010cd02  SFPMAD       lreg_src_a=4, lreg_src_b=3, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L3; lreg_src_c: L3; lreg_dest: L4
    cbc: 3c000002  SFPNOP       
    cc0: 48002906  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=4, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L4
    cc4: 3c000002  SFPNOP       
    cc8: 10108842  SFPMAD       lreg_src_a=4, lreg_src_b=2, lreg_src_c=2, lreg_dest=1, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L1
    ccc: 3c000002  SFPNOP       
    cd0: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    cd4: 3c000002  SFPNOP       
    cd8: c80f8101  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L0
    cdc: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    ce0: 00008067  jalr         x0, 0(x1)
loc_ce4:
    ce4: c00f8201  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    ce8: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    cec: 64000482  SFPARECIP    imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=0  # lreg_c: L1; lreg_dest: L2
    cf0: 1004a8c6  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    cf4: 3c000002  SFPNOP       
    cf8: 100ccd02  SFPMAD       lreg_src_a=3, lreg_src_b=3, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L3; lreg_src_c: L3; lreg_dest: L4
    cfc: 3c000002  SFPNOP       
    d00: 1010cd02  SFPMAD       lreg_src_a=4, lreg_src_b=3, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L3; lreg_src_c: L3; lreg_dest: L4
    d04: 3c000002  SFPNOP       
    d08: 48002906  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=4, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L4
    d0c: 3c000002  SFPNOP       
    d10: 10108842  SFPMAD       lreg_src_a=4, lreg_src_b=2, lreg_src_c=2, lreg_dest=1, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L1
    d14: 3c000002  SFPNOP       
    d18: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    d1c: 3c000002  SFPNOP       
    d20: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    d24: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    d28: 00008067  jalr         x0, 0(x1)
loc_d2c:
    d2c: c00f8301  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    d30: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    d34: 64000482  SFPARECIP    imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=0  # lreg_c: L1; lreg_dest: L2
    d38: 1004a8c6  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    d3c: 3c000002  SFPNOP       
    d40: 100ccd02  SFPMAD       lreg_src_a=3, lreg_src_b=3, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L3; lreg_src_c: L3; lreg_dest: L4
    d44: 3c000002  SFPNOP       
    d48: 1010cd02  SFPMAD       lreg_src_a=4, lreg_src_b=3, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L3; lreg_src_c: L3; lreg_dest: L4
    d4c: 3c000002  SFPNOP       
    d50: 48002906  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=4, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L4
    d54: 3c000002  SFPNOP       
    d58: 10108842  SFPMAD       lreg_src_a=4, lreg_src_b=2, lreg_src_c=2, lreg_dest=1, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L1
    d5c: 3c000002  SFPNOP       
    d60: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    d64: 3c000002  SFPNOP       
    d68: c80f8301  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=192  # lreg_ind: L0
    d6c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    d70: 00008067  jalr         x0, 0(x1)
loc_d74:
    d74: c00f8401  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    d78: c04f8601  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=384  # lreg_ind: L1
    d7c: 64000482  SFPARECIP    imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=0  # lreg_c: L1; lreg_dest: L2
    d80: 1004a8c6  SFPMAD       lreg_src_a=1, lreg_src_b=2, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    d84: 3c000002  SFPNOP       
    d88: 100ccd02  SFPMAD       lreg_src_a=3, lreg_src_b=3, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L3; lreg_src_c: L3; lreg_dest: L4
    d8c: 3c000002  SFPNOP       
    d90: 1010cd02  SFPMAD       lreg_src_a=4, lreg_src_b=3, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L3; lreg_src_c: L3; lreg_dest: L4
    d94: 3c000002  SFPNOP       
    d98: 48002906  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=4, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L4
    d9c: 3c000002  SFPNOP       
    da0: 10108842  SFPMAD       lreg_src_a=4, lreg_src_b=2, lreg_src_c=2, lreg_dest=1, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L1
    da4: 3c000002  SFPNOP       
    da8: 18006402  SFPMUL       lreg_src_a=0, lreg_src_b=1, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    dac: 3c000002  SFPNOP       
    db0: c80f8401  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L0
    db4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    db8: 00008067  jalr         x0, 0(x1)
    dbc:           j FW_TRISC1+4   # return to firmware, linked at install
