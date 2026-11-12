# llama3 8b-bf16 decode: attention_merge, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (8): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9
# params: 0x780=attention_partial_tiles, 0x784=e2e_context, 0x788=kv_blocks, 0xea40=merge_head
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 0001b2b7  lui          x5, 0x0001b  # x5 = 0x0001b000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x0001b000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     20: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     24: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     28: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_2c:
     2c: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
     30: 02840413  addi         x8, x8, 40  # x8 = 0xffb49028
     34: 00045283  lhu          x5, 0(x8)  # 0xffb49028
     38: 40428333  sub          x6, x5, x4
     3c: 01031313  slli         x6, x6, 16
     40: 01035313  srli         x6, x6, 16
     44: 00737663  bgeu         x6, x7, 0x00000050  # target 0x00000050
     48: 0ff0000f  fence        0xf, 0xf
     4c: fe1ff06f  jal          x0, 0x0000002c  # target 0x0000002c
loc_50:
     50: 0ff0000f  fence        0xf, 0xf
     54: 600000ef  jal          x1, 0x00000654  # target 0x00000654; x1 = 0x00000058
     58: 618000ef  jal          x1, 0x00000670  # target 0x00000670; x1 = 0x0000005c
     5c: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     60: a4028293  addi         x5, x5, -1472  # x5 = 0x0000ea40
     64: 0002a203  lw           x4, 0(x5)  # param merge_head; 0x0000ea40
     68: 00921213  slli         x4, x4, 9
     6c: 00020293  addi         x5, x4, 0
     70: 00a2d313  srli         x6, x5, 10
     74: 00030f93  addi         x31, x6, 0
     78: 614000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x0000007c
     7c: 000a8393  addi         x7, x21, 0
     80: 000b0413  addi         x8, x22, 0
     84: 3ff2f293  andi         x5, x5, 1023
     88: 00129493  slli         x9, x5, 1
     8c: 007484b3  add          x9, x9, x7
     90: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
     94: 00048f13  addi         x30, x9, 0
     98: 00040e93  addi         x29, x8, 0
     9c: 63c000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000000a0
     a0: 01028293  addi         x5, x5, 16
     a4: 00129493  slli         x9, x5, 1
     a8: 007484b3  add          x9, x9, x7
     ac: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
     b0: 200f8f93  addi         x31, x31, 512  # x31 = 0x0001b200
     b4: 00048f13  addi         x30, x9, 0
     b8: 00040e93  addi         x29, x8, 0
     bc: 61c000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000000c0
     c0: 02020293  addi         x5, x4, 32
     c4: 00a2d313  srli         x6, x5, 10
     c8: 00030f93  addi         x31, x6, 0
     cc: 5c0000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x000000d0
     d0: 000a8393  addi         x7, x21, 0
     d4: 000b0413  addi         x8, x22, 0
     d8: 3ff2f293  andi         x5, x5, 1023
     dc: 00129493  slli         x9, x5, 1
     e0: 007484b3  add          x9, x9, x7
     e4: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
     e8: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001b800
     ec: 00048f13  addi         x30, x9, 0
     f0: 00040e93  addi         x29, x8, 0
     f4: 5e4000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000000f8
     f8: 01028293  addi         x5, x5, 16
     fc: 00129493  slli         x9, x5, 1
    100: 007484b3  add          x9, x9, x7
    104: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    108: a00f8f93  addi         x31, x31, -1536  # x31 = 0x0001ba00
    10c: 00048f13  addi         x30, x9, 0
    110: 00040e93  addi         x29, x8, 0
    114: 5c4000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000118
    118: 04020293  addi         x5, x4, 64
    11c: 00a2d313  srli         x6, x5, 10
    120: 00030f93  addi         x31, x6, 0
    124: 568000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x00000128
    128: 000a8393  addi         x7, x21, 0
    12c: 000b0413  addi         x8, x22, 0
    130: 3ff2f293  andi         x5, x5, 1023
    134: 00129493  slli         x9, x5, 1
    138: 007484b3  add          x9, x9, x7
    13c: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    140: 00048f13  addi         x30, x9, 0
    144: 00040e93  addi         x29, x8, 0
    148: 590000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000014c
    14c: 01028293  addi         x5, x5, 16
    150: 00129493  slli         x9, x5, 1
    154: 007484b3  add          x9, x9, x7
    158: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    15c: 200f8f93  addi         x31, x31, 512  # x31 = 0x0001c200
    160: 00048f13  addi         x30, x9, 0
    164: 00040e93  addi         x29, x8, 0
    168: 570000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000016c
    16c: 06020293  addi         x5, x4, 96
    170: 00a2d313  srli         x6, x5, 10
    174: 00030f93  addi         x31, x6, 0
    178: 514000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x0000017c
    17c: 000a8393  addi         x7, x21, 0
    180: 000b0413  addi         x8, x22, 0
    184: 3ff2f293  andi         x5, x5, 1023
    188: 00129493  slli         x9, x5, 1
    18c: 007484b3  add          x9, x9, x7
    190: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    194: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001c800
    198: 00048f13  addi         x30, x9, 0
    19c: 00040e93  addi         x29, x8, 0
    1a0: 538000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000001a4
    1a4: 01028293  addi         x5, x5, 16
    1a8: 00129493  slli         x9, x5, 1
    1ac: 007484b3  add          x9, x9, x7
    1b0: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    1b4: a00f8f93  addi         x31, x31, -1536  # x31 = 0x0001ca00
    1b8: 00048f13  addi         x30, x9, 0
    1bc: 00040e93  addi         x29, x8, 0
    1c0: 518000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000001c4
    1c4: 08020293  addi         x5, x4, 128
    1c8: 00a2d313  srli         x6, x5, 10
    1cc: 00030f93  addi         x31, x6, 0
    1d0: 4bc000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x000001d4
    1d4: 000a8393  addi         x7, x21, 0
    1d8: 000b0413  addi         x8, x22, 0
    1dc: 3ff2f293  andi         x5, x5, 1023
    1e0: 00129493  slli         x9, x5, 1
    1e4: 007484b3  add          x9, x9, x7
    1e8: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    1ec: 020f8f93  addi         x31, x31, 32  # x31 = 0x0001b020
    1f0: 00048f13  addi         x30, x9, 0
    1f4: 00040e93  addi         x29, x8, 0
    1f8: 4e0000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000001fc
    1fc: 01028293  addi         x5, x5, 16
    200: 00129493  slli         x9, x5, 1
    204: 007484b3  add          x9, x9, x7
    208: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    20c: 220f8f93  addi         x31, x31, 544  # x31 = 0x0001b220
    210: 00048f13  addi         x30, x9, 0
    214: 00040e93  addi         x29, x8, 0
    218: 4c0000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000021c
    21c: 0a020293  addi         x5, x4, 160
    220: 00a2d313  srli         x6, x5, 10
    224: 00030f93  addi         x31, x6, 0
    228: 464000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x0000022c
    22c: 000a8393  addi         x7, x21, 0
    230: 000b0413  addi         x8, x22, 0
    234: 3ff2f293  andi         x5, x5, 1023
    238: 00129493  slli         x9, x5, 1
    23c: 007484b3  add          x9, x9, x7
    240: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    244: 820f8f93  addi         x31, x31, -2016  # x31 = 0x0001b820
    248: 00048f13  addi         x30, x9, 0
    24c: 00040e93  addi         x29, x8, 0
    250: 488000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000254
    254: 01028293  addi         x5, x5, 16
    258: 00129493  slli         x9, x5, 1
    25c: 007484b3  add          x9, x9, x7
    260: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    264: a20f8f93  addi         x31, x31, -1504  # x31 = 0x0001ba20
    268: 00048f13  addi         x30, x9, 0
    26c: 00040e93  addi         x29, x8, 0
    270: 468000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000274
    274: 0c020293  addi         x5, x4, 192
    278: 00a2d313  srli         x6, x5, 10
    27c: 00030f93  addi         x31, x6, 0
    280: 40c000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x00000284
    284: 000a8393  addi         x7, x21, 0
    288: 000b0413  addi         x8, x22, 0
    28c: 3ff2f293  andi         x5, x5, 1023
    290: 00129493  slli         x9, x5, 1
    294: 007484b3  add          x9, x9, x7
    298: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    29c: 020f8f93  addi         x31, x31, 32  # x31 = 0x0001c020
    2a0: 00048f13  addi         x30, x9, 0
    2a4: 00040e93  addi         x29, x8, 0
    2a8: 430000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000002ac
    2ac: 01028293  addi         x5, x5, 16
    2b0: 00129493  slli         x9, x5, 1
    2b4: 007484b3  add          x9, x9, x7
    2b8: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    2bc: 220f8f93  addi         x31, x31, 544  # x31 = 0x0001c220
    2c0: 00048f13  addi         x30, x9, 0
    2c4: 00040e93  addi         x29, x8, 0
    2c8: 410000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000002cc
    2cc: 0e020293  addi         x5, x4, 224
    2d0: 00a2d313  srli         x6, x5, 10
    2d4: 00030f93  addi         x31, x6, 0
    2d8: 3b4000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x000002dc
    2dc: 000a8393  addi         x7, x21, 0
    2e0: 000b0413  addi         x8, x22, 0
    2e4: 3ff2f293  andi         x5, x5, 1023
    2e8: 00129493  slli         x9, x5, 1
    2ec: 007484b3  add          x9, x9, x7
    2f0: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    2f4: 820f8f93  addi         x31, x31, -2016  # x31 = 0x0001c820
    2f8: 00048f13  addi         x30, x9, 0
    2fc: 00040e93  addi         x29, x8, 0
    300: 3d8000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000304
    304: 01028293  addi         x5, x5, 16
    308: 00129493  slli         x9, x5, 1
    30c: 007484b3  add          x9, x9, x7
    310: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    314: a20f8f93  addi         x31, x31, -1504  # x31 = 0x0001ca20
    318: 00048f13  addi         x30, x9, 0
    31c: 00040e93  addi         x29, x8, 0
    320: 3b8000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000324
    324: 10020293  addi         x5, x4, 256
    328: 00a2d313  srli         x6, x5, 10
    32c: 00030f93  addi         x31, x6, 0
    330: 35c000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x00000334
    334: 000a8393  addi         x7, x21, 0
    338: 000b0413  addi         x8, x22, 0
    33c: 3ff2f293  andi         x5, x5, 1023
    340: 00129493  slli         x9, x5, 1
    344: 007484b3  add          x9, x9, x7
    348: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    34c: 040f8f93  addi         x31, x31, 64  # x31 = 0x0001b040
    350: 00048f13  addi         x30, x9, 0
    354: 00040e93  addi         x29, x8, 0
    358: 380000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000035c
    35c: 01028293  addi         x5, x5, 16
    360: 00129493  slli         x9, x5, 1
    364: 007484b3  add          x9, x9, x7
    368: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    36c: 240f8f93  addi         x31, x31, 576  # x31 = 0x0001b240
    370: 00048f13  addi         x30, x9, 0
    374: 00040e93  addi         x29, x8, 0
    378: 360000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000037c
    37c: 12020293  addi         x5, x4, 288
    380: 00a2d313  srli         x6, x5, 10
    384: 00030f93  addi         x31, x6, 0
    388: 304000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x0000038c
    38c: 000a8393  addi         x7, x21, 0
    390: 000b0413  addi         x8, x22, 0
    394: 3ff2f293  andi         x5, x5, 1023
    398: 00129493  slli         x9, x5, 1
    39c: 007484b3  add          x9, x9, x7
    3a0: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    3a4: 840f8f93  addi         x31, x31, -1984  # x31 = 0x0001b840
    3a8: 00048f13  addi         x30, x9, 0
    3ac: 00040e93  addi         x29, x8, 0
    3b0: 328000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000003b4
    3b4: 01028293  addi         x5, x5, 16
    3b8: 00129493  slli         x9, x5, 1
    3bc: 007484b3  add          x9, x9, x7
    3c0: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    3c4: a40f8f93  addi         x31, x31, -1472  # x31 = 0x0001ba40
    3c8: 00048f13  addi         x30, x9, 0
    3cc: 00040e93  addi         x29, x8, 0
    3d0: 308000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000003d4
    3d4: 14020293  addi         x5, x4, 320
    3d8: 00a2d313  srli         x6, x5, 10
    3dc: 00030f93  addi         x31, x6, 0
    3e0: 2ac000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x000003e4
    3e4: 000a8393  addi         x7, x21, 0
    3e8: 000b0413  addi         x8, x22, 0
    3ec: 3ff2f293  andi         x5, x5, 1023
    3f0: 00129493  slli         x9, x5, 1
    3f4: 007484b3  add          x9, x9, x7
    3f8: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    3fc: 040f8f93  addi         x31, x31, 64  # x31 = 0x0001c040
    400: 00048f13  addi         x30, x9, 0
    404: 00040e93  addi         x29, x8, 0
    408: 2d0000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000040c
    40c: 01028293  addi         x5, x5, 16
    410: 00129493  slli         x9, x5, 1
    414: 007484b3  add          x9, x9, x7
    418: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    41c: 240f8f93  addi         x31, x31, 576  # x31 = 0x0001c240
    420: 00048f13  addi         x30, x9, 0
    424: 00040e93  addi         x29, x8, 0
    428: 2b0000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000042c
    42c: 16020293  addi         x5, x4, 352
    430: 00a2d313  srli         x6, x5, 10
    434: 00030f93  addi         x31, x6, 0
    438: 254000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x0000043c
    43c: 000a8393  addi         x7, x21, 0
    440: 000b0413  addi         x8, x22, 0
    444: 3ff2f293  andi         x5, x5, 1023
    448: 00129493  slli         x9, x5, 1
    44c: 007484b3  add          x9, x9, x7
    450: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    454: 840f8f93  addi         x31, x31, -1984  # x31 = 0x0001c840
    458: 00048f13  addi         x30, x9, 0
    45c: 00040e93  addi         x29, x8, 0
    460: 278000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000464
    464: 01028293  addi         x5, x5, 16
    468: 00129493  slli         x9, x5, 1
    46c: 007484b3  add          x9, x9, x7
    470: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    474: a40f8f93  addi         x31, x31, -1472  # x31 = 0x0001ca40
    478: 00048f13  addi         x30, x9, 0
    47c: 00040e93  addi         x29, x8, 0
    480: 258000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000484
    484: 18020293  addi         x5, x4, 384
    488: 00a2d313  srli         x6, x5, 10
    48c: 00030f93  addi         x31, x6, 0
    490: 1fc000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x00000494
    494: 000a8393  addi         x7, x21, 0
    498: 000b0413  addi         x8, x22, 0
    49c: 3ff2f293  andi         x5, x5, 1023
    4a0: 00129493  slli         x9, x5, 1
    4a4: 007484b3  add          x9, x9, x7
    4a8: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    4ac: 060f8f93  addi         x31, x31, 96  # x31 = 0x0001b060
    4b0: 00048f13  addi         x30, x9, 0
    4b4: 00040e93  addi         x29, x8, 0
    4b8: 220000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000004bc
    4bc: 01028293  addi         x5, x5, 16
    4c0: 00129493  slli         x9, x5, 1
    4c4: 007484b3  add          x9, x9, x7
    4c8: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    4cc: 260f8f93  addi         x31, x31, 608  # x31 = 0x0001b260
    4d0: 00048f13  addi         x30, x9, 0
    4d4: 00040e93  addi         x29, x8, 0
    4d8: 200000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000004dc
    4dc: 1a020293  addi         x5, x4, 416
    4e0: 00a2d313  srli         x6, x5, 10
    4e4: 00030f93  addi         x31, x6, 0
    4e8: 1a4000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x000004ec
    4ec: 000a8393  addi         x7, x21, 0
    4f0: 000b0413  addi         x8, x22, 0
    4f4: 3ff2f293  andi         x5, x5, 1023
    4f8: 00129493  slli         x9, x5, 1
    4fc: 007484b3  add          x9, x9, x7
    500: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    504: 860f8f93  addi         x31, x31, -1952  # x31 = 0x0001b860
    508: 00048f13  addi         x30, x9, 0
    50c: 00040e93  addi         x29, x8, 0
    510: 1c8000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000514
    514: 01028293  addi         x5, x5, 16
    518: 00129493  slli         x9, x5, 1
    51c: 007484b3  add          x9, x9, x7
    520: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    524: a60f8f93  addi         x31, x31, -1440  # x31 = 0x0001ba60
    528: 00048f13  addi         x30, x9, 0
    52c: 00040e93  addi         x29, x8, 0
    530: 1a8000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x00000534
    534: 1c020293  addi         x5, x4, 448
    538: 00a2d313  srli         x6, x5, 10
    53c: 00030f93  addi         x31, x6, 0
    540: 14c000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x00000544
    544: 000a8393  addi         x7, x21, 0
    548: 000b0413  addi         x8, x22, 0
    54c: 3ff2f293  andi         x5, x5, 1023
    550: 00129493  slli         x9, x5, 1
    554: 007484b3  add          x9, x9, x7
    558: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    55c: 060f8f93  addi         x31, x31, 96  # x31 = 0x0001c060
    560: 00048f13  addi         x30, x9, 0
    564: 00040e93  addi         x29, x8, 0
    568: 170000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000056c
    56c: 01028293  addi         x5, x5, 16
    570: 00129493  slli         x9, x5, 1
    574: 007484b3  add          x9, x9, x7
    578: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    57c: 260f8f93  addi         x31, x31, 608  # x31 = 0x0001c260
    580: 00048f13  addi         x30, x9, 0
    584: 00040e93  addi         x29, x8, 0
    588: 150000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x0000058c
    58c: 1e020293  addi         x5, x4, 480
    590: 00a2d313  srli         x6, x5, 10
    594: 00030f93  addi         x31, x6, 0
    598: 0f4000ef  jal          x1, 0x0000068c  # target 0x0000068c; x1 = 0x0000059c
    59c: 000a8393  addi         x7, x21, 0
    5a0: 000b0413  addi         x8, x22, 0
    5a4: 3ff2f293  andi         x5, x5, 1023
    5a8: 00129493  slli         x9, x5, 1
    5ac: 007484b3  add          x9, x9, x7
    5b0: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    5b4: 860f8f93  addi         x31, x31, -1952  # x31 = 0x0001c860
    5b8: 00048f13  addi         x30, x9, 0
    5bc: 00040e93  addi         x29, x8, 0
    5c0: 118000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000005c4
    5c4: 01028293  addi         x5, x5, 16
    5c8: 00129493  slli         x9, x5, 1
    5cc: 007484b3  add          x9, x9, x7
    5d0: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    5d4: a60f8f93  addi         x31, x31, -1440  # x31 = 0x0001ca60
    5d8: 00048f13  addi         x30, x9, 0
    5dc: 00040e93  addi         x29, x8, 0
    5e0: 0f8000ef  jal          x1, 0x000006d8  # target 0x000006d8; x1 = 0x000005e4
    5e4: 070000ef  jal          x1, 0x00000654  # target 0x00000654; x1 = 0x000005e8
    5e8: 088000ef  jal          x1, 0x00000670  # target 0x00000670; x1 = 0x000005ec
    5ec: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5f0: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    5f4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    5f8: 00420213  addi         x4, x4, 4
    5fc: 01021213  slli         x4, x4, 16
    600: 01025213  srli         x4, x4, 16
    604: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    608: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    60c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    610: ffb492b7  lui          x5, 0xffb49  # x5 = 0xffb49000
    614: 02028293  addi         x5, x5, 32  # x5 = 0xffb49020
    618: 0042a023  sw           x4, 0(x5)  # 0xffb49020; write runtime value
    61c: 0ff0000f  fence        0xf, 0xf
    620: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    624: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    628: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    62c: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    630: 00520233  add          x4, x4, x5
    634: 0001d337  lui          x6, 0x0001d  # x6 = 0x0001d000
    638: 00626663  bltu         x4, x6, 0x00000644  # target 0x00000644
    63c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    640: 40720233  sub          x4, x4, x7
loc_644:
    644: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    648: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    64c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    650: 1400006f  jal          x0, 0x00000790  # target 0x00000790
loc_654:
    654: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    658: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    65c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    660: 000a0463  beq          x20, x0, 0x00000668  # target 0x00000668
    664: ff1ff06f  jal          x0, 0x00000654  # target 0x00000654
loc_668:
    668: 0ff0000f  fence        0xf, 0xf
    66c: 00008067  jalr         x0, 0(x1)
loc_670:
    670: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    674: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    678: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    67c: 000a0463  beq          x20, x0, 0x00000684  # target 0x00000684
    680: ff1ff06f  jal          x0, 0x00000670  # target 0x00000670
loc_684:
    684: 0ff0000f  fence        0xf, 0xf
    688: 00008067  jalr         x0, 0(x1)
loc_68c:
    68c: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    690: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x00000784
    694: 007a7d13  andi         x26, x20, 7
    698: ff8a7a13  andi         x20, x20, -8
    69c: 01af8ab3  add          x21, x31, x26
    6a0: 007afb93  andi         x23, x21, 7
    6a4: 003ada93  srli         x21, x21, 3
    6a8: 00ba9a93  slli         x21, x21, 11
    6ac: 014a8ab3  add          x21, x21, x20
    6b0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000006b0
    6b4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000006c8
    6b8: 001b9b93  slli         x23, x23, 1
    6bc: 017b0b33  add          x22, x22, x23
    6c0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6c4: 00008067  jalr         x0, 0(x1)
    6c8: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6cc: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6d0: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6d4: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_6d8:
    6d8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6dc: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    6e0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    6e4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6e8: 015a6463  bltu         x20, x21, 0x000006f0  # target 0x000006f0
    6ec: fedff06f  jal          x0, 0x000006d8  # target 0x000006d8
loc_6f0:
    6f0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6f4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    6f8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    6fc: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    700: 015a6463  bltu         x20, x21, 0x00000708  # target 0x00000708
    704: fedff06f  jal          x0, 0x000006f0  # target 0x000006f0
loc_708:
    708: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    70c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    710: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    714: 014a1a13  slli         x20, x20, 20
    718: 014a5a13  srli         x20, x20, 20
    71c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_720:
    720: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    724: 000b0463  beq          x22, x0, 0x0000072c  # target 0x0000072c
    728: ff9ff06f  jal          x0, 0x00000720  # target 0x00000720
loc_72c:
    72c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    730: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    734: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    738: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    73c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    740: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    744: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    748: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    74c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    750: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    754: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    758: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    75c: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    760: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    764: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    768: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    76c: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    770: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    774: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    778: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    77c: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_780:
    780: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    784: 000b0463  beq          x22, x0, 0x0000078c  # target 0x0000078c
    788: ff9ff06f  jal          x0, 0x00000780  # target 0x00000780
loc_78c:
    78c: 00008067  jalr         x0, 0(x1)
    790:           j FW_NCRISC+4   # return to firmware, linked at install
