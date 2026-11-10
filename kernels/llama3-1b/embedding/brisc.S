# llama3 1b decode: embedding, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (1): 1,2
# params: 0x780=e2e_token_history, 0x784=e2e_embedding_weight, 0x788=e2e_x_a, 0x78c=token_pos
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00010537  lui          x10, 0x00010  # x10 = 0x00010000
      c: fc050513  addi         x10, x10, -64  # x10 = 0x0000ffc0
     10: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000ffc0
     14: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     18: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: 78c00413  addi         x8, x0, 1932  # x8 = 0x0000078c
     24: 00042203  lw           x4, 0(x8)  # param token_pos; 0x0000078c
     28: 00a25293  srli         x5, x4, 10
     2c: 3ff27313  andi         x6, x4, 1023
     30: 00028f93  addi         x31, x5, 0
     34: 2b0000ef  jal          x1, 0x000002e4  # target 0x000002e4; x1 = 0x00000038
     38: 000a8413  addi         x8, x21, 0
     3c: 000b0493  addi         x9, x22, 0
     40: 2f0000ef  jal          x1, 0x00000330  # target 0x00000330; x1 = 0x00000044
     44: 308000ef  jal          x1, 0x0000034c  # target 0x0000034c; x1 = 0x00000048
     48: 00040f93  addi         x31, x8, 0
     4c: 00048f13  addi         x30, x9, 0
     50: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
     54: fc0e8e93  addi         x29, x29, -64  # x29 = 0x0000efc0
loc_58:
     58: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
     5c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
     60: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
     64: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
     68: 015a6463  bltu         x20, x21, 0x00000070  # target 0x00000070
     6c: fedff06f  jal          x0, 0x00000058  # target 0x00000058
loc_70:
     70: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
     74: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
     78: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
     7c: 014a1a13  slli         x20, x20, 20
     80: 014a5a13  srli         x20, x20, 20
     84: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_88:
     88: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
     8c: 000b0463  beq          x22, x0, 0x00000094  # target 0x00000094
     90: ff9ff06f  jal          x0, 0x00000088  # target 0x00000088
loc_94:
     94: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
     98: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
     9c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
     a0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
     a4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x0000efc0
     a8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
     ac: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
     b0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
     b4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
     b8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
     bc: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
     c0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
     c4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     c8: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
     cc: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
     d0: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
     d4: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
     d8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
     dc: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
     e0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
     e4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_e8:
     e8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
     ec: 000b0463  beq          x22, x0, 0x000000f4  # target 0x000000f4
     f0: ff9ff06f  jal          x0, 0x000000e8  # target 0x000000e8
loc_f4:
     f4: 258000ef  jal          x1, 0x0000034c  # target 0x0000034c; x1 = 0x000000f8
     f8: 00231313  slli         x6, x6, 2
     fc: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    100: fc040413  addi         x8, x8, -64  # x8 = 0x0000efc0
    104: 00830333  add          x6, x6, x8
    108: 00032383  lw           x7, 0(x6)  # Address depends on runtime register values
    10c: 00139413  slli         x8, x7, 1
    110: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    114: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    118: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_11c:
    11c: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    120: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    124: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    128: 40a485b3  sub          x11, x9, x10
    12c: 01059593  slli         x11, x11, 16
    130: 0105d593  srli         x11, x11, 16
    134: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    138: 40b60633  sub          x12, x12, x11
    13c: 00100693  addi         x13, x0, 1  # x13 = 0x00000001
    140: 00d67663  bgeu         x12, x13, 0x0000014c  # target 0x0000014c
    144: 0ff0000f  fence        0xf, 0xf
    148: fd5ff06f  jal          x0, 0x0000011c  # target 0x0000011c
loc_14c:
    14c: 0ff0000f  fence        0xf, 0xf
    150: 00040f93  addi         x31, x8, 0
    154: 214000ef  jal          x1, 0x00000368  # target 0x00000368; x1 = 0x00000158
    158: 000a8493  addi         x9, x21, 0
    15c: 000b0513  addi         x10, x22, 0
    160: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    164: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    168: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    16c: 1c4000ef  jal          x1, 0x00000330  # target 0x00000330; x1 = 0x00000170
    170: 1dc000ef  jal          x1, 0x0000034c  # target 0x0000034c; x1 = 0x00000174
    174: 00048f93  addi         x31, x9, 0
    178: 00050f13  addi         x30, x10, 0
    17c: 00058e93  addi         x29, x11, 0
    180: 234000ef  jal          x1, 0x000003b4  # target 0x000003b4; x1 = 0x00000184
    184: 1c8000ef  jal          x1, 0x0000034c  # target 0x0000034c; x1 = 0x00000188
    188: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    18c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    190: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    194: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    198: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    19c: 00a484b3  add          x9, x9, x10
    1a0: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    1a4: fc058593  addi         x11, x11, -64  # x11 = 0x00010fc0
    1a8: 00b4e663  bltu         x9, x11, 0x000001b4  # target 0x000001b4
    1ac: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1b0: 40c484b3  sub          x9, x9, x12
loc_1b4:
    1b4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1b8: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    1bc: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1c0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1c4: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1c8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    1cc: 00148493  addi         x9, x9, 1
    1d0: 01049493  slli         x9, x9, 16
    1d4: 0104d493  srli         x9, x9, 16
    1d8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1dc: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1e0: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1e4: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    1e8: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    1ec: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    1f0: 0ff0000f  fence        0xf, 0xf
    1f4: 00139413  slli         x8, x7, 1
    1f8: 00140413  addi         x8, x8, 1
    1fc: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    200: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    204: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_208:
    208: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    20c: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    210: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    214: 40a485b3  sub          x11, x9, x10
    218: 01059593  slli         x11, x11, 16
    21c: 0105d593  srli         x11, x11, 16
    220: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    224: 40b60633  sub          x12, x12, x11
    228: 00100693  addi         x13, x0, 1  # x13 = 0x00000001
    22c: 00d67663  bgeu         x12, x13, 0x00000238  # target 0x00000238
    230: 0ff0000f  fence        0xf, 0xf
    234: fd5ff06f  jal          x0, 0x00000208  # target 0x00000208
loc_238:
    238: 0ff0000f  fence        0xf, 0xf
    23c: 00040f93  addi         x31, x8, 0
    240: 128000ef  jal          x1, 0x00000368  # target 0x00000368; x1 = 0x00000244
    244: 000a8493  addi         x9, x21, 0
    248: 000b0513  addi         x10, x22, 0
    24c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    250: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    254: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    258: 0d8000ef  jal          x1, 0x00000330  # target 0x00000330; x1 = 0x0000025c
    25c: 0f0000ef  jal          x1, 0x0000034c  # target 0x0000034c; x1 = 0x00000260
    260: 00048f93  addi         x31, x9, 0
    264: 00050f13  addi         x30, x10, 0
    268: 00058e93  addi         x29, x11, 0
    26c: 148000ef  jal          x1, 0x000003b4  # target 0x000003b4; x1 = 0x00000270
    270: 0dc000ef  jal          x1, 0x0000034c  # target 0x0000034c; x1 = 0x00000274
    274: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    278: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    27c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    280: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    284: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    288: 00a484b3  add          x9, x9, x10
    28c: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    290: fc058593  addi         x11, x11, -64  # x11 = 0x00010fc0
    294: 00b4e663  bltu         x9, x11, 0x000002a0  # target 0x000002a0
    298: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    29c: 40c484b3  sub          x9, x9, x12
loc_2a0:
    2a0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2a4: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    2a8: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    2ac: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2b0: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    2b4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    2b8: 00148493  addi         x9, x9, 1
    2bc: 01049493  slli         x9, x9, 16
    2c0: 0104d493  srli         x9, x9, 16
    2c4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2c8: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    2cc: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    2d0: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    2d4: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    2d8: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    2dc: 0ff0000f  fence        0xf, 0xf
    2e0: 1780006f  jal          x0, 0x00000458  # target 0x00000458
loc_2e4:
    2e4: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    2e8: 000aaa03  lw           x20, 0(x21)  # param e2e_token_history; 0x00000780
    2ec: 007a7d13  andi         x26, x20, 7
    2f0: ff8a7a13  andi         x20, x20, -8
    2f4: 01af8ab3  add          x21, x31, x26
    2f8: 007afb93  andi         x23, x21, 7
    2fc: 003ada93  srli         x21, x21, 3
    300: 00ca9a93  slli         x21, x21, 12
    304: 014a8ab3  add          x21, x21, x20
    308: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000308
    30c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000320
    310: 001b9b93  slli         x23, x23, 1
    314: 017b0b33  add          x22, x22, x23
    318: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    31c: 00008067  jalr         x0, 0(x1)
    320: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    324: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    328: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    32c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_330:
    330: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    334: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    338: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    33c: 000a0463  beq          x20, x0, 0x00000344  # target 0x00000344
    340: ff1ff06f  jal          x0, 0x00000330  # target 0x00000330
loc_344:
    344: 0ff0000f  fence        0xf, 0xf
    348: 00008067  jalr         x0, 0(x1)
loc_34c:
    34c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    350: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    354: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    358: 000a0463  beq          x20, x0, 0x00000360  # target 0x00000360
    35c: ff1ff06f  jal          x0, 0x0000034c  # target 0x0000034c
loc_360:
    360: 0ff0000f  fence        0xf, 0xf
    364: 00008067  jalr         x0, 0(x1)
loc_368:
    368: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    36c: 000aaa03  lw           x20, 0(x21)  # param e2e_embedding_weight; 0x00000784
    370: 007a7d13  andi         x26, x20, 7
    374: ff8a7a13  andi         x20, x20, -8
    378: 01af8ab3  add          x21, x31, x26
    37c: 007afb93  andi         x23, x21, 7
    380: 003ada93  srli         x21, x21, 3
    384: 00ba9a93  slli         x21, x21, 11
    388: 014a8ab3  add          x21, x21, x20
    38c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000038c
    390: 018b0b13  addi         x22, x22, 24  # x22 = 0x000003a4
    394: 001b9b93  slli         x23, x23, 1
    398: 017b0b33  add          x22, x22, x23
    39c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    3a0: 00008067  jalr         x0, 0(x1)
    3a4: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    3a8: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3ac: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3b0: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_3b4:
    3b4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3b8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3bc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3c0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    3c4: 015a6463  bltu         x20, x21, 0x000003cc  # target 0x000003cc
    3c8: fedff06f  jal          x0, 0x000003b4  # target 0x000003b4
loc_3cc:
    3cc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3d0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    3d4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    3d8: 014a1a13  slli         x20, x20, 20
    3dc: 014a5a13  srli         x20, x20, 20
    3e0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_3e4:
    3e4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3e8: 000b0463  beq          x22, x0, 0x000003f0  # target 0x000003f0
    3ec: ff9ff06f  jal          x0, 0x000003e4  # target 0x000003e4
loc_3f0:
    3f0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3f4: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    3f8: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    3fc: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    400: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    404: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    408: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    40c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    410: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    414: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    418: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    41c: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    420: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    424: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    428: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    42c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    430: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    434: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    438: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    43c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    440: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    444: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_448:
    448: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    44c: 000b0463  beq          x22, x0, 0x00000454  # target 0x00000454
    450: ff9ff06f  jal          x0, 0x00000448  # target 0x00000448
loc_454:
    454: 00008067  jalr         x0, 0(x1)
    458:           j FW_BRISC+4   # return to firmware, linked at install
