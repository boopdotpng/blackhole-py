# llama3 8b-bf16 decode: attention_merge, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (8): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9
# params: 0x780=attention_partial_tiles, 0x784=e2e_context, 0x788=kv_blocks, 0xea40=merge_head
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
      4: 87830313  addi         x6, x6, -1928  # x6 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
      c: 00732023  sw           x7, 0(x6)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000f000
     10: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
     14: 87c30313  addi         x6, x6, -1924  # x6 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00032023  sw           x0, 0(x6)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 78800413  addi         x8, x0, 1928  # x8 = 0x00000788
     20: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000788
     24: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     28: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     2c: 0063fa63  bgeu         x7, x6, 0x00000040  # target 0x00000040
     30: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     34: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     38: 0063f463  bgeu         x7, x6, 0x00000040  # target 0x00000040
     3c: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_40:
     40: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     44: a4030313  addi         x6, x6, -1472  # x6 = 0x0000ea40
     48: 00032203  lw           x4, 0(x6)  # param merge_head; 0x0000ea40
     4c: 04800313  addi         x6, x0, 72  # x6 = 0x00000048
     50: 02620233  mul          x4, x4, x6
     54: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     58: 87c58593  addi         x11, x11, -1924  # x11 = 0xffb0087c · riscv_local_mem + 0x87c
     5c: 0005a303  lw           x6, 0(x11)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_60:
     60: ffb485b7  lui          x11, 0xffb48  # x11 = 0xffb48000
     64: 02058593  addi         x11, x11, 32  # x11 = 0xffb48020
     68: 0005d383  lhu          x7, 0(x11)  # 0xffb48020
     6c: 40730433  sub          x8, x6, x7
     70: 01041413  slli         x8, x8, 16
     74: 01045413  srli         x8, x8, 16
     78: 00c00493  addi         x9, x0, 12  # x9 = 0x0000000c
     7c: 408484b3  sub          x9, x9, x8
     80: 00600513  addi         x10, x0, 6  # x10 = 0x00000006
     84: 00a4f663  bgeu         x9, x10, 0x00000090  # target 0x00000090
     88: 0ff0000f  fence        0xf, 0xf
     8c: fd5ff06f  jal          x0, 0x00000060  # target 0x00000060
loc_90:
     90: 0ff0000f  fence        0xf, 0xf
     94: 3d4000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x00000098
     98: 3ec000ef  jal          x1, 0x00000484  # target 0x00000484; x1 = 0x0000009c
     9c: 00020313  addi         x6, x4, 0
     a0: 00030f93  addi         x31, x6, 0
     a4: 3fc000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x000000a8
     a8: 000a8393  addi         x7, x21, 0
     ac: 000b0413  addi         x8, x22, 0
     b0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     b4: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
     b8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
     bc: 00038f93  addi         x31, x7, 0
     c0: 00040f13  addi         x30, x8, 0
     c4: 00048e93  addi         x29, x9, 0
     c8: 424000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000000cc
     cc: 00120313  addi         x6, x4, 1
     d0: 00030f93  addi         x31, x6, 0
     d4: 3cc000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x000000d8
     d8: 000a8393  addi         x7, x21, 0
     dc: 000b0413  addi         x8, x22, 0
     e0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     e4: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
     e8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
     ec: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     f0: 00a484b3  add          x9, x9, x10
     f4: 00038f93  addi         x31, x7, 0
     f8: 00040f13  addi         x30, x8, 0
     fc: 00048e93  addi         x29, x9, 0
    100: 3ec000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000104
    104: 00220313  addi         x6, x4, 2
    108: 00030f93  addi         x31, x6, 0
    10c: 394000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x00000110
    110: 000a8393  addi         x7, x21, 0
    114: 000b0413  addi         x8, x22, 0
    118: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    11c: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    120: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    124: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    128: 00a484b3  add          x9, x9, x10
    12c: 00038f93  addi         x31, x7, 0
    130: 00040f13  addi         x30, x8, 0
    134: 00048e93  addi         x29, x9, 0
    138: 3b4000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x0000013c
    13c: 00320313  addi         x6, x4, 3
    140: 00030f93  addi         x31, x6, 0
    144: 35c000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x00000148
    148: 000a8393  addi         x7, x21, 0
    14c: 000b0413  addi         x8, x22, 0
    150: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    154: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    158: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    15c: 00003537  lui          x10, 0x00003  # x10 = 0x00003000
    160: 00a484b3  add          x9, x9, x10
    164: 00038f93  addi         x31, x7, 0
    168: 00040f13  addi         x30, x8, 0
    16c: 00048e93  addi         x29, x9, 0
    170: 37c000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000174
    174: 00420313  addi         x6, x4, 4
    178: 00030f93  addi         x31, x6, 0
    17c: 324000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x00000180
    180: 000a8393  addi         x7, x21, 0
    184: 000b0413  addi         x8, x22, 0
    188: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    18c: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    190: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    194: 00004537  lui          x10, 0x00004  # x10 = 0x00004000
    198: 00a484b3  add          x9, x9, x10
    19c: 00038f93  addi         x31, x7, 0
    1a0: 00040f13  addi         x30, x8, 0
    1a4: 00048e93  addi         x29, x9, 0
    1a8: 344000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000001ac
    1ac: 00520313  addi         x6, x4, 5
    1b0: 00030f93  addi         x31, x6, 0
    1b4: 2ec000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x000001b8
    1b8: 000a8393  addi         x7, x21, 0
    1bc: 000b0413  addi         x8, x22, 0
    1c0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1c4: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    1c8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    1cc: 00005537  lui          x10, 0x00005  # x10 = 0x00005000
    1d0: 00a484b3  add          x9, x9, x10
    1d4: 00038f93  addi         x31, x7, 0
    1d8: 00040f13  addi         x30, x8, 0
    1dc: 00048e93  addi         x29, x9, 0
    1e0: 30c000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000001e4
    1e4: 2a0000ef  jal          x1, 0x00000484  # target 0x00000484; x1 = 0x000001e8
    1e8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1ec: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    1f0: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    1f4: 000063b7  lui          x7, 0x00006  # x7 = 0x00006000
    1f8: 00730333  add          x6, x6, x7
    1fc: 0001b437  lui          x8, 0x0001b  # x8 = 0x0001b000
    200: 00836663  bltu         x6, x8, 0x0000020c  # target 0x0000020c
    204: 0000c4b7  lui          x9, 0x0000c  # x9 = 0x0000c000
    208: 40930333  sub          x6, x6, x9
loc_20c:
    20c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    210: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    214: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    218: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    21c: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    220: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c
    224: 00630313  addi         x6, x6, 6
    228: 01031313  slli         x6, x6, 16
    22c: 01035313  srli         x6, x6, 16
    230: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    234: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    238: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    23c: ffb483b7  lui          x7, 0xffb48  # x7 = 0xffb48000
    240: 02838393  addi         x7, x7, 40  # x7 = 0xffb48028
    244: 0063a023  sw           x6, 0(x7)  # 0xffb48028; write runtime value
    248: 0ff0000f  fence        0xf, 0xf
    24c: 00620213  addi         x4, x4, 6
    250: fff28293  addi         x5, x5, -1
    254: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    258: 00028393  addi         x7, x5, 0
loc_25c:
    25c: 20737463  bgeu         x6, x7, 0x00000464  # target 0x00000464
    260: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    264: 87c68693  addi         x13, x13, -1924  # x13 = 0xffb0087c · riscv_local_mem + 0x87c
    268: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_26c:
    26c: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
    270: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    274: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    278: 40940533  sub          x10, x8, x9
    27c: 01051513  slli         x10, x10, 16
    280: 01055513  srli         x10, x10, 16
    284: 00c00593  addi         x11, x0, 12  # x11 = 0x0000000c
    288: 40a585b3  sub          x11, x11, x10
    28c: 00600613  addi         x12, x0, 6  # x12 = 0x00000006
    290: 00c5f663  bgeu         x11, x12, 0x0000029c  # target 0x0000029c
    294: 0ff0000f  fence        0xf, 0xf
    298: fd5ff06f  jal          x0, 0x0000026c  # target 0x0000026c
loc_29c:
    29c: 0ff0000f  fence        0xf, 0xf
    2a0: 1c8000ef  jal          x1, 0x00000468  # target 0x00000468; x1 = 0x000002a4
    2a4: 1e0000ef  jal          x1, 0x00000484  # target 0x00000484; x1 = 0x000002a8
    2a8: 00420413  addi         x8, x4, 4
    2ac: 00040f93  addi         x31, x8, 0
    2b0: 1f0000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x000002b4
    2b4: 000a8493  addi         x9, x21, 0
    2b8: 000b0513  addi         x10, x22, 0
    2bc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    2c0: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    2c4: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    2c8: 00048f93  addi         x31, x9, 0
    2cc: 00050f13  addi         x30, x10, 0
    2d0: 00058e93  addi         x29, x11, 0
    2d4: 218000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000002d8
    2d8: 00520413  addi         x8, x4, 5
    2dc: 00040f93  addi         x31, x8, 0
    2e0: 1c0000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x000002e4
    2e4: 000a8493  addi         x9, x21, 0
    2e8: 000b0513  addi         x10, x22, 0
    2ec: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    2f0: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    2f4: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    2f8: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2fc: 00c585b3  add          x11, x11, x12
    300: 00048f93  addi         x31, x9, 0
    304: 00050f13  addi         x30, x10, 0
    308: 00058e93  addi         x29, x11, 0
    30c: 1e0000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000310
    310: 00020413  addi         x8, x4, 0
    314: 00040f93  addi         x31, x8, 0
    318: 188000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x0000031c
    31c: 000a8493  addi         x9, x21, 0
    320: 000b0513  addi         x10, x22, 0
    324: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    328: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    32c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    330: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    334: 00c585b3  add          x11, x11, x12
    338: 00048f93  addi         x31, x9, 0
    33c: 00050f13  addi         x30, x10, 0
    340: 00058e93  addi         x29, x11, 0
    344: 1a8000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000348
    348: 00120413  addi         x8, x4, 1
    34c: 00040f93  addi         x31, x8, 0
    350: 150000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x00000354
    354: 000a8493  addi         x9, x21, 0
    358: 000b0513  addi         x10, x22, 0
    35c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    360: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    364: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    368: 00003637  lui          x12, 0x00003  # x12 = 0x00003000
    36c: 00c585b3  add          x11, x11, x12
    370: 00048f93  addi         x31, x9, 0
    374: 00050f13  addi         x30, x10, 0
    378: 00058e93  addi         x29, x11, 0
    37c: 170000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x00000380
    380: 00220413  addi         x8, x4, 2
    384: 00040f93  addi         x31, x8, 0
    388: 118000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x0000038c
    38c: 000a8493  addi         x9, x21, 0
    390: 000b0513  addi         x10, x22, 0
    394: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    398: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    39c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    3a0: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    3a4: 00c585b3  add          x11, x11, x12
    3a8: 00048f93  addi         x31, x9, 0
    3ac: 00050f13  addi         x30, x10, 0
    3b0: 00058e93  addi         x29, x11, 0
    3b4: 138000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000003b8
    3b8: 00320413  addi         x8, x4, 3
    3bc: 00040f93  addi         x31, x8, 0
    3c0: 0e0000ef  jal          x1, 0x000004a0  # target 0x000004a0; x1 = 0x000003c4
    3c4: 000a8493  addi         x9, x21, 0
    3c8: 000b0513  addi         x10, x22, 0
    3cc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    3d0: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    3d4: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    3d8: 00005637  lui          x12, 0x00005  # x12 = 0x00005000
    3dc: 00c585b3  add          x11, x11, x12
    3e0: 00048f93  addi         x31, x9, 0
    3e4: 00050f13  addi         x30, x10, 0
    3e8: 00058e93  addi         x29, x11, 0
    3ec: 100000ef  jal          x1, 0x000004ec  # target 0x000004ec; x1 = 0x000003f0
    3f0: 094000ef  jal          x1, 0x00000484  # target 0x00000484; x1 = 0x000003f4
    3f4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    3f8: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    3fc: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    400: 000064b7  lui          x9, 0x00006  # x9 = 0x00006000
    404: 00940433  add          x8, x8, x9
    408: 0001b537  lui          x10, 0x0001b  # x10 = 0x0001b000
    40c: 00a46663  bltu         x8, x10, 0x00000418  # target 0x00000418
    410: 0000c5b7  lui          x11, 0x0000c  # x11 = 0x0000c000
    414: 40b40433  sub          x8, x8, x11
loc_418:
    418: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    41c: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    420: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    424: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    428: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    42c: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
    430: 00640413  addi         x8, x8, 6
    434: 01041413  slli         x8, x8, 16
    438: 01045413  srli         x8, x8, 16
    43c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    440: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    444: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    448: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    44c: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    450: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    454: 0ff0000f  fence        0xf, 0xf
    458: 00620213  addi         x4, x4, 6
    45c: 00130313  addi         x6, x6, 1
    460: dfdff06f  jal          x0, 0x0000025c  # target 0x0000025c
loc_464:
    464: 1280006f  jal          x0, 0x0000058c  # target 0x0000058c
loc_468:
    468: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    46c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    470: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    474: 000a0463  beq          x20, x0, 0x0000047c  # target 0x0000047c
    478: ff1ff06f  jal          x0, 0x00000468  # target 0x00000468
loc_47c:
    47c: 0ff0000f  fence        0xf, 0xf
    480: 00008067  jalr         x0, 0(x1)
loc_484:
    484: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    488: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    48c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    490: 000a0463  beq          x20, x0, 0x00000498  # target 0x00000498
    494: ff1ff06f  jal          x0, 0x00000484  # target 0x00000484
loc_498:
    498: 0ff0000f  fence        0xf, 0xf
    49c: 00008067  jalr         x0, 0(x1)
loc_4a0:
    4a0: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    4a4: 000aaa03  lw           x20, 0(x21)  # param attention_partial_tiles; 0x00000780
    4a8: 007a7d13  andi         x26, x20, 7
    4ac: ff8a7a13  andi         x20, x20, -8
    4b0: 01af8ab3  add          x21, x31, x26
    4b4: 007afb93  andi         x23, x21, 7
    4b8: 003ada93  srli         x21, x21, 3
    4bc: 00ca9a93  slli         x21, x21, 12
    4c0: 014a8ab3  add          x21, x21, x20
    4c4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004c4
    4c8: 018b0b13  addi         x22, x22, 24  # x22 = 0x000004dc
    4cc: 001b9b93  slli         x23, x23, 1
    4d0: 017b0b33  add          x22, x22, x23
    4d4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4d8: 00008067  jalr         x0, 0(x1)
    4dc: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    4e0: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e4: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    4e8: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_4ec:
    4ec: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4f0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    4f4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    4f8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    4fc: 015a6463  bltu         x20, x21, 0x00000504  # target 0x00000504
    500: fedff06f  jal          x0, 0x000004ec  # target 0x000004ec
loc_504:
    504: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    508: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    50c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    510: 014a1a13  slli         x20, x20, 20
    514: 014a5a13  srli         x20, x20, 20
    518: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_51c:
    51c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    520: 000b0463  beq          x22, x0, 0x00000528  # target 0x00000528
    524: ff9ff06f  jal          x0, 0x0000051c  # target 0x0000051c
loc_528:
    528: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    52c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    530: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    534: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    538: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    53c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    540: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    544: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    548: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    54c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    550: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    554: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    558: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    55c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    560: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    564: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    568: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    56c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    570: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    574: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    578: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_57c:
    57c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    580: 000b0463  beq          x22, x0, 0x00000588  # target 0x00000588
    584: ff9ff06f  jal          x0, 0x0000057c  # target 0x0000057c
loc_588:
    588: 00008067  jalr         x0, 0(x1)
    58c:           j FW_BRISC+4   # return to firmware, linked at install
