# llama3 8b-fp8 decode: down, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (48): 7,4 10,4 11,4 12,4 13,4 14,4 7,5 10,5 11,5 12,5 13,5 14,5 7,6 10,6 11,6 12,6 13,6 14,6 7,7 10,7 11,7 12,7 13,7 14,7 7,8 10,8 11,8 12,8 13,8 14,8 7,9 10,9 11,9 12,9 13,9 14,9 7,10 10,10 11,10 12,10 13,10 14,10 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x7c0=e2e_hidden_dense_decode_token, 0x7c4=e2e_l0_down, 0x7c8=input_scale_0, 0x7cc=input_scale_1, 0x7d0=output_scale_0_0, 0x7d4=output_scale_0_1, 0x7d8=e2e_x_a, 0x7dc=e2e_x_b, 0x8140=e2e_q_compact, 0x8144=e2e_l0_down_row_start, 0x8148=dense_start, 0x814c=e2e_l0_down_rows
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000c8437  lui          x8, 0x000c8  # x8 = 0x000c8000
      c: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x000c8000
     10: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     14: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     18: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     20: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     24: 000cd2b7  lui          x5, 0x000cd  # x5 = 0x000cd000
     28: 80028293  addi         x5, x5, -2048  # x5 = 0x000cc800
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x000cc800
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     3c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     40: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     44: 000d62b7  lui          x5, 0x000d6  # x5 = 0x000d6000
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x000d6000
     4c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     50: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     54: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     58: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     5c: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     60: 000d72b7  lui          x5, 0x000d7  # x5 = 0x000d7000
     64: 80028293  addi         x5, x5, -2048  # x5 = 0x000d6800
     68: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x000d6800
     6c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     70: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     74: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     78: 000cd237  lui          x4, 0x000cd  # x4 = 0x000cd000
     7c: 80020213  addi         x4, x4, -2048  # x4 = 0x000cc800
     80: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_84:
     84: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     88: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     8c: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     90: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     94: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     98: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     9c: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     a0: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     a4: 02020213  addi         x4, x4, 32
     a8: ff828293  addi         x5, x5, -8
     ac: fc029ce3  bne          x5, x0, 0x00000084  # target 0x00000084
     b0: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
     b4: 14c28293  addi         x5, x5, 332  # x5 = 0x0000814c
     b8: 0002a203  lw           x4, 0(x5)  # param e2e_l0_down_rows; 0x0000814c
     bc: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     c0: 00020313  addi         x6, x4, 0
loc_c4:
     c4: 0e62fa63  bgeu         x5, x6, 0x000001b8  # target 0x000001b8
     c8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     cc: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     d0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     d4: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_d8:
     d8: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     dc: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     e0: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     e4: 407404b3  sub          x9, x8, x7
     e8: 01049493  slli         x9, x9, 16
     ec: 0104d493  srli         x9, x9, 16
     f0: 00a4f663  bgeu         x9, x10, 0x000000fc  # target 0x000000fc
     f4: 0ff0000f  fence        0xf, 0xf
     f8: fe1ff06f  jal          x0, 0x000000d8  # target 0x000000d8
loc_fc:
     fc: 0ff0000f  fence        0xf, 0xf
    100: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    104: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    108: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    10c: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    110: 00f2f493  andi         x9, x5, 15
    114: 00149493  slli         x9, x9, 1
    118: 0102f593  andi         x11, x5, 16
    11c: 00559593  slli         x11, x11, 5
    120: 00b4e4b3  or           x9, x9, x11
    124: 1e02f593  andi         x11, x5, 480
    128: 00b4e4b3  or           x9, x9, x11
    12c: 0092d593  srli         x11, x5, 9
    130: 00a59593  slli         x11, x11, 10
    134: 00b4e4b3  or           x9, x9, x11
    138: 000cd537  lui          x10, 0x000cd  # x10 = 0x000cd000
    13c: 80050513  addi         x10, x10, -2048  # x10 = 0x000cc800
    140: 00950533  add          x10, x10, x9
    144: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    148: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    14c: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    150: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    154: 00138393  addi         x7, x7, 1
    158: 01039393  slli         x7, x7, 16
    15c: 0103d393  srli         x7, x7, 16
    160: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    164: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    168: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    16c: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    170: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    174: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    178: 0ff0000f  fence        0xf, 0xf
    17c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    180: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    184: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    188: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    18c: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    190: 008383b3  add          x7, x7, x8
    194: 000c94b7  lui          x9, 0x000c9  # x9 = 0x000c9000
    198: 0093e663  bltu         x7, x9, 0x000001a4  # target 0x000001a4
    19c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1a0: 40a383b3  sub          x7, x7, x10
loc_1a4:
    1a4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1a8: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    1ac: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    1b0: 00128293  addi         x5, x5, 1
    1b4: f11ff06f  jal          x0, 0x000000c4  # target 0x000000c4
loc_1b8:
    1b8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1bc: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1c0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    1c4: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1c8: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    1cc: 00520233  add          x4, x4, x5
    1d0: 000cd337  lui          x6, 0x000cd  # x6 = 0x000cd000
    1d4: 00626863  bltu         x4, x6, 0x000001e4  # target 0x000001e4
    1d8: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1dc: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    1e0: 40720233  sub          x4, x4, x7
loc_1e4:
    1e4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1e8: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1ec: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    1f0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1f4: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    1f8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    1fc: 00120213  addi         x4, x4, 1
    200: 01021213  slli         x4, x4, 16
    204: 01025213  srli         x4, x4, 16
    208: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    20c: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    210: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    214: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    218: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    21c: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    220: 0ff0000f  fence        0xf, 0xf
    224: 00008337  lui          x6, 0x00008  # x6 = 0x00008000
    228: 14830313  addi         x6, x6, 328  # x6 = 0x00008148
    22c: 00032203  lw           x4, 0(x6)  # param dense_start; 0x00008148
    230: 00008337  lui          x6, 0x00008  # x6 = 0x00008000
    234: 14c30313  addi         x6, x6, 332  # x6 = 0x0000814c
    238: 00032283  lw           x5, 0(x6)  # param e2e_l0_down_rows; 0x0000814c
    23c: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    240: 00028393  addi         x7, x5, 0
loc_244:
    244: 04737a63  bgeu         x6, x7, 0x00000298  # target 0x00000298
    248: 00620433  add          x8, x4, x6
    24c: 00141493  slli         x9, x8, 1
    250: 000d4637  lui          x12, 0x000d4  # x12 = 0x000d4000
    254: 00c484b3  add          x9, x9, x12
    258: 0004d583  lhu          x11, 0(x9)  # Address depends on runtime register values
    25c: 00f37513  andi         x10, x6, 15
    260: 00151513  slli         x10, x10, 1
    264: 01037613  andi         x12, x6, 16
    268: 00561613  slli         x12, x12, 5
    26c: 00c56533  or           x10, x10, x12
    270: 1e037613  andi         x12, x6, 480
    274: 00c56533  or           x10, x10, x12
    278: 00935613  srli         x12, x6, 9
    27c: 00a61613  slli         x12, x12, 10
    280: 00c56533  or           x10, x10, x12
    284: 000d6637  lui          x12, 0x000d6  # x12 = 0x000d6000
    288: 00c50533  add          x10, x10, x12
    28c: 00b51023  sh           x11, 0(x10)  # Address depends on runtime register values
    290: 00130313  addi         x6, x6, 1
    294: fb1ff06f  jal          x0, 0x00000244  # target 0x00000244
loc_298:
    298: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    29c: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    2a0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    2a4: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2a8: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    2ac: 00520233  add          x4, x4, x5
    2b0: 000d7337  lui          x6, 0x000d7  # x6 = 0x000d7000
    2b4: 80030313  addi         x6, x6, -2048  # x6 = 0x000d6800
    2b8: 00626863  bltu         x4, x6, 0x000002c8  # target 0x000002c8
    2bc: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c0: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    2c4: 40720233  sub          x4, x4, x7
loc_2c8:
    2c8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2cc: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    2d0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    2d4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2d8: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    2dc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    2e0: 00120213  addi         x4, x4, 1
    2e4: 01021213  slli         x4, x4, 16
    2e8: 01025213  srli         x4, x4, 16
    2ec: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2f0: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    2f4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    2f8: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    2fc: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    300: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    304: 0ff0000f  fence        0xf, 0xf
    308: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    30c: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    310: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    314: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_318:
    318: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    31c: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    320: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    324: 40428333  sub          x6, x5, x4
    328: 01031313  slli         x6, x6, 16
    32c: 01035313  srli         x6, x6, 16
    330: 00737663  bgeu         x6, x7, 0x0000033c  # target 0x0000033c
    334: 0ff0000f  fence        0xf, 0xf
    338: fe1ff06f  jal          x0, 0x00000318  # target 0x00000318
loc_33c:
    33c: 0ff0000f  fence        0xf, 0xf
    340: 000083b7  lui          x7, 0x00008  # x7 = 0x00008000
    344: 14838393  addi         x7, x7, 328  # x7 = 0x00008148
    348: 0003a203  lw           x4, 0(x7)  # param dense_start; 0x00008148
    34c: 000083b7  lui          x7, 0x00008  # x7 = 0x00008000
    350: 14c38393  addi         x7, x7, 332  # x7 = 0x0000814c
    354: 0003a303  lw           x6, 0(x7)  # param e2e_l0_down_rows; 0x0000814c
    358: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    35c: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    360: 0003a283  lw           x5, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c
    364: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    368: 00030413  addi         x8, x6, 0
loc_36c:
    36c: 0483f863  bgeu         x7, x8, 0x000003bc  # target 0x000003bc
    370: 007204b3  add          x9, x4, x7
    374: 00f3f513  andi         x10, x7, 15
    378: 00151513  slli         x10, x10, 1
    37c: 0103f693  andi         x13, x7, 16
    380: 00569693  slli         x13, x13, 5
    384: 00d56533  or           x10, x10, x13
    388: 1e03f693  andi         x13, x7, 480
    38c: 00d56533  or           x10, x10, x13
    390: 0093d693  srli         x13, x7, 9
    394: 00a69693  slli         x13, x13, 10
    398: 00d56533  or           x10, x10, x13
    39c: 00a28533  add          x10, x5, x10
    3a0: 00055603  lhu          x12, 0(x10)  # Address depends on runtime register values
    3a4: 00149593  slli         x11, x9, 1
    3a8: 000d76b7  lui          x13, 0x000d7  # x13 = 0x000d7000
    3ac: 00d585b3  add          x11, x11, x13
    3b0: 00c59023  sh           x12, 0(x11)  # Address depends on runtime register values
    3b4: 00138393  addi         x7, x7, 1
    3b8: fb5ff06f  jal          x0, 0x0000036c  # target 0x0000036c
loc_3bc:
    3bc: 1a0000ef  jal          x1, 0x0000055c  # target 0x0000055c; x1 = 0x000003c0
    3c0: 1b8000ef  jal          x1, 0x00000578  # target 0x00000578; x1 = 0x000003c4
    3c4: 00020393  addi         x7, x4, 0
    3c8: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    3cc: 14c48493  addi         x9, x9, 332  # x9 = 0x0000814c
    3d0: 0004a403  lw           x8, 0(x9)  # param e2e_l0_down_rows; 0x0000814c
    3d4: 00440433  add          x8, x8, x4
loc_3d8:
    3d8: 00a3d493  srli         x9, x7, 10
    3dc: 00048f93  addi         x31, x9, 0
    3e0: 1b4000ef  jal          x1, 0x00000594  # target 0x00000594; x1 = 0x000003e4
    3e4: 000a8793  addi         x15, x21, 0
    3e8: 000b0813  addi         x16, x22, 0
    3ec: 00139513  slli         x10, x7, 1
    3f0: 000d76b7  lui          x13, 0x000d7  # x13 = 0x000d7000
    3f4: 00a686b3  add          x13, x13, x10
    3f8: 7ff57513  andi         x10, x10, 2047
    3fc: 00a78733  add          x14, x15, x10
    400: 00f3f593  andi         x11, x7, 15
    404: 01000613  addi         x12, x0, 16  # x12 = 0x00000010
    408: 40b605b3  sub          x11, x12, x11
    40c: 40740633  sub          x12, x8, x7
    410: 00b67463  bgeu         x12, x11, 0x00000418  # target 0x00000418
    414: 00060593  addi         x11, x12, 0
loc_418:
    418: 00b383b3  add          x7, x7, x11
    41c: 00159593  slli         x11, x11, 1
    420: 00068f93  addi         x31, x13, 0
    424: 00070f13  addi         x30, x14, 0
    428: 00080e93  addi         x29, x16, 0
    42c: 00058e13  addi         x28, x11, 0
loc_430:
    430: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    434: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    438: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    43c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    440: 015a6463  bltu         x20, x21, 0x00000448  # target 0x00000448
    444: fedff06f  jal          x0, 0x00000430  # target 0x00000430
loc_448:
    448: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    44c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    450: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    454: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    458: 015a6463  bltu         x20, x21, 0x00000460  # target 0x00000460
    45c: fedff06f  jal          x0, 0x00000448  # target 0x00000448
loc_460:
    460: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    464: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    468: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    46c: 014a1a13  slli         x20, x20, 20
    470: 014a5a13  srli         x20, x20, 20
    474: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_478:
    478: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    47c: 000b0463  beq          x22, x0, 0x00000484  # target 0x00000484
    480: ff9ff06f  jal          x0, 0x00000478  # target 0x00000478
loc_484:
    484: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    488: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    48c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    490: 014ba423  sw           x20, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    494: 01eba623  sw           x30, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    498: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    49c: 01dbaa23  sw           x29, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    4a0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    4a4: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    4a8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    4ac: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    4b0: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002092
    4b4: 03cba023  sw           x28, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write runtime value
    4b8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    4bc: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    4c0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    4c4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    4c8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    4cc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    4d0: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_4d4:
    4d4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    4d8: 000b0463  beq          x22, x0, 0x000004e0  # target 0x000004e0
    4dc: ff9ff06f  jal          x0, 0x000004d4  # target 0x000004d4
loc_4e0:
    4e0: ee83ece3  bltu         x7, x8, 0x000003d8  # target 0x000003d8
    4e4: 078000ef  jal          x1, 0x0000055c  # target 0x0000055c; x1 = 0x000004e8
    4e8: 090000ef  jal          x1, 0x00000578  # target 0x00000578; x1 = 0x000004ec
    4ec: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4f0: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    4f4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    4f8: 00120213  addi         x4, x4, 1
    4fc: 01021213  slli         x4, x4, 16
    500: 01025213  srli         x4, x4, 16
    504: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    508: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    50c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    510: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    514: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    518: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    51c: 0ff0000f  fence        0xf, 0xf
    520: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    524: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    528: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    52c: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    530: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    534: 00520233  add          x4, x4, x5
    538: 000d7337  lui          x6, 0x000d7  # x6 = 0x000d7000
    53c: 00626863  bltu         x4, x6, 0x0000054c  # target 0x0000054c
    540: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    544: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    548: 40720233  sub          x4, x4, x7
loc_54c:
    54c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    550: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    554: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    558: 0880006f  jal          x0, 0x000005e0  # target 0x000005e0
loc_55c:
    55c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    560: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    564: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    568: 000a0463  beq          x20, x0, 0x00000570  # target 0x00000570
    56c: ff1ff06f  jal          x0, 0x0000055c  # target 0x0000055c
loc_570:
    570: 0ff0000f  fence        0xf, 0xf
    574: 00008067  jalr         x0, 0(x1)
loc_578:
    578: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    57c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    580: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    584: 000a0463  beq          x20, x0, 0x0000058c  # target 0x0000058c
    588: ff1ff06f  jal          x0, 0x00000578  # target 0x00000578
loc_58c:
    58c: 0ff0000f  fence        0xf, 0xf
    590: 00008067  jalr         x0, 0(x1)
loc_594:
    594: 7d800a93  addi         x21, x0, 2008  # x21 = 0x000007d8
    598: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x000007d8
    59c: 007a7d13  andi         x26, x20, 7
    5a0: ff8a7a13  andi         x20, x20, -8
    5a4: 01af8ab3  add          x21, x31, x26
    5a8: 007afb93  andi         x23, x21, 7
    5ac: 003ada93  srli         x21, x21, 3
    5b0: 00ba9a93  slli         x21, x21, 11
    5b4: 014a8ab3  add          x21, x21, x20
    5b8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005b8
    5bc: 018b0b13  addi         x22, x22, 24  # x22 = 0x000005d0
    5c0: 001b9b93  slli         x23, x23, 1
    5c4: 017b0b33  add          x22, x22, x23
    5c8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    5cc: 00008067  jalr         x0, 0(x1)
    5d0: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    5d4: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5d8: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5dc: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    5e0:           j FW_NCRISC+4   # return to firmware, linked at install
