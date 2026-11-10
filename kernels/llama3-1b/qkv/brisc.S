# llama3 1b decode: qkv, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_l0_k, 0x78c=e2e_l0_v, 0x790=e2e_l0_input_norm, 0xe8c0=e2e_q_compact, 0xe8c4=e2e_l0_q_row_start, 0xe8c8=e2e_k_compact, 0xe8cc=e2e_l0_k_row_start, 0xe8d0=e2e_v_compact, 0xe8d4=e2e_l0_v_row_start, 0xe8d8=e2e_l0_q_rows, 0xe8dc=e2e_l0_k_rows, 0xe8e0=e2e_l0_v_rows, 0xe8e4=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000142b7  lui          x5, 0x00014  # x5 = 0x00014000
      c: 7c028293  addi         x5, x5, 1984  # x5 = 0x000147c0
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x000147c0
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 0000f537  lui          x10, 0x0000f  # x10 = 0x0000f000
     2c: fc050513  addi         x10, x10, -64  # x10 = 0x0000efc0
     30: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x0000efc0
     34: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     38: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
     3c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     40: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     44: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     48: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_4c:
     4c: ffb4e4b7  lui          x9, 0xffb4e  # x9 = 0xffb4e000
     50: 02048493  addi         x9, x9, 32  # x9 = 0xffb4e020
     54: 0004d283  lhu          x5, 0(x9)  # 0xffb4e020
     58: 40520333  sub          x6, x4, x5
     5c: 01031313  slli         x6, x6, 16
     60: 01035313  srli         x6, x6, 16
     64: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     68: 406383b3  sub          x7, x7, x6
     6c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
     70: 0083f663  bgeu         x7, x8, 0x0000007c  # target 0x0000007c
     74: 0ff0000f  fence        0xf, 0xf
     78: fd5ff06f  jal          x0, 0x0000004c  # target 0x0000004c
loc_7c:
     7c: 0ff0000f  fence        0xf, 0xf
     80: 48c000ef  jal          x1, 0x0000050c  # target 0x0000050c; x1 = 0x00000084
     84: 4a4000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 4b8000ef  jal          x1, 0x00000544  # target 0x00000544; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 00014eb7  lui          x29, 0x00014  # x29 = 0x00014000
     a4: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000147c0
     a8: 520000ef  jal          x1, 0x000005c8  # target 0x000005c8; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 494000ef  jal          x1, 0x00000544  # target 0x00000544; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
     c8: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00014fc0
     cc: 4fc000ef  jal          x1, 0x000005c8  # target 0x000005c8; x1 = 0x000000d0
     d0: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     d4: 598000ef  jal          x1, 0x0000066c  # target 0x0000066c; x1 = 0x000000d8
     d8: 000a8213  addi         x4, x21, 0
     dc: 000b0293  addi         x5, x22, 0
     e0: 00020f93  addi         x31, x4, 0
     e4: 00028f13  addi         x30, x5, 0
     e8: 00015eb7  lui          x29, 0x00015  # x29 = 0x00015000
     ec: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000157c0
     f0: 4d8000ef  jal          x1, 0x000005c8  # target 0x000005c8; x1 = 0x000000f4
     f4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     f8: 574000ef  jal          x1, 0x0000066c  # target 0x0000066c; x1 = 0x000000fc
     fc: 000a8213  addi         x4, x21, 0
    100: 000b0293  addi         x5, x22, 0
    104: 00020f93  addi         x31, x4, 0
    108: 00028f13  addi         x30, x5, 0
    10c: 00016eb7  lui          x29, 0x00016  # x29 = 0x00016000
    110: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00015fc0
    114: 4b4000ef  jal          x1, 0x000005c8  # target 0x000005c8; x1 = 0x00000118
    118: 410000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x0000011c
    11c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    120: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    124: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    128: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    12c: 00520233  add          x4, x4, x5
    130: 00016337  lui          x6, 0x00016  # x6 = 0x00016000
    134: 7c030313  addi         x6, x6, 1984  # x6 = 0x000167c0
    138: 00626663  bltu         x4, x6, 0x00000144  # target 0x00000144
    13c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    140: 40720233  sub          x4, x4, x7
loc_144:
    144: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    148: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    14c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    150: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    154: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    158: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    15c: 00420213  addi         x4, x4, 4
    160: 01021213  slli         x4, x4, 16
    164: 01025213  srli         x4, x4, 16
    168: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    16c: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    170: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    174: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    178: 02828293  addi         x5, x5, 40  # x5 = 0xffb4e028
    17c: 0042a023  sw           x4, 0(x5)  # 0xffb4e028; write runtime value
    180: 0ff0000f  fence        0xf, 0xf
    184: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    188: 8d828293  addi         x5, x5, -1832  # x5 = 0x0000e8d8
    18c: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e8d8
    190: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    194: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    198: ff82f293  andi         x5, x5, -8
    19c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    1a0: 8c448493  addi         x9, x9, -1852  # x9 = 0x0000e8c4
    1a4: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x0000e8c4
    1a8: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    1ac: 028383b3  mul          x7, x7, x8
    1b0: 0073f313  andi         x6, x7, 7
    1b4: 0033d393  srli         x7, x7, 3
    1b8: 00b39393  slli         x7, x7, 11
    1bc: 007282b3  add          x5, x5, x7
    1c0: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1c4: 00020413  addi         x8, x4, 0
loc_1c8:
    1c8: 0e83f463  bgeu         x7, x8, 0x000002b0  # target 0x000002b0
    1cc: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1d0: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    1d4: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1d8:
    1d8: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1dc: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1e0: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1e4: 40a485b3  sub          x11, x9, x10
    1e8: 01059593  slli         x11, x11, 16
    1ec: 0105d593  srli         x11, x11, 16
    1f0: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    1f4: 40b60633  sub          x12, x12, x11
    1f8: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    1fc: 00d67663  bgeu         x12, x13, 0x00000208  # target 0x00000208
    200: 0ff0000f  fence        0xf, 0xf
    204: fd5ff06f  jal          x0, 0x000001d8  # target 0x000001d8
loc_208:
    208: 0ff0000f  fence        0xf, 0xf
    20c: 300000ef  jal          x1, 0x0000050c  # target 0x0000050c; x1 = 0x00000210
    210: 318000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x00000214
    214: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    218: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    21c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    220: 00028f93  addi         x31, x5, 0
    224: 00030f13  addi         x30, x6, 0
    228: 00048e93  addi         x29, x9, 0
    22c: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    230: 4c0000ef  jal          x1, 0x000006f0  # target 0x000006f0; x1 = 0x00000234
    234: 000f8293  addi         x5, x31, 0
    238: 000f0313  addi         x6, x30, 0
    23c: 2ec000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x00000240
    240: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    244: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    248: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    24c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    250: 00a484b3  add          x9, x9, x10
    254: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    258: fc058593  addi         x11, x11, -64  # x11 = 0x00010fc0
    25c: 00b4e663  bltu         x9, x11, 0x00000268  # target 0x00000268
    260: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    264: 40c484b3  sub          x9, x9, x12
loc_268:
    268: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    26c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    270: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    274: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    278: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    27c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    280: 00248493  addi         x9, x9, 2
    284: 01049493  slli         x9, x9, 16
    288: 0104d493  srli         x9, x9, 16
    28c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    290: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    294: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    298: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    29c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    2a0: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    2a4: 0ff0000f  fence        0xf, 0xf
    2a8: 00138393  addi         x7, x7, 1
    2ac: f1dff06f  jal          x0, 0x000001c8  # target 0x000001c8
loc_2b0:
    2b0: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    2b4: 8dc28293  addi         x5, x5, -1828  # x5 = 0x0000e8dc
    2b8: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x0000e8dc
    2bc: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
    2c0: 0003a283  lw           x5, 0(x7)  # param e2e_l0_k; 0x00000788
    2c4: ff82f293  andi         x5, x5, -8
    2c8: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    2cc: 8cc48493  addi         x9, x9, -1844  # x9 = 0x0000e8cc
    2d0: 0004a383  lw           x7, 0(x9)  # param e2e_l0_k_row_start; 0x0000e8cc
    2d4: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    2d8: 028383b3  mul          x7, x7, x8
    2dc: 0073f313  andi         x6, x7, 7
    2e0: 0033d393  srli         x7, x7, 3
    2e4: 00b39393  slli         x7, x7, 11
    2e8: 007282b3  add          x5, x5, x7
    2ec: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    2f0: 00020413  addi         x8, x4, 0
loc_2f4:
    2f4: 0e83f463  bgeu         x7, x8, 0x000003dc  # target 0x000003dc
    2f8: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2fc: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    300: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_304:
    304: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    308: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    30c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    310: 40a485b3  sub          x11, x9, x10
    314: 01059593  slli         x11, x11, 16
    318: 0105d593  srli         x11, x11, 16
    31c: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    320: 40b60633  sub          x12, x12, x11
    324: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    328: 00d67663  bgeu         x12, x13, 0x00000334  # target 0x00000334
    32c: 0ff0000f  fence        0xf, 0xf
    330: fd5ff06f  jal          x0, 0x00000304  # target 0x00000304
loc_334:
    334: 0ff0000f  fence        0xf, 0xf
    338: 1d4000ef  jal          x1, 0x0000050c  # target 0x0000050c; x1 = 0x0000033c
    33c: 1ec000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x00000340
    340: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    344: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    348: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    34c: 00028f93  addi         x31, x5, 0
    350: 00030f13  addi         x30, x6, 0
    354: 00048e93  addi         x29, x9, 0
    358: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    35c: 394000ef  jal          x1, 0x000006f0  # target 0x000006f0; x1 = 0x00000360
    360: 000f8293  addi         x5, x31, 0
    364: 000f0313  addi         x6, x30, 0
    368: 1c0000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x0000036c
    36c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    370: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    374: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    378: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    37c: 00a484b3  add          x9, x9, x10
    380: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    384: fc058593  addi         x11, x11, -64  # x11 = 0x00010fc0
    388: 00b4e663  bltu         x9, x11, 0x00000394  # target 0x00000394
    38c: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    390: 40c484b3  sub          x9, x9, x12
loc_394:
    394: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    398: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    39c: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    3a0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3a4: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    3a8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    3ac: 00248493  addi         x9, x9, 2
    3b0: 01049493  slli         x9, x9, 16
    3b4: 0104d493  srli         x9, x9, 16
    3b8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3bc: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    3c0: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    3c4: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    3c8: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    3cc: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    3d0: 0ff0000f  fence        0xf, 0xf
    3d4: 00138393  addi         x7, x7, 1
    3d8: f1dff06f  jal          x0, 0x000002f4  # target 0x000002f4
loc_3dc:
    3dc: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    3e0: 8e028293  addi         x5, x5, -1824  # x5 = 0x0000e8e0
    3e4: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x0000e8e0
    3e8: 78c00393  addi         x7, x0, 1932  # x7 = 0x0000078c
    3ec: 0003a283  lw           x5, 0(x7)  # param e2e_l0_v; 0x0000078c
    3f0: ff82f293  andi         x5, x5, -8
    3f4: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    3f8: 8d448493  addi         x9, x9, -1836  # x9 = 0x0000e8d4
    3fc: 0004a383  lw           x7, 0(x9)  # param e2e_l0_v_row_start; 0x0000e8d4
    400: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    404: 028383b3  mul          x7, x7, x8
    408: 0073f313  andi         x6, x7, 7
    40c: 0033d393  srli         x7, x7, 3
    410: 00b39393  slli         x7, x7, 11
    414: 007282b3  add          x5, x5, x7
    418: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    41c: 00020413  addi         x8, x4, 0
loc_420:
    420: 0e83f463  bgeu         x7, x8, 0x00000508  # target 0x00000508
    424: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    428: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    42c: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_430:
    430: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    434: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    438: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    43c: 40a485b3  sub          x11, x9, x10
    440: 01059593  slli         x11, x11, 16
    444: 0105d593  srli         x11, x11, 16
    448: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    44c: 40b60633  sub          x12, x12, x11
    450: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    454: 00d67663  bgeu         x12, x13, 0x00000460  # target 0x00000460
    458: 0ff0000f  fence        0xf, 0xf
    45c: fd5ff06f  jal          x0, 0x00000430  # target 0x00000430
loc_460:
    460: 0ff0000f  fence        0xf, 0xf
    464: 0a8000ef  jal          x1, 0x0000050c  # target 0x0000050c; x1 = 0x00000468
    468: 0c0000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x0000046c
    46c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    470: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    474: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    478: 00028f93  addi         x31, x5, 0
    47c: 00030f13  addi         x30, x6, 0
    480: 00048e93  addi         x29, x9, 0
    484: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    488: 268000ef  jal          x1, 0x000006f0  # target 0x000006f0; x1 = 0x0000048c
    48c: 000f8293  addi         x5, x31, 0
    490: 000f0313  addi         x6, x30, 0
    494: 094000ef  jal          x1, 0x00000528  # target 0x00000528; x1 = 0x00000498
    498: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    49c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    4a0: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    4a4: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4a8: 00a484b3  add          x9, x9, x10
    4ac: 000115b7  lui          x11, 0x00011  # x11 = 0x00011000
    4b0: fc058593  addi         x11, x11, -64  # x11 = 0x00010fc0
    4b4: 00b4e663  bltu         x9, x11, 0x000004c0  # target 0x000004c0
    4b8: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    4bc: 40c484b3  sub          x9, x9, x12
loc_4c0:
    4c0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    4c4: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    4c8: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    4cc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4d0: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    4d4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    4d8: 00248493  addi         x9, x9, 2
    4dc: 01049493  slli         x9, x9, 16
    4e0: 0104d493  srli         x9, x9, 16
    4e4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4e8: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    4ec: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    4f0: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    4f4: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    4f8: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    4fc: 0ff0000f  fence        0xf, 0xf
    500: 00138393  addi         x7, x7, 1
    504: f1dff06f  jal          x0, 0x00000420  # target 0x00000420
loc_508:
    508: 3100006f  jal          x0, 0x00000818  # target 0x00000818
loc_50c:
    50c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    510: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    514: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    518: 000a0463  beq          x20, x0, 0x00000520  # target 0x00000520
    51c: ff1ff06f  jal          x0, 0x0000050c  # target 0x0000050c
loc_520:
    520: 0ff0000f  fence        0xf, 0xf
    524: 00008067  jalr         x0, 0(x1)
loc_528:
    528: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    52c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    530: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    534: 000a0463  beq          x20, x0, 0x0000053c  # target 0x0000053c
    538: ff1ff06f  jal          x0, 0x00000528  # target 0x00000528
loc_53c:
    53c: 0ff0000f  fence        0xf, 0xf
    540: 00008067  jalr         x0, 0(x1)
loc_544:
    544: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    548: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x00000780
    54c: 007a7d13  andi         x26, x20, 7
    550: ff8a7a13  andi         x20, x20, -8
    554: 01af8ab3  add          x21, x31, x26
    558: 007afb93  andi         x23, x21, 7
    55c: 003ada93  srli         x21, x21, 3
    560: 00ba9a93  slli         x21, x21, 11
    564: 014a8ab3  add          x21, x21, x20
    568: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000568
    56c: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000598
    570: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    574: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    578: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    57c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    580: 03cd8db3  mul          x27, x27, x28
    584: 01bb0b33  add          x22, x22, x27
    588: 001b9b93  slli         x23, x23, 1
    58c: 017b0b33  add          x22, x22, x23
    590: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    594: 00008067  jalr         x0, 0(x1)
    598: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    59c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5a0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    5a4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    5a8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5ac: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5b0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    5b4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    5b8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    5bc: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5c0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5c4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_5c8:
    5c8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5cc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    5d0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    5d4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    5d8: 015a6463  bltu         x20, x21, 0x000005e0  # target 0x000005e0
    5dc: fedff06f  jal          x0, 0x000005c8  # target 0x000005c8
loc_5e0:
    5e0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5e4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    5e8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    5ec: 014a1a13  slli         x20, x20, 20
    5f0: 014a5a13  srli         x20, x20, 20
    5f4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_5f8:
    5f8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5fc: 000b0463  beq          x22, x0, 0x00000604  # target 0x00000604
    600: ff9ff06f  jal          x0, 0x000005f8  # target 0x000005f8
loc_604:
    604: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    608: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    60c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    610: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    614: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    618: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    61c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    620: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    624: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    628: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    62c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    630: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    634: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    638: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    63c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    640: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    644: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    648: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    64c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    650: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    654: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    658: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_65c:
    65c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    660: 000b0463  beq          x22, x0, 0x00000668  # target 0x00000668
    664: ff9ff06f  jal          x0, 0x0000065c  # target 0x0000065c
loc_668:
    668: 00008067  jalr         x0, 0(x1)
loc_66c:
    66c: 79000a93  addi         x21, x0, 1936  # x21 = 0x00000790
    670: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_input_norm; 0x00000790
    674: 007a7d13  andi         x26, x20, 7
    678: ff8a7a13  andi         x20, x20, -8
    67c: 01af8ab3  add          x21, x31, x26
    680: 007afb93  andi         x23, x21, 7
    684: 003ada93  srli         x21, x21, 3
    688: 00ba9a93  slli         x21, x21, 11
    68c: 014a8ab3  add          x21, x21, x20
    690: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000690
    694: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006c0
    698: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    69c: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    6a0: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    6a4: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    6a8: 03cd8db3  mul          x27, x27, x28
    6ac: 01bb0b33  add          x22, x22, x27
    6b0: 001b9b93  slli         x23, x23, 1
    6b4: 017b0b33  add          x22, x22, x23
    6b8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6bc: 00008067  jalr         x0, 0(x1)
    6c0: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c4: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c8: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6cc: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6d0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    6dc: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6e0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6e4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6e8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6ec: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_6f0:
    6f0: 00000a17  auipc        x20, 0x00000  # x20 = 0x000006f0
    6f4: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000007e8
    6f8: 0000fcb7  lui          x25, 0x0000f  # x25 = 0x0000f000
    6fc: 8e4c8c93  addi         x25, x25, -1820  # x25 = 0x0000e8e4
    700: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000e8e4
    704: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    708: 038b8bb3  mul          x23, x23, x24
    70c: 017a0a33  add          x20, x20, x23
loc_710:
    710: 001f1a93  slli         x21, x30, 1
    714: 014a8ab3  add          x21, x21, x20
    718: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_71c:
    71c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    720: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    724: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    728: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    72c: 018be463  bltu         x23, x24, 0x00000734  # target 0x00000734
    730: fedff06f  jal          x0, 0x0000071c  # target 0x0000071c
loc_734:
    734: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    738: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    73c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    740: 014b9b93  slli         x23, x23, 20
    744: 014bdb93  srli         x23, x23, 20
    748: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_74c:
    74c: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    750: 000c8463  beq          x25, x0, 0x00000758  # target 0x00000758
    754: ff9ff06f  jal          x0, 0x0000074c  # target 0x0000074c
loc_758:
    758: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    75c: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    760: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    764: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    768: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    76c: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    770: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    774: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    778: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    77c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    780: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    784: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    788: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    78c: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    790: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    794: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    798: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    79c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    7a0: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    7a4: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    7a8: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    7ac: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_7b0:
    7b0: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    7b4: 000c8463  beq          x25, x0, 0x000007bc  # target 0x000007bc
    7b8: ff9ff06f  jal          x0, 0x000007b0  # target 0x000007b0
loc_7bc:
    7bc: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7c0: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    7c4: 016e8eb3  add          x29, x29, x22
    7c8: 001f0f13  addi         x30, x30, 1
    7cc: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    7d0: 015f1663  bne          x30, x21, 0x000007dc  # target 0x000007dc
    7d4: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    7d8: 016f8fb3  add          x31, x31, x22
loc_7dc:
    7dc: fffe0e13  addi         x28, x28, -1
    7e0: f20e18e3  bne          x28, x0, 0x00000710  # target 0x00000710
    7e4: 00008067  jalr         x0, 0(x1)
    7e8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7ec: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7f0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7f4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    7f8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7fc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    800: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    804: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    808: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    80c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    810: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    814: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    818:           j FW_BRISC+4   # return to firmware, linked at install
