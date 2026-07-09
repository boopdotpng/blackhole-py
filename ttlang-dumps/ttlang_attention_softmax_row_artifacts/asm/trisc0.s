    addi	sp,sp,-16
    sw	ra,12(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__stack_base>
    addi	a4,a4,-2012 # ffb00824 <__ldm_bss_end>
    bltu	a4,a5,6aa4 <.L213>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,6a8c <.L214>
    addi	a3,a5,-8
    bltu	a4,a3,6b70 <.L225>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6ac0 <.L216>
    sw	zero,-8(a5)
    auipc	a4,0x2
    addi	a4,a4,20 # 8ad4 <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <unp_cfg_context>
    beq	a4,a5,6b2c <.L218>
    addi	a2,gp,48 # ffb00820 <unp_cfg_context>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6b10 <.L219>
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
    blt	a6,a3,6ae8 <.L220>
    blez	a3,6b2c <.L218>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6b2c <.L218>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb12
    sw	zero,104(a5) # ffb12068 <__stack_base+0x11838>
    lw	a4,1312(zero) # 520 <.LASF1113+0x2>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,6b58 <.L222>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,6b4c <.L223>
    ttzerosrc	0,0,1,3
    jal	6f60 <_Z11kernel_mainv>
    lw	ra,12(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	6ab4 <.L215>
    addi	sp,sp,-48
    lui	t3,0xffe80
    lw	t1,52(t3) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	t1,t1
    bnez	t1,6b80 <.L2>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	t3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	t1,0xffef0
    beqz	t3,6ba4 <.L3>
    addi	t1,t1,896 # ffef0380 <__instrn_buffer+0xb0380>
    andi	t3,a2,3
    li	t5,1024
    beqz	t3,6bc4 <.L4>
    addi	t3,t3,-1
    snez	t3,t3
    neg	t3,t3
    andi	t5,t3,-256
    addi	t5,t5,512
    andi	t3,a3,3
    li	t4,1024
    beqz	t3,6be4 <.L5>
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
    addi	a2,a2,15 # f000f <.LASF490+0xe573d>
    andi	a3,a3,15
    andi	a5,a5,-16
    or	a5,a5,a3
    sw	a2,292(t1)
    sw	a5,32(sp)
    sw	a5,480(t1)
    sw	a2,484(t1)
    lui	a5,0x400
    addi	a5,a5,64 # 400040 <.LASF490+0x3f576e>
    bnez	a4,6d34 <.L6>
    lui	a5,0x1600
    addi	a5,a5,352 # 1600160 <.LASF490+0x15f588e>
    lui	a3,0x100
    addi	a3,a3,16 # 100010 <.LASF490+0xf573e>
    sw	a5,336(t1)
    mul	a4,a4,a3
    lui	a2,0x1000
    sw	a4,344(t1)
    lui	a5,0xffe00
    addi	a2,a2,256 # 1000100 <.LASF490+0xff582e>
    lui	a4,0x800
    sw	a2,160(a5) # ffe000a0 <__stack_base+0x2ff870>
    addi	a4,a4,128 # 800080 <.LASF490+0x7f57ae>
    lui	a2,0x400
    sw	a4,164(a5)
    addi	a2,a2,64 # 400040 <.LASF490+0x3f576e>
    lui	a4,0x200
    sw	a2,168(a5)
    addi	a4,a4,32 # 200020 <.LASF490+0x1f574e>
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
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,6e20 <.L29>
    addi	a6,a3,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a3,a3,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6dc4 <.L21>
    lw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a4,6ddc <.L22>
    mv	a3,a6
    sw	a0,0(a3)
    lui	a4,0xffe80
    sw	zero,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a1,a1,7
    lw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a1,6dfc <.L25>
    andi	a2,a2,7
    beqz	a2,6e34 <.L31>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a3,1
    sub	a2,a3,a4
    sw	a2,48(gp) # ffb00820 <unp_cfg_context>
    beq	a4,a3,6e2c <.L32>
    ttsetc16	41,257
    ret
    addi	a6,a3,304
    addi	a3,a3,308
    j	6dc0 <.L20>
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
    addi	a0,a0,-256 # ff00 <.LASF490+0x562e>
    zext.h	a2,a2
    and	a1,a1,a0
    bnez	a4,6ef4 <.L26>
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
    j	6e08 <.L24>
    addi	sp,sp,-80
    sw	s0,72(sp)
    lui	s0,0xffb00
    addi	s0,s0,32 # ffb00020 <cb_interface>
    lhu	a2,24(s0)
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
    lui	a3,0xffb40
    li	a4,3
    lw	a5,40(a3) # ffb40028 <__stack_base+0x3f7f8>
    sub	a5,a5,a2
    zext.h	a5,a5
    bgeu	a4,a5,6fa8 <.L34>
    lhu	a2,56(s0)
    lui	a3,0xffb41
    li	a4,3
    lw	a5,40(a3) # ffb41028 <__stack_base+0x407f8>
    sub	a5,a5,a2
    zext.h	a5,a5
    bgeu	a4,a5,6fc4 <.L35>
    lw	a3,104(s0)
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,6fdc <.L36>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a4,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a4,7000 <.L37>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,1024
    sw	a4,228(a5)
    sw	a4,236(a5)
    ttatgetm	0
    lui	s1,0xffe40
    mv	s1,s1
    lui	a4,0xb3ff0
    sw	a4,0(s1) # ffe40000 <__instrn_buffer>
    lui	a4,0xb47f0
    sw	a4,0(s1)
    lui	a4,0xb3070
    addi	a4,a4,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a4,0(s1)
    lui	a4,0xb4800
    addi	a4,a4,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a4,0(s1)
    lui	a4,0xb5010
    addi	a4,a4,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a4,0(s1)
    lui	a4,0xb5400
    addi	a2,a4,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a2,0(s1)
    addi	a4,a4,119
    sw	a4,0(s1)
    ttatrelm	0
    li	a4,16
    sw	a4,256(a5)
    lui	a4,0x40
    addi	a4,a4,1 # 40001 <.LASF490+0x3572f>
    lui	a2,0x1000
    sw	a4,260(a5)
    addi	a1,a2,16 # 1000010 <.LASF490+0xff573e>
    sw	a1,448(a5)
    sw	a4,452(a5)
    li	a1,36
    lui	a4,0xf0
    sw	a1,288(a5)
    addi	a4,a4,15 # f000f <.LASF490+0xe573d>
    sw	a4,292(a5)
    sw	a1,480(a5)
    lui	a1,0x400
    sw	a4,484(a5)
    addi	a1,a1,64 # 400040 <.LASF490+0x3f576e>
    sw	a1,336(a5)
    addi	a6,a2,256
    sw	a6,344(a5)
    lui	a4,0xffe00
    lui	a0,0x800
    sw	a6,160(a4) # ffe000a0 <__stack_base+0x2ff870>
    addi	a0,a0,128 # 800080 <.LASF490+0x7f57ae>
    sw	a0,164(a4)
    lui	a0,0x200
    sw	a1,168(a4)
    addi	a0,a0,32 # 200020 <.LASF490+0x1f574e>
    lui	a1,0x100
    sw	a0,172(a4)
    addi	a1,a1,16 # 100010 <.LASF490+0xf573e>
    sw	a1,176(a4)
    sw	zero,8(sp)
    lw	a4,176(a4)
    sw	a4,8(sp)
    ttsetc16	5,4
    li	a4,256
    sw	a4,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a4,0x45000
    slli	a5,a3,0x8
    addi	a2,a2,-256
    and	a5,a5,a2
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
    sw	a5,0(s1)
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
    lhu	a3,120(s0)
    sw	a4,28(a5)
    sw	a4,32(a5)
    lui	a4,0xffb43
    lw	a5,40(a4) # ffb43028 <__stack_base+0x427f8>
    zext.h	a5,a5
    beq	a5,a3,71a4 <.L38>
    lw	a3,8(s0)
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,71b8 <.L39>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a4,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a4,71dc <.L40>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,1024
    sw	a4,228(a5)
    sw	a4,236(a5)
    ttatgetm	0
    lui	a4,0xb3ff0
    sw	a4,0(s1)
    lui	a4,0xb47f0
    sw	a4,0(s1)
    lui	a4,0xb3070
    addi	a4,a4,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a4,0(s1)
    lui	a4,0xb4800
    addi	a4,a4,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a4,0(s1)
    lui	a4,0xb5010
    addi	a4,a4,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a4,0(s1)
    lui	a4,0xb5400
    addi	a2,a4,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a2,0(s1)
    addi	a4,a4,119
    sw	a4,0(s1)
    ttatrelm	0
    li	a4,16
    sw	a4,256(a5)
    lui	a4,0x40
    addi	a4,a4,1 # 40001 <.LASF490+0x3572f>
    lui	a2,0x1000
    sw	a4,260(a5)
    addi	a1,a2,16 # 1000010 <.LASF490+0xff573e>
    sw	a1,448(a5)
    sw	a4,452(a5)
    li	a1,36
    lui	a4,0xf0
    sw	a1,288(a5)
    addi	a4,a4,15 # f000f <.LASF490+0xe573d>
    sw	a4,292(a5)
    sw	a1,480(a5)
    lui	a1,0x400
    sw	a4,484(a5)
    addi	a1,a1,64 # 400040 <.LASF490+0x3f576e>
    sw	a1,336(a5)
    addi	a0,a2,256
    sw	a0,344(a5)
    lui	a4,0xffe00
    sw	a0,160(a4) # ffe000a0 <__stack_base+0x2ff870>
    lui	a0,0x800
    addi	a0,a0,128 # 800080 <.LASF490+0x7f57ae>
    sw	a0,164(a4)
    sw	a1,168(a4)
    lui	a1,0x200
    addi	a1,a1,32 # 200020 <.LASF490+0x1f574e>
    sw	a1,172(a4)
    lui	a1,0x100
    addi	a1,a1,16 # 100010 <.LASF490+0xf573e>
    sw	a1,176(a4)
    sw	zero,12(sp)
    lw	a4,176(a4)
    sw	a4,12(sp)
    ttsetc16	5,4
    li	a4,256
    sw	a4,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a4,0x45000
    slli	a5,a3,0x8
    addi	a2,a2,-256
    and	a5,a5,a2
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
    lui	a0,0xb4010
    sw	a5,0(s1)
    addi	a5,a0,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a5,0(s1)
    ttsetadcxx	1,255,0
    li	a3,0
    lui	a1,0xffe80
    addi	a1,a1,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a3
    sw	a5,0(a1)
    lw	a5,0(a1)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a6,4
    sw	a6,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a7,1
    lui	a4,0x42008
    sw	a7,4(a5)
    addi	a4,a4,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a4,8(a5)
    lui	a4,0x2000
    sw	a4,12(a5)
    lui	a2,0x43800
    sw	a4,16(a5)
    addi	a2,a2,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a2,20(a5)
    sw	a4,24(a5)
    sw	a2,28(a5)
    addi	a0,a0,328
    sw	a2,32(a5)
    sw	a0,0(s1)
    ttsetadcxx	1,255,0
    ttsetadcxx	2,15,0
    ttreplay	0,2,0,1
    ttunpacr	0,1,0,0,0,1,1,0,0,0,0,0,1
    ttunpacr	1,1,0,0,0,1,1,0,0,0,0,0,1
    sw	a3,0(a1)
    lw	a3,0(a1)
    and	zero,zero,a3
    sw	a7,0(a5)
    sw	a6,4(a5)
    sw	a4,8(a5)
    sw	a4,12(a5)
    lui	a3,0x4000
    sw	a4,16(a5)
    addi	a3,a3,32 # 4000020 <.LASF490+0x3ff574e>
    sw	a3,20(a5)
    sw	a4,24(a5)
    sw	a3,28(a5)
    sw	a3,32(a5)
    lw	a2,16(s0)
    lw	a7,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    lw	t1,8(s0)
    addi	a2,a2,-1
    addi	a6,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    bnez	a7,73e8 <.L42>
    mv	a6,a5
    lw	a0,48(gp) # ffb00820 <unp_cfg_context>
    li	a1,4
    lui	a4,0xffe80
    li	t3,1
    lw	a3,112(s0)
    addi	a3,a3,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7404 <.L43>
    beqz	a0,7418 <.LM812>
    j	8920 <.L44>
    sw	a2,304(a6)
    sw	a3,496(a6)
    sw	zero,52(a4)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a0,1
    ttsetc16	41,257
    addi	a1,a1,-1
    add	a2,a2,t1
    bnez	a1,73f8 <.L48>
    lhu	a5,120(s0)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,120(s0)
    sw	a0,48(gp) # ffb00820 <unp_cfg_context>
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,104(s0)
    ttstallwait	32,6
    lw	a3,112(s0)
    lui	a4,0x67111
    add	a5,a5,a3
    addi	a4,a4,-1016 # 67110c08 <__device_print_strings_info_end+0x60c10c08>
    lw	a3,100(s0)
    sw	a5,112(s0)
    sw	a4,0(s1)
    bltu	a5,a3,74a0 <.L49>
    lw	a4,96(s0)
    sub	a5,a5,a4
    sw	a5,112(s0)
    lhu	a3,152(s0)
    lui	a4,0xffb44
    lw	a5,40(a4) # ffb44028 <__stack_base+0x437f8>
    zext.h	a5,a5
    beq	a5,a3,74a8 <.L50>
    lw	a3,136(s0)
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,74bc <.L51>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lui	a5,0xffef0
    beqz	a7,74dc <.L52>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,1024
    sw	a4,228(a5)
    sw	a4,236(a5)
    ttatgetm	0
    lui	a4,0xb3ff0
    sw	a4,0(s1)
    lui	a4,0xb47f0
    sw	a4,0(s1)
    lui	a4,0xb3070
    addi	a4,a4,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a4,0(s1)
    lui	a4,0xb4800
    addi	a4,a4,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a4,0(s1)
    lui	a4,0xb5010
    addi	a4,a4,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a4,0(s1)
    lui	a4,0xb5400
    addi	a2,a4,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a2,0(s1)
    addi	a4,a4,119
    sw	a4,0(s1)
    ttatrelm	0
    li	a4,16
    sw	a4,256(a5)
    lui	a4,0x40
    addi	a4,a4,1 # 40001 <.LASF490+0x3572f>
    lui	a2,0x1000
    sw	a4,260(a5)
    addi	a1,a2,16 # 1000010 <.LASF490+0xff573e>
    sw	a1,448(a5)
    sw	a4,452(a5)
    li	a1,36
    lui	a4,0xf0
    sw	a1,288(a5)
    addi	a4,a4,15 # f000f <.LASF490+0xe573d>
    sw	a4,292(a5)
    sw	a1,480(a5)
    lui	a1,0x400
    sw	a4,484(a5)
    addi	a1,a1,64 # 400040 <.LASF490+0x3f576e>
    sw	a1,336(a5)
    addi	a6,a2,256
    sw	a6,344(a5)
    lui	a4,0xffe00
    lui	a0,0x800
    sw	a6,160(a4) # ffe000a0 <__stack_base+0x2ff870>
    addi	a0,a0,128 # 800080 <.LASF490+0x7f57ae>
    sw	a0,164(a4)
    lui	a0,0x200
    sw	a1,168(a4)
    addi	a0,a0,32 # 200020 <.LASF490+0x1f574e>
    lui	a1,0x100
    sw	a0,172(a4)
    addi	a1,a1,16 # 100010 <.LASF490+0xf573e>
    sw	a1,176(a4)
    sw	zero,16(sp)
    lw	a4,176(a4)
    sw	a4,16(sp)
    ttsetc16	5,4
    li	a4,256
    sw	a4,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a4,0x45000
    slli	a5,a3,0x8
    addi	a2,a2,-256
    and	a5,a5,a2
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
    sw	a5,0(s1)
    lui	a5,0xb4010
    addi	a5,a5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a5,0(s1)
    ttsetadcxx	1,255,0
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a3,1
    sw	a3,4(a5)
    lui	a3,0x42008
    addi	a3,a3,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a3,8(a5)
    lui	a3,0x2000
    sw	a3,12(a5)
    lui	a2,0x43800
    sw	a3,16(a5)
    addi	a2,a2,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a2,20(a5)
    sw	a3,24(a5)
    lw	a3,136(s0)
    sw	a2,28(a5)
    sw	a2,32(a5)
    lw	a5,52(a4)
    zext.b	a5,a5
    bnez	a5,7674 <.L53>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a4,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a4,7698 <.L54>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,1024
    sw	a4,228(a5)
    sw	a4,236(a5)
    ttatgetm	0
    lui	a4,0xb3ff0
    sw	a4,0(s1)
    lui	a4,0xb47f0
    sw	a4,0(s1)
    lui	a4,0xb3070
    addi	a4,a4,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a4,0(s1)
    lui	a4,0xb4800
    addi	a4,a4,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a4,0(s1)
    lui	a4,0xb5010
    addi	a4,a4,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a4,0(s1)
    lui	a4,0xb5400
    addi	a2,a4,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a2,0(s1)
    addi	a4,a4,119
    sw	a4,0(s1)
    ttatrelm	0
    li	a4,16
    sw	a4,256(a5)
    lui	a4,0x40
    addi	a4,a4,1 # 40001 <.LASF490+0x3572f>
    lui	a2,0x1000
    sw	a4,260(a5)
    addi	a1,a2,16 # 1000010 <.LASF490+0xff573e>
    sw	a1,448(a5)
    sw	a4,452(a5)
    li	a1,36
    lui	a4,0xf0
    sw	a1,288(a5)
    addi	a4,a4,15 # f000f <.LASF490+0xe573d>
    sw	a4,292(a5)
    sw	a1,480(a5)
    lui	a1,0x400
    sw	a4,484(a5)
    addi	a1,a1,64 # 400040 <.LASF490+0x3f576e>
    sw	a1,336(a5)
    addi	a6,a2,256
    sw	a6,344(a5)
    lui	a4,0xffe00
    lui	a0,0x800
    sw	a6,160(a4) # ffe000a0 <__stack_base+0x2ff870>
    addi	a0,a0,128 # 800080 <.LASF490+0x7f57ae>
    sw	a0,164(a4)
    lui	a0,0x200
    sw	a1,168(a4)
    addi	a0,a0,32 # 200020 <.LASF490+0x1f574e>
    lui	a1,0x100
    sw	a0,172(a4)
    addi	a1,a1,16 # 100010 <.LASF490+0xf573e>
    sw	a1,176(a4)
    sw	zero,20(sp)
    lw	a4,176(a4)
    sw	a4,20(sp)
    ttsetc16	5,4
    li	a4,256
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    sw	a4,200(a5)
    ttsetc16	41,0
    lui	a4,0x45000
    slli	a5,a3,0x8
    addi	a2,a2,-256
    and	a5,a5,a2
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
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
    lw	a2,144(s0)
    sw	a4,24(a5)
    sw	a4,28(a5)
    addi	a2,a2,-1
    sw	a4,32(a5)
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    bnez	a5,784c <.LBB3549+0x10>
    j	8ac8 <.L146>
    addi	a1,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7858 <.L56>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,7870 <.L57>
    mv	a3,a1
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a1,a5,78a0 <.LM1172>
    j	8ac0 <.L200>
    ttsetc16	41,257
    lw	a2,144(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    bnez	a5,78c0 <.LBB3589+0x10>
    j	8ab4 <.L147>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,78cc <.L61>
    li	a5,1
    bne	a1,a5,78e4 <.L62>
    mv	a3,a0
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a1,a5,7914 <.LM1201>
    j	8aac <.L201>
    ttsetc16	41,257
    lw	a2,144(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    bnez	a5,7934 <.LBB3619+0x10>
    j	8aa0 <.L148>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7940 <.L66>
    li	a5,1
    bne	a1,a5,7958 <.L67>
    mv	a3,a0
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a1,a5,7988 <.LM1230>
    j	8a98 <.L202>
    ttsetc16	41,257
    lw	a2,144(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    bnez	a5,79a8 <.LBB3649+0x10>
    j	8a8c <.L149>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,79b4 <.L71>
    li	a5,1
    bne	a1,a5,79cc <.L72>
    mv	a3,a0
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
    bne	a4,a5,79fc <.LM1259>
    j	8a84 <.L203>
    ttsetc16	41,257
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
    lw	a3,48(s0)
    sw	a4,28(a5)
    sw	a4,32(a5)
    addi	a3,a3,-1 # 1ffffff <.LASF490+0x1ff572d>
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a4,0xffef0
    bnez	a5,7a80 <.LBB3703+0x10>
    j	8a78 <.L150>
    addi	a2,a4,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a4,a4,1204
    lui	a5,0xffe80
    lw	s2,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    andi	s2,s2,254
    bnez	s2,7a8c <.L76>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,7aa4 <.L77>
    mv	a4,a2
    sw	a3,0(a4)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    lui	a5,0xffec2
    lw	a5,0(a5) # ffec2000 <__instrn_buffer+0x82000>
    addi	a5,a5,4
    slli	a4,a5,0x4
    ttsetc16	5,0
    ttrdcfg	52,57
    lui	a3,0x45040
    addi	a3,a3,36 # 45040024 <__device_print_strings_info_end+0x3eb40024>
    sw	a3,0(s1)
    ttwrcfg	18,0,57
    lui	a3,0x10
    lw	a2,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a3,a3,-256 # ff00 <.LASF490+0x562e>
    zext.h	a5,a5
    and	a4,a4,a3
    bnez	a2,8958 <.L78>
    lui	a1,0xb3101
    lui	a2,0xb3ff0
    addi	a1,a1,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a2,a2,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a3,0xb4ff0
    sw	a1,0(s1)
    add	a5,a5,a2
    addi	a3,a3,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s1)
    add	a4,a4,a3
    sw	a4,0(s1)
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
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lw	a5,40(s0)
    lw	a0,48(s0)
    li	a2,0
    add	a0,a0,a5
    addi	a0,a0,-1
    li	a1,0
    jal	6da8 <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    lw	a5,48(s0)
    lw	a0,40(s0)
    addi	a5,a5,-1
    li	a2,0
    sh1add	a0,a0,a5
    li	a1,0
    jal	6da8 <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    lw	a0,48(s0)
    lw	a5,40(s0)
    addi	a0,a0,-1
    li	a2,0
    sh1add	a5,a5,a5
    li	a1,0
    add	a0,a0,a5
    jal	6da8 <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    lhu	a2,216(s0)
    lui	a3,0xffb46
    li	a4,3
    lw	a5,40(a3) # ffb46028 <__stack_base+0x457f8>
    sub	a5,a5,a2
    zext.h	a5,a5
    bgeu	a4,a5,7bcc <.L81>
    li	a7,4
    li	a5,16
    mv	a3,a7
    mv	a4,a5
    mv	a6,a7
    mv	a2,a7
    li	a1,0
    li	a0,0
    lw	s5,104(s0)
    jal	6b78 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lui	a4,0x1000
    slli	a5,s5,0x8
    addi	a4,a4,-256 # ffff00 <.LASF490+0xff562e>
    and	a5,a5,a4
    lui	a4,0x45000
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
    sw	a5,0(s1)
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
    lhu	a3,120(s0)
    sw	a4,28(a5)
    sw	a4,32(a5)
    lui	a4,0xffb43
    lw	a5,40(a4) # ffb43028 <__stack_base+0x427f8>
    zext.h	a5,a5
    beq	a5,a3,7ca4 <.L82>
    li	a7,4
    li	a5,16
    mv	a3,a7
    mv	a4,a5
    mv	a6,a7
    mv	a2,a7
    li	a1,0
    li	a0,0
    lw	s5,200(s0)
    jal	6b78 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lui	a4,0x1000
    slli	a5,s5,0x8
    addi	a4,a4,-256 # ffff00 <.LASF490+0xff562e>
    and	a5,a5,a4
    lui	a4,0x45000
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
    lui	a0,0xb4010
    sw	a5,0(s1)
    addi	a5,a0,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a5,0(s1)
    ttsetadcxx	1,255,0
    li	a3,0
    lui	a1,0xffe80
    addi	a1,a1,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a3
    sw	a5,0(a1)
    lw	a5,0(a1)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a6,4
    sw	a6,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a7,1
    lui	a4,0x42008
    sw	a7,4(a5)
    addi	a4,a4,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a4,8(a5)
    lui	a4,0x2000
    sw	a4,12(a5)
    lui	a2,0x43800
    sw	a4,16(a5)
    addi	a2,a2,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a2,20(a5)
    sw	a4,24(a5)
    sw	a2,28(a5)
    addi	a0,a0,328
    sw	a2,32(a5)
    sw	a0,0(s1)
    ttsetadcxx	1,255,0
    ttsetadcxx	2,15,0
    ttreplay	0,2,0,1
    ttunpacr	0,1,0,0,0,1,1,0,0,0,0,0,1
    ttunpacr	1,1,0,0,0,1,1,0,0,0,0,0,1
    sw	a3,0(a1)
    lw	a3,0(a1)
    and	zero,zero,a3
    sw	a7,0(a5)
    sw	a6,4(a5)
    sw	a4,8(a5)
    sw	a4,12(a5)
    lui	a3,0x4000
    sw	a4,16(a5)
    addi	a3,a3,32 # 4000020 <.LASF490+0x3ff574e>
    sw	a3,20(a5)
    sw	a4,24(a5)
    sw	a3,28(a5)
    sw	a3,32(a5)
    lw	a6,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    addi	a0,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    bnez	a6,7ddc <.L84>
    mv	a0,a5
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    lui	a4,0xffe80
    li	t1,1
    li	a7,4
    lw	a3,208(s0)
    lw	a5,200(s0)
    lw	a2,112(s0)
    mul	a5,s2,a5
    addi	a3,a3,-1
    add	a3,a3,a5
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7e0c <.L85>
    bnez	a1,88f8 <.L86>
    sw	a3,304(a0)
    sw	a2,496(a0)
    sw	zero,52(a4)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    li	a1,1
    ttsetc16	41,257
    addi	s2,s2,1
    bne	s2,a7,7dec <.L90>
    lhu	a5,120(s0)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,120(s0)
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,104(s0)
    ttstallwait	32,6
    lw	a3,112(s0)
    lui	a4,0x67111
    add	a5,a5,a3
    addi	a4,a4,-1016 # 67110c08 <__device_print_strings_info_end+0x60c10c08>
    lw	a3,100(s0)
    sw	a5,112(s0)
    sw	a4,0(s1)
    bltu	a5,a3,7ea0 <.L91>
    lw	a4,96(s0)
    sub	a5,a5,a4
    sw	a5,112(s0)
    lhu	a5,216(s0)
    lui	a3,0x45000
    addi	a5,a5,4
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,216(s0)
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,200(s0)
    ttstallwait	32,6
    lui	a4,0x67112
    lw	a2,208(s0)
    addi	a4,a4,-2040 # 67111808 <__device_print_strings_info_end+0x60c11808>
    lw	a3,196(s0)
    sh2add	a5,a5,a2
    sw	a4,0(s1)
    sw	a5,208(s0)
    bltu	a5,a3,7ef8 <.L92>
    lw	a4,192(s0)
    sub	a5,a5,a4
    sw	a5,208(s0)
    lhu	a3,184(s0)
    lui	a4,0xffb45
    lw	a5,40(a4) # ffb45028 <__stack_base+0x447f8>
    zext.h	a5,a5
    beq	a5,a3,7f00 <.L93>
    lw	a3,136(s0)
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,7f14 <.L94>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lui	a5,0xffef0
    beqz	a6,7f34 <.L95>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,1024
    sw	a4,228(a5)
    sw	a4,236(a5)
    ttatgetm	0
    lui	a4,0xb3ff0
    sw	a4,0(s1)
    lui	a4,0xb47f0
    sw	a4,0(s1)
    lui	a4,0xb3070
    addi	a4,a4,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a4,0(s1)
    lui	a4,0xb4800
    addi	a4,a4,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a4,0(s1)
    lui	a4,0xb5010
    addi	a4,a4,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a4,0(s1)
    lui	a4,0xb5400
    addi	a2,a4,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a2,0(s1)
    addi	a4,a4,119
    sw	a4,0(s1)
    ttatrelm	0
    li	a4,16
    sw	a4,256(a5)
    lui	a4,0x40
    addi	a4,a4,1 # 40001 <.LASF490+0x3572f>
    lui	a2,0x1000
    sw	a4,260(a5)
    addi	a1,a2,16 # 1000010 <.LASF490+0xff573e>
    sw	a1,448(a5)
    sw	a4,452(a5)
    li	a1,36
    lui	a4,0xf0
    sw	a1,288(a5)
    addi	a4,a4,15 # f000f <.LASF490+0xe573d>
    sw	a4,292(a5)
    sw	a1,480(a5)
    lui	a1,0x400
    sw	a4,484(a5)
    addi	a1,a1,64 # 400040 <.LASF490+0x3f576e>
    sw	a1,336(a5)
    addi	a6,a2,256
    sw	a6,344(a5)
    lui	a4,0xffe00
    lui	a0,0x800
    sw	a6,160(a4) # ffe000a0 <__stack_base+0x2ff870>
    addi	a0,a0,128 # 800080 <.LASF490+0x7f57ae>
    sw	a0,164(a4)
    lui	a0,0x200
    sw	a1,168(a4)
    addi	a0,a0,32 # 200020 <.LASF490+0x1f574e>
    lui	a1,0x100
    sw	a0,172(a4)
    addi	a1,a1,16 # 100010 <.LASF490+0xf573e>
    sw	a1,176(a4)
    sw	zero,24(sp)
    lw	a4,176(a4)
    sw	a4,24(sp)
    ttsetc16	5,4
    li	a4,256
    sw	a4,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a4,0x45000
    slli	a5,a3,0x8
    addi	a2,a2,-256
    and	a5,a5,a2
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
    sw	a5,0(s1)
    lui	a5,0xb4010
    addi	a5,a5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a5,0(s1)
    ttsetadcxx	1,255,0
    lui	a4,0xffe80
    li	a5,0
    addi	a3,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a3,1
    sw	a3,4(a5)
    lui	a3,0x42008
    addi	a3,a3,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a3,8(a5)
    lui	a3,0x2000
    sw	a3,12(a5)
    lui	a2,0x43800
    sw	a3,16(a5)
    addi	a2,a2,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a2,20(a5)
    sw	a3,24(a5)
    lw	a3,136(s0)
    sw	a2,28(a5)
    sw	a2,32(a5)
    lw	a5,52(a4)
    zext.b	a5,a5
    bnez	a5,80cc <.L96>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a4,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a4,80f0 <.L97>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,1024
    sw	a4,228(a5)
    sw	a4,236(a5)
    ttatgetm	0
    lui	a4,0xb3ff0
    sw	a4,0(s1)
    lui	a4,0xb47f0
    sw	a4,0(s1)
    lui	a4,0xb3070
    addi	a4,a4,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a4,0(s1)
    lui	a4,0xb4800
    addi	a4,a4,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a4,0(s1)
    lui	a4,0xb5010
    addi	a4,a4,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a4,0(s1)
    lui	a4,0xb5400
    addi	a2,a4,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a2,0(s1)
    addi	a4,a4,119
    sw	a4,0(s1)
    ttatrelm	0
    li	a4,16
    sw	a4,256(a5)
    lui	a4,0x40
    addi	a4,a4,1 # 40001 <.LASF490+0x3572f>
    lui	a2,0x1000
    sw	a4,260(a5)
    addi	a1,a2,16 # 1000010 <.LASF490+0xff573e>
    sw	a1,448(a5)
    sw	a4,452(a5)
    li	a1,36
    lui	a4,0xf0
    sw	a1,288(a5)
    addi	a4,a4,15 # f000f <.LASF490+0xe573d>
    sw	a4,292(a5)
    sw	a1,480(a5)
    lui	a1,0x400
    sw	a4,484(a5)
    addi	a1,a1,64 # 400040 <.LASF490+0x3f576e>
    sw	a1,336(a5)
    addi	a6,a2,256
    sw	a6,344(a5)
    lui	a4,0xffe00
    lui	a0,0x800
    sw	a6,160(a4) # ffe000a0 <__stack_base+0x2ff870>
    addi	a0,a0,128 # 800080 <.LASF490+0x7f57ae>
    sw	a0,164(a4)
    lui	a0,0x200
    sw	a1,168(a4)
    addi	a0,a0,32 # 200020 <.LASF490+0x1f574e>
    lui	a1,0x100
    sw	a0,172(a4)
    addi	a1,a1,16 # 100010 <.LASF490+0xf573e>
    sw	a1,176(a4)
    sw	zero,28(sp)
    lw	a4,176(a4)
    sw	a4,28(sp)
    ttsetc16	5,4
    li	a4,256
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    sw	a4,200(a5)
    ttsetc16	41,0
    lui	a4,0x45000
    slli	a5,a3,0x8
    addi	a2,a2,-256
    and	a5,a5,a2
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
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
    lw	a2,144(s0)
    sw	a4,24(a5)
    sw	a4,28(a5)
    addi	a2,a2,-1
    sw	a4,32(a5)
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,8a6c <.L153>
    addi	a1,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,82ac <.L99>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,82c4 <.L100>
    mv	a3,a1
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    beq	a1,a5,8a64 <.L204>
    ttsetc16	41,257
    lw	a2,144(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,8a58 <.L154>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,8318 <.L104>
    li	a5,1
    bne	a1,a5,8330 <.L105>
    mv	a3,a0
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    beq	a1,a5,8a50 <.L205>
    ttsetc16	41,257
    lw	a2,144(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,8a44 <.L155>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,8384 <.L109>
    li	a5,1
    bne	a1,a5,839c <.L110>
    mv	a3,a0
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    beq	a1,a5,8a3c <.L206>
    ttsetc16	41,257
    lw	a2,144(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,8a30 <.L156>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,83f0 <.L114>
    li	a5,1
    bne	a1,a5,8408 <.L115>
    mv	a3,a0
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
    beq	a4,a5,8a28 <.L207>
    ttsetc16	41,257
    lui	s9,0xb4010
    addi	s9,s9,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	s9,0(s1)
    ttsetadcxx	1,255,0
    li	s7,0
    lui	s8,0xffe80
    addi	s8,s8,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,s7
    sw	a5,0(s8)
    lw	a5,0(s8)
    and	zero,zero,a5
    lui	s2,0xffb80
    li	s5,4
    sw	s5,0(s2) # ffb80000 <__stack_base+0x7f7d0>
    li	s10,1
    sw	s10,4(s2)
    lui	s6,0x2000
    sw	s6,8(s2)
    sw	s6,12(s2)
    lui	a5,0x42088
    sw	s6,16(s2)
    addi	a5,a5,129 # 42088081 <__device_print_strings_info_end+0x3bb88081>
    sw	a5,20(s2)
    lw	a0,48(s0)
    sw	s6,24(s2)
    sw	a5,28(s2)
    sw	a5,32(s2)
    addi	a0,a0,-1
    li	a2,0
    li	a1,0
    jal	6da8 <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    lw	a5,40(s0)
    lw	a0,48(s0)
    li	a2,0
    add	a0,a0,a5
    addi	a0,a0,-1
    li	a1,0
    jal	6da8 <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    lw	a5,48(s0)
    lw	a0,40(s0)
    addi	a5,a5,-1
    li	a2,0
    sh1add	a0,a0,a5
    li	a1,0
    jal	6da8 <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    lw	a0,48(s0)
    lw	a5,40(s0)
    addi	a0,a0,-1
    sh1add	a5,a5,a5
    li	a2,0
    add	a0,a0,a5
    li	a1,0
    jal	6da8 <_Z14_llk_unpack_A_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmm>
    li	a5,16
    mv	a7,s5
    mv	a6,s5
    mv	a3,s5
    mv	a2,s5
    mv	a4,a5
    li	a1,0
    li	a0,0
    lw	s5,168(s0)
    jal	6b78 <_ZN7ckernel8unpacker19configure_unpack_ABILb1ELb0ELb0ELb0EEEvmmmmmmbmm.constprop.0>
    lui	a4,0x1000
    slli	a5,s5,0x8
    addi	a4,a4,-256 # ffff00 <.LASF490+0xff562e>
    and	a5,a5,a4
    lui	a4,0x45000
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s1)
    add	a5,a5,a4
    sw	a5,0(s1)
    sw	s9,0(s1)
    ttsetadcxx	2,255,0
    sw	s7,0(s8)
    lw	s7,0(s8)
    and	zero,zero,s7
    lui	a5,0x43000
    sw	s10,0(s2)
    sw	s10,4(s2)
    addi	a5,a5,257 # 43000101 <__device_print_strings_info_end+0x3cb00101>
    lui	a4,0x42808
    sw	a5,8(s2)
    addi	a4,a4,193 # 428080c1 <__device_print_strings_info_end+0x3c3080c1>
    sw	a4,12(s2)
    sw	s6,16(s2)
    lui	a5,0x54400
    sw	a4,20(s2)
    addi	a5,a5,129 # 54400081 <__device_print_strings_info_end+0x4df00081>
    sw	a5,24(s2)
    lw	a2,176(s0)
    sw	a5,28(s2)
    sw	a5,32(s2)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,8a1c <.L157>
    addi	a1,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,85d4 <.L119>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,85ec <.L120>
    mv	a3,a1
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    beq	a1,a5,8a14 <.L208>
    ttsetc16	41,257
    lw	a2,176(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,8a08 <.L158>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,8640 <.L124>
    li	a5,1
    bne	a1,a5,8658 <.L125>
    mv	a3,a0
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    beq	a1,a5,8a00 <.L209>
    ttsetc16	41,257
    lw	a2,176(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,89f4 <.L159>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,86ac <.L129>
    li	a5,1
    bne	a1,a5,86c4 <.L130>
    mv	a3,a0
    sw	a2,0(a3)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    beq	a1,a5,89ec <.L210>
    ttsetc16	41,257
    lw	a2,176(s0)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,89e0 <.L160>
    addi	a0,a3,1392 # ffef0570 <__instrn_buffer+0xb0570>
    addi	a3,a3,1396
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,8718 <.L134>
    li	a5,1
    bne	a1,a5,8730 <.L135>
    mv	a3,a0
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
    beq	a4,a5,89d8 <.L211>
    ttsetc16	41,257
    lhu	a5,184(s0)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,184(s0)
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,168(s0)
    ttstallwait	32,6
    lw	a3,176(s0)
    lui	a4,0x67111
    add	a5,a5,a3
    addi	a4,a4,1032 # 67111408 <__device_print_strings_info_end+0x60c11408>
    lw	a3,164(s0)
    sw	a5,176(s0)
    sw	a4,0(s1)
    bltu	a5,a3,87b8 <.L138>
    lw	a4,160(s0)
    sub	a5,a5,a4
    sw	a5,176(s0)
    lhu	a5,152(s0)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,152(s0)
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,136(s0)
    ttstallwait	32,6
    lw	a3,144(s0)
    lui	a4,0x67111
    add	a5,a5,a3
    addi	a4,a4,8 # 67111008 <__device_print_strings_info_end+0x60c11008>
    lw	a3,132(s0)
    sw	a5,144(s0)
    sw	a4,0(s1)
    bltu	a5,a3,8810 <.L139>
    lw	a4,128(s0)
    sub	a5,a5,a4
    sw	a5,144(s0)
    lhu	a5,56(s0)
    lui	a3,0x45000
    addi	a5,a5,4
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,56(s0)
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,40(s0)
    ttstallwait	32,6
    lui	a4,0x67110
    lw	a2,48(s0)
    addi	a4,a4,1032 # 67110408 <__device_print_strings_info_end+0x60c10408>
    lw	a3,36(s0)
    sh2add	a5,a5,a2
    sw	a4,0(s1)
    sw	a5,48(s0)
    bltu	a5,a3,8868 <.L140>
    lw	a4,32(s0)
    sub	a5,a5,a4
    sw	a5,48(s0)
    lhu	a5,24(s0)
    lui	a3,0x45000
    addi	a5,a5,4
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,24(s0)
    add	a4,a4,a3
    sw	a4,0(s1)
    lw	a5,8(s0)
    ttstallwait	32,6
    lui	a4,0x67110
    lw	a2,16(s0)
    addi	a4,a4,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    lw	a3,4(s0)
    sh2add	a5,a5,a2
    sw	a4,0(s1)
    sw	a5,16(s0)
    bltu	a5,a3,88c0 <.L33>
    lw	a4,0(s0)
    sub	a5,a5,a4
    sw	a5,16(s0)
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
    addi	sp,sp,80
    ret
    sw	a3,308(a0)
    sw	a2,500(a0)
    sw	zero,52(a4)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    bne	a1,t1,8948 <.L88>
    ttsetc16	41,0
    li	a1,0
    j	7e3c <.L89>
    sw	a2,308(a6)
    sw	a3,500(a6)
    sw	zero,52(a4)
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    bne	a0,t3,8950 <.L46>
    ttsetc16	41,0
    li	a0,0
    j	7438 <.L47>
    sub	a1,t1,a1
    j	7e38 <.L87>
    sub	a0,t3,a0
    j	7434 <.L45>
    lui	a0,0xb3202
    lui	a1,0xb5ff0
    addi	a0,a0,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a1,a1,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a3,0xb6ff0
    sw	a0,0(s1)
    add	a5,a5,a1
    addi	a3,a3,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s1)
    add	a4,a4,a3
    sw	a4,0(s1)
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
    sw	a3,0(s1)
    ttsetc16	5,4
    li	a5,1
    sub	a4,a5,a2
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a2,a5,7b64 <.L79>
    ttsetc16	41,0
    j	7b68 <.L80>
    ttsetc16	41,0
    j	8760 <.L137>
    addi	a0,a3,496
    addi	a3,a3,500
    j	8714 <.L133>
    ttsetc16	41,0
    j	86f4 <.L132>
    addi	a0,a3,496
    addi	a3,a3,500
    j	86a8 <.L128>
    ttsetc16	41,0
    j	8688 <.L127>
    addi	a0,a3,496
    addi	a3,a3,500
    j	863c <.L123>
    ttsetc16	41,0
    j	861c <.L122>
    addi	a1,a3,496
    addi	a3,a3,500
    j	85d0 <.L118>
    ttsetc16	41,0
    j	8438 <.L117>
    addi	a0,a3,496
    addi	a3,a3,500
    j	83ec <.L113>
    ttsetc16	41,0
    j	83cc <.L112>
    addi	a0,a3,496
    addi	a3,a3,500
    j	8380 <.L108>
    ttsetc16	41,0
    j	8360 <.L107>
    addi	a0,a3,496
    addi	a3,a3,500
    j	8314 <.L103>
    ttsetc16	41,0
    j	82f4 <.L102>
    addi	a1,a3,496
    addi	a3,a3,500
    j	82a8 <.L98>
    addi	a2,a4,304
    addi	a4,a4,308
    j	7a88 <.L75>
    ttsetc16	41,0
    j	7a00 <.L74>
    addi	a0,a3,496
    addi	a3,a3,500
    j	79b0 <.L70>
    ttsetc16	41,0
    j	798c <.L69>
    addi	a0,a3,496
    addi	a3,a3,500
    j	793c <.L65>
    ttsetc16	41,0
    j	7918 <.L64>
    addi	a0,a3,496
    addi	a3,a3,500
    j	78c8 <.L60>
    ttsetc16	41,0
    j	78a4 <.L59>
    addi	a1,a3,496
    addi	a3,a3,500
    j	7854 <.L55>
