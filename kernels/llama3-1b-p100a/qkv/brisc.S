# llama3 1b decode: qkv, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_l0_q, 0x7c8=e2e_l0_k, 0x7cc=e2e_l0_v, 0x7d0=e2e_l0_input_norm, 0x8080=e2e_q_compact, 0x8084=e2e_l0_q_row_start, 0x8088=e2e_k_compact, 0x808c=e2e_l0_k_row_start, 0x8090=e2e_v_compact, 0x8094=e2e_l0_v_row_start, 0x8098=e2e_l0_q_rows, 0x809c=e2e_l0_k_rows, 0x80a0=e2e_l0_v_rows, 0x80a4=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000962b7  lui          x5, 0x00096  # x5 = 0x00096000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x00095800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00095800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     24: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00090537  lui          x10, 0x00090  # x10 = 0x00090000
     2c: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00090000
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
     7c: 484000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000080
     80: 49c000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000084
     84: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     88: 4b0000ef  jal          x1, 0x00000538  # target 0x00000538; x1 = 0x0000008c
     8c: 000a8213  addi         x4, x21, 0
     90: 000b0293  addi         x5, x22, 0
     94: 00020f93  addi         x31, x4, 0
     98: 00028f13  addi         x30, x5, 0
     9c: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     a0: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00095800
     a4: 518000ef  jal          x1, 0x000005bc  # target 0x000005bc; x1 = 0x000000a8
     a8: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     ac: 48c000ef  jal          x1, 0x00000538  # target 0x00000538; x1 = 0x000000b0
     b0: 000a8213  addi         x4, x21, 0
     b4: 000b0293  addi         x5, x22, 0
     b8: 00020f93  addi         x31, x4, 0
     bc: 00028f13  addi         x30, x5, 0
     c0: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     c4: 4f8000ef  jal          x1, 0x000005bc  # target 0x000005bc; x1 = 0x000000c8
     c8: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     cc: 594000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x000000d0
     d0: 000a8213  addi         x4, x21, 0
     d4: 000b0293  addi         x5, x22, 0
     d8: 00020f93  addi         x31, x4, 0
     dc: 00028f13  addi         x30, x5, 0
     e0: 00097eb7  lui          x29, 0x00097  # x29 = 0x00097000
     e4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00096800
     e8: 4d4000ef  jal          x1, 0x000005bc  # target 0x000005bc; x1 = 0x000000ec
     ec: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     f0: 570000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x000000f4
     f4: 000a8213  addi         x4, x21, 0
     f8: 000b0293  addi         x5, x22, 0
     fc: 00020f93  addi         x31, x4, 0
    100: 00028f13  addi         x30, x5, 0
    104: 00097eb7  lui          x29, 0x00097  # x29 = 0x00097000
    108: 4b4000ef  jal          x1, 0x000005bc  # target 0x000005bc; x1 = 0x0000010c
    10c: 410000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000110
    110: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    114: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    118: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    11c: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    120: 00520233  add          x4, x4, x5
    124: 00098337  lui          x6, 0x00098  # x6 = 0x00098000
    128: 80030313  addi         x6, x6, -2048  # x6 = 0x00097800
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
    178: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    17c: 09828293  addi         x5, x5, 152  # x5 = 0x00008098
    180: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x00008098
    184: 7c400393  addi         x7, x0, 1988  # x7 = 0x000007c4
    188: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x000007c4
    18c: ff82f293  andi         x5, x5, -8
    190: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    194: 08448493  addi         x9, x9, 132  # x9 = 0x00008084
    198: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x00008084
    19c: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    1a0: 028383b3  mul          x7, x7, x8
    1a4: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
    1a8: 0283f333  remu         x6, x7, x8
    1ac: 0283d3b3  divu         x7, x7, x8
    1b0: 00b39393  slli         x7, x7, 11
    1b4: 007282b3  add          x5, x5, x7
    1b8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1bc: 00020413  addi         x8, x4, 0
loc_1c0:
    1c0: 0e83f263  bgeu         x7, x8, 0x000002a4  # target 0x000002a4
    1c4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    1c8: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    1cc: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1d0:
    1d0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    1d4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    1d8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    1dc: 40a485b3  sub          x11, x9, x10
    1e0: 01059593  slli         x11, x11, 16
    1e4: 0105d593  srli         x11, x11, 16
    1e8: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    1ec: 40b60633  sub          x12, x12, x11
    1f0: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    1f4: 00d67663  bgeu         x12, x13, 0x00000200  # target 0x00000200
    1f8: 0ff0000f  fence        0xf, 0xf
    1fc: fd5ff06f  jal          x0, 0x000001d0  # target 0x000001d0
loc_200:
    200: 0ff0000f  fence        0xf, 0xf
    204: 2fc000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000208
    208: 314000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x0000020c
    20c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    210: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    214: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    218: 00028f93  addi         x31, x5, 0
    21c: 00030f13  addi         x30, x6, 0
    220: 00048e93  addi         x29, x9, 0
    224: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    228: 4bc000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x0000022c
    22c: 000f8293  addi         x5, x31, 0
    230: 000f0313  addi         x6, x30, 0
    234: 2e8000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000238
    238: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    23c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    240: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    244: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    248: 00a484b3  add          x9, x9, x10
    24c: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    250: 00b4e663  bltu         x9, x11, 0x0000025c  # target 0x0000025c
    254: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    258: 40c484b3  sub          x9, x9, x12
loc_25c:
    25c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    260: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    264: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    268: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    26c: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    270: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    274: 00248493  addi         x9, x9, 2
    278: 01049493  slli         x9, x9, 16
    27c: 0104d493  srli         x9, x9, 16
    280: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    284: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    288: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    28c: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    290: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    294: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    298: 0ff0000f  fence        0xf, 0xf
    29c: 00138393  addi         x7, x7, 1
    2a0: f21ff06f  jal          x0, 0x000001c0  # target 0x000001c0
loc_2a4:
    2a4: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    2a8: 09c28293  addi         x5, x5, 156  # x5 = 0x0000809c
    2ac: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x0000809c
    2b0: 7c800393  addi         x7, x0, 1992  # x7 = 0x000007c8
    2b4: 0003a283  lw           x5, 0(x7)  # param e2e_l0_k; 0x000007c8
    2b8: ff82f293  andi         x5, x5, -8
    2bc: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    2c0: 08c48493  addi         x9, x9, 140  # x9 = 0x0000808c
    2c4: 0004a383  lw           x7, 0(x9)  # param e2e_l0_k_row_start; 0x0000808c
    2c8: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    2cc: 028383b3  mul          x7, x7, x8
    2d0: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
    2d4: 0283f333  remu         x6, x7, x8
    2d8: 0283d3b3  divu         x7, x7, x8
    2dc: 00b39393  slli         x7, x7, 11
    2e0: 007282b3  add          x5, x5, x7
    2e4: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    2e8: 00020413  addi         x8, x4, 0
loc_2ec:
    2ec: 0e83f263  bgeu         x7, x8, 0x000003d0  # target 0x000003d0
    2f0: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    2f4: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    2f8: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_2fc:
    2fc: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    300: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    304: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    308: 40a485b3  sub          x11, x9, x10
    30c: 01059593  slli         x11, x11, 16
    310: 0105d593  srli         x11, x11, 16
    314: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    318: 40b60633  sub          x12, x12, x11
    31c: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    320: 00d67663  bgeu         x12, x13, 0x0000032c  # target 0x0000032c
    324: 0ff0000f  fence        0xf, 0xf
    328: fd5ff06f  jal          x0, 0x000002fc  # target 0x000002fc
loc_32c:
    32c: 0ff0000f  fence        0xf, 0xf
    330: 1d0000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000334
    334: 1e8000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000338
    338: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    33c: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    340: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    344: 00028f93  addi         x31, x5, 0
    348: 00030f13  addi         x30, x6, 0
    34c: 00048e93  addi         x29, x9, 0
    350: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    354: 390000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x00000358
    358: 000f8293  addi         x5, x31, 0
    35c: 000f0313  addi         x6, x30, 0
    360: 1bc000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000364
    364: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    368: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    36c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    370: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    374: 00a484b3  add          x9, x9, x10
    378: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    37c: 00b4e663  bltu         x9, x11, 0x00000388  # target 0x00000388
    380: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    384: 40c484b3  sub          x9, x9, x12
loc_388:
    388: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    38c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    390: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    394: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    398: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    39c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    3a0: 00248493  addi         x9, x9, 2
    3a4: 01049493  slli         x9, x9, 16
    3a8: 0104d493  srli         x9, x9, 16
    3ac: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3b0: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    3b4: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    3b8: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    3bc: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    3c0: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    3c4: 0ff0000f  fence        0xf, 0xf
    3c8: 00138393  addi         x7, x7, 1
    3cc: f21ff06f  jal          x0, 0x000002ec  # target 0x000002ec
loc_3d0:
    3d0: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    3d4: 0a028293  addi         x5, x5, 160  # x5 = 0x000080a0
    3d8: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x000080a0
    3dc: 7cc00393  addi         x7, x0, 1996  # x7 = 0x000007cc
    3e0: 0003a283  lw           x5, 0(x7)  # param e2e_l0_v; 0x000007cc
    3e4: ff82f293  andi         x5, x5, -8
    3e8: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    3ec: 09448493  addi         x9, x9, 148  # x9 = 0x00008094
    3f0: 0004a383  lw           x7, 0(x9)  # param e2e_l0_v_row_start; 0x00008094
    3f4: 00200413  addi         x8, x0, 2  # x8 = 0x00000002
    3f8: 028383b3  mul          x7, x7, x8
    3fc: 00700413  addi         x8, x0, 7  # x8 = 0x00000007
    400: 0283f333  remu         x6, x7, x8
    404: 0283d3b3  divu         x7, x7, x8
    408: 00b39393  slli         x7, x7, 11
    40c: 007282b3  add          x5, x5, x7
    410: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    414: 00020413  addi         x8, x4, 0
loc_418:
    418: 0e83f263  bgeu         x7, x8, 0x000004fc  # target 0x000004fc
    41c: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    420: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    424: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_428:
    428: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    42c: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    430: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    434: 40a485b3  sub          x11, x9, x10
    438: 01059593  slli         x11, x11, 16
    43c: 0105d593  srli         x11, x11, 16
    440: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    444: 40b60633  sub          x12, x12, x11
    448: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    44c: 00d67663  bgeu         x12, x13, 0x00000458  # target 0x00000458
    450: 0ff0000f  fence        0xf, 0xf
    454: fd5ff06f  jal          x0, 0x00000428  # target 0x00000428
loc_458:
    458: 0ff0000f  fence        0xf, 0xf
    45c: 0a4000ef  jal          x1, 0x00000500  # target 0x00000500; x1 = 0x00000460
    460: 0bc000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000464
    464: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    468: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    46c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    470: 00028f93  addi         x31, x5, 0
    474: 00030f13  addi         x30, x6, 0
    478: 00048e93  addi         x29, x9, 0
    47c: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    480: 264000ef  jal          x1, 0x000006e4  # target 0x000006e4; x1 = 0x00000484
    484: 000f8293  addi         x5, x31, 0
    488: 000f0313  addi         x6, x30, 0
    48c: 090000ef  jal          x1, 0x0000051c  # target 0x0000051c; x1 = 0x00000490
    490: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    494: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    498: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    49c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4a0: 00a484b3  add          x9, x9, x10
    4a4: 000925b7  lui          x11, 0x00092  # x11 = 0x00092000
    4a8: 00b4e663  bltu         x9, x11, 0x000004b4  # target 0x000004b4
    4ac: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    4b0: 40c484b3  sub          x9, x9, x12
loc_4b4:
    4b4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    4b8: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    4bc: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    4c0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4c4: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    4c8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    4cc: 00248493  addi         x9, x9, 2
    4d0: 01049493  slli         x9, x9, 16
    4d4: 0104d493  srli         x9, x9, 16
    4d8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4dc: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    4e0: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    4e4: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    4e8: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    4ec: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    4f0: 0ff0000f  fence        0xf, 0xf
    4f4: 00138393  addi         x7, x7, 1
    4f8: f21ff06f  jal          x0, 0x00000418  # target 0x00000418
loc_4fc:
    4fc: 30c0006f  jal          x0, 0x00000808  # target 0x00000808
loc_500:
    500: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    504: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    508: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    50c: 000a0463  beq          x20, x0, 0x00000514  # target 0x00000514
    510: ff1ff06f  jal          x0, 0x00000500  # target 0x00000500
loc_514:
    514: 0ff0000f  fence        0xf, 0xf
    518: 00008067  jalr         x0, 0(x1)
loc_51c:
    51c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    520: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    524: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    528: 000a0463  beq          x20, x0, 0x00000530  # target 0x00000530
    52c: ff1ff06f  jal          x0, 0x0000051c  # target 0x0000051c
loc_530:
    530: 0ff0000f  fence        0xf, 0xf
    534: 00008067  jalr         x0, 0(x1)
loc_538:
    538: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    53c: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x000007c0
    540: 007a7d13  andi         x26, x20, 7
    544: ff8a7a13  andi         x20, x20, -8
    548: 01af8ab3  add          x21, x31, x26
    54c: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    550: 038afbb3  remu         x23, x21, x24
    554: 038adab3  divu         x21, x21, x24
    558: 00ba9a93  slli         x21, x21, 11
    55c: 014a8ab3  add          x21, x21, x20
    560: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000560
    564: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000590
    568: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    56c: 0a4e8e93  addi         x29, x29, 164  # x29 = 0x000080a4
    570: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000080a4
    574: 00e00e13  addi         x28, x0, 14  # x28 = 0x0000000e
    578: 03cd8db3  mul          x27, x27, x28
    57c: 01bb0b33  add          x22, x22, x27
    580: 001b9b93  slli         x23, x23, 1
    584: 017b0b33  add          x22, x22, x23
    588: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    58c: 00008067  jalr         x0, 0(x1)
    590: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    594: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    598: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    59c: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    5a0: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5a4: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    5a8: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    5ac: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    5b0: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5b4: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5b8: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_5bc:
    5bc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5c0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    5c4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    5c8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    5cc: 015a6463  bltu         x20, x21, 0x000005d4  # target 0x000005d4
    5d0: fedff06f  jal          x0, 0x000005bc  # target 0x000005bc
loc_5d4:
    5d4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    5d8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    5dc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    5e0: 014a1a13  slli         x20, x20, 20
    5e4: 014a5a13  srli         x20, x20, 20
    5e8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_5ec:
    5ec: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5f0: 000b0463  beq          x22, x0, 0x000005f8  # target 0x000005f8
    5f4: ff9ff06f  jal          x0, 0x000005ec  # target 0x000005ec
loc_5f8:
    5f8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5fc: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    600: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    604: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    608: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    60c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    610: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    614: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    618: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    61c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    620: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    624: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    628: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    62c: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    630: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    634: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    638: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    63c: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    640: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    644: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    648: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    64c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_650:
    650: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    654: 000b0463  beq          x22, x0, 0x0000065c  # target 0x0000065c
    658: ff9ff06f  jal          x0, 0x00000650  # target 0x00000650
loc_65c:
    65c: 00008067  jalr         x0, 0(x1)
loc_660:
    660: 7d000a93  addi         x21, x0, 2000  # x21 = 0x000007d0
    664: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_input_norm; 0x000007d0
    668: 007a7d13  andi         x26, x20, 7
    66c: ff8a7a13  andi         x20, x20, -8
    670: 01af8ab3  add          x21, x31, x26
    674: 00700c13  addi         x24, x0, 7  # x24 = 0x00000007
    678: 038afbb3  remu         x23, x21, x24
    67c: 038adab3  divu         x21, x21, x24
    680: 00ba9a93  slli         x21, x21, 11
    684: 014a8ab3  add          x21, x21, x20
    688: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000688
    68c: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006b8
    690: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    694: 0a4e8e93  addi         x29, x29, 164  # x29 = 0x000080a4
    698: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000080a4
    69c: 00e00e13  addi         x28, x0, 14  # x28 = 0x0000000e
    6a0: 03cd8db3  mul          x27, x27, x28
    6a4: 01bb0b33  add          x22, x22, x27
    6a8: 001b9b93  slli         x23, x23, 1
    6ac: 017b0b33  add          x22, x22, x23
    6b0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6b4: 00008067  jalr         x0, 0(x1)
    6b8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6bc: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6c4: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6c8: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6cc: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    6d0: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    6d4: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6d8: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6dc: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6e0: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_6e4:
    6e4: 00000a17  auipc        x20, 0x00000  # x20 = 0x000006e4
    6e8: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x000007dc
    6ec: 00008cb7  lui          x25, 0x00008  # x25 = 0x00008000
    6f0: 0a4c8c93  addi         x25, x25, 164  # x25 = 0x000080a4
    6f4: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x000080a4
    6f8: 00e00c13  addi         x24, x0, 14  # x24 = 0x0000000e
    6fc: 038b8bb3  mul          x23, x23, x24
    700: 017a0a33  add          x20, x20, x23
loc_704:
    704: 001f1a93  slli         x21, x30, 1
    708: 014a8ab3  add          x21, x21, x20
    70c: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_710:
    710: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    714: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    718: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    71c: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    720: 018be463  bltu         x23, x24, 0x00000728  # target 0x00000728
    724: fedff06f  jal          x0, 0x00000710  # target 0x00000710
loc_728:
    728: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    72c: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    730: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    734: 014b9b93  slli         x23, x23, 20
    738: 014bdb93  srli         x23, x23, 20
    73c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_740:
    740: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    744: 000c8463  beq          x25, x0, 0x0000074c  # target 0x0000074c
    748: ff9ff06f  jal          x0, 0x00000740  # target 0x00000740
loc_74c:
    74c: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    750: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    754: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    758: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    75c: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    760: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    764: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    768: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    76c: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    770: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    774: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    778: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    77c: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    780: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    784: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    788: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    78c: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    790: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    794: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    798: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    79c: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    7a0: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_7a4:
    7a4: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    7a8: 000c8463  beq          x25, x0, 0x000007b0  # target 0x000007b0
    7ac: ff9ff06f  jal          x0, 0x000007a4  # target 0x000007a4
loc_7b0:
    7b0: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7b4: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    7b8: 016e8eb3  add          x29, x29, x22
    7bc: 001f0f13  addi         x30, x30, 1
    7c0: 00700a93  addi         x21, x0, 7  # x21 = 0x00000007
    7c4: 015f1663  bne          x30, x21, 0x000007d0  # target 0x000007d0
    7c8: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    7cc: 016f8fb3  add          x31, x31, x22
loc_7d0:
    7d0: fffe0e13  addi         x28, x28, -1
    7d4: f20e18e3  bne          x28, x0, 0x00000704  # target 0x00000704
    7d8: 00008067  jalr         x0, 0(x1)
    7dc: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7e0: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7e4: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7e8: 03510512  SFPNOT       imm12_math=3396, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    7ec: 04910451  PACR         CfgContext=1, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=1, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7f0: 03120591  XMOV         Mov_block_selection=1, Last=4489572  # Unreachable by statically known control flow
    7f4: 04d20452  SFPLZ        imm12_math=840, lreg_c=1, lreg_dest=1, instr_mod1=4  # lreg_c: L1; lreg_dest: L1; Unreachable by statically known control flow
    7f8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    7fc: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    800: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    804: 00000492  SFPNOT       imm12_math=0, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    808:           j FW_BRISC+4   # return to firmware, linked at install
