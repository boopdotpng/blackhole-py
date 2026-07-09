    addi	sp,sp,-64
    sw	ra,60(sp)
    sw	s0,56(sp)
    sw	s1,52(sp)
    sw	s2,48(sp)
    sw	s3,44(sp)
    sw	s4,40(sp)
    lui	a5,0xffb01
    lui	a4,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__stack_base>
    addi	a4,a4,-2012 # ffb00824 <__ldm_bss_end>
    bltu	a4,a5,6ab8 <.L4>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,6aa0 <.L5>
    addi	a3,a5,-8
    bltu	a4,a3,79dc <.L65>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,6ad4 <.L7>
    sw	zero,-8(a5)
    auipc	a4,0x1
    addi	a4,a4,-128 # 7a54 <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <unp_cfg_context>
    beq	a4,a5,6b40 <.L9>
    addi	a2,gp,48 # ffb00820 <unp_cfg_context>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,6b24 <.L10>
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
    blt	a6,a3,6afc <.L11>
    blez	a3,6b40 <.L9>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,6b40 <.L9>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb12
    sw	zero,104(a5) # ffb12068 <__stack_base+0x11838>
    lw	a4,1312(zero) # 520 <.LLRL508+0x5>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,6b6c <.L15>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,6b60 <.L13>
    ttzerosrc	0,0,1,3
    lui	s1,0xffb00
    addi	s1,s1,32 # ffb00020 <cb_interface>
    lhu	a2,24(s1)
    lui	a3,0xffb40
    li	a4,3
    lw	a5,40(a3) # ffb40028 <__stack_base+0x3f7f8>
    sub	a5,a5,a2
    zext.h	a5,a5
    bgeu	a4,a5,6b84 <.L14>
    lhu	a2,56(s1)
    lui	a3,0xffb41
    li	a4,3
    lw	a5,40(a3) # ffb41028 <__stack_base+0x407f8>
    sub	a5,a5,a2
    zext.h	a5,a5
    bgeu	a4,a5,6ba0 <.L16>
    lw	a3,8(s1)
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    zext.b	a5,a5
    bnez	a5,6bb8 <.L17>
    ttsetadcxy	3,0,0,0,0,11
    ttsetadczw	3,0,0,0,0,15
    lw	a4,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a5,0xffef0
    beqz	a4,6bdc <.L18>
    addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    li	a4,1024
    sw	a4,228(a5)
    sw	a4,236(a5)
    ttatgetm	0
    lui	s0,0xffe40
    mv	s0,s0
    lui	a4,0xb3ff0
    sw	a4,0(s0) # ffe40000 <__instrn_buffer>
    lui	a4,0xb47f0
    sw	a4,0(s0)
    lui	a4,0xb3070
    addi	a4,a4,1 # b3070001 <__device_print_strings_info_end+0xacb70001>
    sw	a4,0(s0)
    lui	a4,0xb4800
    addi	a4,a4,1 # b4800001 <__device_print_strings_info_end+0xae300001>
    sw	a4,0(s0)
    lui	a4,0xb5010
    addi	a4,a4,1 # b5010001 <__device_print_strings_info_end+0xaeb10001>
    sw	a4,0(s0)
    lui	a4,0xb5400
    addi	a2,a4,71 # b5400047 <__device_print_strings_info_end+0xaef00047>
    sw	a2,0(s0)
    addi	a4,a4,119
    sw	a4,0(s0)
    ttatrelm	0
    li	a4,16
    sw	a4,256(a5)
    lui	a4,0x40
    addi	a4,a4,1 # 40001 <.LASF481+0x37cb7>
    lui	a2,0x1000
    sw	a4,260(a5)
    addi	a1,a2,16 # 1000010 <.LASF481+0xff7cc6>
    sw	a1,448(a5)
    sw	a4,452(a5)
    li	a1,32
    lui	a4,0xf0
    sw	a1,288(a5)
    addi	a4,a4,15 # f000f <.LASF481+0xe7cc5>
    sw	a4,292(a5)
    sw	a1,480(a5)
    lui	a1,0x400
    sw	a4,484(a5)
    addi	a1,a1,64 # 400040 <.LASF481+0x3f7cf6>
    sw	a1,336(a5)
    addi	a6,a2,256
    sw	a6,344(a5)
    lui	a4,0xffe00
    lui	a0,0x800
    sw	a6,160(a4) # ffe000a0 <__stack_base+0x2ff870>
    addi	a0,a0,128 # 800080 <.LASF481+0x7f7d36>
    sw	a0,164(a4)
    lui	a0,0x200
    sw	a1,168(a4)
    addi	a0,a0,32 # 200020 <.LASF481+0x1f7cd6>
    lui	a1,0x100
    sw	a0,172(a4)
    addi	a1,a1,16 # 100010 <.LASF481+0xf7cc6>
    sw	a1,176(a4)
    sw	zero,28(sp)
    lw	a4,176(a4)
    sw	a4,28(sp)
    ttsetc16	5,4
    li	a4,256
    sw	a4,200(a5)
    sw	zero,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,0
    lui	a4,0x45000
    addi	a2,a2,-256
    slli	a5,a3,0x8
    and	a5,a5,a2
    addi	a3,a4,72 # 45000048 <__device_print_strings_info_end+0x3eb00048>
    add	a3,a5,a3
    addi	a4,a4,74
    sw	a3,0(s0)
    add	a5,a5,a4
    sw	a5,0(s0)
    jal	79e4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    jal	79e4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lw	a3,16(s1)
    addi	a1,a3,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a2,0xffef0
    beqz	a0,6d30 <.L19>
    addi	a2,a2,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6d34 <.L20>
    sw	a1,304(a2)
    sw	zero,52(a4)
    lui	a5,0xffec2
    lw	a5,0(a5) # ffec2000 <__instrn_buffer+0x82000>
    addi	a5,a5,4
    slli	a4,a5,0x4
    ttsetc16	5,0
    ttrdcfg	52,57
    lui	a2,0x45040
    addi	a2,a2,36 # 45040024 <__device_print_strings_info_end+0x3eb40024>
    sw	a2,0(s0)
    ttwrcfg	18,0,57
    lui	a7,0xb3ff0
    lui	a6,0xb3101
    lui	a1,0x10
    addi	a7,a7,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    addi	a6,a6,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a1,a1,-256 # ff00 <.LASF481+0x7bb6>
    slli	a5,a5,0xc
    lui	a2,0xb4ff0
    zext.h	a5,a5
    sw	a6,0(s0)
    add	a5,a5,a7
    and	a4,a4,a1
    addi	a2,a2,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s0)
    add	a5,a4,a2
    sw	a5,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s0)
    sw	a2,0(s0)
    ttsetc16	5,4
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lw	a5,8(s1)
    add	a3,a3,a5
    addi	a3,a3,-1
    ttsetadczw	3,0,0,0,0,15
    lui	a5,0xffef0
    addi	a2,a5,308 # ffef0134 <__instrn_buffer+0xb0134>
    beqz	a0,6e18 <.L21>
    addi	a2,a5,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6e1c <.L22>
    sw	a3,0(a2)
    sw	zero,52(a4)
    lui	a5,0xffec2
    lw	a5,0(a5) # ffec2000 <__instrn_buffer+0x82000>
    addi	a5,a5,4
    slli	a4,a5,0x4
    ttsetc16	5,0
    ttrdcfg	52,57
    lui	a3,0x45040
    addi	a3,a3,36 # 45040024 <__device_print_strings_info_end+0x3eb40024>
    sw	a3,0(s0)
    ttwrcfg	18,0,57
    lui	a3,0x10
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a3,a3,-256 # ff00 <.LASF481+0x7bb6>
    zext.h	a5,a5
    and	a4,a4,a3
    bnez	a1,7914 <.L23>
    lui	a0,0xb3101
    lui	a2,0xb3ff0
    addi	a0,a0,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a2,a2,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a3,0xb4ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lw	a5,16(s1)
    lw	a2,8(s1)
    addi	a5,a5,-1
    sh1add	a2,a2,a5
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,79d0 <.L70>
    addi	a0,a3,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a3,a3,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,6f14 <.L27>
    li	a5,1
    bne	a1,a5,6f2c <.L28>
    mv	a3,a0
    sw	a2,0(a3)
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
    sw	a3,0(s0)
    ttwrcfg	18,0,57
    lui	a3,0x10
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a3,a3,-256 # ff00 <.LASF481+0x7bb6>
    zext.h	a5,a5
    and	a4,a4,a3
    bnez	a1,7894 <.L29>
    lui	a0,0xb3101
    lui	a2,0xb3ff0
    addi	a0,a0,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a2,a2,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a3,0xb4ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lw	a3,16(s1)
    lw	a5,8(s1)
    addi	a3,a3,-1
    sh1add	a5,a5,a5
    add	a3,a3,a5
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a2,0xffef0
    beqz	a5,79c4 <.L71>
    addi	a0,a2,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a2,a2,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7020 <.L33>
    li	a5,1
    bne	a1,a5,7038 <.L34>
    mv	a2,a0
    sw	a3,0(a2)
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
    sw	a3,0(s0)
    ttwrcfg	18,0,57
    lui	a3,0x10
    lw	s4,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a3,a3,-256 # ff00 <.LASF481+0x7bb6>
    zext.h	a5,a5
    and	a4,a4,a3
    bnez	s4,7814 <.L35>
    lui	a1,0xb3101
    lui	a2,0xb3ff0
    addi	a1,a1,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a2,a2,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a3,0xb4ff0
    sw	a1,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    jal	79e4 <_Z19_llk_unpack_A_init_ILN7ckernel13BroadcastTypeE0ELb0ELNS0_26EltwiseBinaryReuseDestTypeE0ELb1EEvmmmmmm.constprop.0>
    lw	a2,48(s1)
    addi	a2,a2,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,79b8 <.L72>
    addi	a1,a3,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a3,a3,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7124 <.L39>
    li	a5,1
    bne	s4,a5,713c <.L40>
    mv	a3,a1
    sw	a2,0(a3)
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
    sw	a3,0(s0)
    ttwrcfg	18,0,57
    lui	a3,0x10
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a3,a3,-256 # ff00 <.LASF481+0x7bb6>
    zext.h	a5,a5
    and	a4,a4,a3
    bnez	a1,7794 <.L41>
    lui	a0,0xb3101
    lui	a2,0xb3ff0
    addi	a0,a0,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a2,a2,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a3,0xb4ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lw	a3,48(s1)
    lw	a5,40(s1)
    add	a3,a3,a5
    addi	a3,a3,-1
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a2,0xffef0
    beqz	a5,79ac <.L73>
    addi	a0,a2,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a2,a2,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,722c <.L45>
    li	a5,1
    bne	a1,a5,7244 <.L46>
    mv	a2,a0
    sw	a3,0(a2)
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
    sw	a3,0(s0)
    ttwrcfg	18,0,57
    lui	a3,0x10
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a3,a3,-256 # ff00 <.LASF481+0x7bb6>
    zext.h	a5,a5
    and	a4,a4,a3
    bnez	a1,7714 <.L47>
    lui	a0,0xb3101
    lui	a2,0xb3ff0
    addi	a0,a0,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a2,a2,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a3,0xb4ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lw	a5,48(s1)
    lw	a2,40(s1)
    addi	a5,a5,-1
    sh1add	a2,a2,a5
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a3,0xffef0
    beqz	a5,79a0 <.L74>
    addi	a0,a3,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a3,a3,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7334 <.L51>
    li	a5,1
    bne	a1,a5,734c <.L52>
    mv	a3,a0
    sw	a2,0(a3)
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
    sw	a3,0(s0)
    ttwrcfg	18,0,57
    lui	a3,0x10
    lw	a1,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a3,a3,-256 # ff00 <.LASF481+0x7bb6>
    zext.h	a5,a5
    and	a4,a4,a3
    bnez	a1,7694 <.L53>
    lui	a0,0xb3101
    lui	a2,0xb3ff0
    addi	a0,a0,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a2,a2,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a3,0xb4ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lw	a3,48(s1)
    lw	a5,40(s1)
    addi	a3,a3,-1
    sh1add	a5,a5,a5
    add	a3,a3,a5
    ttsetadczw	3,0,0,0,0,15
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lui	a2,0xffef0
    beqz	a5,7994 <.L75>
    addi	a0,a2,1200 # ffef04b0 <__instrn_buffer+0xb04b0>
    addi	a2,a2,1204
    lui	a4,0xffe80
    lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    andi	a5,a5,254
    bnez	a5,7440 <.L57>
    li	a5,1
    bne	a1,a5,7458 <.L58>
    mv	a2,a0
    sw	a3,0(a2)
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
    sw	a3,0(s0)
    ttwrcfg	18,0,57
    lui	a3,0x10
    lw	a2,48(gp) # ffb00820 <unp_cfg_context>
    slli	a5,a5,0xc
    addi	a3,a3,-256 # ff00 <.LASF481+0x7bb6>
    zext.h	a5,a5
    and	a4,a4,a3
    bnez	a2,7614 <.L59>
    lui	a1,0xb3101
    lui	a2,0xb3ff0
    addi	a1,a1,73 # b3101049 <__device_print_strings_info_end+0xacc01049>
    addi	a2,a2,84 # b3ff0054 <__device_print_strings_info_end+0xadaf0054>
    lui	a3,0xb4ff0
    sw	a1,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b4ff0054 <__device_print_strings_info_end+0xaeaf0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b3ff4054 <__device_print_strings_info_end+0xadaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sw	a5,48(gp) # ffb00820 <unp_cfg_context>
    ttsetc16	41,257
    lui	a4,0x3e000
    sw	a4,24(sp)
    lhu	a5,56(s1)
    lw	a3,24(sp)
    sw	a4,20(sp)
    lw	a3,20(sp)
    addi	a5,a5,4
    lui	a2,0x45000
    zext.h	a5,a5
    sw	a4,16(sp)
    slli	a3,a5,0x8
    addi	a2,a2,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    lw	a1,16(sp)
    sh	a5,56(s1)
    sw	a4,12(sp)
    add	a3,a3,a2
    lw	a4,12(sp)
    sw	a3,0(s0)
    lw	a5,40(s1)
    ttstallwait	32,6
    lui	a4,0x67110
    lw	a2,48(s1)
    addi	a4,a4,1032 # 67110408 <__device_print_strings_info_end+0x60c10408>
    lw	a3,36(s1)
    sh2add	a5,a5,a2
    sw	a4,0(s0)
    sw	a5,48(s1)
    bltu	a5,a3,7598 <.L62>
    lw	a4,32(s1)
    sub	a5,a5,a4
    sw	a5,48(s1)
    lhu	a5,24(s1)
    lui	a3,0x45000
    addi	a5,a5,4
    zext.h	a5,a5
    addi	a3,a3,8 # 45000008 <__device_print_strings_info_end+0x3eb00008>
    slli	a4,a5,0x8
    sh	a5,24(s1)
    add	a4,a4,a3
    sw	a4,0(s0)
    lw	a5,8(s1)
    ttstallwait	32,6
    lui	a4,0x67110
    lw	a2,16(s1)
    addi	a4,a4,8 # 67110008 <__device_print_strings_info_end+0x60c10008>
    lw	a3,4(s1)
    sh2add	a5,a5,a2
    sw	a4,0(s0)
    sw	a5,16(s1)
    bltu	a5,a3,75f0 <.L63>
    lw	a4,0(s1)
    sub	a5,a5,a4
    sw	a5,16(s1)
    lw	ra,60(sp)
    lw	s0,56(sp)
    lw	s1,52(sp)
    lw	s2,48(sp)
    lw	s3,44(sp)
    lw	s4,40(sp)
    li	a0,0
    addi	sp,sp,64
    ret
    lui	a0,0xb3202
    lui	a1,0xb5ff0
    addi	a0,a0,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a1,a1,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a3,0xb6ff0
    sw	a0,0(s0)
    add	a5,a5,a1
    addi	a3,a3,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sub	a4,a5,a2
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a2,a5,7518 <.L60>
    ttsetc16	41,0
    j	751c <.L61>
    lui	a0,0xb3202
    lui	a2,0xb5ff0
    addi	a0,a0,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a2,a2,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a3,0xb6ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a1,a5,740c <.L54>
    ttsetc16	41,0
    j	7410 <.L55>
    lui	a0,0xb3202
    lui	a2,0xb5ff0
    addi	a0,a0,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a2,a2,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a3,0xb6ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a1,a5,7304 <.L48>
    ttsetc16	41,0
    j	7308 <.L49>
    lui	a0,0xb3202
    lui	a2,0xb5ff0
    addi	a0,a0,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a2,a2,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a3,0xb6ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a1,a5,71fc <.L42>
    ttsetc16	41,0
    j	7200 <.L43>
    lui	a1,0xb3202
    lui	a2,0xb5ff0
    addi	a1,a1,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a2,a2,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a3,0xb6ff0
    sw	a1,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sub	a4,a5,s4
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	s4,a5,70f8 <.L36>
    ttsetc16	41,0
    j	70fc <.L37>
    lui	a0,0xb3202
    lui	a2,0xb5ff0
    addi	a0,a0,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a2,a2,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a3,0xb6ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a1,a5,6fec <.L30>
    ttsetc16	41,0
    j	6ff0 <.L31>
    lui	a0,0xb3202
    lui	a2,0xb5ff0
    addi	a0,a0,73 # b3202049 <__device_print_strings_info_end+0xacd02049>
    addi	a2,a2,84 # b5ff0054 <__device_print_strings_info_end+0xafaf0054>
    lui	a3,0xb6ff0
    sw	a0,0(s0)
    add	a5,a5,a2
    addi	a3,a3,84 # b6ff0054 <__device_print_strings_info_end+0xb0af0054>
    sw	a5,0(s0)
    add	a4,a4,a3
    sw	a4,0(s0)
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
    sw	a4,0(s0)
    addi	a5,a5,84 # b5ff4054 <__device_print_strings_info_end+0xafaf4054>
    sw	a5,0(s0)
    sw	a3,0(s0)
    ttsetc16	5,4
    li	a5,1
    sub	a4,a5,a1
    sw	a4,48(gp) # ffb00820 <unp_cfg_context>
    bne	a1,a5,6ee4 <.L24>
    ttsetc16	41,0
    j	6ee8 <.L25>
    addi	a0,a2,304
    addi	a2,a2,308
    j	743c <.L56>
    addi	a0,a3,304
    addi	a3,a3,308
    j	7330 <.L50>
    addi	a0,a2,304
    addi	a2,a2,308
    j	7228 <.L44>
    addi	a1,a3,304
    addi	a3,a3,308
    j	7120 <.L38>
    addi	a0,a2,304
    addi	a2,a2,308
    j	701c <.L32>
    addi	a0,a3,304
    addi	a3,a3,308
    j	6f10 <.L26>
    mv	a5,a3
    j	6ac8 <.L6>
    lui	a5,0xffe40
    lui	a4,0xb4010
    mv	a5,a5
    addi	a4,a4,72 # b4010048 <__device_print_strings_info_end+0xadb10048>
    sw	a4,0(a5) # ffe40000 <__instrn_buffer>
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
    sw	a4,28(a5)
    sw	a4,32(a5)
    ret
