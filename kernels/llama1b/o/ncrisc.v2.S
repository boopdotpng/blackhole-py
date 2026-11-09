# llama3 1B decode: o, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (8): 3,2 6,2 11,2 1,3 4,3 7,3 12,3 2,4
# params: 0x7c0=e2e_context_decode_token, 0x7c4=e2e_l0_q, 0x7c8=e2e_x_b, 0x7cc=e2e_x_a, 0x8040=e2e_q_compact, 0x8044=e2e_l0_q_row_start, 0x8048=dense_start
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
     40: 000962b7  lui          x5, 0x00096  # x5 = 0x00096000
     44: 80028293  addi         x5, x5, -2048  # x5 = 0x00095800
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00095800
     4c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     50: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     54: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     58: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     5c: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     60: 000962b7  lui          x5, 0x00096  # x5 = 0x00096000
     64: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00096000
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
     ac: 01800293  addi         x5, x0, 24  # x5 = 0x00000018
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
    200: ffb4a2b7  lui          x5, 0xffb4a  # x5 = 0xffb4a000
    204: 02828293  addi         x5, x5, 40  # x5 = 0xffb4a028
    208: 0042a023  sw           x4, 0(x5)  # 0xffb4a028; write runtime value
    20c: 0ff0000f  fence        0xf, 0xf
    210: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    214: 04828293  addi         x5, x5, 72  # x5 = 0x00008048
    218: 0002a203  lw           x4, 0(x5)  # param dense_start; 0x00008048
    21c: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
    220: 01800313  addi         x6, x0, 24  # x6 = 0x00000018
loc_224:
    224: 0462fe63  bgeu         x5, x6, 0x00000280  # target 0x00000280
    228: 005203b3  add          x7, x4, x5
    22c: 00139413  slli         x8, x7, 1
    230: 000955b7  lui          x11, 0x00095  # x11 = 0x00095000
    234: 80058593  addi         x11, x11, -2048  # x11 = 0x00094800
    238: 00b40433  add          x8, x8, x11
    23c: 00045503  lhu          x10, 0(x8)  # Address depends on runtime register values
    240: 00f2f493  andi         x9, x5, 15
    244: 00149493  slli         x9, x9, 1
    248: 0102f593  andi         x11, x5, 16
    24c: 00559593  slli         x11, x11, 5
    250: 00b4e4b3  or           x9, x9, x11
    254: 1e02f593  andi         x11, x5, 480
    258: 00b4e4b3  or           x9, x9, x11
    25c: 0092d593  srli         x11, x5, 9
    260: 00a59593  slli         x11, x11, 10
    264: 00b4e4b3  or           x9, x9, x11
    268: 000965b7  lui          x11, 0x00096  # x11 = 0x00096000
    26c: 80058593  addi         x11, x11, -2048  # x11 = 0x00095800
    270: 00b484b3  add          x9, x9, x11
    274: 00a49023  sh           x10, 0(x9)  # Address depends on runtime register values
    278: 00128293  addi         x5, x5, 1
    27c: fa9ff06f  jal          x0, 0x00000224  # target 0x00000224
loc_280:
    280: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    284: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    288: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    28c: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    290: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    294: 00520233  add          x4, x4, x5
    298: 00096337  lui          x6, 0x00096  # x6 = 0x00096000
    29c: 00626863  bltu         x4, x6, 0x000002ac  # target 0x000002ac
    2a0: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2a4: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    2a8: 40720233  sub          x4, x4, x7
loc_2ac:
    2ac: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2b0: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    2b4: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    2b8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2bc: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    2c0: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    2c4: 00120213  addi         x4, x4, 1
    2c8: 01021213  slli         x4, x4, 16
    2cc: 01025213  srli         x4, x4, 16
    2d0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2d4: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    2d8: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    2dc: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    2e0: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    2e4: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    2e8: 0ff0000f  fence        0xf, 0xf
    2ec: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2f0: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    2f4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    2f8: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_2fc:
    2fc: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    300: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    304: 00045283  lhu          x5, 0(x8)  # 0xffb4c028
    308: 40428333  sub          x6, x5, x4
    30c: 01031313  slli         x6, x6, 16
    310: 01035313  srli         x6, x6, 16
    314: 00737663  bgeu         x6, x7, 0x00000320  # target 0x00000320
    318: 0ff0000f  fence        0xf, 0xf
    31c: fe1ff06f  jal          x0, 0x000002fc  # target 0x000002fc
loc_320:
    320: 0ff0000f  fence        0xf, 0xf
    324: 00008337  lui          x6, 0x00008  # x6 = 0x00008000
    328: 04830313  addi         x6, x6, 72  # x6 = 0x00008048
    32c: 00032203  lw           x4, 0(x6)  # param dense_start; 0x00008048
    330: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
    334: 87c30313  addi         x6, x6, -1924  # x6 = 0xffb0087c · riscv_local_mem + 0x87c
    338: 00032283  lw           x5, 0(x6)  # riscv_local_mem + 0x87c · 0xffb0087c
    33c: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    340: 01800393  addi         x7, x0, 24  # x7 = 0x00000018
loc_344:
    344: 04737a63  bgeu         x6, x7, 0x00000398  # target 0x00000398
    348: 00620433  add          x8, x4, x6
    34c: 00f37493  andi         x9, x6, 15
    350: 00149493  slli         x9, x9, 1
    354: 01037613  andi         x12, x6, 16
    358: 00561613  slli         x12, x12, 5
    35c: 00c4e4b3  or           x9, x9, x12
    360: 1e037613  andi         x12, x6, 480
    364: 00c4e4b3  or           x9, x9, x12
    368: 00935613  srli         x12, x6, 9
    36c: 00a61613  slli         x12, x12, 10
    370: 00c4e4b3  or           x9, x9, x12
    374: 009284b3  add          x9, x5, x9
    378: 0004d583  lhu          x11, 0(x9)  # Address depends on runtime register values
    37c: 00141513  slli         x10, x8, 1
    380: 00097637  lui          x12, 0x00097  # x12 = 0x00097000
    384: 80060613  addi         x12, x12, -2048  # x12 = 0x00096800
    388: 00c50533  add          x10, x10, x12
    38c: 00b51023  sh           x11, 0(x10)  # Address depends on runtime register values
    390: 00130313  addi         x6, x6, 1
    394: fb1ff06f  jal          x0, 0x00000344  # target 0x00000344
loc_398:
    398: 19c000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x0000039c
    39c: 1b4000ef  jal          x1, 0x00000550  # target 0x00000550; x1 = 0x000003a0
    3a0: 00020313  addi         x6, x4, 0
    3a4: 01820393  addi         x7, x4, 24
loc_3a8:
    3a8: 00a35413  srli         x8, x6, 10
    3ac: 00040f93  addi         x31, x8, 0
    3b0: 1bc000ef  jal          x1, 0x0000056c  # target 0x0000056c; x1 = 0x000003b4
    3b4: 000a8713  addi         x14, x21, 0
    3b8: 000b0793  addi         x15, x22, 0
    3bc: 00131493  slli         x9, x6, 1
    3c0: 00097637  lui          x12, 0x00097  # x12 = 0x00097000
    3c4: 80060613  addi         x12, x12, -2048  # x12 = 0x00096800
    3c8: 00960633  add          x12, x12, x9
    3cc: 7ff4f493  andi         x9, x9, 2047
    3d0: 009706b3  add          x13, x14, x9
    3d4: 00f37513  andi         x10, x6, 15
    3d8: 01000593  addi         x11, x0, 16  # x11 = 0x00000010
    3dc: 40a58533  sub          x10, x11, x10
    3e0: 406385b3  sub          x11, x7, x6
    3e4: 00a5f463  bgeu         x11, x10, 0x000003ec  # target 0x000003ec
    3e8: 00058513  addi         x10, x11, 0
loc_3ec:
    3ec: 00a30333  add          x6, x6, x10
    3f0: 00151513  slli         x10, x10, 1
    3f4: 00060f93  addi         x31, x12, 0
    3f8: 00068f13  addi         x30, x13, 0
    3fc: 00078e93  addi         x29, x15, 0
    400: 00050e13  addi         x28, x10, 0
loc_404:
    404: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    408: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    40c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    410: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    414: 015a6463  bltu         x20, x21, 0x0000041c  # target 0x0000041c
    418: fedff06f  jal          x0, 0x00000404  # target 0x00000404
loc_41c:
    41c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    420: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    424: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    428: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    42c: 015a6463  bltu         x20, x21, 0x00000434  # target 0x00000434
    430: fedff06f  jal          x0, 0x0000041c  # target 0x0000041c
loc_434:
    434: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    438: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    43c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    440: 014a1a13  slli         x20, x20, 20
    444: 014a5a13  srli         x20, x20, 20
    448: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_44c:
    44c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    450: 000b0463  beq          x22, x0, 0x00000458  # target 0x00000458
    454: ff9ff06f  jal          x0, 0x0000044c  # target 0x0000044c
loc_458:
    458: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    45c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    460: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    464: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    468: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    46c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    470: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    474: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    478: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    47c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    480: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    484: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    488: 03cba023  sw           x28, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write runtime value
    48c: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    490: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    494: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    498: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    49c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    4a0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    4a4: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_4a8:
    4a8: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    4ac: 000b0463  beq          x22, x0, 0x000004b4  # target 0x000004b4
    4b0: ff9ff06f  jal          x0, 0x000004a8  # target 0x000004a8
loc_4b4:
    4b4: ee736ae3  bltu         x6, x7, 0x000003a8  # target 0x000003a8
    4b8: 07c000ef  jal          x1, 0x00000534  # target 0x00000534; x1 = 0x000004bc
    4bc: 094000ef  jal          x1, 0x00000550  # target 0x00000550; x1 = 0x000004c0
    4c0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4c4: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    4c8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    4cc: 00120213  addi         x4, x4, 1
    4d0: 01021213  slli         x4, x4, 16
    4d4: 01025213  srli         x4, x4, 16
    4d8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4dc: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    4e0: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    4e4: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    4e8: 02028293  addi         x5, x5, 32  # x5 = 0xffb4c020
    4ec: 0042a023  sw           x4, 0(x5)  # 0xffb4c020; write runtime value
    4f0: 0ff0000f  fence        0xf, 0xf
    4f4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4f8: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    4fc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    500: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    504: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    508: 00520233  add          x4, x4, x5
    50c: 00097337  lui          x6, 0x00097  # x6 = 0x00097000
    510: 80030313  addi         x6, x6, -2048  # x6 = 0x00096800
    514: 00626863  bltu         x4, x6, 0x00000524  # target 0x00000524
    518: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    51c: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    520: 40720233  sub          x4, x4, x7
loc_524:
    524: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    528: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    52c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    530: 0880006f  jal          x0, 0x000005b8  # target 0x000005b8
loc_534:
    534: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    538: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    53c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    540: 000a0463  beq          x20, x0, 0x00000548  # target 0x00000548
    544: ff1ff06f  jal          x0, 0x00000534  # target 0x00000534
loc_548:
    548: 0ff0000f  fence        0xf, 0xf
    54c: 00008067  jalr         x0, 0(x1)
loc_550:
    550: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    554: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    558: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    55c: 000a0463  beq          x20, x0, 0x00000564  # target 0x00000564
    560: ff1ff06f  jal          x0, 0x00000550  # target 0x00000550
loc_564:
    564: 0ff0000f  fence        0xf, 0xf
    568: 00008067  jalr         x0, 0(x1)
loc_56c:
    56c: 7c800a93  addi         x21, x0, 1992  # x21 = 0x000007c8
    570: 000aaa03  lw           x20, 0(x21)  # param e2e_x_b; 0x000007c8
    574: 007a7d13  andi         x26, x20, 7
    578: ff8a7a13  andi         x20, x20, -8
    57c: 01af8ab3  add          x21, x31, x26
    580: 007afb93  andi         x23, x21, 7
    584: 003ada93  srli         x21, x21, 3
    588: 00ba9a93  slli         x21, x21, 11
    58c: 014a8ab3  add          x21, x21, x20
    590: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000590
    594: 018b0b13  addi         x22, x22, 24  # x22 = 0x000005a8
    598: 001b9b93  slli         x23, x23, 1
    59c: 017b0b33  add          x22, x22, x23
    5a0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    5a4: 00008067  jalr         x0, 0(x1)
    5a8: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    5ac: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    5b0: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    5b4: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    5b8:           j FW_NCRISC+4   # return to firmware, linked at install
