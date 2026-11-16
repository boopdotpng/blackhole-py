# llama3 1b decode: down, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (40): 7,2 10,2 11,2 12,2 13,2 7,3 10,3 11,3 12,3 13,3 7,4 10,4 11,4 12,4 13,4 7,5 10,5 11,5 12,5 13,5 7,6 10,6 11,6 12,6 13,6 7,7 10,7 11,7 12,7 13,7 7,8 10,8 11,8 12,8 13,8 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_hidden_dense_decode_token, 0x7c4=e2e_l0_down, 0x7c8=e2e_x_a, 0x7cc=e2e_x_b, 0x8140=e2e_q_compact, 0x8144=e2e_l0_down_row_start, 0x8148=dense_start, 0x814c=e2e_l0_down_rows
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00090537  lui          x10, 0x00090  # x10 = 0x00090000
      c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00090000
     10: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     14: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 290000ef  jal          x1, 0x000002ac  # target 0x000002ac; x1 = 0x00000020
     20: 2a8000ef  jal          x1, 0x000002c8  # target 0x000002c8; x1 = 0x00000024
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: 2bc000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x0000002c
     2c: 000a8213  addi         x4, x21, 0
     30: 000b0293  addi         x5, x22, 0
     34: 00020f93  addi         x31, x4, 0
     38: 00028f13  addi         x30, x5, 0
     3c: 00099eb7  lui          x29, 0x00099  # x29 = 0x00099000
     40: 2f4000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x00000044
     44: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     48: 29c000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x0000004c
     4c: 000a8213  addi         x4, x21, 0
     50: 000b0293  addi         x5, x22, 0
     54: 00020f93  addi         x31, x4, 0
     58: 00028f13  addi         x30, x5, 0
     5c: 0009aeb7  lui          x29, 0x0009a  # x29 = 0x0009a000
     60: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00099800
     64: 2d0000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x00000068
     68: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     6c: 278000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x00000070
     70: 000a8213  addi         x4, x21, 0
     74: 000b0293  addi         x5, x22, 0
     78: 00020f93  addi         x31, x4, 0
     7c: 00028f13  addi         x30, x5, 0
     80: 0009aeb7  lui          x29, 0x0009a  # x29 = 0x0009a000
     84: 2b0000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x00000088
     88: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     8c: 258000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 0009beb7  lui          x29, 0x0009b  # x29 = 0x0009b000
     a4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009a800
     a8: 28c000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x000000ac
     ac: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
     b0: 234000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 0009beb7  lui          x29, 0x0009b  # x29 = 0x0009b000
     c8: 26c000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x000000cc
     cc: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
     d0: 214000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x000000d4
     d4: 000a8213  addi         x4, x21, 0
     d8: 000b0293  addi         x5, x22, 0
     dc: 00020f93  addi         x31, x4, 0
     e0: 00028f13  addi         x30, x5, 0
     e4: 0009ceb7  lui          x29, 0x0009c  # x29 = 0x0009c000
     e8: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009b800
     ec: 248000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x000000f0
     f0: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
     f4: 1f0000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x000000f8
     f8: 000a8213  addi         x4, x21, 0
     fc: 000b0293  addi         x5, x22, 0
    100: 00020f93  addi         x31, x4, 0
    104: 00028f13  addi         x30, x5, 0
    108: 0009ceb7  lui          x29, 0x0009c  # x29 = 0x0009c000
    10c: 228000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x00000110
    110: 00700f93  addi         x31, x0, 7  # x31 = 0x00000007
    114: 1d0000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x00000118
    118: 000a8213  addi         x4, x21, 0
    11c: 000b0293  addi         x5, x22, 0
    120: 00020f93  addi         x31, x4, 0
    124: 00028f13  addi         x30, x5, 0
    128: 0009deb7  lui          x29, 0x0009d  # x29 = 0x0009d000
    12c: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009c800
    130: 204000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x00000134
    134: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    138: 2a0000ef  jal          x1, 0x000003d8  # target 0x000003d8; x1 = 0x0000013c
    13c: 000a8213  addi         x4, x21, 0
    140: 000b0293  addi         x5, x22, 0
    144: 00020f93  addi         x31, x4, 0
    148: 00028f13  addi         x30, x5, 0
    14c: 0009eeb7  lui          x29, 0x0009e  # x29 = 0x0009e000
    150: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009d800
    154: 1e0000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x00000158
    158: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    15c: 27c000ef  jal          x1, 0x000003d8  # target 0x000003d8; x1 = 0x00000160
    160: 000a8213  addi         x4, x21, 0
    164: 000b0293  addi         x5, x22, 0
    168: 00020f93  addi         x31, x4, 0
    16c: 00028f13  addi         x30, x5, 0
    170: 0009eeb7  lui          x29, 0x0009e  # x29 = 0x0009e000
    174: 1c0000ef  jal          x1, 0x00000334  # target 0x00000334; x1 = 0x00000178
    178: 150000ef  jal          x1, 0x000002c8  # target 0x000002c8; x1 = 0x0000017c
    17c: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    180: 14c28293  addi         x5, x5, 332  # x5 = 0x0000814c
    184: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000814c
    188: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
    18c: 0003a283  lw           x5, 0(x7)  # param e2e_l0_down; 0x000007c4
    190: ff82f293  andi         x5, x5, -8
    194: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    198: 14448493  addi         x9, x9, 324  # x9 = 0x00008144
    19c: 0004a383  lw           x7, 0(x9)  # param e2e_l0_down_row_start; 0x00008144
    1a0: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
    1a4: 028383b3  mul          x7, x7, x8
    1a8: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
    1ac: 0283f333  remu         x6, x7, x8
    1b0: 0283d3b3  divu         x7, x7, x8
    1b4: 00b39393  slli         x7, x7, 11
    1b8: 007282b3  add          x5, x5, x7
    1bc: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1c0: 00020413  addi         x8, x4, 0
loc_1c4:
    1c4: 0e83f263  bgeu         x7, x8, 0x000002a8  # target 0x000002a8
    1c8: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1cc: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    1d0: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_1d4:
    1d4: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1d8: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1dc: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1e0: 40a485b3  sub          x11, x9, x10
    1e4: 01059593  slli         x11, x11, 16
    1e8: 0105d593  srli         x11, x11, 16
    1ec: 01000613  addi         x12, x0, 16  # x12 = 0x00000010
    1f0: 40b60633  sub          x12, x12, x11
    1f4: 00800693  addi         x13, x0, 8  # x13 = 0x00000008
    1f8: 00d67663  bgeu         x12, x13, 0x00000204  # target 0x00000204
    1fc: 0ff0000f  fence        0xf, 0xf
    200: fd5ff06f  jal          x0, 0x000001d4  # target 0x000001d4
loc_204:
    204: 0ff0000f  fence        0xf, 0xf
    208: 0a4000ef  jal          x1, 0x000002ac  # target 0x000002ac; x1 = 0x0000020c
    20c: 0bc000ef  jal          x1, 0x000002c8  # target 0x000002c8; x1 = 0x00000210
    210: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    214: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    218: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    21c: 00028f93  addi         x31, x5, 0
    220: 00030f13  addi         x30, x6, 0
    224: 00048e93  addi         x29, x9, 0
    228: 00800e13  addi         x28, x0, 8  # x28 = 0x00000008
    22c: 1fc000ef  jal          x1, 0x00000428  # target 0x00000428; x1 = 0x00000230
    230: 000f8293  addi         x5, x31, 0
    234: 000f0313  addi         x6, x30, 0
    238: 090000ef  jal          x1, 0x000002c8  # target 0x000002c8; x1 = 0x0000023c
    23c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    240: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    244: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    248: 00004537  lui          x10, 0x00004  # x10 = 0x00004000
    24c: 00a484b3  add          x9, x9, x10
    250: 000985b7  lui          x11, 0x00098  # x11 = 0x00098000
    254: 00b4e663  bltu         x9, x11, 0x00000260  # target 0x00000260
    258: 00008637  lui          x12, 0x00008  # x12 = 0x00008000
    25c: 40c484b3  sub          x9, x9, x12
loc_260:
    260: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    264: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    268: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    26c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    270: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    274: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    278: 00848493  addi         x9, x9, 8
    27c: 01049493  slli         x9, x9, 16
    280: 0104d493  srli         x9, x9, 16
    284: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    288: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    28c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    290: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    294: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    298: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    29c: 0ff0000f  fence        0xf, 0xf
    2a0: 00138393  addi         x7, x7, 1
    2a4: f21ff06f  jal          x0, 0x000001c4  # target 0x000001c4
loc_2a8:
    2a8: 2700006f  jal          x0, 0x00000518  # target 0x00000518
loc_2ac:
    2ac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2b0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    2b4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    2b8: 000a0463  beq          x20, x0, 0x000002c0  # target 0x000002c0
    2bc: ff1ff06f  jal          x0, 0x000002ac  # target 0x000002ac
loc_2c0:
    2c0: 0ff0000f  fence        0xf, 0xf
    2c4: 00008067  jalr         x0, 0(x1)
loc_2c8:
    2c8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2cc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    2d0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    2d4: 000a0463  beq          x20, x0, 0x000002dc  # target 0x000002dc
    2d8: ff1ff06f  jal          x0, 0x000002c8  # target 0x000002c8
loc_2dc:
    2dc: 0ff0000f  fence        0xf, 0xf
    2e0: 00008067  jalr         x0, 0(x1)
loc_2e4:
    2e4: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    2e8: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense_decode_token; 0x000007c0
    2ec: 007a7d13  andi         x26, x20, 7
    2f0: ff8a7a13  andi         x20, x20, -8
    2f4: 01af8ab3  add          x21, x31, x26
    2f8: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    2fc: 038afbb3  remu         x23, x21, x24
    300: 038adab3  divu         x21, x21, x24
    304: 00ba9a93  slli         x21, x21, 11
    308: 014a8ab3  add          x21, x21, x20
    30c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000030c
    310: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000324
    314: 001b9b93  slli         x23, x23, 1
    318: 017b0b33  add          x22, x22, x23
    31c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    320: 00008067  jalr         x0, 0(x1)
    324: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    328: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    32c: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    330: 000004d2  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_334:
    334: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    338: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    33c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    340: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    344: 015a6463  bltu         x20, x21, 0x0000034c  # target 0x0000034c
    348: fedff06f  jal          x0, 0x00000334  # target 0x00000334
loc_34c:
    34c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    350: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    354: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    358: 014a1a13  slli         x20, x20, 20
    35c: 014a5a13  srli         x20, x20, 20
    360: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_364:
    364: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    368: 000b0463  beq          x22, x0, 0x00000370  # target 0x00000370
    36c: ff9ff06f  jal          x0, 0x00000364  # target 0x00000364
loc_370:
    370: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    374: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    378: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    37c: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    380: 01dba623  sw           x29, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    384: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    388: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    38c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    390: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    394: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    398: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    39c: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    3a0: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3a4: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    3a8: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    3ac: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    3b0: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    3b4: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    3b8: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    3bc: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    3c0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3c4: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_3c8:
    3c8: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    3cc: 000b0463  beq          x22, x0, 0x000003d4  # target 0x000003d4
    3d0: ff9ff06f  jal          x0, 0x000003c8  # target 0x000003c8
loc_3d4:
    3d4: 00008067  jalr         x0, 0(x1)
loc_3d8:
    3d8: 7cc00a93  addi         x21, x0, 1996  # x21 = 0x000007cc
    3dc: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x000007cc
    3e0: 007a7d13  andi         x26, x20, 7
    3e4: ff8a7a13  andi         x20, x20, -8
    3e8: 01af8ab3  add          x21, x31, x26
    3ec: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    3f0: 038afbb3  remu         x23, x21, x24
    3f4: 038adab3  divu         x21, x21, x24
    3f8: 00ba9a93  slli         x21, x21, 11
    3fc: 014a8ab3  add          x21, x21, x20
    400: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000400
    404: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000418
    408: 001b9b93  slli         x23, x23, 1
    40c: 017b0b33  add          x22, x22, x23
    410: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    414: 00008067  jalr         x0, 0(x1)
    418: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    41c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    420: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    424: 000004d2  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_428:
    428: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000428
    42c: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x00000508
loc_430:
    430: 001f1a93  slli         x21, x30, 1
    434: 014a8ab3  add          x21, x21, x20
    438: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_43c:
    43c: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    440: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb30244 · noc1_regs + 0x244
    444: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x244 · 0xffb30244
    448: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    44c: 018be463  bltu         x23, x24, 0x00000454  # target 0x00000454
    450: fedff06f  jal          x0, 0x0000043c  # target 0x0000043c
loc_454:
    454: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    458: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb30148 · noc1_regs + 0x148
    45c: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x148 · 0xffb30148
    460: 014b9b93  slli         x23, x23, 20
    464: 014bdb93  srli         x23, x23, 20
    468: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
loc_46c:
    46c: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    470: 000c8463  beq          x25, x0, 0x00000478  # target 0x00000478
    474: ff9ff06f  jal          x0, 0x0000046c  # target 0x0000046c
loc_478:
    478: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    47c: 01fd2023  sw           x31, 0(x26)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    480: 000d2223  sw           x0, 4(x26)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    484: 015d2423  sw           x21, 8(x26)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    488: 01dd2623  sw           x29, 12(x26)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    48c: 000d2823  sw           x0, 16(x26)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    490: 017d2a23  sw           x23, 20(x26)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    494: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    498: 01bd2c23  sw           x27, 24(x26)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    49c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    4a0: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    4a4: 01bd2e23  sw           x27, 28(x26)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    4a8: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4ac: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    4b0: 03bd2023  sw           x27, 32(x26)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    4b4: 020d2223  sw           x0, 36(x26)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    4b8: 020d2423  sw           x0, 40(x26)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    4bc: 020d2623  sw           x0, 44(x26)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    4c0: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    4c4: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb30040 · noc1_regs + 0x40
    4c8: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    4cc: 01bd2023  sw           x27, 0(x26)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_4d0:
    4d0: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    4d4: 000c8463  beq          x25, x0, 0x000004dc  # target 0x000004dc
    4d8: ff9ff06f  jal          x0, 0x000004d0  # target 0x000004d0
loc_4dc:
    4dc: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4e0: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    4e4: 016e8eb3  add          x29, x29, x22
    4e8: 001f0f13  addi         x30, x30, 1
    4ec: 00700a93  addi         x21, x0, 7  # x21 = 0x00000007
    4f0: 015f1663  bne          x30, x21, 0x000004fc  # target 0x000004fc
    4f4: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    4f8: 016f8fb3  add          x31, x31, x22
loc_4fc:
    4fc: fffe0e13  addi         x28, x28, -1
    500: f20e18e3  bne          x28, x0, 0x00000430  # target 0x00000430
    504: 00008067  jalr         x0, 0(x1)
    508: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    50c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    510: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    514: 000004d2  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    518:           j FW_BRISC+4   # return to firmware, linked at install
