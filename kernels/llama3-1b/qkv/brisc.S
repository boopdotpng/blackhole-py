# llama3 1b decode: qkv, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_q, 0x78c=e2e_l0_k, 0x790=e2e_k, 0x794=e2e_l0_v, 0x798=e2e_v, 0x79c=e2e_l0_input_norm, 0x118c0=e2e_l0_q_row_start, 0x118c4=e2e_l0_k_row_start, 0x118c8=e2e_l0_v_row_start, 0x118cc=e2e_l0_q_rows, 0x118d0=e2e_l0_k_rows, 0x118d4=e2e_l0_v_rows, 0x118d8=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000162b7  lui          x5, 0x00016  # x5 = 0x00016000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00016000
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
     44: ffb4b4b7  lui          x9, 0xffb4b  # x9 = 0xffb4b000
     48: 02048493  addi         x9, x9, 32  # x9 = 0xffb4b020
     4c: 0004d283  lhu          x5, 0(x9)  # 0xffb4b020
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
     78: 474000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x0000007c
     7c: 48c000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 4a0000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00016eb7  lui          x29, 0x00016  # x29 = 0x00016000
     9c: 50c000ef  jal          x1, 0x000005a8  # target 0x000005a8; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 480000ef  jal          x1, 0x00000524  # target 0x00000524; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00016800
     c0: 4e8000ef  jal          x1, 0x000005a8  # target 0x000005a8; x1 = 0x000000c4
     c4: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     c8: 584000ef  jal          x1, 0x0000064c  # target 0x0000064c; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     e0: 4c8000ef  jal          x1, 0x000005a8  # target 0x000005a8; x1 = 0x000000e4
     e4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     e8: 564000ef  jal          x1, 0x0000064c  # target 0x0000064c; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00017800
    104: 4a4000ef  jal          x1, 0x000005a8  # target 0x000005a8; x1 = 0x00000108
    108: 400000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x0000010c
    10c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    110: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    114: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    118: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    11c: 00520233  add          x4, x4, x5
    120: 00018337  lui          x6, 0x00018  # x6 = 0x00018000
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
    160: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    164: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    168: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    16c: 0ff0000f  fence        0xf, 0xf
    170: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    174: 8cc28293  addi         x5, x5, -1844  # x5 = 0x000118cc
    178: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x000118cc
    17c: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    180: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    184: ff82f293  andi         x5, x5, -8
    188: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    18c: 8c048493  addi         x9, x9, -1856  # x9 = 0x000118c0
    190: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x000118c0
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
    1f8: 2f4000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000001fc
    1fc: 30c000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000200
    200: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    204: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    208: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    20c: 00028f93  addi         x31, x5, 0
    210: 00030f13  addi         x30, x6, 0
    214: 00048e93  addi         x29, x9, 0
    218: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    21c: 4b4000ef  jal          x1, 0x000006d0  # target 0x000006d0; x1 = 0x00000220
    220: 000f8293  addi         x5, x31, 0
    224: 000f0313  addi         x6, x30, 0
    228: 2e0000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x0000022c
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
    29c: 8d028293  addi         x5, x5, -1840  # x5 = 0x000118d0
    2a0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x000118d0
    2a4: 78c00393  addi         x7, x0, 1932  # x7 = 0x0000078c
    2a8: 0003a283  lw           x5, 0(x7)  # param e2e_l0_k; 0x0000078c
    2ac: ff82f293  andi         x5, x5, -8
    2b0: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2b4: 8c448493  addi         x9, x9, -1852  # x9 = 0x000118c4
    2b8: 0004a383  lw           x7, 0(x9)  # param e2e_l0_k_row_start; 0x000118c4
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
    320: 1cc000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000324
    324: 1e4000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000328
    328: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    32c: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    330: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    334: 00028f93  addi         x31, x5, 0
    338: 00030f13  addi         x30, x6, 0
    33c: 00048e93  addi         x29, x9, 0
    340: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    344: 38c000ef  jal          x1, 0x000006d0  # target 0x000006d0; x1 = 0x00000348
    348: 000f8293  addi         x5, x31, 0
    34c: 000f0313  addi         x6, x30, 0
    350: 1b8000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000354
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
    3c0: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    3c4: 8d428293  addi         x5, x5, -1836  # x5 = 0x000118d4
    3c8: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x000118d4
    3cc: 79400393  addi         x7, x0, 1940  # x7 = 0x00000794
    3d0: 0003a283  lw           x5, 0(x7)  # param e2e_l0_v; 0x00000794
    3d4: ff82f293  andi         x5, x5, -8
    3d8: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    3dc: 8c848493  addi         x9, x9, -1848  # x9 = 0x000118c8
    3e0: 0004a383  lw           x7, 0(x9)  # param e2e_l0_v_row_start; 0x000118c8
    3e4: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    3e8: 028383b3  mul          x7, x7, x8
    3ec: 0073f313  andi         x6, x7, 7
    3f0: 0033d393  srli         x7, x7, 3
    3f4: 00b39393  slli         x7, x7, 11
    3f8: 007282b3  add          x5, x5, x7
    3fc: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    400: 00020413  addi         x8, x4, 0
loc_404:
    404: 0e83f263  bgeu         x7, x8, 0x000004e8  # target 0x000004e8
    408: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    40c: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    410: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_414:
    414: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    418: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    41c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    420: 40a485b3  sub          x11, x9, x10
    424: 01059593  slli         x11, x11, 16
    428: 0105d593  srli         x11, x11, 16
    42c: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    430: 40b60633  sub          x12, x12, x11
    434: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    438: 00d67663  bgeu         x12, x13, 0x00000444  # target 0x00000444
    43c: 0ff0000f  fence        0xf, 0xf
    440: fd5ff06f  jal          x0, 0x00000414  # target 0x00000414
loc_444:
    444: 0ff0000f  fence        0xf, 0xf
    448: 0a4000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x0000044c
    44c: 0bc000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x00000450
    450: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    454: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    458: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    45c: 00028f93  addi         x31, x5, 0
    460: 00030f13  addi         x30, x6, 0
    464: 00048e93  addi         x29, x9, 0
    468: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    46c: 264000ef  jal          x1, 0x000006d0  # target 0x000006d0; x1 = 0x00000470
    470: 000f8293  addi         x5, x31, 0
    474: 000f0313  addi         x6, x30, 0
    478: 090000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x0000047c
    47c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    480: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    484: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    488: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    48c: 00a484b3  add          x9, x9, x10
    490: 000145b7  lui          x11, 0x00014  # x11 = 0x00014000
    494: 00b4e663  bltu         x9, x11, 0x000004a0  # target 0x000004a0
    498: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    49c: 40c484b3  sub          x9, x9, x12
loc_4a0:
    4a0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    4a4: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    4a8: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    4ac: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4b0: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    4b4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    4b8: 00248493  addi         x9, x9, 2
    4bc: 01049493  slli         x9, x9, 16
    4c0: 0104d493  srli         x9, x9, 16
    4c4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4c8: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    4cc: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    4d0: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    4d4: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    4d8: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    4dc: 0ff0000f  fence        0xf, 0xf
    4e0: 00138393  addi         x7, x7, 1
    4e4: f21ff06f  jal          x0, 0x00000404  # target 0x00000404
loc_4e8:
    4e8: 3100006f  jal          x0, 0x000007f8  # target 0x000007f8
loc_4ec:
    4ec: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4f0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    4f4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    4f8: 000a0463  beq          x20, x0, 0x00000500  # target 0x00000500
    4fc: ff1ff06f  jal          x0, 0x000004ec  # target 0x000004ec
loc_500:
    500: 0ff0000f  fence        0xf, 0xf
    504: 00008067  jalr         x0, 0(x1)
loc_508:
    508: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    50c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    510: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    514: 000a0463  beq          x20, x0, 0x0000051c  # target 0x0000051c
    518: ff1ff06f  jal          x0, 0x00000508  # target 0x00000508
loc_51c:
    51c: 0ff0000f  fence        0xf, 0xf
    520: 00008067  jalr         x0, 0(x1)
loc_524:
    524: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    528: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x00000780
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
    554: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    558: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
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
    5a8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5ac: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    5b0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    5b4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    5b8: 015a6463  bltu         x20, x21, 0x000005c0  # target 0x000005c0
    5bc: fedff06f  jal          x0, 0x000005a8  # target 0x000005a8
loc_5c0:
    5c0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5c4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    5c8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    5cc: 014a1a13  slli         x20, x20, 20
    5d0: 014a5a13  srli         x20, x20, 20
    5d4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_5d8:
    5d8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5dc: 000b0463  beq          x22, x0, 0x000005e4  # target 0x000005e4
    5e0: ff9ff06f  jal          x0, 0x000005d8  # target 0x000005d8
loc_5e4:
    5e4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5e8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    5ec: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    5f0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    5f4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    5f8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    5fc: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    600: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    604: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    608: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    60c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    610: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    614: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    618: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    61c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    620: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    624: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    628: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    62c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    630: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    634: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    638: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_63c:
    63c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    640: 000b0463  beq          x22, x0, 0x00000648  # target 0x00000648
    644: ff9ff06f  jal          x0, 0x0000063c  # target 0x0000063c
loc_648:
    648: 00008067  jalr         x0, 0(x1)
loc_64c:
    64c: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    650: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_input_norm; 0x0000079c
    654: 007a7d13  andi         x26, x20, 7
    658: ff8a7a13  andi         x20, x20, -8
    65c: 01af8ab3  add          x21, x31, x26
    660: 007afb93  andi         x23, x21, 7
    664: 003ada93  srli         x21, x21, 3
    668: 00ba9a93  slli         x21, x21, 11
    66c: 014a8ab3  add          x21, x21, x20
    670: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000670
    674: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006a0
    678: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    67c: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    680: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    684: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    688: 03cd8db3  mul          x27, x27, x28
    68c: 01bb0b33  add          x22, x22, x27
    690: 001b9b93  slli         x23, x23, 1
    694: 017b0b33  add          x22, x22, x23
    698: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
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
loc_6d0:
    6d0: 00000a17  auipc        x20, 0x00000  # x20 = 0x000006d0
    6d4: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000007c8
    6d8: 00012cb7  lui          x25, 0x00012  # x25 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    6dc: 8d8c8c93  addi         x25, x25, -1832  # x25 = 0x000118d8
    6e0: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x000118d8
    6e4: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    6e8: 038b8bb3  mul          x23, x23, x24
    6ec: 017a0a33  add          x20, x20, x23
loc_6f0:
    6f0: 001f1a93  slli         x21, x30, 1
    6f4: 014a8ab3  add          x21, x21, x20
    6f8: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_6fc:
    6fc: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    700: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    704: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    708: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    70c: 018be463  bltu         x23, x24, 0x00000714  # target 0x00000714
    710: fedff06f  jal          x0, 0x000006fc  # target 0x000006fc
loc_714:
    714: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    718: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    71c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    720: 014b9b93  slli         x23, x23, 20
    724: 014bdb93  srli         x23, x23, 20
    728: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_72c:
    72c: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    730: 000c8463  beq          x25, x0, 0x00000738  # target 0x00000738
    734: ff9ff06f  jal          x0, 0x0000072c  # target 0x0000072c
loc_738:
    738: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    73c: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    740: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    744: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    748: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    74c: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    750: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    754: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    758: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    75c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    760: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    764: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    768: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    76c: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    770: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    774: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    778: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    77c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    780: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    784: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    788: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    78c: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_790:
    790: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    794: 000c8463  beq          x25, x0, 0x0000079c  # target 0x0000079c
    798: ff9ff06f  jal          x0, 0x00000790  # target 0x00000790
loc_79c:
    79c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7a0: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    7a4: 016e8eb3  add          x29, x29, x22
    7a8: 001f0f13  addi         x30, x30, 1
    7ac: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    7b0: 015f1663  bne          x30, x21, 0x000007bc  # target 0x000007bc
    7b4: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    7b8: 016f8fb3  add          x31, x31, x22
loc_7bc:
    7bc: fffe0e13  addi         x28, x28, -1
    7c0: f20e18e3  bne          x28, x0, 0x000006f0  # target 0x000006f0
    7c4: 00008067  jalr         x0, 0(x1)
    7c8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7cc: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7d0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7d4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    7d8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7dc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7e0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    7e4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    7e8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    7ec: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7f0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    7f4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    7f8:           j FW_BRISC+4   # return to firmware, linked at install
