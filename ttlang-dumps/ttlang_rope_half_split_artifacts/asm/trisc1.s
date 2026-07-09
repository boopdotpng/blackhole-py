    addi	sp,sp,-16
    sw	s0,12(sp)
    lui	a5,0xffb00
    lui	a4,0xffb00
    addi	a5,a5,56 # ffb00038 <__stack_base+0x8>
    addi	a4,a4,44 # ffb0002c <__ldm_bss_end>
    bltu	a4,a5,7264 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,724c <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,7a30 <.L29>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,7280 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,1976 # 7a38 <__kernel_data_lma>
    addi	a5,gp,-2000 # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,72f0 <.L7>
    lui	a2,0xffb00
    addi	a2,a2,40 # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,72d4 <.L8>
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
    blt	a6,a3,72ac <.L9>
    blez	a3,72f0 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,72f0 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LLST111+0x14>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7314 <.L11>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7308 <.L12>
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttzeroacc	3,0,0,1,0
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,733c <.L13>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a3,0xffe40
    lui	a5,0xb3080
    mv	a3,a3
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(a3) # ffe40000 <__instrn_buffer>
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(a3)
    lui	a5,0xb6200
    addi	a5,a5,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a5,0(a3)
    lui	a5,0xb6400
    addi	a5,a5,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a5,0(a3)
    lbu	a4,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    beq	a4,a5,7a18 <.L48>
    li	a5,5
    li	a4,1
    sw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    sb	a4,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(a3)
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
    li	t3,0
    lui	t6,0xffe80
    addi	t6,t6,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,t3
    sw	a5,0(t6)
    lw	a5,0(t6)
    and	zero,zero,a5
    lui	a4,0xffb80
    li	a5,4
    sw	a5,0(a4) # ffb80000 <__global_pointer$+0x7f810>
    li	t2,2
    sw	t2,4(a4)
    lui	a1,0x2000
    lui	t0,0x37c00
    sw	a1,8(a4)
    addi	t0,t0,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	t0,12(a4)
    sw	a1,16(a4)
    lui	t4,0x1200a
    sw	t4,20(a4)
    sw	a1,24(a4)
    sw	t4,28(a4)
    sw	t4,32(a4)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	t1,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	t5,0xb2010
    snez	t1,t1
    addi	s0,t5,64 # b2010040 <__device_print_strings_info_end+0xabb10040>
    slli	t1,t1,0x9
    add	t1,t1,s0
    sw	t1,0(a3)
    ttmop	1,0,0
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
    mv	t1,t3
    sw	t1,0(t6)
    lw	t1,0(t6)
    and	zero,zero,t1
    sw	a5,0(a4)
    sw	t2,4(a4)
    sw	a1,8(a4)
    sw	t0,12(a4)
    sw	a1,16(a4)
    sw	t4,20(a4)
    sw	a1,24(a4)
    sw	t4,28(a4)
    sw	t4,32(a4)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	t1,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    addi	t4,t5,128
    snez	t1,t1
    slli	t1,t1,0x9
    add	t1,t1,t4
    sw	t1,0(a3)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
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
    sw	t3,0(t6)
    lw	t3,0(t6)
    and	zero,zero,t3
    sw	a5,0(a4)
    sw	t2,4(a4)
    sw	a1,8(a4)
    sw	a1,12(a4)
    sw	a1,16(a4)
    lui	t1,0x27000
    sw	t1,20(a4)
    sw	a1,24(a4)
    lui	a1,0x27c0c
    sw	a1,28(a4)
    lui	a1,0x27008
    sw	a1,32(a4)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    snez	a4,a4
    slli	a4,a4,0x9
    add	t5,a4,t5
    sw	t5,0(a3)
    ttmop	1,0,0
    addi	a5,a5,-1
    bnez	a5,7578 <.L16>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lui	a5,0xb2010
    addi	a5,a5,64 # b2010040 <__device_print_strings_info_end+0xabb10040>
    add	a4,a4,a5
    sw	a4,0(a3)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,8,1,1
    sfpload	L0,0,0,7
    sfpmov	L0,L0,1
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    sfpload	L0,0,0,7
    sfpmov	L0,L0,1
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,8,0,0
    ttreplay	0,8,0,0
    ttreplay	0,8,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,75b4 <.L17>
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
    sw	a5,0(a3)
    ttstallwait	256,16
    li	a4,4
    li	a5,8
    sfpload	L3,64,0,7
    sfpload	L2,128,0,7
    sfpmul	L0,L3,L2,0
    sfpnop
    sfpshft	L1,L0,0xFF0,5
    sfploadi	L4,1,2
    sfpand	L1,L1,L4,1
    sfploadi	L4,32767,2
    sfpiadd	L0,L4,0x000,4
    sfpiadd	L0,L1,0x000,4
    sfploadi	L1,-1,0
    sfpand	L0,L0,L1,1
    sfpsetcc	L3,0x000,2
    sfpsetcc	L2,0x000,2
    sfpcompc
    sfpmov	L0,L9,0
    sfpencc	0x003,10
    sfpstore	L0,64,0,7
    ttincrwc	0,2,0,0
    addi	a5,a5,-1
    bnez	a5,7630 <.L19>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a4,a4,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    bnez	a4,762c <.L18>
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
    sw	a5,0(a3)
    ttstallwait	256,16
    li	a5,4
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
    addi	a5,a5,-1
    bnez	a5,76cc <.L21>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    li	a1,1
    sub	a1,a1,a4
    sw	a1,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a4,a4,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    snez	a4,a4
    lui	a1,0xb2010
    slli	a4,a4,0x9
    add	a4,a4,a1
    sw	a4,0(a3)
    lui	a4,0xffe80
    addi	a1,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	a5,0(a1) # b2010000 <__device_print_strings_info_end+0xabb10000>
    lw	a5,0(a1)
    and	zero,zero,a5
    lw	a5,36(a4)
    zext.b	a5,a5
    bnez	a5,775c <.L22>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a5,0xb3080
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(a3)
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(a3)
    lui	a5,0xb6200
    addi	a5,a5,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a5,0(a3)
    lui	a5,0xb6400
    addi	a5,a5,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a5,0(a3)
    lbu	a4,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    beq	a4,a5,7a00 <.L49>
    li	a5,5
    li	a4,1
    sw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    sb	a4,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(a3)
    ttsemwait	322,2,2
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
    lui	a4,0xffe80
    li	a5,0
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a4,0xffb80
    li	a5,4
    sw	a5,0(a4) # ffb80000 <__global_pointer$+0x7f810>
    li	a1,2
    sw	a1,4(a4)
    lui	a1,0x2000
    sw	a1,8(a4)
    sw	a1,12(a4)
    sw	a1,16(a4)
    lui	a0,0x27000
    sw	a0,20(a4)
    sw	a1,24(a4)
    lui	a1,0x27c0c
    sw	a1,28(a4)
    lui	a1,0x27008
    sw	a1,32(a4)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a1,0xb2010
    snez	a4,a4
    slli	a4,a4,0x9
    add	a4,a4,a1
    sw	a4,0(a3)
    ttmop	1,0,0
    addi	a5,a5,-1
    bnez	a5,7884 <.L25>
    ttsetrwc	0,0,0,0,0,4
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
    lui	a4,0xffe80
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a4,0xffb80
    li	a5,4
    sw	a5,0(a4) # ffb80000 <__global_pointer$+0x7f810>
    li	a1,2
    sw	a1,4(a4)
    lui	a1,0x2000
    sw	a1,8(a4)
    sw	a1,12(a4)
    sw	a1,16(a4)
    lui	a0,0x27000
    sw	a0,20(a4)
    sw	a1,24(a4)
    lui	a1,0x27c0c
    sw	a1,28(a4)
    lui	a1,0x27008
    sw	a1,32(a4)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a1,0xb2010
    snez	a4,a4
    slli	a4,a4,0x9
    addi	a1,a1,64 # b2010040 <__device_print_strings_info_end+0xabb10040>
    add	a1,a4,a1
    sw	a1,0(a3)
    ttmop	1,0,0
    addi	a5,a5,-1
    bnez	a5,793c <.L26>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lui	a5,0xb2010
    add	a4,a4,a5
    sw	a4,0(a3)
    ttstallwait	256,16
    li	a5,4
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
    addi	a5,a5,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    bnez	a5,7974 <.L27>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    li	a4,1
    sub	a4,a4,a5
    sw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a5,a5,-1
    snez	a5,a5
    slli	a5,a5,0x9
    lui	a4,0xb2010
    lw	s0,12(sp)
    add	a5,a5,a4
    sw	a5,0(a3)
    li	a0,0
    addi	sp,sp,16
    ret
    lw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,5
    bne	a5,a4,77b4 <.L23>
    lw	a4,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a4,a5,77b4 <.L23>
    j	77d8 <.L24>
    lw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a4,5
    bne	a5,a4,739c <.L14>
    lw	a4,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a4,a5,739c <.L14>
    j	73c0 <.L15>
    mv	a5,a3
    j	7274 <.L4>
