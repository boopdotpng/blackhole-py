    addi	sp,sp,-16
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__stack_base>
    addi	a4,a4,-2012 # ffb00824 <__ldm_bss_end>
    bltu	a4,a5,6aa0 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,6a88 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,72fc <.L60>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6abc <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x1
    addi	a4,a4,-1976 # 7304 <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <unp_cfg_context>
    beq	a4,a5,6b28 <.L7>
    addi	a2,gp,48 # ffb00820 <unp_cfg_context>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6b0c <.L8>
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
    blt	a6,a3,6ae4 <.L9>
    blez	a3,6b28 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6b28 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb12
    sw	zero,104(a5) # ffb12068 <__stack_base+0x11838>
    lw	a4,1312(zero) # 520 <.LLST131>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,6b54 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,6b48 <.L11>
    ttzerosrc	0,0,1,3
    lui	a4,0xffb00
    addi	a4,a4,32 # ffb00020 <cb_interface>
    lhu	a1,24(a4)
    lui	a2,0xffb40
    li	a3,3
    lw	a5,40(a2) # ffb40028 <__stack_base+0x3f7f8>
    sub	a5,a5,a1
    zext.h	a5,a5
    bgeu	a3,a5,6b6c <.L12>
    lhu	a1,56(a4)
    lui	a2,0xffb41
    li	a3,3
    lw	a5,40(a2) # ffb41028 <__stack_base+0x407f8>
    sub	a5,a5,a1
    zext.h	a5,a5
    bgeu	a3,a5,6b88 <.L14>
    lw	a1,8(a4)
    lui	a3,0xffe80
    lw	a5,52(a3) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,6ba0 <.L15>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a3,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a3,6bc4 <.L16>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a3,512
    sw	a3,228(a5)
    sw	a3,236(a5)
    ttatgetm	0
    lui	a2,0xffe40
    mv	a2,a2
    lui	a3,0xb3ff0
    sw	a3,0(a2) # ffe40000 <__instrn_buffer>
    lui	a3,0xb47f0
    sw	a3,0(a2)
    lui	a3,0xb3070
    addi	a3,a3,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a3,0(a2)
    lui	a3,0xb4800
    addi	a3,a3,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a3,0(a2)
    lui	a3,0xb5010
    addi	a3,a3,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a3,0(a2)
    lui	a3,0xb5400
    addi	a6,a3,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a6,0(a2)
    addi	a3,a3,119
    sw	a3,0(a2)
    ttatrelm	0
    li	a3,21
    sw	a3,256(a5)
    lui	a3,0x40
    addi	a3,a3,1 # 40001 <.LASF492+0x37c9f>
    lui	a6,0x1000
    sw	a3,260(a5)
    addi	a7,a6,21 # 1000015 <.LASF492+0xff7cb3>
    sw	a7,448(a5)
    sw	a3,452(a5)
    li	a7,37
    lui	a3,0xf0
    sw	a7,288(a5)
    addi	a3,a3,15 # f000f <.LASF492+0xe7cad>
    sw	a3,292(a5)
    sw	a7,480(a5)
    lui	a7,0x400
    sw	a3,484(a5)
    addi	a7,a7,64 # 400040 <.LASF492+0x3f7cde>
    sw	a7,336(a5)
    addi	t1,a6,256
    sw	t1,344(a5)
    lui	a3,0xffe00
    sw	t1,160(a3) # ffe000a0 <__stack_base+0x2ff870>
    lui	t1,0x800
    addi	t1,t1,128 # 800080 <.LASF492+0x7f7d1e>
    sw	t1,164(a3)
    sw	a7,168(a3)
    lui	a7,0x200
    addi	a7,a7,32 # 200020 <.LASF492+0x1f7cbe>
    sw	a7,172(a3)
    lui	a7,0x100
    addi	a7,a7,16 # 100010 <.LASF492+0xf7cae>
    sw	a7,176(a3)
    sw	zero,12(sp)
    lw	a3,176(a3)
    sw	a3,12(sp)
    ttsetc16	5,4
    li	a3,256
    sw	a3,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a7,0x45000
    slli	a5,a1,0x8
    addi	a6,a6,-256
    and	a5,a5,a6
    addi	a1,a7,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a1,a5,a1
    addi	a7,a7,74
    sw	a1,0(a2)
    add	a5,a5,a7
    lui	t4,0xb4010
    sw	a5,0(a2)
    addi	t4,t4,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	t4,0(a2)
    ttsetadcxx	1,255,0
    li	a7,0
    lui	t3,0xffe80
    addi	t3,t3,8 # ffe80008 <__instrn_buffer+0x40008>
    mv	a5,a7
    sw	a5,0(t3)
    lw	a5,0(t3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	t6,4
    sw	t6,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	t5,1
    lui	t1,0x42008
    sw	t5,4(a5)
    addi	t1,t1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	t1,8(a5)
    lui	a6,0x2000
    sw	a6,12(a5)
    lui	a1,0x43800
    sw	a6,16(a5)
    addi	a1,a1,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a1,20(a5)
    sw	a6,24(a5)
    sw	a1,28(a5)
    sw	a1,32(a5)
    sw	t4,0(a2)
    ttsetadcxx	1,255,0
    sw	a7,0(t3)
    lw	a7,0(t3)
    and	zero,zero,a7
    sw	t6,0(a5)
    sw	t5,4(a5)
    sw	t1,8(a5)
    sw	a6,12(a5)
    sw	a6,16(a5)
    sw	a1,20(a5)
    sw	a6,24(a5)
    lw	a7,16(a4)
    sw	a1,28(a5)
    sw	a1,32(a5)
    addi	a7,a7,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a6,0xffef0
    beqz	a5,72f0 <.L63>
    addi	t1,a6,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a6,a6,1204
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6dc0 <.L18>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,6dd8 <.L19>
    mv	a6,t1
    sw	a7,0(a6)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	t1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a1,a5,t1
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    beq	t1,a5,72e8 <.L89>
    ttsetc16	41,257
    lw	a6,16(a4)
    lw	a5,8(a4)
    add	a6,a6,a5
    addi	a6,a6,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a7,0xffef0
    beqz	a5,72dc <.L64>
    addi	t3,a7,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a7,a7,1204
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6e34 <.L23>
    li	a5,1
    bne	t1,a5,6e4c <.L24>
    mv	a7,t3
    sw	a6,0(a7)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	t1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a1,a5,t1
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    beq	t1,a5,72d4 <.L90>
    ttsetc16	41,257
    lw	a5,16(a4)
    lw	a7,8(a4)
    addi	a5,a5,-1
    sh1add	a7,a7,a5
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a6,0xffef0
    beqz	a5,72c8 <.L65>
    addi	t3,a6,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a6,a6,1204
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6ea8 <.L28>
    li	a5,1
    bne	t1,a5,6ec0 <.L29>
    mv	a6,t3
    sw	a7,0(a6)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	t1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a1,a5,t1
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    beq	t1,a5,72c0 <.L91>
    ttsetc16	41,257
    lw	a6,16(a4)
    lw	a5,8(a4)
    addi	a6,a6,-1
    sh1add	a5,a5,a5
    add	a6,a6,a5
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a7,0xffef0
    beqz	a5,72b4 <.L66>
    addi	t3,a7,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a7,a7,1204
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6f20 <.L33>
    li	a5,1
    bne	t1,a5,6f38 <.L34>
    mv	a7,t3
    sw	a6,0(a7)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a6,a5,a1
    sw	a6,48(gp) # ffb00820 <unp_cfg_context>
    beq	a1,a5,72ac <.L92>
    ttsetc16	41,257
    lui	a5,0xb4010
    addi	a5,a5,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a5,0(a2)
    ttsetadcxx	1,255,0
    lui	a1,0xffe80
    li	a5,0
    addi	a1,a1,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a1)
    lw	a5,0(a1)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a1,4
    sw	a1,0(a5) # ffb80000 <__stack_base+0x7f7d0>
    li	a1,1
    sw	a1,4(a5)
    lui	a1,0x42008
    addi	a1,a1,193 # 420080c1 <__device_print_strings_info_end+0x3bb080c1>
    sw	a1,8(a5)
    lui	a6,0x2000
    sw	a6,12(a5)
    lui	a1,0x43800
    sw	a6,16(a5)
    addi	a1,a1,257 # 43800101 <__device_print_strings_info_end+0x3d300101>
    sw	a1,20(a5)
    sw	a6,24(a5)
    lw	a7,48(a4)
    sw	a1,28(a5)
    sw	a1,32(a5)
    addi	a7,a7,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a6,0xffef0
    beqz	a5,72a0 <.L67>
    addi	t1,a6,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a6,a6,1204
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6ff8 <.L38>
    lw	a5,48(gp) # ffb00820 <unp_cfg_context>
    bnez	a5,7010 <.L39>
    mv	a6,t1
    sw	a7,0(a6)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	t1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a1,a5,t1
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    beq	t1,a5,7298 <.L93>
    ttsetc16	41,257
    lw	a6,48(a4)
    lw	a5,40(a4)
    add	a6,a6,a5
    addi	a6,a6,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a7,0xffef0
    beqz	a5,728c <.L68>
    addi	t3,a7,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a7,a7,1204
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,706c <.L43>
    li	a5,1
    bne	t1,a5,7084 <.L44>
    mv	a7,t3
    sw	a6,0(a7)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	t1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a1,a5,t1
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    beq	t1,a5,7284 <.L94>
    ttsetc16	41,257
    lw	a5,48(a4)
    lw	a7,40(a4)
    addi	a5,a5,-1
    sh1add	a7,a7,a5
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a6,0xffef0
    beqz	a5,7278 <.L69>
    addi	t3,a6,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a6,a6,1204
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,70e0 <.L48>
    li	a5,1
    bne	t1,a5,70f8 <.L49>
    mv	a6,t3
    sw	a7,0(a6)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a7,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a1,a5,a7
    sw	a1,48(gp) # ffb00820 <unp_cfg_context>
    beq	a7,a5,7270 <.L95>
    ttsetc16	41,257
    lw	a6,48(a4)
    lw	a5,40(a4)
    addi	a6,a6,-1
    sh1add	a5,a5,a5
    add	a6,a6,a5
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a0,0xffef0
    beqz	a5,7264 <.L70>
    addi	t1,a0,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a0,a0,1204
    lui	a1,0xffe80
    lw	a5,52(a1) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7158 <.L53>
    li	a5,1
    bne	a7,a5,7170 <.L54>
    mv	a0,t1
    sw	a6,0(a0)
    lui	a5,0xffe80
    sw	zero,52(a5) # ffe80034 <__instrn_buffer+0x40034>
    ttstallwait	8,1024
    ttmop	1,0,0
    ttsemget	32
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    li	a5,1
    sub	a0,a5,a1
    sw	a0,48(gp) # ffb00820 <unp_cfg_context>
    beq	a1,a5,725c <.L96>
    ttsetc16	41,257
    lhu	a5,56(a4)
    lui	a1,0x45000
    addi	a5,a5,4
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a5,0x8
    sh	a5,56(a4)
    add	a3,a3,a1
    sw	a3,0(a2)
    lw	a5,40(a4)
    ttstallwait	32,6
    lui	a3,0x67110
    lw	a0,48(a4)
    addi	a3,a3,1032 # 67110408 <__device_print_strings_info_end+0x60c10408>
    lw	a1,36(a4)
    sh2add	a5,a5,a0
    sw	a3,0(a2)
    sw	a5,48(a4)
    bltu	a5,a1,71f8 <.L57>
    lw	a3,32(a4)
    sub	a5,a5,a3
    sw	a5,48(a4)
    lhu	a5,24(a4)
    lui	a1,0x45000
    addi	a5,a5,4
    zext.h	a5,a5
    addi	a1,a1,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a3,a5,0x8
    sh	a5,24(a4)
    add	a3,a3,a1
    sw	a3,0(a2)
    lw	a5,8(a4)
    ttstallwait	32,6
    lui	a3,0x67110
    lw	a0,16(a4)
    addi	a3,a3,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    lw	a1,4(a4)
    sh2add	a5,a5,a0
    sw	a3,0(a2)
    sw	a5,16(a4)
    bltu	a5,a1,7250 <.L58>
    lw	a3,0(a4)
    sub	a5,a5,a3
    sw	a5,16(a4)
    li	a0,0
    addi	sp,sp,16
    ret
    ttsetc16	41,0
    j	71a0 <.L56>
    addi	t1,a0,304
    addi	a0,a0,308
    j	7154 <.L52>
    ttsetc16	41,0
    j	7128 <.L51>
    addi	t3,a6,304
    addi	a6,a6,308
    j	70dc <.L47>
    ttsetc16	41,0
    j	70b4 <.L46>
    addi	t3,a7,304
    addi	a7,a7,308
    j	7068 <.L42>
    ttsetc16	41,0
    j	7040 <.L41>
    addi	t1,a6,304
    addi	a6,a6,308
    j	6ff4 <.L37>
    ttsetc16	41,0
    j	6f68 <.L36>
    addi	t3,a7,304
    addi	a7,a7,308
    j	6f1c <.L32>
    ttsetc16	41,0
    j	6ef0 <.L31>
    addi	t3,a6,304
    addi	a6,a6,308
    j	6ea4 <.L27>
    ttsetc16	41,0
    j	6e7c <.L26>
    addi	t3,a7,304
    addi	a7,a7,308
    j	6e30 <.L22>
    ttsetc16	41,0
    j	6e08 <.L21>
    addi	t1,a6,304
    addi	a6,a6,308
    j	6dbc <.L17>
    mv	a5,a3
    j	6ab0 <.L4>
