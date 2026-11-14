# llama3 8b-fp8 decode: o, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x780=e2e_context_decode_token, 0x784=e2e_l0_q, 0x788=input_scale_0, 0x78c=input_scale_1, 0x790=output_scale_0_0, 0x794=output_scale_0_1, 0x798=e2e_x_b, 0x79c=e2e_x_a, 0x11880=e2e_q_compact, 0x11884=e2e_l0_q_row_start, 0x11888=dense_start, 0x1188c=e2e_l0_q_rows, 0x11890=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00022437  lui          x8, 0x00022  # x8 = 0x00022000
      c: 08040413  addi         x8, x8, 128  # x8 = 0x00022080
     10: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00022080
     14: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     18: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 000242b7  lui          x5, 0x00024  # x5 = 0x00024000
     2c: 08028293  addi         x5, x5, 128  # x5 = 0x00024080
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00024080
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     40: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     44: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     48: 000292b7  lui          x5, 0x00029  # x5 = 0x00029000
     4c: 88028293  addi         x5, x5, -1920  # x5 = 0x00028880
     50: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00028880
     54: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     58: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     5c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     60: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     64: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     68: 000292b7  lui          x5, 0x00029  # x5 = 0x00029000
     6c: 08028293  addi         x5, x5, 128  # x5 = 0x00029080
     70: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00029080
     74: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     78: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     7c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     80: 00024237  lui          x4, 0x00024  # x4 = 0x00024000
     84: 08020213  addi         x4, x4, 128  # x4 = 0x00024080
     88: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_8c:
     8c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     90: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     94: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     98: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     9c: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     a0: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     a4: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     a8: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     ac: 02020213  addi         x4, x4, 32
     b0: ff828293  addi         x5, x5, -8
     b4: fc029ce3  bne          x5, x0, 0x0000008c  # target 0x0000008c
     b8: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     bc: 88c28293  addi         x5, x5, -1908  # x5 = 0x0001188c
     c0: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x0001188c
     c4: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     c8: 00020313  addi         x6, x4, 0
loc_cc:
     cc: 0e62fc63  bgeu         x5, x6, 0x000001c4  # target 0x000001c4
     d0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     d4: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     d8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     dc: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_e0:
     e0: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     e4: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     e8: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     ec: 407404b3  sub          x9, x8, x7
     f0: 01049493  slli         x9, x9, 16
     f4: 0104d493  srli         x9, x9, 16
     f8: 00a4f663  bgeu         x9, x10, 0x00000104  # target 0x00000104
     fc: 0ff0000f  fence        0xf, 0xf
    100: fe1ff06f  jal          x0, 0x000000e0  # target 0x000000e0
loc_104:
    104: 0ff0000f  fence        0xf, 0xf
    108: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    10c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    110: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    114: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
    118: 00f2f493  andi         x9, x5, 15
    11c: 00149493  slli         x9, x9, 1
    120: 0102f593  andi         x11, x5, 16
    124: 00559593  slli         x11, x11, 5
    128: 00b4e4b3  or           x9, x9, x11
    12c: 1e02f593  andi         x11, x5, 480
    130: 00b4e4b3  or           x9, x9, x11
    134: 0092d593  srli         x11, x5, 9
    138: 00a59593  slli         x11, x11, 10
    13c: 00b4e4b3  or           x9, x9, x11
    140: 00024537  lui          x10, 0x00024  # x10 = 0x00024000
    144: 08050513  addi         x10, x10, 128  # x10 = 0x00024080
    148: 00950533  add          x10, x10, x9
    14c: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
    150: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    154: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    158: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    15c: 00138393  addi         x7, x7, 1
    160: 01039393  slli         x7, x7, 16
    164: 0103d393  srli         x7, x7, 16
    168: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    16c: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    170: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    174: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    178: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    17c: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    180: 0ff0000f  fence        0xf, 0xf
    184: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    188: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    18c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    190: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    194: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    198: 008383b3  add          x7, x7, x8
    19c: 000234b7  lui          x9, 0x00023  # x9 = 0x00023000
    1a0: 08048493  addi         x9, x9, 128  # x9 = 0x00023080
    1a4: 0093e663  bltu         x7, x9, 0x000001b0  # target 0x000001b0
    1a8: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1ac: 40a383b3  sub          x7, x7, x10
loc_1b0:
    1b0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    1b4: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    1b8: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    1bc: 00128293  addi         x5, x5, 1
    1c0: f0dff06f  jal          x0, 0x000000cc  # target 0x000000cc
loc_1c4:
    1c4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1c8: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1cc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    1d0: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1d4: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    1d8: 00520233  add          x4, x4, x5
    1dc: 00025337  lui          x6, 0x00025  # x6 = 0x00025000
    1e0: 88030313  addi         x6, x6, -1920  # x6 = 0x00024880
    1e4: 00626863  bltu         x4, x6, 0x000001f4  # target 0x000001f4
    1e8: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1ec: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    1f0: 40720233  sub          x4, x4, x7
loc_1f4:
    1f4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1f8: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1fc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    200: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    204: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    208: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    20c: 00120213  addi         x4, x4, 1
    210: 01021213  slli         x4, x4, 16
    214: 01025213  srli         x4, x4, 16
    218: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    21c: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    220: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    224: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    228: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    22c: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    230: 0ff0000f  fence        0xf, 0xf
    234: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    238: 88830313  addi         x6, x6, -1912  # x6 = 0x00011888
    23c: 00032203  lw           x4, 0(x6)  # param dense_start; 0x00011888
    240: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    244: 88c30313  addi         x6, x6, -1908  # x6 = 0x0001188c
    248: 00032283  lw           x5, 0(x6)  # param e2e_l0_q_rows; 0x0001188c
    24c: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    250: 00028393  addi         x7, x5, 0
loc_254:
    254: 04737e63  bgeu         x6, x7, 0x000002b0  # target 0x000002b0
    258: 00620433  add          x8, x4, x6
    25c: 00141493  slli         x9, x8, 1
    260: 00027637  lui          x12, 0x00027  # x12 = 0x00027000
    264: 88060613  addi         x12, x12, -1920  # x12 = 0x00026880
    268: 00c484b3  add          x9, x9, x12
    26c: 0004d583  lhu          x11, 0(x9)  # Address depends on runtime register values
    270: 00f37513  andi         x10, x6, 15
    274: 00151513  slli         x10, x10, 1
    278: 01037613  andi         x12, x6, 16
    27c: 00561613  slli         x12, x12, 5
    280: 00c56533  or           x10, x10, x12
    284: 1e037613  andi         x12, x6, 480
    288: 00c56533  or           x10, x10, x12
    28c: 00935613  srli         x12, x6, 9
    290: 00a61613  slli         x12, x12, 10
    294: 00c56533  or           x10, x10, x12
    298: 00029637  lui          x12, 0x00029  # x12 = 0x00029000
    29c: 88060613  addi         x12, x12, -1920  # x12 = 0x00028880
    2a0: 00c50533  add          x10, x10, x12
    2a4: 00b51023  sh           x11, 0(x10)  # Address depends on runtime register values
    2a8: 00130313  addi         x6, x6, 1
    2ac: fa9ff06f  jal          x0, 0x00000254  # target 0x00000254
loc_2b0:
    2b0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2b4: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    2b8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    2bc: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c0: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    2c4: 00520233  add          x4, x4, x5
    2c8: 00029337  lui          x6, 0x00029  # x6 = 0x00029000
    2cc: 08030313  addi         x6, x6, 128  # x6 = 0x00029080
    2d0: 00626863  bltu         x4, x6, 0x000002e0  # target 0x000002e0
    2d4: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2d8: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    2dc: 40720233  sub          x4, x4, x7
loc_2e0:
    2e0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2e4: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    2e8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    2ec: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2f0: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    2f4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    2f8: 00120213  addi         x4, x4, 1
    2fc: 01021213  slli         x4, x4, 16
    300: 01025213  srli         x4, x4, 16
    304: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    308: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    30c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    310: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    314: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    318: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    31c: 0ff0000f  fence        0xf, 0xf
    320: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    324: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    328: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    32c: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_330:
    330: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    334: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    338: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    33c: 40428333  sub          x6, x5, x4
    340: 01031313  slli         x6, x6, 16
    344: 01035313  srli         x6, x6, 16
    348: 00737663  bgeu         x6, x7, 0x00000354  # target 0x00000354
    34c: 0ff0000f  fence        0xf, 0xf
    350: fe1ff06f  jal          x0, 0x00000330  # target 0x00000330
loc_354:
    354: 0ff0000f  fence        0xf, 0xf
    358: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    35c: 88838393  addi         x7, x7, -1912  # x7 = 0x00011888
    360: 0003a203  lw           x4, 0(x7)  # param dense_start; 0x00011888
    364: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    368: 88c38393  addi         x7, x7, -1908  # x7 = 0x0001188c
    36c: 0003a303  lw           x6, 0(x7)  # param e2e_l0_q_rows; 0x0001188c
    370: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    374: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    378: 0003a283  lw           x5, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c
    37c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    380: 00030413  addi         x8, x6, 0
loc_384:
    384: 0483fa63  bgeu         x7, x8, 0x000003d8  # target 0x000003d8
    388: 007204b3  add          x9, x4, x7
    38c: 00f3f513  andi         x10, x7, 15
    390: 00151513  slli         x10, x10, 1
    394: 0103f693  andi         x13, x7, 16
    398: 00569693  slli         x13, x13, 5
    39c: 00d56533  or           x10, x10, x13
    3a0: 1e03f693  andi         x13, x7, 480
    3a4: 00d56533  or           x10, x10, x13
    3a8: 0093d693  srli         x13, x7, 9
    3ac: 00a69693  slli         x13, x13, 10
    3b0: 00d56533  or           x10, x10, x13
    3b4: 00a28533  add          x10, x5, x10
    3b8: 00055603  lhu          x12, 0(x10)  # Address depends on runtime register values
    3bc: 00149593  slli         x11, x9, 1
    3c0: 0002a6b7  lui          x13, 0x0002a  # x13 = 0x0002a000
    3c4: 88068693  addi         x13, x13, -1920  # x13 = 0x00029880
    3c8: 00d585b3  add          x11, x11, x13
    3cc: 00c59023  sh           x12, 0(x11)  # Address depends on runtime register values
    3d0: 00138393  addi         x7, x7, 1
    3d4: fb1ff06f  jal          x0, 0x00000384  # target 0x00000384
loc_3d8:
    3d8: 1a8000ef  jal          x1, 0x00000580  # target 0x00000580; x1 = 0x000003dc
    3dc: 1c0000ef  jal          x1, 0x0000059c  # target 0x0000059c; x1 = 0x000003e0
    3e0: 00020393  addi         x7, x4, 0
    3e4: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    3e8: 88c48493  addi         x9, x9, -1908  # x9 = 0x0001188c
    3ec: 0004a403  lw           x8, 0(x9)  # param e2e_l0_q_rows; 0x0001188c
    3f0: 00440433  add          x8, x8, x4
loc_3f4:
    3f4: 00a3d493  srli         x9, x7, 10
    3f8: 00048f93  addi         x31, x9, 0
    3fc: 1bc000ef  jal          x1, 0x000005b8  # target 0x000005b8; x1 = 0x00000400
    400: 000a8793  addi         x15, x21, 0
    404: 000b0813  addi         x16, x22, 0
    408: 00139513  slli         x10, x7, 1
    40c: 0002a6b7  lui          x13, 0x0002a  # x13 = 0x0002a000
    410: 88068693  addi         x13, x13, -1920  # x13 = 0x00029880
    414: 00a686b3  add          x13, x13, x10
    418: 7ff57513  andi         x10, x10, 2047
    41c: 00a78733  add          x14, x15, x10
    420: 00f3f593  andi         x11, x7, 15
    424: 01000613  addi         x12, x0, 16  # x12 = 0x00000010
    428: 40b605b3  sub          x11, x12, x11
    42c: 40740633  sub          x12, x8, x7
    430: 00b67463  bgeu         x12, x11, 0x00000438  # target 0x00000438
    434: 00060593  addi         x11, x12, 0
loc_438:
    438: 00b383b3  add          x7, x7, x11
    43c: 00159593  slli         x11, x11, 1
    440: 00068f93  addi         x31, x13, 0
    444: 00070f13  addi         x30, x14, 0
    448: 00080e93  addi         x29, x16, 0
    44c: 00058e13  addi         x28, x11, 0
loc_450:
    450: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    454: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    458: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    45c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    460: 015a6463  bltu         x20, x21, 0x00000468  # target 0x00000468
    464: fedff06f  jal          x0, 0x00000450  # target 0x00000450
loc_468:
    468: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    46c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    470: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    474: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    478: 015a6463  bltu         x20, x21, 0x00000480  # target 0x00000480
    47c: fedff06f  jal          x0, 0x00000468  # target 0x00000468
loc_480:
    480: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    484: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    488: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    48c: 014a1a13  slli         x20, x20, 20
    490: 014a5a13  srli         x20, x20, 20
    494: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_498:
    498: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    49c: 000b0463  beq          x22, x0, 0x000004a4  # target 0x000004a4
    4a0: ff9ff06f  jal          x0, 0x00000498  # target 0x00000498
loc_4a4:
    4a4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    4a8: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    4ac: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    4b0: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    4b4: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    4b8: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    4bc: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    4c0: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    4c4: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    4c8: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    4cc: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    4d0: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    4d4: 03cba023  sw           x28, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write runtime value
    4d8: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    4dc: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    4e0: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    4e4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    4e8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    4ec: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    4f0: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_4f4:
    4f4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    4f8: 000b0463  beq          x22, x0, 0x00000500  # target 0x00000500
    4fc: ff9ff06f  jal          x0, 0x000004f4  # target 0x000004f4
loc_500:
    500: ee83eae3  bltu         x7, x8, 0x000003f4  # target 0x000003f4
    504: 07c000ef  jal          x1, 0x00000580  # target 0x00000580; x1 = 0x00000508
    508: 094000ef  jal          x1, 0x0000059c  # target 0x0000059c; x1 = 0x0000050c
    50c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    510: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    514: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    518: 00120213  addi         x4, x4, 1
    51c: 01021213  slli         x4, x4, 16
    520: 01025213  srli         x4, x4, 16
    524: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    528: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    52c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    530: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    534: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    538: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    53c: 0ff0000f  fence        0xf, 0xf
    540: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    544: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    548: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    54c: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    550: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    554: 00520233  add          x4, x4, x5
    558: 0002a337  lui          x6, 0x0002a  # x6 = 0x0002a000
    55c: 88030313  addi         x6, x6, -1920  # x6 = 0x00029880
    560: 00626863  bltu         x4, x6, 0x00000570  # target 0x00000570
    564: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    568: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    56c: 40720233  sub          x4, x4, x7
loc_570:
    570: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    574: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    578: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    57c: 0c00006f  jal          x0, 0x0000063c  # target 0x0000063c
loc_580:
    580: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    584: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    588: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    58c: 000a0463  beq          x20, x0, 0x00000594  # target 0x00000594
    590: ff1ff06f  jal          x0, 0x00000580  # target 0x00000580
loc_594:
    594: 0ff0000f  fence        0xf, 0xf
    598: 00008067  jalr         x0, 0(x1)
loc_59c:
    59c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    5a0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    5a4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    5a8: 000a0463  beq          x20, x0, 0x000005b0  # target 0x000005b0
    5ac: ff1ff06f  jal          x0, 0x0000059c  # target 0x0000059c
loc_5b0:
    5b0: 0ff0000f  fence        0xf, 0xf
    5b4: 00008067  jalr         x0, 0(x1)
loc_5b8:
    5b8: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    5bc: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x00000798
    5c0: 007a7d13  andi         x26, x20, 7
    5c4: ff8a7a13  andi         x20, x20, -8
    5c8: 01af8ab3  add          x21, x31, x26
    5cc: 007afb93  andi         x23, x21, 7
    5d0: 003ada93  srli         x21, x21, 3
    5d4: 00ba9a93  slli         x21, x21, 11
    5d8: 014a8ab3  add          x21, x21, x20
    5dc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005dc
    5e0: 030b0b13  addi         x22, x22, 48  # x22 = 0x0000060c
    5e4: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    5e8: 890e8e93  addi         x29, x29, -1904  # x29 = 0x00011890
    5ec: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00011890
    5f0: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    5f4: 03cd8db3  mul          x27, x27, x28
    5f8: 01bb0b33  add          x22, x22, x27
    5fc: 001b9b93  slli         x23, x23, 1
    600: 017b0b33  add          x22, x22, x23
    604: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    608: 00008067  jalr         x0, 0(x1)
    60c: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    610: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    614: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    618: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    61c: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    620: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    624: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    628: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    62c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    630: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    634: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    638: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    63c:           j FW_NCRISC+4   # return to firmware, linked at install
