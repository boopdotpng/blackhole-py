
/tmp/tt-disasm-la7bjost/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00005fc0 <_start>:
    5fc0:	ffb007b7          	lui	a5,0xffb00
    5fc4:	ffb00737          	lui	a4,0xffb00
    5fc8:	45078793          	addi	a5,a5,1104 # ffb00450 <__ldm_bss_end+0x10>
    5fcc:	44070713          	addi	a4,a4,1088 # ffb00440 <__ldm_bss_end>
    5fd0:	00f76e63          	bltu	a4,a5,5fec <.L2>

00005fd4 <.L3>:
    5fd4:	fe07ae23          	sw	zero,-4(a5)
    5fd8:	fe07ac23          	sw	zero,-8(a5)
    5fdc:	fe07aa23          	sw	zero,-12(a5)
    5fe0:	fe07a823          	sw	zero,-16(a5)
    5fe4:	01078793          	addi	a5,a5,16
    5fe8:	fef776e3          	bgeu	a4,a5,5fd4 <.L3>

00005fec <.L2>:
    5fec:	ff878693          	addi	a3,a5,-8
    5ff0:	10d76863          	bltu	a4,a3,6100 <.L14>
    5ff4:	fe07aa23          	sw	zero,-12(a5)
    5ff8:	fe07a823          	sw	zero,-16(a5)

00005ffc <.L4>:
    5ffc:	ffc78693          	addi	a3,a5,-4
    6000:	00d76463          	bltu	a4,a3,6008 <.L5>
    6004:	fe07ac23          	sw	zero,-8(a5)

00006008 <.L5>:
    6008:	00006737          	lui	a4,0x6
    600c:	ffb007b7          	lui	a5,0xffb00
    6010:	10870713          	addi	a4,a4,264 # 6108 <__kernel_data_lma>
    6014:	44078793          	addi	a5,a5,1088 # ffb00440 <__ldm_bss_end>
    6018:	06f70263          	beq	a4,a5,607c <.L7>
    601c:	ffb00637          	lui	a2,0xffb00
    6020:	44060613          	addi	a2,a2,1088 # ffb00440 <__ldm_bss_end>
    6024:	40f60633          	sub	a2,a2,a5
    6028:	00800593          	li	a1,8
    602c:	40265693          	srai	a3,a2,0x2
    6030:	02c5d863          	bge	a1,a2,6060 <.L8>
    6034:	00200813          	li	a6,2

00006038 <.L9>:
    6038:	00072503          	lw	a0,0(a4)
    603c:	00472583          	lw	a1,4(a4)
    6040:	00872603          	lw	a2,8(a4)
    6044:	00c70713          	addi	a4,a4,12
    6048:	00c78793          	addi	a5,a5,12
    604c:	ffd68693          	addi	a3,a3,-3
    6050:	fea7aa23          	sw	a0,-12(a5)
    6054:	feb7ac23          	sw	a1,-8(a5)
    6058:	fec7ae23          	sw	a2,-4(a5)
    605c:	fcd84ee3          	blt	a6,a3,6038 <.L9>

00006060 <.L8>:
    6060:	00d05e63          	blez	a3,607c <.L7>
    6064:	00072583          	lw	a1,0(a4)
    6068:	00200613          	li	a2,2
    606c:	00b7a023          	sw	a1,0(a5)
    6070:	00c69663          	bne	a3,a2,607c <.L7>
    6074:	00472703          	lw	a4,4(a4)
    6078:	00e7a223          	sw	a4,4(a5)

0000607c <.L7>:
    607c:	ffb127b7          	lui	a5,0xffb12
    6080:	0607a423          	sw	zero,104(a5) # ffb12068 <__stack_top+0x11068>
    6084:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x5c20>
    6088:	08000693          	li	a3,128
    608c:	00271713          	slli	a4,a4,0x2
    6090:	37374783          	lbu	a5,883(a4)
    6094:	06070713          	addi	a4,a4,96
    6098:	00d78863          	beq	a5,a3,60a8 <.L11>

0000609c <.L12>:
    609c:	0ff0000f          	fence
    60a0:	31374783          	lbu	a5,787(a4)
    60a4:	fed79ce3          	bne	a5,a3,609c <.L12>

000060a8 <.L11>:
    60a8:	ffb126b7          	lui	a3,0xffb12
    60ac:	1f46a703          	lw	a4,500(a3) # ffb121f4 <__stack_top+0x111f4>
    60b0:	000017b7          	lui	a5,0x1
    60b4:	fff78613          	addi	a2,a5,-1 # fff <_start-0x4fc1>
    60b8:	8878f5b7          	lui	a1,0x8878f
    60bc:	7ff78793          	addi	a5,a5,2047
    60c0:	00c77733          	and	a4,a4,a2
    60c4:	24178793          	addi	a5,a5,577
    60c8:	00b76733          	or	a4,a4,a1
    60cc:	02e7a023          	sw	a4,32(a5)
    60d0:	1f06a703          	lw	a4,496(a3)
    60d4:	02e7a223          	sw	a4,36(a5)
    60d8:	4400001c          	ttzerosrc	0,0,1,3
    60dc:	1f46a703          	lw	a4,500(a3)
    60e0:	9878f5b7          	lui	a1,0x9878f
    60e4:	00000513          	li	a0,0
    60e8:	00c77733          	and	a4,a4,a2
    60ec:	00b76733          	or	a4,a4,a1
    60f0:	02e7a423          	sw	a4,40(a5)
    60f4:	1f06a703          	lw	a4,496(a3)
    60f8:	02e7a623          	sw	a4,44(a5)
    60fc:	00008067          	ret

00006100 <.L14>:
    6100:	00068793          	mv	a5,a3
    6104:	ef9ff06f          	j	5ffc <.L4>
