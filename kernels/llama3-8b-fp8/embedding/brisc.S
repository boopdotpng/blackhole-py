# llama3 8b-fp8 decode: embedding, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (1): 1,4
# params: 0x780=e2e_token_history, 0x784=e2e_embedding_weight, 0x788=e2e_x_a, 0x78c=token_pos
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 87848493  addi         x9, x9, -1928  # x9 = 0xffb00878 · riscv_local_mem + 0x878
      8: 00010537  lui          x10, 0x00010  # x10 = 0x00010000
      c: 04050513  addi         x10, x10, 64  # x10 = 0x00010040
     10: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00010040
     14: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     18: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: 78c00413  addi         x8, x0, 1932  # x8 = 0x0000078c
     24: 00042203  lw           x4, 0(x8)  # param token_pos; 0x0000078c
     28: 00a25293  srli         x5, x4, 10
     2c: 3ff27313  andi         x6, x4, 1023
     30: 00028f93  addi         x31, x5, 0
     34: 488000ef  jal          x1, 0x000004bc  # target 0x000004bc; x1 = 0x00000038
     38: 000a8413  addi         x8, x21, 0
     3c: 000b0493  addi         x9, x22, 0
     40: 4c8000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000044
     44: 4e0000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000048
     48: 00040f93  addi         x31, x8, 0
     4c: 00048f13  addi         x30, x9, 0
     50: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
     54: 040e8e93  addi         x29, x29, 64  # x29 = 0x0000f040
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
     a4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x0000f040
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
     f4: 430000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x000000f8
     f8: 00231313  slli         x6, x6, 2
     fc: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    100: 04040413  addi         x8, x8, 64  # x8 = 0x0000f040
    104: 00830333  add          x6, x6, x8
    108: 00032383  lw           x7, 0(x6)  # Address depends on runtime register values
    10c: 00239413  slli         x8, x7, 2
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
    134: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    138: 40b60633  sub          x12, x12, x11
    13c: 00100693  addi         x13, x0, 1  # x13 = 0x00000001
    140: 00d67663  bgeu         x12, x13, 0x0000014c  # target 0x0000014c
    144: 0ff0000f  fence        0xf, 0xf
    148: fd5ff06f  jal          x0, 0x0000011c  # target 0x0000011c
loc_14c:
    14c: 0ff0000f  fence        0xf, 0xf
    150: 00040f93  addi         x31, x8, 0
    154: 3ec000ef  jal          x1, 0x00000540  # target 0x00000540; x1 = 0x00000158
    158: 000a8493  addi         x9, x21, 0
    15c: 000b0513  addi         x10, x22, 0
    160: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    164: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    168: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    16c: 39c000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000170
    170: 3b4000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000174
    174: 00048f93  addi         x31, x9, 0
    178: 00050f13  addi         x30, x10, 0
    17c: 00058e93  addi         x29, x11, 0
    180: 40c000ef  jal          x1, 0x0000058c  # target 0x0000058c; x1 = 0x00000184
    184: 3a0000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000188
    188: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    18c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    190: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    194: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    198: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    19c: 00a484b3  add          x9, x9, x10
    1a0: 000125b7  lui          x11, 0x00012  # x11 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    1a4: 04058593  addi         x11, x11, 64  # x11 = 0x00012040
    1a8: 00b4e663  bltu         x9, x11, 0x000001b4  # target 0x000001b4
    1ac: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
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
    1f4: 00239413  slli         x8, x7, 2
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
    220: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    224: 40b60633  sub          x12, x12, x11
    228: 00100693  addi         x13, x0, 1  # x13 = 0x00000001
    22c: 00d67663  bgeu         x12, x13, 0x00000238  # target 0x00000238
    230: 0ff0000f  fence        0xf, 0xf
    234: fd5ff06f  jal          x0, 0x00000208  # target 0x00000208
loc_238:
    238: 0ff0000f  fence        0xf, 0xf
    23c: 00040f93  addi         x31, x8, 0
    240: 300000ef  jal          x1, 0x00000540  # target 0x00000540; x1 = 0x00000244
    244: 000a8493  addi         x9, x21, 0
    248: 000b0513  addi         x10, x22, 0
    24c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    250: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    254: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    258: 2b0000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x0000025c
    25c: 2c8000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000260
    260: 00048f93  addi         x31, x9, 0
    264: 00050f13  addi         x30, x10, 0
    268: 00058e93  addi         x29, x11, 0
    26c: 320000ef  jal          x1, 0x0000058c  # target 0x0000058c; x1 = 0x00000270
    270: 2b4000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000274
    274: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    278: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    27c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    280: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    284: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    288: 00a484b3  add          x9, x9, x10
    28c: 000125b7  lui          x11, 0x00012  # x11 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    290: 04058593  addi         x11, x11, 64  # x11 = 0x00012040
    294: 00b4e663  bltu         x9, x11, 0x000002a0  # target 0x000002a0
    298: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
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
    2e0: 00239413  slli         x8, x7, 2
    2e4: 00240413  addi         x8, x8, 2
    2e8: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2ec: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    2f0: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_2f4:
    2f4: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    2f8: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    2fc: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    300: 40a485b3  sub          x11, x9, x10
    304: 01059593  slli         x11, x11, 16
    308: 0105d593  srli         x11, x11, 16
    30c: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    310: 40b60633  sub          x12, x12, x11
    314: 00100693  addi         x13, x0, 1  # x13 = 0x00000001
    318: 00d67663  bgeu         x12, x13, 0x00000324  # target 0x00000324
    31c: 0ff0000f  fence        0xf, 0xf
    320: fd5ff06f  jal          x0, 0x000002f4  # target 0x000002f4
loc_324:
    324: 0ff0000f  fence        0xf, 0xf
    328: 00040f93  addi         x31, x8, 0
    32c: 214000ef  jal          x1, 0x00000540  # target 0x00000540; x1 = 0x00000330
    330: 000a8493  addi         x9, x21, 0
    334: 000b0513  addi         x10, x22, 0
    338: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    33c: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    340: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    344: 1c4000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000348
    348: 1dc000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x0000034c
    34c: 00048f93  addi         x31, x9, 0
    350: 00050f13  addi         x30, x10, 0
    354: 00058e93  addi         x29, x11, 0
    358: 234000ef  jal          x1, 0x0000058c  # target 0x0000058c; x1 = 0x0000035c
    35c: 1c8000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000360
    360: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    364: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    368: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    36c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    370: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    374: 00a484b3  add          x9, x9, x10
    378: 000125b7  lui          x11, 0x00012  # x11 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    37c: 04058593  addi         x11, x11, 64  # x11 = 0x00012040
    380: 00b4e663  bltu         x9, x11, 0x0000038c  # target 0x0000038c
    384: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    388: 40c484b3  sub          x9, x9, x12
loc_38c:
    38c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    390: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    394: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    398: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    39c: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    3a0: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    3a4: 00148493  addi         x9, x9, 1
    3a8: 01049493  slli         x9, x9, 16
    3ac: 0104d493  srli         x9, x9, 16
    3b0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3b4: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    3b8: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    3bc: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    3c0: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    3c4: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    3c8: 0ff0000f  fence        0xf, 0xf
    3cc: 00239413  slli         x8, x7, 2
    3d0: 00340413  addi         x8, x8, 3
    3d4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    3d8: 87c70713  addi         x14, x14, -1924  # x14 = 0xffb0087c · riscv_local_mem + 0x87c
    3dc: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_3e0:
    3e0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    3e4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    3e8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    3ec: 40a485b3  sub          x11, x9, x10
    3f0: 01059593  slli         x11, x11, 16
    3f4: 0105d593  srli         x11, x11, 16
    3f8: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    3fc: 40b60633  sub          x12, x12, x11
    400: 00100693  addi         x13, x0, 1  # x13 = 0x00000001
    404: 00d67663  bgeu         x12, x13, 0x00000410  # target 0x00000410
    408: 0ff0000f  fence        0xf, 0xf
    40c: fd5ff06f  jal          x0, 0x000003e0  # target 0x000003e0
loc_410:
    410: 0ff0000f  fence        0xf, 0xf
    414: 00040f93  addi         x31, x8, 0
    418: 128000ef  jal          x1, 0x00000540  # target 0x00000540; x1 = 0x0000041c
    41c: 000a8493  addi         x9, x21, 0
    420: 000b0513  addi         x10, x22, 0
    424: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    428: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    42c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    430: 0d8000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000434
    434: 0f0000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000438
    438: 00048f93  addi         x31, x9, 0
    43c: 00050f13  addi         x30, x10, 0
    440: 00058e93  addi         x29, x11, 0
    444: 148000ef  jal          x1, 0x0000058c  # target 0x0000058c; x1 = 0x00000448
    448: 0dc000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x0000044c
    44c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    450: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    454: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878
    458: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    45c: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    460: 00a484b3  add          x9, x9, x10
    464: 000125b7  lui          x11, 0x00012  # x11 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    468: 04058593  addi         x11, x11, 64  # x11 = 0x00012040
    46c: 00b4e663  bltu         x9, x11, 0x00000478  # target 0x00000478
    470: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    474: 40c484b3  sub          x9, x9, x12
loc_478:
    478: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    47c: 87868693  addi         x13, x13, -1928  # x13 = 0xffb00878 · riscv_local_mem + 0x878
    480: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    484: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    488: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    48c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c
    490: 00148493  addi         x9, x9, 1
    494: 01049493  slli         x9, x9, 16
    498: 0104d493  srli         x9, x9, 16
    49c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4a0: 87c50513  addi         x10, x10, -1924  # x10 = 0xffb0087c · riscv_local_mem + 0x87c
    4a4: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    4a8: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    4ac: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    4b0: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    4b4: 0ff0000f  fence        0xf, 0xf
    4b8: 1780006f  jal          x0, 0x00000630  # target 0x00000630
loc_4bc:
    4bc: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    4c0: 000aaa03  lw           x20, 0(x21)  # param e2e_token_history; 0x00000780
    4c4: 007a7d13  andi         x26, x20, 7
    4c8: ff8a7a13  andi         x20, x20, -8
    4cc: 01af8ab3  add          x21, x31, x26
    4d0: 007afb93  andi         x23, x21, 7
    4d4: 003ada93  srli         x21, x21, 3
    4d8: 00ca9a93  slli         x21, x21, 12
    4dc: 014a8ab3  add          x21, x21, x20
    4e0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004e0
    4e4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000004f8
    4e8: 001b9b93  slli         x23, x23, 1
    4ec: 017b0b33  add          x22, x22, x23
    4f0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4f4: 00008067  jalr         x0, 0(x1)
    4f8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    4fc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    500: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    504: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_508:
    508: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    50c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    510: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    514: 000a0463  beq          x20, x0, 0x0000051c  # target 0x0000051c
    518: ff1ff06f  jal          x0, 0x00000508  # target 0x00000508
loc_51c:
    51c: 0ff0000f  fence        0xf, 0xf
    520: 00008067  jalr         x0, 0(x1)
loc_524:
    524: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    528: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    52c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    530: 000a0463  beq          x20, x0, 0x00000538  # target 0x00000538
    534: ff1ff06f  jal          x0, 0x00000524  # target 0x00000524
loc_538:
    538: 0ff0000f  fence        0xf, 0xf
    53c: 00008067  jalr         x0, 0(x1)
loc_540:
    540: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    544: 000aaa03  lw           x20, 0(x21)  # param e2e_embedding_weight; 0x00000784
    548: 007a7d13  andi         x26, x20, 7
    54c: ff8a7a13  andi         x20, x20, -8
    550: 01af8ab3  add          x21, x31, x26
    554: 007afb93  andi         x23, x21, 7
    558: 003ada93  srli         x21, x21, 3
    55c: 00ba9a93  slli         x21, x21, 11
    560: 014a8ab3  add          x21, x21, x20
    564: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000564
    568: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000057c
    56c: 001b9b93  slli         x23, x23, 1
    570: 017b0b33  add          x22, x22, x23
    574: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    578: 00008067  jalr         x0, 0(x1)
    57c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    580: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    584: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    588: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_58c:
    58c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    590: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    594: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    598: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    59c: 015a6463  bltu         x20, x21, 0x000005a4  # target 0x000005a4
    5a0: fedff06f  jal          x0, 0x0000058c  # target 0x0000058c
loc_5a4:
    5a4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5a8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    5ac: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    5b0: 014a1a13  slli         x20, x20, 20
    5b4: 014a5a13  srli         x20, x20, 20
    5b8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_5bc:
    5bc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5c0: 000b0463  beq          x22, x0, 0x000005c8  # target 0x000005c8
    5c4: ff9ff06f  jal          x0, 0x000005bc  # target 0x000005bc
loc_5c8:
    5c8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5cc: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    5d0: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    5d4: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    5d8: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    5dc: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    5e0: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    5e4: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    5e8: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    5ec: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    5f0: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    5f4: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    5f8: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5fc: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    600: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    604: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    608: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    60c: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    610: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    614: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    618: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    61c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_620:
    620: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    624: 000b0463  beq          x22, x0, 0x0000062c  # target 0x0000062c
    628: ff9ff06f  jal          x0, 0x00000620  # target 0x00000620
loc_62c:
    62c: 00008067  jalr         x0, 0(x1)
    630:           j FW_BRISC+4   # return to firmware, linked at install
