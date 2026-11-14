# llama3 8b-bf16 decode: qkv, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_l0_q, 0x788=e2e_q, 0x78c=e2e_l0_k, 0x790=e2e_k, 0x794=e2e_l0_v, 0x798=e2e_v, 0x79c=e2e_l0_input_norm, 0x118c0=e2e_l0_q_row_start, 0x118c4=e2e_l0_k_row_start, 0x118c8=e2e_l0_v_row_start, 0x118cc=e2e_l0_q_rows, 0x118d0=e2e_l0_k_rows, 0x118d4=e2e_l0_v_rows, 0x118d8=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000192b7  lui          x5, 0x00019  # x5 = 0x00019000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00019000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     20: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
     24: 00012537  lui          x10, 0x00012  # x10 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     28: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00012000
     2c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     30: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
     34: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     38: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     3c: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     40: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_44:
     44: ffb4b4b7  lui          x9, 0xffb4b  # x9 = 0xffb4b000
     48: 02048493  addi         x9, x9, 32  # x9 = 0xffb4b020
     4c: 0004d283  lhu          x5, 0(x9)  # 0xffb4b020
     50: 40520333  sub          x6, x4, x5
     54: 01031313  slli         x6, x6, 16
     58: 01035313  srli         x6, x6, 16
     5c: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
     60: 406383b3  sub          x7, x7, x6
     64: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
     68: 0083f663  bgeu         x7, x8, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: fd5ff06f  jal          x0, 0x00000044  # target 0x00000044
loc_74:
     74: 0ff0000f  fence        0xf, 0xf
     78: 4fc000ef  jal          x1, 0x00000574  # target 0x00000574; x1 = 0x0000007c
     7c: 514000ef  jal          x1, 0x00000590  # target 0x00000590; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 528000ef  jal          x1, 0x000005ac  # target 0x000005ac; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00019eb7  lui          x29, 0x00019  # x29 = 0x00019000
     9c: 594000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 508000ef  jal          x1, 0x000005ac  # target 0x000005ac; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00019800
     c0: 570000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x000000c4
     c4: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     c8: 4e4000ef  jal          x1, 0x000005ac  # target 0x000005ac; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 0001aeb7  lui          x29, 0x0001a  # x29 = 0x0001a000
     e0: 550000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x000000e4
     e4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     e8: 4c4000ef  jal          x1, 0x000005ac  # target 0x000005ac; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001a800
    104: 52c000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x00000108
    108: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    10c: 5c8000ef  jal          x1, 0x000006d4  # target 0x000006d4; x1 = 0x00000110
    110: 000a8213  addi         x4, x21, 0
    114: 000b0293  addi         x5, x22, 0
    118: 00020f93  addi         x31, x4, 0
    11c: 00028f13  addi         x30, x5, 0
    120: 0001beb7  lui          x29, 0x0001b  # x29 = 0x0001b000
    124: 50c000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x00000128
    128: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    12c: 5a8000ef  jal          x1, 0x000006d4  # target 0x000006d4; x1 = 0x00000130
    130: 000a8213  addi         x4, x21, 0
    134: 000b0293  addi         x5, x22, 0
    138: 00020f93  addi         x31, x4, 0
    13c: 00028f13  addi         x30, x5, 0
    140: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    144: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001b800
    148: 4e8000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x0000014c
    14c: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    150: 584000ef  jal          x1, 0x000006d4  # target 0x000006d4; x1 = 0x00000154
    154: 000a8213  addi         x4, x21, 0
    158: 000b0293  addi         x5, x22, 0
    15c: 00020f93  addi         x31, x4, 0
    160: 00028f13  addi         x30, x5, 0
    164: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    168: 4c8000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x0000016c
    16c: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    170: 564000ef  jal          x1, 0x000006d4  # target 0x000006d4; x1 = 0x00000174
    174: 000a8213  addi         x4, x21, 0
    178: 000b0293  addi         x5, x22, 0
    17c: 00020f93  addi         x31, x4, 0
    180: 00028f13  addi         x30, x5, 0
    184: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    188: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001c800
    18c: 4a4000ef  jal          x1, 0x00000630  # target 0x00000630; x1 = 0x00000190
    190: 400000ef  jal          x1, 0x00000590  # target 0x00000590; x1 = 0x00000194
    194: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    198: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    19c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    1a0: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    1a4: 00520233  add          x4, x4, x5
    1a8: 0001d337  lui          x6, 0x0001d  # x6 = 0x0001d000
    1ac: 00626663  bltu         x4, x6, 0x000001b8  # target 0x000001b8
    1b0: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    1b4: 40720233  sub          x4, x4, x7
loc_1b8:
    1b8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    1bc: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    1c0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1c4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1c8: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1cc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    1d0: 00820213  addi         x4, x4, 8
    1d4: 01021213  slli         x4, x4, 16
    1d8: 01025213  srli         x4, x4, 16
    1dc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    1e0: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    1e4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1e8: ffb4b2b7  lui          x5, 0xffb4b  # x5 = 0xffb4b000
    1ec: 02828293  addi         x5, x5, 40  # x5 = 0xffb4b028
    1f0: 0042a023  sw           x4, 0(x5)  # 0xffb4b028; write runtime value
    1f4: 0ff0000f  fence        0xf, 0xf
    1f8: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    1fc: 8cc28293  addi         x5, x5, -1844  # x5 = 0x000118cc
    200: 0002a203  lw           x4, 0(x5)  # param e2e_l0_q_rows; 0x000118cc
    204: 78400393  addi         x7, x0, 1924  # x7 = 0x00000784
    208: 0003a283  lw           x5, 0(x7)  # param e2e_l0_q; 0x00000784
    20c: ff82f293  andi         x5, x5, -8
    210: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    214: 8c048493  addi         x9, x9, -1856  # x9 = 0x000118c0
    218: 0004a383  lw           x7, 0(x9)  # param e2e_l0_q_row_start; 0x000118c0
    21c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    220: 028383b3  mul          x7, x7, x8
    224: 0073f313  andi         x6, x7, 7
    228: 0033d393  srli         x7, x7, 3
    22c: 00b39393  slli         x7, x7, 11
    230: 007282b3  add          x5, x5, x7
    234: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    238: 00020413  addi         x8, x4, 0
loc_23c:
    23c: 0e83f263  bgeu         x7, x8, 0x00000320  # target 0x00000320
    240: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    244: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    248: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_24c:
    24c: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    250: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    254: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    258: 40a485b3  sub          x11, x9, x10
    25c: 01059593  slli         x11, x11, 16
    260: 0105d593  srli         x11, x11, 16
    264: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    268: 40b60633  sub          x12, x12, x11
    26c: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    270: 00d67663  bgeu         x12, x13, 0x0000027c  # target 0x0000027c
    274: 0ff0000f  fence        0xf, 0xf
    278: fd5ff06f  jal          x0, 0x0000024c  # target 0x0000024c
loc_27c:
    27c: 0ff0000f  fence        0xf, 0xf
    280: 2f4000ef  jal          x1, 0x00000574  # target 0x00000574; x1 = 0x00000284
    284: 30c000ef  jal          x1, 0x00000590  # target 0x00000590; x1 = 0x00000288
    288: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    28c: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    290: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    294: 00028f93  addi         x31, x5, 0
    298: 00030f13  addi         x30, x6, 0
    29c: 00048e93  addi         x29, x9, 0
    2a0: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    2a4: 4b4000ef  jal          x1, 0x00000758  # target 0x00000758; x1 = 0x000002a8
    2a8: 000f8293  addi         x5, x31, 0
    2ac: 000f0313  addi         x6, x30, 0
    2b0: 2e0000ef  jal          x1, 0x00000590  # target 0x00000590; x1 = 0x000002b4
    2b4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2b8: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2bc: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    2c0: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    2c4: 00a484b3  add          x9, x9, x10
    2c8: 000165b7  lui          x11, 0x00016  # x11 = 0x00016000
    2cc: 00b4e663  bltu         x9, x11, 0x000002d8  # target 0x000002d8
    2d0: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    2d4: 40c484b3  sub          x9, x9, x12
loc_2d8:
    2d8: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    2dc: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    2e0: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    2e4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    2e8: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    2ec: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    2f0: 00448493  addi         x9, x9, 4
    2f4: 01049493  slli         x9, x9, 16
    2f8: 0104d493  srli         x9, x9, 16
    2fc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    300: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    304: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    308: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    30c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    310: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    314: 0ff0000f  fence        0xf, 0xf
    318: 00138393  addi         x7, x7, 1
    31c: f21ff06f  jal          x0, 0x0000023c  # target 0x0000023c
loc_320:
    320: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    324: 8d028293  addi         x5, x5, -1840  # x5 = 0x000118d0
    328: 0002a203  lw           x4, 0(x5)  # param e2e_l0_k_rows; 0x000118d0
    32c: 78c00393  addi         x7, x0, 1932  # x7 = 0x0000078c
    330: 0003a283  lw           x5, 0(x7)  # param e2e_l0_k; 0x0000078c
    334: ff82f293  andi         x5, x5, -8
    338: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    33c: 8c448493  addi         x9, x9, -1852  # x9 = 0x000118c4
    340: 0004a383  lw           x7, 0(x9)  # param e2e_l0_k_row_start; 0x000118c4
    344: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    348: 028383b3  mul          x7, x7, x8
    34c: 0073f313  andi         x6, x7, 7
    350: 0033d393  srli         x7, x7, 3
    354: 00b39393  slli         x7, x7, 11
    358: 007282b3  add          x5, x5, x7
    35c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    360: 00020413  addi         x8, x4, 0
loc_364:
    364: 0e83f263  bgeu         x7, x8, 0x00000448  # target 0x00000448
    368: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    36c: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    370: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_374:
    374: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    378: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    37c: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    380: 40a485b3  sub          x11, x9, x10
    384: 01059593  slli         x11, x11, 16
    388: 0105d593  srli         x11, x11, 16
    38c: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    390: 40b60633  sub          x12, x12, x11
    394: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    398: 00d67663  bgeu         x12, x13, 0x000003a4  # target 0x000003a4
    39c: 0ff0000f  fence        0xf, 0xf
    3a0: fd5ff06f  jal          x0, 0x00000374  # target 0x00000374
loc_3a4:
    3a4: 0ff0000f  fence        0xf, 0xf
    3a8: 1cc000ef  jal          x1, 0x00000574  # target 0x00000574; x1 = 0x000003ac
    3ac: 1e4000ef  jal          x1, 0x00000590  # target 0x00000590; x1 = 0x000003b0
    3b0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    3b4: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    3b8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    3bc: 00028f93  addi         x31, x5, 0
    3c0: 00030f13  addi         x30, x6, 0
    3c4: 00048e93  addi         x29, x9, 0
    3c8: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    3cc: 38c000ef  jal          x1, 0x00000758  # target 0x00000758; x1 = 0x000003d0
    3d0: 000f8293  addi         x5, x31, 0
    3d4: 000f0313  addi         x6, x30, 0
    3d8: 1b8000ef  jal          x1, 0x00000590  # target 0x00000590; x1 = 0x000003dc
    3dc: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    3e0: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    3e4: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    3e8: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    3ec: 00a484b3  add          x9, x9, x10
    3f0: 000165b7  lui          x11, 0x00016  # x11 = 0x00016000
    3f4: 00b4e663  bltu         x9, x11, 0x00000400  # target 0x00000400
    3f8: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    3fc: 40c484b3  sub          x9, x9, x12
loc_400:
    400: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    404: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    408: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    40c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    410: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    414: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    418: 00448493  addi         x9, x9, 4
    41c: 01049493  slli         x9, x9, 16
    420: 0104d493  srli         x9, x9, 16
    424: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    428: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    42c: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    430: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    434: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    438: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    43c: 0ff0000f  fence        0xf, 0xf
    440: 00138393  addi         x7, x7, 1
    444: f21ff06f  jal          x0, 0x00000364  # target 0x00000364
loc_448:
    448: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    44c: 8d428293  addi         x5, x5, -1836  # x5 = 0x000118d4
    450: 0002a203  lw           x4, 0(x5)  # param e2e_l0_v_rows; 0x000118d4
    454: 79400393  addi         x7, x0, 1940  # x7 = 0x00000794
    458: 0003a283  lw           x5, 0(x7)  # param e2e_l0_v; 0x00000794
    45c: ff82f293  andi         x5, x5, -8
    460: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    464: 8c848493  addi         x9, x9, -1848  # x9 = 0x000118c8
    468: 0004a383  lw           x7, 0(x9)  # param e2e_l0_v_row_start; 0x000118c8
    46c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    470: 028383b3  mul          x7, x7, x8
    474: 0073f313  andi         x6, x7, 7
    478: 0033d393  srli         x7, x7, 3
    47c: 00b39393  slli         x7, x7, 11
    480: 007282b3  add          x5, x5, x7
    484: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    488: 00020413  addi         x8, x4, 0
loc_48c:
    48c: 0e83f263  bgeu         x7, x8, 0x00000570  # target 0x00000570
    490: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    494: 88470713  addi         x14, x14, -1916  # x14 = 0xffb00884 · riscv_local_mem + 0x884
    498: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x884 · 0xffb00884
loc_49c:
    49c: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    4a0: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    4a4: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    4a8: 40a485b3  sub          x11, x9, x10
    4ac: 01059593  slli         x11, x11, 16
    4b0: 0105d593  srli         x11, x11, 16
    4b4: 00800613  addi         x12, x0, 8  # x12 = 0x00000008
    4b8: 40b60633  sub          x12, x12, x11
    4bc: 00400693  addi         x13, x0, 4  # x13 = 0x00000004
    4c0: 00d67663  bgeu         x12, x13, 0x000004cc  # target 0x000004cc
    4c4: 0ff0000f  fence        0xf, 0xf
    4c8: fd5ff06f  jal          x0, 0x0000049c  # target 0x0000049c
loc_4cc:
    4cc: 0ff0000f  fence        0xf, 0xf
    4d0: 0a4000ef  jal          x1, 0x00000574  # target 0x00000574; x1 = 0x000004d4
    4d4: 0bc000ef  jal          x1, 0x00000590  # target 0x00000590; x1 = 0x000004d8
    4d8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    4dc: 88050513  addi         x10, x10, -1920  # x10 = 0xffb00880 · riscv_local_mem + 0x880
    4e0: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x880 · 0xffb00880
    4e4: 00028f93  addi         x31, x5, 0
    4e8: 00030f13  addi         x30, x6, 0
    4ec: 00048e93  addi         x29, x9, 0
    4f0: 00400e13  addi         x28, x0, 4  # x28 = 0x00000004
    4f4: 264000ef  jal          x1, 0x00000758  # target 0x00000758; x1 = 0x000004f8
    4f8: 000f8293  addi         x5, x31, 0
    4fc: 000f0313  addi         x6, x30, 0
    500: 090000ef  jal          x1, 0x00000590  # target 0x00000590; x1 = 0x00000504
    504: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    508: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    50c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880
    510: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    514: 00a484b3  add          x9, x9, x10
    518: 000165b7  lui          x11, 0x00016  # x11 = 0x00016000
    51c: 00b4e663  bltu         x9, x11, 0x00000528  # target 0x00000528
    520: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    524: 40c484b3  sub          x9, x9, x12
loc_528:
    528: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    52c: 88068693  addi         x13, x13, -1920  # x13 = 0xffb00880 · riscv_local_mem + 0x880
    530: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    534: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    538: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    53c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884
    540: 00448493  addi         x9, x9, 4
    544: 01049493  slli         x9, x9, 16
    548: 0104d493  srli         x9, x9, 16
    54c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    550: 88450513  addi         x10, x10, -1916  # x10 = 0xffb00884 · riscv_local_mem + 0x884
    554: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    558: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    55c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    560: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    564: 0ff0000f  fence        0xf, 0xf
    568: 00138393  addi         x7, x7, 1
    56c: f21ff06f  jal          x0, 0x0000048c  # target 0x0000048c
loc_570:
    570: 3100006f  jal          x0, 0x00000880  # target 0x00000880
loc_574:
    574: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    578: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    57c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    580: 000a0463  beq          x20, x0, 0x00000588  # target 0x00000588
    584: ff1ff06f  jal          x0, 0x00000574  # target 0x00000574
loc_588:
    588: 0ff0000f  fence        0xf, 0xf
    58c: 00008067  jalr         x0, 0(x1)
loc_590:
    590: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    594: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    598: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    59c: 000a0463  beq          x20, x0, 0x000005a4  # target 0x000005a4
    5a0: ff1ff06f  jal          x0, 0x00000590  # target 0x00000590
loc_5a4:
    5a4: 0ff0000f  fence        0xf, 0xf
    5a8: 00008067  jalr         x0, 0(x1)
loc_5ac:
    5ac: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    5b0: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x00000780
    5b4: 007a7d13  andi         x26, x20, 7
    5b8: ff8a7a13  andi         x20, x20, -8
    5bc: 01af8ab3  add          x21, x31, x26
    5c0: 007afb93  andi         x23, x21, 7
    5c4: 003ada93  srli         x21, x21, 3
    5c8: 00ba9a93  slli         x21, x21, 11
    5cc: 014a8ab3  add          x21, x21, x20
    5d0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000005d0
    5d4: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000600
    5d8: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    5dc: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    5e0: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    5e4: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    5e8: 03cd8db3  mul          x27, x27, x28
    5ec: 01bb0b33  add          x22, x22, x27
    5f0: 001b9b93  slli         x23, x23, 1
    5f4: 017b0b33  add          x22, x22, x23
    5f8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    5fc: 00008067  jalr         x0, 0(x1)
    600: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    604: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    608: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    60c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    610: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    614: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    618: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    61c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    620: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    624: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    628: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    62c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_630:
    630: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    634: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    638: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    63c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    640: 015a6463  bltu         x20, x21, 0x00000648  # target 0x00000648
    644: fedff06f  jal          x0, 0x00000630  # target 0x00000630
loc_648:
    648: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    64c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    650: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    654: 014a1a13  slli         x20, x20, 20
    658: 014a5a13  srli         x20, x20, 20
    65c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_660:
    660: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    664: 000b0463  beq          x22, x0, 0x0000066c  # target 0x0000066c
    668: ff9ff06f  jal          x0, 0x00000660  # target 0x00000660
loc_66c:
    66c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    670: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    674: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    678: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    67c: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    680: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    684: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    688: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    68c: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    690: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    694: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    698: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    69c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6a0: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    6a4: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    6a8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    6ac: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    6b0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    6b4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    6b8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    6bc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    6c0: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_6c4:
    6c4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    6c8: 000b0463  beq          x22, x0, 0x000006d0  # target 0x000006d0
    6cc: ff9ff06f  jal          x0, 0x000006c4  # target 0x000006c4
loc_6d0:
    6d0: 00008067  jalr         x0, 0(x1)
loc_6d4:
    6d4: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    6d8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_input_norm; 0x0000079c
    6dc: 007a7d13  andi         x26, x20, 7
    6e0: ff8a7a13  andi         x20, x20, -8
    6e4: 01af8ab3  add          x21, x31, x26
    6e8: 007afb93  andi         x23, x21, 7
    6ec: 003ada93  srli         x21, x21, 3
    6f0: 00ba9a93  slli         x21, x21, 11
    6f4: 014a8ab3  add          x21, x21, x20
    6f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000006f8
    6fc: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000728
    700: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    704: 8d8e8e93  addi         x29, x29, -1832  # x29 = 0x000118d8
    708: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000118d8
    70c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    710: 03cd8db3  mul          x27, x27, x28
    714: 01bb0b33  add          x22, x22, x27
    718: 001b9b93  slli         x23, x23, 1
    71c: 017b0b33  add          x22, x22, x23
    720: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    724: 00008067  jalr         x0, 0(x1)
    728: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    72c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    730: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    734: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    738: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    73c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    740: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    744: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    748: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    74c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    750: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    754: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_758:
    758: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000758
    75c: 0f8a0a13  addi         x20, x20, 248  # x20 = 0x00000850
    760: 00012cb7  lui          x25, 0x00012  # x25 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    764: 8d8c8c93  addi         x25, x25, -1832  # x25 = 0x000118d8
    768: 000cab83  lw           x23, 0(x25)  # param dram_port; 0x000118d8
    76c: 01000c13  addi         x24, x0, 16  # x24 = 0x00000010
    770: 038b8bb3  mul          x23, x23, x24
    774: 017a0a33  add          x20, x20, x23
loc_778:
    778: 001f1a93  slli         x21, x30, 1
    77c: 014a8ab3  add          x21, x21, x20
    780: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_784:
    784: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    788: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    78c: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    790: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    794: 018be463  bltu         x23, x24, 0x0000079c  # target 0x0000079c
    798: fedff06f  jal          x0, 0x00000784  # target 0x00000784
loc_79c:
    79c: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    7a0: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    7a4: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    7a8: 014b9b93  slli         x23, x23, 20
    7ac: 014bdb93  srli         x23, x23, 20
    7b0: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_7b4:
    7b4: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    7b8: 000c8463  beq          x25, x0, 0x000007c0  # target 0x000007c0
    7bc: ff9ff06f  jal          x0, 0x000007b4  # target 0x000007b4
loc_7c0:
    7c0: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    7c4: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    7c8: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    7cc: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    7d0: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    7d4: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    7d8: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    7dc: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    7e0: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    7e4: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    7e8: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    7ec: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    7f0: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7f4: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    7f8: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    7fc: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    800: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    804: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    808: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    80c: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    810: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    814: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_818:
    818: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    81c: 000c8463  beq          x25, x0, 0x00000824  # target 0x00000824
    820: ff9ff06f  jal          x0, 0x00000818  # target 0x00000818
loc_824:
    824: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    828: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    82c: 016e8eb3  add          x29, x29, x22
    830: 001f0f13  addi         x30, x30, 1
    834: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    838: 015f1663  bne          x30, x21, 0x00000844  # target 0x00000844
    83c: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    840: 016f8fb3  add          x31, x31, x22
loc_844:
    844: fffe0e13  addi         x28, x28, -1
    848: f20e18e3  bne          x28, x0, 0x00000778  # target 0x00000778
    84c: 00008067  jalr         x0, 0(x1)
    850: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    854: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    858: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    85c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    860: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    864: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    868: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    86c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    870: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    874: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    878: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    87c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
    880:           j FW_BRISC+4   # return to firmware, linked at install
