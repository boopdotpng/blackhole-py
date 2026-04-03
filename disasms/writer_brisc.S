
/tmp/tt-disasm-8n68qqk5/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

000049d0 <_start>:
    49d0:	ffb017b7          	lui	a5,0xffb01
    49d4:	ffb01737          	lui	a4,0xffb01
    49d8:	89078793          	addi	a5,a5,-1904 # ffb00890 <__ldm_bss_end+0x10>
    49dc:	88070713          	addi	a4,a4,-1920 # ffb00880 <__ldm_bss_end>
    49e0:	00f76e63          	bltu	a4,a5,49fc <.L2>

000049e4 <.L3>:
    49e4:	fe07ae23          	sw	zero,-4(a5)
    49e8:	fe07ac23          	sw	zero,-8(a5)
    49ec:	fe07aa23          	sw	zero,-12(a5)
    49f0:	fe07a823          	sw	zero,-16(a5)
    49f4:	01078793          	addi	a5,a5,16
    49f8:	fef776e3          	bgeu	a4,a5,49e4 <.L3>

000049fc <.L2>:
    49fc:	ff878693          	addi	a3,a5,-8
    4a00:	24d76c63          	bltu	a4,a3,4c58 <.L21>
    4a04:	fe07aa23          	sw	zero,-12(a5)
    4a08:	fe07a823          	sw	zero,-16(a5)

00004a0c <.L4>:
    4a0c:	ffc78693          	addi	a3,a5,-4
    4a10:	00d76463          	bltu	a4,a3,4a18 <.L5>
    4a14:	fe07ac23          	sw	zero,-8(a5)

00004a18 <.L5>:
    4a18:	00005737          	lui	a4,0x5
    4a1c:	ffb017b7          	lui	a5,0xffb01
    4a20:	c6070713          	addi	a4,a4,-928 # 4c60 <__kernel_data_lma>
    4a24:	88078793          	addi	a5,a5,-1920 # ffb00880 <__ldm_bss_end>
    4a28:	06f70263          	beq	a4,a5,4a8c <.L7>
    4a2c:	ffb01637          	lui	a2,0xffb01
    4a30:	88060613          	addi	a2,a2,-1920 # ffb00880 <__ldm_bss_end>
    4a34:	40f60633          	sub	a2,a2,a5
    4a38:	00800593          	li	a1,8
    4a3c:	40265693          	srai	a3,a2,0x2
    4a40:	02c5d863          	bge	a1,a2,4a70 <.L8>
    4a44:	00200813          	li	a6,2

00004a48 <.L9>:
    4a48:	00072503          	lw	a0,0(a4)
    4a4c:	00472583          	lw	a1,4(a4)
    4a50:	00872603          	lw	a2,8(a4)
    4a54:	00c70713          	addi	a4,a4,12
    4a58:	00c78793          	addi	a5,a5,12
    4a5c:	ffd68693          	addi	a3,a3,-3
    4a60:	fea7aa23          	sw	a0,-12(a5)
    4a64:	feb7ac23          	sw	a1,-8(a5)
    4a68:	fec7ae23          	sw	a2,-4(a5)
    4a6c:	fcd84ee3          	blt	a6,a3,4a48 <.L9>

00004a70 <.L8>:
    4a70:	00d05e63          	blez	a3,4a8c <.L7>
    4a74:	00072583          	lw	a1,0(a4)
    4a78:	00200613          	li	a2,2
    4a7c:	00b7a023          	sw	a1,0(a5)
    4a80:	00c69663          	bne	a3,a2,4a8c <.L7>
    4a84:	00472703          	lw	a4,4(a4)
    4a88:	00e7a223          	sw	a4,4(a5)

00004a8c <.L7>:
    4a8c:	ffb307b7          	lui	a5,0xffb30
    4a90:	2087ae83          	lw	t4,520(a5) # ffb30208 <__stack_top+0x2e208>
    4a94:	2287a303          	lw	t1,552(a5)
    4a98:	2047a503          	lw	a0,516(a5)
    4a9c:	2007a583          	lw	a1,512(a5)
    4aa0:	22c7a603          	lw	a2,556(a5)
    4aa4:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x4630>
    4aa8:	ffb007b7          	lui	a5,0xffb00
    4aac:	02b7a423          	sw	a1,40(a5) # ffb00028 <noc_nonposted_atomics_acked+0x4>
    4ab0:	ffb008b7          	lui	a7,0xffb00
    4ab4:	ffb00837          	lui	a6,0xffb00
    4ab8:	ffb006b7          	lui	a3,0xffb00
    4abc:	ffb00e37          	lui	t3,0xffb00
    4ac0:	03488893          	addi	a7,a7,52 # ffb00034 <noc_nonposted_writes_num_issued>
    4ac4:	02c80813          	addi	a6,a6,44 # ffb0002c <noc_nonposted_writes_acked>
    4ac8:	02c6a023          	sw	a2,32(a3) # ffb00020 <noc_posted_writes_num_issued+0x4>
    4acc:	05de2023          	sw	t4,64(t3) # ffb00040 <noc_reads_num_issued+0x4>
    4ad0:	0068a223          	sw	t1,4(a7)
    4ad4:	00271713          	slli	a4,a4,0x2
    4ad8:	37374783          	lbu	a5,883(a4)
    4adc:	00a82223          	sw	a0,4(a6)
    4ae0:	08000693          	li	a3,128
    4ae4:	06070713          	addi	a4,a4,96
    4ae8:	00d78863          	beq	a5,a3,4af8 <.L14>

00004aec <.L11>:
    4aec:	0ff0000f          	fence
    4af0:	31374783          	lbu	a5,787(a4)
    4af4:	fed79ce3          	bne	a5,a3,4aec <.L11>

00004af8 <.L14>:
    4af8:	ffb007b7          	lui	a5,0xffb00
    4afc:	0187a783          	lw	a5,24(a5) # ffb00018 <rta_l1_base>
    4b00:	0087a303          	lw	t1,8(a5)
    4b04:	14030663          	beqz	t1,4c50 <.L36>
    4b08:	ff010113          	addi	sp,sp,-16
    4b0c:	0047a503          	lw	a0,4(a5)
    4b10:	00812623          	sw	s0,12(sp)
    4b14:	0007a403          	lw	s0,0(a5)
    4b18:	ffb005b7          	lui	a1,0xffb00
    4b1c:	ffb002b7          	lui	t0,0xffb00
    4b20:	ffb00fb7          	lui	t6,0xffb00
    4b24:	92492f37          	lui	t5,0x92492
    4b28:	00002eb7          	lui	t4,0x2
    4b2c:	00001e37          	lui	t3,0x1
    4b30:	00912423          	sw	s1,8(sp)
    4b34:	01212223          	sw	s2,4(sp)
    4b38:	01312023          	sw	s3,0(sp)
    4b3c:	04858593          	addi	a1,a1,72 # ffb00048 <cb_interface>
    4b40:	64428293          	addi	t0,t0,1604 # ffb00644 <bank_to_dram_offset>
    4b44:	448f8f93          	addi	t6,t6,1096 # ffb00448 <dram_bank_to_noc_xy>
    4b48:	493f0f13          	addi	t5,t5,1171 # 92492493 <__kernel_data_lma+0x9248d833>
    4b4c:	00650333          	add	t1,a0,t1
    4b50:	092e8e93          	addi	t4,t4,146 # 2092 <_start-0x293e>
    4b54:	800e0e13          	addi	t3,t3,-2048 # 800 <_start-0x41d0>
    4b58:	ffb58637          	lui	a2,0xffb58
    4b5c:	ffb30737          	lui	a4,0xffb30
    4b60:	00100393          	li	t2,1

00004b64 <.L19>:
    4b64:	02062683          	lw	a3,32(a2) # ffb58020 <__stack_top+0x56020>
    4b68:	0806c6b3          	zext.h	a3,a3

00004b6c <.L15>:
    4b6c:	02862783          	lw	a5,40(a2)
    4b70:	0807c7b3          	zext.h	a5,a5
    4b74:	fed78ce3          	beq	a5,a3,4b6c <.L15>
    4b78:	03e537b3          	mulhu	a5,a0,t5
    4b7c:	2105a903          	lw	s2,528(a1)
    4b80:	0027d793          	srli	a5,a5,0x2
    4b84:	00379493          	slli	s1,a5,0x3
    4b88:	40f484b3          	sub	s1,s1,a5
    4b8c:	409504b3          	sub	s1,a0,s1
    4b90:	00b79693          	slli	a3,a5,0xb
    4b94:	2054c7b3          	sh2add	a5,s1,t0
    4b98:	21f4a4b3          	sh1add	s1,s1,t6
    4b9c:	0007a983          	lw	s3,0(a5)
    4ba0:	00e4d783          	lhu	a5,14(s1)
    4ba4:	008686b3          	add	a3,a3,s0
    4ba8:	013686b3          	add	a3,a3,s3
    4bac:	00479493          	slli	s1,a5,0x4

00004bb0 <.L16>:
    4bb0:	04072783          	lw	a5,64(a4) # ffb30040 <__stack_top+0x2e040>
    4bb4:	fe079ee3          	bnez	a5,4bb0 <.L16>
    4bb8:	01d72e23          	sw	t4,28(a4)
    4bbc:	01272023          	sw	s2,0(a4)
    4bc0:	00d72623          	sw	a3,12(a4)
    4bc4:	00072823          	sw	zero,16(a4)
    4bc8:	0044d793          	srli	a5,s1,0x4
    4bcc:	00482683          	lw	a3,4(a6)
    4bd0:	0048a483          	lw	s1,4(a7)
    4bd4:	00f72a23          	sw	a5,20(a4)
    4bd8:	03c72023          	sw	t3,32(a4)
    4bdc:	04772023          	sw	t2,64(a4)
    4be0:	00148793          	addi	a5,s1,1
    4be4:	00168693          	addi	a3,a3,1
    4be8:	00f8a223          	sw	a5,4(a7)
    4bec:	00d82223          	sw	a3,4(a6)

00004bf0 <.L17>:
    4bf0:	20472783          	lw	a5,516(a4)
    4bf4:	fed79ee3          	bne	a5,a3,4bf0 <.L17>
    4bf8:	0ff0000f          	fence
    4bfc:	02062683          	lw	a3,32(a2)
    4c00:	2105a483          	lw	s1,528(a1)
    4c04:	2085a783          	lw	a5,520(a1)
    4c08:	00168693          	addi	a3,a3,1
    4c0c:	009787b3          	add	a5,a5,s1
    4c10:	2045a483          	lw	s1,516(a1)
    4c14:	02d62023          	sw	a3,32(a2)
    4c18:	20f5a823          	sw	a5,528(a1)
    4c1c:	00979863          	bne	a5,s1,4c2c <.L18>
    4c20:	2005a683          	lw	a3,512(a1)
    4c24:	40d787b3          	sub	a5,a5,a3
    4c28:	20f5a823          	sw	a5,528(a1)

00004c2c <.L18>:
    4c2c:	00150513          	addi	a0,a0,1
    4c30:	f2651ae3          	bne	a0,t1,4b64 <.L19>
    4c34:	00c12403          	lw	s0,12(sp)
    4c38:	00812483          	lw	s1,8(sp)
    4c3c:	00412903          	lw	s2,4(sp)
    4c40:	00012983          	lw	s3,0(sp)
    4c44:	00000513          	li	a0,0
    4c48:	01010113          	addi	sp,sp,16
    4c4c:	00008067          	ret

00004c50 <.L36>:
    4c50:	00000513          	li	a0,0
    4c54:	00008067          	ret

00004c58 <.L21>:
    4c58:	00068793          	mv	a5,a3
    4c5c:	db1ff06f          	j	4a0c <.L4>
