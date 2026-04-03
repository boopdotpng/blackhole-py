
/tmp/tt-disasm-skg66i5r/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00003840 <_start>:
    3840:	ffb001b7          	lui	gp,0xffb00
    3844:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    3848:	ffb02137          	lui	sp,0xffb02
    384c:	ff010113          	addi	sp,sp,-16 # ffb01ff0 <__fw_export_ldm_end+0x1750>
    3850:	00810513          	addi	a0,sp,8
    3854:	00a12023          	sw	a0,0(sp)
    3858:	00012223          	sw	zero,4(sp)
    385c:	00912423          	sw	s1,8(sp)
    3860:	00012623          	sw	zero,12(sp)
    3864:	00100513          	li	a0,1
    3868:	00010593          	mv	a1,sp
    386c:	00000613          	li	a2,0
    3870:	008000ef          	jal	3878 <main>
    3874:	0710106f          	j	50e4 <exit>

00003878 <main>:
    3878:	fa010113          	addi	sp,sp,-96
    387c:	04112e23          	sw	ra,92(sp)
    3880:	04812c23          	sw	s0,88(sp)
    3884:	04912a23          	sw	s1,84(sp)
    3888:	05212823          	sw	s2,80(sp)
    388c:	05312623          	sw	s3,76(sp)
    3890:	05412423          	sw	s4,72(sp)
    3894:	05512223          	sw	s5,68(sp)
    3898:	05612023          	sw	s6,64(sp)
    389c:	03712e23          	sw	s7,60(sp)
    38a0:	03812c23          	sw	s8,56(sp)
    38a4:	03912a23          	sw	s9,52(sp)
    38a8:	03a12823          	sw	s10,48(sp)
    38ac:	03b12623          	sw	s11,44(sp)
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
    38e4:	89858593          	addi	a1,a1,-1896 # ffb00898 <__ldm_bss_end>
    38e8:	81418513          	addi	a0,gp,-2028 # ffb00004 <_ZL19active_noc_instance>
    38ec:	768010ef          	jal	5054 <wzerorange>
    38f0:	000085b7          	lui	a1,0x8
    38f4:	81018513          	addi	a0,gp,-2032 # ffb00000 <_ZL16subordinate_sync>
    38f8:	6b058593          	addi	a1,a1,1712 # 86b0 <__fw_export_text_end+0x35c0>
    38fc:	00b50c63          	beq	a0,a1,3914 <main+0x9c>
    3900:	ffb00637          	lui	a2,0xffb00
    3904:	00460613          	addi	a2,a2,4 # ffb00004 <_ZL19active_noc_instance>
    3908:	40a60633          	sub	a2,a2,a0
    390c:	40265613          	srai	a2,a2,0x2
    3910:	788010ef          	jal	5098 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3914:	87818993          	addi	s3,gp,-1928 # ffb00068 <cb_interface>
    3918:	00011437          	lui	s0,0x11
    391c:	6b040593          	addi	a1,s0,1712 # 116b0 <__fw_export_text_end+0xc5c0>
    3920:	00700613          	li	a2,7
    3924:	40098513          	addi	a0,s3,1024
    3928:	770010ef          	jal	5098 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    392c:	ffb01937          	lui	s2,0xffb01
    3930:	6cc40593          	addi	a1,s0,1740
    3934:	07800613          	li	a2,120
    3938:	41c98513          	addi	a0,s3,1052
    393c:	75c010ef          	jal	5098 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3940:	00012437          	lui	s0,0x12
    3944:	8ac40593          	addi	a1,s0,-1876 # 118ac <__fw_export_text_end+0xc7bc>
    3948:	00700613          	li	a2,7
    394c:	5fc98513          	addi	a0,s3,1532
    3950:	748010ef          	jal	5098 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3954:	06890913          	addi	s2,s2,104 # ffb01068 <__fw_export_ldm_end+0x7c8>
    3958:	8c840593          	addi	a1,s0,-1848
    395c:	07800613          	li	a2,120
    3960:	61898513          	addi	a0,s3,1560
    3964:	734010ef          	jal	5098 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3968:	eb040593          	addi	a1,s0,-336
    396c:	00500613          	li	a2,5
    3970:	7f898513          	addi	a0,s3,2040
    3974:	724010ef          	jal	5098 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    3978:	000014b7          	lui	s1,0x1
    397c:	ec440593          	addi	a1,s0,-316
    3980:	00300613          	li	a2,3
    3984:	80c90513          	addi	a0,s2,-2036
    3988:	710010ef          	jal	5098 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>
    398c:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    3990:	84018823          	sb	zero,-1968(gp) # ffb00040 <noc_index>
    3994:	9a04c703          	lbu	a4,-1632(s1) # 9a0 <_start-0x2ea0>
    3998:	ffe40a37          	lui	s4,0xffe40
    399c:	ffb12ab7          	lui	s5,0xffb12
    39a0:	00000513          	li	a0,0
    39a4:	00100413          	li	s0,1
    39a8:	84e182a3          	sb	a4,-1979(gp) # ffb00035 <my_logical_x_>
    39ac:	9a14c783          	lbu	a5,-1631(s1)
    39b0:	84f18223          	sb	a5,-1980(gp) # ffb00034 <my_logical_y_>
    39b4:	ffb207b7          	lui	a5,0xffb20
    39b8:	1487a703          	lw	a4,328(a5) # ffb20148 <__stack_top+0x1e148>
    39bc:	03f77793          	andi	a5,a4,63
    39c0:	00675713          	srli	a4,a4,0x6
    39c4:	03f77713          	andi	a4,a4,63
    39c8:	84f18e23          	sb	a5,-1956(gp) # ffb0004c <my_x>
    39cc:	84e18c23          	sb	a4,-1960(gp) # ffb00048 <my_y>
    39d0:	ffb307b7          	lui	a5,0xffb30
    39d4:	1487a703          	lw	a4,328(a5) # ffb30148 <__stack_top+0x2e148>
    39d8:	85c18613          	addi	a2,gp,-1956 # ffb0004c <my_x>
    39dc:	03f77793          	andi	a5,a4,63
    39e0:	00f600a3          	sb	a5,1(a2)
    39e4:	000a0793          	mv	a5,s4
    39e8:	80f92c23          	sw	a5,-2024(s2)
    39ec:	ffe507b7          	lui	a5,0xffe50
    39f0:	00078793          	mv	a5,a5
    39f4:	80f92e23          	sw	a5,-2020(s2)
    39f8:	00675713          	srli	a4,a4,0x6
    39fc:	ffe607b7          	lui	a5,0xffe60
    3a00:	85818693          	addi	a3,gp,-1960 # ffb00048 <my_y>
    3a04:	03f77713          	andi	a4,a4,63
    3a08:	00078793          	mv	a5,a5
    3a0c:	00e680a3          	sb	a4,1(a3)
    3a10:	82f92023          	sw	a5,-2016(s2)
    3a14:	03f00713          	li	a4,63
    3a18:	ffb117b7          	lui	a5,0xffb11
    3a1c:	240aa023          	sw	zero,576(s5) # ffb12240 <__stack_top+0x10240>
    3a20:	02e7a223          	sw	a4,36(a5) # ffb11024 <__stack_top+0xf024>
    3a24:	8001aa23          	sw	zero,-2028(gp) # ffb00004 <_ZL19active_noc_instance>
    3a28:	608010ef          	jal	5030 <_Z15noc_get_cfg_regm>
    3a2c:	00156593          	ori	a1,a0,1
    3a30:	00000513          	li	a0,0
    3a34:	5d8010ef          	jal	500c <_Z15noc_set_cfg_regmm>
    3a38:	00100513          	li	a0,1
    3a3c:	5f4010ef          	jal	5030 <_Z15noc_get_cfg_regm>
    3a40:	00156593          	ori	a1,a0,1
    3a44:	00100513          	li	a0,1
    3a48:	5c4010ef          	jal	500c <_Z15noc_set_cfg_regmm>
    3a4c:	8081aa23          	sw	s0,-2028(gp) # ffb00004 <_ZL19active_noc_instance>
    3a50:	00000513          	li	a0,0
    3a54:	5dc010ef          	jal	5030 <_Z15noc_get_cfg_regm>
    3a58:	008565b3          	or	a1,a0,s0
    3a5c:	00000513          	li	a0,0
    3a60:	5ac010ef          	jal	500c <_Z15noc_set_cfg_regmm>
    3a64:	00040513          	mv	a0,s0
    3a68:	5c8010ef          	jal	5030 <_Z15noc_get_cfg_regm>
    3a6c:	008565b3          	or	a1,a0,s0
    3a70:	00040513          	mv	a0,s0
    3a74:	598010ef          	jal	500c <_Z15noc_set_cfg_regmm>
    3a78:	8001aa23          	sw	zero,-2028(gp) # ffb00004 <_ZL19active_noc_instance>
    3a7c:	00700793          	li	a5,7
    3a80:	22faaa23          	sw	a5,564(s5)
    3a84:	00003537          	lui	a0,0x3
    3a88:	44050593          	addi	a1,a0,1088 # 3440 <_start-0x400>
    3a8c:	228aae23          	sw	s0,572(s5)
    3a90:	24050513          	addi	a0,a0,576
    3a94:	5c0010ef          	jal	5054 <wzerorange>
    3a98:	ffef0737          	lui	a4,0xffef0
    3a9c:	01f00793          	li	a5,31
    3aa0:	2ef72223          	sw	a5,740(a4) # ffef02e4 <__instrn_buffer+0xb02e4>
    3aa4:	101807b7          	lui	a5,0x10180
    3aa8:	00fa2023          	sw	a5,0(s4) # ffe40000 <__instrn_buffer>
    3aac:	8a0037b7          	lui	a5,0x8a003
    3ab0:	00a78793          	addi	a5,a5,10 # 8a00300a <__fw_export_text_end+0x89ffdf1a>
    3ab4:	00fa2023          	sw	a5,0(s4)
    3ab8:	020007b7          	lui	a5,0x2000
    3abc:	00fa2023          	sw	a5,0(s4)
    3ac0:	7100c7b7          	lui	a5,0x7100c
    3ac4:	f8078793          	addi	a5,a5,-128 # 7100bf80 <__fw_export_text_end+0x71006e90>
    3ac8:	00fa2023          	sw	a5,0(s4)
    3acc:	910007b7          	lui	a5,0x91000
    3ad0:	0b078793          	addi	a5,a5,176 # 910000b0 <__fw_export_text_end+0x90ffafc0>
    3ad4:	00fa2023          	sw	a5,0(s4)
    3ad8:	00c72783          	lw	a5,12(a4)
    3adc:	000046b7          	lui	a3,0x4
    3ae0:	0087e7b3          	or	a5,a5,s0
    3ae4:	00f72623          	sw	a5,12(a4)
    3ae8:	00c72783          	lw	a5,12(a4)
    3aec:	ff868693          	addi	a3,a3,-8 # 3ff8 <.NO_CB1545+0xb0>
    3af0:	0027e793          	ori	a5,a5,2
    3af4:	00f72623          	sw	a5,12(a4)
    3af8:	00c72603          	lw	a2,12(a4)
    3afc:	80048793          	addi	a5,s1,-2048
    3b00:	00f647b3          	xor	a5,a2,a5
    3b04:	00d7f7b3          	and	a5,a5,a3
    3b08:	00c7c7b3          	xor	a5,a5,a2
    3b0c:	00f72623          	sw	a5,12(a4)
    3b10:	a31007b7          	lui	a5,0xa3100
    3b14:	00878713          	addi	a4,a5,8 # a3100008 <__fw_export_text_end+0xa30faf18>
    3b18:	00ea2023          	sw	a4,0(s4)
    3b1c:	01078713          	addi	a4,a5,16
    3b20:	00ea2023          	sw	a4,0(s4)
    3b24:	20078793          	addi	a5,a5,512
    3b28:	00fa2023          	sw	a5,0(s4)
    3b2c:	8101a603          	lw	a2,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    3b30:	404047b7          	lui	a5,0x40404
    3b34:	06002023          	sw	zero,96(zero) # 60 <_start-0x37e0>
    3b38:	04078793          	addi	a5,a5,64 # 40404040 <__fw_export_text_end+0x403fef50>
    3b3c:	00f62023          	sw	a5,0(a2)
    3b40:	1a0aa823          	sw	zero,432(s5)
    3b44:	00062783          	lw	a5,0(a2)
    3b48:	60079663          	bnez	a5,4154 <.NO_CB1545+0x20c>
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
    3b88:	ffb224b7          	lui	s1,0xffb22
    3b8c:	00400893          	li	a7,4
    3b90:	8114a623          	sw	a7,-2036(s1) # ffb2180c <__stack_top+0x1f80c>
    3b94:	8004a823          	sw	zero,-2032(s1)
    3b98:	00002537          	lui	a0,0x2
    3b9c:	80f4aa23          	sw	a5,-2028(s1)
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
    3c04:	8501c783          	lbu	a5,-1968(gp) # ffb00040 <noc_index>
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
    3c48:	83c18593          	addi	a1,gp,-1988 # ffb0002c <noc_reads_num_issued>
    3c4c:	00b12623          	sw	a1,12(sp)
    3c50:	20b7c5b3          	sh2add	a1,a5,a1
    3c54:	0065a023          	sw	t1,0(a1)
    3c58:	83418593          	addi	a1,gp,-1996 # ffb00024 <noc_nonposted_writes_num_issued>
    3c5c:	00b12823          	sw	a1,16(sp)
    3c60:	20b7c5b3          	sh2add	a1,a5,a1
    3c64:	0115a023          	sw	a7,0(a1)
    3c68:	82c18593          	addi	a1,gp,-2004 # ffb0001c <noc_nonposted_writes_acked>
    3c6c:	00b12a23          	sw	a1,20(sp)
    3c70:	20b7c5b3          	sh2add	a1,a5,a1
    3c74:	82418b93          	addi	s7,gp,-2012 # ffb00014 <noc_nonposted_atomics_acked>
    3c78:	84818a13          	addi	s4,gp,-1976 # ffb00038 <noc_posted_writes_num_issued>
    3c7c:	0105a023          	sw	a6,0(a1)
    3c80:	2177c5b3          	sh2add	a1,a5,s7
    3c84:	2147c7b3          	sh2add	a5,a5,s4
    3c88:	00a5a023          	sw	a0,0(a1)
    3c8c:	00e7a023          	sw	a4,0(a5)
    3c90:	00300793          	li	a5,3
    3c94:	00f600a3          	sb	a5,1(a2)
    3c98:	8101aa83          	lw	s5,-2032(gp) # ffb00000 <_ZL16subordinate_sync>
    3c9c:	8401aa23          	sw	zero,-1964(gp) # ffb00044 <_ZN15kernel_profiler10traceCountE>
    3ca0:	ffb707b7          	lui	a5,0xffb70
    3ca4:	000025b7          	lui	a1,0x2
    3ca8:	0c000d93          	li	s11,192
    3cac:	43878c93          	addi	s9,a5,1080 # ffb70438 <__stack_top+0x6e438>
    3cb0:	84048c13          	addi	s8,s1,-1984
    3cb4:	04000413          	li	s0,64
    3cb8:	81c48393          	addi	t2,s1,-2020
    3cbc:	08a58593          	addi	a1,a1,138 # 208a <_start-0x17b6>
    3cc0:	80048813          	addi	a6,s1,-2048
    3cc4:	80448893          	addi	a7,s1,-2044
    3cc8:	80848313          	addi	t1,s1,-2040
    3ccc:	82048e13          	addi	t3,s1,-2016
    3cd0:	00100e93          	li	t4,1
    3cd4:	0e000f13          	li	t5,224
    3cd8:	0f000f93          	li	t6,240
    3cdc:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    3ce0:	08000693          	li	a3,128
    3ce4:	00279793          	slli	a5,a5,0x2
    3ce8:	37078793          	addi	a5,a5,880
    3cec:	0037c783          	lbu	a5,3(a5)
    3cf0:	0ff7f713          	zext.b	a4,a5
    3cf4:	02d78263          	beq	a5,a3,3d18 <main+0x4a0>
    3cf8:	06c02783          	lw	a5,108(zero) # 6c <_start-0x37d4>
    3cfc:	06000693          	li	a3,96
    3d00:	00178793          	addi	a5,a5,1
    3d04:	02d787b3          	mul	a5,a5,a3
    3d08:	00d787b3          	add	a5,a5,a3
    3d0c:	00f7c783          	lbu	a5,15(a5)
    3d10:	60479793          	sext.b	a5,a5
    3d14:	4607d663          	bgez	a5,4180 <.NO_CB1545+0x238>
    3d18:	7c0000ef          	jal	44d8 <_ZN15kernel_profiler13init_profilerEttt.constprop.0>
    3d1c:	06000413          	li	s0,96
    3d20:	ffb12637          	lui	a2,0xffb12
    3d24:	1f462703          	lw	a4,500(a2) # ffb121f4 <__stack_top+0x101f4>
    3d28:	000017b7          	lui	a5,0x1
    3d2c:	fff78693          	addi	a3,a5,-1 # fff <_start-0x2841>
    3d30:	00d77733          	and	a4,a4,a3
    3d34:	8e5336b7          	lui	a3,0x8e533
    3d38:	00d76733          	or	a4,a4,a3
    3d3c:	a4e7a823          	sw	a4,-1456(a5)
    3d40:	1f062703          	lw	a4,496(a2)
    3d44:	a4e7aa23          	sw	a4,-1452(a5)
    3d48:	06c02c03          	lw	s8,108(zero) # 6c <_start-0x37d4>
    3d4c:	028c0433          	mul	s0,s8,s0
    3d50:	0bc42703          	lw	a4,188(s0)
    3d54:	07040413          	addi	s0,s0,112
    3d58:	00173713          	seqz	a4,a4
    3d5c:	a0e7a623          	sw	a4,-1524(a5)
    3d60:	04842703          	lw	a4,72(s0)
    3d64:	a4e7a623          	sw	a4,-1460(a5)
    3d68:	24e7a623          	sw	a4,588(a5)
    3d6c:	000027b7          	lui	a5,0x2
    3d70:	a4e7a623          	sw	a4,-1460(a5) # 1a4c <_start-0x1df4>
    3d74:	24e7a623          	sw	a4,588(a5)
    3d78:	000037b7          	lui	a5,0x3
    3d7c:	a4e7a623          	sw	a4,-1460(a5) # 2a4c <_start-0xdf4>
    3d80:	04c42683          	lw	a3,76(s0)
    3d84:	0026f593          	andi	a1,a3,2
    3d88:	4a059463          	bnez	a1,4230 <.NO_CB1545+0x2e8>
    3d8c:	06c02783          	lw	a5,108(zero) # 6c <_start-0x37d4>
    3d90:	06000713          	li	a4,96
    3d94:	02e787b3          	mul	a5,a5,a4
    3d98:	00e787b3          	add	a5,a5,a4
    3d9c:	0107ad83          	lw	s11,16(a5)
    3da0:	01c7d703          	lhu	a4,28(a5)
    3da4:	0147a603          	lw	a2,20(a5)
    3da8:	01b70733          	add	a4,a4,s11
    3dac:	82e92223          	sw	a4,-2012(s2)
    3db0:	01e7d703          	lhu	a4,30(a5)
    3db4:	00c70733          	add	a4,a4,a2
    3db8:	82e92423          	sw	a4,-2008(s2)
    3dbc:	0187a603          	lw	a2,24(a5)
    3dc0:	0207d703          	lhu	a4,32(a5)
    3dc4:	00c70733          	add	a4,a4,a2
    3dc8:	82e92623          	sw	a4,-2004(s2)
    3dcc:	0267d703          	lhu	a4,38(a5)
    3dd0:	0287d783          	lhu	a5,40(a5)
    3dd4:	01b70733          	add	a4,a4,s11
    3dd8:	82e1a023          	sw	a4,-2016(gp) # ffb00010 <rta_l1_base>
    3ddc:	01b787b3          	add	a5,a5,s11
    3de0:	80f1ae23          	sw	a5,-2020(gp) # ffb0000c <crta_l1_base>
    3de4:	ffef07b7          	lui	a5,0xffef0
    3de8:	01f00713          	li	a4,31
    3dec:	2ee7a223          	sw	a4,740(a5) # ffef02e4 <__instrn_buffer+0xb02e4>
    3df0:	001ac783          	lbu	a5,1(s5)
    3df4:	44079463          	bnez	a5,423c <.NO_CB1545+0x2f4>
    3df8:	0046f793          	andi	a5,a3,4
    3dfc:	00078a63          	beqz	a5,3e10 <main+0x598>
    3e00:	f8000793          	li	a5,-128
    3e04:	00fa80a3          	sb	a5,1(s5)
    3e08:	00fa8123          	sb	a5,2(s5)
    3e0c:	00fa81a3          	sb	a5,3(s5)
    3e10:	04444603          	lbu	a2,68(s0)
    3e14:	8451c783          	lbu	a5,-1979(gp) # ffb00035 <my_logical_x_>
    3e18:	04544803          	lbu	a6,69(s0)
    3e1c:	05c44703          	lbu	a4,92(s0)
    3e20:	0ff67613          	zext.b	a2,a2
    3e24:	40e787b3          	sub	a5,a5,a4
    3e28:	80f18d23          	sb	a5,-2022(gp) # ffb0000a <my_relative_x_>
    3e2c:	05d44703          	lbu	a4,93(s0)
    3e30:	8441c783          	lbu	a5,-1980(gp) # ffb00034 <my_logical_y_>
    3e34:	40e787b3          	sub	a5,a5,a4
    3e38:	80f18ca3          	sb	a5,-2023(gp) # ffb00009 <my_relative_y_>
    3e3c:	84c18823          	sb	a2,-1968(gp) # ffb00040 <noc_index>
    3e40:	8181c783          	lbu	a5,-2024(gp) # ffb00008 <prev_noc_mode>
    3e44:	0ff87c93          	zext.b	s9,a6
    3e48:	ffb20737          	lui	a4,0xffb20
    3e4c:	4a081463          	bnez	a6,42f4 <.NO_CB1545+0x3ac>
    3e50:	3e079a63          	bnez	a5,4244 <.NO_CB1545+0x2fc>
    3e54:	ffb20737          	lui	a4,0xffb20
    3e58:	01061793          	slli	a5,a2,0x10
    3e5c:	20870813          	addi	a6,a4,520 # ffb20208 <__stack_top+0x1e208>
    3e60:	01078833          	add	a6,a5,a6
    3e64:	00082e03          	lw	t3,0(a6)
    3e68:	22870813          	addi	a6,a4,552
    3e6c:	01078833          	add	a6,a5,a6
    3e70:	00082303          	lw	t1,0(a6)
    3e74:	20470813          	addi	a6,a4,516
    3e78:	01078833          	add	a6,a5,a6
    3e7c:	00082883          	lw	a7,0(a6)
    3e80:	20070813          	addi	a6,a4,512
    3e84:	22c70713          	addi	a4,a4,556
    3e88:	01078833          	add	a6,a5,a6
    3e8c:	00e787b3          	add	a5,a5,a4
    3e90:	00082803          	lw	a6,0(a6)
    3e94:	0007a703          	lw	a4,0(a5)
    3e98:	00c12783          	lw	a5,12(sp)
    3e9c:	20f647b3          	sh2add	a5,a2,a5
    3ea0:	01c7a023          	sw	t3,0(a5)
    3ea4:	01012783          	lw	a5,16(sp)
    3ea8:	20f647b3          	sh2add	a5,a2,a5
    3eac:	0067a023          	sw	t1,0(a5)
    3eb0:	01412783          	lw	a5,20(sp)
    3eb4:	20f647b3          	sh2add	a5,a2,a5
    3eb8:	0117a023          	sw	a7,0(a5)
    3ebc:	217647b3          	sh2add	a5,a2,s7
    3ec0:	0107a023          	sw	a6,0(a5)
    3ec4:	214647b3          	sh2add	a5,a2,s4
    3ec8:	00e7a023          	sw	a4,0(a5)
    3ecc:	00300713          	li	a4,3
    3ed0:	01245783          	lhu	a5,18(s0)
    3ed4:	81918c23          	sb	s9,-2024(gp) # ffb00008 <prev_noc_mode>
    3ed8:	0807c7b3          	zext.h	a5,a5
    3edc:	00058663          	beqz	a1,3ee8 <main+0x670>
    3ee0:	f8000593          	li	a1,-128
    3ee4:	00ba8023          	sb	a1,0(s5)
    3ee8:	0016f693          	andi	a3,a3,1
    3eec:	50068663          	beqz	a3,43f8 <.NO_CB1545+0x4b0>
    3ef0:	04042583          	lw	a1,64(s0)
    3ef4:	01b787b3          	add	a5,a5,s11
    3ef8:	00098513          	mv	a0,s3
    3efc:	0580006f          	j	3f54 <.NO_CB1545+0xc>
    3f00:	0047a683          	lw	a3,4(a5)
    3f04:	0007a603          	lw	a2,0(a5)
    3f08:	0087a803          	lw	a6,8(a5)
    3f0c:	00c7a883          	lw	a7,12(a5)
    3f10:	0015d593          	srli	a1,a1,0x1
    3f14:	0015f293          	andi	t0,a1,1
    3f18:	00052c23          	sw	zero,24(a0)
    3f1c:	01078793          	addi	a5,a5,16
    3f20:	00d52023          	sw	a3,0(a0)
    3f24:	00d606b3          	add	a3,a2,a3
    3f28:	00d52223          	sw	a3,4(a0)
    3f2c:	00c52a23          	sw	a2,20(a0)
    3f30:	01052623          	sw	a6,12(a0)
    3f34:	00c52823          	sw	a2,16(a0)
    3f38:	01152423          	sw	a7,8(a0)
    3f3c:	02050513          	addi	a0,a0,32
    3f40:	fc0290e3          	bnez	t0,3f00 <main+0x688>
    3f44:	00058e63          	beqz	a1,3f60 <.NO_CB1545+0x18>

00003f48 <.NO_CB1545>:
    3f48:	01078793          	addi	a5,a5,16
    3f4c:	02050513          	addi	a0,a0,32
    3f50:	0015d593          	srli	a1,a1,0x1
    3f54:	0015f293          	andi	t0,a1,1
    3f58:	fa0294e3          	bnez	t0,3f00 <main+0x688>
    3f5c:	fe0596e3          	bnez	a1,3f48 <.NO_CB1545>
    3f60:	01445503          	lhu	a0,20(s0)
    3f64:	04644583          	lbu	a1,70(s0)
    3f68:	8501c603          	lbu	a2,-1968(gp) # ffb00040 <noc_index>
    3f6c:	0ff5f593          	zext.b	a1,a1
    3f70:	000c8693          	mv	a3,s9
    3f74:	01b50533          	add	a0,a0,s11
    3f78:	00b12c23          	sw	a1,24(sp)
    3f7c:	00c12e23          	sw	a2,28(sp)
    3f80:	2c1000ef          	jal	4a40 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    3f84:	01812583          	lw	a1,24(sp)
    3f88:	02000793          	li	a5,32
    3f8c:	00f58663          	beq	a1,a5,3f98 <.NO_CB1545+0x50>
    3f90:	01c12503          	lw	a0,28(sp)
    3f94:	04c010ef          	jal	4fe0 <_Z33barrier_remote_cb_interface_setuphm.part.0>
    3f98:	02c42783          	lw	a5,44(s0)
    3f9c:	01b787b3          	add	a5,a5,s11
    3fa0:	000780e7          	jalr	a5
    3fa4:	000aa783          	lw	a5,0(s5)
    3fa8:	52079463          	bnez	a5,44d0 <.NO_CB1545+0x588>
    3fac:	00300793          	li	a5,3
    3fb0:	00fa80a3          	sb	a5,1(s5)
    3fb4:	00100793          	li	a5,1
    3fb8:	08fc9063          	bne	s9,a5,4038 <.NO_CB1545+0xf0>
    3fbc:	8501c783          	lbu	a5,-1968(gp) # ffb00040 <noc_index>
    3fc0:	ffb206b7          	lui	a3,0xffb20
    3fc4:	01079713          	slli	a4,a5,0x10
    3fc8:	20868613          	addi	a2,a3,520 # ffb20208 <__stack_top+0x1e208>
    3fcc:	00c70633          	add	a2,a4,a2
    3fd0:	00062583          	lw	a1,0(a2)
    3fd4:	22868613          	addi	a2,a3,552
    3fd8:	00c70633          	add	a2,a4,a2
    3fdc:	00062503          	lw	a0,0(a2)
    3fe0:	20468613          	addi	a2,a3,516
    3fe4:	00c70633          	add	a2,a4,a2
    3fe8:	00062803          	lw	a6,0(a2)
    3fec:	20068613          	addi	a2,a3,512
    3ff0:	22c68693          	addi	a3,a3,556
    3ff4:	00c70633          	add	a2,a4,a2
    3ff8:	00d70733          	add	a4,a4,a3
    3ffc:	00c12683          	lw	a3,12(sp)
    4000:	00062603          	lw	a2,0(a2)
    4004:	20d7c6b3          	sh2add	a3,a5,a3
    4008:	00072703          	lw	a4,0(a4)
    400c:	00b6a023          	sw	a1,0(a3)
    4010:	01012683          	lw	a3,16(sp)
    4014:	20d7c6b3          	sh2add	a3,a5,a3
    4018:	00a6a023          	sw	a0,0(a3)
    401c:	01412683          	lw	a3,20(sp)
    4020:	20d7c6b3          	sh2add	a3,a5,a3
    4024:	0106a023          	sw	a6,0(a3)
    4028:	2177c6b3          	sh2add	a3,a5,s7
    402c:	2147c7b3          	sh2add	a5,a5,s4
    4030:	00c6a023          	sw	a2,0(a3)
    4034:	00e7a023          	sw	a4,0(a5)
    4038:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    403c:	00279793          	slli	a5,a5,0x2
    4040:	360789a3          	sb	zero,883(a5)
    4044:	02a44703          	lbu	a4,42(s0)
    4048:	06078793          	addi	a5,a5,96
    404c:	0c071c63          	bnez	a4,4124 <.NO_CB1545+0x1dc>
    4050:	04042623          	sw	zero,76(s0)
    4054:	04040fa3          	sb	zero,95(s0)
    4058:	3107a783          	lw	a5,784(a5)
    405c:	8501c603          	lbu	a2,-1968(gp) # ffb00040 <noc_index>
    4060:	84048593          	addi	a1,s1,-1984
    4064:	0107d693          	srli	a3,a5,0x10
    4068:	0087d713          	srli	a4,a5,0x8
    406c:	0ff6f693          	zext.b	a3,a3
    4070:	0ff77713          	zext.b	a4,a4
    4074:	00471713          	slli	a4,a4,0x4
    4078:	00a69693          	slli	a3,a3,0xa
    407c:	00e6e6b3          	or	a3,a3,a4
    4080:	0ff7f793          	zext.b	a5,a5
    4084:	ffb70737          	lui	a4,0xffb70
    4088:	00c79793          	slli	a5,a5,0xc
    408c:	43870713          	addi	a4,a4,1080 # ffb70438 <__stack_top+0x6e438>
    4090:	00e78833          	add	a6,a5,a4
    4094:	01061793          	slli	a5,a2,0x10
    4098:	00b785b3          	add	a1,a5,a1
    409c:	0005a703          	lw	a4,0(a1)
    40a0:	fe071ee3          	bnez	a4,409c <.NO_CB1545+0x154>
    40a4:	ffb22737          	lui	a4,0xffb22
    40a8:	82870713          	addi	a4,a4,-2008 # ffb21828 <__stack_top+0x1f828>
    40ac:	00e78733          	add	a4,a5,a4
    40b0:	04000513          	li	a0,64
    40b4:	00a72023          	sw	a0,0(a4)
    40b8:	81c48713          	addi	a4,s1,-2020
    40bc:	00002537          	lui	a0,0x2
    40c0:	00e78733          	add	a4,a5,a4
    40c4:	08a50513          	addi	a0,a0,138 # 208a <_start-0x17b6>
    40c8:	00a72023          	sw	a0,0(a4)
    40cc:	80048713          	addi	a4,s1,-2048
    40d0:	00e78733          	add	a4,a5,a4
    40d4:	01072023          	sw	a6,0(a4)
    40d8:	80448713          	addi	a4,s1,-2044
    40dc:	00e78733          	add	a4,a5,a4
    40e0:	00072023          	sw	zero,0(a4)
    40e4:	80848713          	addi	a4,s1,-2040
    40e8:	00e78733          	add	a4,a5,a4
    40ec:	0046d693          	srli	a3,a3,0x4
    40f0:	00d72023          	sw	a3,0(a4)
    40f4:	82048713          	addi	a4,s1,-2016
    40f8:	00e787b3          	add	a5,a5,a4
    40fc:	0007a023          	sw	zero,0(a5)
    4100:	00100793          	li	a5,1
    4104:	00f5a023          	sw	a5,0(a1)
    4108:	214647b3          	sh2add	a5,a2,s4
    410c:	0007a703          	lw	a4,0(a5)
    4110:	001c0c13          	addi	s8,s8,1
    4114:	00170713          	addi	a4,a4,1
    4118:	00e7a023          	sw	a4,0(a5)
    411c:	007c7c13          	andi	s8,s8,7
    4120:	07802623          	sw	s8,108(zero) # 6c <_start-0x37d4>
    4124:	ffb126b7          	lui	a3,0xffb12
    4128:	1f46a703          	lw	a4,500(a3) # ffb121f4 <__stack_top+0x101f4>
    412c:	000017b7          	lui	a5,0x1
    4130:	fff78613          	addi	a2,a5,-1 # fff <_start-0x2841>
    4134:	00c77733          	and	a4,a4,a2
    4138:	9e533637          	lui	a2,0x9e533
    413c:	00c76733          	or	a4,a4,a2
    4140:	a4e7ac23          	sw	a4,-1448(a5)
    4144:	1f06a703          	lw	a4,496(a3)
    4148:	a4e7ae23          	sw	a4,-1444(a5)
    414c:	468000ef          	jal	45b4 <_ZN15kernel_profiler15finish_profilerEv>
    4150:	b51ff06f          	j	3ca0 <main+0x428>
    4154:	0ff0000f          	fence
    4158:	9edff06f          	j	3b44 <main+0x2cc>
    415c:	01e70e63          	beq	a4,t5,4178 <.NO_CB1545+0x230>
    4160:	b7f71ee3          	bne	a4,t6,3cdc <main+0x464>
    4164:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    4168:	8541a783          	lw	a5,-1964(gp) # ffb00044 <_ZN15kernel_profiler10traceCountE>
    416c:	00178793          	addi	a5,a5,1
    4170:	84f1aa23          	sw	a5,-1964(gp) # ffb00044 <_ZN15kernel_profiler10traceCountE>
    4174:	0180006f          	j	418c <.NO_CB1545+0x244>
    4178:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    417c:	b61ff06f          	j	3cdc <main+0x464>
    4180:	0ff0000f          	fence
    4184:	fdb71ce3          	bne	a4,s11,415c <.NO_CB1545+0x214>
    4188:	06002623          	sw	zero,108(zero) # 6c <_start-0x37d4>
    418c:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    4190:	00279713          	slli	a4,a5,0x2
    4194:	37072683          	lw	a3,880(a4)
    4198:	00279793          	slli	a5,a5,0x2
    419c:	0106d713          	srli	a4,a3,0x10
    41a0:	0086d613          	srli	a2,a3,0x8
    41a4:	0ff77713          	zext.b	a4,a4
    41a8:	0ff67613          	zext.b	a2,a2
    41ac:	00461613          	slli	a2,a2,0x4
    41b0:	360789a3          	sb	zero,883(a5)
    41b4:	00a71713          	slli	a4,a4,0xa
    41b8:	00c76733          	or	a4,a4,a2
    41bc:	8501c603          	lbu	a2,-1968(gp) # ffb00040 <noc_index>
    41c0:	0ff6f693          	zext.b	a3,a3
    41c4:	00c69693          	slli	a3,a3,0xc
    41c8:	01061793          	slli	a5,a2,0x10
    41cc:	019686b3          	add	a3,a3,s9
    41d0:	01878533          	add	a0,a5,s8
    41d4:	00052283          	lw	t0,0(a0)
    41d8:	fe029ee3          	bnez	t0,41d4 <.NO_CB1545+0x28c>
    41dc:	ffb222b7          	lui	t0,0xffb22
    41e0:	21464633          	sh2add	a2,a2,s4
    41e4:	82828293          	addi	t0,t0,-2008 # ffb21828 <__stack_top+0x1f828>
    41e8:	005782b3          	add	t0,a5,t0
    41ec:	0082a023          	sw	s0,0(t0)
    41f0:	007782b3          	add	t0,a5,t2
    41f4:	00b2a023          	sw	a1,0(t0)
    41f8:	010782b3          	add	t0,a5,a6
    41fc:	00d2a023          	sw	a3,0(t0)
    4200:	011786b3          	add	a3,a5,a7
    4204:	0006a023          	sw	zero,0(a3)
    4208:	00475713          	srli	a4,a4,0x4
    420c:	006786b3          	add	a3,a5,t1
    4210:	00e6a023          	sw	a4,0(a3)
    4214:	01c787b3          	add	a5,a5,t3
    4218:	0007a023          	sw	zero,0(a5)
    421c:	01d52023          	sw	t4,0(a0)
    4220:	00062783          	lw	a5,0(a2) # 9e533000 <__fw_export_text_end+0x9e52df10>
    4224:	00178793          	addi	a5,a5,1
    4228:	00f62023          	sw	a5,0(a2)
    422c:	ab1ff06f          	j	3cdc <main+0x464>
    4230:	00100793          	li	a5,1
    4234:	00fa8023          	sb	a5,0(s5)
    4238:	b55ff06f          	j	3d8c <main+0x514>
    423c:	0ff0000f          	fence
    4240:	bb1ff06f          	j	3df0 <main+0x578>
    4244:	14872803          	lw	a6,328(a4)
    4248:	00072223          	sw	zero,4(a4)
    424c:	00685793          	srli	a5,a6,0x6
    4250:	03f7f793          	andi	a5,a5,63
    4254:	03f87813          	andi	a6,a6,63
    4258:	00481813          	slli	a6,a6,0x4
    425c:	00a79793          	slli	a5,a5,0xa
    4260:	0107e7b3          	or	a5,a5,a6
    4264:	0047d793          	srli	a5,a5,0x4
    4268:	00f72423          	sw	a5,8(a4)
    426c:	ffb218b7          	lui	a7,0xffb21
    4270:	0008a223          	sw	zero,4(a7) # ffb21004 <__stack_top+0x1f004>
    4274:	00f8a423          	sw	a5,8(a7)
    4278:	00400813          	li	a6,4
    427c:	8104a623          	sw	a6,-2036(s1)
    4280:	8004a823          	sw	zero,-2032(s1)
    4284:	00002737          	lui	a4,0x2
    4288:	80f4aa23          	sw	a5,-2028(s1)
    428c:	09070713          	addi	a4,a4,144 # 2090 <_start-0x17b0>
    4290:	80e8ae23          	sw	a4,-2020(a7)
    4294:	8008a823          	sw	zero,-2032(a7)
    4298:	80f8aa23          	sw	a5,-2028(a7)
    429c:	ffb308b7          	lui	a7,0xffb30
    42a0:	1488a303          	lw	t1,328(a7) # ffb30148 <__stack_top+0x2e148>
    42a4:	0008a223          	sw	zero,4(a7)
    42a8:	00635793          	srli	a5,t1,0x6
    42ac:	03f7f793          	andi	a5,a5,63
    42b0:	03f37313          	andi	t1,t1,63
    42b4:	00431313          	slli	t1,t1,0x4
    42b8:	00a79793          	slli	a5,a5,0xa
    42bc:	0067e7b3          	or	a5,a5,t1
    42c0:	0047d793          	srli	a5,a5,0x4
    42c4:	00f8a423          	sw	a5,8(a7)
    42c8:	ffb318b7          	lui	a7,0xffb31
    42cc:	0008a223          	sw	zero,4(a7) # ffb31004 <__stack_top+0x2f004>
    42d0:	00f8a423          	sw	a5,8(a7)
    42d4:	ffb32337          	lui	t1,0xffb32
    42d8:	81032623          	sw	a6,-2036(t1) # ffb3180c <__stack_top+0x2f80c>
    42dc:	80032823          	sw	zero,-2032(t1)
    42e0:	80f32a23          	sw	a5,-2028(t1)
    42e4:	80e8ae23          	sw	a4,-2020(a7)
    42e8:	8008a823          	sw	zero,-2032(a7)
    42ec:	80f8aa23          	sw	a5,-2028(a7)
    42f0:	b65ff06f          	j	3e54 <main+0x5dc>
    42f4:	08fc9863          	bne	s9,a5,4384 <.NO_CB1545+0x43c>
    42f8:	ffb20737          	lui	a4,0xffb20
    42fc:	20872383          	lw	t2,520(a4) # ffb20208 <__stack_top+0x1e208>
    4300:	ffb307b7          	lui	a5,0xffb30
    4304:	2087a283          	lw	t0,520(a5) # ffb30208 <__stack_top+0x2e208>
    4308:	22872f83          	lw	t6,552(a4)
    430c:	2287af03          	lw	t5,552(a5)
    4310:	20472e83          	lw	t4,516(a4)
    4314:	2047ae03          	lw	t3,516(a5)
    4318:	20072303          	lw	t1,512(a4)
    431c:	2007a883          	lw	a7,512(a5)
    4320:	22c72803          	lw	a6,556(a4)
    4324:	22c7a703          	lw	a4,556(a5)
    4328:	000077b7          	lui	a5,0x7
    432c:	0477a023          	sw	t2,64(a5) # 7040 <__fw_export_text_end+0x1f50>
    4330:	0607a423          	sw	zero,104(a5)
    4334:	0407aa23          	sw	zero,84(a5)
    4338:	0657ae23          	sw	t0,124(a5)
    433c:	05f7a223          	sw	t6,68(a5)
    4340:	0607a623          	sw	zero,108(a5)
    4344:	0407ac23          	sw	zero,88(a5)
    4348:	09e7a023          	sw	t5,128(a5)
    434c:	05d7a423          	sw	t4,72(a5)
    4350:	0607a823          	sw	zero,112(a5)
    4354:	0407ae23          	sw	zero,92(a5)
    4358:	09c7a223          	sw	t3,132(a5)
    435c:	0467a623          	sw	t1,76(a5)
    4360:	0607aa23          	sw	zero,116(a5)
    4364:	0607a023          	sw	zero,96(a5)
    4368:	0917a423          	sw	a7,136(a5)
    436c:	0507a823          	sw	a6,80(a5)
    4370:	0607ac23          	sw	zero,120(a5)
    4374:	0607a223          	sw	zero,100(a5)
    4378:	08e7a623          	sw	a4,140(a5)
    437c:	00100713          	li	a4,1
    4380:	b51ff06f          	j	3ed0 <main+0x658>
    4384:	14872803          	lw	a6,328(a4)
    4388:	00685793          	srli	a5,a6,0x6
    438c:	03f7f793          	andi	a5,a5,63
    4390:	03f87813          	andi	a6,a6,63
    4394:	00481813          	slli	a6,a6,0x4
    4398:	00a79793          	slli	a5,a5,0xa
    439c:	0107e7b3          	or	a5,a5,a6
    43a0:	0047d793          	srli	a5,a5,0x4
    43a4:	ffb21837          	lui	a6,0xffb21
    43a8:	80f82a23          	sw	a5,-2028(a6) # ffb20814 <__stack_top+0x1e814>
    43ac:	00f72423          	sw	a5,8(a4)
    43b0:	80f4aa23          	sw	a5,-2028(s1)
    43b4:	00f82423          	sw	a5,8(a6)
    43b8:	ffb30837          	lui	a6,0xffb30
    43bc:	14882703          	lw	a4,328(a6) # ffb30148 <__stack_top+0x2e148>
    43c0:	00675793          	srli	a5,a4,0x6
    43c4:	03f7f793          	andi	a5,a5,63
    43c8:	03f77713          	andi	a4,a4,63
    43cc:	00471713          	slli	a4,a4,0x4
    43d0:	00a79793          	slli	a5,a5,0xa
    43d4:	00e7e7b3          	or	a5,a5,a4
    43d8:	0047d793          	srli	a5,a5,0x4
    43dc:	ffb31737          	lui	a4,0xffb31
    43e0:	80f72a23          	sw	a5,-2028(a4) # ffb30814 <__stack_top+0x2e814>
    43e4:	00f82423          	sw	a5,8(a6)
    43e8:	ffb32837          	lui	a6,0xffb32
    43ec:	80f82a23          	sw	a5,-2028(a6) # ffb31814 <__stack_top+0x2f814>
    43f0:	00f72423          	sw	a5,8(a4)
    43f4:	f05ff06f          	j	42f8 <.NO_CB1545+0x3b0>
    43f8:	060c9e63          	bnez	s9,4474 <.NO_CB1545+0x52c>
    43fc:	ffb206b7          	lui	a3,0xffb20
    4400:	01061793          	slli	a5,a2,0x10
    4404:	20868593          	addi	a1,a3,520 # ffb20208 <__stack_top+0x1e208>
    4408:	00b785b3          	add	a1,a5,a1
    440c:	0005a503          	lw	a0,0(a1)
    4410:	22868593          	addi	a1,a3,552
    4414:	00b785b3          	add	a1,a5,a1
    4418:	0005a803          	lw	a6,0(a1)
    441c:	20468593          	addi	a1,a3,516
    4420:	00b785b3          	add	a1,a5,a1
    4424:	0005a883          	lw	a7,0(a1)
    4428:	20068593          	addi	a1,a3,512
    442c:	22c68693          	addi	a3,a3,556
    4430:	00b785b3          	add	a1,a5,a1
    4434:	00d787b3          	add	a5,a5,a3
    4438:	0005a583          	lw	a1,0(a1)
    443c:	0007a683          	lw	a3,0(a5)
    4440:	00c12783          	lw	a5,12(sp)
    4444:	20f647b3          	sh2add	a5,a2,a5
    4448:	00a7a023          	sw	a0,0(a5)
    444c:	01012783          	lw	a5,16(sp)
    4450:	20f647b3          	sh2add	a5,a2,a5
    4454:	0107a023          	sw	a6,0(a5)
    4458:	01412783          	lw	a5,20(sp)
    445c:	20f647b3          	sh2add	a5,a2,a5
    4460:	0117a023          	sw	a7,0(a5)
    4464:	217647b3          	sh2add	a5,a2,s7
    4468:	00b7a023          	sw	a1,0(a5)
    446c:	214647b3          	sh2add	a5,a2,s4
    4470:	00d7a023          	sw	a3,0(a5)
    4474:	04c42783          	lw	a5,76(s0)
    4478:	02078c63          	beqz	a5,44b0 <.NO_CB1545+0x568>
    447c:	01445503          	lhu	a0,20(s0)
    4480:	04644583          	lbu	a1,70(s0)
    4484:	000c8693          	mv	a3,s9
    4488:	0ff5f593          	zext.b	a1,a1
    448c:	01b50533          	add	a0,a0,s11
    4490:	00b12c23          	sw	a1,24(sp)
    4494:	00c12e23          	sw	a2,28(sp)
    4498:	5a8000ef          	jal	4a40 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>
    449c:	01812583          	lw	a1,24(sp)
    44a0:	02000793          	li	a5,32
    44a4:	00f58663          	beq	a1,a5,44b0 <.NO_CB1545+0x568>
    44a8:	01c12503          	lw	a0,28(sp)
    44ac:	335000ef          	jal	4fe0 <_Z33barrier_remote_cb_interface_setuphm.part.0>
    44b0:	3a002783          	lw	a5,928(zero) # 3a0 <_start-0x34a0>
    44b4:	08000713          	li	a4,128
    44b8:	00279793          	slli	a5,a5,0x2
    44bc:	37078793          	addi	a5,a5,880
    44c0:	0037c683          	lbu	a3,3(a5)
    44c4:	aee680e3          	beq	a3,a4,3fa4 <.NO_CB1545+0x5c>
    44c8:	0ff0000f          	fence
    44cc:	ff5ff06f          	j	44c0 <.NO_CB1545+0x578>
    44d0:	0ff0000f          	fence
    44d4:	ad1ff06f          	j	3fa4 <.NO_CB1545+0x5c>

000044d8 <_ZN15kernel_profiler13init_profilerEttt.constprop.0>:
    44d8:	00c00713          	li	a4,12
    44dc:	86e1aa23          	sw	a4,-1932(gp) # ffb00064 <_ZN15kernel_profiler6wIndexE>
    44e0:	8601a823          	sw	zero,-1936(gp) # ffb00060 <_ZN15kernel_profiler9stackSizeE>
    44e4:	86818713          	addi	a4,gp,-1944 # ffb00058 <_ZN15kernel_profiler6sumIDsE>
    44e8:	86018793          	addi	a5,gp,-1952 # ffb00050 <_ZN15kernel_profiler4sumsE>
    44ec:	0007a023          	sw	zero,0(a5)
    44f0:	0007a223          	sw	zero,4(a5)
    44f4:	00072023          	sw	zero,0(a4)
    44f8:	00072223          	sw	zero,4(a4)
    44fc:	00001737          	lui	a4,0x1
    4500:	9f472683          	lw	a3,-1548(a4) # 9f4 <_start-0x2e4c>
    4504:	a0072623          	sw	zero,-1524(a4)
    4508:	02069e63          	bnez	a3,4544 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0x6c>
    450c:	000036b7          	lui	a3,0x3
    4510:	a4070793          	addi	a5,a4,-1472
    4514:	24068693          	addi	a3,a3,576 # 3240 <_start-0x600>
    4518:	0007a023          	sw	zero,0(a5)
    451c:	0007a223          	sw	zero,4(a5)
    4520:	0007a423          	sw	zero,8(a5)
    4524:	0007a623          	sw	zero,12(a5)
    4528:	7ff78793          	addi	a5,a5,2047
    452c:	00178793          	addi	a5,a5,1
    4530:	fed794e3          	bne	a5,a3,4518 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0x40>
    4534:	85c1c783          	lbu	a5,-1956(gp) # ffb0004c <my_x>
    4538:	9ef72c23          	sw	a5,-1544(a4)
    453c:	8581c783          	lbu	a5,-1960(gp) # ffb00048 <my_y>
    4540:	9ef72e23          	sw	a5,-1540(a4)
    4544:	8541a683          	lw	a3,-1964(gp) # ffb00044 <_ZN15kernel_profiler10traceCountE>
    4548:	080007b7          	lui	a5,0x8000
    454c:	00b69693          	slli	a3,a3,0xb
    4550:	80078793          	addi	a5,a5,-2048 # 7fff800 <__fw_export_text_end+0x7ffa710>
    4554:	00001537          	lui	a0,0x1
    4558:	000035b7          	lui	a1,0x3
    455c:	00f6f6b3          	and	a3,a3,a5
    4560:	a4050713          	addi	a4,a0,-1472 # a40 <_start-0x2e00>
    4564:	80000837          	lui	a6,0x80000
    4568:	00c00893          	li	a7,12
    456c:	24058593          	addi	a1,a1,576 # 3240 <_start-0x600>
    4570:	00400793          	li	a5,4
    4574:	20e7c633          	sh2add	a2,a5,a4
    4578:	00178793          	addi	a5,a5,1
    457c:	01062023          	sw	a6,0(a2)
    4580:	ff179ae3          	bne	a5,a7,4574 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0x9c>
    4584:	a4050793          	addi	a5,a0,-1472
    4588:	0087a603          	lw	a2,8(a5)
    458c:	7ff78793          	addi	a5,a5,2047
    4590:	7ff67613          	andi	a2,a2,2047
    4594:	00d66633          	or	a2,a2,a3
    4598:	80c7a4a3          	sw	a2,-2039(a5)
    459c:	00178793          	addi	a5,a5,1
    45a0:	feb794e3          	bne	a5,a1,4588 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0xb0>
    45a4:	7ff70713          	addi	a4,a4,2047
    45a8:	00170713          	addi	a4,a4,1
    45ac:	fcf712e3          	bne	a4,a5,4570 <_ZN15kernel_profiler13init_profilerEttt.constprop.0+0x98>
    45b0:	00008067          	ret

000045b4 <_ZN15kernel_profiler15finish_profilerEv>:
    45b4:	00000613          	li	a2,0
    45b8:	86018593          	addi	a1,gp,-1952 # ffb00050 <_ZN15kernel_profiler4sumsE>
    45bc:	1ff00313          	li	t1,511
    45c0:	00400893          	li	a7,4
    45c4:	00b607b3          	add	a5,a2,a1
    45c8:	0007a803          	lw	a6,0(a5)
    45cc:	04080263          	beqz	a6,4610 <_ZN15kernel_profiler15finish_profilerEv+0x5c>
    45d0:	8741a683          	lw	a3,-1932(gp) # ffb00064 <_ZN15kernel_profiler6wIndexE>
    45d4:	02d36e63          	bltu	t1,a3,4610 <_ZN15kernel_profiler15finish_profilerEv+0x5c>
    45d8:	86818793          	addi	a5,gp,-1944 # ffb00058 <_ZN15kernel_profiler6sumIDsE>
    45dc:	00f607b3          	add	a5,a2,a5
    45e0:	0007a783          	lw	a5,0(a5)
    45e4:	0ffff737          	lui	a4,0xffff
    45e8:	00c79793          	slli	a5,a5,0xc
    45ec:	00e7f7b3          	and	a5,a5,a4
    45f0:	a0000737          	lui	a4,0xa0000
    45f4:	00e7e7b3          	or	a5,a5,a4
    45f8:	00269713          	slli	a4,a3,0x2
    45fc:	7ff70713          	addi	a4,a4,2047 # a00007ff <__fw_export_text_end+0x9fffb70f>
    4600:	24f720a3          	sw	a5,577(a4)
    4604:	00268693          	addi	a3,a3,2
    4608:	250722a3          	sw	a6,581(a4)
    460c:	86d1aa23          	sw	a3,-1932(gp) # ffb00064 <_ZN15kernel_profiler6wIndexE>
    4610:	29161263          	bne	a2,a7,4894 <_ZN15kernel_profiler15finish_profilerEv+0x2e0>
    4614:	00000693          	li	a3,0
    4618:	1ff00593          	li	a1,511
    461c:	80000537          	lui	a0,0x80000
    4620:	8741a783          	lw	a5,-1932(gp) # ffb00064 <_ZN15kernel_profiler6wIndexE>
    4624:	0037f713          	andi	a4,a5,3
    4628:	26e6ea63          	bltu	a3,a4,489c <_ZN15kernel_profiler15finish_profilerEv+0x2e8>
    462c:	000016b7          	lui	a3,0x1
    4630:	9cf6aa23          	sw	a5,-1580(a3) # 9d4 <_start-0x2e6c>
    4634:	a0c6a783          	lw	a5,-1524(a3)
    4638:	00100713          	li	a4,1
    463c:	9c068813          	addi	a6,a3,-1600
    4640:	3ee78e63          	beq	a5,a4,4a3c <_ZN15kernel_profiler15finish_profilerEv+0x488>
    4644:	04082603          	lw	a2,64(a6) # 80000040 <__fw_export_text_end+0x7fffaf50>
    4648:	03082783          	lw	a5,48(a6)
    464c:	f9010113          	addi	sp,sp,-112
    4650:	780405b7          	lui	a1,0x78040
    4654:	fff58593          	addi	a1,a1,-1 # 7803ffff <__fw_export_text_end+0x7803af0f>
    4658:	07212223          	sw	s2,100(sp)
    465c:	05a12223          	sw	s10,68(sp)
    4660:	06912423          	sw	s1,104(sp)
    4664:	05712823          	sw	s7,80(sp)
    4668:	05912423          	sw	s9,72(sp)
    466c:	06812623          	sw	s0,108(sp)
    4670:	07312023          	sw	s3,96(sp)
    4674:	05412e23          	sw	s4,92(sp)
    4678:	00f12023          	sw	a5,0(sp)
    467c:	8501cf83          	lbu	t6,-1968(gp) # ffb00040 <noc_index>
    4680:	ffb207b7          	lui	a5,0xffb20
    4684:	010f9713          	slli	a4,t6,0x10
    4688:	01c78f13          	addi	t5,a5,28 # ffb2001c <__stack_top+0x1e01c>
    468c:	01e70f33          	add	t5,a4,t5
    4690:	000f2503          	lw	a0,0(t5)
    4694:	01478e93          	addi	t4,a5,20
    4698:	00b575b3          	and	a1,a0,a1
    469c:	01d70eb3          	add	t4,a4,t4
    46a0:	00b12623          	sw	a1,12(sp)
    46a4:	000ea583          	lw	a1,0(t4)
    46a8:	00f70933          	add	s2,a4,a5
    46ac:	00b12823          	sw	a1,16(sp)
    46b0:	00c78e13          	addi	t3,a5,12
    46b4:	00092583          	lw	a1,0(s2)
    46b8:	01c70e33          	add	t3,a4,t3
    46bc:	00b12a23          	sw	a1,20(sp)
    46c0:	02078313          	addi	t1,a5,32
    46c4:	000e2583          	lw	a1,0(t3)
    46c8:	00670333          	add	t1,a4,t1
    46cc:	00b12c23          	sw	a1,24(sp)
    46d0:	00032583          	lw	a1,0(t1)
    46d4:	01878493          	addi	s1,a5,24
    46d8:	00b12e23          	sw	a1,28(sp)
    46dc:	00878593          	addi	a1,a5,8
    46e0:	00b705b3          	add	a1,a4,a1
    46e4:	00b12223          	sw	a1,4(sp)
    46e8:	0005a583          	lw	a1,0(a1)
    46ec:	009704b3          	add	s1,a4,s1
    46f0:	02b12023          	sw	a1,32(sp)
    46f4:	00478593          	addi	a1,a5,4
    46f8:	00b70d33          	add	s10,a4,a1
    46fc:	000d2583          	lw	a1,0(s10)
    4700:	05512c23          	sw	s5,88(sp)
    4704:	05612a23          	sw	s6,84(sp)
    4708:	05812623          	sw	s8,76(sp)
    470c:	05b12023          	sw	s11,64(sp)
    4710:	02b12223          	sw	a1,36(sp)
    4714:	0004a583          	lw	a1,0(s1)
    4718:	0004a023          	sw	zero,0(s1)
    471c:	02b12423          	sw	a1,40(sp)
    4720:	02878593          	addi	a1,a5,40
    4724:	00b70cb3          	add	s9,a4,a1
    4728:	000ca583          	lw	a1,0(s9)
    472c:	01078793          	addi	a5,a5,16
    4730:	00f707b3          	add	a5,a4,a5
    4734:	02b12623          	sw	a1,44(sp)
    4738:	0007a583          	lw	a1,0(a5)
    473c:	00000293          	li	t0,0
    4740:	02b12823          	sw	a1,48(sp)
    4744:	00361593          	slli	a1,a2,0x3
    4748:	7f85f593          	andi	a1,a1,2040
    474c:	00b12423          	sw	a1,8(sp)
    4750:	000505b7          	lui	a1,0x50
    4754:	02b60633          	mul	a2,a2,a1
    4758:	00012583          	lw	a1,0(sp)
    475c:	00004bb7          	lui	s7,0x4
    4760:	00b60633          	add	a2,a2,a1
    4764:	02c12a23          	sw	a2,52(sp)
    4768:	08000637          	lui	a2,0x8000
    476c:	80060613          	addi	a2,a2,-2048 # 7fff800 <__fw_export_text_end+0x7ffa710>
    4770:	9d468593          	addi	a1,a3,-1580
    4774:	02c12c23          	sw	a2,56(sp)
    4778:	a4068693          	addi	a3,a3,-1472
    477c:	0086a603          	lw	a2,8(a3)
    4780:	03812503          	lw	a0,56(sp)
    4784:	00a67633          	and	a2,a2,a0
    4788:	00812503          	lw	a0,8(sp)
    478c:	00556533          	or	a0,a0,t0
    4790:	00a66633          	or	a2,a2,a0
    4794:	00c6a423          	sw	a2,8(a3)
    4798:	0005a603          	lw	a2,0(a1) # 50000 <__fw_export_text_end+0x4af10>
    479c:	14060c63          	beqz	a2,48f4 <_ZN15kernel_profiler15finish_profilerEv+0x340>
    47a0:	0005a503          	lw	a0,0(a1)
    47a4:	fec5a603          	lw	a2,-20(a1)
    47a8:	fec58393          	addi	t2,a1,-20
    47ac:	00c50533          	add	a0,a0,a2
    47b0:	fec5a603          	lw	a2,-20(a1)
    47b4:	fec5a883          	lw	a7,-20(a1)
    47b8:	10abe463          	bltu	s7,a0,48c0 <_ZN15kernel_profiler15finish_profilerEv+0x30c>
    47bc:	0005a603          	lw	a2,0(a1)
    47c0:	fea5a623          	sw	a0,-20(a1)
    47c4:	00261613          	slli	a2,a2,0x2
    47c8:	00012503          	lw	a0,0(sp)
    47cc:	12050463          	beqz	a0,48f4 <_ZN15kernel_profiler15finish_profilerEv+0x340>
    47d0:	03412383          	lw	t2,52(sp)
    47d4:	01029513          	slli	a0,t0,0x10
    47d8:	00750533          	add	a0,a0,t2
    47dc:	00d603b3          	add	t2,a2,a3
    47e0:	20a8c8b3          	sh2add	a7,a7,a0
    47e4:	02712e23          	sw	t2,60(sp)
    47e8:	ffb203b7          	lui	t2,0xffb20
    47ec:	10006537          	lui	a0,0x10006
    47f0:	04038393          	addi	t2,t2,64 # ffb20040 <__stack_top+0x1e040>
    47f4:	00002a37          	lui	s4,0x2
    47f8:	10000ab7          	lui	s5,0x10000
    47fc:	01000b37          	lui	s6,0x1000
    4800:	84818413          	addi	s0,gp,-1976 # ffb00038 <noc_posted_writes_num_issued>
    4804:	13050513          	addi	a0,a0,304 # 10006130 <__fw_export_text_end+0x10001040>
    4808:	208fc433          	sh2add	s0,t6,s0
    480c:	000049b7          	lui	s3,0x4
    4810:	007703b3          	add	t2,a4,t2
    4814:	082a0a13          	addi	s4,s4,130 # 2082 <_start-0x17be>
    4818:	00fa8a93          	addi	s5,s5,15 # 1000000f <__fw_export_text_end+0xfffaf1f>
    481c:	fffb0b13          	addi	s6,s6,-1 # ffffff <__fw_export_text_end+0xffaf0f>
    4820:	03c12c03          	lw	s8,60(sp)
    4824:	40cc0c33          	sub	s8,s8,a2
    4828:	1ac9ee63          	bltu	s3,a2,49e4 <_ZN15kernel_profiler15finish_profilerEv+0x430>
    482c:	ffb203b7          	lui	t2,0xffb20
    4830:	04038393          	addi	t2,t2,64 # ffb20040 <__stack_top+0x1e040>
    4834:	007703b3          	add	t2,a4,t2
    4838:	0003a403          	lw	s0,0(t2)
    483c:	fe041ee3          	bnez	s0,4838 <_ZN15kernel_profiler15finish_profilerEv+0x284>
    4840:	00002437          	lui	s0,0x2
    4844:	08240413          	addi	s0,s0,130 # 2082 <_start-0x17be>
    4848:	008f2023          	sw	s0,0(t5)
    484c:	01892023          	sw	s8,0(s2)
    4850:	011e2023          	sw	a7,0(t3)
    4854:	100008b7          	lui	a7,0x10000
    4858:	00f88893          	addi	a7,a7,15 # 1000000f <__fw_export_text_end+0xfffaf1f>
    485c:	011578b3          	and	a7,a0,a7
    4860:	0117a023          	sw	a7,0(a5)
    4864:	00451893          	slli	a7,a0,0x4
    4868:	0088d513          	srli	a0,a7,0x8
    486c:	00aea023          	sw	a0,0(t4)
    4870:	00c32023          	sw	a2,0(t1)
    4874:	00100613          	li	a2,1
    4878:	00c3a023          	sw	a2,0(t2)
    487c:	84818613          	addi	a2,gp,-1976 # ffb00038 <noc_posted_writes_num_issued>
    4880:	20cfc633          	sh2add	a2,t6,a2
    4884:	00062503          	lw	a0,0(a2)
    4888:	00150513          	addi	a0,a0,1
    488c:	00a62023          	sw	a0,0(a2)
    4890:	0640006f          	j	48f4 <_ZN15kernel_profiler15finish_profilerEv+0x340>
    4894:	00400613          	li	a2,4
    4898:	d2dff06f          	j	45c4 <_ZN15kernel_profiler15finish_profilerEv+0x10>
    489c:	00f5ee63          	bltu	a1,a5,48b8 <_ZN15kernel_profiler15finish_profilerEv+0x304>
    48a0:	00279713          	slli	a4,a5,0x2
    48a4:	7ff70713          	addi	a4,a4,2047
    48a8:	24a720a3          	sw	a0,577(a4)
    48ac:	00278793          	addi	a5,a5,2
    48b0:	240722a3          	sw	zero,581(a4)
    48b4:	86f1aa23          	sw	a5,-1932(gp) # ffb00064 <_ZN15kernel_profiler6wIndexE>
    48b8:	00168693          	addi	a3,a3,1
    48bc:	d65ff06f          	j	4620 <_ZN15kernel_profiler15finish_profilerEv+0x6c>
    48c0:	00100513          	li	a0,1
    48c4:	00c60613          	addi	a2,a2,12
    48c8:	00551533          	sll	a0,a0,t0
    48cc:	00cbee63          	bltu	s7,a2,48e8 <_ZN15kernel_profiler15finish_profilerEv+0x334>
    48d0:	00c3a023          	sw	a2,0(t2)
    48d4:	04882603          	lw	a2,72(a6)
    48d8:	00a66633          	or	a2,a2,a0
    48dc:	04c82423          	sw	a2,72(a6)
    48e0:	03000613          	li	a2,48
    48e4:	ee5ff06f          	j	47c8 <_ZN15kernel_profiler15finish_profilerEv+0x214>
    48e8:	04882603          	lw	a2,72(a6)
    48ec:	00a66633          	or	a2,a2,a0
    48f0:	04c82423          	sw	a2,72(a6)
    48f4:	7ff68693          	addi	a3,a3,2047
    48f8:	00128293          	addi	t0,t0,1
    48fc:	00500613          	li	a2,5
    4900:	00168693          	addi	a3,a3,1
    4904:	00458593          	addi	a1,a1,4
    4908:	e6c29ae3          	bne	t0,a2,477c <_ZN15kernel_profiler15finish_profilerEv+0x1c8>
    490c:	84818693          	addi	a3,gp,-1976 # ffb00038 <noc_posted_writes_num_issued>
    4910:	20dfcfb3          	sh2add	t6,t6,a3
    4914:	ffb206b7          	lui	a3,0xffb20
    4918:	22c68693          	addi	a3,a3,556 # ffb2022c <__stack_top+0x1e22c>
    491c:	000fa603          	lw	a2,0(t6)
    4920:	00d706b3          	add	a3,a4,a3
    4924:	0006a583          	lw	a1,0(a3)
    4928:	fec59ee3          	bne	a1,a2,4924 <_ZN15kernel_profiler15finish_profilerEv+0x370>
    492c:	000016b7          	lui	a3,0x1
    4930:	9f46a603          	lw	a2,-1548(a3) # 9f4 <_start-0x2e4c>
    4934:	00160613          	addi	a2,a2,1
    4938:	9ec6aa23          	sw	a2,-1548(a3)
    493c:	00100613          	li	a2,1
    4940:	a0c6a623          	sw	a2,-1524(a3)
    4944:	ffb206b7          	lui	a3,0xffb20
    4948:	04068693          	addi	a3,a3,64 # ffb20040 <__stack_top+0x1e040>
    494c:	00d70733          	add	a4,a4,a3
    4950:	00072683          	lw	a3,0(a4)
    4954:	fe069ee3          	bnez	a3,4950 <_ZN15kernel_profiler15finish_profilerEv+0x39c>
    4958:	00c12703          	lw	a4,12(sp)
    495c:	02012683          	lw	a3,32(sp)
    4960:	00ef2023          	sw	a4,0(t5)
    4964:	01012703          	lw	a4,16(sp)
    4968:	06c12403          	lw	s0,108(sp)
    496c:	00eea023          	sw	a4,0(t4)
    4970:	01412703          	lw	a4,20(sp)
    4974:	06012983          	lw	s3,96(sp)
    4978:	00e92023          	sw	a4,0(s2)
    497c:	01812703          	lw	a4,24(sp)
    4980:	06412903          	lw	s2,100(sp)
    4984:	00ee2023          	sw	a4,0(t3)
    4988:	01c12703          	lw	a4,28(sp)
    498c:	05c12a03          	lw	s4,92(sp)
    4990:	00e32023          	sw	a4,0(t1)
    4994:	00412703          	lw	a4,4(sp)
    4998:	05812a83          	lw	s5,88(sp)
    499c:	00d72023          	sw	a3,0(a4)
    49a0:	02412703          	lw	a4,36(sp)
    49a4:	05412b03          	lw	s6,84(sp)
    49a8:	00ed2023          	sw	a4,0(s10)
    49ac:	02812703          	lw	a4,40(sp)
    49b0:	05012b83          	lw	s7,80(sp)
    49b4:	00e4a023          	sw	a4,0(s1)
    49b8:	02c12703          	lw	a4,44(sp)
    49bc:	06812483          	lw	s1,104(sp)
    49c0:	00eca023          	sw	a4,0(s9)
    49c4:	03012703          	lw	a4,48(sp)
    49c8:	04c12c03          	lw	s8,76(sp)
    49cc:	04812c83          	lw	s9,72(sp)
    49d0:	04412d03          	lw	s10,68(sp)
    49d4:	00e7a023          	sw	a4,0(a5)
    49d8:	04012d83          	lw	s11,64(sp)
    49dc:	07010113          	addi	sp,sp,112
    49e0:	00008067          	ret
    49e4:	0003ad83          	lw	s11,0(t2)
    49e8:	fe0d9ee3          	bnez	s11,49e4 <_ZN15kernel_profiler15finish_profilerEv+0x430>
    49ec:	014f2023          	sw	s4,0(t5)
    49f0:	01892023          	sw	s8,0(s2)
    49f4:	011e2023          	sw	a7,0(t3)
    49f8:	01557c33          	and	s8,a0,s5
    49fc:	0187a023          	sw	s8,0(a5)
    4a00:	00455c13          	srli	s8,a0,0x4
    4a04:	016c7c33          	and	s8,s8,s6
    4a08:	018ea023          	sw	s8,0(t4)
    4a0c:	01332023          	sw	s3,0(t1)
    4a10:	00100c13          	li	s8,1
    4a14:	0183a023          	sw	s8,0(t2)
    4a18:	00042c03          	lw	s8,0(s0)
    4a1c:	41360633          	sub	a2,a2,s3
    4a20:	001c0c13          	addi	s8,s8,1
    4a24:	01842023          	sw	s8,0(s0)
    4a28:	01388c33          	add	s8,a7,s3
    4a2c:	011c3db3          	sltu	s11,s8,a7
    4a30:	00ad8533          	add	a0,s11,a0
    4a34:	000c0893          	mv	a7,s8
    4a38:	de9ff06f          	j	4820 <_ZN15kernel_profiler15finish_profilerEv+0x26c>
    4a3c:	00008067          	ret

00004a40 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0>:
    4a40:	fa010113          	addi	sp,sp,-96
    4a44:	fff58793          	addi	a5,a1,-1
    4a48:	00f12823          	sw	a5,16(sp)
    4a4c:	100007b7          	lui	a5,0x10000
    4a50:	00f78793          	addi	a5,a5,15 # 1000000f <__fw_export_text_end+0xfffaf1f>
    4a54:	00f12423          	sw	a5,8(sp)
    4a58:	010007b7          	lui	a5,0x1000
    4a5c:	ffb20337          	lui	t1,0xffb20
    4a60:	fff78793          	addi	a5,a5,-1 # ffffff <__fw_export_text_end+0xffaf0f>
    4a64:	03b12823          	sw	s11,48(sp)
    4a68:	00b71813          	slli	a6,a4,0xb
    4a6c:	01061d93          	slli	s11,a2,0x10
    4a70:	01b80833          	add	a6,a6,s11
    4a74:	00f12623          	sw	a5,12(sp)
    4a78:	00430793          	addi	a5,t1,4 # ffb20004 <__stack_top+0x1e004>
    4a7c:	04030293          	addi	t0,t1,64
    4a80:	00f807b3          	add	a5,a6,a5
    4a84:	04812e23          	sw	s0,92(sp)
    4a88:	05612223          	sw	s6,68(sp)
    4a8c:	82418393          	addi	t2,gp,-2012 # ffb00014 <noc_nonposted_atomics_acked>
    4a90:	04912c23          	sw	s1,88(sp)
    4a94:	207643b3          	sh2add	t2,a2,t2
    4a98:	05212a23          	sw	s2,84(sp)
    4a9c:	05312823          	sw	s3,80(sp)
    4aa0:	05412623          	sw	s4,76(sp)
    4aa4:	05512423          	sw	s5,72(sp)
    4aa8:	05712023          	sw	s7,64(sp)
    4aac:	03812e23          	sw	s8,60(sp)
    4ab0:	03912c23          	sw	s9,56(sp)
    4ab4:	03a12a23          	sw	s10,52(sp)
    4ab8:	00050413          	mv	s0,a0
    4abc:	87818593          	addi	a1,gp,-1928 # ffb00068 <cb_interface>
    4ac0:	01f00b13          	li	s6,31
    4ac4:	005802b3          	add	t0,a6,t0
    4ac8:	02f12623          	sw	a5,44(sp)
    4acc:	01012783          	lw	a5,16(sp)
    4ad0:	03679e63          	bne	a5,s6,4b0c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0xcc>
    4ad4:	05c12403          	lw	s0,92(sp)
    4ad8:	05812483          	lw	s1,88(sp)
    4adc:	05412903          	lw	s2,84(sp)
    4ae0:	05012983          	lw	s3,80(sp)
    4ae4:	04c12a03          	lw	s4,76(sp)
    4ae8:	04812a83          	lw	s5,72(sp)
    4aec:	04412b03          	lw	s6,68(sp)
    4af0:	04012b83          	lw	s7,64(sp)
    4af4:	03c12c03          	lw	s8,60(sp)
    4af8:	03812c83          	lw	s9,56(sp)
    4afc:	03412d03          	lw	s10,52(sp)
    4b00:	03012d83          	lw	s11,48(sp)
    4b04:	06010113          	addi	sp,sp,96
    4b08:	00008067          	ret
    4b0c:	00042f03          	lw	t5,0(s0)
    4b10:	00442503          	lw	a0,4(s0)
    4b14:	000f2f83          	lw	t6,0(t5)
    4b18:	004f2b83          	lw	s7,4(t5)
    4b1c:	008f2e03          	lw	t3,8(t5)
    4b20:	00cf2783          	lw	a5,12(t5)
    4b24:	010f2783          	lw	a5,16(t5)
    4b28:	014f2903          	lw	s2,20(t5)
    4b2c:	018f2883          	lw	a7,24(t5)
    4b30:	fff50e93          	addi	t4,a0,-1
    4b34:	00fe8eb3          	add	t4,t4,a5
    4b38:	41ce8eb3          	sub	t4,t4,t3
    4b3c:	02aedeb3          	divu	t4,t4,a0
    4b40:	02ae8eb3          	mul	t4,t4,a0
    4b44:	01ce8eb3          	add	t4,t4,t3
    4b48:	280f8663          	beqz	t6,4dd4 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x394>
    4b4c:	3fe5a023          	sw	t5,992(a1)
    4b50:	3fc5a223          	sw	t3,996(a1)
    4b54:	3ef5a823          	sw	a5,1008(a1)
    4b58:	3f25aa23          	sw	s2,1012(a1)
    4b5c:	3f15ac23          	sw	a7,1016(a1)
    4b60:	3f75ae23          	sw	s7,1020(a1)
    4b64:	00cf2f03          	lw	t5,12(t5)
    4b68:	01ee09b3          	add	s3,t3,t5
    4b6c:	02af7fb3          	remu	t6,t5,a0
    4b70:	41f989b3          	sub	s3,s3,t6
    4b74:	0f3ee063          	bltu	t4,s3,4c54 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x214>
    4b78:	40ff0f33          	sub	t5,t5,a5
    4b7c:	01cf0f33          	add	t5,t5,t3
    4b80:	004f5793          	srli	a5,t5,0x4
    4b84:	16078463          	beqz	a5,4cec <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2ac>
    4b88:	00100e93          	li	t4,1
    4b8c:	00000f13          	li	t5,0
    4b90:	0dd68c63          	beq	a3,t4,4c68 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x228>
    4b94:	00830f93          	addi	t6,t1,8
    4b98:	01c30493          	addi	s1,t1,28
    4b9c:	00680ab3          	add	s5,a6,t1
    4ba0:	01f80fb3          	add	t6,a6,t6
    4ba4:	009804b3          	add	s1,a6,s1
    4ba8:	15eb8263          	beq	s7,t5,4cec <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2ac>
    4bac:	212f6a33          	sh3add	s4,t5,s2
    4bb0:	004a2e83          	lw	t4,4(s4)
    4bb4:	000a2c03          	lw	s8,0(s4)
    4bb8:	0008aa03          	lw	s4,0(a7)
    4bbc:	006e9e93          	slli	t4,t4,0x6
    4bc0:	018eeeb3          	or	t4,t4,s8
    4bc4:	01478a33          	add	s4,a5,s4
    4bc8:	0148a023          	sw	s4,0(a7)
    4bcc:	004e9e93          	slli	t4,t4,0x4
    4bd0:	0002aa03          	lw	s4,0(t0)
    4bd4:	fe0a1ee3          	bnez	s4,4bd0 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x190>
    4bd8:	00812a03          	lw	s4,8(sp)
    4bdc:	02c12c03          	lw	s8,44(sp)
    4be0:	011aa023          	sw	a7,0(s5)
    4be4:	014efa33          	and	s4,t4,s4
    4be8:	014c2023          	sw	s4,0(s8)
    4bec:	00c12a03          	lw	s4,12(sp)
    4bf0:	004ede93          	srli	t4,t4,0x4
    4bf4:	014efeb3          	and	t4,t4,s4
    4bf8:	01dfa023          	sw	t4,0(t6)
    4bfc:	00002eb7          	lui	t4,0x2
    4c00:	091e8e93          	addi	t4,t4,145 # 2091 <_start-0x17af>
    4c04:	01d4a023          	sw	t4,0(s1)
    4c08:	00001a37          	lui	s4,0x1
    4c0c:	0028de93          	srli	t4,a7,0x2
    4c10:	07ca0a13          	addi	s4,s4,124 # 107c <_start-0x27c4>
    4c14:	003efe93          	andi	t4,t4,3
    4c18:	014eeeb3          	or	t4,t4,s4
    4c1c:	02030a13          	addi	s4,t1,32
    4c20:	01480a33          	add	s4,a6,s4
    4c24:	01da2023          	sw	t4,0(s4)
    4c28:	02830e93          	addi	t4,t1,40
    4c2c:	01d80eb3          	add	t4,a6,t4
    4c30:	00fea023          	sw	a5,0(t4)
    4c34:	00100e93          	li	t4,1
    4c38:	01d2a023          	sw	t4,0(t0)
    4c3c:	0003ae83          	lw	t4,0(t2)
    4c40:	02088893          	addi	a7,a7,32
    4c44:	001e8e93          	addi	t4,t4,1
    4c48:	01d3a023          	sw	t4,0(t2)
    4c4c:	001f0f13          	addi	t5,t5,1
    4c50:	f59ff06f          	j	4ba8 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x168>
    4c54:	09d78e63          	beq	a5,t4,4cf0 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2b0>
    4c58:	40fe87b3          	sub	a5,t4,a5
    4c5c:	0047d793          	srli	a5,a5,0x4
    4c60:	000e8e13          	mv	t3,t4
    4c64:	f21ff06f          	j	4b84 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x144>
    4c68:	02800493          	li	s1,40
    4c6c:	00007eb7          	lui	t4,0x7
    4c70:	029604b3          	mul	s1,a2,s1
    4c74:	ffb20fb7          	lui	t6,0xffb20
    4c78:	04ce8e93          	addi	t4,t4,76 # 704c <__fw_export_text_end+0x1f5c>
    4c7c:	044f8c13          	addi	s8,t6,68 # ffb20044 <__stack_top+0x1e044>
    4c80:	01d484b3          	add	s1,s1,t4
    4c84:	00b71f13          	slli	t5,a4,0xb
    4c88:	01061e93          	slli	t4,a2,0x10
    4c8c:	01df0f33          	add	t5,t5,t4
    4c90:	018e8eb3          	add	t4,t4,s8
    4c94:	01d12a23          	sw	t4,20(sp)
    4c98:	00cf8e93          	addi	t4,t6,12
    4c9c:	01df0eb3          	add	t4,t5,t4
    4ca0:	01d12c23          	sw	t4,24(sp)
    4ca4:	10000eb7          	lui	t4,0x10000
    4ca8:	00fe8e93          	addi	t4,t4,15 # 1000000f <__fw_export_text_end+0xfffaf1f>
    4cac:	01d12e23          	sw	t4,28(sp)
    4cb0:	004f8e93          	addi	t4,t6,4
    4cb4:	01df0eb3          	add	t4,t5,t4
    4cb8:	03d12023          	sw	t4,32(sp)
    4cbc:	01000eb7          	lui	t4,0x1000
    4cc0:	fffe8e93          	addi	t4,t4,-1 # ffffff <__fw_export_text_end+0xffaf0f>
    4cc4:	008f8c13          	addi	s8,t6,8
    4cc8:	040f8a93          	addi	s5,t6,64
    4ccc:	03d12223          	sw	t4,36(sp)
    4cd0:	01cf8c93          	addi	s9,t6,28
    4cd4:	018f0eb3          	add	t4,t5,s8
    4cd8:	00000a13          	li	s4,0
    4cdc:	015f0ab3          	add	s5,t5,s5
    4ce0:	03d12423          	sw	t4,40(sp)
    4ce4:	019f0cb3          	add	s9,t5,s9
    4ce8:	034b9263          	bne	s7,s4,4d0c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2cc>
    4cec:	000e0e93          	mv	t4,t3
    4cf0:	3fd5a823          	sw	t4,1008(a1)
    4cf4:	3f35a423          	sw	s3,1000(a1)
    4cf8:	3ea5a623          	sw	a0,1004(a1)
    4cfc:	00840413          	addi	s0,s0,8
    4d00:	fffb0b13          	addi	s6,s6,-1
    4d04:	fe058593          	addi	a1,a1,-32
    4d08:	dc5ff06f          	j	4acc <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x8c>
    4d0c:	212a6d33          	sh3add	s10,s4,s2
    4d10:	004d2e83          	lw	t4,4(s10)
    4d14:	000d2d03          	lw	s10,0(s10)
    4d18:	006e9e93          	slli	t4,t4,0x6
    4d1c:	000d0c13          	mv	s8,s10
    4d20:	0008ad03          	lw	s10,0(a7)
    4d24:	018eeeb3          	or	t4,t4,s8
    4d28:	004e9e93          	slli	t4,t4,0x4
    4d2c:	01a78d33          	add	s10,a5,s10
    4d30:	01a8a023          	sw	s10,0(a7)
    4d34:	0004ad03          	lw	s10,0(s1)
    4d38:	001d0d13          	addi	s10,s10,1
    4d3c:	01a4a023          	sw	s10,0(s1)
    4d40:	000aad03          	lw	s10,0(s5)
    4d44:	fe0d1ee3          	bnez	s10,4d40 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x300>
    4d48:	01412d03          	lw	s10,20(sp)
    4d4c:	00400c13          	li	s8,4
    4d50:	000d2d03          	lw	s10,0(s10)
    4d54:	01812d03          	lw	s10,24(sp)
    4d58:	018d2023          	sw	s8,0(s10)
    4d5c:	01c12c03          	lw	s8,28(sp)
    4d60:	01ff0d33          	add	s10,t5,t6
    4d64:	011d2023          	sw	a7,0(s10)
    4d68:	018efd33          	and	s10,t4,s8
    4d6c:	02012c03          	lw	s8,32(sp)
    4d70:	004ede93          	srli	t4,t4,0x4
    4d74:	01ac2023          	sw	s10,0(s8)
    4d78:	02412c03          	lw	s8,36(sp)
    4d7c:	00001d37          	lui	s10,0x1
    4d80:	018efeb3          	and	t4,t4,s8
    4d84:	02812c03          	lw	s8,40(sp)
    4d88:	07cd0d13          	addi	s10,s10,124 # 107c <_start-0x27c4>
    4d8c:	01dc2023          	sw	t4,0(s8)
    4d90:	00002eb7          	lui	t4,0x2
    4d94:	091e8e93          	addi	t4,t4,145 # 2091 <_start-0x17af>
    4d98:	01dca023          	sw	t4,0(s9)
    4d9c:	0028de93          	srli	t4,a7,0x2
    4da0:	003efe93          	andi	t4,t4,3
    4da4:	01aeeeb3          	or	t4,t4,s10
    4da8:	020f8d13          	addi	s10,t6,32
    4dac:	01af0d33          	add	s10,t5,s10
    4db0:	01dd2023          	sw	t4,0(s10)
    4db4:	028f8e93          	addi	t4,t6,40
    4db8:	01df0eb3          	add	t4,t5,t4
    4dbc:	00fea023          	sw	a5,0(t4)
    4dc0:	00100e93          	li	t4,1
    4dc4:	01daa023          	sw	t4,0(s5)
    4dc8:	02088893          	addi	a7,a7,32
    4dcc:	01da0a33          	add	s4,s4,t4
    4dd0:	f19ff06f          	j	4ce8 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2a8>
    4dd4:	00092983          	lw	s3,0(s2)
    4dd8:	00492f83          	lw	t6,4(s2)
    4ddc:	01088493          	addi	s1,a7,16
    4de0:	3fe5a023          	sw	t5,992(a1)
    4de4:	3fc5a223          	sw	t3,996(a1)
    4de8:	3ef5a823          	sw	a5,1008(a1)
    4dec:	3e95ae23          	sw	s1,1020(a1)
    4df0:	3f35aa23          	sw	s3,1012(a1)
    4df4:	3ff5ac23          	sw	t6,1016(a1)
    4df8:	00cf2f03          	lw	t5,12(t5)
    4dfc:	01ee0fb3          	add	t6,t3,t5
    4e00:	02af7933          	remu	s2,t5,a0
    4e04:	412f8fb3          	sub	t6,t6,s2
    4e08:	13fee263          	bltu	t4,t6,4f2c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4ec>
    4e0c:	40ff0f33          	sub	t5,t5,a5
    4e10:	01cf0f33          	add	t5,t5,t3
    4e14:	004f5793          	srli	a5,t5,0x4
    4e18:	10078263          	beqz	a5,4f1c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4dc>
    4e1c:	0ff0000f          	fence
    4e20:	0004af03          	lw	t5,0(s1)
    4e24:	0008ae83          	lw	t4,0(a7)
    4e28:	41ee8eb3          	sub	t4,t4,t5
    4e2c:	fefee8e3          	bltu	t4,a5,4e1c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x3dc>
    4e30:	3f85ae83          	lw	t4,1016(a1)
    4e34:	3f45af03          	lw	t5,1012(a1)
    4e38:	00ae9e93          	slli	t4,t4,0xa
    4e3c:	004f1f13          	slli	t5,t5,0x4
    4e40:	01eeeeb3          	or	t4,t4,t5
    4e44:	00100f13          	li	t5,1
    4e48:	3fc5a883          	lw	a7,1020(a1)
    4e4c:	0fe69a63          	bne	a3,t5,4f40 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x500>
    4e50:	0008af03          	lw	t5,0(a7)
    4e54:	000074b7          	lui	s1,0x7
    4e58:	01e78f33          	add	t5,a5,t5
    4e5c:	01e8a023          	sw	t5,0(a7)
    4e60:	02800f13          	li	t5,40
    4e64:	04c48493          	addi	s1,s1,76 # 704c <__fw_export_text_end+0x1f5c>
    4e68:	03e60f33          	mul	t5,a2,t5
    4e6c:	009f0f33          	add	t5,t5,s1
    4e70:	000f2483          	lw	s1,0(t5)
    4e74:	00d484b3          	add	s1,s1,a3
    4e78:	009f2023          	sw	s1,0(t5)
    4e7c:	0002af03          	lw	t5,0(t0)
    4e80:	fe0f1ee3          	bnez	t5,4e7c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x43c>
    4e84:	ffb20f37          	lui	t5,0xffb20
    4e88:	044f0493          	addi	s1,t5,68 # ffb20044 <__stack_top+0x1e044>
    4e8c:	009d84b3          	add	s1,s11,s1
    4e90:	0004a483          	lw	s1,0(s1)
    4e94:	00cf0493          	addi	s1,t5,12
    4e98:	009804b3          	add	s1,a6,s1
    4e9c:	00400913          	li	s2,4
    4ea0:	0124a023          	sw	s2,0(s1)
    4ea4:	01e804b3          	add	s1,a6,t5
    4ea8:	0114a023          	sw	a7,0(s1)
    4eac:	10000937          	lui	s2,0x10000
    4eb0:	004f0493          	addi	s1,t5,4
    4eb4:	012ef933          	and	s2,t4,s2
    4eb8:	009804b3          	add	s1,a6,s1
    4ebc:	0124a023          	sw	s2,0(s1)
    4ec0:	004e9e93          	slli	t4,t4,0x4
    4ec4:	008f0493          	addi	s1,t5,8
    4ec8:	008ede93          	srli	t4,t4,0x8
    4ecc:	009804b3          	add	s1,a6,s1
    4ed0:	01d4a023          	sw	t4,0(s1)
    4ed4:	01cf0e93          	addi	t4,t5,28
    4ed8:	000024b7          	lui	s1,0x2
    4edc:	01d80eb3          	add	t4,a6,t4
    4ee0:	09148493          	addi	s1,s1,145 # 2091 <_start-0x17af>
    4ee4:	009ea023          	sw	s1,0(t4)
    4ee8:	0028d893          	srli	a7,a7,0x2
    4eec:	00001eb7          	lui	t4,0x1
    4ef0:	07ce8e93          	addi	t4,t4,124 # 107c <_start-0x27c4>
    4ef4:	0038f893          	andi	a7,a7,3
    4ef8:	01d8e8b3          	or	a7,a7,t4
    4efc:	020f0e93          	addi	t4,t5,32
    4f00:	01d80eb3          	add	t4,a6,t4
    4f04:	028f0f13          	addi	t5,t5,40
    4f08:	011ea023          	sw	a7,0(t4)
    4f0c:	01e80f33          	add	t5,a6,t5
    4f10:	00ff2023          	sw	a5,0(t5)
    4f14:	00100793          	li	a5,1
    4f18:	00f2a023          	sw	a5,0(t0)
    4f1c:	000e0e93          	mv	t4,t3
    4f20:	3fd5a823          	sw	t4,1008(a1)
    4f24:	3ff5a423          	sw	t6,1000(a1)
    4f28:	dd1ff06f          	j	4cf8 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x2b8>
    4f2c:	ffd78ae3          	beq	a5,t4,4f20 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4e0>
    4f30:	40fe87b3          	sub	a5,t4,a5
    4f34:	0047d793          	srli	a5,a5,0x4
    4f38:	000e8e13          	mv	t3,t4
    4f3c:	eddff06f          	j	4e18 <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x3d8>
    4f40:	0008af03          	lw	t5,0(a7)
    4f44:	01e78f33          	add	t5,a5,t5
    4f48:	01e8a023          	sw	t5,0(a7)
    4f4c:	0002af03          	lw	t5,0(t0)
    4f50:	fe0f1ee3          	bnez	t5,4f4c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x50c>
    4f54:	00680f33          	add	t5,a6,t1
    4f58:	011f2023          	sw	a7,0(t5)
    4f5c:	00812f03          	lw	t5,8(sp)
    4f60:	0028d893          	srli	a7,a7,0x2
    4f64:	01eef4b3          	and	s1,t4,t5
    4f68:	00430f13          	addi	t5,t1,4
    4f6c:	01e80f33          	add	t5,a6,t5
    4f70:	009f2023          	sw	s1,0(t5)
    4f74:	00c12f03          	lw	t5,12(sp)
    4f78:	004ede93          	srli	t4,t4,0x4
    4f7c:	01eefeb3          	and	t4,t4,t5
    4f80:	00830f13          	addi	t5,t1,8
    4f84:	01e80f33          	add	t5,a6,t5
    4f88:	01df2023          	sw	t4,0(t5)
    4f8c:	01c30e93          	addi	t4,t1,28
    4f90:	00002f37          	lui	t5,0x2
    4f94:	01d80eb3          	add	t4,a6,t4
    4f98:	091f0f13          	addi	t5,t5,145 # 2091 <_start-0x17af>
    4f9c:	01eea023          	sw	t5,0(t4)
    4fa0:	00001eb7          	lui	t4,0x1
    4fa4:	07ce8e93          	addi	t4,t4,124 # 107c <_start-0x27c4>
    4fa8:	0038f893          	andi	a7,a7,3
    4fac:	01d8e8b3          	or	a7,a7,t4
    4fb0:	02030e93          	addi	t4,t1,32
    4fb4:	01d80eb3          	add	t4,a6,t4
    4fb8:	011ea023          	sw	a7,0(t4)
    4fbc:	02830893          	addi	a7,t1,40
    4fc0:	011808b3          	add	a7,a6,a7
    4fc4:	00f8a023          	sw	a5,0(a7)
    4fc8:	00100793          	li	a5,1
    4fcc:	00f2a023          	sw	a5,0(t0)
    4fd0:	0003a783          	lw	a5,0(t2)
    4fd4:	00178793          	addi	a5,a5,1
    4fd8:	00f3a023          	sw	a5,0(t2)
    4fdc:	f41ff06f          	j	4f1c <_ZN12experimental26setup_remote_cb_interfacesILb1EEEvU11rvtt_l1_ptrPmmhhbh.constprop.0+0x4dc>

00004fe0 <_Z33barrier_remote_cb_interface_setuphm.part.0>:
    4fe0:	ffb20737          	lui	a4,0xffb20
    4fe4:	01051793          	slli	a5,a0,0x10
    4fe8:	20070713          	addi	a4,a4,512 # ffb20200 <__stack_top+0x1e200>
    4fec:	00e787b3          	add	a5,a5,a4
    4ff0:	82418713          	addi	a4,gp,-2012 # ffb00014 <noc_nonposted_atomics_acked>
    4ff4:	20e54533          	sh2add	a0,a0,a4
    4ff8:	00052703          	lw	a4,0(a0)
    4ffc:	0007a683          	lw	a3,0(a5)
    5000:	fee69ee3          	bne	a3,a4,4ffc <_Z33barrier_remote_cb_interface_setuphm.part.0+0x1c>
    5004:	0ff0000f          	fence
    5008:	00008067          	ret

0000500c <_Z15noc_set_cfg_regmm>:
    500c:	8141a783          	lw	a5,-2028(gp) # ffb00004 <_ZL19active_noc_instance>
    5010:	ffec8737          	lui	a4,0xffec8
    5014:	00e79793          	slli	a5,a5,0xe
    5018:	04070713          	addi	a4,a4,64 # ffec8040 <__instrn_buffer+0x88040>
    501c:	00e787b3          	add	a5,a5,a4
    5020:	00a787b3          	add	a5,a5,a0
    5024:	00279793          	slli	a5,a5,0x2
    5028:	00b7a023          	sw	a1,0(a5)
    502c:	00008067          	ret

00005030 <_Z15noc_get_cfg_regm>:
    5030:	8141a783          	lw	a5,-2028(gp) # ffb00004 <_ZL19active_noc_instance>
    5034:	ffec8737          	lui	a4,0xffec8
    5038:	04070713          	addi	a4,a4,64 # ffec8040 <__instrn_buffer+0x88040>
    503c:	00e79793          	slli	a5,a5,0xe
    5040:	00e787b3          	add	a5,a5,a4
    5044:	00a787b3          	add	a5,a5,a0
    5048:	00279793          	slli	a5,a5,0x2
    504c:	0007a503          	lw	a0,0(a5)
    5050:	00008067          	ret

00005054 <wzerorange>:
    5054:	01050513          	addi	a0,a0,16
    5058:	02a5f463          	bgeu	a1,a0,5080 <wzerorange+0x2c>
    505c:	ff850793          	addi	a5,a0,-8
    5060:	00f5e863          	bltu	a1,a5,5070 <wzerorange+0x1c>
    5064:	fe052a23          	sw	zero,-12(a0)
    5068:	fe052823          	sw	zero,-16(a0)
    506c:	00050793          	mv	a5,a0
    5070:	ffc78713          	addi	a4,a5,-4
    5074:	00e5e463          	bltu	a1,a4,507c <wzerorange+0x28>
    5078:	fe07ac23          	sw	zero,-8(a5)
    507c:	00008067          	ret
    5080:	fe052e23          	sw	zero,-4(a0)
    5084:	fe052c23          	sw	zero,-8(a0)
    5088:	fe052a23          	sw	zero,-12(a0)
    508c:	fe052823          	sw	zero,-16(a0)
    5090:	01050513          	addi	a0,a0,16
    5094:	fc5ff06f          	j	5058 <wzerorange+0x4>

00005098 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l>:
    5098:	00200793          	li	a5,2
    509c:	02c7c063          	blt	a5,a2,50bc <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x24>
    50a0:	00c05c63          	blez	a2,50b8 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    50a4:	0005a703          	lw	a4,0(a1)
    50a8:	00e52023          	sw	a4,0(a0)
    50ac:	00f61663          	bne	a2,a5,50b8 <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x20>
    50b0:	0045a783          	lw	a5,4(a1)
    50b4:	00f52223          	sw	a5,4(a0)
    50b8:	00008067          	ret
    50bc:	0005a803          	lw	a6,0(a1)
    50c0:	0045a683          	lw	a3,4(a1)
    50c4:	0085a703          	lw	a4,8(a1)
    50c8:	00c58593          	addi	a1,a1,12
    50cc:	00c50513          	addi	a0,a0,12
    50d0:	ffd60613          	addi	a2,a2,-3
    50d4:	ff052a23          	sw	a6,-12(a0)
    50d8:	fed52c23          	sw	a3,-8(a0)
    50dc:	fee52e23          	sw	a4,-4(a0)
    50e0:	fbdff06f          	j	509c <_Z20l1_to_local_mem_copyPmU11rvtt_l1_ptrS_l+0x4>

000050e4 <exit>:
    50e4:	0000006f          	j	50e4 <exit>
