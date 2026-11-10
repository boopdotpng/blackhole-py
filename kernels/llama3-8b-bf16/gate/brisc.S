# llama3 8b-bf16 decode: gate, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_b_decode_token, 0x784=e2e_l0_gate, 0x788=e2e_l0_up, 0x78c=e2e_hidden_dense, 0x790=e2e_l0_post_norm, 0xe940=e2e_gate, 0xe944=e2e_l0_gate_row_start, 0xe948=e2e_up, 0xe94c=e2e_l0_up_row_start, 0xe950=dense_start, 0xe954=e2e_l0_gate_rows, 0xe958=e2e_l0_up_rows, 0xe95c=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000172b7  lui          x5, 0x00017  # x5 = 0x00017000
      c: fc028293  addi         x5, x5, -64  # x5 = 0x00016fc0
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00016fc0
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
     4c: ffb4d4b7  lui          x9, 0xffb4d  # x9 = 0xffb4d000
     50: 02048493  addi         x9, x9, 32  # x9 = 0xffb4d020
     54: 0004d283  lhu          x5, 0(x9)  # 0xffb4d020
     58: 40520333  sub          x6, x4, x5
     5c: 01031313  slli         x6, x6, 16
     60: 01035313  srli         x6, x6, 16
     64: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
     68: 406383b3  sub          x7, x7, x6
     6c: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
     70: 0083f663  bgeu         x7, x8, 0x0000007c  # target 0x0000007c
     74: 0ff0000f  fence        0xf, 0xf
     78: fd5ff06f  jal          x0, 0x0000004c  # target 0x0000004c
loc_7c:
     7c: 0ff0000f  fence        0xf, 0xf
     80: 3f0000ef  jal          x1, 0x00000470  # target 0x00000470; x1 = 0x00000084
     84: 408000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 41c000ef  jal          x1, 0x000004a8  # target 0x000004a8; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     a4: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00016fc0
     a8: 484000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 3f8000ef  jal          x1, 0x000004a8  # target 0x000004a8; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00017eb7  lui          x29, 0x00017  # x29 = 0x00017000
     c8: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000177c0
     cc: 460000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x000000d0
     d0: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     d4: 3d4000ef  jal          x1, 0x000004a8  # target 0x000004a8; x1 = 0x000000d8
     d8: 000a8213  addi         x4, x21, 0
     dc: 000b0293  addi         x5, x22, 0
     e0: 00020f93  addi         x31, x4, 0
     e4: 00028f13  addi         x30, x5, 0
     e8: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
     ec: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00017fc0
     f0: 43c000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x000000f4
     f4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     f8: 3b0000ef  jal          x1, 0x000004a8  # target 0x000004a8; x1 = 0x000000fc
     fc: 000a8213  addi         x4, x21, 0
    100: 000b0293  addi         x5, x22, 0
    104: 00020f93  addi         x31, x4, 0
    108: 00028f13  addi         x30, x5, 0
    10c: 00018eb7  lui          x29, 0x00018  # x29 = 0x00018000
    110: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000187c0
    114: 418000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x00000118
    118: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    11c: 4b4000ef  jal          x1, 0x000005d0  # target 0x000005d0; x1 = 0x00000120
    120: 000a8213  addi         x4, x21, 0
    124: 000b0293  addi         x5, x22, 0
    128: 00020f93  addi         x31, x4, 0
    12c: 00028f13  addi         x30, x5, 0
    130: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
    134: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00018fc0
    138: 3f4000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x0000013c
    13c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    140: 490000ef  jal          x1, 0x000005d0  # target 0x000005d0; x1 = 0x00000144
    144: 000a8213  addi         x4, x21, 0
    148: 000b0293  addi         x5, x22, 0
    14c: 00020f93  addi         x31, x4, 0
    150: 00028f13  addi         x30, x5, 0
    154: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
    158: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x000197c0
    15c: 3d0000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x00000160
    160: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    164: 46c000ef  jal          x1, 0x000005d0  # target 0x000005d0; x1 = 0x00000168
    168: 000a8213  addi         x4, x21, 0
    16c: 000b0293  addi         x5, x22, 0
    170: 00020f93  addi         x31, x4, 0
    174: 00028f13  addi         x30, x5, 0
    178: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
    17c: fc0e8e93  addi         x29, x29, -64  # x29 = 0x00019fc0
    180: 3ac000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x00000184
    184: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    188: 448000ef  jal          x1, 0x000005d0  # target 0x000005d0; x1 = 0x0000018c
    18c: 000a8213  addi         x4, x21, 0
    190: 000b0293  addi         x5, x22, 0
    194: 00020f93  addi         x31, x4, 0
    198: 00028f13  addi         x30, x5, 0
    19c: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
    1a0: 7c0e8e93  addi         x29, x29, 1984  # x29 = 0x0001a7c0
    1a4: 388000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x000001a8
    1a8: 2e4000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x000001ac
    1ac: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1b0: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1b4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1b8: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    1bc: 00520233  add          x4, x4, x5
    1c0: 0001b337  lui          x6, 0x0001b  # x6 = 0x0001b000
    1c4: fc030313  addi         x6, x6, -64  # x6 = 0x0001afc0
    1c8: 00626663  bltu         x4, x6, 0x000001d4  # target 0x000001d4
    1cc: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    1d0: 40720233  sub          x4, x4, x7
loc_1d4:
    1d4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1d8: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1dc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1e0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e4: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1e8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    1ec: 00820213  addi         x4, x4, 8
    1f0: 01021213  slli         x4, x4, 16
    1f4: 01025213  srli         x4, x4, 16
    1f8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1fc: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    200: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    204: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    208: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    20c: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    210: 0ff0000f  fence        0xf, 0xf
    214: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    218: 95428293  addi         x5, x5, -1708  # x5 = 0x0000e954
    21c: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x0000e954
    220: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    224: 0003a283  lw           x5, 0(x7)  # param e2e_l0_gate; 0x00000784
    228: ff82f293  andi         x5, x5, -8
    22c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    230: 94448493  addi         x9, x9, -1724  # x9 = 0x0000e944
    234: 0004a383  lw           x7, 0(x9)  # param e2e_l0_gate_row_start; 0x0000e944
    238: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    23c: 028383b3  mul          x7, x7, x8
    240: 0073f313  andi         x6, x7, 7
    244: 0033d393  srli         x7, x7, 3
    248: 00b39393  slli         x7, x7, 11
    24c: 007282b3  add          x5, x5, x7
    250: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    254: 00020413  addi         x8, x4, 0
loc_258:
    258: 0e83f463  bgeu         x7, x8, 0x00000340  # target 0x00000340
    25c: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    260: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    264: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_268:
    268: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    26c: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    270: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    274: 40a485b3  sub          x11, x9, x10
    278: 01059593  slli         x11, x11, 16
    27c: 0105d593  srli         x11, x11, 16
    280: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    284: 40b60633  sub          x12, x12, x11
    288: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    28c: 00d67663  bgeu         x12, x13, 0x00000298  # target 0x00000298
    290: 0ff0000f  fence        0xf, 0xf
    294: fd5ff06f  jal          x0, 0x00000268  # target 0x00000268
loc_298:
    298: 0ff0000f  fence        0xf, 0xf
    29c: 1d4000ef  jal          x1, 0x00000470  # target 0x00000470; x1 = 0x000002a0
    2a0: 1ec000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x000002a4
    2a4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2a8: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    2ac: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    2b0: 00028f93  addi         x31, x5, 0
    2b4: 00030f13  addi         x30, x6, 0
    2b8: 00048e93  addi         x29, x9, 0
    2bc: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    2c0: 394000ef  jal          x1, 0x00000654  # target 0x00000654; x1 = 0x000002c4
    2c4: 000f8293  addi         x5, x31, 0
    2c8: 000f0313  addi         x6, x30, 0
    2cc: 1c0000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x000002d0
    2d0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2d4: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2d8: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2dc: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    2e0: 00a484b3  add          x9, x9, x10
    2e4: 000135b7  lui          x11, 0x00013  # x11 = 0x00013000
    2e8: fc058593  addi         x11, x11, -64  # x11 = 0x00012fc0
    2ec: 00b4e663  bltu         x9, x11, 0x000002f8  # target 0x000002f8
    2f0: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    2f4: 40c484b3  sub          x9, x9, x12
loc_2f8:
    2f8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2fc: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    300: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    304: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    308: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    30c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    310: 00448493  addi         x9, x9, 4
    314: 01049493  slli         x9, x9, 16
    318: 0104d493  srli         x9, x9, 16
    31c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    320: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    324: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    328: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    32c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    330: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    334: 0ff0000f  fence        0xf, 0xf
    338: 00138393  addi         x7, x7, 1
    33c: f1dff06f  jal          x0, 0x00000258  # target 0x00000258
loc_340:
    340: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    344: 95828293  addi         x5, x5, -1704  # x5 = 0x0000e958
    348: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x0000e958
    34c: 78800393  addi         x7, x0, 1928  # x7 = 0x00000788
    350: 0003a283  lw           x5, 0(x7)  # param e2e_l0_up; 0x00000788
    354: ff82f293  andi         x5, x5, -8
    358: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    35c: 94c48493  addi         x9, x9, -1716  # x9 = 0x0000e94c
    360: 0004a383  lw           x7, 0(x9)  # param e2e_l0_up_row_start; 0x0000e94c
    364: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    368: 028383b3  mul          x7, x7, x8
    36c: 0073f313  andi         x6, x7, 7
    370: 0033d393  srli         x7, x7, 3
    374: 00b39393  slli         x7, x7, 11
    378: 007282b3  add          x5, x5, x7
    37c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    380: 00020413  addi         x8, x4, 0
loc_384:
    384: 0e83f463  bgeu         x7, x8, 0x0000046c  # target 0x0000046c
    388: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    38c: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    390: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_394:
    394: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    398: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    39c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    3a0: 40a485b3  sub          x11, x9, x10
    3a4: 01059593  slli         x11, x11, 16
    3a8: 0105d593  srli         x11, x11, 16
    3ac: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    3b0: 40b60633  sub          x12, x12, x11
    3b4: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    3b8: 00d67663  bgeu         x12, x13, 0x000003c4  # target 0x000003c4
    3bc: 0ff0000f  fence        0xf, 0xf
    3c0: fd5ff06f  jal          x0, 0x00000394  # target 0x00000394
loc_3c4:
    3c4: 0ff0000f  fence        0xf, 0xf
    3c8: 0a8000ef  jal          x1, 0x00000470  # target 0x00000470; x1 = 0x000003cc
    3cc: 0c0000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x000003d0
    3d0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3d4: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    3d8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    3dc: 00028f93  addi         x31, x5, 0
    3e0: 00030f13  addi         x30, x6, 0
    3e4: 00048e93  addi         x29, x9, 0
    3e8: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    3ec: 268000ef  jal          x1, 0x00000654  # target 0x00000654; x1 = 0x000003f0
    3f0: 000f8293  addi         x5, x31, 0
    3f4: 000f0313  addi         x6, x30, 0
    3f8: 094000ef  jal          x1, 0x0000048c  # target 0x0000048c; x1 = 0x000003fc
    3fc: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    400: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    404: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    408: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    40c: 00a484b3  add          x9, x9, x10
    410: 000135b7  lui          x11, 0x00013  # x11 = 0x00013000
    414: fc058593  addi         x11, x11, -64  # x11 = 0x00012fc0
    418: 00b4e663  bltu         x9, x11, 0x00000424  # target 0x00000424
    41c: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    420: 40c484b3  sub          x9, x9, x12
loc_424:
    424: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    428: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    42c: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    430: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    434: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    438: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    43c: 00448493  addi         x9, x9, 4
    440: 01049493  slli         x9, x9, 16
    444: 0104d493  srli         x9, x9, 16
    448: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    44c: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    450: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    454: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    458: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    45c: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    460: 0ff0000f  fence        0xf, 0xf
    464: 00138393  addi         x7, x7, 1
    468: f1dff06f  jal          x0, 0x00000384  # target 0x00000384
loc_46c:
    46c: 3100006f  jal          x0, 0x0000077c  # target 0x0000077c
loc_470:
    470: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    474: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    478: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    47c: 000a0463  beq          x20, x0, 0x00000484  # target 0x00000484
    480: ff1ff06f  jal          x0, 0x00000470  # target 0x00000470
loc_484:
    484: 0ff0000f  fence        0xf, 0xf
    488: 00008067  jalr         x0, 0(x1)
loc_48c:
    48c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    490: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    494: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    498: 000a0463  beq          x20, x0, 0x000004a0  # target 0x000004a0
    49c: ff1ff06f  jal          x0, 0x0000048c  # target 0x0000048c
loc_4a0:
    4a0: 0ff0000f  fence        0xf, 0xf
    4a4: 00008067  jalr         x0, 0(x1)
loc_4a8:
    4a8: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    4ac: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b_decode_token; 0x00000780
    4b0: 007a7d13  andi         x26, x20, 7
    4b4: ff8a7a13  andi         x20, x20, -8
    4b8: 01af8ab3  add          x21, x31, x26
    4bc: 007afb93  andi         x23, x21, 7
    4c0: 003ada93  srli         x21, x21, 3
    4c4: 00ba9a93  slli         x21, x21, 11
    4c8: 014a8ab3  add          x21, x21, x20
    4cc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004cc
    4d0: 030b0b13  addi         x22, x22, 48  # x22 = 0x000004fc
    4d4: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    4d8: 95ce8e93  addi         x29, x29, -1700  # x29 = 0x0000e95c
    4dc: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e95c
    4e0: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4e4: 03cd8db3  mul          x27, x27, x28
    4e8: 01bb0b33  add          x22, x22, x27
    4ec: 001b9b93  slli         x23, x23, 1
    4f0: 017b0b33  add          x22, x22, x23
    4f4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4f8: 00008067  jalr         x0, 0(x1)
    4fc: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    500: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    504: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    508: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    50c: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    510: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    514: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    518: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    51c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    520: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    524: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    528: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_52c:
    52c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    530: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    534: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    538: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    53c: 015a6463  bltu         x20, x21, 0x00000544  # target 0x00000544
    540: fedff06f  jal          x0, 0x0000052c  # target 0x0000052c
loc_544:
    544: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    548: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    54c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    550: 014a1a13  slli         x20, x20, 20
    554: 014a5a13  srli         x20, x20, 20
    558: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_55c:
    55c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    560: 000b0463  beq          x22, x0, 0x00000568  # target 0x00000568
    564: ff9ff06f  jal          x0, 0x0000055c  # target 0x0000055c
loc_568:
    568: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    56c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    570: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    574: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    578: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    57c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    580: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    584: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    588: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    58c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    590: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    594: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    598: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    59c: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    5a0: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    5a4: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5a8: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5ac: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5b0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5b4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    5b8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5bc: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5c0:
    5c0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5c4: 000b0463  beq          x22, x0, 0x000005cc  # target 0x000005cc
    5c8: ff9ff06f  jal          x0, 0x000005c0  # target 0x000005c0
loc_5cc:
    5cc: 00008067  jalr         x0, 0(x1)
loc_5d0:
    5d0: 79000a93  addi         x21, x0, 1936  # x21 = 0x00000790
    5d4: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_post_norm; 0x00000790
    5d8: 007a7d13  andi         x26, x20, 7
    5dc: ff8a7a13  andi         x20, x20, -8
    5e0: 01af8ab3  add          x21, x31, x26
    5e4: 007afb93  andi         x23, x21, 7
    5e8: 003ada93  srli         x21, x21, 3
    5ec: 00ba9a93  slli         x21, x21, 11
    5f0: 014a8ab3  add          x21, x21, x20
    5f4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005f4
    5f8: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000624
    5fc: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    600: 95ce8e93  addi         x29, x29, -1700  # x29 = 0x0000e95c
    604: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e95c
    608: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    60c: 03cd8db3  mul          x27, x27, x28
    610: 01bb0b33  add          x22, x22, x27
    614: 001b9b93  slli         x23, x23, 1
    618: 017b0b33  add          x22, x22, x23
    61c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    620: 00008067  jalr         x0, 0(x1)
    624: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    628: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    62c: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    630: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    634: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    638: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    63c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    640: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    644: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    648: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    64c: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    650: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_654:
    654: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000654
    658: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x0000074c
    65c: 0000fcb7  lui          x25, 0x0000f  # x25 = 0x0000f000
    660: 95cc8c93  addi         x25, x25, -1700  # x25 = 0x0000e95c
    664: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000e95c
    668: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    66c: 038b8bb3  mul          x23, x23, x24
    670: 017a0a33  add          x20, x20, x23
loc_674:
    674: 001f1a93  slli         x21, x30, 1
    678: 014a8ab3  add          x21, x21, x20
    67c: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_680:
    680: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    684: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    688: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    68c: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    690: 018be463  bltu         x23, x24, 0x00000698  # target 0x00000698
    694: fedff06f  jal          x0, 0x00000680  # target 0x00000680
loc_698:
    698: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    69c: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    6a0: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    6a4: 014b9b93  slli         x23, x23, 20
    6a8: 014bdb93  srli         x23, x23, 20
    6ac: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_6b0:
    6b0: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    6b4: 000c8463  beq          x25, x0, 0x000006bc  # target 0x000006bc
    6b8: ff9ff06f  jal          x0, 0x000006b0  # target 0x000006b0
loc_6bc:
    6bc: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    6c0: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    6c4: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    6c8: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    6cc: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    6d0: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    6d4: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    6d8: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    6dc: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    6e0: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    6e4: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    6e8: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    6ec: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6f0: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    6f4: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    6f8: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    6fc: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    700: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    704: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    708: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    70c: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    710: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_714:
    714: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    718: 000c8463  beq          x25, x0, 0x00000720  # target 0x00000720
    71c: ff9ff06f  jal          x0, 0x00000714  # target 0x00000714
loc_720:
    720: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    724: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    728: 016e8eb3  add          x29, x29, x22
    72c: 001f0f13  addi         x30, x30, 1
    730: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    734: 015f1663  bne          x30, x21, 0x00000740  # target 0x00000740
    738: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    73c: 016f8fb3  add          x31, x31, x22
loc_740:
    740: fffe0e13  addi         x28, x28, -1
    744: f20e18e3  bne          x28, x0, 0x00000674  # target 0x00000674
    748: 00008067  jalr         x0, 0(x1)
    74c: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    750: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    754: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    758: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    75c: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    760: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    764: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    768: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    76c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    770: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    774: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    778: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    77c:           j FW_BRISC+4   # return to firmware, linked at install
