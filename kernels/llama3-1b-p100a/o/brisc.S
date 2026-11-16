# llama3 1b decode: o, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_context_decode_token, 0x7c4=e2e_l0_q, 0x7c8=e2e_x_b, 0x7cc=e2e_x_a, 0x8040=e2e_q_compact, 0x8044=e2e_l0_q_row_start, 0x8048=dense_start, 0x804c=e2e_l0_q_rows, 0x8050=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00090537  lui          x10, 0x00090  # x10 = 0x00090000
      c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00090000
     10: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     14: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 1c4000ef  jal          x1, 0x000001e0  # target 0x000001e0; x1 = 0x00000020
     20: 1dc000ef  jal          x1, 0x000001fc  # target 0x000001fc; x1 = 0x00000024
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: 1f0000ef  jal          x1, 0x00000218  # target 0x00000218; x1 = 0x0000002c
     2c: 000a8213  addi         x4, x21, 0
     30: 000b0293  addi         x5, x22, 0
     34: 00020f93  addi         x31, x4, 0
     38: 00028f13  addi         x30, x5, 0
     3c: 00093eb7  lui          x29, 0x00093  # x29 = 0x00093000
     40: 25c000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x00000044
     44: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     48: 1d0000ef  jal          x1, 0x00000218  # target 0x00000218; x1 = 0x0000004c
     4c: 000a8213  addi         x4, x21, 0
     50: 000b0293  addi         x5, x22, 0
     54: 00020f93  addi         x31, x4, 0
     58: 00028f13  addi         x30, x5, 0
     5c: 00094eb7  lui          x29, 0x00094  # x29 = 0x00094000
     60: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00093800
     64: 238000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x00000068
     68: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     6c: 2d4000ef  jal          x1, 0x00000340  # target 0x00000340; x1 = 0x00000070
     70: 000a8213  addi         x4, x21, 0
     74: 000b0293  addi         x5, x22, 0
     78: 00020f93  addi         x31, x4, 0
     7c: 00028f13  addi         x30, x5, 0
     80: 00095eb7  lui          x29, 0x00095  # x29 = 0x00095000
     84: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00094800
     88: 214000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x0000008c
     8c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     90: 2b0000ef  jal          x1, 0x00000340  # target 0x00000340; x1 = 0x00000094
     94: 000a8213  addi         x4, x21, 0
     98: 000b0293  addi         x5, x22, 0
     9c: 00020f93  addi         x31, x4, 0
     a0: 00028f13  addi         x30, x5, 0
     a4: 00095eb7  lui          x29, 0x00095  # x29 = 0x00095000
     a8: 1f4000ef  jal          x1, 0x0000029c  # target 0x0000029c; x1 = 0x000000ac
     ac: 150000ef  jal          x1, 0x000001fc  # target 0x000001fc; x1 = 0x000000b0
     b0: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
     b4: 04c28293  addi         x5, x5, 76  # x5 = 0x0000804c
     b8: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000804c
     bc: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
     c0: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x000007c4
     c4: ff82f293  andi         x5, x5, -8
     c8: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
     cc: 04448493  addi         x9, x9, 68  # x9 = 0x00008044
     d0: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x00008044
     d4: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
     d8: 028383b3  mul          x7, x7, x8
     dc: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
     e0: 0283f333  remu         x6, x7, x8
     e4: 0283d3b3  divu         x7, x7, x8
     e8: 00b39393  slli         x7, x7, 11
     ec: 007282b3  add          x5, x5, x7
     f0: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
     f4: 00020413  addi         x8, x4, 0
loc_f8:
     f8: 0e83f263  bgeu         x7, x8, 0x000001dc  # target 0x000001dc
     fc: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    100: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    104: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_108:
    108: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    10c: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    110: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    114: 40a485b3  sub          x11, x9, x10
    118: 01059593  slli         x11, x11, 16
    11c: 0105d593  srli         x11, x11, 16
    120: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    124: 40b60633  sub          x12, x12, x11
    128: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    12c: 00d67663  bgeu         x12, x13, 0x00000138  # target 0x00000138
    130: 0ff0000f  fence        0xf, 0xf
    134: fd5ff06f  jal          x0, 0x00000108  # target 0x00000108
loc_138:
    138: 0ff0000f  fence        0xf, 0xf
    13c: 0a4000ef  jal          x1, 0x000001e0  # target 0x000001e0; x1 = 0x00000140
    140: 0bc000ef  jal          x1, 0x000001fc  # target 0x000001fc; x1 = 0x00000144
    144: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    148: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    14c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    150: 00028f93  addi         x31, x5, 0
    154: 00030f13  addi         x30, x6, 0
    158: 00048e93  addi         x29, x9, 0
    15c: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    160: 264000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x00000164
    164: 000f8293  addi         x5, x31, 0
    168: 000f0313  addi         x6, x30, 0
    16c: 090000ef  jal          x1, 0x000001fc  # target 0x000001fc; x1 = 0x00000170
    170: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    174: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    178: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    17c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    180: 00a484b3  add          x9, x9, x10
    184: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    188: 00b4e663  bltu         x9, x11, 0x00000194  # target 0x00000194
    18c: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    190: 40c484b3  sub          x9, x9, x12
loc_194:
    194: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    198: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    19c: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1a0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1a4: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1a8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    1ac: 00248493  addi         x9, x9, 2
    1b0: 01049493  slli         x9, x9, 16
    1b4: 0104d493  srli         x9, x9, 16
    1b8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1bc: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1c0: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1c4: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    1c8: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    1cc: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    1d0: 0ff0000f  fence        0xf, 0xf
    1d4: 00138393  addi         x7, x7, 1
    1d8: f21ff06f  jal          x0, 0x000000f8  # target 0x000000f8
loc_1dc:
    1dc: 30c0006f  jal          x0, 0x000004e8  # target 0x000004e8
loc_1e0:
    1e0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    1e4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    1e8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    1ec: 000a0463  beq          x20, x0, 0x000001f4  # target 0x000001f4
    1f0: ff1ff06f  jal          x0, 0x000001e0  # target 0x000001e0
loc_1f4:
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: 00008067  jalr         x0, 0(x1)
loc_1fc:
    1fc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    200: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    204: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    208: 000a0463  beq          x20, x0, 0x00000210  # target 0x00000210
    20c: ff1ff06f  jal          x0, 0x000001fc  # target 0x000001fc
loc_210:
    210: 0ff0000f  fence        0xf, 0xf
    214: 00008067  jalr         x0, 0(x1)
loc_218:
    218: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    21c: 000aaa03  lw           x20, 0(x21)  # param e2e_context_decode_token; 0x000007c0
    220: 007a7d13  andi         x26, x20, 7
    224: ff8a7a13  andi         x20, x20, -8
    228: 01af8ab3  add          x21, x31, x26
    22c: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    230: 038afbb3  remu         x23, x21, x24
    234: 038adab3  divu         x21, x21, x24
    238: 00ba9a93  slli         x21, x21, 11
    23c: 014a8ab3  add          x21, x21, x20
    240: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000240
    244: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000270
    248: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    24c: 050e8e93  addi         x29, x29, 80  # x29 = 0x00008050
    250: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00008050
    254: 00e00e13  addi         x28, x0, 14  # x28 = 0x0000000e
    258: 03cd8db3  mul          x27, x27, x28
    25c: 01bb0b33  add          x22, x22, x27
    260: 001b9b93  slli         x23, x23, 1
    264: 017b0b33  add          x22, x22, x23
    268: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    26c: 00008067  jalr         x0, 0(x1)
    270: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    274: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    278: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    27c: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    280: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    284: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    288: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    28c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    290: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    294: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    298: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_29c:
    29c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2a0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    2a4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    2a8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    2ac: 015a6463  bltu         x20, x21, 0x000002b4  # target 0x000002b4
    2b0: fedff06f  jal          x0, 0x0000029c  # target 0x0000029c
loc_2b4:
    2b4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2b8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    2bc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    2c0: 014a1a13  slli         x20, x20, 20
    2c4: 014a5a13  srli         x20, x20, 20
    2c8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_2cc:
    2cc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    2d0: 000b0463  beq          x22, x0, 0x000002d8  # target 0x000002d8
    2d4: ff9ff06f  jal          x0, 0x000002cc  # target 0x000002cc
loc_2d8:
    2d8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    2dc: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    2e0: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    2e4: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    2e8: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    2ec: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    2f0: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    2f4: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    2f8: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    2fc: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    300: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    304: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    308: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    30c: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    310: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    314: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    318: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    31c: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    320: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    324: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    328: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    32c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_330:
    330: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    334: 000b0463  beq          x22, x0, 0x0000033c  # target 0x0000033c
    338: ff9ff06f  jal          x0, 0x00000330  # target 0x00000330
loc_33c:
    33c: 00008067  jalr         x0, 0(x1)
loc_340:
    340: 7cc00a93  addi         x21, x0, 1996  # x21 = 0x000007cc
    344: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x000007cc
    348: 007a7d13  andi         x26, x20, 7
    34c: ff8a7a13  andi         x20, x20, -8
    350: 01af8ab3  add          x21, x31, x26
    354: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    358: 038afbb3  remu         x23, x21, x24
    35c: 038adab3  divu         x21, x21, x24
    360: 00ba9a93  slli         x21, x21, 11
    364: 014a8ab3  add          x21, x21, x20
    368: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000368
    36c: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000398
    370: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    374: 050e8e93  addi         x29, x29, 80  # x29 = 0x00008050
    378: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00008050
    37c: 00e00e13  addi         x28, x0, 14  # x28 = 0x0000000e
    380: 03cd8db3  mul          x27, x27, x28
    384: 01bb0b33  add          x22, x22, x27
    388: 001b9b93  slli         x23, x23, 1
    38c: 017b0b33  add          x22, x22, x23
    390: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    394: 00008067  jalr         x0, 0(x1)
    398: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    39c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3a0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    3a4: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    3a8: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3ac: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    3b0: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    3b4: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    3b8: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3bc: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3c0: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_3c4:
    3c4: 00000a17  auipc        x20, 0x00000  # x20 = 0x000003c4
    3c8: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000004bc
    3cc: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    3d0: 050c8c93  addi         x25, x25, 80  # x25 = 0x00008050
    3d4: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x00008050
    3d8: 00e00c13  addi         x24, x0, 14  # x24 = 0x0000000e
    3dc: 038b8bb3  mul          x23, x23, x24
    3e0: 017a0a33  add          x20, x20, x23
loc_3e4:
    3e4: 001f1a93  slli         x21, x30, 1
    3e8: 014a8ab3  add          x21, x21, x20
    3ec: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_3f0:
    3f0: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    3f4: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    3f8: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    3fc: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    400: 018be463  bltu         x23, x24, 0x00000408  # target 0x00000408
    404: fedff06f  jal          x0, 0x000003f0  # target 0x000003f0
loc_408:
    408: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    40c: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    410: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    414: 014b9b93  slli         x23, x23, 20
    418: 014bdb93  srli         x23, x23, 20
    41c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_420:
    420: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    424: 000c8463  beq          x25, x0, 0x0000042c  # target 0x0000042c
    428: ff9ff06f  jal          x0, 0x00000420  # target 0x00000420
loc_42c:
    42c: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    430: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    434: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    438: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    43c: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    440: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    444: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    448: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    44c: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    450: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    454: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    458: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    45c: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    460: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    464: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    468: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    46c: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    470: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    474: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    478: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    47c: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    480: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_484:
    484: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    488: 000c8463  beq          x25, x0, 0x00000490  # target 0x00000490
    48c: ff9ff06f  jal          x0, 0x00000484  # target 0x00000484
loc_490:
    490: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    494: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    498: 016e8eb3  add          x29, x29, x22
    49c: 001f0f13  addi         x30, x30, 1
    4a0: 00700a93  addi         x21, x0, 7  # x21 = 0x00000007
    4a4: 015f1663  bne          x30, x21, 0x000004b0  # target 0x000004b0
    4a8: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    4ac: 016f8fb3  add          x31, x31, x22
loc_4b0:
    4b0: fffe0e13  addi         x28, x28, -1
    4b4: f20e18e3  bne          x28, x0, 0x000003e4  # target 0x000003e4
    4b8: 00008067  jalr         x0, 0(x1)
    4bc: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4c0: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4c4: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4c8: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4cc: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4d0: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    4d4: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    4d8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    4dc: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    4e4: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    4e8:           j FW_BRISC+4   # return to firmware, linked at install
