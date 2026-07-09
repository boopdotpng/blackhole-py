    addi	sp,sp,-16
    sw	ra,12(sp)
    lui	a5,0xffb01
    addi	a5,a5,-1808 # ffb008f0 <__ldm_bss_end+0x10>
    addi	a4,gp,240 # ffb008e0 <__ldm_bss_end>
    bltu	a4,a5,7e70 <.L108>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,7e58 <.L109>
    addi	a3,a5,-8
    bltu	a4,a3,7f34 <.L120>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,7e8c <.L111>
    sw	zero,-8(a5)
    auipc	a4,0x2
    addi	a4,a4,1048 # a2a4 <__kernel_data_lma>
    addi	a5,gp,48 # ffb00820 <_ZL19pack_tile_num_faces>
    beq	a4,a5,7efc <.L113>
    lui	a2,0xffb01
    addi	a2,a2,-1824 # ffb008e0 <__ldm_bss_end>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,7ee0 <.L114>
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
    blt	a6,a3,7eb8 <.L115>
    blez	a3,7efc <.L113>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,7efc <.L113>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lw	a4,1312(zero) # 520 <.LASF936+0x1>
    li	a3,128
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    addi	a4,a4,96
    beq	a5,a3,7f20 <.L117>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,7f14 <.L118>
    jal	8270 <_Z11kernel_mainv>
    lw	ra,12(sp)
    li	a0,0
    addi	sp,sp,16
    ret
    mv	a5,a3
    j	7e80 <.L110>
    lui	a4,0xffe80
    li	a5,0
    addi	a4,a4,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
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
    ret
    lui	a3,0xffb00
    slli	a1,a0,0x5
    addi	a3,a3,32 # ffb00020 <cb_interface>
    addi	a5,gp,48 # ffb00820 <_ZL19pack_tile_num_faces>
    addi	a4,gp,176 # ffb008a0 <_ZL15pack_dst_format>
    lw	a2,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    add	a5,a5,a0
    add	a3,a3,a1
    add	a4,a4,a0
    lw	a6,8(a3)
    lbu	a0,0(a4)
    lbu	t1,0(a5)
    lbu	a7,64(a5)
    lbu	a1,128(a5)
    addi	sp,sp,-16
    lui	a3,0xffef0
    beqz	a2,7fc8 <.L4>
    addi	a3,a3,896 # ffef0380 <__instrn_buffer+0xb0380>
    andi	a5,a1,3
    beqz	a5,7ff4 <.L17>
    li	a4,1
    beq	a5,a4,8254 <.L28>
    lui	a2,0x45040
    lui	t3,0x45010
    lui	t4,0x45001
    addi	a2,a2,59 # 4504003b <__device_print_strings_info_end+0x3eb4003b>
    addi	t3,t3,58 # 4501003a <__device_print_strings_info_end+0x3eb1003a>
    addi	t4,t4,57 # 45001039 <__device_print_strings_info_end+0x3eb01039>
    j	800c <.L5>
    lui	a2,0x45100
    lui	t3,0x45040
    lui	t4,0x45004
    addi	a2,a2,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    addi	t3,t3,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    addi	t4,t4,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	a5,0xffe40
    lui	a4,0x45000
    mv	a5,a5
    addi	a4,a4,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    sw	a4,0(a5) # ffe40000 <__instrn_buffer>
    sw	t4,0(a5)
    sw	t3,0(a5)
    sw	a2,0(a5)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    andi	t3,a0,31
    addi	a2,t3,-26
    slli	a4,a1,0x19
    seqz	a2,a2
    lui	t6,0xb5800
    lui	t5,0x2
    addi	t6,t6,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    addi	t5,t5,-512 # 1e00 <.LVUS406+0x3>
    slli	a2,a2,0xf
    srli	a4,a4,0x10
    lui	t4,0xb61e0
    add	a2,a2,t6
    and	a4,a4,t5
    addi	t4,t4,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    sw	a2,0(a5)
    add	a4,a4,t4
    sw	a4,0(a5)
    lui	a4,0xb3fc0
    addi	a4,a4,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    sw	a4,0(a5)
    lui	a4,0xb4ff0
    addi	a4,a4,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    sw	a4,0(a5)
    lui	a4,0xb53f0
    addi	a4,a4,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    sw	a4,0(a5)
    ttatrelm	0
    li	a2,26
    andi	t6,a1,15
    mv	a4,a1
    bne	t3,a2,80c4 <.L6>
    li	a4,1
    sw	zero,4(sp)
    sw	zero,12(sp)
    andi	a2,a0,11
    li	t5,10
    li	t4,0
    beq	a2,t5,80e4 <.L7>
    li	t4,1
    beqz	a7,821c <.L29>
    andi	t0,a0,15
    andi	a2,a4,15
    slli	a4,t0,0x4
    slli	a2,a2,0x8
    ori	a4,a4,1
    or	a4,a4,a2
    sh	t4,6(sp)
    lhu	a2,12(sp)
    lui	t5,0x1
    lui	t4,0xfffff
    addi	t5,t5,-15 # ff1 <.LVUS195>
    addi	t4,t4,14 # fffff00e <__instrn_buffer+0x1bf00e>
    and	a4,a4,t5
    and	a2,a2,t4
    or	a4,a4,a2
    sh	a4,12(sp)
    andi	a4,a0,12
    bnez	a4,8200 <.L8>
    andi	a4,a0,14
    beqz	a4,8208 <.L23>
    lui	a4,0xb6ff7
    lui	a2,0xb5101
    addi	a4,a4,327 # b6ff7147 <__device_print_strings_info_end+0xb0af7147>
    addi	a2,a2,71 # b5101047 <__device_print_strings_info_end+0xaec01047>
    sw	a2,0(a5)
    lw	a2,4(sp)
    sw	a4,0(a5)
    lw	a4,12(sp)
    sw	a2,272(a3)
    sw	a4,280(a3)
    ttstallwait	128,8
    lui	a2,0xb3040
    addi	a2,a2,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    lui	a4,0xb5080
    sw	a2,0(a5)
    addi	a4,a4,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    sw	a4,0(a5)
    li	a4,30
    li	a5,1
    beq	a0,a4,8224 <.L30>
    beq	a1,a5,819c <.L11>
    andi	a1,a1,12
    bnez	a1,8238 <.L12>
    bnez	t6,81a0 <.L13>
    li	a4,26
    bne	t3,a4,81a0 <.L13>
    ori	a5,a5,8
    sw	a5,72(a3)
    lui	a4,0x10
    bnez	a7,81b0 <.L15>
    slli	a4,t1,0x10
    lui	a5,0xffe00
    sw	a4,208(a5) # ffe000d0 <__ldm_bss_end+0x2ff7f0>
    sw	zero,0(sp)
    lw	a1,208(a5)
    li	a2,256
    lui	a4,0x10
    addi	a4,a4,-1 # ffff <trisck.cc.a8a8fe81+0x348b>
    sw	a1,0(sp)
    sw	a2,112(a3)
    sw	a4,96(a3)
    sw	zero,80(a3)
    sw	a6,64(a5)
    sw	zero,68(a5)
    sw	zero,72(a5)
    sw	zero,76(a5)
    sw	zero,4(sp)
    lw	a5,76(a5)
    sw	a5,4(sp)
    addi	sp,sp,16
    ret
    li	a4,11
    beq	t0,a4,8134 <.L27>
    lui	a4,0xb6ff0
    lui	a2,0xb5100
    addi	a4,a4,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    addi	a2,a2,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    j	8144 <.L9>
    mv	t4,t1
    j	80e4 <.L7>
    mv	a4,a5
    li	a5,3
    beq	a1,a4,819c <.L11>
    andi	a1,a1,12
    beqz	a1,81a0 <.L13>
    addi	t6,t6,-10
    zext.b	t6,t6
    li	a4,1
    bgeu	a4,t6,81a0 <.L13>
    li	a4,26
    bne	t3,a4,81a0 <.L13>
    j	819c <.L11>
    lui	a2,0x45080
    lui	t3,0x45020
    lui	t4,0x45002
    addi	a2,a2,59 # 4508003b <__device_print_strings_info_end+0x3eb8003b>
    addi	t3,t3,58 # 4502003a <__device_print_strings_info_end+0x3eb2003a>
    addi	t4,t4,57 # 45002039 <__device_print_strings_info_end+0x3eb02039>
    j	800c <.L5>
    addi	sp,sp,-176
    lui	a5,0xffb00
    sw	s5,148(sp)
    addi	s5,a5,32 # ffb00020 <cb_interface>
    lhu	a2,186(s5)
    lw	a3,172(s5)
    sw	ra,172(sp)
    sw	s0,168(sp)
    sw	s1,164(sp)
    sw	s2,160(sp)
    sw	s3,156(sp)
    sw	s4,152(sp)
    sw	s6,144(sp)
    sw	s7,140(sp)
    sw	s8,136(sp)
    sw	s9,132(sp)
    sw	s10,128(sp)
    sw	s11,124(sp)
    lui	a4,0xffb45
    lw	a5,32(a4) # ffb45020 <__ldm_bss_end+0x44740>
    add	a5,a3,a5
    zext.h	a5,a5
    beq	a2,a5,82bc <.L32>
    lhu	a2,346(s5)
    lw	a3,332(s5)
    lui	a4,0xffb4a
    lw	a5,32(a4) # ffb4a020 <__ldm_bss_end+0x49740>
    add	a5,a3,a5
    zext.h	a5,a5
    beq	a2,a5,82d8 <.L33>
    li	a0,10
    jal	7f80 <_Z21llk_pack_hw_configureILb1EEvm>
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a4,0xffe80
    li	a5,0
    addi	a4,a4,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a5,0(a4)
    lw	a5,0(a4)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a4,4
    sw	a4,0(a5) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	a4,4(a5)
    lui	a4,0x2000
    sw	a4,8(a5)
    sw	a4,12(a5)
    sw	a4,16(a5)
    lui	a3,0x41000
    sw	a3,20(a5)
    sw	a4,24(a5)
    lui	a4,0x41008
    addi	a4,a4,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	a4,28(a5)
    lui	a4,0x41010
    sw	a4,32(a5)
    lui	s0,0x45000
    lui	a5,0xffe40
    mv	s7,a5
    addi	a5,s0,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    sw	a5,0(s7)
    lui	a5,0x45004
    addi	a5,a5,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    sw	a5,0(s7)
    lui	a5,0x45040
    addi	a5,a5,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    sw	a5,0(s7)
    lui	a5,0x45100
    addi	a5,a5,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a5,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    jal	7f3c <_Z20_llk_pack_dest_init_ILN7ckernel7DstSyncE1ELb1EEvv>
    ttsemwait	1,2,1
    lw	a4,340(s5)
    lui	a3,0x1000
    addi	a5,a4,-1 # 4100ffff <__device_print_strings_info_end+0x3ab0ffff>
    slli	a2,a5,0x8
    addi	a3,a3,-256 # ffff00 <trisck.cc.a8a8fe81+0xff338c>
    srli	a5,a5,0x10
    addi	a1,s0,24
    lui	a0,0x508c0
    slli	a5,a5,0x8
    and	a2,a2,a3
    lui	a3,0x800
    sw	a0,0(s7)
    add	a2,a2,a1
    addi	s0,s0,25
    or	a3,a5,a3
    sw	a2,0(s7)
    add	a3,a3,s0
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,s0
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,328(s5)
    lw	a3,324(s5)
    add	a5,a4,a5
    sw	zero,348(s5)
    sw	a5,340(s5)
    bltu	a5,a3,8440 <.L34>
    lw	a4,320(s5)
    sub	a5,a5,a4
    sw	a5,340(s5)
    lhu	a5,346(s5)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a4,a5,0x8
    add	a4,a4,a3
    sh	a5,346(s5)
    sw	a4,0(s7)
    ttstallwait	32,8
    lui	a5,0x67613
    addi	a5,a5,-2038 # 6761280a <__device_print_strings_info_end+0x6111280a>
    sw	a5,0(s7)
    lhu	a2,378(s5)
    lw	a3,364(s5)
    lui	a4,0xffb4b
    lw	a5,32(a4) # ffb4b020 <__ldm_bss_end+0x4a740>
    add	a5,a3,a5
    zext.h	a5,a5
    beq	a2,a5,8480 <.L35>
    li	a0,11
    jal	7f80 <_Z21llk_pack_hw_configureILb1EEvm>
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a2,0xffe80
    addi	a3,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	a3,4(a5)
    lui	a3,0x2000
    sw	a3,8(a5)
    sw	a3,12(a5)
    sw	a3,16(a5)
    lui	a1,0x41000
    sw	a1,20(a5)
    sw	a3,24(a5)
    lui	a3,0x41008
    addi	a3,a3,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	a3,28(a5)
    lui	a3,0x41010
    sw	a3,32(a5)
    lui	a3,0x45000
    addi	a5,a3,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    sw	a5,0(s7)
    lui	a5,0x45004
    addi	a5,a5,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    sw	a5,0(s7)
    lui	a5,0x45040
    addi	a5,a5,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    sw	a5,0(s7)
    lui	a5,0x45100
    addi	a5,a5,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a5,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a5,0
    addi	a2,a2,4
    sw	a5,0(a2)
    lw	a5,0(a2)
    and	zero,zero,a5
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
    lw	a4,372(s5)
    lui	a2,0x1000
    addi	a5,a4,-1
    slli	a1,a5,0x8
    addi	a2,a2,-256 # ffff00 <trisck.cc.a8a8fe81+0xff338c>
    srli	a5,a5,0x10
    addi	a0,a3,24
    lui	a6,0x508c0
    slli	a5,a5,0x8
    and	a1,a1,a2
    lui	a2,0x800
    sw	a6,0(s7)
    add	a1,a1,a0
    addi	a3,a3,25
    or	a2,a5,a2
    sw	a1,0(s7)
    add	a2,a2,a3
    sw	a2,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,a3
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,360(s5)
    lw	a3,356(s5)
    add	a5,a4,a5
    sw	zero,380(s5)
    sw	a5,372(s5)
    bltu	a5,a3,8618 <.L36>
    lw	a4,352(s5)
    sub	a5,a5,a4
    sw	a5,372(s5)
    lhu	a5,378(s5)
    lui	s0,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,s0,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a4,a5,0x8
    add	a4,a4,a3
    sh	a5,378(s5)
    sw	a4,0(s7)
    ttstallwait	32,8
    lui	a5,0x67613
    addi	a5,a5,-1014 # 67612c0a <__device_print_strings_info_end+0x61112c0a>
    sw	a5,0(s7)
    li	a0,5
    jal	7f80 <_Z21llk_pack_hw_configureILb1EEvm>
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a3,0xffe80
    addi	a2,a3,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a2) # 800000 <trisck.cc.a8a8fe81+0x7f348c>
    lw	a5,0(a2)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a2,4
    sw	a2,0(a5) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	a2,4(a5)
    lui	a2,0x2000
    sw	a2,8(a5)
    sw	a2,12(a5)
    sw	a2,16(a5)
    lui	a1,0x41000
    sw	a1,20(a5)
    lui	a1,0x41008
    sw	a2,24(a5)
    addi	a2,a1,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	a2,28(a5)
    lui	a2,0x41010
    sw	a2,32(a5)
    addi	a5,s0,56
    sw	a5,0(s7)
    lui	a5,0x45004
    addi	a5,a5,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    sw	a5,0(s7)
    lui	a5,0x45040
    addi	a5,a5,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    sw	a5,0(s7)
    lui	a5,0x45100
    addi	a5,a5,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a5,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a5,0
    addi	a3,a3,4
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
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
    lui	a5,0xb4ff1
    addi	a5,a5,28 # b4ff101c <__device_print_strings_info_end+0xaeaf101c>
    sw	a5,0(s7)
    ttwrcfg	28,0,24
    ttwrcfg	30,0,25
    ttwrcfg	29,0,21
    ttnop
    ttnop
    ttsetdmareg	3,16383,0,56
    ttsetdmareg	0,0,0,57
    ttstallwait	128,8
    lui	a5,0xb4ff0
    addi	a5,a5,284 # b4ff011c <__device_print_strings_info_end+0xaeaf011c>
    sw	a5,0(s7)
    ttwrcfg	28,0,24
    ttwrcfg	28,0,25
    ttwrcfg	0,0,20
    ttwrcfg	0,0,21
    ttnop
    ttnop
    ttsemwait	1,2,1
    lw	a4,180(s5)
    lui	a3,0x1000
    addi	a5,a4,-1
    slli	a2,a5,0x8
    addi	a3,a3,-256 # ffff00 <trisck.cc.a8a8fe81+0xff338c>
    srli	a5,a5,0x10
    addi	a1,s0,24
    lui	a0,0x508c0
    slli	a5,a5,0x8
    and	a2,a2,a3
    lui	a3,0x800
    sw	a0,0(s7)
    add	a2,a2,a1
    addi	s0,s0,25
    or	a3,a5,a3
    sw	a2,0(s7)
    add	a3,a3,s0
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,s0
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,168(s5)
    lw	a3,164(s5)
    add	a5,a4,a5
    sw	zero,188(s5)
    sw	a5,180(s5)
    bltu	a5,a3,8838 <.L37>
    lw	a4,160(s5)
    sub	a5,a5,a4
    sw	a5,180(s5)
    lhu	a5,186(s5)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a4,a5,0x8
    add	a4,a4,a3
    sh	a5,186(s5)
    sw	a4,0(s7)
    ttstallwait	32,8
    lui	a5,0x67611
    addi	a5,a5,1034 # 6761140a <__device_print_strings_info_end+0x6111140a>
    sw	a5,0(s7)
    lhu	a2,218(s5)
    lw	a3,204(s5)
    lui	a4,0xffb46
    lw	a5,32(a4) # ffb46020 <__ldm_bss_end+0x45740>
    add	a5,a3,a5
    zext.h	a5,a5
    beq	a2,a5,8878 <.L38>
    li	a0,6
    jal	7f80 <_Z21llk_pack_hw_configureILb1EEvm>
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a2,0xffe80
    addi	a3,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	a3,4(a5)
    lui	a3,0x2000
    sw	a3,8(a5)
    sw	a3,12(a5)
    sw	a3,16(a5)
    lui	a1,0x41000
    sw	a1,20(a5)
    sw	a3,24(a5)
    lui	a3,0x41008
    addi	a3,a3,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	a3,28(a5)
    lui	a3,0x41010
    sw	a3,32(a5)
    lui	a3,0x45000
    addi	a5,a3,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    sw	a5,0(s7)
    lui	a5,0x45004
    addi	a5,a5,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    sw	a5,0(s7)
    lui	a5,0x45040
    addi	a5,a5,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    sw	a5,0(s7)
    lui	a5,0x45100
    addi	a5,a5,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a5,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a5,0
    addi	a2,a2,4
    sw	a5,0(a2)
    lw	a5,0(a2)
    and	zero,zero,a5
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
    lw	a4,212(s5)
    lui	a2,0x1000
    addi	a5,a4,-1
    slli	a1,a5,0x8
    addi	a2,a2,-256 # ffff00 <trisck.cc.a8a8fe81+0xff338c>
    srli	a5,a5,0x10
    addi	a0,a3,24
    lui	a6,0x508c0
    slli	a5,a5,0x8
    and	a1,a1,a2
    lui	a2,0x800
    sw	a6,0(s7)
    add	a1,a1,a0
    addi	a3,a3,25
    or	a2,a5,a2
    sw	a1,0(s7)
    add	a2,a2,a3
    sw	a2,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,a3
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,200(s5)
    lw	a3,196(s5)
    add	a5,a4,a5
    sw	zero,220(s5)
    sw	a5,212(s5)
    bltu	a5,a3,8a10 <.L39>
    lw	a4,192(s5)
    sub	a5,a5,a4
    sw	a5,212(s5)
    lhu	a4,218(s5)
    lui	a5,0x45000
    addi	a4,a4,1
    zext.h	a4,a4
    addi	a2,a5,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a3,a4,0x8
    add	a3,a3,a2
    sh	a4,218(s5)
    sw	a3,0(s7)
    ttstallwait	32,8
    lui	a4,0x67612
    addi	a4,a4,-2038 # 6761180a <__device_print_strings_info_end+0x6111180a>
    lui	a0,0x1000
    sw	a4,0(s7)
    lui	s3,0xb5080
    lui	a2,0x45004
    lui	a3,0x45040
    lui	a4,0x45100
    lui	t2,0xb5800
    lui	t0,0xb61e0
    lui	t6,0xffc00
    lui	t5,0xb3fc0
    lui	t4,0xb53f0
    lui	t3,0xb5100
    lui	t1,0xb6ff0
    lui	a7,0xb3040
    lui	s1,0x10
    lui	s0,0xffe80
    lui	a6,0x41008
    addi	s9,a0,-256 # ffff00 <trisck.cc.a8a8fe81+0xff338c>
    li	a0,63
    addi	s11,s3,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    addi	a1,a5,56
    addi	a2,a2,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    addi	a3,a3,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    addi	a4,a4,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    addi	t2,t2,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    addi	t0,t0,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    addi	t6,t6,3 # ffc00003 <__ldm_bss_end+0xff723>
    addi	t5,t5,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    addi	t4,t4,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    addi	t3,t3,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    addi	t1,t1,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    addi	a7,a7,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    addi	s6,s1,-1 # ffff <trisck.cc.a8a8fe81+0x348b>
    addi	s10,s0,8 # ffe80008 <__instrn_buffer+0x40008>
    addi	s8,a6,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	a0,12(sp)
    lhu	s4,186(s5)
    lw	s1,172(s5)
    lui	a6,0xffb45
    lw	a0,32(a6) # ffb45020 <__ldm_bss_end+0x44740>
    add	a0,s1,a0
    zext.h	a0,a0
    beq	s4,a0,8adc <.L40>
    lhu	s4,346(s5)
    lw	s1,332(s5)
    lui	a6,0xffb4a
    lw	a0,32(a6) # ffb4a020 <__ldm_bss_end+0x49740>
    add	a0,s1,a0
    zext.h	a0,a0
    beq	s4,a0,8af8 <.L41>
    lw	a6,328(s5)
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    sw	a6,16(sp)
    lui	a6,0xffef0
    beqz	a0,8b20 <.L42>
    addi	a6,a6,896 # ffef0380 <__instrn_buffer+0xb0380>
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    sw	a4,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lw	a0,44(sp)
    and	a0,a0,t6
    sw	a0,44(sp)
    sw	t2,0(s7)
    slli	s1,a0,0x8
    sw	t0,0(s7)
    zext.h	s1,s1
    add	s1,s1,t5
    sw	s1,0(s7)
    srli	a0,a0,0x10
    lui	s1,0xb4ff0
    addi	s1,s1,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    slli	a0,a0,0x8
    sw	s1,0(s7)
    zext.h	a0,a0
    add	a0,a0,t4
    sw	a0,0(s7)
    ttatrelm	0
    sw	t3,0(s7)
    sw	t1,0(s7)
    lui	s1,0x40
    sw	s1,272(a6)
    li	a0,1
    sw	a0,280(a6)
    ttstallwait	128,8
    sw	a7,0(s7)
    sw	s11,0(s7)
    sw	a0,72(a6)
    lui	a0,0xffe00
    sw	s1,208(a0) # ffe000d0 <__ldm_bss_end+0x2ff7f0>
    sw	zero,60(sp)
    lw	s4,208(a0)
    li	s1,256
    sw	s4,60(sp)
    sw	s1,112(a6)
    sw	s6,96(a6)
    sw	zero,80(a6)
    lw	a6,16(sp)
    sw	a6,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,56(sp)
    lw	a0,76(a0)
    sw	a0,56(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    li	a6,0
    mv	a0,a6
    sw	a0,0(s10)
    lw	a0,0(s10)
    and	zero,zero,a0
    lui	a0,0xffb80
    li	s1,4
    sw	s1,0(a0) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	s1,4(a0)
    lui	s1,0x2000
    sw	s1,8(a0)
    sw	s1,12(a0)
    sw	s1,16(a0)
    lui	s4,0x41000
    sw	s4,20(a0)
    sw	s1,24(a0)
    sw	s8,28(a0)
    lui	s1,0x41010
    sw	s1,32(a0)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    sw	a4,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    addi	a0,s0,4
    sw	a6,0(a0)
    lw	a6,0(a0)
    and	zero,zero,a6
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
    lw	s1,340(s5)
    lui	a0,0x508c0
    sw	a0,0(s7)
    addi	a0,s1,-1 # 4100ffff <__device_print_strings_info_end+0x3ab0ffff>
    slli	a6,a0,0x8
    addi	s4,a5,24
    and	a6,a6,s9
    add	a6,a6,s4
    srli	a0,a0,0x10
    sw	a6,0(s7)
    slli	a0,a0,0x8
    lui	a6,0x800
    or	a6,a0,a6
    addi	s4,a5,25
    add	a6,a6,s4
    sw	a6,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a0,a0,s4
    sw	a0,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a0,328(s5)
    lw	a6,324(s5)
    add	a0,s1,a0
    sw	zero,348(s5)
    sw	a0,340(s5)
    bltu	a0,a6,8d44 <.L43>
    lw	a6,320(s5)
    sub	a0,a0,a6
    sw	a0,340(s5)
    lhu	a0,346(s5)
    addi	s1,a5,48
    addi	a0,a0,1 # 508c0001 <__device_print_strings_info_end+0x4a3c0001>
    zext.h	a0,a0
    slli	a6,a0,0x8
    add	a6,a6,s1
    sh	a0,346(s5)
    sw	a6,0(s7)
    ttstallwait	32,8
    lui	a0,0x67613
    addi	a0,a0,-2038 # 6761280a <__device_print_strings_info_end+0x6111280a>
    sw	a0,0(s7)
    lhu	s4,378(s5)
    lw	s1,364(s5)
    lui	a6,0xffb4b
    lw	a0,32(a6) # ffb4b020 <__ldm_bss_end+0x4a740>
    add	a0,s1,a0
    zext.h	a0,a0
    beq	s4,a0,8d80 <.L44>
    lw	a6,360(s5)
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    sw	a6,16(sp)
    lui	a6,0xffef0
    beqz	a0,8da8 <.L45>
    addi	a6,a6,896 # ffef0380 <__instrn_buffer+0xb0380>
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    sw	a4,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lw	a0,40(sp)
    and	a0,a0,t6
    sw	a0,40(sp)
    sw	t2,0(s7)
    slli	s1,a0,0x8
    sw	t0,0(s7)
    zext.h	s1,s1
    add	s1,s1,t5
    sw	s1,0(s7)
    srli	a0,a0,0x10
    lui	s1,0xb4ff0
    addi	s1,s1,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    slli	a0,a0,0x8
    sw	s1,0(s7)
    zext.h	a0,a0
    add	a0,a0,t4
    sw	a0,0(s7)
    ttatrelm	0
    sw	t3,0(s7)
    sw	t1,0(s7)
    lui	s1,0x40
    sw	s1,272(a6)
    li	a0,1
    sw	a0,280(a6)
    ttstallwait	128,8
    sw	a7,0(s7)
    sw	s11,0(s7)
    sw	a0,72(a6)
    lui	a0,0xffe00
    sw	s1,208(a0) # ffe000d0 <__ldm_bss_end+0x2ff7f0>
    sw	zero,68(sp)
    lw	s4,208(a0)
    li	s1,256
    sw	s4,68(sp)
    sw	s1,112(a6)
    sw	s6,96(a6)
    sw	zero,80(a6)
    lw	a6,16(sp)
    sw	a6,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,64(sp)
    lw	a0,76(a0)
    sw	a0,64(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    li	a6,0
    mv	a0,a6
    sw	a0,0(s10)
    lw	a0,0(s10)
    and	zero,zero,a0
    lui	a0,0xffb80
    li	s1,4
    sw	s1,0(a0) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	s1,4(a0)
    lui	s1,0x2000
    sw	s1,8(a0)
    sw	s1,12(a0)
    sw	s1,16(a0)
    lui	s4,0x41000
    sw	s4,20(a0)
    sw	s1,24(a0)
    sw	s8,28(a0)
    lui	s1,0x41010
    sw	s1,32(a0)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    sw	a4,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    addi	a0,s0,4
    sw	a6,0(a0)
    lw	a6,0(a0)
    and	zero,zero,a6
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
    lw	s1,372(s5)
    lui	a0,0x508c0
    sw	a0,0(s7)
    addi	a0,s1,-1 # 4100ffff <__device_print_strings_info_end+0x3ab0ffff>
    slli	a6,a0,0x8
    addi	s4,a5,24
    and	a6,a6,s9
    add	a6,a6,s4
    srli	a0,a0,0x10
    sw	a6,0(s7)
    slli	a0,a0,0x8
    lui	a6,0x800
    or	a6,a0,a6
    addi	s4,a5,25
    add	a6,a6,s4
    sw	a6,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a0,a0,s4
    sw	a0,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a0,360(s5)
    lw	a6,356(s5)
    add	a0,s1,a0
    sw	zero,380(s5)
    sw	a0,372(s5)
    bltu	a0,a6,8fcc <.L46>
    lw	a6,352(s5)
    sub	a0,a0,a6
    sw	a0,372(s5)
    lhu	a0,378(s5)
    addi	s1,a5,48
    addi	a0,a0,1 # 508c0001 <__device_print_strings_info_end+0x4a3c0001>
    zext.h	a0,a0
    slli	a6,a0,0x8
    add	a6,a6,s1
    sh	a0,378(s5)
    sw	a6,0(s7)
    ttstallwait	32,8
    lui	a0,0x67613
    addi	a0,a0,-1014 # 67612c0a <__device_print_strings_info_end+0x61112c0a>
    sw	a0,0(s7)
    lw	a6,168(s5)
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    sw	a6,16(sp)
    lui	a6,0xffef0
    beqz	a0,9014 <.L47>
    addi	a6,a6,896 # ffef0380 <__instrn_buffer+0xb0380>
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    sw	a4,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lw	a0,36(sp)
    and	a0,a0,t6
    sw	a0,36(sp)
    sw	t2,0(s7)
    slli	s1,a0,0x8
    sw	t0,0(s7)
    zext.h	s1,s1
    add	s1,s1,t5
    sw	s1,0(s7)
    srli	a0,a0,0x10
    lui	s1,0xb4ff0
    addi	s4,s1,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    slli	a0,a0,0x8
    sw	s4,0(s7)
    zext.h	a0,a0
    add	a0,a0,t4
    sw	a0,0(s7)
    ttatrelm	0
    sw	t3,0(s7)
    sw	t1,0(s7)
    lui	s1,0x40
    sw	s1,272(a6)
    li	a0,1
    sw	a0,280(a6)
    ttstallwait	128,8
    sw	a7,0(s7)
    sw	s11,0(s7)
    sw	a0,72(a6)
    lui	a0,0xffe00
    sw	s1,208(a0) # ffe000d0 <__ldm_bss_end+0x2ff7f0>
    sw	zero,76(sp)
    lw	s4,208(a0)
    li	s1,256
    sw	s4,76(sp)
    sw	s1,112(a6)
    sw	s6,96(a6)
    sw	zero,80(a6)
    lw	a6,16(sp)
    sw	a6,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,72(sp)
    lw	a0,76(a0)
    sw	a0,72(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    li	a6,0
    mv	a0,a6
    sw	a0,0(s10)
    lw	a0,0(s10)
    and	zero,zero,a0
    lui	a0,0xffb80
    li	s1,4
    sw	s1,0(a0) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	s1,4(a0)
    lui	s1,0x2000
    sw	s1,8(a0)
    sw	s1,12(a0)
    sw	s1,16(a0)
    lui	s4,0x41000
    sw	s4,20(a0)
    sw	s1,24(a0)
    sw	s8,28(a0)
    lui	s1,0x41010
    sw	s1,32(a0)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    sw	a4,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    addi	a0,s0,4
    sw	a6,0(a0)
    lw	a6,0(a0)
    and	zero,zero,a6
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
    lui	a0,0xb4ff1
    addi	a0,a0,28 # b4ff101c <__device_print_strings_info_end+0xaeaf101c>
    sw	a0,0(s7)
    ttwrcfg	28,0,24
    ttwrcfg	30,0,25
    ttwrcfg	29,0,21
    ttnop
    ttnop
    ttsetdmareg	3,16383,0,56
    ttsetdmareg	0,0,0,57
    ttstallwait	128,8
    lui	s1,0xb4ff0
    addi	a0,s1,284 # b4ff011c <__device_print_strings_info_end+0xaeaf011c>
    sw	a0,0(s7)
    ttwrcfg	28,0,24
    ttwrcfg	28,0,25
    ttwrcfg	0,0,20
    ttwrcfg	0,0,21
    ttnop
    ttnop
    ttsemwait	1,2,1
    lw	s1,180(s5)
    lui	a0,0x508c0
    sw	a0,0(s7)
    addi	a0,s1,-1
    slli	a6,a0,0x8
    addi	s4,a5,24
    and	a6,a6,s9
    add	a6,a6,s4
    srli	a0,a0,0x10
    sw	a6,0(s7)
    slli	a0,a0,0x8
    lui	a6,0x800
    or	a6,a0,a6
    addi	s4,a5,25
    add	a6,a6,s4
    sw	a6,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a0,a0,s4
    sw	a0,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a0,168(s5)
    lw	a6,164(s5)
    add	a0,s1,a0
    sw	zero,188(s5)
    sw	a0,180(s5)
    bltu	a0,a6,92a0 <.L48>
    lw	a6,160(s5)
    sub	a0,a0,a6
    sw	a0,180(s5)
    lhu	a0,186(s5)
    addi	s1,a5,48
    addi	a0,a0,1 # 508c0001 <__device_print_strings_info_end+0x4a3c0001>
    zext.h	a0,a0
    slli	a6,a0,0x8
    add	a6,a6,s1
    sh	a0,186(s5)
    sw	a6,0(s7)
    ttstallwait	32,8
    lui	a0,0x67611
    addi	a0,a0,1034 # 6761140a <__device_print_strings_info_end+0x6111140a>
    sw	a0,0(s7)
    lhu	s4,218(s5)
    lw	s1,204(s5)
    lui	a6,0xffb46
    lw	a0,32(a6) # ffb46020 <__ldm_bss_end+0x45740>
    add	a0,s1,a0
    zext.h	a0,a0
    beq	s4,a0,92dc <.L49>
    lw	a6,200(s5)
    lw	a0,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    sw	a6,16(sp)
    lui	a6,0xffef0
    beqz	a0,9304 <.L50>
    addi	a6,a6,896 # ffef0380 <__instrn_buffer+0xb0380>
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    sw	a4,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lw	a0,20(sp)
    and	a0,a0,t6
    sw	a0,20(sp)
    sw	t2,0(s7)
    slli	s1,a0,0x8
    sw	t0,0(s7)
    zext.h	s1,s1
    add	s1,s1,t5
    sw	s1,0(s7)
    srli	a0,a0,0x10
    lui	s1,0xb4ff0
    addi	s1,s1,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    slli	a0,a0,0x8
    sw	s1,0(s7)
    zext.h	a0,a0
    add	a0,a0,t4
    sw	a0,0(s7)
    ttatrelm	0
    sw	t3,0(s7)
    sw	t1,0(s7)
    lui	s1,0x40
    sw	s1,272(a6)
    li	a0,1
    sw	a0,280(a6)
    ttstallwait	128,8
    sw	a7,0(s7)
    sw	s11,0(s7)
    sw	a0,72(a6)
    lui	a0,0xffe00
    sw	s1,208(a0) # ffe000d0 <__ldm_bss_end+0x2ff7f0>
    sw	zero,84(sp)
    lw	s4,208(a0)
    li	s1,256
    sw	s4,84(sp)
    sw	s1,112(a6)
    sw	s6,96(a6)
    sw	zero,80(a6)
    lw	a6,16(sp)
    sw	a6,64(a0)
    sw	zero,68(a0)
    sw	zero,72(a0)
    sw	zero,76(a0)
    sw	zero,80(sp)
    lw	a0,76(a0)
    sw	a0,80(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    li	a6,0
    mv	a0,a6
    sw	a0,0(s10)
    lw	a0,0(s10)
    and	zero,zero,a0
    lui	a0,0xffb80
    li	s1,4
    sw	s1,0(a0) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	s1,4(a0)
    lui	s1,0x2000
    sw	s1,8(a0)
    sw	s1,12(a0)
    sw	s1,16(a0)
    lui	s4,0x41000
    sw	s4,20(a0)
    sw	s1,24(a0)
    sw	s8,28(a0)
    lui	s1,0x41010
    sw	s1,32(a0)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    sw	a4,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    addi	a0,s0,4
    sw	a6,0(a0)
    lw	a6,0(a0)
    and	zero,zero,a6
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
    lw	s1,212(s5)
    lui	a0,0x508c0
    sw	a0,0(s7)
    addi	a0,s1,-1 # 4100ffff <__device_print_strings_info_end+0x3ab0ffff>
    slli	a6,a0,0x8
    addi	s4,a5,24
    and	a6,a6,s9
    add	a6,a6,s4
    srli	a0,a0,0x10
    sw	a6,0(s7)
    slli	a0,a0,0x8
    lui	a6,0x800
    or	a6,a0,a6
    addi	s4,a5,25
    add	a6,a6,s4
    sw	a6,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a0,a0,s4
    sw	a0,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a0,200(s5)
    lw	a6,196(s5)
    add	a0,s1,a0
    sw	zero,220(s5)
    sw	a0,212(s5)
    bltu	a0,a6,a280 <.L51>
    lhu	a6,218(s5)
    addi	s1,a5,48
    addi	a6,a6,1 # 800001 <trisck.cc.a8a8fe81+0x7f348d>
    zext.h	a6,a6
    sh	a6,218(s5)
    slli	a6,a6,0x8
    add	a6,a6,s1
    lw	s1,192(s5)
    sw	a6,0(s7)
    sub	a0,a0,s1
    sw	a0,212(s5)
    ttstallwait	32,8
    lw	a6,12(sp)
    lui	a0,0x67612
    addi	a6,a6,-1
    addi	a0,a0,-2038 # 6761180a <__device_print_strings_info_end+0x6111180a>
    sw	a6,12(sp)
    sw	a0,0(s7)
    bnez	a6,8ad0 <.L54>
    lhu	a2,250(s5)
    lw	a3,236(s5)
    lui	a4,0xffb47
    lw	a5,32(a4) # ffb47020 <__ldm_bss_end+0x46740>
    add	a5,a3,a5
    zext.h	a5,a5
    beq	a2,a5,9574 <.L55>
    li	a0,7
    jal	7f80 <_Z21llk_pack_hw_configureILb1EEvm>
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a2,0xffe80
    addi	a3,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	s0,0xffb80
    li	s9,4
    sw	s9,0(s0) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	s9,4(s0)
    lui	s1,0x2000
    sw	s1,8(s0)
    sw	s1,12(s0)
    sw	s1,16(s0)
    lui	a5,0x41000
    sw	a5,20(s0)
    lui	s8,0x41008
    sw	s1,24(s0)
    addi	s8,s8,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	s8,28(s0)
    lui	s11,0x41010
    lui	a6,0x45000
    sw	s11,32(s0)
    addi	s10,a6,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    lui	a4,0x45004
    sw	s10,0(s7)
    addi	t1,a4,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    lui	s6,0x45040
    sw	t1,0(s7)
    addi	s6,s6,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    lui	a4,0x45100
    sw	s6,0(s7)
    addi	a7,a4,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a7,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a4,0
    add	s4,a2,s9
    sw	a4,0(s4) # 41000000 <__device_print_strings_info_end+0x3ab00000>
    lw	a4,0(s4)
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
    li	a0,7
    jal	7f80 <_Z21llk_pack_hw_configureILb1EEvm>
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a5,0xffe80
    li	a4,0
    addi	a3,a5,8 # ffe80008 <__instrn_buffer+0x40008>
    sw	a4,0(a3)
    lw	a4,0(a3)
    and	zero,zero,a4
    sw	s9,0(s0)
    sw	s9,4(s0)
    sw	s1,8(s0)
    sw	s1,12(s0)
    sw	s1,16(s0)
    lui	a5,0x41000
    sw	a5,20(s0)
    sw	s1,24(s0)
    sw	s8,28(s0)
    sw	s11,32(s0)
    lui	a5,0x45004
    sw	s10,0(s7)
    addi	t1,a5,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    sw	t1,0(s7)
    lui	a5,0x45100
    sw	s6,0(s7)
    addi	a7,a5,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a7,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a5,0
    sw	a5,0(s4)
    lw	a5,0(s4)
    and	zero,zero,a5
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
    lw	a4,244(s5)
    lui	a3,0x1000
    addi	a5,a4,-1
    lui	a6,0x45000
    slli	a2,a5,0x8
    addi	a3,a3,-256 # ffff00 <trisck.cc.a8a8fe81+0xff338c>
    srli	a5,a5,0x10
    addi	a1,a6,24 # 45000018 <__device_print_strings_info_end+0x3eb00018>
    lui	a0,0x508c0
    slli	a5,a5,0x8
    and	a2,a2,a3
    lui	a3,0x800
    sw	a0,0(s7)
    add	a2,a2,a1
    or	a3,a5,a3
    addi	a1,a6,25
    sw	a2,0(s7)
    add	a3,a3,a1
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,a1
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,232(s5)
    lw	a3,228(s5)
    add	a5,a4,a5
    sw	zero,252(s5)
    sw	a5,244(s5)
    bltu	a5,a3,97d4 <.L56>
    lw	a4,224(s5)
    sub	a5,a5,a4
    sw	a5,244(s5)
    lhu	a5,250(s5)
    lui	a3,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a3,a3,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a4,a5,0x8
    add	a4,a4,a3
    sh	a5,250(s5)
    sw	a4,0(s7)
    ttstallwait	32,8
    lui	a5,0x67612
    addi	a5,a5,-1014 # 67611c0a <__device_print_strings_info_end+0x61111c0a>
    sw	a5,0(s7)
    lhu	a2,282(s5)
    lw	a3,268(s5)
    lui	a4,0xffb48
    lw	a5,32(a4) # ffb48020 <__ldm_bss_end+0x47740>
    add	a5,a3,a5
    zext.h	a5,a5
    beq	a2,a5,9814 <.L57>
    li	a0,8
    jal	7f80 <_Z21llk_pack_hw_configureILb1EEvm>
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    lui	a2,0xffe80
    addi	a3,a2,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,0
    sw	a5,0(a3)
    lw	a5,0(a3)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	a3,4
    sw	a3,0(a5) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	a3,4(a5)
    lui	a3,0x2000
    sw	a3,8(a5)
    sw	a3,12(a5)
    sw	a3,16(a5)
    lui	a1,0x41000
    sw	a1,20(a5)
    sw	a3,24(a5)
    lui	a3,0x41008
    addi	a3,a3,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    sw	a3,28(a5)
    lui	a3,0x41010
    sw	a3,32(a5)
    lui	a3,0x45000
    addi	a5,a3,56 # 45000038 <__device_print_strings_info_end+0x3eb00038>
    sw	a5,0(s7)
    lui	a5,0x45004
    addi	a5,a5,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    sw	a5,0(s7)
    lui	a5,0x45040
    addi	a5,a5,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    sw	a5,0(s7)
    lui	a5,0x45100
    addi	a5,a5,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    sw	a5,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    li	a5,0
    addi	a2,a2,4
    sw	a5,0(a2)
    lw	a5,0(a2)
    and	zero,zero,a5
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
    lw	a4,276(s5)
    lui	a2,0x1000
    addi	a5,a4,-1
    slli	a1,a5,0x8
    addi	a2,a2,-256 # ffff00 <trisck.cc.a8a8fe81+0xff338c>
    srli	a5,a5,0x10
    addi	a0,a3,24
    lui	a6,0x508c0
    slli	a5,a5,0x8
    and	a1,a1,a2
    lui	a2,0x800
    sw	a6,0(s7)
    add	a1,a1,a0
    addi	a3,a3,25
    or	a2,a5,a2
    sw	a1,0(s7)
    add	a2,a2,a3
    sw	a2,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,a3
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,264(s5)
    lw	a3,260(s5)
    add	a5,a4,a5
    sw	zero,284(s5)
    sw	a5,276(s5)
    bltu	a5,a3,99ac <.L58>
    lw	a4,256(s5)
    sub	a5,a5,a4
    sw	a5,276(s5)
    lhu	a5,282(s5)
    lui	a4,0x45000
    addi	a5,a5,1
    zext.h	a5,a5
    addi	a2,a4,48 # 45000030 <__device_print_strings_info_end+0x3eb00030>
    slli	a3,a5,0x8
    add	a3,a3,a2
    sh	a5,282(s5)
    sw	a3,0(s7)
    ttstallwait	32,8
    lui	a5,0x67612
    addi	a5,a5,10 # 6761200a <__device_print_strings_info_end+0x6111200a>
    sw	a5,0(s7)
    lui	a5,0xb61e0
    addi	a5,a5,1 # b61e0001 <__device_print_strings_info_end+0xafce0001>
    lui	s4,0xb5800
    sw	a5,16(sp)
    lui	a5,0xffe80
    addi	s4,s4,71 # b5800047 <__device_print_strings_info_end+0xaf300047>
    lui	a1,0x45004
    lui	a2,0x45040
    lui	a3,0x45100
    lui	s1,0xffc00
    lui	s0,0xb3fc0
    lui	t2,0xb4ff0
    lui	t0,0xb53f0
    lui	t6,0xb5100
    lui	t5,0xb6ff0
    lui	t4,0xb3040
    lui	t3,0xb5080
    lui	t1,0x10
    lui	a7,0x41008
    lui	a6,0x1000
    addi	s6,a5,8 # ffe80008 <__instrn_buffer+0x40008>
    li	a5,64
    sw	s4,12(sp)
    addi	a0,a4,56
    addi	a1,a1,57 # 45004039 <__device_print_strings_info_end+0x3eb04039>
    addi	a2,a2,58 # 4504003a <__device_print_strings_info_end+0x3eb4003a>
    addi	a3,a3,59 # 4510003b <__device_print_strings_info_end+0x3ec0003b>
    addi	s1,s1,3 # ffc00003 <__ldm_bss_end+0xff723>
    addi	s0,s0,2 # b3fc0002 <__device_print_strings_info_end+0xadac0002>
    addi	t2,t2,2 # b4ff0002 <__device_print_strings_info_end+0xaeaf0002>
    addi	t0,t0,2 # b53f0002 <__device_print_strings_info_end+0xaeef0002>
    addi	t6,t6,71 # b5100047 <__device_print_strings_info_end+0xaec00047>
    addi	t5,t5,71 # b6ff0047 <__device_print_strings_info_end+0xb0af0047>
    addi	t4,t4,70 # b3040046 <__device_print_strings_info_end+0xacb40046>
    addi	t3,t3,71 # b5080047 <__device_print_strings_info_end+0xaeb80047>
    addi	t1,t1,-1 # ffff <trisck.cc.a8a8fe81+0x348b>
    addi	a7,a7,1 # 41008001 <__device_print_strings_info_end+0x3ab08001>
    addi	a6,a6,-256 # ffff00 <trisck.cc.a8a8fe81+0xff338c>
    sw	a5,20(sp)
    lui	s4,0xffef0
    lhu	s10,122(s5)
    lw	s9,108(s5)
    lui	s8,0xffb43
    lw	a5,32(s8) # ffb43020 <__ldm_bss_end+0x42740>
    add	a5,s9,a5
    zext.h	a5,a5
    beq	s10,a5,9a8c <.L59>
    lhu	s10,154(s5)
    lw	s9,140(s5)
    lui	s8,0xffb44
    lw	a5,32(s8) # ffb44020 <__ldm_bss_end+0x43740>
    add	a5,s9,a5
    zext.h	a5,a5
    beq	s10,a5,9aa8 <.L60>
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	s9,104(s5)
    lui	s8,0xffef0
    beqz	a5,9acc <.L61>
    addi	s8,s4,896 # ffef0380 <__instrn_buffer+0xb0380>
    sw	a0,0(s7)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lw	a5,32(sp)
    lw	s10,12(sp)
    and	a5,a5,s1
    sw	a5,32(sp)
    lw	s11,16(sp)
    sw	s10,0(s7)
    slli	s10,a5,0x8
    sw	s11,0(s7)
    zext.h	s10,s10
    srli	a5,a5,0x10
    add	s10,s10,s0
    sw	s10,0(s7)
    slli	a5,a5,0x8
    sw	t2,0(s7)
    zext.h	a5,a5
    add	a5,a5,t0
    sw	a5,0(s7)
    ttatrelm	0
    sw	t6,0(s7)
    sw	t5,0(s7)
    lui	s10,0x40
    sw	s10,272(s8) # ffef0110 <__instrn_buffer+0xb0110>
    li	a5,1
    sw	a5,280(s8)
    ttstallwait	128,8
    sw	t4,0(s7)
    sw	t3,0(s7)
    sw	a5,72(s8)
    lui	a5,0xffe00
    sw	s10,208(a5) # ffe000d0 <__ldm_bss_end+0x2ff7f0>
    sw	zero,92(sp)
    lw	s11,208(a5)
    li	s10,256
    sw	s11,92(sp)
    sw	s10,112(s8)
    sw	t1,96(s8)
    sw	zero,80(s8)
    sw	s9,64(a5)
    sw	zero,68(a5)
    sw	zero,72(a5)
    sw	zero,76(a5)
    sw	zero,88(sp)
    lw	a5,76(a5)
    sw	a5,88(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    li	s8,0
    mv	a5,s8
    sw	a5,0(s6)
    lw	a5,0(s6)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	s9,4
    sw	s9,0(a5) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	s9,4(a5)
    lui	s9,0x2000
    sw	s9,8(a5)
    sw	s9,12(a5)
    sw	s9,16(a5)
    lui	s10,0x41000
    sw	s10,20(a5)
    sw	s9,24(a5)
    sw	a7,28(a5)
    lui	s9,0x41010
    sw	s9,32(a5)
    sw	a0,0(s7)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    lui	a5,0xffe80
    addi	a5,a5,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	s8,0(a5)
    lw	s8,0(a5)
    and	zero,zero,s8
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
    lw	a5,116(s5)
    lui	s8,0x508c0
    addi	a5,a5,-1
    slli	s9,a5,0x8
    srli	a5,a5,0x10
    sw	s8,0(s7)
    addi	s10,a4,24
    and	s9,s9,a6
    slli	a5,a5,0x8
    lui	s8,0x800
    add	s9,s9,s10
    or	s8,a5,s8
    addi	s10,a4,25
    sw	s9,0(s7)
    add	s8,s8,s10
    sw	s8,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,s10
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	s9,136(s5)
    lui	s8,0xffef0
    beqz	a5,9ce0 <.L62>
    addi	s8,s4,896
    sw	a0,0(s7)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lw	a5,28(sp)
    lw	s10,12(sp)
    and	a5,a5,s1
    sw	a5,28(sp)
    lw	s11,16(sp)
    sw	s10,0(s7)
    slli	s10,a5,0x8
    sw	s11,0(s7)
    zext.h	s10,s10
    srli	a5,a5,0x10
    add	s10,s10,s0
    sw	s10,0(s7)
    slli	a5,a5,0x8
    sw	t2,0(s7)
    zext.h	a5,a5
    add	a5,a5,t0
    sw	a5,0(s7)
    ttatrelm	0
    sw	t6,0(s7)
    sw	t5,0(s7)
    lui	s10,0x40
    sw	s10,272(s8) # ffef0110 <__instrn_buffer+0xb0110>
    li	a5,1
    sw	a5,280(s8)
    ttstallwait	128,8
    sw	t4,0(s7)
    sw	t3,0(s7)
    sw	a5,72(s8)
    lui	a5,0xffe00
    sw	s10,208(a5) # ffe000d0 <__ldm_bss_end+0x2ff7f0>
    sw	zero,100(sp)
    lw	s11,208(a5)
    li	s10,256
    sw	s11,100(sp)
    sw	s10,112(s8)
    sw	t1,96(s8)
    sw	zero,80(s8)
    sw	s9,64(a5)
    sw	zero,68(a5)
    sw	zero,72(a5)
    sw	zero,76(a5)
    sw	zero,96(sp)
    lw	a5,76(a5)
    sw	a5,96(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    li	s8,0
    mv	a5,s8
    sw	a5,0(s6)
    lw	a5,0(s6)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	s9,4
    sw	s9,0(a5) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	s9,4(a5)
    lui	s9,0x2000
    sw	s9,8(a5)
    sw	s9,12(a5)
    sw	s9,16(a5)
    lui	s10,0x41000
    sw	s10,20(a5)
    sw	s9,24(a5)
    sw	a7,28(a5)
    lui	s9,0x41010
    sw	s9,32(a5)
    sw	a0,0(s7)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    lui	a5,0xffe80
    addi	a5,a5,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	s8,0(a5)
    lw	s8,0(a5)
    and	zero,zero,s8
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
    lw	s11,148(s5)
    lui	a5,0x508c0
    sw	a5,0(s7)
    addi	a5,s11,-1 # 4100ffff <__device_print_strings_info_end+0x3ab0ffff>
    slli	s9,a5,0x8
    srli	a5,a5,0x10
    addi	s10,a4,24
    and	s9,s9,a6
    slli	a5,a5,0x8
    lui	s8,0x800
    add	s9,s9,s10
    or	s8,a5,s8
    addi	s10,a4,25
    sw	s9,0(s7)
    add	s8,s8,s10
    sw	s8,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,s10
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,136(s5)
    lw	s8,132(s5)
    add	a5,s11,a5
    sw	zero,156(s5)
    sw	a5,148(s5)
    bltu	a5,s8,9f04 <.L63>
    lw	s8,128(s5)
    sub	a5,a5,s8
    sw	a5,148(s5)
    lhu	a5,154(s5)
    addi	s9,a4,48
    addi	a5,a5,1 # 508c0001 <__device_print_strings_info_end+0x4a3c0001>
    zext.h	a5,a5
    slli	s8,a5,0x8
    add	s8,s8,s9
    sh	a5,154(s5)
    sw	s8,0(s7)
    ttstallwait	32,8
    lui	s8,0x67611
    lw	s9,116(s5)
    lw	a5,104(s5)
    addi	s8,s8,10 # 6761100a <__device_print_strings_info_end+0x6111100a>
    sw	zero,124(s5)
    add	a5,a5,s9
    lw	s9,100(s5)
    sw	s8,0(s7)
    sw	a5,116(s5)
    bltu	a5,s9,9f5c <.L64>
    lw	s8,96(s5)
    sub	a5,a5,s8
    sw	a5,116(s5)
    lhu	a5,122(s5)
    addi	s9,a4,48
    addi	a5,a5,1
    zext.h	a5,a5
    slli	s8,a5,0x8
    add	s8,s8,s9
    sh	a5,122(s5)
    sw	s8,0(s7)
    ttstallwait	32,8
    lui	a5,0x67611
    addi	a5,a5,-1014 # 67610c0a <__device_print_strings_info_end+0x61110c0a>
    sw	a5,0(s7)
    lhu	s10,314(s5)
    lw	s9,300(s5)
    lui	s8,0xffb49
    lw	a5,32(s8) # ffb49020 <__ldm_bss_end+0x48740>
    add	a5,s9,a5
    zext.h	a5,a5
    beq	s10,a5,9f98 <.L65>
    lw	a5,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    lw	s9,296(s5)
    lui	s8,0xffef0
    beqz	a5,9fbc <.L66>
    addi	s8,s4,896
    sw	a0,0(s7)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttatgetm	0
    lw	a5,24(sp)
    lw	s10,12(sp)
    and	a5,a5,s1
    sw	a5,24(sp)
    lw	s11,16(sp)
    sw	s10,0(s7)
    slli	s10,a5,0x8
    sw	s11,0(s7)
    zext.h	s10,s10
    srli	a5,a5,0x10
    add	s10,s10,s0
    sw	s10,0(s7)
    slli	a5,a5,0x8
    sw	t2,0(s7)
    zext.h	a5,a5
    add	a5,a5,t0
    sw	a5,0(s7)
    ttatrelm	0
    sw	t6,0(s7)
    sw	t5,0(s7)
    lui	s10,0x40
    sw	s10,272(s8) # ffef0110 <__instrn_buffer+0xb0110>
    li	a5,1
    sw	a5,280(s8)
    ttstallwait	128,8
    sw	t4,0(s7)
    sw	t3,0(s7)
    sw	a5,72(s8)
    lui	a5,0xffe00
    sw	s10,208(a5) # ffe000d0 <__ldm_bss_end+0x2ff7f0>
    sw	zero,108(sp)
    lw	s11,208(a5)
    li	s10,256
    sw	s11,108(sp)
    sw	s10,112(s8)
    sw	t1,96(s8)
    sw	zero,80(s8)
    sw	s9,64(a5)
    sw	zero,68(a5)
    sw	zero,72(a5)
    sw	zero,76(a5)
    sw	zero,104(sp)
    lw	a5,76(a5)
    sw	a5,104(sp)
    ttsetc16	37,260
    ttsetc16	38,10272
    ttsetc16	39,4384
    li	s8,0
    mv	a5,s8
    sw	a5,0(s6)
    lw	a5,0(s6)
    and	zero,zero,a5
    lui	a5,0xffb80
    li	s9,4
    sw	s9,0(a5) # ffb80000 <__ldm_bss_end+0x7f720>
    sw	s9,4(a5)
    lui	s9,0x2000
    sw	s9,8(a5)
    sw	s9,12(a5)
    sw	s9,16(a5)
    lui	s10,0x41000
    sw	s10,20(a5)
    sw	s9,24(a5)
    sw	a7,28(a5)
    lui	s9,0x41010
    sw	s9,32(a5)
    sw	a0,0(s7)
    sw	a1,0(s7)
    sw	a2,0(s7)
    sw	a3,0(s7)
    ttstallwait	128,1
    ttwrcfg	28,0,12
    ttwrcfg	29,0,13
    ttnop
    ttnop
    ttsetadcxx	4,15,0
    lui	a5,0xffe80
    addi	a5,a5,4 # ffe80004 <__instrn_buffer+0x40004>
    sw	s8,0(a5)
    lw	s8,0(a5)
    and	zero,zero,s8
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
    lw	s11,308(s5)
    lui	a5,0x508c0
    sw	a5,0(s7)
    addi	a5,s11,-1
    slli	s9,a5,0x8
    srli	a5,a5,0x10
    addi	s10,a4,24
    and	s9,s9,a6
    slli	a5,a5,0x8
    lui	s8,0x800
    add	s9,s9,s10
    or	s8,a5,s8
    addi	s10,a4,25
    sw	s9,0(s7)
    add	s8,s8,s10
    sw	s8,0(s7)
    ttstallwait	128,1
    ttwrcfg	12,0,69
    add	a5,a5,s10
    sw	a5,0(s7)
    ttdmanop
    ttmop	1,0,0
    ttsetadczw	4,0,0,0,0,5
    ttstallwait	64,8
    ttzeroacc	3,1,0,1,0
    ttsemget	2
    lw	a5,296(s5)
    lw	s8,292(s5)
    add	a5,s11,a5
    sw	zero,316(s5)
    sw	a5,308(s5)
    bltu	a5,s8,a25c <.L67>
    lhu	s8,314(s5)
    lw	s11,288(s5)
    addi	s8,s8,1 # 800001 <trisck.cc.a8a8fe81+0x7f348d>
    zext.h	s10,s8
    addi	s8,a4,48
    slli	s9,s10,0x8
    add	s8,s9,s8
    sh	s10,314(s5)
    sub	a5,a5,s11
    sw	s8,0(s7)
    sw	a5,308(s5)
    ttstallwait	32,8
    lw	s8,20(sp)
    lui	a5,0x67612
    addi	s8,s8,-1
    addi	a5,a5,1034 # 6761240a <__device_print_strings_info_end+0x6111240a>
    sw	s8,20(sp)
    sw	a5,0(s7)
    bnez	s8,9a80 <.L70>
    lw	ra,172(sp)
    lw	s0,168(sp)
    lw	s1,164(sp)
    lw	s2,160(sp)
    lw	s3,156(sp)
    lw	s4,152(sp)
    lw	s5,148(sp)
    lw	s6,144(sp)
    lw	s7,140(sp)
    lw	s8,136(sp)
    lw	s9,132(sp)
    lw	s10,128(sp)
    lw	s11,124(sp)
    addi	sp,sp,176
    ret
    lhu	a5,314(s5)
    addi	s9,a4,48
    addi	a5,a5,1
    zext.h	a5,a5
    slli	s8,a5,0x8
    add	s8,s8,s9
    sh	a5,314(s5)
    sw	s8,0(s7)
    j	a200 <.L106>
    lhu	a0,218(s5)
    addi	s1,a5,48
    addi	a0,a0,1 # 508c0001 <__device_print_strings_info_end+0x4a3c0001>
    zext.h	a0,a0
    slli	a6,a0,0x8
    add	a6,a6,s1
    sh	a0,218(s5)
    sw	a6,0(s7)
    j	9548 <.L105>
