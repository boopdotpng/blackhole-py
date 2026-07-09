    addi	sp,sp,-96
    sw	s0,92(sp)
    lui	a5,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__fw_export_ldm_end+0x10>
    addi	a4,gp,48 # ffb00820 <__fw_export_ldm_end>
    bltu	a4,a5,7e70 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,7e58 <.L3>
    addi	a3,a5,-8
    bgeu	a4,a3,7e7c <.LM21>
    j	98f4 <.L35>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,7e90 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x2
    addi	a4,a4,-1428 # 98fc <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <__fw_export_ldm_end>
    beq	a4,a5,7efc <.L7>
    addi	a2,gp,48 # ffb00820 <__fw_export_ldm_end>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,7ee0 <.L8>
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
    blt	a6,a3,7eb8 <.L9>
    blez	a3,7efc <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,7efc <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LLST109>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7f20 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7f14 <.L11>
    lui	a3,0xffb00
    addi	a3,a3,32 # ffb00020 <cb_interface>
    lhu	a1,122(a3)
    lw	a2,108(a3)
    lui	a4,0xffb43
    lw	a5,32(a4) # ffb43020 <__fw_export_ldm_end+0x42800>
    add	a5,a2,a5
    zext.h	a5,a5
    beq	a1,a5,7f34 <.L12>
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t4,104(a3)
    lui	a4,0xffef0
    beqz	a5,7f58 <.L14>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a6,0x45000
    lui	a5,0xffe40
    mv	a5,a5
    addi	t6,a6,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t3,0x45004
    sw	t6,0(a5) # ffe40000 <__instrn_buffer>
    addi	t3,t3,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t1,0x45040
    sw	t3,0(a5)
    addi	t1,t1,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	a7,0x45100
    sw	t1,0(a5)
    addi	a7,a7,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a1,0xb5800
    addi	a1,a1,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a1,0(a5)
    lui	a1,0xb61e0
    addi	a1,a1,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a1,0(a5)
    lui	a1,0xb3fc0
    addi	a1,a1,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a1,0(a5)
    lui	a1,0xb4ff0
    addi	a1,a1,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a1,0(a5)
    lui	a1,0xb53f0
    addi	a1,a1,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a1,0(a5)
    ttatrelm	0
    lui	a1,0xb5100
    addi	a1,a1,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a1,0(a5)
    lui	a1,0xb6ff0
    addi	a1,a1,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a1,0(a5)
    lui	t5,0x40
    sw	t5,272(a4)
    li	t0,1
    sw	t0,280(a4)
    ttstallwait	128,8
    lui	a0,0xb3040
    addi	a0,a0,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    lui	a1,0xb5080
    sw	a0,0(a5)
    addi	a1,a1,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a1,0(a5)
    sw	t0,72(a4)
    lui	a1,0xffe00
    sw	t5,208(a1) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,12(sp)
    lw	t0,208(a1)
    li	t5,256
    lui	a0,0x10
    addi	a0,a0,-1 # ffff <.LASF1709+0x3595>
    sw	t0,12(sp)
    sw	t5,112(a4)
    sw	a0,96(a4)
    sw	zero,80(a4)
    sw	t4,64(a1)
    sw	zero,68(a1)
    sw	zero,72(a1)
    sw	zero,76(a1)
    sw	zero,8(sp)
    lw	a4,76(a1)
    sw	a4,8(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a0,0xffe80
    addi	t4,a0,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t4)
    lw	a4,0(t4)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t4,4
    sw	t4,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t4,4(a4)
    lui	t4,0x2000
    sw	t4,8(a4)
    sw	t4,12(a4)
    sw	t4,16(a4)
    lui	t5,0x41000
    sw	t5,20(a4)
    lui	t5,0x41008
    sw	t4,24(a4)
    addi	t4,t5,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t4,28(a4)
    lui	t4,0x41010
    sw	t4,32(a4)
    sw	t6,0(a5)
    sw	t3,0(a5)
    sw	t1,0(a5)
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	a0,a0,4
    sw	a4,0(a0)
    lw	a4,0(a0)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    ttsemwait	1,2,1
    lw	a0,116(a3)
    lui	a7,0x1000
    addi	a4,a0,-1
    slli	t1,a4,0x8
    addi	a7,a7,-256 # ffff00 <.LASF1709+0xff3496>
    srli	a4,a4,0x10
    addi	t3,a6,24
    lui	t4,0x508c0
    slli	a4,a4,0x8
    and	t1,t1,a7
    lui	a7,0x800
    sw	t4,0(a5)
    add	t1,t1,t3
    addi	a6,a6,25
    or	a7,a4,a7
    sw	t1,0(a5)
    add	a7,a7,a6
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a4,a4,a6
    sw	a4,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a4,104(a3)
    lw	a6,100(a3)
    add	a4,a0,a4
    sw	zero,124(a3)
    sw	a4,116(a3)
    bltu	a4,a6,81d8 <.L15>
    lw	a0,96(a3)
    sub	a4,a4,a0
    sw	a4,116(a3)
    lhu	a4,122(a3)
    lui	a6,0x45000
    addi	a4,a4,1
    zext.h	a4,a4
    addi	a6,a6,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a0,a4,0x8
    add	a0,a0,a6
    sh	a4,122(a3)
    sw	a0,0(a5)
    ttstallwait	32,8
    lui	a4,0x67611
    addi	a4,a4,-1014 # 67610c0a <__device_print_strings_info_end+0x61110c0a>
    sw	a4,0(a5)
    lhu	a7,154(a3)
    lw	a6,140(a3)
    lui	a0,0xffb44
    lw	a4,32(a0) # ffb44020 <__fw_export_ldm_end+0x43800>
    add	a4,a6,a4
    zext.h	a4,a4
    beq	a7,a4,8218 <.L16>
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t6,136(a3)
    lui	a4,0xffef0
    beqz	a0,823c <.L17>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a6,0x45000
    addi	t2,a6,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t5,0x45004
    sw	t2,0(a5)
    addi	t5,t5,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t4,0x45040
    sw	t5,0(a5)
    addi	t4,t4,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	t3,0x45100
    sw	t4,0(a5)
    addi	t3,t3,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	t3,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a0,0xb5800
    addi	a0,a0,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a0,0(a5)
    lui	a0,0xb61e0
    addi	a0,a0,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a0,0(a5)
    lui	a0,0xb3fc0
    addi	a0,a0,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    lui	a7,0xb4ff0
    sw	a0,0(a5)
    addi	a0,a7,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a0,0(a5)
    lui	a0,0xb53f0
    addi	a0,a0,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a0,0(a5)
    ttatrelm	0
    lui	a0,0xb5100
    addi	a0,a0,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a0,0(a5)
    lui	a0,0xb6ff0
    addi	a0,a0,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a0,0(a5)
    lui	t1,0x40
    sw	t1,272(a4)
    li	t0,1
    sw	t0,280(a4)
    ttstallwait	128,8
    lui	a0,0xb3040
    addi	a0,a0,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    sw	a0,0(a5)
    lui	a0,0xb5080
    addi	a0,a0,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a0,0(a5)
    sw	t0,72(a4)
    lui	a0,0xffe00
    sw	t1,208(a0) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,20(sp)
    lw	s0,208(a0)
    li	t0,256
    lui	t1,0x10
    addi	t1,t1,-1 # ffff <.LASF1709+0x3595>
    sw	s0,20(sp)
    sw	t0,112(a4)
    sw	t1,96(a4)
    sw	zero,80(a4)
    sw	t6,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,16(sp)
    lw	a4,76(a0)
    sw	a4,16(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	t1,0xffe80
    addi	t6,t1,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t6)
    lw	a4,0(t6)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t6,4
    sw	t6,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t6,4(a4)
    lui	t6,0x2000
    sw	t6,8(a4)
    sw	t6,12(a4)
    sw	t6,16(a4)
    lui	t0,0x41000
    sw	t0,20(a4)
    lui	t0,0x41008
    sw	t6,24(a4)
    addi	t6,t0,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t6,28(a4)
    lui	t6,0x41010
    sw	t6,32(a4)
    sw	t2,0(a5)
    sw	t5,0(a5)
    sw	t4,0(a5)
    sw	t3,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	t1,t1,4
    sw	a4,0(t1)
    lw	a4,0(t1)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    ttsetdmareg	0,0,0,56
    ttsetdmareg	0,170,0,57
    ttsetdmareg	0,1,0,60
    ttsetdmareg	1,5461,0,58
    ttsetdmareg	1,5461,0,59
    ttstallwait	128,8
    lui	a4,0xb4ff1
    addi	a4,a4,28 # b4ff101c <__device_print_strings_info_end+0xaeaf101c>
    sw	a4,0(a5)
    ttwrcfg	28,0,24
    ttwrcfg	30,0,25
    ttwrcfg	29,0,21
    ttnop
    ttnop
    ttsetdmareg	3,16383,0,56
    ttsetdmareg	0,0,0,57
    ttstallwait	128,8
    addi	a7,a7,284
    sw	a7,0(a5)
    ttwrcfg	28,0,24
    ttwrcfg	28,0,25
    ttwrcfg	0,0,20
    ttwrcfg	0,0,21
    ttnop
    ttnop
    ttsemwait	1,2,1
    lw	a0,148(a3)
    lui	a7,0x1000
    addi	a4,a0,-1
    slli	t1,a4,0x8
    addi	a7,a7,-256 # ffff00 <.LASF1709+0xff3496>
    srli	a4,a4,0x10
    addi	t3,a6,24
    lui	t4,0x508c0
    slli	a4,a4,0x8
    and	t1,t1,a7
    lui	a7,0x800
    sw	t4,0(a5)
    add	t1,t1,t3
    addi	a6,a6,25
    or	a7,a4,a7
    sw	t1,0(a5)
    add	a7,a7,a6
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a4,a4,a6
    sw	a4,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a4,136(a3)
    lw	a6,132(a3)
    add	a4,a0,a4
    sw	zero,156(a3)
    sw	a4,148(a3)
    bltu	a4,a6,8518 <.L18>
    lw	a0,128(a3)
    sub	a4,a4,a0
    sw	a4,148(a3)
    lhu	a4,154(a3)
    lui	a6,0x45000
    addi	a4,a4,1
    zext.h	a4,a4
    addi	a6,a6,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a0,a4,0x8
    add	a0,a0,a6
    sh	a4,154(a3)
    sw	a0,0(a5)
    ttstallwait	32,8
    lui	a4,0x67611
    addi	a4,a4,10 # 6761100a <__device_print_strings_info_end+0x6111100a>
    sw	a4,0(a5)
    lhu	t1,218(a3)
    lw	a7,204(a3)
    lui	a6,0xffb46
    li	a0,3
    lw	a4,32(a6) # ffb46020 <__fw_export_ldm_end+0x45800>
    add	a4,a7,a4
    sub	a4,a4,t1
    zext.h	a4,a4
    bgeu	a0,a4,855c <.L19>
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t5,200(a3)
    lui	a4,0xffef0
    beqz	a0,8584 <.L20>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	t4,0x45000
    addi	t4,t4,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t3,0x45004
    sw	t4,0(a5)
    addi	t3,t3,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t1,0x45040
    sw	t3,0(a5)
    addi	t1,t1,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	a7,0x45100
    sw	t1,0(a5)
    addi	a7,a7,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a0,0xb5800
    addi	a0,a0,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a0,0(a5)
    lui	a0,0xb61e0
    addi	a0,a0,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a0,0(a5)
    lui	a0,0xb3fc0
    addi	a0,a0,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a0,0(a5)
    lui	a0,0xb4ff0
    addi	a0,a0,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a0,0(a5)
    lui	a0,0xb53f0
    addi	a0,a0,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a0,0(a5)
    ttatrelm	0
    lui	a0,0xb5100
    addi	a0,a0,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a0,0(a5)
    lui	a0,0xb6ff0
    addi	a0,a0,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a0,0(a5)
    lui	t6,0x40
    sw	t6,272(a4)
    li	t0,1
    sw	t0,280(a4)
    ttstallwait	128,8
    lui	a6,0xb3040
    addi	a6,a6,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    lui	a0,0xb5080
    sw	a6,0(a5)
    addi	a0,a0,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a0,0(a5)
    sw	t0,72(a4)
    lui	a0,0xffe00
    sw	t6,208(a0) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,28(sp)
    lw	t0,208(a0)
    li	t6,256
    lui	a6,0x10
    addi	a6,a6,-1 # ffff <.LASF1709+0x3595>
    sw	t0,28(sp)
    sw	t6,112(a4)
    sw	a6,96(a4)
    sw	zero,80(a4)
    sw	t5,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,24(sp)
    lw	a4,76(a0)
    sw	a4,24(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a6,0xffe80
    addi	t5,a6,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t5)
    lw	a4,0(t5)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t5,4
    sw	t5,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t5,4(a4)
    lui	t5,0x2000
    sw	t5,8(a4)
    sw	t5,12(a4)
    sw	t5,16(a4)
    lui	t6,0x41000
    sw	t6,20(a4)
    lui	t6,0x41008
    sw	t5,24(a4)
    addi	t5,t6,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t5,28(a4)
    lui	t5,0x41010
    sw	t5,32(a4)
    sw	t4,0(a5)
    sw	t3,0(a5)
    sw	t1,0(a5)
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	a6,a6,4
    sw	a4,0(a6)
    lw	a4,0(a6)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t5,200(a3)
    lui	a4,0xffef0
    beqz	a0,8778 <.L21>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a0,0x45000
    addi	t6,a0,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t4,0x45004
    sw	t6,0(a5)
    addi	t4,t4,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t3,0x45040
    sw	t4,0(a5)
    addi	t3,t3,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	t1,0x45100
    sw	t3,0(a5)
    addi	t1,t1,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	t1,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a6,0xb5800
    addi	a6,a6,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a6,0(a5)
    lui	a6,0xb61e0
    addi	a6,a6,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a6,0(a5)
    lui	a6,0xb3fc0
    addi	a6,a6,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a6,0(a5)
    lui	a6,0xb4ff0
    addi	a6,a6,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a6,0(a5)
    lui	a6,0xb53f0
    addi	a6,a6,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a6,0(a5)
    ttatrelm	0
    lui	a6,0xb5100
    addi	a6,a6,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a6,0(a5)
    lui	a6,0xb6ff0
    addi	a6,a6,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a6,0(a5)
    lui	a7,0x40
    sw	a7,272(a4)
    li	t0,1
    sw	t0,280(a4)
    ttstallwait	128,8
    lui	a6,0xb3040
    addi	a6,a6,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    sw	a6,0(a5)
    lui	a6,0xb5080
    addi	a6,a6,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a6,0(a5)
    sw	t0,72(a4)
    lui	a6,0xffe00
    sw	a7,208(a6) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,36(sp)
    lw	t2,208(a6)
    li	t0,256
    lui	a7,0x10
    addi	a7,a7,-1 # ffff <.LASF1709+0x3595>
    sw	t2,36(sp)
    sw	t0,112(a4)
    sw	a7,96(a4)
    sw	zero,80(a4)
    sw	t5,64(a6)
    sw	zero,68(a6)
    sw	zero,72(a6)
    sw	zero,76(a6)
    sw	zero,32(sp)
    lw	a4,76(a6)
    sw	a4,32(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a7,0xffe80
    addi	t5,a7,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t5) # 41010000 <__device_print_strings_info_end+0x3ab10000>
    lw	a4,0(t5)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t5,4
    sw	t5,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t5,4(a4)
    lui	t5,0x2000
    sw	t5,8(a4)
    sw	t5,12(a4)
    sw	t5,16(a4)
    lui	t0,0x41000
    sw	t0,20(a4)
    sw	t5,24(a4)
    lui	t5,0x41008
    addi	t5,t5,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t5,28(a4)
    lui	t5,0x41010
    sw	t5,32(a4)
    sw	t6,0(a5)
    sw	t4,0(a5)
    sw	t3,0(a5)
    sw	t1,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	a7,a7,4
    sw	a4,0(a7)
    lw	a4,0(a7)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    ttsemwait	1,2,1
    lw	t5,212(a3)
    lui	t4,0x1000
    addi	a4,t5,-1 # 4100ffff <__device_print_strings_info_end+0x3ab0ffff>
    slli	a7,a4,0x8
    addi	t4,t4,-256 # ffff00 <.LASF1709+0xff3496>
    addi	t6,a0,24
    srli	a6,a4,0x10
    and	a7,a7,t4
    lui	t3,0x508c0
    add	a7,a7,t6
    sw	t3,0(a5)
    slli	a6,a6,0x8
    lui	t1,0x800
    sw	a7,0(a5)
    addi	a0,a0,25
    or	a7,a6,t1
    add	a7,a7,a0
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a6,a6,a0
    sw	a6,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    lw	a6,200(a3)
    addi	a7,t3,2 # 508c0002 <__device_print_strings_info_end+0x4a3c0002>
    add	t5,t5,a6
    sw	a7,0(a5)
    addi	a7,t5,-1
    slli	t0,a7,0x8
    and	t0,t0,t4
    srli	a7,a7,0x10
    add	t0,t0,t6
    slli	a7,a7,0x8
    sw	t0,0(a5)
    or	t0,a7,t1
    add	t0,t0,a0
    sw	t0,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a7,a7,a0
    sw	a7,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    addi	a7,t3,4
    sh1add	a4,a6,a4
    slli	t0,a4,0x8
    sw	a7,0(a5)
    and	t0,t0,t4
    srli	a7,a4,0x10
    add	t0,t0,t6
    slli	a7,a7,0x8
    sw	t0,0(a5)
    or	t0,a7,t1
    add	t0,t0,a0
    sw	t0,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a7,a7,a0
    sw	a7,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    add	a4,a6,a4
    slli	a7,a4,0x8
    srli	a4,a4,0x10
    addi	t3,t3,6
    and	a7,a7,t4
    slli	a4,a4,0x8
    sw	t3,0(a5)
    add	a7,a7,t6
    or	t1,a4,t1
    sw	a7,0(a5)
    add	t1,t1,a0
    sw	t1,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a4,a4,a0
    sw	a4,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    sh1add	a6,a6,a6
    lw	a4,196(a3)
    add	a6,a6,t5
    sw	a6,212(a3)
    sw	zero,220(a3)
    bltu	a6,a4,8adc <.L22>
    lw	a4,192(a3)
    sub	a6,a6,a4
    sw	a6,212(a3)
    lhu	a4,218(a3)
    lui	a6,0x45000
    addi	a4,a4,4
    zext.h	a4,a4
    addi	a6,a6,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a0,a4,0x8
    add	a0,a0,a6
    sh	a4,218(a3)
    sw	a0,0(a5)
    ttstallwait	32,8
    lui	a4,0x67612
    addi	a4,a4,-2038 # 6761180a <__device_print_strings_info_end+0x6111180a>
    sw	a4,0(a5)
    lhu	a7,122(a3)
    lw	a6,108(a3)
    lui	a0,0xffb43
    lw	a4,32(a0) # ffb43020 <__fw_export_ldm_end+0x42800>
    add	a4,a6,a4
    zext.h	a4,a4
    beq	a7,a4,8b1c <.L23>
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t5,104(a3)
    lui	a4,0xffef0
    beqz	a0,8b40 <.L24>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a6,0x45000
    addi	t0,a6,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t4,0x45004
    sw	t0,0(a5)
    addi	t4,t4,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t3,0x45040
    sw	t4,0(a5)
    addi	t3,t3,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	t1,0x45100
    sw	t3,0(a5)
    addi	t1,t1,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	t1,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a0,0xb5800
    addi	a0,a0,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a0,0(a5)
    lui	a0,0xb61e0
    addi	a0,a0,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a0,0(a5)
    lui	a0,0xb3fc0
    addi	a0,a0,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a0,0(a5)
    lui	a0,0xb4ff0
    addi	a0,a0,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a0,0(a5)
    lui	a0,0xb53f0
    addi	a0,a0,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a0,0(a5)
    ttatrelm	0
    lui	a0,0xb5100
    addi	a0,a0,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a0,0(a5)
    lui	a0,0xb6ff0
    addi	a0,a0,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a0,0(a5)
    lui	a7,0x40
    sw	a7,272(a4)
    li	t6,1
    sw	t6,280(a4)
    ttstallwait	128,8
    lui	a0,0xb3040
    addi	a0,a0,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    sw	a0,0(a5)
    lui	a0,0xb5080
    addi	a0,a0,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a0,0(a5)
    sw	t6,72(a4)
    lui	a0,0xffe00
    sw	a7,208(a0) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,44(sp)
    lw	t2,208(a0)
    li	t6,256
    lui	a7,0x10
    addi	a7,a7,-1 # ffff <.LASF1709+0x3595>
    sw	t2,44(sp)
    sw	t6,112(a4)
    sw	a7,96(a4)
    sw	zero,80(a4)
    sw	t5,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,40(sp)
    lw	a4,76(a0)
    sw	a4,40(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a7,0xffe80
    addi	t5,a7,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t5)
    lw	a4,0(t5)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t5,4
    sw	t5,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t5,4(a4)
    lui	t5,0x2000
    sw	t5,8(a4)
    sw	t5,12(a4)
    sw	t5,16(a4)
    lui	t6,0x41000
    sw	t6,20(a4)
    lui	t6,0x41008
    sw	t5,24(a4)
    addi	t5,t6,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t5,28(a4)
    lui	t5,0x41010
    sw	t5,32(a4)
    sw	t0,0(a5)
    sw	t4,0(a5)
    sw	t3,0(a5)
    sw	t1,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	a7,a7,4
    sw	a4,0(a7)
    lw	a4,0(a7)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    ttsemwait	1,2,1
    lw	a0,116(a3)
    lui	a7,0x1000
    addi	a4,a0,-1
    slli	t1,a4,0x8
    addi	a7,a7,-256 # ffff00 <.LASF1709+0xff3496>
    srli	a4,a4,0x10
    addi	t3,a6,24
    lui	t4,0x508c0
    slli	a4,a4,0x8
    and	t1,t1,a7
    lui	a7,0x800
    sw	t4,0(a5)
    add	t1,t1,t3
    addi	a6,a6,25
    or	a7,a4,a7
    sw	t1,0(a5)
    add	a7,a7,a6
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a4,a4,a6
    sw	a4,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a4,104(a3)
    lw	a6,100(a3)
    add	a4,a0,a4
    sw	zero,124(a3)
    sw	a4,116(a3)
    bltu	a4,a6,8db8 <.L25>
    lw	a0,96(a3)
    sub	a4,a4,a0
    sw	a4,116(a3)
    lhu	a4,122(a3)
    lui	a6,0x45000
    addi	a4,a4,1
    zext.h	a4,a4
    addi	a6,a6,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a0,a4,0x8
    add	a0,a0,a6
    sh	a4,122(a3)
    sw	a0,0(a5)
    ttstallwait	32,8
    lui	a4,0x67611
    addi	a4,a4,-1014 # 67610c0a <__device_print_strings_info_end+0x61110c0a>
    sw	a4,0(a5)
    lhu	a7,186(a3)
    lw	a6,172(a3)
    lui	a0,0xffb45
    lw	a4,32(a0) # ffb45020 <__fw_export_ldm_end+0x44800>
    add	a4,a6,a4
    zext.h	a4,a4
    beq	a7,a4,8df8 <.L26>
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t6,168(a3)
    lui	a4,0xffef0
    beqz	a0,8e1c <.L27>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a6,0x45000
    addi	t2,a6,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t5,0x45004
    sw	t2,0(a5)
    addi	t5,t5,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t4,0x45040
    sw	t5,0(a5)
    addi	t4,t4,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	t3,0x45100
    sw	t4,0(a5)
    addi	t3,t3,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	t3,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a0,0xb5800
    addi	a0,a0,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a0,0(a5)
    lui	a0,0xb61e0
    addi	a0,a0,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a0,0(a5)
    lui	a0,0xb3fc0
    addi	a0,a0,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    lui	a7,0xb4ff0
    sw	a0,0(a5)
    addi	a0,a7,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a0,0(a5)
    lui	a0,0xb53f0
    addi	a0,a0,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a0,0(a5)
    ttatrelm	0
    lui	a0,0xb5100
    addi	a0,a0,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a0,0(a5)
    lui	a0,0xb6ff0
    addi	a0,a0,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a0,0(a5)
    lui	t1,0x40
    sw	t1,272(a4)
    li	t0,1
    sw	t0,280(a4)
    ttstallwait	128,8
    lui	a0,0xb3040
    addi	a0,a0,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    sw	a0,0(a5)
    lui	a0,0xb5080
    addi	a0,a0,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a0,0(a5)
    sw	t0,72(a4)
    lui	a0,0xffe00
    sw	t1,208(a0) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,52(sp)
    lw	s0,208(a0)
    li	t0,256
    lui	t1,0x10
    addi	t1,t1,-1 # ffff <.LASF1709+0x3595>
    sw	s0,52(sp)
    sw	t0,112(a4)
    sw	t1,96(a4)
    sw	zero,80(a4)
    sw	t6,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,48(sp)
    lw	a4,76(a0)
    sw	a4,48(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	t1,0xffe80
    addi	t6,t1,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t6)
    lw	a4,0(t6)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t6,4
    sw	t6,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t6,4(a4)
    lui	t6,0x2000
    sw	t6,8(a4)
    sw	t6,12(a4)
    sw	t6,16(a4)
    lui	t0,0x41000
    sw	t0,20(a4)
    lui	t0,0x41008
    sw	t6,24(a4)
    addi	t6,t0,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t6,28(a4)
    lui	t6,0x41010
    sw	t6,32(a4)
    sw	t2,0(a5)
    sw	t5,0(a5)
    sw	t4,0(a5)
    sw	t3,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	t1,t1,4
    sw	a4,0(t1)
    lw	a4,0(t1)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    ttsetdmareg	0,0,0,56
    ttsetdmareg	0,170,0,57
    ttsetdmareg	0,1,0,60
    ttsetdmareg	1,5461,0,58
    ttsetdmareg	1,5461,0,59
    ttstallwait	128,8
    lui	a4,0xb4ff1
    addi	a4,a4,28 # b4ff101c <__device_print_strings_info_end+0xaeaf101c>
    sw	a4,0(a5)
    ttwrcfg	28,0,24
    ttwrcfg	30,0,25
    ttwrcfg	29,0,21
    ttnop
    ttnop
    ttsetdmareg	3,16383,0,56
    ttsetdmareg	0,0,0,57
    ttstallwait	128,8
    addi	a7,a7,284
    sw	a7,0(a5)
    ttwrcfg	28,0,24
    ttwrcfg	28,0,25
    ttwrcfg	0,0,20
    ttwrcfg	0,0,21
    ttnop
    ttnop
    ttsemwait	1,2,1
    lw	a0,180(a3)
    lui	a7,0x1000
    addi	a4,a0,-1
    slli	t1,a4,0x8
    addi	a7,a7,-256 # ffff00 <.LASF1709+0xff3496>
    srli	a4,a4,0x10
    addi	t3,a6,24
    lui	t4,0x508c0
    slli	a4,a4,0x8
    and	t1,t1,a7
    lui	a7,0x800
    sw	t4,0(a5)
    add	t1,t1,t3
    addi	a6,a6,25
    or	a7,a4,a7
    sw	t1,0(a5)
    add	a7,a7,a6
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a4,a4,a6
    sw	a4,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a4,168(a3)
    lw	a6,164(a3)
    add	a4,a0,a4
    sw	zero,188(a3)
    sw	a4,180(a3)
    bltu	a4,a6,90f8 <.L28>
    lw	a0,160(a3)
    sub	a4,a4,a0
    sw	a4,180(a3)
    lhu	a4,186(a3)
    lui	a6,0x45000
    addi	a4,a4,1
    zext.h	a4,a4
    addi	a6,a6,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a0,a4,0x8
    add	a0,a0,a6
    sh	a4,186(a3)
    sw	a0,0(a5)
    ttstallwait	32,8
    lui	a4,0x67611
    addi	a4,a4,1034 # 6761140a <__device_print_strings_info_end+0x6111140a>
    sw	a4,0(a5)
    lhu	t1,90(a3)
    lw	a7,76(a3)
    lui	a6,0xffb42
    li	a0,3
    lw	a4,32(a6) # ffb42020 <__fw_export_ldm_end+0x41800>
    add	a4,a7,a4
    sub	a4,a4,t1
    zext.h	a4,a4
    bgeu	a0,a4,913c <.L29>
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t5,72(a3)
    lui	a4,0xffef0
    beqz	a0,9164 <.L30>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	t4,0x45000
    addi	t4,t4,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t3,0x45004
    sw	t4,0(a5)
    addi	t3,t3,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t1,0x45040
    sw	t3,0(a5)
    addi	t1,t1,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	a7,0x45100
    sw	t1,0(a5)
    addi	a7,a7,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a0,0xb5800
    addi	a0,a0,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a0,0(a5)
    lui	a0,0xb61e0
    addi	a0,a0,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a0,0(a5)
    lui	a0,0xb3fc0
    addi	a0,a0,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a0,0(a5)
    lui	a0,0xb4ff0
    addi	a0,a0,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a0,0(a5)
    lui	a0,0xb53f0
    addi	a0,a0,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a0,0(a5)
    ttatrelm	0
    lui	a0,0xb5100
    addi	a0,a0,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a0,0(a5)
    lui	a0,0xb6ff0
    addi	a0,a0,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a0,0(a5)
    lui	t6,0x40
    sw	t6,272(a4)
    li	t0,1
    sw	t0,280(a4)
    ttstallwait	128,8
    lui	a6,0xb3040
    addi	a6,a6,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    lui	a0,0xb5080
    sw	a6,0(a5)
    addi	a0,a0,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a0,0(a5)
    sw	t0,72(a4)
    lui	a0,0xffe00
    sw	t6,208(a0) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,60(sp)
    lw	t0,208(a0)
    li	t6,256
    lui	a6,0x10
    addi	a6,a6,-1 # ffff <.LASF1709+0x3595>
    sw	t0,60(sp)
    sw	t6,112(a4)
    sw	a6,96(a4)
    sw	zero,80(a4)
    sw	t5,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,56(sp)
    lw	a4,76(a0)
    sw	a4,56(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a6,0xffe80
    addi	t5,a6,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t5)
    lw	a4,0(t5)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t5,4
    sw	t5,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t5,4(a4)
    lui	t5,0x2000
    sw	t5,8(a4)
    sw	t5,12(a4)
    sw	t5,16(a4)
    lui	t6,0x41000
    sw	t6,20(a4)
    lui	t6,0x41008
    sw	t5,24(a4)
    addi	t5,t6,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t5,28(a4)
    lui	t5,0x41010
    sw	t5,32(a4)
    sw	t4,0(a5)
    sw	t3,0(a5)
    sw	t1,0(a5)
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	a6,a6,4
    sw	a4,0(a6)
    lw	a4,0(a6)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t5,72(a3)
    lui	a4,0xffef0
    beqz	a0,9358 <.L31>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	t4,0x45000
    addi	t4,t4,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t3,0x45004
    sw	t4,0(a5)
    addi	t3,t3,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t1,0x45040
    sw	t3,0(a5)
    addi	t1,t1,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	a7,0x45100
    sw	t1,0(a5)
    addi	a7,a7,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a0,0xb5800
    addi	a0,a0,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a0,0(a5)
    lui	a0,0xb61e0
    addi	a0,a0,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a0,0(a5)
    lui	a0,0xb3fc0
    addi	a0,a0,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a0,0(a5)
    lui	a0,0xb4ff0
    addi	a0,a0,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a0,0(a5)
    lui	a0,0xb53f0
    addi	a0,a0,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a0,0(a5)
    ttatrelm	0
    lui	a0,0xb5100
    addi	a0,a0,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a0,0(a5)
    lui	a0,0xb6ff0
    addi	a0,a0,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a0,0(a5)
    lui	t6,0x40
    sw	t6,272(a4)
    li	t0,1
    sw	t0,280(a4)
    ttstallwait	128,8
    lui	a6,0xb3040
    addi	a6,a6,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    lui	a0,0xb5080
    sw	a6,0(a5)
    addi	a0,a0,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a0,0(a5)
    sw	t0,72(a4)
    lui	a0,0xffe00
    sw	t6,208(a0) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,68(sp)
    lw	t0,208(a0)
    li	t6,256
    lui	a6,0x10
    addi	a6,a6,-1 # ffff <.LASF1709+0x3595>
    sw	t0,68(sp)
    sw	t6,112(a4)
    sw	a6,96(a4)
    sw	zero,80(a4)
    sw	t5,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,64(sp)
    lw	a4,76(a0)
    sw	a4,64(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a6,0xffe80
    addi	t5,a6,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t5) # 41010000 <__device_print_strings_info_end+0x3ab10000>
    lw	a4,0(t5)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t5,4
    sw	t5,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t5,4(a4)
    lui	t5,0x2000
    sw	t5,8(a4)
    sw	t5,12(a4)
    sw	t5,16(a4)
    lui	t6,0x41000
    sw	t6,20(a4)
    lui	t6,0x41008
    sw	t5,24(a4)
    addi	t5,t6,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t5,28(a4)
    lui	t5,0x41010
    sw	t5,32(a4)
    sw	t4,0(a5)
    sw	t3,0(a5)
    sw	t1,0(a5)
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	a6,a6,4
    sw	a4,0(a6)
    lw	a4,0(a6)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    lw	a2,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t4,72(a3)
    lui	a4,0xffef0
    beqz	a2,954c <.L32>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a2,0x45000
    addi	t6,a2,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t3,0x45004
    sw	t6,0(a5)
    addi	t3,t3,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	t1,0x45040
    sw	t3,0(a5)
    addi	t1,t1,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	a7,0x45100
    sw	t1,0(a5)
    addi	a7,a7,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a0,0xb5800
    addi	a0,a0,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a0,0(a5)
    lui	a0,0xb61e0
    addi	a0,a0,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a0,0(a5)
    lui	a0,0xb3fc0
    addi	a0,a0,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a0,0(a5)
    lui	a0,0xb4ff0
    addi	a0,a0,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a0,0(a5)
    lui	a0,0xb53f0
    addi	a0,a0,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a0,0(a5)
    ttatrelm	0
    lui	a0,0xb5100
    addi	a0,a0,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a0,0(a5)
    lui	a0,0xb6ff0
    addi	a0,a0,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a0,0(a5)
    lui	t5,0x40
    sw	t5,272(a4)
    li	t0,1
    sw	t0,280(a4)
    ttstallwait	128,8
    lui	a6,0xb3040
    addi	a6,a6,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    lui	a0,0xb5080
    sw	a6,0(a5)
    addi	a0,a0,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a0,0(a5)
    sw	t0,72(a4)
    lui	a0,0xffe00
    sw	t5,208(a0) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,76(sp)
    lw	t0,208(a0)
    li	t5,256
    lui	a6,0x10
    addi	a6,a6,-1 # ffff <.LASF1709+0x3595>
    sw	t0,76(sp)
    sw	t5,112(a4)
    sw	a6,96(a4)
    sw	zero,80(a4)
    sw	t4,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,72(sp)
    lw	a4,76(a0)
    sw	a4,72(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a6,0xffe80
    addi	t4,a6,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t4)
    lw	a4,0(t4)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t4,4
    sw	t4,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t4,4(a4)
    lui	t4,0x2000
    sw	t4,8(a4)
    sw	t4,12(a4)
    sw	t4,16(a4)
    lui	t5,0x41000
    sw	t5,20(a4)
    lui	t5,0x41008
    sw	t4,24(a4)
    addi	t4,t5,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t4,28(a4)
    lui	t4,0x41010
    sw	t4,32(a4)
    sw	t6,0(a5)
    sw	t3,0(a5)
    sw	t1,0(a5)
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    addi	a6,a6,4
    sw	a4,0(a6)
    lw	a4,0(a6)
    and	zero,zero,a4
    sw	zero,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    ttwrcfg	4,1,180
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    ttsemwait	1,2,1
    lw	t3,84(a3)
    lui	t1,0x1000
    addi	a4,t3,-1
    slli	a0,a4,0x8
    addi	t1,t1,-256 # ffff00 <.LASF1709+0xff3496>
    addi	t4,a2,24
    srli	a1,a4,0x10
    and	a0,a0,t1
    lui	a7,0x508c0
    add	a0,a0,t4
    sw	a7,0(a5)
    slli	a1,a1,0x8
    lui	a6,0x800
    sw	a0,0(a5)
    addi	a2,a2,25
    or	a0,a1,a6
    add	a0,a0,a2
    sw	a0,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a1,a1,a2
    sw	a1,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    lw	a1,72(a3)
    addi	a0,a7,2 # 508c0002 <__device_print_strings_info_end+0x4a3c0002>
    add	t3,t3,a1
    sw	a0,0(a5)
    addi	a0,t3,-1
    slli	t5,a0,0x8
    srli	a0,a0,0x10
    and	t5,t5,t1
    slli	a0,a0,0x8
    add	t5,t5,t4
    or	t6,a0,a6
    sw	t5,0(a5)
    add	t5,t6,a2
    sw	t5,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a0,a0,a2
    sw	a0,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    sh1add	a4,a1,a4
    slli	t5,a4,0x8
    srli	a0,a4,0x10
    addi	t6,a7,4
    and	t5,t5,t1
    slli	a0,a0,0x8
    sw	t6,0(a5)
    add	t5,t5,t4
    or	t6,a0,a6
    sw	t5,0(a5)
    add	t5,t6,a2
    sw	t5,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a0,a0,a2
    sw	a0,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    add	a4,a1,a4
    slli	a0,a4,0x8
    srli	a4,a4,0x10
    addi	a7,a7,6
    and	a0,a0,t1
    slli	a4,a4,0x8
    sw	a7,0(a5)
    add	a0,a0,t4
    or	a6,a4,a6
    sw	a0,0(a5)
    add	a6,a6,a2
    sw	a6,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a4,a4,a2
    sw	a4,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    sh1add	a1,a1,a1
    lw	a4,68(a3)
    add	a1,a1,t3
    sw	a1,84(a3)
    sw	zero,92(a3)
    bltu	a1,a4,98b0 <.L33>
    lw	a4,64(a3)
    sub	a1,a1,a4
    sw	a1,84(a3)
    lhu	a4,90(a3)
    lui	a1,0x45000
    addi	a4,a4,4
    zext.h	a4,a4
    addi	a1,a1,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a2,a4,0x8
    add	a2,a2,a1
    sh	a4,90(a3)
    sw	a2,0(a5)
    ttstallwait	32,8
    lui	a4,0x67611
    lw	s0,92(sp)
    addi	a4,a4,-2038 # 6761080a <__device_print_strings_info_end+0x6111080a>
    sw	a4,0(a5)
    li	a0,0
    addi	sp,sp,96
    ret
    mv	a5,a3
    j	7e84 <.L4>
