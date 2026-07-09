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
    bltu	a4,a3,4f98 <.L22>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,4d24 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,636 # 4fa0 <__kernel_data_lma>
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
    lw	a4,1312(zero) # 520 <.LLST132+0x1>
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
    lui	a3,0xffb46
    lw	a4,32(a3) # ffb46020 <__fw_export_ldm_end+0x453f0>
    zext.h	a4,a4
    lw	a5,40(a3)
    zext.h	a5,a5
    beq	a5,a4,4df4 <.L12>
    lw	a5,-2016(gp) # ffb00010 <crta_l1_base>
    lw	a6,0(a5)
    addi	a7,gp,-1492 # ffb0021c <bank_to_dram_offset>
    addi	t1,gp,-1960 # ffb00048 <dram_bank_to_noc_xy>
    lui	a3,0xffb00
    lw	t3,0(a7)
    lhu	a5,14(t1)
    addi	a3,a3,1068 # ffb0042c <cb_interface>
    lw	t4,208(a3)
    slli	a2,a5,0x4
    lui	a4,0xffb30
    add	t3,a6,t3
    lw	a5,64(a4) # ffb30040 <__fw_export_ldm_end+0x2f410>
    bnez	a5,4e30 <.L14>
    lui	a5,0x2
    addi	a5,a5,146 # 2092 <.LASF188+0x17>
    sw	a5,28(a4)
    sw	t4,0(a4)
    sw	t3,12(a4)
    sw	zero,16(a4)
    srli	a5,a2,0x4
    sw	a5,20(a4)
    lw	a5,4(a0)
    lw	a2,4(a1)
    lui	t3,0x1
    addi	t3,t3,-2048 # 800 <.LLST192+0x9>
    sw	t3,32(a4)
    addi	a5,a5,1
    addi	a2,a2,1
    li	t3,1
    sw	a5,4(a0)
    sw	a2,4(a1)
    sw	t3,64(a4)
    lui	a4,0xffb30
    lw	a5,516(a4) # ffb30204 <__fw_export_ldm_end+0x2f5d4>
    bne	a5,a2,4e88 <.L15>
    fence
    lui	a2,0xffb46
    lw	t3,208(a3)
    lw	a5,200(a3)
    lw	a4,32(a2) # ffb46020 <__fw_export_ldm_end+0x453f0>
    add	a5,a5,t3
    addi	a4,a4,1
    lw	t3,196(a3)
    sw	a5,208(a3)
    sw	a4,32(a2)
    bne	a5,t3,4ec8 <.L16>
    lw	a4,192(a3)
    sub	a5,a5,a4
    sw	a5,208(a3)
    lui	a2,0xffb47
    lw	a4,32(a2) # ffb47020 <__fw_export_ldm_end+0x463f0>
    zext.h	a4,a4
    lw	a5,40(a2)
    zext.h	a5,a5
    beq	a5,a4,4ed4 <.L17>
    lw	a4,4(a7)
    lhu	a5,16(t1)
    lw	a7,240(a3)
    add	a6,a6,a4
    slli	a2,a5,0x4
    lui	a4,0xffb30
    lw	a5,64(a4) # ffb30040 <__fw_export_ldm_end+0x2f410>
    bnez	a5,4ef8 <.L18>
    lui	a5,0x2
    addi	a5,a5,146 # 2092 <.LASF188+0x17>
    sw	a5,28(a4)
    sw	a7,0(a4)
    sw	a6,12(a4)
    sw	zero,16(a4)
    lw	a6,4(a0)
    srli	a5,a2,0x4
    lui	a7,0x1
    lw	a2,4(a1)
    sw	a5,20(a4)
    addi	a5,a7,-2048 # 800 <.LLST192+0x9>
    sw	a5,32(a4)
    addi	a2,a2,1
    addi	a5,a6,1
    sw	a5,4(a0)
    li	a6,1
    sw	a2,4(a1)
    sw	a6,64(a4)
    lui	a4,0xffb30
    lw	a5,516(a4) # ffb30204 <__fw_export_ldm_end+0x2f5d4>
    bne	a5,a2,4f50 <.L19>
    fence
    lui	a2,0xffb47
    lw	a1,240(a3)
    lw	a5,232(a3)
    lw	a4,32(a2) # ffb47020 <__fw_export_ldm_end+0x463f0>
    add	a5,a5,a1
    addi	a4,a4,1
    lw	a1,228(a3)
    sw	a5,240(a3)
    sw	a4,32(a2)
    bne	a5,a1,4f90 <.L20>
    lw	a4,224(a3)
    sub	a5,a5,a4
    sw	a5,240(a3)
    li	a0,0
    ret
    mv	a5,a3
    j	4d18 <.L4>
