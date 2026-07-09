    addi	sp,sp,-32
    sw	ra,28(sp)
    sw	s0,24(sp)
    sw	s1,20(sp)
    sw	s2,16(sp)
    sw	s3,12(sp)
    sw	s4,8(sp)
    sw	s5,4(sp)
    lui	a5,0xffb00
    lui	a4,0xffb00
    addi	a5,a5,248 # ffb000f8 <__stack_base+0x8>
    addi	a4,a4,236 # ffb000ec <__ldm_bss_end>
    bltu	a4,a5,727c <.L15>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,7264 <.L16>
    addi	a3,a5,-8
    bgeu	a4,a3,7288 <.LM193>
    j	94ac <.L98>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,729c <.L18>
    sw	zero,-8(a5)
    auipc	a4,0x2
    addi	a4,a4,1028 # 96a0 <__kernel_data_lma>
    addi	a5,gp,-2000 # ffb00020 <_ZL21unpack_tile_num_faces>
    beq	a4,a5,730c <.L20>
    lui	a2,0xffb00
    addi	a2,a2,232 # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,72f0 <.L21>
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
    blt	a6,a3,72c8 <.L22>
    blez	a3,730c <.L20>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,730c <.L20>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LVUS78>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7330 <.L26>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7324 <.L24>
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttzeroacc	3,0,0,1,0
    li	a0,3
    jal	94b4 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,7360 <.L25>
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
    bne	a4,a5,73c4 <.L27>
    j	948c <.L169>
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
    bnez	s5,7420 <.L29>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    li	a0,0
    jal	94b4 <_Z36llk_math_eltwise_unary_datacopy_initILN7ckernel12DataCopyTypeE0ELb1ELNS0_13BroadcastTypeE0ELb0ELNS0_8PackModeE0EEvm>
    lui	a4,0xffe80
    addi	a5,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	s5,0(a5) # b2010000 <__device_print_strings_info_end+0xabb10000>
    lw	s5,0(a5)
    and	zero,zero,s5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,7478 <.L30>
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
    bne	a4,a5,74d4 <.L31>
    j	946c <.L170>
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
    lui	a2,0xb3010
    addi	a2,a2,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a2,0(s0)
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
    lui	a3,0x34098
    sw	a3,20(a5)
    sw	a4,24(a5)
    lui	a4,0x34080
    sw	a4,28(a5)
    sw	a4,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a3,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    snez	a3,a3
    lui	a1,0xb2010
    slli	a3,a3,0x9
    add	a3,a3,a1
    addi	a5,a5,-9
    addi	a4,a4,-9 # 3407fff7 <__device_print_strings_info_end+0x2db7fff7>
    seqz	a4,a4
    sw	a3,0(s0)
    seqz	a5,a5
    lbu	a1,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    or	a5,a5,a4
    ttgmpool	3,1,0,0,0
    ttgmpool	0,1,0,0,0
    li	a4,3
    beq	a1,a4,75e8 <.L96>
    ttstallwait	128,2064
    sw	a2,0(s0)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a2,a4,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    slli	a5,a5,0x8
    add	a5,a5,a2
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttgmpool	3,1,0,0,0
    ttgmpool	0,1,0,0,0
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    sw	a3,0(s0)
    ttgmpool	3,1,0,0,0
    ttgmpool	0,1,0,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttgmpool	3,1,0,0,0
    ttgmpool	0,1,0,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    sw	a3,0(s0)
    ttgmpool	3,1,0,0,0
    ttgmpool	0,1,0,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttgmpool	3,1,0,0,0
    ttgmpool	0,1,0,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    sw	a3,0(s0)
    ttgmpool	3,1,0,0,0
    ttgmpool	0,1,0,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttgmpool	3,1,0,0,0
    ttgmpool	0,1,0,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    li	a5,1
    sb	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
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
    lui	a4,0xffe80
    addi	a2,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a2)
    lw	a5,0(a2)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a2,4
    sw	a2,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a2,2
    sw	a2,4(a5)
    lui	a1,0x2000
    lui	a2,0x37c00
    sw	a1,8(a5)
    addi	a2,a2,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a2,12(a5)
    sw	a1,16(a5)
    lui	a2,0x28008
    sw	a2,20(a5)
    sw	a1,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    li	a5,0
    addi	a3,a4,4
    sw	a5,0(a3) # 34098000 <__device_print_strings_info_end+0x2db98000>
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,78d0 <.L33>
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
    bne	a4,a5,792c <.L34>
    j	944c <.L171>
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
    sw	a5,0(a1) # 2000000 <trisck.cc.ca4958b4+0x1fef477>
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
    bnez	a5,79f4 <.L36>
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
    bne	a4,a5,7a50 <.L37>
    j	942c <.L172>
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
    addi	a4,a5,128 # b2010080 <__device_print_strings_info_end+0xabb10080>
    sw	a4,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a4,a5,256
    sw	a4,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a5,a5,384
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a3,2
    sw	a3,4(a5)
    lui	a2,0x2000
    lui	a3,0x37c00
    sw	a2,8(a5)
    addi	a3,a3,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a3,12(a5)
    sw	a2,16(a5)
    lui	a3,0x28008
    sw	a3,20(a5)
    sw	a2,24(a5)
    sw	a3,28(a5)
    sw	a3,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lw	a5,60(a4)
    zext.b	a5,a5
    beqz	a5,7b74 <.L39>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,64
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,4 # 100ec004 <__device_print_strings_info_end+0x9bec004>
    addi	a4,a4,8
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,7bb8 <.L40>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a4,0xffe80
    lw	a5,60(a4) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a5,a5
    beqz	a5,7bd4 <.L41>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,192
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,12 # 100ec00c <__device_print_strings_info_end+0x9bec00c>
    addi	a4,a4,16
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,7c18 <.L42>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a4,0xffe80
    lw	a5,60(a4) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a5,a5
    beqz	a5,7c34 <.L43>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,320
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,4 # 100ec004 <__device_print_strings_info_end+0x9bec004>
    addi	a4,a4,8
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,7c78 <.L44>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a4,0xffe80
    lw	a5,60(a4) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a5,a5
    beqz	a5,7c94 <.L45>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,448
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,12 # 100ec00c <__device_print_strings_info_end+0x9bec00c>
    addi	a4,a4,16
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,7cd8 <.L46>
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
    sfpload	L0,64,0,7
    sfpload	L1,0,0,7
    sfpadd	L0,L0,L1,2
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
    bnez	a5,7d18 <.L47>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,192,0,7
    sfpload	L1,128,0,7
    sfpadd	L0,L0,L1,2
    sfpstore	L0,128,0,7
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
    bnez	a5,7d80 <.L48>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,320,0,7
    sfpload	L1,256,0,7
    sfpadd	L0,L0,L1,2
    sfpstore	L0,256,0,7
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
    bnez	a5,7de8 <.L49>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,448,0,7
    sfpload	L1,384,0,7
    sfpadd	L0,L0,L1,2
    sfpstore	L0,384,0,7
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
    bnez	a5,7e50 <.L50>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    sfploadi	L0,16384,0
    sfpconfig	12,0,0
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s5,4
    jal	95e8 <_ZN7ckernel4sfpu21calculate_exponentialILb0ELb1ELb0ELi8ELb1EEEvm.constprop.0>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s5,s5,-1
    bnez	s5,7ed4 <.L51>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,128 # b2010080 <__device_print_strings_info_end+0xabb10080>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s5,4
    jal	95e8 <_ZN7ckernel4sfpu21calculate_exponentialILb0ELb1ELb0ELi8ELb1EEEvm.constprop.0>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s5,s5,-1
    bnez	s5,7f10 <.L52>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,256 # b2010100 <__device_print_strings_info_end+0xabb10100>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s5,4
    jal	95e8 <_ZN7ckernel4sfpu21calculate_exponentialILb0ELb1ELb0ELi8ELb1EEEvm.constprop.0>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s5,s5,-1
    bnez	s5,7f4c <.L53>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,384 # b2010180 <__device_print_strings_info_end+0xabb10180>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s5,4
    jal	95e8 <_ZN7ckernel4sfpu21calculate_exponentialILb0ELb1ELb0ELi8ELb1EEEvm.constprop.0>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s5,s5,-1
    bnez	s5,7f88 <.L54>
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
    lui	a4,0xffe80
    mv	a5,s5
    addi	a3,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a3) # 28008000 <__device_print_strings_info_end+0x21b08000>
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a3,2
    sw	a3,4(a5)
    lui	a2,0x2000
    lui	a3,0x37c00
    sw	a2,8(a5)
    addi	a3,a3,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a3,12(a5)
    sw	a2,16(a5)
    lui	a3,0x28008
    sw	a3,20(a5)
    sw	a2,24(a5)
    sw	a3,28(a5)
    sw	a3,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    addi	a5,a4,4
    sw	s5,0(a5)
    lw	s5,0(a5)
    and	zero,zero,s5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,803c <.L55>
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
    bne	a4,a5,8098 <.L56>
    j	940c <.L173>
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
    bnez	a5,80f4 <.L58>
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
    lui	a4,0xffe80
    mv	a3,a5
    addi	a2,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a3,0(a2) # 2000000 <trisck.cc.ca4958b4+0x1fef477>
    lw	a3,0(a2)
    and	zero,zero,a3
    lui	a3,0xffb80
    li	a2,4
    sw	a2,0(a3) # ffb80000 <__global_pointer$+0x7f810>
    li	a2,2
    sw	a2,4(a3)
    lui	a1,0x2000
    lui	a2,0x37c00
    sw	a1,8(a3)
    addi	a2,a2,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a2,12(a3)
    sw	a1,16(a3)
    lui	a2,0x28008
    sw	a2,20(a3)
    sw	a1,24(a3)
    sw	a2,28(a3)
    sw	a2,32(a3)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    addi	a3,a4,4
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,81c4 <.L59>
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
    bne	a4,a5,8220 <.L60>
    j	93ec <.L174>
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
    lui	a2,0xb3010
    addi	a2,a2,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a2,0(s0)
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
    lui	a3,0x34098
    sw	a3,20(a5)
    sw	a4,24(a5)
    lui	a4,0x34080
    sw	a4,28(a5)
    sw	a4,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a3,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    snez	a3,a3
    lui	a1,0xb2010
    slli	a3,a3,0x9
    add	a3,a3,a1
    addi	a5,a5,-9
    addi	a4,a4,-9 # 3407fff7 <__device_print_strings_info_end+0x2db7fff7>
    seqz	a4,a4
    sw	a3,0(s0)
    seqz	a5,a5
    lbu	a1,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    or	a5,a5,a4
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    li	a4,3
    beq	a1,a4,8338 <.L95>
    ttstallwait	128,2064
    sw	a2,0(s0)
    ttsetrwc	0,4,0,0,0,3
    ttmovd2b	0,16,0,0,0
    tttrnspsrcb
    ttmovd2b	0,16,0,0,0
    ttsetrwc	0,2,0,8,0,2
    ttsetrwc	0,2,0,8,0,2
    ttzerosrc	0,1,0,1
    ttelwadd	0,0,0,2,0
    ttelwadd	0,0,0,2,0
    ttstallwait	128,2064
    lui	a4,0xb3010
    addi	a2,a4,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    slli	a5,a5,0x8
    add	a5,a5,a2
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    sw	a3,0(s0)
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    sw	a3,0(s0)
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    sw	a3,0(s0)
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	3,4,8,0,0,6
    ttmop	1,0,0
    ttcleardvalid	3,0
    ttmop	1,0,0
    ttstallwait	128,2064
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
    ttstallwait	128,2064
    sw	a5,0(s0)
    ttsetrwc	3,0,0,0,0,6
    li	a5,1
    sb	a5,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
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
    lui	a4,0xffe80
    addi	a2,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a2)
    lw	a5,0(a2)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a2,4
    sw	a2,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a2,2
    sw	a2,4(a5)
    lui	a1,0x2000
    lui	a2,0x37c00
    sw	a1,8(a5)
    addi	a2,a2,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a2,12(a5)
    sw	a1,16(a5)
    lui	a2,0x28008
    sw	a2,20(a5)
    sw	a1,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    li	a5,0
    addi	a3,a4,4
    sw	a5,0(a3) # 34098000 <__device_print_strings_info_end+0x2db98000>
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,863c <.L62>
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
    beq	a4,a5,93d4 <.L175>
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
    sw	a5,0(a1) # 2000000 <trisck.cc.ca4958b4+0x1fef477>
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
    bnez	a5,875c <.L65>
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
    beq	a4,a5,93bc <.L176>
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
    addi	a4,a5,128 # b2010080 <__device_print_strings_info_end+0xabb10080>
    sw	a4,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a4,a5,256
    sw	a4,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a5,a5,384
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    ttsetc16	15,0
    ttsetc16	31,0
    ttsetc16	50,0
    ttsetc16	12,1
    ttsetc16	28,1
    ttsetc16	47,0
    ttsetc16	14,8
    ttsetc16	30,8
    ttsetc16	49,0
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    li	a3,2
    sw	a3,4(a5)
    lui	a2,0x2000
    lui	a3,0x37c00
    sw	a2,8(a5)
    addi	a3,a3,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	a3,12(a5)
    sw	a2,16(a5)
    lui	a3,0x28008
    sw	a3,20(a5)
    sw	a2,24(a5)
    sw	a3,28(a5)
    sw	a3,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lw	a5,60(a4)
    zext.b	a5,a5
    beqz	a5,88d8 <.L68>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,64
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,4 # 100ec004 <__device_print_strings_info_end+0x9bec004>
    addi	a4,a4,8
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,891c <.L69>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a4,0xffe80
    lw	a5,60(a4) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a5,a5
    beqz	a5,8938 <.L70>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,192
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,12 # 100ec00c <__device_print_strings_info_end+0x9bec00c>
    addi	a4,a4,16
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,897c <.L71>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a4,0xffe80
    lw	a5,60(a4) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a5,a5
    beqz	a5,8998 <.L72>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,320
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,4 # 100ec004 <__device_print_strings_info_end+0x9bec004>
    addi	a4,a4,8
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,89dc <.L73>
    ttsemwait	2,128,2
    ttstallwait	2,2064
    ttsempost	128
    lui	a4,0xffe80
    lw	a5,60(a4) # ffe8003c <__instrn_buffer+0x4003c>
    zext.b	a5,a5
    beqz	a5,89f8 <.L74>
    li	a5,1
    sw	a5,60(a4)
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xffec1
    snez	a5,a5
    slli	a5,a5,0x9
    addi	a5,a5,448
    sw	a5,0(a4) # ffec1000 <__instrn_buffer+0x81000>
    ttsemwait	2,4,1
    ttstallwait	2,2064
    ttsemget	4
    lui	a4,0x100ec
    addi	a5,a4,12 # 100ec00c <__device_print_strings_info_end+0x9bec00c>
    addi	a4,a4,16
    sw	a5,0(s0)
    addi	a5,a5,1
    bne	a5,a4,8a3c <.L75>
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
    sfpload	L0,64,0,7
    sfpload	L1,0,0,7
    sfpadd	L0,L0,L1,2
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
    bnez	a5,8a7c <.L76>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,192,0,7
    sfpload	L1,128,0,7
    sfpadd	L0,L0,L1,2
    sfpstore	L0,128,0,7
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
    bnez	a5,8ae4 <.L77>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,320,0,7
    sfpload	L1,256,0,7
    sfpadd	L0,L0,L1,2
    sfpstore	L0,256,0,7
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
    bnez	a5,8b4c <.L78>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,448,0,7
    sfpload	L1,384,0,7
    sfpadd	L0,L0,L1,2
    sfpstore	L0,384,0,7
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
    bnez	a5,8bb4 <.L79>
    ttsetrwc	0,0,0,0,0,4
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
    mv	a3,a5
    addi	a2,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a3,0(a2) # 2000000 <trisck.cc.ca4958b4+0x1fef477>
    lw	a3,0(a2)
    and	zero,zero,a3
    lui	a3,0xffb80
    li	a2,2
    sw	a2,0(a3) # ffb80000 <__global_pointer$+0x7f810>
    sw	a2,4(a3)
    lui	a1,0x2000
    lui	a2,0x37080
    sw	a1,8(a3)
    addi	a2,a2,2 # 37080002 <__device_print_strings_info_end+0x30b80002>
    sw	a2,12(a3)
    sw	a1,16(a3)
    lui	a2,0x28088
    sw	a2,20(a3)
    sw	a1,24(a3)
    sw	a2,28(a3)
    sw	a2,32(a3)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    addi	a3,a4,4
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,8c8c <.L80>
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
    beq	a4,a5,93a4 <.L177>
    li	a5,4
    li	a4,1
    sw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    sb	a4,-1800(gp) # ffb000e8 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(s0)
    lui	a4,0xb2010
    addi	a5,a4,64 # b2010040 <__device_print_strings_info_end+0xabb10040>
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a5,a4,192
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a5,a4,320
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a5,a4,448
    sw	a5,0(s0)
    ttmop	1,0,0
    ttsetrwc	2,0,0,0,0,0
    ttmop	1,0,0
    ttsetrwc	3,0,0,0,0,0
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    sfploadi	L0,16384,0
    sfpconfig	12,0,0
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s2,4
    jal	95e8 <_ZN7ckernel4sfpu21calculate_exponentialILb0ELb1ELb0ELi8ELb1EEEvm.constprop.0>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s2,s2,-1
    bnez	s2,8db4 <.L83>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,128 # b2010080 <__device_print_strings_info_end+0xabb10080>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s2,4
    jal	95e8 <_ZN7ckernel4sfpu21calculate_exponentialILb0ELb1ELb0ELi8ELb1EEEvm.constprop.0>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s2,s2,-1
    bnez	s2,8df0 <.L84>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,256 # b2010100 <__device_print_strings_info_end+0xabb10100>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s2,4
    jal	95e8 <_ZN7ckernel4sfpu21calculate_exponentialILb0ELb1ELb0ELi8ELb1EEEvm.constprop.0>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s2,s2,-1
    bnez	s2,8e2c <.L85>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,384 # b2010180 <__device_print_strings_info_end+0xabb10180>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	s2,4
    jal	95e8 <_ZN7ckernel4sfpu21calculate_exponentialILb0ELb1ELb0ELi8ELb1EEEvm.constprop.0>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	s2,s2,-1
    bnez	s2,8e68 <.L86>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetc16	18,0
    ttsetc16	34,2
    ttsetc16	53,0
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
    ttreplay	0,28,1,1
    sfpload	L2,0,0,7
    sfpsetsgn	L1,L2,0x001,1
    sfpsetexp	L1,L1,0x07E,1
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L3,L1,L0,0
    sfpaddi	L3,16384,0
    sfpmul	L0,L0,L3,0
    sfpmul	L3,L1,L0,0
    sfpaddi	L3,16384,0
    sfpmul	L0,L0,L3,0
    sfpmul	L1,L1,L0,0
    sfpaddi	L1,16384,0
    sfpmul	L0,L0,L1,0
    sfpexexp	L1,L2,0
    sfpexexp	L3,L0,0
    sfpiadd	L1,L3,0x000,6
    sfpiadd	L1,L1,0x07E,5
    sfpsetcc	L1,0x000,0
    sfpmov	L0,L9,0
    sfpmov	L1,L9,0
    sfpencc	0x003,10
    sfpsetexp	L1,L0,0x000,0
    sfpsetcc	L2,0x000,0
    sfpmov	L1,L1,1
    sfpencc	0x003,10
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,8ec4 <.L87>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,192 # b20100c0 <__device_print_strings_info_end+0xabb100c0>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,28,1,1
    sfpload	L2,0,0,7
    sfpsetsgn	L1,L2,0x001,1
    sfpsetexp	L1,L1,0x07E,1
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L3,L1,L0,0
    sfpaddi	L3,16384,0
    sfpmul	L0,L0,L3,0
    sfpmul	L3,L1,L0,0
    sfpaddi	L3,16384,0
    sfpmul	L0,L0,L3,0
    sfpmul	L1,L1,L0,0
    sfpaddi	L1,16384,0
    sfpmul	L0,L0,L1,0
    sfpexexp	L1,L2,0
    sfpexexp	L3,L0,0
    sfpiadd	L1,L3,0x000,6
    sfpiadd	L1,L1,0x07E,5
    sfpsetcc	L1,0x000,0
    sfpmov	L0,L9,0
    sfpmov	L1,L9,0
    sfpencc	0x003,10
    sfpsetexp	L1,L0,0x000,0
    sfpsetcc	L2,0x000,0
    sfpmov	L1,L1,1
    sfpencc	0x003,10
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,8f8c <.L88>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,320 # b2010140 <__device_print_strings_info_end+0xabb10140>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,28,1,1
    sfpload	L2,0,0,7
    sfpsetsgn	L1,L2,0x001,1
    sfpsetexp	L1,L1,0x07E,1
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L3,L1,L0,0
    sfpaddi	L3,16384,0
    sfpmul	L0,L0,L3,0
    sfpmul	L3,L1,L0,0
    sfpaddi	L3,16384,0
    sfpmul	L0,L0,L3,0
    sfpmul	L1,L1,L0,0
    sfpaddi	L1,16384,0
    sfpmul	L0,L0,L1,0
    sfpexexp	L1,L2,0
    sfpexexp	L3,L0,0
    sfpiadd	L1,L3,0x000,6
    sfpiadd	L1,L1,0x07E,5
    sfpsetcc	L1,0x000,0
    sfpmov	L0,L9,0
    sfpmov	L1,L9,0
    sfpencc	0x003,10
    sfpsetexp	L1,L0,0x000,0
    sfpsetcc	L2,0x000,0
    sfpmov	L1,L1,1
    sfpencc	0x003,10
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,9054 <.L89>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    addi	a4,a4,448 # b20101c0 <__device_print_strings_info_end+0xabb101c0>
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,28,1,1
    sfpload	L2,0,0,7
    sfpsetsgn	L1,L2,0x001,1
    sfpsetexp	L1,L1,0x07E,1
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L3,L1,L0,0
    sfpaddi	L3,16384,0
    sfpmul	L0,L0,L3,0
    sfpmul	L3,L1,L0,0
    sfpaddi	L3,16384,0
    sfpmul	L0,L0,L3,0
    sfpmul	L1,L1,L0,0
    sfpaddi	L1,16384,0
    sfpmul	L0,L0,L1,0
    sfpexexp	L1,L2,0
    sfpexexp	L3,L0,0
    sfpiadd	L1,L3,0x000,6
    sfpiadd	L1,L1,0x07E,5
    sfpsetcc	L1,0x000,0
    sfpmov	L0,L9,0
    sfpmov	L1,L9,0
    sfpencc	0x003,10
    sfpsetexp	L1,L0,0x000,0
    sfpsetcc	L2,0x000,0
    sfpmov	L1,L1,1
    sfpencc	0x003,10
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttreplay	0,28,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,911c <.L90>
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
    bnez	a5,91f4 <.L91>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,128,0,7
    sfpload	L1,192,0,7
    sfpmul	L0,L0,L1,0
    sfpstore	L0,128,0,7
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
    bnez	a5,925c <.L92>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,256,0,7
    sfpload	L1,320,0,7
    sfpmul	L0,L0,L1,0
    sfpstore	L0,256,0,7
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
    bnez	a5,92c4 <.L93>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a4,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a4
    sw	a5,0(s0)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,5,1,1
    sfpload	L0,384,0,7
    sfpload	L1,448,0,7
    sfpmul	L0,L0,L1,0
    sfpstore	L0,384,0,7
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
    bnez	a5,932c <.L94>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    lw	ra,28(sp)
    lw	s0,24(sp)
    lw	s1,20(sp)
    lw	s2,16(sp)
    lw	s3,12(sp)
    lw	s4,8(sp)
    lw	s5,4(sp)
    li	a0,0
    addi	sp,sp,32
    ret
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    bne	a5,a4,8ce4 <.L81>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a4,a5,8ce4 <.L81>
    j	8d08 <.L82>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    bne	a5,a4,87b4 <.L66>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a4,a5,87b4 <.L66>
    j	87d8 <.L67>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    bne	a5,a4,8694 <.L63>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a4,a5,8694 <.L63>
    j	86b0 <.L64>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,93fc <.LM4284>
    j	8220 <.L60>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,9408 <.LM4284+0xc>
    j	8220 <.L60>
    j	823c <.L61>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,941c <.LM4287>
    j	8098 <.L56>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,9428 <.LM4287+0xc>
    j	8098 <.L56>
    j	80b4 <.L57>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,943c <.LM4290>
    j	7a50 <.L37>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,9448 <.LM4290+0xc>
    j	7a50 <.L37>
    j	7a74 <.L38>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,945c <.LM4293>
    j	792c <.L34>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,9468 <.LM4293+0xc>
    j	792c <.L34>
    j	7948 <.L35>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,947c <.LM4296>
    j	74d4 <.L31>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,9488 <.LM4296+0xc>
    j	74d4 <.L31>
    j	74f0 <.L32>
    lw	a5,-1804(gp) # ffb000e4 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,4
    beq	a5,a4,949c <.LM4299>
    j	73c4 <.L27>
    lw	a4,-1808(gp) # ffb000e0 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,94a8 <.LM4299+0xc>
    j	73c4 <.L27>
    j	73e0 <.L28>
    mv	a5,a3
    j	7290 <.L17>
    addi	a5,gp,-2000 # ffb00020 <_ZL21unpack_tile_num_faces>
    add	a0,a5,a0
    lbu	a4,128(a0)
    li	a1,30
    lbu	a3,0(a0)
    lbu	a2,64(a0)
    li	a5,0
    bltu	a1,a4,94e4 <.L2>
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
    beqz	a5,9520 <.L3>
    li	a5,9
    lui	a4,0xffe80
    beq	a2,a5,9584 <.L4>
    li	a5,0
    j	952c <.L8>
    li	a4,9
    beq	a2,a4,95e0 <.L6>
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
    j	9588 <.L9>
    li	a5,8
    sfpload	L4,0,0,7
    sfploadi	L1,-21957,2
    sfploadi	L1,16312,8
    sfpmul	L1,L4,L1,0
    sfploadi	L0,5541,1
    sfpstochrnd	L1,L0,L1,0,7,0
    sfpcast	L2,L1,0
    sfploadi	L3,29184,2
    sfploadi	L3,-16591,8
    sfpmad	L3,L2,L3,L4,0
    sfploadi	L4,-16754,2
    sfploadi	L4,-19009,8
    sfpmad	L2,L2,L4,L3,0
    sfploadi	L3,12142,2
    sfploadi	L3,15369,8
    sfpmad	L0,L0,L2,L3,0
    sfploadi	L3,-21075,2
    sfploadi	L3,15658,8
    sfpmad	L0,L0,L2,L3,0
    sfploadi	L3,-21976,2
    sfploadi	L3,15914,8
    sfpmad	L0,L0,L2,L3,0
    sfploadi	L3,-5,2
    sfploadi	L3,16127,8
    sfpmad	L0,L0,L2,L3,0
    sfpmad	L0,L0,L2,L10,0
    sfpsetcc	L1,0x000,0
    sfpsetsgn	L1,L1,0x000,1
    sfpiadd	L1,L9,0x000,6
    sfpencc	0x003,10
    sfpmad	L2,L0,L2,L10,0
    sfpexexp	L3,L2,1
    sfpiadd	L3,L1,0x000,4
    sfpmuli	L0,32640,0
    sfpiadd	L1,L3,0xF01,1
    sfpmov	L0,L3,0
    sfpsetexp	L0,L2,0x000,0
    sfpiadd	L1,L1,0x0FE,1
    sfpmov	L0,L9,0
    sfpencc	0x003,10
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    addi	a5,a5,-1
    bnez	a5,95ec <.L12>
    ret
