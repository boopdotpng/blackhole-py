    lui	a5,0xffb00
    lui	a4,0xffb00
    addi	a5,a5,56 # ffb00038 <__stack_base+0x8>
    addi	a4,a4,44 # ffb0002c <__ldm_bss_end>
    bltu	a4,a5,725c <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,7244 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,7ecc <.L33>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,7278 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x1
    addi	a4,a4,-932 # 7ed4 <__kernel_data_lma>
    addi	a5,gp,-2000 # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    beq	a4,a5,72e8 <.L7>
    lui	a2,0xffb00
    addi	a2,a2,40 # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,72cc <.L8>
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
    blt	a6,a3,72a4 <.L9>
    blez	a3,72e8 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,72e8 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LVUS110+0x3>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,730c <.L11>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7300 <.L12>
    ttsetc16	13,0
    ttsetc16	29,0
    ttsetc16	48,0
    ttzeroacc	3,0,0,1,0
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
    lui	a2,0x1200a
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
    bnez	a5,73b4 <.L13>
    ttseminit	2,0,2
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttsetc16	1,0
    lui	a4,0xffe40
    lui	a5,0xb3080
    mv	a4,a4
    addi	a5,a5,220 # b30800dc <__device_print_strings_info_end+0xacb800dc>
    sw	a5,0(a4) # ffe40000 <__instrn_buffer>
    ttstallwait	128,16
    lui	a5,0xb6800
    addi	a5,a5,1 # b6800001 <__device_print_strings_info_end+0xb0300001>
    sw	a5,0(a4)
    lui	a5,0xb6200
    addi	a5,a5,1 # b6200001 <__device_print_strings_info_end+0xafd00001>
    sw	a5,0(a4)
    lui	a5,0xb6400
    addi	a5,a5,1 # b6400001 <__device_print_strings_info_end+0xaff00001>
    sw	a5,0(a4)
    lbu	a1,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    li	a5,1
    beq	a1,a5,7eb4 <.L49>
    li	a5,5
    sw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    sw	a5,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,2 # b3010002 <__device_print_strings_info_end+0xacb10002>
    sw	a5,0(a4)
    li	t5,2
    sb	t5,-1992(gp) # ffb00028 <_ZN7ckernel4mathL19src_zero_flag_stateE>
    ttstallwait	128,2064
    lui	a5,0xb3010
    addi	a5,a5,258 # b3010102 <__device_print_strings_info_end+0xacb10102>
    sw	a5,0(a4)
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
    lui	t4,0xffe80
    addi	t4,t4,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(t4)
    lw	a5,0(t4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__global_pointer$+0x7f810>
    sw	t5,4(a5)
    lui	a7,0x2000
    lui	t3,0x37c00
    sw	a7,8(a5)
    addi	t3,t3,3 # 37c00003 <__device_print_strings_info_end+0x31700003>
    sw	t3,12(a5)
    sw	a7,16(a5)
    lui	a6,0x1200a
    sw	a6,20(a5)
    sw	a7,24(a5)
    sw	a6,28(a5)
    sw	a6,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a1,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a0,0xb2010
    snez	a1,a1
    slli	a1,a1,0x9
    add	t6,a1,a0
    sw	t6,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	t6,a0,128 # b2010080 <__device_print_strings_info_end+0xabb10080>
    add	t6,a1,t6
    sw	t6,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	t6,a0,256
    add	t6,a1,t6
    sw	t6,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	t6,a0,384
    add	a1,a1,t6
    sw	a1,0(a4)
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
    li	a1,0
    sw	a1,0(t4)
    lw	a1,0(t4)
    and	zero,zero,a1
    sw	a3,0(a5)
    sw	t5,4(a5)
    sw	a7,8(a5)
    sw	t3,12(a5)
    sw	a7,16(a5)
    sw	a6,20(a5)
    sw	a7,24(a5)
    sw	a6,28(a5)
    sw	a6,32(a5)
    ttsetc16	7,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    addi	a1,a0,64
    snez	a5,a5
    slli	a5,a5,0x9
    add	a1,a5,a1
    sw	a1,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a1,a0,192
    add	a1,a5,a1
    sw	a1,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a1,a0,320
    add	a1,a5,a1
    sw	a1,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    addi	a1,a0,448
    add	a1,a5,a1
    sw	a1,0(a4)
    ttmop	1,0,0
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    sfploadi	L0,16384,0
    sfpconfig	12,0,0
    add	a5,a5,a0
    sw	a5,0(a4)
    ttstallwait	256,16
    mv	a5,a3
    ttreplay	0,31,1,1
    sfpload	L1,0,0,7
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L0,L1,L0,1
    sfpaddi	L0,17150,0
    sfploadi	L2,17279,0
    sfpswap	L9,L0,1
    sfpnop
    sfpswap	L0,L2,1
    sfpnop
    sfpexexp	L2,L0,0
    sfpexman	L0,L0,0
    sfpshft	L0,L2,0x000,0
    sfpexexp	L3,L0,1
    sfpexman	L0,L0,1
    sfpcast	L0,L0,0
    sfploadi	L2,-23528,2
    sfploadi	L2,10156,8
    sfploadi	L4,23258,2
    sfploadi	L4,13224,8
    sfpmad	L2,L0,L2,L4,0
    sfploadi	L4,14469,2
    sfploadi	L4,16256,8
    sfpmad	L2,L0,L2,L4,0
    sfpmov	L0,L3,2
    sfpsetexp	L0,L2,0x000,0
    sfpadd	L0,L10,L0,0
    sfparecip	L2,L0,0
    sfpmad	L0,L0,L2,L12,2
    sfpsetcc	L0,0x000,0
    sfpmad	L2,L2,L0,L9,3
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,7610 <.L16>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a5,a5
    addi	a3,a3,128 # b2010080 <__device_print_strings_info_end+0xabb10080>
    slli	a5,a5,0x9
    add	a5,a5,a3
    sw	a5,0(a4)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,31,1,1
    sfpload	L1,0,0,7
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L0,L1,L0,1
    sfpaddi	L0,17150,0
    sfploadi	L2,17279,0
    sfpswap	L9,L0,1
    sfpnop
    sfpswap	L0,L2,1
    sfpnop
    sfpexexp	L2,L0,0
    sfpexman	L0,L0,0
    sfpshft	L0,L2,0x000,0
    sfpexexp	L3,L0,1
    sfpexman	L0,L0,1
    sfpcast	L0,L0,0
    sfploadi	L2,-23528,2
    sfploadi	L2,10156,8
    sfploadi	L4,23258,2
    sfploadi	L4,13224,8
    sfpmad	L2,L0,L2,L4,0
    sfploadi	L4,14469,2
    sfploadi	L4,16256,8
    sfpmad	L2,L0,L2,L4,0
    sfpmov	L0,L3,2
    sfpsetexp	L0,L2,0x000,0
    sfpadd	L0,L10,L0,0
    sfparecip	L2,L0,0
    sfpmad	L0,L0,L2,L12,2
    sfpsetcc	L0,0x000,0
    sfpmad	L2,L2,L0,L9,3
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,7784 <.L17>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a5,a5
    addi	a3,a3,256 # b2010100 <__device_print_strings_info_end+0xabb10100>
    slli	a5,a5,0x9
    add	a5,a5,a3
    sw	a5,0(a4)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,31,1,1
    sfpload	L1,0,0,7
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L0,L1,L0,1
    sfpaddi	L0,17150,0
    sfploadi	L2,17279,0
    sfpswap	L9,L0,1
    sfpnop
    sfpswap	L0,L2,1
    sfpnop
    sfpexexp	L2,L0,0
    sfpexman	L0,L0,0
    sfpshft	L0,L2,0x000,0
    sfpexexp	L3,L0,1
    sfpexman	L0,L0,1
    sfpcast	L0,L0,0
    sfploadi	L2,-23528,2
    sfploadi	L2,10156,8
    sfploadi	L4,23258,2
    sfploadi	L4,13224,8
    sfpmad	L2,L0,L2,L4,0
    sfploadi	L4,14469,2
    sfploadi	L4,16256,8
    sfpmad	L2,L0,L2,L4,0
    sfpmov	L0,L3,2
    sfpsetexp	L0,L2,0x000,0
    sfpadd	L0,L10,L0,0
    sfparecip	L2,L0,0
    sfpmad	L0,L0,L2,L12,2
    sfpsetcc	L0,0x000,0
    sfpmad	L2,L2,L0,L9,3
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,78f8 <.L18>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a5,a5
    addi	a3,a3,384 # b2010180 <__device_print_strings_info_end+0xabb10180>
    slli	a5,a5,0x9
    add	a5,a5,a3
    sw	a5,0(a4)
    ttstallwait	256,16
    li	a5,4
    ttreplay	0,31,1,1
    sfpload	L1,0,0,7
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L0,L1,L0,1
    sfpaddi	L0,17150,0
    sfploadi	L2,17279,0
    sfpswap	L9,L0,1
    sfpnop
    sfpswap	L0,L2,1
    sfpnop
    sfpexexp	L2,L0,0
    sfpexman	L0,L0,0
    sfpshft	L0,L2,0x000,0
    sfpexexp	L3,L0,1
    sfpexman	L0,L0,1
    sfpcast	L0,L0,0
    sfploadi	L2,-23528,2
    sfploadi	L2,10156,8
    sfploadi	L4,23258,2
    sfploadi	L4,13224,8
    sfpmad	L2,L0,L2,L4,0
    sfploadi	L4,14469,2
    sfploadi	L4,16256,8
    sfpmad	L2,L0,L2,L4,0
    sfpmov	L0,L3,2
    sfpsetexp	L0,L2,0x000,0
    sfpadd	L0,L10,L0,0
    sfparecip	L2,L0,0
    sfpmad	L0,L0,L2,L12,2
    sfpsetcc	L0,0x000,0
    sfpmad	L2,L2,L0,L9,3
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttreplay	0,31,0,0
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    sfpload	L1,0,0,7
    sfploadi	L0,-21957,2
    sfploadi	L0,16312,8
    sfpmul	L0,L1,L0,1
    sfpaddi	L0,17150,0
    sfploadi	L2,17279,0
    sfpswap	L9,L0,1
    sfpnop
    sfpswap	L0,L2,1
    sfpnop
    sfpexexp	L2,L0,0
    sfpexman	L0,L0,0
    sfpshft	L0,L2,0x000,0
    sfpexexp	L2,L0,1
    sfpexman	L0,L0,1
    sfpcast	L0,L0,0
    sfploadi	L3,-23528,2
    sfploadi	L3,10156,8
    sfploadi	L4,23258,2
    sfploadi	L4,13224,8
    sfpmad	L3,L0,L3,L4,0
    sfploadi	L4,14469,2
    sfploadi	L4,16256,8
    sfpmad	L3,L0,L3,L4,0
    sfpmov	L0,L2,2
    sfpsetexp	L0,L3,0x000,0
    sfpadd	L0,L10,L0,0
    sfparecip	L2,L0,0
    sfpmad	L0,L0,L2,L12,2
    sfpsetcc	L0,0x000,0
    sfpmad	L2,L2,L0,L9,3
    sfpencc	0x003,10
    sfpmul	L1,L1,L2,0
    sfpstochrnd	L1,L0,L1,0,1,0
    sfpstore	L1,0,0,7
    ttincrwc	0,2,0,0
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a5,a5,-1
    bnez	a5,7a6c <.L19>
    ttsetrwc	0,0,0,0,0,4
    sfpconfig	15,0,1
    ttsetc16	19,0
    ttsetc16	35,0
    ttsetc16	54,0
    ttsetrwc	0,0,0,0,0,15
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a3
    sw	a5,0(a4)
    ttstallwait	256,16
    li	a3,4
    li	a5,8
    sfpload	L3,0,0,7
    sfpload	L2,64,0,7
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
    sfpstore	L0,0,0,7
    ttincrwc	0,2,0,0
    addi	a5,a5,-1
    bnez	a5,7c6c <.L21>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a3,a3,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    bnez	a3,7c68 <.L20>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a3
    sw	a5,0(a4)
    ttstallwait	256,16
    li	a3,4
    li	a5,8
    sfpload	L3,128,0,7
    sfpload	L2,192,0,7
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
    sfpstore	L0,128,0,7
    ttincrwc	0,2,0,0
    addi	a5,a5,-1
    bnez	a5,7cf8 <.L24>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a3,a3,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    bnez	a3,7cf4 <.L23>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a3
    sw	a5,0(a4)
    ttstallwait	256,16
    li	a3,4
    li	a5,8
    sfpload	L3,256,0,7
    sfpload	L2,320,0,7
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
    sfpstore	L0,256,0,7
    ttincrwc	0,2,0,0
    addi	a5,a5,-1
    bnez	a5,7d84 <.L27>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a3,a3,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    bnez	a3,7d80 <.L26>
    ttsetrwc	0,0,0,0,0,4
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    lui	a3,0xb2010
    snez	a5,a5
    slli	a5,a5,0x9
    add	a5,a5,a3
    sw	a5,0(a4)
    ttstallwait	256,16
    li	a3,4
    li	a5,8
    sfpload	L3,384,0,7
    sfpload	L2,448,0,7
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
    sfpstore	L0,384,0,7
    ttincrwc	0,2,0,0
    addi	a5,a5,-1
    bnez	a5,7e10 <.L30>
    ttsetrwc	0,4,8,0,0,4
    ttsetrwc	0,4,8,0,0,4
    addi	a3,a3,-1 # b200ffff <__device_print_strings_info_end+0xabb0ffff>
    bnez	a3,7e0c <.L29>
    ttsetrwc	0,0,0,0,0,4
    ttstallwait	2,2064
    ttsempost	2
    lw	a5,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    li	a3,1
    sub	a3,a3,a5
    sw	a3,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	128,2064
    addi	a5,a5,-1
    snez	a5,a5
    lui	a3,0xb2010
    slli	a5,a5,0x9
    add	a5,a5,a3
    sw	a5,0(a4)
    li	a0,0
    ret
    lw	a5,-1996(gp) # ffb00024 <_ZN7ckernel4mathL22src_zero_flag_srca_fmtE>
    li	a6,5
    bne	a5,a6,7414 <.L14>
    lw	a6,-2000(gp) # ffb00020 <_ZN7ckernel4mathL22src_zero_flag_srcb_fmtE>
    bne	a6,a5,7414 <.L14>
    j	7430 <.L15>
    mv	a5,a3
    j	726c <.L4>
