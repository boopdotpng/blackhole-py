# llama3 1b decode: o, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_context_decode_token, 0x784=e2e_l0_q, 0x788=e2e_x_b, 0x78c=e2e_x_a, 0xe880=e2e_q_compact, 0xe884=e2e_l0_q_row_start, 0xe888=dense_start, 0xe88c=e2e_l0_q_rows, 0xe890=dram_port
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
     20: 1cc000ef  jal          x1, 0x000001ec  # target 0x000001ec; x1 = 0x00000024
     24: 1e4000ef  jal          x1, 0x00000208  # target 0x00000208; x1 = 0x00000028
     28: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     2c: 1f8000ef  jal          x1, 0x00000224  # target 0x00000224; x1 = 0x00000030
     30: 000a8213  addi         x4, x21, 0
     34: 000b0293  addi         x5, x22, 0
     38: 00020f93  addi         x31, x4, 0
     3c: 00028f13  addi         x30, x5, 0
     40: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     44: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00011fc0
     48: 260000ef  jal          x1, 0x000002a8  # target 0x000002a8; x1 = 0x0000004c
     4c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     50: 1d4000ef  jal          x1, 0x00000224  # target 0x00000224; x1 = 0x00000054
     54: 000a8213  addi         x4, x21, 0
     58: 000b0293  addi         x5, x22, 0
     5c: 00020f93  addi         x31, x4, 0
     60: 00028f13  addi         x30, x5, 0
     64: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     68: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000127c0
     6c: 23c000ef  jal          x1, 0x000002a8  # target 0x000002a8; x1 = 0x00000070
     70: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     74: 2d8000ef  jal          x1, 0x0000034c  # target 0x0000034c; x1 = 0x00000078
     78: 000a8213  addi         x4, x21, 0
     7c: 000b0293  addi         x5, x22, 0
     80: 00020f93  addi         x31, x4, 0
     84: 00028f13  addi         x30, x5, 0
     88: 00013eb7  lui          x29, 0x00013  # x29 = 0x00013000
     8c: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000137c0
     90: 218000ef  jal          x1, 0x000002a8  # target 0x000002a8; x1 = 0x00000094
     94: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     98: 2b4000ef  jal          x1, 0x0000034c  # target 0x0000034c; x1 = 0x0000009c
     9c: 000a8213  addi         x4, x21, 0
     a0: 000b0293  addi         x5, x22, 0
     a4: 00020f93  addi         x31, x4, 0
     a8: 00028f13  addi         x30, x5, 0
     ac: 00014eb7  lui          x29, 0x00014  # x29 = 0x00014000
     b0: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00013fc0
     b4: 1f4000ef  jal          x1, 0x000002a8  # target 0x000002a8; x1 = 0x000000b8
     b8: 150000ef  jal          x1, 0x00000208  # target 0x00000208; x1 = 0x000000bc
     bc: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     c0: 88c28293  addi         x5, x5, -1908  # x5 = 0x0000e88c
     c4: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e88c
     c8: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
     cc: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
     d0: ff82f293  andi         x5, x5, -8
     d4: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
     d8: 88448493  addi         x9, x9, -1916  # x9 = 0x0000e884
     dc: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x0000e884
     e0: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
     e4: 028383b3  mul          x7, x7, x8
     e8: 0073f313  andi         x6, x7, 7
     ec: 0033d393  srli         x7, x7, 3
     f0: 00b39393  slli         x7, x7, 11
     f4: 007282b3  add          x5, x5, x7
     f8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
     fc: 00020413  addi         x8, x4, 0
loc_100:
    100: 0e83f463  bgeu         x7, x8, 0x000001e8  # target 0x000001e8
    104: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    108: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    10c: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_110:
    110: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    114: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    118: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    11c: 40a485b3  sub          x11, x9, x10
    120: 01059593  slli         x11, x11, 16
    124: 0105d593  srli         x11, x11, 16
    128: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    12c: 40b60633  sub          x12, x12, x11
    130: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    134: 00d67663  bgeu         x12, x13, 0x00000140  # target 0x00000140
    138: 0ff0000f  fence        0xf, 0xf
    13c: fd5ff06f  jal          x0, 0x00000110  # target 0x00000110
loc_140:
    140: 0ff0000f  fence        0xf, 0xf
    144: 0a8000ef  jal          x1, 0x000001ec  # target 0x000001ec; x1 = 0x00000148
    148: 0c0000ef  jal          x1, 0x00000208  # target 0x00000208; x1 = 0x0000014c
    14c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    150: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    154: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    158: 00028f93  addi         x31, x5, 0
    15c: 00030f13  addi         x30, x6, 0
    160: 00048e93  addi         x29, x9, 0
    164: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    168: 268000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x0000016c
    16c: 000f8293  addi         x5, x31, 0
    170: 000f0313  addi         x6, x30, 0
    174: 094000ef  jal          x1, 0x00000208  # target 0x00000208; x1 = 0x00000178
    178: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    17c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    180: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    184: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    188: 00a484b3  add          x9, x9, x10
    18c: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    190: fc058593  addi         x11, x11, -64  # x11 = 0x00010fc0
    194: 00b4e663  bltu         x9, x11, 0x000001a0  # target 0x000001a0
    198: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    19c: 40c484b3  sub          x9, x9, x12
loc_1a0:
    1a0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1a4: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    1a8: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1ac: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1b0: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1b4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    1b8: 00248493  addi         x9, x9, 2
    1bc: 01049493  slli         x9, x9, 16
    1c0: 0104d493  srli         x9, x9, 16
    1c4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1c8: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1cc: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1d0: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    1d4: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    1d8: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    1dc: 0ff0000f  fence        0xf, 0xf
    1e0: 00138393  addi         x7, x7, 1
    1e4: f1dff06f  jal          x0, 0x00000100  # target 0x00000100
loc_1e8:
    1e8: 3100006f  jal          x0, 0x000004f8  # target 0x000004f8
loc_1ec:
    1ec: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    1f0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    1f4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    1f8: 000a0463  beq          x20, x0, 0x00000200  # target 0x00000200
    1fc: ff1ff06f  jal          x0, 0x000001ec  # target 0x000001ec
loc_200:
    200: 0ff0000f  fence        0xf, 0xf
    204: 00008067  jalr         x0, 0(x1)
loc_208:
    208: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    20c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    210: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    214: 000a0463  beq          x20, x0, 0x0000021c  # target 0x0000021c
    218: ff1ff06f  jal          x0, 0x00000208  # target 0x00000208
loc_21c:
    21c: 0ff0000f  fence        0xf, 0xf
    220: 00008067  jalr         x0, 0(x1)
loc_224:
    224: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    228: 000aaa03  lw           x20, 0(x21)  # param e2e_context_decode_token; 0x00000780
    22c: 007a7d13  andi         x26, x20, 7
    230: ff8a7a13  andi         x20, x20, -8
    234: 01af8ab3  add          x21, x31, x26
    238: 007afb93  andi         x23, x21, 7
    23c: 003ada93  srli         x21, x21, 3
    240: 00ba9a93  slli         x21, x21, 11
    244: 014a8ab3  add          x21, x21, x20
    248: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000248
    24c: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000278
    250: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    254: 890e8e93  addi         x29, x29, -1904  # x29 = 0x0000e890
    258: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e890
    25c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    260: 03cd8db3  mul          x27, x27, x28
    264: 01bb0b33  add          x22, x22, x27
    268: 001b9b93  slli         x23, x23, 1
    26c: 017b0b33  add          x22, x22, x23
    270: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    274: 00008067  jalr         x0, 0(x1)
    278: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    27c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    280: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    284: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    288: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    28c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    290: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    294: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    298: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    29c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    2a0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    2a4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_2a8:
    2a8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2ac: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    2b0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    2b4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    2b8: 015a6463  bltu         x20, x21, 0x000002c0  # target 0x000002c0
    2bc: fedff06f  jal          x0, 0x000002a8  # target 0x000002a8
loc_2c0:
    2c0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2c4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    2c8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    2cc: 014a1a13  slli         x20, x20, 20
    2d0: 014a5a13  srli         x20, x20, 20
    2d4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_2d8:
    2d8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    2dc: 000b0463  beq          x22, x0, 0x000002e4  # target 0x000002e4
    2e0: ff9ff06f  jal          x0, 0x000002d8  # target 0x000002d8
loc_2e4:
    2e4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    2e8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    2ec: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    2f0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    2f4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    2f8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    2fc: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    300: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    304: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    308: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    30c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    310: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    314: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    318: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    31c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    320: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    324: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    328: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    32c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    330: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    334: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    338: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_33c:
    33c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    340: 000b0463  beq          x22, x0, 0x00000348  # target 0x00000348
    344: ff9ff06f  jal          x0, 0x0000033c  # target 0x0000033c
loc_348:
    348: 00008067  jalr         x0, 0(x1)
loc_34c:
    34c: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    350: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x0000078c
    354: 007a7d13  andi         x26, x20, 7
    358: ff8a7a13  andi         x20, x20, -8
    35c: 01af8ab3  add          x21, x31, x26
    360: 007afb93  andi         x23, x21, 7
    364: 003ada93  srli         x21, x21, 3
    368: 00ba9a93  slli         x21, x21, 11
    36c: 014a8ab3  add          x21, x21, x20
    370: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000370
    374: 030b0b13  addi         x22, x22, 48  # x22 = 0x000003a0
    378: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    37c: 890e8e93  addi         x29, x29, -1904  # x29 = 0x0000e890
    380: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e890
    384: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    388: 03cd8db3  mul          x27, x27, x28
    38c: 01bb0b33  add          x22, x22, x27
    390: 001b9b93  slli         x23, x23, 1
    394: 017b0b33  add          x22, x22, x23
    398: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    39c: 00008067  jalr         x0, 0(x1)
    3a0: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3a4: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3a8: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    3ac: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    3b0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3b4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3b8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    3bc: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    3c0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    3c4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3c8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3cc: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_3d0:
    3d0: 00000a17  auipc        x20, 0x00000  # x20 = 0x000003d0
    3d4: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000004c8
    3d8: 0000fcb7  lui          x25, 0x0000f  # x25 = 0x0000f000
    3dc: 890c8c93  addi         x25, x25, -1904  # x25 = 0x0000e890
    3e0: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000e890
    3e4: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    3e8: 038b8bb3  mul          x23, x23, x24
    3ec: 017a0a33  add          x20, x20, x23
loc_3f0:
    3f0: 001f1a93  slli         x21, x30, 1
    3f4: 014a8ab3  add          x21, x21, x20
    3f8: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_3fc:
    3fc: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    400: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    404: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    408: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    40c: 018be463  bltu         x23, x24, 0x00000414  # target 0x00000414
    410: fedff06f  jal          x0, 0x000003fc  # target 0x000003fc
loc_414:
    414: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    418: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    41c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    420: 014b9b93  slli         x23, x23, 20
    424: 014bdb93  srli         x23, x23, 20
    428: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_42c:
    42c: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    430: 000c8463  beq          x25, x0, 0x00000438  # target 0x00000438
    434: ff9ff06f  jal          x0, 0x0000042c  # target 0x0000042c
loc_438:
    438: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    43c: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    440: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    444: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    448: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    44c: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    450: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    454: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    458: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    45c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    460: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    464: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    468: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    46c: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    470: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    474: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    478: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    47c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    480: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    484: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    488: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    48c: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_490:
    490: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    494: 000c8463  beq          x25, x0, 0x0000049c  # target 0x0000049c
    498: ff9ff06f  jal          x0, 0x00000490  # target 0x00000490
loc_49c:
    49c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4a0: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    4a4: 016e8eb3  add          x29, x29, x22
    4a8: 001f0f13  addi         x30, x30, 1
    4ac: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    4b0: 015f1663  bne          x30, x21, 0x000004bc  # target 0x000004bc
    4b4: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    4b8: 016f8fb3  add          x31, x31, x22
loc_4bc:
    4bc: fffe0e13  addi         x28, x28, -1
    4c0: f20e18e3  bne          x28, x0, 0x000003f0  # target 0x000003f0
    4c4: 00008067  jalr         x0, 0(x1)
    4c8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4cc: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4d0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4d4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4d8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4dc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    4e4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    4e8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    4ec: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    4f4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    4f8:           j FW_BRISC+4   # return to firmware, linked at install
