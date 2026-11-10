# llama3 1b decode: down, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (40): 7,2 10,2 11,2 12,2 13,2 7,3 10,3 11,3 12,3 13,3 7,4 10,4 11,4 12,4 13,4 7,5 10,5 11,5 12,5 13,5 7,6 10,6 11,6 12,6 13,6 7,7 10,7 11,7 12,7 13,7 7,8 10,8 11,8 12,8 13,8 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_hidden_dense_decode_token, 0x784=e2e_l0_down, 0x788=e2e_x_a, 0x78c=e2e_x_b, 0xe980=e2e_q_compact, 0xe984=e2e_l0_down_row_start, 0xe988=dense_start, 0xe98c=e2e_l0_down_rows
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0000f537  lui          x10, 0x0000f  # x10 = 0x0000f000
      c: fc050513  addi         x10, x10, -64  # x10 = 0x0000efc0
     10: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000efc0
     14: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     18: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: 2a4000ef  jal          x1, 0x000002c4  # target 0x000002c4; x1 = 0x00000024
     24: 2bc000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x00000028
     28: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     2c: 2d0000ef  jal          x1, 0x000002fc  # target 0x000002fc; x1 = 0x00000030
     30: 000a8213  addi         x4, x21, 0
     34: 000b0293  addi         x5, x22, 0
     38: 00020f93  addi         x31, x4, 0
     3c: 00028f13  addi         x30, x5, 0
     40: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     44: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00017fc0
     48: 300000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x0000004c
     4c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     50: 2ac000ef  jal          x1, 0x000002fc  # target 0x000002fc; x1 = 0x00000054
     54: 000a8213  addi         x4, x21, 0
     58: 000b0293  addi         x5, x22, 0
     5c: 00020f93  addi         x31, x4, 0
     60: 00028f13  addi         x30, x5, 0
     64: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     68: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000187c0
     6c: 2dc000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000070
     70: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     74: 288000ef  jal          x1, 0x000002fc  # target 0x000002fc; x1 = 0x00000078
     78: 000a8213  addi         x4, x21, 0
     7c: 000b0293  addi         x5, x22, 0
     80: 00020f93  addi         x31, x4, 0
     84: 00028f13  addi         x30, x5, 0
     88: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
     8c: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00018fc0
     90: 2b8000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000094
     94: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     98: 264000ef  jal          x1, 0x000002fc  # target 0x000002fc; x1 = 0x0000009c
     9c: 000a8213  addi         x4, x21, 0
     a0: 000b0293  addi         x5, x22, 0
     a4: 00020f93  addi         x31, x4, 0
     a8: 00028f13  addi         x30, x5, 0
     ac: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
     b0: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000197c0
     b4: 294000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x000000b8
     b8: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
     bc: 240000ef  jal          x1, 0x000002fc  # target 0x000002fc; x1 = 0x000000c0
     c0: 000a8213  addi         x4, x21, 0
     c4: 000b0293  addi         x5, x22, 0
     c8: 00020f93  addi         x31, x4, 0
     cc: 00028f13  addi         x30, x5, 0
     d0: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
     d4: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00019fc0
     d8: 270000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x000000dc
     dc: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
     e0: 21c000ef  jal          x1, 0x000002fc  # target 0x000002fc; x1 = 0x000000e4
     e4: 000a8213  addi         x4, x21, 0
     e8: 000b0293  addi         x5, x22, 0
     ec: 00020f93  addi         x31, x4, 0
     f0: 00028f13  addi         x30, x5, 0
     f4: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
     f8: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x0001a7c0
     fc: 24c000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000100
    100: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
    104: 1f8000ef  jal          x1, 0x000002fc  # target 0x000002fc; x1 = 0x00000108
    108: 000a8213  addi         x4, x21, 0
    10c: 000b0293  addi         x5, x22, 0
    110: 00020f93  addi         x31, x4, 0
    114: 00028f13  addi         x30, x5, 0
    118: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    11c: fc0e8e93  addi         x29, x29, -64  # x29 = 0x0001afc0
    120: 228000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000124
    124: 00700f93  addi         x31, x0, 7  # x31 = 0x00000007
    128: 1d4000ef  jal          x1, 0x000002fc  # target 0x000002fc; x1 = 0x0000012c
    12c: 000a8213  addi         x4, x21, 0
    130: 000b0293  addi         x5, x22, 0
    134: 00020f93  addi         x31, x4, 0
    138: 00028f13  addi         x30, x5, 0
    13c: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    140: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x0001b7c0
    144: 204000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000148
    148: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    14c: 2a0000ef  jal          x1, 0x000003ec  # target 0x000003ec; x1 = 0x00000150
    150: 000a8213  addi         x4, x21, 0
    154: 000b0293  addi         x5, x22, 0
    158: 00020f93  addi         x31, x4, 0
    15c: 00028f13  addi         x30, x5, 0
    160: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    164: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x0001c7c0
    168: 1e0000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x0000016c
    16c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    170: 27c000ef  jal          x1, 0x000003ec  # target 0x000003ec; x1 = 0x00000174
    174: 000a8213  addi         x4, x21, 0
    178: 000b0293  addi         x5, x22, 0
    17c: 00020f93  addi         x31, x4, 0
    180: 00028f13  addi         x30, x5, 0
    184: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    188: fc0e8e93  addi         x29, x29, -64  # x29 = 0x0001cfc0
    18c: 1bc000ef  jal          x1, 0x00000348  # target 0x00000348; x1 = 0x00000190
    190: 150000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x00000194
    194: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    198: 98c28293  addi         x5, x5, -1652  # x5 = 0x0000e98c
    19c: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000e98c
    1a0: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    1a4: 0003a283  lw           x5, 0(x7)  # param e2e_l0_down; 0x00000784
    1a8: ff82f293  andi         x5, x5, -8
    1ac: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    1b0: 98448493  addi         x9, x9, -1660  # x9 = 0x0000e984
    1b4: 0004a383  lw           x7, 0(x9)  # param e2e_l0_down_row_start; 0x0000e984
    1b8: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
    1bc: 028383b3  mul          x7, x7, x8
    1c0: 0073f313  andi         x6, x7, 7
    1c4: 0033d393  srli         x7, x7, 3
    1c8: 00b39393  slli         x7, x7, 11
    1cc: 007282b3  add          x5, x5, x7
    1d0: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1d4: 00020413  addi         x8, x4, 0
loc_1d8:
    1d8: 0e83f463  bgeu         x7, x8, 0x000002c0  # target 0x000002c0
    1dc: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1e0: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    1e4: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_1e8:
    1e8: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1ec: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1f0: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1f4: 40a485b3  sub          x11, x9, x10
    1f8: 01059593  slli         x11, x11, 16
    1fc: 0105d593  srli         x11, x11, 16
    200: 01000613  addi         x12, x0, 16  # x12 = 0x00000010
    204: 40b60633  sub          x12, x12, x11
    208: 00800693  addi         x13, x0, 8  # x13 = 0x00000008
    20c: 00d67663  bgeu         x12, x13, 0x00000218  # target 0x00000218
    210: 0ff0000f  fence        0xf, 0xf
    214: fd5ff06f  jal          x0, 0x000001e8  # target 0x000001e8
loc_218:
    218: 0ff0000f  fence        0xf, 0xf
    21c: 0a8000ef  jal          x1, 0x000002c4  # target 0x000002c4; x1 = 0x00000220
    220: 0c0000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x00000224
    224: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    228: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    22c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    230: 00028f93  addi         x31, x5, 0
    234: 00030f13  addi         x30, x6, 0
    238: 00048e93  addi         x29, x9, 0
    23c: 00800e13  addi         x28, x0, 8  # x28 = 0x00000008
    240: 1f8000ef  jal          x1, 0x00000438  # target 0x00000438; x1 = 0x00000244
    244: 000f8293  addi         x5, x31, 0
    248: 000f0313  addi         x6, x30, 0
    24c: 094000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x00000250
    250: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    254: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    258: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    25c: 00004537  lui          x10, 0x00004  # x10 = 0x00004000
    260: 00a484b3  add          x9, x9, x10
    264: 000175b7  lui          x11, 0x00017  # x11 = 0x00017000
    268: fc058593  addi         x11, x11, -64  # x11 = 0x00016fc0
    26c: 00b4e663  bltu         x9, x11, 0x00000278  # target 0x00000278
    270: 00008637  lui          x12, 0x00008  # x12 = 0x00008000
    274: 40c484b3  sub          x9, x9, x12
loc_278:
    278: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    27c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    280: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    284: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    288: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    28c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    290: 00848493  addi         x9, x9, 8
    294: 01049493  slli         x9, x9, 16
    298: 0104d493  srli         x9, x9, 16
    29c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2a0: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    2a4: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    2a8: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    2ac: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    2b0: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    2b4: 0ff0000f  fence        0xf, 0xf
    2b8: 00138393  addi         x7, x7, 1
    2bc: f1dff06f  jal          x0, 0x000001d8  # target 0x000001d8
loc_2c0:
    2c0: 2680006f  jal          x0, 0x00000528  # target 0x00000528
loc_2c4:
    2c4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2c8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    2cc: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    2d0: 000a0463  beq          x20, x0, 0x000002d8  # target 0x000002d8
    2d4: ff1ff06f  jal          x0, 0x000002c4  # target 0x000002c4
loc_2d8:
    2d8: 0ff0000f  fence        0xf, 0xf
    2dc: 00008067  jalr         x0, 0(x1)
loc_2e0:
    2e0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2e4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    2e8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    2ec: 000a0463  beq          x20, x0, 0x000002f4  # target 0x000002f4
    2f0: ff1ff06f  jal          x0, 0x000002e0  # target 0x000002e0
loc_2f4:
    2f4: 0ff0000f  fence        0xf, 0xf
    2f8: 00008067  jalr         x0, 0(x1)
loc_2fc:
    2fc: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    300: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense_decode_token; 0x00000780
    304: 007a7d13  andi         x26, x20, 7
    308: ff8a7a13  andi         x20, x20, -8
    30c: 01af8ab3  add          x21, x31, x26
    310: 007afb93  andi         x23, x21, 7
    314: 003ada93  srli         x21, x21, 3
    318: 00ba9a93  slli         x21, x21, 11
    31c: 014a8ab3  add          x21, x21, x20
    320: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000320
    324: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000338
    328: 001b9b93  slli         x23, x23, 1
    32c: 017b0b33  add          x22, x22, x23
    330: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    334: 00008067  jalr         x0, 0(x1)
    338: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    33c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    340: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    344: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_348:
    348: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    34c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    350: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    354: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    358: 015a6463  bltu         x20, x21, 0x00000360  # target 0x00000360
    35c: fedff06f  jal          x0, 0x00000348  # target 0x00000348
loc_360:
    360: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    364: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    368: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    36c: 014a1a13  slli         x20, x20, 20
    370: 014a5a13  srli         x20, x20, 20
    374: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_378:
    378: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    37c: 000b0463  beq          x22, x0, 0x00000384  # target 0x00000384
    380: ff9ff06f  jal          x0, 0x00000378  # target 0x00000378
loc_384:
    384: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    388: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    38c: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    390: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    394: 01dba623  sw           x29, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    398: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    39c: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    3a0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    3a4: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    3a8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    3ac: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    3b0: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    3b4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3b8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    3bc: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    3c0: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    3c4: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    3c8: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    3cc: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    3d0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    3d4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3d8: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_3dc:
    3dc: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    3e0: 000b0463  beq          x22, x0, 0x000003e8  # target 0x000003e8
    3e4: ff9ff06f  jal          x0, 0x000003dc  # target 0x000003dc
loc_3e8:
    3e8: 00008067  jalr         x0, 0(x1)
loc_3ec:
    3ec: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    3f0: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x0000078c
    3f4: 007a7d13  andi         x26, x20, 7
    3f8: ff8a7a13  andi         x20, x20, -8
    3fc: 01af8ab3  add          x21, x31, x26
    400: 007afb93  andi         x23, x21, 7
    404: 003ada93  srli         x21, x21, 3
    408: 00ba9a93  slli         x21, x21, 11
    40c: 014a8ab3  add          x21, x21, x20
    410: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000410
    414: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000428
    418: 001b9b93  slli         x23, x23, 1
    41c: 017b0b33  add          x22, x22, x23
    420: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    424: 00008067  jalr         x0, 0(x1)
    428: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    42c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    430: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    434: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_438:
    438: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000438
    43c: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x00000518
loc_440:
    440: 001f1a93  slli         x21, x30, 1
    444: 014a8ab3  add          x21, x21, x20
    448: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_44c:
    44c: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    450: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb30244 · noc1_regs + 0x244
    454: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x244 · 0xffb30244
    458: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    45c: 018be463  bltu         x23, x24, 0x00000464  # target 0x00000464
    460: fedff06f  jal          x0, 0x0000044c  # target 0x0000044c
loc_464:
    464: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    468: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb30148 · noc1_regs + 0x148
    46c: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x148 · 0xffb30148
    470: 014b9b93  slli         x23, x23, 20
    474: 014bdb93  srli         x23, x23, 20
    478: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
loc_47c:
    47c: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    480: 000c8463  beq          x25, x0, 0x00000488  # target 0x00000488
    484: ff9ff06f  jal          x0, 0x0000047c  # target 0x0000047c
loc_488:
    488: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    48c: 01fd2023  sw           x31, 0(x26)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    490: 000d2223  sw           x0, 4(x26)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    494: 015d2423  sw           x21, 8(x26)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    498: 01dd2623  sw           x29, 12(x26)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    49c: 000d2823  sw           x0, 16(x26)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    4a0: 017d2a23  sw           x23, 20(x26)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    4a4: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    4a8: 01bd2c23  sw           x27, 24(x26)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    4ac: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    4b0: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    4b4: 01bd2e23  sw           x27, 28(x26)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    4b8: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4bc: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    4c0: 03bd2023  sw           x27, 32(x26)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    4c4: 020d2223  sw           x0, 36(x26)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    4c8: 020d2423  sw           x0, 40(x26)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    4cc: 020d2623  sw           x0, 44(x26)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    4d0: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    4d4: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb30040 · noc1_regs + 0x40
    4d8: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    4dc: 01bd2023  sw           x27, 0(x26)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_4e0:
    4e0: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    4e4: 000c8463  beq          x25, x0, 0x000004ec  # target 0x000004ec
    4e8: ff9ff06f  jal          x0, 0x000004e0  # target 0x000004e0
loc_4ec:
    4ec: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4f0: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    4f4: 016e8eb3  add          x29, x29, x22
    4f8: 001f0f13  addi         x30, x30, 1
    4fc: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    500: 015f1663  bne          x30, x21, 0x0000050c  # target 0x0000050c
    504: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    508: 016f8fb3  add          x31, x31, x22
loc_50c:
    50c: fffe0e13  addi         x28, x28, -1
    510: f20e18e3  bne          x28, x0, 0x00000440  # target 0x00000440
    514: 00008067  jalr         x0, 0(x1)
    518: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    51c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    520: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    524: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    528:           j FW_BRISC+4   # return to firmware, linked at install
