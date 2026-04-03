
/tmp/tt-disasm-rx66rrqr/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00003840 <_start>:
    3840:	ffb001b7          	lui	gp,0xffb00
    3844:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    3848:	ffb02137          	lui	sp,0xffb02
    384c:	ff010113          	addi	sp,sp,-16 # ffb01ff0 <__fw_export_ldm_end+0x1770>
    3850:	00810513          	addi	a0,sp,8
    3854:	00a12023          	sw	a0,0(sp)
    3858:	00012223          	sw	zero,4(sp)
    385c:	00912423          	sw	s1,8(sp)
    3860:	00012623          	sw	zero,12(sp)
    3864:	00100513          	li	a0,1
    3868:	00010593          	mv	a1,sp
    386c:	00000613          	li	a2,0
    3870:	008000ef          	jal	3878 <main>
    3874:	1580106f          	j	49cc <exit>

00003878 <main>:
    3878:	fb010113          	addi	sp,sp,-80
    387c:	04112623          	sw	ra,76(sp)
    3880:	04812423          	sw	s0,72(sp)
    3884:	04912223          	sw	s1,68(sp)
    3888:	05212023          	sw	s2,64(sp)
    388c:	03312e23          	sw	s3,60(sp)
    3890:	03412c23          	sw	s4,56(sp)
    3894:	03512a23          	sw	s5,52(sp)
    3898:	03612823          	sw	s6,48(sp)
    389c:	03712623          	sw	s7,44(sp)
    38a0:	03812423          	sw	s8,40(sp)
    38a4:	03912223          	sw	s9,36(sp)
    38a8:	03a12023          	sw	s10,32(sp)
    38ac:	01b12e23          	sw	s11,28(sp)
    38b0:	00200313          	li	t1,2
    38b4:	7c032073          	csrs	0x7c0,t1
    38b8:	00100313          	li	t1,1
    38bc:	01231313          	slli	t1,t1,0x12
    38c0:	0ff0000f          	fence
    38c4:	7c032073          	csrs	0x7c0,t1
    38c8:	00200313          	li	t1,2
    38cc:	7c033073          	csrc	0x7c0,t1
    38d0:	0ff0000f          	fence
    38d4:	0ff0000f          	fence
    38d8:	00800313          	li	t1,8
    38dc:	7c032073          	csrs	0x7c0,t1
    38e0:	ffb015b7          	lui	a1,0xffb01
    38e4:	87858593          	addi	a1,a1,-1928 # ffb00878 <__ldm_bss_end>
    38e8:	81418513          	addi	a0,gp,-2028 # ffb00004 <my_y>
    38ec:	050010ef          	jal	493c <wzerorange>
    38f0:	000085b7          	lui	a1,0x8
    38f4:	81018513          	addi	a0,gp,-2032 # ffb00000 <_ZL16subordinate_sync>
    38f8:	6b058593          	addi	a1,a1,1712 # 86b0 <__fw_export_text_end+0x3ce0>
    38fc:	00b50c63          	beq	a0,a1,3914 <main+0x9c>
    3900:	ffb00637          	lui	a2,0xffb00
    3904:	00460613          	addi	a2,a2,4 # ffb00004 <my_y>
    3908:	40a60633          	sub	a2,a2,a0
    390c:	40265613          	srai	a2,a2,0x2
    3910:	070010ef          	jal	4980 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3914:	85818993          	addi	s3,gp,-1960 # ffb00048 <cb_interface>
    3918:	00011437          	lui	s0,0x11
    391c:	6b040593          	addi	a1,s0,1712 # 116b0 <__fw_export_text_end+0xcce0>
    3920:	00700613          	li	a2,7
    3924:	40098513          	addi	a0,s3,1024
    3928:	058010ef          	jal	4980 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    392c:	ffb01937          	lui	s2,0xffb01
    3930:	6cc40593          	addi	a1,s0,1740
    3934:	07800613          	li	a2,120
    3938:	41c98513          	addi	a0,s3,1052
    393c:	044010ef          	jal	4980 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3940:	00012437          	lui	s0,0x12
    3944:	8ac40593          	addi	a1,s0,-1876 # 118ac <__fw_export_text_end+0xcedc>
    3948:	00700613          	li	a2,7
    394c:	5fc98513          	addi	a0,s3,1532
    3950:	030010ef          	jal	4980 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3954:	04890913          	addi	s2,s2,72 # ffb01048 <__fw_export_ldm_end+0x7c8>
    3958:	8c840593          	addi	a1,s0,-1848
    395c:	07800613          	li	a2,120
    3960:	61898513          	addi	a0,s3,1560
    3964:	01c010ef          	jal	4980 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3968:	eb040593          	addi	a1,s0,-336
    396c:	00500613          	li	a2,5
    3970:	7f898513          	addi	a0,s3,2040
    3974:	00c010ef          	jal	4980 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3978:	000014b7          	lui	s1,0x1
    397c:	ec440593          	addi	a1,s0,-316
    3980:	00300613          	li	a2,3
    3984:	80c90513          	addi	a0,s2,-2036
    3988:	7f9000ef          	jal	4980 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    398c:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    3990:	84018b23          	sb	zero,-1962(gp) # ffb00046 <noc_index>
    3994:	9a04c703          	lbu	a4,-1632(s1) # 9a0 <_start-0x2ea0>
    3998:	ffe40a37          	lui	s4,0xffe40
    399c:	ffb12ab7          	lui	s5,0xffb12
    39a0:	00000513          	li	a0,0
    39a4:	00100413          	li	s0,1
    39a8:	84e18aa3          	sb	a4,-1963(gp) # ffb00045 <my_logical_x_>
    39ac:	9a14c783          	lbu	a5,-1631(s1)
    39b0:	84f18a23          	sb	a5,-1964(gp) # ffb00044 <my_logical_y_>
    39b4:	ffb207b7          	lui	a5,0xffb20
    39b8:	1487a703          	lw	a4,328(a5) # ffb20148 <__stack_top+0x1e148>
    39bc:	03f77793          	andi	a5,a4,63
    39c0:	00675713          	srli	a4,a4,0x6
    39c4:	03f77713          	andi	a4,a4,63
    39c8:	80f18c23          	sb	a5,-2024(gp) # ffb00008 <my_x>
    39cc:	80e18a23          	sb	a4,-2028(gp) # ffb00004 <my_y>
    39d0:	ffb307b7          	lui	a5,0xffb30
    39d4:	1487a703          	lw	a4,328(a5) # ffb30148 <__stack_top+0x2e148>
    39d8:	81818613          	addi	a2,gp,-2024 # ffb00008 <my_x>
    39dc:	03f77793          	andi	a5,a4,63
    39e0:	00f600a3          	sb	a5,1(a2)
    39e4:	000a0793          	mv	a5,s4
    39e8:	80f92c23          	sw	a5,-2024(s2)
    39ec:	ffe507b7          	lui	a5,0xffe50
    39f0:	00078793          	mv	a5,a5
    39f4:	80f92e23          	sw	a5,-2020(s2)
    39f8:	00675713          	srli	a4,a4,0x6
    39fc:	ffe607b7          	lui	a5,0xffe60
    3a00:	81418693          	addi	a3,gp,-2028 # ffb00004 <my_y>
    3a04:	03f77713          	andi	a4,a4,63
    3a08:	00078793          	mv	a5,a5
    3a0c:	00e680a3          	sb	a4,1(a3)
    3a10:	82f92023          	sw	a5,-2016(s2)
    3a14:	03f00713          	li	a4,63
    3a18:	ffb117b7          	lui	a5,0xffb11
    3a1c:	240aa023          	sw	zero,576(s5) # ffb12240 <__stack_top+0x10240>
    3a20:	02e7a223          	sw	a4,36(a5) # ffb11024 <__stack_top+0xf024>
    3a24:	8001ae23          	sw	zero,-2020(gp) # ffb0000c <_ZL19active_noc_instance>
    3a28:	6f1000ef          	jal	4918 <_Z15noc_get_cfg_regm>
    3a2c:	00156593          	ori	a1,a0,1
    3a30:	00000513          	li	a0,0
    3a34:	6c1000ef          	jal	48f4 <_Z15noc_set_cfg_regmm>
    3a38:	00100513          	li	a0,1
    3a3c:	6dd000ef          	jal	4918 <_Z15noc_get_cfg_regm>
    3a40:	00156593          	ori	a1,a0,1
    3a44:	00100513          	li	a0,1
    3a48:	6ad000ef          	jal	48f4 <_Z15noc_set_cfg_regmm>
    3a4c:	8081ae23          	sw	s0,-2020(gp) # ffb0000c <_ZL19active_noc_instance>
    3a50:	00000513          	li	a0,0
    3a54:	6c5000ef          	jal	4918 <_Z15noc_get_cfg_regm>
    3a58:	008565b3          	or	a1,a0,s0
    3a5c:	00000513          	li	a0,0
    3a60:	695000ef          	jal	48f4 <_Z15noc_set_cfg_regmm>
    3a64:	00040513          	mv	a0,s0
    3a68:	6b1000ef          	jal	4918 <_Z15noc_get_cfg_regm>
    3a6c:	008565b3          	or	a1,a0,s0
    3a70:	00040513          	mv	a0,s0
    3a74:	681000ef          	jal	48f4 <_Z15noc_set_cfg_regmm>
    3a78:	8001ae23          	sw	zero,-2020(gp) # ffb0000c <_ZL19active_noc_instance>
    3a7c:	00700793          	li	a5,7
    3a80:	22faaa23          	sw	a5,564(s5)
    3a84:	00003537          	lui	a0,0x3
    3a88:	44050593          	addi	a1,a0,1088 # 3440 <_start-0x400>
    3a8c:	228aae23          	sw	s0,572(s5)
    3a90:	24050513          	addi	a0,a0,576
    3a94:	6a9000ef          	jal	493c <wzerorange>
    3a98:	ffef0737          	lui	a4,0xffef0
    3a9c:	01f00793          	li	a5,31
    3aa0:	2ef72223          	sw	a5,740(a4) # ffef02e4 <__instrn_buffer+0xb02e4>
    3aa4:	101807b7          	lui	a5,0x10180
    3aa8:	00fa2023          	sw	a5,0(s4) # ffe40000 <__instrn_buffer>
    3aac:	8a0037b7          	lui	a5,0x8a003
    3ab0:	00a78793          	addi	a5,a5,10 # 8a00300a <__fw_export_text_end+0x89ffe63a>
    3ab4:	00fa2023          	sw	a5,0(s4)
    3ab8:	020007b7          	lui	a5,0x2000
    3abc:	00fa2023          	sw	a5,0(s4)
    3ac0:	7100c7b7          	lui	a5,0x7100c
    3ac4:	f8078793          	addi	a5,a5,-128 # 7100bf80 <__fw_export_text_end+0x710075b0>
    3ac8:	00fa2023          	sw	a5,0(s4)
    3acc:	910007b7          	lui	a5,0x91000
    3ad0:	0b078793          	addi	a5,a5,176 # 910000b0 <__fw_export_text_end+0x90ffb6e0>
    3ad4:	00fa2023          	sw	a5,0(s4)
    3ad8:	00c72783          	lw	a5,12(a4)
    3adc:	000046b7          	lui	a3,0x4
    3ae0:	0087e7b3          	or	a5,a5,s0
    3ae4:	00f72623          	sw	a5,12(a4)
    3ae8:	00c72783          	lw	a5,12(a4)
    3aec:	ff868693          	addi	a3,a3,-8 # 3ff8 <.NO_CB1058+0x114>
    3af0:	0027e793          	ori	a5,a5,2
    3af4:	00f72623          	sw	a5,12(a4)
    3af8:	00c72603          	lw	a2,12(a4)
    3afc:	80048793          	addi	a5,s1,-2048
    3b00:	00f647b3          	xor	a5,a2,a5
    3b04:	00d7f7b3          	and	a5,a5,a3
    3b08:	00c7c7b3          	xor	a5,a5,a2
    3b0c:	00f72623          	sw	a5,12(a4)
    3b10:	a31007b7          	lui	a5,0xa3100
    3b14:	00878713          	addi	a4,a5,8 # a3100008 <__fw_export_text_end+0xa30fb638>
    3b18:	00ea2023          	sw	a4,0(s4)
    3b1c:	01078713          	addi	a4,a5,16
    3b20:	00ea2023          	sw	a4,0(s4)
    3b24:	20078793          	addi	a5,a5,512
    3b28:	00fa2023          	sw	a5,0(s4)
    3b2c:	8101a683          	lw	a3,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    3b30:	404047b7          	lui	a5,0x40404
    3b34:	06002023          	sw	zero,96(zero) # 60 <_start-0x37e0>
    3b38:	04078793          	addi	a5,a5,64 # 40404040 <__fw_export_text_end+0x403ff670>
    3b3c:	00f6a023          	sw	a5,0(a3)
    3b40:	1a0aa823          	sw	zero,432(s5)
    3b44:	0006a783          	lw	a5,0(a3)
    3b48:	4e079863          	bnez	a5,4038 <.NO_CB1058+0x154>
    3b4c:	360009a3          	sb	zero,883(zero) # 373 <_start-0x34cd>
    3b50:	ffb20737          	lui	a4,0xffb20
    3b54:	14872583          	lw	a1,328(a4) # ffb20148 <__stack_top+0x1e148>
    3b58:	00072223          	sw	zero,4(a4)
    3b5c:	0065d793          	srli	a5,a1,0x6
    3b60:	03f7f793          	andi	a5,a5,63
    3b64:	03f5f593          	andi	a1,a1,63
    3b68:	00459593          	slli	a1,a1,0x4
    3b6c:	00a79793          	slli	a5,a5,0xa
    3b70:	00b7e7b3          	or	a5,a5,a1
    3b74:	0047d793          	srli	a5,a5,0x4
    3b78:	00f72423          	sw	a5,8(a4)
    3b7c:	ffb215b7          	lui	a1,0xffb21
    3b80:	0005a223          	sw	zero,4(a1) # ffb21004 <__stack_top+0x1f004>
    3b84:	00f5a423          	sw	a5,8(a1)
    3b88:	ffb22437          	lui	s0,0xffb22
    3b8c:	00400893          	li	a7,4
    3b90:	81142623          	sw	a7,-2036(s0) # ffb2180c <__stack_top+0x1f80c>
    3b94:	80042823          	sw	zero,-2032(s0)
    3b98:	00002537          	lui	a0,0x2
    3b9c:	80f42a23          	sw	a5,-2028(s0)
    3ba0:	09050513          	addi	a0,a0,144 # 2090 <_start-0x17b0>
    3ba4:	80a5ae23          	sw	a0,-2020(a1)
    3ba8:	8005a823          	sw	zero,-2032(a1)
    3bac:	80f5aa23          	sw	a5,-2028(a1)
    3bb0:	ffb30837          	lui	a6,0xffb30
    3bb4:	14882583          	lw	a1,328(a6) # ffb30148 <__stack_top+0x2e148>
    3bb8:	00082223          	sw	zero,4(a6)
    3bbc:	0065d793          	srli	a5,a1,0x6
    3bc0:	03f7f793          	andi	a5,a5,63
    3bc4:	03f5f593          	andi	a1,a1,63
    3bc8:	00459593          	slli	a1,a1,0x4
    3bcc:	00a79793          	slli	a5,a5,0xa
    3bd0:	00b7e7b3          	or	a5,a5,a1
    3bd4:	0047d793          	srli	a5,a5,0x4
    3bd8:	00f82423          	sw	a5,8(a6)
    3bdc:	ffb315b7          	lui	a1,0xffb31
    3be0:	0005a223          	sw	zero,4(a1) # ffb31004 <__stack_top+0x2f004>
    3be4:	00f5a423          	sw	a5,8(a1)
    3be8:	ffb32837          	lui	a6,0xffb32
    3bec:	81182623          	sw	a7,-2036(a6) # ffb3180c <__stack_top+0x2f80c>
    3bf0:	80082823          	sw	zero,-2032(a6)
    3bf4:	80f82a23          	sw	a5,-2028(a6)
    3bf8:	80a5ae23          	sw	a0,-2020(a1)
    3bfc:	8005a823          	sw	zero,-2032(a1)
    3c00:	80f5aa23          	sw	a5,-2028(a1)
    3c04:	8561c783          	lbu	a5,-1962(gp) # ffb00046 <noc_index>
    3c08:	20870513          	addi	a0,a4,520
    3c0c:	01079593          	slli	a1,a5,0x10
    3c10:	00a58533          	add	a0,a1,a0
    3c14:	00052303          	lw	t1,0(a0)
    3c18:	22870513          	addi	a0,a4,552
    3c1c:	00a58533          	add	a0,a1,a0
    3c20:	00052883          	lw	a7,0(a0)
    3c24:	20470513          	addi	a0,a4,516
    3c28:	00a58533          	add	a0,a1,a0
    3c2c:	00052803          	lw	a6,0(a0)
    3c30:	20070513          	addi	a0,a4,512
    3c34:	22c70713          	addi	a4,a4,556
    3c38:	00a58533          	add	a0,a1,a0
    3c3c:	00e585b3          	add	a1,a1,a4
    3c40:	00052503          	lw	a0,0(a0)
    3c44:	0005a703          	lw	a4,0(a1)
    3c48:	84c18593          	addi	a1,gp,-1972 # ffb0003c <noc_reads_num_issued>
    3c4c:	00b12223          	sw	a1,4(sp)
    3c50:	20b7c5b3          	sh2add	a1,a5,a1
    3c54:	0065a023          	sw	t1,0(a1)
    3c58:	84418593          	addi	a1,gp,-1980 # ffb00034 <noc_nonposted_writes_num_issued>
    3c5c:	00b12423          	sw	a1,8(sp)
    3c60:	20b7c5b3          	sh2add	a1,a5,a1
    3c64:	83c18c13          	addi	s8,gp,-1988 # ffb0002c <noc_nonposted_writes_acked>
    3c68:	0115a023          	sw	a7,0(a1)
    3c6c:	2187c5b3          	sh2add	a1,a5,s8
    3c70:	83418c93          	addi	s9,gp,-1996 # ffb00024 <noc_nonposted_atomics_acked>
    3c74:	82c18b13          	addi	s6,gp,-2004 # ffb0001c <noc_posted_writes_num_issued>
    3c78:	0105a023          	sw	a6,0(a1)
    3c7c:	2197c5b3          	sh2add	a1,a5,s9
    3c80:	2167c7b3          	sh2add	a5,a5,s6
    3c84:	00a5a023          	sw	a0,0(a1)
    3c88:	00e7a023          	sw	a4,0(a5)
    3c8c:	8101aa03          	lw	s4,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    3c90:	00300793          	li	a5,3
    3c94:	00f680a3          	sb	a5,1(a3)
    3c98:	ffb707b7          	lui	a5,0xffb70
    3c9c:	000025b7          	lui	a1,0x2
    3ca0:	0c000d93          	li	s11,192
    3ca4:	43878d13          	addi	s10,a5,1080 # ffb70438 <__stack_top+0x6e438>
    3ca8:	84040a93          	addi	s5,s0,-1984
    3cac:	04000493          	li	s1,64
    3cb0:	81c40813          	addi	a6,s0,-2020
    3cb4:	08a58593          	addi	a1,a1,138 # 208a <_start-0x17b6>
    3cb8:	80040893          	addi	a7,s0,-2048
    3cbc:	80440313          	addi	t1,s0,-2044
    3cc0:	80840e13          	addi	t3,s0,-2040
    3cc4:	82040e93          	addi	t4,s0,-2016
    3cc8:	00100f13          	li	t5,1
    3ccc:	0e000f93          	li	t6,224
    3cd0:	0f000293          	li	t0,240
    3cd4:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3cd8:	08000693          	li	a3,128
    3cdc:	00279793          	slli	a5,a5,0x2
    3ce0:	37078793          	addi	a5,a5,880
    3ce4:	0037c783          	lbu	a5,3(a5)
    3ce8:	0ff7f713          	zext.b	a4,a5
    3cec:	02d78263          	beq	a5,a3,3d10 <main+0x498>
    3cf0:	06c02783          	lw	a5,108(zero) # 6c <_start-0x37d4>
    3cf4:	06000693          	li	a3,96
    3cf8:	00178793          	addi	a5,a5,1
    3cfc:	02d787b3          	mul	a5,a5,a3
    3d00:	00d787b3          	add	a5,a5,a3
    3d04:	00f7c783          	lbu	a5,15(a5)
    3d08:	60479793          	sext.b	a5,a5
    3d0c:	3207de63          	bgez	a5,4048 <.NO_CB1058+0x164>
    3d10:	06c02a83          	lw	s5,108(zero) # 6c <_start-0x37d4>
    3d14:	06000493          	li	s1,96
    3d18:	029a84b3          	mul	s1,s5,s1
    3d1c:	0bc4a683          	lw	a3,188(s1)
    3d20:	07048493          	addi	s1,s1,112
    3d24:	0026f593          	andi	a1,a3,2
    3d28:	3c059c63          	bnez	a1,4100 <.NO_CB1058+0x21c>
    3d2c:	06c02783          	lw	a5,108(zero) # 6c <_start-0x37d4>
    3d30:	06000713          	li	a4,96
    3d34:	02e787b3          	mul	a5,a5,a4
    3d38:	00e787b3          	add	a5,a5,a4
    3d3c:	0107ad03          	lw	s10,16(a5)
    3d40:	01c7d703          	lhu	a4,28(a5)
    3d44:	0147a603          	lw	a2,20(a5)
    3d48:	01a70733          	add	a4,a4,s10
    3d4c:	82e92223          	sw	a4,-2012(s2)
    3d50:	01e7d703          	lhu	a4,30(a5)
    3d54:	00c70733          	add	a4,a4,a2
    3d58:	82e92423          	sw	a4,-2008(s2)
    3d5c:	0187a603          	lw	a2,24(a5)
    3d60:	0207d703          	lhu	a4,32(a5)
    3d64:	00c70733          	add	a4,a4,a2
    3d68:	82e92623          	sw	a4,-2004(s2)
    3d6c:	0267d703          	lhu	a4,38(a5)
    3d70:	0287d783          	lhu	a5,40(a5)
    3d74:	01a70733          	add	a4,a4,s10
    3d78:	82e1a423          	sw	a4,-2008(gp) # ffb00018 <rta_l1_base>
    3d7c:	01a787b3          	add	a5,a5,s10
    3d80:	82f1a223          	sw	a5,-2012(gp) # ffb00014 <crta_l1_base>
    3d84:	ffef07b7          	lui	a5,0xffef0
    3d88:	01f00713          	li	a4,31
    3d8c:	2ee7a223          	sw	a4,740(a5) # ffef02e4 <__instrn_buffer+0xb02e4>
    3d90:	001a4783          	lbu	a5,1(s4)
    3d94:	36079c63          	bnez	a5,410c <.NO_CB1058+0x228>
    3d98:	0046f793          	andi	a5,a3,4
    3d9c:	00078a63          	beqz	a5,3db0 <main+0x538>
    3da0:	f8000793          	li	a5,-128
    3da4:	00fa00a3          	sb	a5,1(s4)
    3da8:	00fa0123          	sb	a5,2(s4)
    3dac:	00fa01a3          	sb	a5,3(s4)
    3db0:	0444c603          	lbu	a2,68(s1)
    3db4:	8551c783          	lbu	a5,-1963(gp) # ffb00045 <my_logical_x_>
    3db8:	0454c803          	lbu	a6,69(s1)
    3dbc:	05c4c703          	lbu	a4,92(s1)
    3dc0:	0ff67613          	zext.b	a2,a2
    3dc4:	40e787b3          	sub	a5,a5,a4
    3dc8:	82f18123          	sb	a5,-2014(gp) # ffb00012 <my_relative_x_>
    3dcc:	05d4c703          	lbu	a4,93(s1)
    3dd0:	8541c783          	lbu	a5,-1964(gp) # ffb00044 <my_logical_y_>
    3dd4:	40e787b3          	sub	a5,a5,a4
    3dd8:	82f180a3          	sb	a5,-2015(gp) # ffb00011 <my_relative_y_>
    3ddc:	84c18b23          	sb	a2,-1962(gp) # ffb00046 <noc_index>
    3de0:	8201c783          	lbu	a5,-2016(gp) # ffb00010 <prev_noc_mode>
    3de4:	0ff87313          	zext.b	t1,a6
    3de8:	ffb20737          	lui	a4,0xffb20
    3dec:	3c081c63          	bnez	a6,41c4 <.NO_CB1058+0x2e0>
    3df0:	32079263          	bnez	a5,4114 <.NO_CB1058+0x230>
    3df4:	ffb20737          	lui	a4,0xffb20
    3df8:	01061793          	slli	a5,a2,0x10
    3dfc:	20870813          	addi	a6,a4,520 # ffb20208 <__stack_top+0x1e208>
    3e00:	01078833          	add	a6,a5,a6
    3e04:	00082e83          	lw	t4,0(a6)
    3e08:	22870813          	addi	a6,a4,552
    3e0c:	01078833          	add	a6,a5,a6
    3e10:	00082e03          	lw	t3,0(a6)
    3e14:	20470813          	addi	a6,a4,516
    3e18:	01078833          	add	a6,a5,a6
    3e1c:	00082883          	lw	a7,0(a6)
    3e20:	20070813          	addi	a6,a4,512
    3e24:	22c70713          	addi	a4,a4,556
    3e28:	01078833          	add	a6,a5,a6
    3e2c:	00e787b3          	add	a5,a5,a4
    3e30:	00082803          	lw	a6,0(a6)
    3e34:	0007a703          	lw	a4,0(a5)
    3e38:	00412783          	lw	a5,4(sp)
    3e3c:	20f647b3          	sh2add	a5,a2,a5
    3e40:	01d7a023          	sw	t4,0(a5)
    3e44:	00812783          	lw	a5,8(sp)
    3e48:	20f647b3          	sh2add	a5,a2,a5
    3e4c:	01c7a023          	sw	t3,0(a5)
    3e50:	218647b3          	sh2add	a5,a2,s8
    3e54:	0117a023          	sw	a7,0(a5)
    3e58:	219647b3          	sh2add	a5,a2,s9
    3e5c:	0107a023          	sw	a6,0(a5)
    3e60:	216647b3          	sh2add	a5,a2,s6
    3e64:	00e7a023          	sw	a4,0(a5)
    3e68:	00300713          	li	a4,3
    3e6c:	0124d783          	lhu	a5,18(s1)
    3e70:	82618023          	sb	t1,-2016(gp) # ffb00010 <prev_noc_mode>
    3e74:	0807c7b3          	zext.h	a5,a5
    3e78:	00058663          	beqz	a1,3e84 <main+0x60c>
    3e7c:	f8000593          	li	a1,-128
    3e80:	00ba0023          	sb	a1,0(s4)
    3e84:	0016f693          	andi	a3,a3,1
    3e88:	44068063          	beqz	a3,42c8 <.NO_CB1058+0x3e4>
    3e8c:	0404a583          	lw	a1,64(s1)
    3e90:	01a787b3          	add	a5,a5,s10
    3e94:	00098513          	mv	a0,s3
    3e98:	0580006f          	j	3ef0 <.NO_CB1058+0xc>
    3e9c:	0047a683          	lw	a3,4(a5)
    3ea0:	0007a603          	lw	a2,0(a5)
    3ea4:	0087a803          	lw	a6,8(a5)
    3ea8:	00c7a883          	lw	a7,12(a5)
    3eac:	0015d593          	srli	a1,a1,0x1
    3eb0:	0015f293          	andi	t0,a1,1
    3eb4:	00052c23          	sw	zero,24(a0)
    3eb8:	01078793          	addi	a5,a5,16
    3ebc:	00d52023          	sw	a3,0(a0)
    3ec0:	00d606b3          	add	a3,a2,a3
    3ec4:	00d52223          	sw	a3,4(a0)
    3ec8:	00c52a23          	sw	a2,20(a0)
    3ecc:	01052623          	sw	a6,12(a0)
    3ed0:	00c52823          	sw	a2,16(a0)
    3ed4:	01152423          	sw	a7,8(a0)
    3ed8:	02050513          	addi	a0,a0,32
    3edc:	fc0290e3          	bnez	t0,3e9c <main+0x624>
    3ee0:	00058e63          	beqz	a1,3efc <.NO_CB1058+0x18>

00003ee4 <.NO_CB1058>:
    3ee4:	01078793          	addi	a5,a5,16
    3ee8:	02050513          	addi	a0,a0,32
    3eec:	0015d593          	srli	a1,a1,0x1
    3ef0:	0015f293          	andi	t0,a1,1
    3ef4:	fa0294e3          	bnez	t0,3e9c <main+0x624>
    3ef8:	fe0596e3          	bnez	a1,3ee4 <.NO_CB1058>
    3efc:	0144d503          	lhu	a0,20(s1)
    3f00:	0464cd83          	lbu	s11,70(s1)
    3f04:	8561c603          	lbu	a2,-1962(gp) # ffb00046 <noc_index>
    3f08:	0ffdfd93          	zext.b	s11,s11
    3f0c:	00030693          	mv	a3,t1
    3f10:	000d8593          	mv	a1,s11
    3f14:	01a50533          	add	a0,a0,s10
    3f18:	00c12623          	sw	a2,12(sp)
    3f1c:	40c000ef          	jal	4328 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    3f20:	02000793          	li	a5,32
    3f24:	00fd8663          	beq	s11,a5,3f30 <.NO_CB1058+0x4c>
    3f28:	00c12503          	lw	a0,12(sp)
    3f2c:	19d000ef          	jal	48c8 <_Z33barrier_remote_cb_interface_setuphm.part.0>
    3f30:	02c4a783          	lw	a5,44(s1)
    3f34:	01a787b3          	add	a5,a5,s10
    3f38:	000780e7          	jalr	a5
    3f3c:	000a2783          	lw	a5,0(s4)
    3f40:	3e079063          	bnez	a5,4320 <.NO_CB1058+0x43c>
    3f44:	00300793          	li	a5,3
    3f48:	00fa00a3          	sb	a5,1(s4)
    3f4c:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3f50:	00279793          	slli	a5,a5,0x2
    3f54:	360789a3          	sb	zero,883(a5)
    3f58:	02a4c703          	lbu	a4,42(s1)
    3f5c:	06078793          	addi	a5,a5,96
    3f60:	d2071ce3          	bnez	a4,3c98 <main+0x420>
    3f64:	0404a623          	sw	zero,76(s1)
    3f68:	8561c583          	lbu	a1,-1962(gp) # ffb00046 <noc_index>
    3f6c:	04048fa3          	sb	zero,95(s1)
    3f70:	3107a703          	lw	a4,784(a5)
    3f74:	84040513          	addi	a0,s0,-1984
    3f78:	01059793          	slli	a5,a1,0x10
    3f7c:	00a78533          	add	a0,a5,a0
    3f80:	00052683          	lw	a3,0(a0)
    3f84:	fe069ee3          	bnez	a3,3f80 <.NO_CB1058+0x9c>
    3f88:	01075613          	srli	a2,a4,0x10
    3f8c:	00875693          	srli	a3,a4,0x8
    3f90:	0ff67613          	zext.b	a2,a2
    3f94:	0ff6f693          	zext.b	a3,a3
    3f98:	00469693          	slli	a3,a3,0x4
    3f9c:	00a61613          	slli	a2,a2,0xa
    3fa0:	00d66633          	or	a2,a2,a3
    3fa4:	0ff77713          	zext.b	a4,a4
    3fa8:	ffb706b7          	lui	a3,0xffb70
    3fac:	43868693          	addi	a3,a3,1080 # ffb70438 <__stack_top+0x6e438>
    3fb0:	00c71713          	slli	a4,a4,0xc
    3fb4:	00d70733          	add	a4,a4,a3
    3fb8:	82840693          	addi	a3,s0,-2008
    3fbc:	00d786b3          	add	a3,a5,a3
    3fc0:	04000813          	li	a6,64
    3fc4:	0106a023          	sw	a6,0(a3)
    3fc8:	81c40693          	addi	a3,s0,-2020
    3fcc:	00002837          	lui	a6,0x2
    3fd0:	00d786b3          	add	a3,a5,a3
    3fd4:	08a80813          	addi	a6,a6,138 # 208a <_start-0x17b6>
    3fd8:	0106a023          	sw	a6,0(a3)
    3fdc:	80040693          	addi	a3,s0,-2048
    3fe0:	00d786b3          	add	a3,a5,a3
    3fe4:	00e6a023          	sw	a4,0(a3)
    3fe8:	80440713          	addi	a4,s0,-2044
    3fec:	00e78733          	add	a4,a5,a4
    3ff0:	00072023          	sw	zero,0(a4)
    3ff4:	80840713          	addi	a4,s0,-2040
    3ff8:	00e78733          	add	a4,a5,a4
    3ffc:	00465613          	srli	a2,a2,0x4
    4000:	00c72023          	sw	a2,0(a4)
    4004:	82040713          	addi	a4,s0,-2016
    4008:	00e787b3          	add	a5,a5,a4
    400c:	0007a023          	sw	zero,0(a5)
    4010:	00100793          	li	a5,1
    4014:	00f52023          	sw	a5,0(a0)
    4018:	2165c7b3          	sh2add	a5,a1,s6
    401c:	0007a703          	lw	a4,0(a5)
    4020:	001a8a93          	addi	s5,s5,1
    4024:	00170713          	addi	a4,a4,1
    4028:	00e7a023          	sw	a4,0(a5)
    402c:	007afa93          	andi	s5,s5,7
    4030:	07502623          	sw	s5,108(zero) # 6c <_start-0x37d4>
    4034:	c65ff06f          	j	3c98 <main+0x420>
    4038:	0ff0000f          	fence
    403c:	b09ff06f          	j	3b44 <main+0x2cc>
    4040:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    4044:	c91ff06f          	j	3cd4 <main+0x45c>
    4048:	0ff0000f          	fence
    404c:	01b70663          	beq	a4,s11,4058 <.NO_CB1058+0x174>
    4050:	fff708e3          	beq	a4,t6,4040 <.NO_CB1058+0x15c>
    4054:	c85710e3          	bne	a4,t0,3cd4 <main+0x45c>
    4058:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    405c:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    4060:	00279713          	slli	a4,a5,0x2
    4064:	37072683          	lw	a3,880(a4)
    4068:	00279793          	slli	a5,a5,0x2
    406c:	0106d713          	srli	a4,a3,0x10
    4070:	0086d613          	srli	a2,a3,0x8
    4074:	0ff77713          	zext.b	a4,a4
    4078:	0ff67613          	zext.b	a2,a2
    407c:	00461613          	slli	a2,a2,0x4
    4080:	360789a3          	sb	zero,883(a5)
    4084:	00a71713          	slli	a4,a4,0xa
    4088:	00c76733          	or	a4,a4,a2
    408c:	8561c603          	lbu	a2,-1962(gp) # ffb00046 <noc_index>
    4090:	0ff6f693          	zext.b	a3,a3
    4094:	00c69693          	slli	a3,a3,0xc
    4098:	01061793          	slli	a5,a2,0x10
    409c:	01a686b3          	add	a3,a3,s10
    40a0:	01578533          	add	a0,a5,s5
    40a4:	00052383          	lw	t2,0(a0)
    40a8:	fe039ee3          	bnez	t2,40a4 <.NO_CB1058+0x1c0>
    40ac:	ffb223b7          	lui	t2,0xffb22
    40b0:	21664633          	sh2add	a2,a2,s6
    40b4:	82838393          	addi	t2,t2,-2008 # ffb21828 <__stack_top+0x1f828>
    40b8:	007783b3          	add	t2,a5,t2
    40bc:	0093a023          	sw	s1,0(t2)
    40c0:	010783b3          	add	t2,a5,a6
    40c4:	00b3a023          	sw	a1,0(t2)
    40c8:	011783b3          	add	t2,a5,a7
    40cc:	00d3a023          	sw	a3,0(t2)
    40d0:	006786b3          	add	a3,a5,t1
    40d4:	0006a023          	sw	zero,0(a3)
    40d8:	00475713          	srli	a4,a4,0x4
    40dc:	01c786b3          	add	a3,a5,t3
    40e0:	00e6a023          	sw	a4,0(a3)
    40e4:	01d787b3          	add	a5,a5,t4
    40e8:	0007a023          	sw	zero,0(a5)
    40ec:	01e52023          	sw	t5,0(a0)
    40f0:	00062783          	lw	a5,0(a2)
    40f4:	00178793          	addi	a5,a5,1
    40f8:	00f62023          	sw	a5,0(a2)
    40fc:	bd9ff06f          	j	3cd4 <main+0x45c>
    4100:	00100793          	li	a5,1
    4104:	00fa0023          	sb	a5,0(s4)
    4108:	c25ff06f          	j	3d2c <main+0x4b4>
    410c:	0ff0000f          	fence
    4110:	c81ff06f          	j	3d90 <main+0x518>
    4114:	14872803          	lw	a6,328(a4)
    4118:	00072223          	sw	zero,4(a4)
    411c:	00685793          	srli	a5,a6,0x6
    4120:	03f7f793          	andi	a5,a5,63
    4124:	03f87813          	andi	a6,a6,63
    4128:	00481813          	slli	a6,a6,0x4
    412c:	00a79793          	slli	a5,a5,0xa
    4130:	0107e7b3          	or	a5,a5,a6
    4134:	0047d793          	srli	a5,a5,0x4
    4138:	00f72423          	sw	a5,8(a4)
    413c:	ffb21837          	lui	a6,0xffb21
    4140:	00082223          	sw	zero,4(a6) # ffb21004 <__stack_top+0x1f004>
    4144:	00f82423          	sw	a5,8(a6)
    4148:	00400893          	li	a7,4
    414c:	81142623          	sw	a7,-2036(s0)
    4150:	80042823          	sw	zero,-2032(s0)
    4154:	00002737          	lui	a4,0x2
    4158:	80f42a23          	sw	a5,-2028(s0)
    415c:	09070713          	addi	a4,a4,144 # 2090 <_start-0x17b0>
    4160:	80e82e23          	sw	a4,-2020(a6)
    4164:	80082823          	sw	zero,-2032(a6)
    4168:	80f82a23          	sw	a5,-2028(a6)
    416c:	ffb30837          	lui	a6,0xffb30
    4170:	14882e03          	lw	t3,328(a6) # ffb30148 <__stack_top+0x2e148>
    4174:	00082223          	sw	zero,4(a6)
    4178:	006e5793          	srli	a5,t3,0x6
    417c:	03f7f793          	andi	a5,a5,63
    4180:	03fe7e13          	andi	t3,t3,63
    4184:	004e1e13          	slli	t3,t3,0x4
    4188:	00a79793          	slli	a5,a5,0xa
    418c:	01c7e7b3          	or	a5,a5,t3
    4190:	0047d793          	srli	a5,a5,0x4
    4194:	00f82423          	sw	a5,8(a6)
    4198:	ffb31837          	lui	a6,0xffb31
    419c:	00082223          	sw	zero,4(a6) # ffb31004 <__stack_top+0x2f004>
    41a0:	00f82423          	sw	a5,8(a6)
    41a4:	ffb32e37          	lui	t3,0xffb32
    41a8:	811e2623          	sw	a7,-2036(t3) # ffb3180c <__stack_top+0x2f80c>
    41ac:	800e2823          	sw	zero,-2032(t3)
    41b0:	80fe2a23          	sw	a5,-2028(t3)
    41b4:	80e82e23          	sw	a4,-2020(a6)
    41b8:	80082823          	sw	zero,-2032(a6)
    41bc:	80f82a23          	sw	a5,-2028(a6)
    41c0:	c35ff06f          	j	3df4 <main+0x57c>
    41c4:	08679863          	bne	a5,t1,4254 <.NO_CB1058+0x370>
    41c8:	ffb20737          	lui	a4,0xffb20
    41cc:	20872d83          	lw	s11,520(a4) # ffb20208 <__stack_top+0x1e208>
    41d0:	ffb307b7          	lui	a5,0xffb30
    41d4:	2087a383          	lw	t2,520(a5) # ffb30208 <__stack_top+0x2e208>
    41d8:	22872283          	lw	t0,552(a4)
    41dc:	2287af83          	lw	t6,552(a5)
    41e0:	20472f03          	lw	t5,516(a4)
    41e4:	2047ae83          	lw	t4,516(a5)
    41e8:	20072e03          	lw	t3,512(a4)
    41ec:	2007a883          	lw	a7,512(a5)
    41f0:	22c72803          	lw	a6,556(a4)
    41f4:	22c7a703          	lw	a4,556(a5)
    41f8:	000077b7          	lui	a5,0x7
    41fc:	05b7a023          	sw	s11,64(a5) # 7040 <__fw_export_text_end+0x2670>
    4200:	0607a423          	sw	zero,104(a5)
    4204:	0407aa23          	sw	zero,84(a5)
    4208:	0677ae23          	sw	t2,124(a5)
    420c:	0457a223          	sw	t0,68(a5)
    4210:	0607a623          	sw	zero,108(a5)
    4214:	0407ac23          	sw	zero,88(a5)
    4218:	09f7a023          	sw	t6,128(a5)
    421c:	05e7a423          	sw	t5,72(a5)
    4220:	0607a823          	sw	zero,112(a5)
    4224:	0407ae23          	sw	zero,92(a5)
    4228:	09d7a223          	sw	t4,132(a5)
    422c:	05c7a623          	sw	t3,76(a5)
    4230:	0607aa23          	sw	zero,116(a5)
    4234:	0607a023          	sw	zero,96(a5)
    4238:	0917a423          	sw	a7,136(a5)
    423c:	0507a823          	sw	a6,80(a5)
    4240:	0607ac23          	sw	zero,120(a5)
    4244:	0607a223          	sw	zero,100(a5)
    4248:	08e7a623          	sw	a4,140(a5)
    424c:	00100713          	li	a4,1
    4250:	c1dff06f          	j	3e6c <main+0x5f4>
    4254:	14872803          	lw	a6,328(a4)
    4258:	00685793          	srli	a5,a6,0x6
    425c:	03f7f793          	andi	a5,a5,63
    4260:	03f87813          	andi	a6,a6,63
    4264:	00481813          	slli	a6,a6,0x4
    4268:	00a79793          	slli	a5,a5,0xa
    426c:	0107e7b3          	or	a5,a5,a6
    4270:	0047d793          	srli	a5,a5,0x4
    4274:	ffb21837          	lui	a6,0xffb21
    4278:	80f82a23          	sw	a5,-2028(a6) # ffb20814 <__stack_top+0x1e814>
    427c:	00f72423          	sw	a5,8(a4)
    4280:	80f42a23          	sw	a5,-2028(s0)
    4284:	00f82423          	sw	a5,8(a6)
    4288:	ffb30837          	lui	a6,0xffb30
    428c:	14882703          	lw	a4,328(a6) # ffb30148 <__stack_top+0x2e148>
    4290:	00675793          	srli	a5,a4,0x6
    4294:	03f7f793          	andi	a5,a5,63
    4298:	03f77713          	andi	a4,a4,63
    429c:	00471713          	slli	a4,a4,0x4
    42a0:	00a79793          	slli	a5,a5,0xa
    42a4:	00e7e7b3          	or	a5,a5,a4
    42a8:	0047d793          	srli	a5,a5,0x4
    42ac:	ffb31737          	lui	a4,0xffb31
    42b0:	80f72a23          	sw	a5,-2028(a4) # ffb30814 <__stack_top+0x2e814>
    42b4:	00f82423          	sw	a5,8(a6)
    42b8:	ffb32837          	lui	a6,0xffb32
    42bc:	80f82a23          	sw	a5,-2028(a6) # ffb31814 <__stack_top+0x2f814>
    42c0:	00f72423          	sw	a5,8(a4)
    42c4:	f05ff06f          	j	41c8 <.NO_CB1058+0x2e4>
    42c8:	04c4a783          	lw	a5,76(s1)
    42cc:	02078a63          	beqz	a5,4300 <.NO_CB1058+0x41c>
    42d0:	0144d503          	lhu	a0,20(s1)
    42d4:	0464cd83          	lbu	s11,70(s1)
    42d8:	00030693          	mv	a3,t1
    42dc:	0ffdfd93          	zext.b	s11,s11
    42e0:	000d8593          	mv	a1,s11
    42e4:	01a50533          	add	a0,a0,s10
    42e8:	00c12623          	sw	a2,12(sp)
    42ec:	03c000ef          	jal	4328 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    42f0:	02000793          	li	a5,32
    42f4:	00fd8663          	beq	s11,a5,4300 <.NO_CB1058+0x41c>
    42f8:	00c12503          	lw	a0,12(sp)
    42fc:	5cc000ef          	jal	48c8 <_Z33barrier_remote_cb_interface_setuphm.part.0>
    4300:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    4304:	08000713          	li	a4,128
    4308:	00279793          	slli	a5,a5,0x2
    430c:	37078793          	addi	a5,a5,880
    4310:	0037c683          	lbu	a3,3(a5)
    4314:	c2e684e3          	beq	a3,a4,3f3c <.NO_CB1058+0x58>
    4318:	0ff0000f          	fence
    431c:	ff5ff06f          	j	4310 <.NO_CB1058+0x42c>
    4320:	0ff0000f          	fence
    4324:	c19ff06f          	j	3f3c <.NO_CB1058+0x58>

00004328 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>:
    4328:	fa010113          	addi	sp,sp,-96
    432c:	fff58793          	addi	a5,a1,-1
    4330:	00f12823          	sw	a5,16(sp)
    4334:	100007b7          	lui	a5,0x10000
    4338:	00f78793          	addi	a5,a5,15 # 1000000f <__fw_export_text_end+0xfffb63f>
    433c:	00f12423          	sw	a5,8(sp)
    4340:	010007b7          	lui	a5,0x1000
    4344:	ffb20337          	lui	t1,0xffb20
    4348:	fff78793          	addi	a5,a5,-1 # ffffff <__fw_export_text_end+0xffb62f>
    434c:	03b12823          	sw	s11,48(sp)
    4350:	00b71813          	slli	a6,a4,0xb
    4354:	01061d93          	slli	s11,a2,0x10
    4358:	01b80833          	add	a6,a6,s11
    435c:	00f12623          	sw	a5,12(sp)
    4360:	00430793          	addi	a5,t1,4 # ffb20004 <__stack_top+0x1e004>
    4364:	04030293          	addi	t0,t1,64
    4368:	00f807b3          	add	a5,a6,a5
    436c:	04812e23          	sw	s0,92(sp)
    4370:	05612223          	sw	s6,68(sp)
    4374:	83418393          	addi	t2,gp,-1996 # ffb00024 <noc_nonposted_atomics_acked>
    4378:	04912c23          	sw	s1,88(sp)
    437c:	207643b3          	sh2add	t2,a2,t2
    4380:	05212a23          	sw	s2,84(sp)
    4384:	05312823          	sw	s3,80(sp)
    4388:	05412623          	sw	s4,76(sp)
    438c:	05512423          	sw	s5,72(sp)
    4390:	05712023          	sw	s7,64(sp)
    4394:	03812e23          	sw	s8,60(sp)
    4398:	03912c23          	sw	s9,56(sp)
    439c:	03a12a23          	sw	s10,52(sp)
    43a0:	00050413          	mv	s0,a0
    43a4:	85818593          	addi	a1,gp,-1960 # ffb00048 <cb_interface>
    43a8:	01f00b13          	li	s6,31
    43ac:	005802b3          	add	t0,a6,t0
    43b0:	02f12623          	sw	a5,44(sp)
    43b4:	01012783          	lw	a5,16(sp)
    43b8:	03679e63          	bne	a5,s6,43f4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0xcc>
    43bc:	05c12403          	lw	s0,92(sp)
    43c0:	05812483          	lw	s1,88(sp)
    43c4:	05412903          	lw	s2,84(sp)
    43c8:	05012983          	lw	s3,80(sp)
    43cc:	04c12a03          	lw	s4,76(sp)
    43d0:	04812a83          	lw	s5,72(sp)
    43d4:	04412b03          	lw	s6,68(sp)
    43d8:	04012b83          	lw	s7,64(sp)
    43dc:	03c12c03          	lw	s8,60(sp)
    43e0:	03812c83          	lw	s9,56(sp)
    43e4:	03412d03          	lw	s10,52(sp)
    43e8:	03012d83          	lw	s11,48(sp)
    43ec:	06010113          	addi	sp,sp,96
    43f0:	00008067          	ret
    43f4:	00042f03          	lw	t5,0(s0)
    43f8:	00442503          	lw	a0,4(s0)
    43fc:	000f2f83          	lw	t6,0(t5)
    4400:	004f2b83          	lw	s7,4(t5)
    4404:	008f2e03          	lw	t3,8(t5)
    4408:	00cf2783          	lw	a5,12(t5)
    440c:	010f2783          	lw	a5,16(t5)
    4410:	014f2903          	lw	s2,20(t5)
    4414:	018f2883          	lw	a7,24(t5)
    4418:	fff50e93          	addi	t4,a0,-1
    441c:	00fe8eb3          	add	t4,t4,a5
    4420:	41ce8eb3          	sub	t4,t4,t3
    4424:	02aedeb3          	divu	t4,t4,a0
    4428:	02ae8eb3          	mul	t4,t4,a0
    442c:	01ce8eb3          	add	t4,t4,t3
    4430:	280f8663          	beqz	t6,46bc <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x394>
    4434:	3fe5a023          	sw	t5,992(a1)
    4438:	3fc5a223          	sw	t3,996(a1)
    443c:	3ef5a823          	sw	a5,1008(a1)
    4440:	3f25aa23          	sw	s2,1012(a1)
    4444:	3f15ac23          	sw	a7,1016(a1)
    4448:	3f75ae23          	sw	s7,1020(a1)
    444c:	00cf2f03          	lw	t5,12(t5)
    4450:	01ee09b3          	add	s3,t3,t5
    4454:	02af7fb3          	remu	t6,t5,a0
    4458:	41f989b3          	sub	s3,s3,t6
    445c:	0f3ee063          	bltu	t4,s3,453c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x214>
    4460:	40ff0f33          	sub	t5,t5,a5
    4464:	01cf0f33          	add	t5,t5,t3
    4468:	004f5793          	srli	a5,t5,0x4
    446c:	16078463          	beqz	a5,45d4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2ac>
    4470:	00100e93          	li	t4,1
    4474:	00000f13          	li	t5,0
    4478:	0dd68c63          	beq	a3,t4,4550 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x228>
    447c:	00830f93          	addi	t6,t1,8
    4480:	01c30493          	addi	s1,t1,28
    4484:	00680ab3          	add	s5,a6,t1
    4488:	01f80fb3          	add	t6,a6,t6
    448c:	009804b3          	add	s1,a6,s1
    4490:	15eb8263          	beq	s7,t5,45d4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2ac>
    4494:	212f6a33          	sh3add	s4,t5,s2
    4498:	004a2e83          	lw	t4,4(s4)
    449c:	000a2c03          	lw	s8,0(s4)
    44a0:	0008aa03          	lw	s4,0(a7)
    44a4:	006e9e93          	slli	t4,t4,0x6
    44a8:	018eeeb3          	or	t4,t4,s8
    44ac:	01478a33          	add	s4,a5,s4
    44b0:	0148a023          	sw	s4,0(a7)
    44b4:	004e9e93          	slli	t4,t4,0x4
    44b8:	0002aa03          	lw	s4,0(t0)
    44bc:	fe0a1ee3          	bnez	s4,44b8 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x190>
    44c0:	00812a03          	lw	s4,8(sp)
    44c4:	02c12c03          	lw	s8,44(sp)
    44c8:	011aa023          	sw	a7,0(s5)
    44cc:	014efa33          	and	s4,t4,s4
    44d0:	014c2023          	sw	s4,0(s8)
    44d4:	00c12a03          	lw	s4,12(sp)
    44d8:	004ede93          	srli	t4,t4,0x4
    44dc:	014efeb3          	and	t4,t4,s4
    44e0:	01dfa023          	sw	t4,0(t6)
    44e4:	00002eb7          	lui	t4,0x2
    44e8:	091e8e93          	addi	t4,t4,145 # 2091 <_start-0x17af>
    44ec:	01d4a023          	sw	t4,0(s1)
    44f0:	00001a37          	lui	s4,0x1
    44f4:	0028de93          	srli	t4,a7,0x2
    44f8:	07ca0a13          	addi	s4,s4,124 # 107c <_start-0x27c4>
    44fc:	003efe93          	andi	t4,t4,3
    4500:	014eeeb3          	or	t4,t4,s4
    4504:	02030a13          	addi	s4,t1,32
    4508:	01480a33          	add	s4,a6,s4
    450c:	01da2023          	sw	t4,0(s4)
    4510:	02830e93          	addi	t4,t1,40
    4514:	01d80eb3          	add	t4,a6,t4
    4518:	00fea023          	sw	a5,0(t4)
    451c:	00100e93          	li	t4,1
    4520:	01d2a023          	sw	t4,0(t0)
    4524:	0003ae83          	lw	t4,0(t2)
    4528:	02088893          	addi	a7,a7,32
    452c:	001e8e93          	addi	t4,t4,1
    4530:	01d3a023          	sw	t4,0(t2)
    4534:	001f0f13          	addi	t5,t5,1
    4538:	f59ff06f          	j	4490 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x168>
    453c:	09d78e63          	beq	a5,t4,45d8 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2b0>
    4540:	40fe87b3          	sub	a5,t4,a5
    4544:	0047d793          	srli	a5,a5,0x4
    4548:	000e8e13          	mv	t3,t4
    454c:	f21ff06f          	j	446c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x144>
    4550:	02800493          	li	s1,40
    4554:	00007eb7          	lui	t4,0x7
    4558:	029604b3          	mul	s1,a2,s1
    455c:	ffb20fb7          	lui	t6,0xffb20
    4560:	04ce8e93          	addi	t4,t4,76 # 704c <__fw_export_text_end+0x267c>
    4564:	044f8c13          	addi	s8,t6,68 # ffb20044 <__stack_top+0x1e044>
    4568:	01d484b3          	add	s1,s1,t4
    456c:	00b71f13          	slli	t5,a4,0xb
    4570:	01061e93          	slli	t4,a2,0x10
    4574:	01df0f33          	add	t5,t5,t4
    4578:	018e8eb3          	add	t4,t4,s8
    457c:	01d12a23          	sw	t4,20(sp)
    4580:	00cf8e93          	addi	t4,t6,12
    4584:	01df0eb3          	add	t4,t5,t4
    4588:	01d12c23          	sw	t4,24(sp)
    458c:	10000eb7          	lui	t4,0x10000
    4590:	00fe8e93          	addi	t4,t4,15 # 1000000f <__fw_export_text_end+0xfffb63f>
    4594:	01d12e23          	sw	t4,28(sp)
    4598:	004f8e93          	addi	t4,t6,4
    459c:	01df0eb3          	add	t4,t5,t4
    45a0:	03d12023          	sw	t4,32(sp)
    45a4:	01000eb7          	lui	t4,0x1000
    45a8:	fffe8e93          	addi	t4,t4,-1 # ffffff <__fw_export_text_end+0xffb62f>
    45ac:	008f8c13          	addi	s8,t6,8
    45b0:	040f8a93          	addi	s5,t6,64
    45b4:	03d12223          	sw	t4,36(sp)
    45b8:	01cf8c93          	addi	s9,t6,28
    45bc:	018f0eb3          	add	t4,t5,s8
    45c0:	00000a13          	li	s4,0
    45c4:	015f0ab3          	add	s5,t5,s5
    45c8:	03d12423          	sw	t4,40(sp)
    45cc:	019f0cb3          	add	s9,t5,s9
    45d0:	034b9263          	bne	s7,s4,45f4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2cc>
    45d4:	000e0e93          	mv	t4,t3
    45d8:	3fd5a823          	sw	t4,1008(a1)
    45dc:	3f35a423          	sw	s3,1000(a1)
    45e0:	3ea5a623          	sw	a0,1004(a1)
    45e4:	00840413          	addi	s0,s0,8
    45e8:	fffb0b13          	addi	s6,s6,-1
    45ec:	fe058593          	addi	a1,a1,-32
    45f0:	dc5ff06f          	j	43b4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x8c>
    45f4:	212a6d33          	sh3add	s10,s4,s2
    45f8:	004d2e83          	lw	t4,4(s10)
    45fc:	000d2d03          	lw	s10,0(s10)
    4600:	006e9e93          	slli	t4,t4,0x6
    4604:	000d0c13          	mv	s8,s10
    4608:	0008ad03          	lw	s10,0(a7)
    460c:	018eeeb3          	or	t4,t4,s8
    4610:	004e9e93          	slli	t4,t4,0x4
    4614:	01a78d33          	add	s10,a5,s10
    4618:	01a8a023          	sw	s10,0(a7)
    461c:	0004ad03          	lw	s10,0(s1)
    4620:	001d0d13          	addi	s10,s10,1
    4624:	01a4a023          	sw	s10,0(s1)
    4628:	000aad03          	lw	s10,0(s5)
    462c:	fe0d1ee3          	bnez	s10,4628 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x300>
    4630:	01412d03          	lw	s10,20(sp)
    4634:	00400c13          	li	s8,4
    4638:	000d2d03          	lw	s10,0(s10)
    463c:	01812d03          	lw	s10,24(sp)
    4640:	018d2023          	sw	s8,0(s10)
    4644:	01c12c03          	lw	s8,28(sp)
    4648:	01ff0d33          	add	s10,t5,t6
    464c:	011d2023          	sw	a7,0(s10)
    4650:	018efd33          	and	s10,t4,s8
    4654:	02012c03          	lw	s8,32(sp)
    4658:	004ede93          	srli	t4,t4,0x4
    465c:	01ac2023          	sw	s10,0(s8)
    4660:	02412c03          	lw	s8,36(sp)
    4664:	00001d37          	lui	s10,0x1
    4668:	018efeb3          	and	t4,t4,s8
    466c:	02812c03          	lw	s8,40(sp)
    4670:	07cd0d13          	addi	s10,s10,124 # 107c <_start-0x27c4>
    4674:	01dc2023          	sw	t4,0(s8)
    4678:	00002eb7          	lui	t4,0x2
    467c:	091e8e93          	addi	t4,t4,145 # 2091 <_start-0x17af>
    4680:	01dca023          	sw	t4,0(s9)
    4684:	0028de93          	srli	t4,a7,0x2
    4688:	003efe93          	andi	t4,t4,3
    468c:	01aeeeb3          	or	t4,t4,s10
    4690:	020f8d13          	addi	s10,t6,32
    4694:	01af0d33          	add	s10,t5,s10
    4698:	01dd2023          	sw	t4,0(s10)
    469c:	028f8e93          	addi	t4,t6,40
    46a0:	01df0eb3          	add	t4,t5,t4
    46a4:	00fea023          	sw	a5,0(t4)
    46a8:	00100e93          	li	t4,1
    46ac:	01daa023          	sw	t4,0(s5)
    46b0:	02088893          	addi	a7,a7,32
    46b4:	01da0a33          	add	s4,s4,t4
    46b8:	f19ff06f          	j	45d0 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2a8>
    46bc:	00092983          	lw	s3,0(s2)
    46c0:	00492f83          	lw	t6,4(s2)
    46c4:	01088493          	addi	s1,a7,16
    46c8:	3fe5a023          	sw	t5,992(a1)
    46cc:	3fc5a223          	sw	t3,996(a1)
    46d0:	3ef5a823          	sw	a5,1008(a1)
    46d4:	3e95ae23          	sw	s1,1020(a1)
    46d8:	3f35aa23          	sw	s3,1012(a1)
    46dc:	3ff5ac23          	sw	t6,1016(a1)
    46e0:	00cf2f03          	lw	t5,12(t5)
    46e4:	01ee0fb3          	add	t6,t3,t5
    46e8:	02af7933          	remu	s2,t5,a0
    46ec:	412f8fb3          	sub	t6,t6,s2
    46f0:	13fee263          	bltu	t4,t6,4814 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4ec>
    46f4:	40ff0f33          	sub	t5,t5,a5
    46f8:	01cf0f33          	add	t5,t5,t3
    46fc:	004f5793          	srli	a5,t5,0x4
    4700:	10078263          	beqz	a5,4804 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4dc>
    4704:	0ff0000f          	fence
    4708:	0004af03          	lw	t5,0(s1)
    470c:	0008ae83          	lw	t4,0(a7)
    4710:	41ee8eb3          	sub	t4,t4,t5
    4714:	fefee8e3          	bltu	t4,a5,4704 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x3dc>
    4718:	3f85ae83          	lw	t4,1016(a1)
    471c:	3f45af03          	lw	t5,1012(a1)
    4720:	00ae9e93          	slli	t4,t4,0xa
    4724:	004f1f13          	slli	t5,t5,0x4
    4728:	01eeeeb3          	or	t4,t4,t5
    472c:	00100f13          	li	t5,1
    4730:	3fc5a883          	lw	a7,1020(a1)
    4734:	0fe69a63          	bne	a3,t5,4828 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x500>
    4738:	0008af03          	lw	t5,0(a7)
    473c:	000074b7          	lui	s1,0x7
    4740:	01e78f33          	add	t5,a5,t5
    4744:	01e8a023          	sw	t5,0(a7)
    4748:	02800f13          	li	t5,40
    474c:	04c48493          	addi	s1,s1,76 # 704c <__fw_export_text_end+0x267c>
    4750:	03e60f33          	mul	t5,a2,t5
    4754:	009f0f33          	add	t5,t5,s1
    4758:	000f2483          	lw	s1,0(t5)
    475c:	00d484b3          	add	s1,s1,a3
    4760:	009f2023          	sw	s1,0(t5)
    4764:	0002af03          	lw	t5,0(t0)
    4768:	fe0f1ee3          	bnez	t5,4764 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x43c>
    476c:	ffb20f37          	lui	t5,0xffb20
    4770:	044f0493          	addi	s1,t5,68 # ffb20044 <__stack_top+0x1e044>
    4774:	009d84b3          	add	s1,s11,s1
    4778:	0004a483          	lw	s1,0(s1)
    477c:	00cf0493          	addi	s1,t5,12
    4780:	009804b3          	add	s1,a6,s1
    4784:	00400913          	li	s2,4
    4788:	0124a023          	sw	s2,0(s1)
    478c:	01e804b3          	add	s1,a6,t5
    4790:	0114a023          	sw	a7,0(s1)
    4794:	10000937          	lui	s2,0x10000
    4798:	004f0493          	addi	s1,t5,4
    479c:	012ef933          	and	s2,t4,s2
    47a0:	009804b3          	add	s1,a6,s1
    47a4:	0124a023          	sw	s2,0(s1)
    47a8:	004e9e93          	slli	t4,t4,0x4
    47ac:	008f0493          	addi	s1,t5,8
    47b0:	008ede93          	srli	t4,t4,0x8
    47b4:	009804b3          	add	s1,a6,s1
    47b8:	01d4a023          	sw	t4,0(s1)
    47bc:	01cf0e93          	addi	t4,t5,28
    47c0:	000024b7          	lui	s1,0x2
    47c4:	01d80eb3          	add	t4,a6,t4
    47c8:	09148493          	addi	s1,s1,145 # 2091 <_start-0x17af>
    47cc:	009ea023          	sw	s1,0(t4)
    47d0:	0028d893          	srli	a7,a7,0x2
    47d4:	00001eb7          	lui	t4,0x1
    47d8:	07ce8e93          	addi	t4,t4,124 # 107c <_start-0x27c4>
    47dc:	0038f893          	andi	a7,a7,3
    47e0:	01d8e8b3          	or	a7,a7,t4
    47e4:	020f0e93          	addi	t4,t5,32
    47e8:	01d80eb3          	add	t4,a6,t4
    47ec:	028f0f13          	addi	t5,t5,40
    47f0:	011ea023          	sw	a7,0(t4)
    47f4:	01e80f33          	add	t5,a6,t5
    47f8:	00ff2023          	sw	a5,0(t5)
    47fc:	00100793          	li	a5,1
    4800:	00f2a023          	sw	a5,0(t0)
    4804:	000e0e93          	mv	t4,t3
    4808:	3fd5a823          	sw	t4,1008(a1)
    480c:	3ff5a423          	sw	t6,1000(a1)
    4810:	dd1ff06f          	j	45e0 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2b8>
    4814:	ffd78ae3          	beq	a5,t4,4808 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4e0>
    4818:	40fe87b3          	sub	a5,t4,a5
    481c:	0047d793          	srli	a5,a5,0x4
    4820:	000e8e13          	mv	t3,t4
    4824:	eddff06f          	j	4700 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x3d8>
    4828:	0008af03          	lw	t5,0(a7)
    482c:	01e78f33          	add	t5,a5,t5
    4830:	01e8a023          	sw	t5,0(a7)
    4834:	0002af03          	lw	t5,0(t0)
    4838:	fe0f1ee3          	bnez	t5,4834 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x50c>
    483c:	00680f33          	add	t5,a6,t1
    4840:	011f2023          	sw	a7,0(t5)
    4844:	00812f03          	lw	t5,8(sp)
    4848:	0028d893          	srli	a7,a7,0x2
    484c:	01eef4b3          	and	s1,t4,t5
    4850:	00430f13          	addi	t5,t1,4
    4854:	01e80f33          	add	t5,a6,t5
    4858:	009f2023          	sw	s1,0(t5)
    485c:	00c12f03          	lw	t5,12(sp)
    4860:	004ede93          	srli	t4,t4,0x4
    4864:	01eefeb3          	and	t4,t4,t5
    4868:	00830f13          	addi	t5,t1,8
    486c:	01e80f33          	add	t5,a6,t5
    4870:	01df2023          	sw	t4,0(t5)
    4874:	01c30e93          	addi	t4,t1,28
    4878:	00002f37          	lui	t5,0x2
    487c:	01d80eb3          	add	t4,a6,t4
    4880:	091f0f13          	addi	t5,t5,145 # 2091 <_start-0x17af>
    4884:	01eea023          	sw	t5,0(t4)
    4888:	00001eb7          	lui	t4,0x1
    488c:	07ce8e93          	addi	t4,t4,124 # 107c <_start-0x27c4>
    4890:	0038f893          	andi	a7,a7,3
    4894:	01d8e8b3          	or	a7,a7,t4
    4898:	02030e93          	addi	t4,t1,32
    489c:	01d80eb3          	add	t4,a6,t4
    48a0:	011ea023          	sw	a7,0(t4)
    48a4:	02830893          	addi	a7,t1,40
    48a8:	011808b3          	add	a7,a6,a7
    48ac:	00f8a023          	sw	a5,0(a7)
    48b0:	00100793          	li	a5,1
    48b4:	00f2a023          	sw	a5,0(t0)
    48b8:	0003a783          	lw	a5,0(t2)
    48bc:	00178793          	addi	a5,a5,1
    48c0:	00f3a023          	sw	a5,0(t2)
    48c4:	f41ff06f          	j	4804 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4dc>

000048c8 <_Z33barrier_remote_cb_interface_setuphm.part.0>:
    48c8:	ffb20737          	lui	a4,0xffb20
    48cc:	01051793          	slli	a5,a0,0x10
    48d0:	20070713          	addi	a4,a4,512 # ffb20200 <__stack_top+0x1e200>
    48d4:	00e787b3          	add	a5,a5,a4
    48d8:	83418713          	addi	a4,gp,-1996 # ffb00024 <noc_nonposted_atomics_acked>
    48dc:	20e54533          	sh2add	a0,a0,a4
    48e0:	00052703          	lw	a4,0(a0)
    48e4:	0007a683          	lw	a3,0(a5)
    48e8:	fee69ee3          	bne	a3,a4,48e4 <_Z33barrier_remote_cb_interface_setuphm.part.0+0x1c>
    48ec:	0ff0000f          	fence
    48f0:	00008067          	ret

000048f4 <_Z15noc_set_cfg_regmm>:
    48f4:	81c1a783          	lw	a5,-2020(gp) # ffb0000c <_ZL19active_noc_instance>
    48f8:	ffec8737          	lui	a4,0xffec8
    48fc:	00e79793          	slli	a5,a5,0xe
    4900:	04070713          	addi	a4,a4,64 # ffec8040 <__instrn_buffer+0x88040>
    4904:	00e787b3          	add	a5,a5,a4
    4908:	00a787b3          	add	a5,a5,a0
    490c:	00279793          	slli	a5,a5,0x2
    4910:	00b7a023          	sw	a1,0(a5)
    4914:	00008067          	ret

00004918 <_Z15noc_get_cfg_regm>:
    4918:	81c1a783          	lw	a5,-2020(gp) # ffb0000c <_ZL19active_noc_instance>
    491c:	ffec8737          	lui	a4,0xffec8
    4920:	04070713          	addi	a4,a4,64 # ffec8040 <__instrn_buffer+0x88040>
    4924:	00e79793          	slli	a5,a5,0xe
    4928:	00e787b3          	add	a5,a5,a4
    492c:	00a787b3          	add	a5,a5,a0
    4930:	00279793          	slli	a5,a5,0x2
    4934:	0007a503          	lw	a0,0(a5)
    4938:	00008067          	ret

0000493c <wzerorange>:
    493c:	01050513          	addi	a0,a0,16
    4940:	02a5f463          	bgeu	a1,a0,4968 <wzerorange+0x2c>
    4944:	ff850793          	addi	a5,a0,-8
    4948:	00f5e863          	bltu	a1,a5,4958 <wzerorange+0x1c>
    494c:	fe052a23          	sw	zero,-12(a0)
    4950:	fe052823          	sw	zero,-16(a0)
    4954:	00050793          	mv	a5,a0
    4958:	ffc78713          	addi	a4,a5,-4
    495c:	00e5e463          	bltu	a1,a4,4964 <wzerorange+0x28>
    4960:	fe07ac23          	sw	zero,-8(a5)
    4964:	00008067          	ret
    4968:	fe052e23          	sw	zero,-4(a0)
    496c:	fe052c23          	sw	zero,-8(a0)
    4970:	fe052a23          	sw	zero,-12(a0)
    4974:	fe052823          	sw	zero,-16(a0)
    4978:	01050513          	addi	a0,a0,16
    497c:	fc5ff06f          	j	4940 <wzerorange+0x4>

00004980 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>:
    4980:	00200793          	li	a5,2
    4984:	02c7c063          	blt	a5,a2,49a4 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x24>
    4988:	00c05c63          	blez	a2,49a0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    498c:	0005a703          	lw	a4,0(a1)
    4990:	00e52023          	sw	a4,0(a0)
    4994:	00f61663          	bne	a2,a5,49a0 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    4998:	0045a783          	lw	a5,4(a1)
    499c:	00f52223          	sw	a5,4(a0)
    49a0:	00008067          	ret
    49a4:	0005a803          	lw	a6,0(a1)
    49a8:	0045a683          	lw	a3,4(a1)
    49ac:	0085a703          	lw	a4,8(a1)
    49b0:	00c58593          	addi	a1,a1,12
    49b4:	00c50513          	addi	a0,a0,12
    49b8:	ffd60613          	addi	a2,a2,-3
    49bc:	ff052a23          	sw	a6,-12(a0)
    49c0:	fed52c23          	sw	a3,-8(a0)
    49c4:	fee52e23          	sw	a4,-4(a0)
    49c8:	fbdff06f          	j	4984 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x4>

000049cc <exit>:
    49cc:	0000006f          	j	49cc <exit>
