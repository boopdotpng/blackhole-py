# llama3 1b decode: embedding, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (1): 1,2
# params: 0x7c0=e2e_token_history, 0x7c4=e2e_embedding_weight, 0x7c8=e2e_x_a, 0x7cc=token_pos
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00091537  lui          x10, 0x00091  # x10 = 0x00091000
      c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00091000
     10: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     14: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 7cc00413  addi         x8, x0, 1996  # x8 = 0x000007cc
     20: 00042203  lw           x4, 0(x8)  # param token_pos; 0x000007cc
     24: 00a25293  srli         x5, x4, 10
     28: 3ff27313  andi         x6, x4, 1023
     2c: 00028f93  addi         x31, x5, 0
     30: 2a0000ef  jal          x1, 0x000002d0  # target 0x000002d0; x1 = 0x00000034
     34: 000a8413  addi         x8, x21, 0
     38: 000b0493  addi         x9, x22, 0
     3c: 2e4000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000040
     40: 2fc000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000044
     44: 00040f93  addi         x31, x8, 0
     48: 00048f13  addi         x30, x9, 0
     4c: 00090eb7  lui          x29, 0x00090  # x29 = 0x00090000
loc_50:
     50: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
     54: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
     58: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
     5c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
     60: 015a6463  bltu         x20, x21, 0x00000068  # target 0x00000068
     64: fedff06f  jal          x0, 0x00000050  # target 0x00000050
loc_68:
     68: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
     6c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
     70: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
     74: 014a1a13  slli         x20, x20, 20
     78: 014a5a13  srli         x20, x20, 20
     7c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_80:
     80: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
     84: 000b0463  beq          x22, x0, 0x0000008c  # target 0x0000008c
     88: ff9ff06f  jal          x0, 0x00000080  # target 0x00000080
loc_8c:
     8c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
     90: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
     94: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
     98: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
     9c: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x00090000
     a0: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
     a4: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
     a8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
     ac: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
     b0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
     b4: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
     b8: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
     bc: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     c0: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
     c4: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
     c8: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
     cc: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
     d0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
     d4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
     d8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
     dc: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_e0:
     e0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
     e4: 000b0463  beq          x22, x0, 0x000000ec  # target 0x000000ec
     e8: ff9ff06f  jal          x0, 0x000000e0  # target 0x000000e0
loc_ec:
     ec: 250000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x000000f0
     f0: 00231313  slli         x6, x6, 2
     f4: 00090437  lui          x8, 0x00090  # x8 = 0x00090000
     f8: 00830333  add          x6, x6, x8
     fc: 00032383  lw           x7, 0(x6)  # Address depends on runtime register values
    100: 00139413  slli         x8, x7, 1
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
    128: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    12c: 40b60633  sub          x12, x12, x11
    130: 00100693  addi         x13, x0, 1  # x13 = 0x00000001
    134: 00d67663  bgeu         x12, x13, 0x00000140  # target 0x00000140
    138: 0ff0000f  fence        0xf, 0xf
    13c: fd5ff06f  jal          x0, 0x00000110  # target 0x00000110
loc_140:
    140: 0ff0000f  fence        0xf, 0xf
    144: 00040f93  addi         x31, x8, 0
    148: 210000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x0000014c
    14c: 000a8493  addi         x9, x21, 0
    150: 000b0513  addi         x10, x22, 0
    154: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    158: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    15c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    160: 1c0000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x00000164
    164: 1d8000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000168
    168: 00048f93  addi         x31, x9, 0
    16c: 00050f13  addi         x30, x10, 0
    170: 00058e93  addi         x29, x11, 0
    174: 234000ef  jal          x1, 0x000003a8  # target 0x000003a8; x1 = 0x00000178
    178: 1c4000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x0000017c
    17c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    180: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    184: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    188: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    18c: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    190: 00a484b3  add          x9, x9, x10
    194: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    198: 00b4e663  bltu         x9, x11, 0x000001a4  # target 0x000001a4
    19c: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1a0: 40c484b3  sub          x9, x9, x12
loc_1a4:
    1a4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1a8: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    1ac: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1b0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1b4: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1b8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    1bc: 00148493  addi         x9, x9, 1
    1c0: 01049493  slli         x9, x9, 16
    1c4: 0104d493  srli         x9, x9, 16
    1c8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1cc: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    1d0: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1d4: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    1d8: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    1dc: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    1e0: 0ff0000f  fence        0xf, 0xf
    1e4: 00139413  slli         x8, x7, 1
    1e8: 00140413  addi         x8, x8, 1
    1ec: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1f0: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    1f4: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_1f8:
    1f8: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1fc: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    200: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    204: 40a485b3  sub          x11, x9, x10
    208: 01059593  slli         x11, x11, 16
    20c: 0105d593  srli         x11, x11, 16
    210: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    214: 40b60633  sub          x12, x12, x11
    218: 00100693  addi         x13, x0, 1  # x13 = 0x00000001
    21c: 00d67663  bgeu         x12, x13, 0x00000228  # target 0x00000228
    220: 0ff0000f  fence        0xf, 0xf
    224: fd5ff06f  jal          x0, 0x000001f8  # target 0x000001f8
loc_228:
    228: 0ff0000f  fence        0xf, 0xf
    22c: 00040f93  addi         x31, x8, 0
    230: 128000ef  jal          x1, 0x00000358  # target 0x00000358; x1 = 0x00000234
    234: 000a8493  addi         x9, x21, 0
    238: 000b0513  addi         x10, x22, 0
    23c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    240: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    244: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    248: 0d8000ef  jal          x1, 0x00000320  # target 0x00000320; x1 = 0x0000024c
    24c: 0f0000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000250
    250: 00048f93  addi         x31, x9, 0
    254: 00050f13  addi         x30, x10, 0
    258: 00058e93  addi         x29, x11, 0
    25c: 14c000ef  jal          x1, 0x000003a8  # target 0x000003a8; x1 = 0x00000260
    260: 0dc000ef  jal          x1, 0x0000033c  # target 0x0000033c; x1 = 0x00000264
    264: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    268: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    26c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    270: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    274: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    278: 00a484b3  add          x9, x9, x10
    27c: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    280: 00b4e663  bltu         x9, x11, 0x0000028c  # target 0x0000028c
    284: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    288: 40c484b3  sub          x9, x9, x12
loc_28c:
    28c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    290: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    294: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    298: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    29c: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    2a0: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    2a4: 00148493  addi         x9, x9, 1
    2a8: 01049493  slli         x9, x9, 16
    2ac: 0104d493  srli         x9, x9, 16
    2b0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2b4: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    2b8: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    2bc: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    2c0: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    2c4: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    2c8: 0ff0000f  fence        0xf, 0xf
    2cc: 1800006f  jal          x0, 0x0000044c  # target 0x0000044c
loc_2d0:
    2d0: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    2d4: 000aaa03  lw           x20, 0(x21)  # param e2e_token_history; 0x000007c0
    2d8: 007a7d13  andi         x26, x20, 7
    2dc: ff8a7a13  andi         x20, x20, -8
    2e0: 01af8ab3  add          x21, x31, x26
    2e4: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    2e8: 038afbb3  remu         x23, x21, x24
    2ec: 038adab3  divu         x21, x21, x24
    2f0: 00ca9a93  slli         x21, x21, 12
    2f4: 014a8ab3  add          x21, x21, x20
    2f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000002f8
    2fc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000310
    300: 001b9b93  slli         x23, x23, 1
    304: 017b0b33  add          x22, x22, x23
    308: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    30c: 00008067  jalr         x0, 0(x1)
    310: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    314: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    318: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    31c: 00000512  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_320:
    320: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    324: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    328: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    32c: 000a0463  beq          x20, x0, 0x00000334  # target 0x00000334
    330: ff1ff06f  jal          x0, 0x00000320  # target 0x00000320
loc_334:
    334: 0ff0000f  fence        0xf, 0xf
    338: 00008067  jalr         x0, 0(x1)
loc_33c:
    33c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    340: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    344: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    348: 000a0463  beq          x20, x0, 0x00000350  # target 0x00000350
    34c: ff1ff06f  jal          x0, 0x0000033c  # target 0x0000033c
loc_350:
    350: 0ff0000f  fence        0xf, 0xf
    354: 00008067  jalr         x0, 0(x1)
loc_358:
    358: 7c400a93  addi         x21, x0, 1988  # x21 = 0x000007c4
    35c: 000aaa03  lw           x20, 0(x21)  # param e2e_embedding_weight; 0x000007c4
    360: 007a7d13  andi         x26, x20, 7
    364: ff8a7a13  andi         x20, x20, -8
    368: 01af8ab3  add          x21, x31, x26
    36c: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    370: 038afbb3  remu         x23, x21, x24
    374: 038adab3  divu         x21, x21, x24
    378: 00ba9a93  slli         x21, x21, 11
    37c: 014a8ab3  add          x21, x21, x20
    380: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000380
    384: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000398
    388: 001b9b93  slli         x23, x23, 1
    38c: 017b0b33  add          x22, x22, x23
    390: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    394: 00008067  jalr         x0, 0(x1)
    398: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    39c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3a0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    3a4: 00000512  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_3a8:
    3a8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3ac: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3b0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3b4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    3b8: 015a6463  bltu         x20, x21, 0x000003c0  # target 0x000003c0
    3bc: fedff06f  jal          x0, 0x000003a8  # target 0x000003a8
loc_3c0:
    3c0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3c4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    3c8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    3cc: 014a1a13  slli         x20, x20, 20
    3d0: 014a5a13  srli         x20, x20, 20
    3d4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_3d8:
    3d8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3dc: 000b0463  beq          x22, x0, 0x000003e4  # target 0x000003e4
    3e0: ff9ff06f  jal          x0, 0x000003d8  # target 0x000003d8
loc_3e4:
    3e4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    3e8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    3ec: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    3f0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    3f4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    3f8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    3fc: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    400: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    404: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    408: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    40c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    410: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    414: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    418: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    41c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    420: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    424: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    428: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    42c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    430: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    434: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    438: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_43c:
    43c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    440: 000b0463  beq          x22, x0, 0x00000448  # target 0x00000448
    444: ff9ff06f  jal          x0, 0x0000043c  # target 0x0000043c
loc_448:
    448: 00008067  jalr         x0, 0(x1)
    44c:           j FW_BRISC+4   # return to firmware, linked at install
