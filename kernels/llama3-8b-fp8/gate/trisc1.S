# llama3 8b-fp8 decode: gate, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_x_b_decode_token, 0x784=e2e_l0_gate, 0x788=e2e_l0_up, 0x78c=input_scale_0, 0x790=input_scale_1, 0x794=output_scale_0_0, 0x798=output_scale_0_1, 0x79c=output_scale_1_0, 0x7a0=output_scale_1_1, 0x7a4=e2e_hidden_dense, 0x7a8=e2e_l0_post_norm, 0x11940=e2e_gate, 0x11944=e2e_l0_gate_row_start, 0x11948=e2e_up, 0x1194c=e2e_l0_up_row_start, 0x11950=dense_start, 0x11954=e2e_l0_gate_rows, 0x11958=e2e_l0_up_rows, 0x1195c=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: 100000c4  REPLAY       start_idx=0, len=3, execute_while_loading=0, load_mode=1
      4: c04f8001  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[0]; not executed here
      8: 10044002  SFPMAD       lreg_src_a=1, lreg_src_b=1, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L1; lreg_src_c: L0; lreg_dest: L0; Record replay[1]; not executed here
      c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[2]; not executed here
     10: 100300c4  REPLAY       start_idx=3, len=3, execute_while_loading=0, load_mode=1
     14: c04f8001  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[3]; not executed here
     18: 10044002  SFPMAD       lreg_src_a=1, lreg_src_b=1, lreg_src_c=0, lreg_dest=0, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L1; lreg_src_c: L0; lreg_dest: L0; Record replay[4]; not executed here
     1c: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[5]; not executed here
     20: 10060284  REPLAY       start_idx=6, len=10, execute_while_loading=0, load_mode=1
     24: 4c438002  SFPLOADMACRO lreg_ind=1, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[6]; not executed here
     28: c08f8401  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=256  # lreg_ind: L2; Record replay[7]; not executed here
     2c: 4cc3800a  SFPLOADMACRO lreg_ind=3, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L3; Record replay[8]; not executed here
     30: c10f8409  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=258  # lreg_ind: L4; Record replay[9]; not executed here
     34: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1; Record replay[10]; not executed here
     38: 180d24c2  SFPMUL       lreg_src_a=3, lreg_src_b=4, lreg_src_c=9, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L3; Record replay[11]; not executed here
     3c: c84f8001  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[12]; not executed here
     40: c8cf8009  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L3; Record replay[13]; not executed here
     44: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[14]; not executed here
     48: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[15]; not executed here
     4c: 10100144  REPLAY       start_idx=16, len=5, execute_while_loading=0, load_mode=1
     50: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[16]; not executed here
     54: 1801a402  SFPMUL       lreg_src_a=0, lreg_src_b=6, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L6; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0; Record replay[17]; not executed here
     58: 3c000002  SFPNOP         # Record replay[18]; not executed here
     5c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[19]; not executed here
     60: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[20]; not executed here
     64: 101500c4  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=1
     68: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[21]; not executed here
     6c: 10029dc2  SFPMAD       lreg_src_a=0, lreg_src_b=10, lreg_src_c=7, lreg_dest=7, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L7; lreg_dest: L7; Record replay[22]; not executed here
     70: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[23]; not executed here
     74: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
     78: 3c000002  SFPNOP
     7c: 18002702  SFPMUL       lreg_src_a=0, lreg_src_b=0, lreg_src_c=9, lreg_dest=12, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L0; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L12
     80: 46100106  SFPCONFIG    imm16_math=33792, config_dest=4, instr_mod1=1
     84: 443c0206  SFPCONFIG    imm16_math=3840, config_dest=8, instr_mod1=1
     88: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     8c: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     90: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     94: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     98: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     9c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     a0: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     a4: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     a8: 00507033  and          x0, x0, x5
     ac: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     b0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     b4: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     b8: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     bc: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     c0: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     c4: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     c8: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     cc: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
     d0: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     d4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     d8: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
     dc: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     e0: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     e4: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     e8: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
     ec: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     f0: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     f4: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     f8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     fc: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    100: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    104: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    108: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    10c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    110: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    114: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    118: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    11c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    120: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    124: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    128: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    12c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    130: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    134: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    138: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    13c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    140: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    144: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    148: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    14c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    150: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    154: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    158: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    15c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    160: c8040402  SETC16       setc16_reg=1, setc16_value=256  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 256
    164: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    168: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    16c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    170: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    174: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    178: c8040502  SETC16       setc16_reg=1, setc16_value=320  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 320
    17c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    180: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    184: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    188: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    18c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    190: c8040602  SETC16       setc16_reg=1, setc16_value=384  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 384
    194: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    198: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    19c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1a0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1a8: c8040702  SETC16       setc16_reg=1, setc16_value=448  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 448
    1ac: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    1b0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1b4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    1b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1bc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1c0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    1c4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    1c8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    1cc: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    1d0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    1d4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1d8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    1dc: c4000001  SFPLOADI     lreg_ind=0, instr_mod0=0, imm16=0  # lreg_ind: L0
    1e0: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    1e4: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    1e8: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    1ec: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    1f0: 00507033  and          x0, x0, x5
    1f4: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    1f8: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    1fc: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000001
    200: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
    204: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    208: 371202b7  lui          x5, 0x37120  # x5 = 0x37120000
    20c: 00428293  addi         x5, x5, 4  # x5 = 0x37120004
    210: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    214: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    218: 040002b7  lui          x5, 0x04000  # x5 = 0x04000000
    21c: 03028293  addi         x5, x5, 48  # x5 = 0x04000030
    220: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    224: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    228: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    22c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    230: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    234: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    238: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    23c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    240: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    244: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    248: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    24c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    250: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    254: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    258: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    25c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    260: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    264: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    268: 00507033  and          x0, x0, x5
    26c: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    270: 01420213  addi         x4, x4, 20  # x4 = 0xffb80014 · MopCfg[5] · LoopOp / InsnA2
    274: 0400c2b7  lui          x5, 0x0400c  # x5 = 0x0400c000
    278: 03028293  addi         x5, x5, 48  # x5 = 0x0400c030
    27c: 00522023  sw           x5, 0(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    280: 00522423  sw           x5, 8(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    284: 00522623  sw           x5, 12(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    288: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    28c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    290: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    294: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    298: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    29c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2a0: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    2a4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2a8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2ac: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2b0: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    2b4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2bc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2c0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2c4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    2c8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2cc: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    2d0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2d4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2d8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2dc: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    2e0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2e4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2e8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2ec: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2f0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    2f4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2f8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    2fc: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    300: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    304: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    308: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    30c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    310: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    314: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    318: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    31c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    320: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    324: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    328: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    32c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    330: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    334: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    338: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    33c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    340: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    344: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    348: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    34c: c520e601  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=14720  # lreg_ind: L4
    350: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    354: c52b16b1  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=50604  # lreg_ind: L4
    358: c520dc9d  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=14119  # lreg_ind: L4
    35c: 14281002  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=4, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L4; lreg_dest: L0
    360: f0000181  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=6, instr_mod1=0  # lreg_c: L0; lreg_dest: L6
    364: f0001841  SFPMOV       imm12_math=0, lreg_c=6, lreg_dest=1, instr_mod1=0  # lreg_c: L6; lreg_dest: L1
    368: ebffe445  SFPSHFT      imm12_math=4095, lreg_c=9, lreg_dest=1, instr_mod1=1  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    36c: c4a84281  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=4256  # lreg_ind: L2
    370: c4a17c45  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=24337  # lreg_ind: L2
    374: e4000859  SFPIADD      imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=6  # lreg_c: L2; lreg_dest: L1
    378: 18186482  SFPMUL       lreg_src_a=6, lreg_src_b=1, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L6; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    37c: 1804a486  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=2, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    380: c4e85325  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=5321  # lreg_ind: L3
    384: c4e10049  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16402  # lreg_ind: L3
    388: c528d899  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=13862  # lreg_ind: L4
    38c: c5210041  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=16400  # lreg_ind: L4
    390: 14290902  SFPADD       lreg_src_a=10, lreg_src_b=4, lreg_src_c=2, lreg_dest=4, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L4; lreg_src_c: L2; lreg_dest: L4
    394: 10090c82  SFPMAD       lreg_src_a=2, lreg_src_b=4, lreg_src_c=3, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L2
    398: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    39c: 18186482  SFPMUL       lreg_src_a=6, lreg_src_b=1, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L6; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    3a0: 1804a486  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=2, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    3a4: 142a8882  SFPADD       lreg_src_a=10, lreg_src_b=10, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L2; lreg_dest: L2
    3a8: c5680001  SFPLOADI     lreg_ind=5, instr_mod0=10, imm16=0  # lreg_ind: L5
    3ac: c560fc01  SFPLOADI     lreg_ind=5, instr_mod0=8, imm16=16128  # lreg_ind: L5
    3b0: 18056542  SFPMUL       lreg_src_a=1, lreg_src_b=5, lreg_src_c=9, lreg_dest=5, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L5; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L5
    3b4: 10094402  SFPMAD       lreg_src_a=2, lreg_src_b=5, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L5; lreg_src_c: L1; lreg_dest: L0
    3b8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    3bc: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    3c0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    3c4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    3c8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3cc: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    3d0: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    3d4: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    3d8: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    3dc: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    3e0: 00507033  and          x0, x0, x5
    3e4: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    3e8: 00420213  addi         x4, x4, 4  # x4 = 0xffb80004 · MopCfg[1] · InnerCount / Flags
    3ec: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    3f0: 00522023  sw           x5, 0(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    3f4: 040182b7  lui          x5, 0x04018  # x5 = 0x04018000
    3f8: 0a028293  addi         x5, x5, 160  # x5 = 0x040180a0
    3fc: 00522823  sw           x5, 16(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    400: 00522c23  sw           x5, 24(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    404: 00522e23  sw           x5, 28(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    408: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    40c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    410: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    414: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    418: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    41c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    420: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    424: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    428: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    42c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    430: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    434: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    438: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    43c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    440: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    444: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    448: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    44c: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    450: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    454: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    458: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    45c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    460: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    464: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    468: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    46c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    470: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    474: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    478: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    47c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    480: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    484: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    488: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    48c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    490: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    494: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    498: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    49c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    4a0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    4a4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    4a8: 78c00293  addi         x5, x0, 1932  # x5 = 0x0000078c
    4ac: 0002a203  lw           x4, 0(x5)  # param input_scale_0; 0x0000078c
    4b0: ffe402b7  lui          x5, 0xffe40  # x5 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    4b4: 0042a023  sw           x4, 0(x5)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    4b8: 79000293  addi         x5, x0, 1936  # x5 = 0x00000790
    4bc: 0002a203  lw           x4, 0(x5)  # param input_scale_1; 0x00000790
    4c0: ffe402b7  lui          x5, 0xffe40  # x5 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    4c4: 0042a023  sw           x4, 0(x5)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    4c8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    4cc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    4d0: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    4d4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4d8: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    4dc: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4e0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4e4: 3f0000ef  jal          x1, 0x000008d4  # target 0x000008d4; x1 = 0x000004e8
    4e8: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    4ec: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    4f0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4f4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4fc: 3d8000ef  jal          x1, 0x000008d4  # target 0x000008d4; x1 = 0x00000500
    500: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    504: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    508: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    50c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    510: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    514: 3c0000ef  jal          x1, 0x000008d4  # target 0x000008d4; x1 = 0x00000518
    518: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    51c: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    520: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    524: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    528: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    52c: 3a8000ef  jal          x1, 0x000008d4  # target 0x000008d4; x1 = 0x00000530
    530: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    534: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    538: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    53c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    540: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    544: 414000ef  jal          x1, 0x00000958  # target 0x00000958; x1 = 0x00000548
    548: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    54c: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    550: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    554: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    558: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    55c: 3fc000ef  jal          x1, 0x00000958  # target 0x00000958; x1 = 0x00000560
    560: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    564: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    568: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    56c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    570: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    574: 3e4000ef  jal          x1, 0x00000958  # target 0x00000958; x1 = 0x00000578
    578: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    57c: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    580: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    584: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    588: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    58c: 3cc000ef  jal          x1, 0x00000958  # target 0x00000958; x1 = 0x00000590
    590: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    594: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    598: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    59c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    5a0: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    5a4: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    5a8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    5ac: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    5b0: c8302022  SETC16       setc16_reg=12, setc16_value=2056  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 8; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    5b4: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    5b8: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    5bc: c8340002  SETC16       setc16_reg=13, setc16_value=0  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 0; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 0; ADDR_MOD_AB_SEC1_SrcBClear = 0
    5c0: c8740002  SETC16       setc16_reg=29, setc16_value=0  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 0; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    5c4: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    5c8: c83a0202  SETC16       setc16_reg=14, setc16_value=32896  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 1; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 1
    5cc: c8789002  SETC16       setc16_reg=30, setc16_value=9216  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 0; ADDR_MOD_DST_SEC2_DestCR = 1; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 1; ADDR_MOD_DST_SEC2_FidelityClear = 0
    5d0: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    5d4: c83e0202  SETC16       setc16_reg=15, setc16_value=32896  # thread_cfg[15] (current thread); ADDR_MOD_AB_SEC3_SrcAIncr = 0; ADDR_MOD_AB_SEC3_SrcACR = 0; ADDR_MOD_AB_SEC3_SrcAClear = 1; ADDR_MOD_AB_SEC3_SrcBIncr = 0; ADDR_MOD_AB_SEC3_SrcBCR = 0; ADDR_MOD_AB_SEC3_SrcBClear = 1
    5d8: c87e4022  SETC16       setc16_reg=31, setc16_value=36872  # thread_cfg[31] (current thread); ADDR_MOD_DST_SEC3_DestIncr = 8; ADDR_MOD_DST_SEC3_DestCR = 0; ADDR_MOD_DST_SEC3_DestClear = 0; ADDR_MOD_DST_SEC3_DestCToCR = 1; ADDR_MOD_DST_SEC3_FidelityIncr = 0; ADDR_MOD_DST_SEC3_FidelityClear = 1
    5dc: c8c80002  SETC16       setc16_reg=50, setc16_value=0  # thread_cfg[50] (current thread); ADDR_MOD_BIAS_SEC3_BiasIncr = 0; ADDR_MOD_BIAS_SEC3_BiasClear = 0
    5e0: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    5e4: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    5e8: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    5ec: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    5f0: 00507033  and          x0, x0, x5
    5f4: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    5f8: 00420213  addi         x4, x4, 4  # x4 = 0xffb80004 · MopCfg[1] · InnerCount / Flags
    5fc: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    600: 00522023  sw           x5, 0(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    604: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    608: 00522423  sw           x5, 8(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    60c: 00522623  sw           x5, 12(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    610: 270002b7  lui          x5, 0x27000  # x5 = 0x27000000
    614: 00522823  sw           x5, 16(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x27000000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0
    618: 27c0c2b7  lui          x5, 0x27c0c  # x5 = 0x27c0c000
    61c: 00522c23  sw           x5, 24(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x27c0c000; MOP template instruction · ELWMUL clear_dvalid=3, dest_accum_en=0, instr_mod19=0, addr_mode=3, dst=0
    620: 270082b7  lui          x5, 0x27008  # x5 = 0x27008000
    624: 00522e23  sw           x5, 28(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x27008000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    628: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    62c: 95428293  addi         x5, x5, -1708  # x5 = 0x00011954
    630: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x00011954
    634: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    638: 00020313  addi         x6, x4, 0
loc_63c:
    63c: 0462f463  bgeu         x5, x6, 0x00000684  # target 0x00000684
    640: 3c0000ef  jal          x1, 0x00000a00  # target 0x00000a00; x1 = 0x00000644
    644: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    648: 79400413  addi         x8, x0, 1940  # x8 = 0x00000794
    64c: 00042383  lw           x7, 0(x8)  # param output_scale_0_0; 0x00000794
    650: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    654: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    658: 79800413  addi         x8, x0, 1944  # x8 = 0x00000798
    65c: 00042383  lw           x7, 0(x8)  # param output_scale_0_1; 0x00000798
    660: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    664: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    668: 1801a402  SFPMUL       lreg_src_a=0, lreg_src_b=6, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L6; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    66c: 3c000002  SFPNOP
    670: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    674: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    678: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    67c: 00128293  addi         x5, x5, 1
    680: fbdff06f  jal          x0, 0x0000063c  # target 0x0000063c
loc_684:
    684: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    688: 95828293  addi         x5, x5, -1704  # x5 = 0x00011958
    68c: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x00011958
    690: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    694: 00020313  addi         x6, x4, 0
loc_698:
    698: 0462f463  bgeu         x5, x6, 0x000006e0  # target 0x000006e0
    69c: 364000ef  jal          x1, 0x00000a00  # target 0x00000a00; x1 = 0x000006a0
    6a0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    6a4: 79c00413  addi         x8, x0, 1948  # x8 = 0x0000079c
    6a8: 00042383  lw           x7, 0(x8)  # param output_scale_1_0; 0x0000079c
    6ac: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    6b0: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    6b4: 7a000413  addi         x8, x0, 1952  # x8 = 0x000007a0
    6b8: 00042383  lw           x7, 0(x8)  # param output_scale_1_1; 0x000007a0
    6bc: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    6c0: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    6c4: 1801a402  SFPMUL       lreg_src_a=0, lreg_src_b=6, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L6; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    6c8: 3c000002  SFPNOP
    6cc: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    6d0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    6d4: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    6d8: 00128293  addi         x5, x5, 1
    6dc: fbdff06f  jal          x0, 0x00000698  # target 0x00000698
loc_6e0:
    6e0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    6e4: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    6e8: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    6ec: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    6f0: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    6f4: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    6f8: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    6fc: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    700: 00507033  and          x0, x0, x5
    704: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    708: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    70c: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
    710: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    714: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    718: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    71c: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    720: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
    724: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
    728: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    72c: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    730: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    734: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    738: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    73c: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    740: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    744: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    748: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    74c: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    750: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    754: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    758: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    75c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    760: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    764: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    768: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    76c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    770: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    774: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    778: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    77c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    780: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    784: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    788: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    78c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    790: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    794: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    798: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    79c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    7a0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    7a4: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    7a8: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    7ac: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    7b0: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    7b4: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    7b8: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    7bc: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    7c0: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    7c4: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    7c8: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    7cc: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    7d0: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    7d4: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    7d8: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_7dc:
    7dc: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_7e0:
    7e0: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    7e4: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    7e8: 1802e402  SFPMUL       lreg_src_a=0, lreg_src_b=11, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    7ec: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    7f0: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    7f4: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    7f8: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    7fc: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    800: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    804: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    808: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    80c: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    810: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    814: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    818: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    81c: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    820: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    824: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    828: fffa8a93  addi         x21, x21, -1
    82c: fa0a9ae3  bne          x21, x0, 0x000007e0  # target 0x000007e0
    830: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    834: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    838: fffa0a13  addi         x20, x20, -1
    83c: fa0a10e3  bne          x20, x0, 0x000007dc  # target 0x000007dc
    840: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    844: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    848: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    84c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    850: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    854: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    858: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    85c: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    860: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_864:
    864: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_868:
    868: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    86c: d4fe0001  SFPADDI      imm16_math=16256, lreg_dest=0, instr_mod1=0  # lreg_dest: L0
    870: 3c000002  SFPNOP
    874: 64000042  SFPARECIP    imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    878: 10006886  SFPMAD       lreg_src_a=0, lreg_src_b=1, lreg_src_c=10, lreg_dest=2, instr_mod1=1  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L2
    87c: 100888c2  SFPMAD       lreg_src_a=2, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    880: 100c88c2  SFPMAD       lreg_src_a=3, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    884: 3c000002  SFPNOP
    888: 480028c6  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    88c: 100c4402  SFPMAD       lreg_src_a=3, lreg_src_b=1, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L1; lreg_src_c: L1; lreg_dest: L0
    890: c04f8201  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L1
    894: c08f8101  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L2
    898: 18042442  SFPMUL       lreg_src_a=1, lreg_src_b=0, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L0; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    89c: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    8a0: c84f8001  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1
    8a4: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    8a8: fffa8a93  addi         x21, x21, -1
    8ac: fa0a9ee3  bne          x21, x0, 0x00000868  # target 0x00000868
    8b0: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    8b4: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    8b8: fffa0a13  addi         x20, x20, -1
    8bc: fa0a14e3  bne          x20, x0, 0x00000864  # target 0x00000864
    8c0: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    8c4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    8c8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    8cc: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    8d0: 2900006f  jal          x0, 0x00000b60  # target 0x00000b60
loc_8d4:
    8d4: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    8d8: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    8dc: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    8e0: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    8e4: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    8e8: 01507033  and          x0, x0, x21
    8ec: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    8f0: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    8f4: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    8f8: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    8fc: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    900: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    904: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
    908: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    90c: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    910: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    914: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    918: 04040ab7  lui          x21, 0x04040  # x21 = 0x04040000
    91c: 050a8a93  addi         x21, x21, 80  # x21 = 0x04040050
    920: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04040050; MOP template instruction · REPLAY start_idx=16, len=5, execute_while_loading=0, load_mode=0
    924: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    928: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
    92c: 04040ab7  lui          x21, 0x04040  # x21 = 0x04040000
    930: 050a8a93  addi         x21, x21, 80  # x21 = 0x04040050
    934: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04040050; MOP template instruction · REPLAY start_idx=16, len=5, execute_while_loading=0, load_mode=0
    938: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04040050; MOP template instruction · REPLAY start_idx=16, len=5, execute_while_loading=0, load_mode=0
    93c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    940: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    944: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    948: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    94c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    950: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    954: 00008067  jalr         x0, 0(x1)
loc_958:
    958: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    95c: c46bfffd  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=65535  # lreg_ind: L1
    960: c460001d  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=7  # lreg_ind: L1
    964: c4a80005  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=1  # lreg_ind: L2
    968: c4a00001  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=0  # lreg_ind: L2
    96c: c4e80001  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=0  # lreg_ind: L3
    970: c4e3ffc1  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=65520  # lreg_ind: L3
    974: c5680001  SFPLOADI     lreg_ind=5, instr_mod0=10, imm16=0  # lreg_ind: L5
    978: c5610f81  SFPLOADI     lreg_ind=5, instr_mod0=8, imm16=17376  # lreg_ind: L5
    97c: c5a80001  SFPLOADI     lreg_ind=6, instr_mod0=10, imm16=0  # lreg_ind: L6
    980: c5a30f81  SFPLOADI     lreg_ind=6, instr_mod0=8, imm16=50144  # lreg_ind: L6
    984: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_988:
    988: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_98c:
    98c: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    990: f0000101  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=0  # lreg_c: L0; lreg_dest: L4
    994: ebfb0105  SFPSHFT      imm12_math=4076, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    998: f8000901  SFPAND       imm12_math=0, lreg_c=2, lreg_dest=4, instr_mod1=0  # lreg_c: L2; lreg_dest: L4
    99c: e4000511  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4
    9a0: e4001011  SFPIADD      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=4  # lreg_c: L4; lreg_dest: L0
    9a4: f8000c01  SFPAND       imm12_math=0, lreg_c=3, lreg_dest=0, instr_mod1=0  # lreg_c: L3; lreg_dest: L0
    9a8: f00015c1  SFPMOV       imm12_math=0, lreg_c=5, lreg_dest=7, instr_mod1=0  # lreg_c: L5; lreg_dest: L7
    9ac: 48001c06  SFPSWAP      imm12_math=0, lreg_src_c=7, lreg_dest=0, instr_mod1=1  # lreg_src_c: L7; lreg_dest: L0
    9b0: f00019c1  SFPMOV       imm12_math=0, lreg_c=6, lreg_dest=7, instr_mod1=0  # lreg_c: L6; lreg_dest: L7
    9b4: 480001c6  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=7, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L7
    9b8: f4000105  SFPABS       imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    9bc: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7
    9c0: c5e0f201  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=15488  # lreg_ind: L7
    9c4: e40011d9  SFPIADD      imm12_math=0, lreg_c=4, lreg_dest=7, instr_mod1=6  # lreg_c: L4; lreg_dest: L7
    9c8: ebf841c5  SFPSHFT      imm12_math=4065, lreg_c=0, lreg_dest=7, instr_mod1=1  # lreg_c: L0; lreg_dest: L7
    9cc: e7ffddd5  SFPIADD      imm12_math=4095, lreg_c=7, lreg_dest=7, instr_mod1=5  # lreg_c: L7; lreg_dest: L7
    9d0: f8001c01  SFPAND       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0
    9d4: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    9d8: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    9dc: fffa8a93  addi         x21, x21, -1
    9e0: fa0a96e3  bne          x21, x0, 0x0000098c  # target 0x0000098c
    9e4: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    9e8: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    9ec: fffa0a13  addi         x20, x20, -1
    9f0: f80a1ce3  bne          x20, x0, 0x00000988  # target 0x00000988
    9f4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    9f8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    9fc: 00008067  jalr         x0, 0(x1)
loc_a00:
    a00: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    a04: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7
    a08: c5e00001  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=0  # lreg_ind: L7
    a0c: 00000a13  addi         x20, x0, 0  # x20 = 0x00000000
    a10: 00400a93  addi         x21, x0, 4  # x21 = 0x00000004
loc_a14:
    a14: 0f5a7263  bgeu         x20, x21, 0x00000af8  # target 0x00000af8
    a18: 40310000  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    a1c: 40310004  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=1
    a20: 40310008  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=2
    a24: 4031000c  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=3
    a28: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a2c: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    a30: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a34: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a38: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a3c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    a40: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    a44: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    a48: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a4c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a50: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a54: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a58: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a5c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a60: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a64: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a68: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    a6c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    a70: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a74: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a78: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a7c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a80: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a84: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a88: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a8c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a90: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    a94: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    a98: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    a9c: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    aa0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    aa4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    aa8: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    aac: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ab0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ab4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ab8: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    abc: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    ac0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ac4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ac8: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    acc: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ad0: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ad4: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ad8: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    adc: 101500c0  REPLAY       start_idx=21, len=3, execute_while_loading=0, load_mode=0
    ae0: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    ae4: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    ae8: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    aec: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    af0: 001a0a13  addi         x20, x20, 1
    af4: f21ff06f  jal          x0, 0x00000a14  # target 0x00000a14
loc_af8:
    af8: f0001c01  SFPMOV       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0
    afc: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    b00: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    b04: 3c000002  SFPNOP
    b08: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    b0c: 3c000002  SFPNOP
    b10: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    b14: 3c000002  SFPNOP
    b18: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    b1c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    b20: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    b24: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    b28: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    b2c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    b30: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    b34: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    b38: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    b3c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    b40: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    b44: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    b48: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    b4c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    b50: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    b54: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    b58: 3c000002  SFPNOP
    b5c: 00008067  jalr         x0, 0(x1)
    b60:           j FW_TRISC1+4   # return to firmware, linked at install
