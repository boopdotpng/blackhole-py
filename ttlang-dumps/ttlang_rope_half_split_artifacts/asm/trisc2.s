    addi	sp,sp,-16
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
    bltu	a4,a3,8534 <.L20>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,7e88 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,1716 # 853c <__kernel_data_lma>
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
    lw	a4,1312(zero) # 520 <.LLST104+0x7>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7f18 <.L11>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7f0c <.L12>
    lui	a3,0xffb00
    addi	a3,a3,32 # ffb00020 <cb_interface>
    lhu	a1,218(a3)
    lw	a2,204(a3)
    lui	a4,0xffb46
    lw	a5,32(a4) # ffb46020 <__fw_export_ldm_end+0x45800>
    add	a5,a2,a5
    zext.h	a5,a5
    beq	a1,a5,7f2c <.L13>
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t4,200(a3)
    lui	a4,0xffef0
    beqz	a5,7f50 <.L14>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a1,0x45000
    lui	a5,0xffe40
    mv	a5,a5
    addi	t6,a1,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t3,0x45002
    sw	t6,0(a5) # ffe40000 <__instrn_buffer>
    addi	t3,t3,57 # 45002039 <__device_print_strings_info_end+0x3eb02039>
    lui	t1,0x45020
    sw	t3,0(a5)
    addi	t1,t1,58 # 4502003a <__device_print_strings_info_end+0x3eb2003a>
    lui	a6,0x45080
    sw	t1,0(a5)
    addi	a6,a6,59 # 4508003b <__device_print_strings_info_end+0x3eb8003b>
    sw	a6,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a2,0xb5800
    addi	a2,a2,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a2,0(a5)
    lui	a2,0xb61e1
    addi	a2,a2,-1535 # b61e0a01 <__device_print_strings_info_end+0xafce0a01>
    sw	a2,0(a5)
    lui	a2,0xb3fc0
    addi	a2,a2,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a2,0(a5)
    lui	a2,0xb4ff0
    addi	a2,a2,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a2,0(a5)
    lui	a2,0xb53f0
    addi	a2,a2,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a2,0(a5)
    ttatrelm	0
    lui	a2,0xb5100
    addi	a2,a2,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a2,0(a5)
    lui	a2,0xb6ff0
    addi	a2,a2,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a2,0(a5)
    lui	a0,0x40
    sw	a0,272(a4)
    li	a2,1361
    sw	a2,280(a4)
    ttstallwait	128,8
    lui	a2,0xb3040
    addi	a2,a2,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    sw	a2,0(a5)
    lui	a2,0xb5080
    addi	a2,a2,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a2,0(a5)
    sw	zero,72(a4)
    lui	a2,0xffe00
    sw	a0,208(a2) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,4(sp)
    lw	t0,208(a2)
    li	t5,256
    lui	a0,0x10
    addi	a0,a0,-1 # ffff <.LASF564+0x70e5>
    sw	t0,4(sp)
    sw	t5,112(a4)
    sw	a0,96(a4)
    sw	zero,80(a4)
    sw	t4,64(a2)
    sw	zero,68(a2)
    sw	zero,72(a2)
    sw	zero,76(a2)
    sw	zero,0(sp)
    lw	a4,76(a2)
    sw	a4,0(sp)
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
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    lui	a4,0xb0048
    addi	a4,a4,180 # b00480b4 <__device_print_strings_info_end+0xa9b480b4>
    sw	a4,0(a5)
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    ttsemwait	1,2,1
    lw	a2,212(a3)
    lui	a0,0x1000
    addi	a4,a2,-1
    slli	a6,a4,0x8
    addi	a0,a0,-256 # ffff00 <.LASF564+0xff6fe6>
    srli	a4,a4,0x10
    addi	t1,a1,24
    lui	t3,0x508c0
    slli	a4,a4,0x8
    and	a6,a6,a0
    lui	a0,0x800
    sw	t3,0(a5)
    add	a6,a6,t1
    addi	a1,a1,25
    or	a0,a4,a0
    sw	a6,0(a5)
    add	a0,a0,a1
    sw	a0,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a4,a4,a1
    sw	a4,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    lui	a4,0x10104
    sw	a4,0(a5)
    ttsemget	2
    lui	a4,0xb0088
    addi	a4,a4,180 # b00880b4 <__device_print_strings_info_end+0xa9b880b4>
    sw	a4,0(a5)
    li	a4,1
    sw	a4,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    ttdmanop
    ttdmanop
    lw	a4,200(a3)
    lw	a1,196(a3)
    add	a4,a2,a4
    sw	zero,220(a3)
    sw	a4,212(a3)
    bltu	a4,a1,81f4 <.L15>
    lw	a2,192(a3)
    sub	a4,a4,a2
    sw	a4,212(a3)
    lhu	a4,218(a3)
    lui	a1,0x45000
    addi	a4,a4,1
    zext.h	a4,a4
    addi	a1,a1,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a2,a4,0x8
    add	a2,a2,a1
    sh	a4,218(a3)
    sw	a2,0(a5)
    ttstallwait	32,8
    lui	a4,0x67612
    addi	a4,a4,-2038 # 6761180a <__device_print_strings_info_end+0x6111180a>
    sw	a4,0(a5)
    lhu	a0,250(a3)
    lw	a1,236(a3)
    lui	a2,0xffb47
    lw	a4,32(a2) # ffb47020 <__fw_export_ldm_end+0x46800>
    add	a4,a1,a4
    zext.h	a4,a4
    beq	a0,a4,8234 <.L16>
    lw	a2,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	t4,232(a3)
    lui	a4,0xffef0
    beqz	a2,8258 <.L17>
    addi	a4,a4,896 # ffef0380 <__instrn_buffer+0xb0380>
    lui	a1,0x45000
    addi	t6,a1,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	t3,0x45002
    sw	t6,0(a5)
    addi	t3,t3,57 # 45002039 <__device_print_strings_info_end+0x3eb02039>
    lui	t1,0x45020
    sw	t3,0(a5)
    addi	t1,t1,58 # 4502003a <__device_print_strings_info_end+0x3eb2003a>
    lui	a7,0x45080
    sw	t1,0(a5)
    addi	a7,a7,59 # 4508003b <__device_print_strings_info_end+0x3eb8003b>
    sw	a7,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lui	a2,0xb5800
    addi	a2,a2,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    sw	a2,0(a5)
    lui	a2,0xb61e1
    addi	a2,a2,-1535 # b61e0a01 <__device_print_strings_info_end+0xafce0a01>
    sw	a2,0(a5)
    lui	a2,0xb3fc0
    addi	a2,a2,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a2,0(a5)
    lui	a2,0xb4ff0
    addi	a2,a2,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a2,0(a5)
    lui	a2,0xb53f0
    addi	a2,a2,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a2,0(a5)
    ttatrelm	0
    lui	a2,0xb5100
    addi	a2,a2,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    sw	a2,0(a5)
    lui	a2,0xb6ff0
    addi	a2,a2,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    sw	a2,0(a5)
    lui	a0,0x40
    sw	a0,272(a4)
    li	a2,1361
    sw	a2,280(a4)
    ttstallwait	128,8
    lui	a2,0xb3040
    addi	a2,a2,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    sw	a2,0(a5)
    lui	a2,0xb5080
    addi	a2,a2,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a2,0(a5)
    sw	zero,72(a4)
    lui	a2,0xffe00
    sw	a0,208(a2) # ffe000d0 <__fw_export_ldm_end+0x2ff8b0>
    sw	zero,12(sp)
    lw	t0,208(a2)
    li	t5,256
    lui	a0,0x10
    addi	a0,a0,-1 # ffff <.LASF564+0x70e5>
    sw	t0,12(sp)
    sw	t5,112(a4)
    sw	a0,96(a4)
    sw	zero,80(a4)
    sw	t4,64(a2)
    sw	zero,68(a2)
    sw	zero,72(a2)
    sw	zero,76(a2)
    sw	zero,8(sp)
    lw	a4,76(a2)
    sw	a4,8(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a0,0xffe80
    addi	t4,a0,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a4,0
    sw	a4,0(t4) # 41010000 <__device_print_strings_info_end+0x3ab10000>
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
    ttstallwait	33,8
    ttsetdmareg	0,0,0,8
    ttsetdmareg	0,512,0,16
    ttstallwait	128,1
    lui	a4,0xb0048
    addi	a4,a4,180 # b00480b4 <__device_print_strings_info_end+0xa9b480b4>
    sw	a4,0(a5)
    ttdmanop
    ttdmanop
    ttsetadcxy	4,0,0,0,0,11
    ttsetadczw	4,0,0,0,0,15
    ttsemwait	1,2,1
    lw	a2,244(a3)
    lui	a0,0x1000
    addi	a4,a2,-1
    slli	a7,a4,0x8
    addi	a0,a0,-256 # ffff00 <.LASF564+0xff6fe6>
    srli	a4,a4,0x10
    addi	t1,a1,24
    lui	t3,0x508c0
    slli	a4,a4,0x8
    and	a7,a7,a0
    lui	a0,0x800
    sw	t3,0(a5)
    add	a7,a7,t1
    addi	a1,a1,25
    or	a0,a4,a0
    sw	a7,0(a5)
    add	a0,a0,a1
    sw	a0,0(a5)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a4,a4,a1
    sw	a4,0(a5)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    lui	a4,0x10104
    sw	a4,0(a5)
    ttsemget	2
    li	a1,1
    lui	a4,0xb0088
    addi	a4,a4,180 # b00880b4 <__device_print_strings_info_end+0xa9b880b4>
    sw	a1,-2032(gp) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    sw	a4,0(a5)
    ttdmanop
    ttdmanop
    lw	a4,232(a3)
    lw	a1,228(a3)
    add	a4,a2,a4
    sw	zero,252(a3)
    sw	a4,244(a3)
    bltu	a4,a1,84f4 <.L18>
    lw	a2,224(a3)
    sub	a4,a4,a2
    sw	a4,244(a3)
    lhu	a4,250(a3)
    lui	a1,0x45000
    addi	a4,a4,1
    zext.h	a4,a4
    addi	a1,a1,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a2,a4,0x8
    add	a2,a2,a1
    sh	a4,250(a3)
    sw	a2,0(a5)
    ttstallwait	32,8
    lui	a4,0x67612
    addi	a4,a4,-1014 # 67611c0a <__device_print_strings_info_end+0x61111c0a>
    sw	a4,0(a5)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	7e7c <.L4>
