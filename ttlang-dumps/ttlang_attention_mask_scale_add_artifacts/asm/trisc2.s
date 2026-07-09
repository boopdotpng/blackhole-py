    addi	sp,sp,-32
    lui	a5,0xffb01
    addi	a5,a5,-2000 # ffb00830 <__fw_export_ldm_end+0x10>
    addi	a4,gp,48 # ffb00820 <__fw_export_ldm_end>
    bltu	a4,a5,7e6c <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,7e54 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,8328 <.L17>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,7e88 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,1192 # 8330 <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <__fw_export_ldm_end>
    beq	a4,a5,7ef4 <.L7>
    addi	a2,gp,48 # ffb00820 <__fw_export_ldm_end>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,7ed8 <.L8>
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
    blt	a6,a3,7eb0 <.L9>
    blez	a3,7ef4 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,7ef4 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LASF606+0x1>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7f18 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7f0c <.L11>
    lui	a3,0xffb00
    addi	a3,a3,32 # ffb00020 <cb_interface>
    lhu	a0,90(a3)
    lw	a1,76(a3)
    lui	a2,0xffb42
    li	a4,3
    lw	a5,32(a2) # ffb42020 <__fw_export_ldm_end+0x41800>
    add	a5,a1,a5
    sub	a5,a5,a0
    zext.h	a5,a5
    bgeu	a4,a5,7f30 <.L12>
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t3,72(a3)
    lui	a4,0xffef0
    beqz	a5,7f58 <.L14>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a2,0x45000
    lui	a5,0xffe40
    mv	a5,a5
    addi	t4,a2,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t1,0x45004
    sw	t4,0(a5) # ffe40000 <__instrn_buffer>
    addi	t1,t1,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	a7,0x45040
    sw	t1,0(a5)
    addi	a7,a7,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	a6,0x45100
    sw	a7,0(a5)
    addi	a6,a6,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a6,0(a5)
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
    li	t6,1
    sw	t6,280(a4)
    ttstallwait	128,8
    lui	a0,0xb3040
    addi	a0,a0,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    lui	a1,0xb5080
    sw	a0,0(a5)
    addi	a1,a1,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a1,0(a5)
    sw	t6,72(a4)
    lui	a1,0xffe00
    sw	t5,208(a1) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,28(sp)
    lw	t6,208(a1)
    li	t5,256
    lui	a0,0x10
    addi	a0,a0,-1 # ffff <.LASF554+0x734e>
    sw	t6,28(sp)
    sw	t5,112(a4)
    sw	a0,96(a4)
    sw	zero,80(a4)
    sw	t3,64(a1)
    sw	zero,68(a1)
    sw	zero,72(a1)
    sw	zero,76(a1)
    sw	zero,24(sp)
    lw	a4,76(a1)
    sw	a4,24(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a0,0xffe80
    addi	t3,a0,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t3)
    lw	a4,0(t3)
    and	zero,zero,a4
    lui	a4,0xffb80
    li	t3,4
    sw	t3,0(a4) # ffb80000 <__fw_export_ldm_end+0x7f7e0>
    sw	t3,4(a4)
    lui	t3,0x2000
    sw	t3,8(a4)
    sw	t3,12(a4)
    sw	t3,16(a4)
    lui	t5,0x41000
    sw	t5,20(a4)
    sw	t3,24(a4)
    lui	t3,0x41008
    addi	t3,t3,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	t3,28(a4)
    lui	t3,0x41010
    sw	t3,32(a4)
    sw	t4,0(a5)
    sw	t1,0(a5)
    sw	a7,0(a5)
    sw	a6,0(a5)
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
    lui	a4,0x3e000
    sw	a4,20(sp)
    lw	a1,20(sp)
    sw	a4,16(sp)
    lw	a1,16(sp)
    sw	a4,12(sp)
    lw	a1,12(sp)
    sw	a4,8(sp)
    lw	a4,8(sp)
    ttsemwait	1,2,1
    lw	t3,84(a3)
    lui	t1,0x1000
    addi	a4,t3,-1 # 4100ffff <__device_print_strings_info_end+0x3ab0ffff>
    slli	a0,a4,0x8
    addi	t1,t1,-256 # ffff00 <.LASF554+0xff724f>
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
    bltu	a1,a4,82e8 <.L15>
    lw	a4,64(a3)
    sub	a1,a1,a4
    sw	a1,84(a3)
    lhu	a4,90(a3)
    lui	a1,0x45000
    addi	a4,a4,4 # 3e000004 <__device_print_strings_info_end+0x37b00004>
    zext.h	a4,a4
    addi	a1,a1,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a2,a4,0x8
    add	a2,a2,a1
    sh	a4,90(a3)
    sw	a2,0(a5)
    ttstallwait	32,8
    lui	a4,0x67611
    addi	a4,a4,-2038 # 6761080a <__device_print_strings_info_end+0x6111080a>
    sw	a4,0(a5)
    li	a0,0
    addi	sp,sp,32
    ret
    mv	a5,a3
    j	7e7c <.L4>
