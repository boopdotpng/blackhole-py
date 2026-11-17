# llama3 1b decode: gate, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_b_decode_token, 0x784=e2e_l0_gate, 0x788=e2e_l0_up, 0x78c=e2e_hidden_dense, 0x790=e2e_l0_post_norm, 0x11940=e2e_gate, 0x11944=e2e_l0_gate_row_start, 0x11948=e2e_up, 0x1194c=e2e_l0_up_row_start, 0x11950=dense_start, 0x11954=e2e_l0_gate_rows, 0x11958=e2e_l0_up_rows, 0x1195c=dram_port
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
     28: c08f8201  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L2; Record replay[7]; not executed here
     2c: 4cc3800a  SFPLOADMACRO lreg_ind=3, instr_mod0=0, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L3; Record replay[8]; not executed here
     30: c10f8209  SFPLOAD      lreg_ind=4, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=130  # lreg_ind: L4; Record replay[9]; not executed here
     34: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1; Record replay[10]; not executed here
     38: 180d24c2  SFPMUL       lreg_src_a=3, lreg_src_b=4, lreg_src_c=9, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L3; Record replay[11]; not executed here
     3c: c84f8001  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1; Record replay[12]; not executed here
     40: c8cf8009  SFPSTORE     lreg_ind=3, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=2  # lreg_ind: L3; Record replay[13]; not executed here
     44: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[14]; not executed here
     48: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[15]; not executed here
     4c: 101000c4  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=1
     50: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[16]; not executed here
     54: 10029dc2  SFPMAD       lreg_src_a=0, lreg_src_b=10, lreg_src_c=7, lreg_dest=7, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L7; lreg_dest: L7; Record replay[17]; not executed here
     58: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[18]; not executed here
     5c: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
     60: 3c000002  SFPNOP
     64: 18002702  SFPMUL       lreg_src_a=0, lreg_src_b=0, lreg_src_c=9, lreg_dest=12, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L0; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L12
     68: 46100106  SFPCONFIG    imm16_math=33792, config_dest=4, instr_mod1=1
     6c: 443c0206  SFPCONFIG    imm16_math=3840, config_dest=8, instr_mod1=1
     70: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     74: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     78: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     7c: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     80: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
     84: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     88: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     8c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     90: 00507033  and          x0, x0, x5
     94: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
     98: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     9c: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
     a0: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
     a4: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     a8: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     ac: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP
     b0: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
     b4: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
     b8: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     bc: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     c0: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
     c4: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     c8: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     cc: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
     d0: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP
     d4: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
     d8: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     dc: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     e0: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
     e4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
     e8: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
     ec: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
     f0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
     f4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
     f8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
     fc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    100: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    104: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    108: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    10c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    110: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    114: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    118: c8040202  SETC16       setc16_reg=1, setc16_value=128  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 128
    11c: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    120: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    124: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    128: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    12c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    130: c8040302  SETC16       setc16_reg=1, setc16_value=192  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 192
    134: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    138: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    13c: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    140: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    144: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    148: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    14c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    150: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    154: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    158: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    15c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    160: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    164: c4000001  SFPLOADI     lreg_ind=0, instr_mod0=0, imm16=0  # lreg_ind: L0
    168: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    16c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    170: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    174: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    178: 00507033  and          x0, x0, x5
    17c: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    180: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    184: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000001
    188: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
    18c: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    190: 371202b7  lui          x5, 0x37120  # x5 = 0x37120000
    194: 00428293  addi         x5, x5, 4  # x5 = 0x37120004
    198: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    19c: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1a0: 040002b7  lui          x5, 0x04000  # x5 = 0x04000000
    1a4: 03028293  addi         x5, x5, 48  # x5 = 0x04000030
    1a8: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    1ac: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    1b0: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04000030; MOP template instruction · REPLAY start_idx=0, len=3, execute_while_loading=0, load_mode=0
    1b4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1bc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1c0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1c4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    1c8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1cc: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    1d0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    1d4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    1d8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    1dc: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    1e0: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    1e4: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    1e8: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    1ec: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    1f0: 00507033  and          x0, x0, x5
    1f4: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    1f8: 01420213  addi         x4, x4, 20  # x4 = 0xffb80014 · MopCfg[5] · LoopOp / InsnA2
    1fc: 0400c2b7  lui          x5, 0x0400c  # x5 = 0x0400c000
    200: 03028293  addi         x5, x5, 48  # x5 = 0x0400c030
    204: 00522023  sw           x5, 0(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    208: 00522423  sw           x5, 8(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    20c: 00522623  sw           x5, 12(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x0400c030; MOP template instruction · REPLAY start_idx=3, len=3, execute_while_loading=0, load_mode=0
    210: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    214: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    218: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    21c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    220: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    224: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    228: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    22c: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    230: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    234: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    238: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    23c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    240: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    244: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    248: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    24c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    250: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    254: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    258: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    25c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    260: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    264: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    268: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    26c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    270: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    274: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    278: c5280001  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=0  # lreg_ind: L4
    27c: c520e801  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=14848  # lreg_ind: L4
    280: 18012402  SFPMUL       lreg_src_a=0, lreg_src_b=4, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L4; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    284: c52b16b1  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=50604  # lreg_ind: L4
    288: c520dc9d  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=14119  # lreg_ind: L4
    28c: 14281002  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=4, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L4; lreg_dest: L0
    290: f0000181  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=6, instr_mod1=0  # lreg_c: L0; lreg_dest: L6
    294: f0001841  SFPMOV       imm12_math=0, lreg_c=6, lreg_dest=1, instr_mod1=0  # lreg_c: L6; lreg_dest: L1
    298: ebffe445  SFPSHFT      imm12_math=4095, lreg_c=9, lreg_dest=1, instr_mod1=1  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    29c: c4a84281  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=4256  # lreg_ind: L2
    2a0: c4a17c45  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=24337  # lreg_ind: L2
    2a4: e4000859  SFPIADD      imm12_math=0, lreg_c=2, lreg_dest=1, instr_mod1=6  # lreg_c: L2; lreg_dest: L1
    2a8: 18186482  SFPMUL       lreg_src_a=6, lreg_src_b=1, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L6; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    2ac: 1804a486  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=2, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    2b0: c4e85325  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=5321  # lreg_ind: L3
    2b4: c4e10049  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16402  # lreg_ind: L3
    2b8: c528d899  SFPLOADI     lreg_ind=4, instr_mod0=10, imm16=13862  # lreg_ind: L4
    2bc: c5210041  SFPLOADI     lreg_ind=4, instr_mod0=8, imm16=16400  # lreg_ind: L4
    2c0: 14290902  SFPADD       lreg_src_a=10, lreg_src_b=4, lreg_src_c=2, lreg_dest=4, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L4; lreg_src_c: L2; lreg_dest: L4
    2c4: 10090c82  SFPMAD       lreg_src_a=2, lreg_src_b=4, lreg_src_c=3, lreg_dest=2, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L2
    2c8: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    2cc: 18186482  SFPMUL       lreg_src_a=6, lreg_src_b=1, lreg_src_c=9, lreg_dest=2, instr_mod1=0  # lreg_src_a: L6; lreg_src_b: L1; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    2d0: 1804a486  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=2, instr_mod1=1  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L2
    2d4: 142a8882  SFPADD       lreg_src_a=10, lreg_src_b=10, lreg_src_c=2, lreg_dest=2, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L2; lreg_dest: L2
    2d8: c5680001  SFPLOADI     lreg_ind=5, instr_mod0=10, imm16=0  # lreg_ind: L5
    2dc: c560fc01  SFPLOADI     lreg_ind=5, instr_mod0=8, imm16=16128  # lreg_ind: L5
    2e0: 18056542  SFPMUL       lreg_src_a=1, lreg_src_b=5, lreg_src_c=9, lreg_dest=5, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L5; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L5
    2e4: 10094402  SFPMAD       lreg_src_a=2, lreg_src_b=5, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L5; lreg_src_c: L1; lreg_dest: L0
    2e8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2ec: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    2f0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2f4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2f8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2fc: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    300: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    304: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    308: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    30c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    310: 00507033  and          x0, x0, x5
    314: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    318: 00420213  addi         x4, x4, 4  # x4 = 0xffb80004 · MopCfg[1] · InnerCount / Flags
    31c: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    320: 00522023  sw           x5, 0(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000004
    324: 040182b7  lui          x5, 0x04018  # x5 = 0x04018000
    328: 0a028293  addi         x5, x5, 160  # x5 = 0x040180a0
    32c: 00522823  sw           x5, 16(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    330: 00522c23  sw           x5, 24(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    334: 00522e23  sw           x5, 28(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x040180a0; MOP template instruction · REPLAY start_idx=6, len=10, execute_while_loading=0, load_mode=0
    338: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    33c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    340: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    344: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    348: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    34c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    350: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    354: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    358: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    35c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    360: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    364: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    368: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    36c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    370: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    374: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    378: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    37c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    380: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    384: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    388: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    38c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    390: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    394: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    398: c8302022  SETC16       setc16_reg=12, setc16_value=2056  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 8; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    39c: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    3a0: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    3a4: c8340002  SETC16       setc16_reg=13, setc16_value=0  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 0; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 0; ADDR_MOD_AB_SEC1_SrcBClear = 0
    3a8: c8740002  SETC16       setc16_reg=29, setc16_value=0  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 0; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    3ac: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    3b0: c83a0202  SETC16       setc16_reg=14, setc16_value=32896  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 1; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 1
    3b4: c8789002  SETC16       setc16_reg=30, setc16_value=9216  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 0; ADDR_MOD_DST_SEC2_DestCR = 1; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 1; ADDR_MOD_DST_SEC2_FidelityClear = 0
    3b8: c83e0202  SETC16       setc16_reg=15, setc16_value=32896  # thread_cfg[15] (current thread); ADDR_MOD_AB_SEC3_SrcAIncr = 0; ADDR_MOD_AB_SEC3_SrcACR = 0; ADDR_MOD_AB_SEC3_SrcAClear = 1; ADDR_MOD_AB_SEC3_SrcBIncr = 0; ADDR_MOD_AB_SEC3_SrcBCR = 0; ADDR_MOD_AB_SEC3_SrcBClear = 1
    3bc: c87e4022  SETC16       setc16_reg=31, setc16_value=36872  # thread_cfg[31] (current thread); ADDR_MOD_DST_SEC3_DestIncr = 8; ADDR_MOD_DST_SEC3_DestCR = 0; ADDR_MOD_DST_SEC3_DestClear = 0; ADDR_MOD_DST_SEC3_DestCToCR = 1; ADDR_MOD_DST_SEC3_FidelityIncr = 0; ADDR_MOD_DST_SEC3_FidelityClear = 1
    3c0: c8c80002  SETC16       setc16_reg=50, setc16_value=0  # thread_cfg[50] (current thread); ADDR_MOD_BIAS_SEC3_BiasIncr = 0; ADDR_MOD_BIAS_SEC3_BiasClear = 0
    3c4: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    3c8: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    3cc: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    3d0: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    3d4: 00507033  and          x0, x0, x5
    3d8: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    3dc: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    3e0: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000002
    3e4: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    3e8: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    3ec: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP
    3f0: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP
    3f4: 270002b7  lui          x5, 0x27000  # x5 = 0x27000000
    3f8: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x27000000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0
    3fc: 27c0c2b7  lui          x5, 0x27c0c  # x5 = 0x27c0c000
    400: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x27c0c000; MOP template instruction · ELWMUL clear_dvalid=3, dest_accum_en=0, instr_mod19=0, addr_mode=3, dst=0
    404: 270082b7  lui          x5, 0x27008  # x5 = 0x27008000
    408: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x27008000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    40c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    410: 95428293  addi         x5, x5, -1708  # x5 = 0x00011954
    414: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x00011954
    418: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    41c: 00020313  addi         x6, x4, 0
loc_420:
    420: 0062fe63  bgeu         x5, x6, 0x0000043c  # target 0x0000043c
    424: 1fc000ef  jal          x1, 0x00000620  # target 0x00000620; x1 = 0x00000428
    428: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    42c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    430: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    434: 00128293  addi         x5, x5, 1
    438: fe9ff06f  jal          x0, 0x00000420  # target 0x00000420
loc_43c:
    43c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    440: 95828293  addi         x5, x5, -1704  # x5 = 0x00011958
    444: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x00011958
    448: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    44c: 00020313  addi         x6, x4, 0
loc_450:
    450: 0062fe63  bgeu         x5, x6, 0x0000046c  # target 0x0000046c
    454: 1cc000ef  jal          x1, 0x00000620  # target 0x00000620; x1 = 0x00000458
    458: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    45c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    460: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    464: 00128293  addi         x5, x5, 1
    468: fe9ff06f  jal          x0, 0x00000450  # target 0x00000450
loc_46c:
    46c: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    470: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    474: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    478: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    47c: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    480: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    484: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    488: 00507033  and          x0, x0, x5
    48c: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    490: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    494: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
    498: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
    49c: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
    4a0: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    4a4: 1200a2b7  lui          x5, 0x1200a  # x5 = 0x1200a000
    4a8: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    4ac: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    4b0: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    4b4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    4b8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4bc: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    4c0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4c4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4c8: c8040102  SETC16       setc16_reg=1, setc16_value=64  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 64
    4cc: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    4d0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4d4: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    4d8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    4dc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4e0: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    4e4: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    4e8: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    4ec: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    4f0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    4f4: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    4f8: c42aa8ed  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=43579  # lreg_ind: L0
    4fc: c420fee1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=16312  # lreg_ind: L0
    500: 44000302  SFPCONFIG    imm16_math=0, config_dest=12, instr_mod1=0
    504: c42a9061  SFPLOADI     lreg_ind=0, instr_mod0=10, imm16=42008  # lreg_ind: L0
    508: c4209eb1  SFPLOADI     lreg_ind=0, instr_mod0=8, imm16=10156  # lreg_ind: L0
    50c: 44000342  SFPCONFIG    imm16_math=0, config_dest=13, instr_mod1=0
    510: c4680001  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=0  # lreg_ind: L1
    514: c4610bf9  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=17150  # lreg_ind: L1
    518: c4a96b69  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=23258  # lreg_ind: L2
    51c: c4a0cea1  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=13224  # lreg_ind: L2
    520: c4e8e215  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=14469  # lreg_ind: L3
    524: c4e0fe01  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=16256  # lreg_ind: L3
    528: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_52c:
    52c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_530:
    530: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    534: c80f8201  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L0
    538: 1802e402  SFPMUL       lreg_src_a=0, lreg_src_b=11, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L11 · programmable; ttsim reset -1 (0xbf800000); lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    53c: 10030582  SFPMAD       lreg_src_a=0, lreg_src_b=12, lreg_src_c=1, lreg_dest=6, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L12 · programmable; ttsim reset 0.00195312 (0x3b000000); lreg_src_c: L1; lreg_dest: L6
    540: c5010dfd  SFPLOADI     lreg_ind=4, instr_mod0=0, imm16=17279  # lreg_ind: L4
    544: 48001186  SFPSWAP      imm12_math=0, lreg_src_c=4, lreg_dest=6, instr_mod1=1  # lreg_src_c: L4; lreg_dest: L6
    548: dc001901  SFPEXEXP     imm12_math=0, lreg_c=6, lreg_dest=4, instr_mod1=0  # lreg_c: L6; lreg_dest: L4
    54c: e0001801  SFPEXMAN     imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=0  # lreg_c: L6; lreg_dest: L0
    550: e8001001  SFPSHFT      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=0  # lreg_c: L4; lreg_dest: L0
    554: e0000105  SFPEXMAN     imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4
    558: 40001102  SFPCAST      lreg_src_c=4, lreg_dest=4, instr_mod1=0  # lreg_src_c: L4; lreg_dest: L4
    55c: 10134942  SFPMAD       lreg_src_a=4, lreg_src_b=13, lreg_src_c=2, lreg_dest=5, instr_mod1=0  # lreg_src_a: L4; lreg_src_b: L13 · programmable; ttsim reset -0.674878 (0xbf2cc4c7); lreg_src_c: L2; lreg_dest: L5
    560: 5c0025a2  SFPGT        imm12_math=0, lreg_c=9, lreg_dest=6, instr_mod1=8  # lreg_c: L9 · constant 0 (0x00000000); lreg_dest: L6
    564: 10150d02  SFPMAD       lreg_src_a=5, lreg_src_b=4, lreg_src_c=3, lreg_dest=4, instr_mod1=0  # lreg_src_a: L5; lreg_src_b: L4; lreg_src_c: L3; lreg_dest: L4
    568: f8001805  SFPAND       imm12_math=0, lreg_c=6, lreg_dest=0, instr_mod1=1  # lreg_c: L6; lreg_dest: L0
    56c: 0800100a  SFPSETEXP    imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=2  # lreg_c: L4; lreg_dest: L0
    570: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    574: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    578: fffa8a93  addi         x21, x21, -1
    57c: fa0a9ae3  bne          x21, x0, 0x00000530  # target 0x00000530
    580: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    584: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    588: fffa0a13  addi         x20, x20, -1
    58c: fa0a10e3  bne          x20, x0, 0x0000052c  # target 0x0000052c
    590: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    594: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    598: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    59c: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    5a0: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    5a4: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    5a8: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    5ac: 00400a13  addi         x20, x0, 4  # x20 = 0x00000004
loc_5b0:
    5b0: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
loc_5b4:
    5b4: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    5b8: d4fe0001  SFPADDI      imm16_math=16256, lreg_dest=0, instr_mod1=0  # lreg_dest: L0
    5bc: 3c000002  SFPNOP
    5c0: 64000042  SFPARECIP    imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    5c4: 10006886  SFPMAD       lreg_src_a=0, lreg_src_b=1, lreg_src_c=10, lreg_dest=2, instr_mod1=1  # lreg_src_a: L0; lreg_src_b: L1; lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L2
    5c8: 100888c2  SFPMAD       lreg_src_a=2, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L2; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    5cc: 100c88c2  SFPMAD       lreg_src_a=3, lreg_src_b=2, lreg_src_c=2, lreg_dest=3, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L2; lreg_src_c: L2; lreg_dest: L3
    5d0: 3c000002  SFPNOP
    5d4: 480028c6  SFPSWAP      imm12_math=0, lreg_src_c=10, lreg_dest=3, instr_mod1=1  # lreg_src_c: L10 · constant 1 (0x3f800000); lreg_dest: L3
    5d8: 100c4402  SFPMAD       lreg_src_a=3, lreg_src_b=1, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L3; lreg_src_b: L1; lreg_src_c: L1; lreg_dest: L0
    5dc: c04f8201  SFPLOAD      lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=128  # lreg_ind: L1
    5e0: c08f8101  SFPLOAD      lreg_ind=2, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=64  # lreg_ind: L2
    5e4: 18042442  SFPMUL       lreg_src_a=1, lreg_src_b=0, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L0; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    5e8: 1804a442  SFPMUL       lreg_src_a=1, lreg_src_b=2, lreg_src_c=9, lreg_dest=1, instr_mod1=0  # lreg_src_a: L1; lreg_src_b: L2; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L1
    5ec: c84f8001  SFPSTORE     lreg_ind=1, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L1
    5f0: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0
    5f4: fffa8a93  addi         x21, x21, -1
    5f8: fa0a9ee3  bne          x21, x0, 0x000005b4  # target 0x000005b4
    5fc: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    600: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    604: fffa0a13  addi         x20, x20, -1
    608: fa0a14e3  bne          x20, x0, 0x000005b0  # target 0x000005b0
    60c: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    610: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    614: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    618: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    61c: 1640006f  jal          x0, 0x00000780  # target 0x00000780
loc_620:
    620: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    624: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7
    628: c5e00001  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=0  # lreg_ind: L7
    62c: 00000a13  addi         x20, x0, 0  # x20 = 0x00000000
    630: 00200a93  addi         x21, x0, 2  # x21 = 0x00000002
loc_634:
    634: 0f5a7263  bgeu         x20, x21, 0x00000718  # target 0x00000718
    638: 40310000  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    63c: 40310004  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=1
    640: 40310008  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=2
    644: 4031000c  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=3
    648: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    64c: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    650: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    654: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    658: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    65c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    660: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    664: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    668: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    66c: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    670: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    674: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    678: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    67c: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    680: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    684: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    688: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    68c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    690: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    694: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    698: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    69c: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6a0: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6a4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6a8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6ac: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6b0: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    6b4: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    6b8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6bc: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6c0: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6c4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6c8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6cc: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6d0: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6d4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6d8: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    6dc: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    6e0: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6e4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6e8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6ec: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6f0: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6f4: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6f8: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    6fc: 101000c0  REPLAY       start_idx=16, len=3, execute_while_loading=0, load_mode=0
    700: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    704: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    708: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    70c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    710: 001a0a13  addi         x20, x20, 1
    714: f21ff06f  jal          x0, 0x00000634  # target 0x00000634
loc_718:
    718: f0001c01  SFPMOV       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0
    71c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    720: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    724: 3c000002  SFPNOP
    728: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    72c: 3c000002  SFPNOP
    730: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    734: 3c000002  SFPNOP
    738: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    73c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    740: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    744: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    748: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    74c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    750: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    754: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    758: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    75c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    760: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    764: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    768: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    76c: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    770: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    774: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    778: 3c000002  SFPNOP
    77c: 00008067  jalr         x0, 0(x1)
    780:           j FW_TRISC1+4   # return to firmware, linked at install
