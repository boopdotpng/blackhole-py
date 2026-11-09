# llama3 1B decode: down, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (30): 7,4 10,4 11,4 12,4 13,4 7,5 10,5 11,5 12,5 13,5 14,5 7,6 10,6 11,6 12,6 13,6 14,6 7,7 10,7 11,7 12,7 13,7 14,7 7,8 10,8 11,8 12,8 13,8 14,8 7,9
# params: 0x7c0=e2e_hidden_dense_decode_token, 0x7c4=e2e_l0_down, 0x7c8=e2e_x_a, 0x7cc=e2e_x_b, 0x8140=e2e_q_compact, 0x8144=e2e_l0_down_row_start, 0x8148=dense_start
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
      4: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000904b7  lui          x9, 0x00090  # x9 = 0x00090000
      c: 00942023  sw           x9, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00090000
     10: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     14: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00042023  sw           x0, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 280000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x00000020
     20: 298000ef  jal          x1, 0x000002b8  # target 0x000002b8; x1 = 0x00000024
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: 2ac000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x0000002c
     2c: 000a8213  addi         x4, x21, 0
     30: 000b0293  addi         x5, x22, 0
     34: 00020f93  addi         x31, x4, 0
     38: 00028f13  addi         x30, x5, 0
     3c: 00099eb7  lui          x29, 0x00099  # x29 = 0x00099000
     40: 2e0000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000044
     44: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     48: 28c000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x0000004c
     4c: 000a8213  addi         x4, x21, 0
     50: 000b0293  addi         x5, x22, 0
     54: 00020f93  addi         x31, x4, 0
     58: 00028f13  addi         x30, x5, 0
     5c: 0009aeb7  lui          x29, 0x0009a  # x29 = 0x0009a000
     60: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00099800
     64: 2bc000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000068
     68: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     6c: 268000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x00000070
     70: 000a8213  addi         x4, x21, 0
     74: 000b0293  addi         x5, x22, 0
     78: 00020f93  addi         x31, x4, 0
     7c: 00028f13  addi         x30, x5, 0
     80: 0009aeb7  lui          x29, 0x0009a  # x29 = 0x0009a000
     84: 29c000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000088
     88: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     8c: 248000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 0009beb7  lui          x29, 0x0009b  # x29 = 0x0009b000
     a4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009a800
     a8: 278000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x000000ac
     ac: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
     b0: 224000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 0009beb7  lui          x29, 0x0009b  # x29 = 0x0009b000
     c8: 258000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x000000cc
     cc: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
     d0: 204000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x000000d4
     d4: 000a8213  addi         x4, x21, 0
     d8: 000b0293  addi         x5, x22, 0
     dc: 00020f93  addi         x31, x4, 0
     e0: 00028f13  addi         x30, x5, 0
     e4: 0009ceb7  lui          x29, 0x0009c  # x29 = 0x0009c000
     e8: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009b800
     ec: 234000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x000000f0
     f0: 00600f93  addi         x31, x0, 6  # x31 = 0x00000006
     f4: 1e0000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x000000f8
     f8: 000a8213  addi         x4, x21, 0
     fc: 000b0293  addi         x5, x22, 0
    100: 00020f93  addi         x31, x4, 0
    104: 00028f13  addi         x30, x5, 0
    108: 0009ceb7  lui          x29, 0x0009c  # x29 = 0x0009c000
    10c: 214000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000110
    110: 00700f93  addi         x31, x0, 7  # x31 = 0x00000007
    114: 1c0000ef  jal          x1, 0x000002d4  # target 0x000002d4; x1 = 0x00000118
    118: 000a8213  addi         x4, x21, 0
    11c: 000b0293  addi         x5, x22, 0
    120: 00020f93  addi         x31, x4, 0
    124: 00028f13  addi         x30, x5, 0
    128: 0009deb7  lui          x29, 0x0009d  # x29 = 0x0009d000
    12c: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009c800
    130: 1f0000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000134
    134: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    138: 28c000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x0000013c
    13c: 000a8213  addi         x4, x21, 0
    140: 000b0293  addi         x5, x22, 0
    144: 00020f93  addi         x31, x4, 0
    148: 00028f13  addi         x30, x5, 0
    14c: 0009eeb7  lui          x29, 0x0009e  # x29 = 0x0009e000
    150: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0009d800
    154: 1cc000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000158
    158: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    15c: 268000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x00000160
    160: 000a8213  addi         x4, x21, 0
    164: 000b0293  addi         x5, x22, 0
    168: 00020f93  addi         x31, x4, 0
    16c: 00028f13  addi         x30, x5, 0
    170: 0009eeb7  lui          x29, 0x0009e  # x29 = 0x0009e000
    174: 1ac000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000178
    178: 140000ef  jal          x1, 0x000002b8  # target 0x000002b8; x1 = 0x0000017c
    17c: 7c400313  addi         x6, x0, 1988  # x6 = 0x000007c4
    180: 00032203  lw           x4, 0(x6)  # param e2e_l0_down; 0x000007c4
    184: ff827213  andi         x4, x4, -8
    188: 00008437  lui          x8, 0x00008  # x8 = 0x00008000
    18c: 14440413  addi         x8, x8, 324  # x8 = 0x00008144
    190: 00042303  lw           x6, 0(x8)  # param e2e_l0_down_row_start; 0x00008144
    194: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
    198: 02730333  mul          x6, x6, x7
    19c: 00737293  andi         x5, x6, 7
    1a0: 00335313  srli         x6, x6, 3
    1a4: 00b31313  slli         x6, x6, 11
    1a8: 00620233  add          x4, x4, x6
    1ac: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    1b0: 01700393  addi         x7, x0, 23  # x7 = 0x00000017
loc_1b4:
    1b4: 0e737263  bgeu         x6, x7, 0x00000298  # target 0x00000298
    1b8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1bc: 87c68693  addi         x13, x13, -1924  # x13 = 0xffb0087c · riscv_local_mem + 0x87c
    1c0: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_1c4:
    1c4: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
    1c8: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    1cc: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    1d0: 40940533  sub          x10, x8, x9
    1d4: 01051513  slli         x10, x10, 16
    1d8: 01055513  srli         x10, x10, 16
    1dc: 01000593  addi         x11, x0, 16  # x11 = 0x00000010
    1e0: 40a585b3  sub          x11, x11, x10
    1e4: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    1e8: 00c5f663  bgeu         x11, x12, 0x000001f4  # target 0x000001f4
    1ec: 0ff0000f  fence        0xf, 0xf
    1f0: fd5ff06f  jal          x0, 0x000001c4  # target 0x000001c4
loc_1f4:
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: 0a4000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x000001fc
    1fc: 0bc000ef  jal          x1, 0x000002b8  # target 0x000002b8; x1 = 0x00000200
    200: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    204: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
    208: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878
    20c: 00020f93  addi         x31, x4, 0
    210: 00028f13  addi         x30, x5, 0
    214: 00040e93  addi         x29, x8, 0
    218: 00800e13  addi         x28, x0, 8  # x28 = 0x00000008
    21c: 1f4000ef  jal          x1, 0x00000410  # target 0x00000410; x1 = 0x00000220
    220: 000f8213  addi         x4, x31, 0
    224: 000f0293  addi         x5, x30, 0
    228: 090000ef  jal          x1, 0x000002b8  # target 0x000002b8; x1 = 0x0000022c
    22c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    230: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    234: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    238: 000044b7  lui          x9, 0x00004  # x9 = 0x00004000
    23c: 00940433  add          x8, x8, x9
    240: 00098537  lui          x10, 0x00098  # x10 = 0x00098000
    244: 00a46663  bltu         x8, x10, 0x00000250  # target 0x00000250
    248: 000085b7  lui          x11, 0x00008  # x11 = 0x00008000
    24c: 40b40433  sub          x8, x8, x11
loc_250:
    250: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    254: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    258: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    25c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    260: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    264: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
    268: 00840413  addi         x8, x8, 8
    26c: 01041413  slli         x8, x8, 16
    270: 01045413  srli         x8, x8, 16
    274: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    278: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    27c: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    280: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    284: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    288: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    28c: 0ff0000f  fence        0xf, 0xf
    290: 00130313  addi         x6, x6, 1
    294: f21ff06f  jal          x0, 0x000001b4  # target 0x000001b4
loc_298:
    298: 2680006f  jal          x0, 0x00000500  # target 0x00000500
loc_29c:
    29c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2a0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    2a4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    2a8: 000a0463  beq          x20, x0, 0x000002b0  # target 0x000002b0
    2ac: ff1ff06f  jal          x0, 0x0000029c  # target 0x0000029c
loc_2b0:
    2b0: 0ff0000f  fence        0xf, 0xf
    2b4: 00008067  jalr         x0, 0(x1)
loc_2b8:
    2b8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2bc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    2c0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    2c4: 000a0463  beq          x20, x0, 0x000002cc  # target 0x000002cc
    2c8: ff1ff06f  jal          x0, 0x000002b8  # target 0x000002b8
loc_2cc:
    2cc: 0ff0000f  fence        0xf, 0xf
    2d0: 00008067  jalr         x0, 0(x1)
loc_2d4:
    2d4: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    2d8: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense_decode_token; 0x000007c0
    2dc: 007a7d13  andi         x26, x20, 7
    2e0: ff8a7a13  andi         x20, x20, -8
    2e4: 01af8ab3  add          x21, x31, x26
    2e8: 007afb93  andi         x23, x21, 7
    2ec: 003ada93  srli         x21, x21, 3
    2f0: 00ba9a93  slli         x21, x21, 11
    2f4: 014a8ab3  add          x21, x21, x20
    2f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000002f8
    2fc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000310
    300: 001b9b93  slli         x23, x23, 1
    304: 017b0b33  add          x22, x22, x23
    308: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    30c: 00008067  jalr         x0, 0(x1)
    310: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    314: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    318: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    31c: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_320:
    320: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    324: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    328: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    32c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    330: 015a6463  bltu         x20, x21, 0x00000338  # target 0x00000338
    334: fedff06f  jal          x0, 0x00000320  # target 0x00000320
loc_338:
    338: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    33c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    340: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    344: 014a1a13  slli         x20, x20, 20
    348: 014a5a13  srli         x20, x20, 20
    34c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_350:
    350: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    354: 000b0463  beq          x22, x0, 0x0000035c  # target 0x0000035c
    358: ff9ff06f  jal          x0, 0x00000350  # target 0x00000350
loc_35c:
    35c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    360: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    364: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    368: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    36c: 01dba623  sw           x29, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    370: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    374: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    378: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    37c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    380: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    384: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    388: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    38c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    390: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    394: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    398: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    39c: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    3a0: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    3a4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    3a8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    3ac: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3b0: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_3b4:
    3b4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    3b8: 000b0463  beq          x22, x0, 0x000003c0  # target 0x000003c0
    3bc: ff9ff06f  jal          x0, 0x000003b4  # target 0x000003b4
loc_3c0:
    3c0: 00008067  jalr         x0, 0(x1)
loc_3c4:
    3c4: 7cc00a93  addi         x21, x0, 1996  # x21 = 0x000007cc
    3c8: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x000007cc
    3cc: 007a7d13  andi         x26, x20, 7
    3d0: ff8a7a13  andi         x20, x20, -8
    3d4: 01af8ab3  add          x21, x31, x26
    3d8: 007afb93  andi         x23, x21, 7
    3dc: 003ada93  srli         x21, x21, 3
    3e0: 00ba9a93  slli         x21, x21, 11
    3e4: 014a8ab3  add          x21, x21, x20
    3e8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000003e8
    3ec: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000400
    3f0: 001b9b93  slli         x23, x23, 1
    3f4: 017b0b33  add          x22, x22, x23
    3f8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    3fc: 00008067  jalr         x0, 0(x1)
    400: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    404: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    408: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    40c: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_410:
    410: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000410
    414: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x000004f0
loc_418:
    418: 001f1a93  slli         x21, x30, 1
    41c: 014a8ab3  add          x21, x21, x20
    420: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_424:
    424: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    428: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb30244 · noc1_regs + 0x244
    42c: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x244 · 0xffb30244
    430: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    434: 018be463  bltu         x23, x24, 0x0000043c  # target 0x0000043c
    438: fedff06f  jal          x0, 0x00000424  # target 0x00000424
loc_43c:
    43c: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
    440: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb30148 · noc1_regs + 0x148
    444: 000c2b83  lw           x23, 0(x24)  # noc1_regs + 0x148 · 0xffb30148
    448: 014b9b93  slli         x23, x23, 20
    44c: 014bdb93  srli         x23, x23, 20
    450: ffb30c37  lui          x24, 0xffb30  # x24 = 0xffb30000 · noc1_regs + 0x0
loc_454:
    454: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    458: 000c8463  beq          x25, x0, 0x00000460  # target 0x00000460
    45c: ff9ff06f  jal          x0, 0x00000454  # target 0x00000454
loc_460:
    460: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    464: 01fd2023  sw           x31, 0(x26)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    468: 000d2223  sw           x0, 4(x26)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    46c: 015d2423  sw           x21, 8(x26)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    470: 01dd2623  sw           x29, 12(x26)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    474: 000d2823  sw           x0, 16(x26)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    478: 017d2a23  sw           x23, 20(x26)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    47c: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    480: 01bd2c23  sw           x27, 24(x26)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    484: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    488: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    48c: 01bd2e23  sw           x27, 28(x26)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002090
    490: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    494: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    498: 03bd2023  sw           x27, 32(x26)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    49c: 020d2223  sw           x0, 36(x26)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    4a0: 020d2423  sw           x0, 40(x26)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    4a4: 020d2623  sw           x0, 44(x26)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    4a8: ffb30d37  lui          x26, 0xffb30  # x26 = 0xffb30000 · noc1_regs + 0x0
    4ac: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb30040 · noc1_regs + 0x40
    4b0: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    4b4: 01bd2023  sw           x27, 0(x26)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_4b8:
    4b8: 040c2c83  lw           x25, 64(x24)  # noc1_regs + 0x40 · 0xffb30040
    4bc: 000c8463  beq          x25, x0, 0x000004c4  # target 0x000004c4
    4c0: ff9ff06f  jal          x0, 0x000004b8  # target 0x000004b8
loc_4c4:
    4c4: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4c8: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    4cc: 016e8eb3  add          x29, x29, x22
    4d0: 001f0f13  addi         x30, x30, 1
    4d4: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    4d8: 015f1663  bne          x30, x21, 0x000004e4  # target 0x000004e4
    4dc: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    4e0: 016f8fb3  add          x31, x31, x22
loc_4e4:
    4e4: fffe0e13  addi         x28, x28, -1
    4e8: f20e18e3  bne          x28, x0, 0x00000418  # target 0x00000418
    4ec: 00008067  jalr         x0, 0(x1)
    4f0: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f4: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f8: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4fc: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    500:           j FW_BRISC+4   # return to firmware, linked at install
