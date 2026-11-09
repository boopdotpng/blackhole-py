# llama3 1B decode: qkv, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (8): 2,2 5,2 10,2 13,2 3,3 6,3 11,3 1,4
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_l0_q, 0x7c8=e2e_l0_k, 0x7cc=e2e_l0_v, 0x7d0=e2e_l0_input_norm, 0x8080=e2e_q_compact, 0x8084=e2e_l0_q_row_start, 0x8088=e2e_k_compact, 0x808c=e2e_l0_k_row_start, 0x8090=e2e_v_compact, 0x8094=e2e_l0_v_row_start
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000962b7  lui          x5, 0x00096  # x5 = 0x00096000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x00095800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00095800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     24: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
     28: 000904b7  lui          x9, 0x00090  # x9 = 0x00090000
     2c: 00942023  sw           x9, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00090000
     30: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     34: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
     38: 00042023  sw           x0, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
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
     7c: 454000ef  jal          x1, 0x000004d0  # target 0x000004d0; x1 = 0x00000080
     80: 46c000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000084
     84: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     88: 480000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x0000008c
     8c: 000a8213  addi         x4, x21, 0
     90: 000b0293  addi         x5, x22, 0
     94: 00020f93  addi         x31, x4, 0
     98: 00028f13  addi         x30, x5, 0
     9c: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     a0: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00095800
     a4: 4b0000ef  jal          x1, 0x00000554  # target 0x00000554; x1 = 0x000000a8
     a8: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     ac: 45c000ef  jal          x1, 0x00000508  # target 0x00000508; x1 = 0x000000b0
     b0: 000a8213  addi         x4, x21, 0
     b4: 000b0293  addi         x5, x22, 0
     b8: 00020f93  addi         x31, x4, 0
     bc: 00028f13  addi         x30, x5, 0
     c0: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     c4: 490000ef  jal          x1, 0x00000554  # target 0x00000554; x1 = 0x000000c8
     c8: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     cc: 52c000ef  jal          x1, 0x000005f8  # target 0x000005f8; x1 = 0x000000d0
     d0: 000a8213  addi         x4, x21, 0
     d4: 000b0293  addi         x5, x22, 0
     d8: 00020f93  addi         x31, x4, 0
     dc: 00028f13  addi         x30, x5, 0
     e0: 00097eb7  lui          x29, 0x00097  # x29 = 0x00097000
     e4: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00096800
     e8: 46c000ef  jal          x1, 0x00000554  # target 0x00000554; x1 = 0x000000ec
     ec: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     f0: 508000ef  jal          x1, 0x000005f8  # target 0x000005f8; x1 = 0x000000f4
     f4: 000a8213  addi         x4, x21, 0
     f8: 000b0293  addi         x5, x22, 0
     fc: 00020f93  addi         x31, x4, 0
    100: 00028f13  addi         x30, x5, 0
    104: 00097eb7  lui          x29, 0x00097  # x29 = 0x00097000
    108: 44c000ef  jal          x1, 0x00000554  # target 0x00000554; x1 = 0x0000010c
    10c: 3e0000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000110
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
    178: 7c400313  addi         x6, x0, 1988  # x6 = 0x000007c4
    17c: 00032203  lw           x4, 0(x6)  # param e2e_l0_q; 0x000007c4
    180: ff827213  andi         x4, x4, -8
    184: 00008437  lui          x8, 0x00008  # x8 = 0x00008000
    188: 08440413  addi         x8, x8, 132  # x8 = 0x00008084
    18c: 00042303  lw           x6, 0(x8)  # param e2e_l0_q_row_start; 0x00008084
    190: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
    194: 02730333  mul          x6, x6, x7
    198: 00737293  andi         x5, x6, 7
    19c: 00335313  srli         x6, x6, 3
    1a0: 00b31313  slli         x6, x6, 11
    1a4: 00620233  add          x4, x4, x6
    1a8: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    1ac: 01800393  addi         x7, x0, 24  # x7 = 0x00000018
loc_1b0:
    1b0: 0e737263  bgeu         x6, x7, 0x00000294  # target 0x00000294
    1b4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1b8: 88468693  addi         x13, x13, -1916  # x13 = 0xffb00884 · riscv_local_mem + 0x884
    1bc: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1c0:
    1c0: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
    1c4: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    1c8: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    1cc: 40940533  sub          x10, x8, x9
    1d0: 01051513  slli         x10, x10, 16
    1d4: 01055513  srli         x10, x10, 16
    1d8: 00400593  addi         x11, x0, 4  # x11 = 0x00000004
    1dc: 40a585b3  sub          x11, x11, x10
    1e0: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    1e4: 00c5f663  bgeu         x11, x12, 0x000001f0  # target 0x000001f0
    1e8: 0ff0000f  fence        0xf, 0xf
    1ec: fd5ff06f  jal          x0, 0x000001c0  # target 0x000001c0
loc_1f0:
    1f0: 0ff0000f  fence        0xf, 0xf
    1f4: 2dc000ef  jal          x1, 0x000004d0  # target 0x000004d0; x1 = 0x000001f8
    1f8: 2f4000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000001fc
    1fc: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    200: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
    204: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880
    208: 00020f93  addi         x31, x4, 0
    20c: 00028f13  addi         x30, x5, 0
    210: 00040e93  addi         x29, x8, 0
    214: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    218: 42c000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x0000021c
    21c: 000f8213  addi         x4, x31, 0
    220: 000f0293  addi         x5, x30, 0
    224: 2c8000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000228
    228: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    22c: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    230: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880
    234: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    238: 00940433  add          x8, x8, x9
    23c: 00092537  lui          x10, 0x00092  # x10 = 0x00092000
    240: 00a46663  bltu         x8, x10, 0x0000024c  # target 0x0000024c
    244: 000025b7  lui          x11, 0x00002  # x11 = 0x00002000
    248: 40b40433  sub          x8, x8, x11
loc_24c:
    24c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    250: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    254: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    258: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    25c: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
    260: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884
    264: 00240413  addi         x8, x8, 2
    268: 01041413  slli         x8, x8, 16
    26c: 01045413  srli         x8, x8, 16
    270: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    274: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
    278: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    27c: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    280: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    284: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    288: 0ff0000f  fence        0xf, 0xf
    28c: 00130313  addi         x6, x6, 1
    290: f21ff06f  jal          x0, 0x000001b0  # target 0x000001b0
loc_294:
    294: 7c800313  addi         x6, x0, 1992  # x6 = 0x000007c8
    298: 00032203  lw           x4, 0(x6)  # param e2e_l0_k; 0x000007c8
    29c: ff827213  andi         x4, x4, -8
    2a0: 00008437  lui          x8, 0x00008  # x8 = 0x00008000
    2a4: 08c40413  addi         x8, x8, 140  # x8 = 0x0000808c
    2a8: 00042303  lw           x6, 0(x8)  # param e2e_l0_k_row_start; 0x0000808c
    2ac: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
    2b0: 02730333  mul          x6, x6, x7
    2b4: 00737293  andi         x5, x6, 7
    2b8: 00335313  srli         x6, x6, 3
    2bc: 00b31313  slli         x6, x6, 11
    2c0: 00620233  add          x4, x4, x6
    2c4: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    2c8: 00600393  addi         x7, x0, 6  # x7 = 0x00000006
loc_2cc:
    2cc: 0e737263  bgeu         x6, x7, 0x000003b0  # target 0x000003b0
    2d0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2d4: 88468693  addi         x13, x13, -1916  # x13 = 0xffb00884 · riscv_local_mem + 0x884
    2d8: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x884 · 0xffb00884
loc_2dc:
    2dc: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
    2e0: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    2e4: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    2e8: 40940533  sub          x10, x8, x9
    2ec: 01051513  slli         x10, x10, 16
    2f0: 01055513  srli         x10, x10, 16
    2f4: 00400593  addi         x11, x0, 4  # x11 = 0x00000004
    2f8: 40a585b3  sub          x11, x11, x10
    2fc: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    300: 00c5f663  bgeu         x11, x12, 0x0000030c  # target 0x0000030c
    304: 0ff0000f  fence        0xf, 0xf
    308: fd5ff06f  jal          x0, 0x000002dc  # target 0x000002dc
loc_30c:
    30c: 0ff0000f  fence        0xf, 0xf
    310: 1c0000ef  jal          x1, 0x000004d0  # target 0x000004d0; x1 = 0x00000314
    314: 1d8000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000318
    318: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    31c: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
    320: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880
    324: 00020f93  addi         x31, x4, 0
    328: 00028f13  addi         x30, x5, 0
    32c: 00040e93  addi         x29, x8, 0
    330: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    334: 310000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x00000338
    338: 000f8213  addi         x4, x31, 0
    33c: 000f0293  addi         x5, x30, 0
    340: 1ac000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000344
    344: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    348: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    34c: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880
    350: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    354: 00940433  add          x8, x8, x9
    358: 00092537  lui          x10, 0x00092  # x10 = 0x00092000
    35c: 00a46663  bltu         x8, x10, 0x00000368  # target 0x00000368
    360: 000025b7  lui          x11, 0x00002  # x11 = 0x00002000
    364: 40b40433  sub          x8, x8, x11
loc_368:
    368: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    36c: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    370: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    374: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    378: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
    37c: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884
    380: 00240413  addi         x8, x8, 2
    384: 01041413  slli         x8, x8, 16
    388: 01045413  srli         x8, x8, 16
    38c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    390: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
    394: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    398: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    39c: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    3a0: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    3a4: 0ff0000f  fence        0xf, 0xf
    3a8: 00130313  addi         x6, x6, 1
    3ac: f21ff06f  jal          x0, 0x000002cc  # target 0x000002cc
loc_3b0:
    3b0: 7cc00313  addi         x6, x0, 1996  # x6 = 0x000007cc
    3b4: 00032203  lw           x4, 0(x6)  # param e2e_l0_v; 0x000007cc
    3b8: ff827213  andi         x4, x4, -8
    3bc: 00008437  lui          x8, 0x00008  # x8 = 0x00008000
    3c0: 09440413  addi         x8, x8, 148  # x8 = 0x00008094
    3c4: 00042303  lw           x6, 0(x8)  # param e2e_l0_v_row_start; 0x00008094
    3c8: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
    3cc: 02730333  mul          x6, x6, x7
    3d0: 00737293  andi         x5, x6, 7
    3d4: 00335313  srli         x6, x6, 3
    3d8: 00b31313  slli         x6, x6, 11
    3dc: 00620233  add          x4, x4, x6
    3e0: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    3e4: 00600393  addi         x7, x0, 6  # x7 = 0x00000006
loc_3e8:
    3e8: 0e737263  bgeu         x6, x7, 0x000004cc  # target 0x000004cc
    3ec: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    3f0: 88468693  addi         x13, x13, -1916  # x13 = 0xffb00884 · riscv_local_mem + 0x884
    3f4: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x884 · 0xffb00884
loc_3f8:
    3f8: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
    3fc: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    400: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    404: 40940533  sub          x10, x8, x9
    408: 01051513  slli         x10, x10, 16
    40c: 01055513  srli         x10, x10, 16
    410: 00400593  addi         x11, x0, 4  # x11 = 0x00000004
    414: 40a585b3  sub          x11, x11, x10
    418: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    41c: 00c5f663  bgeu         x11, x12, 0x00000428  # target 0x00000428
    420: 0ff0000f  fence        0xf, 0xf
    424: fd5ff06f  jal          x0, 0x000003f8  # target 0x000003f8
loc_428:
    428: 0ff0000f  fence        0xf, 0xf
    42c: 0a4000ef  jal          x1, 0x000004d0  # target 0x000004d0; x1 = 0x00000430
    430: 0bc000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000434
    434: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    438: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
    43c: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880
    440: 00020f93  addi         x31, x4, 0
    444: 00028f13  addi         x30, x5, 0
    448: 00040e93  addi         x29, x8, 0
    44c: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    450: 1f4000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x00000454
    454: 000f8213  addi         x4, x31, 0
    458: 000f0293  addi         x5, x30, 0
    45c: 090000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000460
    460: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    464: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    468: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880
    46c: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    470: 00940433  add          x8, x8, x9
    474: 00092537  lui          x10, 0x00092  # x10 = 0x00092000
    478: 00a46663  bltu         x8, x10, 0x00000484  # target 0x00000484
    47c: 000025b7  lui          x11, 0x00002  # x11 = 0x00002000
    480: 40b40433  sub          x8, x8, x11
loc_484:
    484: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    488: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    48c: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    490: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    494: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
    498: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884
    49c: 00240413  addi         x8, x8, 2
    4a0: 01041413  slli         x8, x8, 16
    4a4: 01045413  srli         x8, x8, 16
    4a8: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    4ac: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
    4b0: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    4b4: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    4b8: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    4bc: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    4c0: 0ff0000f  fence        0xf, 0xf
    4c4: 00130313  addi         x6, x6, 1
    4c8: f21ff06f  jal          x0, 0x000003e8  # target 0x000003e8
loc_4cc:
    4cc: 2680006f  jal          x0, 0x00000734  # target 0x00000734
loc_4d0:
    4d0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4d4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    4d8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    4dc: 000a0463  beq          x20, x0, 0x000004e4  # target 0x000004e4
    4e0: ff1ff06f  jal          x0, 0x000004d0  # target 0x000004d0
loc_4e4:
    4e4: 0ff0000f  fence        0xf, 0xf
    4e8: 00008067  jalr         x0, 0(x1)
loc_4ec:
    4ec: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4f0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    4f4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    4f8: 000a0463  beq          x20, x0, 0x00000500  # target 0x00000500
    4fc: ff1ff06f  jal          x0, 0x000004ec  # target 0x000004ec
loc_500:
    500: 0ff0000f  fence        0xf, 0xf
    504: 00008067  jalr         x0, 0(x1)
loc_508:
    508: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    50c: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x000007c0
    510: 007a7d13  andi         x26, x20, 7
    514: ff8a7a13  andi         x20, x20, -8
    518: 01af8ab3  add          x21, x31, x26
    51c: 007afb93  andi         x23, x21, 7
    520: 003ada93  srli         x21, x21, 3
    524: 00ba9a93  slli         x21, x21, 11
    528: 014a8ab3  add          x21, x21, x20
    52c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000052c
    530: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000544
    534: 001b9b93  slli         x23, x23, 1
    538: 017b0b33  add          x22, x22, x23
    53c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    540: 00008067  jalr         x0, 0(x1)
    544: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    548: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    54c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    550: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_554:
    554: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    558: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    55c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    560: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    564: 015a6463  bltu         x20, x21, 0x0000056c  # target 0x0000056c
    568: fedff06f  jal          x0, 0x00000554  # target 0x00000554
loc_56c:
    56c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    570: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    574: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    578: 014a1a13  slli         x20, x20, 20
    57c: 014a5a13  srli         x20, x20, 20
    580: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_584:
    584: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    588: 000b0463  beq          x22, x0, 0x00000590  # target 0x00000590
    58c: ff9ff06f  jal          x0, 0x00000584  # target 0x00000584
loc_590:
    590: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    594: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    598: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    59c: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    5a0: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    5a4: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    5a8: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    5ac: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    5b0: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    5b4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    5b8: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    5bc: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    5c0: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5c4: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    5c8: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    5cc: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    5d0: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    5d4: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    5d8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    5dc: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    5e0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5e4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_5e8:
    5e8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    5ec: 000b0463  beq          x22, x0, 0x000005f4  # target 0x000005f4
    5f0: ff9ff06f  jal          x0, 0x000005e8  # target 0x000005e8
loc_5f4:
    5f4: 00008067  jalr         x0, 0(x1)
loc_5f8:
    5f8: 7d000a93  addi         x21, x0, 2000  # x21 = 0x000007d0
    5fc: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_input_norm; 0x000007d0
    600: 007a7d13  andi         x26, x20, 7
    604: ff8a7a13  andi         x20, x20, -8
    608: 01af8ab3  add          x21, x31, x26
    60c: 007afb93  andi         x23, x21, 7
    610: 003ada93  srli         x21, x21, 3
    614: 00ba9a93  slli         x21, x21, 11
    618: 014a8ab3  add          x21, x21, x20
    61c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000061c
    620: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000634
    624: 001b9b93  slli         x23, x23, 1
    628: 017b0b33  add          x22, x22, x23
    62c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    630: 00008067  jalr         x0, 0(x1)
    634: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    638: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    63c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    640: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_644:
    644: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000644
    648: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x00000724
loc_64c:
    64c: 001f1a93  slli         x21, x30, 1
    650: 014a8ab3  add          x21, x21, x20
    654: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_658:
    658: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    65c: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    660: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    664: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    668: 018be463  bltu         x23, x24, 0x00000670  # target 0x00000670
    66c: fedff06f  jal          x0, 0x00000658  # target 0x00000658
loc_670:
    670: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    674: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    678: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    67c: 014b9b93  slli         x23, x23, 20
    680: 014bdb93  srli         x23, x23, 20
    684: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_688:
    688: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    68c: 000c8463  beq          x25, x0, 0x00000694  # target 0x00000694
    690: ff9ff06f  jal          x0, 0x00000688  # target 0x00000688
loc_694:
    694: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    698: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    69c: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    6a0: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    6a4: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    6a8: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    6ac: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    6b0: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    6b4: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    6b8: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    6bc: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    6c0: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    6c4: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6c8: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    6cc: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    6d0: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    6d4: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    6d8: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    6dc: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    6e0: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    6e4: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    6e8: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_6ec:
    6ec: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    6f0: 000c8463  beq          x25, x0, 0x000006f8  # target 0x000006f8
    6f4: ff9ff06f  jal          x0, 0x000006ec  # target 0x000006ec
loc_6f8:
    6f8: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6fc: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    700: 016e8eb3  add          x29, x29, x22
    704: 001f0f13  addi         x30, x30, 1
    708: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    70c: 015f1663  bne          x30, x21, 0x00000718  # target 0x00000718
    710: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    714: 016f8fb3  add          x31, x31, x22
loc_718:
    718: fffe0e13  addi         x28, x28, -1
    71c: f20e18e3  bne          x28, x0, 0x0000064c  # target 0x0000064c
    720: 00008067  jalr         x0, 0(x1)
    724: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    728: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    72c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    730: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    734:           j FW_BRISC+4   # return to firmware, linked at install
