    addi	sp,sp,-80
    sw	ra,76(sp)
    sw	s0,72(sp)
    sw	s1,68(sp)
    sw	s2,64(sp)
    sw	s3,60(sp)
    sw	s4,56(sp)
    sw	s5,52(sp)
    sw	s6,48(sp)
    sw	s7,44(sp)
    sw	s8,40(sp)
    sw	s9,36(sp)
    sw	s10,32(sp)
    sw	s11,28(sp)
    lui	a5,0xffb00
    lui	a4,0xffb00
    addi	a5,a5,248 # ffb000f8 <__stack_base+0x8>
    addi	a4,a4,236 # ffb000ec <__ldm_bss_end>
    bltu	a4,a5,7294 <.L12>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,727c <.L13>
    addi	a3,a5,-8
    bgeu	a4,a3,72a0 <.LM160>
    j	8c38 <.L88>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,72b4 <.L15>
    sw	zero,-8(a5)
    auipc	a4,0x2
    addi	a4,a4,-1344 # 8d74 <__kernel_data_lma>
    addi	a5,gp,-2000 # ffb00020 <_ZL21unpack_tile_num_faces>
    beq	a4,a5,7324 <.L17>
    lui	a2,0xffb00
    addi	a2,a2,232 # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,7308 <.L18>
    li	a6,2
    lw	a0,0(a4)
    lw	a1,4(a4)
    lw	a2,8(a4)
    addi	a4,a4,12
    addi	a5,a5,12
    addi	a3,a3,-3
    sw	a0,-12(a5)
    sw	a1,-8(a5)
    sw	a2,-4(a5)
    blt	a6,a3,72e0 <.L19>
    blez	a3,7324 <.L17>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,7324 <.L17>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LASF223+0x2>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7348 <.L23>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,733c <.L21>
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttzeroacc	3,0,0,1,0
    li	a0,0
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,7378 <.L22>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	s0,0xffe40
    lui	a5,0xb3080
    mv	s0,s0
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(s0) # ffe40000 <__instrn_buffer>
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(s0)
    lui	a5,0xb6202
    addi	a5,a5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    sw	a5,0(s0)
    lui	a5,0xb6404
    addi	a5,a5,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a5,0(s0)
    lbu	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    bne	a4,a5,73dc <.L24>
    j	8c18 <.L139>
    li	a5,5
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(s0)
    li	a5,2
    sb	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a5,0(s0)
    ttsemwait	322,2,2
    li	a0,0
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetc16	18,0
    ttsetc16	34,2
    ttsetc16	53,0
    ttsetrwc	0,0,0,0,0,15
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s5,4
    ttreplay	0,5,1,1
    sfpload	L0,0,0,7
    sfpload	L1,0,0,7
    sfpmul	L0,L0,L1,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s5,s5,-1
    bnez	s5,747c <.L26>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	a0,11
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lui	a4,0xffe80
    addi	a5,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	s5,0(a5)
    lw	s5,0(a5)
    and	zero,zero,s5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,74e8 <.L27>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xb3080
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(s0)
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(s0)
    lui	a5,0xb6202
    addi	a5,a5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    sw	a5,0(s0)
    lui	a5,0xb6404
    addi	a5,a5,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a5,0(s0)
    lbu	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    bne	a4,a5,7544 <.L28>
    j	8bf8 <.L140>
    li	a5,4
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(s0)
    li	a5,2
    sb	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a5,0(s0)
    ttsemwait	322,2,2
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lui	a5,0xb2010
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s5,4
    ttreplay	0,4,1,1
    sfpstore	L10,0,0,7
    ttincrwc	0,2,0,0
    sfpstore	L10,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s5,s5,-1
    bnez	s5,75a0 <.L30>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	a0,10
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lui	a4,0xffe80
    addi	a5,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	s5,0(a5) # b2010000 <__device_print_strings_info_end+0xabb10000>
    lw	s5,0(a5)
    and	zero,zero,s5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,75f8 <.L31>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xb3080
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(s0)
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(s0)
    lui	a5,0xb6202
    addi	a5,a5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    sw	a5,0(s0)
    lui	a5,0xb6404
    addi	a5,a5,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a5,0(s0)
    lbu	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    bne	a4,a5,7654 <.L32>
    j	8bd8 <.L141>
    li	a5,4
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(s0)
    li	a5,2
    sb	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a3,0xb3010
    addi	a3,a3,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a3,0(s0)
    ttsemwait	322,2,2
    ttsetc16	12,0
    ttsetc16	28,32768
    ttsetc16	47,0
    ttsetc16	13,256
    ttsetc16	29,1
    ttsetc16	48,0
    ttsetc16	14,2048
    ttsetc16	30,8
    ttsetc16	49,0
    ttsetc16	15,0
    ttsetc16	31,8192
    ttsetc16	50,0
    lui	a4,0xffe80
    li	a5,0
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,1
    sw	a4,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a4,4
    sw	a4,4(a5)
    lui	a4,0x2000
    sw	a4,8(a5)
    sw	a4,12(a5)
    sw	a4,16(a5)
    lui	a2,0x34098
    sw	a2,20(a5)
    sw	a4,24(a5)
    lui	a4,0x34080
    sw	a4,28(a5)
    sw	a4,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    lbu	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,3
    beq	a4,a5,7750 <.L85>
    ttstallwait	128,2064
    sw	a3,0(s0)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    addi	a5,a5,-9
    addi	a4,a4,-9 # b200fff7 <__device_print_strings_info_end+0xabb0fff7>
    seqz	a4,a4
    seqz	a5,a5
    or	a5,a5,a4
    lui	a4,0xb3010
    addi	a3,a4,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    slli	a5,a5,0x8
    add	a5,a5,a3
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
    addi	a4,a4,258
    sw	a4,0(s0)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    li	a4,1
    sb	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    ttstallwait	2,2064
    ttsempost	2
    li	a0,5
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,7830 <.L34>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xb3080
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(s0)
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(s0)
    lui	a5,0xb6202
    addi	a5,a5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    sw	a5,0(s0)
    lui	a5,0xb6404
    addi	a5,a5,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a5,0(s0)
    lbu	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    bne	a4,a5,788c <.L35>
    j	8bb8 <.L142>
    li	a5,4
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(s0)
    li	s7,2
    sb	s7,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	s10,0xb3010
    addi	s11,s10,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	s11,0(s0)
    ttsemwait	322,2,2
    li	a0,5
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    lui	s6,0xffe80
    addi	s9,s6,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a6,63
    li	s8,1
    lui	s5,0xffb80
    li	a0,0
    sw	a6,8(sp)
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    addi	a0,s6,4
    li	a5,0
    sw	a5,0(a0)
    lw	a5,0(a0)
    and	zero,zero,a5
    lui	a5,0x37c00
    addi	a7,a5,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    lui	a5,0xb6404
    addi	a4,a5,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    lui	a5,0xb6202
    addi	a3,a5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    lui	a5,0xb6800
    addi	a2,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    lw	a6,8(sp)
    lui	a5,0xb3080
    addi	a1,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    lw	a5,36(s6)
    zext.b	a5,a5
    bnez	a5,7954 <.L37>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    sw	a1,0(s0)
    ttstallwait	128,16
    sw	a2,0(s0)
    sw	a3,0(s0)
    lbu	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sw	a4,0(s0)
    bne	a5,s8,798c <.L38>
    j	8b54 <.L143>
    li	a5,5
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    addi	a5,s10,2
    sw	a5,0(s0)
    sb	s7,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    sw	s11,0(s0)
    ttsemwait	322,2,2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    li	a5,0
    sw	a5,0(s9)
    lw	a5,0(s9)
    and	zero,zero,a5
    li	a5,4
    sw	a5,0(s5) # ffb80000 <__global_pointer$+0x7f810>
    sw	s7,4(s5)
    lui	t1,0x2000
    sw	t1,8(s5)
    sw	a7,12(s5)
    sw	t1,16(s5)
    lui	a0,0x28008
    sw	a0,20(s5)
    sw	t1,24(s5)
    sw	a0,28(s5)
    sw	a0,32(s5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a0,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	t1,0xb2010
    snez	a0,a0
    slli	a0,a0,0x9
    add	a0,a0,t1
    sw	a0,0(s0)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetc16	18,0
    ttsetc16	34,2
    ttsetc16	53,0
    ttsetrwc	0,0,0,0,0,15
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    sw	a0,0(s0)
    ttstallwait	256,16
    ttreplay	0,5,1,1
    sfpload	L0,0,0,7
    sfpload	L1,0,0,7
    sfpmul	L0,L0,L1,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,7a7c <.L40>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    mv	a0,a5
    sw	a0,0(s9)
    lw	a0,0(s9)
    and	zero,zero,a0
    li	a0,4
    sw	a0,0(s5)
    sw	s7,4(s5)
    lui	t1,0x2000
    sw	t1,8(s5)
    sw	a7,12(s5)
    sw	t1,16(s5)
    lui	a0,0x28008
    sw	a0,20(s5)
    sw	t1,24(s5)
    sw	a0,28(s5)
    sw	a0,32(s5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    addi	a0,s6,4
    sw	a5,0(a0) # 28008000 <__device_print_strings_info_end+0x21b08000>
    lw	a5,0(a0)
    and	zero,zero,a5
    lw	a5,36(s6)
    zext.b	a5,a5
    bnez	a5,7b48 <.L41>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    sw	a1,0(s0)
    ttstallwait	128,16
    sw	a2,0(s0)
    sw	a3,0(s0)
    lbu	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sw	a4,0(s0)
    beq	a5,s8,8b3c <.L144>
    li	a5,4
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    addi	a5,s10,2
    sw	a5,0(s0)
    sb	s7,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    sw	s11,0(s0)
    ttsemwait	322,2,2
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lui	a5,0xb2010
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,4,1,1
    sfpstore	L10,0,0,7
    ttincrwc	0,2,0,0
    sfpstore	L10,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    bnez	a5,7bc8 <.L44>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    mv	a0,a5
    sw	a0,0(s9)
    lw	a0,0(s9)
    and	zero,zero,a0
    li	a0,4
    sw	a0,0(s5)
    sw	s7,4(s5)
    lui	t1,0x2000
    sw	t1,8(s5)
    sw	a7,12(s5)
    sw	t1,16(s5)
    lui	a0,0x28008
    sw	a0,20(s5)
    sw	t1,24(s5)
    sw	a0,28(s5)
    sw	a0,32(s5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    addi	a0,s6,4
    sw	a5,0(a0) # 28008000 <__device_print_strings_info_end+0x21b08000>
    lw	a5,0(a0)
    and	zero,zero,a5
    lw	a5,36(s6)
    zext.b	a5,a5
    bnez	a5,7c80 <.L45>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    sw	a1,0(s0)
    ttstallwait	128,16
    sw	a2,0(s0)
    sw	a3,0(s0)
    lbu	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sw	a4,0(s0)
    beq	a5,s8,8b24 <.L145>
    li	a5,4
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    addi	a5,s10,2
    sw	a5,0(s0)
    sb	s7,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    sw	s11,0(s0)
    ttsemwait	322,2,2
    ttsetc16	12,0
    ttsetc16	28,32768
    ttsetc16	47,0
    ttsetc16	13,256
    ttsetc16	29,1
    ttsetc16	48,0
    ttsetc16	14,2048
    ttsetc16	30,8
    ttsetc16	49,0
    ttsetc16	15,0
    ttsetc16	31,8192
    ttsetc16	50,0
    li	a5,0
    sw	a5,0(s9)
    lw	a5,0(s9)
    and	zero,zero,a5
    li	a5,4
    sw	s8,0(s5)
    sw	a5,4(s5)
    lui	a5,0x2000
    sw	a5,8(s5)
    sw	a5,12(s5)
    sw	a5,16(s5)
    lui	a0,0x34098
    sw	a0,20(s5)
    sw	a5,24(s5)
    lui	a5,0x34080
    sw	a5,28(s5)
    sw	a5,32(s5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a0,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a0
    sw	a5,0(s0)
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    lbu	a0,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,3
    beq	a0,a5,7d90 <.L83>
    ttstallwait	128,2064
    sw	s11,0(s0)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    lw	a0,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    addi	a5,a5,-9 # 3407fff7 <__device_print_strings_info_end+0x2db7fff7>
    addi	a0,a0,-9 # b200fff7 <__device_print_strings_info_end+0xabb0fff7>
    seqz	a0,a0
    seqz	a5,a5
    or	a5,a5,a0
    slli	a5,a5,0x8
    addi	a0,s10,2
    add	a5,a5,a0
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
    sw	s11,0(s0)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    sb	s8,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    ttstallwait	2,2064
    ttsempost	2
    li	a5,0
    addi	a0,s6,4
    sw	a5,0(a0)
    lw	a5,0(a0)
    and	zero,zero,a5
    lw	a5,36(s6)
    zext.b	a5,a5
    bnez	a5,7e58 <.L48>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    sw	a1,0(s0)
    ttstallwait	128,16
    sw	a2,0(s0)
    sw	a3,0(s0)
    lbu	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sw	a4,0(s0)
    beq	a5,s8,8b0c <.L146>
    li	a5,4
    sb	s8,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    addi	a5,s10,2
    sw	a5,0(s0)
    ttsemwait	322,2,2
    ttsetc16	12,2056
    ttsetc16	28,8
    ttsetc16	47,0
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttsetc16	14,32896
    ttsetc16	30,1024
    ttsetc16	49,0
    ttsetc16	15,32896
    ttsetc16	31,36872
    ttsetc16	50,0
    li	a5,0
    sw	a5,0(s9)
    lw	a5,0(s9)
    and	zero,zero,a5
    li	a5,4
    sw	a5,0(s5)
    sw	s7,4(s5)
    lui	a0,0x2000
    lui	a5,0x37cc0
    sw	a0,8(s5)
    addi	a5,a5,3 # 37cc0003 <__device_print_strings_info_end+0x317c0003>
    sw	a5,12(s5)
    sw	a0,16(s5)
    lui	a5,0x28000
    sw	a5,20(s5)
    sw	a0,24(s5)
    sw	a5,28(s5)
    sw	a5,32(s5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a0,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a0
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    addi	a6,a6,-1
    bnez	a6,7908 <.L51>
    li	a0,6
    sw	a6,8(sp)
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    addi	s6,s6,4
    lw	a6,8(sp)
    sw	a6,0(s6)
    lw	a6,0(s6)
    and	zero,zero,a6
    lui	a4,0xffe80
    lw	a5,36(a4) # ffe80024 <__instrn_buffer+0x40024>
    zext.b	a5,a5
    bnez	a5,7f80 <.L52>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xb3080
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(s0)
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(s0)
    lui	a5,0xb6202
    addi	a5,a5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    sw	a5,0(s0)
    lui	a5,0xb6404
    addi	a5,a5,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a5,0(s0)
    lbu	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    beq	a4,a5,8ba0 <.L147>
    li	a5,4
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(s0)
    li	a2,2
    sb	a2,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a5,0(s0)
    ttsemwait	322,2,2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,256
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,2048
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a4,0xffe80
    addi	a1,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a1)
    lw	a5,0(a1)
    and	zero,zero,a5
    lui	a5,0xffb80
    sw	a2,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    sw	a2,4(a5)
    lui	a1,0x2000
    lui	a2,0x37080
    sw	a1,8(a5)
    addi	a2,a2,2 # 37080002 <__device_print_strings_info_end+0x30b80002>
    sw	a2,12(a5)
    sw	a1,16(a5)
    lui	a2,0x28088
    sw	a2,20(a5)
    sw	a1,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    li	a5,0
    addi	a3,a4,4
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,80a0 <.L55>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xb3080
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(s0)
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(s0)
    lui	a5,0xb6202
    addi	a5,a5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    sw	a5,0(s0)
    lui	a5,0xb6404
    addi	a5,a5,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a5,0(s0)
    lbu	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    beq	a4,a5,8b88 <.L148>
    li	a5,4
    li	a4,1
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    sb	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(s0)
    lui	a5,0xb2010
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    li	a0,2
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a4,0xffe80
    lw	a5,60(a4) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a5,a5
    beqz	a5,8150 <.L58>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,64 # b2010040 <__device_print_strings_info_end+0xabb10040>
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,4 # 100ec004 <__device_print_strings_info_end+0x9bec004>
    addi	a4,a4,8
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,8194 <.L59>
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,0,0,7
    sfpload	L1,64,0,7
    sfpmul	L0,L0,L1,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,81d4 <.L60>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,64 # b2010040 <__device_print_strings_info_end+0xabb10040>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    sfploadi	L0,-14932,2
    sfploadi	L0,14119,8
    ttreplay	0,4,1,1
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttreplay	0,4,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,8254 <.L61>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s5,4
    ttreplay	0,5,1,1
    sfpload	L0,0,0,7
    sfpload	L1,64,0,7
    sfpadd	L0,L0,L1,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s5,s5,-1
    bnez	s5,82c4 <.L62>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	a0,7
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lui	a4,0xffe80
    addi	a5,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	s5,0(a5)
    lw	s5,0(a5)
    and	zero,zero,s5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,8330 <.L63>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xb3080
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(s0)
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(s0)
    lui	a5,0xb6202
    addi	a5,a5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    sw	a5,0(s0)
    lui	a5,0xb6404
    addi	a5,a5,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a5,0(s0)
    lbu	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    beq	a4,a5,8b74 <.L149>
    sw	zero,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	zero,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(s0)
    li	a5,2
    sb	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a5,0(s0)
    ttsemwait	322,2,2
    li	a0,7
    jal	8c40 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a4,0xffe80
    lw	a5,60(a4) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a5,a5
    beqz	a5,83d4 <.L66>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a5,0x100ec
    sw	a5,12(sp)
    addi	a5,a5,4 # 100ec004 <__device_print_strings_info_end+0x9bec004>
    lw	a4,12(sp)
    sw	a4,0(s0)
    addi	a4,a4,1
    sw	a4,12(sp)
    bne	a4,a5,8414 <.L67>
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    sfploadi	L0,4256,2
    sfploadi	L0,24337,8
    sfpconfig	12,0,0
    sfploadi	L0,5321,2
    sfploadi	L0,16402,8
    sfpconfig	13,0,0
    sfploadi	L0,13862,2
    sfploadi	L0,16400,8
    sfpconfig	14,0,0
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,25,1,1
    sfpload	L1,0,0,7
    sfpshft	L0,L1,0xFFF,5
    sfpiadd	L0,L12,0x000,6
    sfpmul	L2,L1,L0,0
    sfpmul	L2,L0,L2,1
    sfploadi	L3,32640,0
    sfpadd	L4,L14,L2,0
    sfpmad	L2,L2,L4,L13,0
    sfpmul	L0,L0,L2,0
    sfpmul	L2,L1,L0,0
    sfpmad	L2,L0,L2,L10,1
    sfpdivp2	L5,L0,0xFFF,1
    sfpmov	L4,L1,2
    sfpiadd	L4,L3,0x000,6
    sfpsetcc	L4,0x000,2
    sfpsetcc	L1,0x000,2
    sfpmad	L0,L2,L5,L0,0
    sfpcompc
    sfpmov	L0,L4,0
    sfpencc	0x003,10
    sfpsetcc	L1,0x000,0
    sfploadi	L0,32704,0
    sfpencc	0x003,10
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,25,0,0
    ttreplay	0,25,0,0
    ttreplay	0,25,0,0
    ttreplay	0,25,0,0
    ttreplay	0,25,0,0
    ttreplay	0,25,0,0
    ttreplay	0,25,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,8480 <.L68>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    lui	a3,0xb3010
    lui	a4,0xffe80
    lui	a5,0xffb80
    lui	t5,0x37c00
    lui	s7,0xb3080
    lui	s6,0xb6800
    lui	s5,0xb6202
    lui	t2,0xb6404
    lui	a7,0x100ec
    addi	s11,a3,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    addi	a3,a3,258
    addi	t4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    addi	s10,a4,4
    addi	t3,a5,12 # ffb8000c <__global_pointer$+0x7f81c>
    addi	t5,t5,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    addi	s7,s7,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    addi	s6,s6,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    addi	s5,s5,1 # b6202001 <__device_print_strings_info_end+0xafd02001>
    addi	t2,t2,1 # b6404001 <__device_print_strings_info_end+0xaff04001>
    sw	a3,8(sp)
    addi	a7,a7,8 # 100ec008 <__device_print_strings_info_end+0x9bec008>
    li	s9,64
    li	a6,4
    li	t1,2
    lui	a2,0x2000
    lui	a1,0x28008
    li	t6,1
    li	t0,5
    lui	s8,0xb2010
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    li	a3,0
    mv	a0,a3
    sw	a0,0(t4)
    lw	a0,0(t4)
    and	zero,zero,a0
    sw	a6,0(a5)
    sw	t1,4(a5)
    sw	a2,8(a5)
    sw	t5,0(t3)
    sw	a2,16(a5)
    sw	a1,20(a5)
    sw	a2,24(a5)
    sw	a1,28(a5)
    sw	a1,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    sw	a3,0(s10)
    lw	a3,0(s10)
    and	zero,zero,a3
    lw	a3,36(a4)
    zext.b	a3,a3
    bnez	a3,8604 <.L69>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    sw	s7,0(s0)
    ttstallwait	128,16
    sw	s6,0(s0)
    sw	s5,0(s0)
    lbu	a3,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sw	t2,0(s0)
    beq	a3,t6,8af8 <.L150>
    sw	t0,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	t0,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    sw	s11,0(s0)
    sb	t1,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lw	a3,8(sp)
    sw	a3,0(s0)
    ttsemwait	322,2,2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    li	a0,0
    mv	a3,a0
    sw	a3,0(t4)
    lw	a3,0(t4)
    and	zero,zero,a3
    sw	a6,0(a5)
    sw	t1,4(a5)
    sw	a2,8(a5)
    sw	t5,0(t3)
    sw	a2,16(a5)
    sw	a1,20(a5)
    sw	a2,24(a5)
    sw	a1,28(a5)
    sw	a1,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a3,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    snez	a3,a3
    slli	a3,a3,0x9
    add	a3,a3,s8
    sw	a3,0(s0)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetc16	18,0
    ttsetc16	34,2
    ttsetc16	53,0
    ttsetrwc	0,0,0,0,0,15
    ttstallwait	2,2064
    ttsempost	2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    mv	a3,a0
    sw	a3,0(t4)
    lw	a3,0(t4)
    and	zero,zero,a3
    sw	a6,0(a5)
    sw	t1,4(a5)
    sw	a2,8(a5)
    sw	t5,0(t3)
    sw	a2,16(a5)
    sw	a1,20(a5)
    sw	a2,24(a5)
    sw	a1,28(a5)
    sw	a1,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    sw	a0,0(s10)
    lw	a0,0(s10)
    and	zero,zero,a0
    lw	a3,36(a4)
    zext.b	a3,a3
    bnez	a3,8770 <.L72>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    sw	s7,0(s0)
    ttstallwait	128,16
    sw	s6,0(s0)
    sw	s5,0(s0)
    lbu	a3,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sw	t2,0(s0)
    beq	a3,t6,8ae4 <.L151>
    sw	t0,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	t0,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    sw	s11,0(s0)
    sb	t1,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lw	a3,8(sp)
    sw	a3,0(s0)
    ttsemwait	322,2,2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    li	a0,0
    mv	a3,a0
    sw	a3,0(t4)
    lw	a3,0(t4)
    and	zero,zero,a3
    sw	a6,0(a5)
    sw	t1,4(a5)
    sw	a2,8(a5)
    sw	t5,0(t3)
    sw	a2,16(a5)
    sw	a1,20(a5)
    sw	a2,24(a5)
    sw	a1,28(a5)
    sw	a1,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a3,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    snez	a3,a3
    slli	a3,a3,0x9
    add	a3,a3,s8
    sw	a3,0(s0)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetc16	18,0
    ttsetc16	34,2
    ttsetc16	53,0
    ttsetrwc	0,0,0,0,0,15
    ttstallwait	2,2064
    ttsempost	2
    sw	a0,0(s10)
    lw	a0,0(s10)
    and	zero,zero,a0
    lw	a3,36(a4)
    zext.b	a3,a3
    bnez	a3,887c <.L75>
    ttseminit	1,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    sw	s7,0(s0)
    ttstallwait	128,16
    sw	s6,0(s0)
    sw	s5,0(s0)
    lbu	a3,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sw	t2,0(s0)
    beq	a3,t6,8ad0 <.L152>
    sw	a6,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a6,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    sb	t6,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    sw	s11,0(s0)
    ttsemwait	322,2,2
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    li	a3,0
    sw	a3,0(t4)
    lw	a3,0(t4)
    and	zero,zero,a3
    sw	a6,0(a5)
    sw	t1,4(a5)
    sw	a2,8(a5)
    sw	t5,0(t3)
    sw	a2,16(a5)
    sw	a1,20(a5)
    sw	a2,24(a5)
    sw	a1,28(a5)
    sw	a1,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lw	a3,60(a4)
    zext.b	a3,a3
    beqz	a3,8934 <.L78>
    sw	t6,60(a4)
    lw	a3,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a0,0xffec1
    snez	a3,a3
    slli	a3,a3,0x9
    addi	a3,a3,64
    sw	a3,0(a0) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lw	a3,12(sp)
    sw	a3,0(s0)
    addi	a3,a3,1
    bne	a3,a7,896c <.L79>
    ttsetc16	12,2056
    ttsetc16	28,8
    ttsetc16	47,0
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttsetc16	14,32896
    ttsetc16	30,9216
    ttsetc16	49,0
    ttsetc16	15,32896
    ttsetc16	31,36872
    ttsetc16	50,0
    li	a3,0
    sw	a3,0(t4)
    lw	a3,0(t4)
    and	zero,zero,a3
    sw	a6,0(a5)
    sw	t1,4(a5)
    sw	a2,8(a5)
    sw	a2,0(t3)
    sw	a2,16(a5)
    lui	a3,0x27000
    sw	a3,20(a5)
    sw	a2,24(a5)
    lui	a3,0x27c0c
    sw	a3,28(a5)
    lui	a3,0x27008
    sw	a3,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a0,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    li	a3,4
    snez	a0,a0
    slli	a0,a0,0x9
    add	a0,a0,s8
    sw	a0,0(s0)
    ttmop	1,0,0
    addi	a3,a3,-1 # 27007fff <__device_print_strings_info_end+0x20b07fff>
    bnez	a3,8a08 <.L80>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    sw	a0,0(s0)
    ttstallwait	256,16
    li	a3,4
    ttreplay	0,5,1,1
    sfpload	L0,0,0,7
    sfpload	L1,64,0,7
    sfpmul	L0,L0,L1,0
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttreplay	0,5,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a3,a3,-1
    bnez	a3,8a38 <.L81>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    addi	s9,s9,-1
    bnez	s9,8594 <.L82>
    lw	ra,76(sp)
    lw	s0,72(sp)
    lw	s1,68(sp)
    lw	s2,64(sp)
    lw	s3,60(sp)
    lw	s4,56(sp)
    lw	s5,52(sp)
    lw	s6,48(sp)
    lw	s7,44(sp)
    lw	s8,40(sp)
    lw	s9,36(sp)
    lw	s10,32(sp)
    lw	s11,28(sp)
    li	a0,0
    addi	sp,sp,80
    ret
    lw	a3,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    bne	a3,a6,88b0 <.L76>
    lw	a3,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a3,a6,88b0 <.L76>
    j	88c4 <.L77>
    lw	a3,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    bne	a3,t0,87a4 <.L73>
    lw	a3,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a3,t0,87a4 <.L73>
    j	87b4 <.L74>
    lw	a3,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    bne	a3,t0,8638 <.L70>
    lw	a3,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a3,t0,8638 <.L70>
    j	8648 <.L71>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a0,4
    bne	a5,a0,7e8c <.L49>
    lw	a0,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a0,a5,7e8c <.L49>
    j	7ea8 <.L50>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a0,4
    bne	a5,a0,7cb4 <.L46>
    lw	a0,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a0,a5,7cb4 <.L46>
    j	7ccc <.L47>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a0,4
    bne	a5,a0,7b7c <.L42>
    lw	a0,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a0,a5,7b7c <.L42>
    j	7b94 <.L43>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a0,5
    beq	a5,a0,8b64 <.LM6459>
    j	798c <.L38>
    lw	a0,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a0,a5,8b70 <.LM6459+0xc>
    j	798c <.L38>
    j	79a4 <.L39>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    or	a5,a5,a4
    bnez	a5,8388 <.L64>
    j	83a0 <.L65>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    bne	a5,a4,80f8 <.L56>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a4,a5,80f8 <.L56>
    j	811c <.L57>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    bne	a5,a4,7fd8 <.L53>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a4,a5,7fd8 <.L53>
    j	7ff4 <.L54>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,8bc8 <.LM6469>
    j	788c <.L35>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,8bd4 <.LM6469+0xc>
    j	788c <.L35>
    j	78a8 <.L36>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,8be8 <.LM6472>
    j	7654 <.L32>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,8bf4 <.LM6472+0xc>
    j	7654 <.L32>
    j	7670 <.L33>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,8c08 <.LM6475>
    j	7544 <.L28>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,8c14 <.LM6475+0xc>
    j	7544 <.L28>
    j	7560 <.L29>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,5
    beq	a5,a4,8c28 <.LM6478>
    j	73dc <.L24>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,8c34 <.LM6478+0xc>
    j	73dc <.L24>
    j	73f8 <.L25>
    mv	a5,a3
    j	72a8 <.L14>
    addi	a5,gp,-2000 # ffb00020 <_ZL21unpack_tile_num_faces>
    add	a0,a5,a0
    lbu	a4,128(a0)
    li	a1,30
    lbu	a3,0(a0)
    lbu	a2,64(a0)
    li	a5,0
    bltu	a1,a4,8c70 <.L2>
    lui	a5,0x44004
    addi	a5,a5,1024 # 44004400 <__device_print_strings_info_end+0x3db04400>
    srl	a5,a5,a4
    andi	a5,a5,1
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    beqz	a5,8cac <.L3>
    li	a5,9
    lui	a4,0xffe80
    beq	a2,a5,8d10 <.L4>
    li	a5,0
    j	8cb8 <.L8>
    li	a4,9
    beq	a2,a4,8d6c <.L6>
    lui	a4,0xffe80
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a5,0xffb80
    sw	a3,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a4,2
    sw	a4,4(a5)
    lui	a3,0x2000
    lui	a4,0x37c00
    sw	a3,8(a5)
    addi	a4,a4,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a4,12(a5)
    sw	a3,16(a5)
    lui	a4,0x28008
    sw	a4,20(a5)
    sw	a3,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    ret
    li	a5,0
    addi	a4,a4,8 # 28008008 <__device_print_strings_info_end+0x21b08008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a5,0xffb80
    sw	a3,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a4,2
    sw	a4,4(a5)
    lui	a3,0x2000
    lui	a4,0x37c00
    sw	a3,8(a5)
    addi	a4,a4,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a4,12(a5)
    sw	a3,16(a5)
    lui	a4,0x1280a
    sw	a4,20(a5)
    sw	a3,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    ret
    lui	a4,0xffe80
    j	8d14 <.L9>
