# llama3 8b-fp8 decode: qkv, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_q, 0x78c=e2e_l0_k, 0x790=e2e_k, 0x794=e2e_l0_v, 0x798=e2e_v, 0x79c=input_scale_0, 0x7a0=input_scale_1, 0x7a4=output_scale_0_0, 0x7a8=output_scale_0_1, 0x7ac=output_scale_1_0, 0x7b0=output_scale_1_1, 0x7b4=output_scale_2_0, 0x7b8=output_scale_2_1, 0x7bc=e2e_l0_input_norm, 0x118c0=e2e_l0_q_row_start, 0x118c4=e2e_l0_k_row_start, 0x118c8=e2e_l0_v_row_start, 0x118cc=e2e_l0_q_rows, 0x118d0=e2e_l0_k_rows, 0x118d4=e2e_l0_v_rows, 0x118d8=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000242b7  lui          x5, 0x00024  # x5 = 0x00024000
      c: 08028293  addi         x5, x5, 128  # x5 = 0x00024080
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00024080
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     2c: 08050513  addi         x10, x10, 128  # x10 = 0x00012080
     30: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00012080
     34: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     38: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
     3c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     40: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     44: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     48: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_4c:
     4c: ffb4b4b7  lui          x9, 0xffb4b  # x9 = 0xffb4b000
     50: 02048493  addi         x9, x9, 32  # x9 = 0xffb4b020
     54: 0004d283  lhu          x5, 0(x9)  # 0xffb4b020
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
     80: 51c000ef  jal          x1, 0x0000059c  # target 0x0000059c; x1 = 0x00000084
     84: 534000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x00000088
     88: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     8c: 548000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: 00020f93  addi         x31, x4, 0
     9c: 00028f13  addi         x30, x5, 0
     a0: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
     a4: 080e8e93  addi         x29, x29, 128  # x29 = 0x00024080
     a8: 5b0000ef  jal          x1, 0x00000658  # target 0x00000658; x1 = 0x000000ac
     ac: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     b0: 524000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x000000b4
     b4: 000a8213  addi         x4, x21, 0
     b8: 000b0293  addi         x5, x22, 0
     bc: 00020f93  addi         x31, x4, 0
     c0: 00028f13  addi         x30, x5, 0
     c4: 00025eb7  lui          x29, 0x00025  # x29 = 0x00025000
     c8: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00024880
     cc: 58c000ef  jal          x1, 0x00000658  # target 0x00000658; x1 = 0x000000d0
     d0: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     d4: 500000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x000000d8
     d8: 000a8213  addi         x4, x21, 0
     dc: 000b0293  addi         x5, x22, 0
     e0: 00020f93  addi         x31, x4, 0
     e4: 00028f13  addi         x30, x5, 0
     e8: 00025eb7  lui          x29, 0x00025  # x29 = 0x00025000
     ec: 080e8e93  addi         x29, x29, 128  # x29 = 0x00025080
     f0: 568000ef  jal          x1, 0x00000658  # target 0x00000658; x1 = 0x000000f4
     f4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     f8: 4dc000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x000000fc
     fc: 000a8213  addi         x4, x21, 0
    100: 000b0293  addi         x5, x22, 0
    104: 00020f93  addi         x31, x4, 0
    108: 00028f13  addi         x30, x5, 0
    10c: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    110: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00025880
    114: 544000ef  jal          x1, 0x00000658  # target 0x00000658; x1 = 0x00000118
    118: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    11c: 5e0000ef  jal          x1, 0x000006fc  # target 0x000006fc; x1 = 0x00000120
    120: 000a8213  addi         x4, x21, 0
    124: 000b0293  addi         x5, x22, 0
    128: 00020f93  addi         x31, x4, 0
    12c: 00028f13  addi         x30, x5, 0
    130: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    134: 080e8e93  addi         x29, x29, 128  # x29 = 0x00026080
    138: 520000ef  jal          x1, 0x00000658  # target 0x00000658; x1 = 0x0000013c
    13c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    140: 5bc000ef  jal          x1, 0x000006fc  # target 0x000006fc; x1 = 0x00000144
    144: 000a8213  addi         x4, x21, 0
    148: 000b0293  addi         x5, x22, 0
    14c: 00020f93  addi         x31, x4, 0
    150: 00028f13  addi         x30, x5, 0
    154: 00027eb7  lui          x29, 0x00027  # x29 = 0x00027000
    158: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00026880
    15c: 4fc000ef  jal          x1, 0x00000658  # target 0x00000658; x1 = 0x00000160
    160: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    164: 598000ef  jal          x1, 0x000006fc  # target 0x000006fc; x1 = 0x00000168
    168: 000a8213  addi         x4, x21, 0
    16c: 000b0293  addi         x5, x22, 0
    170: 00020f93  addi         x31, x4, 0
    174: 00028f13  addi         x30, x5, 0
    178: 00027eb7  lui          x29, 0x00027  # x29 = 0x00027000
    17c: 080e8e93  addi         x29, x29, 128  # x29 = 0x00027080
    180: 4d8000ef  jal          x1, 0x00000658  # target 0x00000658; x1 = 0x00000184
    184: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    188: 574000ef  jal          x1, 0x000006fc  # target 0x000006fc; x1 = 0x0000018c
    18c: 000a8213  addi         x4, x21, 0
    190: 000b0293  addi         x5, x22, 0
    194: 00020f93  addi         x31, x4, 0
    198: 00028f13  addi         x30, x5, 0
    19c: 00028eb7  lui          x29, 0x00028  # x29 = 0x00028000
    1a0: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00027880
    1a4: 4b4000ef  jal          x1, 0x00000658  # target 0x00000658; x1 = 0x000001a8
    1a8: 410000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x000001ac
    1ac: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1b0: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1b4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1b8: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    1bc: 00520233  add          x4, x4, x5
    1c0: 00028337  lui          x6, 0x00028  # x6 = 0x00028000
    1c4: 08030313  addi         x6, x6, 128  # x6 = 0x00028080
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
    204: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    208: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    20c: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    210: 0ff0000f  fence        0xf, 0xf
    214: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    218: 8cc28293  addi         x5, x5, -1844  # x5 = 0x000118cc
    21c: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x000118cc
    220: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    224: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    228: ff82f293  andi         x5, x5, -8
    22c: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    230: 8c048493  addi         x9, x9, -1856  # x9 = 0x000118c0
    234: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x000118c0
    238: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
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
    280: 04000613  addi         x12, x0, 64  # x12 = 0x00000040
    284: 40b60633  sub          x12, x12, x11
    288: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    28c: 00d67663  bgeu         x12, x13, 0x00000298  # target 0x00000298
    290: 0ff0000f  fence        0xf, 0xf
    294: fd5ff06f  jal          x0, 0x00000268  # target 0x00000268
loc_298:
    298: 0ff0000f  fence        0xf, 0xf
    29c: 300000ef  jal          x1, 0x0000059c  # target 0x0000059c; x1 = 0x000002a0
    2a0: 318000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x000002a4
    2a4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2a8: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    2ac: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    2b0: 00028f93  addi         x31, x5, 0
    2b4: 00030f13  addi         x30, x6, 0
    2b8: 00048e93  addi         x29, x9, 0
    2bc: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    2c0: 4c0000ef  jal          x1, 0x00000780  # target 0x00000780; x1 = 0x000002c4
    2c4: 000f8293  addi         x5, x31, 0
    2c8: 000f0313  addi         x6, x30, 0
    2cc: 2ec000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x000002d0
    2d0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2d4: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2d8: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2dc: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2e0: 00a484b3  add          x9, x9, x10
    2e4: 000225b7  lui          x11, 0x00022  # x11 = 0x00022000
    2e8: 08058593  addi         x11, x11, 128  # x11 = 0x00022080
    2ec: 00b4e663  bltu         x9, x11, 0x000002f8  # target 0x000002f8
    2f0: 00010637  lui          x12, 0x00010  # x12 = 0x00010000
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
    340: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    344: 8d028293  addi         x5, x5, -1840  # x5 = 0x000118d0
    348: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x000118d0
    34c: 78c00393  addi         x7, x0, 1932  # x7 = 0x0000078c
    350: 0003a283  lw           x5, 0(x7)  # param e2e_l0_k; 0x0000078c
    354: ff82f293  andi         x5, x5, -8
    358: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    35c: 8c448493  addi         x9, x9, -1852  # x9 = 0x000118c4
    360: 0004a383  lw           x7, 0(x9)  # param e2e_l0_k_row_start; 0x000118c4
    364: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
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
    3ac: 04000613  addi         x12, x0, 64  # x12 = 0x00000040
    3b0: 40b60633  sub          x12, x12, x11
    3b4: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    3b8: 00d67663  bgeu         x12, x13, 0x000003c4  # target 0x000003c4
    3bc: 0ff0000f  fence        0xf, 0xf
    3c0: fd5ff06f  jal          x0, 0x00000394  # target 0x00000394
loc_3c4:
    3c4: 0ff0000f  fence        0xf, 0xf
    3c8: 1d4000ef  jal          x1, 0x0000059c  # target 0x0000059c; x1 = 0x000003cc
    3cc: 1ec000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x000003d0
    3d0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3d4: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    3d8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    3dc: 00028f93  addi         x31, x5, 0
    3e0: 00030f13  addi         x30, x6, 0
    3e4: 00048e93  addi         x29, x9, 0
    3e8: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    3ec: 394000ef  jal          x1, 0x00000780  # target 0x00000780; x1 = 0x000003f0
    3f0: 000f8293  addi         x5, x31, 0
    3f4: 000f0313  addi         x6, x30, 0
    3f8: 1c0000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x000003fc
    3fc: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    400: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    404: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    408: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    40c: 00a484b3  add          x9, x9, x10
    410: 000225b7  lui          x11, 0x00022  # x11 = 0x00022000
    414: 08058593  addi         x11, x11, 128  # x11 = 0x00022080
    418: 00b4e663  bltu         x9, x11, 0x00000424  # target 0x00000424
    41c: 00010637  lui          x12, 0x00010  # x12 = 0x00010000
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
    46c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    470: 8d428293  addi         x5, x5, -1836  # x5 = 0x000118d4
    474: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x000118d4
    478: 79400393  addi         x7, x0, 1940  # x7 = 0x00000794
    47c: 0003a283  lw           x5, 0(x7)  # param e2e_l0_v; 0x00000794
    480: ff82f293  andi         x5, x5, -8
    484: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    488: 8c848493  addi         x9, x9, -1848  # x9 = 0x000118c8
    48c: 0004a383  lw           x7, 0(x9)  # param e2e_l0_v_row_start; 0x000118c8
    490: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    494: 028383b3  mul          x7, x7, x8
    498: 0073f313  andi         x6, x7, 7
    49c: 0033d393  srli         x7, x7, 3
    4a0: 00b39393  slli         x7, x7, 11
    4a4: 007282b3  add          x5, x5, x7
    4a8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    4ac: 00020413  addi         x8, x4, 0
loc_4b0:
    4b0: 0e83f463  bgeu         x7, x8, 0x00000598  # target 0x00000598
    4b4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    4b8: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    4bc: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_4c0:
    4c0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    4c4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    4c8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    4cc: 40a485b3  sub          x11, x9, x10
    4d0: 01059593  slli         x11, x11, 16
    4d4: 0105d593  srli         x11, x11, 16
    4d8: 04000613  addi         x12, x0, 64  # x12 = 0x00000040
    4dc: 40b60633  sub          x12, x12, x11
    4e0: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    4e4: 00d67663  bgeu         x12, x13, 0x000004f0  # target 0x000004f0
    4e8: 0ff0000f  fence        0xf, 0xf
    4ec: fd5ff06f  jal          x0, 0x000004c0  # target 0x000004c0
loc_4f0:
    4f0: 0ff0000f  fence        0xf, 0xf
    4f4: 0a8000ef  jal          x1, 0x0000059c  # target 0x0000059c; x1 = 0x000004f8
    4f8: 0c0000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x000004fc
    4fc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    500: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    504: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    508: 00028f93  addi         x31, x5, 0
    50c: 00030f13  addi         x30, x6, 0
    510: 00048e93  addi         x29, x9, 0
    514: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    518: 268000ef  jal          x1, 0x00000780  # target 0x00000780; x1 = 0x0000051c
    51c: 000f8293  addi         x5, x31, 0
    520: 000f0313  addi         x6, x30, 0
    524: 094000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x00000528
    528: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    52c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    530: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    534: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    538: 00a484b3  add          x9, x9, x10
    53c: 000225b7  lui          x11, 0x00022  # x11 = 0x00022000
    540: 08058593  addi         x11, x11, 128  # x11 = 0x00022080
    544: 00b4e663  bltu         x9, x11, 0x00000550  # target 0x00000550
    548: 00010637  lui          x12, 0x00010  # x12 = 0x00010000
    54c: 40c484b3  sub          x9, x9, x12
loc_550:
    550: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    554: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    558: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    55c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    560: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    564: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    568: 00448493  addi         x9, x9, 4
    56c: 01049493  slli         x9, x9, 16
    570: 0104d493  srli         x9, x9, 16
    574: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    578: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    57c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    580: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    584: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    588: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    58c: 0ff0000f  fence        0xf, 0xf
    590: 00138393  addi         x7, x7, 1
    594: f1dff06f  jal          x0, 0x000004b0  # target 0x000004b0
loc_598:
    598: 3100006f  jal          x0, 0x000008a8  # target 0x000008a8
loc_59c:
    59c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5a0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    5a4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    5a8: 000a0463  beq          x20, x0, 0x000005b0  # target 0x000005b0
    5ac: ff1ff06f  jal          x0, 0x0000059c  # target 0x0000059c
loc_5b0:
    5b0: 0ff0000f  fence        0xf, 0xf
    5b4: 00008067  jalr         x0, 0(x1)
loc_5b8:
    5b8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5bc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    5c0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    5c4: 000a0463  beq          x20, x0, 0x000005cc  # target 0x000005cc
    5c8: ff1ff06f  jal          x0, 0x000005b8  # target 0x000005b8
loc_5cc:
    5cc: 0ff0000f  fence        0xf, 0xf
    5d0: 00008067  jalr         x0, 0(x1)
loc_5d4:
    5d4: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    5d8: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x00000780
    5dc: 007a7d13  andi         x26, x20, 7
    5e0: ff8a7a13  andi         x20, x20, -8
    5e4: 01af8ab3  add          x21, x31, x26
    5e8: 007afb93  andi         x23, x21, 7
    5ec: 003ada93  srli         x21, x21, 3
    5f0: 00ba9a93  slli         x21, x21, 11
    5f4: 014a8ab3  add          x21, x21, x20
    5f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005f8
    5fc: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000628
    600: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    604: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    608: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    60c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    610: 03cd8db3  mul          x27, x27, x28
    614: 01bb0b33  add          x22, x22, x27
    618: 001b9b93  slli         x23, x23, 1
    61c: 017b0b33  add          x22, x22, x23
    620: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    624: 00008067  jalr         x0, 0(x1)
    628: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    62c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    630: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    634: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    638: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    63c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    640: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    644: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    648: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    64c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    650: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    654: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_658:
    658: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    65c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    660: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    664: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    668: 015a6463  bltu         x20, x21, 0x00000670  # target 0x00000670
    66c: fedff06f  jal          x0, 0x00000658  # target 0x00000658
loc_670:
    670: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    674: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    678: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    67c: 014a1a13  slli         x20, x20, 20
    680: 014a5a13  srli         x20, x20, 20
    684: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_688:
    688: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    68c: 000b0463  beq          x22, x0, 0x00000694  # target 0x00000694
    690: ff9ff06f  jal          x0, 0x00000688  # target 0x00000688
loc_694:
    694: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    698: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    69c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    6a0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    6a4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    6a8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    6ac: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    6b0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    6b4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    6b8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    6bc: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    6c0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    6c4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6c8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    6cc: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    6d0: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    6d4: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    6d8: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    6dc: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    6e0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    6e4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    6e8: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_6ec:
    6ec: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    6f0: 000b0463  beq          x22, x0, 0x000006f8  # target 0x000006f8
    6f4: ff9ff06f  jal          x0, 0x000006ec  # target 0x000006ec
loc_6f8:
    6f8: 00008067  jalr         x0, 0(x1)
loc_6fc:
    6fc: 7bc00a93  addi         x21, x0, 1980  # x21 = 0x000007bc
    700: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_input_norm; 0x000007bc
    704: 007a7d13  andi         x26, x20, 7
    708: ff8a7a13  andi         x20, x20, -8
    70c: 01af8ab3  add          x21, x31, x26
    710: 007afb93  andi         x23, x21, 7
    714: 003ada93  srli         x21, x21, 3
    718: 00ba9a93  slli         x21, x21, 11
    71c: 014a8ab3  add          x21, x21, x20
    720: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000720
    724: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000750
    728: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    72c: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    730: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    734: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    738: 03cd8db3  mul          x27, x27, x28
    73c: 01bb0b33  add          x22, x22, x27
    740: 001b9b93  slli         x23, x23, 1
    744: 017b0b33  add          x22, x22, x23
    748: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    74c: 00008067  jalr         x0, 0(x1)
    750: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    754: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    758: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    75c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    760: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    764: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    768: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    76c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    770: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    774: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    778: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    77c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_780:
    780: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000780
    784: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000878
    788: 00012cb7  lui          x25, 0x00012  # x25 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    78c: 8d8c8c93  addi         x25, x25, -1832  # x25 = 0x000118d8
    790: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x000118d8
    794: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    798: 038b8bb3  mul          x23, x23, x24
    79c: 017a0a33  add          x20, x20, x23
loc_7a0:
    7a0: 001f1a93  slli         x21, x30, 1
    7a4: 014a8ab3  add          x21, x21, x20
    7a8: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_7ac:
    7ac: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    7b0: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    7b4: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    7b8: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    7bc: 018be463  bltu         x23, x24, 0x000007c4  # target 0x000007c4
    7c0: fedff06f  jal          x0, 0x000007ac  # target 0x000007ac
loc_7c4:
    7c4: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    7c8: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    7cc: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    7d0: 014b9b93  slli         x23, x23, 20
    7d4: 014bdb93  srli         x23, x23, 20
    7d8: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_7dc:
    7dc: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    7e0: 000c8463  beq          x25, x0, 0x000007e8  # target 0x000007e8
    7e4: ff9ff06f  jal          x0, 0x000007dc  # target 0x000007dc
loc_7e8:
    7e8: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    7ec: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    7f0: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    7f4: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    7f8: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    7fc: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    800: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    804: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    808: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    80c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    810: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    814: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    818: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    81c: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    820: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    824: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    828: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    82c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    830: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    834: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    838: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    83c: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_840:
    840: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    844: 000c8463  beq          x25, x0, 0x0000084c  # target 0x0000084c
    848: ff9ff06f  jal          x0, 0x00000840  # target 0x00000840
loc_84c:
    84c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    850: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    854: 016e8eb3  add          x29, x29, x22
    858: 001f0f13  addi         x30, x30, 1
    85c: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    860: 015f1663  bne          x30, x21, 0x0000086c  # target 0x0000086c
    864: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    868: 016f8fb3  add          x31, x31, x22
loc_86c:
    86c: fffe0e13  addi         x28, x28, -1
    870: f20e18e3  bne          x28, x0, 0x000007a0  # target 0x000007a0
    874: 00008067  jalr         x0, 0(x1)
    878: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    87c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    880: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    884: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    888: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    88c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    890: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    894: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    898: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    89c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8a0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    8a4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    8a8:           j FW_BRISC+4   # return to firmware, linked at install
