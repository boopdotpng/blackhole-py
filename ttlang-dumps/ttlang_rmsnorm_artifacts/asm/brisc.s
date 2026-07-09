    addi	sp,sp,-32
    sw	s0,28(sp)
    sw	s1,24(sp)
    sw	s2,20(sp)
    sw	s3,16(sp)
    sw	s4,12(sp)
    sw	s5,8(sp)
    sw	s6,4(sp)
    sw	s7,0(sp)
    lui	a5,0xffb01
    addi	a5,a5,-960 # ffb00c40 <__fw_export_ldm_end+0x10>
    addi	a4,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    bltu	a4,a5,4d2c <.L2>
    sw	zero,-4(a5)
    sw	zero,-8(a5)
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a5,a5,16
    bgeu	a4,a5,4d14 <.L3>
    addi	a3,a5,-8
    bltu	a4,a3,4f64 <.L19>
    sw	zero,-12(a5)
    sw	zero,-16(a5)
    addi	a3,a5,-4
    bltu	a4,a3,4d48 <.L5>
    sw	zero,-8(a5)
    auipc	a4,0x0
    addi	a4,a4,548 # 4f6c <__kernel_data_lma>
    addi	a5,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    beq	a4,a5,4db4 <.L7>
    addi	a2,gp,1088 # ffb00c30 <__fw_export_ldm_end>
    sub	a2,a2,a5
    li	a1,8
    srai	a3,a2,0x2
    bge	a1,a2,4d98 <.L8>
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
    blt	a6,a3,4d70 <.L9>
    blez	a3,4db4 <.L7>
    lw	a1,0(a4)
    li	a2,2
    sw	a1,0(a5)
    bne	a3,a2,4db4 <.L7>
    lw	a4,4(a4)
    sw	a4,4(a5)
    lui	a5,0xffb30
    lw	t4,520(a5) # ffb30208 <__fw_export_ldm_end+0x2f5d8>
    lw	a6,552(a5)
    lw	a0,516(a5)
    lw	a1,512(a5)
    lw	a2,556(a5)
    lw	a4,1312(zero) # 520 <.LVUS126+0x2>
    sw	a1,-1996(gp) # ffb00024 <noc_nonposted_atomics_acked+0x4>
    addi	t1,gp,-1984 # ffb00030 <noc_nonposted_writes_num_issued>
    addi	t3,gp,-1992 # ffb00028 <noc_nonposted_writes_acked>
    sw	a2,-2004(gp) # ffb0001c <noc_posted_writes_num_issued+0x4>
    sw	t4,-1972(gp) # ffb0003c <noc_reads_num_issued+0x4>
    sw	a6,4(t1)
    slli	a4,a4,0x2
    lbu	a5,1267(a4)
    sw	a0,4(t3)
    li	a3,128
    addi	a4,a4,96
    beq	a5,a3,4e0c <.L13>
    fence
    lbu	a5,1171(a4)
    bne	a5,a3,4e00 <.L11>
    lui	t4,0x92492
    lui	a1,0xffb00
    lui	t5,0x2
    addi	s2,t4,1171 # 92492493 <__device_print_strings_info_end+0x8bf92493>
    addi	a1,a1,1068 # ffb0042c <cb_interface>
    addi	t0,gp,-1492 # ffb0021c <bank_to_dram_offset>
    addi	t6,gp,-1960 # ffb00048 <dram_bank_to_noc_xy>
    addi	t5,t5,146 # 2092 <.LASF945+0x22>
    addi	t4,t4,1216
    li	a0,0
    li	a6,0
    li	a7,0
    lui	a2,0xffb49
    lui	a4,0xffb30
    lui	s0,0x1
    li	t2,1
    li	s3,36
    lw	a3,32(a2) # ffb49020 <__fw_export_ldm_end+0x483f0>
    zext.h	a3,a3
    lw	a5,40(a2)
    zext.h	a5,a5
    beq	a5,a3,4e58 <.L14>
    lw	a3,-2016(gp) # ffb00010 <crta_l1_base>
    srli	a5,a6,0x2
    lw	s6,0(a3)
    slli	s4,a5,0x3
    sub	s4,s4,a5
    sub	s4,a7,s4
    slli	a3,a5,0xc
    sh2add	a5,s4,t0
    sh1add	s4,s4,t6
    lw	s7,0(a5)
    lhu	a5,14(s4)
    lw	s5,304(a1)
    slli	s4,a5,0x4
    add	a3,a3,s6
    add	a3,a3,s7
    lw	a5,64(a4) # ffb30040 <__fw_export_ldm_end+0x2f410>
    bnez	a5,4ea0 <.L15>
    sw	t5,28(a4)
    sw	s5,0(a4)
    sw	a3,12(a4)
    sw	zero,16(a4)
    srli	a5,s4,0x4
    lw	a3,4(t3)
    lw	s4,4(t1)
    sw	a5,20(a4)
    sw	s0,32(a4)
    sw	t2,64(a4)
    addi	a5,s4,1
    addi	a3,a3,1
    sw	a5,4(t1)
    sw	a3,4(t3)
    lw	a5,516(a4)
    bne	a5,a3,4ee0 <.L16>
    fence
    lw	a3,32(a2)
    lw	s4,304(a1)
    lw	a5,296(a1)
    addi	a3,a3,1
    add	a5,a5,s4
    lw	s4,292(a1)
    sw	a3,32(a2)
    sw	a5,304(a1)
    bne	a5,s4,4f1c <.L17>
    lw	a3,288(a1)
    sub	a5,a5,a3
    sw	a5,304(a1)
    add	a5,a0,s2
    sltu	a3,a5,a0
    addi	a7,a7,1
    mv	a0,a5
    add	a6,a3,a6
    bne	a5,t4,4e50 <.L28>
    bne	a6,s3,4e50 <.L28>
    lw	s0,28(sp)
    lw	s1,24(sp)
    lw	s2,20(sp)
    lw	s3,16(sp)
    lw	s4,12(sp)
    lw	s5,8(sp)
    lw	s6,4(sp)
    lw	s7,0(sp)
    li	a0,0
    addi	sp,sp,32
    ret
    mv	a5,a3
    j	4d3c <.L4>
