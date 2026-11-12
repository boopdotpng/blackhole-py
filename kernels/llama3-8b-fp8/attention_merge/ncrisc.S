# llama3 8b-fp8 decode: attention_merge, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (8): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9
# params: 0x780=attention_partial_tiles, 0x784=e2e_context, 0x788=kv_blocks, 0xea40=merge_head
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 0001b2b7  lui          x5, 0x0001b  # x5 = 0x0001b000
      c: 08028293  addi         x5, x5, 128  # x5 = 0x0001b080
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x0001b080
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     24: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     28: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     2c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_30:
     30: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
     34: 02840413  addi         x8, x8, 40  # x8 = 0xffb49028
     38: 00045283  lhu          x5, 0(x8)  # 0xffb49028
     3c: 40428333  sub          x6, x5, x4
     40: 01031313  slli         x6, x6, 16
     44: 01035313  srli         x6, x6, 16
     48: 00737663  bgeu         x6, x7, 0x00000054  # target 0x00000054
     4c: 0ff0000f  fence        0xf, 0xf
     50: fe1ff06f  jal          x0, 0x00000030  # target 0x00000030
loc_54:
     54: 0ff0000f  fence        0xf, 0xf
     58: 60c000ef  jal          x1, 0x00000664  # target 0x00000664; x1 = 0x0000005c
     5c: 624000ef  jal          x1, 0x00000680  # target 0x00000680; x1 = 0x00000060
     60: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     64: a4028293  addi         x5, x5, -1472  # x5 = 0x0000ea40
     68: 0002a203  lw           x4, 0(x5)  # param merge_head; 0x0000ea40
     6c: 00921213  slli         x4, x4, 9
     70: 00020293  addi         x5, x4, 0
     74: 00a2d313  srli         x6, x5, 10
     78: 00030f93  addi         x31, x6, 0
     7c: 620000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000080
     80: 000a8393  addi         x7, x21, 0
     84: 000b0413  addi         x8, x22, 0
     88: 3ff2f293  andi         x5, x5, 1023
     8c: 00129493  slli         x9, x5, 1
     90: 007484b3  add          x9, x9, x7
     94: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
     98: 080f8f93  addi         x31, x31, 128  # x31 = 0x0001b080
     9c: 00048f13  addi         x30, x9, 0
     a0: 00040e93  addi         x29, x8, 0
     a4: 644000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000000a8
     a8: 01028293  addi         x5, x5, 16
     ac: 00129493  slli         x9, x5, 1
     b0: 007484b3  add          x9, x9, x7
     b4: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
     b8: 280f8f93  addi         x31, x31, 640  # x31 = 0x0001b280
     bc: 00048f13  addi         x30, x9, 0
     c0: 00040e93  addi         x29, x8, 0
     c4: 624000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000000c8
     c8: 02020293  addi         x5, x4, 32
     cc: 00a2d313  srli         x6, x5, 10
     d0: 00030f93  addi         x31, x6, 0
     d4: 5c8000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x000000d8
     d8: 000a8393  addi         x7, x21, 0
     dc: 000b0413  addi         x8, x22, 0
     e0: 3ff2f293  andi         x5, x5, 1023
     e4: 00129493  slli         x9, x5, 1
     e8: 007484b3  add          x9, x9, x7
     ec: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
     f0: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001b880
     f4: 00048f13  addi         x30, x9, 0
     f8: 00040e93  addi         x29, x8, 0
     fc: 5ec000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000100
    100: 01028293  addi         x5, x5, 16
    104: 00129493  slli         x9, x5, 1
    108: 007484b3  add          x9, x9, x7
    10c: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    110: a80f8f93  addi         x31, x31, -1408  # x31 = 0x0001ba80
    114: 00048f13  addi         x30, x9, 0
    118: 00040e93  addi         x29, x8, 0
    11c: 5cc000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000120
    120: 04020293  addi         x5, x4, 64
    124: 00a2d313  srli         x6, x5, 10
    128: 00030f93  addi         x31, x6, 0
    12c: 570000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000130
    130: 000a8393  addi         x7, x21, 0
    134: 000b0413  addi         x8, x22, 0
    138: 3ff2f293  andi         x5, x5, 1023
    13c: 00129493  slli         x9, x5, 1
    140: 007484b3  add          x9, x9, x7
    144: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    148: 080f8f93  addi         x31, x31, 128  # x31 = 0x0001c080
    14c: 00048f13  addi         x30, x9, 0
    150: 00040e93  addi         x29, x8, 0
    154: 594000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000158
    158: 01028293  addi         x5, x5, 16
    15c: 00129493  slli         x9, x5, 1
    160: 007484b3  add          x9, x9, x7
    164: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    168: 280f8f93  addi         x31, x31, 640  # x31 = 0x0001c280
    16c: 00048f13  addi         x30, x9, 0
    170: 00040e93  addi         x29, x8, 0
    174: 574000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000178
    178: 06020293  addi         x5, x4, 96
    17c: 00a2d313  srli         x6, x5, 10
    180: 00030f93  addi         x31, x6, 0
    184: 518000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000188
    188: 000a8393  addi         x7, x21, 0
    18c: 000b0413  addi         x8, x22, 0
    190: 3ff2f293  andi         x5, x5, 1023
    194: 00129493  slli         x9, x5, 1
    198: 007484b3  add          x9, x9, x7
    19c: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    1a0: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001c880
    1a4: 00048f13  addi         x30, x9, 0
    1a8: 00040e93  addi         x29, x8, 0
    1ac: 53c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000001b0
    1b0: 01028293  addi         x5, x5, 16
    1b4: 00129493  slli         x9, x5, 1
    1b8: 007484b3  add          x9, x9, x7
    1bc: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    1c0: a80f8f93  addi         x31, x31, -1408  # x31 = 0x0001ca80
    1c4: 00048f13  addi         x30, x9, 0
    1c8: 00040e93  addi         x29, x8, 0
    1cc: 51c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000001d0
    1d0: 08020293  addi         x5, x4, 128
    1d4: 00a2d313  srli         x6, x5, 10
    1d8: 00030f93  addi         x31, x6, 0
    1dc: 4c0000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x000001e0
    1e0: 000a8393  addi         x7, x21, 0
    1e4: 000b0413  addi         x8, x22, 0
    1e8: 3ff2f293  andi         x5, x5, 1023
    1ec: 00129493  slli         x9, x5, 1
    1f0: 007484b3  add          x9, x9, x7
    1f4: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    1f8: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x0001b0a0
    1fc: 00048f13  addi         x30, x9, 0
    200: 00040e93  addi         x29, x8, 0
    204: 4e4000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000208
    208: 01028293  addi         x5, x5, 16
    20c: 00129493  slli         x9, x5, 1
    210: 007484b3  add          x9, x9, x7
    214: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    218: 2a0f8f93  addi         x31, x31, 672  # x31 = 0x0001b2a0
    21c: 00048f13  addi         x30, x9, 0
    220: 00040e93  addi         x29, x8, 0
    224: 4c4000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000228
    228: 0a020293  addi         x5, x4, 160
    22c: 00a2d313  srli         x6, x5, 10
    230: 00030f93  addi         x31, x6, 0
    234: 468000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000238
    238: 000a8393  addi         x7, x21, 0
    23c: 000b0413  addi         x8, x22, 0
    240: 3ff2f293  andi         x5, x5, 1023
    244: 00129493  slli         x9, x5, 1
    248: 007484b3  add          x9, x9, x7
    24c: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    250: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x0001b8a0
    254: 00048f13  addi         x30, x9, 0
    258: 00040e93  addi         x29, x8, 0
    25c: 48c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000260
    260: 01028293  addi         x5, x5, 16
    264: 00129493  slli         x9, x5, 1
    268: 007484b3  add          x9, x9, x7
    26c: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    270: aa0f8f93  addi         x31, x31, -1376  # x31 = 0x0001baa0
    274: 00048f13  addi         x30, x9, 0
    278: 00040e93  addi         x29, x8, 0
    27c: 46c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000280
    280: 0c020293  addi         x5, x4, 192
    284: 00a2d313  srli         x6, x5, 10
    288: 00030f93  addi         x31, x6, 0
    28c: 410000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000290
    290: 000a8393  addi         x7, x21, 0
    294: 000b0413  addi         x8, x22, 0
    298: 3ff2f293  andi         x5, x5, 1023
    29c: 00129493  slli         x9, x5, 1
    2a0: 007484b3  add          x9, x9, x7
    2a4: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    2a8: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x0001c0a0
    2ac: 00048f13  addi         x30, x9, 0
    2b0: 00040e93  addi         x29, x8, 0
    2b4: 434000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000002b8
    2b8: 01028293  addi         x5, x5, 16
    2bc: 00129493  slli         x9, x5, 1
    2c0: 007484b3  add          x9, x9, x7
    2c4: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    2c8: 2a0f8f93  addi         x31, x31, 672  # x31 = 0x0001c2a0
    2cc: 00048f13  addi         x30, x9, 0
    2d0: 00040e93  addi         x29, x8, 0
    2d4: 414000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000002d8
    2d8: 0e020293  addi         x5, x4, 224
    2dc: 00a2d313  srli         x6, x5, 10
    2e0: 00030f93  addi         x31, x6, 0
    2e4: 3b8000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x000002e8
    2e8: 000a8393  addi         x7, x21, 0
    2ec: 000b0413  addi         x8, x22, 0
    2f0: 3ff2f293  andi         x5, x5, 1023
    2f4: 00129493  slli         x9, x5, 1
    2f8: 007484b3  add          x9, x9, x7
    2fc: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    300: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x0001c8a0
    304: 00048f13  addi         x30, x9, 0
    308: 00040e93  addi         x29, x8, 0
    30c: 3dc000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000310
    310: 01028293  addi         x5, x5, 16
    314: 00129493  slli         x9, x5, 1
    318: 007484b3  add          x9, x9, x7
    31c: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    320: aa0f8f93  addi         x31, x31, -1376  # x31 = 0x0001caa0
    324: 00048f13  addi         x30, x9, 0
    328: 00040e93  addi         x29, x8, 0
    32c: 3bc000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000330
    330: 10020293  addi         x5, x4, 256
    334: 00a2d313  srli         x6, x5, 10
    338: 00030f93  addi         x31, x6, 0
    33c: 360000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000340
    340: 000a8393  addi         x7, x21, 0
    344: 000b0413  addi         x8, x22, 0
    348: 3ff2f293  andi         x5, x5, 1023
    34c: 00129493  slli         x9, x5, 1
    350: 007484b3  add          x9, x9, x7
    354: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    358: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x0001b0c0
    35c: 00048f13  addi         x30, x9, 0
    360: 00040e93  addi         x29, x8, 0
    364: 384000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000368
    368: 01028293  addi         x5, x5, 16
    36c: 00129493  slli         x9, x5, 1
    370: 007484b3  add          x9, x9, x7
    374: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    378: 2c0f8f93  addi         x31, x31, 704  # x31 = 0x0001b2c0
    37c: 00048f13  addi         x30, x9, 0
    380: 00040e93  addi         x29, x8, 0
    384: 364000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000388
    388: 12020293  addi         x5, x4, 288
    38c: 00a2d313  srli         x6, x5, 10
    390: 00030f93  addi         x31, x6, 0
    394: 308000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000398
    398: 000a8393  addi         x7, x21, 0
    39c: 000b0413  addi         x8, x22, 0
    3a0: 3ff2f293  andi         x5, x5, 1023
    3a4: 00129493  slli         x9, x5, 1
    3a8: 007484b3  add          x9, x9, x7
    3ac: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    3b0: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x0001b8c0
    3b4: 00048f13  addi         x30, x9, 0
    3b8: 00040e93  addi         x29, x8, 0
    3bc: 32c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000003c0
    3c0: 01028293  addi         x5, x5, 16
    3c4: 00129493  slli         x9, x5, 1
    3c8: 007484b3  add          x9, x9, x7
    3cc: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    3d0: ac0f8f93  addi         x31, x31, -1344  # x31 = 0x0001bac0
    3d4: 00048f13  addi         x30, x9, 0
    3d8: 00040e93  addi         x29, x8, 0
    3dc: 30c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000003e0
    3e0: 14020293  addi         x5, x4, 320
    3e4: 00a2d313  srli         x6, x5, 10
    3e8: 00030f93  addi         x31, x6, 0
    3ec: 2b0000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x000003f0
    3f0: 000a8393  addi         x7, x21, 0
    3f4: 000b0413  addi         x8, x22, 0
    3f8: 3ff2f293  andi         x5, x5, 1023
    3fc: 00129493  slli         x9, x5, 1
    400: 007484b3  add          x9, x9, x7
    404: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    408: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x0001c0c0
    40c: 00048f13  addi         x30, x9, 0
    410: 00040e93  addi         x29, x8, 0
    414: 2d4000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000418
    418: 01028293  addi         x5, x5, 16
    41c: 00129493  slli         x9, x5, 1
    420: 007484b3  add          x9, x9, x7
    424: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    428: 2c0f8f93  addi         x31, x31, 704  # x31 = 0x0001c2c0
    42c: 00048f13  addi         x30, x9, 0
    430: 00040e93  addi         x29, x8, 0
    434: 2b4000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000438
    438: 16020293  addi         x5, x4, 352
    43c: 00a2d313  srli         x6, x5, 10
    440: 00030f93  addi         x31, x6, 0
    444: 258000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000448
    448: 000a8393  addi         x7, x21, 0
    44c: 000b0413  addi         x8, x22, 0
    450: 3ff2f293  andi         x5, x5, 1023
    454: 00129493  slli         x9, x5, 1
    458: 007484b3  add          x9, x9, x7
    45c: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    460: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x0001c8c0
    464: 00048f13  addi         x30, x9, 0
    468: 00040e93  addi         x29, x8, 0
    46c: 27c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000470
    470: 01028293  addi         x5, x5, 16
    474: 00129493  slli         x9, x5, 1
    478: 007484b3  add          x9, x9, x7
    47c: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    480: ac0f8f93  addi         x31, x31, -1344  # x31 = 0x0001cac0
    484: 00048f13  addi         x30, x9, 0
    488: 00040e93  addi         x29, x8, 0
    48c: 25c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000490
    490: 18020293  addi         x5, x4, 384
    494: 00a2d313  srli         x6, x5, 10
    498: 00030f93  addi         x31, x6, 0
    49c: 200000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x000004a0
    4a0: 000a8393  addi         x7, x21, 0
    4a4: 000b0413  addi         x8, x22, 0
    4a8: 3ff2f293  andi         x5, x5, 1023
    4ac: 00129493  slli         x9, x5, 1
    4b0: 007484b3  add          x9, x9, x7
    4b4: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    4b8: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x0001b0e0
    4bc: 00048f13  addi         x30, x9, 0
    4c0: 00040e93  addi         x29, x8, 0
    4c4: 224000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000004c8
    4c8: 01028293  addi         x5, x5, 16
    4cc: 00129493  slli         x9, x5, 1
    4d0: 007484b3  add          x9, x9, x7
    4d4: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    4d8: 2e0f8f93  addi         x31, x31, 736  # x31 = 0x0001b2e0
    4dc: 00048f13  addi         x30, x9, 0
    4e0: 00040e93  addi         x29, x8, 0
    4e4: 204000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000004e8
    4e8: 1a020293  addi         x5, x4, 416
    4ec: 00a2d313  srli         x6, x5, 10
    4f0: 00030f93  addi         x31, x6, 0
    4f4: 1a8000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x000004f8
    4f8: 000a8393  addi         x7, x21, 0
    4fc: 000b0413  addi         x8, x22, 0
    500: 3ff2f293  andi         x5, x5, 1023
    504: 00129493  slli         x9, x5, 1
    508: 007484b3  add          x9, x9, x7
    50c: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    510: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x0001b8e0
    514: 00048f13  addi         x30, x9, 0
    518: 00040e93  addi         x29, x8, 0
    51c: 1cc000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000520
    520: 01028293  addi         x5, x5, 16
    524: 00129493  slli         x9, x5, 1
    528: 007484b3  add          x9, x9, x7
    52c: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    530: ae0f8f93  addi         x31, x31, -1312  # x31 = 0x0001bae0
    534: 00048f13  addi         x30, x9, 0
    538: 00040e93  addi         x29, x8, 0
    53c: 1ac000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000540
    540: 1c020293  addi         x5, x4, 448
    544: 00a2d313  srli         x6, x5, 10
    548: 00030f93  addi         x31, x6, 0
    54c: 150000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x00000550
    550: 000a8393  addi         x7, x21, 0
    554: 000b0413  addi         x8, x22, 0
    558: 3ff2f293  andi         x5, x5, 1023
    55c: 00129493  slli         x9, x5, 1
    560: 007484b3  add          x9, x9, x7
    564: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    568: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x0001c0e0
    56c: 00048f13  addi         x30, x9, 0
    570: 00040e93  addi         x29, x8, 0
    574: 174000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000578
    578: 01028293  addi         x5, x5, 16
    57c: 00129493  slli         x9, x5, 1
    580: 007484b3  add          x9, x9, x7
    584: 0001cfb7  lui          x31, 0x0001c  # x31 = 0x0001c000
    588: 2e0f8f93  addi         x31, x31, 736  # x31 = 0x0001c2e0
    58c: 00048f13  addi         x30, x9, 0
    590: 00040e93  addi         x29, x8, 0
    594: 154000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000598
    598: 1e020293  addi         x5, x4, 480
    59c: 00a2d313  srli         x6, x5, 10
    5a0: 00030f93  addi         x31, x6, 0
    5a4: 0f8000ef  jal          x1, 0x0000069c  # target 0x0000069c; x1 = 0x000005a8
    5a8: 000a8393  addi         x7, x21, 0
    5ac: 000b0413  addi         x8, x22, 0
    5b0: 3ff2f293  andi         x5, x5, 1023
    5b4: 00129493  slli         x9, x5, 1
    5b8: 007484b3  add          x9, x9, x7
    5bc: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    5c0: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x0001c8e0
    5c4: 00048f13  addi         x30, x9, 0
    5c8: 00040e93  addi         x29, x8, 0
    5cc: 11c000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000005d0
    5d0: 01028293  addi         x5, x5, 16
    5d4: 00129493  slli         x9, x5, 1
    5d8: 007484b3  add          x9, x9, x7
    5dc: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    5e0: ae0f8f93  addi         x31, x31, -1312  # x31 = 0x0001cae0
    5e4: 00048f13  addi         x30, x9, 0
    5e8: 00040e93  addi         x29, x8, 0
    5ec: 0fc000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000005f0
    5f0: 074000ef  jal          x1, 0x00000664  # target 0x00000664; x1 = 0x000005f4
    5f4: 08c000ef  jal          x1, 0x00000680  # target 0x00000680; x1 = 0x000005f8
    5f8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5fc: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    600: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    604: 00420213  addi         x4, x4, 4
    608: 01021213  slli         x4, x4, 16
    60c: 01025213  srli         x4, x4, 16
    610: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    614: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    618: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    61c: ffb492b7  lui          x5, 0xffb49  # x5 = 0xffb49000
    620: 02028293  addi         x5, x5, 32  # x5 = 0xffb49020
    624: 0042a023  sw           x4, 0(x5)  # 0xffb49020; write runtime value
    628: 0ff0000f  fence        0xf, 0xf
    62c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    630: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    634: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    638: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    63c: 00520233  add          x4, x4, x5
    640: 0001d337  lui          x6, 0x0001d  # x6 = 0x0001d000
    644: 08030313  addi         x6, x6, 128  # x6 = 0x0001d080
    648: 00626663  bltu         x4, x6, 0x00000654  # target 0x00000654
    64c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    650: 40720233  sub          x4, x4, x7
loc_654:
    654: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    658: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    65c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    660: 1400006f  jal          x0, 0x000007a0  # target 0x000007a0
loc_664:
    664: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    668: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    66c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    670: 000a0463  beq          x20, x0, 0x00000678  # target 0x00000678
    674: ff1ff06f  jal          x0, 0x00000664  # target 0x00000664
loc_678:
    678: 0ff0000f  fence        0xf, 0xf
    67c: 00008067  jalr         x0, 0(x1)
loc_680:
    680: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    684: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    688: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    68c: 000a0463  beq          x20, x0, 0x00000694  # target 0x00000694
    690: ff1ff06f  jal          x0, 0x00000680  # target 0x00000680
loc_694:
    694: 0ff0000f  fence        0xf, 0xf
    698: 00008067  jalr         x0, 0(x1)
loc_69c:
    69c: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    6a0: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x00000784
    6a4: 007a7d13  andi         x26, x20, 7
    6a8: ff8a7a13  andi         x20, x20, -8
    6ac: 01af8ab3  add          x21, x31, x26
    6b0: 007afb93  andi         x23, x21, 7
    6b4: 003ada93  srli         x21, x21, 3
    6b8: 00ba9a93  slli         x21, x21, 11
    6bc: 014a8ab3  add          x21, x21, x20
    6c0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000006c0
    6c4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000006d8
    6c8: 001b9b93  slli         x23, x23, 1
    6cc: 017b0b33  add          x22, x22, x23
    6d0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6d4: 00008067  jalr         x0, 0(x1)
    6d8: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6dc: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6e0: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6e4: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_6e8:
    6e8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6ec: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    6f0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    6f4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6f8: 015a6463  bltu         x20, x21, 0x00000700  # target 0x00000700
    6fc: fedff06f  jal          x0, 0x000006e8  # target 0x000006e8
loc_700:
    700: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    704: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    708: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    70c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    710: 015a6463  bltu         x20, x21, 0x00000718  # target 0x00000718
    714: fedff06f  jal          x0, 0x00000700  # target 0x00000700
loc_718:
    718: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    71c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    720: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    724: 014a1a13  slli         x20, x20, 20
    728: 014a5a13  srli         x20, x20, 20
    72c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_730:
    730: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    734: 000b0463  beq          x22, x0, 0x0000073c  # target 0x0000073c
    738: ff9ff06f  jal          x0, 0x00000730  # target 0x00000730
loc_73c:
    73c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    740: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    744: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    748: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    74c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    750: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    754: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    758: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    75c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    760: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    764: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    768: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    76c: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    770: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    774: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    778: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    77c: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    780: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    784: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    788: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    78c: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_790:
    790: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    794: 000b0463  beq          x22, x0, 0x0000079c  # target 0x0000079c
    798: ff9ff06f  jal          x0, 0x00000790  # target 0x00000790
loc_79c:
    79c: 00008067  jalr         x0, 0(x1)
    7a0:           j FW_NCRISC+4   # return to firmware, linked at install
