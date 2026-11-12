# llama3 8b-bf16 decode: qkv, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_l0_k, 0x78c=e2e_l0_v, 0x790=e2e_l0_input_norm, 0xe8c0=e2e_q_compact, 0xe8c4=e2e_l0_q_row_start, 0xe8c8=e2e_k_compact, 0xe8cc=e2e_l0_k_row_start, 0xe8d0=e2e_v_compact, 0xe8d4=e2e_l0_v_row_start, 0xe8d8=e2e_l0_q_rows, 0xe8dc=e2e_l0_k_rows, 0xe8e0=e2e_l0_v_rows, 0xe8e4=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000182b7  lui          x5, 0x00018  # x5 = 0x00018000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x00017800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00017800
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
     60: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
     64: 406383b3  sub          x7, x7, x6
     68: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
     6c: 0083f663  bgeu         x7, x8, 0x00000078  # target 0x00000078
     70: 0ff0000f  fence        0xf, 0xf
     74: fd5ff06f  jal          x0, 0x00000048  # target 0x00000048
loc_78:
     78: 0ff0000f  fence        0xf, 0xf
     7c: 500000ef  jal          x1, 0x0000057c  # target 0x0000057c; x1 = 0x00000080
     80: 518000ef  jal          x1, 0x00000598  # target 0x00000598; x1 = 0x00000084
     84: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     88: 52c000ef  jal          x1, 0x000005b4  # target 0x000005b4; x1 = 0x0000008c
     8c: 000a8213  addi         x4, x21, 0
     90: 000b0293  addi         x5, x22, 0
     94: 00020f93  addi         x31, x4, 0
     98: 00028f13  addi         x30, x5, 0
     9c: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     a0: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00017800
     a4: 594000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x000000a8
     a8: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     ac: 508000ef  jal          x1, 0x000005b4  # target 0x000005b4; x1 = 0x000000b0
     b0: 000a8213  addi         x4, x21, 0
     b4: 000b0293  addi         x5, x22, 0
     b8: 00020f93  addi         x31, x4, 0
     bc: 00028f13  addi         x30, x5, 0
     c0: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     c4: 574000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x000000c8
     c8: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     cc: 4e8000ef  jal          x1, 0x000005b4  # target 0x000005b4; x1 = 0x000000d0
     d0: 000a8213  addi         x4, x21, 0
     d4: 000b0293  addi         x5, x22, 0
     d8: 00020f93  addi         x31, x4, 0
     dc: 00028f13  addi         x30, x5, 0
     e0: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
     e4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00018800
     e8: 550000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x000000ec
     ec: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     f0: 4c4000ef  jal          x1, 0x000005b4  # target 0x000005b4; x1 = 0x000000f4
     f4: 000a8213  addi         x4, x21, 0
     f8: 000b0293  addi         x5, x22, 0
     fc: 00020f93  addi         x31, x4, 0
    100: 00028f13  addi         x30, x5, 0
    104: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
    108: 530000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x0000010c
    10c: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    110: 5cc000ef  jal          x1, 0x000006dc  # target 0x000006dc; x1 = 0x00000114
    114: 000a8213  addi         x4, x21, 0
    118: 000b0293  addi         x5, x22, 0
    11c: 00020f93  addi         x31, x4, 0
    120: 00028f13  addi         x30, x5, 0
    124: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
    128: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00019800
    12c: 50c000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x00000130
    130: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    134: 5a8000ef  jal          x1, 0x000006dc  # target 0x000006dc; x1 = 0x00000138
    138: 000a8213  addi         x4, x21, 0
    13c: 000b0293  addi         x5, x22, 0
    140: 00020f93  addi         x31, x4, 0
    144: 00028f13  addi         x30, x5, 0
    148: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
    14c: 4ec000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x00000150
    150: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    154: 588000ef  jal          x1, 0x000006dc  # target 0x000006dc; x1 = 0x00000158
    158: 000a8213  addi         x4, x21, 0
    15c: 000b0293  addi         x5, x22, 0
    160: 00020f93  addi         x31, x4, 0
    164: 00028f13  addi         x30, x5, 0
    168: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    16c: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001a800
    170: 4c8000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x00000174
    174: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    178: 564000ef  jal          x1, 0x000006dc  # target 0x000006dc; x1 = 0x0000017c
    17c: 000a8213  addi         x4, x21, 0
    180: 000b0293  addi         x5, x22, 0
    184: 00020f93  addi         x31, x4, 0
    188: 00028f13  addi         x30, x5, 0
    18c: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    190: 4a8000ef  jal          x1, 0x00000638  # target 0x00000638; x1 = 0x00000194
    194: 404000ef  jal          x1, 0x00000598  # target 0x00000598; x1 = 0x00000198
    198: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    19c: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1a0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1a4: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    1a8: 00520233  add          x4, x4, x5
    1ac: 0001c337  lui          x6, 0x0001c  # x6 = 0x0001c000
    1b0: 80030313  addi         x6, x6, -2048  # x6 = 0x0001b800
    1b4: 00626663  bltu         x4, x6, 0x000001c0  # target 0x000001c0
    1b8: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    1bc: 40720233  sub          x4, x4, x7
loc_1c0:
    1c0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1c4: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1c8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1cc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1d0: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1d4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    1d8: 00820213  addi         x4, x4, 8
    1dc: 01021213  slli         x4, x4, 16
    1e0: 01025213  srli         x4, x4, 16
    1e4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e8: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1ec: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1f0: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    1f4: 02828293  addi         x5, x5, 40  # x5 = 0xffb4e028
    1f8: 0042a023  sw           x4, 0(x5)  # 0xffb4e028; write runtime value
    1fc: 0ff0000f  fence        0xf, 0xf
    200: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    204: 8d828293  addi         x5, x5, -1832  # x5 = 0x0000e8d8
    208: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0000e8d8
    20c: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    210: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    214: ff82f293  andi         x5, x5, -8
    218: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    21c: 8c448493  addi         x9, x9, -1852  # x9 = 0x0000e8c4
    220: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x0000e8c4
    224: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    228: 028383b3  mul          x7, x7, x8
    22c: 0073f313  andi         x6, x7, 7
    230: 0033d393  srli         x7, x7, 3
    234: 00b39393  slli         x7, x7, 11
    238: 007282b3  add          x5, x5, x7
    23c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    240: 00020413  addi         x8, x4, 0
loc_244:
    244: 0e83f263  bgeu         x7, x8, 0x00000328  # target 0x00000328
    248: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    24c: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    250: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_254:
    254: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    258: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    25c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    260: 40a485b3  sub          x11, x9, x10
    264: 01059593  slli         x11, x11, 16
    268: 0105d593  srli         x11, x11, 16
    26c: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    270: 40b60633  sub          x12, x12, x11
    274: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    278: 00d67663  bgeu         x12, x13, 0x00000284  # target 0x00000284
    27c: 0ff0000f  fence        0xf, 0xf
    280: fd5ff06f  jal          x0, 0x00000254  # target 0x00000254
loc_284:
    284: 0ff0000f  fence        0xf, 0xf
    288: 2f4000ef  jal          x1, 0x0000057c  # target 0x0000057c; x1 = 0x0000028c
    28c: 30c000ef  jal          x1, 0x00000598  # target 0x00000598; x1 = 0x00000290
    290: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    294: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    298: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    29c: 00028f93  addi         x31, x5, 0
    2a0: 00030f13  addi         x30, x6, 0
    2a4: 00048e93  addi         x29, x9, 0
    2a8: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    2ac: 4b4000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x000002b0
    2b0: 000f8293  addi         x5, x31, 0
    2b4: 000f0313  addi         x6, x30, 0
    2b8: 2e0000ef  jal          x1, 0x00000598  # target 0x00000598; x1 = 0x000002bc
    2bc: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2c0: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2c4: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2c8: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    2cc: 00a484b3  add          x9, x9, x10
    2d0: 000135b7  lui          x11, 0x00013  # x11 = 0x00013000
    2d4: 00b4e663  bltu         x9, x11, 0x000002e0  # target 0x000002e0
    2d8: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    2dc: 40c484b3  sub          x9, x9, x12
loc_2e0:
    2e0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2e4: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2e8: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    2ec: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2f0: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    2f4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    2f8: 00448493  addi         x9, x9, 4
    2fc: 01049493  slli         x9, x9, 16
    300: 0104d493  srli         x9, x9, 16
    304: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    308: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    30c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    310: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    314: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    318: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    31c: 0ff0000f  fence        0xf, 0xf
    320: 00138393  addi         x7, x7, 1
    324: f21ff06f  jal          x0, 0x00000244  # target 0x00000244
loc_328:
    328: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    32c: 8dc28293  addi         x5, x5, -1828  # x5 = 0x0000e8dc
    330: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x0000e8dc
    334: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
    338: 0003a283  lw           x5, 0(x7)  # param e2e_l0_k; 0x00000788
    33c: ff82f293  andi         x5, x5, -8
    340: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    344: 8cc48493  addi         x9, x9, -1844  # x9 = 0x0000e8cc
    348: 0004a383  lw           x7, 0(x9)  # param e2e_l0_k_row_start; 0x0000e8cc
    34c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    350: 028383b3  mul          x7, x7, x8
    354: 0073f313  andi         x6, x7, 7
    358: 0033d393  srli         x7, x7, 3
    35c: 00b39393  slli         x7, x7, 11
    360: 007282b3  add          x5, x5, x7
    364: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    368: 00020413  addi         x8, x4, 0
loc_36c:
    36c: 0e83f263  bgeu         x7, x8, 0x00000450  # target 0x00000450
    370: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    374: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    378: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_37c:
    37c: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    380: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    384: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    388: 40a485b3  sub          x11, x9, x10
    38c: 01059593  slli         x11, x11, 16
    390: 0105d593  srli         x11, x11, 16
    394: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    398: 40b60633  sub          x12, x12, x11
    39c: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    3a0: 00d67663  bgeu         x12, x13, 0x000003ac  # target 0x000003ac
    3a4: 0ff0000f  fence        0xf, 0xf
    3a8: fd5ff06f  jal          x0, 0x0000037c  # target 0x0000037c
loc_3ac:
    3ac: 0ff0000f  fence        0xf, 0xf
    3b0: 1cc000ef  jal          x1, 0x0000057c  # target 0x0000057c; x1 = 0x000003b4
    3b4: 1e4000ef  jal          x1, 0x00000598  # target 0x00000598; x1 = 0x000003b8
    3b8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3bc: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    3c0: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    3c4: 00028f93  addi         x31, x5, 0
    3c8: 00030f13  addi         x30, x6, 0
    3cc: 00048e93  addi         x29, x9, 0
    3d0: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    3d4: 38c000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x000003d8
    3d8: 000f8293  addi         x5, x31, 0
    3dc: 000f0313  addi         x6, x30, 0
    3e0: 1b8000ef  jal          x1, 0x00000598  # target 0x00000598; x1 = 0x000003e4
    3e4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    3e8: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    3ec: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    3f0: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    3f4: 00a484b3  add          x9, x9, x10
    3f8: 000135b7  lui          x11, 0x00013  # x11 = 0x00013000
    3fc: 00b4e663  bltu         x9, x11, 0x00000408  # target 0x00000408
    400: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    404: 40c484b3  sub          x9, x9, x12
loc_408:
    408: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    40c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    410: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    414: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    418: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    41c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    420: 00448493  addi         x9, x9, 4
    424: 01049493  slli         x9, x9, 16
    428: 0104d493  srli         x9, x9, 16
    42c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    430: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    434: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    438: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    43c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    440: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    444: 0ff0000f  fence        0xf, 0xf
    448: 00138393  addi         x7, x7, 1
    44c: f21ff06f  jal          x0, 0x0000036c  # target 0x0000036c
loc_450:
    450: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    454: 8e028293  addi         x5, x5, -1824  # x5 = 0x0000e8e0
    458: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x0000e8e0
    45c: 78c00393  addi         x7, x0, 1932  # x7 = 0x0000078c
    460: 0003a283  lw           x5, 0(x7)  # param e2e_l0_v; 0x0000078c
    464: ff82f293  andi         x5, x5, -8
    468: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    46c: 8d448493  addi         x9, x9, -1836  # x9 = 0x0000e8d4
    470: 0004a383  lw           x7, 0(x9)  # param e2e_l0_v_row_start; 0x0000e8d4
    474: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    478: 028383b3  mul          x7, x7, x8
    47c: 0073f313  andi         x6, x7, 7
    480: 0033d393  srli         x7, x7, 3
    484: 00b39393  slli         x7, x7, 11
    488: 007282b3  add          x5, x5, x7
    48c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    490: 00020413  addi         x8, x4, 0
loc_494:
    494: 0e83f263  bgeu         x7, x8, 0x00000578  # target 0x00000578
    498: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    49c: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    4a0: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_4a4:
    4a4: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    4a8: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    4ac: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    4b0: 40a485b3  sub          x11, x9, x10
    4b4: 01059593  slli         x11, x11, 16
    4b8: 0105d593  srli         x11, x11, 16
    4bc: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    4c0: 40b60633  sub          x12, x12, x11
    4c4: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    4c8: 00d67663  bgeu         x12, x13, 0x000004d4  # target 0x000004d4
    4cc: 0ff0000f  fence        0xf, 0xf
    4d0: fd5ff06f  jal          x0, 0x000004a4  # target 0x000004a4
loc_4d4:
    4d4: 0ff0000f  fence        0xf, 0xf
    4d8: 0a4000ef  jal          x1, 0x0000057c  # target 0x0000057c; x1 = 0x000004dc
    4dc: 0bc000ef  jal          x1, 0x00000598  # target 0x00000598; x1 = 0x000004e0
    4e0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4e4: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    4e8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    4ec: 00028f93  addi         x31, x5, 0
    4f0: 00030f13  addi         x30, x6, 0
    4f4: 00048e93  addi         x29, x9, 0
    4f8: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    4fc: 264000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x00000500
    500: 000f8293  addi         x5, x31, 0
    504: 000f0313  addi         x6, x30, 0
    508: 090000ef  jal          x1, 0x00000598  # target 0x00000598; x1 = 0x0000050c
    50c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    510: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    514: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    518: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    51c: 00a484b3  add          x9, x9, x10
    520: 000135b7  lui          x11, 0x00013  # x11 = 0x00013000
    524: 00b4e663  bltu         x9, x11, 0x00000530  # target 0x00000530
    528: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    52c: 40c484b3  sub          x9, x9, x12
loc_530:
    530: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    534: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    538: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    53c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    540: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    544: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    548: 00448493  addi         x9, x9, 4
    54c: 01049493  slli         x9, x9, 16
    550: 0104d493  srli         x9, x9, 16
    554: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    558: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    55c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    560: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    564: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    568: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    56c: 0ff0000f  fence        0xf, 0xf
    570: 00138393  addi         x7, x7, 1
    574: f21ff06f  jal          x0, 0x00000494  # target 0x00000494
loc_578:
    578: 3100006f  jal          x0, 0x00000888  # target 0x00000888
loc_57c:
    57c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    580: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    584: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    588: 000a0463  beq          x20, x0, 0x00000590  # target 0x00000590
    58c: ff1ff06f  jal          x0, 0x0000057c  # target 0x0000057c
loc_590:
    590: 0ff0000f  fence        0xf, 0xf
    594: 00008067  jalr         x0, 0(x1)
loc_598:
    598: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    59c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    5a0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    5a4: 000a0463  beq          x20, x0, 0x000005ac  # target 0x000005ac
    5a8: ff1ff06f  jal          x0, 0x00000598  # target 0x00000598
loc_5ac:
    5ac: 0ff0000f  fence        0xf, 0xf
    5b0: 00008067  jalr         x0, 0(x1)
loc_5b4:
    5b4: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    5b8: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x00000780
    5bc: 007a7d13  andi         x26, x20, 7
    5c0: ff8a7a13  andi         x20, x20, -8
    5c4: 01af8ab3  add          x21, x31, x26
    5c8: 007afb93  andi         x23, x21, 7
    5cc: 003ada93  srli         x21, x21, 3
    5d0: 00ba9a93  slli         x21, x21, 11
    5d4: 014a8ab3  add          x21, x21, x20
    5d8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005d8
    5dc: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000608
    5e0: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    5e4: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    5e8: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    5ec: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    5f0: 03cd8db3  mul          x27, x27, x28
    5f4: 01bb0b33  add          x22, x22, x27
    5f8: 001b9b93  slli         x23, x23, 1
    5fc: 017b0b33  add          x22, x22, x23
    600: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    604: 00008067  jalr         x0, 0(x1)
    608: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    60c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    610: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    614: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    618: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    61c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    620: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    624: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    628: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    62c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    630: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    634: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_638:
    638: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    63c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    640: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    644: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    648: 015a6463  bltu         x20, x21, 0x00000650  # target 0x00000650
    64c: fedff06f  jal          x0, 0x00000638  # target 0x00000638
loc_650:
    650: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    654: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    658: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    65c: 014a1a13  slli         x20, x20, 20
    660: 014a5a13  srli         x20, x20, 20
    664: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_668:
    668: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    66c: 000b0463  beq          x22, x0, 0x00000674  # target 0x00000674
    670: ff9ff06f  jal          x0, 0x00000668  # target 0x00000668
loc_674:
    674: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    678: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    67c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    680: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    684: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    688: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    68c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    690: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    694: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    698: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    69c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    6a0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    6a4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6a8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    6ac: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    6b0: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    6b4: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    6b8: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    6bc: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    6c0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    6c4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    6c8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_6cc:
    6cc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    6d0: 000b0463  beq          x22, x0, 0x000006d8  # target 0x000006d8
    6d4: ff9ff06f  jal          x0, 0x000006cc  # target 0x000006cc
loc_6d8:
    6d8: 00008067  jalr         x0, 0(x1)
loc_6dc:
    6dc: 79000a93  addi         x21, x0, 1936  # x21 = 0x00000790
    6e0: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_input_norm; 0x00000790
    6e4: 007a7d13  andi         x26, x20, 7
    6e8: ff8a7a13  andi         x20, x20, -8
    6ec: 01af8ab3  add          x21, x31, x26
    6f0: 007afb93  andi         x23, x21, 7
    6f4: 003ada93  srli         x21, x21, 3
    6f8: 00ba9a93  slli         x21, x21, 11
    6fc: 014a8ab3  add          x21, x21, x20
    700: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000700
    704: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000730
    708: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    70c: 8e4e8e93  addi         x29, x29, -1820  # x29 = 0x0000e8e4
    710: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e8e4
    714: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    718: 03cd8db3  mul          x27, x27, x28
    71c: 01bb0b33  add          x22, x22, x27
    720: 001b9b93  slli         x23, x23, 1
    724: 017b0b33  add          x22, x22, x23
    728: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    72c: 00008067  jalr         x0, 0(x1)
    730: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    734: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    738: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    73c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    740: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    744: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    748: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    74c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    750: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    754: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    758: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    75c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_760:
    760: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000760
    764: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000858
    768: 0000fcb7  lui          x25, 0x0000f  # x25 = 0x0000f000
    76c: 8e4c8c93  addi         x25, x25, -1820  # x25 = 0x0000e8e4
    770: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000e8e4
    774: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    778: 038b8bb3  mul          x23, x23, x24
    77c: 017a0a33  add          x20, x20, x23
loc_780:
    780: 001f1a93  slli         x21, x30, 1
    784: 014a8ab3  add          x21, x21, x20
    788: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_78c:
    78c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    790: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    794: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    798: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    79c: 018be463  bltu         x23, x24, 0x000007a4  # target 0x000007a4
    7a0: fedff06f  jal          x0, 0x0000078c  # target 0x0000078c
loc_7a4:
    7a4: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    7a8: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    7ac: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    7b0: 014b9b93  slli         x23, x23, 20
    7b4: 014bdb93  srli         x23, x23, 20
    7b8: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_7bc:
    7bc: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    7c0: 000c8463  beq          x25, x0, 0x000007c8  # target 0x000007c8
    7c4: ff9ff06f  jal          x0, 0x000007bc  # target 0x000007bc
loc_7c8:
    7c8: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    7cc: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    7d0: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    7d4: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    7d8: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    7dc: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    7e0: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    7e4: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    7e8: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    7ec: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    7f0: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    7f4: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    7f8: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7fc: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    800: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    804: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    808: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    80c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    810: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    814: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    818: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    81c: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_820:
    820: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    824: 000c8463  beq          x25, x0, 0x0000082c  # target 0x0000082c
    828: ff9ff06f  jal          x0, 0x00000820  # target 0x00000820
loc_82c:
    82c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    830: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    834: 016e8eb3  add          x29, x29, x22
    838: 001f0f13  addi         x30, x30, 1
    83c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    840: 015f1663  bne          x30, x21, 0x0000084c  # target 0x0000084c
    844: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    848: 016f8fb3  add          x31, x31, x22
loc_84c:
    84c: fffe0e13  addi         x28, x28, -1
    850: f20e18e3  bne          x28, x0, 0x00000780  # target 0x00000780
    854: 00008067  jalr         x0, 0(x1)
    858: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    85c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    860: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    864: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    868: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    86c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    870: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    874: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    878: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    87c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    880: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    884: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    888:           j FW_BRISC+4   # return to firmware, linked at install
