    addi	sp,sp,-16
    sw	ra,12(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__stack_base>
    addi	a4,a4,-2012 # ffb00824 <__ldm_bss_end>
    bltu	a4,a5,6aa4 <.L163>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,6a8c <.L164>
    addi	a3,a5,-8
    bltu	a4,a3,6b70 <.L175>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6ac0 <.L166>
    sw	zero,-8(a5)
    auipc	a4,0x2
    addi	a4,a4,-740 # 87dc <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <unp_cfg_context>
    beq	a4,a5,6b2c <.L168>
    addi	a2,gp,48 # ffb00820 <unp_cfg_context>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6b10 <.L169>
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
    blt	a6,a3,6ae8 <.L170>
    blez	a3,6b2c <.L168>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6b2c <.L168>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb12
    sw	zero,104(a5) # ffb12068 <__stack_base+0x11838>
    lw	a4,1312(zero) # 520 <.LLRL645+0x2>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,6b58 <.L172>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,6b4c <.L173>
    ttzerosrc	0,0,1,3
    jal	70c8 <_Z11kernel_mainv>
    lw	ra,12(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	6ab4 <.L165>
    lui	a4,0xffb00
    slli	a5,a0,0x5
    addi	a4,a4,32 # ffb00020 <cb_interface>
    add	a4,a4,a5
    lhu	a5,24(a4)
    lui	a1,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a5,0x8
    lui	a2,0xffe40
    sh	a5,24(a4)
    mv	a2,a2
    add	a5,a3,a1
    lw	a3,8(a4)
    sw	a5,0(a2) # ffe40000 <__instrn_buffer>
    ttstallwait	32,6
    lui	a1,0x3fed0
    slli	a5,a0,0xc
    srli	a5,a5,0x2
    addi	a0,a1,8 # 3fed0008 <__device_print_strings_info_end+0x399d0008>
    lui	a1,0x40
    addi	a1,a1,-1 # 3ffff <.LASF497+0x3537d>
    add	a5,a5,a0
    and	a5,a5,a1
    lui	a1,0x67100
    add	a5,a5,a1
    sw	a5,0(a2)
    lw	a5,16(a4)
    lw	a2,4(a4)
    add	a5,a3,a5
    sw	a5,16(a4)
    bltu	a5,a2,6c08 <.L1>
    lw	a3,0(a4)
    sub	a5,a5,a3
    sw	a5,16(a4)
    ret
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,6c84 <.L14>
    addi	a6,a3,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a3,a3,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6c28 <.L6>
    lw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a4,6c40 <.L7>
    mv	a3,a6
    sw	a0,0(a3)
    lui	a4,0xffe80
    sw	zero,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a1,a1,7
    lw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a1,6c60 <.L10>
    andi	a2,a2,7
    beqz	a2,6c98 <.L16>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a3,1
    sub	a2,a3,a4
    sw	a2,48(gp) # ffb00820 <unp_cfg_context>
    beq	a4,a3,6c90 <.L17>
    ttsetc16	41,257
    ret
    addi	a6,a3,304
    addi	a3,a3,308
    j	6c24 <.L5>
    ttsetc16	41,0
    ret
    lui	a3,0xffec2
    lw	a2,0(a3) # ffec2000 <__instrn_buffer+0x82000>
    addi	a2,a2,4
    slli	a1,a2,0x4
    ttsetc16	5,0
    ttrdcfg	52,57
    lui	a3,0xffe40
    lui	a0,0x45040
    mv	a3,a3
    addi	a0,a0,36 # 45040024 <__device_print_strings_info_end+0x3eb40024>
    sw	a0,0(a3) # ffe40000 <__instrn_buffer>
    ttwrcfg	18,0,57
    lui	a0,0x10
    slli	a2,a2,0xc
    addi	a0,a0,-256 # ff00 <.LASF497+0x527e>
    zext.h	a2,a2
    and	a1,a1,a0
    bnez	a4,6d58 <.L11>
    lui	a6,0xb3101
    lui	a0,0xb3ff0
    addi	a6,a6,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a0,a0,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a4,0xb4ff0
    sw	a6,0(a3)
    add	a2,a2,a0
    addi	a4,a4,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a2,0(a3)
    add	a1,a1,a4
    sw	a1,0(a3)
    ttsemwait	8,4,2
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    ttstallwait	2,2
    ttsempost	4
    ttwrcfg	52,0,57
    lui	a1,0xb3100
    addi	a1,a1,73 # b3100049 <__device_print_strings_info_end+0xacc00049>
    lui	a2,0xb3ff4
    sw	a1,0(a3)
    addi	a2,a2,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a2,0(a3)
    sw	a4,0(a3)
    ttsetc16	5,4
    li	a4,1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    ret
    lui	a7,0xb3202
    lui	a6,0xb5ff0
    addi	a7,a7,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a6,a6,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a0,0xb6ff0
    sw	a7,0(a3)
    add	a2,a2,a6
    addi	a0,a0,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a2,0(a3)
    add	a1,a1,a0
    sw	a1,0(a3)
    ttsemwait	8,4,2
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    ttstallwait	2,2
    ttsempost	4
    ttwrcfg	52,0,57
    lui	a1,0xb3200
    addi	a1,a1,73 # b3200049 <__device_print_strings_info_end+0xacd00049>
    lui	a2,0xb5ff4
    sw	a1,0(a3)
    addi	a2,a2,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a2,0(a3)
    sw	a0,0(a3)
    ttsetc16	5,4
    j	6c6c <.L9>
    addi	sp,sp,-48
    lui	t3,0xffe80
    lw	t1,52(t3) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	t1,t1
    bnez	t1,6dcc <.L19>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	t3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	t1,0xffef0
    beqz	t3,6df0 <.L20>
    addi	t1,t1,896 # ffef0380 <__instrn_buffer+0xb0380>
    andi	t3,a2,3
    li	t5,1024
    beqz	t3,6e10 <.L21>
    addi	t3,t3,-1
    snez	t3,t3
    neg	t3,t3
    andi	t5,t3,-256
    addi	t5,t5,512
    andi	t3,a3,3
    li	t4,1024
    beqz	t3,6e30 <.L22>
    addi	t3,t3,-1
    snez	t3,t3
    neg	t3,t3
    andi	t4,t3,-256
    addi	t4,t4,512
    sw	t5,228(t1)
    sw	t4,236(t1)
    ttatgetm	0
    lui	t3,0xffe40
    mv	t3,t3
    lui	t6,0xb3ff0
    sw	t6,0(t3) # ffe40000 <__instrn_buffer>
    addi	t4,a0,-30
    lui	t6,0xb47f0
    lui	t0,0xb3070
    sw	t6,0(t3)
    addi	t0,t0,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    addi	t6,a1,-30
    seqz	t4,t4
    lui	t5,0xb4800
    sw	t0,0(t3)
    addi	t5,t5,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    slli	t4,t4,0xf
    seqz	t6,t6
    lui	t0,0xb5010
    add	t4,t4,t5
    addi	t0,t0,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    andi	t5,a0,31
    slli	t6,t6,0x8
    sw	t4,0(t3)
    add	t6,t6,t0
    andi	t4,a1,31
    addi	t5,t5,-26
    sw	t6,0(t3)
    seqz	t5,t5
    lui	t6,0xb5400
    addi	t4,t4,-26
    addi	t0,t6,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    slli	t5,t5,0xe
    seqz	t4,t4
    add	t5,t5,t0
    addi	t6,t6,119
    slli	t4,t4,0xe
    sw	t5,0(t3)
    add	t4,t4,t6
    sw	t4,0(t3)
    ttatrelm	0
    andi	a0,a0,15
    sw	zero,16(sp)
    ori	a0,a0,16
    sb	a0,16(sp)
    li	a0,1
    sh	a6,22(sp)
    sh	a0,20(sp)
    lw	a0,16(sp)
    lw	a6,20(sp)
    sw	a0,256(t1)
    andi	a1,a1,15
    andi	a0,a0,-16
    sw	a6,260(t1)
    or	a0,a0,a1
    sw	a0,16(sp)
    slli	a5,a5,0x4
    andi	a2,a2,15
    sh	a5,18(sp)
    sw	zero,32(sp)
    lw	a5,16(sp)
    ori	a2,a2,32
    sh	a7,22(sp)
    sb	a2,32(sp)
    lw	a2,20(sp)
    sw	a5,448(t1)
    lw	a5,32(sp)
    sw	a2,452(t1)
    lui	a2,0xf0
    sw	a5,288(t1)
    addi	a2,a2,15 # f000f <.LASF497+0xe538d>
    andi	a3,a3,15
    andi	a5,a5,-16
    or	a5,a5,a3
    sw	a2,292(t1)
    sw	a5,32(sp)
    sw	a5,480(t1)
    sw	a2,484(t1)
    lui	a5,0x400
    addi	a5,a5,64 # 400040 <.LASF497+0x3f53be>
    bnez	a4,6f80 <.L23>
    lui	a5,0x1600
    addi	a5,a5,352 # 1600160 <.LASF497+0x15f54de>
    lui	a3,0x100
    addi	a3,a3,16 # 100010 <.LASF497+0xf538e>
    sw	a5,336(t1)
    mul	a4,a4,a3
    lui	a2,0x1000
    sw	a4,344(t1)
    lui	a5,0xffe00
    addi	a2,a2,256 # 1000100 <.LASF497+0xff547e>
    lui	a4,0x800
    sw	a2,160(a5) # ffe000a0 <__stack_base+0x2ff870>
    addi	a4,a4,128 # 800080 <.LASF497+0x7f53fe>
    lui	a2,0x400
    sw	a4,164(a5)
    addi	a2,a2,64 # 400040 <.LASF497+0x3f53be>
    lui	a4,0x200
    sw	a2,168(a5)
    addi	a4,a4,32 # 200020 <.LASF497+0x1f539e>
    sw	a4,172(a5)
    sw	a3,176(a5)
    sw	zero,12(sp)
    lw	a5,176(a5)
    sw	a5,12(sp)
    ttsetc16	5,4
    li	a4,256
    sw	a4,200(t1)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    addi	sp,sp,48
    ret
    lui	a5,0xffe40
    lui	a4,0xb4010
    mv	a5,a5
    addi	a4,a4,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a4,0(a5) # ffe40000 <__instrn_buffer>
    bnez	a0,7064 <.L36>
    ttsetadcxx	1,255,0
    lui	a5,0xffe80
    addi	a5,a5,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a0,0(a5)
    lw	a0,0(a5)
    and	zero,zero,a0
    lui	a5,0xffb80
    li	a4,4
    sw	a4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a4,1
    sw	a4,4(a5)
    lui	a3,0x2000
    sw	a3,8(a5)
    sw	a3,12(a5)
    lui	a4,0x42088
    sw	a3,16(a5)
    addi	a4,a4,129 # 42088081 <__device_print_strings_info_end+0x3bb88081>
    sw	a4,20(a5)
    sw	a3,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    ret
    ttsetadcxx	1,255,0
    lui	a4,0xffe80
    li	a5,0
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,4
    sw	a4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a4,1
    sw	a4,4(a5)
    lui	a4,0x42008
    addi	a4,a4,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a4,8(a5)
    lui	a3,0x2000
    sw	a3,12(a5)
    lui	a4,0x43800
    sw	a3,16(a5)
    addi	a4,a4,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a4,20(a5)
    sw	a3,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    ret
    addi	sp,sp,-80
    sw	s0,72(sp)
    lui	s0,0xffb00
    addi	s0,s0,32 # ffb00020 <cb_interface>
    lhu	a3,88(s0)
    sw	ra,76(sp)
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
    lui	a4,0xffb42
    lw	a5,40(a4) # ffb42028 <__stack_base+0x417f8>
    zext.h	a5,a5
    beq	a3,a5,7110 <.L39>
    lhu	a3,24(s0)
    lui	a4,0xffb40
    lw	a5,40(a4) # ffb40028 <__stack_base+0x3f7f8>
    zext.h	a5,a5
    beq	a3,a5,7124 <.L40>
    li	a3,5
    li	a7,4
    li	a5,16
    mv	a6,a7
    mv	a4,a5
    mv	a2,a3
    mv	a1,a3
    mv	a0,a3
    lw	s1,8(s0)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lui	a4,0x1000
    slli	a5,s1,0x8
    addi	a4,a4,-256 # ffff00 <.LASF497+0xff527e>
    and	a5,a5,a4
    lui	a4,0x45000
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    lui	s1,0xffe40
    mv	s1,s1
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1) # ffe40000 <__instrn_buffer>
    add	a5,a5,a4
    lui	a6,0xb4010
    sw	a5,0(s1)
    addi	a6,a6,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a6,0(s1)
    ttsetadcxx	1,255,0
    li	a2,0
    lui	a0,0xffe80
    addi	a0,a0,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a2
    sw	a5,0(a0)
    lw	a5,0(a0)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	t1,4
    sw	t1,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a7,1
    lui	a1,0x42008
    sw	a7,4(a5)
    addi	a1,a1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a1,8(a5)
    lui	a3,0x2000
    sw	a3,12(a5)
    lui	a4,0x43800
    sw	a3,16(a5)
    addi	a4,a4,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a4,20(a5)
    sw	a3,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    sw	a6,0(s1)
    ttsetadcxx	1,255,0
    sw	a2,0(a0)
    lw	a2,0(a0)
    and	zero,zero,a2
    sw	t1,0(a5)
    sw	a7,4(a5)
    sw	a1,8(a5)
    sw	a3,12(a5)
    sw	a3,16(a5)
    sw	a4,20(a5)
    sw	a3,24(a5)
    lw	a0,16(s0)
    li	a2,5
    sw	a4,28(a5)
    sw	a4,32(a5)
    addi	a0,a0,-1
    mv	a1,a2
    jal	6c0c <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    lhu	a3,344(s0)
    lui	a4,0xffb4a
    lw	a5,40(a4) # ffb4a028 <__stack_base+0x497f8>
    zext.h	a5,a5
    beq	a3,a5,7250 <.L41>
    li	a7,4
    li	a5,16
    mv	a3,a7
    mv	a4,a5
    mv	a6,a7
    mv	a2,a7
    li	a1,0
    li	a0,0
    lw	s2,360(s0)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lui	a4,0x1000
    addi	a4,a4,-256 # ffff00 <.LASF497+0xff527e>
    slli	a5,s2,0x8
    and	a5,a5,a4
    lui	a4,0x45000
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
    sw	a5,0(s1)
    li	a0,4
    jal	6ff4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lhu	a3,376(s0)
    lui	a4,0xffb4b
    lw	a5,40(a4) # ffb4b028 <__stack_base+0x4a7f8>
    zext.h	a5,a5
    beq	a3,a5,72c0 <.L42>
    li	a7,4
    li	a5,16
    mv	a3,a7
    mv	a6,a7
    mv	a2,a7
    mv	a4,a5
    li	a1,0
    li	a0,0
    lw	s2,328(s0)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lui	a4,0x1000
    slli	a5,s2,0x8
    addi	a4,a4,-256 # ffff00 <.LASF497+0xff527e>
    and	a5,a5,a4
    lui	a4,0x45000
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    add	a5,a5,a4
    sw	a3,0(s1)
    sw	a5,0(s1)
    li	a0,4
    jal	6ff4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lui	a5,0xb4010
    addi	a5,a5,328 # b4010148 <__device_print_strings_info_end+0xadb10148>
    sw	a5,0(s1)
    ttsetadcxx	1,255,0
    ttsetadcxx	2,15,0
    ttreplay	0,2,0,1
    ttunpacr	0,1,0,0,0,1,1,0,0,0,0,0,1
    ttunpacr	1,1,0,0,0,1,1,0,0,0,0,0,1
    lui	a4,0xffe80
    li	a5,0
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,1
    sw	a4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a4,4
    sw	a4,4(a5)
    lui	a3,0x2000
    sw	a3,8(a5)
    sw	a3,12(a5)
    lui	a4,0x4000
    sw	a3,16(a5)
    addi	a4,a4,32 # 4000020 <.LASF497+0x3ff539e>
    sw	a4,20(a5)
    lw	a1,336(s0)
    lw	a2,368(s0)
    sw	a3,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    addi	a1,a1,-1
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,73c0 <.L43>
    addi	a3,a3,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,73c4 <.L44>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    beqz	a5,73dc <.LM797>
    j	8794 <.L45>
    sw	a1,304(a3)
    sw	a2,496(a3)
    sw	zero,52(a4)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lhu	a5,376(s0)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,376(s0)
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,360(s0)
    ttstallwait	32,6
    lw	a3,368(s0)
    lui	a4,0x67113
    add	a5,a5,a3
    addi	a4,a4,-1016 # 67112c08 <__device_print_strings_info_end+0x60c12c08>
    lw	a3,356(s0)
    sw	a5,368(s0)
    sw	a4,0(s1)
    bltu	a5,a3,7458 <.L48>
    lw	a4,352(s0)
    sub	a5,a5,a4
    sw	a5,368(s0)
    li	a0,10
    jal	6b78 <_Z13llk_pop_tileslll.constprop.0>
    li	a0,0
    jal	6b78 <_Z13llk_pop_tileslll.constprop.0>
    lhu	a3,184(s0)
    lui	a4,0xffb45
    lw	a5,40(a4) # ffb45028 <__stack_base+0x447f8>
    zext.h	a5,a5
    beq	a3,a5,7470 <.L49>
    li	a7,4
    li	a5,16
    mv	a2,a7
    mv	a6,a7
    mv	a3,a7
    li	a1,0
    lw	s2,168(s0)
    mv	a4,a5
    li	a0,0
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lui	s6,0x1000
    lui	s7,0x45000
    slli	a5,s2,0x8
    addi	s6,s6,-256 # ffff00 <.LASF497+0xff527e>
    and	a5,a5,s6
    addi	a4,s7,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a4,a5,a4
    sw	a4,0(s1)
    addi	a4,s7,74
    add	a5,a5,a4
    sw	a5,0(s1)
    li	a0,4
    jal	6ff4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lui	s10,0xffe80
    li	a0,4
    jal	6ff4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lui	s4,0x42008
    lw	a0,176(s0)
    li	a2,4
    addi	a0,a0,-1
    li	a1,0
    jal	6c0c <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    addi	s9,s7,8
    li	a0,5
    jal	6b78 <_Z13llk_pop_tileslll.constprop.0>
    addi	s2,s10,8 # ffe80008 <__instrn_buffer+0x40008>
    lui	a5,0xb4010
    lui	t3,0x43800
    addi	s5,a5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    li	a5,63
    addi	s4,s4,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    addi	s11,t3,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a5,4(sp)
    lhu	a3,24(s0)
    lui	a4,0xffb40
    lw	a5,40(a4) # ffb40028 <__stack_base+0x3f7f8>
    zext.h	a5,a5
    beq	a5,a3,7530 <.L50>
    li	a3,5
    lw	t5,8(s0)
    li	a7,4
    li	a5,16
    mv	a4,a5
    mv	a6,a7
    mv	a2,a3
    mv	a1,a3
    mv	a0,a3
    sw	t5,8(sp)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lw	t5,8(sp)
    addi	a4,s7,72
    slli	a5,t5,0x8
    and	a5,a5,s6
    add	a4,a5,a4
    sw	a4,0(s1)
    addi	a4,s7,74
    add	a5,a5,a4
    sw	a5,0(s1)
    sw	s5,0(s1)
    ttsetadcxx	1,255,0
    li	a3,0
    mv	a5,a3
    sw	a5,0(s2)
    lw	a5,0(s2)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a1,4
    sw	a1,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a2,1
    sw	a2,4(a5)
    sw	s4,8(a5)
    lui	a4,0x2000
    sw	a4,12(a5)
    sw	a4,16(a5)
    sw	s11,20(a5)
    sw	a4,24(a5)
    sw	s11,28(a5)
    sw	s11,32(a5)
    sw	s5,0(s1)
    ttsetadcxx	1,255,0
    sw	a3,0(s2)
    lw	a3,0(s2)
    and	zero,zero,a3
    sw	a1,0(a5)
    sw	a2,4(a5)
    sw	s4,8(a5)
    sw	a4,12(a5)
    sw	a4,16(a5)
    sw	s11,20(a5)
    sw	a4,24(a5)
    lw	a3,16(s0)
    sw	s11,28(a5)
    sw	s11,32(a5)
    addi	a3,a3,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a4,0xffef0
    bnez	a5,7630 <.LBB4392+0x10>
    j	8788 <.L117>
    addi	a2,a4,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a4,a4,1204
    lw	a5,52(s10)
    andi	a5,a5,254
    bnez	a5,7638 <.L52>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,7650 <.L53>
    mv	a4,a2
    sw	a3,0(a4)
    sw	zero,52(s10)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a4,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a3,a5,a4
    sw	a3,48(gp) # ffb00820 <unp_cfg_context>
    bne	a4,a5,767c <.LM1137>
    j	8780 <.L158>
    ttsetc16	41,257
    lhu	a3,344(s0)
    lui	a4,0xffb4a
    lw	a5,40(a4) # ffb4a028 <__stack_base+0x497f8>
    zext.h	a5,a5
    beq	a5,a3,7688 <.L56>
    li	a7,4
    lw	t5,360(s0)
    li	a5,16
    mv	a3,a7
    mv	a4,a5
    mv	a6,a7
    mv	a2,a7
    li	a1,0
    li	a0,0
    sw	t5,8(sp)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lw	t5,8(sp)
    addi	a4,s7,72
    slli	a5,t5,0x8
    and	a5,a5,s6
    add	a4,a5,a4
    addi	a3,s7,74
    sw	a4,0(s1)
    add	a5,a5,a3
    sw	a5,0(s1)
    sw	s5,0(s1)
    ttsetadcxx	1,255,0
    li	a5,0
    sw	a5,0(s2)
    lw	a5,0(s2)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,4
    sw	a4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a4,1
    sw	a4,4(a5)
    sw	s4,8(a5)
    lui	a4,0x2000
    sw	a4,12(a5)
    sw	a4,16(a5)
    sw	s11,20(a5)
    sw	a4,24(a5)
    sw	s11,28(a5)
    sw	s11,32(a5)
    lhu	a3,376(s0)
    lui	a4,0xffb4b
    lw	a5,40(a4) # ffb4b028 <__stack_base+0x4a7f8>
    zext.h	a5,a5
    beq	a5,a3,7738 <.L57>
    li	a7,4
    lw	t5,328(s0)
    li	a5,16
    mv	a4,a5
    mv	a6,a7
    mv	a3,a7
    mv	a2,a7
    li	a1,0
    li	a0,0
    sw	t5,8(sp)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lw	t5,8(sp)
    addi	a4,s7,72
    slli	a5,t5,0x8
    and	a5,a5,s6
    add	a4,a5,a4
    sw	a4,0(s1)
    addi	a4,s7,74
    add	a5,a5,a4
    sw	a5,0(s1)
    sw	s5,0(s1)
    ttsetadcxx	1,255,0
    li	a3,0
    mv	a5,a3
    sw	a5,0(s2)
    lw	a5,0(s2)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a0,4
    sw	a0,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a2,1
    sw	a2,4(a5)
    sw	s4,8(a5)
    lui	a4,0x2000
    sw	a4,12(a5)
    sw	a4,16(a5)
    sw	s11,20(a5)
    sw	a4,24(a5)
    sw	s11,28(a5)
    lui	a1,0xb4010
    sw	s11,32(a5)
    addi	a1,a1,328 # b4010148 <__device_print_strings_info_end+0xadb10148>
    sw	a1,0(s1)
    ttsetadcxx	1,255,0
    ttsetadcxx	2,15,0
    ttreplay	0,2,0,1
    ttunpacr	0,1,0,0,0,1,1,0,0,0,0,0,1
    ttunpacr	1,1,0,0,0,1,1,0,0,0,0,0,1
    sw	a3,0(s2)
    lw	a3,0(s2)
    and	zero,zero,a3
    sw	a2,0(a5)
    sw	a0,4(a5)
    sw	a4,8(a5)
    sw	a4,12(a5)
    lui	a3,0x4000
    sw	a4,16(a5)
    addi	a3,a3,32 # 4000020 <.LASF497+0x3ff539e>
    sw	a3,20(a5)
    sw	a4,24(a5)
    lw	a2,336(s0)
    lw	a4,368(s0)
    sw	a3,28(a5)
    sw	a3,32(a5)
    addi	a2,a2,-1
    addi	a3,a4,-1 # 1ffffff <.LASF497+0x1ff537d>
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a4,0xffef0
    beqz	a5,7860 <.L59>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lw	a5,52(s10)
    andi	a5,a5,254
    bnez	a5,7860 <.L59>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,871c <.L60>
    sw	a2,304(a4)
    sw	a3,496(a4)
    sw	zero,52(s10)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lhu	a5,376(s0)
    lw	a4,360(s0)
    addi	a5,a5,1
    zext.h	a5,a5
    slli	a3,a5,0x8
    add	a3,a3,s9
    sh	a5,376(s0)
    sw	a3,0(s1)
    ttstallwait	32,6
    lw	a5,368(s0)
    lui	a3,0x67113
    add	a5,a4,a5
    sw	a5,368(s0)
    addi	a4,a3,-1016 # 67112c08 <__device_print_strings_info_end+0x60c12c08>
    lw	a3,356(s0)
    sw	a4,0(s1)
    bltu	a5,a3,78e8 <.L63>
    lw	a4,352(s0)
    sub	a5,a5,a4
    sw	a5,368(s0)
    lhu	a5,344(s0)
    lw	a4,328(s0)
    addi	a5,a5,1
    zext.h	a5,a5
    slli	a3,a5,0x8
    add	a3,a3,s9
    sh	a5,344(s0)
    sw	a3,0(s1)
    ttstallwait	32,6
    lw	a5,336(s0)
    lui	a3,0x67113
    add	a5,a4,a5
    sw	a5,336(s0)
    addi	a4,a3,-2040 # 67112808 <__device_print_strings_info_end+0x60c12808>
    lw	a3,324(s0)
    sw	a4,0(s1)
    bltu	a5,a3,7938 <.L64>
    lw	a4,320(s0)
    sub	a5,a5,a4
    sw	a5,336(s0)
    lhu	a5,24(s0)
    lw	a4,8(s0)
    addi	a5,a5,1
    zext.h	a5,a5
    slli	a3,a5,0x8
    add	a3,a3,s9
    sh	a5,24(s0)
    sw	a3,0(s1)
    ttstallwait	32,6
    lw	a5,16(s0)
    lui	a3,0x67110
    add	a5,a4,a5
    sw	a5,16(s0)
    addi	a4,a3,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    lw	a3,4(s0)
    sw	a4,0(s1)
    bltu	a5,a3,7988 <.L65>
    lw	a4,0(s0)
    sub	a5,a5,a4
    sw	a5,16(s0)
    lhu	a3,184(s0)
    lui	a4,0xffb45
    lw	a5,40(a4) # ffb45028 <__stack_base+0x447f8>
    zext.h	a5,a5
    beq	a5,a3,7990 <.L66>
    lhu	a3,216(s0)
    lui	a4,0xffb46
    lw	a5,40(a4) # ffb46028 <__stack_base+0x457f8>
    zext.h	a5,a5
    beq	a5,a3,79a4 <.L67>
    li	a7,4
    lw	t6,200(s0)
    lw	t5,168(s0)
    li	a5,16
    mv	a4,a5
    mv	a6,a7
    mv	a3,a7
    mv	a2,a7
    li	a1,0
    li	a0,0
    sw	t6,12(sp)
    sw	t5,8(sp)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lw	t6,12(sp)
    lw	t5,8(sp)
    slli	t6,t6,0x8
    addi	a5,s7,72
    and	t6,t6,s6
    slli	t5,t5,0x8
    add	t6,t6,a5
    and	t5,t5,s6
    addi	a5,s7,74
    sw	t6,0(s1)
    add	t5,t5,a5
    sw	t5,0(s1)
    sw	s5,0(s1)
    ttsetadcxx	3,255,0
    li	a2,0
    mv	a5,a2
    sw	a5,0(s2)
    lw	a5,0(s2)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a1,2
    sw	a1,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    sw	a1,4(a5)
    lui	a3,0x2000
    sw	a3,8(a5)
    sw	a3,12(a5)
    sw	a3,16(a5)
    lui	a4,0x42808
    sw	s4,20(a5)
    addi	a4,a4,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    sw	a4,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    sw	s5,0(s1)
    ttsetadcxx	3,255,0
    sw	a2,0(s2)
    lw	a2,0(s2)
    and	zero,zero,a2
    sw	a1,0(a5)
    sw	a1,4(a5)
    sw	a3,8(a5)
    sw	a3,12(a5)
    sw	a3,16(a5)
    sw	s4,20(a5)
    sw	a4,24(a5)
    lw	a2,208(s0)
    lw	a3,176(s0)
    sw	a4,28(a5)
    sw	a4,32(a5)
    addi	a2,a2,-1
    addi	a3,a3,-1 # 1ffffff <.LASF497+0x1ff537d>
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a4,0xffef0
    beqz	a5,7ac4 <.L69>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lw	a5,52(s10)
    andi	a5,a5,254
    bnez	a5,7ac4 <.L69>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,86ec <.L70>
    sw	a2,304(a4)
    sw	a3,496(a4)
    sw	zero,52(s10)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lhu	a5,216(s0)
    lw	t5,200(s0)
    addi	a5,a5,1
    zext.h	a5,a5
    slli	a4,a5,0x8
    add	a4,a4,s9
    sw	a4,0(s1)
    sh	a5,216(s0)
    ttstallwait	32,6
    lui	a3,0x67112
    lw	a4,208(s0)
    addi	a3,a3,-2040 # 67111808 <__device_print_strings_info_end+0x60c11808>
    lw	a2,196(s0)
    add	a4,t5,a4
    sw	a3,0(s1)
    sw	a4,208(s0)
    bltu	a4,a2,7b4c <.L73>
    lw	a3,192(s0)
    sub	a4,a4,a3
    sw	a4,208(s0)
    lhu	a4,184(s0)
    lw	a3,168(s0)
    addi	a4,a4,1
    zext.h	a4,a4
    slli	a2,a4,0x8
    add	a2,a2,s9
    sh	a4,184(s0)
    sw	a2,0(s1)
    ttstallwait	32,6
    lw	a4,176(s0)
    lui	a2,0x67111
    add	a4,a3,a4
    sw	a4,176(s0)
    addi	a3,a2,1032 # 67111408 <__device_print_strings_info_end+0x60c11408>
    lw	a2,164(s0)
    sw	a3,0(s1)
    bltu	a4,a2,7b9c <.L74>
    lw	a3,160(s0)
    sub	a4,a4,a3
    sw	a4,176(s0)
    lw	a4,4(sp)
    addi	a4,a4,-1
    sw	a4,4(sp)
    bnez	a4,7528 <.L75>
    lui	a3,0xffb46
    lw	a4,40(a3) # ffb46028 <__stack_base+0x457f8>
    zext.h	a4,a4
    beq	a4,a5,7bb0 <.L76>
    li	a7,4
    li	a5,16
    mv	a6,a7
    mv	a3,a7
    mv	a2,a7
    mv	a4,a5
    li	a1,0
    li	a0,0
    sw	t5,4(sp)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lw	t5,4(sp)
    lui	s6,0x1000
    slli	a5,t5,0x8
    addi	s6,s6,-256 # ffff00 <.LASF497+0xff527e>
    lui	s4,0x45000
    and	a5,a5,s6
    addi	s5,s4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a4,a5,s5
    addi	s4,s4,74
    sw	a4,0(s1)
    add	a5,a5,s4
    sw	a5,0(s1)
    li	a0,4
    jal	6ff4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lw	s2,200(s0)
    li	a7,4
    li	a5,16
    mv	a4,a5
    mv	a6,a7
    mv	a3,a7
    mv	a2,a7
    li	a1,0
    li	a0,0
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    slli	a5,s2,0x8
    and	a5,a5,s6
    add	s5,a5,s5
    sw	s5,0(s1)
    add	a5,a5,s4
    sw	a5,0(s1)
    lui	a5,0xb4010
    addi	a5,a5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a5,0(s1)
    ttsetadcxx	2,255,0
    lui	a4,0xffe80
    li	a5,0
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,1
    sw	a4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    sw	a4,4(a5)
    lui	a4,0x43000
    addi	a4,a4,257 # 43000101 <__device_print_strings_info_end+0x3cb00101>
    lui	a3,0x42808
    sw	a4,8(a5)
    addi	a3,a3,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    sw	a3,12(a5)
    lui	a4,0x2000
    sw	a4,16(a5)
    lui	a4,0x54400
    sw	a3,20(a5)
    addi	a4,a4,129 # 54400081 <__device_print_strings_info_end+0x4df00081>
    lw	a2,208(s0)
    sw	a4,24(a5)
    sw	a4,28(a5)
    addi	a2,a2,-1
    sw	a4,32(a5)
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,87d0 <.L120>
    addi	a1,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7cf0 <.L78>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,7d08 <.L79>
    mv	a3,a1
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a4,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a3,a5,a4
    sw	a3,48(gp) # ffb00820 <unp_cfg_context>
    beq	a4,a5,87c8 <.L159>
    ttsetc16	41,257
    li	a0,0
    jal	6ff4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lw	a0,80(s0)
    li	a2,0
    addi	a0,a0,-1
    li	a1,0
    jal	6c0c <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    li	a0,6
    jal	6b78 <_Z13llk_pop_tileslll.constprop.0>
    lhu	a3,248(s0)
    lui	a4,0xffb47
    lw	a5,40(a4) # ffb47028 <__stack_base+0x467f8>
    zext.h	a5,a5
    beq	a5,a3,7d64 <.L82>
    li	a7,4
    li	a5,16
    mv	a6,a7
    mv	a4,a5
    li	a2,0
    li	a1,0
    li	a3,0
    li	a0,0
    lw	s2,232(s0)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lui	a4,0x1000
    slli	a5,s2,0x8
    addi	a4,a4,-256 # ffff00 <.LASF497+0xff527e>
    and	a5,a5,a4
    lui	a4,0x45000
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    add	a5,a5,a4
    sw	a3,0(s1)
    sw	a5,0(s1)
    li	a0,0
    jal	6ff4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lui	a5,0xb4010
    addi	a5,a5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a5,0(s1)
    ttsetadcxx	1,255,0
    lui	a4,0xffe80
    li	a5,0
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,4
    sw	a4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a4,1
    sw	a4,4(a5)
    lui	a3,0x2000
    sw	a3,8(a5)
    sw	a3,12(a5)
    lui	a4,0x42088
    sw	a3,16(a5)
    addi	a4,a4,129 # 42088081 <__device_print_strings_info_end+0x3bb88081>
    sw	a4,20(a5)
    sw	a3,24(a5)
    lw	a0,240(s0)
    sw	a4,28(a5)
    sw	a4,32(a5)
    addi	a0,a0,-1
    li	a2,0
    li	a1,0
    jal	6c0c <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    li	a0,7
    jal	6b78 <_Z13llk_pop_tileslll.constprop.0>
    lhu	a3,280(s0)
    lui	a4,0xffb48
    lw	a5,40(a4) # ffb48028 <__stack_base+0x477f8>
    zext.h	a5,a5
    beq	a5,a3,7e54 <.L83>
    lui	s5,0x1000
    lui	s10,0xb4010
    lui	s2,0xffe80
    lui	t1,0x42008
    li	a5,64
    lui	s6,0x45000
    addi	s5,s5,-256 # ffff00 <.LASF497+0xff527e>
    addi	s10,s10,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    addi	s11,s2,8 # ffe80008 <__instrn_buffer+0x40008>
    addi	s7,t1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a5,4(sp)
    li	s4,4
    li	s9,1
    lhu	a3,24(s0)
    lui	a4,0xffb40
    lw	a5,40(a4) # ffb40028 <__stack_base+0x3f7f8>
    zext.h	a5,a5
    beq	a5,a3,7e9c <.L84>
    lhu	a3,56(s0)
    lui	a4,0xffb41
    lw	a5,40(a4) # ffb41028 <__stack_base+0x407f8>
    zext.h	a5,a5
    beq	a5,a3,7eb0 <.L85>
    li	a3,5
    lw	t4,8(s0)
    li	a7,4
    li	a5,16
    mv	a4,a5
    mv	a6,a7
    mv	a2,a3
    mv	a1,a3
    mv	a0,a3
    sw	t4,8(sp)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lw	t4,8(sp)
    addi	a4,s6,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    slli	a5,t4,0x8
    and	a5,a5,s5
    add	a4,a5,a4
    sw	a4,0(s1)
    addi	a4,s6,74
    add	a5,a5,a4
    sw	a5,0(s1)
    sw	s10,0(s1)
    ttsetadcxx	1,255,0
    li	a2,0
    mv	a5,a2
    sw	a5,0(s11)
    lw	a5,0(s11)
    and	zero,zero,a5
    lui	a5,0xffb80
    sw	s4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    sw	s9,4(a5)
    sw	s7,8(a5)
    lui	a3,0x2000
    sw	a3,12(a5)
    lui	a4,0x43800
    sw	a3,16(a5)
    addi	a4,a4,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a4,20(a5)
    sw	a3,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    sw	s10,0(s1)
    ttsetadcxx	1,255,0
    sw	a2,0(s11)
    lw	a2,0(s11)
    and	zero,zero,a2
    sw	s4,0(a5)
    sw	s9,4(a5)
    sw	s7,8(a5)
    sw	a3,12(a5)
    sw	a3,16(a5)
    sw	a4,20(a5)
    sw	a3,24(a5)
    lw	a3,16(s0)
    sw	a4,28(a5)
    sw	a4,32(a5)
    addi	a3,a3,-1 # 1ffffff <.LASF497+0x1ff537d>
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a4,0xffef0
    beqz	a5,874c <.L121>
    addi	a2,a4,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a4,a4,1204
    lw	a5,52(s2)
    andi	a5,a5,254
    bnez	a5,7fb4 <.L87>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,7fcc <.L88>
    mv	a4,a2
    sw	a3,0(a4)
    sw	zero,52(s2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    sub	a4,s9,a5
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    beq	a5,s9,8778 <.L160>
    ttsetc16	41,257
    li	a3,5
    lw	t4,40(s0)
    li	a7,4
    li	a5,16
    mv	a4,a5
    mv	a6,a7
    mv	a2,a3
    mv	a1,a3
    mv	a0,a3
    sw	t4,8(sp)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lw	t4,8(sp)
    addi	a4,s6,72
    slli	a5,t4,0x8
    and	a5,a5,s5
    add	a4,a5,a4
    sw	a4,0(s1)
    addi	a4,s6,74
    add	a5,a5,a4
    sw	a5,0(s1)
    sw	s10,0(s1)
    ttsetadcxx	1,255,0
    li	a2,0
    mv	a5,a2
    sw	a5,0(s11)
    lw	a5,0(s11)
    and	zero,zero,a5
    lui	a5,0xffb80
    sw	s4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    sw	s9,4(a5)
    sw	s7,8(a5)
    lui	a3,0x2000
    sw	a3,12(a5)
    lui	a4,0x43800
    sw	a3,16(a5)
    addi	a4,a4,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a4,20(a5)
    sw	a3,24(a5)
    sw	a4,28(a5)
    sw	a4,32(a5)
    sw	s10,0(s1)
    ttsetadcxx	1,255,0
    sw	a2,0(s11)
    lw	a2,0(s11)
    and	zero,zero,a2
    sw	s4,0(a5)
    sw	s9,4(a5)
    sw	s7,8(a5)
    sw	a3,12(a5)
    sw	a3,16(a5)
    sw	a4,20(a5)
    sw	a3,24(a5)
    lw	a3,48(s0)
    sw	a4,28(a5)
    sw	a4,32(a5)
    addi	a3,a3,-1 # 1ffffff <.LASF497+0x1ff537d>
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a4,0xffef0
    beqz	a5,876c <.L122>
    addi	a2,a4,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a4,a4,1204
    lw	a5,52(s2)
    andi	a5,a5,254
    bnez	a5,80ec <.L92>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,8104 <.L93>
    mv	a4,a2
    sw	a3,0(a4)
    sw	zero,52(s2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    sub	a4,s9,a5
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    beq	a5,s9,8764 <.L161>
    ttsetc16	41,257
    lhu	a5,56(s0)
    lui	a2,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a2,a2,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a5,0x8
    add	a3,a3,a2
    sh	a5,56(s0)
    lw	a4,40(s0)
    sw	a3,0(s1)
    ttstallwait	32,6
    lw	a5,48(s0)
    lui	a3,0x67110
    add	a5,a4,a5
    sw	a5,48(s0)
    addi	a4,a3,1032 # 67110408 <__device_print_strings_info_end+0x60c10408>
    lw	a3,36(s0)
    sw	a4,0(s1)
    bltu	a5,a3,8184 <.L96>
    lw	a4,32(s0)
    sub	a5,a5,a4
    sw	a5,48(s0)
    lhu	a5,24(s0)
    lui	a2,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a2,a2,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a5,0x8
    add	a3,a3,a2
    sh	a5,24(s0)
    lw	a4,8(s0)
    sw	a3,0(s1)
    ttstallwait	32,6
    lw	a5,16(s0)
    lui	a3,0x67110
    add	a5,a4,a5
    sw	a5,16(s0)
    addi	a4,a3,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    lw	a3,4(s0)
    sw	a4,0(s1)
    bltu	a5,a3,81dc <.L97>
    lw	a4,0(s0)
    sub	a5,a5,a4
    sw	a5,16(s0)
    lhu	a3,120(s0)
    lui	a4,0xffb43
    lw	a5,40(a4) # ffb43028 <__stack_base+0x427f8>
    zext.h	a5,a5
    beq	a5,a3,81e4 <.L98>
    lhu	a3,152(s0)
    lui	a4,0xffb44
    lw	a5,40(a4) # ffb44028 <__stack_base+0x437f8>
    zext.h	a5,a5
    beq	a5,a3,81f8 <.L99>
    li	a7,4
    lw	t5,104(s0)
    lw	t4,264(s0)
    li	a5,16
    mv	a4,a5
    mv	a6,a7
    mv	a3,a7
    mv	a2,a7
    li	a1,0
    li	a0,0
    sw	t5,12(sp)
    sw	t4,8(sp)
    jal	6dc4 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lw	t5,12(sp)
    lw	t4,8(sp)
    slli	t5,t5,0x8
    addi	a5,s6,72
    and	t5,t5,s5
    slli	t4,t4,0x8
    add	t5,t5,a5
    and	t4,t4,s5
    addi	a5,s6,74
    sw	t5,0(s1)
    add	t4,t4,a5
    sw	t4,0(s1)
    sw	s10,0(s1)
    ttsetadcxx	3,255,0
    li	a3,0
    mv	a5,a3
    sw	a5,0(s11)
    lw	a5,0(s11)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,2
    sw	a4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    sw	a4,4(a5)
    lui	a4,0x2000
    sw	a4,8(a5)
    sw	a4,12(a5)
    sw	a4,16(a5)
    lui	a2,0x42808
    sw	s7,20(a5)
    addi	a2,a2,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    sw	a2,24(a5)
    sw	a2,28(a5)
    sw	a2,32(a5)
    sw	s10,0(s1)
    ttsetadcxx	1,255,0
    sw	a3,0(s11)
    lw	a3,0(s11)
    and	zero,zero,a3
    sw	s4,0(a5)
    sw	s9,4(a5)
    sw	a4,8(a5)
    sw	a4,12(a5)
    lui	a3,0x42088
    sw	a4,16(a5)
    addi	a3,a3,129 # 42088081 <__device_print_strings_info_end+0x3bb88081>
    sw	a3,20(a5)
    sw	a4,24(a5)
    lw	a4,144(s0)
    sw	a3,28(a5)
    sw	a3,32(a5)
    addi	a3,a4,-1 # 1ffffff <.LASF497+0x1ff537d>
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a4,0xffef0
    beqz	a5,8758 <.L123>
    addi	a2,a4,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a4,a4,1204
    lw	a5,52(s2)
    andi	a5,a5,254
    bnez	a5,831c <.L101>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,8334 <.L102>
    mv	a4,a2
    sw	a3,0(a4)
    sw	zero,52(s2)
    lui	a5,0xffec2
    lw	a5,0(a5) # ffec2000 <__instrn_buffer+0x82000>
    addi	a5,a5,4
    slli	a2,a5,0x4
    ttsetc16	5,0
    ttrdcfg	52,57
    lui	a4,0x45040
    addi	a4,a4,36 # 45040024 <__device_print_strings_info_end+0x3eb40024>
    sw	a4,0(s1)
    ttwrcfg	18,0,57
    lui	a4,0x10
    lw	a3,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a4,a4,-256 # ff00 <.LASF497+0x527e>
    zext.h	a5,a5
    and	a4,a2,a4
    bnez	a3,8670 <.L103>
    lui	a1,0xb3101
    lui	a3,0xb3ff0
    addi	a1,a1,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a3,a3,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a2,0xb4ff0
    sw	a1,0(s1)
    add	a5,a5,a3
    addi	a3,a2,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s1)
    add	a5,a4,a3
    sw	a5,0(s1)
    ttsemwait	8,4,2
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    ttstallwait	2,2
    ttsempost	4
    ttwrcfg	52,0,57
    lui	a4,0xb3100
    addi	a4,a4,73 # b3100049 <__device_print_strings_info_end+0xacc00049>
    lui	a5,0xb3ff4
    sw	a4,0(s1)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s1)
    sw	a3,0(s1)
    ttsetc16	5,4
    sw	s9,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    sw	s10,0(s1)
    ttsetadcxx	3,255,0
    li	a5,0
    sw	a5,0(s11)
    lw	a5,0(s11)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,2
    sw	a4,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    sw	a4,4(a5)
    lui	a4,0x2000
    sw	a4,8(a5)
    sw	a4,12(a5)
    sw	a4,16(a5)
    lui	a4,0x42808
    sw	s7,20(a5)
    addi	a4,a4,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    lw	a2,112(s0)
    lw	a3,272(s0)
    sw	a4,24(a5)
    sw	a4,28(a5)
    addi	a2,a2,-1
    addi	a3,a3,-1
    sw	a4,32(a5)
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a4,0xffef0
    beqz	a5,8464 <.L107>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lw	a5,52(s2)
    andi	a5,a5,254
    bnez	a5,8464 <.L107>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,8644 <.L108>
    sw	a2,304(a4)
    sw	a3,496(a4)
    sw	zero,52(s2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    sw	s9,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lhu	a5,152(s0)
    lui	a2,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a2,a2,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a5,0x8
    add	a3,a3,a2
    sh	a5,152(s0)
    lw	a4,136(s0)
    sw	a3,0(s1)
    ttstallwait	32,6
    lw	a5,144(s0)
    lui	a3,0x67111
    add	a5,a4,a5
    sw	a5,144(s0)
    addi	a4,a3,8 # 67111008 <__device_print_strings_info_end+0x60c11008>
    lw	a3,132(s0)
    sw	a4,0(s1)
    bltu	a5,a3,84f0 <.L111>
    lw	a4,128(s0)
    sub	a5,a5,a4
    sw	a5,144(s0)
    lhu	a5,120(s0)
    lui	a2,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a2,a2,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a5,0x8
    add	a3,a3,a2
    sh	a5,120(s0)
    lw	a4,104(s0)
    sw	a3,0(s1)
    ttstallwait	32,6
    lw	a5,112(s0)
    lui	a3,0x67111
    add	a5,a4,a5
    sw	a5,112(s0)
    addi	a4,a3,-1016 # 67110c08 <__device_print_strings_info_end+0x60c10c08>
    lw	a3,100(s0)
    sw	a4,0(s1)
    bltu	a5,a3,8548 <.L112>
    lw	a4,96(s0)
    sub	a5,a5,a4
    sw	a5,112(s0)
    lw	a5,4(sp)
    addi	a5,a5,-1
    sw	a5,4(sp)
    bnez	a5,7e94 <.L113>
    lhu	a5,280(s0)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,280(s0)
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,264(s0)
    ttstallwait	32,6
    lw	a3,272(s0)
    lui	a4,0x67112
    add	a5,a5,a3
    addi	a4,a4,8 # 67112008 <__device_print_strings_info_end+0x60c12008>
    lw	a3,260(s0)
    sw	a5,272(s0)
    sw	a4,0(s1)
    bltu	a5,a3,85b0 <.L114>
    lw	a4,256(s0)
    sub	a5,a5,a4
    sw	a5,272(s0)
    lhu	a5,88(s0)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,88(s0)
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,72(s0)
    ttstallwait	32,6
    lw	a3,80(s0)
    lui	a4,0x67111
    add	a5,a5,a3
    addi	a4,a4,-2040 # 67110808 <__device_print_strings_info_end+0x60c10808>
    lw	a3,68(s0)
    sw	a5,80(s0)
    sw	a4,0(s1)
    bltu	a5,a3,8608 <.L38>
    lw	a4,64(s0)
    sub	a5,a5,a4
    sw	a5,80(s0)
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
    addi	sp,sp,80
    ret
    sw	a2,308(a4)
    sw	a3,500(a4)
    sw	zero,52(s2)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    sub	a4,s9,a5
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a5,s9,8494 <.L109>
    ttsetc16	41,0
    j	8498 <.L110>
    lui	a0,0xb3202
    lui	a1,0xb5ff0
    addi	a0,a0,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a1,a1,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a2,0xb6ff0
    sw	a0,0(s1)
    add	a5,a5,a1
    addi	a2,a2,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s1)
    add	a5,a4,a2
    sw	a5,0(s1)
    ttsemwait	8,4,2
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    ttstallwait	2,2
    ttsempost	4
    ttwrcfg	52,0,57
    lui	a4,0xb3200
    addi	a4,a4,73 # b3200049 <__device_print_strings_info_end+0xacd00049>
    lui	a5,0xb5ff4
    sw	a4,0(s1)
    addi	a5,a5,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a5,0(s1)
    sw	a2,0(s1)
    ttsetc16	5,4
    sub	a5,s9,a3
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bne	a3,s9,83ec <.L104>
    ttsetc16	41,0
    j	83f0 <.L105>
    sw	a2,308(a4)
    sw	a3,500(a4)
    sw	zero,52(s10)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a4,1
    sub	a3,a4,a5
    sw	a3,48(gp) # ffb00820 <unp_cfg_context>
    bne	a5,a4,7af8 <.L71>
    ttsetc16	41,0
    j	7afc <.L72>
    sw	a2,308(a4)
    sw	a3,500(a4)
    sw	zero,52(s10)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a4,1
    sub	a3,a4,a5
    sw	a3,48(gp) # ffb00820 <unp_cfg_context>
    bne	a5,a4,7894 <.L61>
    ttsetc16	41,0
    j	7898 <.L62>
    addi	a2,a4,304
    addi	a4,a4,308
    j	7fb4 <.L87>
    addi	a2,a4,304
    addi	a4,a4,308
    j	831c <.L101>
    ttsetc16	41,0
    j	812c <.L95>
    addi	a2,a4,304
    addi	a4,a4,308
    j	80ec <.L92>
    ttsetc16	41,0
    j	7ff4 <.L90>
    ttsetc16	41,0
    j	7680 <.L55>
    addi	a2,a4,304
    addi	a4,a4,308
    j	7638 <.L52>
    sw	a1,308(a3)
    sw	a2,500(a3)
    sw	zero,52(a4)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a4,1
    sub	a3,a4,a5
    sw	a3,48(gp) # ffb00820 <unp_cfg_context>
    beq	a5,a4,87c0 <.LM2967>
    j	73fc <.L46>
    ttsetc16	41,0
    j	7400 <.L47>
    ttsetc16	41,0
    j	7d38 <.L81>
    addi	a1,a3,496
    addi	a3,a3,500
    j	7cec <.L77>
