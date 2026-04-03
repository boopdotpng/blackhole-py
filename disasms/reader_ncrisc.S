
/tmp/tt-disasm-e6rnxok6/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00005880 <_start>:
    5880:	ffb017b7          	lui	a5,0xffb01
    5884:	ffb01737          	lui	a4,0xffb01
    5888:	88078793          	addi	a5,a5,-1920 # ffb00880 <__stack_base>
    588c:	87870713          	addi	a4,a4,-1928 # ffb00878 <__ldm_bss_end>
    5890:	00f76e63          	bltu	a4,a5,58ac <.L2>

00005894 <.L3>:
    5894:	fe07ae23          	sw	zero,-4(a5)
    5898:	fe07ac23          	sw	zero,-8(a5)
    589c:	fe07aa23          	sw	zero,-12(a5)
    58a0:	fe07a823          	sw	zero,-16(a5)
    58a4:	01078793          	addi	a5,a5,16
    58a8:	fef776e3          	bgeu	a4,a5,5894 <.L3>

000058ac <.L2>:
    58ac:	ff878693          	addi	a3,a5,-8
    58b0:	22d76263          	bltu	a4,a3,5ad4 <.L21>
    58b4:	fe07aa23          	sw	zero,-12(a5)
    58b8:	fe07a823          	sw	zero,-16(a5)

000058bc <.L4>:
    58bc:	ffc78693          	addi	a3,a5,-4
    58c0:	00d76463          	bltu	a4,a3,58c8 <.L5>
    58c4:	fe07ac23          	sw	zero,-8(a5)

000058c8 <.L5>:
    58c8:	00006737          	lui	a4,0x6
    58cc:	ffb017b7          	lui	a5,0xffb01
    58d0:	adc70713          	addi	a4,a4,-1316 # 5adc <__kernel_data_lma>
    58d4:	87078793          	addi	a5,a5,-1936 # ffb00870 <noc_reads_num_issued>
    58d8:	06f70263          	beq	a4,a5,593c <.L7>
    58dc:	ffb01637          	lui	a2,0xffb01
    58e0:	87060613          	addi	a2,a2,-1936 # ffb00870 <noc_reads_num_issued>
    58e4:	40f60633          	sub	a2,a2,a5
    58e8:	00800593          	li	a1,8
    58ec:	40265693          	srai	a3,a2,0x2
    58f0:	02c5d863          	bge	a1,a2,5920 <.L8>
    58f4:	00200813          	li	a6,2

000058f8 <.L9>:
    58f8:	00072503          	lw	a0,0(a4)
    58fc:	00472583          	lw	a1,4(a4)
    5900:	00872603          	lw	a2,8(a4)
    5904:	00c70713          	addi	a4,a4,12
    5908:	00c78793          	addi	a5,a5,12
    590c:	ffd68693          	addi	a3,a3,-3
    5910:	fea7aa23          	sw	a0,-12(a5)
    5914:	feb7ac23          	sw	a1,-8(a5)
    5918:	fec7ae23          	sw	a2,-4(a5)
    591c:	fcd84ee3          	blt	a6,a3,58f8 <.L9>

00005920 <.L8>:
    5920:	00d05e63          	blez	a3,593c <.L7>
    5924:	00072583          	lw	a1,0(a4)
    5928:	00200613          	li	a2,2
    592c:	00b7a023          	sw	a1,0(a5)
    5930:	00c69663          	bne	a3,a2,593c <.L7>
    5934:	00472703          	lw	a4,4(a4)
    5938:	00e7a223          	sw	a4,4(a5)

0000593c <.L7>:
    593c:	ffb207b7          	lui	a5,0xffb20
    5940:	2087a703          	lw	a4,520(a5) # ffb20208 <__stack_top+0x1e208>
    5944:	ffb018b7          	lui	a7,0xffb01
    5948:	2287a683          	lw	a3,552(a5)
    594c:	2047a683          	lw	a3,516(a5)
    5950:	87088893          	addi	a7,a7,-1936 # ffb00870 <noc_reads_num_issued>
    5954:	2007a683          	lw	a3,512(a5)
    5958:	22c7a783          	lw	a5,556(a5)
    595c:	00e8a023          	sw	a4,0(a7)
    5960:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x54e0>
    5964:	08000693          	li	a3,128
    5968:	00271713          	slli	a4,a4,0x2
    596c:	37374783          	lbu	a5,883(a4)
    5970:	06070713          	addi	a4,a4,96
    5974:	00d78863          	beq	a5,a3,5984 <.L14>

00005978 <.L11>:
    5978:	0ff0000f          	fence
    597c:	31374783          	lbu	a5,787(a4)
    5980:	fed79ce3          	bne	a5,a3,5978 <.L11>

00005984 <.L14>:
    5984:	ffb007b7          	lui	a5,0xffb00
    5988:	0387a783          	lw	a5,56(a5) # ffb00038 <rta_l1_base>
    598c:	0087a303          	lw	t1,8(a5)
    5990:	12030e63          	beqz	t1,5acc <.L36>
    5994:	0047a803          	lw	a6,4(a5)
    5998:	0007a383          	lw	t2,0(a5)
    599c:	ff010113          	addi	sp,sp,-16
    59a0:	ffb00637          	lui	a2,0xffb00
    59a4:	ffb00fb7          	lui	t6,0xffb00
    59a8:	ffb00f37          	lui	t5,0xffb00
    59ac:	92492eb7          	lui	t4,0x92492
    59b0:	00001e37          	lui	t3,0x1
    59b4:	00812623          	sw	s0,12(sp)
    59b8:	00912423          	sw	s1,8(sp)
    59bc:	01212223          	sw	s2,4(sp)
    59c0:	46460613          	addi	a2,a2,1124 # ffb00464 <cb_interface>
    59c4:	23cf8f93          	addi	t6,t6,572 # ffb0023c <bank_to_dram_offset>
    59c8:	040f0f13          	addi	t5,t5,64 # ffb00040 <dram_bank_to_noc_xy>
    59cc:	493e8e93          	addi	t4,t4,1171 # 92492493 <__kernel_data_lma+0x9248c9b7>
    59d0:	800e0e13          	addi	t3,t3,-2048 # 800 <_start-0x5080>
    59d4:	00680333          	add	t1,a6,t1
    59d8:	ffb485b7          	lui	a1,0xffb48
    59dc:	ffb216b7          	lui	a3,0xffb21
    59e0:	00100293          	li	t0,1
    59e4:	ffb20537          	lui	a0,0xffb20

000059e8 <.L19>:
    59e8:	0285a403          	lw	s0,40(a1) # ffb48028 <__stack_top+0x46028>
    59ec:	08044433          	zext.h	s0,s0

000059f0 <.L15>:
    59f0:	0ff0000f          	fence
    59f4:	0205a703          	lw	a4,32(a1)
    59f8:	00c62783          	lw	a5,12(a2)
    59fc:	00e787b3          	add	a5,a5,a4
    5a00:	0807c7b3          	zext.h	a5,a5
    5a04:	fe8786e3          	beq	a5,s0,59f0 <.L15>
    5a08:	03d837b3          	mulhu	a5,a6,t4
    5a0c:	01462483          	lw	s1,20(a2)
    5a10:	0027d793          	srli	a5,a5,0x2
    5a14:	00379413          	slli	s0,a5,0x3
    5a18:	40f40433          	sub	s0,s0,a5
    5a1c:	40880433          	sub	s0,a6,s0
    5a20:	00b79713          	slli	a4,a5,0xb
    5a24:	21f447b3          	sh2add	a5,s0,t6
    5a28:	21e42433          	sh1add	s0,s0,t5
    5a2c:	0007a903          	lw	s2,0(a5)
    5a30:	00045783          	lhu	a5,0(s0)
    5a34:	00770733          	add	a4,a4,t2
    5a38:	01270733          	add	a4,a4,s2
    5a3c:	00479413          	slli	s0,a5,0x4

00005a40 <.L16>:
    5a40:	8406a783          	lw	a5,-1984(a3) # ffb20840 <__stack_top+0x1e840>
    5a44:	fe079ee3          	bnez	a5,5a40 <.L16>
    5a48:	8096a623          	sw	s1,-2036(a3)
    5a4c:	80e6a023          	sw	a4,-2048(a3)
    5a50:	8006a223          	sw	zero,-2044(a3)
    5a54:	00445793          	srli	a5,s0,0x4
    5a58:	80f6a423          	sw	a5,-2040(a3)
    5a5c:	83c6a023          	sw	t3,-2016(a3)
    5a60:	8456a023          	sw	t0,-1984(a3)
    5a64:	0008a703          	lw	a4,0(a7)
    5a68:	00170713          	addi	a4,a4,1
    5a6c:	00e8a023          	sw	a4,0(a7)

00005a70 <.L17>:
    5a70:	20852783          	lw	a5,520(a0) # ffb20208 <__stack_top+0x1e208>
    5a74:	fee79ee3          	bne	a5,a4,5a70 <.L17>
    5a78:	0ff0000f          	fence
    5a7c:	0285a703          	lw	a4,40(a1)
    5a80:	01462403          	lw	s0,20(a2)
    5a84:	00862783          	lw	a5,8(a2)
    5a88:	00170713          	addi	a4,a4,1
    5a8c:	008787b3          	add	a5,a5,s0
    5a90:	00462403          	lw	s0,4(a2)
    5a94:	02e5a423          	sw	a4,40(a1)
    5a98:	00f62a23          	sw	a5,20(a2)
    5a9c:	00879863          	bne	a5,s0,5aac <.L18>
    5aa0:	00062703          	lw	a4,0(a2)
    5aa4:	40e787b3          	sub	a5,a5,a4
    5aa8:	00f62a23          	sw	a5,20(a2)

00005aac <.L18>:
    5aac:	00180813          	addi	a6,a6,1
    5ab0:	f2681ce3          	bne	a6,t1,59e8 <.L19>
    5ab4:	00c12403          	lw	s0,12(sp)
    5ab8:	00812483          	lw	s1,8(sp)
    5abc:	00412903          	lw	s2,4(sp)
    5ac0:	00000513          	li	a0,0
    5ac4:	01010113          	addi	sp,sp,16
    5ac8:	00008067          	ret

00005acc <.L36>:
    5acc:	00000513          	li	a0,0
    5ad0:	00008067          	ret

00005ad4 <.L21>:
    5ad4:	00068793          	mv	a5,a3
    5ad8:	de5ff06f          	j	58bc <.L4>
