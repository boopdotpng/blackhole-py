# llama3 1b decode: o, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_context_decode_token, 0x784=e2e_l0_q, 0x788=e2e_x_b, 0x78c=e2e_x_a, 0x11880=e2e_q_compact, 0x11884=e2e_l0_q_row_start, 0x11888=dense_start, 0x1188c=e2e_l0_q_rows, 0x11890=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
      c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00012000
     10: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     14: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 1c0000ef  jal          x1, 0x000001dc  # target 0x000001dc; x1 = 0x00000020
     20: 1d8000ef  jal          x1, 0x000001f8  # target 0x000001f8; x1 = 0x00000024
     24: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     28: 1ec000ef  jal          x1, 0x00000214  # target 0x00000214; x1 = 0x0000002c
     2c: 000a8213  addi         x4, x21, 0
     30: 000b0293  addi         x5, x22, 0
     34: 00020f93  addi         x31, x4, 0
     38: 00028f13  addi         x30, x5, 0
     3c: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
     40: 258000ef  jal          x1, 0x00000298  # target 0x00000298; x1 = 0x00000044
     44: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     48: 1cc000ef  jal          x1, 0x00000214  # target 0x00000214; x1 = 0x0000004c
     4c: 000a8213  addi         x4, x21, 0
     50: 000b0293  addi         x5, x22, 0
     54: 00020f93  addi         x31, x4, 0
     58: 00028f13  addi         x30, x5, 0
     5c: 00016eb7  lui          x29, 0x00016  # x29 = 0x00016000
     60: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00015800
     64: 234000ef  jal          x1, 0x00000298  # target 0x00000298; x1 = 0x00000068
     68: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     6c: 2d0000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000070
     70: 000a8213  addi         x4, x21, 0
     74: 000b0293  addi         x5, x22, 0
     78: 00020f93  addi         x31, x4, 0
     7c: 00028f13  addi         x30, x5, 0
     80: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     84: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00016800
     88: 210000ef  jal          x1, 0x00000298  # target 0x00000298; x1 = 0x0000008c
     8c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     90: 2ac000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000094
     94: 000a8213  addi         x4, x21, 0
     98: 000b0293  addi         x5, x22, 0
     9c: 00020f93  addi         x31, x4, 0
     a0: 00028f13  addi         x30, x5, 0
     a4: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     a8: 1f0000ef  jal          x1, 0x00000298  # target 0x00000298; x1 = 0x000000ac
     ac: 14c000ef  jal          x1, 0x000001f8  # target 0x000001f8; x1 = 0x000000b0
     b0: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     b4: 88c28293  addi         x5, x5, -1908  # x5 = 0x0001188c
     b8: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0001188c
     bc: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
     c0: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
     c4: ff82f293  andi         x5, x5, -8
     c8: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     cc: 88448493  addi         x9, x9, -1916  # x9 = 0x00011884
     d0: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x00011884
     d4: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
     d8: 028383b3  mul          x7, x7, x8
     dc: 0073f313  andi         x6, x7, 7
     e0: 0033d393  srli         x7, x7, 3
     e4: 00b39393  slli         x7, x7, 11
     e8: 007282b3  add          x5, x5, x7
     ec: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
     f0: 00020413  addi         x8, x4, 0
loc_f4:
     f4: 0e83f263  bgeu         x7, x8, 0x000001d8  # target 0x000001d8
     f8: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
     fc: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    100: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_104:
    104: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    108: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    10c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    110: 40a485b3  sub          x11, x9, x10
    114: 01059593  slli         x11, x11, 16
    118: 0105d593  srli         x11, x11, 16
    11c: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    120: 40b60633  sub          x12, x12, x11
    124: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    128: 00d67663  bgeu         x12, x13, 0x00000134  # target 0x00000134
    12c: 0ff0000f  fence        0xf, 0xf
    130: fd5ff06f  jal          x0, 0x00000104  # target 0x00000104
loc_134:
    134: 0ff0000f  fence        0xf, 0xf
    138: 0a4000ef  jal          x1, 0x000001dc  # target 0x000001dc; x1 = 0x0000013c
    13c: 0bc000ef  jal          x1, 0x000001f8  # target 0x000001f8; x1 = 0x00000140
    140: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    144: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    148: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    14c: 00028f93  addi         x31, x5, 0
    150: 00030f13  addi         x30, x6, 0
    154: 00048e93  addi         x29, x9, 0
    158: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    15c: 264000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x00000160
    160: 000f8293  addi         x5, x31, 0
    164: 000f0313  addi         x6, x30, 0
    168: 090000ef  jal          x1, 0x000001f8  # target 0x000001f8; x1 = 0x0000016c
    16c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    170: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    174: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    178: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    17c: 00a484b3  add          x9, x9, x10
    180: 000145b7  lui          x11, 0x00014  # x11 = 0x00014000
    184: 00b4e663  bltu         x9, x11, 0x00000190  # target 0x00000190
    188: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    18c: 40c484b3  sub          x9, x9, x12
loc_190:
    190: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    194: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    198: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    19c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1a0: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1a4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    1a8: 00248493  addi         x9, x9, 2
    1ac: 01049493  slli         x9, x9, 16
    1b0: 0104d493  srli         x9, x9, 16
    1b4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1b8: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1bc: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1c0: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    1c4: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    1c8: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    1cc: 0ff0000f  fence        0xf, 0xf
    1d0: 00138393  addi         x7, x7, 1
    1d4: f21ff06f  jal          x0, 0x000000f4  # target 0x000000f4
loc_1d8:
    1d8: 3100006f  jal          x0, 0x000004e8  # target 0x000004e8
loc_1dc:
    1dc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    1e0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    1e4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    1e8: 000a0463  beq          x20, x0, 0x000001f0  # target 0x000001f0
    1ec: ff1ff06f  jal          x0, 0x000001dc  # target 0x000001dc
loc_1f0:
    1f0: 0ff0000f  fence        0xf, 0xf
    1f4: 00008067  jalr         x0, 0(x1)
loc_1f8:
    1f8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    1fc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    200: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    204: 000a0463  beq          x20, x0, 0x0000020c  # target 0x0000020c
    208: ff1ff06f  jal          x0, 0x000001f8  # target 0x000001f8
loc_20c:
    20c: 0ff0000f  fence        0xf, 0xf
    210: 00008067  jalr         x0, 0(x1)
loc_214:
    214: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    218: 000aaa03  lw           x20, 0(x21)  # param e2e_context_decode_token; 0x00000780
    21c: 007a7d13  andi         x26, x20, 7
    220: ff8a7a13  andi         x20, x20, -8
    224: 01af8ab3  add          x21, x31, x26
    228: 007afb93  andi         x23, x21, 7
    22c: 003ada93  srli         x21, x21, 3
    230: 00ba9a93  slli         x21, x21, 11
    234: 014a8ab3  add          x21, x21, x20
    238: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000238
    23c: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000268
    240: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    244: 890e8e93  addi         x29, x29, -1904  # x29 = 0x00011890
    248: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00011890
    24c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    250: 03cd8db3  mul          x27, x27, x28
    254: 01bb0b33  add          x22, x22, x27
    258: 001b9b93  slli         x23, x23, 1
    25c: 017b0b33  add          x22, x22, x23
    260: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    264: 00008067  jalr         x0, 0(x1)
    268: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    26c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    270: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    274: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    278: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    27c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    280: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    284: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    288: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    28c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    290: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    294: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_298:
    298: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    29c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    2a0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    2a4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    2a8: 015a6463  bltu         x20, x21, 0x000002b0  # target 0x000002b0
    2ac: fedff06f  jal          x0, 0x00000298  # target 0x00000298
loc_2b0:
    2b0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2b4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    2b8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    2bc: 014a1a13  slli         x20, x20, 20
    2c0: 014a5a13  srli         x20, x20, 20
    2c4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_2c8:
    2c8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    2cc: 000b0463  beq          x22, x0, 0x000002d4  # target 0x000002d4
    2d0: ff9ff06f  jal          x0, 0x000002c8  # target 0x000002c8
loc_2d4:
    2d4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    2d8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    2dc: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    2e0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    2e4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    2e8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    2ec: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    2f0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    2f4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    2f8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    2fc: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    300: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    304: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    308: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    30c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    310: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    314: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    318: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    31c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    320: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    324: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    328: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_32c:
    32c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    330: 000b0463  beq          x22, x0, 0x00000338  # target 0x00000338
    334: ff9ff06f  jal          x0, 0x0000032c  # target 0x0000032c
loc_338:
    338: 00008067  jalr         x0, 0(x1)
loc_33c:
    33c: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    340: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x0000078c
    344: 007a7d13  andi         x26, x20, 7
    348: ff8a7a13  andi         x20, x20, -8
    34c: 01af8ab3  add          x21, x31, x26
    350: 007afb93  andi         x23, x21, 7
    354: 003ada93  srli         x21, x21, 3
    358: 00ba9a93  slli         x21, x21, 11
    35c: 014a8ab3  add          x21, x21, x20
    360: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000360
    364: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000390
    368: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    36c: 890e8e93  addi         x29, x29, -1904  # x29 = 0x00011890
    370: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00011890
    374: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    378: 03cd8db3  mul          x27, x27, x28
    37c: 01bb0b33  add          x22, x22, x27
    380: 001b9b93  slli         x23, x23, 1
    384: 017b0b33  add          x22, x22, x23
    388: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    38c: 00008067  jalr         x0, 0(x1)
    390: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    394: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    398: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    39c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    3a0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3a4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3a8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    3ac: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    3b0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    3b4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3b8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3bc: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_3c0:
    3c0: 00000a17  auipc        x20, 0x00000  # x20 = 0x000003c0
    3c4: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000004b8
    3c8: 00012cb7  lui          x25, 0x00012  # x25 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    3cc: 890c8c93  addi         x25, x25, -1904  # x25 = 0x00011890
    3d0: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x00011890
    3d4: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    3d8: 038b8bb3  mul          x23, x23, x24
    3dc: 017a0a33  add          x20, x20, x23
loc_3e0:
    3e0: 001f1a93  slli         x21, x30, 1
    3e4: 014a8ab3  add          x21, x21, x20
    3e8: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_3ec:
    3ec: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    3f0: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    3f4: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    3f8: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    3fc: 018be463  bltu         x23, x24, 0x00000404  # target 0x00000404
    400: fedff06f  jal          x0, 0x000003ec  # target 0x000003ec
loc_404:
    404: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    408: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    40c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    410: 014b9b93  slli         x23, x23, 20
    414: 014bdb93  srli         x23, x23, 20
    418: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_41c:
    41c: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    420: 000c8463  beq          x25, x0, 0x00000428  # target 0x00000428
    424: ff9ff06f  jal          x0, 0x0000041c  # target 0x0000041c
loc_428:
    428: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    42c: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    430: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    434: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    438: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    43c: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    440: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    444: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    448: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    44c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    450: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    454: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    458: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    45c: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    460: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    464: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    468: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    46c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    470: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    474: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    478: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    47c: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_480:
    480: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    484: 000c8463  beq          x25, x0, 0x0000048c  # target 0x0000048c
    488: ff9ff06f  jal          x0, 0x00000480  # target 0x00000480
loc_48c:
    48c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    490: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    494: 016e8eb3  add          x29, x29, x22
    498: 001f0f13  addi         x30, x30, 1
    49c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    4a0: 015f1663  bne          x30, x21, 0x000004ac  # target 0x000004ac
    4a4: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    4a8: 016f8fb3  add          x31, x31, x22
loc_4ac:
    4ac: fffe0e13  addi         x28, x28, -1
    4b0: f20e18e3  bne          x28, x0, 0x000003e0  # target 0x000003e0
    4b4: 00008067  jalr         x0, 0(x1)
    4b8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4bc: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4c0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4c4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4c8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4cc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4d0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    4d4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    4d8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    4dc: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    4e4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    4e8:           j FW_BRISC+4   # return to firmware, linked at install
