
/tmp/tt-disasm-f0917y2p/out.elf:     file format elf32-littleriscv


Disassembly of section .text:

00005e30 <_start>:
    5e30:	fe010113          	addi	sp,sp,-32
    5e34:	ffb007b7          	lui	a5,0xffb00
    5e38:	ffb00737          	lui	a4,0xffb00
    5e3c:	43078793          	addi	a5,a5,1072 # ffb00430 <__stack_base>
    5e40:	42470713          	addi	a4,a4,1060 # ffb00424 <__ldm_bss_end>
    5e44:	00f76e63          	bltu	a4,a5,5e60 <.L2>

00005e48 <.L3>:
    5e48:	fe07ae23          	sw	zero,-4(a5)
    5e4c:	fe07ac23          	sw	zero,-8(a5)
    5e50:	fe07aa23          	sw	zero,-12(a5)
    5e54:	fe07a823          	sw	zero,-16(a5)
    5e58:	01078793          	addi	a5,a5,16
    5e5c:	fef776e3          	bgeu	a4,a5,5e48 <.L3>

00005e60 <.L2>:
    5e60:	ff878693          	addi	a3,a5,-8
    5e64:	40d76a63          	bltu	a4,a3,6278 <.L27>
    5e68:	fe07aa23          	sw	zero,-12(a5)
    5e6c:	fe07a823          	sw	zero,-16(a5)

00005e70 <.L4>:
    5e70:	ffc78693          	addi	a3,a5,-4
    5e74:	00d76463          	bltu	a4,a3,5e7c <.L5>
    5e78:	fe07ac23          	sw	zero,-8(a5)

00005e7c <.L5>:
    5e7c:	00006737          	lui	a4,0x6
    5e80:	ffb007b7          	lui	a5,0xffb00
    5e84:	28070713          	addi	a4,a4,640 # 6280 <__kernel_data_lma>
    5e88:	42078793          	addi	a5,a5,1056 # ffb00420 <unp_cfg_context>
    5e8c:	06f70263          	beq	a4,a5,5ef0 <.L7>
    5e90:	ffb00637          	lui	a2,0xffb00
    5e94:	42060613          	addi	a2,a2,1056 # ffb00420 <unp_cfg_context>
    5e98:	40f60633          	sub	a2,a2,a5
    5e9c:	00800593          	li	a1,8
    5ea0:	40265693          	srai	a3,a2,0x2
    5ea4:	02c5d863          	bge	a1,a2,5ed4 <.L8>
    5ea8:	00200813          	li	a6,2

00005eac <.L9>:
    5eac:	00072503          	lw	a0,0(a4)
    5eb0:	00472583          	lw	a1,4(a4)
    5eb4:	00872603          	lw	a2,8(a4)
    5eb8:	00c70713          	addi	a4,a4,12
    5ebc:	00c78793          	addi	a5,a5,12
    5ec0:	ffd68693          	addi	a3,a3,-3
    5ec4:	fea7aa23          	sw	a0,-12(a5)
    5ec8:	feb7ac23          	sw	a1,-8(a5)
    5ecc:	fec7ae23          	sw	a2,-4(a5)
    5ed0:	fcd84ee3          	blt	a6,a3,5eac <.L9>

00005ed4 <.L8>:
    5ed4:	00d05e63          	blez	a3,5ef0 <.L7>
    5ed8:	00072583          	lw	a1,0(a4)
    5edc:	00200613          	li	a2,2
    5ee0:	00b7a023          	sw	a1,0(a5)
    5ee4:	00c69663          	bne	a3,a2,5ef0 <.L7>
    5ee8:	00472703          	lw	a4,4(a4)
    5eec:	00e7a223          	sw	a4,4(a5)

00005ef0 <.L7>:
    5ef0:	ffb127b7          	lui	a5,0xffb12
    5ef4:	0607a423          	sw	zero,104(a5) # ffb12068 <__stack_top+0x11068>
    5ef8:	3a002703          	lw	a4,928(zero) # 3a0 <_start-0x5a90>
    5efc:	08000693          	li	a3,128
    5f00:	00271713          	slli	a4,a4,0x2
    5f04:	37374783          	lbu	a5,883(a4)
    5f08:	06070713          	addi	a4,a4,96
    5f0c:	00d78863          	beq	a5,a3,5f1c <.L13>

00005f10 <.L11>:
    5f10:	0ff0000f          	fence
    5f14:	31374783          	lbu	a5,787(a4)
    5f18:	fed79ce3          	bne	a5,a3,5f10 <.L11>

00005f1c <.L13>:
    5f1c:	4400001c          	ttzerosrc	0,0,1,3
    5f20:	ffb007b7          	lui	a5,0xffb00
    5f24:	0147a783          	lw	a5,20(a5) # ffb00014 <rta_l1_base>
    5f28:	ffb008b7          	lui	a7,0xffb00
    5f2c:	0007a283          	lw	t0,0(a5)
    5f30:	02088893          	addi	a7,a7,32 # ffb00020 <cb_interface>
    5f34:	0088a683          	lw	a3,8(a7)
    5f38:	ffe80737          	lui	a4,0xffe80

00005f3c <.L12>:
    5f3c:	03472783          	lw	a5,52(a4) # ffe80034 <__instrn_buffer+0x40034>
    5f40:	0ff7f793          	zext.b	a5,a5
    5f44:	fe079ce3          	bnez	a5,5f3c <.L12>
    5f48:	4580002d          	ttsetadcxy	3,0,0,0,0,11
    5f4c:	5180003d          	ttsetadczw	3,0,0,0,0,15
    5f50:	ffb00e37          	lui	t3,0xffb00
    5f54:	01ce2703          	lw	a4,28(t3) # ffb0001c <_ZN7ckernel12cfg_state_idE>
    5f58:	ffef07b7          	lui	a5,0xffef0
    5f5c:	00070463          	beqz	a4,5f64 <.L14>
    5f60:	38078793          	addi	a5,a5,896 # ffef0380 <__instrn_buffer+0xb0380>

00005f64 <.L14>:
    5f64:	20000713          	li	a4,512
    5f68:	0ee7a223          	sw	a4,228(a5)
    5f6c:	0ee7a623          	sw	a4,236(a5)
    5f70:	80000002          	ttatgetm	0
    5f74:	ffe40537          	lui	a0,0xffe40
    5f78:	00050513          	mv	a0,a0
    5f7c:	b3ff0737          	lui	a4,0xb3ff0
    5f80:	00e52023          	sw	a4,0(a0) # ffe40000 <__instrn_buffer>
    5f84:	b47f0737          	lui	a4,0xb47f0
    5f88:	00e52023          	sw	a4,0(a0)
    5f8c:	b3070737          	lui	a4,0xb3070
    5f90:	00170713          	addi	a4,a4,1 # b3070001 <__kernel_data_lma+0xb3069d81>
    5f94:	00e52023          	sw	a4,0(a0)
    5f98:	b4800737          	lui	a4,0xb4800
    5f9c:	00170713          	addi	a4,a4,1 # b4800001 <__kernel_data_lma+0xb47f9d81>
    5fa0:	00e52023          	sw	a4,0(a0)
    5fa4:	b5010737          	lui	a4,0xb5010
    5fa8:	00170713          	addi	a4,a4,1 # b5010001 <__kernel_data_lma+0xb5009d81>
    5fac:	00e52023          	sw	a4,0(a0)
    5fb0:	b6600737          	lui	a4,0xb6600
    5fb4:	00170713          	addi	a4,a4,1 # b6600001 <__kernel_data_lma+0xb65f9d81>
    5fb8:	00e52023          	sw	a4,0(a0)
    5fbc:	b3010737          	lui	a4,0xb3010
    5fc0:	10270713          	addi	a4,a4,258 # b3010102 <__kernel_data_lma+0xb3009e82>
    5fc4:	00e52023          	sw	a4,0(a0)
    5fc8:	84000002          	ttatrelm	0
    5fcc:	01500713          	li	a4,21
    5fd0:	10e7a023          	sw	a4,256(a5)
    5fd4:	00040737          	lui	a4,0x40
    5fd8:	00170713          	addi	a4,a4,1 # 40001 <__kernel_data_lma+0x39d81>
    5fdc:	01000637          	lui	a2,0x1000
    5fe0:	10e7a223          	sw	a4,260(a5)
    5fe4:	01560593          	addi	a1,a2,21 # 1000015 <__kernel_data_lma+0xff9d95>
    5fe8:	1cb7a023          	sw	a1,448(a5)
    5fec:	1ce7a223          	sw	a4,452(a5)
    5ff0:	02500593          	li	a1,37
    5ff4:	000f0737          	lui	a4,0xf0
    5ff8:	12b7a023          	sw	a1,288(a5)
    5ffc:	00f70713          	addi	a4,a4,15 # f000f <__kernel_data_lma+0xe9d8f>
    6000:	12e7a223          	sw	a4,292(a5)
    6004:	1eb7a023          	sw	a1,480(a5)
    6008:	1ee7a223          	sw	a4,484(a5)
    600c:	5e240737          	lui	a4,0x5e240
    6010:	c0070713          	addi	a4,a4,-1024 # 5e23fc00 <__kernel_data_lma+0x5e239980>
    6014:	00e52023          	sw	a4,0(a0)
    6018:	5e440737          	lui	a4,0x5e440
    601c:	c0070713          	addi	a4,a4,-1024 # 5e43fc00 <__kernel_data_lma+0x5e439980>
    6020:	004005b7          	lui	a1,0x400
    6024:	00e52023          	sw	a4,0(a0)
    6028:	04058593          	addi	a1,a1,64 # 400040 <__kernel_data_lma+0x3f9dc0>
    602c:	14b7a823          	sw	a1,336(a5)
    6030:	10060813          	addi	a6,a2,256
    6034:	1507ac23          	sw	a6,344(a5)
    6038:	ffe00737          	lui	a4,0xffe00
    603c:	0b072023          	sw	a6,160(a4) # ffe000a0 <__stack_top+0x2ff0a0>
    6040:	00800837          	lui	a6,0x800
    6044:	08080813          	addi	a6,a6,128 # 800080 <__kernel_data_lma+0x7f9e00>
    6048:	0b072223          	sw	a6,164(a4)
    604c:	0ab72423          	sw	a1,168(a4)
    6050:	002005b7          	lui	a1,0x200
    6054:	02058593          	addi	a1,a1,32 # 200020 <__kernel_data_lma+0x1f9da0>
    6058:	0ab72623          	sw	a1,172(a4)
    605c:	001005b7          	lui	a1,0x100
    6060:	01058593          	addi	a1,a1,16 # 100010 <__kernel_data_lma+0xf9d90>
    6064:	0ab72823          	sw	a1,176(a4)
    6068:	00012223          	sw	zero,4(sp)
    606c:	0b072703          	lw	a4,176(a4)
    6070:	00e12223          	sw	a4,4(sp)
    6074:	c8140012          	ttsetc16	5,4
    6078:	10000713          	li	a4,256
    607c:	ffb00337          	lui	t1,0xffb00
    6080:	0ce7a423          	sw	a4,200(a5)
    6084:	42032023          	sw	zero,1056(t1) # ffb00420 <unp_cfg_context>
    6088:	c8a40002          	ttsetc16	41,0
    608c:	45000737          	lui	a4,0x45000
    6090:	00869793          	slli	a5,a3,0x8
    6094:	f0060613          	addi	a2,a2,-256
    6098:	00c7f7b3          	and	a5,a5,a2
    609c:	04870693          	addi	a3,a4,72 # 45000048 <__kernel_data_lma+0x44ff9dc8>
    60a0:	00d786b3          	add	a3,a5,a3
    60a4:	04a70713          	addi	a4,a4,74
    60a8:	00d52023          	sw	a3,0(a0)
    60ac:	00e787b3          	add	a5,a5,a4
    60b0:	b4010837          	lui	a6,0xb4010
    60b4:	00f52023          	sw	a5,0(a0)
    60b8:	04880813          	addi	a6,a6,72 # b4010048 <__kernel_data_lma+0xb4009dc8>
    60bc:	01052023          	sw	a6,0(a0)
    60c0:	788ff001          	ttsetadcxx	1,255,0
    60c4:	00012423          	sw	zero,8(sp)
    60c8:	00812783          	lw	a5,8(sp)
    60cc:	ffe805b7          	lui	a1,0xffe80
    60d0:	00f5a423          	sw	a5,8(a1) # ffe80008 <__instrn_buffer+0x40008>
    60d4:	0085a703          	lw	a4,8(a1)
    60d8:	ffb807b7          	lui	a5,0xffb80
    60dc:	00400f13          	li	t5,4
    60e0:	00100e93          	li	t4,1
    60e4:	00e12423          	sw	a4,8(sp)
    60e8:	01e7a023          	sw	t5,0(a5) # ffb80000 <__stack_top+0x7f000>
    60ec:	42008637          	lui	a2,0x42008
    60f0:	01d7a223          	sw	t4,4(a5)
    60f4:	0c160613          	addi	a2,a2,193 # 420080c1 <__kernel_data_lma+0x42001e41>
    60f8:	00c7a423          	sw	a2,8(a5)
    60fc:	020006b7          	lui	a3,0x2000
    6100:	00d7a623          	sw	a3,12(a5)
    6104:	43800737          	lui	a4,0x43800
    6108:	00d7a823          	sw	a3,16(a5)
    610c:	10170713          	addi	a4,a4,257 # 43800101 <__kernel_data_lma+0x437f9e81>
    6110:	00e7aa23          	sw	a4,20(a5)
    6114:	00d7ac23          	sw	a3,24(a5)
    6118:	00e7ae23          	sw	a4,28(a5)
    611c:	02e7a023          	sw	a4,32(a5)
    6120:	01052023          	sw	a6,0(a0)
    6124:	788ff001          	ttsetadcxx	1,255,0
    6128:	00012623          	sw	zero,12(sp)
    612c:	00c12803          	lw	a6,12(sp)
    6130:	0105a423          	sw	a6,8(a1)
    6134:	0085a583          	lw	a1,8(a1)
    6138:	00b12623          	sw	a1,12(sp)
    613c:	01e7a023          	sw	t5,0(a5)
    6140:	01d7a223          	sw	t4,4(a5)
    6144:	00c7a423          	sw	a2,8(a5)
    6148:	00d7a623          	sw	a3,12(a5)
    614c:	00d7a823          	sw	a3,16(a5)
    6150:	00e7aa23          	sw	a4,20(a5)
    6154:	00d7ac23          	sw	a3,24(a5)
    6158:	00e7ae23          	sw	a4,28(a5)
    615c:	02e7a023          	sw	a4,32(a5)
    6160:	0c028e63          	beqz	t0,623c <.L41>
    6164:	01ce2703          	lw	a4,28(t3)
    6168:	ffef07b7          	lui	a5,0xffef0
    616c:	00812e23          	sw	s0,28(sp)
    6170:	00912c23          	sw	s1,24(sp)
    6174:	01212a23          	sw	s2,20(sp)
    6178:	38078393          	addi	t2,a5,896 # ffef0380 <__instrn_buffer+0xb0380>
    617c:	0e070a63          	beqz	a4,6270 <.L44>

00006180 <.L17>:
    6180:	45000fb7          	lui	t6,0x45000
    6184:	67112f37          	lui	t5,0x67112
    6188:	0088a483          	lw	s1,8(a7)
    618c:	0048a403          	lw	s0,4(a7)
    6190:	0008a903          	lw	s2,0(a7)
    6194:	0188d703          	lhu	a4,24(a7)
    6198:	0108a583          	lw	a1,16(a7)
    619c:	008f8f93          	addi	t6,t6,8 # 45000008 <__kernel_data_lma+0x44ff9d88>
    61a0:	008f0f13          	addi	t5,t5,8 # 67112008 <__kernel_data_lma+0x6710bd88>
    61a4:	00000813          	li	a6,0
    61a8:	ffb48637          	lui	a2,0xffb48
    61ac:	ffe806b7          	lui	a3,0xffe80
    61b0:	00100e93          	li	t4,1

000061b4 <.L18>:
    61b4:	02862783          	lw	a5,40(a2) # ffb48028 <__stack_top+0x47028>
    61b8:	0807c7b3          	zext.h	a5,a5
    61bc:	fee78ce3          	beq	a5,a4,61b4 <.L18>
    61c0:	fff58e13          	addi	t3,a1,-1
    61c4:	5180003d          	ttsetadczw	3,0,0,0,0,15

000061c8 <.L19>:
    61c8:	0346a783          	lw	a5,52(a3) # ffe80034 <__instrn_buffer+0x40034>
    61cc:	0fe7f793          	andi	a5,a5,254
    61d0:	fe079ce3          	bnez	a5,61c8 <.L19>
    61d4:	42032783          	lw	a5,1056(t1)
    61d8:	06079863          	bnez	a5,6248 <.L20>
    61dc:	13c3a823          	sw	t3,304(t2)
    61e0:	0206aa23          	sw	zero,52(a3)
    61e4:	88101002          	ttstallwait	8,1024
    61e8:	06000000          	ttmop	1,0,0
    61ec:	94000202          	ttsemget	32
    61f0:	43d32023          	sw	t4,1056(t1)

000061f4 <.L21>:
    61f4:	c8a40406          	ttsetc16	41,257

000061f8 <.L22>:
    61f8:	00170713          	addi	a4,a4,1
    61fc:	08074733          	zext.h	a4,a4
    6200:	00871793          	slli	a5,a4,0x8
    6204:	01f787b3          	add	a5,a5,t6
    6208:	00e89c23          	sh	a4,24(a7)
    620c:	00f52023          	sw	a5,0(a0)
    6210:	8840001a          	ttstallwait	32,6
    6214:	01e52023          	sw	t5,0(a0)
    6218:	009585b3          	add	a1,a1,s1
    621c:	0085e463          	bltu	a1,s0,6224 <.L23>
    6220:	412585b3          	sub	a1,a1,s2

00006224 <.L23>:
    6224:	00b8a823          	sw	a1,16(a7)
    6228:	00180813          	addi	a6,a6,1
    622c:	f90294e3          	bne	t0,a6,61b4 <.L18>
    6230:	01c12403          	lw	s0,28(sp)
    6234:	01812483          	lw	s1,24(sp)
    6238:	01412903          	lw	s2,20(sp)

0000623c <.L41>:
    623c:	00000513          	li	a0,0
    6240:	02010113          	addi	sp,sp,32
    6244:	00008067          	ret

00006248 <.L20>:
    6248:	13c3aa23          	sw	t3,308(t2)
    624c:	0206aa23          	sw	zero,52(a3)
    6250:	88101002          	ttstallwait	8,1024
    6254:	06000000          	ttmop	1,0,0
    6258:	94000202          	ttsemget	32
    625c:	40fe8e33          	sub	t3,t4,a5
    6260:	43c32023          	sw	t3,1056(t1)
    6264:	f9d798e3          	bne	a5,t4,61f4 <.L21>
    6268:	c8a40002          	ttsetc16	41,0
    626c:	f8dff06f          	j	61f8 <.L22>

00006270 <.L44>:
    6270:	00078393          	mv	t2,a5
    6274:	f0dff06f          	j	6180 <.L17>

00006278 <.L27>:
    6278:	00068793          	mv	a5,a3
    627c:	bf5ff06f          	j	5e70 <.L4>
