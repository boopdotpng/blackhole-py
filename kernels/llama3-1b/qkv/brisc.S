# llama3 1b decode: qkv, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_l0_k, 0x78c=e2e_l0_v, 0x790=e2e_l0_input_norm, 0xe8c0=e2e_q_compact, 0xe8c4=e2e_l0_q_row_start, 0xe8c8=e2e_k_compact, 0xe8cc=e2e_l0_k_row_start, 0xe8d0=e2e_v_compact, 0xe8d4=e2e_l0_v_row_start, 0xe8d8=e2e_l0_q_rows, 0xe8dc=e2e_l0_k_rows, 0xe8e0=e2e_l0_v_rows, 0xe8e4=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000152b7  lui          x5, 0x00015  # x5 = 0x00015000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x00014800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00014800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 0000f537  lui          x10, 0x0000f  # x10 = 0x0000f000
     2c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x0000f000
     30: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     34: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
     38: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     3c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     40: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     44: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_48:
     48: ffb4e4b7  lui          x9, 0xffb4e  # x9 = 0xffb4e000
     4c: 02048493  addi         x9, x9, 32  # x9 = 0xffb4e020
     50: 0004d283  lhu          x5, 0(x9)  # 0xffb4e020
     54: 40520333  sub          x6, x4, x5
     58: 01031313  slli         x6, x6, 16
     5c: 01035313  srli         x6, x6, 16
     60: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     64: 406383b3  sub          x7, x7, x6
     68: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
     6c: 0083f663  bgeu         x7, x8, 0x00000078  # target 0x00000078
     70: 0ff0000f  fence        0xf, 0xf
     74: fd5ff06f  jal          x0, 0x00000048  # target 0x00000048
loc_78:
     78: 0ff0000f  fence        0xf, 0xf
     7c: 478000ef  jal          x1, 0x000004f4  # target 0x000004f4; x1 = 0x00000080
     80: 490000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x00000084
     84: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     88: 4a4000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x0000008c
     8c: 000a8213  addi         x4, x21, 0
     90: 000b0293  addi         x5, x22, 0
     94: 00020f93  addi         x31, x4, 0
     98: 00028f13  addi         x30, x5, 0
     9c: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
     a0: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00014800
     a4: 50c000ef  jal          x1, 0x000005b0  # target 0x000005b0; x1 = 0x000000a8
     a8: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     ac: 480000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x000000b0
     b0: 000a8213  addi         x4, x21, 0
     b4: 000b0293  addi         x5, x22, 0
     b8: 00020f93  addi         x31, x4, 0
     bc: 00028f13  addi         x30, x5, 0
     c0: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
     c4: 4ec000ef  jal          x1, 0x000005b0  # target 0x000005b0; x1 = 0x000000c8
     c8: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     cc: 588000ef  jal          x1, 0x00000654  # target 0x00000654; x1 = 0x000000d0
     d0: 000a8213  addi         x4, x21, 0
     d4: 000b0293  addi         x5, x22, 0
     d8: 00020f93  addi         x31, x4, 0
     dc: 00028f13  addi         x30, x5, 0
     e0: 00016eb7  lui          x29, 0x00016  # x29 = 0x00016000
     e4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00015800
     e8: 4c8000ef  jal          x1, 0x000005b0  # target 0x000005b0; x1 = 0x000000ec
     ec: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     f0: 564000ef  jal          x1, 0x00000654  # target 0x00000654; x1 = 0x000000f4
     f4: 000a8213  addi         x4, x21, 0
     f8: 000b0293  addi         x5, x22, 0
     fc: 00020f93  addi         x31, x4, 0
    100: 00028f13  addi         x30, x5, 0
    104: 00016eb7  lui          x29, 0x00016  # x29 = 0x00016000
    108: 4a8000ef  jal          x1, 0x000005b0  # target 0x000005b0; x1 = 0x0000010c
    10c: 404000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x00000110
    110: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    114: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    118: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    11c: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    120: 00520233  add          x4, x4, x5
    124: 00017337  lui          x6, 0x00017  # x6 = 0x00017000
    128: 80030313  addi         x6, x6, -2048  # x6 = 0x00016800
    12c: 00626663  bltu         x4, x6, 0x00000138  # target 0x00000138
    130: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    134: 40720233  sub          x4, x4, x7
loc_138:
    138: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    13c: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    140: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    144: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    148: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    14c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    150: 00420213  addi         x4, x4, 4
    154: 01021213  slli         x4, x4, 16
    158: 01025213  srli         x4, x4, 16
    15c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    160: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    164: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    168: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    16c: 02828293  addi         x5, x5, 40  # x5 = 0xffb4e028
    170: 0042a023  sw           x4, 0(x5)  # 0xffb4e028; write runtime value
    174: 0ff0000f  fence        0xf, 0xf
    178: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    17c: 8d828293  addi         x5, x5, -1832  # x5 = 0x0000e8d8
    180: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e8d8
    184: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    188: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    18c: ff82f293  andi         x5, x5, -8
    190: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    194: 8c448493  addi         x9, x9, -1852  # x9 = 0x0000e8c4
    198: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x0000e8c4
    19c: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    1a0: 028383b3  mul          x7, x7, x8
    1a4: 0073f313  andi         x6, x7, 7
    1a8: 0033d393  srli         x7, x7, 3
    1ac: 00b39393  slli         x7, x7, 11
    1b0: 007282b3  add          x5, x5, x7
    1b4: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1b8: 00020413  addi         x8, x4, 0
loc_1bc:
    1bc: 0e83f263  bgeu         x7, x8, 0x000002a0  # target 0x000002a0
    1c0: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1c4: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    1c8: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1cc:
    1cc: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1d0: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1d4: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1d8: 40a485b3  sub          x11, x9, x10
    1dc: 01059593  slli         x11, x11, 16
    1e0: 0105d593  srli         x11, x11, 16
    1e4: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    1e8: 40b60633  sub          x12, x12, x11
    1ec: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    1f0: 00d67663  bgeu         x12, x13, 0x000001fc  # target 0x000001fc
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: fd5ff06f  jal          x0, 0x000001cc  # target 0x000001cc
loc_1fc:
    1fc: 0ff0000f  fence        0xf, 0xf
    200: 2f4000ef  jal          x1, 0x000004f4  # target 0x000004f4; x1 = 0x00000204
    204: 30c000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x00000208
    208: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    20c: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    210: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    214: 00028f93  addi         x31, x5, 0
    218: 00030f13  addi         x30, x6, 0
    21c: 00048e93  addi         x29, x9, 0
    220: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    224: 4b4000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000228
    228: 000f8293  addi         x5, x31, 0
    22c: 000f0313  addi         x6, x30, 0
    230: 2e0000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x00000234
    234: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    238: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    23c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    240: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    244: 00a484b3  add          x9, x9, x10
    248: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    24c: 00b4e663  bltu         x9, x11, 0x00000258  # target 0x00000258
    250: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    254: 40c484b3  sub          x9, x9, x12
loc_258:
    258: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    25c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    260: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    264: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    268: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    26c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    270: 00248493  addi         x9, x9, 2
    274: 01049493  slli         x9, x9, 16
    278: 0104d493  srli         x9, x9, 16
    27c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    280: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    284: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    288: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    28c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    290: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    294: 0ff0000f  fence        0xf, 0xf
    298: 00138393  addi         x7, x7, 1
    29c: f21ff06f  jal          x0, 0x000001bc  # target 0x000001bc
loc_2a0:
    2a0: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    2a4: 8dc28293  addi         x5, x5, -1828  # x5 = 0x0000e8dc
    2a8: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x0000e8dc
    2ac: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
    2b0: 0003a283  lw           x5, 0(x7)  # param e2e_l0_k; 0x00000788
    2b4: ff82f293  andi         x5, x5, -8
    2b8: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    2bc: 8cc48493  addi         x9, x9, -1844  # x9 = 0x0000e8cc
    2c0: 0004a383  lw           x7, 0(x9)  # param e2e_l0_k_row_start; 0x0000e8cc
    2c4: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    2c8: 028383b3  mul          x7, x7, x8
    2cc: 0073f313  andi         x6, x7, 7
    2d0: 0033d393  srli         x7, x7, 3
    2d4: 00b39393  slli         x7, x7, 11
    2d8: 007282b3  add          x5, x5, x7
    2dc: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    2e0: 00020413  addi         x8, x4, 0
loc_2e4:
    2e4: 0e83f263  bgeu         x7, x8, 0x000003c8  # target 0x000003c8
    2e8: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2ec: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    2f0: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_2f4:
    2f4: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    2f8: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    2fc: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    300: 40a485b3  sub          x11, x9, x10
    304: 01059593  slli         x11, x11, 16
    308: 0105d593  srli         x11, x11, 16
    30c: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    310: 40b60633  sub          x12, x12, x11
    314: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    318: 00d67663  bgeu         x12, x13, 0x00000324  # target 0x00000324
    31c: 0ff0000f  fence        0xf, 0xf
    320: fd5ff06f  jal          x0, 0x000002f4  # target 0x000002f4
loc_324:
    324: 0ff0000f  fence        0xf, 0xf
    328: 1cc000ef  jal          x1, 0x000004f4  # target 0x000004f4; x1 = 0x0000032c
    32c: 1e4000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x00000330
    330: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    334: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    338: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    33c: 00028f93  addi         x31, x5, 0
    340: 00030f13  addi         x30, x6, 0
    344: 00048e93  addi         x29, x9, 0
    348: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    34c: 38c000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000350
    350: 000f8293  addi         x5, x31, 0
    354: 000f0313  addi         x6, x30, 0
    358: 1b8000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x0000035c
    35c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    360: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    364: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    368: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    36c: 00a484b3  add          x9, x9, x10
    370: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    374: 00b4e663  bltu         x9, x11, 0x00000380  # target 0x00000380
    378: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    37c: 40c484b3  sub          x9, x9, x12
loc_380:
    380: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    384: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    388: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    38c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    390: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    394: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    398: 00248493  addi         x9, x9, 2
    39c: 01049493  slli         x9, x9, 16
    3a0: 0104d493  srli         x9, x9, 16
    3a4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3a8: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    3ac: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    3b0: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    3b4: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    3b8: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    3bc: 0ff0000f  fence        0xf, 0xf
    3c0: 00138393  addi         x7, x7, 1
    3c4: f21ff06f  jal          x0, 0x000002e4  # target 0x000002e4
loc_3c8:
    3c8: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    3cc: 8e028293  addi         x5, x5, -1824  # x5 = 0x0000e8e0
    3d0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x0000e8e0
    3d4: 78c00393  addi         x7, x0, 1932  # x7 = 0x0000078c
    3d8: 0003a283  lw           x5, 0(x7)  # param e2e_l0_v; 0x0000078c
    3dc: ff82f293  andi         x5, x5, -8
    3e0: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    3e4: 8d448493  addi         x9, x9, -1836  # x9 = 0x0000e8d4
    3e8: 0004a383  lw           x7, 0(x9)  # param e2e_l0_v_row_start; 0x0000e8d4
    3ec: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    3f0: 028383b3  mul          x7, x7, x8
    3f4: 0073f313  andi         x6, x7, 7
    3f8: 0033d393  srli         x7, x7, 3
    3fc: 00b39393  slli         x7, x7, 11
    400: 007282b3  add          x5, x5, x7
    404: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    408: 00020413  addi         x8, x4, 0
loc_40c:
    40c: 0e83f263  bgeu         x7, x8, 0x000004f0  # target 0x000004f0
    410: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    414: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    418: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_41c:
    41c: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    420: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    424: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    428: 40a485b3  sub          x11, x9, x10
    42c: 01059593  slli         x11, x11, 16
    430: 0105d593  srli         x11, x11, 16
    434: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    438: 40b60633  sub          x12, x12, x11
    43c: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    440: 00d67663  bgeu         x12, x13, 0x0000044c  # target 0x0000044c
    444: 0ff0000f  fence        0xf, 0xf
    448: fd5ff06f  jal          x0, 0x0000041c  # target 0x0000041c
loc_44c:
    44c: 0ff0000f  fence        0xf, 0xf
    450: 0a4000ef  jal          x1, 0x000004f4  # target 0x000004f4; x1 = 0x00000454
    454: 0bc000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x00000458
    458: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    45c: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    460: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    464: 00028f93  addi         x31, x5, 0
    468: 00030f13  addi         x30, x6, 0
    46c: 00048e93  addi         x29, x9, 0
    470: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    474: 264000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000478
    478: 000f8293  addi         x5, x31, 0
    47c: 000f0313  addi         x6, x30, 0
    480: 090000ef  jal          x1, 0x00000510  # target 0x00000510; x1 = 0x00000484
    484: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    488: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    48c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    490: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    494: 00a484b3  add          x9, x9, x10
    498: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    49c: 00b4e663  bltu         x9, x11, 0x000004a8  # target 0x000004a8
    4a0: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    4a4: 40c484b3  sub          x9, x9, x12
loc_4a8:
    4a8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    4ac: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    4b0: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    4b4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4b8: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    4bc: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    4c0: 00248493  addi         x9, x9, 2
    4c4: 01049493  slli         x9, x9, 16
    4c8: 0104d493  srli         x9, x9, 16
    4cc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4d0: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    4d4: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    4d8: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    4dc: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    4e0: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    4e4: 0ff0000f  fence        0xf, 0xf
    4e8: 00138393  addi         x7, x7, 1
    4ec: f21ff06f  jal          x0, 0x0000040c  # target 0x0000040c
loc_4f0:
    4f0: 3100006f  jal          x0, 0x00000800  # target 0x00000800
loc_4f4:
    4f4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4f8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    4fc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    500: 000a0463  beq          x20, x0, 0x00000508  # target 0x00000508
    504: ff1ff06f  jal          x0, 0x000004f4  # target 0x000004f4
loc_508:
    508: 0ff0000f  fence        0xf, 0xf
    50c: 00008067  jalr         x0, 0(x1)
loc_510:
    510: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    514: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    518: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    51c: 000a0463  beq          x20, x0, 0x00000524  # target 0x00000524
    520: ff1ff06f  jal          x0, 0x00000510  # target 0x00000510
loc_524:
    524: 0ff0000f  fence        0xf, 0xf
    528: 00008067  jalr         x0, 0(x1)
loc_52c:
    52c: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    530: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x00000780
    534: 007a7d13  andi         x26, x20, 7
    538: ff8a7a13  andi         x20, x20, -8
    53c: 01af8ab3  add          x21, x31, x26
    540: 007afb93  andi         x23, x21, 7
    544: 003ada93  srli         x21, x21, 3
    548: 00ba9a93  slli         x21, x21, 11
    54c: 014a8ab3  add          x21, x21, x20
    550: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000550
    554: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000580
    558: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    55c: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    560: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    564: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    568: 03cd8db3  mul          x27, x27, x28
    56c: 01bb0b33  add          x22, x22, x27
    570: 001b9b93  slli         x23, x23, 1
    574: 017b0b33  add          x22, x22, x23
    578: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    57c: 00008067  jalr         x0, 0(x1)
    580: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    584: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    588: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    58c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    590: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    594: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    598: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    59c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    5a0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    5a4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5a8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5ac: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_5b0:
    5b0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5b4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    5b8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    5bc: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    5c0: 015a6463  bltu         x20, x21, 0x000005c8  # target 0x000005c8
    5c4: fedff06f  jal          x0, 0x000005b0  # target 0x000005b0
loc_5c8:
    5c8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5cc: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    5d0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    5d4: 014a1a13  slli         x20, x20, 20
    5d8: 014a5a13  srli         x20, x20, 20
    5dc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_5e0:
    5e0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5e4: 000b0463  beq          x22, x0, 0x000005ec  # target 0x000005ec
    5e8: ff9ff06f  jal          x0, 0x000005e0  # target 0x000005e0
loc_5ec:
    5ec: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5f0: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    5f4: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    5f8: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    5fc: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    600: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    604: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    608: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    60c: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    610: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    614: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    618: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    61c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    620: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    624: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    628: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    62c: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    630: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    634: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    638: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    63c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    640: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_644:
    644: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    648: 000b0463  beq          x22, x0, 0x00000650  # target 0x00000650
    64c: ff9ff06f  jal          x0, 0x00000644  # target 0x00000644
loc_650:
    650: 00008067  jalr         x0, 0(x1)
loc_654:
    654: 79000a93  addi         x21, x0, 1936  # x21 = 0x00000790
    658: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_input_norm; 0x00000790
    65c: 007a7d13  andi         x26, x20, 7
    660: ff8a7a13  andi         x20, x20, -8
    664: 01af8ab3  add          x21, x31, x26
    668: 007afb93  andi         x23, x21, 7
    66c: 003ada93  srli         x21, x21, 3
    670: 00ba9a93  slli         x21, x21, 11
    674: 014a8ab3  add          x21, x21, x20
    678: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000678
    67c: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006a8
    680: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    684: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    688: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    68c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    690: 03cd8db3  mul          x27, x27, x28
    694: 01bb0b33  add          x22, x22, x27
    698: 001b9b93  slli         x23, x23, 1
    69c: 017b0b33  add          x22, x22, x23
    6a0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6a4: 00008067  jalr         x0, 0(x1)
    6a8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6ac: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6b0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6b4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6b8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6bc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    6c4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6c8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6cc: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6d4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_6d8:
    6d8: 00000a17  auipc        x20, 0x00000  # x20 = 0x000006d8
    6dc: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000007d0
    6e0: 0000fcb7  lui          x25, 0x0000f  # x25 = 0x0000f000
    6e4: 8e4c8c93  addi         x25, x25, -1820  # x25 = 0x0000e8e4
    6e8: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000e8e4
    6ec: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    6f0: 038b8bb3  mul          x23, x23, x24
    6f4: 017a0a33  add          x20, x20, x23
loc_6f8:
    6f8: 001f1a93  slli         x21, x30, 1
    6fc: 014a8ab3  add          x21, x21, x20
    700: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_704:
    704: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    708: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    70c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    710: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    714: 018be463  bltu         x23, x24, 0x0000071c  # target 0x0000071c
    718: fedff06f  jal          x0, 0x00000704  # target 0x00000704
loc_71c:
    71c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    720: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    724: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    728: 014b9b93  slli         x23, x23, 20
    72c: 014bdb93  srli         x23, x23, 20
    730: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_734:
    734: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    738: 000c8463  beq          x25, x0, 0x00000740  # target 0x00000740
    73c: ff9ff06f  jal          x0, 0x00000734  # target 0x00000734
loc_740:
    740: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    744: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    748: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    74c: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    750: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    754: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    758: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    75c: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    760: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    764: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    768: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    76c: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    770: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    774: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    778: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    77c: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    780: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    784: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    788: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    78c: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    790: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    794: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_798:
    798: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    79c: 000c8463  beq          x25, x0, 0x000007a4  # target 0x000007a4
    7a0: ff9ff06f  jal          x0, 0x00000798  # target 0x00000798
loc_7a4:
    7a4: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7a8: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    7ac: 016e8eb3  add          x29, x29, x22
    7b0: 001f0f13  addi         x30, x30, 1
    7b4: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    7b8: 015f1663  bne          x30, x21, 0x000007c4  # target 0x000007c4
    7bc: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    7c0: 016f8fb3  add          x31, x31, x22
loc_7c4:
    7c4: fffe0e13  addi         x28, x28, -1
    7c8: f20e18e3  bne          x28, x0, 0x000006f8  # target 0x000006f8
    7cc: 00008067  jalr         x0, 0(x1)
    7d0: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7d4: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7d8: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7dc: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    7e0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7e4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7e8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    7ec: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    7f0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    7f4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7f8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    7fc: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    800:           j FW_BRISC+4   # return to firmware, linked at install
