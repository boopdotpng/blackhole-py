# llama3 1B decode: o, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (21): 4,4 7,4 12,4 2,5 5,5 10,5 13,5 2,6 5,6 10,6 13,6 2,7 5,7 10,7 13,7 2,8 5,8 10,8 13,8 2,9 5,9
# params: 0x7c0=e2e_context_decode_token, 0x7c4=e2e_l0_q, 0x7c8=e2e_x_b, 0x7cc=e2e_x_a, 0x8040=e2e_q_compact, 0x8044=e2e_l0_q_row_start, 0x8048=dense_start
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
      4: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000904b7  lui          x9, 0x00090  # x9 = 0x00090000
      c: 00942023  sw           x9, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00090000
     10: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     14: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00042023  sw           x0, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 1b4000ef  jal          x1, 0x000001d0  # target 0x000001d0; x1 = 0x00000020
     20: 1cc000ef  jal          x1, 0x000001ec  # target 0x000001ec; x1 = 0x00000024
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: 1e0000ef  jal          x1, 0x00000208  # target 0x00000208; x1 = 0x0000002c
     2c: 000a8213  addi         x4, x21, 0
     30: 000b0293  addi         x5, x22, 0
     34: 00020f93  addi         x31, x4, 0
     38: 00028f13  addi         x30, x5, 0
     3c: 00093eb7  lui          x29, 0x00093  # x29 = 0x00093000
     40: 214000ef  jal          x1, 0x00000254  # target 0x00000254; x1 = 0x00000044
     44: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     48: 1c0000ef  jal          x1, 0x00000208  # target 0x00000208; x1 = 0x0000004c
     4c: 000a8213  addi         x4, x21, 0
     50: 000b0293  addi         x5, x22, 0
     54: 00020f93  addi         x31, x4, 0
     58: 00028f13  addi         x30, x5, 0
     5c: 00094eb7  lui          x29, 0x00094  # x29 = 0x00094000
     60: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00093800
     64: 1f0000ef  jal          x1, 0x00000254  # target 0x00000254; x1 = 0x00000068
     68: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     6c: 28c000ef  jal          x1, 0x000002f8  # target 0x000002f8; x1 = 0x00000070
     70: 000a8213  addi         x4, x21, 0
     74: 000b0293  addi         x5, x22, 0
     78: 00020f93  addi         x31, x4, 0
     7c: 00028f13  addi         x30, x5, 0
     80: 00095eb7  lui          x29, 0x00095  # x29 = 0x00095000
     84: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00094800
     88: 1cc000ef  jal          x1, 0x00000254  # target 0x00000254; x1 = 0x0000008c
     8c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     90: 268000ef  jal          x1, 0x000002f8  # target 0x000002f8; x1 = 0x00000094
     94: 000a8213  addi         x4, x21, 0
     98: 000b0293  addi         x5, x22, 0
     9c: 00020f93  addi         x31, x4, 0
     a0: 00028f13  addi         x30, x5, 0
     a4: 00095eb7  lui          x29, 0x00095  # x29 = 0x00095000
     a8: 1ac000ef  jal          x1, 0x00000254  # target 0x00000254; x1 = 0x000000ac
     ac: 140000ef  jal          x1, 0x000001ec  # target 0x000001ec; x1 = 0x000000b0
     b0: 7c400313  addi         x6, x0, 1988  # x6 = 0x000007c4
     b4: 00032203  lw           x4, 0(x6)  # param e2e_l0_q; 0x000007c4
     b8: ff827213  andi         x4, x4, -8
     bc: 00008437  lui          x8, 0x00008  # x8 = 0x00008000
     c0: 04440413  addi         x8, x8, 68  # x8 = 0x00008044
     c4: 00042303  lw           x6, 0(x8)  # param e2e_l0_q_row_start; 0x00008044
     c8: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
     cc: 02730333  mul          x6, x6, x7
     d0: 00737293  andi         x5, x6, 7
     d4: 00335313  srli         x6, x6, 3
     d8: 00b31313  slli         x6, x6, 11
     dc: 00620233  add          x4, x4, x6
     e0: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
     e4: 01700393  addi         x7, x0, 23  # x7 = 0x00000017
loc_e8:
     e8: 0e737263  bgeu         x6, x7, 0x000001cc  # target 0x000001cc
     ec: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
     f0: 87c68693  addi         x13, x13, -1924  # x13 = 0xffb0087c · riscv_local_mem + 0x87c
     f4: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_f8:
     f8: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
     fc: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    100: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    104: 40940533  sub          x10, x8, x9
    108: 01051513  slli         x10, x10, 16
    10c: 01055513  srli         x10, x10, 16
    110: 00400593  addi         x11, x0, 4  # x11 = 0x00000004
    114: 40a585b3  sub          x11, x11, x10
    118: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    11c: 00c5f663  bgeu         x11, x12, 0x00000128  # target 0x00000128
    120: 0ff0000f  fence        0xf, 0xf
    124: fd5ff06f  jal          x0, 0x000000f8  # target 0x000000f8
loc_128:
    128: 0ff0000f  fence        0xf, 0xf
    12c: 0a4000ef  jal          x1, 0x000001d0  # target 0x000001d0; x1 = 0x00000130
    130: 0bc000ef  jal          x1, 0x000001ec  # target 0x000001ec; x1 = 0x00000134
    134: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    138: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
    13c: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878
    140: 00020f93  addi         x31, x4, 0
    144: 00028f13  addi         x30, x5, 0
    148: 00040e93  addi         x29, x8, 0
    14c: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    150: 1f4000ef  jal          x1, 0x00000344  # target 0x00000344; x1 = 0x00000154
    154: 000f8213  addi         x4, x31, 0
    158: 000f0293  addi         x5, x30, 0
    15c: 090000ef  jal          x1, 0x000001ec  # target 0x000001ec; x1 = 0x00000160
    160: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    164: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    168: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    16c: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    170: 00940433  add          x8, x8, x9
    174: 00092537  lui          x10, 0x00092  # x10 = 0x00092000
    178: 00a46663  bltu         x8, x10, 0x00000184  # target 0x00000184
    17c: 000025b7  lui          x11, 0x00002  # x11 = 0x00002000
    180: 40b40433  sub          x8, x8, x11
loc_184:
    184: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    188: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    18c: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    190: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    194: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    198: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
    19c: 00240413  addi         x8, x8, 2
    1a0: 01041413  slli         x8, x8, 16
    1a4: 01045413  srli         x8, x8, 16
    1a8: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    1ac: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    1b0: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1b4: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    1b8: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    1bc: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    1c0: 0ff0000f  fence        0xf, 0xf
    1c4: 00130313  addi         x6, x6, 1
    1c8: f21ff06f  jal          x0, 0x000000e8  # target 0x000000e8
loc_1cc:
    1cc: 2680006f  jal          x0, 0x00000434  # target 0x00000434
loc_1d0:
    1d0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    1d4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    1d8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    1dc: 000a0463  beq          x20, x0, 0x000001e4  # target 0x000001e4
    1e0: ff1ff06f  jal          x0, 0x000001d0  # target 0x000001d0
loc_1e4:
    1e4: 0ff0000f  fence        0xf, 0xf
    1e8: 00008067  jalr         x0, 0(x1)
loc_1ec:
    1ec: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    1f0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    1f4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    1f8: 000a0463  beq          x20, x0, 0x00000200  # target 0x00000200
    1fc: ff1ff06f  jal          x0, 0x000001ec  # target 0x000001ec
loc_200:
    200: 0ff0000f  fence        0xf, 0xf
    204: 00008067  jalr         x0, 0(x1)
loc_208:
    208: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    20c: 000aaa03  lw           x20, 0(x21)  # param e2e_context_decode_token; 0x000007c0
    210: 007a7d13  andi         x26, x20, 7
    214: ff8a7a13  andi         x20, x20, -8
    218: 01af8ab3  add          x21, x31, x26
    21c: 007afb93  andi         x23, x21, 7
    220: 003ada93  srli         x21, x21, 3
    224: 00ba9a93  slli         x21, x21, 11
    228: 014a8ab3  add          x21, x21, x20
    22c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000022c
    230: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000244
    234: 001b9b93  slli         x23, x23, 1
    238: 017b0b33  add          x22, x22, x23
    23c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    240: 00008067  jalr         x0, 0(x1)
    244: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    248: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    24c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    250: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_254:
    254: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    258: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    25c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    260: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    264: 015a6463  bltu         x20, x21, 0x0000026c  # target 0x0000026c
    268: fedff06f  jal          x0, 0x00000254  # target 0x00000254
loc_26c:
    26c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    270: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    274: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    278: 014a1a13  slli         x20, x20, 20
    27c: 014a5a13  srli         x20, x20, 20
    280: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_284:
    284: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    288: 000b0463  beq          x22, x0, 0x00000290  # target 0x00000290
    28c: ff9ff06f  jal          x0, 0x00000284  # target 0x00000284
loc_290:
    290: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    294: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    298: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    29c: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    2a0: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    2a4: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    2a8: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    2ac: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    2b0: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    2b4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    2b8: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    2bc: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    2c0: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c4: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    2c8: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    2cc: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    2d0: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    2d4: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    2d8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    2dc: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    2e0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    2e4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_2e8:
    2e8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    2ec: 000b0463  beq          x22, x0, 0x000002f4  # target 0x000002f4
    2f0: ff9ff06f  jal          x0, 0x000002e8  # target 0x000002e8
loc_2f4:
    2f4: 00008067  jalr         x0, 0(x1)
loc_2f8:
    2f8: 7cc00a93  addi         x21, x0, 1996  # x21 = 0x000007cc
    2fc: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x000007cc
    300: 007a7d13  andi         x26, x20, 7
    304: ff8a7a13  andi         x20, x20, -8
    308: 01af8ab3  add          x21, x31, x26
    30c: 007afb93  andi         x23, x21, 7
    310: 003ada93  srli         x21, x21, 3
    314: 00ba9a93  slli         x21, x21, 11
    318: 014a8ab3  add          x21, x21, x20
    31c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000031c
    320: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000334
    324: 001b9b93  slli         x23, x23, 1
    328: 017b0b33  add          x22, x22, x23
    32c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    330: 00008067  jalr         x0, 0(x1)
    334: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    338: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    33c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    340: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_344:
    344: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000344
    348: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x00000424
loc_34c:
    34c: 001f1a93  slli         x21, x30, 1
    350: 014a8ab3  add          x21, x21, x20
    354: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_358:
    358: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    35c: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    360: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    364: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    368: 018be463  bltu         x23, x24, 0x00000370  # target 0x00000370
    36c: fedff06f  jal          x0, 0x00000358  # target 0x00000358
loc_370:
    370: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    374: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    378: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    37c: 014b9b93  slli         x23, x23, 20
    380: 014bdb93  srli         x23, x23, 20
    384: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_388:
    388: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    38c: 000c8463  beq          x25, x0, 0x00000394  # target 0x00000394
    390: ff9ff06f  jal          x0, 0x00000388  # target 0x00000388
loc_394:
    394: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    398: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    39c: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    3a0: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    3a4: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    3a8: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    3ac: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    3b0: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    3b4: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    3b8: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    3bc: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    3c0: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    3c4: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3c8: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    3cc: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    3d0: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    3d4: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    3d8: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    3dc: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    3e0: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    3e4: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    3e8: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_3ec:
    3ec: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    3f0: 000c8463  beq          x25, x0, 0x000003f8  # target 0x000003f8
    3f4: ff9ff06f  jal          x0, 0x000003ec  # target 0x000003ec
loc_3f8:
    3f8: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3fc: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    400: 016e8eb3  add          x29, x29, x22
    404: 001f0f13  addi         x30, x30, 1
    408: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    40c: 015f1663  bne          x30, x21, 0x00000418  # target 0x00000418
    410: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    414: 016f8fb3  add          x31, x31, x22
loc_418:
    418: fffe0e13  addi         x28, x28, -1
    41c: f20e18e3  bne          x28, x0, 0x0000034c  # target 0x0000034c
    420: 00008067  jalr         x0, 0(x1)
    424: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    428: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    42c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    430: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    434:           j FW_BRISC+4   # return to firmware, linked at install
