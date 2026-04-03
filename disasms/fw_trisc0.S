
/tmp/tt-disasm-gcpwqzdx/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00005a40 <_start>:
    5a40:	ffb001b7          	lui	gp,0xffb00
    5a44:	7f018193          	addi	gp,gp,2032 # ffb007f0 <__global_pointer$>
    5a48:	ffb01137          	lui	sp,0xffb01
    5a4c:	ff010113          	addi	sp,sp,-16 # ffb00ff0 <__global_pointer$+0x800>
    5a50:	00810513          	addi	a0,sp,8
    5a54:	00a12023          	sw	a0,0(sp)
    5a58:	00012223          	sw	zero,4(sp)
    5a5c:	00912423          	sw	s1,8(sp)
    5a60:	00012623          	sw	zero,12(sp)
    5a64:	00100513          	li	a0,1
    5a68:	00010593          	mv	a1,sp
    5a6c:	00000613          	li	a2,0
    5a70:	008000ef          	jal	5a78 <main>
    5a74:	3ac0006f          	j	5e20 <exit>

00005a78 <main>:
    5a78:	fb010113          	addi	sp,sp,-80
    5a7c:	04112623          	sw	ra,76(sp)
    5a80:	04812423          	sw	s0,72(sp)
    5a84:	04912223          	sw	s1,68(sp)
    5a88:	05212023          	sw	s2,64(sp)
    5a8c:	03312e23          	sw	s3,60(sp)
    5a90:	03412c23          	sw	s4,56(sp)
    5a94:	03512a23          	sw	s5,52(sp)
    5a98:	03612823          	sw	s6,48(sp)
    5a9c:	03712623          	sw	s7,44(sp)
    5aa0:	03812423          	sw	s8,40(sp)
    5aa4:	03912223          	sw	s9,36(sp)
    5aa8:	03a12023          	sw	s10,32(sp)
    5aac:	01b12e23          	sw	s11,28(sp)
    5ab0:	00200313          	li	t1,2
    5ab4:	7c032073          	csrs	0x7c0,t1
    5ab8:	00100313          	li	t1,1
    5abc:	01231313          	slli	t1,t1,0x12
    5ac0:	0ff0000f          	fence
    5ac4:	7c032073          	csrs	0x7c0,t1
    5ac8:	00200313          	li	t1,2
    5acc:	7c033073          	csrc	0x7c0,t1
    5ad0:	0ff0000f          	fence
    5ad4:	0ff0000f          	fence
    5ad8:	00800313          	li	t1,8
    5adc:	7c032073          	csrs	0x7c0,t1
    5ae0:	ffb007b7          	lui	a5,0xffb00
    5ae4:	ffb00737          	lui	a4,0xffb00
    5ae8:	01078793          	addi	a5,a5,16 # ffb00010 <crta_l1_base>
    5aec:	42070713          	addi	a4,a4,1056 # ffb00420 <__fw_export_ldm_end>
    5af0:	00f76e63          	bltu	a4,a5,5b0c <main+0x94>
    5af4:	fe07ae23          	sw	zero,-4(a5)
    5af8:	fe07ac23          	sw	zero,-8(a5)
    5afc:	fe07aa23          	sw	zero,-12(a5)
    5b00:	fe07a823          	sw	zero,-16(a5)
    5b04:	01078793          	addi	a5,a5,16
    5b08:	fef776e3          	bgeu	a4,a5,5af4 <main+0x7c>
    5b0c:	ff878693          	addi	a3,a5,-8
    5b10:	30d76463          	bltu	a4,a3,5e18 <.NO_CB170+0x178>
    5b14:	fe07aa23          	sw	zero,-12(a5)
    5b18:	fe07a823          	sw	zero,-16(a5)
    5b1c:	ffc78693          	addi	a3,a5,-4
    5b20:	00d76463          	bltu	a4,a3,5b28 <main+0xb0>
    5b24:	fe07ac23          	sw	zero,-8(a5)
    5b28:	0000c737          	lui	a4,0xc
    5b2c:	81018793          	addi	a5,gp,-2032 # ffb00000 <_ZN7ckernel14dest_offset_idE>
    5b30:	6b070713          	addi	a4,a4,1712 # c6b0 <__fw_export_text_end+0x6880>
    5b34:	06e78063          	beq	a5,a4,5b94 <main+0x11c>
    5b38:	81018613          	addi	a2,gp,-2032 # ffb00000 <_ZN7ckernel14dest_offset_idE>
    5b3c:	40f60633          	sub	a2,a2,a5
    5b40:	00800593          	li	a1,8
    5b44:	40265693          	srai	a3,a2,0x2
    5b48:	02c5d863          	bge	a1,a2,5b78 <main+0x100>
    5b4c:	00200813          	li	a6,2
    5b50:	00072503          	lw	a0,0(a4)
    5b54:	00472583          	lw	a1,4(a4)
    5b58:	00872603          	lw	a2,8(a4)
    5b5c:	00c70713          	addi	a4,a4,12
    5b60:	00c78793          	addi	a5,a5,12
    5b64:	ffd68693          	addi	a3,a3,-3
    5b68:	fea7aa23          	sw	a0,-12(a5)
    5b6c:	feb7ac23          	sw	a1,-8(a5)
    5b70:	fec7ae23          	sw	a2,-4(a5)
    5b74:	fcd84ee3          	blt	a6,a3,5b50 <main+0xd8>
    5b78:	00d05e63          	blez	a3,5b94 <main+0x11c>
    5b7c:	00072583          	lw	a1,0(a4)
    5b80:	00200613          	li	a2,2
    5b84:	00b7a023          	sw	a1,0(a5)
    5b88:	00c69663          	bne	a3,a2,5b94 <main+0x11c>
    5b8c:	00472703          	lw	a4,4(a4)
    5b90:	00e7a223          	sw	a4,4(a5)
    5b94:	ffe007b7          	lui	a5,0xffe00
    5b98:	10078713          	addi	a4,a5,256 # ffe00100 <__stack_top+0x2ff100>
    5b9c:	0007a023          	sw	zero,0(a5)
    5ba0:	00478793          	addi	a5,a5,4
    5ba4:	fee79ce3          	bne	a5,a4,5b9c <main+0x124>
    5ba8:	8201a623          	sw	zero,-2004(gp) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    5bac:	ffef07b7          	lui	a5,0xffef0
    5bb0:	2e07a423          	sw	zero,744(a5) # ffef02e8 <__stack_top+0x3ef2e8>
    5bb4:	ffb127b7          	lui	a5,0xffb12
    5bb8:	1f07a703          	lw	a4,496(a5) # ffb121f0 <__stack_top+0x111f0>
    5bbc:	1f87a683          	lw	a3,504(a5)
    5bc0:	25870593          	addi	a1,a4,600
    5bc4:	00e5b733          	sltu	a4,a1,a4
    5bc8:	00d706b3          	add	a3,a4,a3
    5bcc:	1f07a603          	lw	a2,496(a5)
    5bd0:	1f87a703          	lw	a4,504(a5)
    5bd4:	fed76ce3          	bltu	a4,a3,5bcc <main+0x154>
    5bd8:	00e69463          	bne	a3,a4,5be0 <main+0x168>
    5bdc:	feb668e3          	bltu	a2,a1,5bcc <main+0x154>
    5be0:	000017b7          	lui	a5,0x1
    5be4:	9a07c703          	lbu	a4,-1632(a5) # 9a0 <_start-0x50a0>
    5be8:	06078793          	addi	a5,a5,96
    5bec:	ffb68b37          	lui	s6,0xffb68
    5bf0:	83018413          	addi	s0,gp,-2000 # ffb00020 <cb_interface>
    5bf4:	028b0b13          	addi	s6,s6,40 # ffb68028 <__stack_top+0x67028>
    5bf8:	08000b93          	li	s7,128
    5bfc:	82e184a3          	sb	a4,-2007(gp) # ffb00019 <my_logical_x_>
    5c00:	9417c783          	lbu	a5,-1727(a5)
    5c04:	ffe80cb7          	lui	s9,0xffe80
    5c08:	00300c13          	li	s8,3
    5c0c:	82f18423          	sb	a5,-2008(gp) # ffb00018 <my_logical_y_>
    5c10:	060004a3          	sb	zero,105(zero) # 69 <_start-0x59d7>
    5c14:	06904783          	lbu	a5,105(zero) # 69 <_start-0x59d7>
    5c18:	01778c63          	beq	a5,s7,5c30 <main+0x1b8>
    5c1c:	06904783          	lbu	a5,105(zero) # 69 <_start-0x59d7>
    5c20:	17878863          	beq	a5,s8,5d90 <.NO_CB170+0xf0>
    5c24:	0ff0000f          	fence
    5c28:	06904783          	lbu	a5,105(zero) # 69 <_start-0x59d7>
    5c2c:	ff7798e3          	bne	a5,s7,5c1c <main+0x1a4>
    5c30:	06c02783          	lw	a5,108(zero) # 6c <_start-0x59d4>
    5c34:	00040713          	mv	a4,s0
    5c38:	20f7a7b3          	sh1add	a5,a5,a5
    5c3c:	00579793          	slli	a5,a5,0x5
    5c40:	07078e93          	addi	t4,a5,112
    5c44:	0707af03          	lw	t5,112(a5)
    5c48:	012ed783          	lhu	a5,18(t4)
    5c4c:	040ea583          	lw	a1,64(t4)
    5c50:	01e787b3          	add	a5,a5,t5
    5c54:	0580006f          	j	5cac <.NO_CB170+0xc>
    5c58:	0047a683          	lw	a3,4(a5)
    5c5c:	0007a603          	lw	a2,0(a5)
    5c60:	00c7a883          	lw	a7,12(a5)
    5c64:	0015d593          	srli	a1,a1,0x1
    5c68:	0015f293          	andi	t0,a1,1
    5c6c:	00072c23          	sw	zero,24(a4)
    5c70:	01078793          	addi	a5,a5,16
    5c74:	0046d693          	srli	a3,a3,0x4
    5c78:	00465613          	srli	a2,a2,0x4
    5c7c:	0048d893          	srli	a7,a7,0x4
    5c80:	00d72023          	sw	a3,0(a4)
    5c84:	00d606b3          	add	a3,a2,a3
    5c88:	00d72223          	sw	a3,4(a4)
    5c8c:	00c72823          	sw	a2,16(a4)
    5c90:	01172423          	sw	a7,8(a4)
    5c94:	02070713          	addi	a4,a4,32
    5c98:	fc0290e3          	bnez	t0,5c58 <main+0x1e0>
    5c9c:	00058e63          	beqz	a1,5cb8 <.NO_CB170+0x18>

00005ca0 <.NO_CB170>:
    5ca0:	01078793          	addi	a5,a5,16
    5ca4:	02070713          	addi	a4,a4,32
    5ca8:	0015d593          	srli	a1,a1,0x1
    5cac:	0015f293          	andi	t0,a1,1
    5cb0:	fa0294e3          	bnez	t0,5c58 <main+0x1e0>
    5cb4:	fe0596e3          	bnez	a1,5ca0 <.NO_CB170>
    5cb8:	014ed503          	lhu	a0,20(t4)
    5cbc:	046ec783          	lbu	a5,70(t4)
    5cc0:	02000693          	li	a3,32
    5cc4:	01e50533          	add	a0,a0,t5
    5cc8:	0ff7fd93          	zext.b	s11,a5
    5ccc:	c1018713          	addi	a4,gp,-1008 # ffb00400 <cb_interface+0x3e0>
    5cd0:	01f00893          	li	a7,31
    5cd4:	04d79a63          	bne	a5,a3,5d28 <.NO_CB170+0x88>
    5cd8:	0e00006f          	j	5db8 <.NO_CB170+0x118>
    5cdc:	00d72023          	sw	a3,0(a4)
    5ce0:	00c72223          	sw	a2,4(a4)
    5ce4:	01072823          	sw	a6,16(a4)
    5ce8:	00672a23          	sw	t1,20(a4)
    5cec:	01c72c23          	sw	t3,24(a4)
    5cf0:	01a72e23          	sw	s10,28(a4)
    5cf4:	00c6a803          	lw	a6,12(a3)
    5cf8:	010606b3          	add	a3,a2,a6
    5cfc:	02b87833          	remu	a6,a6,a1
    5d00:	410686b3          	sub	a3,a3,a6
    5d04:	00d7f463          	bgeu	a5,a3,5d0c <.NO_CB170+0x6c>
    5d08:	00078613          	mv	a2,a5
    5d0c:	00c72823          	sw	a2,16(a4)
    5d10:	00d72423          	sw	a3,8(a4)
    5d14:	00b72623          	sw	a1,12(a4)
    5d18:	00850513          	addi	a0,a0,8
    5d1c:	fe070713          	addi	a4,a4,-32
    5d20:	091d8c63          	beq	s11,a7,5db8 <.NO_CB170+0x118>
    5d24:	fff88893          	addi	a7,a7,-1
    5d28:	00052683          	lw	a3,0(a0)
    5d2c:	00452583          	lw	a1,4(a0)
    5d30:	0006af83          	lw	t6,0(a3)
    5d34:	0046ad03          	lw	s10,4(a3)
    5d38:	0086a603          	lw	a2,8(a3)
    5d3c:	00c6a783          	lw	a5,12(a3)
    5d40:	0106a803          	lw	a6,16(a3)
    5d44:	0146a303          	lw	t1,20(a3)
    5d48:	0186ae03          	lw	t3,24(a3)
    5d4c:	fff58793          	addi	a5,a1,-1
    5d50:	010787b3          	add	a5,a5,a6
    5d54:	40c787b3          	sub	a5,a5,a2
    5d58:	02b7f2b3          	remu	t0,a5,a1
    5d5c:	010e0393          	addi	t2,t3,16
    5d60:	405787b3          	sub	a5,a5,t0
    5d64:	00c787b3          	add	a5,a5,a2
    5d68:	f60f9ae3          	bnez	t6,5cdc <.NO_CB170+0x3c>
    5d6c:	00032e03          	lw	t3,0(t1)
    5d70:	00432303          	lw	t1,4(t1)
    5d74:	00d72023          	sw	a3,0(a4)
    5d78:	00c72223          	sw	a2,4(a4)
    5d7c:	01072823          	sw	a6,16(a4)
    5d80:	00772e23          	sw	t2,28(a4)
    5d84:	01c72a23          	sw	t3,20(a4)
    5d88:	00672c23          	sw	t1,24(a4)
    5d8c:	f69ff06f          	j	5cf4 <.NO_CB170+0x54>
    5d90:	ffb487b7          	lui	a5,0xffb48
    5d94:	02878793          	addi	a5,a5,40 # ffb48028 <__stack_top+0x47028>
    5d98:	00001737          	lui	a4,0x1
    5d9c:	0007a023          	sw	zero,0(a5)
    5da0:	fe07ac23          	sw	zero,-8(a5)
    5da4:	00e787b3          	add	a5,a5,a4
    5da8:	ff679ae3          	bne	a5,s6,5d9c <.NO_CB170+0xfc>
    5dac:	060004a3          	sb	zero,105(zero) # 69 <_start-0x59d7>
    5db0:	0ff0000f          	fence
    5db4:	e75ff06f          	j	5c28 <main+0x1b0>
    5db8:	01eed583          	lhu	a1,30(t4)
    5dbc:	8291c683          	lbu	a3,-2007(gp) # ffb00019 <my_logical_x_>
    5dc0:	020ed603          	lhu	a2,32(t4)
    5dc4:	05cec803          	lbu	a6,92(t4)
    5dc8:	8281c703          	lbu	a4,-2008(gp) # ffb00018 <my_logical_y_>
    5dcc:	05dec503          	lbu	a0,93(t4)
    5dd0:	034ea783          	lw	a5,52(t4)
    5dd4:	410686b3          	sub	a3,a3,a6
    5dd8:	01e585b3          	add	a1,a1,t5
    5ddc:	01e60633          	add	a2,a2,t5
    5de0:	01e787b3          	add	a5,a5,t5
    5de4:	40a70733          	sub	a4,a4,a0
    5de8:	80d18ea3          	sb	a3,-2019(gp) # ffb0000d <my_relative_x_>
    5dec:	82b1a223          	sw	a1,-2012(gp) # ffb00014 <rta_l1_base>
    5df0:	82c1a023          	sw	a2,-2016(gp) # ffb00010 <crta_l1_base>
    5df4:	80e18e23          	sb	a4,-2020(gp) # ffb0000c <my_relative_y_>
    5df8:	000780e7          	jalr	a5
    5dfc:	00012623          	sw	zero,12(sp)
    5e00:	00c12783          	lw	a5,12(sp)
    5e04:	00fca223          	sw	a5,4(s9) # ffe80004 <__stack_top+0x37f004>
    5e08:	004ca783          	lw	a5,4(s9)
    5e0c:	00f12623          	sw	a5,12(sp)
    5e10:	060004a3          	sb	zero,105(zero) # 69 <_start-0x59d7>
    5e14:	e01ff06f          	j	5c14 <main+0x19c>
    5e18:	00068793          	mv	a5,a3
    5e1c:	d01ff06f          	j	5b1c <main+0xa4>

00005e20 <exit>:
    5e20:	0000006f          	j	5e20 <exit>
