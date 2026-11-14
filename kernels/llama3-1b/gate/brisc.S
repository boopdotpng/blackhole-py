# llama3 1b decode: gate, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_b_decode_token, 0x784=e2e_l0_gate, 0x788=e2e_l0_up, 0x78c=e2e_hidden_dense, 0x790=e2e_l0_post_norm, 0x11940=e2e_gate, 0x11944=e2e_l0_gate_row_start, 0x11948=e2e_up, 0x1194c=e2e_l0_up_row_start, 0x11950=dense_start, 0x11954=e2e_l0_gate_rows, 0x11958=e2e_l0_up_rows, 0x1195c=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000172b7  lui          x5, 0x00017  # x5 = 0x00017000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00017000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     20: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     24: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     28: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00012000
     2c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     30: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
     34: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     38: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     3c: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     40: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_44:
     44: ffb4d4b7  lui          x9, 0xffb4d  # x9 = 0xffb4d000
     48: 02048493  addi         x9, x9, 32  # x9 = 0xffb4d020
     4c: 0004d283  lhu          x5, 0(x9)  # 0xffb4d020
     50: 40520333  sub          x6, x4, x5
     54: 01031313  slli         x6, x6, 16
     58: 01035313  srli         x6, x6, 16
     5c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     60: 406383b3  sub          x7, x7, x6
     64: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
     68: 0083f663  bgeu         x7, x8, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: fd5ff06f  jal          x0, 0x00000044  # target 0x00000044
loc_74:
     74: 0ff0000f  fence        0xf, 0xf
     78: 34c000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x0000007c
     7c: 364000ef  jal          x1, 0x000003e0  # target 0x000003e0; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 378000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     9c: 3e4000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 358000ef  jal          x1, 0x000003fc  # target 0x000003fc; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00017800
     c0: 3c0000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x000000c4
     c4: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     c8: 45c000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     e0: 3a0000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x000000e4
     e4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     e8: 43c000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00018800
    104: 37c000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000108
    108: 2d8000ef  jal          x1, 0x000003e0  # target 0x000003e0; x1 = 0x0000010c
    10c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    110: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    114: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    118: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    11c: 00520233  add          x4, x4, x5
    120: 00019337  lui          x6, 0x00019  # x6 = 0x00019000
    124: 00626663  bltu         x4, x6, 0x00000130  # target 0x00000130
    128: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    12c: 40720233  sub          x4, x4, x7
loc_130:
    130: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    134: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    138: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    13c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    140: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    144: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    148: 00420213  addi         x4, x4, 4
    14c: 01021213  slli         x4, x4, 16
    150: 01025213  srli         x4, x4, 16
    154: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    158: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    15c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    160: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    164: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    168: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    16c: 0ff0000f  fence        0xf, 0xf
    170: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    174: 95428293  addi         x5, x5, -1708  # x5 = 0x00011954
    178: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x00011954
    17c: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    180: 0003a283  lw           x5, 0(x7)  # param e2e_l0_gate; 0x00000784
    184: ff82f293  andi         x5, x5, -8
    188: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    18c: 94448493  addi         x9, x9, -1724  # x9 = 0x00011944
    190: 0004a383  lw           x7, 0(x9)  # param e2e_l0_gate_row_start; 0x00011944
    194: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    198: 028383b3  mul          x7, x7, x8
    19c: 0073f313  andi         x6, x7, 7
    1a0: 0033d393  srli         x7, x7, 3
    1a4: 00b39393  slli         x7, x7, 11
    1a8: 007282b3  add          x5, x5, x7
    1ac: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1b0: 00020413  addi         x8, x4, 0
loc_1b4:
    1b4: 0e83f263  bgeu         x7, x8, 0x00000298  # target 0x00000298
    1b8: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1bc: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    1c0: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1c4:
    1c4: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1c8: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1cc: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1d0: 40a485b3  sub          x11, x9, x10
    1d4: 01059593  slli         x11, x11, 16
    1d8: 0105d593  srli         x11, x11, 16
    1dc: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    1e0: 40b60633  sub          x12, x12, x11
    1e4: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    1e8: 00d67663  bgeu         x12, x13, 0x000001f4  # target 0x000001f4
    1ec: 0ff0000f  fence        0xf, 0xf
    1f0: fd5ff06f  jal          x0, 0x000001c4  # target 0x000001c4
loc_1f4:
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: 1cc000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x000001fc
    1fc: 1e4000ef  jal          x1, 0x000003e0  # target 0x000003e0; x1 = 0x00000200
    200: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    204: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    208: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    20c: 00028f93  addi         x31, x5, 0
    210: 00030f13  addi         x30, x6, 0
    214: 00048e93  addi         x29, x9, 0
    218: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    21c: 38c000ef  jal          x1, 0x000005a8  # target 0x000005a8; x1 = 0x00000220
    220: 000f8293  addi         x5, x31, 0
    224: 000f0313  addi         x6, x30, 0
    228: 1b8000ef  jal          x1, 0x000003e0  # target 0x000003e0; x1 = 0x0000022c
    22c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    230: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    234: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    238: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    23c: 00a484b3  add          x9, x9, x10
    240: 000145b7  lui          x11, 0x00014  # x11 = 0x00014000
    244: 00b4e663  bltu         x9, x11, 0x00000250  # target 0x00000250
    248: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    24c: 40c484b3  sub          x9, x9, x12
loc_250:
    250: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    254: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    258: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    25c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    260: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    264: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    268: 00248493  addi         x9, x9, 2
    26c: 01049493  slli         x9, x9, 16
    270: 0104d493  srli         x9, x9, 16
    274: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    278: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    27c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    280: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    284: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    288: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    28c: 0ff0000f  fence        0xf, 0xf
    290: 00138393  addi         x7, x7, 1
    294: f21ff06f  jal          x0, 0x000001b4  # target 0x000001b4
loc_298:
    298: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    29c: 95828293  addi         x5, x5, -1704  # x5 = 0x00011958
    2a0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x00011958
    2a4: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
    2a8: 0003a283  lw           x5, 0(x7)  # param e2e_l0_up; 0x00000788
    2ac: ff82f293  andi         x5, x5, -8
    2b0: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2b4: 94c48493  addi         x9, x9, -1716  # x9 = 0x0001194c
    2b8: 0004a383  lw           x7, 0(x9)  # param e2e_l0_up_row_start; 0x0001194c
    2bc: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    2c0: 028383b3  mul          x7, x7, x8
    2c4: 0073f313  andi         x6, x7, 7
    2c8: 0033d393  srli         x7, x7, 3
    2cc: 00b39393  slli         x7, x7, 11
    2d0: 007282b3  add          x5, x5, x7
    2d4: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    2d8: 00020413  addi         x8, x4, 0
loc_2dc:
    2dc: 0e83f263  bgeu         x7, x8, 0x000003c0  # target 0x000003c0
    2e0: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2e4: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    2e8: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_2ec:
    2ec: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    2f0: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    2f4: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    2f8: 40a485b3  sub          x11, x9, x10
    2fc: 01059593  slli         x11, x11, 16
    300: 0105d593  srli         x11, x11, 16
    304: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    308: 40b60633  sub          x12, x12, x11
    30c: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    310: 00d67663  bgeu         x12, x13, 0x0000031c  # target 0x0000031c
    314: 0ff0000f  fence        0xf, 0xf
    318: fd5ff06f  jal          x0, 0x000002ec  # target 0x000002ec
loc_31c:
    31c: 0ff0000f  fence        0xf, 0xf
    320: 0a4000ef  jal          x1, 0x000003c4  # target 0x000003c4; x1 = 0x00000324
    324: 0bc000ef  jal          x1, 0x000003e0  # target 0x000003e0; x1 = 0x00000328
    328: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    32c: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    330: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    334: 00028f93  addi         x31, x5, 0
    338: 00030f13  addi         x30, x6, 0
    33c: 00048e93  addi         x29, x9, 0
    340: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    344: 264000ef  jal          x1, 0x000005a8  # target 0x000005a8; x1 = 0x00000348
    348: 000f8293  addi         x5, x31, 0
    34c: 000f0313  addi         x6, x30, 0
    350: 090000ef  jal          x1, 0x000003e0  # target 0x000003e0; x1 = 0x00000354
    354: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    358: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    35c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    360: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    364: 00a484b3  add          x9, x9, x10
    368: 000145b7  lui          x11, 0x00014  # x11 = 0x00014000
    36c: 00b4e663  bltu         x9, x11, 0x00000378  # target 0x00000378
    370: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    374: 40c484b3  sub          x9, x9, x12
loc_378:
    378: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    37c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    380: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    384: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    388: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    38c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    390: 00248493  addi         x9, x9, 2
    394: 01049493  slli         x9, x9, 16
    398: 0104d493  srli         x9, x9, 16
    39c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3a0: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    3a4: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    3a8: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    3ac: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    3b0: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    3b4: 0ff0000f  fence        0xf, 0xf
    3b8: 00138393  addi         x7, x7, 1
    3bc: f21ff06f  jal          x0, 0x000002dc  # target 0x000002dc
loc_3c0:
    3c0: 3100006f  jal          x0, 0x000006d0  # target 0x000006d0
loc_3c4:
    3c4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3c8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    3cc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    3d0: 000a0463  beq          x20, x0, 0x000003d8  # target 0x000003d8
    3d4: ff1ff06f  jal          x0, 0x000003c4  # target 0x000003c4
loc_3d8:
    3d8: 0ff0000f  fence        0xf, 0xf
    3dc: 00008067  jalr         x0, 0(x1)
loc_3e0:
    3e0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3e4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3e8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3ec: 000a0463  beq          x20, x0, 0x000003f4  # target 0x000003f4
    3f0: ff1ff06f  jal          x0, 0x000003e0  # target 0x000003e0
loc_3f4:
    3f4: 0ff0000f  fence        0xf, 0xf
    3f8: 00008067  jalr         x0, 0(x1)
loc_3fc:
    3fc: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    400: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b_decode_token; 0x00000780
    404: 007a7d13  andi         x26, x20, 7
    408: ff8a7a13  andi         x20, x20, -8
    40c: 01af8ab3  add          x21, x31, x26
    410: 007afb93  andi         x23, x21, 7
    414: 003ada93  srli         x21, x21, 3
    418: 00ba9a93  slli         x21, x21, 11
    41c: 014a8ab3  add          x21, x21, x20
    420: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000420
    424: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000450
    428: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    42c: 95ce8e93  addi         x29, x29, -1700  # x29 = 0x0001195c
    430: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0001195c
    434: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    438: 03cd8db3  mul          x27, x27, x28
    43c: 01bb0b33  add          x22, x22, x27
    440: 001b9b93  slli         x23, x23, 1
    444: 017b0b33  add          x22, x22, x23
    448: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    44c: 00008067  jalr         x0, 0(x1)
    450: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    454: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    458: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    45c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    460: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    464: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    468: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    46c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    470: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    474: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    478: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    47c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_480:
    480: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    484: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    488: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    48c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    490: 015a6463  bltu         x20, x21, 0x00000498  # target 0x00000498
    494: fedff06f  jal          x0, 0x00000480  # target 0x00000480
loc_498:
    498: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    49c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    4a0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    4a4: 014a1a13  slli         x20, x20, 20
    4a8: 014a5a13  srli         x20, x20, 20
    4ac: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_4b0:
    4b0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    4b4: 000b0463  beq          x22, x0, 0x000004bc  # target 0x000004bc
    4b8: ff9ff06f  jal          x0, 0x000004b0  # target 0x000004b0
loc_4bc:
    4bc: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    4c0: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    4c4: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    4c8: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    4cc: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    4d0: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    4d4: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    4d8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    4dc: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    4e0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    4e4: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    4e8: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    4ec: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4f0: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    4f4: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    4f8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    4fc: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    500: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    504: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    508: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    50c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    510: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_514:
    514: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    518: 000b0463  beq          x22, x0, 0x00000520  # target 0x00000520
    51c: ff9ff06f  jal          x0, 0x00000514  # target 0x00000514
loc_520:
    520: 00008067  jalr         x0, 0(x1)
loc_524:
    524: 79000a93  addi         x21, x0, 1936  # x21 = 0x00000790
    528: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_post_norm; 0x00000790
    52c: 007a7d13  andi         x26, x20, 7
    530: ff8a7a13  andi         x20, x20, -8
    534: 01af8ab3  add          x21, x31, x26
    538: 007afb93  andi         x23, x21, 7
    53c: 003ada93  srli         x21, x21, 3
    540: 00ba9a93  slli         x21, x21, 11
    544: 014a8ab3  add          x21, x21, x20
    548: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000548
    54c: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000578
    550: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    554: 95ce8e93  addi         x29, x29, -1700  # x29 = 0x0001195c
    558: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0001195c
    55c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    560: 03cd8db3  mul          x27, x27, x28
    564: 01bb0b33  add          x22, x22, x27
    568: 001b9b93  slli         x23, x23, 1
    56c: 017b0b33  add          x22, x22, x23
    570: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    574: 00008067  jalr         x0, 0(x1)
    578: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    57c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    580: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    584: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    588: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    58c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    590: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    594: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    598: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    59c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5a0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5a4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_5a8:
    5a8: 00000a17  auipc        x20, 0x00000  # x20 = 0x000005a8
    5ac: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000006a0
    5b0: 00012cb7  lui          x25, 0x00012  # x25 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    5b4: 95cc8c93  addi         x25, x25, -1700  # x25 = 0x0001195c
    5b8: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0001195c
    5bc: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    5c0: 038b8bb3  mul          x23, x23, x24
    5c4: 017a0a33  add          x20, x20, x23
loc_5c8:
    5c8: 001f1a93  slli         x21, x30, 1
    5cc: 014a8ab3  add          x21, x21, x20
    5d0: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_5d4:
    5d4: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    5d8: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    5dc: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    5e0: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    5e4: 018be463  bltu         x23, x24, 0x000005ec  # target 0x000005ec
    5e8: fedff06f  jal          x0, 0x000005d4  # target 0x000005d4
loc_5ec:
    5ec: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    5f0: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    5f4: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    5f8: 014b9b93  slli         x23, x23, 20
    5fc: 014bdb93  srli         x23, x23, 20
    600: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_604:
    604: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    608: 000c8463  beq          x25, x0, 0x00000610  # target 0x00000610
    60c: ff9ff06f  jal          x0, 0x00000604  # target 0x00000604
loc_610:
    610: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    614: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    618: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    61c: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    620: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    624: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    628: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    62c: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    630: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    634: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    638: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    63c: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    640: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    644: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    648: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    64c: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    650: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    654: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    658: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    65c: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    660: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    664: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_668:
    668: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    66c: 000c8463  beq          x25, x0, 0x00000674  # target 0x00000674
    670: ff9ff06f  jal          x0, 0x00000668  # target 0x00000668
loc_674:
    674: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    678: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    67c: 016e8eb3  add          x29, x29, x22
    680: 001f0f13  addi         x30, x30, 1
    684: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    688: 015f1663  bne          x30, x21, 0x00000694  # target 0x00000694
    68c: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    690: 016f8fb3  add          x31, x31, x22
loc_694:
    694: fffe0e13  addi         x28, x28, -1
    698: f20e18e3  bne          x28, x0, 0x000005c8  # target 0x000005c8
    69c: 00008067  jalr         x0, 0(x1)
    6a0: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6a4: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6a8: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6ac: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6b0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6b4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6b8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    6bc: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6c0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6c4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6cc: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    6d0:           j FW_BRISC+4   # return to firmware, linked at install
