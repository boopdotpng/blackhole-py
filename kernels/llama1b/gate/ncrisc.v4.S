# llama3 1B decode: gate, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (27): 12,2 2,3 5,3 10,3 13,3 3,4 6,4 11,4 1,5 4,5 7,5 12,5 1,6 4,6 7,6 12,6 1,7 4,7 7,7 12,7 1,8 4,8 7,8 12,8 1,9 4,9 7,9
# params: 0x7c0=e2e_x_b_decode_token, 0x7c4=e2e_l0_gate, 0x7c8=e2e_l0_up, 0x7cc=e2e_hidden_dense, 0x7d0=e2e_l0_post_norm, 0x8100=e2e_gate, 0x8104=e2e_l0_gate_row_start, 0x8108=e2e_up, 0x810c=e2e_l0_up_row_start, 0x8110=dense_start
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
      4: 86430313  addi         x6, x6, -1948  # x6 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000923b7  lui          x7, 0x00092  # x7 = 0x00092000
      c: 00732023  sw           x7, 0(x6)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00092000
     10: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
     14: 86830313  addi         x6, x6, -1944  # x6 = 0xffb00868 · riscv_local_mem + 0x868
     18: 00032023  sw           x0, 0(x6)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     20: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     24: 000942b7  lui          x5, 0x00094  # x5 = 0x00094000
     28: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00094000
     2c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     30: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     34: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     38: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     3c: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     40: 000952b7  lui          x5, 0x00095  # x5 = 0x00095000
     44: 80028293  addi         x5, x5, -2048  # x5 = 0x00094800
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00094800
     4c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     50: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     54: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     58: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     5c: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     60: 000972b7  lui          x5, 0x00097  # x5 = 0x00097000
     64: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00097000
     68: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     6c: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     70: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     74: 00094237  lui          x4, 0x00094  # x4 = 0x00094000
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
     a8: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
     ac: 05d00293  addi         x5, x0, 93  # x5 = 0x0000005d
loc_b0:
     b0: 0e527863  bgeu         x4, x5, 0x000001a0  # target 0x000001a0
     b4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     b8: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
     bc: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
     c0: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
loc_c4:
     c4: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
     c8: 02850513  addi         x10, x10, 40  # x10 = 0xffb49028
     cc: 00055383  lhu          x7, 0(x10)  # 0xffb49028
     d0: 40638433  sub          x8, x7, x6
     d4: 01041413  slli         x8, x8, 16
     d8: 01045413  srli         x8, x8, 16
     dc: 00947663  bgeu         x8, x9, 0x000000e8  # target 0x000000e8
     e0: 0ff0000f  fence        0xf, 0xf
     e4: fe1ff06f  jal          x0, 0x000000c4  # target 0x000000c4
loc_e8:
     e8: 0ff0000f  fence        0xf, 0xf
     ec: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     f0: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
     f4: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
     f8: 00035383  lhu          x7, 0(x6)  # Address depends on runtime register values
     fc: 00f27413  andi         x8, x4, 15
    100: 00141413  slli         x8, x8, 1
    104: 01027513  andi         x10, x4, 16
    108: 00551513  slli         x10, x10, 5
    10c: 00a46433  or           x8, x8, x10
    110: 1e027513  andi         x10, x4, 480
    114: 00a46433  or           x8, x8, x10
    118: 00925513  srli         x10, x4, 9
    11c: 00a51513  slli         x10, x10, 10
    120: 00a46433  or           x8, x8, x10
    124: 000944b7  lui          x9, 0x00094  # x9 = 0x00094000
    128: 008484b3  add          x9, x9, x8
    12c: 00749023  sh           x7, 0(x9)  # Address depends on runtime register values
    130: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    134: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
    138: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868
    13c: 00130313  addi         x6, x6, 1
    140: 01031313  slli         x6, x6, 16
    144: 01035313  srli         x6, x6, 16
    148: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    14c: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
    150: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    154: ffb493b7  lui          x7, 0xffb49  # x7 = 0xffb49000
    158: 02038393  addi         x7, x7, 32  # x7 = 0xffb49020
    15c: 0063a023  sw           x6, 0(x7)  # 0xffb49020; write runtime value
    160: 0ff0000f  fence        0xf, 0xf
    164: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    168: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    16c: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    170: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    174: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    178: 00730333  add          x6, x6, x7
    17c: 00093437  lui          x8, 0x00093  # x8 = 0x00093000
    180: 00836663  bltu         x6, x8, 0x0000018c  # target 0x0000018c
    184: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    188: 40930333  sub          x6, x6, x9
loc_18c:
    18c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    190: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    194: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    198: 00120213  addi         x4, x4, 1
    19c: f15ff06f  jal          x0, 0x000000b0  # target 0x000000b0
loc_1a0:
    1a0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1a4: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1a8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    1ac: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1b0: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    1b4: 00520233  add          x4, x4, x5
    1b8: 00095337  lui          x6, 0x00095  # x6 = 0x00095000
    1bc: 80030313  addi         x6, x6, -2048  # x6 = 0x00094800
    1c0: 00626863  bltu         x4, x6, 0x000001d0  # target 0x000001d0
    1c4: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1c8: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    1cc: 40720233  sub          x4, x4, x7
loc_1d0:
    1d0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1d4: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    1d8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    1dc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e0: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    1e4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    1e8: 00120213  addi         x4, x4, 1
    1ec: 01021213  slli         x4, x4, 16
    1f0: 01025213  srli         x4, x4, 16
    1f4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1f8: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    1fc: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    200: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    204: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    208: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    20c: 0ff0000f  fence        0xf, 0xf
    210: 00095237  lui          x4, 0x00095  # x4 = 0x00095000
    214: 80020213  addi         x4, x4, -2048  # x4 = 0x00094800
    218: 20000293  addi         x5, x0, 512  # x5 = 0x00000200
loc_21c:
    21c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
    220: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
    224: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
    228: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
    22c: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
    230: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    234: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    238: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    23c: 02020213  addi         x4, x4, 32
    240: ff828293  addi         x5, x5, -8
    244: fc029ce3  bne          x5, x0, 0x0000021c  # target 0x0000021c
    248: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
    24c: 05d00293  addi         x5, x0, 93  # x5 = 0x0000005d
loc_250:
    250: 0e527a63  bgeu         x4, x5, 0x00000344  # target 0x00000344
    254: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    258: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
    25c: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
    260: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
loc_264:
    264: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
    268: 02850513  addi         x10, x10, 40  # x10 = 0xffb49028
    26c: 00055383  lhu          x7, 0(x10)  # 0xffb49028
    270: 40638433  sub          x8, x7, x6
    274: 01041413  slli         x8, x8, 16
    278: 01045413  srli         x8, x8, 16
    27c: 00947663  bgeu         x8, x9, 0x00000288  # target 0x00000288
    280: 0ff0000f  fence        0xf, 0xf
    284: fe1ff06f  jal          x0, 0x00000264  # target 0x00000264
loc_288:
    288: 0ff0000f  fence        0xf, 0xf
    28c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    290: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    294: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    298: 00035383  lhu          x7, 0(x6)  # Address depends on runtime register values
    29c: 00f27413  andi         x8, x4, 15
    2a0: 00141413  slli         x8, x8, 1
    2a4: 01027513  andi         x10, x4, 16
    2a8: 00551513  slli         x10, x10, 5
    2ac: 00a46433  or           x8, x8, x10
    2b0: 1e027513  andi         x10, x4, 480
    2b4: 00a46433  or           x8, x8, x10
    2b8: 00925513  srli         x10, x4, 9
    2bc: 00a51513  slli         x10, x10, 10
    2c0: 00a46433  or           x8, x8, x10
    2c4: 000954b7  lui          x9, 0x00095  # x9 = 0x00095000
    2c8: 80048493  addi         x9, x9, -2048  # x9 = 0x00094800
    2cc: 008484b3  add          x9, x9, x8
    2d0: 00749023  sh           x7, 0(x9)  # Address depends on runtime register values
    2d4: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    2d8: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
    2dc: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868
    2e0: 00130313  addi         x6, x6, 1
    2e4: 01031313  slli         x6, x6, 16
    2e8: 01035313  srli         x6, x6, 16
    2ec: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    2f0: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
    2f4: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    2f8: ffb493b7  lui          x7, 0xffb49  # x7 = 0xffb49000
    2fc: 02038393  addi         x7, x7, 32  # x7 = 0xffb49020
    300: 0063a023  sw           x6, 0(x7)  # 0xffb49020; write runtime value
    304: 0ff0000f  fence        0xf, 0xf
    308: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    30c: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    310: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    314: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    318: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    31c: 00730333  add          x6, x6, x7
    320: 00093437  lui          x8, 0x00093  # x8 = 0x00093000
    324: 00836663  bltu         x6, x8, 0x00000330  # target 0x00000330
    328: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    32c: 40930333  sub          x6, x6, x9
loc_330:
    330: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    334: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    338: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    33c: 00120213  addi         x4, x4, 1
    340: f11ff06f  jal          x0, 0x00000250  # target 0x00000250
loc_344:
    344: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    348: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    34c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    350: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    354: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    358: 00520233  add          x4, x4, x5
    35c: 00095337  lui          x6, 0x00095  # x6 = 0x00095000
    360: 00626863  bltu         x4, x6, 0x00000370  # target 0x00000370
    364: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    368: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    36c: 40720233  sub          x4, x4, x7
loc_370:
    370: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    374: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    378: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    37c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    380: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    384: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    388: 00120213  addi         x4, x4, 1
    38c: 01021213  slli         x4, x4, 16
    390: 01025213  srli         x4, x4, 16
    394: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    398: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    39c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    3a0: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    3a4: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    3a8: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    3ac: 0ff0000f  fence        0xf, 0xf
    3b0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3b4: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    3b8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    3bc: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_3c0:
    3c0: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    3c4: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    3c8: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    3cc: 40428333  sub          x6, x5, x4
    3d0: 01031313  slli         x6, x6, 16
    3d4: 01035313  srli         x6, x6, 16
    3d8: 00737663  bgeu         x6, x7, 0x000003e4  # target 0x000003e4
    3dc: 0ff0000f  fence        0xf, 0xf
    3e0: fe1ff06f  jal          x0, 0x000003c0  # target 0x000003c0
loc_3e4:
    3e4: 0ff0000f  fence        0xf, 0xf
    3e8: 00008337  lui          x6, 0x00008  # x6 = 0x00008000
    3ec: 11030313  addi         x6, x6, 272  # x6 = 0x00008110
    3f0: 00032203  lw           x4, 0(x6)  # param dense_start; 0x00008110
    3f4: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    3f8: 87c30313  addi         x6, x6, -1924  # x6 = 0xffb0087c · riscv_local_mem + 0x87c
    3fc: 00032283  lw           x5, 0(x6)  # riscv_local_mem + 0x87c · 0xffb0087c
    400: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    404: 05d00393  addi         x7, x0, 93  # x7 = 0x0000005d
loc_408:
    408: 04737a63  bgeu         x6, x7, 0x0000045c  # target 0x0000045c
    40c: 00620433  add          x8, x4, x6
    410: 00f37493  andi         x9, x6, 15
    414: 00149493  slli         x9, x9, 1
    418: 01037613  andi         x12, x6, 16
    41c: 00561613  slli         x12, x12, 5
    420: 00c4e4b3  or           x9, x9, x12
    424: 1e037613  andi         x12, x6, 480
    428: 00c4e4b3  or           x9, x9, x12
    42c: 00935613  srli         x12, x6, 9
    430: 00a61613  slli         x12, x12, 10
    434: 00c4e4b3  or           x9, x9, x12
    438: 009284b3  add          x9, x5, x9
    43c: 0004d583  lhu          x11, 0(x9)  # Address depends on runtime register values
    440: 00141513  slli         x10, x8, 1
    444: 00098637  lui          x12, 0x00098  # x12 = 0x00098000
    448: 80060613  addi         x12, x12, -2048  # x12 = 0x00097800
    44c: 00c50533  add          x10, x10, x12
    450: 00b51023  sh           x11, 0(x10)  # Address depends on runtime register values
    454: 00130313  addi         x6, x6, 1
    458: fb1ff06f  jal          x0, 0x00000408  # target 0x00000408
loc_45c:
    45c: 19c000ef  jal          x1, 0x000005f8  # target 0x000005f8; x1 = 0x00000460
    460: 1b4000ef  jal          x1, 0x00000614  # target 0x00000614; x1 = 0x00000464
    464: 00020313  addi         x6, x4, 0
    468: 05d20393  addi         x7, x4, 93
loc_46c:
    46c: 00a35413  srli         x8, x6, 10
    470: 00040f93  addi         x31, x8, 0
    474: 1bc000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x00000478
    478: 000a8713  addi         x14, x21, 0
    47c: 000b0793  addi         x15, x22, 0
    480: 00131493  slli         x9, x6, 1
    484: 00098637  lui          x12, 0x00098  # x12 = 0x00098000
    488: 80060613  addi         x12, x12, -2048  # x12 = 0x00097800
    48c: 00960633  add          x12, x12, x9
    490: 7ff4f493  andi         x9, x9, 2047
    494: 009706b3  add          x13, x14, x9
    498: 00f37513  andi         x10, x6, 15
    49c: 01000593  addi         x11, x0, 16  # x11 = 0x00000010
    4a0: 40a58533  sub          x10, x11, x10
    4a4: 406385b3  sub          x11, x7, x6
    4a8: 00a5f463  bgeu         x11, x10, 0x000004b0  # target 0x000004b0
    4ac: 00058513  addi         x10, x11, 0
loc_4b0:
    4b0: 00a30333  add          x6, x6, x10
    4b4: 00151513  slli         x10, x10, 1
    4b8: 00060f93  addi         x31, x12, 0
    4bc: 00068f13  addi         x30, x13, 0
    4c0: 00078e93  addi         x29, x15, 0
    4c4: 00050e13  addi         x28, x10, 0
loc_4c8:
    4c8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4cc: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    4d0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    4d4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    4d8: 015a6463  bltu         x20, x21, 0x000004e0  # target 0x000004e0
    4dc: fedff06f  jal          x0, 0x000004c8  # target 0x000004c8
loc_4e0:
    4e0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4e4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    4e8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    4ec: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    4f0: 015a6463  bltu         x20, x21, 0x000004f8  # target 0x000004f8
    4f4: fedff06f  jal          x0, 0x000004e0  # target 0x000004e0
loc_4f8:
    4f8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    4fc: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    500: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    504: 014a1a13  slli         x20, x20, 20
    508: 014a5a13  srli         x20, x20, 20
    50c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_510:
    510: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    514: 000b0463  beq          x22, x0, 0x0000051c  # target 0x0000051c
    518: ff9ff06f  jal          x0, 0x00000510  # target 0x00000510
loc_51c:
    51c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    520: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    524: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    528: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    52c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    530: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    534: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    538: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    53c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    540: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    544: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    548: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    54c: 03cba023  sw           x28, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write runtime value
    550: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    554: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    558: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    55c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    560: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    564: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    568: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_56c:
    56c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    570: 000b0463  beq          x22, x0, 0x00000578  # target 0x00000578
    574: ff9ff06f  jal          x0, 0x0000056c  # target 0x0000056c
loc_578:
    578: ee736ae3  bltu         x6, x7, 0x0000046c  # target 0x0000046c
    57c: 07c000ef  jal          x1, 0x000005f8  # target 0x000005f8; x1 = 0x00000580
    580: 094000ef  jal          x1, 0x00000614  # target 0x00000614; x1 = 0x00000584
    584: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    588: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    58c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    590: 00120213  addi         x4, x4, 1
    594: 01021213  slli         x4, x4, 16
    598: 01025213  srli         x4, x4, 16
    59c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5a0: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    5a4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    5a8: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    5ac: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    5b0: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    5b4: 0ff0000f  fence        0xf, 0xf
    5b8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5bc: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    5c0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    5c4: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5c8: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    5cc: 00520233  add          x4, x4, x5
    5d0: 00098337  lui          x6, 0x00098  # x6 = 0x00098000
    5d4: 80030313  addi         x6, x6, -2048  # x6 = 0x00097800
    5d8: 00626863  bltu         x4, x6, 0x000005e8  # target 0x000005e8
    5dc: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5e0: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    5e4: 40720233  sub          x4, x4, x7
loc_5e8:
    5e8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5ec: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    5f0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    5f4: 0880006f  jal          x0, 0x0000067c  # target 0x0000067c
loc_5f8:
    5f8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    5fc: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    600: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    604: 000a0463  beq          x20, x0, 0x0000060c  # target 0x0000060c
    608: ff1ff06f  jal          x0, 0x000005f8  # target 0x000005f8
loc_60c:
    60c: 0ff0000f  fence        0xf, 0xf
    610: 00008067  jalr         x0, 0(x1)
loc_614:
    614: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    618: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    61c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    620: 000a0463  beq          x20, x0, 0x00000628  # target 0x00000628
    624: ff1ff06f  jal          x0, 0x00000614  # target 0x00000614
loc_628:
    628: 0ff0000f  fence        0xf, 0xf
    62c: 00008067  jalr         x0, 0(x1)
loc_630:
    630: 7cc00a93  addi         x21, x0, 1996  # x21 = 0x000007cc
    634: 000aaa03  lw           x20, 0(x21)  # param e2e_hidden_dense; 0x000007cc
    638: 007a7d13  andi         x26, x20, 7
    63c: ff8a7a13  andi         x20, x20, -8
    640: 01af8ab3  add          x21, x31, x26
    644: 007afb93  andi         x23, x21, 7
    648: 003ada93  srli         x21, x21, 3
    64c: 00ba9a93  slli         x21, x21, 11
    650: 014a8ab3  add          x21, x21, x20
    654: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000654
    658: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000066c
    65c: 001b9b93  slli         x23, x23, 1
    660: 017b0b33  add          x22, x22, x23
    664: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    668: 00008067  jalr         x0, 0(x1)
    66c: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    670: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    674: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    678: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    67c:           j FW_NCRISC+4   # return to firmware, linked at install
