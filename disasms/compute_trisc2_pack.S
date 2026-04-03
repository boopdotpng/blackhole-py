
/tmp/tt-disasm-f9w5_0er/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00006e00 <_start>:
    6e00:	fc010113          	addi	sp,sp,-64
    6e04:	03212a23          	sw	s2,52(sp)
    6e08:	03312823          	sw	s3,48(sp)
    6e0c:	ffb007b7          	lui	a5,0xffb00
    6e10:	ffb00737          	lui	a4,0xffb00
    6e14:	43078793          	addi	a5,a5,1072 # ffb00430 <__ldm_bss_end+0x10>
    6e18:	42070713          	addi	a4,a4,1056 # ffb00420 <__ldm_bss_end>
    6e1c:	00f76e63          	bltu	a4,a5,6e38 <.L2>

00006e20 <.L3>:
    6e20:	fe07ae23          	sw	zero,-4(a5)
    6e24:	fe07ac23          	sw	zero,-8(a5)
    6e28:	fe07aa23          	sw	zero,-12(a5)
    6e2c:	fe07a823          	sw	zero,-16(a5)
    6e30:	01078793          	addi	a5,a5,16
    6e34:	fef776e3          	bgeu	a4,a5,6e20 <.L3>

00006e38 <.L2>:
    6e38:	ff878693          	addi	a3,a5,-8
    6e3c:	44d76a63          	bltu	a4,a3,7290 <.L21>
    6e40:	fe07aa23          	sw	zero,-12(a5)
    6e44:	fe07a823          	sw	zero,-16(a5)

00006e48 <.L4>:
    6e48:	ffc78693          	addi	a3,a5,-4
    6e4c:	00d76463          	bltu	a4,a3,6e54 <.L5>
    6e50:	fe07ac23          	sw	zero,-8(a5)

00006e54 <.L5>:
    6e54:	00007737          	lui	a4,0x7
    6e58:	ffb007b7          	lui	a5,0xffb00
    6e5c:	29870713          	addi	a4,a4,664 # 7298 <__kernel_data_lma>
    6e60:	42078793          	addi	a5,a5,1056 # ffb00420 <__ldm_bss_end>
    6e64:	06f70263          	beq	a4,a5,6ec8 <.L7>
    6e68:	ffb00637          	lui	a2,0xffb00
    6e6c:	42060613          	addi	a2,a2,1056 # ffb00420 <__ldm_bss_end>
    6e70:	40f60633          	sub	a2,a2,a5
    6e74:	00800593          	li	a1,8
    6e78:	40265693          	srai	a3,a2,0x2
    6e7c:	02c5d863          	bge	a1,a2,6eac <.L8>
    6e80:	00200813          	li	a6,2

00006e84 <.L9>:
    6e84:	00072503          	lw	a0,0(a4)
    6e88:	00472583          	lw	a1,4(a4)
    6e8c:	00872603          	lw	a2,8(a4)
    6e90:	00c70713          	addi	a4,a4,12
    6e94:	00c78793          	addi	a5,a5,12
    6e98:	ffd68693          	addi	a3,a3,-3
    6e9c:	fea7aa23          	sw	a0,-12(a5)
    6ea0:	feb7ac23          	sw	a1,-8(a5)
    6ea4:	fec7ae23          	sw	a2,-4(a5)
    6ea8:	fcd84ee3          	blt	a6,a3,6e84 <.L9>

00006eac <.L8>:
    6eac:	00d05e63          	blez	a3,6ec8 <.L7>
    6eb0:	00072583          	lw	a1,0(a4)
    6eb4:	00200613          	li	a2,2
    6eb8:	00b7a023          	sw	a1,0(a5)
    6ebc:	00c69663          	bne	a3,a2,6ec8 <.L7>
    6ec0:	00472703          	lw	a4,4(a4)
    6ec4:	00e7a223          	sw	a4,4(a5)

00006ec8 <.L7>:
    6ec8:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x6a60>
    6ecc:	08000693          	li	a3,128
    6ed0:	00271713          	slli	a4,a4,0x2
    6ed4:	37374783          	lbu	a5,883(a4)
    6ed8:	06070713          	addi	a4,a4,96
    6edc:	00d78863          	beq	a5,a3,6eec <.L13>

00006ee0 <.L11>:
    6ee0:	0ff0000f          	fence
    6ee4:	31374783          	lbu	a5,787(a4)
    6ee8:	fed79ce3          	bne	a5,a3,6ee0 <.L11>

00006eec <.L13>:
    6eec:	ffb007b7          	lui	a5,0xffb00
    6ef0:	ffb00737          	lui	a4,0xffb00
    6ef4:	0147a783          	lw	a5,20(a5) # ffb00014 <rta_l1_base>
    6ef8:	ffb008b7          	lui	a7,0xffb00
    6efc:	01c72703          	lw	a4,28(a4) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    6f00:	02088893          	addi	a7,a7,32 # ffb00020 <cb_interface>
    6f04:	0007a903          	lw	s2,0(a5)
    6f08:	2088ae03          	lw	t3,520(a7)
    6f0c:	ffef07b7          	lui	a5,0xffef0
    6f10:	00070463          	beqz	a4,6f18 <.L12>
    6f14:	38078793          	addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>

00006f18 <.L12>:
    6f18:	45000fb7          	lui	t6,0x45000
    6f1c:	ffe406b7          	lui	a3,0xffe40
    6f20:	00068693          	mv	a3,a3
    6f24:	038f8f13          	addi	t5,t6,56 # 45000038 <__kernel_data_lma+0x44ff8da0>
    6f28:	45002837          	lui	a6,0x45002
    6f2c:	01e6a023          	sw	t5,0(a3) # ffe40000 <__instrn_buffer>
    6f30:	03980813          	addi	a6,a6,57 # 45002039 <__kernel_data_lma+0x44ffada1>
    6f34:	45020637          	lui	a2,0x45020
    6f38:	0106a023          	sw	a6,0(a3)
    6f3c:	03a60e93          	addi	t4,a2,58 # 4502003a <__kernel_data_lma+0x45018da2>
    6f40:	45080537          	lui	a0,0x45080
    6f44:	01d6a023          	sw	t4,0(a3)
    6f48:	03b50513          	addi	a0,a0,59 # 4508003b <__kernel_data_lma+0x45078da3>
    6f4c:	00a6a023          	sw	a0,0(a3)
    6f50:	89000006          	ttstallwait	128,1
    6f54:	c0700032          	ttwrcfg	28,0,12
    6f58:	c0740036          	ttwrcfg	29,0,13
    6f5c:	08000000          	ttnop
    6f60:	08000000          	ttnop
    6f64:	80000002          	ttatgetm	0
    6f68:	b61e1737          	lui	a4,0xb61e1
    6f6c:	a0170713          	addi	a4,a4,-1535 # b61e0a01 <__kernel_data_lma+0xb61d9769>
    6f70:	00e6a023          	sw	a4,0(a3)
    6f74:	b3fc0737          	lui	a4,0xb3fc0
    6f78:	00270713          	addi	a4,a4,2 # b3fc0002 <__kernel_data_lma+0xb3fb8d6a>
    6f7c:	00e6a023          	sw	a4,0(a3)
    6f80:	b4ff0737          	lui	a4,0xb4ff0
    6f84:	00270713          	addi	a4,a4,2 # b4ff0002 <__kernel_data_lma+0xb4fe8d6a>
    6f88:	00e6a023          	sw	a4,0(a3)
    6f8c:	b53f0737          	lui	a4,0xb53f0
    6f90:	00270713          	addi	a4,a4,2 # b53f0002 <__kernel_data_lma+0xb53e8d6a>
    6f94:	00e6a023          	sw	a4,0(a3)
    6f98:	84000002          	ttatrelm	0
    6f9c:	000405b7          	lui	a1,0x40
    6fa0:	10b7a823          	sw	a1,272(a5)
    6fa4:	55100713          	li	a4,1361
    6fa8:	10e7ac23          	sw	a4,280(a5)
    6fac:	0407a423          	sw	zero,72(a5)
    6fb0:	ffe00737          	lui	a4,0xffe00
    6fb4:	0cb72823          	sw	a1,208(a4) # ffe000d0 <__stack_top+0x2ff0d0>
    6fb8:	00012423          	sw	zero,8(sp)
    6fbc:	0d072283          	lw	t0,208(a4)
    6fc0:	000015b7          	lui	a1,0x1
    6fc4:	00010337          	lui	t1,0x10
    6fc8:	fff30313          	addi	t1,t1,-1 # ffff <__kernel_data_lma+0x8d67>
    6fcc:	00512423          	sw	t0,8(sp)
    6fd0:	06b7a823          	sw	a1,112(a5)
    6fd4:	06b7aa23          	sw	a1,116(a5)
    6fd8:	06b7ac23          	sw	a1,120(a5)
    6fdc:	06b7ae23          	sw	a1,124(a5)
    6fe0:	0667a023          	sw	t1,96(a5)
    6fe4:	0407a823          	sw	zero,80(a5)
    6fe8:	05c72023          	sw	t3,64(a4)
    6fec:	04072223          	sw	zero,68(a4)
    6ff0:	04072423          	sw	zero,72(a4)
    6ff4:	04072623          	sw	zero,76(a4)
    6ff8:	00012223          	sw	zero,4(sp)
    6ffc:	04c72783          	lw	a5,76(a4)
    7000:	5e8045b7          	lui	a1,0x5e804
    7004:	c0058593          	addi	a1,a1,-1024 # 5e803c00 <__kernel_data_lma+0x5e7fc968>
    7008:	00f12223          	sw	a5,4(sp)
    700c:	00b6a023          	sw	a1,0(a3)
    7010:	c8940412          	ttsetc16	37,260
    7014:	c898a082          	ttsetc16	38,10272
    7018:	c89c4482          	ttsetc16	39,4384
    701c:	00012623          	sw	zero,12(sp)
    7020:	00c12783          	lw	a5,12(sp)
    7024:	ffe80737          	lui	a4,0xffe80
    7028:	00f72423          	sw	a5,8(a4) # ffe80008 <__instrn_buffer+0x40008>
    702c:	00872283          	lw	t0,8(a4)
    7030:	ffb807b7          	lui	a5,0xffb80
    7034:	00400e13          	li	t3,4
    7038:	02000337          	lui	t1,0x2000
    703c:	00512623          	sw	t0,12(sp)
    7040:	01c7a023          	sw	t3,0(a5) # ffb80000 <__stack_top+0x7f000>
    7044:	01c7a223          	sw	t3,4(a5)
    7048:	0067a423          	sw	t1,8(a5)
    704c:	0067a623          	sw	t1,12(a5)
    7050:	0067a823          	sw	t1,16(a5)
    7054:	41000e37          	lui	t3,0x41000
    7058:	01c7aa23          	sw	t3,20(a5)
    705c:	41008e37          	lui	t3,0x41008
    7060:	0067ac23          	sw	t1,24(a5)
    7064:	001e0313          	addi	t1,t3,1 # 41008001 <__kernel_data_lma+0x41000d69>
    7068:	0067ae23          	sw	t1,28(a5)
    706c:	41010337          	lui	t1,0x41010
    7070:	0267a023          	sw	t1,32(a5)
    7074:	01e6a023          	sw	t5,0(a3)
    7078:	0106a023          	sw	a6,0(a3)
    707c:	01d6a023          	sw	t4,0(a3)
    7080:	00a6a023          	sw	a0,0(a3)
    7084:	89000006          	ttstallwait	128,1
    7088:	c0700032          	ttwrcfg	28,0,12
    708c:	c0740036          	ttwrcfg	29,0,13
    7090:	08000000          	ttnop
    7094:	08000000          	ttnop
    7098:	00b6a023          	sw	a1,0(a3)
    709c:	00012023          	sw	zero,0(sp)
    70a0:	00012783          	lw	a5,0(sp)
    70a4:	ffb009b7          	lui	s3,0xffb00
    70a8:	00f72223          	sw	a5,4(a4)
    70ac:	00472783          	lw	a5,4(a4)
    70b0:	0009a023          	sw	zero,0(s3) # ffb00000 <_ZN7ckernel14dest_offset_idE>
    70b4:	00f12023          	sw	a5,0(sp)
    70b8:	88420022          	ttstallwait	33,8
    70bc:	008f8793          	addi	a5,t6,8
    70c0:	01060613          	addi	a2,a2,16
    70c4:	00f6a023          	sw	a5,0(a3)
    70c8:	00c6a023          	sw	a2,0(a3)
    70cc:	89000006          	ttstallwait	128,1
    70d0:	b00482b7          	lui	t0,0xb0048
    70d4:	0b428293          	addi	t0,t0,180 # b00480b4 <__kernel_data_lma+0xb0040e1c>
    70d8:	0056a023          	sw	t0,0(a3)
    70dc:	80000001          	ttdmanop
    70e0:	80000001          	ttdmanop
    70e4:	4600002d          	ttsetadcxy	4,0,0,0,0,11
    70e8:	5200003d          	ttsetadczw	4,0,0,0,0,15
    70ec:	18090863          	beqz	s2,727c <.L32>
    70f0:	02812e23          	sw	s0,60(sp)
    70f4:	02912c23          	sw	s1,56(sp)
    70f8:	01912c23          	sw	s9,24(sp)
    70fc:	01a12a23          	sw	s10,20(sp)
    7100:	01b12823          	sw	s11,16(sp)
    7104:	010004b7          	lui	s1,0x1000
    7108:	54800437          	lui	s0,0x54800
    710c:	676163b7          	lui	t2,0x67616
    7110:	20c8a583          	lw	a1,524(a7)
    7114:	2088ad03          	lw	s10,520(a7)
    7118:	2048ac83          	lw	s9,516(a7)
    711c:	2008ad83          	lw	s11,512(a7)
    7120:	21a8d783          	lhu	a5,538(a7)
    7124:	21c8a803          	lw	a6,540(a7)
    7128:	2148a503          	lw	a0,532(a7)
    712c:	03412623          	sw	s4,44(sp)
    7130:	03512423          	sw	s5,40(sp)
    7134:	03612223          	sw	s6,36(sp)
    7138:	03712023          	sw	s7,32(sp)
    713c:	01812e23          	sw	s8,28(sp)
    7140:	018f8b93          	addi	s7,t6,24
    7144:	019f8f13          	addi	t5,t6,25
    7148:	f0048493          	addi	s1,s1,-256 # ffff00 <__kernel_data_lma+0xff8c68>
    714c:	00540413          	addi	s0,s0,5 # 54800005 <__kernel_data_lma+0x547f8d6d>
    7150:	00a38393          	addi	t2,t2,10 # 6761600a <__kernel_data_lma+0x6760ed72>
    7154:	00000e13          	li	t3,0
    7158:	00000e93          	li	t4,0
    715c:	ffb58637          	lui	a2,0xffb58
    7160:	508c0c37          	lui	s8,0x508c0
    7164:	00800b37          	lui	s6,0x800
    7168:	030f8f93          	addi	t6,t6,48
    716c:	10104ab7          	lui	s5,0x10104
    7170:	00100a13          	li	s4,1

00007174 <.L18>:
    7174:	98020026          	ttsemwait	1,2,1

00007178 <.L15>:
    7178:	02062703          	lw	a4,32(a2) # ffb58020 <__stack_top+0x57020>
    717c:	00e58733          	add	a4,a1,a4
    7180:	08074733          	zext.h	a4,a4
    7184:	fee78ae3          	beq	a5,a4,7178 <.L15>
    7188:	00a80733          	add	a4,a6,a0
    718c:	fff70713          	addi	a4,a4,-1
    7190:	00871813          	slli	a6,a4,0x8
    7194:	01075713          	srli	a4,a4,0x10
    7198:	00987833          	and	a6,a6,s1
    719c:	00871713          	slli	a4,a4,0x8
    71a0:	0186a023          	sw	s8,0(a3)
    71a4:	01780833          	add	a6,a6,s7
    71a8:	01676333          	or	t1,a4,s6
    71ac:	0106a023          	sw	a6,0(a3)
    71b0:	01e30333          	add	t1,t1,t5
    71b4:	0066a023          	sw	t1,0(a3)
    71b8:	89000026          	ttstallwait	128,9
    71bc:	c0300116          	ttwrcfg	12,0,69
    71c0:	01e70733          	add	a4,a4,t5
    71c4:	00e6a023          	sw	a4,0(a3)
    71c8:	80000001          	ttdmanop
    71cc:	06000000          	ttmop	1,0,0
    71d0:	01a50533          	add	a0,a0,s10
    71d4:	20a8aa23          	sw	a0,532(a7)
    71d8:	0086a023          	sw	s0,0(a3)
    71dc:	2008ae23          	sw	zero,540(a7)
    71e0:	01956663          	bltu	a0,s9,71ec <.L16>
    71e4:	41b50533          	sub	a0,a0,s11
    71e8:	20a8aa23          	sw	a0,532(a7)

000071ec <.L16>:
    71ec:	00178793          	addi	a5,a5,1
    71f0:	0807c7b3          	zext.h	a5,a5
    71f4:	00879713          	slli	a4,a5,0x8
    71f8:	01f70733          	add	a4,a4,t6
    71fc:	00e6a023          	sw	a4,0(a3)
    7200:	20f89d23          	sh	a5,538(a7)
    7204:	88400022          	ttstallwait	32,8
    7208:	0076a023          	sw	t2,0(a3)
    720c:	88800022          	ttstallwait	64,8
    7210:	015e0733          	add	a4,t3,s5
    7214:	00e6a023          	sw	a4,0(a3)
    7218:	94000022          	ttsemget	2
    721c:	001e4713          	xori	a4,t3,1
    7220:	00e9a023          	sw	a4,0(s3)
    7224:	00028813          	mv	a6,t0
    7228:	014e0663          	beq	t3,s4,7234 <.L17>
    722c:	b0088837          	lui	a6,0xb0088
    7230:	0b480813          	addi	a6,a6,180 # b00880b4 <__kernel_data_lma+0xb0080e1c>

00007234 <.L17>:
    7234:	0106a023          	sw	a6,0(a3)
    7238:	80000001          	ttdmanop
    723c:	80000001          	ttdmanop
    7240:	001e8e93          	addi	t4,t4,1
    7244:	00000813          	li	a6,0
    7248:	01d90663          	beq	s2,t4,7254 <.L35>
    724c:	00070e13          	mv	t3,a4
    7250:	f25ff06f          	j	7174 <.L18>

00007254 <.L35>:
    7254:	03c12403          	lw	s0,60(sp)
    7258:	03812483          	lw	s1,56(sp)
    725c:	02c12a03          	lw	s4,44(sp)
    7260:	02812a83          	lw	s5,40(sp)
    7264:	02412b03          	lw	s6,36(sp)
    7268:	02012b83          	lw	s7,32(sp)
    726c:	01c12c03          	lw	s8,28(sp)
    7270:	01812c83          	lw	s9,24(sp)
    7274:	01412d03          	lw	s10,20(sp)
    7278:	01012d83          	lw	s11,16(sp)

0000727c <.L32>:
    727c:	03412903          	lw	s2,52(sp)
    7280:	03012983          	lw	s3,48(sp)
    7284:	00000513          	li	a0,0
    7288:	04010113          	addi	sp,sp,64
    728c:	00008067          	ret

00007290 <.L21>:
    7290:	00068793          	mv	a5,a3
    7294:	bb5ff06f          	j	6e48 <.L4>
