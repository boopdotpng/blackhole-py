# llama3 8b-bf16 decode: o, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
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
     20: 25c000ef  jal          x1, 0x0000027c  # target 0x0000027c; x1 = 0x00000024
     24: 274000ef  jal          x1, 0x00000298  # target 0x00000298; x1 = 0x00000028
     28: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     2c: 288000ef  jal          x1, 0x000002b4  # target 0x000002b4; x1 = 0x00000030
     30: 000a8213  addi         x4, x21, 0
     34: 000b0293  addi         x5, x22, 0
     38: 00020f93  addi         x31, x4, 0
     3c: 00028f13  addi         x30, x5, 0
     40: 00014eb7  lui          x29, 0x00014  # x29 = 0x00014000
     44: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00013fc0
     48: 2f0000ef  jal          x1, 0x00000338  # target 0x00000338; x1 = 0x0000004c
     4c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     50: 264000ef  jal          x1, 0x000002b4  # target 0x000002b4; x1 = 0x00000054
     54: 000a8213  addi         x4, x21, 0
     58: 000b0293  addi         x5, x22, 0
     5c: 00020f93  addi         x31, x4, 0
     60: 00028f13  addi         x30, x5, 0
     64: 00014eb7  lui          x29, 0x00014  # x29 = 0x00014000
     68: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000147c0
     6c: 2cc000ef  jal          x1, 0x00000338  # target 0x00000338; x1 = 0x00000070
     70: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     74: 240000ef  jal          x1, 0x000002b4  # target 0x000002b4; x1 = 0x00000078
     78: 000a8213  addi         x4, x21, 0
     7c: 000b0293  addi         x5, x22, 0
     80: 00020f93  addi         x31, x4, 0
     84: 00028f13  addi         x30, x5, 0
     88: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
     8c: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00014fc0
     90: 2a8000ef  jal          x1, 0x00000338  # target 0x00000338; x1 = 0x00000094
     94: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     98: 21c000ef  jal          x1, 0x000002b4  # target 0x000002b4; x1 = 0x0000009c
     9c: 000a8213  addi         x4, x21, 0
     a0: 000b0293  addi         x5, x22, 0
     a4: 00020f93  addi         x31, x4, 0
     a8: 00028f13  addi         x30, x5, 0
     ac: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
     b0: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000157c0
     b4: 284000ef  jal          x1, 0x00000338  # target 0x00000338; x1 = 0x000000b8
     b8: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     bc: 320000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x000000c0
     c0: 000a8213  addi         x4, x21, 0
     c4: 000b0293  addi         x5, x22, 0
     c8: 00020f93  addi         x31, x4, 0
     cc: 00028f13  addi         x30, x5, 0
     d0: 00016eb7  lui          x29, 0x00016  # x29 = 0x00016000
     d4: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000167c0
     d8: 260000ef  jal          x1, 0x00000338  # target 0x00000338; x1 = 0x000000dc
     dc: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     e0: 2fc000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x000000e4
     e4: 000a8213  addi         x4, x21, 0
     e8: 000b0293  addi         x5, x22, 0
     ec: 00020f93  addi         x31, x4, 0
     f0: 00028f13  addi         x30, x5, 0
     f4: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     f8: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00016fc0
     fc: 23c000ef  jal          x1, 0x00000338  # target 0x00000338; x1 = 0x00000100
    100: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    104: 2d8000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x00000108
    108: 000a8213  addi         x4, x21, 0
    10c: 000b0293  addi         x5, x22, 0
    110: 00020f93  addi         x31, x4, 0
    114: 00028f13  addi         x30, x5, 0
    118: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
    11c: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000177c0
    120: 218000ef  jal          x1, 0x00000338  # target 0x00000338; x1 = 0x00000124
    124: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    128: 2b4000ef  jal          x1, 0x000003dc  # target 0x000003dc; x1 = 0x0000012c
    12c: 000a8213  addi         x4, x21, 0
    130: 000b0293  addi         x5, x22, 0
    134: 00020f93  addi         x31, x4, 0
    138: 00028f13  addi         x30, x5, 0
    13c: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
    140: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00017fc0
    144: 1f4000ef  jal          x1, 0x00000338  # target 0x00000338; x1 = 0x00000148
    148: 150000ef  jal          x1, 0x00000298  # target 0x00000298; x1 = 0x0000014c
    14c: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    150: 88c28293  addi         x5, x5, -1908  # x5 = 0x0000e88c
    154: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e88c
    158: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    15c: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    160: ff82f293  andi         x5, x5, -8
    164: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    168: 88448493  addi         x9, x9, -1916  # x9 = 0x0000e884
    16c: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x0000e884
    170: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    174: 028383b3  mul          x7, x7, x8
    178: 0073f313  andi         x6, x7, 7
    17c: 0033d393  srli         x7, x7, 3
    180: 00b39393  slli         x7, x7, 11
    184: 007282b3  add          x5, x5, x7
    188: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    18c: 00020413  addi         x8, x4, 0
loc_190:
    190: 0e83f463  bgeu         x7, x8, 0x00000278  # target 0x00000278
    194: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    198: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    19c: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_1a0:
    1a0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1a4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1a8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1ac: 40a485b3  sub          x11, x9, x10
    1b0: 01059593  slli         x11, x11, 16
    1b4: 0105d593  srli         x11, x11, 16
    1b8: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    1bc: 40b60633  sub          x12, x12, x11
    1c0: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    1c4: 00d67663  bgeu         x12, x13, 0x000001d0  # target 0x000001d0
    1c8: 0ff0000f  fence        0xf, 0xf
    1cc: fd5ff06f  jal          x0, 0x000001a0  # target 0x000001a0
loc_1d0:
    1d0: 0ff0000f  fence        0xf, 0xf
    1d4: 0a8000ef  jal          x1, 0x0000027c  # target 0x0000027c; x1 = 0x000001d8
    1d8: 0c0000ef  jal          x1, 0x00000298  # target 0x00000298; x1 = 0x000001dc
    1dc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1e0: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    1e4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    1e8: 00028f93  addi         x31, x5, 0
    1ec: 00030f13  addi         x30, x6, 0
    1f0: 00048e93  addi         x29, x9, 0
    1f4: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    1f8: 268000ef  jal          x1, 0x00000460  # target 0x00000460; x1 = 0x000001fc
    1fc: 000f8293  addi         x5, x31, 0
    200: 000f0313  addi         x6, x30, 0
    204: 094000ef  jal          x1, 0x00000298  # target 0x00000298; x1 = 0x00000208
    208: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    20c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    210: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    214: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    218: 00a484b3  add          x9, x9, x10
    21c: 000135b7  lui          x11, 0x00013  # x11 = 0x00013000
    220: fc058593  addi         x11, x11, -64  # x11 = 0x00012fc0
    224: 00b4e663  bltu         x9, x11, 0x00000230  # target 0x00000230
    228: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    22c: 40c484b3  sub          x9, x9, x12
loc_230:
    230: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    234: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    238: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    23c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    240: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    244: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    248: 00448493  addi         x9, x9, 4
    24c: 01049493  slli         x9, x9, 16
    250: 0104d493  srli         x9, x9, 16
    254: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    258: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    25c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    260: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    264: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    268: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    26c: 0ff0000f  fence        0xf, 0xf
    270: 00138393  addi         x7, x7, 1
    274: f1dff06f  jal          x0, 0x00000190  # target 0x00000190
loc_278:
    278: 3100006f  jal          x0, 0x00000588  # target 0x00000588
loc_27c:
    27c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    280: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    284: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    288: 000a0463  beq          x20, x0, 0x00000290  # target 0x00000290
    28c: ff1ff06f  jal          x0, 0x0000027c  # target 0x0000027c
loc_290:
    290: 0ff0000f  fence        0xf, 0xf
    294: 00008067  jalr         x0, 0(x1)
loc_298:
    298: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    29c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    2a0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    2a4: 000a0463  beq          x20, x0, 0x000002ac  # target 0x000002ac
    2a8: ff1ff06f  jal          x0, 0x00000298  # target 0x00000298
loc_2ac:
    2ac: 0ff0000f  fence        0xf, 0xf
    2b0: 00008067  jalr         x0, 0(x1)
loc_2b4:
    2b4: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    2b8: 000aaa03  lw           x20, 0(x21)  # param e2e_context_decode_token; 0x00000780
    2bc: 007a7d13  andi         x26, x20, 7
    2c0: ff8a7a13  andi         x20, x20, -8
    2c4: 01af8ab3  add          x21, x31, x26
    2c8: 007afb93  andi         x23, x21, 7
    2cc: 003ada93  srli         x21, x21, 3
    2d0: 00ba9a93  slli         x21, x21, 11
    2d4: 014a8ab3  add          x21, x21, x20
    2d8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000002d8
    2dc: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000308
    2e0: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    2e4: 890e8e93  addi         x29, x29, -1904  # x29 = 0x0000e890
    2e8: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e890
    2ec: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    2f0: 03cd8db3  mul          x27, x27, x28
    2f4: 01bb0b33  add          x22, x22, x27
    2f8: 001b9b93  slli         x23, x23, 1
    2fc: 017b0b33  add          x22, x22, x23
    300: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    304: 00008067  jalr         x0, 0(x1)
    308: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    30c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    310: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    314: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    318: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    31c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    320: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    324: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    328: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    32c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    330: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    334: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_338:
    338: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    33c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    340: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    344: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    348: 015a6463  bltu         x20, x21, 0x00000350  # target 0x00000350
    34c: fedff06f  jal          x0, 0x00000338  # target 0x00000338
loc_350:
    350: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    354: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    358: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    35c: 014a1a13  slli         x20, x20, 20
    360: 014a5a13  srli         x20, x20, 20
    364: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_368:
    368: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    36c: 000b0463  beq          x22, x0, 0x00000374  # target 0x00000374
    370: ff9ff06f  jal          x0, 0x00000368  # target 0x00000368
loc_374:
    374: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    378: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    37c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    380: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    384: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    388: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    38c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    390: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    394: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    398: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    39c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    3a0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    3a4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3a8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    3ac: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    3b0: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    3b4: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    3b8: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    3bc: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3c0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    3c4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3c8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_3cc:
    3cc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3d0: 000b0463  beq          x22, x0, 0x000003d8  # target 0x000003d8
    3d4: ff9ff06f  jal          x0, 0x000003cc  # target 0x000003cc
loc_3d8:
    3d8: 00008067  jalr         x0, 0(x1)
loc_3dc:
    3dc: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    3e0: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x0000078c
    3e4: 007a7d13  andi         x26, x20, 7
    3e8: ff8a7a13  andi         x20, x20, -8
    3ec: 01af8ab3  add          x21, x31, x26
    3f0: 007afb93  andi         x23, x21, 7
    3f4: 003ada93  srli         x21, x21, 3
    3f8: 00ba9a93  slli         x21, x21, 11
    3fc: 014a8ab3  add          x21, x21, x20
    400: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000400
    404: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000430
    408: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    40c: 890e8e93  addi         x29, x29, -1904  # x29 = 0x0000e890
    410: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e890
    414: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    418: 03cd8db3  mul          x27, x27, x28
    41c: 01bb0b33  add          x22, x22, x27
    420: 001b9b93  slli         x23, x23, 1
    424: 017b0b33  add          x22, x22, x23
    428: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    42c: 00008067  jalr         x0, 0(x1)
    430: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    434: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    438: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    43c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    440: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    444: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    448: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    44c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    450: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    454: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    458: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    45c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_460:
    460: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000460
    464: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000558
    468: 0000fcb7  lui          x25, 0x0000f  # x25 = 0x0000f000
    46c: 890c8c93  addi         x25, x25, -1904  # x25 = 0x0000e890
    470: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000e890
    474: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    478: 038b8bb3  mul          x23, x23, x24
    47c: 017a0a33  add          x20, x20, x23
loc_480:
    480: 001f1a93  slli         x21, x30, 1
    484: 014a8ab3  add          x21, x21, x20
    488: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_48c:
    48c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    490: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    494: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    498: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    49c: 018be463  bltu         x23, x24, 0x000004a4  # target 0x000004a4
    4a0: fedff06f  jal          x0, 0x0000048c  # target 0x0000048c
loc_4a4:
    4a4: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    4a8: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    4ac: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    4b0: 014b9b93  slli         x23, x23, 20
    4b4: 014bdb93  srli         x23, x23, 20
    4b8: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_4bc:
    4bc: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    4c0: 000c8463  beq          x25, x0, 0x000004c8  # target 0x000004c8
    4c4: ff9ff06f  jal          x0, 0x000004bc  # target 0x000004bc
loc_4c8:
    4c8: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    4cc: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    4d0: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    4d4: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    4d8: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    4dc: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    4e0: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    4e4: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    4e8: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    4ec: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    4f0: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    4f4: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    4f8: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4fc: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    500: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    504: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    508: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    50c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    510: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    514: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    518: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    51c: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_520:
    520: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    524: 000c8463  beq          x25, x0, 0x0000052c  # target 0x0000052c
    528: ff9ff06f  jal          x0, 0x00000520  # target 0x00000520
loc_52c:
    52c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    530: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    534: 016e8eb3  add          x29, x29, x22
    538: 001f0f13  addi         x30, x30, 1
    53c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    540: 015f1663  bne          x30, x21, 0x0000054c  # target 0x0000054c
    544: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    548: 016f8fb3  add          x31, x31, x22
loc_54c:
    54c: fffe0e13  addi         x28, x28, -1
    550: f20e18e3  bne          x28, x0, 0x00000480  # target 0x00000480
    554: 00008067  jalr         x0, 0(x1)
    558: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    55c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    560: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    564: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    568: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    56c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    570: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    574: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    578: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    57c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    580: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    584: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    588:           j FW_BRISC+4   # return to firmware, linked at install
