
/tmp/tt-disasm-s76bnc_h/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00006fa0 <_start>:
    6fa0:	ffb007b7          	lui	a5,0xffb00
    6fa4:	ffb00737          	lui	a4,0xffb00
    6fa8:	45078793          	addi	a5,a5,1104 # ffb00450 <__ldm_bss_end+0x10>
    6fac:	44070713          	addi	a4,a4,1088 # ffb00440 <__ldm_bss_end>
    6fb0:	00f76e63          	bltu	a4,a5,6fcc <.L2>

00006fb4 <.L3>:
    6fb4:	fe07ae23          	sw	zero,-4(a5)
    6fb8:	fe07ac23          	sw	zero,-8(a5)
    6fbc:	fe07aa23          	sw	zero,-12(a5)
    6fc0:	fe07a823          	sw	zero,-16(a5)
    6fc4:	01078793          	addi	a5,a5,16
    6fc8:	fef776e3          	bgeu	a4,a5,6fb4 <.L3>

00006fcc <.L2>:
    6fcc:	ff878693          	addi	a3,a5,-8
    6fd0:	10d76263          	bltu	a4,a3,70d4 <.L14>
    6fd4:	fe07aa23          	sw	zero,-12(a5)
    6fd8:	fe07a823          	sw	zero,-16(a5)

00006fdc <.L4>:
    6fdc:	ffc78693          	addi	a3,a5,-4
    6fe0:	00d76463          	bltu	a4,a3,6fe8 <.L5>
    6fe4:	fe07ac23          	sw	zero,-8(a5)

00006fe8 <.L5>:
    6fe8:	00007737          	lui	a4,0x7
    6fec:	ffb007b7          	lui	a5,0xffb00
    6ff0:	0dc70713          	addi	a4,a4,220 # 70dc <__kernel_data_lma>
    6ff4:	44078793          	addi	a5,a5,1088 # ffb00440 <__ldm_bss_end>
    6ff8:	06f70263          	beq	a4,a5,705c <.L7>
    6ffc:	ffb00637          	lui	a2,0xffb00
    7000:	44060613          	addi	a2,a2,1088 # ffb00440 <__ldm_bss_end>
    7004:	40f60633          	sub	a2,a2,a5
    7008:	00800593          	li	a1,8
    700c:	40265693          	srai	a3,a2,0x2
    7010:	02c5d863          	bge	a1,a2,7040 <.L8>
    7014:	00200813          	li	a6,2

00007018 <.L9>:
    7018:	00072503          	lw	a0,0(a4)
    701c:	00472583          	lw	a1,4(a4)
    7020:	00872603          	lw	a2,8(a4)
    7024:	00c70713          	addi	a4,a4,12
    7028:	00c78793          	addi	a5,a5,12
    702c:	ffd68693          	addi	a3,a3,-3
    7030:	fea7aa23          	sw	a0,-12(a5)
    7034:	feb7ac23          	sw	a1,-8(a5)
    7038:	fec7ae23          	sw	a2,-4(a5)
    703c:	fcd84ee3          	blt	a6,a3,7018 <.L9>

00007040 <.L8>:
    7040:	00d05e63          	blez	a3,705c <.L7>
    7044:	00072583          	lw	a1,0(a4)
    7048:	00200613          	li	a2,2
    704c:	00b7a023          	sw	a1,0(a5)
    7050:	00c69663          	bne	a3,a2,705c <.L7>
    7054:	00472703          	lw	a4,4(a4)
    7058:	00e7a223          	sw	a4,4(a5)

0000705c <.L7>:
    705c:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x6c00>
    7060:	08000693          	li	a3,128
    7064:	00271713          	slli	a4,a4,0x2
    7068:	37374783          	lbu	a5,883(a4)
    706c:	06070713          	addi	a4,a4,96
    7070:	00d78863          	beq	a5,a3,7080 <.L11>

00007074 <.L12>:
    7074:	0ff0000f          	fence
    7078:	31374783          	lbu	a5,787(a4)
    707c:	fed79ce3          	bne	a5,a3,7074 <.L12>

00007080 <.L11>:
    7080:	ffb126b7          	lui	a3,0xffb12
    7084:	1f46a703          	lw	a4,500(a3) # ffb121f4 <__stack_top+0x111f4>
    7088:	00001637          	lui	a2,0x1
    708c:	fff60613          	addi	a2,a2,-1 # fff <_start-0x5fa1>
    7090:	8878f5b7          	lui	a1,0x8878f
    7094:	00c77733          	and	a4,a4,a2
    7098:	000027b7          	lui	a5,0x2
    709c:	7ff78793          	addi	a5,a5,2047 # 27ff <_start-0x47a1>
    70a0:	00b76733          	or	a4,a4,a1
    70a4:	26e7a0a3          	sw	a4,609(a5)
    70a8:	1f06a703          	lw	a4,496(a3)
    70ac:	9878f5b7          	lui	a1,0x9878f
    70b0:	00000513          	li	a0,0
    70b4:	26e7a2a3          	sw	a4,613(a5)
    70b8:	1f46a703          	lw	a4,500(a3)
    70bc:	00c77733          	and	a4,a4,a2
    70c0:	00b76733          	or	a4,a4,a1
    70c4:	26e7a4a3          	sw	a4,617(a5)
    70c8:	1f06a703          	lw	a4,496(a3)
    70cc:	26e7a6a3          	sw	a4,621(a5)
    70d0:	00008067          	ret

000070d4 <.L14>:
    70d4:	00068793          	mv	a5,a3
    70d8:	f05ff06f          	j	6fdc <.L4>
