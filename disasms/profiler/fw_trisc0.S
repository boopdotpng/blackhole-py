
/tmp/tt-disasm-fw_trisc0-udks1a8u/out.elf:     file format elf32-littleriscv


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
    5a74:	5480006f          	j	5fbc <exit>

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
    5aec:	43870713          	addi	a4,a4,1080 # ffb00438 <__ldm_bss_end>
    5af0:	00f76e63          	bltu	a4,a5,5b0c <main+0x94>
    5af4:	fe07ae23          	sw	zero,-4(a5)
    5af8:	fe07ac23          	sw	zero,-8(a5)
    5afc:	fe07aa23          	sw	zero,-12(a5)
    5b00:	fe07a823          	sw	zero,-16(a5)
    5b04:	01078793          	addi	a5,a5,16
    5b08:	fef776e3          	bgeu	a4,a5,5af4 <main+0x7c>
    5b0c:	ff878693          	addi	a3,a5,-8
    5b10:	34d76a63          	bltu	a4,a3,5e64 <.NO_CB682+0x19c>
    5b14:	fe07aa23          	sw	zero,-12(a5)
    5b18:	fe07a823          	sw	zero,-16(a5)
    5b1c:	ffc78693          	addi	a3,a5,-4
    5b20:	00d76463          	bltu	a4,a3,5b28 <main+0xb0>
    5b24:	fe07ac23          	sw	zero,-8(a5)
    5b28:	0000c737          	lui	a4,0xc
    5b2c:	81018793          	addi	a5,gp,-2032 # ffb00000 <_ZN7ckernel14dest_offset_idE>
    5b30:	6b070713          	addi	a4,a4,1712 # c6b0 <__fw_export_text_end+0x66f0>
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
    5be0:	00001bb7          	lui	s7,0x1
    5be4:	9a0bc703          	lbu	a4,-1632(s7) # 9a0 <trisc.cc.5e4acb22+0x13f>
    5be8:	7ffb8413          	addi	s0,s7,2047
    5bec:	ffb68c37          	lui	s8,0xffb68
    5bf0:	24140413          	addi	s0,s0,577
    5bf4:	84818913          	addi	s2,gp,-1976 # ffb00038 <cb_interface>
    5bf8:	028c0c13          	addi	s8,s8,40 # ffb68028 <__stack_top+0x67028>
    5bfc:	08000c93          	li	s9,128
    5c00:	82e184a3          	sb	a4,-2007(gp) # ffb00019 <my_logical_x_>
    5c04:	9a1bc783          	lbu	a5,-1631(s7)
    5c08:	ffb124b7          	lui	s1,0xffb12
    5c0c:	82f18423          	sb	a5,-2008(gp) # ffb00018 <my_logical_y_>
    5c10:	060004a3          	sb	zero,105(zero) # 69 <trisc.cc.5e4acb22-0x7f8>
    5c14:	06904783          	lbu	a5,105(zero) # 69 <trisc.cc.5e4acb22-0x7f8>
    5c18:	01978e63          	beq	a5,s9,5c34 <main+0x1bc>
    5c1c:	06904703          	lbu	a4,105(zero) # 69 <trisc.cc.5e4acb22-0x7f8>
    5c20:	00300793          	li	a5,3
    5c24:	18f70a63          	beq	a4,a5,5db8 <.NO_CB682+0xf0>
    5c28:	0ff0000f          	fence
    5c2c:	06904783          	lbu	a5,105(zero) # 69 <trisc.cc.5e4acb22-0x7f8>
    5c30:	ff9796e3          	bne	a5,s9,5c1c <main+0x1a4>
    5c34:	238000ef          	jal	5e6c <_ZN15kernel_profiler13init_profilerEttt.constprop.0>
    5c38:	1f44a783          	lw	a5,500(s1) # ffb121f4 <__stack_top+0x111f4>
    5c3c:	fffb8613          	addi	a2,s7,-1
    5c40:	80e986b7          	lui	a3,0x80e98
    5c44:	00090713          	mv	a4,s2
    5c48:	00c7f7b3          	and	a5,a5,a2
    5c4c:	00d7e7b3          	or	a5,a5,a3
    5c50:	00f42823          	sw	a5,16(s0)
    5c54:	1f04a783          	lw	a5,496(s1)
    5c58:	00f42a23          	sw	a5,20(s0)
    5c5c:	06c02783          	lw	a5,108(zero) # 6c <trisc.cc.5e4acb22-0x7f5>
    5c60:	20f7a7b3          	sh1add	a5,a5,a5
    5c64:	00579793          	slli	a5,a5,0x5
    5c68:	07078e93          	addi	t4,a5,112
    5c6c:	0707af03          	lw	t5,112(a5)
    5c70:	012ed783          	lhu	a5,18(t4)
    5c74:	040ea583          	lw	a1,64(t4)
    5c78:	01e787b3          	add	a5,a5,t5
    5c7c:	0580006f          	j	5cd4 <.NO_CB682+0xc>
    5c80:	0047a683          	lw	a3,4(a5)
    5c84:	0007a603          	lw	a2,0(a5)
    5c88:	00c7a883          	lw	a7,12(a5)
    5c8c:	0015d593          	srli	a1,a1,0x1
    5c90:	0015f293          	andi	t0,a1,1
    5c94:	00072c23          	sw	zero,24(a4)
    5c98:	01078793          	addi	a5,a5,16
    5c9c:	0046d693          	srli	a3,a3,0x4
    5ca0:	00465613          	srli	a2,a2,0x4
    5ca4:	0048d893          	srli	a7,a7,0x4
    5ca8:	00d72023          	sw	a3,0(a4)
    5cac:	00d606b3          	add	a3,a2,a3
    5cb0:	00d72223          	sw	a3,4(a4)
    5cb4:	00c72823          	sw	a2,16(a4)
    5cb8:	01172423          	sw	a7,8(a4)
    5cbc:	02070713          	addi	a4,a4,32
    5cc0:	fc0290e3          	bnez	t0,5c80 <main+0x208>
    5cc4:	00058e63          	beqz	a1,5ce0 <.NO_CB682+0x18>

00005cc8 <.NO_CB682>:
    5cc8:	01078793          	addi	a5,a5,16
    5ccc:	02070713          	addi	a4,a4,32
    5cd0:	0015d593          	srli	a1,a1,0x1
    5cd4:	0015f293          	andi	t0,a1,1
    5cd8:	fa0294e3          	bnez	t0,5c80 <main+0x208>
    5cdc:	fe0596e3          	bnez	a1,5cc8 <.NO_CB682>
    5ce0:	014ed503          	lhu	a0,20(t4)
    5ce4:	046ec783          	lbu	a5,70(t4)
    5ce8:	02000693          	li	a3,32
    5cec:	01e50533          	add	a0,a0,t5
    5cf0:	0ff7fd93          	zext.b	s11,a5
    5cf4:	c2818713          	addi	a4,gp,-984 # ffb00418 <cb_interface+0x3e0>
    5cf8:	01f00893          	li	a7,31
    5cfc:	04d79a63          	bne	a5,a3,5d50 <.NO_CB682+0x88>
    5d00:	0dc0006f          	j	5ddc <.NO_CB682+0x114>
    5d04:	00d72023          	sw	a3,0(a4)
    5d08:	00c72223          	sw	a2,4(a4)
    5d0c:	01072823          	sw	a6,16(a4)
    5d10:	01c72a23          	sw	t3,20(a4)
    5d14:	00672c23          	sw	t1,24(a4)
    5d18:	01a72e23          	sw	s10,28(a4)
    5d1c:	00c6a803          	lw	a6,12(a3) # 80e9800c <__fw_export_text_end+0x80e9204c>
    5d20:	010606b3          	add	a3,a2,a6
    5d24:	02b87833          	remu	a6,a6,a1
    5d28:	410686b3          	sub	a3,a3,a6
    5d2c:	00d7f463          	bgeu	a5,a3,5d34 <.NO_CB682+0x6c>
    5d30:	00078613          	mv	a2,a5
    5d34:	00c72823          	sw	a2,16(a4)
    5d38:	00d72423          	sw	a3,8(a4)
    5d3c:	00b72623          	sw	a1,12(a4)
    5d40:	00850513          	addi	a0,a0,8
    5d44:	fe070713          	addi	a4,a4,-32
    5d48:	091d8a63          	beq	s11,a7,5ddc <.NO_CB682+0x114>
    5d4c:	fff88893          	addi	a7,a7,-1
    5d50:	00052683          	lw	a3,0(a0)
    5d54:	00452583          	lw	a1,4(a0)
    5d58:	0006af83          	lw	t6,0(a3)
    5d5c:	0046ad03          	lw	s10,4(a3)
    5d60:	0086a603          	lw	a2,8(a3)
    5d64:	00c6a783          	lw	a5,12(a3)
    5d68:	0106a803          	lw	a6,16(a3)
    5d6c:	0146ae03          	lw	t3,20(a3)
    5d70:	0186a303          	lw	t1,24(a3)
    5d74:	fff58793          	addi	a5,a1,-1
    5d78:	010787b3          	add	a5,a5,a6
    5d7c:	40c787b3          	sub	a5,a5,a2
    5d80:	02b7f2b3          	remu	t0,a5,a1
    5d84:	01030393          	addi	t2,t1,16
    5d88:	405787b3          	sub	a5,a5,t0
    5d8c:	00c787b3          	add	a5,a5,a2
    5d90:	f60f9ae3          	bnez	t6,5d04 <.NO_CB682+0x3c>
    5d94:	000e2303          	lw	t1,0(t3)
    5d98:	004e2e03          	lw	t3,4(t3)
    5d9c:	00d72023          	sw	a3,0(a4)
    5da0:	00c72223          	sw	a2,4(a4)
    5da4:	01072823          	sw	a6,16(a4)
    5da8:	00772e23          	sw	t2,28(a4)
    5dac:	00672a23          	sw	t1,20(a4)
    5db0:	01c72c23          	sw	t3,24(a4)
    5db4:	f69ff06f          	j	5d1c <.NO_CB682+0x54>
    5db8:	ffb487b7          	lui	a5,0xffb48
    5dbc:	02878793          	addi	a5,a5,40 # ffb48028 <__stack_top+0x47028>
    5dc0:	0007a023          	sw	zero,0(a5)
    5dc4:	fe07ac23          	sw	zero,-8(a5)
    5dc8:	017787b3          	add	a5,a5,s7
    5dcc:	ff879ae3          	bne	a5,s8,5dc0 <.NO_CB682+0xf8>
    5dd0:	060004a3          	sb	zero,105(zero) # 69 <trisc.cc.5e4acb22-0x7f8>
    5dd4:	0ff0000f          	fence
    5dd8:	e55ff06f          	j	5c2c <main+0x1b4>
    5ddc:	01eed583          	lhu	a1,30(t4)
    5de0:	020ed603          	lhu	a2,32(t4)
    5de4:	8291c683          	lbu	a3,-2007(gp) # ffb00019 <my_logical_x_>
    5de8:	05cec803          	lbu	a6,92(t4)
    5dec:	01e60633          	add	a2,a2,t5
    5df0:	05dec503          	lbu	a0,93(t4)
    5df4:	8281c703          	lbu	a4,-2008(gp) # ffb00018 <my_logical_y_>
    5df8:	034ea783          	lw	a5,52(t4)
    5dfc:	410686b3          	sub	a3,a3,a6
    5e00:	01e585b3          	add	a1,a1,t5
    5e04:	82c1a023          	sw	a2,-2016(gp) # ffb00010 <crta_l1_base>
    5e08:	01e787b3          	add	a5,a5,t5
    5e0c:	40a70733          	sub	a4,a4,a0
    5e10:	80d18ea3          	sb	a3,-2019(gp) # ffb0000d <my_relative_x_>
    5e14:	82b1a223          	sw	a1,-2012(gp) # ffb00014 <rta_l1_base>
    5e18:	80e18e23          	sb	a4,-2020(gp) # ffb0000c <my_relative_y_>
    5e1c:	000780e7          	jalr	a5
    5e20:	00012623          	sw	zero,12(sp)
    5e24:	00c12703          	lw	a4,12(sp)
    5e28:	ffe807b7          	lui	a5,0xffe80
    5e2c:	00e7a223          	sw	a4,4(a5) # ffe80004 <__stack_top+0x37f004>
    5e30:	0047a783          	lw	a5,4(a5)
    5e34:	fffb8693          	addi	a3,s7,-1
    5e38:	90e98737          	lui	a4,0x90e98
    5e3c:	00f12623          	sw	a5,12(sp)
    5e40:	060004a3          	sb	zero,105(zero) # 69 <trisc.cc.5e4acb22-0x7f8>
    5e44:	1f44a783          	lw	a5,500(s1)
    5e48:	00d7f7b3          	and	a5,a5,a3
    5e4c:	00e7e7b3          	or	a5,a5,a4
    5e50:	00f42c23          	sw	a5,24(s0)
    5e54:	1f04a783          	lw	a5,496(s1)
    5e58:	00f42e23          	sw	a5,28(s0)
    5e5c:	038000ef          	jal	5e94 <_ZN15kernel_profiler15finish_profilerEv>
    5e60:	db5ff06f          	j	5c14 <main+0x19c>
    5e64:	00068793          	mv	a5,a3
    5e68:	cb5ff06f          	j	5b1c <main+0xa4>

00005e6c <_ZN15kernel_profiler13init_profilerEttt.constprop.0>:
    5e6c:	83818713          	addi	a4,gp,-1992 # ffb00028 <_ZN15kernel_profiler6sumIDsE>
    5e70:	83018793          	addi	a5,gp,-2000 # ffb00020 <_ZN15kernel_profiler4sumsE>
    5e74:	00c00593          	li	a1,12
    5e78:	00072023          	sw	zero,0(a4) # 90e98000 <__fw_export_text_end+0x90e92040>
    5e7c:	00072223          	sw	zero,4(a4)
    5e80:	0007a023          	sw	zero,0(a5)
    5e84:	0007a223          	sw	zero,4(a5)
    5e88:	84b1a223          	sw	a1,-1980(gp) # ffb00034 <_ZN15kernel_profiler6wIndexE>
    5e8c:	8401a023          	sw	zero,-1984(gp) # ffb00030 <_ZN15kernel_profiler9stackSizeE>
    5e90:	00008067          	ret

00005e94 <_ZN15kernel_profiler15finish_profilerEv>:
    5e94:	83018793          	addi	a5,gp,-2000 # ffb00020 <_ZN15kernel_profiler4sumsE>
    5e98:	0007a683          	lw	a3,0(a5)
    5e9c:	8441a703          	lw	a4,-1980(gp) # ffb00034 <_ZN15kernel_profiler6wIndexE>
    5ea0:	08069263          	bnez	a3,5f24 <_ZN15kernel_profiler15finish_profilerEv+0x90>
    5ea4:	0047a883          	lw	a7,4(a5)
    5ea8:	10089263          	bnez	a7,5fac <_ZN15kernel_profiler15finish_profilerEv+0x118>
    5eac:	00377613          	andi	a2,a4,3
    5eb0:	04060c63          	beqz	a2,5f08 <_ZN15kernel_profiler15finish_profilerEv+0x74>
    5eb4:	00000813          	li	a6,0
    5eb8:	00000693          	li	a3,0
    5ebc:	1ff00513          	li	a0,511
    5ec0:	000015b7          	lui	a1,0x1
    5ec4:	800008b7          	lui	a7,0x80000
    5ec8:	20b747b3          	sh2add	a5,a4,a1
    5ecc:	7ff78793          	addi	a5,a5,2047
    5ed0:	02e56663          	bltu	a0,a4,5efc <_ZN15kernel_profiler15finish_profilerEv+0x68>
    5ed4:	2517a0a3          	sw	a7,577(a5)
    5ed8:	00270713          	addi	a4,a4,2
    5edc:	2407a2a3          	sw	zero,581(a5)
    5ee0:	00168693          	addi	a3,a3,1
    5ee4:	00377613          	andi	a2,a4,3
    5ee8:	02c6f663          	bgeu	a3,a2,5f14 <_ZN15kernel_profiler15finish_profilerEv+0x80>
    5eec:	20b747b3          	sh2add	a5,a4,a1
    5ef0:	00100813          	li	a6,1
    5ef4:	7ff78793          	addi	a5,a5,2047
    5ef8:	fce57ee3          	bgeu	a0,a4,5ed4 <_ZN15kernel_profiler15finish_profilerEv+0x40>
    5efc:	00168693          	addi	a3,a3,1
    5f00:	fcc6e4e3          	bltu	a3,a2,5ec8 <_ZN15kernel_profiler15finish_profilerEv+0x34>
    5f04:	00081863          	bnez	a6,5f14 <_ZN15kernel_profiler15finish_profilerEv+0x80>
    5f08:	000017b7          	lui	a5,0x1
    5f0c:	9ce7ae23          	sw	a4,-1572(a5) # 9dc <trisc.cc.5e4acb22+0x17b>
    5f10:	00008067          	ret
    5f14:	84e1a223          	sw	a4,-1980(gp) # ffb00034 <_ZN15kernel_profiler6wIndexE>
    5f18:	000017b7          	lui	a5,0x1
    5f1c:	9ce7ae23          	sw	a4,-1572(a5) # 9dc <trisc.cc.5e4acb22+0x17b>
    5f20:	00008067          	ret
    5f24:	1ff00813          	li	a6,511
    5f28:	f8e862e3          	bltu	a6,a4,5eac <_ZN15kernel_profiler15finish_profilerEv+0x18>
    5f2c:	83818513          	addi	a0,gp,-1992 # ffb00028 <_ZN15kernel_profiler6sumIDsE>
    5f30:	00052603          	lw	a2,0(a0)
    5f34:	000018b7          	lui	a7,0x1
    5f38:	0ffff5b7          	lui	a1,0xffff
    5f3c:	00c61613          	slli	a2,a2,0xc
    5f40:	00b67633          	and	a2,a2,a1
    5f44:	a0000e37          	lui	t3,0xa0000
    5f48:	a4088593          	addi	a1,a7,-1472 # a40 <trisc.cc.5e4acb22+0x1df>
    5f4c:	20b745b3          	sh2add	a1,a4,a1
    5f50:	01c66633          	or	a2,a2,t3
    5f54:	011585b3          	add	a1,a1,a7
    5f58:	00c5a023          	sw	a2,0(a1) # ffff000 <__fw_export_text_end+0xfff9040>
    5f5c:	0047a883          	lw	a7,4(a5)
    5f60:	00d5a223          	sw	a3,4(a1)
    5f64:	00270713          	addi	a4,a4,2
    5f68:	02088e63          	beqz	a7,5fa4 <_ZN15kernel_profiler15finish_profilerEv+0x110>
    5f6c:	02e86c63          	bltu	a6,a4,5fa4 <_ZN15kernel_profiler15finish_profilerEv+0x110>
    5f70:	00452783          	lw	a5,4(a0)
    5f74:	0ffff6b7          	lui	a3,0xffff
    5f78:	00001637          	lui	a2,0x1
    5f7c:	00c79793          	slli	a5,a5,0xc
    5f80:	00d7f7b3          	and	a5,a5,a3
    5f84:	a00005b7          	lui	a1,0xa0000
    5f88:	a4060693          	addi	a3,a2,-1472 # a40 <trisc.cc.5e4acb22+0x1df>
    5f8c:	20d746b3          	sh2add	a3,a4,a3
    5f90:	00b7e7b3          	or	a5,a5,a1
    5f94:	00c686b3          	add	a3,a3,a2
    5f98:	00f6a023          	sw	a5,0(a3) # ffff000 <__fw_export_text_end+0xfff9040>
    5f9c:	0116a223          	sw	a7,4(a3)
    5fa0:	00270713          	addi	a4,a4,2
    5fa4:	84e1a223          	sw	a4,-1980(gp) # ffb00034 <_ZN15kernel_profiler6wIndexE>
    5fa8:	f05ff06f          	j	5eac <_ZN15kernel_profiler15finish_profilerEv+0x18>
    5fac:	1ff00793          	li	a5,511
    5fb0:	eee7eee3          	bltu	a5,a4,5eac <_ZN15kernel_profiler15finish_profilerEv+0x18>
    5fb4:	83818513          	addi	a0,gp,-1992 # ffb00028 <_ZN15kernel_profiler6sumIDsE>
    5fb8:	fb9ff06f          	j	5f70 <_ZN15kernel_profiler15finish_profilerEv+0xdc>

00005fbc <exit>:
    5fbc:	0000006f          	j	5fbc <exit>
