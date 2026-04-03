
/tmp/tt-disasm-ld2lm4j6/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

000059c0 <_start>:
    59c0:	ffb017b7          	lui	a5,0xffb01
    59c4:	ffb01737          	lui	a4,0xffb01
    59c8:	89078793          	addi	a5,a5,-1904 # ffb00890 <__ldm_bss_end+0x10>
    59cc:	88070713          	addi	a4,a4,-1920 # ffb00880 <__ldm_bss_end>
    59d0:	00f76e63          	bltu	a4,a5,59ec <.L2>

000059d4 <.L3>:
    59d4:	fe07ae23          	sw	zero,-4(a5)
    59d8:	fe07ac23          	sw	zero,-8(a5)
    59dc:	fe07aa23          	sw	zero,-12(a5)
    59e0:	fe07a823          	sw	zero,-16(a5)
    59e4:	01078793          	addi	a5,a5,16
    59e8:	fef776e3          	bgeu	a4,a5,59d4 <.L3>

000059ec <.L2>:
    59ec:	ff878693          	addi	a3,a5,-8
    59f0:	10d76a63          	bltu	a4,a3,5b04 <.L14>
    59f4:	fe07aa23          	sw	zero,-12(a5)
    59f8:	fe07a823          	sw	zero,-16(a5)

000059fc <.L4>:
    59fc:	ffc78693          	addi	a3,a5,-4
    5a00:	00d76463          	bltu	a4,a3,5a08 <.L5>
    5a04:	fe07ac23          	sw	zero,-8(a5)

00005a08 <.L5>:
    5a08:	00006737          	lui	a4,0x6
    5a0c:	ffb017b7          	lui	a5,0xffb01
    5a10:	b0c70713          	addi	a4,a4,-1268 # 5b0c <__kernel_data_lma>
    5a14:	88078793          	addi	a5,a5,-1920 # ffb00880 <__ldm_bss_end>
    5a18:	06f70263          	beq	a4,a5,5a7c <.L7>
    5a1c:	ffb01637          	lui	a2,0xffb01
    5a20:	88060613          	addi	a2,a2,-1920 # ffb00880 <__ldm_bss_end>
    5a24:	40f60633          	sub	a2,a2,a5
    5a28:	00800593          	li	a1,8
    5a2c:	40265693          	srai	a3,a2,0x2
    5a30:	02c5d863          	bge	a1,a2,5a60 <.L8>
    5a34:	00200813          	li	a6,2

00005a38 <.L9>:
    5a38:	00072503          	lw	a0,0(a4)
    5a3c:	00472583          	lw	a1,4(a4)
    5a40:	00872603          	lw	a2,8(a4)
    5a44:	00c70713          	addi	a4,a4,12
    5a48:	00c78793          	addi	a5,a5,12
    5a4c:	ffd68693          	addi	a3,a3,-3
    5a50:	fea7aa23          	sw	a0,-12(a5)
    5a54:	feb7ac23          	sw	a1,-8(a5)
    5a58:	fec7ae23          	sw	a2,-4(a5)
    5a5c:	fcd84ee3          	blt	a6,a3,5a38 <.L9>

00005a60 <.L8>:
    5a60:	00d05e63          	blez	a3,5a7c <.L7>
    5a64:	00072583          	lw	a1,0(a4)
    5a68:	00200613          	li	a2,2
    5a6c:	00b7a023          	sw	a1,0(a5)
    5a70:	00c69663          	bne	a3,a2,5a7c <.L7>
    5a74:	00472703          	lw	a4,4(a4)
    5a78:	00e7a223          	sw	a4,4(a5)

00005a7c <.L7>:
    5a7c:	ffb207b7          	lui	a5,0xffb20
    5a80:	2087a703          	lw	a4,520(a5) # ffb20208 <__stack_top+0x1e208>
    5a84:	2287a703          	lw	a4,552(a5)
    5a88:	2047a703          	lw	a4,516(a5)
    5a8c:	2007a703          	lw	a4,512(a5)
    5a90:	22c7a783          	lw	a5,556(a5)
    5a94:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x5620>
    5a98:	08000693          	li	a3,128
    5a9c:	00271713          	slli	a4,a4,0x2
    5aa0:	37374783          	lbu	a5,883(a4)
    5aa4:	06070713          	addi	a4,a4,96
    5aa8:	00d78863          	beq	a5,a3,5ab8 <.L11>

00005aac <.L12>:
    5aac:	0ff0000f          	fence
    5ab0:	31374783          	lbu	a5,787(a4)
    5ab4:	fed79ce3          	bne	a5,a3,5aac <.L12>

00005ab8 <.L11>:
    5ab8:	ffb126b7          	lui	a3,0xffb12
    5abc:	1f46a703          	lw	a4,500(a3) # ffb121f4 <__stack_top+0x101f4>
    5ac0:	000017b7          	lui	a5,0x1
    5ac4:	fff78613          	addi	a2,a5,-1 # fff <_start-0x49c1>
    5ac8:	859fd5b7          	lui	a1,0x859fd
    5acc:	00c77733          	and	a4,a4,a2
    5ad0:	00b76733          	or	a4,a4,a1
    5ad4:	26e7a023          	sw	a4,608(a5)
    5ad8:	1f06a703          	lw	a4,496(a3)
    5adc:	959fd5b7          	lui	a1,0x959fd
    5ae0:	00000513          	li	a0,0
    5ae4:	26e7a223          	sw	a4,612(a5)
    5ae8:	1f46a703          	lw	a4,500(a3)
    5aec:	00c77733          	and	a4,a4,a2
    5af0:	00b76733          	or	a4,a4,a1
    5af4:	26e7a423          	sw	a4,616(a5)
    5af8:	1f06a703          	lw	a4,496(a3)
    5afc:	26e7a623          	sw	a4,620(a5)
    5b00:	00008067          	ret

00005b04 <.L14>:
    5b04:	00068793          	mv	a5,a3
    5b08:	ef5ff06f          	j	59fc <.L4>
