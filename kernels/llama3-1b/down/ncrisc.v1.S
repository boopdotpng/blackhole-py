# llama3 1b decode: down, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (40): 7,2 10,2 11,2 12,2 13,2 7,3 10,3 11,3 12,3 13,3 7,4 10,4 11,4 12,4 13,4 7,5 10,5 11,5 12,5 13,5 7,6 10,6 11,6 12,6 13,6 7,7 10,7 11,7 12,7 13,7 7,8 10,8 11,8 12,8 13,8 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_hidden_dense_decode_token, 0x784=e2e_l0_down, 0x788=e2e_x_a, 0x78c=e2e_x_b, 0xe980=e2e_q_compact, 0xe984=e2e_l0_down_row_start, 0xe988=dense_start, 0xe98c=e2e_l0_down_rows
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00017437  lui          x8, 0x00017  # x8 = 0x00017000
      c: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00017000
     10: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     14: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     18: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     20: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     24: 0001c2b7  lui          x5, 0x0001c  # x5 = 0x0001c000
     28: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x0001c000
     2c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     30: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     34: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     38: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     3c: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     40: 0001e2b7  lui          x5, 0x0001e  # x5 = 0x0001e000
     44: 80028293  addi         x5, x5, -2048  # x5 = 0x0001d800
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x0001d800
     4c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     50: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     54: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     58: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     5c: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     60: 0001e2b7  lui          x5, 0x0001e  # x5 = 0x0001e000
     64: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x0001e000
     68: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     6c: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     70: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     74: 0001c237  lui          x4, 0x0001c  # x4 = 0x0001c000
     78: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_7c:
     7c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     80: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     84: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     88: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     8c: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     90: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     94: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     98: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     9c: 02020213  addi         x4, x4, 32
     a0: ff828293  addi         x5, x5, -8
     a4: fc029ce3  bne          x5, x0, 0x0000007c  # target 0x0000007c
     a8: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     ac: 98c28293  addi         x5, x5, -1652  # x5 = 0x0000e98c
     b0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000e98c
     b4: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     b8: 00020313  addi         x6, x4, 0
loc_bc:
     bc: 0e62f863  bgeu         x5, x6, 0x000001ac  # target 0x000001ac
     c0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     c4: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     c8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     cc: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_d0:
     d0: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     d4: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     d8: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     dc: 407404b3  sub          x9, x8, x7
     e0: 01049493  slli         x9, x9, 16
     e4: 0104d493  srli         x9, x9, 16
     e8: 00a4f663  bgeu         x9, x10, 0x000000f4  # target 0x000000f4
     ec: 0ff0000f  fence        0xf, 0xf
     f0: fe1ff06f  jal          x0, 0x000000d0  # target 0x000000d0
loc_f4:
     f4: 0ff0000f  fence        0xf, 0xf
     f8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     fc: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    100: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    104: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    108: 00f2f493  andi         x9, x5, 15
    10c: 00149493  slli         x9, x9, 1
    110: 0102f593  andi         x11, x5, 16
    114: 00559593  slli         x11, x11, 5
    118: 00b4e4b3  or           x9, x9, x11
    11c: 1e02f593  andi         x11, x5, 480
    120: 00b4e4b3  or           x9, x9, x11
    124: 0092d593  srli         x11, x5, 9
    128: 00a59593  slli         x11, x11, 10
    12c: 00b4e4b3  or           x9, x9, x11
    130: 0001c537  lui          x10, 0x0001c  # x10 = 0x0001c000
    134: 00950533  add          x10, x10, x9
    138: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    13c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    140: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    144: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    148: 00138393  addi         x7, x7, 1
    14c: 01039393  slli         x7, x7, 16
    150: 0103d393  srli         x7, x7, 16
    154: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    158: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    15c: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    160: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    164: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    168: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    16c: 0ff0000f  fence        0xf, 0xf
    170: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    174: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    178: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    17c: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    180: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    184: 008383b3  add          x7, x7, x8
    188: 000184b7  lui          x9, 0x00018  # x9 = 0x00018000
    18c: 0093e663  bltu         x7, x9, 0x00000198  # target 0x00000198
    190: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    194: 40a383b3  sub          x7, x7, x10
loc_198:
    198: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    19c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    1a0: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    1a4: 00128293  addi         x5, x5, 1
    1a8: f15ff06f  jal          x0, 0x000000bc  # target 0x000000bc
loc_1ac:
    1ac: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1b0: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1b4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    1b8: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1bc: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    1c0: 00520233  add          x4, x4, x5
    1c4: 0001d337  lui          x6, 0x0001d  # x6 = 0x0001d000
    1c8: 80030313  addi         x6, x6, -2048  # x6 = 0x0001c800
    1cc: 00626863  bltu         x4, x6, 0x000001dc  # target 0x000001dc
    1d0: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1d4: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    1d8: 40720233  sub          x4, x4, x7
loc_1dc:
    1dc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1e0: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1e4: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    1e8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1ec: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    1f0: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    1f4: 00120213  addi         x4, x4, 1
    1f8: 01021213  slli         x4, x4, 16
    1fc: 01025213  srli         x4, x4, 16
    200: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    204: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    208: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    20c: ffb4a2b7  lui          x5, 0xffb4a  # x5 = 0xffb4a000
    210: 02828293  addi         x5, x5, 40  # x5 = 0xffb4a028
    214: 0042a023  sw           x4, 0(x5)  # 0xffb4a028; write runtime value
    218: 0ff0000f  fence        0xf, 0xf
    21c: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
    220: 98830313  addi         x6, x6, -1656  # x6 = 0x0000e988
    224: 00032203  lw           x4, 0(x6)  # param dense_start; 0x0000e988
    228: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
    22c: 98c30313  addi         x6, x6, -1652  # x6 = 0x0000e98c
    230: 00032283  lw           x5, 0(x6)  # param e2e_l0_down_rows; 0x0000e98c
    234: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    238: 00028393  addi         x7, x5, 0
loc_23c:
    23c: 04737e63  bgeu         x6, x7, 0x00000298  # target 0x00000298
    240: 00620433  add          x8, x4, x6
    244: 00141493  slli         x9, x8, 1
    248: 0001d637  lui          x12, 0x0001d  # x12 = 0x0001d000
    24c: 80060613  addi         x12, x12, -2048  # x12 = 0x0001c800
    250: 00c484b3  add          x9, x9, x12
    254: 0004d583  lhu          x11, 0(x9)  # Address depends on runtime register values
    258: 00f37513  andi         x10, x6, 15
    25c: 00151513  slli         x10, x10, 1
    260: 01037613  andi         x12, x6, 16
    264: 00561613  slli         x12, x12, 5
    268: 00c56533  or           x10, x10, x12
    26c: 1e037613  andi         x12, x6, 480
    270: 00c56533  or           x10, x10, x12
    274: 00935613  srli         x12, x6, 9
    278: 00a61613  slli         x12, x12, 10
    27c: 00c56533  or           x10, x10, x12
    280: 0001e637  lui          x12, 0x0001e  # x12 = 0x0001e000
    284: 80060613  addi         x12, x12, -2048  # x12 = 0x0001d800
    288: 00c50533  add          x10, x10, x12
    28c: 00b51023  sh           x11, 0(x10)  # Address depends on runtime register values
    290: 00130313  addi         x6, x6, 1
    294: fa9ff06f  jal          x0, 0x0000023c  # target 0x0000023c
loc_298:
    298: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    29c: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    2a0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    2a4: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2a8: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    2ac: 00520233  add          x4, x4, x5
    2b0: 0001e337  lui          x6, 0x0001e  # x6 = 0x0001e000
    2b4: 00626863  bltu         x4, x6, 0x000002c4  # target 0x000002c4
    2b8: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2bc: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    2c0: 40720233  sub          x4, x4, x7
loc_2c4:
    2c4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2c8: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    2cc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    2d0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2d4: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    2d8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    2dc: 00120213  addi         x4, x4, 1
    2e0: 01021213  slli         x4, x4, 16
    2e4: 01025213  srli         x4, x4, 16
    2e8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2ec: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    2f0: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    2f4: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    2f8: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    2fc: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    300: 0ff0000f  fence        0xf, 0xf
    304: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    308: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    30c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    310: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_314:
    314: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    318: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    31c: 00045283  lhu          x5, 0(x8)  # 0xffb4c028
    320: 40428333  sub          x6, x5, x4
    324: 01031313  slli         x6, x6, 16
    328: 01035313  srli         x6, x6, 16
    32c: 00737663  bgeu         x6, x7, 0x00000338  # target 0x00000338
    330: 0ff0000f  fence        0xf, 0xf
    334: fe1ff06f  jal          x0, 0x00000314  # target 0x00000314
loc_338:
    338: 0ff0000f  fence        0xf, 0xf
    33c: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    340: 98838393  addi         x7, x7, -1656  # x7 = 0x0000e988
    344: 0003a203  lw           x4, 0(x7)  # param dense_start; 0x0000e988
    348: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    34c: 98c38393  addi         x7, x7, -1652  # x7 = 0x0000e98c
    350: 0003a303  lw           x6, 0(x7)  # param e2e_l0_down_rows; 0x0000e98c
    354: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    358: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    35c: 0003a283  lw           x5, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c
    360: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    364: 00030413  addi         x8, x6, 0
loc_368:
    368: 0483fa63  bgeu         x7, x8, 0x000003bc  # target 0x000003bc
    36c: 007204b3  add          x9, x4, x7
    370: 00f3f513  andi         x10, x7, 15
    374: 00151513  slli         x10, x10, 1
    378: 0103f693  andi         x13, x7, 16
    37c: 00569693  slli         x13, x13, 5
    380: 00d56533  or           x10, x10, x13
    384: 1e03f693  andi         x13, x7, 480
    388: 00d56533  or           x10, x10, x13
    38c: 0093d693  srli         x13, x7, 9
    390: 00a69693  slli         x13, x13, 10
    394: 00d56533  or           x10, x10, x13
    398: 00a28533  add          x10, x5, x10
    39c: 00055603  lhu          x12, 0(x10)  # Address depends on runtime register values
    3a0: 00149593  slli         x11, x9, 1
    3a4: 0001f6b7  lui          x13, 0x0001f  # x13 = 0x0001f000
    3a8: 80068693  addi         x13, x13, -2048  # x13 = 0x0001e800
    3ac: 00d585b3  add          x11, x11, x13
    3b0: 00c59023  sh           x12, 0(x11)  # Address depends on runtime register values
    3b4: 00138393  addi         x7, x7, 1
    3b8: fb1ff06f  jal          x0, 0x00000368  # target 0x00000368
loc_3bc:
    3bc: 1a8000ef  jal          x1, 0x00000564  # target 0x00000564; x1 = 0x000003c0
    3c0: 1c0000ef  jal          x1, 0x00000580  # target 0x00000580; x1 = 0x000003c4
    3c4: 00020393  addi         x7, x4, 0
    3c8: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    3cc: 98c48493  addi         x9, x9, -1652  # x9 = 0x0000e98c
    3d0: 0004a403  lw           x8, 0(x9)  # param e2e_l0_down_rows; 0x0000e98c
    3d4: 00440433  add          x8, x8, x4
loc_3d8:
    3d8: 00a3d493  srli         x9, x7, 10
    3dc: 00048f93  addi         x31, x9, 0
    3e0: 1bc000ef  jal          x1, 0x0000059c  # target 0x0000059c; x1 = 0x000003e4
    3e4: 000a8793  addi         x15, x21, 0
    3e8: 000b0813  addi         x16, x22, 0
    3ec: 00139513  slli         x10, x7, 1
    3f0: 0001f6b7  lui          x13, 0x0001f  # x13 = 0x0001f000
    3f4: 80068693  addi         x13, x13, -2048  # x13 = 0x0001e800
    3f8: 00a686b3  add          x13, x13, x10
    3fc: 7ff57513  andi         x10, x10, 2047
    400: 00a78733  add          x14, x15, x10
    404: 00f3f593  andi         x11, x7, 15
    408: 01000613  addi         x12, x0, 16  # x12 = 0x00000010
    40c: 40b605b3  sub          x11, x12, x11
    410: 40740633  sub          x12, x8, x7
    414: 00b67463  bgeu         x12, x11, 0x0000041c  # target 0x0000041c
    418: 00060593  addi         x11, x12, 0
loc_41c:
    41c: 00b383b3  add          x7, x7, x11
    420: 00159593  slli         x11, x11, 1
    424: 00068f93  addi         x31, x13, 0
    428: 00070f13  addi         x30, x14, 0
    42c: 00080e93  addi         x29, x16, 0
    430: 00058e13  addi         x28, x11, 0
loc_434:
    434: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    438: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    43c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    440: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    444: 015a6463  bltu         x20, x21, 0x0000044c  # target 0x0000044c
    448: fedff06f  jal          x0, 0x00000434  # target 0x00000434
loc_44c:
    44c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    450: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    454: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    458: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    45c: 015a6463  bltu         x20, x21, 0x00000464  # target 0x00000464
    460: fedff06f  jal          x0, 0x0000044c  # target 0x0000044c
loc_464:
    464: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    468: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    46c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    470: 014a1a13  slli         x20, x20, 20
    474: 014a5a13  srli         x20, x20, 20
    478: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_47c:
    47c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    480: 000b0463  beq          x22, x0, 0x00000488  # target 0x00000488
    484: ff9ff06f  jal          x0, 0x0000047c  # target 0x0000047c
loc_488:
    488: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    48c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    490: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    494: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    498: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    49c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    4a0: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    4a4: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    4a8: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    4ac: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    4b0: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    4b4: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    4b8: 03cba023  sw           x28, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write runtime value
    4bc: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    4c0: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    4c4: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    4c8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    4cc: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    4d0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    4d4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_4d8:
    4d8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    4dc: 000b0463  beq          x22, x0, 0x000004e4  # target 0x000004e4
    4e0: ff9ff06f  jal          x0, 0x000004d8  # target 0x000004d8
loc_4e4:
    4e4: ee83eae3  bltu         x7, x8, 0x000003d8  # target 0x000003d8
    4e8: 07c000ef  jal          x1, 0x00000564  # target 0x00000564; x1 = 0x000004ec
    4ec: 094000ef  jal          x1, 0x00000580  # target 0x00000580; x1 = 0x000004f0
    4f0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4f4: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    4f8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    4fc: 00120213  addi         x4, x4, 1
    500: 01021213  slli         x4, x4, 16
    504: 01025213  srli         x4, x4, 16
    508: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    50c: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    510: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    514: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    518: 02028293  addi         x5, x5, 32  # x5 = 0xffb4c020
    51c: 0042a023  sw           x4, 0(x5)  # 0xffb4c020; write runtime value
    520: 0ff0000f  fence        0xf, 0xf
    524: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    528: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    52c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    530: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    534: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    538: 00520233  add          x4, x4, x5
    53c: 0001f337  lui          x6, 0x0001f  # x6 = 0x0001f000
    540: 80030313  addi         x6, x6, -2048  # x6 = 0x0001e800
    544: 00626863  bltu         x4, x6, 0x00000554  # target 0x00000554
    548: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    54c: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    550: 40720233  sub          x4, x4, x7
loc_554:
    554: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    558: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    55c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    560: 0880006f  jal          x0, 0x000005e8  # target 0x000005e8
loc_564:
    564: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    568: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    56c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    570: 000a0463  beq          x20, x0, 0x00000578  # target 0x00000578
    574: ff1ff06f  jal          x0, 0x00000564  # target 0x00000564
loc_578:
    578: 0ff0000f  fence        0xf, 0xf
    57c: 00008067  jalr         x0, 0(x1)
loc_580:
    580: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    584: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    588: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    58c: 000a0463  beq          x20, x0, 0x00000594  # target 0x00000594
    590: ff1ff06f  jal          x0, 0x00000580  # target 0x00000580
loc_594:
    594: 0ff0000f  fence        0xf, 0xf
    598: 00008067  jalr         x0, 0(x1)
loc_59c:
    59c: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    5a0: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x00000788
    5a4: 007a7d13  andi         x26, x20, 7
    5a8: ff8a7a13  andi         x20, x20, -8
    5ac: 01af8ab3  add          x21, x31, x26
    5b0: 007afb93  andi         x23, x21, 7
    5b4: 003ada93  srli         x21, x21, 3
    5b8: 00ba9a93  slli         x21, x21, 11
    5bc: 014a8ab3  add          x21, x21, x20
    5c0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005c0
    5c4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000005d8
    5c8: 001b9b93  slli         x23, x23, 1
    5cc: 017b0b33  add          x22, x22, x23
    5d0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    5d4: 00008067  jalr         x0, 0(x1)
    5d8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    5dc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5e0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5e4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    5e8:           j FW_NCRISC+4   # return to firmware, linked at install
