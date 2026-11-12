# llama3 8b-fp8 decode: attention_merge, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (8): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9
# params: 0x780=attention_partial_tiles, 0x784=e2e_context, 0x788=kv_blocks, 0xea40=merge_head
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
      4: 87830313  addi         x6, x6, -1928  # x6 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
      c: 08038393  addi         x7, x7, 128  # x7 = 0x0000f080
     10: 00732023  sw           x7, 0(x6)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000f080
     14: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
     18: 87c30313  addi         x6, x6, -1924  # x6 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00032023  sw           x0, 0(x6)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: 78800413  addi         x8, x0, 1928  # x8 = 0x00000788
     24: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000788
     28: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     2c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     30: 0063fa63  bgeu         x7, x6, 0x00000044  # target 0x00000044
     34: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     38: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     3c: 0063f463  bgeu         x7, x6, 0x00000044  # target 0x00000044
     40: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_44:
     44: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     48: a4030313  addi         x6, x6, -1472  # x6 = 0x0000ea40
     4c: 00032203  lw           x4, 0(x6)  # param merge_head; 0x0000ea40
     50: 04800313  addi         x6, x0, 72  # x6 = 0x00000048
     54: 02620233  mul          x4, x4, x6
     58: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     5c: 87c58593  addi         x11, x11, -1924  # x11 = 0xffb0087c · riscv_local_mem + 0x87c
     60: 0005a303  lw           x6, 0(x11)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_64:
     64: ffb485b7  lui          x11, 0xffb48  # x11 = 0xffb48000
     68: 02058593  addi         x11, x11, 32  # x11 = 0xffb48020
     6c: 0005d383  lhu          x7, 0(x11)  # 0xffb48020
     70: 40730433  sub          x8, x6, x7
     74: 01041413  slli         x8, x8, 16
     78: 01045413  srli         x8, x8, 16
     7c: 00c00493  addi         x9, x0, 12  # x9 = 0x0000000c
     80: 408484b3  sub          x9, x9, x8
     84: 00600513  addi         x10, x0, 6  # x10 = 0x00000006
     88: 00a4f663  bgeu         x9, x10, 0x00000094  # target 0x00000094
     8c: 0ff0000f  fence        0xf, 0xf
     90: fd5ff06f  jal          x0, 0x00000064  # target 0x00000064
loc_94:
     94: 0ff0000f  fence        0xf, 0xf
     98: 3dc000ef  jal          x1, 0x00000474  # target 0x00000474; x1 = 0x0000009c
     9c: 3f4000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x000000a0
     a0: 00020313  addi         x6, x4, 0
     a4: 00030f93  addi         x31, x6, 0
     a8: 404000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x000000ac
     ac: 000a8393  addi         x7, x21, 0
     b0: 000b0413  addi         x8, x22, 0
     b4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     b8: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
     bc: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
     c0: 00038f93  addi         x31, x7, 0
     c4: 00040f13  addi         x30, x8, 0
     c8: 00048e93  addi         x29, x9, 0
     cc: 42c000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x000000d0
     d0: 00120313  addi         x6, x4, 1
     d4: 00030f93  addi         x31, x6, 0
     d8: 3d4000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x000000dc
     dc: 000a8393  addi         x7, x21, 0
     e0: 000b0413  addi         x8, x22, 0
     e4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     e8: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
     ec: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
     f0: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     f4: 00a484b3  add          x9, x9, x10
     f8: 00038f93  addi         x31, x7, 0
     fc: 00040f13  addi         x30, x8, 0
    100: 00048e93  addi         x29, x9, 0
    104: 3f4000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x00000108
    108: 00220313  addi         x6, x4, 2
    10c: 00030f93  addi         x31, x6, 0
    110: 39c000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x00000114
    114: 000a8393  addi         x7, x21, 0
    118: 000b0413  addi         x8, x22, 0
    11c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    120: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    124: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    128: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    12c: 00a484b3  add          x9, x9, x10
    130: 00038f93  addi         x31, x7, 0
    134: 00040f13  addi         x30, x8, 0
    138: 00048e93  addi         x29, x9, 0
    13c: 3bc000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x00000140
    140: 00320313  addi         x6, x4, 3
    144: 00030f93  addi         x31, x6, 0
    148: 364000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x0000014c
    14c: 000a8393  addi         x7, x21, 0
    150: 000b0413  addi         x8, x22, 0
    154: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    158: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    15c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    160: 00003537  lui          x10, 0x00003  # x10 = 0x00003000
    164: 00a484b3  add          x9, x9, x10
    168: 00038f93  addi         x31, x7, 0
    16c: 00040f13  addi         x30, x8, 0
    170: 00048e93  addi         x29, x9, 0
    174: 384000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x00000178
    178: 00420313  addi         x6, x4, 4
    17c: 00030f93  addi         x31, x6, 0
    180: 32c000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x00000184
    184: 000a8393  addi         x7, x21, 0
    188: 000b0413  addi         x8, x22, 0
    18c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    190: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    194: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    198: 00004537  lui          x10, 0x00004  # x10 = 0x00004000
    19c: 00a484b3  add          x9, x9, x10
    1a0: 00038f93  addi         x31, x7, 0
    1a4: 00040f13  addi         x30, x8, 0
    1a8: 00048e93  addi         x29, x9, 0
    1ac: 34c000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x000001b0
    1b0: 00520313  addi         x6, x4, 5
    1b4: 00030f93  addi         x31, x6, 0
    1b8: 2f4000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x000001bc
    1bc: 000a8393  addi         x7, x21, 0
    1c0: 000b0413  addi         x8, x22, 0
    1c4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1c8: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    1cc: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    1d0: 00005537  lui          x10, 0x00005  # x10 = 0x00005000
    1d4: 00a484b3  add          x9, x9, x10
    1d8: 00038f93  addi         x31, x7, 0
    1dc: 00040f13  addi         x30, x8, 0
    1e0: 00048e93  addi         x29, x9, 0
    1e4: 314000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x000001e8
    1e8: 2a8000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x000001ec
    1ec: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1f0: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    1f4: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    1f8: 000063b7  lui          x7, 0x00006  # x7 = 0x00006000
    1fc: 00730333  add          x6, x6, x7
    200: 0001b437  lui          x8, 0x0001b  # x8 = 0x0001b000
    204: 08040413  addi         x8, x8, 128  # x8 = 0x0001b080
    208: 00836663  bltu         x6, x8, 0x00000214  # target 0x00000214
    20c: 0000c4b7  lui          x9, 0x0000c  # x9 = 0x0000c000
    210: 40930333  sub          x6, x6, x9
loc_214:
    214: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    218: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    21c: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    220: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    224: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    228: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c
    22c: 00630313  addi         x6, x6, 6
    230: 01031313  slli         x6, x6, 16
    234: 01035313  srli         x6, x6, 16
    238: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    23c: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    240: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    244: ffb483b7  lui          x7, 0xffb48  # x7 = 0xffb48000
    248: 02838393  addi         x7, x7, 40  # x7 = 0xffb48028
    24c: 0063a023  sw           x6, 0(x7)  # 0xffb48028; write runtime value
    250: 0ff0000f  fence        0xf, 0xf
    254: 00620213  addi         x4, x4, 6
    258: fff28293  addi         x5, x5, -1
    25c: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    260: 00028393  addi         x7, x5, 0
loc_264:
    264: 20737663  bgeu         x6, x7, 0x00000470  # target 0x00000470
    268: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    26c: 87c68693  addi         x13, x13, -1924  # x13 = 0xffb0087c · riscv_local_mem + 0x87c
    270: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_274:
    274: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
    278: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    27c: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    280: 40940533  sub          x10, x8, x9
    284: 01051513  slli         x10, x10, 16
    288: 01055513  srli         x10, x10, 16
    28c: 00c00593  addi         x11, x0, 12  # x11 = 0x0000000c
    290: 40a585b3  sub          x11, x11, x10
    294: 00600613  addi         x12, x0, 6  # x12 = 0x00000006
    298: 00c5f663  bgeu         x11, x12, 0x000002a4  # target 0x000002a4
    29c: 0ff0000f  fence        0xf, 0xf
    2a0: fd5ff06f  jal          x0, 0x00000274  # target 0x00000274
loc_2a4:
    2a4: 0ff0000f  fence        0xf, 0xf
    2a8: 1cc000ef  jal          x1, 0x00000474  # target 0x00000474; x1 = 0x000002ac
    2ac: 1e4000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x000002b0
    2b0: 00420413  addi         x8, x4, 4
    2b4: 00040f93  addi         x31, x8, 0
    2b8: 1f4000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x000002bc
    2bc: 000a8493  addi         x9, x21, 0
    2c0: 000b0513  addi         x10, x22, 0
    2c4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    2c8: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    2cc: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    2d0: 00048f93  addi         x31, x9, 0
    2d4: 00050f13  addi         x30, x10, 0
    2d8: 00058e93  addi         x29, x11, 0
    2dc: 21c000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x000002e0
    2e0: 00520413  addi         x8, x4, 5
    2e4: 00040f93  addi         x31, x8, 0
    2e8: 1c4000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x000002ec
    2ec: 000a8493  addi         x9, x21, 0
    2f0: 000b0513  addi         x10, x22, 0
    2f4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    2f8: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    2fc: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    300: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    304: 00c585b3  add          x11, x11, x12
    308: 00048f93  addi         x31, x9, 0
    30c: 00050f13  addi         x30, x10, 0
    310: 00058e93  addi         x29, x11, 0
    314: 1e4000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x00000318
    318: 00020413  addi         x8, x4, 0
    31c: 00040f93  addi         x31, x8, 0
    320: 18c000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x00000324
    324: 000a8493  addi         x9, x21, 0
    328: 000b0513  addi         x10, x22, 0
    32c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    330: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    334: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    338: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    33c: 00c585b3  add          x11, x11, x12
    340: 00048f93  addi         x31, x9, 0
    344: 00050f13  addi         x30, x10, 0
    348: 00058e93  addi         x29, x11, 0
    34c: 1ac000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x00000350
    350: 00120413  addi         x8, x4, 1
    354: 00040f93  addi         x31, x8, 0
    358: 154000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x0000035c
    35c: 000a8493  addi         x9, x21, 0
    360: 000b0513  addi         x10, x22, 0
    364: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    368: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    36c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    370: 00003637  lui          x12, 0x00003  # x12 = 0x00003000
    374: 00c585b3  add          x11, x11, x12
    378: 00048f93  addi         x31, x9, 0
    37c: 00050f13  addi         x30, x10, 0
    380: 00058e93  addi         x29, x11, 0
    384: 174000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x00000388
    388: 00220413  addi         x8, x4, 2
    38c: 00040f93  addi         x31, x8, 0
    390: 11c000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x00000394
    394: 000a8493  addi         x9, x21, 0
    398: 000b0513  addi         x10, x22, 0
    39c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    3a0: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    3a4: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    3a8: 00004637  lui          x12, 0x00004  # x12 = 0x00004000
    3ac: 00c585b3  add          x11, x11, x12
    3b0: 00048f93  addi         x31, x9, 0
    3b4: 00050f13  addi         x30, x10, 0
    3b8: 00058e93  addi         x29, x11, 0
    3bc: 13c000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x000003c0
    3c0: 00320413  addi         x8, x4, 3
    3c4: 00040f93  addi         x31, x8, 0
    3c8: 0e4000ef  jal          x1, 0x000004ac  # target 0x000004ac; x1 = 0x000003cc
    3cc: 000a8493  addi         x9, x21, 0
    3d0: 000b0513  addi         x10, x22, 0
    3d4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    3d8: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    3dc: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    3e0: 00005637  lui          x12, 0x00005  # x12 = 0x00005000
    3e4: 00c585b3  add          x11, x11, x12
    3e8: 00048f93  addi         x31, x9, 0
    3ec: 00050f13  addi         x30, x10, 0
    3f0: 00058e93  addi         x29, x11, 0
    3f4: 104000ef  jal          x1, 0x000004f8  # target 0x000004f8; x1 = 0x000003f8
    3f8: 098000ef  jal          x1, 0x00000490  # target 0x00000490; x1 = 0x000003fc
    3fc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    400: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    404: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    408: 000064b7  lui          x9, 0x00006  # x9 = 0x00006000
    40c: 00940433  add          x8, x8, x9
    410: 0001b537  lui          x10, 0x0001b  # x10 = 0x0001b000
    414: 08050513  addi         x10, x10, 128  # x10 = 0x0001b080
    418: 00a46663  bltu         x8, x10, 0x00000424  # target 0x00000424
    41c: 0000c5b7  lui          x11, 0x0000c  # x11 = 0x0000c000
    420: 40b40433  sub          x8, x8, x11
loc_424:
    424: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    428: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    42c: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    430: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    434: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    438: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
    43c: 00640413  addi         x8, x8, 6
    440: 01041413  slli         x8, x8, 16
    444: 01045413  srli         x8, x8, 16
    448: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    44c: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    450: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    454: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    458: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    45c: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    460: 0ff0000f  fence        0xf, 0xf
    464: 00620213  addi         x4, x4, 6
    468: 00130313  addi         x6, x6, 1
    46c: df9ff06f  jal          x0, 0x00000264  # target 0x00000264
loc_470:
    470: 1280006f  jal          x0, 0x00000598  # target 0x00000598
loc_474:
    474: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    478: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    47c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    480: 000a0463  beq          x20, x0, 0x00000488  # target 0x00000488
    484: ff1ff06f  jal          x0, 0x00000474  # target 0x00000474
loc_488:
    488: 0ff0000f  fence        0xf, 0xf
    48c: 00008067  jalr         x0, 0(x1)
loc_490:
    490: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    494: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    498: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    49c: 000a0463  beq          x20, x0, 0x000004a4  # target 0x000004a4
    4a0: ff1ff06f  jal          x0, 0x00000490  # target 0x00000490
loc_4a4:
    4a4: 0ff0000f  fence        0xf, 0xf
    4a8: 00008067  jalr         x0, 0(x1)
loc_4ac:
    4ac: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    4b0: 000aaa03  lw           x20, 0(x21)  # param attention_partial_tiles; 0x00000780
    4b4: 007a7d13  andi         x26, x20, 7
    4b8: ff8a7a13  andi         x20, x20, -8
    4bc: 01af8ab3  add          x21, x31, x26
    4c0: 007afb93  andi         x23, x21, 7
    4c4: 003ada93  srli         x21, x21, 3
    4c8: 00ca9a93  slli         x21, x21, 12
    4cc: 014a8ab3  add          x21, x21, x20
    4d0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000004d0
    4d4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000004e8
    4d8: 001b9b93  slli         x23, x23, 1
    4dc: 017b0b33  add          x22, x22, x23
    4e0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    4e4: 00008067  jalr         x0, 0(x1)
    4e8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    4ec: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4f0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    4f4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_4f8:
    4f8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    4fc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    500: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    504: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    508: 015a6463  bltu         x20, x21, 0x00000510  # target 0x00000510
    50c: fedff06f  jal          x0, 0x000004f8  # target 0x000004f8
loc_510:
    510: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    514: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    518: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    51c: 014a1a13  slli         x20, x20, 20
    520: 014a5a13  srli         x20, x20, 20
    524: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_528:
    528: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    52c: 000b0463  beq          x22, x0, 0x00000534  # target 0x00000534
    530: ff9ff06f  jal          x0, 0x00000528  # target 0x00000528
loc_534:
    534: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    538: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    53c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    540: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    544: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    548: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    54c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    550: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    554: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    558: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    55c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    560: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    564: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    568: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    56c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    570: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    574: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    578: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    57c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    580: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    584: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_588:
    588: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    58c: 000b0463  beq          x22, x0, 0x00000594  # target 0x00000594
    590: ff9ff06f  jal          x0, 0x00000588  # target 0x00000588
loc_594:
    594: 00008067  jalr         x0, 0(x1)
    598:           j FW_BRISC+4   # return to firmware, linked at install
