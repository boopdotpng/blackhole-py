# llama3 8b-fp8 decode: qkv, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_q, 0x78c=e2e_l0_k, 0x790=e2e_k, 0x794=e2e_l0_v, 0x798=e2e_v, 0x79c=input_scale_0, 0x7a0=input_scale_1, 0x7a4=output_scale_0_0, 0x7a8=output_scale_0_1, 0x7ac=output_scale_1_0, 0x7b0=output_scale_1_1, 0x7b4=output_scale_2_0, 0x7b8=output_scale_2_1, 0x7bc=e2e_l0_input_norm, 0x118c0=e2e_l0_q_row_start, 0x118c4=e2e_l0_k_row_start, 0x118c8=e2e_l0_v_row_start, 0x118cc=e2e_l0_q_rows, 0x118d0=e2e_l0_k_rows, 0x118d4=e2e_l0_v_rows, 0x118d8=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
      4: 86448493  addi         x9, x9, -1948  # x9 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00022537  lui          x10, 0x00022  # x10 = 0x00022000
      c: 08050513  addi         x10, x10, 128  # x10 = 0x00022080
     10: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00022080
     14: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     18: 86848493  addi         x9, x9, -1944  # x9 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     24: 8c030313  addi         x6, x6, -1856  # x6 = 0x000118c0
     28: 00032203  lw           x4, 0(x6)  # param e2e_l0_q_row_start; 0x000118c0
     2c: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     30: 8cc30313  addi         x6, x6, -1844  # x6 = 0x000118cc
     34: 00032283  lw           x5, 0(x6)  # param e2e_l0_q_rows; 0x000118cc
     38: 00121313  slli         x6, x4, 1
     3c: 000283b7  lui          x7, 0x00028  # x7 = 0x00028000
     40: 08038393  addi         x7, x7, 128  # x7 = 0x00028080
     44: 00730333  add          x6, x6, x7
     48: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
     4c: 00028413  addi         x8, x5, 0
loc_50:
     50: 0c83f463  bgeu         x7, x8, 0x00000118  # target 0x00000118
     54: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
     58: 86868693  addi         x13, x13, -1944  # x13 = 0xffb00868 · riscv_local_mem + 0x868
     5c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x868 · 0xffb00868
     60: 00100613  addi         x12, x0, 1  # x12 = 0x00000001
loc_64:
     64: ffb496b7  lui          x13, 0xffb49  # x13 = 0xffb49000
     68: 02868693  addi         x13, x13, 40  # x13 = 0xffb49028
     6c: 0006d503  lhu          x10, 0(x13)  # 0xffb49028
     70: 409505b3  sub          x11, x10, x9
     74: 01059593  slli         x11, x11, 16
     78: 0105d593  srli         x11, x11, 16
     7c: 00c5f663  bgeu         x11, x12, 0x00000088  # target 0x00000088
     80: 0ff0000f  fence        0xf, 0xf
     84: fe1ff06f  jal          x0, 0x00000064  # target 0x00000064
loc_88:
     88: 0ff0000f  fence        0xf, 0xf
     8c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     90: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
     94: 0005a483  lw           x9, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
     98: 0004d503  lhu          x10, 0(x9)  # Address depends on runtime register values
     9c: 00a31023  sh           x10, 0(x6)  # Address depends on runtime register values
     a0: 00230313  addi         x6, x6, 2
     a4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     a8: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
     ac: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
     b0: 00148493  addi         x9, x9, 1
     b4: 01049493  slli         x9, x9, 16
     b8: 0104d493  srli         x9, x9, 16
     bc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     c0: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
     c4: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
     c8: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
     cc: 02050513  addi         x10, x10, 32  # x10 = 0xffb49020
     d0: 00952023  sw           x9, 0(x10)  # 0xffb49020; write runtime value
     d4: 0ff0000f  fence        0xf, 0xf
     d8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
     dc: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
     e0: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864
     e4: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     e8: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
     ec: 00a484b3  add          x9, x9, x10
     f0: 000235b7  lui          x11, 0x00023  # x11 = 0x00023000
     f4: 08058593  addi         x11, x11, 128  # x11 = 0x00023080
     f8: 00b4e663  bltu         x9, x11, 0x00000104  # target 0x00000104
     fc: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    100: 40c484b3  sub          x9, x9, x12
loc_104:
    104: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    108: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    10c: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    110: 00138393  addi         x7, x7, 1
    114: f3dff06f  jal          x0, 0x00000050  # target 0x00000050
loc_118:
    118: 004282b3  add          x5, x5, x4
    11c: 364000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000120
    120: 37c000ef  jal          x1, 0x0000049c  # target 0x0000049c; x1 = 0x00000124
    124: 00020313  addi         x6, x4, 0
loc_128:
    128: 00a35393  srli         x7, x6, 10
    12c: 00038f93  addi         x31, x7, 0
    130: 388000ef  jal          x1, 0x000004b8  # target 0x000004b8; x1 = 0x00000134
    134: 000a8693  addi         x13, x21, 0
    138: 000b0713  addi         x14, x22, 0
    13c: 00131413  slli         x8, x6, 1
    140: 000285b7  lui          x11, 0x00028  # x11 = 0x00028000
    144: 08058593  addi         x11, x11, 128  # x11 = 0x00028080
    148: 008585b3  add          x11, x11, x8
    14c: 7ff47413  andi         x8, x8, 2047
    150: 00868633  add          x12, x13, x8
    154: 00f37493  andi         x9, x6, 15
    158: 01000513  addi         x10, x0, 16  # x10 = 0x00000010
    15c: 409504b3  sub          x9, x10, x9
    160: 40628533  sub          x10, x5, x6
    164: 00957463  bgeu         x10, x9, 0x0000016c  # target 0x0000016c
    168: 00050493  addi         x9, x10, 0
loc_16c:
    16c: 00930333  add          x6, x6, x9
    170: 00149493  slli         x9, x9, 1
    174: 00058f93  addi         x31, x11, 0
    178: 00060f13  addi         x30, x12, 0
    17c: 00070e93  addi         x29, x14, 0
    180: 00048e13  addi         x28, x9, 0
    184: 3b8000ef  jal          x1, 0x0000053c  # target 0x0000053c; x1 = 0x00000188
    188: fa5360e3  bltu         x6, x5, 0x00000128  # target 0x00000128
    18c: 2f4000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000190
    190: 30c000ef  jal          x1, 0x0000049c  # target 0x0000049c; x1 = 0x00000194
    194: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    198: 8c430313  addi         x6, x6, -1852  # x6 = 0x000118c4
    19c: 00032203  lw           x4, 0(x6)  # param e2e_l0_k_row_start; 0x000118c4
    1a0: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    1a4: 8d030313  addi         x6, x6, -1840  # x6 = 0x000118d0
    1a8: 00032283  lw           x5, 0(x6)  # param e2e_l0_k_rows; 0x000118d0
    1ac: 00121313  slli         x6, x4, 1
    1b0: 0002a3b7  lui          x7, 0x0002a  # x7 = 0x0002a000
    1b4: 08038393  addi         x7, x7, 128  # x7 = 0x0002a080
    1b8: 00730333  add          x6, x6, x7
    1bc: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    1c0: 00028413  addi         x8, x5, 0
loc_1c4:
    1c4: 0c83f463  bgeu         x7, x8, 0x0000028c  # target 0x0000028c
    1c8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1cc: 86868693  addi         x13, x13, -1944  # x13 = 0xffb00868 · riscv_local_mem + 0x868
    1d0: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x868 · 0xffb00868
    1d4: 00100613  addi         x12, x0, 1  # x12 = 0x00000001
loc_1d8:
    1d8: ffb496b7  lui          x13, 0xffb49  # x13 = 0xffb49000
    1dc: 02868693  addi         x13, x13, 40  # x13 = 0xffb49028
    1e0: 0006d503  lhu          x10, 0(x13)  # 0xffb49028
    1e4: 409505b3  sub          x11, x10, x9
    1e8: 01059593  slli         x11, x11, 16
    1ec: 0105d593  srli         x11, x11, 16
    1f0: 00c5f663  bgeu         x11, x12, 0x000001fc  # target 0x000001fc
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: fe1ff06f  jal          x0, 0x000001d8  # target 0x000001d8
loc_1fc:
    1fc: 0ff0000f  fence        0xf, 0xf
    200: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    204: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    208: 0005a483  lw           x9, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    20c: 0004d503  lhu          x10, 0(x9)  # Address depends on runtime register values
    210: 00a31023  sh           x10, 0(x6)  # Address depends on runtime register values
    214: 00230313  addi         x6, x6, 2
    218: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    21c: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    220: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
    224: 00148493  addi         x9, x9, 1
    228: 01049493  slli         x9, x9, 16
    22c: 0104d493  srli         x9, x9, 16
    230: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    234: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    238: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    23c: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
    240: 02050513  addi         x10, x10, 32  # x10 = 0xffb49020
    244: 00952023  sw           x9, 0(x10)  # 0xffb49020; write runtime value
    248: 0ff0000f  fence        0xf, 0xf
    24c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    250: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    254: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864
    258: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    25c: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    260: 00a484b3  add          x9, x9, x10
    264: 000235b7  lui          x11, 0x00023  # x11 = 0x00023000
    268: 08058593  addi         x11, x11, 128  # x11 = 0x00023080
    26c: 00b4e663  bltu         x9, x11, 0x00000278  # target 0x00000278
    270: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    274: 40c484b3  sub          x9, x9, x12
loc_278:
    278: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    27c: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    280: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    284: 00138393  addi         x7, x7, 1
    288: f3dff06f  jal          x0, 0x000001c4  # target 0x000001c4
loc_28c:
    28c: 004282b3  add          x5, x5, x4
    290: 1f0000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000294
    294: 208000ef  jal          x1, 0x0000049c  # target 0x0000049c; x1 = 0x00000298
    298: 00020313  addi         x6, x4, 0
loc_29c:
    29c: 00a35393  srli         x7, x6, 10
    2a0: 00038f93  addi         x31, x7, 0
    2a4: 34c000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x000002a8
    2a8: 000a8693  addi         x13, x21, 0
    2ac: 000b0713  addi         x14, x22, 0
    2b0: 00131413  slli         x8, x6, 1
    2b4: 0002a5b7  lui          x11, 0x0002a  # x11 = 0x0002a000
    2b8: 08058593  addi         x11, x11, 128  # x11 = 0x0002a080
    2bc: 008585b3  add          x11, x11, x8
    2c0: 7ff47413  andi         x8, x8, 2047
    2c4: 00868633  add          x12, x13, x8
    2c8: 00f37493  andi         x9, x6, 15
    2cc: 01000513  addi         x10, x0, 16  # x10 = 0x00000010
    2d0: 409504b3  sub          x9, x10, x9
    2d4: 40628533  sub          x10, x5, x6
    2d8: 00957463  bgeu         x10, x9, 0x000002e0  # target 0x000002e0
    2dc: 00050493  addi         x9, x10, 0
loc_2e0:
    2e0: 00930333  add          x6, x6, x9
    2e4: 00149493  slli         x9, x9, 1
    2e8: 00058f93  addi         x31, x11, 0
    2ec: 00060f13  addi         x30, x12, 0
    2f0: 00070e93  addi         x29, x14, 0
    2f4: 00048e13  addi         x28, x9, 0
    2f8: 244000ef  jal          x1, 0x0000053c  # target 0x0000053c; x1 = 0x000002fc
    2fc: fa5360e3  bltu         x6, x5, 0x0000029c  # target 0x0000029c
    300: 180000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000304
    304: 198000ef  jal          x1, 0x0000049c  # target 0x0000049c; x1 = 0x00000308
    308: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    30c: 8c830313  addi         x6, x6, -1848  # x6 = 0x000118c8
    310: 00032203  lw           x4, 0(x6)  # param e2e_l0_v_row_start; 0x000118c8
    314: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    318: 8d430313  addi         x6, x6, -1836  # x6 = 0x000118d4
    31c: 00032283  lw           x5, 0(x6)  # param e2e_l0_v_rows; 0x000118d4
    320: 00121313  slli         x6, x4, 1
    324: 0002b3b7  lui          x7, 0x0002b  # x7 = 0x0002b000
    328: 88038393  addi         x7, x7, -1920  # x7 = 0x0002a880
    32c: 00730333  add          x6, x6, x7
    330: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    334: 00028413  addi         x8, x5, 0
loc_338:
    338: 0c83f463  bgeu         x7, x8, 0x00000400  # target 0x00000400
    33c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    340: 86868693  addi         x13, x13, -1944  # x13 = 0xffb00868 · riscv_local_mem + 0x868
    344: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x868 · 0xffb00868
    348: 00100613  addi         x12, x0, 1  # x12 = 0x00000001
loc_34c:
    34c: ffb496b7  lui          x13, 0xffb49  # x13 = 0xffb49000
    350: 02868693  addi         x13, x13, 40  # x13 = 0xffb49028
    354: 0006d503  lhu          x10, 0(x13)  # 0xffb49028
    358: 409505b3  sub          x11, x10, x9
    35c: 01059593  slli         x11, x11, 16
    360: 0105d593  srli         x11, x11, 16
    364: 00c5f663  bgeu         x11, x12, 0x00000370  # target 0x00000370
    368: 0ff0000f  fence        0xf, 0xf
    36c: fe1ff06f  jal          x0, 0x0000034c  # target 0x0000034c
loc_370:
    370: 0ff0000f  fence        0xf, 0xf
    374: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    378: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    37c: 0005a483  lw           x9, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    380: 0004d503  lhu          x10, 0(x9)  # Address depends on runtime register values
    384: 00a31023  sh           x10, 0(x6)  # Address depends on runtime register values
    388: 00230313  addi         x6, x6, 2
    38c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    390: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    394: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
    398: 00148493  addi         x9, x9, 1
    39c: 01049493  slli         x9, x9, 16
    3a0: 0104d493  srli         x9, x9, 16
    3a4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3a8: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    3ac: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    3b0: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
    3b4: 02050513  addi         x10, x10, 32  # x10 = 0xffb49020
    3b8: 00952023  sw           x9, 0(x10)  # 0xffb49020; write runtime value
    3bc: 0ff0000f  fence        0xf, 0xf
    3c0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    3c4: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    3c8: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864
    3cc: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3d0: 80050513  addi         x10, x10, -2048  # x10 = 0x00000800
    3d4: 00a484b3  add          x9, x9, x10
    3d8: 000235b7  lui          x11, 0x00023  # x11 = 0x00023000
    3dc: 08058593  addi         x11, x11, 128  # x11 = 0x00023080
    3e0: 00b4e663  bltu         x9, x11, 0x000003ec  # target 0x000003ec
    3e4: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    3e8: 40c484b3  sub          x9, x9, x12
loc_3ec:
    3ec: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    3f0: 86468693  addi         x13, x13, -1948  # x13 = 0xffb00864 · riscv_local_mem + 0x864
    3f4: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    3f8: 00138393  addi         x7, x7, 1
    3fc: f3dff06f  jal          x0, 0x00000338  # target 0x00000338
loc_400:
    400: 004282b3  add          x5, x5, x4
    404: 07c000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000408
    408: 094000ef  jal          x1, 0x0000049c  # target 0x0000049c; x1 = 0x0000040c
    40c: 00020313  addi         x6, x4, 0
loc_410:
    410: 00a35393  srli         x7, x6, 10
    414: 00038f93  addi         x31, x7, 0
    418: 25c000ef  jal          x1, 0x00000674  # target 0x00000674; x1 = 0x0000041c
    41c: 000a8693  addi         x13, x21, 0
    420: 000b0713  addi         x14, x22, 0
    424: 00131413  slli         x8, x6, 1
    428: 0002b5b7  lui          x11, 0x0002b  # x11 = 0x0002b000
    42c: 88058593  addi         x11, x11, -1920  # x11 = 0x0002a880
    430: 008585b3  add          x11, x11, x8
    434: 7ff47413  andi         x8, x8, 2047
    438: 00868633  add          x12, x13, x8
    43c: 00f37493  andi         x9, x6, 15
    440: 01000513  addi         x10, x0, 16  # x10 = 0x00000010
    444: 409504b3  sub          x9, x10, x9
    448: 40628533  sub          x10, x5, x6
    44c: 00957463  bgeu         x10, x9, 0x00000454  # target 0x00000454
    450: 00050493  addi         x9, x10, 0
loc_454:
    454: 00930333  add          x6, x6, x9
    458: 00149493  slli         x9, x9, 1
    45c: 00058f93  addi         x31, x11, 0
    460: 00060f13  addi         x30, x12, 0
    464: 00070e93  addi         x29, x14, 0
    468: 00048e13  addi         x28, x9, 0
    46c: 0d0000ef  jal          x1, 0x0000053c  # target 0x0000053c; x1 = 0x00000470
    470: fa5360e3  bltu         x6, x5, 0x00000410  # target 0x00000410
    474: 00c000ef  jal          x1, 0x00000480  # target 0x00000480; x1 = 0x00000478
    478: 024000ef  jal          x1, 0x0000049c  # target 0x0000049c; x1 = 0x0000047c
    47c: 27c0006f  jal          x0, 0x000006f8  # target 0x000006f8
loc_480:
    480: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    484: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    488: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    48c: 000a0463  beq          x20, x0, 0x00000494  # target 0x00000494
    490: ff1ff06f  jal          x0, 0x00000480  # target 0x00000480
loc_494:
    494: 0ff0000f  fence        0xf, 0xf
    498: 00008067  jalr         x0, 0(x1)
loc_49c:
    49c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4a0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    4a4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    4a8: 000a0463  beq          x20, x0, 0x000004b0  # target 0x000004b0
    4ac: ff1ff06f  jal          x0, 0x0000049c  # target 0x0000049c
loc_4b0:
    4b0: 0ff0000f  fence        0xf, 0xf
    4b4: 00008067  jalr         x0, 0(x1)
loc_4b8:
    4b8: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    4bc: 000aaa03  lw           x20, 0(x21)  # param e2e_q; 0x00000788
    4c0: 007a7d13  andi         x26, x20, 7
    4c4: ff8a7a13  andi         x20, x20, -8
    4c8: 01af8ab3  add          x21, x31, x26
    4cc: 007afb93  andi         x23, x21, 7
    4d0: 003ada93  srli         x21, x21, 3
    4d4: 00ba9a93  slli         x21, x21, 11
    4d8: 014a8ab3  add          x21, x21, x20
    4dc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004dc
    4e0: 030b0b13  addi         x22, x22, 48  # x22 = 0x0000050c
    4e4: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4e8: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    4ec: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    4f0: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    4f4: 03cd8db3  mul          x27, x27, x28
    4f8: 01bb0b33  add          x22, x22, x27
    4fc: 001b9b93  slli         x23, x23, 1
    500: 017b0b33  add          x22, x22, x23
    504: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    508: 00008067  jalr         x0, 0(x1)
    50c: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    510: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    514: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    518: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    51c: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    520: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    524: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    528: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    52c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    530: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    534: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    538: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_53c:
    53c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    540: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    544: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    548: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    54c: 015a6463  bltu         x20, x21, 0x00000554  # target 0x00000554
    550: fedff06f  jal          x0, 0x0000053c  # target 0x0000053c
loc_554:
    554: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    558: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    55c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    560: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    564: 015a6463  bltu         x20, x21, 0x0000056c  # target 0x0000056c
    568: fedff06f  jal          x0, 0x00000554  # target 0x00000554
loc_56c:
    56c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    570: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    574: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    578: 014a1a13  slli         x20, x20, 20
    57c: 014a5a13  srli         x20, x20, 20
    580: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_584:
    584: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    588: 000b0463  beq          x22, x0, 0x00000590  # target 0x00000590
    58c: ff9ff06f  jal          x0, 0x00000584  # target 0x00000584
loc_590:
    590: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    594: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    598: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    59c: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    5a0: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    5a4: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    5a8: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    5ac: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    5b0: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    5b4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    5b8: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    5bc: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    5c0: 03cba023  sw           x28, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write runtime value
    5c4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    5c8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    5cc: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    5d0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    5d4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    5d8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    5dc: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_5e0:
    5e0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    5e4: 000b0463  beq          x22, x0, 0x000005ec  # target 0x000005ec
    5e8: ff9ff06f  jal          x0, 0x000005e0  # target 0x000005e0
loc_5ec:
    5ec: 00008067  jalr         x0, 0(x1)
loc_5f0:
    5f0: 79000a93  addi         x21, x0, 1936  # x21 = 0x00000790
    5f4: 000aaa03  lw           x20, 0(x21)  # param e2e_k; 0x00000790
    5f8: 007a7d13  andi         x26, x20, 7
    5fc: ff8a7a13  andi         x20, x20, -8
    600: 01af8ab3  add          x21, x31, x26
    604: 007afb93  andi         x23, x21, 7
    608: 003ada93  srli         x21, x21, 3
    60c: 00ba9a93  slli         x21, x21, 11
    610: 014a8ab3  add          x21, x21, x20
    614: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000614
    618: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000644
    61c: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    620: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    624: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    628: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    62c: 03cd8db3  mul          x27, x27, x28
    630: 01bb0b33  add          x22, x22, x27
    634: 001b9b93  slli         x23, x23, 1
    638: 017b0b33  add          x22, x22, x23
    63c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    640: 00008067  jalr         x0, 0(x1)
    644: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    648: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    64c: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    650: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    654: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    658: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    65c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    660: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    664: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    668: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    66c: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    670: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_674:
    674: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    678: 000aaa03  lw           x20, 0(x21)  # param e2e_v; 0x00000798
    67c: 007a7d13  andi         x26, x20, 7
    680: ff8a7a13  andi         x20, x20, -8
    684: 01af8ab3  add          x21, x31, x26
    688: 007afb93  andi         x23, x21, 7
    68c: 003ada93  srli         x21, x21, 3
    690: 00ba9a93  slli         x21, x21, 11
    694: 014a8ab3  add          x21, x21, x20
    698: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000698
    69c: 030b0b13  addi         x22, x22, 48  # x22 = 0x000006c8
    6a0: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    6a4: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    6a8: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    6ac: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    6b0: 03cd8db3  mul          x27, x27, x28
    6b4: 01bb0b33  add          x22, x22, x27
    6b8: 001b9b93  slli         x23, x23, 1
    6bc: 017b0b33  add          x22, x22, x23
    6c0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6c4: 00008067  jalr         x0, 0(x1)
    6c8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6cc: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6d4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    6d8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6dc: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6e0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    6e4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    6e8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    6ec: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6f0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    6f4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    6f8:           j FW_NCRISC+4   # return to firmware, linked at install
