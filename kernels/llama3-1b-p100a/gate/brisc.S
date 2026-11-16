# llama3 1b decode: gate, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_x_b_decode_token, 0x7c4=e2e_l0_gate, 0x7c8=e2e_l0_up, 0x7cc=e2e_hidden_dense, 0x7d0=e2e_l0_post_norm, 0x8100=e2e_gate, 0x8104=e2e_l0_gate_row_start, 0x8108=e2e_up, 0x810c=e2e_l0_up_row_start, 0x8110=dense_start, 0x8114=e2e_l0_gate_rows, 0x8118=e2e_l0_up_rows, 0x811c=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000952b7  lui          x5, 0x00095  # x5 = 0x00095000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00095000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     20: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     24: 00090537  lui          x10, 0x00090  # x10 = 0x00090000
     28: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00090000
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
     78: 354000ef  jal          x1, 0x000003cc  # target 0x000003cc; x1 = 0x0000007c
     7c: 36c000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 380000ef  jal          x1, 0x00000404  # target 0x00000404; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00095eb7  lui          x29, 0x00095  # x29 = 0x00095000
     9c: 3ec000ef  jal          x1, 0x00000488  # target 0x00000488; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 360000ef  jal          x1, 0x00000404  # target 0x00000404; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00095800
     c0: 3c8000ef  jal          x1, 0x00000488  # target 0x00000488; x1 = 0x000000c4
     c4: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     c8: 464000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     e0: 3a8000ef  jal          x1, 0x00000488  # target 0x00000488; x1 = 0x000000e4
     e4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     e8: 444000ef  jal          x1, 0x0000052c  # target 0x0000052c; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 00097eb7  lui          x29, 0x00097  # x29 = 0x00097000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00096800
    104: 384000ef  jal          x1, 0x00000488  # target 0x00000488; x1 = 0x00000108
    108: 2e0000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x0000010c
    10c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    110: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    114: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    118: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    11c: 00520233  add          x4, x4, x5
    120: 00097337  lui          x6, 0x00097  # x6 = 0x00097000
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
    170: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    174: 11428293  addi         x5, x5, 276  # x5 = 0x00008114
    178: 0002a203  lw           x4, 0(x5)  # param e2e_l0_gate_rows; 0x00008114
    17c: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
    180: 0003a283  lw           x5, 0(x7)  # param e2e_l0_gate; 0x000007c4
    184: ff82f293  andi         x5, x5, -8
    188: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    18c: 10448493  addi         x9, x9, 260  # x9 = 0x00008104
    190: 0004a383  lw           x7, 0(x9)  # param e2e_l0_gate_row_start; 0x00008104
    194: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    198: 028383b3  mul          x7, x7, x8
    19c: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
    1a0: 0283f333  remu         x6, x7, x8
    1a4: 0283d3b3  divu         x7, x7, x8
    1a8: 00b39393  slli         x7, x7, 11
    1ac: 007282b3  add          x5, x5, x7
    1b0: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1b4: 00020413  addi         x8, x4, 0
loc_1b8:
    1b8: 0e83f263  bgeu         x7, x8, 0x0000029c  # target 0x0000029c
    1bc: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1c0: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    1c4: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1c8:
    1c8: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1cc: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1d0: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1d4: 40a485b3  sub          x11, x9, x10
    1d8: 01059593  slli         x11, x11, 16
    1dc: 0105d593  srli         x11, x11, 16
    1e0: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    1e4: 40b60633  sub          x12, x12, x11
    1e8: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    1ec: 00d67663  bgeu         x12, x13, 0x000001f8  # target 0x000001f8
    1f0: 0ff0000f  fence        0xf, 0xf
    1f4: fd5ff06f  jal          x0, 0x000001c8  # target 0x000001c8
loc_1f8:
    1f8: 0ff0000f  fence        0xf, 0xf
    1fc: 1d0000ef  jal          x1, 0x000003cc  # target 0x000003cc; x1 = 0x00000200
    200: 1e8000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x00000204
    204: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    208: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    20c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    210: 00028f93  addi         x31, x5, 0
    214: 00030f13  addi         x30, x6, 0
    218: 00048e93  addi         x29, x9, 0
    21c: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    220: 390000ef  jal          x1, 0x000005b0  # target 0x000005b0; x1 = 0x00000224
    224: 000f8293  addi         x5, x31, 0
    228: 000f0313  addi         x6, x30, 0
    22c: 1bc000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x00000230
    230: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    234: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    238: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    23c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    240: 00a484b3  add          x9, x9, x10
    244: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    248: 00b4e663  bltu         x9, x11, 0x00000254  # target 0x00000254
    24c: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    250: 40c484b3  sub          x9, x9, x12
loc_254:
    254: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    258: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    25c: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    260: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    264: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    268: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    26c: 00248493  addi         x9, x9, 2
    270: 01049493  slli         x9, x9, 16
    274: 0104d493  srli         x9, x9, 16
    278: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    27c: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    280: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    284: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    288: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    28c: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    290: 0ff0000f  fence        0xf, 0xf
    294: 00138393  addi         x7, x7, 1
    298: f21ff06f  jal          x0, 0x000001b8  # target 0x000001b8
loc_29c:
    29c: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    2a0: 11828293  addi         x5, x5, 280  # x5 = 0x00008118
    2a4: 0002a203  lw           x4, 0(x5)  # param e2e_l0_up_rows; 0x00008118
    2a8: 7c800393  addi         x7, x0, 1992  # x7 = 0x000007c8
    2ac: 0003a283  lw           x5, 0(x7)  # param e2e_l0_up; 0x000007c8
    2b0: ff82f293  andi         x5, x5, -8
    2b4: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    2b8: 10c48493  addi         x9, x9, 268  # x9 = 0x0000810c
    2bc: 0004a383  lw           x7, 0(x9)  # param e2e_l0_up_row_start; 0x0000810c
    2c0: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    2c4: 028383b3  mul          x7, x7, x8
    2c8: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
    2cc: 0283f333  remu         x6, x7, x8
    2d0: 0283d3b3  divu         x7, x7, x8
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
    328: 0a4000ef  jal          x1, 0x000003cc  # target 0x000003cc; x1 = 0x0000032c
    32c: 0bc000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x00000330
    330: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    334: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    338: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    33c: 00028f93  addi         x31, x5, 0
    340: 00030f13  addi         x30, x6, 0
    344: 00048e93  addi         x29, x9, 0
    348: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    34c: 264000ef  jal          x1, 0x000005b0  # target 0x000005b0; x1 = 0x00000350
    350: 000f8293  addi         x5, x31, 0
    354: 000f0313  addi         x6, x30, 0
    358: 090000ef  jal          x1, 0x000003e8  # target 0x000003e8; x1 = 0x0000035c
    35c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    360: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    364: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    368: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    36c: 00a484b3  add          x9, x9, x10
    370: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
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
    3c8: 30c0006f  jal          x0, 0x000006d4  # target 0x000006d4
loc_3cc:
    3cc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3d0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    3d4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    3d8: 000a0463  beq          x20, x0, 0x000003e0  # target 0x000003e0
    3dc: ff1ff06f  jal          x0, 0x000003cc  # target 0x000003cc
loc_3e0:
    3e0: 0ff0000f  fence        0xf, 0xf
    3e4: 00008067  jalr         x0, 0(x1)
loc_3e8:
    3e8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3ec: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3f0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3f4: 000a0463  beq          x20, x0, 0x000003fc  # target 0x000003fc
    3f8: ff1ff06f  jal          x0, 0x000003e8  # target 0x000003e8
loc_3fc:
    3fc: 0ff0000f  fence        0xf, 0xf
    400: 00008067  jalr         x0, 0(x1)
loc_404:
    404: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    408: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b_decode_token; 0x000007c0
    40c: 007a7d13  andi         x26, x20, 7
    410: ff8a7a13  andi         x20, x20, -8
    414: 01af8ab3  add          x21, x31, x26
    418: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    41c: 038afbb3  remu         x23, x21, x24
    420: 038adab3  divu         x21, x21, x24
    424: 00ba9a93  slli         x21, x21, 11
    428: 014a8ab3  add          x21, x21, x20
    42c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000042c
    430: 030b0b13  addi         x22, x22, 48  # x22 = 0x0000045c
    434: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    438: 11ce8e93  addi         x29, x29, 284  # x29 = 0x0000811c
    43c: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000811c
    440: 00e00e13  addi         x28, x0, 14  # x28 = 0x0000000e
    444: 03cd8db3  mul          x27, x27, x28
    448: 01bb0b33  add          x22, x22, x27
    44c: 001b9b93  slli         x23, x23, 1
    450: 017b0b33  add          x22, x22, x23
    454: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    458: 00008067  jalr         x0, 0(x1)
    45c: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    460: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    464: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    468: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    46c: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    470: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    474: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    478: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    47c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    480: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    484: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_488:
    488: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    48c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    490: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    494: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    498: 015a6463  bltu         x20, x21, 0x000004a0  # target 0x000004a0
    49c: fedff06f  jal          x0, 0x00000488  # target 0x00000488
loc_4a0:
    4a0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4a4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    4a8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    4ac: 014a1a13  slli         x20, x20, 20
    4b0: 014a5a13  srli         x20, x20, 20
    4b4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_4b8:
    4b8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    4bc: 000b0463  beq          x22, x0, 0x000004c4  # target 0x000004c4
    4c0: ff9ff06f  jal          x0, 0x000004b8  # target 0x000004b8
loc_4c4:
    4c4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    4c8: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    4cc: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    4d0: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    4d4: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    4d8: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    4dc: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    4e0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    4e4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    4e8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    4ec: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    4f0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    4f4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4f8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    4fc: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    500: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    504: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    508: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    50c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    510: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    514: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    518: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_51c:
    51c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    520: 000b0463  beq          x22, x0, 0x00000528  # target 0x00000528
    524: ff9ff06f  jal          x0, 0x0000051c  # target 0x0000051c
loc_528:
    528: 00008067  jalr         x0, 0(x1)
loc_52c:
    52c: 7d000a93  addi         x21, x0, 2000  # x21 = 0x000007d0
    530: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_post_norm; 0x000007d0
    534: 007a7d13  andi         x26, x20, 7
    538: ff8a7a13  andi         x20, x20, -8
    53c: 01af8ab3  add          x21, x31, x26
    540: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    544: 038afbb3  remu         x23, x21, x24
    548: 038adab3  divu         x21, x21, x24
    54c: 00ba9a93  slli         x21, x21, 11
    550: 014a8ab3  add          x21, x21, x20
    554: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000554
    558: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000584
    55c: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    560: 11ce8e93  addi         x29, x29, 284  # x29 = 0x0000811c
    564: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000811c
    568: 00e00e13  addi         x28, x0, 14  # x28 = 0x0000000e
    56c: 03cd8db3  mul          x27, x27, x28
    570: 01bb0b33  add          x22, x22, x27
    574: 001b9b93  slli         x23, x23, 1
    578: 017b0b33  add          x22, x22, x23
    57c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    580: 00008067  jalr         x0, 0(x1)
    584: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    588: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    58c: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    590: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    594: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    598: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    59c: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    5a0: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    5a4: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5a8: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5ac: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_5b0:
    5b0: 00000a17  auipc        x20, 0x00000  # x20 = 0x000005b0
    5b4: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000006a8
    5b8: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    5bc: 11cc8c93  addi         x25, x25, 284  # x25 = 0x0000811c
    5c0: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x0000811c
    5c4: 00e00c13  addi         x24, x0, 14  # x24 = 0x0000000e
    5c8: 038b8bb3  mul          x23, x23, x24
    5cc: 017a0a33  add          x20, x20, x23
loc_5d0:
    5d0: 001f1a93  slli         x21, x30, 1
    5d4: 014a8ab3  add          x21, x21, x20
    5d8: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_5dc:
    5dc: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    5e0: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    5e4: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    5e8: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    5ec: 018be463  bltu         x23, x24, 0x000005f4  # target 0x000005f4
    5f0: fedff06f  jal          x0, 0x000005dc  # target 0x000005dc
loc_5f4:
    5f4: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    5f8: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    5fc: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    600: 014b9b93  slli         x23, x23, 20
    604: 014bdb93  srli         x23, x23, 20
    608: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_60c:
    60c: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    610: 000c8463  beq          x25, x0, 0x00000618  # target 0x00000618
    614: ff9ff06f  jal          x0, 0x0000060c  # target 0x0000060c
loc_618:
    618: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    61c: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    620: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    624: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    628: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    62c: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    630: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    634: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    638: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    63c: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    640: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    644: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    648: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    64c: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    650: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    654: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    658: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    65c: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    660: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    664: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    668: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    66c: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_670:
    670: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    674: 000c8463  beq          x25, x0, 0x0000067c  # target 0x0000067c
    678: ff9ff06f  jal          x0, 0x00000670  # target 0x00000670
loc_67c:
    67c: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    680: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    684: 016e8eb3  add          x29, x29, x22
    688: 001f0f13  addi         x30, x30, 1
    68c: 00700a93  addi         x21, x0, 7  # x21 = 0x00000007
    690: 015f1663  bne          x30, x21, 0x0000069c  # target 0x0000069c
    694: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    698: 016f8fb3  add          x31, x31, x22
loc_69c:
    69c: fffe0e13  addi         x28, x28, -1
    6a0: f20e18e3  bne          x28, x0, 0x000005d0  # target 0x000005d0
    6a4: 00008067  jalr         x0, 0(x1)
    6a8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6ac: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6b0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6b4: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6b8: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6bc: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    6c0: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    6c4: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6c8: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6cc: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6d0: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    6d4:           j FW_BRISC+4   # return to firmware, linked at install
