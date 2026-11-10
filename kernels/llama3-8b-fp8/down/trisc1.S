# llama3 8b-fp8 decode: down, trisc1. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_hidden_dense_decode_token, 0x784=e2e_l0_down, 0x788=input_scale_0, 0x78c=input_scale_1, 0x790=output_scale_0_0, 0x794=output_scale_0_1, 0x798=e2e_x_a, 0x79c=e2e_x_b, 0xe980=e2e_q_compact, 0xe984=e2e_l0_down_row_start, 0xe988=dense_start, 0xe98c=e2e_l0_down_rows
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: 10000144  REPLAY       start_idx=0, len=5, execute_while_loading=0, load_mode=1
      4: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[0]; not executed here
      8: 1801a402  SFPMUL       lreg_src_a=0, lreg_src_b=6, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L6; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0; Record replay[1]; not executed here
      c: 3c000002  SFPNOP         # Record replay[2]; not executed here
     10: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[3]; not executed here
     14: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[4]; not executed here
     18: 10050584  REPLAY       start_idx=5, len=22, execute_while_loading=0, load_mode=1
     1c: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[5]; not executed here
     20: f0000101  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=0  # lreg_c: L0; lreg_dest: L4; Record replay[6]; not executed here
     24: ebfb0105  SFPSHFT      imm12_math=4076, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4; Record replay[7]; not executed here
     28: f8000901  SFPAND       imm12_math=0, lreg_c=2, lreg_dest=4, instr_mod1=0  # lreg_c: L2; lreg_dest: L4; Record replay[8]; not executed here
     2c: e4000511  SFPIADD      imm12_math=0, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Record replay[9]; not executed here
     30: e4001011  SFPIADD      imm12_math=0, lreg_c=4, lreg_dest=0, instr_mod1=4  # lreg_c: L4; lreg_dest: L0; Record replay[10]; not executed here
     34: f8000c01  SFPAND       imm12_math=0, lreg_c=3, lreg_dest=0, instr_mod1=0  # lreg_c: L3; lreg_dest: L0; Record replay[11]; not executed here
     38: f00015c1  SFPMOV       imm12_math=0, lreg_c=5, lreg_dest=7, instr_mod1=0  # lreg_c: L5; lreg_dest: L7; Record replay[12]; not executed here
     3c: 48001c06  SFPSWAP      imm12_math=0, lreg_src_c=7, lreg_dest=0, instr_mod1=1  # lreg_src_c: L7; lreg_dest: L0; Record replay[13]; not executed here
     40: 3c000002  SFPNOP         # Record replay[14]; not executed here
     44: f00019c1  SFPMOV       imm12_math=0, lreg_c=6, lreg_dest=7, instr_mod1=0  # lreg_c: L6; lreg_dest: L7; Record replay[15]; not executed here
     48: 480001c6  SFPSWAP      imm12_math=0, lreg_src_c=0, lreg_dest=7, instr_mod1=1  # lreg_src_c: L0; lreg_dest: L7; Record replay[16]; not executed here
     4c: 3c000002  SFPNOP         # Record replay[17]; not executed here
     50: f4000105  SFPABS       imm12_math=0, lreg_c=0, lreg_dest=4, instr_mod1=1  # lreg_c: L0; lreg_dest: L4; Record replay[18]; not executed here
     54: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7; Record replay[19]; not executed here
     58: c5e0f201  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=15488  # lreg_ind: L7; Record replay[20]; not executed here
     5c: e40011d9  SFPIADD      imm12_math=0, lreg_c=4, lreg_dest=7, instr_mod1=6  # lreg_c: L4; lreg_dest: L7; Record replay[21]; not executed here
     60: ebf841c5  SFPSHFT      imm12_math=4065, lreg_c=0, lreg_dest=7, instr_mod1=1  # lreg_c: L0; lreg_dest: L7; Record replay[22]; not executed here
     64: e7ffddd5  SFPIADD      imm12_math=4095, lreg_c=7, lreg_dest=7, instr_mod1=5  # lreg_c: L7; lreg_dest: L7; Record replay[23]; not executed here
     68: f8001c01  SFPAND       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0; Record replay[24]; not executed here
     6c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[25]; not executed here
     70: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[26]; not executed here
     74: 101b00c4  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=1
     78: c00f8001  SFPLOAD      lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0; Record replay[27]; not executed here
     7c: 10029dc2  SFPMAD       lreg_src_a=0, lreg_src_b=10, lreg_src_c=7, lreg_dest=7, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L10 · constant 1 (0x3f800000); lreg_src_c: L7; lreg_dest: L7; Record replay[28]; not executed here
     80: e0020000  INCRWC       rwc_cr=0, rwc_d=2, rwc_b=0, rwc_a=0  # Record replay[29]; not executed here
     84: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
     88: 00e00293  addi         x5, x0, 14  # x5 = 0x0000000e
loc_8c:
     8c: 22527863  bgeu         x4, x5, 0x000002bc  # target 0x000002bc
     90: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
     94: c8380022  SETC16       setc16_reg=14, setc16_value=8  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
     98: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
     9c: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
     a0: ffe80337  lui          x6, 0xffe80  # x6 = 0xffe80000 · tensix_pc_buf + 0x0
     a4: 00830313  addi         x6, x6, 8  # x6 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
     a8: 00032023  sw           x0, 0(x6)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
     ac: 00032383  lw           x7, 0(x6)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
     b0: 00707033  and          x0, x0, x7
     b4: ffb80337  lui          x6, 0xffb80  # x6 = 0xffb80000 · MOP_CFG
     b8: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     bc: 00732023  sw           x7, 0(x6)  # MOP_CFG · 0xffb80000; write 0x00000004
     c0: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
     c4: 00732223  sw           x7, 4(x6)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
     c8: 020003b7  lui          x7, 0x02000  # x7 = 0x02000000
     cc: 00732423  sw           x7, 8(x6)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
     d0: 37c003b7  lui          x7, 0x37c00  # x7 = 0x37c00000
     d4: 00338393  addi         x7, x7, 3  # x7 = 0x37c00003
     d8: 00732623  sw           x7, 12(x6)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
     dc: 020003b7  lui          x7, 0x02000  # x7 = 0x02000000
     e0: 00732823  sw           x7, 16(x6)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
     e4: 1200a3b7  lui          x7, 0x1200a  # x7 = 0x1200a000
     e8: 00732a23  sw           x7, 20(x6)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     ec: 020003b7  lui          x7, 0x02000  # x7 = 0x02000000
     f0: 00732c23  sw           x7, 24(x6)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
     f4: 1200a3b7  lui          x7, 0x1200a  # x7 = 0x1200a000
     f8: 00732e23  sw           x7, 28(x6)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
     fc: 02732023  sw           x7, 32(x6)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x1200a000; MOP template instruction · MOVA2D dest_32b_lo=0, src=0, addr_mode=2, instr_mod=2, dst=0
    100: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    104: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    108: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    10c: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    110: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    114: 88800202  STALLWAIT    stall_res=64, wait_res=128  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD
    118: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    11c: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    120: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    124: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
    128: 0003a303  lw           x6, 0(x7)  # param input_scale_0; 0x00000788
    12c: ffe403b7  lui          x7, 0xffe40  # x7 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    130: 0063a023  sw           x6, 0(x7)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    134: 78c00393  addi         x7, x0, 1932  # x7 = 0x0000078c
    138: 0003a303  lw           x6, 0(x7)  # param input_scale_1; 0x0000078c
    13c: ffe403b7  lui          x7, 0xffe40  # x7 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    140: 0063a023  sw           x6, 0(x7)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    144: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    148: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    14c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    150: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    154: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    158: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    15c: 3c000002  SFPNOP       
    160: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    164: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    168: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    16c: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    170: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    174: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    178: 01507033  and          x0, x0, x21
    17c: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    180: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    184: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    188: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    18c: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    190: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    194: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
    198: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    19c: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    1a0: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1a4: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    1a8: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    1ac: 050a8a93  addi         x21, x21, 80  # x21 = 0x04000050
    1b0: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04000050; MOP template instruction · REPLAY start_idx=0, len=5, execute_while_loading=0, load_mode=0
    1b4: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    1b8: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    1bc: 04000ab7  lui          x21, 0x04000  # x21 = 0x04000000
    1c0: 050a8a93  addi         x21, x21, 80  # x21 = 0x04000050
    1c4: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04000050; MOP template instruction · REPLAY start_idx=0, len=5, execute_while_loading=0, load_mode=0
    1c8: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04000050; MOP template instruction · REPLAY start_idx=0, len=5, execute_while_loading=0, load_mode=0
    1cc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1d0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1d4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1d8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    1dc: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    1e0: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    1e4: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    1e8: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    1ec: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    1f0: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    1f4: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    1f8: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    1fc: 3c000002  SFPNOP       
    200: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    204: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    208: c46bfffd  SFPLOADI     lreg_ind=1, instr_mod0=10, imm16=65535  # lreg_ind: L1
    20c: c460001d  SFPLOADI     lreg_ind=1, instr_mod0=8, imm16=7  # lreg_ind: L1
    210: c4a80005  SFPLOADI     lreg_ind=2, instr_mod0=10, imm16=1  # lreg_ind: L2
    214: c4a00001  SFPLOADI     lreg_ind=2, instr_mod0=8, imm16=0  # lreg_ind: L2
    218: c4e80001  SFPLOADI     lreg_ind=3, instr_mod0=10, imm16=0  # lreg_ind: L3
    21c: c4e3ffc1  SFPLOADI     lreg_ind=3, instr_mod0=8, imm16=65520  # lreg_ind: L3
    220: c5680001  SFPLOADI     lreg_ind=5, instr_mod0=10, imm16=0  # lreg_ind: L5
    224: c5610f81  SFPLOADI     lreg_ind=5, instr_mod0=8, imm16=17376  # lreg_ind: L5
    228: c5a80001  SFPLOADI     lreg_ind=6, instr_mod0=10, imm16=0  # lreg_ind: L6
    22c: c5a30f81  SFPLOADI     lreg_ind=6, instr_mod0=8, imm16=50144  # lreg_ind: L6
    230: ffe80a37  lui          x20, 0xffe80  # x20 = 0xffe80000 · tensix_pc_buf + 0x0
    234: 008a0a13  addi         x20, x20, 8  # x20 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    238: 000a2023  sw           x0, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    23c: 000a2a83  lw           x21, 0(x20)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    240: 01507033  and          x0, x0, x21
    244: ffb80a37  lui          x20, 0xffb80  # x20 = 0xffb80000 · MOP_CFG
    248: 00100a93  addi         x21, x0, 1  # x21 = 0x00000001
    24c: 015a2023  sw           x21, 0(x20)  # MOP_CFG · 0xffb80000; write 0x00000001
    250: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    254: 015a2223  sw           x21, 4(x20)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000008
    258: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    25c: 015a2423  sw           x21, 8(x20)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
    260: 37120ab7  lui          x21, 0x37120  # x21 = 0x37120000
    264: 004a8a93  addi         x21, x21, 4  # x21 = 0x37120004
    268: 015a2623  sw           x21, 12(x20)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    26c: 015a2823  sw           x21, 16(x20)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x37120004; MOP template instruction · SETRWC clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    270: 04014ab7  lui          x21, 0x04014  # x21 = 0x04014000
    274: 160a8a93  addi         x21, x21, 352  # x21 = 0x04014160
    278: 015a2a23  sw           x21, 20(x20)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x04014160; MOP template instruction · REPLAY start_idx=5, len=22, execute_while_loading=0, load_mode=0
    27c: 02000ab7  lui          x21, 0x02000  # x21 = 0x02000000
    280: 015a2c23  sw           x21, 24(x20)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    284: 04014ab7  lui          x21, 0x04014  # x21 = 0x04014000
    288: 160a8a93  addi         x21, x21, 352  # x21 = 0x04014160
    28c: 015a2e23  sw           x21, 28(x20)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x04014160; MOP template instruction · REPLAY start_idx=5, len=22, execute_while_loading=0, load_mode=0
    290: 035a2023  sw           x21, 32(x20)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x04014160; MOP template instruction · REPLAY start_idx=5, len=22, execute_while_loading=0, load_mode=0
    294: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    298: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    29c: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2a0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    2a4: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    2a8: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2ac: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    2b0: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    2b4: 00120213  addi         x4, x4, 1
    2b8: dd5ff06f  jal          x0, 0x0000008c  # target 0x0000008c
loc_2bc:
    2bc: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    2c0: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    2c4: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    2c8: d8808006  RMWCIB3      Mask=32, Data=32, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 1
    2cc: 89002002  STALLWAIT    stall_res=128, wait_res=2048  # stall_res: Stall.CFG; wait_res: Wait.SFPU
    2d0: d9010006  RMWCIB3      Mask=64, Data=64, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_SFPU_Fp32_enabled = 1
    2d4: 440003c6  SFPCONFIG    imm16_math=0, config_dest=15, instr_mod1=1
    2d8: 3c000002  SFPNOP       
    2dc: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    2e0: c8302022  SETC16       setc16_reg=12, setc16_value=2056  # thread_cfg[12] (current thread); ADDR_MOD_AB_SEC0_SrcAIncr = 8; ADDR_MOD_AB_SEC0_SrcACR = 0; ADDR_MOD_AB_SEC0_SrcAClear = 0; ADDR_MOD_AB_SEC0_SrcBIncr = 8; ADDR_MOD_AB_SEC0_SrcBCR = 0; ADDR_MOD_AB_SEC0_SrcBClear = 0
    2e4: c8700022  SETC16       setc16_reg=28, setc16_value=8  # thread_cfg[28] (current thread); ADDR_MOD_DST_SEC0_DestIncr = 8; ADDR_MOD_DST_SEC0_DestCR = 0; ADDR_MOD_DST_SEC0_DestClear = 0; ADDR_MOD_DST_SEC0_DestCToCR = 0; ADDR_MOD_DST_SEC0_FidelityIncr = 0; ADDR_MOD_DST_SEC0_FidelityClear = 0
    2e8: c8bc0002  SETC16       setc16_reg=47, setc16_value=0  # thread_cfg[47] (current thread); ADDR_MOD_BIAS_SEC0_BiasIncr = 0; ADDR_MOD_BIAS_SEC0_BiasClear = 0
    2ec: c8340002  SETC16       setc16_reg=13, setc16_value=0  # thread_cfg[13] (current thread); ADDR_MOD_AB_SEC1_SrcAIncr = 0; ADDR_MOD_AB_SEC1_SrcACR = 0; ADDR_MOD_AB_SEC1_SrcAClear = 0; ADDR_MOD_AB_SEC1_SrcBIncr = 0; ADDR_MOD_AB_SEC1_SrcBCR = 0; ADDR_MOD_AB_SEC1_SrcBClear = 0
    2f0: c8740002  SETC16       setc16_reg=29, setc16_value=0  # thread_cfg[29] (current thread); ADDR_MOD_DST_SEC1_DestIncr = 0; ADDR_MOD_DST_SEC1_DestCR = 0; ADDR_MOD_DST_SEC1_DestClear = 0; ADDR_MOD_DST_SEC1_DestCToCR = 0; ADDR_MOD_DST_SEC1_FidelityIncr = 0; ADDR_MOD_DST_SEC1_FidelityClear = 0
    2f4: c8c00002  SETC16       setc16_reg=48, setc16_value=0  # thread_cfg[48] (current thread); ADDR_MOD_BIAS_SEC1_BiasIncr = 0; ADDR_MOD_BIAS_SEC1_BiasClear = 0
    2f8: c83a0202  SETC16       setc16_reg=14, setc16_value=32896  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 0; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 1; ADDR_MOD_AB_SEC2_SrcBIncr = 0; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 1
    2fc: c8789002  SETC16       setc16_reg=30, setc16_value=9216  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 0; ADDR_MOD_DST_SEC2_DestCR = 1; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 1; ADDR_MOD_DST_SEC2_FidelityClear = 0
    300: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    304: c83e0202  SETC16       setc16_reg=15, setc16_value=32896  # thread_cfg[15] (current thread); ADDR_MOD_AB_SEC3_SrcAIncr = 0; ADDR_MOD_AB_SEC3_SrcACR = 0; ADDR_MOD_AB_SEC3_SrcAClear = 1; ADDR_MOD_AB_SEC3_SrcBIncr = 0; ADDR_MOD_AB_SEC3_SrcBCR = 0; ADDR_MOD_AB_SEC3_SrcBClear = 1
    308: c87e4022  SETC16       setc16_reg=31, setc16_value=36872  # thread_cfg[31] (current thread); ADDR_MOD_DST_SEC3_DestIncr = 8; ADDR_MOD_DST_SEC3_DestCR = 0; ADDR_MOD_DST_SEC3_DestClear = 0; ADDR_MOD_DST_SEC3_DestCToCR = 1; ADDR_MOD_DST_SEC3_FidelityIncr = 0; ADDR_MOD_DST_SEC3_FidelityClear = 1
    30c: c8c80002  SETC16       setc16_reg=50, setc16_value=0  # thread_cfg[50] (current thread); ADDR_MOD_BIAS_SEC3_BiasIncr = 0; ADDR_MOD_BIAS_SEC3_BiasClear = 0
    310: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    314: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    318: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    31c: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    320: 00507033  and          x0, x0, x5
    324: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    328: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    32c: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000001
    330: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    334: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    338: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    33c: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
    340: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x02000000; MOP template instruction · NOP 
    344: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    348: 270002b7  lui          x5, 0x27000  # x5 = 0x27000000
    34c: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x27000000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=0, dst=0
    350: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    354: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    358: 27c0c2b7  lui          x5, 0x27c0c  # x5 = 0x27c0c000
    35c: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x27c0c000; MOP template instruction · ELWMUL clear_dvalid=3, dest_accum_en=0, instr_mod19=0, addr_mode=3, dst=0
    360: 270082b7  lui          x5, 0x27008  # x5 = 0x27008000
    364: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x27008000; MOP template instruction · ELWMUL clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    368: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    36c: 98c28293  addi         x5, x5, -1652  # x5 = 0x0000e98c
    370: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000e98c
    374: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    378: 00020313  addi         x6, x4, 0
loc_37c:
    37c: 1c62f463  bgeu         x5, x6, 0x00000544  # target 0x00000544
    380: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    384: c5e80001  SFPLOADI     lreg_ind=7, instr_mod0=10, imm16=0  # lreg_ind: L7
    388: c5e00001  SFPLOADI     lreg_ind=7, instr_mod0=8, imm16=0  # lreg_ind: L7
    38c: 00000a13  addi         x20, x0, 0  # x20 = 0x00000000
    390: 00e00a93  addi         x21, x0, 14  # x21 = 0x0000000e
loc_394:
    394: 0f5a7263  bgeu         x20, x21, 0x00000478  # target 0x00000478
    398: 40310000  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=0
    39c: 40310004  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=1
    3a0: 40310008  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=2
    3a4: 4031000c  ZEROACC      clear_mode=1, use_32_bit_mode=1, clear_zero_flags=0, addr_mode=1, where=3
    3a8: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3ac: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    3b0: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    3b4: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    3b8: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    3bc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    3c0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    3c4: 8a000042  STALLWAIT    stall_res=256, wait_res=16  # stall_res: Stall.SFPU; wait_res: Wait.MATH
    3c8: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3cc: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3d0: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3d4: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3d8: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3dc: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3e0: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3e4: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3e8: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    3ec: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    3f0: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3f4: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3f8: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    3fc: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    400: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    404: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    408: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    40c: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    410: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    414: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    418: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    41c: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    420: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    424: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    428: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    42c: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    430: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    434: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    438: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    43c: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    440: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    444: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    448: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    44c: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    450: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    454: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    458: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    45c: 101b00c0  REPLAY       start_idx=27, len=3, execute_while_loading=0, load_mode=0
    460: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    464: dc480010  SETRWC       clear_ab_vld=0, rwc_cr=4, rwc_d=8, rwc_b=0, rwc_a=0, BitMask=4
    468: dc000010  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=4
    46c: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    470: 001a0a13  addi         x20, x20, 1
    474: f21ff06f  jal          x0, 0x00000394  # target 0x00000394
loc_478:
    478: f0001c01  SFPMOV       imm12_math=0, lreg_c=7, lreg_dest=0, instr_mod1=0  # lreg_c: L7; lreg_dest: L0
    47c: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    480: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    484: 3c000002  SFPNOP       
    488: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    48c: 3c000002  SFPNOP       
    490: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    494: 3c000002  SFPNOP       
    498: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    49c: 3c000002  SFPNOP       
    4a0: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    4a4: 3c000002  SFPNOP       
    4a8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    4ac: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    4b0: 3c000002  SFPNOP       
    4b4: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    4b8: 3c000002  SFPNOP       
    4bc: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    4c0: 3c000002  SFPNOP       
    4c4: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    4c8: 5000044e  SFPSHFT2     imm12_math=0, lreg_src_c=1, lreg_dest=1, instr_mod1=3  # lreg_src_c: L1; lreg_dest: L1
    4cc: 3c000002  SFPNOP       
    4d0: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    4d4: 3c000002  SFPNOP       
    4d8: f0000041  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=1, instr_mod1=0  # lreg_c: L0; lreg_dest: L1
    4dc: f0000081  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=2, instr_mod1=0  # lreg_c: L0; lreg_dest: L2
    4e0: f00000c1  SFPMOV       imm12_math=0, lreg_c=0, lreg_dest=3, instr_mod1=0  # lreg_c: L0; lreg_dest: L3
    4e4: 30000002  SFPTRANSP    imm12_math=0, lreg_c=0, lreg_dest=0, instr_mod1=0  # lreg_c: L0; lreg_dest: L0
    4e8: 14280402  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=1, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L1; lreg_dest: L0
    4ec: 3c000002  SFPNOP       
    4f0: 14280802  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=2, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L2; lreg_dest: L0
    4f4: 3c000002  SFPNOP       
    4f8: 14280c02  SFPADD       lreg_src_a=10, lreg_src_b=0, lreg_src_c=3, lreg_dest=0, instr_mod1=0  # lreg_src_a: L10 · constant 1 (0x3f800000); lreg_src_b: L0; lreg_src_c: L3; lreg_dest: L0
    4fc: 3c000002  SFPNOP       
    500: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    504: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
    508: 00042383  lw           x7, 0(x8)  # param output_scale_0_0; 0x00000790
    50c: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    510: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    514: 79400413  addi         x8, x0, 1940  # x8 = 0x00000794
    518: 00042383  lw           x7, 0(x8)  # param output_scale_0_1; 0x00000794
    51c: ffe40437  lui          x8, 0xffe40  # x8 = 0xffe40000 · TensixMMIO.INSTRN_BUF_BASE
    520: 00742023  sw           x7, 0(x8)  # TensixMMIO.INSTRN_BUF_BASE · 0xffe40000; write runtime value
    524: 1801a402  SFPMUL       lreg_src_a=0, lreg_src_b=6, lreg_src_c=9, lreg_dest=0, instr_mod1=0  # lreg_src_a: L0; lreg_src_b: L6; lreg_src_c: L9 · constant 0 (0x00000000); lreg_dest: L0
    528: 3c000002  SFPNOP       
    52c: c80f8001  SFPSTORE     lreg_ind=0, instr_mod0=3, sfpu_addr_mode=7, dest_reg_addr=0  # lreg_ind: L0
    530: 3c000002  SFPNOP       
    534: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    538: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    53c: 00128293  addi         x5, x5, 1
    540: e3dff06f  jal          x0, 0x0000037c  # target 0x0000037c
loc_544:
    544: 9a84002a  SEMWAIT      stall_res=322, sem_sel=2, wait_sem_cond=2  # stall_res: Stall.SYNC | Stall.MATH | Stall.SFPU; sem_sel: Sem.MATH_PACK; wait_sem_cond: SemWait.ON_MAX
    548: c8000002  SETC16       setc16_reg=0, setc16_value=0  # thread_cfg[0] (current thread); CFG_STATE_ID_StateID = 0
    54c: c8040002  SETC16       setc16_reg=1, setc16_value=0  # thread_cfg[1] (current thread); DEST_TARGET_REG_CFG_MATH_Offset = 0
    550: 89002042  STALLWAIT    stall_res=128, wait_res=2064  # stall_res: Stall.CFG; wait_res: Wait.MATH | Wait.SFPU
    554: d8800006  RMWCIB3      Mask=32, Data=0, CfgRegAddr=1  # cfg[1] (current thread StateID); ALU_ACC_CTRL_Fp32_enabled = 0
    558: c8382022  SETC16       setc16_reg=14, setc16_value=2056  # thread_cfg[14] (current thread); ADDR_MOD_AB_SEC2_SrcAIncr = 8; ADDR_MOD_AB_SEC2_SrcACR = 0; ADDR_MOD_AB_SEC2_SrcAClear = 0; ADDR_MOD_AB_SEC2_SrcBIncr = 8; ADDR_MOD_AB_SEC2_SrcBCR = 0; ADDR_MOD_AB_SEC2_SrcBClear = 0
    55c: c8780022  SETC16       setc16_reg=30, setc16_value=8  # thread_cfg[30] (current thread); ADDR_MOD_DST_SEC2_DestIncr = 8; ADDR_MOD_DST_SEC2_DestCR = 0; ADDR_MOD_DST_SEC2_DestClear = 0; ADDR_MOD_DST_SEC2_DestCToCR = 0; ADDR_MOD_DST_SEC2_FidelityIncr = 0; ADDR_MOD_DST_SEC2_FidelityClear = 0
    560: c8c40002  SETC16       setc16_reg=49, setc16_value=0  # thread_cfg[49] (current thread); ADDR_MOD_BIAS_SEC2_BiasIncr = 0; ADDR_MOD_BIAS_SEC2_BiasClear = 0
    564: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    568: 88800602  STALLWAIT    stall_res=64, wait_res=384  # stall_res: Stall.MATH; wait_res: Wait.SRCA_VLD | Wait.SRCB_VLD
    56c: ffe80237  lui          x4, 0xffe80  # x4 = 0xffe80000 · tensix_pc_buf + 0x0
    570: 00820213  addi         x4, x4, 8  # x4 = 0xffe80008 · TensixMMIO.PC_BUF_MOP_SYNC
    574: 00022023  sw           x0, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008; write 0x00000000
    578: 00022283  lw           x5, 0(x4)  # TensixMMIO.PC_BUF_MOP_SYNC · 0xffe80008
    57c: 00507033  and          x0, x0, x5
    580: ffb80237  lui          x4, 0xffb80  # x4 = 0xffb80000 · MOP_CFG
    584: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    588: 00522023  sw           x5, 0(x4)  # MOP_CFG · 0xffb80000; write 0x00000004
    58c: 00200293  addi         x5, x0, 2  # x5 = 0x00000002
    590: 00522223  sw           x5, 4(x4)  # MopCfg[1] · InnerCount / Flags · 0xffb80004; write 0x00000002
    594: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    598: 00522423  sw           x5, 8(x4)  # MopCfg[2] · StartOp / InsnB · 0xffb80008; write 0x02000000; MOP template instruction · NOP 
    59c: 37c002b7  lui          x5, 0x37c00  # x5 = 0x37c00000
    5a0: 00328293  addi         x5, x5, 3  # x5 = 0x37c00003
    5a4: 00522623  sw           x5, 12(x4)  # MopCfg[3] · EndOp0 / InsnA0 · 0xffb8000c; write 0x37c00003; MOP template instruction · SETRWC clear_ab_vld=3, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=3
    5a8: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    5ac: 00522823  sw           x5, 16(x4)  # MopCfg[4] · EndOp1 / InsnA1 · 0xffb80010; write 0x02000000; MOP template instruction · NOP 
    5b0: 280082b7  lui          x5, 0x28008  # x5 = 0x28008000
    5b4: 00522a23  sw           x5, 20(x4)  # MopCfg[5] · LoopOp / InsnA2 · 0xffb80014; write 0x28008000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    5b8: 020002b7  lui          x5, 0x02000  # x5 = 0x02000000
    5bc: 00522c23  sw           x5, 24(x4)  # MopCfg[6] · LoopOp1 / InsnA3 · 0xffb80018; write 0x02000000; MOP template instruction · NOP 
    5c0: 280082b7  lui          x5, 0x28008  # x5 = 0x28008000
    5c4: 00522e23  sw           x5, 28(x4)  # MopCfg[7] · Loop0Last / SkipA0 · 0xffb8001c; write 0x28008000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    5c8: 02522023  sw           x5, 32(x4)  # MopCfg[8] · Loop1Last / SkipB · 0xffb80020; write 0x28008000; MOP template instruction · ELWADD clear_dvalid=0, dest_accum_en=0, instr_mod19=0, addr_mode=2, dst=0
    5cc: 06000000  MOP          mop_type=1, loop_count=0, zmask_lo16_or_loop_count=0
    5d0: dc00003c  SETRWC       clear_ab_vld=0, rwc_cr=0, rwc_d=0, rwc_b=0, rwc_a=0, BitMask=15
    5d4: 88042042  STALLWAIT    stall_res=2, wait_res=2064  # stall_res: Stall.SYNC; wait_res: Wait.MATH | Wait.SFPU
    5d8: 90000022  SEMPOST      sem_sel=2  # sem_sel: Sem.MATH_PACK
    5dc:           j FW_TRISC1+4   # return to firmware, linked at install
