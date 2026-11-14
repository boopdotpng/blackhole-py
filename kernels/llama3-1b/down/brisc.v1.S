# llama3 1b decode: down, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (40): 7,2 10,2 11,2 12,2 13,2 7,3 10,3 11,3 12,3 13,3 7,4 10,4 11,4 12,4 13,4 7,5 10,5 11,5 12,5 13,5 7,6 10,6 11,6 12,6 13,6 7,7 10,7 11,7 12,7 13,7 7,8 10,8 11,8 12,8 13,8 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_hidden_dense_decode_token, 0x784=e2e_l0_down, 0x788=e2e_x_a, 0x78c=e2e_x_b, 0x11980=e2e_q_compact, 0x11984=e2e_l0_down_row_start, 0x11988=dense_start, 0x1198c=e2e_l0_down_rows
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
      c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00012000
     10: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     14: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 28c000ef  jal          x1, 0x000002a8  # target 0x000002a8; x1 = 0x00000020
     20: 2a4000ef  jal          x1, 0x000002c4  # target 0x000002c4; x1 = 0x00000024
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: 2b8000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x0000002c
     2c: 000a8213  addi         x4, x21, 0
     30: 000b0293  addi         x5, x22, 0
     34: 00020f93  addi         x31, x4, 0
     38: 00028f13  addi         x30, x5, 0
     3c: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
     40: 2ec000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x00000044
     44: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     48: 298000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x0000004c
     4c: 000a8213  addi         x4, x21, 0
     50: 000b0293  addi         x5, x22, 0
     54: 00020f93  addi         x31, x4, 0
     58: 00028f13  addi         x30, x5, 0
     5c: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
     60: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001b800
     64: 2c8000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x00000068
     68: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     6c: 274000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x00000070
     70: 000a8213  addi         x4, x21, 0
     74: 000b0293  addi         x5, x22, 0
     78: 00020f93  addi         x31, x4, 0
     7c: 00028f13  addi         x30, x5, 0
     80: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
     84: 2a8000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x00000088
     88: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     8c: 254000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
     a4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001c800
     a8: 284000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x000000ac
     ac: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
     b0: 230000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
     c8: 264000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x000000cc
     cc: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
     d0: 210000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x000000d4
     d4: 000a8213  addi         x4, x21, 0
     d8: 000b0293  addi         x5, x22, 0
     dc: 00020f93  addi         x31, x4, 0
     e0: 00028f13  addi         x30, x5, 0
     e4: 0001eeb7  lui          x29, 0x0001e  # x29 = 0x0001e000
     e8: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001d800
     ec: 240000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x000000f0
     f0: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
     f4: 1ec000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x000000f8
     f8: 000a8213  addi         x4, x21, 0
     fc: 000b0293  addi         x5, x22, 0
    100: 00020f93  addi         x31, x4, 0
    104: 00028f13  addi         x30, x5, 0
    108: 0001eeb7  lui          x29, 0x0001e  # x29 = 0x0001e000
    10c: 220000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x00000110
    110: 00700f93  addi         x31, x0, 7  # x31 = 0x00000007
    114: 1cc000ef  jal          x1, 0x000002e0  # target 0x000002e0; x1 = 0x00000118
    118: 000a8213  addi         x4, x21, 0
    11c: 000b0293  addi         x5, x22, 0
    120: 00020f93  addi         x31, x4, 0
    124: 00028f13  addi         x30, x5, 0
    128: 0001feb7  lui          x29, 0x0001f  # x29 = 0x0001f000
    12c: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001e800
    130: 1fc000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x00000134
    134: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    138: 298000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x0000013c
    13c: 000a8213  addi         x4, x21, 0
    140: 000b0293  addi         x5, x22, 0
    144: 00020f93  addi         x31, x4, 0
    148: 00028f13  addi         x30, x5, 0
    14c: 00020eb7  lui          x29, 0x00020  # x29 = 0x00020000
    150: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001f800
    154: 1d8000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x00000158
    158: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    15c: 274000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x00000160
    160: 000a8213  addi         x4, x21, 0
    164: 000b0293  addi         x5, x22, 0
    168: 00020f93  addi         x31, x4, 0
    16c: 00028f13  addi         x30, x5, 0
    170: 00020eb7  lui          x29, 0x00020  # x29 = 0x00020000
    174: 1b8000ef  jal          x1, 0x0000032c  # target 0x0000032c; x1 = 0x00000178
    178: 14c000ef  jal          x1, 0x000002c4  # target 0x000002c4; x1 = 0x0000017c
    17c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    180: 98c28293  addi         x5, x5, -1652  # x5 = 0x0001198c
    184: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0001198c
    188: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    18c: 0003a283  lw           x5, 0(x7)  # param e2e_l0_down; 0x00000784
    190: ff82f293  andi         x5, x5, -8
    194: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    198: 98448493  addi         x9, x9, -1660  # x9 = 0x00011984
    19c: 0004a383  lw           x7, 0(x9)  # param e2e_l0_down_row_start; 0x00011984
    1a0: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
    1a4: 028383b3  mul          x7, x7, x8
    1a8: 0073f313  andi         x6, x7, 7
    1ac: 0033d393  srli         x7, x7, 3
    1b0: 00b39393  slli         x7, x7, 11
    1b4: 007282b3  add          x5, x5, x7
    1b8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1bc: 00020413  addi         x8, x4, 0
loc_1c0:
    1c0: 0e83f263  bgeu         x7, x8, 0x000002a4  # target 0x000002a4
    1c4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1c8: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    1cc: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_1d0:
    1d0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1d4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1d8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1dc: 40a485b3  sub          x11, x9, x10
    1e0: 01059593  slli         x11, x11, 16
    1e4: 0105d593  srli         x11, x11, 16
    1e8: 01000613  addi         x12, x0, 16  # x12 = 0x00000010
    1ec: 40b60633  sub          x12, x12, x11
    1f0: 00800693  addi         x13, x0, 8  # x13 = 0x00000008
    1f4: 00d67663  bgeu         x12, x13, 0x00000200  # target 0x00000200
    1f8: 0ff0000f  fence        0xf, 0xf
    1fc: fd5ff06f  jal          x0, 0x000001d0  # target 0x000001d0
loc_200:
    200: 0ff0000f  fence        0xf, 0xf
    204: 0a4000ef  jal          x1, 0x000002a8  # target 0x000002a8; x1 = 0x00000208
    208: 0bc000ef  jal          x1, 0x000002c4  # target 0x000002c4; x1 = 0x0000020c
    20c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    210: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    214: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    218: 00028f93  addi         x31, x5, 0
    21c: 00030f13  addi         x30, x6, 0
    220: 00048e93  addi         x29, x9, 0
    224: 00800e13  addi         x28, x0, 8  # x28 = 0x00000008
    228: 1f4000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x0000022c
    22c: 000f8293  addi         x5, x31, 0
    230: 000f0313  addi         x6, x30, 0
    234: 090000ef  jal          x1, 0x000002c4  # target 0x000002c4; x1 = 0x00000238
    238: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    23c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    240: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    244: 00004537  lui          x10, 0x00004  # x10 = 0x00004000
    248: 00a484b3  add          x9, x9, x10
    24c: 0001a5b7  lui          x11, 0x0001a  # x11 = 0x0001a000
    250: 00b4e663  bltu         x9, x11, 0x0000025c  # target 0x0000025c
    254: 00008637  lui          x12, 0x00008  # x12 = 0x00008000
    258: 40c484b3  sub          x9, x9, x12
loc_25c:
    25c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    260: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    264: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    268: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    26c: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    270: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    274: 00848493  addi         x9, x9, 8
    278: 01049493  slli         x9, x9, 16
    27c: 0104d493  srli         x9, x9, 16
    280: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    284: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    288: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    28c: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    290: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    294: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    298: 0ff0000f  fence        0xf, 0xf
    29c: 00138393  addi         x7, x7, 1
    2a0: f21ff06f  jal          x0, 0x000001c0  # target 0x000001c0
loc_2a4:
    2a4: 2680006f  jal          x0, 0x0000050c  # target 0x0000050c
loc_2a8:
    2a8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2ac: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    2b0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    2b4: 000a0463  beq          x20, x0, 0x000002bc  # target 0x000002bc
    2b8: ff1ff06f  jal          x0, 0x000002a8  # target 0x000002a8
loc_2bc:
    2bc: 0ff0000f  fence        0xf, 0xf
    2c0: 00008067  jalr         x0, 0(x1)
loc_2c4:
    2c4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2c8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    2cc: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    2d0: 000a0463  beq          x20, x0, 0x000002d8  # target 0x000002d8
    2d4: ff1ff06f  jal          x0, 0x000002c4  # target 0x000002c4
loc_2d8:
    2d8: 0ff0000f  fence        0xf, 0xf
    2dc: 00008067  jalr         x0, 0(x1)
loc_2e0:
    2e0: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    2e4: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense_decode_token; 0x00000780
    2e8: 007a7d13  andi         x26, x20, 7
    2ec: ff8a7a13  andi         x20, x20, -8
    2f0: 01af8ab3  add          x21, x31, x26
    2f4: 007afb93  andi         x23, x21, 7
    2f8: 003ada93  srli         x21, x21, 3
    2fc: 00ba9a93  slli         x21, x21, 11
    300: 014a8ab3  add          x21, x21, x20
    304: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000304
    308: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000031c
    30c: 001b9b93  slli         x23, x23, 1
    310: 017b0b33  add          x22, x22, x23
    314: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    318: 00008067  jalr         x0, 0(x1)
    31c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    320: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    324: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    328: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_32c:
    32c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    330: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    334: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    338: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    33c: 015a6463  bltu         x20, x21, 0x00000344  # target 0x00000344
    340: fedff06f  jal          x0, 0x0000032c  # target 0x0000032c
loc_344:
    344: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    348: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    34c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    350: 014a1a13  slli         x20, x20, 20
    354: 014a5a13  srli         x20, x20, 20
    358: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_35c:
    35c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    360: 000b0463  beq          x22, x0, 0x00000368  # target 0x00000368
    364: ff9ff06f  jal          x0, 0x0000035c  # target 0x0000035c
loc_368:
    368: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    36c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    370: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    374: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    378: 01dba623  sw           x29, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    37c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    380: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    384: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    388: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    38c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    390: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    394: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    398: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    39c: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    3a0: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    3a4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    3a8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    3ac: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    3b0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    3b4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    3b8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3bc: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_3c0:
    3c0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    3c4: 000b0463  beq          x22, x0, 0x000003cc  # target 0x000003cc
    3c8: ff9ff06f  jal          x0, 0x000003c0  # target 0x000003c0
loc_3cc:
    3cc: 00008067  jalr         x0, 0(x1)
loc_3d0:
    3d0: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    3d4: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x0000078c
    3d8: 007a7d13  andi         x26, x20, 7
    3dc: ff8a7a13  andi         x20, x20, -8
    3e0: 01af8ab3  add          x21, x31, x26
    3e4: 007afb93  andi         x23, x21, 7
    3e8: 003ada93  srli         x21, x21, 3
    3ec: 00ba9a93  slli         x21, x21, 11
    3f0: 014a8ab3  add          x21, x21, x20
    3f4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000003f4
    3f8: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000040c
    3fc: 001b9b93  slli         x23, x23, 1
    400: 017b0b33  add          x22, x22, x23
    404: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    408: 00008067  jalr         x0, 0(x1)
    40c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    410: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    414: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    418: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_41c:
    41c: 00000a17  auipc        x20, 0x00000  # x20 = 0x0000041c
    420: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x000004fc
loc_424:
    424: 001f1a93  slli         x21, x30, 1
    428: 014a8ab3  add          x21, x21, x20
    42c: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_430:
    430: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    434: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb30244 · noc1_regs + 0x244
    438: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x244 · 0xffb30244
    43c: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    440: 018be463  bltu         x23, x24, 0x00000448  # target 0x00000448
    444: fedff06f  jal          x0, 0x00000430  # target 0x00000430
loc_448:
    448: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    44c: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb30148 · noc1_regs + 0x148
    450: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x148 · 0xffb30148
    454: 014b9b93  slli         x23, x23, 20
    458: 014bdb93  srli         x23, x23, 20
    45c: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
loc_460:
    460: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    464: 000c8463  beq          x25, x0, 0x0000046c  # target 0x0000046c
    468: ff9ff06f  jal          x0, 0x00000460  # target 0x00000460
loc_46c:
    46c: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    470: 01fd2023  sw           x31, 0(x26)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    474: 000d2223  sw           x0, 4(x26)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    478: 015d2423  sw           x21, 8(x26)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    47c: 01dd2623  sw           x29, 12(x26)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    480: 000d2823  sw           x0, 16(x26)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    484: 017d2a23  sw           x23, 20(x26)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    488: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    48c: 01bd2c23  sw           x27, 24(x26)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    490: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    494: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    498: 01bd2e23  sw           x27, 28(x26)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    49c: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4a0: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    4a4: 03bd2023  sw           x27, 32(x26)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    4a8: 020d2223  sw           x0, 36(x26)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    4ac: 020d2423  sw           x0, 40(x26)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    4b0: 020d2623  sw           x0, 44(x26)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    4b4: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    4b8: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb30040 · noc1_regs + 0x40
    4bc: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    4c0: 01bd2023  sw           x27, 0(x26)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_4c4:
    4c4: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    4c8: 000c8463  beq          x25, x0, 0x000004d0  # target 0x000004d0
    4cc: ff9ff06f  jal          x0, 0x000004c4  # target 0x000004c4
loc_4d0:
    4d0: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4d4: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    4d8: 016e8eb3  add          x29, x29, x22
    4dc: 001f0f13  addi         x30, x30, 1
    4e0: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    4e4: 015f1663  bne          x30, x21, 0x000004f0  # target 0x000004f0
    4e8: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    4ec: 016f8fb3  add          x31, x31, x22
loc_4f0:
    4f0: fffe0e13  addi         x28, x28, -1
    4f4: f20e18e3  bne          x28, x0, 0x00000424  # target 0x00000424
    4f8: 00008067  jalr         x0, 0(x1)
    4fc: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    500: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    504: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    508: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    50c:           j FW_BRISC+4   # return to firmware, linked at install
