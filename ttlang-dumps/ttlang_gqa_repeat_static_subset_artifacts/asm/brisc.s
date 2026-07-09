    lui	a5,0xffb01
    addi	a5,a5,-960 # ffb00c40 <__fw_export_ldm_end+0x10>
    addi	a4,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    bltu	a4,a5,4d08 <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,4cf0 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,4fe8 <.L22>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,4d24 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,716 # 4ff0 <__kernel_data_lma>
    addi	a5,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    beq	a4,a5,4d90 <.L7>
    addi	a2,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,4d74 <.L8>
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
    blt	a6,a3,4d4c <.L9>
    blez	a3,4d90 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,4d90 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb30
    lw	t4,520(a5) # ffb30208 <__fw_export_ldm_end+0x2f5d8>
    lw	t1,552(a5)
    lw	a7,516(a5)
    lw	a6,512(a5)
    lw	a2,556(a5)
    lw	a4,1312(zero) # 520 <.LLST122+0x6>
    sw	a6,-1996(gp) # ffb00024 <noc_nonposted_atomics_acked+0x4>
    addi	a0,gp,-1984 # ffb00030 <noc_nonposted_writes_num_issued>
    addi	a1,gp,-1992 # ffb00028 <noc_nonposted_writes_acked>
    sw	a2,-2004(gp) # ffb0001c <noc_posted_writes_num_issued+0x4>
    sw	t4,-1972(gp) # ffb0003c <noc_reads_num_issued+0x4>
    sw	t1,4(a0)
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    sw	a7,4(a1)
    li	a3,128
    addi	a4,a4,96
    beq	a5,a3,4de8 <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,4ddc <.L11>
    lui	a3,0xffb42
    lw	a4,32(a3) # ffb42020 <__fw_export_ldm_end+0x413f0>
    lbu	a6,-1967(gp) # ffb00041 <my_logical_x_>
    lbu	a2,-1968(gp) # ffb00040 <my_logical_y_>
    zext.h	a4,a4
    lw	a5,40(a3)
    zext.h	a5,a5
    beq	a5,a4,4dfc <.L12>
    sh1add	a2,a2,a6
    lw	a4,-2016(gp) # ffb00010 <crta_l1_base>
    lui	a5,0x92492
    lw	t6,0(a4)
    addi	a5,a5,1171 # 92492493 <__device_print_strings_info_end+0x8bf92493>
    mulhu	a5,a2,a5
    srli	a5,a5,0x2
    slli	a4,a5,0x3
    sub	a4,a4,a5
    sub	a2,a2,a4
    addi	t3,a2,7
    addi	t4,gp,-1960 # ffb00048 <dram_bank_to_noc_xy>
    addi	t5,gp,-1492 # ffb0021c <bank_to_dram_offset>
    sh1add	a3,t3,t4
    lui	a7,0xffb00
    sh2add	a4,a2,t5
    slli	a6,a5,0xb
    lw	a4,0(a4)
    lhu	a5,0(a3)
    addi	a7,a7,1068 # ffb0042c <cb_interface>
    add	t6,a6,t6
    lw	t0,80(a7)
    add	t6,t6,a4
    slli	a3,a5,0x4
    lui	a4,0xffb30
    lw	a5,64(a4) # ffb30040 <__fw_export_ldm_end+0x2f410>
    bnez	a5,4e6c <.L14>
    lui	a5,0x2
    addi	a5,a5,146 # 2092 <.LASF203+0x4>
    sw	a5,28(a4)
    sw	t0,0(a4)
    sw	t6,12(a4)
    sw	zero,16(a4)
    srli	a5,a3,0x4
    sw	a5,20(a4)
    lw	a5,4(a0)
    lw	a3,4(a1)
    lui	t6,0x1
    addi	t6,t6,-2048 # 800 <.LLST190+0x5>
    sw	t6,32(a4)
    addi	a5,a5,1
    addi	a3,a3,1
    li	t6,1
    sw	a5,4(a0)
    sw	a3,4(a1)
    sw	t6,64(a4)
    lui	a4,0xffb30
    lw	a5,516(a4) # ffb30204 <__fw_export_ldm_end+0x2f5d4>
    bne	a5,a3,4ec4 <.L15>
    fence
    lui	a3,0xffb42
    lw	t6,80(a7)
    lw	a5,72(a7)
    lw	a4,32(a3) # ffb42020 <__fw_export_ldm_end+0x413f0>
    add	a5,a5,t6
    addi	a4,a4,1
    lw	t6,68(a7)
    sw	a5,80(a7)
    sw	a4,32(a3)
    bne	a5,t6,4f04 <.L16>
    lw	a4,64(a7)
    sub	a5,a5,a4
    sw	a5,80(a7)
    lui	a3,0xffb43
    lw	a4,32(a3) # ffb43020 <__fw_export_ldm_end+0x423f0>
    zext.h	a4,a4
    lw	a5,40(a3)
    zext.h	a5,a5
    beq	a4,a5,4f10 <.L17>
    lw	a5,-2016(gp) # ffb00010 <crta_l1_base>
    sh1add	t3,t3,t4
    sh2add	a2,a2,t5
    lw	t1,0(a2)
    lw	t4,4(a5)
    lhu	a5,0(t3)
    lw	a2,112(a7)
    slli	a3,a5,0x4
    lui	a4,0xffb30
    add	a6,a6,t4
    add	a6,a6,t1
    lw	a5,64(a4) # ffb30040 <__fw_export_ldm_end+0x2f410>
    bnez	a5,4f48 <.L18>
    lui	a5,0x2
    addi	a5,a5,146 # 2092 <.LASF203+0x4>
    sw	a5,28(a4)
    sw	a2,0(a4)
    sw	a6,12(a4)
    sw	zero,16(a4)
    lw	a2,4(a0)
    srli	a5,a3,0x4
    lui	a6,0x1
    lw	a3,4(a1)
    sw	a5,20(a4)
    addi	a5,a6,-2048 # 800 <.LLST190+0x5>
    sw	a5,32(a4)
    addi	a3,a3,1
    addi	a5,a2,1
    sw	a5,4(a0)
    li	a2,1
    sw	a3,4(a1)
    sw	a2,64(a4)
    lui	a4,0xffb30
    lw	a5,516(a4) # ffb30204 <__fw_export_ldm_end+0x2f5d4>
    bne	a5,a3,4fa0 <.L19>
    fence
    lui	a3,0xffb43
    lw	a2,112(a7)
    lw	a5,104(a7)
    lw	a4,32(a3) # ffb43020 <__fw_export_ldm_end+0x423f0>
    add	a5,a5,a2
    addi	a4,a4,1
    lw	a2,100(a7)
    sw	a5,112(a7)
    sw	a4,32(a3)
    bne	a5,a2,4fe0 <.L20>
    lw	a4,96(a7)
    sub	a5,a5,a4
    sw	a5,112(a7)
    li	a0,0
    ret
    mv	a5,a3
    j	4d18 <.L4>
