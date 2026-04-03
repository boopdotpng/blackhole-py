
/tmp/tt-disasm-sk8x7c_l/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

000050f0 <_start>:
    50f0:	ffb017b7          	lui	a5,0xffb01
    50f4:	ffb01737          	lui	a4,0xffb01
    50f8:	8b078793          	addi	a5,a5,-1872 # ffb008b0 <__ldm_bss_end+0x10>
    50fc:	8a070713          	addi	a4,a4,-1888 # ffb008a0 <__ldm_bss_end>
    5100:	00f76e63          	bltu	a4,a5,511c <.L2>

00005104 <.L3>:
    5104:	fe07ae23          	sw	zero,-4(a5)
    5108:	fe07ac23          	sw	zero,-8(a5)
    510c:	fe07aa23          	sw	zero,-12(a5)
    5110:	fe07a823          	sw	zero,-16(a5)
    5114:	01078793          	addi	a5,a5,16
    5118:	fef776e3          	bgeu	a4,a5,5104 <.L3>

0000511c <.L2>:
    511c:	ff878693          	addi	a3,a5,-8
    5120:	12d76e63          	bltu	a4,a3,525c <.L14>
    5124:	fe07aa23          	sw	zero,-12(a5)
    5128:	fe07a823          	sw	zero,-16(a5)

0000512c <.L4>:
    512c:	ffc78693          	addi	a3,a5,-4
    5130:	00d76463          	bltu	a4,a3,5138 <.L5>
    5134:	fe07ac23          	sw	zero,-8(a5)

00005138 <.L5>:
    5138:	00005737          	lui	a4,0x5
    513c:	ffb017b7          	lui	a5,0xffb01
    5140:	26470713          	addi	a4,a4,612 # 5264 <__kernel_data_lma>
    5144:	8a078793          	addi	a5,a5,-1888 # ffb008a0 <__ldm_bss_end>
    5148:	06f70263          	beq	a4,a5,51ac <.L7>
    514c:	ffb01637          	lui	a2,0xffb01
    5150:	8a060613          	addi	a2,a2,-1888 # ffb008a0 <__ldm_bss_end>
    5154:	40f60633          	sub	a2,a2,a5
    5158:	00800593          	li	a1,8
    515c:	40265693          	srai	a3,a2,0x2
    5160:	02c5d863          	bge	a1,a2,5190 <.L8>
    5164:	00200813          	li	a6,2

00005168 <.L9>:
    5168:	00072503          	lw	a0,0(a4)
    516c:	00472583          	lw	a1,4(a4)
    5170:	00872603          	lw	a2,8(a4)
    5174:	00c70713          	addi	a4,a4,12
    5178:	00c78793          	addi	a5,a5,12
    517c:	ffd68693          	addi	a3,a3,-3
    5180:	fea7aa23          	sw	a0,-12(a5)
    5184:	feb7ac23          	sw	a1,-8(a5)
    5188:	fec7ae23          	sw	a2,-4(a5)
    518c:	fcd84ee3          	blt	a6,a3,5168 <.L9>

00005190 <.L8>:
    5190:	00d05e63          	blez	a3,51ac <.L7>
    5194:	00072583          	lw	a1,0(a4)
    5198:	00200613          	li	a2,2
    519c:	00b7a023          	sw	a1,0(a5)
    51a0:	00c69663          	bne	a3,a2,51ac <.L7>
    51a4:	00472703          	lw	a4,4(a4)
    51a8:	00e7a223          	sw	a4,4(a5)

000051ac <.L7>:
    51ac:	ffb307b7          	lui	a5,0xffb30
    51b0:	2087ae83          	lw	t4,520(a5) # ffb30208 <__stack_top+0x2e208>
    51b4:	2287a303          	lw	t1,552(a5)
    51b8:	2047a803          	lw	a6,516(a5)
    51bc:	2007a583          	lw	a1,512(a5)
    51c0:	22c7a683          	lw	a3,556(a5)
    51c4:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x4d50>
    51c8:	ffb007b7          	lui	a5,0xffb00
    51cc:	ffb00e37          	lui	t3,0xffb00
    51d0:	ffb008b7          	lui	a7,0xffb00
    51d4:	ffb00537          	lui	a0,0xffb00
    51d8:	ffb00637          	lui	a2,0xffb00
    51dc:	02d7ae23          	sw	a3,60(a5) # ffb0003c <noc_posted_writes_num_issued+0x4>
    51e0:	03de2823          	sw	t4,48(t3) # ffb00030 <noc_reads_num_issued+0x4>
    51e4:	0268a423          	sw	t1,40(a7) # ffb00028 <noc_nonposted_writes_num_issued+0x4>
    51e8:	03052023          	sw	a6,32(a0) # ffb00020 <noc_nonposted_writes_acked+0x4>
    51ec:	00b62c23          	sw	a1,24(a2) # ffb00018 <noc_nonposted_atomics_acked+0x4>
    51f0:	08000693          	li	a3,128
    51f4:	00271713          	slli	a4,a4,0x2
    51f8:	37374783          	lbu	a5,883(a4)
    51fc:	06070713          	addi	a4,a4,96
    5200:	00d78863          	beq	a5,a3,5210 <.L11>

00005204 <.L12>:
    5204:	0ff0000f          	fence
    5208:	31374783          	lbu	a5,787(a4)
    520c:	fed79ce3          	bne	a5,a3,5204 <.L12>

00005210 <.L11>:
    5210:	ffb126b7          	lui	a3,0xffb12
    5214:	1f46a703          	lw	a4,500(a3) # ffb121f4 <__stack_top+0x101f4>
    5218:	000017b7          	lui	a5,0x1
    521c:	fff78613          	addi	a2,a5,-1 # fff <_start-0x40f1>
    5220:	8d6b05b7          	lui	a1,0x8d6b0
    5224:	00c77733          	and	a4,a4,a2
    5228:	00b76733          	or	a4,a4,a1
    522c:	a6e7a023          	sw	a4,-1440(a5)
    5230:	1f06a703          	lw	a4,496(a3)
    5234:	9d6b05b7          	lui	a1,0x9d6b0
    5238:	00000513          	li	a0,0
    523c:	a6e7a223          	sw	a4,-1436(a5)
    5240:	1f46a703          	lw	a4,500(a3)
    5244:	00c77733          	and	a4,a4,a2
    5248:	00b76733          	or	a4,a4,a1
    524c:	a6e7a423          	sw	a4,-1432(a5)
    5250:	1f06a703          	lw	a4,496(a3)
    5254:	a6e7a623          	sw	a4,-1428(a5)
    5258:	00008067          	ret

0000525c <.L14>:
    525c:	00068793          	mv	a5,a3
    5260:	ecdff06f          	j	512c <.L4>
